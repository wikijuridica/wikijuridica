---
name: regua-do-jsonl-nao-e-a-regua-do-html
description: Limiar calibrado no HTML servido aplicado ao corpo do JSONL produz falso positivo em massa — offset medido em 1.213 pares
metadata:
  type: project
---

Limiar calibrado sobre `public/**/index.html` **não** se aplica cru ao corpo do
JSONL (`data/editorial/v2_pages`). A página renderizada carrega camada autoral
que o JSONL não tem (proveniência, aviso legal, moldura editorial).

**Why:** ao estender `check-derived-authorial-floor` para medir o estoque antes
da publicação (2026-09-16), a primeira versão acusou 132 páginas — **123 delas
já publicadas e aprovadas pelo eixo em HTML**. Era o defeito de duas réguas que
o próprio gate existe para acusar.

**Offset medido** sobre 1.213 pares (mesma página no JSONL e no HTML servido),
seis famílias derivadas:

    proporcao citada   JSONL − HTML : min +0,0041 · mediana +0,0358 · max +0,0726
    palavras autorais  HTML − JSONL : min   +59   · mediana   +75   · max   +125

**How to apply:** ao medir estoque com limiar de página publicada, mova o limiar
pela ponta do offset que evita acusar quem a página publicada aprova (piso −59,
teto +0,0726) e declare uma **banda de incerteza** para o meio, que nomeia sem
reprovar. Refazer a medição do offset se o render mudar de moldura.

Relacionado: [[cadeia-de-pagina-tem-dois-trilhos]].
