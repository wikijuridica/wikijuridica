#!/usr/bin/env bash
# Prova que notify-owner carrega a idade REAL do incidente (`aberto_desde`) e o
# contador de ocorrencias em toda linha do ledger — inclusive na silenciada por
# cooldown — e que o consumidor check-owner-alerts-abertos mede por ele.
#
# O defeito que isto apanha (2026-09-02): critica aberta ha 15,7 h passou 24x por
# "OK" porque a idade era lida de `alertado_em` da ULTIMA linha, regravada a cada
# 2 min mesmo silenciada.
#
# Isolamento: copia do notify-owner num ROOT temporario (ele deriva a raiz de
# __file__), consumidor apontado por WIKI_ROOT/WIKI_OWNER_ALERTS_LEDGER, e um
# notify-send DUBLE na frente do PATH — o real vive em /usr/bin ao lado do
# python3, entao "tirar do PATH" nao existe; sem o duble o teste abre baloes no
# desktop do dono (aconteceu na primeira versao deste arquivo).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
T=$(mktemp -d "${TMPDIR:-/tmp}/notify-owner.XXXXXX")
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/tools" "$T/data/ops" "$T/bin" "$T/content"
cp tools/notify-owner tools/check-owner-alerts-abertos "$T/tools/"
[ -f content/alert_policy.json ] && cp content/alert_policy.json "$T/content/"
printf '#!/bin/sh\nexit 0\n' >"$T/bin/notify-send"
chmod +x "$T/bin/notify-send"
export PATH="$T/bin:$PATH"
NO="$T/tools/notify-owner"
L="$T/data/ops/owner_alerts.jsonl"
falhou=0

chama() {
	python3 "$NO" --chave x-teste --severidade critica --titulo t --mensagem m --evidencia e --cooldown "$1" 2>&1
	echo "  rc=$?"
}
saidas=$(
	chama 1800
	chama 1800
	chama 0
)

res=$(
	python3 - "$L" <<'EOF'
import json,sys
ls=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
a=[l for l in ls if l['chave']=='x-teste']
ok = len(a)==3 and a[0]['aberto_desde'] and a[1]['aberto_desde']==a[0]['aberto_desde'] and a[2]['aberto_desde']==a[0]['aberto_desde'] \
     and a[0].get('ocorrencias')==1 and a[1].get('ocorrencias')==1 and a[2].get('ocorrencias')==2 \
     and a[1].get('silenciado_por_cooldown') is True and not a[2].get('silenciado_por_cooldown')
print('ok' if ok else 'falhou:'+json.dumps([(l.get('aberto_desde'),l.get('ocorrencias'),l.get('silenciado_por_cooldown')) for l in a]))
EOF
)
if [ "$res" = ok ]; then
	echo "ok caso 1: aberto_desde constante nas 3 linhas (inclusive silenciada) e ocorrencias 1,1,2"
else
	echo "FALHOU caso 1: $res"
	echo "$saidas" | sed 's/^/    /'
	falhou=1
fi

# Caso 2: resolvido zera.
python3 "$NO" --chave x-teste --resolvido --titulo ok --mensagem ok >/dev/null 2>&1
res=$(python3 -c "
import json
ls=[json.loads(l) for l in open('$L') if l.strip()]
l=[x for x in ls if x['chave']=='x-teste'][-1]
print('ok' if l['resolvido'] and l['aberto_desde'] is None and l['ocorrencias']==0 else 'falhou:'+json.dumps(l))")
if [ "$res" = ok ]; then echo "ok caso 2: --resolvido fecha o incidente (aberto_desde nulo, ocorrencias 0)"; else
	echo "FALHOU caso 2: $res"
	falhou=1
fi

# Caso 3: o consumidor mede a idade pelo aberto_desde, nao pela ultima linha.
python3 - "$L" <<'EOF'
import json,sys,datetime
old=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=20)).isoformat()
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
base={"schema_version":"owner_alert_v1","chave":"y-velha","severidade":"critica","resolvido":False,"titulo":"t","mensagem":"m","evidencia":"e","origem":"o","canais":{"desktop":"silenciado","journal":"silenciado"}}
with open(sys.argv[1],'a') as fh:
    fh.write(json.dumps(dict(base,alertado_em=old,aberto_desde=old,ocorrencias=1))+"\n")
    fh.write(json.dumps(dict(base,alertado_em=now,aberto_desde=old,ocorrencias=1,silenciado_por_cooldown=True))+"\n")
EOF
saida=$(cd "$T" && WIKI_ROOT="$T" WIKI_OWNER_ALERTS_LEDGER="$L" python3 tools/check-owner-alerts-abertos 2>&1)
rc=$?
if [ "$rc" -eq 1 ] && grep -q 'y-velha — aberta ha 20h' <<<"$saida"; then
	echo "ok caso 3: consumidor mede 20h pelo aberto_desde apesar da ultima linha ser de agora"
else
	echo "FALHOU caso 3 (rc=$rc)"
	echo "$saida" | sed 's/^/    /'
	falhou=1
fi

[ "$falhou" -eq 0 ] && echo "test_notify_owner_aberto_desde: OK (3 casos)" || echo "test_notify_owner_aberto_desde: REPROVADO"
exit "$falhou"
