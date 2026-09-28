# ADR 2026-08-19: Bluge como motor de índice embarcado no benchmark de busca

Status: ADR **retroativo**. A dependência entrou em `go.mod` no commit `1b098d1c` (2026-07-03, "integrate open source scale gates") sem ADR; este documento registra o estado medido em 2026-08-19.

## Contexto

O projeto precisa comparar motores de busca candidatos sobre o corpus jurídico real antes de escolher qualquer um para uso interno, e a comparação precisa ser reprodutível sem subir serviço externo. `internal/searchbackendbench` é o banco de provas: mede ingestão e consulta (BM25, frase, termo exato) sobre `data/editorial/refined_public_prose.jsonl` para nove backends, com linha de base em Bleve e SQLite FTS5.

Bluge ocupa nesse banco de provas o papel de segundo motor Go nativo, embarcado em processo, ao lado do Bleve — não é cliente de serviço externo. É por isso que ele **não** está no ADR agrupado dos três clientes de sidecar (`docs/adr/2026-08-19-search-sidecar-clients-meilisearch-typesense-opensearch.md`): pacote diferente, natureza diferente (biblioteca in-process vs. cliente HTTP) e, ao contrário deles, benchmark real medido.

## Versão fixada e licença

- Módulo: `github.com/blugelabs/bluge`, versão **`v0.2.2`**, fixada em `go.mod` linha 16.
- Licença: **Apache-2.0**, lida em `~/go/pkg/mod/github.com/blugelabs/bluge@v0.2.2/LICENSE`.
- Traz dependências indiretas próprias já presentes em `go.mod`: `blugelabs/bluge_segment_api v0.2.0` (linha 66), `blugelabs/ice v1.0.0` (linha 67), `blugelabs/ice/v2 v2.0.1` (linha 68).

## Onde é usada de fato

Import único: `internal/searchbackendbench/bench.go:28`. Uso real, todo dentro do mesmo pacote:

- `bench.go:784` — `bluge.OpenWriter(bluge.InMemoryOnlyConfig())`: índice apenas em memória, nunca em disco.
- `bench.go:790`, `801` — `bluge.NewBatch()`, ingestão em lotes.
- `bench.go:806-811` — `bluge.NewDocument` com `NewTextField` para `title`, `h1`, `body`, `NewKeywordField` para `exact` e `NewCompositeFieldExcluding("_all", ...)`.
- `bench.go:833` — `reader.Search(ctx, bluge.NewTopNSearch(10, query))`.
- `bench.go:2018-2025` — `blugeQuery`: `NewMatchPhraseQuery`, `NewTermQuery`, `NewMatchQuery` conforme o modo.

Constantes de proveniência declaradas em `bench.go:47-49` (`BlugeModule`, `BlugeVersion`, `BlugeLicense`). O despacho está em `bench.go:318` (`case "bluge": result, err = runBluge(docs, modes)`) — caminho distinto do `runClientSidecarProbe` usado pelos clientes de sidecar.

## Runtime de produção: NÃO

Grafo estático de imports a partir dos `main.go`: `cmd/server`, `cmd/build` e `cmd/publish-v2-direct` **não alcançam** `github.com/blugelabs/bluge`. Alcançam apenas 5 entrypoints, todos de gate/evidência: `cmd/check`, `cmd/generate`, `cmd/generate-check-performance-ledger`, `cmd/generate-oss-installation-matrix`, `cmd/generate-search-backend-benchmark`.

Bluge não serve busca pública, não escreve `public/`, não toca sitemap nem `published_manifest`. O índice é `InMemoryOnlyConfig()`, portanto não deixa artefato em disco. A evidência declara `use_policy: "blocked_local_search_backend_benchmark_no_public_runtime_no_public_service"` e `publication_allowed/render_allowed/sitemap_allowed = false`, `index_policy: "noindex"`.

Ressalva de método: o walker de imports não avalia `//go:build`; os entrypoints citados foram conferidos e não têm build tag.

## Benchmark: REALIZADO, medição real

`data/ops/search_backend_benchmark.jsonl`, `evidence_id: search-backend-benchmark-2026-07-05`, `checked_at: 2026-07-05`, sobre `data/editorial/refined_public_prose.jsonl` (`corpus_records: 10000`, `benchmark_records: 10000`). Entrada do backend `bluge`:

- `index_built: true`, `ingest_records: 10000`, `ingest_p95_ms: 3267`
- `query_p95_ms: 1`; por modo: BM25 3 ms, frase 1 ms, exato 1 ms
- `query_hit_count_by_mode`: 10 em cada um dos três modos (índice respondeu, não é verde vazio)
- `aggregation_count: 133`, `aggregation_records: 100000`, `scale_tier_records: [10000, 100000]`

Comparação com o Bleve na mesma execução: Bleve ingere os mesmos 10.000 em `ingest_p95_ms: 1467` (mais rápido na ingestão) e consulta em `query_p95_ms: 3`, com BM25 em 21 ms (mais lento na consulta que os 3 ms do Bluge). Ou seja, Bluge ingere ~2,2x mais devagar e consulta BM25 ~7x mais rápido que o Bleve neste corpus.

**Não medido:** 1M de registros; latência com índice persistido em disco (só houve in-memory); comportamento com concorrência de leitura/escrita. O campo `scale_path` da evidência declara `"10k_now_100k_1m_by_sharded_local_sidecars_without_public_write"` — 100k só foi exercitado na agregação, e 1M é plano, não medição.

## Alternativas consideradas

Bluge é, ele próprio, a alternativa: o banco de provas existe justamente para comparar nove backends (Bleve, Bluge, SQLite FTS5, Tantivy CLI, Sonic, Quickwit e os três clientes de sidecar), com `comparison_baseline_ids: ["bleve", "sqlite-fts5"]`.

O registro contemporâneo da intenção está em `internal/ossinstallmatrix/matrix.go:462-475`: `BenchmarkPlan: "Go-native index/search/aggregation benchmark for 10k and 100k legal documents"` e `AdapterPlan: "internal blocked Bluge benchmark adapter, no public search backend"`. O ADR do Bleve, anterior, existe (`docs/adr/2026-06-17-codex2-bleve-internal-search-adoption.md`) e trata do full-text interno; Bluge nunca teve o seu.

O que **não** está documentado na época: por que manter Bluge além do Bleve depois de medido, dado que o Bleve já tem ADR de adoção e os dois são bibliotecas Go embarcadas com papéis sobrepostos. Este ADR registra o estado, não reconstrói uma decisão que ninguém escreveu. Não há `Record` de dependência para Bluge em `internal/codex2policyenforcement/policy.go` (busca por `blugelabs/bluge` no arquivo: zero ocorrências).

## Risco e saída

Licença Apache-2.0, permissiva, sem obrigação que afete o projeto. `blugelabs/bluge` está em `v0.2.x` — versão pré-1.0, o que significa API sem garantia de estabilidade; a mitigação em vigor é a fixação exata da versão e o isolamento do import em um único arquivo.

Se a dependência sumisse: nada do acervo público é afetado — `cmd/server`, `cmd/build` e `cmd/publish-v2-direct` não a alcançam. O que se perde é um dos dois pontos de comparação Go-nativos do benchmark, e o gate `search_backend_benchmark` reprova por `required_backend_count: 9` até `BackendSpecs()`/`RequiredBackendIDs()` serem ajustados. O Bleve, com ADR próprio e mesma natureza, cobriria o papel de motor embarcado; a perda seria a comparação, não a capacidade.

## Consequências

O registro documental exigido pelo contrato passa a existir para Bluge, com licença lida em disco, versão fixada conferida em `go.mod` e benchmark real citado com os números medidos. Nenhuma flag pública é aberta por este ADR e nada aqui autoriza servir busca pública com Bluge — para isso seriam necessários ADR novo, medição sob carga e passagem pelos gates de publicação.
