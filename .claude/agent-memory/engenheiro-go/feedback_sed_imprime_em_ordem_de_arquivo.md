---
name: sed-imprime-em-ordem-de-arquivo
description: sed -n 'Ap;Bp' imprime na ordem do ARQUIVO, nunca na dos argumentos; ler o par invertido vira achado falso
metadata:
  type: feedback
---

Conferir duas linhas com `sed -n '372p;334p' arquivo` devolve **334 antes de 372**:
o `sed` percorre o arquivo uma vez e imprime na ordem em que encontra. A saida
nao tem rotulo de linha, entao a leitura "primeiro que saiu = primeiro que pedi"
e silenciosamente invertida.

**Why:** em 2026-09-22 isso quase produziu um achado falso — li `334:rclone-browser`
como `372:rclone-browser` e conclui que duas ancoras de `consolidar-discos.sh`
estavam trocadas. Elas estavam **corretas**, e a guarda que eu estava desenhando
teria sido calibrada para reprova-las. Quem pegou foi o [[advisor]], nao um teste.

**How to apply:** para conferir linhas especificas use `grep -n` (que rotula) ou
`sed -n` com `=` / `awk 'NR==A||NR==B {print NR": "$0}'`. Sempre que a evidencia
for "linha N contem X", o rotulo da linha tem de estar na saida citada — sem
rotulo, nao e medicao, e uma suposicao sobre ordem.
Relacionado: [[ancora-so-reprova-com-deslocamento-provado]].
