# ADR: go-edlib para distancia curta de superficies publicas

## Decisao

Adotar `github.com/hbollon/go-edlib v1.7.0` somente atras do adapter `internal/textdistance`, para comparar superficies publicas curtas (`title`, `meta description` e `h1`) e bloquear quase duplicatas em `public-prose-language-patterns`.

## Escopo

- Uso permitido: qualidade editorial bloqueada, dedupe de superficie curta e release blocker.
- Uso proibido: corpo completo em all-pairs, crawler, fonte juridica, render, sitemap, `public_path`, `published_manifest` ou aprovacao publica.
- Politica: import direto fora de `internal/textdistance/` deve falhar em `codex2-policy-enforcement`.

## Risco

`go-edlib` e MIT e nao traz dependencias diretas, mas distancia textual pode gerar falso positivo. A mitigacao e limitar a buckets pequenos, usar threshold alto, manter evidencia bloqueada e tratar o resultado como bloqueio de qualidade a revisar, nunca como aprovacao.
