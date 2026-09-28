# Handoff — revisão das 11 worktrees do Codex (2026-07-28)

## 1. Contexto em 5 linhas

1. `/opt/wiki/.worktrees` tem 10 git worktrees (+1 em `~/.config/superpowers/worktrees/wiki`) criadas pelo agente **Codex**, desativado pelo dono em 2026-07-21; juntas ocupam **20 GB** (`du -sh /opt/wiki/.worktrees`).
2. Cada uma carrega trabalho **não commitado** (Go novo, testes, evidência JSONL) feito sobre bases de 2026-06-19 a 2026-07-03; o `main` de hoje é `42e29f88` (2026-07-28), ou seja **1005 a 1201 commits à frente** (`git rev-list --count <base>..HEAD`).
3. Todas as bases são **ancestrais do HEAD** (`git merge-base --is-ancestor` → sim para `1b098d1c`, `7d19da8b`, `df6450ba`, `3b7ae51f`, `bc585ad7`), então o repo não bifurcou: as worktrees apenas ficaram para trás.
4. Por isso o dono determinou **editar para frente**: um merge/cherry-pick de ~4 semanas de defasagem reintroduziria arquitetura morta (assinaturas antigas, gates com pisos stale, camadas de storage já removidas) e quebraria o que hoje compila e passa. `merge`, `cherry-pick`, `rebase`, `reset`, `checkout`, `restore`, `stash` são **proibidos por contrato** e há hook que bloqueia.
5. O trabalho já está preservado em `/home/rafael/.config/ai-terminal-backups/worktree-work-20260728-075936/<worktree>/` (2,3 MB no total) com `modificados.patch`, `untracked.lista`, `untracked/`, `base-commit.txt`, `branch.txt`. **Nada foi perdido, nada precisa ser resgatado.**

---

## 2. Veredito por worktree

Revisão concluída nas 11. **0 recomendações de integração sobreviveram à refutação adversarial; 0 foram derrubadas** — ou seja, o resultado não é "não deu tempo de analisar": as 11 foram analisadas e as 11 se provaram já integradas no `main`.

| worktree (branch) | o que faz | status no main | integrar? | esforço |
|---|---|---|---|---|
| `codex-p0-engineeringnow-missing-path-20260703` | Fecha buraco no gate `engineering-now-contract`: troca o skip de doc >2 MB por leitura em streaming (`bufio`) | já integrado — commit `0b5b1aa3` (2026-07-03) | **NÃO** | baixo |
| `codex-task2-public-prose-perf` | Inverted-index (postings) no lugar da varredura O(n²) de pares em `publicproselanguagepatterns` | já integrado — commit `e179403c` (2026-07-03) | **NÃO** | baixo |
| `codex-task4-workreuse-20260703093112` | Endurece anti-colisão do `work-reuse-ledger`: `running` só cobre processo vivo se tiver `artifact_claim` concreto | já integrado — commit `91f665b0` (2026-07-03) | **NÃO** | baixo |
| `codex2-p0-public-final-source-live-recheck` | Gate `public-final-source-live-recheck` sobre `public_final_page_rehearsal.jsonl` | já integrado e superado — pacote próprio `internal/publicfinalsourceliverecheck` (`5b71123f`, 2026-06-28) | **NÃO** | baixo |
| `codex384-legal-signature` | Protótipo de assinatura PT-BR (shingles, SimHash64, MinHash bottom-K) | já integrado e superado — `internal/legalsignature` canônico (`6f43bcc6`) | **NÃO** | baixo |
| `faraday-ptbr-text-shape-release` | Gate `ptbr-text-shape-release` (forma do texto PT-BR visível, uax29 + snowball) | já integrado — `9142bf84` (2026-06-30, 74 min após a base) | **NÃO** | baixo |
| `kepler-publicrelease-seooracles` | Liga `internal/seooracles` (parsers robots/sitemap) ao smoke do release transacional | já integrado e superado — `38e3087d` | **NÃO** | baixo |
| `linnaeus-roaring-postings` (`cycle-399-linnaeus-roaring-postings`) | Roaring Bitmap → índice de postings + check `roaring-postings-dedupe-evidence` | já integrado e superado — `9142bf84` + `ce5520ed` (2026-07-04) | **NÃO** | baixo |
| `lorentz-parquet-lt-399` | Sidecar Parquet do gate LanguageTool (`RequireScaleSidecar`, coordenadas de origem, hash de texto visível) | já integrado e superado — `9142bf84`, depois `bd382976`, `3ae4a8eb`, `b500f0c1` | **NÃO** | baixo |
| `p0-anchor-join-fix-20260627072738` | Corrige "anchor joins" mecânicos em `internal/refinedpublicprose` (+ probe do build pipeline) | já integrado — `157e86da` (2026-06-28); 538/539 funções presentes | **NÃO** | baixo |
| `ptolemy-ckan-oracle-cycle399` | Extrai parser CKAN para `internal/ckanmetadata` + gate `ckan-package-search-oracle` | já integrado byte-idêntico — `9142bf84` (2026-06-30) | **NÃO** | baixo |

---

## 3. Worktrees que VALEM integrar

**Nenhuma.** Esta seção existe vazia de propósito: não há trabalho pendente a portar, não há arquivo do `main` a editar por causa das worktrees.

O padrão que explica todas as 11: o Codex **commitava o trabalho no `main` por outra rota** (tipicamente no mesmo dia, às vezes 74 min depois da base) e a worktree ficava para trás segurando a cópia de staging não commitada. O que parecia "1000 commits de trabalho perdido" é, na verdade, **resíduo de staging de trabalho já entregue**. O valor desta revisão é exatamente esse veredito: ninguém precisa refazê-lo.

Se você foi acionado para "integrar as worktrees": **a integração correta é não fazer nada no código.** Vá para a seção 4 antes de duvidar disso, e para a seção 7 para o que fazer com o disco.

---

## 4. O que NÃO integrar, e a evidência

Regra geral que vale para as 11: **o risco não é perder trabalho, é reintroduzir trabalho velho.** Todo patch aqui é ancestral do código de hoje; aplicá-lo é regressão, não avanço. Em vários casos ele nem compila contra o `main`.

### 4.1 `codex-p0-engineeringnow-missing-path-20260703`
- Patch: 161 linhas, 6.676 bytes, 2 arquivos, 0 untracked.
- `grep -rn 'skipLargeCommandLedgerMaterialDeclarationScan' internal/ --include='*.go'` → **vazio**: a função que o patch removia já não existe (removida por `0b5b1aa3`, 2026-07-03).
- O `main` foi além: `materialArtifactDeclarationsFromFile` hoje tem assinatura `(root, relDoc, lineFilter, window)` com **3 retornos**; a do patch é `(root, relDoc)` com 2. Aplicar quebra a compilação em `internal/engineeringnowcontract/contract.go:560` e em ~14 call sites de teste, e apaga `lineFilter`, `materialEvidenceReadWindow` e `passiveMaterialIntegrationStatus` (features posteriores).
- O teste que o patch renomeia (`TestValidateRejectsLargeCommandLedgerMissingMaterialPathDespiteDeferredFields`) já existe byte-idêntico em `contract_test.go:150`.
- Gate continua vivo: `internal/checks/checks.go:1424` → `engineeringnowcontract.Validate`.

### 4.2 `codex-task2-public-prose-perf`
- Prova decisiva (read-only, não escreve nada): `git apply --check --reverse .../codex-task2-public-prose-perf/modificados.patch` **sai 0** — o patch já está aplicado no `main`, verbatim.
- Confirmado por grep: `shortSurfaceVocabularyCandidatePairs` presente em `internal/publicproselanguagepatterns/patterns.go` (2 ocorrências), além de `shortSurfaceWordCounts`, `shortSurfaceWordOverlapThreshold`, `minInt`.
- Reaplicar duplicaria `TestShortSurfaceVocabularyCandidatePairsPruneImpossibleBucketPairs` (`patterns_test.go:3640`) e `BenchmarkShortSurfaceVocabularyCandidatePairsLargeBucket` (`:4307`) → **redeclaração de símbolo → pacote de teste não compila**.
- Merge do branch arrastaria a versão de 2026-07-03 dos detectores, desfazendo 16 commits posteriores (DEC-017 anti-H1-molde, detectores em texto RAW com acento/pontuação).

### 4.3 `codex-task4-workreuse-20260703093112`
- 101 linhas, 3 hunks, 2 arquivos, 0 untracked. Os 3 hunks estão no `main` desde `91f665b0` (2026-07-03).
- `grep -n 'func recordHasConcreteArtifactClaimEvidence' internal/workreuseledger/ledger.go` → **`:6951`**, corpo byte-idêntico ao patch, com um segundo call site em `:7050`.
- O guard do `main` (`activeProcessCoveredByRunningLedger`, `:6930`) é **mais restritivo**: tem as 2 conjunções do patch **mais** `!ValidateRecordWithOptions(record, Options{Now: now}).Passed()`, e é pré-filtrado por `runningRecordCanCoverActiveCollision(record, now)` (`:6926`). Aplicar o patch **afrouxaria** o gate.
- `TestConcurrentCollisionRejectsDirectGenerateProcessWithMatchingRunningRecordButMissingDirectClaim` já existe em `ledger_test.go:4794`; readicionar duplica símbolo.

### 4.4 `codex2-p0-public-final-source-live-recheck`
- Base `7d19da8b`, **1201 commits atrás** (a maior defasagem do lote).
- O patch era função inline em `checks.go`. O `main` tem **pacote dedicado**: `internal/publicfinalsourceliverecheck/{recheck.go (42.560 B), recheck_test.go}`, criado em `5b71123f` (2026-06-28), com camada JSONL própria (452 registros), gerador `cmd/`, wrappers `tools/`, validação de storage e um segundo check derivado.
- Check registrado: `checks.go` Names `:491`, switch `:1794`, PassLine `:3655`, delegação em `:10003`.
- **Armadilha ativa**: o patch adiciona em `internal/storage/storage.go` uma cláusula exigindo `strings.Contains(layer.Description, "public_final_source_live_recheck")` na camada `public_final_page_rehearsal`. A descrição viva em `content/storage_contract.json` **não contém essa string** → aplicar reprova `cmd/check storage-contract` na hora com `public_final_page_rehearsal_missing_source_live_recheck_c…`. Quebra gate hoje verde.
- Pisos hardcoded do patch são stale: `MinimumPages=181` / `MinimumSources=21` contra o estoque real de hoje (360 rehearsals / 452 rechecks) — reintroduzi-los criaria gate que passa trivialmente (falsa cobertura).
- O helper `dedupeKnown()` do patch é redundante: `buildProfile` (`internal/checkselection/selection.go:1953`) já normaliza via `orderCheckDependencies` (`:2609`) → `uniqueSorted` (`:2628`).

### 4.5 `codex384-legal-signature`
- `modificados.patch` tem **0 bytes**: é 100% arquivo novo (`untracked.lista` = `internal/legalsignature/signature.go` + `signature_test.go`).
- O `main` criou o **mesmo caminho** depois da base: `git cat-file -e df6450ba:internal/legalsignature/signature.go` → *não existia*; `git log df6450ba..HEAD -- internal/legalsignature/signature.go` → `6f43bcc6`, `b49cd239`, `27531341`.
- Hoje `internal/legalsignature/` tem **9 arquivos** (inclui `cascade.go`, `streamdedup.go`) — superset do protótipo, com 15 pacotes não-teste consumindo a API.
- Sobrepor causaria: regressão de performance (sha256 no lugar de `xxhash64`/fasthash), **colisão de símbolo** com `func Signature` em `streamdedup.go:541`, e invalidação do cache de distinctness de todo o estoque (a constante `Algorithm` e o normalizador entram no fingerprint do `v2pagedistinctness`).

### 4.6 `faraday-ptbr-text-shape-release`
- Base `3b7ae51f` (2026-06-30 04:58), **1025 commits atrás**. O pacote entrou no `main` em `9142bf84` (2026-06-30 06:12) — **74 minutos depois**. A worktree é o canteiro de obra, não trabalho perdido.
- `git cat-file -e 3b7ae51f:internal/ptbrtextshaperelease/release.go` → não existia na base; `git log --diff-filter=A` confirma a criação em `9142bf84`, seguida de `3ed5907c`, `283ce765`, `51deef68`.
- Versão do `main` é superset (571 linhas vs 459 do patch): ganhou `schema_version`, `total_significant_word_count`, `scan_duration_ms`, `release_shape_ready`, `license_contents_stored`, `DefaultScannerBufferBytes=32MB` (o patch usa bufio default e **estoura em linha JSONL longa**) e `effectiveMinimumRecords()` acoplado a `authorialmassstock.EffectiveReleaseMinimum` por **DEC-014**.
- Registro completo já existe: `checks.go` L207 (import), L296 (Names), L1892-1893 (case), L5232, L5442; fan-in em `internal/scaledcontentreleaseverdict/verdict.go` L38/L146/L2672/L3023-3027/L3223/L4530; cobertura OSS em `internal/ossscaleintegration/coverage.go` L68/L281/L295/L510/L2289-2302/L2607-2637.
- **Não sobrescrever** `data/ops/ptbr_text_shape_release_evidence.jsonl`: o registro do patch é da era v1 (`input_records=10000`, `checked_at` 2026-06-30); o vivo é de 2026-07-14 com `input_records=590`, batendo com `wc -l data/editorial/refined_public_prose.jsonl` = 590. Trocar reprova por `ptbr_text_shape_release_input_stale`.
- **Não sobrescrever** `tools/generate-ptbr-text-shape-release`: o do `main` tem flock de artefato, `p0-factory-chain-lock`, budget/throughput/timeout `WIKI_HEAVY_*` e GOCACHE persistente; o do patch tem 9 linhas sem lock — abriria escrita concorrente no JSONL de evidência.

### 4.7 `kepler-publicrelease-seooracles`
- 5.961 bytes, 136 linhas, 2 arquivos, `untracked.lista` vazio. Base `3b7ae51f`, 1025 commits atrás.
- `ls internal/seooracles/` → `oracles.go` + `oracles_test.go`; `grep -n 'func RobotsAllowsConsensus' internal/seooracles/oracles.go` → **`:39`**. Funções: `RobotsAllows`, `RobotsAllowsByTemoto`, `RobotsAllowsConsensus`, `RobotsSitemaps`, `ParseSitemapXML`.
- Fiação já existe e é superset: `validateTemporaryPublicSEOOraclesWithIdentity` (`internal/publicrelease/publicrelease.go:3005`), chamada no smoke transacional em `:2646`, helpers `:3053-3127` — commit `38e3087d`, posterior à base.
- Três melhorias que o patch **não** tem: consenso de dois parsers de robots (vs 1), cobertura de **todas** as canonicals indexáveis + artifacts de sitemap do plano (vs 2 URLs fixas), e gate extra de variante com querystring.
- Testes equivalentes já existem em `publicrelease_sharded_sitemap_test.go:873/903/933`.

### 4.8 `linnaeus-roaring-postings`
- Base `3b7ae51f`, ancestral, 1025 commits atrás. Landou em `9142bf84` (2026-06-30) e melhorou em `ce5520ed` (2026-07-04).
- `grep -n 'BucketWindow' internal/roaringpostings/postings.go` → `:25`, `:39`, `:177`. O patch **não tem** `BucketWindow`/`TruncatedPairReferences`: é exatamente o corte da explosão quadrática de pares (janela deslizante default 32) — **o único mecanismo que torna o índice viável em 100k/1M URLs**. Regredir aqui destrói a proteção de escala.
- `internal/semanticclusterindex/roaring_postings_evidence.go` no `main` tem `sameStringSlice()` e o Issue `roaring_postings_dedupe_source_layers_invalid`; o patch só validava `len(SourceLayers)`.
- **Armadilha**: as 8 strings do patch em `internal/codex2policyenforcement/policy.go` são redação **anterior** a `internal/densepairset/`. Escrever a versão do patch derrubaria `densepairset` dos `AllowedImportScopes`/`AllowedWriteScopes` → o gate de política de dependência reprovaria um pacote legítimo.
- Check já registrado: `checks.go:377` (Names), `:1652` (dispatch), `:5297` (loader de evidência); `checkselection/selection.go:1200-1202` (`isRoaringPostingsPath`) e `:366-368`.

### 4.9 `lorentz-parquet-lt-399`
- `grep -n 'RequireScaleSidecar' internal/languagetoolquality/batch.go` → `:69` (BatchOptions), `:219` (ReleaseValidationOptions), `:264` (bloco de validação). Também `SourceIndexModeParquetScaleSidecar:41`, campos `ScaleSidecar*` `:177-181`, `ValidateRelease` → `ValidateReleaseWithOptions{RequireScaleSidecar:true}` `:1728`.
- `internal/contentinventoryparquet/inventory.go`: campos `SourceLineNumber/SourceByteOffset/SourceLineBytes/VisibleTextSHA256/VisibleTextBytes` (`:58-62`), `LanguageToolSidecarExpectation` (`:124`), `LoadLanguageToolSidecarRows` (`:619`), `ValidateLanguageToolReleaseSidecar` (`:639`).
- Landou em `9142bf84`, 74 min após a base; depois `bd382976`, `3ae4a8eb`, `b500f0c1`, `34…`.
- **Aplicar é ativamente nocivo**, 3 regressões concretas: (a) `bd382976` deletou de propósito a cópia unexported `joinVisibleTextSlots` e promoveu `JoinVisibleTextSlots` a canônica — o comentário em `inventory.go:854-860` documenta o bug de **falso mismatch** que a duplicação causava; o patch a reintroduz. (b) `batch.go` reverteria `totalSourceRecords` para `len(sourceRecords)`, quebrando a contabilidade de shard, e trocaria agregação de issues por `append` por registro (O(n) em 10k). (c) `cmd/generate-languagetool-quality/main.go` regrediria a usage string e o endpoint de exemplo de `:8082` para `:8010`, apagando `--cache-plan-json`, `--require-complete-cache`, `--profile-batches`, `--max-live-checks`, `--shard-count`, `--shard-index`. A flag `--require-scale-sidecar` já existe (`:191`, propagada em `:136`/`:257`) e já está em `tools/generate-languagetool-quality-release:102` + help `:66`.
- Testes do patch já existem e o `main` adicionou mais: `inventory_test.go:49` e `:93`; `languagetoolquality_test.go:2245` (+ assertivas `:2302-2309`) e `:2734-2738`.

### 4.10 `p0-anchor-join-fix-20260627072738`
- Patch gigante, mas **538 de 539** funções que ele define já existem no `main`; a única "ausente" é renomeação com corpo igual.
- O fix epônimo é **byte-idêntico**: `grep -n 'func rewriteMechanicalAnchorJoins' internal/refinedpublicprose/*.go` → `refined.go:40407`; bloco de 72 linhas até `mechanicalAnchorJoinSubject`, `diff` vazio contra o worktree. Landou em `157e86da` (2026-06-28), ancestral do HEAD, um dia após a base `bc585ad7`.
- Além disso, sob a **DEC-017** (`docs/goal/DECISIONS.md:134`) o caminho de reescrita mecânica está **desligado no regime v2** pelo flag `mechanicalClosureDisabled` — reativar a lógica do patch contraria decisão vigente.
- Aplicar sobrescreveria `refined.go` (42.615 linhas) com uma versão de ~10.000, revertendo assinaturas evoluídas (`effectiveRewriteTargets` ganhou `root string`; `validateRecordsWithStageTimings` e `planRequiresP0FullRefinement` ganharam `expectedTotal int`; `buildRecordsWithStageTimings` ganhou `reusable map[...]`) e quebrando a compilação de 781 testes do pacote.

### 4.11 `ptolemy-ckan-oracle-cycle399`
- `ls internal/ckanmetadata/` → `metadata.go` (22.121 B, 619 linhas) + `metadata_test.go`. Extraindo as linhas `+` do hunk e comparando: `diff` **vazio** nos dois arquivos → idêntico. A evidência `data/research/ckan_package_search_oracle_evidence.jsonl` também é idêntica (1 registro, `evidence_id=ckan-package-search-oracle-2026-06-30-stj-fixture`).
- Check registrado: `checks.go:438` (Names), `:1690-1691` (switch → `ckanmetadata.Validate(root).Messages()`).
- **Armadilha**: o hunk do patch em `internal/storage/storage.go` reverte a lista `required` ao estado de 2026-06-30, **removendo 6 camadas** adicionadas depois (`demand_terms_review_decisions`, `demand_terms_stj_policy_evidence`, `demand_terms_stj_capture_transaction`, `trafilatura_offline_extractor_evidence`, `readability_demand_html_extractor_evidence`, `colly_demand_metadata_probe_evidence`) → reprova `cmd/check storage-contract`.
- **Não sobrescrever** `tools/check-ckan-package-search-oracle`: o do `main` usa bash com `set -euo pipefail`, GOCACHE persistente em `$HOME/.cache/go-build` e `exec tools/run-check --timings`; o do patch usa `sh` + `go run ./cmd/check` + GOCACHE em `/tmp` (perde cache entre execuções).

---

## 5. Ordem de execução recomendada

Não há integração de código a executar. A ordem abaixo é a de **fechamento da frente**:

1. **Não editar nenhum arquivo do repo por causa das worktrees.** Nenhuma das 11 abre trabalho pendente. Se algo te levar a duvidar, releia a seção 4 do item específico antes de tocar em qualquer `.go`.
2. **Não rodar nenhum gate/teste "para conferir".** Nada mudou; suíte verde não prova nada aqui e custa CPU (ver seção 6 para as exceções, caso você mexa nesses pacotes por outro motivo).
3. **Registrar o veredito** onde o projeto guarda decisão de engenharia (`docs/goal/MAESTRO_CODEX_LOG.md` e/ou uma DEC em `docs/goal/DECISIONS.md`), com o resumo: *11 worktrees do Codex revisadas em 2026-07-28; 11/11 já integradas ao `main`; 0 a portar; backups preservados em `/home/rafael/.config/ai-terminal-backups/worktree-work-20260728-075936`*. Isso é o que impede a próxima sessão de refazer 11 investigações.
4. **Levar ao dono a decisão de disco** (seção 7). Só ele libera os 20 GB.

Dependências: o passo 3 não depende de nada; o passo 4 depende do passo 3 (a decisão do dono deve poder apontar para o registro escrito).

---

## 6. Como validar

Como nada é integrado, **não há validação a rodar** — e rodar suíte aqui é desperdício. Os comandos abaixo servem **só** se você for mexer nesses pacotes por outro motivo, no futuro. Go sempre via `./tools/go-modern`; **nunca** `go build ./...` (≈5 min, 504 pacotes).

| pacote | teste focado |
|---|---|
| `internal/engineeringnowcontract` | `./tools/go-modern test -count=1 ./internal/engineeringnowcontract/` |
| `internal/publicproselanguagepatterns` | `./tools/go-modern test -count=1 ./internal/publicproselanguagepatterns/` |
| `internal/workreuseledger` | `./tools/go-modern test -count=1 ./internal/workreuseledger/` (caro: `ledger.go` ~232 KB + testes ~325 KB) |
| `internal/publicfinalsourceliverecheck` | `./tools/go-modern test -count=1 ./internal/publicfinalsourceliverecheck/` |
| `internal/legalsignature` | evitar rodada cega: `streamdedup_scale_test.go` (17 KB) é teste de escala caro |
| `internal/ptbrtextshaperelease` | `./tools/go-modern test -count=1 ./internal/ptbrtextshaperelease/` (verde, 0,035 s) |
| `internal/publicrelease` | `./tools/go-modern test -count=1 -run 'TestValidateTemporaryPublicSEOOracles' ./internal/publicrelease/` |
| `internal/roaringpostings` / `internal/semanticclusterindex` | `./tools/go-modern test -count=1 ./internal/roaringpostings/` (0,003 s) e `./internal/semanticclusterindex/` (0,134 s) |
| `internal/languagetoolquality` / `internal/contentinventoryparquet` | teste focado do pacote tocado |
| `internal/refinedpublicprose` | focar por `-run` — 781 testes no pacote |
| `internal/ckanmetadata` | `./tools/go-modern test -count=1 ./internal/ckanmetadata/` (0,006 s) |

Gates que os patches quebrariam se alguém os aplicasse (úteis como canário caso apareça falha nova nessa área): `./tools/go-modern run ./cmd/check storage-contract` (itens 4.4 e 4.11) e o gate de política de dependência de `internal/codex2policyenforcement` (item 4.8).

---

## 7. O que fazer com as worktrees depois

**NÃO apague nada.** Estado verificado hoje:

- **Backups completos e íntegros**: `/home/rafael/.config/ai-terminal-backups/worktree-work-20260728-075936/` — 11 diretórios, 2,3 MB no total, cada um com `modificados.patch`, `untracked.lista`, `untracked/` (quando havia), `base-commit.txt`, `branch.txt`.
- **Os branches existem no repo** e são ancestrais do HEAD — nada some se a worktree sair do disco:

  | branch | commit |
  |---|---|
  | `codex-p0-engineeringnow-missing-path-20260703` | `1b098d1c` |
  | `codex-task2-public-prose-perf` | `1b098d1c` |
  | `codex-task4-workreuse-20260703093112` | `1b098d1c` |
  | `codex2-p0-public-final-source-live-recheck` | `7d19da8b` |
  | `codex384-legal-signature` | `df6450ba` |
  | `faraday-ptbr-text-shape-release` | `3b7ae51f` |
  | `kepler-publicrelease-seooracles` | `3b7ae51f` |
  | `cycle-399-linnaeus-roaring-postings` | `3b7ae51f` |
  | `lorentz-parquet-lt-399` | `3b7ae51f` |
  | `p0-anchor-join-fix-20260627072738` | `bc585ad7` |
  | `ptolemy-ckan-oracle-cycle399` | `3b7ae51f` |

- Qualquer uma é **recriável** a qualquer momento com `git worktree add <caminho> <branch>` — o custo de "desfazer" a limpeza é um comando.
- Nota de inventário: `codex-task4-workreuse-20260703093112` **não** está em `/opt/wiki/.worktrees`; ela vive em `/home/rafael/.config/superpowers/worktrees/wiki/codex-task4-workreuse-20260703093112` (por isso `.worktrees` tem 10 diretórios e os backups, 11). Confira com `git worktree list`.
- **A decisão de liberar os 20 GB é do dono.** Este handoff não autoriza remoção. Quando ele autorizar, o caminho limpo é `git worktree remove` (não `rm -rf`, que deixa metadado órfão em `.git/worktrees`), **depois** de confirmar com `git worktree list` que nenhum processo está usando o diretório. Manter os backups de 2,3 MB indefinidamente é barato e respeita a regra de nunca descartar trabalho.
