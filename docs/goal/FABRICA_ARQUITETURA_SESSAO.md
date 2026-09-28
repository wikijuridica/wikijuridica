# FABRICA_ARQUITETURA_SESSAO — arquitetura da fábrica jurídica de IA em escala

> Documento PERMANENTE de arquitetura, consolidado nesta sessão (2026-07-17).
> Fonte: o plano de arquitetura desta sessão (`~/.claude/plans/voc-o-engenheiro-modular-stream.md`,
> síntese das 14 frentes de pesquisa 2026) **ancorado ao estado REAL do repo** (git status +
> pacotes `internal/` inspecionados). Meta: 10k piso → milhões de páginas jurídicas únicas,
> indexáveis pelo Google e citáveis por bots de IA, com fiscalização de qualidade+ética 100%
> autônoma e algorítmica. Motor = Claude Code + frota de agentes Claude; **só open-source/in-house,
> zero SaaS/API paga**.
>
> **Estado honesto (não é fábrica rodando):** o motor abaixo é **scaffold determinístico + cola**,
> a maioria **untracked** (criado nesta sessão, ainda não committado). A **camada-IA é interface**
> (`ProseGenerator`, chamadas de revisor) — testável sem IA real, **ainda não ligada em produção**.
> Nenhuma página pública foi gerada/fiscalizada por este motor ainda (`published_manifest=0`).

---

## 0. Premissas vinculantes (do dono, nesta sessão)

1. **O motor é a IA orquestrada** — Claude Code + agentes Claude (Opus 4.8 / Sonnet / Haiku / Fable)
   em muitos streams paralelos. NÃO GPU, NÃO LLM local, NÃO OpenAI/API externa. Throughput = largura
   de paralelismo da orquestração.
2. **Só open-source (MIT/BSD/Apache) integrável no Go, ou construído in-house.** Técnica de terceiro =
   reimplementar, nunca depender de serviço.
3. **Fiscalização de qualidade+ética 100% autônoma e ALGORÍTMICA.** O dono não revisa nem por
   amostragem — é impossível ver milhões de páginas uma a uma. Fiscalização = algoritmo + sinal +
   amostragem estatística certificada + agente caro só no resíduo. Rafael Toledo (OAB/RJ 227191) é
   responsável LEGAL em nome, operacionalmente hands-off.
4. **Qualidade inegociável:** PT-BR natural não-robotizado, unicidade real anti-template, fonte oficial
   como proveniência (nunca corpo), ética OAB, HTML ≤50KB zero-JS.
5. **Ambição real: 10M+ em dias, não anos** — a arquitetura muda onde precisa, reaproveita o que presta,
   desativa o inescalável.
6. **Autonomia contínua, sem ociosidade.** Só se para em decisão exclusiva do dono (e diz qual).

---

## 1. Modelo mental (o que muda vs. hoje)

Hoje: `published_manifest=0`; a arquitetura transforma milhares de páginas produzidas (v2: **7.934**
páginas em ~445 shards) em **zero públicas**; build de 10+ min; auditoria longa; promoção big-bang.
**O modelo nunca foi o gargalo — a arquitetura é.**

Novo: um **grafo de fábrica incremental content-addressed** onde (a) demanda/entidade define candidatos,
(b) a frota Claude gera em largura, (c) a fiscalização algorítmica em tiers aprova **sem ler tudo**,
(d) a promoção é por **cohort incremental**. O trabalho é **ligar + cortar + escalar**, não reescrever.

---

## 2. Como se chega a MILHÕES sem virar SPAM/doorway

Google 2026 (core update mar/2026) pune **volume-para-manipular sem valor adicionado**, não IA.
Doorway canônico = "serviço em [cidade]" (permutação que não muda a resposta). **Três corpora
genuinamente distintos somam milhões SEM doorway:**

1. **Intents de PERGUNTA do cidadão (~100k–300k defensável).** Eixos que mudam a *resposta*
   (documento × prazo × órgão × cenário fático × risco), podados pelo **teste contrafactual**.
   Localização/sinônimo como eixo = proibido.
2. **Páginas de ENTIDADE jurídica (o motor dos milhões).** Cada lei, artigo, súmula, Tema RG/repetitivo,
   conceito, instituto, procedimento é entidade distinta, ancorada em **URN LexML única** — como cada
   verbete da Wikipédia (7M+). É a via mais defensável (jurídico = YMYL, fonte oficial = E-E-A-T máximo).
3. **Variação jurisdicional REAL** (onde a lei de fato difere: tributo municipal, procedimento local),
   sob gate anti-doorway rigoroso.

**Regra de ouro:** *gerar largo pelos eixos/entidades, podar duro pelo contrafactual + unicidade + fonte.*
O nº de páginas publicáveis é sempre menor que o de candidatos — essa diferença É a qualidade.

---

## 3. Dados content-addressed — a chave da escala incremental

Revisões imutáveis (reuso `factorygraph`): `IntentRevision`, `PageRevision`, `LegalClaim`, `GateResult`,
`TaskKey=(node,subject,input_hash,gate_version)`, `ReleaseSnapshot`. Mudança de intent/fonte invalida
**só o subgrafo dependente**.

**★ Princípio O(fontes) ≠ O(páginas):** cada `LegalClaim`-átomo é verificado por entailment contra a
fonte oficial **UMA vez** (custo caro, O(nº claims/fontes)); as páginas são **compostas** de átomos já
verificados (custo O(páginas), barato). O átomo é o **briefing fact-checked do redator, NUNCA slot de
corpo** — slot = o template-substitution que o Google matou em mar/2026. Unicidade é **MEDIDA**
(MinHash/SimHash < 0,70, piso ≥30–40% miolo único), nunca presumida. **O recurso escasso é
demanda/entidade distinta real, não compute.**

---

## 4. As 14 frentes de pesquisa 2026 (síntese — nada descartado)

Cada frente tem relatório durável em `~/.claude/plans/voc-o-engenheiro-modular-stream-agent-<id>.md`.

1. **Mapa do repo** — reuso vs. descarte (§8 deste doc).
2. **Google/pSEO/GEO 2026** — punição método-agnóstica; core update mar/2026; answer-first é gate editorial.
3. **Throughput** — largura de paralelismo de agentes; a parede real é *intents distintos*, não tokens.
4. **Revisão Claude-julga-Claude** — independência engenheirada; gerador ≠ revisor; oráculo externo (a lei).
5. **Demanda** — 2 famílias independentes; DataJud/Senacon/INSS; teto ~100k–300k intents-pergunta.
6. **Grounding fonte BR** — URN LexML; 3 eixos de vigência; canais de máquina que contornam o WAF gov.br.
7. **Indexação/schema** — FAQ-rich-result morto 07/05/2026; `Legislation`+URN; gate anti-órfã.
8. **Arquitetura de referência** — O(fontes) ≠ O(páginas); átomo = briefing, nunca slot.
9. **Loop de qualidade / honestidade dura** — verbatim ~100% em Go; semântico com teto ~77%; controles negativos.
10. **Ética OAB** — lícito na origem (Prov. 205/2021 arts. 1º/4º); policy-pack de 14 regras; mitigação ≠ imunidade.
11. **Embeddings-Go** — Model2Vec `potion-multilingual-128M` (MIT, 256-d, static embedding em Go puro, sem CGO/ONNX).
12. **Info-gain** — `internal/infogain`: regressão logística sobre sinais robust-scaled; léxico já no repo.
13. **Fiscalização algorítmica** — tiers T0–T4 + `qualitysampling` com bound RCPS/LTT certificado.
14. **Dedup 100M** — Bloom → MinHash-LSH (b=25, r=5, num_perm=125) → HNSW.

**Em voo:** corpus-oráculo de verificação (coleta + uso), integrado nas §5–§6.

---

## 5. O motor CONSTRUÍDO nesta sessão (estado real por pacote)

> **Legenda de estado:** `untracked` = criado nesta sessão, ainda não committado (`git status` = `??`);
> `staged` = adicionado (`A`); `interface-IA` = a camada-IA é interface para testabilidade, **não ligada
> em produção**. `fiscalizationtiers` documenta que os pacotes de fundação estavam como **código morto**
> (sem consumidor de produção) até esta cola existir.

### 5.1 Fiscalização em tiers T0–T4 (o coração — algoritmo, não leitura item-a-item)

Topologia universal (comprovada em Google SpamBrain, Wikipedia ORES/Automoderator, Meta): **sinal barato
em 100% → classificador em 100% → amostragem estatística com GARANTIA CERTIFICADA → agente caro só no
resíduo.** Cascata **fail-closed; abstenção = reprovação.** O bound distribution-free (RCPS/Learn-Then-Test)
certifica *P(taxa de má-aprovação residual ≤ 1%) ≥ 0,95*, e o tamanho de amostra **independe de N**
(~9.604 páginas para ±1% a 95%, seja 10k ou 10M). **Zero humano, com número.**

- **`internal/fiscalizationtiers`** (untracked) — a **cola** que liga numa cascata única as fundações que
  estavam isoladas: `internal/quality` (T0 sinais determinísticos), `internal/legalsignature`
  (T1 SimHash/MinHash), `internal/infogain` (ganho de informação robust-scaled), `internal/qualitysampling`
  (T2 calibração + bound estatístico). Três níveis, cada um mais caro e seletivo.
- **T0 — determinístico Go, µs/página, zero token, em 100%:** PT-BR (truncamento/conectivo/vocabulário
  interno vazando), ética OAB (regex A–E), HTML ≤50KB zero-JS, title/meta únicos, proveniência por claim,
  anti-doorway, sinais de qualidade. Reuso: `quality`, `checks`, pilha PT-BR, `paidintentgates`.
- **T1 — unicidade sub-linear em 100% (sem par-a-par), a 100M:** Bloom O(n) → MinHash+LSH-banding
  (b=25, r=5, num_perm=125) → SimHash+Hamming → embedding+HNSW só nos sobreviventes; sharding pela chave
  de bucket LSH; union-by-representative contra pior-caso template. Reuso: `v2pagedistinctness`,
  `v2bodysemanticdedup`, `legalsignature`. **Gap:** versão streaming/sharded do `checkDuplicates`.
- **T2 — classificador leve determinístico (100%) + amostragem CERTIFICADA:** logístico/GBDT (µs/página,
  zero LLM) sobre sinais contínuos; rótulos vêm do tier caro; re-treina com drift. `internal/qualitysampling`
  fixa cortes aprova/cinzenta/reprova com bound RCPS/LTT + Clopper-Pearson/Wilson + SPRT + ADWIN/KS. **É o
  gate estatístico que AUTORIZA a promoção do lote — sem humano.**
- **T3 — grounding contra o CORPUS-ORÁCULO** (§5.2 abaixo).
- **T4 — `internal/adversarialconsensus`** (untracked, interface-IA) — consenso adversarial assimétrico
  estilo FACTS sobre alto-risco/borderline. Agrega votos de **lentes diferentes** (refutador com
  *kill-mandate*, juiz com rubrica, escalador), decide fail-closed; revisores do mesmo tier têm piso de
  correlação (contam como 1 voto de tier — independência engenheirada). A lógica de voto/veto é Go
  determinístico; as chamadas Fable/Sonnet/Opus são camada-IA acima.

### 5.2 Grounding + corpus-oráculo (o que blinda "IA julga IA")

O juiz não é opinião de outra IA — é um leitor **preso a bytes externos**. A IA rotula, **o Go PROVA, a
lei decide.**

- **`internal/corpus`** (staged: `A`) — o corpus-oráculo: texto oficial content-addressed (chave URN,
  texto, hash, vigência `[início,fim]`, versionado). `Store` com `Get/ReadBlob/HasDispositivo/Records/
  VerifyBytes`. **NÃO é republicado** — o público usa só proveniência/autoral.
- **`internal/grounding`** (untracked) — recuperação = **união de 3 sinais** com fusão RRF:
  R1 URN-exato O(1) determinístico + R2 BM25 in-house (`bm25.go`) + R3 (Model2Vec static-Go). Arquivos:
  `adapter.go` (`CorpusOracle` liga `corpus.Store` à interface `OracleResolver` — re-resolve byte-a-byte
  e **prova** que o blob bate com `ContentSHA256`), `bm25.go`, `rrf.go`, `decompose.go` (claims atômicos),
  `cache.go` (cache O(fontes) ≠ O(páginas): átomo verificado uma vez, chave `claim_id` + `{DepURNs,
  DepHashes, Label}`; emenda invalida só páginas dependentes).
- **`internal/groundingcontrols`** (untracked) — controles negativos por construção
  (`controls.go`: ARTICLE_SWAP, NUMBER_PERTURB, NONEXISTENT, REVOKED, ANACHRONISM — rótulo garantido) +
  `leakguard.go` (anti-vazamento mecânico: maior corrida consecutiva de tokens vs. bytes oficiais). O gate
  só é válido no ciclo se reprovar 100% destes controles (**prova a fiação, não a cobertura** — a cobertura
  é do red-team, §5.5).
- **Guardas determinísticos O(1) ANTES da IA:** existência (art. 5000 numa lei de 300 → bloqueio),
  vigência/anacronismo (aritmética `@data [início,fim]`), número↔conteúdo.
- **Anti-vazamento tríplice:** físico (`internal/corpus/text` que `render` NÃO importa — import-graph test
  quebra o build) + contratual (prompt) + mecânico (leak-guard). **★ Gap:** o diretório físico
  `internal/corpus/text` e o import-graph test **ainda não existem** — isolamento é hoje lógico, o físico é
  planejado.

### 5.3 Geração de páginas de entidade (a via de escala)

- **`internal/entitycandidate`** (untracked) — modela cada ENTIDADE jurídica distinta como candidato de
  página; aplica o **anti-doorway determinístico ANTES** da redação/dedup (distinção pela entidade, não
  pela keyword). `EntityKind`; testes de rota e slug.
- **`internal/pagefactory`** (untracked, interface-IA) — orquestra o pipeline de UMA página:
  `entitycandidate` (anti-doorway) + camada-IA de redação (`ProseGenerator`, **interface**) + `answerfirst`
  (GEO) + `groundingcontrols` (leak-guard) + `grounding` (cada claim ancorado, nenhum CONTRADICTED). É a
  cola determinística; a IA é desacoplada para o pipeline ser testável sem chamar IA de verdade.
- **`internal/factorybatch`** (untracked) — produção EM LOTE: liga `entitycandidate` (candidato +
  anti-doorway + dedup por âncora + slug único) a `pagefactory` num funil determinístico fail-closed;
  contabiliza e separa `ApprovedPage` / `RejectedPage` (com razões nomeadas). Não reimplementa as camadas —
  só orquestra. **Aprovada aqui ≠ publicável** (falta dedup semântico/consenso/cohort).

### 5.4 GEO / answer-first / busca interna

- **`internal/answerfirst`** (untracked) — gate editorial answer-first: a página abre com parágrafo-resposta
  autossuficiente (40–60 palavras) + ≥1 heading em forma de pergunta. É gate de **conteúdo**, não markup
  (rich-result FAQ morreu 07/05/2026). Detecta conectivo pendurado (parágrafo não-autossuficiente).
- **`internal/sitesearch`** (untracked) — busca interna `/buscar/` (P1): indexa páginas publicadas, responde
  por relevância BM25 in-house (reusa `grounding`). **Contrato:** `/buscar/` e resultados são SEMPRE noindex
  e fora do sitemap (busca interna indexada = doorway).

### 5.5 Controle negativo permanente — DOIS canais (a distinção É a defensibilidade)

- **Canal 1 — fiação/regressão:** `groundingcontrols` (mutação determinística, rótulo por construção). Gate
  válido só se reprovar **100%** — mas é tautológico (prova a fiação).
- **Canal 2 — cobertura adversarial:** `internal/redteamcoverage` (untracked, interface-IA) — rastreia o
  **catch-rate** de um red-team **cego aos limiares** com missão inversa de EVADIR os detectores. É a métrica
  REAL (espera-se < 100%; rastreia-se a TENDÊNCIA — queda do catch-rate = gate ficando cego). Sem o canal 2,
  "100% catch" é circular. `EvasionAttempt.Caught`. O red-team em si é camada-IA.

### 5.6 Canais de coleta + enumeradores (contornar WAF só por canal de máquina, NUNCA por evasão)

Chave canônica = **URN LexML** (`urn:lex:br:...`). UA identificável, jamais bot falso; sem
utls/chromedp/TLS-spoof. Coleta **demand-driven** (coleta o que as páginas citam, nunca crawl cego).

- **`internal/lexmlenum`** (existente) — parser SRU/Dublin-Core do catálogo LexML (só PARSER: não acessa rede).
- **`internal/lexml`** (existente) — já extrai artigo/§ → URN.
- **`internal/entitycorpus`** (existente) — via de escala na ponta de ENUMERAÇÃO (leis/artigos/súmulas +
  precedentes); `Enumerate` só orquestra, não reimplementa.
- **`internal/entitycanonical` / `entityrender` / `entitysitemap`** (existentes) — URL canônica absoluta +
  render + sitemap das páginas de entidade.
- **`internal/planaltochannel`** (untracked) — decodifica e segmenta o HTML compilado do Planalto
  (ISO-8859-1/charmap) em registros. Load-bearing para o *texto compilado*; passo-zero = reachability probe
  do nosso egress.
- **`internal/dadosabertoschannel`** (untracked) — Senado/Câmara dados-abertos (`senado.go`, `camara.go`).
- **`internal/douinlabs`** (untracked) — parser do XML diário do DOU via INLABS (só PARSER; fail-closed em
  `<article>` sem `id`).
- **DataJud/CNJ** (APIKey pública; cobre STF/STJ/TST metadado num canal — ver
  `internal/codex2datajudobservations`). STJ portal `Disallow: /` → usar DataJud+DOU, nunca scraping
  não-compliant.

---

## 6. Ética OAB autônoma — lícito na origem; a pilha é mitigação, não imunidade

Marketing de conteúdo jurídico é **expressamente permitido** (Prov. CFOAB 205/2021, arts. 1º/4º). Nenhuma
norma exige revisão humana por página; o dever de veracidade é **por resultado, não por método**; a
responsabilidade do advogado é indelegável (Estatuto 8.906/94 art. 32). A pilha reduz risco real; o dono
responde pelo resíduo irredutível.

**Policy pack de 14 regras determinísticas** (gate Go, [NOMEADA]=proibição citável, [CG]=subsunção — nunca
fake-citar artigo): (A identidade) nome+OAB [CED 44], "especialista" só com título [Prov 3º,III], sem porte
[Prov 6º]. (B sobriedade) sem superlativo [Prov 3º,IV], sem promessa/êxito [Prov 6º/5º§3º], sem
preço/desconto [Prov 3º,I], sem urgência/medo [CG]. (C CTA — o mais crítico) bloquear
"contrate/processe agora/foi lesado?" [CED 46§único + Cartilha 2024]; permitir só CTA informativo + canal
contextual [Prov 4º§3º]. (D gratuidade) BPC/LOAS/assistência → **lane sem CTA comercial** [CG]. (E veracidade)
proveniência obrigatória por afirmação [Prov 1º§§1º-2º], sem vínculo a produto [Prov 8º], sem mala-direta
[CED 40,VI].

---

## 7. ★ Honestidade dura (inegociável)

O **verbatim/determinístico** (nº de lei/artigo, data/vigência, texto literal, citação) é provável **~100%
em Go**. O **semântico** ("a fonte sustenta a afirmação?" = misgrounding, o modo de falha dominante no
jurídico) tem verificador-IA com **teto ~77%** — logo **NÃO se atinge ~100% de recall**. Qualquer pipeline
que reporte "~100%/zero alucinação" é **gate relaxado/métrica inflada**. LLM jurídico cru alucina 69–88%;
RAG jurídico comercial ainda 15–34%. Desenho defensável = **fail-closed** (recall alto pagando precisão) +
oráculo externo (a lei) + controles negativos (2 canais) + re-verificação viva; **o OAB carrega o resíduo
irredutível LEGALMENTE.** Google julga por **padrão de site across várias páginas** (QRG set/2025) — por isso
anti-template (<0,70) + valor/E-E-A-T + fonte oficial são a defesa real (detectores de IA são não-confiáveis).

---

## 8. Mapa de REUSO vs. construir vs. descartar

**REUSAR (maduro/provado no repo):**
- **`internal/factorygraph`** — CAS idempotente + executor com slots `MaxWorkers/MaxModelWorkers/
  MaxNetworkWorkers`. Base do grafo content-addressed e da largura de paralelismo.
- **`internal/contentstore` + `scaleindex`** — storage/índice **provado a 1M** (O(n log n), não O(n²)).
- **`internal/v2pagedistinctness` + `v2bodysemanticdedup`** — dedup anti-all-pairs (base do T1).
- **`internal/publicrelease`** — publicação transacional; cohort já parcial (`P0ReleaseCohortMaxRecords`,
  preflight predecessor+sucessor, `public_release_promotion_cohort_delta_exceeded`). **Fronteira P4 a partir
  de `publicrelease.go:3379` é inviolável** (escalar ao especialista-crítico).
- **Pilha de gates:** `quality`, `checks`, PT-BR (`ptbrtext`/languagetool/vale/simplemma), `paidintentgates`.
- **`internal/qualitysampling`, `legalsignature`, `infogain`** — fundações estatísticas/de sinal que a cola
  `fiscalizationtiers` finalmente liga em produção.
- **`v2sourceprovenance` + `source_registry.json`, `structureddata`, `v2internallinkgraph`, `sitemap`,
  `v2ingest`** (transação com lock/journal/recovery), `demandevidence`/`demandsurfacecatalog`, `crawl_policy`.

**CONSTRUIR (lacunas remanescentes):** dedup sharded 10M streaming; schema `Legislation`+`legislationIdentifier`
=URN; `OutboundLinks()` no render + gate anti-órfã (`Orphans==0 && Danglers==0`); cliente IndexNow in-house;
Tier1 Model2Vec (embed-once no `coder/hnsw`); score info-gain calibrado; **diretório físico `internal/corpus/text`
+ import-graph test** (anti-vazamento físico); reaper de processo durável; conversor demanda→portfolio.

**DESATIVAR/SUBSTITUIR:** `internal/openaireview` (motor OpenAI/Batch errado → revisão por agente Claude);
os ~259 dev-mains fora do build quente (build-tag `//go:build devcmds`); bake-off de 4 motores de busca
(build tag `searchbench`); template composition (`authorialmasscontentexpansion` — já bloqueada, DEC-004/017);
big-bang de promoção; recompute full-corpus nos gates standalone; 246 always_run indiscriminado.

---

## 9. Sequência de execução P0 (destravar a fábrica)

Ordem crítica até `published_manifest > 0` e além:

0. **Reclamar memória** — parar Codex órfãos em loop; reaper de processo durável; enxugar LanguageTool
   (carrega 30+ idiomas, precisa só pt).
1. **Destravar build** — build-tag os ~259 dev-mains (`//go:build devcmds`); isolar bake-off pesado
   (`//go:build searchbench`); desinchar `cmd/check`; estreitar `block-heavy-go.sh` (não bloquear read-only).
   Perfis de gate `focused/delta-release/full-reconciliation` (reuso `checkselection`); **fix CAS**
   (store persistente, não tempdir descartado por commit).
2. **Fecho do v2** — fechar as 7.934 páginas v2 (reconciliar árvore por pathspec; docs/CLAUDE.md).
3. **Ingest** — `v2ingest` (transação com lock/journal/recovery).
4. **Verdict** — ligar `cmd/factory` autoritativo com a cascata de fiscalização em tiers (`fiscalizationtiers`
   + grounding contra corpus-oráculo); primeiro `verdict_passed > 0`.
5. **Cohort** — substituir o big-bang de 10.000 (`publicrelease.go:5069`) por cohorts de ~250:
   `before+approved_delta=after`, swap atômico de manifest/HTML/canonical/robots/sitemap, receipt com hashes,
   rollback como transação forward.
6. **Promote** — promover o 1º cohort das 7.934 → primeiro `published_manifest > 0`.
7. **Gap barato via fact-brief** — completar o resíduo pelas páginas de ENTIDADE (átomos já verificados =
   composição barata, O(páginas)), não por redação manual.

**P1–P5:** 100k → 1M → 10M por corpora de entidade; busca própria Bleve em `/buscar/` (`sitesearch`);
histórico/rollback; escala incremental. **Correção só para frente; red-team Fable antes de tocar
gate/hook/política/release; medir antes de mudar; nunca relaxar gate para passar.**

---

*Consolidado em 2026-07-17 a partir de `~/.claude/plans/voc-o-engenheiro-modular-stream.md` (14 frentes) +
inspeção do repo real. Estado do motor: scaffold determinístico + cola, camada-IA em interface, maioria
untracked, `published_manifest=0` — arquitetura desenhada e aterrada, fábrica ainda não em produção.*
