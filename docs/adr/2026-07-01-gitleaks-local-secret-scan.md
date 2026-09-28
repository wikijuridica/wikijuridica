# ADR: Gitleaks Local Secret Scan

Date: 2026-07-01

## Decision

Adopt Gitleaks as an isolated local CI/SCA secret-scanning gate:

- source repository: `https://github.com/gitleaks/gitleaks`
- Go module path: `github.com/zricethezav/gitleaks/v8`
- pinned version: `v8.30.1`
- license: MIT
- check: `sca-gitleaks-secrets`

## Scope

The check runs from the isolated `tools/sca` module via `go tool -modfile=tools/sca/go.mod gitleaks dir ...`. It scans source, contracts, CI/tooling and configuration for hardcoded credentials. It excludes bulk generated legal corpora, public build surfaces and local caches through `.gitleaks.toml`.

## Reason

The existing SCA stack covers Go vulnerabilities, OSV lockfiles, SBOM, licenses, gosec and staticcheck. It did not cover accidental secrets in source/config/tooling. Gitleaks fills that gap without adding runtime code, public rendering, content generation or publication behavior.

## Risk Controls

- The root runtime `go.mod` is not changed.
- The tool is pinned only in `tools/sca`.
- The check fails closed when `.gitleaks.toml` is missing.
- Findings are redacted and written only to a temporary report removed after the check.
- The gate is heavy/proportional, selected with SCA changes and release fan-in, not always-run by habit.
- It does not write `public/`, `content/pages.json`, `published_manifest`, sitemap, robots or `.release-staging`.
- It is not a replacement for tests, SCA, source review or publication gates; it only blocks credential leakage.
