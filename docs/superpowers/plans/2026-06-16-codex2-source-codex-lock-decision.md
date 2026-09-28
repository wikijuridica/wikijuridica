# Codex2 Source Codex Lock Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a blocked Codex-controlled source lock decision layer that consumes `codex2_source_live_recheck` and lets Codex approve internal source locks when executable live metadata evidence is sufficient, without requiring per-page human review and without publishing anything.

**Architecture:** Add a standalone package and generator/check wrappers, mirroring the existing Codex2 JSONL pattern. The layer emits one record per live-recheck candidate, marks only live-accessible metadata records as `codex_source_lock_approved_reference_only_blocked`, blocks the rest with actionable reasons, and keeps every public/render/sitemap/manifest flag false.

**Tech Stack:** Go standard library, JSONL data in `data/research/`, focused contract tests under `internal/contract`, shell wrappers under `tools/`.

---

### Task 1: Contract First

**Files:**
- Create: `internal/contract/codex2_source_codex_lock_decision_test.go`
- Later create: `internal/codex2sourcecodexlockdecision/decision.go`

- [ ] **Step 1: Write the failing test**

Create `TestCodex2SourceCodexLockDecisionApprovesOnlyExecutableEvidenceWithoutPublication`.

Required assertions:
- `Generate(".")` returns 209 records from `data/research/codex2_source_live_recheck.jsonl`.
- Exactly 8 records are `codex_source_lock_approved_reference_only_blocked`.
- The 8 approved records cover `emprestimo-consignado-nao-contratado`, `golpe-pix`, `inventario-extrajudicial-online` and `nome-negativado-indevidamente`.
- Approved records require `metadata_access_status=http_metadata_accessible`, `live_recheck_status=codex2_source_live_recheck_metadata_attempted_blocked`, `http_method=HEAD`, status `200..399`, no network error, no body read and no official text stored.
- Blocked records have `codex_source_lock_approved=false` and non-empty `blocking_reasons`.
- Every record keeps raw text, scraping, ingestion, external fetch, CTA, render, sitemap, manifest, `content/pages.json`, `published_manifest`, public artifact and `public_path` blocked.
- `publication_allowed=false` for every record, even when `codex_source_lock_approved=true`.
- Records reject unknown raw-text keys like `source_text` and reject any public or source-overclaim escape.

- [ ] **Step 2: Verify RED**

Run:

```bash
GOCACHE=/tmp/opt-wiki-go-cache go test -count=1 ./internal/contract -run TestCodex2SourceCodexLockDecision
```

Expected: fail because `portaljuridico/internal/codex2sourcecodexlockdecision` does not exist.

### Task 2: Minimal Package And Generator

**Files:**
- Create: `internal/codex2sourcecodexlockdecision/decision.go`
- Create: `cmd/generate-codex2-source-codex-lock-decision/main.go`
- Create: `tools/generate-codex2-source-codex-lock-decision`
- Create: `tools/check-codex2-source-codex-lock-decision`
- Create: `data/research/codex2_source_codex_lock_decision.jsonl`

- [ ] **Step 1: Implement minimal GREEN**

Implement `Generate`, `Refresh`, `WriteRecords`, `LoadRecords`, `Validate`, `ValidateRecords`, `ValidateRecord` and `ValidateJSONLine` following `internal/codex2sourceevidencegate`.

Required constants:
- output path `data/research/codex2_source_codex_lock_decision.jsonl`
- status `codex2_source_codex_lock_decision_blocked_parallel_p0`
- use policy `metadata_only_codex_source_lock_no_scraping_no_content_copy`
- decisions `codex_source_lock_approved_reference_only_blocked`, `codex_source_lock_blocked_no_live_metadata_access`, `codex_source_lock_blocked_not_ready_for_live_recheck`

- [ ] **Step 2: Run GREEN**

Run:

```bash
GOCACHE=/tmp/opt-wiki-go-cache go test -count=1 ./internal/codex2sourcecodexlockdecision ./cmd/generate-codex2-source-codex-lock-decision ./internal/contract -run TestCodex2SourceCodexLockDecision
./tools/generate-codex2-source-codex-lock-decision
./tools/check-codex2-source-codex-lock-decision
```

Expected: all pass and generator prints 209 records, 8 Codex source locks approved and publication=false.

### Task 3: Documentation, Ledger, Checkpoint And Commit

**Files:**
- Modify: `codex2/AGENTS.md`
- Modify: `.agents/agent_context_ledger.jsonl`
- Modify: `CHECKPOINT.md`
- Create: `docs/adr/2026-06-16-codex2-source-codex-lock-decision.md`

- [ ] **Step 1: Document durable rule**

Add a short `P0 Codex Source Lock Decision` section to `codex2/AGENTS.md` saying Codex can approve internal source locks by executable criteria, without requiring per-page human review and without public release.

- [ ] **Step 2: Record subagents and checkpoint**

Append read-only subagents with `closed_before_checkpoint=true`. Add a Cycle 340 checkpoint with worktree, data counts, validation, no-publication proof and continuity.

- [ ] **Step 3: Final validation**

Run:

```bash
gofmt -l internal/codex2sourcecodexlockdecision/decision.go internal/contract/codex2_source_codex_lock_decision_test.go cmd/generate-codex2-source-codex-lock-decision/main.go
GOCACHE=/tmp/opt-wiki-go-cache go test -count=1 ./internal/codex2sourcecodexlockdecision ./cmd/generate-codex2-source-codex-lock-decision ./internal/contract -run TestCodex2SourceCodexLockDecision
./tools/check-codex2-source-codex-lock-decision
./tools/check-codex2-source-evidence-gate
./tools/check-agent-context-ledger
git diff --check
git diff --exit-code -- public/ content/pages.json data/editorial/published_manifest.jsonl .release-staging public/sitemap.xml public/sitemaps public/robots.txt
git diff --quiet -- go.mod go.sum
```

Expected: all pass; public diff and `go.mod/go.sum` have no output.

- [ ] **Step 4: Commit branch**

Stage only the new Codex2 source lock decision files, docs, ledger and checkpoint. Commit:

```bash
git commit -m "codex2: add blocked codex source lock decision"
```
