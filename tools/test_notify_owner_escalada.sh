#!/bin/bash
# Prova a escalada do notify-owner: eleva severidade no limiar, abre incidente
# uma vez so, e nao escala o que a politica manda tolerar.
#
# ESTADO ISOLADO: WIKI_OPS_DIR aponta para um diretorio temporario, entao o
# ledger real de alertas nao e tocado. E o `notify-send` e DUBLADO no PATH — o
# real vive em /usr/bin ao lado do python3, e sem o duble cada caso deste teste
# abriria um balao no desktop do dono.
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/data/ops" "$TMP/ops"
printf '#!/bin/sh\nexit 0\n' >"$TMP/bin/notify-send"
chmod +x "$TMP/bin/notify-send"
printf '#!/bin/sh\nexit 0\n' >"$TMP/bin/systemd-cat"
chmod +x "$TMP/bin/systemd-cat"
export PATH="$TMP/bin:$PATH"
cp "$RAIZ/ops/alert_policy.json" "$TMP/ops/"

FALHAS=0
chk() { if [ "$2" = "$3" ]; then echo "  ok   $1"; else
	echo "  FALHA $1: obtive '$2', queria '$3'"
	FALHAS=$((FALHAS + 1))
fi; }

# O tool resolve ROOT pelo proprio caminho, entao copiamos a arvore minima.
mkdir -p "$TMP/tools"
cp "$RAIZ/tools/notify-owner" "$TMP/tools/"
disparar() { "$TMP/tools/notify-owner" --chave "$1" --severidade "$2" --titulo t --mensagem m \
	--evidencia e --cooldown 0 --json 2>/dev/null; }

echo "== portal-fora: eleva em 2, incidente em 3"
S1=$(disparar portal-fora media | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["severidade"],d["escalado"],d["ocorrencias"])')
chk "1a ocorrencia nao escala" "$S1" "media False 1"
S2=$(disparar portal-fora media | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["severidade"],d["escalado"])')
chk "2a ocorrencia ja no limiar escala" "$S2" "alta True"
S3=$(disparar portal-fora media | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["severidade"],d.get("incidente_aberto"))')
chk "3a ocorrencia abre incidente" "$S3" "alta True"
S4=$(disparar portal-fora media | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("incidente_aberto"))')
chk "4a ocorrencia NAO reabre incidente" "$S4" "False"
chk "uma linha no ledger de incidentes" "$(wc -l <"$TMP/data/ops/incidents.jsonl" 2>/dev/null || echo 0)" "1"

echo "== rede-banda: politica tolerante, nao escala cedo"
for _ in 1 2 3 4; do disparar rede-banda media >/dev/null; done
S5=$(disparar rede-banda media | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["severidade"],d["escalado"])')
chk "5a ocorrencia de alerta cronico nao escala" "$S5" "media False"

echo "== critica nao passa do teto"
disparar portal-fora critica >/dev/null
disparar portal-fora critica >/dev/null
S6=$(disparar portal-fora critica | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["severidade"])')
chk "critica continua critica" "$S6" "critica"

echo "== politica ausente nao trava o alerta"
rm -f "$TMP/ops/alert_policy.json"
S7=$(disparar chave-sem-politica alta | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["severidade"],d["escalado"])')
chk "sem politica, comportamento anterior" "$S7" "alta False"

[ "$FALHAS" -eq 0 ] && echo "test_notify_owner_escalada: OK" || {
	echo "test_notify_owner_escalada: $FALHAS falha(s)"
	exit 1
}
