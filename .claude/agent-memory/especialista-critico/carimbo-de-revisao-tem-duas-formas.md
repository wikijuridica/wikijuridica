---
name: carimbo-de-revisao-tem-duas-formas
description: content.Page.LastModified() devolve data pura OU instante RFC3339-Z; consumidor que parseia sozinho quebra só no subconjunto com instante
metadata:
  type: project
---

`content.Page.LastModified()` tem DUAS formas legítimas por contrato
(`content.ValidRevisionStamp`): `2026-08-26` e `2026-09-16T15:52:35Z`. Quem
precisa do DIA usa `content.RevisionDay`; quem precisa do instante usa
`content.RevisionTime`. Parser próprio no pacote consumidor quebra só na minoria
com instante — falha silenciosa, sem erro e sem gate.

**Why:** medido em 2026-09-16. `internal/pagemarkdown.dateParts` partia a string
em `-`, então o instante virava três campos com `16T15:52:35Z` no meio e o
registro CSL-JSON saía SEM `issued`. As 85 rotas com carimbo instante eram
EXATAMENTE as 85 sem `issued` (conjunto idêntico, diferença zero nos dois
sentidos): um defeito, não dois. A mesma origem fazia a linha em prosa "Como
citar" imprimir `Wiki Jurídica. 2026-09-16T15:52:35Z.` numa referência
bibliográfica. `internal/sitemap` e `internal/structureddata` já usavam os
adaptadores sancionados — só `pagemarkdown` tinha parser próprio.

**How to apply:** ao medir "quantas rotas perderam o campo X derivado de data",
compare o CONJUNTO com o das rotas com carimbo instante antes de concluir que
são dois defeitos. E não "conserte" aceitando qualquer string: os controles do
teste (data fora de faixa, texto que não é data) têm de continuar sem o campo —
citação sem data é incompleta, com data errada é falsa. O front matter mantém o
instante íntegro em `date_modified`, que alimenta `<lastmod>`/`Last-Modified`:
rebaixar para dia ali destruiria a precisão do sinal de frescor.
