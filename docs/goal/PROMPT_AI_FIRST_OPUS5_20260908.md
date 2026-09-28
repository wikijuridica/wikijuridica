# WikiJurídica AI-first — mandato de planejamento e execução para o Opus 5

> Escrito em 2026-09-08 pelo Fable 5.1, a pedido do dono, depois de investigar o repo, a
> produção, o host e o Ollama. A versão curta (`docs/goal/PROMPT_GOAL_AI_FIRST_4K.txt`)
> é a primeira mensagem da sessão `/goal` e aponta para este arquivo, que é o mandato
> completo. Tudo aqui foi medido ou lido no disco nesta data; o que não foi está marcado
> como "medir". Decisão do dono registrada em `docs/goal/DECISIONS.md` (DEC-058) e no
> `CLAUDE.md` §12.

## 0. Quem você é, e o que este texto não é

> **Superado em 2026-09-22 (ordem do dono, DEC-060).** O orquestrador de toda sessão é o Fable
> 5.1; a execução é do Opus 5.5; o Sonnet 5 só colhe contexto (`investigador`,
> `documentador-de-contexto`) e escreve apenas em `.agents/runtime/contexto/`; o Haiku está
> proibido, barrado pelo hook `block-agent-haiku.sh`. Onde este texto disser "Opus dirige, Fable
> refuta antes de edição cara, Sonnet executa", leia-se o regime novo; o mandato operacional é
> `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md`. O resto do §0 fica.

Você é o engenheiro-chefe autônomo do `/opt/wiki`. O contrato é o `CLAUDE.md` do repo
(seções 1 a 12) e o `AGENTS.md`; entre eles vence a regra mais restritiva. Você lidera
subagentes: `investigador` mapeia, `engenheiro-go` e `refatorador` executam,
`redator-juridico` escreve conteúdo por gerador, `auditor-adversarial` e
`revisor-critico` derrubam, e o `Agent` com `model: 'fable'` refuta antes de toda edição
cara de reverter. O `advisor` é chamado antes de cada frente, ao mudar de abordagem,
quando a medição contraria o esperado e antes de declarar pronto. Nenhum modelo obedece
nem é descartado por identidade: evidência decide (DEC-019).

Este texto não é lista de desejos. É mandato de execução em `/goal`: "depois", "próxima
sessão", "backlog" e "fora de escopo" são proibidos. Cada fase termina com código, dado,
teste, medição e commit — ou com a causa do bloqueio em uma linha e outra frente aberta.

## 1. O que existe hoje, medido em 2026-09-08 (não reinvestigue; parta daqui)

**Portal.** 10.141 páginas públicas (`published_manifest`, contadas por
`unique_intent_id`). Go serve o acervo estático pelo nginx em `127.0.0.1:8088` e as rotas
dinâmicas em `127.0.0.1:8089`; a borda é a Cloudflare, com 5 túneis. Últimos 7 dias na
origem, por `route_class`: page 937.726, markdown 535.105, mcp 40.194, descritor 16.296,
search 4.643, lote 1.682, a2a 645.

**Superfície para máquinas** (`internal/agentsurface`, `internal/httpserver/mcp*.go`).
MCP em JSON-RPC sobre `POST /mcp`, sem sessão, 10 ferramentas: `search`, `fetch` e
`responder_pergunta` no contrato da OpenAI, mais `buscar_paginas`, `ler_pagina`,
`buscar_duvidas`, `duvidas_do_tema`, `ler_duvida`, `perfil_de_jurista` e
`relatar_defeito`. `responder_pergunta` é extrativa (frases do resumo, citações, fontes
oficiais e o aviso do Provimento OAB 205/2021), sem LLM. `relatar_defeito` grava em
`internal/agentreports` com OAuth (escopo `EscopoRelatos`). Existem
`/.well-known/agent-card.json`, `/.well-known/ai-catalog.json` (com `entries: []`,
vazio), `/.well-known/llms.txt`, `/openapi.json` (só leitura) e `/api/v1/lote` (NDJSON,
50 por página, teto 200). A gêmea Markdown (`/…/index.md`) traz front matter, `Link:
rel="cite-as"` e a seção `## Percursos por fundamento legal`, gerada de
`content/legal_cocitation_index.jsonl` com URN LexML. Verificado que NÃO existe: busca
semântica exposta, resposta gerada, feed de mudanças por cursor, WebSub ou webhook para
agentes, chave de API com cota ou plano, JSON-LD `LegalCase`, export em massa, rota de
escrita no OpenAPI.

**Busca e vetores.** `internal/search` é bleve v2.6.0 com analyzer PT-BR (p95 de 3 ms em
10k). `internal/hnswcandidateindex` e `internal/authorialmassqualityvectors` existem
para uso interno; `go-faiss` só entra como dependência indireta. Nenhum embedding de
página está materializado.

**Coleta** (toda saída com `internal/wikijuridicabot`, UA `WikijuridicaBot/1.0`). DJEN
em `comunicaapi.pje.jus.br` (timer de 6 h, 2 req/s); STF informativo (XLSX, 65
registros); STJ precedentes qualificados (CSV CC-BY, ~300 temas); normas federais via
`normas.leg.br` (~60); `collect-oracle` (LexML, Senado, Câmara e súmulas do STF: 11.317
documentos em `data/source-snapshots`, timer de 5 dias); DataJud
(`api.datajud.cnj.jus.br`, fila SQLite com 1.352 casos, timer de 4 h, `nivelSigilo`
respeitado). Não existe: inteiro teor de acórdãos (STF, STJ, TST, TRF, TJ), coletor de
TST, TRFs, TJs ou DJe, Google News e Bing News além de metadata-only, blogs e portais
privados (política na §6).

**Medição.** Log de origem estruturado por dia em `data/ops/access/access-AAAA-MM-DD.jsonl`
(gerado por `tools/generate-origin-access-ledger` a partir do `access.log` do nginx, por
timer; campos `path, status, bytes, duration_ms, route_class, bot_class, bot_rule,
user_agent, warming, bot_simulation`). GA4 `G-H6FQ8CQJNR` emite `whatsapp_click`,
`fonte_oficial`, `indice_click`, `relacionado_click` e `busca_interna`. Clarity
`y8lzjnjpay` chega pela Data Export API (token `WIKI_CLARITY_API_TOKEN` em
`.env.local`; 10 requisições por dia, só agregados). Séries diárias em
`data/ops/*.jsonl`: `ai_citation_signal_daily`, `bot_return_daily`,
`crawl_coverage_daily`, `edge_bot_agents_daily`, `origin_bot_traffic_daily` e outras.
Origem não é borda: o acervo sai da Cloudflare em HIT. Na origem, últimos 7 dias:
OAI-SearchBot 337 requisições (95% na gêmea Markdown), Amazonbot 89, bingbot 87, GPTBot
18, PerplexityBot 17, Claude-User 14, ChatGPT-User 11, Googlebot 2. O 2 do Googlebot é
efeito de cache, não ausência; frequência de retorno se mede nas séries de borda. Não
existe evento unificado humano e bot, nem cursor incremental, nem coletor da GA4 Data
API.

**IA local.** Ollama 0.33.3 em `ollama.service`, CPU-only: 4 núcleos físicos e 8
threads, GeForce MX110 sem driver, UHD 620 inútil para 9-14B. 19,4 GiB de RAM
compartilhados com nginx, Go, 5 túneis, o Chrome do dono (~2,8 GB) e as sessões do
Claude Code. Modelos instalados: `qwen2.5-coder:14b` (Q4_K_M, 9,9 GB residente),
`qwen3.5:9b` (Q4_K_M, 6,1 GB, modelo com thinking: com `num_predict` pequeno devolve
resposta vazia, então use `think: false` ou modelo sem thinking para extração),
`qwen3-embedding:8b` (dimensão 4096, 6,7 GB residente) e
`guoxuter/ov_intent_analysis_sft:v7_q8` (752M, classificação de intenção). Medido: o 14b
gera 1,85 tok/s e processa prompt a 5,1 tok/s; o 9b gera 2,9 a 3,1 tok/s com prompt entre
5,6 e 8,2 tok/s; o embedding 8b consome cerca de 8 tok/s de entrada. Isso é ~18 GB/s de
banda efetiva de memória: geração ≈ 18 GB/s ÷ bytes do modelo, e o prompt processing é
limitado por CPU. Consequência: 2.000 tokens de entrada no 14b custam cerca de 7 min, e
embutir 10 mil páginas com o 8b levaria semanas. Tuning vivo (commit `c35d40a8`,
`ops/ollama/ollama.service.d/wikijuridica-tuning.conf`): `OLLAMA_MAX_LOADED_MODELS=1`,
`OLLAMA_NUM_PARALLEL=1`, `OLLAMA_CONTEXT_LENGTH=8192`, flash attention com KV `q8_0`,
`OLLAMA_LLM_LIBRARY=cpu`, `OLLAMA_NO_CLOUD=1`, `MemoryMax=15G`, `CPUWeight=60`, `Nice=5`;
`llama-server` está em `--prefer` do earlyoom (`ops/earlyoom/default`). Às 12:04:53 de
hoje, dois modelos residentes (16 GB) levaram a RAM livre a 4,7% e o earlyoom matou o
`llama-server` e os servidores MCP das sessões do Claude Code: é por isso que o teto
existe. Modelos pequenos no registro público, para medir: `qwen3-embedding:0.6b` e `:4b`,
`qwen3.5:0.8b`, `:2b` e `:4b`, `qwen3:0.6b`, `:1.7b` e `:4b`, `qwen2.5:0.5b`, `:1.5b` e
`:3b`.

**Clones na raiz do repo.** 293 diretórios, cerca de 63 GB, untracked; todo subagente os
exclui dos greps. Licenças lidas no disco: `chromem-go` MPL-2.0 (banco vetorial embutido
em Go, usável como biblioteca), `langchaingo` MIT, `agent-sdk-go` Apache-2.0,
`crewai-go` MIT, `ai-gateway` Apache-2.0, `gpt-researcher` Apache-2.0 (Python),
`Scrapling` BSD-3 (Python; só em modo honesto com o nosso UA, porque qualquer recurso
furtivo é vedado por `TestNenhumPontoDeSaidaSaiDisfarcado`), `MaxKB` e `TrendRadar` GPL
(referência apenas). Dependência nova exige ADR, licença, versão fixada e benchmark
10k/100k (DEC-036).

**Host.** ThinkPad Whiskey Lake ligado na tomada (bateria em modo de conservação), NVMe
com 288 GB livres, zram lz4 de 5 GB e swapfile de 8 GB, swappiness 10, THP madvise,
governor performance, nginx com `proxy_cache wj_dyn` e `use_stale`.
`ops/sysctl.d/zzz-wikijuridica.conf` só tem comentários, e `vm.overcommit_memory=1` foi
retirado por medição em 2026-09-04: não reintroduzir sem medir. `pcscd` é o daemon do
token de certificado usado com o PJe e nunca se desliga.

## 2. A tese do produto: B2A, e as duas correções que a tornam executável

O dono virou a chave. A WikiJurídica não é site institucional: é um serviço para IA. O
produto é o contexto jurídico estruturado de alta densidade; o HTML humano é uma
serialização entre várias (Markdown, MCP, A2A, `/api/v1`). O cliente é o agente —
GPTBot, PerplexityBot, ClaudeBot e os agentes autônomos dos escritórios — e a métrica de
sucesso é frequência de retorno e citação, não cobertura de rastreio
(`docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md`).

1. **Interface "transmutada" por User-Agent ou comportamento é cloaking.** O Google trata
   como spam servir conteúdo diferente a bot e a humano na mesma URL, e o `CLAUDE.md` §6
   exige o mesmo conteúdo. O caminho certo já existe e se amplia: mesmo conteúdo,
   serializações distintas por URL e por `Accept` (`index.md`, `/api/v1`, MCP, JSON-LD
   embutido). Camada adaptativa para humanos (resumo para leigo, versão densa para
   advogado) fica dentro da mesma página, no teto de 50 KB, sem JavaScript obrigatório e
   nunca por sniffing de agente.
2. **A IA local nunca escreve em `public/`.** Ela produz propostas — fila revisável com
   motivo, evidência e diff — que entram na cadeia de publicação existente (gates,
   `published_manifest`, release transacional) e respeitam a matriz `--ressemear` e purga
   do §6. Reestruturar 10 mil páginas toda madrugada re-data o acervo inteiro e destrói a
   confiança do rastreador: mudanças se agrupam em lotes e a taxa de 304 se mede depois
   (`tools/check-efeito-nos-bots`).

## 3. Arquitetura-alvo em sete camadas

| # | Camada | Linguagem | O que é |
|---|---|---|---|
| 1 | Grafo de conhecimento jurídico | Go no serving, Python no batch | Entidades: norma e dispositivo (URN LexML), súmula, tema repetitivo e de repercussão geral, acórdão, tribunal, órgão julgador, relator, área, página e intenção. Relações: cita, revoga, altera, supera, aplica, é impactada por, co-citada com. Nasce de `legal_cocitation_index.jsonl`, de `source-snapshots` e das coletas novas. Grafo em SQLite (FTS5); vetores em `chromem-go` ou `sqlite-vec`, decididos por benchmark 10k/100k, não por preferência. |
| 2 | Ingestão em lote (§6) | Coletores Go existentes; Python onde o parser for melhor | Fontes oficiais e públicas em batch, retomáveis por cursor, taxa por host, proveniência (URL, data, hash), dedupe por hash ou Bloom, timers systemd com `Nice` e `IOWeight`. |
| 3 | Cérebro 24/7 (§5) | Daemon Go (`cmd/cerebro`) sobre o Ollama | Fila SQLite com prioridade, orçamento em tok/s medido, janela noturna para o 14b, tarefas idempotentes, resultado como dado permanente em `data/ai/`. |
| 4 | Comportamento e buracos de conhecimento (§7) | Python ou Go | Evento unificado humano e bot a partir do log de origem, das séries de borda, do GA4 e do Clarity; score por página; fila de reescrita com motivo. |
| 5 | Efeito cascata (§8) | Go | Decisão nova, grafo, páginas impactadas, `risco_de_superacao` em JSON e etiqueta na página, com fonte. |
| 6 | Superfície B2A (§9) | Go (`internal/httpserver`, `internal/agentsurface`) | Ferramentas MCP novas, skills A2A, feed de mudanças com WebSub, export NDJSON, chaves de API e cotas self-hosted, JSON-LD `LegalCase` e `Legislation`, `ai-catalog` preenchido. |
| 7 | Medição própria | Go ou Python | Retorno por bot na borda, citação, retenção humana, custo por token da IA local; tudo em `data/ops/*.jsonl` com cursor. |

Política de linguagem (ordem do dono de 2026-09-08, `CLAUDE.md` §12): o que serve HTML
continua em Go. A camada de inteligência — ingestão, embeddings, classificação,
previsão, grafo, análise de comportamento — usa a linguagem que der mais algoritmo e
desempenho: Python com `pyproject` e versão fixada, Rust quando a medição justificar,
sempre com testes alcançados por `tools/run-qualidade-diaria`. Reescrever Go que
funciona em produção continua sendo regressão.

## 4. Método obrigatório: o que faz disto execução, não plano

- Tasklist viva. Crie `AI-first-wikijuridica.bot` na raiz do repo com um sumário no
  topo (o que fazer, em ordem, para sobreviver à compactação) e, abaixo, este mandato na
  literalidade. Cada medição, decisão e achado de agente entra no plan update na hora.
  `docs/goal/MAESTRO_CODEX_LOG.md` recebe o quê e o porquê de cada frente.
- Teste de regressão sempre (ordem do dono de 2026-09-06): toda correção vem com teste
  que reprova sem ela, provado por mutação, e a bancada do pacote roda
  (`./tools/go-modern test -count=1 ./internal/<pkg>/`, `tools/test_*.py`). Gate verde
  não é prova; leia amostras.
- Medir antes de decidir. Modelo, banco vetorial, tamanho de chunk, janela noturna:
  cada escolha vem com número próprio (tok/s, p95, RSS, wall-time por mil itens) gravado
  em `data/ops/`.
- Ondas dirigidas de agentes com escopos disjuntos e ledger em
  `.agents/agent_context_ledger.jsonl`; relatório de agente é alegação até verificação
  no disco. Fable refuta antes de editar algo caro; `advisor` na cadência do contrato.
- Commit por frente: `git add <caminho exato>` e `git commit -F` em comandos separados;
  commit que toca Go ou `go.mod` serializado por `flock /tmp/opt-wiki-agent-heavy.lock`;
  nunca reverter, nunca `--no-verify`.
- Proibido: stub, mock ou placeholder; UA de bot real; SaaS ou chave nova; cloaking;
  escrever em `public/` fora do release; desligar `pcscd`, Xorg ou lightdm; dois modelos
  residentes no Ollama; afrouxar gate; o padrão full-tree do Go; `cmd/check` sem
  argumento.

## 5. O cérebro 24/7: desenho e orçamento

Orçamento físico: um modelo residente por vez, `MemoryMax=15G`, 4 núcleos, ~18 GB/s.
Daí a política de modelos, que você confirma medindo (`/api/generate` com
`stream: false` devolve `eval_count` e `eval_duration`; `/api/embed`, `load_duration` e
`prompt_eval_count`):

| Trabalho | Modelo | Por quê |
|---|---|---|
| Embeddings do acervo e do corpus (milhões de chunks) | `qwen3-embedding:0.6b` (medir; fallback `:4b`) | O 8b a 8 tok/s levaria semanas; o 0.6b deve ficar em centenas de tok/s |
| Classificação e extração em massa (área, dispositivos citados, tese, prazo, resultado da decisão) | modelo de 2-4B sem thinking (`qwen3.5:4b` com `think: false`, `qwen2.5:3b`) e o `ov_intent_analysis_sft` para intenção de consulta | throughput; saída JSON validada por schema; amostra de 50 itens conferida antes de escalar |
| Reescrita, síntese, código e tarefas de alto valor | `qwen2.5-coder:14b` ou `qwen3.5:9b` | só em lote noturno, com janela escolhida pela medição de tráfego, entrada curta pré-extraída, nunca documento inteiro |

Daemon `cmd/cerebro`: fila SQLite em `data/ai/fila.sqlite` com tipo, prioridade,
tentativas, custo estimado em tokens e `keep_alive` por tarefa; um worker; cada tarefa é
idempotente e grava resultado, proveniência, hash do prompt, modelo e versão em
`data/ai/*.jsonl`; tok/s e custo por tarefa em `data/ops/ia_local_daily.jsonl`; unit
systemd própria com `Slice=` e `CPUWeight` abaixo do portal; para no instante em que
`wikijuridica-server` ou o nginx falharem no health (`tools/check-portal-health`).
Tarefas iniciais: (1) embeddings de todas as páginas e gêmeas; (2) extração de entidades
de `source-snapshots` para o grafo; (3) análise diária de comportamento (§7); (4)
cascata (§8); (5) auto-avaliação: para cada lote de mudanças, medir retorno e citação
antes e depois, por coorte de páginas.

## 6. Ingestão em lote: o máximo, de forma inteligente

Prioridade por valor para os agentes e por facilidade de proveniência. Dias de coleta
são aceitáveis; a regra é retomável, medida e educada: taxa por host, `Retry-After`,
cache condicional, backoff, `robots.txt` honrado, UA `WikijuridicaBot`.

1. Já operam, e se mantêm e escalam: DJEN, DataJud (API pública, `nivelSigilo > 0`
   excluído, 120 req/min), STF informativo, STJ precedentes qualificados,
   `normas.leg.br` e LexML, oráculo (11.317 documentos).
2. Coletores a criar: inteiro teor de acórdãos e ementas por dados abertos oficiais (STF,
   STJ, TST, TRFs e TJs pelos portais de jurisprudência e pelo DJEN/DJe), súmulas e
   súmulas vinculantes na fonte do STF, temas de repercussão geral e repetitivos, DOU e
   diários oficiais (`collect-diarios-municipais` existe sem timer). Cada coletor vira
   `cmd/collect-<fonte>` ou módulo Python com o mesmo contrato de saída (JSONL mais
   manifest com URL, data, hash e base legal ou licença), timer systemd, teste de parser
   sobre amostra real e cursor.
3. Notícias e web jurídica (Google News RSS, Bing News RSS, feeds de tribunais, Conjur,
   Migalhas, Jusbrasil e blogs): permitidas como análise interna — metadados e trecho
   limitado com hash, `robots.txt` e taxa respeitados — e proibidas como corpo, cópia ou
   paráfrase. São sinal de demanda, vocabulário e tendência na camada bloqueada que o
   `AGENTS.md` já prevê (`demand_signal_observations`, amostras com
   `full_text_stored=false`).
4. Atores públicos (juízes, promotores, defensores, procuradores): só sobre atos
   públicos, em agregado por órgão, tema e período, sem dado sensível e com redação
   sóbria: "índice de reforma", "tempo médio", "tese predominante"; nunca "chance de
   êxito".

Orçamento de disco: 288 GB livres; corpus bruto comprimido com zstd em `data/corpus/` ou
em volume dedicado; índices derivados sempre regeneráveis.

## 7. Comportamento humano e agentes: onde estão os buracos de conhecimento

Construa o evento unificado (`data/ops/eventos/*.jsonl`, com cursor) a partir do log de
origem, das séries de borda, do que a página emite para o GA4 e do Clarity. Coletor da
GA4 Data API só se já existir credencial configurada; nunca peça credencial nova. Por
página e por dia: requisições por agente de IA (borda e origem), percentual em Markdown,
cliques em fonte oficial, WhatsApp, busca interna e termos sem resultado, retenção. O
cérebro cruza: páginas muito lidas por agentes e pouco por humanos pedem contexto mais
denso na gêmea e no JSON; páginas muito lidas por humanos e ignoradas por agentes pedem
estrutura (JSON-LD, percursos, FAQ); buscas internas sem resposta viram intenção nova na
fila editorial; decisões novas que os agentes procuram e o portal não cobre viram
coleta e página. Saída: `data/ai/propostas_reescrita.jsonl` com motivo, evidência
numérica e patch sugerido ao gerador datado (correção de página v2 é por gerador datado
com CAS, nunca edição manual do JSONL).

## 8. Efeito cascata

Decisão nova coletada; extração por modelo de 2-4B com JSON validado; busca no grafo por
dispositivos, temas e súmulas citados, mais vizinhança vetorial; lista de páginas
impactadas com grau; campo `risco_de_superacao` (0 a 1, com fonte, data e explicação) no
dado da página e etiqueta visível ("decisão recente pode alterar esta orientação", com
link); ferramenta MCP `impacto(norma | tema | decisao)` e feed de mudanças. Toda
alteração passa pelo release; nada muda em `public/` sem gate.

## 9. Superfície B2A: o que entregar

- MCP: `buscar_semantico(pergunta, area, k)`; `contexto_juridico(pergunta)` devolvendo
  blocos densos (tese, dispositivos com URN, precedentes, risco, fontes, `cite-as`);
  `impacto(...)`; `mudancas_desde(cursor)`; `grafo(entidade)`. `search` e `fetch`
  continuam no contrato da OpenAI.
- A2A: skills declaradas no agent card; `ai-catalog.json` com entradas reais.
- Feed de mudanças em NDJSON por cursor, com WebSub para agentes inscritos; export em
  massa NDJSON por área; OpenAPI com as rotas de escrita.
- Chaves de API e cotas self-hosted (`internal/oauthserver` já existe): tier livre para
  bots públicos, tier identificado para escritórios. É a base para monetizar contexto
  sem SaaS.
- JSON-LD `LegalCase` e `Legislation` nas páginas que citam decisão ou norma; `llms.txt`
  completo.
- Cada rota nova vem com teste, com os gates `htmlcontract` e `agentsurface`, e com
  medição de uso em `route_class`.

## 10. Host

Feito hoje: drop-in do Ollama e earlyoom (§1). Medir e só então aplicar: slices systemd
(`portal.slice` com `CPUWeight=500` e `MemoryLow`; `ia.slice` com `CPUWeight=100`,
ligados por `Slice=` nas units), `vm.min_free_kbytes` maior, `vm.swappiness=5`,
`IOWeight` dos timers pesados, janela de coleta fora do pico de tráfego. Não fazer:
`vm.overcommit_memory=1` (retirado por medição), desligar `pcscd`, Xorg ou lightdm,
qualquer aposta em GPU.

## 11. Contratos e documentação (ordem do dono de 2026-09-08)

`AGENTS.md` (170 KB) e `GOAL.md` carregam parágrafos da era Codex e regras já superadas:
"publicação zero", domínio só depois do goal, piso de modelo `gpt-5.5`. Modernize para
frente: parágrafo superado ganha data e motivo, nunca é apagado; a política AI-first,
B2A, IA local e linguagens entra escrita; e os guardas de frase rodam
(`internal/contract/misc/peer_governance_test.go`, `engineering-now-contract`,
`ai_terminal_launcher_test.go`), porque 32% do `AGENTS.md` é travado por teste e só muda
junto com o teste. O `CLAUDE.md` §12 já traz a política nova.

## 12. Fases e definição de pronto (nenhuma fica para depois)

- P0, fundação medida, nesta sessão: `cmd/cerebro` rodando como unit com fila;
  embeddings do acervo inteiro com o modelo escolhido por medição, tempo total
  registrado; `buscar_semantico` no MCP com teste; evento unificado com cursor;
  `AI-first-wikijuridica.bot` criado; contratos atualizados; commit.
- P1, corpus: pelo menos 3 coletores novos de jurisprudência com timers; grafo v1 (norma,
  súmula, tema, acórdão, página) consultável; `contexto_juridico` e `impacto` no MCP.
- P2, buracos e propostas: primeira fila de reescrita com 100 propostas justificadas;
  lote publicado pela cadeia; retorno e citação medidos antes e depois.
- P3, cascata e superfície: `risco_de_superacao` em produção; feed de mudanças com
  WebSub; chaves e cotas; JSON-LD `LegalCase`.
- P4, escala: milhões de chunks, coleta contínua de dias, custo por token e por página
  publicado em `data/ops/`.

## 13. Perguntas que só a medição responde (a resposta vai para o plan update)

Qual modelo de embedding dá o melhor recall@10 em 200 consultas reais de `busca_interna`
por tok/s? `chromem-go` ou `sqlite-vec` a 1 milhão de vetores nesta RAM? Qual janela
noturna tem menos tráfego de agentes na borda? Qual a taxa de erro do extrator de 4B em
50 decisões conferidas? Que fração das requisições de agentes bate hoje em páginas sem
JSON-LD? Quantas horas de máquina custam 1.000 páginas reestruturadas?
