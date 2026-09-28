#!/usr/bin/env bash
# Prova por MUTACAO do teste de regressao do renovador de heartbeat do build
# lock (run-go-cmd-cached), 2026-09-05.
#
# O defeito: a subshell do renovador dormia em PRIMEIRO plano, entao o `kill`
# de stop_build_lock_heartbeat_renewer alcancava a subshell e nunca o `sleep`.
# O sono ficava orfao, era adotado pelo subreaper que envelopa o wrapper e
# `supervise-process-tree --fail-on-descendant-cleanup` devolvia 125.
#
# Um teste de regressao que nunca foi visto reprovar nao prova nada. Aqui a
# ancora e um COMMIT FIXO -- nunca HEAD, que anda e transformaria a prova em
# tautologia assim que a correcao entrasse no historico.
#
# O mutante entra por symlink farm (`cp -as`): RUNNER_SOURCE nao resolve o
# link e pega o arquivo mutado; REPO_ROOT resolve e continua apontando o repo
# real, onde vivem go-modern e a toolchain que o teste precisa de verdade.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANCORA='58de2a6ef45335fb2b174b5e6d733fe9cd42b189:tools/run-go-cmd-cached'
# Os tres testes de regressao que nasceram desta frente. TODOS reprovam contra a
# ancora, cada um pelo seu defeito:
#
#   orphan       -> o sono em primeiro plano ficava orfao      (sintoma abaixo)
#   zero_padded  -> `00`/`007` eram aceitos como intervalo
#   term_ignored -> `wait` sem teto pendurava o wrapper
#
# Rodar os tres contra a mesma ancora custa uma execucao a mais e prova que
# NENHUM deles esta cego -- teste de regressao que ninguem viu reprovar nao e
# prova, e um comentario com pretensao.
TESTES=(
	'test_build_lock_heartbeat_renewer_leaves_no_orphan_under_strict_supervisor'
	'test_build_lock_heartbeat_interval_rejects_zero_padded_values'
	'test_build_lock_heartbeat_renewer_stop_is_bounded_when_term_is_ignored'
)
# So o primeiro tem "motivo errado" plausivel (o wrapper recusar o comando antes
# de tomar o lock), entao so ele exige sintoma nomeado.
SINTOMA='descendant_cleanup_after_leader_exit'

falhas=0
reprova() {
	printf 'REPROVA: %s\n' "$1" >&2
	falhas=$((falhas + 1))
}

T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT

if ! cp -as "$RAIZ/tools" "$T/tools"; then
	printf 'INFRA: nao consegui montar o symlink farm em %s\n' "$T" >&2
	exit 75
fi
rm -f "$T/tools/run-go-cmd-cached"
rm -rf "$T/tools/__pycache__"
if ! git -C "$RAIZ" show "$ANCORA" >"$T/tools/run-go-cmd-cached"; then
	printf 'INFRA: ancora %s ilegivel\n' "$ANCORA" >&2
	exit 75
fi
chmod +x "$T/tools/run-go-cmd-cached"

if ! grep -q 'while sleep "\$LOCK_HEARTBEAT_INTERVAL_SECONDS"' "$T/tools/run-go-cmd-cached"; then
	reprova "a ancora $ANCORA nao contem mais o sono em primeiro plano: a mutacao deixou de mutar"
fi

for TESTE in "${TESTES[@]}"; do
	saida_mutante="$(cd "$RAIZ" && PYTHONPATH="$RAIZ" PYTHONDONTWRITEBYTECODE=1 \
		timeout 300 python3 "$T/tools/test_run_go_cmd_cached.py" -k "$TESTE" 2>&1)"
	rc_mutante=$?
	if [ "$rc_mutante" = 124 ]; then
		printf 'INFRA: o mutante de %s estourou o timeout de 300s\n' "$TESTE" >&2
		exit 75
	fi
	if [ "$rc_mutante" = 0 ]; then
		reprova "$TESTE: o mutante PASSOU -- o teste esta cego ao defeito que deveria pegar"
	fi
	case "$TESTE" in
	*leaves_no_orphan*)
		if ! printf '%s' "$saida_mutante" | grep -q "$SINTOMA"; then
			reprova "$TESTE: o mutante reprovou por outro motivo -- nao achei '$SINTOMA'"
			printf '%s\n' "$saida_mutante" | tail -20 >&2
		fi
		;;
	esac

	saida_atual="$(cd "$RAIZ" && PYTHONPATH="$RAIZ" PYTHONDONTWRITEBYTECODE=1 \
		timeout 300 python3 "$RAIZ/tools/test_run_go_cmd_cached.py" -k "$TESTE" 2>&1)"
	rc_atual=$?
	if [ "$rc_atual" = 124 ]; then
		printf 'INFRA: o codigo atual de %s estourou o timeout de 300s\n' "$TESTE" >&2
		exit 75
	fi
	if [ "$rc_atual" != 0 ]; then
		reprova "$TESTE: o codigo ATUAL reprova (rc=$rc_atual)"
		printf '%s\n' "$saida_atual" | tail -20 >&2
	fi
	printf '  %s: mutante rc=%s, atual rc=%s\n' "$TESTE" "$rc_mutante" "$rc_atual"
done

if [ "$falhas" != 0 ]; then
	printf 'test_run_go_cmd_cached_heartbeat_mutacao: %d verificacao(oes) reprovada(s)\n' "$falhas" >&2
	exit 1
fi
printf 'test_run_go_cmd_cached_heartbeat_mutacao: os %d testes reprovam contra a ancora e passam no codigo atual\n' "${#TESTES[@]}"
