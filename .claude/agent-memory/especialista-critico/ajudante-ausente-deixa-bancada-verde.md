---
name: ajudante-ausente-deixa-bancada-verde
description: Em bancada shell, chamar ajudante inexistente imprime "comando não encontrado" e a bancada termina ok — abra com laço que exige cada ajudante declarado
metadata:
  type: feedback
---

Toda bancada `.sh` nova começa com um laço que confere, por `declare -F`, que **cada** ajudante
usado existe, e sai 1 nomeando o que falta.

**Why:** usei `confere` sem tê-lo definido (ele vive na bancada irmã). Sete asserções imprimiram
"comando não encontrado", o `$?` delas nunca foi lido, e a bancada terminou dizendo **ok**. Uma
bancada que passa sem medir é pior que bancada ausente: ela autoriza a próxima sessão a confiar.

**How to apply:** o laço vai antes da primeira asserção. Vale também para função extraída por
âncora de outro arquivo (`sed -n '/^func()/,/^}/p'` + `eval`): se a âncora mudar de nome, a
extração vem vazia e o `eval` não define nada — confira o resultado da extração com a mesma
régua. E prove a bancada por mutação: mutante que sobrevive denuncia a fixture, não o predicado,
e fixture com DOIS marcadores da mesma classe mantém o mutante vivo — isole um por caso.
Relacionado: [[bancada-nao-escreve-em-producao]].
