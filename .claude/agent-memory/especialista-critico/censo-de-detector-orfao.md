---
name: censo-de-detector-orfao
description: O censo de detector órfão é por alcançabilidade (não por menção) e seu registro de decisões NUNCA pode ser gerado por timer — isso deixaria o gate verde por construção
metadata:
  type: project
---

`tools/check-detector-orfao` mede quais `tools/check-*` / `tools/generate-*` têm
executor, e `ops/detectores-decididos.jsonl` congela o backlog decidido para que
o gate reprove **entrada nova**. `tools/generate-detectores-decididos` escreve
esse registro e é de **acionamento humano**.

**Why:** se o gerador do registro rodasse num timer, todo órfão novo ganharia
linha sozinho e o gate ficaria verde por construção — o instrumento passaria a
absolver o defeito que existe para acusar. Foi por isso que ele ficou fora de
`tools/run-qualidade-diaria`, com o motivo escrito na própria linha dele no
registro.

**How to apply:** ao propor "automatizar" a manutenção desse registro, ou ao ver
o gate vermelho com um órfão novo, a rota certa é decidir o destino do detector
(ligar, arquivar, aposentar) e regenerar à mão — nunca agendar o gerador. Três
caminhos de execução contam como "ligado", e ignorar qualquer um deles infla o
número: glob de descoberta do vigia, unit/hook, e wrapper que chama
`run-check <gate>` (esse roda pela fila de `tools/run-gates-rotativos`).
Menção em comentário e teste que só faz `os.Stat` no arquivo NÃO são executores.
