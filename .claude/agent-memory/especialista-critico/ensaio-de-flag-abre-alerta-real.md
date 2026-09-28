---
name: ensaio-de-flag-abre-alerta-real
description: Smoke com flag inválida em tools/run-daily-content abre alerta real no ledger do dono; resolva na mesma sessão e nomeie que é seu
metadata:
  type: feedback
---

Exercitar `tools/run-daily-content` com flag inválida (`--gatilho=nao-existe`,
`--somente=canal-que-nao-existe`) **abre alerta de verdade** em
`data/ops/owner_alerts.jsonl`, pela chave da passada, e o alerta chega ao
desktop do dono. Resolva na mesma sessão com
`python3 tools/notify-owner --chave <k> --resolvido --titulo ... --mensagem ...`
e diga, no retorno, que o alerta foi seu e era falso.

**Why:** o `trap EXIT` de `gravaEvidencia` chama `notify-owner` sempre que
`falhas` não está vazia, e o aborto por flag inválida passou a chamar `registra`
(correção de 2026-09-16: antes ele imprimia "ONDA DIÁRIA OK" e *resolvia* o
alerta da onda, que era pior). Alerta que ninguém fecha faz
`check-owner-alerts-abertos` reprovar por uma condição que nunca existiu, e
ensina o dono a ignorar o canal.

**How to apply:** antes de qualquer smoke que invoque `run-daily-content`,
confira `flock -n` em `/tmp/wiki-daily-content.lock` (ocupado ⇒ a passada sai 0
em silêncio e o smoke não mede nada) e, depois de rodar, cheque a última linha
por chave em `data/ops/owner_alerts.jsonl`. Ver [[hook-barra-git-add-e-commit-como-literal]].
