---
paths:
  - "tools/check-*"
  - "data/ops/portal_health_state.json"
  - "internal/cerebro/saude.go"
---

# `tools/check-*` — read-only por padrao, e o que grava tem de declarar

Memorias de origem: `check-tools-gravar-precedente.md`,
`check-portal-health-escreve-estado.md`.

## O precedente vale contra a leitura absoluta do contrato (BUG-236)

O §4 do `CLAUDE.md` diz "check-* que grave JSONL e' falha de ferramenta a
separar". Em 2026-09-09 isso quase virou uma separacao de
`tools/check-edge-frescor --gravar --purgar` em check + generate. O repositorio
ja tem precedente contrario e **explicito** (BUG-236):
`check-edge-cache-coverage`, `check-disk-growth`, `check-fontes-alcancaveis`,
`check-internal-link-block` e `check-superficie-bots-live` sao read-only sem
flag e gravam a propria serie **so com `--gravar`**; a unit diaria passa a flag.

A forma sancionada para ferramenta nova de medicao com serie propria:
`check-*` read-only + `--gravar` (e `--purgar`/acao so sob flag), nunca escrita
silenciosa. Regra escrita de forma absoluta no contrato convive com precedente
documentado no codigo; o precedente e' o que os gates e a bancada cobram.

## O caso que prova o custo da escrita silenciosa: `check-portal-health`

`tools/check-portal-health` **nao e' read-only**: escreve
`data/ops/portal_health_state.json` (linhas ~603-607) em toda rodada, com
`reparo_ultimo: ""` quando roda sem `--repair`. O
`wikijuridica-watchdog.timer` (a cada 2 min, com `--repair`) le `reparo_anterior`
desse arquivo para contar reparos iguais seguidos e escalar
(`LIMITE_REPAROS_IGUAIS=3`). Qualquer outro processo que rode o script a cada
minuto **zera essa memoria** e reabre o laco de restart invisivel (448 restarts,
2026-08). O cerebro chamava o script antes de cada lote (~100 s); um refutador
Fable achou em 2026-09-08.

Conserto adotado: `internal/cerebro/saude.go` faz as MESMAS sondas (home,
`/healthz`, `/buscar/` pelo nginx com Host e UA de sonda; `NRestarts` por
`systemctl show`; `/api/version` do Ollama) **so em leitura**. Nunca chame
`check-portal-health` de daemon ou timer que nao seja o watchdog; para saude em
codigo, reuse `cerebro.SaudeDoPortal`.
