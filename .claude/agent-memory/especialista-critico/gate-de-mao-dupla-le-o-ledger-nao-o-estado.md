---
name: gate-de-mao-dupla-le-o-ledger-nao-o-estado
description: Ao fechar um gate no sentido inverso, a fonte decide se ele mede ou mente; estado que so grava o que tem artefato local e verde por construcao
metadata:
  type: feedback
---

Fechar um detector "nos dois sentidos" nao e escrever a segunda comparacao: e
escolher, para o sentido novo, uma fonte que possa CONTER o defeito. Fonte que
nao registra a classe procurada devolve zero e o gate fica verde para sempre —
falso-verde pior que a ausencia do gate, porque afirma o que nao mediu.

**O caso medido (2026-09-16).** `tools/check-indexnow-backlog` conferia
sitemap → recibo e imprimia "OK: toda URL no ar tem recibo", enquanto 1.968
URLs FORA do sitemap eram anunciadas (2.422 eventos, 17,4% do total). A fonte
obvia para o sentido inverso seria `data/ops/indexnow_submission_state.json`.
Ela tem ZERO `.md` por CONSTRUCAO: quem escreve
(`generate-indexnow-direct-submit.registrar_no_estado_compartilhado`) so grava
URL para a qual conseguiu hashear `public/<rota>/index.html`, e para
`/x/index.md` esse caminho e `public/x/index.md/index.html`, que nao existe. A
gemea era POSTada de verdade e sumia do estado, calada.

A fonte certa era `data/ops/indexnow_url_state.jsonl` — o ledger por URL, uma
linha por URL por lote REALMENTE POSTado, escrito no unico ponto por onde os
dois submissores passam. Evidencia do que foi ao fio, nao do que se pretendeu.

**Why:** a assimetria "submete mas nao registra" e o que esconde o defeito, e
ela some quando o skip e silencioso. O conserto tem duas metades: o gate le o
ledger, E o produtor IMPRIME quando POSTa sem registrar ("N de M nao entraram
no estado compartilhado").

**How to apply:**
- Antes de escolher a fonte do sentido novo, pergunte: **esta fonte registraria
  o defeito que procuro?** Se o produtor dela filtra por um artefato local,
  provavelmente nao.
- O mutante que prova o gate e a TROCA DE FONTE (ledger → estado). Se ele
  sobrevive, o gate nao mede nada. Aqui ele matou 4 testes.
- Ponha o detector novo ANTES do `return 0` do sentido antigo. O caminho feliz
  do gate era justamente o early-return "toda URL no ar tem recibo" — detector
  depois dele nunca executaria.
- Reprove por FLUXO (janela de dias), nao por estoque: 2.422 eventos historicos
  como reprovacao deixariam o gate vermelho para sempre sem nada que o drene.
- Ao rebindar `ROOT` numa fixture, rebinde TODA constante derivada dele. A
  fixture leu o arquivo real de producao e tres testes ficaram vermelhos.
- Duble incompleto falha fingindo outro defeito: `_RespostaFalsa` sem `headers`
  virou `AttributeError` → `except Exception` → `status = 0` → "lote recusado"
  numa submissao que o duble mandara aceitar.

Ver [[lista-de-purga-nao-e-lista-de-anuncio]] — o defeito que este gate deixou
passar.
