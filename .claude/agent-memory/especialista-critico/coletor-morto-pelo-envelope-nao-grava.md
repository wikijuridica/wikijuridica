---
name: coletor-morto-pelo-envelope-nao-grava
description: Coletor que grava só no fim perde a passada inteira quando o envelope o mata — --tempo-limite tem de ficar bem abaixo do teto efetivo, e o teto vem do BUDGET_MS
metadata:
  type: feedback
---

Em coletor que acumula e só grava no fim (`Mescla` depois da varredura), o
`--tempo-limite` do processo tem de ficar **bem abaixo** do teto efetivo do
envelope. Morto por SIGKILL do wrapper, ele não grava nem artefato nem cursor de
retomada: a passada inteira se perde.

**Why:** 2026-09-16, `tools/collect-djen` contra o DJEN. Três falhas seguidas
antes de a primeira linha pousar no disco:

- `WIKI_HEAVY_TIMEOUT_SECONDS=2400` → **exit 2**, recusado: `run-go-cmd-cached`
  tem teto duro de **1800 s** e o comando nem rodou;
- `--tempo-limite 20m` sob `BUDGET_MS=1700000` → **exit 124** com 0 registro
  gravado. A mensagem do wrapper é explícita: *"timeout efetivo=1700s vindo de
  WIKI_HEAVY_BUDGET_MS; o WIKI_HEAVY_TIMEOUT_SECONDS declarado NÃO estava em
  vigor (vence o menor dos dois)"* — **subir só TIMEOUT_SECONDS não muda nada**;
- `--tempo-limite 8m` sob o budget padrão de 660 s → exit 124 de novo: a varredura
  de um dia inteiro do TJRJ não cabe, e o processo não chegou a decidir parar.

O que funcionou foi **fatiar com `--max-paginas`**: `--max-paginas 40
--tempo-limite 5m` → **exit 3** (= "progrediu e não terminou, cursor gravado"),
19.663 registros no disco em 110 s. A retomada costura as fatias.

**How to apply:**
- leia o teto efetivo na própria saída do wrapper antes de culpar o comando;
- prefira **fatiar o trabalho** a esticar o orçamento — a assimetria decide:
  orçamento menor só divide o trabalho, orçamento maior arrisca perder a passada;
- `exit 3` do coletor **não é falha**; `exit 124` é passada perdida e `exit 2` é
  "não rodou". Ver [[run-heavy-throttled-envelope]] e o cabeçalho de
  `ops/systemd/wikijuridica-djen-coleta.service`, que já traz essa aritmética.

**E não rode harness de mutação junto com build cacheado:** o
`run-go-cmd-cached` sai **75** com *"build source changed after authenticated
read"* quando o fonte muda no meio. Serialize os dois.
