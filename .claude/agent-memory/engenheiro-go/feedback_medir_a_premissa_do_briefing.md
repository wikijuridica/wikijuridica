---
name: medir-a-premissa-do-briefing
description: Antes de construir o mecanismo que o maestro pediu, meça a premissa dele na fonte — briefing com número ou atribuição de causa já veio errado e o mecanismo teria silenciado verdadeiro positivo
metadata:
  type: feedback
---

O briefing do maestro traz premissa **e** solução. Meça a premissa na fonte primária antes de
construir a solução; se a premissa cair, devolva a medição em vez do mecanismo.

**Why:** em 2026-09-16 o maestro pediu um mecanismo de "declaração de reinício" porque
`check-cerebro-vivo` teria ficado vermelho por **deploys deliberados** que o gate não distingue de
laço de crash. O journal refutou: o gate casa
`Scheduled restart job, restart counter is at N`, linha que **só** o caminho `Restart=always`
produz — o `systemctl restart` do deploy sai como `Stopping…` → `Deactivated successfully.` →
`Started`, **invisível ao gate**. Os três restarts contados eram três crashes com
`database is locked (517)`. O mecanismo pedido teria silenciado três verdadeiros positivos, com a
autoridade de uma peça nova. O mesmo padrão apareceu no §P10: o plano dizia "4 checks órfãos" (eram
2), "19 pontos sem teto" (eram 22) e "hoje passaria verde" (frase, não medição — medi e passava, mas
o número é meu, não do plano).

**How to apply:** vale quando o briefing carrega (a) contagem, (b) atribuição de causa, ou (c) a
frase "hoje passaria verde". Custo típico de conferir: um `journalctl`, um `wc -l`, um script de
medição sobre snapshot datado. Devolva os dois números — o do briefing e o medido — e o comando que
os separa; o maestro corrige o plano (regra 23, "o plano não mente"). Não é insubordinação: é o que
`ESTADO.md` chama de evidência, e relato sem evidência não fecha item. Ver
[[medir-com-a-regua-do-pacote]] para o caso em que a régua é código, e
[[parar-em-arquivo-concorrente]] para quando a medição encontra outra frente no mesmo arquivo.
