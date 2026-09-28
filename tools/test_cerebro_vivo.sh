#!/usr/bin/env bash
# Prova tools/check-cerebro-vivo nos tres estados.
#
# POR QUE HA CONTROLE POSITIVO SINTETICO AQUI: quando este teste foi escrito, o
# journal retido desta maquina tinha ZERO reinicios em TODAS as units — nao havia
# caso positivo real contra o qual validar o parser. Um teste que so visse o zero
# provaria apenas que a ferramenta sabe imprimir "estavel", e o precedente
# `instrumento-casa-um-produtor` e explicito: controle positivo ANTES do zero.
# Por isso a ferramenta aceita `--journal-de <arquivo>` e o teste alimenta o
# parser com a frase literal que o systemd emite.
#
# ATUALIZADO em 2026-09-16, mais tarde no mesmo dia: o caso positivo real
# APARECEU — 23 reinicios em 24 h, sendo 21 num laco de 9 minutos (12:09 a
# 12:18), por SQLITE_BUSY tratado como fatal. A fixture sintetica FICA, porque
# journal retido nao e' fonte reproduzivel, mas a afirmacao "zero em todas as
# units" deixou de ser verdadeira e nao pode continuar escrita aqui.
#
# SAO DOIS EIXOS, e o teste tem de controlar os dois. `--journal-de` controla o
# NIVEL (quantos reinicios na janela) e `--estavel-ha` controla o FLUXO (ha
# quanto tempo a unit esta de pe). Sem o segundo, a fixture de laco seria julgada
# contra a estabilidade REAL da maquina: em 2026-09-16 a maquina estava estavel ha
# 3,8 h, e o controle positivo desta suite passou a REPROVAR quando o eixo de
# fluxo entrou no gate. Foi este teste que pegou a regressao.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

GATE=${GATE_CEREBRO_VIVO:-./tools/check-cerebro-vivo}
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# A frase e' a que o systemd 252 emite a cada reinicio agendado.
cat >"$TMP/journal-em-laco.txt" <<'EOF'
set 16 04:00:01 debian systemd[1]: wikijuridica-cerebro.service: Main process exited, code=exited, status=1/FAILURE
set 16 04:00:01 debian systemd[1]: wikijuridica-cerebro.service: Failed with result 'exit-code'.
set 16 04:00:16 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 1.
set 16 04:00:31 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 2.
set 16 04:00:46 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 3.
set 16 04:01:01 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 4.
set 16 04:01:16 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 5.
set 16 04:01:31 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 6.
EOF

# Um restart isolado: operacao normal (troca de binario, daemon-reload).
cat >"$TMP/journal-um-restart.txt" <<'EOF'
set 16 04:00:16 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 1.
set 16 04:00:20 debian systemd[1]: Started WikiJuridica — cérebro de IA local.
EOF

cat >"$TMP/journal-tranquilo.txt" <<'EOF'
set 16 08:47:02 debian cerebro[926445]: cerebro: lote extrair_dispositivos x3 modelo=qwen3.5:4b
set 16 08:47:02 debian cerebro[926445]: cerebro: pausa: portal ou ollama fora do health
EOF

echo "== CONTROLE POSITIVO: laco de reinicio TEM de reprovar"
saida=$("$GATE" --journal-de "$TMP/journal-em-laco.txt" --estavel-ha 20 2>&1); rc=$?
if [ "$rc" -eq 1 ] && [[ "$saida" == *"EM LACO"* ]]; then
	passo OK "6 reinicios e de pe ha 20 s -> exit 1 (nivel E fluxo)"
else
	passo FALHA "laco deveria sair 1 (rc=$rc) :: $(echo "$saida" | tail -2 | tr '\n' ' ')"; falhou=1
fi

# O numero tem de aparecer: veredito sem quantidade nao se confere.
if [[ "$saida" == *"restarts na janela de 24h: 6"* ]]; then
	passo OK "a linha diz QUANTOS reinicios contou"
else
	passo FALHA "a saida nao informa a contagem :: $saida"; falhou=1
fi

echo
echo "== CONTROLE NEGATIVO: o que NAO pode ser acusado"
saida=$("$GATE" --journal-de "$TMP/journal-tranquilo.txt" 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then
	passo OK "journal sem reinicio -> exit 0"
else
	passo FALHA "journal tranquilo foi acusado (rc=$rc) :: $saida"; falhou=1
fi

# A folga de operacao e' deliberada: 1 restart nao e' laco.
saida=$("$GATE" --journal-de "$TMP/journal-um-restart.txt" 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then
	passo OK "1 reinicio isolado NAO reprova (folga de operacao sobre o piso medido)"
else
	passo FALHA "1 reinicio nao pode reprovar (rc=$rc) :: $saida"; falhou=1
fi

echo
echo "== REPROVA POR FLUXO, NAO POR NIVEL"
# O acumulado (NRestarts) e' cumulativo e so zera com reset-failed. Se ele
# entrasse no veredito, o gate ficaria vermelho para sempre sem nada que o
# drenasse. Aqui o journal tranquilo passa mesmo com contador alto no texto.
cat >"$TMP/journal-nivel-alto-sem-fluxo.txt" <<'EOF'
set 16 08:00:00 debian systemd[1]: wikijuridica-cerebro.service: Scheduled restart job, restart counter is at 873.
EOF
saida=$("$GATE" --journal-de "$TMP/journal-nivel-alto-sem-fluxo.txt" 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then
	passo OK "contador 873 com UM evento na janela passa: e fluxo que reprova, nao nivel"
else
	passo FALHA "nivel alto nao pode reprovar sozinho (rc=$rc) :: $saida"; falhou=1
fi

echo
echo "== LACO JA CONSERTADO PASSA, E AVISA"
# ESTE CASO EXISTE POR UM FALSO POSITIVO MEDIDO em 2026-09-16: com o veredito
# apoiado so no NIVEL, o gate reprovava as 24 h seguintes a qualquer conserto --
# 23 reinicios na janela com a unit de pe ha 3,8 h saiam como "EM LACO", no
# presente. E vermelho por divida ja paga, que e' o vermelho que se aprende a
# ignorar. O mutante que este caso mata: remover a conjuncao com `estavel_ha`.
saida=$("$GATE" --journal-de "$TMP/journal-em-laco.txt" --estavel-ha 13600 2>&1); rc=$?
if [ "$rc" -eq 0 ] && [[ "$saida" == *"laco ja consertado"* ]]; then
	passo OK "6 reinicios mas de pe ha 3,8 h -> exit 0 com AVISO nomeado"
else
	passo FALHA "laco consertado nao pode reprovar (rc=$rc) :: $(echo "$saida" | head -2 | tr '\n' ' ')"; falhou=1
fi

# O aviso nao pode ser silencioso: quem le a saida tem de ver que houve laco.
if [[ "$saida" == *"23"* || "$saida" == *"Houve 6 reinicios"* ]]; then
	passo OK "o aviso diz quantos reinicios houve"
else
	passo FALHA "o aviso omite a contagem :: $saida"; falhou=1
fi

# E a fronteira tem de ser o parametro, nao um numero escondido no codigo.
saida=$("$GATE" --journal-de "$TMP/journal-em-laco.txt" --estavel-ha 1799 2>&1); rc=$?
if [ "$rc" -eq 1 ]; then
	passo OK "1 s abaixo da fronteira ainda reprova (a fronteira e a declarada)"
else
	passo FALHA "a fronteira de 1800 s nao esta sendo aplicada (rc=$rc)"; falhou=1
fi

echo
echo "== NAO MEDI vale 2, nunca 0 nem 1"
saida=$("$GATE" --journal-de "$TMP/arquivo-que-nao-existe" 2>&1); rc=$?
if [ "$rc" -eq 2 ] && [[ "$saida" == *"NAO MEDIDO:"* ]]; then
	passo OK "journal ilegivel -> exit 2 com a frase-ancora"
else
	passo FALHA "journal ilegivel deveria sair 2 (rc=$rc) :: $saida"; falhou=1
fi

echo
echo "== O DETECTOR NOMEIA O QUE VIGIA"
# check-units-alarme so aceita este arquivo como cobertura do OnFailure
# inalcancavel se ele nomear a unit. Detector que nao nomeia o alvo nao e
# detector -- e por isso a regra esta no gate E aqui.
if grep -q "wikijuridica-cerebro.service" ./tools/check-cerebro-vivo; then
	passo OK "check-cerebro-vivo nomeia wikijuridica-cerebro.service"
else
	passo FALHA "o detector nao nomeia a unit que vigia"; falhou=1
fi

echo
if [ "$falhou" -eq 0 ]; then
	echo "test_cerebro_vivo: OK"
	exit 0
fi
echo "test_cerebro_vivo: REPROVADO"
exit 1
