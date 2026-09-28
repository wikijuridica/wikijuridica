# ADR: Roaring bitmap no scale index bloqueado

Data: 2026-06-22

## Decisão

Adotar `github.com/RoaringBitmap/roaring/v2 v2.14.5` como dependência runtime Go direta, restrita a `internal/scaleindex/`, para calcular cardinalidade de shards alterados e evidência de escala em índices derivados.

## Escopo Permitido

- uso interno e bloqueado em índices de escala derivados;
- evidência em `data/ops/scale_index_benchmark_evidence.jsonl`;
- nenhum acesso a `public/`, `content/pages.json`, `published_manifest`, sitemap real ou `.release-staging`;
- nenhuma aprovação editorial, renderização, sitemap ou publicação.

## Justificativa

O ciclo P0 precisa preparar 10k agora e 100k/1M depois sem varrer conjuntos por O(n^2) quando bastar representar IDs de shards alterados. Roaring já existia como transitive de Bleve e passa a ser usado diretamente em adapter controlado, com versão fixa, licença Apache-2.0 e validação por benchmark/check de escala.

## Riscos E Controles

Risco principal: uso fora do adapter virar dependência silenciosa em fluxo público ou gate editorial. O controle é o gate `codex2-policy-enforcement`, que bloqueia imports fora de `internal/scaleindex/`, exige versão exata, ADR, evidência sem flags públicas e mantém `publication_allowed=false`.

## Validação

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/scaleindex ./internal/contract -run 'TestScaleIndex|TestCodex2PolicyEnforcement'`
- `./tools/check-scale-index-benchmark`
- `./tools/check-codex2-policy-enforcement`
