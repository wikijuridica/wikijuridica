# Cadeia editorial — ordem de regeneração dos derivados de `data/editorial/`

Documento derivado por **leitura direta do código**, não por memória do
repositório. Fonte: `grep -rn "older_than" internal/ --include=*.go`
(2026-09-08) e leitura de cada detector encontrado, mais os campos
`InputRelPath`/constantes equivalentes de cada pacote `internal/authorialmass*`
que referenciam o `OutputRelPath` de outro pacote.

**Por que existe**: a cadeia não está declarada em lugar nenhum — vive
implícita nos detectores de `mtime`. Regenerar fora de ordem já parou a
fábrica por 31 dias (05/08–05/09); o erro que aparece nesse caso é
`fingerprint mismatch` ou `*_artifact_stale`, **nunca** "ordem errada". Este
documento existe para que às 3 da manhã, sem tempo para arqueologia, dê para
saber o que rodar e em que ordem.

`tools/check-cadeia-editorial-ordem-declarada` prova que a lista de
detectores abaixo (bloco legível por máquina, delimitado por comentário HTML,
mais adiante nesta seção) cobre **todos** os detectores `older_than` que
existem no código **agora** — se alguém adicionar um detector novo e não
atualizar este documento, o gate reprova nomeando `arquivo:linha` do detector
órfão.

---

## 0. ATENÇÃO — esta cadeia NÃO é a cadeia de `data/editorial/v2_pages/*.jsonl`

**Achado crítico desta sessão, cheque antes de usar o resto do documento**:
nenhum dos cinco detectores `older_than`, nem os seis artefatos sem detector
próprio (§3), lê `data/editorial/v2_pages/*.jsonl`. Confirmado por leitura:

```
grep -rl "v2_pages" internal/authorialmassstock/ internal/authorialmassdrafts/ \
  internal/authorialmasscontentexpansion/ internal/authorialmass*/*.go \
  cmd/generate-authorial-mass-drafts/ cmd/generate-authorial-mass-content-expansion/
```

devolve **zero ocorrências** (rodado em 2026-09-08). A cadeia dos 13 elos
abaixo é o pipeline que CRIA rascunhos novos (`authorial_mass_drafts.jsonl`,
`authorial_mass_content_expansion.jsonl`) a partir de fontes próprias — é um
subsistema irmão do estoque `v2_pages`, não o mesmo grafo.

**Consequência prática**: reordenar linhas de um shard de
`data/editorial/v2_pages/*.jsonl` (via
`tools/generate-v2-shard-slice-reorder`) **não dispara nenhum dos cinco
detectores `older_than` deste documento** e não exige rodar nenhum dos 13
passos do §2. O que o reorder invalida é outro mecanismo, inteiramente CAS
(hash), não `mtime`: o **contrato semântico da fila**
(`data/editorial/v2_writing_semantic_contract.json`, campo
`dependency_sha256`, carregado por
`tools/generate_v2_review_queue.load_writing_semantic_contract`) — é ele que
o próprio gerador invalida em memória a cada escrita
(`_invalidate_semantic_contract`) e é ele quem `ops/relaunch-writing.sh`
reconcilia. Se depois de reordenar um shard aparecer `fingerprint mismatch`
ligado a `v2writingsemantic` (`internal/v2writingsemantic/git_index.go:927`)
ou a mensagem `manifesto stale`/`preimagem já é canônica`, a correção é
**rodar `ops/relaunch-writing.sh` de novo** (que o próprio
`tools/generate-v2-shard-slice-reorder --apply` já imprime como próximo
passo) — **nunca** os passos do §2 desta cadeia, que resolvem um problema
diferente.

**Outros consumidores que hasheiam os BYTES do shard e podem acusar depois
de um reorder** (achados pelo mesmo levantamento de `fingerprint mismatch`
que fundamentou este documento, não lidos em profundidade — fora do escopo
desta engenharia):
`internal/v2ingest/reusable_artifact_semantics.go:575`
(`source shard fingerprint mismatch`) e `:728`
(`portfolio shard fingerprint mismatch`),
`internal/v2pagedistinctness/store.go:3175`
(`manifest fingerprint mismatch shard=`), e
`internal/v2privateverdict/verdict.go:1306`
(`private verdict shard fingerprint mismatch`). Se a mensagem citar
`shard=` num destes quatro pacotes depois de um reorder, a reconciliação é
do subsistema respectivo (fora deste documento) — **não** é
`relaunch-writing.sh` nem os passos do §2. Este documento não resolve esses
quatro; só evita que sejam confundidos com a cadeia `authorial_mass_*`.

O restante deste documento (§1–§5) descreve a cadeia `authorial_mass_*` tal
como ela é — real e com o mesmo risco de regeneração fora de ordem — mas é
importante não confundir as duas cadeias na urgência das 3 da manhã.

---

## 1. Os cinco detectores `older_than` (lista fechada em 2026-09-08)

`grep -rn "older_than" internal/ --include=*.go` devolve exatamente 5
ocorrências, todas dentro de funções de "freshness" que comparam
`os.Stat(saída).ModTime()` contra `os.Stat(entrada).ModTime()` para cada
entrada declarada, e produzem uma mensagem `"<saída> older_than <entrada>"`
quando a entrada é mais nova. Nenhuma outra ocorrência de `ModTime().After(`
no repositório pertence a esta família (conferido: `internal/factorymetrics`
e `internal/proc` usam o padrão para achar o mtime mais recente de uma
árvore, não para comparar derivado-vs-fonte; ambos ficam **fora** desta
lista, de propósito).

| # | Função (arquivo) | Artefato que exige mais novo (saída) | Check exposto |
|---|---|---|---|
| D1 | `authorialMassGlobalSimilarityFreshnessMessages` (`internal/checks/checks.go`) | `data/editorial/authorial_mass_global_similarity_audit.jsonl` | `tools/check-authorial-mass-global-similarity-audit` |
| D2 | `qualityVectorPersistedCurrentInputFreshnessIssues` (`internal/authorialmassqualityvectors/quality_vectors.go`) | `data/editorial/authorial_mass_editorial_quality_vectors.jsonl` | `tools/check-authorial-mass-editorial-quality-vectors` |
| D3 | `refinementQualityArtifactFreshnessIssues` (`internal/authorialmassqualityvectors/quality_vectors.go`) | `data/editorial/authorial_mass_refinement_quality_report.jsonl` | **não é case de `cmd/check`** — roda DENTRO de `authorialmassqualityvectors.Generate`/`GenerateWithTimingSink`, ou seja, dispara ao regenerar quality-vectors (`tools/generate-authorial-mass-editorial-quality-vectors`) ou ao rodar `tools/probe-authorial-mass-quality-vectors-timing` |
| D4 | `globalSimilarityArtifactFreshnessIssues` (`internal/authorialmassqualityvectors/quality_vectors.go`) | `data/editorial/authorial_mass_global_similarity_audit.jsonl` | idem D3 — interno ao gerador de quality-vectors, **mesma saída que D1**, ver ambiguidade §4 |
| D5 | `readinessCurrentInputFreshnessIssues` (`internal/authorialmassreadiness/readiness.go`) | `data/editorial/authorial_mass_publication_readiness.jsonl` | `tools/check-authorial-mass-publication-readiness` |

<!-- cadeia:detectores -->
internal/checks/checks.go:authorialMassGlobalSimilarityFreshnessMessages
internal/authorialmassqualityvectors/quality_vectors.go:qualityVectorPersistedCurrentInputFreshnessIssues
internal/authorialmassqualityvectors/quality_vectors.go:refinementQualityArtifactFreshnessIssues
internal/authorialmassqualityvectors/quality_vectors.go:globalSimilarityArtifactFreshnessIssues
internal/authorialmassreadiness/readiness.go:readinessCurrentInputFreshnessIssues
<!-- /cadeia:detectores -->

### O que cada detector compara, e a mensagem exata

- **D1** — compara `authorial_mass_global_similarity_audit.jsonl` contra
  `authorial_mass_drafts.jsonl`, `authorial_mass_content_expansion.jsonl` e
  `data/editorial/authorial_mass_signature_candidate_pairs.jsonl`. Mensagem:
  `authorial_mass_global_similarity_artifact_stale: data/editorial/authorial_mass_global_similarity_audit.jsonl older_than <entrada>`.
- **D2** — compara `authorial_mass_editorial_quality_vectors.jsonl` contra
  `authorial_mass_refinement_quality_report.jsonl`,
  `authorial_mass_global_similarity_audit.jsonl`,
  `authorial_mass_content_expansion_section_chunks.jsonl`,
  `authorial_mass_paid_intent_refinements.jsonl` (aqui **não** é opcional —
  ausente vira `authorial_mass_quality_vectors_current_input_stat_failed`,
  diferente do comportamento de D5), `authorial_mass_drafts.jsonl` e
  `authorial_mass_content_expansion.jsonl`. Mensagem:
  `authorial_mass_quality_vectors_current_input_artifact_stale: data/editorial/authorial_mass_editorial_quality_vectors.jsonl older_than <entrada>`.
- **D3** — compara `authorial_mass_refinement_quality_report.jsonl` contra
  `authorial_mass_drafts.jsonl`, `authorial_mass_content_expansion.jsonl` e
  `authorial_mass_signature_candidate_pairs.jsonl`. Mensagem:
  `authorial_mass_quality_vectors_refinement_authorial_mass_refinement_quality_artifact_stale: data/editorial/authorial_mass_refinement_quality_report.jsonl older_than <entrada>`.
- **D4** — compara `authorial_mass_global_similarity_audit.jsonl` contra as
  MESMAS três entradas de D1. Mensagem: idêntica ao prefixo de D1
  (`authorial_mass_global_similarity_artifact_stale: ... older_than ...`),
  mas emitida como `authorialmassglobalsimilarity.Issue`, não `string` — ver
  ambiguidade §4.
- **D5** — compara `authorial_mass_publication_readiness.jsonl` contra
  `authorial_mass_paid_intent_refinements.jsonl` (**opcional**: ausente não
  reprova, só é pulado — `readinessCurrentInputOptionalDependency`),
  `authorial_mass_editorial_quality_vectors.jsonl`,
  `authorial_mass_contextual_compatibility.jsonl`,
  `authorial_mass_signature_refinement_queue.jsonl`,
  `authorial_mass_similarity_report.jsonl`,
  `authorial_mass_similarity_semantic_reviews.jsonl`,
  `authorial_mass_global_similarity_audit.jsonl`,
  `authorial_mass_drafts.jsonl` e `authorial_mass_content_expansion.jsonl`.
  Mensagem:
  `authorial_mass_readiness_current_input_artifact_stale: data/editorial/authorial_mass_publication_readiness.jsonl older_than <entrada>`.

### Um gate irmão que NÃO é desta família (não confundir)

`checkAuthorialMassRefinementQualityReport` (case
`authorial-mass-refinement-quality-report`) chama
`authorialMassRefinementQualityFreshnessMessages` (`internal/checks/checks.go:12051`),
que compara um **sidecar de fingerprint de conteúdo**
(`authorialmassrefinementquality.WriteInputFingerprint` /
`LoadInputFingerprint`/`ComputeInputFingerprint`) contra os inputs vivos —
**não usa `mtime`, não usa a string `older_than`**, e por isso o `grep` desta
seção corretamente não o lista. O comentário no próprio código
(`internal/checks/checks.go:12041-12050`) explica o motivo: `mtime` reprovava
qualquer append legítimo em `authorial_mass_drafts.jsonl` (43 MB, edição
contínua) mesmo sem mudança relevante. Mensagem quando desatualizado:
`authorial_mass_refinement_quality_artifact_stale: content_fingerprint_mismatch recorded=<x> current=<y>`,
com o hint de regeneração embutido na própria mensagem. Trate esta mensagem
como **P1**: é o mesmo tipo de defeito (artefato atrás da fonte), mecanismo
diferente.

---

## 2. Grafo de dependência (fonte → derivado) e ordem topológica

Derivado por leitura de `SourceLayers`, `InputRelPath`/`*InputRelPath` e das
chamadas `authorialmass<pkg>.LoadRecords`/`.Validate` dentro de cada pacote —
não só dos cinco detectores acima, porque um detector `older_than` só prova
a ordem de QUEM ELE COMPARA; a ordem completa da cadeia depende também de
constantes de input que não geram detector de frescor próprio (ver §3).

```
authorial_mass_drafts.jsonl ────────────────────┐
authorial_mass_content_expansion.jsonl (+ section_chunks) ─┤
                                                  │
        ┌─────────────────────────────────────────┼───────────────┬──────────────────┐
        ▼                                          ▼               ▼                  ▼
authorial_mass_legal_signatures.jsonl   authorial_mass_contextual_  authorial_mass_    authorial_mass_
        │                                compatibility.jsonl        paid_intent_       similarity_report.jsonl
        ▼                                                           refinements.jsonl         │
authorial_mass_signature_candidate_pairs.jsonl                                                 ▼
        │                                                                          authorial_mass_similarity_
        ├──────────────────────────────────┐                                       semantic_reviews.jsonl
        ▼                                   ▼
authorial_mass_refinement_quality_   authorial_mass_global_similarity_
report.jsonl  (D3)                   audit.jsonl  (D1, D4)
        │                                   │
        └─────────────┬─────────────────────┘
                       ▼
        authorial_mass_editorial_quality_vectors.jsonl  (D2)
                       │
                       ▼
        authorial_mass_signature_refinement_queue.jsonl
        (depende TAMBÉM de signature_candidate_pairs, legal_signatures
         e de refined_public_prose.jsonl — ver ambiguidade/fronteira §4)
                       │
        ┌──────────────┴───────────────────────────────────┬──────────────────┐
        ▼                                                   ▼                  ▼
authorial_mass_publication_readiness.jsonl (D5) ◄── contextual_compatibility, paid_intent_refinements(opcional),
                                                        similarity_report, semantic_reviews, global_similarity_audit,
                                                        drafts, content_expansion
```

### Ordem topológica linear (a que se segue na prática)

<!-- cadeia:ordem -->
1. data/editorial/authorial_mass_drafts.jsonl
2. data/editorial/authorial_mass_content_expansion.jsonl
3. data/editorial/authorial_mass_legal_signatures.jsonl
4. data/editorial/authorial_mass_contextual_compatibility.jsonl
5. data/editorial/authorial_mass_paid_intent_refinements.jsonl
6. data/editorial/authorial_mass_similarity_report.jsonl
7. data/editorial/authorial_mass_signature_candidate_pairs.jsonl
8. data/editorial/authorial_mass_similarity_semantic_reviews.jsonl
9. data/editorial/authorial_mass_refinement_quality_report.jsonl
10. data/editorial/authorial_mass_global_similarity_audit.jsonl
11. data/editorial/authorial_mass_editorial_quality_vectors.jsonl
12. data/editorial/authorial_mass_signature_refinement_queue.jsonl
13. data/editorial/authorial_mass_publication_readiness.jsonl
<!-- /cadeia:ordem -->

**Nota de honestidade sobre o número**: o contrato do repositório fala em
"~9 artefatos". Medido agora, a cadeia tem **13 elos distintos** (contando
`content_expansion` + seu sidecar `_section_chunks` como um único gerador).
Não arredondei para 9 — o valor medido é este; se "~9" vinha de uma contagem
mais estreita (só os que têm detector `older_than` próprio: são 4 saídas
distintas — `global_similarity_audit`, `editorial_quality_vectors`,
`refinement_quality_report`, `publication_readiness` — mais as 2 fontes
brutas, dá 6, ainda não 9), é uma discrepância a esclarecer com quem mediu
"~9", não um erro deste documento.

| Passo | Comando exato para regenerar |
|---|---|
| 1 | `tools/generate-authorial-mass-drafts` |
| 2 | `tools/generate-authorial-mass-content-expansion` |
| 3 | `tools/generate-authorial-mass-legal-signatures` |
| 4 | `tools/generate-authorial-mass-contextual-compatibility` |
| 5 | `tools/generate-authorial-mass-paid-intent-refinements` |
| 6 | `tools/generate-authorial-mass-similarity-report` |
| 7 | `tools/generate-authorial-mass-signature-candidate-pairs` |
| 8 | `tools/generate-authorial-mass-similarity-semantic-reviews` |
| 9 | `tools/generate-authorial-mass-refinement-quality-report` |
| 10 | `tools/generate-authorial-mass-global-similarity-audit` |
| 11 | `tools/generate-authorial-mass-editorial-quality-vectors` |
| 12 | `tools/generate-authorial-mass-signature-refinement-queue` |
| 13 | `tools/generate-authorial-mass-publication-readiness` |

Todos os wrappers acima já vêm envelopados em `tools/run-heavy-throttled` +
`tools/run-go-cmd-cached` (conferido no próprio script de cada um) — **não**
chame `./tools/go-modern run -tags devcmds ./cmd/generate-authorial-mass-*`
direto; o wrapper é quem tem o orçamento de tempo/throughput calibrado.
Rodar um passo é trabalho pesado (compila + processa o estoque inteiro) —
**envelope e serialização são decisão do maestro**, esta seção só documenta
a ordem e o comando, não autoriza esta sessão a executá-los.

---

## 3. Os seis artefatos sem detector `older_than` próprio

`authorial_mass_legal_signatures.jsonl`,
`authorial_mass_contextual_compatibility.jsonl`,
`authorial_mass_paid_intent_refinements.jsonl`,
`authorial_mass_similarity_report.jsonl`,
`authorial_mass_signature_candidate_pairs.jsonl` e
`authorial_mass_similarity_semantic_reviews.jsonl` **não têm nenhum detector
que compare o próprio `mtime` contra o das fontes que leem**. A posição deles
na ordem acima vem de constantes de código (`InputRelPath`, chamadas
`LoadRecords` dentro do pacote), **não de um gate que reprove se a ordem for
violada**:

- `authorial_mass_legal_signatures.jsonl` lê `authorialmassstock.LoadRecords`
  (drafts + content_expansion) — `internal/authorialmasslegalsignatures/sharddelta.go:229`.
  `Validate` (`signatures.go:217`) não confere contagem/fingerprint contra o
  estoque vivo nesta leitura — **é o mais fraco dos seis**.
- `authorial_mass_signature_candidate_pairs.jsonl` declara
  `InputRelPath = authorial_mass_legal_signatures.jsonl` —
  `internal/authorialmasssignaturepairs/pairs.go:25`. `Validate` (`pairs.go:473`)
  recarrega `LoadSignatureRecords` e valida os pares contra as assinaturas
  vivas — pega drift de CONTEÚDO das assinaturas, não de mtime.
- `authorial_mass_contextual_compatibility.jsonl` lê
  `authorialmassstock.LoadRecords` — `internal/authorialmasscontextcompat/compatibility.go:106,226`.
  `ValidateRecordsWithExpectedTotal` (`compatibility.go:249`) reprova
  `authorial_mass_contextual_compatibility_count_mismatch` se
  `len(records) != len(stock)` — pega estoque que cresceu/encolheu, não
  reescrita de conteúdo com a mesma contagem.
- `authorial_mass_paid_intent_refinements.jsonl` lê `authorialmassdrafts` e
  `authorialmasscontentexpansion` diretamente —
  `internal/authorialmasspaidrefinement/refinement.go:249-250`.
- `authorial_mass_similarity_report.jsonl` lê só `authorialmassdrafts` (não
  precisa de `content_expansion`) — `internal/authorialmasssimilarity/similarity.go:82,221`.
  `ValidateRecords` (`similarity.go:241,249`) reprova
  `authorial_mass_similarity_source_mismatch` se `SourceDraftCount` divergir
  da contagem viva de drafts, e `authorial_mass_similarity_fingerprint_missing`/
  `_report_fingerprint_mismatch` sobre `SourceDraftFingerprint` — validação de
  CONTEÚDO (contagem + fingerprint), não de `mtime`.
- `authorial_mass_similarity_semantic_reviews.jsonl` lê
  `authorialmasssimilarity.LoadRecords` + `authorialmassdrafts` —
  `internal/authorialmasssemanticreviews/semantic_reviews.go:65-76`. `Validate`
  (`semantic_reviews.go:240`) recalcula o esperado via `Generate` e compara
  registro a registro por `SemanticReviewID`.

**Precisão sobre a AMBIGUIDADE**: os seis artefatos **têm** validação de
conteúdo (contagem e/ou fingerprint) contra a fonte que leem — não é
"nenhum gate os protege". O que falta especificamente é um detector de
**`mtime`/`older_than`**: se alguém regenerar
`authorial_mass_similarity_report.jsonl` e a contagem de drafts não tiver
mudado (só o CONTEÚDO de um draft já existente mudou, sem entrar/sair
nenhum), `SourceDraftCount` continua batendo e o gate de contagem passa —
só um fingerprint de conteúdo pegaria isso, e nem todos os seis calculam um
(legal_signatures não calcula). A ordem na tabela do §2 é a correta pela
leitura das dependências de código; o risco residual é regenerar um destes
seis DEPOIS de uma mudança de conteúdo (não de contagem) na fonte e não ser
avisado. Se isso incomodar na prática, a correção é estender a validação de
`legal_signatures` com um fingerprint como os demais — não existe hoje.

---

## 4. Ambiguidades adicionais, declaradas em vez de resolvidas por invenção

1. **D1 e D4 protegem o MESMO artefato** (`authorial_mass_global_similarity_audit.jsonl`)
   com as MESMAS três entradas, mas em pontos diferentes do código: D1 roda
   como `tools/check-authorial-mass-global-similarity-audit` (depois do
   artefato já escrito); D4 roda DENTRO do gerador de quality-vectors, antes
   de aceitar `authorial_mass_global_similarity_audit.jsonl` como input
   válido para calcular `authorial_mass_editorial_quality_vectors.jsonl`. Se
   um dos dois for editado (ex.: alguém adicionar uma quarta entrada a D1 e
   esquecer D4), os dois gates DIVERGEM sobre o que é "fresco" para o mesmo
   arquivo — hoje nada os mantém sincronizados além de leitura humana. Não
   unifiquei os dois nesta sessão (seria mudar `internal/checks` e
   `internal/authorialmassqualityvectors` ao mesmo tempo por um motivo fora
   do escopo desta tarefa) — fica registrado como dívida.

2. **`authorial_mass_paid_intent_refinements.jsonl` é opcional em D5 e
   obrigatório (não-opcional) em D2.** Mesma entrada, dois comportamentos
   diferentes quando ausente: D5 pula silenciosamente
   (`readinessCurrentInputOptionalDependency`); D2 reprova com
   `authorial_mass_quality_vectors_current_input_stat_failed`. Não uniformizei
   — é comportamento medido, registrado para não ser confundido com bug do
   gate.

3. **D3 e D4 não são `cmd/check` cases** — disparam apenas quando alguém tenta
   REGENERAR `authorial_mass_editorial_quality_vectors.jsonl`
   (`tools/generate-authorial-mass-editorial-quality-vectors`) ou roda
   `tools/probe-authorial-mass-quality-vectors-timing`. Rodar só
   `tools/check-authorial-mass-refinement-quality-report` ou
   `tools/check-authorial-mass-global-similarity-audit` NÃO exercita D3/D4 —
   só o detector por fingerprint de conteúdo (para refinement-quality-report)
   e D1 (para global-similarity-audit). Confundir isso leva a achar que "o
   gate passou" quando na verdade o gate que passou é outro.

4. **`authorial_mass_signature_refinement_queue.jsonl` depende de
   `data/editorial/refined_public_prose.jsonl`**
   (`RefinedPublicProseRelPath`, `internal/authorialmasssignaturerefinementqueue/queue.go:34`).
   Esse artefato é produzido pela fronteira **P4**
   (`internal/refinedpublicprose`, `internal/publicrelease` a partir de
   `publicrelease.go:3379`) — **fora do escopo desta engenharia**. Este
   documento trata `refined_public_prose.jsonl` como **entrada externa já
   fresca**: se o passo 12 (`signature-refinement-queue`) acusar staleness
   contra ele, a correção NÃO é regenerá-lo por aqui — é escalar ao
   especialista responsável pela fronteira P4, conforme a fronteira
   inviolável já registrada no contrato desta sessão.

5. **Nenhum ciclo foi encontrado.** O grafo do §2, incluindo os seis
   artefatos do §3, é um DAG — cada aresta aponta de uma fonte mais antiga
   para um derivado mais novo, sem retorno.

---

## 5. O que fazer quando aparecer `fingerprint mismatch`

`fingerprint mismatch` (sem qualificação) é o nome genérico usado por MUITOS
subsistemas fora desta cadeia (CAS de `v2ingest`, `v2sourceprovenance`,
`v2privateverdict`, `demandtermsdecision`, etc. — nenhum deles é
`authorial_mass_*`). **Não assuma que é esta cadeia** só porque a mensagem
contém a palavra. Para saber se É esta cadeia:

- Mensagem contém `authorial_mass_*_artifact_stale` + `older_than` → **É**
  esta cadeia, §1. A mensagem tem o formato `<SAÍDA> older_than <ENTRADA>` —
  **regenere a partir da posição de `<ENTRADA>` (Y) na lista topológica do
  §2, nunca a partir de `<SAÍDA>` (X)**. Exemplo real: se a mensagem for
  `authorial_mass_editorial_quality_vectors.jsonl older_than
  authorial_mass_drafts.jsonl` (X=passo 11, Y=passo 1), regenerar só a
  partir do passo 11 PULARIA os passos 6 e 8
  (`similarity_report`/`semantic_reviews`), que também dependem de
  `authorial_mass_drafts.jsonl` e não têm detector `older_than` próprio (§3)
  — eles ficariam desatualizados em silêncio. Regenerar a partir da posição
  de Y sobre-regenera um pouco (alguns elos que já estavam frescos rodam de
  novo), mas nunca deixa um elo sem gate para trás — é o lado seguro do erro.
- Mensagem é `authorial_mass_refinement_quality_artifact_stale: content_fingerprint_mismatch`
  → é o gate de sidecar do §1 (não-`older_than`); regenere com o wrapper
  `tools/generate-authorial-mass-refinement-quality-report` (já envelopado em
  `run-heavy-throttled`/`run-go-cmd-cached` — não chame
  `./tools/go-modern run -tags devcmds ./cmd/generate-...` direto, que é o
  padrão proibido pelo hook local para trabalho pesado fora do wrapper).
- Mensagem cita `v2ingest`, `v2sourceprovenance`, `v2privateverdict`,
  `demandtermsdecision`, `contentstore`, `v2pagedistinctness`,
  `v2supersessionintegrity` ou `officialsourceurlliveevidenceschema` → **não**
  é esta cadeia; é a família CAS de conteúdo/hash desses pacotes, com
  regeneração e troubleshooting próprios, fora do escopo deste documento.

**Antes de regenerar qualquer elo**, preserve o artefato anterior em
`.agents/runtime/` com data (regra geral do repositório para artefato com
trabalho pago) — a cadeia de geração é pesada (compila + processa o estoque
inteiro) e reverter uma regeneração ruim não é uma operação de git.
