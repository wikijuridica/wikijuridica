# ADR: tdewolff HTML minify

## Status

Approved for internal blocked runtime use.

## Decision

Adopt `github.com/tdewolff/minify/v2 v2.24.13` only behind `internal/htmlminify/` and `internal/htmlpolicy/`.

The minifier is guarded by HTML contract validation and visible-text parity checks. It cannot approve render, sitemap, `public_path` or publication.

## Constraints

`github.com/tdewolff/parse/v2 v2.8.12` is approved only as exact transitive.
