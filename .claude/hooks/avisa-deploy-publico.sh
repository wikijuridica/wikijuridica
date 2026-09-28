#!/usr/bin/env bash
# avisa-deploy-publico.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# NAO BLOQUEIA. Injeta, no momento exato do comando, a decisao que o deploy
# publico exige e que nao esta no comando: `--ressemear` ou nao, e purgar ou
# nao. Errar essa decisao re-data as ~11 mil rotas e re-anuncia o acervo
# inteiro ao Googlebot, ou deixa a borda servindo acervo velho por 7 dias
# (s-maxage=604800). E a decisao acontece uma vez, no ato — e por isso que ela
# e' injetada aqui e nao escrita num documento que ninguem abre na hora.
set -uo pipefail
trap 'exit 0' ERR
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
[ -z "$INPUT" ] && exit 0
[[ "$INPUT" != *deploy-publico* ]] && exit 0

# ANCORA DE POSICAO DE COMANDO. Sem ela, este injetor dispara em PROSA — medido
# em 2026-09-16: escrever uma regra que CITA o nome do comando fez o aviso
# inteiro entrar no contexto, sem nenhum deploy acontecendo. Injetor barato que
# dispara errado deixa de ser barato: ele paga tokens em toda escrita que
# mencione a palavra. E' a mesma classe de falso-positivo que block-heavy-go.sh
# ja documenta no cabecalho dele.
RE_ANCORA='("command":[[:space:]]*"|[;&|(`'$'\n'']|\$\(|\\n)[[:space:]]*(([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*|nice|-n|[0-9]+|sudo|-E|time|env|command|exec|nohup|setsid|flock|xargs)[[:space:]]+)*'
RE_GATILHO=$RE_ANCORA'(\./)?(tools/)?deploy-publico'
[[ ! "$INPUT" =~ $RE_GATILHO ]] && exit 0

avisa "Matriz 'mudei X, entao faco Y' — decida antes de confirmar:

  texto editorial ............ SEM --ressemear (a re-datacao e' verdadeira) · purga do deploy basta
  markup/CSS/atributo servido  COM --ressemear (e --desde-commit fica proibido nessa passada) · purga do deploy basta
  script inline .............. SEM --ressemear (ja e' neutralizado) · purga AMPLA manual obrigatoria
  malha de links/relacionados  SEM --ressemear · purga AMPLA manual obrigatoria

Depois de purga ampla: ./tools/warm-edge-cache --rps 12 (o timer so passa as 04:20 e 16:20 UTC).
Antes de purgar a mao: confira data/ops/edge_cache_purge.jsonl — se o deploy ja gravou
scope: \"tudo\", purgar de novo joga fora ~870 s de aquecimento e deixa a borda em MISS.
Se o deploy imprimir 'purgando tudo', NAO purgue de novo — mas LEIA o motivo impresso:
'registro de revisao indisponivel' ja foi mentira (era --purge-targets caindo no teto de churn).
Detalhe do procedimento: skill deploy-publico."
