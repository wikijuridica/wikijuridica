#!/bin/sh
# Mede o regime de energia da CPU e grava UMA linha JSON em data/ops/energia_cpu.jsonl.
# Uso: tools/medir-energia-cpu.sh [segundos_de_amostra=3]
# Lê RAPL (energy_uj) antes/depois, MHz médio e máximo, temperatura do pacote e
# do NVMe, contador de throttle e o PL1/PL2 vigentes — para flagrar reescrita por
# thermald ou pelo EC/DPTF (INT3400 existe neste Lenovo).
set -eu
cd "$(dirname "$0")/.."
DT=${1:-3}
R=/sys/class/powercap/intel-rapl:0
a=$(cat $R/energy_uj)
t0=$(date +%s.%N)
timeout "$DT" tail -f /dev/null || true # espera ociosa sem ocupar CPU
b=$(cat $R/energy_uj)
t1=$(date +%s.%N)
w=$(awk -v a="$a" -v b="$b" -v t0="$t0" -v t1="$t1" 'BEGIN{printf "%.2f",(b-a)/1e6/(t1-t0)}')
mhz=$(awk '/^cpu MHz/{s+=$4;n++} END{printf "%.0f",s/n}' /proc/cpuinfo)
mhzmax=$(awk '/^cpu MHz/{if($4>m)m=$4} END{printf "%.0f",m}' /proc/cpuinfo)
pkg=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -n | tail -1)
nvme2=$(sensors 2>/dev/null | awk '/^Sensor 2/{gsub(/[^0-9.]/,"",$3);print $3;exit}')
thr=$(cat /sys/devices/system/cpu/cpu0/thermal_throttle/package_throttle_count)
pl1=$(cat $R/constraint_0_power_limit_uw)
pl2=$(cat $R/constraint_1_power_limit_uw)
pl1m=$(cat /sys/class/powercap/intel-rapl-mmio:0/constraint_0_power_limit_uw 2>/dev/null || echo 0)
nt=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo)
gov=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
epp=$(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference)
load=$(cut -d' ' -f1 /proc/loadavg)
line=$(printf '{"ts":"%s","watts":%s,"mhz_medio":%s,"mhz_max":%s,"pkg_temp_mc":%s,"nvme_sensor2_c":"%s","pkg_throttle_count":%s,"pl1_uw":%s,"pl1_mmio_uw":%s,"pl2_uw":%s,"no_turbo":%s,"governor":"%s","epp":"%s","load1":%s}' \
	"$(date -Is)" "$w" "$mhz" "$mhzmax" "${pkg:-0}" "${nvme2:-}" "$thr" "$pl1" "$pl1m" "$pl2" "$nt" "$gov" "$epp" "$load")
mkdir -p data/ops
echo "$line" >>data/ops/energia_cpu.jsonl
echo "$line"
