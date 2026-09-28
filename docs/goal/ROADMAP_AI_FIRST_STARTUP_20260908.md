# Roadmap AI-first — a Wiki Jurídica como máquina de dados para IA (2026-09-08)

Documento de estratégia com número. Nasce da ordem do dono de 2026-09-08 ("máquina de dados
jurídicos para IAs valiosas; plataforma viva; startup jurídica brasileira, diferente de
qualquer outra") e de três levantamentos feitos no mesmo dia por subagentes — plataformas do
exterior (CourtListener, Legifrance/DILA, EUR-Lex/Cellar, legislation.gov.uk, CanLII, Perma.cc,
Pile of Law/LegalBench, Harvey/Ironclad via MCP), padrões e OSS de 2026 (MCP registry,
Web Bot Auth, RSL, Content-Digest RFC 9530, Memento RFC 7089, WebMCP, Agent Skills,
llms.txt) e o inventário da nossa própria superfície de máquina — mais a medição de quem de
fato nos lê. Tudo o que está marcado **[feito]** foi ao ar hoje; o resto está ordenado por
alavancagem medida, com dono.

## 1. O que a medição diz (origem, nginx, 8 dias, sem aquecimento)

| quem | páginas HTML | gêmea .md | rotas de máquina |
|---|---|---|---|
| PerplexityBot | 11.555 (redesocial/tema 2.596, glossário 917) | 0 | /buscar/ 7 |
| OAI-SearchBot | 3.957 | 787 | 0 |
| ChatGPT-User | 502 | 0 | /mcp 1 |
| Amazonbot | 581 | 289 | /api/v1/lote 1 |
| GPTBot | 0 | 45 | descritores 4, /api/v1/lote 2 |

- **Os agentes valiosos chegam pelo HTML e pela gêmea Markdown**, não pelas portas de
  máquina. `/mcp` tem 1.484 req/dia com **zero** agente de IA identificado (636 são
  scanners: sentineloracle, mcpbeat). `/llms.txt`, `/feed`, `/changes.json`: 0.
  Confirmado fora: 97 % dos `llms.txt` recebem zero bot (Ahrefs 2026); Google não o usa.
- Toda linha "404 de agente de IA" era **um scanner de segredos trocando o User-Agent**
  (GPTBot, Claude-User, PerplexityBot…). A métrica do mandato contava isso como agente.
  Corrigido: identidade por faixa de IP no evento unificado (`identidade_por_agente`).
- A cauda longa que já existe: 5.370 acórdãos do STJ com referência estruturada,
  18.663 arestas `cita` no grafo — pagas pelo parser, não pelo LLM.

**Consequência estratégica:** densidade e verificabilidade *no canal que eles já usam*
valem mais do que porta nova. A ordem abaixo segue isso.

## 2. O que a Wiki Jurídica já tem que nenhuma plataforma jurídica brasileira tem

- Mesma página em quatro serializações (HTML, Markdown, MCP, A2A) a partir do mesmo objeto.
- **Citação verificável** **[feito]**: `/api/v1/citar/{path}` com `html_sha256` (manifesto ==
  disco == bytes pela borda), `markdown_sha256`, `Repr-Digest` (RFC 9530) na gêmea e nos
  itens, ETag/304, referência ABNT. A pesquisa não achou padrão pronto de "citation API"
  fora — é lacuna de mercado.
- **Citation lookup** **[feito, deploy em cadeia]**: `POST /api/v1/citacoes` — texto → URN
  provada, URL oficial, páginas que citam a mesma norma. É a única chamada que um agente faz
  *durante* a geração (o padrão que criou demanda para o CourtListener).
- **Dumps públicos versionados** **[feito]**: `/datasets/` com corpus STJ (CC-BY), extrações
  por LLM, grafo (24.376 nós / 170.696 arestas), co-citação, metadados do acervo; sha256,
  licença, JSON-LD `DataCatalog`, bytes reproduzíveis (gzip `mtime=0`).
- Grafo jurídico com `risco_de_superacao` medido, `impacto`, `contexto_juridico` no MCP.
- Coleta oficial diária (STJ dados abertos), IA local 24/7 que só propõe, publicação por
  cadeia com hash.

## 3. O que falta para "plataforma viva" — ordenado por alavancagem, com dono

| # | item | por que viraliza / diferencia | custo | dono | estado |
|---|---|---|---|---|---|
| 1 | Densidade na página lida pelo agente: bloco `cite-as` + `describedby` para `/api/v1/citar` via header `Link` (mapa nginx, sem `--ressemear`) | descoberta pelo canal que os agentes já usam | baixo | maestro | próximo |
| 2 | **Radar de IA** (página humana diária): que temas os agentes verificados leem, por área, sem IP, aquecimento fora | "plataforma viva" visível ao humano; conteúdo que ninguém no Brasil publica | médio | maestro | próximo |
| 3 | Publicar `/mcp` no MCP Registry oficial (`server.json` já existe; DNS TXT; `MCP_REGISTRY_PRIVATE_KEY` já no `.env.local`) | descoberta por Claude/editores MCP sem SaaS | baixo | maestro | depois de 1–2 |
| 4 | Web Bot Auth (RFC 9421) na origem: identidade criptográfica de Claude/OpenAI/Perplexity | primeiro log honesto de quem é o bot; hoje é faixa de IP | baixo (Cloudflare já) / médio (Go) | revisora | fila |
| 5 | Benchmark jurídico PT-BR derivado do acervo (14.854 pares de FAQ; só páginas com proveniência `checked_at` e sem severidade crítica) | citação acadêmica obrigatória de quem avaliar LLM jurídico em PT | médio | maestro | licença primeiro (ver §4) |
| 6 | `sameAs` → QID do Wikidata em normas, tribunais, súmulas (campo já existe no JSON-LD) | entra no grafo de conhecimento que todo LLM consulta | baixo | maestro | fila |
| 7 | Memento (RFC 7089) sobre o ledger de revisão: `TimeMap` por página | "como estava antes" por padrão, sem formato próprio | médio | maestro | fila |
| 8 | URI dereferenciável por dispositivo (ELI-like) ao lado da URN LexML | link canônico por artigo, não só por diploma | médio | maestro | fila |
| 9 | Fila de IA local por valor (embeddings primeiro → `buscar_semantico` no `tools/list`; extração só onde rende) | busca semântica para agente > aresta marginal | baixo | revisora | decidido |
| 10 | `tools/list` pré-serializado; custo por porta medido antes/depois | barato para bot valioso; scanner não paga montagem | baixo | revisora | em curso |
| 11 | RSL `license.xml` + linha no robots | único padrão aberto de licença para IA; ninguém no BR declara | baixo | maestro | depois do §4 |
| 12 | XML/RDF por extensão de URL (legislation.gov.uk) | ferramenta que não fala Markdown nem MCP | médio | — | avaliar demanda medida |

Fora, com motivo: WebMCP (só Chrome, colide com a CSP de script único), ActivityPub (nenhum
agente consome), pay-per-crawl (conta/dashboard de terceiro), Hugging Face (exige conta e
chave — só com autorização nominal do dono, como a Google Indexing API).

## 4. A decisão que só o dono toma: licença do texto integral

A gêmea já sai com `Content-Signal: ai-train=yes, search=yes, ai-input=yes` e
`Content-Usage: train-ai=y`. Os Termos de Uso em `/termos/` vedam "reprodução integral ou
substancial… nem a coleta automatizada em massa". As duas declarações se contradizem. Por
isso os dumps publicados **não** trazem o corpo das páginas, e o benchmark (item 5) espera.
Recomendação de engenharia: CC BY 4.0 para o texto autoral com atribuição obrigatória
(`referencia_abnt` já sai pronta), mantendo o STJ em CC-BY do STJ; declarar em `/termos/`,
em `license.xml` (RSL) e no `datasets.json`. Sem isso, "máquina de dados" para treino é
promessa só nos cabeçalhos.

## 5. Dívidas declaradas hoje (todas com número no plano vivo)

- Fila de escrita v2: 86 vermelhos (32 mecânicos = esteira inteira; 46 redação; 8 editoriais).
- Nginx: 53 diretivas da rede social só no dedicado (fonte de verdade dividida).
- `mudancas_desde` zerado no ar desde o deploy das 20:07 (closure sobre `Server` congelado);
  correção + gate estático da revisora, deploy em cadeia com o lookup.
- Variante identity da gêmea velha no cache de origem após deploy (revisora).
- Extração por LLM na faixa "sem referência": denso reprovado (71 % sem item); braço pareado
  do híbrido decide se a faixa rende; 5 recusas do STJ são ano errado na fonte.
