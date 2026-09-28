# ADR: gofeed para feeds públicos bloqueados de demanda

Data: 2026-06-24

## Decisão

Adotar `github.com/mmcdole/gofeed v1.3.0` como parser interno de RSS, Atom e JSON Feed em `internal/demandobservations`.

## Escopo permitido

- Parser chamado somente com `Parse(bytes.NewReader(body))`.
- Proibido usar `ParseURL` ou o cliente HTTP do parser.
- O download continua sendo feito pelo coletor existente, com limite de bytes, headers, cache, rate/concurrency e diagnóstico próprios.
- Amostras seguem bloqueadas para pesquisa, reescrita autoral e revisão; não abrem `publication_allowed`, `render_allowed`, `sitemap_allowed`, `public_path`, `content/pages.json`, `published_manifest` ou `public/`.

## Motivo

O parser manual RSS/Atom deixava a superfície textual de demanda frágil e não cobria JSON Feed. `gofeed` reduz esse gargalo sem transformar feed público em crawler, scraping de página vinculada ou fonte de texto publicável.

## Gates

- Rejeitar descrição/conteúdo que só repete título, autor ou link.
- Preservar PT-BR, alinhamento com oportunidade e limite de amostra.
- Manter fonte oficial digest-only quando a política oficial se aplicar.
- Import permitido apenas em `internal/demandobservations/`.
