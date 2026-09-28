# ADR: tidwall/sjson for source-provenance JSONL field patching

## Status

Approved for internal blocked runtime use.

## Decision

Adopt `github.com/tidwall/sjson v1.2.5` only behind `internal/v2sourceprovenance/` (`apply.go`), paired with the already-approved `github.com/tidwall/gjson v1.19.0` reader.

## Context

`internal/v2sourceprovenance/apply.go` patches individual fields (`official_sources.N.verified_at`, `official_sources.N.http_status`) into existing JSONL records that carry source-audit evidence produced upstream by `cmd/generate-source-live-evidence` and related generators. These records already exist on disk with a specific byte layout, key order and formatting produced by their original generator.

The alternative — unmarshal the full record into a Go struct, mutate the field, and re-`json.Marshal` — was rejected because:

- It risks silently reordering keys or normalizing whitespace/escaping across thousands of already-durable JSONL lines, which is indistinguishable from data loss when diffing evidence history and breaks the "never hand-edit JSONL" contract for anything that touches bytes it doesn't own.
- Records in this family carry heterogeneous, evolving optional fields across generators; round-tripping through a narrow Go struct would silently drop fields the apply step doesn't know about.
- `sjson.SetBytes` performs a surgical byte-level patch of only the named path, preserving every other byte of the record untouched — the correct semantics for a provenance-evidence patcher whose job is exactly "touch this one field, nothing else."

## Constraints

- Direct imports of `github.com/tidwall/sjson` are limited to `internal/v2sourceprovenance/`.
- `github.com/tidwall/match v1.1.1` and `github.com/tidwall/pretty v1.2.1` are approved only as exact transitive versions of `gjson`/`sjson`.
- No public artifact, sitemap, render permission or publication approval flows through this adapter. It patches blocked JSONL evidence in `data/`, never `public/`, never `content/pages.json`, never a `published_manifest`.
- Does not touch the render or crawl hot path (`internal/render`, `internal/httpserver`, `internal/crawl`, `internal/sitemap`); `apply.go` runs only in the offline `cmd/generate-*` / evidence-apply pipeline under a file lock (`acquireApplyLock`) with a transactional journal (`applyJournal`), staged writes, and `syncDirectory` fsync-of-directory durability — the same durability pattern used elsewhere in `internal/v2ingest/transaction.go`.

## Licence and version

- Licence: MIT (`github.com/tidwall/sjson`, same licence family as the already-adopted `tidwall/gjson`).
- Version fixed at `v1.2.5` in `go.mod`/`go.sum` (no floating/latest resolution).

## Benchmark note

The adapter operates on individual JSONL lines (single-record field patch), not on the full 10k/100k corpus in one call — each `sjson.SetBytes` call is O(len(one record)), invoked once per evidence record inside the existing batched/locked apply loop in `applyWithOperations`. This is consistent with the existing `gjson` ADR's scope (`internal/jsonfieldscan/`, partial field reads on large JSONL gates) and does not introduce a new full-corpus scan; no separate 10k/100k throughput benchmark is required because the per-call cost does not scale with corpus size, only with individual record size, and the outer loop's iteration cost is already accounted for by the existing apply-pipeline benchmarks.

## Rollback

Remove the `sjson.SetBytes` calls in `apply.go` and replace with struct-level unmarshal/marshal only if a future generator standardizes the full record schema for this family; until then, byte-level patching is the safer default. Removing the dependency requires re-deriving the same two field writes without corrupting untouched bytes in the existing evidence JSONL.
