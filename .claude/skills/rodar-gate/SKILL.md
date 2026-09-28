---
name: rodar-gate
description: Use antes de rodar qualquer gate, check ou teste Go — escolhe o escopo pelo risco e evita o comando que derruba a máquina.
---

# Rodar gate

## As três formas que derrubam a máquina

| Nunca | Porque | Em vez disso |
|---|---|---|
| `cmd/check` ou `run-check` **sem argumento** | o default é `target: "all"` (`cmd/check/main.go:223`): 45 processos, load 52 | `./tools/go-modern run ./cmd/check <nome>` |
| padrão full-tree (`./` + três pontos) | são 488 pacotes | `./tools/go-modern build ./internal/... ./cmd/...` |
| rodar o runner "para ver a lista" | executa tudo | `./tools/go-modern run ./cmd/check --lista-nomes` |

Um hook barra as três. Se ele barrou, a mensagem já traz o comando certo.

## Escolher o escopo pelo risco, não pelo hábito

1. `./tools/generate-check-selection-profiles --paths <arquivos>` deriva o
   conjunto de checks a partir do que mudou.
2. **Probe curto antes de qualquer passada 10k/100k.** Amostra por *stride*
   determinístico; prefixo conveniente não é evidência de escala.
3. Teste focado. Suíte global só em mudança crítica, e sempre envelopada em
   `./tools/run-heavy-throttled`.

## Gate verde não é prova

- **Gate verde não é "não quebrei nada".** Em 2026-09-05 um gate passou verde e
  **14 dos 17 testes dele** quebraram — o defeito pousou em HEAD. Rode a bancada
  do pacote: `./tools/go-modern test -count=1 ./internal/<pkg>/`.
- **Gate vermelho não é veredito.** Leia a implementação do detector antes de
  decidir por ela. Reprovação por dívida alheia não é regressão sua — confira o
  baseline de vermelhos conhecidos.
- Detector novo nasce com teste de **falso positivo** sobre amostra real. Já
  houve detector que acusou 46 páginas e as 46 eram falso positivo.
- `check-*` é read-only; `generate-*` escreve. `check-*` que grave é falha de
  ferramenta a separar.

## Antes de comando pesado

`./tools/check-load-headroom --max 12` · `tools/check-coord-status`. Lock ativo
⇒ trabalhe outra frente; nunca derrube o dono do lock. Em pipeline, `cmd | tail`
engole o exit real — leia `PIPESTATUS[0]`.

Lentidão em 10k é **bug P0** de escala, mesmo com CPU e I/O folgados, e é
proibido "corrigir" aumentando timeout.
