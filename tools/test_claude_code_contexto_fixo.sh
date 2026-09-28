#!/usr/bin/env bash
# Invólucro de tools/check-claude-code-contexto-fixo para o tools/run-qualidade-diaria,
# que descobre tools/test_*.sh por glob (plano IDE_TERMINAL_20260923 §8 frente 4 item 8;
# refutação 2, item 18: "etapa nomeada" exigiria editar o runner, o glob não).
#
# Mede o transcript INTERATIVO mais novo de ~/.claude/projects/<slug do repo>/: o check
# pula `claude -p` (entrypoint sdk-cli, sem registro permission-mode), sessão sem 1º turno
# e continuação pós-compactação — o transcript pequeno da bancada E2E passaria no teto de
# 82.000 pela sessão errada (refutação 2, item 23).
#
# Exit, na convenção do runner (run-qualidade-diaria, bloco dos test_*.sh):
#   0   verde — todas as réguas cabem;
#   1   vermelho — régua violada (AGENTS.md no contexto, instruções > 62.000 B,
#       skill_listing > 20.000 B, plugin ou conector claude.ai barrado nas listagens,
#       prompt_total do 1º turno > 82.000, `Bash true` > 0,5 s);
#   75  não mediu (sem sessão interativa com 1º turno, CLAUDE_CONFIG_DIR sem transcripts):
#       infra ausente, nunca veredito sobre o produto, e nunca verde.
# O JSON do check vai para a saída (só caminhos, contagens e bytes; nenhum conteúdo).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 75

python3 ./tools/check-claude-code-contexto-fixo "$@"
rc=$?
case "$rc" in
0) exit 0 ;;
1) exit 1 ;;
2) echo "contexto-fixo: nao medido (rc 2 do check -> 75, infra)" >&2; exit 75 ;;
*) echo "contexto-fixo: rc inesperado $rc do check" >&2; exit 1 ;;
esac
