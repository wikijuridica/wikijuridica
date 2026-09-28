# ADR: Codex2 Bleve Internal Blocked Search Adoption

Date: 2026-06-17

## Decision

Adopt `github.com/blevesearch/bleve/v2 v2.6.0` as a real Go runtime dependency for Codex2 internal blocked search, ranking and evidence review. The dependency is allowed only through the Codex2 policy gate, with public search, render, sitemap, publication and public artifact writes still closed.

## Context

The Codex2 P0 lane requires real open source integration, not a paper-only evaluation. The system Go in this environment is `go1.19.8`, which cannot compile newer Bleve transitive code that imports modern standard-library packages. The project uses an official project-local Go `go1.26.4` toolchain when installed under `.toolchains/go1.26.4`, or `GO_MODERN_BIN` when supplied by the operator. `.toolchains/` is a local, unversioned toolchain install, not repository source.

## Scope

Allowed:

- internal blocked indexing over research/editorial records;
- DataJud aggregate/editorial evidence search;
- validation, benchmark and policy checks;
- `go.mod` and `go.sum` changes for the exact approved module/version.

Forbidden:

- public search runtime;
- `public/`, `content/pages.json`, `published_manifest`, sitemap, robots or release staging writes;
- indexing individual process/person data as public content;
- CTA generation from individual DataJud cases.

## Evidence

- Official Go download source used for local toolchain: `https://go.dev/dl/`
- Bleve module/repository evidence: `https://pkg.go.dev/github.com/blevesearch/bleve/v2`, `https://github.com/blevesearch/bleve`
- Benchmark evidence: `data/research/codex2_bleve_benchmark_evidence.jsonl`
