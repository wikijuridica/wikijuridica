# ADR: Snowball PT-BR Stemming for Quality Dedupe

Date: 2026-06-24

## Decision

Adopt `github.com/blevesearch/snowballstem v0.9.0` behind `internal/ptbrtext` for Portuguese stemming used by blocked quality and near-duplicate checks.

## Scope

The dependency may normalize PT-BR legal tokens into stems for internal shingles, similarity and anti-doorway checks. It must not rewrite public prose, approve publication, write `public/`, write sitemap files or change canonical URLs.

## Reason

At 10k pages and beyond, legal topics vary by singular/plural, gender and common suffixes. Stemmed shingles improve duplicate and doorway detection without making the generated text more mechanical.

## Risk Controls

- Exact module version is pinned in `go.mod`.
- Imports are allowed only under `internal/ptbrtext/`.
- Exact-content hashes continue to use folded words, not stems, to avoid over-merging distinct pages.
- Evidence is versioned in `data/ops/ptbr_stemming_evidence.jsonl`.
- Public flags remain false: no render, sitemap, public path or approved publication.
