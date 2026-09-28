# MOTOR DE CITAÇÃO — arquitetura de crescimento IA-first

Frente: ALAVANCAGEM IA-FIRST. Sessão 2026-09-15, PLAN MODE, somente leitura.
Todo número declara a CAMADA. O que não medi nesta sessão está marcado.

---

## 0. A TESE, EM TRÊS FRASES

**O identificador de versão que este portal serve a máquinas está errado em
10.070 de 10.070 páginas (100,0%)** — a gêmea anuncia `version: sha256:e37dba50…`
enquanto os bytes servidos hasheiam `8123d77e…` —, e o comentário do próprio
código diz que "um identificador que não bate com o artefato publicado é pior
que identificador nenhum". A classe de agente que produz resposta gerada lê
**HTML** (3.352 req/24 h na borda, das quais 26 tocam a gêmea), e o teto da
citação no Copilot hoje não é conteúdo nem descoberta: é **cobertura de índice
— 7.158 de 11.106 (64,5%)**, subindo sozinha a +448/dia, sem alavanca nossa que
a acelere (o IndexNow foi medido como não movendo o bingbot). Logo o crescimento
se compra em dois eixos separados: **volume** (corpus → geradores parados →
páginas que entram no índice no mesmo ritmo) e **citabilidade** (consertar a
versão, unificar o título, validar a URN) — e o instrumento de borda tem de
nascer **hoje**, porque a retenção é de 8 dias e em 2026-09-17 toda a colheita
desta sessão fica irreproduzível.

---

## 1. O QUE EU MEDI NESTA SESSÃO

Doze medições próprias. Cada uma corrige ou confirma uma linha do dossiê.

| # | Medi | Resultado | Efeito |
|---|---|---|---|
| **M0** | `content_sha256` do `anchor_claim_publication.jsonl` × `html_sha256` do `published_manifest.jsonl`, rota a rota | **10.070 de 10.070 divergem (100,0%)**; mais 1.036 rotas do manifesto sem versão anunciada | **defeito central**, §2.0 |
| M0b | `curl \| sha256sum` dos bytes servidos vs manifesto vs gêmea | bytes = `8123d77e…` = manifesto ✓; gêmea diz `e37dba50…` ✗ | prova do M0 num caso |
| M0c | `stat` do `anchor_claim_publication.jsonl` | mtime **2026-08-26 14:16:49** — 20 dias congelado | a causa raiz |
| **M1** | `rel=` no HTML servido + `Link:` do nginx | `rel="alternate" type="text/markdown"` **presente** nos dois | refuta "falta anunciar a gêmea" |
| **M2** | `grep -c 'index.md' data/ops/indexnow_url_state.jsonl` | **2.295** | o IndexNow já entrega a gêmea |
| **M3** | `grep -c sha256` no HTML servido | **0** | o HTML não tem versão nenhuma |
| **M4** | `os.walk` em `public/`, todo `index.html` | N=**11.357**, max **38.466 B**, p99 30.040, p50 23.162; zero acima de 45 KB | folga de **12.734 B no pior arquivo** |
| **M5** | `cat -A` no byte servido de `/autonomos/cobranca-prescricao/index.md` | `urn:…13105!art240\_par1` — contrabarra no corpo | confirma a corrupção da URN |
| **M6** | `POST /mcp` com `Mcp-Method: initialize` | `capabilities` = `{"logging":{},"tools":{"listChanged":true}}` | zero `resources` sobre 11.106 páginas |
| **M7** | `cursor.json` do corpus STJ, soma por dataset | **4** datasets, 60.221 registros; 1ª Turma em **3 de 52** meses | "aborta por arquivo de 599 bytes" — 599 é `registros`, não bytes |
| **M8** | `<title>` × `<h1>` × front matter × `/api/v1/citar` | `<title>`/`headline`/`citar` **concordam**; gêmea e CSL usam o **H1** | a divergência é 3-contra-1 |
| **M9** | série `rastreio_diario` do ledger do Bing | InIndex **2.939 → 7.158** (09-02→09-13), monotônica, **+448/dia**; **64,5%** de 11.106; faltam 3.948 | **o teto real da citação**, §2.1 |
| **M10** | `systemctl show … -p OnFailure` | `wikijuridica-bing-submit` e `-ai-citation` **têm** `OnFailure=wikijuridica-alerta@…` | exit ≠ 0 diário = alerta falso ao dono |
| **M11** | fila do cérebro (`fila.sqlite?mode=ro`) | `extrair_dispositivos` pendente **34.118**; `medir_modelo` pendente **3** | §6 |

**Duas coisas que pareciam lacuna e são desenho correto** — não mexer:

- **`rel="cite-as"` ausente no HTML é deliberado.** `internal/httpserver/markdown.go:359-363`: no HTML a URL já É a canônica, e `cite-as` para si mesmo "é uma tautologia que não instrui ninguém".
- **A gêmea fora do sitemap é decisão de SEO.** `tools/test_generate_indexnow_gemea_markdown.py:17-19`: "não está lá por decisão de SEO, não por não existir (§7: o canal de máquina tem caminho próprio para não dividir chave de cache)".

**Denominadores, declarados por métrica daqui em diante:** `content/pages.json`
11.118 · `published_manifest` **11.106** · grafo 11.104 · temas sociais 11.039 ·
`public/index.html` **11.357** (inclui hubs) · vetores 11.248 · rotas com versão
anunciada **10.070**.

---

## 2. LEVER 1 — AS ALAVANCAS, EM DOIS EIXOS

O 128× de alcance (abaixo) decide **onde mora o aparato de citação**. Ele **não**
decide o que faz a citação crescer — e confundir as duas perguntas seria a
falha de raciocínio deste plano. Por isso: dois eixos.

Na borda, 24 h: classe que **responde** (ChatGPT-User 1.115 + oai-searchbot
1.233 + Applebot 530 + PerplexityBot 363 + Googlebot 111) = **3.352**, das quais
**3.326 no HTML** e **26 na gêmea** → **128×**. A classe que **varre** (GPTBot,
Amazonbot, Baiduspider, ShapBot) lê a gêmea a 35–58%.

### 2.0 · O DEFEITO QUE VEM ANTES DE TODA ALAVANCA (M0)

`internal/content/content.go:175-190` define `ContentSHA256` como "o html_sha256
que o published_manifest já grava por rota" e promete: *"baixar a página e
recalcular o sha256 do HTML tem de dar o mesmo número"*; e fecha com *"Nunca
inventar um hash local: um identificador que não bate com o artefato publicado é
pior que identificador nenhum."* `internal/pagemarkdown/frontmatter.go:173-179`
emite esse valor como `version:` e repete a promessa no comentário.

**A promessa é falsa em 100,0% do acervo.** O valor não vem do manifesto: vem de
`data/editorial/anchor_claim_publication.jsonl` (via
`internal/content/anchorclaim.go:213-214`, `pages[i].ContentSHA256 = sha`), um
arquivo **congelado em 2026-08-26 14:16:49**. Desde então toda republicação
mudou o HTML e não mudou esse arquivo.

Consequências que ordenam o plano inteiro:

1. **Consertar antes de propagar.** Emitir `page.ContentSHA256` no JSON-LD hoje carimbaria o **mesmo valor errado** em 11.106 páginas — transformando um defeito de um canal em defeito de dois.
2. **A fonte certa já existe e já confere:** `published_manifest.html_sha256`, que é o que a transação de publicação produz e que eu conferi byte a byte contra o corpo servido.
3. **1.036 rotas** estão no manifesto e **não** no `anchor_claim`: hoje não anunciam versão nenhuma. Com a fonte trocada, passam a anunciar.
4. Isto é **defeito de citabilidade**, não de SEO: um agente que tentasse verificar nossa versão falharia 10.070 vezes em 10.070.

### 2.1 · O TETO REAL DA CITAÇÃO, E QUE ELE NÃO É NOSSO (M9)

O Copilot só cita o que o Bing indexou. Medido no ledger do próprio Bing:

| Data | InIndex | Data | InIndex |
|---|---|---|---|
| 2026-09-02 | 2.939 | 2026-09-09 | 5.049 |
| 2026-09-05 | 4.022 | 2026-09-11 | 5.872 |
| 2026-09-08 | 4.667 | **2026-09-13** | **7.158** |

**+3.136 em 7 dias = +448/dia, monotônico. 64,5% de 11.106. Faltam 3.948** — que,
nesse ritmo, fecham por volta de 2026-09-22.

**Nenhuma alavanca nossa acelera isso, e isso está medido, não suposto:**
`tools/check-descoberta-do-bing:18-26` registra que a submissão de 2.679 URLs por
IndexNow em 12/08 rendeu **45 requisições** naquele dia, que 1.313 delas (49%)
seguiam nunca pedidas 24 dias depois, e conclui — depois de medir os quatro
canais — que "nenhum canal nosso está quebrado; o gargalo é o ritmo com que o
Bing absorve um domínio novo, e ele melhora em todas as séries".

**O que isso muda no plano:** (a) ~35% do acervo é hoje **incitável no Copilot
por construção**, e nada a fazer além de esperar a curva; (b) a régua de
crescimento de citação é **páginas novas entrando na esteira**, que absorvem no
mesmo ritmo; (c) **não quebrar o que já está indexado** vale mais que qualquer
otimização — o que se traduz numa proibição concreta em §5.

### 2.2 · EIXO VOLUME — o que faz existir página citável

| Ordem | Alavanca | Ganho medido/derivado | Custo |
|---|---|---|---|
| **V1** | **L7 · corpus: 6 datasets ausentes + 1ª Turma** | destrava as 4 maiores demandas do país; é **pré-requisito duro** de V2/V3 | ~361 req × Crawl-Delay 10 ≈ **1 h** |
| **V2** | **L3 · `generate-lei-artigo-pages` no mapa** | responde ao caderno de 404 assinado por nós (**865 de 1.297 com Referer nosso**); CPC servível hoje (50.076 citações) | **1 linha** + env |
| **V3** | **L4 · `generate-acordao-pages` no mapa** | dossiê diz 2.488 páginas — **não medido nesta sessão** | **1 linha** + env |

**L7 é primeiro por dependência lida, não por preferência.**
`cmd/generate-lei-artigo-pages/main.go:249-253` **recusa** o candidato quando o
corpus não tem acórdão citando a URN (`corpus_sem_acordao_para_a_urn`). Com o
corpus 97,4% 3ª+4ª Turma (M7), execução fiscal, IPTU, previdenciário e criminal
**não se atendem hoje nem subindo limite nenhum**. Inverter a ordem produz página
recusada uma a uma, com o custo pago e nada no ar.

`internal/stjacordaos/fonte.go:23-32` lista **10** datasets; o cursor tem 4.
Ausentes: corte-especial, primeira-secao, terceira-secao, segunda-turma,
quinta-turma, sexta-turma. Mapa demanda→órgão:

| Demanda nacional [disco, DataJud] | Órgão | Cobertura hoje |
|---|---|---|
| execução fiscal 20,16 M · IPTU 12,68 M | 1ª/2ª Turma, 1ª Seção | 862 de 60.221 |
| auxílio por incapacidade 6,59 M | 1ª/2ª Turma | idem |
| tráfico 3,22 M | 5ª/6ª Turma, 3ª Seção | **zero** |

**Teto físico externo e medido, não margem própria:** `robots.txt` do STJ declara
**Crawl-Delay 10** e o coletor nunca vai mais rápido
(`cmd/collect-stj-acordaos/main.go:19-22`). Derivado: (6 × 52) + 49 ≈ **361** req
≈ 1 h. Dossiê diz 391 competências; a diferença não muda decisão.

**Mecanismo de V2/V3, pronto:** `tools/run-daily-content:369-373` tem **cinco**
geradores no mapa `GERADORES`; os dois acima **não estão lá** (só num comentário
em `:446-447`). O timer `wikijuridica-daily-content.timer` está **ativo**
(verificado). `internal/tetodelote` garante que o limite governa **apenas o que
se acrescenta** — publicada não consome cota (`:359-361`) — e o valor vem de env
`WIKI_LIMITE_<CANAL>`. **Pré-requisito:**
`data/editorial/motor/tier_a_artigos.jsonl` tem **255 linhas, mtime de 10/set**;
`tools/generate-motor-tier-a` roda antes, senão V2 drena 255 e para.

### 2.3 · EIXO CITABILIDADE — o que faz a página existente ser citável

| Ordem | Alavanca | Ganho medido | Custo |
|---|---|---|---|
| **C1** | **Trocar a fonte da versão** para `published_manifest.html_sha256` | corrige **10.070 de 10.070** e dá versão a **+1.036** | 1 fonte de dado |
| **C2** | **Versão + identificador no JSON-LD do HTML** | alcança **3.326 req/24 h** da classe que cita; hoje `grep -c sha256` = **0** | struct + schema, **mesmo commit** |
| **C3** | **Unificar o título citável** | 87,5% de divergência (M8) | **1 linha**, oráculo pronto |
| **C4** | **Corrigir a URN corrompida** | 356 URNs de parágrafo inválidas (M5) | **1 linha**, oráculo no JSON-LD |
| **C5** | **MCP `resources`** | 1.671 sessões SDK/dia que só podem chamar ferramenta | **1 call site** |

**C2 — as duas travas, ambas verificadas por leitura:**
1. `internal/structureddata/structured_data.go:2511` tem `"additionalProperties": false` no schema do Article, e o comentário de `:2549-2553` diz "o schema fecha propriedades de propósito, então a régua aprende junto com o emissor". Campo na struct (`:115-127`) **sem** a propriedade no schema (`:2542-2556`) reprova o documento inteiro. **Duas edições, um commit.**
2. **Nada de bloco em prosa.** `internal/render/author_credential_test.go:41-43` exige `strings.Count(visivel, "OAB/RJ 227191") == 2` sobre `semDadoEstruturado(html)`, e `internal/pagemarkdown/citacao.go:241-243` mostra que a linha de citação da gêmea **carrega a credencial** — seria a terceira ocorrência visível, teste vermelho por sobriedade do Provimento 205/2021. O dado estruturado está **fora** da contagem por construção (`:37-40`). O caminho certo é o que o próprio teste abriu.

Forma: `"version": "sha256:<html_sha256>"` e `"identifier"` com o canonical —
ambas propriedades de `CreativeWork` no schema.org, sem vocabulário inventado.

**C3:** `internal/pagemarkdown/render.go:285` faz
`titulo := primeiroNaoVazio(page.Heading, page.Title)`. Três superfícies usam
`page.Title`; uma usa `page.Heading`. **Vence `page.Title`** — minoria cede: uma
linha contra três superfícies, e `page.Title` é a string que o índice guarda, que
é o que torna a referência resolvível para quem chegou pelo índice. Oráculo:
`apiCitacao.Title` (`internal/httpserver/api_citar.go:150`).

**C4:** `internal/pagemarkdown/render.go:485` passa a URN por `escapaTexto`
**dentro de code span**; `blocks.go:100-113` escapa `_` como `\_` e o CommonMark
**não** processa escape entre backticks. Provado no byte servido (M5). O oráculo
está no próprio objeto: o JSON-LD do HTML já serve as URNs bem formadas.

**C5:** `servidor.AddResourceTemplate(...)` em `internal/httpserver/mcp.go:238-243`.
A capability **aparece sozinha**: `go-sdk@v1.7.0/mcp/server.go:645-652` —
`if … s.resourceTemplates.len() > 0 { caps.Resources = &ResourceCapabilities{ListChanged: true} }`.
E o **transporte já está preparado**: `internal/httpserver/mcp.go:1866-1873` tem
`case "resources/read":` lendo `params.uri` "e não `params.name`: é o que a tabela
da spec manda". Ainda assim, P8 confere `mcp_method_derivado_test.go` e
`mcp_recusas_transporte_test.go` antes de afirmar que não há encanamento.

### 2.4 · MEDIDO COMO FECHADO — não são tarefas
- **Gêmea no sitemap:** três canais já ligados (M1, M2), 0,038% de adesão de quem cita, exclusão deliberada por chave de cache, e a gêmea serve `Link: rel=canonical` para o HTML — até o índice que a absorvesse resolveria para o HTML. **Ganho esperado ≈ 0.**
- **Densidade da gêmea:** 26 de 3.352. Rende sobre 0,8% de quem cita. É retorno de **varredura**, não de **citação** — e a frente é citação.

---

## 3. LEVER 2 — A ROTINA DE MEDIÇÃO QUE FECHA O CICLO

### 3.1 · BORDA = VOLUME · `tools/generate-edge-leitura-de-agente-daily`
- **Mede:** por dia e por `agent_key`, requisições partidas em classes de rota — `html_acervo`, `gemea_md`, `redesocial`, `feed_atom`, `api_v1` (por endpoint), `mcp` (por método), `a2a`, `well_known` (por descritor), `sitemap`, `assets`, `sem_barra_final` — com `status`, `cacheStatus`, `verifiedBotCategory` e **`papel`** (responde/varre/treina) em coluna própria.
- **Reusa:** `tools/cloudflare_auth.py` (fonte única de credencial), `tools/botagents.py` (mapa `FUNCAO`), `tools/edgetelemetry.py` (helper GraphQL). As consultas já existem em `/tmp/borda_*.py` desta sessão — foram pagas e devem sair de `/tmp` para `tools/`.
- **Grava:** `data/ops/edge_agent_reading_daily.jsonl`, `edge_agent_reading_v1`, append-only, `camada: "borda"` na linha.
- **Periodicidade:** diária, unit própria, 1 dia por chamada (o plano Free recusa janela maior).
- **Exit:** 0 coletado · 1 consulta falhou · 2 sem credencial ou API fora · 3 janela já coletada (idempotente). **Sem `OnFailure` na unit** enquanto 3 for caminho normal — ou 3 vira alerta diário (M10).
- **Três armadilhas obrigatórias, porque as três enganaram esta sessão:** (a) contagem por `clientRequestPath_like`/`_notlike` **exata**, nunca pela dimensão crua — ela **truncou em 09-09, 09-10, 09-11 e 09-12**; (b) `userAgent` **íntegro** — truncar em 120 chars jogou **OAI-SearchBot inteiro** (12.118 req) no balde "navegador", porque os agentes põem o token no FIM de um UA em forma de navegador; (c) separação interno/externo por UA — **73,0%** da borda (866.020 de 1.186.321 em 8 d) é aquecimento nosso.
- **Controle positivo antes do zero:** a soma das classes mais "outro" tem de fechar com o total obtido **sem dimensão** (não truncável). Sem isso, um padrão `_like` errado produz série falsa em silêncio.
- **Por que HOJE:** retenção de **8 dias**. As rajadas de 09-09 (GPTBot 36.671) e 09-11 (meta-externalads 33.365) **somem em 2026-09-17**. Sem ele, o gate de §3.4 não tem linha de base e esta colheita é irreproduzível. **É o item mais urgente do plano.**

### 3.2 · BING = CITAÇÃO · bloco `ia` em `tools/collect-bing-webmaster`
- **Estado da API, confirmado na fonte:** **não existe** método para o relatório de IA. Resposta aceita na Microsoft Q&A, 2026-02-19: *"In the Blog post, no API is mentioned so the answer is not right now."* Nesta sessão, 40 nomes candidatos deram 404 e `$metadata` também. **Outro agente está caçando o método — meu entregável é o encaixe, não a caça duplicada.**
- **Encaixe:** entrada nova no dict `BLOCOS` (`tools/collect-bing-webmaster:111-116`), reusando `Ritmo` (10 req/62 s; a 11ª leva `ThrottleHost`), o ledger append-only e o cursor. Grava no mesmo `bing_webmaster_daily.jsonl` os tipos `ia_citacao_diaria`, `ia_pagina_citada`, `ia_consulta_de_fundamentacao`.
- **A regra de saída, corrigida por M10:** `wikijuridica-bing-submit.service` **tem** `OnFailure=wikijuridica-alerta@…`. Portanto **a execução padrão termina em 0** e grava no ledger `api_disponivel: false` com a data; o exit **3** ("método ainda indisponível") só existe sob `--so ia` explícito. **O gate de §3.4 lê o campo do ledger, nunca o exit code.** A sonda gasta **≤ 2** das 10 requisições da janela numa lista curta — não 40.
- **A linha de base dos ~23.000, com proveniência no schema:** `tipo: "ia_painel_leitura_manual"`, `camada: "painel-bing"`, `metodo: "leitura-do-painel"`, `api_disponivel: false`, `citacoes: 23000`, `precisao: "ordem-de-grandeza-lida-no-painel"`, `lido_em`, `lido_por: "titular-da-conta"`. É **fato medido pela Microsoft e exibido na conta do dono** — o estágio de preview qualifica a API, nunca o número. Mas é **leitura de painel**, não série, e o schema diz isso.
- **E o campo que já existe e importa mais:** `InIndex` do `rastreio_diario` é o **teto** da citação (§2.1) e já é coletado. O painel o exibe ao lado do número de citação, sempre.

### 3.3 · ORIGEM = SÓ O QUE É DELA · `tools/measure-ai-citation` (existe, com timer ativo)
Já declara `is_citation_count: false` e `interpretation: "considered_for_answer"`
em cada registro. **Um ajuste:** é o **único** canal que alcança o clique de volta
— a borda no plano Free nega `clientRequestReferer` —, e o painel deve dizer isso
ao lado dela. A camada `fetch` (2.638 em 36 d) é piso por construção; o HIT de
64–75% nos assistentes [borda] mede o tamanho do piso.

### 3.4 · O GATE — e por que ele NÃO se chama "citação não regride"
Chamá-lo de gate de citação seria mentira: citação não é observável por dia em
camada nenhuma deste projeto, e nomear instrumento pelo que ele não mede é o
defeito que o §R2 proíbe. Nome: **`tools/check-leitura-de-agente-nao-regride`**.
Ele reprova a **leitura pela classe que responde**, o antecedente mensurável mais
próximo da citação. Estende o padrão de `tools/check-descoberta-do-bing`
(read-only, teto **dia a dia** dentro da janela — depois de a versão acumulada ter
escondido dois dias acima do teto).

**Régua pré-registrada — resultado → veredito → ação, ANTES de qualquer número:**

| Condição | Exit | Ação |
|---|---|---|
| agente da classe `responde`: mediana de 3 d de `html_acervo` cai além do limiar contra a mediana de 14 d **e** não há publicação correspondente na janela | **1** | investigar o canal, nunca afrouxar o teto |
| rota 404 pedida por **AI Crawler verificado** em ≥ **3** dias seguidos **e** ausente da fila de produção | **1** | entra em `data/ops/demanda_de_agente_pendente.jsonl` |
| descritor anunciado em `internal/agentsurface` com 404 na borda | **1** | corrige o anúncio ou serve a rota |
| `csp-report` acima de zero | **1** | relatório de CSP é **defeito**, não métrica |
| `InIndex` cai contra o dia anterior | **1** | regressão de indexação — o teto encolheu |
| série com menos de 14 dias, ou `api_disponivel: false` no bloco `ia` | **2** | "não sei" — nunca verde por falta de dado |
| nenhuma das acima | 0 | — |

**As constantes, honestamente rotuladas:**
- **≥ 3 dias é DERIVADO e eu digo de quê:** 1.114 dos 1.118 404 de `/redesocial/` se resolveram em **48 h** [origem]. Três dias é estritamente maior que o atraso medido de sincronismo, então não confunde lag com demanda desatendida.
- **O limiar de queda e a janela de 14 d são PROVISÓRIOS**, e o plano diz o método em vez de inventar número: calibram-se sobre os **primeiros 14 dias** da série de P1, com o limiar em N desvios da variação dia-a-dia da mediana de `html_acervo` da classe `responde`. Até lá o gate roda em exit 2 (observa e não reprova). **Atenção medida:** a classe dobrou em 8 dias (chatgpt-user 542→1.092), então limiar simétrico exige a cláusula de deploy que a tabela já tem.

**Por que por FLUXO e por AGENTE, nunca um limiar global fixo:** a série tem
**três regimes medidos** — cresce (amazonbot ~0→3.446/dia, applebot 81→523, SDK
no `/mcp` 461→898), cai (cf-ai-search 21×, perplexitybot 13×) e estoura em rajada
(gptbot 36.671 num dia). Um limiar global reprovaria no primeiro dia pelo
cf-ai-search e passaria verde com o amazonbot sumindo.

**Duas travas que eu confirmei NÃO existirem, e isso libera a frente:** **304 = 0**
em todo agente de IA (só bingbot 109 e googlebot 8 em 8 dias) — o aviso do
contrato sobre republicação rebaixar o acervo vale para 117 requisições, não para
as 144.524 de IA; e **429 = 0** em toda a tabela. **Publicação frequente de
conteúdo novo não tem custo medido em agente de IA.**

### 3.5 · O painel de três camadas
Estende `wikijuridica-painel.timer` (ativo). Cada número sai com a camada e
**nunca se soma entre camadas**: borda = volume (73,0% dela é aquecimento nosso,
marcado e fora da conta), Bing = citação **com `InIndex` ao lado como teto**,
origem = só o que é dela. `ORIGEM ≤ BORDA` sempre, e o quociente é **fan-out de
cache, não erro** — tratá-lo como erro levaria a "consertar" duas ferramentas
corretas.

**A ponte que não existe, dita com clareza:** entre "o agente leu" e "o agente
citou" **não há camada neste projeto, e nenhuma medição de borda a produz**. Isso
não é motivo para não medir — é motivo para o painel jamais apresentar leitura
como citação.

---

## 4. LEVER 3 — AS GROUNDING QUERIES COMO PAUTA EDITORIAL

São as consultas que o Copilot gera internamente para buscar conteúdo — a pauta
mais valiosa do projeto — e estão **indisponíveis por API** pelo mesmo motivo de
§3.2. O laço roda com proxies hoje e recebe o dado real no mesmo encaixe quando o
método aparecer, **sem redesenho**.

### Colher — três fontes, três camadas
1. **`consulta_diaria` do Bing** — 229 consultas, 440 impressões, 77 cliques (08-21 a 09-11) [painel-bing/API]. É **busca clássica**, declarada **proxy**, nunca citação de IA.
2. **O caderno de 404 assinado por nós** — 1.297 em 7 dias, **865 com Referer de 865 páginas nossas** [origem, travessia 98,7%]. Única fonte que é **demanda de agente real**, não proxy, e é de graça.
3. **A taxonomia que o agente presume** — uma página por artigo de código (`cpc-art-536`, `cc-art-167`) e uma por tribunal por dia (`stf-20260908`). Sai dos próprios 404.

### Cruzar — o conserto é do CRITÉRIO, não do gerador
`tools/generate-datajud-corpus:152-183` faz
`return [caminho for caminho, vocab in paginas if distintivos & vocab]` — **OR de
um token**. Reproduzido: 4,46 assuntos por página, 391 de 400 assuntos "cobertos"
(97,8%), "fiscal" casando bagagem aérea com execução fiscal. Enquanto for esse
critério, "9 assuntos descobertos / 2.589.576 processos" é **número inválido** e
não entra em decisão nenhuma.

**O critério certo já está no disco:** `buscar_semantico`, **11.248 vetores**, dim
1024, zero página publicada sem vetor. Consulta → página por significado, com
limiar **derivado de medição**: calibra-se sobre as 229 consultas do Bing, cujo
par consulta↔página o próprio `GetQueryPageStats` já entrega (`consulta_pagina`,
`pagina_consulta` no ledger) — **há conjunto rotulado sem coletar nada**.
Conserta-se o produtor existente; não nasce ferramenta nova.

### Cruzar com a demanda do DataJud — com a ressalva que ordena o trabalho
Maiores demandas [disco]: execução fiscal 20,16 M · dano moral 12,90 M · IPTU
12,68 M · dano material 8,60 M · inclusão indevida 6,98 M · auxílio por
incapacidade 6,59 M · tráfico 3,22 M. Cobertura por mérito: consumidor 78,0% (a
única grande demanda bem servida) contra tributário 26,6%, criminal 22,1%,
previdenciário 12,7%.

**A ressalva é causal:** essas áreas não se atendem hoje nem subindo limite
nenhum (§2.2, `main.go:249-253`). Logo **hoje** o laço gera onde o corpus
sustenta — CPC (50.076 citações) e CC (11.945) → os `leis/cpc-art-*` que os 404
pedem; e **V1 primeiro** destrava o resto.

### Gerar → Medir
Gerar: V2/V3 pelo mapa `GERADORES`, com `--seco` antes para saber o número real.
Medir: o `agent_key` da rota nova no coletor de §3.1, a página no bloco `urlinfo`
do Bing — que já escolhe janela de 200 URLs/dia por **stride determinístico**
`sha256(path)`, cobrindo o acervo em ~51 dias sem sorteio —, e o `InIndex` como
teto. **É esse stride que define o coorte** do teste de C2: metade por paridade
do ordinal, leitura antes e depois na mesma janela.

**Onde o coorte pode não ser possível, dito antes:** o deploy é de acervo
inteiro, então um A/B verdadeiro pode não ser viável. Nesse caso o teste é
antes/depois na **mesma** coorte de stride, com a ressalva de que antes/depois
entre árvores diferentes **não atribui causa** — e a atribuição fica declarada
como não medida, nunca afirmada.

---

## 5. LEVER 4 — O QUE NÃO FAZER

- **Nada de cloaking.** Mesmo conteúdo para bot e humano, sempre; serialização muda por **URL** e por **Accept**, **nunca** por User-Agent. Medi que hoje está correto: 4 UAs distintos (o do projeto, curl, Chrome/131 e **sem** UA) devolveram **sha256 idêntico** na mesma URL, e `Accept: text/markdown` varia como deve. Os **6 maps** sobre `$http_user_agent` no nginx vivo (`wj_bot_allow:203` + cinco `wj_tier_*_marca`) foram verificados: alimentam **só** `limit_req_zone` e `log_format`, zero `return`/`rewrite`/`root`/`try_files`. **Não introduzir o primeiro.**
- **Não quebrar o que já está indexado.** §2.1 mede que o teto é o índice e que ele cresce sozinho. Qualquer mudança que faça URL indexada mudar de endereço, sumir ou responder 4xx/5xx destrói valor que **não se recompra com alavanca nenhuma** — só esperando a curva de novo.
- **Nada de métrica de vaidade.** Não somar camadas. Não somar a categoria "AI Crawler" da Cloudflare como interesse de citação (é quase toda Amazonbot = treinamento). Não apresentar leitura como citação. Não contar as **866.020** requisições de aquecimento (73,0% da borda) como audiência. Não contar 304/405/404 como alcance.
- **Nada que quebre o teto de 50 KB.** Folga medida: 12.734 B no pior de 11.357 arquivos. C2 cabe com margem enorme, mas o tamanho vai declarado em bytes no commit.
- **Nada que toque a CSP.** C2 é JSON-LD, não script. `internal/pageinline.Script` é **um** script só, isento byte a byte em `htmlcontract.go:189`; **segundo script reprova em oito gates** e exigiria 10 mil hashes ou `'unsafe-inline'`. Nenhuma alavanca aqui precisa de JS.
- **Nada de UA de terceiro.** Toda saída por `wikijuridicabot.Aplica(req, proposito)`; sonda própria por `AplicaSondaInterna` (que escreve o `X-Warming-Request`, sem o qual o portal mede o próprio eco). `TestNenhumPontoDeSaidaSaiDisfarcado` cobra isso.
- **Nada de `glama.json`.** São 86 requisições em 8 dias, mas o arquivo é prova de propriedade da Glama.ai e **exige conta e API key** — rota proibida pelo self-hosted-first. Os alias legítimos (`/.well-known/mcp.json`, `ard.json`) são dois arquivos sem dado novo e sem credencial; esses sim.
- **Nada de "revisão humana" como etapa.** `relatar_defeito` promete, na descrição servida e na skill do agent-card, que o relato vai para triagem humana. A ordem em vigor proíbe desenhar isso. Ou o cérebro triagem (DEC-059 já o autoriza), ou **a frase muda**.
- **Nada de afrouxar gate para passar.** Página reprovada vira correção do elo que reprovou.

---

## 6. LEVER 5 — O EFEITO DA GPU (RTX 5060 Ti 16 GB)

`k` medido **na própria placa**: 0,648 e 0,660 (contra 0,44 da 4090) — planejar
pela banda subestima em ~47%. Decode **17–23×**, **prefill 74–130×**.

**A conta certa pesa prefill, porque a carga é de prefill:** medido no próprio
arquivo de extrações, **6.268.192 prompt_tokens contra 985.671 eval_tokens =
6,36:1**.

**Estado da fila, medido por mim** (`data/ai/fila.sqlite?mode=ro`):

| tipo | estado | linhas |
|---|---|---|
| `extrair_dispositivos` | pendente | **34.118** |
| `extrair_dispositivos` | concluída | 8.370 |
| `extrair_dispositivos` | executando / erro | 3 / 39 |
| `embed_pagina` | concluída / erro | 11.248 / 5 |
| `medir_modelo` | **pendente** | **3** |

Modelo dominante: `qwen3.5:4b` em 42.531 tarefas.

**O que a GPU destrava, concretamente:**

1. **A fila drena.** `tools/run-daily-content:445` registra **75–100 s por item**. 34.118 × 75 s ÷ 3.600 = **711 h ≈ 30 dias** de CPU contínua. Com o ganho ponderado pelo prefill (6,36:1 favorecendo o eixo de 74–130×), o mesmo lote cai para a ordem de **horas**. Os 24.181 acórdãos sem extração deixam de ser horizonte e viram lote noturno. **Derivado, não medido na placa** — ela ainda não está no host.
2. **`medir_modelo` deixa de ser ironia.** Três pendentes significam que **a própria medição do modelo está parada** por falta de CPU. O primeiro trabalho da GPU é essa fila, porque é ela que produz os números com que todo o resto se decide.
3. **O 14b vira usável para geração.** Hoje `qwen2.5-coder:14b` faz **1,85 tok/s**. Isso importa para a rede social de IA por motivo medido, não por preferência: o L-MAD mede debate jurídico multiagente em **+7,6 e +7,8 pontos com modelo médio** e **−7,35 com modelo fraco**. O cérebro roda `qwen3.5:4b`. **Ligar debate com modelo fraco piora a qualidade** — a GPU é o que torna o debate seguro de ligar, e por isso é pré-requisito, não acessório.
4. **Geração longa passa a caber.** O piso de 1.100 caracteres do `social_policy.json` (derivado: a página indexável mais magra tem 1.111) é a especificação do tamanho da peça. A 2,9 tok/s é lento por peça; com decode 17–23× vira lote.

**O que a GPU NÃO resolve, e não se deve conflacionar:** `buscar_semantico` custa
**8,98 s a frio** e 0,21–1,78 s quente — o custo é **carga de modelo**, não
embedding, e a causa é `KeepAlive: "2m"` em
`internal/httpserver/mcp_semantico.go:87`. É **um parâmetro**, vale **antes** da
GPU, e resolvê-lo com hardware seria pagar placa por configuração. Idem os
21–48 s de `load_duration` por alternância embed↔geração.

**E uma trava que a GPU não dispensa:** `MemoryMax=12G`,
`OLLAMA_MAX_LOADED_MODELS=2` e a guarda de `internal/cerebro/saude.go` (teto de
9 GiB **residentes**, que pesa bytes em vez de contar modelos) existem porque em
2026-09-08 12:04:53 dois residentes levaram a RAM livre a 4,7% e o earlyoom matou
`llama-server` **e os servidores MCP das sessões**. A placa muda o throughput; não
muda o fato de que a guarda mede memória.

---

## 7. IMPLEMENTAÇÃO — NA ORDEM, COM O ARTEFATO DE CADA PASSO

A ordem não é preferência: **P1** primeiro porque a retenção de 8 dias apaga a
linha de base de tudo; **P4 antes de P5** porque emitir a versão errada no HTML
transformaria um defeito de um canal em defeito de dois; **P9 antes de P11**
porque o gerador recusa sem corpus.

| # | Passo | Artefato que produz |
|---|---|---|
| **P1** | `tools/generate-edge-leitura-de-agente-daily` + unit diária **sem `OnFailure`**. Reusa `cloudflare_auth.py`, `botagents.py`, `edgetelemetry.py`; migra as consultas de `/tmp/borda_*.py`; embute as três armadilhas e o controle positivo de §3.1. | `data/ops/edge_agent_reading_daily.jsonl` (`edge_agent_reading_v1`) + `ops/systemd/wikijuridica-edge-leitura-agente.{service,timer}` |
| **P2** | `tools/check-leitura-de-agente-nao-regride` com a régua de §3.4 **pré-registrada no cabeçalho**; exit 2 enquanto a série < 14 d; lê `api_disponivel` do ledger, **nunca** exit code. | ferramenta read-only + teste de falso positivo sobre amostra real |
| **P3** | Bloco `ia` em `collect-bing-webmaster` (dict `:111-116`); **execução padrão exit 0** gravando `api_disponivel: false` (M10); exit 3 só sob `--so ia`; sonda ≤ 2 req/dia; linha de base `ia_painel_leitura_manual` de §3.2. | tipos novos no `bing_webmaster_daily.jsonl` + `test_collect_bing_webmaster.py` estendido |
| **P4** | **C1 — o defeito central.** Trocar a fonte de `ContentSHA256` de `anchor_claim_publication.jsonl` (congelado em 26/08) para `published_manifest.html_sha256`. Gate novo: **versão emitida == sha256 dos bytes servidos**, sobre amostra por stride. | 10.070 versões corretas + 1.036 rotas ganhando versão + `tools/check-versao-confere-com-artefato` |
| **P5** | **C2** — `version` + `identifier` na struct (`structured_data.go:115-127`) **e** no schema (`:2542-2556`), mesmo commit. Rodar `internal/structureddata` e `internal/render` (inclusive `author_credential_test.go`). | JSON-LD com versão verificável em 11.106 páginas |
| **P6** | Deploy de P5: `./tools/deploy-publico --ressemear` (JSON-LD é **markup**), `--desde-commit` **proibido** nessa passada; conferir `tools/check-csp-style-hashes` antes; ler o MOTIVO impresso e **não** purgar de novo se disser `purgando tudo`. | `public/` republicado + linha no `edge_cache_purge.jsonl` |
| **P7** | **C4** — tirar `escapaTexto` de dentro do code span (`render.go:485`); oráculo = a URN do JSON-LD; teste por **mutação** com os spans impressos antes da asserção. | 356 URNs de parágrafo válidas + teste de regressão |
| **P8** | **C3** — inverter `primeiroNaoVazio` em `render.go:285`; teste compara com `apiCitacao.Title` sobre amostra, sem reimplementar a regra. | título citável único nos quatro canais |
| **P9** | **C5** — `AddResourceTemplate` em `mcp.go:238-243` devolvendo o **mesmo** objeto de `ler_pagina`; conferir `mcp_method_derivado_test.go` e `mcp_recusas_transporte_test.go`; acrescentar ao `mcp_paridade_tres_vias_test.go`; estender `TestSuperficieDeAgenteSoAnunciaRotaViva` para cobrir **capacidade**, não só rota. | `capabilities.resources` no `initialize` + gate de igualdade dos três inventários (15 tools / 14 skills / 4 skills A2A) |
| **P10** | **Publicar P7/P8/P9 pela via certa:** `./tools/deploy-binario-go` — binário → socket → serviço → **invalidar origem → purgar borda**, nessa ordem. A gêmea sai com `s-maxage=604800` atrás do `proxy_cache wj_dyn` em `@markdown`: **swap de binário sozinho deixa a borda servindo URN corrompida e título velho por 7 dias**, e purgar antes de invalidar repopula o Tiered Cache com o conteúdo VELHO (medido 2026-09-05). | binário no ar + borda coerente + `warm-origin-cache` reposto |
| **P11** | **V1** — `collect-stj-acordaos --aplicar --dataset <os 6 ausentes>` e completar a 1ª Turma, respeitando Crawl-Delay 10 (~1 h). | cursor com 10 datasets + `registros-*.jsonl` das 6 turmas/seções |
| **P12** | `tools/generate-motor-tier-a` (a seleção tem 255 linhas de 10/set) e **V2/V3 com `--seco`** para medir o estoque real antes de gravar. | `tier_a_artigos.jsonl` fresco + número medido de candidatos (**substitui** os 2.488/4.763 do dossiê) |
| **P13** | **V2/V3** — duas linhas no mapa `GERADORES` (`run-daily-content:369-373`) + `WIKI_LIMITE_LEI_ARTIGO` e `WIKI_LIMITE_ACORDAO`. `internal/tetodelote` garante que publicada não consome cota. | páginas `leis/cpc-art-*` e de acórdão no ar, pela cadeia do §5 |
| **P14** | Conserto do **critério** do cruzamento (`generate-datajud-corpus:152-183`): OR-de-um-token → `buscar_semantico`, limiar calibrado sobre o par consulta↔página que `consulta_pagina`/`pagina_consulta` já entregam. | `ranking_nacional.json` com cobertura válida + conjunto rotulado da calibração |
| **P15** | Gate de coerência do link acervo → rede social (o vazamento que queimou 1.114 requisições de AI Crawler verificado em 48 h e ainda vaza 141). | `tools/check-link-acervo-rede-social` + `data/ops/demanda_de_agente_pendente.jsonl` |
| **P16** | Fechar `Percursos` para 100%: hoje 5.815 de 11.104 (52,4%), faltam 5.289. Regeneração pelo passo 2.6 do `deploy-publico`, respeitando a **ordem topológica** dos ~9 derivados (cada um mais novo que sua fonte) e preservando em `.agents/runtime/` antes. | `legal_cocitation_index.jsonl` cobrindo o acervo |
| **P17** | Corrigir a promessa de "triagem humana" em `relatar_defeito` (descrição servida + skill do agent-card). | descritor coerente com a ordem em vigor |

**Serialização:** P5, P7, P8, P9 tocam Go → build ~5 min, `flock
/tmp/opt-wiki-commit.lock`, índice **vazio** antes de pedir a vez (índice sujo
levou o `go-index-compile-closure` de 14,9 s a 77,6 s). P1–P3, P11–P16 são leves e
concorrentes. P11 e P12 são I/O e rede, não disputam CPU com o build.

---

## 8. RISCOS — ONDE ESTE DESENHO PODE FALHAR

1. **C2 pode não mover a citação.** Que o grounder do Copilot **leia** `version` do JSON-LD é **não medido e não mensurável de fora**. Se não ler, C2 entrega citabilidade (o agente **pode** conferir a revisão) e **zero** citação. O coorte por stride de §4 mede antes de investir mais nessa direção.
2. **O coorte pode ser inviável.** O deploy é de acervo inteiro; antes/depois entre árvores diferentes não atribui causa. É o limite honesto do teste e não se resolve com mais análise.
3. **O teto de índice pode dominar tudo.** Com 64,5% de cobertura e +448/dia sem alavanca nossa, a citação pode subir (ou não) por razões que **não são deste plano**, e qualquer atribuição de efeito a C1–C5 fica confundida com a curva de absorção do Bing. Mitigação parcial: o painel exibe `InIndex` ao lado, e nenhuma conclusão de efeito se tira sem normalizar por ele.
4. **O método do Bing pode nunca aparecer.** Então o numerador de citação segue sendo leitura de painel e o §12 do contrato fica sem série. A alternativa — XHR do painel com a sessão do dono — é **rota errada** pela regra de credencial, e eu não a proponho.
5. **P13 pode gerar página que o gate recusa em massa.** O gerador de artigo tinha mediana de 1 bloco e ~50 palavras autorais contra o piso de 250 antes de a Frente D criar três famílias de aresta; com a seleção velha (255 linhas, 10/set) o risco é real. Mitigação: **P12 com `--seco` antes**, e o número do `--seco` manda — não o do dossiê.
6. **O corpus pode continuar monotemático mesmo depois de P11.** Se os 6 datasets ausentes tiverem cobertura rala de meses, o desbloqueio não vem. **Não medi a densidade mensal desses 6 datasets nesta sessão.**
7. **O coletor de borda pode truncar em silêncio.** A dimensão crua já truncou em 4 dos 8 dias; padrão `_like` errado vira série falsa sem erro. Mitigação: o controle positivo de §3.1, que é obrigatório e não opcional.
8. **P9 pode divergir dos outros canais.** Um quinto canal servindo objeto diferente é o defeito que `agentsurface` existe para impedir, e nenhum teste de paridade atual o pegaria. Mitigação: o `ResourceTemplate` chama a **mesma** função de `ler_pagina`, e o gate de capacidades entra no mesmo passo.
9. **Um terço da métrica por agente é ficção enquanto os 30,7% não identificados durarem.** 26.834 requisições sem `agent_key`; 15.493 são agentes que se declaram e o registro não conhece (`meta-externalads/1.1` 8.485, `AionBot/1.0` 7.008). `verifiedBotCategory` vazio **não** significa falso — a Cloudflare não verifica PerplexityBot. Atribuir demanda por UA lê scanner como cliente.
10. **`--ressemear` em P6 é irreversível em efeito.** As ~11.100 rotas contam como conteúdo novo, o acervo é re-datado e o sitemap re-anuncia tudo. Para **markup** é o correto (a re-datação é suprimida), mas errar a flag nessa passada é o erro caro — e `--desde-commit` fica proibido nela.
11. **P4 pode revelar que o manifesto também envelhece.** Eu provei que o manifesto bate com os bytes **numa** página, hoje, com o processo iniciado às 12:30:27 e o manifesto escrito às 12:28:57. Se a transação de publicação escrever o manifesto **antes** de o `public/` final assentar, a nova fonte teria a mesma classe de defeito num ponto diferente. O gate de P4 (versão emitida == sha256 dos bytes servidos) é justamente o que detecta isso, e por isso ele é parte do passo, não um extra.
12. **A CSP que o Applebot relata segue sem causa.** 243 violações/dia de `script-src-elem`, origem = a nossa própria, e o nosso script **não** é o bloqueado (hash confere byte a byte, borda idêntica à origem, os quatro injetores da Cloudflare off). 45% do orçamento do Applebot — porta de Siri/Spotlight/Apple Intelligence — se gasta relatando isso. `cmd/social/cspreport.go` **descarta o caminho por desenho**, então a causa é ininvestigável do disco até existir vocabulário fechado de caminho. Candidato vivo: Speculative Loading (`/cdn-cgi/speculation`, 186 req em 09-14), e o setting **não é legível** em `zones/{id}/settings/speculation_rules`.
13. **Os 2.488/4.763 são do dossiê.** Procurei o artefato da passada exaustiva em `data/editorial/motor/` e `.agents/runtime/` e **não o achei**. Qualquer dimensionamento que dependa deles está pendurado em número que eu não medi — daí P12.

---

## 9. O QUE O ADVISOR MUDOU

Duas chamadas. A primeira depois da orientação e antes de escrever; a segunda com
o plano já durável no disco. **Mudou onze coisas, cinco delas evitando erro caro.**

**Primeira chamada — cinco mudanças:**

1. **Deu o critério de ordenação.** Eu tinha refutações soltas; ele transformou M1 ("`rel=alternate` já existe e a classe que responde ignora") no **método**: população que lê a superfície × o que falta nela ÷ custo. Daí o 128×.
2. **Evitou um teste vermelho.** Eu ia levar o bloco "Como citar" da gêmea para o HTML. Mandou ler `author_credential_test.go` antes. Li: `:41-43` exige **exatamente duas** ocorrências visíveis de `OAB/RJ 227191`, e `citacao.go:241-243` mostra que a linha da gêmea carrega a credencial — seria a terceira. O desenho virou **JSON-LD**, que o próprio teste exclui da contagem.
3. **Evitou derrubar a validação do acervo.** Alertou para `additionalProperties`. Achei `structured_data.go:2511` com `false` no schema do Article: campo na struct sem a propriedade no schema reprovaria o documento inteiro. P5 virou um passo com **duas edições obrigatórias no mesmo commit**.
4. **Corrigiu o nome do gate.** Ao escrever a régua ficou claro que "gate de citação" era a mentira: citação não é observável por dia. Virou `check-leitura-de-agente-nao-regride`, com régua pré-registrada e exit 2 para "não sei".
5. **Redirecionou o cruzamento e a GPU.** Consertar o **critério** do produtor existente em vez de criar cruzamento novo — e percebi que o conjunto rotulado para calibrar já existe em `consulta_pagina`/`pagina_consulta`. E mandou ler a fila antes de escrever sobre GPU: medi 34.118 pendentes e as **3 `medir_modelo` pendentes**, o achado mais eloquente da seção.

**Segunda chamada — seis mudanças, e uma delas achou o defeito central:**

6. **Levou ao achado M0, o mais importante do plano.** Ele apontou que `version` podia não bater com o hash da página servida. Fui medir: **bate** conceitualmente (o doc diz que é o `html_sha256`), mas **não bate na prática em 10.070 de 10.070 rotas** — a fonte é `anchor_claim_publication.jsonl`, congelado em 26/08. Sem essa provocação eu teria escrito P5 propagando o valor errado para 11.106 páginas de HTML. O plano ganhou C1 e P4, e a tese mudou.
7. **Separou volume de citabilidade.** Eu tinha uma lista única com L1 em primeiro. Ele mostrou que isso confunde "onde mora o aparato" com "o que faz a citação crescer": C2 é hipótese não medida, enquanto V2/V3 transformam 404 em 200 em rota que um AI Crawler **verificado** pediu. §2 virou dois eixos.
8. **Fez aparecer o teto que eu não tinha ranqueado.** Mandou ler `rastreio_diario`. Medi **InIndex 7.158 de 11.106 (64,5%)**, +448/dia, monotônico — e `check-descoberta-do-bing` já documenta que o IndexNow não acelera isso. Virou §2.1, entrou como proibição em §5 e como linha no painel e no gate.
9. **Evitou 7 dias de borda servindo o defeito.** Eu tinha escrito "basta o swap do binário" para as correções da gêmea. Ele lembrou do `s-maxage=604800` e do `proxy_cache wj_dyn`: o caminho é `deploy-binario-go`, com invalidar origem **antes** de purgar borda. Virou **P10**.
10. **Evitou um alerta falso diário ao dono.** Eu tinha desenhado exit 3 diário no coletor do Bing. Fui verificar: `wikijuridica-bing-submit.service` **tem** `OnFailure=wikijuridica-alerta@…` (M10). A execução padrão passou a terminar em 0 gravando `api_disponivel: false`, com exit 3 só sob `--so ia`, e o gate lendo o ledger em vez do exit.
11. **Rotulou as constantes do gate.** `≥ 3 dias` virou **derivado** (contra as 48 h medidas de lag dos 404); o limiar de queda e a janela de 14 d ficaram **provisórios com método de calibração** em vez de número redondo disfarçado de medição.

**Onde não segui, com evidência primária:** ele sugeriu achar a construção de
`capabilities` por grep em `mcp.go`/`mcp_conector.go`. O grep deu vazio duas
vezes; **medi o servidor vivo** (`POST /mcp` com `Mcp-Method: initialize`) e achei
a causa no SDK — `mcp.NewServer(…, nil)` em `mcp.go:239` e a derivação automática
em `go-sdk@v1.7.0/mcp/server.go:645-652`. Resultado mais forte que o esperado: a
capability aparece sozinha ao registrar um template. E sobre a preocupação dele
de que `resources/*` fosse recusado no transporte, achei
`internal/httpserver/mcp.go:1866-1873` com `case "resources/read":` já
implementado — o encanamento **existe**; P9 confirma nos dois testes nomeados
antes de afirmar.

Também segui o conselho de **não** rodar `--seco` em plan mode (compila, e há
risco de exit 75 com Go em edição) — por isso o número real de candidatos é P12,
não afirmação minha.
