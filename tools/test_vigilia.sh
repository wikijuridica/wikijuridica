#!/usr/bin/env bash
# test_vigilia.sh — bancada funcional do tools/vigilia, na sessão X real.
#
# Testa o que quebra na prática: ida e volta dos tempos do X, idempotência do
# `on` (que já apagou baseline em ferramenta parecida), recuperação quando o
# baseline vem corrompido, e o contrato de saída do genmon que o painel lê.
#
# É seguro rodar com o dono na máquina: nada aqui apaga a tela nem suspende. O
# teste devolve o estado ao valor que encontrou, inclusive se falhar no meio.

set -uo pipefail

VIG="$(dirname "$(readlink -f "$0")")/vigilia"
# A bancada toma o lock da execução inteira (abaixo) e diz ao `vigilia` para não
# tentar tomá-lo de novo: senão cada uma das dezenas de chamadas esperaria 10 s.
export VIGILIA_SEM_LOCK=1
[ -n "${DISPLAY:-}" ] || export DISPLAY=:0
ESTADO_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vigilia"
BASE="$ESTADO_DIR/baseline"

falhas=0
ok() { printf 'ok    %s\n' "$*"; }
falha() {
	printf 'FALHA %s\n' "$*"
	falhas=$((falhas + 1))
}

campo() { xset q 2>/dev/null | awk -v pat="$1" -v col="$2" '$0 ~ pat {print $col; exit}'; }
blank() { xset q 2>/dev/null | grep -q 'prefer blanking:  yes' && echo blank || echo noblank; }
snap() { printf '%s|%s|%s|%s|%s' "$(campo 'timeout:' 2)" "$(campo 'timeout:' 4)" \
	"$(campo 'Standby:' 2)" "$(campo 'Standby:' 4)" "$(campo 'Standby:' 6)"; }
xfpm() { xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled 2>/dev/null; }

xset q >/dev/null 2>&1 || {
	echo "sem X em DISPLAY=$DISPLAY — bancada exige sessão gráfica"
	exit 3
}

# EXCLUSIVIDADE. A bancada muda os tempos do X e o baseline do dono, e esta
# máquina tem outros escritores do mesmo estado: o `caffeine` (que roda
# `xset s off` em tela cheia), o botão do painel e — medido em 2026-09-10 —
# outra sessão de agente rodando ESTA bancada ao mesmo tempo. Duas bancadas
# concorrentes produziram quatro falhas espúrias (baseline apagado por uma
# enquanto a outra o lia) e deixaram o monitor apagado. O lock é o MESMO do
# `vigilia`, então a bancada e os cliques do painel se serializam.
mkdir -p "$ESTADO_DIR"
exec 9>"$ESTADO_DIR/lock"
if command -v flock >/dev/null 2>&1; then
	flock -n 9 || {
		echo "outra bancada ou um clique do painel está escrevendo agora (lock em $ESTADO_DIR/lock)."
		echo "rodar em paralelo dá falha espúria: espere terminar e rode de novo."
		exit 4
	}
fi
if pgrep -x caffeine >/dev/null 2>&1; then
	echo "aviso: caffeine vivo (PID $(pgrep -x caffeine | head -1)); ele roda 'xset s off' em tela cheia."
	echo "       se algum vídeo estiver em tela cheia agora, feche antes: ele disputa os tempos do X."
fi

ESTADO="$ESTADO_DIR/estado"
ANTES_X=$(snap)
ANTES_XFPM=$(xfpm)
BASE_BACKUP=""
EST_BACKUP=""
[ -s "$BASE" ] && BASE_BACKUP=$(cat "$BASE")
# A escolha do dono (`estado`) entra no MESMO trap que o X. Sem isso a bancada
# devolvia o X em vigília e o arquivo em `off`: divergência que o próprio
# `status` acusa como "provável caffeine" — alarme falso plantado pelo teste.
[ -s "$ESTADO" ] && EST_BACKUP=$(cat "$ESTADO")

ANTES_BLANK=$(blank)
restaurar() {
	IFS='|' read -r t c s u o <<<"$ANTES_X"
	xset s "$t" "$c"
	xset s "$ANTES_BLANK"
	xset +dpms
	xset dpms "$s" "$u" "$o"
	[ -n "$ANTES_XFPM" ] && xfconf-query -c xfce4-power-manager \
		-p /xfce4-power-manager/dpms-enabled -n -t bool -s "$ANTES_XFPM" 2>/dev/null
	if [ -n "$BASE_BACKUP" ]; then printf '%s\n' "$BASE_BACKUP" >"$BASE"; else rm -f "$BASE"; fi
	if [ -n "$EST_BACKUP" ]; then printf '%s\n' "$EST_BACKUP" >"$ESTADO"; else rm -f "$ESTADO"; fi
}
trap restaurar EXIT INT TERM

echo "== estado de partida: $ANTES_X  xfpm=$ANTES_XFPM"

# 1. on desliga o screensaver, zera Suspend/Off e arma o Standby no teto
"$VIG" on >/dev/null
[ "$(snap)" = "0|600|65535|0|0" ] && ok "on deixa 0|600|65535|0|0 (screensaver off, Standby armado)" ||
	falha "on deixou $(snap), esperado 0|600|65535|0|0"
[ "$(xfpm)" = false ] && ok "on põe xfce4-power-manager/dpms-enabled=false" ||
	falha "xfpm dpms-enabled=$(xfpm), esperado false"

# 2. DPMS segue HABILITADO E ARMADO — com Standby=0 o `force off` vira noop e o
#    botão "apagar a tela" não funcionaria (medido 2026-09-10).
xset q | grep -q 'DPMS is Enabled' && ok "DPMS continua habilitado" ||
	falha "DPMS foi desabilitado: 'vigilia tela' não funcionaria"
[ "$(campo 'Standby:' 2)" != "0" ] && ok "Standby armado: 'vigilia tela' consegue apagar sob demanda" ||
	falha "Standby=0 desarma o force off"

# 3. on repetido não sobrescreve o baseline com zeros
"$VIG" on >/dev/null
grep -q '^DPMS_OFF=1500' "$BASE" && ok "on idempotente: baseline preserva DPMS_OFF=1500" ||
	falha "segundo on corrompeu o baseline: $(tr '\n' ' ' <"$BASE")"

# 4. off devolve exatamente os valores do baseline
"$VIG" off >/dev/null
[ "$(snap)" = "600|600|900|0|1500" ] && ok "off restaura 600|600|900|0|1500" ||
	falha "off deixou $(snap), esperado 600|600|900|0|1500"
[ "$(xfpm)" = true ] && ok "off devolve o DPMS ao xfce4-power-manager" ||
	falha "xfpm dpms-enabled=$(xfpm), esperado true"

# 5. baseline corrompido com zeros cai nos valores de fábrica, não em zero
"$VIG" on >/dev/null
printf 'S_TIMEOUT=0\nS_CYCLE=0\nDPMS_STANDBY=0\nDPMS_SUSPEND=0\nDPMS_OFF=0\nXFPM_DPMS=lixo\n' >"$BASE"
"$VIG" off >/dev/null
[ "$(snap)" = "600|600|900|0|1500" ] && ok "baseline zerado cai na fábrica 600|600|900|0|1500" ||
	falha "com baseline zerado sobrou $(snap)"
[ "$(xfpm)" = true ] && ok "XFPM_DPMS inválido cai em true" || falha "xfpm=$(xfpm), esperado true"

# 6. contrato de saída do genmon (o painel só entende estas tags)
saida=$("$VIG" genmon)
grep -q '<txt>' <<<"$saida" && ok "genmon emite <txt>" || falha "genmon sem <txt>"
grep -q '<tool>' <<<"$saida" && ok "genmon emite <tool>" || falha "genmon sem <tool>"
grep -q '<txtclick>' <<<"$saida" && ok "genmon emite <txtclick>" || falha "genmon sem <txtclick>"
grep -q 'toggle</txtclick>' <<<"$saida" && ok "clique do painel chama 'toggle'" ||
	falha "genmon não liga o clique ao toggle"

# 7. guardas anti-suspensão: read-only, exit 0 só com as quatro camadas de pé
"$VIG" guardas >/dev/null 2>&1 && ok "guardas: as quatro camadas anti-suspensão de pé" ||
	falha "guardas reprovou — a máquina pode dormir; rode 'vigilia guardas'"

# 8. status não altera nada
antes=$(snap)
"$VIG" status >/dev/null
[ "$(snap)" = "$antes" ] &&
	ok "status é read-only" || falha "status alterou o X"

# 9. REGRESSÃO 2026-09-10: `on` com o X já sem apagamento (caffeine, ou xset na
#    mão) e SEM baseline gravava zeros como baseline. O `off` devolvia
#    dpms-enabled=false e o xfce4-power-manager ficava fora do jogo para sempre.
rm -f "$BASE"
# X ja com a assinatura completa da vigilia (o caso "o dono clicou duas vezes em
# sessoes diferentes"): a captura tem de cair na fabrica, nao gravar a si mesma.
xset s off
xset +dpms
xset dpms 65535 0 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled -n -t bool -s false 2>/dev/null
"$VIG" on >/dev/null
grep -q '^DPMS_OFF=1500' "$BASE" && ok "on sobre X sem apagamento grava baseline de fábrica" ||
	falha "baseline virou $(tr '\n' ' ' <"$BASE")"
"$VIG" off >/dev/null
[ "$(snap)" = "600|600|900|0|1500" ] && ok "off recupera os tempos de fábrica nesse caso" ||
	falha "off deixou $(snap)"
[ "$(xfpm)" = true ] && ok "off devolve o DPMS ao power-manager nesse caso" ||
	falha "xfpm ficou $(xfpm), esperado true"

# 10. `aplicar` (o que o autostart chama) reaplica so quando o dono escolheu on
echo off >"$ESTADO"
xset s 600 600
xset +dpms
xset dpms 900 0 1500
"$VIG" aplicar >/dev/null
[ "$(snap)" = "600|600|900|0|1500" ] && ok "aplicar com escolha=off nao toca em nada" ||
	falha "aplicar mexeu no X com a vigília desligada: $(snap)"
echo on >"$ESTADO"
"$VIG" aplicar >/dev/null
[ "$(snap)" = "0|600|65535|0|0" ] && ok "aplicar com escolha=on reaplica a vigília (caminho do autostart)" ||
	falha "aplicar deixou $(snap), esperado 0|600|65535|0|0"

# 10b. REGRESSÃO 2026-09-10: baseline com campo VAZIO (o que o `on` contra um X
#      sem extensão DPMS gravou) fazia o `off` passar string vazia ao `xset`,
#      que aceitava calado e não restaurava nada.
"$VIG" on >/dev/null
printf 'S_TIMEOUT=600\nS_CYCLE=600\nDPMS_STANDBY=\nDPMS_SUSPEND=\nDPMS_OFF=\nXFPM_DPMS=false\n' >"$BASE"
"$VIG" off >/dev/null
[ "$(snap)" = "600|600|900|0|1500" ] && ok "baseline com campo vazio cai na fábrica inteira" ||
	falha "com baseline vazio sobrou $(snap)"
[ "$(xfpm)" = true ] && ok "baseline inválido devolve o DPMS ao power-manager" ||
	falha "xfpm ficou $(xfpm), esperado true"

# 11. REGRESSÃO 2026-09-10: num X sem a extensão DPMS (os Xvfb do waydroid e dos
#     testes), `on` escrevia dpms-enabled=false no xfconf REAL, o `xset dpms`
#     falhava com "unknown option 65535" e o comando ainda saía com 0.
if xdpyinfo -display :99 >/dev/null 2>&1; then
	xfpm_antes=$(xfpm)
	saida_99=$(DISPLAY=:99 "$VIG" on 2>&1)
	rc_99=$?
	[ "$rc_99" = 4 ] && ok "on num X sem DPMS recusa com exit 4" ||
		falha "on em DISPLAY=:99 saiu $rc_99, esperado 4"
	[ "$(xfpm)" = "$xfpm_antes" ] && ok "recusa não toca no xfconf da sessão real" ||
		falha "xfconf foi alterado por um DISPLAY sem DPMS"
	grep -q 'unknown option' <<<"$saida_99" && falha "xset ainda foi chamado: $saida_99" ||
		ok "recusa acontece ANTES de chamar xset"
else
	echo "aviso sem X em :99 nesta execução: regressão do X sem DPMS não exercitada"
fi

# 12. o .desktop do autostart e o do lançador precisam ser validos para o XFCE
if command -v desktop-file-validate >/dev/null 2>&1; then
	for d in "$HOME/.config/autostart/vigilia.desktop" \
		"$HOME/.local/share/applications/vigilia-apagar-tela.desktop"; do
		if desktop-file-validate "$d" >/dev/null 2>&1; then
			ok "desktop válido: $(basename "$d")"
		else falha "desktop inválido: $d — $(desktop-file-validate "$d" 2>&1 | head -1)"; fi
	done
else
	echo "aviso desktop-file-validate ausente: validade dos .desktop não conferida"
fi

# 13. clique duplo no painel: dois toggles em paralelo nao podem gravar baseline
#     de vigilia como se fosse o do dono (o lock serializa quem escreve).
"$VIG" off >/dev/null
"$VIG" toggle >/dev/null 2>&1 &
p1=$!
"$VIG" toggle >/dev/null 2>&1 &
p2=$!
wait "$p1" "$p2"
grep -q '^DPMS_OFF=1500' "$BASE" && ok "dois toggles concorrentes preservam o baseline do dono" ||
	falha "corrida de toggle corrompeu o baseline: $(tr '\n' ' ' <"$BASE")"
case "$(snap)" in
"0|600|65535|0|0" | "600|600|900|0|1500") ok "estado final da corrida é um dos dois válidos: $(snap)" ;;
*) falha "corrida deixou estado hibrido: $(snap)" ;;
esac

# 13b. REGRESSAO 2026-09-10: `xset -dpms` de terceiro. Com o DPMS desabilitado a
#      tela tambem nao apaga sozinha, entao isso e vigilia — mas Standby de
#      fabrica (900 s) com Off=0 APAGA o painel e nao pode contar como vigilia.
"$VIG" on >/dev/null
xset -dpms
vigilia_diz=$("$VIG" genmon | grep -c 'VIGÍLIA')
[ "$vigilia_diz" = 1 ] && ok "DPMS desabilitado por terceiro ainda conta como vigília" ||
	falha "com -dpms o painel diz que a tela apaga, e ela não apaga"
xset +dpms
xset dpms 900 0 0
"$VIG" genmon | grep -q 'VIGÍLIA' &&
	falha "Standby=900 conta como vigília, mas apaga o painel em 15 min" ||
	ok "Standby intermediário NÃO conta como vigília"
"$VIG" on >/dev/null

# 13c. GRAVE 2026-09-10 (achado pela revisao adversarial): o `caffeine` roda
#      `xset s off` via xdg-screensaver e NUNCA toca em Standby/Suspend/Off. O X
#      fica `0|600|900|0|1500`, e a guarda antiga (que exigia os TRES zerados)
#      deixava passar: gravava S_TIMEOUT=0 no baseline e o `off` seguinte fazia
#      `xset s 0 600` — screensaver nunca mais armava e o light-locker, que so
#      tranca em ScreenSaverNotify, nunca mais trancava a sessao. Estado estavel.
rm -f "$BASE"
xset s off
xset +dpms
xset dpms 900 0 1500 # exatamente o que o caffeine deixa
"$VIG" on >/dev/null
grep -q '^S_TIMEOUT=600' "$BASE" &&
	ok "cenário caffeine: baseline guarda S_TIMEOUT=600, não o zero do caffeine" ||
	falha "baseline envenenado pelo caffeine: $(tr '\n' ' ' <"$BASE")"
"$VIG" off >/dev/null
[ "$(campo 'timeout:' 2)" = 600 ] &&
	ok "cenário caffeine: off devolve o screensaver (a sessão volta a trancar)" ||
	falha "off deixou timeout=$(campo 'timeout:' 2) — light-locker nunca mais tranca"

# 13d. MENOR 2026-09-10: `prefer blanking`. A vigilia grava `noblank` e a versao
#      anterior nao restaurava nunca: o X ficava com o padrao desenhado em vez
#      de apagar, para sempre.
xset s 600 600
xset s blank
xset +dpms
xset dpms 900 0 1500
rm -f "$BASE"
"$VIG" on >/dev/null
[ "$(blank)" = noblank ] && ok "on grava noblank (o X não desenha padrão)" ||
	falha "on deixou prefer blanking=$(blank)"
"$VIG" off >/dev/null
[ "$(blank)" = blank ] && ok "off restaura prefer blanking=blank" ||
	falha "off deixou prefer blanking=$(blank), esperado blank"

# 13e. `baseline_valido`: arquivo nao-vazio nao e baseline valido. O baseline com
#      campos vazios ficou no disco do dono e 25 verificacoes verdes nao viram.
printf 'S_TIMEOUT=600\nS_CYCLE=600\nDPMS_STANDBY=\nDPMS_SUSPEND=\nDPMS_OFF=\nXFPM_DPMS=false\n' >"$BASE"
xset s 600 600
xset +dpms
xset dpms 900 0 1500
"$VIG" on >/dev/null
grep -q '^DPMS_OFF=1500' "$BASE" &&
	ok "on sobre baseline inválido regrava um baseline válido" ||
	falha "baseline inválido sobreviveu ao on: $(tr '\n' ' ' <"$BASE")"

# 14. `status` e `genmon` NAO pegam o lock: o painel chama genmon de 5 em 5 s e
#     nao pode ficar na fila atras de um `on` em andamento. ESTA execucao ja
#     segura o lock (fd 9, no topo), entao basta cronometrar as leituras.
#     A versao anterior deste teste abria `9>` de novo num subshell e travava
#     esperando o lock da propria bancada — deadlock que prendeu duas execucoes
#     por tres minutos em 2026-09-10.
if command -v timeout >/dev/null 2>&1; then
	timeout 5 "$VIG" genmon >/dev/null 2>&1 &&
		ok "genmon responde em <5 s com o lock tomado (não bloqueia o painel)" ||
		falha "genmon travou ou falhou com o lock tomado"
	timeout 5 "$VIG" status >/dev/null 2>&1 &&
		ok "status responde em <5 s com o lock tomado" ||
		falha "status travou com o lock tomado"
fi

echo
if [ "$falhas" -eq 0 ]; then
	echo "bancada vigilia: 100% verde"
	exit 0
fi
echo "bancada vigilia: $falhas falha(s)"
exit 1
