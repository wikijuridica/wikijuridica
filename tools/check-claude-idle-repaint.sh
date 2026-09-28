#!/bin/bash
# Um TUI do Claude Code OCIOSO, numa sessão detached, repinta sozinho?
#
# A pergunta fecha o desenho do relógio do ai-session-reaper. Se `window_activity`
# renova com output (medido em check-tmux-activity-clock), ele só serve de relógio
# caso o TUI PARADO fique mudo. Se o spinner, o relógio do rodapé ou qualquer
# animação repintarem sozinhos, `window_activity` nunca congela — e o reaper
# jamais encerraria nada, voltando ao vazamento original.
#
# Sessão própria com prefixo `idleprobe-`, fora do escopo de qualquer reaper.

set -uo pipefail
S="idleprobe-$$"
JANELA="${1:-120}"

limpar() { tmux kill-session -t "$S" 2>/dev/null; }
trap limpar EXIT INT TERM

campo() { tmux display-message -p -t "$S" "$1" 2>/dev/null; }

tmux new-session -d -s "$S" -x 120 -y 40 \
	'cd /opt/wiki && claude --permission-mode bypassPermissions' 2>/dev/null || {
	echo "não foi possível criar a sessão"
	exit 2
}

echo "sessão: $S — aguardando o Claude terminar o startup e ficar ocioso no prompt"
# o startup produz output; espera window_activity estabilizar por 15s seguidos
estavel=0
ant=0
for _ in $(seq 1 90); do
	command sleep 1
	wa=$(campo '#{window_activity}')
	[ -z "$wa" ] && continue
	if [ "$wa" = "$ant" ]; then estavel=$((estavel + 1)); else estavel=0; fi
	ant="$wa"
	[ "$estavel" -ge 15 ] && break
done
echo "  startup terminou (window_activity parado há ${estavel}s)"
echo

wa0=$(campo '#{window_activity}')
sa0=$(campo '#{session_activity}')
t0=$(date +%s)
echo "  marco zero: window_activity=$wa0  session_activity=$sa0"

for _ in $(seq 1 $((JANELA / 20))); do
	command sleep 20
	wa=$(campo '#{window_activity}')
	sa=$(campo '#{session_activity}')
	printf '  t=%3ss  window_activity Δ%-4s  session_activity Δ%s\n' \
		"$(($(date +%s) - t0))" "$((wa - wa0))" "$((sa - sa0))"
done

wa=$(campo '#{window_activity}')
dwa=$((wa - wa0))
dt=$(($(date +%s) - t0))
echo
if [ "$dwa" -le 5 ]; then
	echo "  VEREDITO: o TUI ocioso fica MUDO (${dwa}s de avanço em ${dt}s)."
	echo "            window_activity congela quando não há trabalho — serve de relógio."
	exit 0
fi
echo "  VEREDITO: o TUI ocioso REPINTA sozinho (${dwa}s de avanço em ${dt}s)."
echo "            window_activity nunca congela; sozinho não distingue parado de ativo."
exit 1
