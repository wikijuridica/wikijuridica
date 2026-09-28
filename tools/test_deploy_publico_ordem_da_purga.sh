#!/usr/bin/env bash
# Prova que a transacao INVALIDA A ORIGEM ANTES de purgar a borda -- e que a
# invalidacao que falha nao derruba o deploy nem passa calada.
#
# POR QUE (medido 2026-09-16): ate hoje o deploy purgava a borda e nunca tocava
# na zona wj_dyn do nginx, cujo s-maxage para gemea, /api/v1 e descritores e de
# SETE DIAS. O passo 5 AQUECE a origem, e aquecer e um GET que recebe HIT do
# objeto anterior. Resultado: a borda purgada volta a origem no primeiro MISS e
# repopula com o corpo de ANTES da publicacao. Nas 129 rotas carimbadas nas 24 h
# daquele dia, 125 gemeas estavam velhas na borda contra 0 no HTML, todas com
# `age` ~12,2 ks -- a idade da propria publicacao. Controle numa rota nomeada:
# purgar so a borda de /noticias/index.md devolveu MISS em 1,11 s com o corpo
# ANTIGO; invalidar a origem antes devolveu MISS em 1,03 s com o corpo do Go.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

FONTE="${DEPLOY_PUBLICO:-tools/deploy-publico}"

# ---------- 1. a ORDEM, no arquivo: cada purga de borda por lista vem depois da
#               invalidacao da origem da MESMA lista, dentro de 5 linhas.
#
# A JANELA DE 5 LINHAS E PARTE DA GUARDA. Hoje ha uma linha entre as duas
# (`PURGE_TETO=$((PURGE_TETO + 1))`). Quem inserir mais de quatro linhas entre a
# invalidacao e a purga faz este teste reprovar -- e a saida certa e mover a
# invalidacao para junto da purga, nao alargar a janela: o que a guarda protege e
# a ADJACENCIA, porque comando no meio e onde um `return` antecipado se esconde.
mapfile -t purgas < <(grep -n 'tools/purge-edge-cache --de-arquivo "\$PURGE_TODOS"' "$FONTE" | cut -d: -f1)
if [[ "${#purgas[@]}" -lt 2 ]]; then
	passo FALHA "esperava ao menos 2 purgas de borda por lista em $FONTE (achei ${#purgas[@]})"
	falhou=1
fi
for linha in "${purgas[@]}"; do
	inicio=$((linha > 5 ? linha - 5 : 1))
	if sed -n "${inicio},${linha}p" "$FONTE" | grep -q 'invalida_origem_relatando "\$PURGE_TODOS"'; then
		passo OK "linha $linha: a origem e invalidada antes da purga da borda"
	else
		passo FALHA "linha $linha: purga de borda SEM invalidar a origem antes -- o primeiro MISS repopula o velho"
		falhou=1
	fi
done

# ---------- 2. a FUNCAO: falha da invalidacao avisa e NAO derruba o deploy
bloco=$(sed -n '/^invalida_origem_da_lista()/,/^}$/p;/^invalida_origem_relatando()/,/^}$/p' "$FONTE")
[[ -n "$bloco" ]] || {
	passo FALHA "bloco das funcoes de invalidacao nao encontrado em $FONTE"
	exit 1
}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/tools"
printf '%s\n' '/a/index.md' >"$TMP/lista"
eval "$bloco"

cat >"$TMP/tools/purge-origin-cache" <<'STUB'
#!/usr/bin/env bash
echo "2 rota(s), 24933 arquivo(s) na zona, 4 objeto(s) removidos, 0 restante(s), 0 recriado(s)"
exit 0
STUB
cat >"$TMP/tools/purge-origin-cache-falha" <<'STUB'
#!/usr/bin/env bash
echo "FALHA: 2 objeto(s) continuam na zona depois da remocao." >&2
exit 2
STUB
chmod +x "$TMP/tools/purge-origin-cache" "$TMP/tools/purge-origin-cache-falha"

pushd "$TMP" >/dev/null || exit 1
saida="$(invalida_origem_relatando "$TMP/lista" 2>&1)"
codigo=$?
popd >/dev/null || exit 1
if [[ "$codigo" -eq 0 && "$saida" == *"removidos"* && "$saida" != *AVISO* ]]; then
	passo OK "invalidacao bem-sucedida: relata os objetos e segue calada"
else
	passo FALHA "invalidacao bem-sucedida deu codigo=$codigo saida='$saida'"
	falhou=1
fi

pushd "$TMP" >/dev/null || exit 1
mv tools/purge-origin-cache-falha tools/purge-origin-cache
saida="$(invalida_origem_relatando "$TMP/lista" 2>&1)"
codigo=$?
popd >/dev/null || exit 1
if [[ "$codigo" -eq 0 ]]; then
	passo OK "invalidacao que falha NAO derruba a transacao (a publicacao ja esta no disco)"
else
	passo FALHA "invalidacao que falha derrubou a transacao (codigo=$codigo)"
	falhou=1
fi
if [[ "$saida" == *AVISO* && "$saida" == *restantes=0* ]]; then
	passo OK "a falha avisa e diz como conferir"
else
	passo FALHA "a falha passou calada ou sem saida acionavel: '$saida'"
	falhou=1
fi

exit "$falhou"
