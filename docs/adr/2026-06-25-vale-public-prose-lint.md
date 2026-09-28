# ADR: Vale para Lint Editorial Bloqueado da Prosa Publica

Date: 2026-06-25
Updated: 2026-06-30

## Decision

Adopt `github.com/errata-ai/vale/v3/cmd/vale` as an open source editorial lint gate for the blocked `refined_public_prose` corpus. Vale must run against real 10k corpus Markdown shards generated from `data/editorial/refined_public_prose.jsonl`, not only against a token fixture.

- Module/command: `github.com/errata-ai/vale/v3/cmd/vale`
- Pinned version: `v3.15.1`
- License: MIT
- Source repository: `https://github.com/vale-cli/vale`
- Documentation: `https://vale.sh/docs`
- Versioned style pack: `tools/vale-public-prose`
- Project checks: `vale-public-prose-lint`, `vale-public-prose-lint-release`
- Evidence: `data/ops/vale_public_prose_lint_evidence.jsonl`

## Scope

The adapter now has two layers:

- A local parallel Go scanner reads the full blocked refined prose text and catches all `publicprosemechanical` blockers, including tokens that Vale's existence rule does not match reliably when punctuation is semantically part of the phrase.
- Vale reads versioned Markdown shards from the real 10k corpus using `tools/vale-public-prose/.vale.ini` and `tools/vale-public-prose/styles/PortalJuridico/*.yml`. The style-pack self-test remains only a small rule-health check and is not accepted as corpus coverage.

Evidence must store `style_pack_sha256`, `style_rule_count`, `vale_corpus_record_coverage`, `vale_corpus_file_count`, `vale_corpus_input_bytes`, `vale_corpus_alert_count`, worker count, duration and public-write flags. Release validation fails if the evidence references `vale-token-validation.md`, lacks the live style-pack hash, has stale input fingerprint, has `vale_corpus_record_coverage != input_records`, or has any alert.

The integration must not write `public/`, `content/pages.json`, `published_manifest`, real sitemap files or public flags. The normal check validates stored evidence; the release check fails closed while any Vale alert remains.

## Risk

Supply-chain risk is medium: Vale is a mature open source CLI with an MIT license, but it runs as a development tool with transitive dependencies. The integration pins the module version, stores module/license/source metadata, runs through a narrow adapter, and records no public publication approval.

Operational risk is medium: sending all 10k records as one large Markdown file to a CLI is a scale bug and does not preserve the path to 100k/1M/100M pages. The adapter writes bounded shards and runs Vale over those shards with controlled parallelism. Vale exits with status 1 when it finds alerts; the adapter treats that exit code as valid lint evidence, parses the JSON payload per shard, records the alert count, and leaves publication blocked until the release gate is clean.

## Validation

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/valepublicproselint`
- `GOBIN=/tmp/opt-wiki-tools GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern install github.com/errata-ai/vale/v3/cmd/vale@v3.15.1`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/generate-vale-public-prose-lint --dry-run --timings --checked-at 2026-06-30`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/generate-vale-public-prose-lint --timings --checked-at 2026-06-30`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/check-vale-public-prose-lint --timings --max-duration 30000ms`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/check-vale-public-prose-lint-release --timings --max-duration 30000ms`
