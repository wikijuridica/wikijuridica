#!/usr/bin/env bash
# test_ide_ponta_a_ponta.sh — a ponte /ide com o VSCodium real em :99, na
# qualidade diaria (glob tools/test_*.sh de tools/run-qualidade-diaria; teto de
# 600 s; saida 75 = infra, fora da conta de vermelhos).
#
# Roda ops/ide/testa-ide-ponta-a-ponta.sh --agendada (plano §11.3):
#   * SEM modelo — o `claude --ide` interativo (numa janela tmux propria, a
#     forma que conecta; `claude -p --ide` nao conecta) e so do --completo;
#   * SEM subir display — a execucao agendada nao sobe o :99. Se a unit
#     wikijuridica-xvfb99.service estiver parada, a bancada sai 75; ela nunca a
#     para, e nunca toca a tela do dono;
#   * sem codium instalado (o kit ainda nao rodou neste host), 75;
#   * a evidencia vai para o stdout, que o runner guarda — a execucao agendada
#     nao deixa arquivo em .agents/runtime/;
#   * o teto de RSS do gopls e 3.447 MB: o pico MEDIDO na E2E real de 2026-09-23
#     (2.756 MB de VmHWM, /opt/wiki aberto e cmd/build/main.go carregado; em
#     .agents/runtime/ide-bancada/20260923-095713/gopls-rss.txt) x 1,25. A
#     "aspiracao de 2 GB" do plano nao foi atendida — e fato registrado, e o gate
#     e o medido. A 2a E2E do dia (12:57, cache do gopls quente e sem main.go
#     aberto) mediu 583 MB; o teto fica. Nova medicao troca o numero aqui e no
#     padrao da bancada.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
exec bash ops/ide/testa-ide-ponta-a-ponta.sh --agendada --teto-rss-gopls 3447
