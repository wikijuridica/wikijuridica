# PLANO DE DESTRAVA DA FÁBRICA — 2026-07-22

Objetivo: publicar as primeiras páginas jurídicas HOJE (`published_manifest>0`), escalar para
milhões depois, sem tocar nenhum gate de conteúdo. Une o Relatório A (atrito da cadeia) e o
Relatório B (arquitetura alvo). Regra de ouro deste plano: **o caminho que publica hoje vence
o caminho perfeito**; toda cerimônia que não protege invariante morre, tudo que protege vira
O(delta)/idempotente/assíncrono — nunca é eliminado.

> Fato vivo verificado em 2026-07-22 11:37 (decisivo, reorganiza o ranking dos relatórios):
> `./tools/go-modern run ./cmd/check-v2-writing-semantic-contract` = **VERDE, EXIT=0**
> (`requirements=21 resolutions=5 unresolved=16 dependencies=679 evidence_files=2
> owners_absent=0`). A evidência **reconstrói agora**. Portanto a tese "falta 4ª âncora /
> regenerar o archive de 21 preimages" (Relatório B, passo 1) está **STALE** para o estado
> atual — vira contingência do ramo RED, não o primeiro passo. O bloqueio real é o do
> Relatório A: **consumo single-use do canal de pouso + índice limpo**.

## 1. Diagnóstico — as 5 causas dominantes (file:line)

1. **Consumo single-use do canal de pouso.** A closure do `commit-verified --kind
   semantic-recut` foi consumida por `aff5fd7e`; a unidade de 969 arquivos ficou órfã e o
   rerun não tem rota sancionada ("porcelain esgotado por design", RCA_D48 §4.4:142-149;
   terminal `<fp>.terminal.json` em `commit-verified-v2-workflow-results:919,:1191`).
2. **Identidade da unidade presa a HEAD e declarada à mão.** O committer já computa
   `_singleflight_fingerprint` (`:933-969`) mas mete `expected_head` na *identidade* (`:948`),
   então rerun idêntico é invisível e o lock morre com a sessão (RCA §4.1:104-117).
3. **Closure declarada à mão em 4 âncoras com regra delta-vs-HEAD.** `SEMANTIC_FIXED_CLOSURE`
   + `SEMANTIC_DELTA_REQUIRED_ANCHORS={contract,receipt}` (`:172,:186`); o committer exige
   índice LIMPO das âncoras não-staged na transação inteira (`:3115-3128`) → dirty concorrente
   falha. A atomicidade real, porém, já vem do CAS `commit-tree`+`update-ref`.
4. **Validação O(N) full-corpus por gate/ingest.** `AuditRepository` relê 671 shards e reporta
   só `Issues[0]` (`internal/v2ingest/main.go:253`, 133s [M]); `bootstrap-chain` tem teto
   TOTAL de 600s (`:289`) com passo que custa até 540s → a cadeia não fecha numa invocação;
   `verify-v2-workflow-results` re-audita full por wave.
5. **Release por invocações manuais.** `P0ReleaseCohortMaxRecords=250`
   (`internal/publicrelease/publicrelease.go:72`, env `WIKI_PUBLIC_RELEASE_COHORT_MAX`) é
   trilho de segurança legítimo, mas exige ~28 invocações manuais do promoter para 6.846,
   cada uma refazendo preflight sobre o manifest inteiro.

Padrão transversal (RCA §4): nenhuma unidade tem `unit_key` computável → "valida o mundo,
para no 1º erro" gerou 5 quebras em série; cada erro exigiu re-run completo para achar o
próximo.

## 2. INVARIANTES preservados (lista fechada — NADA aqui muda)

- **Grounding**: fonte oficial é proveniência, nunca corpo; proibido scraping/cópia/paráfrase
  mecânica; proibido inventar lei, ementa, artigo, data ou resultado.
- **PT-BR** natural e acentuado em todo texto visível (os 13 oráculos do bootstrap cl.2).
- **Ética OAB** Provimento 205/2021 (sóbrio, sem promessa de resultado, sem captação indevida);
  autor via `content/site.json`.
- **Anti-template / anti-dup**: similaridade semântica de corpo < 0.70.
- **HTML leve**: ≤ 50 KB, zero `<script>`/JS/wasm, title/meta/H1 únicos, canonical/robots/
  sitemap coerentes; mesmo conteúdo ao Googlebot sem custo de render.
- **Release transacional**: staging, SHA-256, lock, ledger, rollback, smoke HTTP/Googlebot.
- **Autenticação por-SHA dos bytes staged** (`internal/v2writingsemantic/contract.go:493-1032`)
  — fica byte-idêntica.
- **Grafo de link interno**: `Orphans==0 && Danglers==0`
  (`internal/v2internallinkgraph/graph.go:1016`).

Nenhuma mudança das Fases 0–2 toca esses gates: são todos gates de *conteúdo*; o que muda é
cerimônia de *processo* (identidade, consumo, agendamento, build).

## 3. FASE 0 — HOJE (pousar os 969 staged + 1º cohort público)

Dois marcos. **0a** pousa a unidade de 969 arquivos staged (transação semantic-recut). **0b**
leva o estoque ao primeiro `published_manifest>0`. Critério de verde da Fase 0 inteira =
**`published_manifest>0`**. Todos os passos: `dono=maestro`.

### Marco 0a — pousar os 969 staged

- **0a.1 — Confirmar o gate de conteúdo (FEITO/VERDE hoje).**
  `./tools/go-modern run ./cmd/check-v2-writing-semantic-contract`.
  *Verde* = EXIT=0, `owners_absent=0`, evidência reconstrói (confirmado 2026-07-22 11:37).
  *Ramo RED (contingência, NÃO o caminho de hoje)*: se um dia reprovar "does not reconstruct
  source" (`contract.go:1017`), **regenerar via produtor sancionado**
  `./tools/generate-v2-supersession-forward-evidence` e stage como âncora (o committer aceita
  âncora staged pelo ramo `:3106-3108`) — **NUNCA fabricar envelope à mão** (= páginas órfãs,
  proibido).
- **0a.2 — Garantir índice limpo das âncoras fixas.** O committer exige `index_entry==HEAD`
  para authority+evidence não-staged (`:3115-3128`).
  `git status --short data/editorial/v2_semantic_superseded/writing-semantic-recuts-20260715.jsonl data/ops/v2_supersession_independent_reviews_20260716.jsonl`.
  *Verde* = âncoras não aparecem sujas por escrita concorrente.
- **0a.3 — Rodar a transação de pouso pela ROTA HONESTA (RCA §4.4:156), não por fabricação.**
  `./tools/commit-verified-v2-workflow-results --kind semantic-recut` sobre a fila re-derivada
  do portfólio (contrato+recibo já staged; páginas staged; evidência no HEAD limpa).
  *Verde* = commit CAS criado, os 969 arquivos pousam, os `.v2txn-retired-*` e os
  `.tombstone-aereo-*` deixam de ser órfãos.
  *Ramo RED (single-use consumido)*: se o committer recusar por `unit_key`/terminal já
  consumido, aplicar **o mínimo do §4.1** — declarar delta causal (novo `input_oids` da fila
  re-derivada ou novo epoch de código) e gravar em `.agents/runtime/unit-ledger.jsonl` — para
  re-executar COM delta. **Jamais `--no-verify`, jamais `git reset/restore`, jamais envelope
  à mão.**

### Marco 0b — primeiro público

- **0b.1 — Ingest WRITE-FULL.** `./tools/go-modern generate ./internal/v2ingest` →
  `./tools/ingest-v2-stock` **sem `--prepare-only`**. *Verde* = transação durável, corpus
  ingerido, zero Issues de supersessão.
- **0b.2 — bootstrap-chain em blocos.** `./tools/bootstrap-chain --from <passo> --until <passo>`
  em janelas curtas (LanguageTool em `:8082` no ar). *Verde* = `verdict_passed>0`.
- **0b.3 — Promover 1 cohort de 250.** `./tools/run-promote-cohort-loop --execute` para UM
  cohort (cap 250 intacto). *Verde* = **`published_manifest>0`** — primeiro público.

## 4. FASE 1 — ESTA SEMANA (matar single-use e deadlock; O(delta); release contínuo)

Design por arquivo. Cada mudança preserva os gates de conteúdo (§2).

- **`tools/commit-verified-v2-workflow-results` — identidade derivada + unit-ledger (RCA §4.1/4.3/4.4).**
  Dropar `expected_head` da identidade (`:948`): HEAD vira **pré-condição CAS**, não identidade.
  `unit_key = sha256(kind + queue + sorted(input_oids) + epoch_do_código)`. O
  `<fp>.terminal.json` (`:919,:1191`) vira **`.agents/runtime/unit-ledger.jsonl` append-only**.
  Guard: `unit_key` terminal-**success** ⇒ no-op idempotente; `input_oids`/epoch novo ⇒
  `unit_key` novo ⇒ pousa; falha-transiente ⇒ retry até `max_attempts` e então circuit-open
  (§4.3) — distinguir os dois evita órfão novo. Closure **DERIVADA**: as 4 âncoras viram
  dependências computadas ligadas ao seu OID onde estiver (staged se mudou, HEAD se não),
  aposentando `SEMANTIC_DELTA_REQUIRED_ANCHORS` (`:186`). Tombstones passam a ser nomeados por
  `unit_key` (fim do nome aleatório em `internal/v2ingest/transaction_safe_io.go:1142`).
- **Validação O(delta) — attestation herdada por OID.** Generalizar o memo já provado
  (`TestSemanticSuccessorMemoRevalidatesAdulteratedDependency`) para uma attestation por página
  `{page_oid, gate_version, verdict, dep_oids, dep_hashes}`; chave de cache
  `(page_oid, gate_version, sorted(dep_oids+hashes))`; **fail-closed** (ausente/adulterada ⇒
  recompute; bump de `gate_version`/epoch ⇒ recompute). Aplicar em: `AuditRepository`
  (`main.go:253` — audita só shards com fingerprint novo **e reporta TODAS as issues**), os 13
  oráculos PT-BR, legal-signature, grounding, OAB, e `verify-v2-workflow-results` (memo keyado
  no hash que o **próprio** verificador recomputa — nunca no `audited_sha256` do writer).
- **`tools/bootstrap-chain` — fan-out + O(delta).** Fan-out das 13 classes independentes que
  leem o mesmo `refined` (padrão `RunAll SetLimit 6` já provado em `c88c15ed`); processar só
  shards com delta; **teto POR-PASSO**, não o teto-total de 600s (`:289`) que trunca a cadeia.
- **`internal/publicrelease` — drainer contínuo.** **NADA muda no swap atômico.** Adicionar um
  entrypoint drainer de longa duração que itera `ExecutePromotionSwapPlan` em lotes ≤250, cada
  lote com sua transação+receipt+rollback e append no release-ledger, até
  `published_manifest==target`. Restrição inegociável: o drainer **loteia componentes conexos
  de link** (respeita `Orphans==0 && Danglers==0`, `graph.go:1016`), nunca FIFO cego. Cap 250 e
  rollback atômico permanecem.
- **Reportar-tudo (cross-cutting).** Geradores/`generate_v2_review_queue.py` (5845L) **acumulam
  defeitos e emitem manifesto único** em vez de parar no 1º erro. Não relaxa gate nenhum: um
  pass revela as N causas, reduz N ciclos de descoberta a 1.

## 5. FASE 2 — ESCALA (milhões; só o que morde além de 10k)

- **Archive congelado → ledger append-only content-addressed.** Trocar o snapshot single-use
  com freeze whole-file + `checked_at` hardcoded (`contract.go:1010`) por um ledger append-only
  onde o gate liga por **pertinência** ("o preimage deste requisito existe no ledger com SHA
  por-registro batendo", `contract.go:1032`), não por identidade whole-file. Uma geração nova só
  *appenda* seus preimages. Preserva `page_record_sha256`/`visible_text_sha256` por shard
  (`:855-871`); descarta só o freeze de arquivo inteiro.
- **Cross-page dedup/similaridade incremental.** Bucket LSH por shard: re-bucketiza só os OIDs
  que mudaram, em vez de O(N²) de pares a frio.
- **Build-tag nos dev-mains.** `//go:build devcmds` nos ~259 dev-`cmd/` + isolar bleve/arrow
  atrás de tag → a closure de um commit Go pequeno encolhe de 504 pacotes para o fecho do
  pacote tocado. Regra operacional: **o canal de pouso de dado NUNCA staged Go junto** — dado e
  Go em commits separados, dado nunca espera build.
- **HEAVY_AUDIT_LOCK — seção crítica curta.** Segurar o `flock` só na fase build/CAS; auditoria
  read-only fora do lock, com revalidação de fingerprint na entrada (RCA §4.2).
- **Dedup de compilação.** `pre-commit` e `commit-verified` compartilham o receipt de compilação
  por OID, evitando o 2º cold build (~0,5 GiB).

## 6. O QUE MORRE (cerimônia eliminada — e por que nenhum invariante depende dela)

- **Consumo single-use do pouso** → `unit_key` idempotente. A atomicidade sempre veio do CAS
  `update-ref`, não do consumo. Nenhum invariante depende.
- **`expected_head` na identidade da unidade (`:948`)** → vira pré-condição CAS. Atomicidade
  preservada; identidade passa a ser o conteúdo (`input_oids`).
- **Distinção delta-required-vs-HEAD (`:186`) e closure de 4 âncoras à mão** → closure derivada
  do conteúdo. A autenticação por-SHA (`contract.go:493-1032`) fica intacta.
- **Freeze whole-file + `checked_at` do archive (`contract.go:1010`)** → ledger append-only. O
  SHA por-registro continua autenticando cada preimage; página stale não cavalga.
- **Recompute full-corpus por gate** → attestation por-OID, recompute só no delta, fail-closed.
  Nenhum gate relaxado (ausente/adulterada ⇒ recompute).
- **28 invocações manuais do promoter** → drainer contínuo. Cap 250 e rollback atômico ficam.
- **Religação de 259 dev-mains em commit de dado** → build-tag. Dado nunca espera build.
- **Tombstones anônimos (`transaction_safe_io.go:1142`)** → nomeados por `unit_key`; GC sob
  fronteira exclusiva (nunca unlink concorrente).
- **"Para no 1º erro"** → manifesto acumulado. O gate não afrouxa; só se descobrem as N causas
  em 1 pass.

**Por que é seguro:** todos os itens acima são cerimônia de *processo* — identidade, consumo,
agendamento, build. Os gates de *conteúdo* do §2 (grounding, PT-BR, OAB, anti-dup<0.70, HTML
leve, smoke Googlebot, rollback, proveniência por claim) ficam byte-idênticos. O fio condutor
único é executar o `unit_key`/unit-ledger já escrito na RCA §4.1-4.4 como guard transversal:
é rodar o plano existente, não inventar arquitetura nova.
