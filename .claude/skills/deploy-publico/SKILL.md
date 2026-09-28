---
name: deploy-publico
description: Use antes de publicar o acervo com tools/deploy-publico — decide --ressemear e purga conforme o que mudou.
---

# Deploy público

Uma decisão manda no resultado: **`--ressemear` ou não**. Errar re-data as ~11 mil
rotas e re-anuncia o acervo inteiro ao Googlebot, ou esconde do buscador conteúdo
que mudou de fato.

## A matriz

| Mudei | `--ressemear`? | Purga |
|---|---|---|
| texto editorial | **não** — a re-datação é verdadeira | a do deploy basta |
| markup, CSS, atributo servido (`target`, `aria-label`, classe) | **sim**, e `--desde-commit` fica proibido nessa passada | a do deploy basta (o IndexNow fica calado: o lastmod não avança) |
| script inline | **não** — já é neutralizado no hash, não re-data | **ampla manual**, obrigatória |
| malha de links / bloco de relacionados | **não** — usá-lo suprimiria re-datação legítima do JSON-LD | **ampla manual**, obrigatória |

`tools/generate-page-content-revision` hasheia o HTML **depois de neutralizar** os
blocos de script sem atributo e `<section aria-labelledby="conteudos-relacionados">`.
É daí que a matriz sai.

## Antes

1. `git status` — worktree compartilhada: o deploy compila `./cmd/...` **do
   worktree**, então arquivo em edição de outra frente entra no binário.
2. `./tools/check-csp-style-hashes` — ele roda na suíte, **não** no caminho do
   deploy. Se a URL da folha no nginx não bater byte a byte com
   `render.StylesheetPath()`, nenhuma página tem estilo.
3. `./tools/check-load-headroom --max 12` e `tools/check-coord-status`.

## Depois

- O deploy detecta mudança de camada sozinho. Quando imprimir `purgando tudo`,
  **não purgue de novo** — mas leia o MOTIVO impresso: *"registro de revisao
  indisponivel"* já foi mentira (era `--purge-targets` caindo no teto de churn
  com exit 1).
- Purga ampla manual ⇒ em seguida `./tools/warm-edge-cache --rps 12`. O timer só
  passa às 04:20 e 16:20 UTC.
- `data/ops/edge_cache_purge.jsonl` antes de qualquer purga à mão: se o deploy já
  gravou `scope: "tudo"`, purgar de novo joga fora ~870 s de aquecimento.
- Borda fria depois da purga é **esperado**, não defeito.
- O `lastmod` entra no sitemap no ciclo **seguinte**, por desenho.

Recusa no passo 7 **não desfaz a publicação** — o acervo já está no ar.

Borda: skill `purgar-e-aquecer-borda`. Binário Go: skill `deploy-binario-go`.
