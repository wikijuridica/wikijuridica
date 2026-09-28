#!/usr/bin/env bash
# lib/bloqueio.sh — leitura de payload e emissao de bloqueio para os hooks
# PreToolUse deste repositorio. Fonte unica: as tres funcoes abaixo resolvem
# problemas que ja custaram incidente, e resolve-los uma vez por hook produziria
# oito versoes que divergem.

# ---------------------------------------------------------------------------
# le_payload — entrega o payload do hook ja normalizado para analise.
#
# Faz duas coisas, nesta ordem, e as duas nasceram de defeito MEDIDO:
#
# 1. DESPE O CORPO DE HEREDOC QUOTED. Dentro de `<<'FIM'` o shell nao expande
#    nem executa: aquilo e' DADO a caminho de um arquivo. Sem isto, um hook
#    bloqueia quem tenta DOCUMENTAR o comando que ele barra — e documentar a
#    regra e' como ela se propaga. Reaproveita strip-heredoc-body.py, que ja
#    trata a excecao que fecha a evasao: heredoc que alimenta um INTERPRETADOR
#    (bash, python, node…) e' executado e continua sob analise.
#    Custo: um processo python SOMENTE quando ha heredoc no payload.
#
# 2. DESESCAPA \n e \t. O payload chega em JSON, entao uma quebra de linha vem
#    como os DOIS caracteres \ e n. Medido em 2026-09-16: `sudo nginx -t` seguido
#    de quebra de linha nao era barrado, porque o `-t` era seguido de `\` e nao
#    de espaco; e `git add data/` numa linha de comando multilinha virava a
#    palavra unica `data/\nRESTO`, que nao casa com `*/`. Os dois eram FALSO
#    NEGATIVO — o hook dizia que estava tudo bem. Virando quebra de linha REAL,
#    a ancora de posicao de comando e o word splitting do bash voltam a valer.
#    Zero processo: expansao de parametro do proprio bash.
le_payload() {
	local bruto cmd despido
	bruto="$(cat)"
	[ -z "$bruto" ] && return 0

	# 1. RECORTA O COMANDO ANTES DE QUALQUER ANALISE.
	#
	# Ate 2026-09-16 tudo era analisado sobre o ENVELOPE JSON inteiro, e isso
	# fazia o veredito depender do ESPACAMENTO do serializador. O caso medido: o
	# strip de heredoc olhava 60 caracteres ANTES do `<<` para decidir se o corpo
	# alimenta um interpretador (ate 2026-09-23; hoje a busca do dono do heredoc e
	# ancorada na linha logica, com alcance de 1000 caracteres e parada na quebra —
	# strip-heredoc-body.py); sobre o envelope, esses 60 caracteres caiam dentro
	# de `{"tool_name":"Bash","tool_input":{"command":"...`, e quanto do envelope
	# cabe ali muda conforme o JSON venha compacto ou espacado. Resultado: os
	# mesmos tres hooks barravam DOCUMENTACAO com payload compacto e a liberavam
	# com payload espacado. Um hook cujo veredito depende do espacamento do
	# serializador e um hook quebrado, mesmo quando a forma testada acerta.
	#
	# O recorte nao depende do espacamento: anda ate a chave "command" e dai ate a
	# proxima aspa, que e a de abertura do valor.
	cmd="$bruto"
	if [[ "$bruto" == *'"command"'* ]]; then
		cmd="${bruto#*\"command\"}"
		cmd="${cmd#*\"}"
		cmd="${cmd%\"*}"
	fi

	# 2. DESPE O CORPO DE HEREDOC QUOTED. Dentro de `<<'FIM'` o shell nao expande
	# nem executa: aquilo e DADO a caminho de um arquivo. Sem isto, um hook
	# bloqueia quem tenta DOCUMENTAR o comando que ele barra — e documentar a
	# regra e como ela se propaga. A excecao que fecha a evasao continua valendo:
	# heredoc que alimenta um INTERPRETADOR (bash, python, node...) e executado e
	# segue sob analise. Custo: um processo python SOMENTE quando ha heredoc.
	if [[ "$cmd" == *"<<'"* || "$cmd" == *'<<\"'* || "$cmd" == *'<<-'* ]]; then
		despido="$(printf '%s' "$cmd" | python3 -I "$(dirname "${BASH_SOURCE[0]}")/../strip-heredoc-body.py" 2>/dev/null)" || despido=""
		[ -n "$despido" ] && cmd="$despido"
	fi

	# 3. DESESCAPA. O payload chega em JSON, entao uma quebra de linha vem como os
	# DOIS caracteres \ e n. Medido: `sudo nginx -t` seguido de quebra nao era
	# barrado (o `-t` era seguido de `\`, nao de espaco), e `git add data/` numa
	# linha multilinha virava a palavra unica `data/\nRESTO`. Falso NEGATIVO nos
	# dois casos — o hook dizia que estava tudo bem.
	cmd=${cmd//\\n/$'\n'}
	cmd=${cmd//\\t/$'\t'}
	cmd=${cmd//\\\"/\"}

	# 4. Devolve com o rotulo `"command":"` na frente, que e a ancora de POSICAO DE
	# COMANDO que os hooks usam para o primeiro comando da linha.
	printf '"command":"%s"' "$cmd"
}

# json_escape <texto> — escapa aspas, contrabarra, quebra de linha e tab.
# Em expansao de parametro do bash (sem sed/python): estes hooks rodam em TODA
# chamada Bash do repositorio e um processo por hook seria pago sempre.
json_escape() {
	local s=$1
	s=${s//\\/\\\\}
	s=${s//\"/\\\"}
	s=${s//$'\t'/\\t}
	s=${s//$'\n'/\\n}
	printf '%s' "$s"
}

# bloqueia <motivo-curto> <ensino-multilinha>
#
# Emite pelas DUAS rotas de proposito. A doc oficial diz que o PreToolUse honra
# permissionDecision E additionalContext ao mesmo tempo, e que exit 2 com JSON
# valido no stdout tem cada campo suportado honrado; mas tambem diz que exit 2
# SEM JSON legivel manda o stderr como motivo. Escrever as duas faz o hook
# funcionar igual sob qualquer das duas leituras do harness.
#
# O motivo diz o que foi barrado; o ensino diz o COMANDO certo, com caminho e
# numero. Hook que so nega nao ensina nada.
bloqueia() {
	local motivo=$1 ensino=$2
	printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s","additionalContext":"%s"}}\n' \
		"$(json_escape "$motivo")" "$(json_escape "$ensino")"
	printf '%s\n%s\n' "$motivo" "$ensino" >&2
	exit 2
}

# avisa <contexto> — nao bloqueia; injeta contexto no momento do ato.
avisa() {
	printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' \
		"$(json_escape "$1")"
	exit 0
}
