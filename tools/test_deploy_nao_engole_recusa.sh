#!/usr/bin/env bash
# Prova que o deploy mostra o veredito do gerador de revisao em vez de engoli-lo,
# e que so o RECUSADO deliberado interrompe o deploy.
#
# POR QUE (medido 2026-08-28): `tools/deploy-publico:741` chamava o gerador com
# `> /dev/null 2>&1 || echo AVISO`. A guarda `confere_formula` recusa quando a
# formula do served_sha256 mudou sem ressemeadura -- rodar assim carimbaria a data
# de hoje em TODAS as rotas e reanunciaria o sitemap inteiro ao Googlebot -- e vem
# com dez linhas explicando o remedio. Tudo isso ia para /dev/null.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
# extrai o bloco real do deploy, com o binario do gerador trocado por um duble
bloco=$(sed -n '/^revisao_saida=\$(tools\/generate-page-content-revision/,/^fi$/p' tools/deploy-publico)
[[ -n "$bloco" ]] || {
	echo "FALHA: bloco nao encontrado em deploy-publico"
	exit 1
}

roda() { # $1 = saida do duble, $2 = exit code do duble
	mkdir -p "$TMP/tools"
	printf '#!/usr/bin/env bash\nprintf "%%s\\n" "%s"\nexit %s\n' "$1" "$2" >"$TMP/tools/generate-page-content-revision"
	chmod +x "$TMP/tools/generate-page-content-revision"
	(cd "$TMP" && eval "$bloco") 2>&1
	echo "RC=$?"
}

# ---------- caso 1: RECUSADO deliberado -> mostra o remedio E interrompe
saida=$(roda "RECUSADO: a formula do served_sha256 mudou desde a ultima execucao." 1)
if [[ "$saida" == *"RECUSADO"* ]]; then
	passo OK "o RECUSADO aparece (nao vai para /dev/null)"
else
	passo FALHA "o RECUSADO foi engolido"
	falhou=1
fi
if [[ "$saida" == *"RC=1"* ]]; then
	passo OK "RECUSADO interrompe o deploy"
else
	passo FALHA "RECUSADO nao interrompeu"
	falhou=1
fi

# ---------- FALSO POSITIVO 1: falha transitoria NAO pode abortar o deploy
saida=$(roda "erro: nao consegui abrir o ledger (disco ocupado)" 3)
if [[ "$saida" == *"RC=0"* ]]; then
	passo OK "falso positivo: falha transitoria nao aborta"
else
	passo FALHA "falha transitoria abortou o deploy (largo demais)"
	falhou=1
fi
if [[ "$saida" == *"disco ocupado"* ]]; then
	passo OK "e a causa transitoria tambem aparece"
else
	passo FALHA "causa transitoria engolida"
	falhou=1
fi

# ---------- FALSO POSITIVO 2: sucesso nao pode imprimir aviso nem abortar
saida=$(roda "10117 rota(s) conferidas; 0 data(s) nova(s)" 0)
if [[ "$saida" != *"AVISO"* && "$saida" == *"RC=0"* ]]; then
	passo OK "falso positivo: sucesso passa em silencio"
else
	passo FALHA "sucesso produziu ruido ou aborto: $saida"
	falhou=1
fi

echo
[[ $falhou -eq 0 ]] && echo "deploy nao engole a recusa: sem defeito" || echo "REPROVADO"
exit $falhou
