# Diagnóstico — por que o verdict N=209 dá 0 passed (2026-07-09)

Investigação a partir do verdict stale `scaled_content_release_verdict.jsonl`
(209/209 blocked) + censo de todos os oráculos + leitura do código do verdict.

## Achado central

O **verdict exige evidência de oráculo em modo RELEASE (full-corpus)**, mas o
`tools/bootstrap-chain` gera os oráculos em **modo AMOSTRA** (rápido, para
iteração). Mismatch estrutural: a cadeia produz o que o verdict rejeita.

- `generate-languagetool-quality` roda `deterministic_stride` (sample_limit=200,
  service_required=False). O verdict exige `full_corpus_over_refined_public_prose`
  + `service_required=true`. Existe `tools/generate-languagetool-quality-release`
  (full-corpus) — a cadeia precisa usá-lo para o run que fecha o verdict.
- `ptbr_text_shape` também tem variante `-release`.
- `ptbr_morphsyntax` é **sample oracle** sem variante release, e é **deep-check
  obrigatório mesmo no mass fan-in** (`qualityOracleDeepCheckRequiredForMassFanIn`
  retorna true). Precisa virar gate release full-corpus (ver abaixo).

## Manifesto e N

`stock_manifest.json`: drafts_expected=209, expansion_expected=0 → N esperado
= 209, e `refined_public_prose.jsonl` tem 209. Ou seja **N=209 é o corpus cheio**,
não um parcial de 632. `sourceRecords (209) >= required (209)` → caminho de mass
fan-in ativo; morphsyntax e ptbr_pair_rescoring rodam deep-check assim mesmo.

## Blockers do verdict — classificação

**STALE (somem no run fresco; já corrigidos ou regeneráveis):**
- `contextual_public_page_review_missing`, `missing_semantic_cluster_index` →
  regenerados (elos 25-26 verdes após fix de gate).
- `external_dedupe_oracle_*` (near_dup/mechanical/bucket/input_stale) → fix de
  gate feito (corpus limpo = aprovação); regen fresco zera.
- `ptbr_pair_rescoring / ptbr_text_shape ... _input_stale` → stale.
- `languagetool ... service_unavailable / fail_closed / error_present` → LT
  estava down quando gerou; :8082 está UP agora.

**REAIS — estruturais (engenharia):**
1. **languagetool release**: rodar `generate-languagetool-quality-release`
   (full-corpus, service_required) no run do verdict.
2. **morphsyntax**: virar gate release full-corpus com spaCy NER. Stanza 1.13.0
   não tem PT-NER oficial (documentado no script) — spaCy É o motor de NER e
   `detect_broken_legal_entity` já usa `spacy_entities`. Remover a exigência de
   Stanza-NER (impossível) sem perder a checagem de entidade quebrada.
3. **external_dedupe**: fix de gate feito; regen.

**REAIS — conteúdo (revisão/reescrita):**
- `languagetool blockers_present`: 123/200 páginas com gramática real
  (DOUBLE_PUNCTUATION 72, POR_QUE_PORQUE 71, MORFOLOGIK 66, etc.); 77 já limpas.
- `vale alerts_present / errors_present`.
- `language_gate ... dangling_connector` (truncamentos — reparos do censo cobrem).
- `public_prose_broad_official_source_url` (143) — fontes raiz/host (ex.: STF
  raiz em trab-contrato-intermitente; reparo trabalhista-13 cobre).
- `cta_contextual_required` (121), `oab_paid_intent_cta_blocked` (119),
  `page_antitemplate_recheck_required` (121), `public_prose_official_source_recheck_required` (176).

## Fora do escopo do verdict (não bloqueiam)

- `sca_scorecard`: `release_blocked=True` (score 8.9; Binary-Artifacts 9,
  Security-Policy 3 no modo local), **mas NÃO aparece nos blocking_reasons do
  verdict** (0 ocorrências). É gate de release-evidence separado. SECURITY.md
  enriquecido (melhoria genuína); calibração do gate `any check < 10` fica para
  quando/​se ele entrar no caminho crítico, com DEC.

## Plano de execução

1. Redesenhar oráculo morphsyntax → release full-corpus (spaCy NER; sem exigir
   Stanza-NER; status release-grade; bloqueia só em achado real de conteúdo).
2. Cadeia do verdict roda variantes `-release` (languagetool, text-shape) +
   morphsyntax full-corpus.
3. Reparos de conteúdo (censo, gramática LT, vale, broad_source, cta/paid-intent)
   — workflow de revisão/reescrita.
4. Run fresco → ler verdict verdadeiro → iterar no residual real.
