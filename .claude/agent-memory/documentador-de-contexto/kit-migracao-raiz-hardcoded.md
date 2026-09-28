---
name: kit-migracao-raiz-hardcoded
description: ops/provisionamento/provisionar.sh tem RAIZ=/opt/wiki hardcoded (sem override), diferente de comum.sh; e o autoinstall (user-data) é quem coloca o kit ali antes do primeiro boot
metadata:
  type: project
---

Em `/opt/wiki/ops/provisionamento/provisionar.sh:58`, `RAIZ=/opt/wiki` é
literal, sem `${RAIZ:-/opt/wiki}` — ao contrário de `comum.sh:10`, que aceita
override por variável de ambiente. O script não usa `$0`/`dirname` para achar
seus próprios arquivos de apoio (`pacotes.txt`, `python-user-site.txt`,
`sudoers-wikijuridica-ops*`, `systemd-para-a-nova/.../20-python.conf`) —
todos são lidos por `$RAIZ/ops/provisionamento/...`. Copiar só o
`provisionar.sh` para outro diretório e rodar não falha com erro claro: as
leituras ausentes viram `aviso`/`falha` no relatório, produzindo um
provisionamento incompleto em silêncio relativo (sem lista de pacotes, sem
PATH do venv, sem sudoers instalado).

O que fazia esse `RAIZ` fixo funcionar sem fricção era o `late-commands` do
`ops/provisionamento/user-data` (linhas 174-198): ele copiava
`/cdrom/wikijuridica/.` inteiro para `/target/opt/wiki/ops/provisionamento/`
e instalava/habilitava `wikijuridica-primeiro-boot.service`
(`ConditionPathExists=/opt/wiki/ops/provisionamento/provisionar.sh`) ANTES do
primeiro boot — automação zero-touch que só existe com autoinstall/curtin.

**Why:** o dono decidiu em 2026-09-24 abandonar o autoinstall remasterizado
em favor da ISO oficial + instalador interativo padrão (subiquity) + offline
sem cabo + Wi-Fi depois. Isso remove o mecanismo automático que colocava o
kit no lugar certo e disparava o script sozinho — sem reescrever
`provisionar.sh`, o dono precisa copiar o KIT INTEIRO (não só o script) para
`/opt/wiki/ops/provisionamento/` manualmente (USB comum) antes de rodar
`sudo /opt/wiki/ops/provisionamento/provisionar.sh`, e decidir se ainda quer
a unit de primeiro boot (instalação manual da unit) ou só rodar o script uma
vez à mão.

**How to apply:** próxima onda que tocar o kit de migração deve ler
`/opt/wiki/.agents/runtime/contexto/2026-09-24-migracao-kit-vs-autoinstall.md`
antes de reescrever o roteiro — tem a tabela completa arquivo:linha do que o
`user-data` fazia e do que `provisionar.sh`/`comum.sh` pressupõem. Ver também
[[onde-fica-o-que-cerebro]] para o padrão geral de "config do host mora no
repo mas precisa ser instalada" (`.claude/rules/config-de-ops.md`), que é o
mesmo tipo de armadilha em outro subsistema.
