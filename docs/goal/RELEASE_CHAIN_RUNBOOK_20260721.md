# RELEASE_CHAIN_RUNBOOK — pré-flight verificado da cadeia b4→b6 (2026-07-21)

> Gerado por investigação read-only (sessão goal P0, evidência arquivo:linha).
> Sequência pós-pouso da unidade v2: go generate v2ingest → ingest WRITE-FULL →
> bootstrap-chain (42 passos, verdict no 41) → cohort ≤250 → promote --allow-public-write.

# PRE-FLIGHT PROMOÇÃO PÚBLICA — mapa acionável

## (1) Artefatos/gates verdes exigidos pela promoção
Fluxo em `cmd/promote-authorial-mass-public-release/main.go:315-379` (`runWithStockFreshnessValidator`), na ordem:
- **Stock freshness (v2 epoch)** — `main.go:317` `v2ingest.ValidateInstalledCanonicalStockSnapshot`; gate `main.go:460` (revalida antes do write, `:361`). Exige receipt `data/ops/v2_ingest_transaction_receipt.json`.
- **Manifest transaction validado** — `main.go:321,488` `authorialmassmanifesttransaction.ValidateAndLoadRecords` (lê `authorial_mass_manifest_transaction_rehearsal.jsonl`, `..._body_section_chunks.jsonl`).
- **Cohort progressivo** — `main.go:381-454`; casa `published_manifest.jsonl` atual == `--expected-current` (`:390`), delta ≤ `P0ReleaseCohortMaxRecords` (`:441`), estoque elegível suficiente (`:447`).
- **Preflight de transação** — `main.go:341` `publicrelease.ValidateCohortTransactionPreflight`.
- **Staging** — `main.go:344,348` `PrepareStagingTransactionPlan`/`MaterializeStaging` (hashes SHA-256; `.release-staging/promotion_manifest.json`, status `promotion_prepared_blocked_by_default` `publicrelease.go:57`).
- **Promotion plan + temp public + smoke HTTP/Googlebot** — `main.go:351,355`; smoke em `publicrelease.go:2613 ValidateTemporaryPublicHTTPSmoke` e robots/identity Googlebot `:1435`.
- **Verdict** — `main.go:358` `scaled_content_release_verdict.jsonl`; passado como `ApprovalVerdictPath` e `ExpectedApprovalVerdictRecords: targetN` (`:373-375`); approval revalida verdict em `approval.go:33,86`.
- **Swap + promotion_lock + release evidence** — `main.go:365,369` `BuildPromotionSwapPlan`→`ExecutePromotionSwapPlanWithOptions`; lease exclusivo `public_state_lease.go:11`; lock fases `approval_prepared`/`public_write_authorized` (`publicrelease.go:59-60`).
- **artifact_claims** — `main.go:98,126` exige claims p/ `public/`, `content/pages.json`, `data/editorial/published_manifest.jsonl`, `.release-staging/promotion_manifest.json`, todos com flags fechados (`publication_allowed=false`, `index_policy=noindex` `:291`) — o wrapper monta isso.

## (2) `public_release_promotion_blocked_by_default`
Vive em `internal/publicrelease/publicrelease.go:1298` (promotion), `:3745` (swap execution), `:3647` (recovery), `:4545` (rollback). Destrave legítimo ÚNICO: `PromotionExecutionOptions.AllowPublicWrite=true` (`publicrelease.go:3737` `if !options.AllowPublicWrite`), setado por `--allow-public-write` (`main.go:73,370`). Sem a flag a chamada é read-only e sempre retorna o blocker. Reflexo em `controlled_promotion.go:326,349,360,569`. Não existe `cmd/approve-public-release` — a aprovação é interna (`approval.go`), disparada pelo mesmo run com a flag.

## (3) Cadeia b4→b6 (confirmação de existência e ordem)
Fonte: `CHECKPOINT.md:13`. Comandos existem:
- **b4 ingest WRITE-FULL**: `go generate ./internal/v2ingest` (target `internal/v2ingest/validator_fingerprint_graph.go:53`) → `./tools/go-modern run -tags devcmds ./cmd/ingest-v2-stock` **sem `--prepare-only`** (WRITE-FULL = `Commit: !prepareOnly`, `cmd/ingest-v2-stock/main.go:133,188`). `--prepare-only` é dry-run.
- **b5 bootstrap-chain**: `tools/bootstrap-chain` existe (42 passos, `--list/--from/--until/--from N`); passo 41 = `generate-scaled-content-release-verdict`, 42 = manifest-transaction. Verdict ANTES do manifest (ordem provada).
- **verdict>0**: checar `data/editorial/scaled_content_release_verdict.jsonl` (`tools/check-scaled-content-release-verdict --timings`).
- **b6 cohort ~250 → promote**: `tools/run-promote-authorial-mass-public-release --allow-public-write --expected-current-manifest-records=N --expected-manifest-records=N+250` OU driver `tools/run-promote-cohort-loop --target 6846 --step 250 --execute` (default dry-run; `--execute` encaminha `--allow-public-write`, lê manifest vivo a cada passo, idempotente).

`TARGET_N` canônico = **6846** (`stock_manifest.json` drafts_expected=6846, expansion=0; wrapper `run-promote…:16-27`), NÃO 10000 (DEC-014).

## (4) Riscos de estouro (N≈7.6k)
- **bootstrap-chain passos 12-31** (prose candidate/refined + oráculos PT-BR full-corpus + semantic cluster): custo >5min cada em N-produção. Rodar em blocos `--from/--until`, nunca full-tree num disparo; LanguageTool :8082 precisa estar UP (CHECKPOINT.md:13).
- **verdict (passo 41)**: exige oráculos em modo RELEASE full-corpus, não amostra (STATUS.md:233) — se stale, verdict=0/N.
- **promote budget**: `WIKI_HEAVY_BUDGET_MS=180000` / `TIMEOUT_SECONDS=180` (wrapper). Um único shot só move ≤250 (`P0ReleaseCohortMaxRecords=250`, `publicrelease.go:72`, env `WIKI_PUBLIC_RELEASE_COHORT_MAX`). 6846/250 ≈ **28 cohorts** — usar `run-promote-cohort-loop` (serializa, retoma).

## RUNBOOK exato pós-pouso v2
```bash
cd /opt/wiki
# b4 — ingest WRITE-FULL
./tools/go-modern generate ./internal/v2ingest
./tools/go-modern run -tags devcmds ./cmd/ingest-v2-stock        # SEM --prepare-only
# (garantir LanguageTool :8082 up antes da cadeia)
# b5 — cadeia até o verdict (em blocos, stop-on-fail)
./tools/bootstrap-chain --from 12 --until 31
./tools/bootstrap-chain --from 32 --until 41                     # ...release-evidence → verdict
./tools/check-scaled-content-release-verdict --timings           # exigir verdict_passed>0
./tools/bootstrap-chain --from 42 --until 42                     # manifest-transaction
./tools/check-authorial-mass-manifest-transaction --timings      # included>0
# b6 — cohort loop até published_manifest=6846
./tools/run-promote-cohort-loop --target 6846 --step 250 --dry-run    # confere comandos
./tools/run-promote-cohort-loop --target 6846 --step 250 --execute    # write real (1º manifest>0)
./tools/check-published-manifest --timings
```

## NÃO encontrado / ressalvas
- `cmd/approve-public-release` (citado em STATUS.md:301) NÃO existe — approval é interno ao promote (`internal/publicrelease/approval.go`). Não invocar separado.
- Estado vivo agora: `published_manifest.jsonl`=0 linhas, `scaled_content_release_verdict.jsonl`=vazio/ausente → cadeia b5 ainda NÃO rodou em produção; ingest v2 pendente do pouso.
- Não li `bootstrap-chain` passos 1-11 (pré-massa) nem `run-heavy-throttled`/`run-go-cmd-cached` internos — fora do escopo do pre-flight de promoção. Escopos em edição concorrente (`internal/checks`, `v2ingest`, `contract`) não foram tocados.

---

# Anexo: os 16 unresolved do contrato semântico (não bloqueiam a cadeia)

MAPA — check-v2-writing-semantic-contract / os 16 unresolved

(1) O QUE SAO
`data/editorial/v2_writing_semantic_contract.json` (schema `v2_writing_semantic_contract_v3`, purpose=`block_reuse_until_exact_page_semantic_review`). Estrutura: 21 `requirements` + 5 resolvidos (2 `resolutions` + 3 `adopt_existing_targets`) + 16 `forward_candidates` (todos `status=internal_review_pending`). Cada requirement diz `reason=portfolio_semantics_changed_after_page_review`, `required_review=codex_legal_editorial_semantic_exact_page`: a semantica do portfolio mudou DEPOIS da review da pagina, entao aquela pagina v2 precisa de nova review semantica exata antes de poder ser reusada/avancada. Os 16 pendentes (14 glossario + 2 imobiliario), com alvo:
- gloss-{alienacao-parental, paternidade-socioafetiva, uniao-estavel} → glossario-02.jsonl
- gloss-{cessao-direitos-hereditarios, peticao-de-heranca} → glossario-01.jsonl
- gloss-{dcb, periodo-de-graca, ppp} → glossario-10.jsonl
- gloss-{dissolucao-parcial, endosso} → glossario-14.jsonl
- gloss-auxilio-reclusao→glossario-11; gloss-benfeitorias→glossario-12; gloss-rescisao-indireta→glossario-08; gloss-direitos-do-titular-lgpd→glossario2-14; gloss-registros-de-conexao→glossario2-15; imob-duas-garantias-vedacao→imobiliario-02.

Cada um pede: review juridico-editorial semantica exata da pagina + evidencia (`semantic_review_evidence`, `material_validation` com `visible_text_sha256`/`official_sources_sha256`, `verdict`, `reviewed_by`) que promova o forward_candidate a `resolution`/adoption.

(2) UNRESOLVED BLOQUEIA O QUE — nada, no caminho atual
- `cmd/check-v2-writing-semantic-contract/main.go:64` — `unresolved` so vira FAIL **se passar `--require-resolved`**. Sem essa flag o gate imprime unresolved e retorna 0 (PASSA). Confirmado ao vivo: `requirements=21 resolutions=5 unresolved=16`, exit 0.
- Ninguem passa `--require-resolved`: `grep -rn require-resolved tools/ .githooks/ *.sh` → 0 hits (o `RequireResolvedSources` em `internal/publicrelease/publicrelease.go:301/423` e outra coisa — sources, nao este contrato).
- `internal/v2writingsemantic/contract.go:337` calcula `Unresolved = len(requirements) - resolvedCount()`, `resolvedCount()=len(resolutions)+len(existingTargetAdoptions)` (linha 216). E puramente informativo no Report.
- Consumo real da ponte: `resolvedSuccessors()` (contract.go:352) so exporta os `resolutions` que sejam `duplicate_supersession_record`; `internal/v2supersessionintegrity/repository.go:96-97` explicitamente ignora unresolved ("Unresolved semantic dependencies must not become fictitious required files here"). Logo unresolved NAO bloqueia ingest, verdict nem promote — so nega a esses 16 intents a autoridade de forward-write/reuso ate a review.

(3) PRODUTOR SANCIONADO E TRABALHO PARA ZERAR
Produtor que ESCREVE o contrato (resolutions/forward/adopt): `tools/generate_v2_review_queue.py` (valida schema, autentica evidencia, material_validation) e a finalizacao via `cmd/finalize-v2-semantic-recut/main.go` (emite `forward_candidates`/`adopt_existing_targets` — schema `v2_semantic_forward_candidates_command_report_v1`). Um requirement vira resolvido de 2 formas: (a) `resolutions[]` com review semantica exata (`reviewed_by`, `semantic_review_evidence`, `verdict`, `material_validation`) — foi assim os 2 ja feitos (codex-eng-pts4/codex-root-source-closure, 2026-07-16); (b) `adopt_existing_targets[]` (`affirm_existing_owner`/`adopt_existing_target`) — os 3 ja feitos. Para zerar os 16: rodar a review juridico-editorial exata de cada pagina-alvo (14 shards glossario + imobiliario-02) e, para cada intent, gerar via `generate_v2_review_queue.py` a `resolution` (ou adoption) com a evidencia — promovendo o `forward_candidate internal_review_pending` a resolvido. Trabalho e do Codex (review `codex_legal_editorial_semantic_exact_page`), 16 paginas concretas.

NAO ENCONTRADO: nenhum gate/tool na cadeia ingest→verdict→cohort→promote que invoque `--require-resolved` (varri tools/, .githooks/, *.sh, cmd/, internal/checks/checks.go). Se o maestro quiser que unresolved BLOQUEIE, teria de adicionar essa flag — hoje nao bloqueia o primeiro `published_manifest>0`.
---

## Passos enumerados do bootstrap-chain (verificados 2026-07-21 19:11)

1-13: estoque→prosa (scale-shards, legal-signatures, pares, quality-report,
similarity-audit, quality-vectors, contextual-compat, refinement-queue,
shard-rewrite-plan, publication-readiness, legal-reviews, public-prose-
candidate, refined-public-prose). 14-31: inventários colunares + oráculos
PT-BR (languagetool@8082 VIVO ✓, vale, simplemma, text-shape, pair-rescoring,
wordfreq, ftfy, lexical-diversity, spellcheck, morphsyntax [stanza baixa
resources no 1º run], confusables, unicode, fts5, external-dedupe, semantic-
cluster). 32-42: release (evidence, final-page-rehearsal [REGENERADO hoje ✓],
contextual-review, source-inventory [563 URLs ✓], live-metadata [telemetria
CORRIGIDA ✓], live-evidence, source-approval, live-recheck, release-
transaction, VERDICT, manifest-transaction). Pré-requisito: ingest WRITE-FULL
com receipt (b4) após o pouso da unidade.
