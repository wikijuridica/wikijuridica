# ADR: Go x/text para normalizacao PT-BR bloqueada

Data: 2026-06-24

## Status

Adotado para uso interno bloqueado, sem autorizacao de publicacao.

## Decisao

Integrar `golang.org/x/text v0.38.0` como dependencia Go aprovada para normalizacao local de caixa em portugues brasileiro no pacote `internal/refinedpublicprose/` e normalizacao Unicode em `internal/ptbrtext/`.

O uso permitido fica limitado a `golang.org/x/text/cases`, `golang.org/x/text/language` e `golang.org/x/text/unicode/norm` para transformar fragmentos derivados de slugs, IDs e campos auxiliares em texto visivel com caixa natural antes da geracao de `data/editorial/refined_public_prose.jsonl`, alem de manter tokenizacao e comparacao PT-BR em forma Unicode estavel nos gates de qualidade.

## Motivo

O ciclo 399 encontrou conteudo visivel com sinais artificiais em H1, meta e corpo, incluindo capitalizacao de slug, residuos sem acento e expressoes mecanicas. A biblioteca padrao resolve parte do problema, mas nao fornece mapeamento de caixa com locale PT-BR. `golang.org/x/text` e modulo oficial complementar do Go, documentado em `pkg.go.dev`, com licenca BSD-3-Clause e comportamento deterministico local.

## Escopo Permitido

- `go.mod`
- `go.sum`
- `internal/refinedpublicprose/`
- `internal/ptbrtext/`
- `data/ops/check_performance_ledger.jsonl`

## Escopo Proibido

Esta dependencia nao pode abrir `public/`, `content/pages.json`, `data/editorial/published_manifest.jsonl`, sitemap real, robots publico, canonical publico, `approval=true`, `publication_allowed=true`, `render_allowed=true`, `sitemap_allowed=true` ou qualquer `public_path`.

Tambem nao pode substituir fonte oficial juridica, revisao juridico-editorial, anti-spam, anti-duplicidade, leitura humana/Codex dos conteudos visiveis ou o gate `p0-cycle-close-indexable-10k`.

## Validacao Obrigatoria

```bash
GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/refinedpublicprose
GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/ptbrtext ./internal/quality
GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/contract -run 'TestCodex2PolicyEnforcement'
GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern run ./cmd/check codex2-policy-enforcement --timings
```

## Evidencia

- Modulo: `golang.org/x/text v0.38.0`
- Documentacao: `https://pkg.go.dev/golang.org/x/text`
- Pacote usado: `https://pkg.go.dev/golang.org/x/text/cases`
- Pacote usado: `https://pkg.go.dev/golang.org/x/text/unicode/norm`
- Repositorio: `https://github.com/golang/text`
- Evidencia de performance/politica: `data/ops/check_performance_ledger.jsonl`
