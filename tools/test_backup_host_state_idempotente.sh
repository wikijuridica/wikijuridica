#!/usr/bin/env bash
# Prova as DUAS propriedades de `grava_se_mudou` em tools/backup-host-state,
# sem sudo e sem tocar no host: (1) nao reescreve destino cujo conteudo nao
# mudou; (2) a marca de mudanca ATRAVESSA o subshell do pipe.
#
# A segunda e a que justifica o teste existir. `algo | grava_se_mudou destino`
# roda a funcao num SUBSHELL: uma variavel `MUDOU=1` la dentro morre com o
# subshell e o pai nunca ve. O sintoma seria a AUSENCIA de uma linha no
# GERADO_EM.txt -- defeito que nao levanta erro e que ninguem percebe olhando.
# Por isso a marca e arquivo.
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
FONTE="$RAIZ/tools/backup-host-state"
FALHAS=0

falhou() {
	printf 'FALHOU: %s\n' "$1" >&2
	FALHAS=$((FALHAS + 1))
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Extrai o helper e a marca do script real, sem executar o resto dele: o teste
# tem de exercitar O CODIGO QUE VAI PARA PRODUCAO, nao uma copia que envelhece.
sed -n '/^MARCA_DE_MUDANCA=/,/^mudou_algo() { \[ -s "\$MARCA_DE_MUDANCA" \]; }$/p' "$FONTE" >"$TMP/helper.sh"
if ! grep -q 'grava_se_mudou()' "$TMP/helper.sh"; then
	falhou "nao consegui extrair grava_se_mudou de $FONTE — o teste ficaria passando por vazio"
	exit 1
fi

# shellcheck disable=SC1090
. "$TMP/helper.sh"

destino="$TMP/alvo.txt"

# (a) primeira escrita: cria e marca
printf 'linha um' | grava_se_mudou "$destino"
[ "$(cat "$destino")" = "linha um" ] || falhou "primeira escrita nao gravou o conteudo"
mudou_algo || falhou "primeira escrita nao marcou mudanca (a marca nao atravessou o pipe)"

# (b) mesmo conteudo: nao reescreve — provado pelo mtime, nao pela fe
: >"$MARCA_DE_MUDANCA"
antes="$(stat -c %Y "$destino")"
sleep 1.1
printf 'linha um' | grava_se_mudou "$destino"
depois="$(stat -c %Y "$destino")"
[ "$antes" = "$depois" ] || falhou "conteudo igual reescreveu o arquivo (mtime mudou de $antes para $depois)"
mudou_algo && falhou "conteudo igual marcou mudanca"

# (c) conteudo diferente: reescreve e marca
printf 'linha dois' | grava_se_mudou "$destino"
[ "$(cat "$destino")" = "linha dois" ] || falhou "conteudo novo nao foi gravado"
mudou_algo || falhou "conteudo novo nao marcou mudanca"

# (d) nao deixa .tmp para tras
[ -e "$destino.tmp" ] && falhou "sobrou $destino.tmp"

if [ "$FALHAS" -gt 0 ]; then
	printf '%s falha(s)\n' "$FALHAS" >&2
	exit 1
fi
printf 'test_backup_host_state_idempotente: ok (4 propriedades)\n'
