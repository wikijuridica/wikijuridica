# 2026-07-01: coder/hnsw candidate index for blocked dedupe evidence

Status: adopted for internal blocked evidence only.

## Context

The P0 content factory already integrates Bleve, Roaring, Bloom, go-minhash, bitset, xxhash, Pebble, SQLite/modernc and Parquet. The remaining gap is a local approximate-nearest-neighbor candidate layer over existing authorial quality vectors, useful for dedupe and clustering review before expensive exact checks at 10k, 100k and 1M scale.

## Options Compared

- `github.com/coder/hnsw`: pure Go HNSW graph, tagged module `v0.6.1`, pkg.go.dev and GitHub evidence, CC0-1.0 license. Good fit for a Go-first adapter with deterministic seed and exact cosine confirmation.
- `github.com/MichaelAyles/goformersearch`: pure Go and zero-dependency vector search with HNSW, but public docs show materially slower HNSW build times at 10k/100k than this cycle should put on the default path without a separate benchmark.
- `github.com/fogfish/hnsw`: generic Go HNSW with MIT license; useful candidate, but this cycle preferred the smaller coder/hnsw graph API already suited to direct float32 vectors.
- `github.com/habedi/hann`: broader ANN suite, but requires C/C++ toolchain and AVX-oriented assumptions, increasing portability and supply-chain risk for the Go-first factory.
- `github.com/oligo/hnswgo`: hnswlib binding; rejected for this integration because CGO/C++ adds operational complexity for the default dedupe gate.

## Decision

Adopt `github.com/coder/hnsw@v0.6.1` behind `internal/hnswcandidateindex` only. The adapter projects persisted `authorialmassqualityvectors` records into a stable numeric surface, builds HNSW candidates, and persists only exact-cosine-confirmed candidate evidence.

The evidence path is `data/ops/hnsw_candidate_index_evidence.jsonl`. It is explicitly blocked:

- `publication_allowed=false`
- `render_allowed=false`
- `sitemap_allowed=false`
- `approval=false`
- `index_policy=noindex`
- no public path

## Consequences

This integration improves candidate generation for dedupe and clustering review without claiming publication readiness. It is 10k-oriented evidence only until separate 100k/1M benchmark evidence exists. HNSW remains a prefilter; exact cosine confirmation is mandatory before a candidate pair is counted.
