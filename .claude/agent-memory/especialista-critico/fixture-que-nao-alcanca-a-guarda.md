---
name: fixture-que-nao-alcanca-a-guarda
description: Teste de rota fica falso-verde quando nenhum termo da consulta alcança um registro que precise da guarda — o mutante sobrevive compilando
metadata:
  type: feedback
---

Antes de declarar que um teste de rota prova a fiação de uma guarda, confira que
**o caminho exercitado alcança um registro que de fato aciona a guarda**. Se
nenhum termo consultado renderiza um registro que precise dela, o teste passa com
a guarda arrancada — e ele *compila*, então [[mutante-de-fiacao-precisa-compilar]]
não pega este caso.

**Why:** em 2026-09-16, `TestOCPFNaoSaiNaRota` (cmd/social, acervo do DJEN)
consultava três nomes e afirmava que nenhum CPF saía. O único registro da fixture
com CPF era de classe **AÇÃO PENAL**, que a busca por nome nunca alcança por
política (Res. CNJ 121/2010, art. 4º). Resultado: o teste passava com
`pii.Mascarar` removido da rota. O cabeçalho do arquivo dizia "esta bancada prova
a fiação" — e não provava. O conserto foi acrescentar à fixture uma **EXECUÇÃO
FISCAL** real (classe cível, alcançável por nome) que carrega CPF *e* rótulo de
polo; só então o mutante morreu.

**How to apply:** a prova tem duas metades, e a primeira é a que se esquece:
1. **asserção positiva de alcance** — o teste falha se a consulta *não* devolver
   o registro esperado ("a busca não alcançou o ato que carrega CPF; sem ele este
   teste não mede a máscara"). Sem ela, "CPF ausente" é ausência de resposta, não
   efeito da guarda;
2. **a guarda declara o que fez** — asserte o efeito visível (`"Identificadores
   retirados do texto"`), não só a ausência do dado. Ausência prova pouco;
   presença do efeito prova que o código rodou.

E rode o mutante **no pacote onde o teste mora**: um harness que só roda
`./internal/<pkg>/` nunca vê o teste de rota em `./cmd/<bin>/`. O instrumento em
`tools/prova-mutacao-djenacervo` carrega o pacote por mutante justamente por isso.

Vizinho por classe: [[fixture-que-e-o-alvo-do-trabalho]].
