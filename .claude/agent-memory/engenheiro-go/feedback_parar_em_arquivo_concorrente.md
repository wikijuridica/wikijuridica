---
name: feedback-parar-em-arquivo-concorrente
description: Quando o arquivo-alvo está sendo reescrito por outra frente agora, PARE e devolva o patch ao maestro em vez de editar
metadata:
  type: feedback
---

Antes de editar qualquer arquivo, rode `git diff -U0 <arquivo> | grep '^@@'` e confira o
mtime. Se houver hunk da outra frente **dentro da função que você precisa mudar**, e o
arquivo tiver sido escrito nos últimos minutos, **não edite**: devolva ao maestro o patch
ancorado em texto atual (com número de linha só como referência de leitura), diga qual
função conflita e por quê.

**Why:** o maestro dá essa ordem explicitamente ("se o conflito for grande, PARE e me
avise — eu coordeno"), e o risco não é conflito de merge — é *lost update*: o editor da
outra frente escreve de um buffer antigo e a sua mudança some **em silêncio**. O maestro
então acredita que o defeito foi corrigido quando não foi. Em frente cujo objeto é
justamente "código que não roda não aparece em incidente", esse falso verde é o pior
desfecho possível. Em 2026-09-16 foi o caso de `cmd/generate-acordao-pages/main.go`: a
outra frente reescrevia `roda()` (+22 linhas) exatamente onde a correção do teto de lote
teria de entrar.

**How to apply:** vale só quando o hunk alheio cai na **mesma função/região**. Hunk noutra
parte do arquivo ⇒ edição pontual ancorada em texto único é segura. E parar num arquivo
não é parar na frente: entregue tudo o mais, e nomeie explicitamente o que ficou de fora,
para que o maestro não leia "gate verde" como "família fechada". Ver
[[project-p3-produtores-orfaos]].
