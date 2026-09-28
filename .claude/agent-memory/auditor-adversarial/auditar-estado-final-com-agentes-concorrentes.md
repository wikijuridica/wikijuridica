---
name: auditar-estado-final-com-agentes-concorrentes
description: Em sessão com agentes concorrentes, re-rodar a bancada e re-derivar âncoras arquivo:linha no ESTADO FINAL do disco; relato "verde às HH:MM" envelhece em minutos
metadata:
  type: feedback
---

Re-rode a bancada e re-confira toda âncora `arquivo:linha` no estado atual do disco antes de dar veredito; o relato do worker ("13/13, 79 mutantes, às 08:56") é alegação sobre um instante que já passou.

**Why:** 2026-09-23, goal IDE: `tools/test_ide_workspace.py` lia o kit por `glob("extensoes*.txt")`; um agente concorrente (`kit-midia`) criou `ops/ide/extensoes-proibidas.txt` às 09:01 e a asserção 9 passou a reprovar (exit 1) — o worker tinha visto verde às 08:56. No mesmo goal, docs "conferidos às 08:46" citavam `LEIA-ME.txt:611-629`, `provisionar.sh:157` etc., e o kit foi reescrito entre 08:56 e 09:01: todas as âncoras de `ops/provisionamento/` deslocaram (+2 a +53 linhas).

**How to apply:** (1) `stat -c '%y'` dos alvos citados vs. hora do relato do worker — mtime posterior invalida a alegação até re-medir; (2) glob de família (`prefixo*.txt`) em teste é ponto de entrada para arquivo irmão de outro agente: procure quem mais escreve no mesmo diretório; (3) para provar que o teste em si está certo sem editar, copie os insumos para o scratchpad SEM o arquivo intruso e rode lá — separa "teste errado" de "insumo mudou"; (4) entregue ao orquestrador o comando de re-derivação das âncoras, não números novos, se o agente concorrente ainda estiver escrevendo.
