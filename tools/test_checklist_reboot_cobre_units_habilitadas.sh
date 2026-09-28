#!/usr/bin/env bash
# Toda unit `wikijuridica-*` HABILITADA no host tem de ter (1) cópia versionada
# em ops/systemd/ e (2) linha em ops/host-state/CHECKLIST-REBOOT.md.
#
# POR QUE, medido em 2026-09-08: das 52 units habilitadas, o checklist de reboot
# mencionava QUATRO. Quem o seguisse depois de um reboot subiria o portal e
# deixaria 48 unidades para trás — cérebro, coleta do STJ, DJEN, DataJud, evento
# unificado, grafo jurídico, IndexNow, expurgo LGPD, aquecimento de borda,
# backup. A custódia das units estava íntegra (as 52 tinham cópia em
# ops/systemd/); a lacuna era de INVENTÁRIO, e ela só cobra o preço no dia em
# que a máquina não volta — que é o pior dia possível para descobrir.
#
# O teste é de HOST: ele lê `systemctl list-unit-files` da máquina onde roda.
# Fora do host de produção não há unit `wikijuridica-*` habilitada, e aí ele
# PULA dizendo o motivo. Passar por vazio seria pior que não existir: daria a
# impressão de cobertura onde não há medição nenhuma.
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
CHECKLIST="$RAIZ/ops/host-state/CHECKLIST-REBOOT.md"
UNITS="$RAIZ/ops/systemd"
FALHAS=0

if ! command -v systemctl >/dev/null 2>&1; then
	printf 'PULADO: sem systemctl neste ambiente — nada a conferir\n'
	exit 0
fi

habilitadas="$(systemctl list-unit-files --state=enabled --no-pager --no-legend 2>/dev/null |
	awk '{print $1}' | grep '^wikijuridica-' || true)"

if [ -z "$habilitadas" ]; then
	printf 'PULADO: nenhuma unit wikijuridica-* habilitada neste host — este teste só mede no host de produção\n'
	exit 0
fi

total=0
for unit in $habilitadas; do
	total=$((total + 1))
	if [ ! -f "$UNITS/$unit" ]; then
		printf 'FALHOU: %s está habilitada no host e NÃO tem cópia em ops/systemd/ — perda de custódia\n' "$unit" >&2
		FALHAS=$((FALHAS + 1))
	fi
	if ! grep -q -- "$unit" "$CHECKLIST"; then
		printf 'FALHOU: %s está habilitada no host e NÃO aparece no CHECKLIST-REBOOT.md — quem seguir o checklist a deixa para trás\n' "$unit" >&2
		FALHAS=$((FALHAS + 1))
	fi
done

if [ "$FALHAS" -gt 0 ]; then
	printf '%s falha(s) sobre %s unit(s) habilitada(s)\n' "$FALHAS" "$total" >&2
	printf 'conserto: acrescentar a unit ao inventário de ops/host-state/CHECKLIST-REBOOT.md,\n' >&2
	printf '          com o que ela habilita, como conferir depois do boot e o que se perde sem ela\n' >&2
	exit 1
fi
printf 'test_checklist_reboot_cobre_units_habilitadas: ok (%s units habilitadas, todas com cópia e linha)\n' "$total"
