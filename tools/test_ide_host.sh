#!/usr/bin/env bash
# test_ide_host.sh — as invariantes do IDE neste host (tools/check-ide-host), na
# qualidade diaria (glob tools/test_*.sh de tools/run-qualidade-diaria; teto de
# 600 s; saida 75 = infra, fora da conta de vermelhos).
#
# Saidas do check: 0 verde · 1 falha · 75 pulada (codium nao instalado e sem o
# marcador ~/.config/VSCodium/.kit-ide: o kit ainda nao rodou neste host).
#
# --sem-gopls-funcional: o `gopls check cmd/build/main.go` mede 28,6 s e 3,8 GB de
# RSS no notebook, e a suite diaria roda no servidor de producao com o earlyoom
# armado (decisao do orquestrador, 2026-09-23). A parte ESTATICA do gopls
# (gopls-do-toolchain: toolchain do go.mod e pino) continua aqui; a funcional
# roda no `ops/ide/instalar-ide.sh --verificar --completo` e na E2E.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
exec python3 tools/check-ide-host --sem-gopls-funcional
