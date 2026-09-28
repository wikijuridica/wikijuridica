#!/usr/bin/env bash
# test_pre_commit_binario_confiavel.sh — bancada da guarda de binários
# confiáveis do .githooks/pre-commit (bloco `binario_confiavel`).
#
# ONDE RODA: em qualquer máquina do projeto, sem root; extrai o bloco REAL do
# hook entre os marcadores `>>>> binario_confiavel` e `<<<< binario_confiavel`
# (não é cópia) e o exercita contra arquivos de verdade.
#
# POR QUE EXISTE (2026-09-24). No Ubuntu 26.04 da torre, /usr/bin/nice, env,
# stat, timeout, mktemp, chmod, readlink e rmdir são symlinks de root para o
# uutils, e a guarda recusava todo symlink: nenhum commit passava na máquina
# de produção. A regra nova aceita symlink cujo elo E alvo sejam confiáveis.
# Esta bancada prova as duas metades: o symlink de root para binário de root
# passa, e o symlink de USUÁRIO (o que um atacante sem root consegue criar)
# reprova, mesmo apontando para um binário legítimo.
#
# Casos que exigem criar arquivo de root (symlink de root para alvo gravável)
# só rodam como root; sem root eles são declarados como não medidos.
set -uo pipefail

AQUI=$(cd "$(dirname "$0")" && pwd)
HOOK=$AQUI/../.githooks/pre-commit
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
falhas=0
checa() {  # checa <descricao> <obtido> <esperado>
	if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FALHA $1: esperado '$3', veio '$2'"; falhas=$((falhas + 1)); fi
}

sed -n '/^# >>>> binario_confiavel: inicio/,/^# <<<< binario_confiavel: fim/p' "$HOOK" > "$T/bloco.sh"
[ -s "$T/bloco.sh" ] || { echo "marcadores do bloco binario_confiavel nao achados em $HOOK"; exit 2; }
# Lidas pelo bloco, como no hook.
export STAT_BIN=/usr/bin/stat READLINK_BIN=/usr/bin/readlink
# O bloco roda em /bin/sh com `set -eu`, porque e assim que o hook o roda
# (#!/bin/sh; dash no Debian 12 e no Ubuntu 26.04): um bashism passaria verde
# se a bancada o carregasse no proprio bash (achado da refutacao de 2026-09-24).
BLOCO=$T/bloco.sh
veredito() {  # veredito <caminho> -> aceita|recusa, com o bloco em $BLOCO
	if /bin/sh -c 'set -eu; PATH=/usr/bin:/bin; . "$1"; binario_confiavel "$2"' _ "$BLOCO" "$1" >/dev/null 2>&1; then
		echo aceita
	else
		echo recusa
	fi
}

echo "=== binario_confiavel ==="
# Um executável regular de root que existe nas duas distros.
REGULAR=""
for c in /usr/bin/git /usr/bin/flock /usr/bin/dpkg; do
	if [ -f "$c" ] && [ ! -L "$c" ] && [ "$(stat -c %u "$c")" = 0 ]; then REGULAR=$c; break; fi
done
[ -n "$REGULAR" ] || { echo "nenhum executavel regular de root achado para a bancada"; exit 2; }
checa "executavel regular de root ($REGULAR) passa" "$(veredito "$REGULAR")" aceita
# /usr/bin/python3 é symlink de root para o interpretador de root no Debian 12
# e no Ubuntu 26.04: é o caso do uutils na forma que existe nas duas máquinas.
if [ -L /usr/bin/python3 ] && [ "$(stat -c %u /usr/bin/python3)" = 0 ]; then
	checa "symlink de root para binario de root (/usr/bin/python3) passa" "$(veredito /usr/bin/python3)" aceita
else
	echo "  !    /usr/bin/python3 nao e symlink de root nesta maquina -- caso nao medido"
fi
# Como root, o que este script cria nasce de root: os dois arquivos "do
# usuario" passam a um uid comum, senao a fixture mede outra coisa.
USUARIO_COMUM=${SUDO_UID:-1000}
de_usuario() { if [ "$(id -u)" = 0 ]; then chown -h "$USUARIO_COMUM:$USUARIO_COMUM" "$1"; fi; }
ln -s "$REGULAR" "$T/link-do-usuario"; de_usuario "$T/link-do-usuario"
checa "symlink do USUARIO para binario legitimo reprova" "$(veredito "$T/link-do-usuario")" recusa
printf '#!/bin/sh\nexit 0\n' > "$T/binario-do-usuario"; chmod 755 "$T/binario-do-usuario"; de_usuario "$T/binario-do-usuario"
checa "executavel regular do usuario reprova" "$(veredito "$T/binario-do-usuario")" recusa
ln -s "$T/nao-existe" "$T/link-quebrado"
checa "symlink quebrado reprova" "$(veredito "$T/link-quebrado")" recusa
checa "caminho inexistente reprova" "$(veredito "$T/nada")" recusa
if [ "$(id -u)" = 0 ]; then
	printf '#!/bin/sh\nexit 0\n' > "$T/alvo-gravavel"; chmod 777 "$T/alvo-gravavel"; chown 0:0 "$T/alvo-gravavel"
	ln -s "$T/alvo-gravavel" "$T/link-root-para-gravavel"
	checa "symlink de root para alvo gravavel por outros reprova" "$(veredito "$T/link-root-para-gravavel")" recusa
else
	echo "  !    sem root: 'symlink de root para alvo gravavel' nao medido aqui"
fi

echo "=== mutantes (no bloco extraido; o hook real nao e tocado) ==="
# M1: sem a checagem do dono do ELO, o symlink do usuario passaria.
sed '/if ! dono_confiavel "\$1"; then/,/^\t\tfi$/d' "$T/bloco.sh" > "$T/m1.sh"
cmp -s "$T/bloco.sh" "$T/m1.sh" && { echo "mutante M1 nao se aplicou"; exit 2; }
BLOCO=$T/m1.sh
checa "M1 (sem checar o elo): symlink do usuario PASSA -- a bancada ve" "$(veredito "$T/link-do-usuario")" aceita
# M2: a regra antiga, recusar todo symlink, reprovaria o /usr/bin/python3.
sed 's/^\tif \[ -L "\$1" \]; then$/\tif [ -L "$1" ]; then return 1; fi; if false; then/' "$T/bloco.sh" > "$T/m2.sh"
cmp -s "$T/bloco.sh" "$T/m2.sh" && { echo "mutante M2 nao se aplicou"; exit 2; }
BLOCO=$T/m2.sh
if [ -L /usr/bin/python3 ]; then
	checa "M2 (recusa todo symlink): /usr/bin/python3 REPROVA -- a bancada ve" "$(veredito /usr/bin/python3)" recusa
fi
BLOCO=$T/bloco.sh
checa "o loop do hook chama binario_confiavel" \
	"$(grep -c '^[[:space:]]*binario_confiavel "\$TRUSTED_BIN" || exit 1' "$HOOK")" 1

echo
echo "falhas: $falhas"
exit $((falhas > 0))
