#!/usr/bin/env bash
# Prova que o alerta da onda diaria carrega o VEREDITO do gate, nao o nome dele.
#
# POR QUE ESTE TESTE EXISTE (medido em 2026-08-28): a onda reprovou em
# check-lastmod-causalidade e o alerta que chegou ao desktop dizia apenas
# "Falhou em: check-lastmod-causalidade". O achado real -- 10.102 rotas
# afirmando revisao de advogado que nao ocorreu -- ficou no log. Alerta que nao
# carrega o achado nao e alarme, e sumario.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
# AS TRES VARIAVEIS ABAIXO SAO LIDAS — pelas funcoes que a linha seguinte
# carrega com `eval`. O shellcheck nao consegue ver isso e nunca vai conseguir:
# `vereditoDe` e `montaMensagemFalha` entram por
# `eval "$(sed -n '/^vereditoDe()/,/^}/p;...' tools/run-daily-content)"`, um
# recorte por faixa de linha do fonte de producao. As funcoes leem `LOGS_COLETA`
# (onde estao os logs dos gates), `HOJE` (a data da onda) e o array `falhas`
# (quais gates reprovaram) como globais.
#
# A diretiva vai SOZINHA na linha: com texto depois do codigo o shellcheck
# recusa a diretiva inteira com SC1125 e o aviso continua ligado — foi o que
# aconteceu em tools/run-daily-content e so apareceu hoje.
# shellcheck disable=SC2034
LOGS_COLETA="$TMP"
# shellcheck disable=SC2034
HOJE="2026-08-28"
# shellcheck disable=SC2034
falhas=()

# carrega SO as duas funcoes, sem executar a onda
eval "$(sed -n '/^vereditoDe()/,/^}/p;/^montaMensagemFalha()/,/^}/p' tools/run-daily-content)"

# ---------- caso 1: gate com linha REPROVADO -> o veredito viaja
cat >"$TMP/check-lastmod-causalidade.log" <<'LOG'
conferindo 10331 rotas
REPROVADO: reviewed_at avancou em 10102 rota(s) sem o conteudo mudar — a pagina afirma revisao de advogado que nao ocorreu.
LOG
saida=$(vereditoDe check-lastmod-causalidade)
if [[ "$saida" == *"10102 rota"* ]]; then
	passo OK "veredito viaja para o alerta"
else
	passo FALHA "veredito NAO viajou: $saida"
	falhou=1
fi

# ---------- caso 2: o alerta NAO pode ser so o nome do gate (o defeito medido)
if [[ "$saida" != "check-lastmod-causalidade" ]]; then
	passo OK "alerta nao e so o nome do gate"
else
	passo FALHA "alerta degenerou para o nome do gate"
	falhou=1
fi

# ---------- caso 3: a frase falsa nao volta
falhas=(check-lastmod-causalidade)
msg=$(montaMensagemFalha)
if [[ "$msg" != *"etapas seguintes nao rodaram"* ]]; then
	passo OK "sem a frase falsa sobre etapas"
else
	passo FALHA "a frase falsa voltou"
	falhou=1
fi
if [[ "$msg" == *"10102 rota"* ]]; then
	passo OK "mensagem final carrega o achado"
else
	passo FALHA "mensagem final sem o achado: $msg"
	falhou=1
fi

# ---------- FALSO POSITIVO 1: gate sem log nao pode quebrar o trap nem sumir
falhas=(gate-sem-log)
msg=$(montaMensagemFalha) || {
	passo FALHA "montaMensagemFalha quebrou com log ausente"
	falhou=1
}
if [[ "$msg" == *"gate-sem-log"* ]]; then
	passo OK "gate sem log ainda aparece no alerta"
else
	passo FALHA "gate sem log SUMIU do alerta: $msg"
	falhou=1
fi

# ---------- FALSO POSITIVO 2: log gigante nao pode despejar tudo no notify-send
python3 -c "open('$TMP/gate-tagarela.log','w').write('REPROVADO: '+'x'*5000)"
saida=$(vereditoDe gate-tagarela)
if [[ ${#saida} -le 200 ]]; then
	passo OK "veredito truncado (${#saida} chars)"
else
	passo FALHA "veredito de ${#saida} chars estouraria o notify-send"
	falhou=1
fi

# ---------- FALSO POSITIVO 3: log sem linha REPROVADO usa a primeira linha util
printf '\n\n   diagnostico solto sem palavra-chave\n' >"$TMP/gate-mudo.log"
saida=$(vereditoDe gate-mudo)
if [[ "$saida" == *"diagnostico solto"* ]]; then
	passo OK "cai na primeira linha util"
else
	passo FALHA "nao achou a primeira linha util: $saida"
	falhou=1
fi

# ---------- FALSO POSITIVO 4: exit code do trap nao pode ser alterado
(exit 7)
guardado=$?
# Lida por montaMensagemFalha, que entra por eval — ver a nota do topo.
# shellcheck disable=SC2034
falhas=(check-lastmod-causalidade)
montaMensagemFalha >/dev/null
if [[ $guardado -eq 7 ]]; then
	passo OK "exit code preservado"
else
	passo FALHA "exit code corrompido"
	falhou=1
fi

echo
[[ $falhou -eq 0 ]] && echo "alerta carrega veredito: sem defeito" || echo "REPROVADO"
exit $falhou
