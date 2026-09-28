# ADR: Codex-Controlled Source Lock Decision

Date: 2026-06-16

## Status

Accepted as blocked P0 research/source infrastructure. This ADR does not authorize public rendering, sitemap inclusion, `content/pages.json`, `published_manifest` writes or publication.

## Context

`codex2_source_live_recheck.jsonl` contains 209 candidate-level source records. Eight records have live metadata evidence from HEAD requests with `http_metadata_accessible`, status `200`, no body read and no official text stored. A human-review queue for 10,000 possible pages would not scale and would shift the engineering responsibility away from Codex.

## Decision

Create `data/research/codex2_source_codex_lock_decision.jsonl` as a Codex-controlled source lock layer. The layer approves only internal metadata-only source locks where executable criteria are satisfied and blocks every other candidate with machine-actionable reasons.

The current expected state is:

- `records=209`
- `codex_source_lock_approved=8`
- `blocked_no_live_access=49`
- `blocked_not_ready=152`
- `publication_allowed=0`

`codex_source_lock_approved=true` is not final source approval and is not publication approval. It only means Codex can carry the candidate forward as an internal reference for later blocked editorial gates.

## Consequences

- Codex can advance source decisions without asking the user to review candidates one by one.
- The branch avoids stale integration from the old `codex2-p0-source-final-lock` worktree, which overclaimed source locks against newer evidence.
- Public artifacts remain untouched: no `public/`, `content/pages.json`, `published_manifest`, sitemap, robots, render or `public_path`.
- Future cycles can consume the eight approved internal source locks in authorial/release gates, but must still pass content quality, OAB/CTA, SEO/crawl, anti-duplication, HTML and release transaction gates before any public page.
