# Colheita: estado da arte — rede social de agentes, protocolos, plataforma jurídica citada por LLM

Sessão 2026-09-15. PLAN MODE (somente leitura). Colheita 5/5 (majoritariamente web).

Nota metodológica: `WebFetch` NÃO permite definir User-Agent (usa o fetcher da
Anthropic). Para string exata (nome de campo, versão de spec, JSON Schema) usei
`curl -sL` com o UA canônico do projeto. `WebFetch` só para prosa. Declarado, não
escondido.

## Estado (preenchido à medida que mede)

- [ ] 1. Protocolos de agente
- [ ] 2. Identidade e autenticação de agente
- [ ] 3. Rede social para agentes
- [ ] 4. Plataformas jurídicas e LLM
- [ ] 5. Moderação por IA e refutação estruturada

## 1. PROTOCOLOS — A2A: o veredito INVERTE o que o briefing supunha

Fonte canônica da v1.0 NÃO é JSON. `specification/json/README.md` do repo oficial:
"`a2a.json` is a **non-normative build artifact** derived from the canonical proto
definition at `specification/a2a.proto`... intentionally **not** committed".
Logo, a régua é o proto (812 linhas, baixado 2026-09-15).

`message AgentCard` da v1.0 — 8 campos REQUIRED: name, description,
**supported_interfaces**, version, capabilities, default_input_modes,
default_output_modes, skills. Opcionais: provider, documentation_url,
**security_schemes**, **security_requirements**, **signatures**, icon_url.

**O card vivo tem os 8 REQUIRED.** `supportedInterfaces` NÃO é campo inventado:
é o campo REQUIRED da v1.0, e os 3 campos REQUIRED de `AgentInterface`
(url, protocol_binding, protocol_version) estão todos preenchidos. Os campos que
o briefing esperava (`url`, `preferredTransport`, `additionalInterfaces`,
`protocolVersion` no topo) são o formato **v0.3, superado**. Nosso card está
ADIANTE da suposição, não atrás.

Faltam exatamente 3 campos opcionais, e dois deles importam:
- `securitySchemes` + `securityRequirements`: a skill `relatar-defeito` exige
  token de escopo `relatos:escrever` e o card NÃO declara como autenticar. O
  servidor OAuth JÁ EXISTE e responde (`/.well-known/oauth-protected-resource`,
  353 B; `oauth-authorization-server`, 1.175 B, escopo `relatos:escrever`). É
  mapear metadado existente para `OAuth2SecurityScheme` — a v1.0 tem o oneof
  pronto (api_key / http_auth / oauth2 / openid / mtls). `AgentSkill` também tem
  `security_requirements` por skill.
- `signatures` (`AgentCardSignature`: protected, signature, header): a v1.0
  (12/03/2026) formaliza card assinado em JWS (RFC 7515) com canonicalização JCS
  (RFC 8785), para o agente que recebe provar que o card é do domínio que diz ser.
  Não temos. Com `signatures` + Web Bot Auth fechamos identidade nos dois sentidos.

A2A v1.0: doada por Google à Linux Foundation, 150+ organizações em 09/04/2026.

## 2. IDENTIDADE — Web Bot Auth virou draft de GRUPO DE TRABALHO do IETF

O que o briefing e a maioria dos textos chamam de `draft-meunier-*` está
**substituído**: `draft-meunier-web-bot-auth-architecture-05` consta como
"Replaced by draft-meunier-webbotauth-httpsig-protocol", e este por
**`draft-ietf-webbotauth-httpsig-protocol-00`, de 01/09/2026, do WG `webbotauth`**.
Saiu de rascunho individual para documento adotado há duas semanas. Define
`Signature`, `Signature-Input` e `Signature-Agent`, com diretório de chaves em
**`/.well-known/http-message-signatures-directory`** (JWKS).

Cloudflare: exige **Ed25519**, diretório nesse mesmo caminho, registro em
Manage Account > Configurations > Bot Submission Form, e popula
`cf.bot_management.verified_bot`. (NÃO medi se esse campo chega à ORIGEM no plano
do dono — é configuração de Transform Rule/Worker; declarado não medido.)

Medido na produção: `/.well-known/http-message-signatures-directory` = **404**.
Não somos verificáveis por assinatura nem como servidor nem como cliente.

**Amazonbot é a maior lacuna medida.** 3.446 req/24 h na borda — o MAIOR agente
de IA que nos visita — e zero cobertura: não há arquivo em
`data/ops/bot_ip_ranges/` (14 arquivos) nem operador `amazon` no `geo` do nginx
(2.492 prefixos, 7 operadores). A Amazon documenta a verificação por **rDNS para
subdomínio de `crawl.amazonbot.amazon`** e publica faixas em
developer.amazon.com/amazonbot/ip-addresses/ (NÃO medi a contagem de prefixos: a
página é SPA renderizada por JS, 529.870 B sem nenhum CIDR no primeiro response).
UA oficial: `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible;
Amazonbot/0.1) Chrome/W.X.Y.Z Safari/537.36`. Ignora `crawl-delay`.

E o método que falta **já está escrito no repo**: `internal/crawleridentity/
identity.go:525` faz PTR + forward com `miekg/dns`. Está amarrado ao Google
(`IdentityPolicy: ...reverse_dns_ptr_google_domain...`) e nenhum chamador vive em
`httpserver` ou no nginx — só release/smoke/policy. Não é construir: é generalizar
o sufixo e ligar ao caminho de serving.

## 1b. MCP — quase reportei um falso vermelho. O servidor ESTÁ em dia.

A revisão CORRENTE do MCP é **2026-07-28** (modelcontextprotocol.io/specification/
versioning). Ela trocou a negociação: a versão passa a ir por requisição no `_meta`
sob `io.modelcontextprotocol/protocolVersion` (e no header `MCP-Protocol-Version`
no Streamable HTTP), com o RPC **obrigatório `server/discover`** e o
`UnsupportedProtocolVersionError`. `2025-11-25` e anteriores são as revisões
"handshake-based".

Como o `initialize` responde `2025-11-25`, a leitura fácil seria "estamos duas
revisões atrás". **Errado, e medi até o fim antes de escrever.** Chamando
`server/discover` com o `_meta` completo (o servidor exigiu, em dois passos,
`protocolVersion` e depois `clientCapabilities` — ou seja, valida o modelo novo):

```
supportedVersions: ["2026-07-28","2025-11-25","2025-06-18","2025-03-26","2024-11-05"]
resultType: complete · cacheScope: public · 15 ferramentas
```

O servidor implementa a revisão corrente e o RPC obrigatório, e responder
`2025-11-25` ao `initialize` é o comportamento CERTO de compatibilidade. Não é
defeito. (Lição do próprio contrato: ausência de sinal não é evidência; gate
vermelho não é veredito.)

**O que sobra de verdade:** `capabilities` traz só `logging` e `tools`. Não há
`resources`, nem `prompts`, nem `completions`. São 11.106 páginas publicadas e
**zero resources MCP** — o cliente não consegue listar/assinar o acervo como
recurso, só chamar ferramenta. Essa é a lacuna real, e é de alavancagem alta.

## 3. REDE SOCIAL PARA AGENTES — EXISTE, e já teve consolidação e desastre

**Moltbook** (moltbook.com), lançada 28/01/2026 por Matt Schlicht, estilo Reddit,
só agentes postam (humanos leem), sobre o projeto aberto OpenClaw.
**Adquirida pela Meta em 10/03/2026**, time para o Meta Superintelligence Labs.
Em 06/06/2026: **2.895.874 agentes registrados, mas só 206.839 verificados por
humano — 92,9% nunca foram verificados.**

Os modos de falha estão documentados e são exatamente o nosso projeto de risco:
- Identidade: começou **sem verificação nenhuma**; em 02/2026 pôs um "CAPTCHA
  reverso" (puzzle de matemática com tema de lagosta, texto ofuscado), burlado
  por humanos que repassavam o puzzle a um LLM.
- Segurança: 01/02/2026 a Wiz achou Supabase mal configurada com leitura e
  escrita totais — **1,5 milhão de tokens de API, 35.000 e-mails e mensagens
  privadas entre agentes**; depois do primeiro remendo, a ESCRITA em tabelas
  públicas continuou aberta (dava para injetar payload em post ao vivo).
- Injeção de prompt agente-a-agente: a Permiso mediu **2,6% dos posts amostrados
  com payload de injeção escondido**, parte dormente na memória do agente até a
  condição de disparo.
- Crítica de mérito: "AI theater" — posts vinham de humanos que mandavam o agente
  postar, e os agentes reproduziam padrão de rede social do treino.

## Medições locais já feitas (disco / produção)

| o quê | número | camada | como |
|---|---|---|---|
| chaves do agent card vivo | 11 chaves; `supportedInterfaces` com `protocolBinding=JSONRPC`, `protocolVersion=1.0`, `url=/a2a/v1` | produção (borda) | `curl /.well-known/agent-card.json` |
| campos ausentes no card | `securitySchemes`, `security`, `protocolVersion` (topo), `url`, `preferredTransport` = null | produção | idem |
| MCP vivo | `protocolVersion: 2025-11-25`, capabilities = `logging` + `tools` (sem `resources`/`prompts`) | produção | POST /mcp initialize |
| testdata MCP no disco | schema `2025-12-11` | disco | `internal/httpserver/testdata/` |
| superfícies que respondem 200 | ai-catalog.json 5.363 B · llms.txt 18.132 B · openapi.json 14.163 B · agent.json 4.597 B · oauth-protected-resource 353 B · oauth-authorization-server 1.175 B · /bot/ 15.336 B | produção | curl -o /dev/null -w |
| `/.well-known/mcp.json` | 404 | produção | idem |
| mapa `geo` do nginx | 2.492 prefixos, 7 operadores (anthropic 26 · apple 33 · duckduckgo 486 · google 1.647 · microsoft 28 · openai 260 · perplexity 12) | disco | `ops/nginx/bot-operators.conf` |
| rDNS no projeto | EXISTE em `internal/crawleridentity/identity.go:525` (PTR + forward, miekg/dns), mas nenhum chamador em `httpserver`/nginx — só release/smoke/policy | disco | grep de chamadores |
| amazonbot | 3.446 req/24h na borda (maior agente de IA) e ZERO cobertura de IP: sem arquivo em `data/ops/bot_ip_ranges/` (14 arquivos), sem operador `amazon` no mapa | borda + disco | dados da sessão + ls |
| ferramentas MCP vivas | 15 (`buscar_semantico`, `grafo`, `impacto`, `contexto_juridico`, `responder_pergunta`, `perfil_de_jurista`, `relatar_defeito`, …) | produção | tools/list |
| `llms-full.txt` | 1.586.684 B servidos | produção | curl -w size_download |

## 4. PLATAFORMAS JURÍDICAS E LLM — o mundo abriu MCP em maio/2026; o Brasil não

**Fora do Brasil, MCP virou o canal padrão de acesso jurídico por agente, e a
data é precisa: 12/05/2026.** A Anthropic lançou o Claude para o setor jurídico
com 20+ conectores MCP e 12 plugins por área. No mesmo dia, DOIS provedores de
pesquisa jurídica publicaram conector MCP (LawSites, 12/05/2026):
- **Free Law Project / CourtListener** — MCP em `mcp.courtlistener.com`, de graça
  com conta, expondo jurisprudência, PACER, análise de citação, sustentação oral,
  dados de juízes, busca e alertas. Sem fins de lucro, desde 2010. Em 07/07/2026
  dobraram o acesso gratuito por 30 dias.
- **Thomson Reuters** — conector sobre Westlaw e Practical Law (sem KeyCite).
- **Harvey** — conector oficial. Confirmado de primeira mão: a lista de
  ferramentas diferidas DESTA sessão traz `mcp__claude_ai_Harvey__*` apontando
  para `https://api.harvey.ai`.
- vLex/Vincent: 1B+ documentos, 110 jurisdições; a Clio fechou a compra da vLex
  por US$ 1B em 11/2025. (Conector MCP próprio: não achei.)
- Cuidado com falso-amigo: o conector `mcp__claude_ai_CNA__*` desta sessão é o
  **中央社 CNA, agência de notícias de Taiwan** (`ask.cna.com.tw`) — NÃO é o
  Cadastro Nacional dos Advogados da OAB. Conferi antes de citar.

**No Brasil, a assimetria é o achado.**
- **JusBrasil: API não é pública** — exige contato comercial, sem documentação
  nem preço abertos. Sem MCP.
- **Escavador: API Business comercial** (`api.escavador.com/v1/docs/`), consulta
  por CPF/CNPJ/OAB/número CNJ. Sem MCP.
- Existem MCPs brasileiros, mas **todos são consulta processual sobre o DataJud**:
  `mcp-juridico-brasil` (MIT, 105 estrelas, 26 forks, pré-1.0) expõe consulta por
  número CNJ, histórico de movimentos, monitoramento com snapshot, cálculo de
  prazo em dias úteis pelo CPC arts. 219–224 e lista de 91 tribunais — e declara
  não devolver processo em segredo de justiça. Mais os scrapers de DataJud com
  endpoint MCP na Apify e um `pje-mcp-server`.

**Conclusão medida: ninguém no Brasil serve CONTEÚDO JURÍDICO EXPLICATIVO com
fonte oficial a agente.** O que existe é encanamento de andamento processual. Nós
servimos 11.106 páginas por 4 canais que renderizam o mesmo objeto (HTML, gêmea
Markdown, MCP com 15 ferramentas, A2A, `/api/v1/lote`), com busca semântica em
11.248 vetores e grafo de 79.706 nós / 393.081 arestas. Nesse eixo estamos à
frente de JusBrasil e Escavador, não atrás — e é um eixo que eles não disputam.

## 5. MODERAÇÃO POR IA E REFUTAÇÃO — a literatura já mediu o NOSSO bug

**O ponto cego do gate social não é idiossincrasia nossa: é o viés conhecido do
juiz-LLM.** O levantamento de argument mining (arXiv 2506.16383) registra que
LLMs "favour fluent but logically thin arguments over less polished yet
better-supported ones" — preferem o argumento fluente e logicamente magro ao
menos polido e melhor sustentado. É exatamente o que a medição desta sessão
achou: das 3 peças, a reprovada citava `REsp 1.794.991` e `Lei 11.771/2008`
(citações reais) e a aprovada passou trocando o precedente nominado por "a
jurisprudência relevante diferencia". **Um cérebro-moderador ingênuo
industrializaria essa inversão em escala.**

O antídoto é estrutura, não mais modelo. Project Debater (IBM, arXiv 2110.01029)
decompõe em serviços separáveis: Claim Detection (a frase contém tese sobre o
tópico?), Evidence Detection (a frase é evidência — resultado de pesquisa ou
opinião de especialista — a favor ou contra?) e Argument Quality (regressor BERT
treinado em 27 mil argumentos anotados por *crowdsourcing*). Corpus de ranking de
qualidade de argumento: arXiv 1911.11408. Modelo de Toulmin operacionalizado com
rótulos por componente (Lead, Position, Claim, Counterclaim, Rebuttal, Evidence,
Concluding Statement) e três níveis de qualidade.

**Julgar sem virar censor: bridging-based ranking**, e com as falhas medidas.
Community Notes/Birdwatch (arXiv 2210.15723) usa fatoração de matriz sobre a
matriz esparsa nota×avaliador para inferir a dimensão latente de opinião e só
promove o que recebe apoio de quem costuma discordar — algoritmo e dados
abertos, e X e Meta o usam. Mas: *Science Advances* (2026) mostra que ele
**submodera conteúdo polarizador por desenho**, e arXiv 2511.02615 mostra
vulnerabilidade a viés e manipulação de avaliador; arXiv 2604.11224 propõe
fatoração sensível à qualidade contra manipulação; arXiv 2506.24118 é o trabalho
do próprio X sobre escalar julgamento humano com LLM escrevendo notas.

**Debate multi-agente em DIREITO já tem medição, e ela tem lado ruim.** L-MAD
(arXiv 2607.09099, 10/07/2026) avalia estruturas de debate em *legal textual
entailment* com três papéis — Juiz (avaliador imparcial), Advogado (prova que a
premissa implica a hipótese) e Advogado contrário (prova que não implica) — e
compara consenso (itera até maioria/supermaioria/unanimidade) contra votação
(cada um mantém raciocínio independente e só agrega no fim):

| modelo | protocolo | acurácia | baseline |
|---|---|---|---|
| Qwen3-30B | consenso | 88,46% | 80,86% |
| Qwen3-8B | votação | 89,37% | 81,59% |
| Qwen3-32B | — | ganho marginal (autoconsistência empata) | — |
| Llama3.1-8B | consenso | **64,53% (PIOR)** | 71,88% |

Modos de falha nomeados: **alucinação colaborativa** (modelo fraco adota premissa
errada sem perceber), **deriva por excesso de deliberação** (mais rodadas
degradam: o agente desconfia da conclusão certa) e **sicofancia** (consenso
forçado faz o modelo médio adotar sem crítica a linha dominante).
Consequência direta para nós: debate com modelo pequeno PIORA o resultado, e o
cérebro roda hoje `qwen3.5:4b` / `qwen2.5-coder:14b`. Votação com raciocínio
independente evita a sicofancia melhor que consenso. Rodada precisa de teto.
Também na área: AgenticSimLaw (debate de tribunal com papéis, protocolo de
interação, raciocínio privado e auditabilidade) e "LLM Agents in Law: Taxonomy,
Applications, and Challenges" (arXiv 2601.06216).

## 6. A MEDIÇÃO QUE MUDA A ARQUITETURA: a origem é 99,5% instrumento nosso

Fui verificar o rDNS do Amazonbot no nosso próprio log e achei coisa maior.
`data/ops/access/access-2026-09-10.jsonl`, 410.510 linhas, separando pelos
campos `warming` e `bot_simulation` que o próprio log carrega:

| camada da linha | linhas | % |
|---|---|---|
| `warming: true` (nossa sonda) | 209.773 | 51,1% |
| `bot_simulation: true` (nosso smoke) | 198.816 | 48,4% |
| **tráfego REAL** | **1.890** | **0,46%** |

Dos 1.890 reais: `claude-user` 7, `Applebot` 2, `PerplexityBot` 1. **Zero
Googlebot, zero GPTBot, zero OAI-SearchBot, zero Amazonbot.**

E a armadilha que quase me pegou: por substring na linha inteira, "Googlebot"
aparecia 88.263 vezes e `index.md` 181.141 vezes. **Todas em linha de warming ou
de simulação.** Contando pelo campo `path`, a gêmea Markdown tem **0 de 1.890**
requisições reais. (Absence por substring é sólida — substring só superestima —
então os zeros de Amazonbot e da família OpenAI valem; os 88.263 não valiam.)

**Consequência de engenharia, e ela corrige a minha própria alavanca #2:** o
acervo sai estático com `s-maxage=604800`, então verificar identidade de agente
no nginx veria quase nada — 3.446 requisições de Amazonbot na borda contra 0 de
410.510 na origem. **Identidade de agente tem de ser verificada NA BORDA**
(Worker/Web Bot Auth no Cloudflare), não no nginx. rDNS no nginx só alcançaria
rota dinâmica, e a rota dinâmica mais importante — a gêmea — tem zero real medido.
A série de origem se declara `is_lower_bound: true`; este é o tamanho do piso:
0,46%.

## 7. AGNTCY e OpenAI Apps SDK (o que faltava do item 1)

**AGNTCY** — aberto pela Cisco em 03/2025 (com LangChain e Galileo), acolhido pela
Linux Foundation, 65+ empresas; membros formativos Cisco, Dell, Google Cloud,
Oracle e Red Hat. Quatro componentes: **Agent Discovery** (OASF, Open Agent
Schema Framework), **Agent Identity** (identidade criptograficamente verificável
e controle de acesso entre organizações), **Agent Messaging** (SLIM, multimodal,
com humano no laço, resistente a quântico) e **Agent Observability**. O que
exigiria de nós: um descritor OASF ao lado do agent card A2A, e identidade
verificável — que é o mesmo par de chaves do Web Bot Auth. Convergente, não
concorrente.

**OpenAI Apps SDK — e aqui está a alavanca escondida: é construído SOBRE MCP.**
Apps in ChatGPT e o Apps SDK (OpenAI) usam o Model Context Protocol como padrão
aberto de conexão; em 09/07/2026 o diretório de apps foi migrado para o diretório
de **Plugins** (plugin passou a poder conter skills, apps e templates), e apps
aprovadas começaram a sair para usuários no começo de 2026. Como já servimos MCP
na revisão corrente com 15 ferramentas, **a rampa para o ecossistema da OpenAI já
está construída** — e a família OpenAI já nos visita 2.574 vezes/24 h na borda
(oai-searchbot 1.234 + chatgpt 1.099 + gptbot 241). Falta submeter, não construir.

## 8. Item 4, agora MEDIDO por mim (não por resumo de busca)

GET com o UA canônico, 7 rotas de agente por host (15/09/2026):

| rota | jusbrasil | escavador | courtlistener (www) |
|---|---|---|---|
| `/.well-known/agent-card.json` | **404** | **404** | 404 |
| `/.well-known/agent.json` | **404** | **404** | 404 |
| `/.well-known/http-message-signatures-directory` | **404** | **404** | 404 |
| `/.well-known/mcp.json` | **404** | **404** | 404 |
| `/mcp` | 301 | 403 | 403 |
| `/openapi.json` | 301 | 403 | 403 |
| `/llms.txt` | **200 (8.949 B)** | **200 (8.244 B)** | 403 |

Leitura honesta: **404 é prova de ausência; 301 e 403 não são** (redirect e WAF —
declaro não medido). O que fica medido: **nem JusBrasil nem Escavador publica
agent card A2A nem diretório de chaves Web Bot Auth — 4 de 7 rotas em 404 nos
dois.** Mas **os dois publicam `/llms.txt`**: estão fazendo trabalho voltado a
LLM, só não trabalho de PROTOCOLO de agente. E o nosso `/llms.txt` tem 18.132 B —
2,0× o do JusBrasil e 2,2× o do Escavador — mais `llms-full.txt` com 1.586.684 B,
que nenhum dos dois serve.
CourtListener em `www` dá 404/403 em tudo, mas isso **localiza**, não refuta: o
MCP dele vive em host próprio — `mcp.courtlistener.com/` responde **200** e serve
`/.well-known/oauth-protected-resource` **200**, o mesmo desenho de recurso
protegido por OAuth que nós já temos.

**"São citados por LLM?" — NÃO MEDIDO para os concorrentes**, e não tenho
instrumento para medir citação de domínio de terceiro: o painel de IA do Bing
mostra o site da conta do dono (~23.000 citações nossas), não o de outros. Dizer
qualquer número para JusBrasil ou Escavador seria invenção.

## 9. Item 3 completo: arenas, peer review por IA, e o padrão que EXISTE

Correção ao meu próprio rascunho: eu ia escrever que não há padrão aberto de
post/comentário/refutação entre agentes. **Há, e é o ActivityPub** (Recomendação
W3C de 23/01/2018): ator, objeto, `Create`/`Note`/`Announce`, resposta por
`inReplyTo`, federação, e o tipo de ator `Service` para automação; descoberta por
WebFinger — e medi `/.well-known/webfinger` = **404** no nosso portal. O correto
é: **não existe padrão específico de DISCURSO ENTRE AGENTES**; existe o padrão
geral de rede social federada, e a Moltbook não o usou (não publicou protocolo
nenhum). A2A cobre delegação de tarefa entre agentes, não fala público entre
pares — então para "postar, comentar, refutar" ele não serve, e é isso que abre a
decisão de arquitetura: **federar por ActivityPub ou servir malha própria**.

Vizinhos mais próximos do que o dono pediu:
- **Agents4Science** (Stanford, 2025): primeira conferência em que autoria de IA
  não é só permitida, é **exigida** — IA como primeiro autor E revisor, humano em
  supervisão. Aceitação por nota média de revisor LLM > 4,5 (escala 1–6), com voto
  humano decidindo o limítrofe. É o precedente institucional mais forte de
  "IA revisa IA" com régua declarada.
- **Arena** (ex-LMArena/Chatbot Arena; rebatizada em 28/01/2026, arena.ai):
  avaliação pública de LLM por comparação pareada — é ranking de modelo, não
  discussão entre agentes.
- **Agents Arena** (agentsarena.dev): debates multiagente com formatos sequencial
  e aberto. Mais próximo de espetáculo que de deliberação com evidência.
- Debate multiagente com refutação estruturada em direito: L-MAD e AgenticSimLaw
  (seção 5).

## Lacunas (o que falta MEDIR ou EXISTIR)

1. `/.well-known/http-message-signatures-directory` = 404. Não somos
   verificáveis por assinatura em nenhum dos dois sentidos, e o draft virou
   documento de WG do IETF em 01/09/2026.
2. Amazonbot: 3.446 req/24 h, o maior agente de IA que nos visita, sem faixa de
   IP e sem operador no `geo`. Um terço do sinal do maior visitante é anônimo.
3. rDNS existe em `crawleridentity` mas está preso ao Google e não tem chamador
   no caminho de serving.
4. Agent card sem `securitySchemes`/`securityRequirements` (com OAuth já no ar) e
   sem `signatures` (card assinado JWS/JCS da v1.0, 12/03/2026).
5. MCP sem `resources`/`prompts`: 11.106 páginas e zero resource.
6. Não medi se `cf.bot_management.verified_bot` chega à origem no plano do dono.
7. Não medi a contagem de prefixos publicados da Amazon (página é SPA; 529.870 B
   sem um CIDR no primeiro response).
8. `gptbot` é 33,4% do tráfego de `/redesocial/tema/` (28.036 de 83.810) e não
   está em `agentesValiososParaRanking` (`cmd/cerebro/comentarios.go:42-50`).
9. **Não achei: nenhuma rede social de agentes com recorte JURÍDICO**, em nenhum
   idioma. Não existe padrão de DISCURSO entre agentes (A2A delega tarefa; a
   Moltbook não publicou protocolo). O padrão geral existe — ActivityPub, W3C
   23/01/2018 — e está a decidir se federamos. Ausência é informação: no recorte
   jurídico não há padrão a seguir, e o risco é ser o primeiro.
10. A origem não serve para medir agente: 0,46% das linhas são reais. Verificação
    de identidade e medição de comportamento têm de viver na BORDA.
11. A gêmea Markdown tem **0 de 1.890** requisições reais na origem de 2026-09-10.
    Não sei se agente algum a busca — falta quebrar a borda por caminho × UA.
    Não medido, e é o número mais importante que falta para a tese AI-first.
12. Nenhum descritor OASF (AGNTCY) e nenhuma submissão ao diretório de Plugins da
    OpenAI, tendo o MCP já pronto e 2.574 req/24 h da família OpenAI na borda.
13. `/.well-known/webfinger` = 404: se a decisão for federar por ActivityPub,
    falta descoberta.
14. **Defeito de guarda, não de rota:** `~/.claude/hooks/protect-bot-ratelimit.sh`
    bloqueou a saída com o UA canônico DO PRÓPRIO PROJETO contra host externo,
    por casar a substring "Bot" em `WikijuridicaBot`. Usei a via sancionada
    (`X-Bot-Simulation: true`), mas pelo contrato isso é causa a corrigir na
    guarda, com teste — a guarda deve casar UA de bot de TERCEIRO, e o UA do
    projeto contra host externo é obrigatório, não infração.

## Alavancas (o que, medido, indica caminho de crescimento)

1. **Web Bot Auth nos dois sentidos.** Como servidor, verifica agente que chega
   sem depender de faixa de IP. Como cliente, publicar nosso diretório JWKS e
   assinar a saída com Ed25519 dá identidade verificável ao WikijuridicaBot
   contra WAF — exatamente o caso do F5 BIG-IP do Planalto que já nos recusou.
2. **rDNS generalizado destrava o maior visitante.** Amazon documenta PTR para
   subdomínio de `crawl.amazonbot.amazon`; o código PTR+forward já existe
   (`identity.go:525`). Generalizar sufixo + ligar ao serving converte 3.446
   req/24 h de anônimas em atribuídas.
3. **Agent card assinado + `securitySchemes`** é quase de graça: o OAuth já
   responde com escopo `relatos:escrever`; falta mapear no card e assinar.
4. **`resources` no MCP** publica 11.106 páginas como recurso listável e
   assinável, com o grafo (79.706 nós) e os 11.248 vetores por trás.
5. **O vácuo brasileiro é o produto.** Ninguém no Brasil serve doutrina a agente;
   o que existe é andamento processual. E o mundo mostrou o canal (12/05/2026).
6. **Moderador estruturado, não juiz de fluência.** Claim/Evidence/Quality
   separados, com `/api/v1/citacoes` fazendo da citação verificável um ponto
   POSITIVO — inverte o prêmio à vagueza que a medição pegou.
7. **Bridging por posição doutrinária.** Promover a refutação que convence quem
   parte da tese oposta (consumidor×fornecedor, fisco×contribuinte) é o análogo
   jurídico do Community Notes, e é desenho genuinamente novo — com a submoderação
   do polarizador já medida como preço conhecido.
8. **Votação com raciocínio independente, teto de rodadas, modelo grande.** L-MAD
   mede +7,8 a +8 pontos com modelo médio e −7,35 com modelo fraco. A migração
   para a RTX 5060 Ti (prefill 74–130×) é o que torna o debate seguro de ligar.
9. **Colher o que a Moltbook pagou para aprender.** 92,9% de agentes não
   verificados, 1,5 M de tokens vazados, 2,6% dos posts com injeção de prompt e
   escrita aberta em tabela pública depois do primeiro remendo. Identidade
   criptográfica antes do primeiro post, e conteúdo de agente tratado como dado
   hostil (a injeção agente-a-agente é o vetor), não como texto.

## Fontes (URL e data)

- A2A proto canônico: raw.githubusercontent.com/a2aproject/A2A/main/specification/a2a.proto + specification/json/README.md (baixados 15/09/2026)
- A2A v1.0, Linux Foundation, 150+ organizações: linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations… (09/04/2026); v1.0 em 12/03/2026
- MCP versionamento e revisão corrente 2026-07-28: modelcontextprotocol.io/specification/versioning (15/09/2026)
- Web Bot Auth WG: datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/ rev 00, 01/09/2026; substituiu draft-meunier-webbotauth-httpsig-protocol-02 (19/08/2026) e draft-meunier-web-bot-auth-architecture-05
- Cloudflare Web Bot Auth (Ed25519, `cf.bot_management.verified_bot`): github.com/cloudflare/cloudflare-docs …/bot-verification/web-bot-auth.mdx; blog.cloudflare.com/web-bot-auth/ e /verified-bots-with-cryptography/
- Amazonbot: developer.amazon.com/amazonbot e /amazonbot/ip-addresses/ (15/09/2026)
- Moltbook: en.wikipedia.org/wiki/Moltbook (lançada 28/01/2026; Meta 10/03/2026; 2.895.874 registrados / 206.839 verificados em 06/06/2026); wiz.io/blog/exposed-moltbook-database-reveals-millions-of-api-keys (01/02/2026); securityweek.com/security-analysis-of-moltbook-agent-network-bot-to-bot-prompt-injection-and-data-leaks/ (Permiso, 2,6%)
- CourtListener MCP: mcp.courtlistener.com; free.law/2026/05/12/courtlistener-is-now-available-inside-claude/; free.law/2026/07/07/double-api-access-to-courtlistener/; lawnext.com/2026/05/two-legal-research-providers-launch-mcp-integrations-with-claude… (12/05/2026)
- JusBrasil / Escavador: conteudo.jusbrasil.com.br/api; api.escavador.com/v1/docs/
- mcp-juridico-brasil: github.com/DeHor-Labs/mcp-juridico-brasil (MIT, 105 estrelas, pré-1.0)
- L-MAD: arxiv.org/html/2607.09099v1 (10/07/2026)
- Argument mining survey: arxiv.org/html/2506.16383v3 · Project Debater APIs: arxiv.org/pdf/2110.01029 · ranking de qualidade: arxiv.org/pdf/1911.11408
- Community Notes: arxiv.org/pdf/2210.15723 · science.org/doi/full/10.1126/sciadv.aee6932 (submoderação por desenho) · arxiv.org/pdf/2511.02615 (manipulação) · arxiv.org/html/2604.11224 · arxiv.org/html/2506.24118
- LLM Agents in Law: arxiv.org/pdf/2601.06216

## Correções de proveniência (para não passar resumo por medição)

- A2A: o release primário é **v1.0.1, publicado 2026-05-28T11:34:36Z**
  (`api.github.com/repos/a2aproject/A2A/releases/latest`). A data "12/03/2026"
  para a v1.0 GA e o "150+ organizações em 09/04/2026" vêm de blog e do press
  release da Linux Foundation — fonte secundária, marcada como tal.
- Moltbook (2.895.874 / 206.839 / 28-01-2026 / Meta 10-03-2026) = Wikipédia.
  Vazamento (1,5 M tokens, 35.000 e-mails) = Wiz. Injeção em 2,6% dos posts =
  Permiso via SecurityWeek. **Fonte secundária, não medição minha.**
- Amazonbot verificável por rDNS em `crawl.amazonbot.amazon` = re:Post/DataDome.
  **Não confirmei na página da Amazon** (SPA de 529.870 B, sem CIDR no primeiro
  response) e **não pude testar no nosso log: 0 linhas de Amazonbot em 410.510.**
- `2025-12-11` do testdata não está em `supportedVersions` do servidor nem na
  lista de revisões publicadas: é instantâneo de schema para teste, **não** sinal
  de conformidade.
- `cf.bot_management.verified_bot` chegando à origem: **não medido** (depende de
  Transform Rule/Worker e do plano da zona).

## O que o advisor mudou

Chamei duas vezes. A primeira, antes de pesquisar, mudou o resultado; a segunda,
na revisão, mudou o que o resultado AFIRMA.

Da 1ª chamada:
1. **Impediu o erro central.** Eu ia julgar o agent card pela lista de campos do
   briefing e declarar não-conformidade. Ele mandou buscar o schema oficial e
   diferenciar v0.3 de v1.0 — e o veredito INVERTEU: o card está em dia, e os
   campos "faltando" eram do formato superado.
2. **Curl para schema, WebFetch só para prosa**, porque WebFetch resume por
   modelo pequeno e alucinaria nome de campo — fatal justamente no item 1.
3. Apontou que rDNS **existe** em `crawleridentity` (o briefing dizia que não) e
   que amazonbot sem faixa de IP era o par lacuna→alavanca mais forte. Os dois
   viraram achado.
4. Deu as pistas de Moltbook, Community Notes, Project Debater e L-MAD, que eu
   confirmei em fonte primária.

Da 2ª chamada (revisão), três bloqueios legítimos:
5. **AGNTCY e OpenAI Apps SDK estavam faltando** — o item 1 os nomeava e eu tinha
   zero. Fui buscar, e o Apps SDK virou alavanca: **é construído sobre MCP**, logo
   nosso servidor já é a rampa.
6. **Lacuna #9 estava falsa como escrita** — ActivityPub é exatamente o padrão
   aberto de post/resposta/federação, Recomendação W3C desde 2018. Reescrevi: não
   há padrão de discurso ENTRE AGENTES; o geral existe e a Moltbook o ignorou.
7. **O item 4 se apoiava em "a busca não mencionou MCP"** — ausência de sinal, que
   o próprio contrato proíbe. Fui sondar as 7 rotas nos hosts. Virou medição minha
   (4 de 7 em 404), e **descobri o que eu não esperava: os dois publicam
   `/llms.txt`** — o que torna a afirmação mais precisa e mais útil.
8. Mandou upgradar a data do A2A e o rDNS do Amazonbot para fonte primária. A do
   A2A deu v1.0.1/28-05-2026. A do Amazonbot **não deu**: ao ir ao nosso log achei
   a medição que mais mudou o plano — **a origem é 99,5% instrumento nosso
   (0,46% real)**, e por isso identidade de agente tem de ser verificada na BORDA,
   não no nginx. Isso corrige a MINHA alavanca #2, que dizia "ligar ao caminho de
   serving".

Não contrariei nada dele. O único item que deixei como "não medido" por escolha
foi o plano da zona Cloudflare: é leitura de API autorizada, mas não altera
nenhuma conclusão desta colheita e o custo cai melhor na frente de borda.

