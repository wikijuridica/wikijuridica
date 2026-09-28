# ADR: pkg.go.dev module audit with golang.org/x/mod

Status: adopted internal blocked no-publication

`internal/pkgsiteaudit` uses `golang.org/x/mod/modfile` at `v0.36.0` to parse `go.mod` structurally before querying the official pkg.go.dev API for module metadata and license types.

The adapter is restricted to dependency-governance evidence in `data/ops/pkgsite_module_audit.jsonl`. It does not write `public/`, `content/pages.json`, `published_manifest`, sitemap, robots, rendered content, source text, or public flags.

The integration replaces ad hoc `go.mod` parsing in the high-scale open-source audit path and keeps publication blocked by contract until the normal release gates approve content independently.
