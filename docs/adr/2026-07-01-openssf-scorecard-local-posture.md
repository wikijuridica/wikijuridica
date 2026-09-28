# ADR: OpenSSF Scorecard local posture gate

Date: 2026-07-01

## Status

Accepted for blocked local evidence only.

## Context

The existing SCA stack already covers SBOM generation with CycloneDX, vulnerability checks with OSV Scanner and govulncheck, Go static analysis with gosec and staticcheck, secret scanning with Gitleaks, pkgsite audit, go.mod parsing, work-reuse ledger, artifact provenance and storage policy. A new integration must avoid duplicating those surfaces.

Compared options:

- OpenSSF Scorecard: covers repository and release policy posture such as binary artifacts, workflow hazards, pinned dependencies, SAST signals, security policy and token permissions.
- GitHub dependency-review-action: useful for pull request dependency diffs, but overlaps with OSV and CycloneDX license policy and depends on GitHub PR context.
- slsa-verifier: useful after release artifacts and provenance exist, but there is no approved public release artifact in this worktree to verify.
- Semgrep OSS: useful general static analysis, but duplicates the current Go static stack for the immediate local scope.

Sources:

- https://github.com/ossf/scorecard
- https://scorecard.dev/
- https://github.com/ossf/scorecard/blob/main/docs/checks.md
- https://github.com/ossf/scorecard/releases/tag/v5.5.0
- https://github.com/actions/dependency-review-action
- https://github.com/slsa-framework/slsa-verifier
- https://github.com/semgrep/semgrep

## Decision

Install `github.com/ossf/scorecard/v5` in the isolated `tools/sca/scorecard` module and add a local blocked evidence gate named `sca-scorecard`.

Scorecard stays in its own tool module because the existing `tools/sca` module includes OSV Scanner, whose graph selects `go.yaml.in/yaml/v4@v4.0.0-rc.4`; Scorecard v5.5.0 currently reaches `github.com/rhysd/actionlint` against the `rc.3` YAML API. Keeping the modules separate avoids weakening the existing OSV toolchain or adding a broad replace directive.

The selected local checks are:

- `Binary-Artifacts`
- `Dangerous-Workflow`
- `Pinned-Dependencies`
- `SAST`
- `Security-Policy`
- `Token-Permissions`

The evidence file is `data/ops/sca_scorecard_evidence.jsonl`. It stores only normalized counters, check summaries, hashes and public-flag state. The raw Scorecard JSON is not stored. Any low score or unavailable check blocks release posture evidence and does not open publication, rendering, sitemap or approval flags.

The local invocation materializes a temporary clean worktree from `git ls-files --cached --others --exclude-standard` before running Scorecard. This keeps repository and relevant untracked files in scope while excluding ignored local caches such as virtualenvs. The generator rejects `.git`, `.cache`, parent-escaping paths and symlinks instead of silently producing a green result.

## Consequences

This integration complements the existing SCA stack by checking release and repository policy posture instead of package vulnerability, license or Go source findings. It is local evidence for engineering and supply-chain hardening only. It must not touch `public/`, `content/pages.json`, `published_manifest`, sitemap or robots artifacts.
