# 2026-06-29: Pebble derived scale sidecar

## Status

Adopted internally, blocked from publication.

## Context

The P0 factory cannot depend on repeated full JSONL scans as the only lookup path for 10k now, 100k/1M next, and larger future validation. Existing SQLite and Roaring integrations cover relational counts and shard bitmaps. A separate ordered KV sidecar is useful for ID lookup and shard prefix scans over canonical JSONL layers without making any sidecar the source of truth.

## Decision

Adopt `github.com/cockroachdb/pebble/v2` at `v2.1.6` only inside `internal/pebblescalesidecar`.

The adapter builds a temporary derived Pebble database outside the repo, from canonical JSONL layers already used by `internal/scaleindex`. It stores record metadata by ID and shard-prefix keys, validates lookup and prefix scan, writes only blocked evidence to `data/ops/pebble_scale_sidecar_evidence.jsonl`, and keeps `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `approval=false`, `public_path=""`, and `index_policy=noindex`.

## Consequences

Positive:
- Adds a real high-scale OSS storage path for lookup and prefix scan without relaxing public release gates.
- Preserves JSONL as canonical source and fails closed when source fingerprints are stale.
- Gives the release/check pipeline another route away from linear scans as the integration matrix grows.

Risks and mitigations:
- Pebble has a larger transitive graph than small libraries. `codex2-policy-enforcement`, SBOM and SCA gates must keep version, license, import scope and transitives explicit.
- KV sidecars can hide stale derived state. The adapter uses source hashes, temp rebuild outside the repo and freshness checks.
- This is not a 1M/10M benchmark claim. Evidence explicitly keeps those capacity claims false until dedicated benchmarks run.
