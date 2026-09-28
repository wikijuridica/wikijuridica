#!/usr/bin/env bash
# Testes de tools/commit-revalidacao-de-fontes.
#
# POR QUE EXISTEM (2026-09-10). A unit
# wikijuridica-source-evidence-recheck.service ficou `failed` com
# "nao consegui commitar a evidencia de vida das fontes depois de 5 tentativas"
# — o wrapper desistia em 10 s de um indice do git que outra sessao segurava
# durante uma compilacao de pre-commit. Ao ler o laco apareceu um defeito pior:
# o `if` testava um PIPELINE (`git commit ... | tail -2`), entao lia o status do
# `tail`, nao o do git — um commit REPROVADO sairia como sucesso.
#
# Os casos abaixo sao exatamente esses, e nenhum usa o repositorio real.
#
# UMA HIPOTESE MINHA CAIU AQUI, e o registro fica: eu ia afirmar que o `if
# git commit ... | tail -2` descartava o exit do git. Nao descartava —
# `set -uo pipefail` na linha 26 do wrapper propaga a falha do pipeline. A
# mutacao provou: reintroduzir o `| tail -2` deixa este teste VERDE. O defeito
# real do commit reprovado era outro e menor: a causa ("provavelmente
# index.lock") era afirmada sem ser conferida, e a saida do git era descartada.
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FERRAMENTA="$RAIZ/tools/commit-revalidacao-de-fontes"
falhas=0

monta_repo() {
	local tmp="$1"
	mkdir -p "$tmp/tools" "$tmp/data/source-registry"
	cp "$FERRAMENTA" "$tmp/tools/"
	git -C "$tmp" init -q
	git -C "$tmp" config user.email teste@local
	git -C "$tmp" config user.name teste
	printf '{"a":1}\n' >"$tmp/data/source-registry/official_source_url_live_metadata_attempts.jsonl"
	printf '{"b":1}\n' >"$tmp/data/source-registry/official_source_url_live_evidence.jsonl"
	git -C "$tmp" add -A >/dev/null
	git -C "$tmp" commit -qm base >/dev/null
	printf '{"a":2}\n' >>"$tmp/data/source-registry/official_source_url_live_metadata_attempts.jsonl"
	printf '{"b":2}\n' >>"$tmp/data/source-registry/official_source_url_live_evidence.jsonl"
}

# (1) O INDICE OCUPADO POR MAIS DE 10 s NAO PODE MAIS DERRUBAR A UNIT.
tmp="$(mktemp -d)"
monta_repo "$tmp"
: >"$tmp/.git/index.lock"
# 25 s, e o numero e escolhido para DISCRIMINAR: com o orcamento antigo de
# 10 s as esperas 2+4+8 chegam a 14 s e o laco desiste; com 600 s ele espera os
# 25 s e commita. Um bloqueio de 14 s nao separava os dois — a verificacao de
# orcamento acontece ANTES do sleep, entao 10 s ainda toleravam 14.
(
	sleep 25
	rm -f "$tmp/.git/index.lock"
) &
liberador=$!
saida="$("$tmp/tools/commit-revalidacao-de-fontes" 2>&1)"
rc=$?
wait "$liberador" 2>/dev/null
if [ $rc -ne 0 ]; then
	printf 'FALHA (1): desistiu do indice ocupado por 25 s (exit %d)\n%s\n' "$rc" "$saida" >&2
	falhas=$((falhas + 1))
elif ! git -C "$tmp" log --oneline -1 | grep -q "revalidacao diaria"; then
	printf 'FALHA (1): saiu 0 mas nao commitou\n%s\n' "$saida" >&2
	falhas=$((falhas + 1))
else
	echo "  OK indice ocupado por 25 s: espera e commita (o teto antigo desistia em ~14 s)"
fi
rm -rf "$tmp"

# (2) COMMIT REPROVADO PELO PRE-COMMIT NAO PODE SAIR COMO SUCESSO.
tmp="$(mktemp -d)"
monta_repo "$tmp"
mkdir -p "$tmp/.git/hooks"
cat >"$tmp/.git/hooks/pre-commit" <<'HOOK'
#!/usr/bin/env bash
echo "pre-commit: reprovado de proposito pelo teste" >&2
exit 1
HOOK
chmod +x "$tmp/.git/hooks/pre-commit"
saida="$("$tmp/tools/commit-revalidacao-de-fontes" 2>&1)"
rc=$?
if [ $rc -eq 0 ]; then
	printf 'FALHA (2): pre-commit reprovou e a ferramenta saiu 0\n%s\n' "$saida" >&2
	falhas=$((falhas + 1))
elif ! git -C "$tmp" log --oneline -1 | grep -q "base"; then
	printf 'FALHA (2): commitou apesar do pre-commit reprovar\n%s\n' "$saida" >&2
	falhas=$((falhas + 1))
elif ! printf '%s' "$saida" | grep -q "reprovou"; then
	printf 'FALHA (2): reprovou sem dizer que foi o git, nao o indice\n%s\n' "$saida" >&2
	falhas=$((falhas + 1))
else
	echo "  OK pre-commit reprovado devolve exit 1 e nao inventa commit"
fi
rm -rf "$tmp"

# (3) SEM MUDANCA, NAO HA O QUE COMMITAR — e isso nao e falha.
tmp="$(mktemp -d)"
monta_repo "$tmp"
# ARVORE LIMPA POR COMMIT, NAO POR DESCARTE. Ate 2026-09-11 esta linha era
# `git checkout -q -- . || git stash`, e as duas metades sao comandos que o
# contrato proibe no repositorio — `check-shell-script-quality` as acusa em
# `shell_script_quality_destructive_git_command`, com razao, porque quem le o
# script aprende o padrao errado mesmo o alvo sendo um `mktemp -d`.
#
# O estado que o caso (3) precisa e "nada a commitar", e commitar o que
# `monta_repo` acrescentou entrega esse estado sem descartar nada: o append
# vira o commit `limpa` e a arvore fica igual ao HEAD.
git -C "$tmp" add -A >/dev/null
git -C "$tmp" commit -qm limpa >/dev/null 2>&1
saida="$("$tmp/tools/commit-revalidacao-de-fontes" 2>&1)"
rc=$?
if [ $rc -ne 0 ]; then
	printf 'FALHA (3): arvore limpa devolveu exit %d\n%s\n' "$rc" "$saida" >&2
	falhas=$((falhas + 1))
else
	echo "  OK arvore limpa sai 0 sem commitar"
fi
rm -rf "$tmp"

if [ $falhas -gt 0 ]; then
	echo "REPROVADO: $falhas caso(s)" >&2
	exit 1
fi
echo "test_commit_revalidacao_de_fontes: ok"
