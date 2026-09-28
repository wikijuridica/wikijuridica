#!/usr/bin/env bash
# Bancada de `alvos_do_registro` — a funcao que tirou o varrimento de diretorio
# das duas etapas de commit de `tools/run-daily-content`.
#
# ★ POR QUE ELA EXISTE, com os numeros do dia
#
# As duas etapas adicionavam o DIRETORIO inteiro. Medido em 2026-09-16: 69
# arquivos em `portfolio_v2` e 879 em `v2_pages`, contra SETE produtores no
# registro. Tudo que qualquer outra frente tocasse ali entrava no commit da onda,
# sob a mensagem da onda, sem revisao — e a onda roda sozinha as 04:20.
#
# O contrato de maquina ja proibia adicionar diretorio ("ja varreu trabalho
# nao-commitado de outra sessao tres vezes"); estas duas linhas eram a excecao
# que sobrava, no pior lugar possivel.
#
# A funcao e extraida do arquivo REAL por ancora literal — copiar o corpo para
# ca criaria uma segunda versao que envelhece sozinha, que e o defeito que
# `teste-que-reimplementa-nao-testa` registra.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
falhas=0

confere() {
	if [[ "$1" != "$2" ]]; then
		printf 'FALHA: %s\n  esperado: %s\n  veio    : %s\n' "$3" "$2" "$1" >&2
		falhas=$((falhas + 1))
	fi
}

confere_contem() {
	if ! grep -qF "$2" <<<"$1"; then
		printf 'FALHA: %s\n  nao contem: %s\n' "$3" "$2" >&2
		falhas=$((falhas + 1))
	fi
}

# EXTRACAO POR ANCORA do arquivo real.
corpo="$(sed -n '/^alvos_do_registro()/,/^}/p' "$RAIZ/tools/run-daily-content")"
if [[ -z "$corpo" ]]; then
	echo "FALHA: nao achei alvos_do_registro em tools/run-daily-content" >&2
	exit 1
fi
eval "$corpo"

cd "$RAIZ" || exit 1

# --- CONTROLE POSITIVO: a funcao devolve caminhos, e sao os do registro -------
saida_shard="$(alvos_do_registro shard)"
confere_contem "$saida_shard" "data/editorial/v2_pages/stj-tema-derivado-01.jsonl" \
	"o shard declarado no registro tem de sair"
saida_port="$(alvos_do_registro portfolio)"
confere_contem "$saida_port" "data/editorial/portfolio_v2/jurisprudencia-stj-derivada-01.jsonl" \
	"o portfolio declarado no registro tem de sair"

# --- O QUE ELA NAO PODE DEVOLVER: o diretorio inteiro ------------------------
# 879 arquivos em v2_pages contra 7 produtores. Se a contagem se aproximar do
# diretorio, o varrimento voltou por outro caminho.
n_shard="$(wc -l <<<"$saida_shard")"
n_dir="$(find data/editorial/v2_pages -name '*.jsonl' | wc -l)"
if ((n_shard >= n_dir)); then
	printf 'FALHA: a funcao devolveu %s caminho(s) para um diretorio de %s — isso e varrimento\n' \
		"$n_shard" "$n_dir" >&2
	falhas=$((falhas + 1))
fi
if ((n_shard < 3)); then
	printf 'FALHA: so %s caminho(s); o registro declara mais, e teste com amostra minuscula passa por vacuidade\n' \
		"$n_shard" >&2
	falhas=$((falhas + 1))
fi

# --- TODO caminho devolvido EXISTE -------------------------------------------
while read -r caminho; do
	[[ -n "$caminho" ]] || continue
	if [[ ! -e "$caminho" ]]; then
		printf 'FALHA: caminho inexistente devolvido: %s\n' "$caminho" >&2
		falhas=$((falhas + 1))
	fi
done <<<"$saida_shard"

# --- FALHA RUIDOSA: registro ilegivel NAO cai de volta no diretorio -----------
# Cair de volta trocaria um defeito conhecido por um silencioso.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat >"$tmp/listar-produtores-de-pagina" <<'FALSO'
#!/usr/bin/env bash
echo "registro corrompido" >&2
exit 1
FALSO
chmod +x "$tmp/listar-produtores-de-pagina"
mkdir -p "$tmp/raiz/tools"
cp "$tmp/listar-produtores-de-pagina" "$tmp/raiz/tools/"
(
	cd "$tmp/raiz" || exit 1
	eval "$corpo"
	if alvos_do_registro shard >/dev/null 2>&1; then
		echo "FALHA: registro ilegivel devolveu sucesso — a onda commitaria sem saber o que" >&2
		exit 1
	fi
)
confere "$?" "0" "registro ilegivel tem de fazer a funcao falhar"

# --- ARGUMENTO DESCONHECIDO tambem falha -------------------------------------
if alvos_do_registro coluna-que-nao-existe >/dev/null 2>&1; then
	echo "FALHA: argumento desconhecido devolveu sucesso" >&2
	falhas=$((falhas + 1))
fi


# --- CENARIO PROPRIO: registro que declara arquivo INEXISTENTE ---------------
# Ate 2026-09-16 este caso era exercitado por acidente, porque o shard de
# acordaos ainda nao existia. Assim que a frente P6a o criou, o mutante que
# remove o `[[ -e ]]` passou a SOBREVIVER: a fixture deixou de exercitar o
# cenario sem que nada ficasse vermelho. Cenario proprio nao depende do estado
# de producao.
mkdir -p "$tmp/cenario/tools" "$tmp/cenario/data/editorial/v2_pages"
cat >"$tmp/cenario/tools/listar-produtores-de-pagina" <<'REGISTRO'
#!/usr/bin/env bash
printf 'a\t./cmd/a\tdata/editorial/v2_pages/existe-01.jsonl\tdata/editorial/v2_pages/existe-01.jsonl\tE\t1\n'
printf 'b\t./cmd/b\tdata/editorial/v2_pages/fantasma-01.jsonl\tdata/editorial/v2_pages/fantasma-01.jsonl\tF\t1\n'
REGISTRO
chmod +x "$tmp/cenario/tools/listar-produtores-de-pagina"
: >"$tmp/cenario/data/editorial/v2_pages/existe-01.jsonl"
saida_cenario="$(cd "$tmp/cenario" && eval "$corpo" && alvos_do_registro shard)"
confere_contem "$saida_cenario" "existe-01.jsonl" "o arquivo que existe tem de sair"
if grep -qF "fantasma" <<<"$saida_cenario"; then
	echo "FALHA: caminho declarado no registro mas AUSENTE no disco foi devolvido — " >&2
	echo "  o commit receberia um pathspec que nao casa nada e a etapa mentiria" >&2
	falhas=$((falhas + 1))
fi

# --- O PONTO DE CHAMADA, e nao so a funcao -----------------------------------
# A funcao pode estar perfeita e as duas etapas continuarem varrendo o diretorio.
# Foi esse o mutante que sobreviveu na primeira rodada desta bancada.
for diretorio in data/editorial/v2_pages data/editorial/portfolio_v2; do
	if grep -qE "git add $diretorio\b" "$RAIZ/tools/run-daily-content"; then
		printf 'FALHA: a onda voltou a adicionar o DIRETORIO %s ao indice\n' "$diretorio" >&2
		falhas=$((falhas + 1))
	fi
done
if ! grep -qF 'ALVOS_PAGINAS[@]' "$RAIZ/tools/run-daily-content"; then
	echo "FALHA: a etapa de paginas nao usa mais os caminhos do registro" >&2
	falhas=$((falhas + 1))
fi
if ! grep -qF 'ALVOS_PORTFOLIO[@]' "$RAIZ/tools/run-daily-content"; then
	echo "FALHA: a etapa de portfolio nao usa mais os caminhos do registro" >&2
	falhas=$((falhas + 1))
fi


# --- REGISTRO QUE SO DECLARA FANTASMA: a funcao FALHA -------------------------
# Este caso fecha o contrato da funcao, e nao so o do chamador. Com a lista
# vazia o ponto de chamada ja para a onda (`((${#ALVOS[@]} == 0))`), entao um
# `return 0` mudo aqui seria INERTE — mas contrato implicito e o que some na
# proxima edicao. A funcao declara: lista vazia e erro.
mkdir -p "$tmp/so-fantasma/tools" "$tmp/so-fantasma/data/editorial/v2_pages"
cat >"$tmp/so-fantasma/tools/listar-produtores-de-pagina" <<'SOFANTASMA'
#!/usr/bin/env bash
printf 'b\t./cmd/b\tdata/editorial/v2_pages/fantasma-01.jsonl\tdata/editorial/v2_pages/fantasma-01.jsonl\tF\t1\n'
SOFANTASMA
chmod +x "$tmp/so-fantasma/tools/listar-produtores-de-pagina"
(
	cd "$tmp/so-fantasma" || exit 1
	eval "$corpo"
	if alvos_do_registro shard >/dev/null 2>&1; then
		echo "FALHA: registro que so declara arquivo ausente devolveu sucesso com lista vazia" >&2
		exit 1
	fi
)
confere "$?" "0" "lista vazia tem de fazer a funcao falhar"

if ((falhas > 0)); then
	printf 'test_alvos_do_registro: %s falha(s)\n' "$falhas" >&2
	exit 1
fi
echo "test_alvos_do_registro: ok"
