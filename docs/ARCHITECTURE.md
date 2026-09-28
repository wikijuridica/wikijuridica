# ARCHITECTURE.md

## Decisao de base

O projeto usa Go e biblioteca padrao como base tecnica. A escolha privilegia binario proprio, tipagem estatica, concorrencia nativa, `net/http`, `encoding/xml`, `html` e `testing`, sem SDK externo e sem framework frontend.

Pedido explícito, contrato vivo, checkpoint, roadmap, pergunta de engenharia e achado integrado de agente exigem execução verificável do `/goal` ativo, não comentário, recomendação ou fase posterior. Todo requisito executável pertence a este `/goal`. Arquitetura neste repo deve criar ou operar a peça faltante para a vertical P0: coletor/API/schema/check, armazenamento permanente de trabalho, gerador, gate, render HTML leve, smoke Googlebot, sitemap/canonical/robots, manifesto/transação preparada, publicação aprovada com gate completo e correção executável do item que reprovar. Ajuste arquitetural estreito só é suficiente quando destrava essa cadeia.

## Modulos

- `cmd/build`: gera artefatos publicos em `public/`.
- `cmd/check`: executa validadores locais por `internal/checks`, com `RunAll` para preservar ordem, contexto e cache defensivo dos checks nomeados.
- `cmd/profile-tests`: executa perfil de testes Go via `go test -json` para ranquear gargalos antes de commit.
- `cmd/server`: entrega paginas com geracao on demand propria.
- `internal/httpserver`: handler HTTP testavel para paginas, `robots.txt`, sitemap index e sitemap de paginas, usando os mesmos contratos de canonical/robots do build.
- `internal/content`: modelos e carregamento do manifesto de paginas.
- `internal/manualresearch`: banco leve de pesquisa editorial manual de termos de alta intencao digital.
- `internal/contentbriefs`: briefs editoriais iniciais, nao-template e nao publicaveis.
- `internal/scale`: plano finito de blueprints para pelo menos 10 mil paginas, mantendo bloqueio publico ate release gate completo e sem transformar P0 em adiamento de publicacao aprovada.
- `internal/cta`: politica propria de CTA WhatsApp subordinada a fonte, revisao e aprovacao editorial.
- `internal/router`: rotas canonicas limpas e mapeamento para cache/saida.
- `internal/render`: HTML completo textual, sem hidratacao.
- `internal/ondemand`: geracao sob demanda e cache local controlado pelo projeto.
- `internal/seo`: title, meta description, canonical e robots.
- `internal/crawl`: robots.txt e politica configuravel de bots.
- `internal/sitemap`: sitemap index e sitemap particionado.
- `internal/quality`: gates contra duplicidade, conteudo raso, falta de fonte e falta de revisao.
- `internal/editorial`: estados editoriais e politica index/noindex.
- `internal/editorialdrafts`: persistencia de rascunhos em banco leve, sempre sem rota publica.
- `internal/prioritybriefcandidates`: fila editorial bloqueada que liga prioridades observadas a investigacao interna por `priority_id`/`unique_intent_id`, sem sobrescrever briefs curados.
- `internal/priorityauthorialdrafts`: rascunhos autorais internos bloqueados por prioridade, com texto proprio preliminar, fonte oficial exigida, CTA interno contextual, noindex e publicacao zero.
- `internal/prioritysourcespecificity`: resolucao bloqueada de fonte especifica para rascunhos prioritarios, preservando linhagem por draft/prioridade/intencao, hash de URL, uso reference-only, bloqueio contra scraping/ingestao e decisao explicita entre fonte travada como referencia ou blocker acionavel.
- `internal/priorityreadiness`: prontidao bloqueada pos-fonte para rascunhos prioritarios, cruzando paid-intent, SEO/search appearance, anti-template e revisao juridico-editorial sem render, sitemap, publicacao ou `public_path`.
- `internal/prioritylegalreviews`: revisao juridico-editorial bloqueada para rascunhos prioritarios, consumindo readiness, fonte, rascunho e identidade OAB versionada, com CTA interno e bloqueio publico completo.
- `internal/prioritymanifestplan`: plano bloqueado de `published_manifest` para os gates finais prioritarios, com revisao semantica minima, risco de texto generico, hashes, canonical planejado, requisitos de transacao publica e prova de escrita publica zero.
- `internal/prioritymanifesttransaction`: ensaio transacional bloqueado para os planos prioritarios, validando `publicrelease.TransactionPlan` em memoria sem materializar staging, manifesto, sitemap ou HTML publico.
- `internal/prioritysourceurlaudits`: auditoria metadata-only de URLs oficiais candidatas para blockers prioritarios, separada de conteudo editorial e usada para recalculo de especificidade sem liberar revisao, render, sitemap ou publicacao.
- `internal/reviewqueue`: fila editorial `needs_review` com historico e publicacao bloqueada.
- `internal/approvals`: aprovacao editorial separada de publicacao, ainda sem URL publica.
- `internal/publicationblockers`: manifesto de requisitos faltantes antes de qualquer URL publica.
- `internal/publicrelease`: plano transacional de release público, ainda em laboratório, com evidência de final draft, paid-intent, revisão jurídico-editorial, fonte resolvida, artefatos calculados, staging auditável e promoção bloqueada por padrão.
- `internal/sourceblockers`: bloqueios por termo quando a fonte atual ainda nao e especifica o suficiente para aprovacao/publicacao.
- `internal/legal`: controle de conteudo juridico.
- `internal/sources`: contratos de fontes oficiais.
- `internal/storage`: banco leve proprio em JSONL para termos juridicos, auditorias, snapshots, rascunhos e manifesto publicado.
- `internal/termintents`: candidatos de termos juridicos com demanda humana, fonte oficial e adequacao a contratacao 100% digital.
- `internal/termpromotion`: ranking e promocao controlada de candidatos para seeds `draft_only`, com diversidade de areas e penalizacao de sinais fracos.
- `internal/batchdraftarchive`: arquivo permanente bloqueado de rascunhos de lote que passaram no laboratorio e ainda nao podem virar pagina publica.
- `internal/batchcandidategates`: selecao bloqueada de candidatos a partir do arquivo permanente, com base URL configuravel e publicacao falsa.
- `internal/batchcandidatereviews`: revisao juridico-editorial bloqueada de candidatos de lote, com CTA WhatsApp contextual e matriz de fonte auditada.
- `internal/batchprepublication`: gates de pre-publicacao bloqueada por candidato revisado, com canonical oficial e `noindex`.
- `internal/batchfinaldrafts`: rascunhos autorais finais bloqueados para candidatos com fonte travada e manifesto SEO pendente.
- `internal/paidintent`: gate persistente de intenção comercial paga, bloqueando gratuidade explícita, não pagamento, promessa indevida e status comercial fraco; separa sinal pago do corpo e do CTA, exige contratação particular online nas famílias comerciais e mantém uma lane previdenciária informativa bloqueada por `paid_intent_flexible_previdenciario_informational_blocked_publication`.
- `internal/paidintentrefinement`: refinador em lote para mover sinal de contratação paga do CTA para o corpo informativo quando natural, persistindo ledger bloqueado e mantendo idempotência em no-op.
- `cmd/refresh-editorial-drafts`: regeneracao segura de rascunhos persistidos quando o algoritmo de escrita e refinado.
- `internal/provenance`: contrato de proveniencia por payload antes de qualquer conteudo.
- `internal/architecture`: validacao de estrutura e proibicoes P0.
- `internal/agentcontext`: ledger persistente de contexto de agentes auxiliares para sobreviver a compactação, exigir ID real/escopo/evidência/risco/decisão de integração e impedir uso de pesquisa ou escrita delegada sem validação principal.
- `internal/testprofile`: parser próprio de eventos `go test -json` para timing de testes lentos sem dependência externa.
- `tools`: scripts locais obrigatorios.

## Geracao on demand obrigatoria

Rotas publicas devem poder ser geradas sob demanda por `internal/ondemand`, sem Next.js e sem mecanismo terceirizado de ISR/SSR. O gerador resolve uma rota canonica, valida cobertura de `published_manifest` antes de renderizar página jurídica indexável, renderiza HTML completo no primeiro response e grava cache local. Página jurídica indexável usa assinatura da página e da versão do contrato de render junto do cache para não servir HTML antigo depois de mudança editorial ou de renderizador. Página jurídica que esteja no estado atual como noindex/bloqueada deve regenerar o HTML atual e não reutilizar cache antigo indexável.

O build estatico continua permitido como artefato operacional, mas nao substitui o requisito de geracao on demand propria.

O servidor publico usa `internal/httpserver` para expor tambem `robots.txt`, `sitemap.xml` e `sitemaps/pages-0001.xml` por HTTP real. `./tools/check-http-smoke` prova HTTP 200, content type, robots, sitemap, busca noindex e ausencia de runtime cliente no HTML principal.

`cmd/build` consulta a cobertura de `published_manifest` antes de gerar HTML publico. Página jurídica indexável sem manifesto publicado é bloqueada antes de qualquer alteração em `public/` ou sitemap.

## Release transacional em staging

`internal/publicrelease` prepara a cadeia transacional de publicação do `/goal` ativo sem liberar URL pública por atalho. `BuildPlanFromReleaseEvidence` monta um `TransactionPlan` a partir de rascunho final, paid-intent aprovado, revisão jurídico-editorial, identidade editorial versionada, fonte específica resolvida e datas de aprovação/revisão. O builder calcula hashes de HTML e sitemap a partir do conteúdo planejado, sem confiar em hash informado pelo chamador. Quando os gates reais passarem, a promoção aprovada deve ocorrer e contar para a meta pública mínima, não virar adiamento por nomenclatura de fase.

`MaterializeStaging` escreve somente em `.release-staging/public`, limpa esse staging antes de nova escrita, recusa qualquer `OutputPath` fora de staging e grava `.release-staging/staging_report.jsonl` com tipo, path, output path e SHA-256 de cada artefato escrito. `ValidateStagingReport` compara o relatório com o plano e rejeita artefato ausente, divergente, inesperado ou duplicado; `BuildPromotionPlan` só prepara promoção depois de validar transação, relatório, hashes staged, hash do relatório e raiz única de staging, guardando cópia defensiva da transação, raiz pública final, diretório isolado de promoção fora de `public/` e do staging renderizado, snapshot de rollback do estado público existente, artefatos públicos finais planejados, sitemap final planejado a partir das páginas existentes mais a transação e artefatos de dados finais planejados para `content/pages.json` e `published_manifest`, preservando registros existentes e anexando a transação validada. A mescla planejada bloqueia conflito de path, intenção ou manifest ID já existente antes de qualquer promoção. `MaterializeTemporaryPublicPlan` limpa e recria somente o diretório isolado de promoção, copia HTML staged validado, renderiza sitemap final mesclado, grava dados finais mesclados e persiste `.release-staging/promotion_manifest.json` com status bloqueado, hash do staging report, artefatos planejados e snapshot de rollback; `ValidateTemporaryPublicPlan` compara esse diretório com os artefatos finais planejados, usando caminhos relativos ao repositório e SHA-256, e rejeita arquivo faltante, divergente ou inesperado antes de qualquer troca de `public/`. `RehearseTemporaryPromotion` orquestra a sequência release-ready até `ValidateTemporaryPublicHTTPSmoke` e só retorna `PromotionPlan` quando staging, promoção temporária, hashes e preview HTTP/Googlebot passam; em falha retorna plano vazio e não chama swap, lock, rollback ou promoção real. `BuildPromotionSwapPlan` exige diretório isolado validado, smoke HTTP/Googlebot da árvore temporária e manifesto de promoção íntegro antes de transformar o plano em operações descritivas de swap com SHA-256 do manifesto, snapshot de rollback e cópia defensiva da promoção preparada, registrando `.release-staging/promotion_execution_ledger.jsonl` com `attempt_id` derivado do manifesto, `owner_pid`, `owner_hostname`, `recorded_at` em UTC/RFC3339, `previous_record_sha256`, `record_sha256` e etapa `swap_plan_built`; cada append valida a cadeia existente e rejeita ledger corrompido por `public_release_promotion_execution_ledger_invalid`. `ExecutePromotionSwapPlan` revalida staging, relatório, diretório isolado, smoke HTTP/Googlebot temporário, SHA do manifesto de promoção, conteúdo do manifesto e operações contra os artefatos planejados congelados, cria `promotion_lock.json` por `O_CREATE|O_EXCL` com `attempt_id`, SHA do manifesto, `owner_pid`, `owner_hostname`, `acquired_at` e `lease_expires_at` de 15 minutos, retorna `public_release_promotion_lock_exists` quando já existe execução ativa, `public_release_promotion_lock_stale` quando o lease válido já expirou e `public_release_promotion_lock_invalid` quando o lock existente está corrompido ou incoerente; nesses casos não remove lock, não reaproveita lock expirado e não anexa nova linha de execução no ledger. Só depois de lock recém-adquirido registra `swap_execution_validated` no ledger e continua bloqueado por padrão sem executar renomeação sem release gate final. `BuildPromotionLockRecoveryPlan` aceita somente lock expirado válido, revalida swap, smoke HTTP/Googlebot temporário, manifesto, operações e ledger, congela evidência do lock, path/SHA-256 do arquivo, `observed_at`, último SHA do ledger, contagem e resumo da última linha `swap_execution_validated`; rejeita lock ativo por `public_release_recovery_lock_active` e lock divergente por `public_release_recovery_lock_mismatch`. `ExecutePromotionLockRecoveryPlan` revalida tudo e retorna `public_release_recovery_blocked_by_default`, sem remover lock, sem append no ledger e sem tocar em `public/`; mudança de ledger retorna `public_release_recovery_ledger_mismatch`. `BuildPromotionRollbackPlan` deriva operações de restauração a partir do snapshot público congelado e operações de remoção para outputs novos da promoção, congela a evidência de `promotion_lock.json` incluindo PID, hostname e lease, valida paths relativos ao repositório, SHA-256 e ordem semântica: dados/manifest antes de sitemap, sitemap antes de HTML; lock ausente retorna `public_release_rollback_lock_missing`. `ExecutePromotionRollbackPlan` revalida staging, relatório, diretório isolado, lock congelado, operações de swap, operações de rollback e SHA dos alvos de remoção presentes antes do bloqueio default; lock alterado retorna `public_release_rollback_lock_mismatch`; nenhuma restauração, remoção ou escrita pública é feita. `PromoteStagingToPublic` passa por esse plano preparado, revalida se o hash do relatório mudou, recalcula os hashes dos artefatos staged no momento final e, mesmo com staging válido, permanece bloqueado por padrão por `public_release_promotion_blocked_by_default`.

Staging e diretório isolado de promoção não são publicação. `staging_report.jsonl` validado não substitui `published_manifest`, fonte oficial específica auditada, revisão/OAB, paid-intent/CTA responsável, sitemap público completo, smoke HTTP e release gate final. Qualquer promoção para `public/` deve validar transação, relatório de staging, hashes reais e conteúdo final planejado antes de tocar no diretório público.

`internal/releaserehearsal` diagnostica a prontidão do primeiro candidato real para ensaio temporário sem escrever arquivos. O check `release-rehearsal-readiness` lê rascunhos finais, paid-intent e revisão jurídico-editorial, conta candidatos e retorna o primeiro blocker executável na ordem: final draft ainda bloqueado, paid-intent não aprovado para release, revisão jurídica não aprovada para release. Esse diagnóstico não altera `public/`, `content/pages.json`, `published_manifest` nem flags de render/sitemap/publicação; ele existe para impedir que o P0 confunda rascunho permanente bloqueado com evidência pronta.

`BuildSandboxReleaseEvidenceForTemporaryPromotion` cria evidência release-ready somente em memória a partir de cópias de camadas bloqueadas, para ensaio em fixture/tempdir. A função aceita apenas originais explicitamente bloqueados, exige identidade completa entre final draft, paid-intent e revisão, datas ISO fornecidas pelo chamador e fonte selecionada; em seguida altera somente as cópias para `release_evidence_ready`, `paid_intent_release_approved` e `batch_candidate_review_release_approved`. Essa API não aprova dados reais e não deve ser usada para escrever JSONL, `content/pages.json`, `published_manifest` ou `public/`.

`RehearseFirstBlockedCandidateSandbox` automatiza o ensaio sandbox para o primeiro
candidato real bloqueado. O root real é lido apenas para selecionar o trio coerente
das camadas permanentes; a função grava uma fixture mínima em tempdir, recarrega as
cópias serializadas, chama `BuildSandboxReleaseEvidenceForTemporaryPromotion`,
executa `RehearseTemporaryPromotion` e valida o smoke temporário. `.release-staging`,
HTML, sitemap e dados planejados ficam restritos ao tempdir removido ao final.

`AssessFirstCandidateEditorialBlockers` é o diagnóstico pós-sandbox. Ele cruza o
primeiro rascunho final com revisão jurídico-editorial, resolução de fonte
específica e gate de manifesto público para retornar blockers nomeados sem tratar
blocker como erro de execução. O objetivo é explicar por que um candidato que já
passa no sandbox temporário ainda não pode virar página pública real.

`AssessEditorialBlockerPlan` generaliza esse diagnóstico para o lote inteiro. Ele
usa os rascunhos finais como universo canônico, cruza paid-intent por `draft_id` e
revisão, fonte específica e manifesto por `unique_intent_id`, rejeita duplicatas de
índice antes de agregar, conta blockers por código e por `batch_id`, identifica
candidatos release-ready/publicáveis e calcula a próxima ação editorial. O check
`release-rehearsal-editorial-plan` passa quando consegue calcular o plano sem erro
estrutural; blockers esperados de laboratório são dados do plano, não autorização de
publicação.

`BuildEditorialBlockerPlanReport` transforma o plano em saída operacional read-only.
O relatório ordena batches e blockers, preserva amostras determinísticas por blocker,
mantém `PublicationAllowedCount` e `ReleaseReadyCandidateCount` explícitos e fornece
`SafetyNotice` para evitar que `pass` seja confundido com aprovação. A linha de sucesso
do check também carrega `approval=false`, `publication=false`, `blockers_present=true`,
`publication_allowed=0`, `release_ready=0` e o próximo batch calculado.

## URL base e canonical

`content/site.json` define a base de canonical, robots e sitemap. O dominio oficial do projeto esta travado como `https://wikijuridica.com.br`, com `base_url_mode="official_configured"`, `official_url_status="locked"` e `official_url_locked=true`.

Validadores devem usar a base configurada, nao uma constante de dominio. O contrato continua exigindo HTTPS absoluto, path limpo e canonical correspondente a rota; a URL oficial travada nao libera publicacao de candidatos, que ainda dependem de fonte, revisao, qualidade, SEO, CTA e manifesto publico finito.

## HTML publico leve

Leveza e requisito de indexacao. O renderizador deve entregar HTML textual completo, com CSS minimo e sem JavaScript, bundle, WebAssembly, import map, `modulepreload`, payload de framework ou marcador de hidratacao. Isso protege Googlebot, OAI-SearchBot e outros bots valiosos, alem de reduzir custo operacional em escala massiva.

`internal/checks` reprova HTML publico acima do orcamento, CSS inline excessivo, referencias a runtime cliente e marcadores de Next.js, React, Vue/Svelte/Astro/Angular, Vite ou Webpack. Qualquer excecao exigiria ADR de dependencia e continuaria bloqueada para pagina publica indexavel enquanto P0 estiver ativo.

## Escala e fábrica de conteúdo

Durante P0, a plataforma deve preparar escala massiva sem publicar spam. `content/scale_plan.json` define blueprints finitos para pelo menos 10 mil paginas planejadas, mas a arquitetura deve suportar centenas de milhares ou milhões de URLs por geração on demand própria. O desbloqueio público de conteúdo jurídico exige release gate completo, fonte oficial documentada, proveniencia, autoria, revisão automatizada/algorítmica comprovada, intenção única, qualidade, paid-intent/CTA classificado, SEO/crawl, HTML leve e indexacao coerente. P0 deve continuar produzindo dados versionados, rascunhos, fontes, gates, ensaios e provas bloqueadas rumo à publicação segura; não é fase para passividade documental.

O plano de escala e um contrato de capacidade e uma fábrica de conteúdo validado, nao um gerador de spam para Google. O modulo `scale` deve ajudar a medir capacidade de escala além do piso de 10k deste `/goal`, montar lotes finitos por família jurídica, diversificar intenção e bloquear publicacao em massa enquanto fontes, scoring, CTA e validadores nao estiverem maduros.

Eixo obrigatório implementado: `scalable_content_batches`. Essa camada registra lotes com centenas de milhares de intenções candidatas planejadas, score de naturalidade, fonte, CTA contextual, similaridade intra-lote e decisão de bloqueio. O pipeline deve gerar, pontuar, reescrever e revalidar em lote.

A arquitetura deve favorecer engenharia agressiva inteligente: processamento em lote, validação agregada, diagnósticos específicos, reexecução rápida, refinamento de algoritmo e prova por dados. O runtime público deve continuar barato, mas o laboratório pode consumir CPU de forma agressiva para provar escala e qualidade antes de qualquer publicação.

Achados de auditoria P0 viram execução arquitetural: duplicidade exata de title em `priority_publication_readiness` deve ser corrigida no gerador de `priority_authorial_drafts` com foco real por cenário/contexto, não no classificador; fonte bloqueada com candidato oficial auditado compatível deve virar mapeamento explicável por família/seed/contexto ou nova auditoria URL-level, mantendo reference-only e publicação zero. Esses gargalos devem ser tratados em camada vertical com recálculo downstream, porque afetam diretamente search readiness, fonte, revisão, release evidence e manifesto bloqueado.

## CTA WhatsApp

`content/cta_policy.json` registra a arquitetura de CTA proprio por WhatsApp para paginas de alta intencao de contratar advogado. O CTA nao pode aparecer como atalho para publicar conteudo sem fonte ou sem revisao; ele depende de pagina juridica aprovada, proveniencia e revisao editorial.

CTA WhatsApp e critico para o produto: as paginas devem ser informativas e classificadas para intencao de contratacao digital quando o contexto juridico, a fonte, a etica e o risco permitirem. A classificacao deve produzir CTA contextual rastreavel ou bloqueio explicito; a criticidade comercial nao remove os gates juridicos.

Todo CTA de WhatsApp deve carregar mensagem contextual de origem. A mensagem precisa incluir path/canonical ou rota candidata, intencao unica/termo e resumo da demanda para o atendimento saber de onde a pessoa veio e qual triagem inicial faz sentido.

## Proveniencia por payload

Antes de qualquer dado oficial virar conteudo, o payload precisa de registro com fonte, URL oficial, data de acesso, hash SHA-256, snapshot de robots, snapshot de termos, campos usados e finalidade. Fonte pesquisada nao equivale a conteudo aprovado.

## Banco leve de termos e ingestao

Ingestao de termos juridicos e valida para iniciar conteudos somente como semente de rascunho. O armazenamento e proprio, leve e separado em `content/storage_contract.json`, usando arquivos JSONL em `data/` e biblioteca padrao Go.

Camadas obrigatorias:
- `term_seeds`: termos juridicos para iniciar rascunhos, sem texto oficial bruto e sem texto editorial publico;
- `term_intent_candidates`: candidatos priorizados por demanda humana e contratacao online, ainda sem publicacao;
- `manual_keyword_research`: pesquisa editorial manual de alta intencao digital, com Trends como orientacao e fontes oficiais como autoridade;
- `term_seeds` promovidos: seeds com `candidate_id`, evidencia de demanda, modo `digital_only` e CTA alto, mas ainda `draft_only`;
- `source_audits`: auditoria de robots, termos de uso, alcance HTTP e decisao de bloqueio;
- `batch_source_url_audits`: auditoria URL-a-URL das fontes da matriz de lote, com hash da URL, robots/termos revisados, uso apenas referencial e bloqueio de scraping/ingestao/publicacao;
- `source_snapshots`: snapshots autorizados, pequenos, com hash e proveniencia;
- `editorial_drafts`: texto editorial proprio em PT-BR, sempre noindex ate aprovacao;
- `content_briefs`: brief inicial natural e especifico por termo, sem URL publica;
- `authorial_content_drafts`: rascunhos autorais derivados de briefs, com anti-template, CTA digital contextual e publicacao bloqueada;
- `priority_brief_candidates`: candidatos bloqueados derivados de prioridade observada, preservando observacoes externas, fonte exigida e identidade por prioridade/intencao, sem texto autoral e sem publicacao;
- `priority_authorial_drafts`: rascunhos autorais internos permanentes derivados de candidatos prioritarios, com fonte oficial exigida, CTA interno contextual, orcamento de title/meta, noindex e flags publicas falsas;
- `priority_source_specificity_resolutions`: resolucoes bloqueadas de fonte especifica por rascunho prioritario, com metadados e hash de URL, sem texto oficial bruto, sem scraping, sem ingestao, sem render, sem sitemap e sem publicacao;
- `priority_publication_readiness`: diagnosticos bloqueados de prontidao pos-fonte por rascunho prioritario, com paid-intent, SEO/search appearance, anti-template, revisao juridico-editorial e gates restantes, sem render, sitemap, publicacao ou `public_path`;
- `priority_legal_editorial_reviews`: revisoes juridico-editoriais prioritarias bloqueadas, com identidade OAB versionada, notas de revisao, required_fixes, CTA interno, bloqueio de paid-intent quando cabivel e flags publicas falsas;
- `priority_release_evidence`: evidencias bloqueadas de release prioritario, com hash de HTML, canonical, robots noindex, smoke Googlebot e publicacao zero;
- `priority_release_transaction_evidence`: evidencias HTTP transacionais bloqueadas da vertical prioritaria, com rota candidata isolada, robots, sitemap de ensaio, hashes, smoke HTTP/Googlebot e prova de ausencia nos artefatos publicos reais;
- `priority_promotability_selection`: selecao bloqueada de promotabilidade prioritaria, separando candidatos pre-release tecnicamente aptos de exclusoes por paid-intent/fonte/tecnica, sem abrir render, sitemap, `public_path` ou publicacao;
- `priority_release_gate`: gate final bloqueado dos candidatos prioritarios selecionados, exigindo aprovação jurídico-editorial algorítmica/Codex auditável, plano de manifesto, canonical/robots/sitemap indexaveis, smoke publico Googlebot, leitura amostral e escrita publica zero;
- `priority_manifest_plan`: plano bloqueado de manifesto para os gates finais, com revisao semantica, requisitos de escrita transacional, bloqueadores finais, hashes e flags publicas falsas; nao e `published_manifest` e nao publica;
- `priority_manifest_transaction_rehearsal`: ensaio transacional bloqueado para os planos de manifesto, com `TransactionPlan` valido em memoria, hashes, lock/rollback exigidos e materializacao publica proibida;
- `priority_source_url_audits`: auditoria metadata-only de URLs oficiais candidatas para blockers prioritarios, com hash, metodo de evidencia, fonte rejeitada, proxima acao e bloqueio total de render/sitemap/publicacao;
- `source_specificity_blockers`: manifesto que impede aprovacao/publicacao quando o termo ainda precisa fonte primaria, norma especifica ou recorte juridico;
- `source_specificity_resolutions`: manifesto de fontes especificas resolvidas para pre-publicacao, ainda sem URL publica;
- `prepublication_gates`: contrato SEO/crawl para rota candidata finita, com render, sitemap e publicacao bloqueados;
- `legal_editorial_reviews`: revisao juridico-editorial bloqueada com CTA WhatsApp contextual em rascunho;
- `scalable_content_batches`: lotes massivos de intenções únicas e rascunhos autorais, bloqueados quando houver spam, template ou score humano insuficiente;
- `human_content_score`: score de naturalidade/IA-like/mecânico para revisão algorítmica, reescrita e auditoria;
- `batch_drafts`: rascunhos de amostra por lote massivo, com score e reescrita comprovada, ainda sem render, sitemap ou publicacao;
- `batch_draft_expansion_archive`: arquivo permanente bloqueado de rascunhos validados em laboratorio, preservado como base de pesquisa jurídica interna e candidatos a publicacao futura ate prova contraria;
- `batch_candidate_expansion_readiness`: prontidao bloqueada de expansao por familia, conectando os rascunhos permanentes versionados aos alvos derivados por `archive_prefix_by_batch` e diferenciando paid-intent ausente, paid-intent existente mas reprovado, fonte ampla, proximo gate pendente e flags publicas;
- `batch_candidate_gates`: gate permanente de candidatos selecionados do arquivo, atualmente com 2.220 intenções internas em 24 shards físicos, ainda sem render, sitemap, publicacao ou `public_path`;
- `batch_candidate_reviews`: revisao juridico-editorial bloqueada de cada candidato de lote selecionado, com fonte matricial auditada e CTA WhatsApp de origem rastreavel;
- `batch_prepublication_gates`: pre-publicacao bloqueada de cada candidato revisado, com canonical oficial, title/meta, `noindex` e fonte final ainda pendente;
- `batch_source_specificity_resolutions`: resolucao de fonte por candidato pre-publicado, marcando URL especifica auditada ou bloqueio explicito por fonte ampla, sem liberar render/sitemap/publicacao;
- `batch_public_manifest_gates`: manifesto publico bloqueado por candidato, permitindo SEO/conteudo pendente apenas quando a fonte esta travada e mantendo fonte ampla bloqueada;
- `batch_final_authorial_drafts`: rascunhos autorais finais bloqueados, com fonte travada, score humano/naturalidade, CTA contextual e intenção comercial paga, ainda sem render, sitemap ou publicação;
- `batch_paid_intent_gates`: gate bloqueado de intencao comercial paga por rascunho final ou alvo de expansao, com `gate_scope`, `paid_signals` do corpo, `cta_paid_signals` do CTA, status comercial especifico para CTA-only/curiosidade/gratuidade/autoatendimento e status previdenciario informativo restrito a `batch-previdenciario-digital`;
- `batch_paid_intent_refinements`: ledger bloqueado de refinamentos em lote, registrando status original, status apos reescrita, campo alterado, sinal pago no corpo, score humano e flags publicas falsas;
- `batch_generation_metrics`: métricas agregadas de geração/refino por lote, provando volume, reescrita, score e similaridade sem criar URL pública;
- `batch_source_matrix`: matriz de fontes oficiais por subtema, usada como referência/proveniência sem scraping e sem publicação;
- `batch_source_url_audits`: auditoria das URLs da matriz, separada da camada editorial, exigindo cobertura de cada URL por `matrix_id` antes de escalar rascunhos;

Ferramentas operacionais de escala: `./tools/expand-batch-candidate-gates` recalcula a seleção current sem salto implícito; `./tools/advance-batch-candidate-gates` promove explicitamente o `next_candidate_target` planejado pela estratégia; `./tools/refresh-batch-candidate-pipeline` propaga a seleção para revisões, pre-publicação, fonte específica, manifesto e rascunhos finais bloqueados. As ferramentas devem ser idempotentes e não podem publicar: elas travam fonte por matriz quando existe URL oficial específica auditada, geram rascunhos finais bloqueados para manifests elegíveis, preservam apenas rascunhos antigos que ainda passam score/qualidade e mantêm os demais candidatos em `final_source_blocked_needs_specific_url`.
- `published_manifest`: manifesto leve de conteudo aprovado, sem substituir o renderizador.
  Página jurídica indexável em `content/pages.json` precisa estar representada em `published_manifest`; home/institucional não jurídica pode permanecer fora do manifesto jurídico.

`internal/checks.RunAll` orquestra `cmd/check all` e preserva a API `Run(name, root)` para checks isolados. O contexto atual cacheia resultados top-level com cópias defensivas; cache tipado dentro dos validadores downstream continua como evolução P0 para reduzir recálculo interno sem enfraquecer gates. Cache, arquitetura genérica ou otimização interna não podem tomar a frente de demanda externa, fonte, conteúdo, SEO/crawl, release bloqueado ou publicação segura quando o diagnóstico atual indicar cobertura inicial (`external_coverage_initial_needs_more_observation`), salvo falha P0 de performance que bloqueie a própria coleta, validação ou promoção.

Camada operacional fora do banco de conteúdo:
- `.agents/agent_context_ledger.jsonl`: registra subagentes por ciclo, ID real, escopo, status, política de uso, evidência, riscos, decisão de integração, validação obrigatória do Codex principal e fechamento antes do checkpoint ou preservação explícita de contexto concluído/integrado. Não é conteúdo jurídico, não autoriza publicação e não substitui validação do Codex principal.

Regra P0: termos podem iniciar `draft_only`; nenhuma linha do banco vira pagina indexavel sem fonte, revisao, qualidade, SEO, intencao unica e checkpoint.

## Laboratorio

Toda mudanca P0/P1 deve passar por ciclo de laboratorio proporcional ao risco: escrever ou ajustar teste, rodar validacao focada, refinar, testar novamente e inspecionar artefatos. `tools/lab-cycle` existe para momentos criticos e combina `./tools/go-modern test -count=1 ./...`, `./tools/go-modern run ./cmd/check all`, build, auditoria de dependencias, diff check e busca por residuos Python, sem duplicar checks individuais ja cobertos. Ele nao e ritual obrigatorio de todo ciclo.

O laboratorio pode gerar primeiro em `/tmp`, mas resultado validado, juridicamente util e reutilizavel deve ser trazido para o repo como camada permanente bloqueada. Isso evita depender de contexto compactado ou diretorio de execução em `/tmp` para continuar a fabrica de conteudo, sem confundir rascunho aprovado em laboratorio com pagina publicada.

Antes de commit, o laboratório deve registrar autocrítica: hipótese do ciclo, prova obtida, riscos, melhorias possíveis, motivo pelo qual o commit é apenas checkpoint e próximo ciclo planejado. Essa autocrítica impede commit tratado como conclusão do projeto massivo.

## Release público transacional

O módulo `internal/publicrelease` mantém a promoção pública em laboratório bloqueado. Staging, plano de promoção, swap e rollback são contratos executáveis de preparação, não autorização de publicação.

`ValidateTemporaryPublicHTTPSmoke` valida a árvore de promoção materializada antes do swap real. Ela combina `TemporaryPublicRoot/public` com `robots.txt` e `sitemap.xml` gerados em preview a partir das configs do repo, exige que `TemporaryPublicRoot/content/pages.json` preserve as páginas indexáveis da transação exatamente como congeladas no plano, verifica páginas indexáveis da transação com status 200, canonical, robots, H1, HTML sem runtime cliente e orçamento de 50 KB, além de conferir o sitemap final planejado. Essa validação complementa hashes e não escreve em `public/`.

Swap planejado usa sequência exata: HTML público primeiro, sitemap depois e dados/manifesto por último. O executor bloqueado reconstrói essa ordem a partir dos artefatos congelados e reprova reordenação com `public_release_promotion_plan_invalid`.

Rollback planejado separa restauração de snapshots e remoção de artefatos criados. Antes de qualquer execução real, o executor bloqueado revalida staging, relatório, artefatos temporários, operações de swap, sequência exata do rollback e SHA-256 dos alvos. Remoções só aceitam alvo ausente ou com SHA criado pela promoção; restaurações só aceitam alvo ausente, alvo igual ao snapshot ou alvo igual ao SHA promovido planejado para aquele output. Divergência retorna `public_release_rollback_target_changed`; reordenação retorna `public_release_rollback_plan_invalid`; nenhuma escrita pública é feita.

## Evidência de Release Prioritária

`internal/priorityreleaseevidence` conecta a vertical prioritária revisada ao contrato de render/SEO sem abrir publicação. O módulo consome `priority_legal_editorial_reviews`, `priority_authorial_drafts`, `priority_publication_readiness` e `content/site.json`; monta `content.Page`, renderiza via `internal/render`, calcula SHA-256/bytes e valida canonical oficial, robots `noindex,follow`, HTML leve e ausência de runtime cliente.

Essa arquitetura preserva separação de responsabilidades: o HTML de evidência é hash de ensaio, não arquivo público; `SitemapCandidateURL` é candidato bloqueado, não entrada em sitemap real; `RenderAllowed`, `SitemapAllowed`, `PublicationAllowed`, `Approval` e `PublicPath` continuam fechados. A otimização é real porque antecipa falha de HTML/Googlebot antes do release transacional, mas não substitui `internal/publicrelease`, HTTP público real, manifesto publicado ou escala mínima.
