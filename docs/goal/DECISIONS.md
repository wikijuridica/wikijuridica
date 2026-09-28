# DECISIONS.md — Decisões arquiteturais e jurídicas do /goal

Autoridade: o `/goal` ativo (2026-07-05) instrui o agente a atuar como engenheiro sênior + advogado brasileiro, com autonomia técnica e jurídica plena sobre P1–P5, e autoriza expressamente atualizar regras dos contratos que não fizerem mais sentido para a nova engenharia, registrando o raciocínio aqui.

---

## DEC-001 — Diagnóstico da causa raiz do loop do Codex (Fase 0)

**Decisão:** tratar o loop de ~400 ciclos sem publicação como defeito estrutural de governança, não como sequência de bugs pontuais.

**Evidência:**
1. **Deadlock de código:** a promoção exige `.release-staging/promotion_manifest.json` com `Status="promotion_public_write_approved"`, mas o único escritor (`internal/publicrelease/publicrelease.go:1242`) grava sempre `promotion_prepared_blocked_by_default`. Não existe produtor do status aprovado em todo o repo. A porta não tem chave (BUGLOG BUG-001).
2. **Gates que apagam produto:** em 2026-06-29, 8.263 páginas publicadas no manifest foram zeradas por gate de auditoria (`data/audits/published_manifest_publication_zero_correction_2026-06-29.jsonl`) porque a cadeia de flags transacionais não tinha caminho de abertura (BUG-002).
3. **Processo medindo o processo:** ~52% dos commits tocam maquinário de guarda; 277 scripts `check-*`; ledger de comando com 1,76 GB commitado (`.git` = 17 GB); 324 de 381 ciclos gastam esforço "provando que não publicaram"; a doutrina anti-"falso verde" converte cada check que passa em obrigação de endurecer, gerando gates novos que reprovam trabalho anterior (BUG-003).
4. **Contrato que invalida a si mesmo:** o registro de "leitura viva do HEAD" exigido pelo pré-commit é invalidado pelo próprio commit que ele autoriza — esteira infinita por design.

**Consequência:** qualquer correção "de sintoma" (mais um gate, mais um refinamento) alimenta o loop. A correção de causa é redesenhar a governança (DEC-002) e criar o caminho de abertura da publicação (DEC-003).

## DEC-002 — Nova governança: gates medem o produto, não o processo

**Decisão:** substituir a burocracia processual por regras mínimas e verificáveis:
1. **Ledger congelado:** `.agents/runtime/command-ledger.jsonl` deixa de receber appends e deixa de ser exigido no pré-commit. Permanece no histórico (correção só para frente, sem reescrita de história).
2. **Pré-commit leve:** compilação (`go build ./...` via wrapper) + `go vet` nos pacotes tocados. Gates de conteúdo/SEO rodam como parte do pipeline de release, onde pertencem, não a cada commit de código.
3. **Checks de processo desativados como gate:** `work-reuse-ledger`, `agent-context-ledger`, `parallel-codex-operational-contract`, `engineering-now-contract` saem do pré-commit. O código permanece (sem deleção), mas não bloqueia mais o trabalho.
4. **Documentos de contrato:** `AGENTS.md`/`GOAL.md` ganham um adendo declarando este regime; `docs/goal/` passa a ser o estado operacional vivo.

**Racional:** a meta do repositório é publicar 10.000 páginas jurídicas de qualidade e escalar a milhões. Toda regra que consome engenharia sem melhorar o produto público é custo puro; a evidência (DEC-001) mostra que esse custo capturou o projeto inteiro. O `/goal` ativo autoriza expressamente esta atualização de regras.

## DEC-003 — Criar o produtor legítimo do promotion manifest aprovado

**Decisão:** implementar o elo ausente: um comando de aprovação (`cmd/approve-public-release` ou equivalente) que, **somente após** os gates de produto passarem (qualidade, unicidade, fonte, OAB, HTML leve, smoke), grava `promotion_manifest.json` com `promotion_public_write_approved` e flags abertas, permitindo que `tools/run-promote-authorial-mass-public-release` execute a transação real.

**Racional:** publicação bloqueada por default é correto; publicação **impossível** por default é bug. O gate final passa a ter dono, critério objetivo e trilha de auditoria.

## DEC-004 — O estoque atual de 10k não é publicável; a fábrica de conteúdo será refeita

**Decisão (como advogado e editor-chefe):** os 10.000 textos bloqueados atuais reprovam no mérito editorial — são permutação de molde (12 headings idênticos ×4.599 registros, 14.327 pares near-duplicate, distância de Hamming mínima 0, frases mecânicas em 100% da amostra, 27 seed terms para 10.000 páginas). Publicá-los violaria as diretrizes do Google (scaled content abuse / doorway) e o próprio `/goal` ("never mechanical, templated or AI-sounding"). A fábrica de conteúdo será redesenhada (PLAN.md fase B) para gerar substância única por página a partir de uma base de conhecimento jurídico autoral (leis, prazos, documentos, procedimentos, órgãos por tema), com variação estrutural real e profundidade variável, reaproveitando do estoque atual apenas o que tem valor: a taxonomia de intenções, as fontes oficiais específicas (23.366 deep-links auditados) e os metadados de demanda.

**Racional jurídico:** conteúdo jurídico informativo com CTA de contratação digital deve ser sóbrio e tecnicamente correto (Provimento OAB 205/2021); texto-molde em massa também é risco reputacional/disciplinar, não só risco de SEO.

## DEC-005 — Redefinição de P5 e escopo das fases (autoridade do /goal ativo)

**Decisão:** o `/goal` ativo do usuário redefine P5 como "preparar para o mundo": Cloudflare Tunnel configurado/preparado + proxy (nginx ou superior justificado), domínio `wikijuridica.com.br` **não publicado** (sem chave Cloudflare). As capacidades de "inteligência própria" do P5 histórico (grafo, MinHash/SimHash/LSH, Bleve etc.) são absorvidas onde forem necessárias às fases anteriores (a dedupe escalável já é requisito de P0/P3). Fases operativas:
- **P0** = 10.000 páginas públicas indexáveis aprovadas (contrato inalterado).
- **P1** = ≥100.000 candidatos governados (inventário bloqueado com lineage e gates computáveis).
- **P2** = cobertura ampla de fontes oficiais (proveniência, nunca cópia).
- **P3** = benchmark reproduzível de capacidade para 1M de URLs em inventário, sem O(n²).
- **P4** = operação de produção: release estático versionado, promoção atômica, rollback comprovado.
- **P5** = servidor pronto para tráfego (tunnel + proxy preparados, domínio não ativado).

**Racional:** o usuário tem precedência sobre o anexo histórico do Codex; as exigências processuais do anexo (10 agentes, 5 revisores nomeados etc.) são substituídas pelo uso proporcional de subagentes desta sessão, registrado neste diretório.

## DEC-007 — Novo portfólio editorial: não cartesiano, misto e com teste contrafactual

**Decisão:** a taxonomia atual (27 seeds × cenário × contexto = 10.000 intenções) é substituída. Evidência: dentro de um único seed ("guarda compartilhada") há ~360 páginas que diferem apenas por modificadores genéricos ("em PDF", "WhatsApp advogado", "empresa com CNPJ"), incluindo combinações juridicamente sem sentido ("guarda compartilhada cobrança indevida com comprovantes"). Isso é doorway por definição e viola a seção 16 do anexo do goal ("A expansão cartesiana é proibida").

O novo portfólio de 10.000 páginas será composto por intenções **materialmente distintas** (teste contrafactual: a dimensão só cria página se mudar regra, procedimento, documento, prazo, risco, fonte ou resposta útil), com mix de tipos de página:
1. **Guias de problema com intenção de contratação** (lane comercial, CTA WhatsApp contextual) — núcleo do negócio: trabalhista, previdenciário comercial (sem BPC/LOAS), consumidor, bancário, saúde suplementar, família/sucessões online, imobiliário, LGPD, INPI, tributário PJ/MEI, contratos B2B, seguros, telecom, energia, transporte aéreo, trânsito.
2. **Perguntas jurídicas específicas** (Q&A de cauda longa real, lane por classificação).
3. **Verbetes de institutos/termos jurídicos** (informativo, autoridade e citabilidade por bots de IA).
4. **Guias de procedimento digital** (gov.br, Meu INSS, consumidor.gov.br, cartório online, juizado especial — jornada 100% digital real).

**Racional:** nenhuma área jurídica sustenta 360 consultas reais distintas por seed; o mix informativo+comercial cobre a meta de 10.000 sem inflação cartesiana, preserva o negócio (núcleo comercial com paid-intent no corpo) e constrói autoridade tópica que os guias comerciais herdam por links internos. BPC/LOAS e assistência permanecem informativos/noindex conforme contrato.

**Reaproveitamento:** o schema/contêiner `authorial_mass_*` e toda a cadeia de release são mantidos; troca-se o payload (intenções + corpos). Fontes oficiais auditadas (23.366 deep-links) e infraestrutura de gates continuam válidas.

## DEC-008 — Esquema de URL público: `/{area}/{slug}/` em vez de `/massa-juridica/...`

**Decisão:** as URLs públicas seguirão o padrão semântico `/{practice_area}/{intent-slug}/` (ex.: `/trabalhista/fgts-nao-depositado/`, `/glossario/tutela-de-urgencia/`, `/planos-de-saude/negativa-de-home-care/`). O prefixo atual `/massa-juridica/` (hardcoded em `internal/authorialmassreleasetransaction`, `internal/authorialmassreleaseevidence`, `internal/authorialmassmanifesttransaction`) é vocabulário interno vazando para a URL pública e será substituído.

**Racional:** URL é sinal de SEO e de confiança; "massa jurídica" comunica exatamente o que o Google pune (conteúdo em massa). Áreas como segmento de URL criam hubs naturais (`/trabalhista/`) para arquitetura de links internos.

## DEC-009 — Arquitetura da Fase B: retrofit da cadeia authorial_mass com estoque v2

**Decisão:** manter a cadeia de release existente (stock → quality vectors → readiness → legal reviews → release evidence → release transaction → manifest rehearsal → verdict → promoção) e **substituir o estoque** (drafts + expansion) pelo conteúdo v2. Fundamentos do mapeamento (agente de exploração, 2026-07-06):
- Toda camada derivada se regenera a partir do estoque via `cmd/generate-*`; o caminho barato e correto é regenerar a cadeia inteira, nunca editar camada derivada à mão.
- `internal/publicrelease` e `internal/checks` são agnósticos ao esquema de URL; o prefixo `/massa-juridica/` vive em ~12 pontos mapeados (release_evidence 1082/1168/1182, release_transaction 631/1103, verdict 1921, manifest_transaction 1526/2209, unlockconsistency 494-612, controlledpromotion 485, rca 1362, 2 CLIs) que serão alterados juntos para `/{practice_area}/{slug}/` (DEC-008).
- O slug é derivado de `slugFrom(SeedTermID, ScenarioID, ContextID)` e conferido em release_evidence.go:1168; os registros v2 preencherão a tripla de forma que o slug derivado = slug da intenção (detalhe de implementação registrado no código).

**Fluxo de produção v2:** redatores (subagentes) entregam páginas no formato de `WRITING_SPEC.md §7` em `data/editorial/v2_pages/<area>.jsonl` → ferramenta de ingestão converte para o schema do estoque → cadeia regenerada → oráculos de produto reais (external_dedupe SimHash/HNSW, LanguageTool, ptbr_*, Vale) julgam → reprovados voltam para fila de reescrita → aprovados seguem para manifest/verdict/promoção com o aprovador da DEC-003.

## DEC-010 — Serviço de produção: nginx estático + Go como fallback, atrás de Cloudflare Tunnel próprio

**Decisão:** produção serve conteúdo público como **release estático imutável** (`releases/<id>/public`, symlink `releases/current` como ponteiro atômico — P4) via **nginx** em `127.0.0.1:8081`, com o binário Go (`cmd/server`, :8080) como controle/preview/fallback dinâmico (health, busca noindex, geração on demand na transição). Exposição por **Cloudflare Tunnel dedicado** `wikijuridica-local` (config em `ops/cloudflared/`, unit em `ops/systemd/`), sem credencial no repo e sem ativação de DNS. O túnel do projeto antigo (/opt/divorcio) permanece intocado.

**Racional:** nginx já opera neste host, tem o melhor perfil para arquivo estático e o modelo symlink-release dá promoção/rollback atômicos exigidos pelo P4; TLS termina no edge da Cloudflare, então o vhost local escuta apenas loopback para o cloudflared. Caddy (também instalado) documentado como alternativa; servir tudo pelo Go foi descartado como caminho quente por juntar processo de aplicação e serviço de arquivo estático no mesmo ponto de falha.

## DEC-011 — Arquitetura de redação: lotes por família, conhecimento embutido no lote

**Decisão:** a unidade de redação é o **lote por família** (área+família, 10–40 páginas por agente-redator), não a página isolada nem uma base de conhecimento separada por tema. O redator do lote pesquisa as fontes oficiais da família uma vez (briefing embutido), escreve todas as páginas da família em sequência e é o primeiro responsável por diferenciá-las materialmente entre si (estrutura, profundidade, ângulo — WRITING_SPEC). Justificativa: (a) consistência factual dentro da família; (b) o maior risco de near-duplicate é intra-família, e o redator com o lote inteiro em contexto evita colisões na origem; (c) elimina a camada intermediária de knowledge base por tema (B1 do PLAN), que duplicaria trabalho — o conhecimento vive nas fontes citadas com `anchor_claim` por página. Fatia vertical piloto (1–2 famílias → ingestão → oráculos) antes de qualquer onda em massa.

## DEC-012 — Virada do estoque: v2 substitui o estoque v1 no worktree, com história preservada

**Decisão:** quando a fatia vertical piloto validar a cadeia, o estoque v1 (300 drafts + 9.700 expansões cartesianas) será substituído no worktree pelo estoque v2, e as camadas derivadas serão regeneradas pelos geradores oficiais. O v1 permanece integralmente recuperável no histórico git (commits até `9a5495b`); nada é apagado da história. Fundamento: DEC-004 condenou o v1 no mérito (doorway); as camadas derivadas são recalculáveis por construção; a publicação permanece estruturalmente bloqueada abaixo de 10.000 registros aprovados (`ValidateExactP0TransactionPreflight` exige exatamente 10.000), então a troca não cria risco de publicação indevida.

**Piloto (fatia vertical):** 34 páginas v2 (família fgts + verbetes processo-civil) → `ingest-v2-pages --mode rewrite` → regenerar quality vectors, readiness, legal reviews, release evidence, release transaction, manifest rehearsal, prosa pública/oráculos e verdict em n=34 → staging isolado. Promoção real só no marco de 10.000.

## DEC-013 — Completude proporcional ao page_type (o estoque deixa de exigir 4 seções fixas)

**Decisão:** a invariante v1 "todo registro do estoque tem ≥ 4 seções" (`stock.go:1115`, `v2ingest/validate.go:24`, `quality_vectors.go:2066`) é substituída por um mínimo **proporcional ao `page_type`**: verbete ≥ 2, pergunta ≥ 2, procedimento ≥ 3, guia_problema ≥ 4. Registros sem `page_type` (estoque v1) mantêm o mínimo 4 — comportamento antigo preservado.

**Racional:** a seção 19 do anexo do goal exige que "a estrutura seja escolhida pelo tipo de problema, e não repetida mecanicamente" e proíbe "obrigar todas as páginas ao mesmo número de seções". Um verbete jurídico denso de 400–700 palavras se resolve em 2–3 seções; forçar 4 produziria o enchimento que a WRITING_SPEC proíbe. Na fatia vertical piloto, 16 dos 20 verbetes reprovaram só por essa invariante — ela custaria ~⅓ da capacidade de 10.000 (todo o glossário + verbetes de cada área). O `page_type` passa a fluir do portfólio → página v2 → `authorialmassdrafts.Record.PageType` → `stock.Record` → gates. A completude mínima de palavras por page_type (WRITING_SPEC §3) é o segundo eixo de qualidade, verificado na ingestão.

## DEC-014 — Desacoplar a cadeia de release do número mágico 10.000; adaptá-la ao estoque v2

**Decisão:** a cadeia authorial_mass passa a ser dirigida pelo `stock_manifest.json` em vez da constante `TargetTotalContents = 10000`, e o agrupamento/gates de similaridade passam a refletir a estrutura real do estoque v2 (não cartesiano, por area/família, com page_type). Três eixos:
1. **Total esperado do manifesto:** `authorialmassstock.TargetTotalContents` (referência hardcoded em ~15 pacotes) é substituído por `ExpectedTotalContents(root)` (soma do manifesto; fallback 10000 quando não há manifesto ⇒ produção v1 idêntica, todos os testes v1 verdes). Oráculos com `DefaultMinRecords/DefaultMinimumRecords = 10000` passam a aceitar o total do manifesto.
2. **Agrupamento e pares proporcionais:** `refinement_quality` e `contextcompat` agrupam por `scenario/context` cartesianos (v1). No v2 (scenario/context vazios) o agrupamento é por `practice_area`/`family`; o piso `ExpectedPairCount >= 1000000` (refinement_quality.go:395) vira `>= minExpectedPairsForTotal(total)` (proporcional a N e à estrutura de grupos), preservando 1M quando total=10000-v1.
3. **Prova de escala separada da validação de conteúdo:** a evidência de capacidade para 1M/milhões (P3) migra para benchmark sintético dedicado (`internal/scaleindex`, `internal/parallelbatch.SyntheticProbeRecords`, `contentstorepebble` já têm sondas de 100k/1M) — deixa de ser um gate embutido no gerador de qualidade de conteúdo, que passa a validar só a qualidade do conteúdo real presente.

**Racional:** a rigidez em 10.000 é a raiz mecânica do loop do Codex (BUG-006) e contradiz o requisito de escala do goal (P3: "1 milhão como capacidade de inventário", "arquitetura não pode depender de all-pairs O(n²)"). Desacoplar permite (a) iterar/provar com amostras (fatia vertical), (b) escalar o conteúdo real sem o teto artificial, (c) manter a prova de escala onde ela pertence — no benchmark, não no gate de conteúdo. O goal autoriza expressamente mudar arquitetura para melhor.

**Execução:** por gerador, na ordem da cadeia, começando por `refinement_quality` (primeiro bloqueio) → `quality_vectors` → `contextcompat` → `scale_shards`/`public_prose_candidate` → oráculos. Cada gerador: preserva comportamento em total=10000-v1 (teste), aceita N do manifesto, gates proporcionais. Trabalho multi-sessão; estado em STATUS.md.

## DEC-015 — O P0 real regenera em N=10.000; a fatia vertical n=34 já cumpriu seu papel

**Decisão:** parar de adaptar o pipeline `signature→scale` para N pequeno como pré-requisito. O caminho crítico do P0 é: escrever 10.000 páginas → ingerir → regenerar a cadeia **em N=10.000** → verdict → promoção.

**Racional (insight do afb12):** a fatia vertical n=34 trava em hardcodes de contagem (`refined_public_prose_count_mismatch: records=34 expected=10000`; `changed_count_below_minimum: expected_min=38` do signature plan v1 stale). Esses gates estão **satisfeitos naturalmente em produção** (records=10000=10000; o signature plan regenerado sobre 10.000 v2 dá um expected coerente). Portanto **não bloqueiam o P0 real** — bloqueiam apenas amostras pequenas. O valor da fatia vertical era: (a) provar que a arquitetura desacoplou (feito — refinement/global_similarity/quality_vectors/candidate/readiness/contextcompat/scale_shards/legal_signatures regeneram em N=34, testes v1 verdes); (b) descobrir o cold-start bootstrap (feito — `quality_vectors` deriva de stock quando refined ausente, `quality_vectors.go:1372`; ordem: qv-from-stock → readiness → candidate; funciona em qualquer N, inclusive 10.000). Ambos cumpridos.

**Consequência:** a adaptação restante do `signature→scale` para N pequeno (≈6 pacotes) fica como de-risking **opcional/paralelo**, não caminho crítico. O caminho crítico volta ao conteúdo: acumular as páginas (workflow de escrita) e, com o volume, executar a regeneração de produção com a ordem de bootstrap conhecida.

**Ferramentas de oráculo** (wordfreq/ftfy/simplemma/lexicalrichness/Vale/morphsyntax/LanguageTool) instaladas e reprodutíveis (`ops/setup-oracle-tools.sh`) — requisito da regeneração de produção (N=10.000), onde os oráculos PT-BR de fato rodam (em N pequeno o gate de escala os pula).

## DEC-016 — Wrappers leves por default: cache persistente, awareness rápida, ledger congelado de fato (ULTRAPLAN E2)

**Decisão (2026-07-08, autorizada pelo dono via ULTRAPLAN):**
1. **Caches persistem**: `GOCACHE` default sai de `/tmp/opt-wiki-go-cache` (evaporava a cada boot → cold-start recorrente) para o default do Go `~/.cache/go-build` (compartilhado com go-modern/pre-commit) em `tools/run-go-cmd-cached` e `tools/lab-cycle`; binários cacheados saem de `/tmp/opt-wiki-go-cmd-bin` para `.cache/go-cmd-bin` (gitignored) — medido: `/tmp` estava vazio, forçando recompilar todos os geradores após reboot.
2. **Repo awareness rápida por default**: a coleta completa (7 comandos git por invocação — status/diff/diff-cached/ls-files/log/show — ≈5,7s de CPU por comando em repo de 16,8 GiB) vira opt-in por `WIKI_REPO_AWARENESS_FULL=1` em `run-go-cmd-cached` e `run-heavy-throttled`. Medido: invocação de comando cacheado caiu de 6,1s para 0,22s (28×). As linhas de `artifact_claim` continuam emitidas (disciplina de claim preservada).
3. **DEC-002 executada no produtor**: `material_artifact_ledger_command` agora exige `WIKI_HEAVY_FORCE_LEDGER=1` — o command-ledger de 1,76 GB estava congelado no papel, mas `run-heavy-throttled` seguia apendando (última escrita 2026-07-07) e cada append invocava outro comando Go cacheado (imposto recursivo). Nenhum check de gate lê esses appends desde a DEC-002.

**Racional:** BUG-003 (governança mais cara que o produto) continuava vivo nos wrappers. O custo era pago por TODA invocação de gerador/check da fábrica — burocracia de processo taxando o produto. A exclusão mútua real é o flock do wrapper, não o registro no ledger.

## DEC-017 — O subsistema de reescrita mecânica do refined é DESLIGADO no regime v2

**Decisão (2026-07-08, ensaio N=209; diretriz do dono: causa raiz, nunca correção um-a-um):** o `internal/refinedpublicprose` v1 contém uma fábrica de reescrita sintética (~172 rotinas `repair*/rebuild*/close*`, estágios por registro em `newRecordWithStageSink`, closure/dedupe de corpus em `finalizeRefinedBuildPipeline*`) construída para diferenciar à força o estoque doorway cartesiano. Sob o regime do `stock_manifest` (estoque v2), esse subsistema INTEIRO é desligado por um único interruptor de processo (`mechanicalClosureDisabled`, setado nos entry points) nos dois gargalos estruturais por onde todo o pipeline passa. O mesmo princípio vale para a camada candidate: sem seções suplementares sintéticas, sem reescrita de headings, sem guidance mecânica no summary, sanitização mínima de segurança (URLs cruas, espaçamento de citação).

**Racional:** no v2 a qualidade nasce na FONTE (redator-agente com fontes oficiais + auditor canônico) e o controle em escala é dos GATES (detectores) + fila de revisão de agentes Claude Code — revisão humana página-a-página é impossível em milhares de páginas (diretriz do dono); humano lê amostras estratificadas. Texto público reescrito por máquina é o padrão-molde que a DEC-004 condenou ("Vínculo com a operadora parte da conferência de prova escrita em contexto documentado…"). Detector sinaliza → agente reescreve com fontes → auditor confere. Máquina NUNCA inventa prosa pública.

**Correções de detector no mesmo ensaio (falsos positivos sobre léxico jurídico):** "bloqueio/bloqueado" (bloqueio cautelar Pix/BCB, Sisbajud), "score" (score de crédito), "triagem" (triagem por WhatsApp — vocabulário do PRODUTO na WRITING_SPEC), "manifesto" (manifesto de carga) e o padrão de contração pendente (norma culta PROÍBE contrair antes de sujeito de infinitivo: "a chance de a operação ser…"). O jargão interno agora é detectado por COLOCAÇÃO composta ("bloqueio de publicação", "score humano", "manifesto de publicação", "em o/em a").

## DEC-018 — morphsyntax vira gate release full-corpus via spaCy (Stanza fica diagnóstico)

**Decisão (2026-07-09, ensaio N=209; diretriz do dono: entregar, causa raiz):** o
oráculo `ptbr_morphsyntax` era, por construção, um diagnóstico de amostra curta
(`--limit 4`, `--max-sample-chars 180`) com `validate_record` e `coverage_status`
*hardwired* como sempre-bloqueado por um "gap de NER do Stanza". Mas o verdict o
exige como deep-check release full-corpus (`qualityOracleDeepCheckRequiredForMassFanIn`
retorna true, com teste `TestQualityOraclesUseMorphsyntaxReleaseValidatorForMassCoverage`
afirmando a intenção). Isso tornava o verdict INSATISFAZÍVEL a qualquer conteúdo —
elo insatisfazível, não gate. Correção honrando a intenção (não demovendo o gate):

1. **Passe RELEASE full-corpus com spaCy** (`analyze_record_spacy_only`): analisa
   TODOS os registros do `refined_public_prose` (POS/dependência/NER). spaCy é o
   motor primário PT-BR e o único com **NER PT oficial** (`pt_core_news_sm`); os
   detectores combinam os motores por OR + fallback de regex, então rodar só com
   spaCy cobre todo o corpus sem perder checagem. Campo novo `release_covered_records`
   prova a cobertura; Go usa-o no gate de cobertura.
2. **Stanza fica no diagnóstico de amostra curta** (cross-check spaCy×Stanza,
   `useful_divergences`). Stanza 1.13.0 depparse é lento demais para full-corpus
   (medido: 20 páginas full-text estouraram 2 min → 10k inviável — lentidão em 10k
   é bug P0). E o catálogo oficial do Stanza 1.13 PT **não tem NER** (documentado no
   produtor com fontes oficiais), então exigir NER dele era requisito impossível.
3. **`ValidateRelease` (Go)**: cobertura por `release_covered_records >= input_records`;
   **spaCy NER continua EXIGIDO** (`spacy_ner_gap` reprova); **Stanza NER não é
   exigido** (`validateReleaseOracleCoverage("stanza", …, false)`). Status
   release-grade, sem `blocked_coverage_reasons`.

**Racional / por que NÃO é afrouxamento:** a cobertura saltou de **4 amostras de
180 chars** para as **209 páginas inteiras** (no ensaio N=209 o passe achou 85
páginas com issues reais, antes invisíveis) — o gate ficou MUITO mais estrito. O
que saiu foi um requisito impossível (NER de um modelo que o upstream não publica).
A enforcement das mesmas classes em full-corpus também vive no `language_gate`
(`dangling_connector` + `truncated_sentences`) e no `languagetool-release`.
Otimização futura para 10k: passe full-corpus spaCy-only já é escalável; o
diagnóstico Stanza permanece amostral.

## DEC-006 — Correção só para frente é mantida

**Decisão:** nenhuma reescrita de história, `reset`, `revert` ou descarte de worktree. O ledger gigante e os dados históricos permanecem; a mudança é parar de alimentá-los. Dados derivados obsoletos serão regenerados ou marcados como históricos, nunca apagados às cegas.

## DEC-019 — Governança de Claude Code e Codex é entre pares

**Decisão (2026-07-10, ordem do dono):** Claude Code e Codex/GPT-5.6 são engenheiros-chefes autônomos de suas frentes e podem liderar, revisar, questionar e corrigir para frente o trabalho um do outro. É proibido presumir superioridade, inferioridade ou papel coadjuvante pela identidade do modelo. Coordenação temporária, lock e ownership de artefato existem para exclusão mútua e rastreabilidade, não para criar hierarquia de capacidade.

**Consequência:** `AGENTS.md`, `CLAUDE.md` e o log cross-agente passam a exigir revisão crítica recíproca com evidência. Qualquer agente pode corrigir bugs de código, conteúdo jurídico, engenharia ou integração da outra frente, preservando trabalho válido e os mesmos gates. Referências históricas a maestro descrevem somente a coordenação de uma operação naquele momento e não limitam a autonomia do outro par.

## DEC-020 — `intent_id` ativo é globalmente único; supersessão preserva e autentica o original

**Decisão (2026-07-11):** nenhum shard finalizado pode manter uma segunda página ativa para o mesmo `intent_id`. O auditor global marca todas as ocorrências por `intent_id_dup_global`, e o merge do estoque conserva a rejeição redundante de duplicata no lote. Uma cópia histórica só deixa o estoque ativo por tombstone com `skip_reason=duplicate_intent_consolidated`, `superseded_by=<shard-finalizado.jsonl>`, archive fora de `v2_pages` e SHA-256 do registro integral substituído.

**Validação transacional:** Python e Go exigem outro shard finalizado com exatamente um vencedor ativo do mesmo intent, destino diferente do shard de origem, archive canônico em `data/editorial/v2_superseded/`, registro original decodificável e coerente com o hash, intent, shard e vencedor, além de `render_allowed=false`, `sitemap_allowed=false` e `publication_allowed=false` explícitos. Tombstone editorial comum continua reprovando na ingestão e indo para reescrita; essa exceção não transforma pulo de conteúdo em aprovação.

**Racional e operação viva:** a revisão cruzada encontrou 17 duplicatas ativas, todas com uma versão canônica mais nova em `imobiliario-05`, que inflavam o estoque e deixavam o auditor global verde. Os 17 originais foram preservados integralmente em `data/editorial/v2_superseded/duplicate-intent-consolidation-2026-07-11.jsonl`; as cópias perdedoras em cinco shards viraram tombstones verificáveis. A correção é para frente, auditável e não publica nada.

## DEC-021 — Redação por FACT-BRIEF automático (fonte=proveniência), NUNCA transformação semântica de corpo; corpus-oráculo de verificação autorizado

**Decisão (2026-07-17, ordem do dono + exploração adversarial de 3 agentes):** a economia de redação vem de automatizar o FACT-BRIEF (coleta + verificação de fatos da fonte oficial), NUNCA de transformar semanticamente o texto oficial em prosa. Explorada e **REJEITADA** a forma "scraping → transformação semântica automática → IA só revisa": é o exemplo NOMINAL de *scaled content abuse* do Google 2026 e reincide na DEC-004/DEC-017 (spinning mecânico). Veredito convergente: redator-jurídico + Fable red-team + design técnico.

**Fronteira inviolável:** o sistema automático decide O QUÊ a página diz (fatos destilados, estrutura, `distinct_because`, proveniência); a IA sintetiza AUTORALMENTE o COMO diz. No instante em que qualquer frase do corpo público for DERIVADA POR TRANSFORMAÇÃO do texto da fonte (fonte=corpo) é spinning; se for SINTETIZADA a partir de fatos estruturados (fonte=proveniência) é legítima. O brief leva FATOS destilados ("art. 51 do CDC fixa X"), NUNCA spans crus de texto (span cru tenta à paráfrase).

**Ganho honesto:** ~2-4× menos tokens/página (via first-pass yield ↑ + rebaixamento de modelo Opus→Sonnet→Haiku viabilizado por fatos já verificados), NÃO "~10× porque a IA só revisa" (fantasia que colide com os gates). O custo real hoje é o loop de reescrita (~28% dos intents = `needs_source_research`). Fetch amortiza FORTE (top-100 diplomas = 50% das citações; CDC serve 1.513 intents); claim/prosa NÃO amortiza (cauda longa, 70% dos documentos citados por 1 intent).

**Corpus-oráculo de verificação (autorizado pelo dono):** coletar o TEXTO OFICIAL das fontes para um corpus SEPARADO (`internal/corpus`, `data/source-snapshots/`, `public_indexable=false`) — gabarito objetivo de verificação (o Go re-resolve byte-a-byte: a IA rotula, o Go PROVA, a lei decide) e input do fact-brief. NÃO republicado: separação proveniência↔corpo preservada (`raw_text_stored` só no vault, nunca no publicável). Concilia o "no-scraping de corpo" do `AGENTS.md` (que PERMANECE) com coleta de fatos para verificação privada. Guardas O(1) pré-escrita (`internal/oracle`: ExistGuard/VigenciaGuard/NumericGuard) barram citação alucinada antes de gastar escrita.

**Engenharia nova da sessão 2026-07-17 (plano aprovado):** fundações testadas `internal/{qualitysampling,infogain,corpus,oracle,legalfacts}`; motor do fact-brief `cmd/{collect-oracle,distill-facts}`; fiscalização em tiers T0-T4 com bound estatístico CERTIFICADO (`qualitysampling`: RCPS/Learn-Then-Test, amostra independente de N) — IA fiscaliza IA sem revisão humana por página, o dono responde pelo resíduo irredutível. Reusa o pipeline sancionado (writing-mass → verify → commit-verified). Correção só para frente; gates integrais; sem relaxar.

## DEC-022 — Topologia de launch em 8088/8089, DEC-005 superada por ordem do dono, treino bloqueado na camada HTTP como contrato de produto

**Decisão (2026-08-04, ordem do dono — launch no 1º milheiro):** a DEC-005 ("domínio não publicado até ordem explícita") está **SUPERADA**: o dono ordenou o launch do portal com o primeiro milheiro aprovado. A topologia de serviço passa a ser: cloudflared → nginx local em **127.0.0.1:8088** (estático de `releases/current/public` + enforcement de bots + rate limit) → fallback dinâmico Go (`cmd/server`) em **127.0.0.1:8089**. As portas 8080/8081 previstas na DEC-010 colidiam com o projeto vizinho `divorcio` (fora do ar por decisão do dono, mas com configs nginx ainda carregadas, que são intocáveis); 8082 é o LanguageTool. 8088/8089 foram medidas livres — coexistência sem editar conf alheio.

**Política de bots como contrato de produto:** bots de **treinamento** com User-Agent HTTP real (fonte única `crawl.HTTPDeniedBots()`: GPTBot, ClaudeBot, CCBot, Bytespider, meta-externalagent, Amazonbot) são **negados com 403** no ingress nginx em todas as rotas exceto `/robots.txt` (o bot precisa poder ler a diretiva que o exclui). Tokens robots-only (`crawl.RobotsTokenOnlyBots()`: Google-Extended, Applebot-Extended) nunca entram na negação por UA — não enviam UA próprio; o controle deles é exclusivamente via robots.txt. Bots valiosos de busca/usuário (`crawl.RequiredValuableBots()`) têm pista de rate limit generosa (600 r/m vs 120 r/m do tráfego genérico, chave por IP real via `CF-Connecting-IP`). O conteúdo servido é idêntico para bot e humano (contrato de HTML leve mantido). Drift entre `ops/nginx/wikijuridica.conf` e o pacote `internal/crawl` é reprovado por `internal/contract/public/nginx_bot_policy_drift_test.go`.

**Precedência do endereço do Go:** argumento posicional > env `WIKI_HTTP_ADDR` > default `127.0.0.1:8089` (`cmd/server/main.go`); unit `ops/systemd/wikijuridica-server.service` fixa o env. Symlink do site, `nginx -t` e reload são passos do maestro/dono na ativação (checklist em `ops/README.md`).

## DEC-023 — Política de bots PERMISSIVA por ordem do titular do conteúdo; bloqueio de treino da DEC-022 revertido

**Decisão (2026-08-04, ordem direta do dono — Rafael Toledo, titular do conteúdo e do domínio): "deixa liberado para bots, sendo permissivo. Sem luta contra bots."** A decisão é do titular do conteúdo, a quem cabe dispor sobre o uso do próprio acervo. Ela **reverte o bloqueio de bots de treinamento da DEC-022** (403 no ingress + `Disallow: /` em robots.txt), que fica superado nesse ponto; a DEC-022 permanece vigente no restante (topologia 8088/8089, launch, precedência de endereço).

**O que mudou, coerente nos três lugares:**
1. **`internal/crawl` (fonte única):** `crawl.HTTPDeniedBots()` passa a retornar lista **vazia** — nenhum User-Agent recebe 403 por ser bot. `DefaultPolicy`/`content/crawl_policy.json` deixam de emitir `Disallow: /` por identidade: bots de treinamento (GPTBot, ClaudeBot, CCBot, Bytespider, Amazonbot, meta-externalagent, Applebot-Extended) e tokens de controle (Google-Extended) recebem o MESMO tratamento do `*` — `Allow: /` com apenas os Disallow de higiene de indexação (`/buscar/` e `/*?*`), que não são luta contra bot. `ValidatePolicy` inverteu o sinal do gate: agora REPROVA bot de treinamento com raiz bloqueada (`crawl_policy_training_bot_not_crawlable`) e mantém como controles obrigatórios a higiene (`crawl_policy_training_bot_search_query_crawl_open`) e o rate tier declarado (`crawl_policy_training_bot_without_rate_tier`).
2. **`ops/nginx/wikijuridica.conf` (produção viva):** removidos o map `$wj_bot_deny`, o map `$wj_block` e os dois `if (...) { return 403; }`. Permanecem o map `$wj_bot_allow` (pista generosa) e o **rate limit por IP em duas pistas** (120 r/m genérico / 600 r/m bots valiosos, burst 60/300, 429) — proteção de DISPONIBILIDADE, não de identidade; ser permissivo não é deixar crawler agressivo derrubar o servidor.
3. **robots.txt público (`public/robots.txt`, regenerado por `cmd/generate-public-robots`):** nenhum `Disallow` por ser bot; mantidos os Disallow legítimos de higiene (busca interna `/buscar/`, parâmetros `/*?*`) e o `Allow: /buscar/` dos bots valiosos de busca (precisam rastrear a rota para ver o noindex).

**Gates e testes reescritos para provar a NOVA política (sem deletar teste):** `internal/contract/public/nginx_bot_policy_drift_test.go` agora reprova nos dois sentidos — Go declarando negação (lista não-vazia) OU nginx praticando negação (map de deny, `return 403`, diretiva nomeando bot de treinamento) — e exige a permanência das zonas de rate limit; `internal/crawl/crawl_test.go`, `internal/contract/p0/p0p1_test.go`, `internal/checks` (`public-robots-drift`, `crawlability`, `openai-bot-policy`) e `internal/crawlsmoke` invertidos no mesmo contrato. Alinha-se ao contrato já escrito em `docs/SEO_CRAWL_INDEXING.md` ("rate limit de treinamento é política de tráfego, não bloqueio de crawl"). Lado Cloudflare já permissivo (fight_mode/ai_bots_protection/crawler_protection desativados pelo dono). Reintroduzir qualquer negação por UA exige nova DEC.

## DEC-024 — O detector de promessa de resultado é recalibrado por frase (R1/R1b/R2), com allowlist residual em código e quarentena auditável no lugar do batch-fatal indiscriminado

**Decisão (2026-08-04, gate `public_prose_candidate_oab_cta_promise` travando 7.962 páginas em 12 ocorrências de 10 páginas; especificação de red-team + refutação empírica de uma premissa dele):** o detector de promessa de resultado do `internal/publicprosecandidate` deixa de ser substring cego sobre o campo inteiro e passa a classificar **por frase**, em três regras, com separação de consequência por classe.

**Causa raiz — elo insatisfazível herdado da DEC-017.** No v1, as formas NEGADAS eram apagadas ANTES da checagem pela reescrita mecânica do `refined`/`candidate` (`internalVocabularyReplacements`: "sem resultado garantido" → "sem promessa de resultado", "não há resultado garantido" → "não há promessa de resultado"). O detector nunca precisou distinguir promessa de negação: a máquina reescrevia a negação e só sobrava o afirmativo. A **DEC-017 desligou essa reescrita no regime v2 — corretamente**, porque máquina não escreve prosa pública; mas o detector **não foi recalibrado junto**. Resultado: qualquer página educativa que precise NOMEAR a promessa de terceiro para desmenti-la reprovava. É o mesmo padrão que a DEC-018 chamou de "elo insatisfazível, não gate", e a mesma família dos falsos-positivos léxicos que a própria DEC-017 corrigiu ("bloqueio", "score", "triagem", "manifesto"). O caso que fecha a questão: `cons-clinica-prometeu-resultado-garantido`, página sobre o **art. 30 do CDC** — cujo tema É que publicidade de resultado garantido OBRIGA o fornecedor. Slug, H1 e abertura precisam nomear a promessa; reescrever o texto destruiria a página.

**O que passou a valer (`internal/publicprosecandidate/outcome_promise.go`).** Recorte em frases no texto CRU (só `.`, `!`, `?` e quebra de linha — `;` e `:` ligam orações da MESMA frase em português, e tratá-los como fronteira arrancaria o marcador de voz própria do termo, deixando "Contrate agora: resultado garantido" cair na classe branda); normalização por frase; então:
- **R1 — promessa em voz própria (fatal, sem exceção):** frase com termo proibido + marcador de auto-referência (`garantimos/garanto/asseguramos/prometemos/prometo/nosso(a)(s)/conosco/contrate/whatsapp`).
- **R1b — colocação de primeira pessoa (fatal, sem exceção, buraco NOVO fechado):** verbo `garantimos|garanto|garantiremos|asseguramos|asseguro|prometemos|prometo` a ≤4 tokens de substantivo de resultado (`resultado, exito, ganho, vitoria, causa, aprovacao, concessao, beneficio, ressarcimento, indenizacao`). O red-team apurou que **"Garantimos o resultado da sua causa" NÃO era pego pelo detector antigo** — nenhum dos 7 termos da lista casa. A recalibração fecha isso.
- **R2 — escape estreito por ADJACÊNCIA:** (a) partícula de negação (`sem, nao, nunca, jamais, nenhum, nenhuma`) colada ao termo, tolerando no máximo um elo da lista fechada `ha|existe|e|esta|sera|seria|houve`; (b) verbo de atribuição a terceiro (`prometeu, anunciou, oferece, divulga, vende…`) a ≤2 tokens; (c) substantivo de atribuição (`publicidade, propaganda, anuncio, oferta, promessa`) a ≤3 tokens, ligado ao termo só por `de|da|do|com|que`. **Sem janela larga e sem exceção por aspas**, que foram propostas e REJEITADAS: janela de qualquer tamanho é burlável ("Sem burocracia e sem demora, resultado garantido") e aspas custam zero para o gerador de texto.

**Premissa do red-team refutada por medição — por isso a allowlist.** A especificação afirmava que "as 12 ocorrências reais têm o marcador COLADO no termo; distância só aparece nas burlas" (verificado em UMA página, `consumidor-15.jsonl`, e generalizado). A extração do acervo vivo mostra o contrário: **só 3 das 12 têm marcador adjacente** — exatamente os três campos da página do art. 30 do CDC, que por isso passa pela regra R2 sem depender de dispensa nenhuma. Nas outras 9 a negação/atribuição está a 4–6 tokens ("a falta de assistência **não transforma** qualquer gasto em ressarcimento certo"; "**sem transformar** o deferimento em resultado garantido"; "**Nenhuma** dessas ferramentas transforma uma pista incompleta em resultado garantido"). Como a regra de adjacência continua certa (é o que impede a burla), o resíduo é coberto pela via que o próprio red-team deixou aberta: **allowlist residual por intent**, com 9 entradas de `intent + termo + justificativa` em **código versionado** (`outcome_promise_allowlist.go`). Marca no dado foi rejeitada: a mesma IA que redige a página setaria o flag — porta dos fundos estrutural. Limites duros, cobertos por teste: a allowlist **só alcança a classe afirmativa** (R1/R1b a ignoram por completo), é consultada **depois** da classificação, e é **recusada quando o campo inteiro fala em primeira pessoa ou possessivo** (`garantimos…`, `nosso(a)(s)`, `conosco`) — vocabulário de canal (`whatsapp`, `contrate`) não recusa, porque a WRITING_SPEC o usa legitimamente em página informativa, e ele segue fatal via R1 quando aparece na mesma frase do termo.

**Consequência por classe, no lugar do batch-fatal indiscriminado (`generateWithOutcomePromiseQuarantine`).** Hit **R1/R1b** continua **reprovando o lote inteiro** — promessa em primeira pessoa escrita pelo gerador é defeito sistêmico e tem que parar tudo com barulho; o registro é mantido no lote de propósito, para reprovar. Hit **afirmativo fora da allowlist** retira a **página individual**, grava linha no ledger versionado `data/editorial/public_prose_outcome_promise_quarantine.jsonl` (id, intent, campo, termo, **frase exata**) e imprime sumário em stderr — nunca silencioso; a página só volta com texto corrigido. **Disjuntor:** >20 páginas OU >0,3% do lote volta a ser batch-fatal (indício de molde). O modo `--check` acompanha: o count esperado desconta a quarentena persistida e a comparação de frescor aplica a mesma separação, de modo que ledger adulterado desalinha a contagem e REPROVA. O racional é que o batch-fatal indiscriminado criou a pressão para afrouxar a ética a fim de destravar 7.962 páginas — esse incentivo perverso era, em si, o maior risco à inscrição OAB do titular.

**Prova exigida e obtida.** Bateria adversarial em `outcome_promise_test.go`: as 10 frases que DEVEM reprovar (incluindo as construídas para burlar — negação distante, elo inválido, aspas, conectivo quebrado, "vendemos ressarcimento certo") reprovam; os 7 casos de escape legítimo passam; as **9 ocorrências reais entram como fixtures com o CAMPO PÚBLICO INTEIRO** produzido pelo builder, não aproximações; a página do art. 30 do CDC passa **sem allowlist**; promessa em voz própria **num intent dispensado** continua reprovando; a mesma frase real **em outro intent** continua reprovando. Varredura do classificador novo sobre os **7.962 registros**: 9 ocorrências afirmativas (todas dispensadas), **zero** hits de voz própria — R1b não introduziu falso positivo.

**Risco residual assumido, registrado para não ficar oculto:** a chave da allowlist é `intent + termo` e não a frase exata, para que refinamento editorial normal não volte a travar o lote. Se um desses 9 intents for reescrito, a nova frase com o mesmo termo entra dispensada — mitigado por R1/R1b nunca serem dispensáveis, pela recusa quando o campo fala em voz própria, e pelo dever de reler a ocorrência em qualquer reescrita dessas páginas.

**Lacuna conhecida, FORA do escopo desta correção (não é regressão — já existia):** `outcomePromiseTerms` casa sequências contíguas, então uma palavra intercalada quebra todos os needles — "o resultado **seria** garantido se nos contratar" escapa hoje, e escapava antes. Não é a regra de contexto que falha, é a lista de termos; corrigir exige needles com lacuna tolerada e medição própria de falso positivo sobre os 7.962. Fica registrado aqui para não se perder; R1/R1b pegam a variante com auto-referência explícita ("garantimos"/"nosso"/"conosco"), que é a forma perigosa.

## DEC-025 — Hub de área entra no sitemap por DERIVAÇÃO AUTENTICADA, com a porta dos fundos fechada por controle nomeado

**Decisão (2026-08-07):** as 29 hubs de área e as 177 páginas de paginação (`/{area}/` e `/{area}/pagina/N/`, 206 URLs) passam a constar do sitemap público. A invariante `sitemap ⊆ published_manifest` **não é afrouxada**: o validador aprende a **recalcular** o conjunto de hubs a partir do mesmo acervo e aceita a loc por **pertinência ao conjunto derivado**, nunca por exceção.

**O custo que a regra anterior cobrava.** A hub é navegação sintética derivada do acervo: não tem — nem pode fraudar — registro editorial de manifesto, e por isso ficava fora do sitemap, com razão. Só que essas 206 URLs carregam a descoberta por link de **8.202 artigos (85% do acervo)**, que estão em depth 3 com in-degree mediano 2. Elas não constavam de sitemap nenhum, e ainda eram servidas exclusivamente pelo fallback Go — medido em 2026-08-07: 9.651 ocorrências de link interno dependiam de um processo estar de pé.

**Onde a fórmula mora, e por quê.** `internal/areahubroutes` é pacote FOLHA (depende só de `content` e `editorial`). Não pode morar em `publishedmanifest` porque `internal/ondemand` já importa `publishedmanifest` — o inverso seria ciclo. E não pode ser duplicada: duas cópias divergiriam na primeira mudança de `PageSize`, e a bijeção passaria a acusar 206 falhas falsas. `ondemand` consome a constante e a função de URL de lá; a equivalência entre a derivação nova e o índice que o servidor realmente serve está pinada em `internal/ondemand/areahub_routes_equivalence_test.go`, sobre seis acervos sintéticos (vazio, uma página, duas áreas, exatamente no limite de 50, um a mais, três páginas cheias).

**A PORTA DOS FUNDOS, e o controle que a fecha.** O laço geral do validador isenta loc cujo canonical seja de página indexável **não-jurídica**, e `hub-area` não está em `content.LegalPageTypes`. Sem controle próprio, a implementação preguiçosa desta DEC seria despejar em `content/pages.json` as `content.Page` sintéticas que `ondemand` já fabrica (`Status: published`, `IndexPolicy: index`) — e as 206 locs passariam **sem validação nenhuma**, com "derivação autenticada" virando rótulo. Por isso:

- `published_manifest_area_hub_shadowed_by_page_record` — hub com registro de manifesto **ou** entrada indexável em `pages.json` REPROVA. Checa contra os dois mapas: cobrir só um deixa a outra variante do despejo passar.
- `published_manifest_area_hub_public_html_missing` — hub anunciada no sitemap sem HTML em `public/` REPROVA. Anunciar 206 URLs sem prova de que resolvem seria o mesmo defeito que a invariante existe para impedir, por outra porta.
- Loc que **não** pertence ao conjunto derivado não é hub: cai nos dois códigos originais (`_sitemap_loc_without_manifest`, `_sitemap_loc_without_indexable_page`) e continua reprovando. O teste de controle usa `/promocao-qualquer/` e segue exigindo reprovação nos dois.

**O que fica DEFERIDO, declarado para não virar buraco silencioso.** O check de "hub derivada FALTANDO no sitemap" **não é ligado nesta DEC**. São cinco produtores de shard (`cmd/publish-v2-direct`, `internal/build`, `internal/httpserver`, e dois em `internal/publicrelease`) e ligar o check antes de todos incluírem as hubs faria o gate pousar vermelho — com `publishedmanifest.Validate` sendo `log.Fatal` no boot, isso derrubaria o servidor. Dois produtores já foram convertidos (`publish-v2-direct` e `internal/build`), e enquanto o check não existe a proteção contra regressão é o teste de bijeção em `area_hub_discovery_test.go`, que reprova se o plano perder uma hub. Ligar o check exige converter os três restantes no mesmo commit.

**Consequência aceita:** as hubs são anexadas ao fim do plano, então caem no rabo do último shard em vez de junto das suas áreas. Reordenar consertaria a estética e reembaralharia todo `SitemapSHA256` do manifesto — troca ruim. Fica como está.

**Verificado antes de ir ao ar,** em worktree isolada: sitemap de 9.628 → **9.834 locs**, `publishedmanifest.Validate` OK, **zero** entradas `hub-area` em `content/pages.json`, e `lastmod` de cada hub derivado da revisão mais recente da sua área.

## DEC-026 — CITAR não é INGERIR: o gate de fonte passa a exigir endereço oficial, não auditoria de raspagem

**Decisão (2026-08-07):** o controle de fonte em conteúdo jurídico indexável deixa de exigir `audit_status: approved` no registro curado e passa a exigir que o endereço **citado** seja de órgão oficial brasileiro (`.gov.br`, `.jus.br`, `.leg.br`, `.mp.br`, `.def.br`) **ou** conste do registro. O registro continua governando **ingestão**, que é outra coisa e que o portal não faz.

**A confusão que isto desfaz.** Os campos do `content/source_registry.json` são `ingestion_enabled`, `robots_url`, `robots_status`, `terms_url`, `terms_status`, `access_mode`, `provenance_strategy`: vocabulário de **autorização para raspar**. Mas o contrato do projeto é explícito — *"fonte oficial é referência/proveniência, nunca corpo; proibido scraping de conteúdo, cópia, espelho"*. A página **linka** o texto oficial e afirma o que ele resolve. Linkar a Constituição no Planalto não exige auditar os termos de uso do Planalto para raspagem.

**A medição que fecha a questão.** Nenhuma das 54 fontes do registro tem `audit_status: "approved"` — todas são `preliminar_bloqueado` ou `..._bloqueada_sem_publicacao`, herdadas da era em que nada era publicado, e `ingestion_enabled` é `false` nas 54. O gate acusava **23.501 ocorrências** de `source_not_registered` no acervo. Enquanto isso, **21.006 dos 21.038** registros de proveniência apontam para domínio oficial brasileiro, em 140 hosts distintos.

**Por que não bastava cadastrar as fontes.** Marcar 3.245 fontes como `approved` seria afirmar uma auditoria de termos/robots que ninguém fez — a fraude que o contrato proíbe, e a mesma pressão para afrouxar gate que a DEC-024 já nomeou.

**O controle novo é mais forte, não mais fraco.** Ele verifica algo que nada verificava: que o endereço citado é de fato de órgão oficial. A comparação é por **host**, nunca por string — `https://falso.com/www.planalto.gov.br` contém o sufixo e não é o Planalto — e exige HTTPS. Códigos: `source_url_not_official_nor_registered` (citação) e `source_ingestion_enabled_without_audit` (ingestão, que permanece exigindo auditoria completa e hoje está corretamente inativo, porque nada é ingerido).

**Decisão explícita sobre `.org.br`:** o sufixo **não** autentica — qualquer associação registra um. A OAB (`oab.org.br`) portanto **não** passa pelo host, e passa pelo REGISTRO. Esse é o caminho previsto para toda fonte legítima fora do domínio público: CFM, ICAO, EUR-Lex, Normattiva, BOE, Diário da República.

**Fila nomeada que isto revelou** — 13 hosts legítimos a cadastrar no registro curado, hoje acusados (53 ocorrências): `sistemas.cfm.org.br` (20), `www.icao.int` (8), `europa.eu` (4), `www.normattiva.it` (4), `www.oab.org.br` (3), `diariodarepublica.pt` (3), `publications.europa.eu` (2), `oeil.europarl.europa.eu` (2), `www.govinfo.gov` (2), `www.boe.es` (2), `portaldascomunidades.mne.gov.pt` (1), `site.cfp.org.br` (1), `www.subtel.gob.cl` (1). Cadastrar fonte é curadoria com campos de termos e robots — fica como próxima frente, não como remendo.

**Teste de contrato reescrito, nunca afrouxado.** `TestIndexableLegalPageCannotUsePreliminarySource` vira quatro casos: endereço arbitrário reprova; endereço oficial passa; sufixo no CAMINHO não autentica (cinco variantes, incluindo `http://` e host vazio); e `.org.br` só passa via registro. O invariante que sobrevive é o mesmo de antes — página jurídica indexável não cita endereço arbitrário.

## DEC-027 — FAQPage e HowTo FICAM, mesmo com o rich result extinto: dado estruturado não é só enfeite de SERP

**Decisão (2026-08-12, depois de pesquisa em fonte oficial acessada no dia).** O acervo emite **7.762 blocos `FAQPage`, 441 `QAPage` e 290 `HowTo`**. Os dois primeiros perderam a razão original: o Google anunciou em 08/05/2026 que o rich result de FAQ **deixaria de aparecer a partir de 07/05/2026** e removeu a documentação em 15/06/2026; o `HowTo` já estava morto desde 2023 (`developers.google.com/search/updates` e o blog de 08/2023). O gallery vigente (15/06/2026) lista Article, Breadcrumb, Organization, Profile page, Q&A e Local business — sem FAQ e sem HowTo.

**Mesmo assim, mantém-se, por três razões medidas:**
1. **Não custa orçamento.** A mediana de página é 21,7 KB e a maior é 34,3 KB, contra o teto de 50 KB do contrato de HTML leve. O `FAQPage` não é o que aperta o orçamento, e não há byte a economizar que mude uma decisão de rastreio.
2. **O consumidor não é só o Google.** Rich result é uma superfície; extração de resposta por sistema de IA é outra. `Question`/`acceptedAnswer` continua sendo par pergunta-resposta explicitamente marcado no documento, e nada na retirada do rich result indica que os motores parem de ler o bloco.
3. **O custo de tirar é alto e o ganho é zero.** Remover exigiria regerar 7.762 páginas — churn de artefato, hash novo no manifesto, rastreio inteiro reprocessado — para economizar bytes que não faltam.

**O que esta decisão IMPEDE:** que uma sessão futura leia "FAQ rich result foi extinto" e "corrija" o gerador removendo os blocos, sem perceber que a remoção é mais cara que a manutenção. Reverter exige nova DEC com medição de custo-benefício, não só a citação do changelog do Google.

**O que ela NÃO cobre:** emitir FAQ em página que não tenha FAQ de verdade. A coerência entre dado estruturado e conteúdo visível continua obrigatória — divergência ali é classificada como spam de dado estruturado pelo próprio Google, e é defeito P0.

## DEC-028 — O rate limit da origem é redimensionado: ele nunca barrou ninguém de fora, e estrangulava a própria casa

**Decisão (2026-08-12, com o log como prova).** A DEC-023 estabeleceu política permissiva com bots e manteve o rate limit como proteção de **disponibilidade**. A medição de dois dias de log mostrou que essa proteção, do jeito que estava, protegia zero e cobrava caro.

**O dado.** De **12.975 respostas 429** servidas por este host, **100% foram para ferramentas nossas**: 9.501 para uma varredura de auditoria, 1.184 e 996 para sondas de agente, e **1.294 para o próprio `wikijuridica-cache-warm`**. Nenhum bot real levou 429 em nenhum dia — `allow=0` em todas as linhas, ou seja, nenhuma era bot valioso (bot valioso não entra em zona alguma).

**Causa-raiz.** Requisição vinda do túnel traz `CF-Connecting-IP`, e o `real_ip_header` a converte no IP do visitante: o balde é por pessoa, como deve ser. Requisição **local** não tem esse header, `$binary_remote_addr` fica em 127.0.0.1 e **todas as ferramentas internas dividem um balde só**. O aquecimento de borda — que existe justamente para o crawler não receber 530 — estava sendo estrangulado pelo nosso próprio limitador.

**O que mudou (`ops/nginx/wikijuridica.conf`):** (a) `map $http_cf_connecting_ip $wj_client_key` devolve chave **vazia** para quem não veio da internet; o socket escuta só em 127.0.0.1, então "sem CF-Connecting-IP" equivale a "somos nós"; (b) o teto genérico sobe de **600 r/m para 3.000 r/m** e o burst de **300 para 600**.

**Por que subir o teto, e não só isentar o interno.** A lista de bot valioso é uma **allowlist por User-Agent**, e 2026 continua produzindo agente novo — `MistralAI-Index` e `DuckAssistBot` entraram no mesmo dia. Um crawler de citação ainda não listado cai na pista genérica e leva 429 **em silêncio**, que é o modo de perder um canal de citação sem nunca saber. 50 req/s por IP de visitante real continua impedindo flood, e a defesa de verdade contra volume hostil é o ruleset DDoS da camada anterior, não este balde: aqui o acervo é arquivo estático em disco, com custo por requisição essencialmente nulo.

**Provado depois do reload:** 500 requisições locais instantâneas = 500× 200; 700 requisições instantâneas de um IP externo simulado = 613 servidas e 87 barradas. Proteção intacta, casa liberada.

## DEC-029 — O portal ganha um servidor MCP próprio, e a dependência de runtime é justificada aqui

**Decisão (2026-08-12).** O acervo passa a expor um servidor **MCP** (Model Context Protocol) em `/mcp`, self-hosted no mesmo binário Go, atrás do nginx e do túnel. Isto é um ADR: adota-se `github.com/modelcontextprotocol/go-sdk`, dependência que afeta runtime público, e o contrato do repositório exige que ela venha com licença revisada, versão fixada, racional e medição.

**Licença e versão.** `v1.7.0` (publicada 2026-07-28), fixada em `go.mod` — não `latest`, não faixa. Licença lida no módulo baixado, não no README de terceiro: o projeto está em transição do MIT para **Apache-2.0**, com contribuições novas já em Apache-2.0 e documentação em CC-BY-4.0. Ambas permissivas e compatíveis com infraestrutura própria. Mantido por Anthropic em colaboração com o Google.

**Por que MCP dá retorno, e não é enfeite de protocolo.** A objeção honesta — "nenhum assistente descobre servidor MCP sozinho" — está certa quanto à descoberta **autônoma** e errada quanto à conclusão. Existe canal público, gratuito e self-service: o `registry.modelcontextprotocol.io` aceita servidor remoto self-hosted, com verificação de posse por arquivo no próprio domínio, e é dele que os agregadores puxam. A Cloudflare publica os servidores dela por lá (`com.cloudflare.mcp/mcp`, 30 remotes), e há precedente brasileiro do mesmo caso de uso (`senado-br-mcp-cloudflare`, ativo). A descoberta resultante é **assistida** — a pessoa encontra e instala em dois cliques, em vez de nunca saber que o serviço existe. Prometer mais que isso seria vender o que não se entrega.

**Por que no binário, e não em Workers.** O contrato do projeto é self-hosted first: Workers é serviço proprietário de terceiro, e a allowlist deste repositório nomeia apenas o Tunnel como exposição. O SDK oferece `NewStreamableHTTPHandler`, que é um `http.Handler` puro — encaixa no roteador existente sem processo novo, sem porta nova, sem supervisor novo.

**A pegadinha que decidiu a configuração.** `Stateless: true` não é preferência: o SDK **só aceita o protocolo corrente `2026-07-28` em modo stateless** e, sem isso, recusa a versão atual e passa a falar apenas as antigas — sem erro visível. Em stateless o próprio SDK responde **405 a GET e DELETE**, que é o que a spec pede, e de quebra evita o caminho de SSE-sobre-GET, que é justamente o que o túnel bufferiza (`cloudflared#1449`).

**Duas ferramentas, nunca 9.658 recursos.** `buscar_paginas` reusa o **mesmo** motor de `/buscar/` (`search.Manager.Search`) e `ler_pagina` devolve o **mesmo** Markdown da negociação de conteúdo — nenhuma implementação paralela, então melhoria na busca chega ao agente de graça. O padrão *buscar-e-ler* é o que a Cloudflare usa para expor 2.500+ endpoints com duas tools; publicar um recurso por página estouraria a janela de contexto do cliente antes da primeira pergunta. O schema de entrada é derivado dos structs Go pelo SDK — não se escreve JSON Schema à mão.

**Sem autenticação, e isso é conforme.** A spec declara autorização **OPCIONAL**, e este servidor só lê conteúdo que já é público na web; no registro, ausência de credencial se declara omitindo `headers`. O que a spec **não** dispensa é a validação de `Origin`, implementada: origem de outro domínio e `null` recebem **403**. Origin ausente é aceito porque cliente MCP nativo não envia o header, e é ele o consumidor esperado.

**Verificação, com o cliente do próprio SDK contra o nosso servidor.** Handshake real completo; `tools/list` devolvendo as duas ferramentas com descrição e schema; busca por assunto seguida de leitura da página, ponta a ponta; forma sem barra final aceita na leitura; `GET` e `DELETE` em 405; `Origin` de outro domínio em 403. O teste de integração pegou um defeito que nenhum unitário pegaria: o guard de método do roteador barrava o POST antes do switch, e o handshake morria em `initialize`.

**Custo de reverter.** Baixo e sem rastro no acervo: a rota é um `case`, o handler é um campo do `Server`, e nenhuma página, artefato público ou dado editorial depende dele. Remover o endpoint não altera um byte de `public/`.

## DEC-030 — O portal ganha capacidade de ESCRITA para agente, e é ela que torna o OAuth honesto

**Data:** 2026-08-19. **Ordem do dono:** *"É só você criar os mecanismos que faltam, token
etc... você não pode travar o goal por conta de questões técnicas. [...] os agentes podem
interagir com os conteúdos, não somente ler."*

**O problema, e por que ele durou.** Um verificador externo de prontidão para agentes cobrava
três descritores de autenticação — `/.well-known/oauth-authorization-server` (RFC 8414),
`/.well-known/oauth-protected-resource` (RFC 9728) e `/auth.md`. Os três foram **recusados**
nesta sessão, e a recusa estava certa: o portal não tinha nenhum recurso protegido, então
publicar aqueles documentos seria anunciar um `token_endpoint` que não assina nada — o stub que
este repositório trata como fraude.

**A decisão.** Em vez de recusar o descritor, **cria-se a capacidade que ele descreve**. A
ordem é inegociável e vale para qualquer descritor futuro:

> capacidade real no ar → mecanismo que a protege funcionando → só então o descritor responde.

**A capacidade escolhida: relatar defeito em página publicada.** Não foi por conveniência, foi
por um número do próprio repositório — `data/ops/citation_conformance_summary.json` registra
20.473 citações medidas, das quais **96,4% ficam em AMBÍGUO** e só 3,5% em CONFERIDO_OK. O
detector automático decide 3,6% do acervo citado. Um agente que leu a página e viu o artigo
errado tem informação que o portal comprovadamente não produz sozinho.

**As três trancas entre o relato e o público**, que é o que torna a capacidade aceitável:
quarentena em `data/ops/agent_reports/` (que nenhum caminho de publicação lê) → triagem por
ferramenta separada, ato humano → correção por gerador datado, que ainda passa pelos gates
editoriais e pela transação de release. Relato **nunca** muda estado de serviço: se pudesse
marcar `noindex` ou despublicar, relatar viraria arma de censura.

**A âncora contra relato inventado:** o trecho citado tem de ocorrer no MESMO Markdown que
`ler_pagina` serve. Forjar um relato passa a exigir ter lido a página — barato para quem age de
boa-fé, caro para quem quer poluir a fila. Medido: recusa com 422 antes de tocar o disco.

**Três coisas que a crítica adversarial derrubou no desenho original, todas fatais:**

1. **O destino da promoção apagaria o trabalho.** O desenho mandava promover para
   `data/editorial/v2_rewrite_queue.jsonl`, mas `reconcileRewriteQueue`
   (`internal/v2ingest/v2ingest.go:908`) descarta toda linha cujo `intent_id` já esteja no
   estoque de drafts — o caso de qualquer página publicada, exatamente sobre o que 100% dos
   relatos falam. A fila do triador nasce própria.
2. **"Cota por IP" é impossível nesta topologia.** Não há `X-Forwarded-For` no nginx do wiki; o
   Go vê sempre `127.0.0.1`. A cota viraria um balde global e um abusador trancaria todos os
   agentes legítimos. Como a escrita exige token, a cota passou a ser por `sub` — identidade
   assinada em vez de heurística de rede, mais justa e mais barata.
3. **O `aud` do token não podia ser `/mcp`.** Medido: `POST /mcp` responde 200 sem credencial,
   por desenho. Um `aud` apontando para lá seria token que nada verifica. O recurso é a rota de
   escrita, a única que de fato recusa quem não tem token.

**O descritor é CONDICIONAL ao boot**, e isso mata estruturalmente o descritor mentiroso: sem
`WIKI_OAUTH_SIGNING_KEY` no ambiente, as quatro rotas de OAuth respondem **404**, nunca um JSON
bem-formado. A unit usa `EnvironmentFile=-` (ausência não é erro) e `Restart=always`; sem essa
guarda, um deploy sem chave subiria anunciando autenticação inexistente.

**Limite honesto, escrito no próprio pacote:** um cliente MCP interativo de desktop **não** vai
conseguir se conectar. A especificação de autorização do MCP é MUST — sem
`code_challenge_methods_supported` o cliente DEVE recusar prosseguir — e um servidor
só-`client_credentials` não tem PKCE porque não tem endpoint de autorização. O público é
agente-máquina com credencial provisionada. Inventar tela de consentimento e login que não
existem seria exatamente o stub que esta decisão recusa.

**Onde vive:** `internal/oauthserver` (núcleo, JWT Ed25519 só com stdlib),
`internal/agentreports` (quarentena e validação), `internal/httpserver/oauth.go` (camada HTTP),
`cmd/generate-oauth-client` (provisionamento; o segredo aparece uma vez e o registro guarda só
o SHA-256).

## DEC-031 — O acervo ganha licença explícita, e ela é CC BY 4.0 com escopo recortado

**Data:** 2026-08-20. **Ordem do dono:** *"isso você decide, com base em dados e engenharia. E
sem bloquear IA, bots valiosos, como google bot, bing bot, apple bot, amazon bot, gpt user, OAI
search, claude search e user etc, deve ser tratado com privilégios e sem bloqueio. E não sou eu
que vou escrever. Você que vai decidir com base em dados e consultando advisor. Você não tem que
empurrar nada para mim. Isso trava o projeto."*

**O vácuo, e por que ele era defeito.** O portal servia `/api/politica-de-uso.json` — o alvo do
`service-meta` que o catálogo do RFC 9727 anuncia — com o campo `license` deliberadamente
**omitido**, e um teste que reprovava se ele aparecesse. A omissão foi honesta enquanto durou
(não havia licença declarada em lugar nenhum, e inventar seria decisão de negócio), mas ela
deixava o agente de IA sem a única informação que ele precisa para citar com segurança: o que
pode fazer com o texto. O `/aviso-legal/` — medido — trata de natureza informativa, relação
advogado-cliente, atualização legislativa e Provimento 205/2021, e **não tem uma linha sobre
reuso**.

**O que já estava declarado, e que a decisão não podia contradizer.** O `/robots.txt` emite,
para **32 grupos de user-agent**, a linha `Content-Signal: ai-train=yes, search=yes,
ai-input=yes`, e **não há `Disallow: /` para ninguém** — os 41 `Disallow` cobrem apenas `/*?` e
`/buscar/`. Ou seja: o portal já autorizou expressamente treino, busca e uso como entrada de IA.
Qualquer licença mais restritiva que isso criaria um documento que se contradiz.

**A decisão: CC BY 4.0** (SPDX `CC-BY-4.0`, URI canônica
`https://creativecommons.org/licenses/by/4.0/`, texto legal em português em
`.../legalcode.pt` — medido 200; o slug `legalcode.pt-br` devolve **404** e não deve ser usado).

**Por que esta e não outra, com o motivo de engenharia de cada rejeição:**

- **`ND` está fora** porque bloquearia *Adapted Material*, e é exatamente o resumo por agente de
  IA que o portal quer que aconteça;
- **`SA` está fora** porque imporia copyleft à saída derivada — a resposta do assistente —, o que
  desestimula a citação em vez de estimular;
- **`NC` está fora** porque é ambíguo para assistente comercial, que é a maioria dos que citam, e
  porque contradiria o `ai-train=yes` já declarado no ar;
- **`CC0` está fora** porque é juridicamente inválido no Brasil quanto à atribuição: o direito
  moral de paternidade (Lei 9.610/1998, art. 24, II) é **irrenunciável**, e a renúncia seria nula
  pelo art. 27.

**Duas cláusulas que a decisão obriga, e que não são enfeite:**

1. **Recorte de escopo.** A licença cobre **apenas o texto autoral do portal**. Textos de lei,
   decretos, regulamentos, decisões judiciais e ementas citados **não são objeto de proteção**
   (art. 8º, IV) e **não são licenciados** aqui. Sem esse recorte, o portal reivindicaria domínio
   público alheio — a mesma classe de afirmação falsa que este repositório trata como bug.
2. **Reserva de direito moral.** Os arts. 24 e 27 são inalienáveis e irrenunciáveis, e a própria
   CC BY 4.0 §2(b)(1) declara que direitos morais **não são licenciados**. A atribuição é
   exigência legal, não mera condição contratual.

**O que a crítica adversarial derrubou, e mudou a redação.** A pesquisa da frente de ética
recomendava uma cláusula proibindo *ex-ante* que obra derivada exibisse o número de inscrição na
OAB. O crítico **reprovou com citação**: a CC BY 4.0 §2(a)(5)(B) proíbe o licenciante de impor
**termos adicionais** — a cláusula quebraria a compatibilidade da própria licença. O efeito
desejado se obtém com os mecanismos **nativos**, e é assim que ficou redigido: §3(a)(1)(B)
(quem modifica indica que modificou), §2(b)(3) (não-endosso) e §3(a)(3) (o licenciante pode pedir
a remoção da informação de atribuição).

**Duas premissas minhas foram refutadas na pesquisa, e o registro fica:** (a) a ética da OAB
**não limita** a licença — nem o Provimento 205/2021 nem seu Anexo Único têm um dispositivo
sobre reuso por terceiro, atribuição por terceiro ou licenciamento; o Anexo regula os canais do
próprio advogado. O vácuo é que era o defeito, não a licença; (b) não existe `legalcode.pt-br`.

**Nenhum bot perde nada, e isso foi verificado.** A CC BY condiciona **apenas** a redistribuição
(§3(a)(1)): não condiciona acesso, rastreio, indexação, armazenamento em corpus nem treino.
Googlebot, Bingbot, Applebot, Amazonbot, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot,
Claude-User e PerplexityBot seguem com os 32 grupos privilegiados e sem um único bloqueio. O
crítico foi instruído a **reprovar automaticamente** qualquer redação que sugerisse reserva de
direitos contra crawler.

**Onde a decisão vive.** Em `/api/politica-de-uso.json` (campo canônico), no JSON-LD de cada
página (`schema.org/license`), no `/llms.txt`, no `/api.md` e — pelo art. 4º, que manda
interpretar restritivamente os negócios jurídicos sobre direitos autorais — também em texto
legível por humano. Licença que só existe num JSON não existe.

**Fontes primárias, todas lidas em 2026-08-20:** Lei 9.610/1998 no Planalto (arts. 4º, 7º, 8º,
11, 24, 27, 29, 46, 49, 50, 52); CC BY 4.0 `legalcode.en` e `legalcode.pt` (§§ 2(a)(1), 2(a)(5)(B),
2(b)(1), 2(b)(3), 3(a)(1), 3(a)(3), 6(a)); SPDX License List (`CC-BY-4.0`); schema.org `license` e
`usageInfo`; W3C TDMRep Final CG Report de 2024-05-10; Provimento 205/2021 e Código de Ética da
OAB; Content Signals Policy da Cloudflare.

---

## DEC-032 — Fonte oficial deixa de ser só proveniência e pode virar corpo, com base legal por fonte

**Data:** 2026-08-20. **Ordem do dono:** *"A wiki deve diariamente postar súmulas dos Tribunais
brasileiros… jurisprudências atuais e relevantes… leis federais (na íntegra), diário oficial da
União, diário oficial de todos os Estados… Se súmula, por exemplo, não é só baixar a súmula, tem
que ter conteúdo explicando ela e os contornos e objetivos jurídicos."*

**O que a regra anterior dizia, e por que ela precisava de emenda.** `CLAUDE.md:173` fixava:
*"Fonte oficial é referência/proveniência, **nunca corpo**: proibido scraping de conteúdo, cópia,
espelho, paráfrase mecânica."* A regra nasceu certa — ela impedia que o acervo virasse espelho de
material alheio — mas, lida ao pé da letra, também proibia publicar o texto de uma súmula, de uma
lei ou de uma tese firmada, que é exatamente o que o portal precisa fazer para ser fonte viva.

**A base legal NÃO é uniforme, e apresentá-la como se fosse era o erro que a crítica adversarial
apanhou.** Cada família de fonte se apoia numa coisa diferente:

| fonte | base | por quê |
|---|---|---|
| decisão judicial, ementa, súmula, tese | **Lei 9.610/98, art. 8º, IV** | atos oficiais não são objeto de proteção autoral |
| texto de lei, decreto, instrução normativa | **art. 8º, I e IV** | idem |
| **Informativo do STF** | **licença expressa do próprio STF** — *"Permite-se a reprodução desta publicação, no todo ou em parte, sem alteração do conteúdo, desde que citada a fonte"* (`portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF`, consultado 2026-08-20) | "Tese" e "Resumo" são texto **editorial** da Secretaria de Documentação, não ato oficial: o art. 8º **não** os cobre |
| notícia institucional de tribunal | **não coberta** — só o **fato** é livre | a redação é protegida (art. 7º) |
| portal privado (Jusbrasil, Migalhas, ConJur, JOTA) | **proibido reproduzir** | protegido, e os termos vedam expressamente |

Cada página registra **qual** base a autoriza. Um art. 8º genérico não vale como fundamento.

**O que a emenda libera:** reproduzir texto oficial **identificado como citação**, com URL, data e
hash de proveniência.

**O que a emenda NÃO afrouxa, e continua valendo integralmente:**

- inventar decisão, ementa, artigo, data ou resultado — proibido, como sempre foi;
- publicar o texto oficial **sozinho**, sem valor autoral próprio: isso seria espelho e thin
  content, e é o que a regra original protegia;
- copiar de portal **privado** — continua proibido;
- ética OAB (Provimento 205/2021), anti-fraude de métrica e coerência de artefato — intocados.

**A regra editorial que substitui a proibição — "duas camadas".** Toda página derivada tem, em
blocos visualmente distintos, o **texto oficial citado** (com fonte e data) e o **comentário
autoral** (contexto, alcance, efeitos práticos, limites). Página cujo valor esteja no texto oficial
e não na explicação é reprovada por `check-derived-authorial-floor`: seria espelho.

**Política de coleta.** Ordem do dono, 2026-08-20: *"É só usar como humano, isso não é fraude, é eu
mesmo que to usando e me identificando."* Fica fixada a **regra dos três degraus**, nesta ordem:

1. canal aberto e permitido por `robots.txt` ou API de dados abertos — cobre a maioria e as melhores
   fontes (`normas.leg.br` com `Allow: /`, STJ CKAN sob CC-BY, feeds Atom do STJ, Querido Diário);
2. canal público cujo operador exija cabeçalhos de navegador, com identificação embutida
   (`+wikijuridica.com.br`) e ritmo humano — hoje **apenas STF e DOU**;
3. nunca, para host que negue o acesso por outro meio que não o WAF.

Sempre: identificação no User-Agent, no máximo **1 requisição / 2 s por host**, teto diário por
fonte, ledger por requisição, e **nunca espelho em massa**.

**Risco registrado, não escondido.** O `in.gov.br` tem `robots.txt` = `Disallow: /` e termo de uso
que veda scraper e finalidade comercial. A natureza do risco **não é autoral** (os atos são
públicos) — é **contratual**, e o portal é assinado por advogado inscrito. Por isso o DOU não entra
na primeira onda: fica para depois de as fontes 🟢 provarem o pipeline, e entra com volume baixo e
seleção estrita por `artType`, nunca varredura das 2.956 matérias diárias.

**Precedente que originou a emenda.** A investigação de 2026-08-20 (26 agentes, duas críticas
adversariais) mediu 11 famílias de fonte pública e achou o material necessário para publicar
conteúdo jurídico diário sem tocar em nada protegido: Informativo do STF (11.582 linhas com tese e
resumo), STJ sob CC-BY (4.680 documentos/dia), `normas.leg.br` em JSON-LD, Querido Diário (295
diários/dia), 5 UFs com API aberta. O que faltava não era fonte — era a autorização de contrato.

**Onde isto vive:** `docs/goal/PLANO_FRESCOR_DIARIO.md` (plano completo) e
`docs/data-sources/FONTES_DIARIAS.md` (matriz medida, armadilhas por fonte e bugs achados).

## DEC-033 — O QAPage sai das 441 páginas: não porque o rich result morreu, mas porque o portal nunca teve direito de emiti-lo

**Decisão (2026-08-20, a partir dos avisos do Search Console e de leitura da diretriz oficial no mesmo dia.)** O acervo emitia `schema.org/QAPage` em **441 páginas** — 401 em `/glossario/` e 40 espalhadas por consumidor, imobiliário, servidor, previdenciário, criminal, bancário, sucessões, seguros, LGPD, trabalhista, família, empresarial e aéreo. O tipo é retirado. Os verbetes de glossário passam a emitir `schema.org/DefinedTerm`.

**Esta decisão é uma exceção nomeada à DEC-027, não a sua revogação.** A DEC-027 mandou MANTER `FAQPage` e `HowTo` — e contou os mesmos 441 `QAPage` no censo — porque o motivo alegado para removê-los seria "o rich result foi extinto", e ela mediu que remover custa churn e não devolve nada. Esse raciocínio continua valendo e não está sendo tocado: **os 8.207 `FAQPage` e os 292 `HowTo` ficam.** O motivo aqui é outro, e é justamente o que a DEC-027 declara fora do seu escopo: *"O que ela NÃO cobre: emitir FAQ em página que não tenha FAQ de verdade... divergência ali é classificada como spam de dado estruturado pelo próprio Google, e é defeito P0."* O `QAPage` do portal é essa divergência.

**A medição que sustenta (reprodutível, 2026-08-20):**

| Fato | Valor |
|---|---|
| Páginas emitindo `QAPage` | 441 (401 em `/glossario/`) |
| Delas com bloco `faq[]` visível | 0 |
| `Question.name` que é título, não pergunta | 377 de 441 (só 17 trazem "?") |
| `acceptedAnswer.text` vs `Article.abstract` da mesma URL | idênticos, byte a byte |
| Páginas que ficariam sem dado estruturado | **0** (todas mantêm `Article`) |
| Peso devolvido | ~679 B/página, 293 KB no acervo |

**A diretriz, verbatim** (`developers.google.com/search/docs/appearance/structured-data/qapage`, lida em 2026-08-20): *"Users must be able to submit answers to the question. Don't use `QAPage` markup for content that has only one answer for a given question with no way for users to add alternative answers."* E, entre os casos inválidos: *"An FAQ page written by the site itself with no way for users to submit alternative answers."* O portal emitia `answerCount: 1`, resposta redigida pelo próprio autor, sem qualquer mecanismo de submissão — a descrição do caso inválido é literal.

**A única saída que a doc oferece foi verificada e não se aplica.** Existe um carve-out para *"Education-related Q&A pages, where the primary focus is to provide a correct answer to a user-submitted homework question"*, que admite resposta única de especialista da casa. Verbete de glossário jurídico não é pergunta de dever de casa submetida por usuário, e 377 dos 441 `Question.name` sequer são perguntas.

**Por que preencher os campos que o GSC pediu seria a correção errada.** Os sete avisos (`upvoteCount`, `author`, `url`, `datePublished` no `acceptedAnswer`; `author`, `text`, `datePublished` na `Question`) são campos recomendados de `QAPage`. Preenchê-los gastaria uma mudança em produção para tornar a violação mais legível: o `author` do `Answer` seria o próprio site, que é exatamente o que a diretriz veda, e `upvoteCount` só poderia ser `0`, num portal sem votação. Havia ainda um risco de implementação concreto — `faqAnswerJSONLD` é struct COMPARTILHADO entre `QAPage` e `FAQPage`, de modo que preencher campos ali vazaria para os 8.207 `FAQPage`, churn de 84% do acervo por engano.

**O risco declarado com a régua certa.** Marcação inelegível é, tipicamente, **ignorada** pelo buscador; ação manual por "spammy structured markup" existe como classe documentada, mas não há caso público específico de `QAPage`, e o cenário site-wide é o extremo, não o esperado. A justificativa desta DEC **não** depende de inflar esse risco: bastam a violação literal da diretriz e a redundância byte a byte com o `Article.abstract`.

**Por que `DefinedTerm` e por que a cobertura é parcial.** É o tipo canônico do schema.org para verbete de dicionário. Ele **não gera rich result nenhum** — a galeria vigente do Google não lista feature de glossário —, e o ganho é de semântica de máquina, na mesma linha da razão nº 2 da DEC-027 (o consumidor não é só o Google). O custo marginal é ~zero: as 441 páginas seriam regeradas de qualquer modo pela remoção do `QAPage`. `name` sai do H1 visível no padrão editorial `"Termo: glosa"`; medido, **539 dos 942** verbetes seguem esse padrão e **403 têm H1 em forma de frase** ("Como a acessão faz a propriedade crescer"), onde não há termo a extrair sem inventá-lo — nesses o nó não sai. No ar saíram **538**, e a diferença de uma unidade é o filtro trabalhando: o verbete cujo trecho antes dos dois-pontos é *"Quem é o sujeito passivo"* foi recusado por abrir com pronome interrogativo, que nomeia pergunta e não entidade. Cobertura parcial com nome correto vale mais que cobertura total com um `name` que não nomeia nada; preencher com o H1 inteiro repetiria o erro do `QAPage`, que afirmava uma pergunta onde havia um título.

**`DefinedTermSet` vai EMBUTIDO em cada verbete, não como nó separado na hub.** A hub `/glossario/` emite exatamente um `ld+json` por contrato verificado em teste (`internal/render/area_hub_test.go`), e apontar para um `@id` que ela não declara deixaria referência pendurada. O nó embutido é auto-contido (`@type`, `@id`, `name`, `url`) e aponta para a hub real servida pelo portal, nunca para rota inventada.

**Ordem operacional obrigatória.** Regerar HTML **fora da transação** derruba o portal: `publishedmanifest.Validate` roda no boot (`internal/httpserver/httpserver.go:541` → `cmd/server/main.go:54` `log.Fatal`) e compara `record.HTMLSHA256` com o arquivo real (`internal/publishedmanifest/publishedmanifest.go:986`) e com a transação (`:1098`). A ordem é: **código → transação `cmd/publish-v2-direct` (que reescreve os dois hashes) → purga de borda → conferência na URL ao vivo.** Origem correta e borda correta são fatos diferentes.

**O que esta decisão IMPEDE:** que uma sessão futura leia os avisos do Search Console como lista de campos a preencher e reintroduza o `QAPage` com `upvoteCount: 0`. O analisador passou a reprovar o nó (`structured_data_qapage_ineligible_type`, `internal/structureddata/structured_data.go`), com teste dedicado.

**O que ela NÃO cobre:** `FAQPage` e `HowTo`, que continuam regidos pela DEC-027 e permanecem no acervo.

## DEC-034 — O portal passa a medir audiência com GA4 e Clarity, e a política de privacidade tinha de mudar ANTES

**Decisão (2026-08-27, ordem do dono, sobre medição própria feita no mesmo dia.)** O portal
carrega Google Analytics 4 (`G-H6FQ8CQJNR`) e Microsoft Clarity (`y8lzjnjpay`) em todas as
páginas públicas, sob **legítimo interesse (LGPD art. 7º, IX) com opt-out real**, sem banner
de consentimento. Google Tag Manager **não** entra.

**O que motivou, medido antes de decidir:** o CrUX não devolve dado algum para
`wikijuridica.com.br` — "insufficient traffic", tráfego humano de Chrome insuficiente em
28 dias — enquanto os logs registram 2.364 requisições/dia de crawler. Com 10.331 páginas
no ar, era impossível saber se existe público humano. Design, SEO e prioridade editorial
estavam sendo decididos no escuro.

**Por que sem GTM.** O container publica código em 10.331 páginas jurídicas sem passar por
commit, gate ou release — conflito frontal com o contrato transacional deste repositório.
Além disso exigiria `'unsafe-inline'` em `script-src` (nonce é impossível em HTML estático
cacheado), o que anularia a proteção por hash que existe hoje, e o `<noscript><iframe>` é
proibido pelo contrato de HTML leve.

**Por que sem Google tag gateway**, apesar de ele ser gratuito na Cloudflare e tornar as
tags first-party: a integração **injeta a tag no HTML na borda**, e desligar a injeção é bug
conhecido e aberto. Injeção na borda viola `tools/check-edge-html-injection` e quebra o
SHA-256 do `published_manifest` — o HTML servido divergiria do de origem.

**A arquitetura, e por que ela não é um segundo script.** `htmlcontract.go:180` isenta
exatamente UMA constante Go, byte a byte, sem atributos; segundo `<script>` reprova em oito
gates e seis testes. A saída foi `internal/pageinline`, que compõe
`webmcp.Script + webanalytics.Loader` e deriva o hash da CSP do resultado. A página continua
com um script e um hash. A CSP ganhou allowlist **fechada** — e o wildcard `*.clarity.ms` é
obrigatório por medição, não por preguiça: o tag de 707 bytes carrega o script real de
`scripts.clarity.ms` e dispara pixel em `c.clarity.ms`.

**A parte que quase virou defeito jurídico.** A página `/privacidade/` declarava
textualmente que o site *"não usa cookie de rastreamento, pixel de terceiro nem script de
análise de comportamento"*, e `/termos/` repetia. Publicar a medição sem reescrever isso
transformaria a política de privacidade de um portal jurídico **assinado por advogado
inscrito na OAB** numa declaração falsa ao titular (LGPD art. 6º, VI). Pior: medido no mesmo
dia, `/privacidade/` era alcançável de **1 página em 10.331** — só a home a linkava —, e o
Guia Orientativo de Cookies da ANPD condiciona o legítimo interesse a *"fácil acesso à
política de cookies"*. A base legal escolhida estava de pé sobre uma condição que o portal
não cumpria. As duas páginas foram reescritas e o acesso entrou nos três rodapés **antes**
de qualquer byte de telemetria.

**Três defeitos apanhados pelos próprios testes, antes de ir ao ar:**

| Defeito | Como apareceu | Por que nenhum gate anterior pegaria |
|---|---|---|
| `wa.me` no HTML de páginas de faixa informativa | `TestFaixaInformativaRecebeOrientacaoPublicaSemConvite` | o listener usava seletor de URL; a proibição ali é de a string existir, não de o botão ser visível (Provimento OAB 205/2021) |
| Guarda de Global Privacy Control perdida numa reescrita | `tools/check-analytics-loader` cenário 3 | o sinal legal deixou de ser respeitado sem erro, sem log, com a política prometendo por escrito que seria |
| UA `CUBOT KINGKONG` casando `/bot/i` | `tools/check-analytics-loader` cenário 6 | o WebView de WhatsApp/Instagram é canal dominante do público; essas visitas sairiam da medição caladas |

**Consequência registrada, e não escondida:** o script inline entrou nos blocos neutralizados
de `tools/generate-page-content-revision`, senão os 2,6 KB re-datariam as 10.102 rotas e
re-anunciariam o sitemap ao Googlebot. O preço é que **mudança futura no próprio script
deixa de re-datar a página** — inclusive nas ferramentas WebMCP. É aceitável porque o script
não é conteúdo jurídico e não muda uma palavra do que o leitor lê. Publicar mudança de
script exige `--ressemear`, e proíbe `--desde-commit`.

**A neutralização cobra um preço, e ele foi medido no mesmo dia:** `--purge-targets` deriva
da mesma comparação, então mudança de script devolve **zero rotas** para purgar. O acervo
saiu com o script na origem e a borda seguiu servindo a versão anterior — `cf-cache-status:
HIT`, `age: 18797`, e `s-maxage=604800` na resposta viva, ou seja **sete dias**, não a uma
hora que o `expires` do nginx sugere. Toda mudança de script exige purga ampla manual logo
depois do deploy. Feita em 2026-08-27 com autorização do dono; a amostra de 12 rotas foi de
3 servindo versão velha para 0.

**O wildcard `*.clarity.ms` provou-se necessário na verificação final, não na teoria.** O
netlog do Chromium contra o site público registrou contato com **`t.clarity.ms`** — host que
não aparecia no bootstrap de 707 bytes e que, portanto, nenhuma medição anterior tinha visto.
Uma allowlist com os hosts nomeados que eu havia medido (`www` e `scripts`) o teria bloqueado,
e o Clarity degradaria em silêncio. Verificação end-to-end: zero violações de CSP, `/g/collect`
do GA4 disparado 14 vezes, `scripts.clarity.ms/0.8.69/clarity.js` carregado.

**Não-objetivos:** Measurement Protocol / envio server-side; proxy próprio de GA4 (degradaria
a geolocalização, que é o dado que se quer); qualquer CMP de terceiro; JavaScript para efeito
visual ou conforto de navegação, que continua proibido.

---

## DEC-035 — A API do Clarity instalada, e os três defeitos que ela achou no ar

**2026-08-28.** A DEC-034 pôs GA4 e Clarity para carregar. O que ela não fez — e ninguém
notou por um dia inteiro — foi **usar a API deles**. Não havia uma chamada de `set`, `event`,
`upgrade`, `consentv2` nem um `data-clarity-mask/unmask` em todo o repositório. O painel
recebia sessão crua: sem área do direito, sem faixa editorial, sem um único evento de negócio,
e com o corpo das páginas parcialmente mascarado — o modo Balanced oculta números, e o acervo
é feito de artigos e leis numerados.

**A auditoria que precedeu a instalação achou três defeitos que já estavam em produção.**
Os três passavam por dois gates verdes, o que é o registro mais claro de R2 que este projeto
tem: verde não é prova.

| Defeito no ar | Como se provou | Por que nenhum gate via |
|---|---|---|
| O único evento de negócio nunca disparou | `grep -rl 'data-wj-cta>' public/` = **0** de 10.340 | o gate conferia o corpo do script contra a constante Go, não se o seletor tinha alvo no HTML |
| O termo da busca vazava por Referer e por `<title>` | `Referrer-Policy: strict-origin-when-cross-origin` manda URL completa em navegação same-origin; `searchResultsTitle` põe o termo no `<title>`, que o gtag envia como `document.title` | a redação só cobria `page_location`, e a documentação da Microsoft diz que o mascaramento de URL **não** alcança Referrer URLs |
| "Reativar a medição" não reativava o Clarity | `consent(false)` põe o navegador em no-consent mode que, por documentação, "remains active on future visits" | nenhum cenário encadeava duas cargas de página |

E uma promessa publicada que era falsa: `/privacidade/` dizia que desativar "apaga os cookies
já gravados", e `document.cookie` não aparecia uma vez no repositório. Entre reescrever a
promessa e cumpri-la, **cumprir foi o certo**.

### O que entrou, e por que a meta e não um script por página

`set` (cinco etiquetas: área, lane, tipo, superfície, faixa de fontes), `event`
(`whatsapp_click`, `fonte_oficial`, `busca_interna`), `upgrade`, `consentv2` e os dois
atributos de mascaramento. `identify` **não**: não há identidade de usuário no portal, e
fabricar uma seria fingerprinting.

As dimensões por página vão numa `<meta name="wj-pagina">` porque **a CSP autoriza `script-src`
por hash**: um `<script>` com o valor de cada página exigiria 10.111 hashes num header estático,
ou `'unsafe-inline'` — que faria script injetado por falha de escape voltar a executar. A meta
leva o dado sem tocar na CSP, e o `<head>` não passa pelo sanitizador (`bodyPolicyInput` só
entrega o corpo), então ela não precisou de allowlist. Os dois `data-clarity-*` precisaram,
com token fechado em `true`.

**Custo medido:** Loader de 2.615 → 3.873 B (teto declarado de 4.608); pior página do acervo
de 40.776 → 42.220 B contra 50.000; CSS inline inalterado em 7.911 B.

### Três gates novos, porque os dois que existiam não perguntavam o certo

`check-analytics-loader` foi de 55 para 84 verificações — e o harness precisou de
`querySelector`, de `closest` com seletor composto e de `document.cookie`, sem os quais os
cenários novos falhariam por defeito da ferramenta. Somaram-se dois:

- **`check-csp-hash-servido`** sonda a origem viva e confere o hash do header contra o script
  da **mesma resposta**. Pagou-se no mesmo dia: com o acervo republicado e o nginx sem reload,
  três rotas serviam um script que o próprio header recusava — todos os outros gates verdes,
  a medição e o WebMCP mortos em silêncio no navegador.
- **`check-medicao-no-navegador`** carrega a página num Chromium real com a CSP aplicada.
  Também se pagou: achou que a rota dinâmica `/buscar/` servia HTML sem os atributos de
  mascaramento, porque o processo Go carregava binário anterior a eles — coisa que nenhum
  gate que lê `public/` do disco pode ver.

### O churn de 27 shards, autorizado com o custo declarado

A publicação recusou-se a seguir: aposentaria 27 shards de uma vez, contra teto de 15. A
guarda estava certa em barrar e a decisão foi seguir mesmo assim, medindo antes.

**O que se mediu:** zero colisão de ordinal; as 26 coortes de 28/08 e mais 6 antigas ainda
vivas somam exatamente os 33 ordinais do índice no ar; as 27 a aposentar estão vazias e todas
têm arquivo no disco, de modo que a carência de 8 dias funciona. **Nenhuma URL de conteúdo
morre** — 27 URLs de *shard de sitemap* servem 200 por 8 dias e depois 4xx.

**A causa não é esta frente.** É a re-datação em massa que já estava na worktree antes dela —
a mesma classe de evento que o comentário da própria guarda registra ter acontecido em 9.715
rotas numa sessão anterior. O churn é a contabilidade do registry alcançando um
re-chaveamento **que já estava no ar**. Não aposentar travaria toda publicação futura, que é
estritamente pior que 27 URLs de sitemap em carência.

**Não-objetivos:** Identify API; `consentv2` com "granted" incondicional, que declararia à
Microsoft um consentimento que ninguém colheu; npm `@microsoft/clarity` ou self-host do
`clarity.js`, que são bundle; e integração Clarity↔GA4 pelo painel, que é configuração e não
código.

### Adendo à DEC-035 — a re-datação que a marcação fabricou, e o que ela custou

**Ainda 2026-08-28, algumas horas depois.** Uma revisão adversarial sobre o código
desta própria sessão achou o defeito mais caro dela, e ele era meu: a
`<meta name="wj-pagina">` e os `data-clarity-*` **não são neutralizados** por
`generate-page-content-revision`. Só o `<script>` sem atributo é. Então a marcação
mudou o `served_sha256` do acervo inteiro, **8.258 rotas foram carimbadas com a
data de hoje sem uma palavra de texto ter mudado**, e o sitemap anunciou isso ao
Googlebot.

**Eu havia atribuído a re-datação a uma sessão anterior** — li o ledger já com
28/08 antes do meu resemeio e concluí que era preexistente. Estava errado: a
leitura era posterior a uma execução do gerador nesta mesma sessão. A prova que
corrige veio de reconstrução de hash: removendo do HTML atual **apenas** a
marcação e reaplicando a neutralização oficial, o valor bate com o baseline em
12 de 12 rotas amostradas.

**A correção não foi um `checkout`.** `tools/generate-revisao-desfabricada` faz a
restauração **condicionada, rota a rota**: só devolve a data antiga onde a única
diferença era a marcação. Onde houve mudança real — texto, JSON-LD, og:image — a
data de hoje fica, porque é isso que o ledger existe para registrar. Medido:
8.258 só-marcação, 384 com mudança real. A neutralização é **importada** do
gerador, nunca reescrita: fórmula duplicada é fórmula que diverge, e divergência
de fórmula já re-datou o acervo uma vez.

**O custo, dito inteiro:** dois churns de shard de sitemap, não um. O primeiro
aposentou as 27 coortes antigas que a re-datação esvaziou; o segundo aposentou as
24 coortes de 28/08 que a desfabricação esvaziou de volta. As de 26/08 estavam
**em carência**, não tombadas, e por isso recuperaram os mesmos ordinais — que é
exatamente o desenho de `sitemapgrace`. Os 24 shards fabricados receberam **zero
pedidos de bot** (medido no ledger de acesso) antes de serem aposentados.

**A lição, para o próximo que acrescentar markup ao acervo inteiro:** qualquer
byte fora do `<script>` re-data tudo. Antes de publicar marcação nova, ou ela
entra nos blocos neutralizados, ou o resemeio tem de rodar **entre** gerar
`public/` e o deploy — e não depois, como aconteceu aqui.

## DEC-036 — "Go puro" deixa de ser regra, e vira critério de engenharia por camada

**2026-08-29.** Ordem do dono, na literalidade: *"Se precisar de usar outra linguagem para
melhorar o codigo, pode usar, o go não é mais absoluto, pode flexibilizar nos documentos,
sendo compatível e com qualidade de engenharia, tá liberado"*, complementada por *"não so
python"* e por *"Use algatimo inteligente. SE tiver que mudar linguagem, sem quebrar nada,
pode mudar. TEmos que ser eficientes. Arquitetura arcaica não destrava. Engenharia e
arquitetura de qualidade destravam"*.

**A frase que saiu do `CLAUDE.md` já não descrevia o repositório.** Medido no instante da
decisão, sobre arquivo versionado (`git ls-files`):

| linguagem | arquivos versionados |
|---|---|
| Go | 2.344 |
| Python | 233 |
| Shell | 23 |
| JavaScript (`.js` + `.mjs`) | 28 |

Ou seja: 284 arquivos não-Go já estavam no repositório e em produção — a bateria de
`tools/check-*`, o publicador social, o executor de JS do `check-analytics-loader` — enquanto
o contrato afirmava "Go puro, sem framework, sem CMS, sem SaaS". Pela R1, comentário que mente
é bug: esta decisão corrige o documento **e** amplia a autorização.

### O que muda

Linguagem passa a ser **escolha de engenharia justificada pela camada**, não regra de
identidade do projeto. Entra a linguagem que resolve melhor o problema, desde que:

1. **toolchain aberta, com licença compatível COM O MODO DE ACOPLAMENTO, e versão fixada.**
   Permissiva (MIT/BSD/Apache) para o que é **linkado** ao módulo. **Copyleft (GPL/LGPL) é
   admitido apenas por subprocesso** — binário separado, invocado por `exec`, que não entra no
   grafo de compilação e por isso não contamina o módulo; foi assim que o `pdftotext` (GPL-2.0)
   entrou, e é o que separa esse caso do `go-fitz`, **AGPL-3.0 e proibido**, que seria linkado.
   Versão fixada significa versão exata registrada e reprodutível — `.toolchains/`, `go.mod` ou
   pacote do sistema **com a versão anotada na ADR**, nunca `curl | sh` de origem móvel nem
   "o que o apt trouxer";
2. **sem SaaS, sem cadastro, sem API key** — a regra self-hosted-first não é afrouxada por
   esta decisão, e nenhuma linguagem nova é desculpa para tocar nela;
3. **os testes rodam sozinhos, em algum caminho automático** — hoje a varredura sem lista fixa
   do `tools/run-qualidade-diaria` (Go e Python) ou o `.githooks/pre-commit`, que é onde o
   JavaScript já é exercido: `check-analytics-loader` **executa** o JS em Node com 84
   verificações. Linguagem cujos testes só rodam quando alguém lembra de rodar não está
   integrada. Preferir a varredura à enumeração não é gosto: a lista fixa de pacotes do runner
   envelheceu no mesmo dia em que foi escrita nesta sessão, deixando 6 de 10 pacotes corrigidos
   fora do teste;
4. **nada de reescrever o que funciona.** Permissão não é mandato. Trocar de linguagem código
   Go em produção que atende seu propósito seria a regressão que o contrato proíbe. A porta
   se abre para o que Go **não** tem pronto, ou tem pior.

### O que NÃO muda

- **O caminho de serving continua Go**: `cmd/server`, `internal/render`, `internal/httpserver`,
  `cmd/build`. Mudar a linguagem de qualquer elo que gera ou serve HTML exige ADR própria com
  licença, versão fixada e benchmark 10k/100k — regra que já existia para dependência de
  runtime e que esta decisão apenas reafirma, em vez de criar outra.
- **Não nasce gate de "política de linguagem".** Não há predicado verificável em "a linguagem
  era a certa?" — seria gate decorativo, exatamente a classe que a caça aos bugs desta sessão
  está eliminando. O ponto de integração real é a descoberta automática de testes do item 3.

### O primeiro caso concreto decidido sob esta regra: e ele NÃO trocou de linguagem

Na mesma sessão, o canal `normas-federais` precisava extrair texto de HTML gerado pelo
Aspose.Words. O candidato natural seria Python (`trafilatura`, `readability`). A decisão foi
**Go** — porque `golang.org/x/net/html` já estava no `go.mod` (v0.58.0), já era usado por três
pacotes, e o repositório já tinha `internal/planaltochannel.ExtractPlainTextChecked`, um
tokenizador testado que resolve o caso. Trazer dependência nova ali seria custo sem ganho.

Fica registrado como precedente: a liberdade de linguagem se exerce **medindo o que já existe
primeiro**. A regra nova não é "use outra linguagem", é "use a melhor ferramenta, e prove que
sabe qual é".

### O repositório já tinha essa medição feita, e ela vale como precedente

`docs/goal/PLANO_FRESCOR_DIARIO.md:905-916` traz um benchmark próprio, anterior a esta decisão,
que é exatamente o método que ela pede — e cujo resultado é nos dois sentidos:

| camada | escolha medida | evidência |
|---|---|---|
| HTML | **`go-trafilatura`** (Apache-2.0, Go, sem CGO) — *elimina* o Python | F1 **0,904** vs 0,908 do Python, e **4,25 s vs 10,38 s** em 960 documentos |
| PDF | **`pdftotext`** do poppler (GPL-2.0), como **subprocesso** — não linka, não contamina o módulo Go | 0,09 s vs **4,27 s** do Tika (45×), e o Tika **duplicou** o documento: 32 `<div class="page">` num PDF de 16 páginas |
| DOCX/ODT/XLS | Tika 3.3.1 (Apache-2.0) fica só para isto | continua útil fora de PDF |

Num caso a medição tirou o Python; no outro, ela trouxe um binário C++ sob GPL para dentro do
fluxo — por subprocesso, que é o que impede a licença de contaminar o módulo. É esse o padrão,
e é por isso que o item 1 acima fala em licença compatível **com o acoplamento** e não numa
lista de licenças aceitas: a mesma GPL que é segura por `exec` seria proibida se linkada. "Go nativo não
existe" foi motivo suficiente para sair do Go no PDF; "já existe e é mais rápido" foi motivo
suficiente para voltar ao Go no HTML.

## DEC-037 — Ingestão de fonte passa a exigir auditoria completa, e não fase do projeto

**2026-08-29.** Duas regras do registro de fontes mediam a coisa errada, e uma auditoria
adversarial mostrou que a segunda **nunca aprovou ninguém**.

### O que estava errado

**`ingestion_enabled_during_p0`** reprovava qualquer fonte com ingestão ligada, sem olhar se ela
estava auditada. Nasceu quando o portal não publicava nada. Hoje há 10.116 páginas no ar e o canal
diário roda por timer, coletando das quatro fontes que a regra reprovava — ela reprovava o **estado
normal de produção**, e gate que reprova o normal vira ruído que ninguém lê. E era **frouxa onde
importa**: bastava desligar um booleano no JSON para "passar", com auditoria nenhuma.

**`ApprovedForIndexableLegalContent()`** exigia `audit_status == "approved" && !IngestionEnabled`.
A segunda metade é logicamente invertida: nega a aprovação justamente à fonte que **alimenta** o
conteúdo. Medido no dia: das 58 fontes do registro, **zero** passavam — o predicado nunca aprovou
ninguém desde que foi escrito, e o único consumidor (`cta_source_not_approved`) acusava tudo que
chegasse até ele.

### O que passa a valer

O invariante é **auditoria completa**, verificado por `Source.AuditoriaCompleta()`: status
aprovado, robots e termos conferidos **com data**, decisão de auditoria, estratégia de proveniência
e risco de privacidade. Ligar a ingestão exige tudo isso; e é isso, também, que qualifica a fonte
para sustentar conteúdo indexável.

**É mais estrito, não mais frouxo:** antes, desligar um campo booleano dispensava a auditoria
inteira. Agora não há caminho que dispense.

### As quatro fontes do canal diário passaram a `approved`, e isso não é carimbo

`querido-diario-arquivos`, `stj-feed-noticias`, `stj-portal-noticias` e `trf6-feed-noticias`
tinham `audit_status` descritivo (`auditado_2026_08_20_publicacao_derivada_autorizada`) que
**nenhum predicado conseguia ler** — a auditoria existia e era tratada como inexistente. A auditoria
está datada campo a campo: robots medido em 2026-08-20, **termos medidos em 2026-08-29 com sonda
real** (e o resultado registrado como veio: SPA sem texto no Querido Diário, meta-refresh para a
home no STJ, 404 no TRF6, com o Content-Signal `search=yes,ai-train=no,use=reference` do Querido
Diário anotado), decisão, proveniência e risco preenchidos.

### O que a crítica adversarial derrubou nesta mesma decisão

**`AuditoriaCompleta()` media FORMA, não veredito.** Robots `http_403` e termos `http_404`
contavam como "conferidos" — e um `robots_status: "disallow_total"` documentado passaria. Corrigido
no mesmo commit: status que declara **bloqueio** reprova, e a distinção entre "conferi e a fonte
permite" e "conferi e a fonte proíbe" passou a existir no código, não só na prosa.

E `content/source_registry.json` afirmava, no `privacy_risk` do Querido Diário, que *"o coletor
anonimiza por internal/pii antes de gravar"* — frase que a **DEC-038** (nome de agente público
deixa de ser mascarado) tornou falsa no mesmo dia. O campo foi reescrito: o que o coletor remove
hoje é **identificador**, não nome. Auditoria que se apoia em mitigação revogada é auditoria
vencida.

## DEC-038 — Nome de pessoa em ato oficial e em processo público deixa de ser mascarado

**2026-08-29.** Ordem do dono, que é o advogado responsável: *"nome de pessoas públicas, não pode
ter PII, eles são públicos"*; *"todos os processos publicos, podem constar o nome toda da pessoa. O
jus brasil faz isso e o ordenamento juridico garante isso. É principio consticional"*.

A fundamentação completa — com o texto literal de cada dispositivo conferido contra a fonte
oficial, e a lista das exceções taxativas — está em
**`docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md`**, produzido por seis frentes de pesquisa com
verificação adversarial de cada citação (104 levantadas, 35 atacadas, 13 corrigidas, nenhuma
refutada).

**O custo do desenho anterior estava medido:** 88 ocorrências de `[nome removido]` no acervo, em
trechos como *"Exonerar a Sra. [nome removido] de Enfermeira, lotada na Secretaria de Saúde"*. Pior:
`pii.Contem` **reprovava** o texto por conter nome, e o coletor descartava o que acabara de baixar e
anonimizar. O canal parecia morto porque o anonimizador o matava.

**O que continua saindo:** CPF e RG. **CNPJ deixou de sair** — a LGPD protege a pessoa natural
(art. 1º), CNPJ identifica pessoa jurídica com consulta pública na Receita, e a LAI (art. 8º, §1º,
IV) manda publicar contrato: o único CNPJ das amostras estava em *"CONTRATADO(A): F & J
REPRESENTACAO LTDA, inscrito no CNPJ nº 57.080.860/0001-08"*.

**O que a crítica adversarial achou, e que teria passado:** CPF escrito com **barra**
(`132.576.298/93`) e RG com sigla de UF (`RG/SP nº 25.069.617-4`) escapavam do detector **e** do
gate novo — que nasceu com cópia dos padrões, e a cópia saiu mais fraca que o original. Os dois
casos eram reais, estavam no acervo versionado, e o gate passava verde por cima. Corrigido: os
padrões aceitam as duas formas, o gate passou a chamar `pii.IdentificadorExposto` em vez de manter
detector próprio, e `cmd/repii-acervo-diarios` reaplicou o anonimizador ao acervo já coletado. A
correção trouxe um falso positivo junto — "CEP 49.140-000" lido por OCR como "CI-IP 49.140-000",
que virou acusação contra o endereço de uma prefeitura —, desarmado com teste sobre a amostra real.

**Gate:** `publicidade-nome-fonte-oficial` (`internal/publicidadenome`) cobra os dois lados —
identificador exposto **e** nome suprimido —, porque suprimir demais destrói o ato e suprimir de
menos vaza credencial.

## DEC-039 — A armadilha número um do repositório era uma linha de `go.mod` que faltava

**2026-08-29.** `./...` "não expandia" neste repositório, e isso estava gravado no `CLAUDE.md`
como regra absoluta. A causa nunca foi do Go nem do wrapper: `var/nginx/{body,fastcgi,proxy,scgi,uwsgi}`
pertence ao runtime do nginx com modo 0700, e o caminhador do Go abortava o padrão INTEIRO ao
esbarrar neles — `go: pattern all: open /opt/wiki/var/nginx/fastcgi: permission denied`.

### O que essa armadilha custou, medido

| Defeito | Efeito |
|---|---|
| `tools/go-build-check:46` usava `./...` | **`go vet` nunca verificou nada** (BUG-107) |
| `tools/check-all:51` usava `go test ./...` | **zero pacotes testados** (BUG-108) |
| `tools/check-go-compile-closure:134` | cego pela mesma causa (BUG-135) |
| `go mod tidy` | **nunca pôde rodar** — dependência órfã ficava no go.mod sem que ninguém pudesse removê-la |

### A correção, e as duas que foram descartadas

Vale a diretiva **`ignore ./var`** no `go.mod` raiz (Go 1.25+; aqui `go 1.25.12`). Uma linha
**rastreada**, que tira a subárvore do alcance dos padrões sem tocar em nada que esteja no ar.

Duas alternativas foram testadas e descartadas, e o registro importa mais que a escolha:

- **`var/go.mod` sentinela** — foi a primeira tentativa, e funcionava neste disco. É inútil:
  `/var/` está no `.gitignore` (linha 4), e `!/var/go.mod` **não resgata**, porque o git não
  re-inclui arquivo sob diretório excluído. A "correção" viveria numa máquina e morreria no
  próximo checkout — pior que não corrigir, porque a documentação passaria a dizer que funciona.
- **mover `var/nginx` para fora do módulo** — ataca a mesma causa, mas mexe em caminho de
  **produção**, referenciado por `ops/nginx/standalone/nginx.conf`, por unit systemd e por
  `deploy-publico:72`. Cirurgia no que está no ar para resolver o que uma linha resolve.

### A proibição de `./...` PERMANECE, com fundamento novo

Não é mais "não expande, então mente". Agora expande — e por isso virou **comando full-tree
pesado**: 488 pacotes. `AGENTS.md` já o proíbe nessa condição e o hook
`.claude/hooks/block-heavy-go.sh` continua guardando; ele bloqueou, no dia da correção, até a
edição desta própria documentação, por conter o padrão no comando.

O escopo recomendado (`./internal/... ./cmd/...`) cobre exatamente os mesmos 488 pacotes —
medido, não suposto. O que mudou é que um `./...` acidental agora **funciona devagar** em vez de
mentir que não achou nada.

### O que NÃO cai com esta decisão

- O **cache-buster do `go vet`** (BUG-107) é ortogonal: o falso-verde por `VetxOnly` continua
  existindo e a defesa contra ele fica.
- As exclusões de nível **git** (`tools/check-untracked-product-inventory`, `:(exclude)var/nginx`)
  continuam necessárias — o walker do git independe do Go.


## DEC-040 — Emitir alerta ao dono não é "gate que escreve"

**Data:** 2026-08-29 · **Contexto:** BUG-023/075/123 da caça aos bugs.

A separação dos papéis `check-*` (mede) e `generate-*`/`repair-*` (age) fechou os
dois casos que reescreviam o que auditavam, e deixou uma pergunta de fronteira em
aberto: **dez gates escrevem via `tools/notify-owner`** — append em
`data/ops/owner_alerts.jsonl` e `os.replace` de `data/ops/owner_alerts_state.json`.
Pelo critério literal ("altera bytes persistentes do projeto"), os dez violam o
contrato read-only.

**Decisão: não violam. O canal de alerta é isento, e continua como está.**

O que a regra read-only protege é **o dado que o gate audita**. Um gate que mexe
na série que ele mesmo mede destrói a medição seguinte — foi assim que a
cobertura de borda passou a medir o rastro que ela própria acabara de aquecer, e
foi por isso que `check-brotli-e-recomprimir` recomprimia o acervo que dizia
estar conferindo. O `owner_alerts.jsonl` não é auditado por nenhum dos dez: é a
**saída** deles.

E o estado é o que torna o alerta utilizável. Sem `owner_alerts_state.json`, o
mesmo alerta seria reemitido a cada execução — de hora em hora, no caso dos
vigias — e o dono aprenderia a ignorar o canal. Alerta que não chega é pior que
alerta que não existe, porque cria a sensação de cobertura (BUG-149); alerta
repetido em laço produz exatamente o mesmo efeito por outro caminho.

**O que esta decisão NÃO autoriza:** gate que escreve na série que mede; gate que
toca a worktree versionada; gate que dispara `systemctl restart` (a família
`network-health` / `portal-health` / `tunnel-health` continua sendo defeito a
corrigir, e a decisão aqui não a absolve). A isenção alcança **um** destino —
o canal de alerta — e nada mais.

**Consequência para a contagem:** o critério publicado passa a ser "escreve = 
altera bytes persistentes do projeto, **exceto o canal de alerta ao dono**".
Pelo critério novo, os gates que escrevem são **8**, não 18: os 10 do grupo
`notify-owner` saem da conta, e quem aparecer nos dois grupos continua contado
pelo outro motivo.

## DEC-041 — O texto do diário municipal passa a virar corpo de página, como citação identificada e sob filtro duplo

**2026-08-29 (BUG-174).** O coletor de diários municipais baixava, anonimizava e
versionava o texto integral das edições — 172 registros com `texto_anonimo`
não-vazio, os mesmos 172 com `texto_publicavel: true` — e **nada consumia**.
`cmd/generate-diario-pages` não lia o campo (grep: zero ocorrências) e o próprio
cabeçalho do pacote declarava, em versal, *"NÃO PUBLICA — o texto do diário"*.
Banda, disco e processamento de anonimização pagos todo dia para produzir dado
que morria no JSONL, enquanto a página pública era um índice de edições — a
forma que produziu os piores pares de similaridade deste acervo.

### Por que a razão antiga caiu

A regra não era arbitrária: quando foi escrita, **não existia mecanismo capaz de
separar o ato administrativo comum do ato que a lei manda proteger**. Sem ele,
promover texto de diário a corpo de página poria no ar registros como o de
Capela/SE — sentença com adolescente de 15 anos, `"diabetes mellitus tipo 1 -
CID 10: E10"`, mãe nomeada e "Segredo de Justiça" no mesmo arquivo —, que estava
no acervo com `texto_publicavel: true` e gate verde (BUG-177). "Não publica" era
a única trava disponível, e ela funcionou.

O mecanismo passou a existir hoje: `internal/publicidadenome` traz oito classes
de exceção, cada uma com o dispositivo que a cria, e a API
`PodeVirarCorpoDePagina` recusa o registro quando qualquer marcador aparece em
qualquer ponto do texto. Com a trava certa no lugar, a trava improvisada virou o
defeito — e o comentário que a descrevia virou documentação de política
revogada, que é bug pela R1 e a próxima armadilha para quem chegar depois. O
bloco foi reescrito no mesmo diff.

### O que da razão antiga SOBREVIVE, sem uma vírgula de mudança

- **NUNCA página por ato.** Um decreto municipal isolado não sustenta uma URL, e
  publicá-los um a um seria a fábrica de página magra que condenou o v1
  (DEC-004). O trecho entra **dentro** da página UF/dia que já existe.
- **O índice continua sendo o produto.** Quem chega quer saber quais municípios
  circularam diário naquele dia, com edição e link; a citação acrescenta, não
  substitui.
- **Granularidade é risco de LGPD.** Quanto mais fina a página, mais fácil ela
  virar índice de nome de pessoa. Por isso o teto é de três trechos por página,
  e o registro barrado nunca é nomeado no texto — a contagem entra, o município
  não, porque nome mais data seria mapa para o leitor achar o ato protegido.
- **Espelho continua proibido** (DEC-032): o que entra é trecho identificado,
  jamais o inteiro teor.

### A forma, e os números que a sustentam

Regra das duas camadas da DEC-032, em blocos distintos: uma seção com os trechos
citados (município, edição, data, e a URL com o hash na lista de fontes) e outra
com o comentário autoral, derivado de fato medido do dia — contagem por tipo de
ato nos cabeçalhos, defasagem entre assinatura e circulação, valor declarado no
trecho, quantos registros o filtro de exceção barrou. Nunca moldura com número
trocado: a frase agregada substituiu a frase por citação justamente porque a
primeira saída repetiu a mesma oração três vezes numa página.

Medido no lote de 2026-08-29, com `-limite 60`:

| medida | valor |
|---|---|
| páginas com trecho citado | 15 de 38 |
| citações no lote | 17 |
| proporção de texto citado, pior página | 17,3% (teto do gate: 55%) |
| comentário autoral, pior página | 529 palavras (piso do gate: 250) |
| registros com texto | 156 · 28 citáveis · **19 barrados por exceção** · 109 sem trecho legível |
| similaridade 3-grama máxima da família | 0,5679 (corpo inteiro) e 0,6164 (só a prosa própria) |

Três decisões de engenharia que o número obrigou:

1. **O filtro é duplo e incide sobre o texto INTEIRO** (`texto_publicavel` do
   coletor **e** `PodeVirarCorpoDePagina`), nunca sobre o trecho escolhido:
   marcador em qualquer ponto do diário barra o registro todo, porque o trecho
   vizinho identifica por contexto o caso protegido.
2. **O hash se chama pelo que é** — `sha256_texto_anonimo`, o SHA-256 do texto
   anonimizado que este repositório versiona. O registro do coletor não tem
   campo de hash de conteúdo, e preencher um campo chamado "hash da fonte" com
   outra coisa seria declarar verificação de rede que não houve, que é o defeito
   do BUG-049. Este prova o que pode provar: que o trecho publicado saiu do
   texto versionado.
3. **O detector interno de similaridade passou a medir só a prosa própria**,
   retirando os trechos entre aspas curvas antes do shingling. Texto de terceiro
   é único por construção e derrubaria a medida sem que uma linha da máquina
   mudasse — seria comprar unicidade emprestada. No acervo atual o efeito é
   nulo (zero aspas curvas nas 36 páginas anteriores); a proteção é futura.

### Tensão registrada, não resolvida aqui

`internal/v2ingest/adjudicate_shard.go:80` mantém um conjunto FECHADO de chaves
para `official_sources` (`url`, `name`, `anchor_claim`, `verified_at`,
`http_status`). O shard destas páginas já emitia `source_id` e `publication_date`
fora desse conjunto antes desta decisão, e `sha256_texto_anonimo` é a terceira
chave nessa condição. Não é regressão nova — é um contrato que já divergia do
produtor —, e a escolha aqui foi **não mexer no adjudicador**: fechar essa
divergência é decisão de quem governa o pipeline de ingestão, com o inventário
das três chaves na mão.

---

## DEC-040 — Um calendário só para o produto: a janela morta de três horas por dia

**2026-08-30.** O recibo do ingest carrega duas chaves de dia — `validation_as_of`
e `legal_as_of` — e `internal/v2ingest/stock_freshness.go:361-364` exige que as
**duas** batam com o relógio de agora. Até esta decisão, a primeira truncava no
dia **UTC** e a segunda no dia de **São Paulo**. Dois calendários que viram com
três horas de diferença.

### O que isso custava, medido e não presumido

`internal/v2ingest.TestNenhumMinutoDoDiaTemCalendarioDivergente` varre o dia
minuto a minuto: **180 minutos por dia**, das 21:00 às 24:00 BRT, em que os dois
calendários discordam — e portanto **nenhum recibo pode estar válido**. O buraco
tinha duas bocas, e só uma delas tinha guarda:

- **A boca com guarda.** `tools/ingest-v2-stock:13` recusava rodar entre 00Z e
  03Z com a mensagem "recibo natimorto", porque um ingest ali nascia com
  `validation_as_of` do dia UTC seguinte e morria à meia-noite de Brasília, em no
  máximo três horas. A guarda descrevia o defeito corretamente e mandava esperar.
- **A boca sem guarda, que foi a que travou o deploy de 2026-08-29.** Às 21:00
  BRT o dia UTC virava e **todo recibo já existente ficava stale**.
  `./tools/go-modern run ./cmd/check-v2-stock-epoch` às 00:48Z devolvia
  `v2_stock_freshness_validation_as_of_stale: receipt=2026-08-29
  required=2026-08-30` sobre um ingest bem-sucedido de sete horas antes, sem
  ninguém ter tocado no estoque.

Havia ainda um terceiro efeito, sobre o DADO e não sobre o processo:
`cmd/generate-v2-official-source-verify:334` carimbava `verified_at` com
`NormalizeValidationAsOf`, então uma verificação rodada às 22:00 BRT gravava na
proveniência da fonte **a data de amanhã**.

### A decisão

`NormalizeValidationAsOf` passa a truncar no **dia civil brasileiro**, o mesmo de
`NormalizeLegalAsOf`. As duas funções continuam separadas, porque os conceitos
são distintos — uma mede quando a fonte foi conferida, a outra quando a norma
passa a valer, e `TestOsDoisRelogiosContinuamSeparadosMasNoMesmoCalendario` trava
essa independência. O que deixa de existir é o segundo calendário.

**O fundamento não é conveniência de deploy.** Este é um portal jurídico
brasileiro: as fontes oficiais são publicadas em diário brasileiro, a vigência
das normas começa à meia-noite de Brasília, o `verified_at` é lido como data
brasileira e o leitor é brasileiro. Não há neste acervo leitor, norma nem órgão
para quem o dia vire às 21:00. A redação anterior justificava a separação como
"provenance receipts turn on the UTC day" — uma escolha defensável em abstrato,
que na prática só produzia a faixa morta.

### O que veio junto, porque a mudança de fuso o exigia

1. **Data pura passa a ser interpretada no calendário do produto.**
   `"2026-07-11"` não carrega fuso, e `time.Parse` a colocava em UTC; com o
   truncamento brasileiro ela **retrocederia um dia** na normalização
   (2026-07-11T00:00Z é 2026-07-10 às 21:00 em São Paulo). Três pontos passaram a
   `time.ParseInLocation`: `validate.go:886` (`parseOfficialSourceVerifiedAt`),
   `plan.go:1202` (a data do recibo que se compara com o `verified_at`) e
   `adjudicate_shard.go:953` (que devolve o valor para a reprodução da
   adjudicação, onde um dia de diferença faria a reprodução divergir do original
   sem nenhum dado ter mudado). O quarto ponto, `reusable_artifact_semantics.go
   :984`, ficou como estava de propósito: ele só confere formato, e formato é
   invariante ao fuso. Foi `TestOfficialSourceFutureDecisionUsesCallerValidationAsOf`
   que apanhou o defeito antes de qualquer dado ser tocado.
2. **`directValidatorSnapshotAsOf` foi declarada no fuso legal.** Ela vale o DIA
   "2026-07-11"; declarada em UTC, passaria a normalizar para 2026-07-10 e todo
   pino direto mudaria de chave sem que um byte tivesse mudado.
   `TestOInstanteAncoraDoValidadorDiretoNaoMudaDeDia` guarda isso.
3. **A guarda 00-03Z saiu de `tools/ingest-v2-stock`,** com a razão registrada no
   lugar dela. Manter uma trava sem defeito atrás é pior que não ter trava: um
   `exit 2` que ninguém consegue explicar. `WIKI_INGEST_ALLOW_UTC_NIGHT_WINDOW`
   deixou de ter efeito.
4. **Dois testes que travavam o design antigo foram reescritos, não apagados,**
   com a explicação do que mudou e por quê — eram eles que sustentavam a janela.

### Um defeito pré-existente que a mesma passada revelou

Rodar as suítes vizinhas expôs **três testes de `internal/v2sourceresearchreconcile`
já vermelhos no HEAD** (medido em worktree isolada sobre `745720c1`, portanto
anterior a esta mudança): a fixture de "fonte vencida" usava `2026-05-01`, escrita
quando `OfficialSourceVerificationMaxAgeDays` era **30**. A constante subiu para
**90** em 2026-08-04 e a fixture ficou para trás, de modo que o teste passou a
afirmar o contrário do que o código faz. Datada em `2026-03-01` (143 dias antes
do `fixedAsOf`), o pacote volta ao verde. É a mesma família de defeito da
DEC-039: teste que reporta vermelho e que ninguém executava.

## DEC-041 — Consolidar as cinco sondas de bot foi REFUTADO por leitura: são lentes distintas, o defeito era ninguém rodá-las

**Data:** 2026-09-03 · **Contexto:** Fase 5.5 do plano de bots de IA desta sessão.

O plano mandava consolidar `check-what-bots-see`, `check-what-bots-see-externo`,
`check-superficie-bots-live`, `check-perfil-por-bot` e `check-googlebot-smoke`
numa sonda única "com `--alvo origem|borda`", sob a suspeita de duplicação —
suspeita levantada pelos nomes parecidos, não por leitura do código.

**Li as quatro antes de fundir, e a suspeita não se sustenta:**

| ferramenta | linhas | o que mede |
|---|---:|---|
| `check-what-bots-see` | 499 | o que cada perfil de visitante recebe **da origem** |
| `check-what-bots-see-externo` | 199 | **borda × origem**, cabeçalho a cabeçalho |
| `check-perfil-por-bot` | 439 | perfil individual e reproduzível de **cada agente** |
| `check-superficie-bots-live` | 371 | a superfície por **classe** de bot, com ledger |

São quatro lentes sobre o mesmo objeto, não quatro cópias. Fundi-las trocaria
quatro medições por uma, com flags decidindo qual delas se perde — destruição de
capacidade disfarçada de simplificação. `check-googlebot-smoke` tem 9 linhas e é
um invólucro, não uma quinta sonda.

**Decisão: não consolidar. O defeito real era outro, e é o mesmo que a linha 6e
do `run-qualidade-diaria` já tinha apanhado:** das cinco, **só uma estava
agendada**. Sonda que ninguém dispara não mede nada, e o custo de agendar é de
segundos. As três passam a rodar na qualidade diária, com teto de 300 s cada.

**Segurança de UA conferida ANTES de agendar, não depois:** `cabecalhos_para()`
decide pelo **alvo**, nunca pela flag de linha de comando — UA de bot real só
sai contra `127.0.0.1`, que lê `X-Bot-Simulation` e exclui a visita do tráfego
real; contra a borda pública o UA é sempre próprio e declarado. Agendar uma
sonda que mandasse UA de bot real ao domínio público seria a fraude que o
`CLAUDE.md` proíbe, com consequência legal — e agendar multiplica por 365 o que
uma execução manual faria uma vez.

**O que faria a decisão mudar:** medição mostrando que duas dessas sondas
produzem o mesmo veredito sobre o mesmo dado por 30 dias. Aí a duplicação seria
fato, e não semelhança de nome.

## DEC-042 — Escalada de alerta nasce do ledger, com limiar por chave; sem canal externo e sem cadastro

**Data:** 2026-09-03 · **Contexto:** Fase 5.3 do mesmo plano.

`notify-owner` gravava `ocorrencias` desde 2026-09-02 e o próprio comentário
dizia que era "o contador que a escalada usa" — a escalada nunca existiu. Um
alerta crítico repetia na mesma severidade indefinidamente: 1.032 linhas em 24 h,
895 silenciadas por cooldown, e uma crítica aberta há 15,7 h que o consumidor
reportou como OK 24 vezes.

**Decisão: escalar dentro de casa, derivando do ledger que já existe.** Não há
canal externo instalado, e não se cria nenhum — nem MTA, nem SaaS, nem cadastro,
que o contrato proíbe. Escalar aqui significa três coisas concretas: subir a
severidade um degrau, abrir incidente em `data/ops/incidents.jsonl`, e fazer o
consumidor cobrar o incidente. Quem resolve é engenharia; notificação mais alta
não conserta nada sozinha.

**Os limiares são por chave e deliberadamente desiguais** (`ops/alert_policy.json`):
`portal-fora` escala em 2 e abre incidente em 3, porque em 2026-09-01 a superfície
ficou 17 h fora enquanto o watchdog dava 448 restarts fúteis — três ocorrências
já provam que a auto-cura não está curando. `rede-banda` só escala em 8 e abre em
20: oscilação de uplink único por Wi-Fi é condição conhecida do enlace, foram 679
linhas em 24 h, e escalar cedo ali treina o dono a ignorar a fila inteira — que é
como alerta crônico mata alerta real.

**Quatro invariantes fixadas por teste** (`tools/test_notify_owner_escalada.sh`,
8 casos, estado isolado e dublê de `notify-send` no PATH): um degrau por escalada
e não um por ocorrência; `critica` é teto, porque acima dela não há canal e o
próximo passo é o incidente; a escalada rompe o cooldown **uma** vez, já que
silenciar justamente a entrega que anuncia "isto não se resolveu" repetiria o
defeito que o cooldown por severidade corrigiu; e o incidente é gravado uma única
vez por ciclo de vida do alerta, garantido pelo `aberto_desde` — sem isso um
crônico de 2 em 2 minutos escreveria 30 incidentes por hora, e o ledger que
existe para destacar o grave viraria a parede de ruído que a fila já era.

**Política ausente ou ilegível devolve limiares infinitos**, e o comportamento
volta a ser o anterior: o canal que avisa que algo quebrou não pode ser o próximo
a quebrar por causa de um JSON malformado.

**Efeito colateral que a decisão obrigou a consertar:** o reconciliador lia o
`owner_alerts_state.json` (reescrito a cada envio) e o consumidor cobrava o
`owner_alerts.jsonl` (append-only). Medido no dia: 1 chave aberta no estado
contra 7 no ledger, e as duas críticas vencidas — de 27 h e 44 h, com as units já
saindo `Result=success` — estavam só no ledger. Reconciliar contra a fonte mais
fraca deixava a mais forte acumulando dívida para sempre. As duas fontes passam a
ser unidas, com o estado tendo precedência por carregar `ocorrencias` e
`aberto_desde`.

## DEC-043 — Descritor de máquina sobrevive à queda do Go pelo cache de origem, não por uma segunda cópia em disco

**Data:** 2026-09-03 · **Contexto:** item D da Fase 1 do plano de bots de IA.

O plano pedia **duas** proteções para o mesmo risco — descritor de máquina
morrer junto com o processo Go, como aconteceu nas 17 h de 2026-09-01:

- **C:** `proxy_cache` no nginx com `proxy_cache_use_stale`, servindo a última
  resposta boa quando o upstream cai;
- **D:** `cmd/build` gravando `/.well-known/*`, `openapi.json`, `api.md`,
  `auth.md` e `politica-de-uso.json` em `public/`, para o `try_files` achar o
  arquivo antes de chegar ao Go.

**Decisão: C entra, D não.** Medido em 2026-09-03, com a posição do
`access.log` marcada antes das sondas e o delta lido depois:

```
GET /.well-known/agent-card.json   ocs=HIT
GET /openapi.json                  ocs=HIT
GET /auth.md                       ocs=HIT
GET /familia/index.md              ocs=HIT
```

10.265 objetos no cache de origem, e `proxy_cache_use_stale error timeout
updating http_500 http_502 http_503 http_504` cobrindo `@markdown` e
`@fallback`. O risco que D existia para cobrir já está coberto.

**Por que não fazer os dois assim mesmo:** D criaria uma **segunda cópia** de
cada descritor, gravada num momento diferente do que o Go serve, livre para
divergir da primeira sem que nada acuse. É a mesma objeção que descartou o
despejo do acervo no `llms-full.txt` — e ali ela custou a promessa falsa de um
arquivo que anunciava texto e servia links. Um descritor de contrato que
diverge é pior que um descritor ausente, porque o agente confia no que lê.

Há uma diferença real entre as duas rotas, e ela não muda a conclusão: com D,
o descritor sobreviveria a uma queda **e** a um cache frio; com C, só à queda.
Cache frio acontece depois de purga ampla — e o `tools/warm-origin-cache`
reaquece as 10.255 rotas em 128 s dentro do próprio deploy, com `inactive=30d`
no `proxy_cache_path`. A janela existe e é de minutos, contra uma divergência
silenciosa que duraria até alguém notar.

**O que faria a decisão mudar:** medição mostrando descritor servido 5xx por
cache frio depois de um deploy — aí a janela deixaria de ser teórica, e D
entraria com o gate de paridade (`check-paridade-go-nginx`) cobrando byte a byte
que as duas cópias são a mesma.

## DEC-044 — A rede social roda em processo Go próprio na 8091; a DEC-022 é estendida, não contrariada

**Data:** 2026-09-04 · **Contexto:** aprovação do `docs/goal/PLANO_REDE_SOCIAL.md`, ordem do
dono para erguer `wikijuridica.com.br/redesocial` sobre o acervo.

A DEC-022 fixou `cloudflared → nginx 127.0.0.1:8088 → Go 127.0.0.1:8089`. A rede social
**não entra no `cmd/server`**: nasce como `cmd/social` em **127.0.0.1:8091**, mesmo módulo
`portaljuridico`, mesmo `internal/` compartilhado, unit e socket próprios.

**A razão é isolamento de falha, não elegância.** O acervo estático sai do disco e não
depende do Go, mas o **canal de máquina** — `/mcp`, `/a2a/v1`, as gêmeas Markdown,
`/api/v1/*` e os descritores — passa pelo `cmd/server`, e é ele o diferencial do projeto. Um
*panic* numa escrita de post, um vazamento de goroutine ou uma carga de upload no mesmo
processo derrubaria o canal que os bots de IA consomem. Com dois processos, `/redesocial/`
pode cair sozinho num incidente sem tirar o portal do ar, e o deploy da rede social não
republica 10.141 páginas nem re-data o acervo.

**Por que 8091 e não 8090:** `tools/generate-nginx-standalone --porta 8091` documenta 8091
como porta de **ensaio do cutover**, e `ops/nginx/standalone/server.conf` (morto) declara
8090. Ambas estão livres hoje; 8090 colidiria com o próximo ensaio de cutover, que é
justamente o procedimento que não pode falhar. A escolha de 8091 assume o custo de coordenar
com o ensaio, que é agendado, contra o de colidir com ele, que não é.

**O que muda no ingress, e nenhuma das quatro é opcional** (medido em
`ops/nginx/standalone/nginx.conf`, o arquivo **vivo** — `wikijuridica.conf` traz banner
"NAO-CARREGADO-EM-PRODUCAO" e rodar o gerador **regride** o que está no ar):

1. `location ^~ /api/v1/redesocial/` **antes** do catch-all. Não existe `location /api`
   nenhuma hoje: sem ela, toda escrita cairia em `@fallback` → `:8089` → 404, **e a resposta
   entraria na zona de cache do acervo**.
2. Escrita sob `/api/v1/*` porque a regra 2 do WAF da Cloudflare bloqueia todo método fora de
   GET/HEAD/OPTIONS exceto `/mcp`, `starts_with /a2a` e `starts_with /api` — e essa mesma
   regra já quebrou `/a2a/v1` em silêncio quando aquele endpoint nasceu sem a exceção.
3. `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`, copiando o padrão que
   `location = /sitemaps/` já usa. O `real_ip_header CF-Connecting-IP` do `server{}`
   (`:934-936`) já dá o IP verdadeiro ao nginx; o que falta é repassá-lo ao Go.
4. `location ^~ /redesocial/assets/` própria, porque a allowlist de extensões do nginx
   devolve **404 puro** para `.css` e `.js` — e o Dynamic Redirect da Cloudflare ainda
   acrescenta barra final a esses dois, matando-os uma segunda vez.

**Cache de borda condicionado à sessão, não desligado:** zona `wj_social` própria (nunca a
`wj_dyn` do acervo), com `proxy_cache_bypass`/`proxy_no_cache` em `$cookie_wjsession`.
Desligar o cache serviria mal os bots de alto valor, que são o canal de resultado do projeto.
O cookie **tem de se chamar `wjsession`**: `$cookie_<nome>` do nginx só aceita
`[A-Za-z0-9_]`, então um prefixo `__Host-` exigiria `map $http_cookie` com regex no caminho
exato que impede vazamento de sessão pelo cache.

## DEC-045 — O `codex2-policy-enforcement` está com 273 falhas por causa única, e a correção é derivar o registro do go.mod

**Data:** 2026-09-04 · **Contexto:** passo 0 do `PLANO_REDE_SOCIAL.md`, que propõe usar este
gate como trava estrutural do DataJud.

**Medição própria** (`./tools/go-modern run ./cmd/check codex2-policy-enforcement
--max-errors 0`, exit 1): **273 falhas**, das quais **163 (60%)** são
`external_dependency_unapproved` (84) e `runtime_candidate_module_unapproved` (79). As outras
110 são escapes de escopo de import distribuídos por 16 módulos, mais 7 evidências inválidas.

**Causa raiz, única para as 163:** `adoptedDependencyRecord` (`policy.go:1288+`) mantém o
registro de dependências **hardcoded em Go**, com `AdoptedModuleVersion` literal, enquanto o
`go.mod` tem **201 requires diretos** que evoluíram desde então. Cada `go get` que subiu uma
versão criou uma falha. `golang.org/x/net@v0.58.0` reprova mesmo tendo `xNetHTMLImportAllowed`
— o módulo tem registro; a **versão** não bate. Duplicar à mão um dado que já existe no
`go.mod` é a definição de fonte-de-verdade dupla, e ela divergiu exatamente como se espera.

**Decisão:**

1. **Registrar o baseline de 273 com esta data**, para que regressão nova seja distinguível
   da dívida herdada. Isso não é tolerar o vermelho: é poder enxergar dentro dele.
2. **Corrigir a causa, não os 273 sintomas:** a versão adotada passa a ser **derivada do
   `go.mod`**, e o registro guarda o que o `go.mod` não sabe — licença, ADR, escopo de
   import, evidência de benchmark. Um módulo que suba de versão deixa de reprovar por isso;
   um módulo **novo** e não registrado continua reprovando, que é a propriedade que o gate
   existe para dar.
3. **Nada é afrouxado.** Escopo de import, licença e ADR continuam obrigatórios, e as 110
   falhas de escopo permanecem vermelhas até serem tratadas uma a uma, com leitura.

### DEC-045.1 — As allowlists de import: dois regimes de SQLite e a trava estrutural do DataJud

**Data:** 2026-09-04 · Complementa a DEC-045 e fecha o item 3 do passo 0 do
`PLANO_REDE_SOCIAL.md`, que a DEC-045 não cobria — ela trata das 273 falhas e da
fonte-de-verdade dupla, não do escopo de import.

**1. `modernc.org/sqlite` passa a servir DOIS regimes, e a distinção é o ponto.**
`moderncSQLiteImportAllowed` autorizava três pacotes, todos **sidecar derivado**: o JSONL é
canônico, o índice reconstrói, e perder o arquivo custa uma regeneração. O
`DecisionReason` dizia exatamente isso — *"JSONL remains canonical, sidecars rebuild
atomically"*.

A rede social é o regime oposto. Conta, perfil, postagem, denúncia, decisão de moderação e
trilha **nascem no SQLite e não existem em nenhum outro lugar**. Perder o arquivo é perder o
dado do usuário. Manter a frase antiga faria o registro **mentir sobre o regime do dado**,
que é precisamente o que este pacote existe para impedir.

Consequências que decorrem do regime canônico, não de preferência: backup próprio com
`VACUUM INTO` (copiar `.db` + `-wal` + `-shm` em três instantes produz arquivo que **abre e
mente**), e localização fora de `var/on-demand-cache`, que o `deploy-publico` apaga com
`rm -rf` no passo 4.

Autorizados: `internal/moderacao`, `internal/contas`, `internal/socialdb`, `internal/lgpd`,
`internal/sigilo`, `internal/socialconteudo`, `cmd/social`. **Nenhum pacote do caminho de
publicação aparece na lista** — dado de usuário não vira página, e não por disciplina: por
não compilar.

**2. `datajudImportAllowed` nasce como trava estrutural.** Diferente das outras, ela olha um
pacote **interno**, então compara por prefixo do caminho de import e não por
`moduleImportMatches`.

A garantia: dado do DataJud não alcança artefato público. As duas razões são independentes e
qualquer uma basta — o termo de uso do CNJ restringe uso comercial e redistribuição
(cláusulas 3.3/3.8), e o lag **medido em 42 dias** torna o dado imprestável para prazo.

Medição ao ligar a trava contra a árvore real: **8 escapes**, todos ferramentas da própria
frente DataJud (`cmd/*-datajud-*`, `internal/codex2datajudfrontiersignalreport`) — e
**nenhum no caminho de publicação**, o que confirma que a propriedade já valia de fato antes
de existir quem a cobrasse. A allowlist foi completada com esses consumidores; o total do
gate voltou a 273, sem regressão.

`datajud_trava_estrutural_test.go` prova a propriedade pelos **dois lados**, porque só um
deles passaria por acaso: nenhum dos 12 pacotes do caminho de publicação importa o DataJud
(varredura de AST sobre a árvore), **e** a função de allowlist recusa cada um deles. Um
terceiro teste prova que a trava não ficou impossível de satisfazer.

**Por que isso é bloqueio real e não burocracia:** o plano propõe `datajudImportAllowed`
como trava que impede dado do DataJud alcançar artefato público — não por política, mas
porque nenhum pacote do caminho de publicação compilaria contra ele. **Um gate com 273
falhas não trava nada**: ninguém lê um vermelho permanente, e foi exatamente assim que as
273 se acumularam sem ninguém notar. A trava só passa a valer quando o gate volta a ser
legível, e por isso a frente é pré-requisito de F4, não de F0.

## DEC-046 — O Resend entra como exceção nominal datada, e o produto não depende dele

**Data:** 2026-09-05 · **Contexto:** ordem do dono autorizando nominalmente o Resend, sem que
existisse DEC no disco. O contrato proíbe serviço proprietário e API externa, e sem este
registro o `codex2-policy-enforcement` reprovaria o primeiro import como
`external_dependency_unapproved` — a mesma classe que responde por 84 das 273 falhas medidas
na DEC-045.

**As rotas próprias foram esgotadas primeiro, e é a medição que fecha a porta.** Medido em
2026-09-05, do IP de saída `187.125.5.167`: `/dev/tcp/gmail-smtp-in.l.google.com/25`
**bloqueada** e `/dev/tcp/mx.uol.com.br/25` — destino fora do Google, escolhido justamente
para separar "o Google nos recusa" de "a porta não sai daqui" — **também bloqueada**. As duas
morrem por **timeout**, não por conexão recusada: pacote descartado em silêncio é a assinatura
de bloqueio no provedor, e uma recusa seria instantânea. O controle positivo
`/dev/tcp/smtp.gmail.com/587` **abre**, o que prova que a saída TCP existe e que o que falta é
especificamente a 25.

A cadeia de reputação está quebrada antes disso. O PTR de `187.125.5.167` é
`1871255167.telemar.net.br`, e esse nome **não tem registro A** — o FCrDNS quebra no primeiro
passo, e nenhum receptor sério aceita MTA assim. O domínio, por sua vez, declara hoje
`v=spf1 -all`, `_dmarc` com `p=reject` e MX `0 .` (null MX da RFC 7505): a zona afirma, de
três formas independentes, que este domínio **não envia e não recebe** e-mail. Servidor
próprio não é pendência de configuração adiada; é rota fechada pela característica do link.

**Armadilha a registrar antes que alguém tente o caminho óbvio:** o pacote `postfix` está em
estado `rc` — removido com os conffiles preservados — e `/etc/postfix/main.cf` sobreviveu
configurado para **outro domínio**, `myhostname = mail.divorcioem1dia.com` e
`mydomain = divorcioem1dia.com`, com `relayhost = [smtp.gmail.com]:587` e
`smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd`. Esse é o projeto vizinho
arquivado, que o contrato proíbe usar como fonte, e um `apt install postfix` herdaria a
configuração dele **em silêncio**, passando a assinar correio nosso com identidade alheia.
Qualquer instalação futura exige `apt purge` antes — é a mesma classe de acidente do certbot
do vizinho, que parava o nginx inteiro ~2×/dia e servia 502 ao Googlebot
(`docs/PRECEDENTES_DAS_ORDENS.md:80`).

**Os três limites que mantêm o Resend fora do caminho crítico**, e sem os quais a exceção não
vale:

**(1) O produto funciona sem ele.** O desenho manda que todo e-mail vire linha em `email_saida`
na mesma transação que cria a conta, para que transporte indisponível faça a fila crescer sem
derrubar cadastro nenhum — e `internal/contas` já foi escrito assim de propósito, produzindo o
segredo em claro e devolvendo-o ao chamador em vez de enviar (`contas.go:24`), justamente para
que um MTA fora do ar não derrube o login. **Mas o estado real de hoje é pior do que isso, e
nenhuma exceção de política o conserta:** `email_saida` existe como **uma linha de comentário**
e `internal/socialmail` **não existe**, de modo que a conta nasce `nao_confirmada` e **não há
caminho para `ativa`** — `Entrar` barra em `entrada.go:302` com `ErrContaNaoConfirmada`. O
Resend destrava a última milha de um elo que ainda precisa ser construído; ele não é o elo, e
esta DEC não deve ser lida como se fosse.

**(2) Só trafegam destinatário e um identificador de template de conjunto fechado**, e a
garantia tem de ser ausência de superfície, não disciplina: o pacote nasce **sem** função que
aceite corpo livre, com `CHECK` de conjunto fechado na coluna de template — mala direta
impossível de **gravar**, do mesmo jeito que a trava do DataJud da DEC-045.1 vale por não
compilar. **(3) A chave mora em `.env.local`**, nunca no repositório e nunca em prompt de
agente. *(Retificado em 2026-09-09, commit fcb2b01d: a KEK mora em `.env.social`, arquivo
próprio da unit do social; `.env.local` é compartilhado com o `cmd/server` e não a leva —
o isolamento é de processo, medido no `/proc/<pid>/environ`.)*

Um efeito colateral que é ganho: autorizar o Resend no SPF torna o `-all` uma afirmação
**verdadeira** em vez de contraditória. Hoje a zona nega todo remetente enquanto o produto
pretende enviar; depois ela passa a nomear exatamente um.

**O que esta decisão NÃO faz:** `F1-smtp` e `F1-fechamento` continuam `pendente`
(`docs/goal/TASKLIST_REDE_SOCIAL.md:102` e `:94`). A prova de `F1-fechamento` exige e-mail
efetivamente chegando ao Gmail, e reescrevê-la para passar com o que existe hoje seria
relaxar o gate para caber no resultado — o que este contrato chama de
fraude operacional. A exceção autoriza o import; ela não declara a frente concluída.

## DEC-047 — Acesso total dos bots à rede social, e a causa do abandono é tratada ANTES da abertura

**Data:** 2026-09-05 · **Contexto:** ordem do dono de dar acesso total dos bots à rede social,
inclusive os de treinamento, com limites generosos para os famosos.

**O raciocínio de produto é do dono e não se discute pela engenharia:** o acervo existe para
ser **citado**, quem cita é o modelo, e o modelo aprende com o que rastreia. Manter bot de
treinamento em tier apertado é otimizar banda contra o único canal de distribuição que não se
compra. GPTBot e ClaudeBot passam a `$wj_bot_allow`.

**O sequenciamento, esse é decisão de engenharia, e a medição o inverteu.** O comentário de
`ops/nginx/standalone/nginx.conf:1662-1663` afirma que a herança de `limit_req` na location da
rede social preserva a regra que dá "pista livre ao Googlebot, ao GPTBot e ao ClaudeBot". O
mapa `$wj_bot_allow` (`:396-445`) **não contém nenhum dos dois**: GPTBot e ClaudeBot estão em
`$wj_tier_training_std_marca` (`:853-862`), tier de 600 r/m. É comentário que mente, e a
entrega é fazer o código dizer a verdade que o comentário já afirmava.

**Antes disso, porém, a R6.** `data/ops/bot_return_state.json` acusa queda de 100% para
claudebot e gptbot e de 99,2% para googlebot. Fui verificar se o alarme era artefato de
medição — **e não é**. A checagem confirmou o alarme e derrubou a minha própria suspeita, que
é o que a R2 manda registrar quando o detector resiste à leitura.

O que a checagem achou foi uma armadilha de leitura, não um defeito da série.
`edge_bot_agents_daily.jsonl` é **append-only com restatements**, e **somá-lo é a leitura
errada**: `serie_saneada` (`tools/edgetelemetry.py:270`) deduplica por `(date, agent_key)`
mantendo a **última** linha e descarta a fisicamente impossível. Um consumidor que somasse
leria, para o googlebot, "pico" de **105.001.038 requisições em um dia**; lido pelo redutor
canônico, o pico é **4.297** — exatamente o que `bot_return_state` registra. As 10 linhas
descartadas caem por teto explícito: fator de extrapolação de até 1.000.000× contra o teto de
100×, e volume acima do teto físico de **381.080 requisições/dia** (19.054 URLs públicas × 20
requisições por URL). A lição é operacional e vale para toda série da borda: **usar
`serie_saneada`, nunca reimplementar a leitura** — foi reimplementá-la que produziu o número
falso, e o repositório já tinha a guarda certa.

Com a série lida corretamente, o alarme **se sustenta nos três**: o googlebot roda hoje entre
36 e 50 requisições/dia contra pico de 4.297; o gptbot, em unidades contra pico de 16.456; e
o claudebot **zerou** — 08-25 = 23, 08-26 = 25, 08-27 = 34, 08-28 = 3, 08-29 = 0, sem nenhuma
visita desde então.

**E a causa NÃO está medida, o que é diferente de não existir.** A hipótese natural era o
incidente do `wikijuridica-server.socket`, que o `.service` declara em `Requires=`: o journal
registra **493 ocorrências** de `Unit wikijuridica-server.socket not found` entre 2026-09-01
18:37:05 e 2026-09-02 10:44:51, e **nenhuma antes disso em todo o journal**. As datas refutam
a hipótese — o ClaudeBot já tinha zerado em 29/08, **três dias antes** de o incidente começar.
E `edge_bot_status_daily.jsonl` a refuta de novo, por outro lado: no colapso o ClaudeBot
recebeu **só HTTP 200** — 22, 23, 25, 34 e 3 requisições de 24 a 28/08, sem um único 5xx. Ele
não foi embora tomando erro; foi embora sendo bem servido.

Ficam então duas coisas separadas, e fundi-las seria inventar causa. A queda do ClaudeBot é
**defeito de engenharia até prova medida em contrário** (R6) e segue **sem causa medida**:
é trabalho de medição em aberto, não mistério a arquivar. O incidente do socket é defeito real
e independente, que teria recebido com a página de erro estática (hoje 6.598 bytes) qualquer
bot que voltasse nas dezesseis horas em que durou, sem `use_stale` porque não havia objeto
quente. Ele se corrige **antes** de abrir a pista não porque explique a saída, mas porque
garantiria a próxima.

**Duas travas que a decisão carrega, e nenhuma é opcional.** A primeira é aritmética do
próprio nginx: os tiers são chaves compostas, `map "$wj_bot_allow:$wj_tier_training_std_marca"`
com `default ""` e `"0:1" $binary_remote_addr`. Entrar em `$wj_bot_allow` muda a chave de
`0:1` para `1:1`, que cai no `default ""` — e **chave vazia desliga o `limit_req` inteiro**,
de uma vez, para a estática **e** para a dinâmica. Isso inclui `/buscar/`, que monta índice
por requisição, e o `/api/v1/lote` de 604 KB. Ou o teto agregado por operador vem na mesma
mudança, ou a abertura espera por ele. A segunda é que a pista sem limite **já é forjada**:
das 194 requisições com `bot_allow=1` declarando `ChatGPT-User` nos logs de acesso, **9
vieram de 8 IPs distintos que não caem em nenhuma faixa oficial publicada pela OpenAI** — e a
contagem não muda se a comparação for feita contra a união de todas as faixas dos operadores
da OpenAI em vez de só as do `chatgpt-user`, o que descarta erro de escolha de lista. Casar
bot por string de User-Agent é casar por um campo que o cliente escolhe; verificação por faixa
de IP deixa de ser refinamento e vira pré-requisito da abertura.

**O afrouxamento vale só para GPTBot e ClaudeBot.** Os cinco de `$wj_tier_training_strict_marca`
(`:871-878`) — Bytespider, CCBot, ImagesiftBot, Applebot-Extended e webzio-extended — ficam
onde estão. A ordem do dono nomeou dois; estender a terceiros por analogia seria decidir no
lugar dele, e nenhuma medição nossa hoje os justifica.

## DEC-048 — `/redesocial/` não carrega analytics de cliente, e isso não é desativar a medição

**Data:** 2026-09-05 · **Contexto:** duas regras do mesmo contrato apontando para lados opostos
sobre a mesma superfície, descobertas ao revisar a CSP da rede social.

O `CLAUDE.md` §6 diz que "analytics é PERMITIDO (decisão do dono, 2026-08-27) e desativar a
medição é proibido". A CSP da rede social é `script-src 'none'` nas **duas** variantes —
`ContentSecurityPolicyPublica` e `ContentSecurityPolicyPrivada`, em
`internal/socialheaders/socialheaders.go:96` e `:118` —, logo zero GA4 e zero Clarity em
`/redesocial/`. E `cmd/social/render.go` confirma que não é descuido: o modelo da página não
tem `<script>` nenhum.

**Decisão: `script-src 'none'` fica, e a medição da rede social é 100% de servidor.** Três
razões medidas, e a primeira é a que resolve a aparência de contradição.

**A ordem de 2026-08-27 foi sobre o acervo, e a topologia lá é a oposta desta.** As 10.141
páginas saem estáticas de `public/` com `s-maxage=604800`; a borda serve a maioria e o log de
origem **não a vê**. Sem GA4 e Clarity ali não haveria medição de humano nenhuma — foi
exatamente esse buraco que a decisão do dono veio tapar. Na rede social **toda** requisição
atravessa o Go, porque não existe `public/` para ela, e o `proxy_cache_bypass $cookie_wjsession`
(`nginx.conf:1686`) garante que a sessão autenticada chegue sempre à origem. O instrumento de
servidor vê aqui o que o de cliente veria — e mais: o loader de
`internal/webanalytics` só carrega o tag em `requestIdleCallback(...,{timeout:1200})`, com
recuo de 2 s, aborta em opt-out e sob Global Privacy Control, e retorna cedo para todo UA que
case o filtro de bot. Trocar um instrumento que vê tudo por um que vê parte não é medir mais.

**A rede social publica texto de terceiro.** `script-src 'none'` é a defesa que segura o
payload **quando a sanitização falhar** — e a sanitização é código nosso, logo código que pode
ter defeito. É a mesma lógica do escape contextual que `cmd/social/render.go` já documenta:
não confiar na revisão prévia num canal onde não há revisão prévia.

**Um `<script>` a mais reprova a cadeia inteira do acervo.**
`internal/htmlcontract/htmlcontract.go:240` isenta `internal/pageinline.Script` por
**igualdade byte a byte e com zero atributos**, e a CSP das dez mil páginas deriva o hash
**dessa** constante — daí a conta que o `CLAUDE.md` §6 já registra, de que um segundo script
reprova em oito gates. Não há como a rede social ganhar um script sem reabrir aquela cadeia.

**As três obrigações sem as quais isto vira desculpa**, e é por elas que a decisão se deixa
cobrar: a série de humano real da rede social sai do log de origem, com método escrito e piso
declarado; ela nasce **junto** com a primeira rota pública nova, nunca depois — medição que
chega meses após a superfície é medição que nunca chega; e um gate prova que
`pageinline.Script` não aparece em nenhuma resposta de `/redesocial/`, para que a isenção do
acervo não vaze para cá por conveniência.

## DEC-049 — A maquinaria de autoria do acervo é mono-autor por construção, e a ponte editorial depende disso

**Data:** 2026-09-05 · **Contexto:** ao desenhar como conteúdo nascido na rede social poderia
alimentar o acervo, a pergunta era de que autoria ele sairia.

`authorMatchesConfiguredIdentity` (`internal/structureddata/structured_data.go:1170`) autentica
o autor visível da página contra a identidade editorial de `content/site.json` por **igualdade
exata, nunca prefixo ou substring**. Ela aceita duas formas — o nome puro e o nome com a
credencial acoplada, `"<nome> OAB/<seção> <número>"` —, mas as duas são materializações da
**mesma** identidade única, reconstruídas de `site.json` e nunca de literal. Não há segundo
autor: qualquer conteúdo de terceiro que virasse página do acervo sairia com autoria errada
ou, mais provavelmente, mudo — sem `@id` de autor, que é justamente o sinal E-E-A-T que a
função existe para consolidar.

**A consequência para a rede social é uma fronteira, não uma limitação a contornar:** conteúdo
nascido de thread **não** vira página do acervo sob a autoria do publisher. Atribuir a Rafael
Toledo texto que ele não escreveu seria falso na origem, e a maquinaria felizmente não oferece
o atalho.

Daí decorrem os dois campos que a superfície social precisa emitir e hoje não emite. A gêmea
Markdown social sai com `CC-BY-4.0` — a mesma `pagemarkdown.LicenseSPDX` do acervo — **somente**
quando o autor casa com a identidade de `site.json`, e `CC-BY-NC-ND-4.0` em todo o resto.
Nunca omissa: hoje `renderizaMarkdown` (`cmd/social/render.go:87`) **não emite front matter
nenhum**, começando direto no `#` do cabeçalho, de modo que a gêmea social sai sem campo
`license` algum. Não é licença errada, é licença **ausente** — e ausente é mais grave, porque
licença errada um leitor contesta e licença ausente ele resolve sozinho, presumindo o que lhe
convier. O mesmo discriminador de autoria decide o tipo do JSON-LD: `Article` para conteúdo do
publisher, `QAPage` ou `DiscussionForumPosting` para conteúdo de terceiro.

## DEC-050 — Conferência de prazo é ferramenta para advogado; para o leigo seria consultoria jurídica

**Data:** 2026-09-05 · **Contexto:** `internal/prazo` está pronto e sem consumidor, e a
tentação era expor ao leigo a pergunta óbvia — "recebi a intimação em tal dia, até quando
ajo?".

**A medição do próprio pacote derruba a ideia por duas vias, e as duas bastam sozinhas.**

**Técnica:** `prazo.Entrada` (`internal/prazo/prazo.go:14`) pede `CodigoClasse`, `NomeClasse`,
`TipoDocumento` e `TipoComunicacao`, campos que chegam por
`EntradaDoDJEN(djen.Comunicacao)` — isto é, do **diário eletrônico**. E `presuncao.go` modela
atos publicados em diário, com sentença e acórdão abrindo embargos de declaração em 5 dias
pelo CPC art. 1.023, contados no calendário forense de `internal/prazo/calendario.go`. O leigo
intimado pessoalmente não possui nenhum desses campos, e o termo inicial dele é outro (CPC
art. 231). Alimentar o cálculo com o que o leigo sabe informar produziria número com aparência
de resposta e sem lastro no ato — e o pacote é explícito sobre a assimetria do erro
(`estado.go`: "NA DUVIDA, O DIA CONTA COMO UTIL"), porque um dia a mais empurra a data para
depois da real e produz perda de prazo.

**Jurídica, e esta decide antes da técnica:** dizer a uma pessoa determinada até quando ela
deve agir no processo dela é **consultoria jurídica**, atividade privativa da advocacia pelo
art. 1º, II da Lei 8.906/94. Uma plataforma que a automatiza pratica, sem advogado no
circuito, o que a lei reserva — e o risco não é de SEO, é disciplinar. Ainda que a conta
estivesse certa, não caberia oferecê-la assim.

**A entrega não é suspensa, e isto é o oposto de engavetar:** o código está pronto e o valor é
real. `internal/prazo` vira **conferência de prazo para o advogado verificado** — ferramenta
profissional para profissional, onde os campos do DJEN existem de fato e onde há advogado
respondendo pelo resultado. Ao leigo fica o que é lícito e continua útil: dizer que **existe**
prazo, que ele corre, e que ele precisa de advogado. Informação, não cálculo.

## DEC-051 — O IP do `registros_acesso` vai cifrado e reversível, e o expurgo de 6 meses passa a ter quem o execute

**Data:** 2026-09-05 · **Contexto:** `internal/lgpd/registrosacesso.go` já guardava o endereço
cifrado com `ip_hash` ao lado, e `lgpd.Varrer` já apagava o vencido — mas **nenhum processo
chamava `Varrer` fora dos testes**, e a retenção existia só no aviso ao titular.

**Por que o IP é cifrado e NÃO hasheado, e a distinção é jurídica antes de ser técnica.** O
art. 5º, VIII da Lei 12.965/2014 define registro de acesso a aplicação como o conjunto de
informações de data e hora de uso "a partir de um determinado endereço IP": a obrigação de
guarda do art. 15 é sobre o **endereço**. Hash não é endereço. Guardar apenas o digest
atenderia à correlação interna e **descumpriria a guarda**, porque, diante de requisição
judicial, a plataforma não teria o que apresentar — cumpriria a aparência da lei e faltaria com
a obrigação dela. Cifra reversível (AES-256-GCM, nonce por registro) preserva o dever legal sem
deixar o endereço em claro no arquivo; `lgpd.DecifraRegistro` é a operação que o atende.

`ip_hash` fica em **coluna adicional**, e é HMAC-SHA256 com chave própria, nunca SHA puro: o
espaço IPv4 tem 2³² endereços e um digest sem chave é enumerável em segundos — seria
pseudonimização no nome e texto claro no efeito. Ele serve às correlações que não precisam
decifrar (mesmo visitante em rotas diferentes, contagem por origem), e essas são a maioria.

**O prazo é fato da linha, não regra do varredor.** `expira_em` é calculado no momento do
registro, a partir da tabela de finalidades. Mudar a política de retenção amanhã não reescreve
retroativamente o prazo do que já foi coletado — e é isso que separa retenção declarada de
retenção conveniente.

**O que esta decisão acrescenta:** `cmd/lgpd-expurgo`, `tools/run-lgpd-expurgo` e o par
`wikijuridica-lgpd-expurgo.service`/`.timer` (04:10, `Persistent=true`, `OnFailure=`). O
comando **recusa diretório sem banco** em vez de criar um vazio e relatar sucesso: era esse o
falso verde disponível — varrer um arquivo que ninguém escreve e anunciar zero apagados. O
prazo do art. 15 só vira comportamento quando existe um processo que apaga, e um processo que
apaga precisa de cadência própria: prendê-lo ao boot do servidor faria a frequência do expurgo
depender de quantas vezes o `Restart=always` reiniciou o serviço.

## DEC-052 — O selo de advogado sai de JOIN com a decisão vigente, e nunca de coluna booleana

**Data:** 2026-09-05 · **Contexto:** `perfis_advogado` (`internal/socialdb/esquema.go`) já
declarava por escrito que o selo sairia de JOIN, e não havia decisão com que fazer o JOIN.

**A inversão que esta decisão impede.** Uma coluna `verificado` no perfil é mais barata e está
errada, porque **coluna booleana não expira**. Inscrição suspensa em processo disciplinar,
cancelada a pedido ou licenciada pelo art. 28 do EOAB deixa de habilitar o exercício da
advocacia; um selo que sobrevivesse a isso seria a plataforma **afirmando publicamente que uma
pessoa está habilitada quando ela não está**. Não é defeito de interface: é afirmação falsa
sobre habilitação profissional, feita por quem publica.

`internal/verificacaooab` grava a decisão com `vigente_ate`, e `Selo` é uma consulta com o
relógio dentro. Revogar não apaga nada: empurra `vigente_ate` para o instante da revogação, e o
selo cai na mesma consulta que o concedia. A linha de `perfis_advogado` **fica** — ela é a
reivindicação da inscrição, e apagá-la liberaria o par `(oab_numero, seccional)` para outra
conta no minuto seguinte a uma revogação por fraude, que é justamente quando a trava precisa
valer. A vigência tem prazo de um ano por razão operacional medida: a OAB não nos notifica
suspensão, então selo sem prazo é a coluna booleana com outro nome.

**O par é a chave, e nunca só o número:** o mesmo número de inscrição existe em seccionais
diferentes e pertence a pessoas diferentes. Unicidade só pelo número recusaria advogado
legítimo.

## DEC-053 — Jurista é autoridade de conteúdo e não recebe caso, por trava de código

**Data:** 2026-09-05 · **Contexto:** os quatro papéis da rede social (visitante, leigo,
advogado verificado, jurista) precisavam de um lugar onde o impedimento funcional fosse
executável.

Juiz, membro do Ministério Público e delegado participam escrevendo e esclarecendo. Receber
consulta seria exercício de advocacia **incompatível** com a função — Lei 8.906/94 art. 28, I e
II, e LC 35/1979 (LOMAN) art. 36, I —, e a incompatibilidade é total, alcançando inclusive a
causa própria. Se a plataforma encaminhasse a consulta de um leigo a um juiz cadastrado, o juiz
estaria exercendo advocacia vedada **e a plataforma teria construído o caminho**.

Por isso a regra vive em `socialpapeis.DestinatarioDeCaso`, que devolve **erro** e não booleano:
`if !PodeReceberCaso(p) {}` sem corpo compila e passa em revisão; erro descartado, não. Uma
regra que morasse no template sumiria no dia em que outra rota passasse a encaminhar caso.
`socialpapeis.Deriva` também falha fechado no estado impossível — conta de jurista **com**
inscrição vigente —, porque quem assume a magistratura precisa pedir o licenciamento e, até
pedir, a inscrição segue ativa na consulta pública: escolher um dos dois em silêncio daria caso
a quem não pode receber.

## DEC-054 — A fila `email_saida` nasce dentro da transação do cadastro, e o corpo livre não existe

**Data:** 2026-09-05 · **Contexto:** `email_saida` existia como **uma linha de comentário**
(`internal/contas/contas.go:24`) e `internal/socialmail` não existia, de modo que a conta
nascia `nao_confirmada` sem caminho para `ativa`. Esta decisão registra o desenho do pacote que
fecha esse elo. Ela **não** reautoriza o Resend — quem o autoriza, com os três limites e a
medição do link, é a **DEC-046**, que continua valendo sem alteração.

**`Enfileira(ctx, tx *sql.Tx, cofre, mensagem)` recebe a transação e nunca abre a própria.**
Se abrisse, existiriam dois instantes — a conta gravada e a mensagem enfileirada — e uma falha
entre eles produz a pior linha possível: conta `nao_confirmada` sem nenhuma mensagem que a leve
a `ativa`, isto é, usuário trancado do lado de fora sem erro visível em lugar nenhum. Com a
transação de quem chama, o e-mail existe **se e somente se** a conta existir. É a mesma razão
pela qual `internal/contas` já produzia o segredo em claro e o devolvia ao chamador em vez de
enviar: um MTA fora do ar não pode derrubar o cadastro.

**Mala direta é impossível de GRAVAR, e não apenas de escrever.** Não há neste pacote função
que aceite corpo livre: o corpo é derivado de um `Template` de conjunto fechado, o conjunto
está no `CHECK (template IN (...))` do DDL — portanto vale também para quem inserir por outro
caminho — e as únicas variáveis admitidas são campos nomeados e validados (URL https sem
credencial nem fragmento, nome de exibição sem caractere de controle, protocolo em
`[A-Za-z0-9._-]` e uma quantidade inteira). `map[string]string` seria a porta pela qual uma
campanha entraria sem alterar uma linha de DDL. A igualdade entre o enum Go e o `CHECK` é
cobrada por teste que **extrai o conjunto do DDL**, e a trava é provada **por mutação**: o
mesmo teste reescreve o esquema sem a cláusula, aplica num banco novo e grava `'mala_direta'`
com sucesso. Sem essa segunda metade, o teste provaria apenas que o INSERT falhou — não que
falhou *por causa do CHECK*.

**O endereço nunca repousa em claro, e o cofre é interface por necessidade de compilação.**
A fila mora no mesmo `var/social/social.db` das contas, cujo e-mail já é AES-256-GCM; gravar o
destinatário legível desfaria essa proteção com uma tabela nova. Só que `internal/contas` vai
**importar** este pacote para enfileirar a confirmação dentro da transação de cadastro, e
importá-lo de volta fecharia o ciclo e pararia a compilação do módulo. Daí a interface `Cofre`,
com os métodos de mesmo nome e assinatura de `contas.cifraCampo`/`decifraCampo` (`contas.go:307`
e `:325`): ligar os dois custa exportar dois métodos. O AAD é
`email_saida||destinatario_cifrado||mensagem_id`, com o id sorteado antes do INSERT, e o teste
prova que o blob **não abre** com o AAD de outra linha.

**`conta_id` é TEXT e não tem chave estrangeira**, pelo motivo já escrito em
`internal/socialdb/esquema.go` sobre `perfis.conta_id`: FK declarada contra tabela que ainda não
nasceu na ordem de migração não reclama no `CREATE` — reclama em **todo INSERT**, com
"no such table: main.contas", e `PRAGMA foreign_key_check` devolve **vazio** nesse caso, de
modo que a falha não apareceria em gate nenhum, só em produção. TEXT porque `contas.id` é um
sorteio de 16 bytes em base64url, que uma coluna INTEGER alias de rowid recusa com
`datatype mismatch`. O preço de não ter `ON DELETE CASCADE` está pago por `ExpurgaDaConta`,
chamada explícita na eliminação de conta (LGPD art. 18, VI): fila órfã com endereço cifrado é
dado pessoal sobrevivendo ao titular.

**Duas implementações reais atrás de `Transporte`, e a que não entrega hoje também é real.**
`TransporteMTA` resolve o MX e conversa SMTP na porta 25 — correta e completa, num link que a
bloqueia. Ela existe porque o bloqueio é do **link** e não do produto, porque é ela que a
`Sonda` mede (sem implementação, "a porta 25 não sai daqui" seria alegação em vez de medição) e
porque manter as duas rotas atrás da mesma interface é o que impede o Resend de virar
dependência estrutural. Ela **não assina DKIM** de propósito: assinatura sem seletor publicado
computa `dkim=fail` no receptor, que pesa mais contra o remetente do que `dkim=none`.
Reivindicação e envio ficam em transações separadas — manter a transação aberta durante a
conversa SMTP prenderia a trava de escrita do SQLite pelo tempo do timeout, e todo o resto do
produto escreve no mesmo arquivo. Por isso não existe estado "enviando": processo morto no meio
do envio deixa a linha pendente com recuo aplicado, e o preço aceito (possível reenvio) é o
certo — confirmação duplicada é incômodo, confirmação nunca enviada é conta perdida.

**A sonda grava série, não frase.** `data/ops/social_email_entregabilidade.jsonl` recebe, por
medição, o alcance de cada destino, a cadeia FCrDNS, o SPF/DMARC/MX publicados e o que o
`Authentication-Results` **diria** — campo nomeado "prevista" justamente porque não é cabeçalho
recebido. O veredito de bloqueio só é emitido com **controle positivo aberto**: sem ele,
"nenhum destino respondeu" pode ser queda geral de saída TCP, e concluir bloqueio ali seria
alegação sem medição.

**O resumo de quem se segue é opt-in com padrão falso**, em tabela própria, e a ausência de
linha **é** o não: conta criada antes da tabela não recebe nada por omissão, e um bug que apague
a tabela desliga o resumo em vez de ligá-lo para todos. Falhar fechado, no correio, é não
mandar. O desligamento grava a decisão datada em vez de apagar a linha — a data da recusa é a
prova de que ela existiu.

## DEC-055 — A conferencia de prazo é do advogado verificado, e negá-la ao leigo é a lei, não produto

**Data:** 2026-09-05 · **Contexto:** `internal/prazo` calcula prazo processual desde sempre e
**não tinha um único consumidor**. O plano de execução propôs, primeiro, uma triagem para o
leigo — "recebi a intimação em tal dia, até quando ajo" — porque o código estava pronto e a dor
é real. A medição derrubou a proposta por duas razões independentes, e esta DEC registra as
duas, porque a segunda é a que decide.

**A razão técnica:** `prazo.Entrada` exige `CodigoClasse`, `NomeClasse`, `TipoDocumento` e
`TipoComunicacao`, campos que saem de `EntradaDoDJEN(djen.Comunicacao)` — o diário eletrônico.
As presunções do pacote são **atos do diário** (sentença e acórdão com embargos em cinco dias
pelo CPC art. 1.023), contadas no calendário forense. O leigo intimado pessoalmente não tem
nenhum desses campos, e o termo inicial dele é outro (CPC art. 231). Alimentar o cálculo com o
que o leigo sabe informar produziria um número com aparência de precisão e sem lastro — pior
que não responder.

**A razão que decide, e ela é legal antes de ser de produto:** dizer a um leigo até quando ele
deve agir é **consultoria jurídica**, atividade privativa da advocacia pelo art. 1º, II da Lei
8.906/94. Uma plataforma que a automatiza pratica, sem advogado no circuito, o que a lei
reserva — e o risco não é do usuário, é da inscrição de quem responde pelo portal. Não há
desenho de interface que contorne isso: o ilícito está no ato de orientar, não na forma de
apresentá-lo.

**O que fica, então:** a **conferencia de prazo** é ferramenta profissional para profissional,
servida em `/redesocial/conta/prazo/` e restrita ao advogado **verificado** — e "verificado"
significa JOIN com a decisão de verificação vigente (DEC-052), nunca coluna booleana de perfil,
porque a linha em `perfis_advogado` sobrevive à revogação de propósito, para travar o par
número/seccional. Sem sessão a rota responde 303 para a entrada; com sessão de quem não é
advogado verificado, recusa — e a recusa tem teste próprio nos dois canais, HTML e gêmea.

**E o que o leigo recebe no lugar, que é lícito e continua útil:** a informação de que **existe**
prazo e de que ele precisa de advogado. Isso é informação jurídica, não cálculo, e é
exatamente a fronteira que o art. 1º, II desenha. A rede social conduz o leigo ao ato que ela
existe para permitir — publicar a dúvida e ser respondido por quem tem inscrição — em vez de
substituir esse ato por um número.

**Consequência para quem for estender:** qualquer superfície nova que devolva prazo, data-limite
ou contagem regressiva a usuário não verificado reabre esta decisão, e reabri-la exige medir de
novo as duas razões acima — não basta achar que a interface ficou mais clara.

## DEC-056 — A medicao de humano real da rede social sai do log de origem, e isso não é desativar analytics

**Data:** 2026-09-05 · **Contexto:** duas regras do mesmo contrato apontavam para lados
opostos sobre a **mesma** superfície. O CLAUDE.md §6 diz que "analytics é PERMITIDO (decisão do
dono, 2026-08-27) e desativar a medição é proibido". A CSP da rede social é `script-src 'none'`
nas duas variantes — logo zero GA4 e zero Clarity em `/redesocial/`. Um agente obedeceria à que
lesse primeiro.

**A decisão: `script-src 'none'` fica, e a medição da rede social é 100% de servidor.** Três
razões medidas, não preferência.

**A ordem de 2026-08-27 foi sobre o acervo, e a topologia lá é o oposto.** As 10.141 páginas
saem estáticas de `public/` com `s-maxage=604800` — a borda serve a maioria dos visitantes e o
log de origem **não os vê**. Sem GA4 e Clarity ali não haveria medição de humano nenhuma, e é
por isso que a ordem existe. Na rede social **toda** requisição atravessa o Go (não há
`public/`), e o `proxy_cache_bypass $cookie_wjsession` garante que o logado sempre chegue à
origem. O instrumento de servidor vê o que o de cliente veria, e mais: o Clarity só carrega após
1,2 s de ocioso e morre com bloqueador — é piso, não população.

**A rede social publica texto de terceiro.** `script-src 'none'` é a defesa que segura o payload
**quando a sanitização falhar** — e a sanitização é código nosso, logo é código que pode ter
defeito. Trocar a única proteção que não depende de nós estarmos certos por um número que já
temos de outra fonte é trocar para pior.

**Um `<script>` a mais reprova oito gates.** `htmlcontract.go:189` isenta
`internal/pageinline.Script` byte a byte, e a CSP do acervo deriva o hash **dessa** constante.
Servir o loader do acervo em `/redesocial/` exigiria um segundo hash na CSP social ou
`'unsafe-inline'` — e o contrato proíbe o segundo.

**A obrigação que essa decisão carrega, e sem a qual ela vira desculpa:** a **medicao de humano
real** da rede social existe como série derivada do log de origem, com o método escrito e o piso
declarado. Ela nasceu junto com a primeira rota pública, nunca depois — "não tem analytics" só é
honesto enquanto "tem medição". A série sai por `ExecStartPost` do ledger de origem, cujo timer
roda de hora em hora, porque o consumidor é função pura do que o produtor acabou de escrever;
antes disso ela só avançava quando alguém a rodava à mão, e mediu-se o efeito: 3 registros às
08:59 e o tráfego da manhã inteira fora dela.

**O que ela NÃO pode afirmar, e declara:** o teto. A borda serve o anônimo com `s-maxage=3600`
por PoP, então quem foi servido pelo cache não toca a origem — medido, a segunda requisição
volta `HIT` com `age: 0`. O registro publica **piso, método e a ausência de teto**, nunca um
número único (R3 do contrato: amostra não se apresenta como população).

## DEC-057 — A licença do Pwned Passwords, lida na fonte antes de qualquer download, e a lista que fica

**Data:** 2026-09-05 · **Contexto:** `internal/contas` aplica a política de senha do
**NIST SP 800-63B** — piso de 12 caracteres (`ComprimentoMinimoDeSenha`, `senha.go:123`) e
blocklist embarcada, **sem regra de composição**, porque exigir maiúscula, dígito e símbolo
produz `Senha@123` e piora a entropia real. A blocklist existe em
`internal/contas/senhas_comuns.txt` (`//go:embed`, `senha.go:337`) e o cabeçalho dela declarava
que a adoção do Pwned Passwords tinha "licença a apurar na fonte oficial". Esta decisão fecha
essa apuração: a licença foi **lida na fonte, antes de qualquer download**, que é a ordem que a
entrega exige.

**O que a fonte oficial diz, lido em 2026-09-05.** Fonte primária:
`https://haveibeenpwned.com/API/v3`, seção **"License – breach & paste APIs"**, acessada em
2026-09-05 com a identidade `WikijuridicaBot` (HTTP 200, 125.018 bytes). Duas frases, citadas
literalmente:

> "This work is licensed under a Creative Commons Attribution 4.0 International License. In
> other words, you're welcome to use the public API to build other services, but you must
> identify Have I Been Pwned as the source of the data."

> "In order to help maximise adoption, there is **no licencing or attribution requirements on
> the Pwned Passwords API**, although it is welcomed if you would like to include it."

**A leitura corrige uma crença comum, e a correção importa.** Circula a afirmação de que "o
Pwned Passwords é CC BY 4.0"; a fonte não diz isso. A **CC BY 4.0 cobre as APIs de breach e
paste**, com atribuição obrigatória e link visível. O **corpus de senhas** está expressamente
**fora** de qualquer exigência de licença ou de atribuição — atribuir é bem-vindo, não devido.
Também não é "domínio público": a página não usa esse termo, e afirmá-lo seria trocar uma
imprecisão por outra. Quem citar esta DEC cite a frase, não o rótulo.

**Decisão 1 — a lista embarcada NÃO é o Pwned Passwords, e o cabeçalho passa a dizer isso sem
pendência.** `senhas_comuns.txt` é compilação própria dos padrões notórios de senha fraca, com
ênfase no que um usuário brasileiro deste portal escolheria (`senha`, `123456`, `flamengo`,
`habeascorpus`). A comparação é feita sobre o **radical normalizado** — minúscula, leet
desfeito, pontuação e dígitos de borda removidos —, então `Senha@123456`, `s3nh4123456` e
`SENHA123456!!` batem todos em `senha`. É isso que o piso de 12 caracteres sozinho não pega: o
usuário que apenas alonga a palavra com números, que é exatamente o que uma regra de composição
ensinaria a fazer.

**Decisão 2 — o corpus do Pwned Passwords NÃO é adotado agora, e por dois motivos de contrato,
não por prazo.** *(a)* A **API k-anonymity** manda os 5 primeiros caracteres do SHA-1 da senha
a um terceiro dentro do caminho de cadastro e de troca de senha. A rota é
`GET https://api.pwnedpasswords.com/range/{first 5 SHA-1 chars}`, literal da mesma página lida
hoje. O contrato proíbe "API externa proprietária" e "enviar dado do projeto a terceiro", e o
k-anonymity reduz o vazamento sem eliminá-lo: o prefixo é derivado da senha de um usuário
nosso, e a chamada revela a este terceiro o instante em que alguém se cadastra aqui. *(b)* O
**corpus offline** (`https://haveibeenpwned.com/Passwords`, "use the free and open source Pwned
Passwords downloader to take the entire corpus offline and run it yourself") é adoção de dado
externo: exige ADR, versão fixada, medição do tamanho no disco do servidor e benchmark da
consulta sob a carga de cadastro. **O tamanho do corpus não foi medido aqui, e a fonte lida não
o declara** — quem escrever a ADR o mede, e nenhum número entra nesta DEC sem medição própria
(R3). Isso é decisão de arquitetura, não desta entrega — e a licença, que era a única incógnita
jurídica, está agora registrada, de modo que a ADR começa com esse ponto resolvido.

**Decisão 3 — o critério positivo que autoriza a adoção, para que ela não dependa de opinião.**
A lista própria é substituída ou complementada quando **medição própria** mostrar que ela deixa
passar senha real: amostra de senhas recusadas e aceitas pelo `AnalisaSenha` confrontada com o
corpus, com a taxa de falso negativo escrita em `data/ops/`. Sem esse número, trocar uma lista
que funciona por um corpus externo de tamanho ainda não medido é preferência, não engenharia. **Enquanto isso, nada trava**: a
política do 800-63B está no ar, com piso, blocklist por radical e blocklist contextual (o
próprio e-mail, o nome do titular e o vocabulário do site), e é ela que decide hoje.


## DEC-058 — AI-first e B2A: o portal é serviço para IA, com IA local 24/7 e linguagem livre na camada de inteligência

**Data:** 2026-09-08. **Ordem do dono**, redigida pelo Fable 5.1 depois de investigar repo,
produção, host e Ollama. A evidência e o mandato de execução estão em
`docs/goal/PROMPT_AI_FIRST_OPUS5_20260908.md`; a versão curta para abrir a sessão `/goal` em
`docs/goal/PROMPT_GOAL_AI_FIRST_4K.txt`; o plano vivo em `AI-first-wikijuridica.bot`. A política
resumida entrou no `CLAUDE.md` como seção 12.

**Decisão 1 — o produto.** A WikiJurídica é um serviço para IA (B2A). O produto é o contexto
jurídico estruturado de alta densidade; o HTML humano é uma serialização entre várias (gêmea
Markdown, MCP, A2A, `/api/v1`). A métrica que vale é retorno e citação por agente, medida na
borda, não cobertura de rastreio — reafirma o enquadramento de 2026-08-26.

**Decisão 2 — sem cloaking.** Mesmo conteúdo para bot e humano em toda URL; a serialização muda
por URL e por `Accept`, nunca por User-Agent ou por comportamento. A ideia de "transmutação de
interface" por agente foi rejeitada por ser cloaking; a camada adaptativa para humanos fica
dentro da mesma página, no teto de 50 KB.

**Decisão 3 — a IA local.** O Ollama trabalha 24/7 como cérebro de análise, ingestão e proposta, e
nunca escreve em `public/`: produz dado permanente em `data/ai/` e propostas que passam pela
cadeia de publicação. Orçamento físico medido nesta data: CPU-only, 4 núcleos, ~18 GB/s de banda
(`qwen2.5-coder:14b` gera 1,85 tok/s; `qwen3.5:9b` 2,9 tok/s; prompt ~5 tok/s), um modelo
residente por vez e `MemoryMax=15G` (revisão `c35d40a8`). Dois modelos residentes derrubaram o
host às 12:04:53 e o earlyoom matou `llama-server` e os servidores MCP do Claude Code; esse é o
fato que fixa o teto. Trabalho em massa vai em modelos de 0,6 a 4B; o 14b só em lote noturno.

**Decisão 4 — linguagens.** Go continua servindo HTML (DEC-036). A camada de inteligência —
ingestão, embeddings, classificação, previsão, grafo, comportamento — usa a linguagem que der
mais algoritmo e desempenho (Python com toolchain fixada; Rust quando a medição justificar), com
testes na descoberta de `tools/run-qualidade-diaria`. Reescrever Go que funciona em produção
continua proibido.

**Decisão 5 — coleta.** Fonte oficial e API pública se coletam, armazenam, indexam e servem
(`CLAUDE.md` §2). Notícias, portais privados e blogs jurídicos entram como sinal interno
(metadado e trecho limitado com URL, data e hash, `robots.txt` e taxa honrados), nunca como corpo
ou paráfrase. Análise de atores públicos só em agregado, sobre atos públicos, com redação sóbria.

**Decisão 6 — contratos.** `AGENTS.md` e `GOAL.md` se modernizam para frente, com data e motivo no
parágrafo superado e com os guardas de frase rodando.

**O que não muda:** anti-fraude, ética OAB (Provimento 205/2021), cadeia de publicação
transacional, self-hosted first e a proibição de reverter trabalho.

## DEC-059 — Plataforma informativa própria não é captação: o cérebro publica pela cadeia sob a assinatura do advogado, e a ética se cobra pelo conteúdo, não pela contagem

**Data:** 2026-09-09. **Ordem do dono**, registrada pelo Fable 5.1 (sessão wiki-61) depois de medir
o estado do portal (plano em `~/.claude/plans/voc-o-engenheiro-humming-horizon.md`). Texto do dono,
resumido sem mudar o sentido: a plataforma é AI-first, com rede social, notícias, conteúdo diário e
cérebro ativo; o conteúdo é informativo e a rede social é comunidade — **não é captação de
clientela**, porque o dono não vai ao cliente, as pessoas e os juristas vêm à plataforma; o Claude
Code travou trabalho útil por leitura literal do Provimento OAB 205/2021 e de regra que não existe;
a ética se respeita, mas política arcaica que trava a plataforma é perda de tokens e dinheiro; o
cérebro deve publicar páginas coerentes, notícias e comentários **assinados pelo advogado, sem crédito
à IA**; o dono, advogado inscrito, assume a responsabilidade.

**O que muda, com o arquivo:**

1. `content/social_policy.json` — `consulta_publica_de_advogado.habitualidade_modo: "auditoria"`:
   o teto de 5 respostas públicas em 7 dias deixa de recusar e vira parâmetro de auditoria
   (`oab_habitualidade_acima_do_parametro_de_auditoria`, `SeveritySoft`, série de transparência).
   Fundamento: o CED art. 42, I fala em "meios de comunicação social" (imprensa, rádio, TV);
   plataforma informativa própria com resposta geral é o conteúdo que o Provimento 205/2021,
   art. 3º, admite. O regime "bloqueio" fica no código; voltar é uma palavra.
2. `reputacao.destrava_abrir_thread: 0` — thread de pauta (tópico público que não é pergunta) é
   ato fundador da comunidade, livre. As duas portas de spam (link externo e mensagem a
   desconhecido) continuam custando reputação, e a quarentena de conta nova continua.
3. `CLAUDE.md` §12, `GOAL.md`, `AGENTS.md` — "a IA local nunca publica" ganha data e motivo e passa
   a "publica só pela cadeia": rede social pelo processo `cmd/social` (endpoint interno assinado,
   não sessão de browser), acervo pela cadeia v2; gate de conteúdo antes (sem promessa de resultado,
   sem preço, sem orientação a caso concreto, citação verificada por `/api/v1/citacoes`); byline do
   advogado; proveniência privada em `data/ai/publicacoes_cerebro.jsonl`, nunca no HTML.
4. Trailers de commit do harness (`Co-Authored-By`) continuam: não são artefato público.

**O que NÃO muda:** anti-fraude, promessa de resultado, preço como chamariz, orientação individual
em canal público (classificação estrutural manda caso concreto ao canal privado), citação inventada,
`check-lastmod-causalidade` (`reviewed_at` só avança quando o texto muda).

**Como é cobrado:** `internal/socialpolicy` (`TestHabitualidadeModoInvalidoReprova`,
`TestHabitualidadeAuditoriaExigeTeto`, `TestThreadDePautaLivreEValida`), `internal/oabgate`
(`TestHabitualidadeEContagemNaoLeitura/auditoria marca sem recusar`), e os guardas de frase de
`internal/contract/misc`.

## DEC-060 — Alocação de modelos por papel: Fable 5.1 orquestra e refuta, Opus 5.5 executa, Sonnet 5 colhe contexto, Haiku está proibido

**Decisão (2026-09-22, ordem do dono):** o orquestrador de toda sessão deste projeto — Claude
Code no terminal e Cowork — é o **Fable 5.1**: decide, delega, integra, verifica no disco e
commita. **Opus 5.5 é o padrão de execução** — código, dado, gate, hook, teste, deploy e conteúdo
por gerador. **Sonnet 5 só colhe contexto**: lê, mapeia, mede e grava o mapa em
`.agents/runtime/contexto/`; não edita arquivo versionado — a edição básica de documentação que a
ordem admite sai como proposta nesse mesmo arquivo, e quem a aplica é o orquestrador ou um Opus 5.5.
**Fable 5.1 é também o crítico** — o `auditor-adversarial`, que tenta refutar com evidência — e o
executor dos itens graves (`especialista-critico`). **Haiku está proibido** em agente, skill,
parâmetro de chamada e variável de ambiente que a sessão controla. O texto literal da ordem está
em `docs/PRECEDENTES_DAS_ORDENS.md` (sessão de 2026-09-22); o mandato operacional, em
`docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md`; a versão de sessão, em
`docs/goal/PROMPT_OPERACIONAL_4K.txt`.

**Evidência:**
1. **O roster executável contradizia a política escrita.** A alocação de 2026-09-15 (`CLAUDE.md`
   e o "Texto do item 14" do plano do cérebro) dizia "Sonnet não entra neste projeto", e o
   frontmatter de `.claude/agents/` — que é o que o harness roda — mantinha `engenheiro-go` e
   `redator-juridico` em `model: sonnet` e `investigador` em `model: haiku`, com quatro dos cinco
   agentes ainda falando em "maestro Opus 4.8". Três regimes de alocação foram escritos em prosa
   — "Opus 4.8 orquestra, Haiku para lookups" (2026-07-16), "Opus dirige, Fable refuta, Sonnet
   executa" (2026-07-21 e 2026-09-08) e "Opus 5 padrão, Sonnet fora" (2026-09-15) — e nenhum
   chegou ao executável.
2. **Prosa não é mecanismo.** O `CLAUDE.md` chega ao modelo como mensagem de usuário, "there's no
   guarantee of strict compliance" (https://code.claude.com/docs/en/memory); para barrar uma ação
   independentemente do que o modelo decidir, o caminho documentado é um hook `PreToolUse` com
   exit 2 (https://code.claude.com/docs/en/hooks). O modelo do subagente se resolve na ordem
   parâmetro da chamada → `model` do frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → modelo da
   sessão (https://code.claude.com/docs/en/sub-agents#choose-a-model): a prosa não entra nela.
3. **O harness usa Haiku por conta própria.** O avaliador do `/goal` "defaults to Haiku on the
   Claude API" (https://code.claude.com/docs/en/goal) e o subagente embutido `claude-code-guide`
   roda em Haiku (https://code.claude.com/docs/en/sub-agents). A doc manda trocar o avaliador por
   `ANTHROPIC_DEFAULT_HAIKU_MODEL`, que também redireciona o alias `haiku` e as tarefas de fundo
   (https://code.claude.com/docs/en/model-config#environment-variables).
4. **Agente sem modelo declarado herdaria o orquestrador.** O `general-purpose` roda no modelo de
   `CLAUDE_CODE_SUBAGENT_MODEL` ou, sem ela, no da sessão (https://code.claude.com/docs/en/sub-agents):
   com a sessão em Fable 5.1, todo agente lançado sem `model` executaria em Fable, e não em Opus 5.5
   como a ordem manda.
5. **O alias sozinho não fixa a versão que a ordem nomeia.** `opus` só resolve para Opus 5.5 a
   partir da v2.1.280, e `fable` resolve para Fable 5 no Claude apps gateway; a doc manda "To pin
   to a specific version, [...] set the corresponding environment variable like
   `ANTHROPIC_DEFAULT_OPUS_MODEL`" (https://code.claude.com/docs/en/model-config).
6. **O que é da Anthropic e o que é do dono.** A Anthropic recomenda "start with Claude Opus 5.5
   for most workloads" e Fable 5.1 "for demanding reasoning and long-horizon agentic work"
   (https://platform.claude.com/docs/en/models/overview), e descreve o verificador em
   contexto novo que "has a fresh model try to refute the result, so the agent doing the work isn't
   the one grading it" (https://code.claude.com/docs/en/best-practices). Fable como orquestrador de
   toda sessão, Sonnet restrito a contexto e Haiku banido são **escolha do dono**, não recomendação
   literal da Anthropic — valem por ordem, não por citação.

**Consequência:**
- `.claude/settings.json`: `"model": "fable"`; `"advisorModel": "fable"` (para sessão Fable 5.1 o
  único advisor aceito é o próprio Fable 5.1 — https://code.claude.com/docs/en/advisor —, e os
  subagentes herdam); `"availableModels": ["fable", "opus", "sonnet"]` (Haiku fora também onde o
  hook não alcança: `/model`, `--model` e `ANTHROPIC_MODEL` da sessão principal —
  https://code.claude.com/docs/en/model-config#restrict-model-selection) com
  `"enforceAvailableModels": true` (v2.1.175+, escopo "Any file"), que estende a allowlist à opção
  Default do `/model` e a remapeia para a 1ª entrada, o Fable — a garantia plena da Default é de
  managed settings, então aqui ela soma às variáveis, não as substitui;
  `env.ANTHROPIC_DEFAULT_FABLE_MODEL = "claude-fable-5-1"`, `env.ANTHROPIC_DEFAULT_OPUS_MODEL =
  "claude-opus-5-5"` e `env.ANTHROPIC_DEFAULT_SONNET_MODEL = "claude-sonnet-5"` (cada alias aponta
  para a versão da ordem; versão nova só por ordem nova);
  `env.CLAUDE_CODE_SUBAGENT_MODEL = "opus"` (agente sem modelo declarado executa em Opus);
  `env.ANTHROPIC_DEFAULT_HAIKU_MODEL = "claude-opus-5-5"` — o alias `haiku`, o avaliador do `/goal`,
  as tarefas de fundo e os embutidos que caem no padrão Haiku (como o `claude-code-guide`) passam a
  resolver para Opus 5.5; a suposição é que o salto de custo é aceitável, e a doc a sustenta:
  "typically negligible compared to main-turn spend" (raw/goal.md:176) — reversão: se a medição em
  `data/ops/` mostrar gasto de fundo material, aponta-se o alias `haiku` para um modelo mais barato
  que não seja Haiku; hook `block-agent-haiku.sh` em `PreToolUse` `Agent` (barra Haiku em qualquer
  forma e Sonnet em agente que edita); hook `block-write-fora-de-contexto.sh` em `PreToolUse` de
  escrita e de `Bash`; hook `registra-modelo-do-agente.sh` em `PostToolUse` `Agent`, que grava o
  `resolvedModel` de cada chamada em `.agents/runtime/contexto/modelos-<AAAA-MM-DD>.jsonl` e nunca
  bloqueia — é a autoridade contra a qual a 1ª linha "Modelo:" de cada entrega se confere.
- Roster: `engenheiro-go` e `redator-juridico` → `opus`/`high`; `investigador` → `sonnet`/`medium`;
  `auditor-adversarial` e `especialista-critico` seguem `fable`; nasce o `documentador-de-contexto`
  (Sonnet 5, escrita só em `.agents/runtime/contexto/` e na própria memória, com hook de agente).
- Parágrafo superado ganha data e motivo, sem se apagar: `CLAUDE.md` §Governança entre pares,
  `.claude/WORKFLOWS.md`, `docs/goal/COWORK_FABLE_DIVISION.md`, o "Texto do item 14", o §5 e o §6.1
  do plano do cérebro, e a decisão 5 da entrada de 2026-09-15/16 do `MAESTRO_CODEX_LOG.md`.
- A rota "Opus→Sonnet→Haiku" do "Ganho honesto" da DEC-021 fica superada no degrau Haiku: o ganho
  daquela DEC vem do fact-brief, não do rebaixamento de modelo.

**O que não muda:** a **DEC-019** vale sem ressalva — nenhum modelo é superior ou inferior por
identidade, e divergência técnica se resolve por evidência. Esta DEC é alocação de papel e de
custo por ordem do dono, não hierarquia: o `auditor-adversarial` roda no mesmo modelo do
orquestrador, e a independência dele vem do contexto limpo, não do nome do modelo. **Concordância
entre agentes não é verificação; refutação tentada e falhada é.**

**Como é cobrado:** `internal/contract/misc/alocacao_de_modelos_test.go` (roster sem Haiku, Sonnet
sem escrita fora da guarda, modelo e esforço de cada papel fixados e iguais no `WORKFLOWS.md`,
settings da sessão com as versões fixadas, `enforceAvailableModels`, `availableModels[0]` = Fable,
`ANTHROPIC_DEFAULT_HAIKU_MODEL` = `claude-opus-5-5`, os registros de hook — inclusive o
`PostToolUse` `Agent` do registrador — e sem sobreposição no `settings.local.json`, marcadores do
`CLAUDE.md`, mandato com as seções que ele declara e versão de sessão em até 4.000 caracteres, e a
regra do Workflow: em `scripts/workflows/*.js`, `model: 'sonnet'` só com `agentType` de contexto),
`python3 .claude/hooks/block-agent-haiku.test.py`, `python3 .claude/hooks/block-write-fora-de-contexto.test.py`,
`python3 .claude/hooks/registra-modelo-do-agente.test.py` e `tools/check-modo-operacional --provar-mutacao`.

