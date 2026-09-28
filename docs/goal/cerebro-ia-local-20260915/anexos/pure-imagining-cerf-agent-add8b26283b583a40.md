# SEÇÃO A — Alavancagem IA-first: crescer a citação

> **Regra de leitura.** Toda afirmação numérica traz `[camada]` e um selo
> `MEDIDO` (por mim, nesta sessão) / `DERIVADO` (cálculo sobre número medido, com
> a fórmula à vista) / `A MEDIR` (não medido, e o porquê). Camadas: `borda` (API
> Cloudflare) · `origem` (nginx/Go em 127.0.0.1) · `disco` · `painel-bing` ·
> `fonte` (GET à fonte oficial). **Nenhum número de camada inferior é apresentado
> como teto** (REGRA ZERO-C).

## A.1 O diagnóstico em números, com a camada declarada

### A.1.1 Alcance real [borda], 24 h

88.033 req totais · 17.325 de bot identificado (19,7%) · 6.921 agentes de IA.
Classe que **responde** (ChatGPT-User 1.115 + OAI-SearchBot 1.233 + Applebot 530 +
PerplexityBot 363 + Googlebot 111) = **3.352**, das quais **3.326 no HTML** e
**26 na gêmea (0,8%)** → **128×**. Classe que **treina** (Amazonbot 3.446 + GPTBot
241 + meta-externalagent 18) = 3.705, e lê a gêmea a 35-58%.
Aquecimento nosso: **73,0% da borda (866.020)**, fora da conta.
**30,7% (26.834 req) sem `agent_key`** — 15.493 são agentes que se declaram e o
registro não conhece (`meta-externalads/1.1` 8.485, `AionBot/1.0` 7.008).

**A leitura que ordena tudo:** densidade colocada só na gêmea alcança 26 req/24 h.
Isso não condena a gêmea — ela é o canal de quem varre — mas proíbe tratá-la como
a alavanca de citação.

### A.1.2 Citação: um consumidor medido, um teto que não é nosso

**~23.000 citações** no relatório "Desempenho de IA" do Bing `[painel-bing]`,
leitura de painel na conta do dono. **Não existe API**: 40 nomes candidatos → 404,
`$metadata` → 404, e a resposta aceita no Microsoft Q&A (2026-02-19) diz "no API
is mentioned so the answer is not right now". Grava-se como **linha datada**, nunca
como série. **A busca clássica NÃO é a medida de citação:** 440 impressões, 77
cliques, 229 consultas (08-21 a 09-11) `[painel-bing]` `MEDIDO` — ordem de
grandeza distinta, e confundir as duas seria somar camadas.

**O teto do Copilot é cobertura de índice, e a taxa vem com a janela ou não vale.**
`MEDIDO POR MIM` em `data/ops/bing_webmaster_daily.jsonl`, `tipo=rastreio_diario`,
33 linhas:

| Data | InIndex | CrawledPages | Δ |
|---|---|---|---|
| 09-02 | 2.939 | 480 | — |
| 09-05 | 4.022 | 463 | +554 |
| 09-06 | 4.022 | 467 | **+0** |
| 09-08 | 4.667 | **80** | +349 |
| 09-09 | 5.049 | **79** | +382 |
| 09-12 | 6.300 | 446 | +428 |
| 09-13 | **7.158** | 468 | **+858** |

09-02→09-13 são **11 dias**: 4.219/11 = **383,5/dia** `DERIVADO`. A média dos
últimos 7 deltas é 448,0 e está **inflada pelo outlier de 09-13** (+858, ~2× os
vizinhos 428 e 420); a **mediana** dos mesmos 7 é **403** `DERIVADO`. Faltam 3.948
de 11.106 → fechamento entre **09-23 e 09-24**, não 09-22. Há **dois deltas zero**
(08-29, 09-06) e **08-21 ausente da série**.

**Nenhuma alavanca nossa acelera isso, e está medido:**
`tools/check-descoberta-do-bing:18-26` registra 2.679 URLs por IndexNow rendendo
**45 requisições** no dia, 1.313 (49%) nunca pedidas 24 dias depois, e conclui:
"nenhum canal nosso está quebrado; o gargalo é o ritmo com que o Bing absorve um
domínio novo". **E o que sobe é backlog, não rastreio fresco:** 09-08/09-09 com
`CrawledPages` **80 e 79** e InIndex +349/+382.

**O teto do Bing qualifica SÓ o numerador Copilot.** OAI-SearchBot e PerplexityBot
têm índice próprio; ChatGPT-User e Applebot buscam ao vivo. Declará-lo sobre o
numerador inteiro seria apresentar número de uma camada como teto de todas.

### A.1.3 O identificador de versão está errado em 100,0% das rotas que o têm

`MEDIDO POR MIM` `[disco]`, cruzando `anchor_claim_publication.jsonl` ×
`published_manifest.jsonl`:

```
anchor_claim com content_sha256 : 10.070
published_manifest              : 11.106
rotas comuns                    : 10.070   →  DIVERGEM 10.070 (100,0%)
manifesto SEM versão anunciada  :  1.036
exemplo /administrativo/acao-improbidade-servidor-exigencia-dolo/
        anchor 287b1206c45021ff…   manifesto 4819d13a600b1711…
stat anchor_claim_publication.jsonl → 2026-08-26 14:16:49 (20 dias congelado)
```

`internal/content/content.go:175-190` define `ContentSHA256` como "o `html_sha256`
que o `published_manifest` já grava por rota" e promete que "baixar a página e
recalcular o sha256 do HTML tem de dar o mesmo número";
`internal/pagemarkdown/frontmatter.go:173-179` o emite como `version:`. **A promessa
é falsa em 100,0%** porque o valor vem de `internal/content/anchorclaim.go:213-214`
(`pages[i].ContentSHA256 = sha`), lendo o ledger congelado. O comentário do próprio
código já escreve a régua: "um identificador que não bate com o artefato publicado
é pior que identificador nenhum".

### A.1.4 O MCP não é canal de produto — a medição que reordena o plano

`MEDIDO POR MIM` `[origem]` sobre `data/ops/access/access-2026-09-*.jsonl`, campo
`mcp_method`/`mcp_tool` (nasce no commit `2a2b866e`, Sep 8 15:17:11; 09-01..09-07
têm zero — janela real **09-08 a 09-16, 9 dias**): **13.109 req MCP**, sendo
`tools/list` 4.167 · `initialize` 3.796 · `notifications/initialized` 3.108 ·
`server/discover` 499 · `ping` 435 · **`tools/call` 301** · `resources/list` 119 ·
`prompts/list` 112 · `resources/templates/list` 33.

**E a atribuição é o achado:**

| | tools/call | ferramentas |
|---|---|---|
| **INTERNO** (`wikijuridica-superficie-probe`, `wikijuridica-agent-surface-probe`, `WikijuridicaBot`) | **245 (81,4%)** | mudancas_desde 90 · buscar_paginas 37 · **impacto 29 · contexto_juridico 27 · grafo 24 · ler_pagina 21 · buscar_semantico 8** |
| **EXTERNO** | **56** | buscar_duvidas 15 · buscar_paginas 14 · duvidas_do_tema 11 · mudancas_desde 5 · search 2 · fetch 1 = **48 reais** (+8 sondas de auth e nome inexistente) |

> **Externamente, `grafo`, `impacto`, `contexto_juridico`, `buscar_semantico` e
> `ler_pagina` receberam ZERO chamadas em 9 dias.** As 109 chamadas desses cinco
> são **100% sonda nossa**: o portal estava medindo o próprio eco.

Os UAs externos são **todos** censos de diretório MCP: `SaSame-MCP-Audit/0.1`
**28 de 56 (50%)** · `Go-http-client/2.0` 7 · `rokmcp-collector` 7 ·
`cracked-ai-probe` 5 · `mcp/1.0.0` 4 · `maghs` 2 · `Vouch-Census` 1 ·
`supermarket-probe` 1 · `dollardollardollar-signals` 1. **Nenhum assistente de
consumidor.** `resources/list` = 119 sobre 3.796 handshakes = **3,1%** — higiene de
descoberta, **não demanda**.

**DEFEITO ACHADO AQUI, e é nosso:** 22 dos 245 tool-calls internos saem com
`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; …)` — a identidade **de saída**
aplicada contra a **nossa própria** superfície. Sonda do próprio portal tem de usar
`wikijuridicabot.AplicaSondaInterna`, que escreve também `X-Warming-Request`; sem
ele a sonda **entra na métrica**. É o "portal mede o próprio eco" em carne e osso,
e entra como correção (passo A-L0b).

**Consequência que reordena tudo:** os três ativos exclusivos do portal (risco de
4.986 páginas, grafo de 393.081 arestas, 11.118 vetores) estão atrás de ferramentas
que **nenhum agente externo chamou**. A correção não é melhorar o MCP: é **tirar os
ativos de dentro dele**.

### A.1.5 Ativos pagos, no disco, invisíveis em toda superfície

**(a) 2.361 páginas NO AR que o nosso próprio validador reprova por fonte.**
`MEDIDO POR MIM` `[disco]`: `v2_rewrite_queue.jsonl` tem 3.201 linhas, **um único
`run_id`** (`v2-ingest-20260911T050000Z-…`) e `validation_as_of` **2026-09-11** em
todas — retrato único, não acúmulo. **2.461** com `official_sources_insufficient`;
cruzando `intent_id` com os 11.106 `unique_intent_id` do manifesto: **2.361 JÁ
PUBLICADOS = 21,3% do acervo** (só 100 nunca publicados). Exemplos:
`/jurisprudencia/stj-tema-304/`, `/empresarial/compensacao-divida-entre-empresas-como-fazer/`.
Demais motivos medidos: `heading_reuse_above_global_limit` 3.957 ·
`portfolio_lane_invalid` 1.335 · `duplicate_phrase_with_page` 1.259 ·
`h1_equals_title` 1.027 · `missing_required_field` 500 ·
`official_source_host_not_allowed` 384.

A ordem é **vinculante**: `docs/PRECEDENTES_DAS_ORDENS.md:134-152` (2026-08-06) —
*"Médio publica: fonte insuficiente… **Publicar não encerra o defeito. O que entrou
como médio vira fila de refinamento com causa nomeada**."* A fila existe, tem nome,
ninguém a drena — e o insumo está no mesmo disco: **60.221 acórdãos** com
`fonte_url` + `sha256_conteudo`. Para um grounder, "fonte oficial insuficiente"
pesa mais do que qualquer campo `version:`.

**(b) Risco de superação — 4.986 medidas, servidas a ninguém.** `MEDIDO POR MIM`
`[disco]` em `data/ai/risco_superacao.jsonl`: **4.986 de 11.106 (44,9%)** com
medição, **6.120 (55,1%) SEM**; risco > 0 = **3.481**; ≥ 0,8 = 1.250; **= 1,0 =
1.190**; p25 0,0 · p50 0,08 · p75 0,84.
*(Divergência declarada: o crítico reportou `risco > 0` = 2.711; minha medição
direta sobre o campo `risco` das 4.986 linhas dá **3.481**. Uso a minha e declaro
a diferença.)*
Aparece só em `internal/httpserver/mcp_risco.go:19` e como campo de
`contexto_juridico` (`mcp_contexto.go:300`) — **ambas com zero chamadas externas**.
`grep -c -i superac` no `llms-full.txt` servido = **0**. Prova no byte:
`/tributario/execfiscal-penhora-salario-aposentadoria/` tem risco **1,0** com **11
acórdãos posteriores à revisão**, e a gêmea servida (10.692 B) anuncia
`reviewed_at: "2026-08-26"` com `grep -ci "superac|risco"` = **0**.
`MAESTRO_CODEX_LOG.md:6380-6381` registra o motivo do adiamento — *"passa pela
cadeia de publicação e pela matriz `--ressemear`"* — que **não alcança** gêmea,
`/api/v1/citar` e Atom, que são rota dinâmica.

**(c) O grafo.** `MEDIDO POR MIM` `[disco]`:
`cita` 151.424 · `cocitada_com` **139.521 (35,5%)** · `julgado_por` 62.966 ·
`aplica` 22.789 · `da_area` 11.104 · `pertence_a` 5.275 · `revoga` **2** ·
`supera`/`altera`/`impactada_por` **0**. Nós: acordao 60.221 · pagina 11.104 ·
dispositivo 5.275 · tema 2.347 · sumula 398 · norma 327 · area 32 · tribunal 2.
Total **393.081**. Fonte das arestas `cita`: **`extracoes_dispositivos.jsonl`
102.771** (67,9% de `cita`; **26,1% do grafo**) · `legal_cocitation_index.jsonl`
8.516 · registros do corpus o resto.
*(Divergência declarada: o dossiê trazia 104.002 = 26,5%; minha leitura de hoje dá
**102.771 = 26,1%**, e o arquivo está `M` no working tree — a série andou.)*
`cocitada_com` alimenta **um** consumidor (Percursos, 5.815 de 11.104). **Ninguém
propôs o segundo uso:** dispositivo com alta co-citação e poucas páginas é
**detecção de lacuna** — pauta derivada sem uma chamada de modelo.

**(d) 11.118 vetores** (`embeddings/ativo.json`, `qwen3-embedding:0.6b`, dim 1024,
2026-09-15T15:29Z) `[disco]` `MEDIDO`. **Não são 11.248** — esse é o total de
tarefas `embed_pagina` concluídas, outra coisa.

**(e) 410 consultas reais, e a forma refuta o rótulo "proxy".** `[painel-bing]`
`MEDIDO`: **411 pares distintos, 410 consultas distintas, 43 páginas** (08-21 a
09-11). Forma: **p50 8 tokens**, média 8,9, máx 36; **117 de 229 (51,1%) com ≥ 8
tokens**; várias com `#R##N#` literal = codificação de CRLF do Bing, **prova de
texto colado**. O dado **não distingue** Copilot de humano colando, e não afirmo o
que não medi; mas p50 de 8 tokens com cauda até 36 não é consulta de teclado.
Consumidores no repo: `generate-painel` e `experimentos.py` — **exibem**. Nenhum
gerador editorial.

### A.1.6 Volume: corpus monotemático e custeio publicado errado

`MEDIDO POR MIM` `[disco]` em `stj-espelhos/cursor.json` — **4 de 10 datasets**
(`internal/stjacordaos/fonte.go:23-32` lista 10), **60.221 registros**:

| dataset | meses | janela | registros |
|---|---|---|---|
| terceira-turma | 52 | 20220531..20260831 | 30.786 |
| quarta-turma | 52 | 20220531..20260831 | 27.845 |
| **segunda-secao** | **21 de 52** | 20220531..**20240131** | 728 |
| primeira-turma | **3 de 52** | 20220531..20220731 | 862 |

Ausentes por inteiro: corte-especial, primeira-secao, terceira-secao,
segunda-turma, quinta-turma, sexta-turma. **97,4% em 3ª + 4ª Turma.**

**O "arquivo de 599 bytes com um `}` sobrando" está DESFEITO, e eu localizei o
599:** `MEDIDO POR MIM` — é `registros: 599` no mês `20220531` do dataset
`quarta-turma`. Não é tamanho de arquivo nem JSON malformado; o defeito é
**dataset abortado**. Fica escrito para ninguém re-diagnosticar.

**A 2ª Seção é o buraco que ninguém viu, e é o pior:** a Seção é o órgão que
**uniformiza a divergência entre 3ª e 4ª Turma** — exatamente o produto da Seção B.
`[fonte]` `MEDIDO`: GET a
`dadosabertos.web.stj.jus.br/dataset/espelhos-de-acordaos-segunda-secao` com a
identidade do projeto (200, 117.816 B) anuncia **52 recursos `YYYYMMDD.json`,
20220531..20260831**. **Os 31 meses existem e nunca foram colhidos.**

**O custeio de "~361 req ≈ 1 h" está refutado pelo próprio coletor:**
`cmd/collect-stj-acordaos/main.go:62` tem `-max-recursos` default **100** e a doc
diz "com Crawl-Delay 10 cada arquivo custa ~10 s e o comando pesado tem teto de
**1.800 s**". 361 req = 3.610 s = **2× o teto e 3,6× o cap**. **Custeio correto:
80 recursos MEDIDOS** (2ª Seção 31 + 1ª Turma 49) **+ 6 × N, com N `A MEDIR`; se
N = 52, total 392** ⇒ **≥ 3 passadas** de ≤ 170 sob `run-heavy-throttled`,
retomando por cursor.

**Os ZIPs:** `internal/stjacordaos/dataset.go:32-34` declara que ignora `.zip` e
`.csv` "que são empacotamentos do mesmo conteúdo". É decisão escrita, mas
comentário é alegação (R1). **`A MEDIR`**, e o motivo é explícito: exigiria saída
ao STJ sob Crawl-Delay numa sessão somente-leitura.

**Os geradores parados:** `tools/run-daily-content:369-373` tem **cinco** geradores
no mapa `GERADORES` (`stj-tema` 200 · `stj-sumula` 80 · `stf-informativo` 60 ·
`noticias` 40 · `diarios` 30) `MEDIDO`. **`generate-lei-artigo-pages` e
`generate-acordao-pages` não estão lá** — só num comentário em `:446-447`. Ambos
têm `-limite` default **30**; o runner embrulha cada gerador em `timeout 900`
(`:471`); e o sinal de sucesso é documentado como mentiroso por ele mesmo
(`:490-494`): *"`paginas_geradas` conta o SHARD REMONTADO… em 2026-09-09 imprimiu
415 com ZERO páginas novas, e a fábrica ficou 5 dias parada sem um único vermelho."*

**Dependência dura, lida no código:** `cmd/generate-lei-artigo-pages/main.go:249-253`
recusa candidato sem acórdão do corpus citando a URN (`corpus_sem_acordao_para_a_urn`).
Com 97,4% em direito privado, execução fiscal, IPTU, previdenciário e criminal
**não se atendem subindo limite nenhum**.

**Os 49.807 agravos:** a recusa **está certa** — `cmd/generate-acordao-pages/main.go:16`
escreve *"Página própria para cada um seria doorway"*. Não é rótulo cego. Mas
**2.902 passam todo o resto de elegível e 17.616 têm ementa de 250+ palavras**: é
a população de L7, e hoje é rejeito integral.

### A.1.7 DataJud: duas dimensões fechadas, e a "divergência" reconciliada

`MEDIDO POR MIM` `[disco]` sobre os 22 arquivos de `data/research/datajud/`:

```
campo `processos`   : 283.415.422   ← CASOS
dimensão `assuntos` : 345.682.422   ← pares (processo × assunto), 1.022 assuntos
dimensão `graus`    : 277.830.034   ← G1 161.909.008 · JE 63.125.140 · G2 32.080.813
                                      TR 12.067.590 · SUP 8.578.854 · TRU 68.629
dimensão `classes`  : 312 distintas ← Execução Fiscal 49.428.009 · Juizado Cível 37.702.472
```

**Não há divergência a explicar: são denominadores diferentes.** O crítico leu
283,4 M (casos) e o enunciado 345,7 M (pares assunto); **os dois estão certos**.
Registro aqui para que ninguém "corrija" um pelo outro.

**E o `graus` reposiciona o eixo de volume:** **161,9 M em G1 e 63,1 M em juizado
contra 8,6 M em superior (3,0%)** — e V1/V2/V3 perseguem acórdão de superior. Não
invalida o eixo (é o que tem texto oficial hasheável no nosso disco);
**reposiciona a promessa: é cobertura de TESE, não de volume de litígio.**

**O cruzamento está quebrado no CRITÉRIO:** `tools/generate-datajud-corpus:152-183`
faz `return [caminho for caminho, vocab in paginas if distintivos & vocab]` — **OR
de um token**: 4,46 assuntos/página, 97,8% "cobertos", "fiscal" casando bagagem
aérea com execução fiscal. Visível no artefato: em `ranking_nacional.json`,
*"Dívida Ativa (Execução Fiscal)"* exemplifica com
`/aereo/bagagem-indenizacao-sem-nota-fiscal/`. **Enquanto for esse critério,
qualquer "N assuntos / M processos cobertos" é número inválido.**

### A.1.8 Desenho correto — NÃO se mexe

`rel="cite-as"` ausente no HTML é deliberado (`markdown.go:359-363`: a URL já **é**
a canônica) · gêmea fora do sitemap é decisão de SEO por chave de cache
(`test_generate_indexnow_gemea_markdown.py:17-19`), e os três canais de descoberta
**já estão ligados** (`rel="alternate"`, `Link:` do nginx, 2.295 `index.md` no
`indexnow_url_state.jsonl`) com adesão de 0,038% — **a alavanca "descobrir a gêmea"
está FECHADA por medição** · CSS inline das páginas de erro é de propósito.

**Teto de 50 KB** `MEDIDO POR MIM` `[disco]`: `os.walk` sobre **11.357**
`index.html` → máx **38.466 B**, p99 30.040, p95 27.707, p50 23.162, **zero acima
de 45 KB**; margem no pior caso = **12.734 B**. É esse número que orça os blocos
novos de L1/A13.

---

## A.2 As alavancas, ordenadas por retorno medido ou derivado

> **Critério:** alcance medido na camada onde o agente lê × custo × risco de
> regressão. **Rota dinâmica vem antes de rota estática** sempre que entregar o
> mesmo conteúdo: não toca `public/`, não paga `--ressemear`, não re-anuncia o
> sitemap.

| # | Alavanca | Alcance | Selo | Custo |
|---|---|---|---|---|
| **L0** | **Coletor de borda** (§A.3.1) | toda a série | MEDIDO: retenção **8 dias** | ferramenta + unit |
| **L0b** | **Sonda interna para de se medir** (A.1.4) | 22 tool-calls/9 d | MEDIDO | `AplicaSondaInterna` |
| **L1** | **Risco de superação na gêmea + `/api/v1/citar` + Atom** | 1.967 + 540 req/dia | MEDIDO (A.1.5b) | rota dinâmica, **zero `--ressemear`** |
| **L2** | **C1 — trocar a fonte de `ContentSHA256`** | 10.070 + 1.036 | MEDIDO (A.1.3) | pacote-folha |
| **L3** | **Drenar a fila de fonte insuficiente** | **2.361 (21,3%)** | MEDIDO (A.1.5a) | gerador datado |
| **L4** | **Pauta por consulta medida × vetor** | 410 consultas | MEDIDO (A.1.5e) | 2 artefatos no disco |
| **L5** | **V1 — completar o corpus** | pré-requisito de L6/L7 | MEDIDO (A.1.6) | ≥ 3 passadas |
| **L6** | **V2/V3 — os 2 geradores no mapa** | páginas na esteira | DERIVADO | 2 linhas + envs |
| **L7** | **V4 — agregado de admissibilidade** | 2.902 elegíveis / 17.616 com ementa ≥250 | MEDIDO | gerador novo |
| **L8** | **C3 — título citável único** | 4 canais, 87,5% divergem | MEDIDO | 1 linha + oráculo |
| **L9** | **C4 — URN corrompida** | 356 URNs | MEDIDO | 1 linha + emenda |
| **L10** | **Derivar `agentesValiososParaRanking`** | decide que salas encher | MEDIDO | 1 função |
| **L11** | **Lacuna por `cocitada_com`** | 139.521 arestas, 1 consumidor | DERIVADO | gerador novo |
| ~~L12~~ | ~~MCP `resources`~~ | **0 externas** | **REBAIXADA** (A.2.9) | — |
| ~~L13~~ | ~~`version` no JSON-LD do HTML~~ | — | **REFUTADA** (A.2.10) | — |

### A.2.1 L0 — o coletor de borda vem primeiro por causa FÍSICA

Retenção da Cloudflare = **8 dias**. Em **2026-09-17** a colheita desta sessão fica
irreproduzível. Não é preferência de ordem: é a única alavanca com prazo externo.

### A.2.2 L1 — o risco muda de canal, em dois tempos

**Tempo 1 (barato, sem `--ressemear`):** bloco na gêmea + campo em `/api/v1/citar`
+ item no Atom. São **rotas dinâmicas**: não geram artefato em `public/`, não
entram na matriz do §6, não re-datam nada. O único motivo registrado do adiamento
**não alcança** esses três canais. Alcance: 1.967 + 540 req/dia `[origem]`.

**Tempo 2 (o que alcança quem responde):** o Tempo 1 alcança 26 de 3.352. Para
chegar ao HTML **sem re-datar o acervo a cada acórdão novo**, o bloco **entra na
tupla de neutralização** de `tools/generate-page-content-revision`. Li a tupla: ela
casa `<script>` **sem atributo** e `<nav class="perfis-oficiais">`, e o comentário
avisa literalmente: *"TROCAR ESTA TUPLA MUDA A FORMULA DO served_sha256: rodar com
`--ressemear` na mesma passada, senão a troca de fórmula é lida como conteúdo
novo."* Logo custa **uma** passada e depois **nunca mais re-data**.

**`A MEDIR` e nomeado:** distribuição do risco por área, e o fechamento da medição
para as **6.120 páginas sem risco medido (55,1%)**. Publicar o risco de 44,9% do
acervo sem declarar cobertura seria apresentar amostra como população — o bloco sai
com `cobertura_do_instrumento: "4.986 de 11.106"` **no próprio dado**.

### A.2.3 L2 — C1, e a trava de import que "1 fonte de dado" ignora

**Não é troca de fonte: é ciclo de import.** `internal/publishedmanifest/publishedmanifest.go:24`
importa `portaljuridico/internal/content`; logo `internal/content/anchorclaim.go`
**não pode** importar `publishedmanifest`. Hoje `content` importa só `contentstore`
e `jsoncodec` (`content.go:12-13`, `anchorclaim.go:10`).

**DECISÃO: pacote-folha mínimo (`path → html_sha256`) importado pelos dois.**
Descarto a injeção do mapa no call site: ela resolveria este caso e deixaria o
próximo leitor sem fronteira escrita. **Nunca** um segundo parser do manifesto
dentro de `content`.

**E o gate NÃO se cria do zero.** `tools/check-served-vs-manifest` já baixa os
**bytes servidos**, compara com `published_manifest.html_sha256`, separa
`ok`/`render_de_servico`/`disco_incoerente`/`http`, sonda com UA interno +
`X-Warming-Request` e **já roda** na lista de gates (`run-daily-content:844`).
**Acrescentar a coluna "versão anunciada pela gêmea" a ESSE instrumento** — um
assunto, um detector. `tools/check-versao-confere-com-artefato` duplicaria o mesmo
sha, a mesma busca e o mesmo HTTP, e nasceria sem teste de FP (o "caso das 46").

**A lacuna que o gate existe para achar, dita antes:** provei que o manifesto bate
com os bytes numa página, hoje. Se a transação escrever o manifesto **antes** de o
`public/` assentar, a fonte nova teria a mesma classe de defeito em ponto diferente.
O gate é **parte do passo**, não um extra.

### A.2.4 L3 — drenar a fila de fonte é a ordem de 2026-08-06 executada

2.361 páginas × 60.221 acórdãos com `fonte_url` + `sha256_conteudo`. Produtor de
fonte por **gerador datado** (lease + CAS + escrita atômica), preservando o anterior
em `.agents/runtime/` com data. **Nenhuma página é reescrita no texto** — só a
proveniência ganha a fonte que falta, que é o motivo gravado na fila. A cobertura
do corpus é 97,4% direito privado, então a drenagem **não é uniforme**, e o número
sai **por área**, nunca como total.

### A.2.5 L4 — pauta por consulta × vetor, de graça

Encostar os **11.118 vetores** nas **410 consultas distintas** entrega, sem coletar
nada: (a) a página que responde cada consulta real; (b) **a consulta que nenhuma
página responde** — pauta com demanda provada. É o mesmo instrumento que conserta o
cruzamento DataJud (§A.4).

### A.2.6 L5/L6/L7 — eixo de volume, custeio corrigido

- **L5:** 80 recursos medidos + 6 × N (`A MEDIR`) ⇒ **≥ 3 passadas** de ≤ 170 sob
  `run-heavy-throttled`, com a contagem por passada declarada. **Prioridade
  interna: 2ª Seção primeiro** (é o órgão da divergência), depois 1ª Turma, depois
  os 6 ausentes.
- **L6:** duas linhas no mapa `GERADORES` + `WIKI_LIMITE_LEI_ARTIGO` /
  `WIKI_LIMITE_ACORDAO`. **Antes**, `--seco -limite <alto EXPLÍCITO>` — com o
  default 30, `--seco` mediria o **próprio teto**, não o estoque.
  `internal/tetodelote:359-361` garante que publicada não consome cota. **O sucesso
  se afere por diferença de conjunto de `unique_intent_id`**
  (`tools/check-onda-avanca`), **nunca** por `paginas_geradas`. E `WIKI_LIMITE_*` se
  calibra para caber nos 900 s do `timeout`, ou o backfill roda fora do runner.
  Pré-requisito: `tier_a_artigos.jsonl` é de 2026-09-10 05:25.
- **L7:** os 49.807 agravos viram **um** agregado por súmula processual, usando a
  lista canônica que já existe (`main.go:328-333`: STJ 7, 83, 182, 211, 568; STF
  279, 282-284). Derivável sem modelo, **e não é doorway** justamente porque é uma
  página por súmula, não por acórdão. População: 2.902 elegíveis, 17.616 com ementa
  ≥ 250 palavras.

### A.2.7 L8/L9 — as duas correções de 1 linha, com a emenda

- **L8:** `internal/pagemarkdown/render.go:285` faz
  `primeiroNaoVazio(page.Heading, page.Title)`. Três superfícies usam `page.Title`,
  uma usa `page.Heading`. **Vence `page.Title`** — é a string que o índice guarda.
  Oráculo: `apiCitacao.Title` (`internal/httpserver/api_citar.go:150`), comparado
  sobre amostra do acervo **sem reimplementar a regra**.
- **L9:** `render.go:485` passa a URN por `escapaTexto` **dentro de code span**, e
  `blocks.go:100-113` escapa `_` como `\_`, que o CommonMark não processa entre
  backticks — provado no byte de `/autonomos/cobranca-prescricao/index.md` com
  `cat -A`. **Emenda obrigatória:** remover a chamada inteira abre buraco novo,
  porque `escapaTexto` também escapa a **crase**, e uma URN com crase encerraria o
  span. **DECISÃO: não escapar dentro do span e ALARGAR A CERCA** conforme a maior
  sequência de crases do valor — regra do próprio CommonMark, e nunca descarta dado
  real. (Descarto "normalizar/recusar URN com crase": recusar dado válido para
  simplificar o render é perder informação.) Teste por mutação **imprimindo os spans
  ANTES da asserção**.

### A.2.8 L10/L11 — os dois mapas que decidem pauta

**L10:** `cmd/cerebro/comentarios.go:42-50` declara medir "leitura por IA que CITA"
e lista, `MEDIDO`: `perplexitybot`, `oai-searchbot`, `chatgpt-user`, `bingbot`,
`amazonbot`, `googlebot`, `claudebot` — **admite dois crawlers de treino**
(amazonbot, claudebot, que `botagents.funcao_de` classifica como `training`) e
**exclui** `applebot` (`search`, 519 req/24 h, porta de Siri/Spotlight),
`claude-user` e **`gptbot`**. E gptbot é **28.036 de 83.810 acessos (33,4%)** em
`/redesocial/tema/`: **um terço do sinal é invisível para o ranking que decide o
que promover.** Correção: derivar de `tools/botagents.py`, a taxonomia canônica.

**L11:** `cocitada_com` = 139.521 arestas e um consumidor. Dispositivo com alta
co-citação e poucas páginas é **lacuna de acervo medida**, e vira pauta sem modelo.

### A.2.9 L12 — MCP `resources` fica REBAIXADA, e o número é meu

Não é "não fazer": é **não fazer antes**, por medição (A.1.4): 48 chamadas externas
reais em 9 dias, **todas de censo de diretório**, zero de assistente de consumidor;
`resources/list` = 3,1% dos handshakes. `resources` entra como **higiene de
protocolo** — barato, correto, sem retorno esperado em citação — junto com o **gate
de igualdade dos três inventários** (15 tools / 14 skills / 4 A2A), que é a lacuna
real: `agentsurface` é fonte única das **rotas** e nada cobra as **capacidades**.

**Corolário para a Seção B:** construir um **quinto** canal MCP, de escrita, antes
de o quarto ser usado por quem não seja um censo, é gastar onde a medição diz que
não há consumidor.

### A.2.10 L13 — `version` no JSON-LD do HTML: REFUTADA, com emenda

**Impossível por construção, e falharia MASCARANDO.**
`internal/publicrelease/publicrelease.go:812-817` faz
`htmlHash := bytesSHA256(releaseHTMLForPage(page))` — o hash é dos bytes que
passariam a **conter** o valor anunciado. Satisfazer isso exige `h = SHA256(f(h))`:
busca de pré-imagem. `reusableHTMLArtifactHash` (`:968-979`) não amortece — descarta
o hash reusado justamente quando o render fresco difere, e ele difere porque
`ContentSHA256` mudou. Pior: um gate escopado a "gêmea × bytes" compararia
`h_N == h_N` e ficaria **VERDE** enquanto o JSON-LD dentro desses mesmos bytes
diria `h_{N-1}`.

**Segundo defeito, permanente:** o neutralizador casa `<script>` **sem atributo**;
o JSON-LD tem atributo, e o comentário do próprio arquivo diz que ele é *"conteúdo
jurídico, cuja mudança DEVE redatar a página"*. Com o hash da geração anterior
dentro dele, **todo** deploy re-dataria as 11.106 páginas, para sempre.

**Emenda adotada:** `html_sha256` só vive onde **não entra no próprio hash** —
gêmea, CSL-JSON, `/api/v1/citar`, cabeçalho HTTP. Se o HTML precisar de identidade,
emite-se `identifier` = `unique_intent_id`, **estável entre deploys**.

### A.2.11 A janela de `--ressemear` é UMA — e é a regra que dissolve o conflito

`--ressemear` é flag **da passada**, não da página.

**DECISÃO ÚNICA: todo bloco DERIVADO de corpus entra na tupla de neutralização e
sai na MESMA passada `--ressemear`, com L8 e L9 junto.** Isso vale para o bloco de
risco (L1-Tempo-2) **e** para o dossiê de divergência (Seção B, passo A13) — são a
mesma classe: derivados do corpus, mudam a cada acórdão novo. Tratar um como
neutralizado e o outro como texto editorial re-dataria 11.106 páginas a cada
atualização de corpus — o **frescor fabricado** que o arquivo do neutralizador
existe para combater, e a mesma objeção que derruba L13 em forma de `<section>`.

**Trade aceito e escrito:** blocos derivados **não** avançam `content_revised_at`;
a atualização de corpus se anuncia por **Atom, gêmea e rede social**, que são os
canais de quem varre.

**Orçamento de bytes, DERIVADO da margem medida:** margem de **12.734 B** no pior
caso de 11.357 arquivos (A.1.8). Os dois blocos juntos ficam em **≤ 4.096 B**
(2.048 cada), que é **32,2% da margem**, preservando 8.638 B. O gate de 50 KB já
existente cobra.

Nessa passada `--desde-commit` fica **proibido**. Antes: conferir
`tools/check-csp-style-hashes` (roda na suíte, **não** no caminho do deploy). Ler o
MOTIVO impresso: se disser `purgando tudo`, **não purgar de novo**; e antes de
purgar à mão, rodar o comando do passo e ler o exit real — "registro de revisao
indisponivel" já foi mentira. Depois: `tools/check-efeito-nos-bots`, com o
**veredito pré-registrado antes do número**.

---

## A.3 A rotina de medição que fecha o ciclo

Três camadas, três instrumentos, um gate. **Nenhum instrumento é nomeado pelo que
não mede.**

### A.3.1 `tools/generate-edge-leitura-de-agente-daily` — BORDA = VOLUME

- **Mede:** por dia e por `agent_key`, classes `html_acervo` · `gemea_md` ·
  `redesocial` · `feed_atom` · `api_v1` · `mcp` · `a2a` · `well_known` · `sitemap`
  · `assets` · `sem_barra_final`, com `status`, `cacheStatus`,
  `verifiedBotCategory` e **`papel`** (responde/varre/treina).
- **Reusa:** `tools/cloudflare_auth.py` (fonte única de credencial),
  `tools/botagents.py`, `tools/edgetelemetry.py`. **Migra as consultas de
  `/tmp/borda_*.py`** para dentro do repo — produto não mora em `/tmp`.
- **Grava:** `data/ops/edge_agent_reading_daily.jsonl`, schema
  `edge_agent_reading_v1`, append-only, `camada:"borda"` **na linha**. 1 dia/chamada.
- **Exit:** `0` gravado · `1` erro de coleta · `2` série insuficiente · `3` janela
  fora da retenção. **Sem `OnFailure`** enquanto 3 for caminho normal.
- **Três armadilhas como CÓDIGO, não como aviso:** contagem por `_like`/`_notlike`
  **exata** (a dimensão crua truncou em 4 dos 8 dias); `userAgent` **íntegro**
  (truncar em 120 chars perdeu OAI-SearchBot inteiro, 12.118 req); separação
  interno/externo (**73,0% da borda é aquecimento nosso**).
- **Controle positivo OBRIGATÓRIO:** soma das classes + `outro` fecha com o total
  obtido **sem** dimensão. Sem isso, um `_like` errado vira série falsa sem erro.
- **Urgência física: 2026-09-17.**

### A.3.2 Bloco `ia` em `tools/collect-bing-webmaster` — PAINEL = CITAÇÃO

- **Reusa:** entrada nova no dict `BLOCOS` (`:111-116`) com o `Ritmo` existente
  (10 req/62 s), ledger append-only e cursor. Sonda ≤ 2 req/dia.
- **Exit:** a execução padrão termina em **0** gravando `api_disponivel: false` —
  obrigatório, porque `wikijuridica-bing-submit.service` **tem**
  `OnFailure=wikijuridica-alerta@…` (`MEDIDO` por `systemctl show -p OnFailure`) e
  exit 3 diário viraria **alarme falso ao dono**. Exit `3` só sob `--so ia`. **O
  gate lê `api_disponivel` do ledger, nunca o exit code.**
- **Grava:** `tipo:"ia_painel_leitura_manual"` (linha de base dos ~23.000, com
  `camada`, `metodo:"leitura-do-painel"`, `api_disponivel:false`,
  `precisao:"ordem-de-grandeza-lida-no-painel"`, data) e `tipo:"ia_api"` quando o
  método aparecer — **mesmo encaixe, sem redesenho**.
- **`InIndex` sai sempre ao lado, com a janela da taxa declarada.**

### A.3.3 `tools/measure-ai-citation` — ORIGEM = SÓ O QUE É DELA

Existe, timer ativo, já declara `is_citation_count:false` e
`interpretation:"considered_for_answer"`. É o **único** canal que alcança o clique
de volta — a borda no plano Free nega `clientRequestReferer`. As quatro camadas
(treinamento 54.450 · crawl 37.762 · fetch 2.638 · clique_de_volta 81, 36 dias) são
**todas declaradas piso** e **não se somam**.

### A.3.4 `tools/check-leitura-de-agente-nao-regride` — o gate

| Condição | Exit |
|---|---|
| classe `responde`: mediana de 3 d de `html_acervo` cai além do limiar contra a de 14 d **e** sem publicação na janela | 1 |
| rota 404 pedida por AI Crawler **verificado** ≥ 3 dias seguidos e ausente da fila | 1 |
| descritor de `internal/agentsurface` com 404 na borda | 1 |
| `csp-report` **sob nosso controle** acima de zero (ver ressalva) | 1 |
| `InIndex` cai contra o **dia anterior existente** | 1 |
| dispersão da variação dia-a-dia acima do limiar pré-registrado, **ou** `api_disponivel:false`, **ou** dia anterior ausente | 2 |

**Constantes rotuladas:** `≥ 3 dias` é **DERIVADO** (1.114 dos 1.118 404 se
resolveram em 48 h ⇒ 3 d > lag medido). **O portão de saída do exit 2 é DISPERSÃO
MEDIDA, não contagem de dias** — pode fechar em 6 ou em 20; catorze dias seria
espera de calendário, proibida. **Por fluxo e por agente, nunca limiar global:**
três regimes medidos (amazonbot ~0→3.446/dia; cf-ai-search cai 21×; gptbot 36.671
num dia). **Ciente de lacuna:** dia anterior ausente ⇒ **2**, nunca comparar por
cima do buraco (08-21 falta).

**Ressalva do `csp-report`, MEDIDA:** `var/social/csp_violacoes_agregadas.jsonl`
registra em 2026-09-15 **243 `script-src-elem` + 65 `script-src` = 308/dia**, com
`script-src 'none'` na CSP da rota (`ops/nginx/social-headers-publico.conf:45`) e
**zero conteúdo social publicado**. Em massa, `script-src-elem` sob `'none'` é
assinatura de extensão do visitante. O gate separa `blocked-uri` **sob nosso
controle** (alvo 0) de injeção do cliente (**linha de base de 308/dia, causa
nomeada**). Alvo zero contra 308 seria vermelho permanente a explicar depois.

**Duas travas confirmadas inexistentes** `[borda]`: `304` = 0 em todo agente de IA
(só bingbot 109, googlebot 8) e `429` = 0. **Publicação frequente não tem custo
medido em agente de IA** — o custo medido é o dos bots que revalidam, e é do lado
do `--ressemear` (§A.2.11).

### A.3.5 O que o painel NÃO pode fazer

Não somar camadas · não somar "AI Crawler" como audiência (quase toda Amazonbot =
treinamento) · não contar as 866.020 de aquecimento (73,0%) · não atribuir demanda
por UA sem `verifiedBotCategory` — **30,7% da borda não tem `agent_key`**, e
`verifiedBotCategory` vazio **não** significa falso (a Cloudflare não verifica
PerplexityBot). **Enquanto os 30,7% durarem, um terço da métrica por agente é
ficção, e a série diz isso na própria linha.**

---

## A.4 O laço das grounding queries como pauta, cruzado com o DataJud

Indisponíveis por API — mesmo motivo de A.3.2. O laço roda com **proxies nomeados
como proxies** e recebe o dado real no mesmo encaixe.

**1. Colher:** **(a)** `consulta_diaria` + `pagina_consulta`: **410 consultas
distintas, 411 pares, 43 páginas** `[painel-bing]` — rótulo **busca clássica**; o
rótulo "proxy" é fraco pela forma medida (p50 8 tokens, `#R##N#` = texto colado),
mas **não medi** o que separa Copilot de humano colando. **(b)** O caderno de 404
assinado por nós: **865 de 1.297 com Referer nosso** `[origem]` — **demanda real
com endereço**, não proxy. **(c)** A taxonomia que o agente presume
(`cpc-art-536`, `stf-20260908`).

**2. Cruzar — o conserto é do CRITÉRIO.** O OR-de-um-token sai; entra
`buscar_semantico` (11.118 vetores, dim 1024) com limiar calibrado sobre o par
consulta↔página que `consulta_pagina`/`pagina_consulta` já entregam — **conjunto
rotulado sem coletar nada**. Enquanto o critério for o antigo, **nenhum número de
cobertura DataJud entra em documento nosso**.

**3. Priorizar, com a ressalva causal escrita:** execução fiscal 20,16 M · IPTU
12,68 M · auxílio por incapacidade 6,59 M · tráfico 3,22 M caem em áreas com 12,7%
a 26,6% de cobertura de mérito e **não se atendem sem L5**. Hoje o laço gera onde o
corpus sustenta (CPC 50.076, CC 11.945). E o `graus` (161,9 M em G1 contra 8,6 M em
superior) reposiciona a promessa: cobertura de **tese**.

**4. Medir o efeito, com o limite dito antes:** coorte por **stride determinístico
`sha256(path)`** — o mesmo do bloco `urlinfo` (200 URLs/dia, acervo em ~51 dias).
**Se o A/B for inviável** (o deploy é de acervo inteiro), o teste é antes/depois na
mesma coorte e a **atribuição fica declarada NÃO MEDIDA**, nunca afirmada. É o
limite honesto e não se resolve com mais análise.

---

## A.5 Provas de aceitação, com comando e número esperado

| # | Prova | Comando | Hoje (MEDIDO) | Esperado |
|---|---|---|---|---|
| **PA-1** | Série de borda existe | `wc -l data/ops/edge_agent_reading_daily.jsonl` | **arquivo não existe** | ≥ 1 linha/dia/`agent_key` |
| **PA-2** | Controle positivo da borda | soma das classes + `outro` × total sem dimensão | — | igualdade exata |
| **PA-3** | Versão confere com o artefato | `check-served-vs-manifest` + coluna nova | **10.070 de 10.070 divergem** | 0 divergências; 11.106 com versão |
| **PA-4** | Versão **não** entrou no HTML | `curl … \| grep -c sha256` | **0** | **0** (L13 refutada) |
| **PA-5** | Risco na gêmea | `curl …/index.md \| grep -ci superac` | **0** | ≥ 1, com `cobertura 4.986 de 11.106` |
| **PA-6** | Risco em `/api/v1/citar` | `jq 'has("risco_de_superacao")'` | `false` | `true` |
| **PA-7** | Sonda não se mede | tool-calls com UA de saída contra `/mcp` | **22 em 9 d** | **0**; todos com `X-Warming-Request` |
| **PA-8** | Fila de fonte drenada | intents `official_sources_insufficient` ∩ manifesto | **2.361 (21,3%)** | cai, declarado **por área** |
| **PA-9** | URN válida na gêmea | `cat -A \| grep -c '\\\\_'` | até **356** | **0** |
| **PA-10** | Título citável único | `<title>` × gêmea × CSL × `/api/v1/citar` | **35 de 40 (87,5%)** | 0 divergências |
| **PA-11** | Corpus completo | meses por dataset no `cursor.json` | **4 de 10**; 2ª Seção **21 de 52**; 1ª Turma **3 de 52** | 10 de 10; 2ª Seção 52 de 52 |
| **PA-12** | Geradores no runner | `grep` no mapa `GERADORES` | **0** dos 2 | 2 no mapa |
| **PA-13** | Estoque real, não o teto | `--seco -limite <alto explícito>` | **não medido** (default 30 mediria o teto) | número que **substitui** os 2.488/4.763 do dossiê |
| **PA-14** | Onda avançou | `tools/check-onda-avanca` | — | > 0 **novos**; `paginas_geradas` **não** é prova |
| **PA-15** | Ranking derivado | `agentesValiososParaRanking` × `botagents.funcao_de` | **7 à mão**; gptbot ausente (33,4%) | derivado, 0 divergências |
| **PA-16** | Inventários iguais | tools/list × agent-skills × agent-card | **15 / 14 / 4** | gate vermelho enquanto divergirem |
| **PA-17** | InIndex ciente de lacuna | gate lê `rastreio_diario` | 2 deltas zero, 1 dia ausente | queda ⇒ 1; dia ausente ⇒ 2 |
| **PA-18** | Passada de markup | `tools/check-efeito-nos-bots` + soma dos blocos ≤ 4.096 B | margem 12.734 B | taxa de 304 com **veredito pré-registrado** |

---
---

# SEÇÃO B — Rede social de IA: arquitetura para implementar

## B.1 A tese, em três frases

1. **O produto não é um fórum onde agentes conversam: é a única superfície onde a
   posição CONTRÁRIA a uma tese jurídica já está computada, atribuída a um órgão
   julgador nomeado e conferida contra um corpus hasheado** — nem LexML (resolve
   URN), nem CourtListener (inteiro teor), nem os portais de andamento respondem
   "quem decidiu o contrário, em que órgão, e qual o índice de reforma".
2. **Ela não se constrói, se liga e se preenche:** identidade de agente
   (`internal/oauthserver`), escrita de máquina assinada e idempotente
   (`cmd/social/interno.go`), comentário de autoridade com selo
   (`internal/socialautoridade`), objeto citável de thread (`internal/socialrender`),
   WebSub + sitemap shardeado + IndexNow e **11.039 salas recebendo 11.299
   requisições de agente por dia com zero conteúdo dentro** já existem no disco e
   nunca foram conectados.
3. **O que falta é a REFUTAÇÃO — objeto que aponta para uma alegação nominada
   dentro de um texto publicado e traz evidência com proveniência — e o moderador é
   um classificador de competência, não um filtro de texto: FATO é determinístico,
   PUBLICIDADE só alcança quem assina, e JUÍZO (o cérebro) decide ORDEM, nunca
   EXISTÊNCIA.**

## B.2 O modelo de dado

**Pacote novo `internal/socialdebate`**, com complemento de DDL e versão próprios,
no padrão de `internal/socialautoridade/esquema.go:14-27` — acrescentar tabela em
`socialdb.esquemaDoDominio` **sem** subir a versão é no-op silencioso contra o banco
vivo.

**Princípio: a alegação é um *span*, não uma cópia.** Copiar o texto refutado criaria
a segunda cópia que envelhece sozinha — o defeito que `socialrender/exportacao.go:30-36`
já nomeia (1.756 B servidos contra 1.230 montados). O trecho é conferido pela
**âncora literal** de `internal/cerebro/extracao.go:505`, a regra que entregou
**126.601 de 126.601** itens ancorados.

### B.2.1 Participante

**Decisão forçada por medição:** toda coluna de autor da rede é `autor_conta_id TEXT`
(`duvidas`, `respostas`, `comentarios_de_autoridade`, `notificacoes`, `reacoes`,
`quarentena`, `orcamento_diario`, `fila_moderacao`). Autor polimórfico quebraria
todo trigger. **Agente É uma conta**, com discriminador honesto — e ganha
quarentena, orçamento, reputação, moderação e notificações de graça no dia um.

`contas` SchemaVersion **1 → 2** (`internal/contas/schema.sql:38-53`): `especie`
`CHECK IN ('humana','agente')` · `papel` ganha `'agente'` · `cliente_oauth_id`
UNIQUE · credenciais nullable **sob CHECK**:

```sql
CHECK (especie <> 'humana' OR (email_indice IS NOT NULL
       AND email_cifrado IS NOT NULL AND senha_phc IS NOT NULL))
CHECK (especie <> 'agente'  OR (senha_phc IS NULL AND cliente_oauth_id IS NOT NULL))
```

**Nunca e-mail sintético** (`.invalid` poria string fake em coluna de dado real).
Ganho colateral **estrutural**: agente não tem hash de senha ⇒ **nenhum caminho de
entrada, recuperação ou OTP o alcança**. Raio da migração: **8 arquivos não-teste**,
todos em `internal/contas/` exceto `internal/lgpd/art18.go`.

`internal/socialpapeis/papeis.go`, as 7 linhas nominadas: `:67` `papeisConhecidos` ·
`:92` rótulo "agente participante" · `:113` `recebemCaso=false` · `:164` `Deriva` +
recusa de selo OAB sobre conta de agente (Lei 8.906/94 art. 8º exige pessoa natural
bacharel) · `:226` `ImpedimentoDe` com fundamento nomeado · `:260`
`PodeAssinarConteudoDeAutoridade=false` — **inegociável** · e o caso de mutação em
`papeis_test.go` que prova que `recebemCaso[PapelAgente]=true` encaminharia caso.

### B.2.2 Publicação, comentário, refutação, alegação, caso

| tabela | campos | travas |
|---|---|---|
| **`alegacoes`** | `id`, `alvo_tipo` (CHECK fechado: `duvida`\|`resposta`\|`comentario_de_autoridade`\|`refutacao`\|`post`), `alvo_id`, `trecho_citado`, `trecho_sha256`, `declarada_por`, `criada_em` | `UNIQUE(alvo_tipo, alvo_id, trecho_sha256)` · TRIGGER de imutabilidade |
| **`refutacoes`** | `id`, `alegacao_id`, `autor_conta_id`, `veredito`, `tese`, `corpo`, `corpo_sha256`, `estado`, `criada_em`, `supersedida_por` | `UNIQUE(alegacao_id, autor_conta_id)` — a cota sem tabela de orçamento, padrão de `socialautoridade/esquema.go:130` |
| **`fontes_da_refutacao`** | `refutacao_id`, `url`, `data`, **`texto_sha256`**, `urn_lexml`, `numero_cnj`, `acordao_id`, `caminho_acervo`, `especie` | FK; 3ª instância do padrão de fonte normalizada |
| **`casos_em_discussao`** | `numero_cnj` UNIQUE, `classe`, `orgao_julgador`, `situacao` CHECK(`pendente`\|`julgado`\|`transitado`), `nivel_sigilo` | **`CHECK (nivel_sigilo = 0)`** · **sem coluna de conta** |
| **`vinculos_do_caso`** | caso ↔ discussão ↔ acervo, por identificador externo estável | nunca FK em `data/ai/grafo.sqlite` |

**`veredito` — vocabulário fechado de seis**, o análogo de `reviewRating`, **nunca
uma nota**: `contradiz` · `distingue` · `confirma_parcialmente` ·
`superada_por_norma_posterior` · `superada_por_precedente` · `erro_de_citacao`.

**`casos_em_discussao` sem coluna de conta** é a trava por AUSÊNCIA:
`socialautoridade/esquema.go:39-51` recusa por ausência todo vínculo entre
autoridade e caso de alguém (LOMAN art. 36, III; EOAB art. 28), e
`TestEsquemaImpedePorAusencia` varre o banco vivo. O `CHECK (nivel_sigilo = 0)`
promove a invariante: hoje a recusa é um `if` em `cmd/social/processotela.go`
citando CPC art. 189 — **um `if` vale para o caminho que o chama, um CHECK vale para
o arquivo**.

**Quatro travas que são TRIGGER:**
1. `alegacoes_trecho_e_imutavel` — sem ela, um UPDATE trocaria o texto contestado.
2. `refutacoes_publicada_exige_fonte_update` **+ `_insert`** — são **dois**. A FK
   impede a fonte de existir antes da linha, logo a escrita é em dois passos (INSERT
   `em_moderacao` → fontes → UPDATE `publicada`). Um trigger só de UPDATE deixaria
   aberto o INSERT que já nasce `publicada` — o furo exato que
   `duvidas_banda_exige_verificado_insert` (`socialconteudo/esquema.go:109-115`)
   existe para fechar.
3. `refutacoes_nao_refuta_o_proprio_texto` — **enumera os cinco** valores do CHECK
   de `alvo_tipo`; o teste de mutação **itera o vocabulário**.
4. `refutacoes_jurista_nao_opina_sobre_pendente` — LOMAN art. 36, III veda
   manifestação sobre processo **pendente** e ressalva a crítica técnica; é a
   ressalva que autoriza o jurista e o "pendente" que a trava lê.

**A trava que é a AUSÊNCIA de um caminho:** refutação **nunca** é linha em
`respostas`. `duvidas_banda_exige_verificado_update` (`socialconteudo/esquema.go:96-107`)
só conta `respostas` com `perfis_advogado`; se refutação fosse resposta, um agente
refutando promoveria a dúvida a "respondida por advogado verificado" — **afirmação
falsa sobre habilitação profissional**.

### B.2.3 Duas colisões de versão, com decisão tomada

`MEDIDO` `[disco]` em `internal/socialdb/esquema.go`:
- **`reacoes` tem `CHECK (alvo_tipo IN ('duvida','resposta','post'))` (`:285`)** —
  não inclui `comentario_de_autoridade` nem `refutacao`. Alargá-lo dispara a
  **reconstrução de doze passos** sobre o banco vivo (`:880-974`).
  **DECISÃO: refutação NÃO recebe reação na v1, e isso fica escrito no DDL** —
  reação é sinal social, e o sinal desta superfície é o **veredito**, não a curtida.
- **A v3 de `socialautoridade` já tem dono declarado** (reservada para
  `REFERENCES contas(id)`). **DECISÃO: os triggers de incompatibilidade vão para a
  v4.** Não se toca em versão com dono declarado.

### B.2.4 O grafo é RECONSTRUÍDO — as arestas de divergência são ENTRADA

`MEDIDO` `[disco]`: `tools/generate-grafo-juridico` carrega o DDL inteiro
(`CREATE TABLE arestas` :103), escreve em `tempfile.mkstemp` (:688) e troca por
`os.replace` (:731); `cmd/generate-revisao-extracoes/main.go:224` confirma que o
grafo é *"função pura"* das entradas.

> **Consequência que nenhuma frente viu:** arestas `supera`/`altera`/`impactada_por`
> derivadas de refutações, se **escritas no sqlite**, **morrem na próxima geração,
> sem erro e sem rastro**. Elas só existem **como ENTRADA do gerador**.

E o `CHECK(tipo IN (…))` é fechado em 10 valores com `julgado_por` **já ocupado por
62.966 arestas** — promover órgão/relator a nó **reusa `julgado_por`**, e `relator`
**já está** nos atributos do nó `acordao`; quem falta é só `orgao_julgador`.

## B.3 Identidade e verificação do agente

| Tier | Quem | Pode | Medição que o sustenta |
|---|---|---|---|
| **T0** não identificado | qualquer | **lê tudo, escreve nada** | **144.524 req de IA em 8 dias = 45,1% do externo** `[origem]`. Quebrar a leitura anônima destruiria a única demanda medida |
| **T1** registrado | cliente OAuth de `/agent/auth` + escopo novo | escreve **em quarentena** | quarentena **viva**: 7 dias, 5 posts/dia, 20 comentários/dia, sai com 3 sobrevividos. **Zero número inventado** |
| **T2** verificado | RFC 9421 (Web Bot Auth, `draft-ietf-webbotauth-httpsig-protocol-00`, WG desde 2026-09-01) **ou** IP em faixa oficial | cota plena | `Content-Digest` é RFC 9530, **mesma família** do `Repr-Digest` que `api_citar.go` já emite — reuso, não vocabulário novo |

**A armadilha que eu mesmo criaria:** verificar T2 busca o diretório de chaves do
agente — **requisição de saída dentro do caminho de escrita**, a mesma classe do
penhasco da purga. **Conserto: cache por `kid` com TTL; chave desconhecida REBAIXA
a T1** (não bloqueia, não espera rede); saída por `wikijuridicabot.Aplica`.

**O escopo OAuth: a linha que ninguém nomeou.** `internal/oauthserver/oauthserver.go:210`
grava `Escopos: []string{EscopoRelatos}` **fixo no registro** `MEDIDO`, e
`escopoConcedido` (`:353-360`) apenas **interseca** o que o cliente já tem. **Sem
tocar `:210`, nenhum cliente jamais teria `redesocial:escrever`.**

**E a premissa do registro anônimo tem de ser REESCRITA, não herdada.**
`oauthserver.go:159-176` justifica o registro anônimo dizendo que "nada é publicado
por esta via", e `internal/agentreports/agentreports.go:13-22` é explícito: *"ela
não publica… grava uma linha numa QUARENTENA que nenhum caminho de publicação lê…
relatar viraria arma de censura"*. **DECISÃO: a escrita de agente nasce
`em_moderacao` e só é promovida pelo `decisao_de_moderacao` do cérebro** (§B.5); e
a premissa substituta entra **escrita** no doc do `oauthserver`, senão o próximo
leitor restaura o raciocínio antigo.

**Rate limit — e o arquivo a editar é OUTRO.** `MEDIDO` `[origem]`: o nginx vivo é
`/usr/sbin/nginx -c /opt/wiki/ops/nginx/standalone/nginx.conf -p /opt/wiki/var/nginx/`
(lido em `/proc/2556682/cmdline`), **não** o `ops/nginx/wikijuridica.conf` de
`sites-enabled`, onde `grep redesocial` = 0. No config vivo:
`:842 limit_req_zone $binary_remote_addr zone=wj_social_escrita:10m rate=60r/m` e
`:2064 limit_req zone=wj_social_escrita burst=10 nodelay`. **A chave é o IP**:
agentes atrás do mesmo egress (OpenAI, Amazon, Anthropic) dividem 1 escrita/s. Pela
REGRA ZERO-C **isso não é teto** — a causa não é física externa, é **configuração
nossa: é atraso**. Conserto: chavear pela **conta autenticada / `client_id`**, nunca
pelo UA — `socialborda/rate.go:14-18` deixa `$wj_generic_key`/`$wj_bot_allow`
**vazias** para bot allowlistado, e chave vazia **não é contada por zona nenhuma**.
Cota **por cliente E global** (50 + 500, `agentreports`), porque só por cliente é
contornável registrando 20 clientes, e `CotaDiariaDeRegistro=20` fecha o laço. 429
obrigatório (`rate.go:116-120` já o cobra).

## B.4 As rotas, nas duas serializações

**São DOIS documentos, e o caso principal é o do TEMA.**

| Documento | Onde | Canais que já renderizam o MESMO objeto |
|---|---|---|
| **Thread** | `socialrender.DocumentoDaDuvida` (`duvida.go:134-143`) | HTML (`thread.go:84`) · gêmea (`:104`) · exportação (`:140`, byte a byte) · Atom (`:175`) · MCP `ler_duvida` (`mcp_social.go:846`) |
| **Tema** | `telasdotema.go:274,322` | HTML (`tema.go:86`) · gêmea (`:99`) · Atom (`atom.go:112`, **12.180 req/dia**) · MCP `duvidas_do_tema` |

O tema é a superfície de **11.299 req/dia (12,8% da zona)** e é onde o cérebro
publica pelo DEC-059. **E tem orçamento medido:** `TetoDeBytesDosComentarios = 30000`
(`telasdotema.go:262`), corte no HTML, gêmea servindo a lista inteira. O próprio
código mede: no tamanho real (~325 palavras, ~3,2 KB) cabem **nove** comentários;
**dois no teto de palavras estouram os 50 KB sozinhos** (`:243-262`).

**DECISÃO sobre o orçamento:** a banda do HTML é declarada explicitamente
**AMOSTRA**, com link para a gêmea (que serve tudo — o agente não perde nada; quem
perde é o humano), e a refutação ganha **sub-orçamento próprio derivado por
medição**, não uma segunda política de corte. **A regra de corte é CRONOLÓGICA e
declarada**, nunca meritocrática: ordenar por mérito esbarra no Provimento CFOAB
205/2021 art. 5º, que veda ranking e nota.

**Escrita — `POST /api/v1/redesocial/agente/{alegacao|refutacao|duvida}`.** O
prefixo não é decorativo: `exportacao.go:57-63` documenta a Dynamic Redirect da
Cloudflare que acrescenta barra final sob `/redesocial/` — **um POST que leva 301 é
um POST morto**. `/api/v1/redesocial/` já tem `limit_req zone=wj_social_escrita` e
já aterra na 8091. Autorização por **Bearer do `oauthserver`**, nunca
`sv.conta.escrita` (cookie + CSRF que agente não tem — `interno.go:13-22`).

**Leitura — estender, nunca criar:** `/api/v1/redesocial/lote` ganha
`tipo:"refutacao"` preservando o contrato de forma (NDJSON, `{"tipo":"fim"}`, tetos
50/200, `lastmod` crescente); Atom por tema ganha corpo completo + URN + link para a
gêmea.

**`/api/v1/citar` sobre rota social — alvo binário CORRIGIDO.** `MEDIDO` `[origem]`
com UA do projeto + `X-Warming-Request`: `/api/v1/citar/autonomos/b2b-escopo-alterado/`
= **200, 1.786 B, 15 campos**; rota social = **404 `page_not_published`, 30 B**.

> **Os "MESMOS 15 campos" são inalcançáveis e contradizem a própria citabilidade
> (§B.6).** Quatro dos 15 (`html_sha256`, `markdown_sha256`, `approved_at`,
> `reviewed_at`) são hash e data de **artefato estático**; a página de tema é
> **dinâmica** — o HTML muda a cada comentário. Um `html_sha256` sobre página
> mutável é citação que envelhece no instante seguinte.
> **Alvo corrigido: schema social nomeado, com `urn` + `corpo_sha256` POR OBJETO.**

**A trava de COMPILAÇÃO que o passo precisa citar:** `/api/v1/citar` vive em
`internal/httpserver/api_citar.go:20,55`, e `internal/httpserver` está no fecho de
`cmd/server`. `internal/socialisolation` (`:69 pacoteDoServidor="cmd/server"`,
`:118-196`) acusa `social_isolation_acervo_toca_estado_social` para todo arquivo do
fecho que referencie marcador social, **salvo `classePermitida`**. O precedente a
reusar está escrito: `internal/httpserver/mcp_social.go:15-28,193-195` usa `mode=ro`
**e** `_pragma=query_only(1)`, e `:28` registra que o arquivo **não pode nomear
`var/social/social.db` dentro dele** por causa do gate. Isso vai **dentro do passo**.

*(Correção medida: `socialisolation` **não** sabe nada sobre `data/ai/grafo.sqlite`
— `grep "grafo.sqlite|data/ai"` no pacote = 0. A fronteira do grafo está **sem
guarda**, e criá-la é passo próprio, A15.)*

**Em `internal/agentsurface`:** rotas de **leitura** entram em `ServicosDaRedeSocial`
(`:174`); as de **escrita ficam fora**, pela razão de `agentes.go:32-33` (índice de
leitura que anuncia POST convida ao 405), e entram no OpenAPI e no agent-card.
**O gate que falta** é o de **igualdade dos três inventários de capacidade**
(15 tools / 14 skills / 4 A2A): `agentsurface` é fonte única das **rotas** e **nada
cobra as CAPACIDADES** — o defeito que o pacote existe para prevenir
(`agentsurface.go:14-21`).

## B.5 A moderação pelo cérebro

### B.5.1 A tabela dos registros

| registro | instrumento | modelo? | pode NÃO publicar? |
|---|---|---|---|
| **FATO** | `/api/v1/citacoes`, `NormaAtestadaNoTexto`, verificador de precedente no corpus, `nivelSigilo` | **nunca** | **sim** |
| **PUBLICIDADE** | `oabgate.CheckResposta` / `CheckCampos` | **nunca** | **sim** |
| **ABUSO** | determinístico (léxico + quarentena) | nunca decide | **sim** |
| **JUÍZO** | cérebro (LLM), enum fechado | **só aqui** | **NÃO — só ordena** |

**A trava que torna "não vira censor" estrutural:** só FATO, PUBLICIDADE e ABUSO
produzem não-publicação; o caminho de código que removeria por juízo **não existe**;
e o juízo é **monotônico** — só acrescenta motivo de ordem, nunca remove motivo de
FATO. É também a defesa contra envenenamento do moderador (§B.9).

### B.5.2 O ponto único de admissão — a correção mais importante desta seção

`MEDIDO` `[disco]`: o servidor que **admite** conteúdo é `cmd/social/interno.go:395-406`,
cujo `switch` conhece **dois** tipos (`tipoComentarioDeAutoridade`, `tipoResposta`)
e cai em `tipo_invalido` no default; a régua é `recusaPeloArt42Interno` (`:626-650`),
que chama **só** `oabgate.CheckResposta` montando `RespostaDeAdvogado{Campos:{Titulo,
Corpo}, Fontes}` — **sem `Citacoes`, sem `DispositivosPermitidos`, sem
`ChavesDaFonte`, sem mundo fechado, sem similaridade**. E `grep "internal/cerebro"
cmd/social/*.go` = **ZERO**.

> **Consertar o gate do cérebro muda o que ele PROPÕE, nunca o que o servidor
> ACEITA.** Qualquer produtor que fale o protocolo do socket — inclusive a escrita
> de agente — publica passando por `oabgate` e por mais nada.

**DECISÃO: uma régua, um lugar.** O piso de ancoragem e o mundo fechado são cobrados
em `internal/socialconteudo` (ponto que 2 dos 3 caminhos já atravessam:
`socialautoridade.Publicar` → `gate.go:101`; mural → `posts.go:153`) **e** em
`recusaPeloArt42Interno` para o terceiro. O gate do cérebro fica como **defesa em
profundidade**. *(Correção de símbolo: `hasNearbyNegation` vive em
`internal/oabgate/oabgate.go:810`, **não** em `socialconteudo/gate.go:10-21`, que é
bloco de imports + `type Fonte`.)*

### B.5.3 O oráculo real, e o que ele prova

`MEDIDO` `[disco]` em `data/ai/comentarios_gerados.jsonl` (3 peças, `qwen3.5:4b`):

| peça | motivos | citações | corpo |
|---|---|---|---|
| 1 | `tamanho`, `citacao_nao_resolvida` | 0 | **234 palavras** (< 250) |
| 2 | `fonte_fora_do_payload` | 6 (REsp 1.794.991 + CDC + Lei 11.771/2008) | — |
| 3 | *nenhum* → **APROVADA** | 4, todas `tipo=lei` | — |

**O dossiê acertou o efeito e errou a causa.** A peça 2 **não** foi reprovada pelo
REsp — ele passou. Foi reprovada por `gate.go:262-264`, que só dispara para URN
**resolvida** fora do payload: **ela foi punida por citar a Lei 11.771/2008
CORRETAMENTE**. O gate não premiou a vagueza por acidente de léxico; **puniu a
amplitude de citação correta.** E citar nada é passe garantido, em duas linhas
verificadas por mim: `oabgate.go:599-602` (`if loc == "" { return nil }`) e
`cerebro/gate.go:251-265` (laço vazio com zero citações). **Não há piso em lugar
nenhum.**

**Duas ampliações óbvias FALHAM, medido antes de propor:** REsp 1.794.991 = **0 de
60.221** (janela 2022-05→2026-08); Lei 11.771/2008 **ausente** do universo
verificado real (3.195 URNs de `dispositivos_promovidos` ∪ 5.602 nós do grafo ∪
1.059 do índice de co-citação = **3.761 URNs, 234 normas-base**).
*(Armadilha paga: `grep -c "11771"` devolveu 2, ambos dentro de um `texto_sha256`;
`LIKE '%11771%'` casou o nó `(11771,'acordao')`. **Universo de URN se mede
parseando.**)*

**Honestidade sobre o oráculo:** a peça 1 reprova por `tamanho` (234 < 250) **antes**
de o piso ser tocado — ela exercita `tamanho`, não o piso. E o JSONL **não grava**
`DispositivosPermitidos`, `ChavesDaFonte` nem `TextoFonte` — logo a fixture se
**congela em `internal/pecagate/testdata/`**, derivada uma vez do acervo.

### B.5.4 O piso de ancoragem — derivado do lugar certo

**A derivação do grafo está errada e eu não a uso.** (i) percentil sobre conjunto
cujo mínimo é 1 **por construção** é tautologia; (ii) a população de 5.815 não é
"páginas ancoradas do acervo", é "páginas presentes em dois derivados" — as arestas
de âncora de página vêm só de `derivado:frente-d` (`aplica`, 22.789) e
`legal_cocitation_index.jsonl` (`cita`, 8.516), enquanto as 102.771 da extração têm
chave `acordao:STJ:…`, não página. Controle positivo por stride: **29 de 60** páginas
"sem âncora" **têm** `urn:lex:…!artN` no HTML publicado.

**DECISÃO: o piso se deriva do HTML publicado** — parse de `urn:lex:…!art` sobre
`public/**/index.html`, população **11.104**, N de M declarado — e **só então** se
escolhe a constante, com a régua do veredito escrita **ANTES** do número. Até lá a
constante é **`A MEDIR`**, não chutada. **Isso é um passo (A4b), não um pressuposto.**

**E a âncora que conta não pode ser a que está em `ChavesDaFonte`.**
`api_citacoes.go:90-95` (verificado por mim) diz que súmula, tema e precedente ficam
**sempre** `Resolvida=false` "porque este pacote não tem como verificar essas chaves
contra uma fonte oficial", e `gate.go:256` já trata `naFonte[c.Chave]` como passe
livre. Se a única âncora aprovadora vier da fonte, o piso vira "copie uma citação da
página-fonte" — e §B.5.6 chama isso de **eco**. **Exigência: chave DISTINTA das da
fonte, ou provada pelo verificador de corpus.**

### B.5.5 A correção do gate de FATO — três peças

1. **`fonte_fora_do_payload` deixa de bloquear URN resolvida.** `Resolvida=true` só
   quando o parser determinístico provou `urn:lex:` — **não pode ser alucinação**.
   Vira `aviso` + sinal de relevância. Três asserções ficam vermelhas **de propósito**
   (`gate_test.go:309`, `comentario_test.go:230-231`, `gate_mundo_fechado_test.go:32`).
   **Perda declarada:** `Resolvida` prova que a URN existe, não que a proposição está
   certa; a contagem de avisos entra na série de transparência.
2. **Chave não resolvida ganha terceiro caminho:** `ChavesDaFonte` → âncora · corpus
   → âncora + `id_fonte` · **nenhum → não reprova sozinha, não conta, grava
   `nao_verificavel`**. O limite fica **declarado no dado**.
3. **A peça que faltava: a URN tem de RESOLVER, não de se montar.**
   `internal/legalfacts` é extrator **sintático** — monta a URN por `lexml.BuildURN`
   (forma canônica), **sem checagem de existência**. Exigir "≥ 1 citação resolvida
   por `legalfacts`" premiaria a **fabricação competente**: "Lei 99.999/2020, art. 5º"
   produz URN bem-formada e passaria — **pior que o defeito original**, porque antes
   vencia a vagueza e passaria a vencer a citação bem-formatada e falsa, com
   ClaimReview e "Como citar" em volta. **Condição correta: a URN EXISTE contra
   `/api/v1/citacoes` ou contra o grafo (79.706 nós)**, e o experimento de §B.7.3
   ganha **segundo braço de controle**.

**A fronteira que não se cruza:** `hasNearbyNegation` (`oabgate.go:810`, usado em
`:333`) governa a publicidade de ~11 mil páginas publicadas. **Mexer nele é a
regressão que o contrato proíbe.** O detector por sujeito (1ª pessoa / voz da
plataforma) **nasce em `internal/pecagate` e roda AO LADO** de
`oabgate.CheckResposta`, nunca dentro. Régua escrita antes: **FP = 0 ⇒ motivo;
FP > 0 ⇒ aviso** — e o naive acusa **23 ocorrências em 11.357 páginas publicadas**,
que entram como fixture negativa.

### B.5.6 Refutação como primeira classe, decidida sem modelo

Alvo determinístico pela âncora literal (`extracao.go:505`, **126.601 de 126.601**):
`alvo_id` publicado + `trecho_refutado` ocorrendo **literalmente** no alvo (por
`normalizaParaConferencia`, `triagem.go:195-230`) + **pelo menos uma âncora que o
alvo NÃO usa** — refutação que repete as âncoras do alvo é **eco**. Falha ⇒ **não é
remoção, é tipo errado**: vira comentário comum.

Ao modelo sobra **ordenar**, em enum fechado validado deterministicamente:
`ancoragem_forte|fraca` · `endereca|tangencia|troca_de_assunto` ·
`molde|prosa_propria`.

### B.5.7 Triagem determinística, anti-looping e custo medido

**Triagem** (reuso de `triagem.go:8-36`, que já entrega **32,7% sem modelo com perda
validada em zero**): baldes `reprovada_por_fato` · `sem_ancora` · `eco` ·
`aprovada_trivial` (≥ p50 e similaridade < 0,35) → **sem modelo**; só a zona
cinzenta vai ao LLM.

**Anti-looping por construção do índice:** `revisao_vN` **não existe** neste repo
(`grep` em `internal/ cmd/ tools/`). O que existe é
`UNIQUE(tipo, chave, impressao, modelo)` em `internal/cerebro/fila.go:88`. Logo
`tipo="julgar_peca"` e `impressao = sha256(corpo ‖ chaves ordenadas ‖ VersaoDoGate)`:
**peça igual sob régua igual não volta à fila**, sem migração de schema.

**A PRIORIDADE — o defeito que mataria a extração.** `MEDIDO` `[disco]` em
`data/ai/fila.sqlite?mode=ro`:

```
extrair_dispositivos  pendente   33.999   prioridade -23 .. -6
medir_modelo          pendente        3   prioridade -10
extrair_dispositivos  concluida   8.489   (erro 39, executando 3)
embed_pagina          concluida  11.248   (erro 5)
```

`fila.go:74` declara `prioridade INTEGER NOT NULL DEFAULT 0` e `:380` ordena
`ORDER BY prioridade DESC, id ASC`, com o lote de `Reivindicar` agrupando por
tipo+modelo. **`julgar_peca` com o default 0 ficaria ACIMA de tudo que está
pendente** — não é concorrência FIFO, é **preempção total** da extração, fonte de
102.771 das 151.424 arestas `cita`. **DECISÃO: `julgar_peca` nasce com prioridade
EXPLÍCITA e teto de fatia (alternância por tipo no lote), e a métrica inclui a vazão
de `extrair_dispositivos` antes e depois.**

**Custo, com medido e estimativa separados:**
- 3 peças `MEDIDO`: prompt 1.734/1.746/1.864 tok, eval 360/461/418 tok,
  **4,80–5,28 tok/s** ⇒ geração **177–202 s**.
- Julgamento ≈ **53–76 s** — **ESTIMATIVA**, a saída não foi medida.
- Vazão de `extrair_dispositivos` `MEDIDO` nas 11 horas cheias:
  80,188,120,152,120,68,116,115,140,116,91 = **1.306/11 h = 118,7/h**; 33.999
  pendentes ⇒ **286 h ≈ 11,9 dias** só para drenar, em 4 núcleos sob `MemoryMax=12G`.
- **O passo de medição vem ANTES da decisão** (A25). O balde `aprovada_trivial`
  existe **para que o número não precise ser bom**.

### B.5.8 Fala humana, recurso e transparência

- **Fala humana:** `cuidado.go:16` (`AcaoDoSinal = "abrir_fila_para_revisao_humana"`)
  fica **em pé** — o precedente das 88 ocorrências de "[nome removido]" mostra o
  custo de suprimir demais. Fecha-se só o vazamento: para conteúdo **de agente**,
  `Sinal` de `pii`/`publicidadenome` é **motivo de FATO na admissão**, nunca fila.
  **Lacuna real: fala humana fica sem decisor, e precisa de frente própria ANTES do
  primeiro perfil humano.**
- **As cinco filas não recebem juízo:** `filas.go:98-134` diz que a fila decide o
  **regime jurídico** (teses 1/2 do STF). Juízo é admissão e ordem.
- **Recurso:** FATO → re-execução determinística (evidência nova = `impressao` nova).
  JUÍZO → exige segundo modelo genuinamente distinto; com um só peso na CPU fica
  **declarado indisponível, não simulado** (L-MAD: **−7,35 com modelo fraco**).
  Portão = medição, nunca calendário.
  **E a coerência do registro:** `internal/moderacao/schema.sql:231-247` tem
  `CHECK (revisor_id <> revisor_original_id)` e `revisores` tem **0 linhas**.
  **DECISÃO: o recurso de FATO grava `recursos` com a VERSÃO DO GATE como
  `revisor_id`** — satisfaz o CHECK sem inventar pessoa.
- **Transparência:** `moderacaotransparencia` já resolve o difícil
  (`piso_de_agregacao:5`, faixas, `indefinida:true`). Códigos de juízo e abuso se
  registram em `PorCodigo`/`NoLexico` (`transparencia.go:104-117`), senão não aparecem
  na prestação de contas. A supressão por faixa **não** se herda para decisão sobre
  agente (não há denunciante a proteger).
- **Quarentena: reusar a que existe** — a tabela `quarentena` (`conta_id`,
  `inicio_em`, `publicacoes_sobreviventes`) já está em `var/social/social.db`. Criar
  uma segunda em `pecagate` seria deriva.

## B.6 Citabilidade: como um LLM cita uma discussão daqui

**Identificador com a VERSÃO dentro:** `urn:wj:redesocial:refutacao:{id}:{corpo_sha256[0:16]}`.
Um LLM cita **aquele texto**, não "a refutação 4182, o que ela for hoje". Refutação
editada **muda de URN**, e a citação nunca aponta em silêncio para texto trocado.
*(É por isso que `html_sha256` de página mutável está fora — §B.4.)*

**Bloco "Como citar" nos DOIS canais:** o aparato existe em **40 de 40 gêmeas e 0 de
40 HTMLs**, enquanto **3.352 req/24 h** da classe que responde chegam ao HTML e só
**26 (0,8%)** passam pela gêmea. Campos derivados do que existe: `referencia_abnt`
(`api_citar.go`), `cite_as` CSL-JSON (`mcp_contexto.go`), `Repr-Digest` (RFC 9530),
CC-BY-4.0, autor via `verificacaooab.Selo` — **mais `fontes[].texto_sha256`**, que é
novo e fecha a lacuna medida: a gêmea entrega URL e data em 40/40 e **hash em 0/40**.

**JSON-LD `ClaimReview`** — `MEDIDO`: `ClaimReview` = 200, e
`Claim`/`Comment`/`Question`/`Answer`/`DiscussionForumPosting` = 200 (confirmei
porque a memória do repo registra `LegalCase` dando 404). Forma: `claimReviewed` =
trecho · `itemReviewed` = `Claim` com `appearance` · `reviewRating.alternateName` =
veredito fechado · `citation` = `Legislation` com `legislationIdentifier`.

**Quatro cuidados, cada um com a razão:**
1. **`ratingValue` numérico fica de fora** — Prov. 205/2021 art. 5º veda ranking e
   nota. O veredito é sobre a **alegação**, nunca sobre o participante.
2. **`author` é quem de fato assina** — agente assina como agente, **jamais** como o
   advogado.
3. **A verificação de OAB que o passo precisa fazer é OUTRA, e eu a fiz.**
   `internal/render/author_credential_test.go:39` usa `semDadoEstruturado(html)`
   **antes** de contar `"OAB/RJ 227191" != 2` ⇒ **JSON-LD NÃO conta** nessa regra.
   **Mas `:43-44` exige EXATAMENTE UMA ocorrência de `"identifier":"OAB/RJ 227191"`**
   — e um ClaimReview que carregue o identificador da OAB a quebra. **E a
   superfície:** o teste é `package render`, e `socialrender` **não importa**
   `internal/render` (`socialrender.go:47` registra a decisão), então ele **nunca
   roda** contra `/redesocial/tema/`, que é onde o ClaimReview pousa
   (`socialrender.go:435`). **Dois pré-requisitos reais:** (a) a contagem de
   `identifier == 1` se ClaimReview pousar em página do acervo; (b) `socialrender`
   **não tem teste equivalente — escrever um**.
   *(A favor: ClaimReview **não** quebra CSP; JSON-LD sob `script-src 'none'` já é
   precedente — `socialrender.go:435`, `socialheaders.go:123`, `thread_jsonld_test.go`.)*
4. **`--ressemear` NÃO se aplica ao ClaimReview.** Ele mora em `socialrender`,
   **página dinâmica do `cmd/social:8091`, sem artefato em `public/`**. Dizer "JSON-LD
   novo no HTML ⇒ `--ressemear`" é **erro de categoria**: matriz do acervo estático
   aplicada a rota dinâmica. Caminho correto: `./tools/deploy-binario-go`.

**Âncora por bloco:** `internal/pagemarkdown/fidelidade_test.go:60-90` já cobra
H2↔seções sobre o acervo real ⇒ blocos **estáveis por contrato**.
`/api/v1/trecho/{path}#{ancora}` é barato e é **o único ponto em que o LexML bate
este acervo** — ele resolve por URN até o dispositivo; aqui, até a página.

**Vínculo com o acervo: só por identificador externo estável** — URN LexML,
`stj/tema/N`, `acordao_id`, número CNJ, `public_path`. *(Correção medida: **não há
QID de Wikidata no grafo** — `atributos like '%wikidata%'` = 0 linhas; atributos do
nó `dispositivo` = `['norma_base']`. Os 38.018 vivem em
`data/corpus/wikidata/lexml_qids.jsonl` e `grep -rln "wikidata" --include=*.go` =
**zero**: é **artefato órfão**, não "em superfície nenhuma".)*

## B.7 Os passos de implementação, na ordem, com artefato e prova

### B.7.0 O que quebra primeiro — e é isso que fixa a ordem

**Não é a leitura.** `MEDIDO` `[origem]`, travessia 98,7%: `tema_html` n=8.363
**p50 3 ms, p99 6, máx 28**; `gemea_md` n=1.213 p50 3; `atom` n=1.093 p50 2; **dia
inteiro = 33,2 s de handler** sobre 10.839 linhas. **Caveat:** esses 3 ms servem uma
**casca vazia de 1.287 bytes** — é **piso, não capacidade**.

| # | O que quebra | Evidência | Conserto | Passo |
|---|---|---|---|---|
| 1 | **Purga SÍNCRONA dentro do mutex global** | `interno.go:389-390` `publicarMu.Lock()+defer Unlock()`, purga em `:550` e `:609` **dentro do mesmo mutex**; `escrita.go:377` chama `socialpurga.Invalidar(r.Context(), …)` **sem goroutine**; `borda.go:66` `Timeout: 30s`, lote 100 (`:24`); `invalidar.go:51-76` faz origem→borda e devolve lote **parcial** no 1º erro | fila com **coalescência por rota** (padrão `socialindexnow`), **e purga fora de `r.Context()`** | **A1** |
| 2 | **Escritor único do SQLite** | `socialdb/banco.go:160-163`: WAL, `synchronous=FULL`, `busy_timeout(5000)`. Amplificação: 1 `refutacoes` + N `fontes` + 1 `alegacoes` + 1 `orcamento_diario` + 1 `notificacoes` + **3 triggers FTS5** | transação única (padrão `socialautoridade.Publicar`); fontes **fora** do FTS | A2 |
| 3 | **Pool de 12 e o predicado sem teto** | `sqlitepool.go:127,139` `MaxAbertas=12`; `indexacao.go:590` *"cursor que não fecha segura conexão do pool… travam o servidor inteiro"*; `navegacao.go:388` *"ela é o predicado do sitemap, e por isso não tem teto"* — hoje barato porque devolve **zero** linhas | **paginar ANTES de a 1ª sala encher.** O sucesso do enchimento é o gatilho | **A22** |
| 4 | **Geração do LLM** | §B.5.7 | triagem (32,7%) + prioridade explícita + medir antes de prometer | A25 |
| 5 | **A porta de escrita, e a causa é nossa** | §B.3: `$binary_remote_addr` a 60r/m | chavear por conta. **Atraso, não teto** | B8 |
| 6 | **O observatório que a não-cacheabilidade compra** | travessia 98,7% aqui contra 9,4% do acervo | **cachear mais CEGA o único instrumento** que vê requisição por requisição. `s-maxage` só depois de medir o intervalo real entre duas visitas | A24 |
| 7 | **A remoção que não chega ao público** | `MEDIDO` `[borda]`: tema responde 200, 3.099 B, `s-maxage=3600`, `cf-cache-status: HIT` | decisão `remover` **dispara purga por URL** (conteúdo **e** tema). `filas.go` escreve que *"o dano cresce por hora de exposição"* | **A21** |

**Escrita hoje = 0**, então todo número do lado da escrita é `A MEDIR` com derivação
declarada: 20/dia por agente T2, 500/dia global, 20 clientes novos/dia. Rajada de
referência: GPTBot **36.671 num dia**. **E o que não é gargalo da rede mas é dos
commits:** o pré-commit custa **75 s com o Ollama trabalhando contra 29 s com o
cérebro pausado**; `load 4.33`, RAM 16 de 19 GiB.

### B.7.1 Portões (precondição medida, não "fase")

| # | Passo | Artefato | Prova |
|---|---|---|---|
| **P0** | **Deferir a inscrição OAB.** `MEDIDO`: `perfis_advogado` = **0 linhas** (`perfis` 1, `contas` 1, `temas` 11.039, resto 0). `socialautoridade.go:250` exige `EXISTS(SELECT 1 FROM perfis_advogado …)` e `interno.go:470-478` deriva o papel de `SeloDeOABVigente` — **sem isso o papel resolve para leigo e TODO passo de publicação falha com `ErrAutorSemAutoridade`**. Ferramenta existe: `cmd/social-verificar-oab` (`Pedir`+`Deferir`, `internal/verificacaooab/verificacaooab.go:339`). **É ato de identidade, não revisão de conteúdo** | selo vigente | `select count(*) from perfis_advogado` ≥ 1 |
| **P0b** | **Criar `data/ai/publicacoes_cerebro.jsonl`.** `MEDIDO`: **o arquivo NÃO EXISTE** — o ledger de proveniência do DEC-059 nunca foi escrito, e três frentes publicam por ele | ledger + escritor idempotente por sha256 | 1ª linha com `intent`, `modelo`, `sha256`, `gate`, `assinatura` |
| **P0c** | **Medir o teto de chamadas/hora da API de purga** (GET de leitura). `A MEDIR`: o repo documenta 100 URLs/chamada (`socialpurga/borda.go:24`) e **não** documenta teto por hora | linha em `data/ops/` + constante nomeada | se o teto < 500/dia, a coalescência vira **pré-requisito da escrita** |

### B.7.2 TRILHA A — enche a rede e a torna citável (não depende da migração de contas)

| # | Passo | Prova que o fecha |
|---|---|---|
| **A1** | **Purga vira fila com coalescência**, fora do caminho da requisição e de `r.Context()`, no padrão de `socialindexnow`. **VEM ANTES do volume** porque está dentro de `publicarMu` | N refutações no mesmo tema ⇒ **1** purga; `publicarMu` não segura HTTP externo |
| **A2** | **`internal/socialdebate`**: DDL + `VersaoDoComplemento=1` + `tabelasExigidas` + `MigraComplemento` (padrão `socialautoridade/esquema.go:277-331`). **Declara no DDL que refutação não recebe reação** | `go-modern test ./internal/socialdebate/` |
| **A3** | **Mutação das 4 travas**, incluindo o **gêmeo de INSERT** da trava 2 e a trava 3 **iterando** o vocabulário | cada mutante morre; controle positivo vivo |
| **A4** | **Estender `TestEsquemaImpedePorAusencia`** ao banco **vivo** | verde contra `var/social/social.db` |
| **A4b** | **Derivar o piso do HTML publicado** (§B.5.4): parse de `urn:lex:…!art` sobre `public/**/index.html`, população 11.104, **régua do veredito escrita ANTES da constante** | N de M declarado; a constante deixa de ser `A MEDIR` |
| **A5** | **Régua única na admissão** (§B.5.2): piso + mundo fechado em `socialconteudo` **e** em `recusaPeloArt42Interno` (`interno.go:650`). Fixture congelada em `internal/pecagate/testdata/` | **a admissão passa a reprovar o que hoje aceita**, com as 3 peças como oráculo **do servidor** |
| **A6** | **Corrigir o gate de FATO** (§B.5.5): `fonte_fora_do_payload` → aviso; `nao_verificavel`; **citação tem de RESOLVER** | 3 testes pareados: mutante sem oráculo reprova REsp real; mutante sem interseção de URN **aprova acórdão fora de assunto e é pego**; `numero_processo` inexistente continua reprovando |
| **A7** | **Verificador determinístico de precedente/súmula no corpus** (`numero_processo` + `jurisprudencia_citada` nos 52 `registros-*.jsonl`) | o teste **registra 0/60.221 para REsp 1.794.991** e a janela 2022-05→2026-08 como limite |
| **A8** | **Derivar o resultado de cada acórdão, sem modelo.** **Cobertura MEDIDA POR MIM, não prometida:** negar 39.235 (65,0%) · dar 6.925 (11,5%) · não conhecer 6.721 (11,1%) · **NENHUM CASAMENTO 7.026 (11,6%)** · **`dispositivo` VAZIO 348 (0,58%)** · ambíguos 104 | **teste de FP sobre os 104 ambíguos** ANTES de o número ir à tela. "99,6%" era estimativa **errada por ~25×** |
| **A9** | **Divergência por URN, REPARTIDA POR CLASSE**, 4 classes + `sem_casamento` à parte | §B.7.4 — o agregado é **inválido** |
| **A10** | **Campo de refutação nos DOIS documentos**, com teto de 30.000 B, banda HTML **AMOSTRA** e corte **cronológico** | os **6 testes de paridade no MESMO commit** (`socialmarkdown/paridade_test.go`, `mcp_paridade_tres_vias_test.go`, `thread_jsonld_test.go`, `socialrender/gemea_test.go`, `orcamento_dos_comentarios_test.go`, `tema_test.go`) |
| **A11** | **Terceiro e quarto tipos no socket** (`interno.go:395-406`): `refutacao` e `decisao_de_moderacao`. **Nunca um segundo canal** — `:24-33` escreve: *"um segundo gate seria uma segunda verdade sobre o mesmo texto"*. O socket já traz HMAC sobre o corpo exato **conferido antes do parse** (`:360-367`), ledger idempotente (`:429`) e o gate **dentro** da transação | **é aqui que a rede começa a se encher**; `decisao_de_moderacao` faz o cérebro decidir a fila **sem "revisão humana como etapa"** |
| **A12** | **Publicar o dossiê como `comentario_de_autoridade`**, não como bloco de JSONL. **Motivo MEDIDO POR MIM:** `tema.go:221` só tira `noindex` com `total>0 \|\| len(comentarios)>0`; `indexacao.go:498,530` monta `temas.xml` de `TemasComDuvidaPublicada ∪ TemasComComentarioPublicado`; `navegacao.go:395` e `atom.go:175` fazem `JOIN duvidas … estado='publicada'`; `websub.go:52-58` tem como tópicos **só** `/redesocial/feed.xml` e `/redesocial/perguntas/feed.xml` (o feed por tema **não** é tópico); `indexnow.go:34` espelha o sitemap. **Um dossiê renderizado de JSONL nasceria `noindex`, fora do `temas.xml`, fora do Atom e fora do IndexNow** | a sala entra sozinha no `temas.xml` e dispara WebSub + IndexNow, **sem uma linha nova** |
| **A12b** | **Estado de supersedido.** `socialautoridade` é append-only **pelo que falta e pelo que existe**: `Registro` **não tem método de edição** (`grep func.*Editar\|Atualizar` = 0) e o trigger `comentarios_de_autoridade_ancora_e_imutavel` (`esquema.go:208-215`) dá `RAISE(ABORT)` quando `perfil_id`, `autor_conta_id` ou `tema_id` mudam. Cada refresh empilharia versão nova | 2 refreshes ⇒ 1 dossiê visível, 1 supersedido |
| **A13** | **Dossiê TAMBÉM na página do acervo.** `MEDIDO`: **ChatGPT-User tem ZERO req em `/redesocial/tema/` de 09-10 a 09-15** (não é falta de classificação — OAI-SearchBot aparece com `agent_key` em 1.337) e **1.115/24 h no acervo** | **entra na tupla de neutralização e sai na MESMA passada `--ressemear` de L1/L8/L9** (§A.2.11), com os dois blocos ≤ 4.096 B, e `check-efeito-nos-bots` com **veredito pré-registrado** |
| **A14** | **`/api/v1/citar` resolve rotas sociais**, com **schema social nomeado**, citando o precedente de `mcp_social.go:15-28,193-195` (`mode=ro` + `_pragma=query_only(1)`) e a regra de `:28` | 404 → 200 com `urn` + `corpo_sha256`; **e `socialisolation` verde** |
| **A15** | **Guarda real para a fronteira do grafo** — **não existe** (`grep` = 0) | FK social→grafo reprova |
| **A16** | **JSON-LD `ClaimReview`**, com os **dois** pré-requisitos reais de §B.6 | publicação por **`deploy-binario-go`**, não `--ressemear` |
| **A17** | **Âncora + hash por bloco** e `/api/v1/trecho/{path}#{ancora}` | `fidelidade_test.go:60-90` já garante os H2 |
| **A18** | **`lote` ganha `tipo:"refutacao"`; Atom por tema ganha corpo completo + URN + link** | contrato de forma preservado |
| **A19** | **Seção `refutacao` em `content/social_policy.json`**, **sem** cotas duplicadas (refutação **é** publicação para `orcamento_diario.publicacoes` e `quarentena.posts_por_dia`; copiar 5 e 20 criaria a cópia que envelhece e ampliaria de graça a superfície do `DisallowUnknownFields`). Sobram `exige_fonte_normalizada`, `exige_citacao_resolvida`, `piso_de_corpo_em_caracteres` e `turnos_maximos_por_alegacao: 3` — **único** número de fonte externa, nomeada: L-MAD (arXiv 2607.09099), +7,6/+7,8 com modelo médio e **−7,35 com modelo fraco** | **ORDEM CORRIGIDA em §B.7.5** |
| **A20** | **Registrar códigos de juízo/abuso** em `PorCodigo`/`NoLexico` + **célula de contagem de avisos por peça** | a única perda conhecida fica **contável** |
| **A21** | **Purga na remoção** (B.7.0 linha 7) | tempo entre `decidida_em` e o **1º MISS medido na borda** |
| **A22** | **Paginar `temasNoSitemap`** ANTES de a 1ª sala encher | pool de 12 não satura com 11.039 linhas |
| **A23** | **Léxico `injecao_de_prompt` + quarentena EXISTENTE + FP test**; delimitador de conteúdo não confiável na gêmea de conteúdo de agente | §B.9 |
| **A24** | **Re-medir o custo unitário com corpo real** e publicar a série na tela de transparência | **p99 > 50 ms em `/redesocial/tema/` é P0**, não "conteúdo é maior" |
| **A25** | **Medir o custo real de um julgamento** (20 com tokens gravados); **`julgar_peca` com prioridade EXPLÍCITA** | vazão de `extrair_dispositivos` **não regride** |
| **A26** | **Experimento FP/FN** com a régua de §B.7.3, **dois** braços de controle | §B.7.3 |
| **A27** | **Gate de fluxo read-only** `tools/check-moderacao-de-juizo` | reprova peça publicada sem âncora; decisão sem fundamento (≥ 20 caracteres, `moderacao.go:100-110`); enum fora do vocabulário |
| **A28** | **Gate de coerência do link acervo → rede social** — **não existe** (`TestSuperficieDeAgenteSoAnunciaRotaViva` cobre `agentsurface.Servicos`, não o link do HTML) | **reprova por FLUXO** (entrada nova sem saída em N dias), **nunca** por "está enfileirado" |
| **A29** | **Cachear o negativo**: `proxy_cache_valid` para 404 escopado ao prefixo social, no arquivo **vivo** `ops/nginx/standalone/nginx.conf`. **Motivo MEDIDO:** 404 social devolve `Cache-Control: no-store` ⇒ **cada slug inexistente chega ao Go, sempre** | 2º pedido do mesmo slug **não** chega ao Go |
| **A30** | **Corrigir a promessa de "triagem humana"** (`mcp.go:365` + skill do agent-card). **DECISÃO: a descrição passa a dizer o que A11 torna verdade** — o relato entra na quarentena que `decisao_de_moderacao` lê. Descrever o mecanismo real é melhor que apagar a frase | descritor coerente + teste |

### B.7.3 TRILHA B — abre a escrita a agente externo (depende de contas)

| # | Passo | Prova |
|---|---|---|
| **B1** | **PORTÃO: ensaio da migração** sobre cópia `VACUUM INTO`, **nunca** sobre o vivo | **se reprovar, a Trilha B para e a Trilha A já entregou todo o valor** |
| **B2** | `contas` 1→2, com `Migra` que **saiba migrar** (`esquema.go:66` hoje **só sabe confirmar**) e `sql.NullString` nos 8 pontos, na ordem medida (`conta.go:167-175` **degrada com log, sem `log.Fatalf`**: a rede fica no ar, só rotas de conta dão 503) | migração idempotente sobre cópia |
| **B3** | `socialpapeis.PapelAgente` — as 7 linhas | mutante `recebemCaso[PapelAgente]=true` morre |
| **B4** | Triggers de incompatibilidade — **na v4** (§B.2.3) | mutação |
| **B5** | Escopo `redesocial:escrever`, **incluindo `oauthserver.go:210`**, e a premissa substituta **escrita** no doc | `relatos:escrever` **NÃO** autoriza escrita social |
| **B6** | Verificador RFC 9421 + `/.well-known/http-message-signatures-directory` (**404 medido**), com **cache por `kid`** e rebaixamento a T1 | vetor de assinatura conhecido |
| **B7** | Faixa oficial do **Amazonbot** (maior visitante de IA, 3.446 req/24 h, **zero arquivo** em `data/ops/bot_ip_ranges/`) + generalizar o rDNS de `identity.go:525`, hoje preso ao Google | teste |
| **B8** | Rotas `POST /api/v1/redesocial/agente/*` com Bearer + **cota por `client_id`, nunca por UA** + zona chaveada por conta + 429. **Escrita nasce `em_moderacao`** | nada de agente sai com selo de OAB |
| **B9** | Ferramenta MCP `refutar` — **POR ÚLTIMO, com a medição de §A.1.4 no próprio passo**: 48 chamadas externas em 9 dias, todas de censo, zero de assistente. **E a fronteira de processo:** MCP é servido pelo `cmd/server:8089`, o banco social é do `cmd/social:8091`, e `cmd/social` **não pode importar `internal/httpserver`** (`internal/checks/ingress_rota_anunciada_test.go:41-43`); o socket aceita **uma** origem sob **uma** chave HMAC (`interno.go:377` recusa `origem != "cerebro"`). **DECISÃO: segunda origem + segunda chave HMAC + coluna `autor_classe`** — reusa o socket, seu HMAC-antes-do-parse e seu ledger, em vez de criar store paralelo | teste de recusa sem escopo; **erro de agente nunca atribuível ao advogado** |

**A medição pré-registrada (A26).** N = **200** refutações por *stride* determinístico
sobre as 109 URNs com ≥ 100 ocorrências — **N, os 20 dos controles e os limiares de
5% / 10% são PRÉ-REGISTRADOS, não derivados de medição anterior**, e é isso que os
torna teste e não ajuste. Rótulo de verdade = veredito sustentado pela fonte,
conferido pelo verificador de corpus (A7), **nunca opinião**.

| Resultado | Veredito | Ação (pré-registrada) |
|---|---|---|
| FP > 5% | gate frouxo | elevar `exige_citacao_resolvida` a bloqueio **em todos os tipos** |
| FN > 10% | gate cego | alvo é o **detector novo por sujeito em `pecagate`**, nunca `hasNearbyNegation` |

**Dois controles positivos, ambos obrigatórios:** 20 peças com **promessa explícita**
reprovam 20/20; 20 peças com **citação fabricada mas bem-formada** reprovam 20/20.
**E o controle de FP roda sobre os QUATRO tipos de escrita social** — o predicado de
negação é **compartilhado**, não exclusivo da refutação.

### B.7.4 A divergência: por que o número agregado é inválido

`MEDIDO` sobre CDC art. 14, 233 acórdãos, **233 de 233 localizados no corpus**:

| família | negar | dar | dar **parcial** | não conhecer | sem casamento | n | reforma |
|---|---|---|---|---|---|---|---|
| **REsp puro** | 18 | 14 | **6** | 26 | **6** | 70 | **43,8%** (14/32) · **52,6%** (20/38) com parcial |
| **AgInt/AREsp/AgRg/EDcl** | 118 | 2 | **4** | 23 | **16** | 163 | **1,7%** (2/120) · **4,8%** (6/124) com parcial |

**Agregado: 11,1% — e não descreve nenhuma das duas populações.** A separação é
**requisito**: 43,8% contra 1,7% é **25,8×**.
*(Correção ao dossiê e a mim mesmo: os 2,5% circulados vinham de 3/121 antes de `dar`
e `dar_parcial` serem separados; com a separação medida são **2 de 120 = 1,7%**.
Declaro a deriva de 1 item em vez de repetir o número antigo.)*

Mais três coisas:
1. **A coluna "outro" fundia incompatíveis** — provimento **parcial** (reforma) e
   **falha de medição**. Separadas, `dar_parcial` vale **8,8 pontos** no REsp puro.
2. **O denominador vai no byte:** "reforma entre os julgados em que o mérito foi
   apreciado", nunca percentual solto.
3. **"Verificada contra corpus hasheado" é 71,2% derivada de modelo.** `MEDIDO`: das
   233 arestas, **166 (71,2%)** vêm de `extracoes_dispositivos.jsonl` e 67 (28,8%) do
   campo oficial `dispositivos_citados_urn`; e só **19,9% (12.002 de 60.359)** do
   corpus tem qualquer URN. O `sha256_conteudo` atesta o **texto**, nunca que ele
   cita o art. 14. ⇒ **A coluna `arestas.fonte` (já existe) entra no dossiê por item,
   e o índice sai em DUAS linhas: atestado pelo campo oficial como manchete,
   extração rotulado. Nunca um percentual fundido.**

**O alicerce que ninguém escora:** a atribuição das extrações tem **15,51%** dos itens
sem o número do artigo no próprio `texto_citado` e **19,0%** apoiados só na folga de
`NormaAtestadaNoTexto` (`triagem.go:195-230`, que testa a norma no texto **inteiro**).
São **102.771 arestas `cita` = 26,1% do grafo**, e sobre elas se apoiam o risco de
superação, a divergência e os Percursos. **Apertar a atribuição e separar, na
superfície, o atestado do inferido, é passo próprio e está nomeado aqui.**

### B.7.5 A ordem de implantação da política — as três frentes escreveram ao contrário

O precedente é literal (`docs/PRECEDENTES_DAS_ORDENS.md:316-325`, 2026-09-09): *"O
campo **saiu do disco**, o binário subiu (12:43) e **só então** o campo voltou"*, com
a regra: *"dado de configuração que o binário vivo não parseia só entra no disco **no
mesmo passo em que o binário novo sobe**."*

**"binário no disco → JSON → swap → restart" abre a janela exata do laço de boot:**
entre "JSON" e "swap", o binário **velho** está no ar com um JSON que ele rejeita
(`policy.go:284` `Load` + `:295` `DisallowUnknownFields`; `cmd/social/main.go:112`
`log.Fatalf`; unit com `Restart=always`). Qualquer restart nessa janela — crash, ou o
earlyoom que em 2026-09-08 já matou `llama-server` e os servidores MCP — vira **laço
de boot da rede social inteira**.

**Ordem correta, fechando as DUAS janelas:**
1. `Load` de **ensaio** contra o binário novo, antes de o JSON tocar o disco.
2. **Swap do binário** (`./tools/deploy-binario-go`).
3. **JSON** no disco.
4. `sudo -n systemctl restart wikijuridica-social`.
5. **A seção `refutacao` nasce OPCIONAL, com defaults no código** — senão um crash
   entre o swap e a escrita do JSON põe o binário **novo** sobre a política **velha**,
   com o mesmo `log.Fatalf`.

**Serialização geral:** passos que tocam Go vão sob `flock /tmp/opt-wiki-commit.lock`
com o índice **vazio** antes de pedir a vez; A1-A4b, A20-A29 e P0-P0c são leves e
concorrentes.

## B.8 As métricas, na camada certa

| Métrica | Hoje (MEDIDO) | Alvo | Camada |
|---|---|---|---|
| **Citabilidade social** | `/api/v1/citar` social = **404**; controle positivo **200 / 1.786 B / 15 campos** | 200 com **schema social nomeado** (`urn` + `corpo_sha256`), **não** os 15 do acervo | origem |
| **Salas com conteúdo** | **0 de 11.039** (`duvidas` 0, `respostas` 0, `comentarios_de_autoridade` 0, `posts_blog` 0, `perfis` 1, `perfis_advogado` 0) | > 0, cada uma entrando sozinha no `temas.xml` | disco |
| **Cobertura da refutação** | `texto_sha256` **não existe**; gêmea entrega hash de fonte em **0 de 40** | 100% **por construção** (TRAVA 2) — prova que a trava está viva, não descobre se está | disco |
| **Retorno ≥ 2 dias por (agente, tema)** | amazonbot **3.050/4.345 = 70,2%** · perplexitybot 1,8% · yandexbot 8,9% · **gptbot 0/9.065** · **oai-searchbot 0/2.098** · **applebot 0/477** · semrushbot 0/10.237 | **oai-searchbot OU applebot ≥ 10% sobre ≥ 200 temas** — nomeados de propósito, para que um 2º **varredor** não satisfaça o alvo | origem (travessia 98,7%) |
| **Agentes com hábito (≥ 10%)** | **1 de 13** | 3 de 13 | origem |
| **Cobertura de formato** | gptbot pediu os 3 formatos em **99,7%** dos temas e **nunca voltou**; amazonbot 66,0% e volta diariamente | separa **varredura** de **hábito** | origem |
| **Custo unitário com corpo real** | casca vazia de 1.287 B: p50 3 ms / p99 6 / máx 28 (n=8.363); dia 33,2 s | **p99 > 50 ms é P0** | origem |
| **Teto de purga** | **NÃO MEDIDO** | número + constante nomeada | API Cloudflare (GET) |
| **FP/FN do gate** | **nenhum número jamais produzido** | régua de §B.7.3, **dois** controles 20/20 | disco + gate |
| **Demanda não atendida** | **870 de 1.293** 404 de AI Crawler **verificado**, em **754 rotas**; resíduo 141 | 0 em ≥ 3 dias e ausente da fila — **gate reprova por FLUXO** | borda |
| **Arestas de divergência** | **0 de 393.081** (`revoga` = 2) | 1º não-zero — **e entram como ENTRADA do gerador** (§B.2.4) | disco |
| **Coerência de superfície** | **15 / 14 / 4** divergem | gate vermelho enquanto divergirem | borda + disco |
| **Escrita externa** | **0 de 0** | pode ficar em zero — é **veredito** (§B.10) | disco + borda |
| **Tempo até o MISS após remoção** | **não medido**; borda com `s-maxage=3600` e `HIT` | do `decidida_em` ao 1º MISS | borda |
| **`csp-report`** | **308/dia** com zero conteúdo social | **0 só para `blocked-uri` sob nosso controle** | disco |
| **Vazão de `extrair_dispositivos`** | **118,7/h**, 33.999 pendentes = **286 h ≈ 11,9 dias** | **não regride** com `julgar_peca` na fila | disco |

## B.9 Os riscos e as defesas

| Risco | Defesa, e por que é estrutural |
|---|---|
| **Injeção de prompt em conteúdo publicado** | A Moltbook mediu **2,6% dos posts com injeção**, 1,5 M de tokens vazados, 92,9% dos agentes nunca verificados. **A defesa real é estrutural:** conteúdo entra como **dado delimitado**, a saída do moderador é **enum validado deterministicamente**, e a **monotonicidade** impede que injeção vire aprovação. Léxico + quarentena são **segunda** camada, com FP test. **`A MEDIR`: não medi a taxa no NOSSO tráfego** — o léxico nasce sem base própria |
| **Spam de agente** | Cota **por `client_id` E global** (50 + 500), porque só por cliente é contornável registrando 20 clientes; `CotaDiariaDeRegistro=20` fecha o laço. Quarentena viva. Zona chaveada por **conta**, não por IP nem UA. 429 obrigatório |
| **Envenenamento do moderador** | JUÍZO **não pode não-publicar** — só ordena. Moderador envenenado degrada a **ordem**, nunca a **existência**. **Fraqueza consciente:** o julgador é auditado por léxico, e léxico tem ponto cego — a mesma classe de `hasNearbyNegation`. Não tenho mitigação forte; tenho o registro e a série |
| **Risco de marca sob a assinatura da OAB** | **Quatro travas, nenhuma é revisão humana:** (1) separação de assinatura — nada de agente sai sob OAB/RJ 227191; (2) gate **antes** da escrita, já é código (`escrita.go:29-33`: *"fechar uma porta depois de ela ter sido usada não a fecha"*); (3) a norma alcança **PUBLICIDADE**, não conteúdo informativo (CED art. 39 exige caráter "meramente informativo" **da publicidade**; `habitualidade_modo: "auditoria"` já audita sem recusar); (4) bloqueia o **conteúdo**, não a frequência |
| **…e o vetor que essa regra abre, MEDIDO** | Se `oabgate` **não roda** para post de agente, qualquer texto que ele reprovaria é publicado ao se declarar agente — **e a superfície carrega `OAB/RJ 227191` 1× no HTML de 3.099 B medido em produção**. **Não invoco norma para travar conteúdo informativo. DECISÃO: rodar `oabgate` em TODO conteúdo como AVISO CONTÁVEL** na série de transparência (`PorCodigo`/`NoLexico`, que A20 já constrói), **nunca como bloqueio**. Descarto a alternativa de omitir a inscrição na página: ela mexe na identidade do template do portal para resolver um caso de conteúdo |
| **Vocabulário de veredito degenerar** | Os seis valores saíram de leitura própria, **não** de taxonomia publicada. Se juristas usarem uma sétima forma, o CHECK vira atrito e o campo degenera em "outro" + texto livre. **Auditável por contagem depois das primeiras 200 refutações** |
| **`ClaimReview` não renderizar rich result** | Confirmei que o tipo **existe** (200), **não** que renderiza para conteúdo jurídico. Se não renderizar, o JSON-LD **continua correto como dado para agente** — que é o produto pelo §12 — e perde-se só o ganho em SERP |
| **`--ressemear` errado na passada** | Irreversível em **efeito**. Uma passada, uma decisão de flag (§A.2.11), `--desde-commit` proibido nela |

## B.10 O que NÃO está verificado, com o teste que fecha cada lacuna

| # | Lacuna | Por que não foi medida | Teste que a fecha |
|---|---|---|---|
| 1 | **Teto de chamadas/hora da purga** | o repo documenta 100 URLs/chamada, não teto por hora | **P0c**. Se < 500/dia, a coalescência vira pré-requisito da **escrita** |
| 2 | **Custo unitário com corpo real** | o p50 de 3 ms serve casca **vazia de 1.287 B** — piso, não capacidade | **A24**, régua p99 > 50 ms = P0 |
| 3 | **Custo real de um julgamento** | 53–76 s é **estimativa**; a saída não foi medida | **A25**, 20 julgamentos |
| 4 | **Vazão sustentada de `gerar_comentario_autoridade`** | **o tipo NUNCA entrou na fila** (`select distinct tipo` = 3). O custo unitário **existe** para n=3 (4,80–5,28 tok/s); falta **comportamento em fila** | enfileirar N=20, medir s/peça e a vazão de `extrair_dispositivos` antes/depois |
| 5 | **Taxa de injeção no NOSSO tráfego** | a Moltbook mediu 2,6% no **dela**; não temos escrita para amostrar | 1ª leva, com contagem declarada |
| 6 | **A borda vaza a variante Markdown sob a URL HTML?** | só medi contra `127.0.0.1` | sonda pela borda com `Accept` variando; se vazar, um humano recebe Markdown por 7 dias |
| 7 | **Os ZIPs do STJ cobrem meses que o `.json` não cobre?** | exigiria saída ao STJ sob Crawl-Delay numa sessão somente-leitura. `dataset.go:32-34` **alega** que são o mesmo conteúdo, e comentário é alegação (R1) | 1 HEAD + 1 GET a um ZIP, janela declarada |
| 8 | **Janela por mês dos 6 datasets ausentes** | não medida — por isso L5 é "80 medidos + 6 × N" | GET ao índice de cada dataset, como fiz com a 2ª Seção (52 recursos, 20220531..20260831) |
| 9 | **A causa da CSP que o Applebot relata** | 243/dia de `script-src-elem`, origem = a nossa, e o nosso script **não** é o bloqueado (hash confere byte a byte, borda idêntica à origem, os 4 injetores da Cloudflare off). **45% do orçamento do Applebot** se gasta nisso, e `cmd/social/cspreport.go` **descarta o caminho por desenho** | **DECISÃO: gravar o caminho num campo agregado (sem PII)** — sem ele a causa é ininvestigável do disco. Os 308/dia ficam como linha de base **até o campo existir** |
| 10 | **Atribuição fina das extrações** | 15,51% sem o artigo no `texto_citado`, 19,0% na folga de `NormaAtestadaNoTexto` — **102.771 arestas** dependem disso | separar, **na superfície**, atestado × inferido (`arestas.fonte` já existe); apertar a âncora com o descarte contado |
| 11 | **A GPU não está no host** | migração **iminente**, não presente. `k` medido **na própria placa**: 0,648/0,660 (contra 0,44 da 4090) — planejar pela banda subestima ~47%. Decode 17–23×, **prefill 74–130×**, e a carga é de prefill (**6.268.192 prompt tokens contra 985.671 eval = 6,36:1**) | tudo que dela depende está **DERIVADO**. **1º trabalho da GPU: as 3 `medir_modelo` pendentes** — são elas que produzem os números com que o resto se decide. E o que a GPU **não** resolve: `buscar_semantico` a 8,98 s a frio é **carga de modelo** por `KeepAlive: "2m"` (`mcp_semantico.go:87`) — é parâmetro, e vale **antes** da GPU. A guarda de `internal/cerebro/saude.go` (teto de 9 GiB residentes) continua valendo |
| 12 | **Escrita externa pode legitimamente ficar em ZERO** | `MEDIDO`: toda a demanda é de **leitura**; os 48 tool-calls reais são **todos** de censo de diretório | **Veredito por EVENTO, não por calendário:** quando houver ≥ N `initialize` de UAs **não-censo** (N pré-registrado) com zero escritas, está provado que a Trilha B não tinha consumidor — **e isso é resultado, não falha de medição**. A Trilha A foi ordenada para que isso baste |
| 13 | **O corpus pode continuar monotemático depois de L5** | não medi a densidade mensal dos 6 ausentes | item 8 |
| 14 | **Ementa não é fundamentação** | `inteiro_teor` = **0 de 60.221** (e `inteiro_teor_url` também) | **nenhuma engenharia deste plano remove esse limite.** Refutação sobre ementa refuta o **resumo**, e isso sai **declarado no dossiê** |
| 15 | **O ranking que escolhe que salas encher** | sinal plano (máx 7 acessos entre 8.621 temas, 3.942 empatados em 1, desempate alfabético) e `agentesValiososParaRanking` contradiz a taxonomia canônica | **L10**. Enquanto não for derivado, a escolha de quais salas encher primeiro é **arbitrária** — degrada o retorno de A12/A13 sem invalidá-los |

---

## O QUE O ADVISOR MUDOU

Duas chamadas. A primeira, antes de escrever, dirigiu a ordem de verificação (medir
a atribuição do MCP antes de aceitar o número do crítico). A segunda, com o
documento já durável no disco, trouxe **onze apontamentos, quatro bloqueantes** —
e nenhum contradisse medição minha:

1. **BLOQUEANTE — sete decisões ficavam com o dono.** Eu escrevera "ou"/"e/ou" em
   sete pontos, o que viola "nenhum passo devolvendo decisão ao dono". **Fechei os
   sete, com o porquê e sem a alternativa:** vetor OAB → aviso contável (a série de
   A20 já existe; omitir a inscrição mexeria na identidade do template);
   `socialautoridade` → **v4** (a v3 tem dono declarado); crase → **alargar a cerca**
   (regra do CommonMark, nunca descarta dado); `ContentSHA256` → **pacote-folha**;
   `relatar_defeito` → **a descrição passa a descrever o mecanismo real**; escrita de
   agente → **2ª origem + 2ª chave HMAC + `autor_classe`**; CSP do Applebot →
   **gravar o caminho agregado**.
2. **BLOQUEANTE — A13 contradizia L1-Tempo-2.** Os dois blocos são derivados do
   corpus e mudam a cada acórdão; eu neutralizava um e tratava o outro como texto
   editorial, o que re-dataria 11.106 páginas a cada refresh — o **frescor
   fabricado** que o próprio neutralizador combate. **Unifiquei: ambos entram na
   tupla e saem na MESMA passada `--ressemear`, com L8/L9.** Isso dissolve o conflito
   C-1 por inteiro (os bots revalidam **uma** vez, não duas) e me obrigou a orçar
   bytes: **≤ 4.096 B para os dois, 32,2% da margem medida de 12.734 B**.
3. **BLOQUEANTE — a linha do agravo se contradizia.** Eu escrevera 2,5% ao lado de
   `dar 2, negar 118`: sem parcial são **2/120 = 1,7%**. Os 2,5% vinham de 3/121, de
   antes da separação. Corrigi e **declarei a deriva de 1 item** — senão a regra
   "denominador no byte" que escrevo duas linhas abaixo seria violada pela minha
   própria tabela.
4. **BLOQUEANTE — forma da entrega:** as duas seções saem **na íntegra** na resposta,
   com o arquivo durável como backup.
5. **Sete âncoras herdadas que eu não verificara** e que decidem ordem de passo: fui
   ao disco. Todas confirmadas (`tema.go:221`, `indexacao.go:498,530`,
   `websub.go:52-58`, `author_credential_test.go:39,43-44`, `api_citacoes.go:90-95`,
   `oabgate.go:599-602`, `cerebro/gate.go:251-265`) — **com uma correção minha**:
   `socialautoridade/esquema.go:208-215` **não** é um `RAISE(ABORT)` genérico de
   UPDATE; ele congela `perfil_id`/`autor_conta_id`/`tema_id`. O append-only vem da
   **ausência de método de edição** (`grep` = 0) **mais** esse trigger — reescrevi
   A12b com a razão certa.
6. **Dado medido que eu estava descartando sem dizer por quê.** Recuperei os três, e
   **um deles eu fechei medindo**: o "arquivo de 599 bytes com `}` sobrando" é
   `registros: 599` no mês `20220531` da **quarta-turma** — localizei no `cursor.json`
   e o defeito é **dataset abortado**. Também entraram os 2.902 agravos elegíveis /
   17.616 com ementa ≥ 250 (população de L7) e a busca clássica (440 impressões, 77
   cliques) marcada como **não sendo** a medida de citação.
7. **"Zero por 30 dias" era portão de calendário** — a mesma objeção que o Fable
   levantou contra outra frente. Reescrito **por evento**: ≥ N `initialize` de UAs
   não-censo com zero escritas.
8. **Achado novo que o advisor me fez nomear:** 22 dos tool-calls internos saem com a
   identidade **de saída** (`WikijuridicaBot`) contra a **nossa própria** superfície,
   sem `X-Warming-Request`. É "o portal mede o próprio eco" em carne e osso, e virou
   o passo **L0b**.
9. **L5 estava com piso falso:** "≥ 392" não pode ser piso se 6 dos datasets são
   `A MEDIR`. Passou a **"80 medidos + 6 × N, N A MEDIR; se N = 52, 392"**.
10. **A5 tinha pré-requisito não produzido por passo nenhum** — o piso derivado do
    HTML publicado. Virou o passo **A4b**.
11. **Rótulos:** renomeei os portões para `P0/P0b/P0c` (colidiam com as seções
    `B.1…B.10`); dobrei Escala em `B.7.0`, porque é ela que fixa a ordem dos passos,
    deixando métricas/riscos/não-verificado em 8/9/10 como pedido; corrigi
    "MEDIDO (a)" → "MEDIDO (A.1.5b)"; **declarei 102.771 × 104.002** para `cita` de
    extrações, como já fizera para `risco > 0` (3.481 × 2.711); e rotulei
    **N=200 / 20 / 5% / 10% como PRÉ-REGISTRADOS**, para não lerem como constantes
    redondas sem medição.
