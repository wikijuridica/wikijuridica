# ADR: json-iterator no adapter JSON bloqueado

Data: 2026-06-28

## Decisao

Adotar `github.com/json-iterator/go v1.1.12` somente atras de `internal/jsoncodec` para acelerar decode de JSON grande em caminhos bloqueados da fabrica P0.

## Escopo permitido

- `go.mod` e `go.sum`, somente na versao fixa `v1.1.12`.
- `internal/jsoncodec/`, como unico pacote autorizado a importar `github.com/json-iterator/go`.
- Consumidores internos devem chamar `jsoncodec.UnmarshalIterator`; import direto fora do adapter e fuga para artefato publico sao violacoes.
- Evidencia em `data/ops/jsonl_stream_benchmark_evidence.jsonl`, com `json_iterator_module` e `json_iterator_version_pinned`.

## Racional tecnico

O repo ja carregava `json-iterator/go` como transitive e tinha gargalos de decode em `content/pages.json`, contentstore e scanners de JSONL. Promover a dependencia para uso direto e governado remove subutilizacao OSS sem espalhar API externa pela aplicacao.

## Controles

- `codex2-policy-enforcement` exige import scope, ADR, versao exata e evidencia sem flags publicas.
- `jsonl-stream-benchmark` prova varredura de 40k registros com public flags fechadas.
- Decode estrito continua separado em `jsoncodec.UnmarshalStrict`; a dependencia nao aprova schema, conteudo, sitemap, manifest ou publicacao.
