# ADR: SEO Oracle for Robots and Sitemap Validation

Date: 2026-06-24

## Decision

Adopt `github.com/jimsmart/grobotstxt v1.0.3` and `github.com/aafeher/go-sitemap-parser v1.0.1` behind `internal/seooracles` as offline validation oracles for robots.txt and sitemap XML.

## Scope

The adapter may parse already available robots.txt text and already generated sitemap XML during blocked validation. It must not fetch remote URLs, write `public/`, write sitemap files, approve `published_manifest`, render pages or authorize scraping.

## Reason

The P0 release gate needs independent checks for Googlebot crawlability, sitemap declarations and sitemap XML structure. A dedicated adapter keeps the third-party API isolated, version-pinned and testable while preserving project contracts for publication zero.

## Risk Controls

- Exact module versions are pinned in `go.mod`.
- Imports are allowed only under `internal/seooracles/`.
- Evidence is versioned in `data/ops/seo_oracle_validation_evidence.jsonl`.
- Public flags remain false: no render, sitemap publication, public path or approved publication.
- Robots.txt is treated as a crawl signal, not legal permission to collect, copy or publish content.
