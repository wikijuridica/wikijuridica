---
name: ferramenta-seco-gerador-envelope
description: Rodar `./cmd/generate-*` (inclusive `-seco`) exige run-generate-supervised com WIKI_GO_CMD_TIMEOUT_SECONDS; o teto oculto de 300 s mata passada exaustiva
metadata:
  type: reference
---

Executar um `./cmd/generate-*` no /opt/wiki **não** passa por
`./tools/run-heavy-throttled ./tools/go-modern run ...`: o envelope exige
`cached_runner` + artifact_claim + budget + stop_condition e aborta com exit 2.
O caminho sancionado é `tools/run-generate-supervised`, que preenche o contrato:

```
WIKI_GO_CMD_TIMEOUT_SECONDS=1700 \
WIKI_HEAVY_ARTIFACT_CLAIM_PATH=<artefato material que o gerador produz> \
WIKI_HEAVY_BUDGET_MS=1800000 WIKI_HEAVY_EXPECTED_DURATION_MS=600000 \
WIKI_HEAVY_TIMEOUT_SECONDS=1800 WIKI_HEAVY_THROUGHPUT_EXPECTED=records_per_second=12 \
./tools/run-generate-supervised ./cmd/generate-<nome> <args>
```

**Why:** três tentativas se perderam em 2026-09-16 até achar cada trava, e nenhuma
mensagem de erro aponta a variável que falta:
- `WIKI_HEAVY_BUDGET_MS` acima de **1.800.000** é recusado (`budget_ms_exceeds_1800s_or_invalid`);
- o `run-go-cmd-cached` tem teto **próprio** de execução de **300 s** (`run_timeout_spec=300s`)
  que só `WIKI_GO_CMD_TIMEOUT_SECONDS` levanta (máximo 1800) — sem ele a passada
  morre com **exit 124** no meio, sem imprimir o relatório;
- exit **75** (`source/toolchain/binary identity changed before exec`) é a
  proteção certa disparando porque OUTRA frente está editando Go no worktree:
  não é bug, e a resposta é repetir o comando.

**How to apply:** ao medir "antes e depois" de um gerador, rode a passada
completa, confira o `EXIT=` e o `duration_ms`, e trave também o `-limite`: com
limite baixo o laço para antes de classificar todos os candidatos e a tabela de
recusas não é exaustiva. Em teste (`go-modern test`), se outra frente segurar o
lock genérico, `WIKI_HEAVY_LOCK_SCOPE=test:<pacote>` dá escopo próprio em vez de
esperar. Relacionado: [[corpus-vivo-durante-medicao]].
