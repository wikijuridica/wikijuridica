# ADR: sourcegraph/conc para parallelbatch interno

Data: 2026-07-01

## Decisao

Adotar `github.com/sourcegraph/conc v0.3.0` atras do adapter interno `internal/parallelbatch`, usando `conc/iter.Mapper` para lotes internos CPU-bound com chunks, limite explicito de workers, saida deterministica por indice e metricas de throughput.

## Escopo permitido

- `go.mod` e `go.sum`, somente na versao fixa `v0.3.0`.
- `internal/parallelbatch/`, como pacote autorizado a importar `github.com/sourcegraph/conc/iter`.
- `cmd/generate-parallelbatch-conc-evidence` e `tools/check-parallelbatch-conc-evidence`.
- `data/ops/parallelbatch_conc_evidence.jsonl`, evidencia bloqueada sem publicacao.

## Comparacao OSS

- `sourcegraph/conc`: escolhido porque o README oficial descreve pools, iteradores, stream e objetivos de reduzir vazamento de goroutines, panics e legibilidade; `pkg.go.dev` documenta `iter.Mapper` com `MaxGoroutines`, `MapErr`, ordem de resultados e overhead baixo por elemento. Isso complementa `internal/pipeline`: `x/sync/errgroup` continua sendo o adapter fail-fast/contexto; `parallelbatch` passa a ser o adapter chunked com evidencia de throughput.
- `alitto/pond`: rejeitado neste ciclo. E uma worker pool com metricas, mas duplica a politica de workers fixos ja usada em geradores/checks e adiciona semantica de pool/queue que nao resolve o gargalo escolhido sem migracao mais ampla.
- `panjf2000/ants`: rejeitado neste ciclo. O beneficio principal e reciclar goroutines em carga massiva de submits; o repo ja usa workers fixos/chunks em varios caminhos 10k, entao o ganho seria menor que um adapter chunked ordenado.
- `valyala/fasthttp`: rejeitado nesta frente. Apesar dos benchmarks do README, nao e substituto drop-in de `net/http` e troca a API HTTP sem evidencia de gargalo no runtime publico leve.

## Gates

- Evidencia deve manter `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `approval=false`, `public_path=""` e `index_policy=noindex`.
- `oss-scale-integration-coverage` deve exigir modulo fixo, adapter real, wrapper executavel e evidencia com metricas `input_records`, `worker_count`, `chunk_count`, `duration_ms` e `records_per_second`.
- A integracao nao aprova conteudo, nao altera `published_manifest`, nao renderiza HTML publico, nao escreve sitemap e nao troca o servidor HTTP.

## Autocritica de engenharia

Esta mudanca reduz risco operacional de loops manuais sem metricas ao oferecer uma API reaproveitavel para 10k/100k/1M, mas ainda nao migra um gerador pesado especifico. O proximo ganho real e substituir um loop manual seguro por `parallelbatch.MapIndexed` quando a worktree permitir escopo exclusivo, comparando duracao antes/depois sem reduzir cobertura.
