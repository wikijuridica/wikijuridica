#!/usr/bin/env bash
# Prova tools/aguardar-fim-de-deploy nos TRES estados do lock, e fixa a
# constante de 1800 s contra os cinco lugares que a escrevem a mao.
#
# NUNCA toca data/ops/.deploy-em-curso.lock de verdade: criar aquele arquivo
# calaria check-portal-health, check-producao-saudavel e o http_smoke da rede
# social por 30 minutos. Todo lock aqui e' de mentira, numa raiz temporaria.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

WRAPPER=${WRAPPER_AGUARDAR:-./tools/aguardar-fim-de-deploy}
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
LOCK="$TMP/.deploy-em-curso.lock"

# Passo curto: o teste mede COMPORTAMENTO, nao paciencia.
export AGUARDAR_LOCK="$LOCK" AGUARDAR_PASSO_S=1

echo "== OS TRES ESTADOS DO LOCK"

# ---------- 1. SEM LOCK: executa na hora.
rm -f "$LOCK"
saida=$(AGUARDAR_TETO_ESPERA_S=5 "$WRAPPER" /bin/echo EXECUTOU 2>&1); rc=$?
if [ "$rc" -eq 0 ] && [[ "$saida" == *EXECUTOU* ]]; then
	passo OK "sem lock: executa o comando (rc=0)"
else
	passo FALHA "sem lock deveria executar (rc=$rc) :: $saida"; falhou=1
fi

# ---------- 2. LOCK ORFAO: o comando roda assim mesmo.
# Um deploy interrompido nao pode adiar o restart para sempre — sem esta regra,
# um lock esquecido deixaria o servidor com indice velho ate alguem notar.
: >"$LOCK"
touch -d "@$(( $(date +%s) - 3600 ))" "$LOCK"   # 60 min > janela de 30
saida=$(AGUARDAR_TETO_ESPERA_S=5 "$WRAPPER" /bin/echo EXECUTOU 2>&1); rc=$?
if [ "$rc" -eq 0 ] && [[ "$saida" == *EXECUTOU* && "$saida" == *ORFAO* ]]; then
	passo OK "lock orfao (60 min): executa e diz que o lock era orfao"
else
	passo FALHA "lock orfao deveria executar (rc=$rc) :: $saida"; falhou=1
fi

# ---------- 3. LOCK FRESCO: NAO executa, espera e estoura o teto com 2.
# Este e o caso que protege a transacao: o restart e adiado, nunca pulado.
#
# A prova e por EFEITO COLATERAL, e nao por texto na saida. A primeira versao
# procurava a ausencia da palavra "EXECUTOU" e dava FALSO NEGATIVO: o wrapper
# ecoa o comando que esta adiando ("adiando `/bin/echo EXECUTOU`"), entao a
# palavra aparecia na saida justamente no caso em que o comando NAO rodou.
# Um arquivo que so existe se o comando executou nao tem como ser ambiguo.
: >"$LOCK"
PROVA="$TMP/executou-3"
rm -f "$PROVA"
saida=$(AGUARDAR_TETO_ESPERA_S=2 "$WRAPPER" /usr/bin/touch "$PROVA" 2>&1); rc=$?
if [ "$rc" -eq 2 ] && [ ! -e "$PROVA" ]; then
	passo OK "lock fresco: NAO executa, espera e sai 2 no teto"
else
	passo FALHA "lock fresco deveria adiar e sair 2 (rc=$rc) :: $saida"; falhou=1
fi

# ---------- 3b. o exit 2 do teto TEM de ser 2, e nao 1.
# 1 e' o codigo de veredito, e ha units que o mascaram. Se este numero virar 1,
# o estouro de espera passa a ser engolido como "sucesso" em qualquer unit que
# mascare — que e' a familia de defeitos que esta frente inteira corrige.
if [[ "$saida" == *"NAO MEDIDO:"* ]]; then
	passo OK "teto estourado carrega a frase-ancora NAO MEDIDO"
else
	passo FALHA "teto estourado sem a frase-ancora :: $saida"; falhou=1
fi

# ---------- 4. LOCK QUE E' LIBERADO NO MEIO DA ESPERA: executa depois.
# E' o caso REAL: o deploy termina, o trap apaga o lock, e o restart represado
# acontece em seguida. Sem isto o teste so provaria os extremos.
: >"$LOCK"
( sleep 2; rm -f "$LOCK" ) &
liberador=$!
saida=$(AGUARDAR_TETO_ESPERA_S=30 "$WRAPPER" /bin/echo EXECUTOU 2>&1); rc=$?
wait "$liberador" 2>/dev/null
if [ "$rc" -eq 0 ] && [[ "$saida" == *EXECUTOU* && "$saida" == *"lock liberado"* ]]; then
	passo OK "lock liberado no meio: espera e ENTAO executa (restart adiado, nao perdido)"
else
	passo FALHA "deveria esperar e executar (rc=$rc) :: $saida"; falhou=1
fi

echo
echo "== A CONSTANTE MORA NUM LUGAR SO"

# A janela de orfao esta escrita a mao em CINCO leitores que nao podem ser
# reescritos (um deles e Go no caminho de serving). O que impede a deriva e'
# esta asserção: o dia em que um deles mudar sozinho, isto fica vermelho.
# shellcheck disable=SC1091
. ./tools/lib/deploy_lock.env
esperado="$DEPLOY_LOCK_JANELA_ORFAO_S"

verifica_literal() {
	local arquivo="$1" descricao="$2"
	if [ ! -f "$arquivo" ]; then
		passo FALHA "$descricao: $arquivo nao existe"; falhou=1; return
	fi
	if grep -qE "(^|[^0-9])${esperado}([^0-9]|$)" "$arquivo"; then
		passo OK "$descricao usa $esperado"
	else
		passo FALHA "$descricao NAO tem mais o literal $esperado — a constante divergiu de tools/lib/deploy_lock.env"
		falhou=1
	fi
}

verifica_literal tools/check-portal-health          "check-portal-health (janela de manutencao)"
verifica_literal tools/check-producao-saudavel      "check-producao-saudavel (JANELA_DE_DEPLOY)"

# O 5o leitor e Go e escreve a MESMA janela em MINUTOS (`30 * time.Minute`), que
# e a forma legivel na linguagem dele. Exigir o literal em segundos ali seria o
# teste mandando o codigo piorar para satisfazer a asserção. O que se verifica e
# a EQUIVALENCIA: 1800 s / 60 = 30 min.
esperado_min=$(( esperado / 60 ))
if grep -qE "${esperado_min} \* time\.Minute" internal/checks/http_smoke_redesocial.go; then
	passo OK "http_smoke_redesocial.go (o 5o leitor) usa ${esperado_min} * time.Minute = ${esperado}s"
else
	passo FALHA "http_smoke_redesocial.go nao tem mais ${esperado_min} * time.Minute — divergiu de tools/lib/deploy_lock.env"
	falhou=1
fi

# E o caminho do lock tem de ser o mesmo nos cinco.
for arquivo in tools/deploy-publico tools/deploy-binario-go tools/check-portal-health \
               tools/check-producao-saudavel internal/checks/http_smoke_redesocial.go; do
	if grep -q "$DEPLOY_LOCK_CAMINHO" "$arquivo" 2>/dev/null; then
		passo OK "$(basename "$arquivo") aponta para $DEPLOY_LOCK_CAMINHO"
	else
		passo FALHA "$(basename "$arquivo") nao menciona $DEPLOY_LOCK_CAMINHO"; falhou=1
	fi
done

echo
if [ "$falhou" -eq 0 ]; then
	echo "test_aguardar_fim_de_deploy: OK"
	exit 0
fi
echo "test_aguardar_fim_de_deploy: REPROVADO"
exit 1
