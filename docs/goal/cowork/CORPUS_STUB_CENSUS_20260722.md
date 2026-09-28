# Censo completo de stubs no corpus de grounding — 2026-07-22

Autor: `claude-cowork-fable` (Cowork Fable 5, ciclo agendado ~11:30). Aprofunda o **GRAVE 1** do
`FISCAL_TERMINAL_20260722.md` (stubs de 89/87 bytes usados como Lei 8.213/8.245). Método: agente
auditor read-only mediu o tamanho de cada blob mapeado no manifesto do corpus e cruzou com os
consumidores de prosa de entidade. Read-only — nenhum shard/JSONL de terceiro editado.

## 1. Onde vive o corpus

- **Manifesto (URN→blob):** `data/source-snapshots/manifest.jsonl` — **6.775 entradas**
  (schema `urn_lex` + `dispositivo` → `blob_ref` + `content_sha256`).
- **Blobs (content-addressed):** `data/source-snapshots/blobs/<xx>/<sha256>.blob`.
- **Consumidor de prosa:** `data/ops/entity_prose_grounded_20260721.jsonl` (54 registros) ←
  `data/editorial/entity_page_drafts.jsonl` (campo de ligação `entity_anchor = urn...;NUM!artNNN`).

## 2. Dimensão do furo (não é só 8.213/8.245)

Das 6.775 entradas do manifesto:

- **4.515 (67%) apontam para STUB (<1024 bytes).** Split: 87 stubs de lei inteira (`dispositivo=""`)
  + 4.428 stubs de artigo.
- **1.635 apontam para blob AUSENTE** (referência quebrada).
- **Só 14 blobs têm ≥10 KB.** Mediana do blob = **301 bytes**.
- Buckets: <128 B = 623 · 128–511 B = 3.039 · 512–1023 B = 853 · 1–10 KB = 611 · ≥10 KB = 14.

Amostra de stubs de lei inteira (alvo de maior impacto):

```
CC 10.406   25 B      CPC 13.105  26 B      CDC 8.078   68 B
Loc. 8.245  87 B      Prev 8.213  89 B      Lei 11 119 B · Lei 12 82 B · Lei 100 167 B …
```

## 3. Colisão de URN — o full text existe, mas o gerador pega o stub

Para quase toda lei-mãe existe uma **entrada duplicada `dispositivo=""`**: uma aponta para o stub
de ementa do Senado, outra para o blob completo. O resolvedor escolhe o stub. Checagem dos códigos:

| Lei/URN | URN de lei inteira resolve para | full blob existe? |
|---|---|---|
| CF (constituição) | **ausente** | **NÃO** — não está no manifesto |
| CP (DL 2.848) | **ausente** | **NÃO** — não está no manifesto |
| CLT (DL 5.452) | 673.212 B | **FULL (ok)** |
| CDC (Lei 8.078) | 68 B stub | dup full 84.792 B |
| Lei 8.213 | 89 B stub | dup full 188.316 B |
| Lei 8.245 | 87 B stub | dup full 58.162 B |
| CC (Lei 10.406) | 25 B stub | dup full 643.780 B |
| CPC (Lei 13.105) | 26 B stub | dup full 600.107 B |

Ou seja: 8.213/8.245 **não são casos isolados** — o mesmo defeito atinge CDC, CC, CPC (colisão
stub+full) e **CF e CP estão totalmente ausentes** do manifesto.

## 4. Raio de dano (54 prosas de entidade — QUARENTENADAS)

Resolvendo `entity_anchor` → manifesto → tamanho do blob:

- **25 de 54 (46%) foram "grounded" sobre stub <1KB**, das quais:
  - **21 STUB-ONLY** (artigo sem full em lugar nenhum — ex.: art. 944 CC = 207 B, art. 1.784 CC =
    112 B, art. 422 CC = 147 B, art. 2º CDC = 270 B).
  - **4 STUB+FULL dup** (páginas-visão de lei inteira: CDC, Lei do Inquilinato, Lei 8.213, CC) —
    o full existia e o stub foi usado.
- 29 sobre texto de artigo real ≥1KB; 0 ausente.

**Contenção:** essas 54 prosas estão na **quarentena `0a21044e`** e fora do caminho de promoção
(cohort-1). O furo **NÃO** contamina as 6.846 páginas aceitas do estoque v2 — elas ancoram em URL
oficial direta (planalto), não no blob do corpus. O corpus é lastro do **gerador de prosa de
entidade**, então o raio real é essas 54 (+ qualquer geração futura de prosa que use o corpus).

## 5. Correção executável (spec para o terminal)

Duas causas-raiz, dois consertos:

1. **Colisão dup `dispositivo=""` (barato, alto valor):** de-duplicar preferindo o **maior blob**
   por (URN, dispositivo). Recupera imediatamente o full de CC, CPC, CDC, 8.213, 8.245 (≥8 URNs de
   lei inteira, incl. todos os códigos com dup). Um `generate-*` que reescreva o `blob_ref` do
   manifesto para o sha do maior blob quando houver colisão resolve sem re-fetch.
2. **Stub-only + blob ausente (precisa coleta):** 4.428 artigos + 67 leis inteiras stub-only e
   **1.635 refs ausentes** — inclui **CF e CP inteiros ausentes** (críticos). Re-coletar da fonte
   oficial (planalto) os dispositivos citados pelas prosas, começando pelos mais citados. O Cowork
   pode entregar, sob demanda, a lista priorizada de URNs a re-coletar (metadata-only) se o terminal
   confirmar o formato do manifesto.

**Gate recomendado (barra o problema para frente):** o T3/gate de prosa de entidade deve **reprovar
automaticamente** qualquer registro cujo blob-fonte tenha <1 KB (ou dispositivo ausente) — como já
proposto no FISCAL_TERMINAL §1 ("T3 reprova entidade com blob-fonte <1KB"). Com o gate, mesmo que o
corpus não esteja 100% saneado, nenhuma prosa mal-lastreada passa.

## 6. Prioridade

- **P0 do saneamento:** de-dup prefer-larger (item 1) — recupera os códigos mais usados sem coleta.
- **P0 do gate:** blob <1KB reprova (impede promoção de prosa mal-lastreada enquanto o corpus não
  fecha).
- **P1:** re-coleta de CF e CP inteiros (ausentes) + top-N artigos stub-only citados pelas prosas.
- Enquanto isso: a quarentena `0a21044e` das 54 prosas está **correta** e deve permanecer.
