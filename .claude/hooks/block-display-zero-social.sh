#!/usr/bin/env bash
# block-display-zero-social.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# BARRA: automacao de navegador/janela apontada para o display :0.
# O :0 e' a sessao grafica do titular, e nela vive a VM com PJe/e-SAJ e o token
# de assinatura. Teclado e mouse enviados para la alcancam o processo judicial
# do dono; e uma captura da tela cheia leva junto o que estiver aberto.
# O display do agente e' :99 (Xvfb), inalcancavel por construcao.
#
# NAO barra: `tools/publicar-perfis-sociais` (o wrapper ja forca :99, com a
# excecao unica de --login, em que o TITULAR digita a credencial), nem
# diagnostico que nao dirige entrada (xdpyinfo, xrandr), nem TEXTO que cita :0.
#
# ---------------------------------------------------------------------------
# DOIS FALSOS POSITIVOS MEDIDOS EM 2026-09-16, e por que eles eram graves
# ---------------------------------------------------------------------------
# A versao anterior casava a ferramenta por SUBSTRING crua:
#
#     for f in ... import ... ; do [[ "$INPUT" == *"$f"* ]] && dirige=1
#
# `import` e' o comando de captura do ImageMagick — e tambem a primeira palavra
# de quase todo script Python, Go, JS e TS. E o teste do `:0` casava a sequencia
# em QUALQUER posicao, inclusive dentro de prosa, hora (`12:04:53`) e fatia
# (`texto[:0]`).
#
# Sozinho, nenhum dos dois bloqueava; juntos, barravam trabalho legitimo. Medido:
# um `python3` que so reescrevia texto de um documento foi barrado, e o texto era
# a propria DOCUMENTACAO desta regra, citando `:0`.
#
# O custo do falso positivo aqui nao e' o atraso: guarda que barra o comando
# inocente ensina a contorna-la, e guarda contornada nao protege a VM com o
# token de assinatura. **A guarda so vale enquanto for CRIVEL.**
#
# O PREDICADO AGORA TEM TRES ETAPAS, e cada uma tem controle negativo na bancada:
#   1. o `:0` tem de ser VALOR DE DISPLAY ou token isolado;
#   2. a ferramenta tem de estar em POSICAO DE COMANDO — primeiro token de uma
#      linha ou de um segmento separado por ; | && || ( ), descontados prefixos
#      transparentes (env, sudo, nohup, timeout N) e atribuicoes (DISPLAY=:0);
#   3. `import` exige, alem disso, que o proximo token comece com `-` — e' assim
#      que se chama o do ImageMagick (`import -window root`), e nunca e' assim
#      que se escreve o do Python.
set -uo pipefail
trap 'exit 0' ERR
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
if [ -z "$INPUT" ]; then exit 0; fi

# O wrapper sancionado tem a propria guarda; deixa passar antes de tudo.
if [[ "$INPUT" == *publicar-perfis-sociais* ]]; then exit 0; fi

# O payload chega como JSON inteiro, e a analise POSICIONAL das etapas 2 e 3
# precisa do comando limpo: sobre o JSON, o primeiro token de um segmento seria
# `{"tool_name":"Bash",...` e nenhuma posicao de comando seria reconhecida.
# Medido em 2026-09-16: a primeira versao posicional deixou passar TODOS os casos
# perigosos por isto — e so a bancada acusou, antes de o hook ir para o disco.
#
# A extracao e' de expansao de parametro (zero processo). Sem o campo, cai no
# payload cru, que e' o comportamento das guardas por substring.
# O separador do JSON pode ou nao ter espaco: o harness manda compacto
# ("command":"..."), mas json.dumps do Python manda "command": "...". Medido em
# 2026-09-16: o extrator so casava a forma compacta, entao no teste o COMANDO
# ficava sendo o JSON inteiro e NENHUM caso perigoso era reconhecido. A bancada
# era mais geral que o real e achou a fragilidade antes dela importar.
# O SEPARADOR DO JSON PODE TER ESPACO, e isto ja abriu a guarda (2026-09-16).
# A extracao casava so a forma COMPACTA (`"command":"`). Um produtor que escreve
# `"command": "..."` -- o default do json.dumps do Python, e o que a bancada
# usa -- nao casava; COMANDO caia no JSON INTEIRO e a analise POSICIONAL das
# etapas 2 e 3 passava a procurar posicao de comando dentro de
# `{"tool_name": "Bash", ...`, onde ela nao existe. Medido: os TRES casos
# perigosos (xdotool, virt-viewer, node olhar-pagina) sairam com exit 0. E o
# mesmo fail-open que o comentario acima documenta ter custado a primeira
# versao posicional -- ele voltou pela porta do espaco.
#
# Agora o recorte nao depende do espacamento: anda ate a chave "command" e dai
# ate a PROXIMA aspa, que e a de abertura do valor com ou sem espaco no meio.
COMANDO=""
if [[ "$INPUT" == *'"command"'* ]]; then
	COMANDO="${INPUT#*\"command\"}"
	COMANDO="${COMANDO#*\"}"
	COMANDO="${COMANDO%\"*}"
	COMANDO="${COMANDO//\\\"/\"}"
	COMANDO="${COMANDO//\\n/$'\n'}"
	COMANDO="${COMANDO//\\t/$'\t'}"
	COMANDO="${COMANDO//\\\\/\\}"
fi

# SEM RECORTE, A GUARDA NAO CAI PARA POSICIONAL — ela cai para SUBSTRING.
# Analise posicional sobre texto que nao e uma linha de comando falha ABERTA, e
# esta guarda protege a VM com o token de assinatura do titular: o lado seguro
# do erro aqui e barrar demais, nunca de menos. Falso positivo e visivel e
# corrigivel; falso negativo e silencioso.
MODO_CONSERVADOR=0
if [ -z "${COMANDO// /}" ]; then
	COMANDO="$INPUT"
	MODO_CONSERVADOR=1
fi

# ---------------------------------------------------------------------------
# 1. O :0 tem de ser DISPLAY, nao uma sequencia qualquer.
# ---------------------------------------------------------------------------
aponta_para_zero=0
# DISPLAY=:0 / DISPLAY=:0.0 / --display :0 / --display=:0 / -display :0
if [[ "$COMANDO" =~ (DISPLAY=|--display=|--display[[:space:]]|-display[[:space:]])[[:space:]]*:0(\.[0-9]+)?([^0-9.]|$) ]]; then
	aponta_para_zero=1
# token isolado `:0` ou `:0.0`, cercado de espaco ou fim de linha
elif [[ "$COMANDO" =~ (^|[[:space:]])":0"(\.[0-9]+)?([[:space:]]|$) ]]; then
	aponta_para_zero=1
fi
# ATENCAO: `if`, nunca `[ cond ] && exit 0`.
# Com `trap ... ERR` ativo, uma lista `&&` cuja condicao e FALSA devolve 1, o
# trap dispara e o hook sai com o codigo do trap. Medido em 2026-09-16: com
# `&& exit 0` aqui, TODO caso perigoso passava -- a guarda virava no-op
# exatamente quando tinha de bloquear, e o teste foi o unico a enxergar.
if [ "$aponta_para_zero" = 0 ]; then exit 0; fi

# ---------------------------------------------------------------------------
# 2 e 3. A ferramenta tem de estar em POSICAO DE COMANDO.
# ---------------------------------------------------------------------------
# Ferramentas que dirigem entrada ou capturam a tela. `import` fica na lista
# porque e' o comando de captura do ImageMagick, com a regra extra da etapa 3.
eh_ferramenta() {
	case "${1##*/}" in
	xdotool | wmctrl | virt-viewer | scrot | xwd | ydotool | olhar-pagina | \
		playwright | puppeteer | chromium | chromium-browser | google-chrome | firefox | xdg-open | import)
		return 0
		;;
	esac
	return 1
}

# Prefixos que nao mudam a posicao de comando do que vem depois.
eh_transparente() {
	case "${1##*/}" in
	env | sudo | nohup | exec | command | timeout | nice | stdbuf | setsid | doas) return 0 ;;
	esac
	return 1
}

# INTERPRETADOR + SCRIPT DE AUTOMACAO (lacuna medida em 2026-09-16).
#
# A lista posicional casa `olhar-pagina` como COMANDO, mas a forma que este
# repositorio de fato usa e `node scripts/olhar-pagina.mjs`: ali o comando e
# `node` e o alvo e ARGUMENTO. Medido nas duas formas de payload —
# `DISPLAY=:0 node scripts/olhar-pagina.mjs` saia com exit 0, e e exatamente o
# comando que dirige um navegador para a sessao grafica do titular.
#
# A varredura de ARGUMENTO e mais estreita que a de comando, de proposito:
# `import` fica de fora dela. Em posicao de comando `import` e a captura do
# ImageMagick; como argumento e a primeira palavra de quase todo script — o
# falso positivo que a frente anterior mediu e corrigiu.
eh_interpretador() {
	case "${1##*/}" in
	node | nodejs | deno | bun | python | python3 | ts-node | tsx) return 0 ;;
	esac
	return 1
}

eh_script_de_navegador() {
	local base="${1##*/}"
	base="${base%.*}"
	case "$base" in
	olhar-pagina | playwright | puppeteer) return 0 ;;
	esac
	return 1
}


dirige_entrada=0

# Modo conservador: sem comando recortado nao ha posicao de comando confiavel,
# entao volta-se a casar por substring — barra demais em vez de barrar de menos.
if [ "$MODO_CONSERVADOR" = 1 ]; then
	for ferramenta in xdotool wmctrl virt-viewer scrot xwd ydotool olhar-pagina \
		playwright puppeteer chromium google-chrome firefox xdg-open; do
		if [[ "$INPUT" == *"$ferramenta"* ]]; then
			dirige_entrada=1
			break
		fi
	done
fi

# Parte o payload em SEGMENTOS de comando. O bash ja faz o trabalho pesado: com
# IFS de separadores, cada segmento comeca onde um comando comeca.
segmentos="$COMANDO"
segmentos="${segmentos//&&/$'\n'}"
segmentos="${segmentos//||/$'\n'}"
segmentos="${segmentos//|/$'\n'}"
segmentos="${segmentos//;/$'\n'}"
segmentos="${segmentos//&/$'\n'}"
segmentos="${segmentos//\(/$'\n'}"
segmentos="${segmentos//\)/$'\n'}"

while [ "$MODO_CONSERVADOR" = 0 ] && IFS= read -r segmento; do
	if [ -z "${segmento// /}" ]; then continue; fi
	# shellcheck disable=SC2086
	set -- $segmento
	# Descasca atribuicoes de ambiente e prefixos transparentes ate achar o
	# primeiro token que e' de fato o comando.
	while [ $# -gt 0 ]; do
		case "$1" in
		[A-Za-z_]*=*) shift ;;         # DISPLAY=:0 VAR=x
		-*) shift ;;                   # -n 19, --rede facebook (opcao de prefixo)
		[0-9]*)                        # o N de `timeout 120` / `nice -n 19`
			shift
			;;
		*)
			if eh_transparente "$1"; then
				shift
				continue
			fi
			break
			;;
		esac
	done
	if [ $# -eq 0 ]; then continue; fi
	comando="$1"
	if ! eh_ferramenta "$comando"; then
		eh_interpretador "$comando" || continue
		achou_script=0
		for arg in "$@"; do
			if eh_script_de_navegador "$arg"; then
				achou_script=1
				break
			fi
		done
		[ "$achou_script" = 1 ] || continue
	fi

	# Etapa 3: `import` so conta com opcao logo depois (`import -window root`).
	# `import pathlib` de Python nunca tem `-` no token seguinte.
	if [ "${comando##*/}" = "import" ]; then
		if [ $# -lt 2 ]; then continue; fi
		if [[ "$2" != -* ]]; then continue; fi
	fi

	dirige_entrada=1
	break
done <<<"$segmentos"

if [ "$dirige_entrada" = 0 ]; then exit 0; fi

bloqueia \
	"Automacao de navegador/janela apontada para o display :0, que e' a sessao grafica do titular — nela roda a VM com PJe/e-SAJ e o token de assinatura." \
	"Use o display virtual do agente:
  DISPLAY=:99 <comando>
Para publicar em rede social, use o wrapper, que ja forca :99:
  ./tools/publicar-perfis-sociais --rede facebook --todas --dry-run
  ./tools/publicar-perfis-sociais --rede facebook --todas
Nao existe Xvfb em :99? O wrapper sobe um sozinho (tools/publicar-perfis-sociais:52).
Para fotografar, use page.screenshot() da propria pagina, nunca captura da tela:
ver a tela traz junto o risco de clicar no terminal ao lado.
Unica excecao a :0 e' --login, em que o TITULAR digita a credencial."
exit 0
