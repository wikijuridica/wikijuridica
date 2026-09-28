#!/usr/bin/env bash
# avisa-derivado-editorial.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# NAO BLOQUEIA. Injeta a ordem topologica quando um gerador da familia
# authorial-mass e' invocado. A cadeia tem 13 passos e cada artefato precisa ser
# MAIS NOVO que sua fonte; fora de ordem o erro diz `fingerprint mismatch`,
# nunca "ordem errada" — e a fabrica ja ficou 31 dias parada por causa disso.
set -uo pipefail
trap 'exit 0' ERR
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
[ -z "$INPUT" ] && exit 0
[[ "$INPUT" != *generate-authorial-mass* ]] && exit 0

# ANCORA DE POSICAO DE COMANDO. Sem ela, este injetor dispara em PROSA — medido
# em 2026-09-16: escrever uma regra que CITA o nome do comando fez o aviso
# inteiro entrar no contexto, sem nenhum deploy acontecendo. Injetor barato que
# dispara errado deixa de ser barato: ele paga tokens em toda escrita que
# mencione a palavra. E' a mesma classe de falso-positivo que block-heavy-go.sh
# ja documenta no cabecalho dele.
RE_ANCORA='("command":[[:space:]]*"|[;&|(`'$'\n'']|\$\(|\\n)[[:space:]]*(([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*|nice|-n|[0-9]+|sudo|-E|time|env|command|exec|nohup|setsid|flock|xargs)[[:space:]]+)*'
RE_GATILHO=$RE_ANCORA'(\./)?(tools/)?generate-authorial-mass'
[[ ! "$INPUT" =~ $RE_GATILHO ]] && exit 0

avisa "Cadeia editorial: 13 passos em ordem obrigatoria, cada artefato mais novo que sua fonte.
  1 drafts · 2 content-expansion · 3 legal-signatures · 4 contextual-compatibility
  5 paid-intent-refinements · 6 similarity-report · 7 signature-candidate-pairs
  8 similarity-semantic-reviews · 9 refinement-quality-report · 10 global-similarity-audit
  11 editorial-quality-vectors · 12 signature-refinement-queue · 13 publication-readiness
(cada um e' tools/generate-authorial-mass-<nome>)

Regenerar um passo obriga a regenerar TODOS os seguintes — senao o proximo gate
reprova com 'fingerprint mismatch', que nao diz qual e' a ordem certa.
Preserve o artefato anterior em .agents/runtime/<data>/ ANTES de regravar.
A ordem vive em docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md e o gate
tools/check-cadeia-editorial-ordem-declarada prova que ela nao ficou pra tras do codigo.
Detalhe do procedimento: skill ordem-derivados-editoriais."
