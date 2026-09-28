# DUPPHRASE_DRAIN_SPEC_20260722 — Drenagem da fila duplicate_phrase (Cowork Fable 5)

Autor: `claude-cowork-fable`. Fontes: `data/ops/v2_dupphrase_analysis_20260721.jsonl` (452 linhas/385
páginas), `data/ops/v2_ingest_report.jsonl`, `internal/v2ingest/validate.go:987-1072`, commit `e9905e06`.

## Achado central: A FILA ESTÁ OBSOLETA — RERUN ANTES DE QUALQUER DRENAGEM MANUAL

Cronologia provada por git: `v2_ingest_report.jsonl` (16:59) e `v2_dupphrase_analysis` (19:01) são
ANTERIORES ao fix da exempção auditável de citação legal `e9905e06` (19:19, com teste de 152 linhas).
Nenhum rerun depois. Consequências:

- O número corrente real é **536 páginas** rejeitadas por duplicate_phrase no report (448 razão única),
  não 484; **151 nunca foram triadas** pela análise.
- A amostra adversarial (3 pares lidos lado a lado: familia-17×familia-01 art. 1.658 CC;
  consumidor-p1×consumidor-16 CDC art. 104-A §2º; bancario-inf1×bancario-09 DL 911/1969 art. 2º) deu
  **3/3 citação legal legítima pelo critério objetivo do código** — mas a análise antiga os rotulou em
  3 classes diferentes (`citacao_legal_legitima`, `near_dup_real`, `formula_gerador`). O campo `classe`
  do arquivo antigo NÃO é confiável.

## Spec de drenagem (ordem obrigatória)

1. **RERUN do ingest dry-run** sobre o merged atual → novo report + nova análise. Resolve sozinho
   ~282 casos (91 stale + 191 sem análise/indeterminados) e migra a maior parte para
   `duplicate_phrase_exempt_legal_citation`. Custo baixo (não é build Go).
2. **Classe citação legítima (estimados 190–260)**: zero-touch pós-rerun; auditar amostra de 10-15
   para confirmar âncora±20 tokens + ≤40 palavras + mesma norma nos dois `official_sources`.
3. **Classe fórmula-esqueleto real (70–110)**: fila de reescrita com variação da cláusula genérica
   preservando o fato jurídico e a citação — casar com o lote de molde (MOLD_ADJUDICATION_20260722).
4. **Classe duplicação genuína (10–25)**: leitura par a par; canônica fica, outra `superseded_by`
   por tombstone (DEC-020). Nunca as duas públicas.
5. Commit leve de dado a cada etapa (pathspec; não serializa build).

Estimativa de esforço poupado pelo rerun-primeiro: ~60-70% da fila se resolve sem redator.
