# ADR: simplemma PT-BR Lemma Audit

Date: 2026-06-26

## Decision

Adopt `simplemma==1.2.0` as an offline Python oracle for PT-BR lemmatization evidence used by blocked public prose quality checks.

## Scope

The integration lives behind `tools/generate-simplemma-ptbr-lemma-audit`, `tools/requirements-simplemma-ptbr.txt` and `internal/simplemmaptbr`. It reads `data/editorial/refined_public_prose.jsonl`, writes `data/ops/simplemma_ptbr_lemma_audit.jsonl`, and validates only blocked evidence.

## Risk Controls

- Version is pinned to `simplemma==1.2.0`.
- Evidence must keep `approval=false`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""` and `index_policy=noindex`.
- The tool must not write `public/`, `content/pages.json`, sitemap files or `published_manifest`.
- The package is used as a lemma oracle, not as a public prose rewriter and not as a legal source.

## Reason

PT-BR legal pages need dedupe and anti-template checks that understand inflection. Lemma evidence complements existing Go stemming and similarity checks without introducing a heavy model into runtime.
