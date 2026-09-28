#!/bin/sh
# Aplica o teto de potência (RAPL), liga o turbo e normaliza o EPB.
# Chamado por ops/systemd/wikijuridica-energia.service; roda como root.
# Valores vêm do ambiente da unit (WIKI_PL1_UW etc.) para que ajuste = editar a
# unit, não o script. Falha alto se qualquer escrita não "pegar".
set -eu
R=/sys/class/powercap/intel-rapl:0
: "${WIKI_PL1_UW:=20000000}" "${WIKI_PL1_WINDOW_US:=27983872}"
: "${WIKI_PL2_UW:=30000000}" "${WIKI_PL2_WINDOW_US:=2440}"

escreve() { # escreve ARQUIVO VALOR e confere a leitura de volta
	printf '%s' "$2" >"$1"
	lido=$(cat "$1")
	[ "$lido" = "$2" ] || {
		echo "energia: $1 ficou em $lido, esperado $2" >&2
		return 1
	}
}

# 1. RAPL. Há DUAS zonas de pacote e vale a MENOR: intel-rapl:0 (MSR) e
#    intel-rapl-mmio:0 (MCHBAR, que o firmware Lenovo deixa em PL1=15 W).
#    Medido 2026-09-09: só a MSR em 20 W → regime travou em 14,9 W. As duas
#    precisam do mesmo valor. A janela é quantizada pelo hardware, então a
#    leitura de volta pode diferir do pedido — por isso `|| true` só nela.
for Z in "$R" /sys/class/powercap/intel-rapl-mmio:0; do
	[ -d "$Z" ] || continue
	escreve "$Z/constraint_0_time_window_us" "$WIKI_PL1_WINDOW_US" || true
	escreve "$Z/constraint_0_power_limit_uw" "$WIKI_PL1_UW"
	escreve "$Z/constraint_1_time_window_us" "$WIKI_PL2_WINDOW_US" || true
	escreve "$Z/constraint_1_power_limit_uw" "$WIKI_PL2_UW"
	escreve "$Z/enabled" 1
done

# 2. Turbo ligado (o TLP também faz; aqui é cinto e suspensório).
escreve /sys/devices/system/cpu/intel_pstate/no_turbo 0

# 3. EPB = 6 (normal) em todas as CPUs — desfaz o 0 (performance) do tuned.
if [ -e /dev/cpu/0/msr ]; then
	for c in /dev/cpu/[0-9]*; do
		python3 - "$c/msr" <<'PY'
import os, struct, sys
f = os.open(sys.argv[1], os.O_RDWR)
os.lseek(f, 0x1B0, 0)
v = struct.unpack('<Q', os.read(f, 8))[0]
v = (v & ~0xF) | 6
os.lseek(f, 0x1B0, 0)
os.write(f, struct.pack('<Q', v))
os.close(f)
PY
	done
fi

M=/sys/class/powercap/intel-rapl-mmio:0
echo "energia: msr PL1=$(cat $R/constraint_0_power_limit_uw)uW/$(cat $R/constraint_0_time_window_us)us PL2=$(cat $R/constraint_1_power_limit_uw)uW/$(cat $R/constraint_1_time_window_us)us | mmio PL1=$(cat $M/constraint_0_power_limit_uw)uW PL2=$(cat $M/constraint_1_power_limit_uw)uW | no_turbo=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo)"
