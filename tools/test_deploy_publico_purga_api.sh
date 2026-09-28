#!/usr/bin/env bash
# Prova que a lista de purga do deploy cobre, para cada pagina do acervo que
# mudou, as QUATRO entradas que ela tem na borda: o HTML, a gemea Markdown e os
# dois itens da API por caminho (/api/v1/pages/<rota> e /api/v1/citar/<rota>).
#
# POR QUE (medido 2026-09-09): a Cache Rule 3 (versao 18 da zona) passou a
# respeitar o s-maxage=3600 dos itens da API. O item de /api/v1/citar carrega o
# html_sha256 da pagina -- e o agente usa esse hash para conferir integridade.
# Sem purga por URL, a borda serviria o hash VELHO por ate uma hora depois de
# cada republicacao, justamente no canal de quem cita. Hub, paginacao, /fontes/ e
# institucionais nao tem item na API (404 medido em 2026-09-09 para /sobre/,
# /glossario/ e /familia/pagina/2/): pedir a purga deles seria pedir o que nao
# existe -- e a gemea das institucionais continua na lista, como antes.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
# ANCORAS TOLERANTES A FORMATACAO (2026-09-16): a versao anterior exigia quatro
# espacos de indentacao e um espaco depois do `<`. O shfmt trocou os espacos por
# TAB e colou `<"`, o bloco extraido virou VAZIO e este teste passou a reprovar
# com "bloco nao encontrado" sem que a purga tivesse mudado. O fim do bloco agora
# e um marcador em comentario, que nenhum formatador move.
bloco=$(sed -n '/^[[:space:]]*# AS GEMEAS EM MARKDOWN DE CADA PAGINA QUE MUDOU\.$/,/^[[:space:]]*# --- fim da expansao por pagina ---$/p' "${DEPLOY_PUBLICO:-tools/deploy-publico}")
[[ -n "$bloco" ]] || {
	echo "FALHA: bloco da expansao nao encontrado em deploy-publico"
	exit 1
}

PURGE_ALVOS="$TMP/alvos"
PURGE_TODOS="$TMP/todos"
: >"$PURGE_TODOS"
cat >"$PURGE_ALVOS" <<'ALVOS'
/familia/abandono-afetivo-indenizacao/
/familia/pagina/2/
/fontes/stj/
/sobre/
/glossario/
ALVOS
eval "$bloco"

espera() { # $1 = URL que TEM de estar na lista
	if grep -qxF -- "$1" "$PURGE_TODOS"; then
		passo OK "purga $1"
	else
		passo FALHA "falta na purga: $1"
		falhou=1
	fi
}
nao_espera() { # $1 = URL que NAO pode estar na lista
	if grep -qxF -- "$1" "$PURGE_TODOS"; then
		passo FALHA "purga o que nao existe: $1"
		falhou=1
	else passo OK "nao purga $1"; fi
}

espera "/familia/abandono-afetivo-indenizacao/index.md"
# A GEMEA DO HUB DA AREA TOCADA (2026-09-16). O hub lista o que a area tem, muda
# na publicacao que acrescenta pagina a ela, e so o HTML dele era alcancado:
# medido, /jurisprudencia/index.md estava na borda com HIT age 12.730 s e corpo
# diferente do que o Go servia, com o HTML do hub ja fresco.
espera "/familia/index.md"
espera "/fontes/index.md"
nao_espera "/familia/pagina/index.md"
espera "/api/v1/pages/familia/abandono-afetivo-indenizacao/"
espera "/api/v1/citar/familia/abandono-afetivo-indenizacao/"
espera "/sobre/index.md"
nao_espera "/api/v1/pages/sobre/"
nao_espera "/api/v1/citar/sobre/"
nao_espera "/familia/pagina/2/index.md"
nao_espera "/api/v1/pages/familia/pagina/2/"
nao_espera "/fontes/stj/index.md"
nao_espera "/glossario/index.md"
nao_espera "/api/v1/pages/glossario/"

# a lista nao pode ter duplicata: cada URL conta no teto de 30 por lote da API da Cloudflare
dup=$(sort "$PURGE_TODOS" | uniq -d | wc -l)
if [[ "$dup" -eq 0 ]]; then passo OK "sem duplicata na lista"; else
	passo FALHA "$dup URL(s) duplicada(s)"
	falhou=1
fi

exit "$falhou"
