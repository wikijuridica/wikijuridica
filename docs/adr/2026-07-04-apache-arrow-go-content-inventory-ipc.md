# ADR: Apache Arrow Go no inventario IPC bloqueado

## Decisao

Adotar `github.com/apache/arrow-go/v18 v18.6.0` como dependencia runtime direta para `internal/contentinventoryarrow`, gerando um sidecar IPC derivado do inventario Parquet canonico.

## Escopo

- `internal/contentinventoryarrow/` e `cmd/generate-content-inventory-arrow/`.
- Evidencias `data/ops/content_inventory_arrow_evidence.jsonl` e sidecar `data/ops/content_inventory.arrow`.
- Transitivos Arrow aprovados apenas como indiretos exatos dessa versao: `apache/thrift`, `flatbuffers`, `xxh3`, `brotli` e `lz4`.

## Contrato

- JSONL editorial continua sendo fonte canonica; Parquet continua sendo ponte de inventario.
- Arrow IPC e derivado interno bloqueado: nao publica, nao renderiza, nao escreve `public/`, `content/pages.json`, sitemap real ou `published_manifest`.
- `content-inventory-arrow` exige 10k rows, roundtrip, hash do Parquet fonte, hash do sidecar, schema fingerprint, batches limitados, allocator final zero e flags publicas fechadas.
- Nenhuma prontidao 10M pode ser declarada sem benchmark 10M dedicado.
