#!/usr/bin/env bash
# O cache negativo de falha upstream do `oss-install-matrix-env`, provado por
# mutacao.
#
# POR QUE ESTE TESTE EXISTE. A decisao de PULAR uma instalacao ja conhecida como
# falha roda dentro da sonda de identidade do Go do `run-go-cmd-cached`, que tem
# teto de poucos segundos. Errar para um lado custa exit 75 na matriz inteira
# (medido em 2026-09-10: `generate-oss-installation-matrix` devolvia
# `could not authenticate bounded Go version for fast cache` numa maquina
# ociosa). Errar para o outro cristaliza um veredito e esconde upstream que
# voltou — foi por isso que a guarda ganhou TTL, chave por rustc e, para o
# quickwit, precondicao amarrada a causa registrada (DNS).
#
# O autoteste vive DENTRO do wrapper (`WIKI_OSS_AUTOTESTE=1`) porque precisa das
# funcoes dele; aqui se prova que ele nao esta apenas dizendo "ok". Cada mutante
# apaga uma das quatro invalidacoes e tem de morrer.
set -euo pipefail

RAIZ="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
ALVO="$RAIZ/tools/oss-install-matrix-env"
TRABALHO="$(mktemp -d)"
trap 'rm -rf "$TRABALHO"' EXIT

falhas=0

if ! WIKI_OSS_AUTOTESTE=1 "$ALVO" >"$TRABALHO/base.log" 2>&1; then
	printf 'FALHA: o autoteste do wrapper reprova em HEAD\n' >&2
	cat "$TRABALHO/base.log" >&2
	exit 1
fi
printf 'ok   autoteste em HEAD: %s\n' "$(grep -c '^ok ' "$TRABALHO/base.log") caso(s) verde(s)"

mutante() {
	local nome="$1" antigo="$2" novo="$3"
	local copia="$TRABALHO/mut.sh"
	cp "$ALVO" "$copia"
	ANTIGO="$antigo" NOVO="$novo" python3 - "$copia" <<'PY'
import os
import sys
from pathlib import Path

caminho = Path(sys.argv[1])
texto = caminho.read_text(encoding="utf-8")
antigo = os.environ["ANTIGO"]
if texto.count(antigo) != 1:
    raise SystemExit(f"ancora do mutante nao e unica ({texto.count(antigo)}x): {antigo!r}")
caminho.write_text(texto.replace(antigo, os.environ["NOVO"]), encoding="utf-8")
PY
	if WIKI_OSS_AUTOTESTE=1 bash "$copia" >"$TRABALHO/mut.log" 2>&1; then
		printf 'MUTANTE SOBREVIVEU: %s\n' "$nome" >&2
		falhas=$((falhas + 1))
	else
		printf 'morto %s\n' "$nome"
	fi
}

mutante "precondicao ignora o marcador da causa" \
	'if [[ -n "$marcador" && "$motivo" == *"$marcador"* ]] && (($# > 0)) && "$@"; then' \
	'if (($# > 0)) && "$@"; then'

mutante "guarda ignora a troca de rustc" \
	'		index($0, "\"rustc\":\"" rustc "\"") == 0 { next }
' \
	''

mutante "guarda ignora o TTL" \
	'			if (epoch == "" || agora - epoch >= ttl) { next }' \
	'			if (epoch == "") { next }'

mutante "guarda le o registro mais antigo, nao o mais novo" \
	'			if (achou && epoch + 0 < melhor + 0) { next }' \
	'			if (achou) { next }'

# ETAPA 2 — o laco de retry, provado com o wrapper de verdade e sem rede.
#
# Levantar a guarda e metade do trabalho; a outra metade e o motivo REGISTRADO
# depois da retentativa. Se a instalacao voltar a falhar por outra causa e a
# linha nova ainda disser "saiu do DNS", a precondicao levanta a guarda outra
# vez e o retry vira laco — que e o custo que esta guarda existe para nao pagar.
#
# O override aponta para http://localhost:1/, que RESOLVE (entao a precondicao
# dispara) e e recusado pela allowlist do proprio wrapper antes de qualquer
# requisicao. Nao ha rede neste teste, e o ledger de producao nao e tocado.
ledger="$TRABALHO/ledger.jsonl"
printf '{"quando":"x","epoch":%s,"crate":"quickwit","versao":"prebuilt","rustc":"%s","motivo":"upstream: install.quickwit.io saiu do DNS (NOERROR com 0 respostas em 1.1.1.1)"}\n' \
	"$(date -u +%s)" "$(rustc --version 2>/dev/null || echo sem-rustc)" >"$ledger"

if ! WIKI_OSS_INSTALL_FALHAS="$ledger" WIKI_OSS_QUICKWIT_INSTALL_SCRIPT_URL="http://localhost:1/" \
	"$ALVO" true >"$TRABALHO/retry.log" 2>&1; then
	printf 'FALHA: o wrapper abortou na retentativa do quickwit\n' >&2
	cat "$TRABALHO/retry.log" >&2
	exit 1
fi
if grep -q 'quickwit@prebuilt retentado' "$TRABALHO/retry.log"; then
	printf 'ok   DNS de volta levanta a guarda\n'
else
	printf 'FALHA: com o host resolvendo, a guarda nao foi levantada\n' >&2
	falhas=$((falhas + 1))
fi

linha_nova="$(grep '"crate":"quickwit"' "$ledger" | tail -1)"
if printf '%s' "$linha_nova" | grep -q 'saiu do DNS'; then
	printf 'FALHA: a falha nova foi registrada como "saiu do DNS" com o host resolvendo — a proxima invocacao levantaria a guarda de novo\n' >&2
	falhas=$((falhas + 1))
else
	printf 'ok   motivo registrado reflete a causa real\n'
fi

if WIKI_OSS_INSTALL_FALHAS="$ledger" WIKI_OSS_QUICKWIT_INSTALL_SCRIPT_URL="http://localhost:1/" \
	"$ALVO" true 2>&1 | grep -q 'quickwit pulado'; then
	printf 'ok   segunda invocacao pula: nao ha laco de retry\n'
else
	printf 'FALHA: a segunda invocacao retentou de novo — laco de retry\n' >&2
	falhas=$((falhas + 1))
fi

if ((falhas > 0)); then
	printf 'test_oss_install_matrix_env_cache_negativo: %s mutante(s) sobreviveu(ram)\n' "$falhas" >&2
	exit 1
fi
printf 'PASS test_oss_install_matrix_env_cache_negativo: 4 mutantes mortos, sem laco de retry\n'
