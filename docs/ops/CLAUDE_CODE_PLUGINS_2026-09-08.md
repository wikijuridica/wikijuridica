# Plugins, hooks e MCP do Claude Code — medição e decisão de 2026-09-08

Ordem do dono: medir marketplaces e plugins (instalados, ativos, inativos, no repo e
globalmente), analisar criticamente, deixar o Claude Code focado e eficiente — menos
contexto, menos latência, sem bloqueios — e corrigir todo defeito de hook, plugin ou MCP
em vez de silenciá-lo. Este documento registra o que foi medido, o que foi decidido por
plugin e como verificar. O plano aprovado está em
`~/.claude/plans/wiggly-splashing-quokka.md`; o backup dos JSON tocados e o log da limpeza
ficam em `.agents/runtime/claude-code-plugins/20260908/`.

## 1. O que estava instalado

| grandeza | valor medido |
|---|---|
| marketplaces conhecidos (`known_marketplaces.json`) | 100, todos com clone `.git`; só `knowledge-work-plugins` com `autoUpdate: true` |
| plugins instalados (`installed_plugins.json`) | 216 (63 de `knowledge-work-plugins`, 39 de `ruflo`) |
| ligados em `~/.claude/settings.json` | 52 (163 desligados) |
| `/opt/wiki/.claude/settings.json` | desligava 71 e ligava 1 (`theme-factory`) |
| efetivos no `/opt/wiki` | 28 |
| hooks registrados (plugins + globais + projeto) | 154 |
| processos por chamada | `Bash` 31, `Edit` 35, `Write` 36, `Read` 15 |
| `Bash true` | 1,45 s (13,97 s na véspera, antes de desligar o `npx` do ruflo) |
| disco em `~/.claude/plugins` | 10,1 GB (cache 6,1 + marketplaces 4,0) |
| lixo de cache | 2.078 diretórios `temp_*` (2,6 GB), 279 versões órfãs, `claude-plugins-official` (456 MB) sem marketplace nem plugin |
| skills / commands / agents expostos no prompt | 442 / 145 / 121 |
| injeção de `SessionStart` + `UserPromptSubmit` por sessão | ~51 KB |
| contexto de abertura desta sessão | 75.387 tokens (`cache_creation_input_tokens` do primeiro turno) |

## 2. Uso real, em 582 transcripts do projeto (42.894 chamadas de ferramenta)

| categoria | chamadas |
|---|---|
| `Skill` de plugin | 9 (`/deep-research` 7, último em 2026-08-12; `superpowers-optimized:context-management` 1; `/security-review` 1) |
| MCP de plugin | `context-mode` 28; `ecc` chrome-devtools, `mem0`, `oh-my-claudecode`, `ruflo`, `u22a8`: 0 |
| `Agent` de plugin | 0 — os 1.000+ agentes usados são do repo (`engenheiro-go` 262, `investigador` 119, `auditor-adversarial` 102, `redator-juridico` 78, `especialista-critico` 76) e builtins |

Dos 28 plugins efetivos, só `context-mode` tinha uso comprovado. Os estilos
(`caveman`, `hush`, `ponytail`, `sloptrim`) agem por hook, não por chamada.

## 3. Bench por hook numa chamada de `Bash` (medido sob carga do Ollama; hooks do mesmo evento rodam em paralelo, então o custo observado ≈ o mais lento)

| hook | ms |
|---|---|
| `context-mode` PostToolUse | 1.261 — ditava o 1,45 s do `true` |
| `ecc` PreToolUse (dispatcher) e mais quatro | 510 / 315 / 296 / 250 |
| `oh-my-claudecode` PostToolUse verifier / project-memory / PreToolUse enforcer | 493 / 429 / 424 |
| `foreman` PostToolUse | 487 |
| `context-mode` PreToolUse | 402 |
| `mem0` | 208 |
| global `snapshot-antes-de-escrever.py` / `audit-log.sh` / `block-heavy-cmds.sh` | 185 / 146 / 141 (em máquina ociosa: 93 / 35 / 8) |
| `hush` (3 hooks) | 142 / 109 / 105 |
| `claim-check` (`Stop`) | 160, sem efeito sem `CLAIM_CHECK_ENFORCE=1` |

## 4. O que bloqueava, injetava ou violava política

- `context-mode` (PreToolUse) negava `WebFetch` e redirecionava para `ctx_fetch_and_index`; injetava nudge em todo Bash/Read/Grep; avisava "security module not found — deny patterns NOT enforced".
- `oh-my-claudecode`: 25 hooks, `PermissionRequest` handler, `pre-tool-enforcer`, 4 hooks em `Stop`, `keyword-detector` que reescrevia `settings.local.json` — e foi ele que gravou `skillOverrides` desligando as 5 skills do repo (`estado-real`, `ler-gigante`, `medir-bots`, `publicar-lote`, `verificar-citacao-legal`).
- `ecc`: 286 skills + 94 commands + 68 agents na listagem do prompt; `config-protection`, `block-no-verify`, `gateguard-fact-force` (já desligado por `ECC_GATEGUARD=off`), 7 hooks em `Stop`.
- `agent-rules`: copiava `AGENTS.md` (179 KB) para `.claude/rules/agents/AGENTS.md` com `paths: ["**/*"]`, e o Claude Code carregava a cópia como `nested_memory` ao tocar qualquer arquivo — provado no transcript `27871ebe…` de 2026-09-08 19:25 (uma injeção de 524 KB). Decisão registrada: o contrato carregado é o `CLAUDE.md`; o `AGENTS.md` é referência por gatilho (§2).
- `superpowers`: 10 KB por sessão mandando invocar `brainstorming` antes de qualquer resposta; 0 invocações. `backlog`: manda oferecer "três opções" ao dono. `ponytail`: "Did X; need full X? Say so". Os três contradizem "Mandou fazer = faz" e "Decidir sem devolver".
- `hush`: o `compress-tool-output.js` omitia linhas das saídas (36, 22, 25, 44 linhas numa auditoria) rotulando "none with warnings/errors/failures" — decidia o que o modelo vê, contra R1.
- `claude-code-handoff`: aviso "Stop hook does not appear to be running" a cada prompt; 23,5 KB por sessão; duplicava memória nativa, `CHECKPOINT.md` e a memória do `context-mode`.
- `planning-with-files`: PreToolUse devolvia rc 127 em todo Write/Edit/Bash/Read/Glob/Grep. `d2`: 4 hooks e binário ausente. `ruflo-core`: MCP falhando em toda sessão ("Skipping connection… retries in 15 min"), 300+ tools, 1,1 GB.
- Política self-hosted do `~/.claude/CLAUDE.md`: `mem0` (api.mem0.ai + posthog), `u22a8` (MCP remoto), `trustycap-production` (mcp.trustycap.com), `claude-seo` (DataForSEO/Moz), `grounding-guard` (registries externos com nomes de pacote do projeto).

## 5. Decisão

Regra: fica o que tem **uso medido** ou é **estilo que o dono escolheu e age por hook**.
O dono decidiu (2026-09-08) manter só `caveman` entre os estilos.

| fica | forma |
|---|---|
| `caveman@caveman` | plugin (único), marketplace `caveman` |
| `context-mode` | **só MCP**, sem plugin e sem hooks: `npm i -g context-mode@1.0.169` + `claude mcp add -s user context-mode -- context-mode`. Tools passam a `mcp__context-mode__ctx_*`. Licença Elastic 2.0 (ferramenta de sessão, não dependência do portal); `ctx_insight` (dashboard hospedado) não se usa |
| `wikijuridica` | MCP do produto, `/opt/wiki/.mcp.json`, inalterado |

Saem os outros 26 plugins efetivos (`ecc`, `oh-my-claudecode`, `ruflo-core`, `superpowers`,
`claude-code-handoff`, `planning-with-files`, `worklog`, `backlog`, `mem0`, `u22a8`,
`trustycap-production`, `super-agents`, `theme-factory`, `claude-seo`, `d2`, `foreman`,
`gh-review-loop`, `grounding-guard`, `watermarks-remover`, `agent-rules`,
`agentic-bundle-llm-application-developer`, `popper-probe`, `claim-check`, `hush`,
`ponytail`, `sloptrim`), os 99 marketplaces restantes (com a cascata de uninstall dos
215 plugins deles) e o cache órfão. Dos 163 já desligados nenhum volta: `context7` é MCP
externo, `tdd-guard` bloqueava Write, `headroom` reescrevia settings, `ringmaster`
bloqueava commit, `claude-hud` só faz statusline.

## 6. Correções feitas nesta sessão

| defeito | correção |
|---|---|
| `skillOverrides` desligando as 5 skills do repo | removido de `settings.local.json` após a cascata (o OMC que o reescrevia deixa de existir) |
| cópia de 179 KB em `.claude/rules/agents/`, `.claude/tdd-guard/` tracked, `.claude/proven-config*` (ruflo), `.handoff_skel.*` | removidos; `tdd-guard` sai do índice |
| `env` órfão (`RINGMASTER_ALLOW_VCS_WRITES`, `RUFLO_HOOK_SKIP_NPX`, `ECC_*`) e `context-mode-cache-heal.mjs` no SessionStart global | removidos dos dois `settings.json` |
| `snapshot-antes-de-escrever.py` a 93 ms em todo Bash (78 ms são o arranque do python) | pré-filtro em bash puro `snapshot-antes-de-escrever.sh`: só delega ao python quando o evento pode escrever (Write/Edit/NotebookEdit, `>`, `open(`, `sed -i`). 4 ms num `true`. Teste: `snapshot-antes-de-escrever-test.py` (11 casos, ponta a ponta com repo git) |
| `audit-log.sh` a 35 ms com nove forks e truncando o comando na primeira aspa escapada | parse em regex de bash sem fork, fallback em python acima de 8 KB, linha vazia não se registra. 8 ms. Teste: `audit-log-test.py` (6 casos) |
| `~/.claude/hooks/*.bak`, `*.disabled` misturados ao runtime | `~/.claude/hooks/attic/` |
| medidor de latência sem régua e fora de qualquer suíte | `check-claude-code-hooks-latency --bench --max-ms 300` reprova hook lento, com rc ≠ 0 ou timeout, nomeando-o; `tools/test_check_claude_code_hooks_latency.py` (5 casos por mutação); linha no `run-qualidade-diaria` |
| `CLAUDE.md` sem dizer como usar o `ctx_*` sem nudge | parágrafo no §4 |

## 7. Verificação na sessão seguinte

```bash
./tools/check-claude-code-hooks-latency --bench --repeticoes 3 --max-ms 300   # OK, plugins habilitados = 1
claude plugin list --json | python3 -c 'import json,sys;print([p["id"] for p in json.load(sys.stdin)])'   # ['caveman@caveman']
ls ~/.claude/plugins/marketplaces | wc -l          # 1
du -sh ~/.claude/plugins                           # <= 1 GB
python3 -c 'import json;print(len(json.load(open("/home/rafael/.claude/settings.json"))["extraKnownMarketplaces"]))'   # 1
claude mcp list                                    # context-mode e wikijuridica conectados, nada "failed"
```

Na sessão nova: dois `Bash true` com delta `tool_use → tool_result` ≤ 0,5 s (era 1,45 s);
`cache_creation_input_tokens` do primeiro turno ≤ 50.000 (era 75.387); boot sem
"Skipping orphaned enabledPlugins entry", sem "failed to connect" e sem
"Contents of /opt/wiki/.claude/rules"; as 5 skills do repo na listagem.

**Acréscimo de 2026-09-23 (goal do IDE, frente 4).** A linha `claude plugin list --json | … print([p["id"] …])` acima deixou de devolver `['caveman@caveman']`: medido às 08:17 -03, ela devolve **95 ids** — `caveman@caveman` de escopo `user`, o mesmo de escopo `project` e **93 de escopo `synced`** (92 habilitados, 1 desabilitado). Os 93 vieram da sincronização de plugins do claude.ai: `stat -c %w ~/.claude/plugins/synced` → 2026-09-22 19:07:19 -03, `du -sh` → 93M, com `syncClaudeAiPlugins` indefinido em `~/.claude/settings.json` (o padrão é ligado). A verificação da sessão seguinte ganha três linhas, medidas pelo `tools/check-claude-code-contexto-fixo` (instrumento da frente 4, escrito pelo agente `claude-tokens`) sobre o transcript da sessão **interativa** mais nova:

1. `AGENTS.md` **fora** do anexo `instructions` do 1º turno — o bloco `pluginConfigs."agents-md@builtin"` (`instructionFiles = claude-md-and-agents-md`) sai de `~/.claude/settings.json` e o padrão `claude-md-or-agents-md` volta a valer;
2. `syncClaudeAiPlugins: false` em `~/.claude/settings.json` e **0** entradas `scope: synced` em `claude plugin list --json | python3 -c 'import json,sys;print(sum(p.get("scope")=="synced" for p in json.load(sys.stdin)))'`;
3. primeiro `permissionMode` = **`auto`** nas 3 sessões interativas seguintes — exige tirar `permissions.defaultMode: "bypassPermissions"` de `.claude/settings.local.json`, que em arquivo local não vale e põe a sessão em Manual.

Plano: `docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8 frente 4 e §9; registro: `docs/ops/IDE_VSCODIUM_20260923.md` §6.

Regra daqui em diante: plugin novo entra com medição de uso em 30 dias ou sai; hook
novo entra com bench abaixo de 300 ms e teste ao lado.
