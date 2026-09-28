# ADR: parquet-go no inventario colunar bloqueado

Data: 2026-06-29

## Decisao

Adotar `github.com/parquet-go/parquet-go v0.30.1` como dependencia runtime direta para `internal/contentinventoryparquet`, gerando um sidecar colunar derivado de JSONL canonico.

## Escopo permitido

- `go.mod` e `go.sum`, somente na versao fixa `v0.30.1`.
- `internal/contentinventoryparquet/` e `cmd/generate-content-inventory-parquet/`.
- Evidencias `data/ops/content_inventory_parquet_evidence.jsonl` e sidecar `data/ops/content_inventory.parquet`.
- Transitivos Parquet aprovados apenas como indiretos exatos dessa versao: `brotli`, `klauspost/compress`, `parquet-go/bitpack`, `parquet-go/jsonlite`, `pierrec/lz4/v4` e `twpayne/go-geom`.

## Racional tecnico

O P0 precisa operar 10k agora e preparar 100k/1M sem scans repetidos em JSONL para todo join, contagem e filtro. O sidecar Parquet reduz custo de leitura analitica, mas nao vira fonte canonica nem canal de publicacao.

## Controles

- `content-inventory-parquet` exige 10k rows, roundtrip, hash da fonte, hash do sidecar, public flags fechadas e `ten_million_benchmark_required=true`.
- O registro `projected_ten_million_ready` deve permanecer falso ate existir benchmark real de 10M.
- `codex2-policy-enforcement` bloqueia import fora do adapter e nao permite `public/`, `content/pages.json`, `published_manifest`, sitemap ou flags publicas.
