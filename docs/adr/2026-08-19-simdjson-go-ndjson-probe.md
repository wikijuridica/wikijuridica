# ADR 2026-08-19: simdjson-go como sonda SIMD de validade NDJSON, com fallback obrigatório

Status: ADR **retroativo**. A dependência entrou em `go.mod` no commit `1b098d1c` (2026-07-03, "integrate open source scale gates") sem ADR; este documento registra o estado medido em 2026-08-19.

## Contexto

O banco de dados do projeto é JSONL: dezenas de arquivos em `data/editorial/`, `data/ops/` e `data/research/`, somando centenas de milhares de linhas e centenas de MB. Os gates de escala precisam varrer essa massa repetidamente, e "lentidão em 10k é bug P0" pelo contrato do repositório. Validar sintaticamente cada linha com o decodificador padrão custa caro quando o objetivo é apenas garantir que o fluxo é JSON válido antes de extrair alguns campos quentes.

`simdjson-go` parseia JSON usando instruções vetoriais (AVX2/AVX512), com ganho grande sobre parsers escalares — **quando a CPU suporta**. Como o projeto roda em máquina fixa mas precisa ser reprodutível em qualquer host, a dependência só é aceitável com caminho de fallback.

## Versão fixada e licença

- Módulo: `github.com/minio/simdjson-go`, versão **`v0.4.5`**, fixada em `go.mod` linha 30.
- Licença: **Apache-2.0**, lida em `~/go/pkg/mod/github.com/minio/simdjson-go@v0.4.5/LICENSE`.
- Constantes de proveniência no código, batendo com o disco: `internal/jsonfieldscan/simdjson.go:12-14` (`SIMDJSONModule`, `SIMDJSONVersionPinned = "v0.4.5"`, `SIMDJSONLicense = "Apache-2.0"`).

## Onde é usada de fato

Import único: `internal/jsonfieldscan/simdjson.go:8` (`simdjson "github.com/minio/simdjson-go"`). Superfície de uso deliberadamente mínima — duas chamadas à biblioteca:

- `simdjson.SupportedCPU`, capturado em variável de pacote (`simdjson.go:34`) para permitir substituição em teste, exposto por `SIMDJSONSupportedCPU()` (`simdjson.go:36`).
- `simdjson.ParseND(trimmed, nil)` em `ValidateNDJSONWithSIMDJSON` (`simdjson.go:54`) — parse NDJSON, resultado descartado; só interessa se houve erro.

**Invocação real** (não apenas alcance): `internal/jsonlstream/stream.go:601` chama `jsonfieldscan.ValidateNDJSONWithSIMDJSON(simdjsonProbe.Bytes())` sobre uma amostra do fluxo, e `stream.go:248`, `367`, `370`, `423`, `568` e `621` consultam `SIMDJSONSupportedCPU()` para decidir e registrar o caminho tomado. É o gate `jsonl-stream-benchmark` que exercita a dependência.

O fallback é parte do contrato de uso, não um extra: `ValidateNDJSONFast` (`simdjson.go:62`) tenta o caminho SIMD e, **apenas** quando o erro é `ErrSIMDJSONUnsupportedCPU`, cai para `validateNDJSONWithGJSONLineScan` (`simdjson.go:70`). Erro de JSON de verdade propaga — o fallback cobre CPU, não corrige dado inválido. A política está escrita no próprio pacote (`simdjson.go:15-16`): `SIMDJSONUsePolicy = "controlled_ndjson_probe_with_gjson_streaming_fallback_no_publication"`.

## Runtime de produção: NÃO no servidor; SIM no pipeline de gates e release

Distinção que importa: `cmd/server`, `cmd/build` e `cmd/publish-v2-direct` **não alcançam** `simdjson-go`. Nenhuma requisição HTTP, nenhum HTML gerado e nenhuma promoção direta de página passa por esta dependência.

Ela é alcançada por 60 entrypoints, entre eles `cmd/check`, `cmd/factory`, `cmd/generate-refined-public-prose`, `cmd/promote-authorial-mass-public-release` e `cmd/snapshot-public-release` — o pipeline de conteúdo e de release. (Contagem por grafo estático de imports; `//go:build` não avaliado, portanto 60 é limite superior. Os três entrypoints citados como "não alcançam" foram conferidos e não têm build tag.)

Nenhuma flag pública é aberta por ela: a evidência que a registra declara `publication_allowed`, `render_allowed`, `sitemap_allowed` e `approval` em `false`, `public_path` vazio e `index_policy: "noindex"`.

## Benchmark: REALIZADO sobre dado vivo

`data/ops/jsonl_stream_benchmark_evidence.jsonl`, gerado por `internal/jsonlstream`:

- `live_record_count: 40000` registros reais, `live_byte_count: 667.992.262` bytes (≈ 668 MB)
- `scan_duration_ms: 8043`, `records_per_second: 4973`, `bytes_per_second: 83.052.624`
- `invalid_json_lines: 0`, `public_flag_open_records: 0`
- Por camada, a sonda aparece com resultado próprio; na camada `scaled_content_release_verdict` (10.000 registros, 173.722.583 bytes): `simdjson_probe_supported: true`, `simdjson_probe_validated: true`, `simdjson_probe_records: 243`, `simdjson_probe_bytes: 4.189.954`

O critério de desempenho gravado é `"jsonl_stream_scan_live_40k_under_10s_..."` — 40k em menos de 10 s, cumprido com 8,04 s.

Leitura honesta desses números: a sonda SIMD roda sobre **amostra** (243 registros / ≈4,2 MB na camada citada), não sobre o fluxo inteiro; os 4.973 registros/s são do scanner de campos quentes como um todo, não atribuíveis ao simdjson isoladamente. **Não medido:** ganho comparativo do caminho SIMD contra o fallback gjson (não existe medição A/B no repositório); 100k e 1M em uma única varredura; comportamento em CPU sem AVX2 (a máquina atual suporta, conforme `simdjson_probe_supported: true`).

## Alternativas consideradas

Decisão histórica **não documentada na época**; este ADR é retroativo. O registro contemporâneo é `internal/ossscaleintegration/coverage.go:1085`, que ancora o módulo à área `performance`, aos artefatos `internal/jsonfieldscan/simdjson.go` e `internal/jsonlstream/stream.go`, e ao check `tools/check-jsonl-stream-benchmark`.

O que se pode afirmar sobre alternativas a partir do código, sem inventar: as alternativas **não foram rejeitadas — coexistem**. O repositório mantém, com ADR próprio, `gjson` (`docs/adr/2026-06-27-gjson-jsonfieldscan.md`), `jsoniter` (`docs/adr/2026-06-28-jsoniter-jsoncodec-adapter.md`) e `segmentio` (`docs/adr/2026-06-25-segmentio-jsoncodec-adapter.md`). O `gjson` é literalmente o fallback desta dependência, no mesmo pacote. A divisão de papéis observável no código é: `simdjson` valida sintaxe do fluxo em massa, `gjson` extrai campo quente e cobre CPU sem SIMD, `jsoniter`/`segmentio` fazem decodificação estruturada. O que não está escrito em lugar nenhum é a comparação que teria motivado somar mais um parser JSON a três já existentes. Não há `Record` de dependência para `simdjson-go` em `internal/codex2policyenforcement/policy.go` (busca por `simdjson-go`: zero ocorrências).

## Risco e saída

Licença Apache-2.0, permissiva. Risco de portabilidade tratado por engenharia, não por sorte: a biblioteca depende de instruções vetoriais e o adapter já trata CPU não suportada como caminho normal, com `ErrSIMDJSONUnsupportedCPU` (`simdjson.go:22`) e fallback testável.

Risco residual: `v0.4.x` é pré-1.0; a superfície usada (`SupportedCPU`, `ParseND`) é mínima e estável, o que limita a exposição a quebra de API. Parsers SIMD têm histórico de CVEs por leitura fora de limites em entrada malformada — mitigação em vigor é o uso restrito a **validação** (resultado descartado) sobre dados que o próprio projeto gerou, nunca sobre entrada de terceiro vinda da rede.

Se a dependência sumisse: **este é o caso de saída mais barato dos sete**. O fallback já está implementado, testado e no mesmo arquivo; `ValidateNDJSONFast` continuaria funcionando via `validateNDJSONWithGJSONLineScan`, com perda de velocidade na validação sintática e nenhuma perda de correção. O trabalho seria remover as duas chamadas de `simdjson.go` e ajustar os campos `simdjson_*` da evidência e do validador em `internal/jsonlstream`. Nenhum impacto em publicação, render, sitemap ou `published_manifest`.

## Consequências

O registro documental exigido pelo contrato passa a existir, com licença lida em disco, versão conferida em `go.mod`, invocação real localizada (`internal/jsonlstream/stream.go:601`) e benchmark citado com os números medidos e com o que não foi medido. A dependência permanece confinada a `internal/jsonfieldscan`; ampliar seu uso para o caminho de render ou de servidor exigiria ADR novo e medição própria.
