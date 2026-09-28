---
name: vm-libvirt-escritorio-mapa
description: onde ficam os recursos da VM escritorio-win11 (libvirt/qemu) e a armadilha do hostdev USB anexado só em runtime, para colher contexto de migração de VM outra vez
metadata:
  type: project
---

Mapeado em 2026-09-23 (`2026-09-23-vm-escritorio-migracao.md`), para a migração
Debian 12 (notebook) -> Ubuntu Server 26.04.1 (torre nova).

**Recursos "óbvios" (disco, ISO, nvram, TPM emulado) NÃO estão todos no mesmo
lugar.** `/opt/escritorio/vm/disk/*.qcow2` e `/opt/escritorio/iso/*.iso` moram
dentro da árvore que o dono já trata como dado do escritório -- mas
`/var/lib/libvirt/qemu/nvram/<dominio>_VARS.fd` (UEFI vars persistentes) e
`/var/lib/libvirt/swtpm/<uuid>/` (estado do TPM emulado) ficam em `/var/lib/`,
fora de qualquer diretório de projeto, e por isso escapam de backup escopado
por caminho de aplicação. Perder o TPM zera as chaves seladas do Windows;
perder o NVRAM zera a configuração de Secure Boot. **Antes de declarar uma
migração de VM completa, sempre confira `/var/lib/libvirt/{qemu/nvram,swtpm}`
pelo UUID do domínio, além do óbvio em `/opt/<projeto>/vm/`.**

**Token/dongle USB anexado por `virsh attach-device --live` (sem
`--config`) nunca aparece no XML estático do domínio.** Só existe enquanto a
VM está ligada e um script o anexou -- `virsh dumpxml`/`cat
/etc/libvirt/qemu/*.xml` não mostra hostdev nenhum. A prova de que existe
está no script operacional (aqui, `/opt/escritorio/bin/token-para-vm`) que
chama `attach-device`, não no XML. Quem procura hostdev só no XML conclui,
errado, que "não há passthrough USB configurado".

**Regra "vendor:product, não porta/barramento"** é o padrão certo para
qualquer dongle -- casa em qualquer porta física, via `<vendor
id='0x...'/><product id='0x.../>` no hostdev e via `ATTR{idVendor}==...,
ATTR{idProduct}==...` na regra udev correspondente.

Ver também [[hook-so-permite-leitura-listada]] (virsh/qemu-img fora da
allowlist do agente de contexto).
