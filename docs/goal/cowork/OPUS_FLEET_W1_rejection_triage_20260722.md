# OPUS_FLEET_W1 — Rejection-queue triage (frontboard `rejection-queues-857`, P1)

Read-only triage. Author: Opus fleet W1 agent. Date: 2026-07-22. For: main + active wave.

## SCOPE

Triage the v2-ingest rejection queue into executable buckets: count → root cause → the ONE
action that clears each → pages unblocked → owner. Objective: maximize approved/indexable v2
stock toward the 10k floor. NO edits made (read-only); this is the plan for the main to execute.

**Authority note (read this first):** the frontboard name says "857", but that number is the
**stale** 07-21 dry-run summary (`v2_ingest_dryrun_funnel_20260721.txt`:
`pages=7703 accepted=6846 rejected=857`). The **live** per-page ledger
`data/ops/v2_ingest_report.jsonl` (single run `v2-ingest-20260722T140000Z`, mtime 2026-07-22)
shows **7702 records → 7178 accepted / 524 rejected**. So **333 pages were already recovered
between 07-21 and 07-22**; the real queue today is **524**, not 857. All counts below are from
the live 524.

## WHAT I READ (files + counts)

- `data/ops/v2_ingest_report.jsonl` — 7702 lines, authoritative live ledger. Grouped the 524
  `status=rejected` records by `reasons[]` (each page → ONE dominant root-cause bucket by
  priority; a page can carry a cascade of reasons but has ONE root cause).
- `data/ops/v2_ingest_dryrun_funnel_20260721.txt` — the 857 summary (superseded).
- `internal/v2ingest/validate.go` — confirmed gate mechanics: dup-phrase reject at :409;
  `isLegalCitationExempt` at :1040 (anchor + ≤40-word span + same official_source); source-stamp
  gate at :657-716 (`verified_at` must parse & be within max-age; `http_status` must be allowed;
  ingest is **metadata-only, does no network** — stamps are lineage, release revalidates live).
- `data/source-audit/` — restamp evidence **already on disk & fresh**:
  `cowork_source_recheck_20260722_wave2.jsonl`, `v2_source_provenance.jsonl`,
  `cowork_sumulas_vigencia_oficial_20260722.jsonl`, + poscutoff verificacao lote3-5.
- `data/ops/v2_legalfact_outcome_queue_20260721.jsonl` — 23 lines (legal-fact recheck queue).
- `.agents/runtime/p0_frontboard.jsonl` — confirms `rejection-queues-857` queued P1.

Dup-phrase blocking refs are overwhelmingly **same practice-area / same norm** (aer←aer,
banc←banc, adm←adm, imob←imob) → citation-driven recurrence, not generator molde → **gate-tune,
not rewrite**, is the correct lever (one cross-area case flagged for the red-team, below).

## BUCKET TABLE (sorted by pages-unblocked desc)

| # | bucket | representative reason code | pages | root cause | ONE executable action | type | pages unblocked | owner-hint |
|---|--------|----------------------------|------:|------------|-----------------------|------|----------------:|-----------|
| 1 | src-stamp | `official_source_verified_at_invalid:index=N:value=` + `official_source_http_status_invalid:index=N:status=0` | 214 | sources carry empty `verified_at` and `http_status=0` — never stamped (ingest is metadata-only, no net) | Restamp every source in the affected v2_pages shards with recent ISO `verified_at` (≤ max-age) + allowed `http_status`, **consuming `cowork_source_recheck_20260722_wave2.jsonl` + `v2_source_provenance.jsonl`**; re-ingest | data-fix | **205** (9 also need #2) | source/content agent |
| 2 | dup-phrase | `duplicate_phrase_with_page:line=X:intent=Y` | 194 | verifiable same-norm legal-citation windows (same art./Lei/Súmula across pages of same area) fail one of anchor/≤40w-span/same-source in `isLegalCitationExempt` | **Gate-tune `isLegalCitationExempt` (validate.go:1040)** — broaden anchor detection / span cap / same-norm (family) match so verifiable citations are exempt; do **NOT** run rewriter | gate-tune | **194** | engenharia (Fable red-team first) |
| 3 | legal-fact hold | `current_legal_fact_outcome_missing` / `_temporal_stale` / `_source_missing` | 30 | post-cutoff legal facts pending re-verify (tema_987 modulation, EU261 reform, INSS 2026, LGPD child basis) | Semantic audit: fill outcome/anchor from official recheck (`v2_legalfact_outcome_queue`, poscutoff verificacao lotes), stamp `checked_at` | content/research | **30** (9 also need #1) | content agent |
| 4 | title-length | `title_length_out_of_range:NN` (66-85) | 18 | title outside 20-65 chars | Batch title-normalize to 20-65 Unicode chars | content-fix | **18** (1 also #7) | content agent (cheap) |
| 5 | faq-unmarshal | `missing_required_field:faq[N]` (core fields present) | 8 | FAQ q/a struct unmarshal bug — **code fix already in flight** (v2ingest/validate) | Re-ingest once the FAQ fix lands | code-fix | **8** | engenharia (in flight) |
| 6 | research-pending | `source_unverified_research_pending` | 5 | official STF/host surfaces fail TLS / return 403 in this env | Find alternate TLS-valid official surface OR hold | research/external | **~2** (3 multi) | content agent (ext-blocked) |
| 7 | word-count | `word_count_out_of_range:NNN:allowed=..` (wc>0) | 4 | body length outside page-type band | Trim/expand body to band | content-fix | **4** (2 also #4) | content agent |
| 8 | src-specificity | `official_source_homepage_not_specific` / `_root_url_not_specific` | 3 | source URL is homepage/root, not a deep link | Replace with specific deep-link official URL | data-fix | **3** | source agent |
| 9 | public-path-dup | `public_path_duplicate_in_batch:line=X` | 2 | two pages resolve to the same `public_path` | Rename/dedupe one slug | data-fix | **2** | content agent |
| 10 | lane-mismatch | `lane_mismatch_with_portfolio` | 1 | page lane ≠ portfolio lane | Reclassify lane to portfolio | data-fix | **1** | content agent |
| 11 | orphan-empty (DROP) | `intent_skipped_by_writer:orphan_no_portfolio_join_semantic_duplicate_of_active_canonical` (39) / foreign-law out-of-allowlist (5) / `intent_id_not_in_portfolio` (6) | 45 | writer intentionally skipped: record is empty. 39 are **semantic dupes of an ALREADY-active canonical** (canonical already counts); 5 depend on Italian-law hosts outside allowlist; 6 not in portfolio | **DROP from target** (do NOT publish dupes); portfolio-join only the ~6 recoverable | drop/dedup | **~6** (39 legit drop) | coordenação |

Buckets sum: 214+194+30+18+8+5+4+3+2+1+45 = **524** ✓.

## TOTAL REACHABLE

- **Accepted now (live run):** 7,178
- **Mechanical, ZERO content rewrite** (restamp 205 + dup-tune 194 + faq 8 + title 18 + wc 4 +
  src-specificity 3 + path 2 + lane 1 + 9 restamp&dup combined) ≈ **+444**
- **Content/research** (legal-fact 30 + research-pending ~5, some ext-blocked) ≈ **+35**
- **Drop** (orphan-empty: 39 dupes of active canonicals — already counted; not "new"): ~6 recoverable
- **Ceiling if every non-drop page clears:** 7,178 + (524 − 39) ≈ **7,663 approved**

**★ CRITICAL 10k finding:** the entire ingested v2 stock is only **7,703 candidate pages**. Even at
100% acceptance the stock caps **~2,300 short of the 10,000 floor**. **The rejection queue alone
CANNOT reach 10k** — clearing it maximizes the existing ~7.7k. Reaching the P0 floor requires
**generating ≥ ~2,300 net-new approved intents in parallel** (sanctioned batch pipeline). Route
the queue-clearing (this doc) and net-new generation as two concurrent frentes.

## TOP-3 HIGHEST-LEVERAGE ACTIONS

1. **Restamp source `verified_at` + `http_status` (bucket #1) → +205 pages, no rewrite.** The
   evidence file is already on disk (`cowork_source_recheck_20260722_wave2.jsonl` +
   `v2_source_provenance.jsonl`). Single data pass over the affected v2_pages shards + re-ingest.
   Biggest single lever in the queue.
2. **Gate-tune `isLegalCitationExempt` (validate.go:1040) (bucket #2) → +194 pages, no rewrite.**
   Same-norm legal citations across same-area pages are being counted as molde. Broaden the
   exemption (anchor/span/same-norm-family). **One function edit.**
   → #1 + #2 alone = **399 pages (76% of the queue) with zero content rewrite** — both are
   single-commit engineering actions.
3. **Re-ingest after the in-flight FAQ unmarshal fix (+8) and batch-normalize titles (+18) +
   word-count (+4) (buckets #5/#4/#7) → +30 pages of cheap mechanical cleanup.** Then hand the
   legal-fact 30 to the content/research frente.

## COLLISION-SAFETY NOTE

- **`validate.go` is shared with the live wave / Codex.** Bucket #2 edits `isLegalCitationExempt`
  and bucket #5 touches the FAQ unmarshal path (fix already in flight) — check mtime/`git status`
  and use **pointwise edits**, never a rewrite that could clobber concurrent work. Serialize the
  Go-touching commit (heavy pre-commit build).
- **#2 is an anti-template gate — loosening it risks admitting real molde.** One cross-area
  dup was observed (`cons-assinatura...` ← `aer-milhas...`). **Run a Fable-5 adversarial red-team
  on the tuned exemption before applying** (per CLAUDE.md: red-team before editing a caro gate).
  Keep it principled (same-norm + ≤40-word span), not a blanket relax.
- **Buckets #1/#3/#8/#9/#10 write under `data/editorial/v2_pages/` — the wave2 restamp may
  already be consuming the same shards.** Claim the artifact via the coordination bus and edit by
  shard to avoid two writers on one file. **Do NOT publish the 45 orphan-empty pages** (39 are
  dupes of active canonicals — publishing = duplicate-content regression).
- Re-run `v2-ingest` (dry-run) after each bucket to re-measure; 857→524 shows the queue is a
  moving target — always classify against the newest `v2_ingest_report.jsonl` run_id.
