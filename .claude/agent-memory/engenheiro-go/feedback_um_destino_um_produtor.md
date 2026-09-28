---
name: um-destino-um-produtor
description: Ao achar um destino sem produtor, procure o produtor existente antes de escrever um segundo; se existir, o passo novo VERIFICA e nomeia quem produz
metadata:
  type: feedback
---

Quando um passo de provisionamento/ops parecer estar sem produtor, **procure o
produtor existente antes de escrever o seu**. Se ele existir, o passo novo não
copia: **confere pelo nome do artefato e nomeia o produtor no log**.

**Why:** em 2026-09-22, no kit de migração, `/usr/local/share/ca-certificates`
(cadeia ICP-Brasil) parecia órfão; o produtor era `restaurar-segredos.sh` — e não
só a cópia (`:96`), mas o `update-ca-certificates` (`:104`), que é o passo que de
fato põe a cadeia no trust store. Duplicar a cópia daria dois produtores para o
mesmo destino, que é como nasce deriva — e sem o segundo comando a cópia nem
valida nada. O maestro confirmou a escolha de verificar em vez de duplicar.

**How to apply:** `grep -rn '<caminho-destino>'` em todo o kit/ops antes de
escrever a cópia. Achou produtor: verifique o artefato **pelos nomes esperados**
(contagem genérica de arquivos não prova que os cinco certos chegaram) e cite
`arquivo:linha` de quem produz. Não achou: aí sim o passo é seu, e o comentário
registra a medição que provou a ausência. Vale também para o par oposto —
`/usr/local/bin` estava genuinamente sem produtor (nem apt, nem tarball de
segredos, nem captura de `/etc`), e aí o passo novo é obrigatório.

Relacionado: [[mutacao-em-diretorio-atestado]], [[feedback-parar-em-arquivo-concorrente]]
