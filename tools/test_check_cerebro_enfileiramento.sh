#!/usr/bin/env bash
# Prova tools/check-cerebro-enfileiramento nos tres desfechos, com ledger de
# fixture. O controle positivo REAL e o ledger de producao de 2026-09-17, em que
# o enfileiramento levou 1.359 s e o cerebro ficou 40 min parado: a primeira
# versao deste canario reprovou nele antes de existir o teste.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
GATE=${GATE_ENFILEIRAMENTO:-./tools/check-cerebro-enfileiramento}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }
linha() { printf '{"schema_version":"cerebro_enfileirar_v1","inicio":"2026-09-17T13:00:25Z","gatilho":"path","duracao_s":%s}\n' "$1"; }

{ linha 38; linha 1359; } >"$TMP/regressao.jsonl"
"$GATE" --ledger "$TMP/regressao.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 1 ] && passo OK "1.359 s (a regressao medida) -> exit 1" || { passo FALHA "regressao deveria sair 1 (rc=$rc)"; falhou=1; }

{ linha 1359; linha 33; } >"$TMP/sao.jsonl"
"$GATE" --ledger "$TMP/sao.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && passo OK "33 s (o algoritmo de delta) -> exit 0, e so a ULTIMA execucao decide" || { passo FALHA "execucao sa deveria sair 0 (rc=$rc)"; falhou=1; }

linha 300 >"$TMP/fronteira.jsonl"
"$GATE" --ledger "$TMP/fronteira.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] && passo OK "exatamente no limiar (300 s) passa" || { passo FALHA "300 s nao pode reprovar (rc=$rc)"; falhou=1; }
linha 301 >"$TMP/fronteira1.jsonl"
"$GATE" --ledger "$TMP/fronteira1.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 1 ] && passo OK "1 s acima do limiar reprova (a fronteira aplicada e a declarada)" || { passo FALHA "301 s deveria reprovar (rc=$rc)"; falhou=1; }

: >"$TMP/vazio.jsonl"
"$GATE" --ledger "$TMP/vazio.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && passo OK "ledger vazio -> exit 2 (nao medi, nunca 'sao')" || { passo FALHA "vazio deveria sair 2 (rc=$rc)"; falhou=1; }
"$GATE" --ledger "$TMP/nao-existe.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && passo OK "ledger ausente -> exit 2" || { passo FALHA "ausente deveria sair 2 (rc=$rc)"; falhou=1; }
echo '{"inicio":"x"}' >"$TMP/sem-duracao.jsonl"
"$GATE" --ledger "$TMP/sem-duracao.jsonl" >/dev/null 2>&1; rc=$?
[ "$rc" -eq 2 ] && passo OK "linha sem duracao_s -> exit 2" || { passo FALHA "sem duracao deveria sair 2 (rc=$rc)"; falhou=1; }

if grep -q "check-cerebro-enfileiramento" ops/systemd/wikijuridica-cerebro-saude.service; then
	passo OK "a unit de saude executa o canario"
else
	passo FALHA "o canario nao esta na unit de saude: detector que ninguem roda nao detecta"; falhou=1
fi
[ "$falhou" -eq 0 ] && { echo "test_check_cerebro_enfileiramento: OK"; exit 0; }
echo "test_check_cerebro_enfileiramento: REPROVADO"; exit 1
