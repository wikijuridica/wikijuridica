---
name: oraculo-go-em-scratch
description: Espelhar parser Go em Python/shell exige medir o Go num programa de scratch (GO111MODULE=off tools/go-modern run), nao recitar a regra; o brief errou 2 premissas assim
metadata:
  type: feedback
---

Quando uma ferramenta fora do Go precisa aceitar/recusar EXATAMENTE o que um parser Go aceita, copie a funcao Go (so stdlib) para um main.go no scratchpad e rode `GO111MODULE=off /opt/wiki/tools/go-modern run main.go` (~1 s, toolchain igual ao do binario). As tabelas medidas viram dado do teste Python; o programa vai no docstring do teste para re-medir.

**Why:** em 2026-09-23 (tools/cerebro-pausar) o brief dizia "chaves exatas, nem mais nem menos" e o Go aceita chave faltando, chave maiuscula, lixo depois do objeto; `time.Parse(RFC3339)` aceita `+24:00`, `,5`, ano 0000. Recitar teria feito o `status` gritar onde o gate esta verde.

**How to apply:** leitor = paridade com o oraculo; escritor = subconjunto estrito (aceitar menos e seguro, aceitar mais escreve o que o daemon nao le). Ver [[medir-a-premissa-do-briefing]].
