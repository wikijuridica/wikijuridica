# Brief de Demanda — Priorização de Ondas de Escrita (2026-07-22)

Subagente de pesquisa de demanda, sessão Cowork Fable 5. Análise metadata-only,
somente leitura, sobre o portfólio de intents e o estoque v2 atual. Objetivo:
priorizar as próximas ondas de `writing-mass` para fechar o gap rumo a 10.000
páginas públicas aprovadas.

## Números-chave

| Métrica | Valor |
|---|---|
| Portfólio total (intents únicos, 61 arquivos `data/editorial/portfolio_v2/*.jsonl`) | **10.041** |
| Estoque v2 (671 shards `data/editorial/v2_pages/*.jsonl`, intent_id por linha) | **7.702** intent_ids únicos (7.722 linhas; 65 tombstones `skipped:true` contam como slot preenchido) |
| Intents do portfólio **SEM página** no estoque (gap de escrita nova) | **2.345** |
| Intent_ids no estoque que não estão no portfólio atual (órfãos — legado/renomeado, não é ação deste brief) | 6 |
| Duplicatas de intent_id entre arquivos do portfólio | 0 (waves `-w3`/`-r0N` são disjuntas da base) |

**Reconciliação com o gap de ~3.2k da missão:** o gap de portfólio (2.345) é
menor que o gap declarado (~3.2k) porque parte da diferença está no lado da
**revisão**, não da escrita: dos 7.702 intent_ids já no estoque v2, a missão
reporta apenas ~6.8k "aceitas" no dry-run — ou seja, ~900 páginas já escritas
ainda não passam o gate de qualidade/fonte e formam fila de correção
(`ops/relaunch-review.sh`), separada da fila de escrita nova
(`ops/relaunch-writing.sh`) tratada aqui. Fechar os 10k exige as duas frentes:
2.345 páginas novas de portfólio + reaprovação da fila de revisão existente.

## Metodologia

1. **Portfólio**: 61 arquivos em `data/editorial/portfolio_v2/*.jsonl`, schema
   `{intent_id, page_type, practice_area, family, long_tail_query,
   working_title, reader_problem, lane, source_hints, needs_source_research,
   distinct_because}`. Dedupe por `intent_id` (primeira ocorrência).
2. **Estoque**: um único passe sobre os 671 shards de
   `data/editorial/v2_pages/*.jsonl`, extraindo `intent_id` por linha
   (convenção confirmada em `ops/relaunch-writing.sh`: tombstone
   `{"intent_id":..., "skipped": true}` conta como slot preenchido).
3. **Gap** = `portfolio_ids − stock_ids`.
4. **Ancoragem no corpus** (proxy): média de `cobertura_pct` por área em
   `data/ops/v2_corpus_coverage_map_20260721.jsonl` (commit `4f15979d`, 7.654
   páginas já mapeadas contra o oráculo local content-addressed
   `data/source-snapshots/` — manifest confirma 48 leis + 2 decretos + 67
   súmulas STF em blobs sha256). É proxy porque mede a qualidade de ancoragem
   das páginas **já escritas** na área, não dos intents ausentes
   especificamente — mas é o melhor sinal disponível sem escrever as páginas
   primeiro, e a hipótese (mesma área ⇒ normas semelhantes) é razoável dado
   que `distinct_because` do portfólio mostra intents da mesma família citando
   os mesmos diplomas-base.
5. **Score de priorização** = `0,45 × volume_normalizado + 0,30 ×
   cobertura_corpus_normalizada + 0,25 × prontidão`, onde prontidão = `1 −
   fração de needs_source_research=true` (fonte já resolvida no catálogo
   `v2_source_hint_catalog.json` = mais barato/rápido).

## Top 10 famílias (practice_area) para fechar o gap

| # | Família | Intents ausentes | Ancoragem corpus | Lane predominante | Lote sugerido |
|---|---|---|---|---|---|
| 1 | **consumidor** | 243 | sim (49,1%) | comercial 97% | 40–50/onda — maior bolsão único (`energia-solar` 22, `marketplace` 10); exigir sinal de contratação particular explícito no corpo, não só CTA (`paid_intent_blocked_cta_only_paid_signal`) |
| 2 | **glossario** | 182 | sim (54,5%) | informativa 100% | 60–80/onda — mais barato (93% já com source_hint resolvido) e zero risco de gate paid-intent/CTA; ATENÇÃO anti-template: formato verbete curto tende a repetir estrutura |
| 3 | **bancario** | 142 | sim (45,5%) | comercial 100% | 30–40/onda — `dividas` (19) e `tarifas-cobranca` (11) concentram volume |
| 4 | **empresarial** | 172 | parcial (31,4%) | comercial 91% | 25–30/onda — 61% `needs_source_research=true`, custo de pesquisa maior |
| 5 | **trabalhista** | 159 | parcial/baixa (24,7%) | comercial 89% | 30–35/onda — `rescisao-e-verbas` (22) concentra; dispositivos específicos da CLT ainda fora do oráculo (cobertura mais baixa do top 10) |
| 6 | **previdenciario** | 132 | sim (55,4%) | comercial 94% + bolsão informativa seguro (`auxilio-inclusao`/BPC, 6 intents 100% informativa) | 25–30/onda — `pensao-por-morte` (22) é requisito semântico já sinalizado no commit `5a40b63d` |
| 7 | **digital** | 102 | sim (50,8%) | comercial 100% | 25/onda — adjacente a LGPD, boa prontidão (61%) |
| 8 | **seguros** | 102 | sim — MAIOR ancoragem do portfólio (70,3%) | comercial 87% | 20/onda — ancoragem excelente uma vez escrito, mas 82% exige pesquisa nova (menor prontidão do top 10) |
| 9 | **saude** | 105 | sim (59,1%) | comercial 93% | 20–25/onda |
| 10 | **familia** | 108 | parcial (39,1%) | comercial 88% | 20–25/onda — `paternidade` (21) e `guarda` (14) concentram |

**Cobertura combinada do top 10:** 1.447 intents ausentes (~61,7% do gap de
2.345). Nenhuma família individual passa de 16,8% do lote top10 (consumidor) —
diversidade satisfeita, 10 áreas de prática distintas.

**Runners-up perto do corte** (não incluídos, mas monitorar): `lgpd` (57
ausentes, score 0,469 — quase empatado com o 10º), `criminal` (110 ausentes,
score 0,448 — famílias sensíveis `violencia-domestica`/`transito-criminal`, 22
cada, exigem reforço de tom ético OAB), `tributario` (95 ausentes, cobertura
baixa 19,0% — área de alta acurácia, modelo Opus recomendado por
`ops/relaunch-writing.sh`).

## Racional curto

- O score prioriza **volume real** (fecha o gap absoluto mais rápido),
  **ancoragem no corpus** (grounding barato: menos risco de o redator
  precisar "inventar" citação, mais fatos já verificados) e **prontidão**
  (source_hints já resolvidos no catálogo = menos pesquisa nova = ciclo mais
  curto por lote).
- **Lane não entrou como peso positivo no score** — a maior parte do gap é
  `comercial` (conteúdo de maior valor de negócio, correto priorizar). Lane
  foi tratado como sinal de **risco/velocidade de aprovação**: `glossario`
  (100% informativa) é o único bolsão do top 10 sem nenhum risco de gate
  paid-intent/CTA, e o bolsão `auxilio-inclusao` dentro de `previdenciario` (6
  intents, 100% informativa, ligado a BPC) é o exemplo concreto do padrão
  "BPC/LOAS/gratuidade = lane informativa sem CTA comercial" citado no
  contrato do projeto.

## 3 recomendações executáveis para o writing-mass

1. **Ordem das ondas**: abrir `glossario` (lote 60–80, baixo custo/risco) em
   paralelo com `consumidor` (lote 40–50, maior valor comercial). Isso
   maximiza páginas fechadas por ciclo de CPU/token logo nas primeiras ondas
   (quick win de volume) enquanto o lote comercial mais caro (mais
   `needs_source_research`) roda em paralelo.
2. **Tamanho de lote proporcional à prontidão, não fixo**: usar a fração
   `needs_source_research=false` de cada família como teto do lote por onda.
   Famílias com >80% `needs_source_research=true` (`previdenciario`,
   `seguros`) devem rodar lotes menores (20–25) com resolução de fonte prévia
   via `ops/relaunch-writing.sh` (catálogo `v2_source_hint_catalog.json`)
   antes de disparar a escrita; famílias com fonte já resolvida
   (`glossario`, `digital`) podem ir de lote maior (60–80).
3. **Riscos de molde por família**: `glossario` e `sumulas` (`page_type =
   verbete`) são as famílias com **maior risco de similaridade estrutural**
   (definição curta, forma repetitiva) — reforçar variação de ângulo/exemplo
   por lote e medir similaridade semântica < 0,70 antes de promover.
   Famílias comerciais de alto volume (`consumidor`, `bancario`, lane
   comercial >95%) precisam de auditoria extra de paid-intent-no-corpo (não
   só CTA). `criminal` (fora do top 10, mas com volume relevante:
   `violencia-domestica`/`transito-criminal`) exige reforço redobrado de tom
   OAB — sem promessa de resultado — por ser tema sensível.

---

**Fontes dos dados:** `data/editorial/portfolio_v2/*.jsonl` (61 arquivos,
10.041 intents únicos) · `data/editorial/v2_pages/*.jsonl` (671 shards, 7.702
intent_ids) · `data/ops/v2_corpus_coverage_map_20260721.jsonl` (commit
`4f15979d`, 7.654 páginas mapeadas) · `data/source-snapshots/manifest.jsonl`
(oráculo content-addressed: 48 leis + 2 decretos + 67 súmulas STF) ·
migração do inventário de escrita para intent_ids explícitos: commit
`5a40b63d`.

Gerado por subagente de pesquisa de demanda (Cowork Fable 5), 2026-07-22.
Análise 100% metadata-only/leitura — nenhum shard, código ou config foi
alterado.
