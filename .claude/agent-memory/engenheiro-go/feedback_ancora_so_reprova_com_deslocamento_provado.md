---
name: ancora-so-reprova-com-deslocamento-provado
description: guarda de referencia arquivo:linha so pode reprovar quando o token citado existe em OUTRA linha do alvo; caso contrario vira ruido e alguem desliga
metadata:
  type: feedback
---

Guarda que confere comentario `arquivo:linha` tem tres desfechos, nao dois:
**passa** (o identificador citado esta na janela do alvo), **reprova** (o
identificador esta comprovadamente em outra linha — deslocamento provado, e a
mensagem diz para onde foi) e **nota** (a frase nao nomeia nada que exista no
alvo: nao da para julgar, so se confere existencia de arquivo e de linha).

**Why:** a versao de dois desfechos reprova ancora correta cuja frase nomeia
conceito em vez de identificador (`ICP-Brasil` apontando para a linha que faz
`por usr-local-share-ca-certificates`). Guarda que reprova o que esta certo vira
ruido, e ruido alguem desliga — perdendo tambem as reprovacoes verdadeiras.
Medido em 2026-09-22 no kit de `ops/provisionamento/`: 30 ancoras, 8 podres, e a
versao de dois desfechos reprovava 3 ancoras corretas — duas de `pacotes.txt`
(salvas depois pela camada de palavra lisa, `tmux`) e a da cadeia ICP-Brasil,
que so o terceiro desfecho resolve.

**How to apply:** vale para qualquer detector sobre texto humano (ancora,
citacao, indice, TODO com dono). Antes de reprovar, exija a prova positiva de
que o alvo existe noutro lugar; sem ela, classifique como "nao verificavel" e
conte no rodape. E escreva no comentario o que a guarda NAO pega — folga de
linhas, referencia em prosa ("linha 38"), alvo fora do repositorio.
Relacionado: [[sed-imprime-em-ordem-de-arquivo]], [[mutante-vivo-terceiro-desfecho]].
