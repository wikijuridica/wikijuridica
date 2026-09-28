---
name: hook-colhedor-barra-ssh
description: o hook do agente documentador-de-contexto não permite ssh nem nome de comando dinâmico ($VAR) — colheita em máquina remota fica sem essa via
metadata:
  type: feedback
---

**SUPERADO EM 2026-09-24 (commit c4052966 na torre, ordem do dono: "isso é bug; corrija e dê permissão").** O hook passou a julgar o `ssh` pelo COMANDO REMOTO, com a mesma lista de leitura e sem nenhum destino de escrita do outro lado; e libera `findmnt`, `dpkg-query`, `dpkg -l/-L/-S/-s/--verify`, `apt-mark show*`, `apt-cache`/`apt` de consulta, `crontab -l`, `virsh`/`docker`/`podman`/`snap`/`flatpak`/`npm`/`pipx`/`loginctl` em subcomando de leitura, `ip` sem verbo de escrita. Use o comando direto; as vias indiretas abaixo ficam só como histórico. Todo agente ganhou `SendMessage`: avise o par por ele e pelo barramento da onda.

O `PreToolUse:Bash` deste agente (colhedor de contexto) recusa dois padrões, testados em
2026-09-24 na auditoria de migração notebook→torre:

1. **Nome de comando por variável** (`SSH="ssh ..."; $SSH '...'`) — mensagem "nome de comando
   dinâmico (\$SSH)". A leitura tem que ser um comando literal, sem indireção.
2. **`ssh` como comando**, mesmo literal e mesmo só de leitura (`ssh -o BatchMode=yes ... 'ls ...'`)
   — mensagem "ssh não está na lista de leitura do colhedor de contexto".

**Por quê**: a lista de leitura permitida a este agente é fixa (git log/show/diff/blame/status,
rg/grep, wc, sha256sum, ls, stat, date, find sem -delete/-exec, jq, sqlite3 SELECT, curl GET sem
-o, ./tools/check-*, python3 -c/heredoc literal) e `ssh` não está nela — nem para medir uma
máquina remota só leitura. Contornar com `python3 -c` chamando `subprocess.run(['ssh', ...])` é
proibido pelo mesmo espírito (edição/execução fora do escopo do colhedor).

**Como aplicar**: quando a encomenda pedir medição de host remoto, faça toda a parte local
completa, registre no mapa os comandos SSH prontos e copiáveis (num bloco separado, claramente
marcado "para quem executa"), e devolva no handback que a fatia remota não foi medida por causa
desta allowlist — quem roda é a onda de execução (Opus 5.5) ou o próprio orquestrador, que tem
`ssh` liberado. Não vale insistir tentando variações do comando.

Ver também [[hook-so-permite-leitura-listada]] (padrão geral do hook de leitura restrita).
