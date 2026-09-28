# ADR: bitset dense pairset adapter

## Status

Approved for internal blocked runtime use.

## Context

The authorial mass refinement and global similarity gates deduplicate candidate pairs while building anti-duplication evidence for 10k legal pages and future 100k/1M scale. The previous implementation used `map[uint64]bool` for every pair frontier. That is simple, but it allocates hash-map entries even when the pair universe is small and dense.

## Decision

Adopt `github.com/bits-and-blooms/bitset v1.24.2` as a direct runtime dependency only behind `internal/densepairset/`.

`internal/densepairset` uses a dense bitset when the pair universe is bounded, and falls back to a sparse map when the pair universe is too large. This prevents accidental memory blowups for 100k/1M while reducing overhead for dense local pair frontiers.

## Constraints

- No public artifact is written by this adapter.
- It cannot set `approval`, `publication_allowed`, `render_allowed`, `sitemap_allowed` or `public_path`.
- It is not a legal-content source and cannot authorize publication.
- Direct imports of `github.com/bits-and-blooms/bitset` are limited to `internal/densepairset/`.
- Similarity scoring remains exact after candidate selection; the adapter only deduplicates pair IDs.

## Validation

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test ./internal/densepairset -count=1`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test ./internal/authorialmassrefinementquality -count=1`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test ./internal/authorialmassglobalsimilarity -run "TestBuildRecordRecordsExactPairSemanticsAndKeepsPublicFlagsClosed|TestBuildRecordSignatureUnionCatchesCrossFrontierNearDuplicate" -count=1`
