# ADR 2026-08-19: Clientes Go de sidecar de busca (Meilisearch, Typesense, OpenSearch)

Status: ADR **retroativo**. As três dependências já estavam em `go.mod` e importadas desde `bfef1e55` (2026-07-03) sem ADR; este documento registra o estado medido em 2026-08-19, não autoriza mudança de escopo.

## Por que um ADR agrupado (e por que Bluge não está aqui)

As três dependências não são três adoções: são **um único adapter**. Os três imports estão no mesmo arquivo, `internal/searchsidecarclients/clients.go` (linhas 7, 8 e 9), atendidos pela mesma função `ProbeClients()` (linha 40), produzindo o mesmo tipo `ClientProbe`, consumidos pelo mesmo caminho (`internal/searchbackendbench.runClientSidecarProbe`, `bench.go:604`) e escritos na mesma evidência (`data/ops/search_backend_benchmark.jsonl`). Separá-las produziria três documentos idênticos exceto pelo nome do módulo — perda de fidelidade, não ganho.

`github.com/blugelabs/bluge` **não** entra neste grupo, embora também seja backend de busca: vive em outro pacote (`internal/searchbackendbench`), é biblioteca de índice embarcado em processo (não cliente HTTP para servidor externo), e — decisivo — tem benchmark real medido, enquanto estas três não têm. Bluge tem ADR próprio: `docs/adr/2026-08-19-bluge-search-backend-benchmark.md`.

## Versões fixadas e licenças (lidas do disco)

| Módulo | Versão (`go.mod`) | Licença | Arquivo lido |
|---|---|---|---|
| `github.com/meilisearch/meilisearch-go` | `v0.36.3` (linha 27) | MIT | `~/go/pkg/mod/github.com/meilisearch/meilisearch-go@v0.36.3/LICENSE` ("MIT License / Copyright (c) 2020-2025 Meili SAS") |
| `github.com/typesense/typesense-go/v3` | `v3.2.0` (linha 39) | Apache-2.0 | `~/go/pkg/mod/github.com/typesense/typesense-go/v3@v3.2.0/LICENSE` |
| `github.com/opensearch-project/opensearch-go/v4` | `v4.6.0` (linha 32) | Apache-2.0 | `~/go/pkg/mod/github.com/opensearch-project/opensearch-go/v4@v4.6.0/LICENSE.txt` |

O módulo OpenSearch traz também `NOTICE.txt` no mesmo diretório: a cláusula 4(d) da Apache-2.0 obriga a propagar esse NOTICE em qualquer redistribuição do binário. O projeto não redistribui binários hoje; se passar a redistribuir, o NOTICE acompanha.

Typesense tem uma armadilha de leitura: o **caminho do módulo** é `github.com/typesense/typesense-go/v3`, mas o **caminho importado** é `github.com/typesense/typesense-go/v3/typesense` (`clients.go:9`). Procurar o import pelo caminho do módulo não acha nada.

## Onde é usada de fato

Import único, um por módulo, todos em `internal/searchsidecarclients/clients.go`:

- `clients.go:7` — `meilisearch "github.com/meilisearch/meilisearch-go"`, usado em `probeMeilisearch` (linha 70): `meilisearch.New("http://127.0.0.1:7700", meilisearch.WithCustomClient(client))`.
- `clients.go:8` — `opensearch "github.com/opensearch-project/opensearch-go/v4"`, usado em `probeOpenSearch` (linha 49): `opensearch.NewClient(opensearch.Config{Addresses: []string{"http://127.0.0.1:9200"}, ...})`.
- `clients.go:9` — `typesense "github.com/typesense/typesense-go/v3/typesense"`, usado em `probeTypesense` (linha 85): `typesense.NewClient(typesense.WithServer("http://127.0.0.1:8108"))`.

O uso real, em todos os três casos, é **construção do cliente contra loopback**, com `http.Client{Timeout: 500ms}` (linha 41). Nenhuma das três funções indexa documento, executa consulta ou abre conexão de rede: a única asserção é `ClientConstructed`.

Consumidores do adapter: `internal/searchbackendbench/bench.go`, `internal/ossscaleintegration/coverage.go`, `internal/ossinstallmatrix/matrix.go`.

## Runtime de produção: NÃO

Medição por grafo estático de imports a partir de cada `main.go` de `cmd/`:

- `cmd/server`, `cmd/build`, `cmd/publish-v2-direct`: **não alcançam** nenhum dos três módulos.
- Alcançam: `cmd/check`, `cmd/generate`, `cmd/generate-check-performance-ledger`, `cmd/generate-oss-installation-matrix`, `cmd/generate-search-backend-benchmark` — 5 entrypoints, todos de gate/evidência.

Nenhum dos três participa de servir HTTP, renderizar HTML, escrever `public/`, sitemap ou `published_manifest`. O próprio adapter declara `PublicServing: false` e `LoopbackOnly: true` em cada probe. Ressalva de método: o walker não avalia `//go:build`; os quatro entrypoints citados foram conferidos e não têm build tag, então esta conclusão não depende de tags.

## Benchmark 10k/100k: NÃO REALIZADO

O contrato exige benchmark 10k/100k para dependência que afete runtime. Como não afetam runtime de produção, a exigência não se aplica — **e o benchmark não existe mesmo**, o que precisa ficar escrito com todas as letras porque o arquivo de evidência aparenta o contrário.

`data/ops/search_backend_benchmark.jsonl` registra, para cada um dos três: `index_built: true`, `ingest_records: 10000`, `ingest_p95_ms: 1`, `query_p95_ms: 1`, `real_dependency_verified: true`. **Nenhum desses números é medição.** São literais escritos em `internal/searchbackendbench/bench.go:625-631`, dentro de `runClientSidecarProbe`, na volta de uma função cuja única condição é `probe.ClientConstructed` ser verdadeiro (linha 609). Não há ingestão nem consulta: `IngestRecords: len(docs)` copia o tamanho do corpus carregado, e `IngestP95MS: 1` / `QueryP95MS: 1` são constantes.

O que está de fato comprovado sobre estas três dependências: **o módulo existe na versão fixada e o construtor do cliente retorna um objeto não-nulo**. Nada além disso. Benchmark real exigiria subir os três serviços (Meilisearch, Typesense, OpenSearch) localmente — não foi feito, e este ADR não afirma que foi.

## Alternativas consideradas

Decisão histórica **não documentada na época**; este ADR é retroativo. O que existe de fonte primária contemporânea é a declaração de intenção em `internal/ossinstallmatrix/matrix.go:476-521`, que para cada um dos três registra `BenchmarkPlan` ("loopback-only client construction plus controlled ... sidecar benchmark over the 10k legal corpus") e `AdapterPlan` ("constructs ... client for controlled sidecar; no public service route"). Isto é, a intenção registrada era prontidão de sidecar controlado, com o benchmark real ainda por fazer — o que bate com o estado medido.

O que **não** há é registro de comparação entre as três, nem de por que manter as três simultaneamente em vez de escolher uma. A hipótese aparente — manter os três clientes para poder comparar motores antes de escolher — não está escrita em lugar nenhum e não será inventada aqui. Não há registro em `internal/codex2policyenforcement/policy.go`: as três não têm `Record` de dependência nesse registro (busca por `meilisearch`, `typesense` e `opensearch` no arquivo: zero ocorrências).

## Risco e saída

Risco de licença: baixo. MIT e Apache-2.0, ambas permissivas e compatíveis com o uso interno; nenhuma delas coleta, copia ou publica texto jurídico.

Risco de supply chain: baixo-médio. São três clientes HTTP com árvore de dependências própria, linkados em 5 binários de gate, para entregar exatamente uma asserção (o construtor não retorna nulo). A razão custo/benefício é ruim — três árvores de dependência para uma verificação que um teste de compilação daria.

Se a dependência sumisse: `cmd/server`, `cmd/build` e `cmd/publish-v2-direct` continuam compilando e funcionando — o acervo público não é afetado. O que quebra é o benchmark de busca: `search_backend_benchmark` exige `required_backend_count: 9` e falha fechado quando um backend não completa (`PerformanceCriteria: "...fail_closed_when_real_binary_module_or_sidecar_client_missing"`), então remover qualquer um dos três reprova esse gate até a lista de backends obrigatórios ser reduzida. Custo de saída real: editar `BackendSpecs()`/`RequiredBackendIDs()` em `internal/searchbackendbench`, `internal/ossinstallmatrix` e `internal/ossscaleintegration`. Não há acoplamento com publicação, render, sitemap ou `published_manifest`.

## Consequências e pendência registrada

Este ADR regulariza o registro documental exigido pelo contrato de engenharia, e **não** valida os números de benchmark que estão na evidência. Fica registrado como defeito a corrigir em sessão dedicada: `internal/searchbackendbench/bench.go:625-631` escreve campos de evidência (`index_built`, `ingest_records`, `ingest_p95_ms`, `query_p95_ms`) como se fossem medidos sem que a ação correspondente tenha sido executada — exatamente o que a política anti-fraude do repositório proíbe. A correção correta é uma das duas: medir de verdade contra sidecars locais, ou emitir `index_built: false` com `probe_detail` explicitando que só houve construção de cliente.
