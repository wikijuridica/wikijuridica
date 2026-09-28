#!/usr/bin/env bash
# block-check-runner-sem-alvo.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# BARRA: o runner de gates invocado SEM alvo nomeado.
#   ./tools/run-check                      -> roda TODOS
#   ./tools/go-modern run ./cmd/check      -> roda TODOS
# `cmd/check/main.go:223` fixa `options{target: "all"}` como default, entao a
# invocacao nua nao "lista" nem "ajuda": ela dispara o runner inteiro. Em
# 2026-08-29 isso abriu 45 processos e levou o load da maquina de 8 nucleos a 52.
#
# NAO barra: alvo posicional (`run-check <nome>`), `--checks a,b`, `--lista-nomes`
# (que responde QUAIS gates existem sem executar nenhum — cmd/check/main.go:61),
# nem `--help`/`-h`. O alvo `all` ja e barrado por block-heavy-go.sh.
#
# Fail-open: qualquer erro -> exit 0. Um hook quebrado derruba TODA chamada Bash
# do repositorio, e ja derrubou (ver o cabecalho de block-heavy-go.sh).
set -uo pipefail
trap 'exit 0' ERR
# shellcheck source=lib/bloqueio.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
[ -z "$INPUT" ] && exit 0

# Saida rapida sem processo: se nenhum dos dois tokens aparece, o hook nao tem
# o que fazer. E o caminho de 99% das chamadas Bash deste repo.
[[ "$INPUT" != *run-check* && "$INPUT" != *cmd/check* ]] && exit 0

# Ancora de POSICAO DE COMANDO, na mesma forma que block-heavy-go.sh usa: abertura
# do campo `command` do JSON, separador de shell, ou quebra de linha escapada.
# Sem ela, uma MENCAO em prosa (mensagem de commit, documentacao) casaria — e
# documentar a regra e como ela se propaga.
RE_ANCORA='("command":[[:space:]]*"|[;&|(`'$'\n'']|\$\(|\\n)[[:space:]]*(([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*|nice|-n|[0-9]+|sudo|-E|time|env|command|exec|nohup|setsid|flock|xargs|(\./)?(tools/)?go-modern|go|run)[[:space:]]+)*'
RE_RUNNER=$RE_ANCORA'(\./)?(tools/)?(run-check|[^[:space:];&|"]*cmd/check)'

resto="$INPUT"
while [[ "$resto" =~ $RE_RUNNER ]]; do
	# A cauda e' derivada por POSICAO, nao por numero de grupo: contar grupos de
	# uma ERE montada por concatenacao ja quebrou este hook uma vez (o indice
	# apontava para o nome do runner, entao TODA invocacao parecia ter alvo e
	# nada era barrado). Aqui o texto depois do casamento e' cortado no proximo
	# separador de shell — o que sobra e' a cauda daquela invocacao.
	depois="${resto#*"${BASH_REMATCH[0]}"}"
	resto="$depois"
	cauda="${depois%%[;&|]*}"
	cauda="${cauda%%\"*}"

	tem_alvo=0
	# `--lista-nomes`, `--checks` e `--help` sao alvos legitimos de leitura.
	[[ "$cauda" == *--lista-nomes* || "$cauda" == *--checks* ]] && tem_alvo=1
	[[ "$cauda" == *--help* || "$cauda" == *" -h"* ]] && tem_alvo=1
	if [ "$tem_alvo" = 0 ]; then
		# Alvo posicional = primeira palavra da cauda que nao comeca com `-`.
		for palavra in $cauda; do
			[[ "$palavra" == -* ]] && continue
			tem_alvo=1
			break
		done
	fi
	[ "$tem_alvo" = 1 ] && continue

	bloqueia \
		"Runner de gates sem alvo nomeado: cmd/check/run-check sem argumento roda TODOS os gates (cmd/check/main.go:223 usa target=all como default). Em 2026-08-29 abriu 45 processos e levou o load a 52." \
		"Rode UM gate, nomeado:
  ./tools/go-modern run ./cmd/check <nome>
Nao sabe o nome? A flag responde sem executar gate nenhum:
  ./tools/go-modern run ./cmd/check --lista-nomes
Escolher o conjunto pelo que mudou (nao pelo habito):
  ./tools/generate-check-selection-profiles --paths <arquivos>
Gate verde nao e 'nao quebrei nada': rode tambem a bancada do pacote —
  ./tools/go-modern test -count=1 ./internal/<pkg>/"
done
exit 0
