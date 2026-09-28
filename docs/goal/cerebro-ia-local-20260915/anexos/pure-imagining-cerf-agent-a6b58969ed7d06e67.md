# CRÍTICO DE COMPLETUDE — o que as quatro arquiteturas deixaram na mesa

Medido por mim nesta sessão, no disco e na origem de /opt/wiki. Toda linha traz a
camada e o N de M. Onde não medi, escrevo "não medido" e por quê.

---

## 1. DADO MEDIDO QUE NENHUMA DAS QUATRO USA

### 1.1 O maior: **2.361 páginas NO AR que o próprio validador reprova por fonte oficial** [disco]

`data/editorial/v2_rewrite_queue.jsonl`: 3.201 linhas, **3.201 intents distintos**,
**um único `run_id`** (`v2-ingest-20260911T050000Z-v2-stock-merged-jsonl`) e
`validation_as_of` **2026-09-11** em todas as linhas — é um retrato de uma
validação só, não um acúmulo de execuções, então os números abaixo não contam a
mesma página duas vezes. **2.461** carregam `official_sources_insufficient`.
Cruzando com `data/editorial/published_manifest.jsonl` (11.106 paths):

| | N |
|---|---|
| intents com fonte insuficiente | 2.461 |
| **destes, JÁ PUBLICADOS** | **2.361** (21,3% do acervo) |
| nunca publicados | 100 |

E o precedente que ordena isso é **vinculante e citado por nome**:
`docs/PRECEDENTES_DAS_ORDENS.md:134-152` — *"Médio publica: fonte insuficiente
(decisão expressa do dono — 'faltando fonte não é proibido publicar, se tem
informação única')"*, seguido de: **"Publicar não encerra o defeito. O que entrou
como médio vira fila de refinamento com causa nomeada, e a correção é por gerador
datado."**

A fila existe e tem nome. **Nenhuma das quatro frentes a drena.** E o insumo que
a fecharia está no mesmo disco: **60.221 acórdãos do STJ com `fonte_url` e
`sha256_conteudo` por registro** (`data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl`),
mais 5.275 dispositivos, 398 súmulas e 2.347 temas no grafo.

A FRENTE ALAVANCAR gasta o eixo inteiro de "citabilidade" em C1–C5 (versão,
JSON-LD, título, URN, MCP resources) — **cinco itens de metadado e zero fonte
acrescentada a uma página**. Para um grounder, "fonte oficial insuficiente" pesa
mais que `version: sha256:`.

### 1.2 `risco_superacao.jsonl` — 4.986 páginas medidas, servido em UM canal que quase ninguém lê [disco + origem]

`data/ai/risco_superacao.jsonl` (9.399.568 B, regerado 2026-09-15 06:53):

| | N |
|---|---|
| páginas com risco medido | 4.986 de 11.106 = **44,9%** |
| **páginas SEM risco medido** | **6.120** |
| risco > 0 | 2.711 |
| risco ≥ 0,8 | 1.250 (todas no manifesto) |
| **risco = 1,0 (máximo)** | **1.190** |
| duplo defeito (risco ≥ 0,8 **e** fonte insuficiente) | 87 |

**Onde ele aparece:** só em `internal/httpserver/mcp_risco.go:19` (carga no boot) e
`internal/httpserver/mcp_contexto.go:300`, como **campo** `risco_de_superacao` da
ferramenta MCP `contexto_juridico`.

**Onde ele NÃO aparece** — `grep -rln "risco_superacao\|riscoDeSuperacao"` sobre
`internal/render/ internal/seo/ internal/pagemarkdown/ internal/structureddata/
internal/socialrender/ cmd/build/` devolve **zero arquivos**: nem HTML, nem gêmea
Markdown, nem JSON-LD, nem Atom, nem `/api/v1/citar`. E `grep -c -i superac` sobre
o `llms-full.txt` servido (1.586.684 B) devolve **0**.

**A ausência no HTML é decisão registrada; a ausência nos canais dinâmicos não é.**
`docs/goal/MAESTRO_CODEX_LOG.md:6380-6381` (2026-09-08) escreve, ao entregar o
gerador: *"Sem etiqueta no HTML: isso passa pela cadeia de publicação e pela
matriz `--ressemear`."* A razão é o **custo de publicação** — e ela é boa. Mas a
gêmea Markdown, o `/api/v1/citar`, o Atom e o `contexto_juridico` são **rota
dinâmica servida pelo Go**: não passam por `public/`, não pagam `--ressemear` e
não têm o custo que motivou o adiamento. **Ninguém, em nenhuma das quatro frentes
nem no log, perguntou por que os canais que não pagam o custo também não o têm.**

**Provado no byte servido.** `/tributario/execfiscal-penhora-salario-aposentadoria/`
tem risco **1,0** com **11 acórdãos julgados depois da revisão** (mais recente
2026-08-24). A gêmea que o portal serve para máquina
(`curl http://127.0.0.1:8088/…/index.md`, 10.692 B, UA do projeto +
`X-Warming-Request`) anuncia `reviewed_at: "2026-08-26"`, traz
`## Proveniência` e `## Como citar esta página` — e `grep -ci "superac\|risco"`
sobre ela devolve **0**.

O portal diz ao agente *"revisado em 26/08, cite assim"*, sabe internamente que 11
acórdãos posteriores citam os mesmos dispositivos, e não fala.

**O canal onde ele mora é o de menor USO medido — e o número é muito pior do que
"pouco tráfego".** Origem, 2026-09-15
(`data/ops/access/nginx-2026-09-15.jsonl`, 18.382 linhas, zero aquecimento):

| família | req |
|---|---|
| /redesocial | 9.626 |
| html (acervo) | 3.876 |
| gêmea `/index.md` | 1.967 |
| /mcp | 1.949 |
| /api/v1 | 540 |
| feed/sitemap | 344 |

**E o `/mcp` não é lido: é inventariado.** O ledger `data/ops/access/access-*.jsonl`
grava `mcp_method` e `mcp_tool` por requisição desde o commit `2a2b866e`
(**Tue Sep 8 15:17:11 2026**). A janela real do campo é **2026-09-08 a 09-16 —
9 dias, dois deles parciais** (09-08 com 677 linhas, 09-16 com 211; os dias
anteriores têm **zero** ocorrências do campo, conferido arquivo a arquivo).
Nessa janela, **12.358 requisições MCP** fora aquecimento e simulação:

| `mcp_method` | N (9 dias) |
|---|---|
| `tools/list` | **4.030** |
| `initialize` | 3.776 |
| `notifications/initialized` | 3.099 |
| `ping` | 432 |
| `server/discover` | 426 |
| `subscriptions/listen` | 142 |
| `notifications/cancelled` | 139 |
| **`resources/list`** | **114** |
| `prompts/list` | 107 |
| **`tools/call`** | **56** |
| **`resources/templates/list`** | **30** |

**56 chamadas de ferramenta em 9 dias — ≈ 6,2 por dia.** E as ferramentas
efetivamente nomeadas em `mcp_tool` somam **48 reais** (o resto são 8 sondas
`__verifymcp_auth_probe_*` e um nome falso):

`buscar_duvidas` 15 · `buscar_paginas` 14 · `duvidas_do_tema` 11 ·
`mudancas_desde` 5 · `search` 2 · `fetch` 1.

> **`buscar_semantico` 0 · `grafo` 0 · `impacto` 0 · `contexto_juridico` 0 ·
> `ler_pagina` 0 — em nove dias.** (O `risco_de_superacao` não é ferramenta: é
> **campo** de `contexto_juridico`, `internal/httpserver/mcp_contexto.go:300` —
> logo é servido por uma ferramenta com **zero** chamadas.)

Os três ativos que só o WikiJurídica tem (risco de superação de 4.986 páginas,
grafo de 393.081 arestas, busca semântica de 11.118 vetores) estão atrás de
ferramentas chamadas **zero vezes em nove dias**. O servidor é listado 4.030
vezes e usado 48. Nenhuma das quatro frentes abriu este ledger.

**Sobre `resources`, a leitura honesta — e ela NÃO é "demanda medida".**
`resources/list` 114 + `resources/templates/list` 30 = 144, contra **3.776
`initialize`**: são **3%** dos handshakes. Cliente MCP sonda `resources/list` e
`prompts/list` na conexão, como parte da descoberta de capacidade — é a mesma
classe de sinal que eu acabei de recusar para `tools/list`, e chamá-la de demanda
seria a inconsistência que o Fable pegaria. O que está medido é: **144 clientes
sondaram `resources` no handshake e receberam uma capacidade vazia.** Isso apoia
ALAVANCAR **P9** e REDE-DADOS **A12** como *higiene de protocolo* — nenhuma das
duas trouxe número nenhum (ALAVANCAR cita "1.671 sessões SDK/dia", que é outra
coisa e não foi verificada) — mas **não** prova que um recurso seria lido.

### 1.3 O grafo: `cocitada_com` = 139.521 arestas, 35,5% do total, com um consumidor só [disco]

`data/ai/grafo.sqlite` (`?mode=ro`), 393.081 arestas:

| tipo | N | fonte |
|---|---|---|
| cita | 151.424 | extrações (104.002) + corpus |
| **cocitada_com** | **139.521** | legal_cocitation_index 128.951 + frente-d 10.570 |
| julgado_por | 62.966 | |
| aplica | 22.789 | |
| da_area | 11.104 | |
| pertence_a | 5.275 | |
| revoga | **2** | |
| supera / altera / impactada_por | **0** | |

Nós: acordao 60.221 · pagina 11.104 · dispositivo 5.275 · tema 2.347 · sumula 398
· norma 327 · area 32 · tribunal 2.

A segunda maior classe de aresta do grafo alimenta **um** consumidor: o bloco
`## Percursos por fundamento legal` da gêmea, que a própria FRENTE ALAVANCAR mede
em 5.815 de 11.104 (52,4%) e propõe fechar (P16). Ninguém propõe o outro uso da
co-citação: **detecção de lacuna** — dispositivo com muita co-citação e pouca
página é pauta pronta, derivada sem uma chamada de modelo.

**Correção a uma alegação da FRENTE REDE-DADOS:** não há QID de Wikidata no grafo.
`select … from nos where atributos like '%wikidata%' or '%qid%'` devolve **zero
linhas**; os atributos do nó `dispositivo` são `['norma_base']` e nada mais. Os
38.018 QIDs vivem em `data/corpus/wikidata/lexml_qids.jsonl`, fora do grafo, e
`grep -rln "wikidata" --include=*.go internal/ cmd/` devolve **zero arquivos Go**.
Nenhum código Go do portal lê aquele arquivo — é um artefato órfão, não "em
superfície nenhuma".

### 1.4 DataJud: as duas dimensões que ninguém abriu, e um número do dossiê que o disco desmente [disco]

`data/research/datajud/`: 22 arquivos por tribunal + `ranking_nacional.json`.

**O que as quatro usam:** só `assuntos`, e só pelo agregado nacional.

**O que está lá e ninguém cita:**

| dimensão | conteúdo |
|---|---|
| `classes` | **312 classes processuais distintas** (ex. TJSP "Execução Fiscal" 21.364.836; STJ "Agravo em Recurso Especial" 1.972.911) |
| `graus` | **G1 161.909.008 · JE 63.125.140 · G2 32.080.813 · TR 12.067.590 · SUP 8.578.854 · TRU 68.629** |

O `graus` é a refutação silenciosa do produto inteiro: **161,9 M de processos em
primeiro grau e 63,1 M em juizado especial contra 8,6 M em tribunal superior.** O
acervo e o corpus falam de tese de tribunal superior; a demanda mora onde o
corpus não olha.

**Divergência a declarar:** o enunciado desta sessão traz "1.022 assuntos,
345.682.422 processos". No disco: **1.022 assuntos distintos ✓** (3.150 linhas de
assunto em 22 arquivos, deduplicadas) mas **283.415.422 processos**, coletados em
2026-08-07. `ranking_nacional.json` diz 400 assuntos / 283.415.422 / 22 tribunais.
Os 345,7 M não saem de nenhum dos dois; nenhuma frente declara a origem.

**E o instrumento está quebrado de um jeito visível no dado**, não só no código
que ALAVANCAR P14 nomeia: em `ranking_nacional.json`, o assunto *"Dívida Ativa
(Execução Fiscal)"* lista como exemplo `/aereo/bagagem-indenizacao-sem-nota-fiscal/`.
391 de 400 assuntos "têm página no acervo" por esse critério; os 9 sem página
somam 2.589.576 processos — o número que ALAVANCAR já declara inválido. Correto.

### 1.5 As 410 consultas reais — e a forma delas refuta o rótulo de "proxy" [disco]

`data/ops/bing_webmaster_daily.jsonl`, tipos vivos: `url_info` 888 ·
**`pagina_consulta` 437** · `consulta_diaria` 231 · `pagina_diaria` 218 ·
`busca_diaria` 35 · `rastreio_diario` 33 · `consulta_pagina` 3.

**411 pares (consulta → página) distintos, 410 consultas distintas, 43 páginas
distintas**, janela 2026-08-21 a 2026-09-11.

A FRENTE ALAVANCAR §5 declara essas consultas "busca clássica, declarada
**proxy**". Medi a forma antes de aceitar o rótulo:

- tokens por consulta: **p50 = 8**, média 8,9, **max 36**
- **117 de 229 (51,1%)** com ≥ 8 tokens
- 24 terminam em "?"
- e há consultas com **`#R##N#` e `#N#` literais no meio** — quebras de linha de
  **texto colado**, não digitado:

```
"estabilidade do dirigente sindical – desde o registro da candidatura até 1 ano
 após o término do mandato (art. #R##N#8º, viii, cf). – não se aplica ao suplente
 que não exerça funções efetivas (súmula 369 tst)."            (36 tokens)

"maria fez doação com reserva de usufruto: o filho recebeu a nua-propriedade,
 mas maria ficou com o uso e os frutos do imóvel.#N#com a morte da usufrutuária,
 o usufruto se extingue automaticamente.#N#nessa"              (32 tokens)
```

`#R##N#` é a codificação de CRLF do próprio Bing Webmaster Tools: marca consulta
**de várias linhas**, isto é, **texto colado**, não digitado. O dado **não
distingue** Copilot colando um trecho para ancorar de humano colando um parágrafo
na caixa de busca — e eu não afirmo o que não medi. O que está medido é a forma, e
ela é anômala para busca digitada: **p50 de 8 tokens e cauda até 36 não é
consulta de teclado**. É **compatível com** consulta de ancoragem e é, em
qualquer das duas leituras, **demanda real redigida pelo interessado**. Nenhuma
frente a trata como pauta — ALAVANCAR a classifica como proxy e segue para o
cruzamento DataJud, que ela mesma declara inválido. A alavanca (§2.C) vale nas
duas leituras.

Consumidores no repo: `tools/generate-painel` e `tools/experimentos.py` — **exibem**.
Nenhum gerador editorial.

### 1.6 Os 49.807 agravos: um uso, e o que falta [disco]

`cmd/generate-acordao-pages/main.go:311-324` (`classesProcedimentais`,
`procedimental()`) e `:514-517` (`elegivel` → `agravo_ou_embargo_nao_vira_pagina_propria`).
O motivo está escrito em `main.go:16`: *"Página própria para cada um seria doorway."*
**A recusa está certa para página própria** e a FRENTE ALAVANCAR erra ao tratá-la
como defeito de rótulo cego — o comentário do código dá a razão, e ela é boa.

A REDE-PRODUTO os usa bem, como denominador do índice de reforma (163 dos 233 do
exemplo do CDC art. 14).

**O que ninguém propõe:** usá-los pelo que são — **jurisprudência de
admissibilidade**. `cmd/generate-acordao-pages/main.go:328-333` já tem a lista
canônica (`sumulasProcessuais`: STJ 7, 83, 182, 211, 568; STF 279, 282, 283, 284).
"Por que o STJ não conhece o recurso" é conteúdo de altíssima demanda, derivável
sem modelo, em agregado (nunca página por acórdão), e hoje é rejeito.

### 1.7 A 2ª Seção parou em 2024-01-31 — e nenhuma frente diz [disco]

`data/corpus/jurisprudencia/stj-espelhos/cursor.json`:

| dataset | meses | janela | registros |
|---|---|---|---|
| terceira-turma | 52 | 2022-05 .. 2026-08 | 30.786 |
| quarta-turma | 52 | 2022-05 .. 2026-08 | 27.845 |
| **segunda-secao** | **21** | **2022-05 .. 2024-01** | **728** |
| primeira-turma | 3 | 2022-05 .. 2022-07 | 862 |

**Confirmado NA FONTE, não suposto.** Uma requisição de leitura a
`https://dadosabertos.web.stj.jus.br/dataset/espelhos-de-acordaos-segunda-secao`
(UA do projeto, 200, 117.816 B) anuncia **52 recursos `YYYYMMDD.json`, de
20220531 a 20260831**. O cursor tem 21. **Os 31 meses existem na fonte e nunca
foram colhidos.**

A FRENTE ALAVANCAR P11 enumera "os 6 ausentes + completar a 1ª Turma (3 de 52
meses)" e **não vê que a 2ª Seção está truncada há 31 meses**. Não é detalhe: a
**Seção é o órgão que uniformiza a divergência entre a 3ª e a 4ª Turma** — é
exatamente o produto que a REDE-PRODUTO vende, e o exemplo dela mostra "2ª Seção 1".

E o custeio de P11 muda de novo: 6 × 52 (assumindo a mesma janela — **não medido
na fonte para os 6**) + 49 (1ª Turma) + **31 (2ª Seção, medido)** = **≈ 392
recursos**, não 361 — com `-max-recursos` default 100
(`cmd/collect-stj-acordaos/main.go:62`) e Crawl-Delay 10, são **≥ 3 passadas**, não
"1 h". A janela real dos 6 ausentes se mede do mesmo jeito: uma leitura por
página de dataset.

### 1.8 Os ZIPs históricos: a alegação do dossiê é contradita pelo código, e ninguém mediu

`internal/stjacordaos/dataset.go:32-34`:

```go
// Ele NAO casa /api/ nem /revision/ por construcao, e ignora os .zip e os
// .csv do mesmo dataset, que sao empacotamentos do mesmo conteudo.
reRecurso = regexp.MustCompile(`href="(https://[^"]+/download/(\d{8})\.json)"`)
```

O dossiê diz "~460 MB de ZIPs que o regex nunca leu", como se fosse descuido. É
**decisão declarada**. Mas comentário é alegação (R1): se o ZIP contiver meses
anteriores a 2022-05 (onde todos os quatro datasets começam), a frase "mesmo
conteúdo" é falsa e o corpus tem anos inteiros a ganhar de graça.
**NÃO MEDIDO por mim** — exigiria requisição de saída ao STJ sob Crawl-Delay 10, e
esta sessão é somente leitura. **Nenhuma das quatro mediu, e todas as quatro
opinaram.**

### 1.9 Os 11.118 vetores: usados, e o uso que fecha o laço não foi proposto [disco]

`data/ai/embeddings/ativo.json`: `qwen3-embedding:0.6b`, dim 1024, **11.118
páginas**, gerado 2026-09-15T15:29:55Z (não 11.248 — esse é o total de tarefas
`embed_pagina` concluídas na fila). `vetores.f32` = 46.071.808 B.

Consumidores reais: `internal/httpserver/mcp_semantico.go`,
**`internal/v2relatedpages/relatedpages.go`** (a malha de links interna),
`internal/cerebro/*`, `internal/oabpolicy`, `cmd/collect-oracle/catalog.go`,
`cmd/publish-v2-direct`. A ALAVANCAR P14 propõe usá-los no cruzamento DataJud —
**crédito, é o uso certo**.

O que ninguém propõe, e é o mais barato do documento: **encostar os 11.118 vetores
nas 410 consultas medidas** (§1.5). Sai de graça (a) a página que responde cada
consulta real e (b) **a consulta real que nenhuma página responde** — pauta com
demanda provada, sem coletar nada e sem o critério quebrado do DataJud.

---

## 2. ALAVANCAS DE CRESCIMENTO QUE NENHUMA PROPÔS

**A. Mudar o risco de superação de canal — a alavanca com a melhor razão do
documento, EM DOIS TEMPOS (e o segundo é o que importa).** 2.711 páginas com risco
> 0 e 1.190 em risco 1,0, com fontes, datas e URLs por linha, hoje atrás de uma
ferramenta MCP chamada **0 vezes em nove dias**.

- **Tempo 1, de graça:** bloco `## Risco de superação` na gêmea Markdown e campo
  em `/api/v1/citar`. São **rota dinâmica servida pelo Go**: não tocam `public/`,
  não pagam `--ressemear`, e o único motivo registrado do adiamento
  (`MAESTRO_CODEX_LOG.md:6380-6381` — *"passa pela cadeia de publicação e pela
  matriz `--ressemear`"*) **não se aplica a eles**. Alcança 1.967 + 540 req/dia na
  origem.
- **Tempo 2, o que de fato importa, e que não posso omitir:** essa camada **não
  alcança quem responde**. A borda mede a classe que responde lendo o **HTML
  3.326×** e a **gêmea 26×** por dia (128×). Para chegar a ChatGPT-User,
  oai-searchbot, Applebot e Perplexity, o risco precisa estar **no HTML**.
- **E o HTML tem uma armadilha que o log não nomeia:** o risco **muda** a cada
  acórdão colhido. Um bloco cru no HTML re-hashearia e **re-dataria o acervo
  inteiro a cada atualização do corpus** — a mesma classe do ataque do Fable ao C2
  da ALAVANCAR. A saída já existe no repo:
  `tools/generate-page-content-revision:335-355` **neutraliza**
  `<section aria-labelledby="conteudos-relacionados">`. Um bloco irmão, declarado
  na mesma lista de neutralização, custa **uma** passada `--ressemear` (que se
  agrupa com a de C-1) e depois **nunca mais re-data**, por mais que o número
  mude.

Sem o tempo 2, a alavanca A entrega citabilidade à classe que **varre**, não à que
**responde**. Nenhuma das quatro frentes desenhou nem o tempo 1 nem o tempo 2.

**B. Drenar a fila de refinamento de fonte com o corpus.** 2.361 páginas
publicadas × 60.221 acórdãos com `fonte_url` + `sha256_conteudo`. É a ordem do
dono de 2026-08-06 executada, não uma ideia nova.

**C. Pauta por consulta medida + vetor.** §1.5 + §1.9. Zero coleta, zero modelo,
critério válido — contra o OR-de-um-token que ALAVANCAR já declara inválido.

**D. Abrir o `graus` do DataJud.** 161,9 M em G1 e 63,1 M em juizado. Todo o plano
de volume (V1/V2/V3) persegue acórdão de tribunal superior, que é 8,6 M (3,0%).

**E. Agregado de admissibilidade a partir dos 49.807 agravos** (§1.6).

**F. Completar a 2ª Seção** (§1.7) — sem ela o "mercado de divergência" não tem o
órgão que resolve divergência.

**H. Parar de tratar o MCP como canal de produto e tratá-lo como o que ele é:
vitrine.** Medido: 4.030 `tools/list` contra **48 chamadas reais** em 9 dias, e
144 sondagens de `resources` no handshake que recebem capacidade vazia. Os agentes
**listam** o servidor e **não o usam**. Isso reordena tudo: o trabalho que vale é
(i) **tirar os ativos de dentro das ferramentas** e pô-los nos canais que já são
lidos (alavanca A), (ii) entregar `resources` como higiene de protocolo, barato,
sem prometer retorno, e (iii) **não** construir um quinto canal MCP de escrita
antes de o quarto ser usado. Nenhuma frente mediu isto, e três delas investem no
MCP como se ele fosse o produto.

**G. Derivar `agentesValiososParaRanking` da taxonomia canônica.** Medido nos dois
sentidos agora: `tools/botagents.funcao_de` diz gptbot=**training**,
claudebot=**training**, amazonbot=**training**, applebot=**search**,
claude-user=**user**. A lista de `cmd/cerebro/comentarios.go:42-50` declara em
comentário que mede "leitura por IA que CITA, não rastreamento de indexação
genérica" e então **admite dois crawlers de treino (amazonbot, claudebot) e exclui
um de busca (applebot, 519 req/24 h na borda, a porta de Siri/Spotlight) e o
claude-user**. É uma cópia manual de um mapa canônico que já existe no repo, e ela
decide quais salas o cérebro enche primeiro. A REDE-PRODUTO nomeia o defeito e
escreve "este plano não o conserta"; as outras três não o veem.

---

## 3. CONFLITOS ENTRE AS QUATRO

### C-1 — `--ressemear`: uma frente pede, outra proíbe, e a flag é DA PASSADA
- ALAVANCAR **P6**: `deploy-publico --ressemear` (JSON-LD é markup servido).
- REDE-PRODUTO **passo 7**: deploy **SEM** `--ressemear` (dossiê = texto
  editorial) — e acrescenta `<section>` nova ao HTML do acervo.

`--ressemear` governa a **passada**, não a página (CLAUDE.md §6). As duas mudanças
pousam nas mesmas ~11.106 rotas. Numa passada só, a flag de uma delas está errada
por construção; em passadas separadas, o acervo é republicado 2×, e o contrato
mede que os bots que revalidam rebaixam o acervo junto. **Serializa: uma janela de
publicação, uma decisão de flag, e o hasheador de revisão
(`tools/generate-page-content-revision:335-355`) auditado antes contra as duas
mudanças juntas.**

**Correção que tira uma frente do conflito, e vira achado próprio:** REDE-DADOS
**A10** não pertence a C-1. O ClaimReview dela mora em
`internal/socialrender/socialrender.go:435` — **página dinâmica do
`cmd/social:8091`, sem artefato em `public/`, com `s-maxage=3600`**. Não há
`deploy-publico` no caminho e `--ressemear` não se aplica. A frase da A10
(*"JSON-LD novo no HTML ⇒ `--ressemear`"*) é **erro de categoria**: aplica a
matriz de publicação do **acervo estático** a uma **superfície dinâmica**. O risco
prático não é publicar errado — é a frente gastar um passo de publicação que ela
não precisa e, pior, ficar convencida de que a purga do deploy a cobre, quando o
que a cobre é o `deploy-binario-go` (binário → socket → serviço → invalidar
origem → purgar borda).

### C-2 — três gates de citação, em três pacotes, em direções opostas
| frente | arquivo | o que faz com a mesma pergunta |
|---|---|---|
| REDE-MODERACAO passo 4 | `internal/cerebro/gate.go` | `fonte_fora_do_payload` **rebaixa a aviso** |
| REDE-PRODUTO passo 5 | `internal/cerebro/gate.go:255-259` | **aperta**: duas condições cumulativas |
| REDE-DADOS A6 | `internal/socialconteudo/gate.go` | terceira régua, `AvaliarRefutacao` por `legalfacts` |

MODERACAO **passo 2** ainda move o pacote inteiro para `internal/pecagate`, o que
apaga as linhas que PRODUTO edita. E a memória desta máquina tem regra literal
para isto: *"3ª correção do mesmo subsistema = parar e atacar a família inteira"*
(`anti-looping-e-concorrencia.md`). São três correções do mesmo subsistema em três
pacotes. **Serializa: uma frente só define onde mora a régua de citação, e as
outras duas chamam.**

### C-3 — `cmd/social/interno.go`, o mesmo `switch`
REDE-DADOS **A8** acrescenta `refutacao` + `decisao_de_moderacao`; REDE-PRODUTO
**passo 8** acrescenta "terceiro tipo para tese de pauta"; REDE-MODERACAO precisa
da régua em `:650` (`recusaPeloArt42Interno`). Mesma função, três frentes.

### C-4 — `internal/httpserver/mcp.go`, três vezes
ALAVANCAR **P9** (`AddResourceTemplate`, :238-243), REDE-DADOS **A12** (resources +
`ler_refutacoes` + gate dos três inventários), REDE-PRODUTO **passo 8**
(ferramenta de escrita, :388). Duas delas entregam `resources` — trabalho
duplicado, e o gate de igualdade dos inventários é pedido por duas.

### C-5 — `content/social_policy.json`, três vezes, todas com a ordem que o precedente desmente
Ver §5.

### C-6 — o grafo é RECONSTRUÍDO do zero: aresta escrita no sqlite morre na próxima passada
Este é pior do que "precisa de migração". `tools/generate-grafo-juridico` carrega
o DDL inteiro numa constante (`CREATE TABLE nos` :95, `CREATE TABLE arestas` :103,
`CREATE TABLE meta` :126) e o cabeçalho :70 declara o método: *"escreve num
arquivo temporário e troca por `os.replace` — quem lê nunca vê o…"*, com
`tempfile.mkstemp(prefix=".grafo-", …)` em :688. **Cada execução monta um banco
novo e o substitui atomicamente.** `cmd/generate-revisao-extracoes/main.go:224`
confirma: `data/ai/grafo.sqlite` é *"função pura"* das suas entradas.

Consequência que nenhuma frente vê:

- REDE-PRODUTO **passo 3** quer `acordao→orgao` e `acordao→relator` no grafo — e
  o `CHECK` fecha em 10 tipos, sem esses dois (`julgado_por` já está tomado, com
  62.966 arestas);
- REDE-DADOS quer que o cérebro **derive `supera/altera/impactada_por`** das
  refutações. Esses três **estão** no CHECK (hoje em 0) — mas se forem escritos
  direto no sqlite, **a próxima geração os apaga**, sem erro e sem rastro.

Os dois passos só existem se entrarem **como entrada do gerador**, não como
escrita no banco. Nenhuma das duas frentes diz isso.

---

## 4. O QUE NENHUMA MEDIU E DEVERIA TER MEDIDO ANTES DE PROPOR

1. **Quantas páginas publicadas o próprio validador reprova por fonte.** 2.361 de
   11.106 (21,3%). Medi agora. As quatro falam de citabilidade sem este número.
2. **A forma das consultas do Bing**, antes de chamá-las de proxy (§1.5).
3. **A lacuna de meses da 2ª Seção** (§1.7), num plano que enumera o corpus.
4. **Se os ZIPs cobrem ano que o `.json` não cobre** (§1.8) — ninguém mediu, todas
   opinaram.
5. **A cobertura do próprio risco de superação:** 4.986 de 11.106 (44,9%);
   **6.120 páginas sem risco medido**. Nenhuma frente sabe que o instrumento cobre
   menos da metade do acervo.
6. **A vazão de `gerar_comentario_autoridade`, e só ela.** Correção a uma leitura
   apressada minha e do Fable da REDE-DADOS: o caminho **não** tem zero execuções.
   `data/ai/comentarios_gerados.jsonl` (8.669 B, 2026-09-09 14:28) tem **3 peças
   reais**, com custo medido — `qwen3.5:4b`, prompt 1.734/1.746/1.864 tok, eval
   360/461/418 tok, **4,80–5,28 tok/s**. O custo unitário **está medido para n=3** e
   é a base do oráculo da MODERACAO.
   O que **não** existe: `select distinct tipo from tarefa` em
   `data/ai/fila.sqlite?mode=ro` devolve **três** tipos — `embed_pagina`,
   `extrair_dispositivos`, `medir_modelo`. **O tipo nunca entrou na fila**, então
   não há uma única medição de comportamento em fila: prioridade efetiva,
   concorrência com `extrair_dispositivos` (34.022 pendentes) e vazão sustentada.
   É esse o número que falta para dimensionar 11.039 salas, e é dele que o ataque
   de prioridade do Fable (`fila.go:74` DEFAULT 0 contra pendentes em −23..−6)
   depende.
7. **O teto de chamadas/hora da purga de borda** — REDE-DADOS o nomeia como não
   medido (crédito); as outras três dependem dele sem citá-lo.
8. **A distribuição do risco por área.** Nenhuma. Medi só o agregado.
9. **O uso real do MCP, que já está gravado desde o commit `2a2b866e`
   (2026-09-08).** Três frentes investem no MCP (ALAVANCAR P9, REDE-DADOS A12,
   REDE-PRODUTO 8 e 12) e **nenhuma abriu `mcp_method`/`mcp_tool`**. 56
   `tools/call` em 9 dias, e zero para as cinco ferramentas que carregam os ativos
   distintivos (§1.2). REDE-PRODUTO chegou a afirmar que o registro não existe —
   ele existe e refuta a tese que o passo serviria.

---

## 5. PRECEDENTES DO REPOSITÓRIO QUE CONTRADIZEM AS FRENTES

**P-1 — `docs/PRECEDENTES_DAS_ORDENS.md:134-152` (2026-08-06, VINCULANTE).**
*"Médio publica: fonte insuficiente… Publicar não encerra o defeito. O que entrou
como médio vira fila de refinamento com causa nomeada, e a correção é por gerador
datado — nunca editando JSONL à mão."* A fila tem 2.361 páginas no ar; nenhuma
frente a drena. **Contradiz o silêncio das quatro.**

**P-2 — `docs/PRECEDENTES_DAS_ORDENS.md:316-325` (2026-09-09).** A ordem executada
foi: *"O campo **saiu do disco**, o binário subiu (12:43) e **só então** o campo
voltou, com um restart medido."* Regra que ficou: *"dado de configuração que o
binário vivo não parseia só entra no disco **no mesmo passo em que o binário novo
sobe**."*

REDE-DADOS **A5**, REDE-MODERACAO (ordem obrigatória) e REDE-PRODUTO **passo 8**
escrevem, as três, **"binário no disco → JSON → swap → restart"**. Entre "JSON" e
"swap" o binário **velho** está no ar com um JSON que ele rejeita, e a unit tem
`Restart=always`. O precedente mandou o oposto. **Contradiz as três.**

**P-3 — `docs/PRECEDENTES_DAS_ORDENS.md:303-315` (2026-09-09, o teto de 5
respostas).** *"A plataforma é informativa e própria, não é captação; ética se
cobra pelo conteúdo. O teto virou parâmetro de auditoria… e o gate ficou onde ele
morde: promessa, preço, caso concreto, citação inventada."*

REDE-MODERACAO acrescenta `PisoDeAncorasEspecificas` como **bloqueio de
publicação**. Piso de âncora não está na lista de onde o gate morde, e a mesma
seção fixa: *"política que bloqueia o objetivo da plataforma se flexibiliza com
data, motivo e teste"*. Com a rede em 0 dúvidas / 0 respostas / 0 comentários, um
piso novo de bloqueio anda **contra** a direção do precedente. **Contradiz a
MODERACAO na direção, não no mérito do piso.**

**P-4 — `docs/PRECEDENTES_DAS_ORDENS.md:273-280` ("o caso das 46").** *"Detector
novo nasce com teste de falso positivo sobre amostra real."* MODERACAO passo 9 e
REDE-PRODUTO passo 6 escrevem a régua FP; **ALAVANCAR P4 cria
`tools/check-versao-confere-com-artefato` sem nenhum teste de falso positivo** — e
o Fable já mostrou que a ferramenta duplica `tools/check-served-vs-manifest`.

**P-5 — `git log` desmente o passo 12 da REDE-PRODUTO.** Ela pede "contador por
tool no handler → `data/ops/mcp_ferramenta_invocada_daily.jsonl`", justificando:
*"Hoje são 13.364 POSTs JSON-RPC em 8 dias e **ZERO registro de qual ferramenta
foi chamada**; o §12 do contrato não tem numerador sem isto."* **Falso, e
construído há dias:** commit `2a2b866e — feat(medicao): o ledger de acesso grava
qual ferramenta MCP cada agente chamou`. Os campos `mcp_method` e `mcp_tool`
estão em `data/ops/access/access-*.jsonl` e foi deles que saiu a medição do §1.2
(56 `tools/call` e 48 ferramentas nomeadas em 16 dias). O passo 12 construiria de
novo o que existe — e, pior, o número que ele diz não ter é justamente o que
refuta o MCP como canal de produto.

**P-6 — `docs/goal/MAESTRO_CODEX_LOG.md:6380-6381` (2026-09-08).** A ausência do
risco de superação no HTML é **decisão registrada com motivo** (*"passa pela
cadeia de publicação e pela matriz `--ressemear`"*), e o motivo **não alcança** a
gêmea, o `/api/v1/citar` e o Atom, que são rota dinâmica. Nenhuma frente leu esse
registro, e por isso nenhuma viu que a porta barata continua aberta (§1.2).

**P-7 — `870d4485 fix(cerebro): mundo fechado de citação por chave e tipo — o
primeiro comentário real reprovou pelo gate, não pelo texto`.** O mundo fechado
que REDE-PRODUTO (passo 5) e REDE-MODERACAO (passo 4) propõem mexer **já foi
corrigido uma vez**, com o caso concreto no título do commit. Terceira mexida no
mesmo predicado, por duas frentes, em direções opostas (C-2) — é o gatilho literal
de `anti-looping-e-concorrencia.md`.

---

## 6. A REDE SOCIAL CABE JUNTO? ONDE COMPETE, E O QUE SERIALIZA

**Recurso de máquina: não é o gargalo da REDE, e é o gargalo dos COMMITS Go.**
Medido agora: `load average 4.33` (1 min), RAM **16 de 19 GiB usada, 3 GiB
disponível**. A fila do cérebro drena (34.217 → 34.118 → 34.085 → 34.022 ao longo
da sessão ≈ 100/h). O Ollama já tem `MemoryMax=12G` e a slice em peso 20.

- **Para a rede social em si, não é gargalo:** 0 dúvidas, 0 respostas, p50 de 3 ms
  medido pela REDE-DADOS.
- **Para os commits Go, é O gargalo, e está medido no repo:** o pré-commit custou
  **75 s com o Ollama trabalhando contra 29 s com o cérebro pausado**
  (`docs/goal/MAESTRO_CODEX_LOG.md`, 2026-09-08; CLAUDE.md §12). Com 3 GiB livres e
  o earlyoom já tendo disparado a 4,7%, **quatro frentes commitando Go são quatro
  ciclos de compilação disputando a mesma máquina que o LLM ocupa** — além do
  `/tmp/opt-wiki-commit.lock` e da bancada diária, que segura o `flock` pesado por
  70–90 min.

**O que compete de verdade é ARQUIVO e JANELA DE PUBLICAÇÃO, não CPU:**

| recurso disputado | quem disputa | serializa como |
|---|---|---|
| `internal/cerebro/gate.go` + `socialconteudo/gate.go` + `oabgate` | MODERACAO, PRODUTO, REDE-DADOS (C-2) | **uma frente define onde mora a régua de citação; as outras chamam.** É o gargalo real da rede social. |
| `cmd/social/interno.go` switch de tipos | REDE-DADOS, PRODUTO, MODERACAO (C-3) | um commit acrescenta os tipos de uma vez |
| `internal/httpserver/mcp.go` | ALAVANCAR, REDE-DADOS, PRODUTO (C-4) | `resources` entra uma vez só |
| janela de `deploy-publico` | ALAVANCAR P6, REDE-DADOS A10, PRODUTO 7 (C-1) | **uma passada, uma decisão de flag** |
| `content/social_policy.json` + swap do binário social | as três (C-5) | uma seção, um swap, na ordem do P-2 |
| `/tmp/opt-wiki-commit.lock` + índice limpo | todo commit Go | já é regra do contrato |

**Veredito:** a rede social **é implementável junto**, porque o que ela exige de
CPU é quase zero hoje (0 dúvidas, 0 respostas, p50 de 3 ms medido pela REDE-DADOS)
e o que ela exige de máquina de IA está travado por outra coisa (§7). O que **não**
cabe junto é **quatro frentes editando a mesma família de gates e a mesma janela de
publicação**. Serializa por arquivo, não por relógio.

---

## 7. O QUE DEPENDE DE ALGO QUE NÃO EXISTE, E NINGUÉM PROPÕE CONSTRUIR

Verificado por mim, no disco:

1. **`data/ai/publicacoes_cerebro.jsonl` não existe.** O ledger de proveniência que
   a DEC-059 exige para toda publicação do cérebro nunca foi escrito. As três
   frentes de rede social publicam por esse caminho.
2. **`perfis_advogado` = 0 linhas** (`var/social/social.db?mode=ro`; `perfis` 1,
   `contas` 1, `temas` 11.039, todo o resto 0). Sem inscrição deferida, nenhuma
   peça sai sob a assinatura do advogado. Só o Fable da REDE-PRODUTO nomeou.
3. **O tipo de tarefa `gerar_comentario_autoridade` nunca existiu na fila** (§4.6).
   O executor está no código e jamais foi exercido.
4. **A GPU não está no host.** Todo o §7 da ALAVANCAR (a fila drenando em horas, o
   14b usável, o segundo modelo que habilita recurso de JUÍZO na MODERACAO) é
   derivado de hardware ausente.
5. **O método da API de IA do Bing não existe** (40 nomes → 404). Os ~23.000 são
   leitura de painel.
6. **O artefato das 2.488 páginas da passada exaustiva não foi achado** — a
   ALAVANCAR já declara isso e cria P12 para substituí-lo. Crédito.
7. **`tier_a_artigos.jsonl` é de 2026-09-10 05:25** — 5 dias, e é pré-requisito de
   V2/V3.

8. **A ATRIBUIÇÃO das extrações — o alicerce que ninguém escora.** O enunciado já
   traz medido: **15,51% dos itens do modelo não têm o número do artigo dentro do
   próprio `texto_citado`** e **19,0% só se apoiam na folga de
   `NormaAtestadaNoTexto`** (`internal/cerebro/triagem.go:195-230`, que testa a
   norma no texto **inteiro**). Essas extrações são **104.002 arestas `cita` =
   26,5% do grafo** (`data/ai/extracoes_dispositivos.jsonl`, medido por mim na
   coluna `fonte` das arestas).

   Sobre elas se apoiam, simultaneamente: o **risco de superação** (deriva do
   grafo — `MAESTRO_CODEX_LOG.md:6368`), a **divergência** da REDE-PRODUTO (cujo
   próprio Fable mediu **71,2% das 233 arestas do exemplo vindas da extração, não
   do campo oficial**) e os **Percursos** da ALAVANCAR. **Nenhuma das quatro
   propõe apertar a regra de atribuição**, e nenhuma propõe separar, na
   superfície, o subconjunto atestado pelo campo oficial do subconjunto inferido.
   É a fundação de três produtos, e está com uma folga medida de ~19%.

**E o que ninguém propõe construir, embora o dado já esteja pago e no disco:**

- o **dreno** da fila de refinamento de fonte (2.361 páginas × 60.221 acórdãos);
- o **produtor de fonte** que transforma acórdão do corpus em fonte oficial de
  página do acervo;
- a **superfície de risco de superação** fora do MCP;
- o **mapa consulta↔página** a partir das 410 consultas medidas e dos 11.118
  vetores;
- o **fechamento do risco** para as 6.120 páginas sem medição.

---

## 8. O QUE O ADVISOR MUDOU

Uma chamada, oito apontamentos, **três bloqueantes — e os três viraram medição
nova que mudou o conteúdo, não só a redação**:

1. **Q5 pedia três fontes e eu tinha lido uma.** Fui a `docs/goal/MAESTRO_CODEX_LOG.md`
   e ao `git log` dos arquivos em conflito. Vieram **três precedentes novos**: P-5
   (o commit `2a2b866e` já grava a ferramenta MCP chamada, refutando o passo 12 da
   REDE-PRODUTO), P-6 (`:6380-6381`, a ausência do risco no HTML é decisão
   registrada cujo motivo **não** alcança os canais dinâmicos) e P-7 (`870d4485`,
   o mundo fechado do gate já foi corrigido uma vez). O P-5 abriu o ledger que
   produziu a medição mais forte do documento (§1.2: 56 `tools/call` em 16 dias).
2. **Eu escrevera "caminho com zero execuções" e era falso.** `data/ai/comentarios_gerados.jsonl`
   tem 3 peças reais com custo medido (4,80–5,28 tok/s). Corrigi §4.6: o custo
   unitário **está** medido para n=3; o que falta é comportamento em fila.
3. **Eu afirmara "31 meses truncados" sem consultar a fonte.** Uma leitura de
   `dadosabertos.web.stj.jus.br/dataset/espelhos-de-acordaos-segunda-secao` (200,
   117.816 B) contou **52 recursos, 20220531..20260831**. Os 31 meses existem — a
   afirmação passou de suposição a medição, e o custeio de P11 ficou honesto
   (a janela dos 6 datasets ausentes segue **não medida**, e está dito).
4. **`#R##N#` era inferência minha, não fato.** É a codificação de CRLF do próprio
   Bing: prova **texto colado**, não prova **assistente**. Reescrevi para
   "compatível com; indistinguível no dado", mantendo o que está medido (p50 8
   tokens, 51,1% ≥ 8, max 36) e a alavanca, que vale nas duas leituras.
5. **Eu larguei a checagem de reconstrução do grafo no caminho errado.** O gerador
   é `tools/generate-grafo-juridico`, e ele monta o banco inteiro num temporário e
   troca com `os.replace` (:70, :688). Isso **escalou o C-6**: aresta escrita direto
   no sqlite morre na próxima passada, em silêncio — o que atinge REDE-PRODUTO
   passo 3 e as arestas `supera/altera` da REDE-DADOS.
6. **Faltava a atribuição das extrações no §7.** Entrou como item 8: 26,5% do
   grafo vem de extração com folga medida de ~19%, e três produtos se apoiam nela.
7. **Eu descartara a RAM rápido demais.** Reescrevi: não é gargalo da rede (0
   conteúdo, p50 3 ms), **é** o gargalo dos commits Go concorrentes (75 s contra
   29 s, medido no repo).
8. **Duas afirmações a mais do que o dado sustentava.** "gptbot 1 no /mcp" virou a
   medição correta por método e ferramenta; e a ausência do risco no
   `llms-full.txt` passou de suposta a medida (`grep -c -i superac` = 0 sobre os
   1.586.684 B servidos).

Nada do que o advisor apontou contradisse medição minha; os três bloqueantes eram
lacuna de medição, e medi os três.

**Segunda chamada, seis apontamentos, dois bloqueantes — e um deles derrubou um
número meu:**

9. **BLOQUEANTE — a janela do ledger MCP era de 9 dias, não 16.** O campo
   `mcp_method` nasce com o commit `2a2b866e` (**Tue Sep 8 15:17:11 2026**) e os
   arquivos de 09-01 a 09-07 têm **zero** ocorrências (conferido um a um). Corrigi
   tudo: **56 `tools/call` em 9 dias ≈ 6,2/dia**, e os zeros de `buscar_semantico`,
   `grafo`, `impacto`, `contexto_juridico` e `ler_pagina` valem para **nove** dias.
   O achado sobrevive inteiro; a taxa estava subestimada em 1,8×.
10. **BLOQUEANTE — a fila de reescrita podia estar acumulando execuções.** Não
    está: **um único `run_id`**, `validation_as_of` **2026-09-11** em todas as
    3.201 linhas. O 2.461/2.361 (21,3% do acervo) **se sustenta**, datado.
11. **A alavanca A, como eu a escrevera, não alcançava quem responde.** A gêmea
    recebe 26 das 3.326 requisições diárias da classe que responde (128× a favor do
    HTML), e o risco muda a cada acórdão — um bloco cru no HTML re-dataria o acervo
    a cada atualização. Reescrevi em dois tempos, com a saída que já existe no repo
    (`generate-page-content-revision:335-355` neutraliza uma `<section>` nomeada;
    um bloco irmão custa uma passada e nunca mais re-data).
12. **`resources/list` = 144 não é demanda.** Era a mesma classe de sinal que eu
    acabara de recusar para `tools/list`: 3% dos 3.776 handshakes, sondagem de
    capacidade. Reescrito como higiene de protocolo, com o crédito a P9/A12
    mantido e a promessa de retorno retirada.
13. **C-1 tinha um membro falso.** REDE-DADOS A10 serve ClaimReview em
    `socialrender/socialrender.go:435`, superfície **dinâmica** do `cmd/social:8091`
    — `--ressemear` não se aplica. Virou achado próprio: erro de categoria (matriz
    do acervo estático aplicada a rota dinâmica).
14. **Precisão:** `risco_de_superacao` é **campo** de `contexto_juridico`
    (`mcp_contexto.go:300`), não ferramenta. Corrigido nos dois pontos.
