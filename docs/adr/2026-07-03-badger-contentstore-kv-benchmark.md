# 2026-07-03: Badger KV benchmark sidecar for contentstore scale

## Status

Adopted internally, blocked from publication.

## Context

The P0 factory needs storage evidence for shard/contentstore paths that can grow beyond JSONL-only scans. Pebble and SQLite already provide ordered KV/relational baselines. Badger gives a second Go-native embedded KV baseline for write, point lookup and shard-prefix scan behavior over the same canonical JSONL-derived records.

## Decision

Adopt `github.com/dgraph-io/badger/v4` at `v4.9.2` only inside `internal/contentstorekvbench`.

The adapter builds temporary derived Badger databases outside the repo, compares Badger against Pebble and SQLite, and writes only blocked benchmark evidence to `data/ops/contentstore_kv_benchmark.jsonl`. The JSONL/content layers remain canonical. The evidence must keep `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `approval=false`, `public_path=""`, and `index_policy=noindex`.

## Consequences

Positive:
- Adds a real Apache-2.0 KV benchmark path for 10k, 100k and 1M shard/contentstore validation.
- Preserves publication zero and keeps Badger scoped to benchmark sidecars, not public content storage.
- Records license, provenance, source fingerprints, timings and artifact claim in machine-readable evidence.

Risks and mitigations:
- Badger has embedded-storage transitives and can hide stale derived state. The adapter rebuilds in temp paths and validates source fingerprints.
- Benchmark evidence can be mistaken for publication readiness. Policy and checks keep all public flags closed.
- One benchmark run does not prove production storage selection. It only compares sidecar behavior and preserves future 10M/P5 claims as blocked until dedicated evidence exists.

Autocritica: this reduces storage-scale uncertainty for the P0 factory, but it does not move public publication by itself. The next higher-value step is using this evidence to choose or harden the contentstore/release path that removes a real publication blocker without changing `public/`, `content/pages.json` or `published_manifest` prematurely.
