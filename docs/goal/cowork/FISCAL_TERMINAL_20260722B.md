# FISCAL_TERMINAL_20260722B — red-team dos commits novos + resumo da onda

Autor: `claude-cowork-fable` (Cowork Fable 5, ciclo agendado ~11:30). Continuação do
`FISCAL_TERMINAL_20260722.md`. Escopo: commits do terminal posteriores à onda-4
(`ff5b9030`, `2bffdf6a`) + integração do censo pós-cutoff e do censo de corpus desta janela.

## 1. `ff5b9030` — guard DEC-020 + reportar-tudo + inventário re-pinado: **SÓLIDO** (aprovado)

Red-team adversarial (agente read-only, 18 tool-uses, evidência file:line). Refator **fail-closed**;
nenhum caminho deixa conteúdo ruim passar nem corrompe a fila. As 4 hipóteses de ataque falharam:

- **H1 — semântica do exit-code (acumular N defeitos):** SÓLIDO. `ops/relaunch-writing.sh:833-873`
  e `ops/relaunch-review.sh:369-397` envolvem o classificador por lote em `try/except SystemExit →
  batch_defects.append; continue`, e ao final `if batch_defects: raise SystemExit(1)`
  incondicional. Todo `raise SystemExit(<msg>)` original foi preservado (`:633-825`), todos com
  string truthy — não há `SystemExit(0)` que registre defeito como limpo. O gate de escrita
  (CAS re-auth + `target_sha256` por item, `:875-897`) só é alcançado com `batch_defects` vazio.
  Exceção não-SystemExit ainda propaga → exit≠0 (fail-closed).
- **H2 — autenticação de tombstone:** SÓLIDO. Linha skipped só é preservável se
  `skip_reason=="duplicate_intent_consolidated"` **e** `(superseded_by, iid) in winners` **e**
  `iid not in extra_seen`; qualquer outro caso `raise` (`generate_v2_review_queue.py:2907-2938`,
  espelho `:2434-2461`). `winners` re-deriva DEC-020 do zero com validação de arquivo SHA-pinada
  (`audit_v2_pages.py:24261-24346`); `superseded_by` é validado como basename do shard vencedor.
  Página legítima não é derrubada; tombstone duplicado → `valid_tombstone_not_unique` → fora dos
  winners. Nenhum tombstone fabricado passa sem archive confiável correspondente.
- **H3 — `writing-mass-full.js` inerte:** SÓLIDO. `throw` no topo (linha 10) após `const batches`
  não-exportado (só `meta` é exportado); os relaunch consomem o arquivo como **texto** via regex,
  nunca executam o JS. Executor real é o `writing-mass.js` separado. O commit editou só dado de
  inventário — sem divergência executável.
- **H4 — validação de source_kind/fonte oficial:** SÓLIDO (intacta). Os hunks ficam em
  `verify_staged_writing_source_resolution` e `classify_batch_completion`; `_CATALOG_SOURCE_KINDS`
  (`:1498`), `_canonical_official_source_url`, allowlist `gov.br/jus.br/leg.br/mp.br` (`:204`) e os
  checks de `official_sources` obrigatórios (`:2571-2759`) ficam **fora** do diff. Nenhum check
  enfraquecido.

**Fix executável:** nenhum necessário. Nit cosmético (não afeta o gate): o nome do manifesto
`relaunch_writing_defects_*` chaveia no mtime do `inventory_path`, não na data do run
(`relaunch-writing.sh:857`) — re-runs do mesmo inventário sobrescrevem o manifesto anterior.

`2bffdf6a` (163 preimagens raw-recovery + log de sorteio do red-team B): dado content-addressed,
baixo risco; não auditado linha a linha (blobs de recuperação, não conteúdo publicável).

## 2. Integração das outras entregas desta janela

- **Verificação viva pós-cutoff** (`data/source-audit/cowork_poscutoff_census_verificacao_20260722.md`):
  6 Leis 15.xxx novas + 4 LC + EC 131 + Tema 987 checadas ao vivo. **1 erro material**
  (crim-abandono-de-incapaz: atribuição do § 3º do art. 133 à Lei 15.163/2025). 3 cross-checks
  adversariais no estoque (LC 207 revogada / EC 131 nacionalidade / Tema 987 STF vs STJ cancelado)
  **todos limpos** — disciplina de fonte confirmada.
- **Censo de corpus** (`docs/goal/cowork/CORPUS_STUB_CENSUS_20260722.md`): GRAVE 1 é sistêmico —
  **67% do corpus são stubs <1KB**, CF e CP inteiros ausentes, códigos (CC/CPC/CDC/8.213/8.245)
  sombreados por stub apesar de haver full blob. Raio contido às 54 prosas quarentenadas. Fix:
  de-dup prefer-larger + gate blob<1KB reprova.

## 3. Veredito de promoção (não é veto — evidência)

Nada nesta janela bloqueia o **cohort-1** já aprovado (PROMOTE_REDTEAM_20260722 + B). Antes do
primeiro promote, aplicar na fila de revisão: (a) fix crim-abandono-de-incapaz; (b) manter a
quarentena das 54 prosas de entidade até o corpus ser saneado e o gate blob<1KB entrar.
