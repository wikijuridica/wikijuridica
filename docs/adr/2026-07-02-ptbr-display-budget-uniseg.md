# ADR: uniseg for PT-BR Display Budgets

Date: 2026-07-02

## Status

Approved for internal blocked diagnostics only.

## Context

SEO/title/meta validators were counting runes, which overstates decomposed accented Portuguese text such as `e` plus a combining acute accent. Public-facing PT-BR budgets should count user-perceived characters for title and meta diagnostics before any release gate can reason about search snippets.

## Decision

Adopt `github.com/rivo/uniseg` at `v0.4.7` behind `internal/ptbrdisplaybudget` only. The dependency is used for Unicode grapheme cluster counts and display width diagnostics in internal SEO validation.

## Constraints

- License: MIT.
- No network access, scraping, ingestion, render approval, sitemap approval, public path, or publication approval.
- Imports are allowed only through `internal/ptbrdisplaybudget/`.
- Public release remains blocked by the normal publication transaction gates.
