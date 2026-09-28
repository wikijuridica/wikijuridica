#!/usr/bin/env bash
# test_ide_kit.sh — as bancadas do kit ops/ide/ na qualidade diaria.
#
# Entra pelo glob tools/test_*.sh de tools/run-qualidade-diaria (teto de 600 s por
# arquivo; saida 75 conta como infra, fora da conta de vermelhos). Roda, nesta
# ordem:
#   1. ops/ide/verificar-pilha-grafica.sh --autoteste — a logica dos gates da pilha
#      grafica da maquina nova contra /sys e comandos de mentira. E pura: roda em
#      qualquer host, e e o unico jeito de ver esses gates reprovarem antes de a
#      maquina nova existir;
#   2. ops/ide/testa-instalar-ide.sh — o ops/ide/instalar-ide.sh REAL num namespace
#      de usuario, montagem, PID e rede, com dubles e mutantes. Sai 75 se o kernel
#      nao der namespace de usuario sem privilegio.
#
# SAIDA: 1 se alguma reprovou; senao 75 se alguma foi infra; senao 0. A ultima
# linha resume as duas — o runner guarda `tail -2` no ledger.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

reprovou=""; infra=""
roda() {  # roda <rotulo> <comando...>
  local rotulo=$1 rc
  shift
  echo "── $rotulo"
  "$@"
  rc=$?
  case "$rc" in
    0) ;;
    75) infra="$infra $rotulo" ;;
    *) reprovou="$reprovou $rotulo(rc=$rc)" ;;
  esac
}
roda pilha-grafica bash ops/ide/verificar-pilha-grafica.sh --autoteste
roda instalar-ide bash ops/ide/testa-instalar-ide.sh

echo
if [ -n "$reprovou" ]; then echo "test_ide_kit: REPROVOU em:$reprovou${infra:+ (infra em:$infra)}"; exit 1; fi
if [ -n "$infra" ]; then echo "test_ide_kit: infra em:$infra (o resto verde)"; exit 75; fi
echo "test_ide_kit: VERDE (autoteste da pilha grafica e bancada do instalar-ide.sh)"
exit 0
