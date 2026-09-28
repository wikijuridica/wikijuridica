# ADR: temoto/robotstxt for blocked robots audit

Date: 2026-06-19

## Decision

Adopt `github.com/temoto/robotstxt` at `v1.1.2` behind `internal/robotsaudit`, with live consumers importing only the internal adapter.

The adapter parses robots.txt evidence for external source audit and keeps every public flag closed. It may mark collection allowed only when a fetched 2xx robots.txt explicitly allows the requested path for the internal research user agent. Missing policy, 5xx, unexpected status and parse ambiguity are blocked for project collection.

As of 2026-06-30, `internal/demandobservations` must run this adapter before textual external content fetches. The collector caches `/robots.txt` per host for the run, evaluates every target URL through `robotsaudit.Evaluate`, blocks the content GET when collection is not allowed, and records parser/status/hash/user-agent evidence on blocked `demand_content_samples` records. Metadata-only autosuggest remains metadata-only and does not use this preflight.

## Constraints

- No scraping authorization is created by this dependency.
- No official or external body can become public content.
- No `public/`, `content/pages.json`, `published_manifest`, sitemap, render or public path can be opened by robots audit.
- Demand textual samples without an allowed robots preflight must fail closed before fetching external content.
- Portal traffic policy is separate: valuable search/user bots are unlimited, training bots are rate-limited by tier in `content/crawl_policy.json`.

## Validation

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/robotsaudit ./internal/crawl`
- `GOCACHE=/tmp/opt-wiki-go-cache go test -count=1 ./internal/demandobservations -run 'RobotsPreflight|OfficialSourcePageTextualSample'`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/codex2policyenforcement ./internal/contract -run Codex2PolicyEnforcement`
- `./tools/check-codex2-policy-enforcement --timings`
- `./tools/check-oss-scale-integration-coverage --timings`
