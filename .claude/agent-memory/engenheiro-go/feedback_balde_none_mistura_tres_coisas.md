---
name: balde-none-mistura-tres-coisas
description: Antes de tratar "X% sem chave/sem classificação" como lacuna, particione o balde nulo — ele mistura o que não deve ter chave com o que deveria
metadata:
  type: feedback
---

Classificador que devolve `None`/`null`/`desconhecido` NÃO produz um número de
lacuna. Antes de publicar "X% sem chave", parta o balde nulo em: (a) o que por
desenho não tem chave, (b) o que não pode ter (não se declara), (c) o que
deveria ter e não tem. Só (c) é a lacuna, e só (c) tem conserto.

**Why:** em 2026-09-16, na frente B9, o briefing mandava fechar "30,7% do
tráfego sem `agent_key`". Medido na borda, "sem `agent_key`" eram 17.251 de
30.115 requisições líquidas (57,3%) — mas 3.210 eram navegadores humanos (não
têm chave por desenho, e está certo) e 1.300 eram clientes genéricos (`node`,
`curl`, `undici`: dizem COMO a requisição foi feita, nunca QUEM). A lacuna real
eram 12.741 (42,3%) de agente que se declara com nome próprio. Consertar "os
57,3%" seria construir contra um número que não mede a coisa que se quer
consertar — e um balde chamado `Mozilla`, que o produtor criava, virava uma
linha de registro com um `user_agent_sample` sorteado entre milhares: rótulo
com autoridade sobre coisa nenhuma.

**How to apply:** vale para qualquer eixo com valor nulo — `agent_key`,
`intent_id`, `route_class`, `nivelSigilo`, `agent_key` em `por_agente`. O teste
é perguntar, para cada membro do balde nulo, "qual seria o valor certo?". Se a
resposta honesta for "nenhum", ele não é dívida. Publique a partição inteira com
os literais, nunca o agregado — e meça o efeito do conserto no balde (c), não no
total. Relaciona-se com [[feedback_medir_a_premissa_do_briefing]]: o número do
briefing pode estar certo e ainda assim medir outra coisa.
