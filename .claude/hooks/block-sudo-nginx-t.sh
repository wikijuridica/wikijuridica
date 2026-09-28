#!/usr/bin/env bash
# block-sudo-nginx-t.sh — PreToolUse:Bash (projeto /opt/wiki)
#
# BARRA: `sudo nginx -t` / `sudo nginx -T`.
# Rodar o teste de configuracao como root faz o nginx recriar os diretorios
# temporarios e de cache sob o usuario da diretiva `user` — ou seja, devolve
# `var/nginx/` a `nobody`. Os workers vivos passam a tomar EACCES e o canal de
# maquina inteiro (gemea Markdown, /api/v1, descritores) vira 500.
#
# NAO barra: `nginx -t` sem sudo (a forma certa), nem `sudo nginx -s reload`,
# `sudo systemctl reload nginx` ou qualquer outra operacao de nginx com sudo.
set -uo pipefail
trap 'exit 0' ERR
. "$(dirname "${BASH_SOURCE[0]}")/lib/bloqueio.sh" 2>/dev/null || exit 0

INPUT="$(le_payload)"
[ -z "$INPUT" ] && exit 0
[[ "$INPUT" != *nginx* ]] && exit 0

# sudo (com flags opcionais como -n / -E / -u X) seguido de nginx e, na mesma
# invocacao, a flag de teste de configuracao.
re_sudo_nginx='sudo([[:space:]]+(-[A-Za-z]+|-u[[:space:]]*[A-Za-z0-9_-]+))*[[:space:]]+(/[^[:space:]]*/)?nginx([^;&|"]*)'
resto="$INPUT"
while [[ "$resto" =~ $re_sudo_nginx ]]; do
	trecho="${BASH_REMATCH[0]}"
	resto="${resto#*"$trecho"}"
	cauda="${trecho#*nginx}"
	if [[ "$cauda" =~ (^|[[:space:]])-[tT]([[:space:]]|$) ]]; then
		bloqueia \
			"sudo nginx -t recria var/nginx/ como 'nobody': os workers vivos tomam EACCES e o canal de maquina inteiro passa a responder 500." \
			"Valide a configuracao SEM sudo — e a forma sancionada:
  nginx -t
Para recarregar depois de validar:
  sudo -n systemctl reload nginx
Se ja rodou com sudo e o canal caiu, o sintoma e 500 em /familia/x/index.md e
/api/v1/*: confira o dono de var/nginx/ antes de qualquer outra hipotese."
	fi
done
exit 0
