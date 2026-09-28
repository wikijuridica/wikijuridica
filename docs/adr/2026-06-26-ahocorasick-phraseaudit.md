# Aho-Corasick Phrase Audit Adapter

`github.com/coregx/ahocorasick` v0.2.1 is adopted only behind `internal/phraseaudit` for blocked phrase scans in public quality gates.

The adapter is used to speed up residual phrase detection over 10k and larger public prose surfaces while preserving word-boundary and overlap behavior covered by tests. It does not fetch, scrape, render, approve, publish, write sitemap entries, or open public flags.

Approved scope:

- Imports only in `internal/phraseaudit/`.
- Data/evidence only in blocked internal JSONL.
- Public artifacts remain fail-closed until the release gates pass.

Policy and semantics:

- License is MIT in the local module cache for `github.com/coregx/ahocorasick@v0.2.1`.
- Runtime transitives are zero third-party modules for this adapter path.
- `Matcher` preserves caller-owned normalization: it lowercases and collapses spaces, but it does not remove punctuation or fold accents.
- Callers that need PT-BR folding or punctuation boundaries must pass token-normalized text or words, as `publicproselanguagepatterns` does through `normalizedText`.
- Boundary, overlap and accent behavior are locked in `internal/phraseaudit` tests.

Benchmark evidence:

- Evidence path: `data/ops/ahocorasick_phraseaudit_evidence.jsonl`.
- Command: `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test ./internal/phraseaudit -run '^$' -bench PhraseAudit -benchmem -benchtime=100ms -count=1`.
- Latest blocked benchmark on 2026-06-29: `BenchmarkPhraseAuditMatcherCountNormalizedWords-8`, 1,370 iterations, 88,904 ns/op, 85.65 MB/s, 69,000 B/op and 16 allocs/op on synthetic internal text.
