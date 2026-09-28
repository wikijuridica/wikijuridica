#!/usr/bin/env bash
# block-git-add-por-diretorio-test.sh — bancada da guarda do `git add`.
#
#   ./.claude/hooks/block-git-add-por-diretorio-test.sh
#
# ONDE RODA: dentro do /opt/wiki, sem root. Nao escreve no indice e nao chama
# git: alimenta o hook com payloads de mentira e le o veredito dele.
#
# POR QUE ELA EXISTE. A guarda nasceu sem bancada, e em 2026-09-22 reprovou a
# forma CERTA: `git add <arquivo-exato>` seguido, na LINHA DE BAIXO, de um
# `git status --porcelain -- tools/`. A classe negada do regex que recorta a
# cauda do `git add` nao excluia a quebra de linha, entao a captura atravessava
# para a linha seguinte e engolia um `tools/` que o `git add` nunca recebe.
#
# Guarda sem bancada e regra que ninguem pode mudar com seguranca: cada
# conserto vira aposta. E guarda que reprova a forma certa nao e so ruido --
# ela empurra para a forma errada, que aqui e `git add <diretorio>`, que e o
# defeito que a guarda existe para impedir.
#
# AS FIXTURES SAO PAYLOAD, NAO COMANDO: elas nascem de um `printf` montado em
# tempo de execucao, nunca escritas como linha literal neste arquivo. A guarda
# le o proprio texto do comando que a chama, entao uma fixture escrita literal
# aqui faria a bancada ser barrada pela guarda que ela testa -- medido em
# 2026-09-22, ao criar este arquivo por heredoc.
set -uo pipefail
AQUI=$(cd "$(dirname "$0")" && pwd)
HOOK=$AQUI/block-git-add-por-diretorio.sh
[ -x "$HOOK" ] || { echo "  ✗ hook ausente ou sem permissao: $HOOK"; exit 2; }

erros=0
ADD="git ""add"      # montado em duas partes: ver a nota das fixtures acima

paga() {  # paga <comando> -> JSON do payload, como o hook o recebe
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1"
}

veredito() {  # veredito <comando> -> 0 se passou, 1 se a guarda barrou
  paga "$1" | "$HOOK" >/dev/null 2>&1
}

passa() {  # passa <descricao> <comando>
  if veredito "$2"; then echo "   ✓ PASSA: $1"
  else echo "   ✗ PASSA: $1 — a guarda BARROU e nao devia"; erros=$((erros+1)); fi
}

barra() {  # barra <descricao> <comando>
  if veredito "$2"; then echo "   ✗ BARRA: $1 — a guarda DEIXOU PASSAR"; erros=$((erros+1))
  else echo "   ✓ BARRA: $1"; fi
}

echo "════════ 1. o que a guarda TEM de barrar ════════"
barra "o ponto"                      "$ADD ."
barra "-A"                           "$ADD -A"
barra "--all"                        "$ADD --all"
barra "-u"                           "$ADD -u"
barra "diretorio com barra final"    "$ADD ops/provisionamento/"
barra "diretorio sem barra final"    "$ADD ops/provisionamento"
barra "glob que casa diretorio"      "$ADD ops/*"
barra "diretorio no meio de arquivos" "$ADD ops/provisionamento/comum.sh docs/"

echo
echo "════════ 2. o que a guarda NAO pode barrar ════════"
passa "um arquivo exato"        "$ADD ops/provisionamento/comum.sh"
passa "dois arquivos exatos"    "$ADD ops/provisionamento/comum.sh ops/provisionamento/README.md"
passa "com o separador --"      "$ADD -- ops/provisionamento/comum.sh"
passa "glob que so casa arquivo" "$ADD ops/provisionamento/*.sh"
passa "-p nao materializa no indice" "$ADD -p"
passa "--dry-run nao materializa"    "$ADD --dry-run ops/"
passa "lista DERIVADA por substituicao" "$ADD \$(git ls-files -m -- ops/provisionamento)"
passa "find | xargs, cauda vazia"       "find .claude/rules -type f -print0 | xargs -0 $ADD --"

echo
echo "════════ 3. A REGRESSAO de 2026-09-22 — a cauda termina na LINHA ════════"
# Foi este payload, na forma exata, que a guarda barrou. O `add` nomeia DOIS
# ARQUIVOS; o `tools/` que a acusacao citava esta na linha de baixo, num comando
# de LEITURA que nunca toca o indice.
passa "arquivos + git status -- <dir>/ na linha seguinte" \
  "$ADD tools/check-network-health tools/test_medir_wifi.py
git status --porcelain -- tools/ .agents/runtime/ | sed 's/^/  /'"
passa "arquivo + git diff --stat -- <dir>/ depois" \
  "$ADD ops/provisionamento/comum.sh
git diff --stat -- ops/"
passa "arquivo + echo terminando em barra depois" \
  "$ADD ops/provisionamento/comum.sh
echo 'olhe em docs/'"

# E a travessia NAO pode virar cegueira. Sem os dois casos abaixo, o conserto do
# regex teria trocado o falso positivo por um falso NEGATIVO: um segundo `add`
# de verdade, na linha de baixo, continua sob analise.
barra "segundo add, por diretorio, na linha seguinte" \
  "$ADD ops/provisionamento/comum.sh
$ADD docs/"
barra "primeiro add certo, segundo com -A na linha seguinte" \
  "$ADD ops/provisionamento/comum.sh
$ADD -A"

echo
if [ "$erros" -eq 0 ]; then
  echo "  BANCADA VERDE — a guarda barra o que deve e passa o que deve."
  exit 0
fi
echo "  BANCADA REPROVOU em $erros caso(s)."
exit 1
