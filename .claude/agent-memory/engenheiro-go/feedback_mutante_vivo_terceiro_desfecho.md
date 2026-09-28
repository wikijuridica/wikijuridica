---
name: mutante-vivo-terceiro-desfecho
description: Mutante que sobrevive tem TRÊS desfechos, não dois — o terceiro é guarda contra regressão futura, e se prova com outro mutante
metadata:
  type: feedback
---

Quando um mutante sobrevive, existe um terceiro desfecho além de "fixture fraca"
e "predicado errado": **a guarda é real mas hoje inobservável, e o que está
errado é o alcance do comentário.** Nesse caso não se apaga a guarda nem se
mente sobre ela — escreve-se qual regressão ela trava e **prova-se com o mutante
DESSA regressão**.

**Why:** em 2026-09-16, em `internal/v2ingest/admissibilidade.go`, a cópia
defensiva do slice de razões (`append([]string(nil), verdict.Reasons...)`)
sobreviveu ao mutante que a removia — `validateBatch` reconstrói vereditos a
cada chamada, então nada de fora alcança memória compartilhada e a cópia é
semanticamente inerte hoje. Apagar o teste teria removido a única trava contra a
memoização do oráculo, que é a "otimização" óbvia para o produtor que consulta em
laço. Escrito o mutante certo — um cache de lote de três linhas devolvendo a
mesma memória a todos os chamadores —, o teste matou na hora. A guarda valia; o
comentário é que prometia proteção contra um cenário que não existe.

**How to apply:** ao ver mutante vivo sobre código defensivo, antes de decidir,
pergunte "que mudança FUTURA e plausível este código impede?". Se houver uma,
escreva-a como mutante e rode. Morreu: mantenha a guarda e reescreva o
comentário dizendo os dois fatos — que o mutante trivial sobrevive e qual
regressão o teste realmente mata. Não morreu nenhum mutante plausível: aí sim é
decoração, e sai. Vale para cópia defensiva, revalidação, clamp e reset de
estado. Complementa [[teste-e-aprendizado-sao-par]] e
[[comentario-de-teste-que-mente-sobre-cobertura]], que cobrem só os dois
primeiros desfechos.
