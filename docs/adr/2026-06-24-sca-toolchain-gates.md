# ADR: Isolated SCA Toolchain Gates

Date: 2026-06-24

## Decision

Adopt an isolated Go toolchain module in `tools/sca` for supply-chain analysis gates:

- `golang.org/x/vuln/cmd/govulncheck v1.4.0`
- `github.com/google/osv-scanner/v2/cmd/osv-scanner v2.4.0`
- `github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod v1.10.0`
- `github.com/zricethezav/gitleaks/v8 v8.30.1`

## Scope

The tools run from `tools/sca/go.mod` through wrappers/checks for vulnerability scanning, OSV lockfile scanning, license checking, CycloneDX SBOM generation and local secret scanning. They are development and release gates only; they must not be imported by public runtime code, render pages, write `public/`, update `content/pages.json`, write `published_manifest`, create sitemap entries or approve publication.

`sca-osv` scans the product root `go.mod` lockfile. The `tools/sca/go.mod` lockfile is tracked by Dependabot, SBOM and this ADR, but it is not included in `sca-osv` because OSV Scanner v2.4.0 currently brings vulnerable Docker transitives in its own development-only tool graph with no newer `github.com/docker/docker` tag available in the module list observed on 2026-06-24. Treating that circular toolchain result as product vulnerability would block useful SCA for the legal factory while adding no public runtime protection. The exception is evidence-bound and must be revisited when OSV Scanner or Docker releases a fixed graph.

## Reason

The project now integrates useful open source aggressively. At 10k pages and on the path to 100k/1M URLs, accepting dependencies without an executable SCA gate would create a false green. The isolated module keeps scanner transitives out of the root runtime dependency graph while making supply-chain validation reproducible.

## Risk Controls

- Exact tool versions are pinned in `tools/sca/go.mod`.
- Dependabot tracks both `/` and `/tools/sca`.
- `internal/checks` exposes `sca-govulncheck`, `sca-osv`, `sca-licenses` and `sca-sbom`.
- `internal/checks` exposes `sca-gitleaks-secrets` as a redacted, temporary-report secret scan over source/config/tooling.
- `internal/checkselection` treats root and SCA module changes as heavy supply-chain gates.
- `internal/checkperformance` records tool module/version evidence and 300s heavy budgets.
- Evidence is versioned in `data/ops/sca_toolchain_evidence.jsonl`.
- `generate-sca-sbom` uses `cyclonedx-gomod mod -json -licenses` for both the root module and `tools/sca`; `sca-licenses` then validates the structured license evidence in the versioned SBOM files read-only. This avoids retaining `go-licenses` in the isolated toolchain after its vulnerable `go-git` transitive path became unnecessary and keeps the commit gate bounded.
- `sca-gosec` scans the expanded SCA, provenance and check packages while excluding `G304` path-inclusion findings, because these packages intentionally read project-root artifacts; package coverage remains active for other gosec rules.
- Public flags remain false: no render, sitemap, public path or approved publication.
