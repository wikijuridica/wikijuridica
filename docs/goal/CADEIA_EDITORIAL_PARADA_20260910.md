# A cadeia editorial está parada desde 2026-08-05 — medição de 2026-09-10

Este documento existe para que o próximo leitor **não trate isto como regressão
da leva de hoje**, e para que ninguém repita a investigação que o produziu.

O contrato (`CLAUDE.md`, §1, "Regenerar derivado de `data/editorial/`") registra
que essa mesma família já deixou a fábrica **31 dias parada**, e que o erro dela
nunca diz "ordem errada" — diz `fingerprint mismatch`. Ela voltou a parar. O que
segue é a medição, não a suspeita.

---

## 1. O que foi medido, e como

Para cada passo declarado em `tools/bootstrap-chain` (linhas 28-100), extraí a
saída que o wrapper escreve e comparei o `mtime` dela com o da fonte da cadeia:

```
FONTE  data/editorial/authorial_mass_drafts.jsonl        2026-09-08 21:06

authorial_mass_scale_shards.jsonl                        09-05 21:03  STALE
authorial_mass_legal_signatures.jsonl                    09-05 20:43  STALE
authorial_mass_signature_candidate_pairs.jsonl           09-05 20:49  STALE
authorial_mass_refinement_quality_report.jsonl           09-05 20:52  STALE
authorial_mass_global_similarity_audit.jsonl             09-05 21:07  STALE
authorial_mass_editorial_quality_vectors.jsonl           09-05 20:57  STALE
authorial_mass_contextual_compatibility.jsonl            08-05 19:37  STALE
authorial_mass_signature_refinement_queue.jsonl          09-05 21:04  STALE
authorial_mass_signature_shard_rewrite_plan.jsonl        09-05 21:05  STALE
authorial_mass_publication_readiness.jsonl               08-05 19:38  STALE
authorial_mass_legal_editorial_reviews.jsonl             08-05 19:39  STALE
public_prose_candidate.jsonl                             08-05 19:39  STALE
refined_public_prose.jsonl                               08-05 19:39  STALE
content_inventory_parquet_evidence.jsonl                 08-05 19:40  STALE
content_inventory_arrow_evidence.jsonl                   08-05 19:40  STALE
public_prose_language_patterns.jsonl                     08-05 19:40  STALE
languagetool_quality_evidence.jsonl                      08-30 17:02  STALE
vale_public_prose_lint_evidence.jsonl                    08-30 15:32  STALE
simplemma_ptbr_lemma_audit.jsonl                         08-05 19:54  STALE
ptbr_text_shape_release_evidence.jsonl                   08-30 15:09  STALE
ptbr_pair_rescoring_evidence.jsonl                       08-05 19:55  STALE
ptbr_wordfreq_quality_evidence.jsonl                     08-05 19:55  STALE
ptbr_ftfy_unicode_oracle_evidence.jsonl                  08-05 19:55  STALE
ptbr_lexical_diversity_evidence.jsonl                    08-05 19:56  STALE
ptbr_spellcheck_evidence.jsonl                           08-30 15:25  STALE
ptbr_morphsyntax_evidence.jsonl                          08-06 14:01  STALE
ptbr_confusables_evidence.jsonl                          08-06 14:01  STALE
ptbr_unicode_quality_evidence.jsonl                      08-06 14:01  STALE
sqlite_fts5_corpus_evidence.jsonl                        08-30 15:30  STALE
external_dedupe_oracle.jsonl                             08-06 14:01  STALE
semantic_cluster_index.jsonl                             09-05 21:07  STALE
authorial_mass_release_evidence.jsonl                    08-06 14:01  STALE
contextual_public_page_review.jsonl                      08-06 14:01  STALE
public_final_source_approval.jsonl                       08-06 14:01  STALE
authorial_mass_release_transaction_evidence.jsonl        08-06 14:01  STALE
authorial_mass_manifest_transaction_rehearsal.jsonl      09-09 13:57  ok
```

**Dos 40 passos, 38 estão para trás da fonte.** Onze deles carregam o carimbo
`08-05 19:38`–`19:40` — o mesmo minuto: foi a última execução completa da cadeia.

## 2. Por que ninguém viu

Cada gate acusa o **próprio** derivado, e nenhum acusa a cadeia. O vermelho sai
como `..._live_metrics_stale`, `..._input_fingerprint_mismatch`,
`..._stale_or_mismatch` — sempre em nome do artefato, nunca em nome da ordem.
Quem lê um deles vê um arquivo desatualizado; ninguém vê os 38.

É a mesma forma que o contrato já nomeia: *"o erro diz `fingerprint mismatch`,
nunca 'ordem errada'"*.

## 3. O que NÃO é a causa

**Não é o commit `6d3623c2` desta sessão.** Ele commitou `authorial_mass_drafts.jsonl`
com 7.985 linhas contra 7.972 em HEAD, e isso ficou visível como
`public_prose_candidate_count_mismatch: records=7959 expected=7985`. Três
medições separam o sintoma da causa:

1. O `mtime` da fonte é **2026-09-08 21:06**, e era o mesmo antes do commit — o
   arquivo já estava no disco; o commit registrou, não produziu.
2. O `expected` do gate é `len(inputs.Stock) − quarentena`
   (`internal/publicprosecandidate/public_prose_candidate.go:282`), isto é, os
   **drafts** — não o `drafts_expected` do `stock_manifest.json`. A divergência é
   7.985 − 7.959 = **26**, e só 13 vieram no commit: as outras **13 já estavam
   lá**.
3. Os 13 que entraram **não trazem página nova**: conferidos um a um contra o
   `published_manifest`, os 13 já estão publicados —
   `crim-assistente-de-acusacao`, `crim-como-processar-quem-me-ofendeu`,
   `crim-crime-acao-publica-ou-privada`, `crim-perdao-do-ofendido`,
   `crim-representar-prazo-decadencial`, `crim-vitima-discorda-do-arquivamento`,
   `fam-investigacao-paternidade`, `imob-area-menor-escritura`,
   `imob-certidao-onus-reais`, `imob-comprei-nao-registrei`,
   `imob-due-diligence-compra`, `imob-escritura-registro-matricula-diferenca`,
   `imob-retrovenda-verbete`.

## 4. O que isto NÃO afeta

**Nenhuma página publicada.** Os 38 artefatos são, sem exceção,
`publication_allowed: false`, `render_allowed: false`, `index_policy: noindex`, e
nenhum entra em `public/`, no sitemap ou no `published_manifest`. Buildar com eles
stale publica exatamente o mesmo byte que buildar com eles frescos; o que muda é
só o veredito dos gates que os leem — e esses estão vermelhos há 35 dias, não por
regressão de nenhuma leva recente.

Por isso a publicação de 2026-09-10 **não espera por esta cadeia**, e o hold que
esta sessão havia pedido à sessão par foi retirado com esta medição.

## 5. Por que a correção não é rodar `bootstrap-chain`

`tools/bootstrap-chain:298` fixa `P0_BOOTSTRAP_TOTAL_TIMEOUT_SECONDS` em **600 s**
e `:302` **recusa** valor maior, com a mensagem *"timeout nao e correcao de
performance"* — que está certa. Quarenta passos sobre 7.985 registros em 600 s é
parcial garantido.

**E parcial é pior que o estado de hoje.** Agora todo derivado está uniformemente
em 7.959: um estado limpo, descritível e comparável. Uma passada que morre no
meio deixa parte em 7.985 e parte em 7.959, e o mismatch passa a ser espalhado em
vez de uniforme — mais caro de diagnosticar do que a dívida que ele tentava pagar.

O caminho é o que a operação deste repo já registrou: **aquecer os produtores
fora da cadeia, medindo a parede de cada um, e usar a cadeia só para autenticar**
o que já está quente. Cada produtor aquecido é um passo que a cadeia encontra em
short-circuit por state key.

## 6. Ordem de ataque, quando esta frente for aberta

A ordem é a do próprio `tools/bootstrap-chain` e não se inventa: fase fria
acíclica (shards → assinaturas → pares → relatório de qualidade → similaridade
global → vetores → compatibilidade contextual → fila de refino → plano de
reescrita), depois readiness → revisão jurídica → candidato → refined, depois os
inventários colunares (o sidecar parquet é validado contra o `refined` VIVO;
regenerar o refined sem eles deixa o languagetool com `visible_text_mismatch`),
depois os oráculos PT-BR, e só então release → verdict → manifest.

**Preservar antes de escrever**: cada artefato anterior vai para
`.agents/runtime/` com data, pela regra do §8 do contrato — texto redigido foi
pago pelo dono.

## 7. Um gate cuja leitura muda por causa disto

`ptbr-spellcheck` reprova com `misspellings=824`. A evidência dele
(`data/ops/ptbr_spellcheck_evidence.jsonl`) declara `input_layer:
data/editorial/refined_public_prose.jsonl`, `checked_at: 2026-06-26` e
`publication_allowed: false`. Ou seja: ele reprova a publicação por ortografia de
um artefato que **nunca vai ao ar**, medido há 76 dias.

E o top-50 é dominado por sigla oficial brasileira (ATPV, CRLV, CDAs, CNAEs,
CNDs, CNHs, CPFs, Contran, Cetran, Confaz, Cosit, Cras, Creci, Cadastur,
CadÚnico, Capag, Cafir, Cepac, Cetip, Conare) e por estrangeirismo corrente
(Cold Calling, Churning, Coworking, Couvert, Cookie, Content, Business), contra
uma allowlist viva de **156 tokens** para 31.557 verificados. Antes de encostar
em dicionário, mede-se a ortografia do corpo **realmente publicado** — que é
outro arquivo.
