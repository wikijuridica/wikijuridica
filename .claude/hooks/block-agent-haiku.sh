#!/usr/bin/env bash
# block-agent-haiku.sh — PreToolUse:Agent (projeto /opt/wiki)
#
# BARRA, pela ordem do dono de 2026-09-22 ("Haiyco é proibido"; "sonnet 5 somente para ganhar
# contexto"), dois subagentes:
#   1. o que rodaria em Haiku — em qualquer forma, por qualquer caminho;
#   2. o que rodaria em Sonnet num agente que pode editar fora de .agents/runtime/contexto/.
# Sonnet passa só em agente sob a guarda de escrita (AGENTES_RESTRITOS de
# block-write-fora-de-contexto.sh: investigador, documentador-de-contexto) ou em agente cujo
# `tools:` declara só ferramentas que não gravam (Read, Grep, Glob, WebFetch, WebSearch). Opus 5.5
# executa, Fable 5.1 orquestra e refuta: esses passam sempre.
#
# POR QUE HOOK, E NÃO SÓ PROSA. O CLAUDE.md chega ao modelo como mensagem de usuário, "there's no
# guarantee of strict compliance" (https://code.claude.com/docs/en/memory); para barrar uma ação
# independentemente do que o modelo decidir, a doc manda um PreToolUse com exit 2
# (https://code.claude.com/docs/en/hooks#exit-code-2). De 2026-09-15 a 2026-09-22 a prosa dizia
# uma coisa e o frontmatter do investigador rodava Haiku: prosa não é mecanismo.
#
# O QUE SE CONFERE é o modelo EFETIVO, na ordem de resolução documentada
# (https://code.claude.com/docs/en/sub-agents#choose-a-model):
#   1. o parâmetro `model` da chamada (tool_input.model);
#   2. o `model` do frontmatter do agente nomeado em subagent_type — projeto antes de usuário;
#      embutidos pela tabela oficial: claude-code-guide roda em Haiku, statusline-setup em Sonnet,
#      Explore/Plan herdam;
#   3. CLAUDE_CODE_SUBAGENT_MODEL, para agente sem modelo próprio;
#   e CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1 põe a variável na frente de tudo.
# "haiku" em qualquer caixa e em ID completo (claude-haiku-4-5-20251001) barra, mesmo com
# ANTHROPIC_DEFAULT_HAIKU_MODEL redirecionando o alias: a ordem proíbe o nome. Alias remapeado por
# ANTHROPIC_DEFAULT_{SONNET,OPUS,FABLE}_MODEL vale pelo modelo para onde aponta.
#
# QUEM PODE EDITAR, para a regra do Sonnet: embutido (general-purpose, claude, fork, Explore, Plan,
# statusline-setup, claude-code-guide — todos com escrita ou Bash); agente sem `tools:` (herda
# todas); agente com `memory:` ("Read, Write, and Edit tools are automatically enabled",
# https://code.claude.com/docs/en/sub-agents#enable-persistent-memory) ou `mcpServers:`; agente
# com qualquer ferramenta fora da lista de leitura, Bash incluído. Falso positivo aqui é visível e
# se corrige com model: "opus"; falso negativo é Sonnet editando sem ninguém ver.
#
# FORA DO ALCANCE, declarado: agentes que um script de Workflow lança não passam pela ferramenta
# Agent (o teste de contrato varre scripts/workflows/ atrás de haiku); agente de plugin não é lido
# (a definição mora fora de .claude/agents/); e o modelo da SESSÃO não chega ao hook — ele é
# fixado por "model": "fable" no .claude/settings.json.
#
# FALHA: payload ilegível não barra — avisa o modelo (additionalContext) de que a proibição não
# foi conferida naquela chamada. Sem python3, confere só o parâmetro `model`, em bash puro.
set -uo pipefail
trap 'exit 0' ERR

# Leitura por `read` embutido: com um PATH sem `cat` (medido pelo red team de 2026-09-22), `$(cat)`
# voltava vazio e o hook saía 0 antes de olhar o modelo.
INPUT=""
IFS= read -r -d '' INPUT || true
if [ -z "$INPUT" ]; then exit 0; fi

DIR="${BASH_SOURCE[0]%/*}"
if [ "$DIR" = "${BASH_SOURCE[0]}" ]; then DIR=.; fi
RAIZ="${CLAUDE_PROJECT_DIR:-$DIR/../..}"
# shellcheck source=lib/bloqueio.sh
. "$DIR/lib/bloqueio.sh" 2>/dev/null || exit 0

read -r -d '' RESOLVE_MODELO <<'PY' || true
import json, os, re, sys

raiz, casa, pasta_do_hook = sys.argv[1], sys.argv[2], sys.argv[3]

# Tabela oficial dos embutidos (https://code.claude.com/docs/en/sub-agents, "Built-in subagents").
# "" = sem modelo próprio (segue a ordem); "inherit" = herda a sessão, e a variável sozinha não o
# alcança.
EMBUTIDOS = {"general-purpose": "", "claude": "", "Explore": "inherit", "Plan": "inherit",
             "fork": "inherit", "statusline-setup": "sonnet", "claude-code-guide": "haiku"}
ALIAS_ENV = {"sonnet": "ANTHROPIC_DEFAULT_SONNET_MODEL", "opus": "ANTHROPIC_DEFAULT_OPUS_MODEL",
             "fable": "ANTHROPIC_DEFAULT_FABLE_MODEL"}
# Ferramentas que não gravam arquivo. Bash não está aqui: ele escreve.
SO_LEITURA = {"Read", "Grep", "Glob", "WebFetch", "WebSearch", "TodoWrite", "LS", "NotebookRead"}


def limpa(valor):
    if not isinstance(valor, str):
        return ""
    valor = valor.strip()
    if valor[:1] in ("'", '"'):
        fim = valor.find(valor[0], 1)
        return valor[1:fim].strip() if fim > 0 else valor[1:].strip()
    return valor.split(" #", 1)[0].strip()


INDICADORES_DE_BLOCO = ("", "|", ">", "|-", ">-", "|+", ">+")


def frontmatter(caminho):
    """Chaves de topo; item de lista YAML ("  - Read") vai para "<chave>[]", e chave com bloco
    indentado de qualquer forma ganha "<chave>+". BOM e linhas vazias antes do `---` não escondem
    o frontmatter, e escalar em bloco (`model:` e o valor na linha de baixo) vale como valor — os
    dois passavam pelo hook (red team, 2026-09-22)."""
    try:
        with open(caminho, encoding="utf-8-sig") as arquivo:
            linhas = arquivo.read().replace("\r\n", "\n").split("\n")
    except (OSError, UnicodeDecodeError):
        return {}
    while linhas and not linhas[0].strip():
        linhas = linhas[1:]
    if not linhas or linhas[0].strip() != "---":
        return {}
    chaves, atual, escalar = {}, "", {}
    for linha in linhas[1:]:
        if linha.strip() == "---":
            break
        if linha[:1] in (" ", "\t"):
            item = linha.strip()
            if atual and item:
                chaves[atual + "+"] = True
            if atual and item.startswith("- "):
                chaves.setdefault(atual + "[]", []).append(limpa(item[2:]))
            elif atual in escalar and item and not re.match(r"[\w-]+\s*:(\s|$)", item):
                escalar[atual].append(item)
                chaves[atual] = limpa(" ".join(escalar[atual]))
            continue
        if ":" not in linha:
            atual = ""
            continue
        chave, _, valor = linha.partition(":")
        atual = chave.strip()
        chaves[atual] = limpa(valor)
        if chaves[atual] in INDICADORES_DE_BLOCO:
            escalar[atual] = []
    return chaves


def lista(campos, chave):
    itens = list(campos.get(chave + "[]", []))
    valor = campos.get(chave, "").strip().strip("[]")
    itens += [parte for parte in valor.split(",")]
    nomes = []
    for item in itens:
        nome = limpa(item).split("(", 1)[0].strip().strip("'\"")
        if nome:
            nomes.append(nome)
    return nomes


def definicao(tipo):
    for base in (os.path.join(raiz, ".claude", "agents"), os.path.join(casa, ".claude", "agents") if casa else ""):
        if not base or not os.path.isdir(base):
            continue
        for pasta, _, arquivos in sorted(os.walk(base)):
            for nome in sorted(arquivos):
                if nome.endswith(".md"):
                    caminho = os.path.join(pasta, nome)
                    campos = frontmatter(caminho)
                    if campos.get("name") == tipo:
                        return campos, os.path.relpath(caminho, raiz) if base.startswith(raiz) else caminho
    if tipo in EMBUTIDOS:
        return {"model": EMBUTIDOS[tipo], "embutido": "sim"}, "embutido do Claude Code"
    return None, None


def guardados():
    """AGENTES_RESTRITOS da guarda de escrita: lista única, lida de onde ela é aplicada."""
    try:
        with open(os.path.join(pasta_do_hook, "block-write-fora-de-contexto.sh"), encoding="utf-8") as arquivo:
            achado = re.search(r'^AGENTES_RESTRITOS="([^"]*)"', arquivo.read(), re.M)
    except OSError:
        return set()
    return set(achado.group(1).split()) if achado else set()


def aponta(modelo):
    """O modelo para onde o nome aponta: alias remapeado vale pelo destino."""
    minusculo = (modelo or "").strip().lower()
    alias = minusculo.replace("[1m]", "")
    if alias in ALIAS_ENV:
        destino = os.environ.get(ALIAS_ENV[alias], "").strip().lower()
        if destino:
            return destino
    return minusculo


def eh_haiku(modelo):
    return "haiku" in (modelo or "").lower() or "haiku" in aponta(modelo)


def eh_sonnet(modelo):
    return "sonnet" in aponta(modelo)


def por_que_edita(tipo, campos):
    """None se o agente não grava fora de .agents/runtime/contexto/; senão, o motivo."""
    if tipo in guardados():
        return None
    if campos is None:
        return "não foi achado em .claude/agents/ nem em ~/.claude/agents/, então nada garante que só leia"
    if campos.get("embutido"):
        return "é embutido do Claude Code, com ferramenta de escrita ou Bash"
    if campos.get("memory") or campos.get("memory+"):
        return "declara memory:, que habilita Write e Edit sozinho"
    if campos.get("mcpServers") or campos.get("mcpServers+"):
        return "declara mcpServers:, ferramentas que a guarda de escrita não vê"
    declaradas = lista(campos, "tools")
    if not declaradas:
        return "não declara tools: e herda todas, inclusive as de escrita"
    negadas = set(lista(campos, "disallowedTools"))
    escrevem = sorted(set(declaradas) - negadas - SO_LEITURA)
    if escrevem:
        return "declara " + ", ".join(escrevem) + " em tools:"
    return None


try:
    dados = json.loads(sys.stdin.read())
except ValueError:
    print("ILEGIVEL")
    sys.exit(0)
if not isinstance(dados, dict) or not isinstance(dados.get("tool_input"), dict):
    print("ILEGIVEL")
    sys.exit(0)
if dados.get("tool_name") not in ("Agent", "Task"):
    print("PASSA")
    sys.exit(0)

entrada = dados["tool_input"]
parametro = limpa(entrada.get("model"))
tipo = limpa(entrada.get("subagent_type")) or "general-purpose"
variavel = limpa(os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL"))
if variavel.lower() == "inherit":
    variavel = ""
forcado = os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "").strip().lower() in ("1", "true", "yes", "on")
campos, origem = definicao(tipo)

efetivo, fonte = "", ""
if forcado and variavel:
    efetivo, fonte = variavel, "CLAUDE_CODE_SUBAGENT_MODEL com CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1"
elif parametro:
    efetivo, fonte = parametro, "o parâmetro model da chamada"
else:
    modelo = None if campos is None else campos.get("model", "")
    if modelo and modelo.lower() != "inherit":
        efetivo, fonte = modelo, f"o frontmatter de {tipo} ({origem})"
    elif modelo is None or modelo == "":
        if variavel:
            efetivo, fonte = variavel, "CLAUDE_CODE_SUBAGENT_MODEL"

motivo = por_que_edita(tipo, campos) if efetivo and eh_sonnet(efetivo) else None
if efetivo and eh_haiku(efetivo):
    print("\t".join(("BLOQUEIA", fonte, efetivo, tipo)))
elif motivo:
    print("\t".join(("SONNET", fonte, efetivo, tipo, motivo)))
else:
    print("PASSA")
PY

veredito=""
if command -v python3 >/dev/null 2>&1; then
	veredito="$(printf '%s' "$INPUT" | python3 -I -S -c "$RESOLVE_MODELO" "$RAIZ" "${HOME:-}" "$DIR" 2>/dev/null)" || veredito=""
fi

ENSINO='Escolha o modelo pelo papel (ordem do dono, 2026-09-22):
  contexto — ler, mapear, medir, documentar no disco: subagent_type "investigador" (só lê) ou "documentador-de-contexto" (grava em .agents/runtime/contexto/), que já rodam em Sonnet 5;
  execução — código, dado, gate, hook, teste, conteúdo por gerador: model: "opus", ou "engenheiro-go" / "redator-juridico";
  refutação e itens graves: model: "fable", ou "auditor-adversarial" / "especialista-critico".
Sonnet só roda em agente que não edita: os dois de contexto acima, sob a guarda block-write-fora-de-contexto.sh, ou agente com tools: só de leitura (Read, Grep, Glob, WebFetch, WebSearch). Embutido (general-purpose, Explore, Plan, statusline-setup, claude-code-guide) roda com model: "opus".
Se a definição do agente declara haiku, ou sonnet com escrita, corrija o frontmatter em .claude/agents/ — internal/contract/misc/alocacao_de_modelos_test.go reprova.
Pergunta sobre o próprio Claude Code: documentador-de-contexto com WebFetch em https://code.claude.com/docs/en/<página>.md, em vez do claude-code-guide, que roda em Haiku.
Mapa completo: docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md §3–§4.'

case "$veredito" in
PASSA)
	exit 0
	;;
BLOQUEIA*)
	IFS=$'\t' read -r _ fonte modelo tipo <<<"$veredito"
	bloqueia \
		"Subagente em Haiku barrado: ${fonte} resolve '${tipo}' para '${modelo}'. Ordem do dono, 2026-09-22: Haiku é proibido neste projeto — sonnet para contexto (investigador, documentador-de-contexto), opus para execução, fable para refutar." \
		"$ENSINO"
	;;
SONNET*)
	IFS=$'\t' read -r _ fonte modelo tipo motivo <<<"$veredito"
	bloqueia \
		"Subagente em Sonnet barrado: ${fonte} resolve '${tipo}' para '${modelo}', e '${tipo}' ${motivo}. Ordem do dono, 2026-09-22: Sonnet 5 só colhe contexto e não edita arquivo versionado — contexto com investigador ou documentador-de-contexto, execução com opus." \
		"$ENSINO"
	;;
ILEGIVEL)
	avisa "block-agent-haiku: payload ilegível; a alocação de modelos (ordem do dono, 2026-09-22) não foi conferida nesta chamada. Confira o modelo do subagente em /tasks."
	;;
esac

# Sem o juiz (python3 ausente ou com erro): confere o parâmetro model em bash puro, sem processo.
minusculo="${INPUT,,}"
re_haiku='"model"[[:space:]]*:[[:space:]]*"[^"]*haiku'
if [[ "$minusculo" =~ $re_haiku ]]; then
	bloqueia \
		"Subagente em Haiku barrado: o parâmetro model da chamada pede Haiku. Ordem do dono, 2026-09-22: Haiku é proibido neste projeto — sonnet para contexto (investigador, documentador-de-contexto), opus para execução, fable para refutar." \
		"$ENSINO"
fi
re_sonnet='"model"[[:space:]]*:[[:space:]]*"[^"]*sonnet'
if [[ "$minusculo" =~ $re_sonnet ]]; then
	re_tipo='"subagent_type"[[:space:]]*:[[:space:]]*"([^"]*)"'
	tipo=""
	if [[ "$INPUT" =~ $re_tipo ]]; then tipo="${BASH_REMATCH[1]}"; fi
	guardados=""
	if [ -r "$DIR/block-write-fora-de-contexto.sh" ]; then
		while IFS= read -r linha; do
			case "$linha" in
			AGENTES_RESTRITOS=*)
				guardados="${linha#AGENTES_RESTRITOS=\"}"
				guardados="${guardados%%\"*}"
				break
				;;
			esac
		done <"$DIR/block-write-fora-de-contexto.sh"
	fi
	if [ -n "$tipo" ]; then
		case " $guardados " in
		*" $tipo "*) exit 0 ;;
		esac
	fi
	bloqueia \
		"Subagente em Sonnet barrado: o parâmetro model pede Sonnet para '${tipo:-general-purpose}', que não está sob a guarda de escrita. Ordem do dono, 2026-09-22: Sonnet 5 só colhe contexto e não edita arquivo versionado — contexto com investigador ou documentador-de-contexto, execução com opus." \
		"$ENSINO"
fi
avisa "block-agent-haiku: o juiz em python3 não rodou; só o parâmetro model foi conferido nesta chamada (ordem do dono, 2026-09-22: Haiku é proibido, e Sonnet só colhe contexto)."
