#!/usr/bin/env bash
# Prova que o diagnostico da suite diaria DECLARA quanto cortou, antes da amostra.
#
# POR QUE (medido 2026-09-10). `roda()` gravava `printf ... | tail -4000` e o
# comentario logo acima afirmava "o corte avisa que cortou". Nao avisava: `tail`
# imprime as ultimas N linhas em silencio. Quem abre
# `.agents/runtime/qualidade-diaria/<dia>/<etapa>.log` nao tinha como saber se
# estava lendo a saida inteira ou o rabo dela — e o corte e no COMECO, que e onde
# o `go test` poe a primeira falha quando o -timeout dispara e ele despeja o stack
# de todas as goroutines. Concluir sobre a amostra achando que e a populacao e o
# que o R3 proibe, e neste runner era o desenho.
#
# O teste extrai a funcao REAL do arquivo real e a executa. Nao ha copia da
# implementacao aqui: renomear ou apagar a funcao quebra a extracao, em vez de
# deixar um teste verde sobre codigo que nao existe mais.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

fonte=tools/run-qualidade-diaria
bloco=$(sed -n '/^TETO_DE_DIAGNOSTICO=/,/^}$/p' "$fonte")
[[ "$bloco" == *"corpo_com_corte()"* ]] || {
	echo "FALHA: corpo_com_corte nao encontrada em $fonte"
	exit 1
}
eval "$bloco"

teto=$(printf '%s\n' "$bloco" | sed -n 's/^TETO_DE_DIAGNOSTICO=\([0-9]*\)$/\1/p')
[[ -n "$teto" ]] || {
	echo "FALHA: teto nao lido"
	exit 1
}

# ---------- caso 1: saida MAIOR que o teto -> declara o numero exato de omitidas
total=$((teto + 137))
grande=$(seq 1 "$total")
saida=$(corpo_com_corte "$grande")
cabecalho=$(printf '%s\n' "$saida" | head -1)
if [[ "$cabecalho" == "# linhas_totais=$total omitidas=137 "* ]]; then
	passo OK "declara linhas_totais=$total omitidas=137"
else
	passo FALHA "cabecalho errado: $cabecalho"
	falhou=1
fi

# ---------- caso 2: a declaracao vem ANTES da amostra, nao depois
if [[ "$cabecalho" == "#"* ]]; then
	passo OK "cardinalidade na PRIMEIRA linha"
else
	passo FALHA "a amostra veio antes da cardinalidade"
	falhou=1
fi

# ---------- caso 3: o corte e no COMECO, e o log tem de dizer isso
if [[ "$cabecalho" == *"corte no COMECO"* ]]; then
	passo OK "o cabecalho diz de que LADO o corte caiu"
else
	passo FALHA "nao diz onde cortou: quem le nao sabe que a primeira falha sumiu"
	falhou=1
fi

# ---------- caso 4: o corpo tem exatamente teto+1 linhas (cabecalho + amostra)
linhas=$(printf '%s\n' "$saida" | wc -l)
if [[ "$linhas" -eq $((teto + 1)) ]]; then
	passo OK "amostra respeita o teto de $teto"
else
	passo FALHA "amostra com $linhas linhas, esperado $((teto + 1))"
	falhou=1
fi

# ---------- caso 5: as linhas entregues sao as ULTIMAS, nao as primeiras
ultima=$(printf '%s\n' "$saida" | tail -1)
primeira_da_amostra=$(printf '%s\n' "$saida" | sed -n '2p')
if [[ "$ultima" == "$total" && "$primeira_da_amostra" == "138" ]]; then
	passo OK "entrega o rabo (138..$total), como o cabecalho afirma"
else
	passo FALHA "amostra $primeira_da_amostra..$ultima nao casa com o declarado"
	falhou=1
fi

# ---------- FALSO POSITIVO: saida MENOR que o teto nao pode alegar corte
pequena=$(seq 1 3)
saida=$(corpo_com_corte "$pequena")
cabecalho=$(printf '%s\n' "$saida" | head -1)
if [[ "$cabecalho" == "# linhas_totais=3 omitidas=0 "* ]]; then
	passo OK "falso positivo: sem corte declara omitidas=0"
else
	passo FALHA "declarou corte onde nao houve: $cabecalho"
	falhou=1
fi
corpo=$(printf '%s\n' "$saida" | tail -n +2)
if [[ "$corpo" == "$pequena" ]]; then
	passo OK "e entrega a saida inteira, intacta"
else
	passo FALHA "saida curta foi alterada"
	falhou=1
fi

# ---------- nenhum sitio de diagnostico pode voltar a cortar em silencio
orfaos=$(grep -c 'tail -4000' "$fonte" || true)
if [[ "$orfaos" -eq 0 ]]; then
	passo OK "nenhum tail -4000 solto em $fonte"
else
	passo FALHA "$orfaos corte(s) em silencio voltaram a $fonte"
	falhou=1
fi

if [[ "$falhou" -eq 0 ]]; then
	echo "OK: o corte do diagnostico e declarado"
	exit 0
fi
echo "FALHOU"
exit 1
