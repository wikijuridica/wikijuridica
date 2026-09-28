# Orquestração multi-agente nativa — guia para o orquestrador (Fable 5.1, ordem do dono de 2026-09-22)

Este diretório configura o Claude Code como **orquestrador nativo**: **Fable 5.1 orquestra** (main
loop, `"model": "fable"` em `.claude/settings.json`) e **refuta**; **Opus 5.5 executa**; **Sonnet 5
só colhe contexto**; **Haiku é proibido** (hook `block-agent-haiku.sh`). Neste arquivo, "maestro" é
o orquestrador. Substitui parte do encanamento bespoke (tmux + worktree + ledger). Obedece
`AGENTS.md > GOAL.md > CHECKPOINT.md > docs/` (vence a mais restritiva). Ver o plano em
`~/.claude/plans/preciso-que-voc-investigue-generic-aho.md`; o regime de modelos e o método em
ondas estão em `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md` §3–§4 e na DEC-060.

*Superado em 2026-09-22 (ordem do dono): até esta data o texto dizia "Opus 4.8 é o maestro (main
loop); Sonnet 5 e Fable 5 executam como subagentes por papel", com `engenheiro-go` e
`redator-juridico` em Sonnet e `investigador` em Haiku — roster que já contrariava a política de
2026-09-15 ("Sonnet não entra neste projeto") e que nenhum regime anterior chegou a propagar
para cá.*

## Roster (`.claude/agents/`)
| agente | modelo | esforço | edita? | usar para |
|---|---|---|---|---|
| `documentador-de-contexto` | sonnet | medium | só `.agents/runtime/contexto/` e a própria memória (hook) | onda 0: colher contexto e gravar o mapa no disco antes da execução |
| `investigador` | sonnet | medium | não (read-only; hook de escrita) | mapear os pacotes e devolver arquivo:linha, em N cópias paralelas |
| `engenheiro-go` | opus | high | sim | engenharia Go de risco contido: gate no pacote de origem, check novo, render/seo/sitemap, endpoint |
| `redator-juridico` | opus | high | via generate-* | conteúdo PT-BR, anti-template, fonte oficial (proveniência), classificar prosa |
| `auditor-adversarial` | fable | high | não (read-only) | refutação com rubrica, em contexto limpo, antes de integrar/promover |
| `especialista-critico` | fable | max | sim | MUITO crítico: refinedpublicprose/DEC-017, causa-raiz de família, adoção de OSS, throughput 10k |

`internal/contract/misc/alocacao_de_modelos_test.go` reprova quando esta tabela e o frontmatter dos
agentes divergem — foi a distância entre os dois que deixou o roster contrariando a política.

**Como o orquestrador decide criticidade (advisory, não gate):** Fable (`especialista-critico`) quando
toca refinedpublicprose/DEC-017, fronteira P4 (publicrelease.go:3379+)/escrita pública, causa-raiz de
família, adoção de OSS, algo caro de reverter, OAB/paid-intent, ou 3º sintoma. Opus no resto da
execução. Contexto antes (Sonnet: `documentador-de-contexto`, `investigador`), refutação depois
(`auditor-adversarial`). O orquestrador sempre promove/rebaixa. *(Até 2026-09-22: "Sonnet no resto.
Na dúvida: Sonnet constrói"; superado pela mesma ordem.)*

## Regras invioláveis (todos os subagentes)
- **Só o maestro** commita, publica, fecha checkpoint e roda comando pesado full-tree
  (`go build/test ./...`, `lab-cycle`, `cmd/check all`, `--global`). Subagente edita e entrega; o maestro valida e commita.
- Teste **focado** de 1 pacote é permitido ao subagente via `./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./internal/<pkg>/` (a critério do orquestrador por load; agente de contexto não roda teste — o hook de escrita barra).
- Git **só pra frente** (nada de reset/checkout/restore/revert/stash/clean/cherry-pick; ler antigo com `git show HEAD:`).
- **Nunca relaxar gate** (fraude). **DEC-017**: a máquina nunca inventa prosa pública. **3º sintoma** → RCA de família.
- Concorrência **sem teto artificial**, a critério do maestro por load medido (o travamento de 2026-07-08 foi git pesado, já resolvido). `python3` de agente com `nice -n 19`; montagem de arquivo inteiro sob `flock /tmp/opt-wiki-agent-heavy.lock`.

## Enforcement determinístico
- `.claude/hooks/block-heavy-go.sh` (PreToolUse:Bash): bloqueia Go full-tree/pesado **salvo** se
  envelopado em `run-heavy-throttled` (cap GOMAXPROCS + nice + lock = 1 por vez). Testado 24/24.
- `.claude/hooks/block-agent-haiku.sh` (PreToolUse:Agent): barra subagente cujo modelo efetivo é
  Haiku — parâmetro `model`, frontmatter do agente, `CLAUDE_CODE_SUBAGENT_MODEL` e o embutido
  `claude-code-guide` —, e Sonnet em agente que edita: Sonnet só roda nos dois agentes de
  contexto, sob a guarda de escrita, ou em agente com `tools:` só de leitura. Bancada:
  `python3 .claude/hooks/block-agent-haiku.test.py`.
- `.claude/hooks/block-write-fora-de-contexto.sh` (PreToolUse de escrita e Bash): os agentes Sonnet
  do roster só escrevem em `.agents/runtime/contexto/` e na própria memória; o Bash deles é leitura
  por lista de permissão (`lib/guarda_de_escrita.py`). Bancada:
  `python3 .claude/hooks/block-write-fora-de-contexto.test.py`.
- Hooks globais (`~/.claude/hooks/`): `git-guard` (barra reset/checkout/…), `block-heavy-cmds`, guards de Edit/Write.

## Workflows (`scripts/workflows/`)
Rode com `Workflow({scriptPath: "scripts/workflows/<x>.js", args: {...}})`. Agentes do workflow **nunca**
rodam Go/pesado; a execução pesada é do maestro **entre** fases.

### `engenharia-gate.js` — genérico, reutilizável (o principal daqui pra frente)
`args = {gate, evidence_paths[], symptom_ledger[], criticality:"high"|"normal", max_verify_iters}`.
Fases: Investigar (4 ângulos) → RCA (guarda do 3º sintoma; delega ao censo se família) →
Corrigir↔Verificar (loop evaluator-optimizer; fixer Opus/Fable por criticidade — o `model` do fixer
mora no script e, desde 2026-09-22, não pode ser Sonnet nem Haiku) → devolve
`files_changed` + `maestro_checklist` pesado. Use para QUALQUER gate reprovado (ex.: passos 13+:
oráculos PT-BR, dedupe/cluster, source-live, verdict).

### `censo-familia-detectores.js` — para família de detectores falso-positivando prosa autoral
Coreografia (maestro faz o pesado, 1 por vez, via `run-heavy-throttled`):
1. Maestro roda o censo Go (tabela código→count→samples) e `tools/generate-public-prose-blocker-rca --top 25 --samples 3`.
2. Maestro: `./ops/relaunch-censo-detectores.sh` → gera `scripts/workflows/censo-detectores-todo.js` com os dados embutidos
   (lê `public_prose_language_patterns_blocker_rca.jsonl` + `public_prose_candidate.jsonl`; controles opcionais em
   `data/editorial/public_prose_doorway_controls.json`). Se 0 blockers, não gera (nada a censar).
3. `Workflow({scriptPath: "scripts/workflows/censo-detectores-todo.js"})` → plano de calibração em lote + `route_to_content_fix`.
4. Maestro aplica a calibração (especialista-critico no refinedpublicprose; engenheiro-go no resto), `auditor-adversarial` verifica.
5. Maestro (prova de **estado final**): re-roda o censo (FP cai E controles doorway ainda reprovam), `check-refined-public-prose`, commit, `bootstrap-chain --from N`.
> Nota: em 2026-07-09 o passo 12 já foi destravado por outra frente (censo equivalente, commits 25f2f2ae/beafc73d/75a5366f). Este workflow fica pronto para a **próxima** família de detector (passos 13+).

`args.concurrency` (opcional) janela a fan-out se o load pedir; padrão = cap do runtime.
