#!/usr/bin/env bash
# block-git-add-com-commit.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# BARRA: `git add` e `git commit` EXECUTADOS no MESMO payload de Bash.
# O pre-commit deste repositorio compila o INDICE. Com os dois no mesmo comando
# o indice ainda esta sendo escrito quando a compilacao comeca, e o hook reprova
# com "indice mudou durante compilacao" — reprovacao que nao diz o que fazer.
#
# NAO barra: `git add` sozinho; `git commit -F` sozinho; `git commit` precedido
# apenas de leitura (`git status`, `git diff`); nem TEXTO que só cita os dois.
#
# ---------------------------------------------------------------------------
# FALSOS POSITIVOS MEDIDOS EM 2026-09-23 (bancada: block-git-add-com-commit.test.py)
# ---------------------------------------------------------------------------
# A versão anterior casava por SUBSTRING crua (`*"git add"*` e `*"git commit"*`)
# sobre o payload inteiro. Três barragens medidas no mesmo dia, nenhuma executava
# os dois comandos:
#   * um `python3 - <<'EOF'` cujo corpo só GRAVAVA num documento a rota
#     "`git add <caminho>` -> `git commit -F <msg>`", entre crases de markdown;
#   * um `grep -l 'git add e git commit no mesmo comando'` que só procurava a
#     própria mensagem deste hook;
#   * a escrita DESTE arquivo por `cat > ...sh <<'EOF'`: o `.sh` do nome virava
#     "interpretador" no strip-heredoc-body.py (defeito 1 de lá) e o corpo ficava
#     sob análise.
# Guarda que barra quem documenta a regra ensina a contorná-la.
#
# O predicado agora tem DUAS etapas, e cada uma tem controle negativo na bancada:
#   1. o corpo de heredoc QUOTED sai da análise, pelo mesmo auxiliar do
#      block-heavy-go.sh (strip-heredoc-body.py), com `--so-shell`: só fica o corpo
#      que alimenta um SHELL (bash, sh, ssh...), porque só ali `git add` é comando.
#      Corpo de python/node/perl é código de outra linguagem: `git add` lá dentro é
#      texto de string, e a crase do markdown não é substituição de comando.
#      Se o auxiliar falhar, a análise segue sobre o payload cru (barra demais,
#      nunca de menos);
#   2. `git add` e `git commit` têm de estar em POSIÇÃO DE COMANDO: início do
#      valor de "command", ou depois de ; & | ( { ! crase `$(` ou quebra de linha
#      (o `\n` do JSON), ou no início do comando de `bash -c`/`sh -lc`/`eval`/
#      `ssh host '...'`/`su -c '...'`, descontados prefixos transparentes
#      (sudo -u x, command, env VAR=x, nice -n N, timeout N, xargs, then/do/else, VAR=x,
#      `flock [opções] TRAVA`, setsid, stdbuf, ionice, systemd-run, taskset, chronic,
#      unbuffer) e as opções globais do git (`git -C dir add`, `git -c k=v commit`,
#      `/usr/bin/git`). Heredoc que vai para shell por pipe ou por arquivo executado
#      na mesma linha fica sob análise (defeito 7 do strip-heredoc-body.py).
#
# LIMITE DECLARADO (medido em 2026-09-23): python/node que executa git por
# `os.system("git add x && git commit ...")` ou `subprocess` NÃO é visto — o corpo
# de python sai pelo `--so-shell`, e dentro dele não há posição de comando de
# shell. O hook antigo barrava o `os.system` por acaso de substring (e deixava
# passar a forma de lista do subprocess). Mesma fronteira que o
# block-heavy-go.test.py declara; o custo do falso negativo aqui é o pre-commit
# reprovar com 'indice mudou', não dado perdido. Script ou alvo de make que faz os
# dois (`make commit-tudo`) é invisível aqui, como sempre foi.
#
# O valor de "command" é analisado CRU, escapado de JSON, como no block-heavy-go.sh
# (a "description" fica de fora): o auxiliar reconhece a quebra de linha pelo par
# `\n` sem confundir com `\\n`, e o recorte cobre o separador com e sem espaço
# (`"command":"` e `"command": "`).
set -uo pipefail
trap 'exit 0' ERR
AQUI="$(dirname "${BASH_SOURCE[0]}")"
. "$AQUI/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT=""
IFS= read -r -d '' INPUT || true
if [ -z "$INPUT" ]; then exit 0; fi
# Caminho rápido, zero processo: sem as três palavras no payload não há o que julgar.
if [[ "$INPUT" != *git* || "$INPUT" != *add* || "$INPUT" != *commit* ]]; then exit 0; fi

# Só o VALOR de "command" entra na análise: a "description" é prosa do agente, e
# `x; git add y; git commit` escrito nela não executa nada. O recorte respeita o
# escape do JSON (`\"` e `\\` não encerram o valor). Sem o campo, fica o payload
# inteiro — o lado conservador.
TEXTO="$INPUT"
re_valor='"command":[[:space:]]*"(([^"\\]|\\.)*)"'
if [[ "$INPUT" =~ $re_valor ]]; then
	TEXTO="\"command\":\"${BASH_REMATCH[1]}\""
	if [[ "$TEXTO" != *git* || "$TEXTO" != *add* || "$TEXTO" != *commit* ]]; then exit 0; fi
fi
if [[ "$TEXTO" == *"<<'"* || "$TEXTO" == *'<<\"'* || "$TEXTO" == *'<<-'* || "$TEXTO" == *'<< '* ]]; then
	DESPIDO="$(printf '%s' "$TEXTO" | python3 -I "$AQUI/strip-heredoc-body.py" --so-shell 2>/dev/null)" || DESPIDO=""
	if [ -n "$DESPIDO" ]; then TEXTO="$DESPIDO"; fi
fi

# As ERE ficam em VARIÁVEL e o teste usa `=~ $var` sem aspas: com `(` dentro de
# colchete, a ERE literal dentro de [[ ]] quebra o PARSE do arquivo inteiro
# (medido em block-heavy-go.sh, 2026-07-28).
NL=$'\n'
# A string de `bash -c '...'`, `sh -lc "..."`, `/bin/bash -e -c '...'` e `eval "..."`
# também é comando. Medido em 2026-09-23: sem esta âncora, `bash -c 'git add x &&
# git commit -F m'` saía 0 (o `git add` vinha depois de aspa), e o hook antigo
# barrava — regressão que a bancada agora cobre (mutante m3g).
SHELL_C='(^|[^[:alnum:]_.-]|\\[nt])((ba|da|z|k|mk)?sh|busybox[[:space:]]+sh)([[:space:]]+-[A-Za-z]+)*[[:space:]]+-[A-Za-z]*c[[:space:]]+(\\"|'"'"'|\$'"'"')?|(^|[^[:alnum:]_.-]|\\[nt])eval[[:space:]]+(\\"|'"'"'|\$'"'"')?|(^|[^[:alnum:]_.-]|\\[nt])(flock|script)([[:space:]]+[^[:space:];&|]+)*[[:space:]]+(-[A-Za-z]*c|--command)[[:space:]]+(\\"|'"'"'|\$'"'"')?'
# O comando de `ssh [opções] host '...'` e de `su [usuario] -c '...'`, pelo mesmo
# motivo: o hook antigo barrava os dois por acaso de substring, e sem esta âncora o
# novo deixava passar (medido em 2026-09-23; mutante m3h). `ssh-add`/`ssh-keygen`
# não casam: o nome tem de terminar em espaço.
REMOTO='(^|[^[:alnum:]_.-]|\\[nt])(ssh|autossh)([[:space:]]+-[A-Za-z]+([[:space:]]+[^-[:space:];&|][^[:space:];&|]*)?)*[[:space:]]+[^-[:space:];&|][^[:space:];&|]*[[:space:]]+(\\"|'"'"'|\$'"'"')?|(^|[^[:alnum:]_.-]|\\[nt])su([[:space:]]+[^[:space:];&|]+)*[[:space:]]+-c[[:space:]]+(\\"|'"'"'|\$'"'"')?'
ANCORA='(^|"command":[[:space:]]*"|[;&|({`!]|\\n|'"$NL"'|'"$SHELL_C"'|'"$REMOTO"')'
ESP='([[:space:]]|\\t)'
PAL='[^[:space:];&|]'
# PREFIXO: o que vem antes do `git` sem mudar a posição de comando. Wrapper com
# opções, com opção que leva argumento, e wrapper que leva um POSICIONAL antes do
# comando (`flock [opções] TRAVA git commit`, `taskset MÁSCARA`, `script -q ARQ`).
# O `flock` entrou em 2026-09-23 porque a forma DOCUMENTADA do commit deste repo é
# `flock /tmp/opt-wiki-agent-heavy.lock git commit -F <msg>`
# (docs/OPERACAO_COMANDOS_E_CAMINHOS.md) e a própria mensagem abaixo ensina o flock:
# sem ele, `git add x && flock LOCK git commit -F m` saía 0 (o hook antigo barrava).
OPCOES='('"$ESP"'+-'"$PAL"'+('"$ESP"'+[^-[:space:];&|]'"$PAL"'*)?)*'
PREFIXO='((sudo|doas|xargs|setsid|stdbuf|ionice|systemd-run|chronic|unbuffer|command|exec|nohup|time|then|do|else|if|while|until)'"$OPCOES"'|env('"$ESP"'+(-'"$PAL"'+|[A-Za-z_][A-Za-z0-9_]*='"$PAL"'*))*|nice('"$ESP"'+-'"$PAL"'+('"$ESP"'+-?[0-9]+)?)*|timeout('"$ESP"'+-'"$PAL"'+('"$ESP"'+[0-9.]+[smhd]?)?)*'"$ESP"'+[0-9.]+[smhd]?|(flock|taskset|script)'"$OPCOES$ESP"'+'"$PAL"'+|[A-Za-z_][A-Za-z0-9_]*='"$PAL"'*)'
GIT='('"$PAL"'*/)?git('"$ESP"'+(-C|-c|--git-dir|--work-tree|--namespace|--exec-path|--config-env)'"$ESP"'+'"$PAL"'+|'"$ESP"'+--?[A-Za-z][A-Za-z0-9-]*(='"$PAL"'*)?)*'
FIM='([[:space:];&|)"`]|\\|$)'
re_add="$ANCORA$ESP*($PREFIXO$ESP+)*$GIT$ESP+add$FIM"
re_commit="$ANCORA$ESP*($PREFIXO$ESP+)*$GIT$ESP+commit$FIM"

if [[ "$TEXTO" =~ $re_add ]] && [[ "$TEXTO" =~ $re_commit ]]; then
	bloqueia \
		"git add e git commit no mesmo comando: o pre-commit deste repo compila o INDICE e reprova com 'indice mudou durante compilacao'." \
		"Separe em DUAS chamadas Bash:
  1)  git add caminho/exato/do/arquivo
  2)  git commit -F /caminho/da/mensagem.txt
A mensagem vai por -F sempre, nunca por -m com heredoc, e a saida do hook nunca
e capturada no MESMO arquivo passado a -F (isso sobrescreve a mensagem).
Commit que toca Go/go.mod/go.sum serializa com flock /tmp/opt-wiki-commit.lock."
fi
exit 0
