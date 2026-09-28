# Colheita: as superfícies IA-first do /opt/wiki — inventário medido

Sessão 2026-09-15, PLAN MODE (somente leitura). Processo vivo:
`/opt/wiki/bin/wikijuridica-server` pid 1715804, subiu 2026-09-15 12:30:27.
nginx 127.0.0.1:8088 → Go 127.0.0.1:8089, 5 cloudflared ativos.
Load average durante as medições: **9,78 / 11,13 / 10,93** (declarado porque
afeta latência).

Toda sonda saiu com
`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; inventario-superficies)`
e `X-Warming-Request: true`.

**Camadas.** `borda` = Cloudflare `httpRequestsAdaptiveGroups`, zona
wikijuridica.com.br, janela de 24 h terminando ~2026-09-16T01:00Z. `origem` =
curl contra 127.0.0.1:8088 (nginx + Go; o acervo HTML sai do disco por
`root public/`). `disco` = leitura de arquivo do repositório.
Total da janela em consulta **sem dimensão** (não truncável): **88.419** —
coerente com as 88.033 do briefing, janela deslizada.

---

## 0. Correções que esta colheita faz

### No briefing

| Afirma | A medição diz | Camada / onde |
|---|---|---|
| `risco_de_superacao` é ferramenta MCP | **É CAMPO, não ferramenta.** `tools/list` devolve 15 ferramentas, nenhuma com esse nome; o número vive em `contexto_juridico` | origem + disco: `mcp_contexto.go:300`, `:306`; `mcp_risco.go:104-137`; artefato 4.986 linhas (esse número está certo) |
| malha do HTML = 23,4% cross-área | **38,9%** (140/360) no bloco de relacionados | origem, 40 páginas |
| Percursos = 76,7% cross-área | **79,6%** (82/103) — CONFIRMADO | origem, 40 páginas |

O salto Percursos-vs-malha é real, mas **2,04×**, não os 3,3× implícitos.

### Em mim mesmo — quatro erros meus, corrigidos por medição

1. **Truncamento.** Minha 1ª consulta pediu 5.000 grupos por `count_DESC` e somou
   62.016. Declarei "zero" para seis rotas. Consulta **nomeada por rota** derrubou
   quatro desses zeros: `/api.md` = 4, `/api/politica-de-uso.json` = 2,
   `/.well-known/mcp/server-card.json` = 3, `/rss.xml` = 3. Só quatro zeros
   sobreviveram.
2. **Sonda própria contada como demanda.** A subárvore de habilidades parecia a
   família mais ativa de `/.well-known/` (220 req). Cruzando por User-Agent:
   **219 de 220 (99,5%) é a nossa sonda de aquecimento.**
3. **Latência de partida a frio vendida como custo.** Eu reportei
   `buscar_semantico` a 9.720 ms com **uma amostra**. Quatro chamadas seguidas:
   **8.978 ms → 740 → 1.777 → 207 ms.** O número era carga de modelo no Ollama
   (`KeepAlive: "2m"`, `mcp_semantico.go:87`), não custo de embedding.
4. **`glama.json` recomendado sem verificar o que é.** É **prova de propriedade**
   da Glama.ai, que exige conta e devolve chave — **rota proibida** pelo
   self-hosted-first. Ver §6.1: a rota se troca, não se segue.

---

## 1. Inventário completo das superfícies de máquina

### 1.1 As duas que carregam demanda real de agente

Separando nossas sondas (`wikijuridica-cache-warm`, `-agent-surface-probe`,
`-superficie-probe`, `WikijuridicaBot`) do tráfego externo — camada **borda**:

| Rota | Total 24 h | Interno | **Externo** | Quem consome |
|---|---|---|---|---|
| **`*/index.md`** (gêmea) | 2.936 | 9 | **2.927 (99,7%)** | Amazonbot 1.180 · Baiduspider 789 · ShapBot 512 · GPTBot 112 · bingbot 67 · "pc" 104 |
| **`/mcp`** | 1.952 | 15 | **1.937 (99,2%)** | `node` 639 · SentinelOracle 373 · mcpbeat 271 · aiohttp 142 · rokmcp 81 · undici 39 · httpx 38 — **81 UAs distintos** |

### 1.2 **O achado central: quem cita não lê a gêmea**

Total do agente × quanto dele vai para a gêmea, **na mesma janela de 24 h**
(camada borda, uma consulta por agente):

| Agente | Total | Na gêmea | % na gêmea | Papel |
|---|---|---|---|---|
| ShapBot | 876 | 512 | **58,4%** | rastreio |
| GPTBot | 241 | 112 | **46,5%** | treino |
| Baiduspider | 2.101 | 789 | **37,6%** | rastreio |
| Amazonbot | 3.322 | 1.180 | **35,5%** | treino/rastreio |
| bingbot | 528 | 67 | 12,7% | busca |
| oai-searchbot | 1.233 | 24 | **1,9%** | **responde** |
| Applebot | 530 | 2 | **0,4%** | busca |
| **ChatGPT-User** | **1.115** | **0** | **0,0%** | **responde ao vivo** |
| **PerplexityBot** | **363** | **0** | **0,0%** | **responde ao vivo** |
| **Googlebot** | **111** | **0** | **0,0%** | busca |

**Os agentes que RASTREIAM consomem a gêmea (35–58%). Os agentes que RESPONDEM
não a tocam (0–1,9%).** Somados, ChatGPT-User + PerplexityBot + oai-searchbot +
Applebot + Googlebot = **3.352 requisições** de quem produz resposta gerada — e
**26** delas (0,8%) na gêmea.

Isso reordena tudo: **todo o aparato de citação (sha256, CSL-JSON, licença,
"Como citar esta página") existe em 40 de 40 gêmeas e em 0 de 40 HTMLs** (§2), e
**quem cita lê o HTML.** A superfície de citação está no canal errado para o
público que importa. É a maior alavanca desta colheita, e não estava no briefing.

### 1.3 O resto do inventário, com teto

| Rota | Devolve (bytes, origem) | Borda 24 h | Teto |
|---|---|---|---|
| `/api/v1/search` | JSON 3.339 B | 227 | — |
| `/robots.txt` | 3.501 B | 127 | — |
| `/feed.xml` | Atom | 59 | — |
| `/sitemap.xml` | 7.304 B | 36 | — |
| `/.well-known/agent-card.json` | A2A card, 4 skills, 4.597 B | 33 | — |
| `/a2a/v1` | JSON-RPC (GET = 405) | **20, só 1 externo** | — |
| `/llms.txt` | 18.132 B | 20 | — |
| `/.well-known/api-catalog` | RFC 9727 | 19 | — |
| `/openapi.json` | OpenAPI 3.1.1, 13 operações, 14.163 B | 15 | — |
| `/.well-known/oauth-protected-resource` | RFC 9728, 353 B | 11 | — |
| `/.well-known/agent-skills/index.json` | 14 habilidades, 13.846 B | 10 | — |
| `/.well-known/ai-catalog.json` | ARD, 11 entradas, 5.363 B | 6 | — |
| `/llms-full.txt` | **1.586.684 B** | 5 | 1,5 MB num response |
| `/api/v1/lote` | NDJSON 637.626 B | **4** | 50 padrão / 200 teto / **2 MiB** (`api_lote.go:79-92`) |
| `/api/v1/citacoes` | guardrail, 4.050 B | **4** | — |
| `/api.md` | 18.547 B | 4 | — |
| `/api/v1/citar` | descritor, 326 B | **3** | — |
| `/.well-known/mcp/server-card.json` | 507 B | 3 | — |
| `/.well-known/mcp` | mesmo documento, 507 B | 1 | — |
| `/rss.xml` | RSS | 3 | — |
| `/api/politica-de-uso.json` | 4.448 B | 2 | — |
| `/api/v1/pages` | 277 B | 2 | — |
| `/api/v1/health` | 30 B | 2 | — |
| `/api/v1/citar/{path}` | hash HTML+MD, ABNT, Repr-Digest | **1** | — |
| `/api/v1/redesocial/lote` | NDJSON 189 B | **1** | 50/200, cursor por chamada |
| `/api/v1/relatos` | escrita (OAuth) | 1 | única escrita da API |
| `/api/v1/novidades` | 53.001 B | **0** | teto 1.000 |
| `/api/v1/sitemap` | **779.480 B** | **0** | — |
| `/changes.json` | — | **0** | — |
| `/.well-known/tdmrep.json` | 58 B | **0** | — |

Status de `/mcp`: 200 = 1.277 · **202 = 415** · **405 = 214** · 400 = 14 · 499 = 14.
Os 214 são GET (contrato). Os 415 com 202 e os 14 com 400 pedem leitura própria —
**não investigados nesta colheita**.

**O `/api/v1/*` mais chamado não é da API:** é
`/api/v1/redesocial/csp-report`, com **309** requisições — mais que toda a API de
leitura somada (245). Contra 85 acessos ao HTML de `/redesocial/*` na mesma
janela, são ~3,6 violações de CSP por carregamento. **É defeito de CSP vivo nas
páginas sociais, não curiosidade de tráfego.** Fora do escopo desta colheita;
fica nomeado.

### 1.4 A assimetria descritor-vs-execução

O agent-card foi buscado **33** vezes; o endpoint A2A que ele anuncia recebeu **1
chamada externa** em 24 h. Mesmo padrão em `/api/v1/citar` (descritor 3, item 1) e
`/openapi.json` (15 leituras contra 245 chamadas de API no total). **Agentes leem
descritor e não executam.**

### 1.5 A árvore de habilidades é lida por nós mesmos

`/.well-known/*` somou **355** requisições; a subárvore de habilidades é **220**:

| Subárvore | Total | Interno | Externo |
|---|---|---|---|
| `/.well-known/agent-skills/*` | 137 | **136** | **1** (Neuronto) |
| `/.well-known/skills/*` | 83 | **83** | **0** |

**219 de 220 (99,5%) é a nossa sonda de aquecimento.** A superfície mais elaborada
do portal — 14 skills com `SKILL.md`, bundles `.tar.gz`, `references/`, `assets/`
— teve **1 consumidor externo em 24 h**. Em `/.well-known/` como um todo, 264 de
355 (74,4%) é interno; quem lê de fora são **registries** (Golemreach, Neuronto,
WellknownBot, strata-observatory, mcpi/probe), não consumidores.

### 1.6 Três inventários de capacidade que não conversam

- MCP `tools/list`: **15** ferramentas
- `/.well-known/agent-skills/index.json`: **14** habilidades
- `/.well-known/agent-card.json`: **4** skills A2A

`agentsurface.Servicos` (`agentsurface.go:122-141`) é fonte única das **rotas**,
não das **capacidades**. Nenhum teste cobra igualdade entre os três inventários —
e a razão de o pacote existir é exatamente impedir descritor que promete rota
morta (`agentsurface.go:14-21`).

O agent-card usa `supportedInterfaces` (A2A 1.0: `protocolBinding: JSONRPC`,
`protocolVersion: 1.0`, `url: /a2a/v1`) e **não** traz `protocolVersion`, `url`
nem `preferredTransport` no topo. É a forma moderna, não defeito — cliente A2A
0.2.x quebraria nela. Quantos clientes 0.2.x existem: **não medido**.

---

## 2. A gêmea Markdown, medida

Amostra: **40 de 11.106** páginas publicadas, stride determinístico 277,
**40/40** com HTTP 200 nos dois canais. Camada **origem**.

| Métrica | HTML | Gêmea .md | Razão |
|---|---|---|---|
| bytes (média) | 22.895 | 10.005 | **0,44×** |
| **palavras de texto (média)** | 889 | **957** | **1,08×** |
| links internos únicos | 15,0 | 11,3 | 0,75× |
| bloco de relacionados | 9,0 | 10 (+2 de rede social) | — |
| **URN LexML distintas** | **2,4** | **1,1** | **0,46×** |
| H2 | — | 9,2 | — |
| H3 (= perguntas de FAQ) | — | 1,5 | contrato |

**A gêmea não é maior: é mais densa.** 8% mais texto em 44% dos bytes —
**densidade textual 2,47×**. Comparar bytes crus (o que o briefing sugere)
inverteria a conclusão: os ~12.900 bytes de diferença são markup, JSON-LD, CSP e
navegação que só o HTML paga.

### O que a gêmea tem e o HTML não tem

Medido em 40/40: front matter YAML com `version: sha256:…`, `license: CC-BY-4.0`,
`license_url`, `usage_policy`, mapa `services:` com as 7 rotas de máquina, e
`sources:` com `verified_at`, `text_version`, `text_version_checked_at` e `claim`
(a afirmação que cada fonte sustenta). Mais o bloco **"Como citar esta página"**
com referência ABNT, `sha256` e **CSL-JSON** — **40 de 40** gêmeas, **0 de 40**
HTMLs. Cruzar com §1.2: quem cita não lê este canal.

### DEFEITO A: a URN correta está no HTML; a corrompida, na gêmea

Mesmo objeto, duas serializações, e **a de máquina é a pior**:

- **HTML:** o JSON-LD traz `mentions` com `@type: Legislation`,
  `legislationIdentifier`, `legislationType`, `legislationJurisdiction` — 4 URN
  distintas, **bem formadas**, inclusive `…10406!art206_par5`.
- **Gêmea:** as `sources` do front matter trazem só URL do Planalto, **sem URN**.
  A URN só aparece na seção Percursos — e lá sai **corrompida**.

`render.go:485` escreve a URN dentro de uma **code span** e a passa por
`escapaTexto` (`blocks.go:100-113`), que escapa `_` → `\_`. CommonMark **não**
processa escape dentro de code span, então o byte servido é literal — verificado
com `cat -A` sobre os bytes servidos, não sobre o render:

```
urn:lex:br:federal:lei:2002-01-10;10406!art206\_par5
```

Medido em `content/legal_cocitation_index.jsonl` (camada **disco**): **365 de
8.516 percursos (4,3%)** têm URN com `_`; **73 URN distintas**, todas de nível
parágrafo (`!artNNN_parN`) — as mais precisas, as que cruzam com LexML. Servidas
são **até 365**: `render.go:470-477` descarta percurso cujos itens esvaziam no
filtro de auto-referência, então o número servido é ≤ 365. Correção: não escapar
dentro de code span.

### DEFEITO B: 87,5% das páginas dão dois títulos a duas superfícies

O front matter da gêmea (e o CSL-JSON dentro dela) usa o **H1**; `/api/v1/citar`
e o `<title>` usam o título do manifesto. Medido em
`/autonomos/cliente-parou-de-pagar-as-parcelas/`:

- gêmea + CSL-JSON: "Parcelas interrompidas no meio do contrato: como cobrar o restante"
- `/api/v1/citar` + `<title>`: "Cliente pagou parte e parou: como cobrar o saldo restante"

**35 de 40 (87,5%)** divergem. Dois agentes citando a mesma URL por canais
diferentes produzem registros bibliográficos diferentes, e nenhum teste de
paridade vê, porque cada canal é internamente consistente. (`<title>` ≠ `<h1>` é
SEO correto; o defeito é o **CSL-JSON e o `/api/v1/citar` discordarem**.)

### Percursos por fundamento legal: metade do acervo não tem

- Amostra: **21 de 40** (52,5%).
- População (disco): `content/legal_cocitation_index.jsonl` cobre **5.815 de
  11.106** páginas = **52,4%**. Amostra e população batem.
- 8.516 percursos, 1.059 URN distintas, média 2,6 links/página (máx. 8).
- Cross-área **79,6%** (82/103) — a afirmação do plano se confirma.

**O diferencial de ponta do canal de máquina não existe em 5.291 páginas.**

---

## 3. O MCP: 15 ferramentas, custo medido

`tools/list` = **21.796 bytes** para 15 ferramentas (~1.453 B cada, só o
catálogo). Camada **origem**, load average 9,78 — declarado porque o número
depende dele.

| Ferramenta | bytes | latência |
|---|---|---|
| `grafo` | 193 | 26 ms |
| `impacto` | 193 | 33 ms |
| `mudancas_desde` | 37.455 | 44 ms |
| `responder_pergunta` | 10.713 | 52 ms |
| `buscar_paginas` | 6.947 | 56 ms |
| `search` | 3.629 | 57 ms |
| `ler_pagina` | 27.962 | 65 ms |
| `contexto_juridico` | 26.327 | **2.162 / 1.036 / 1.566 ms** (3 amostras) |
| `buscar_semantico` | 15.937 | **8.978 → 740 → 1.777 → 207 ms** (4 seguidas) |

As 15: `search`, `fetch`, `buscar_paginas`, `buscar_semantico`, `ler_pagina`,
`contexto_juridico`, `grafo`, `impacto`, `mudancas_desde`, `responder_pergunta`,
`relatar_defeito`, `buscar_duvidas`, `duvidas_do_tema`, `ler_duvida`,
`perfil_de_jurista`.

**`buscar_semantico` é 8,98 s a FRIO e 0,21–1,78 s a quente.** O custo é a carga
do modelo no Ollama, não o embedding — `KeepAlive: "2m"` (`mcp_semantico.go:87`)
significa que **todo intervalo maior que 2 minutos entre chamadas paga os ~9 s de
novo.** Para um agente que chama uma vez, o custo típico é o de partida a frio.
Fila concorrente durante a medição: 3 `extrair_dispositivos` executando,
34.154 pendentes.

**Confirmado: `buscar_semantico` depende do daemon vivo NO BOOT.**
`mcp_semantico.go:81-86` sonda o Ollama por 3 s; falhando, a ferramenta fica fora
de `tools/list` e o log diz. Hoje está presente. O desenho é honesto — anunciar
ferramenta que sempre falha seria pior. O efeito é que **uma superfície de produto
entra e sai do catálogo conforme o estado de um daemon local**, e o agente que leu
o catálogo ontem não sabe. Nenhuma das 15 declara "capacidade condicional".

`mudancas_desde` funciona: 50 itens/chamada (teto 200), `proximo_cursor` =
`2026-08-26T00:00:00Z|/aereo/…`, `restantes: 11056`; cada item traz caminho,
título, URL, `url_markdown`, `modificado_em`. **Não traz hash**, e
`modificado_em` tem hora zerada (`00:00:00Z`) — duas mudanças no mesmo dia são
indistinguíveis e o consumidor não sabe se o corpo mudou sem baixar a página.

`relatar_defeito` promete ao agente **"triagem humana"** (na descrição servida do
parâmetro `descricao`, e na skill homônima do agent-card). A ordem em vigor diz
que revisão de conteúdo não é do dono. **Promessa servida a agente que o processo
não honra**: ou o cérebro triagem, ou a frase muda.

---

## 4. O que falta para um agente citar ESTA plataforma

### Já existe, e é forte

| Requisito | Estado | Evidência |
|---|---|---|
| Bloco "como citar" | ✅ na gêmea / ❌ no HTML | 40/40 e 0/40 |
| CSL-JSON | ✅ na gêmea | 40/40 |
| Referência ABNT | ✅ `/api/v1/citar/{path}` | origem |
| Licença por rota | ✅ CC-BY-4.0 no front matter, no JSON-LD (`license`, `usageInfo`) e no CSL-JSON | 40/40 |
| Hash do conteúdo | ✅ `html_sha256` + `markdown_sha256` + **Repr-Digest (RFC 9530)** | **verificado byte a byte** |
| URN LexML por norma | ✅ no JSON-LD (`legislationIdentifier`) | origem |
| Data da fonte oficial | ✅ `verified_at`, `text_version_checked_at` | 40/40 |
| Feed de mudanças | ✅ `mudancas_desde`, `/api/v1/novidades`, `/changes.json` | origem |
| Descoberta desde o HTML | ✅ `Link: rel="alternate" type="text/markdown"` + `rel="describedby"` → `/api/v1/citar/…`, **no HTML estático do nginx** | headers medidos |

A verificação de integridade **funciona de ponta a ponta**: o `html_sha256` que
`/api/v1/citar` declara (`8123d77e20d38cc3…`) é o sha256 exato dos bytes que a URL
devolve, e o `markdown_sha256` (`dda9d39f9230f194…`) o da gêmea. Conferido nesta
sessão, nas duas pontas.

### Falta

1. **Bloco de citação no HTML — a lacuna de maior alavanca.** 0 de 40. Cruzado com
   §1.2: os 3.352 pedidos de quem responde ao vivo chegam ao HTML, e o HTML não
   tem hash, CSL-JSON nem "como citar". O `Link: rel="describedby"` aponta o
   caminho, mas exige uma 2ª requisição que **1 agente em 24 h** fez.
2. **Identificador citável por trecho.** Há sha256 **da página inteira**; não há
   âncora estável por seção nem hash por bloco. Um agente que cita um parágrafo
   não pode apontar para ele nem provar que não mudou.
3. **Hash da FONTE OFICIAL.** O contrato (§8, DEC-032) manda "URL, data e hash".
   Gêmea e `/api/v1/citar` entregam URL e data; **o hash do texto oficial não
   aparece em superfície nenhuma.** Um agente não pode conferir que o Planalto não
   mudou o texto desde `verified_at`.
4. **URN LexML nas `sources` da gêmea** (só URL do Planalto) e **URN não
   corrompida nos Percursos** (Defeito A).
5. **Hash e hora no feed de mudanças** (§3).
6. **`version`/`identifier` no JSON-LD.** Tem `license`, `usageInfo`, `citation`,
   `mentions`, `reviewedBy`, `wordCount` — e nenhum campo de versão, embora o
   `sha256` exista e já esteja na gêmea.

### Comparação com fontes jurídicas de referência

O guardrail de citação em tempo real (`/api/v1/citacoes`) segue o padrão que o
CourtListener popularizou, e o hash verificável com Repr-Digest é mais do que
fontes jurídicas costumam expor. A única capacidade em que uma referência bate
este acervo é o **identificador por trecho** (LexML resolve por URN até o
dispositivo; aqui resolve até a página). **Comparação não medida nesta sessão** —
é recall, não medição na fonte, e fica marcada como tal.

---

## 5. Cloaking: conteúdo idêntico por UA. Mas o UA **é** lido — no nginx.

### O conteúdo não varia por User-Agent (medido)

Mesma URL `/autonomos/cliente-parou-de-pagar-as-parcelas/`, camada **origem**
(atravessa o nginx, que é quem serve o acervo):

**Eixo Accept (deve variar):**

| Accept | Content-Type | bytes | sha256 |
|---|---|---|---|
| `text/html` | text/html | 25.146 | `8123d77e20d38cc3…` |
| `text/markdown` | **text/markdown** | **13.151** | `dda9d39f9230f194…` |
| `text/markdown, text/html;q=0.9` | text/markdown | 13.151 | `dda9d39f9230f194…` |
| `application/json` | text/html | 25.146 | `8123d77e20d38cc3…` |
| `*/*` | text/html | 25.146 | `8123d77e20d38cc3…` |

**Eixo User-Agent (não pode variar):** 4 agentes — o nosso, `curl/8.5.0`, um
Chrome de desktop e **nenhum UA** — devolveram os **mesmos 25.146 bytes** e o
**mesmo sha256 `8123d77e20d38cc3…`**. Zero variação.

`Vary: Accept, Accept-Encoding` está no response do HTML estático, e a gêmea tem
URL própria (`/index.md`) exatamente porque CDN pode não honrar `Vary`.

### Correção de uma afirmação minha: o UA **é** lido, e não só pelo Go

Minha primeira leitura foi que "não há caminho por onde o UA alcance a
serialização", com base em `httpserver.go:1518-1524` (o
`serveHTTPRecovered` produz a resposta **antes** de o UA ser lido, em `:1524`,
para métrica e ledger). **Isso vale para o Go, e o acervo não passa pelo Go.**

O nginx vivo é `/etc/nginx/sites-enabled/wikijuridica` →
`/opt/wiki/ops/nginx/wikijuridica.conf`, e ele tem **seis** maps sobre
`$http_user_agent`: `wj_bot_allow` (:203) e cinco `wj_tier_*_marca`
(:598, :612, :626, :643, :659).

**O que eles fazem, verificado:** alimentam **exclusivamente** chaves de
`limit_req_zone` (:609–674) e o `log_format` (:59). Não há **nenhum** `return`,
`rewrite`, `root`, `try_files` ou `proxy_pass` condicionado a UA — grep
confirmado. Ou seja: **mesmos bytes para todos; orçamento de requisições
diferente por classe declarada.** Não é cloaking (a regra do Google é sobre
conteúdo), mas é tratamento por UA, e afirmar que ele não existe era exagero meu.

### O risco real que isso expõe: quem consome a gêmea não está classificado

Cruzando os tiers do nginx com os consumidores reais da gêmea (§1.2):

| Consumidor da gêmea | req na gêmea | Casa em | Orçamento |
|---|---|---|---|
| Amazonbot | 1.180 (40,3%) | `wj_tier_training_std` (`~*amazonbot`) | 600 r/m, burst 300 — **classificado como TREINO** |
| Baiduspider | 789 (27,0%) | **nada** | `wj_generic` 3.000 r/m |
| ShapBot | 512 (17,5%) | **nada** | `wj_generic` 3.000 r/m |
| GPTBot | 112 (3,8%) | `wj_tier_training_aggregated` | 6.000 r/m |

**1.301 de 2.927 (44,5%) do consumo da gêmea vem de agentes que não casam com
nenhuma regra** e caem no curinga; e o maior consumidor único (Amazonbot, 40,3%)
está classificado como treino — não como quem consome o canal de máquina.
`wj_bot_allow` lista `~*amzn-searchbot` e `~*amzn-user`, que **não casam** com
`Amazonbot/0.1`. É o mesmo ponto cego que o briefing já achou em
`agentesValiososParaRanking` (gptbot fora), repetido na camada do nginx.

### Os outros riscos

1. **`X-Warming-Request`** muda métrica, não conteúdo. Correto — é o que impede o
   portal de medir o próprio eco — e é a nossa única entrada privilegiada.
2. **Query string → `noindex`** (`/buscar/?q=`, `/contato/?origem=`): política de
   indexação por rota, não conteúdo por agente. Correto.
3. **Risco de cache, não de código:** se a borda cachear a variante markdown sob a
   URL HTML, um humano recebe markdown; `Cache-Tag: wj-acervo` com
   `s-maxage=604800` faz durar 7 dias. **Não medido nesta sessão** — a verificação
   é uma requisição por área contra a borda pública comparando `Content-Type` com
   e sem `Accept`.

---

## 6. LACUNAS: o que falta existir, e quanto custa

### 6.1 Demanda medida em 404 — e a rota proibida a trocar

**35 de 355 requisições (9,9%) em `/.well-known/` receberam 404 na borda.** Não é
scanner: são registries de MCP e de agente pedindo manifesto que não servimos.

| Rota pedida | 404 em 24 h | O que é (verificado) |
|---|---|---|
| `/.well-known/glama.json` | **17** (100% externo, UA vazio) | **prova de propriedade da Glama.ai** — exige conta e devolve chave própria |
| `/.well-known/mcp.json` | 3 | 3ª grafia da descoberta MCP |
| `/.well-known/ard.json` | 2 | ARD noutro caminho (servimos `ai-catalog.json`) |
| `/.well-known/ai-plugin.json` | 2 | manifesto de plugin |
| `/.well-known/x402` + `x402.json` | 3 | pagamento por requisição de agente |
| `/.well-known/http-message-signatures-directory` | 2 | RFC 9421, assinatura de requisição |
| `owners.json`, `webfinger`, `nostr.json`, `openid-configuration`, `dnt-policy.txt`, `indexnow` | 1 cada | — |

**`glama.json` é rota proibida, e eu a havia recomendado.** Verificado por busca:
é o arquivo de **verificação de propriedade** da Glama.ai, que destrava edição do
dono, monitoramento e **uma API key** — ou seja, exige cadastro e credencial de
terceiro, o que o self-hosted-first veda expressamente. **TROQUE A ROTA:** o
ganho pretendido (ser listado num diretório de MCP) se obtém servindo as grafias
**abertas** de descoberta, que não pedem conta nenhuma.

**E essas quase já existem.** O portal serve, em `/.well-known/mcp/server-card.json`
**e** em `/.well-known/mcp`, o **mesmo** documento no schema oficial do MCP
Registry (`static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`:
`name` em DNS reverso `br.com.wikijuridica/acervo-juridico`, `remotes`, `version`
1.2.0, `websiteUrl`). Falta **só a grafia `/.well-known/mcp.json`** — 3 pedidos
medidos. Custo: **um alias**.

Nota de conformidade, sem inflar: os dois SEPs comunitários usam outros nomes de
campo (SEP-1649 pede `protocolVersion`, `serverInfo`, `transport`, `capabilities`;
SEP-1960 pede `mcp_version`, `endpoints`), e o documento servido não os tem. O
schema oficial é a escolha melhor; o registro é que **um cliente escrito contra
SEP-1649 leria o nosso documento e não acharia `capabilities`**. Nenhum dos dois
SEPs está fundido na spec oficial.

### 6.2 A superfície que falta existir: `/api/v1/trecho/{path}#{ancora}`

Citação por trecho com hash próprio: cada H2 vira âncora estável com sha256 do
próprio bloco; a rota devolve o trecho, a âncora, o hash do trecho, o hash da
página e as URN que aquele trecho invoca.

**Por que:** é o item 2 do §4 e o único em que uma fonte de referência bate este
acervo.

**Custo:** os H2 já existem e já são estáveis —
`internal/pagemarkdown/fidelidade_test.go:70-90` cobra igualdade H2↔seções e
H3↔perguntas de FAQ sobre o acervo real. O renderizador já tem os blocos em mãos e
já calcula o `version:` da página. É hash por bloco no mesmo lugar, mais uma rota
de leitura. **Nenhum dado novo, nenhum modelo, nenhuma credencial.**

### 6.3 As correções, por razão ganho/custo

| Falta | Custo | Ganho medido |
|---|---|---|
| **Bloco de citação no HTML** | reaproveita o que a gêmea já emite em 40/40 | alcança os **3.352** pedidos/24 h de quem responde ao vivo e hoje não vê hash nem licença |
| Não escapar URN em code span | 1 linha (`render.go:485`) + teste de regressão | conserta até **365** URN servidas corrompidas |
| URN nas `sources` da gêmea | o JSON-LD já as tem bem formadas | fecha a inversão do Defeito A |
| Alias `/.well-known/mcp.json` (+ `ard.json`) | 2 alias, zero dado novo | atende **5** pedidos/24 h que são 404, sem credencial |
| Classificar Baiduspider, ShapBot e Amazonbot pelo consumo real | padrões no nginx + `agentesValiososParaRanking` | tira **44,5%** do consumo da gêmea do curinga de rate limit |
| Fechar Percursos para 100% do acervo | regenerar o índice de co-citação (o gerador existe) | leva o diferencial de 79,6% cross-área de 5.815 para **11.106** páginas |
| Unificar o título citável entre os 4 canais | decidir qual título é o citável | remove divergência em **87,5%** das páginas |
| Hash da fonte oficial no front matter | o coletor já baixa o texto; falta gravar o sha | fecha a exigência do §8/DEC-032 |
| `KeepAlive` do embedding > 2 min | um parâmetro (`mcp_semantico.go:87`) | evita os 8,98 s de partida a frio na rota anunciada |
| Igualar os 3 inventários (15/14/4) | teste comparando `tools/list` × agent-skills × agent-card | impede descritor que promete capacidade morta |

### 6.4 A lacuna de MEDIÇÃO — a mais cara de deixar aberta

**Não existe série que meça consumo por superfície de máquina.** Todo o §1 saiu de
consultas GraphQL ad-hoc desta sessão; elas não existem como ferramenta e não
deixam ledger. Sem isso ninguém sabe que:

- a gêmea tem **2.927** consumidores externos e a árvore de habilidades tem **1**;
- quem **responde** (3.352 req) usa a gêmea em **0,8%**, e quem **rastreia** usa em
  35–58%;
- `/api/v1/citar` teve **3** requisições e o `csp-report` teve **309**;
- **9,9%** de `/.well-known/` é 404 com registry atrás.

E o volume bruto **mente**: 74,4% de `/.well-known/` é a nossa sonda, e 99,5% da
árvore de habilidades também. Decisão tomada sobre número bruto investe no lugar
errado — **eu quase fiz isso nesta colheita**, e só não fiz porque cruzei por
User-Agent.

**`tools/generate-superficie-maquina-daily` é a ferramenta que falta**, e ela tem
de nascer com três coisas embutidas, porque as três já me enganaram aqui:
(a) separação interno/externo por User-Agent; (b) consulta **nomeada por rota**
para as rotas de baixo volume, nunca `orderBy count_DESC` truncado;
(c) papel do agente (rastreia / responde) como dimensão, porque é ele que
reordena a prioridade.

As quatro consultas já estão escritas em `/tmp/borda_superficies.py`,
`/tmp/borda_gemea.py`, `/tmp/verifica_zeros.py`, `/tmp/skills_quem.py`,
`/tmp/amazon.py` e `/tmp/medir_gemea.py` — **foram pagas nesta sessão e deveriam
sair de `/tmp` para `tools/`.**

---

## 7. O que o advisor mudou

Consultado. **Mudou quatro coisas, e duas inverteram conclusão:**

1. **`buscar_semantico`.** Apontou que 9.720 ms era **uma** amostra com estado do
   Ollama não controlado (`KeepAlive: "2m"`, fila concorrente, load 9,78) e que eu
   havia construído o argumento da RTX sobre ela. Remedi 4× seguidas:
   **8.978 → 740 → 1.777 → 207 ms.** O número era partida a frio. O argumento da
   placa continua válido, mas **muda de natureza**: o que dói é a carga do modelo,
   então o conserto barato é o `KeepAlive`, não a placa. §3 e §6.3 reescritos.
2. **A prova de cloaking.** Apontou que `httpserver.go:1518-1524` não cobre as 11
   mil páginas estáticas, que saem do nginx. Grep no nginx vivo achou **seis maps
   sobre `$http_user_agent`** — e a verificação mostrou que alimentam só
   `limit_req_zone` e o log, nunca conteúdo. **Minha frase "não há caminho por
   onde o UA alcance a serialização" era exagero e foi corrigida**, e a
   investigação rendeu o achado de §5: 44,5% do consumo da gêmea não casa com
   nenhum tier.
3. **`glama.json`.** Apontou que eu recomendava construir manifesto para um schema
   que não vi, de um requerente que não identifiquei. Verificado: é **prova de
   propriedade que exige conta e API key da Glama.ai** — rota proibida. **A
   recomendação foi invertida** (§6.1): troca-se pela grafia aberta
   `/.well-known/mcp.json`, e descobri no caminho que o portal já serve o schema
   oficial do MCP Registry em dois caminhos.
4. **As URN.** Apontou que eu chamei a gêmea de "pior" sem achar onde vivem as URN
   do HTML. Estão no JSON-LD, em `mentions` com `legislationIdentifier`, e **bem
   formadas**. O achado ficou mais nítido: mesmo objeto, duas serializações, e a
   de máquina é a que perde e corrompe o identificador (§2, Defeito A).

Também acatei: "até 365" em vez de 365 (o filtro de `render.go:470-477` pode
reduzir o servido); Amazonbot medido **na minha janela** (3.322, 35,5% — não os
34,2% que misturavam janelas); o `csp-report` nomeado como defeito de CSP vivo
(~3,6 violações por carregamento) e não curiosidade; e a comparação com
CourtListener/LexML marcada como **não medida nesta sessão**.

**O padrão comum aos meus quatro erros — e o motivo de §6.4 existir:** tomar
volume bruto, amostra única ou nome de arquivo como medição. Truncamento,
sonda própria, partida a frio e schema suposto são a mesma falha em quatro
roupas.
