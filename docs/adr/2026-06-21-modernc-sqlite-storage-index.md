# ADR: modernc SQLite for Derived Storage Index

Date: 2026-06-21

Decision: adopt `modernc.org/sqlite@v1.53.0` only for derived, local SQLite sidecars rebuilt from canonical JSONL.

Context: P0 checks scan large JSONL layers repeatedly. The sidecar accelerates lookup/count/join over blocked RCA data and generic scale-index layers while preserving JSONL as the source of truth.

Constraints:
- SQLite files are derived temporary artifacts and are not committed.
- The adapter is limited to `internal/storageindex/` and `internal/scaleindex/`.
- `internal/scaleindex/` may expose generic iteration, grouped lookup by shard and changed-shard detection for blocked 10k/100k/1M factory layers.
- Rebuild is atomic and fails closed if the source is stale, corrupt, or has public flags open.
- Evidence is `data/ops/storage_index_benchmark_evidence.jsonl`.
- The adapter cannot write `public/`, `content/pages.json`, `published_manifest`, sitemap, robots, or release staging.

Rollback: delete the sidecar generation path and keep JSONL scan checks; publication gates remain closed.
