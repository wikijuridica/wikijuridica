#!/usr/bin/env bash
# block-write-fora-de-contexto.sh — PreToolUse (Write|Edit|MultiEdit|NotebookEdit|Bash), projeto /opt/wiki
#
# BARRA: agente de contexto (Sonnet 5) escrevendo fora de .agents/runtime/contexto/.
#
# Ordem do dono, 2026-09-22: "sonnet 5 somente para ganhar contexto de forma eficiente, sem
# editar". Os agentes do roster que rodam em Sonnet 5 estão em AGENTES_RESTRITOS, e para eles:
#   - Write/Edit/MultiEdit/NotebookEdit só em .agents/runtime/contexto/, na memória do próprio
#     agente (.claude/agent-memory/<nome>/) e no scratchpad da sessão;
#   - Bash é leitura e medição, julgado por lista de permissão em lib/guarda_de_escrita.py.
# Quem edita código, dado, conteúdo, gate, hook, teste e página é a onda de execução (Opus 5.5).
#
# DOIS PONTOS DE REGISTRO, porque cada um cobre um buraco do outro:
#   1. frontmatter de .claude/agents/documentador-de-contexto.md, com --sempre: roda só enquanto
#      aquele agente existe. A doc oficial avisa que hook de frontmatter de subagente de projeto
#      NÃO roda em sessão -p nem em pasta sem confiança aceita
#      (https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents);
#   2. .claude/settings.json, sem argumento: roda em toda chamada, inclusive em -p, e julga pelo
#      campo agent_type do payload, que o harness preenche dentro de subagente
#      (https://code.claude.com/docs/en/hooks#common-input-fields).
#
# CUSTO: no registro do settings.json este hook roda em TODA chamada Bash do repositório. O
# caminho de 99% delas sai sem criar processo: se o payload não contém o nome de nenhum agente
# restrito, o agente não é restrito — e o hook termina em expansão de parâmetro do bash, como a
# otimização de 2026-07-28 de block-heavy-go.sh exige. Menção ao nome no TEXTO do comando só
# custa um python3, que lê o agent_type de verdade.
#
# LADO SEGURO: para agente restrito, não conseguir julgar é barrar (falso positivo é visível e
# corrigível; falso negativo é silencioso — block-display-zero-social.sh). Para os demais, o
# hook nunca barra.

AGENTES_RESTRITOS="documentador-de-contexto investigador"

set -uo pipefail
trap 'exit 0' ERR

MODO=roster
if [ "${1:-}" = "--sempre" ]; then MODO=sempre; fi

# Leitura por `read` embutido: com um PATH sem `cat` (medido pelo red team de 2026-09-22), `$(cat)`
# voltava vazio e o hook saía 0 até no modo --sempre.
INPUT=""
IFS= read -r -d '' INPUT || true
if [ -z "$INPUT" ]; then
	if [ "$MODO" = sempre ]; then
		printf '%s\n' "Payload vazio: a guarda de escrita do documentador-de-contexto não conseguiu conferir o destino e, para agente de contexto, não conferir é barrar." >&2
		exit 2
	fi
	exit 0
fi

if [ "$MODO" = roster ]; then
	menciona=0
	for agente in $AGENTES_RESTRITOS; do
		if [[ "$INPUT" == *"$agente"* ]]; then
			menciona=1
			break
		fi
	done
	if [ "$menciona" = 0 ]; then exit 0; fi
fi

DIR="${BASH_SOURCE[0]%/*}"
if [ "$DIR" = "${BASH_SOURCE[0]}" ]; then DIR=.; fi
RAIZ="${CLAUDE_PROJECT_DIR:-$DIR/../..}"

# shellcheck source=lib/bloqueio.sh
if ! . "$DIR/lib/bloqueio.sh" 2>/dev/null; then
	# Sem a biblioteca, o bloqueio continua possível: exit 2 com stderr é o contrato mínimo.
	bloqueia() {
		printf '%s\n%s\n' "$1" "$2" >&2
		exit 2
	}
fi

# O ensino diz o que fazer, com caminho — hook que só nega não ensina nada (lib/bloqueio.sh).
ENSINO="Você é agente de contexto (Sonnet 5) — ordem do dono, 2026-09-22: colher contexto, sem editar.
Onde você escreve (caminho RELATIVO à raiz, não \$CLAUDE_PROJECT_DIR/... — o destino calculado barra):
  .agents/runtime/contexto/<AAAA-MM-DD>-<frente>-<tema>.md  (o mapa da onda, com Write)
  .claude/agent-memory/<seu-nome>/                          (a sua memória)
  /tmp/... (rascunho não versionado; fora do repositório)
Bash, para você, é leitura e medição: git log/show/diff/blame/status, git branch/tag só listando,
rg/grep, wc, sha256sum, ls, stat, date, find sem -delete/-exec de escrita, jq, sqlite3 só com
SELECT, curl GET sem -o, ./tools/check-*, python3 -c/heredoc com código LITERAL entre aspas simples.
Achou o que precisa mudar? Registre no mapa com arquivo:linha e o comando que reproduz;
quem edita é a onda de execução (Opus 5.5: engenheiro-go, redator-juridico), e quem
commita é o orquestrador (Fable 5.1)."

veredito=""
if command -v python3 >/dev/null 2>&1; then
	# shellcheck disable=SC2086
	veredito="$(printf '%s' "$INPUT" | python3 -I -S "$DIR/lib/guarda_de_escrita.py" "$MODO" "$RAIZ" $AGENTES_RESTRITOS 2>/dev/null)" || veredito=""
fi

case "$veredito" in
PASSA)
	exit 0
	;;
BLOQUEIA*)
	resto="${veredito#BLOQUEIA$'\t'}"
	agente="${resto%%$'\t'*}"
	motivo="${resto#*$'\t'}"
	bloqueia \
		"Escrita barrada para o agente de contexto ${agente}: ${motivo}. Ordem do dono, 2026-09-22: Sonnet 5 colhe contexto e não edita." \
		"$ENSINO"
	;;
ILEGIVEL)
	if [ "$MODO" = sempre ]; then
		bloqueia "Payload ilegível: a guarda de escrita do documentador-de-contexto não conseguiu conferir o destino e, para agente de contexto, não conferir é barrar." "$ENSINO"
	fi
	exit 0
	;;
esac

# O juiz não rodou (python3 ausente ou quebrado). Para agente restrito o lado seguro é barrar;
# o agent_type sai por expansão de parâmetro, sem processo.
agente_payload=""
if [[ "$INPUT" == *'"agent_type"'* ]]; then
	agente_payload="${INPUT#*\"agent_type\"}"
	agente_payload="${agente_payload#*\"}"
	agente_payload="${agente_payload%%\"*}"
fi
restrito=0
if [ "$MODO" = sempre ]; then restrito=1; fi
for agente in $AGENTES_RESTRITOS; do
	if [ "$agente_payload" = "$agente" ]; then restrito=1; fi
done
if [ "$restrito" = 1 ]; then
	bloqueia "A guarda de escrita não conseguiu julgar (python3 ausente ou lib/guarda_de_escrita.py com erro) e, para agente de contexto, não julgar é barrar. Rode: python3 .claude/hooks/block-write-fora-de-contexto.test.py" "$ENSINO"
fi
exit 0
