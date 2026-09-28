# Desenho da reescrita do modo operacional do Claude Code em `/opt/wiki`

**Ordem do dono, 2026-09-15:** *"Revise as regras e deixa elas mais operacionais e modo
engenharia padrão Anthropic… com engenharia de qualidade e com obediência às regras,
evitando retrabalho, gasto de tokens errado e melhorando eficiência… Vamos mudar o modo
operacional do Claude Code neste repo, com caminhos corretos, engenharia correta e nada
solto e nada hardcoded."*

Auditoria feita em 2026-09-15, modo somente leitura. Nada foi editado, commitado nem
publicado. Este documento é o DESENHO; a execução é a frente seguinte.

**Método de estimativa de tokens.** Não há tokenizador da Anthropic disponível localmente e
chamar `count_tokens` exigiria credencial de API — o contrato de self-hosted-first proíbe.
Toda estimativa aqui é **caracteres ÷ 3,5**, razão típica de PT-BR acentuado, e vem
acompanhada de um intervalo **÷ 4,0 (piso) a ÷ 3,0 (teto)** para que nenhuma decisão dependa
do ponto central. Os *caracteres* são contados por `len()` de Python sobre o arquivo decodificado
em UTF-8 (não bytes: acento em UTF-8 gasta 2 bytes e 1 caractere, e usar bytes infla a conta
em ~3%). Onde não medi, está escrito **não medido**.

---

## 0. O diagnóstico que decide todo o desenho

O dono listou cinco erros repetidos nesta sessão. A pergunta que importa não é "a regra
existia?" — é **onde a regra estava quando o erro aconteceu**:

| Erro do dono | Onde a regra vivia | Estava em contexto? |
|---|---|---|
| Reabri o DataJud que ele manda destravar "sempre" | `CLAUDE.md:72-92` (§2) — diz "é livre para usar, consultar, armazenar, indexar e servir" e desmonta a cláusula 3.8 pelo nome | **SIM** |
| Inventei risco da OAB para travar conteúdo informativo | `CLAUDE.md` §8 (Provimento 205/2021, o que é e o que não é vedado) | **SIM** |
| Devolvi decisão ao dono três vezes | `~/.claude/CLAUDE.md`, "Decidir sem devolver" | **SIM** |
| Medi tráfego na camada errada | `docs/MEDICAO_DE_AUDIENCIA.md` + skill `medir-bots` | **NÃO** (doc não carregado; skill com gatilho de tema) |
| Desenhei "revisão humana" como etapa de esteira | só `~/.claude/projects/-opt-wiki/memory/dono-nao-revisa-paginas.md` | **NÃO** (só o título de uma linha entra no contexto; o corpo não) |

**Três dos cinco erros aconteceram com a regra em contexto.** Isso mata a hipótese mais
intuitiva — "a regra está escondida, vamos deixá-la mais visível". Para esses três, mais
visibilidade não resolve: eles já eram visíveis. O que falhou foi **densidade**.

O defeito, nomeado: **22.358 tokens de prosa fixa por sessão, em que a imposição afogou no
argumento.** O `CLAUDE.md` de hoje é excelente como memória de engenharia (cada regra tem o
caso, a data e o prejuízo) e ruim como norma no momento do ato. Pior: no caso do DataJud a
prosa é **contra-produtiva**. As linhas 72-92 argumentam — citam a cláusula, a ressalva que
ela não contém, o hash do documento oficial, o que JusBrasil faz. Um modelo que lê vinte
linhas de "há quem diga X, mas na verdade Y" **reconstrói a dúvida que o texto queria
fechar**. Argumento convida a re-litigar; veredito encerra.

Daí a consequência de desenho que não estava no enunciado da missão: além de
hook / skill / doc, existe um **quarto destino** para um bloco de regra —

> **VEREDITO ADOTADO**: uma linha imperativa com data, autoridade e caminho. Sem o porquê.
> O porquê fica no parecer, para quem quiser auditar.

O DataJud deixa de ser 20 linhas e passa a ser uma:

```
DataJud/CNJ, DJEN, LexML, normas.leg.br, Planalto, diários, transparência: LIBERADO.
Parecer adotado pelo titular em 2026-09-05 — docs/data-sources/PARECER_DATAJUD_3_3_3_8.md.
Limite: 120 req/min e nivelSigilo > 0. NÃO REABRA a discussão de licitude.
```

Isso é a diferença entre um contrato que ensina e um contrato que manda. O repo precisa
dos dois, em arquivos diferentes, com custos diferentes.

---

## 1. Inventário medido

### 1.1 Custo fixo por sessão (entra em TODA sessão, sempre)

| arquivo | bytes | caracteres | linhas | tok ÷4,0 | **tok ÷3,5** | tok ÷3,0 |
|---|---|---|---|---|---|---|
| `/opt/wiki/CLAUDE.md` | 43.142 | 41.868 | 645 | 10.467 | **11.962** | 13.956 |
| `/home/rafael/.claude/CLAUDE.md` | 13.584 | 13.176 | 270 | 3.294 | **3.765** | 4.392 |
| `…/projects/-opt-wiki/memory/MEMORY.md` (índice) | 23.970 | 23.209 | 167 | 5.802 | **6.631** | 7.736 |
| **soma do custo fixo** | **80.696** | **78.253** | **1.082** | **19.563** | **22.358** | **26.084** |

Mais o *tier* que **não** entra: 166 arquivos de memória linkados, 351.793 bytes ≈ **100.512
tok** de conteúdo que existe no disco e do qual a sessão recebe apenas o título de uma linha.
É aí que morava a regra "o dono não revisa páginas".

### 1.2 O `CLAUDE.md` do repo, seção por seção (medido)

| seção | linhas | caracteres | tok ÷3,5 | % do arquivo |
|---|---|---|---|---|
| cabeçalho | 1-14 | 508 | 145 | 1,2% |
| §1 As dezesseis armadilhas caras | 15-50 | 5.309 | 1.517 | 12,7% |
| §2 Leitura obrigatória, por gatilho | 51-118 | 4.475 | 1.279 | 10,7% |
| §3 O que é o projeto, e o que está medido | 119-185 | 3.624 | 1.035 | 8,7% |
| §4 Comandos | 186-233 | 2.464 | 704 | 5,9% |
| §5 A regra de ouro da publicação | 234-273 | 2.213 | 632 | 5,3% |
| §6 Contrato de indexação (HTML leve) | 274-371 | 6.182 | 1.766 | **14,8%** |
| §7 O canal de máquina | 372-408 | 2.085 | 596 | 5,0% |
| §8 Conteúdo, fonte e ética | 409-469 | 3.447 | 985 | 8,2% |
| §9 Redes sociais | 470-493 | 1.065 | 304 | 2,5% |
| §10 Governança entre pares | 494-518 | 1.240 | 354 | 3,0% |
| §11 Escala, autonomia e coordenação | 519-583 | 3.818 | 1.091 | 9,1% |
| §12 AI-first, B2A e a IA local | 584-646 | 5.426 | 1.550 | 13,0% |

### 1.3 `.claude/` do repositório

`git ls-files .claude/` rastreia **15 arquivos**: `WORKFLOWS.md`, 5 agents, 3 hooks,
`settings.json`, 5 skills. O resto do diretório (125 arquivos no disco) é ruído local
corretamente ignorado (`.gitignore:661` cobre `handoff_backups/`, 656.006 bytes em 4
arquivos — lixo em disco, **não** lixo versionado).

**Skills — 5, somando 23.926 bytes.** Todas com gatilho por ATO, não por tema:

| skill | bytes | gatilho declarado | veredito |
|---|---|---|---|
| `estado-real` | 3.843 | "antes de confiar em qualquer número que a documentação afirme" | ATO ✓ |
| `ler-gigante` | 3.113 | "quando precisar consultar um arquivo grande" | ATO ✓ |
| `medir-bots` | 7.198 | "quando a pergunta for quanto um crawler rastreou" | ATO ✓ |
| `publicar-lote` | 4.796 | "quando for promover páginas do acervo v2 para o ar" | ATO ✓ |
| `verificar-citacao-legal` | 4.976 | "ao escrever ou auditar página que cite lei, artigo, súmula" | ATO ✓ |

As cinco estão bem desenhadas. **Não há duplicação de prosa com o `CLAUDE.md`** (verificado
por busca de frases-chave; não confronto linha a linha das 23.926 vs 41.868 — *amostra, não
população*). A lacuna não é qualidade, é **cobertura**: nenhuma skill cobre deploy, purga de
borda, cadeia editorial, coordenação entre sessões nem rede social — que são exatamente os
procedimentos que hoje pagam custo fixo em prosa do `CLAUDE.md`.

**Agents — 5, somando 13.474 bytes.** `auditor-adversarial` (fable/high, read-only),
`especialista-critico` (fable/max, edita), `engenheiro-go` (sonnet/high),
`redator-juridico` (sonnet/medium), `investigador` (haiku/low). Os agentes
`revisor-critico` e `refatorador` **não existem** neste repo — são definições de outro
nível. Sobreposição real: **2** de revisão adversarial, separados por fronteira explícita
(read-only vs. edita). Não há desperdício aqui; nada a consolidar.

**Commands — `/opt/wiki/.claude/commands/` NÃO EXISTE.** Nem `~/.claude/commands/`. Zero
slash commands nos dois níveis. **Todo procedimento deste repositório mora em prosa de custo
fixo**, e essa é a maior causa única de desperdício que esta auditoria encontrou.

**Hooks do repo — 3:**

| hook | evento | bloqueia? |
|---|---|---|
| `.claude/hooks/block-heavy-go.sh` (8.850 B) | `PreToolUse`/`Bash` | **sim**, exit 2 |
| `tools/hook-warn-tmp-product-write` (104 linhas Python) | `PreToolUse`/`Write\|Edit\|MultiEdit\|NotebookEdit` | não — só `additionalContext` + `systemMessage`, sempre exit 0 (decisão do dono 2026-08-04: bloquear inviabilizaria plan mode) |
| `tools/generate-tmp-product-rescue` (216 linhas Python) | `Stop`, `async` | n/a — copia `/tmp` para `.agents/runtime/tmp_rescue/<AAAAMMDD>/` |

`block-heavy-go.sh` é o **modelo de referência** para todo hook novo deste desenho, e vale
transcrever por que: as regex são construídas em variáveis (para que editar o próprio hook
não o dispare), estão ancoradas em **posição de comando** (`"command":\s*"`, separador de
shell, quebra de linha) e não em qualquer menção — então `git commit -m "cita ./tools/lab-cycle"`
passa; corpo de heredoc *quoted* é removido antes da análise, mas heredoc que alimenta
interpretador é analisado; `run-heavy-throttled` é exceção explícita; `trap 'exit 0' ERR`
faz *fail-open*. A bancada `block-heavy-go.test.py` tem **22 casos**, dos quais **12 são de
falso-positivo** — e o arquivo declara a lacuna que sabe ter em vez de maquiá-la
(comando pesado dentro de `os.system(...)` de outra linguagem não é detectado, por desenho).
E a mensagem de erro **ensina**: nomeia o motivo, cita o incidente (servidor de 8 núcleos
travado em 2026-07-08), dá o comando exato envelopado e orienta o subagente.

### 1.4 Hooks globais: 28 arquivos, 19 ligados, **5 órfãos**

| ligado no `~/.claude/settings.json` | evento |
|---|---|
| `block-sleep.sh`, `git-guard.sh`, `block-heavy-cmds.sh`, `merge-conflict-check.sh`, `protect-bot-ratelimit.sh`, `snapshot-antes-de-escrever.sh` | `PreToolUse`/`Bash` |
| `protect-files.sh`, `block-masking.sh`, `block-empty-catch.sh` | `PreToolUse`/`Edit\|Write` |
| `auto-approve-read.sh` | `PreToolUse`/`WebFetch\|WebSearch` |
| `audit-log.sh` (async) | `PostToolUse`/`Bash` |
| `commit-reminder.sh` (async), `validate-hook-edit.sh` | `PostToolUse`/`Edit\|Write` |
| `compact-context.sh`, `session-git-check.sh` | `SessionStart` |
| `notify.sh` | `Stop`, `Notification` (async) |

**Órfãos — no disco, fora do `settings.json`: 4.** `keep-working.sh`,
`sequential-agents.sh`, `agent-cleanup.sh`, `context-mode-cache-heal.mjs`.
**`git-guard-prune.py` NÃO é órfão**: é chamado por `git-guard.sh`, que está ligado
(`grep -l 'git-guard-prune' ~/.claude/hooks/*.sh` → `git-guard.sh`). A distinção importa
porque a asserção (b) de `tools/check-modo-operacional` reprovaria um **auxiliar** como se
fosse hook morto — falso positivo que a bancada dele tem de cobrir desde o primeiro dia.

Dois desses órfãos são achados, não sujeira:

- **`sequential-agents.sh` é o padrão correto de desativação**: o cabeçalho diz a data
  (2026-07-28), a causa medida (o PID gravado era o do próprio hook, que morre em seguida;
  subagente do Claude Code roda *in-process* e nunca foi processo separado, então contar por
  PID nunca poderia funcionar), o custo que cobrava (~11 ms + flock + varredura por
  lançamento) e onde está a informação correta. **É assim que se aposenta um mecanismo neste
  repo** — não se apaga, se data e se explica.
- **`keep-working.sh` é o protótipo do mecanismo que falta.** É um hook `Stop` que devolve
  `{"decision":"block","reason":"…"}` — ou seja, **impede o turno de terminar e devolve ao
  modelo o texto que ensina o que fazer em vez de parar**. Tem *circuit-breaker*
  (`MAXBLK=25` em janela de 180 s) para não virar laço infinito. É exatamente a mecânica que
  o erro #3 do dono ("devolvi decisão três vezes") precisa. Está desligado e **sem nota
  dizendo por quê** — ao contrário do `sequential-agents.sh`. Provável motivo: ele bloqueia
  *toda* parada, o que é forte demais. O desenho abaixo reaproveita a mecânica com escopo
  estreito (bloquear só a parada que devolve decisão), em vez de escrever de novo.

### 1.5 Custo dos hooks: medido, e a memória está desatualizada

A memória `custo-dos-hooks-claude-code.md` registra `Bash true` a **13,97 s** com 48 plugins
/ 271 hooks / 55 processos por chamada, depois **1,45 s** com 28 plugins / 154 hooks, com
alvo de 0,3 s. **Esse estado não existe mais.** Medido hoje com
`./tools/check-claude-code-hooks-latency --bench --max-ms 300` (exit **0**):

```
hooks por fonte: global 19 · projeto/settings.json 3 · caveman 2   (total 24)
processos por chamada: Bash Pre=7 Post=1 → 8 · Edit/Write Pre=6 Post=2 → 8 · Read/Grep/Task → 0
hook mais lento (Bash, mediana de 3): merge-conflict-check 16,6 ms
soma PreToolUse 0,10 s · soma PostToolUse 0,02 s
OK: todos os 8 hooks de Bash dentro de 300 ms e rc=0
```

Confirmei o modelo de custo por medição própria, 7 hooks de `Bash` com payload sintético:
**serial 75,3 ms · paralelo 36,4 ms** — o paralelo bate com o hook mais lento mais o
*overhead* de fork, não com a soma. Com payload **real** (o que o advisor exigiu, porque
`echo ok` é caminho rápido): `git commit -F …` → `git-guard` 10 ms (num arquivo de 36 KB);
`./tools/go-modern build ./internal/... ./cmd/...` → `block-heavy-go` 12 ms,
`block-heavy-cmds` 12 ms. No evento `Edit` sobre `AGENTS.md` (180 KB, para forçar a cópia do
snapshot): `snapshot-antes-de-escrever` 77 ms, `hook-warn-tmp-product-write` 69 ms,
`protect-files` 13 ms, `block-masking` 9 ms, `block-empty-catch` 14 ms.

**Conclusões operacionais.** (a) Há **orçamento de sobra** para os hooks novos deste desenho:
o pior evento hoje custa ~77 ms contra régua de 300 ms. (b) O caro não é o hook, é o
**`SessionStart`**, que injeta contexto para sempre — a mesma medição histórica atribuiu
**27.463 tokens** de abertura ao texto que 27 hooks de `SessionStart` injetavam. Nenhum hook
deste desenho usa `SessionStart` para injetar prosa. (c) Régua a herdar:
`tools/check-claude-code-hooks-latency --bench --max-ms 300`, que já existe e já passa —
todo hook novo entra com essa medição no commit.

### 1.6 Testes de contrato: o que trava trecho literal de qual documento

`internal/contract/` tem **194 arquivos `_test.go`, 2.869.816 bytes**.

| documento | teste | o que exige |
|---|---|---|
| `CLAUDE.md` §10 | `internal/contract/misc/peer_governance_test.go:14` `TestLiveAgentGovernanceTreatsClaudeAndCodexAsPeerLeads` | "Governança entre pares", "Claude Code e Codex/GPT-5.6 são engenheiros-chefes autônomos", "sem presunção de superioridade ou inferioridade entre modelos"; **proíbe** regex de hierarquia |
| `AGENTS.md` | idem | "Governança multi-agente entre pares", "Nenhum modelo ou agente é tratado como inferior, superior ou coadjuvante por identidade" |
| `docs/goal/MAESTRO_CODEX_LOG.md` | idem | "Log de revisão entre pares" + 2 frases |
| `docs/goal/DECISIONS.md` | idem | "DEC-019 — Governança de Claude Code e Codex é entre pares" + 2 frases |
| `AGENTS.md`, `GOAL.md`, `docs/P0_OPERATIONAL_RUNBOOK.md`, `.agents/contracts/p0-work-reuse-command-ledger.md` | `internal/engineeringnowcontract/contract.go` (gate `engineering-now-contract`, testado em `contract_test.go`) | ~26 cláusulas obrigatórias + lista de proibidas, casadas por whitespace normalizado (`foldContractWhitespace`) — **não** byte-exato |
| `AGENTS.md`, `GOAL.md`, `docs/DECISIONS.md`, `docs/P0_OPERATIONAL_RUNBOOK.md` | `internal/contract/misc/continuity_test.go` (152.866 B) | frases de continuidade/ordem do dono |
| `tools/start-ai-terminal` + 3 docs | `internal/contract/misc/ai_terminal_launcher_test.go` | 14 fragmentos de script + regex de `tmux set-environment` |
| `content/site.json` | `internal/contract/misc/site_url_flexibility_test.go:15` | `BaseURL=="https://wikijuridica.com.br"`, `BaseURLMode=="official_configured"`, `OfficialURLStatus=="locked"` |
| HTML renderizado | `internal/render/author_credential_test.go:26` | byline + rodapé + JSON-LD, **exatamente 2** ocorrências visíveis de `OAB/RJ 227191` |

**A lacuna é grande e é o ponto de partida da seção 9:** de todo o `CLAUDE.md`, **só o §10
tem teste**. §1 a §9, §11 e §12 — as armadilhas, os vereditos, o contrato de indexação, a
ética, o mandato AI-first — **não são cobrados por nada**. Uma condensação distraída apaga
qualquer um deles em silêncio. O precedente existe e está citado no próprio §10: a
condensação `64832bdd` apagou o parágrafo de governança e deixou o teste vermelho (BUG-171)
— o teste é o único motivo de sabermos. Também sem teste localizado:
`docs/PRECEDENTES_DAS_ORDENS.md`, `docs/ARQUITETURA_FIEL.md`, `docs/CONTRATO_DADO_REAL.md`,
`docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`, `docs/MEDICAO_DE_AUDIENCIA.md`, `CHECKPOINT.md`.

### 1.7 Os outros contratos, e o custo de obedecer o §2 à letra

| documento | bytes | tok ÷3,5 |
|---|---|---|
| `CHECKPOINT.md` | 2.470.023 | **693.836** |
| `AGENTS.md` | 180.212 | 50.061 |
| `GOAL.md` | 152.782 | 42.488 |
| `AI-first-wikijuridica.bot` | 95.227 | 26.595 |
| `docs/DECISIONS.md` | 406.848 | 116.242 |

A tabela "Leitura obrigatória, por gatilho" (§2) amarra 7 documentos a 7 temas. Todos os 7
existem. Obedecê-la literalmente numa sessão custa:

| documento | bytes | tok ÷3,5 |
|---|---|---|
| `docs/OPERACAO_COMANDOS_E_CAMINHOS.md` — gatilho *"antes de rodar qualquer comando"* | 53.240 | 15.211 |
| `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` | 68.646 | 19.613 |
| `docs/ARQUITETURA_FIEL.md` | 35.779 | 10.223 |
| `docs/MEDICAO_DE_AUDIENCIA.md` | 32.437 | 9.268 |
| `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` | 19.662 | 5.618 |
| `docs/CONTRATO_DADO_REAL.md` | 10.226 | 2.922 |
| `docs/PUBLICACAO_EM_REDES_SOCIAIS.md` | 7.435 | 2.124 |
| **soma** | **227.425** | **64.979** |

**Nenhuma sessão paga isso, e é por isso que a tabela não funciona.** Uma instrução cujo
cumprimento custa 65 mil tokens — 15.211 deles antes do *primeiro comando* — não é obedecida:
é ignorada. E uma instrução que todas as sessões ignoram ensina que instruções são
ignoráveis, o que contamina as que importam. A tabela é um **custo fixo de 1.279 tokens que
compra zero obediência**.

### 1.8 `context-mode`: prosa sem mecanismo

- `.mcp.json` do repo declara **um** servidor: `wikijuridica` (HTTP `127.0.0.1:8088/mcp`).
  `context-mode` é MCP de **usuário**, fora do repo, conforme
  `docs/ops/CLAUDE_CODE_PLUGINS_2026-09-08.md:74`.
- Esse doc decide: dos 28 plugins medidos, só `context-mode` tinha uso comprovado; o resto
  saiu. E o plugin de `context-mode` **também** saiu, ficando **só o MCP puro, sem hooks** —
  porque o plugin custava 1.261 chamadas de `PostToolUse` (era ele que ditava o 1,45 s do
  `true`) e injetava *nudge* automático em todo `Bash`/`Read`/`Grep`.
- **Consequência medida: hoje não existe nenhum mecanismo empurrando para `ctx_execute`.**
  O §4 do `CLAUDE.md` é prosa pura, e a última linha dele admite: *"Nada nudge
  automaticamente — a escolha é sua a cada chamada."*

Isso é um caso de **decisão correta com registro incompleto**. O *nudge* automático foi
retirado por custo real e medido, e não deve voltar. Mas a orientação em prosa que sobrou
custa tokens em toda sessão e não muda comportamento. A saída está na §5 deste desenho: o
`ctx_execute` é **procedimento**, não imposição — vai para skill/command com receita, e a
prosa fixa cai para uma linha.

---

## 2. Classificação de cada bloco do `CLAUDE.md`

Cinco destinos. `VEREDITO` é o destino novo, justificado pela §0.

| bloco | tok hoje | classe | destino |
|---|---|---|---|
| cabeçalho + precedência | 145 | **FATO** | fica (encolhido) |
| §1, 16 linhas de armadilha | 1.517 | **IMPOSIÇÃO** (11 linhas) + **PROCEDIMENTO** (5) | hooks H1-H4, H7-H8; procedimentos → skills; fica um índice de 10 linhas apontando o mecanismo |
| §2 tabela de leitura por gatilho | ~300 | **IMPOSIÇÃO** | `.claude/rules/*.md` com `paths:` (injeta as 3 linhas certas no ato); a tabela sai |
| §2 publicidade/sigilo, API pública, DataJud | ~980 | **VEREDITO** | 4 linhas imperativas + `docs/data-sources/PARECER_DATAJUD_3_3_3_8.md`; hook H6 reinjeta no ato |
| §3 o que o projeto é + topologia | 1.035 | **FATO** | fica (é o único bloco que justifica custo fixo sem ressalva) |
| §3 "Estado atual (medido em …): 11.039 páginas" | ~150 | **OBSOLETO** | sai. Número vive em `data/`, skill `estado-real` mede |
| §4 Go pelo wrapper, nunca full-tree, nunca `check` sem argumento | ~250 | **IMPOSIÇÃO** | já é hook (`block-heavy-go`) + hook novo H1; fica 1 linha de fato |
| §4 validação proporcional ao risco, 3 passos | ~250 | **PROCEDIMENTO** | skill `validar-proporcional` |
| §4 `context-mode` / saída grande | ~200 | **SAÍDA GRANDE** | skill `saida-grande`; fica 1 linha |
| §5 cadeia de publicação + severidade (11 motivos, 3 médios) | 632 | **IMPOSIÇÃO** (o gate) + **OBSOLETO** (as listas) | listas saem — vivem em `tools/generate-v2-publication-severity`; ficam 3 linhas: regra de ouro, PUBLICAR E CORRIGIR, anti-fraude não se flexibiliza |
| §6 invariantes de HTML/CSS/CSP/analytics | ~900 | **FATO** | fica condensado a 8 bullets — é o bloco cuja violação derruba o portal inteiro |
| §6 explicação do porquê de cada invariante | ~450 | **PROCEDIMENTO/DOC** | `docs/SEO_CRAWL_INDEXING.md`, injetado por `.claude/rules/render-e-html.md` |
| §6 matriz "mudei X, então faço Y" | ~420 | **PROCEDIMENTO** | slash command `/deploy-decidir` |
| §7 topologia do canal de máquina | ~400 | **FATO** | fica |
| §7 passo 2.6, regeneração de co-citação | ~200 | **PROCEDIMENTO** | skill `cadeia-editorial` |
| §8 ética OAB, autoria, PT-BR, anti-template | ~700 | **IMPOSIÇÃO** + **FATO** | ética → gate + hook H7; autoria é FATO, fica; limiar 0,70 vira constante única |
| §8 fonte oficial, DEC-032, duas camadas | ~285 | **VEREDITO** | 2 linhas + `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` |
| §9 redes sociais | 304 | **PROCEDIMENTO** | skill `publicar-social`. `:99` nunca `:0` **já é `hard_deny`** no `autoMode` |
| §10 governança entre pares | 354 | **FATO travado por teste** | fica **verbatim** — `peer_governance_test.go` |
| §11 escala, coordenação, sondagem, WikijuridicaBot | 1.091 | **IMPOSIÇÃO** + **PROCEDIMENTO** | UA já é função + teste; coordenação → `/coord`; fica 3 linhas |
| §12 mandato AI-first + linguagem por camada | ~600 | **FATO/VEREDITO** | fica condensado |
| §12 números do Ollama (MemoryMax, tok/s, RSS, pesos) | ~950 | **OBSOLETO por construção** | sai. A fonte é `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`, que já carrega tudo com data |

---

## 3. A estrutura nova do `CLAUDE.md`

Princípio: **o `CLAUDE.md` contém apenas o que o modelo não consegue descobrir sozinho e não
pode ser imposto por máquina.** Tudo que uma máquina pode impedir, ela impede. Tudo que só
importa em certos momentos, chega nesses momentos.

```
CLAUDE.md — contrato do /opt/wiki                      alvo ≤ 4.500 tok (hoje 11.962)

§0  COMO ESTE CONTRATO FUNCIONA                                          ~120 tok
    As imposições estão em hooks e gates — se você errar, a máquina barra e
    ensina o caminho. Os procedimentos estão em skills e slash commands —
    invoque, não decore. Os números NÃO estão aqui: skill `estado-real`.
    Precedência: AGENTS.md → GOAL.md → CHECKPOINT.md → docs/. Vence a mais
    restritiva.

§1  VEREDITOS ADOTADOS — NÃO REABRA                                      ~320 tok
    Uma linha cada, com data, autoridade e caminho do parecer. Sem argumento.
    (a) API pública e dado processual: LIBERADO — 2026-09-05.
    (b) Publicidade é a regra, sigilo é a exceção — 2026-08-29.
    (c) Conteúdo informativo não tem risco de OAB — o vedado é promessa de
        resultado, captação e preço como chamariz.
    (d) O dono NÃO revisa páginas; "auditoria humana" é veredito de agente.
    (e) Analytics é permitido; desativar a medição é proibido — 2026-08-27.
    (f) Autoria é do advogado; nada publicado menciona ferramenta — 2026-09-09.
    (g) A IA local publica pela cadeia (DEC-059) — 2026-09-09.
    Reabrir um veredito é retrabalho que o dono paga. H6 reinjeta no ato.

§2  O QUE É O PROJETO (FATO)                                             ~900 tok
    Portal jurídico, sem framework/CMS/SaaS. Meta P0 = 10.000 páginas.
    Topologia (o diagrama), o acervo não passa pelo Go, o nginx tem cache de
    origem, a frota do túnel é 5. Módulos. Estoque canônico é o v2.
    NENHUM NÚMERO DE ESTADO. Ponteiro: skill `estado-real`.

§3  OS INVARIANTES QUE DERRUBAM O PORTAL (FATO)                          ~450 tok
    8 bullets: ≤50 KB e HTML completo no 1º response · UMA folha externa e a
    CSP dela sai do nginx, não do Go · `style-src` sem 'self' · UM script só
    (`pageinline.Script`), CSP por hash, sem 'unsafe-inline'/'self' ·
    `target="_blank"` + aviso WCAG nos alvos instrumentados · wildcard do
    Clarity é obrigatório · utm_* mantém canonical e NÃO leva noindex ·
    o CSS inline das páginas de erro é de propósito.
    Cada bullet nomeia o gate que o cobra. Explicação: docs/SEO_CRAWL_INDEXING.md.

§4  O CANAL DE MÁQUINA (FATO)                                            ~400 tok
    Gêmea Markdown é rota dinâmica; 4 canais renderizam o MESMO objeto;
    H3 é do FAQ e é contrato; anti-404 em duas camadas.

§5  AI-FIRST E A IA LOCAL (MANDATO)                                      ~400 tok
    O produto é contexto jurídico para IA; HTML é uma serialização.
    Mesmo conteúdo para bot e humano, sempre — serialização muda por URL e
    por Accept, nunca por User-Agent.
    Linguagem por camada: o que serve HTML é Go (DEC-036).
    Ao sair para a rede: `wikijuridicabot.Aplica(req, proposito)`.
    Parâmetros da IA local: ops/ollama/ollama.service.d/wikijuridica-tuning.conf.

§6  GOVERNANÇA ENTRE PARES (VERBATIM — TRAVADO POR TESTE)                 354 tok
    Texto de hoje, sem uma palavra alterada.
    internal/contract/misc/peer_governance_test.go

§7  ONDE ESTÁ O RESTO                                                    ~350 tok
    Índice de mecanismo, não de assunto. Três colunas:
    vou fazer X → invoque Y → a máquina barra Z.
    ~18 linhas cobrindo publicar, deploy, purgar, medir bot, citar lei,
    cadeia editorial, rede social, coordenar, ler arquivo gigante,
    saída grande, validar, commitar.
                                                              TOTAL ~3.294 tok
```

**Duas notas de forma que a documentação liberou.** (a) Comentário HTML de bloco
(`<!-- revisado em 2026-09-15; o porquê deste bloco está em docs/... -->`) é **removido antes
de entrar no contexto** — então a nota de manutenção para humano é **de graça**, e o contrato
novo a usa em cada seção para registrar data de revisão e onde foi parar o que saiu. (b)
**Nenhum `@caminho` de import**: a doc é explícita — *"doesn't reduce context, since imported
files load at launch"*. Import organiza e não economiza; quem economiza é regra por caminho,
`CLAUDE.md` de subdiretório e skill.

`~/.claude/CLAUDE.md` (3.765 → alvo ~3.000): sai a tabela "Terminal de agentes" (procedimento
→ `/terminal`), sai a tabela "Guardas automáticas" (cada hook se anuncia quando dispara;
listar todos custa sempre e informa nunca), e resolve-se a **duplicação medida** com o repo —
"`git add` separado do `git commit`" está nos dois arquivos (`CLAUDE.md` §1 linha de commit +
`~/.claude/CLAUDE.md` seção "Git e commits") e é regra de máquina: fica só no de máquina.

---

## 4. Tabela de migração: bloco atual → mecanismo novo

| # | bloco atual | mecanismo novo | arquivo a criar |
|---|---|---|---|
| 1 | §1 "`cmd/check` sem argumento roda TODOS" | **hook H1** | `.claude/hooks/guard-check-sem-argumento.sh` + `.test.py` |
| 2 | §1 "`sudo nginx -t` devolve `var/nginx/` a `nobody`" | **hook H2** | `.claude/hooks/guard-sudo-nginx-t.sh` |
| 3 | §1 "purgar a borda sem conferir o ledger" / "purgar antes de invalidar origem" | **hook H3** | `.claude/hooks/guard-ordem-de-deploy.sh` |
| 4 | §1 "regenerar derivado de `data/editorial/` fora de ordem" | **hook H4** | `.claude/hooks/guard-ordem-cadeia-editorial.sh` |
| 5 | §1 "mudar `content/social_policy.json` sem o binário" | **hook H5** | `.claude/hooks/guard-social-policy.sh` |
| 6 | §2 DataJud / publicidade / risco de OAB | **hook H6** (UserPromptSubmit) + §1 do novo contrato | `.claude/hooks/injeta-vereditos.sh` |
| 7 | §8 ética OAB, promessa de resultado | **hook H7** + gate existente | `.claude/hooks/guard-promessa-de-resultado.sh` |
| 8 | §1 "rodar gate e achar que acabou" / bancada do pacote | **hook H8** (PostToolUse) | `.claude/hooks/lembra-bancada-do-pacote.sh` |
| 9 | §2 tabela "Leitura obrigatória, por gatilho" | **`.claude/rules/*.md` com `paths:`** (nativo, custo fixo zero) — **não** hook | `.claude/rules/dado-editorial.md`, `borda-e-csp.md`, `grafo-do-validador.md`, `medicao-de-audiencia.md`, `politica-social.md`, `render-e-html.md` |
| 10 | erro #4 — medir tráfego na camada errada | **hook H10** | `.claude/hooks/guard-camada-de-medicao.sh` |
| 11 | erro #3 — devolver decisão ao dono | **hook H11** (Stop, mecânica de `keep-working.sh`) | `.claude/hooks/guard-devolve-decisao.sh` |
| 12 | erro #5 — "revisão humana" como etapa | **hook H12** + renome do rótulo no dado | `.claude/hooks/guard-revisao-humana.sh` |
| 13 | §1 "subir binário Go novo" (socket/notify/ordem) | **skill** | `.claude/skills/deploy/SKILL.md` |
| 14 | §6 matriz "mudei X, então faço Y" + purga/aquecimento | **mesma skill do item 13** (invocável como `/deploy`) | `.claude/skills/deploy/SKILL.md` |
| 15 | §1 "commitar página v2" + pareamento de portfólio | **skill** (`/commit-v2`) | `.claude/skills/commit-v2/SKILL.md` |
| 16 | §1 "tocar `internal/v2ingest`…" + atestação | **skill** + regra por caminho (item 9) | `.claude/skills/atestar-grafo/SKILL.md` |
| 17 | §1 "regenerar derivado de `data/editorial/`" (o como) | **skill** | `.claude/skills/cadeia-editorial/SKILL.md` |
| 18 | §4 validação proporcional ao risco | **skill** | `.claude/skills/validar-proporcional/SKILL.md` |
| 19 | §4 `context-mode` / saída grande | **skill** | `.claude/skills/saida-grande/SKILL.md` |
| 20 | §9 redes sociais (todo o bloco) | **skill** | `.claude/skills/publicar-social/SKILL.md` |
| 21 | §11 coordenação entre sessões | **skill** (`/coord`) | `.claude/skills/coord/SKILL.md` |
| 23 | `~/.claude/CLAUDE.md` tabela "Terminal de agentes" | **skill de usuário** (`/terminal`) | `~/.claude/skills/terminal/SKILL.md` |
| 24 | §3 / §5 / §6 / §12 — todo número de estado | **skill existente** `estado-real`, ampliada | — |
| 25 | §12 números do Ollama | **fonte única no disco** | nenhum — o `.conf` já é a fonte |
| 26 | §5 listas de severidade | **fonte única no código** | nenhum — `tools/generate-v2-publication-severity` |

**Onde os hooks NOVOS devem morar:** todos em `/opt/wiki/.claude/hooks/`, registrados no
`/opt/wiki/.claude/settings.json` (versionado, entra no commit). Nenhum em
`~/.claude/hooks/` — são regras **deste** projeto, e regra de projeto que mora na máquina é
regra que o próximo clone não tem. Corolário que o inventário provou: a regra "o dono não
revisa páginas" existia só na memória da máquina, e por isso falhou.

---

## 5. Os mecanismos do harness, confirmados em documentação

Antes dos hooks, o que a documentação oficial garante — porque três decisões deste desenho
dependiam de mecanismo e duas estavam erradas na primeira redação. Confirmado por leitura das
páginas oficiais (`hooks-guide`, `memory`, `large-codebases`, `permissions`), com o nível de
confirmação declarado; a referência de hooks truncou em três tentativas e o que veio dela
está marcado como parcial.

| mecanismo | o que garante | uso neste desenho |
|---|---|---|
| **`.claude/rules/<nome>.md` com `paths:` no frontmatter** | Carrega automaticamente quando o Claude **lê** arquivo que casa o glob. Recarrega depois de `/compact` quando o arquivo é lido de novo. | **Substitui o hook H9.** É o mecanismo de primeira classe para "injetar o documento certo no momento do ato" — exatamente a pergunta do §4 da missão. Custo fixo: **zero**. |
| **`CLAUDE.md` em subdiretório** | Descoberto automaticamente e incluído **quando o Claude lê arquivos daquele diretório** (não no launch). | Regra de dado editorial em `data/editorial/CLAUDE.md`, de borda em `ops/nginx/CLAUDE.md`. |
| **Skill invocável como `/<nome>`** | O nome do diretório **é** o comando. `description` (+ `when_to_use`) carrega sempre, truncado em **1.536 caracteres** no *listing*; o corpo só na invocação. Recomendação: `SKILL.md` ≤ 500 linhas. | **`.claude/commands/` é formato LEGADO** — a doc diz "prefira skill para trabalho novo", porque skill aceita arquivos de apoio. Os 5 slash commands da primeira redação viram **skills**. |
| **`UserPromptSubmit`: stdout entra no contexto** | Texto simples (exit 0) é adicionado ao contexto do Claude. Em JSON, o campo é `hookSpecificOutput.additionalContext` — **no topo do JSON é silenciosamente ignorado**. | Viabiliza **H6**. O detalhe do aninhamento é obrigatório: errá-lo produz um hook que roda, sai 0 e não injeta nada. |
| **`PreToolUse` `deny`: a razão volta ao MODELO** | *"Claude Code cancels the tool call and feeds `permissionDecisionReason` back to Claude."* | Confirma o desenho "a mensagem ensina". Vale para H1, H2, H7. |
| **`PreToolUse` `ask`: a razão ao modelo NÃO é documentada** | A doc só diz que mostra o prompt ao usuário. | **Correção de desenho:** todo hook deste plano que usa `ask` passa a emitir **também** `hookSpecificOutput.additionalContext`, que é garantido — *"Text from `additionalContext` is kept from every hook and passed to Claude together."* Sem isso, H3/H4/H5/H10/H12 pediriam confirmação ao dono sem ensinar nada ao modelo: exatamente o erro #3. |
| **`PreToolUse` com campo `if`** | Filtro por padrão de ferramenta/caminho (ex. `if: "Edit(data/editorial/**/*.jsonl)"`), declarado **best-effort** — *"use the permission system rather than a hook to enforce a hard allow or deny"*. | Barateia o disparo dos hooks de escrita. Nunca como fronteira dura. |
| **`Stop`: `decision:"block"` impede o encerramento** | Confirmado (trecho parcial): *"Prevents Claude from stopping, continues the conversation"*. **O harness já tem teto: 8 bloqueios consecutivos sem progresso**, ajustável por `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, e a entrada traz `stop_hook_active`. | **Correção:** H11 **lê `stop_hook_active`** e usa o teto do harness; o *circuit-breaker* caseiro de `keep-working.sh` deixa de ser necessário e some do desenho. |
| **`Stop`/`SubagentStop` + `additionalContext`** | **Contradição reconhecida na própria doc** (issue `anthropics/claude-code#65495`): a seção de `SubagentStop` diz que não aceita; o changelog (≥ v2.1.163) e outras seções dizem que aceita. | H11 usa `decision:"block"` + `reason`, que é o caminho confirmado. **Não depender** de `additionalContext` em `Stop` sem teste empírico na versão instalada. |
| **Hooks do mesmo evento rodam em paralelo** | Citação literal: *"When an event fires, Claude Code runs all matching hooks in parallel"*; um `deny` não impede os irmãos de executar. | Confirma o orçamento da §1.5. **Nota de honestidade:** "custo = o do mais lento, não a soma" é **inferência** a partir do paralelismo, não frase da doc — a confirmação é a medição própria (36 ms paralelo vs 75 ms serial), e as duas coisas ficam separadas. |
| **`async: true`** | Roda em segundo plano sem bloquear; o `timeout` **não** se aplica. | H8. |
| **`systemMessage`** | Vai **só ao usuário**. | Nunca usado para ensinar o modelo. |
| **`@caminho` no `CLAUDE.md`** | **Inlinado no launch** — *"doesn't reduce context, since imported files load at launch"*. Profundidade máxima: 4 saltos. | **Não usar** como economia. Confirma a estrutura da §3, que não tem imports. |
| **Comentário HTML de bloco no `CLAUDE.md`** | Removido antes de entrar no contexto. | Nota para humano (data de revisão, motivo de um bloco) **de graça**. Entra no padrão do contrato novo. |
| **`permissions.deny` em Bash** | Texto **literal** com `*` como único especial; subcomandos checados um a um; e a doc afirma que **não é fronteira de segurança** — *"To inspect the full command text with your own logic before it runs, use a PreToolUse hook."* | **Não** usar `deny` para barrar padrão dentro do comando (`PKGS=./... && go build $PKGS` escapa). Confirma o que o repo já faz com `block-heavy-go.sh`: hook, não permissão. |
| **`InstructionsLoaded`** (matchers `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`) | Dispara quando um `CLAUDE.md` ou `.claude/rules/*.md` entra no contexto. | **O instrumento de verificação desta reescrita.** Permite medir se as regras por caminho realmente disparam, em vez de supor. Entra na onda 1. |

**A consequência mais importante:** a pergunta do §4 da missão — *"há mecanismo de hook que
injete o documento certo no momento da ação, em vez de confiar na lembrança?"* — tem resposta
**melhor que hook**. `.claude/rules/*.md` com `paths:` é nativo, custa zero fixo e não precisa
de bancada. A ressalva literal da doc: *"Path-scoped rules trigger when Claude **reads** files
matching the pattern, not on every tool use"* — o gatilho documentado é **leitura**. Se
`Edit`/`Write` sem `Read` prévio dispara, **não documentado**. Por isso o desenho usa os dois:
**regra por caminho** para o que é arquivo, e **hook** para o que é **comando** (contar log de
origem, purgar borda, rodar gate) — que nenhuma regra por glob alcança.

Um limite a respeitar, e o número dele eu tinha inventado. A doc diz: com muitas skills
descobertas, *"names always load, but when there are many, some skills lose their descriptions
entirely"* — criar skill demais **degrada a escolha da skill certa**. A primeira redação fixou
um teto de "12" sem base. **Medido no listing desta própria sessão: 43 skills descobertas** —
**21 do plugin `caveman` (49%)**, 17 nativas do Claude Code, **5 do repositório (12%)**. Ou
seja: o repo é a minoria do listing e **a alavanca do risco é o roster de plugins, não as
skills do projeto**. O desenho passa a **8 skills novas** (13 do repo, 51 no listing) e troca
o teto inventado por uma **medição na onda 2**: conferir se as 13 descrições do repo sobrevivem
inteiras ao corte de 1.536 caracteres. Se não sobreviverem, a correção é **revisar o roster de
`caveman`** — que já passou por triagem por uso medido em 2026-09-08 e voltou a 21 skills —
antes de consolidar skill do projeto, porque é ali que estão 49% das descrições.

---

## 5-bis. Os hooks a criar

Padrão obrigatório para todos, herdado de `block-heavy-go.sh`: regex em variável (para que
editar o hook não o dispare) · ancoragem em posição de comando · corpo de heredoc *quoted*
removido antes da análise · `trap 'exit 0' ERR` (*fail-open*: hook quebrado nunca trava a
sessão) · bancada `.test.py` com **caso de falso-positivo obrigatório** · alvo de custo
verificado por `tools/check-claude-code-hooks-latency --bench --max-ms 300` · e, quando a
decisão for `ask`, **`hookSpecificOutput.additionalContext` obrigatório** (a razão do `ask`
não é documentada como chegando ao modelo).

E a regra que vale para os onze: **a mensagem ensina o caminho certo, não só nega.** Nomeia
o motivo, dá o comando exato, e cita o incidente quando houver.

### H1 — `guard-check-sem-argumento`
- **Evento:** `PreToolUse` / `Bash`. **Decisão:** `deny` (exit 2). **Custo alvo:** ≤ 15 ms.
- **Bloqueia:** `run ./cmd/check` (e `run ./cmd/check all`, já coberto) sem nome de gate.
- **Mensagem:** `cmd/check sem argumento roda TODOS os gates — já abriu 45 processos e levou o load a 52. O nome do gate está em internal/checks/checks.go (leia, NÃO rode o runner para "ver a lista"). Use: ./tools/go-modern run ./cmd/check <nome>`

### H2 — `guard-sudo-nginx-t`
- **Evento:** `PreToolUse` / `Bash`. **Decisão:** `deny`. **Custo alvo:** ≤ 10 ms.
- **Bloqueia:** `sudo` e `nginx -t` no mesmo comando.
- **Mensagem:** `sudo nginx -t re-atribui var/nginx/ ao usuário da diretiva user (nobody); os workers tomam EACCES e o canal de máquina inteiro vira 500. Rode nginx -t SEM sudo.`
- Por que hook e não prosa: o efeito é um incidente de produção, e a diferença entre o
  comando certo e o errado são cinco caracteres.

### H3 — `guard-ordem-de-deploy`
- **Evento:** `PreToolUse` / `Bash`. **Decisão:** `ask` com razão (não `deny`: há caso
  legítimo). **Custo alvo:** ≤ 40 ms (lê o ledger).
- **Dispara em:** `purge-edge-cache` / `warm-edge-cache` / `deploy-binario-go`.
- **Faz:** lê `data/ops/edge_cache_purge.jsonl` e, se o deploy já gravou `scope: "tudo"`,
  devolve a linha com o horário.
- **Mensagem:** `O deploy de <hora> já gravou scope:"tudo" em data/ops/edge_cache_purge.jsonl. Purgar de novo joga fora ~870 s de aquecimento e deixa a borda em MISS. E em binário novo a ordem é binário → socket → serviço → invalidar ORIGEM → purgar borda: purgar antes repopula o Tiered Cache com o conteúdo VELHO (medido 2026-09-05: HIT, age 0, campos=0, 5×).`

### H4 — `guard-ordem-cadeia-editorial`
- **Evento:** `PreToolUse` / `Bash`. **Decisão:** `ask`. **Custo alvo:** ≤ 60 ms.
- **Dispara em:** `tools/generate-*` cujo alvo derive de `data/editorial/`.
- **Faz:** compara mtime do artefato com o das fontes e responde **qual passo vem antes**.
- **Mensagem:** `A cadeia tem ~9 artefatos e cada um tem de ser mais novo que sua fonte. Fora de ordem o erro diz "fingerprint mismatch" e NUNCA "ordem errada" — a fábrica ficou 31 dias parada por isso. Ordem em docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md; preserve o anterior em .agents/runtime/<data>/ antes. Próximo passo devido: <derivado>`
- Este hook converte em máquina a armadilha mais cara já medida no repo (31 dias).

### H5 — `guard-social-policy`
- **Evento:** `PreToolUse` / `Write|Edit`. **Decisão:** `ask`. **Custo alvo:** ≤ 20 ms.
- **Dispara em:** escrita em `content/social_policy.json`.
- **Mensagem:** `A política é lida no boot, cmd/social faz log.Fatalf se ela reprova e a unit tem Restart=always: campo que o binário VIVO recusa vira laço de boot. Confira git show HEAD:internal/socialpolicy/policy.go (DisallowUnknownFields + limiares). Campo novo entra no disco junto com o swap do binário e o restart.`

### H6 — `injeta-vereditos` — **o hook que resolve os erros #1 e #2**
- **Evento:** `UserPromptSubmit`. **Decisão:** nenhuma — **injeta contexto**. **Custo alvo:**
  ≤ 20 ms. Sai **≤ 400 tokens**, e só quando casa.
- **Faz:** casa o prompt do usuário contra uma tabela de tópicos encerrados e injeta **só as
  linhas de veredito** dos que casaram.
- **Tabela inicial** (`.claude/hooks/vereditos.tsv`, uma linha por veredito: `regex ⇥ data ⇥ autoridade ⇥ caminho ⇥ veredito`):

| tópico | veredito injetado |
|---|---|
| `datajud\|api p[úu]blica\|cl[áa]usula 3\.8\|termo de uso` | `LIBERADO. Parecer adotado pelo titular em 2026-09-05 (docs/data-sources/PARECER_DATAJUD_3_3_3_8.md): a 3.8 não exige autorização prévia; quem prevê autorização é a 3.13, só para passar de 120 req/min. Limite: 120 req/min e nivelSigilo>0. NÃO REABRA.` |
| `oab\|[ée]tica\|provimento 205\|risco disciplinar` | `Conteúdo informativo não tem risco de OAB. O vedado é: promessa de resultado, captação indevida, preço como chamariz. Inventar risco para travar conteúdo informativo é retrabalho — ordem do dono 2026-09-15.` |
| `sigilo\|anonimiza\|nome de parte\|remover nome` | `Publicidade é a REGRA, sigilo é a EXCEÇÃO (2026-08-29). Nome de parte e de agente público em ato publicado PODE constar; o que sai é IDENTIFICADOR (CPF, RG). Exceções taxativas em docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md. Suprimir demais destrói o ato: 88 "[nome removido]" já tornaram ilegível o canal diário.` |
| `revis[ãa]o humana\|auditoria humana\|aprova[çc][ãa]o do dono` | `O dono NÃO revisa páginas (2026-08-07). "reprovada_em_auditoria_humana" é veredito de AGENTE — código numérico com justificativa VAZIA. Quem revisa e corrige é você. Revisão humana NÃO é etapa de esteira.` |
| `analytics\|ga4\|clarity\|consentimento` | `Analytics é PERMITIDO (2026-08-27) e desativar a medição é proibido. UM script só (internal/pageinline.Script), CSP por hash.` |

- **Por que `UserPromptSubmit` e não `SessionStart`:** o `SessionStart` custa contexto em
  toda sessão, inclusive nas 90% que não tocam o assunto — foi assim que 27 hooks de
  `SessionStart` chegaram a injetar 27.463 tokens de abertura. O `UserPromptSubmit` custa só
  quando o assunto aparece. **Mecanismo confirmado** (§5): o *stdout* de texto simples do
  `UserPromptSubmit` é adicionado ao contexto do Claude. Se optar por JSON, o campo **tem** de
  ser `hookSpecificOutput.additionalContext` — no topo do JSON é **silenciosamente ignorado**,
  e um hook que roda, sai 0 e não injeta nada é pior que hook nenhum, porque ninguém percebe.
  A bancada de H6 tem de asseverar o **aninhamento**, não só o texto.

### H7 — `guard-promessa-de-resultado`
- **Evento:** `PreToolUse` / `Write|Edit`. **Decisão:** `deny`. **Custo alvo:** ≤ 25 ms.
- **Bloqueia:** promessa de resultado em texto editorial (`data/editorial/*.jsonl`,
  `content/*`), reusando o detector que já existe (`tools/check-promise-detector`).
- **Mensagem:** nomeia o trecho e o Provimento 205/2021 art. 40.
- **Ressalva de desenho:** este hook só barra o que o detector já sabe detectar. A classe
  **citação legal mal atribuída** continua P1 permanente e **sem detecção automática** — o
  contrato novo tem de continuar dizendo isso, porque é a única classe com risco real sob a
  OAB e nenhum hook a alcança. Skill `verificar-citacao-legal` é o instrumento.

### H8 — `lembra-bancada-do-pacote`
- **Evento:** `PostToolUse` / `Bash`. **async.** **Custo alvo:** ≤ 20 ms, fora do caminho
  crítico.
- **Dispara depois de:** `run ./cmd/check <nome>` verde.
- **Injeta:** `Gate verde NÃO é "não quebrei nada": em 2026-09-05 um gate passou VERDE e 14 dos 17 testes dele quebraram, e o defeito pousou em HEAD. Rode a bancada do pacote: ./tools/go-modern test -count=1 ./internal/<pkg>/`
- Converte em máquina a armadilha nº 14 do §1.

### ~~H9~~ → **regras por caminho**: `.claude/rules/*.md` com `paths:` — **substitui a tabela do §2**

Na primeira redação deste desenho H9 era um hook. **Era a solução errada:** o harness tem
mecanismo nativo para isso, `.claude/rules/<nome>.md` com `paths:` no frontmatter, que carrega
sozinho quando o Claude lê arquivo que casa o glob, custa **zero** fixo, não precisa de
bancada e recarrega depois de `/compact`. Hook aqui seria reimplementar, pior, o que já existe.

**A mudança de desenho, e é o ponto 4 da missão:** a tabela de hoje amarra **tema** ("antes de
mexer em anonimização, leia X"). **Tema não é acionável**, e o erro #4 do dono é a prova: quem
vai afirmar um volume de tráfego não pensa "vou ler sobre medição" — pensa "vou contar linhas
do log". O gatilho tem de ser o **ato**. E ato tem duas naturezas, com mecanismo diferente
para cada:

**(a) Ato que é ARQUIVO → `.claude/rules/` (nativo, zero custo fixo):**

| arquivo a criar | `paths:` | conteúdo (3 a 6 linhas operacionais + caminho do resto) |
|---|---|---|
| `.claude/rules/dado-editorial.md` | `data/editorial/**/*.jsonl`, `data/editorial/**/*.json` | nunca editar JSONL à mão — use `tools/generate-*`; preserve o anterior em `.agents/runtime/<data>/`; JSONL de produtor Go reserializado em Python muda 7.959 linhas por um caractere; `pages.json` escapa `&` como `&` |
| `.claude/rules/borda-e-csp.md` | `ops/nginx/**`, `ops/cloudflared/**` | a CSP das 10 mil páginas estáticas sai daqui, não do Go; `style-src` tem de ser byte a byte `render.StylesheetPath()`; `'self'` é proibido em `style-src` e `script-src`; `nginx -t` **sem** sudo |
| `.claude/rules/grafo-do-validador.md` | `internal/v2ingest/**`, `cmd/ingest-v2-stock/**`, `go.mod`, `go.sum` | `./tools/go-modern generate ./internal/v2ingest` e a atestação **no mesmo commit**; `go-modern list -deps` mostra quem está no grafo; confira `git status go.mod go.sum` antes (a atestação lê o **disco**); 25+ testes reprovam depois de ~10 min |
| `.claude/rules/medicao-de-audiencia.md` | `data/ops/access/**`, `data/ops/*bot*`, `data/ops/*edge*` | log de origem **não prova ausência** (cache de borda, rotação diária, agrupamento por UA); `edge_bot_agents_daily` é **cumulativo** (último por dia — somar dias infla); o acervo não passa pelo Go |
| `.claude/rules/politica-social.md` | `content/social_policy.json`, `content/redesocial_*` | a política é lida no boot; `DisallowUnknownFields`; `Restart=always` transforma campo novo em laço de boot |
| `.claude/rules/render-e-html.md` | `internal/render/**`, `internal/seo/**`, `internal/htmlcontract/**` | teto de 50 KB; UM script (`pageinline.Script`), CSP por hash; exatamente **2** ocorrências de `OAB/<seccional> <número>` (`author_credential_test.go`); H3 é do FAQ |

Alternativa equivalente para 2 destes, se a granularidade por diretório bastar: **`CLAUDE.md`
de subdiretório** (`data/editorial/CLAUDE.md`, `ops/nginx/CLAUDE.md`), também nativo e também
carregado só quando o Claude lê arquivos de lá. A regra com `paths:` é preferível porque o
glob é explícito e o `InstructionsLoaded` permite medir o disparo.

**Ressalva literal da doc, e é o motivo de (b) existir:** *"Path-scoped rules trigger when
Claude **reads** files matching the pattern, not on every tool use."* O gatilho documentado é
**leitura**; se `Edit`/`Write` sem `Read` prévio dispara, **não documentado**. Como o contrato
deste repo já obriga ler antes de editar (R1), o risco é pequeno — mas a onda 1 **mede** isso
com o hook `InstructionsLoaded` (matcher `path_glob_match`) antes de a onda 3 remover a prosa
correspondente do `CLAUDE.md`.

**(b) Ato que é COMANDO → hook (nenhuma regra por glob alcança):** contar log de origem
(**H10**), purgar borda (**H3**), regenerar derivado (**H4**), rodar gate (**H8**),
`cmd/check` sem argumento (**H1**), `sudo nginx -t` (**H2**). É aqui que hook é
insubstituível, e é só aqui que este desenho o usa para injeção.

- Custo comparado: a tabela do §2 custa **1.279 tok fixos** e compra zero leitura; o conjunto
  (a)+(b) custa **0 tok fixos** e entrega ~250 tok **no momento em que mudam a decisão**.

### H10 — `guard-camada-de-medicao` — **resolve o erro #4**
- **Evento:** `PreToolUse` / `Bash`. **Decisão:** `ask` com razão. **Custo alvo:** ≤ 15 ms.
- **Dispara em:** comando que conta/agrega sobre `data/ops/access/`, `nginx-*.jsonl` ou log
  de origem **com** termo de bot (`Googlebot`, `GPTBot`, `ClaudeBot`, `bingbot`,
  `PerplexityBot`, `crawler`, `bot`).
- **Mensagem:** `Você está medindo rastreio de bot na camada ERRADA. O acervo NÃO passa pelo Go e sai estático do disco; o log de origem não vê o que a borda serviu, rotaciona por dia e agrupa por UA. Ausência de sinal aqui NÃO é evidência de ausência. Use a skill medir-bots. E lembre: edge_bot_agents_daily é CUMULATIVO (último por dia), somar dias infla.`

### H11 — `guard-devolve-decisao` — **resolve o erro #3**
- **Evento:** `Stop`. **Decisão:** `block` + `reason` — mecânica já provada nesta máquina por
  `keep-working.sh`. **Custo alvo:** ≤ 50 ms.
- **Faz:** lê a última mensagem do assistente no transcript e casa padrões de devolução —
  `quer que eu`, `posso seguir`, `prefere que`, `opção (a)`, `qual das duas`, `aguardo`,
  `me diga se`, `devo prosseguir`.
- **Se casar, devolve:** `Você devolveu a decisão ao dono. O contrato manda DECIDIR SEM DEVOLVER: diante de duas rotas, escolha a melhor, registre o porquê e execute. O único limite é o destrutivo e a decisão genuinamente exclusiva do dono (ética ou negócio irreversível) — e nesse caso diga QUAL em uma linha e siga trabalhando outra frente. Reescreva o fecho: decida e execute.`
- **Escopo estreito de propósito** — e essa é a diferença em relação ao `keep-working.sh`,
  que bloqueava *toda* parada e por isso (provavelmente) foi desligado. H11 bloqueia **só a
  parada que devolve decisão**; parada que entrega trabalho passa.
- **Sem circuit-breaker caseiro.** A primeira redação deste desenho copiava o `MAXBLK=25` de
  `keep-working.sh`; a documentação mostrou que **o harness já tem o teto**: *"Claude Code
  overrides a Stop hook after it blocks eight times in a row without progress"*, ajustável por
  `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, e a entrada do hook traz **`stop_hook_active`**. H11 lê
  `stop_hook_active` e **não bloqueia quando ele é verdadeiro** — é a guarda oficial, e
  reimplementá-la seria a terceira cópia de um mecanismo que já existe (o mesmo antipadrão que
  a §7 deste documento condena no 0.70).
- Usa `decision:"block"` + `reason`, que é o caminho confirmado. **Não** depende de
  `additionalContext` em `Stop`: a própria doc se contradiz nesse ponto (issue
  `anthropics/claude-code#65495`) e depender de campo em disputa é fragilidade gratuita.
- **Registro necessário:** ao ligar H11, escrever no `keep-working.sh` a nota de aposentadoria
  no padrão do `sequential-agents.sh` (data, causa medida, onde está o substituto). Hoje ele
  está órfão e mudo.

### H12 — `guard-revisao-humana` — **resolve o erro #5**
- **Evento:** `PreToolUse` / `Write|Edit`. **Decisão:** `ask` com razão. **Custo alvo:**
  ≤ 20 ms.
- **Dispara em:** escrita cujo conteúdo novo contenha `revisão humana`, `revisao humana`,
  `aprovação do dono`, `revisar manualmente`, `auditoria humana` **em posição de etapa**
  (lista, tabela, passo numerado de plano).
- **Mensagem:** a linha (d) do §1 do contrato novo, mais: `Se a etapa é mesmo necessária, ela é do CLAUDE CODE revisando e corrigindo — nunca do dono.`
- **E a causa raiz, que é de dado, não de prosa:** o rótulo
  `reprovada_em_auditoria_humana` (`tools/generate-v2-publication-severity:594`) **mente
  sobre a própria origem** — é escrito a partir de saída de agentes de IA de sessões
  anteriores (`.agents/runtime/staging/audit_lote*.json`,
  `audits/lote*_veredito.json`, `tmp_rescue/*/qa_*.json`), com vereditos numéricos
  (`REPROVADA:3`, `:8`, `:11`) e campo de justificativa **vazio**. O nome é o que produz o
  erro: quem lê "humana" respeita como sentença do dono. **Renomear para
  `reprovada_por_auditor_agente`**, com migração do dado e leitor que aceite os dois nomes
  por uma geração. Isso é o eixo "identidade literal" da missão aplicado ao **dado**, e é o
  único item desta seção que corrige causa em vez de sintoma.

**Nenhum hook novo usa `SessionStart`.** É a única regra de custo inegociável deste desenho:
`SessionStart` cobra contexto para sempre.

---

## 6. As skills a criar

Skill é **lazy** e é o mecanismo certo para procedimento: o `description` do frontmatter é o
que custa sempre; o corpo só entra quando invocado — *"skill descriptions are loaded into
context so Claude knows what's available, but full skill content only loads when invoked"*.
Toda `description` nova é escrita **por ATO**, no padrão que as 5 skills atuais já acertaram.

**Duas correções de desenho vindas da documentação.** (a) **Nada de
`.claude/commands/`.** A primeira redação propunha 5 slash commands; a doc diz que o
diretório de skill **já é** o comando (`/<nome>`) e que `.claude/commands/` é *"the older
format"*, com a recomendação explícita *"prefer a skill for new work, since skills also
support supporting files"*. O diretório permanece inexistente de propósito — os 5 viram
skills. (b) **Orçamento de descrições** (medido na §5): 43 skills no listing, 5 do repo.
Cada `description` nova cabe em **uma frase que começa por "Use ao/antes de/quando"**, o corpo
fica ≤ 500 linhas com referência em arquivo de apoio ao lado do `SKILL.md`, e a onda 2 **mede**
se as 13 sobrevivem ao corte de 1.536 caracteres.

**São 8 skills novas, não 7 nem 9** — a primeira redação dizia "7" em dois lugares e "11" num
terceiro, e nenhum dos três casava com a lista. `deploy-binario` e `deploy-decidir` viraram
**uma** skill (`deploy`): subir binário e publicar conteúdo são o mesmo ato ("vou pôr algo em
produção") e separá-los força o modelo a escolher entre duas descrições parecidas, que é como
se perde a skill certa. As 8: `deploy`, `cadeia-editorial`, `atestar-grafo`,
`validar-proporcional`, `saida-grande`, `publicar-social`, `commit-v2`, `coord`.

### Skills

| skill | `description` (o gatilho) | contém |
|---|---|---|
| `deploy` | "Use ao pôr qualquer coisa em produção: binário Go novo, conteúdo republicado, purga ou aquecimento de borda." | **Binário:** a ordem binário → socket → serviço → invalidar origem → purgar borda; `Type=notify` + `LISTEN_FDS` (bind próprio = EADDRINUSE em laço de 5 s com a porta em LISTEN → 504); `./tools/deploy-binario-go`. **Conteúdo:** as 4 perguntas da matriz do §6 e a decisão de `--ressemear` e tipo de purga; lê `data/ops/edge_cache_purge.jsonl`; manda ler o **exit real** do passo antes de purgar à mão (o `--purge-targets` já caiu no teto de churn com exit 1 e o diagnóstico impresso mentiu); `purge-edge-cache` + `warm-edge-cache --rps 12`. Substitui `deploy-binario` **e** `deploy-decidir`: é um ato só. |
| `cadeia-editorial` | "Use antes de regenerar qualquer derivado de `data/editorial/` ou quando um comando reprovar com `fingerprint mismatch`." | Os ~9 artefatos e a ordem topológica; como derivá-la dos detectores (`grep -rn "older_than" internal/ --include=*.go`); preservar em `.agents/runtime/`; que o erro nunca diz "ordem errada". |
| `atestar-grafo` | "Use ao tocar `internal/v2ingest`, `cmd/ingest-v2-stock`, `go.mod` ou `go.sum`." | `go-modern generate ./internal/v2ingest`, atestação no mesmo commit, `list -deps` para ver quem está no grafo, `git status go.mod go.sum` antes (a atestação lê o disco), os 25+ testes que reprovam depois de ~10 min. |
| `validar-proporcional` | "Use antes de rodar teste, gate ou passada de validação, para escolher o escopo pelo risco em vez do hábito." | `generate-check-selection-profiles --paths <arquivos>`; probe curto por *stride* antes de qualquer 10k; teste focado; `run-heavy-throttled` e suas 5 variáveis; nunca full-tree. |
| `saida-grande` | "Use quando a saída de um comando ou arquivo for PROCESSADA (contar, filtrar, agregar) em vez de lida inteira." | `ctx_execute` / `ctx_batch_execute` / `ctx_execute_file` / `ctx_search` com exemplos deste repo; quando NÃO usar (saída curta, mutar estado); `PIPESTATUS[0]` porque `cmd \| tail` engole o exit. |
| `publicar-social` | "Use ao publicar em Facebook, LinkedIn ou Instagram pelos perfis do portal." | `:99` nunca `:0`; `page.screenshot()` nunca `scrot`; `olhar-pagina.mjs`; a guarda de "Turbine esse post"; Instagram bloqueado desde 2026-08-27; inscrição na OAB em toda arte (CED art. 44 §1º). |
| `estado-real` (**ampliar**) | (mantém) | Acrescentar: páginas por `unique_intent_id` no `published_manifest`; severidade por `data/ops/v2_publication_severity_summary.json`; pacotes por `go-modern list`; linguagens por `git ls-files`; grafo por `data/ai/grafo_manifest.json`; parâmetros do Ollama pelo drop-in. **E corrigir a citação obsoleta** a `CLAUDE.md:72` "publicação zero", linha que não existe mais. |

### Skills que também funcionam como comando digitado

| skill / `/comando` | `description` (o gatilho) | contém |
|---|---|---|
| `commit-v2` | "Use ao commitar página do acervo v2 ou intenção de portfólio." | `portfolio_v2/` primeiro, `v2_pages/` depois; `./tools/check-v2-portfolio-pairing` antes; `git add <caminho exato>` e `git commit -F <arquivo>` **separados**; lock de commit (`/tmp/opt-wiki-commit.lock`) distinto do heavy; esvaziar o índice antes de pedir a vez. |
| `coord` | "Use ao mudar de frente de trabalho ou antes de comando pesado, para não colidir com outra sessão." | Presença (`generate-coord-presence`), inbox (`check-coord-inbox --agent SEU_ID --last 15`), `check-coord-status`, `check-load-headroom --max 12`; nunca `pkill`; lock ativo ⇒ outra frente. |
| `~/.claude/skills/terminal/` | "Use ao entrar numa frente nova ou antes de onda pesada de agentes." | `ai-brief`, `ai-pane run` (nunca `send`+`read`, que devolve o eco), `ai-tokens`, `ai-top`; `PIPESTATUS[0]` em pipeline. |

---

## 7. A des-hardcodificação

### 7.1 O limiar de similaridade 0,70 — **6 constantes + 2 usos inline, zero ligação**

| arquivo:linha | símbolo |
|---|---|
| `internal/v2pagedistinctness/types.go:28` | `DefaultBodyJaccardThreshold = 0.70` |
| `internal/v2bodyneardup/neardup.go:65` | `DefaultThreshold = 0.70` |
| `internal/authorialmassrefinementquality/refinement_quality.go:39` | `SemanticRiskThreshold = 0.70` |
| `internal/authorialmasssemanticreviews/semantic_reviews.go:20` | `MinRiskScore = 0.70` |
| `internal/cerebro/gate.go:139` | `LimiarDeSimilaridade = 0.70` |
| `internal/fiscalization/fiscalization.go:261` | `DefaultSemanticSimThreshold = 0.70` |
| `internal/batchdrafts/batchdrafts.go:265` | inline |
| `internal/authorialmassreadiness/readiness.go:1340` | inline |

**Nenhum importa o outro.** O `CLAUDE.md` §8 diz "Similaridade de corpo < 0,70" como se
houvesse um valor; há oito. Mudar o limiar exige tocar oito pontos e **esquecer um não gera
erro de compilação** — o gate simplesmente passa a medir outra régua.

**Onde passa a morar: UMA constante Go em pacote de política** — `internal/contentpolicy`,
importada pelos oito. **NÃO em JSON de config**, e a razão é primária:
`internal/fiscalization/fiscalization.go:182` diz que *"o 0.70 é SEMANTICO e vive no
model2vec"* — é **valor calibrado contra um modelo**, não parâmetro de operação. Valor
calibrado em JSON é valor que alguém muda sem recalibrar. A constante entra com o comentário
da calibração (modelo, data, amostra) e um teste que **falha se qualquer pacote redeclarar
0.70** — mesma técnica de `site_url_flexibility_test.go`, varrendo o literal fora de
comentário.

### 7.2 O teto de 50 KB — 4 declarações

`internal/htmlcontract/htmlcontract.go:28` `HTMLBudgetBytes = 50000` é o canônico (citado por
`seo_test.go:497`). Redeclarado em `internal/authorialmassreleaseevidence/release_evidence.go:38`,
`internal/priorityreleaseevidence/priorityreleaseevidence.go:34`,
`internal/publicfinalpagerehearsal/public_final_page_rehearsal.go:44`. **Correção:** os três
importam `htmlcontract.HTMLBudgetBytes`; teste proíbe redeclaração do literal.

### 7.3 O domínio — 47 literais de runtime, e o teste que não os vê

`grep` em `internal/ cmd/ --include=*.go` excluindo `_test.go`: **47 ocorrências** de
`"https://wikijuridica.com.br"` em código. Exemplos:
`internal/publicrelease/publicrelease.go:62` (`officialReleaseBaseURL`),
`internal/htmlreadability/evidence.go:491` e `:499`,
`internal/factorymetrics/factorymetrics.go:529`,
`internal/batchsourcespecificity/batchsourcespecificity.go:161`,
`internal/batchpublicmanifest/batchpublicmanifest.go:172` e `:183`,
`internal/socialtema/folha.go:37`, `internal/releaserehearsal/releaserehearsal.go:843`,
`internal/checks/agent_skills_discovery_gate.go:52` (4 ocorrências).

O contrato diz que a URL é *"travada em `content/site.json`"*, e existe
`site_url_flexibility_test.go` — mas **ele varre só `"Rafael Toledo"`, `"227191"` e
`"OAB/RJ"`** (lido: o `for _, forbidden := range []string{...}` da linha ~82). **O domínio
não está na cerca.** Ou seja: a disciplina anti-hardcode existe, está bem construída
(inclusive com o cuidado de não acusar comentário, depois de dois falsos-positivos
catalogados) e simplesmente **não cobre o valor que o contrato mais afirma estar centralizado**.

**Correção, em duas partes.** (a) Acrescentar `"wikijuridica.com.br"` à lista `forbidden`
do teste, com isenção nominal para a **única** fonte legítima — o `content` que lê
`site.json` — e para `internal/wikijuridicabot/bot.go:72` (`DocumentacaoURL`), que é a
identidade canônica de saída. (b) Os 47 pontos passam a receber a base por parâmetro ou por
`content.LoadRepository(...).BaseURL`. Os de `internal/checks/*` e `crawlsmoke` são oráculos
de gate (valor esperado fixo é correto ali) e ficam, **listados na isenção** — isenção
nomeada é diferente de cerca ausente. Estimativa de reparo real: **não medido** por ponto;
a triagem legítimo-vs-indevido dos 47 é o primeiro passo da execução.

### 7.4 O piso de 250 palavras — o mesmo número em dois produtores sem ligação

| onde | o quê |
|---|---|
| `cmd/generate-acordao-pages/main.go:402` | `const pisoEmentaPalavras = 250`. O comentário das linhas 399-400 diz: *"Medido: com 250 palavras sobram 1.674"* |
| `tools/generate-v2-publication-severity:50` | `MIN_WORDS_HARD = 250   # abaixo disso nao e pagina, e nota` |

São **duas linguagens, dois produtores, zero ligação** — e o `CLAUDE.md` §5 fala de "corpo
abaixo de 250 palavras" como se fosse um só. **Mas eles não são o mesmo valor**, e isso é o
achado: um é **calibração de rendimento** (com 250 sobram 1.674 candidatos — mexer muda
quantas páginas existem), o outro é **piso de qualidade editorial** (abaixo disso não é
página). Fundi-los seria errado. A correção é **nomeá-los diferente e declarar a coincidência**:
`pisoEmentaPalavras` mantém o nome e ganha `// coincide com MIN_WORDS_HARD por acidente de
calibração, não por dependência`; o piso editorial passa a ter **um** dono
(`internal/contentpolicy.MinBodyWords`) do qual o Python lê por artefato gerado, não por
cópia do número. Sem isso, alguém "unifica" os dois e muda a população de páginas sem saber.

### 7.5 Caminhos absolutos

| achado | veredito |
|---|---|
| `internal/codex2integrationaudit/audit.go:28` `DefaultMainRoot = "/opt/wiki"` | **corrigir** — constante de produção que não deriva de `os.Getwd()`/env. Rodar o binário num worktree de ensaio aponta silenciosamente para a árvore de produção, e o contrato já tem o precedente "ensaio: tudo por cópia" |
| 4 units com `Environment=PATH=/home/rafael/go/bin:…` (`wikijuridica-daily-content-noticias`, `-qualidade-longa`, `-qualidade-diaria`, `-noticias-coleta`) | **corrigir para `%h/go/bin`** ou `EnvironmentFile` — hoje a unit amarra o usuário |
| `ops/systemd/cloudflared-wikijuridica.service:26` e `cloudflared-wikijuridica-replica@.service:110` → `/home/rafael/bin/cloudflared-2026.7.3` | **corrigir**: caminho + versão fixada no `ExecStart`. Trocar de versão hoje exige editar 2 units; o binário devia estar em caminho estável do repo/ops com a versão em `EnvironmentFile` |
| `tools/test_start_ai_terminal.py:26-28,290`, `tools/test_commit_verified_v2_workflow_results.py:4151` | **fica** — fixture determinística de teste |
| `/tmp/opt-wiki-agent-heavy.lock`, `/tmp/opt-wiki-commit.lock` | **fica** — lock de coordenação com nome fixo por desenho, e `/tmp` é o lugar certo para lock |
| `127.0.0.1:8088` / `:8089` (111 / 140 ocorrências) | **fica** — é a topologia oficial declarada no §3, não vazamento |
| `.toolchains/` (43) | **fica** — é o mecanismo oficial, via `./tools/go-modern` |

Não encontrado: nenhum token, ID de zona Cloudflare, chave de API ou e-mail do dono
hardcoded em `ops/` ou `tools/`. **Não medido:** os 86 arquivos com `/tmp/` literal não foram
triados um a um para separar lock legítimo de produto em `/tmp` (o hook
`hook-warn-tmp-product-write` já cobre o caso de escrita nova).

### 7.6 Identidade literal: onde a disciplina está certa, e onde falta

**Certo** (verificado, não é achado): `G-H6FQ8CQJNR` e `y8lzjnjpay` só em
`internal/webanalytics/webanalytics.go`; `227191` em `internal/agendaprazo/agendaprazo.go:110`
e `internal/socialcard/cartaodethread.go:92` só em **comentário** descrevendo formatos que o
validador recusa; `Chrome/126.0.0.0` em `cmd/collect-stf-informativo/main.go:68-69` é
exceção **documentada e isenta pelo próprio gate** (`EhNavegadorDisfarcado` em
`internal/wikijuridicabot/bot_test.go:168`, porque o STF devolve 403 a UA de robô);
simulação de Googlebot por `httptest.NewRequest` é legítima pelo §11.

**Falta**: o **domínio** (§7.3). É o único ponto onde a mesma disciplina que protege a
identidade do advogado não protege a identidade do site — e o contrato afirma o contrário.

---

## 8. Os fatos obsoletos, com o número medido

### Obsoletos CONFIRMADOS

| # | afirmação | onde | afirmado | **medido 2026-09-15** | método |
|---|---|---|---|---|---|
| 1 | páginas públicas | `CLAUDE.md:128` | 11.039 | **11.106** | `unique_intent_id` distintos em `data/editorial/published_manifest.jsonl` |
| 2 | contagem de linguagens | `CLAUDE.md` §3 | 2.493 Go · 259 Py · 28 JS · 27 sh | **3.259 Go · 365 Py · 23 JS · 82 sh** | `git ls-files \| grep -c` |
| 3 | pacotes Go (2 menções) | `CLAUDE.md` §4 | 488 | **585** | `./tools/go-modern list ./internal/... ./cmd/...` |
| 4 | severidade da publicação | `CLAUDE.md` §5 | 100 crít · 9.394 méd · 747 limpas | **119 · 10.337 · 769** | `data/ops/v2_publication_severity_summary.json` |
| 5 | média do HTML publicado | `CLAUDE.md` §6 | 22.631 B sobre 10.369 arquivos | **23.414 B sobre 11.358 `.html`** | `os.walk` + `getsize` em `public/` |
| 6 | grafo jurídico | `ops/systemd/wikijuridica-grafo-juridico.service:38` | 9,7 s · 13.575 nós · 148.571 arestas | **43,134 s · 79.706 nós · 393.081 arestas** | `data/ai/grafo_manifest.json` |
| 7 | aresta `aplica` "não populada" | `tools/generate-grafo-juridico:55` | não populada | **22.789 arestas `aplica`** — e a linha ~637 do **próprio arquivo** as popula | `grafo_manifest.json.arestas_por_tipo` |
| 8 | dimensão dos embeddings | `internal/semantica/semantica.go:12` | "10.141 paginas x 1024 dims x 4 B = 41,5 MB" | **11.118 páginas** (o campo `paginas` de `data/ai/embeddings/ativo.json`, modelo `qwen3-embedding:0.6b`, `dim` 1024) ⇒ 11.118 × 1024 × 4 = **45.539.328 B = 45,5 MB**; e o diretório tem **49.711.702 B = 49,7 MB** | `json.load` de `ativo.json` + `du -sb`. **Primeira redação media a população ERRADA** (11.106 do `published_manifest`): página publicada e página com embedding são conjuntos diferentes — "medir a coisa ao lado", que este repo já catalogou |
| 9 | RSS do `qwen3.5:4b` | `CLAUDE.md` §12 (herdado) | 3,23 GB | **conflito interno na fonte**: o mesmo `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` tem 3,23 GB (2026-09-08/09) e **5.816 MB de RSS** (2026-09-10). O contrato herdou o número antigo | grep no drop-in |
| 10 | precedente citado na skill | `.claude/skills/estado-real/SKILL.md` | cita `CLAUDE.md:72` "publicação zero" | linha inexistente hoje | leitura das duas |
| 11 | maior arquivo mensal de espelhos | `internal/stjacordaos/coleta.go:28-29` | "O maior medido em 2026-09-08 tem **360.619 bytes**; 64 MB e teto de sanidade, nao expectativa" | **26.704.470 B** (`registros-2026-06.jsonl`), de 54 arquivos | `find … -printf '%s\t%p' \| sort -rn` |
| 12 | mecanismo de build da onda de conteúdo | `ops/systemd/wikijuridica-daily-content.service:7` | "O binário Go é construído no **ExecStartPre**" | a unit **não tem `ExecStartPre=`**. Só 4 units no repo têm (`wikijuridica-nginx`, `-server`, `-energia`, e o drop-in `-backup.service.d/10-host-state.conf`) | `grep -rc 'ExecStartPre=' ops/systemd/` |

### CONFIRMADOS CORRETOS (a missão suspeitava, a medição absolveu)

- **§5, "onze motivos críticos":** o texto **vivo** já diz onze e lista os onze. Os motivos
  reais no gerador são `sem_corpo`, `falta_<campo>`, `campo_obrigatorio_ausente`,
  `corpo_abaixo_de_250_palavras`, `promessa_oab:*`, `encoding:*`,
  `intent_duplicado_entre_shards`, `intencao_pulada_deliberadamente`, `area_nao_derivavel`,
  `reprovada_em_auditoria_humana`, `veredito_conflitante` (+ `rota_duplicada` em runtime).
  O enunciado da missão citava a redação antiga. **Nada a corrigir** — e é um exemplo de
  contrato que se auto-corrigiu direito, com data e motivo.
- ~~`internal/stjacordaos/coleta.go:29` estaria correto por ser autodatado~~ — **ERRADO, e a
  correção está na tabela acima como item 11.** Esta linha, na primeira redação, absolvia o
  item porque o comentário traz data. Medi: **não absolve.** A regra "comentário datado não é
  obsolescência" vale quando o número datado ainda descreve a ordem de grandeza; aqui ele
  errou por **74×** e invalidou o raciocínio de folga que justifica a constante. Aplicar o
  princípio sem medir foi absolver o item que o dono listou — e é exatamente o defeito que
  este documento acusa nos outros.
- CSS de **12.117 bytes**: confere exatamente (`public/assets/wj-5b082578c84d2407.css`).
- Ollama: `MemoryMax=12G`, `OLLAMA_MAX_LOADED_MODELS=2`, `CPUWeight=60`, `Nice=5`,
  `OOMScoreAdjust=800`, `Slice=wikijuridica_alimentacao.slice`; `1,85`/`2,90` tok/s; `234,2 s`
  — todos batem com o drop-in. O §12 **já registrou a própria superação com data e motivo**.
- Os **14** nomes `./tools/<x>` extraídos do `CLAUDE.md` existem e são executáveis (`test -x`).
- Os **6** `docs/*.md` da tabela do §2 existem.
- O gate `contrato-dado-real` existe (`internal/checks/checks.go:801` e `:1679`).

### NÃO CONFIRMADOS / NÃO MEDIDOS — declarados

- ~~"unit da onda compila no `ExecStartPre`": não localizei a unit~~ — **LOCALIZADA E
  CONFIRMADA**, agora item 12 da tabela de obsoletos. A unit é
  `ops/systemd/wikijuridica-daily-content.service` ("a onda que produz CONTEÚDO"); a primeira
  busca falhou por procurar o nome "onda" no arquivo, não a função. Lição de método que vale
  registrar: **procurar pela função, não pelo apelido** — o apelido do dono raramente é o nome
  do arquivo.
- `cmd/generate-acordao-pages/main.go:185`, flag `-limite`: o comentário **no código** diz
  "máximo de páginas a ACRESCENTAR (nunca corta publicada)". Se ela conta remontagens, o
  defeito está na contagem e não na descrição. **Não medido** — exige rodar o gerador.
- `76,7%` cross-área vs `23,4%` (§7) — **não medido**.
- `84 verificações` do `check-analytics-loader` — **não medido**.
- `5 instâncias` da frota do túnel — **não medido**.
- Ferramentas citadas **sem** o prefixo `./` exato (`tools/warm-origin-cache`,
  `tools/measure-tunnel-gaps`, `tools/check-csp-style-hashes`, `tools/check-efeito-nos-bots`,
  `tools/generate-page-content-revision`) — existência **não testada**.

### A correção estrutural, que vale mais que as dez linhas

Corrigir 11.039 → 11.106 hoje garante que o número esteja errado amanhã: a fábrica publica
todos os dias. **Dez dos dez achados são da mesma classe — número de estado gravado em texto
de contrato.** A regra nova, cobrada por teste (§9):

> **Nenhum número de estado no `CLAUDE.md`.** O contrato nomeia o ARTEFATO que carrega o
> número (`published_manifest`, `v2_publication_severity_summary.json`,
> `grafo_manifest.json`, o drop-in do Ollama) e a skill que o mede (`estado-real`). Número em
> prosa de contrato só é admitido com `medido em <AAAA-MM-DD>` **e** o comando que o reproduz
> — que é a regra do próprio `docs/CONTRATO_DADO_REAL.md` R3, hoje não cobrada no `CLAUDE.md`.

Comentário em código é outro caso: ali o número é **contexto de engenharia** e o padrão que
o repo já acertou (`coleta.go:29`) é **autodatar**. Os itens 6, 7 e 8 se corrigem no lugar,
com a data — e o 7 não é número desatualizado, é **comentário que contradiz o código do
próprio arquivo**, que é bug de documentação a consertar, não fato a atualizar.

---

## 9. O teste de contrato

Um arquivo novo, `internal/contract/misc/claude_md_operational_test.go`, no padrão de
`peer_governance_test.go` e `engineeringnowcontract`. Quatro asserções — as três que o
advisor exigiu mais a que os dez obsoletos justificam:

**T1 — cláusulas que não podem sumir.** Vetor `requiredClauses` com casamento por whitespace
normalizado (`foldContractWhitespace` do `engineeringnowcontract`, **não** byte-exato — é o
que permite reformatar sem quebrar). Entram: os 7 vereditos do §1; os 8 invariantes do §3;
"Publicidade é a REGRA, sigilo é a EXCEÇÃO"; "O dono NÃO revisa páginas"; "Mesmo conteúdo
para bot e humano"; "o que gera e serve HTML é Go"; "anti-fraude não se flexibiliza";
"citação legal mal atribuída é P1 permanente"; e o §6 **verbatim**, que já é cobrado por
`peer_governance_test.go` (o teste novo **não** o duplica — apenas confere que a seção
continua presente, para que uma reordenação não a mova para fora do alcance do outro teste).

**T2 — teto de bytes, para que não volte a crescer.** `len(CLAUDE.md) <= 18000` bytes
(alvo ~4.500 tok; 18.000 B dá folga de ~15% sobre a estimativa de 15.750 caracteres). É a
asserção que impede a regressão que criou este problema: um contrato cresce por acréscimo
bem-intencionado, um bloco de cada vez, e ninguém vê o total. Quem quiser passar do teto
**move algo para skill/hook primeiro** — o teste força a troca, não o acúmulo. Mensagem de
falha: `o CLAUDE.md passou de 18 KB. Isso é custo fixo em TODA sessão. Antes de subir o teto, mova um bloco de procedimento para .claude/skills/ ou .claude/commands/ (veja a tabela de migração em docs/…).`

**T3 — nenhum caminho citado é inexistente.** Extrai do `CLAUDE.md` todo `tools/<x>`,
`docs/<x>.md`, `internal/<x>`, `cmd/<x>`, `.claude/<x>` e `ops/<x>` e exige `os.Stat`. É o
teste que impede a classe "frase que manda rodar ferramenta que não existe" — hoje os 14
`./tools/` passam, mas nada garante que continuem passando, e a lista de ausentes desta
auditoria está incompleta justamente porque a extração por prefixo `./` não pega
`tools/warm-origin-cache`. O teste extrai os dois formatos.

**T4 — nenhum número de estado em prosa.** Varre o `CLAUDE.md` por números com separador de
milhar (`\d{1,3}\.\d{3}`) e por `\d+([.,]\d+)?\s*(KB|MB|GB|páginas|pacotes|rotas|arestas|nós)`
e **reprova** quem não vier acompanhado de `medido em <AAAA-MM-DD>` **na mesma frase** ou de
uma isenção nomeada. Isenções iniciais: `50 KB` (teto de contrato, não estado), `10.000
páginas` (meta P0, não medição), `12.117 bytes` do CSS (invariante conferido por gate),
`OAB/RJ 227191`, `120 req/min`, `9 GiB`, `Provimento 205/2021`, `DEC-0xx`, datas.
**Isenção obrigatória para citação legal**, ou T4 reprova na primeira frase correta: o
padrão `\d{1,3}\.\d{3}` casa `Lei 9.610/98`, `Lei 12.527/2011`, `art. 1.022`, `Res. CNJ
121/2010` — e o §1 do contrato novo cita a base legal do DEC-032. Entram na lista de isenções:
`Lei \d`, `art\. \d`, `Res\. CNJ`, `Provimento \d`, `CPC art`, `CF art`, `Tema \d`,
`Súmula \d`, `OAB/`, `DEC-\d`, e data em `AAAA-MM-DD`. A prova por mutação de T4 tem de
incluir um caso **negativo** com citação legal — senão a asserção nasce reprovando o texto que
existe para proteger.

É a asserção que teria pegado os itens 1 a 5 desta auditoria antes do dono.

**T5 — a estrutura de instrução não se desmonta em silêncio.** Para cada mecanismo que a §4
promete, uma asserção de existência: os 11 hooks registrados no `.claude/settings.json`; as 6
`.claude/rules/*.md` com `paths:` não-vazio e glob que casa pelo menos um arquivo rastreado
(*controle positivo* — regra cujo glob não casa nada é regra morta que responde ao `grep`); as
13 skills do repo com `description` presente e **≤ 1.536 caracteres** somados a
`when_to_use`, que é onde o *listing* trunca. Sem T5, a onda 3 remove a prosa e um mecanismo que ninguém ligou
deixa a regra sem nenhum dono — o pior estado possível, porque nem custa token nem impõe nada.

**Mais um gate, fora do Go:** `tools/check-modo-operacional`, que (a) roda
`check-claude-code-hooks-latency --bench --max-ms 300`, (b) confere que **todo** hook em
`.claude/hooks/` está registrado no `.claude/settings.json` **ou** tem nota de aposentadoria
datada no cabeçalho **ou é auxiliar chamado por um hook registrado** (como
`git-guard-prune.py`, chamado por `git-guard.sh`) — a régua que `sequential-agents.sh` cumpre
e `keep-working.sh` não, e que impediria os 4 órfãos de hoje; (c) confere que todo hook tem `.test.py` com pelo menos um
caso de falso-positivo; (d) confere que todo hook de decisão `ask` emite também
`hookSpecificOutput.additionalContext` **aninhado** — o campo no topo do JSON é silenciosamente
ignorado, e essa é a falha que não dá erro nenhum. `check-*` é **read-only** por contrato:
ele reprova, não conserta.

---

## 10. A economia estimada, com método

**Método.** Caracteres ÷ 3,5 (PT-BR acentuado), com intervalo ÷4,0 a ÷3,0. Não há tokenizador
local e `count_tokens` exigiria credencial de API, vedada pelo contrato — portanto **estimativa
declarada, não medição**.

**Dois alvos, e eles não são o mesmo número.** A estrutura desenhada na §3 soma **3.294 tok**;
o teto da asserção T2 é **~4.500 tok (18.000 B)**. A diferença é folga deliberada: o teto tem
de caber a redação real sem forçar quem escreve a cortar conteúdo por causa de uma vírgula. As
contas abaixo usam o **alvo redigido (~15.750 caracteres)**, não o teto — a economia está
portanto **subestimada**, não inflada. Se a redação chegar no teto, a economia cai de 8.227
para ~6.800 tok.

### Custo fixo por sessão

| arquivo | caracteres hoje | alvo | poupado (car.) |
|---|---|---|---|
| `/opt/wiki/CLAUDE.md` | 41.868 | ~15.750 | **26.118** |
| `/home/rafael/.claude/CLAUDE.md` | 13.176 | ~10.500 | **2.676** |
| **soma** | **55.044** | **~26.250** | **28.794** |

| conversão | hoje | depois | **economia/sessão** |
|---|---|---|---|
| ÷ 4,0 (piso) | 13.761 | 6.562 | **7.199** |
| **÷ 3,5 (central)** | **15.727** | **7.500** | **8.227** |
| ÷ 3,0 (teto) | 18.348 | 8.750 | **9.598** |

**7.200 a 9.600 tokens por sessão, central 8.227** — **37%** do custo fixo de 22.358 tok
(incluindo o índice de memória, que este desenho não reduz).

### Quanto disso é procedimento que vira skill/command

Dos 26.118 caracteres que saem do `CLAUDE.md` do repo: **~11.400 car. (≈3.257 tok) são
procedimento puro** — §9 inteiro, a matriz do §6, os 5 procedimentos do §1, a validação
proporcional do §4, o `context-mode`, a coordenação do §11, o passo 2.6 do §7. Eles não
desaparecem: passam a custar **0 fixo** e ~600-900 tok **quando invocados** — e chegam mais
completos do que chegavam na prosa, porque o corpo da skill não disputa espaço com nada.

*(A primeira redação extrapolava isso para "tok/dia" supondo 5 sessões por dia e 1 invocação
por sessão. As duas eram **suposições, não medições**, e a conta saiu: o consumo real do dia
está em `ai-tokens --today` e não é decomposto por arquivo de contrato.)*

### O custo evitado, que é maior e não entra na conta fixa

A tabela do §2 pede 64.979 tok de leitura. Nenhuma sessão paga, e é por isso que não
funciona. A regra por caminho entrega ≤ 250 tok **no ato**, quando o arquivo é lido. Se uma sessão
toca 3 atos cobertos: **750 tok contra 64.979 pedidos** — e, ao contrário dos 64.979, os 750
efetivamente chegam. Isto é **mudança de obediência**, não economia, e por isso está
declarado fora do número principal.

### A ressalva que muda a conclusão: o custo fixo é pago em CACHE-READ

Medido nesta máquina hoje com `ai-tokens`: **cache-read é 97% do volume** de tokens
(623,5 M de cache-read contra 17 k de input em 2026-09-15, US$ 1.477,09 no dia; agentes
respondem por 47% do total). O `CLAUDE.md` vive no **prefixo cacheado** — é escrito uma vez e
lido como cache em cada turno seguinte. Então a economia de 8.227 tok **se multiplica pelo
número de turnos**, e não pelo de sessões: nesta sessão houve 158 chamadas de `Bash`, e
8.227 × ~158 turnos ≈ **1,3 M de tokens de cache-read poupados numa sessão só**.

**E ao mesmo tempo cache-read é o token barato** — é o próprio `ai-tokens` que registra isso
("token barato: quanto maior, melhor o reaproveitamento de contexto"). Portanto, e é preciso
dizer com clareza para não vender o que o desenho não entrega: **a economia de tokens é o
benefício SECUNDÁRIO desta reescrita.** O benefício primário é o que a §0 mediu — **três dos
cinco erros do dono aconteceram com a regra em contexto**, e cada um custou um ciclo de
correção repetida. Um ciclo desses gasta, em saída de modelo (o token caro), ordens de
grandeza mais do que os 8.227 de prefixo, além do tempo do dono, que não tem preço de tabela.
A ordem do dono pede as duas coisas — *"evitando retrabalho, gasto de tokens errado"* — e o
retrabalho é a parcela grande. Quem justificar esta frente só pelo número de tokens está
justificando pela metade menor.

### O que este desenho NÃO economiza

Os 6.631 tok do `MEMORY.md` e os 100.512 tok não carregados dos 166 arquivos linkados.
Esse *tier* é gerido pelo harness, não pelo repo. O que o desenho faz é **mover o conteúdo
que é ORDEM** — a começar por `dono-nao-revisa-paginas` — para hook, teste ou linha de
contrato, porque **ordem que mora só nesta máquina é ordem que a próxima sessão não tem**.
Depois dessa migração o índice pode ser podado, mas a economia daí é **não estimada**.

---

## 11. Os cinco erros do dono → o mecanismo que impede cada um

Este é o teste de aceitação. Se um destes ficar sem mecanismo, o desenho falhou.

| erro | mecanismo | por que agora não repete |
|---|---|---|
| Reabri o DataJud | §1 do contrato novo (1 linha de veredito, sem argumento) + **H6** injetando no ato | o texto que convidava a re-litigar sai; sobra a ordem. Reabrir passa a exigir contrariar uma linha imperativa, não escolher um lado de um argumento de 20 linhas |
| Inventei risco da OAB | §1 linha (c) + **H6** + **H7** (barra promessa de resultado de verdade) | separa o que é risco real (promessa, captação, preço) do que não é (conteúdo informativo). O risco fica nomeado; inventar exige contradizê-lo |
| Devolvi decisão 3× | **H11** (Stop, `decision: block` + razão, mecânica de `keep-working.sh`, com circuit-breaker) | a devolução não chega ao dono: volta ao modelo com a ordem de decidir. Não depende de lembrança |
| Medi tráfego na camada errada | **H10** (barra a contagem na camada de origem) + **`.claude/rules/medicao-de-audiencia.md`** (injeta as 4 linhas ao ler `data/ops/access/**`) + skill `medir-bots` | o gatilho passa a ser o ATO (`grep` no log de origem com termo de bot), não o tema ("medição") |
| "Revisão humana" como etapa | **H12** + §1 linha (d) + **renome de `reprovada_em_auditoria_humana` → `reprovada_por_auditor_agente`** | corrige a causa: o rótulo mentia sobre a própria origem. Sem o renome, o dado continua ensinando o erro a cada sessão nova |

---

## 12. Ordem de execução

Cada onda nasce do resultado medido da anterior. Nenhuma toca página publicada.

**Onda 1 — o teste e o instrumento, antes do texto** (sem isso a reescrita é irreversível).
Escrever `claude_md_operational_test.go` com T1-T4 contra o `CLAUDE.md` **atual** (T2 com o
teto em 44.000 B, o tamanho de hoje, para o teste nascer verde); `tools/check-modo-operacional`;
provar cada asserção **por mutação**. E ligar o hook **`InstructionsLoaded`** (matcher
`path_glob_match`) gravando em `data/ops/instructions_loaded.jsonl`: é ele que vai **medir**,
na onda 2, se a regra por caminho dispara de fato — e a doc só garante o disparo na
**leitura**, não em `Edit`/`Write` sem `Read` prévio. Commit leve.

**Onda 2 — mecanismo antes de remover prosa.** Os 11 hooks (H9 não existe mais) + as 6 regras
por caminho + as 8 skills novas, cada hook com bancada e caso de falso-positivo,
`--max-ms 300` verde. A bancada de H6 assevera o **aninhamento** de
`hookSpecificOutput.additionalContext`. Nota de aposentadoria datada em `keep-working.sh` e
nos outros 3 órfãos. Ler `data/ops/instructions_loaded.jsonl` e **confirmar por medição** que
as 6 regras dispararam nos atos previstos; regra que não dispara vira hook de `PreToolUse` com
`if`. Medir se as 12 descrições de skill sobrevivem inteiras no *listing* (teto de 1.536
caracteres) — e, se não sobreviverem, revisar o roster de `caveman` (21 das 43) antes de
consolidar skill do projeto. **Nenhuma linha do `CLAUDE.md` sai nesta onda** — só quando o mecanismo
substituto estiver no disco, testado e **medido disparando**.

**Onda 3 — a reescrita.** `CLAUDE.md` novo na estrutura da §3; §6 verbatim; baixar o teto de
T2 para 18.000 B **no mesmo commit** que encolhe o arquivo. Rodar
`peer_governance_test.go`, `engineering-now-contract`, `continuity_test.go` e o novo.

**Onda 4 — des-hardcodificação.** `internal/contentpolicy` com o 0.70 e o
`MinBodyWords`; os 8 pontos importando; `HTMLBudgetBytes` nos 3; a cerca do domínio no
`site_url_flexibility_test.go` com a triagem dos 47; `DefaultMainRoot`; `%h/go/bin` nas 4
units; o `ExecStart` do cloudflared. **Toca `go.mod`? Então a atestação vai no mesmo
commit** e sob `flock /tmp/opt-wiki-agent-heavy.lock`.

**Onda 5 — os fatos obsoletos.** Os 10 confirmados; o renome de
`reprovada_em_auditoria_humana` com migração e leitor tolerante por uma geração; resolver o
conflito interno do drop-in do Ollama medindo o RSS ao vivo; medir os 6 itens hoje
"não medidos" e, se obsoletos, corrigir.

---

## 13. O que o advisor mudou

Chamei o advisor depois da orientação e antes de escrever. Ele mudou cinco coisas, e a
primeira é a espinha do documento.

1. **Deu o diagnóstico que eu tinha em pedaços e não tinha somado.** Eu havia medido os
   tamanhos, os hooks e a tabela do §2; ele mandou mapear cada um dos cinco erros do dono
   **contra o lugar onde a regra vivia**. O resultado — **3 de 5 com a regra em contexto** —
   inverteu o desenho: sem isso eu teria escrito "mova para doc e crie gatilho", que para
   esses três **piora** (menos visibilidade). Daí saíram o destino **VEREDITO ADOTADO** (§0),
   a linha única do DataJud, o hook H6 e a §11 como teste de aceitação.
2. **Mandou medir hook com payload real, não `echo ok`.** Eu tinha 13-24 ms de caminho
   rápido e ia declarar isso como custo. Com `git commit -F`, `go-modern build` e um `Edit`
   em arquivo de 180 KB, o pior caso subiu para **77 ms** — número que muda o orçamento dos
   11 hooks novos. Também mandou ler `memory/custo-dos-hooks-claude-code.md` antes de citar
   o 13,97 s; foi de lá que veio a régua `--max-ms 300`, que já existe, e a constatação de
   que **o caro é `SessionStart`, não `PreToolUse`** — que é a razão pela qual nenhum hook
   deste desenho usa `SessionStart`.
3. **Não deixou o "não olhei" de um subagente virar "não há" no plano.** O agente do
   hardcoded devolveu `/home/rafael` (24 hits) e o domínio (301 arquivos) como "não
   aprofundei" — justamente os dois que o dono pediu. Fui atrás: **47 literais de runtime do
   domínio** e a descoberta de que `site_url_flexibility_test.go` **não varre o domínio**,
   só a identidade do advogado. Esse é o achado mais acionável da §7, e ele só existe porque
   o advisor mandou não herdar a lacuna. O mesmo valeu para `pisoEmentaPalavras`, que o
   agente não achou (buscou em `internal/` por valor) e que está em
   `cmd/generate-acordao-pages/main.go:402`.
4. **Corrigiu dois erros de desenho que eu ia cometer.** (a) Eu ia propor **JSON de config**
   para o 0.70; ele apontou `fiscalization.go:182` — *"o 0.70 é SEMANTICO e vive no
   model2vec"* — e a diferença entre **calibrado** e **configurável**: calibrado em JSON é
   valor que alguém muda sem recalibrar. Virou **uma constante Go + teste**. (b) Eu ia
   propor **atualizar** os números obsoletos; ele apontou que atualizar garante que estejam
   errados amanhã, e que o remédio é **removê-los** do contrato — daí a asserção **T4** e a
   ampliação da skill `estado-real`.
5. **Mandou ler os hooks órfãos antes de projetar do zero.** `keep-working.sh` já implementa
   `Stop` + `decision: block` + razão + circuit-breaker — é o protótipo de H11, e H11 passou
   a ser "reaproveitar a mecânica com escopo estreito" em vez de código novo.
   `sequential-agents.sh` deu o **padrão de aposentadoria** (data + causa medida + onde está
   o substituto) que virou asserção (b) do `check-modo-operacional`.

6. **Proibiu responder "padrão Anthropic" de memória** — e essa foi a exigência que mais mudou
   o documento, porque a documentação **contrariou três decisões minhas**. Lancei o
   `claude-code-guide` para confirmar em fonte oficial quais eventos injetam contexto, se
   skill é invocável como `/nome` e se `@import` é inlinado. O que voltou (§5 inteira é nova):
   - **`.claude/rules/*.md` com `paths:` existe e é nativo.** Meu H9 era um hook para
     reimplementar, pior, um mecanismo do harness. **H9 foi eliminado** e substituído por 6
     arquivos de regra por caminho, custo fixo zero, mais `CLAUDE.md` de subdiretório como
     alternativa. Esta é a resposta ao §4 da missão, e ela é melhor do que "criar um hook".
   - **`.claude/commands/` é formato legado**; o diretório de skill já é o comando. Meus 5
     slash commands **viraram skills**, e o diretório segue inexistente de propósito.
   - **`ask` não tem garantia de que a razão chegue ao modelo.** Cinco dos meus hooks usavam
     `ask` para ensinar — teriam pedido confirmação ao dono **sem ensinar nada ao modelo**,
     que é o erro #3 disfarçado de guarda. Todos passaram a emitir também
     `hookSpecificOutput.additionalContext`, que é garantido.
   - **O `Stop` já tem teto de 8 bloqueios e expõe `stop_hook_active`.** Meu
     *circuit-breaker* caseiro em H11 saiu: era a terceira cópia de um mecanismo existente —
     o mesmo antipadrão que a §7 condena no 0.70.
   - Confirmou o que eu supunha e permite parar de supor: `UserPromptSubmit` injeta contexto
     (H6 viável), `deny` devolve a razão ao modelo, hooks do mesmo evento rodam **em
     paralelo** (citação literal). E deixou explícito que *"custo = o do mais lento, não a
     soma"* é **inferência**, não frase da doc — a prova é a minha medição, e as duas ficam
     separadas no documento.
   - Dois brindes que entraram: comentário HTML de bloco no `CLAUDE.md` **não custa tokens**
     (nota para humano de graça), e existe o hook **`InstructionsLoaded`** com matcher
     `path_glob_match`, que é como se **mede** se as regras por caminho disparam de fato — em
     vez de confiar que disparam. Entrou na onda 1.

7. **Na segunda chamada, com o documento já no disco, achou seis defeitos INTERNOS** — e dois
   eram do tipo que este próprio documento condena nos outros:
   - **Contradição de contagem:** eu dizia "12 skills (5+7)" em dois lugares e "11 skills
     novas" num terceiro, e a lista real tinha 9. Pior: o teto de "12" era **inventado**,
     escrito duas linhas depois de eu citar a doc sobre descrições que se perdem. Fui medir o
     listing **desta sessão**: **43 skills, 21 do `caveman` (49%), 5 do repo (12%)** — a
     alavanca nunca foi o projeto. Agora são 8 skills novas (com `deploy-binario` e
     `deploy-decidir` fundidas, porque são um ato só) e o teto virou **medição na onda 2**.
   - **Eu absolvi dois itens que o dono havia medido, sem medir.** Em `coleta.go:29` meu
     subagente viu data no comentário e escreveu "CONFIRMADO CORRETO"; medido, o maior arquivo
     mensal tem **26.704.470 B** contra os 360.619 do comentário — **74×**, e a folga que
     justifica a constante de 64 MB deixou de existir (o arquivo real é 40% do teto, não 0,5%).
     Em `semantica.go:12` eu medi **a população errada** (11.106 do `published_manifest` em vez
     dos embeddings): o certo é `paginas = 11118` em `data/ai/embeddings/ativo.json`, 45,5 MB
     calculados e **49,7 MB no disco** contra os 41,5 do comentário. Aplicar o princípio
     "comentário datado não é obsolescência" **sem medir** foi usar uma regra boa para absolver
     o que o dono apontou — e "medir a coisa ao lado" é defeito que este repo já catalogou.
   - **"Localizada" em vez de "não localizei":** a unit do `ExecStartPre` é
     `wikijuridica-daily-content.service` (a linha 7 afirma o mecanismo; a unit **não tem**
     `ExecStartPre=`, e só 4 units no repo têm). A primeira busca falhou por procurar o
     **apelido** ("onda") e não a **função**.
   - **Órfãos: 4, não 5.** `git-guard-prune.py` é auxiliar chamado por `git-guard.sh` — e a
     asserção que eu havia escrito o reprovaria como hook morto. O falso positivo entrou na
     bancada.
   - **T4 ia reprovar o texto que existe para proteger:** `\d{1,3}\.\d{3}` casa
     `Lei 9.610/98` e `art. 1.022`, que o §1 do contrato novo cita. Entrou a lista de isenções
     de citação legal e um caso negativo obrigatório na prova por mutação.
   - **E a correção mais importante de todas, que muda a CONCLUSÃO:** mandou confrontar a
     economia com o consumo real. `ai-tokens` mostra **cache-read em 97% do volume** — o
     `CLAUDE.md` é prefixo cacheado, então os 8.227 tok se multiplicam pelos **turnos** (~1,3 M
     numa sessão de 158 chamadas de `Bash`) **e ao mesmo tempo são o token barato**. Isso
     rebaixa a economia de tokens a benefício **secundário** e promove o que a §0 mediu — três
     erros com a regra em contexto — a benefício primário. Vender esta frente pelo número de
     tokens seria vendê-la pela metade menor, e a §10 agora diz isso com letras.

**Verificação de mecanismo, para não deixar o pivô no ar:** `claude --version` devolve
**2.1.268**, que é exatamente o `minimumVersion` declarado em `~/.claude/settings.json`. A
versão satisfaz o mínimo, mas **versão não prova suporte a `paths:` no frontmatter** — por isso
a onda 1 liga o `InstructionsLoaded` e a onda 2 só remove a prosa depois de **ver a regra
disparar** em `data/ops/instructions_loaded.jsonl`. Regra que não dispara vira hook de
`PreToolUse` com `if`, e isso está escrito na ordem de execução.

Onde a documentação contrariar este desenho, vence a documentação; onde ela se contradizer
(o caso de `additionalContext` em `Stop`/`SubagentStop`), vence o teste empírico na versão
instalada, e o desenho não depende do campo em disputa.

---

## 14. O que NÃO foi medido — declarado

- Tokens **reais**: toda contagem é caracteres ÷ 3,5 com intervalo ÷4,0-÷3,0. Sem tokenizador
  local; `count_tokens` exigiria credencial de API, vedada.
- Confronto **linha a linha** das 23.926 B de skills contra os 41.868 car. do `CLAUDE.md`:
  fiz busca por frases-chave (amostra), não varredura completa. Nenhuma duplicação achada —
  *ausência em amostra não é ausência na população*.
- As ~30 funções de `internal/contract/misc/continuity_test.go` (152.866 B) e
  `checkmeta/check_wrappers_test.go` (306.000 B): confirmei os caminhos de documento por
  grep, não transcrevi cada substring exigida.
- Os ~40 `tools/*` que citam `CLAUDE.md`/`AGENTS.md`: localizados por grep; **não** abri cada
  um para saber quais cobram substring de verdade. Pode haver trava de documento que esta
  auditoria não listou.
- Os 86 arquivos com `/tmp/` literal e os 301 que citam o domínio (fora dos 47 `.go` de
  runtime que triei): contados, não triados.
- Os 6 itens numéricos da §8 marcados "não medido", e a unit do `ExecStartPre`, que não
  localizei.
- O **custo de execução** das ondas 1-5: não estimado em tokens nem em tempo.

---

*Auditoria em modo somente leitura, 2026-09-15. Nada editado, commitado ou publicado neste
repositório — a única escrita foi este arquivo, em
`/home/rafael/.claude/plans/pure-imagining-cerf-agente-modo-operacional.md`.*
