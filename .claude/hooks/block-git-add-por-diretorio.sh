#!/usr/bin/env bash
# block-git-add-por-diretorio.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# BARRA: `git add` que varre mais do que o arquivo declarado —
#   git add .            git add -A            git add --all
#   git add -u           git add data/         git add internal/render
# O INDICE e compartilhado entre as sessoes deste repositorio. Adicionar por
# diretorio ja varreu trabalho nao-commitado de outra frente tres vezes: o
# commit sai com arquivo que o autor nunca leu, e desfazer e' proibido aqui.
#
# NAO barra: `git add caminho/exato/do/arquivo.go`, nem `git add -p`, `--patch`,
# `--dry-run`, `-n`, `--intent-to-add`/`-N` (que nao materializam conteudo).
#
# A distincao arquivo x diretorio nao e' derivavel de regex: o hook roda DENTRO
# do repositorio, entao ela e' feita com `test -d`, que e' builtin (zero processo).
set -uo pipefail
trap 'exit 0' ERR
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
[ -z "$INPUT" ] && exit 0
[[ "$INPUT" != *"git add"* ]] && exit 0

RAIZ="${CLAUDE_PROJECT_DIR:-/opt/wiki}"

ensino="Adicione o CAMINHO EXATO de cada arquivo:
  git add internal/render/page.go
Em lote, DERIVE a lista em vez de colar caminho a caminho (as duas passam):
  find .claude/rules -type f -print0 | xargs -0 git add --
  git add \$(git ls-files -m -- internal/render)
Para ver o que entraria antes de decidir:
  git status --short
  git diff --stat -- <caminho>
Caminho exato nao basta quando outra frente edita o mesmo arquivo: confira o
mtime e o diff contra a copia preservada antes de adicionar.
Depois, o commit vai em chamada SEPARADA e com -F <arquivo>."

# A CAUDA DO `git add` TERMINA NA LINHA, e isto custou um falso positivo caro.
# A classe negada original nao excluia a QUEBRA DE LINHA, entao num payload de
# varias linhas a captura atravessava para a seguinte. Medido em 2026-09-22:
#
#     git add tools/check-network-health tools/test_medir_wifi.py
#     git status --porcelain -- tools/ .agents/runtime/ | sed 's/^/  /'
#
# O `git add` da primeira linha nomeia DOIS ARQUIVOS e nada mais. Mas a captura
# seguia ate o `|` do `sed`, la na segunda linha, e engolia o `tools/` do `git
# status` -- um argumento que o `git add` nunca recebe, e que termina em `/`.
# Resultado: a forma CERTA era barrada por causa de um comando de LEITURA que
# vinha depois. E o bloqueio ensinava a fazer o que ja estava sendo feito.
#
# E o mesmo erro de forma que o comentario do `derivada` logo abaixo ja descreve:
# o predicado tem de ser "o git RECEBE este argumento", nunca "o payload MENCIONA
# este texto". Guarda que reprova a forma certa empurra para a errada.
NL=$'\n'
resto="$INPUT"
while [[ "$resto" =~ git[[:space:]]+add([^;&|\"$NL]*) ]]; do
	args="${BASH_REMATCH[1]}"
	resto="${resto#*"${BASH_REMATCH[0]}"}"

	# Formas que varrem por definicao, independente do que exista no disco.
	for bandeira in $args; do
		case "$bandeira" in
		-A | --all | -u | --update | --no-ignore-removal)
			bloqueia \
				"git add $bandeira varre a arvore inteira: o indice e' compartilhado entre sessoes e isso ja arrastou trabalho nao-commitado de outra frente tres vezes." \
				"$ensino"
			;;
		-p | --patch | --dry-run | --intent-to-add | -N)
			# Nao materializam conteudo no indice: deixa passar a invocacao toda.
			exit 0
			;;
		esac
	done

	# O PREDICADO E "o git RECEBE um diretorio", nao "o comando MENCIONA um".
	#
	# Defeito medido em 2026-09-16: `git add $(find .claude/hooks -type f)` era
	# barrado. O word splitting do payload parte a substituicao em pedacos, um
	# deles e' `.claude/hooks`, e `test -d` dizia "diretorio" sobre um texto que o
	# git NUNCA recebe -- a substituicao entrega arquivo por arquivo.
	#
	# E O FALSO POSITIVO NAO ERA INOCUO. Ele encarecia justamente a forma CERTA
	# (derivar a lista de arquivos), empurrando para `git add <dir>` -- o defeito
	# real -- ou para colar uma lista gigante a mao, que e' onde se erra um
	# caminho. Guarda que torna o caminho certo mais caro que o errado inverte o
	# incentivo que ela existe para criar.
	#
	# Entao: lista DERIVADA (substituicao de comando ou de variavel) sai da
	# analise de diretorio. Nao e' afrouxamento -- `-A`, `--all` e `-u`, que
	# varrem por definicao e nao dependem de argumento, continuam barrados acima,
	# e sao eles que arrastam trabalho alheio. `find | xargs git add` tambem passa,
	# e sempre passou: ali a cauda do `git add` e' vazia ou so `--`.
	derivada=0
	if [[ "$args" == *'$('* || "$args" == *'`'* || "$args" == *'${'* ]]; then
		derivada=1
	fi

	for alvo in $args; do
		[[ "$alvo" == -* ]] && continue
		[ "$alvo" = "--" ] && continue
		[ "$derivada" = 1 ] && continue

		if [ "$alvo" = "." ] || [ "$alvo" = ".." ] || [[ "$alvo" == */ ]]; then
			bloqueia \
				"git add $alvo adiciona por diretorio: o indice e' compartilhado entre sessoes e isso ja arrastou trabalho nao-commitado de outra frente tres vezes." \
				"$ensino"
		fi

		# GLOB: quem decide e' o que ele CASA, nao o texto. `.claude/hooks/*.sh` so
		# casa arquivo e passa; `.claude/*` casa diretorio e o git o adicionaria
		# recursivamente, entao reprova. Expansao do proprio bash, zero processo.
		if [[ "$alvo" == *[\*\?\[]* ]]; then
			for casado in "$RAIZ"/$alvo $alvo; do
				if [ -d "$casado" ]; then
					bloqueia \
						"git add $alvo e um glob que casa o DIRETORIO ${casado##*/}: o git o adicionaria inteiro, e o indice e' compartilhado entre sessoes." \
						"$ensino"
				fi
			done
			continue
		fi

		if [ -d "$RAIZ/$alvo" ] || [ -d "$alvo" ]; then
			bloqueia \
				"git add $alvo aponta para um DIRETORIO: o indice e' compartilhado entre sessoes e adicionar por diretorio ja arrastou trabalho nao-commitado de outra frente tres vezes." \
				"$ensino"
		fi
	done
done
exit 0
