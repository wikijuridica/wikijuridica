# ADR: go-readability HTML oracle bloqueado

Data: 2026-06-25

## Decisão

Adotar `codeberg.org/readeck/go-readability/v2@v2.1.2` somente por meio de `internal/htmlreadability` para avaliar HTML local já gerado ou ensaiado em memória. A integração usa `FromReader`; `FromURL`, fetch de rede, scraping, cópia de texto externo, aprovação pública, render, sitemap e publicação continuam bloqueados. O adapter agora também sustenta o check `html-readability`, com evidência em `data/ops/htmlreadability_evidence.jsonl`.

## Motivo

A fábrica P0 precisa de um oracle OSS para medir se páginas HTML leves preservam conteúdo principal útil para humanos, Googlebot e bots de busca/IA, sem confundir navegação/rodapé com corpo editorial. O gate valida `public/**/*.html`, registra extração, palavras em `<main>`, razão extraído/main, consistência title/H1, orçamento de HTML/estilo inline e vazamento de nav/footer como evidência bloqueada. Páginas jurídicas indexáveis futuras continuam com regra estrita de vazamento; shells institucionais/noindex têm tolerância limitada para rodapé institucional.

## Limites

- Uso permitido: `internal/htmlreadability/`.
- Entrada permitida: HTML local em `io.Reader`.
- Saída permitida: evidência de bloqueio/qualidade, nunca aprovação pública isolada.
- Check read-only: `tools/check-html-readability`, via `cmd/check html-readability`.
- Gerador de evidência: `tools/generate-html-readability-evidence`.
- Proibido: `FromURL`, `net/http` runtime no adapter, download de página externa, `publication_allowed=true`, `render_allowed=true`, `sitemap_allowed=true`, `public_path` e `approval=true`.

## Validação

- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/go-modern test -count=1 ./internal/htmlreadability`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/check-html-readability`
- `GOCACHE=/tmp/opt-wiki-go-cache ./tools/check-codex2-policy-enforcement --timings`
