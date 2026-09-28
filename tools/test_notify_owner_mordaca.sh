#!/bin/bash
# Prova que ALTA e CRITICA nao ficam caladas indefinidamente, e que a escalada
# rompe o cooldown UMA vez — nao todas.
#
# ★ OS DOIS DEFEITOS MEDIDOS EM 2026-09-05
#
# 1. ROMPIMENTO SEM FIM. A ordem era: decidir o silencio -> gravar o estado ->
#    escalar -> `silenciado = False`. Na volta silenciada a gravacao nao mexia
#    em `ultimo_envio`, entao na chamada seguinte o cooldown estava vencido de
#    novo e a escalada disparava de novo. Contado em data/ops/owner_alerts.jsonl
#    (3.592 linhas): a chave `rede-banda` tem 152 eventos com `escalado: true` e
#    OS 152 FORAM ENTREGUES ao desktop do dono. O comentario do codigo dizia
#    "rompe o cooldown UMA vez".
#
# 2. MORDACA POR COOLDOWN LONGO. `--cooldown` e escolhido pelo produtor e nao
#    tinha teto. Como `ocorrencias` so conta envio NAO silenciado, um cooldown
#    longo calava a chave E congelava o contador de que a escalada depende: a
#    critica ficava muda com a escalada desligada junto. `bot-abandono` sai com
#    --cooldown 86400, e os 5 do `eleva_severidade_em` dela eram CINCO DIAS.
#
# ESTADO ISOLADO: arvore minima em TMP, ledger real intocado, `notify-send`
# dublado no PATH (sem o duble cada caso abriria um balao no desktop do dono).
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/data/ops" "$TMP/ops" "$TMP/tools"
printf '#!/bin/sh\nexit 0\n' >"$TMP/bin/notify-send"
chmod +x "$TMP/bin/notify-send"
printf '#!/bin/sh\nexit 0\n' >"$TMP/bin/logger"
chmod +x "$TMP/bin/logger"
export PATH="$TMP/bin:$PATH"
cp "$RAIZ/ops/alert_policy.json" "$TMP/ops/"
cp "$RAIZ/tools/notify-owner" "$TMP/tools/"

FALHAS=0
chk() { if [ "$2" = "$3" ]; then echo "  ok   $1"; else
	echo "  FALHA $1: obtive '$2', queria '$3'"
	FALHAS=$((FALHAS + 1))
fi; }

ESTADO="$TMP/data/ops/owner_alerts_state.json"

# Semeia o estado da chave: (chave, ocorrencias, severidade, horas_desde_o_envio,
# horas_aberta). E o unico jeito honesto de testar relogio sem esperar o relogio.
semear() {
	CHAVE="$1" OCOR="$2" SEV="$3" H_ENVIO="$4" H_ABERTO="$5" python3 - "$ESTADO" <<'PY'
import datetime, json, os, sys
agora = datetime.datetime.now(datetime.timezone.utc)
def atras(horas):
    return (agora - datetime.timedelta(hours=float(horas))).isoformat()
json.dump({os.environ["CHAVE"]: {
    "aberto": True,
    "aberto_desde": atras(os.environ["H_ABERTO"]),
    "ultimo_envio": atras(os.environ["H_ENVIO"]),
    "severidade": os.environ["SEV"],
    "repeticoes": int(os.environ["OCOR"]),
    "ocorrencias": int(os.environ["OCOR"]),
}}, open(sys.argv[1], "w"))
PY
}

# Dispara e devolve os campos pedidos do evento JSON.
disparar() {
	local chave="$1" sev="$2" cooldown="$3"
	shift 3
	"$TMP/tools/notify-owner" --chave "$chave" --severidade "$sev" --titulo t \
		--mensagem m --evidencia e --cooldown "$cooldown" --json 2>/dev/null |
		python3 -c "import json,sys;d=json.load(sys.stdin);print(*[d.get(c) for c in sys.argv[1:]])" "$@"
}

echo "== 1. a escalada rompe o cooldown UMA vez, nao todas (defeito das 152 entregas)"
# portal-fora: eleva_severidade_em = 2. Estado com 2 ocorrencias em `media` e
# envio ha 1 minuto: o cooldown de 1 h esta valendo.
semear portal-fora 2 media 0.016 0.02
A1="$(disparar portal-fora media 3600 severidade escalado silenciado_por_cooldown ocorrencias)"
chk "1a chamada: escala e ENTREGA" "$A1" "alta True False 3"
A2="$(disparar portal-fora media 3600 severidade escalado silenciado_por_cooldown)"
chk "2a chamada: escalada ja registrada, volta a silenciar" "$A2" "alta True True"
A3="$(disparar portal-fora media 3600 silenciado_por_cooldown)"
chk "3a chamada: continua silenciada" "$A3" "True"

echo "== 2. teto de cooldown para alta/critica"
# 604800 s (uma semana) pedidos pelo produtor; 48 h desde o ultimo envio.
semear borda-origem 1 critica 48 48
B1="$(disparar borda-origem critica 604800 silenciado_por_cooldown cooldown_efetivo_s)"
chk "critica: cooldown de 1 semana cai para o teto de 86400 e a entrega sai" "$B1" "False 86400"
# CONTRAPROVA: `media` nao tem relogio, e o cronico continua tolerado.
semear rede-banda 1 media 48 48
B2="$(disparar rede-banda media 604800 silenciado_por_cooldown cooldown_efetivo_s)"
chk "media: sem teto, o cronico segue calado como o produtor pediu" "$B2" "True 604800"

echo "== 3. escalada por TEMPO ABERTO, com o contador de ocorrencias parado"
# borda-origem: eleva_severidade_em = 3 (nao alcancado: 1 ocorrencia) e o padrao
# eleva_severidade_apos_h = 24. Aberta ha 30 h, ultimo envio ha 1 minuto.
semear borda-origem 1 alta 0.016 30
C1="$(disparar borda-origem alta 3600 severidade escalado silenciado_por_cooldown)"
chk "alta aberta ha 30h escala para critica e rompe o cooldown" "$C1" "critica True False"
# CONTRAPROVA 1: a MESMA idade, em `media`, nao escala — o relogio e so de
# alta/critica, senao a tolerancia comprada para o enlace de rede se desfaz.
semear rede-banda 1 media 0.016 30
C2="$(disparar rede-banda media 3600 severidade escalado silenciado_por_cooldown)"
chk "media aberta ha 30h NAO escala pelo relogio" "$C2" "media False True"
# CONTRAPROVA 2: alta recem-aberta nao escala por tempo.
semear borda-origem 1 alta 0.016 2
C3="$(disparar borda-origem alta 3600 severidade escalado)"
chk "alta aberta ha 2h nao escala" "$C3" "alta False"

echo "== 4. incidente pelo relogio, com ocorrencias abaixo do limiar"
# borda-origem: abre_incidente_em = 6 (temos 1) e abre_incidente_apos_h = 72.
rm -f "$TMP/data/ops/incidents.jsonl"
semear borda-origem 1 alta 0.016 100
D1="$(disparar borda-origem alta 3600 incidente_aberto)"
chk "alta aberta ha 100h abre incidente com 1 ocorrencia" "$D1" "True"
chk "uma unica linha no ledger de incidentes" "$(wc -l <"$TMP/data/ops/incidents.jsonl" 2>/dev/null || echo 0)" "1"
D2="$(disparar borda-origem alta 3600 incidente_aberto)"
chk "a 2a chamada NAO reabre o incidente" "$D2" "False"

echo "== 5. politica ausente nao trava nem escala nada"
rm -f "$TMP/ops/alert_policy.json"
semear chave-sem-politica 1 alta 0.016 500
E1="$(disparar chave-sem-politica alta 3600 severidade escalado silenciado_por_cooldown cooldown_efetivo_s)"
chk "sem politica: sem teto e sem relogio, comportamento anterior" "$E1" "alta False True 3600"

[ "$FALHAS" -eq 0 ] && echo "test_notify_owner_mordaca: OK" || {
	echo "test_notify_owner_mordaca: $FALHAS falha(s)"
	exit 1
}
