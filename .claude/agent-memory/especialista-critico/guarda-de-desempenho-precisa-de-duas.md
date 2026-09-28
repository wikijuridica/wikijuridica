---
name: guarda-de-desempenho-precisa-de-duas
description: Guarda de paralelismo exige DUAS asserções — igualdade de resultado e concorrência observada; a de igualdade fica verde quando a correção é apagada
metadata:
  type: feedback
---

Ao paralelizar uma fase para consertar lentidão, escreva **duas** guardas, e
nunca um cronômetro: (1) igualdade de resultado entre o caminho sequencial e o
paralelo, e (2) **concorrência máxima OBSERVADA** na fase, exposta pelo próprio
código de produção como instrumento.

**Why:** medido em 2026-09-16 no `internal/v2ingest`. Ao paralelizar a fase por
página do validador, a prova por mutação mostrou que as duas asserções cobrem
mutantes **disjuntos**:

- mutante `trabalhadores := min(1, runtime.GOMAXPROCS(0))` (apaga a correção):
  o teste de igualdade **PASSOU** — ele compara sequencial contra paralelo, e o
  mutante torna os dois idênticos, então a igualdade é trivialmente verdadeira.
  Só a asserção de concorrência morreu: *"DIMENSIONADA com 1 trabalhador(es)
  tendo GOMAXPROCS=8"*.
- mutante que faz o `reset()` do memo limpar só a faixa 0: as duas guardas
  acima passam, e só um teste específico do anel morre.

Guarda por parede é **falso vermelho garantido**: nesta mesma sessão o load
oscilou entre 5,9 e 11,5, e limite em milissegundos reprovaria por vizinho
ocupado — o tipo de teste que alguém apaga na segunda vez que vê vermelho.
Concorrência observada é fato estrutural: verdadeira sob qualquer carga, desde
que N seja grande o bastante para haver sobreposição.

Corolário sobre CACHE compartilhado: anel de memoização dimensionado para uma
goroutine (poucos slots, um mutex) **destrói o ganho** do paralelismo por
atropelo de capacidade, não por contenção. As páginas simultâneas expulsam a
decomposição uma da outra, a taxa de acerto desaba e o custo volta. Sharding por
faixa (chave barata, posicional, com a identidade ainda confirmada pela chave
integral) resolve sem mexer em assinatura.

**How to apply:** vale para qualquer fase que se torne paralela neste repo.
Antes de declarar a correção pronta, mute a própria correção e confira que a
guarda de concorrência fica vermelha; se só a igualdade existir, a guarda é
decorativa. Ver [[mutante-de-fiacao-precisa-compilar]] — o mutante de
paralelismo também precisa compilar: trocar só a atribuição deixa `runtime`
importado e não usado, e o vermelho é de build, não da guarda.
