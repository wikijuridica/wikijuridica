#!/usr/bin/env bash
# Prova que check-units-instaladas REPROVA o caso ruim e ACEITA o legítimo.
#
# Nasce junto com o gate (2026-09-02), pela regra do repositório: detector que
# só foi visto passar no caso certo não está testado. Os dois casos ruins são
# exatamente os do incidente de 01-02/09: (1) Requires= para unit sem arquivo /
# não instalada; (2) unit instalada como CÓPIA divergente do repositório. O
# caso bom é a instalação por symlink com toda dependência presente.
#
# Roda com --sem-systemctl: as regras de runtime (LoadState, daemon-reload,
# timer ativo) dependem do systemd da máquina e ficam fora do teste; as regras
# de arquivo são as que o teste prova.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
GATE=${GATE_UNITS_INSTALADAS:-./tools/check-units-instaladas}
T=$(mktemp -d "${TMPDIR:-/tmp}/units-instaladas.XXXXXX")
trap 'rm -rf "$T"' EXIT
falhou=0

monta() { # $1 = nome do caso
	# ${T:?} aborta se T estiver vazio, em vez de `rm -rf /<caso>`.
	rm -rf "${T:?}/$1"
	mkdir -p "$T/$1/ops" "$T/$1/etc"
	cat >"$T/$1/ops/wikijuridica-x.service" <<'U'
[Unit]
Description=x
Requires=wikijuridica-x.socket
[Service]
Type=simple
ExecStart=/bin/true
[Install]
WantedBy=multi-user.target
U
	cat >"$T/$1/ops/wikijuridica-x.socket" <<'U'
[Unit]
Description=socket de x
[Socket]
ListenStream=127.0.0.1:1
[Install]
WantedBy=sockets.target
U
}

# Caso 1 (o incidente): dependência declarada sem instalação e sem arquivo.
monta caso1
rm "$T/caso1/ops/wikijuridica-x.socket"
ln -sf "$T/caso1/ops/wikijuridica-x.service" "$T/caso1/etc/"
if "$GATE" --sem-systemctl --dir "$T/caso1/ops" --etc "$T/caso1/etc" >/dev/null 2>&1; then
	echo "FALHOU caso 1: Requires= para unit sem arquivo passou"
	falhou=1
else
	echo "ok caso 1: dependência sem arquivo reprova"
fi

# Caso 2: socket existe no repo mas NÃO está instalada (referenciada => esperada).
monta caso2
ln -sf "$T/caso2/ops/wikijuridica-x.service" "$T/caso2/etc/"
saida=$("$GATE" --sem-systemctl --dir "$T/caso2/ops" --etc "$T/caso2/etc" 2>&1)
rc=$?
if [ "$rc" -eq 1 ] && grep -q '\[instalada\] wikijuridica-x.socket' <<<"$saida"; then
	echo "ok caso 2: unit referenciada e não instalada reprova"
else
	echo "FALHOU caso 2 (rc=$rc): esperava [instalada] wikijuridica-x.socket"
	echo "$saida" | sed 's/^/    /'
	falhou=1
fi

# Caso 3: instalada como cópia DIVERGENTE.
monta caso3
ln -sf "$T/caso3/ops/wikijuridica-x.socket" "$T/caso3/etc/"
sed 's/Description=x/Description=outra/' "$T/caso3/ops/wikijuridica-x.service" >"$T/caso3/etc/wikijuridica-x.service"
saida=$("$GATE" --sem-systemctl --dir "$T/caso3/ops" --etc "$T/caso3/etc" 2>&1)
rc=$?
if [ "$rc" -eq 1 ] && grep -q 'cópia DIVERGENTE' <<<"$saida"; then
	echo "ok caso 3: cópia divergente reprova"
else
	echo "FALHOU caso 3 (rc=$rc)"
	echo "$saida" | sed 's/^/    /'
	falhou=1
fi

# Caso 4 (legítimo): tudo por symlink, dependência presente, e o binário do
# serviço que exige socket sabe herdá-lo (contém LISTEN_FDS — é a string que o
# gate procura, a mesma que cmd/server/main.go usa em `escutar`).
monta caso4
printf '#!/bin/sh\n# LISTEN_FDS NOTIFY_SOCKET\nexit 0\n' >"$T/caso4/bin-x"
chmod +x "$T/caso4/bin-x"
sed -i "s#ExecStart=/bin/true#ExecStart=$T/caso4/bin-x#" "$T/caso4/ops/wikijuridica-x.service"
ln -sf "$T/caso4/ops/wikijuridica-x.service" "$T/caso4/ops/wikijuridica-x.socket" "$T/caso4/etc/"
if "$GATE" --sem-systemctl --dir "$T/caso4/ops" --etc "$T/caso4/etc" >/dev/null 2>&1; then
	echo "ok caso 4: instalação por symlink com dependência presente passa"
else
	echo "FALHOU caso 4: caso legítimo reprovou"
	"$GATE" --sem-systemctl --dir "$T/caso4/ops" --etc "$T/caso4/etc" | sed 's/^/    /'
	falhou=1
fi

# Caso 5: Type=notify com binário sem NOTIFY_SOCKET (o /bin/true não tem).
monta caso5
sed -i 's/Type=simple/Type=notify/' "$T/caso5/ops/wikijuridica-x.service"
ln -sf "$T/caso5/ops/wikijuridica-x.service" "$T/caso5/ops/wikijuridica-x.socket" "$T/caso5/etc/"
saida=$("$GATE" --sem-systemctl --dir "$T/caso5/ops" --etc "$T/caso5/etc" 2>&1)
rc=$?
if [ "$rc" -eq 1 ] && grep -q '\[notify_binario\]' <<<"$saida" && grep -q '\[socket_binario\]' <<<"$saida"; then
	echo "ok caso 5: Type=notify e Requires=.socket com binário sem sd_notify/LISTEN_FDS reprovam"
else
	echo "FALHOU caso 5 (rc=$rc)"
	echo "$saida" | sed 's/^/    /'
	falhou=1
fi

if [ "$falhou" -eq 0 ]; then echo "test_units_instaladas: OK (5 casos)"; else echo "test_units_instaladas: REPROVADO"; fi
exit "$falhou"
