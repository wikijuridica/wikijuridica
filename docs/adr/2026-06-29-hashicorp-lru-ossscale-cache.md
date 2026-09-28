# 2026-06-29 - HashiCorp LRU for OSS Scale Coverage Cache

## Decision

Adopt `github.com/hashicorp/golang-lru/v2` at `v2.0.7` only inside `internal/ossscaleintegration` to cache expected OSS integration evidence file bodies by path, size and modification time.

## Scope

The cache is an internal validation accelerator. It does not fetch network data, does not store public content, does not touch `public/`, `content/pages.json`, `published_manifest`, sitemap or robots output, and does not approve publication.

## Scale Reason

`oss-scale-integration-coverage` validates many expected integrations and several of them share the same JSONL evidence files. Without a bounded cache, the gate repeatedly reads and scans the same files during a single validation. A fixed LRU keeps the gate proportional as the integration matrix grows for 10k, 100k and 1M page factories.

## Risk

The dependency is MPL-2.0 and already existed in the module graph transitively. Runtime import is restricted to `internal/ossscaleintegration`; the evidence file and policy gate keep public flags closed.
