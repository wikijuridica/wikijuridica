---
name: hook-nao-permite-ler-dentro-de-iso
description: xorriso/unsquashfs/isoinfo/7z barrados pelo hook do colhedor de contexto, mesmo em uso read-only; sem atalho, workdir de extração some ao fim do script
metadata:
  type: project
---

`guarda_de_escrita.py:764-781` (`LEITURA_PURA`) não contém `xorriso`, `unsquashfs`, `isoinfo` nem
`7z`; nenhum tem tratamento de subcomando como `git`/`systemctl` têm. Qualquer chamada — mesmo
`xorriso -find` ou `unsquashfs -l`, ambos 100% leitura — cai no `else` final
(`guarda_de_escrita.py:1869`) e é recusada com "não está na lista de leitura do colhedor de
contexto". Confirmado por `grep -n "7z\|isoinfo\|xorriso\|unsquashfs\|squashfs" guarda_de_escrita.py`
→ zero ocorrências.

Não há atalho: `/opt/wiki/ops/provisionamento/remasterizar-iso.sh:38-39` usa
`mktemp -d /var/tmp/remaster-iso.XXXXXX` com `trap 'rm -rf "$TRAB"' EXIT` — o squashfs extraído
nunca sobrevive ao fim do script, então não há workdir residual para ler depois. `/proc/mounts` e
`lsblk` também não mostram ISO/squashfs de instalador já montado (só snaps do sistema).

**Como apurar**: antes de tentar de novo, `grep -i 'iso9660\|squashfs' /proc/mounts` e
`ls /var/tmp/remaster-iso.* 2>/dev/null` — mas normalmente vazio, ver acima.

**Como fechar** (registrado em `.agents/runtime/contexto/2026-09-23-subiquity-defaults.md`, rotas
a/b): (a) pedir a um agente com permissão de escrita para extrair só os caminhos necessários para
`.agents/runtime/contexto/` (texto puro, não `/tmp`, que é efêmero entre sessões minhas) e
reinvocar este agente para ler com `cat`/`grep`/`sed -n`; (b) estender o hook com judges para
`xorriso -find|-l` e `unsquashfs -l|-d <destino-permitido>`, nos moldes dos judges existentes por
volta de `guarda_de_escrita.py:1820-1850` — trabalho de execução, não meu.

Relacionado: [[hook-so-permite-leitura-listada]] (claude/kitty/tmux/dpkg-query/sysctl também
barrados, mesma família de restrição).
