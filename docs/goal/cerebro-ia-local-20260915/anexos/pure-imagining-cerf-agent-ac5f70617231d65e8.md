# Colheita: o que os agentes de IA REALMENTE leem na borda

Medido em 2026-09-15 contra a zona real `wikijuridica.com.br` pela API GraphQL da
Cloudflare (`httpRequestsAdaptiveGroups`), via `tools/cloudflare_auth.py`, escopo
`leitura`, proposito `colheita-leitura-de-agentes`. Janela fatiada em 1 dia por
chamada (`JANELA_MAXIMA_DIAS_FREE = 1`), 8 dias: **2026-09-08 a 2026-09-15** — o
limite nao e escolha, e a retencao de 8 dias do dataset adaptativo.

**CAMADA DE TODO NUMERO ABAIXO: BORDA** (Cloudflare), salvo onde escrito o
contrario. `count` do adaptativo e contagem, nao amostra a extrapolar (conferido
no cabecalho de `tools/generate-cache-baseline`: Σ count a ≤ 0,3% do
`httpRequests1dGroups`).

## ERRO DE METODO QUE EU COMETI E CORRIGI — vale como regra

Na primeira passada guardei o `userAgent` truncado em 120 caracteres. **Os
agentes de IA poem o proprio token no FIM de um UA em forma de navegador**:

```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot
```

Truncar em 120 jogou **OAI-SearchBot (12.118 req/8 dias) para o balde
"navegador"** e fundiu Applebot com ele pelo prefixo comum. Todo numero deste
documento foi re-colhido com UA integro. Quem medir isto de novo: **UA inteiro,
sempre** — e `userAgent_like` da Cloudflare e SENSIVEL A CAIXA (nao existe
`userAgent_ilike`).

---

## 0. O enquadramento: quanto da borda e agente

| camada | requisicoes 8 dias | %  |
|---|---|---|
| total na borda | **1.186.321** | 100% |
| aquecimento INTERNO (`wikijuridica-*`) | **866.020** | 73,0% |
| externo real | **320.301** | 27,0% |
| **agentes de IA** (17 tokens) | **144.524** | **45,1% do externo** |

**Composicao dos 144.524, declarada para o numero nao ser lido como maior do que
e:** 34.935 sao `meta-externalads` (a Cloudflare rotula *Advertising & Marketing*
— e o crawler de anuncio do Facebook, nao busca resposta), 15.449 sao
`Cloudflare-AI-Search-External` (o indexador de RAG da propria Cloudflare) e
6.170 sao `PetalBot` (buscador da Huawei). O nucleo que busca para RESPONDER
pergunta de usuario — ChatGPT-User, PerplexityBot, OAI-SearchBot, Claude-*,
Applebot — soma **31.037** em 8 dias (3.880/dia), e o nucleo que VARRE para
treinar/indexar — GPTBot, Amazonbot, ShapBot, Bytespider, CCBot — soma
**57.127**.
| infra de agente / MCP (registries, sondas, SDKs) | ~20.000 | ~6,2% do externo |
| SEO (ahrefs, semrush, baidu, bing, google, yandex, dotbot) | ~43.000 | ~13,4% do externo |

Serie diaria total: 150.508 · 220.391 · 267.028 · 237.633 · 77.534 · 71.335 ·
73.776 · 88.116. A queda de 267k (09-10) para 77k (09-12) e o **aquecimento
interno**, que passou a rodar so as 04:20/16:20 UTC — nao e queda de audiencia.

---

## 1. QUAIS CAMINHOS OS AGENTES BUSCAM (exato, 3 dias estaveis 09-13/14/15, sem truncamento)

| agente | req/3d | familia dominante | 2a | 3a |
|---|---|---|---|---|
| **amazonbot** | 9.840 | REDESOCIAL 36% | **GEMEA.md 33%** | **FEED ATOM 28%** — HTML so 4% |
| **oai-searchbot** | 4.742 | HTML 85% | redesocial 8% | gemea.md 6% |
| **petalbot** | 3.033 | HTML 90% (jurisprudencia 41%) | sitemap 6% | redesocial 4% |
| **chatgpt-user** | 2.480 | **HTML 99%** | sem-barra 1% | **gemea.md 0 · api 0 · mcp 0** |
| **cf-ai-search** | 992 | **SITEMAP 68%** | favicon/css/svg 21% | HTML 7% |
| **applebot** | 939 | **API 45% (423 csp-report, 204)** | redesocial 49% | HTML 2% |
| **perplexitybot** | 895 | HTML 68% | redesocial 30% | **gemea.md 0** |
| **gptbot** (pos-varredura) | 318 | HTML 43% | GEMEA.md 40% | sitemap 10% |

Areas do acervo mais lidas, por agente (3 dias, exato):

- **chatgpt-user**: sumulas 318 · leis 312 · tributario 285 · glossario 184 ·
  procedimentos 171 · trabalhista 145 · previdenciario 130
- **oai-searchbot**: imobiliario 480 · leis 477 · glossario 387 · trabalhista 309
  · consumidor 234 · sucessoes 198 · procedimentos 171
- **perplexitybot**: leis 104 · sumulas 66 · imobiliario 54 · glossario 40
- **petalbot**: jurisprudencia 1.253 (41%) · trabalhista 224 · tributario 189
- **amazonbot**: jurisprudencia 372 (quase so jurisprudencia no HTML)

**A leitura:** o que os assistentes buscam e **lei, sumula e glossario** —
superficie de *definicao e dispositivo*, nao de caso. O que os varredores buscam
e **jurisprudencia**. Sao duas demandas distintas e o acervo atende as duas por
acidente, nao por desenho.

### /redesocial/ e o maior ima de IA do portal

| agente | /redesocial/ 200, 8 dias |
|---|---|
| gptbot | **23.105** |
| amazonbot | 8.420 |
| oai-searchbot | 1.303 |
| meta | 833 |
| perplexity | 743 |
| applebot | 364 |

Temas mais lidos pelo gptbot: glossario 2.449 · previdenciario 1.540 ·
imobiliario 1.532 · consumidor 1.450 · trabalhista 1.239.

E `comentarios_de_autoridade = 0`. **A superficie mais visitada por IA no portal
esta vazia de conteudo proprio.**

---

## 2. HTML OU GEMEA MARKDOWN? — a medicao decisiva

Requisicoes de 8 dias, `clientRequestPath_like:"%index.md"` contra
`clientRequestPath_like:"%/"`, por agente:

**CLASSE QUE BUSCA PARA RESPONDER (fetch em tempo de resposta):**

| agente | HTML | gemea.md | % md |
|---|---|---|---|
| meta | 17.482 | 7 | 0,04% |
| perplexity | 11.913 | 4 | 0,03% |
| petalbot | 5.828 | 1 | 0,02% |
| chatgpt-user | 4.992 | **0** | **0,00%** |
| cf-ai-search | 3.404 | **0** | **0,00%** |
| applebot | 666 | 4 | 0,60% |
| anthropic | 46 | **0** | **0,00%** |
| ~~meta~~ / ~~petalbot~~ | *(ver nota)* | | |
| **soma da classe DEFENSAVEL** | **21.021** | **8** | **0,038%** |

*Nota de classe, para o numero nao ser contestavel:* `meta-externalads` (crawler
de anuncio) e `petalbot` (buscador Huawei) **nao buscam para responder pergunta**
e sairam da soma da classe, ainda que suas linhas de medicao fiquem na tabela.
A classe defensavel e ChatGPT-User + PerplexityBot + Cloudflare-AI-Search +
Applebot + Claude-*: **21.021 HTML contra 8 gemeas = 0,038%**. O veredito nao
muda; a classe fica a prova de objecao.

**CLASSE QUE VARRE O ACERVO:**

| agente | HTML | gemea.md | % md |
|---|---|---|---|
| gptbot | 15.666 | 14.884 | **48,7%** |
| baiduspider | 6.292 | 4.855 | **43,6%** |
| amazonbot | 5.955 | 3.646 | **38,0%** |
| shapbot | 1.609 | 512 | 24,1% |
| bingbot | 3.061 | 494 | 13,9% |
| oai-searchbot | 11.014 | 1.026 | 8,5% |

**VEREDITO: o problema da gemea NAO e de conteudo, e de DESCOBERTA EM TEMPO DE
RESPOSTA.** Quem varre o acervo acha a gemea (38–49%) — o link no HTML funciona.
Quem chega para responder uma pergunta agora (ChatGPT-User, Perplexity, Claude,
Cloudflare AI Search) pede **a URL que estava no indice do buscador**, que e a
HTML, e nunca mais navega. Densidade da gemea nao e a alavanca para essa classe;
**estar no indice como a URL canonica para agente** e.

Serie da gemea (8 dias) mostra o canal em CRESCIMENTO nos varredores:
amazonbot 0 → 1 → 4 → 67 → 371 → 684 → **1.306 → 1.213**;
baiduspider 0 → 0 → 0 → 51 → 1.865 → 1.303 → 883 → 753.

---

## 3. /api/v1/, MCP, A2A, DESCRITORES DE MAQUINA

**/mcp — 14.658 requisicoes em 8 dias (1.832/dia).** E a rota nao-HTML mais
pedida do portal (2.437 em 09-14, contra 689 de `/healthz`). Quem pede:

| classe | /mcp 8 dias |
|---|---|
| infra de agente / registries (mcpbeat, SentinelOracle, rokmcp-collector, MCPScoringEngine, mcpi/probe, MCPScan, mcp-watch, io.verifymcp, mcp-observatory, ProofBench, Neuronto, WellknownBot, aisec-registry, GolemreachTrustBot…) | **8.426** |
| clientes SDK genericos (`node` 4.051, `aiohttp`, `python-httpx`, `undici`) | **5.617** |
| anthropic (`claude-user` / `claude-code`) | 372 |
| UA vazio | 156 |
| interno | 87 |
| **gptbot / chatgpt-user / perplexity / amazonbot / applebot / meta / cf-ai-search** | **1** |

**Nenhum agente de IA de consumidor toca o MCP.** O MCP esta sendo consumido por
um MERCADO DE DIRETORIOS E OBSERVABILIDADE de MCP que o projeto nao sabia que
existia — 40+ operadores distintos, batendo todo dia com regularidade de cron.

**E a maioria e SESSAO REAL, nao ping de liveness — medido por metodo HTTP:**

| metodo | req 8 dias | status | leitura |
|---|---|---|---|
| **POST** | **13.364 (89,8%)** | 200 e 202 | **JSON-RPC de verdade.** SentinelOracle 3.473 · `node` 3.060 · mcpbeat 2.184 · rokmcp 574 · `aiohttp` 502 · `python-httpx` 428 |
| GET | 1.315 | **405** em 1.214 | `node` 774, AgentReliabilityMonitor 119, rokmcp 92, `Bun` 38, `undici` 14, Neuronto 12 — **e 1 GET do GPTBot, que tambem levou 405** |
| HEAD | 158 | **405** em 157 | `node` 113, `undici` 22, AIVE-MCP-EndpointProbe, TheMcpDirectoryHealthProbe, MCPExplorerBot, arete-mcp |
| OPTIONS | 27 | 204 | preflight CORS (`mcpi/probe`) |
| DELETE | 12 | 405 | `Go-http-client/2.0` |

`node`/`undici` e o que o `fetch` do **SDK TypeScript de MCP** manda;
`aiohttp`/`python-httpx`, o do **SDK Python**. Chamar isso de "cliente generico"
subestimava o sinal: sao clientes de MCP, e 5.617 dos seus POSTs sao sessao.
**1.473 requisicoes (GET+HEAD+DELETE) levam 405** — todo cliente que descobre
`/mcp` por link em vez de por descritor bate num 405 e nao recebe nada que o
oriente. O GPTBot foi um deles.

**Camada de ORIGEM, para o MCP e possivel e foi conferida:** `/mcp` e rota
DINAMICA pelo Go, entao a origem ve tudo — `data/ops/access/nginx-2026-09-14.jsonl`
tem **2.387** linhas de `/mcp` contra 2.437 na borda (a diferenca sao 405/499
terminados na borda). **Mas o nome da ferramenta chamada vive no corpo JSON-RPC,
nao no caminho** — nenhum log responde se alguem invocou `ler_pagina` ou
`buscar_semantico`. O unico artefato que ja registrou isso,
`data/ops/mcp_consumo_externo.jsonl`, tem **1 linha, escrita em 2026-08-13
12:10** (33 dias parado) sobre uma janela de 12 h. Ou seja: **13.364 sessoes MCP
em 8 dias e zero registro de qual ferramenta foi usada.**

**/.well-known/** — 521 requisicoes externas em 8 dias (65/dia), contra 4.143
internas. Descoberta praticamente nula. `/.well-known/agent-card.json` = 39/dia.

**/openapi.json** — 130 em 8 dias.

**/a2a/v1** — 19 em 09-14.

**/api/v1/** — 6.256 em 8 dias, e a composicao desmonta a expectativa:

| endpoint | 8 dias | quem |
|---|---|---|
| `/api/v1/search` | 2.672 | UA de navegador (Mac 708, Win 581) |
| `/api/v1/redesocial/csp-report` | **684** | **Applebot 499 · Baiduspider 150** |
| `/api/v1/lote` | 326 | **309 e aquecimento interno**; externo real: 17 |
| `/api/v1/citar/*` | ~200 | **100% aquecimento interno** |
| `/api/v1/health`, `/api/v1/pages` | 55 | sondas internas |

**`/api/v1/lote` e `/api/v1/citar` — as duas rotas que o contrato anuncia como o
canal de maquina — tem 17 chamadas externas em 8 dias.** O resto e o proprio
portal se aquecendo.

### O achado que e defeito, nao metrica: 684 CSP reports

`/api/v1/redesocial/csp-report` recebeu **423 relatorios do Applebot em 3 dias**
(status 204), o que e **45% de todo o orcamento de requisicao do Applebot** — e
os 457 acessos do Applebot a `/redesocial/` no mesmo periodo dizem que e **uma
violacao por pagina renderizada**. Baiduspider soma 150. Applebot executa
JavaScript: enquanto isso durar, Siri / Spotlight / Apple Intelligence renderizam
o portal quebrado.

**E o relatorio ESTA no disco — eu fui ler.** `cmd/social/cspreport.go` agrega em
`var/social/csp_violacoes_agregadas.jsonl` (21 linhas). A diretiva violada:

| dia | `script-src` | `script-src-elem` | superficie | origem do bloqueio |
|---|---|---|---|---|
| 2026-09-06 | 38 | 0 | publica | (+ `style-src-attr`, `style-src-elem`) |
| 09-08 | 2 | 0 | publica | `https://wikijuridica.com.br` |
| 09-09 | 1 | 3 | publica | idem |
| 09-10 | 1 | 15 | publica | idem |
| 09-11 | 2 | **41** | publica | idem |
| 09-12 | 3 | 15 | publica | idem |
| 09-13 | 4 | **49** | publica | idem |
| 09-14 | **109** | **132** | publica | idem |
| 09-15 | 65 | **243** | publica | idem |

**`script-src-elem` cresceu de 0 para 243/dia em 7 dias.** O que eu consegui
fechar por medicao, e o que fica declarado como nao medido:

- **MEDIDO — nao e o script do portal.** O unico script sem atributo na pagina
  servida tem 5.428 bytes e hash `sha256-AxM6ZsiaBmAZXu850m0njvH67GmpJW4q1BXHvVH+PUY=`,
  **identico, byte a byte, ao que o CSP servido autoriza**. A camada de medicao
  do portal nao esta bloqueada. (Os outros 3 scripts sao `application/ld+json`,
  que CSP nao executa.) Nao ha nenhum `<script src>` externo no HTML.
- **MEDIDO — a borda nao injeta.** `/leis/clt-art-2/` sai com **21.680 bytes
  identicos** na origem (`127.0.0.1:8088`) e na borda
  (`https://wikijuridica.com.br`), mesmos 4 scripts, mesmos hashes, sem
  `speculationrules` e sem `/cdn-cgi/` no corpo — para UA declarado de bot.
- **MEDIDO — os injetores conhecidos da Cloudflare estao DESLIGADOS**:
  `rocket_loader=off`, `email_obfuscation=off`, `mirage=off`,
  `automatic_platform_optimization=off` (GET nos settings da zona).
- **NAO MEDIDO, com o motivo**: qual elemento de script de MESMA ORIGEM e
  bloqueado. (i) o agregador reduz `blocked-uri` a esquema+host **por desenho**
  (`origemDoBloqueio`, para nao gravar texto livre do cliente), entao o CAMINHO
  nao esta no disco; (ii) confirmar injecao da borda condicionada a UA de
  navegador exigiria sair como navegador, **proibido** pelo contrato §11 e
  cobrado por `TestNenhumPontoDeSaidaSaiDisfarcado`. O candidato que resta com
  evidencia viva e o **Speculative Loading** da Cloudflare: `/cdn-cgi/speculation`
  recebeu **186 requisicoes em 09-14** na borda, e o setting nao e legivel no
  caminho `zones/{id}/settings/speculation_rules` (devolveu sem valor).

---

## 4. STATUS POR AGENTE (8 dias) — e o 304 que o contrato temia NAO EXISTE

| agente | total | 200 | 304 | 301 | 404 | 403 | 429 | 5xx | %304 | %HIT borda |
|---|---|---|---|---|---|---|---|---|---|---|
| gptbot | 39.771 | 38.863 | **0** | 18 | 873 | 16 | 0 | 0 | 0,0% | 5,1% |
| meta | 34.994 | 17.485 | **0** | **17.480** | 25 | 3 | 0 | 1 | 0,0% | 5,5% |
| cf-ai-search | 15.449 | 15.347 | 0 | 0 | 0 | 0 | 0 | 0 | 0,0% | 75,1% |
| amazonbot | 12.721 | 12.675 | 0 | 16 | 15 | 15 | 0 | 0 | 0,0% | 7,3% |
| oai-searchbot | 12.118 | 12.067 | 0 | 14 | 18 | 15 | 0 | 4 | 0,0% | 64,3% |
| perplexity | 11.993 | 11.573 | 0 | 18 | 390 | 12 | 0 | 0 | 0,0% | 25,5% |
| baiduspider | 11.472 | 5.531 | 0 | **5.785** | 1 | 0 | 0 | 2 | 0,0% | 33,4% |
| petalbot | 6.170 | 6.162 | 0 | 3 | 0 | 0 | 0 | 5 | 0,0% | 57,7% |
| chatgpt-user | 5.087 | 4.982 | 0 | 83 | 10 | 11 | 0 | 0 | 0,0% | 72,8% |
| shapbot | 4.632 | 2.241 | 0 | **2.391** | 0 | 0 | 0 | 0 | 0,0% | 42,9% |
| bingbot | 3.740 | 3.590 | **109** | 20 | 3 | 0 | 0 | 4 | **2,9%** | 61,8% |
| applebot | 1.349 | 826 | 0 | 9 | 4 | 9 | 0 | 0 | 0,0% | 16,7% |
| googlebot | 584 | 544 | 8 | 30 | 2 | 0 | 0 | 0 | 1,4% | 57,9% |

Tres conclusoes medidas:

1. **304 = 0 em TODOS os agentes de IA.** Os unicos que revalidam sao bingbot
   (109) e googlebot (8). O aviso do contrato — "publicacao que zera mtime e ETag
   faz os bots rebaixarem o acervo" — **nao se aplica a agente de IA**: eles nao
   revalidam, fazem GET integral sempre. O risco de rebaixamento por republicacao
   e um risco de BUSCA CLASSICA, e vale para 117 requisicoes em 8 dias.
2. **429 = 0 em toda a tabela.** Nenhum teto de taxa esta cortando agente algum.
   Nao ha perda por rate limit a recuperar.
3. **17.759 requisicoes de 301 em 8 dias** — 5.786 do meta, 5.708 do baiduspider,
   2.391 do shapbot, 3.688 de outros; 50% do orcamento do meta e do baiduspider.
   **E NAO E UMA CAUSA SO — eu media isso errado.** A dimensao
   `clientRequestScheme` **nao esta disponivel nesta zona** (erro literal da API:
   *"zone ... does not have access to the field 'clientrequestscheme'"*), entao
   parti as causas por sonda contra a producao (UA `WikijuridicaBot/1.0`,
   proposito `diagnostico-de-redirecionamento`):

   | sonda | resultado | quem gasta assim |
   |---|---|---|
   | `https://…/transito/veiculo-parado-patio-anos-leilao/` (COM barra) | **200** | — |
   | `http://…/transito/veiculo-parado-patio-anos-leilao/` (COM barra) | **301 → https** | **baiduspider 5.708** (rastreia por http) |
   | `https://…/leis/clt-art-2` (SEM barra) | **301 → `/leis/clt-art-2/`** | **shapbot 2.391**, parte do meta |

   Emitir barra final em sitemap, feed e gemea resolve shapbot e meta; **nao
   resolve um unico dos 5.708 do baiduspider**, que vem de indice http proprio.
   Confirmacao de que o host tambem contribui: `www.wikijuridica.com.br` aparece
   com 28 requisicoes 301 em 09-14 (dimensao `clientRequestHTTPHost`, esta
   disponivel).
4. **%HIT na borda separa duas populacoes**: quem responde pergunta bate em cache
   quente (chatgpt-user 72,8%, cf-ai-search 75,1%, oai-searchbot 64,3%) — e por
   isso **a origem nao os ve**, o que confirma por que
   `data/ops/ai_citation_signal_daily.jsonl` se declara `is_lower_bound: true`.
   Quem varre bate em MISS (gptbot 5,1%, amazonbot 7,3%, applebot 16,7%).

---

## 5. 404: DEMANDA EXPLICITA E NAO ATENDIDA — a alavanca mais barata

2.921 requisicoes com 404 em 8 dias, 1.185 rotas distintas. A separacao por
`verifiedBotCategory` (a propria Cloudflare) parte a massa em duas:

| categoria verificada pela Cloudflare | total 404 | /redesocial/ | /.well-known/ ou /mcp | outras |
|---|---|---|---|---|
| **AI Crawler (VERIFICADO)** | **871** | **870** | 1 | **0** |
| Advertising & Marketing (meta-externalads) | 22 | 22 | 0 | 0 |
| Search Engine Crawler | 18 | 8 | 2 | 8 |
| Search Engine Optimization | 6 | 3 | 0 | 3 |
| NAO-VERIFICADO | 2.004 | 390 | 242 | 1.372 |

**A) 404 em `/redesocial/`: 1.293 requisicoes em 754 rotas distintas — das quais
870 (67,3%) assinadas por crawler que a Cloudflare VERIFICOU como AI Crawler.**
As outras 423 sao 374 do mesmo prefixo de UA mas NAO-VERIFICADO (ambiguo entre
GPTBot de IP que a CF nao cobre e disfarce), 22 do `meta-externalads` (verificado
*Advertising & Marketing*) e 27 de buscador/SEO verificado.

| padrao | 404 / 8 dias |
|---|---|
| `/redesocial/tema/jurisprudencia/stj-tema-NNN/` | **1.118** |
| `/redesocial/tema/leis/cpc-art-NNN/`, `cc-art-`, `cdc-art-`, `clt-art-` | 89 |
| `/redesocial/tema/noticias/stf-AAAAMMDD/`, `stj-` | 38 |
| `/redesocial/tema/sumulas/stj-NNN/`, `tst-` | 34 |
| `/redesocial/tema/diarios/UF-AAAAMMDD/` | 14 |

**E A CAUSA NAO E "FALTA CONTEUDO" — eu medi, e o que eu tinha escrito antes
estava errado.** Quatro medicoes, nesta ordem:

1. **Sonda na origem, agora**: `/redesocial/tema/jurisprudencia/stj-tema-1015/`
   devolve **200**; `stj-tema-260/` **200**; `sumulas/stj-554/` **200**;
   `glossario/carne-leao/` **200**. Mas `leis/cpc-art-321/` **404** e
   `diarios/mg-20260911/` **404**.
   (`curl` contra `127.0.0.1:8088` com `wikijuridica-superficie-probe/1.0` +
   `X-Warming-Request: true`.)
2. **Data dos 404**: `1.114 dos 1.118` de `stj-tema-*` cairam em **09-09 (126) e
   09-10 (988)** e cessaram: 09-11=1, 09-12=2, 09-13=1, 09-14=0, 09-15=0.
3. **O processo social em execucao comecou em `2026-09-11 03:08:16`**
   (`systemctl show wikijuridica-social -p ExecMainStartTimestamp`,
   `NRestarts=0`). A janela de 404 fecha exatamente no start.
4. **Quem anunciou a rota**: nao foi o sitemap — `/redesocial/sitemap/superficie.xml`
   tem **38 `<loc>` e ZERO rota `tema/`**. Foi o proprio acervo:
   `public/jurisprudencia/stj-tema-1015/index.html` contem o link
   `/redesocial/tema/jurisprudencia/stj-tema-1015/`, e o acervo tem **1.039**
   paginas `/jurisprudencia/stj-tema-NNN/`.

**Veredito: defeito de COERENCIA DE SUPERFICIE, nao lacuna de conteudo.** O HTML
publicado anunciava rotas da rede social que o processo social ainda nao servia;
a varredura do GPTBot seguiu esses links e queimou **1.114 requisicoes em 48 h**
num 404. E exatamente a classe que o repo ja nomeia em
`TestSuperficieDeAgenteSoAnunciaRotaViva` ("o gate existe para reprovar quem
anuncia rota morta ... a gemea `/index.md` que devolvia 404"), e ja se resolveu
sozinho no start de 09-11 — **produzir 754 paginas seria trabalho sobre um
problema que nao existe.**

**Residuo que AINDA e defeito vivo: 141 requisicoes** — `tema/leis/*` 89
(`cpc-art-321` da 404 hoje; 36+40+3+5+5 de 09-11 a 09-15, ou seja **depois** do
start, logo estrutural), `tema/noticias/*` 38 e `tema/diarios/*` 14 (rotas com
data, que expiram por desenho e continuam anunciadas depois de expirar).

**B) 242 requisicoes 404 em descritores de maquina que um mercado inteiro
espera:**

| rota 404 | req | quem espera |
|---|---|---|
| `/.well-known/glama.json` | **86** | Glama — diretorio de servidores MCP (verificacao de posse) |
| `/mcp/.well-known/oauth-authorization-server` | 31 | descoberta de OAuth do proprio protocolo MCP |
| `/mcp/.well-known/mcp` | 31 | descoberta de capacidade MCP |
| `/.well-known/x402` + `/.well-known/x402.json` | 16 | x402 — pagamento HTTP 402 para agente |
| `/.well-known/ard.json` | 10 | Agent Registry Descriptor (Neuronto) |
| `/.well-known/owners.json` + `/mcp/.well-known/owners.json` | 16 | prova de posse de superficie de agente |
| `/.well-known/openid-configuration` | 7 | idem OAuth |
| `/.well-known/mcp.json`, `/.well-known/mcp-server.json` | 7 | descritor de servidor MCP |
| `/.well-known/http-message-signatures-directory` | 1 | assinatura de mensagem HTTP (RFC 9421) |
| `/agents.txt`, `/CLAUDE.md`, `/api/docs`, `/docs/openapi.json`, `/api/openapi.json`, `/openapi-public.json` | 7 | convencoes alternativas |

**C) Ruido a NAO confundir com demanda:** 1.372 dos 404 vem de UA
**NAO-VERIFICADO** pedindo `/secrets.json`, `/id_rsa`, `/.claude/settings.json`,
`/config/anthropic.json`, `/wp-json/batch/v1/`. Sao **varredores de credencial
que se disfarcam de ChatGPT-User, PerplexityBot, Claude-User e Amazonbot** —
nenhum AI Crawler verificado pediu uma unica rota dessas. Quem for atribuir
demanda por UA sem cruzar com `verifiedBotCategory` vai ler scanner como cliente.

---

## 6. SERIE TEMPORAL: cresce, estavel ou cai

Requisicoes/dia na borda, por agente (8 dias):

| agente | 09-08 | 09-09 | 09-10 | 09-11 | 09-12 | 09-13 | 09-14 | 09-15 | leitura |
|---|---|---|---|---|---|---|---|---|---|
| **amazonbot** | 16 | 10 | 511 | 872 | 1.444 | 2.586 | 3.808 | 3.446 | **de ~0 a 3.446/dia em 8 dias**, monotonico ate 09-14 |
| **baiduspider** | 0 | 0 | 0 | 242 | 3.598 | 3.079 | 2.366 | 2.034 | **entrante novo**, do zero |
| **chatgpt-user** | 542 | 608 | 600 | 566 | 291 | 290 | 1.098 | 1.092 | **dobrou** no fim da janela |
| applebot | 81 | 60 | 79 | 132 | 58 | 119 | 297 | 523 | **6x** |
| oai-searchbot | 888 | 470 | 1.251 | 591 | 4.176 | 2.163 | 1.338 | 1.241 | volatil, base ~1.200 |
| perplexitybot | 198 | 3.454 | 4.875 | 1.235 | 1.319 | 263 | 267 | 365 | **caiu 13x do pico** |
| gptbot | 44 | **36.671** | 2.615 | 6 | 117 | 6 | 71 | 241 | varredura unica em 09-09 |
| meta-externalads | 0 | 0 | 0 | **33.365** | 1.264 | 306 | 0 | 0 | rajada unica em 09-11 |
| cf-ai-search | 1.365 | 3.896 | 6.242 | 2.417 | 537 | 361 | 341 | 290 | **caiu 21x** |
| petalbot | 1 | 359 | 750 | 1.016 | 1.011 | 1.007 | 1.008 | 1.018 | estavel (cron) |
| shapbot | 71 | 90 | 35 | 49 | 3.461 | 15 | 45 | 866 | esporadico |
| infra MCP (/mcp) | 1.055 | 1.118 | 1.066 | 1.049 | 1.077 | 1.028 | 1.062 | 971 | **estavel, cron diario** |
| SDK generico (/mcp) | 461 | 490 | 448 | 393 | 448 | 1.160 | 1.319 | 898 | **quase 3x** |

**Nao ha uma tendencia; ha tres regimes.** (i) varredura em rajada (gptbot,
meta-externalads): um dia enorme e depois quase nada; (ii) crescimento sustentado
(amazonbot 215x, applebot 6x, chatgpt-user 2x, SDK no /mcp 3x); (iii) queda
sustentada (cf-ai-search 21x, perplexitybot 13x do pico). Media de 8 dias
esconderia os tres.

### Feed Atom: o canal mais consumido por maquina e ninguem sabia

12.801 requisicoes de `content-type: atom` em 8 dias, em **5.258 rotas
distintas**. Consumo:

| agente | atom, 8 dias |
|---|---|
| **gptbot** | **9.121** |
| **amazonbot** | **3.092** |
| websub interno | 369 |
| mj12bot | 49 |
| resto | ~170 |

**95,4% do consumo de feed vem dos dois maiores crawlers de IA**, e eles pedem os
feeds POR TEMA da rede social (`/redesocial/tema/<area>/<slug>/feed.xml`), nao o
`/feed.xml` global (536). Para o amazonbot, feed = 28% de todo o seu orcamento.

---

## LACUNA A NOMEAR: falta o instrumento, e ele e especificavel

**Hoje nao existe ferramenta que responda "o que os agentes leem".** O que existe
mede coisa ao lado:

| ferramenta existente | o que mede | por que nao responde |
|---|---|---|
| `tools/generate-bot-agents-daily` | requisicoes por AGENTE | nenhuma dimensao de rota |
| `tools/generate-edge-humano-por-rota` | rotas do trafego NAO-bot-verificado | filtra `verifiedBotCategory: ""` — **exclui de proposito exatamente os agentes** |
| `tools/generate-edge-bot-status-daily` | status por agente | sem rota, sem classe de superficie |
| `data/ops/ai_citation_signal_daily.jsonl` | ORIGEM | com 64–75% de HIT nos assistentes, nao ve a maioria |
| `tools/check-perfil-por-bot` | perfil por bot | nao cruza superficie x rota |

**Proposta, com nome, medida, gravacao e gate:**

1. `tools/generate-edge-leitura-de-agente-daily` (gerador, escreve)
   - **mede, por dia e por `agent_key` da fonte unica `tools/botagents.py`**:
     requisicoes por CLASSE DE SUPERFICIE — `html_acervo`, `gemea_md`,
     `redesocial`, `feed_atom`, `api_v1` (por endpoint), `mcp`, `a2a`,
     `well_known` (por descritor), `sitemap`, `assets`, `sem_barra_final` —
     mais status (200/301/304/403/404/429/5xx), `cacheStatus` (hit/miss) e a
     `verifiedBotCategory` da Cloudflare em coluna PROPRIA.
   - **como**: uma consulta por dia por classe com `clientRequestPath_like` /
     `clientRequestPath_notlike` — **contagem exata, sem truncamento**, que e o
     que a dimensao `clientRequestPath` crua nao entrega (ela estoura o teto de
     10.000 grupos em dia de varredura: medido 09-09, 09-10, 09-11, 09-12).
   - **grava**: `data/ops/edge_agent_reading_daily.jsonl`, append-only, uma
     linha por dia, `schema_version: edge_agent_reading_v1`, com
     `janela_retencao_dias: 8` e `camada: "borda"` declarados na propria linha.
   - **guarda obrigatoria**: `userAgent` INTEGRO na classificacao (o erro de 120
     caracteres acima) e `agent_key` derivado por `botagents.agente_de()`, nunca
     por tabela local.

2. `tools/generate-edge-agent-404-demanda` (gerador, escreve)
   - **mede**: 404 por rota cruzado com `verifiedBotCategory`, separando
     `demanda` (AI Crawler/Search Engine verificado) de `scanner`
     (nao-verificado pedindo credencial/WordPress), e agrupando a demanda por
     **padrao de rota** (`/redesocial/tema/jurisprudencia/stj-tema-*`,
     `/.well-known/*`, `/mcp/.well-known/*`).
   - **grava**: `data/ops/edge_agent_404_demanda_daily.jsonl` + a fila de
     pedidos nominados em `data/ops/demanda_de_agente_pendente.jsonl`
     (rota pedida, quantas vezes, por quem, desde quando) — que e a entrada
     direta da fabrica de paginas.

3. `tools/check-edge-leitura-de-agente` (gate, read-only)
   - **reprova por FLUXO, nao por nivel** (precedente do repo: gate vermelho por
     estoque que nada drena): (a) rota 404 pedida por AI Crawler verificado por
     ≥ 3 dias seguidos e nao presente na fila de producao; (b) descritor de
     maquina anunciado em `internal/agentsurface` com 404 na borda; (c) queda
     > 50% em 3 dias de `gemea_md` ou `/mcp` sem deploy correspondente;
     (d) `csp-report` acima de zero — relatorio de CSP e defeito, nao metrica.

4. `tools/generate-mcp-ferramenta-invocada-daily` (gerador, escreve) — **a
   lacuna mais grave que eu achei.** Houve **13.364 POSTs JSON-RPC em `/mcp` em
   8 dias** e **nenhum registro de qual ferramenta foi invocada**: o nome vive no
   corpo JSON-RPC, o log do nginx so tem o caminho, e o unico artefato que ja
   mediu isso — `data/ops/mcp_consumo_externo.jsonl` — tem **1 linha, escrita em
   2026-08-13 12:10**, sobre uma janela de 12 h. O portal nao sabe se alguem
   usou `ler_pagina`, `buscar_semantico`, `grafo` ou `responder_pergunta`.
   Instrumentar no handler MCP do Go (contador por `method`/`tool`, por dia, sem
   corpo de requisicao), gravar em `data/ops/mcp_ferramenta_invocada_daily.jsonl`.
   Sem isso, o §12 do contrato ("a metrica que vale e retorno e citacao por
   agente") nao tem numerador para a superficie que o proprio contrato chama de
   produto.

5. **Correcao de instrumento, nao ferramenta nova**: `cmd/social/cspreport.go`
   grava `diretiva` + `origem` (esquema+host) e **descarta o caminho do
   `blocked-uri` por desenho**. Com origem = a nossa propria, a linha gravada nao
   distingue "script `/x.js` bloqueado" de "script `/y.js` bloqueado" — 243
   violacoes/dia e nenhuma pista de qual elemento. O conserto que respeita a
   razao do desenho (nao gravar texto livre do cliente) e um **vocabulario
   fechado de caminho**: allowlist dos caminhos que o portal de fato serve, mais
   `outro`.

6. Duas lacunas de MEDICAO que nenhum instrumento deste projeto cobre hoje, e
   que eu **nao medi** nesta colheita (declarado como nao medido, com o porque):
   - **retencao de 8 dias**: a borda nao guarda serie longa. Sem um coletor
     diario gravando no disco, toda pergunta historica sobre agente e
     irrespondivel — as rajadas de 09-09 (gptbot 36.671) e 09-11
     (meta-externalads 33.365) **desaparecem em 2026-09-17**.
   - **IP verificado por faixa oficial**: `verifiedBotCategory` vazio nao
     significa "falso" (a Cloudflare nao verifica PerplexityBot). Os 390 404 de
     "perplexity" ficam ambiguos entre agente real e scanner disfarcado. O
     projeto ja tem `data/ops/bot_ip_ranges/*.json`; falta cruzar `clientIP`
     com a faixa na MESMA consulta — o que `generate-bot-agents-daily` ja faz
     para volume e ninguem faz para ROTA.

---

## ALAVANCAS, cada uma com o numero que a sustenta

1. **Gate de coerencia de superficie que cubra o link do acervo para a rede
   social** — nao "produzir 754 paginas". A medicao (secao 5A) mostra que
   1.114 dos 1.118 404 de `stj-tema-*` cairam em 48 h porque o HTML publicado
   anunciava rota que o processo social ainda nao servia, e cessaram no start de
   2026-09-11 03:08:16. O que resta a consertar sao **141 requisicoes**:
   `tema/leis/*` (89, estrutural — `cpc-art-321` da 404 hoje) e
   `tema/noticias/*` + `tema/diarios/*` (52, rotas com data que continuam
   anunciadas depois de expirar). `TestSuperficieDeAgenteSoAnunciaRotaViva` ja
   cobre `agentsurface.Servicos`; **nao cobre o link acervo → rede social**, que
   e onde o vazamento ocorreu. Custo: um gate. Ganho: nenhuma varredura de IA
   volta a queimar mil requisicoes num 404 nosso.
2. **Publicar os 10 descritores de maquina que dao 404** (242 req/8 dias):
   `glama.json` (86), `mcp/.well-known/oauth-authorization-server` (31),
   `mcp/.well-known/mcp` (31), `x402` (16), `owners.json` (16), `ard.json` (10),
   `openid-configuration` (7), `mcp.json`/`mcp-server.json` (7), `agents.txt`.
   Custo: arquivo estatico. Ganho: entrada nos diretorios de MCP que hoje
   registram o portal como incompleto — 8.426 requisicoes/8 dias de 40+
   operadores ja batendo.
3. **Encher /redesocial/**: e a superficie mais lida por IA (gptbot 23.105,
   amazonbot 8.420 em 8 dias) e `comentarios_de_autoridade = 0`. DEC-059 ja
   autoriza o cerebro a publicar por lá.
4. **O feed Atom por tema e o canal que a IA ja escolheu**: 12.213 de 12.801
   (95,4%) vem de gptbot + amazonbot, em 5.258 rotas. Densificar `feed.xml` por
   tema (corpo completo, URN LexML, link para a gemea) atinge o consumidor que
   ja esta lá — sem custo de descoberta.
5. **Consertar a CSP que o Applebot reporta — e primeiro gravar o `blocked-uri`**:
   `script-src-elem` subiu de 0 para **243/dia** em 7 dias, origem = nossa
   propria, e o script do portal **nao** e o bloqueado (hash confere byte a
   byte). Como o agregador reduz `blocked-uri` a esquema+host por desenho, o
   caminho do elemento bloqueado nao existe em lugar nenhum — **a correcao do
   instrumento precede a correcao da CSP**: gravar o caminho normalizado contra
   vocabulario fechado (allowlist de caminhos conhecidos + `outro`), nunca texto
   livre. 45% do orcamento do Applebot se gasta relatando isso.
6. **Eliminar os 17.759 redirecionamentos de 301, por DUAS rotas distintas**
   (medido por sonda, secao 4.3): barra final ausente → resolve **shapbot 2.391
   e parte do meta 5.786**, emitindo a URL com barra em sitemap, feed, gemea e
   `Percursos por fundamento legal`; esquema http → **nao se resolve emitindo
   nada**, sao 5.708 do baiduspider vindos do indice http dele, e o unico
   instrumento e HSTS com preload (ja ha 301 correto). Tratar as duas como uma
   causa so foi o erro que eu corrigi.
7. **`gptbot` corrige o pressuposto do canal de maquina**: 48,7% da leitura dele
   e `index.md`. A gemea funciona — para quem varre. Para quem responde
   (0,036%), a alavanca e a URL que esta no INDICE, nao a densidade do documento.
8. **Zero 429 e zero 304 em agente de IA** liberam duas frentes: nao ha teto de
   taxa a negociar, e republicacao nao rebaixa agente de IA (o risco de mtime/ETag
   vale para 117 requisicoes de bingbot+googlebot em 8 dias, nao para as 144.524
   de IA).
9. **Amazonbot e o perfil-alvo**: 96% do seu consumo e maquina-nativo
   (redesocial 36% + gemea 33% + feed 28%), HTML so 4%, e cresceu 215x em 8 dias.
   E a prova viva de que a arquitetura AI-first funciona quando o agente a
   descobre.

---

## O que o advisor mudou

Ele **derrubou uma alavanca inteira e corrigiu tres numeros**. Nao foi cosmetico:

1. **Alavanca #1 reescrita do zero.** Eu tinha afirmado a causa ("os agentes
   vieram do sitemap e a rota nao existe") sem medi-la, e concluido "produzir
   754 paginas". Ele listou as tres causas candidatas e o comando que as separa.
   Medi: a rota devolve **200 hoje**, `1.114 dos 1.118` 404 cairam em 48 h,
   o processo social comecou em **2026-09-11 03:08:16**, o sitemap da rede social
   tem **38 `<loc>` e ZERO rota `tema/`**, e quem anunciava era o **HTML do
   acervo**. Era defeito de coerencia de superficie, ja fechado; o residuo real
   e **141 requisicoes**, nao 754 paginas. Sem essa chamada eu teria mandado a
   fabrica produzir conteudo para um problema que nao existia.
2. **Alavanca #6 partida em duas causas.** Ele apontou que meu proprio exemplo
   (`/transito/…/` COM barra levando 301) refuta "barra final". Sondei:
   `http` + barra → 301 (esquema, baiduspider 5.708) e `https` sem barra → 301
   (barra, shapbot 2.391). A dimensao `clientRequestScheme` **nao existe nesta
   zona** (erro literal da API), o que virou uma linha de "nao medido na borda,
   medido por sonda".
3. **Erro numerico na secao 5A corrigido**: eu escrevi 1.293 como "verificado
   pela Cloudflare"; a minha propria tabela dizia **870**. Corrigido, com a
   composicao das outras 423.
4. **Classe "busca para responder" reconstruida**: ele apontou que
   `meta-externalads` e crawler de anuncio e `petalbot` e buscador da Huawei —
   nenhum busca para responder. A classe defensavel virou 21.021 HTML contra 8
   gemeas = **0,038%** (o veredito nao mudou, a classe ficou a prova de
   objecao), e a composicao dos 144.524 do cabecalho passou a ser declarada.
5. **`/mcp` medido uma camada abaixo**: ele desconfiou de eu chamar
   `node`/`aiohttp`/`python-httpx` de "cliente generico". Parti por metodo:
   **POST 13.364 (89,8%)** — sessao JSON-RPC real, nao ping — contra 1.473 em
   GET/HEAD/DELETE levando **405**. E fui a origem: 2.387 linhas de `/mcp` no
   log de 09-14, mas o nome da ferramenta vive no corpo, e
   `data/ops/mcp_consumo_externo.jsonl` tem **1 linha de 2026-08-13**.
6. **CSP: de "causa desconhecida" para diretiva nomeada.** Ele disse para ler o
   que o handler faz com o corpo. Achei
   `var/social/csp_violacoes_agregadas.jsonl`: diretiva `script-src-elem`
   subindo **0 → 243/dia**, origem = a nossa. Depois refutei a hipotese mais
   grave: o hash do script inline **confere byte a byte** com o CSP servido, a
   borda devolve HTML identico (21.680 bytes) e os quatro injetores da
   Cloudflare estao `off`. O que sobra ficou declarado como nao medido, com o
   motivo (o agregador descarta o caminho por desenho; sair como navegador e
   proibido).
7. **"215x em 8 dias" saiu** — sobre base 16 e inflacao de leitura. Virou
   "de ~0 a 3.446/dia".

Nao contrariei nada que ele disse. Onde ele levantou hipotese que a medicao
derrubou — a de que os 404 poderiam ser demanda genuina extrapolada (causa `c`) —
a propria medicao que ele mandou fazer foi a que decidiu.
