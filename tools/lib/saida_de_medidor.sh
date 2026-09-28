# shellcheck shell=bash
# saida_de_medidor.sh — o equivalente em bash de tools/lib/saida_de_medidor.py.
#
# Mesmo contrato (0 = mediu e esta sao, 1 = mediu e esta degradado, >=2 = NAO
# mediu), mesma razao: a unit mascara o 1, entao um script que MORRE com 1
# entrega o numero de quem mediu e o OnFailure fica mudo. O motivo completo esta
# no docstring do modulo Python; aqui fica so o que e especifico do bash.
#
# ────────────────────────────────────────────────────────────────────────────
# DUAS PROTECOES, PORQUE `trap ERR` NAO COBRE O CASO MAIS COMUM DESTE REPO
#
# O plano prescrevia `trap '...' ERR` junto com `set -e`. Medido em 2026-09-16,
# nesta maquina, e o resultado muda o desenho: dos seis scripts bash chamados
# pelas units que mascaram exit 1, CINCO nao tem `set -e` — eles usam
# `set -uo pipefail` (run-daily-content:32, run-qualidade-diaria:34,
# check-untracked-e-alertar:21, repair-brotli-cobertura:39, run-qualidade-race:75).
# So run-recoleta-corpus-oraculo:34 tem `set -euo pipefail`.
#
# E a medicao do comportamento:
#
#   set -uo pipefail (SEM -e) + trap ERR + referencia a variavel nao definida
#     -> a ERR trap NAO dispara, o shell sai com 1. O crash colapsa em veredito.
#   set -uo pipefail (SEM -e) + trap EXIT
#     -> a EXIT trap DISPARA, e da para corrigir o codigo para 2.
#   set -euo pipefail + set -E + trap ERR + `false` dentro de funcao
#     -> a ERR trap dispara (o `-E` e obrigatorio: sem ele a trap nao herda
#        para funcoes e subshells, que e onde o erro costuma acontecer).
#
# Ou seja: a violacao de `set -u` — que e o modo mais comum de um script deste
# repositorio morrer — passa batido pela ERR trap. Por isso ha duas funcoes, e
# a escolha entre elas NAO e estilo: e qual `set` o script ja usa.
#
# E ACRESCENTAR `set -e` A UM SCRIPT QUE NAO O TEM ESTA PROIBIDO AQUI. Mudaria a
# semantica de falha de cada comando dele — um `grep` que nao acha nada passaria
# a abortar a execucao inteira. Isso e a regressao que o contrato veda, e seria
# introduzida por uma correcao de alarme, que e o pior lugar para descobri-la.
#
# ────────────────────────────────────────────────────────────────────────────
# COMO USAR
#
#   . "$(dirname "${BASH_SOURCE[0]}")/lib/saida_de_medidor.sh"
#
#   (A) script que JA tem `set -e`:
#         medidor_protege_err
#       Nada mais muda. Todo comando que falhar vira exit 2; os `exit N`
#       deliberados do script continuam intactos, porque a ERR trap nao os ve.
#
#   (B) script que NAO tem `set -e` (a maioria aqui):
#         medidor_protege_exit
#       e TODO ponto de saida deliberado passa a chamar `medidor_sai N` em vez
#       de `exit N`. Sem essa troca, um `exit 1` legitimo de veredito seria
#       promovido a 2 e viraria alarme falso — que e exatamente o defeito que
#       este arquivo existe para nao criar.
#
# A frase `NAO MEDIDO:` e ANCORA LITERAL lida por tools/check-units-alarme, igual
# a do modulo Python. Mudar o texto sem mudar o gate cega a deteccao.

MEDIDOR_CODIGO_NAO_MEDIDO=2

# Sentinela: 1 depois que o script alcancou um ponto de saida DELIBERADO.
# E o unico jeito de a EXIT trap distinguir "o autor decidiu sair com 1" de
# "o shell morreu com 1".
_medidor_veredito_deliberado=0

medidor_sai() {
	_medidor_veredito_deliberado=1
	exit "${1:-0}"
}

_medidor_ao_sair() {
	local rc=$?
	if [ "$rc" -eq 1 ] && [ "$_medidor_veredito_deliberado" -eq 0 ]; then
		echo "NAO MEDIDO: o script morreu com 1 sem passar por um ponto de saida" >&2
		echo "  deliberado (medidor_sai). 1 e o codigo de quem MEDIU e achou degradacao," >&2
		echo "  e a unit o mascara — sair com 1 aqui esconderia a queda atras de" >&2
		echo "  Result=success. Saindo com $MEDIDOR_CODIGO_NAO_MEDIDO para o OnFailure disparar." >&2
		rc=$MEDIDOR_CODIGO_NAO_MEDIDO
	fi
	exit "$rc"
}

_medidor_ao_errar() {
	local rc=$?
	# Sob `set -e` o shell ja esta abortando. So corrigimos o numero: 1 (o codigo
	# de veredito) vira 2 (defeito). Codigo >= 2 ja diz a verdade e passa intacto.
	if [ "$rc" -eq 1 ]; then
		echo "NAO MEDIDO: comando falhou sob 'set -e' (linha ${BASH_LINENO[0]:-?})." >&2
		echo "  Promovendo 1 -> $MEDIDOR_CODIGO_NAO_MEDIDO para que a unit nao mascare a queda como veredito." >&2
		rc=$MEDIDOR_CODIGO_NAO_MEDIDO
	fi
	exit "$rc"
}

medidor_protege_exit() {
	trap _medidor_ao_sair EXIT
}

medidor_protege_err() {
	# `-E` (errtrace) e obrigatorio: sem ele a ERR trap nao e herdada por funcoes,
	# substituicoes de comando nem subshells — que e onde o erro acontece.
	set -E
	trap _medidor_ao_errar ERR
}
