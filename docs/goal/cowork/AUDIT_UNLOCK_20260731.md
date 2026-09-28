# Auditoria red-team pós-fato — cadeia de destrave da promoção CAS (2026-07-31)

Auditor: agente Fable 5 (red-team adversarial), sessão claude-cowork-goal.
Escopo: commits `420186ee` (resgate), `1622377a` (recut semântico), `b73c912e` (tools),
`5f1bb540` (fila) + diff vivo não commitado de `internal/v2ingest/`.
Método: leitura de código dos gates + reexecução dos binários pinados do gate no
worktree vivo + reconstrução criptográfica de estados + sondas de syscall no mount.

---

## Item 1 — Hand-edit do contrato semântico (fc→resolution gloss-dissolucao-parcial / gloss-endosso)

**VEREDITO: SEM fraude aberta e SEM inconsistência que o gate deixe passar no conteúdo
determinístico; 2 pendências reais de cadeia de evidência e 1 gap latente de gate.**

Cobertura do gate (verificada por código e por reexecução):

- `internal/v2writingsemantic/contract.go:1038-1064` (`validateResolutions`): o gate exige
  match único por `intent_id` no shard alvo, `sha256(linha viva) == page_record_sha256`
  (1054) e **recomputa** `computeMaterialValidation` da linha viva, exigindo igualdade
  estrita do bloco `material_validation` (1057-1063). Hand-edit não consegue falsificar
  `visible_text_sha256`/`official_sources_sha256`/`computed_word_count`.
- `contract.go:854-886` (`validateResolutionIdentity`): binding exato de requirement/owner,
  evidência canônica com os mesmos shas, verdict fixo, e rejeição de reuso dos bytes
  supersedidos (871-873).
- `contract.go:454-473`: `_meta.requirements_sha256` é recomputado e comparado — a seção
  `requirements` não pode ser corrompida silenciosamente.
- Reexecução hoje do binário pinado (`tools/v2-gate-binary-pins.json`, gate `writing`
  `dd6abd29…`): **PASS** — `contract_sha256=58a00afe… requirements=21 resolutions=7
  unresolved=14`. Hook ativo: `git config core.hooksPath = .githooks`;
  `.githooks/reference-transaction:108-205` roda `tools/run-v2-index-product-gates`
  (gates `cmd/check-v2-supersession-integrity` + `cmd/check-v2-writing-semantic-contract`,
  linhas 690-691) do commit pai imutável — o commit `1622377a` só existe porque passou.
- Linhas 21/22 vivas de `data/editorial/v2_pages/glossario-14.jsonl`: shas `834643a5…` /
  `d6b34a2b…` == resolutions; política presente (`needs_source_research=false`,
  `index_policy=noindex`, `publication_allowed=false`, `lane=informativa`).
- Fontes: byte-idênticas às da versão anterior da página (URLs, `verified_at=2026-07-14`,
  `http_status=200` iguais em `1622377a^` e live; `official_sources_sha256` inalterado no
  recibo) — nenhuma data de verificação fabricada; dentro da janela de 30 dias de
  `internal/v2writingsemantic/material.go:16,197-201`.
- Unicidade: varredura de 7.961 linhas vivas de `v2_pages/*.jsonl` — cada intent ocorre
  **1×**; 6 sondas de 10-gram por página ocorrem **1×** cada (sem molde/dup-phrase). A
  "segunda cópia" de cada intent está apenas em quarentena deslocada
  `data/editorial/v2_pages/.glossario-14.jsonl.stale-cas-…` (ignorada por `.gitignore:48`).

Achados (frestas reais):

1. **Recibo órfão / sha fantasma (médio, corrigível).** O hand-edit avançou o contrato
   para `58a00afe…` mas deixou `data/ops/v2_semantic_forward_candidates_receipt.json`
   apontando `updated_contract_sha256=3d461e5a…` — um estado intermediário que **nunca foi
   commitado** (existiu em disco só entre ~07:45 e 08:03) — e `candidates` ainda lista os
   2 intents como forward candidates. Nenhum gate valida o recibo; o único consumidor é
   `internal/v2semanticrecut/forward.go:491` (`readExactForwardFinal`), que com o mismatch
   devolve "não aplicado" e **se auto-supera** no próximo `--plan-forward-candidates`
   (constrói plano novo do estado vivo, forward.go:148-176) — sem deadlock, mas a cadeia
   de custódia do epoch v3 está quebrada até re-mintar o recibo.
   *Remediação: rodar `finalize-v2-semantic-recut --plan-forward-candidates` +
   `--apply-forward-candidates` para recibo honesto com previous=58a00afe.*
2. **Escopo do hand-edit foi MAIOR que o declarado.** Prova: os 16 `candidates` do recibo
   (incluindo os 2 intents) descrevem o contrato `3d461e5a…` — ou seja, no estado instalado
   pela transação os 2 ainda eram forward candidates; a conversão fc→resolution INTEIRA
   (objeto resolution com revisão, evidência e material) foi manual às ~08:03. Reversão
   byte-a-byte só dos 4 shas **não** reproduz `3d461e5a…` (obtive `5f36e0db…`), confirmando
   mudança estrutural além do sha-swap. O gate re-valida tudo que é determinístico, então
   não há fraude material — mas a revisão semântica é **auto-atestada**
   (`reviewed_by=claude-cowork-goal`) sem evidência fora do contrato, e **não há entrada
   2026-07-31 em `docs/goal/MAESTRO_CODEX_LOG.md`** (grep vazio) — violação da regra de
   registro de intervenção manual. *Registrar a posteriori o quê/porquê.*
3. **Gap latente de gate (baixo hoje, real em escala).** `validateResolutions` lê apenas o
   shard alvo (`contract.go:1046-1053`); a unicidade **global** do intent de uma resolution
   não é verificada pelo gate — a lane fc/adoção verifica ("globalmente exato e único",
   `internal/v2writingsemantic/forward_candidates.go:456`), a lane resolution não. Hoje não
   há dup vivo; um dup futuro em outro shard passaria o writing gate.

## Item 2 — Convergência in-place da transação v2ingest órfã (committing)

**VEREDITO: TERMINOU LIMPA no estado durável; rastreabilidade incompleta (sem terminal
receipt e sem log).**

- `data/ops/v2_ingest_transaction_journal.json`: **ausente** (ENOENT).
- `data/ops/v2_ingest_plan_evidence/`: **vazio** (nenhuma reserva viva).
- Nenhum artefato `.v2txn-*` ativo (não-tombstone) sob `data/` (find limpo); nenhum
  `.v2-ingest-transaction-journal-*` remanescente.
- Tombstones unit-keyed novos em `data/ops/` com mtime de hoje (07:45 e 07:57), formato
  `\.v2txn-retired-v2-<owner64>-<conteudo64>-<token24>\.tombstone` — retirada autenticada
  dos artefatos da transação.
- Cofre: `journals/active/` vazio; 4 journals terminais novos coerentes (ex.:
  `b1176d9d…`: manifest existe em `manifests/sha256/43/4329db93…jsonl`, records
  original→retained íntegros) — são da onda de resgate (`420186ee`), não conflitam.
- Alvos: contrato e recibo vivos == commitados em `1622377a` (worktree limpo para os 3
  paths; `git diff` vazio).
- Ressalvas: (a) a convergência manual não minta terminal receipt em
  `data/ops/v2_ingest_terminal_receipts/` (nenhum `*forward*`/`*semantic*` lá) — custódia
  só por tombstones + git; (b) o recibo instalado ficou órfão em <20 min pelo hand-edit do
  item 1 (mesma pendência); (c) sem entrada no MAESTRO log.

## Item 3 — Patches Go em internal/v2ingest (fallback O_TMPFILE→temp nomeado)

**VEREDITO: patch SÓLIDO em identidade e fail-closed; 1 defeito REAL de ciclo de vida
encontrado e CORRIGIDO PARA FRENTE nesta auditoria.**

Sondas do mount (medidas 2026-07-31): `renameat2 NOREPLACE=EINVAL` (coberto pela emulação),
`renameat2 flags=0` OK, `O_TMPFILE=ENOTSUP` (dispara o fallback), `unlink=EPERM`,
`link` OK. A lista de errnos do patch cobre exatamente os erros vivos deste mount; `EPERM`
em renameat2 fora da lista continua erro duro (fail-closed correto).

Red-team da emulação e das janelas:

- `renameTransactionNoReplaceAt` (transaction_safe_io.go): janela TOCTOU stat→rename é real,
  mas TODO chamador tem pós-verificação de identidade: `publishNamedTransactionBytesExclusivePortable`
  faz `verifyNamedStat` (dev+ino via `sameUnixFile`) após sync; a via nomeada de
  `renameTransactionFileWithHooks` refaz `Fstat`+`sameUnixFile`+`verifyNamedStat` do alvo
  publicado; no cofre, `ensureTerminalArtifactObject` re-lê o objeto e re-verifica
  digest/size/mode pós-rename, e `ensureContentAddressedBytes` é CAS (colisão de path ⇒
  bytes idênticos por construção). O perdedor de qualquer corrida SEMPRE erra — nunca há
  aceitação silenciosa de bytes alheios. Semântica EEXIST preservada e classificada
  (`appeared-before-named-install`, `ErrTransactionRecoveryConflict`).
- Anti-simetria com linkat: hardlink publicaria atômico, mas com unlink=EPERM deixaria o
  alvo com nlink=2 — `transactionRegularStat` exige nlink==1 e envenenaria o produto para
  sempre. O rename emulado é a escolha correta neste mount.
- **DEFEITO REAL (corrigido):** qualquer falha entre criar o temp nomeado
  `.v2txn-install-*` e publicá-lo deixava o temp estrandado (unlink=EPERM), e
  `inspectTransactionArtifacts` (`transaction.go:3838`) classifica todo nome com
  `.v2txn-` não-tombstone como artefato **ATIVO** — bloqueando PARA SEMPRE reuse/apply
  (`transaction.go:747,823`) e aposentadoria de reservas
  (`transaction_reservation_retire.go:269-270`). Fix aplicado no worktree (Edit, sem
  commit): helper `retireOrphanNamedInstallTemp` (aposentadoria unit-keyed via
  `removeNamedByInodeCAS` — rename→hold→ftruncate→tombstone, sem unlink; CAS por inode
  preserva substituto concorrente; `errors.Join` nunca mascara o erro original) + defers
  em `publishNamedTransactionBytesExclusivePortable` (flag `published`),
  `createNamedTransactionInstallFile.fail` e `renameTransactionFileWithHooks`
  (flag `namedInstallPublished`). Validação: `go vet ./internal/v2ingest/` OK, `gofmt -l`
  limpo, testes focados (`SafeIO|Portable|NoReplace|Orphan|Retire|NamedInstall|Tombstone`)
  **ok 3.6s**. Tombstones minted em falha consomem orçamento generoso
  (`transactionMaxRetiredTombstones=65_536`).

## Item 4 — Gap de ciclo de vida: resolution fechada + página evolui = deadlock

**PROPOSTA (não aplicada), fecho sancionado:**

Causa confirmada em código: nenhuma lane refresca resolution — `PrepareForwardCandidates`
só refresca candidates/adoptions; o builder recusa explicitamente conversão implícita
(`forward_candidates.go:518` "forward candidate cannot be converted to existing-target
adoption implicitly"); o recut por proposta (`--build-proposal`) exige requirement
supersedido. Página sob resolution que muda 1 byte (mesmo campo mecânico) reprova o gate
inteiro (`contract.go:1054`) sem rota de reparo — exatamente o que forçou o hand-edit.

Desenho: novo modo `--refresh-resolutions` em `cmd/finalize-v2-semantic-recut` (plan/apply
com `--observed-by/--observed-at`, mesmo padrão do forward):

1. Para cada resolution cujo alvo não autentica mais: exigir linha viva ÚNICA no
   `target_rel_path` com o mesmo `intent_id` e `computeMaterialValidation` (pesquisa
   fechada) bem-sucedida.
2. **Invariante de validade da revisão:** refresh automático SÓ se
   `visible_text_sha256` E `official_sources_sha256` recomputados da linha viva forem
   IGUAIS aos gravados na resolution (mudança puramente mecânica/não-visível; é o caso
   needs_source_research/index_policy/publication_allowed de hoje). Divergência visível ⇒
   recusar e exigir `--re-reviewed-by/--re-reviewed-at` explícitos, que estampam revisão
   NOVA (nunca herdam a antiga silenciosamente).
3. Efeito: reescrever apenas `page_record_sha256` + `semantic_review_evidence.page_record_sha256`
   (e `computed_word_count` se recomputado igual), preservando reviewed_at/by/contract.
4. Instalação pela MESMA transação durável do forward (guards em todos os shards +
   contrato como commit marker) e **recibo próprio**
   (`v2_semantic_resolution_refresh_receipt_v1` com previous/updated contract shas e a
   lista de refreshes) — elimina para sempre a classe "recibo fantasma" do item 1.
5. Bônus recomendado: lane explícita fc→resolution (`--close-candidate --intent
   --reviewed-by --reviewed-at`) reutilizando `validateResolutionIdentity` +
   `computeMaterialValidation`, para que a conversão de hoje nunca mais precise de editor
   manual; e verificação de unicidade GLOBAL do intent na lane resolution (fecha a fresta
   3 do item 1).

## Observações fora de escopo direto

- `check-v2-supersession-integrity` **FALHA no worktree vivo agora** (6 issues
  `active_source_changed_without_provenance`: gloss-certidao-onus-reais,
  gloss-planejamento-sucessorio, pi-da-herdeiros, +3) — todos em arquivos com edição
  não commitada de outra frente viva (`portfolio_v2/glossario.jsonl`, `portfolio_v2/inpi.jsonl`,
  `v2_pages/glossario2-19.jsonl`; `cmd/generate-v2-portfolio-hint-normalize` também
  modificado). NÃO relaciona com os 2 intents auditados nem invalida `1622377a` (o hook
  valida a árvore candidata no commit); precisa de provenance/successor antes do próximo
  commit dessas frentes.
- Fila `5f1bb540` embute o contrato pós-hand-edit (`58a00afe…`, 3 ocorrências no diff) —
  a cadeia forward dos 109 lotes está pinada no estado vivo correto.
