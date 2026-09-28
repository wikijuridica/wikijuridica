---
name: onde-fica-o-que-cerebro
description: mapa de arquivos e armadilhas de leitura para investigar o cérebro de IA local, pausa manual, Ollama e os timers systemd do portal
metadata:
  type: project
---

Onde mora o quê, medido em 2026-09-23, para não redescobrir em colheitas
futuras sobre o cérebro/Ollama:

- **Régua da pausa**: `internal/cerebrobatimento/cerebrobatimento.go` tem as
  constantes (`LimiarPausaPortal=15min`, `Infra`/`Ambiente=25min`,
  `OcupacaoCarga=30min`, `OcupacaoLock=120min`, `Manual=0` — sem teto de
  duração, só vence pelo campo `ate`). `internal/cerebro/pausa.go` só
  reexporta e adiciona `LePausaManual`/`Venceu`. O veredito de verde/vermelho
  do gate mora em `internal/checks/cerebro_batimento_gate.go:216-252`
  (`vereditoDaPausa`) — leia esse arquivo, não o wrapper bash
  `tools/check-cerebro-batimento` (que só chama `run-check`).
- **A pausa manual é checada ANTES de qualquer sonda de Ollama**
  (`internal/cerebro/saude.go:213-228`, `return` antecipado). Isso significa
  que qualquer pergunta "o que acontece se pausa manual + Ollama parado ao
  mesmo tempo" tem resposta simples: a pausa manual manda, Ollama nunca é
  sondado enquanto ela vale.
- **`wikijuridica-cerebro-saude.timer` é 1 unit oneshot com 3 `ExecStart=`**
  (`check-cerebro-vivo`, `check-cerebro-batimento`,
  `check-cerebro-enfileiramento`), não 3 timers separados. `Type=oneshot`
  para no primeiro que falhar.
- **`check-cerebro-vivo` e `check-cerebro-enfileiramento` são cegos a
  pausa/Ollama** — o primeiro só lê `systemctl show`/`journalctl` da unit
  `wikijuridica-cerebro.service` (loop de restart); o segundo só lê a
  duração da última linha de `data/ops/cerebro_enfileirar.jsonl` (regressão
  do enfileiramento em SQLite, nada de Ollama).
- **`tools/check-portal-health` (watchdog do nginx/server/cloudflared) é
  ORTOGONAL ao cérebro** — grep de `cerebro|ollama|11434|fila.sqlite`
  devolve zero. Não confundir com um detector do cérebro só porque está no
  mesmo diretório `tools/`.
- **Liberação de modelo do Ollama é sempre passiva** (`keep_alive`, nunca
  chamada de unload): drop-in `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`
  fixa `OLLAMA_KEEP_ALIVE=15m` de padrão; chamadas específicas do cérebro
  passam `KeepAlive` menor por requisição (`internal/cerebro/extracao.go:471`
  e `tarefas.go:292` usam `"10m"`; `tarefas.go:450` usa `"1m"`). Não existe
  em `internal/cerebro/*.go` nenhuma chamada explícita de descarregar
  modelo.
- **`internal/checks/cerebro_extracao_gate.go`** (gate
  `extracao-do-cerebro`) tem uma janela temporal (`janelaDaExtracao`) que
  parece predicado mas é só DIAGNÓSTICO — entra em string de erro, nunca em
  `if` que decide reprovação. Os 3 eixos reais são: âncora literal 100% na
  última linha por chave, promoção sem órfã, e frescor do manifesto do
  grafo (30h). Nenhum exige volume novo de extração.
- **`tools/generate-grafo-juridico` é independente do cérebro**: zero
  referência a `fila.sqlite`, pausa ou Ollama — só lê os JSONL de
  extração/promoção no disco, então pausar o cérebro não trava o grafo.
- **60 timers `wikijuridica-*.timer` em `ops/systemd/`, fuso MISTO**:
  `OnCalendar=` com `UTC` explícito roda em UTC; sem sufixo roda na hora
  LOCAL do host (-03:00). Comparar dois horários da tabela sem checar o
  sufixo gera falso "colidem"/"não colidem". Ex.: `cerebro-enfileirar`
  mostra `06:05 UTC`, que é `03:05` local.
- Units sempre-ligadas (sem `.timer` correspondente) se acham com
  `comm -23 <(ls *.service) <(ls *.timer)`: server, nginx, cloudflared
  (+réplica `@`), cerebro, social, alerta `@`, energia (oneshot), xvfb99,
  server-reload (via `.path`).
