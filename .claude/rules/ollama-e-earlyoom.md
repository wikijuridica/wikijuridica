---
paths:
  - "ops/ollama/**"
  - "ops/earlyoom/**"
  - "internal/cerebro/saude.go"
  - "tools/generate-medicao-runner-local"
  - "data/ops/ia_local_runner_variantes.jsonl"
---

# Ollama e earlyoom neste host — o valor corrente mora no drop-in, nao na memoria

Memorias de origem: `ollama-local-memoria-e-banda.md`,
`ollama-sampler-e-modelo-escondem-custo.md`, `earlyoom-prefer-nao-ordena.md`.

Host: 19,4 GiB de RAM, 4 nucleos fisicos / 8 threads, sem GPU util (MX110 sem
driver, UHD 620 inutil para 9-14B). Modelos em `/usr/share/ollama/.ollama`.

## O incidente que originou o teto (2026-09-08)

Um benchmark carregou `qwen2.5-coder:14b` (9,9 GB) e `qwen3.5:9b` (6,1 GB) em
sequencia; com o `OLLAMA_MAX_LOADED_MODELS` padrao os dois ficaram residentes
(16 GB), a RAM livre caiu a 4,7% e o **earlyoom** matou `chrome_crashpad` e
`llama-server` — e junto foram os quatro servidores MCP (node) da sessao do
Claude Code (`Connection closed`). Nao foi bug de plugin: foi memoria.

## O remedio de hoje (2026-09-10) — e por que nao e' "um modelo por vez"

`OLLAMA_MAX_LOADED_MODELS` e' **2**, e a guarda real nao conta modelos: ela pesa
**bytes residentes** (teto de 9 GiB) em `internal/cerebro/saude.go`. O par do
incidente (14b + 9b = 16 GB) continua barrado; os dois que alternam hoje somam
3,87 GB. `MemoryMax` passou de 15G para **12G** — os 15G vinham da RAM do host,
nao do consumo, e deixavam 4,4 GiB de folga, exatamente a folga que o earlyoom
comeu. `CPUWeight` segue 60; a slice `wikijuridica_alimentacao` desceu para 20.

O que um residente por vez custa e' LATENCIA da rota anunciada, nao throughput:
cada troca cobra o load de volta, e o pior caso medido e' 234,2 s.

**Antes de recomendar qualquer flag, leia o drop-in vivo**
`ops/ollama/ollama.service.d/wikijuridica-tuning.conf` — esta regra descreve o
incidente e a fisica; o valor corrente mora la.

## `--prefer` do earlyoom NAO ordena — e por isso ele matou o alvo errado

Medido em 2026-09-08: `--prefer` da o **mesmo bonus** a todos os nomes da lista e
a vitima e' sempre a de maior *badness*. Como o Chrome sobe o proprio
`oom_score_adj` nos renderizadores, ele fica acima do `llama-server` por
construcao. Censo das 28 mortes daquele dia
(`journalctl -u earlyoom --since today | grep -E 'sending SIG(TERM|KILL) to process'`):
chrome n=21 badness 1101 somando 2.026 MiB; node n=4 badness 966 somando 120 MiB
(os MCP das sessoes); chrome-devtools 1; chrome_crashpad 1; e
**llama-server n=1, badness 856, 9.405 MiB — o unico que resolvia, e o ultimo a
cair**. O host matou 27 processos somando 2,2 GB antes de chegar no que segurava
9,4 GB.

O `CLAUDE.md` §12 e o proprio `ops/earlyoom/default` afirmavam que "llama-server
e' o primeiro alvo": era intencao escrita, nao comportamento medido.
**Para escolher a vitima de verdade use `OOMScoreAdjust=` na unit** (herdado
pelos filhos: no `ollama.service` o `llama-server` herda), nunca `--prefer`.
Aplicado: `OOMScoreAdjust=800` no drop-in do ollama (`oom_score` 1200, acima dos
1101-1172 medidos no Chrome) e `node` fora do `--prefer`. Confira pelo journal,
nunca pelo comentario: `--prefer` promove, `--avoid` protege, e so a badness
decide.

## Tres custos que `ollama ps` nao mostra e o journal mostra (2026-09-08)

1. **O `presence_penalty` do Modelfile CHEGA ao sampler.** `presence_penalty =
   1.500` em 124 das 128 linhas de sampler do journal do dia, porque o Modelfile
   de `qwen3.5:4b` traz `presence_penalty 1.5`. Em saida estruturada isso e'
   veneno: a resposta repete `"norma"`, `"artigo"`, `"texto_citado"` a cada item
   e a penalidade empurra o modelo contra escrever a propria gramatica a partir
   do segundo item — candidata direta a `done_reason=length` e item descartado.
   O cliente Go nao mandava o campo; zere por ordem, como ja se faz com `think`
   e `temperature`.
2. **Modelo com `vision` cobra a torre mesmo em uso so-texto.** `ollama show
   qwen3.5:4b` traz `capabilities: vision` e `qwen35.vision.block_count = 24`; o
   ollama sobe `--mmproj <o mesmo blob do --model>` e o log declara
   `estimated worst-case memory usage of mmproj is 961.74 MiB`.
3. **Modelo hibrido nao reaproveita prefixo compartilhado.**
   `qwen35.full_attention_interval = 4` com `block_count = 32` da 8 camadas de
   atencao plena (`llama_kv_cache: 8 layers`); o resto e' recorrente. Prompt
   identico repetido reaproveita tudo (1088 -> 4 tokens processados), mas entre
   ementas DIFERENTES com o mesmo prefixo de sistema o `prompt_n` sai cheio
   (1088, 581, 650, 808, 600). O log culpa "SWA or hybrid/recurrent memory".

## Como medir tuning sem enganar-se

`tools/generate-medicao-runner-local` sobe um llama-server proprio em porta
separada, com prompt e corpus reais, e escreve
`data/ops/ia_local_runner_variantes.jsonl`. **Leia `prompt_n`**: e' contagem de
token, imune a carga da maquina, ao contrario de tok/s. Medido la:
`--flash-attn` e KV `q8_0` sao NEUTROS para velocidade nesta CPU (15,63 vs 15,35
tok/s de prompt; 4,42 vs 4,55 de eval) — o que eles compram e' memoria (508 MiB).

Velocidade da CPU, para calcular antes de prometer: 14b = prompt 5,1 tok/s,
geracao 1,85 tok/s; 9b = prompt 5,6 e 2,90. Isso e' ~18 GB/s de banda efetiva
(geracao ~= 18 GB/s / bytes do modelo; o prompt e' compute-bound). Consequencia:
trabalho 24/7 em modelos de 0,6 a 4B com entrada curta pre-extraida; o 14b so em
lote noturno de alto valor.
