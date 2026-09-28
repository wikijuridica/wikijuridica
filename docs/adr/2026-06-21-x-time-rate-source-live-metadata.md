# ADR: x/time/rate for Official Source Metadata Attempts

Date: 2026-06-21

Decision: adopt `golang.org/x/time/rate@v0.15.0` only inside the blocked official source URL live metadata attempt pipeline.

Context: P0 source checks need host-level throttling for metadata-only HEAD attempts. The portal must not copy official body text, scrape source pages, publish, render, or open sitemap/manifest flags from this adapter.

Constraints:
- JSONL remains the durable evidence layer.
- The adapter is limited to `internal/sourceliveevidence/`.
- Every live attempt must stay metadata-only with `raw_text_stored=false` semantics and public flags closed.
- Evidence is `data/source-registry/official_source_url_live_metadata_attempts.jsonl`.

Rollback: remove the rate limiter adapter and regenerate metadata attempts with live probing disabled; publication gates remain closed.
