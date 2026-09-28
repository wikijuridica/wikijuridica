# ADR: bluemonday HTML policy

## Status

Approved for internal blocked runtime use.

## Decision

Adopt `github.com/microcosm-cc/bluemonday v1.0.27` only behind `internal/htmlpolicy/`.

The adapter sanitizes generated HTML in blocked rehearsals. It cannot open `render_allowed`, sitemap, `public_path` or publication.

## Constraints

`github.com/aymerick/douceur v0.2.0` and `github.com/gorilla/css v1.0.1` are approved only as exact transitives.
