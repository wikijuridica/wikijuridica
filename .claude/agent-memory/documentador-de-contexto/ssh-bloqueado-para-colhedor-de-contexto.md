---
name: ssh-bloqueado-para-colhedor-de-contexto
description: DUPLICADO — ver hook-colhedor-barra-ssh.md, que é a versão canônica deste achado
metadata:
  type: feedback
---

**SUPERADO EM 2026-09-24 (commit c4052966 na torre, ordem do dono: "isso é bug; corrija e dê permissão").** O hook passou a julgar o `ssh` pelo COMANDO REMOTO, com a mesma lista de leitura e sem nenhum destino de escrita do outro lado; e libera `findmnt`, `dpkg-query`, `dpkg -l/-L/-S/-s/--verify`, `apt-mark show*`, `apt-cache`/`apt` de consulta, `crontab -l`, `virsh`/`docker`/`podman`/`snap`/`flatpak`/`npm`/`pipx`/`loginctl` em subcomando de leitura, `ip` sem verbo de escrita. Use o comando direto; as vias indiretas abaixo ficam só como histórico. Todo agente ganhou `SendMessage`: avise o par por ele e pelo barramento da onda.

Este arquivo é redundante com [[hook-colhedor-barra-ssh]] (mesmo achado, escrito por outra fatia
concorrente na mesma auditoria de 2026-09-24, com mais detalhe: cobre também o bloqueio de nome de
comando dinâmico via `$VAR`). Ver aquele arquivo — este fica só para não haver referência quebrada
caso algo já aponte para este nome.

Atualização 2026-09-24 13:xx: o próprio chefe já contornou a lacuna medindo a torre por fora
(`.agents/runtime/contexto/torre-inventario-20260924/inventario-torre.txt`, 45 seções `### nome`,
coletado por ssh do chefe) e reportou que o bloqueio de ssh é bug do hook em correção — não vale
mais esperar por ele: quando faltar acesso remoto, peça o inventário já coletado antes de registrar
a lacuna como aberta.
