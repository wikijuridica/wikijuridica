# ADR: segmentio/encoding para JSONL bloqueado

Data: 2026-06-25

## Decisao

Adotar `github.com/segmentio/encoding v0.5.4` somente atras do adapter interno `internal/jsoncodec`, para acelerar leitura e escrita de JSON/JSONL em geradores e validadores bloqueados da fabrica P0.

## Escopo permitido

- `go.mod` e `go.sum`, somente na versao fixa `v0.5.4`.
- `github.com/segmentio/asm v1.1.3`, somente como dependencia indireta fixa de `segmentio/encoding`.
- `internal/jsoncodec/`, como unico pacote autorizado a importar `github.com/segmentio/encoding/json`.
- `data/ops/jsoncodec_segmentio_evidence.jsonl`, como evidencia bloqueada sem publicacao.

## Racional tecnico

Os caminhos P0 leem e escrevem JSONL em lotes de 10k registros e precisam crescer para 100k/1M sem depender de parsers ad hoc. O benchmark local mostrou ganho material em unmarshal de payload juridico representativo, com custo de marshal equivalente ao stdlib. O adapter centralizado evita que pacotes de dominio importem a dependencia diretamente e preserva `DisallowUnknownFields` onde o contrato exige schema fechado.

## Gates

- Import direto de `github.com/segmentio/encoding` fora de `internal/jsoncodec/` deve falhar em `codex2-policy-enforcement`.
- Evidencia deve manter `approval=false`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""`, `raw_text_stored=false`, `scraping_allowed=false` e `ingestion_allowed=false`.
- A dependencia nao aprova conteudo, nao abre `published_manifest`, nao renderiza pagina, nao altera sitemap e nao substitui hashes oficiais SHA-256.
- Qualquer expansao para novos loaders deve passar por `internal/jsoncodec` e teste funcional do pacote consumidor.

## Licenca e risco

`github.com/segmentio/encoding` declara licenca MIT e `github.com/segmentio/asm v1.1.3` declara licenca MIT. O risco principal e divergencia semantica de JSON em relacao a `encoding/json`; mitigacao: adapter unico, testes de round-trip PT-BR, strict decode, versoes fixas, SCA e policy gate antes de commit.
