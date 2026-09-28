#!/usr/bin/env bash
# block-heavy-go.sh — Hook PreToolUse:Bash (projeto /opt/wiki)
#
# Bloqueia comando Go full-tree / pesado (build/test ./..., lab-cycle, cmd/check all,
# run-check all, tools/check-all, auditoria --global) A MENOS que envelopado em
# `run-heavy-throttled` — que capa GOMAXPROCS, aplica nice e serializa com lock
# (= "1 pesado por vez"), garantindo a seguranca de recurso (o servidor de 8 cores
# travou por sobrecarga em 2026-07-08).
#
# Enforcement UNIVERSAL por ENVELOPE (nao por "quem chama"): nao ha como distinguir
# maestro de subagente de forma confiavel (o Bash tool abre shell fresco do profile).
# A distincao "so o maestro roda pesado" fica na camada de prompt dos subagentes.
#
# Deteccao no payload CRU: os tokens pesados e o proprio `run-heavy-throttled` nao
# contem aspas duplas, entao grepar o INPUT e imune ao truncamento de escape JSON.
#
# Fail-open: qualquer erro -> exit 0 (nunca trava a sessao).

# PERFORMANCE (2026-07-28): os testes abaixo usavam `printf | grep` — 8 processos
# por chamada, pagos em TODA chamada Bash de TODO agente neste repo. Trocados por
# `[[ =~ ]]` / `[[ == ]]` do bash, que avaliam a MESMA ERE sem criar processo. A
# fonte continua sendo o payload CRU ($INPUT), como o cabecalho acima exige.
set -euo pipefail
trap 'exit 0' ERR

INPUT="$(cat)"
[ -z "$INPUT" ] && exit 0

# HEREDOC QUOTED NAO E EXECUCAO (fix 2026-08-19).
#
# O DEFEITO. RE_CMD trata crase como posicao de comando — e esta certo, porque crase
# e substituicao de comando em shell. So que markdown usa crase para CODIGO INLINE,
# entao escrever documentacao que CITA um comando pesado passou a ser bloqueado.
# Aconteceu duas vezes nesta sessao: um `cat > SKILL.md <<QUOTED` foi barrado porque o
# TEXTO da skill ensinava a NAO rodar comando full-tree, e depois o proprio comando que
# escrevia esta correcao foi barrado pelo mesmo motivo. O hook impedia de documentar a
# regra que ele aplica — e documentar a regra e justamente como ela se propaga.
#
# O FIX NAO AFROUXA NADA. Dentro de um heredoc QUOTED (delimitador entre aspas) o shell
# nao expande nem executa: aquilo e DADO a caminho de um arquivo. Entao o corpo do
# heredoc sai da analise e todo o resto do payload continua avaliado igual.
#
# A EXCECAO QUE MANTEM O FECHO: se o heredoc alimenta um INTERPRETADOR (bash, sh, zsh,
# ksh, python, perl, ruby, node), o corpo E executado — ai nada e removido, e o
# comando pesado escondido no corpo continua sendo barrado.
#
# CUSTO: um processo python3 SOMENTE quando o payload contem heredoc quoted, que e
# minoria. Sem heredoc, o caminho segue em ERE pura do bash, com zero processo, como
# a otimizacao de 2026-07-28 exige.
if [[ "$INPUT" == *"<<'"* || "$INPUT" == *'<<\"'* || "$INPUT" == *'<<-'* ]]; then
	STRIPPED="$(printf '%s' "$INPUT" | python3 -I "$(dirname "${BASH_SOURCE[0]}")/strip-heredoc-body.py" 2>/dev/null)" || STRIPPED=""
	[ -n "$STRIPPED" ] && INPUT="$STRIPPED"
fi

# Envelopado em run-heavy-throttled? -> recurso capado, permite (inclusive full-tree do maestro).
if [[ "$INPUT" == *run-heavy-throttled* ]]; then
	exit 0
fi

# `go list` (mesmo ./...) e READ-ONLY: so enumera pacotes/metadata, nao compila nem
# linka os ~504 pacotes, entao nunca e o comando que travou o servidor em 2026-07-08.
# Barrar go list era falso-positivo do glob ./... (bug de over-block). Libera go list;
# build/test/vet ./... continuam pesados e barrados abaixo.
#
# DEFEITO fechado (fiscalizacao 2026-07-17): o grep de go list e NAO-ANCORADO, entao um
# comando COMPOSTO como `go list ./... && go build ./...` casava e dava exit 0 ANTES do
# check pesado — furando o throttle que existe porque o servidor travou em 2026-07-08.
# Fix: so eximir go list se NAO houver build/test/vet/run no MESMO payload (encadeado).
# NOTA (2026-07-28): as ERE ficam em VARIAVEL e sao usadas como `=~ $re`. Escrever a
# ERE crua dentro de [[ ]] quebra o PARSE do script quando ela contem `(` dentro de
# bracket expression (ex.: [;&|([:space:]]) — o parser do bash conta esse `(` como
# grupo e o arquivo inteiro vira "unexpected EOF", travando TODA chamada Bash do repo
# (fail-open nao salva: o erro e de parse, o script nunca roda). Variavel = mesma ERE,
# parse seguro, e sem processo extra.
re_golist='(go-modern|\bgo)[[:space:]]+list([[:space:]]|$)'
re_goheavy='(go-modern|\bgo)[[:space:]]+(build|test|vet|run)([[:space:]]|$)'
if [[ "$INPUT" =~ $re_golist ]]; then
	if ! [[ "$INPUT" =~ $re_goheavy ]]; then
		exit 0
	fi
fi

is_heavy=0

# Padroes ancorados em INVOCACAO (2026-07-21): prosa citando um comando em
# mensagem de commit/doc NAO casa mais — o scan literal amplo bloqueava o
# proprio trabalho (falsos-positivos em git commit). Casa apenas:
#  go/go-modern build|test|vet|run ... ./...   (full-tree como ARGUMENTO)
#  invocacao de lab-cycle / tools/check-all / run-check all / cmd/check all
#  (exigem ./ ou tools/ ou go-modern run no MESMO segmento de comando)
#
# ATENCAO (fix 2026-07-28): estes regexes tem `(` DENTRO do bracket `[;&|([:space:]]`.
# Em `grep -E '...'` o padrao ia entre aspas e o bash nao o parseava; ja em
# `[[ =~ ... ]]` o operando NAO pode ir literal — o bash conta os parenteses antes
# de entregar a ERE e aborta o arquivo inteiro com "unexpected EOF looking for `)'",
# derrubando o hook (e portanto TODA chamada Bash do repo). Por isso a ERE fica numa
# VARIAVEL e o teste usa `=~ $var` SEM aspas (com aspas viraria match literal).
#
# ANCORA REESCRITA (2026-07-28) — POSICAO DE COMANDO, nao "precedido de espaco".
#
# Historico do defeito: a ancora `[;&|([:space:]]` errava dos DOIS lados.
#  - Falso-NEGATIVO: o payload chega em JSON (`{"command":"./tools/lab-cycle"}`), o
#    comando vem precedido de `"`, que nao estava no conjunto -> a suite completa
#    NUNCA disparava quando era o primeiro token do campo `command` (o caso normal).
#  - Falso-POSITIVO: `[:space:]` casa QUALQUER mencao precedida de espaco, entao
#    `git commit -m "roda ./tools/lab-cycle"` e ate um `echo` em doc eram barrados.
#    Isso travava trabalho legitimo — inclusive o commit deste proprio fix.
#    (Passar a aceitar `"` na ancora fechava o negativo e piorava o positivo.)
#
# Fix correto: ancorar onde um comando REALMENTE comeca a executar —
#   RE_CMD = abertura do campo `command` do JSON  |  separador de shell (; && || | ( `$( )
# seguida de prefixos benignos opcionais (nice -n N, sudo, env VAR=x, time, nohup...).
# Uma mencao dentro de `-m "..."` vem depois de `git commit -m \"`, que NAO e posicao
# de comando -> nao casa. Sem processo extra: continua tudo em ERE do proprio bash.
# FURO FECHADO (2026-08-19): a ancora nao incluia QUEBRA DE LINHA, entao um comando
# pesado na SEGUNDA linha de um script multilinha passava livre — medido: um `echo` numa
# linha e o build full-tree na seguinte nao era barrado. Como o payload chega em JSON, a
# quebra vem como a sequencia de dois caracteres \ + n; por isso a alternativa cobre as
# duas formas (o \n literal do JSON e uma quebra real, se algum caller nao escapar).
# Isto e o furo exato que o hook existe para fechar: o servidor travou em 2026-07-08 por
# comando pesado nao envelopado, e um `cd X && build` era barrado enquanto o mesmo par em
# duas linhas nao era. O strip de heredoc roda ANTES desta ancora, entao documentacao que
# cita o comando continua passando.
RE_CMD='("command":[[:space:]]*"|[;&|(`]|\$\(|\\n|\n)[[:space:]]*(([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*|nice|-n|[0-9]+|sudo|-E|time|env|command|exec|nohup|setsid|xargs)[[:space:]]+)*'

re_fulltree=$RE_CMD'(\./)?(tools/)?(go-modern|go)[[:space:]]+(build|test|vet|run)[[:space:]][^;&|"]*\./\.\.\.'
re_labcycle=$RE_CMD'(\./)?tools/(lab-cycle|check-all)\b'
re_checkall=$RE_CMD'((\./)?tools/run-check[[:space:]]+all\b|(\./)?(tools/)?(go-modern|go)[[:space:]]+run[[:space:]][^;&|"]*cmd/check[[:space:]]+all\b|\./cmd/check[[:space:]]+all\b)'

if [[ "$INPUT" =~ $re_fulltree ]]; then
	is_heavy=1
fi
if [[ "$INPUT" =~ $re_labcycle ]]; then
	is_heavy=1
fi
if [[ "$INPUT" =~ $re_checkall ]]; then
	is_heavy=1
fi

# Auditoria global (ex.: tools/audit_v2_pages.py --global). Escopado por "audit"
# para NAO barrar comandos legitimos com --global (ex.: git config --global).
if [[ "$INPUT" == *--global* && "${INPUT,,}" == *audit* ]]; then
	is_heavy=1
fi

if [ "$is_heavy" = 1 ]; then
	echo "BLOQUEADO: comando Go full-tree/pesado (build/test ./..., lab-cycle, cmd/check all, run-check all, check-all, auditoria --global)." >&2
	echo "Servidor de 8 cores travou por sobrecarga em 2026-07-08. Rode 1 por vez, ENVELOPADO:" >&2
	echo "  ./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./...   (defina WIKI_HEAVY_* para comandos 10k)" >&2
	echo "Subagente: NAO rode pesado — entregue o codigo; o maestro valida e commita. Teste focado: ./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./internal/<pkg>/" >&2
	exit 2
fi

exit 0
