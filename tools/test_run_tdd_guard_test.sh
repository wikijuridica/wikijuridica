#!/usr/bin/env bash
# Prova que tools/run-tdd-guard-test entrega ao TDD Guard o relatorio que ele le,
# E que o codigo de saida do wrapper e o do `go test`, nao o do reporter.
#
# POR QUE ESTE TESTE EXISTE. O wrapper e um PIPE: `go test -json | tdd-guard-go`.
# Em pipe, `$?` e o codigo do ULTIMO comando -- o reporter, que sai 0 mesmo com a
# suite vermelha. Um wrapper escrito da forma ingenua transforma teste reprovado
# em "verde" silencioso, que e exatamente a classe de defeito que este repositorio
# ja pagou ("cmd | tail engole o exit real"). Por isso o caso 3 aqui roda o wrapper
# contra um pacote inexistente: `go test` reprova, o reporter nao, e so quem le
# PIPESTATUS[0] devolve o codigo certo.
#
# Rodar:
#     ./tools/test_run_tdd_guard_test.sh
#
# Teste de MUTACAO (um teste que nunca reprova nao prova nada):
#     WRAPPER_TDD_GUARD=/tmp/wrapper-mutante ./tools/test_run_tdd_guard_test.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RAIZ=$(pwd)

WRAPPER=${WRAPPER_TDD_GUARD:-./tools/run-tdd-guard-test}
RELATORIO="$RAIZ/.claude/tdd-guard/data/test.json"

# Pacote-alvo: o MENOR do repositorio com teste (167 linhas), para que este teste
# custe segundos e nao minutos na suite diaria.
PACOTE=./internal/pageinline/

falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }
ok() { passo 'OK  ' "$1"; }
erro() {
	passo 'FALHA' "$1"
	falhou=1
}

echo "test_run_tdd_guard_test: wrapper=$WRAPPER"

# --- caso 1: o wrapper existe e e executavel -------------------------------
if [ -x "$WRAPPER" ]; then
	ok "wrapper existe e e executavel"
else
	erro "wrapper ausente ou nao-executavel: $WRAPPER"
	echo "test_run_tdd_guard_test: REPROVADO" >&2
	exit 1
fi

# --- caso 3: REGRESSAO -- exit do go test, nao do reporter -----------------
# Pacote inexistente: `go test` reprova, `tdd-guard-go` sai 0. Wrapper que usa
# `$?` do pipe (ou so `set -o pipefail` sem ler PIPESTATUS[0]) devolveria 0 aqui
# e esconderia suite vermelha.
saida=$("$WRAPPER" ./internal/pacote-inexistente-tdd-guard/ 2>&1)
codigo=$?
if [ "$codigo" -ne 0 ]; then
	ok "pacote invalido propaga exit $codigo (nao engole o do reporter)"
else
	erro "pacote invalido devolveu exit 0 -- o wrapper engoliu o codigo do go test"
	printf '%s\n' "$saida" | tail -10 >&2
fi

# --- caso 4: o wrapper NUNCA EXECUTA o padrao full-tree --------------------
# `./...` e barrado por .claude/hooks/block-heavy-go.sh (exit 2) e por
# permissions.deny. Um default full-tree tornaria o wrapper inexecutavel pela
# sessao que ele existe para servir.
#
# A checagem ignora COMENTARIO de proposito. O proprio block-heavy-go.sh ja pagou
# esse defeito: a analise crua barrava documentacao que CITAVA o comando proibido,
# e assim impedia de documentar a regra que ela aplica. Citar o padrao para
# explicar por que ele nao se usa e o mecanismo pelo qual a regra se propaga.
if sed 's/[[:space:]]*#.*$//' "$WRAPPER" | grep -qF './...'; then
	erro "wrapper EXECUTA o padrao full-tree ./... -- barrado pelo hook do repo"
else
	ok "wrapper nao executa o padrao full-tree"
fi

# --- caso 5: reporter quebrado nao passa por suite verde -------------------
# Se tdd-guard-go falha, o relatorio nao reflete a rodada e o TDD Guard fica
# cego. Verde silencioso ai e pior que vermelho: a sessao segue confiando num
# estado de suite que ninguem atualizou. O wrapper tem de sair diferente de zero
# E dizer que quem falhou foi o reporter, nao o teste.
FALSO=$(mktemp -d)
trap 'rm -rf "$FALSO"' EXIT
cat >"$FALSO/tdd-guard-go" <<'REPORTER'
#!/usr/bin/env bash
cat >/dev/null
exit 3
REPORTER
chmod +x "$FALSO/tdd-guard-go"

saida=$(PATH="$FALSO:$PATH" "$WRAPPER" "$PACOTE" 2>&1)
codigo=$?
if [ "$codigo" -ne 0 ] && [[ "$saida" == *reporter* ]]; then
	ok "reporter quebrado reprova com mensagem propria (exit $codigo)"
else
	erro "reporter quebrado devolveu exit $codigo sem acusar o reporter"
	printf '%s\n' "$saida" | tail -10 >&2
fi

# --- caso 2 (POR ULTIMO): roda um pacote verde e grava o relatorio ---------
# A ORDEM AQUI E CONTRATO, nao estetica. Cada caso sobrescreve
# .claude/tdd-guard/data/test.json, e o ultimo que escrever e o que o TDD Guard
# vai LER depois. Com o caso verde no meio, o arquivo terminava contendo a falha
# de compilacao fabricada pelo caso 3 -- e a suite diaria deixava o guard
# convencido de que o repositorio nao compila. Por isso o caso verde fecha a
# bateria: o estado final do relatorio tem de ser verdadeiro.
rm -f "$RELATORIO"
saida=$("$WRAPPER" "$PACOTE" 2>&1)
codigo=$?

if [ "$codigo" -eq 0 ]; then
	ok "pacote verde devolve exit 0"
else
	erro "pacote verde devolveu exit $codigo"
	printf '%s\n' "$saida" | tail -20 >&2
fi

if [ -s "$RELATORIO" ]; then
	ok "relatorio gravado em .claude/tdd-guard/data/test.json"
else
	erro "relatorio ausente ou vazio: $RELATORIO"
fi

# O relatorio precisa ser JSON valido COM pelo menos um teste aprovado. Arquivo
# existir nao basta: um reporter que grava `{}` deixaria o TDD Guard cego.
if python3 - "$RELATORIO" <<'PY'; then
import json, sys
try:
	dado = json.load(open(sys.argv[1], encoding='utf-8'))
except Exception as e:  # arquivo ausente, truncado ou nao-JSON
	print(f'json invalido: {e}', file=sys.stderr)
	sys.exit(1)
modulos = dado.get('testModules') or []
casos = [t for m in modulos for t in (m.get('tests') or [])]
aprovados = [t for t in casos if t.get('state') == 'passed']
if not aprovados:
	print(f'nenhum teste aprovado no relatorio (modulos={len(modulos)} casos={len(casos)})', file=sys.stderr)
	sys.exit(1)
print(f'{len(aprovados)} aprovados de {len(casos)} casos em {len(modulos)} modulos')
PY
	ok "relatorio e JSON com teste aprovado"
else
	erro "relatorio nao tem teste aprovado legivel"
fi

if [ "$falhou" -eq 0 ]; then
	echo "test_run_tdd_guard_test: OK"
	exit 0
fi
echo "test_run_tdd_guard_test: REPROVADO" >&2
exit 1
