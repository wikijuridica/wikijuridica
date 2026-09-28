---
paths:
  - "ops/**"
  - "cmd/server/main.go"
---

# `ops/` e' a config do HOST — editar o repo nao muda o host por si so

Memorias de origem: `custodia-ops-em-symlink.md`, `socket-systemd-binario-antes.md`.

## Antes de editar qualquer arquivo de `ops/`: `ls -la` no caminho INSTALADO

A config do host mora no repo e e' **instalada por symlink** — e' o padrao de
`/etc/default/earlyoom` e das ~101 units de `ops/systemd/`. Em 2026-09-08 duas
eram **copia regular**, nao symlink:
`/etc/systemd/system/ollama.service.d/wikijuridica-tuning.conf` e
`/etc/systemd/system/wikijuridica-backup.service.d/10-host-state.conf`.

Copia regular cria o "segundo lugar onde olhar" que o proprio `ops/earlyoom/default`
alerta a nao criar: editar o repo nao muda o host, e a deriva **nao aparece em
`git status`**.

Se o instalado for copia: `diff` contra `git show HEAD:<caminho no repo>`,
preserve a copia instalada em `.agents/runtime/` com data, e so entao troque por
symlink + `systemctl daemon-reload`. Varredura barata do buraco inteiro: para
cada `/etc/systemd/system/wikijuridica-*`, conferir se existe o par em
`ops/systemd/` e se o instalado e' symlink.

## O servidor pega a porta do systemd: a ordem e' binario -> socket -> servico

Desde 2026-09-01 `ops/systemd/wikijuridica-server.service` tem
`Requires=wikijuridica-server.socket` e `Type=notify`; o binario herda o socket
(`cmd/server/main.go`, `escutar`/`notificaPronto`). O systemd e' dono da porta —
binario que faz bind proprio **nunca sobe**.

Em 2026-09-02 a `.socket` nao estava instalada (17 h de 503 em toda rota
dinamica) e, ao instala-la, o watchdog (`check-portal-health --repair`, timer de
2 min) disparou `systemctl restart` com o binario velho: EADDRINUSE em laco,
porta em LISTEN pelo systemd, fila do kernel, **504 — pior que o 503**.

Ordem obrigatoria: binario novo em `bin/`
(`strings … | grep -c LISTEN_FDS` >= 1) -> symlink da `.socket` +
`daemon-reload` -> `start socket+servico`. O caminho sancionado e'
`tools/deploy-publico --sem-republicar` (compila no passo 2, sobe no 5). Antes
de instalar unit a mao, `systemctl stop wikijuridica-watchdog.timer` ou deixe o
`--repair` classificado (desde 2026-09-02 ele recusa binario sem LISTEN_FDS).
Gate: `tools/check-units-instaladas`.

## Parar unit `oneshot` em execucao dispara alerta ao dono

`systemctl stop` numa unit `Type=oneshot` que esta executando **nao** a deixa
`inactive`: ela vai a `failed (Result: signal)`, porque o `ExecStart` morre por
SIGTERM. Como as units deste repo tem `OnFailure=wikijuridica-alerta@%N.service`,
isso dispara notify-send, logger e `data/ops/owner_alerts.jsonl`. Medido em
2026-09-05 ao interromper `wikijuridica-qualidade-diaria.service`. Depois de
parar, rode `sudo systemctl reset-failed <unit>` e **diga ao dono, na mesma
resposta, que o alerta e' seu e e' falso**. `stop` nao desarma o timer.
