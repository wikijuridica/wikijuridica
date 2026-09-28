# ADR: uax29 para segmentacao PT-BR juridica bloqueada

Data: 2026-06-24

## Decisao

Adotar `github.com/clipperhouse/uax29/v2` em `v2.7.0` somente atras do adapter interno `internal/ptbrtext`, para segmentacao Unicode de palavras e frases usadas por qualidade textual, anti-template, dedupe e analise PT-BR juridica bloqueada.

## Escopo permitido

- `go.mod` e `go.sum`, somente na versao fixa `v2.7.0`.
- `internal/ptbrtext/`, como unico pacote autorizado a importar `github.com/clipperhouse/uax29/v2`.
- `internal/quality/`, consumindo apenas a API interna `internal/ptbrtext`.
- `data/ops/ptbr_text_segmentation_evidence.jsonl`, como evidencia bloqueada sem publicacao.

## Racional tecnico

O projeto precisa analisar 10k conteudos e crescer para 100k/1M URLs sem depender de tokenizacao fragil por regex simples. A implementacao UAX #29 reduz falso positivo/falso negativo em palavras com acento, hifen, barra, numero juridico e abreviacoes comuns, mantendo o custo de analise no Go e sem alterar HTML publico.

## Gates

- Import direto fora de `internal/ptbrtext/` deve falhar em `codex2-policy-enforcement`.
- Evidencia deve manter `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false` e `public_path=""`.
- A dependencia nao aprova conteudo, nao abre `published_manifest`, nao renderiza pagina e nao insere URL em sitemap.

## Licenca e risco

Licenca MIT verificada no modulo Go local. Risco de supply chain e baixo a medio: dependencia pequena, versao fixa, escopo de import restrito e uso interno bloqueado. Qualquer upgrade exige nova evidencia, ajuste de politica e teste.
