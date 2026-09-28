---
paths:
  - "ops/ide/**"
  - ".vscode/**"
  - "ops/terminal/**"
---

# Editor (VSCodium) e terminal (kitty): o que ja quebrou e o gate que cobra

Decisao, medicoes e bancadas: `docs/ops/IDE_VSCODIUM_20260923.md`. ADR:
`docs/adr/2026-09-23-vscodium-no-lugar-do-vscode.md`. Plano: `docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8.

## Perfil do editor e' MERGE, nunca symlink

A fonte e' `ops/ide/perfil/settings.json`. Em `~/.config/VSCodium/User/settings.json` o kit faz
merge: as chaves do repo vencem, as do dono (tema, fonte, atalhos) ficam, e o anterior vira
`settings.json.substituido-AAAAMMDD-HHMMSS`. Symlink levaria a escrita do editor para dentro do
repo; "substituir tudo" apagaria a preferencia do dono a cada execucao. Gate: `tools/check-ide-host`
confere as invariantes por parser JSONC, nao os bytes. No terminal e' o contrario: kitty e tmux so
leem a config, entao ela mora em `ops/terminal/` com symlink no home.

## Exclusoes: o que cada arquivo faz

- Watcher: o workspace (`.vscode/settings.json`, relativo) tira `.agents/runtime`,
  `.artifact-quarantine`, `.cache`, `.git`, `.toolchains`, `.venv*`, `agent-skills`, `bin`, `data`,
  `deer-flow`, `public`, `robots` e `var`; o perfil (`ops/ide/perfil/settings.json`) repete as
  raizes com caminho ABSOLUTO (`/opt/wiki/.agents/**` inteiro).
- Caminho absoluto so vale em `files.watcherExclude`. `search.exclude` e `files.exclude` sao
  relativos a pasta aberta, e chave absoluta ali e' inerte (medido com o rg embutido). No perfil,
  a busca so tira `**/.venv*/**`.
- `.agents` e `data` NAO saem inteiros da busca: saem `.agents/runtime/**/*.jsonl`,
  `.agents/runtime/tmp_rescue/**`, `data/**/*.jsonl` e `data/source-snapshots/**`;
  `.agents/runtime/contexto/` e `data/editorial/*.json` continuam pesquisaveis.
- Raiz nova com mais de 1.000 diretorios entra no watcher. O teto de inotify NAO sobe por
  precaucao: so por gatilho medido (watches do editor > 25 % do teto, ou `ENOSPC`), com drop-in
  `ops/sysctl.d/60-*`.

Gate: `python3 tools/test_ide_workspace.py` (tem controle para chave absoluta inerte).

## Extensao == CLI, e `codium` em hold

`anthropic.claude-code@<versao>` tem de ser a versao de `claude --version`. Atualizar e'
`ops/ide/atualizar-claude-code.sh <versao>`, que consulta o Open VSX ANTES de tocar o CLI. O
`codium` fica em `apt-mark hold`; pacote em hold nao aparece como `Inst` em `apt-get -s upgrade`,
entao versao nova se ve por `apt-cache policy codium` (Installed != Candidate). Sob `sudo`, a
versao do CLI se le por `readlink -f /home/rafael/.local/bin/claude`, nunca executando `claude`
de root. Gate: `tools/check-ide-host` (paridade, hold, fingerprint da chave).

## Bancada com janela: sempre `:99`, pela unit, com perfil proprio

- O display sobe so pela unit: `systemctl start wikijuridica-xvfb99.service`. Nunca `stop` (outra
  sessao pode estar em `:99`), nunca `Xvfb`/`xvfb-run` ad hoc, nunca `DISPLAY=:0` (VM do PJe).
- `codium --user-data-dir <dir proprio>`: sem isso o segundo codium fala por IPC com o do dono e a
  janela abre em `:0`. Prove a janela em `:99` com `env DISPLAY=:99 xdotool search --pid <pid do
  lock>`: o `environ` do processo do lock veio SEM `DISPLAY` na E2E de 2026-09-23.
- `claude -p --ide` NAO conecta (o init vem sem o servidor `ide`): a ponte se prova com `claude
  --ide` interativo no tmux. Handshake 101 nao prova autenticacao: sem o token o Upgrade tambem da
  101, e o `initialize` fecha com `1008 Unauthorized`.
- `--extensions-dir ~/.vscode-oss/extensions`, o real: dir vazio e' extensao ausente e falha por
  construcao.
- Espere por evento (`timeout N tail -F <log> | grep -m1 <padrao>`), nunca `sleep`.

Gate: `ops/ide/testa-ide-ponta-a-ponta.sh`, sempre como `rafael`, nunca sob `sudo`.

## Arquivar e' `mv`, nunca `rm`

Perfil antigo (`~/.config/Code`, `~/.vscode`), fontes e chave da Microsoft e `.desktop`
substituidos vao para `~/.local/share/archive-vscode-<data>/`, com `MANIFESTO.sha256`. As fontes
da Microsoft saem ANTES do purge: o `postrm` do `code` as apaga ja no `remove`. O VS Code so sai
depois de o VSCodium passar em `--verificar`. Gate: mutantes `mv`->`cp -a` e "purge antes de mover"
em `ops/ide/testa-instalar-ide.sh`.

## O que nao entra

Pylance (ausente do Open VSX), `ms-python.python` (arrasta o Pylance), Copilot, Cline, Roo,
GitLens. Python e' basedpyright + ruff na regua do gate. Sem `.editorconfig`, sem `formatOnSave`
global, sem trim de espaco nem newline final: reescrevem bytes cujo SHA-256 vai ao
`published_manifest`. So `[go]` formata, com gofmt. Nao defina `claudeCode.initialPermissionMode`
nem `claudeCode.claudeProcessWrapper`.

## O token do lock nao se imprime

`~/.claude/ide/<porta>.lock` (0600) carrega o token da ponte `/ide`. Leia so `pid`,
`workspaceFolders` e `ideName`, com `jq`; nunca o arquivo inteiro, nunca o token em log ou em
evidencia de bancada.

## kitty: `kitty @ send-key` mente

Ele injeta conforme o modo de teclado do programa, IGNORA a camada `map` e sai 0 mesmo sem enviar
nada. Tecla real: `env DISPLAY=:99 xdotool key shift+Return` (o `xdotool key` nao tem
`--display`). A assercao e' sempre por
`kitty @ get-text`, nunca pelo exit do `send-key`. No tmux, `terminal-features 'xterm*:extkeys'`
(o kitty entra como `xterm-kitty`); prova: `display -p '#{client_termfeatures}'` contem
`extkeys`. O `map shift+enter send_text all \e\r` do `kitty.conf` FICA: medido em 2026-09-23, sem
ele, dentro do tmux, Shift+Enter chega como `\r` e submete. Gate: `ops/terminal/testa-terminal.sh`.

## `/etc/sysctl.d/` e' diretorio REAL

So o `zzz-wikijuridica.conf` e' symlink para `ops/`. Arquivo novo em `ops/sysctl.d/` nao chega ao
host sem `sudo ln -sfnT`. O `zzz` tem 6 linhas ativas: comentario pode, chave nova nao. Gate:
`sudo sysctl -p /etc/sysctl.d/zzz-wikijuridica.conf | wc -l` = 6.
