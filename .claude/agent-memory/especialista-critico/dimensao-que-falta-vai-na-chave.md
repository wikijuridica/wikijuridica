---
name: dimensao-que-falta-vai-na-chave
description: Quando dois processos independentes compartilham um cursor, acrescentar campo de conferência não fecha o buraco — a dimensão tem de entrar na CHAVE
metadata:
  type: feedback
---

Quando dois consumidores independentes compartilham uma estrutura indexada por
uma chave que **não** os distingue, a correção é pôr a dimensão que falta **na
chave** — não acrescentar um campo e conferir antes de usar.

**Why:** 2026-09-16, `internal/djen/retomada.go`. O cursor de retomada da coleta
do DJEN era indexado por `(tribunal, dia)`, e os regimes `monitor` e `acervo`
guardam **coisas diferentes** do mesmo dia, logo têm coberturas independentes.
Uma coleta de acervo parou na página 41 e gravou o ponto; a unit diária, em
monitor, ia consumir esse ponto (deixando 1..40 sem leitura no regime dela) e
apagá-lo ao chegar à página vazia.

A instrução que recebi era "acrescente `Regime` ao ponto e recuse ponto de regime
diferente no consumo". Li o código antes de aplicar e **três** caminhos furavam
isso, não um: `Ponto` (consumo), `Conclui` (apagamento) e — o que a instrução não
previa — `Marca`, que fazia `r.Pontos[chave] = ponto` **incondicional**: um
monitor que não terminasse sobrescreveria o ponto do acervo. Campo + conferência
não estreitava o buraco, só mudava o nome dele; e a própria instrução pedia que
os dois pontos coexistissem em `Pendentes()`, o que **exige** chaves distintas.

Com a dimensão na chave, os três caminhos ficam certos **por construção** e não
existe "lembrar de conferir".

**How to apply:**
- o sintoma é "X consumiu/apagou o estado de Y". Antes de escrever a conferência,
  **enumere todos os pontos que escrevem, leem e apagam** aquela estrutura. Se
  forem mais de um, conferência é remendo;
- teste a coexistência, não só a recusa: dois estados vivos ao mesmo tempo para a
  mesma chave antiga;
- mutante que importa é **a dimensão saindo da chave** e a dimensão chegando
  vazia **em cada call site** — em `tools/prova-mutacao-djen-retomada` foram 7;
- **não suba a versão do arquivo persistido** se o registro antigo desserializa:
  `CarregaRetomada` recusa versão diferente, e o bump travaria a execução
  seguinte com "é da versão 1". Reindexe na carga em vez disso;
- registro antigo sem a dimensão é **desconhecido**, não "provavelmente o meu":
  promovê-lo por suposição faz pular trabalho que ninguém fez (perda silenciosa e
  permanente); recomeçar custa releitura que a mesclagem deduplica. Escreva a
  régua **antes** de olhar quantos existem.

Divergir da instrução exigiu evidência primária (`armazem.go:146`, `:163`) e uma
volta ao `advisor` para reconciliar — não troquei de rota em silêncio. Ver
[[fixture-que-nao-alcanca-a-guarda]] e [[mutante-de-fiacao-precisa-compilar]].
