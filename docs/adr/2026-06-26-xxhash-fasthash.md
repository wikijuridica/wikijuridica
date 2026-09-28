# ADR: xxhash fast hash adapter

Date: 2026-06-26

## Decision

Adopt `github.com/cespare/xxhash/v2` at `v2.3.0` only behind `internal/fasthash`.

The adapter provides deterministic non-cryptographic 64-bit hashing for blocked similarity and legal-signature factories. It is not a security primitive and must not be used as proof of uniqueness without the surrounding textual checks.

## Scope

- Allowed import scope: `internal/fasthash/`.
- Allowed write scope: `internal/fasthash/`, `go.mod`, `go.sum`, and `data/ops/xxhash_fasthash_evidence.jsonl`.
- Public output remains blocked: no `public/`, no `content/pages.json`, no `published_manifest`, no sitemap and no render permission.

## Evidence

`data/ops/xxhash_fasthash_evidence.jsonl` records the pinned module, MIT license, adapter package and consumers.
