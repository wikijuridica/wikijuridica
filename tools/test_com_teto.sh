#!/usr/bin/env bash
# test_com_teto.sh — prova o wrapper de teto de tempo da onda diaria.
#
# O QUE ELE GUARDA, e por que cada asserção existe:
#
#   1. o exit code do comando VOLTA INTACTO. `com_teto` limita e nomeia; ele
#      nao decide nada. Se ele traduzisse exit codes, todo `if !` da onda
#      passaria a julgar o wrapper em vez do passo.
#   2. o teto DISPARA, e a mensagem diz "TETO ESTOURADO" com o rotulo. Sem a
#      frase, o operador le "falhou" e vai investigar conteudo onde nao ha o
#      que investigar.
#   3. NAO HA `--kill-after`, e esta e a asserção que protege o repositorio
#      inteiro. Com `-k`, um `git commit` estourado levaria SIGKILL e deixaria
#      `.git/index.lock` no disco -- e index.lock orfao trava TODAS as sessoes,
#      que compartilham o indice. O teste prova a propriedade pelo efeito: um
#      filho que TRATA o SIGTERM consegue terminar a propria limpeza.
#
# A funcao e extraida do ARQUIVO REAL por ancora literal, nunca copiada: teste
# que reimplementa o alvo fica verde com a regra desligada no codigo real.
#
#   bash tools/test_com_teto.sh
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ALVO="$RAIZ/tools/run-daily-content"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

falhas=0
ok() { printf 'ok   %s\n' "$1"; }
falha() {
	printf 'FALHA %s\n' "$1" >&2
	falhas=$((falhas + 1))
}

# ---- extracao por ancora literal: de `com_teto() {` ate o `}` na coluna 0.
awk '/^com_teto\(\) \{$/ {dentro=1} dentro {print} dentro && /^\}$/ {exit}' \
	"$ALVO" >"$TMP/com_teto.sh"
if ! grep -q '^com_teto() {$' "$TMP/com_teto.sh" || ! grep -q '^}$' "$TMP/com_teto.sh"; then
	echo "FALHA: nao consegui extrair com_teto de $ALVO -- a ancora mudou" >&2
	exit 2
fi
# shellcheck source=/dev/null
. "$TMP/com_teto.sh"

# ---- 1. exit code intacto, nos dois sentidos.
if com_teto 10 "verdadeiro" true; then ok "exit 0 do comando volta 0"; else falha "exit 0 virou outra coisa"; fi
com_teto 10 "falso" false
rc=$?
[ "$rc" -eq 1 ] && ok "exit 1 do comando volta 1" || falha "exit 1 virou $rc"
com_teto 10 "codigo 75" bash -c 'exit 75'
rc=$?
[ "$rc" -eq 75 ] && ok "exit 75 do comando volta 75" || falha "exit 75 virou $rc"

# ---- 2. o teto dispara, devolve 124 e NOMEIA o passo.
saida="$(com_teto 1 "passo-que-nao-acaba" timeout 20 tail -f /dev/null 2>&1)"
rc=$?
[ "$rc" -eq 124 ] && ok "teto estourado devolve 124" || falha "teto estourado devolveu $rc, esperado 124"
case "$saida" in
*"TETO ESTOURADO"*"passo-que-nao-acaba"*) ok "a mensagem nomeia o passo que estourou" ;;
*) falha "a mensagem do teto nao nomeia o passo: $saida" ;;
esac
case "$saida" in
*"NÃO é reprovação de conteúdo"*) ok "a mensagem separa relogio de conteudo" ;;
*) falha "a mensagem nao separa relogio de conteudo: $saida" ;;
esac

# ---- 3. SEM --kill-after: o filho que trata SIGTERM consegue se limpar.
#
# ESTA E A ASSERCAO QUE MATA O MUTANTE `timeout -k`. O filho instala um trap de
# SIGTERM que leva ~2 s para escrever a marca -- exatamente o que o `git` faz
# para remover `.git/index.lock`. Com `--kill-after` menor que isso, o SIGKILL
# chega antes e a marca NUNCA aparece; sem ele, o filho termina a limpeza.
MARCA="$TMP/limpeza-feita"
cat >"$TMP/filho.sh" <<'FILHO'
#!/usr/bin/env bash
limpa() {
	timeout 2 tail -f /dev/null 2>/dev/null
	printf 'limpei\n' >"$1"
	exit 143
}
trap 'limpa "$1"' TERM
timeout 30 tail -f /dev/null 2>/dev/null
FILHO
chmod +x "$TMP/filho.sh"
com_teto 1 "filho-que-se-limpa" bash "$TMP/filho.sh" "$MARCA" >/dev/null 2>&1
if [ -f "$MARCA" ]; then
	ok "sem --kill-after: o filho que trata SIGTERM conclui a propria limpeza"
else
	falha "o filho NAO conseguiu se limpar -- com_teto ganhou --kill-after, e um git commit estourado passaria a deixar .git/index.lock orfao"
fi

# ---- 3-bis. A ASSERCAO LITERAL, E POR QUE ELA EXISTE AO LADO DA DE CIMA.
#
# Medido em 2026-09-16, com o proprio filho acima: `--kill-after=0s` NAO mata
# (o coreutils trata 0 como "desabilitado", rc=124 e a marca aparece);
# `--kill-after=1s` e `=5s` matam (rc=137, marca ausente). Ou seja: a asserção
# COMPORTAMENTAL so pega `-k` MENOR que o tempo de limpeza do filho, que aqui e
# de 2 s. Um `-k 30s` passaria por ela e ainda assim seria a regressao que se
# quer impedir no dia em que o pre-commit demorar mais que isso.
#
# Entao vao as DUAS: a comportamental prova que a propriedade IMPORTA (o filho
# realmente se limpa), e esta prova que ela nao foi introduzida de nenhuma
# forma. Sozinha, a literal seria detector que responde ao grep; sozinha, a
# comportamental deixaria passar o `-k` grande.
if grep -qE -- '--kill-after|[[:space:]]-k[[:space:]]' "$TMP/com_teto.sh"; then
	falha "com_teto passou a usar --kill-after/-k: SIGKILL deixaria .git/index.lock orfao e travaria TODAS as sessoes deste repositorio"
else
	ok "com_teto nao usa --kill-after nem -k em nenhuma forma"
fi

# ---- 4. a onda nao pode voltar a ter ponto nu: a contagem e parte do gate.
nus="$(nice -n 19 python3 - "$ALVO" <<'PY'
import re, sys
pad = re.compile(r"(\$GO run |git com" + "mit|git ad" + r"d |reload-wiki-server|\./tools/check-|\./tools/generate-|python3 )")
n = 0
for linha in open(sys.argv[1], encoding="utf-8"):
    t = linha.strip()
    if t.startswith("#") or not pad.search(linha):
        continue
    if "timeout " in linha or "com_teto" in linha:
        continue
    if t.startswith("echo ") or t.startswith("printf "):
        continue
    n += 1
print(n)
PY
)"
[ "$nus" = "0" ] && ok "nenhuma invocacao sem teto em run-daily-content" ||
	falha "voltaram $nus invocacoes sem teto de tempo em run-daily-content"

echo
if [ "$falhas" -eq 0 ]; then
	echo "test_com_teto: OK"
	exit 0
fi
echo "test_com_teto: $falhas falha(s)"
exit 1
