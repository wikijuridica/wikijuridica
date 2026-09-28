# ADR: LanguageTool Local para Qualidade Linguistica Bloqueada

Date: 2026-06-25

## Decision

Adopt LanguageTool only through a localhost HTTP service as a blocked linguistic-quality gate for PT-BR public prose evidence.

- Service API: `http://localhost:8010/v2/check` or `http://127.0.0.1:<port>/v2/check`
- Project adapter: `internal/languagetoolquality`
- Generator: `cmd/generate-languagetool-quality`
- Project check: `languagetool-quality`
- Evidence: `data/ops/languagetool_quality_evidence.jsonl`

The adapter rejects non-local hosts, rejects HTTPS public API endpoints such as `api.languagetool.org`, sends `language=pt-BR`, enforces request timeout and text-size limits, and writes JSONL evidence with public flags closed. Text from `refined_public_prose` must not be sent to any public external LanguageTool service.

## Scope

The generator samples the blocked 10k `data/editorial/refined_public_prose.jsonl` layer with deterministic stride sampling. The default cap is 200 records so routine checks remain proportional, while the evidence records retain `source_record_count`, `sample_limit`, `sample_strategy`, visible-text hash, endpoint host/path, timeout, match counts, blockers and fail-closed state.

When the local LanguageTool service is unavailable and `--require-service` is false, the generator writes blocked no-publication evidence instead of treating the corpus as linguistically approved. When `--require-service` is true, the command fails closed on local service unavailability. The read-only `languagetool-quality` check validates stored evidence rather than sending text during every release profile run.

The integration must not write `public/`, `content/pages.json`, `published_manifest`, real sitemap files, public paths or publication flags. It is a quality gate for the 10k factory, not a publication transaction.

## Risk

Privacy and publication risk is high if prose is sent to a public external grammar API. Mitigation: endpoint validation permits only local HTTP loopback hosts and `/v2/check`; public LanguageTool API hosts are rejected before any text leaves the process.

Operational risk is medium: checking all 10k pages synchronously can be slow or brittle. Mitigation: evidence generation uses deterministic sampling with a configurable cap, per-request timeout and max text bytes. Release flows can require an available local service with `--require-service`; otherwise evidence remains explicitly blocked and fail-closed.

## Validation

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/languagetoolquality ./cmd/generate-languagetool-quality`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/generate-languagetool-quality --checked-at 2026-06-25 --max-records 200 --timeout 500ms --max-text-bytes 65536 --timings`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/generate-languagetool-quality --dry-run --require-service --checked-at 2026-06-25 --max-records 1 --timeout 50ms --max-text-bytes 65536 --timings`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/check-languagetool-quality`
- `git diff --name-only -- public content/pages.json data/editorial/published_manifest.jsonl public/sitemap.xml public/sitemaps public/robots.txt .release-staging`
