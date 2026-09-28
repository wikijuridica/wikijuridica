# OPUS FLEET W1 — restamp-391-live (P1) — engineering fix spec

Author: Opus 4.8 Go engineer (Cowork W1, read-only). Date: 2026-07-22.
Deliverable is spec-only; **nothing was applied to disk, no git, no build, no restamp run.**

---

## SCOPE

Frontboard `restamp-391-live` (P1). The source-recheck **data** is CLOSED (morning
`cowork_source_recheck_20260722.jsonl` 120 recs + wave2 `..._wave2.jsonl` 59 recs +
`..._pages.jsonl` 391 recs cover 513/513 refs of the 225-page bucket). Only the
**engineering of the live re-stamp** remains, stuck on two gates surfaced when running
`audit-v2-source-provenance --live --reuse-successful [--scope all|incomplete] [--cowork-live-browser-insumo …]`:

- **GATE A** — full-scope (`--scope all`) inventory build refuses `tributario-r02` because one
  source is a generic STJ search page (`pesquisa.jsp`, no tema code).
- **GATE B** — `--reuse-successful` aborts because stale, pre-schema-bump prior evidence
  ("evidence-0012") reports `checked_at_stale` **together with** `input_selection`/`audit_policy`
  issues, and the renewal filter only tolerates a *pure* `checked_at_stale` report.

Both are real. Fixes below: GATE A = one source-ref replacement (verified live), GATE B = one
patch to `reusableEvidenceForLiveRenewal`. A third prerequisite (wave2 cannot be fed to the
insumo loader as-is) is documented under EXPECTED EFFECT so the bucket actually clears.

---

## WHAT I READ (file:line)

Restamp tool / flow (producer→consumer):
- `cmd/audit-v2-source-provenance/main.go`
  - `:21` `checkedAtStaleIssueCode = "v2_source_provenance_checked_at_stale"`
  - `:32-49` `reusableEvidenceForLiveRenewal` (**GATE B site**)
  - `:57` `--reuse-successful` flag; `:112-114` requires `--live`; `:69` `--cowork-live-browser-insumo`
  - `:223-232` reuse path: `LoadEvidenceForLiveReuseFiles` → `SelectionEvidenceNotFound` → `reusableEvidenceForLiveRenewal` → `AuditWithReuse`
- `internal/v2sourceprovenance/audit.go`
  - `:38-39` `EvidenceSchemaVersion=6`, `AuditPolicyVersion=…_v6` (current); `:51-52` legacy=v4
  - `:482-491` `sameReusableAuditContext` — reuse requires `record.CheckedAt == checkedAt` (today) **and** current schema/policy
  - `:610-612` `validateEvidenceForLiveReuse`; `:638-641` `audit_policy_invalid`; `:649-652` `input_selection_invalid`
  - `:783-791` `checked_at_stale` emitted per record; `:976-986` `validateCurrentCheckedAt` (`:982-984` stale when `checkedDate.Before(today)`)
  - `:1000-1009` `evidenceInputSelection` returns invalid when `EvidenceSchemaVersion != 6` (⇒ v5 records fail selection)
- `internal/v2sourceprovenance/selection_store.go`
  - `:75-79` `LoadEvidenceForLiveReuseFiles`; `:81-115` load flow (`:94-100` exact sidecar returns its failing validation report incl. `checked_at_stale`; `:104-114` singleton compat-fallback)
  - `:135-145` `validateEvidenceSelectionAtPath` → `input_selection_mismatch`
- `internal/v2sourceprovenance/check.go:17-34` `CheckEvidenceSelection` → `input_selection_mismatch`
- `internal/v2sourceprovenance/inventory.go`
  - `:27` `EvidenceRelPath` (all-finalized singleton); `:28` `EvidenceSelectionDirRelPath` (exact sidecars)
  - `:353-356` **every** source URL is normalized (specificity checked) **before** the scope filter; `:361-363` scope-incomplete skip is *after* it; `:660-662` `officialsourcespecificity.NonSpecificReason` ⇒ `source_url_not_specific` (**GATE A site**)
- `internal/officialsourcespecificity/specificity.go:20-68` — `:45-48` STJ rule; `:60-68` `stjRepetitiveIndexPath` (matches `repetitivos/temas_repetitivos/pesquisa.jsp`); `:96-116` `hasPositiveNumericQuery` (allow keys `cod_tema_inicial`,`cod_tema_final`,`num_processo_classe`)
- `internal/v2sourceprovenance/cowork_live_browser.go` — `:44` path pattern `^data/source-audit/cowork_source_recheck_\d{8}\.jsonl$`; `:46-57` insumo record schema; `:99` `DisallowUnknownFields`; `:138-169` record validation (`:149-151` method must start `cowork-fable-live-`; `:152-156` verdict ∈ {ok,replace_source}); `:187-196` override only when verdict `ok` + browser-required note
- `tools/finalize-v2-review:1061-1094` `_source_provenance` — runs `--scope incomplete` then `--scope all`, both `--reuse-successful`, **but never passes `--cowork-live-browser-insumo`**

Data read:
- `data/editorial/v2_pages/tributario-r02.jsonl` — intent `trib-contrib-sistema-s-teto-20-salarios`, sources[1] = the generic Tema-1.390 URL
- `data/source-registry/v2_source_provenance_live_evidence.jsonl` — the singleton: **12 records, all schema v5 / policy v5, checked_at 2026-07-14, selection exact_files:[cidadania-09.jsonl]** ⇒ "evidence-0012" is its last record
- Evidence sidecars: 105 current (v6), **15 stale (v5)** ⇒ GATE B is a *class* of stale pre-bump evidence, not one file
- Recheck sidecars: morning has 20 browser-required (`client-rendered`/`client-side`) verdict-ok entries; wave2 schema = `{url,reachable,http_status,final_url,title,looks_official,method,note,verified_at}` (no `verdict`, extra `http_status`, method `live_fetch_200`/`websearch_confirmed`)

---

## GATE A — DIAGNOSIS + FIX (with official source)

**Diagnosis.** `officialsourcespecificity.NonSpecificReason` (specificity.go:45-48) classifies any
`processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp` URL as `institution_homepage`
**unless** it carries a positive `cod_tema_inicial` / `cod_tema_final` / `num_processo_classe`.
This is called from inventory.go:660 via `MetadataRequestURL` at inventory.go:353 — **before** the
scope filter — so a non-specific URL fails the inventory build and aborts the run.

In `tributario-r02.jsonl`, intent `trib-contrib-sistema-s-teto-20-salarios`, the four STJ URLs:

| src idx | tema | URL query | specificity |
|---|---|---|---|
| 0 | 1.079 | `cod_tema_inicial=1079` | PASS |
| **1 (src1)** | **1.390** | **`pesquisa_livre=1390`** (free-text search, no tema code) | **FAIL → institution_homepage** |
| — | 986 (other intent) | `cod_tema_inicial=986` | PASS |
| — | 779 (other intent) | `cod_tema_inicial=779` | PASS |

`pesquisa_livre` is not in the allowlist, so `hasPositiveNumericQuery` returns false → blocked.
**src1 = source_index 1 (0-based) of that intent = the Tema-1.390 free-text URL.** That is the single
GATE-A blocker.

**Official source (verified live, 2026-07-22, WebSearch on stj.jus.br).** STJ **Tema Repetitivo
1.390** (Primeira Seção, rito dos repetitivos, tese publicada fev/2026): o teto de 20 salários
mínimos do art. 4º, parágrafo único, da Lei 6.950/1981 **não** se aplica à base de cálculo das
contribuições parafiscais de terceiros (INCRA, salário-educação, DPC, FAER, SENAR, SEST, SENAT,
SESCOOP, SEBRAE, APEX-Brasil, ABDI). This matches the record's `anchor_claim` exactly and complements
sibling src0 (Tema 1.079 = Sistema S). STJ's own canonical deep-link form (surfaced live for Tema
1.079) is `pesquisa.jsp?novaConsulta=true&tipo_pesquisa=T&cod_tema_inicial=<n>&cod_tema_final=<n>`.

**Fix (source-ref replacement — via the sanctioned review queue, NOT a hand-edit).**
File `data/editorial/v2_pages/tributario-r02.jsonl`, intent `trib-contrib-sistema-s-teto-20-salarios`, `sources[1]`:

```
BEFORE  "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?i=1&novaConsulta=true&p=true&pesquisa_livre=1390&quantidadeResultadosPorPagina=10"
AFTER   "url": "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true&tipo_pesquisa=T&cod_tema_inicial=1390&cod_tema_final=1390"
```

`name`, `anchor_claim` unchanged. `verified_at`/`http_status` are re-stamped by the live audit's
`--apply`. The new URL carries `cod_tema_inicial=1390` (positive) ⇒ `hasPositiveNumericQuery` true ⇒
`NonSpecificReason` returns "" ⇒ passes; it is the **same endpoint** as the three already-passing
sibling tema URLs, just addressed by tema code instead of free-text search.

---

## GATE B — DIAGNOSIS + PATCH

**Diagnosis.** `--reuse-successful` (main.go:223-232) loads prior evidence via
`LoadEvidenceForLiveReuseFiles`, then filters it through `reusableEvidenceForLiveRenewal`
(main.go:32-49). That filter is fail-closed on **any** issue whose code is not exactly
`checked_at_stale`.

The blocking evidence is stale, **pre-v5→v6-bump** evidence — the 12-record singleton
`v2_source_provenance_live_evidence.jsonl` (checked_at 2026-07-14, schema v5, selection
exact_files:[cidadania-09]; "evidence-0012" = its 12th record) and the 15 remaining v5 sidecars.
When `validateEvidenceForLiveReuse` re-validates such a record today it emits **three** issues, not one:

- `checked_at_stale` (audit.go:783-791 → validateCurrentCheckedAt:982-984; 2026-07-14 < today)
- `audit_policy_invalid` (audit.go:638-641; schema/policy v5 ≠ current v6)
- `input_selection_invalid` (audit.go:649-652; `evidenceInputSelection`:1000-1009 rejects v5 ⇒ "input_selection")

The last two are **symptoms of the same staleness** (a prior-day sidecar naturally predates the
schema/policy in force today), but because they are not literally `checked_at_stale`, the loop at
main.go:40-44 returns `nil, report` and `failReport` aborts the whole run. Note that stale evidence is
**never** reusable anyway: `sameReusableAuditContext` (audit.go:490) requires `record.CheckedAt == today`.
So the correct behavior for *any* stale load is "drop it and re-fetch live," exactly as the function's
own comment already intends for a pure-stale sidecar — the filter simply fails to recognize staleness
that arrives with its usual companions.

**Patch — `cmd/audit-v2-source-provenance/main.go:36-49` (before → after):**

```go
// BEFORE
func reusableEvidenceForLiveRenewal(records []v2sourceprovenance.EvidenceRecord, report v2sourceprovenance.Report) ([]v2sourceprovenance.EvidenceRecord, v2sourceprovenance.Report) {
	if report.Passed() {
		return records, v2sourceprovenance.Report{}
	}
	for _, issue := range report.Issues {
		if issue.Code != checkedAtStaleIssueCode {
			return nil, report
		}
	}
	// Nothing from a stale day is handed to AuditWithReuse. A previously
	// blocked URL is therefore retried live under the current policy rather
	// than being reused or allowed to prevent renewal of the whole selection.
	return nil, v2sourceprovenance.Report{}
}
```

```go
// AFTER
func reusableEvidenceForLiveRenewal(records []v2sourceprovenance.EvidenceRecord, report v2sourceprovenance.Report) ([]v2sourceprovenance.EvidenceRecord, v2sourceprovenance.Report) {
	if report.Passed() {
		return records, v2sourceprovenance.Report{}
	}
	// A prior-day sidecar is never reusable: the same-day reuse guard
	// (sameReusableAuditContext) requires CheckedAt == today, so stale evidence
	// can only be dropped and re-fetched live. Evidence that predates a
	// schema/policy bump additionally reports audit_policy_invalid and
	// input_selection_invalid *together with* checked_at_stale; those are
	// symptoms of the same staleness, not a live-day corruption. Whenever the
	// load reports staleness, drop the whole selection and let the live audit
	// re-verify it (with the cowork insumo, when supplied) instead of failing
	// the run closed on schema-drift companions.
	stale := false
	for _, issue := range report.Issues {
		if issue.Code == checkedAtStaleIssueCode {
			stale = true
			break
		}
	}
	if !stale {
		// Today's evidence with a genuine (non-stale) validation failure stays
		// fail-closed: a hand-edited or corrupt current sidecar must never be
		// silently discarded.
		return nil, report
	}
	// Nothing from a stale day is handed to AuditWithReuse. A previously
	// blocked URL is therefore retried live under the current policy rather
	// than being reused or allowed to prevent renewal of the whole selection.
	return nil, v2sourceprovenance.Report{}
}
```

**Why this is safe (no gate relaxation).** Behavior changes for exactly one case — stale + schema-drift
companions — from *abort* to *drop-and-refetch-live*. Preserved unchanged: pure-stale ⇒ drop (as
before); today's evidence with any non-stale failure ⇒ fail-closed (as before). Dropped evidence is
re-verified live under the current policy with all guards (apply-eligibility, blocked-URL, final-URL,
metadata-only) intact — no trust is extended to the stale bytes, so there is no bypass.

**Test to add/adjust:** `cmd/audit-v2-source-provenance/main_test.go` — assert that a report containing
`checked_at_stale` + `audit_policy_invalid` + `input_selection_invalid` returns `(nil, empty)` (drops),
while a today-dated report with only `audit_policy_invalid` still returns `(nil, report)` (fail-closed).

---

## EXPECTED EFFECT

With GATE A + GATE B applied and the restamp invoked as
`audit-v2-source-provenance --live --scope {incomplete,all} --reuse-successful --cowork-live-browser-insumo data/source-audit/cowork_source_recheck_20260722.jsonl --file <shard>`:

1. GATE B fix ⇒ `--reuse-successful` no longer aborts on the stale v5 singleton / 15 v5 sidecars; it
   drops them and runs a **full live** audit, which then consults the insumo. The dropped evidence is
   replaced with fresh evidence stamped `checked_at = today` (no stale timestamp survives).
2. GATE A fix ⇒ the `--scope all` inventory build for `tributario-r02` no longer fails on the
   Tema-1.390 URL, so its 513-ref cohort can complete.
3. The morning insumo supplies the 20 browser-required (STF `noticias`/`portal`, STJ `REJ.cgi` PDF)
   overrides; the ~495 static planalto/gov.br/receita refs pass live curl directly. Bucket clears.

**Caveat — two insumo-consumption prerequisites for the phrase "consume the 2 jsonl" to hold
(otherwise ~26 refs stay blocked):**

- **(P1) The restamp driver must actually pass `--cowork-live-browser-insumo`.** `finalize-v2-review._source_provenance`
  (tools/finalize-v2-review:1061-1094) does **not** pass it today, so its live audit has no override
  and the 20 client-rendered morning refs would block. The re-stamp of the 225 bucket must run the
  audit tool *with* the flag (dedicated driver), or finalize-v2-review must be extended to pass it.
- **(P2) Wave2's browser-required refs cannot be fed to the current insumo loader.** wave2 holds ~6
  curl-failing refs (3 STJ `jurisprudencia/externo/informativo` JS pages + 3 gov.br PDFs — RFB/ANPD/INPI,
  all `websearch_confirmed`) that need an override, but `LoadCoworkLiveBrowserInsumo` is fail-closed
  and rejects wave2 on four counts: filename `_wave2` fails the `\d{8}\.jsonl$` path pattern
  (cowork_live_browser.go:44/132-134); `http_status` is an unknown field (`DisallowUnknownFields`:99);
  `method: live_fetch_200|websearch_confirmed` fails the `cowork-fable-live-` prefix (:149-151); and no
  `verdict` field fails the enum (:152-156). The flag is also a single `flag.String`. **Preferred
  (fail-closed-preserving) resolution:** normalize+merge the wave2 browser-required rows into the
  sanctioned `cowork_source_recheck_20260722.jsonl` (add `verdict:"ok"`, map `method`→`cowork-fable-live-*`,
  drop `http_status`, tag a browser note) via a `generate-*` step, so the existing loader consumes them
  unchanged. (Alternative: extend the flag to repeatable insumos and relax the loader schema — larger
  code change, weakens the strict contract.)

---

## COLLISION-SAFETY NOTE

- **Read-only honored.** No files edited, no `data/`/`v2ingest.go`/`validate.go` touched, no git, no
  restamp run, no `go build ./...`/suite. Only focused Grep/Read + read-only jsonl inspection (jq/wc/grep).
  This spec file is the single Write.
- **GATE B patch (`cmd/audit-v2-source-provenance/main.go`, `//go:build devcmds`)** is a Go change ⇒
  triggers the heavy serialized pre-commit build (one Go build at a time). Frontboard
  `verifier-live-browser-kind` is `done_pending_commit` and touches
  `internal/v2sourceprovenance/{audit.go,cowork_live_browser.go}` in a serialized Go bundle. Apply the
  main.go edit into that same serialized bundle (pontual edit, preserve concurrent work; never
  reset/checkout/restore). Different files ⇒ low collision risk, but same build unit — do not launch a
  second concurrent Go commit.
- **GATE A change is data** (`data/editorial/v2_pages/tributario-r02.jsonl`) ⇒ must go through the
  sanctioned review queue (`generate_v2_review_queue.py` / `finalize-v2-review`), never a hand-edit
  (CLAUDE.md: never edit v2_pages JSONL by hand; frontboard flags it "fila revisao"). That shard/producer
  may be under `flock` during the active regen (frontboard `fila-noop-filter`) — check the lock before
  queuing.
- **P2 normalization** writes under `data/source-audit/` ⇒ out of my read-only scope; specified for the
  driver/data owner, not applied here.
