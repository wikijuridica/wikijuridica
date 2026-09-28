#!/usr/bin/env bash
# Prova que check-nginx-standalone-parity pega divergencia de cabecalho NOS DOIS
# sentidos -- inclusive linha que sobra so no arquivo que a unit carrega.
#
# POR QUE (2026-08-28): o gate era subset de mao unica. Removi
# `more_set_headers 'Vary: Accept-Encoding'` do @fallback do arquivo DORMENTE em
# vez do vivo, o gate disse `pass`, e a resposta real continuou saindo com o Vary
# incompleto. Um gate que so olha um lado nao e paridade, e meia paridade.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

# ESTE TESTE EDITA CONFIG DE PRODUCAO IN-PLACE, e desde 2026-09-05 ele roda
# TODO DIA na qualidade-diaria (passo 2c-bis, com teto de 600 s). Restaurar so
# no caminho feliz nao serve mais: morto pelo timeout no meio de um check, o
# nginx dedicado ficaria com a diretiva injetada no disco, e um `git add
# ops/nginx/standalone/nginx.conf` de outra sessao nessa janela commitaria o
# mutante. A restauracao passa a ser do trap EXIT, que roda em qualquer saida.
restaura_e_limpa() {
	if [[ -f "$TMP/ded.conf" ]] &&
		! diff -q "$TMP/ded.conf" ops/nginx/standalone/nginx.conf >/dev/null 2>&1; then
		cp "$TMP/ded.conf" ops/nginx/standalone/nginx.conf
		printf '  !! saida sem restauro: repus ops/nginx/standalone/nginx.conf da copia do teste\n' >&2
	fi
	rm -rf "$TMP"
}
TMP=$(mktemp -d)
trap restaura_e_limpa EXIT
cp ops/nginx/wikijuridica.conf "$TMP/vivo.conf"
cp ops/nginx/standalone/nginx.conf "$TMP/ded.conf"
cp ops/nginx/security-headers.conf "$TMP/"

# ---------- controle: como esta hoje, passa
./tools/check-nginx-standalone-parity >/dev/null 2>&1
[[ $? -eq 0 ]] && passo OK "controle: estado atual passa" || {
	passo FALHA "controle ja reprova"
	falhou=1
}

# ---------- injeta cabecalho SO no dedicado (o caso que passava batido)
python3 - "$TMP" <<'PY'
import sys, pathlib, shutil, os
tmp = pathlib.Path(sys.argv[1])
alvo = pathlib.Path("ops/nginx/standalone/nginx.conf")
shutil.copy2(alvo, tmp / "ded.backup")
s = alvo.read_text(encoding="utf-8")
i = s.index("location @fallback")
j = s.index("proxy_pass", i)
s = s[:j] + "more_set_headers -s '200 304' 'Vary: Accept-Encoding';\n        " + s[j:]
alvo.write_text(s, encoding="utf-8")
PY
./tools/check-nginx-standalone-parity >"$TMP/saida" 2>&1
rc=$?
python3 -c "
import pathlib, shutil, sys
shutil.copy2('$TMP/ded.backup', 'ops/nginx/standalone/nginx.conf')
"
if [[ $rc -ne 0 ]] && grep -q 'SO no nginx dedicado' "$TMP/saida"; then
	passo OK "pega cabecalho que sobra so no dedicado (o meu erro de hoje)"
else
	passo FALHA "NAO pegou o cabecalho extra (rc=$rc)"
	sed 's/^/      /' "$TMP/saida" | head -4
	falhou=1
fi

# ---------- SEGUNDO CRITERIO: diretiva a mais no dedicado reprova pela GUARDA DE
# PERDA, e nao como cabecalho sobrando. Reescrito em 2026-09-09.
#
# Ate 4b3e080e este caso exigia exit 0: o unico criterio do gate era comparar
# CABECALHOS de resposta, e `proxy_read_timeout` nao e cabecalho. O commit
# acrescentou o segundo criterio -- `linhas_perdidas_na_regeracao()`, que compara
# TODA linha nao-comentario do dedicado com o que o gerador produziria hoje --,
# e sob ele a diretiva injetada a mao passa a reprovar CORRETAMENTE: ela sumiria
# na proxima regeracao, que e a classe de defeito que apagou producao em
# silencio e motivou o criterio.
#
# O teste continuava exigindo exit 0 e ficou vermelho na bancada diaria desde
# 2026-09-08 acusando o gate certo. Agora ele afirma a regra real: a diretiva
# reprova, e reprova PELO MOTIVO CERTO -- a mensagem tem de ser a da guarda de
# perda, nunca a de cabecalho sem declaracao. Assim o teste ainda pega o falso
# positivo que ele nasceu para pegar (o criterio de cabecalho acusando o que nao
# e cabecalho), sem exigir que o gate ignore uma perda real.
# O backup vai para $TMP e nao para um /tmp/ded.backup2 fixo: nome fixo faz duas
# execucoes concorrentes se atropelarem, e a que terminar por ultimo repoe no
# disco o arquivo que a outra ja tinha mutado.
python3 - "$TMP" <<'PY'
import sys, pathlib, shutil
tmp = pathlib.Path(sys.argv[1])
alvo = pathlib.Path("ops/nginx/standalone/nginx.conf")
shutil.copy2(alvo, tmp / "ded.backup2")
s = alvo.read_text(encoding="utf-8")
i = s.index("location @fallback")
j = s.index("proxy_pass", i)
s = s[:j] + "proxy_read_timeout 42s;\n        " + s[j:]
alvo.write_text(s, encoding="utf-8")
PY
./tools/check-nginx-standalone-parity >"$TMP/saida2" 2>&1
rc2=$?
cp "$TMP/ded.backup2" ops/nginx/standalone/nginx.conf
if [[ $rc2 -eq 0 ]]; then
	passo FALHA "diretiva injetada a mao no dedicado passou: a guarda de perda nao viu que ela sumiria na regeracao"
	falhou=1
elif grep -q "SUMIRIAM se o gerador rodasse agora" "$TMP/saida2" && grep -q "proxy_read_timeout 42s" "$TMP/saida2"; then
	passo OK "diretiva so no dedicado reprova pela guarda de perda, nomeando a linha"
elif grep -q "EXTRAS_DE_CABECALHO_AUTORIZADOS" "$TMP/saida2"; then
	passo FALHA "reprovou pelo criterio de CABECALHO uma linha que nao e cabecalho (falso positivo original)"
	falhou=1
else
	passo FALHA "reprovou por motivo inesperado: $(head -3 "$TMP/saida2" | tr '\n' ' ')"
	falhou=1
fi

# ---------- restaurou tudo?
if diff -q "$TMP/ded.conf" ops/nginx/standalone/nginx.conf >/dev/null; then
	passo OK "arquivo restaurado ao estado original"
else
	passo FALHA "o teste deixou o vhost alterado — RESTAURE A MAO"
	falhou=1
fi

echo
[[ $falhou -eq 0 ]] && echo "paridade bidirecional: sem defeito" || echo "REPROVADO"
exit $falhou
