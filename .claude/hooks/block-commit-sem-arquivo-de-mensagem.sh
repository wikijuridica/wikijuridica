#!/usr/bin/env bash
# block-commit-sem-arquivo-de-mensagem.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# BARRA duas formas de commit:
#   `git commit -m ...`         mensagem inline. O contrato exige -F <arquivo>.
#   `git commit --no-verify`    pular o pre-commit em vez de corrigir a causa.
#
# NAO barra: `git commit -F arquivo`, `git commit --amend -F`, `git commit -F -`.
set -uo pipefail
trap 'exit 0' ERR
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
[ -z "$INPUT" ] && exit 0
[[ "$INPUT" != *"git commit"* ]] && exit 0

cauda="${INPUT#*git commit}"
cauda="${cauda%%[;&|]*}"

if [[ "$cauda" =~ (^|[[:space:]])(--no-verify|-n)([[:space:]]|$) ]]; then
	bloqueia \
		"git commit --no-verify: pular o pre-commit e contornar o diagnostico, nao resolve-lo." \
		"Pre-commit reprovou? Leia o motivo e corrija a CAUSA.
Motivos frequentes neste repo, com o remedio de cada um:
  'indice mudou durante compilacao'  -> separe git add de git commit em duas chamadas
  orcamento do go-index-compile-closure estourado -> esvazie o indice (ele compila
      o INDICE, nao o seu pathspec: 77,6 s com internal/v2ingest dentro, 14,9 s limpo)
  'shards v2 exigem tools/commit-verified-v2-workflow-results' -> use esse pipeline
  atestacao do grafo -> ./tools/go-modern generate ./internal/v2ingest no MESMO commit"
fi

if [[ "$cauda" =~ (^|[[:space:]])(-m|--message)([[:space:]=]|$) ]]; then
	bloqueia \
		"git commit -m: a mensagem deste repositorio vai por arquivo, nunca inline." \
		"Escreva a mensagem num arquivo e passe por -F:
  printf '%s\\n' 'feat(x): ...' > /tmp/msg.txt
  git commit -F /tmp/msg.txt
Nunca capture a saida do hook (2>&1) no MESMO arquivo passado a -F: isso
sobrescreve a mensagem e e irreversivel.
Para escopar o commit sem tocar a worktree, use pathspec:
  git commit -F /tmp/msg.txt -- caminho/exato"
fi
exit 0
