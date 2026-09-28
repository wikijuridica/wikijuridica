# ADR 2026-07-01: Vellum FST para indice lexical bloqueado de conteudo

Status: adotado para evidencia bloqueada, sem publicacao.

## Contexto

A frente P0 precisa reduzir gargalos de busca, dedupe, similaridade e indexacao em 10k/100k/1M URLs sem tocar `public/`, `content/pages.json`, `published_manifest`, sitemap real ou robots. O repositorio ja tem Bleve, Pebble, Roaring, Bloom, MinHash, HNSW, xxhash, Parquet, SQLite, HyperLogLog, zstd, HdrHistogram, go-readability, Trafilatura, LanguageTool, Vale, Simplemma e SCA.

## Alternativas comparadas

- `github.com/mfonda/simhash`: nao foi adotado para construir o FST lexical desta ADR, mas foi adotado depois como oraculo externo bloqueado em `internal/dedupeexternaloracle`, comparando Hamming distance contra o dedupe interno sem substituir a assinatura juridica propria.
- LSH/MinHash adicional: rejeitado pelo mesmo motivo; a camada Bottom-K MinHash ja tem adapter e evidencia.
- ANN/HNSW adicional: rejeitado porque `internal/hnswcandidateindex` ja integra `github.com/coder/hnsw` para candidatos de similaridade vetorial bloqueados.
- Tantivy wrappers Go: rejeitados para esta frente por custo operacional de binding Rust/nativo e por duplicarem o papel de full-text search ja coberto por Bleve.
- FST com `github.com/blevesearch/vellum`: escolhido porque e Go puro, Apache-2.0, ja auditado no grafo SCA como dependencia indireta de Bleve, e oferece superficie diferente: membership, ordenacao lexicografica e prefix/range scan compacto para termos normalizados de titulo, H1, slug e intent.

## Decisao

Criar `internal/fstcontentindex` como adapter controlado para construir sidecar FST bloqueado a partir de `data/editorial/refined_public_prose.jsonl`, persistindo:

- `data/ops/fst_content_term_index.fst`
- `data/ops/fst_content_term_index_evidence.jsonl`

A evidencia deve manter `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `approval=false`, `public_path=""` e `index_policy=noindex`. O adapter pode declarar prontidao de 10k apenas se a camada fonte tiver no minimo 10.000 registros; 100k/1M continuam sem reivindicacao ate benchmark dedicado.

## Consequencias

O portal ganha um indice lexical compacto e bloqueado para probes de unicidade e prefixo sem substituir Bleve, HNSW ou MinHash. A liberacao publica continua dependente dos gates de release; esta ADR nao autoriza escrita em superficie publica.
