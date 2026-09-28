# ANEXO DE EVIDÊNCIA POR SUBSISTEMA — Destrava da Fábrica (2026-07-22)

Anexo complementar de `PLANO_DESTRAVA_FABRICA_20260722.md`. **Não o contradiz**: consolida a
evidência por subsistema da auditoria em escala da fábrica, coletada por três grupos e já
**refutada adversarialmente** (só passam os sobreviventes às refutações). Cada mudança recebe uma
**tag de fase** (FASE 0/1/2) que a amarra aos marcos do plano-mãe — o anexo é *evidência A FAVOR*
do plano, não um plano rival.

**Disciplina de evidência (verificações ao vivo, 2026-07-22):**
- Âncoras `file:line` conferidas no disco. **Correção de âncora:** a síntese de grupo citou
  `internal/render/structured_data.go:696 (buildLegislationNode)` — esse arquivo **não existe** em
  `internal/render/` (só `render.go`, `area_hub.go`). A resolução de citação legal flui de fato por
  `internal/legalfacts/norma.go` (laço `ParseCitation`/`BuildURN`, L74-156) e a tabela de apelidos é
  `codigosCanonicos` em `internal/lexml/knowncodes.go:27` com `buscaPorApelido:118` chamando
  `dobraAcentos` (`internal/lexml/parse.go:366`). A âncora foi corrigida nas linhas abaixo.
- **Percentuais de CPU (47,7% / 45-53%) são reportados por profile** e não foram reproduzidos
  nesta sessão — tratados como *sinal de prioridade*, nunca como magnitude comprovada (as próprias
  sínteses já reprovaram "magnitudes fabricadas"; ver §3).
- **Reconciliação com o fato-vivo 11:37 do plano:** `check-v2-writing-semantic-contract` = VERDE
  (`cmd/check-v2-writing-semantic-contract`, importa `v2writingsemantic`). O binding
  `consumed==claims` / "unconsumed decisions" vive em **outro** pacote/gate
  (`v2supersessionintegrity`, `integrity.go:541-545`, `forward_evidence.go:352`; consumido por
  `cmd/check-v2-supersession-integrity` / committer / ingest). Portanto podar a entrada órfã (§2,
  item 4) **não altera** o número que o plano declarou verde.

Invariantes de conteúdo do §2 do plano-mãe (grounding, PT-BR, OAB, anti-dup<0.70, HTML leve, smoke
Googlebot, release transacional, autenticação por-SHA, grafo de link `Orphans==0 && Danglers==0`)
ficam **byte-idênticos** em toda mudança abaixo. O que muda é cerimônia de *processo*.

---

## 1. Tabela: subsistema → custo hoje → custo alvo → mudança-chave

| Subsistema | Custo hoje | Custo alvo | Mudança-chave (arquivo) |
|---|---|---|---|
| commit-verified / auditoria global | O(estoque) por commit; asserção `stock_pages==total` | O(delta) sobre shards do report; reconciliação full-stock assíncrona fail-closed | `tools/commit-verified-v2-workflow-results` `_run_private_global_audit` L4392-4454 |
| verify-v2-workflow-results | relê catálogo 250×/wave (~50MB); re-hash de todas as deps | itera só `claimed_set`; epoch statx (dev/ino/ctime_ns/size) | `tools/verify-v2-workflow-results` L2208-2251 |
| writing-mass (fila de escrita) | 1 batch stale derruba fila de 6.700 (throw) | dropar stale com motivo logado, rodar o resto; rerun re-tenta só dropados | `scripts/workflows/writing-mass.js` L391-438 |
| writing-review (finalizer) | serial, halt no 1º erro; teto `MAX_DRAFTS_PER_EPOCH=24` | pool paralelo de unidades disjuntas, no-halt; teto 24→31 (hard-max produtor) | `scripts/workflows/writing-review.js` L983,L1032-1104 |
| recut (rerun) | preflight resolvido → recusa → beco "porcelain esgotado" | proposal idempotente `AlreadyResolved` verificada por `verifyExactFinalStock` | `internal/v2semanticrecut/recut.go` L236,L469-473,L595 |
| wrapper de timeout Go | cap 540s rejeita passos de 900/1800s na validação de args (`exit=2`) | teto reconciliado ao p99 medido, gravando `duration_ms` real | `tools/run-go-cmd-cached` L39,L80,L543 |
| contrato semântico (unidade 969) | entrada órfã quebra `consumed==claims` no binding de integridade | podar a entrada órfã (dado); `consumed==claims` byte-idêntico | `v2supersessionintegrity/integrity.go` L541-545 |
| scaled verdict | O(N) full-stock por invocação | motor `incrementalverdict` por shard-fingerprint; `buildRecord` byte-idêntico | `cmd/generate-scaled-content-release-verdict/main.go` L78 |
| promoção pública | validação cumulativa O(N²) + render de sitemap incondicional | 4 índices (path+URL+intent+manifest) incremental; pular render se hash estável | `internal/publicrelease/publicrelease.go` L6015-6020, L821-822 |
| v2ingest / validateBatch | `validatePage` serial | pool NumCPU; single-thread só nas cruzadas globais (n-grama/heading) | `internal/v2ingest/validate.go` L161,L357,L407,L475 |
| auditor-canônico / load_portfolio | ~45-53% CPU do auditor (profile), 10k line-parses | sidecar por STAT; blob reduzido `{intent:(type,lane,area,family)}` | `tools/audit_v2_pages.py` L23123, L25074-25121 |
| render / resolução legal | ~47,7% CPU cumulativo (profile) renormaliza aliases por chamada | tabela `codigosCanonicos` pré-computada no `init()`; memo só de HIT | `internal/lexml/knowncodes.go` L27,L118 + `legalfacts/norma.go` L74-156 |
| render / build | rebuild O(corpus) mesmo sem mudança | build incremental por content-hash; manifesto de cache (dado) | `internal/build/build.go` L103-113 |
| checks-runner | re-audita full-corpus por gate | memo `{check, corpus_sha, hash-da-lógica}→verdict`; só shards alterados | `internal/checks` `sharedV2Corpus` L225-241 |
| httpserver / ondemand + locks | disco por request; locks órfãos root em /tmp | `sync.Map` por `pageCacheSignature`; PID-identity+stale-reclaim nos locks | `internal/ondemand/ondemand.go` L152-177,L253 |

---

## 2. TOP 12 mudanças (ordenadas por alavancagem/esforço)

Formato: **[FASE]** alvo — esboço — *verde*.

**1. [FASE 0 — pré-requisito de TODO commit] Unstage `_prototypes/**.go` + gitignore.**
`_prototypes/contrafactual_pruner/{main,sample}.go` estão STAGED (A); `tools/check-go-index-compile-closure`
os recusa corretamente (Go ignora dir `_`) → **bloqueia todo commit do repo**. Unstage por pathspec +
`.gitignore` `_prototypes/**.go`. *Verde:* `check-go-index-compile-closure` verde; commit flui.

**2. [FASE 0 — destrava lock] Remover/reclamar lock root em /tmp.**
`/tmp/opt-wiki-v2-civil-verify-*.transaction.lock` são `root:root` (uid rafael → EACCES = deadlock).
Reclamar/remover os órfãos; fix estrutural vira o item 12. *Verde:* zero lock root-owned; verify-civil
adquire lock. (Confirmado ao vivo: 10+ locks `root:root` de 20-jul 14:12.)

**3. [FASE 0 — destrava bootstrap-chain passo 12] Reverter o cap 540s ao p99 medido.**
`tools/run-go-cmd-cached` `MAX_WRAPPER_TIMEOUT_SECONDS=540` (regressão de `dad121a3`) rejeita na
VALIDAÇÃO DE ARGS (`L80,L543` "must not exceed 540s", `exit=2`) passos com default 900/1800s — o passo
nunca executa. Elevar o teto ao p99 MEDIDO gravando `duration_ms` real (não inflar timeout de código
lento). *Verde:* `bootstrap-chain --from 12` fecha passos 12-13 a N=590 com `duration_ms < budget`.

**4. [FASE 0/1 — caminho crítico da 1ª publicação; plano causa #1/#3] Podar a entrada órfã do contrato semântico (DADO, não gate).**
A refutação PROVOU que relaxar `consumed==claims`→`claims⊇consumed` é fraude (reabre replay
cross-transação; full-consumption é intencional). O sobrevivente é **apagar a entrada órfã** (decisão
sem consumidor) pela rota sancionada — `consumed==claims` fica byte-idêntico, **nenhum Go editado,
nenhum gate relaxado**. Alvo do binding: `v2supersessionintegrity/integrity.go:541-545`,
`forward_evidence.go:352`. Alinha-se à causa #1 do plano (órfã da unidade 969 sem rota de rerun) e à #3
(closure de âncoras à mão). *Verde:* `check-v2-supersession-integrity` fecha sem `unconsumed decisions`
/ staged órfã; `check-v2-writing-semantic-contract` **segue verde** (gate distinto, item de reconciliação).

**5. [FASE 1 — 1 linha] Elevar `MAX_DRAFTS_PER_EPOCH` 24→31.**
`scripts/workflows/writing-review.js:983`; 31 = hard-max do produtor
(`MAX_EXACT_COMPONENT_WAVE_MEMBERS=31`, `generate_v2_review_queue.py:89` — confirmado). Menos epochs =
menos regen de fila. *Verde:* até 31 shards/invocação, sem estourar o hard-max.

**6. [FASE 0 — destrava fila de 6.700] Filtrar-em-vez-de-throw na fila de escrita.**
`writing-mass.js:391-438` (`unsafeBatch`→`throw`, confirmado). Validar cada batch, DROPAR os stale com
motivo logado, rodar os válidos; rerun idempotente re-tenta só os dropados. (Ganho real = poupar o bloco
REGRAS 1-9 ~16KB/launch; comandos CAS/preflight NÃO saem.) *Verde:* 1 batch drifted não derruba a fila;
verdicts do auditor Python inalterados.

**7. [FASE 1] Finalizador de review assíncrono + no-halt.**
`writing-review.js:1032-1104` (finalizer serial). Rodar as unidades PROVADAMENTE resource-disjuntas
(L949-976) em pool limitado e NÃO halt no 1º erro (coletar falha, seguir disjuntas). *Verde:* stall
isolado não desperdiça o epoch; verdicts inalterados.

**8. [FASE 1 — plano causa #1] Rota de rerun sancionada no recut.**
`recut.go` `BuildProposalFromCurrent:236`; quando `preflight.Resolved`, retornar proposal idempotente
`AlreadyResolved` verificada por `verifyExactFinalStock:595` (padrão já vivo em `prepareParsed`,
`L469-473` confirmado); ler `ReviewedAt/ReviewedBy` de `contract.resolutions`, não de params frescos
(senão falha fechado). Fecha o beco "porcelain esgotado" (plano causa #1). *Verde:* rerun idêntico =
no-op provado (nunca envelope fabricado / página órfã). Adjacente ao generation-aware `6e69183b` e ao
`unit_key` ao vivo — coordenar para não colidir.

**9. [FASE 2 — profile ~47,7% CPU render] Hoist de `codigosCanonicos` no `init()` + memo de resolução legal.**
`internal/lexml/knowncodes.go:27,118` (tabela `codigosCanonicos` + `buscaPorApelido`, hoje re-dobra
acentos por chamada) — pré-computar a tabela dobrada no `init()`; e `sync.Map[urn]→url` package-level em
`legalfacts/norma.go:74-156`, **cacheando SÓ HIT** (Store só com `ParseCitation` ok; senão suprimir a lei
do corpus inteiro). *Verde:* bench many-citations cai (profile); JSON-LD/HTML **byte-idêntico**; parse-fail
segue reavaliado.

**10. [FASE 2 — profile ~45-53% CPU auditor] Memoizar `load_portfolio` por STAT.**
`audit_v2_pages.py:23123` + padrão `_shard_cache_identity/_store_shard_sidecar:25074/25121` (confirmados).
Sidecar chaveado por STAT de `portfolio_v2/*.jsonl` (NÃO por content-fingerprint — acopla caches); 1
`json.load` de blob reduzido vs 10k line-parses; re-derivar só shard com stat mudado. *Verde:* cProfile —
`load_portfolio` deixa de ser #1; veredito idêntico ao parse completo; flat a 100k/1M.

**11. [FASE 1/2 — chokepoint O(N) do verdict] Plugar o motor `incrementalverdict`.**
`cmd/generate-scaled-content-release-verdict/main.go:78` → `internal/incrementalverdict` (existe,
`seamsource.go`, `ShardKey` L28) + `scaledcontentreleaseverdict/incremental_seam.go` (existe). Construir o
`ShardKey` draftID→shard e drenar por shard-fingerprint; `buildRecord` byte-idêntico (zero nova superfície
anti-fraude). *Verde:* `TestIncrementalSeamMatchesWholeStock`
(`incremental_seam_whitebox_test.go:53`, existe) roda contra os 590 REAIS e bate byte-a-byte; editar 1
shard reconstrói só D shards.

**12. [FASE 2 — maior alavanca de escala] Auditoria global O(delta) por-commit no committer.**
`commit-verified-v2-workflow-results` `_run_private_global_audit:4392-4454` + `audit_v2_pages.py:25959`.
Religar a primitiva JÁ existente `fail_closed_incremental_distinctness` no lugar do batch full-stock;
auditar só páginas dos shards em `report.files` contra o store content-addressed (revalidado fail-closed a
cada hit); trocar `inventory_complete/stock_pages==total` por reconciliação full-stock **assíncrona/
periódica**. *Verde:* verdict de distinctness IDÊNTICO ao full-batch numa amostra; anti-dup<0.70 preservado;
commit de poucos shards deixa de ser O(estoque). **Ressalva:** a reconciliação async tem de ficar
fail-closed (mudança security-relevant — desenhar com cuidado).

### Sobreviventes limpos abaixo do corte (menor alavanca ou dependentes — nada se descarta)
- **[FASE 1/2] verify-v2 O(delta):** iterar só `claimed_set` + epoch statx (`verify-...:2208-2251`).
  Verdict inalterado; TOCTOU ainda pego por ctime.
- **[FASE 2] publicrelease cumulativo O(delta):** 4 índices em contentstore/bbolt + pular
  `renderSitemapShardsForPages` quando `reuseExistingHashes && hash!=""`. **Não é opcional — é o consumidor
  das coortes do item 11** (ver §4); fica abaixo do corte só por depender do item 11.
- **[FASE 2] validateBatch paralelo:** pool NumCPU em `validatePage` (puro), single-thread nas cruzadas
  globais (`validate.go:357,407`). Verdicts idênticos ao serial; anti-dup global inalterado.
- **[FASE 2] build incremental por content-hash** (`build.go:103-113`); cache é DADO. HTML byte-idêntico.
- **[FASE 2] checks-runner memo de veredito** (`internal/checks`); chave OBRIGATÓRIA inclui
  hash-da-lógica-do-check (sem ele = falso-verde = fraude).
- **[FASE 2] httpserver ondemand + locks self-healing** (`ondemand.go:152-177`); SEMPRE revalidar
  `CoverageCache.Validate` por request (nunca curto-circuitar o no-orphan); portar PID-identity+stale-reclaim
  aos `*.transaction.lock` (fix estrutural do item 2).

---

## 3. O que cai (cerimônia refutada — uma linha cada)

**Falsos ganhos de escala (já em produção ou vaporware):**
- writing-contract "índice ngram O(delta) against-stock": JÁ em produção (Pebble incremental); o scan O(N) legacy nem é chamado.
- review-queue-producer "índice por `mtime_ns/size`": `mtime_ns` forjável e colidível → fura fail-closed anti-fraude; `intent_id` global segue O(N).
- ancoras-semânticas "índice via `TransactionGuardFingerprint`": fingerprint é de DIRETÓRIO (sha256 nome+tipo); não detecta shard reescrito in-place → índice stale aprova duplicata.
- "Cache de `loadSourceRepository` por `TransactionGuardFingerprint`": serve índice STALE sob fail-closed; commit já testou+rejeitou ("pular revalidação = fraude").
- "Manifest de âncoras assinado": vaporware (sem PKI). Sobrevive só como pluralizar 2 singletons → matar deadlock de build.
- verifier "deletar merit/stock morto": NÃO é morto — tripwire; `TestV2WorkflowCommitClosureUsesPrivatePlumbingCAS` EXIGE `count==1`. Manter.
- "O(delta) por herança de shard no ingest": Rewrite zera `existing=nil` → seed n-grama MORTO; ganho "segundos", não sub-segundo.
- "Colapsar re-parse no ingest": `validatePreparedTransactionPayloads` lê `projectRoot` REAL (anti-TOCTOU); colapso total abre fraude.
- httpserver "offset lazy `pagesByURL`": cópia Go é rasa; "1-5GB" inflado ~25-30× (real ~37MB); teto O(N) real é UPSTREAM em `content.LoadRepository`.

**Falsas remoções de gate (matam invariante):**
- Relaxar `consumed==claims`→`claims⊇consumed`: reabre replay cross-transação. Substituído pelo item 4 (prune de dado).
- precommit B: content-only já dá SKIP antes da dupla-auth (enfraquecer = regressão sem ganho).
- precommit C: regex `\.go$` é fail-OPEN; `//go:embed` pularia o gate → build quebrado.
- precommit A (escrito): exige parser require/replace inseguro; sobrevive só reverse-closure de `require`.
- locks "remover engineering-now-contract do RunAll": mata o gate anti-fraude `validateContractDeclaredMaterialArtifacts`. Sobrevive só limitar o que o check LÊ (janela incremental), nunca truncar o ledger.
- locks "tombstone sha puro": regride (EEXIST na 2ª retirada legítima esgota loop 128→abort). Manter sufixo random.
- render "sitemap tolerante": confunde fora-do-sitemap com fora-da-publicação. Sobrevive só acumular `LocError` mantendo `report.Passed()==false`.
- auditor "deaccent por página": já é 1×/página; redundância real é por-CAMPO.
- checks "prewarm concorrente": BUG — roda antes de `setFrozen`, concurrent map writes → fatal throw que `recover()` NÃO captura.

**Especulação / flags inexistentes / cadeia intencionalmente linear:**
- review-queue "deadlock em `authenticate_superseded_evidence`": função linear, sem locks/threads.
- "Paralelizar passos 4-7 do bootstrap": passo 6 DEPENDE de 4+5 (`quality_vectors.go:577-586`).
- "`--changed-shards`/`--since-receipt`": flags NÃO existem; dirty-set entre 13 estágios é subsistema novo.
- "Skip por `--prior-evidence`": `bootstrap-step-receipts:938-941` REJEITA saída inalterada; chave mais fraca que `source_contract_sha256`.
- "Fan-out dos oráculos 14-31": `require_predecessor:756-778` exige cadeia LINEAR (ledger tamper-evident, não DAG).

**Magnitudes fabricadas (o O(N) qualitativo sobrevive; a escala do problema cai):**
- "166MB / 282KB-por-registro / 28GB / 8-9h" — real ~15-22 KB/registro.
- "20/80 rps / 83min" — nenhum evidence grava timing.
- Inventário "668/549/119/~22%" — snapshot obsoleto (migração posicional→pinned ao vivo ~44%); `.stale-cas-displaced` é GC de retenção, não drift.
- Committer "Go 5min→~0": GOCACHE já persistente; custo real é untar do toolchain ~9-13s + link.

---

## 4. Mapa de dependências

- **Pré-requisito de TUDO:** itens 1 e 2 (unstage `_prototypes` + limpar lock root) precedem QUALQUER
  commit / verify. São FASE 0 imediata.
- **Itens 12 e "verify O(delta)" compartilham o store content-addressed de distinctness**
  (`internal/v2pagedistinctness`/Pebble; catch-up `factory index-distinctness --require-exact` em
  `verify-v2-workflow-results:1734-1747`). Ambos dependem desse store seguir sendo a autoridade e o
  catch-up permanecer fail-closed — é a âncora que torna o incremental seguro (a mesma que refuta
  "writing-contract A").
- **Item 3 (cap 540s) é pré-requisito do item 11 (`incrementalverdict`):** o verdict é o passo 41 da
  bootstrap-chain; sem destravar o cap a cadeia morre no passo 12 e o motor nunca é exercitado
  end-to-end a N≥590.
- **Item 11 → publicrelease cumulativo (ordem de pipeline):** verdict/manifest produz as coortes que a
  promoção consome; o item 11 deve fechar o consumo de `InputFingerprintSHA256` em `approval.go:404`
  (anti-drift grant↔promoção) ANTES de substituir o fingerprint uniforme. Por isso publicrelease fica
  "abaixo do corte" — é **dependente**, não opcional.
- **Item 11 e publicrelease compartilham infra:** ambos precisam do content-store por-shard
  (`incrementalverdict` já usa) — construir no 11 e reusar no snapshot 4-índices.
- **Itens 6 e 7 (writing-mass / writing-review) são independentes** entre si e do resto, executáveis HOJE
  (`scripts/workflows`); o item 7 acopla ao hard-max 31 do produtor (item 5).
- **Item 8 (recut)** é Go standalone, adjacente ao generation-aware `6e69183b` já pousado e ao `unit_key`
  ao vivo — coordenar para não colidir.
- **Itens 9, 10, build incremental e httpserver são paralelizáveis** entre si (lexml+legalfacts / python /
  build / ondemand). Itens 3+4 (checks memo) compartilham o padrão "chave = content-hash + versão-da-lógica";
  o memo de checks SEM hash-do-checker é fraude (dependência interna obrigatória).
- **CRÍTICO transversal — EDIÇÃO CONCORRENTE agora:** `relaunch-writing.sh`, `writing-mass-full.js`,
  `commit-verified-v2-workflow-results`, `transaction_safe_io.go` e `generate_v2_review_queue.py` estão sob
  M/diff ao vivo (processos sob `flock`). **Coordenar via bus de arquivos** (`.agents/runtime/coordination/`)
  antes de tocar; edição pontual que preserva escrita concorrente; nunca duplicar o que já está em voo.

---

**Fecho.** Nenhuma das 12 mudanças toca a fronteira anti-fraude nem os gates de conteúdo do §2 do
plano-mãe. Nenhuma, sozinha, entrega os 10k — isso depende de o `published_manifest` ser populado
(FASE 0 do plano, Marco 0b). Este anexo é o *como* por subsistema; o *quando* e o *caminho que publica
hoje* seguem governados por `PLANO_DESTRAVA_FABRICA_20260722.md`.
