#!/usr/bin/env bash
# Prova a regra de purga por CAMADA do deploy-publico (2026-09-09): binario novo
# do servidor ou do social purga a lista dinamica (o que o Go serve) e preserva
# o HTML estatico na borda; "tudo" fica para ingress, camada sem registro e
# revisao indisponivel.
#
# POR QUE (medido 2026-09-09): tres purgas totais num dia por "binario mudou
# (ingress intacto)", cada uma jogando fora 1.644 s de reaquecimento de 12.331
# URLs, para mudanca que nao toca public/. A versao anterior desta regra e o
# mutante que o caso 4 apanha.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

FONTE="${DEPLOY_PUBLICO:-tools/deploy-publico}"
bloco=$(sed -n '/^# --- purga por camada: o que um binario novo muda, e so isso ---/,/^# --- fim da purga por camada ---/p' "$FONTE")
[[ -n "$bloco" ]] || {
	echo "FALHA: bloco da purga por camada nao encontrado em $FONTE"
	exit 1
}
eval "$bloco"

espera() { # $1 = rotulo, $2 = obtido, $3 = esperado
	if [[ "$2" == "$3" ]]; then passo OK "$1"; else
		passo FALHA "$1: obtido '$2', esperado '$3'"
		falhou=1
	fi
}

# ---------- modo: quando e "tudo" e quando e "lista"
espera "revisao indisponivel => tudo" "$(modo_de_purga_da_camada '' 0 abc | cut -d: -f1)" "tudo"
espera "camada sem registro anterior => tudo" "$(modo_de_purga_da_camada 12 0 '' | cut -d: -f1)" "tudo"
espera "ingress mudou => tudo" "$(modo_de_purga_da_camada 12 1 abc | cut -d: -f1)" "tudo"
# caso 4: o mutante de ontem (binario mudou, ingress intacto => tudo)
espera "binario mudou com ingress intacto => lista" "$(modo_de_purga_da_camada 12 0 abc)" "lista"
espera "zero alvos e ingress intacto => lista" "$(modo_de_purga_da_camada 0 0 abc)" "lista"

# ---------- lista dinamica: dubles no lugar da rede
rotas_dinamicas_do_servidor() { printf '%s\n' /index.md /familia/index.md /.well-known/agent-card.json /familia/x/index.md; }
# o duble do social tem o TAMANHO do social real (raiz + 120 temas): a guarda e por tamanho
rotas_dinamicas_do_social() {
	echo /redesocial/
	for i in $(seq 1 120); do echo "/redesocial/tema/familia/x$i/"; done
}

espera "nenhum binario mudou => lista vazia" "$(lista_dinamica_da_camada 0 0 | wc -l | tr -d ' ')" "0"
lista=$(lista_dinamica_da_camada 1 0)
espera "so o servidor: 4 rotas" "$(printf '%s\n' "$lista" | wc -l | tr -d ' ')" "4"
espera "so o servidor: indice de area em Markdown entra" "$(printf '%s\n' "$lista" | grep -c '^/familia/index.md$')" "1"
espera "so o servidor: nada de /redesocial/" "$(printf '%s\n' "$lista" | grep -c redesocial)" "0"
lista=$(lista_dinamica_da_camada 0 1)
espera "so o social: raiz + 120 temas" "$(printf '%s\n' "$lista" | grep -c .)" "121"
espera "so o social: a raiz entra" "$(printf '%s\n' "$lista" | grep -c '^/redesocial/$')" "1"
lista=$(lista_dinamica_da_camada 1 1)
espera "os dois: 4 + 121 rotas" "$(printf '%s\n' "$lista" | grep -c .)" "125"
espera "HTML estatico de pagina nunca entra" "$(printf '%s\n' "$lista" | grep -c '^/familia/x/$')" "0"

# ---------- social de verdade: indice -> shard, temas do banco, guarda por tamanho
eval "$bloco" # devolve as funcoes reais; so as de baixo nivel ganham duble
baixa_sitemap_social() {
	case "$1" in
	/redesocial/sitemap.xml) printf '<sitemapindex><sitemap><loc>https://wikijuridica.com.br/redesocial/sitemap/superficie.xml</loc></sitemap></sitemapindex>\n' ;;
	/redesocial/sitemap/superficie.xml) for i in $(seq 1 12); do printf '<url><loc>https://wikijuridica.com.br/redesocial/s%s/</loc></url>\n' "$i"; done ;;
	*) return 22 ;;
	esac
}
temas_do_social() { for i in $(seq 1 150); do echo "/redesocial/tema/familia/t$i/"; done; }
lista=$(lista_dinamica_da_camada 0 1)
espera "social real: raiz + 12 de superficie + 150 temas, sem duplicata" "$(printf '%s\n' "$lista" | grep -c .)" "163"
espera "social real: raiz uma vez so" "$(printf '%s\n' "$lista" | grep -c '^/redesocial/$')" "1"
espera "social real: segue o indice ate o shard (nao purga o .xml como pagina)" "$(printf '%s\n' "$lista" | grep -c '\.xml$')" "0"
espera "social real: tema do banco entra" "$(printf '%s\n' "$lista" | grep -c '^/redesocial/tema/familia/t150/$')" "1"
temas_do_social() { echo "/redesocial/tema/familia/t1/"; }
if lista_dinamica_da_camada 0 1 >/dev/null 2>&1; then
	passo FALHA "1 tema so passou em silencio (sub-purga)"
	falhou=1
else passo OK "temas de menos (banco vazio/ilegivel) => exit 1"; fi
temas_do_social() { for i in $(seq 1 150); do echo "/redesocial/tema/familia/t$i/"; done; }
baixa_sitemap_social() { printf '<sitemapindex><sitemap><loc>https://wikijuridica.com.br/redesocial/sitemap/superficie.xml</loc></sitemap></sitemapindex>\n'; }
if lista_dinamica_da_camada 0 1 >/dev/null 2>&1; then
	passo FALHA "indice sem shard legivel passou em silencio"
	falhou=1
else passo OK "so o indice (shard ilegivel) => exit 1"; fi

# lister vazio = falha, nunca lista curta em silencio
rotas_dinamicas_do_servidor() { :; }
if lista_dinamica_da_camada 1 0 >/dev/null 2>&1; then
	passo FALHA "lister do servidor vazio passou em silencio"
	falhou=1
else passo OK "lister do servidor vazio => exit 1"; fi
rotas_dinamicas_do_social() {
	echo "/redesocial/"
	for i in $(seq 1 20); do echo "/redesocial/tema/x$i/"; done
}
if lista_dinamica_da_camada 0 1 >/dev/null 2>&1; then
	passo FALHA "social com 21 rotas passou em silencio"
	falhou=1
else passo OK "social curto demais (21 rotas) => exit 1"; fi

exit "$falhou"
