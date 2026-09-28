# SCALE.md — Arquitetura de escala para milhões (P3) e busca própria (P5)

Baseado em investigação de código real (2026-07-07). Veredito por componente: **A** funcional · **B** implementado mas evidência sintética/hardcoded · **C** ausente/stub.

## O que já existe (não reinventar)

O repositório tem infraestrutura de escala/busca **real e substancial**, quase toda committada como evidência bloqueada (`no_public_runtime`), aguardando ser exercida e servida:

| Camada | Pacote | Veredito | Nota |
|---|---|---|---|
| Contentstore shardado | `internal/contentstore` | A | shards físicos `content/page_shards`, offsets int64, SHA256 por entry, releases versionados, lock, journal, `VerifyRelease` |
| Índice KV sidecar | `internal/contentstorepebble` (Pebble) | A/B | write em lotes, swap atômico; evidência pequena |
| Benchmark KV multi-backend | `internal/contentstorekvbench` | A capaz | badger v4 + pebble v2 + sqlite; alvos {10k,100k,1M}; **fail-closed honesto** (não reivindica 1M sem exercer 1M) |
| Índice de escala | `internal/scaleindex` (SQLite+roaring) | B | `ChangedShardsSince`, `LookupManyGroupedByShard`; projeção `1000000` hardcoded, rejeita claim sem benchmark |
| Worker pool paralelo | `internal/parallelbatch` (`sourcegraph/conc`) | A | `MapIndexed` com MaxGoroutines |
| Inventário colunar | `contentinventoryparquet`/`arrow` | A/B | parquet-go + arrow-go reais |
| Dedupe SimHash+buckets | `internal/dedupeexternaloracle` (`mfonda/simhash`+`zoekt`) | A@10k | janela de bucket limitada; declara "100k_1m_requires_shard_workers" |
| ANN | `internal/hnswcandidateindex` (`coder/hnsw`) | A@10k | vizinhança, não all-pairs |
| MinHash | `internal/legalminhash` (`dgryski/go-minhash`) | A | bottom-k sobre shingles xxhash64 |
| Clustering | `internal/semanticclusterindex` | A | union-find sobre arestas pré-computadas |
| Busca Bleve | `internal/codex2bleveindex` (`blevesearch/bleve`) | B | `bleve.New` persistente + swap atômico; `no_public_runtime` |
| FTS5 / FST | `sqlitefts5corpus` / `fstcontentindex` (vellum) | B | reais, evidência-only |
| Parser HTML | `htmlpolicy`/`htmlreadability` (`x/net/html`+readability+bluemonday) | A | robusto |
| Robots RFC 9309 | `temoto/robotstxt`, `jimsmart/grobotstxt` | A | matcher real (usado em auditoria do próprio site) |

## Gaps concretos (o trabalho de P3/P5)

### P3 — capacidade de 1M em inventário, sem O(n²)
1. **Benchmark 1M reproduzível — ✅ CUMPRIDO (2026-07-07).** `cmd/bench-scale-1m` exercitou **1.000.000 de registros reais** nos 3 backends (pebble/badger/sqlite). Resultados: pebble write p50/p95/p99=1/1/1µs, read p50=302µs; badger read p50=19µs; sqlite write p50=53µs. **Latências p50/p95/p99 estáveis de 10k→100k→1M** (ex.: badger scan 14→35→87µs) e **memória linear** (peak RSS 1.8GB para 1M) — prova de que **não é O(n²)** (`latency_stability_ratio`, `not_quadratic_proven` na evidência). Throughput 11.374 rec/s em 1M. Evidência em `data/ops/scale_1m_benchmark_evidence.jsonl`; a claim `OneMillionCapacityClaimed` foi destravada honestamente em `scaleindex` (fail-closed, só com o benchmark real on-disk, amarrada por SHA256).
2. **Compaction/rebuild incremental do contentstore.** Hoje há releases append-only + `RebuildPathIndex` em memória; falta delta-merge de shards alterados (senão churn reescreve diretórios inteiros — O(n·releases)). Ação: `ChangedShardsSince` já existe no scaleindex; wire um rebuild que só reescreve shards com fingerprint alterado.
3. **Pipeline de dedupe sharded para 100k/1M.** HNSW+buckets evitam all-pairs a 10k; falta LSH-banding por bucket + HNSW por shard (worker pool `parallelbatch` já existe) + merge cross-shard. Ação: encadear os componentes existentes num gerador sharded.

### P5 — busca própria servida + grafo
1. **Servir Bleve em `/buscar/`.** `codex2bleveindex` já tem build persistente + swap atômico; falta promover a índice servido atrás de `/buscar/` no `internal/httpserver` (hoje `/buscar/` é página estática noindex). Manter noindex na SERP interna (contrato). Índice é derivado/reconstruível.
2. **Grafo jurídico consultável.** `semanticclusterindex` (union-find) e `hnswcandidateindex` são evidência-only; expor como "páginas relacionadas" (links internos derivados do cluster) — reforça a arquitetura de links internos e a autoridade tópica.
3. **Reconciliação de contagem Bleve↔manifest** (observabilidade P4/P5).

## Princípio de escala (para o conteúdo)
A cadeia editorial foi desacoplada do número 10.000 (DEC-014): total dirigido pelo `stock_manifest`, agrupamento por practice_area, similaridade por buckets/ANN (não all-pairs). Isso é o que permite crescer de 6.353 → 10.000 → centenas de milhares sem reescrever a fábrica. A prova de 1M vive no benchmark sintético (P3), separada da validação de conteúdo real.

## Ordem recomendada
P0 (10k páginas publicadas) primeiro — é o marco e o gargalo real (redação). P3/P5 usam infraestrutura já pronta: o benchmark 1M e o wire da busca Bleve são executáveis com custo controlado e podem correr em paralelo à redação quando o orçamento permitir.
