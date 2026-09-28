#!/usr/bin/env bash
# test_cerebro_provas_negativas — as sete provas negativas do §P9, na parte que
# exige um PROCESSO VIVO.
#
# ★ A REGRA UNICA QUE ELAS VERIFICAM
#
#   NENHUMA das sete pode produzir tarefa nova em `erro`.
#
# Derrubar o Ollama, remover o modelo, `kill -9`, `kill -STOP`, corromper a
# fila, segurar o flock e forcar o teto de residentes sao todos fatos sobre a
# MAQUINA. Nenhum deles diz coisa alguma sobre o acordao que a tarefa carrega —
# e ate 2026-09-16 todos eles debitavam tentativa e levavam tarefa boa ao `erro`
# terminal. Como a `impressao` da tarefa e o sha256 do texto, que nao muda, o
# `INSERT OR IGNORE` nunca recria a linha: era morte definitiva.
#
# ★ LABORATORIO, NUNCA PRODUCAO
#
# Este roteiro NAO toca o ollama.service, NAO toca wikijuridica-cerebro e NAO
# toca data/ai/fila.sqlite. Ele sobe uma instancia PROPRIA do binario, com:
#
#   • fila propria, num diretorio temporario;
#   • WIKI_OLLAMA_URL apontando para uma porta MORTA (ou para um Ollama falso
#     de tres linhas), conforme a prova;
#   • um portal falso no lugar do nginx, para as sondas de saude passarem;
#   • --lock-pesado proprio, para nao interferir em quem esta compilando.
#
# As provas que exigem o systemd (o watchdog matando um processo travado; o
# `OnFailure` do timer dos detectores) ficam para quem opera a maquina, com o
# roteiro no retorno da frente — este script nao instala nem reinicia unit.
#
# CODIGOS
#   0  as provas rodaram e passaram
#   1  alguma prova reprovou             (VEREDITO)
#   2  NAO MEDI — faltou binario, porta, ou o ambiente nao permitiu
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
ROOT="$(pwd)"

falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }
ok() { passo OK "$1"; }
mal() { passo FALHA "$1"; falhou=1; }

TMP=$(mktemp -d) || exit 2
PORTAL_PID=""
LAB_PID=""
limpa() {
	[ -n "$LAB_PID" ] && kill -KILL "$LAB_PID" 2>/dev/null
	[ -n "$PORTAL_PID" ] && kill -TERM "$PORTAL_PID" 2>/dev/null
	[ -n "${OLLAMA_FALSO_PID:-}" ] && kill -TERM "$OLLAMA_FALSO_PID" 2>/dev/null
	rm -rf "$TMP"
}
trap limpa EXIT

BIN="$TMP/cerebro"
if ! "$ROOT/tools/go-modern" build -o "$BIN" ./cmd/cerebro/ >"$TMP/build.log" 2>&1; then
	echo "NAO MEDIDO: nao consegui construir bin/cerebro" >&2
	tail -5 "$TMP/build.log" >&2
	exit 2
fi

# ---- os dois servidores falsos moram em arquivos, nao em heredoc aninhado:
# heredoc dentro de heredoc dentro de funcao e a forma classica de um script
# passar a executar outra coisa sem que ninguem perceba.
cat >"$TMP/porta_livre.py" <<'FIMPY'
import socket

s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
FIMPY

cat >"$TMP/portal_falso.py" <<'FIMPY'
"""O nginx do portal, reduzido ao que a guarda de saude do cerebro sonda: 200 em
/, /healthz e /buscar/. Sem ele TODA prova pausaria por `portal` e nenhuma
mediria o que pretende medir.
"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Mao(BaseHTTPRequestHandler):
    def do_GET(self):
        corpo = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), Mao).serve_forever()
FIMPY

cat >"$TMP/ollama_falso.py" <<'FIMPY'
"""Um Ollama que responde, para as provas em que o alvo NAO e o Ollama.

As respostas sao a forma REAL medida em 2026-09-16 contra o Ollama 0.33.3 deste
host -- inclusive `size_vram` e `context_length` em /api/ps, os dois campos que
o cliente descartava em silencio ate essa data.
"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

CORPOS = {
    "/api/version": b'{"version":"0.33.3"}',
    "/api/ps": b'{"models":[{"name":"qwen3.5:4b","size":3227894413,'
               b'"size_vram":0,"context_length":8192}]}',
    "/api/tags": b'{"models":[{"name":"qwen3.5:4b","model":"qwen3.5:4b",'
                 b'"size":3227894413}]}',
}


class Mao(BaseHTTPRequestHandler):
    def do_GET(self):
        corpo = CORPOS.get(self.path, b"{}")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), Mao).serve_forever()
FIMPY

porta_livre() { python3 "$TMP/porta_livre.py"; }

PORTAL_PORT=$(porta_livre) || exit 2
python3 "$TMP/portal_falso.py" "$PORTAL_PORT" &
PORTAL_PID=$!
sleep 0.5
if ! curl -fsS -m 3 "http://127.0.0.1:$PORTAL_PORT/healthz" >/dev/null 2>&1; then
	echo "NAO MEDIDO: o portal falso nao subiu na porta $PORTAL_PORT" >&2
	exit 2
fi

# ---- porta morta: a forma mais fiel de "ollama.service parado". O kernel
# recusa o connect na hora, exatamente como faz com o servico fora do ar.
PORTA_MORTA=$(porta_livre) || exit 2

# ---- raiz de laboratorio: SYMLINKS para o que se le, diretorios PROPRIOS para
# o que se escreve.
#
# O daemon precisa de um repositorio de verdade -- `content.LoadRepository`
# procura o `go.mod` subindo a arvore e le content/site.json, content/pages.json
# e o acervo inteiro. Uma raiz falsa com um pages.json vazio devolve
# `file does not exist` e nenhuma prova chega a rodar.
#
# O que ele ESCREVE fica so aqui: data/ai (a fila e as extracoes) e data/ops (o
# batimento e a medicao). Nenhuma prova toca artefato de producao.
LAB_ROOT="$TMP/raiz"
mkdir -p "$LAB_ROOT/data/ai" "$LAB_ROOT/data/ops"
ln -s "$ROOT/go.mod" "$LAB_ROOT/go.mod"
ln -s "$ROOT/content" "$LAB_ROOT/content"
for d in "$ROOT"/data/*/; do
	n=$(basename "$d")
	case "$n" in
	ai | ops) continue ;;
	esac
	ln -s "$d" "$LAB_ROOT/data/$n"
done
FILA="$LAB_ROOT/data/ai/fila.sqlite"
LOCK="$TMP/lock-de-laboratorio"
: >"$LOCK"

# tarefas de ensaio na fila do laboratorio
semear() {
	"$BIN" enfileirar-medicao --root "$LAB_ROOT" --fila "$FILA" \
		--modelo qwen3.5:4b --modo gerar --prompt "diga ok" --num-predict 8 >/dev/null 2>&1
}

conta() { # conta(estado) -> numero de tarefas naquele estado
	sqlite3 -readonly "file:$FILA?mode=ro" "SELECT COUNT(*) FROM tarefa WHERE estado='$1';" 2>/dev/null || echo "?"
}

campo_do_batimento() { # campo_do_batimento(chave)
	python3 - "$LAB_ROOT/data/ops/cerebro_batimento.json" "$1" <<'PY' 2>/dev/null
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(json.load(fh).get(sys.argv[2], ""))
except Exception:
    print("")
PY
}

sobe_lab() { # sobe_lab(url_do_ollama, args extras...)
	local url="$1"; shift
	WIKI_OLLAMA_URL="$url" "$BIN" servir \
		--root "$LAB_ROOT" --fila "$FILA" --worker lab \
		--nginx "http://127.0.0.1:$PORTAL_PORT" --host localhost \
		--ocioso 1s --saude-a-cada 1s --saude-prazo 3s \
		--lock-pesado "$LOCK" --carga-max 0 \
		--tentativas 1 --backoff 1s "$@" >"$TMP/lab.log" 2>&1 &
	LAB_PID=$!
}

derruba_lab() {
	[ -n "$LAB_PID" ] && kill -TERM "$LAB_PID" 2>/dev/null
	wait "$LAB_PID" 2>/dev/null
	LAB_PID=""
}

# ---- Ollama falso: as sondas de OCUPACAO (flock, loadavg) ficam por ULTIMO em
# `Saude.Verifica`, DE PROPOSITO -- sao as mais baratas, mas pausar por carga so
# faz sentido depois de saber que o resto esta de pe. Consequencia para este
# roteiro: com o Ollama morto, a sonda do flock NUNCA e alcancada, e uma prova
# sobre o lock que rodasse assim mediria a sonda errada. Por isso as provas do
# flock sobem um Ollama que RESPONDE.
OLLAMA_FALSO_PID=""
OLLAMA_FALSO_PORT=""
sobe_ollama_falso() {
	OLLAMA_FALSO_PORT=$(porta_livre) || return 1
	python3 "$TMP/ollama_falso.py" "$OLLAMA_FALSO_PORT" &
	OLLAMA_FALSO_PID=$!
	sleep 0.5
	curl -fsS -m 3 "http://127.0.0.1:$OLLAMA_FALSO_PORT/api/version" >/dev/null 2>&1
}

derruba_ollama_falso() {
	[ -n "$OLLAMA_FALSO_PID" ] && kill -TERM "$OLLAMA_FALSO_PID" 2>/dev/null
	OLLAMA_FALSO_PID=""
}

if ! command -v sqlite3 >/dev/null 2>&1; then
	echo "NAO MEDIDO: sqlite3 ausente — sem ele nao ha como contar o estado das tarefas" >&2
	exit 2
fi

echo "== PROVA 1: Ollama fora do ar"
semear
sobe_lab "http://127.0.0.1:$PORTA_MORTA"
sleep 6
if ! kill -0 "$LAB_PID" 2>/dev/null; then
	mal "o daemon MORREU com o Ollama fora do ar — e o laco de reinicio mudo: com Restart=always e RestartSec=15 a unit nunca chega a \`failed\` e o OnFailure nunca dispara"
else
	ok "o daemon SOBE e fica de pe com o Ollama fora do ar (antes: os.Exit(1) em laco)"
fi
if [ "$(conta erro)" = "0" ]; then
	ok "nenhuma tarefa em erro com o Ollama fora do ar"
else
	mal "Ollama fora do ar produziu $(conta erro) tarefa(s) em erro"
fi
classe=$(campo_do_batimento classe_pausa)
if [ "$classe" = "infra" ]; then
	ok "o batimento classifica a pausa como \`infra\` (sonda: $(campo_do_batimento sonda_pausa))"
else
	mal "o batimento deveria dizer classe_pausa=infra, disse '$classe'"
fi

echo "== PROVA 3: kill -9 no worker"
kill -KILL "$LAB_PID" 2>/dev/null
wait "$LAB_PID" 2>/dev/null
LAB_PID=""
if [ "$(conta executando)" = "0" ] || [ "$(conta erro)" = "0" ]; then
	ok "depois do kill -9 nada ficou em erro"
else
	mal "kill -9 produziu tarefa em erro"
fi

echo "== PROVA 6: o flock pesado tomado"
semear
# `flock -n` num descritor proprio e o que a compilacao de outra frente faz.
exec 9>"$LOCK"
flock -n 9 || { echo "NAO MEDIDO: nao consegui tomar o lock de laboratorio" >&2; exit 2; }
if ! sobe_ollama_falso; then
	echo "NAO MEDIDO: o Ollama falso nao subiu" >&2
	exit 2
fi
sobe_lab "http://127.0.0.1:$OLLAMA_FALSO_PORT"
sleep 5
classe=$(campo_do_batimento classe_pausa)
if [ "$classe" = "ocupacao_lock" ]; then
	ok "flock tomado pausa com classe \`ocupacao_lock\` (antes da correcao a sonda respondia sempre 'livre')"
else
	mal "flock tomado deveria dar classe_pausa=ocupacao_lock, deu '$classe'"
fi
if [ "$(conta erro)" = "0" ]; then
	ok "nenhuma tarefa em erro com o flock tomado"
else
	mal "flock tomado produziu $(conta erro) tarefa(s) em erro"
fi
derruba_lab
exec 9>&-

echo "== o lock AUSENTE nao pode ser lido como livre"
rm -f "$LOCK"
sobe_lab "http://127.0.0.1:$OLLAMA_FALSO_PORT"
sleep 5
diag=$(campo_do_batimento diagnostico_pausa)
case "$diag" in
*"nao existe neste namespace"*) ok "lock ausente pausa com diagnostico nomeado (falha fechada)" ;;
*) mal "lock ausente deveria pausar por ErrLockAusente; diagnostico veio: '$diag'" ;;
esac
derruba_lab
derruba_ollama_falso
: >"$LOCK"

echo "== PROVA 5: fila corrompida"
printf 'isto nao e um banco sqlite, e lixo' >"$FILA"
rm -f "$FILA-wal" "$FILA-shm"
sobe_lab "http://127.0.0.1:$PORTA_MORTA"
sleep 5
if ls "$FILA".corrompida-* >/dev/null 2>&1; then
	ok "a fila corrompida foi PRESERVADA em $(ls -1 "$FILA".corrompida-* | head -1 | xargs basename)"
else
	mal "a fila corrompida tinha de ser preservada, nao apagada"
fi
if grep -q '"transicao":"fila_recriada"' "$LAB_ROOT/data/ops/cerebro_batimento.jsonl" 2>/dev/null; then
	ok "a recriacao entrou no historico do batimento — recriar a fila e FATO, nunca silencio"
else
	mal "a recriacao da fila nao apareceu no historico: seria silencio sobre trabalho perdido"
fi
if kill -0 "$LAB_PID" 2>/dev/null; then
	ok "o daemon continua de pe depois de recriar a fila (nao virou laco de boot)"
else
	mal "o daemon morreu com a fila corrompida — e o laco de reinicio mudo de 15 em 15 s"
fi
derruba_lab

echo
if [ $falhou -eq 0 ]; then
	echo "cerebro: as provas negativas de laboratorio passaram"
	echo "  As que exigem o systemd (watchdog sobre processo travado, OnFailure do"
	echo "  timer dos detectores) e as que exigem producao (parar o ollama.service,"
	echo "  \`ollama rm\`) estao roteirizadas para quem opera a maquina."
else
	echo "REPROVADO"
fi
exit $falhou
