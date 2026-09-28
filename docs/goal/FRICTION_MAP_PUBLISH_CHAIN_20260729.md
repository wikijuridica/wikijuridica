# Mapa de atrito — cadeia b4→b6 até published_manifest > 0 (2026-07-29)

Autor: especialista-critico (Fable 5), Frente 4. Evidência medida em execução real
(repo vivo + bancada-clone `--shared` isolada em scratchpad; NENHUM gate afrouxado,
NENHUM dado do repo real editado na mão, nada commitado por esta frente).

## Estado de partida (medido 07:21)
- `data/editorial/v2_pages/`: 693 shards, 7.746 páginas vivas. `published_manifest.jsonl` = 0 linhas.
- LanguageTool :8082 vivo (HTTP 200). Load 1.07.
- `tools/ensure-audit-ready`: verde (rebuild=1, ~25s).

## Elo b4 — ingest-v2-stock: VERMELHO no repo real, causa-raiz PROVADA
`./tools/ingest-v2-stock --prepare-only` → exit 1 em 4,6s:
`validate v2 supersession integrity: issues=9 code=active_source_changed_without_provenance`
(subiu 2→9 durante a manhã: frentes concorrentes editando shards arquivados).

### Causa-raiz (família inteira, não caso a caso)
Gate: `internal/v2supersessionintegrity` — registro ativo listado num archive de
`data/editorial/v2_superseded/` não pode divergir do preimage autenticado sem
proveniência durável. Os 9 divergiram por edições UNCOMMITTED legítimas de duas
passadas concorrentes:
- 7 intents (portfolio_v2: glossario x4, familia, sucessoes, inpi): `source_hints`
  normalizados (frente `generate-v2-portfolio-hint-normalize`).
- 2 intents (v2_pages/glossario2-02:22 `gloss-dolo-eventual-culpa-consciente`,
  v2_pages/glossario2-19:4 `gloss-certidao-onus-reais`): `official_sources[].verified_at/http_status`
  gravados pela passada de verificação de fonte ao vivo de 2026-07-28.

O mecanismo `authenticatedCommittedForward` (git_committed_forward.go:174-192) só
deriva proveniência quando worktree == HEAD (byte-igual). Edição uncommitted nunca
autentica — fail-closed correto, não é bug.

### Prova (bancada-clone com delta editorial commitado)
- Commit simulado do delta de `data/editorial/` (1.118 arquivos): issues 9→2,
  committed_forwards 52→66. **Os 7 de portfolio destravam com o commit.**
- Os 2 de v2_pages NÃO destravam por commit: `committedForwardRecordEligible`
  (committed_forward.go:84) exige `index_policy=="noindex"` literal no registro, e o
  schema de página v2 não carrega `index_policy` → kind=page é SEMPRE inelegível a
  committed forward (desenho: página real exige canal revisado). Os 4 canais:
  - committed forward: inelegível (acima);
  - independent review: conjunto fechado em 81 rows (forward_evidence.go:585);
  - semantic recut unitário: `finalize-v2-semantic-recut --build-proposal` reprova
    "intent is not a contract requirement" (não estão na fila do contrato);
  - forward-candidates v3: plano devolve só os 16 candidates já registrados.
- Reposto o preimage BYTE-EXATO nos 2 (na bancada): issues=0
  (active_exact 26→28). `--prepare-only` no clone: **exit 0, 76,5s**, receipt:
  `files=693 portfolio_files=61 pages=7746 accepted=7436 rejected=310`.

### Destrave sancionado (decisão do maestro)
1. Commitar o delta editorial vivo (conteúdo, commit leve) — destrava 7/9.
2. Para os 2 de v2_pages: a PRÓPRIA frente da passada já os declarou "frente
   própria" e os deixou FORA do commit 3eae99b0 ("Eles precisam do forward de
   supersessão antes de pousar") — mas a escrita FICOU no worktree, e o audit do
   ingest é de WORKTREE: deixá-los fora do commit NÃO destrava b4. Rotas:
   (a) regravar o preimage byte-exato nos 2 via gerador sancionado (barata,
   PROVADA na bancada: issues 2→0; o verified_at deles está preservado no log da
   passada e refaz-se depois do forward pelo canal próprio); ou
   (b) completar o forward de supersessão (canal pleno: requirement no contrato
   semântico + finalize-v2-semantic-recut; hoje `--build-proposal` reprova
   "intent is not a contract requirement" — exigiria abrir requirement antes).
   Nota: para kind=page NUNCA há committed-forward por commit simples — o schema
   de página v2 não carrega `index_policy` e a elegibilidade exige o literal
   "noindex" (committed_forward.go:84). O canal de página é sempre revisado.
3. Fix de família nos escritores in-place de shard (ex.: passada de verificação):
   pular intents ativos listados em `v2_superseded/*.jsonl` e mandá-los para o canal
   de proveniência (14 linhas ativas hoje; conjunto pequeno e estável).

## Elo b5 — bootstrap-chain 12-31: VERMELHO por fotografia stale (consequência do b4)
`./tools/bootstrap-chain --from 12 --until 31` → exit 1 em 11,9s no preflight
`v2-stock-freshness`: 64 shards com `source record changed` vs fotografia canônica
de 2026-07-22 + `reconstructed terminal guards differ from receipt source snapshot`.
Mesma família: a fotografia realinha com o write-full do ingest pós-commit.
Veredito literal do wrapper: "estoque v2 ausente ou stale; valide sem escrita com
tools/ingest-v2-stock --prepare-only e, quando os shards estiverem estáveis, instale
a fotografia canônica com tools/ingest-v2-stock antes de regenerar a cadeia".

## Rejeições do ingest (backlog editorial das 310, por ocorrência)
missing_required_field=320, duplicate_phrase_with_page=146,
official_sources_insufficient=80, word_count_out_of_range=64,
intent_skipped_by_writer=64, declared_word_count_missing_or_invalid=64,
body_sections_below_stock_minimum=64, verified_at_invalid=27 (fila de verificação
pendente, não bug — validação exige parse+frescor+allowlist de status),
http_status_invalid=27, current_legal_fact_outcome_missing=25,
title_length_out_of_range=24, declared_word_count_incoherent=8.

## ATRITO CRÍTICO descoberto na bancada: write-full novo => cadeia recomeça em --from 1
Após instalar a fotografia nova (epoch muda, draft_records 7178→7436), o bootstrap
REPROVA `--from 12` com exit 125 e o veredito literal:
"bootstrap-chain: epoch/contrato de detox mudou ou está ausente; retomar em --from 12
confiaria em derivado stale. Recomece em: tools/bootstrap-chain --from 1".
Consequência: o plano de blocos 12-31/32-41/42 só vale se NÃO houver write-full novo.
Com estoque novo (haverá, pós-commit), a ordem real é `--from 1` — os derivados dos
passos 1-11 (shards de escala, assinaturas, similarity global, vetores, readiness,
legal reviews) são stale por definição. Medição dos passos 1-31 na bancada em curso.

## Elo b5 passo 4 — refinement-quality: VERMELHO por falso-negativo de família (FIX APLICADO)
Com estoque 7436, o passo 4 reprova 7 grupos-seed novos (agencia-reguladora,
clausula-nao-concorrencia, cobranca-apos-cancelamento, +4) com
`authorial_mass_refinement_quality_missing_similarity_evidence` +
`raw_adjusted_summary_invalid` (14 issues, 2 por seed).

Causa-raiz MEDIDA (não achismo): cada seed tem exatamente 2 páginas de lanes
distintas (91 duos no estoque novo; o antigo tinha 0), o par único É avaliado e a
similaridade REAL é 0.0 — reproduzido fora do Go: adm-agencia-reguladora (606
4-grams de tokens) × gloss-agencia-reguladora (355) → interseção 0, Jaccard 0.0.
O gerador só adiciona TopPair com rawScore>0 (refinement_quality.go, loop de
candidates) e o validador exigia MaxBodySimilarityScore>0 SEMPRE (linha 442) —
confundindo "medido e deu zero" (sucesso anti-template) com "não medido" (fraude).
Perverso: quanto mais dissimilar o conteúdo novo, mais a cadeia trava.

Fix de família aplicado em `internal/authorialmassrefinementquality/refinement_quality.go`
(ValidateRecords): ESPELHA o contrato do gate irmão `authorialmassglobalsimilarity`
(audit.go:790-792), que já trata score-zero como estado válido bilateral.
Controles que CONTINUAM reprovando (falso-verde impossível):
- não mediu: CandidatePairCount==0 / Evaluated!=Candidate / small_group_not_exact
  (linhas 416-431, intocadas);
- score>0 fabricado sem par nomeado/TopPairs → missing_similarity_evidence;
- evidência fantasma (score==0 com TopPairs ou par preenchido) → passa a reprovar
  EXPLICITAMENTE (controle novo, mais forte que o anterior);
- resumo incoerente (raw≠body, adjusted>raw, zeros mistos) → raw_adjusted_summary_invalid.
Teste focado do pacote: `ok portaljuridico/internal/authorialmassrefinementquality 0.893s`.
Blindagem adicionada em `internal/authorialmassrefinementquality/refinement_quality_zero_score_test.go`
(5 testes: zero medido coerente passa; TopPairs fantasma, par nomeado com zero,
resumo raw>0 com body 0 e score>0 sem TopPairs REPROVAM) — pacote verde em 2,3s.
Prova de fechamento na bancada: **passo 4 VERDE com o fix** — saída literal:
`authorial-mass-refinement-quality-report: reports=123 source_contents=7436
compared_pairs=298923 max_body_similarity=0.0566 publication=false` (22s).
O máximo global 0.0566 confirma estoque altamente dissimilar (limiar de risco 0.70).

AVISO pré-existente (independe do fix): `internal/contract/authorial/
authorial_mass_refinement_quality_test.go` já FALHA hoje contra o artefato vivo da
linha e5 (linha 106, SourceContentCount=590; e a linha 162 exige rollup==10000 do
v1 morto — impossível com v2). Resíduo v1 a atualizar quando a cadeia regenerar o
artefato com o estoque v2.

## Tempos medidos por passo (bancada, estoque 7436, load 3-8)
1 scale-shards 13s | 2 legal-signatures 34s | 3 candidate-pairs 15s |
4 refinement-quality 22s (com fix) | 5 global-similarity 16s | 6 quality-vectors 40s |
7 contextual-compat 15s | 8 refinement-queue 23s.
ATRITO passo 9 (signature-shard-rewrite-plan): declara budget_ms=300000 e o
run-heavy-throttled REBAIXA o timeout de 540s para 300s (run-heavy-throttled:620-629);
sob load 8-10 (frentes concorrentes) o passo estourou (exit 124, sem veredito).
Ação: rodar a cadeia em janela de load < 3-4 (ou serializar as frentes pesadas);
NÃO elevar budget — se o passo não couber em 300s com load normal e estoque 10k,
o fix é algorítmico no gerador (lentidão em 10k é bug P0).
Atrito derivado (acontece no repo real também): passo morto por timeout deixa
binário parcial `.build.*` + `build.lock` órfãos em `.cache/go-cmd-bin/<cmd>/`;
o próximo run falha exit 75 ("active build lock ... refusing passive sleep").
Correção: remover o diretório de cache do cmd afetado (build reproduzível) e
retomar com `--from N` — nunca retry cego.
Segunda dependência do passo 9: consome `data/research/demand_expansion_opportunities.jsonl`
e o HEAD está com schema ANTIGO (linha 1 sem `semantic_compatibility_family`, 30 keys,
18.228 linhas); o WORKTREE real já tem o regenerado (33 keys, 10.083 linhas, `M`
não-staged). Sem commitar data/research junto, o passo 9 reprova com
`demand_expansion_invalid_json: required field semantic_compatibility_family is absent`.
=> O commit do maestro deve cobrir o delta de `data/` INTEIRO (editorial + research +
ops), não apenas editorial.

BLOCKER REMANESCENTE DO PASSO 9 (dado real, provado na bancada com o worktree atual):
a regeneração de ontem (16:13) reduziu o expansion 18.228→10.083 SEM reconciliar os
artefatos irmãos — censo medido de referências órfãs (`exp-*` sem oportunidade viva):
- `demand_signal_observations.jsonl` (coletado, mtime 29/06): 2.049/5.858 órfãs;
- `demand_opportunity_priority.jsonl`: 354/1.255 órfãs;
- `demand_confirmation_state.jsonl`: 2.148/11.255 órfãs.
Veredito literal do passo 9: `demand_observation_dependency_failed:
observation_opportunity_missing: obs-000064056fff744fc6b9:exp-desconto-indevido-inss-
risco-golpe-outro-estado`. Fail-closed CORRETO — não relaxar. O elo é da frente de
demanda: fechar a migração regenerando/reconciliando os 3 irmãos contra o expansion
novo (produtores: cmd/collect-demand-observations, tools/generate-demand-priority,
tools/generate-demand-confirmation-state) ANTES do commit geral de `data/`. Ambos os
estados atuais reprovam o passo 9: HEAD por schema antigo, worktree por órfãs — não
há rota de commit que o contorne sem a reconciliação.

## Sequência exata para o maestro (ordem, com tempos medidos)
ORDEM IMPORTA: commitar TODO o delta de `data/` ANTES do write-full — qualquer
escrita em `data/` depois do ingest invalida os terminal guards da fotografia e o
preflight reprova (`v2_stock_freshness_terminal_evidence_invalid: reconstructed
terminal guards differ from receipt source snapshot`), mandando re-ingerir.
1. Pausar/serializar as passadas vivas que escrevem em `data/` (verificação de
   fonte, hint-normalize, recount) e commitar o delta COMPLETO de `data/`
   (editorial + research + ops; commit leve).
2. Resolver os 2 residuais de v2_pages (item "Destrave" acima) e commitar.
3. `./tools/ingest-v2-stock --prepare-only` (~76-95s; exigir exit 0).
4. `./tools/ingest-v2-stock` (write-full, ~172s, instala fotografia).
5. `./tools/bootstrap-chain --from 1 --until 31` (epoch novo => começa do 1;
   LanguageTool :8082 vivo — religar com `nohup ./tools/run-languagetool-local`;
   janela de load < 3-4).
6. `./tools/bootstrap-chain --from 32 --until 41`;
   `./tools/check-scaled-content-release-verdict --timings` (exigir verdict_passed>0).
7. `./tools/bootstrap-chain --from 42 --until 42` (manifest-transaction).
8. `./tools/run-promote-cohort-loop --target <N> --step 250 --dry-run` e, decisão
   do dono/maestro, `--execute` (promoção pública real, teto 250/transação).
   N = min(verdict_passed, alvo do ciclo); default do driver é 6846 e o hard-cap do
   loop é o marco P0 de 10.000. O driver relê o manifest vivo a cada passo
   (idempotente) e aborta se o manifest não avançar exatamente ao esperado.
   Dry-run VALIDADO na bancada (saída literal, target 500):
   `run-promote-cohort-loop: mode=dry-run target=500 step=250` →
   `tools/run-promote-authorial-mass-public-release --allow-public-write
   --expected-current-manifest-records=0 --expected-manifest-records=250` →
   `...=250 ...=500` → `done mode=dry-run steps=2 final_manifest=500`.
   Nada foi executado; a promoção real (--execute) é decisão do maestro/dono.

## Estado final da bancada (run definitivo, ordem commit→ingest→chain)
- ingest write-full: verde, accepted=7436 rejected=310 (3 execuções idênticas).
- bootstrap 1-8: VERDES — 6s/12s/6s/12s/10s/17s/7s/11s (load ~4,5).
- passo 4: verde com o fix (2 execuções pós-fix, determinístico).
- passo 9: VERMELHO por dado (família demand órfã acima) — cadeia para aqui até a
  frente de demanda reconciliar. 10-31 dependem linearmente do 9.
- b6 dry-run: validado (nenhuma escrita; comandos impressos corretos).

## Resultados da bancada-clone (continuação abaixo quando concluída)
- prepare-only: exit 0, 76,5s exec (135,5s CPU c/ build), accepted=7436 rejected=310.
- write-full: exit 0, 171,6s exec (177,3s CPU), fotografia instalada
  (drafts_expected 7178→7436, transação v2-rewrite-v5-9b6a6930...). Nota: 171s NÃO
  cabe no run_timeout de 300s com folga pequena sob load — rodar com load < 3.
  MEDIDO sob load ~6: o mesmo write-full levou 293,2s — passou a 7s do teto de
  300s do run-go-cmd-cached. Sob load alto o b4 ESTOURA o timeout: serializar as
  frentes pesadas antes de rodar o ingest é obrigatório, não cosmético.
