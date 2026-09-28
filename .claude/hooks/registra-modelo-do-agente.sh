#!/usr/bin/env bash
# registra-modelo-do-agente.sh — PostToolUse:Agent (projeto /opt/wiki)
#
# GRAVA, a cada chamada da ferramenta Agent, uma linha JSON em
# .agents/runtime/contexto/modelos-<AAAA-MM-DD>.jsonl: quando, a sessão, o agentId, o
# subagent_type, o modelo PEDIDO (tool_input.model) e o modelo em que o subagente de fato
# COMEÇOU (tool_response.resolvedModel), mais status e modelsUsed quando vierem.
#
# POR QUE. A ordem do dono de 2026-09-22 fixa o modelo de cada papel, e block-agent-haiku.sh
# confere o modelo ANTES da chamada, pela ordem de resolução documentada. O que de fato rodou só o
# harness sabe, e ele o entrega aqui: "resolvedModel — Model the subagent started on, which may
# differ from the requested model" (https://code.claude.com/docs/en/hooks, ferramenta Agent;
# também em lançamento em segundo plano, status "async_launched"). Este registro é a autoridade da
# alocação: a primeira linha "Modelo:" de cada entrega se confere contra ele.
#
# NUNCA BLOQUEIA: sai 0 sempre — a chamada já aconteceu. Quando o modelo resolvido é Haiku, ou de
# família diferente da pedida, devolve additionalContext ao orquestrador (PostToolUse aceita o
# campo) para ele reabrir a frente no modelo certo.
#
# CUSTO: um python3 -I -S (sem site, só stdlib) por chamada de Agent, nunca por Bash (matcher
# "Agent", e a saída barata abaixo antes de qualquer processo). Sem python3, bash puro, sem processo
# externo além de um mkdir quando a pasta ainda não existe. Régua da casa: 300 ms
# (tools/check-modo-operacional --max-ms 300); medido em 2026-09-23: ~24 ms no contêiner de
# validação, ~100 ms na VM da ponte (sistema de arquivos montado), e no host se mede na hora.
set -uo pipefail
trap 'exit 0' ERR

INPUT=""
IFS= read -r -d '' INPUT || true
if [ -z "$INPUT" ]; then exit 0; fi
# Saída barata antes de qualquer processo: só payload da ferramenta Agent (ou o nome legado Task)
# segue; o matcher do settings.json já é "Agent", e isto é defesa em profundidade sem custo.
re_agente='"tool_name"[[:space:]]*:[[:space:]]*"(Agent|Task)"'
[[ "$INPUT" =~ $re_agente ]] || exit 0

DIR="${BASH_SOURCE[0]%/*}"
if [ "$DIR" = "${BASH_SOURCE[0]}" ]; then DIR=.; fi
RAIZ="${CLAUDE_PROJECT_DIR:-$DIR/../..}"

read -r -d '' REGISTRA <<'PY' || true
import datetime, json, os, sys

raiz = sys.argv[1]
try:
    dados = json.loads(sys.stdin.read())
except ValueError:
    sys.exit(0)
if not isinstance(dados, dict) or dados.get("tool_name") not in ("Agent", "Task"):
    sys.exit(0)
entrada = dados.get("tool_input") if isinstance(dados.get("tool_input"), dict) else {}
resposta = dados.get("tool_response") if isinstance(dados.get("tool_response"), dict) else {}
agora = datetime.datetime.now().astimezone()
dia = agora.strftime("%Y-%m-%d")
linha = {
    "ts": agora.isoformat(timespec="seconds"),
    "sessao": dados.get("session_id"),
    "agentId": resposta.get("agentId"),
    "subagent_type": entrada.get("subagent_type") or "general-purpose",
    "model_pedido": entrada.get("model"),
    "resolvedModel": resposta.get("resolvedModel"),
    "modelsUsed": resposta.get("modelsUsed") or None,
    "status": resposta.get("status"),
    "lancado_por": dados.get("agent_type"),
}
linha = {chave: valor for chave, valor in linha.items() if valor is not None}
try:
    pasta = os.path.join(raiz, ".agents", "runtime", "contexto")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "modelos-" + dia + ".jsonl"), "a", encoding="utf-8") as saida:
        saida.write(json.dumps(linha, ensure_ascii=False) + "\n")
except OSError:
    pass


def familia(modelo):
    modelo = str(modelo or "").lower()
    return next((f for f in ("haiku", "sonnet", "opus", "fable") if f in modelo), "")


rodou = [resposta.get("resolvedModel")] + list(resposta.get("modelsUsed") or [])
avisos = []
if any(familia(m) == "haiku" for m in rodou):
    avisos.append("rodou em Haiku, que a ordem do dono de 2026-09-22 proíbe")
pedida, resolvida = familia(entrada.get("model")), familia(resposta.get("resolvedModel"))
if pedida and resolvida and pedida != resolvida:
    avisos.append(f"foi pedido em {pedida} e começou em {resolvida}")
if avisos:
    texto = (f"registra-modelo-do-agente: o subagente {linha.get('agentId', '?')} ({linha['subagent_type']}) "
             + "; ".join(avisos) + f". Registro: .agents/runtime/contexto/modelos-{dia}.jsonl; papel de cada modelo: "
             + "docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md §3.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": texto}},
                     ensure_ascii=False))
PY

if command -v python3 >/dev/null 2>&1; then
	printf '%s' "$INPUT" | python3 -I -S -c "$REGISTRA" "$RAIZ" 2>/dev/null
	exit 0
fi

# Sem python3: os campos saem por expressão regular do bash, sem processo. O valor entre aspas de
# um JSON válido já está escapado, então volta ao JSON como está.
re_ferramenta='"tool_name"[[:space:]]*:[[:space:]]*"(Agent|Task)"'
[[ "$INPUT" =~ $re_ferramenta ]] || exit 0
campo() {
	local re="\"$1\"[[:space:]]*:[[:space:]]*\"([^\"]*)\""
	if [[ "$INPUT" =~ $re ]]; then printf '%s' "${BASH_REMATCH[1]}"; fi
}
printf -v dia '%(%Y-%m-%d)T' -1
printf -v ts '%(%Y-%m-%dT%H:%M:%S%z)T' -1
pasta="$RAIZ/.agents/runtime/contexto"
[ -d "$pasta" ] || mkdir -p "$pasta" 2>/dev/null || exit 0
resolvido="$(campo resolvedModel)"
printf '{"ts":"%s","sessao":"%s","agentId":"%s","subagent_type":"%s","model_pedido":"%s","resolvedModel":"%s","juiz":"bash"}\n' \
	"$ts" "$(campo session_id)" "$(campo agentId)" "$(campo subagent_type)" "$(campo model)" "$resolvido" \
	>>"$pasta/modelos-$dia.jsonl" 2>/dev/null || true
if [[ "${resolvido,,}" == *haiku* ]]; then
	printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"registra-modelo-do-agente: o subagente rodou em Haiku (%s), que a ordem do dono de 2026-09-22 proíbe. Registro: .agents/runtime/contexto/modelos-%s.jsonl."}}\n' \
		"$resolvido" "$dia"
fi
exit 0
