---
name: mascara-por-campo-nao-sobrevive-a-campo-novo
description: Guarda de sanitização que masca campos nomeados vaza no dia em que o tipo ganha um campo novo com a mesma carga; e anunciar o achado do detector como "removido" mente quando o detector só anota
metadata:
  type: feedback
---

Guarda que sanitiza **campo por campo** vaza no dia em que o tipo ganha um campo
novo com a mesma carga. A asserção tem de varrer a **saída inteira** com o
detector do próprio produtor, não a lista de campos que alguém lembrou.

**Why:** 2026-09-16, `internal/djenacervo`. `AtoDoRegistro` chamava
`pii.Mascarar(registro.Corpo)` e os testes conferiam "o corpo está mascarado".
Horas depois o mesmo tipo ganhou `Destinatarios[].Nome` (nome da parte vindo da
coluna estruturada). O nome é texto do diário, e o TJRJ escreve o identificador
DENTRO dele: medidas 61 das 52.252 linhas de destinatário do dia com CPF em
claro, 60 delas em atos publicáveis. Iria para a página pública **e para o índice
de busca** — nome é a chave da busca, então o CPF viraria termo indexado. Treze
mutantes da bancada continuavam morrendo; nenhum tocava o caminho novo. Quem
apanhou foi **medição no dado real**, não teste — e a fixture tinha `destinatarios: []`
em todos os 5 registros, então o caminho não era alcançável ([[fixture-que-nao-alcanca-a-guarda]]).

O segundo defeito do mesmo commit é irmão: a página escrevia "Identificadores
retirados do texto: <lista>" copiando `achado.Tipo` cru. `pii.Mascarar` devolve
duas coisas com o mesmo nome de campo — o que **substituiu** (cpf, rg) e o que só
**anotou** (`nome_agente_publico`, que por ordem do dono fica no texto). Medidos
130 atos que anunciariam ter retirado um nome que continua lá: afirmação falsa em
canal público, e ainda sugerindo que a máquina apaga nome de parte.

**How to apply:**
- a guarda de família é um teste que monta o objeto público e varre **todas** as
  strings dele (inclusive `Partes[i].Nome`) com o detector exportado do produtor
  (`pii.IdentificadorExposto`). Campo novo entra na varredura no dia em que entra
  no tipo, sem ninguém lembrar;
- antes da asserção, **conte o material bruto** e falhe se for zero: "a amostra
  não tem um nome com identificador" é o que impede o teste virar decoração;
- para saber se o achado foi mesmo retirado, pergunte à **saída** (`o trecho
  ainda está no texto publicado?`), nunca a uma segunda lista de "tipos que são
  documento" — lista paralela diverge do detector, que é o defeito que
  `internal/pii` documenta no próprio cabeçalho;
- ao varrer o disco procurando a família, varra **todos** os campos string do
  registro, não o que você suspeita: aqui só `corpo` e `destinatarios[].nome`
  tinham identificador, e saber que órgão/classe/link estão limpos é o que
  delimita a correção;
- detector improvisado de "parece endereço" achou 4 nomes e **2 eram falso
  positivo** ("TV PLANICIE LTDA" casou com Travessa). Ruído de 0,004% não se
  filtra com regra nova sem teste de falso positivo: mede-se e declara-se.
