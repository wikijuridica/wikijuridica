---
name: hook-so-permite-leitura-listada
description: o PreToolUse:Bash deste agente barra qualquer binário fora de uma allowlist fixa de leitura (git, grep/rg, wc, sha256sum, ls, stat, date, find sem -delete/-exec, jq, sqlite3 SELECT, curl GET sem -o, ./tools/check-*, python3 -c/heredoc literal) — inclusive claude, kitty, tmux, dpkg-query, sysctl, systemctl cat, ssh, apt-mark, ldd, npm, pipx
metadata:
  type: feedback
---

**SUPERADO EM 2026-09-24 (commit c4052966 na torre, ordem do dono: "isso é bug; corrija e dê permissão").** O hook passou a julgar o `ssh` pelo COMANDO REMOTO, com a mesma lista de leitura e sem nenhum destino de escrita do outro lado; e libera `findmnt`, `dpkg-query`, `dpkg -l/-L/-S/-s/--verify`, `apt-mark show*`, `apt-cache`/`apt` de consulta, `crontab -l`, `virsh`/`docker`/`podman`/`snap`/`flatpak`/`npm`/`pipx`/`loginctl` em subcomando de leitura, `ip` sem verbo de escrita. Use o comando direto; as vias indiretas abaixo ficam só como histórico. Todo agente ganhou `SendMessage`: avise o par por ele e pelo barramento da onda.

Ao colher contexto para a frente "IDE + terminal" (2026-09-23), pedi para rodar
`claude --version`, `~/.local/kitty.app/bin/kitty --version`, `tmux -V`,
`dpkg-query -W ...` e `sysctl -n ...` — todos vieram do prompt literal do
orquestrador. Todos foram barrados pelo hook do agente de contexto com a
mesma mensagem: "X não está na lista de leitura do colhedor de contexto".

**Por quê:** o hook não é "bloqueia escrita", é "só permite uma lista fechada
de comandos de leitura". Qualquer binário que não esteja nessa lista — mesmo
que seja só `--version`, sem efeito colateral algum — é recusado. `systemctl`
(is-active, cat) passou; `dpkg-query` não passou (mas ler `/var/lib/dpkg/status`
com `grep`/`awk` passa). `sysctl -n` não passou (mas `cat /proc/sys/fs/inotify/*`
passa). Python com `import subprocess` (mesmo sem uso) é recusado só pela
palavra no código — o hook casa por texto, não por AST.

**Como aplicar na próxima colheita:** antes de pedir versão de uma ferramenta
externa (editor, terminal, multiplexador), planeje a via indireta primeiro:
- pacote apt → `grep -A20 '^Package: NOME$' /var/lib/dpkg/status` (não
  `dpkg-query`).
- binário compilado à mão sem `--version` disponível → `grep -a -o` de padrão
  de versão no próprio arquivo binário, ou changelog/doc que viaja com a
  instalação (ex.: `.../share/doc/kitty/html/_sources/changelog.rst.txt`)
  cruzado com `mtime` do binário.
- sysctl → `/proc/sys/<caminho>` direto.
- systemd → `systemctl is-active`/`systemctl cat` funcionam (são leitura de
  estado, não execução de programa arbitrário); mas `systemctl status` de
  unidade não testado.
- Python `-c`/heredoc: nunca usar `import subprocess` nem montar código com
  variável/f-string dentro do `-c` — só literal entre aspas simples, senão o
  hook recusa por "código montado na execução". `python3 --version` e
  `python3 -V` também são recusados ("lendo código do stdin que a guarda não
  vê") — use `python3 -c 'import sys; print(sys.version)'`.
- Nunca colocar `set -x` ou múltiplos comandos com binário fora da allowlist
  no mesmo bloco: o hook recusa o bloco inteiro pelo primeiro nome de
  binário não reconhecido, mesmo que o resto do bloco seja leitura pura.

Ver também: `2026-09-23-ide-medicoes.md` (o mapa onde isso apareceu 6 vezes
na mesma sessão) e a skill `estado-real` (medir, não confiar no doc).

**`virsh` e `qemu-img` também estão fora da lista** (colheita "VM escritorio",
2026-09-23): mesmo subcomandos puramente informativos (`dumpxml`,
`domblklist`, `net-list`, `qemu-img info --backing-chain`) são recusados —
o prompt do orquestrador pode autorizá-los explicitamente por nome, mas o
hook não lê o prompt, só a allowlist fixa em `guarda_de_escrita.py:1861-1869`
(`_julga_binario`, os `if base == "..."` antes do `return f"{nome} não está
na lista..."`). Via indireta que funcionou: `sudo -n cat
/etc/libvirt/qemu/<dominio>.xml` (é exatamente o que `virsh dumpxml`
devolveria para um domínio `shutoff`/persistente — `cat` está em
`LEITURA_PURA`, `sudo` é prefixo aceito) em vez de `virsh dumpxml`; não há
equivalente indireto para `qemu-img info --backing-chain` além de ler os
elementos `<backingStore>` do próprio XML (que o libvirt já preenche com a
cadeia completa quando o domínio foi definido normalmente — mas isso não é
prova equivalente a rodar a ferramenta, é inferência sobre o que o libvirt
sabia na última vez que releu o arquivo). Ambos ficam como lacuna explícita
no mapa entregue, com o comando exato para a onda de execução rodar.

**`ssh` está TOTALMENTE fora da lista, sem exceção alguma** (auditoria de
migração, fatia C, 2026-09-24): confirmado por leitura direta de
`guarda_de_escrita.py` — `ssh` não está em `LEITURA_PURA` (linha 764-782),
não tem `PREFIXOS` que o cubra, e não tem `if base == "ssh"` próprio antes do
`return f"{nome} não está na lista..."` (linha 1869). Ao contrário de
`virsh`/`sysctl`, **não existe via indireta local** para ler o estado de uma
máquina remota — não há arquivo local equivalente a sondar. Isso barra por
completo uma tarefa cuja encomenda pede explicitamente `ssh -o BatchMode=yes
... rafael@<host> '<comando>'`. Nessa sessão o bloqueio foi contornado só
porque **o chefe (com ssh liberado) mediu a máquina remota e publicou o
resultado em `.agents/runtime/contexto/<pasta>/inventario-*.txt`**, que o
colhedor de contexto pode ler normalmente (é arquivo local). Sem essa
medição já publicada, o correto é registrar a lacuna com o comando ssh exato
para a onda de execução rodar — nunca tentar contornar via `bash -c`, `eval`
nem interpretador, porque a guarda os re-julga pelo mesmo caminho.

**Outros binários confirmados fora da lista nesta mesma colheita**:
`apt-mark` (via indireta: `/var/lib/dpkg/status` `Status: install ok
installed` menos `Auto-Installed: 1` de `/var/lib/apt/extended_states` —
reproduz o `showmanual`), `ldd` real (mas outra sessão/agente com ssh pode
rodá-lo remotamente; localmente `file -Lb` diferencia ELF de script, e
`ldd` roda se estiver na allowlist do agente QUE MEDIU, não deste), `npm`
(sem `ls`+`jq` no `package.json` de `node_modules/*/package.json`), `pipx`
(sem `ls ~/.local/pipx/venvs` ou `~/.local/share/pipx/venvs`, ambos
caminhos possíveis — conferir os dois).

Ver também: `hook-nao-permite-ler-dentro-de-iso.md` (mesmo padrão de
allowlist fechada, para `xorriso`/`unsquashfs`).

**`grep -l padrao arquivo` prova que a STRING aparece, não que o arquivo
depende do RECURSO nomeado** (auditoria de migração, fatia A, 2026-09-24).
Rodei `grep -l 'deer-flow\|agent-skills' tools/*` para achar quem exige os
diretórios clonados `/opt/wiki/deer-flow/` e `/opt/wiki/agent-skills/`, e
escrevi no mapa que 10 `tools/check-*` "referenciam" (logo, dependem d)eles.
O advisor pegou: lendo `grep -n` linha a linha, quase todos falavam de
`content/agent-skills/` (outro diretório, dado de produto, sem relação com o
clone) ou da rota HTTP `/.well-known/agent-skills/` (`internal/agentsurface`);
só `test_ide_workspace.py` cita os diretórios de verdade, e é para EXCLUIR do
lint, não para exigir presença. A torre confirmou por ausência: os dois
diretórios não existem lá e nada quebrou. **Antes de afirmar dependência a
partir de grep de string, leia a linha completa e classifique o que ela
realmente nomeia** — nome de diretório igual não é a mesma coisa quando o
projeto tem dois `agent-skills` (um clone na raiz, um dado em `content/`).
