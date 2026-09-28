# LACUNA 3 — A ordem topologica da cadeia editorial (medido 2026-09-15)

## Veredito: GRAVE — e o perigo esta no OPOSTO do que o contrato aponta

O aviso do contrato (§1, "Regenerar derivado de `data/editorial/`", "~9 artefatos",
"31 dias parada", "`fingerprint mismatch`") descreve uma cadeia **real**, declarada e
com gate. Mas **nao e a cadeia que o P6 quebra.** Sao duas cadeias distintas, e o
implementador que ler o contrato literalmente vai regenerar a errada (40 passos,
teto duro de 600 s) sem tocar em nada que o P6 invalida.

- **Cadeia A — `authorial_mass_*`** (a dos 31 dias, ordenada por `mtime`, 13 elos):
  o P6 **nao a toca**. Medido: `grep -rl v2_pages internal/authorialmass*/
  cmd/generate-authorial-mass-*` = **0 arquivos**. CONTROLADO para o P6.
- **Cadeia B — a cadeia de publicacao v2** (ordenada por CAS/fingerprint e por
  **sequencia de runner**, nunca por `mtime`): e a que o P6 perturba, **nao esta
  declarada em documento nenhum**, e dois dos seus derivados estao stale AGORA.

---

## 1. Cadeia A — reconstruida e conferida hoje

`grep -rn "older_than" internal/ --include=*.go` devolve **exatamente 5** ocorrencias
hoje (2026-09-15), as mesmas 5 de 2026-09-08. `ModTime().After(` fora dessa familia:
so `internal/factorymetrics:652` e `internal/proc` (acham o mtime mais recente de uma
arvore, nao comparam derivado-vs-fonte). Em Python nao ha detector de ordem desta
cadeia (`getmtime`/`st_mtime` aparece em `tools/accessledger.py` e em 13 `test_*.py`).

Os 5 detectores, as 4 saidas que eles protegem:

| # | Funcao | Saida protegida |
|---|---|---|
| D1 | `authorialMassGlobalSimilarityFreshnessMessages` (`internal/checks/checks.go:12101`) | `authorial_mass_global_similarity_audit.jsonl` |
| D2 | `qualityVectorPersistedCurrentInputFreshnessIssues` (`internal/authorialmassqualityvectors/quality_vectors.go:430`) | `authorial_mass_editorial_quality_vectors.jsonl` |
| D3 | `refinementQualityArtifactFreshnessIssues` (`.../quality_vectors.go:984`) | `authorial_mass_refinement_quality_report.jsonl` |
| D4 | `globalSimilarityArtifactFreshnessIssues` (`.../quality_vectors.go:1029`) | `authorial_mass_global_similarity_audit.jsonl` (mesma de D1) |
| D5 | `readinessCurrentInputFreshnessIssues` (`internal/authorialmassreadiness/readiness.go:1059`) | `authorial_mass_publication_readiness.jsonl` |

**O DAG ja esta escrito e o gate dele passa.** `docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md`
traz o grafo e a ordem topologica em blocos legiveis por maquina
(`<!-- cadeia:ordem -->`, 13 elos com o comando de cada passo). Rodado agora:

```
./tools/check-cadeia-editorial-ordem-declarada
pass — 5 detector(es) older_than no codigo, todos declarados em docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md   (exit 0)
```

Ordem topologica (do doc, conferida contra os detectores): drafts → content_expansion
→ legal_signatures → contextual_compatibility → paid_intent_refinements →
similarity_report → signature_candidate_pairs → similarity_semantic_reviews →
refinement_quality_report → global_similarity_audit → editorial_quality_vectors →
signature_refinement_queue → publication_readiness.

### Estado AGORA: 11 de 11 derivados stale, e piorou desde 09-10

Fonte `authorial_mass_drafts.jsonl` = **2026-09-10 23:41** (era 09-08 21:06 na medicao
do doc de 09-10). mtimes medidos hoje:

| artefato | mtime | vs fonte |
|---|---|---|
| authorial_mass_drafts (FONTE) | 2026-09-10 23:41 | — |
| authorial_mass_content_expansion (FONTE) | 2026-07-06 19:03 | — |
| legal_signatures | 2026-09-05 20:43 | STALE |
| contextual_compatibility | 2026-08-05 19:37 | STALE |
| paid_intent_refinements | 2026-09-05 20:21 | STALE |
| similarity_report | 2026-06-30 20:56 | STALE |
| signature_candidate_pairs | 2026-09-05 20:49 | STALE |
| similarity_semantic_reviews | 2026-06-30 20:56 | STALE |
| refinement_quality_report | 2026-09-05 20:52 | STALE |
| global_similarity_audit | 2026-09-05 21:07 | STALE |
| editorial_quality_vectors | 2026-09-05 20:57 | STALE |
| signature_refinement_queue | 2026-09-05 21:04 | STALE (tambem vs `refined_public_prose.jsonl` = 09-10 23:18) |
| publication_readiness | 2026-08-05 19:38 | STALE |

**11 de 11 derivados atras da fonte.** Nao afeta pagina publicada: o doc de 09-10
mediu que os 38 artefatos da `bootstrap-chain` sao todos
`publication_allowed:false`/`render_allowed:false`/`noindex` e nenhum entra em
`public/`, sitemap ou `published_manifest`. **Nao e frente do P6.**

---

## 2. Cadeia B — a que o P6 quebra (nao declarada em lugar nenhum)

Derivada por leitura: `internal/v2publish/v2publish.go:179`
(`PagesGlob = "data/editorial/v2_pages/*.jsonl"`), `cmd/publish-v2-direct/main.go:89-94`
(`pages.json`, `published_manifest.jsonl`, `public/sitemaps`), `tools/run-daily-content`
(a sequencia viva) e `tools/deploy-publico` (os passos que so existem la).

```
        cmd/generate-acordao-pages  (P6, roda FORA da onda)
                    │
      ┌─────────────┴─────────────┐
      ▼                           ▼
data/editorial/portfolio_v2/   data/editorial/v2_pages/*.jsonl
      │  (intencao)                 │  (pagina)
      │                             │
      │   guarda: tools/check-shard-preservation         [onda 3/9]
      │   ORDEM DE COMMIT: portfolio PRIMEIRO ────────────┐
      └──> check-v2-portfolio-pairing (le o commit PAI) ──┘  depois v2_pages
                    │
      ┌─────────────┼──────────────────────────┬─────────────────────────┐
      ▼             ▼                          ▼                         ▼
generate-v2-    generate-page-content-   cmd/ingest-v2-stock       (nada mais
publication-    revision                 → contentstore +           depende do
severity        → data/ops/page_          data/editorial/            shard cru)
→ v2_publication content_revision.jsonl   stock_manifest.json
  _severity.jsonl  **ANTES do publish**   consumidores: internal/content,
                   (o publish le          internal/search, internal/publicrelease,
                    content_revised_at)   internal/scaleindex
                    │
                    ▼
        cmd/publish-v2-direct  (le o GLOB dos shards, nao o contentstore)
                    │
      ┌─────────────┼───────────────┬──────────────────┬─────────────────┐
      ▼             ▼               ▼                  ▼                 ▼
 public/**.html  public/sitemaps/ published_        content/pages.json  (public/index,
                 + sitemap.xml    manifest.jsonl          │              feed, rss)
                                                          │
                    ┌─────────────────────────────────────┼──────────────────┐
                    ▼                                     ▼                  ▼
        cmd/generate-legal-cocitation          cmd/generate-social-      tools/generate-
        → content/legal_cocitation_index.jsonl temas --aplicar           brotli-static
          LIDO UMA VEZ NO BOOT                 → banco social            → *.br
          (gemea .md, MCP, A2A, /api/v1/lote)    (/redesocial/tema/…)
                    │                                     │                  │
                    └──────────────┬──────────────────────┴──────────────────┘
                                   ▼
                    tools/reload-wiki-server   (o boot le o indice)
                                   ▼
                    generate-indexnow-incremental-submit
```

### O achado estrutural: a onda diaria JA publica por fora, e ja paga o preco

`tools/run-daily-content` (unit `wikijuridica-daily-content.timer`, 04:31) publica por
`cmd/publish-v2-direct` e **nao chama** `deploy-publico`. Medido por grep no arquivo:

| passo do `deploy-publico` | esta na onda diaria? |
|---|---|
| 0 — `ingest-v2-stock` (contentstore) | **NAO** (`grep -n ingest tools/run-daily-content` = 0 linhas) |
| 2.6 — `generate-legal-cocitation` | **NAO** (unico chamador no repo: `tools/deploy-publico:678`) |
| 2.7 — `generate-social-temas --aplicar` | **NAO** (unico chamador: `tools/deploy-publico:714`) |
| 2.5 — brotli | sim (8.5/9) |
| 5 — reload | sim (9/9, `reload-wiki-server`) |

**A janela do 2.6 existe na onda e ninguem colocou o passo nela.** O comentario do
`deploy-publico:652-676` fixa a restricao: o indice deriva de `content/pages.json`
(que o publish acaba de reescrever) e e lido **uma vez no BOOT**; entao tem de nascer
**depois do publish e antes do restart**. Na onda diaria essa janela e exatamente
**entre a etapa 8/9 (publish) e a 9/9 (`reload-wiki-server`)** — hoje ocupada apenas
por brotli (8.5), onda-avanca (8.6) e 7 gates (8.7). Custo do passo: ~16 s ocioso,
~29 s sob carga, linear no acervo (`legalcocitation.TestEnsaioSobreOAcervoReal`).

---

## 3. Medicao: os dois derivados stale AGORA, e o que ve cada um

mtimes (2026-09-15):

| artefato | mtime | fonte | atraso |
|---|---|---|---|
| `content/pages.json` | 09-15 12:28:56 | — | — |
| `data/editorial/published_manifest.jsonl` | 09-15 12:28:57 | — | — |
| `content/legal_cocitation_index.jsonl` | **09-11 03:08:12** | pages.json | **4 dias** |
| `data/editorial/stock_manifest.json` | **09-11 02:59:23** | shards | **4 dias**; 5 shards e 5 portfolios mais novos |

### 3a. Atribuicao EXATA (nao estimativa) do deficit do indice

`git show HEAD:data/editorial/published_manifest.jsonl` (commit `315ac61b`,
2026-09-10 17:06) contra o disco de agora:

```
manifesto em HEAD (2026-09-10 17:06) : 11.039 rotas
manifesto no disco (2026-09-15 12:28): 11.106 rotas   (M, nao commitado ha 5 dias)
ROTAS NOVAS desde o commit           :     67
  dessas SEM entrada no indice       :     67   ← 67 de 67 = 100%
  dessas COM entrada                 :      0
rotas que ja existiam em HEAD        : 11.039
  dessas sem entrada no indice       :  5.224   (47,3% — taxa-base do CRITERIO)
rotas removidas do manifesto         :      0
```

A taxa-base de 47,3% **nao e staleness**: o gerador so indexa pagina que esta no
`published_manifest`, tem corpo visivel e cita dispositivo com vizinha servivel
(`cmd/generate-legal-cocitation/main.go:63-105`). O deficit atribuivel a ordem e
**67 de 67 rotas novas (100%)**, e cresce ~a producao diaria da onda por dia.

Cobertura total: **5.815 de 11.106** rotas publicadas tem entrada (5.291 sem).
Integridade em repouso intacta: **0 de 31.102** destinos fora do manifesto, **0**
entradas orfas — `filtraPercursosServiveis` nao tem o que descartar. O modo de falha
**nao e link morto; e AUSENCIA silenciosa da secao** no canal que o §12 do contrato
declara ser o produto.

### 3b. O indice NAO TEM detector de frescor — provado por execucao

```
./tools/check-percursos-fundamento-legal
paginas=5815 links=31102 cross_area=24295 (78,1%) maior_atrator=40   EXIT=0  ← VERDE
```

O gate passa verde contra um indice 4 dias e 5.291 paginas atras do acervo. As reguas
dele (lidas no arquivo) sao anti-404 em repouso, auto-referencia, teto de atrator (40),
**unicidade** de fingerprint e piso cross-area (50%) — **nenhuma de cobertura,
nenhuma de frescor**.

E o `entrada_sha256` nao fecha essa porta: `internal/legalcocitation/artefato.go:162-167`
so compara os registros **entre si, dentro do mesmo arquivo** ("montado de duas
geracoes diferentes"). O comentario do campo (`:53-54`) afirma *"nao impede leitura de
artefato velho — impede que ela passe despercebida"*, e **essa promessa nao esta
implementada**: nada compara o fingerprint com o acervo vivo, entao a leitura de
artefato velho passa inteiramente despercebida. Precedente da memoria desta maquina:
*"guarda pela metade"* e *"instrumento pela metade mede a metade"*.

Agravante: o gate roda em runner nenhum — `grep` acha so
`internal/checks/crawl_recovery_gates.go:161` (case `percursos-fundamento-legal`) e o
proprio teste; **nao** esta na lista de 7 gates da etapa 8.7 da onda nem em
`run-qualidade-diaria`. E `check-cadeia-editorial-ordem-declarada` (o guarda da
Cadeia A) tambem e orfao: nenhum runner o chama.

### 3c. O espelho de temas: mesmo conjunto, e aqui o detector DISPARA

```
./tools/check-social-temas-espelhados
FALTANDO tema : 67      EXIT=1   ← VERMELHO
  /diarios/al-20260911/ -> /redesocial/tema/diarios/al-20260911/   (+57 outras)
```

**Exatamente as mesmas 67 rotas.** Dois derivados, o mesmo conjunto, um deles com
detector que reprova e outro cego — e o que reprova tambem nao esta em nenhum runner
da onda (so no passo 2.7 do deploy).

**Consequencia medida em trafego real** (`data/ops/access/nginx-2026-09-1[2-5].jsonl`,
status 404 em `/redesocial/tema/`): 54 + 11 + 16 + 7 = **88 requisicoes 404 em 4 dias**,
com YandexBot e SemrushBot entre os agentes. E o mesmo vazamento que o
`deploy-publico:698-704` registra de 2026-09-10: 898 paginas sem tema geraram **1.161
404 de bot em 10 dias (GPTBot 817, PerplexityBot 339, 817 caminhos distintos)**. O
passo 2.7 foi criado para fechar isso; publicar por fora do deploy **reabriu** o
vazamento.

### 3d. Corroboracao exata do P1b (frente irma), de graca nesta medicao

`approved_at = 2026-09-15` no manifesto: **944 paginas**. Rotas realmente novas desde
o ultimo commit: **67**. Logo **877 das 944 paginas carimbadas com a data de hoje nao
sao rotas novas** — ja existiam em `HEAD` (2026-09-10 17:06). E o
`-published-at HOJE` do fallback, medido por conjunto. O manifesto tambem confirma o
"M ha 5 dias": ultimo commit `315ac61b` 2026-09-10 17:06, com 11.039 rotas contra
11.106 no disco.

---

## 4. Resposta a "o que os docs dizem que ainda esta parado HOJE"

- `docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md` (09-08): declara o DAG dos 13 elos e
  **avisa em §0, em caixa alta, que essa cadeia NAO e a de `v2_pages`** — o achado que
  esta lacuna confirma por medicao independente (0 arquivos no grep). Diz tambem que
  `refined_public_prose.jsonl` e entrada externa (fronteira P4): hoje ela e **mais
  nova** (09-10 23:18) que o passo 12 (09-05 21:04), entao o elo 12 esta stale por
  dois caminhos.
- `docs/goal/CADEIA_EDITORIAL_PARADA_20260910.md`: 38 de 40 passos atras da fonte; a
  correcao **nao** e rodar `bootstrap-chain` (teto duro de 600 s em `:298`, recusa
  valor maior em `:302`, e passada parcial e **pior** que o estado uniforme atual);
  nada disso afeta pagina publicada. **Continua valido hoje**, e ficou 5 dias mais
  velho: 11 de 11 derivados stale, com a fonte avancada para 09-10 23:41.

Conclusao dos dois: a Cadeia A esta parada, documentada, com guarda de documentacao
verde, e **irrelevante para o P6**. O que nenhum dos dois documentos cobre — e que e
o risco real do P6 — e a Cadeia B.

---

## 5. A sequencia que o publicador autonomo TEM de executar

Ordem obrigatoria, com o motivo de cada posicao medido acima. Passos **novos** em
relacao ao que a onda diaria faz hoje estao marcados **[FALTA HOJE]**.

1. `./tools/check-shard-preservation` — antes de qualquer commit; a onda **para** aqui
   se o shard perdeu texto (`run-daily-content` 3/9).
2. `./tools/check-untracked-product-inventory` — produto untracked alem de 24 h.
3. `git add data/editorial/portfolio_v2` + `git commit -- data/editorial/portfolio_v2`
   — **o portfolio PRIMEIRO, em comando separado do add.** A autoridade de pertinencia
   e o commit **pai**, por desenho do gate.
4. `./tools/check-v2-portfolio-pairing` — **depois** do commit do portfolio, nunca
   antes (a onda registra que 4 tentativas queimaram um pre-commit cada por inverter).
5. `git add data/editorial/v2_pages` + `git commit -- data/editorial/v2_pages`.
6. `python3 tools/generate-v2-publication-severity --write` — censo.
7. `./tools/generate-page-content-revision` — **ANTES do publish**: o publish le
   `content_revised_at` para carimbar HTML, `<lastmod>` e `Last-Modified`; rodando
   depois, a data nova so alcanca o publico na onda seguinte.
8. **[FALTA HOJE]** `./tools/ingest-v2-stock` — se algum shard/portfolio estiver mais
   novo que `data/editorial/stock_manifest.json` (a condicao exata do
   `deploy-publico:~418`: `find data/editorial/v2_pages -name '*.jsonl' -newer
   data/editorial/stock_manifest.json -print -quit`). Hoje: **5 shards e 5 portfolios
   mais novos** — o backlog esta aberto. Nao e pre-requisito do `publish-v2-direct`
   (que le o glob direto), e **por isso** deriva calado; e pre-requisito de
   `internal/content`, `internal/search`, `internal/publicrelease`,
   `internal/scaleindex`.
9. `cmd/publish-v2-direct -allow-public-write` — escreve `public/`, `public/sitemaps/`,
   `published_manifest.jsonl` e `content/pages.json`. **Falha aqui = exit 2 e PARE**:
   recarregar o servidor depois de publicacao parcial deixa sitemap sem manifesto, o
   que aborta o boot com `Restart=always` e sem teto → laco infinito.
10. **[FALTA HOJE]** `./tools/go-modern run ./cmd/generate-legal-cocitation` — **a
    janela e aqui**: depois do passo 9 (precisa do `pages.json` e do
    `published_manifest` novos) e **antes** do passo 13 (o boot le o indice uma vez).
    Nao aborta: ausente ⇒ nenhuma secao; velho ⇒ `filtraPercursosServiveis` descarta
    destino nao-servivel.
11. **[FALTA HOJE]** `./tools/go-modern run ./cmd/generate-social-temas --aplicar` +
    `./tools/check-social-temas-espelhados` — antes do reload e **antes do IndexNow**:
    sem isto as paginas novas anunciam `/redesocial/tema/…` que devolve 404, e o
    portal manda o bot para o vazio (88 404 medidos em 4 dias; 1.161 em 10 dias no
    precedente de 09-10).
12. `./tools/generate-brotli-static --jobs 4` — depois do publish (senao `.br` velho
    ao lado de HTML novo, e a Cloudflare puxa a origem comprimida) e antes do IndexNow.
13. `./tools/reload-wiki-server` — o boot le o indice de co-citacao do passo 10.
14. `./tools/check-onda-avanca --depois --minimo 1` + os gates de resultado. **Incluir
    `check-percursos-fundamento-legal` e `check-social-temas-espelhados`** na lista
    (hoje a onda roda 7 gates e nenhum dos dois esta entre eles).
15. `python3 tools/generate-indexnow-incremental-submit` — exit real por
    `PIPESTATUS[0]`.

### Conserto de engenharia que falta, alem de ordenar os passos

O indice de co-citacao e o unico derivado desta cadeia **sem nenhum detector de
frescor**. O conserto que torna a ordem auto-verificavel (em vez de depender de
disciplina de runner): comparar `entrada_sha256` do artefato com o
`impressaoDoInsumo` do acervo vivo — o gerador ja calcula a funcao
(`cmd/generate-legal-cocitation/main.go:117,219-222`) e o artefato ja carrega o campo;
falta so o lado que compara, em `check-percursos-fundamento-legal`, mais um piso de
cobertura sobre as rotas do `published_manifest` que satisfazem o criterio. Isso cumpre
a promessa que o comentario de `artefato.go:53-54` ja faz e nao entrega.

---

## 6. O que NAO foi medido, e por que

- **`generate-legal-cocitation -ensaio`** (que daria "N paginas seriam indexadas HOJE",
  e portanto o deficit de staleness em uma medicao unica): **nao medido** — o
  classificador de permissao negou a execucao ("Irreversible Local Destruction"),
  apesar de a leitura do codigo provar que `-ensaio` retorna antes de
  `legalcocitation.Salvar` (`main.go:167-170`). Nao contornei. O deficit foi obtido por
  outra via, **exata e sem estimativa**: diferenca de conjunto entre o manifesto de
  `HEAD` e o do disco (67 de 67 rotas novas ausentes do indice).
- **Raio de acao exato de um contentstore stale** (busca interna, rotas dinamicas):
  **nao medido**. Levantei os consumidores por grep (`internal/content`,
  `internal/search`, `internal/publicrelease`, `internal/scaleindex`), mas nao medi o
  que degrada em cada um.
- **Atribuicao das 88 respostas 404 as 67 rotas especificas**: nao fiz o casamento
  caminho a caminho; medi o total de 404 em `/redesocial/tema/` por dia e o conjunto
  de 67 temas faltantes separadamente.

---

## 7. O que o advisor mudou

O advisor apontou tres pontos cegos que podiam derrubar o DAG. Remedi os tres; **o
DAG e o veredito GRAVE ficaram de pe**, e dois achados novos entraram.

**A — "`content.LoadRepository` le `pages.json` ou o contentstore?" (podia inverter
o DAG e escalar o veredito).** O advisor estava certo em desconfiar: eu havia inferido
"pages.json" pelo nome. Medido agora, `internal/content/content.go:855-884`
(`loadPages`) **PREFERE o contentstore** — se `content/page_index.jsonl` existir, ele
verifica a release e carrega os registros de la; `pages.json` e so o ramo **legado**.
E ele so cai no legado se **nenhum** artefato da release sharded existir. Conferido no
disco, os quatro estao **ausentes**:

```
content/page_index.jsonl             ausente
content/page_release_manifest.json   ausente
content/page_shards                  ausente
content/page_release_journal.jsonl   ausente
```

Logo o ramo legado esta ativo, **`content/pages.json` E a fonte, e o DAG do §2 fica
como esta**. A sonda funcional fecha a questao, com controle positivo (UA de sonda
propria + `X-Warming-Request: true`, pelo nginx em 8088):

| rota | HTTP | bytes | secao "Percursos por fundamento legal" |
|---|---|---|---|
| `/diarios/sp-20260912/index.md` (1 das 67 novas) | **200** | 9.785 | **0** |
| `/autonomos/b2b-escopo-alterado/index.md` (controle, esta no indice) | 200 | 12.122 | **1** |

O canal serve a rota nova (nao e 404 — o gatilho de escalada do advisor **nao**
disparou) e a secao **falta**. O instrumento funciona: no controle a secao aparece.
Confirma-se o modo de falha **ausencia silenciosa**, medido no canal servido e nao
so no artefato.

**Achado NOVO que isto produz (risco condicional, para o P9/P12):** o dia em que a
release sharded do contentstore for ativada, `loadPages` **troca de fonte** e o passo
8 (`ingest-v2-stock`) deixa de ser um ramo independente e passa a ser **pre-requisito
duro** do passo 10 e de o servidor servir qualquer coisa. Pior: `loadPages:866-884`
transforma release **parcial** (manifesto, journal ou diretorio de shards sem o
indice) em **erro de BOOT**, nao em fallback — com `Restart=always` e sem teto, e o
mesmo laco de reinicio que a onda diaria ja documenta. Quem ativar o contentstore tem
de mover o passo 8 para antes do 10 **no mesmo commit**.

**B — "`reload-wiki-server` reinicia de verdade, ou o passo 10 e inocuo?"** Medido:
`tools/reload-wiki-server:245` executa `sudo -n systemctl restart <SERVICO>` — restart
real, entao o boot roda e `carregaPercursosLegais` **rele** o indice. A dependencia
10 → 13 e valida; regenerar o indice antes do reload alcanca o publico na mesma
passada. (`--check` e read-only, pelo proprio docstring `:36`.)

**C — "o nome do shard novo esta em algum registry?"** Medido: **nao ha registry**. O
caminho e constante hardcoded em cada gerador — `cmd/generate-acordao-pages/main.go:70-71`
ja declara `data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` e o portfolio par.
Nenhuma allowlist de basename em `content/*.json` nem em `data/editorial/*.json`.
**Nao entra passo de registro na sequencia.**

**Achado NOVO que a checagem C produziu:** `tools/check-shard-preservation:145` monta a
lista de conferidos com `git ls-tree -r --name-only HEAD` — isto e, **so shards que ja
existem em HEAD**. O shard do P6 nunca existiu em HEAD, entao na **primeira** onda do
publicador autonomo ele **nao e conferido**: o passo 1 passa verde sem cobrir o unico
shard que a onda escreveu. A guarda vira efetiva a partir da segunda onda. Nao e
motivo para tirar o passo 1 da sequencia — e motivo para **nao confiar nele na estreia**
e conferir a contagem do shard novo a mao nessa primeira passada.
