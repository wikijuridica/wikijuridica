# ADR: Codex2 Source Evidence Gate

Date: 2026-06-16

## Status

Accepted as blocked P0 metadata gate.

## Context

`codex2_source_audit_queue` covers 4,800 source-audit tasks and `codex2_source_specificity_recheck` selects 209 official-source candidates across 27 seeds. Those candidates are useful for source review, but they are not final source approvals. Several high scores come from official hosts, article anchors, or deep paths that can still be semantically broad or cross-seed.

## Decision

Create `data/research/codex2_source_evidence_gate.jsonl` and `internal/codex2sourceevidencegate` as a metadata-only, blocked gate. The gate separates three states:

- `source_evidence_candidate_ready_for_human_lock_blocked`
- `source_evidence_needs_specific_official_url_blocked`
- `source_evidence_needs_higher_specificity_candidate_blocked`

The gate rejects raw text, external fetch, CTA/publication flags, public artifacts, final source approval and unknown JSON fields. It preserves Google/OAB/terms/robots/privacy review blockers on every record.

## Consequences

This reduces false positives before any authorial draft, readiness, render, sitemap or manifest action. It does not reduce the public deficit by itself: `published_manifest` remains zero and all source decisions remain blocked until full source, legal-editorial, SEO/crawl and release gates pass.
