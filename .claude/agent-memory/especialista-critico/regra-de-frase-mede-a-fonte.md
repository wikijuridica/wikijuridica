---
name: regra-de-frase-mede-a-fonte
description: Antes de culpar a moldura do gerador por duplicate_phrase, separe a camada citada da autoral — em canal derivado de fonte oficial o teto é do texto do tribunal, não da nossa prosa
metadata:
  type: feedback
---

Em canal derivado de fonte oficial, antes de aceitar que "o gerador repete moldura",
meça a colisão **por camada da DEC-032**: janela inteiramente dentro das aspas curvas
(texto oficial, que não podemos variar) contra janela autoral (nossa prosa, que
podemos).

**Why:** medido em 2026-09-16 no `cmd/generate-acordao-pages`. O oráculo do ingest
acusava `duplicate_phrase_with_page` em 29 de 30 páginas e o diagnóstico corrente
culpava quatro frases do gerador. A classificação por camada mostrou outra coisa: a
moldura autoral é o gargalo **de hoje** (58 de 58 colisões), mas mesmo com a camada
autoral perfeitamente única só **5 de 60** páginas entrariam no estoque — e **1 de 12**
num lote de mesmo órgão/data/relator —, porque o dispositivo do STJ é fórmula
("acordam os Ministros da <órgão> ... em Sessão Virtual de <data>, por unanimidade")
idêntica entre todos os acórdãos do colegiado. Sem a separação, gasta-se a frente
reescrevendo prosa para um teto que não é dela.

**How to apply:** regra absoluta de frase (N-grama exato, "uma janela mata") aplicada a
corpo que mistura citação literal + disclaimer + comentário próprio é medida da grandeza
errada. Antes de editar o produtor: (1) classifique a colisão por camada, (2) simule o
teto guloso usando SÓ o resíduo citado — é o número que decide se vale mexer na prosa,
(3) só então decida. E desconfie do reflexo de enfiar identificador no meio da frase
para quebrar a corrida: duas frentes anteriores registraram no próprio código que isso é
otimizar contra o detector, não consertar o molde. Ver [[oraculo-antes-de-refinar]] e
[[detector-conta-em-vez-de-comparar-conjunto]].
