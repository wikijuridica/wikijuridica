# Tasklist — execução do plano de ferramental e descoberta (2026-08-19)

Plano aprovado: `~/.claude/plans/recursive-churning-sutherland.md`; versão longa em
`docs/goal/PLANO_FERRAMENTAL_E_DESCOBERTA_20260819.md`. Evidências em
`.agents/runtime/investigacao-20260819/` (lanes 1-9).

Estados: `pendente` · `fazendo` · `feito` · `bloqueado`. Toda task tem TESTE — sem teste
verificado, não vira `feito`.

## Bloco 0 — perecível

| id | task | estado | teste | quando |
|---|---|---|---|---|
| 0.1 | rodar cobertura dos 10 crawlers antes de a janela de 8 dias fechar | **feito** | `crawl_coverage_daily.jsonl`: 10 crawlers com data 2026-08-19 ✔ (80 registros, `last_updated` 11:00Z) | 2026-08-19 |
| 0.2 | materializar lane8 (red-team) e lane9 (consistência) no repo | **feito** | os dois arquivos existem em `.agents/runtime/investigacao-20260819/` ✔ | 2026-08-19 |
| 0.3 | atualizar o plano longo do repo com as 4 correções e os dados frescos | **feito** | nenhuma ocorrência de "104 páginas prontas" como AÇÃO (as 3 restantes são registro da correção) ✔ | 2026-08-19 |

## Bloco A — ferramental

| id | task | estado | teste |
|---|---|---|---|
| A.1 | adicionar marketplace oficial `claude-plugins-official` | **feito** | `marketplace list` mostra `claude-plugins-official` ✔ |
| A.2 | `details` + ler o código de cada | **feito** | gopls-lsp = só README+LICENSE Apache-2.0, zero código; session-report = zero rede, zero child_process, só lê transcripts. Custo real: ~0 e ~70 tok ✔ |
| A.3 | instalar `gopls-lsp` com `--scope project` | **feito** (teste funcional na próxima sessão) | instalado, enabled, scope project; `details` confirma 0 tok, LSP out-of-process ✔ |
| A.4 | instalar `session-report` com `--scope project` | **feito** (teste funcional na próxima sessão) | instalado, enabled, scope project; ~70 tok always-on ✔ |
| A.5 | desativar os 72 conectores MCP (2 formatos) | **feito** (teste estrutural) | 151 entradas = 7 + 144; nenhum dos 5 mantidos desativado; nenhum dos 75 faltando ✔. `claude -p` não carrega conector claude.ai, então o teste funcional é na próxima sessão interativa |

## Bloco B — descoberta e citação por IA

| id | task | estado | teste |
|---|---|---|---|
| B.1 | estender `ExecStart` do unit de cobertura aos 10 crawlers | **feito** | `systemctl start` exit 0, gravou **80 registros** (10 crawlers × 8 dias) contra 8 antes ✔ |
| B.2 | criar `wikijuridica-ai-citation.{service,timer}` | **feito** | timer ativo (próximo disparo em 3h); `--gravar` recuperou **+58 registros**, cursor 12/08 → 19/08 ✔ |
| B.3 | destino do `generate-indexnow-incremental-submit` | **feito — fica dormente de propósito** | verificado: `deploy-publico:454` (`--purge-targets`) + `:689` (`direct-submit --de-arquivo`) já selecionam pelo **mesmo** `content_sha256` da mesma fonte. Ligar os dois causaria submissão dupla — o 403 que o repo já levou. Documentado no cabeçalho da ferramenta ✔ |
| B.4 | destravar os 57 tombstones de catálogo | **medido: o gerador não tem o que fazer** | dry-run próprio: `already_in_catalog: 1336`, `pending: 0`, `resolved_added: 0` — já rodou em 07/08. O bloqueio é o **pin antigo da fila**; 27 intents destraváveis por re-pin. Sob crítica do Fable antes de executar |
| B.5 | extensão da allowlist a fonte oficial estrangeira | **fora de escopo desta sessão** (ordem do dono: foco em engenharia) |
| B.6 | grafo interno: linkagem por entidade em `internal/render` | pendente | distribuição de links no `<main>` sai de p10=p90=7; nenhuma página > 50 KB |
| B.7 | `lastmod` dos 28 shards | **refutado — nada a corrigir** | o `lastmod` de 06/08 é o sinal HONESTO: bate com o máximo das URLs de cada shard (30/31 exato), 9.160 HTMLs têm mtime 05/08 e os dois detectores sancionados passam. Carimbar 13/08 seria o date-bumping que `check-lastmod-por-evento` existe para barrar |
| B.8 | reconciliar FAQPage e backfill de JSON-LD | **fora de escopo desta sessão** (ordem do dono: foco em engenharia) |
| B.9 | corrigir 2 titles de 69 chars e 1 description de 167 | **feito na fonte** (republicação pendente) | gerador datado novo; medido no dado: 64, 59 e 147 ✔; unicidade conferida contra 9.930 titles/metas. `public/` ainda serve o antigo até republicar |

## Bloco C — engenharia

| id | task | estado | teste |
|---|---|---|---|
| C.1 | partição do boot fail-closed | **feito** | `TestBootPartition*` verde (0,016s): artefato estático não bloqueia, estrutural continua fatal, volume volta a ser fatal, e `Messages()` não esconde nada — o check segue vermelho ✔ |
| C.2 | zerar untracked de produto | **feito** | exit **0**: `untracked_produto_stale=0`, `ignored_sensitive_failures=0`. 2.099 arquivos / 197 MB commitados; 12 sensíveis classificados com sha256 ✔ |
| C.3 | consertar teste vermelho de `internal/checks` | **feito** | `ok portaljuridico/internal/checks **1,758s**` sob `-race`, exit 0 — antes morria por SIGTERM aos 532 s. Causa: o teste usava o repo REAL onde o próprio cabeçalho prometia root inválido ✔ |
| C.4 | ADRs de dependência de runtime | **feito** | **5 ADRs** (os 3 clientes de sidecar são um adapter só), versão do `go.mod` e licença lida em disco. Só `jsonschema/v6` é runtime de produção ✔ + **2 achados P0 de evidência literal** |
| C.5 | CSS externo cacheável | pendente | mediana de `<style>` < 2.000 B, nenhuma > 50 KB, smoke verde |
| C.6 | commitar as 20 publicações só-worktree | **feito** (ledger de 160 MB pendente) | HEAD passou de 9.690 para **9.710** linhas; as 20 têm HTML em `public/`, nenhuma órfã ✔ |

## Bloco D — skills

| id | task | estado | teste |
|---|---|---|---|
| D.1 | criar as 5 skills em `.claude/skills/` | **feito** | `validate --strict` exit **0** (conferido por mim) e as 5 aparecem carregadas nesta sessão ✔ |
| D.2 | teste comportamental por skill | **feito** | `claude -p` escolheu `medir-bots` sozinha e respondeu **0** (saneado), citando `serie_saneada()` e explicando que o cru diz 2.008 por 10 linhas descartadas ✔ |
| D.3 | testar o campo `skills:` de pré-carga em agente | **feito — funciona** | agente de teste com `skills: [medir-bots]` respondeu `SKILL PRE-CARREGADA: SIM`. Deixa de ser documentação não verificada ✔ |
| D.4 | reescrever `cowork-opus-fleet-factory` | **feito** | bootstrap com fallback e falha alta; commit obrigatório; gatilho mede páginas/registros/shards separados; escopo vem da tasklist datada ✔ |
| D.5 | corrigir `cowork-fable-goal-loop` | **feito** | as 5: bootstrap com fallback · fila hardcoded → fonte viva · lock unificado em 30 min · guarda de atualidade do contrato · rota da VM removida ✔ |

## Bloco E — contratos que mentem

| id | task | estado | teste |
|---|---|---|---|
| E.1 | corrigir CLAUDE.md | **feito** | `check-contrato-vs-medicao` exit 0; contrato declara 9.710 e o manifest mede 9.710 ✔ |
| E.2 | corrigir `docs/goal/PROJECT_GAPS.md:11` | **feito** | item 1 marcado RESOLVIDO com a medição; redação original preservada como registro histórico ✔ |
| E.3 | campo de data obrigatório no frontboard | **feito** | **73/73 com `opened_at`**, recuperado do git (primeiro commit em que cada id aparece), não inventado ✔. Revelou 33 tasks abertas há mais de 4 semanas e nenhuma nova desde 04/08 |
| E.4 | criar `tools/check-contrato-vs-medicao` + pre-commit | **feito** | testado nos dois sentidos: exit **0** no contrato corrigido, exit **1** no anterior (aponta linha 72, 3 razões), sem falso positivo no registro histórico. Ancorado no pre-commit ✔ |

## Bloco F — retomar publicação

| id | task | estado | teste |
|---|---|---|---|
| F.1 | recuperar corpos redigidos presos em tombstone | **fora de escopo desta sessão** (ordem do dono: já há conteúdo suficiente em produção; foco em engenharia) — registrado: **23 dos 30 aprovados têm rascunho recuperável, 20.243 palavras**, em `data/editorial/v2_recovered_drafts_20260728/recovered_pages.jsonl`. Armadilha anotada: a chave de topo `sections` é um **int** de contagem e `word_count` é 0 — o texto vive em `page.*` |
| F.2 | gerar lote sobre os intents destravados | **fora de escopo desta sessão** (mesma ordem) |

## Bugs de engenharia, infra e gates — os 14 (plano aprovado 2026-08-19)

Três varreduras precederam a correção: família de evidência fabricada, gates falso-verdes e
infra/produção. **Resultado que reduziu o escopo**: evidência fabricada **não é família** (85
candidatos, 22 lidos no código, só as 2 conhecidas são reais) e o falso-verde clássico (glob
vazio, caminho morto) **não existe aqui** (838 caminhos e 23 globs testados, zero vazio). Em
compensação, a varredura achou algo pior que os quatro originais — o X.14.

Laudos: `lane15-familia-evidencia-fabricada.md`, `lane16-gates-falso-verde.md`,
`lane17-infra-producao.md`.

| id | achado | sev | estado |
|---|---|---|---|
| X.14 | **journal órfão travava a família de gates v2 há 6 dias** | **crítica** | **RESOLVIDO** — finalização pinada: `recovered=true`, `disposition=fully_desired`, `publication=false`, journal consumido. `v2-writing-semantic-contract` saiu de exit 1 (`transaction in progress`) para **pass**; `v2-public-path-collision` pass. Prova de não-regressão: `stock_manifest`, `published_manifest` e `pages.json` byte a byte idênticos ✔ |
| X.1 | `crawleridentity` fabrica evidência de DNS; `ValidateRecord:561` **exige** o `true` fabricado. Campos não saem do pacote, mas `LoadVerifiedIdentity→ValidateRecord` alimenta `publicrelease`/`crawlsmoke` — zerar trava P4 | **crítica** | fila (após X.14) |
| X.12 | **1.753 páginas no ar (18%) fora do gate de ética OAB e do anti-template** | alta | fila |
| X.3 | suíte de `internal/httpserver` não cabia em 540 s | alta | **RESOLVIDO** — `test -short` em **0,271 s** (39 rodam, 65 pulam, 0 falham), 17 guardas, 51 inserções e **0 remoções**. Causa medida: 1 teste de acervo real = 9,34 s; 65 × 9,3 ≈ 605 s > 540 s — aritmética, não ambiente ✔ |
| X.2 | `searchbackendbench` grava `IndexBuilt/p95` literais nos 3 go-clients (6 de 9 medem de verdade). Check **já vermelho** por staleness; nenhum consumidor externo lê os campos | alta | fila (depende de X.10) |
| X.11 | `superseded-absent-from-sitemap` verde permanente: `if superseded == 0 { return nil }` e **nenhum gerador escreve esse status** | média | fila |
| X.10 | binários OSS (`tantivy`, `sonic`, `quickwit`) moram em `/tmp`, que o systemd apaga no boot — raiz em `ossinstallmatrix/matrix.go:1955` | média | fila |
| X.5 | código morto que fabrica SHA de promoção (`publicsnapshot:2005-2053`); 3 funções chamadoras com **zero** referências | média-baixa | **em execução** |
| X.13 | `source-claim-graph` roda sobre corpus com **interseção zero** com as 9.710 publicadas | média | fila |
| X.4 | revival: `RevivalRefused` nunca capturada (1ª recusa aborta o lote), snapshot congelado antes do laço, `revert` impossível com shard vazio | média | **em execução** |
| X.7 | `generate-bot-traffic-origin`: cursor avança, dado zero (borda em ~100% HIT). Sensor certo, legibilidade errada | média | fila |
| X.8 | aquecimento de borda mede o instante, não cobertura entre ciclos (`hit: 9968` lido como cobertura) | média | fila |
| X.6 | três campos com nome que afirma mais que o código (um deles torna o validador **tautológico**) | baixa | **em execução** |
| X.9 | `tools/measure-uplink-throughput` sem gatilho | baixa | **em execução** |

**Confirmado correto, não mexer**: coerência de artefato (amostra de 300 páginas com `html_sha256`
byte a byte), regra `utm_*` na origem e na borda, watchdogs bem guardados, 9 dos 11 timers movendo
seu artefato, e ausência de arquivo virando issue vermelha (nunca pass) em `crawler-error-budget`,
`prioritymanifesttransaction` e `scaleindex`.

### X.15 — o grafo do DADO EDITORIAL está quebrado (ALTA — bloqueia publicação nova)

**Correção de rota, feita antes de virar trabalho errado.** Quando o X.14 destravou o gate
`v2-internal-link-graph-topology`, ele acusou "9.536 de 9.712 páginas inalcançáveis a partir dos
hubs" e eu registrei isso como gargalo de descoberta do portal. **Fui medir o HTML servido e é
falso para produção.**

Medição própria sobre os 9.929 arquivos de `public/`, seguindo apenas `href` dentro de `<main>`
(sem menu nem rodapé), BFS a partir da home:

| profundidade | páginas |
|---|---|
| 0 (home) | 1 |
| 1 | 36 |
| 2 | 1.601 |
| 3 | 8.290 |
| **alcançáveis** | **9.928 de 9.929 (100,0%)** |
| **inalcançáveis** | **1** |

O crawler que entra pela home alcança o acervo inteiro em **no máximo 3 saltos**. O rótulo do
próprio gate dizia onde eu deveria ter olhado: `escopo=editorial_internal_link_topics_only,
publication_evidence=false` — ele mede o grafo do **dado editorial**, não o do HTML publicado.

**O defeito é real, mas é outro, e o impacto é outro**: os `internal_link_topics` do estoque têm
3.473 páginas sem link de entrada e 11.775 tópicos pendurados. Isso **não afeta o que está no ar**;
afeta **publicação nova**, porque o gate diz "corrigir a conectividade interna antes de promover"
— ou seja, trava a promoção do próximo lote.

**E desfaz a conexão que eu tinha afirmado**: o gap de descoberta por IA (3.793 URLs nunca tocadas)
**não** se explica por alcançabilidade, já que em produção ela é 100%. A causa daquele gap continua
sendo a do plano original — os bots que citam (Bing 0,7%, Perplexity 0%) simplesmente rastreiam
pouco, e o grafo raso (mediana 7 links, p10=p90=7) reduz o *incentivo* de rastreio, não a
possibilidade.

`v2-stock-freshness` também voltou vermelho (`validation_as_of: receipt=2026-08-13
required=2026-08-19`), consequência direta de não haver publicação desde 13/08.

## Bloco D — superfície de agente (aberto em 2026-08-19, tarde)

Frente nascida de uma correção do dono: *"o markdown tá escrito errado... quando eu vejo no
sistema 'is your agent ready' da cloudflare, diz que não tem negociação, e que tem algo nomeado
errado"*. A investigação confirmou o apontamento e derrubou duas hipóteses minhas pelo caminho
(o robots está correto; a borda respeita `Vary: Accept` mesmo sob HIT — medido com cache quente).

**Critério oficial** (blog.cloudflare.com/agent-readiness): Discoverability (robots, sitemap, Link
headers RFC 8288) · Content (Markdown for Agents) · Bot Access Control (Content Signals, regras de
IA no robots, Web Bot Auth) · Capabilities (Agent Skills, API Catalog RFC 9727, OAuth discovery
RFC 8414/9728, **MCP Server Card**, WebMCP). O checker sonda 6 endereços, 3 deles na raiz.

| id | task | estado | teste |
|---|---|---|---|
| D.1 | `/.well-known/mcp/server-card.json` — servidor MCP existia e era indescobrível (404 medido) | **feito** | 4 casos do card + 1 do catálogo, EXIT=0; não-regressão dos descritores EXIT=0. Commit `753ee50a` |
| D.2 | `service-desc` do `/mcp` apontava para busca no registry de TERCEIRO; agora aponta o card local | **feito** | teste reprova se `registry.modelcontextprotocol.io` voltar ao catálogo ✔ |
| D.3 | identidade do MCP em constantes compartilhadas (literal repetido deixaria o card envelhecer mudo) | **feito** | teste amarra título e versão do card à `Implementation` ✔ |
| D.4 | índice estrutural em Markdown para a home e os 29 hubs — a promessa do `llms.txt` era FALSA nas duas | **feito** | `internal/ondemand` EXIT=0: home lista áreas com contagem, hub lista **todos** os 60 membros (não a fatia de 50), rota desconhecida e página de conteúdo recusadas |
| D.5 | verificar em produção após deploy que `/index.md` e `/{área}/index.md` respondem 200 | **feito** | deploy 14:43. Origem e **borda**: `/index.md` 5.924B · `/administrativo/index.md` 7.178B · `/trabalhista/index.md` **72.468B** (cauda inteira da área) · server-card 448B · api-catalog aponta o card local. Promessa do llms.txt: **5/5 em 200, zero falhas**. `check-http-smoke` pass, 9.710 páginas. Site público nunca caiu (nginx serve estático) |
| D.10 | bug introduzido por D.4: a raiz entregava 328 bytes de esqueleto | **feito** | achado pelo `advisor` ANTES do deploy — o defeito nunca serviu requisição real. Porta de entrada passou a entregar corpo curado **+** mapa; teste no nível do Server com piso de 400 bytes. Commit `b57bb1f9` |
| D.6 | Content Signals no robots.txt | **feito** (já estava, por outra frente) | medido na borda: **32 ocorrências** de `Content-Signal: search=yes, ai-input=yes`, uma por grupo de User-agent — repetição deliberada, porque pela RFC 9309 §2.2.1 o crawler lê UM grupo e não cai para `*`. Minha leitura inicial de "ausente" veio de cópia do robots baixada no início da sessão, antes da regeneração: **medir o artefato servido, não a cópia local**. `ai-train` fica sem declaração de propósito — o controle real é o rate limit dos 8 `training_bot`, e declarar preferência sobre treino é decisão do dono, não derivável do código |
| D.7 | negociação por `Accept` na home e nos hubs | **bloqueado** | inerte enquanto essas URLs saem do DISCO pelo nginx; exige mapa nginx + confirmar `expression` da Cache Rule. Crítico Fable: precondição não verificada |
| D.8 | aliases `application/markdown` / `text/x-markdown` | **descartado** | crítico Fable, com evidência: inerte no Go (regex do nginx não casa) ou ENVENENA a borda (allowlist da Cache Rule normaliza para `text/markdown`; alias cairia na chave da variante HTML e serviria markdown a humanos por até 7 dias). Zero demanda medida |
| D.9 | comentário stale em `httpserver.go` afirmando que os 29 hubs são servidos pelo Go | **feito** | medido por mim, não aceito do subagente: `/administrativo/` com e sem query devolve `Server: nginx` e ETag do nginx, zero headers do Go. Comentário corrigido com a medição escrita |

**Medições que sustentam o bloco** (2026-08-19, contra o portal no ar):

- Cobertura por bot que cita, via `verifiedBotCategory` (não por UA, que é contaminado por sonda
  própria — o ledger bruto atribuía 2.008 requisições ao PerplexityBot, e a série saneada mostra
  **zero** verificado): perplexitybot 0 · claude-searchbot 1 · chatgpt-user 157 · oai-searchbot 448
  · bingbot 474 · googlebot 9.404 · yandexbot 10.218 · claudebot 43.484 (treino, não citação).
- Quarentena da telemetria de borda tem 7 registros por extrapolação absurda — um deles yandexbot
  com `requests_estimated = 1.000.002.640.524`. **Ler o ledger bruto é armadilha; o leitor canônico
  é `serie_saneada`.**
- IndexNow: 9.906 URLs submetidas ao endpoint direto do Bing (8 lotes, HTTP 200) e 445 ao do
  Yandex (HTTP 202). Perplexity e OpenAI **não participam do protocolo** — para eles o canal é
  crawl e descoberta, que é o que este bloco endereça.

## Bloco E — o que a verificação de hoje achou e onde cada coisa parou (14:5x)

| id | achado | estado | evidência |
|---|---|---|---|
| E.1 | **binário no ar era de 13/08 — 54 commits atrás**; tudo que a sessão corrigia existia no git e não para o bot | **feito** | deploy com backup, rename atômico, pré-voo (morreu em `bind: address already in use`, provando que a validação fail-closed passou antes do bind). `vcs.revision` do binário no ar = commit servido |
| E.2 | `Content-Signal` correto no código e ausente no ar: `content/crawl_policy.json` tinha **zero** declarações em 32 bots (campo é `omitempty`) | **feito** | 32/32 grupos com o sinal, verificado **através da borda** após purga. `ai-train` deliberadamente omitido — ausência é "sem preferência expressa", e licença de treino é decisão do dono |
| E.3 | `public/robots.txt` (disco) vencia o renderizador; gate `check-public-robots-drift` **existia e estava vermelho**, ninguém o rodava | **feito** | regravado a partir do renderizador; escrevi só porque o sha256 bateu com o esperado pelo gate. `pass required_bots=32 EXIT=0` |
| E.4 | as 3 rotas de agente respondiam 404 na borda | **feito** | server-card 200 · `/index.md` 200 (5,9 KB) · `/administrativo/index.md` 200 (7,2 KB) · `/familia/index.md` 200 (**59 KB**, área inteira com a cauda que o HTML paginava) |
| E.5 | caminhos: errei `wikijuridica-portal.service` (não existe) e `./server` (existe, mas é outro arquivo, de 04/08) | **feito** | `docs/ARQUITETURA_FIEL.md` §3.9, com coluna "como CONFIRMAR" e âncoras por símbolo. O gate reprovou na 1ª execução (ancorei um símbolo no wrapper `tools/` quando ele vive em `internal/checks/checks.go`) |
| E.6 | **2 páginas no ar violam o contrato de HTML leve**: title 69>65 nas duas, meta 167>160 numa | **corrigido no estoque, NÃO promovido** | `generate-v2-title-meta-length-repair-20260819` existia e nunca fora executado; rodei e o v2 já está conforme (64 e 59 chars). Mas o gerador declara: *"NÃO REPUBLICA — enquanto `cmd/publish-v2-direct` não rodar, `public/` segue servindo o texto antigo"* |

**E.6 — por que parei antes de promover, e o que falta exatamente.** `cmd/publish-v2-direct`
(`main.go:138-144`) expõe `-root`, `-allow-public-write`, `-limit N`, `-published-at`,
`-reviewed-at`, `-mesh-report` — e **nenhum seletor de página**. Não há como pedir "promova
apenas estes 2 `intent_id`". Disparar a transação sem alvo, sobre um acervo de 9.710 páginas
publicadas, para corrigir dois títulos 4 caracteres acima do limite, é raio de explosão que eu
não medi — e o contrato manda medir antes, não depois. Os dois `intent_id` são
`suc-holding-imovel-rural-georreferenciamento` e `trib-aduana-drawback-isencao-reposicao-estoque`.
Enquanto não promover, 2 testes de `internal/checks` seguem vermelhos por **conteúdo real**, não
por defeito de código — e é assim que devem ficar: o gate está certo.

**Falhas de `internal/checks` medidas e classificadas** (suíte completa: 702,5 s, EXIT=1, 6 falhas,
nenhuma no diff dos gates): 2 são o E.6 acima (conteúdo), 3 são o oráculo de robots discordando em
URL com query string (rede/terceiro), 1 é `permission denied` em `var/nginx/body` (ambiente).
Os testes dos gates tocados, isolados: **EXIT=0, 1,762 s**.
