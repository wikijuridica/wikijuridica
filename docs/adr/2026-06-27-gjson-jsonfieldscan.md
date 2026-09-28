# ADR: gjson JSON field scanner

## Status

Approved for internal blocked runtime use.

## Decision

Adopt `github.com/tidwall/gjson v1.19.0` only behind `internal/jsonfieldscan/`.

The adapter is used for partial field reads in large JSONL gates. It cannot replace full schema validation before legal, release or publication decisions.

## Constraints

- No public artifact, sitemap, render permission or publication approval.
- Direct imports are limited to `internal/jsonfieldscan/`.
- `tidwall/match v1.1.1` and `tidwall/pretty v1.2.0` are approved only as exact transitives.
