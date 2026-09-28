# STATUS.md — Estado vivo do /goal (retomável por sessão nova)

## Atualização viva 2026-07-20 — verdade P0 após reinício e auditoria Codex

- `published_manifest=0`, `public_indexable_legal_pages=0`, déficit público=10.000.
  `content/pages.json` contém somente quatro páginas institucionais/utilitárias; sitemap
  real contém apenas a home. Nenhuma linha privada/noindex é contada como publicação.
- Portfólio V2: 10.041 intents únicos. O contador bruto 10.041−7.934=2.107 era falso:
  após finalizados, supersessões, partials, skips, duplicatas e IDs fora do portfólio,
  a interseção viva é 7.661 e faltam **2.380** corpos ativos (2.341 ausentes +39 apenas
  skipped). Estoque aceito=6.846; qualidade/compatibilidade/revisão≈590; release antigo=209.
- Há 2.082 `*.tmp` em `v2_pages`; não apagar. O finish-forward autenticado foi
  corrigido e commitado em `41514c2d`; uma única recuperação pinada do journal
  `v2-semantic-forward-candidates-v3` concluiu em 2026-07-20. A inspeção viva após
  a operação prova `journal_absent`, contrato interno `sha256:2ce72de1...` e recibo
  `sha256:4a6c420f...`, com `publication_allowed=false`. Não repetir o apply; revisar
  e integrar os artefatos finais por pathspec antes da próxima ingestão V2.
- DataJud histórico tem 218 linhas incompatíveis com o contrato semântico atual. A
  reconciliação offline planeja 387 pares canônicos e classifica cada linha; operação
  real aguarda preflight adversarial, receipt/storage e falso-verde 401/403 fechados.
- O ensaio público de 360 páginas continua todo bloqueado. Leitura humana encontrou
  title/meta mecânicos que o language gate não acusava; correção sistêmica está em curso.
- O loop de `tools/run-check` por EACCES em cache root-owned foi corrigido e commitado
  em `f8067928`: lock inválido falha rápido, metadata é atômica e cache é por worktree.
- A família maior `run-go-cmd-cached` foi revisada adversarialmente e commitada em
  `dad121a3`: leitura/execução por descritor autenticado evita FIFO/symlink/TOCTOU,
  locks têm identidade e orçamento, e 54/54 testes passaram em 42,2 s. O custo
  residual é uma varredura linear de ~41,5 MB da árvore Go; não depende do volume de
  páginas, mas deve evoluir para closure/Merkle incremental antes de a árvore de código
  crescer materialmente.
- A política semântica central de intenção foi commitada em `87f07e13`: o cartesiano
  bruto de 18.228 combinações produz agora 10.083 compatíveis; após regras/cap do
  seletor, o estoque interno honesto é 9.590 (déficit interno=410, distinto do déficit
  público=10.000). JSONL histórico sem fingerprint/lineage atual continua fail-closed;
  não regenerar nem promover até fechar a fonte e os gates downstream.
- O detector anti-loop `check-command-progress` foi commitado em `e466d4f5`: elimina
  dupla contagem de I/O, processo sem baseline, auto-observação e artefato sem progresso
  autenticado; 53/53 testes passaram. A família watchdog ainda tem deadline de fixture
  não determinístico e está em correção separada antes de declarar a pilha inteira verde.
- DataJud foi confrontado com a documentação/termo oficial vivo: uso desta integração é
  somente pesquisa editorial agregada não comercial, no máximo 120 requisições/minuto,
  sem hits individuais/partes/processos no artefato e sem publicação. O catálogo TPU
  interno minimizado planeja 57 requests para 387 pares (−85,27%, workers derivados=40),
  mas a operação real continua bloqueada até executor com token bucket global, chave
  pública atual lida em runtime, Retry-After, cancelamento e receipt atômico.
- Configuração Codex oficial auditada como usuário `rafael`: config global sem
  `agents.max_threads`, sem `workers` e sem `agents.v2`; `multi_agent` estável ativo;
  launchers global/repo são idênticos; `doctor` normal e `--strict-config` verdes.
  Um `CODEX_HOME` global stale foi removido do ambiente tmux, preservando o home
  isolado correto da sessão. O teto efetivo desta ferramenta ainda é transitório e
  não será hardcoded: todos os slots expostos são usados e o trabalho segue em ondas.
- Revalidação oficial em 2026-07-20: o manual Codex vivo documenta
  `agents.max_threads` como cap de threads abertas e padrão 6 quando ausente. Os
  launchers idênticos aceitam `--max-agents=N`/`AI_CODEX_MAX_THREADS=N` e injetam
  somente `-c agents.max_threads=N` no processo novo, recusando cap persistente e nomes
  não oficiais. A sessão atual foi aberta sem override. `codex --strict-config -C
  /opt/wiki doctor --no-color --all` terminou em 1,04 s com `17 ok`, `1 idle`, `0 warn`,
  `0 fail`, bancos íntegros e `multi_agent` ativo; nenhuma configuração foi inventada ou
  alterada para contornar a capacidade transitória já exposta ao thread.
- Antes de P1–P5, revisar integralmente todos os arquivos versionáveis staged/unstaged/
  untracked, incluindo divergências `MM`/`AM`, código, conteúdo, dados, integrações,
  configuração e ferramentas. A tasklist D4 de PLAN.md exige mapa produtor/consumidor,
  revisão adversarial, correção para frente, validação proporcional, releitura e commit
  somente por pathspec explícito. Merge, cherry-pick e descarte são proibidos.
- Primeiro censo D4 expandindo todos os untracked (após `f70b1288`): 7.042 entradas
  vivas, sendo 5.436 com mudança no índice, 602 mudanças tracked fora do índice e
  1.078 arquivos untracked; há 24 `MM` e 50 `AM`. O censo é volátil e deve ser
  recalculado a cada onda. A concentração atual inclui 4.993 artefatos em
  `data/source-snapshots`, 740 untracked em `data/editorial` e 119 adições staged na
  mesma família; isso confirma que D4 precisa operar por produtor/consumidor, não por
  um commit geral.
- O primeiro reparo do grafo de commit V2 foi integrado em `f70b1288`: quatro arquivos
  Go fazem precedência por chave exata entre sucessor semântico e revisão independente,
  preservam claims não relacionados e removem uma materialização temporária descartada
  de blobs Git. O fechamento compilou 1.418 arquivos/32,4 MB em 29,8 s. A revalidação
  subsequente encontrou outro deadlock de gate entre membership no parent e correção
  monotônica de páginas legacy; o lote de dados continua NO-GO até o checker e controles
  negativos provarem uma sequência edit-forward executável.

Próxima ordem P0: (1) fechar preflight e reconciliar/coletar DataJud sem publicação;
(2) revisar/commitar os artefatos finais do finish-forward V2; (3) resolver joins/fontes stale; (4) corrigir
fábrica PT-BR e formar os 2.380 corpos faltantes; (5) avançar o estoque inteiro pelos
gates até exatamente 10.000 páginas públicas verificadas; (6) executar D4; só então P1–P5.

Última atualização: 2026-07-09 noite (sessão Claude — PASSO 12 DESTRAVADO)

## Atualização 2026-07-09 noite — PASSO 12 PASSA, refined 590 gerado 0-molde (LER PRIMEIRO)

**MARCO: `generate-refined-public-prose` EXIT=0.** O passo 12, que travava a
cadeia editorial inteira, está destravado. `data/editorial/refined_public_prose.jsonl`
gerado com 590 registros; verificação: os 590 têm H1/title/summary IDÊNTICOS ao
candidato autoral — **ZERO molde/invenção** (gate DEC-017 100% passthrough).

**Causa raiz completa (o que a sessão anterior deixou pela metade):** o guard
DEC-017 anterior (cc53c112, em `repairPublicHeadingPrepositionChainSlot`) era
INCOMPLETO. O caminho REAL do molde no probe era
`closeSinglePassPublicProseQualityFromStatWithFinalStat` (refined.go) — a variante
de quality-closure do caminho SHORT do probe, que ficou SEM o gate
`mechanicalClosureDisabled` que as irmãs já tinham. Bisseção determinística provou:
o H1 autoral de junta virava molde exatamente nessa closure. Gate espelhado.

**A "CASCATA de falso-positivos" prevista foi atacada por inteiro** (2 workflows,
12 agentes Sonnet 5, triagem FP-vs-real). Corpus 590: registros-com-código
**117 → 33**. 9 famílias de detector corrigidas por CAUSA RAIZ, sem afrouxar
(moldes/doorways de controle continuam reprovando; unit tests verdes):
- closure DEC-017 (gate faltante) — molde-invenção de H1.
- shape terminal_connector: `FoldedWords` confundia verbos tônicos "dá"/"é" com
  conectores átonos "da"/"e"; + homógrafo "para"(parar) + sufixo lei "484-A".
- repeated_phrase: frequência de 3-gram → CLUSTERING (template longo concentrado
  OU dominância), pra não reprovar recorrência temática ("Lei 9.656" 6x, "quebra
  de caixa" 10x). Idem a STAT crua do probe (report-only sob DEC-017).
- stacked_prepositions + de_article: bug do `\b` ASCII do Go em palavra ACENTUADA
  ("saúde do"→par falso "de do") → token-based (ptbrtext.Words).
- heading_meta: título interrogativo "...deve/precisa?" isento (normalização
  apagava o "?"). heading_preposition_chain: sintagma genitivo "de X de Y de Z"
  e enumeração "com A, com B ou C" isentos. adjacent_repeated: segmenta por frase.

**Cauda restante (33 registros, NÃO bloqueia mais o probe):** thin_section (5),
measured_placeholder (4), + ~1 defeito real de conteúdo (trab-empresa-fechou-sumiu:
citação "no art." truncada → fila de revisão). São relatório/revisão, não blocker.

**PRÓXIMO:** `bootstrap-chain --from 13` (language-patterns → oráculos PT-BR →
dedupe/cluster/contextual/source-live → legal_reviews → release_evidence →
release_transaction → verdict → manifest) até `verdict_passed > 0`. Pré-req:
LanguageTool :8082, venvs dos oráculos ptbr_* (passo 14+).

---

Última atualização anterior: 2026-07-09 (sessão Claude — reparo do censo + diagnóstico do verdict)

## Atualização 2026-07-09 tarde — ensaio E5 em N=590 (LER PRIMEIRO)

**Marco: morphsyntax virou gate release full-corpus (DEC-018, commit a3af2796)** —
o deep-check que tornava o verdict INSATISFAZÍVEL agora passa (spaCy full-corpus,
209→209 cobertas; Stanza vira diagnóstico). Isso destrava o caminho do verdict.

**Ensaio E5 expandido para N=590** (commit 72009d93): re-ingestão dos 37 arquivos
v2_pages limpos (590 páginas, reparos do censo propagados ao estoque — o refined
estava stale citando "dia 7" FGTS revogado). stock_manifest drafts_expected=590.
3 arquivos ficam na fila de revisão (saude-04, saude-13, trabalhista-20).

**Cadeia N=590: regenera limpa até o passo 11** (commit 3f36df9c). Dois elos de
escala corrigidos (assumiam o estoque doorway cartesiano do v1):
- global_similarity: a N>250 o banding acha 0 candidatos near-dup em corpus
  autoral diverso; 0 com cobertura provada = válido (não "corpus sujo").
- conector de+artigo: isenta "de, no máximo" (adverbial pós-vírgula) via texto RAW.

**BLOQUEIO ATUAL — passo 12 (refined-public-prose): FAMÍLIA de detectores de
prosa PT-BR/editorial calibrados para o v1 cartesiano que FALSO-POSITIVAM a prosa
v2 AUTORAL** (tema da DEC-017). Count converge (5→4→2 registros). Confirmados:
- `public_ptbr_connector_boundary_de_article` (corrigido, patterns.go RAW).
- `public_editorial_heading_meta_instruction`: H1 natural "O que é sobreaviso e
  quando ele deve ser pago" casava `^(a|o)…deve`; tightening para posição de
  diretiva (corrigido).
- `public_editorial_body_title_case_run` (2 registros, trab-audiencia-por-video):
  nome próprio jurídico Title-Case fora da allowlist. PENDENTE.

**RAIZ DO PASSO 12 ENCONTRADA E CORRIGIDA (commit cc53c112, DEC-017):** o build
`repairPublicHeadingPrepositionChainSlot`, para conteúdo autoral v2 de eixos
vazios, INVENTAVA um H1-molde doorway ("Cobertura de saúde em situação
documentada") e SUBSTITUÍA o H1 autoral real ("Junta médica: o desempate técnico
da RN 424/2017") — invenção de prosa pública pela máquina (viola DEC-004/DEC-017),
e o molde trazia o resíduo que o gate reprovava. Guard DEC-017 aplicado (v2 mantém
o heading autoral). O reparo MASCARAVA detectores v1; gateá-lo expõe uma CASCATA
de falso-positivos desses detectores em prosa autoral NATURAL (de-chain calibrado;
restam outros).

**MÉTODO DE REPRODUÇÃO (a chave — usar na continuação):** teste Go no pacote
`refinedpublicprose` chamando `ProbeBuildPipelineRecordsWithStageTimings("../..",
2000, nil)` (com `mechanicalClosureDisabled.Store(true)`), achando o registro
bloqueado nos `records` e imprimindo o campo+substring do resíduo. Isso reproduz
EXATAMENTE o gate do passo 12 e mostra qual reparo corrompe qual campo. Bissectar:
(a) se o campo é molde inventado → gatear o reparo por DEC-017 (como o H1); (b) se
o detector reprova prosa natural → calibrar o detector (como de-chain). Repetir até
`ProbeBuildPipeline` reportar 0 blockers, então `bootstrap-chain --from 12`.

**ISOLAÇÃO PRECISA do passo 12 (2026-07-09 tarde, investigação profunda):** a
corrupção que reprova `saude-o-que-e-junta-medica` (stacked_prepositions) NÃO está
no candidato, NÃO no slot-rewrite, NÃO no detector. Provado por teste Go: (a)
candidato limpo (0 stacked em todos os campos); (b) aplicar o slot-rewrite
(`normalizePublicTextSlotPTBRUncached`) em cada campo + `AnalyzeRecord` → CLEAN
(ReleaseBlocker=false); (c) o build COMPLETO reprova. Logo a corrupção é de uma
transformação a nível de REGISTRO aplicada DEPOIS do slot-rewrite. Gatear 4
funções por DEC-017 (slot-rewrite; repairOperationalPolishRecord;
repairRecordGenericEvidenceSentenceMold; rebalanceContactHistoryPhraseRecords) NÃO
resolveu: gatear o slot-rewrite PIOROU (2→6, ele fixa resíduos reais); gatear as 3
de registro não mudou (count 2, sem regressão). Restam ~35 transformações
`repair*/rewrite*Record*` a bissectar. **Próximo passo: teste Go que constrói o
registro refinado COMPLETO (via buildInitialRefinedRecords) de junta-medica e
imprime o campo+substring do par empilhado, bissectando qual transformação o
introduz; então gateá-la por DEC-017 (mantendo o slot-rewrite que fixa resíduos).**

**ACHADO PROFUNDO no passo 12 (investigado, não resolvido — decisão deliberada
pendente):** o gate que reprova roda a audit `publicproselanguagepatterns` sobre
o texto que o refined CONSTRÓI, não sobre o candidato. O candidato de
`saude-o-que-e-junta-medica` está LIMPO (teste Go direto: 0 stacked), mas o texto
refinado reprova `stacked_prepositions`. Causa: `normalizePublicTextSlotPTBRUncached`
(refined.go:12180) aplica ~40 reparos mecânicos `repair*/rewrite*` à prosa —
maquinário v1 SEM guard `mechanicalClosureDisabled`. Experimento: gatear pela
DEC-017 (retornar texto autoral intacto no v2) **PIOROU** o count (2→6) — ou seja,
a reescrita FIXA resíduos reais dos candidatos (6→2), não só corrompe. Interação
complexa: a reescrita tanto conserta "de no" quanto pode achatar acento ("nó"→"no").
NÃO é fix pontual nem guard cego — requer decidir deliberadamente: (a) limpar os
resíduos PT-BR na FONTE (candidatos, via redator/auditor com checagem de resíduo)
e então desligar a reescrita v1 (DEC-017 pleno); ou (b) corrigir o reparo
específico que deixa/introduz o par no refinado. Guard revertido (worktree limpo).

**PRÓXIMO PASSO (regra anti-loop do dono): censo da família, não correção
reativa.** Enumerar TODOS os códigos de detector que reprovam os 590 candidatos
(escrever pequeno cmd Go que roda `publicproselanguagepatterns` sobre
public_prose_candidate.jsonl e tabula códigos+contagens), separar falso-positivo
(prosa autoral legítima) de defeito real, calibrar os detectores em lote (RAW vs
normalizado; allowlist de proper-nouns jurídicos; posição de diretiva), então
retomar `tools/bootstrap-chain --from 12`. Depois: languagetool-release na cadeia
do verdict (ver diagnóstico), passos 13-33, verdict. Estado resumível.

## Atualização 2026-07-09 (LER PRIMEIRO)

**Marcos de hoje (commits):**
- `dcc560fa` — destrava elos 24-28 da cadeia (external-dedupe aceita corpus limpo;
  semantic-cluster aceita fila vazia sob manifesto; contextual/rehearsal
  regenerados); **command-ledger 1,676 GB → 151 MB** (correção na fonte:
  `currentGitDirtyPathStates` não expande mais diretório ignorado não-material; *(Desde 2026-08-29 o padrão EXPANDE: o `go.mod` traz `ignore ./var`, e a proibição permanece por ser comando full-tree pesado — DEC-039.)*
  compactação para frente preservando os 4.048 registros). Recovery snapshots
  `.stale-*`/`.poisoned*` no `.gitignore`.
- `e4ac5741` — **10 arquivos do censo reparados** (lei vigente conferida na fonte
  VIVA, fontes viradas em deep-links com proveniência 2026-07-09). Achado crítico:
  "Súmula 95 do STJ" era lei FALSA (é a Súmula 95 do **TJSP**; a do STJ é ICMS) —
  corrigido. FGTS dia 20 (Lei 14.438/2022), art. 169 CP caput, RN 465/2021 no
  lugar de CONSU 11/1998 revogada, etc.

**Diagnóstico do verdict N=209 → 0 passed: `docs/goal/DIAGNOSTICO_VERDICT_N209.md`.**
Achado central: o verdict exige oráculos em modo **RELEASE (full-corpus)**, mas o
`bootstrap-chain` gera em modo **AMOSTRA**. A maioria das 59 razões do verdict era
leitura STALE. `sca_scorecard` NÃO bloqueia o verdict (0 ocorrências).

**Caminho estrutural para verdict_passed > 0 (próximos passos precisos):**
1. **languagetool**: cadeia do verdict deve rodar `generate-languagetool-quality-release`
   (full-corpus, service_required) — não a variante amostra.
2. **morphsyntax**: hoje é diagnóstico minúsculo hardwired-blocked (`--limit 4`,
   `--max-sample-chars 180`; `validate_record` exige `public_release_blocked=True`).
   Precisa virar gate release full-corpus via **spaCy** (Stanza 1.13 não tem PT-NER
   oficial; spaCy é o motor de NER e `detect_broken_legal_entity` já usa spaCy).
   Detectores usam OR entre motores + fallback regex → spaCy-only full-corpus é
   viável e escalável; Stanza fica no diagnóstico amostral. Mudança coordenada:
   script generate + script validate_record + Go `ValidateRelease` (stanza
   `requireNER=false`). É deep-check obrigatório no mass fan-in
   (`qualityOracleDeepCheckRequiredForMassFanIn`), então bloqueia até virar release.
3. **external_dedupe**: fix de gate feito (dcc560fa); regen fresco zera.
4. **Conteúdo** (gate corpus-wide, all-or-nothing): languagetool ~123/209 páginas
   com gramática real (contar de novo após chain fresco pós-reparo); fontes raiz
   (`broad_official_source_url`); cta_contextual; oab_paid_intent. Estratégia:
   após chain fresco, medir residual REAL e limpar por workflow OU provar a cadeia
   num subconjunto genuinamente limpo (manifesto dirige N — DEC-014).

**Sequência de retomada:** (a) plumbing de oráculo release (morphsyntax +
languagetool-release na cadeia do verdict); (b) chain fresco pós-reparo → ler
verdict verdadeiro; (c) limpar residual de conteúdo; (d) verdict_passed > 0.

---

Última atualização anterior: 2026-07-08 (sessão Claude — ULTRAPLAN aprovado pelo dono)

> **PLANO VIGENTE: `docs/goal/ULTRAPLAN.md`** (aprovado 2026-07-08). Contém o diagnóstico
> medido (3 agentes + validação de código) e o ultraprompt de execução P0→P5. Sessão nova:
> ler ULTRAPLAN.md junto com este STATUS antes de agir.

## Onde estamos

| Fase | Estado |
|---|---|
| Fase 0 — Investigação | **concluída** (PLAN.md §1, BUGLOG.md, DEC-001) |
| Fase A — Governança e destravamento | **concluída** (DEC-002; pré-commit leve, aprovador de release, ledger congelado) |
| Fase B — Fábrica de conteúdo v2 | **em andamento** (portfólio 6.353 pronto; ~357/6.269 páginas escritas; cadeia desacoplada DEC-014; ferramentas de oráculo instaladas) |
| Fase C — Suíte leve | **concluída** (BUG-004; cache tipado, −17% CPU) |
| Fase D — P0 (publicar 10.000) | pendente (depende da escrita acumular + regeneração de produção) |
| Fase E — P1 (100k candidatos) | pendente (portfólio 6.353 é a base; expandir via leis/súmulas/verbetes) |
| Fase F — P2 (fontes oficiais) | pendente |
| Fase G — P3 (benchmark 1M) | **concluída** (benchmark real de 1M, não-O(n²), claim destravada — SCALE.md) |
| Fase H — P4 (operação) | pendente (release estático + rollback drill) |
| Fase I — P5 (traffic-ready) | **preparada** (tunnel + nginx validados; domínio não publicado); busca Bleve servida pendente |

## Contadores vivos (medidos, não declarados)

- `published_manifest`: 0 registros (arquivo vazio).
- Estoque bloqueado: 300 drafts + 9.700 expansões (reprovados no mérito — DEC-004).
- `verdict_passed`: 0/10.000.
- `.git`: 17 GB (ledger histórico); ledger de comando: 1,76 GB, congelado pela DEC-002.

## Caminho crítico do P0 (para retomada) — 2026-07-07

O gargalo é volume de redação (multi-sessão). Sequência:
1. **Escrever + revisar ~6.269 páginas** em lotes por família — duas filas idempotentes MUTUAMENTE EXCLUSIVAS (interseção 0 provada; rodar UMA por vez para não haver trabalho concorrente):
   - **Escrita** (preenche faltantes): `bash ops/relaunch-writing.sh` → `Workflow({scriptPath:"scripts/workflows/writing-mass-todo.js"})`. Idempotência por CONJUNTO de intent_ids vs slice do portfólio (não contagem cega); injeta fontes auditadas por área (`data/editorial/v2_area_sources.json`) e `reuse` (páginas válidas preservadas). Tombstone `{"skipped":true,"skip_reason":...}` conta como slot (pulo honesto não re-enfileira).
   - **Revisão** (corrige defeitos dos completos): `bash ops/relaunch-review.sh` → `Workflow({scriptPath:"scripts/workflows/writing-review-todo.js"})`. Detecção 100% pelo **auditor canônico** `tools/audit_v2_pages.py --global` (espelha o gate Go; n-gram/heading/title cross-arquivo); injeta `alvos` {classe: [intent_ids]}. Arquivo incompleto fica FORA (pertence à escrita).
   - **NUNCA usar resumeFromRunId** (re-executa lotes já em disco). **Circuit breaker embutido**: janelas de 8 lotes; janela ~toda falhando (rate limit) para o workflow — retomar com o helper na próxima janela.
   - **Auditoria ultracode 2026-07-08** (commit b882587): fórmula de word_count unificada com o gate (253/594 páginas normalizadas mecanicamente por `tools/generate-v2-word-count-refresh`); `needs_source_research`/`skipped` agora REPROVAM na ingestão; n-gram 12+ cruza estoque existente no gate. WAF gov.br bloqueia UA custom → checks de vivacidade usam UA de navegador (decisão documentada em v2_area_sources.json). **Correção 2026-07-08 (investigação ULTRAPLAN): `data/source-audit/v2_source_provenance.jsonl` NÃO existe em disco — a persistência de proveniência prometida aqui ainda precisa ser implementada (frente E4 do ULTRAPLAN).**
   - **Integrar**: `python3 tools/audit_v2_pages.py --global` e commitar só arquivos `ok`. Fila de revisão pendente: 30 arquivos (fonte_nao_verificada 35, ngram_dup_global 34, thin 18, meta 17, secoes_min 12) — rodar quando a escrita pausar.
2. **Ingerir** com `cmd/ingest-v2-pages` (todos os v2_pages → estoque de N páginas; atualiza `stock_manifest.json`).
3. **Regenerar a cadeia em N=produção** na ordem de bootstrap descoberta (DEC-015): mover refined stale → `generate-authorial-mass-editorial-quality-vectors` (bootstrap from stock) → `-publication-readiness` → `-public-prose-candidate` → `generate-refined-public-prose` (com oráculos rodando: iniciar LanguageTool server porta 8081; Vale/python já instalados) → oráculos PT-BR → `-legal-reviews` → `-release-evidence` → `-release-transaction` → `-manifest-transaction` → `generate-scaled-content-release-verdict`. Em N=10.000 os hardcodes de contagem estão satisfeitos (não bloqueiam como bloqueavam n=34).
4. **Promover**: `cmd/approve-public-release` (grava promotion_manifest aprovado após gates) → `tools/run-promote-authorial-mass-public-release --allow-public-write --expected-manifest-records=10000`.
5. **Verificar**: `check p0-cycle-close-indexable-10k`; smoke HTTP/Googlebot; leitura de amostras.

Selecionar exatamente 10.000 aprovadas (portfólio tem 6.517; expandir via leis/súmulas/verbetes comentados — WAVE_BRIEFS tem os briefs). Frente paralela: servir Bleve em /buscar/ (P5, SCALE.md). **Correção 2026-07-08:** o benchmark 1M (P3) está CONCLUÍDO — `cmd/bench-scale-1m` existe (444 linhas) com evidência real em `data/ops/scale_1m_benchmark_evidence.jsonl` (1M em 3 backends, não-quadrático).

## Manutenção pendente (janela ociosa, NUNCA com agentes ativos)

- ✅ **`git gc` EXECUTADO em 2026-07-08 (ULTRAPLAN E1 parcial): `.git` de 16,8 GiB → 3,1 GB** (repack completo, 0 objetos soltos). gc.auto continua 0 — rodar gc manual de novo só em janela ociosa futura.
- Restante do E1 (aguarda janela sem agentes + atualização das regras que protegem os artefatos, com DEC): remover `.worktrees/` (26 GB, 17 worktrees mortas — inspecionar trabalho único antes), `.artifact-quarantine/` (1,1 GB), `*.test` da raiz (~330 MB).
- Pre-commit otimizado (2026-07-08): build Go só quando o commit toca Go/go.mod/go.sum; commit de conteúdo custa ~1s (antes: ~5 min de CPU por religação de 504 pacotes).

## MARCO 2026-07-09: cadeia completa 28/28 fecha em N=209 (commit e06c7a4b)

Primeira travessia stock→verdict→manifest da história do repo, com conteúdo v2
autoral intocado (0 corrupção, todos os oráculos verdes, incl. LanguageTool/
hunspell/morphsyntax). `tools/bootstrap-chain` é o comando canônico (ordem
provada: verdict ANTES de manifest; detox automático de camadas stale no passo 0).

**Verdict atual: 209 registros, 0 passed** — blockers enumerados (o caminho até
verdict_passed>0):
1. Camadas fora do bootstrap ainda: `external_dedupe_oracle` (simhash/hnsw),
   `semantic_cluster_index`, `contextual_public_page_review`,
   `official_source_recheck/live` — acrescentar os geradores aos STEPS.
2. `public_prose_broad_official_source_url` — fontes raiz/amplas remanescentes
   → fila de revisão (trocar por deep-link verificado, como feito no BCB).
3. Censo editorial adversarial (data/ops/censo_editorial_findings.jsonl):
   **base legal desatualizada FGTS dia 7→dia 20 (Lei 14.438/2022/FGTS Digital)**
   em 3+ páginas, truncamentos residuais na FONTE e promessas de seção não
   cumpridas → fila de reparo de agentes + upsert (`ingest -mode upsert`).

## Execução do ULTRAPLAN — sessão 2026-07-08 (tarde)

- **E2 ✅** (commit f577f5d): caches persistentes (GOCACHE + binários em `.cache/go-cmd-bin`); wrapper de comando cacheado: 6,1s → 0,22s/invocação (28×) — awareness de 7 comandos git virou opt-in (`WIKI_REPO_AWARENESS_FULL=1`); appends no command-ledger de 1,76 GB viraram opt-in (`WIKI_HEAVY_FORCE_LEDGER=1`, DEC-016 executa a DEC-002 no produtor).
- **E4 ✅** (commit 8e307e6): fila de reescrita reconciliada na ingestão (as 36 entradas eram 100% entulho pré-DEC-013 — todos os intents já ingeridos); auditor canônico persiste `data/ops/v2_audit_report.jsonl` (primeiro registro gravado: 632 páginas, 12/40 arquivos ok); proveniência v2 já estava wired e materializa na próxima ingestão.
- **E3 (DEC-014 fechada) ✅** (commit 45a9ae24): limiar de massa do verdict + count gates do refined + piso de auditoria do patterns agora manifest-driven (`EffectiveReleaseMinimum`); em N<10.000 com manifesto os oráculos são EXIGIDOS (ensaio prova a cadeia de verdade); produção v1 idêntica; suítes verdes nos 3 pacotes.
- **E3b write-if-unchanged**: `internal/jsonlwrite.RenameIfChanged` aplicado aos 16 writers da cadeia (13 arquivos) — rewrite byte-idêntico preserva mtime e estanca o ripple de falso-stale. **E3a**: `tools/bootstrap-chain` criado (28 passos na ordem DEC-015, `--list/--from/--until`, stop-on-fail).
- **Teste com skew de transição conhecido**: `TestGenerateRejectsStaleReleaseEvidenceAfterAuthorialStockRewrite` (releasetransaction) lê o `release_evidence` VIVO (v1 stale, 10k) e os drafts VIVOS (34 v2) — vermelho desde a troca de estoque DEC-012, alheio ao diff de hoje; cura natural na regeneração E5 (re-rodar o pacote após o bootstrap N≈632).
- **C2 em andamento**: fila de revisão relançada (28 arquivos; defeitos: ngram_dup_global 36, fonte_nao_verificada 35, ngram_dup 20, meta_len 17, heading_generico 3, fontes_host 2). Circuit breaker funcionou no limite de sessão de 13:40.

## Para retomar numa sessão nova

1. Ler `docs/goal/PLAN.md` (plano), `DECISIONS.md` (autoridade e racional), `BUGLOG.md` (defeitos estruturais).
2. Conferir esta tabela de fases e continuar da primeira não concluída.
3. Regras de governança vigentes: DEC-002 (pré-commit leve, ledger congelado, gates de produto). Não retomar a burocracia antiga do AGENTS.md histórico.
4. Comandos úteis: `./tools/go-modern build ./...`; `./tools/go-modern run ./cmd/check <nome>`; conteúdo em `data/editorial/`; conhecimento novo em `data/knowledge/`.

## Registro de marcos

- 2026-07-05: Fase 0 concluída. Diagnóstico do loop (DEC-001), auditoria de conteúdo (DEC-004), mapa da cadeia de release (BUG-001). PLAN/DECISIONS/BUGLOG/STATUS criados.
- 2026-07-05: Fase A parte 1 commitada (09b150c): pré-commit leve, adendos de regime em AGENTS.md/GOAL.md, docs/goal/.
- 2026-07-06: BUG-001 corrigido — `internal/publicrelease/approval.go` cria o produtor legítimo do `promotion_public_write_approved`, com revalidação de verdict (todos passed, zero blockers), staging report SHA e campos estáveis; wiring no promote CLI entre MaterializeTemporaryPublicPlan e BuildPromotionSwapPlan. 7 testes novos verdes.
- 2026-07-06: Fase B iniciada — PORTFOLIO_BRIEF.md, PORTFOLIO_PLAN.md (20 áreas, ~10.700 candidatos), WAVE_BRIEFS.md (subfamílias curadas), WRITING_SPEC.md, INGEST_SPEC.md.
- 2026-07-06: Pilotos do portfólio v2 aprovados na auditoria: trabalhista 345, saúde 207, glossário 350 — disciplina contrafactual real (agentes entregam ~60–85% dos tetos; onda suplementar será planejada na consolidação). Onda A disparada (previdenciário, consumidor, bancário, família, sucessões, imobiliário).
- 2026-07-06: Renderer v2 pronto (parágrafos múltiplos, listas, escape por segmento, rodapé público sem vocabulário interno, disclaimer em páginas indexáveis, marca "Wiki Jurídica"); testes verdes em render/build/httpserver/seo.
- 2026-07-06: Mapeamento do contrato mínimo de publicação concluído (DEC-009): cadeia se regenera do estoque; ~12 sítios de `/massa-juridica/` em retrofit para `/{area}/{slug}/`; esqueleto ops/ do P5 criado (DEC-010: nginx + tunnel dedicado, sem credencial).

## Plano realista de conclusão (2026-07-07)

O gargalo do P0 **não é engenharia** — é volume de redação por LLM (10.000 páginas de qualidade humana se acumulam ao longo de sessões; o limite de sessão foi atingido 2× em 06/07). Ordem de ataque:
1. **Arquitetura destravada** (quase completa): governança (DEC-002), aprovação de release (BUG-001), URL scheme (DEC-008), renderer v2, suíte leve, ingestão v2, completude proporcional ao page_type (DEC-013, em curso).
2. **Fatia vertical n=34 fecha** end-to-end (ingestão → 36 dependências do verdict → verdict_passed → staging isolado). Prova de que, quando as 10k páginas existirem, publicam. Marco técnico decisivo.
3. **Portfólio governado ~10k intenções** (P1 parcial) — workflow em curso, 20 áreas.
4. **Ondas de escrita** em lotes por família — o quanto o orçamento de sessão permitir por vez; motor pronto para retomar.
5. **P5 pronto** (feito: cloudflared valida OK, nginx/systemd preparados).

## Revisão de qualidade/indexabilidade das páginas v2 (gate de fim de fase)

Ferramenta `cmd/preview-v2-page` renderiza uma página v2 pelo renderer real e verifica o contrato. Amostras reais (2026-07-07):
- **Guia comercial** `/trabalhista/fgts-nao-depositado/`: 9.8 KB, 0 scripts, `index,follow,max-snippet:160`, canonical absoluto, title/meta/h1 naturais distintos, H2s específicos e variados ("Denúncia à fiscalização", "Atenção ao prazo: a prescrição de cinco anos"), 1.108 palavras com base legal (Lei 8.036/90 art. 15) citada. Bom para Googlebot indexar/citar e humanos lerem.
- **Verbete informativo** `/glossario/citacao/`: 5.3 KB, 0 scripts, robots ok, 500 palavras. URLs limpas e semânticas.

Contrato de HTML leve/indexável verificado end-to-end no renderer real. Este é o gate de qualidade que precede qualquer avanço de fase (diretriz do dono).

## Ferramentas de oráculo PT-BR instaladas (fábrica funcional)

Instaladas (self-hosted, open source, sem serviço pago) — reprodutível por `ops/setup-oracle-tools.sh`:
- Python: wordfreq, ftfy, simplemma, lexicalrichness (+nltk punkt), morphsyntax (torch-cpu, spacy, stanza) — invocadas pelos geradores `ptbr_*`.
- Vale (Go CLI, version master) — lint de prosa.
- LanguageTool (self-hosted, Java 17) — servidor local de gramática (`java -cp .toolchains/languagetool/LanguageTool-*/languagetool-server.jar org.languagetool.server.HTTPServer --port 8081`).

Sem esses oráculos os gates de qualidade PT-BR reprovariam por `input_stale`/cliente nil. São requisito de produção (N=10000); em N pequeno o gate de escala `requiredRefinedPublicProseRecordCount=10000` os pula.

## Locks — verificado (não há bloqueio)

`.cache/p0-factory-chain.lock` é `flock -n` advisory (liberado na morte do processo); com 0 processos Go ativos, está livre. Os geradores adquirem-no normalmente. Nenhum lock stale trava os agentes.

## Bloqueio residual da fatia vertical n=34 (não da arquitetura)

A cadeia v1 tem um **cold-start freshness deadlock**: readiness↔candidate↔refined dependem por mtime, e o downstream stale de 10000 não avança para 34 numa passada única (a cadeia v1 nunca foi construída "do zero", sempre incremental — o mesmo ciclo existe em N=10000). Adaptado o código (todas as camadas centrais regeneram em N=34: refinement, global_similarity, quality_vectors, candidate, readiness, contextcompat, scale_shards). O verdict end-to-end em N=34 depende de quebrar esse ciclo de bootstrap — trabalho em curso; será naturalmente exercido na regeneração de produção.

## Checkpoint 2026-07-07 (commits até b6rsxa30i)

Arquitetura destravada e commitada: governança (DEC-002), aprovação de release/BUG-001, URL scheme (DEC-008), renderer v2, suíte leve (BUG-004), ingestão v2, completude proporcional (DEC-013), **cadeia inteira desacoplada de 10.000 (DEC-014/BUG-006)** — total dirigido pelo manifesto, agrupamento por practice_area, pares proporcionais, produção v1 preservada (testes verdes). Portfólio 6.353 intenções commitado. Preview de qualidade prova páginas ≤10KB indexáveis. P5 (tunnel/nginx) validado. SCALE.md documenta P3/P5.

Frentes ativas: (1) workflow `writing-mass-full` (405 lotes/6.269 páginas em fila); (2) regeneração da cadeia n=34 até o verdict (agente focado, código já adaptado).

## Adaptação da cadeia ao manifesto (DEC-014) — progresso por elo

Cadeia do estoque ao verdict, adaptada para N do manifesto (produção 10000 idêntica):
- ✅ `refinement_quality` + `quality_vectors` (commit a61ee89): agrupamento por practice_area, pares proporcionais.
- ✅ `global_similarity_audit`: regenera limpo em N=34 (561 pares, similaridade 0.0000).
- ⏳ `public_prose_candidate` (hardcode `expected=10000` linha 41), `refined_public_prose`, oráculos PT-BR (`ptbrwordfreqquality`, `valepublicproselint`, `ptbrftfyoracle`, `sqlitefts5corpus`, `jsonlstream`, `ptbrlexicaldiversity` — todos `DefaultMinimumRecords=10000`), `contextcompat` (condicionais `if len==10000` que pulam em v2 — precisam rodar), `scale_shards`, e os validadores do verdict (`verdict.go:2853/2890`, `ossscaleintegration`, `checks.go:4531`).
- **NÃO tocar** (prova de escala P3): sondas de 1M/100k em `scaleindex`, `pebblescalesidecar`, `contentstorepebble`, `contentinventory*`, `parallelbatch.SyntheticProbeRecords`.

## Motores em execução (2026-07-07)

1. **Workflow portfólio v2** (22 áreas restantes + suplementares, incl. leis/súmulas comentadas) — entregas parciais em `data/editorial/portfolio_v2/`.
2. **Workflow Onda de Escrita 1** (saúde+bancário+família, 49 lotes, 819 páginas) — saída em `data/editorial/v2_pages/<slug>.jsonl`.
3. **Fatia vertical piloto (DEC-012)**: ingestão dos 34 pilotos → regeneração da cadeia n=34 → gates → staging bloqueado.

Pilotos de escrita aprovados na revisão jurídica (FGTS 14 páginas, verbetes processo civil 20 páginas — corretas, atuais, com MPs 2025/2026 verificadas ao vivo, zero molde). Ferramenta de ingestão commitada (`70348a8`).

## Pendências de configuração do dono (para o launch, não bloqueiam a fábrica)

- ~~`content/cta_policy.json`: `phone_placeholder` — configurar o número real de WhatsApp antes do launch.~~ **RESOLVIDO 2026-08-04:** o canal vive em `.env.local` (`WIKI_WHATSAPP_PHONE`), é resolvido em tempo de render por `internal/contactchannel` e materializa só em `/contato/advogado/`. Número em `content/` ou em página é regressão — há teste de contrato que reprova (`internal/contract/cta/contact_channel_contract_test.go`).
- Chave/credencial do Cloudflare Tunnel (P5 deixa tudo preparado sem ela).

## Atualização 2026-07-09 (noite) — ENSAIO N=590: passos 12-20 destravados

Cadeia `authorial_mass` regenerada em N=590 (stock_manifest drafts_expected=590). Passos 1-20 passam ponta-a-ponta:
- **Passo 12** (`refined_public_prose`): 590 registros, 0 molde (H1/title/summary == candidato) sob DEC-017.
- **Passos 13-19**: language_patterns, languagetool, vale, wordfreq, ftfy, lexical_diversity, spellcheck — todos verdes (allowlist de domínio ampliada para termos jurídico-médicos legítimos; erro real nunca entra).
- **Passo 20** (`ptbr_morphsyntax_evidence`): **destravado**. Dois problemas resolvidos com causa raiz:
  1. **Perf (P0)**: `nlp.pipe` (batch) + `disable=["parser"]` no passe release → 180s (timeout) → **116s**. Escala para 10k.
  2. **Gate (120 falsos-positivos → 0)**: os detectores spaCy-only reprovavam prosa jurídica legítima (imperativos PT taggeados como NOUN, split de sentença em dois-pontos, NER truncado). Fix **não-relaxante**: `sentence_without_verb` vira gate **dual-engine em nível de segmento** (spaCy marca, Stanza confirma — Stanza acerta imperativo PT); `broken_legal_entity` texto-determinístico (para de confiar no span do NER fraco); `meta_description` isenta (campo nominal SEO); locução adverbial "para trás" guardada. Controles do diagnóstico continuam disparando (gate intacto). `public_release_blocked=false`, `release_blocked_record_count=0`. Validado por auditoria adversarial.
- **Próximo**: passos 21-33 (verdict + manifest). Bloqueador latente conhecido no verdict: `ValidateRelease` rejeita `coverage_status` contendo "sample" (a constante do produtor tem "stanza_sample_cross_check") — a corrigir quando o verdict reportar.

## Atualização 2026-07-14 (Claude) — cadeia reordenada (42 passos), corpus limpo, fábrica de escrita+review em produção

**Numeração mudou: a cadeia agora tem 42 passos** — `generate-content-inventory-parquet` e
`generate-content-inventory-arrow` entraram como passos 13-14 logo após o refined (o gate
languagetool valida o sidecar parquet contra o refined vivo; sem regenerá-los na cadeia, qualquer
regeneração do refined deixava o sidecar stale). Fonte de verdade: `bootstrap-chain --list`.

Cadeia N=590 avançou do passo 13 ao 23 com causa-raiz corrigida em cada elo (nunca gate relaxado):
LanguageTool 6.8 restaurado com M2 persistente em `.toolchains/`; mínimos de inventário dirigidos
pelo stock_manifest (DEC-014) em parquet/arrow; montagem canônica única de visible text
(`contentinventoryparquet.JoinVisibleTextSlots`) consumida pelo languagetoolquality; detector de
conectivo pendurado com contexto ("a partir de quando", "pesa contra" não são fragmento);
fronteira vazia de pares near-duplicate legítima no rescoring sob manifesto; refined regenerado
como passthrough DEC-017 (27→4 refinement_changed; 2 headings mutilados em 11/07 restaurados).
**Parado no passo 24 (spellcheck)**: "Natjus"→NatJus corrigido na fonte + allowlist; "concluíem" é
mutação mecânica em 1 dos 4 registros ainda envenenados — mutador fura o guard DEC-017 mesmo com
plano de reescrita VAZIO; especialista investigando o caminho exato para blindar (depois: regenerar
refined e retomar `--from 13`, passos 13-23 são rápidos/cacheados).

**O bloqueador latente do verdict documentado em 09/07 (coverage_status com "sample") JÁ ESTÁ
resolvido** — o produtor usa `full_corpus_release_..._diagnostic_cross_check_no_publication`
(scripts/ptbr_morphsyntax_oracle.py:90); não há mais token "sample" no coverage_status.

Fábrica de escrita: 1ª janela (6 lotes lgpd) reprovou honestamente no auditor — `ngram_dup_global`
de citações de caput contra o estoque de 4.5k páginas que o redator não vê. Prompt-base corrigido
(writing-mass.js regra 2: proibida a construção canônica "o art. X garante/assegura..."), filas
regeneradas e rodando: **escrita 122 lotes/1.849 páginas** (telecom_energia-03..14 reservados à
frente Codex) + **review de 117 arquivos** (309 ngram_dup_global, 38 metadados de proveniência,
headings/fontes/title). Estoque v2 físico: ~4.6k páginas e crescendo.

Próximo: (1) refined blindado + `--from 13` → morphsyntax → verdict (passo 41) até
`verdict_passed>0` em N=590; (2) escrita+review até esgotar filas; (3) com verdict verde,
promover o corpus aprovado via release transacional (publicação local; DNS segue em P5).
