# ADR 2026-06-30: Bloom release-frontier dedupe

## Decision

Adopt `github.com/bits-and-blooms/bloom/v3` at `v3.7.1` behind `internal/bloomdedupe` for release-frontier duplicate prefilter evidence.

## Scope

The adapter scans `data/editorial/authorial_mass_manifest_transaction_rehearsal.jsonl`, builds Bloom-filter signals for manifest transaction IDs, unique intent IDs, planned public paths and canonical URLs, then verifies every positive through an exact map. Bloom positives never approve publication. Exact duplicate counts, stale evidence and public flags fail closed.

## Policy

The module is BSD-2-Clause and is approved only for blocked internal evidence:

- allowed imports: `internal/bloomdedupe/`
- evidence: `data/ops/bloom_release_frontier_dedupe_evidence.jsonl`
- public writes: forbidden
- public flags: always false
- index policy: `noindex`

The integration targets 10k now and keeps projected 1M capacity as sizing metadata only. A real 1M readiness claim requires a dedicated benchmark and exact verification.
