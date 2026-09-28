---
name: referencia-matriz-fontes-noticias
description: Onde vivem a matriz de fontes de notícia oficial, o laudo da sondagem de candidatas e o que cada veredito significa
metadata:
  type: reference
---

A matriz de fontes do canal diário de notícias é **dado**, em
`/opt/wiki/content/noticias_oficiais_fontes.json`, lida e validada por
`/opt/wiki/internal/noticiasfontes`. Acrescentar tribunal é editar o JSON, não o Go.

O laudo das candidatas fica em
`/opt/wiki/data/research/daily/noticias-oficiais/_sondagem-AAAA-MM-DD.json`, produzido por
`./cmd/collect-noticias-oficiais -sondar`. O prefixo `_` e a extensão `.json` (nunca `.jsonl`)
são deliberados: os três leitores daquele diretório filtram por `*.jsonl`, e laudo visível para
`cmd/generate-noticia-pages` viraria página.

Vereditos, e nenhum é o status HTTP: `SERVE` (feed com item e janela recente), `OBSOLETO` (200,
RSS válido, arquivo), `ATOM`/`RDF` (envelope que o parser não lê — trava nossa), `RECUSADA`
(robots.txt nega), `ERRO`, `VAZIO`.

Os logs por onda de sondagem ficam em `/opt/wiki/.agents/runtime/sondagem-noticias-*.log`; o
laudo em `data/` é sobrescrito por data, então é neles que está o histórico das ondas do dia.

Ver [[coleta-noticias-fronteira-do-feed]].
