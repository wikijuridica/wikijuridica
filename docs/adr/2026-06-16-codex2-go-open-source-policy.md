# ADR: Codex2 Go Open Source Policy Gate

Date: 2026-06-16

## Status

Accepted as blocked P0 policy. No runtime dependency is adopted by this ADR.

## Context

The P0 portal needs better search, crawling, source and similarity tooling, but public publication remains forbidden until legal source, OAB, Google quality, editorial and release gates pass. Go dependencies are allowed only after license, maturity, maintenance, transitive dependency, supply-chain, legal, performance and P0 benefit review.

## Decision

Create `data/research/codex2_policy_enforcement.jsonl` as a blocked policy layer and `internal/codex2policyenforcement` as the executable validator. The layer documents Bleve, Colly, MinHash/LSH or own stdlib alternative, OpenAI Codex/MCP/docs, Context7 and official legal/SEO sources. It keeps public flags false and forbids `go.mod`, `go.sum`, `public/`, `content/pages.json`, `published_manifest`, sitemap and staging writes.

Bleve, Colly and MinHash/LSH remain `accept_blocked_prototype` only. Runtime adoption requires a separate ADR, fixed version, benchmark and validation. Context7, Codex and OpenAI Docs MCP remain tooling context only, not product runtime and not legal source. Official sources are reference/provenance only, with no scraping, ingestion or bulk republication.

## Consequences

This gate reduces accidental dependency adoption and accidental publication risk, but it does not reduce the public 10k deficit. The next executable step is to use this policy before any prototype that adds search, crawler, similarity or MCP runtime behavior, then benchmark on real blocked data before changing `go.mod`.
