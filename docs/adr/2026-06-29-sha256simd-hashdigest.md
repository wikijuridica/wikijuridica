# ADR: sha256-simd hashdigest adapter

Date: 2026-06-29

## Decision

Adopt `github.com/minio/sha256-simd` at `v1.0.1` only behind `internal/hashdigest`.

The adapter keeps SHA-256 output compatible with `crypto/sha256` while allowing SIMD-backed hashing for blocked source-file freshness checks in large JSONL scans. It is not a publication approval mechanism and does not replace schema, source, legal, SEO, anti-spam or release gates.

## Scope

- Allowed import scope: `internal/hashdigest/`.
- Allowed consumers: internal blocked scanners, starting with `internal/jsonlstream`.
- Allowed write scope: `internal/hashdigest/`, `internal/jsonlstream/`, `go.mod`, `go.sum`, `data/ops/sha256simd_hashdigest_evidence.jsonl`, and `data/ops/jsonl_stream_benchmark_evidence.jsonl`.
- Public output remains blocked: no `public/`, no `content/pages.json`, no `published_manifest`, no sitemap and no render permission.

## License And Risk

`github.com/minio/sha256-simd` is Apache-2.0. It brings `github.com/klauspost/cpuid/v2` for CPU feature detection. The adapter has parity tests against the standard library and keeps the external API inside `internal/hashdigest` so the dependency can be replaced if it regresses on a target architecture.

## Evidence

`data/ops/sha256simd_hashdigest_evidence.jsonl` records module, version, license, adapter package, risk controls and public flags. `jsonl-stream-benchmark` records the same adapter identity on live JSONL scanner evidence.
