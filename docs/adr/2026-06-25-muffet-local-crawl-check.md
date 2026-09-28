# ADR: Muffet para Link/Crawl Check Local Bloqueado

Date: 2026-06-25

## Decision

Adopt `github.com/raviqqe/muffet/v2` only as an external CLI adapter for local-only blocked crawl/link validation of final page rehearsals.

- Module/command: `github.com/raviqqe/muffet/v2`
- Pinned version: `v2.11.5`
- License: MIT
- Source repository: `https://github.com/raviqqe/muffet`
- Package documentation: `https://pkg.go.dev/github.com/raviqqe/muffet/v2`
- Release evidence: `https://github.com/raviqqe/muffet/releases/tag/v2.11.5`
- Project check: `muffet-local-crawl`
- Evidence: `data/ops/muffet_local_crawl_evidence.jsonl`

## Scope

The adapter starts an in-memory `httptest` server from blocked `public_final_page_rehearsal` HTML and invokes Muffet only against `http://127.0.0.1:<port>/`. The invocation uses the pinned module path/version or an explicitly supplied pinned binary path. It includes a local-host include regex, ignores fragments, keeps response budget at 50,000 bytes, and serves support routes for blocked local crawl only.

The adapter must not fetch `wikijuridica.com.br`, write `public/`, write `content/pages.json`, append `published_manifest`, create a real sitemap, open render/publication flags, scrape official sources, or turn external/source links into public content. Non-local links are rewritten to a local suppressed support route before Muffet runs.

## Risk

Supply-chain risk is medium: Muffet is a mature Go project with a recent release and MIT license, but it is a CLI dependency with transitive modules and currently requires a modern Go toolchain. The integration therefore uses an exact version, isolates execution behind `internal/muffetlocalcrawl`, records source/license/release evidence, and keeps runtime crawling local-only.

Operational risk is medium-low: link crawling can become expensive or accidentally remote if misconfigured. Mitigation: target validation rejects non-local URLs, command construction includes only local targets, evidence records `public_domain_accessed=false`, and the read-only check validates stored evidence/fingerprint instead of executing network work on every run.

## Validation

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/muffetlocalcrawl`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern run ./cmd/generate-muffet-local-crawl --dry-run --timings --muffet-bin /tmp/opt-wiki-tools/muffet`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern run ./cmd/generate-muffet-local-crawl --timings --checked-at 2026-06-25 --muffet-bin /tmp/opt-wiki-tools/muffet`
- `./tools/check-muffet-local-crawl`
- `git diff --name-only -- public content/pages.json data/editorial/published_manifest.jsonl public/sitemap.xml public/sitemaps public/robots.txt .release-staging`
