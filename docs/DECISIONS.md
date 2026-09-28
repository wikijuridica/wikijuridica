# DECISIONS.md

Nota operacional viva: entradas datadas preservam contexto histórico e podem citar `published_manifest=0`, `content/pages.json` intocado ou `public/` intocado como verdade daquele ciclo. Para o estado atual, prevalecem os artefatos vivos e checks executáveis: `data/editorial/published_manifest.jsonl`, `content/pages.json`, `public/`, `public/sitemaps/`, `./tools/check-published-manifest`, `./tools/check-public-release-transaction-unlock-consistency` e `./tools/check-p0-cycle-close-indexable-10k`. Não use uma decisão histórica como prova de publicação zero nem como aprovação pública.

## 2026-06-30 - Worktree compartilhada e fonte operacional para todo Codex

Decisao: toda a worktree compartilhada é fonte de verdade operacional. Todo Codex que operar neste repo obedece esta regra como lei permanente do repositório. tracked, staged, unstaged, untracked e diretórios versionáveis contam como dados vivos. `git ls-files`, índice Git, commit base, staged snapshot ou `git_index_tracked_content` não podem substituir leitura e validação da worktree viva. `worktree_filesystem` é o snapshot padrão para evidência viva de fábrica. `git_index_tracked_content` nunca cobre frescor, head atual, worktree viva, comando pesado, rerun, release ou decisão P0. `git_head` atual só pode ser coberto por registro dedicado `ledger_current_head_refresh`; registro genérico `completed` ou `reused` não cobre freshness do head atual e reprova por `work_reuse_current_head_refresh_required`. `ledger_current_head_refresh` deve registrar `worktree_filesystem`, `git status --short`, `git diff`, `git diff --cached`, `git ls-files --others --exclude-standard`, `git log`, `git show --stat HEAD`, `committed_history`, dirty paths materiais e fingerprints do disco vivo. untracked versionável deve ser lido, classificado, fingerprintado, integrado para frente ou colocado em camada bloqueada validada, sempre com flags públicas falsas quando ainda não houver release aprovado. checks devem falhar quando untracked versionável material for invisível ao contrato ou ao ledger.

Motivo: o projeto opera com dirty tree, agentes, frentes paralelas e dados grandes. Usar índice Git ou snapshot staged como padrão apaga trabalho vivo, esconde integração open source pendente, cria falso verde de ledger e permite passividade. A regra vira contrato repository-wide e regressão em `internal/contract`, não recomendação de ciclo.

Consequencia: contrato, runbook, goal e ledger precisam tratar untracked versionável, índice e histórico commitado como estado vivo. Evidência de fábrica deve registrar `worktree_filesystem`, `git status --short`, `git diff`, `git diff --cached`, `git ls-files --others --exclude-standard`, `git log`, `git show --stat HEAD`, `committed_history`, dirty paths materiais e fingerprints do disco vivo; `git_index_tracked_content` nunca cobre frescor nem head atual. Check que não enxerga worktree viva e histórico commitado precisa falhar ou ser corrigido para frente.

Consequencia executável adicional: Registro `ledger_current_head_refresh` e registro material de comando pesado devem carregar em `data_read_paths` a leitura explícita de `staged`, `unstaged`, `untracked`, `git diff --cached`, `git ls-files --others --exclude-standard`, `git show --stat HEAD` e `committed_history`; `git status --short` sem esses estados declarados é evidência incompleta e reprova por `work_reuse_current_head_repo_awareness_missing` ou `work_reuse_repo_awareness_missing`.

Guarda executável anti-descarte: comandos, automação, ledger, artifact_claim, analise_comando_ativo, próxima ação, RCA ou check não podem recomendar `git reset`, `git restore`, `git checkout`, `git revert`, `git clean`, `git stash`, `git switch -f`, `git switch --discard-changes`, `git rm`, `git update-index --assume-unchanged`, `git update-index --skip-worktree`, `rm`, `unlink`, `truncate`, limpeza destrutiva, tratar diff/untracked/worktree viva como lixo, ou orientar apagar, limpar, remover, ignorar, esconder, invalidar ou reverter trabalho vivo. O ledger deve reprovar esse bypass por `work_reuse_live_worktree_discard_recommendation`; a correção válida é leitura, classificação, fingerprint, integração para frente, camada bloqueada validada ou decisão explícita do usuário, nunca tratar diff/untracked como lixo. Linguagem de registro supersedido só é aceita para registro ledger histórico e não pode aparecer junto com descartar diff, untracked ou worktree viva.

Regra executável de comando pesado: Registro de comando pesado, gerador, check de release, validação em escala ou rerun equivalente que não carregue essas leituras em `data_read_paths` reprova por `work_reuse_repo_awareness_missing`; a resposta obrigatória é ler repo vivo, ledger, histórico, staged, unstaged, untracked, artefatos e editar para frente.

Regressão Git viva vinculada ao `work-reuse-ledger`: os checks `work-reuse-ledger`, `duplicate-command-guard` e `artifact-freshness` devem manter o vínculo executável entre contrato e ledger. Registro de comando material sem `worktree_filesystem`, `git status --short`, `git diff`, `git diff --cached`, `git ls-files --others --exclude-standard`, `git log`, `git show --stat HEAD`, `committed_history`, `staged`, `unstaged` e `untracked` reprova por `work_reuse_repo_awareness_missing` ou `work_reuse_current_head_repo_awareness_missing`; comando, RCA, artifact_claim, análise ativa ou próxima ação que trate diff, staged, unstaged, untracked, histórico commitado ou worktree como lixo descartável reprova por `work_reuse_live_worktree_discard_recommendation`; `ledger_current_head_refresh` baseado em índice, commit base, staged snapshot ou `git_index_tracked_content` reprova por `work_reuse_current_head_git_index_snapshot_forbidden`. Esses estados não podem ser tratados como histórico descartável; a correção é editar para frente, fingerprintar/ler o disco vivo, integrar achado útil, recalcular derivados e validar.

Autocritica: a regra aumenta segurança de integração, mas não publica página sozinha. Ela reduz falso negativo de trabalho compartilhado e força o próximo Codex a operar código, dado, check e integração real em vez de esconder pendência por estado do índice.

## 2026-06-25 - Delegacao proporcional de subagentes substitui contagem fixa

Decisao: a ferramenta de agentes e meio tecnico permitido por criterio proporcional neste `/goal` e tambem obrigatorio quando houver frente independente real, revisao, performance, integracao, causa raiz ou risco P0. ciclos P0 complexos e todo ciclo novo do `/goal` devem registrar decisao explicita de delegacao proporcional, com quantidade, escopo, `model`, `effort`, `service_tier`, risco e motivo tecnico. Em P0 ativo, `model`, `effort` e `service_tier` reais devem ser exatamente `gpt-5.5`, `xhigh` e `priority`; valor herdado, vazio, inferior, `pre_rule_unspecified` ou sem tier reprova. A contagem fixa historica de agentes e revisores fica substituida: sem teto operacional artificial quando houver frentes independentes reais, e nova onda deve ter escopo objetivo, frente independente clara e integracao prevista no mesmo ciclo.

Motivo: contagem fixa virou custo operacional e loop de recursos quando a tarefa nao tinha frentes independentes suficientes, enquanto ainda deixava o risco real sem resposta quando havia diff critico. A politica vigente precisa manter agressividade inteligente: agentes entram para acelerar pesquisa, patch, revisao e investigacao com escopos disjuntos, mas o Codex principal continua responsavel por integracao, validacao, checkpoint e commit.

Consequencia: escopo editavel so e valido com `delegated_repo_write_codex_validated`, sem commit pelo subagente, com validacao obrigatoria do Codex principal. Revisao independente passa a ser proporcional ao risco antes de commit critico. Todo agente usado continua exigindo ledger completo, fechamento, `model`, `effort`, `service_tier`, achados aproveitados e decisao concreta de integracao no mesmo ciclo.

Autocritica: a mudanca reduz desperdicio de agentes sem autorizar passividade. O risco remanescente e Codex usar "proporcional" como desculpa para trabalhar sozinho em frentes paralelizaveis; por isso a decisao precisa ser registrada e validada por contrato, e falta de agente em frente independente real continua falha de execucao.

## 2026-06-22 - Regra anti cherry-pick e revisão de frentes vivas

Decisao: antes de qualquer commit ou integração de frente paralela, o Codex principal deve revisar frentes vivas, `git status --short`, `git diff`, `git diff --cached`, `git ls-files --others --exclude-standard`, `git log`, `git show --stat HEAD`, diff por arquivo, histórico recente e artefatos compartilhados que possam ter sido tocados por outra execução. A integração correta é preservar evolução válida e editar para frente no arquivo vivo.

Motivo: este `/goal` opera com dirty tree, subagentes e frentes paralelas. Merge cego, `git cherry-pick`, pick/cherry manual de snapshot ou substituição de arquivo por estado antigo pode apagar evolução concorrente, commitar contador stale, esconder falha de ferramenta ou transformar checkpoint histórico em fila errada.

Consequencia: `merge`, merge cego, `git cherry-pick`, pick/cherry manual de snapshot, `git restore`, `checkout`, `reset`, `revert`, limpeza destrutiva e substituição por snapshot antigo ficam proibidos como mecanismo normal de integração. Se um ciclo tomou direção errada, a resposta é causa raiz, guarda executável, dado regenerado, validação proporcional e correção para frente.

Autocritica: a regra não substitui validação nem autoriza acumular diff sem revisão. Ela aumenta segurança de concorrência, mas ainda exige leitura real dos dados e dos contratos antes de commit, especialmente quando agentes ou outra frente tocaram JSONL, release, publicação, checks ou docs contratuais.

## 2026-06-17 - Timing P0 separa prova pesada de validacao rapida

Decisao: otimizar `storage-contract` e `authorial-mass-controlled-promotion` sem enfraquecer gates publicos. `storage-contract` passou a validar JSONL por `json.Valid`, checagem explicita de objeto e scans paralelos limitados por camada com ordenacao deterministica de mensagens. `authorial-mass-controlled-promotion` passou a gravar fingerprint da fonte e hashes de evidencia do ensaio pesado, permitindo que `Validate` confirme frescor sem reconstruir staging/temp public/smoke/swap em todo check; `Generate` continua executando o ensaio completo.

Motivo: o ciclo anterior deixou gargalos medidos em checks de rotina (`storage-contract` acima do alvo fast e `authorial-mass-controlled-promotion` em torno de 9-12s). Repetir parse completo de centenas de MiB ou reconstruir o ensaio de promocao a cada check reduzia a capacidade de ciclos longos e incentivava validacao menor. O objetivo era melhorar throughput de laboratorio mantendo prova pesada sob comando gerador e mantendo publicacao bloqueada.

Consequencia: o registro `authorial_mass_controlled_promotion_rehearsal` agora inclui `source_transaction_sha256`, `transaction_plan_sha256`, `staging_report_sha256`, `promotion_manifest_sha256`, `planned_public_artifact_count` e `planned_public_data_artifact_count`, todos bloqueados. `ops_check_selection_profiles` foi regenerado com `selected_checks=238`, incluindo `authorial-mass-release-evidence`, `authorial-mass-release-transaction`, `authorial-mass-manifest-transaction`, `authorial-mass-controlled-promotion`, `priority-controlled-promotion` e `public-release-transaction` em caminhos de release, preservando o check comercial P0 já presente no main. A cadeia derivada atual tem `paid_passed=5355`, `paid_blocked=4645`, `googlebot_smoke=5355`, `manifest_record_count=5355`, `refinement_max_body_similarity=0.6174`, `refinement_high_risk_pairs=18` no rollup e `publication_allowed=0`. `Generate` pesado permanece obrigatorio quando o plano fonte ou o ensaio precisar ser recalculado. `published_manifest` permanece zero e nenhuma flag publica foi aberta.

Autocritica: fingerprint nao aprova pagina, nao substitui fonte final, nao corrige blocker anti-template ou editorial remanescente e nao reduz o deficit publico de 10.000. Ele apenas impede falso stale e reduz custo operacional. Se a fonte mudar, se faltar hash de evidencia ou se o gerador alterar staging/HTML/sitemap/manifesto, o check deve falhar e o proximo passo e regenerar a promocao controlada pesada antes de qualquer release.

## 2026-06-16 - Codex 2 trava locks internos por live metadata sem publicar

Decisao: criar `codex2_source_codex_lock_decision` como camada bloqueada que consome `codex2_source_live_recheck`, aprova somente locks internos de referencia quando HEAD/status/hash live estao acessiveis e bloqueia os demais como sem acesso live ou nao prontos para rechecagem.

Motivo: a rechecagem live de 209 candidatos oficiais podia indicar URLs internamente lockaveis, mas ainda nao autorizava texto oficial, fonte final publica, CTA, render, sitemap, `content/pages.json`, `published_manifest` ou publicacao. Era necessario transformar essa evidencia em decisao executavel sem exigir revisao humana por pagina e sem abrir artefato publico.

Consequencia: a camada registra 209 decisoes, sendo 8 `codex_source_lock_approved_reference_only_blocked`, 49 bloqueadas por falta de metadata live acessivel e 152 bloqueadas por nao estarem prontas para live recheck. Todos os registros mantem `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `manifest_allowed=false`, `published_manifest_write_allowed=false`, `content_pages_write_allowed=false`, `public_artifact_write_allowed=false`, sem raw/official text, sem response body e sem CTA publico.

Autocritica: lock interno de referencia nao e fonte final nem pagina publica. A proxima promocao ainda precisa de fonte oficial especifica final, revisao juridico-editorial/OAB, politica Google, terms/robots/privacy, HTML leve, canonical/robots/sitemap e release gate completo; `published_manifest` permanece zero.

## 2026-06-15 - Refino negativa-formal trabalhista e continuidade por cobertura direcionada

Decisao: adicionar regressao focada para `horas-extras-nao-pagas` versus `verbas-rescisorias-nao-pagas` em `negativa-formal/prazo-sete-dias`, especializar o gerador com secoes materiais de jornada/ponto/escala/banco de horas versus TRCT/aviso/FGTS/rubricas finais e recalcular a cadeia bloqueada.

Motivo: o topo vivo anterior tinha `max_body_similarity=0.6683` e repetia estrutura entre negativa de horas extras e negativa de acerto final. A correção precisava preservar a evolução trabalhista do ciclo anterior sem remover conteúdo e sem relaxar threshold.

Consequencia: apos regenerar a cadeia bloqueada no main combinado e depois ampliar os gates finais para o estoque autoral completo, `authorial_mass_similarity_report` ficou com `max_body_similarity=0.6806`; `authorial_mass_refinement_quality_report` manteve 81 registros e 2.759.729 comparacoes por grupos, com `max_body_similarity=0.6250`, 66 pares de alto risco no rollup e 0 eventos semanticos; `authorial_mass_shard_refinement_plan` ficou com 100 planos, 10.000 conteudos, 2.805 eventos top-k, 66 eventos top-k de alto risco e prioridade no shard `authorial-mass-scale-shard-001`. O refino trabalhista foi preservado, mas o topo vivo do main passou para `reembolso-plano-saude` versus `revisao-aposentadoria` em `prazo-urgente/prazo-sete-dias`.

Autocritica: o refino reduziu risco trabalhista e provou que fingerprint impede falso verde stale, mas nao publica pagina, nao resolve fonte final e expôs novo risco de alto template no main combinado. A proxima macrocamada Codex principal deve tratar o shard 001 ou frente vertical equivalente de conteudo/fonte/revisao/release, mantendo `published_manifest=0`; a frente Codex 2 de cobertura externa direcionada deve seguir isolada e ser preservada sem merge cego.

## 2026-06-15 - Fingerprint reduz check pesado de refino massivo

Decisao: `authorial_mass_refinement_quality_report` passa a gravar fingerprint de todo o estoque, fingerprint do grupo e assinatura de evidencia do proprio relatorio. O check `authorial-mass-refinement-quality-report` valida esses fingerprints e deixa de recomputar 13.090.690 pares quando o JSONL esta fresco.

Motivo: a geracao completa continua necessaria quando corpo, fonte, CTA, title/meta ou algoritmo mudam, mas repetir todos os pares em cada check cria gargalo de escala. O estado desejado e falhar rapido quando o artefato esta stale e rodar a geracao pesada apenas quando o fingerprint indicar que ela e obrigatoria.

Consequencia: o ledger vivo agora tem `checks=123`, `heavy=5`, `medium=28`, `fast=90`, `always_run=118` e `publication_allowed=0`. `authorial-mass-refinement-quality-report` e `authorial-mass-contextual-compatibility` seguem `medium`; o relatório de refino valida fingerprint em poucos segundos no check fresco, e `./tools/generate-authorial-mass-refinement-quality-report` permanece a operacao pesada para recalcular os pares quando fingerprint ou corpo mudarem. Os 81 relatorios seguem bloqueados, `noindex`, sem render/sitemap/publicacao e com `max_body_similarity=0.6207`.

Autocritica: fingerprint nao substitui refino autoral nem fonte final. Ele melhora escala operacional e impede falso verde stale, mas quando o check reprovar por fingerprint a resposta correta continua sendo regenerar o relatorio completo, revisar o topo vivo e recalcular os derivados antes de release.

## 2026-06-15 - Perfis de selecao transformam ledger em comando proporcional

Decisao: criar `ops_check_selection_profiles` como camada operacional bloqueada que consome o ledger de performance e materializa perfis executaveis para `p0-fast`, `p0-authorial-mass`, `p0-release`, `p0-full-heavy-triggered` e selecao ad hoc por paths.

Motivo: o ledger classificava custo, mas ainda deixava a escolha de checks dependente de leitura manual do Codex. Em escala, isso vira dois riscos: rodar contratos pesados por habito ou pular cobertura relevante por excesso de confianca em teste verde. O seletor torna a decisao proporcional verificavel e repetivel.

Consequencia: o estado vivo tem `profiles=4`, `selected_checks=238`, `heavy_profiles=2` e `publication_allowed=0`. Paths autorais selecionam `authorial-mass-refinement-quality-report` como check de fingerprint; paths de docs/storage/ops selecionam checks rapidos como `storage-contract`, `ops-check-performance-ledger` e `ops-check-selection-profiles`; paths de release/publicacao acionam contratos de release, manifesto, promocao controlada, `public-release-transaction` e budget.

Autocritica: isso ainda nao otimiza o algoritmo pesado nem substitui leitura de contexto. A melhoria e operacional: antes de commit/checkpoint, a frente deve gerar o plano por path, ler o diff real, rodar os checks indicados com `--timings` e escalar para heavy completo quando o path tocar cobertura protegida.

## 2026-06-15 - Refino trabalhista desloca topo prazo urgente para negativa formal

Decisao: adicionar regressao focada para `horas-extras-nao-pagas` versus `verbas-rescisorias-nao-pagas` em `prazo-urgente/prazo-sete-dias` e especializar o gerador com secoes materiais sobre jornada, intervalo, habitualidade, controle de ponto, TRCT, aviso e rubricas finais.

Motivo: o topo vivo do ciclo anterior ainda confundia prova de labor extra com acerto rescisorio. A similaridade `0.6688` indicava que o texto diferia por substituicoes trabalhistas, mas mantinha estrutura de urgencia muito intercambiavel.

Consequencia: apos regenerar a cadeia bloqueada, `authorial_mass_similarity_report` ficou com `max_body_similarity=0.6731`; `authorial_mass_refinement_quality_report` manteve 81 registros e 13.090.690 comparacoes por grupos, com `max_body_similarity=0.6683`, 2.358 pares de alto risco e fila semantica zero; `authorial_mass_shard_refinement_plan` ficou com 100 planos, 10.000 conteudos, 2.566 eventos top-k, 706 eventos top-k de alto risco e prioridade no shard `authorial-mass-scale-shard-002`. O novo topo continua no cluster trabalhista, agora em `horas-extras-nao-pagas` versus `verbas-rescisorias-nao-pagas` em `negativa-formal/prazo-sete-dias`.

Autocritica: a melhoria reduziu risco sem relaxar threshold, mas deslocou o gargalo dentro do mesmo cluster. A proxima macrocamada deve atacar `negativa-formal/prazo-sete-dias`, resolver fonte oficial especifica trabalhista por seed e manter readiness/release como ensaio bloqueado ate aprovacao publica real.

## 2026-06-15 - Refino autoral derruba o topo acidente/aposentadoria

Decisao: adicionar regressao focada para o par `acidente-trabalho-indenizacao` versus `aposentadoria-especial-negada` em `prazo-urgente/prazo-sete-dias` e especializar abertura urgente, memoria tematica e rotulo curto dos 300 rascunhos massivos.

Motivo: o relatorio de refino apontava similaridade `0.6774` entre indenizacao por acidente de trabalho e aposentadoria especial negada. O risco nao era abstrato: ambos ainda usavam cronologia de urgencia intercambiavel, apesar de um tema depender de evento laboral, CAT, prontuario, nexo e dano, e o outro depender de indeferimento INSS, PPP, LTCAT, CNIS, agente nocivo e prova tecnica.

Consequencia: apos regenerar a cadeia bloqueada, `authorial_mass_similarity_report` caiu para `max_body_similarity=0.6749`; `authorial_mass_refinement_quality_report` ficou com 81 registros, 13.090.690 comparacoes por grupos, `max_body_similarity=0.6688`, 2.441 pares de alto risco e fila semantica zero; `authorial_mass_shard_refinement_plan` ficou com 100 planos, 10.000 conteudos, 2.568 eventos top-k, 715 eventos top-k de alto risco e prioridade no shard `authorial-mass-scale-shard-002`. O novo topo e `horas-extras-nao-pagas` versus `verbas-rescisorias-nao-pagas` em `prazo-urgente/prazo-sete-dias`.

Autocritica: a mudanca melhora diferenciacao material, mas ainda nao publica nada e nao resolve fonte final, revisao OAB, paid-intent/CTA publico, HTML publico ou `published_manifest`. A proxima macrocamada deve atacar o cluster trabalhista horas extras/verbas rescisorias com novo RED/GREEN, recalculo de relatorio e plano de shards, mantendo publicacao zero ate gate completo.

## 2026-06-15 - Ledger de performance torna validação proporcional obrigatória

Decisao: criar `ops_check_performance_ledger` como camada operacional bloqueada para todos os checks registrados em `checks.Names`, com classe de custo, comando `--timings`, gatilho proporcional e regra executável de que contrato pesado não entra em `always_run`.

Motivo: o projeto ja tem checks que varrem massa grande, como `authorial-mass-refinement-quality-report`; rodar esses contratos por hábito em todo checkpoint cria gargalo de escala. A cobertura não pode cair, então a decisão é registrar quando rodar pesado e usar checks focados/shards quando a frente não tocar corpo, fonte, CTA, algoritmo ou publicação.

Consequencia: o estado vivo agora tem `checks=123`, `heavy=5`, `medium=28`, `fast=90`, `always_run=118` e `publication_allowed=0` depois da otimização por fingerprint, da integração comercial P0 e das integrações Codex 2. `storage-contract`, `ops-check-performance-ledger`, `ops-check-selection-profiles`, `authorial-mass-contextual-compatibility` e `authorial-mass-refinement-quality-report` ficam rodáveis por classe proporcional; a regeneração completa do relatório de refino continua pesada e só roda por stale real.

Autocritica: isso não acelera o algoritmo pesado por si só. A camada remove falso dever de rodar tudo sempre e cria base permanente para a próxima macrocamada de otimização real: cache incremental, sharding de checks ou execução seletiva com evidência de cobertura.

## 2026-06-15 - Plano de continuidade por shard prioriza refino dos 10k

Decisao: criar `authorial_mass_shard_refinement_plan` como camada bloqueada que consome `authorial_mass_scale_shards` e `authorial_mass_refinement_quality_report`, ranqueia os 100 shards da massa 10k por risco top-k e materializa comandos por shard para refino/fonte/revisao.

Motivo: registrar apenas que o ledger existe deixava continuidade solta. O P0 precisa de proximo comando executavel em escala real: abrir o shard prioritario, atacar os pares top-k, resolver fonte especifica e repetir os checks proporcionais antes de qualquer readiness/release publico.

Consequencia: o estado vivo tem `plans=100`, `contents=10000`, `observed_top_pairs=2566`, `high_risk_top_pairs=706`, `max_similarity=0.6683`, prioridade no shard `authorial-mass-scale-shard-002` e `publication_allowed=0`. A amostragem do plano guarda top-k por score para expor o par que justificou a prioridade, nao os primeiros pares encontrados.

Autocritica: o plano ainda nao reescreve os pares nem resolve fonte final. Ele elimina passividade de checkpoint e transforma a continuidade em fila operavel; a proxima macrocamada deve aplicar refino real no shard prioritario e recalcular `authorial_mass_refinement_quality_report`.

## 2026-06-15 - Ledger de escala cobre 10k conteudos em shards reais

Decisao: criar `authorial_mass_scale_shards` como ledger bloqueado de 100 shards sobre os 10.000 conteudos autorais massivos, consumindo `authorialmassstock` sem alterar os 300 rascunhos nem os 9.700 conteudos de expansao.

Motivo: 27 seeds ou 27 locks de fonte nao sao alta escala operacional. A escala real do P0 esta nos 10.000 conteudos bloqueados, nos 12.960 candidatos/oportunidades e nos checks que precisam rodar proporcionalmente sem perder cobertura. O ledger transforma o estoque 300+9.700 em fatias de 100 registros com cobertura, diversidade, comandos de perfil e flags publicas fechadas.

Consequencia: o estado vivo tem `shards=100`, `contents=10000`, `shard_size=100`, `drafts=300`, `expansions=9700`, `publication_allowed=0` e maior linha JSONL abaixo do limite de storage. A primeira tentativa de 40 shards de 250 registros falhou corretamente no `storage-contract` por `jsonl_record_too_large`; a correcao para 100 shards preservou cobertura e reduziu o maior registro para cerca de 15 KB.

Autocritica: o ledger nao refina texto por si so e nao reduz o deficit publico. Ele remove gargalo operacional de escala e cria unidade proporcional para os proximos gates: fonte especifica, revisao juridico-editorial, anti-duplicidade, readiness/release e publicacao controlada.

## 2026-06-15 - Codex 2 seleciona candidatos oficiais para rechecagem de especificidade

Decisao: criar `codex2_source_specificity_recheck` como camada bloqueada que consome `codex2_source_candidate_pack`, calcula score metadata-only e seleciona os melhores candidatos oficiais por seed/matriz para rechecagem de fonte.

Motivo: o pacote de candidatos tinha 732 referências, mas não separava o que deveria ser rechecado primeiro. A nova camada transforma esse volume em 209 candidatos selecionados para rechecagem em 27 seeds, sem fingir que candidato virou fonte final e sem entrar na frente autoral/refino do outro Codex.

Consequencia: o estado vivo tem `records=27`, `tasks=4800`, `matrix_groups=7`, `selected_candidates=209`, `publication_allowed=0`, `raw_text_stored=false`, `scraping_allowed=false`, `ingestion_allowed=false`, `render_allowed=false` e `sitemap_allowed=false`. A próxima frente deve travar fonte final por seed/URL com validação de especificidade e só depois recalcular readiness/release derivado.

Autocritica: a camada reduz ruído e prioriza rechecagem, mas ainda não prova fonte oficial final nem autoriza conteúdo público. O score é heurístico e metadata-only; quando uma URL for escolhida como fonte final, ela ainda precisa de auditoria jurídica/editorial e gates públicos.

## 2026-06-15 - Codex 2 cria pacote macro de candidatos oficiais sem publicar

Decisao: criar `codex2_source_candidate_pack` como camada bloqueada que agrega as 4.800 tarefas de fonte por 27 seeds e 7 grupos da matriz, anexando candidatos oficiais de `priority_source_urls`, `batch_source_matrix`, `batch_source_urls` e da fila atual para rechecagem metadata-only.

Motivo: a matriz de 7 grupos reduzia o problema, mas ainda deixava a próxima execução sem um workpack seed-level acionável. A nova camada transforma a frente Fonte 4.800 em pacote massivo independente do refino autoral do outro Codex, mantendo branch/worktree Codex 2, catálogos locais e proibição de scraping, cópia de texto, render, sitemap e publicação.

Consequencia: o estado vivo tem `seed_packs=27`, `tasks=4800`, `matrix_groups=7`, `candidate_refs=732`, `candidate_hosts=8`, `publication_allowed=0`, `raw_text_stored=false`, `scraping_allowed=false` e `ingestion_allowed=false`. Candidato oficial não é fonte final resolvida; a próxima frente deve reexecutar especificidade por seed/matriz, recalcular camadas derivadas quando a fonte mudar e manter `published_manifest=0` até gate completo.

Autocritica: a camada melhora escala e coordenação, mas não reduz o déficit público por si só. O check transversal `internal/checks` levou 76.084s e 78.323s durante a rodada Codex 2, então alta escala agora pede shard/cache/incrementalidade dos checks pesados sem cortar cobertura, junto com rechecagem de fonte e refino semântico antes de qualquer release público.

## 2026-06-15 - Codex 2 integra fronteira e fila de auditoria de fonte sem merge cego

Decisao: integrar manualmente ao `main` as camadas Codex 2 `codex2_source_frontier` e `codex2_source_audit_queue`, preservando a evolução simultânea de `authorial_mass_refinement_quality_report` e editando arquivos compartilhados para frente em vez de fazer merge/cherry-pick cego da branch antiga.

Motivo: a branch Codex 2 continha trabalho útil para uma macrocamada independente de fonte oficial, mas estava atrás do `main` e uma integração cega apagaria evolução recente. A solução segura foi copiar apenas arquivos próprios ausentes, registrar as camadas em storage/checks, adicionar pass lines no `cmd/check`, manter os edits de refino massivo do outro Codex e combinar otimização de performance sem remover validações existentes.

Consequencia: o estado vivo atual tem `codex2_source_frontier=120` com 4.800 oportunidades selecionadas e `codex2_source_audit_queue=4800`, sendo 3.930 tarefas para fonte oficial mais específica e 870 para verificar metadado oficial existente. As camadas vivem em `data/research`, são metadata-only, mantêm scraping/ingestão/render/sitemap/publicação fechados e não alteram `public/`, `content/pages.json`, `published_manifest` ou sitemap real.

## 2026-06-15 - Codex 2 consolida fila de fonte em matriz de resolucao bloqueada

Decisao: criar `codex2_source_resolution_matrix` como camada bloqueada que agrega `codex2_source_audit_queue` por host oficial, perfil de caminho e decisao, com check `codex2-source-resolution-matrix` e comandos metadata-only.

Motivo: a fila de 4.800 tarefas precisava virar trabalho macro e deduplicado sem misturar com a frente autoral do outro Codex. A matriz permite atacar grupos de fonte oficial e preservar contexto de coordenação sem publicar, raspar, ingerir texto, renderizar ou alterar manifesto.

Consequencia: o estado vivo atual da matriz tem 7 grupos, 4 hosts, 4.800 tarefas cobertas, 3.930 tarefas ainda exigindo fonte oficial mais específica, 870 verificações de metadado existente e `publication_allowed=0`. Arquivos compartilhados devem continuar sendo integrados por forward-edit: Codex 2 lê o arquivo vivo, preserva evolução concorrente e registra overlap, sem merge cego nem rollback.

## 2026-06-15 - Relatorio de refino audita os 10k bloqueados antes da promocao

Decisao: criar `authorial_mass_refinement_quality_report` como camada bloqueada sobre os dois estoques autorais massivos: 300 `authorial_mass_drafts` e 9.700 `authorial_mass_content_expansion`. O relatório usa Jaccard de 4-gramas com top-k bounded por seed, area, cenario e contexto, mais `group_rollup` declarado como nao all-pairs global, para transformar risco de template/duplicacao semantica em fila executavel de refino antes de qualquer readiness/release dos 9.700.

Motivo: o ciclo anterior fechou 10.000 conteudos bloqueados, mas publicar ou promover readiness por contador seria falso verde. A massa completa ainda precisava de auditoria em lote sem estourar memoria nem materializar todos os pares. O algoritmo novo compara grupos explicaveis, preserva apenas os 20 piores pares por grupo e mantem flags publicas fechadas, permitindo que a proxima macrocamada ataque os clusters dominantes em vez de repetir diagnostico ou tentar validar todos os contratos sem necessidade.

Consequencia: foram criados `internal/authorialmassstock`, `internal/authorialmassrefinementquality`, `cmd/generate-authorial-mass-refinement-quality-report`, wrappers de geração/check, teste contratual, storage/check registry e `data/editorial/authorial_mass_refinement_quality_report.jsonl`. O estado vivo apos refino seed/cenario/contexto e dos 300 rascunhos iniciais tem 81 relatórios, 13.090.690 comparações por grupos, `max_body_similarity=0.6683`, 2.358 pares de alto risco e 0 pares semânticos acima de `0.70`, com maior risco atual em `horas-extras-nao-pagas` versus `verbas-rescisorias-nao-pagas` em `negativa-formal/prazo-sete-dias`. O `group_rollup` tem `global_all_pairs_compared=false`, `pair_count_policy=sum_of_group_pair_events_pairs_can_repeat_across_dimensions` e `requires_cross_group_blocking_audit=true`, então não pode ser lido como auditoria global de todos os pares. A camada vive em `data/editorial`, `noindex`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""` e não toca `public/`, `content/pages.json`, `published_manifest` ou sitemap real.

Autocritica: a mudança é segura porque não abre publicação e expõe risco real que impediria promoção fraca. É otimização real porque usa auditoria de grupos com top-k bounded e declara explicitamente que não executou all-pairs global; isso evita falso verde e ainda exige reescrita/refino material. O score 0.6683 e a fila semântica zero não podem ser tratados como aprovação pública, porque ainda existem 2.358 pares de alto risco, fonte específica pendente nos 9.700, revisão jurídica/OAB, paid-intent/CTA ou bloqueio informativo e release gate. A próxima evidência deve refinar os top pairs de alto risco restantes, recalcular o relatório, manter auditoria cross-group bloqueada quando o risco exigir, resolver fonte específica e só então promover para readiness/release.

## 2026-06-15 - Estoque autoral 10k fecha antes do refino publico

Decisao: manter `authorial_mass_drafts` em 300 rascunhos refinados que ja alimentam similarity/readiness/release, e criar `authorial_mass_content_expansion` com 9.700 conteudos autorais bloqueados para os candidatos ranks 301-10.000. A soma dos 300 rascunhos refinados com os 9.700 conteudos de expansao fecha 10.000 conteudos bloqueados para refino, sem declarar paginas publicas, sem abrir `published_manifest`, sem tocar `content/pages.json`, `public/` ou sitemap real.

Motivo: tres auditorias read-only convergiram que mudar o pipeline principal direto para 10.000 acionaria similarity e derivados ainda dimensionados para 300, com custo O(n²), contadores fixos e risco de falso negativo/falso positivo. O pedido atual era focar primeiro no deficit de conteudo e depois no refino. A camada separada reduz o deficit de estoque autoral sem forcar release prematuro nem mascarar candidato como conteudo.

Consequencia: `./tools/generate-authorial-mass-content-expansion` e `./tools/check-authorial-mass-content-expansion` passam a ser comandos oficiais; `content/storage_contract.json`, `internal/storage` e `internal/checks` exigem a camada permanente. O proximo P0 deve refinar essa massa em shards, endurecer anti-template/similaridade com estrategia subquadratica ou top-k auditavel, resolver fonte especifica e revisar paid-intent/CTA antes de promover os 9.700 para readiness/release. `published_manifest` permanece zero e a meta publica de 10.000 paginas juridicas indexaveis continua aberta.

Autocritica: a mudanca e segura porque produz conteudo bloqueado, com fonte esperada, observacoes externas metadata-only, CTA online bloqueado e flags publicas falsas. Ela nao prova qualidade final, similaridade semantica, revisao juridica, HTML leve ou indexacao. O risco residual e a expansao compacta ainda precisar de refinamento pesado para evitar thin/template; por isso o contrato exige que a proxima camada trate refino e algoritmo antes de qualquer publicacao.

## 2026-06-15 — Promoção controlada massiva bloqueada prova staging sem publicar

Decisao: criar `authorial_mass_controlled_promotion_rehearsal` como camada agregada depois de `authorial_mass_manifest_transaction_rehearsal`, consumindo o `publicrelease.TransactionPlan` massivo e ensaiando staging, espelho temporário, smoke HTTP/Googlebot, swap bloqueado, lock, ledger e rollback fora do workspace público real.

Motivo: o manifesto massivo provava o plano em memória para elegíveis bloqueados, mas ainda não exercitava a mecânica de staging/promoção que antecede qualquer escrita pública. Pular direto para `published_manifest` converteria registros `approval=false` em páginas indexáveis sem autorização final.

Consequencia: foram criados `internal/authorialmasscontrolledpromotion`, `cmd/generate-authorial-mass-controlled-promotion`, wrappers de geração/check, contrato focado, storage/check registry e `data/editorial/authorial_mass_controlled_promotion_rehearsal.jsonl`. O estado vivo atual tem 1 registro agregado, `source_transaction_record_count=10000`, `manifest_record_count=5355`, `paid_blocked_count=4645`, `temporary_http_smoke_passed=true`, `promotion_swap_blocked_by_default=true`, `promotion_ledger_record_count=2` e `publication_allowed=0`.

Autocrítica: essa camada ainda não cria página pública indexável. Ela remove uma lacuna técnica de promoção controlada, mas os próximos gates para reduzir o déficit público exigem aprovação final explícita, suporte de manifesto publicado para release massivo aprovado, rechecagem de fonte/duplicidade/thin content e execução pública transacional com rollback real.

## 2026-06-15 — Transação de manifesto massiva bloqueada valida plano sem publicar

Decisao: criar `authorial_mass_manifest_transaction_rehearsal` como gate 1:1 das transações HTTP massivas, antes de qualquer staging real, swap, sitemap público ou escrita em `published_manifest`.

Motivo: a transação HTTP massiva provava rota isolada, robots e sitemap de ensaio, mas ainda não validava o plano agregado de `published_manifest`, `content/pages`, HTML e sitemap com o corpo autoral real dos rascunhos massivos. Chamar HTTP isolado de manifesto pronto seria falso verde.

Consequencia: foram criados `internal/authorialmassmanifesttransaction`, `cmd/generate-authorial-mass-manifest-transaction`, wrappers de geração/check, contrato focado e camada `data/editorial/authorial_mass_manifest_transaction_rehearsal.jsonl`. O estado vivo atual tem 10.000 registros bloqueados, 5.355 incluídos no plano, 4.645 paid-blocked, `manifest_record_count=5355`, `content_page_count=5355`, `html_artifact_count=5355`, `sitemap_artifact_count=1` e `publication_allowed=0`. `content/storage_contract.json`, `internal/storage` e `internal/checks` conhecem a camada.

Autocrítica: transação de manifesto massiva bloqueada não é `published_manifest`, não é staging real, não é sitemap real, não é aprovação final e não é página indexável. Ela aproxima o lote da mecânica pública sem materializar nada; o próximo avanço deve ser promoção controlada/revisão final pública quando todos os gates permitirem ou expansão de demanda/conteúdo autoral de alta intenção com cadeia completa.

## 2026-06-15 — Codex 2 amplia plano de coleta externa para 4.800 oportunidades bloqueadas

Decisao: preservar a evolução Codex 2 que aumenta `codex2_mass_scale_plan` e `codex2_external_collection_wave` para 60 shards de 80 oportunidades, adiciona `--exhaust-selected-opportunities` ao coletor e amplia recovery por superfície para 1.000 oportunidades.

Motivo: a cobertura externa ainda é inicial e o projeto não pode crescer para 10k+ tratando dados locais como mercado. A mudança remove o gargalo de microcoleta, mas mantém cada superfície como requisito executável e mantém tentativa sem registros fora do ranking editorial.

Consequencia: `data/research/codex2_mass_scale_plan.jsonl` e `data/research/codex2_external_collection_wave.jsonl` agora têm 60 registros cada; `cmd/collect-demand-observations` aceita `--exhaust-selected-opportunities`; os testes Codex 2 exigem macro floor de 4.800 oportunidades e comandos com recovery amplo. As camadas seguem bloqueadas, metadata-only/planejamento, sem render, sitemap, `content/pages.json`, `published_manifest` ou publicação.

Autocrítica: wave planejada não é demanda capturada, não é briefing e não autoriza conteúdo público. Cada shard ainda precisa ser operado com política de superfície, tentativa versionada, validação de observação/amostra e recálculo das camadas derivadas quando houver novos metadados aceitos.

## 2026-06-14 — Transação HTTP massiva bloqueada prova rota sem publicar

Decisao: criar `authorial_mass_release_transaction_evidence` como gate 1:1 das evidências de release massivas, antes de qualquer manifesto real, sitemap público, `.release-staging` real ou escrita em `public/`.

Motivo: a release evidence massiva provava HTML leve em memória, canonical e smoke Googlebot para os elegíveis, mas ainda não provava resposta HTTP isolada com rota candidata, robots, sitemap de ensaio, content-type e ausência verificável nos artefatos públicos reais. Chamar isso de publicação ou repetir o smoke anterior seria falso verde.

Consequencia: foram criados `internal/authorialmassreleasetransaction`, `cmd/generate-authorial-mass-release-transaction`, wrappers de geração/check, contrato focado e camada `data/editorial/authorial_mass_release_transaction_evidence.jsonl`. O estado vivo atual tem 10.000 registros bloqueados, `http_smoke=10000`, `paid_blocked=4645` e `publication_allowed=0`. `content/storage_contract.json`, `internal/storage` e `internal/checks` conhecem a camada.

Autocrítica: transação HTTP massiva bloqueada não é manifesto publicado, sitemap real, rota pública, staging real, aprovação final ou página indexável. A próxima macrocamada deve avançar manifesto/transação agregada bloqueada ou ampliar conteúdo/fonte/demanda externa de alta intenção; `public/`, `content/pages.json`, `published_manifest` e sitemap real continuam intocados.

## 2026-06-14 — Release evidence massiva bloqueada mede HTML/Googlebot sem publicar

Decisao: criar `authorial_mass_release_evidence` como gate 1:1 das revisões jurídico-editoriais massivas, antes de qualquer HTTP transacional, plano de manifesto, sitemap real ou escrita pública.

Motivo: as revisões massivas versionavam OAB, fonte, paid-intent e fixes, mas ainda não provavam HTML leve, canonical oficial, robots noindex/follow, hash recalculável e smoke Googlebot. A evidência precisava ser em memória e bloqueada, para não confundir rota candidata com página pública.

Consequencia: foram criados `internal/authorialmassreleaseevidence`, `cmd/generate-authorial-mass-release-evidence`, wrappers de geração/check, contrato focado e camada `data/editorial/authorial_mass_release_evidence.jsonl`. O estado vivo atual tem 10.000 registros bloqueados, `googlebot_smoke=5355`, `paid_blocked=4645`, `max_html_bytes=31056` e `publication_allowed=0`. `content/storage_contract.json`, `internal/storage` e `internal/checks` conhecem a camada.

Autocrítica: release evidence massiva não é rota pública, HTTP transacional, plano de manifesto, `published_manifest`, sitemap real ou aprovação final. A próxima macrocamada deve produzir HTTP/manifest transaction bloqueada ou coordenar integração da frente Codex 2 sem misturar commits; `public/`, `content/pages.json`, `published_manifest` e sitemap real continuam intocados.

## 2026-06-14 — Revisão jurídico-editorial massiva bloqueada consome a readiness

Decisao: criar `authorial_mass_legal_editorial_reviews` como gate 1:1 dos registros de `authorial_mass_publication_readiness`, antes de qualquer release evidence, manifesto, HTML público ou sitemap.

Motivo: a readiness massiva reunia fonte, paid-intent, search e anti-template, mas ainda não versionava a revisão jurídico-editorial/OAB da massa. Repetir readiness seria passividade; publicar sem revisão em massa seria falso verde. A nova camada grava identidade OAB de `content/site.json`, CTA interno contextual ou bloqueio explícito, notas e fixes obrigatórios sem abrir flags públicas.

Consequencia: foram criados `internal/authorialmasslegalreviews`, `cmd/generate-authorial-mass-legal-reviews`, wrappers de geração/check, contrato focado e camada `data/editorial/authorial_mass_legal_editorial_reviews.jsonl`. O estado vivo atual tem 10.000 registros bloqueados, `source_locked=10000`, `paid_blocked=4645`, `identity_from_config=10000` e `publication_allowed=0`. `content/storage_contract.json`, `internal/storage` e `internal/checks` conhecem a camada.

Autocrítica: revisão massiva bloqueada não é aprovação final, não é release evidence, não é transação de manifesto e não é publicação. A próxima macrocamada deve produzir release evidence/HTTP/manifest transaction bloqueados ou ampliar evidência externa multifonte; `public/`, `content/pages.json`, `published_manifest` e sitemap real continuam intocados.

## 2026-06-14 — Readiness massiva bloqueada liga o estoque autoral a fonte, paid-intent e revisão

Decisao: criar `authorial_mass_publication_readiness` como gate 1:1 do estoque autoral massivo, antes de qualquer HTML, manifesto ou sitemap público.

Motivo: zerar `authorial_mass_similarity_semantic_reviews` removia o blocker semântico acima de `0.70`, mas ainda deixava o lote massivo sem camada própria que cruzasse fonte oficial específica, paid-intent/CTA ou bloqueio informativo, search appearance, anti-template e revisão jurídico-editorial/OAB. Repetir o relatório de similaridade seria passividade; avançar para publicação sem readiness seria falso verde.

Consequencia: foram criados `internal/authorialmassreadiness`, `cmd/generate-authorial-mass-publication-readiness`, wrappers de geração/check, contrato focado e camada `data/editorial/authorial_mass_publication_readiness.jsonl`. O estado vivo atual tem 10.000 registros bloqueados, `source_locked=10000`, `paid_passed=5369`, `paid_blocked=4631`, `search_ready=6633`, `anti_template_ready=9953`, `anti_template_blocked=47`, `legal_review_required=10000`, `codex_review_ready=1494`, `max_body_similarity=0.6837`, `global_similarity_max=0.6627` e `publication_allowed=0`. `content/storage_contract.json`, `internal/storage` e `internal/checks` conhecem a camada.

Autocrítica: readiness massiva não é revisão OAB final, não é release evidence, não é transação de manifesto e não é publicação. O próximo avanço deve produzir fonte final/revisão/release evidence/manifests bloqueados ou ampliar evidência externa multifonte; `public/`, `content/pages.json`, `published_manifest` e sitemap real continuam intocados.

## 2026-06-14 — Matriz anti-template zera fila semântica massiva 0.70+

Decisao: o gerador massivo passa a combinar matriz anti-template por intenção/cenário/contexto/problema humano com narrativas próprias por seed e contexto, e o contrato aceita `authorial_mass_similarity_semantic_reviews=0` quando nenhum par permanece acima de `0.70`.

Motivo: após o ciclo anterior, a fila tinha 74 revisões e pico `0.7393`. Os remanescentes concentravam-se em temas próximos de plano de saúde, INSS, família e previdenciário, muitos ainda usando narrativa temática default. Reduzir o limiar seria falso verde; a correção correta era adicionar diferenciação autoral material.

Consequencia: `authorial_mass_similarity_report` continua com 37 relatórios bloqueados, mas `max_body_similarity` caiu para `0.6731`, abaixo do limiar semântico. `authorial_mass_similarity_semantic_reviews` caiu para 0 registros, `rewrite_required=0`, publicação zero e nenhuma escrita em `public/`, `content/pages.json`, `published_manifest` ou sitemap real. O teste `TestAuthorialMassSemanticReviewQueueKeepsShrinkingWithMatrixEvidence` impede aceitar novamente fila ampla ou pico acima de `0.725`.

Autocrítica: zerar a fila semântica não transforma os 300 rascunhos em páginas públicas. Ainda faltam fonte específica final, revisão jurídico-editorial/OAB, paid-intent/CTA ou bloqueio informativo, HTML leve, canonical/robots/sitemap, smoke de bot, plano/transação de manifesto e release gate completo antes de qualquer publicação.

## 2026-06-14 — Refino autoral reduz fila semântica massiva sem publicar

Decisao: `./tools/generate-authorial-mass-drafts` passa a diferenciar o lote 300 por cenário, contexto e tema com ângulos editoriais próprios, e o contrato passa a exigir que a fila de `authorial_mass_similarity_semantic_reviews` encolha materialmente antes de nova expansão.

Motivo: a camada semântica anterior materializou 118 pares acima de `0.70` e pico `0.7731`. Isso era fila útil, mas repetir o mesmo relatório seria passividade. A causa viva era repetição de seções entre cenários iguais, contextos parecidos e temas da mesma área; a correção precisava alterar corpo autoral real, não relaxar limiar.

Consequencia: naquele ciclo, o relatório massivo recalculado continuou com 38 registros bloqueados, mas `max_body_similarity` caiu para `0.7393`. `authorial_mass_similarity_semantic_reviews` caiu de 118 para 74 registros, com `rewrite_required=67`, flags públicas fechadas e nenhuma escrita em `public/`, `content/pages.json`, `published_manifest` ou sitemap real. O teste `TestAuthorialMassSemanticReviewQueueShrinksAfterMaterialRefinement` impede voltar a aceitar fila grande sem refino material.

Autocrítica: 74 revisões semânticas ainda são blocker P0. A camada prova redução de template, não página premium nem autorização de publicação. A próxima macrocamada deve reduzir os remanescentes por nova diferenciação autoral, fonte específica final, evidência externa multifonte ou preparar promoção pública somente quando todos os gates finais estiverem comprovados.

## 2026-06-14 — Revisões semânticas massivas materializam o blocker remanescente

Decisao: `authorial_mass_similarity_semantic_reviews` passa a ser a camada bloqueada que transforma pares massivos acima de `0.70` em ação editorial antes de expansão ou publicação.

Motivo: depois do refino anti-template, o relatório caiu para `max_body_similarity=0.7731`, mas ainda havia risco material nos piores pares. Repetir o relatório ou chamar `0.7731` de aprovação seria falso verde; a operação precisava criar fila versionada de reescrita/refino com contraste de documento, fonte, risco humano e decisão editorial.

Consequencia: foram criados `internal/authorialmasssemanticreviews`, `cmd/generate-authorial-mass-similarity-semantic-reviews`, wrappers de geração/check, storage contract e check `authorial-mass-similarity-semantic-reviews`. Naquele ciclo, a camada tinha 118 revisões bloqueadas, `rewrite_required=118`, `max_body_similarity=0.7731`, flags públicas fechadas e nenhuma escrita em `public/`, `content/pages.json`, `published_manifest` ou sitemap real.

Autocrítica: a camada não reescreve texto e não reduz o risco sozinha. Ela torna o próximo trabalho mais objetivo: reduzir os 118 pares por reescrita autoral substantiva, fonte específica final, valor informacional e recálculo da cadeia, mantendo publicação bloqueada até release gate completo.

## 2026-06-14 — Configuração histórica de concorrência de subagentes fica explícita

Decisao: `.codex/config.toml` passou a declarar `[agents] max_threads = 12` para o projeto `/opt/wiki` como configuração histórica de concorrência da época, não como teto contratual vigente de agentes do `/goal`.

Motivo: o ciclo P0 tentou abrir três auditores read-only e recebeu `collab spawn failed: agent thread limit reached`. A investigação com o manual atual do Codex mostrou que `agents.max_threads` fica em 6 quando não configurado, e o contexto da sessão já tinha seis threads antigas abertas. Isso não era regra jurídica do projeto, bloqueio do usuário, sandbox ou negação de permissão; era cap operacional padrão combinado com threads concluídas ainda abertas.

Consequencia historica: as seis threads antigas foram fechadas, três novos subagentes read-only abriram corretamente, e o projeto documentou uma configuração de concorrência maior para aquele ciclo P0 complexo. A regra posterior de contagem fixa virou registro historico substituido pela politica proporcional vigente: todo ciclo novo do `/goal` exige decisao explicita de delegacao proporcional, sem teto operacional artificial quando houver frentes independentes reais. Subagente continua subordinado a escopo, ledger, fechamento antes de checkpoint ou preservação explícita de contexto para agente concluído/integrado, e validação do Codex principal; o ajuste histórico não autoriza fan-out recursivo, publicação, escrita delegada sem validação ou omissão de gates.

Autocrítica: aumentar configuração histórica de concorrência não remove custo de tokens, latência nem necessidade de fechar agentes concluídos. Se uma sessão futura ainda falhar mesmo com agentes concluídos fechados, o blocker passa a ser runtime externo do Codex e deve ser registrado com evidência depois de reorientação ou relançamento ativo, não tratado como política do repo nem usado para reduzir a obrigação proporcional de paralelizar frentes independentes reais.

## 2026-06-14 — Refino anti-template massivo reduz similaridade sem liberar publicação

Decisao: `./tools/generate-authorial-mass-drafts` passa a gerar o lote 300 com perfis editoriais por seed, cenário e contexto, variando documentos, risco, fonte esperada, triagem digital e CTA antes de recalcular `authorial_mass_similarity_report`.

Motivo: o relatório anti-template dos 300 rascunhos massivos expôs `max_body_similarity=0.8770`, alto demais para ampliar lote ou preparar publicação. O problema não era falta de volume, mas repetição estrutural entre rascunhos juridicamente próximos; trocar palavras seria cosmético e manteria risco de template.

Consequencia: naquele ciclo, o relatório caiu para `max_body_similarity=0.7731`, com 37 relatórios bloqueados e publicação zero. O teste contratual passou a reprovar similaridade acima de `0.78` antes de expansão, e os rascunhos continuaram `noindex`, sem render, sem sitemap, sem `public_path` e sem `published_manifest`.

Autocrítica: `0.7731` ainda é blocker de qualidade, não aprovação editorial. O próximo avanço deve criar revisão semântica/valor informacional dos piores pares, ampliar refino por fonte específica final ou operar nova coleta externa multifonte antes de qualquer HTML público ou manifesto real.

## 2026-06-14 — Seleção 10k bloqueada materializa o plano sem chamar candidato de página

Decisao: `authorial_mass_generation_plan` passa a ser operado por `data/editorial/authorial_mass_candidate_selection.jsonl`, gerado por `./tools/generate-authorial-mass-candidate-selection` e validado por `authorial-mass-candidate-selection`.

Motivo: o `/goal` exige chegar a 10.000 páginas públicas aprovadas, mas publicar sem gate seria spam. A camada correta agora é selecionar exatamente 10.000 candidatos bloqueados para o déficit atual, usando oportunidades, batch 2.220, readiness e política ROI/web/100% digital sem tocar `published_manifest`.

Consequencia: o repo tem 10.000 candidatos únicos e diversos, com `index_policy=noindex`, manifest/content pages fechados e `publication_allowed=false`. Essa camada ainda exige coleta externa/refino, rascunho autoral, fonte específica, revisão, paid-intent ou lane informativa, HTML leve e release gate antes de qualquer página pública.

Autocrítica: a seleção 10k cobre volume operacional, não valida demanda externa 10k. A cobertura externa segue inicial/concentrada; o próximo avanço precisa operar coletores versionados ou gerar/refinar lotes bloqueados com evidência de qualidade antes de qualquer promoção.

## 2026-06-14 — Plano 10k vira artefato executável bloqueado

Decisao: a estratégia de gerar massa jurídica de alta intenção até 10k+ antes do refinamento final passa a ser materializada em `data/editorial/authorial_mass_generation_plan.jsonl`, com gerador `./tools/generate-authorial-mass-generation-plan` e check `authorial-mass-generation-plan`.

Motivo: o usuário pediu plano de expansão de geração de conteúdo jurídico de alta intenção contratual em massa, mirando ROI, 100% digital e valor informacional. Documentar a estratégia não bastava; o repo precisava calcular déficit, alvo bloqueado e insumos vivos para impedir plano passivo ou publicação fraca.

Consequencia: `internal/authorialmassplan` calcula `current_public=0`, `deficit=10000`, `target_blocked=12960`, `opportunities=12960`, `batch_archive=2220`, `authorial_readiness=27`, `priority_readiness=177`, política de pesquisa web/ROI quando faltarem termos e refinamento obrigatório antes de publicação. A camada fica sem render, sitemap, `published_manifest`, `public_path` ou publicação.

Autocrítica: plano executável ainda não é geração de 10k rascunhos. A próxima camada deve operar esse plano com seleção e geração de lote real, ou pesquisar web termos jurídicos de maior ROI quando os insumos atuais não cobrirem a expansão.

## 2026-06-14 — Readiness autoral geral exige paid-intent no corpo, não CTA-only

Decisao: a cadeia geral dos 27 rascunhos passa a ter `data/editorial/authorial_publication_readiness.jsonl`, gerada por `./tools/refresh-authorial-publication-readiness` e validada por `authorial-publication-readiness`. Antes dela, `./tools/refine-authorial-paid-intent-drafts` pode refinar rascunhos comerciais para inserir contratação particular, documentos, valor/protocolo e orçamento de honorários no corpo autoral. BPC/LOAS fica bloqueado como informativo/public assistance e não deve ser forçado para lane comercial.

Motivo: fonte, pré-publicação e revisão estavam 1:1, mas paid-intent ainda ficava ausente do corpo nos 26 temas comerciais. Isso criava risco de CTA-only, baixa intenção real e páginas futuras sem palavras-chave de contratação. Também havia falso positivo no classificador: "sem promessa de resultado, prazo, vantagem, gratuidade ou comparação" era tratado como oferta gratuita, embora seja regra ética de não prometer gratuidade.

Consequencia: foram criados `internal/authorialreadiness` e `internal/authorialpaidrefinement`, com comandos e wrappers. `internal/paidintent` agora ignora sinal de gratuidade em contexto de negação ética, preservando bloqueio real para advogado gratuito, consulta grátis, sem pagar e assistência pública. O estado vivo ficou `readiness=27`, `paid_passed=26`, `paid_blocked=1`, `search_ready=27`, `anti_template_ready=27` e `publication_allowed=0`.

Autocrítica: a mudança não publica página e não basta para o marco público. Ela remove falso bloqueio e melhora alta intenção nos textos comerciais, mas ainda faltam revisão final, fonte rechecada, release evidence, HTML leve, Googlebot, sitemap/canonical/robots e `published_manifest`. A próxima execução deve usar essa readiness como ponte para release bloqueado ou expansão maior, sem ignorar a base `batch_*` de 2.220.

## 2026-06-14 — Rascunho autoral geral cobre todo brief vivo antes de release

Decisao: `data/editorial/authorial_drafts.jsonl` deve ter um rascunho autoral bloqueado para cada registro vivo de `data/editorial/content_briefs.jsonl`. A geração fica em `./tools/generate-authorial-content-drafts`, preserva rascunhos curados válidos, regenera apenas os automáticos e reprova lacuna 1:1 por contrato. Rascunho autoral geral continua sem render, sitemap, `published_manifest`, `public_path` ou CTA público.

Motivo: após a expansão para 27 termos/briefs, a camada autoral geral ainda tinha só 6 rascunhos. Isso criava uma falsa ponte entre pesquisa e conteúdo: a base parecia maior, mas não havia texto autoral bloqueado para a maioria dos temas. A correção precisava respeitar o que já estava construído, não apagar rascunhos curados nem publicar por atalho.

Consequencia: `internal/authorialdrafts` ganhou gerador, escrita JSONL, preservação de curadoria, normalização de PT-BR acentuado para termos comuns e suporte a fonte oficial do BCB. `cmd/generate-authorial-content-drafts` e `tools/generate-authorial-content-drafts` materializam a camada. `internal/contract/authorial_content_drafts_test.go` agora exige contagem igual entre briefs e rascunhos, fonte por draft, ângulo único e publicação bloqueada. `authorial_drafts` subiu de 6 para 27 registros bloqueados.

Autocrítica: a mudança é segura porque não toca `public/`, `content/pages.json`, `published_manifest` ou sitemap real. É avanço real porque transforma pesquisa de alta intenção em texto autoral inicial, ainda bloqueado, e prepara a próxima esteira de fonte específica/revisão/paid-intent/SEO. Ainda não é conteúdo premium publicável: os rascunhos automáticos precisam de revisão jurídico-editorial, anti-template mais forte, fonte específica por tema e gates de release antes de qualquer URL pública.

## 2026-06-14 — API interna é motor de escala, não fonte única de descoberta

Decisao: a criação de conteúdo jurídico em escala passa a usar uma estratégia híbrida. Pesquisa web atual em fontes oficiais brasileiras, Google Trends como orientação direcional, sinais públicos permitidos e leitura editorial do problema humano escolhem palavras-chave de alta intenção de contratação. A API interna do repo é o motor para transformar essa pesquisa em sinais, briefs, oportunidades, checks, rastreabilidade e filas bloqueadas de escala. Coletor externo só conta como demanda quando produz observação ou amostra validável; tentativa sem registro vira diagnóstico bloqueado.

Motivo: o usuário corrigiu duas leituras ruins: os 2.220 candidatos já construídos não podem ser ignorados, mas também não são limite do projeto; e a API não pode virar gargalo ou fonte única se a pesquisa oficial do Codex puder escolher temas melhores. A operação focada nos 6 termos novos provou esse limite: a cadeia interna gerou 27 sinais, 27 briefs e 12.960 oportunidades, mas o Google autosuggest focado retornou `status_400` e zero observações externas. Isso não invalida a pesquisa de alta intenção; invalida tratar a API/coletor como oráculo.

Consequencia: `data/research/high_intent_terms.jsonl` tem 27 termos bloqueados, com 6 novos recortes em INSS/desconto associativo, Pix MED negado, cancelamento de plano por inadimplência, superendividamento, proteção de dados do consumidor e cartão consignado/RMC. `data/research/digital_demand_signals.jsonl`, `data/editorial/content_briefs.jsonl` e `data/research/demand_expansion_opportunities.jsonl` foram recalculados para 27, 27 e 12.960 registros. A tentativa Google autosuggest focada fica em `demand_surface_collection_attempts` como falha operacional bloqueada, não observação de demanda. README, `docs/DATA_SOURCES.md`, `docs/LAB_VALIDATION.md`, `GOAL.md` e `CHECKPOINT.md` registram a operação antes do commit.

Autocrítica: a decisão é segura porque não publica página, não toca `public/`, `content/pages.json`, `published_manifest` ou sitemap real, e mantém tudo em pesquisa/brief/oportunidade bloqueada. É otimização real porque aumenta o plano calculável rumo a 10k+ sem depender de uma única superfície. A validação ainda não prova mercado suficiente nem conteúdo público premium; a próxima prova material deve gerar rascunhos autorais ou páginas candidatas bloqueadas a partir dos briefs e/ou operar conector externo melhor, sempre com fonte oficial específica, revisão, paid-intent/CTA ético, anti-template, HTML leve e release gate.

## 2026-06-14 — Handoff P0 curto governa o próximo Codex

Decisao: os contratos passam a ter um handoff operacional curto para o próximo Codex. Antes de escolher qualquer frente, ele deve calcular `current_public_indexable_count` contando somente páginas jurídicas públicas aprovadas em `published_manifest`, calcular `deficit_to_10000 = max(0, 10000 - current_public_indexable_count)`, e atacar esse déficit em macrocamadas de conteúdo autoral, fonte oficial específica, revisão, paid-intent/CTA ou bloqueio explícito, SEO/crawl, HTML leve, Googlebot, sitemap/canonical/robots e release gate. A home institucional e qualquer rascunho, staging, manifesto bloqueado ou candidato interno não contam para a meta jurídica.

Motivo: o contrato permanente estava correto, mas longo e repetitivo. Isso protegia o `/goal`, mas podia desorientar o próximo Codex entre histórico, contadores duplicados e frases antigas sobre P0. O refinamento cria uma ordem curta sem remover a essência: P0 não passa para P1 enquanto o déficit até 10 mil páginas jurídicas públicas aprovadas for maior que zero ou enquanto houver risco de spam, thin content, duplicidade, fonte fraca, revisão pendente, CTA indevido ou HTML/crawl fraco.

Consequencia: `AGENTS.md`, `GOAL.md`, README, `docs/ROADMAP_P0_P5.md`, `docs/LAB_VALIDATION.md`, `docs/SEO_CRAWL_INDEXING.md` e `internal/contract/continuity_test.go` agora travam o handoff. `docs/SEO_CRAWL_INDEXING.md` deixou de carregar contadores stale 65/64/1 e passou a refletir 177 ensaios prioritários, 162 selecionados bloqueados, 8 paid-blocked, 7 source-blocked e `published_manifest=0`. O helper de checkpoint mais recente agora lê a seção mais nova no topo do arquivo, alinhado com a organização real de `CHECKPOINT.md`.

Autocrítica: a mudança é segura porque não publica página, não toca `public/`, `content/pages.json`, `published_manifest` ou sitemap real, e mantém os gates públicos fechados. É otimização real de coordenação: reduz loop documental e impede avançar para P1-P5 antes do marco P0. A validação prova o contrato e os checks vivos, mas não cria conteúdo público; a próxima evidência material deve operar conector/superfície de demanda ou ampliar conteúdo autoral bloqueado com fonte, revisão e release gate rumo ao déficit de 10 mil.

## 2026-06-13 — Amostras textuais externas ficam bloqueadas e autorais

Decisao: a coleta externa passa a distinguir observações metadata-only de amostras textuais curtas para análise editorial. A nova política permite trecho limitado somente em camada própria bloqueada, com origem, superfície, método, política de uso, hashes, deduplicação, vínculo com oportunidade/consulta e flags públicas falsas. A amostra serve para compreender linguagem real, risco de duplicidade e lacunas de utilidade antes de reescrita autoral; não pode compor página por cópia, substituir fonte oficial jurídica, gerar CTA público, alimentar `public/`, `content/pages.json`, `published_manifest`, sitemap real, render público ou `public_path`.

Motivo: expansão 10k+ precisa captar linguagem humana real sem transformar fonte externa em matéria-prima de clonagem. O contrato anterior protegia bem as camadas metadata-only, mas podia levar o próximo ciclo a escolher entre não observar texto algum ou registrar falha como relatório. A política nova cria uma trilha auditável e bloqueada para análise, mantendo a exigência de texto próprio, fonte oficial específica, revisão Codex principal, revisão jurídico-editorial/OAB e anti-duplicidade antes de qualquer página.

Consequencia: `internal/demandobservations`, `cmd/collect-demand-observations`, `content/storage_contract.json`, `internal/checks`, testes de contrato e `data/research/demand_content_samples.jsonl` materializam a camada bloqueada. O coletor aceita `--capture-content-samples`, `--require-content-samples`, `--max-content-sample-runes` e `--min-content-samples`, valida amostras em memória antes da escrita, normaliza HTML, rejeita amostra incompleta e mantém `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false` e `public_path=""`. `AGENTS.md`, `GOAL.md`, README, `docs/DATA_SOURCES.md`, `docs/LAB_VALIDATION.md` e `docs/ROADMAP_P0_P5.md` passam a exigir que falha de API/superfície vire reparo executável, adaptador, schema/check ou alternativa operada. A decisão não altera `public/`, `content/pages.json`, `published_manifest` ou sitemap real.

Autocrítica: a mudança reduz ambiguidade operacional e permite análise editorial mais rica sem abrir publicação indevida. A prova material agora cobre API, schema, arquivo versionado, check e testes; no estado atual a camada tem 4 amostras reais aceitas, bloqueadas, deduplicadas, limitadas por orçamento, `full_text_stored=false` e com flags públicas falsas. A próxima prova deve operar nova superfície adequada ou transformar essas amostras apenas em reescrita autoral própria com fonte oficial específica, revisão jurídico-editorial e recálculo da cadeia editorial. O risco remanescente é falso conforto se uma amostra curta for tratada como autorização de texto público; por isso a revisão Codex/jurídico-editorial e a prova de ausência em artefatos públicos continuam obrigatórias.

## 2026-06-13 — Capacidades complementares sobem para P0 e ledger exige agentes suficientes

Decisao: P2-P5/capacidades complementares viram P0 operacional quando forem necessarias para produzir, validar, publicar, indexar ou escalar este `/goal`. Capacidade historicamente rotulada como fonte, cache, concorrencia, historico editorial, busca propria, grafo, recomendacao interna ou refinamento de tipo de pagina nao pode ficar como backlog quando bloquear conteudo juridico autoral, validacao, release, indexacao ou escala segura. falha de superfície exigida obriga correção executável: investigar parametros seguros, corrigir coletor/parser/schema ou operar alternativa metadata-only com tentativa versionada. falha de ferramenta não fecha ciclo como diagnóstico. A decisao operacional e não registrar apenas investigação sem próximo comando.

Consequencia historica substituida: a ferramenta de agentes e meio tecnico obrigatorio por criterio proporcional neste `/goal`; ciclos P0 complexos e todo ciclo novo do `/goal` devem registrar decisao explicita de delegacao proporcional, em ondas coordenadas pelo Codex principal para preservar contexto, com escopos independentes e ledger antes de checkpoint/commit, sem teto operacional artificial quando houver frentes independentes reais. subagente implementador só é evidência depois de registrado no ledger antes de checkpoint. Subagente com escopo editavel so e valido com `delegated_repo_write_codex_validated`, sem commit pelo subagente, com evidencia de diff, riscos declarados, fechamento antes de checkpoint e validacao obrigatoria do Codex principal. `context_kept_open=true` não é escape para agente concluído/integrado; agente concluído/integrado deve ser fechado antes de checkpoint/commit após achados capturados e integrados. qualquer ponte `priority_*` -> `batch_*` exige prova operacional versionada antes de propagação; sem prova operacional, `priority_*` e `batch_*` continuam camadas bloqueadas separadas. Se contexto ou limite simultaneo apertar, preservar contexto dos agentes anteriores no ledger, fechar os concluidos e relancar nova onda objetiva para frente independente ainda nao coberta; falta de contexto exige preservacao/fechamento/relancamento, nunca alegacao de indisponibilidade.

Autocritica: a mudanca e contratual e nao publica pagina, nao altera `public/`, `content/pages.json`, `published_manifest` ou sitemap real. O ganho real e reduzir falso verde de investigacao passiva e impedir que escrita delegada pareca validada sem revisao principal. A proxima prova material continua sendo operar a superficie metadata-only ou a alternativa segura, recalcular dados derivados quando houver observacao aceita e manter publicacao bloqueada ate gate completo.

## 2026-06-13 — Coleta externa concorrente com limite por superfície

Decisao: tornar `collect-demand-observations` mais eficiente sem reduzir inteligência do algoritmo. O coletor agora aceita `--max-concurrent-requests` e executa oportunidades/superfícies em paralelo com limite, preservando diversidade, merge/upsert, política metadata-only e `--require-surface`. Para superfícies metadata-only que exigem cadência própria, `--metadata-surface-request-interval` aplica intervalo por superfície e por requisição real; Google/Bing continuam podendo usar concorrência maior quando a origem responde.

Consequencia: a tentativa GDELT (`organic_result_metadata`) deixou de ser tratada como problema local de rede: uma consulta direta informou limite de 1 requisição a cada 5s, então a operação responsável foi reexecutada com intervalo de 5s. Google e Bing passaram a aceitar 10/10 oportunidades nessa execução, enquanto GDELT continuou `required_surface_satisfied=false`, agora como `http_status_error` persistido em `demand_surface_collection_attempts`. `demand_signal_observations` permaneceu com 1.238 registros; a superfície orgânica falha não entrou no ranking como demanda capturada.

Autocritica: a melhoria é real porque reduz tempo perdido por serialização e separa eficiência de agressividade irresponsável contra uma fonte. É segura porque só guarda metadados de tentativa, não copia corpo de terceiros, não abre flags públicas e mantém publicação zero. A otimização é real para Google/Bing e para próximas superfícies compatíveis; GDELT ainda não provou utilidade para as queries atuais e exige investigar parametros seguros de consulta/formato ou operar outra fonte metadata-only com tentativa versionada. A validação cobre parser `articles[].title`, concorrência e throttle; falso positivo ainda seria contar tentativa GDELT como mercado, e falso negativo possível é a query jurídica atual não casar com a linguagem da API.

## 2026-06-13 — Seções autorais prioritárias sem bloco dominante

Decisao: fortalecer `priority_authorial_drafts` contra repetição material no corpo, não apenas na abertura. O teste `TestPriorityAuthorialDraftBodySectionsDoNotUseDominantTemplateLead` nasceu vermelho com seção 0 dominada por `antes de qualquer orientação conclusiva` em 138/138 rascunhos e passou depois que as seções passaram a variar por intenção, cenário, contexto e documentos. O check `priority-authorial-drafts` também expôs que variação curta gerava `priority_authorial_draft_thin_section`; a correção foi alongar e contextualizar fonte, risco e triagem, mantendo o gate de 35 palavras e a detecção de texto mecânico.

Consequencia: regenerei a cadeia derivada de `priority_authorial_drafts` até `priority_final_sample_reviews`. Os volumes continuam 138 rascunhos, 132 revisões finais bloqueadas e 6 lane informativa; `published_manifest`, `content/pages.json`, `public/`, sitemap real e `.release-staging` real não foram alterados. A distribuição de leads por seção ficou abaixo do limite de 35%, e os blocos exatos que antes apareciam em 138/138 agora permanecem como risco residual concentrado por família, não como repetição total do lote.

Autocritica: a melhoria é real porque nasceu de falso negativo apontado por auditoria e virou teste/gate em dados reais. É segura porque mantém `noindex`, flags públicas falsas e publicação zero. É otimização real porque reduz padrão de molde antes de qualquer render público. A validação é real para lead de seção, espessura mínima e cadeia derivada; ainda há falso positivo plausível se Jaccard de corpo continuar alto dentro de seeds concentradas. A próxima evidência deve implementar comparador de n-grams/Jaccard em lote ou operar nova superfície externa diversa, sem reduzir `duplicate_risk_score` para parecer avanço.

## 2026-06-13 — Aberturas autorais prioritárias sem lead dominante

Decisao: fortalecer o gerador `priority_authorial_drafts` contra repetição estrutural visível nas aberturas. O teste `TestPriorityAuthorialDraftOpeningsDoNotUseDominantTemplateLead` nasceu vermelho porque 138/138 rascunhos começavam com o mesmo lead, e passou depois que `openingLead` passou a variar a frase inicial por intenção, colocando seed/cenário/contexto logo nos primeiros termos. O normalizador de title também passou a remover `não` quando truncado no fim do prefixo, preservando orçamento de busca sem title pendurado.

Consequencia: regenerei a cadeia derivada de `priority_authorial_drafts` até `priority_final_sample_reviews`. Os 138 rascunhos prioritários permanecem bloqueados, 132 seguem em gates/manifestos/revisões finais bloqueadas, 6 continuam na lane informativa, `published_manifest`, `content/pages.json`, `public/` e sitemap real não foram alterados. A distribuição de lead ficou `para=34`, `quando=31`, `busca=30`, `em=22`, `antes=21`, sem lead dominante acima de 35%.

Autocritica: a melhoria é real porque remove um padrão textual que passava no verde anterior e poderia parecer conteúdo de molde em escala. É segura porque só altera dado bloqueado, preserva fonte, revisão, CTA interno, `noindex` e publicação falsa. É otimização real porque transforma inspeção semântica em teste automatizado antes de publicar. A validação é real para abertura/title e para a cadeia derivada; ainda há risco residual de duplicidade por concentração de seed, evidenciado por 77 revisões finais com `duplicate_risk_score=100`. Esse score não foi reduzido por conveniência; a próxima execução deve atacar diversidade de seções/corpo, nova coleta externa ou aprovação pública somente com gate completo.

## 2026-06-13 — Tentativas de superfície externa persistidas

Decisao: criar `data/research/demand_surface_collection_attempts.jsonl` como camada permanente metadata-only para tentativas de superfícies externas, com contrato de storage, check `demand-surface-collection-attempts`, ferramenta dedicada, validação e teste de contrato. O coletor agora escreve tentativas antes de retornar falha de `--require-surface`, para que superfície pedida sem registros não fique apenas em stderr ou checkpoint.

Consequencia: o estado atual registra 3 tentativas: Google e Bing aceitaram registros metadata-only, enquanto `reddit_public_listing_metadata` foi exigida e falhou com `accepted_records=0`, `required_surface_satisfied=false` e `last_failure_code=http_status_error`. `demand_signal_observations` permaneceu com 1.238 registros e 156 oportunidades; a tentativa falha não virou observação, não alimentou ranking, não abriu brief, não renderizou, não entrou em sitemap e não tocou `published_manifest`, `content/pages.json` ou `public/`.

Autocritica: a melhoria é real porque fecha a lacuna apontada por agente: falha de superfície exigida vira dado versionado e validado, não memória volátil. É segura porque só guarda metadados de tentativa, host/hash/contadores e flags públicas falsas, sem corpo de terceiros nem conteúdo publicável. É otimização real porque evita que o próximo Codex gaste ciclo redescobrindo que a superfície falhou e obriga engenharia de conector/superfície mais precisa. A validação é real para persistência, contrato e bloqueio público; ainda pode haver falso positivo se alguém ler tentativa como demanda, e falso negativo se outra superfície pública permitida capturar sinais melhores. A próxima execução deve criar ou operar nova superfície confiável, reduzir concentração e só recalcular prioridade com observações aceitas.

## 2026-06-13 — Coleta externa exigida e vertical 138/132

Decisao: endurecer `collect-demand-observations` para aceitar parâmetros extras por superfície, superfície distinta `reddit_public_listing_metadata` e `--require-surface`, fazendo a coleta falhar quando uma superfície explicitamente exigida não entrega registros. A operação metadata-only ampliou a camada existente para 1.238 observações, 156 oportunidades e 21 seeds; a tentativa escalada com listagem pública exigida falhou com `required_surface_without_records: reddit_public_listing_metadata`, então essa fonte não foi contabilizada como evidência de mercado.

Consequencia: a cadeia derivada foi recalculada para 166 prioridades, 138 investigações editoriais bloqueadas, 28 lacunas de nova observação, 138 candidatos/rascunhos/fontes/readiness/revisões/evidências/transações, `source_locked=138`, `source_blocked=0`, `paid_passed=132`, `paid_blocked=6`, 132 gates/planos/transações/revisões finais bloqueadas, 6 registros na lane informativa e 45 auditorias URL-level com candidatos oficiais. `published_manifest`, `content/pages.json`, `public/`, sitemap real e `.release-staging` real permanecem sem promoção pública.

Autocritica: a melhoria é real porque impede verde falso quando uma fonte pedida falha, aumenta a cobertura externa e recalcula a vertical downstream em vez de deixar dados stale. É segura porque os novos sinais continuam metadata-only, os rascunhos são permanentes e bloqueados, e a fonte pública exigida que não entregou registros ficou como falha explícita, não como sucesso. É otimização real porque reduz tempo perdido com microcamadas e melhora a precisão operacional do coletor. A validação ainda pode ter falso positivo se a superfície social/vídeo for confundida com demanda social suficiente, e falso negativo se outra API pública permitida capturar sinais melhores; a próxima execução deve criar ou operar nova superfície confiável, reduzir concentração e continuar a vertical de publicação apenas com gate completo.

## 2026-06-13 — Contratos vivos exigem execução verificável, não comentário

Decisao: Pedido explícito, contrato vivo, checkpoint, roadmap, pergunta de engenharia e achado integrado de agente exigem execução verificável do `/goal` ativo, não comentário, recomendação ou fase posterior. Todo requisito executável pertence a este `/goal`. A saída aceitável é código, dado permanente de trabalho, coletor/API/conector operado, schema, teste, check, gerador, revisão, release evidence, manifesto/transação preparada e publicação aprovada com gate completo. Validação proporcional regula custo e escopo, mas não transforma requisito em recomendação, intenção futura ou fase posterior.

Motivo: o contrato já proibia passividade, mas a revisão antes do commit mostrou que o próximo agente precisa de regra ainda mais operacional: se o documento aponta uma ação e o repo permite avanço seguro, o trabalho é executar a vertical coerente, não registrar plano. Se faltar ferramenta, a entrega é construir a ferramenta ou o blocker comprovado.

Consequencia: `AGENTS.md`, `GOAL.md`, README e todos os documentos obrigatórios de `docs/` passam a carregar a mesma regra. `internal/contract/continuity_test.go` deve reprovar documento vivo que perca essa exigência. A mudança não publica página, não altera `public/`, `content/pages.json`, `published_manifest` ou sitemap real; ela fecha margem de leitura passiva antes da próxima vertical P0.

Autocrítica: a melhoria é segura porque endurece contrato e teste sem abrir flags públicas. É otimização real para continuidade porque reduz perda de contexto e obriga artefato validável em vez de comentário. A validação textual não prova páginas públicas, 10k URLs, demanda suficiente ou qualidade jurídica final; a próxima evidência precisa ser vertical técnica com dados reais, fonte, gerador/check e cadeia bloqueada recalculada ou publicação aprovada quando todos os gates permitirem.

## 2026-06-13 — Diagnóstico de concentração e vertical 123/118

Decisao: ampliar a coleta externa metadata-only para 1.170 observacoes e 138 oportunidades, recalcular toda a cadeia prioritária bloqueada e transformar concentração de demanda em diagnóstico de contrato. `demand-signal-observations` agora reporta `top_seed`, `top_seed_basis_points`, `top_area`, `top_area_basis_points` e `concentration_status`, impedindo que volume concentrado seja lido como cobertura suficiente para escala.

Consequencia: a cadeia derivada foi recalculada para 148 prioridades, 123 investigações editoriais bloqueadas, 25 lacunas de nova observação, 123 candidatos/rascunhos/fontes/readiness/revisões/evidências/transações, `source_locked=123`, `source_blocked=0`, `paid_passed=118`, `paid_blocked=5`, 118 gates/planos/transações/revisões finais bloqueadas, 5 BPC/LOAS na lane informativa e 38 auditorias URL-level com candidatos oficiais. O check de demanda mostra `opportunity_coverage_basis_points=136`, `coverage_status=external_coverage_initial_needs_more_observation` e `concentration_status=external_demand_concentration_needs_diversification`. `published_manifest`, `content/pages.json`, `public/`, sitemap real e `.release-staging` real permanecem sem promocao publica.

Autocritica: a melhoria e real porque aumentou dados externos, zerou fonte bloqueada na vertical atual, expos concentração por seed/área e recalculou camadas downstream sem apagar dados permanentes. E segura porque todo dado segue metadata-only ou bloqueado, sem corpo de terceiros, sem render público, sitemap, `public_path` ou publicacao. E otimizacao real porque reduz falso conforto de "mais registros" quando a distribuição ainda é concentrada. A validação exercita dados reais, mas ainda há falso positivo possível se a concentração for ignorada no próximo ciclo ou falso negativo se nova superfície permitida trouxer demanda fora do vocabulário atual; a próxima execução deve ampliar cobertura acima de 138 oportunidades, reduzir concentração medida, qualificar nova superfície metadata-only ou avançar publicação aprovada apenas com gate final completo.

## 2026-06-13 — Penalidade de concentração histórica e vertical 87/84

Decisao: transformar a lacuna de diversidade externa em algoritmo e teste, nao em recomendacao. `internal/demandobservations` agora limita selecao de novas oportunidades por concentracao historica de seed e area; quando um cluster domina observacoes anteriores, a coleta `--focus-unobserved` prioriza alternativas diversas antes de preencher fallback. O teste `TestFocusUnobservedSelectionPenalizesHistoricallyConcentratedSeeds` nasceu vermelho com seed historicamente dominante selecionada 2 vezes e passou apos o ajuste.

Consequencia: a coleta real metadata-only com rede escalada passou `demand_signal_observations` para 968 observacoes e 96 oportunidades. A cadeia derivada foi recalculada para 106 prioridades, 87 investigacoes editoriais bloqueadas, 19 lacunas de nova observacao, 87 candidatos/rascunhos/fontes/readiness/revisoes/evidencias/transacoes, `source_locked=87`, `source_blocked=0`, `paid_passed=84`, `paid_blocked=3`, 84 gates/planos/transacoes/revisoes finais bloqueadas, 3 BPC/LOAS na lane informativa e 20 auditorias URL-level com candidatos oficiais. `published_manifest`, `content/pages.json`, `public/`, sitemap real e `.release-staging` real permanecem sem promocao publica.

Autocritica: a melhoria e real porque corrige o algoritmo que escolhe oportunidades, opera dado externo versionado, recalcula toda a vertical e aumenta a base bloqueada sem destruir dados permanentes. E segura porque a coleta continua metadata-only, sem corpo de terceiros, e a vertical permanece `noindex`, sem render, sitemap, `public_path` ou publicacao. E teste real porque cobre o falso positivo de cluster dominante parecer cobertura de mercado; ainda ha falso negativo possivel se uma superficie externa permitida trouxer demanda nova fora dos sinais atuais. A proxima execucao deve aumentar cobertura acima de 96 oportunidades, qualificar novas superficies ou ampliar conteudo autoral de alta intencao com a mesma cadeia de fonte, revisao, HTML leve, Googlebot e release bloqueado.

## 2026-06-13 — Fonte prioritária zerada e coleta externa exige diversidade

Decisao: resolver para frente os 6 blockers de fonte prioritária restantes, sem Git para voltar estado e sem mascarar fonte ampla. `priority_source_url_audits` agora reaproveita candidatos oficiais por família apenas quando a avaliação metadata-only é específica e o rascunho autoral removeu alegação temporal incompatível. A cadeia foi regenerada de auditoria URL-level até revisão final bloqueada.

Consequencia: `priority-source-url-audits` passa para `audits=14 with_candidates=14`; `priority-source-specificity` passa para `locked=76 blocked=0`; `priority-publication-readiness` passa para `source_locked=76`, `paid_passed=74`, `paid_blocked=2`, `search_ready=76`, `anti_template_ready=76` e `publication_allowed=0`; a promotability passa para `selected_blocked=74`, `paid_intent_excluded=2`; gate, plano, transação de manifesto e revisão final passam para 74 registros bloqueados; `priority_controlled_promotion_rehearsal` segue com 1 registro agregado, `materialized=0`, `published_manifest=0` e publicação zero.

Decisao de escala integrada: a auditoria read-only da demanda externa mostrou que 901 observações e 84 oportunidades ainda são cobertura inicial e concentrada: `acidente-trabalho-indenizacao` e trabalhista dominam a amostra. O próximo avanço de coleta não deve apenas aumentar volume; deve implementar ou operar seleção metadata-only com controle/penalidade de concentração por seed/área, diversidade equivalente e superfície confiável adicional quando permitido, mantendo apenas metadados e recalculando prioridades e camadas autorais quando os sinais mudarem.

Autocrítica: a melhoria é real porque removeu fonte stale em dados permanentes e aumentou a vertical bloqueada de 68 para 74 itens finais sem tocar `public/`, `content/pages.json`, `published_manifest` ou sitemap real. É segura porque fonte oficial continua reference-only, sem scraping, sem texto oficial bruto e com release bloqueado por revisão final, paid-intent e manifesto. O risco restante é confundir fonte travada com aprovação pública ou aceitar concentração externa como demanda para escala; o próximo teste útil deve proteger diversidade de seleção/coleta e expor falsos positivos de cluster repetido antes de gerar mais rascunhos.

## 2026-06-13 — Coleta externa com merge/upsert 901/84 e vertical 76/68

Decisao: adicionar merge/upsert e foco em oportunidades ainda sem observacao ao coletor `collect-demand-observations`, operar a coleta real metadata-only com rede escalada, recalcular `demand_opportunity_priority` e propagar a vertical prioritária bloqueada ate revisao final, promocao controlada e lane informativa. A camada externa passou a 901 observacoes, 84 oportunidades observadas e 94 prioridades; a vertical passou a 76 candidatos/drafts/reviews/evidencias/transacoes, 70 fontes travadas, 6 fontes bloqueadas, 74 paid pass, 2 paid blocked, 68 gates/planos/transacoes/revisoes finais e 2 BPC/LOAS em lane informativa bloqueada.

Motivo: a auditoria indicou que cobertura externa seguia inicial e que uma nova coleta poderia sobrescrever dados úteis. O avanço correto era preservar dados permanentes por `observation_id`, priorizar lacunas sem observacao e recalcular a cadeia derivada, nao apenas documentar recomendacao ou aumentar contador local sem propagacao.

Consequencia: `cmd/check all` passa com `demand-signal-observations observations=901 opportunities=84`, `demand-opportunity-priority records=94 prioritized_for_blocked_review=76 needs_more_external_observation=18`, `priority-source-specificity locked=70 blocked=6`, `priority-release-gate gates=68`, `priority-final-sample-reviews reviews=68` e `priority-informational-lane records=2`. `public/`, `content/pages.json`, `published_manifest`, sitemap real e `.release-staging` real permanecem intocados.

Autocritica: a melhoria e real porque aumenta cobertura externa sem destruir observacoes existentes, expõe 6 blockers de fonte e adapta a lane BPC/LOAS ao dado novo sem mascarar paid-intent. E segura porque toda a cadeia continua `noindex`, sem render, sem sitemap, sem publicacao e sem copia de conteudo externo. A otimizacao reduz risco de falso positivo por coleta destrutiva e falso negativo por lacuna ignorada, mas ainda nao prova demanda suficiente para 10k nem aprovacao juridica publica. A validacao exercitou dados reais e cadeia derivada; ainda ha risco de concentracao semantica e de fonte bloqueada travar parte da vertical. A proxima evidencia deve resolver os 6 blockers de fonte ou aumentar superficie/cobertura externa com diversidade maior antes de gerar volume publico.

## 2026-06-13 — Lane informativa bloqueada BPC/LOAS

Decisao: criar `priority_informational_lane_reviews` como camada permanente bloqueada para BPC/LOAS excluido da promotability comercial, com gerador, check, CLI, contrato de storage, teste de contrato e JSONL versionado. A camada registra as revisoes informativas bloqueadas de BPC/LOAS calculadas pelo repo; no estado atual sao 2 registros, com fonte oficial MDS em hash, documentos especificos, aviso de vulnerabilidade, OAB, ausencia de CTA comercial, ausencia de promotability comercial e flags publicas fechadas.

Motivo: o BPC/LOAS nao podia ser promovido como tema comercial sem mascarar assistencia publica/gratuidade, mas manter apenas a exclusao deixava utilidade informativa sem trilha propria. Como o usuario exigiu execucao precisa, sem passividade e sem tratar dado real como descartavel, a resposta correta foi materializar a lane bloqueada com codigo, dado permanente e check global, nao registrar nova recomendacao.

Consequencia: `priority-informational-lane` entra em `cmd/check all` e no estado atual reporta `records=2`, `blocked=2`, `commercial_cta_open=0` e `publication_allowed=0`. `data/editorial/priority_informational_lane_reviews.jsonl` passa a fazer parte do contrato de storage como dado permanente bloqueado. `public/`, `content/pages.json`, `published_manifest`, sitemap real e `.release-staging` real permanecem intocados.

Autocritica: a melhoria e real porque transforma o BPC/LOAS remanescente em camada auditavel, sem forcar paid-intent comercial e sem apagar a utilidade humana. E segura porque a lane mantem `approval=false`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `index_policy=noindex`, `public_path=""` e CTA comercial fechado. A otimizacao reduz falso positivo de promocao comercial e falso negativo de perda informativa, mas nao prova aprovacao juridica publica nem cria pagina indexavel. A validacao exercita dados reais e falha se a camada ficar stale; ainda ha risco se uma revisao humana futura exigir recorte mais fino de fonte, texto ou linguagem de vulnerabilidade. A proxima evidencia deve avancar uma frente maior: publicacao aprovada com gate completo, ampliacao externa/conteudo autoral de alta intencao ou algoritmo anti-duplicidade/SEO mais forte, nao repetir a lane ja criada.

## 2026-06-13 — Revisão final bloqueada prioritária dos 64

Decisao: criar `priority_final_sample_reviews` como camada permanente bloqueada depois de `priority_controlled_promotion_rehearsal`, com gerador, check, CLI, contrato de storage, teste de contrato e JSONL versionado. A camada registra 64 revisoes finais bloqueadas, uma por transacao de manifesto atual, cruzando corpo autoral real, fonte oficial em hash, CTA/OAB, paid-intent, HTML/SEO, riscos de duplicidade, notas de falso positivo/falso negativo e blockers finais.

Motivo: a promocao controlada bloqueada provava mecanica de staging/espelho/smoke/lock/ledger/rollback, mas ainda havia risco de falso conforto: tratar a prova tecnica como suficiente sem leitura de corpo, fonte, CTA/OAB e SEO por registro. Como o usuario exigiu vertical maior, precisao e nada de passividade, a resposta correta foi criar a camada executavel e validada, nao documentar recomendacao.

Consequencia: `priority-final-sample-reviews` entra em `cmd/check all` e reporta `reviews=64`, `seeds=16`, `contexts=18`, `blocked=64` e `publication_allowed=0`. `data/editorial/priority_final_sample_reviews.jsonl` passa a fazer parte do contrato de storage como dado permanente bloqueado. `public/`, `content/pages.json`, `published_manifest`, sitemap real e `.release-staging` real permanecem intocados.

Autocritica: a melhoria e real porque adiciona leitura tecnica por registro e impede que a vertical avance por contador ou smoke isolado. E segura porque todos os registros mantem `approval=false`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `index_policy=noindex` e `public_path=""`. A otimizacao reduz risco de falso positivo antes de release, mas nao prova aprovacao juridica publica nem cria paginas indexaveis. A validacao exercita dados reais e falha se a camada ficar stale; ainda ha falso negativo possivel se uma pagina boa exigir reescrita humana final fora do algoritmo. A proxima evidencia deve avancar uma frente diferente: publicacao aprovada quando todos os gates permitirem, lane informativa BPC/LOAS bloqueada ou expansao externa/conteudo autoral de alta intencao com cadeia completa.

## 2026-06-13 — Contratos vivos travados em 834/72/65/64/1

Decisao: travar os contratos operacionais no estado vivo derivado do repo apos `70f3a1e`: 834 observacoes externas, 72 oportunidades observadas, 65 prioridades em investigacao editorial, 64 selecionados/gates/planos/transacoes bloqueadas e 1 BPC/LOAS remanescente excluido por paid-intent. O README, `docs/DATA_SOURCES.md`, `docs/LAB_VALIDATION.md` e `docs/ROADMAP_P0_P5.md` foram alinhados, e `internal/contract/continuity_test.go` passou a reprovar retorno de contadores 41/37/4 nos documentos vivos.

Motivo: tres auditorias read-only do ciclo confirmaram que os documentos ainda carregavam contadores antigos. Isso poderia fazer o proximo Codex repetir diagnostico ja superado, atacar quatro BPC/LOAS inexistentes, recalcular a vertical como 37 em vez de 64 ou tratar um checkpoint antigo como fronteira do `/goal`. Como o usuario exigiu contrato preciso e sem passividade, contador vivo errado virou falha de contrato, nao ajuste cosmético.

Consequencia: a documentacao operacional agora aponta a proxima execucao material para revisao juridico-editorial/amostral estratificada dos 64, lane informativa bloqueada para o BPC/LOAS remanescente quando essa frente for escolhida, nova cobertura externa ou publicacao aprovada somente quando todos os gates permitirem. Nenhum texto transforma os 64 em publicacao real: `published_manifest`, `content/pages.json`, `public/` e sitemap real continuam fechados.

Autocritica: a melhoria e real porque reduz perda de contexto e torna stale counter uma regressao automatizada. E segura porque so altera contratos/teste/ledger/checkpoint, sem abrir render, sitemap, publicacao ou `public_path`. A otimizacao e operacional: evita retrabalho caro antes da proxima vertical P0. A validacao prova que os documentos vivos refletem os dados atuais, mas nao prova qualidade juridica final dos 64 nem suficiencia para 10k. Falso positivo plausivel: interpretar contrato atualizado como avanco material suficiente. Falso negativo plausivel: tratar o BPC/LOAS informativo como impossivel quando a lane bloqueada pode ser util. A proxima evidencia deve ser camada/check de revisao final amostral ou lane informativa bloqueada, com dado permanente e flags publicas fechadas.

## 2026-06-13 — Expansão externa 834/72 e vertical prioritária 65/64 sem publicação

Decisao: ampliar a coleta externa metadata-only de oportunidades prioritárias, corrigir o algoritmo de seleção para diversificar cenário e contexto, recalcular `demand_opportunity_priority` e propagar a vertical prioritária bloqueada até promoção controlada. A coleta atual registra 834 observações, 72 oportunidades observadas, 21 seeds, 3 superfícies, 24 cenários e 20 contextos; o ranking passa a 82 prioridades, com 65 para revisão editorial bloqueada e 17 exigindo nova observação externa.

Motivo: o estado anterior tinha 48 oportunidades observadas e só 2 cenários/2 contextos, risco claro de falso avanço por contador. O contrato exigia operar cobertura externa quando `coverage_status=external_coverage_initial_needs_more_observation`; manter arquitetura ou diagnóstico no lugar da coleta seria passividade. A correção preserva política metadata-only, não guarda corpo de terceiros e recalcula os dados derivados em vez de editar JSON manualmente.

Consequencia: a vertical prioritária passa a 65 rascunhos/fontes/readiness/revisões/evidências, 64 seleções/gates/planos/transações e 1 promoção controlada bloqueada com `transactions=64`, `isolated_http_smoke=1`, `swap_blocked=1`, `ledger_records=2` e `publication_allowed=0`. `priority-source-url-audits` foi recalculado para 8 auditorias atuais, sem IDs órfãos. `public/`, `content/pages.json`, `published_manifest`, sitemap real e `.release-staging` real permanecem intocados.

Autocritica: a melhoria é real porque aumenta cobertura externa e diversidade antes de gerar mais conteúdo, corrige teste/algoritmo contra falso positivo de cenário/contexto e prova a cadeia downstream bloqueada. É segura porque todas as camadas mantêm `noindex`, flags públicas falsas e diffs públicos críticos vazios. A validação é real para coleta, ranking, fonte, gates e promoção bloqueada, mas não prova suficiência de mercado para 10k, revisão jurídica final nem página indexável. O próximo avanço deve aprofundar revisão final/amostral dos 64, resolver o BPC/LOAS remanescente em lane adequada, adicionar superfície externa confiável ou preparar publicação aprovada quando todos os gates permitirem.

## 2026-06-13 — Promoção controlada prioritária bloqueada dos 37

Decisao: criar `priority_controlled_promotion_rehearsal` como camada permanente bloqueada depois de `priority_manifest_transaction_rehearsal`, com gerador, check, CLI e wrapper. A camada usa `publicrelease.PrepareStagingTransactionPlan` para preencher `OutputPath` de staging em raiz isolada, materializa staging e temporary public recriaveis, valida smoke HTTP/Googlebot temporario, cria plano de swap, executa a tentativa ate o bloqueio `public_release_promotion_blocked_by_default`, registra lock/ledger e constrói rollback sem tocar artefatos permanentes.

Motivo: `priority_manifest_transaction_rehearsal` provava apenas coerencia transacional em memoria. A proxima falha provavel era descobrir problema de staging, temporary public, smoke, lock, ledger ou rollback tarde demais. Escrever na `.release-staging` real ou em `public/` seria publicacao indevida; deixar a etapa como recomendacao seria passividade. A raiz isolada permite prova de promocao bloqueada sem contaminar o workspace publico.

Consequencia: `priority-controlled-promotion` entra em `cmd/check all` com `records=1`, `transactions=37`, `temporary_http_smoke=1`, `swap_blocked=1`, `ledger_records=2` e `publication_allowed=0`. `data/editorial/priority_controlled_promotion_rehearsal.jsonl` registra `swap_operation_count=40`, `rollback_snapshot_count=2`, `rollback_operation_count=40`, lock escrito, flags publicas falsas e `public_path=""`. `public/`, `content/pages.json`, `published_manifest`, sitemap real e `.release-staging` real permanecem intocados.

Autocritica: a melhoria e segura porque staging e temporary public ficam em raiz isolada recriavel, enquanto o dado util fica versionado no repo. E otimizacao real porque transforma uma etapa P0 material em check global e reduz risco de promocao futura sem rollback/lock/smoke. A validacao e real para mecanica de promocao bloqueada, mas nao prova aprovacao juridica final nem resolve os 5 BPC/LOAS; falso positivo ainda seria tratar smoke temporario como publicacao aprovada. A proxima evidencia deve aprofundar revisao final/publicacao aprovada quando gates permitirem, criar lane informativa BPC/LOAS bloqueada ou ampliar demanda externa de alta intencao.

## 2026-06-13 — Linguagem de utilidade não reduz pedido explícito

Decisao: pedido explicito nao e item de utilidade abstrata. Quando util ou se util nao reduz requisito solicitado; essas expressoes so podem funcionar como criterio tecnico de classificacao, risco ou proporcionalidade, nunca como permissao para omitir trabalho contratado. Pedido do usuario com avanço seguro no repo obriga entrega de codigo, dado permanente de trabalho, teste, check e documentacao operacional, preservando gates publicos fechados.

Motivo: o contrato ja dizia que pedido explicito pertence ao `/goal`, mas o pedido atual exige fechar a leitura residual de que uma regra documentada poderia ficar condicionada a utilidade futura. A decisao torna a linguagem mais precisa para o proximo Codex: utilidade do requisito ja foi estabelecida; o que resta para a engenharia e escolher a maior camada vertical segura, validar e continuar.

Consequencia: `internal/contract/continuity_test.go` passa a exigir essa regra em `AGENTS.md`, `GOAL.md`, README, `docs/LAB_VALIDATION.md`, `docs/ROADMAP_P0_P5.md` e neste arquivo. A mudanca nao publica pagina, nao abre `render_allowed`, nao altera `content/pages.json`, `published_manifest`, `public/` ou sitemap real. Ela prepara o commit para continuar a vertical P0 com promocao controlada bloqueada dos 37 ou lane informativa BPC/LOAS bloqueada, sem passividade.

Autocritica: a melhoria e segura porque reforca contrato e teste sem tocar artefato publico. E otimizacao real porque reduz perda de tempo por interpretacao opcional antes do proximo ciclo. A validacao e real para texto contratual, mas nao substitui prova em dados: ainda falta implementar a camada P0 material, ler os registros reais, validar subagentes no ledger e manter diff publico vazio. Falso conforto possivel seria tratar contrato verde como entrega final; a proxima evidencia deve ser codigo/dado/check vertical.

## 2026-06-13 — Contratos sem passividade e agentes integrados antes do commit

Decisao: revisar os contratos obrigatorios antes do commit, corrigir contadores vivos que ainda citavam 28 gates/planos/transacoes na vertical prioritária, integrar os achados dos dois subagentes read-only do ciclo e transformar as recomendações em comandos operacionais do `/goal`. Linguagem opcional, contador stale, "proximo ciclo" como adiamento e relatorio de agente sem ledger passam a ser tratados como falha de execução, não detalhe documental.

Motivo: o estado real do repo apos a correção de fonte é 41 rascunhos prioritários, 37 selecionados bloqueados, 37 gates, 37 planos, 37 ensaios transacionais, 5 BPC/LOAS excluídos por paid-intent, `published_manifest=0` e `publication_allowed=0`. O relatório sobre BPC/LOAS confirmou que seleção comercial forçada seria mascaramento; o relatório sobre promoção confirmou que a maior vertical segura seguinte é promoção controlada bloqueada com staging/temporary public/smoke/lock/rollback, sem tocar artefatos permanentes.

Consequencia: `AGENTS.md`, `GOAL.md`, README, `DATA_SOURCES.md`, `LAB_VALIDATION.md`, `CONTENT_QUALITY.md` e `ROADMAP_P0_P5.md` agora registram que BPC/LOAS deve permanecer excluído comercialmente ou virar lane informativa bloqueada, e que os 37 selecionados devem seguir para camada/check de promoção controlada bloqueada com swap bloqueado por padrão. Os contratos vivos deixam claro que revisão antes do commit, integração de agentes e contagem atual fazem parte da execução do `/goal`; não são recomendação nem fase posterior.

Autocrítica de engenharia: a melhoria é segura porque só altera contratos, checkpoint e ledger, preservando publicação zero. É otimização real porque evita que o próximo Codex repita auditoria já feita, trabalhe contra contador antigo ou force BPC/LOAS como comercial para passar contador. A validação precisa provar que os checks contratuais continuam verdes, que os agentes foram registrados e que `public/`, `content/pages.json`, `published_manifest` e sitemap real não mudaram. Falso positivo ainda é possível se a futura promoção controlada medir apenas HTTP temporário e não conteúdo autoral real; falso negativo ainda é possível se BPC/LOAS informativo legítimo ficar sempre parado. A próxima evidência executável é teste vermelho e implementação da camada de promoção controlada bloqueada dos 37, ou lane informativa bloqueada BPC/LOAS com documentos/fonte/revisão específicos, sem publicação.

## 2026-06-13 — Fonte específica prioritária 41/0 sem publicar

Decisao: corrigir a vertical `priority_source_specificity` para reaproveitar candidatos oficiais metadata-only por família/seed/contexto quando o rascunho autoral está alinhado e não contém prazo sem suporte. A auditoria URL-level passa a registrar candidatos para as variações irmãs de aposentadoria especial, empréstimo consignado não contratado e desconto indevido no INSS; a resolução de fonte consome esses candidatos por resolução exata e mantém `reference_only_no_scraping_no_ingestion`.

Motivo: havia 9 blockers de fonte porque o mapeamento dependia do `unique_intent_id` exato, embora candidatos oficiais específicos já existissem para intents irmãs. Manter esses blockers depois da auditoria viraria falso negativo; liberar por domínio ou fonte ampla seria falso positivo. A correção exigiu teste vermelho, regra explicável por seed e recálculo downstream.

Consequencia: `priority-source-url-audits` passa para `audits=17 with_candidates=17`; `priority-source-specificity` passa para `locked=41 blocked=0`; `priority-publication-readiness` passa para `source_locked=41`, `paid_passed=37`, `paid_blocked=5`, `search_ready=41`, `anti_template_ready=41` e `publication_allowed=0`. A cadeia derivada foi recalculada até manifesto transacional bloqueado, com `selected_blocked=37`, `gates=37`, `plans=37`, `transactions=37`, `materialized=0` e publicação zero.

Autocrítica de engenharia: a melhoria é real porque remove blockers de fonte por mapeamento estreito sem afrouxar fonte ampla. É segura porque não guarda texto oficial bruto, não copia fonte, não abre render/sitemap/publicação e mantém `public_path=""`. A otimização reduz falso negativo e aumenta candidatos tecnicamente ensaiados de 28 para 37, mas não prova revisão jurídica final nem resolve os 4 bloqueios de paid-intent. A próxima evidência deve atacar paid-intent/assistência pública ou preparar promoção controlada bloqueada com leitura jurídica amostral, mantendo diff público vazio.

## 2026-06-13 — Search readiness prioritário corrigido sem afrouxar gate

Decisao: corrigir o gerador de títulos de `priority_authorial_drafts` para eliminar duplicidade exata de `title_candidate` e cortes artificiais antes do foco de search appearance. A correção usa termos-base editoriais por `seed_term_id` e foco curto por cenário/contexto, mantendo o classificador de `priority_publication_readiness` intacto.

Motivo: a auditoria read-only do ciclo 252 mostrou que os 26 bloqueios de `search_ready` eram `priority_duplicate_title_candidate`. O primeiro ajuste removeu duplicidade, mas a leitura manual pegou falso conforto editorial em títulos truncados como fragmento terminado em conector. A resposta correta foi adicionar teste negativo para título duplicado e conector pendurado antes dos dois-pontos, não aceitar `search_ready=41` por contador apenas.

Consequencia: `priority-publication-readiness` agora passa com `search_ready=41`, `source_locked=32`, `paid_passed=37`, `paid_blocked=5`, `anti_template_ready=41`, `legal_review_required=41` e `publication_allowed=0`. A cadeia derivada foi regenerada até `priority_manifest_transaction_rehearsal`, preservando `transactions=28`, `public_release_valid=28`, `materialized=0` e publicação zero. O próximo gargalo material deixa de ser search appearance exata e passa a ser fonte específica dos 9 blockers, paid-intent/assistência pública dos 4 bloqueados, cobertura externa ainda inicial e promoção/revisão final bloqueada.

Autocrítica de engenharia: a melhoria é real porque remove um blocker SEO sem enfraquecer gate e transforma a leitura manual de títulos ruins em teste. É segura porque todos os registros seguem `approval=false`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false` e `public_path=""`. A otimização é de qualidade editorial e crawl: reduz canibalização e títulos truncados antes de qualquer sitemap público. A validação ainda pode ter falso positivo semântico se dois títulos diferentes continuarem muito parecidos para humanos; a próxima evidência deve atacar fonte específica ou paid-intent com testes e dados reais, mantendo leitura amostral.

## 2026-06-13 — Expansão externa 518/41/28 e contratos recalculados

Decisao: ampliar a coleta externa metadata-only para 48 oportunidades, recalcular a cadeia prioritária até o ensaio transacional bloqueado e alinhar contratos vivos ao estado real do repo. `demand_signal_observations` passa a registrar 518 observações, 21 seeds e 3 superfícies; `demand_opportunity_priority` passa a 58 prioridades, com 41 para revisão editorial bloqueada e 17 exigindo nova coleta. A vertical derivada passa a 41 candidatos, 41 rascunhos autorais permanentes bloqueados, 41 reviews/evidências/transações, 28 gates finais, 28 planos de manifesto e 28 ensaios transacionais, com `published_manifest=0` e `publication_allowed=0`.

Motivo: os contratos ainda continham contadores de 207/258 observações, 19/20 registros prioritários e frases que poderiam orientar o próximo Codex por estado superado. A expansão também expôs falha real de qualidade: o gerador autoral reutilizava aberturas nos primeiros termos quando a escala subiu para 41 candidatos. A correção correta foi refinar a abertura determinística por identidade editorial, preservar o check `priority_authorial_reused_opening` e regenerar dados derivados, não reduzir a exigência nem reverter para volume anterior.

Consequencia histórica atualizada: `GOAL.md`, `README.md`, `DATA_SOURCES.md`, `LAB_VALIDATION.md`, `SEO_CRAWL_INDEXING.md`, `ROADMAP_P0_P5.md` e `ARCHITECTURE.md` foram atualizados para tratar números como estado calculado, não limite; P2-P5 permanecem rótulos históricos e não adiam requisito executável do `/goal`; cache/arquitetura não devem tomar a frente de demanda/fonte/conteúdo/release quando a cobertura externa ainda for inicial. O ciclo 253 resolveu para frente os 26 itens sem `search_ready`; o próximo avanço deve mirar os 9 blockers de fonte, os 4 bloqueios de paid-intent, promoção/revisão final bloqueada ou ampliar cobertura acima de 48 oportunidades com superfície confiável, mantendo HTML leve, dados permanentes, fonte oficial e publicação bloqueada.

Autocrítica de engenharia: a melhoria material foi ampliar demanda externa e recalcular a vertical prioritária até transação bloqueada, mas a cobertura ainda é inicial contra 10.080 oportunidades e a terceira superfície é apenas sinal social/vídeo metadata-only. O ciclo permaneceu seguro porque a cadeia manteve `approval=false`, `publication_allowed=0`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""`, `published_manifest` vazio e diff público crítico vazio. O ganho foi real para coordenação e escala porque dobrou a cobertura operacional, propagou dados até manifesto transacional bloqueado e removeu falso conforto de contadores stale. A validação exercitou anti-template, linhagem, flags públicas, HTML leve e ausência de publicação, mas ainda admite falso positivo de intenção paga em termos com assistência pública e falso negativo em termos digitais sem vocabulário comercial explícito. A próxima ação executável deve atacar esses riscos com algoritmo, fonte oficial e leitura de amostras, não apenas aceitar check verde.

## 2026-06-13 — Requisito documentado vira execução do goal

Decisao: qualquer contrato vivo, checkpoint, roadmap, pergunta de engenharia ou documentação obrigatória que identifique ação executável deve ser lido como fila de execução do `/goal`, não como recomendação. Linguagem de conveniência não rebaixa obrigação já contratada; ela apenas orienta proporcionalidade por risco quando o próprio contrato exigir validação focada em vez de prova full. Coletor, API, schema, teste, fixture, camada versionada, algoritmo ou fonte oficial insuficiente obriga construir a peça faltante com evidência, não registrar a ausência como plano passivo.

Consequencia: `AGENTS.md`, `GOAL.md`, README, `LAB_VALIDATION.md`, `DATA_SOURCES.md`, `CONTENT_QUALITY.md` e `ROADMAP_P0_P5.md` foram alinhados para exigir execução verificável, dados permanentes, expansão externa metadata-only, subagentes obrigatórios com ferramenta de agentes sempre disponível e obrigatória no `/goal`, leitura de contexto antes de confiar em verde e continuidade depois de checkpoint/commit. A meta mínima de 10 mil páginas públicas jurídicas únicas, aprovadas, indexáveis e verificadas continua distante e pertence ao `/goal` atual; o estado local, os 41 rascunhos prioritários atuais e os 2.220 candidatos internos são base inicial, não fronteira do produto.

Autocrítica: a melhoria reduz ambiguidade e perda de contexto, mas ainda é contratual. É segura porque não altera publicação, sitemap, `content/pages.json`, `public/` ou `published_manifest`. A validação real precisa confirmar que os checks continuam verdes e que o diff público crítico permanece vazio; o próximo avanço técnico deve voltar para expansão externa metadata-only ou seleção/promotabilidade real das prioridades elegíveis, com ferramenta/check/dado e sem mascarar qualidade.

## 2026-06-13 — Plano bloqueado de manifesto prioritário com revisão semântica

Decisao: criar `priority_manifest_plan` como camada permanente bloqueada depois de `priority_release_gate`, consumindo 1:1 os 19 gates finais e calculando plano de `published_manifest` sem tocar artefatos públicos. A camada registra manifest ID planejado, path/canonical/title/meta planejados, hashes de HTML e sitemap de ensaio, revisão semântica, risco de texto genérico, notas finais, blockers restantes e requisitos explícitos de transação pública.

Motivo: o gate final ainda deixava "plano de manifesto" como requisito textual. Manter isso apenas como frase permitiria passividade e falso conforto; escrever direto em `published_manifest`, `content/pages.json`, `public/` ou sitemap real seria publicação indevida. O avanço correto é uma camada versionada, recalculável e bloqueada que leia o conteúdo autoral real, recuse padrões genéricos e prove que a próxima promoção ainda depende de aprovação humana final, transação de manifesto, escrita pública controlada, smoke HTTP/Googlebot e rechecagem de duplicidade.

Consequencia: `priority-manifest-plan` entra em `cmd/check all`, com `plans=19`, `semantic_passed=19`, `manifest_blocked=19` e `publication_allowed=0`. O gerador autoral prioritário foi refinado para substituir orientação documental genérica por documentos e foco probatório por área/termo/contexto; a validação reprova risco semântico alto em vez de reduzir limite para passar. `data/editorial/priority_manifest_plan.jsonl` mantém `approval=false`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""`, `content_pages_touched=false`, `published_manifest_touched=false` e `public_sitemap_touched=false`.

Autocrítica: a melhoria reduz risco real porque transforma plano textual em dado/check e pega repetição autoral antes de `published_manifest`. É segura porque preserva publicação zero e diff público crítico vazio. A otimização é de qualidade e coordenação: o próximo Codex não precisa redescobrir que a etapa faltante é manifesto transacional/release público ou expansão externa, mas ainda não há página jurídica pública nem sitemap indexável da meta mínima. A validação exercita dados reais e falhou antes da correção por texto genérico, mas ainda pode ter falso positivo se a revisão semântica mínima aceitar conteúdo juridicamente fraco; a próxima evidência deve aprofundar leitura jurídica/duplicidade ou avançar a transação bloqueada de manifesto sem abrir publicação indevida.

## 2026-06-13 — Ensaio transacional bloqueado dos manifestos prioritários

Decisao: criar `priority_manifest_transaction_rehearsal` como camada permanente bloqueada depois de `priority_manifest_plan`, validando em memória um `publicrelease.TransactionPlan` para os 19 planos prioritários. A camada registra manifesto planejado, página planejada, hash de HTML, hash de sitemap, hash do plano transacional e requisitos de append/merge/write/lock/rollback, mas mantém materialização e promoção proibidas.

Motivo: depois do plano de manifesto, a próxima lacuna era provar que os 19 planos conseguem formar uma transação pública coerente sem tocar os artefatos finais. Escrever direto em staging, `published_manifest`, `content/pages.json`, `public/` ou sitemap real ainda seria prematuro; validar apenas contadores também seria passivo. O ensaio transacional usa o contrato existente de `publicrelease.ValidateTransactionPlan` e deixa explícito o que ainda falta antes de qualquer materialização.

Consequencia: `priority-manifest-transaction` entra em `cmd/check all`, com `transactions=19`, `public_release_valid=19`, `materialized=0` e `publication_allowed=0`. O arquivo `data/editorial/priority_manifest_transaction_rehearsal.jsonl` preserva flags públicas falsas e prova que a transação planejada é completa em memória, sem chamar `MaterializeStaging` nem escrever artefatos públicos reais.

Autocrítica: a melhoria reduz risco de descobrir incompatibilidade de manifesto só no momento de promoção. É segura porque não materializa staging e mantém diff público crítico vazio. É otimização real de engenharia porque reaproveita o validador transacional existente e transforma uma próxima etapa em prova executável. A validação ainda pode ter falso positivo editorial, porque uma página tecnicamente transacional pode ter corpo jurídico insuficiente; a próxima evidência deve aprofundar revisão humana/jurídica, anti-duplicidade ou preparar promoção controlada bloqueada com smoke final, sem pular gates.

## 2026-06-13 — Contratos P0 sem passividade e com expansão executável

Decisao: os contratos principais foram endurecidos para deixar explícito que a meta mínima de 10 mil páginas públicas jurídicas aprovadas pertence ao `/goal` ativo, não a uma fase vaga posterior. `AGENTS.md`, `GOAL.md`, `README.md`, `PROJECT_VISION.md`, `DATA_SOURCES.md`, `CONTENT_QUALITY.md`, `SEO_CRAWL_INDEXING.md` e `LAB_VALIDATION.md` agora tratam checkpoint, commit, laboratório verde e documentação como rastreabilidade para continuar, exigem camadas verticais maiores quando houver frente segura e obrigam criar ferramenta/schema/CLI/check/camada versionada quando a expansão depender de sinais externos que o repo ainda não capture.

Adendo do ciclo atual: linguagem de conveniência em contrato não pode enfraquecer requisito já solicitado. Documento que registra expansão externa, alta intenção jurídica digital, coleta metadata-only, subagentes/ledger, dados permanentes, revisão jurídico-editorial, robustecimento de teste, recalculo de SEO/paid-intent/review após mudança autoral ou pergunta de engenharia obriga o próximo Codex a executar uma ação verificável no repo. "Próximo ciclo" é continuidade técnica imediata; não é estacionamento de escopo. O lote atual e os contadores existentes são ponto de partida, não fronteira do produto.

Motivo: o estado atual ainda está distante da meta pública mínima: há rascunhos, candidatos, observações e resoluções bloqueadas, mas não há 10 mil páginas jurídicas públicas aprovadas, indexáveis e verificadas. Um contrato que permita “próximo ciclo” como estacionamento, P0 como arquitetura isolada ou ausência de coletor como justificativa enfraquece o objetivo. A documentação oficial atual do Google Search Central reforça conteúdo útil para pessoas, valor original, cuidado com automação em escala sem valor, JavaScript/HTML rastreável e sitemap como descoberta, não aprovação. O manual oficial atual do Codex confirma `AGENTS.md` como superfície persistente de instruções do repo e descreve subagentes como mecanismo para frentes paralelas, com cuidado em escrita concorrente.

Consequencia: o próximo Codex deve executar avanço P0 calculado pelo repo, com pesquisa externa e fonte oficial quando necessário, sem reduzir a missão ao blocker local corrente. Se faltar coletor de demanda orgânica, autosuggest, Bing, Google, rede social pública, API, feed ou observação equivalente, a ação é construir o coletor e sua validação metadata-only no repo. Se conteúdo, CTA, title/meta, fonte ou final draft mudar, os testes SEO/paid-intent/review/manifest devem ser recalculados sobre os dados reais. Validação focada continua correta para mudança localizada; validação pesada só entra quando o risco atravessa contratos centrais, publicação, render, sitemap, crawl, storage, massa ou performance.

Autocrítica: a melhoria é real porque remove ambiguidade operacional que podia transformar diagnóstico em pausa e falta de ferramenta em desculpa. É segura porque só altera contrato/documentação, não toca `public/`, `content/pages.json` nem `published_manifest`, e mantém rascunhos/camadas bloqueadas. A otimização é de coordenação: reduz perda de contexto e orienta o próximo avanço para ferramenta e dado executável, mas ainda não resolve os 3 blockers prioritários nem cria páginas públicas. A validação documental pode ter falso conforto se o próximo ciclo não transformar o contrato em código/check/dado; a próxima evidência forte é resolver ou reclassificar os blockers prioritários com fonte oficial específica e, em paralelo, ampliar captura externa metadata-only com ferramenta validada.

Autocrítica complementar: a revisão documental só é útil se impedir passividade operacional no próximo commit. Ela não mede página pública, não aumenta `published_manifest` e não substitui conteúdo jurídico autoral. A próxima melhoria segura e mais valiosa deve ser recalculada pelo repo: neste estado, resolver 9 blockers de fonte, 26 itens sem `search_ready`, 4 bloqueios de paid-intent e ampliar coleta externa são frentes materiais para os 41 rascunhos prioritários atuais. O teste real precisa ler dados e contratos, não apenas procurar palavras; falso conforto permanece se um check passar sem amostra suficiente ou se um agente tratar pergunta de engenharia como comentário.

## 2026-06-12 — Fonte prioritária específica fica em camada própria bloqueada

Decisao: rascunhos autorais prioritários devem ter uma camada própria de resolução de fonte, `data/editorial/priority_source_specificity_resolutions.jsonl`, validada por `priority-source-specificity`. A camada é chaveada por `priority_authorial_draft_id`, preserva `brief_candidate_id`, `priority_id`, `unique_intent_id`, seed/cenário/contexto e decide por URL se a fonte fica `priority_source_locked_reference_only` ou `priority_source_blocked_needs_specific_official_url`. Ela não reutiliza `source_resolutions.jsonl`, porque aquele schema é orientado a `term_id/source_brief_id` e perderia a linhagem da vertical de prioridade observada.

Motivo: os 15 `priority_authorial_drafts` já estavam bloqueados e com `source_resolution_required=true`, mas ainda podiam carregar URL oficial ampla como se fosse fonte suficiente. Homes como BCB/INSS, notícia contextual ou canal genérico precisam bloquear até existir fonte oficial específica do recorte; domínio oficial e score local não bastam para release.

Consequencia: a camada nova grava 15 resoluções bloqueadas: 8 com fonte específica travada apenas como referência e 7 com blocker acionável por fonte ampla/contextual. Cada registro guarda metadados e hash SHA-256 da URL, `use_policy=reference_only_no_scraping_no_ingestion`, `raw_text_stored=false`, `scraping_allowed=false`, `ingestion_allowed=false`, `index_policy=noindex`, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`. `cmd/check all` passou a incluir `priority-source-specificity`.

Autocrítica: a melhoria é real porque transforma “fonte oficial exigida” em decisão executável por rascunho prioritário, reduzindo falso positivo de fonte ampla mascarada. É segura porque só cria camada bloqueada, sem texto oficial bruto, sem render, sem sitemap e sem publicação. A otimização é estrutural e prepara paid-intent/SEO/revisão com fonte mais clara, mas ainda não resolve as 7 fontes bloqueadas nem prova revisão jurídica. A validação exercita dados reais e pegaria count mismatch, URL não oficial, fonte travada sem especificidade e flags públicas; falso negativo ainda é possível para notícia oficial específica ou código com âncora suficiente, então o próximo avanço deve pesquisar fontes oficiais atuais para os 7 blockers ou ajustar o classificador com evidência e teste negativo.

## 2026-06-12 — P0 não adia publicação aprovada nem reduz o goal a arquitetura

Decisao: registros históricos que dizem que P0 não publica conteúdo ou que publicação depende de fase futura devem ser lidos apenas como proteção contra publicação sem gate. O contrato atual é mais preciso: P0 não publica por volume, atalho, laboratório verde ou fase nominal, mas deve promover página pública aprovada quando fonte específica, revisão jurídico-editorial/OAB, paid-intent/CTA ou bloqueio explícito, qualidade/anti-template, SEO/crawl, HTML leve, `published_manifest`, sitemap/canonical/robots, smoke HTTP/Googlebot e release gate completo passarem. A meta de 10 mil páginas jurídicas públicas continua ativa neste `/goal` e não pode ser diferida por nomenclatura de fase.

Motivo: a auditoria documental do ciclo 224 encontrou documentos auxiliares que ainda podiam ser lidos como se P0 fosse apenas preparação arquitetural ou como se P2 adiasse fontes oficiais. Essa leitura contraria `AGENTS.md` e `GOAL.md`, que exigem avanço vertical, conteúdo, páginas públicas aprovadas, Googlebot, sitemap/canonical/robots, escala e continuidade sem pausa.

Consequencia: `ROADMAP_P0_P5.md`, `ARCHITECTURE.md`, `DATA_SOURCES.md`, `LAB_VALIDATION.md`, `CONTENT_QUALITY.md`, `SEO_CRAWL_INDEXING.md` e `content/storage_contract.json` foram endurecidos para exigir cadeia completa de publicação jurídica, fonte resolvida obrigatória em release público, rascunhos permanentes, revisão jurídico-editorial preservada, coleta externa obrigatória para escala e continuidade do mesmo `/goal` após validação.

Autocrítica: a melhoria é real porque remove ambiguidade contratual que poderia transformar checkpoint em pausa ou P0 em laboratório infinito. É segura porque não publica, não toca `public/`, não altera `content/pages.json` nem `published_manifest`, e apenas reforça gates já exigidos. A otimização é de coordenação: reduz perda de contexto e evita falso positivo documental, mas ainda não cria páginas públicas nem resolve os 15 rascunhos prioritários. O próximo avanço executável deve voltar para a vertical P0 material: fonte específica/proveniência dos rascunhos prioritários ou expansão de coleta externa, com subagentes registrados e validação proporcional nos dados reais.

## 2026-06-09 — Go como base propria do portal

Decisao: usar Go e biblioteca padrao como base do projeto.

Motivos:
- linguagem compilada, tipada e adequada a servicos com concorrencia;
- biblioteca padrao suficiente para HTTP, XML, HTML escaping, arquivos e testes;
- binario proprio e operacao sem framework frontend;
- melhor alinhamento com geracao on demand propria e cache controlado pelo projeto.

Evidencia documental consultada:
- `https://go.dev/doc/`: documenta Go como linguagem eficiente, compilada, tipada, com concorrencia e toolchain oficial.
- `https://go.dev/doc/modules/layout`: recomenda `internal/` e `cmd/` para projetos de servidor.
- `https://pkg.go.dev/net/http`: biblioteca padrao para cliente e servidor HTTP.
- `https://pkg.go.dev/encoding/xml`: biblioteca padrao para XML, usada em sitemaps.
- `https://pkg.go.dev/testing`: biblioteca padrao para testes automatizados.

Alternativas avaliadas:
- Python com biblioteca padrao: suficiente para prototipar validadores, mas menos alinhado ao objetivo de portal massivo com binario proprio e geracao HTTP concorrente;
- Next.js ou frameworks frontend: proibidos pelo contrato P0.

Consequencia: qualquer artefato Python criado no ciclo foi descartado; o contrato e a implementacao passam a ser Go-first.

## 2026-06-09 — Geracao on demand propria obrigatoria

Decisao: o portal deve gerar paginas sob demanda com codigo proprio em `internal/ondemand`, sem Next.js, ISR terceirizado ou framework equivalente.

Motivos:
- o projeto quer autonomia sobre roteamento, cache e politica de indexacao;
- rotas futuras podem chegar a milhoes de URLs e nao devem depender de build total;
- o primeiro response de pagina publica deve conter HTML textual completo.

Consequencia: build estatico e permitido como ferramenta operacional, mas nao substitui o gerador on demand. O gerador on demand deve aplicar barreiras próprias: página jurídica indexável precisa de cobertura em `published_manifest`, cache indexável jurídico precisa de assinatura da página e da versão do contrato de render, e cache de página jurídica atual noindex/bloqueada não pode reutilizar HTML antigo indexável.

## 2026-06-09 — Checkpoint nao encerra trabalho

Decisao: checkpoint e rastreabilidade operacional para continuar, nao entrega final nem ordem de parada.

Motivos:
- o projeto tem escopo continuo e grande;
- cada ciclo precisa deixar contexto, provas, falhas e proximo plano;
- o agente deve continuar trabalhando enquanto nao houver bloqueio P0 real.

Consequencia: `CHECKPOINT.md` deve registrar plano de continuidade explicito e nao pode ser usado como substituto da definicao de pronto.

Adendo operacional: sempre planejar o proximo passo e continuar executando. Uma resposta no thread ou um checkpoint nao encerram a missao.

Adendo de persistencia: cada ciclo deve ser commitado apos validacao, incluindo `CHECKPOINT.md`, para preservar continuidade em Git.
Antes do commit, registrar hora local e numero do ciclo no checkpoint.

Adendo de autonomia: Codex atua como engenheiro senior, arquiteto e criador de conteudo juridico. Se houver trabalho no escopo ou bug identificado, deve continuar e corrigir sem pedir aprovacao para decisao normal de engenharia.

## 2026-06-09 — Meta de 10 mil paginas com CTA subordinado a qualidade

Decisao: a meta de produto inclui no minimo 10 mil paginas juridicas informativas, com alta intencao de contratar advogado e CTA proprio de WhatsApp quando classificado por intenção, ética, fonte e revisão.

Motivos:
- o portal deve ter escala nacional e alta intencao comercial;
- a arquitetura precisa suportar grande volume sem URLs infinitas;
- CTA comercial nao pode sacrificar fonte, revisao, utilidade e seguranca juridica.

Consequencia historica superada por contrato posterior: durante P0 o projeto criou plano de blueprints e politica de CTA sem publicar 10 mil paginas juridicas naquele ciclo. Isso nao transforma P0 em espera temporal nem limita o `/goal` a arquitetura; publicacao aprovada deve acontecer neste `/goal` quando release gate completo, fonte, revisao, qualidade, CTA/blocked lane, HTML leve, sitemap/canonical/robots e smoke passarem. A publicacao em escala depende dos gates atuais mais restritivos.

Adendo de precedência atual: esta consequência é histórica e fica subordinada a `AGENTS.md`, `GOAL.md` e às decisões posteriores. P0 não publica sem release gate completo, mas também não é bloqueio temporal contra publicação aprovada. Se fonte oficial específica, revisão jurídico-editorial/OAB, paid-intent/CTA ou bloqueio explícito, qualidade/anti-template, SEO/crawl, HTML leve, `published_manifest`, sitemap/canonical/robots, smoke HTTP/Googlebot e release gate passarem, o Codex deve promover página pública aprovada e continuar rumo ao piso de 10 mil páginas deste `/goal`.

Adendo de intencao digital: alta intencao comercial significa potencial de contratacao juridica 100% online. O primeiro lote de termos deve favorecer problemas juridicos que podem ser triados, documentados e contratados por canais digitais, especialmente WhatsApp. Demanda alta com dependencia presencial predominante nao deve ser tratada como prioridade inicial.

## 2026-06-09 — Laboratorio antes de conteudo e mudancas P0

Decisao: toda mudanca P0/P1 deve passar por laboratorio de testes, validacao, refinamento e reteste.

Motivos:
- scripts isolados podem passar e ainda deixar falha de contrato;
- conteudo juridico exige fonte correta e escrita natural;
- escala de 10 mil paginas sem laboratorio vira risco de spam, duplicidade e baixa qualidade.

Consequencia: `tools/lab-cycle` passa a ser o comando minimo de laboratorio, e conteudo juridico em escala permanece bloqueado ate pesquisa de fonte, documentacao, revisao e gates.

## 2026-06-09 — Fontes como referencia, nao scraping

Decisao: fontes oficiais e APIs publicas registradas sao referencia/proveniencia, nao alvo de scraping, clone ou espelhamento.

Motivos:
- o portal deve ser unico e editorialmente proprio;
- copiar massa de dados ou estrutura oficial cria risco de spam e baixa qualidade;
- conteudo juridico precisa ser natural, humano e contextualizado.

Consequencia: qualquer uso de fonte oficial exige pesquisa critica, registro de proveniencia e redacao propria. Ingestao automatica permanece bloqueada em P0.

## 2026-06-09 — HTML publico leve para bots valiosos

Decisao: pagina publica deve permanecer leve por contrato, com HTML textual completo, CSS minimo e sem runtime cliente.

Motivos:
- Googlebot, OAI-SearchBot e bots valiosos precisam rastrear conteudo textual com baixo custo;
- escala massiva amplifica qualquer excesso de bytes, bundle ou hidratacao;
- framework frontend, payload JavaScript e ferramenta pesada no HTML publico contrariam P0/P1.

Consequencia: `./tools/check-performance-budget` reprova HTML acima do orcamento, `<script>`, referencias a `.js/.mjs/.wasm`, assets pesados, `modulepreload`, import map, marcadores de hidratacao e sinais de runtime/framework. UI publica deve ser resolvida com HTML semantico e CSS minimo.

## 2026-06-09 — Algoritmos auditaveis e explicaveis

Decisao: gates e algoritmos do projeto devem ser inteligentes, auditaveis e explicaveis.

Motivos:
- escala massiva torna heuristica burra perigosa e cara;
- qualidade juridica depende de decisoes rastreaveis, nao de aprovacoes opacas;
- falsos positivos e falsos negativos precisam virar melhoria de algoritmo, nao excecao manual permanente.

Consequencia: quando um algoritmo estiver ingenuo, caro, opaco, permissivo demais ou agressivo demais, o agente deve escrever teste que reproduza a falha, melhorar a regra, manter mensagens especificas de reprovação e registrar a decisao. Heuristicas simples sao permitidas como etapa inicial, mas devem evoluir quando houver sinal melhor disponivel.

## 2026-06-09 — Conteudo publico em PT-BR correto

Decisao: todo conteudo visivel ao publico deve ser escrito em PT-BR com grafia correta, acentuacao correta, pontuacao clara e linguagem natural.

Motivos:
- o portal serve primeiro a humanos no Brasil;
- texto publico sem acento ou com grafia tecnica empobrece confianca editorial;
- qualidade juridica depende de clareza, naturalidade e revisao humana.

Consequencia: rascunhos tecnicos internos podem usar texto operacional sem polimento, mas paginas, metadados visiveis, CTA, navegacao e rodape publicos devem ser PT-BR correto. O algoritmo de normalizacao de qualidade deve preservar letras acentuadas para nao degradar os gates em portugues.

## 2026-06-09 — Orcamento SERP conservador baseado em pesquisa Google

Decisao: o projeto usa limites internos conservadores para `title`, metadescricao e snippet, sem afirmar que sao limites oficiais fixos do Google.

Pesquisa oficial feita no dia da sessao:
- `https://developers.google.com/search/docs/appearance/title-link?hl=pt-BR`
- `https://developers.google.com/search/docs/appearance/snippet?hl=pt-br`
- `https://developers.google.com/search/docs/essentials/technical`

Motivos:
- Google informa que nao ha limite fixo oficial para `<title>` e metadescricoes;
- os textos podem ser truncados conforme a largura do dispositivo;
- conteudo indexavel exige acesso do Googlebot, HTTP 200 e conteudo que nao viole politicas de spam.

Consequencia: `title` deve ter 20 a 65 caracteres Unicode, metadescricao deve ter 70 a 160 caracteres Unicode e paginas indexaveis recebem `max-snippet:160`. Quando faltarem dados atuais sobre Googlebot ou superficie de busca, pesquisar a Central da Pesquisa Google no dia da sessao.

## 2026-06-09 — Laboratorio contra conteudo mecanico antes do Googlebot

Decisao: conteudo raso, mecanico ou criado por permutacao de palavras-chave deve ser detectado em laboratorio antes de qualquer exposicao ao Googlebot.

Motivos:
- a meta de escala nao autoriza spam;
- humanos e Googlebot precisam receber conteudo natural, util e especifico;
- scripts isolados podem ser enganados por texto longo, mas repetitivo.

Consequencia: `./tools/lab-content-quality` cria textos temporarios em `/tmp`, aprova texto natural e reprova texto mecanico. `./tools/check-mechanical-content` bloqueia paginas indexaveis com sinais de thin content, keyword stuffing, baixa diversidade lexical, frases repetidas ou permutacao mecanica. Falsos positivos e falsos negativos devem virar melhoria de algoritmo.

## 2026-06-09 — CPU baixo no runtime publico

Decisao: CPU deve ser reservada para trafego legitimo, Googlebot, OAI-SearchBot e bots valiosos no runtime publico.

Motivos:
- producao precisa atender muitas URLs e bots sem desperdiçar CPU;
- renderizacao publica deve ser previsivel, local e barata;
- laboratorio pode ser mais pesado quando necessario para provar qualidade, mas isso nao pode virar dependencia do atendimento publico.

Consequencia: `./tools/check-cpu-budget` escaneia caminhos de runtime publico/producao e reprova execucao externa, chamadas de rede, sleeps ou loops sem limite. Testes, build, laboratorio e auditorias podem usar comandos mais pesados quando forem necessarios e registrados.

## 2026-06-09 — Modo /goal nao permite parada operacional

Decisao: quando o Codex estiver em modo `/goal`, nao deve parar enquanto houver trabalho no escopo e nao houver bloqueio P0 real comprovado.

Motivos:
- checkpoint e resposta no thread sao rastreabilidade, nao ordem de parada;
- o projeto exige continuidade autonoma e documentada;
- o proximo passo deve sobreviver a compactacao de contexto, troca de sessao e perda de chat.

Consequencia: a primeira linha de `AGENTS.md` registra a regra literal de `/goal`; `GOAL.md`, `CHECKPOINT.md` e documentos de decisao devem manter proximo passo planejado e continuidade explicita. O agente deve executar o proximo passo documentado sem aguardar nova cobranca do usuario, salvo bloqueio P0 real comprovado.

## 2026-06-09 — Sem mascarar pendencia e com rede quando necessaria

Decisao: nenhuma pendencia pode ser mascarada como entrega, e rede deve ser usada quando for necessaria para resolver o escopo.

Motivos:
- registrar bloqueio ou "pendente" como avanço desperdiça ciclo e nao resolve o projeto;
- fontes oficiais, robots.txt, termos de uso, APIs publicas e documentos atuais exigem verificacao real quando impactam decisao;
- sandbox sem rede nao e desculpa para parar quando existe mecanismo de escalonamento pela ferramenta.

Consequencia: Nada deve ser deixado para o futuro por conveniencia. Tudo que estiver no escopo e para esta sessao. Alternativa so e valida quando resolve o requisito ou produz prova executavel que desbloqueia o requisito; artefato que nao sera usado nao conta como entrega. Se a rede do sandbox falhar e a rede for necessaria, o agente deve repetir o comando com `sandbox_permissions=require_escalated` e justificativa objetiva pela ferramenta, sem perguntar no chat. Se o escalonamento for negado, a negativa vira bloqueio real com evidencia, nao pendencia mascarada.

## 2026-06-09 — Fonte especifica por matriz auditada destrava lote bloqueado

Decisao: `refresh-batch-candidate-pipeline` deve promover fonte travada por matriz quando existir URL oficial especifica auditada, em vez de depender de rascunho final preexistente por intent.

Motivos:
- o comportamento anterior travava artificialmente variantes de um mesmo subtema que ja tinham fonte especifica;
- escala massiva exige destravar por prova de fonte e paid-intent, nao por edicao manual de cada pagina;
- a Resolução CNJ 35/2007 foi verificada no portal de atos do CNJ e cobre atos notariais de inventario, partilha, divorcio consensual e uniao estavel por via administrativa.

Consequencia: `batch_source_specificity_resolutions` passou a usar `BuildSpecificSourceURLsByMatrix`; fontes amplas como Codigo Civil, CDC, CLT, raiz de orgao ou home institucional continuam bloqueadas sem URL especifica. O ciclo promoveu 102 candidatos para fonte travada e 102 rascunhos finais bloqueados, mantendo `noindex`, sem render, sem sitemap, sem publicacao e sem scraping/ingestao.

## 2026-06-09 — Ancoras oficiais especificas do Planalto como referencia bloqueada

Decisao: matrizes que ainda dependiam de CLT, Codigo Civil ou CDC amplos podem usar ancoras de artigo em `www.planalto.gov.br/ccivil_03.old/...#art...` como fonte especifica auditada, desde que o uso seja estritamente `reference_only_no_scraping_no_ingestion`.

Motivos:
- o ciclo precisava reduzir o bloqueio de fonte sem mascarar fonte ampla como especifica;
- a propria resposta web do Planalto para a CLT compilada apontou o caminho historico `ccivil_03.old`;
- artigo especifico e uma referencia juridica mais precisa do que a pagina compilada inteira para rescisao, jornada, justa causa, verbas, alimentos, guarda, revisao de pensao, negativacao e cobranca.

Consequencia: o audit URL-level registra robots, termos, hash, timeout HTTP local/escalonado e uso bloqueado; nao ha scraping, ingestao, render, sitemap ou publicacao. A fonte ampla continua na matriz como contexto, mas o destravamento de `final_source_locked_reference_only` passa a exigir a URL de artigo especifica auditada.

## 2026-06-09 — Estrategia de expansao bloqueada antes de ampliar lote

Decisao: quando fonte/readiness deixam de ser gargalo, o proximo passo deve ser registrado em `batch_expansion_strategy` antes de ampliar candidatos, para evitar checkpoint passivo.

Motivos:
- source locked e rascunho final bloqueado nao sao publicacao nem conclusao do `/goal`;
- escala massiva precisa de crescimento real, mas por passos auditaveis para nao virar spam;
- familias prontas devem crescer, enquanto familia com paid-intent reprovado deve preservar bloqueio comercial.

Consequencia: `internal/batchexpansionstrategy`, `data/editorial/batch_expansion_strategy.jsonl`, `cmd/refresh-batch-expansion-strategy`, `./tools/check-batch-expansion-strategy` e `./tools/refresh-batch-expansion-strategy` entram no laboratorio. O plano atual aumenta 5 familias de 30 para 60 candidatos no proximo gate e mantem previdenciario em 18 ate refino/bloqueio comercial, sem render, sitemap, manifest público ou publicação.

## 2026-06-09 — Banco leve separado para ingestao de termos

Decisao: ingestao de termos juridicos pode iniciar conteudos apenas como semente de rascunho, usando banco leve proprio em JSONL e camadas separadas.

Motivos:
- termos juridicos sao uma boa unidade inicial para organizar pautas e glossario sem criar spam;
- fonte auditada, termos de uso, snapshot oficial, rascunho editorial e conteudo publicado tem riscos e contratos diferentes;
- usar Go e arquivos JSONL evita dependencia externa, SDK, SaaS ou banco pesado durante P0.

Consequencia: `content/storage_contract.json` define `term_seeds`, `source_audits`, `source_snapshots`, `editorial_drafts` e `published_manifest`. `./tools/check-storage-contract` reprova camada ausente, caminho compartilhado, arquivo inexistente, record pesado, camada diretamente indexavel ou mistura entre fonte bruta e texto editorial. Termos juridicos so podem iniciar `draft_only` ate fonte, revisao, qualidade, SEO, CTA e checkpoint passarem.

## 2026-06-09 — URL oficial do Portal da Legislacao

Decisao: para o registro Planalto, a URL oficial de pesquisa do Portal da Legislacao passa a ser `https://legislacao.presidencia.gov.br/`, com atos em `https://legislacao.presidencia.gov.br/atos/?...`.

Motivos:
- pagina publica confiavel do proprio `gov.br` para o servico "Realizar pesquisa de legislacao no Portal da Legislacao" aponta o canal Web para `legislacao.presidencia.gov.br`;
- o resultado tambem descreve que a pesquisa acessa atos normativos federais de hierarquia superior e a base REFLEGIS;
- `www.planalto.gov.br` e `www4.planalto.gov.br` sao referencias historicas/auxiliares, mas falharam na auditoria HTTP local desta sessao.

Consequencia: `content/source_registry.json` registra `https://legislacao.presidencia.gov.br/` como base oficial e mantem ingestao bloqueada. A auditoria local teve timeout em `legislacao.presidencia.gov.br`, reset em `www.planalto.gov.br` e timeout em `www4.planalto.gov.br`; portanto a URL foi confirmada documentalmente, mas coleta automatica continua proibida.

## 2026-06-09 — Term seeds como pauta, nao pagina

Decisao: `data/terms/legal_terms.jsonl` pode conter sementes de termos juridicos para laboratorio editorial, desde que cada registro seja `draft_only`, PT-BR, tenha fonte, URL oficial, data de verificacao e intencao editorial.

Motivos:
- termos sao unidade leve para iniciar pauta e glossario sem criar pagina automaticamente;
- uma seed sem fonte vira risco de conteudo juridico inventado;
- um termo publicado direto seria spam ou thin content.

Consequencia: `internal/terms` e `./tools/check-term-seeds` validam as seeds. O laboratorio pode usar essas seeds para rascunhos temporarios, mas nenhuma seed vira pagina publica, CTA ou URL indexavel sem passar pelos demais gates.

## 2026-06-09 — Rascunho temporario antes de pagina publica

Decisao: seed valida pode gerar rascunho temporario em `/tmp` por `./tools/lab-term-draft`, sempre `draft/noindex` e fora do manifesto publico.

Motivos:
- permite testar escrita natural, fonte e aviso informativo antes de tocar o pipeline publico;
- impede que uma seed vire pagina mecanica ou thin content;
- preserva baixo CPU e HTML leve em producao, deixando o experimento no laboratorio.

Consequencia: `internal/draftlab` gera rascunho proprio em PT-BR e roda `quality.AnalyzeText`. O rascunho nao recebe URL publica, nao entra em sitemap, nao recebe CTA e nao altera `content/pages.json`.

## 2026-06-09 — Goal nao termina em ciclo parcial

Decisao: nenhum ciclo e final e parada. `/goal` nao pode ser marcado como completo por checkpoint, commit, laboratorio verde, P0 parcial, seed ou rascunho.

Motivos:
- o objetivo contratado inclui plataforma grande e minimo de 10 mil paginas publicas juridicas aprovadas;
- o projeto ainda esta em P0/laboratorio e nao saiu para publicacao em escala;
- marcar goal como completo em ciclo parcial distorce a missao e causa parada indevida.

Consequencia: `AGENTS.md`, `GOAL.md` e testes de contrato exigem nao marcar `/goal` como completo ate a meta publica minima estar verificada: no minimo 10 mil paginas publicas aprovadas, indexaveis, com fonte, revisao, qualidade, CTA quando cabivel, sitemap/canonical/robots corretos e validacao completa.

## 2026-06-09 — Proibido finalizar goal por ferramenta em P0

Decisao: o agente nao pode chamar `update_goal` com `status=complete` enquanto o projeto estiver em P0/laboratório ou antes de 10 mil paginas publicas juridicas aprovadas e verificadas.

Motivos:
- o goal ativo e a meta publica minima sao maiores que qualquer checkpoint de laboratorio;
- resposta final no thread, commit, check verde ou arquivo persistido nao provam o objetivo real;
- marcar completion por ferramenta encerraria a continuidade operacional contra o contrato.

Consequencia: a primeira linha de `AGENTS.md` e `GOAL.md` explicita a proibicao operacional. `internal/contract/continuity_test.go` reprova se a regra sumir dos contratos. O agente deve deixar o goal ativo, registrar o proximo ciclo e continuar trabalhando enquanto nao houver bloqueio P0 real comprovado.

## 2026-06-09 — Continuidade preserva o objetivo completo apos compactacao

Decisao: quando houver `codex_internal_context`, resumo de retomada, compactação ou subobjetivo, o Codex deve preservar o objetivo completo e nao pode reduzir o objetivo total ao recorte do ciclo atual.

Motivos:
- compactação pode mostrar apenas um subobjetivo e ocultar parte do contexto operacional;
- resposta final no thread é relatório de checkpoint, não é decisão de conclusão;
- checkpoint, commit, teste verde e retomada de ciclo sao rastreabilidade, nao aceite final.

Consequencia: e proibido chamar update_goal status=complete por engano por causa de `codex_internal_context`, compactação, subobjetivo, resposta final, checkpoint ou commit. `AGENTS.md`, `GOAL.md` e `internal/contract/continuity_test.go` devem manter essa regra literal enquanto a meta minima de 10 mil paginas publicas juridicas aprovadas nao estiver comprovada.

## 2026-06-09 — Draft editorial persistido ainda nao e publicacao

Decisao: rascunho validado pode ser persistido em `data/editorial/drafts.jsonl`, mas continua `draft/noindex`, sem rota publica, sem sitemap e sem CTA.

Motivos:
- persistir rascunho reduz perda de contexto entre ciclos sem expor conteudo incompleto;
- separar `editorial_drafts` de `published_manifest` impede que laboratorio seja confundido com pagina publica;
- validacao de qualidade deve acompanhar a persistencia, nao ficar apenas no texto temporario.

Consequencia: `internal/editorialdrafts`, `./tools/persist-term-drafts` e `./tools/check-editorial-drafts` controlam a camada editorial. O fluxo atual e seed -> draft temporario -> draft persistido; ainda nao existe publicacao indexavel desse conteudo.

## 2026-06-09 — Fila editorial antes de promocao

Decisao: draft persistido deve entrar em `data/editorial/review_queue.jsonl` como `needs_review`, com autoria, motivo e historico, ainda com `publication_allowed=false`.

Motivos:
- revisao precisa ser rastreavel antes de qualquer promocao;
- separar fila de revisao de draft e manifesto publicado evita confundir laboratorio com publicacao;
- a meta de 10 mil paginas exige processo repetivel, nao improviso por pagina.

Consequencia: `internal/reviewqueue`, `./tools/queue-editorial-review` e `./tools/check-review-queue` validam a fila. Nenhuma entrada da fila cria URL publica, sitemap, canonical ou CTA.

## 2026-06-09 — Aprovacao editorial ainda nao publica

Decisao: aprovacao editorial de laboratorio fica em `data/editorial/approved_drafts.jsonl` e continua com `publication_allowed=false`, `public_path` vazio e `noindex`.

Motivos:
- aprovacao de texto nao equivale a publicacao tecnica;
- publicacao publica exige fonte especifica, revisao juridica completa, SEO, CTA, sitemap, canonical, robots e escala segura;
- separar aprovacao editorial de manifesto publicado evita salto indevido do laboratorio para Googlebot.

Consequencia: `internal/approvals`, `./tools/approve-editorial-review` e `./tools/check-approvals` validam aprovacao sem publicacao. O proximo contrato deve preparar manifest de publicacao bloqueado antes de qualquer URL publica.

## 2026-06-09 — Manifesto de publicacao bloqueada

Decisao: aprovacao editorial deve gerar manifesto de publicacao bloqueada antes de qualquer URL publica.

Motivos:
- explicitar requisitos faltantes evita mascarar laboratorio como producao;
- publicacao em escala exige lista objetiva de pendencias por termo;
- o fluxo precisa saber quando migrar do laboratorio para host/produção controlada.

Consequencia: `internal/publicationblockers`, `./tools/block-publication` e `./tools/check-publication-blockers` registram `publication_status=blocked`, `publication_allowed=false`, `public_path=""` e requisitos como pesquisa de fonte especifica, revisor juridico real, intencao unica, canonical, SEO, CTA e capacidade de lote.

## 2026-06-09 — Termos humanos de alta intencao antes de conteudo publico

Decisao: quando os gates passarem com seguranca, o agente deve migrar o fluxo para host/produção controlada e priorizar termos juridicos mais pesquisados por humanos e com alta intencao de contratar advogado online.

Motivos:
- o objetivo e portal juridico util e comercial, nao laboratorio infinito;
- termos reais de busca humana reduzem risco de pagina artificial;
- CTA WhatsApp so faz sentido em temas com intencao de contratacao e utilidade juridica clara;
- servicos juridicos digitais sao prioridade: triagem, envio de documentos e contratacao remota devem ser viaveis sem atendimento presencial como padrao.

Consequencia: antes de criar conteudo publico, deve haver pesquisa atual de demanda/intencao, registro no banco leve, fonte confiavel, intencao unica e bloqueio contra spam. Essa regra nao libera publicacao automatica; ela define o proximo movimento apos gates seguros.

## 2026-06-09 — Caminhos seguros para demanda humana

Decisao: usar Google Trends e Google Search Central como caminhos seguros para orientar demanda humana e estrategia, sem tratar esses caminhos como fonte juridica ou como autorizacao de publicacao.

Caminhos registrados:
- Google Trends Explore Brasil: `https://trends.google.com.br/trends/explore?geo=BR`
- Ajuda do Google Trends sobre comparacao: `https://support.google.com/trends/answer/4359550?hl=pt-BR`
- FAQ de dados do Google Trends: `https://support.google.com/trends/answer/4365533?hl=pt-br`
- Google Search Central sobre Trends: `https://developers.google.com/search/docs/monitor-debug/trends-start`

Motivos:
- o Google Trends permite comparar termos e observar interesse de busca, mas seus dados sao normalizados e direcionais;
- a Central da Pesquisa Google orienta usar Trends para estrategia de conteudo sem escrever apenas porque algo esta em alta;
- o projeto precisa escolher termos com demanda humana real antes de criar pauta publica.

Consequencia: `data/terms/intent_candidates.jsonl` deve registrar URL de comparacao, fonte juridica oficial, adequacao a contratacao 100% digital e bloqueio de publicacao. Nenhum candidato vira pagina publica sem novo ciclo de fonte, revisao, qualidade, SEO e CTA.

## 2026-06-09 — Ranking refinavel de termos, sem confiar no primeiro sinal

Decisao: promover candidatos de alta intencao para `term_seeds` por ranking refinavel e testado, nao por lista fixa nem confianca cega em Google Trends.

Motivos:
- um unico sinal de demanda pode ser enganoso, sazonal ou amplo demais;
- termo presencial pode ter volume, mas baixa adequacao ao produto 100% digital;
- fonte nao oficial ou fraca aumenta risco juridico e editorial;
- concentrar todos os termos em uma area reduz aprendizado e escala.

Consequencia: `internal/termpromotion` pontua candidatos, penaliza fonte nao oficial e modo presencial, exige diversidade de areas e preserva evidencia de demanda na seed. `./tools/promote-term-candidates` e `./tools/check-promoted-term-seeds` mantem seeds como `draft_only`, sem URL publica e sem CTA publico.

## 2026-06-09 — Rascunho PT-BR natural tambem no laboratorio

Decisao: rascunhos editoriais persistidos devem usar grafia natural em PT-BR, mesmo antes de publicacao.

Motivos:
- laboratorio e onde erro mecanico deve aparecer, nao no Googlebot;
- texto sem acento ou sem conectivos naturais e sinal de algoritmo burro;
- persistir rascunho ruim aumenta risco de promover conteudo fraco depois.

Consequencia: `internal/draftlab` aplica termo de exibicao natural; `./tools/refresh-editorial-drafts` regenera drafts persistidos apos refinamento; fila de revisao atualiza registros existentes sem liberar publicacao.

## 2026-06-09 — Fonte especifica bloqueia aprovacao

Decisao: termo priorizado com fonte ampla, institucional ou generica nao pode ser aprovado nem publicado ate haver manifesto de fonte especifica resolvido.

Motivos:
- demanda humana e CTA alto nao substituem base juridica correta;
- fonte institucional pode orientar pesquisa, mas texto publico precisa regra, norma, artigo, requisito ou limite juridico aplicavel;
- bloquear aprovacao evita que rascunho de laboratorio vire conteudo publico por engano.

Consequencia: `data/editorial/source_blockers.jsonl` registra `approval_allowed=false`, `publication_allowed=false`, `public_path=""`, requisitos faltantes e proxima pesquisa por termo. `./tools/check-source-specificity-blockers` entra no laboratorio.

## 2026-06-09 — Pesquisa editorial manual antes de scripts de termo

Decisao: a estrategia principal para escolher termos de alta intencao passa a ser pesquisa editorial manual na web, nao script conservador ou gerador de termos.

Motivos:
- termos juridicos de contratacao digital dependem de leitura de intencao humana, nao apenas heuristica;
- Google Trends e util como orientacao direcional, mas nao substitui julgamento editorial;
- fontes oficiais dao autoridade, mas nao sao fonte de demanda nem autorizam clone;
- a meta de 10 mil paginas exige uma base leve, organizada e escalavel sem template mecanico.

Consequencia: `data/research/high_intent_terms.jsonl` vira o banco leve de pesquisa manual; `data/editorial/content_briefs.jsonl` inicia conteudos como briefs nao publicaveis; `./tools/check-manual-keyword-research` e `./tools/check-content-briefs` entram no laboratorio. Nenhum brief vira pagina publica sem fonte especifica, revisao, qualidade, SEO, CTA e nova validacao.

## 2026-06-09 — Rascunhos autorais antes de qualquer pagina de alta intencao

Decisao: briefs pesquisados podem virar rascunhos autorais no banco leve, mas esses rascunhos continuam bloqueados para publicacao ate passarem por fonte especifica, revisao editorial, SEO/crawl, qualidade, CTA e checkpoint.

Motivos:
- o projeto precisa comecar a construir conteudo sem gerar spam, clone ou pagina mecanica;
- Googlebot e humanos devem receber apenas paginas com valor proprio, nao texto de molde;
- CTA WhatsApp e critico, mas deve ser contextual e responsavel;
- a escala de 10 mil paginas exige banco organizado antes de renderizacao publica.

Consequencia: `data/editorial/authorial_drafts.jsonl` vira camada propria de rascunho autoral; `internal/authorialdrafts` e `./tools/check-authorial-content-drafts` reprovam abertura repetida, shape de secoes reaproveitado, heading generico, CTA raso, fonte ausente, publicacao permitida e path publico.

## 2026-06-09 — Resolução de fonte específica antes de pré-publicação

Decisao: fonte específica resolvida deve virar manifesto próprio antes de qualquer contrato de publicação, sem remover automaticamente bloqueadores nem criar URL pública.

Motivos:
- o projeto precisa diferenciar fonte ampla de fonte realmente útil para revisar o texto;
- fontes oficiais devem dar autoridade e proveniência, não texto copiado;
- Googlebot só deve ver página depois de fonte, revisão, qualidade, SEO/crawl e CTA passarem;
- a escala de 10 mil páginas exige rastreabilidade por termo.

Consequencia: `data/editorial/source_resolutions.jsonl` registra a primeira resolução para `negativa-cobertura-plano-saude`; `internal/sourceresolutions` e `./tools/check-source-specificity-resolutions` exigem lei primária, regra de cobertura, fontes oficiais específicas, score mínimo, `noindex`, `publication_allowed=false` e `public_path=""`.

## 2026-06-09 — Gate SEO/crawl de pré-publicação bloqueada

Decisao: uma rota candidata pode ter title, meta description, canonical e path planejados antes de publicar, mas esse planejamento deve ficar em gate bloqueado e nao pode renderizar HTML publico.

Motivos:
- Googlebot deve ver somente paginas realmente aprovadas;
- SEO tecnico deve ser validado antes de render publico, nao depois;
- fonte resolvida nao remove sozinha bloqueio editorial, CTA e revisao juridica;
- a escala de 10 mil paginas exige paths finitos e canonicals planejados sem criar URL prematura.

Consequencia: `data/editorial/prepublication_gates.jsonl` registra a primeira rota candidata para `negativa-cobertura-plano-saude`; `internal/prepublication` e `./tools/check-prepublication-gates` exigem fonte resolvida, blocker ativo, path limpo, canonical HTTPS, `noindex,follow`, title/meta dentro do orcamento, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`.

## 2026-06-09 — Revisão jurídico-editorial bloqueada com CTA contextual

Decisao: CTA WhatsApp e parte critica do produto, mas deve passar por revisao juridico-editorial antes de ficar visivel.

Motivos:
- paginas informativas podem ter alta intencao de contratacao sem prometer resultado;
- CTA agressivo sem fonte e revisao vira risco juridico e conteudo ruim para humanos;
- o fluxo digital precisa pedir documentos relevantes sem induzir expectativa falsa;
- publicar CTA antes dos gates poderia contaminar a pagina e prejudicar confianca.

Consequencia: `data/editorial/legal_reviews.jsonl` registra a primeira revisao bloqueada; `internal/legalreviews` e `./tools/check-legal-editorial-reviews` exigem rascunho autoral, fonte resolvida, gate de pre-publicacao, notas juridicas, correcoes pendentes, CTA WhatsApp sem promessa, mensagem contextual com origem da pagina/rota candidata, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`. `content/cta_policy.json` tambem exige template global com `{path}`, `{unique_intent_id}` e `{title}`.

## 2026-06-09 — Mudança para fábrica massiva de conteúdo único

Decisao: o projeto nao deve depender de revisão humana página a página nem limitar a produção a uma página ou poucas dezenas de rascunhos. A estratégia passa a ser geração massiva por lotes, com validação automática agressiva, score humano/IA-like, reescrita automática e bloqueio de lote quando houver spam, template ou baixa utilidade.

Motivos:
- a meta real é portal jurídico massivo, com potencial para milhões de páginas;
- revisão manual repetitiva não escala;
- conteúdo único e natural precisa ser propriedade do algoritmo, não exceção artesanal;
- Googlebot deve encontrar páginas informativas, úteis e leves, não templates;
- CTA WhatsApp deve ser contextual e lucrativo para advogado, sem transformar o texto em anúncio.

Consequencia: próximos ciclos devem implementar `human_content_score` e `scalable_content_batches`. Cada lote deve gerar muitas intenções únicas de contratação jurídica 100% digital, validar fonte, CTA contextual, score de naturalidade, similaridade intra-lote e bloqueio de publicação. Itens abaixo do score devem ser reescritos automaticamente e revalidados, não entregues ao usuário para correção manual.

## 2026-06-09 — Engenharia agressiva inteligente e autocrítica pré-commit

Decisao: Codex deve operar com engenharia agressiva inteligente: planejar a hipótese, executar sem passividade, validar em massa quando o escopo for massa, refinar algoritmo e registrar autocrítica antes de commitar.

Motivos:
- o contrato do projeto ja define plataforma juridica massiva, alta intencao e contratação digital;
- perguntas desnecessarias e decisões medrosas atrasam o P0;
- commit por ciclo é rastreabilidade, não conclusão do `/goal`;
- massa sem validação em massa vira spam, e validação tímida não prova milhões de páginas;
- o agente precisa registrar a próxima melhoria executável, blocker P0 ou validação necessária antes de preservar o checkpoint.

Consequencia: antes de cada commit, `CHECKPOINT.md` deve registrar o que foi resolvido, provas, autocrítica, pendências reais, próxima melhoria executável, próximo ciclo e a frase operacional de que o commit não encerra o `/goal`. O laboratório pode usar CPU agressivamente para testes, score, reescrita, auditoria e validação em massa; o baixo consumo de CPU continua obrigatório no runtime público/produção.

## 2026-06-09 — Score humano e lotes massivos bloqueados

Decisao: implementar `human_content_score` e `scalable_content_batches` como primeiras camadas executáveis da fábrica massiva de conteúdo jurídico único, mantendo tudo bloqueado para render, sitemap, indexação e publicação.

Motivos:
- o projeto precisa planejar milhões de páginas sem criar spam nem páginas públicas prematuras;
- validação massiva precisa ser artefato executável, não promessa em contrato;
- score humano/IA-like deve orientar reescrita automática e bloqueio de lote;
- CTA WhatsApp contextual precisa nascer no lote com origem e documentos esperados;
- produção continua leve, enquanto laboratório pode usar CPU para score e validação em massa.

Consequencia: `data/editorial/scalable_content_batches.jsonl` registra 1.020.000 páginas planejadas em seis famílias jurídicas digitais, todas bloqueadas. `data/editorial/human_content_scores.jsonl` registra scores humanos/naturalidade sem publicar conteúdo. `internal/humanscore`, `internal/scalablebatches`, `./tools/check-human-content-score` e `./tools/check-scalable-content-batches` entram no laboratório. O próximo ciclo deve gerar drafts em lote e testar reescrita automática de falhas, sem exposição pública.

## 2026-06-09 — Batch drafts com score e reescrita bloqueada

Decisao: implementar `batch_drafts` como camada de rascunhos de amostra por lote massivo, com texto editorial próprio, score humano calculado, prova de reescrita automática em falhas iniciais, baixa similaridade e publicação bloqueada.

Motivos:
- manifestos de milhão de páginas precisam virar amostras editoriais verificáveis antes de qualquer página pública;
- validar em massa sem amostra textual ainda não prova naturalidade, especificidade ou CTA contextual;
- reescrita automática precisa deixar evidência de falha inicial e correção;
- a escala deve evoluir por algoritmo, não por revisão manual página a página;
- Googlebot não deve ver rascunho enquanto score, fonte, revisão, SEO e publicação não estiverem completos.

Consequencia: `data/editorial/batch_drafts.jsonl` registra 18 rascunhos, três por família jurídica de lote, todos `batch_draft_scored_blocked`. `internal/batchdrafts` valida score via `internal/humanscore`, similaridade máxima, reescritas, origem de lote e bloqueio de render/sitemap/publicação. `./tools/check-batch-drafts` entra no laboratório. O próximo ciclo deve transformar amostras em geração programática ampliada e medição agregada por lote.

## 2026-06-09 — Gerador/refinador de batch drafts com métricas agregadas

Decisao: implementar `batchdraftgen` como gerador/refinador determinístico de rascunhos de lote, produzindo amostras temporárias e persistindo métricas agregadas bloqueadas.

Motivos:
- a fábrica massiva precisa gerar e validar lote por comando, não depender de amostras escritas uma a uma;
- reescrita automática deve ser comprovada por falha inicial, score final e métrica agregada;
- métricas por família permitem crescer volume sem mascarar similaridade, IA-like ou baixa especificidade;
- o laboratório pode usar CPU para gerar/refinar, mas nada deve escapar para HTML, sitemap, `public_path` ou publicação;
- CTA WhatsApp precisa nascer com origem de `unique_intent_id` para triagem digital.

Consequencia: `internal/batchdraftgen`, `cmd/generate-batch-drafts`, `./tools/generate-batch-drafts` e `./tools/check-batch-draft-generation` entram no laboratório. `data/editorial/batch_generation_metrics.jsonl` registra 6 métricas de geração bloqueada; o comando gera 30 rascunhos temporários, cinco por família, todos reescritos e com similaridade máxima 0.27 no laboratório. O próximo ciclo deve aumentar o volume por família, cruzar fonte específica por subtema e preparar gate de pré-publicação bloqueada por lote sem publicar.

## 2026-06-09 — Escala semântica com matriz de fontes por subtema

Decisao: ampliar o gerador para 10 amostras por família e criar `batch_source_matrix` como matriz leve de fontes oficiais por subtema, mantendo uso apenas referencial e sem scraping.

Motivos:
- escala maior revelou que similaridade pode subir quando o algoritmo repete vocabulário operacional de laboratório;
- o projeto exige boa semântica por tema/subtema, não mecanização de palavras;
- cada draft de lote precisa carregar fonte oficial específica, documento, risco, ação digital e CTA de origem;
- métricas de escala precisam registrar cobertura de fonte, risco estrutural e custo estimado de laboratório;
- publicar sem matriz de fonte específica criaria risco jurídico e risco de conteúdo raso.

Consequencia: `internal/batchsourcematrix`, `data/editorial/batch_source_matrix.jsonl` e `./tools/check-batch-source-matrix` entram no laboratório. `batchdraftgen` passa a gerar 60 drafts temporários com `source_matrix_id`, cobertura de matriz, risco estrutural e estimativa de CPU de laboratório; a similaridade máxima validada caiu para 0.52 após refinamento semântico. O próximo ciclo deve ampliar a matriz e o gerador para centenas de amostras por família, mantendo fonte específica e publicação bloqueada.

## 2026-06-09 — Auditoria URL-level e centenas de rascunhos por família

Decisao: criar `batch_source_url_audits` e ampliar o gerador para validar 100 amostras por família no laboratório, mantendo publicação bloqueada e sem afrouxar score, similaridade ou fonte.

Motivos:
- matriz de fonte por subtema ainda nao prova auditoria de cada URL oficial usada pelo lote;
- centenas de amostras por família exigem algoritmo semântico, não repetição de três sufixos;
- similaridade precisa diferenciar faceta e subtema, sem confundir metadado bruto com texto editorial;
- testes podem usar CPU no laboratório, mas o runtime público continua leve;
- nenhum rascunho de lote pode virar render, sitemap, `public_path` ou página indexável no P0.

Consequencia: `internal/batchsourceaudit`, `data/source-audit/batch_source_urls.jsonl` e `./tools/check-batch-source-url-audits` entram no laboratório. `batchdraftgen` passa a gerar 600 drafts temporários em teste de contrato, com 100 por família, facetas semânticas distribuídas por subtema, contexto de área, auditoria URL-level e similaridade máxima abaixo do limite de 0.64. `batchdrafts.MaximumPairSimilarity` foi otimizado para pré-computar sinais semânticos e pondera subtema/faceta sem afrouxar o limite. O próximo ciclo deve transformar essa massa temporária em gate de lote candidato, ainda bloqueado, com amostra persistida controlada e pré-publicação sem URL pública.

## 2026-06-09 — Laboratorio aprovado vira arquivo permanente bloqueado

Decisao: rascunhos massivos gerados em `/tmp` que passam nos gates e contêm informação jurídica útil devem ser preservados no repositório como `batch_draft_expansion_archive`, não descartados.

Motivos:
- checkpoint nao pode depender de diretorio temporario ou contexto compactado;
- rascunhos validados podem virar base permanente de páginas futuras depois de expansão, fonte e revisão;
- excluir dados jurídicos úteis sem prova atrasa a fabrica de conteúdo e reduz rastreabilidade;
- persistir no repo nao significa publicar, renderizar, criar sitemap ou liberar CTA público.

Consequencia: `data/editorial/batch_draft_expansion_archive.jsonl`, `internal/batchdraftarchive` e `./tools/check-batch-draft-expansion-archive` entram no laboratório. O arquivo exige 600 rascunhos, 100 por família, `source_matrix_id`, reescrita automática, baixa similaridade e bloqueio total de render/sitemap/publicação. Remoção ou rebaixamento de rascunho validado exige prova em checkpoint e gate próprio.

## 2026-06-09 — URL oficial do projeto ainda nao esta travada

Decisao: tratar `content/site.json` como fonte configuravel da base de canonical/sitemap/robots e marcar a base atual como placeholder de laboratorio, nao URL oficial do produto.

Motivos:
- o projeto ainda esta em P0 e a URL oficial publica nao foi definida;
- testes rigidos por dominio quebrariam a migracao futura sem melhorar SEO;
- canonical continua obrigatorio, mas deve ser validado por base configurada, HTTPS e path limpo;
- pre-publicacao bloqueada pode planejar canonical candidato sem criar URL publica.

Consequencia: `content/site.json` passa a declarar `base_url_mode`, `official_url_status` e `official_url_locked`. `internal/prepublication` valida canonical candidato contra a base carregada de `content/site.json`, e o teste `TestPrepublicationGateAcceptsConfigurableProjectBaseURL` prova que outro dominio HTTPS pode ser aceito sem alterar algoritmo. `portal-juridico.example` so pode ser tratado como placeholder enquanto `base_url_mode="lab_placeholder"`.

## 2026-06-09 — Gate candidato bloqueado a partir do arquivo permanente

Decisao: criar `batch_candidate_gates` como etapa intermediaria entre arquivo permanente de rascunhos e pre-publicacao, selecionando candidatos reais sem publicar.

Motivos:
- o arquivo de 600 rascunhos precisa virar continuidade operacional, nao ficar apenas como massa bruta;
- seleção de candidato nao pode ser confundida com URL publica, sitemap ou CTA visivel;
- a URL oficial ainda nao esta travada, entao o gate precisa respeitar `base_url_mode`;
- cada candidato deve existir no arquivo permanente, carregar CTA contextual e continuar vinculado a fonte matricial.

Consequencia: `data/editorial/batch_candidate_gates.jsonl`, `internal/batchcandidategates` e `./tools/check-batch-candidate-gates` entram no laboratorio. O gate exige 6 famílias, 3 intenções selecionadas por família, 100 registros mínimos no arquivo por lote, similaridade <=0.64, score humano mínimo, base URL flexível e flags públicas falsas. O próximo ciclo deve transformar candidatos selecionados em revisão jurídico-editorial por candidato, ainda sem render público.

## 2026-06-09 — URL oficial travada em wikijuridica.com.br

Decisao: travar a URL oficial do projeto como `https://wikijuridica.com.br` e remover o placeholder `portal-juridico.example` dos canonicals e gates vivos.

Motivos:
- o usuario definiu `wikijuridica.com.br` como dominio oficial do projeto;
- canonical, sitemap e robots precisam de base real antes de evoluir pre-publicacao;
- testes continuam lendo `content/site.json` para evitar algoritmo hardcoded, mas o contrato agora exige `official_configured`;
- URL oficial travada nao e autorizacao para publicar candidatos de lote ou rascunhos.

Consequencia: `content/site.json` passa para `base_url_mode="official_configured"`, `official_url_status="locked"` e `official_url_locked=true`. `content/pages.json`, `data/editorial/prepublication_gates.jsonl` e `data/editorial/batch_candidate_gates.jsonl` acompanham a base oficial. O proximo ciclo deve manter candidatos bloqueados e preparar pre-publicacao em lote apenas depois de fonte e revisao especificas.

## 2026-06-09 — Revisao juridico-editorial bloqueada de candidatos de lote

Decisao: criar `batch_candidate_reviews` como camada obrigatoria entre `batch_candidate_gates` e qualquer pre-publicacao em lote.

Motivos:
- selecionar candidato nao basta para preparar pagina juridica publica;
- cada candidato precisa de revisao juridico-editorial, CTA WhatsApp contextual e fonte matricial auditada;
- escala massiva nao pode depender de revisao manual pagina a pagina, mas a revisao algoritmica precisa deixar rastro por candidato;
- URL oficial travada nao remove os gates de fonte, qualidade, SEO e publicacao;
- promessa de resultado, CTA raso, path com dominio e fonte nao auditada precisam reprovar antes de qualquer render.

Consequencia: `data/editorial/batch_candidate_reviews.jsonl`, `internal/batchcandidatereviews`, `./tools/check-batch-candidate-reviews`, `internal/checks` e `tools/lab-cycle` entram no laboratorio. O gate exige 18 revisoes bloqueadas, uma por intencao selecionada, com `Origem`, `Gate` e `Intent` na mensagem de WhatsApp, matriz auditada, notas especificas e flags publicas falsas. O proximo ciclo deve transformar essas revisoes em pre-publication gates de lote com canonical oficial e `noindex`, ainda sem sitemap/publicacao.

## 2026-06-09 — Validacao global proporcional ao risco

Decisao: tratar `./tools/go-modern test -count=1 ./...`, `./tools/check-all`, `./tools/lab-cycle` e equivalentes completos como validacao global de alto custo, nao como ritual automatico para toda alteracao pequena.

Motivos:
- validacao global consome tempo e pode atrasar ciclos localizados;
- engenharia agressiva exige prova suficiente, nao excesso de ritual;
- mudancas pequenas podem ser comprovadas com teste focado, check especifico, diff check e inspecao direta;
- mudancas amplas ou criticas ainda exigem prova global para evitar regressao em varias camadas.

Consequencia: o proximo ciclo deve escolher validacao proporcional. Rodar validacao global quando houver alteracao ampla, contrato central, risco P0/P1 critico, HTML/sitemap/canonical/robots/indexacao/performance, gerador em massa, preparacao de publicacao ou falha transversal. Em ciclos localizados, registrar no checkpoint os checks focados usados e por que eles cobrem o risco.

## 2026-06-09 — Pre-publicacao bloqueada para candidatos revisados

Decisao: criar `batch_prepublication_gates` como etapa posterior a `batch_candidate_reviews`, registrando canonical oficial, `noindex,follow`, title/meta e pendencias finais sem publicar.

Motivos:
- revisao juridico-editorial de candidato ainda nao equivale a pagina publica;
- a URL oficial ja esta travada e deve aparecer no canonical candidato;
- Googlebot nao deve receber candidatos enquanto fonte final, revisao SEO, manifesto publico e render/sitemap nao forem aprovados;
- pre-publicacao em lote precisa ser validada por candidato, nao por suposicao global.

Consequencia: `data/editorial/batch_prepublication_gates.jsonl`, `internal/batchprepublication`, `./tools/check-batch-prepublication-gates`, `internal/checks` e `tools/lab-cycle` entram no laboratorio. O ciclo usa validacao focada por politica proporcional: teste do contrato novo, tool especifica, storage contract, checks internos e diff check; validacao global fica reservada para alteracao ampla ou risco critico.

## 2026-06-09 — Especificidade de fonte por candidato pre-publicado

Decisao: criar `batch_source_specificity_resolutions` como camada obrigatoria depois de `batch_prepublication_gates`, cobrindo cada candidato com fonte final travada como referencia ou bloqueio explicito por fonte ampla.

Motivos:
- matriz de fonte auditada nao basta para dizer que todo candidato esta pronto;
- fonte institucional ampla nao pode ser mascarada como fonte final;
- candidatos com URL oficial especifica podem avancar para o proximo gate bloqueado sem scraping, ingestao ou publicacao;
- candidatos com fonte ampla precisam registrar motivo, detalhe necessario e permanecer fora de render/sitemap/publicacao.

Consequencia: `data/editorial/batch_source_specificity_resolutions.jsonl`, `internal/batchsourcespecificity`, `./tools/check-batch-source-specificity`, `internal/checks`, `content/storage_contract.json` e `tools/lab-cycle` entram no laboratorio. O gate exige 18 resolucoes, uma por candidato pre-publicado, fonte URL-level auditada, politica `reference_only_no_scraping_no_ingestion`, `candidate_robots=noindex,follow`, canonical oficial e flags publicas falsas. O ciclo usa validacao proporcional focada; `check-all` e `lab-cycle` ficam reservados para alteracao ampla ou risco transversal.

## 2026-06-09 — Manifesto publico bloqueado por candidato de lote

Decisao: criar `batch_public_manifest_gates` como camada bloqueada depois de `batch_source_specificity_resolutions`, cobrindo todos os candidatos e permitindo avanço interno para SEO/conteudo final apenas quando a fonte esta travada.

Motivos:
- fonte travada ainda nao autoriza publicacao, render ou sitemap;
- candidatos com fonte ampla nao podem entrar em revisao SEO como se estivessem prontos;
- o pipeline precisa separar backlog de fonte de backlog de SEO/conteudo;
- manifesto publico real deve ser posterior e mais restrito que este gate bloqueado.

Consequencia: `data/editorial/batch_public_manifest_gates.jsonl`, `internal/batchpublicmanifest`, `./tools/check-batch-public-manifest-gates`, `internal/checks`, `content/storage_contract.json` e `tools/lab-cycle` entram no laboratorio. O gate exige 18 registros, 7 com `public_manifest_blocked_seo_review_pending` e 11 com `public_manifest_blocked_source_specificity`, mantendo `index_policy=noindex`, `manifest_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`.

## 2026-06-09 — Rascunho autoral final bloqueado e intenção paga

Decisao: criar `batch_final_authorial_drafts` apenas para os candidatos com fonte travada e manifesto SEO pendente, e adicionar `paid-intent` como gate de negócio para impedir funil de gratuidade, curiosidade ou baixa intenção de contratação.

Motivos:
- rascunho final não é publicação, mas precisa virar artefato permanente para escalar conteúdo;
- CTA WhatsApp deve carregar origem, intenção, documentos e sinal de contratação particular;
- serviço jurídico comercial precisa priorizar busca com honorários/orçamento, valor envolvido, urgência e documentos concretos;
- termos de gratuidade, defensoria, justiça gratuita, estudo acadêmico, modelo pronto ou curiosidade não devem alimentar o lote comercial;
- inferência aceitável é textual e jurídico-econômica do termo/caso, não perfil pessoal sensível.

Consequencia: `data/editorial/batch_final_authorial_drafts.jsonl`, `internal/batchfinaldrafts`, `internal/paidintent`, `./tools/check-batch-final-authorial-drafts`, `./tools/check-paid-intent`, `internal/checks`, `content/storage_contract.json` e `tools/lab-cycle` entram no laboratorio. Todos os 7 rascunhos seguem `noindex`, sem render, sem sitemap, sem publicação e sem `public_path`; o gate pago deve ser refinado quando surgir falso positivo/negativo antes de escalar.

## 2026-06-09 — Agentes auxiliares planejados sem concorrência crítica

Decisao: no próximo ciclo e nos seguintes, usar agentes auxiliares é obrigatório quando houver duas ou mais frentes independentes, especialmente pesquisa de fontes oficiais, matriz de proveniência, testes, conteúdo bloqueado e debugging, mas sem concorrência no estado do repositório.

Motivos:
- a meta massiva exige acelerar pesquisa e produção sem perder validação;
- fontes oficiais e conteúdo por subtema podem ser divididos por área/fonte;
- concorrência no mesmo arquivo, gate, commit, fonte jurídica ou decisão crítica aumenta risco de conflito e mascaramento;
- o Codex principal deve manter responsabilidade por arquitetura, P0/P1, integração, validação, checkpoint e commit.

Consequencia: agentes devem produzir pesquisa, evidência, teste, edição disjunta ou rascunho em escopo isolado. Se houver escrita, ela precisa ser disjunta e só entra no repo após validação do Codex principal. O Codex principal valida evidência, revisa o diff, roda os checks relevantes, registra checkpoint e não publica nada sem gate. Para não perder contexto em compactação, todo agente usado em ciclo deve virar registro em `.agents/agent_context_ledger.jsonl` antes do checkpoint/commit.

## 2026-06-09 — Ledger persistente contra perda de contexto de agentes

Decisao: criar `.agents/agent_context_ledger.jsonl` e `./tools/check-agent-context-ledger` como contrato operacional para preservar contexto de subagentes entre compactações.

Motivos:
- compactação pode remover IDs, achados, riscos e decisões de integração dos agentes;
- pesquisa de fonte oficial e revisão de conteúdo precisam sobreviver ao próximo ciclo;
- agente auxiliar não pode virar prova invisível nem autorização implícita;
- o Codex principal precisa conseguir retomar sem refazer pesquisa ou confiar em memória solta.

Consequencia: cada agente usado deve registrar ciclo, ID real, apelido, tipo de tarefa, escopo, status, política de uso, resumo, evidências, riscos, decisão de integração e flags `repo_write_allowed`, `codex_validation_required=true`, `closed_before_checkpoint` ou `context_kept_open=true` com `kept_open_reason`. A política padrão é `reference_only_no_repo_write`; escrita por agente só é válida com `delegated_repo_write_codex_validated`, escopo disjunto, evidência do diff, riscos, fechamento antes do checkpoint ou contexto preservado intencionalmente, e validação/integração pelo Codex principal. `internal/agentcontext` valida o ledger; `check-all` e `lab-cycle` passam a incluir esse gate.

Adendo historico do ciclo 46, atualizado pela política proporcional de 2026-06-25: em ciclo de escala com duas ou mais frentes independentes, usar agentes auxiliares em paralelo deixa de ser opcional. O Codex principal deve acionar ondas coordenadas pela concorrência real da ferramenta, da sessão, do contexto e da segurança operacional para pesquisa, teste, auditoria, documentação, conteúdo bloqueado ou edição disjunta, mantendo a chefia técnica nos críticos; a antiga contagem fixa foi substituida por decisao proporcional registrada, sem teto operacional artificial quando houver frentes independentes reais. Todo agente precisa deixar contexto durável em `.agents/agent_context_ledger.jsonl`; compactação, memória do chat ou checkpoint genérico não bastam.

## 2026-06-09 — Timing e otimização obrigatórios antes de commit

Decisao: teste lento não pode ser tratado como normal sem medição. Criar `cmd/profile-tests`, `internal/testprofile`, `./tools/profile-contract-tests` e fazer `tools/lab-cycle` medir cada etapa com `TIMING`, removendo duplicação de `check-all` e checks individuais já cobertos por `cmd/check all`.

Motivos:
- `internal/contract` chegou a 207,365s em medição por `go test -json`;
- gargalos reais eram revalidação editorial upstream e similaridade de 600 drafts, não falta de vontade de usar CPU;
- `lab-cycle` repetia `go test`, `check-all` e vários checks individuais;
- otimização precisa preservar contrato, não mascarar gate.

Consequencia: antes de commit com teste/gate lento, rodar perfil ou registrar timing. O ciclo otimizado usa `./tools/go-modern test -count=1 ./...`, `./tools/go-modern run ./cmd/check all` e ferramentas de laboratório não cobertas pelo check-all. `batchdrafts` evita alocação de mapa de união em Jaccard e validadores finais deixam de reconstruir índice upstream duas vezes no mesmo caminho. Medição pós-otimização de `./tools/profile-contract-tests`: `total_observed_seconds=17.02`, `slow_tests=0` com threshold de 5s.

## 2026-06-09 — Gate pago persistente e fonte geral como fonte ampla

Decisao: intenção comercial paga agora fica registrada em `batch_paid_intent_gates`, e fontes legais gerais como Código Civil, CDC e CLT compilada não destravam recortes específicos sozinhas.

Motivos:
- CTA com honorários não basta quando o tema dominante indica assistência pública, gratuidade provável ou autoatendimento administrativo;
- BPC/LOAS, CadÚnico, renda familiar, baixa renda e cumprimento de exigência precisam de bloqueio comercial explícito antes de escalar conteúdo; vulnerabilidade isolada nao basta para inferir assistencia publica;
- fonte ampla pode ser referência oficial, mas não substitui ato, súmula, regra, serviço ou orientação específica para o subtema;
- agentes auxiliares podem acelerar pesquisa oficial e rascunho bloqueado, mas o Codex principal precisa validar evidência, integração e gates críticos.

Consequencia: `./tools/check-paid-intent` valida o arquivo permanente `data/editorial/batch_paid_intent_gates.jsonl`; candidatos comerciais fortes continuam bloqueados para publicação, e candidatos com risco de assistência pública ou self-service ficam roteados para bloqueio comercial. `./tools/check-batch-source-specificity` trata `codigo_civil`, `codigo_consumidor` e `clt_compilada` como fontes amplas quando o recorte precisa de fonte específica. O próximo ciclo deve criar prontidão de expansão de candidatos, usando agentes sem concorrência crítica para pesquisar fontes oficiais e ampliar conteúdo bloqueado com validação pelo Codex principal.

## 2026-06-09 — Prontidao de expansao bloqueada por paid gate

Decisao: criar `batch_candidate_expansion_readiness` como camada entre o arquivo permanente de 600 rascunhos e a seleção candidata ampliada, com alvo inicial de 30 candidatos por família e bloqueio explícito quando faltar paid-intent por intenção.

Motivos:
- o projeto precisa sair de 18 candidatos rumo a dezenas/centenas por família sem publicar spam;
- `batch_draft_expansion_archive` já prova massa útil, mas não prova que cada intenção expandida tem paid gate, fonte específica e CTA aptos;
- CTA colado não pode salvar candidato fraco, e paid-intent ausente deve ser blocker acionável;
- readiness precisa sobreviver ao checkpoint e orientar agentes auxiliares sem concorrência no mesmo gate.

Consequencia: `data/editorial/batch_candidate_expansion_readiness.jsonl`, `internal/batchcandidateexpansion` e `./tools/check-batch-candidate-expansion-readiness` entram no laboratório. O gate registra 6 famílias com 30 alvos cada, mas mantém status `batch_candidate_expansion_blocked_paid_gate_missing` enquanto as intenções expandidas não tiverem `batch_paid_intent_gates`. Nenhum registro permite manifesto, render, sitemap, publicação ou `public_path`.

## 2026-06-09 — Paid gate em lote e bloqueio CTA-only

Decisao: gerar `batch_paid_intent_gates` para os 180 alvos de `batch_candidate_expansion_readiness`, adicionar `gate_scope` para separar rascunho final de prontidao de expansao, e bloquear candidato cujo sinal de contratacao paga aparece apenas no CTA/WhatsApp.

Motivos:
- paid-intent ausente e paid-intent existente mas reprovado sao diagnosticos diferentes;
- CTA contextual e importante, mas CTA colado nao pode salvar corpo informativo sem intencao de contratacao natural;
- o algoritmo precisa explicar se reprovou por CTA-only, sinal pago ausente, baixa pontuacao de negocio, gratuidade, pesquisa sem contratacao, assistencia publica dominante ou autoatendimento;
- `vulnerabilidade` isolada e termo juridico amplo e nao deve inferir assistencia publica sem BPC/LOAS, CadUnico, renda familiar, baixa renda, defensoria ou justica gratuita.

Consequencia: `data/editorial/batch_paid_intent_gates.jsonl` agora tem 180 registros bloqueados, `internal/paidintent` separa `paid_signals` do corpo e `cta_paid_signals` do CTA, `cmd/generate-paid-intent-gates` materializa o banco leve e `cmd/refresh-expansion-readiness` recalcula os contadores de prontidao. `batch_candidate_expansion_readiness` passa a usar `batch_candidate_expansion_blocked_paid_gate_failed` quando nao falta gate, mas ainda ha bloqueio comercial. O proximo ciclo deve reescrever/refinar em lote os candidatos bloqueados por CTA-only ou sinal pago ausente, sem liberar render, sitemap, publicacao ou `public_path`.

## 2026-06-09 — Refinamento pago em lote sem publicar

Decisao: criar `batch_paid_intent_refinements` e `internal/paidintentrefinement` para reescrever em lote apenas candidatos com paid-intent ausente ou CTA-only, movendo sinal de contratacao paga para o corpo informativo quando natural e mantendo o ledger bloqueado.

Motivos:
- CTA WhatsApp contextual e critico, mas sinal de honorarios somente no CTA nao basta para escalar conteudo;
- paid-intent ausente/CTA-only pode ser corrigido por algoritmo quando o tema permite contratacao particular online;
- BPC/assistencia publica dominante e autoatendimento administrativo continuam bloqueios comerciais, nao alvos de refinamento;
- script de laboratorio precisa ser idempotente para nao falhar quando o ciclo ja foi aplicado;
- readiness sem blocker antigo de paid/fonte precisa apontar o proximo gate real, nao ficar com blocker vazio.

Consequencia: `./tools/refine-paid-intent-drafts` refinou 140 registros na primeira aplicacao (135 no arquivo permanente de expansao e 5 rascunhos finais), `./tools/check-paid-intent-refinements` entrou no check-all, `batch_paid_intent_gates` passou a registrar 168 candidatos pagos bloqueados para publicacao, 6 bloqueios de assistencia publica e 6 bloqueios de autoatendimento. `batch_candidate_expansion_readiness` usa `batch_candidate_gate_pending` quando a familia esta livre de paid/source blockers antigos, mas continua `noindex`, sem manifesto, render, sitemap, publicacao ou `public_path`. O proximo ciclo executavel e ampliar `batch_candidate_gates` a partir dos candidatos pagos aprovados internamente, mantendo bloqueio publico e fonte especifica como gates.

## 2026-06-09 — Expansao candidata de 168 e refresh idempotente da cadeia bloqueada

Decisao: `batch_candidate_gates` deve ser expandido por algoritmo a partir de `batch_candidate_expansion_readiness` e `batch_paid_intent_gates`, e a cadeia downstream deve ser regenerada por `refresh-batch-candidate-pipeline`, nunca por edicao manual de JSONL em massa.

Motivos:
- ampliar de 18 para 168 candidatos sem propagar revisao, pre-publicacao, fonte especifica e manifesto quebra o contrato P0;
- paid-intent aprovado internamente nao equivale a publicacao, pois fonte especifica e revisao ainda podem bloquear;
- rascunhos finais bons devem ser preservados quando continuam elegiveis, mas BPC/assistencia publica e autoatendimento devem sair da cadeia candidata paga;
- a meta de 10k/milhoes exige ferramenta idempotente, nao ajuste manual lento.

Consequencia: `./tools/expand-batch-candidate-gates` seleciona 168 intenções pagas bloqueadas; `./tools/refresh-batch-candidate-pipeline` materializa 168 revisoes, 168 prepublication gates, 168 resolucoes de fonte e 168 manifestos, preservando 5 rascunhos finais elegiveis e bloqueando 163 por fonte especifica. Todos permanecem `noindex`, sem render, sitemap, publicacao ou `public_path`.

## 2026-06-09 — Expansao 318 com current separado do next target

Decisao: `batch_candidate_expansion_readiness` pode carregar o próximo alvo planejado pela estratégia, mas `batch_candidate_gates` só deve materializar o `current_candidate_count` da estratégia no ciclo atual.

Motivos:
- readiness com alvo 90 por família precisa existir para o próximo ciclo e para gerar paid gates antecipados;
- selecionar todos os paid-passed da readiness no mesmo ciclo saltaria de 318 para 468 candidatos sem checkpoint próprio;
- `ApplyStrategy` não pode trocar IDs sem recomputar paid counts, blockers, status e current count;
- expansão agressiva precisa ser rápida, mas cada salto de escala deve ser rastreável, validado e bloqueado para publicação.

Consequencia: `internal/batchexpansionapply` passou a recalcular cada readiness record após aplicar a estratégia; `internal/batchcandidatepromotion` limita a seleção ao `strategy.CurrentCandidateCount`; `batch_paid_intent_gates` cobre 480 registros incluindo próximos alvos; `batch_candidate_gates` permanece com 318 candidatos materializados; reviews, prepublication, source-specificity, public manifest e final drafts permanecem em 318, todos `noindex`, sem render, sitemap, publicação ou `public_path`. O próximo ciclo deve promover o alvo 90 das cinco famílias prontas para nova materialização validada, mantendo previdenciário bloqueado por paid-intent.

## 2026-06-09 — Lane previdenciaria informativa bloqueada

Decisao: previdenciario pode crescer por uma lane informativa/curiosa bloqueada, sem exigir alta intencao de pagamento, desde que a excecao fique restrita a `batch-previdenciario-digital` e nunca publique, renderize, entre em sitemap ou crie `public_path`.

Motivos:
- temas previdenciarios como BPC/LOAS, CadUnico, exigencia do INSS e autoatendimento podem ter utilidade humana e demanda real mesmo quando nao mostram alta intencao paga;
- tratar essa demanda como lixo comercial reduziria crescimento de familia juridica relevante;
- afrouxar a regra global criaria risco de spam, funil de gratuidade e selecao fraca nas familias comerciais;
- a excecao precisa ser status proprio, auditavel e bloqueada, nao mascaramento de paid-intent aprovado.

Consequencia: `internal/paidintent` cria `paid_intent_flexible_previdenciario_informational_blocked_publication` e centraliza elegibilidade em `paidintent.AllowsExpansion`, que aceita o status apenas em `batch-previdenciario-digital` e com flags publicas falsas. `internal/batchexpansionapply`, `internal/batchcandidateexpansion`, `internal/batchcandidatepromotion` e `internal/batchcandidatepipeline` usam esse helper. `batch_candidate_gates` sobe para 330 candidatos internos bloqueados; `batch_paid_intent_gates` cobre 510 alvos de laboratorio, com 42 previdenciarios informativos bloqueados; `batch_expansion_strategy` planeja proximo crescimento para 510 current total, sendo 90 nas cinco familias comerciais e 60 em previdenciario. Gratuidade explicita, defensoria/justica gratuita, "sem pagar", promessa de beneficio, promessa de resultado ou substituicao de canal publico continuam bloqueios P0.

## 2026-06-09 — Avanco explicito para 510 candidatos bloqueados

Decisao: criar `./tools/advance-batch-candidate-gates` para promover explicitamente o `next_candidate_target` planejado por `batch_expansion_strategy`, sem mudar o comportamento conservador de `./tools/expand-batch-candidate-gates`.

Motivos:
- o contrato atual separa current de next target para impedir salto implicito no mesmo checkpoint;
- o ciclo 47 precisava materializar 510 candidatos, mas isso deveria ser uma acao explicita, rastreavel e validada;
- reaproveitar `expand-batch-candidate-gates` como salto automatico quebraria a decisao anterior e poderia mascarar crescimento sem checkpoint;
- a meta massiva exige comando rapido de avancar lote, com teste e regeneracao downstream, nao edicao manual de JSONL.

Consequencia: `internal/batchcandidatepromotion` passa a ter `AdvanceToNextTargets`, mantendo `ExpandFromReadiness` como selecao current; `cmd/advance-batch-candidate-gates` e `tools/advance-batch-candidate-gates` materializam o next target quando a estrategia esta pronta. `batch_candidate_gates` sobe para 510 candidatos internos bloqueados: 90 em cada uma das cinco familias comerciais e 60 em previdenciario. A cadeia downstream sobe para 510 revisoes, prepublication gates, source-specificity, manifests e final drafts, todos `noindex`, sem render, sitemap, publicacao ou `public_path`. `batch_paid_intent_gates` passa a cobrir 590 alvos de laboratorio para o proximo crescimento planejado.

## 2026-06-09 — Flexibilidade previdenciaria por curiosidade qualificada

Decisao: previdenciario informativo nao precisa de alta intencao de pagamento para crescer internamente no laboratorio, desde que haja curiosidade qualificada, utilidade humana e bloqueio publico total.

Motivos:
- previdenciario tem demanda humana real em beneficios, CNIS, pericia, exigencia, prazo, documento e revisao, mesmo quando a pessoa ainda esta curiosa ou em fase administrativa;
- bloquear toda curiosidade previdenciaria reduziria crescimento de familia juridica relevante e impediria cobertura informativa util;
- afrouxar a regra geral criaria risco comercial em consumidor, familia, saude, sucessorio e trabalhista;
- a excecao precisa continuar auditavel, com status proprio e sem publicacao.

Consequencia: `batch-previdenciario-digital` pode usar `paid_intent_flexible_previdenciario_informational_blocked_publication` para crescer familias previdenciarias bloqueadas. Famílias comerciais continuam exigindo intencao paga particular ou bloqueio explicito. Gratuidade explicita, defensoria/justica gratuita, "sem pagar", promessa de beneficio, promessa de resultado e substituicao de canal publico continuam bloqueios P0. A lane previdenciaria permanece `noindex`, sem render, sitemap, publicacao ou `public_path`.

Adendo: famílias comerciais também são informativas. Não retirar o conteúdo informativo da plataforma jurídica; a intenção natural de contratação deve ser incorporada por cenário jurídico, documentos, risco econômico, urgência, honorários/orçamento e CTA contextual, sem transformar a página em oferta seca.

## 2026-06-12 — Escala massiva exige unicidade, não repetição

Decisao: a meta mínima de 10 mil páginas públicas jurídicas não é teto, nem sinônimo de duplicação, permutação de template, texto artificial, thin content ou spam. A plataforma deve ser projetada para crescer para centenas de milhares ou milhões de URLs quando houver demanda real, fonte verificável, intenção única, conteúdo autoral, revisão, HTML leve e validação massiva.

Motivos:
- escala grande é requisito de produto e engenharia, não desculpa para degradar qualidade;
- Googlebot e leitores humanos detectam repetição estrutural, páginas sem valor adicional, textos mecânicos e baixa utilidade;
- automação só é aceitável quando aumenta capacidade de pesquisa, diferenciação, revisão, prova e bloqueio seguro;
- se o volume reduz unicidade, naturalidade, precisão jurídica ou leveza, o problema está no algoritmo, no dado ou no gate.

Consequencia: ciclos futuros devem tratar aumento de volume e qualidade como o mesmo problema técnico. O caminho correto é criar melhores geradores, bases, validadores, scores, diagnósticos, amostragem e reescrita, mantendo publicação bloqueada até prova. Não limitar o projeto por receio de escala, mas também não avançar volume quando o lote estiver mecânico, duplicado, raso, pesado ou juridicamente fraco.

Autocrítica histórica deste checkpoint: a pergunta "O que podemos melhorar, e por que? É seguro? É otimização real? É teste real sem falso positivo ou negativo?" fica preservada como eixo de revisão daquele ciclo, não como formulário rígido nem substituto da execução verificável atual.

## 2026-06-09 — OAB, autoria configurada e atendimento jurídico digital

Decisao: o projeto deve tratar atendimento jurídico 100% digital, tudo online, sem sair de casa, envio remoto de documentos, WhatsApp contextual e atendimento a brasileiros fora do Brasil como modo real de prestação jurídica digital; isso não é promessa de resultado, é realidade brasileira quando usado como descrição objetiva do atendimento.

Pesquisa oficial feita no dia da sessao:
- `https://www.oab.org.br/leisnormas/legislacao/provimentos/205-2021`
- `https://www.oab.org.br/publicacoes/AbrirPDF?LivroId=0000004085`

Motivos:
- o Provimento OAB 205/2021 permite marketing jurídico compatível com a ética da OAB e define marketing de conteúdos jurídicos como criação/divulgação de conteúdo jurídico voltado a informar o público;
- o mesmo Provimento exige informação objetiva, verdadeira, sobriedade e veda captação, mercantilização, valores, gratuidade/descontos, expressões persuasivas, autoengrandecimento, promessa de resultados e casos concretos como oferta;
- o anexo do Provimento admite criação de conteúdo, artigos, ferramentas tecnológicas e chatbot para facilitar comunicação/coleta de dados sem suprimir a pessoalidade do advogado;
- o Código de Ética e Disciplina exige publicidade informativa, internet como veículo lícito com limites, e nome/OAB na publicidade profissional.

Consequencia: gates não devem reprovar termos como 100% digital, tudo online, sem sair de casa ou atendimento remoto quando forem descrição do fluxo. Devem reprovar garantia de êxito, liminar garantida, resultado certo, prazo prometido, comparação, captação indevida, caso concreto usado como oferta, sensacionalismo, valores, descontos e gratuidade. Autor dos conteúdos: Rafael Toledo, OAB/RJ 227191; a identidade fica em `content/site.json` como configuração versionada, não hardcoded em runtime.

## 2026-06-09 — Avanco 590 com refino semantico e archive esgotado explicito

Decisao: o avanço interno de 510 para 590 candidatos bloqueados só pode ocorrer depois de teste semântico específico contra repetição previdenciária e refresh completo da cadeia downstream.

Motivos:
- `--expect-total` evita salto acidental, mas não prova qualidade semântica;
- a lane previdenciária informativa pode crescer por curiosidade qualificada, mas não pode manter abertura, documentos, triagem e CTA repetidos;
- final drafts antigos podem ser reutilizados pelo pipeline se o reuso não detectar padrão legado;
- cinco famílias comerciais chegaram a 100/100 registros do archive, então fingir próximo crescimento sem novo archive seria pendência mascarada.

Consequencia: `batch_final_authorial_drafts` passa a exigir variação semântica mínima em previdenciário e o pipeline reconstrói finais previdenciários legados usando problema do leitor, documentos, risco e ação digital do rascunho selecionado. `batch_candidate_gates` sobe para 590 candidatos internos bloqueados, com cadeia downstream em 590 e flags públicas falsas. `batch_expansion_strategy` ganha `batch_expansion_strategy_blocked_archive_growth_required` para famílias com current igual ao archive observado; o próximo ciclo deve gerar mais `batch_draft_expansion_archive` permanente, bloqueado, semântico e validado antes de novo avanço.

## 2026-06-09 — Archive 780, anti-mascaramento e estratégia 770

Decisao: expandir o arquivo permanente bloqueado para 780 rascunhos, 130 por família, usando perfis semânticos de expansão e similaridade profile-aware, e registrar anti-mascaramento como regra explícita do próximo agente.

Motivos:
- o ciclo anterior expôs cinco famílias comerciais no limite de 100/100 do archive; crescer sem novo archive seria pendência mascarada;
- rascunho temporário de laboratório que passa nos gates e contém informação jurídica útil deve vir para o repositório como dado permanente bloqueado;
- apenas trocar faceta ou palavra não basta para escala; cada rodada acima de 100 precisa de eixo semântico novo, documento, risco, fonte, problema do leitor e CTA contextual;
- paid-intent não pode depender só do CTA; o corpo informativo precisa carregar sinal natural de contratação particular quando a família é comercial;
- teste verde não substitui leitura técnica do contexto, do texto gerado, dos blockers, da fonte e da semântica jurídica.

Consequencia: `cmd/generate-batch-drafts` ganha `--write-archive`; `internal/batchdraftgen` valida antes de escrever archive permanente; `internal/batchdrafts` passa a entender perfis de expansão na similaridade; `internal/batchcandidateexpansion` atualiza contadores reais de archive e similaridade; `data/editorial/batch_draft_expansion_archive.jsonl` fica com 780 registros; `batch_paid_intent_gates` cobre 770 alvos; `batch_paid_intent_refinements` registra 529 refinamentos; readiness e strategy ficam prontos para o próximo candidate gate. O estado público continua bloqueado: sem render, sitemap, publicação, `public_path` ou `index`.

Regra operacional: quando houver bug de contrato, falso positivo, falso negativo, dado stale, métrica suspeita ou conteúdo que passe no script mas pareça raso, mecânico, sem contexto ou comercial demais, a correção correta é investigar, refinar algoritmo/teste/dado e revalidar. É proibido baixar limite, remover blocker, renomear status ou aceitar script isolado como verdade P0/P1. O próximo ciclo deve materializar o avanço explícito de 590 para 770 candidatos bloqueados, regenerar a cadeia downstream e validar sem publicar.

## 2026-06-09 — Dados reais antes de inferência no algoritmo de conteúdo

Decisao: nenhum ajuste de similaridade, n-grama, título, termo, paid-intent, CTA ou expansão de lote pode ser feito por inferência no escuro. O laboratório deve primeiro expor dados reais do erro e só então alterar gerador, comparador ou gate.

Motivos:
- o ciclo de archive 780 mostrou que similaridade alta podia vir de campos concretos repetidos, não de limite baixo;
- título/termo repetido em várias seções gera n-grama mecânico e não pode ser tratado como diversidade semântica;
- algoritmo de conteúdo precisa entender área jurídica e contexto, evitando confundir tema de família/pensão com trabalhista por token solto;
- afrouxar limite ou filtrar token sem diagnóstico mascara spam, falso positivo ou falso negativo.

Consequencia: testes e diagnósticos de lote devem mostrar par/registro que falhou, `legal_area`, `source_matrix_id`, `unique_intent_id`, campos textuais, blocker, score e código gerador antes de refinamento. Se faltar dado, o próximo passo é instrumentar diagnóstico ou teste. Se o teste estiver certo, corrigir geração/conteúdo; se for falso positivo, fortalecer o comparador sem reduzir limite e mantendo teste negativo.

## 2026-06-09 — Lab aprovado vira repo permanente bloqueado

Decisao: artefato aprovado no laboratório não pode ficar apenas em `/tmp` quando tem valor para páginas futuras. Antes do commit do ciclo, rascunho, métrica, fonte ou conteúdo de lote que passou com segurança deve ser trazido para camada versionada do repositório, sempre bloqueado para publicação.

Motivos:
- rascunhos aprovados contêm informação jurídica e contexto útil para expansão futura;
- depender de `/tmp`, chat ou compactação desperdiça prova e quebra continuidade;
- mover para repo não significa publicar, renderizar, indexar ou criar sitemap;
- descarte de dado útil só é válido com prova e gate específico.

Consequencia: o ciclo 50 materializou no repo `batch_draft_expansion_archive` com 780 registros, métricas em `batch_generation_metrics`, `batch_paid_intent_gates` com 770, `batch_paid_intent_refinements` com 529, readiness e strategy em 6 famílias. Tudo permanece em camadas editoriais bloqueadas, sem `content/pages.json`, sem `public_path`, sem render, sem sitemap, sem publicação e sem `index`.

## 2026-06-09 — Archive 1.140 com diversidade de matriz e avanço 1.140

Decisao: expandir o arquivo permanente bloqueado para 1.140 rascunhos, 190 por família, somente depois de novo gate de diversidade por `source_matrix_id`, reparo de especificidade documental e validação do gerador acima de 160 por família.

Motivos:
- o archive de 960 ainda repetia 4-gramas dentro das mesmas matrizes de fonte, mesmo com intenção única;
- reduzir cue sem diagnóstico enfraquecia especificidade e criava risco de texto raso;
- a correção correta era fazer o gerador usar sinais reais do caso matriz, documento, fonte, risco e ação digital, sem baixar limite de similaridade;
- artefato validado no laboratório não pode ficar apenas em `/tmp` quando contém dado jurídico útil para páginas futuras;
- paid-intent stale depois de refinamento é bug de ordem, não blocker a mascarar; a cadeia deve ser regenerada até ficar idempotente antes de qualquer advance.

Consequencia: `internal/batchdrafts.ValidateSourceMatrixDiversity` passa a reprovar dominância de 4-grama e baixa diversidade por campo dentro de cada `source_matrix_id`; `internal/batchdraftgen` gera cues discriminativos por campo e acrescenta reparo de especificidade por área apenas quando o score acusa `low_specificity`; `data/editorial/batch_draft_expansion_archive.jsonl` fica com 1.140 registros; `batch_generation_metrics` registra 190 por família; `batch_paid_intent_gates` cobre 1.140; `batch_paid_intent_refinements` registra 827 e fica idempotente após regeneração; `batch_candidate_gates` avança para 1.140 com cadeia downstream completa em 1.140. O orçamento leve de `batch_candidate_gates` sobe para 32KB porque 190 IDs por família passam de 16KB, mas isso não é solução de escala infinita: antes de crescimento muito maior, o gate deve ser particionado por shard/tier ou registro candidato. O estado público continua bloqueado: sem render, sitemap, publicação, `public_path` ou `index`. O próximo ciclo deve gerar novo archive semântico acima de 190 por família, revalidar diversidade intra-matriz, regenerar paid/readiness/strategy e só então avançar além de 1.140.

## 2026-06-09 — Archive 1.320, concorrência de agentes e avanço 1.320

Decisao: expandir o arquivo permanente bloqueado para 1.320 rascunhos, 220 por família, e avançar `batch_candidate_gates` para 1.320 somente depois de dry-run limpo, persistência explícita, paid gates em 1.320, refinamento idempotente, readiness/strategy verdes e cadeia downstream bloqueada em 1.320.

Motivos:
- dry-run 220 isolado comprovou 1.320 rascunhos com similaridade máxima 0.60 sem alterar o repo;
- artefato aprovado em laboratório deve ser persistido no repo, não ficar apenas em `/tmp`;
- refinamento de paid-intent alterou o archive e exigiu regenerar paid gates antes de aceitar readiness;
- um subagente executou `git restore` e `rm` no workspace compartilhado sem autorização do Codex principal, apagando uma tentativa local de expansão; isso é falha operacional P0 de concorrência e não pode se repetir;
- `batch_candidate_gates` com 220 IDs por família ainda cabe em 32KB, mas a maior linha chegou a 22.173 bytes e confirma necessidade de particionamento antes de escala muito maior.

Consequencia: `data/editorial/batch_draft_expansion_archive.jsonl`, `batch_paid_intent_gates`, `batch_candidate_reviews`, `batch_prepublication_gates`, `batch_source_specificity_resolutions`, `batch_public_manifest_gates` e `batch_final_authorial_drafts` ficam com 1.320 registros bloqueados; `batch_paid_intent_refinements` registra 969 refinamentos; `batch_expansion_strategy` volta para `batch_expansion_strategy_blocked_archive_growth_required` em todas as famílias porque current=archive=220. Contratos de agentes passam a proibir `git restore`, `git checkout`, `rm`, reset, limpeza, snapshot substitutivo ou retorno de estado para apagar tentativa, reduzir diff ou ocultar erro; conflito deve ser resolvido editando para frente, com causa raiz, dados derivados recalculados e validação proporcional. O próximo ciclo deve particionar `batch_candidate_gates` ou provar limite seguro antes de crescer muito acima de 220 por família.

## 2026-06-10 — Candidate gates shardados, idempotentes e bloqueados

Decisao: particionar `batch_candidate_gates` em shards físicos antes de novo crescimento, mantendo o contrato lógico por 6 famílias e 1.320 candidatos bloqueados agregados.

Motivos:
- a maior linha de `batch_candidate_gates` em 1.320 chegou a 22.173 bytes e não escalaria para 10k+ sem linha gigante;
- baixar regra ou aceitar 32KB como solução permanente mascararia gargalo de storage;
- normalização não idempotente poderia remover metadados de shard e duplicar `gate_id` em execução futura;
- `WriteRecords` precisava validar o conjunto normalizado antes de substituir o JSONL, para não truncar arquivo em falha tardia;
- reviews/prepublication carregam `gate_id` físico, então mudar shards exige regenerar downstream e validar paridade.

Consequencia: `internal/batchcandidategates` passa a normalizar por `gate_group_id`, `shard_index`, `shard_count` e `selected_total`, com limite `MaxSelectedIntentIDsPerRecord=120`, validação global de `gate_id`, seleção duplicada, índice faltante/duplicado e total divergente. `WriteRecords` valida em memória e escreve via arquivo temporário/rename. `batch_candidate_gates.jsonl` passa de 6 para 12 linhas físicas, mantendo 1.320 candidatos lógicos bloqueados, maior linha 12.978 bytes e `record_max_bytes=16.384`. `batch_candidate_reviews` e `batch_prepublication_gates` foram regenerados para os `gate_id` shardados. O estado público continua bloqueado: sem render, sitemap, publicação, `public_path` ou `index`. O próximo ciclo deve crescer o archive acima de 220 por família, regenerar paid/refinement/readiness/strategy e avançar candidatos em shards sem ultrapassar orçamento leve.

## 2026-06-10 — Expansao bloqueada para 1.500 candidatos e similaridade otimizada sem afrouxar gate

Decisao: crescer o arquivo permanente bloqueado para 250 rascunhos por família, total 1.500, e avançar candidate gates para 1.500 em shards, mantendo publicação bloqueada e reduzindo custo de similaridade sem mudar o score aceito.

Motivos:
- o contrato vigente naquele ciclo limitava avanço a +30 por família, então 250 por família foi o degrau histórico correto após 220;
- rascunho aprovado em laboratório precisa ir para repo permanente quando tem valor futuro, portanto `batch_draft_expansion_archive` e métricas foram atualizados, não deixados em `/tmp`;
- `refine-paid-intent-drafts` altera o archive, então paid gates precisam ser recalculados depois do refinamento;
- readiness calculada antes do advance fica stale depois que candidate gates sobem de 220 para 250; por isso readiness e strategy devem ser rodadas novamente após `advance-batch-candidate-gates`;
- `MaximumPairSimilarityDetail` era o gargalo dominante em 1.500 registros; pular Jaccard semântico apenas quando `source_matrix_id` difere é equivalente porque `maximumSimilarityScore` já retorna somente `textScore` nesse caso.

Consequencia: `batch_draft_expansion_archive`, `batch_paid_intent_gates`, `batch_candidate_reviews`, `batch_prepublication_gates`, `batch_source_specificity_resolutions`, `batch_public_manifest_gates` e `batch_final_authorial_drafts` ficam com 1.500 registros bloqueados; `batch_candidate_gates` fica com 18 shards físicos; `batch_paid_intent_refinements` fica com 1.114 registros. `internal/batchdrafts` mantém threshold de similaridade, adiciona teste para a equivalência de matrizes diferentes, aumenta cache de fingerprints para 32 worksets e reduz o perfil de contratos para cerca de 29s. O estado público continua bloqueado: sem alteração em `content/pages.json`, sem diff público, sem `render_allowed=true`, `sitemap_allowed=true`, `publication_allowed=true` ou `public_path`. A continuidade imediata histórica apontava crescimento para 280 por família, total 1.680, com a mesma ordem: dry-run, write archive/metrics, paid, refinement, paid, readiness, strategy, advance esperado, readiness/strategy pós-advance, pipeline downstream, checks e checkpoint.

## 2026-06-10 — Expansao bloqueada para 1.680 com diversidade por rodada

Decisao: crescer para 280 rascunhos por família, total 1.680, somente depois de corrigir o gerador para variar documento, risco e ação digital por facet e perfil de rodada.

Motivos:
- o dry-run inicial de 280 reprovou corretamente por `generation_batch_draft_matrix_document_diversity_low` e `generation_batch_draft_matrix_risk_diversity_low`, com várias matrizes em 0.38/0.39;
- baixar threshold de diversidade mascararia conteúdo mecânico, então a correção precisava melhorar o algoritmo;
- o limite real era a assinatura inicial dos campos, ainda dominada pelo facet, enquanto o perfil de rodada aparecia tarde demais;
- combinar pista do facet com pista da rodada no início de `DocumentContext`, `RiskContext` e `DigitalAction` aumenta diversidade sem remover n-grama, sem reduzir score e sem publicar nada.

Consequencia: `internal/batchdraftgen` passa a misturar pista primária e secundária em perfis de rodada; `internal/contract` ganha teste para geração diversa em 280 por família. O dry-run de 280 passou com `generated_drafts=1680`, `rewritten=1680` e `max_similarity=0.61`; o archive permanente, paid gates, candidate gates, reviews, prepublication, source-specificity, manifest e final drafts ficam em 1.680 registros bloqueados. `batch_candidate_gates` continua em shards físicos dentro do orçamento leve. O estado público continua bloqueado: sem alteração em `content/pages.json`, sem diff público e sem flags públicas verdadeiras. O próximo ciclo deve crescer para 310 por família, total 1.860, mantendo teste de diversidade, paid/refinement/readiness/strategy, advance esperado, refresh pós-advance, pipeline e checks completos.

## 2026-06-10 — Expansao bloqueada para 1.860 e readiness leve derivado do archive

Decisao: crescer para 310 rascunhos por família, total 1.860, e corrigir `batch_candidate_expansion_readiness` para não armazenar a lista completa de intenções por família.

Motivos:
- o dry-run e a escrita permanente de 310 por família passaram com `generated_drafts=1860`, `rewritten=1860` e `max_similarity=0.61`;
- rascunho aprovado em laboratório deve ir para o repo permanente bloqueado, portanto archive e métricas foram materializados antes do commit;
- `check-storage-contract` reprovou corretamente `batch_candidate_expansion_readiness:1` por linha JSONL acima de 32KB, mostrando que guardar 310 IDs completos no readiness era bug de escala;
- aumentar orçamento ou ignorar storage mascararia o problema e voltaria em 2.040/10k+;
- a lista completa já existe no archive permanente e pode ser derivada por `batch_id` + `target_candidate_count` sem perder validação.

Consequencia: `batch_draft_expansion_archive`, paid gates, candidate gates, reviews, prepublication, source-specificity, public manifest e final drafts ficam com 1.860 registros bloqueados. `batch_candidate_expansion_readiness` passa a gravar `expansion_candidate_selector=archive_prefix_by_batch` e amostra curta, enquanto `batchcandidateexpansion.CandidateIntentIDs`, `batchcandidatepromotion` e `paidintent` derivam os alvos completos do archive. Testes novos impedem readiness pesado e provam promoção por alvos derivados. O estado público continua bloqueado: sem alteração em `content/pages.json`, sem diff público, sem `render_allowed=true`, `sitemap_allowed=true`, `publication_allowed=true` ou `public_path`. O próximo ciclo deve crescer para 340 por família, total 2.040, mantendo storage leve, diversidade, paid/refinement/readiness/strategy, advance esperado, refresh pós-advance, pipeline, checks completos e otimização do gargalo de similaridade/readiness.

## 2026-06-11 — Expansao bloqueada para 2.040 com diversidade em 340 por familia

Decisao: crescer para 340 rascunhos por familia, total 2.040, somente depois de corrigir o gerador para manter diversidade por `source_matrix_id`, consertar datas stale em readiness/strategy e revalidar a cadeia bloqueada inteira.

Motivos:
- o primeiro dry-run de 340 reprovou `generation_similarity_too_high`, provando que avanço por volume sem ajuste criaria risco de texto mecânico;
- baixar limite ou aceitar par similar mascararia bug editorial, então o ciclo adicionou teste de contrato para 340 por família e corrigiu a escolha de perfil de rodada;
- `checked_at` antigo em readiness/strategy confundia o estado real do lote, então os regeneradores passaram a gravar 2026-06-11;
- paid gates, readiness e strategy precisam ser recalculados na ordem correta depois de refinamento e advance; arquivo stale não pode destravar expansão;
- expressão repetida em rascunho final previdenciário mostrou que teste verde não basta sem ler o conteúdo, então o polish final foi ajustado e a cadeia regenerada.

Consequencia: `batch_draft_expansion_archive`, `batch_paid_intent_gates`, `batch_candidate_reviews`, `batch_prepublication_gates`, `batch_source_specificity_resolutions`, `batch_public_manifest_gates` e `batch_final_authorial_drafts` ficam com 2.040 registros bloqueados; `batch_candidate_gates` permanece em 18 shards físicos; `batch_candidate_expansion_readiness` e `batch_expansion_strategy` ficam com 6 registros leves e `checked_at=2026-06-11`. O estado público continua bloqueado: sem alteração em `content/pages.json`, sem diff em `public/`, sem `render_allowed=true`, `sitemap_allowed=true`, `publication_allowed=true` ou `public_path`. O próximo ciclo deve crescer para 370 por família, total 2.220, mantendo algoritmo semântico, paid/refinement/readiness/strategy na ordem correta, refresh pós-advance, pipeline downstream, timing, scans públicos e checkpoint sem concluir o `/goal`.

## 2026-06-11 — Release transacional em staging, fonte resolvida e promoção bloqueada

Decisao: o caminho futuro de publicação deve passar por `internal/publicrelease` com plano transacional, staging auditável e promoção bloqueada por padrão.

Motivos:
- `published_manifest`, `content/pages.json` e `public/` não podem ser alterados por atalho enquanto o release gate completo não existir;
- hashes de HTML e sitemap devem ser calculados pelo builder a partir do plano, não aceitos do chamador;
- fonte oficial específica deve enriquecer a proveniência por URL normalizada de forma conservadora, sem perder a URL escolhida pelo rascunho;
- em release público jurídico, `RequireResolvedSources` deve estar ativo e toda fonte selecionada precisa ter resolução específica, ou o release deve bloquear;
- staging só vira prova se tiver relatório auditável, e esse relatório só é forte se os arquivos staged reais também tiverem hash revalidado;
- promoção para `public/` deve permanecer bloqueada por padrão até existir release gate final, sitemap público completo, smoke HTTP e autorização técnica explícita.

Consequencia: `BuildPlanFromReleaseEvidence` carrega identidade editorial versionada, fonte resolvida, calcula artefatos em `.release-staging/public` e valida a transação. `MaterializeStaging` escreve somente em staging e gera `.release-staging/staging_report.jsonl`. `ValidateStagingReport` compara relatório e plano. `BuildPromotionPlan` exige transação, relatório, hashes staged, hash do relatório e raiz única de staging antes de preparar promoção, preservando cópia defensiva da transação, raiz pública final, diretório temporário público fora de `public/`, snapshot de rollback do estado público existente, artefatos públicos finais planejados, sitemap final planejado a partir das páginas existentes mais a transação e artefatos de dados finais planejados para `content/pages.json` e `published_manifest`, preservando registros existentes, anexando a transação validada e bloqueando conflito de path, intenção ou manifest ID já existente. `PromoteStagingToPublic` usa esse plano preparado, reprova plano stale quando o relatório muda e revalida os hashes dos artefatos staged no momento final, mas retorna `public_release_promotion_blocked_by_default` antes de qualquer escrita pública. Staging validado não é publicação, não entra em sitemap e não altera `published_manifest`.

## 2026-06-11 — Validação do diretório isolado de promoção planejada

Decisao: antes de qualquer troca futura em `public/`, o diretório isolado de promoção deve ser validado contra os artefatos finais planejados pelo `PromotionPlan`.

Motivos:
- staging validado prova a renderização preparada, mas não prova que o conjunto final materializado para promoção contém exatamente os arquivos finais esperados;
- `content/pages.json`, `published_manifest` e sitemap final dependem de mescla com estado existente e precisam ser conferidos por hash antes de qualquer escrita pública;
- arquivo faltante, divergente ou inesperado no diretório isolado de promoção deve bloquear a cadeia antes de tocar em `public/`.

Consequencia: `ValidateTemporaryPublicPlan` compara caminhos relativos ao repositório e SHA-256 de `PlannedPublicArtifacts` e `PlannedPublicDataArtifacts` contra o diretório isolado de promoção, rejeitando `public_release_temporary_public_artifact_missing`, `public_release_temporary_public_artifact_sha256_mismatch` e `public_release_temporary_public_artifact_unexpected`. A validação é apenas prova de preparação: não publica, não atualiza sitemap público, não altera `content/pages.json` e não grava `published_manifest`.

## 2026-06-11 — Materialização isolada da promoção planejada

Decisao: o plano de promoção pode materializar o destino isolado a partir dos artefatos staged e dos dados finais mesclados, mas a troca real para `public/` continua bloqueada.

Motivos:
- validar o diretório isolado exige uma etapa própria que gere os bytes finais esperados, sem depender de helper de teste ou montagem manual;
- lixo antigo no destino isolado precisa ser removido antes da validação para não esconder arquivos inesperados;
- evidência de promoção e rollback precisa sobreviver fora do diretório de artefatos para ser revalidada antes de qualquer swap;
- materializar destino isolado ainda não satisfaz release gate final, smoke HTTP, rollback real ou autorização técnica de publicação.

Consequencia: `MaterializeTemporaryPublicPlan` recria apenas o diretório isolado dentro de `.release-staging`, fora de `public/` e fora do staging renderizado, copia HTML staged validado, renderiza sitemap final com páginas existentes mais transação, grava `content/pages.json` e `published_manifest` finais mesclados, chama `ValidateTemporaryPublicPlan` e persiste `.release-staging/promotion_manifest.json` com status bloqueado, SHA do staging report, raízes, artefatos planejados e snapshot de rollback. A função não escreve em `public/`, não muda `content/pages.json` real e não remove `public_release_promotion_blocked_by_default`.

## 2026-06-11 — Plano de swap público ainda bloqueado

Decisao: a cadeia de release pode descrever operações de swap e rollback, mas a execução real continua bloqueada por padrão.

Motivos:
- antes de qualquer troca futura, o projeto precisa saber exatamente quais arquivos sairiam do diretório isolado e quais destinos seriam afetados;
- snapshot de rollback precisa acompanhar o plano executável, não ficar apenas como evidência solta no `PromotionPlan`;
- swap planejado sem manifesto de promoção perde rastreabilidade durável entre staging report, artefatos temporários e rollback;
- swap planejado e execução bloqueada precisam deixar ledger de etapa antes de qualquer escrita pública, para diferenciar plano montado de execução validada;
- o ledger precisa carregar uma tentativa derivada do manifesto e horário auditável para preparar lock/recovery futuro;
- descrever operações não equivale a publicar, porque ainda faltam release gate final, smoke HTTP, rollback real testado e autorização técnica explícita.

Consequencia: `BuildPromotionSwapPlan` exige diretório isolado validado e manifesto de promoção íntegro antes de montar `PromotionSwapOperation` com path lógico, origem isolada, destino final e SHA-256 esperado, preservando `RollbackSnapshot` e `PromotionManifestSHA256`, e anexa `swap_plan_built` em `.release-staging/promotion_execution_ledger.jsonl` com `attempt_id`, `owner_pid`, `owner_hostname`, `recorded_at`, hash do manifesto, contagens, `previous_record_sha256` e `record_sha256`. Antes de cada append, o ledger existente é revalidado linha a linha por cadeia SHA-256; corrupção, remoção ou reordenação detectável retorna `public_release_promotion_execution_ledger_invalid`. Manifesto ausente retorna `public_release_promotion_manifest_missing`; manifesto divergente retorna `public_release_promotion_manifest_mismatch`; manifesto alterado depois do swap plan retorna `public_release_promotion_manifest_sha256_mismatch`. `ExecutePromotionSwapPlan` revalida staging, hash do relatório, diretório isolado, SHA do manifesto e manifesto de promoção, adquire `promotion_lock.json` por criação exclusiva com `attempt_id`, SHA do manifesto, `owner_pid`, `owner_hostname`, `acquired_at` e `lease_expires_at` de 15 minutos, reprova segunda execução ativa por `public_release_promotion_lock_exists`, diagnostica lease válido expirado por `public_release_promotion_lock_stale`, reprova lock corrompido por `public_release_promotion_lock_invalid`, não remove nem reaproveita lock existente e não anexa nova linha no ledger quando para por lock; apenas lock recém-adquirido anexa `swap_execution_validated` e então retorna `public_release_promotion_blocked_by_default`. Lock expirado não é reaproveitado automaticamente até existir recovery validado; não renomeia arquivos, não altera `public/`, não muda dados reais e não libera indexação.

Atualizacao 2026-06-11: `BuildPromotionLockRecoveryPlan` prepara apenas recovery bloqueado de lock expirado: revalida swap plan, temporary public, manifesto, SHA, operações e ledger, exige `attempt_id` derivado do manifesto, congela `PromotionLockEvidence`, path e SHA-256 de `promotion_lock.json`, `observed_at`, último `record_sha256`, contagem e resumo da última linha `swap_execution_validated` do ledger. Rejeita lock ativo por `public_release_recovery_lock_active`, divergência de lock por `public_release_recovery_lock_mismatch` e divergência de ledger por `public_release_recovery_ledger_mismatch`. `ExecutePromotionLockRecoveryPlan` revalida as evidências e retorna `public_release_recovery_blocked_by_default`; não remove `promotion_lock.json`, não anexa linha no ledger, não renova lock e não escreve em `public/`.

## 2026-06-11 — Swap plan com snapshot defensivo da promoção

Decisao: `PromotionSwapPlan` deve congelar a promoção preparada por cópia defensiva própria, não carregar slices mutáveis do `PromotionPlan` recebido.

Motivos:
- o plano de swap é a evidência executável mais próxima da futura troca pública e não pode ser contaminado por mutação posterior do chamador;
- o executor bloqueado deve reprovar plano stale real, mas não pode transformar alteração externa em falso blocker como `public_release_missing_author`;
- antes de qualquer execução real, operações e rollback precisam ser snapshot auditável.

Consequencia: `BuildPromotionSwapPlan` passa a armazenar `clonePromotionPlan`, copiando transação, artefatos públicos planejados, artefatos de dados planejados e rollback snapshot. Mutação posterior do `PromotionPlan` original não altera o resultado de `ExecutePromotionSwapPlan`; o bloqueio default permanece e nenhuma escrita pública é feita.

## 2026-06-11 — Operações de swap revalidadas contra artefatos congelados

Decisao: `ExecutePromotionSwapPlan` deve validar cada `PromotionSwapOperation` contra os artefatos planejados congelados antes de retornar o bloqueio default.

Motivos:
- uma operação adulterada não pode chegar ao bloqueio default como se o plano continuasse íntegro;
- origem isolada, destino final e SHA-256 esperado são parte do contrato de swap, não detalhes derivados descartáveis;
- antes de qualquer execução real, divergência de operação deve ser diagnosticada como plano inválido.

Consequencia: o executor compara quantidade, duplicidade, origem isolada, destino, path lógico e SHA-256 das operações contra `PlannedPublicArtifacts` e `PlannedPublicDataArtifacts` do snapshot. Operação alterada, inesperada ou duplicada retorna `public_release_promotion_plan_invalid`; nenhuma escrita pública é feita.

## 2026-06-11 — Plano de rollback simulado e bloqueado

Decisao: a cadeia de promoção deve modelar rollback a partir do snapshot público congelado antes de qualquer execução real, mas a restauração continua bloqueada por padrão.

Motivos:
- snapshot de rollback só é útil como contrato executável quando vira operações verificáveis;
- paths de restauração precisam ser relativos ao repositório e não podem escapar para fora da árvore controlada;
- simular rollback não equivale a restaurar arquivos reais nem autoriza publicação.

Consequencia: `BuildPromotionRollbackPlan` revalida o swap plan, transforma cada `PublicFileSnapshot` em `PromotionRollbackOperation` com path de snapshot, destino absoluto e SHA-256, rejeita snapshot vazio, duplicado ou com path inválido e congela o swap plan por cópia defensiva. `ExecutePromotionRollbackPlan` revalida as operações e retorna `public_release_rollback_blocked_by_default`; nenhuma escrita em `public/`, `content/pages.json` ou `published_manifest` é feita.

Atualizacao 2026-06-11: `BuildPromotionRollbackPlan` tambem exige e congela evidencia de `promotion_lock.json` com `attempt_id`, SHA do manifesto, PID, hostname e lease; lock ausente retorna `public_release_rollback_lock_missing`. `ExecutePromotionRollbackPlan` revalida o lock em disco contra essa evidencia e retorna `public_release_rollback_lock_mismatch` se ela mudou. O rollback continua bloqueado por padrão e não remove, restaura, renova lock nem escreve em `public/`.

## 2026-06-11 — Rollback bloqueado revalida plano stale

Decisao: `ExecutePromotionRollbackPlan` deve revalidar o staging, o hash do relatório, o diretório isolado e as operações de swap antes de retornar o bloqueio default de rollback.

Motivos:
- rollback futuro depende do mesmo plano de promoção que seria revertido;
- relatório de staging alterado depois do build do rollback não pode ser mascarado por `public_release_rollback_blocked_by_default`;
- executor bloqueado também deve diagnosticar stale plan antes de qualquer autorização real.

Consequencia: se `.release-staging/staging_report.jsonl` mudar depois da preparação do rollback, `ExecutePromotionRollbackPlan` retorna `public_release_promotion_plan_stale`. O bloqueio default continua existindo apenas depois que promotion/swap/rollback permanecem íntegros; nenhuma escrita pública é feita.

## 2026-06-11 — Snapshot de rollback duplicado invalida plano

Decisao: `ExecutePromotionRollbackPlan` deve reprovar duplicidade no snapshot congelado antes do bloqueio default.

Motivos:
- mapa de operações não pode esconder duas entradas de snapshot com o mesmo path;
- snapshot duplicado torna a ordem e a intenção de restauração ambíguas;
- contrato de rollback precisa diagnosticar plano corrompido, não tratá-lo como bloqueio normal.

Consequencia: `validatePromotionRollbackOperations` detecta path duplicado em `Swap.RollbackSnapshot` e retorna `public_release_rollback_plan_invalid`. O executor não escreve em `public/` e não altera dados publicados.

## 2026-06-11 — Rollback inclui remoção de artefatos novos

Decisao: o plano de rollback deve representar arquivos que seriam criados pela promoção e que não existiam no snapshot público anterior.

Motivos:
- restaurar apenas arquivos existentes antes da promoção deixa sobras públicas novas após uma falha parcial;
- rollback real precisa diferenciar restauração de snapshot e remoção de artefato criado;
- o SHA-256 do artefato criado deve acompanhar a remoção planejada para auditoria antes de qualquer execução.

Consequencia: `PromotionRollbackOperation` passa a ter `RemoveIfCreated`. `BuildPromotionRollbackPlan` adiciona operações de remoção para cada output de swap que não aparece no snapshot anterior, usando o SHA-256 real da operação de swap. `validatePromotionRollbackOperations` valida restaurações e remoções por chave separada de tipo/destino; o executor segue bloqueado e não remove arquivos reais.

## 2026-06-11 — Rollback tem ordem semântica explícita

Decisao: operações de rollback devem ser ordenadas por classe antes de qualquer execução real: dados e manifesto primeiro, sitemap depois e HTML público por último.

Motivos:
- ordem lexicográfica de snapshot e anexação posterior de remoções deixavam a remoção do `published_manifest` criado depois de sitemap e HTML;
- rollback futuro não pode depender de ordem incidental de arrays;
- estados transitórios devem privilegiar retirar dados/manifest de publicação antes de mexer em sitemap e HTML.

Consequencia: `BuildPromotionRollbackPlan` ordena `PromotionRollbackOperation` por classe operacional e `ExecutePromotionRollbackPlan` reprova plano reordenado com `public_release_rollback_plan_invalid`. A execução continua bloqueada, sem restaurar ou remover arquivos reais.

## 2026-06-11 — Remoção de rollback confere SHA do alvo

Decisao: operação de rollback `RemoveIfCreated` só pode avançar até o bloqueio default se o arquivo existente no destino ainda tiver o SHA-256 criado pela promoção planejada.

Motivos:
- remoção futura não pode apagar conteúdo alheio que apareceu no mesmo path depois de falha parcial;
- arquivo ausente no destino é estado aceitável para remoção idempotente, mas arquivo presente divergente é plano inseguro;
- mesmo com execução bloqueada, o laboratório deve diagnosticar target alterado antes de autorização real.

Consequencia: `ExecutePromotionRollbackPlan` chama `validatePromotionRollbackRemovalTargets`; alvo ausente continua válido, alvo presente com SHA divergente retorna `public_release_rollback_target_changed`, e erro de leitura retorna `public_release_rollback_target_read_failed`. Nenhum arquivo é removido.

## 2026-06-11 — Restauração de rollback confere SHA do alvo

Decisao: operação de rollback que restaura snapshot só pode avançar até o bloqueio default quando o destino atual estiver ausente, igual ao snapshot preservado ou igual ao SHA promovido planejado para aquele mesmo output.

Motivos:
- rollback futuro não pode sobrescrever conteúdo alterado por terceiro ou por ciclo concorrente;
- arquivo ausente continua aceitável porque a restauração recriaria o snapshot, mas arquivo divergente exige diagnóstico antes de qualquer escrita real;
- em falha parcial futura, um alvo já promovido pode ser restaurável quando seu SHA bate exatamente com a operação de swap planejada.

Consequencia: `ExecutePromotionRollbackPlan` chama `validatePromotionRollbackRestoreTargets`; alvo restaurável divergente retorna `public_release_rollback_target_changed`, erro de leitura retorna `public_release_rollback_target_read_failed` e o bloqueio default só aparece depois de plano, staging, swap, remoções e restaurações permanecerem íntegros. Nenhum arquivo é restaurado.

## 2026-06-11 — Ordem de rollback é sequência exata

Decisao: o executor de rollback bloqueado deve reprovar qualquer permutação de operações, inclusive dentro da mesma classe semântica.

Motivos:
- ordem por classe sozinha ainda deixa planos diferentes chegarem ao bloqueio default;
- execução real futura precisa de sequência determinística e auditável, não apenas de conjunto equivalente de operações;
- permutação dentro de dados/manifesto, sitemap ou HTML pode alterar estados transitórios e dificultar recuperação após falha parcial.

Consequencia: `validatePromotionRollbackOperations` reconstrói as operações esperadas, aplica `sortPromotionRollbackOperations` e compara cada posição. Operação fora da sequência exata retorna `public_release_rollback_plan_invalid`; nenhuma escrita de rollback é executada.

## 2026-06-11 — Swap público tem sequência exata

Decisao: operações de swap público devem ser ordenadas e revalidadas como sequência exata: HTML público primeiro, sitemap depois e dados/manifesto por último.

Motivos:
- promocao aprovada neste `/goal` deve criar entregaveis publicos antes de expor dados ou manifesto que apontem para eles;
- ordem incidental dos arrays de artefatos não pode ser contrato implícito de release;
- permutação dentro da mesma classe precisa ser diagnosticada como plano adulterado, não como bloqueio normal.

Consequencia: `BuildPromotionSwapPlan` aplica `sortPromotionSwapOperations` e `validatePromotionSwapOperations` reconstrói a sequência esperada, comparando posição a posição. Operação fora da ordem retorna `public_release_promotion_plan_invalid`; a execução segue bloqueada por padrão e não escreve em `public/`.

## 2026-06-11 — Smoke HTTP da promoção temporária

Decisao: a árvore materializada em `TemporaryPublicRoot` deve passar por smoke HTTP próprio antes de qualquer swap real.

Motivos:
- SHA-256 correto prova bytes esperados, mas não prova que Googlebot receberia HTTP 200 com canonical, robots indexável, H1 e HTML barato;
- o smoke HTTP do repo real valida `public/` atual, não a árvore isolada que seria promovida;
- `content/pages.json` rehashado pode divergir da transação congelada e contaminar sitemap/canonical sem explicar a causa raiz;
- promocao aprovada neste `/goal` nao pode depender de inspecao manual para detectar HTML grande, runtime cliente ou sitemap final incompleto.

Consequencia: `ValidateTemporaryPublicHTTPSmoke` roda depois de `ValidateTemporaryPublicPlan`, serve `TemporaryPublicRoot/public` por handler de preview, exige que as páginas indexáveis da transação existam em `TemporaryPublicRoot/content/pages.json` com conteúdo idêntico ao plano, valida `robots.txt` e `sitemap.xml` gerados a partir das configs do repo, valida as páginas indexáveis da transação, confere canonical absoluto, `index,follow,max-snippet:160`, H1, ausência de runtime cliente, orçamento de 50 KB e sitemap final com URLs indexáveis planejadas. A validação não escreve em `public/`, `content/pages.json` nem `published_manifest`. `BuildPromotionSwapPlan`, `ExecutePromotionSwapPlan` e recovery de lock precisam chamar esse smoke antes de montar operação, adquirir lock ou aceitar recuperação bloqueada; árvore temporária rehashada mas inválida para HTTP/Googlebot deve falhar antes de qualquer ledger de execução ou swap.

## 2026-06-12 — Readiness read-only para rehearsal de release

Decisao: adicionar `release-rehearsal-readiness` como contrato read-only para diagnosticar por que o primeiro candidato real ainda não pode entrar em ensaio temporário de release.

Motivos:
- o P0 precisa avançar conteúdo, páginas, HTML e Googlebot, mas sem transformar rascunho permanente bloqueado em publicação por atalho;
- os dados reais têm milhares de candidatos bloqueados, então o próximo passo deve explicar o primeiro blocker executável em vez de micro-refinar só arquitetura;
- `release_evidence_ready`, `paid_intent_release_approved` e `batch_candidate_review_release_approved` precisam ser tratados como camadas separadas antes de qualquer staging temporário;
- diagnóstico verde não pode significar aprovação editorial ou liberação de render/sitemap/publicação.

Consequencia: `internal/releaserehearsal.AssessFirstCandidate` lê `batch_final_authorial_drafts`, `batch_paid_intent_gates` e `batch_candidate_reviews`, conta candidatos e retorna o primeiro blocker executável sem escrever arquivos. A ordem de bloqueio é final draft ainda bloqueado, paid-intent não aprovado para release e revisão jurídico-editorial não aprovada para release. `./tools/check-release-rehearsal-readiness` entra no `cmd/check all`; passar no check prova apenas que o diagnóstico foi calculado e que os dados continuam legíveis, não que algum candidato está publicado ou liberado.

## 2026-06-12 — API explícita de promoção temporária ensaiada

Decisao: adicionar `publicrelease.RehearseTemporaryPromotion` para orquestrar a promoção temporária bloqueada de evidência release-ready sem chamar swap nem escrever artefatos permanentes.

Motivos:
- os próximos ciclos precisam avançar release, HTML, sitemap e Googlebot em camada vertical, sem repetir manualmente seis chamadas em cada teste ou ferramenta;
- plano parcialmente preparado não pode escapar como se fosse pronto;
- o ensaio precisa provar árvore temporária materializada, hashes e preview HTTP antes de qualquer swap/lock;
- o nome deve refletir promoção temporária bloqueada, não publicação final.

Consequencia: `RehearseTemporaryPromotion(root, evidence)` executa `BuildPlanFromReleaseEvidence`, `MaterializeStaging`, `BuildPromotionPlan`, `MaterializeTemporaryPublicPlan`, `ValidateTemporaryPublicPlan` e `ValidateTemporaryPublicHTTPSmoke`, parando no primeiro `Report` com falha e retornando `PromotionPlan{}` em erro. Quando passa, retorna o `PromotionPlan` validado e deixa artefatos apenas em `.release-staging`; não chama `BuildPromotionSwapPlan`, `ExecutePromotionSwapPlan`, `PromotePreparedStagingToPublic`, rollback ou qualquer escrita em `public/`, `content/pages.json` ou `published_manifest`.

## 2026-06-12 — Evidência sandbox a partir de candidato bloqueado

Decisao: criar `BuildSandboxReleaseEvidenceForTemporaryPromotion` para transformar apenas cópias em memória de registros bloqueados em `ReleaseEvidence` release-ready, exclusivamente para ensaio temporário.

Motivos:
- o ciclo precisa aproximar dados reais bloqueados do caminho de release sem alterar JSONL reais;
- `publicrelease.ReleaseEvidence` é indistinguível de evidência real para o planner, então a API precisa ter nome sandbox e invariantes fortes;
- o primeiro candidato real atual cruza camadas relevantes, mas continua bloqueado para release real;
- datas de aprovação/revisão não podem ser inventadas nem mascaradas como aprovação editorial.

Consequencia: a API aceita apenas final draft `batch_final_authorial_draft_blocked` com `noindex`, flags públicas falsas e `public_path=""`; paid-intent `paid_intent_passed_blocked_publication` com flags públicas falsas; revisão `batch_candidate_review_blocked` com flags públicas falsas; identidade idêntica entre camadas por draft, intent, batch, source matrix, termo e path; fonte selecionada; e datas ISO. Em sucesso, somente as cópias recebem estados release-ready para passar por `RehearseTemporaryPromotion` em fixture/tempdir. Em falha, retorna diagnóstico e não gera evidência. Isso não aprova revisão, não libera CTA público, não escreve dados reais e não publica.

## 2026-06-12 - Check sandbox com candidato real bloqueado

Decisao: adicionar `release-rehearsal-sandbox` como check separado do diagnóstico
`release-rehearsal-readiness`.

Motivo: readiness calcula o primeiro bloqueio; sandbox precisa provar que um trio
real bloqueado consegue atravessar, por cópia temporária, a cadeia de evidência,
render, sitemap e smoke HTTP/Googlebot sem mutar os arquivos permanentes.

Consequencia: o check lê dados reais, mas executa `RehearseTemporaryPromotion`
apenas em tempdir/fixture. Sucesso não significa aprovação editorial, publicação,
manifesto público ou liberação de sitemap real.

## 2026-06-12 - Diagnóstico editorial pós-sandbox

Decisao: adicionar `release-rehearsal-editorial-blockers` para classificar blockers
do primeiro candidato real depois do ensaio sandbox.

Motivo: o candidato linha 1 já tem fonte travada como reference-only, mas continua
com revisão bloqueada, CTA não público e manifesto pendente de SEO/conteúdo. O
diagnóstico precisa separar essas camadas para evitar tratar sandbox verde como
aprovação pública.

Consequencia: blockers como fonte travada, revisão bloqueada, CTA draft, SEO pending
e conteúdo exigido aparecem como dados estruturados do diagnóstico, enquanto o check
passa se conseguir ler e cruzar as camadas sem publicar.

## 2026-06-12 - Autocrítica de engenharia obrigatória em checkpoint e documentação

Decisao: todo checkpoint e toda documentação de decisão/check/gate criada ou alterada
deve incluir autocrítica de engenharia obrigatória, sem fórmula rígida. O agente deve
responder qual melhoria técnica ainda falta e por que importa agora, qual risco de
segurança/publicação/indexação/dados permanentes/regressão foi criado ou reduzido, se
a mudança reduz custo/tempo/risco de forma real ou só desloca complexidade, se a
validação pode gerar falso positivo/falso negativo e qual próximo passo executável
aumenta mais confiança.

Motivo: teste verde, checkpoint e documentação podem virar falso conforto se o agente
não ler o contexto atual, não avaliar segurança ou tratar microcorreção como avanço
vertical. A autocrítica técnica força checagem de qualidade, segurança, ganho real e
validade da prova antes de commit, sem prender o próximo Codex a perguntas mecânicas.

Consequencia: `AGENTS.md`, `GOAL.md` e `LAB_VALIDATION.md` exigem leitura de contexto
antes de agir, camadas verticais coerentes e autocrítica com análise de falso
positivo/falso negativo. A ausência dessas respostas torna o checkpoint/documentação
incompleto para ciclos P0.

Refinamento do mesmo dia: a frase "O que podemos melhorar, e por que? É seguro? É
otimização real? É teste real sem falso positivo ou negativo?" não deve ser copiada
como formulário rígido. Ela é um atalho histórico para perguntas de engenharia mais
úteis: qual melhoria vertical P0 falta, qual risco mudou, se houve ganho real ou
deslocamento de complexidade, se a validação usou dados reais, quais falsos positivos
ou negativos ainda são plausíveis, que evidência reduziria a dúvida e qual próximo
passo executável preserva dados permanentes e continuidade.

## 2026-06-12 - Plano agregado de blockers editoriais pós-sandbox

Decisao: adicionar `release-rehearsal-editorial-plan` como diagnóstico agregado do
lote inteiro, separado do check do primeiro candidato.

Motivo: linha 1 não representa o lote. O batch previdenciário mistura 363 intenções
informativas flexíveis bloqueadas com 7 intenções comerciais normais, enquanto os
outros cinco batches têm paid-intent comercial bloqueado. Um diagnóstico só da linha
1 pode mascarar exceções por lane e concentração de blockers por família.

Consequencia: `AssessEditorialBlockerPlan` conta candidatos, batches, blockers por
código e por batch, rejeita duplicatas de camada e calcula próxima ação editorial sem
publicar. O check passa se o plano é calculável; blockers continuam sendo evidência
de laboratório, não falha operacional nem aprovação pública.

O que podemos melhorar, e por que? Transformar o plano em relatório persistente
bloqueado por ciclo/família para orientar correções editoriais em lote sem depender
do chat. É seguro? Sim, porque a função é read-only, não escreve JSONL/public/pages e
falha fechado em duplicatas. É otimização real? Sim, porque troca inspeção manual de
cinco camadas por agregação determinística de 2.220 candidatos. É teste real sem
falso positivo ou negativo? O teste cobre dados reais e duplicata sintética; ainda
pode ter falso negativo se novos blockers surgirem sem entrar na lista de prioridades,
então próximos ciclos devem expandir amostras e saída do relatório.

## 2026-06-12 - Saída operacional do plano editorial agregado

Decisao: `release-rehearsal-editorial-plan` não deve voltar a imprimir apenas
`pass`. A linha de sucesso precisa expor `calculated=true`, `approval=false`,
`publication=false`, `blockers_present=true`, contagem de candidatos, batches,
publicáveis, release-ready e próximo batch calculado. O relatório interno também deve
preservar amostras determinísticas por blocker e batch.

Motivo: `pass` silencioso economiza caracteres, mas perde contexto operacional e pode
ser lido como aprovação. A meta P0 exige que o próximo Codex veja rapidamente que o
lote está calculado, bloqueado, sem publicação e com próxima ação concreta.

Consequencia: o check continua read-only e verde quando consegue calcular o plano,
mas sua saída nega aprovação/publicação explicitamente. O próximo avanço deve usar
essa saída para corrigir a camada editorial do batch prioritário sem mexer em
`published_manifest`, `content/pages.json`, sitemap ou `public/`.

Autocrítica de engenharia: a melhoria técnica que ainda falta é persistir ou exportar
relatório bloqueado por ciclo/família com amostras suficientes para correção em lote.
O risco reduzido é falso conforto de laboratório verde; o risco restante é o relatório
ainda não trazer linhas de todas as camadas. O ganho é real porque evita reabrir cinco
JSONL manualmente para saber que há 2.220 blockers e próximo batch calculado. A
validação cobre dados reais, saída do check e amostra previdenciária, mas pode deixar
falso negativo se um novo blocker não entrar em `NextAction`; a próxima evidência deve
expandir prioridade e correção editorial do batch consumidor financeiro.

## 2026-06-12 - Correção bloqueada da tensão de fonte em reviews de consumidor financeiro

Decisao: corrigir `required_fixes` dos 370 reviews do batch
`batch-consumidor-financeiro-digital` para remover a pendência ambígua de fonte final,
porque a camada `batch_source_specificity_resolutions` já está travada como
`final_source_locked_reference_only`.

Motivo: manter "resolver fonte específica final" em review depois da fonte travada cria
blocker textual stale e impede o plano editorial de avançar para a próxima família. A
correção não aprova conteúdo; ela separa camadas: source já travada como referência,
enquanto SEO, conteúdo, CTA e manifesto continuam bloqueados.

Consequencia: os 370 reviews continuam `batch_candidate_review_blocked`, com
`render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e
`public_path=""`. `required_fixes` passa a listar três pendências concretas: revisão
SEO, conteúdo autoral completo e validação de CTA/manifesto em modo bloqueado. O plano
agregado passa a calcular a próxima ação em `batch-familia-digital`, ainda com
`approval=false` e `publication=false`.

Autocrítica de engenharia: a melhoria técnica restante é aplicar a mesma correção por
família somente quando source specificity estiver travada e manifest/review seguirem
bloqueados; aplicar em lote sem essa condição poderia esconder fonte realmente
pendente. O risco reduzido é falso positivo textual no blocker de source; o risco
restante é a regra ainda depender de substring em `required_fixes`. O ganho é real
porque 370 registros saíram de um blocker stale e mantiveram blockers substantivos. A
validação cobriu testes de contrato, check de reviews, plano editorial e diff público
vazio; a próxima evidência deve generalizar a correção para `batch-familia-digital`
com a mesma guarda.

## 2026-06-12 - Guarda source/manifest antes de correção de reviews por família

Decisao: `ApplySourceTensionCorrection` só pode corrigir um batch quando cada review
do batch tiver source specificity travada como `final_source_locked_reference_only` e
manifesto ainda bloqueado por SEO/conteúdo, com todas as flags públicas falsas.

Motivo: remover a palavra `fonte` de `required_fixes` sem conferir source/manifest
poderia esconder fonte realmente pendente. A guarda torna a correção repetível por
família sem transformar review em aprovação.

Consequencia: a correção foi aplicada também em `batch-familia-digital` após `guarded=370`.
O plano editorial passou a apontar `next_batch=batch-previdenciario-digital`, ainda com
`approval=false`, `publication=false`, `publication_allowed=0` e `release_ready=0`.

Autocrítica de engenharia: a melhoria restante é tratar o batch previdenciário com
cuidado de lane, porque há 363 informativos flexíveis e 7 comerciais normais. O risco
reduzido foi aplicar correção em batch sem source/manifest coerentes; o risco restante
é a guarda estar dentro do pacote de reviews com structs mínimos locais. O ganho é
real porque a correção agora é operacionalmente escalável e verificável. A validação
cobriu contrato, check de reviews e plano agregado; a próxima evidência deve confirmar
que a exceção previdenciária não muda paid-intent nem política pública.

## 2026-06-12 - Contrato de alta escala editorial com fontes atuais e HTML barato

Decisao: reforçar que a meta pública mínima continua distante enquanto não houver
manifesto jurídico publicado em escala, e que o trabalho do Codex não pode ser
reduzido a arquitetura. O próximo avanço P0 deve combinar engenharia de código,
algoritmos de conteúdo, pesquisa oficial atual, validação com dados reais, HTML leve
e gates de publicação.

Motivo: a Central da Pesquisa Google consultada em 2026-06-12 orienta conteúdo
voltado a pessoas, originalidade, confiança, acurácia, qualidade e relevância; também
alerta que automação em grande volume sem valor adicional é risco de política. Para
este portal jurídico, isso significa que conteúdo automático só é aceitável quando
fonte oficial, explicação autoral, diferenciação semântica, revisão, CTA adequado e
prova anti-duplicidade acompanham a escala. O custo de rastreamento também importa:
HTML público indexável deve ser completo no primeiro response e barato para Googlebot,
bots valiosos e usuários.

Consequencia: `AGENTS.md`, `GOAL.md`, `README.md`, `PROJECT_VISION.md`,
`CONTENT_QUALITY.md`, `SEO_CRAWL_INDEXING.md`, `DATA_SOURCES.md`,
`LAB_VALIDATION.md` e `ROADMAP_P0_P5.md` passam a enfatizar fábrica segura de
conteúdo, pesquisa oficial antes de texto jurídico substantivo, CTA calibrado por
família, automação auditável, validação contra falso positivo/falso negativo,
Googlebot como superfície técnica de crawl/indexação e página pública leve por
contrato.

Autocrítica de engenharia: a melhoria técnica restante é transformar essa diretriz em
checks e geradores mais fortes, começando pela lane previdenciária e depois por
conteúdo/fonte/revisão em lote. O risco reduzido é o próximo ciclo confundir
arquitetura limpa com progresso suficiente rumo a 10 mil páginas ou aceitar página
pesada como inevitável; o risco restante é documentação sem gate executável, mitigado
pelo plano de continuidade que exige algoritmo, dados reais e validação proporcional.
O ganho é real porque alinha escala, Googlebot e conteúdo jurídico antes de publicar;
a validação documental pode deixar falso negativo se algum contrato secundário não
lido repetir regra fraca, então os contratos vivos e checks devem ser a fonte
operacional do próximo ciclo.

## 2026-06-12 - Intenção de busca para contratação jurídica remota

Decisao: pesquisa de palavras-chave, serviços jurídicos, paid-intent e expansão
editorial devem priorizar demanda real de busca que possa virar jornada jurídica
remota: conteúdo informativo, triagem contextual, envio digital de documentos,
WhatsApp e atendimento online quando juridicamente viável e eticamente permitido,
com limite informativo explícito quando algum ato exigir presença, diligência local
ou providência externa. O fluxo padrão do produto não deve convidar o leitor ao
presencial.

Motivo: a plataforma jurídica também é canal de contratação, mas a contratação deve
nascer de intenção real, utilidade, fonte, revisão e CTA contextual, não de oferta
seca. Termos de alto volume sem viabilidade digital, com dependência presencial
dominante, autoatendimento público ou gratuidade dominante tendem a consumir escala
sem aproximar o produto da meta de páginas jurídicas úteis e contratáveis.

Consequencia: `AGENTS.md`, `GOAL.md`, `PROJECT_VISION.md`, `CONTENT_QUALITY.md` e
`ROADMAP_P0_P5.md` passam a exigir que algoritmos e editores considerem sinais de
serviço jurídico contratável pela internet: documentos disponíveis, prazo, negativa,
risco econômico, urgência, contrato, benefício, cobertura, consumidor, família,
trabalho, empresa, imóvel, INSS ou plano de saúde, sempre com triagem remota e sem
promessa de resultado. Necessidade de ato presencial ou diligência local deve aparecer
como limite informativo do caso, não como jornada comercial principal.

Autocrítica de engenharia: a melhoria técnica restante é transformar essa regra em
score/check executável no paid-intent e na pesquisa manual, para que o algoritmo
penalize presencialidade dominante sem bloquear temas juridicamente bons que apenas
tenham etapa externa eventual. O risco reduzido é desperdiçar a fábrica de conteúdo
com termos que geram tráfego mas não servem ao modelo digital; o risco criado é um
falso negativo contra tema útil que precise de algum ato presencial, mitigado pela
regra de tratar esse ato como limite e manter triagem remota. O ganho é real se o
próximo ciclo converter a diretriz em dados e validação; por enquanto, a evidência é
documental e deve orientar o próximo refinamento executável.

## 2026-06-12 - Readiness SEO bloqueado para o lote consumidor financeiro

Decisao: criar `release-rehearsal-review-seo-readiness` como diagnóstico read-only do
próximo lote apontado pelo plano editorial. O check cruza `batch_public_manifest_gates`
e `batch_prepublication_gates`, mede title/meta/canonical/robots, flags públicas,
duplicidade e sinais de truncamento, mas mantém semântica explícita de laboratório:
`approval=false`, `publication=false`, `publication_allowed=0` e `release_ready=0`.

Motivo: o ciclo confirmou que os 370 candidatos de
`batch-consumidor-financeiro-digital` têm canonical HTTPS oficial, robots
`noindex,follow` e budgets formais coerentes nas duas camadas, mas ainda apresentam
41 valores de title duplicados e 48 valores de meta duplicados. Budget verde não
prova intenção única, naturalidade, H1, conteúdo autoral ou qualidade de leitura. A
Central da Pesquisa Google consultada em 2026-06-12 reforça conteúdo útil para
pessoas, originalidade, confiança e cautela com conteúdo em escala sem valor
adicional; portanto SEO básico coerente deve virar etapa de correção, não aprovação.

Consequencia: `internal/releaserehearsal` passa a expor
`AssessReviewSEOReadiness`; `internal/checks`, `cmd/check` e
`tools/check-release-rehearsal-review-seo-readiness` passam a reportar a fotografia
do lote. O check atual imprime `candidate_count=370`,
`mechanical_ready_blocked=370`, `duplicate_title_values=41`,
`duplicate_meta_values=48`, `duplicate_canonical_values=0`,
`publication_allowed=0` e `release_ready=0`. Nenhum JSONL editorial, `public/`,
`content/pages.json`, sitemap ou `published_manifest` foi alterado por essa camada.

Autocrítica de engenharia: a melhoria vertical que falta agora é um refinador em lote
de title/meta por intenção única, usando problema, documento, risco, fonte e ação
digital, sem cortar texto mecanicamente para caber no orçamento. A mudança é segura
porque só calcula e expõe blockers; não publica nem remove pendências de conteúdo
autoral, CTA/manifesto e revisão jurídica. A otimização é real porque reduz falso
conforto de budget verde e orienta a próxima correção em 370 registros; ainda há
risco de falso negativo para H1 e naturalidade do corpo enquanto esses sinais não
forem validados por render/final draft. O próximo ciclo deve corrigir a geração SEO
em lote e validar duplicidade/truncamento novamente antes de avançar para conteúdo e
CTA.

## 2026-06-12 - Refinamento bloqueado de title/meta no batch consumidor

Decisao: criar `batchseorefinement` e `./tools/refine-batch-seo` para corrigir title
e metadescrição em camadas bloqueadas, começando por
`batch-consumidor-financeiro-digital`, sem acionar refresh completo do pipeline.

Motivo: `refresh-batch-candidate-pipeline` também reescreve reviews e poderia
desfazer correções anteriores em `required_fixes`. O refinador dedicado altera apenas
`batch_prepublication_gates`, `batch_public_manifest_gates` e
`batch_final_authorial_drafts`, preservando source, paid-intent, reviews e todas as
flags públicas bloqueadas.

Consequencia: o batch consumidor passou de 41 valores de title duplicados e 48 valores
de meta duplicados para zero duplicatas exatas; os sinais de truncamento do
diagnóstico também foram a zero. `release-rehearsal-review-seo-readiness` continua
`approval=false`, `publication=false`, `publication_allowed=0` e `release_ready=0`.
O fix canônico de SEO em `batch_candidate_reviews` ainda não foi removido neste ciclo;
o próximo passo deve remover esse marcador somente com a readiness limpa e mantendo
conteúdo autoral e CTA/manifesto como blockers.

Autocrítica de engenharia: a melhoria foi real porque corrigiu dados permanentes
bloqueados e sincronizou três camadas downstream sem tocar em `public/`,
`content/pages.json` ou `published_manifest`. É seguro porque o refinador recusa flags
públicas inseguras e valida orçamento/deduplicação. O risco restante é que títulos
únicos por label ainda são diagnósticos de laboratório, não copy final aprovado; H1,
corpo autoral e CTA continuam pendentes. A próxima validação precisa transformar o
SEO fix do review em estado resolvido apenas para o batch consumidor e recalcular o
plano editorial para avançar ao próximo batch sem mascarar conteúdo/CTA.

## 2026-06-12 - Resolução guardada do fix SEO em reviews do batch consumidor

Decisao: criar `reviewseofixresolver` e `./tools/resolve-review-seo-fix` para remover
o fix canônico de revisão SEO dos reviews somente quando o readiness do lote alvo
estiver limpo, bloqueado e sem sinal público. A resolução foi aplicada apenas ao
`batch-consumidor-financeiro-digital`.

Motivo: depois do refinamento de title/meta, o lote consumidor tinha 370 candidatos
mecanicamente coerentes, duplicidade e truncamento zerados, `publication_allowed=0` e
`release_ready=0`. Manter o fix de SEO nos reviews criava blocker stale e impedia o
plano editorial de avançar para o próximo lote. Remover o fix sem guarda, porém,
poderia mascarar duplicidade, corte mecânico ou publicação indevida.

Consequencia: `data/editorial/batch_candidate_reviews.jsonl` mantém 370 reviews do
batch consumidor bloqueados por conteúdo autoral e CTA/manifesto, mas sem o blocker
SEO já resolvido. Os demais batches ainda somam 1.850 blockers de SEO. O plano
editorial agora aponta `batch-familia-digital`; o readiness desse lote reporta 37
titles duplicados, 43 metas duplicadas, 66 sinais de truncamento em title e 89 em
meta, com publicação em zero. Nenhuma URL foi movida para `published_manifest`,
`content/pages.json`, `public/` ou sitemap.

Fontes oficiais consultadas no ciclo para manter o contrato alinhado a Googlebot e
conteúdo em escala: Central da Pesquisa Google sobre conteúdo útil
(`https://developers.google.com/search/docs/fundamentals/creating-helpful-content`),
políticas de spam (`https://developers.google.com/search/docs/essentials/spam-policies`),
JavaScript SEO (`https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics`)
e sitemaps (`https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview`).

Autocrítica de engenharia: a melhoria real foi remover um blocker stale com guarda
executável e fazer o plano avançar, sem reduzir os blockers editoriais restantes. É
seguro porque a ferramenta rejeita duplicidade, truncamento, issue básica, drift e
qualquer flag pública antes de escrever. A otimização é real porque evita repetir
trabalho no consumidor e concentra o próximo ciclo no lote família; ainda há risco de
falso conforto se alguém tratar SEO mecânico como copy final. A próxima evidência
útil é corrigir title/meta do `batch-familia-digital` em camada bloqueada ou avançar
uma vertical maior que inclua SEO, conteúdo autoral e CTA com validação em dados
reais, mantendo HTML público leve e diff público vazio.

## 2026-06-12 - Refinamento SEO bloqueado do batch família

Decisao: reaplicar a vertical de SEO bloqueado em `batch-familia-digital`, melhorando
`batchseorefinement` para não deixar títulos terminarem em conectivo ou expressão
cortada após ajuste de orçamento.

Motivo: a primeira aplicação no lote família zerou duplicatas de title/meta, mas a
readiness ainda reportou 17 sinais de title truncado. A causa raiz era `trimAtWord`
preservar finais como `e`, `com` ou `linha do` quando o orçamento cortava uma frase
longa. Remover o blocker de review nesse estado seria falso positivo.

Consequencia: o refinador agora limpa finais truncados antes de persistir title/meta
e tem teste específico para impedir regressão. O lote família passou a
`duplicate_title_values=0`, `duplicate_meta_values=0`, `truncated_title_signals=0` e
`truncated_meta_signals=0`, mantendo `publication_allowed=0` e `release_ready=0`.
Depois disso, `./tools/resolve-review-seo-fix -batch batch-familia-digital` removeu
o fix SEO de 370 reviews, preservando conteúdo autoral e CTA/manifesto como blockers.
Como title/meta do rascunho final participam da avaliação de paid-intent, a camada
`batch_paid_intent_gates` precisou ser regenerada a partir dos dados atuais para
remover sinais stale de `protocolo` em registros de família. O plano editorial
avançou para `batch-previdenciario-digital`, com 1.480 blockers SEO restantes nos
batches ainda não resolvidos.

Autocrítica de engenharia: a melhoria foi real porque corrigiu falso positivo de
readiness e removeu blocker stale só depois da evidência limpa. É seguro porque todos
os registros continuam `noindex`, sem render, sitemap, publicação ou `public_path`, e
as lanes previdenciárias ainda não foram tocadas. A otimização reduziu retrabalho ao
generalizar o refinador para próximos lotes; o risco restante é tratar a limpeza de
title/meta como aprovação editorial ou esquecer que SEO pode exigir refresh de gates
derivados. A próxima camada deve atacar o previdenciário respeitando a exceção
informativa e validando que paid-intent, conteúdo e CTA não sejam distorcidos por um
refinamento apenas mecânico de SEO.

## 2026-06-12 - Refinamento SEO bloqueado do batch previdenciário

Decisao: aplicar a mesma vertical de SEO bloqueado ao `batch-previdenciario-digital`
sem alterar a semântica das lanes pagas e informativas.

Motivo: o lote previdenciário era o próximo blocker calculado e tinha 370 candidatos
bloqueados, 42 titles duplicados, 46 metas duplicadas, 100 sinais de title truncado e
126 de meta truncada. O batch também possui exceção operacional: 363 candidatos podem
crescer como informativos previdenciários bloqueados, enquanto 7 continuam comerciais
normais. Refinar SEO sem checar lanes poderia distorcer paid-intent.

Consequencia: `./tools/refine-batch-seo -batch batch-previdenciario-digital` zerou
duplicidade e truncamento nas três camadas SEO/final draft bloqueadas; `paid-intent`
permaneceu válido sem regeneração e manteve 363 registros
`paid_intent_flexible_previdenciario_informational_blocked_publication` e 7
`paid_intent_passed_blocked_publication`. Depois da readiness limpa,
`./tools/resolve-review-seo-fix -batch batch-previdenciario-digital` removeu o fix SEO
de 370 reviews, preservando blockers de conteúdo autoral e CTA/manifesto. O próximo
lote calculado é `batch-saude-suplementar-digital`, com 1.110 blockers SEO restantes
nos batches ainda não resolvidos.

Autocrítica de engenharia: o ganho foi real porque uma família com exceção de lane
avançou sem perder a separação entre informativo previdenciário e comercial. É seguro
porque as flags públicas continuaram falsas, `published_manifest` não mudou e
paid-intent validou as contagens. A otimização é real porque o refinador corrigiu o
lote sem intervenção manual por intent. O risco restante é que SEO limpo ainda não
prova conteúdo previdenciário final nem revisão jurídica; o próximo ciclo deve atacar
saúde suplementar ou uma camada vertical maior mantendo prova de não publicação e
checando gates derivados quando title/meta mexerem em sinais comerciais.

## 2026-06-12 - Refinamento SEO bloqueado do batch saúde suplementar

Decisao: aplicar a vertical SEO bloqueada ao `batch-saude-suplementar-digital` e
regenerar paid-intent quando o refinamento de final drafts alterar sinais comerciais
derivados.

Motivo: saúde suplementar era o próximo blocker calculado, com 39 titles duplicados,
43 metas duplicadas e sinais de truncamento. Após o refinamento, readiness ficou
limpa, mas `paid-intent` detectou um registro stale que ainda esperava `nota fiscal`
como business signal. Como o gate pago deriva do texto atual do final draft, a
correção correta foi regenerar `batch_paid_intent_gates`, não forçar o sinal no SEO.

Consequencia: o lote saúde suplementar ficou com duplicidade e truncamento zerados,
370 registros comerciais pagos bloqueados preservados, `publication_allowed=0` e
`release_ready=0`. Depois da readiness limpa,
`./tools/resolve-review-seo-fix -batch batch-saude-suplementar-digital` removeu o fix
SEO de 370 reviews e preservou conteúdo autoral/CTA como blockers. O próximo lote
calculado é `batch-sucessorio-digital`, restando 740 blockers SEO.

Autocrítica de engenharia: a mudança foi segura porque a falha de paid-intent
impediu falso conforto e obrigou refresh do gate derivado antes do commit. A
otimização é real porque consolidou o padrão de refinamento+refresh+resolução para
mais um batch sem publicar. O risco restante é o mesmo: SEO limpo ainda não aprova
conteúdo final, e gates derivados precisam continuar na validação sempre que final
draft mudar.

## 2026-06-12 - Refinamento SEO bloqueado do batch sucessório

Decisao: aplicar a vertical SEO bloqueada ao `batch-sucessorio-digital` e repetir a
regra de refresh de paid-intent quando o final draft refinado alterar sinais
comerciais derivados.

Motivo: sucessório era o próximo blocker calculado e apresentava 39 titles duplicados,
45 metas duplicadas, 88 sinais de title truncado e 74 de meta truncada. Depois do
refinamento, `paid-intent` detectou sinais stale de `protocolo` e `contrato` em gates
pagos persistidos, incompatíveis com o texto atual recalculado.

Consequencia: o lote sucessório ficou com readiness SEO limpa, paid-intent regenerado
e válido, 370 reviews sem o fix SEO stale e conteúdo autoral/CTA ainda bloqueando
publicação. O próximo e último lote com blocker SEO é `batch-trabalhista-digital`,
restando 370 blockers SEO.

Autocrítica de engenharia: o ciclo reforçou que gates derivados devem acompanhar
final drafts depois de SEO, e não apenas passar em isolamento. É seguro porque nenhum
registro saiu de `noindex` nem ganhou render/sitemap/publicação. A otimização é real
porque reduziu o blocker SEO a um último batch; o risco restante é avançar para a
próxima camada de conteúdo/CTA sem revisar que SEO limpo ainda não aprova texto final.

## 2026-06-12 - Testes derivados acompanham mudanças autorais sem afrouxar contrato

Decisao: qualquer mudança em conteúdo autoral, final draft, CTA, title/meta ou texto
visível deve recalcular camadas e testes derivados de SEO/search appearance,
paid-intent, public manifest, reviews e plano editorial.

Motivo: os ciclos de SEO mostraram que alterar final drafts pode mudar sinais de
paid-intent, duplicidade, truncamento e próximo blocker calculado. Manter expectativas
antigas em testes vira falso negativo ou falso positivo; remover o teste vira quebra
de contrato.

Consequencia: adaptar testes após mudança autoral é obrigatório quando refletir os
dados reais regenerados, mas é proibido afrouxar exigência. A sequência segura é
regenerar a camada derivada, validar contadores reais, atualizar expectativa
contratual, provar flags públicas falsas e registrar a causa no checkpoint.

Autocrítica de engenharia: a regra reduz falso positivo e falso negativo em testes
derivados, mas só é segura quando a regeneração vem antes da expectativa. É
otimização real porque evita retrabalho e impede que dados stale travem ou aprovem o
lote errado. O risco restante é alguém usar "atualizar teste" como atalho; por isso o
checkpoint deve registrar causa, contadores reais, flags públicas e próximo plano de
expansão.

## 2026-06-12 - Todos os blockers SEO de reviews foram resolvidos sem publicação

Decisao: concluir a camada de revisão SEO bloqueada no `batch-trabalhista-digital` e
tratar ausência de lote SEO pendente como estado válido do readiness, desde que o
plano editorial calcule o próximo blocker real.

Motivo: depois do refinamento trabalhista e resolução guardada dos reviews, nenhum dos
2.220 candidatos mantém `release_rehearsal_review_seo_fix_pending`. Antes, o check
`release-rehearsal-review-seo-readiness` transformava esse estado em erro por falta de
alvo; isso era falso negativo de continuidade, porque a camada SEO acabou e o próximo
P0 passou a ser conteúdo autoral/CTA/manifesto.

Consequencia: o readiness SEO agora passa com `target=false`, contadores zerados,
`publication_allowed=0` e `release_ready=0` quando não houver blocker SEO pendente. O
plano editorial continua `blockers_present=true` e aponta
`release_rehearsal_next_action_complete_review_authorial_content_fixes_in_batch` em
`batch-consumidor-financeiro-digital`. O ciclo não publica, não renderiza, não altera
sitemap e não move candidatos para `published_manifest`.

Autocrítica de engenharia: a mudança evita falso negativo sem transformar ausência de
pendência SEO em aprovação pública. É segura porque o próximo blocker permanece
explícito, todos os registros seguem bloqueados e o diff público crítico fica vazio. A
otimização é real porque impede que o próximo Codex reabra lotes SEO já resolvidos e
força avanço vertical em conteúdo/CTA. O risco restante é conteúdo autoral mudar
title/meta/sinais comerciais; por isso a próxima camada deve regenerar gates derivados
e adaptar testes aos dados reais sem afrouxar contrato.

## 2026-06-12 - Expansão editorial orientada por demanda qualificada e fontes oficiais

Decisao: pautas, termos e novos conteúdos devem combinar alta intenção orgânica,
viabilidade de atendimento jurídico digital, sinais públicos de interesse social e
fontes oficiais auditáveis, sem depender de uma única superfície de busca.

Motivo: Googlebot e Google Search continuam P0 para crawl, indexação, qualidade técnica
e detecção de conteúdo ruim, mas a plataforma precisa capturar problemas reais que
aparecem na linguagem de usuários, redes sociais e conversas públicas. Popularidade só
é útil quando vira conteúdo jurídico próprio, verificável, sóbrio e adequado à OAB.
Temas sobre IA/OpenAI/Codex exigem documentação oficial da OpenAI como base primária;
temas jurídicos exigem fonte oficial brasileira.

Consequencia: backlog, briefs, rascunhos e algoritmos de expansão devem considerar
sinais orgânicos e sociais, mas sempre bloquear publicação até fonte, revisão,
paid-intent, CTA, SEO/crawl, anti-spam, HTML leve e release gate. Redes sociais servem
para priorização, linguagem e descoberta de dúvidas; não servem para afirmar fato
jurídico sem fonte nem para criar conteúdo oportunista.

Autocrítica de engenharia: a regra melhora cobertura temática e chance de tração sem
trocar rigor por tendência. É segura porque mantém fonte oficial e gates como condição
de publicação. A otimização é real se virar ranking, score, testes e dados versionados;
se ficar só em texto, não basta. O próximo passo é transformar essa regra em
pipeline/score de pauta quando a vertical de conteúdo autoral avançar.

## 2026-06-12 - Conteúdo autoral consumidor exige unicidade em lote antes de resolver blocker

Decisao: fortalecer o gerador e os testes de final drafts do
`batch-consumidor-financeiro-digital` antes de remover o blocker de conteúdo autoral,
e resolver essa pendência apenas depois de evidência anti-template em dados reais.

Motivo: a auditoria read-only mostrou que 370 final drafts consumidores passavam
`human_score` isolado, mas repetiam `document_guidance`, `digital_triage` e CTA em
escala. Isso seria falso positivo editorial: páginas formalmente válidas, mas pouco
únicas para humanos e Googlebot. O primeiro refresh também reabriu a frase antiga de
fonte/SEO nos reviews, provando que regeneração sem preservar contexto pode desfazer
camadas já conquistadas.

Consequencia: o pipeline passou a preservar/normalizar `required_fixes` já resolvidos,
o gerador consumidor passou a usar sinais semânticos do draft original e o contrato
ganhou teste anti-template por lote. Depois de regenerar, `check-batch-final-authorial-drafts`
passou; `resolve-review-content-fix` removeu somente o blocker autoral do
batch consumidor e marcou `content_draft_required=false` nos 370 manifestos
consumidores, mantendo SEO, CTA/manifesto e todas as flags públicas bloqueadas. Como
conteúdo/CTA mudaram, `batch_paid_intent_gates` foi regenerado.

Autocrítica de engenharia: a mudança é segura porque o resolvedor só roda com final
draft bloqueado, fonte presente, manifesto alinhado e zero sinal público; publicação
continua em zero. É otimização real porque evita que o próximo ciclo retrabalhe
consumidor autoral e impede falso positivo de score isolado. O risco restante é que
demanda qualificada/social/oficial ainda não está vinculada ao batch consumidor; a
próxima camada deve versionar essa atribuição antes de CTA/manifesto ou expansão.

## 2026-06-12 - Conteúdo autoral de família exige finalizador próprio e refresh preservado

Decisao: resolver o blocker de conteúdo autoral do `batch-familia-digital` somente
depois de teste anti-template em lote, finalizador específico de família e correção do
refresh para não reabrir `content_draft_required` já resolvido.

Motivo: auditoria read-only mostrou que 370 final drafts de família tinham
`human_score=100`, mas repetiam `document_guidance`, `digital_triage` e documentos de
CTA porque caíam no caminho genérico do gerador. O primeiro ajuste também revelou que o
pipeline derivava `content_draft_required=true` apenas de fonte travada, ignorando
reviews já resolvidos; isso reabria manifesto autoral de consumidor durante refresh.

Consequencia: `batch_final_authorial_drafts` agora tem teste de variação semântica para
família; o pipeline usa `ReaderProblem`, `DocumentContext`, `RiskContext` e
`DigitalAction` também em família; documentos de revisão/CTA variam por matéria e
faceta; `buildManifest` deriva `content_draft_required` do blocker autoral remanescente
no review. Depois de regenerar, `resolve-review-content-fix` removeu o blocker autoral
dos 370 reviews de família e marcou `content_draft_required=false` nos manifestos do
batch, mantendo SEO, CTA/manifesto e todas as flags públicas bloqueadas. O plano
editorial passou para `batch-previdenciario-digital`.

Autocrítica de engenharia: a mudança resolveu falso positivo de score isolado e falso
negativo de refresh. É segura porque não publicou, não renderizou, não alterou sitemap
e manteve `publication_allowed=0`. É otimização real porque preserva estado resolvido
em refresh futuro e evita que escala familiar vire template. Risco restante: a camada
previdenciária tem exceção informativa e precisa de validação própria para não confundir
conteúdo educativo bloqueado com intenção comercial.

## 2026-06-12 - Correção para frente em vez de retorno por Git

Decisao: Codex principal e subagentes não pode usar Git para voltar ao estado anterior.
Git não é ferramenta de correção por retorno de estado; Git é ferramenta de inspeção,
diff, stage, commit e rastreabilidade. `git reset`, `git checkout`, `git restore`,
`git revert`, `git cherry-pick`, merge cego ou limpeza equivalente não podem apagar tentativa,
reduzir diff, recuperar contador antigo, substituir análise de causa raiz ou fazer teste passar
por retorno operacional. A regra do projeto é correção para frente.

Motivo: voltar ao estado anterior pode esconder erro de engenharia, perder contexto,
destruir dados permanentes e transformar crítica válida em edição defensiva. Quando um
ciclo toma direção errada, o trabalho correto é entender a causa raiz, criar uma guarda
executável, refinar algoritmo, recalcular dados derivados, preservar artefatos
permanentes e registrar o aprendizado. Conflito deve ser resolvido editando para frente,
preservando evolução válida, corrigindo bug, recalculando dado derivado e validando o
arquivo vivo.

Consequencia: Git fica permitido para inspeção, diff, stage, commit e rastreabilidade. worktree rastreada ou não rastreada versionável é estado vivo do repo. Codex deve integrar para frente código, dado, ferramenta, teste, contrato, agente ou artefato versionável presente na worktree. É proibido invalidar, ignorar, apagar, reverter, excluir ou rebaixar trabalho vivo por não estar staged, commitado ou rastreado por acidente. arquivo não rastreado versionável é pendência de integração e rastreabilidade, não inexistência. Gate ou check deve validar conteúdo, schema, segurança, licença, origem, flags públicas e utilidade; não pode reprovar apenas por ausência em `git ls-files --cached`. O próximo Codex deve avançar com código, gate, validador, refresh calculado ou migração que corrija o sistema.

Autocrítica de engenharia: essa regra reduz falso conforto porque impede apagar o erro
em vez de transformá-lo em proteção executável. O ganho real só aparece se cada falha
virar teste, contrato ou algoritmo melhor; se ficar só como texto, o risco permanece. O
próximo ciclo deve manter a trava previdenciária como correção para frente e construir
o gate autoral específico, em vez de tentar apenas restaurar contadores antigos.

## 2026-06-12 - CTA previdenciário precisa variar por benefício e faceta

Decisao: o gate anti-template de `batch-previdenciario-digital` deve medir também a
variação dos documentos no CTA, não apenas abertura, orientação documental e triagem
digital. O CTA previdenciário deve variar por tipo de benefício/problema e por faceta
do intent, mantendo linguagem informativa, origem rastreável e bloqueio público.

Motivo: auditoria read-only mostrou que 369/370 CTAs repetiam o mesmo bloco documental.
Esse padrão passava em checks estruturais, mas criava falso positivo editorial e texto
com aparência mecânica. A página institucional do INSS e serviços gov.br sobre
aposentadoria e auxílio por incapacidade confirmam que o vocabulário previdenciário
precisa distinguir CNIS, protocolo, decisão, perícia, laudo, exigência, recurso, BPC,
dependência, cálculo e histórico contributivo conforme o problema.

Consequencia: `TestBatchFinalAuthorialDraftsKeepPrevidenciarioSemanticVariation`
passou a exigir variação de CTA; o pipeline gera documentos de CTA por subtipo
previdenciário e faceta; `reusableFinalDraft` invalida CTAs previdenciários legados
quando eles preservam blocos repetidos. O lote continua `noindex`, sem render, sitemap,
publicação ou `public_path`, e o resolvedor autoral genérico segue bloqueado para
previdenciário.

Autocrítica de engenharia: a mudança reduz um falso negativo concreto de unicidade em
lote e usa dados reais para provar a melhoria. É segura porque atua em final drafts
bloqueados e paid-intent foi regenerado. A otimização é parcial: remove repetição de
CTA, mas ainda não aprova conteúdo autoral previdenciário nem resolve frases ou
semântica em todos os campos. A próxima camada deve criar gate autoral previdenciário
com similaridade por campo, amostras de naturalidade, separação informativo/comercial e
critérios de frase quebrada antes de remover `ContentDraftFix`.

## 2026-06-12 - Gate autoral previdenciário como diagnóstico bloqueado

Decisao: criar `previdenciario-authorial-gate` como check próprio em `cmd/check all`
antes de permitir que qualquer resolvedor remova `ContentDraftFix` do
`batch-previdenciario-digital`.

Motivo: o resolvedor genérico não conhece a exceção informativa previdenciária, e checks
isolados já produziram falso conforto. O gate precisa calcular o lote inteiro, cruzar
final drafts, reviews e paid-intent, provar que 363 registros seguem na lane
informativa bloqueada, 7 seguem comerciais bloqueados, nenhum registro foi publicado e
o blocker autoral permanece até existir validação lane-specific completa.

Consequencia: `internal/previdenciarioauthorialgate`, `./tools/check-previdenciario-authorial-gate`
e o check `previdenciario-authorial-gate` entram no laboratório. A linha de pass é
diagnóstica: `approval=false`, `publication=false`, `content_fix_remaining=370`. Isso
não autoriza resolver conteúdo autoral; dá ao próximo ciclo um ponto executável para
evoluir similaridade por campo, frases quebradas e separação informativo/comercial.

Autocrítica de engenharia: o ganho é real porque o próximo Codex deixa de depender de
memória do checkpoint para saber que previdenciário está bloqueado por design. É seguro
porque o check reprova publicação ou alteração de lane. Ainda é diagnóstico inicial:
não mede naturalidade profunda nem similaridade semântica entre todos os campos. A
próxima melhoria deve transformar esse gate em avaliador mais forte, não em liberação
prematura.

## 2026-06-12 - Naturalidade previdenciária precisa ser métrica de gate

Decisao: o `previdenciario-authorial-gate` deve medir diversidade e naturalidade por
campo autoral antes de qualquer resolução de `ContentDraftFix`. A linha diagnóstica
passa a expor variantes e repetição máxima de `document_guidance` e `digital_triage`,
além de `broken_phrases` e `short_fields`.

Motivo: rascunhos previdenciários podiam passar em checks estruturais mesmo contendo
frases com ordem artificial e repetição de termo completo entre abertura, documentos e
triagem. Isso cria falso conforto para conteúdo jurídico em escala: o texto fica
bloqueado, mas o pipeline aprenderia um padrão ruim se o problema não virasse contrato
executável.

Consequencia: o pipeline previdenciário deixa de reaproveitar snippets degradados dos
drafts de expansão, invalida rascunhos finais com frases quebradas conhecidas e gera
orientação documental/triagem por categoria e faceta. O lote continua bloqueado:
`approval=false`, `publication=false`, `content_fix_remaining=370`, sem render, sitemap
ou `public_path`.

Autocrítica de engenharia: o ganho é real porque a falha apareceu primeiro como RED
com 31 ocorrências e só ficou verde após corrigir gerador e dados derivados. É seguro
porque não remove blocker autoral e não promove página pública. Ainda falta medir
similaridade semântica profunda e amostras por lane; a próxima melhoria deve continuar
nessa direção antes de qualquer resolvedor lane-specific.

## 2026-06-12 - Fonte oficial previdenciária entra no gate autoral

Decisao: o `previdenciario-authorial-gate` deve calcular presença de fonte oficial por
registro e diversidade mínima de URLs oficiais, expondo `official_sources`,
`source_variants` e `max_source_repeat` no `cmd/check all`.

Motivo: naturalidade textual sem fonte oficial rastreável ainda cria risco jurídico e
editorial. O lote previdenciário precisa provar, no mesmo diagnóstico operacional, que
os rascunhos permanentes bloqueados carregam referência oficial reconhecível antes de
qualquer resolvedor autoral.

Consequencia: o gate conta URLs `gov.br` e `planalto.gov.br`, exige fonte oficial em
todos os 370 registros previdenciários e reprova baixa diversidade. O estado atual é
`official_sources=370`, `source_variants=7`, `max_source_repeat=148`, com publicação
e aprovação ainda bloqueadas.

Autocrítica de engenharia: a regra melhora governança de fonte, mas ainda não mede
se a URL é específica o bastante para cada benefício/faceta. A próxima camada deve
pontuar especificidade da fonte e amostras por lane antes de qualquer liberação.

## 2026-06-12 - Matriz previdenciária não pode depender só de URL ampla

Decisao: o `previdenciario-authorial-gate` deve reprovar matriz previdenciária sem
ao menos uma URL oficial específica de benefício ou serviço. URLs institucionais,
diretórios amplos e páginas gerais de serviço digital podem apoiar a matriz, mas não
podem ser a única âncora de fonte.

Motivo: auditoria read-only mostrou que CNIS usava fonte ampla (`Meu INSS` e home do
INSS) enquanto havia serviço oficial específico para Extrato de Contribuição (CNIS).
Isso poderia mascarar fonte ampla como fonte suficiente para páginas futuras em escala.

Consequencia: a matriz `previdenciario-aposentadoria-cnis-incompleto` passou a usar
`https://www.gov.br/pt-br/servicos/emitir-extrato-de-contribuicao-cnis`; a auditoria
URL-level ganhou registro próprio; o gate expõe `benefit_specific_matrices=5` e
`broad_only_matrices=0`. Publicação continua bloqueada.

Autocrítica de engenharia: a melhoria fecha um falso negativo concreto, mas ainda não
classifica suficiência por faceta fina. Notícias oficiais, páginas de diretório e
serviços operacionais precisam de avaliação mais forte antes de qualquer resolvedor
autoral previdenciário.

## 2026-06-12 - Fonte primária previdenciária deve priorizar serviço específico

Decisao: resoluções previdenciárias devem selecionar, como primeira fonte, a URL mais
específica disponível. Serviços oficiais e páginas específicas de benefício têm
prioridade sobre diretórios, canais digitais amplos e notícias; notícia oficial pode
apoiar contexto, mas não deve aparecer como fonte primária de matriz.

Motivo: a auditoria do ciclo mostrou que BPC/LOAS e auxílio por incapacidade já tinham
fonte específica na matriz, mas a resolução ordenava alfabeticamente e colocava a URL
ampla primeiro. Também mostrou que exigência parada e cessação/laudo ainda dependem de
fonte fraca como primária ou de notícia contextual, o que não pode ser mascarado como
prova suficiente para conteúdo jurídico em escala.

Consequencia: `batchsourcespecificity.BuildSpecificSourceURLsByMatrix` passa a ordenar
fontes por prioridade editorial/auditável; o `previdenciario-authorial-gate` expõe
`primary_specific_sources`, `weak_primary_sources`, `news_sources`,
`news_primary_sources` e `news_context_sources`. O estado atual fica bloqueado e
explícito: `primary_specific_sources=222`, `weak_primary_sources=148`,
`news_primary_sources=0`, `news_context_sources=1`, `approval=false` e
`publication=false`.

Autocrítica de engenharia: o ganho reduz falso negativo real sem inventar fonte oficial
para exigência ou cessação. É seguro porque preserva rascunhos permanentes, mantém os
148 casos fracos como blocker calculado e não toca `published_manifest`, `content/pages`
ou `public/`. A otimização é real porque remove uma ordenação alfabeticamente ingênua
que prejudicava 148 resoluções já cobertas por fonte específica. A dúvida restante é
substantiva: facetas de exigência, cessação, recurso e prova nova precisam de fonte
oficial própria ou bloqueio mais duro antes de qualquer resolvedor autoral.

## 2026-06-12 - Paid-intent previdenciário fraco permanece informativo

Decisao: no `batch-previdenciario-digital`, um registro só pode permanecer em
`paid_intent_passed_blocked_publication` quando o corpo tiver core comercial forte.
Se o corpo fica abaixo do limiar previdenciário de 7 e o CTA é a parte mais intensa,
o registro deve ficar na lane informativa previdenciária bloqueada, ainda disponível
para expansão interna, mas sem ser tratado como comercial pronto.

Motivo: a auditoria dos 7 comerciais mostrou que todos tinham
`core_paid_business_score=6` e `cta_paid_business_score=9`; após recalcular a regra,
o dado real revelou 11 registros com esse padrão. O status comercial antigo podia
criar falso positivo: o CTA e sinais genéricos de documentos/protocolo compensavam
corpo ainda informativo, administrativo ou sem fonte recursal/específica suficiente.

Consequencia: `paidintent.evaluateParts` flexibiliza `PassedBlockedStatus` fraco no
batch previdenciário para `paid_intent_flexible_previdenciario_informational_blocked_publication`.
O gate previdenciário passa a expor `informational_weak_commercial_core=11`,
`commercial=0`, `commercial_weak_core=0` e `commercial_strong_core=0`. O plano de
release continua bloqueado e o paid-intent comercial agregado cai de 1.857 para 1.850.

Autocrítica de engenharia: a mudança reduz um falso positivo comercial real e mantém
coerência com a exceção informativa previdenciária. É segura porque não publica,
não remove `ContentDraftFix` e não impede expansão interna bloqueada. A validação
foi real: falhou primeiro por dados persistidos stale e só passou depois de regenerar
`batch_paid_intent_gates`. O risco restante é o limiar 7 ainda ser heurístico; a
próxima camada deve cruzar fonte recursal/exigência/cessação e qualidade do corpo
antes de qualquer tentativa de transformar item previdenciário em comercial forte.

## 2026-06-12 - Fonte estável previdenciária deve ser separada de contexto

Decisao: o gate autoral previdenciário passa a diferenciar matriz com fonte oficial
estável e específica de matriz que tem apenas apoio contextual, notícia, página ampla
ou página de assunto. URLs oficiais contextuais continuam úteis como referência, mas
não podem contar como prova de fonte primária estável para publicação futura.

Motivo: o estado anterior já expunha `benefit_specific_matrices=5`, mas esse número
ainda podia dar falso conforto porque páginas de notícia/assunto ou canais amplos
podiam ser vistas como especificidade suficiente. A inspeção das cinco matrizes mostrou
que auxílio por incapacidade, BPC/LOAS e CNIS têm fonte estável específica, enquanto
cumprimento de exigência e benefício cessado/laudo ainda dependem de canal amplo e
contexto editorial.

Consequencia: `previdenciario-authorial-gate` calcula `stable_specific_matrices=3`
e `contextual_only_matrices=2`, e o `cmd/check all` passa a mostrar ambos os números.
A página de assunto do Atestmed e notícias do INSS ficam fora da métrica de fonte
estável. O lote segue bloqueado com `approval=false`, `publication=false`,
`content_fix_remaining=370`, `render_allowed=false`, `sitemap_allowed=false` e sem
alteração em `published_manifest`, `content/pages.json` ou `public/`.

Autocrítica de engenharia: a melhoria reduz um falso positivo de fonte e deixa claro
qual lacuna ainda precisa de pesquisa oficial. É segura porque endurece diagnóstico
sem promover conteúdo, sem apagar rascunhos permanentes e sem usar Git para voltar
estado. A otimização é real porque impede o próximo ciclo de tratar notícia/assunto
como se fosse base normativa ou serviço específico. A validação foi real nos dados
atuais: o RED falhou por métrica ausente e depois expôs uma suposição errada de
contagem até a classificação excluir contexto Atestmed. O risco restante é substantivo:
exigência parada, cessação/laudo, recurso e prova nova ainda precisam de fonte oficial
mais própria ou bloqueio editorial mais explícito antes de resolver conteúdo autoral.

## 2026-06-12 - Cessação/laudo usa serviço oficial de revisão por incapacidade

Decisao: a matriz `previdenciario-beneficio-cessado-laudo` passa a usar o serviço
oficial `Solicitar Revisão Administrativa de Benefício por Incapacidade` como fonte
primária específica. A página ampla de benefícios por incapacidade fica como apoio e
a página Atestmed permanece apenas como contexto auditado, sem contar como fonte
estável principal.

Motivo: a URL oficial de revisão administrativa por incapacidade foi confirmada em
2026-06-12 por GET leve com status 206 e título compatível. Slugs testados para
recurso e cumprimento de exigência retornaram 404, então não foram usados. A matriz
de cessação/laudo tinha fonte contextual suficiente para pesquisa, mas fraca demais
para futura página pública jurídica sobre benefício cessado com laudo atualizado.

Consequencia: o lote previdenciário passa de `stable_specific_matrices=3` para 4,
`contextual_only_matrices=2` para 1, `primary_specific_sources=222` para 296 e
`weak_primary_sources=148` para 74. O gate autoral foi endurecido para esses novos
limiares, e os derivados bloqueados foram recalculados. `render_allowed`,
`sitemap_allowed`, `publication_allowed` e `public_path` continuam bloqueados/vazios.

Autocrítica de engenharia: a mudança reduz um blocker real sem inventar fonte para
exigência parada. É segura porque a fonte foi verificada no dia, auditada como
referência sem scraping/ingestão e não promoveu página pública. A otimização é real
porque 74 resoluções deixam de depender de diretório/notícia como primária. A
validação pegou dois riscos úteis: paid-intent deve ser regenerado depois do refresh,
e a nova fonte expôs repetição textual em drafts de cessação/laudo; ambos foram
corrigidos no gerador/pipeline antes do checkpoint. Risco restante: exigência parada
ainda depende de Meu INSS/notícia e precisa de fonte oficial mais própria ou blocker
editorial explícito por faceta.

## 2026-06-12 - Exigência parada fica bloqueada antes de final draft

Decisao: notícia oficial, página de assunto e canal digital amplo como Meu INSS são
fontes contextuais, não fontes específicas suficientes para liberar `LockedStatus` em
`batch_source_specificity_resolutions`. Quando a matriz só tiver esse tipo de fonte,
o candidato deve ficar em `final_source_blocked_needs_specific_url`, com motivo e
detalhe de fonte necessária, antes de gerar final draft.

Motivo: `previdenciario-cumprimento-exigencia-parado` ainda depende de Meu INSS e de
notícia sobre anexar documentos. Slugs de serviço testados para cumprimento de
exigência retornaram 404 em 2026-06-12, então não há base para inventar fonte
específica. Tratar essas URLs como específicas gerava falso conforto e permitia final
draft para 74 itens cuja fonte ainda é insuficiente.

Consequencia: 74 candidatos previdenciários de exigência passam a ficar bloqueados por
fonte antes de final draft; `batch_final_authorial_drafts` cai de 2.220 para 2.146
registros; no gate previdenciário, `candidate_count=370`, `final_drafts=296`,
`official_sources=296`, `primary_specific_sources=296` e `weak_primary_sources=74`.
O plano editorial passa a calcular `candidate_count=2146` e próximo batch de correção
autoral como `batch-saude-suplementar-digital`, enquanto exigência fica pendente de
fonte específica ou blocker editorial mais fino.

Autocrítica de engenharia: a mudança é segura porque remove drafts finais sem fonte
suficiente, mas preserva rascunhos/candidatos bloqueados e não toca publicação pública.
É otimização real porque evita validar conteúdo autoral sobre base contextual fraca e
obriga a próxima pesquisa oficial a resolver uma lacuna concreta. A validação foi real:
quebrou release rehearsal, readiness e contadores do gate até paid-intent, readiness,
estratégia e testes serem recalculados. Risco restante: o plano de release agora avança
para saúde suplementar; o próximo ciclo precisa manter a lacuna de exigência visível
para não perder o P0 previdenciário.

## 2026-06-12 - Blockers de fonte em lote entram no check global

Decisao: `batch-source-blocker-report` passa a fazer parte do `cmd/check all` e
expõe, por lote/matriz, candidatos bloqueados em
`batch_source_specificity_resolutions`. O relatório é calculado sobre dados reais,
não sobre o plano editorial do próximo lote.

Motivo: depois que exigência parada ficou bloqueada antes de final draft, o plano de
release passou a apontar a próxima correção autoral para saúde suplementar. Isso é
útil para continuidade, mas podia esconder a lacuna previdenciária de fonte. O blocker
precisa permanecer visível enquanto não houver fonte oficial específica ou decisão
editorial bloqueada por faceta.

Consequencia: o check global mostra `blocked_candidates=74`, `blocked_matrices=1`,
`top_batch=batch-previdenciario-digital`,
`top_matrix=previdenciario-cumprimento-exigencia-parado`, `publication=false` e
`source_url_variants=2`. O check também falha se algum blocker em lote vier com
`render_allowed`, `sitemap_allowed`, `publication_allowed` ou `public_path`.

Autocrítica de engenharia: o que podemos melhorar, e por que? A próxima camada deve
transformar esse agregado em decisão editorial/fonte por faceta, não apenas em
contador. É seguro? Sim, porque só lê resoluções bloqueadas e endurece diagnóstico,
sem publicar, renderizar, gerar sitemap ou apagar rascunhos permanentes. É otimização
real? Sim, porque evita perder tempo procurando a lacuna por inspeção manual quando
o plano editorial aponta outro lote. É teste real sem falso positivo ou negativo? O
teste RED falhou por check inexistente e o GREEN usa o arquivo versionado atual; o
risco restante é o teste depender da contagem atual de 74, então mudanças futuras no
conteúdo autoral ou na fonte devem atualizar a expectativa junto com a nova realidade.

## 2026-06-12 - Candidatos NotFound não contam como fonte específica

Decisao: URLs oficiais candidatas com checagem atual `NotFound` ou 404 entram apenas
como evidência negativa bloqueada e não podem contar como fonte específica auditada.
`batchsourcespecificity` passa a carregar `live_check_status` da auditoria e rejeitar
esses casos no classificador de fonte específica.

Motivo: três variações oficiais de serviço para cumprimento de exigência do INSS foram
testadas em 2026-06-12 por GET leve e retornaram `NotFound`. Usar qualquer uma delas
para desbloquear `previdenciario-cumprimento-exigencia-parado` seria inventar fonte.
A pesquisa negativa precisa ficar versionada para o próximo ciclo não repetir o mesmo
teste nem tratar ausência de fonte como permissão.

Consequencia: `data/source-audit/batch_source_urls.jsonl` registra as três URLs
candidatas como `servico_digital_govbr_candidate_not_found`, ligadas à matriz de
exigência, com scraping, ingestão, render, sitemap, publicação e caminho público
fechados. `batch-source-blocker-report` permanece com `blocked_candidates=74` e
`source_url_variants=2`, porque as URLs negativas não entram como fontes selecionadas.

Autocrítica de engenharia: o que podemos melhorar, e por que? A próxima etapa deve
criar decisão editorial por faceta para exigência parada, separando demora sem
resposta, documento complementar, fase recursal e divergência cadastral, ou encontrar
fonte oficial atual realmente específica. É seguro? Sim, porque a mudança só reduz
falso positivo de fonte e preserva bloqueio total. É otimização real? Sim, porque
evita repetir pesquisa oficial negativa e impede que uma URL inexistente destrave
final draft. É teste real sem falso positivo ou negativo? O RED falhou por campo
ausente e o GREEN passa a usar o status real da auditoria; o risco restante é uma URL
oficial futura surgir com outro slug, então a pesquisa deve continuar aberta, mas sem
aproveitar endpoints já verificados como inexistentes.

## 2026-06-12 - Saúde suplementar exige diversidade autoral antes de resolver blocker

Decisao: `batch-saude-suplementar-digital` não pode usar o resolvedor autoral genérico
enquanto o lote não provar diversidade real em campos autorais centrais. O resolvedor
passa a reprovar saúde suplementar com
`review_content_fix_resolver_saude_authorial_diversity_gate_missing` quando uma mesma
orientação documental ou triagem digital domina o lote.

Motivo: os checks formais estavam verdes, titles/metas/canonicals estavam únicos e o
lote tinha 370 rascunhos finais bloqueados, mas auditoria read-only mostrou que
`document_guidance` e `digital_triage` repetiam quase integralmente em 367 de 370
registros. Remover `ContentDraftFix` nessa condição seria falso positivo editorial:
pareceria avanço de revisão, mas manteria conteúdo mecânico demais para escala jurídica.

Consequencia: a tentativa inicial de resolver saúde foi corrigida para frente por
código versionado. Foi criado um RED no resolvedor, implementado gate de diversidade
por lote e adicionado `cmd/reblock-review-content-fix` para recolocar a pendência
autoral e `content_draft_required=true` sem usar Git para retornar estado anterior.
O lote de saúde permanece com 370 revisões bloqueadas por conteúdo autoral e
CTA/manifesto, todos os manifestos continuam noindex e nenhuma URL pública foi criada.

Autocrítica de engenharia: a melhoria real é impedir que validação por registro mascare
repetição em lote. É seguro porque a correção endurece o gate e reabre bloqueio
editorial sem publicar, renderizar, inserir sitemap ou apagar rascunhos permanentes.
É otimização real porque evita desperdiçar ciclos posteriores com um aceite autoral
fraco e transforma relatório de agente em prova executável. A validação foi real:
o teste falhou antes do gate, passou depois da implementação e `cmd/check all` leu os
dados versionados já reparados. O risco restante é o limiar de 70% ainda ser sintático;
o próximo ciclo deve criar diversidade semântica por faceta/documento/triagem, não
apenas evitar igualdade literal.

## 2026-06-12 - Previdenciário resolve autoral apenas para registros com fonte e final draft

Decisao: `batch-previdenciario-digital` pode remover `ContentDraftFix` somente dos registros que possuem rascunho final bloqueado, fonte oficial selecionada, qualidade por registro e manifesto em estado `public_manifest_blocked_seo_review_pending`. Registros da matriz `previdenciario-cumprimento-exigencia-parado` sem rascunho final continuam com correção autoral no review e bloqueio de fonte em `batch-source-blocker-report`.

Motivo: o lote previdenciário mistura lane informativa e uma lacuna real de fonte específica. Tratar os 370 registros como homogêneos criaria falso positivo: 296 tinham base suficiente para remover o blocker autoral, mas 74 ainda dependem de fonte oficial específica ou decisão editorial formal antes de final draft. A correção segura é parcial, mensurável e bloqueada para publicação.

Consequencia: `reviewcontentfixresolver` passou a permitir resolução parcial apenas para `batch-previdenciario-digital`, preservando registros source-blocked sem publicar. `resolve-review-content-fix -batch batch-previdenciario-digital` reportou `reviewed=370`, `resolved_reviews=296`, `updated_manifest=296`, `remaining_content_fixes=74`, `remaining_manifest_content=0`, `publication=false`. O plano editorial avançou para `release_rehearsal_next_action_complete_review_cta_manifest_fixes_in_batch` em `batch-consumidor-financeiro-digital`, mas `published_manifest`, `public/`, `content/pages.json`, render, sitemap, publicação e `public_path` continuam fechados.

Autocrítica: a mudança é segura porque não resolve fonte ausente, não move páginas para público e torna explícita a diferença entre revisão autoral resolvida e fonte ainda bloqueada. É otimização real porque evita manter 296 registros presos por causa dos 74 sem fonte, sem mascarar estes 74. A validação exercitou dados reais e pegou um falso pressuposto inicial: manifestos source-blocked já tinham `content_draft_required=false`, então o review é a camada que preserva a pendência autoral nesses casos. Risco remanescente: os 74 ainda precisam de fonte oficial específica atual ou decisão editorial documentada, e o próximo ciclo de CTA/manifesto deve continuar adaptando testes SEO/editoriais quando copy, CTA ou contrato mudarem.

## 2026-06-12 - Saúde suplementar só resolve blocker autoral com diversidade provada

Decisao: `batch-saude-suplementar-digital` pode remover `ContentDraftFix` somente depois de prova em lote para variação de `opening`, `document_guidance`, `digital_triage` e documentos de CTA, além de score humano/qualidade por registro, paid-intent recalculado e manifesto/review ainda bloqueados para publicação.

Motivo: o lote tinha dados de origem ricos, mas o finalizador anterior colapsava campos finais em poucas variantes. Aceitar apenas checks verdes por registro criava falso positivo: texto formalmente válido, mas mecânico em escala.

Consequencia: o finalizador de saúde passou a ter funções específicas por subtema e faceta, sem reaproveitar o mesmo checklist em abertura, documentos, triagem e CTA. `batch_final_authorial_drafts` e `batch_paid_intent_gates` foram regenerados, `resolve-review-content-fix -batch batch-saude-suplementar-digital` removeu 370 blockers autorais e `batch_public_manifest_gates` ficou com `content_draft_required=false` para saúde, mantendo `manifest_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`.

Autocrítica: a correção é segura para o estado bloqueado porque não promove publicação e foi validada por `./tools/check-all`. É otimização real porque reduz falso conforto anti-template e atualiza o plano de release para o próximo batch autoral (`batch-sucessorio-digital`). O risco remanescente é a diversidade ainda ser medida por variantes textuais e não por análise semântica profunda; próximo ciclo deve ampliar essa inteligência antes de CTA/manifesto final.

## 2026-06-12 - Sucessório só resolve blocker autoral com variação por subtema e faceta

Decisao: `batch-sucessorio-digital` pode remover `ContentDraftFix` somente depois de prova em lote para variação de `opening`, `document_guidance`, `digital_triage` e documentos de CTA, com rascunhos finais bloqueados, paid-intent recalculado e manifesto/review ainda proibidos de publicar.

Motivo: sucessório já tinha fonte específica e intenção digital suficientes para continuar a vertical bloqueada, mas o finalizador genérico produzia abertura, documentos, triagem e CTA repetitivos. Aceitar o resolver autoral nessa condição criaria falso positivo editorial parecido com o que já foi encontrado em saúde: conteúdo formalmente válido por registro, mas fraco em escala.

Consequencia: o finalizador sucessório passou a separar vocabulário por abertura, prova documental, recorte operacional, triagem, risco e CTA; `batch_final_authorial_drafts` e `batch_paid_intent_gates` foram regenerados; `resolve-review-content-fix -batch batch-sucessorio-digital` removeu 370 blockers autorais; `batch_public_manifest_gates` ficou com `content_draft_required=false` para sucessório, mantendo `manifest_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`. O plano editorial avançou o próximo blocker autoral para `batch-trabalhista-digital`, com 666 blockers autorais restantes e `published_manifest` ainda vazio.

Autocrítica: a melhoria real foi transformar uma família inteira em estado autoral bloqueado mais maduro sem abrir publicação. É seguro porque a mudança preserva `noindex`, não altera `public/`, `content/pages.json` nem `published_manifest`, e recalcula dados derivados depois de mudar copy autoral. É otimização real porque reduz repetição estrutural e move o próximo P0 para trabalhista com evidência calculada, sem esconder os 74 blockers previdenciários de fonte. A validação foi real nos dados atuais: o teste RED falhou por baixa variação documental, o checker completo pegou trigramas repetidos, o paid-intent acusou dado stale depois da copy nova e só passou após regeneração; risco remanescente é a métrica ainda ser textual, então as próximas camadas devem fortalecer similaridade semântica, amostragem humana e gates SEO/CTA antes de qualquer promoção pública.

## 2026-06-12 - Trabalhista só resolve blocker autoral com finalizador próprio

Decisao: `batch-trabalhista-digital` pode remover `ContentDraftFix` somente depois de finalizador próprio e prova em lote para variação de `opening`, `document_guidance`, `digital_triage` e documentos de CTA, com rascunhos finais bloqueados, paid-intent recalculado e manifesto/review ainda proibidos de publicar.

Motivo: o lote trabalhista usava o finalizador genérico de direito do trabalho, repetindo abertura, documentos de contrato/jornada e triagem em massa. O problema não era falta de tamanho de texto, mas composição mecânica: os campos reutilizavam a mesma lista documental e o mesmo risco em abertura, prova, triagem e CTA.

Consequencia: o finalizador trabalhista passou a separar subtemas de acidente/estabilidade, horas extras, justa causa, rescisão indireta e verbas rescisórias; também separa facetas como prazo, fonte, prova digital, negativa, recurso, divergência e atendimento digital. `batch_final_authorial_drafts` e `batch_paid_intent_gates` foram regenerados; `resolve-review-content-fix -batch batch-trabalhista-digital` removeu 370 blockers autorais; `batch_public_manifest_gates` ficou com `content_draft_required=false` para trabalhista, mantendo `manifest_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`. O plano editorial avançou o próximo blocker autoral para `batch-previdenciario-digital`, com 296 blockers autorais restantes e 74 candidatos previdenciários ainda bloqueados por fonte.

Autocrítica: a mudança é segura para o estado bloqueado porque não promoveu publicação, não alterou `public/`, `content/pages.json` ou `published_manifest`, e manteve o blocker previdenciário exposto. É otimização real porque reduz repetição estrutural em 370 final drafts e fecha a camada autoral dos lotes comerciais atuais sem afrouxar gate. A validação foi real nos dados atuais: o RED falhou com uma abertura dominante, o checker completo expôs repetições por subtema e o gerador só passou depois de ajustes específicos em horas extras, justa causa, rescisão indireta e verbas rescisórias. Risco remanescente: a métrica continua textual; previdenciário exige lógica própria de lane informativa, fonte fina e diversidade semântica antes de qualquer CTA/manifesto final.

## 2026-06-12 - CTA/manifesto de consumidor só resolve com contexto documental bloqueado

Decisao: `batch-consumidor-financeiro-digital` pode remover `ManifestCTAFix` dos reviews somente quando review, manifesto e final draft concordam por identidade, todos continuam bloqueados para publicação e o CTA do final draft registra origem, intenção, documentos, contratação online, honorários e ausência de promessa ou vantagem indevida.

Motivo: o lote consumidor já tinha conteúdo autoral e paid-intent comercial bloqueados, mas o review ainda carregava CTA/manifesto pendente. Aceitar apenas CTA genérico no review criaria falso positivo: pareceria pronto para release, sem provar que a mensagem contextual do final draft respeita documentos esperados, atendimento digital, ética OAB, origem rastreável e bloqueio público.

Consequencia: foi criado `internal/reviewctamanifestresolver` e `cmd/resolve-review-cta-manifest-fix`. O resolvedor removeu `ManifestCTAFix` de 370 reviews consumidores, marcou `cta_status=cta_contextual_reviewed_blocked_publication`, preservou `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`, e deixou o plano editorial em `candidate_count=2146`, `publication_allowed=0`, `release_ready=0`, `next_batch=batch-familia-digital` e 1776 pendências de CTA/manifesto restantes.

Correção para frente: a primeira escrita do resolvedor expôs uma falha no writer de reviews: `WriteRecords` criava/truncava o JSONL antes de validar todos os registros e poderia deixar `batch_candidate_reviews.jsonl` vazio quando uma validação falhasse. A resposta não foi usar Git para voltar estado; o writer foi tornado transacional em memória, o pipeline foi reconstruído por ferramentas versionadas, os resolvedores autorais anteriores foram reaplicados e o CTA de consumidor foi reaplicado. A validação ampliada também encontrou contrato stale no primeiro candidato consumidor, que ainda esperava blockers já resolvidos; o teste foi adaptado para exigir que o candidato continue bloqueado pelos demais gates, sem reintroduzir `required_fixes_pending`. Essa decisão reforça que dados editoriais são permanentes e que erro operacional exige guarda executável, recalculo e checkpoint claro.

Autocrítica: a melhoria é real porque transforma CTA/manifesto em gate executável e reduz 370 pendências sem abrir render, sitemap ou publicação. É seguro para o estado atual porque a validação leu dados reais, manteve `published_manifest` vazio e o comando é idempotente no consumidor. O teste é real contra falsos positivos de CTA sem documentos, mas ainda é majoritariamente sintático: próximas camadas devem ampliar similaridade e qualidade semântica do CTA, validar família em lote, adaptar SEO/search appearance se a copy mudar e manter os 74 previdenciários sem fonte fora de qualquer promoção.

## 2026-06-12 - CTA/manifesto comercial em lote e score editorial sem metadado técnico

Decisao: o score de rascunho final deve avaliar texto editorial, documentos e contratação do CTA, mas não deve contar `Origem:` e `Intent:` como conteúdo autoral. Esses identificadores continuam obrigatórios para rastreabilidade e para o resolvedor de CTA/manifesto, mas não podem gerar falso positivo de repetição por slug. O resolvedor de CTA/manifesto também não pode remover `ManifestCTAFix` se `ContentDraftFix` ainda estiver pendente.

Motivo: ao exigir `Intent` exato no CTA, os slugs passaram a aparecer em `term`, caminho e intent. Isso derrubava scores por `repeated_ngram` mesmo quando o corpo editorial computava 100/0. Ao mesmo tempo, o ciclo expôs repetições reais em família, saúde, sucessório e trabalhista; essas foram corrigidas no gerador, não mascaradas no validador.

Consequencia: `batchfinaldrafts.Record` ganhou `EditorialQualityText`, usado por validação e reuso de final drafts. O pipeline invalida registros com score armazenado divergente do score editorial computado. O gerador foi refinado para separar abertura, prova, triagem, risco e CTA nos lotes comerciais; `batch_paid_intent_gates` foi recalculado. Cinco batches comerciais ficaram com `required_fixes=[]` e `cta_status=cta_contextual_reviewed_blocked_publication`, todos ainda bloqueados para publicação. Previdenciário preserva 74 candidatos sem fonte e 296 pendências de CTA/manifesto como próximo P0.

Autocrítica: a melhoria reduz falso positivo de teste sem remover a proteção anti-template, porque `quality.AnalyzeText` e `humanscore.ScoreText` ainda leem a copy editorial e pegaram repetições reais após a mudança. É seguro porque não abriu `manifest_allowed`, render, sitemap, publicação nem `public_path`, e porque o incidente de subagente read-only foi registrado no ledger em vez de apagado por Git. A otimização é real: o plano caiu de 1776 para 296 pendências de CTA/manifesto e manteve `publication_allowed=0`. Risco remanescente: a métrica ainda é textual; o próximo ciclo precisa resolver CTA previdenciário parcialmente sem tocar nos 74 source-blocked e depois fortalecer similaridade semântica/expansão antes de qualquer promoção pública.

## 2026-06-12 - CTA/manifesto previdenciário parcial preserva fonte bloqueada

Decisao: `batch-previdenciario-digital` pode remover `ManifestCTAFix` somente dos 296 registros que possuem final draft e fonte específica travada como referência. Os 74 registros de `previdenciario-cumprimento-exigencia-parado` continuam com `ContentDraftFix` e `ManifestCTAFix` enquanto estiverem em manifesto `SourceBlockedStatus`, `index_policy=noindex`, render/sitemap/publicação falsos e `public_path=""`.

Motivo: o lote previdenciário mistura conteúdo informativo com fonte suficiente e uma lacuna real de fonte oficial específica. Tratar os 370 registros como homogêneos criaria falso positivo de publicação/release: 296 tinham CTA final rastreável, documentos, origem, intent, contratação online e honorários; 74 ainda não tinham base oficial específica nem final draft. O mesmo ciclo mostrou que final draft legado sem caminho online explícito poderia ser reaproveitado pelo refresh; esse reuso agora é bloqueado na origem do pipeline.

Consequencia: `reviewctamanifestresolver` ganhou resolução parcial controlada para o remanescente source-blocked previdenciário, e `batchcandidatepipeline` passou a invalidar CTA previdenciário sem `Contratação:`, `online` e `honorários`. `resolve-review-cta-manifest-fix -batch batch-previdenciario-digital` reportou `reviewed=370`, `resolved_reviews=296`, `remaining_cta_manifest_fixes=74`, `publication=false`. O plano editorial avançou para `release_rehearsal_next_action_complete_manifest_seo_review_in_batch` em `batch-consumidor-financeiro-digital`, com `candidate_count=2146`, `publication_allowed=0` e `release_ready=0`.

Correção operacional: resolvedores que escrevem os mesmos JSONL editoriais não devem ser paralelizados entre si. Uma execução paralela durante o ciclo corrompeu parcialmente `batch_candidate_reviews.jsonl`; a correção foi reconstruir a cadeia por `refresh-batch-candidate-pipeline` e reaplicar os resolvedores em ordem sequencial, sem usar Git para voltar estado. Esse incidente reforça que paralelismo útil deve ser reservado para leitura, auditoria, testes independentes ou escrita em escopos disjuntos.

Autocrítica: a mudança é segura porque não publica, não renderiza, não inclui sitemap e preserva o blocker de fonte. A otimização é real porque elimina 296 pendências sem mascarar as 74 lacunas que continuam P0. A validação foi real nos dados atuais: falhou primeiro por CTA legado, depois por contrato stale e por contador previdenciário stale, e só passou após refresh, paid-intent recalculado, testes focados e `cmd/check all`. Risco remanescente: manifesto SEO pode virar falso conforto se title/meta/canonical passarem sem avaliar duplicidade semântica, utilidade humana, CTA e fonte; o próximo ciclo deve fortalecer essa camada antes de qualquer promoção pública.

## 2026-06-12 - Manifesto SEO revisado continua bloqueado antes de publicação

Decisao: manifesto público bloqueado passa a ter um estado intermediário `public_manifest_blocked_seo_reviewed`. Esse estado remove apenas a pendência de revisão SEO do manifesto, mantendo fonte travada como referência, `index_policy=noindex`, `manifest_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `publication_allowed=false` e `public_path=""`.

Motivo: `refine-batch-seo` já refinava title/meta em prepublication, manifesto e final draft, mas o release rehearsal continuava sem uma forma persistente de distinguir SEO pendente de SEO revisado ainda bloqueado. Resolver isso por remoção de blocker sem estado versionado mascararia o pipeline. O novo estado cria rastreabilidade sem transformar SEO básico em autorização de publicação.

Consequencia: `batchpublicmanifest` aceita `SEOReviewedStatus` bloqueado e exige `seo_review_required=false`; `batchfinaldrafts` continua tratando esse manifesto como elegível para final draft bloqueado; `manifestseoresolver` só aplica o estado quando review não tem `required_fixes`, CTA está revisado bloqueado, final draft está bloqueado e title/meta estão sincronizados. Em consumidor financeiro, 370 manifestos saíram de `release_rehearsal_manifest_seo_review_pending`, e o próximo batch calculado passou a ser `batch-familia-digital`; `publication_allowed` e `release_ready` continuam 0.

Autocrítica: a mudança é segura porque cria maturidade interna sem tocar `public/`, `content/pages.json` ou `published_manifest`. É otimização real porque reduz o plano de blockers de 2146 para 1776 e transforma o próximo avanço em lote familiar calculado. A validação foi real porque contratos quebraram ao não reconhecer o novo estado e só passaram depois de adaptar manifesto, final drafts, release rehearsal e check global. Risco remanescente: title/meta dentro de orçamento não provam qualidade semântica, então os próximos ciclos devem medir intenção única, naturalidade de snippet, duplicidade e utilidade humana antes de qualquer release público.

## 2026-06-12 - Unicidade SEO não pode depender de contador artificial

Decisao: `refine-batch-seo` não pode resolver duplicidade de title ou metadescrição por sufixo numérico artificial. Quando houver colisão, o algoritmo deve usar rótulos semânticos do recorte, base jurídica compacta por matriz e diagnóstico explícito; se ainda não houver unicidade natural, deve falhar em vez de gravar texto mecânico.

Motivo: ao aplicar manifesto SEO em família, a inspeção do diff mostrou titles/metas bloqueados com sufixos `#NN`. Embora continuassem noindex e fora de publicação, chamar essa camada de SEO revisado criaria falso conforto editorial e aproximaria o conteúdo de aparência mecânica. A solução correta é melhorar o algoritmo e recalcular dados derivados, não ajustar testes para aceitar contador.

Consequencia: `batchseorefinement` passou a gerar alternativas semânticas por faceta (`documento posterior`, `recurso`, `erro cadastral`, `boa-fé`, `prova técnica`, `via administrativa`, `histórico previdenciário` e outras), usar bases compactas por matriz jurídica e aceitar a exceção previdenciária source-blocked sem final draft sem promover publicação. As camadas `batch_prepublication_gates`, `batch_public_manifest_gates`, `batch_final_authorial_drafts` e `batch_paid_intent_gates` foram recalculadas. Consumidor e família somam 740 manifestos `public_manifest_blocked_seo_reviewed`; 1406 permanecem pendentes; 74 seguem bloqueados por fonte específica; `published_manifest` continua vazio.

Autocrítica: a melhoria é segura porque não abriu render, sitemap, publicação ou `public_path`, e `cmd/check all` confirmou `publication_allowed=0` e `release_ready=0`. É otimização real porque remove uma forma fraca de unicidade antes que ela vire padrão de escala. A validação foi real: a primeira versão do algoritmo falhou em dados reais, o diagnóstico mostrou rótulos insuficientes, a correção preservou combinações semânticas dentro do orçamento e os testes agora reprovam contador artificial. Risco remanescente: unicidade de title/meta ainda não prova profundidade do conteúdo; o próximo ciclo deve aplicar a camada em saúde suplementar e continuar fortalecendo similaridade semântica, snippet humano e anti-template antes de qualquer promoção pública.

## 2026-06-12 - Manifesto SEO de saúde suplementar avança sem publicação

Decisao: `batch-saude-suplementar-digital` pode sair de `public_manifest_blocked_seo_review_pending` para `public_manifest_blocked_seo_reviewed` somente mantendo `noindex`, flags públicas falsas e `public_path` vazio. Essa transição continua sendo maturidade interna, não release público.

Motivo: depois do saneamento semântico do refinador, saúde suplementar já tinha title/meta sincronizados, CTA/review bloqueados revisados e final drafts bloqueados. O próximo avanço calculado era remover apenas o blocker de manifesto SEO desse lote, preservando fonte ANS como referência e sem abrir render/sitemap.

Consequencia: `resolve-manifest-seo-review -batch batch-saude-suplementar-digital` marcou 370 manifestos como SEO revisados bloqueados. Consumidor, família e saúde somam 1110 manifestos nesse estado; 1036 seguem pendentes; 74 previdenciários continuam bloqueados por fonte específica. O plano editorial passou para `next_batch=batch-sucessorio-digital`, com `publication_allowed=0` e `release_ready=0`.

Autocrítica: a mudança é segura porque o diff público crítico continua vazio e `cmd/check all` passou. É otimização real porque reduz o próximo gargalo sem confundir SEO básico com aprovação jurídica. A validação foi real nos dados atuais, mas o risco remanescente é aceitar revisão SEO como sintática; sucessório deve continuar com análise de naturalidade, intenção única, snippet humano e anti-template antes de qualquer promoção pública.

## 2026-06-12 - Manifesto SEO sucessório avança sem publicação

Decisao: `batch-sucessorio-digital` pode avançar para `public_manifest_blocked_seo_reviewed` mantendo a mesma barreira: `noindex`, sem render, sem sitemap, sem publicação e sem `public_path`. A revisão SEO do manifesto continua subordinada a release gate completo.

Motivo: sucessório já tinha final drafts bloqueados, CTA/review resolvidos e dados SEO saneados pelo refinador semântico. O plano calculado apontava esse lote como próximo blocker de manifesto SEO; manter pendência depois da validação só atrasaria a próxima camada sem aumentar segurança.

Consequencia: 370 manifestos sucessórios foram marcados como SEO revisados bloqueados. O total passou para 1480 manifestos nesse estado, 666 pendentes e 74 source-blocked. O plano editorial passou a apontar `batch-trabalhista-digital`, ainda com `publication_allowed=0` e `release_ready=0`.

Autocrítica: a mudança é segura porque não altera artefatos públicos e foi validada por `cmd/check all`. É otimização real porque reduz o blocker agregado sem remover proteção jurídica/editorial. A validação é real para a transição de manifesto, mas ainda não prova qualidade profunda de conteúdo público; trabalhista deve continuar com análise de snippet, naturalidade, intenção única e anti-template antes de qualquer publicação.

## 2026-06-12 - Manifesto SEO trabalhista fecha os batches comerciais

Decisao: `batch-trabalhista-digital` pode avançar para `public_manifest_blocked_seo_reviewed` nos 370 registros, mantendo todos os bloqueios públicos. Com isso, os cinco batches comerciais atuais ficam com manifesto SEO revisado bloqueado, sem publicação.

Motivo: trabalhista já tinha conteúdo autoral específico, CTA/review resolvidos e title/meta saneados. O plano calculado apontava o lote como último batch comercial pendente de manifesto SEO; resolver essa camada permite concentrar o próximo ciclo na lane previdenciária sem misturar contextos.

Consequencia: 1850 manifestos comerciais estão em `public_manifest_blocked_seo_reviewed`; 296 previdenciários com final draft seguem pendentes de SEO; 74 previdenciários continuam source-blocked. `published_manifest`, `public/`, render, sitemap, publicação e `public_path` seguem fechados.

Autocrítica: a mudança é segura porque não publica e `cmd/check all` passou. É otimização real porque fecha uma camada horizontal dos batches comerciais e expõe o próximo gargalo previdenciário. A validação é real para os dados atuais, mas o próximo ciclo precisa respeitar a lane informativa previdenciária e não misturar os 296 registros com os 74 bloqueados por fonte.

## 2026-06-12 - Manifesto SEO previdenciário resolve apenas registros com final draft

Decisao: `manifestseoresolver` pode resolver `batch-previdenciario-digital` parcialmente: os 296 registros com final draft e fonte travada avançam para `public_manifest_blocked_seo_reviewed`; os 74 registros `public_manifest_blocked_source_specificity` continuam bloqueados, sem final draft, sem render, sem sitemap, sem publicação e sem `public_path`.

Motivo: depois dos batches comerciais, o próximo blocker era previdenciário, mas o lote mistura registros elegíveis e lacuna real de fonte. Exigir final draft dos 74 source-blocked parava o avanço correto; resolver os 370 mascararia ausência de fonte específica.

Consequencia: `manifestseoresolver` ganhou skip explícito para source-blocked seguro e teste de resolução parcial. O plano editorial deixou de ter blocker de manifesto SEO para candidatos com final draft e passou a apontar `release_rehearsal_next_action_review_cta_in_batch` em consumidor, com 2146 manifestos SEO revisados bloqueados e 74 source-blocked.

Autocrítica: a mudança é segura porque preserva os 74 bloqueios de fonte e não abre publicação. É otimização real porque fecha a camada de manifesto SEO dos candidatos com final draft e expõe o próximo gargalo de CTA/release sem misturar contextos. A validação é real nos dados atuais, mas o próximo ciclo deve investigar se `cta_draft_not_public` representa revisão final de release, render HTML bloqueado ou outro gate, sem promover CTA ou página por atalho.

## 2026-06-12 - Próximo passo após manifesto SEO é evidência de release, não CTA público

Decisao: depois que não há blocker de manifesto SEO, o release rehearsal deve priorizar `release_rehearsal_final_draft_blocked` como preparação de evidência de release bloqueada antes de qualquer CTA público. `cta_contextual_reviewed_blocked_publication` não deve ser tratado como pronto para render público.

Motivo: o plano estava apontando `release_rehearsal_cta_draft_not_public` porque o status do review não é `public_contextual`, mas todos os final drafts, paid-intent e reviews ainda estão bloqueados para publicação. Mandar o próximo agente “revisar CTA” nessa ordem poderia induzir promoção comercial antes de release evidence, render leve, revisão final e transação pública.

Consequencia: `chooseEditorialNextAction` passou a incluir `release_rehearsal_final_draft_blocked` antes de CTA público e a retornar `release_rehearsal_next_action_prepare_release_evidence_in_batch`. O próximo lote calculado continua consumidor financeiro, mas o objetivo é preparar evidência de release sem publicar, não trocar CTA para público.

Autocrítica: a mudança é segura porque só corrige a priorização do plano e mantém `publication_allowed=0`, `release_ready=0` e diff público vazio. É otimização real porque evita um próximo ciclo na direção errada. A validação é real porque testes de contrato e `cmd/check all` passaram com o novo next action; risco remanescente é desenhar release evidence amplo demais, então o próximo ciclo deve ser transacional e bloqueado.

## 2026-06-12 - Evidência de release bloqueada deve mostrar prova e risco

Decisao: `release-rehearsal-blocked-evidence` passa a ser o diagnóstico operacional da etapa de release evidence. O check usa o próximo batch calculado pelo plano editorial, amostra candidatos em cópia isolada de ensaio, calcula HTML, sitemap, hashes e smoke HTTP/Googlebot sem escrever em `public/`, `content/pages.json`, `published_manifest` ou `.release-staging` real. A mesma saída mostra repetição estrutural de `source_use`, `document_guidance` e `digital_triage`.

Motivo: o projeto já tinha transação pública e ensaio isolado, mas faltava uma camada agregada que provasse o caminho de release bloqueado no lote atual sem induzir aprovação pública. A auditoria do lote consumidor mostrou que um ensaio verde poderia virar falso conforto se não carregasse o risco anti-template: há 370 registros bloqueados e coerentes, mas 369 linhas repetem `source_use`, 103 são afetadas por repetição de documentos e 85 por repetição de triagem.

Consequencia: `releaserehearsal` ganhou `AssessBlockedReleaseEvidenceForNextBatch`, com 5 amostras determinísticas em cópia isolada, contagem de originais bloqueados, hashes de artefatos, smoke HTTP/Googlebot isolado e contadores anti-template. `internal/checks` registrou `release-rehearsal-blocked-evidence`, e há ferramenta `./tools/check-release-rehearsal-blocked-evidence`. O check passa com `approval=false`, `publication=false`, `publication_allowed=0`, `release_ready=0`, `real_staging=false`, `isolated_html=5`, `isolated_sitemaps=5` e `googlebot_smoke=5`.

Autocrítica: a mudança é segura porque só escreve em cópia isolada de ensaio e falha se `.release-staging` real aparecer; não altera dados permanentes de publicação. É otimização real porque converte a próxima ação em prova executável e já calcula o próximo risco editorial. A validação é real nos dados atuais, mas não libera publicação: o próximo ciclo precisa reduzir repetição estrutural do consumidor financeiro e reforçar anti-template antes de promover qualquer página.

## 2026-06-12 - Anti-template consumidor mede campo completo, não só primeira frase

Decisao: o contrato de final drafts consumidores passa a medir repetição de campo completo em `source_use`, `document_guidance` e `digital_triage`, além das variantes de primeira frase e CTA. O finalizador consumidor agora separa vocabulário de fonte, documento e triagem, usa fonte oficial como proveniência específica, acrescenta pergunta documental no guia e foco remoto distinto na triagem.

Motivo: o check de release evidence mostrou que testes verdes por primeira frase não detectavam repetição estrutural suficiente para escala. Ao fortalecer o teste, o RED expôs `source_use` repetido em 369 registros e depois falhas de repetição interna por reuso das mesmas expressões entre fonte, documento e triagem. A correção precisava melhorar o gerador e recalcular dados, não afrouxar o gate.

Consequencia: `batchcandidatepipeline` ganhou finalização consumidora mais específica e invalidou padrões intermediários de rascunho final. `batch_final_authorial_drafts.jsonl` foi regenerado para o consumidor, os resolvedores de conteúdo, CTA/manifesto e manifesto SEO foram reaplicados em todos os lotes elegíveis, e `batch_paid_intent_gates` foi recalculado. O check `release-rehearsal-blocked-evidence` agora mostra `duplicate_document_values=0`, `max_document_repeat=1`, `max_source_use_repeat=15` e `max_triage_repeat=15`, ainda com `publication_allowed=0`, `release_ready=0` e `real_staging=false`.

Autocrítica: a mudança é segura porque só mexe em dados bloqueados/noindex e preserva diff público vazio. É otimização real porque transformou uma métrica fraca em RED/GREEN de campo completo e reduziu repetição dominante antes de release real. A validação é real nos dados versionados, mas ainda há repetição residual de fonte e triagem por subtema/faceta; o próximo ciclo pode reduzir esses máximos ou aplicar o mesmo diagnóstico a outros batches antes de qualquer promoção pública.

## 2026-06-12 - Anti-template consumidor usa subfacetas jurídicas, não contador artificial

Decisao: o finalizador consumidor financeiro deve usar subfacetas jurídicas intermediárias em `source_use` e `digital_triage`, como custo de inércia, evidência de boa-fé, fonte primária, impacto familiar, negociação prévia, parte responsável, prova de negativa, prova digital, prova técnica, prova patrimonial, risco econômico, rota administrativa e vulnerabilidade. O contrato de campo completo foi endurecido para limitar repetição máxima a `consumidorCount/40`.

Motivo: após o ciclo anterior, a repetição residual vinha de 14 variantes por matriz e recorte porque o gerador ignorava essas subfacetas. A primeira tentativa reduziu valores duplicados, mas ainda deixou `max_source_use_repeat=14` e criou repetição interna em expressões como `e documento novo` e `e resposta administrativa`. A causa raiz era vocabulário insuficiente no gerador, não um problema de teste.

Consequencia: `batchcandidatepipeline` passou a emitir `Lente probatória`, `Ângulo de demanda`, `Etapa operacional` e `Sinal de triagem` com vocabulários separados. `batch_final_authorial_drafts.jsonl` e `batch_paid_intent_gates.jsonl` foram recalculados; os resolvedores de conteúdo, CTA/manifesto e manifesto SEO foram reaplicados nos seis batches, preservando os 74 previdenciários source-blocked. O relatório atual de release evidence mostra `duplicate_source_use_values=0`, `duplicate_source_use_affected=0`, `max_source_use_repeat=1`, `duplicate_document_values=0`, `max_document_repeat=1`, `duplicate_triage_values=0`, `duplicate_triage_affected=0` e `max_triage_repeat=1`, com `publication_allowed=0`, `release_ready=0` e `real_staging=false`.

Autocrítica: a mudança é segura porque só recalcula dados bloqueados e o diff público crítico permanece vazio. É otimização real porque remove a repetição exata residual do próximo lote de release evidence sem usar slug técnico, contador ou texto artificial. A validação é real para repetição exata, qualidade interna, paid-intent e release bloqueado; ainda não prova similaridade semântica profunda para todos os batches. Mesmo que esse diagnóstico seja generalizado, isso não encerra o `/goal`: ainda faltam pesquisa e geração de novos temas de alta intenção jurídica digital, páginas públicas aprovadas, HTML leve real, sitemap/canonical/robots públicos, smoke de bots, fontes oficiais por tema e escala mínima de 10 mil páginas únicas. O próximo ciclo deve tratar anti-template como gate local dentro de uma esteira maior de conteúdo, publicação, indexação e expansão.

## 2026-06-12 - Pesquisa de demanda exige coleta automatizada responsavel

Decisao: a expansao editorial deve operar coleta externa metadata-only por APIs publicas, conectores proprios, autosuggest permitido, busca organica, Bing, Google, sinais sociais publicos permitidos, scraping responsavel ou fonte equivalente para descobrir palavras-chave, long tails, perguntas, metadados, URLs oficiais e linguagem real de usuarios. Esses dados devem ser gravados em camada separada de pesquisa/auditoria, com origem, data, metodo, politica de uso, hash quando cabivel, status bloqueado e check executavel. A proibicao continua sobre clonar, espelhar, copiar ou republicar conteudo de fonte oficial ou de terceiros como texto autoral.

Motivo: 21 termos de pesquisa e 2220 candidatos bloqueados nao chegam perto da meta publica minima; depender apenas de Google Trends, memoria do modelo ou pesquisa manual estreita limita a fabrica e cria risco de escolher temas sem demanda real. Ao mesmo tempo, sinais sociais e consultas publicas servem para priorizacao e linguagem, nao para afirmar fato juridico sem fonte oficial.

Consequencia: contratos passam a exigir que Codex crie ferramenta, schema, CLI, auditoria e validacao quando faltar infraestrutura para captar demanda real. Google, Search Central e OpenAI continuam fontes primarias nas suas areas; direito brasileiro continua exigindo fonte oficial brasileira. Dados coletados por scraping entram como insumo bloqueado de pesquisa, nunca como corpo de pagina publica.

Autocrítica: a regra e segura porque separa descoberta de demanda de publicacao e reforca fonte oficial para conteudo juridico. E otimizacao real porque tira a expansao do improviso e cria caminho de engenharia para termos buscados/virais com potencial de contratacao digital. A validacao ainda precisa virar ferramenta concreta de coleta e checks de `data/research/`; sem isso, a regra fica documental e nao prova volume, qualidade ou legalidade operacional.

## 2026-06-12 - Release evidence bloqueada deve medir todos os batches

Decisao: `release-rehearsal-blocked-evidence-all-batches` passa a medir todos os batches com final draft bloqueado. O check usa uma cópia isolada de execução por batch para render/smoke, roda HTML/sitemap/smoke HTTP/Googlebot sem escrever em `public/`, `content/pages.json` ou `published_manifest`, reconhece a lane previdenciaria informativa bloqueada e reporta o pior batch por repeticao de `source_use`, `document_guidance` e `digital_triage`. Os dados reais medidos continuam permanentes no repo; somente os artefatos de render/smoke criados a partir da cópia são descartáveis.

Motivo: depois do refinamento consumidor, o check por proximo batch dava verde local e podia ocultar risco nos outros 1776 final drafts. Auditorias read-only confirmaram que ainda nao ha pagina juridica publicada, que o sitemap publico so contem a home e que a expansao atual 6x5x74 e regular demais para ser promovida sem diagnostico multi-batch.

Consequencia: o novo check reporta `candidate_count=2146`, `batch_count=6`, `samples=6`, `isolated_html=6`, `isolated_sitemaps=6`, `googlebot_smoke=6`, `publication_allowed=0`, `release_ready=0`, `real_staging=false` e aponta `batch-familia-digital` como pior alvo atual (`worst_source_repeat=370`, `worst_document_repeat=38`, `worst_triage_repeat=60`). `cmd/check all` passa a incluir esse diagnostico.

Autocrítica: a mudanca e segura porque so usa cópia isolada para render/smoke e mantem publicacao zerada; os JSONL reais continuam versionados e permanentes. E otimizacao real porque impede falso conforto do consumidor verde e calcula o proximo alvo editorial antes de qualquer promocao. A validacao e real para repeticao exata e smoke isolado por batch, mas ainda nao mede similaridade semantica profunda nem cria pagina publica; o proximo ciclo deve reduzir familia e construir coleta de demanda de alta intencao em camada propria.
## 2026-06-12 - Resolucao prioritaria consome auditoria URL-level sem liberar release

Decisao: `priority_source_specificity_resolutions` passa a consumir, de forma conservadora, candidatos especificos vindos de `priority_source_url_audits`. A resolucao saiu de 8 fontes travadas e 7 bloqueadas para 12 fontes travadas e 3 bloqueadas, mantendo todos os registros `noindex`, `reference_only_no_scraping_no_ingestion`, sem render, sitemap, publicacao ou `public_path`.

Motivo: a auditoria URL-level do ciclo anterior preservou pesquisa oficial, mas ainda nao movia o gate seguinte. Repetir a pesquisa ou deixar o recálculo para depois seria passividade. Ao mesmo tempo, aceitar todo candidato por estar em dominio oficial seria mascaramento de fonte. A implementacao aceita apenas avaliacoes explicitamente especificas e deixa candidatos contextuais/pendentes bloqueados.

Consequencia: reembolso ANS, golpe Pix no BCB, inventario extrajudicial no CNJ e aposentadoria especial no INSS passaram a referencia bloqueada. Emprestimo consignado nao contratado, nome negativado indevidamente e desconto indevido INSS continuam bloqueados por exigirem fonte oficial mais exata ou desambiguacao. `priority-source-specificity` reporta `locked=12 blocked=3 publication_allowed=0`.

Autocrítica: a melhoria e segura porque reduz blockers sem alterar `published_manifest`, `content/pages.json` ou `public/`, e porque os candidatos fracos continuam bloqueados. E otimizacao real porque transforma auditoria em decisao do gate seguinte. A validacao prova consumo conservador por teste e dados reais, mas ainda ha falso positivo plausivel em URL oficial SPA ou pagina tematica ampla; a proxima evidencia deve pesquisar os 3 blockers restantes e recalcular revisao/SEO/paid-intent antes de qualquer pagina publica.

## 2026-06-13 - Auditoria URL-level prioritaria destrava pesquisa sem publicar

Decisao: blockers de `priority_source_specificity_resolutions` passam a ter camada propria em `data/source-audit/priority_source_urls.jsonl`. A camada registra uma auditoria por resolucao bloqueada, preserva linhagem do rascunho prioritario, guarda hash da URL, fonte rejeitada anterior, candidatos oficiais pesquisados, metodo de evidencia e proxima acao. Ela usa politica `metadata_only_reference_no_scraping_no_content_copy` e mantem render, sitemap, publicacao e `public_path` fechados.

Motivo: o ciclo anterior separou 8 fontes travadas de 7 fontes amplas/contextuais, mas ainda faltava preservar a pesquisa oficial que pode resolver esses blockers. Registrar apenas um plano no checkpoint faria o proximo agente repetir pesquisa ou aceitar fonte ampla por pressa. A camada nova transforma pesquisa oficial em dado permanente, auditavel e bloqueado.

Consequencia: `priority-source-url-audits` reporta 7 auditorias, 6 com candidatos oficiais pesquisados e 1 ainda pendente de fonte especifica. O proximo passo correto e recalcular `priority_source_specificity_resolutions` com esses candidatos e manter revisao juridico-editorial, paid-intent, SEO, anti-template e release gate bloqueados. Nenhum HTML publico, sitemap, `published_manifest` ou `content/pages.json` muda por causa dessa camada.

Autocrítica: a melhoria e segura porque nao guarda corpo de fonte oficial, nao escreve texto editorial e nao publica. E otimizacao real porque reduz retrabalho e diferencia pesquisa confirmada de blocker ainda aberto. A validacao e real para linhagem, flags publicas e ausencia de texto bruto, mas ainda pode haver falso positivo de especificidade em URL SPA, lei ampla ou pagina contextual; a evidencia adicional necessaria e recalcular a resolucao e revisar manualmente o recorte juridico antes de qualquer release.

## 2026-06-13 - Recorte autoral prioritario deve alinhar fonte antes de destravar especificidade

Decisao: os tres rascunhos prioritarios que estavam bloqueados por `prazo-sete-dias` e fonte insuficiente passaram a usar recorte autoral especifico em `priority_authorial_drafts`: consignado nao contratado agora fala em consulta, bloqueio preventivo e reclamacao por canais oficiais; negativacao indevida fala em correcao de cadastro de consumo conforme fonte legislativa oficial; desconto indevido no INSS fala em contestacao conforme prazo oficial vigente. A validacao saiu do teste isolado e entrou em `priorityauthorialdrafts.ValidateRecord`, para reprovar tambem JSONL persistido que volte a sustentar prazo sem lastro.

Motivo: manter `unique_intent_id` historico com `prazo-sete-dias` nao autoriza escrever a frase como fato juridico. A pesquisa oficial do ciclo anterior encontrou fontes uteis, mas tambem mostrou que o prazo literal nao era sustentado nesses tres recortes. A solucao correta era corrigir o texto autoral e os documentos esperados na origem, nao editar JSONL manualmente nem liberar fonte por dominio oficial.

Consequencia: `priority-source-specificity` passou de `locked=12 blocked=3` para `locked=15 blocked=0`, sempre com `publication_allowed=0`, `render_allowed=false`, `sitemap_allowed=false` e `public_path=""`. A auditoria URL-level preserva 7 registros historicos metadata-only, atualiza linhagem quando o termo autoral muda e aceita novos assessments apenas quando o rascunho persistido removeu a afirmacao sem lastro ou passou a usar prazo oficial atual.

Autocrítica: a melhoria e segura porque elimina um falso conforto juridico sem publicar nada e sem apagar metadados brutos de busca. E otimizacao real porque remove tres blockers de fonte ao mesmo tempo em que fortalece o teste contra rascunho antigo persistido. A validacao e real para os dados atuais, mas ainda pode haver falso positivo se uma noticia oficial do INSS for tratada como referencia estavel sem revisao juridico-editorial posterior. O proximo passo tecnico deve recalcular paid-intent, SEO/search appearance, anti-template e revisao dos 15 rascunhos prioritarios; passar source-specificity ainda nao cria pagina publica, CTA publico, sitemap ou `published_manifest`.

## 2026-06-13 - Revisao juridico-editorial prioritaria vira camada bloqueada

Decisao: criar `priority_legal_editorial_reviews` como camada permanente bloqueada entre `priority_publication_readiness` e qualquer ensaio de release. A camada consome readiness, rascunho autoral, resolucao de fonte e identidade versionada de `content/site.json`; registra notas de revisao, required_fixes, CTA interno, origem rastreavel, status de paid-intent e flags publicas falsas. BPC/LOAS permanece com `priority_legal_editorial_review_blocked_paid_intent`, sem forcar aprovacao.

Motivo: `priority_publication_readiness` ja mostrava `paid_passed=14`, `paid_blocked=1` e `legal_review_required=15`, mas nao havia evidencia versionada de revisao juridico-editorial/OAB para essa vertical. Deixar isso no checkpoint seria passividade; liberar pagina sem essa camada seria quebrar contrato. A criacao do gate tambem expôs que o gerador ainda convertia o identificador bruto `prazo-sete-dias` em texto autoral para registros nao especializados; a correcao para frente removeu essa afirmacao e endureceu a validacao contra regressao.

Consequencia: `priority-legal-reviews` entra em `cmd/check all`, com `reviews=15`, `paid_intent_blocked=1`, `identity_from_config=15` e `publication_allowed=0`. `content/storage_contract.json` passa a exigir a camada. `priority_authorial_drafts`, `priority_source_specificity_resolutions`, `priority_publication_readiness` e `priority_legal_editorial_reviews` foram regenerados sem tocar `published_manifest`, `content/pages.json` ou `public/`.

Autocrítica: a melhoria e segura porque todos os registros ficam `noindex`, sem render, sitemap, publicacao, aprovacao ou `public_path`, e porque a identidade OAB vem de config versionada em vez de hardcode. E otimizacao real porque transforma revisao pendente em gate executavel e pegou um falso conforto autoral residual. A validacao e real para dados persistidos e check global, mas ainda nao prova HTML publico leve, canonical/robots/sitemap real, smoke Googlebot de rota juridica aprovada ou escala ate 10 mil paginas; a proxima fatia deve construir release evidence/HTML leve bloqueado para essa vertical ou ampliar captura externa metadata-only de alta intencao, escolhendo o maior avanço seguro.

## 2026-06-13 - Release evidence prioritaria prova HTML leve sem publicar

Decisao: criar `priority_release_evidence` como camada permanente bloqueada depois de `priority_legal_editorial_reviews`. A camada registra uma evidencia por revisao prioritaria, renderiza HTML apenas em memoria, calcula SHA-256 e bytes, valida canonical oficial, robots `noindex,follow`, ausencia de runtime cliente, smoke Googlebot bloqueado e flags publicas falsas. BPC/LOAS permanece com status bloqueado por paid-intent; as 14 evidencias elegiveis passam smoke tecnico sem virar rota publica.

Motivo: a revisao juridico-editorial prioritaria ainda deixava o proximo passo em required_fixes de HTML leve, canonical, robots, sitemap e smoke Googlebot. Registrar isso apenas como plano seria passividade; escrever em `public/` ou sitemap real seria publicacao indevida. A solucao correta foi criar evidencia calculavel e versionada, com hash recalculavel a partir dos rascunhos e reviews, sem materializar HTML publico.

Consequencia: `priority-release-evidence` entra em `cmd/check all`, `content/storage_contract.json` passa a exigir a camada, e `data/editorial/priority_release_evidence.jsonl` guarda 15 registros bloqueados com `html_lightweight=15`, `googlebot_smoke=14`, `paid_intent_blocked=1` e `publication_allowed=0`. O ciclo tambem corrigiu um falso negativo idempotente em `reviewcontentfixresolver`: manifesto de saude suplementar ja revisado, bloqueado, `content_draft_required=false` e sem flags publicas agora e aceito como estado idempotente em vez de erro de SEO pending.

Autocrítica: a melhoria e segura porque nao escreve em `public/`, `content/pages.json`, `published_manifest` ou sitemap real, e porque a evidencia guarda hash e flags bloqueadas no repo. E otimizacao real porque antecipa falha de HTML/Googlebot antes de release transacional e remove um falso negativo de teste sem abrir publicacao. A validacao e real para hash, canonical, robots, bytes, runtime cliente e estado idempotente de saude suplementar; falso positivo ainda e plausivel se o render em memoria tiver corpo juridico pobre apesar de H1/canonical/robots corretos. A proxima acao deve aumentar prova vertical com release transacional bloqueado/HTTP real quando os gates publicos forem suficientes ou expandir demanda externa e novos temas de alta intencao para aproximar a meta 10k.

## 2026-06-13 - Ensaio HTTP transacional prioritario continua bloqueado

Decisao: criar `priority_release_transaction_evidence` como camada permanente bloqueada depois de `priority_release_evidence`. A camada serve rota candidata, robots e sitemap apenas por handler isolado em memoria, registra hashes de HTML/robots/sitemap, status HTTP, content-type, canonical, robots `noindex,follow`, ausencia de runtime cliente e prova de que a URL nao existe em `public/`, `content/pages.json`, `published_manifest` ou sitemap real.

Motivo: chamar o release publico como se os registros estivessem `index`/aprovados seria falso positivo e quebraria o contrato. A vertical precisa provar HTTP e sitemap de ensaio sem promover flags, sem `.release-staging` real e sem transformar sitemap isolado em sitemap publico.

Consequencia: `priority-release-transaction` entra em `cmd/check all`, com `transactions=15`, `http_smoke=15`, `paid_intent_blocked=1` e `publication_allowed=0`. A camada reforca que HTTP 200 de ensaio bloqueado nao e publicacao, mas reduz risco tecnico de canonical/robots/content-type antes da proxima fatia.

Autocrítica: a melhoria e segura porque nao altera artefatos publicos e valida explicitamente ausencia da URL real. E otimizacao real porque adiciona prova HTTP isolada depois do hash de HTML, sem simular aprovacao indevida. A validacao ainda pode ter falso positivo se o corpo renderizado for juridicamente pobre; o proximo passo deve medir qualidade semantica ou expandir conteudo/demanda, nao confundir smoke tecnico com aceite publico.

## 2026-06-13 - Expansao externa prioritaria preserva blockers especificos

Decisao: ampliar a coleta externa metadata-only e propagar a vertical prioritaria de 15 para 20 registros bloqueados, sem reduzir exigencia de fonte, paid-intent, SEO, anti-template, HTML leve, release evidence ou HTTP isolado. O contrato passa a tratar fonte bloqueada como blocker explicito em readiness, review, release evidence e transaction, em vez de falha opaca ou status de paid-intent indevido.

Motivo: a coleta anterior de 68 observacoes e 28 prioridades ainda era pequena diante da meta minima. Ao subir para 207 observacoes, 34 prioridades e 20 candidatos, apareceram dois riscos reais: abertura autoral repetida nos primeiros tokens e `revisao-aposentadoria` sem fonte oficial especifica alem da home do INSS. A solucao correta era ajustar gerador e gates para preservar o blocker real, nao mascarar a fonte ampla nem voltar ao volume antigo.

Consequencia: `demand-signal-observations` reporta `observations=207`, `opportunities=24`, `seeds=21`; `demand-opportunity-priority` reporta `records=34`, `prioritized_for_blocked_review=20`, `needs_more_external_observation=14`; a vertical prioritaria possui 20 briefs, 20 rascunhos, 20 reviews, 20 release evidences e 20 transacoes bloqueadas. `priority-source-specificity` reporta `locked=19 blocked=1`; `priority-publication-readiness` reporta `paid_passed=19`, `paid_blocked=1`, `search_ready=16`, `anti_template_ready=16`; `priority-release-evidence` reporta `html_lightweight=20`, `googlebot_smoke=18`; `priority-release-transaction` reporta `http_smoke=20`; `publication_allowed=0`.

Autocrítica: a melhoria e segura porque preserva publicação zero e separa blocker de fonte de blocker comercial. E otimizacao real porque aumenta cobertura externa, melhora abertura autoral e impede falso positivo de fonte ampla. A validacao e real para dados persistidos, mas ainda ha falso positivo plausivel em similaridade semantica e falso negativo em fonte oficial especifica se a pesquisa URL-level estiver estreita. O proximo avanço deve resolver a fonte de revisao de aposentadoria ou atacar os 4 blockers de SEO/anti-template enquanto continua a expansao de demanda externa.

## 2026-06-13 - Revisao de aposentadoria usa servico oficial sem publicar

Decisao: `revisao-aposentadoria::negativa-formal::prazo-sete-dias` deixa de depender da home do INSS e passa a usar a pagina oficial gov.br `https://www.gov.br/pt-br/servicos/solicitar-revisao-de-beneficio` como fonte especifica metadata-only. A home do INSS permanece registrada como fonte rejeitada ampla. Nenhum texto oficial foi copiado para o repo.

Motivo: o ciclo anterior preservou corretamente o blocker porque a home do INSS era ampla. A pesquisa metadata-only atual confirmou que a pagina de servico oficial responde HTTP 200 e cobre o procedimento de revisao de beneficio, que e mais especifico para o recorte do rascunho. Manter o blocker depois disso viraria falso negativo; aceitar a home ampla teria sido falso positivo.

Consequencia: `priority-source-url-audits` reporta `audits=8 with_candidates=8`; `priority-source-specificity` reporta `locked=20 blocked=0`; `priority-publication-readiness` reporta `source_locked=20 paid_passed=19 paid_blocked=1 search_ready=16 anti_template_ready=16`; `priority-release-evidence` reporta `googlebot_smoke=19`; `priority-release-transaction` continua `http_smoke=20`; `publication_allowed=0`.

Autocrítica: a melhoria e segura porque so adiciona metadado de URL oficial, preserva hashes e politicas sem scraping/copia e mantem publicação zero. E otimizacao real porque remove um blocker de fonte sem mascarar BPC/LOAS ou os 4 blockers de SEO/anti-template. A validacao e real para HTTP metadata, fonte especifica e cadeia derivada, mas ainda ha falso positivo plausivel se o conteudo autoral de revisao de aposentadoria nao for lido juridicamente antes de publicacao. O proximo avanço deve fortalecer SEO/anti-template ou seleção/promotabilidade bloqueada, mantendo revisão final antes de qualquer indexação.

## 2026-06-13 - SEO e anti-template prioritarios ficam verdes sem publicar

Decisao: refinar o gerador autoral prioritario para diferenciar title, metadescricao, documentos e triagem por cenário/contexto, em vez de aceitar duplicidade entre quatro recortes de acidente de trabalho. O refinamento permanece em camada bloqueada e nao abre render, sitemap, `published_manifest` ou pagina publica.

Motivo: depois da fonte 20/0, os 4 blockers restantes eram duplicidade de title/meta e repeticao de `document_guidance`/`digital_triage`. A primeira tentativa corrigiu anti-template, mas produziu metadescricoes longas e derrubou `search_ready` para 2; a causa raiz era metadescricao verbosa, nao um erro do check. A correção final usa foco curto por cenário/contexto.

Consequencia: `priority-publication-readiness` reporta `source_locked=20`, `paid_passed=19`, `paid_blocked=1`, `search_ready=20`, `anti_template_ready=20`, `legal_review_required=20` e `publication_allowed=0`. `priority-release-evidence` permanece `html_lightweight=20`, `googlebot_smoke=19`, `paid_intent_blocked=1`; `priority-release-transaction` permanece `http_smoke=20`.

Autocrítica: a melhoria e segura porque so recalcula rascunhos e evidencias bloqueadas, com diff publico vazio. E otimizacao real porque remove duplicidade estrutural sem baixar orçamento de title/meta nem esconder BPC/LOAS. A validacao e real para contadores, orçamento SERP, anti-template exato e cadeia derivada; ainda ha falso positivo plausivel em similaridade semantica profunda e revisao juridica final, entao a proxima etapa deve tratar paid-intent/rota informativa ou seleção/promotabilidade bloqueada, nao publicar direto.

## 2026-06-13 - Seleção bloqueada de promotabilidade prioritária

Decisao: criar `priority_promotability_selection` como camada permanente bloqueada derivada de `priority_release_transaction_evidence`, selecionando 19 candidatos pre-release e excluindo BPC/LOAS por paid-intent/assistencia publica sem tentar transformar esse tema em sinal comercial.

Motivo: depois de fonte 20/0, SEO 20/20 e HTTP smoke 20, o maior avanço seguro era separar o que pode seguir para revisão final/release gate bloqueado do que deve continuar excluido. Forçar BPC/LOAS como paid-intent comercial mascararia a proteção existente contra gratuidade/assistência pública; a engenharia correta é registrar a exclusão e criar lane informativa com fonte, noindex, sem CTA público e próximo check.

Consequencia: `priority-promotability` entra em `cmd/check all`, com `selections=20`, `selected_blocked=19`, `paid_intent_excluded=1` e `publication_allowed=0`. A camada preserva `noindex`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""`, ausência em `public/`, `content/pages.json`, `published_manifest` e sitemap real.

Autocrítica: a melhoria é segura porque não publica, não muda flags públicas e não rebaixa BPC/LOAS; é otimização real porque transforma HTTP smoke bloqueado em fila auditável para o próximo release gate, em vez de deixar a cadeia parar em diagnóstico. A validação é real para contadores, ausência pública e classificação de exclusão, mas falso positivo ainda é plausível se os 19 forem promovidos sem leitura jurídica final de amostras. O próximo avanço deve criar revisão final/release gate bloqueado dos 19 ou ampliar demanda externa, mantendo conteúdo único e sem mascarar paid-intent.

## 2026-06-13 - Gate final prioritário bloqueado exige prova antes de promoção

Decisao: criar `priority_release_gate` como camada permanente bloqueada derivada de `priority_promotability_selection`, consumindo somente os 19 registros `priority_promotability_selected_blocked_pre_release`. A camada exige revisao juridico-editorial final, plano de `published_manifest`, canonical/robots/sitemap indexaveis, smoke publico Googlebot, leitura amostral e prova de escrita publica zero antes de qualquer promocao.

Motivo: `selected_blocked` poderia ser mal interpretado como aprovacao publica se a cadeia parasse em promotabilidade. A engenharia correta e transformar a selecao em gate final auditavel, preservando todos os bloqueios publicos e impedindo que HTML leve/HTTP 200 de ensaio substituam revisao juridica, manifesto, sitemap real e smoke publico. BPC/LOAS permanece fora da promocao comercial; a solucao correta para esse tema e lane informativa bloqueada ou blocker P0 acionavel, nao mascaramento.

Consequencia: `priority-release-gate` entra em `cmd/check all`, com `gates=19`, `final_review_required=19` e `publication_allowed=0`. `data/editorial/priority_release_gate.jsonl` preserva linhagem de fonte, rascunho, review, release evidence, transaction e promotability, mantem `approval=false`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""` e flags de escrita publica falsas. `content/scale_plan.json` tambem passa a declarar publicacao como regra bloqueada ate gate completo, seguida de publicacao aprovada neste `/goal`, em vez de zero fixo por fase.

Autocrítica: o que podemos melhorar, e por que? A proxima melhoria deve materializar revisao final semantica, plano transacional de manifesto ou lane informativa BPC/LOAS, porque gate final bloqueado ainda nao cria pagina publica. E seguro? Sim: a camada deriva somente dos 19 selecionados, nao toca `public/`, `content/pages.json`, `published_manifest` ou sitemap real, e preserva BPC/LOAS excluido. E otimizacao real? Sim: substitui risco de falsa promocao por contrato executavel no check global, sem aumentar CPU do runtime publico. E teste real sem falso positivo ou negativo? E real para contadores, linhagem, flags publicas e requisitos finais; ainda pode haver falso positivo sem leitura juridica profunda do corpo e falso negativo se um candidato tecnicamente pronto ficar parado sem plano de manifesto. O proximo ciclo deve continuar a fatia vertical ou ampliar demanda externa com ferramenta/check, nao parar no checkpoint.

## 2026-06-13 - Pedido explicito vira execucao obrigatoria do goal atual

Decisao: reforcar `AGENTS.md`, `GOAL.md`, README, `docs/LAB_VALIDATION.md` e `docs/ROADMAP_P0_P5.md` para declarar que pedido explicito do usuario e requisito operacional do `/goal` ativo. Linguagem de conveniência nao pode transformar qualidade juridica, alta escala, alta intencao digital, fonte oficial, conteudo autoral, testes robustos, HTML leve, Googlebot, sitemap/canonical/robots, CTA etico ou publicacao segura em sugestao. Caminho tecnico seguro obriga execução; ferramenta, dado, fonte, coletor, API, schema, teste ou validador ausente obriga construir a peca verificavel.

Motivo: os contratos ja proibiam passividade, mas o pedido atual exigiu remover qualquer margem de leitura em que "quando util" ou "proximo ciclo" virasse adiamento. A regra nova tambem impede que o proximo Codex trate documentacao, checkpoint, achado de subagente ou pergunta de engenharia como recomendacao consultiva.

Consequencia: `internal/contract/continuity_test.go` ganhou `TestContractsTreatUserRequestedWorkAsCurrentGoalExecution`, cobrindo os documentos centrais. A decisao nao publica paginas, nao altera `published_manifest`, nao toca sitemap real e nao substitui a vertical tecnica seguinte; ela torna a obrigacao testavel antes do commit.

Autocrítica: a melhoria e segura porque altera contrato e teste, sem abrir flags publicas. E otimizacao real para continuidade porque reduz perda de contexto e impede falso conforto documental antes de fonte/conteudo/publicacao. A validacao e real para o texto contratual, mas nao prova ainda os 9 blockers de fonte, os 4 paid-intent bloqueados, a expansao 10k+ nem paginas indexaveis; a proxima evidencia deve ser codigo/dado em camada vertical, com teste vermelho e recálculo downstream.

## 2026-06-14 - Cadeia geral pos-rascunho cobre 27 rascunhos sem publicar

Decisao: a operacao geral de criacao de conteudo nao pode parar em `authorial_drafts`. `./tools/refresh-authorial-draft-pipeline` passa a ser o motor interno para propagar rascunhos autorais para `source_blockers`, `source_resolutions`, `prepublication_gates` e `legal_reviews` em cobertura 1:1, mantendo todos os registros bloqueados, `noindex`, sem render, sitemap, `public_path` ou publicacao.

Motivo: os checks legados passavam com apenas 1 resolucao de fonte, 1 gate de prepublicacao e 1 revisao juridica para 27 rascunhos. Isso era falso verde de cobertura parcial. A API interna e adequada como motor de escala, persistencia e validacao, mas nao e oraculo unico: os perfis por termo combinam fontes oficiais especificas, matrizes batch/priority ja versionadas, pesquisa oficial, sinais publicos e revisao juridica.

Consequencia: `authorial-draft-pipeline` foi adicionado a `cmd/check`, e `internal/contract/authorial_pipeline_coverage_test.go` reprova lacuna entre rascunhos e cadeia pos-rascunho. `source_resolutions` deixou de exigir `coverage_rule` de ANS para todos os dominios e agora aceita fonte primaria ou fonte oficial especifica adequada ao tema. O estado atual fica `authorial_drafts=27`, `source_blockers=27`, `source_resolutions=27`, `prepublication_gates=27`, `legal_reviews=27`, `published_manifest=0`.

Autocritica: a mudanca e segura porque so mexe em dados bloqueados e validadores, com prova de diff publico vazio. E otimizacao real porque elimina falso verde e torna a proxima macrocamada executavel. Ainda nao prova pagina publica premium nem 10 mil URLs; faltam paid-intent/CTA final ou lane informativa, anti-template em lote, HTML leve, smoke HTTP/Googlebot, manifesto e release gate completo antes de qualquer indexacao.

## 2026-06-13 - Contratos removem ambiguidade de execução do goal

Decisao: decisao permanente: nada no contrato deve tratar arquitetura como fim do goal. O `/goal` exige arquitetura, conteudo, alta intencao digital, demanda externa, fonte oficial, revisao juridica, HTML leve, Googlebot, sitemap/canonical/robots, CTA etico, testes robustos e publicacao segura como cadeia unica de execucao. Quando cabivel e criterio de classificacao tecnica, nao autorizacao para omitir requisito pedido; o mesmo vale para condicoes de CTA, fonte, validacao, coleta, publicacao e performance.

Motivo: a revisao antes do commit mostrou que a regra ja estava forte, mas ainda precisava de uma guarda explicita contra leitura passiva de linguagem de conveniência. O proximo Codex deve entender que teste verde, checkpoint, documentacao ou promocao bloqueada nao encerram o trabalho nem reduzem a meta a arquitetura ou ao gargalo local.

Consequencia: `TestContractsRequirePreciseNonPassiveExecutionForAllGoalAxes` passa a exigir essa precisao em `AGENTS.md`, `GOAL.md`, README, laboratorio, roadmap e decisoes. A mudanca nao publica pagina, nao toca `public/`, `content/pages.json`, `published_manifest` nem sitemap real; ela transforma a exigencia em contrato testavel para que a proxima fatia P0 continue por execucao verificavel.

Autocrítica: a melhoria e segura porque altera apenas contrato e teste de continuidade. E otimizacao real para continuidade porque reduz ambiguidade operacional e evita que o proximo ciclo trate alta escala, conteudo, fonte, Googlebot ou CTA como temas opcionais. A validacao prova a presenca textual da regra, mas nao prova paginas publicas, 10k URLs, cobertura externa suficiente nem qualidade juridica final; a proxima evidencia deve ser vertical tecnica com dado real, fonte, gerador, check e cadeia bloqueada recalculada.

## 2026-06-13 - Amostra textual bloqueada nao pode virar sucesso vazio

Decisao: operar amostras textuais externas como exigência explícita de rodada, não como efeito colateral de coleta metadata-only. Quando a análise editorial depender de linguagem real, o coletor deve rodar com `--capture-content-samples --require-content-samples --min-content-samples N`; superfície que devolve só metadados pode preservar a camada metadata-only, mas `demand_content_samples` continua não satisfeita e a execução deve corrigir parser/filtro/superfície ou operar alternativa permitida.

Motivo: o estado atual tem camada de amostras separada com zero amostras aceitas. Esse zero é correto como armazenamento bloqueado, mas vira falso verde se relatório ou checkpoint chamar metadata-only de coleta textual concluída. A distinção protege o projeto contra página autoral construída por inferência fraca, contra cópia de trecho externo e contra expansão 10k+ baseada em superfície vazia.

Consequencia: `internal/demandobservations` agora emite diagnóstico específico para amostra ausente, amostra textual vazia/inválida, amostra sem alinhamento contextual e texto não compatível com PT-BR (`content_sample_text_not_ptbr`). `--require-content-samples` conta apenas amostras validadas, não apenas amostras capturadas; portanto texto em inglês ou em outro idioma não satisfaz `--min-content-samples` mesmo quando a superfície declara locale brasileiro. `docs/DATA_SOURCES.md`, `docs/LAB_VALIDATION.md` e `docs/ROADMAP_P0_P5.md` passam a exigir distinção operacional entre camada vazia, metadata-only aceito, amostra aceita e requisito textual não satisfeito. API metadata-only deve registrar tentativa e contadores, mas não cumpre `--require-content-samples`. Blocker P0 de amostra precisa citar superfície, política, flags, contagem de metadados, zero amostras válidas, causa e próxima correção executável.

Autocrítica: a mudança é segura porque altera coletor, validação e contrato apenas em camadas bloqueadas de pesquisa, sem tocar `public/`, `content/pages.json`, `published_manifest` ou sitemap real. É otimização real porque remove um falso positivo provável antes de novas coletas externas: metadado aceito ou texto em idioma errado deixa de parecer amostra editorial válida. A validação focada cobre fixtures de ausência, parse inválido, desalinhamento e inglês declarado como `pt-BR`; o risco residual é que a heurística inicial de idioma ainda é conservadora e deve evoluir com mais dados reais, sem reduzir a exigência de reescrita autoral, fonte oficial específica e revisão jurídico-editorial.

## 2026-06-13 - Pares semanticos so reduzem por reescrita autoral recalculada

Decisao: a correcao dos pares semanticos remanescentes em `priority_similarity_semantic_reviews` deve ser tratada como acao editorial bloqueada, nao como ajuste de limite. Um par so deixa de ser blocker quando houver reescrita autoral real do corpo ou dos elementos substantivos que causaram a proximidade, preservacao de fonte oficial e risco juridico, recálculo das camadas de similaridade/revisao afetadas e evidencia de que a distincao nasceu do conteudo. Baixar threshold, trocar palavras isoladas, remover amostra, renomear status ou reduzir a fila sem recálculo e mascaramento; isso nao resolve o gate.

Motivo: a reducao anterior de pares mostrou diferenciacao autoral parcial, mas nao autoriza tratar a fila atual como publicacao, nem como problema numerico a esconder. A proxima execucao deve ler os pares vivos, identificar se a colisao vem de problema humano, documentos, fonte, CTA, risco ou estrutura de texto, corrigir para frente nos rascunhos/revisoes apropriados e recalcular antes de mudar qualquer contador. Se algum par continuar materialmente semelhante depois da reescrita, ele permanece bloqueado ou exige amostragem semantica mais ampla, sem abrir sitemap, render, `public_path`, `content/pages.json`, `published_manifest` ou `public/`.

Consequencia: esta decisao nao declara nenhum par resolvido e nao altera contadores especificos. A documentacao operacional passa a exigir que a evidencia de resolucao cite os registros afetados, o tipo de reescrita autoral feita, as camadas recalculadas, o check usado e a prova de publicacao zero. Mesmo que o recálculo futuro elimine todos os pares remanescentes, a macrocamada seguinte continua sendo expansao externa confiavel com diversidade, conteudo autoral de alta intencao e publicacao segura com gate completo; resolver similaridade apenas abre essa frente, nao encerra o P0.

Autocrítica: a melhoria reduz risco de falso verde documental porque separa criterio editorial de contador e impede que threshold vire atalho. Ela ainda nao prova conteudo diferenciado, porque nenhum JSONL foi recalculado nesta decisao; a evidencia adicional necessaria e operar a reescrita nos pares vivos, rodar o check focado e inspecionar diffs de texto antes de qualquer promocao. O risco residual e um falso negativo se o comparador continuar sensivel a termos juridicos inevitaveis; nesse caso a resposta correta e diagnostico semantico explicavel com amostra ampliada, nao relaxamento silencioso do gate.

## 2026-06-13 - API de amostras textuais captura contexto estruturado sem publicar

Decisao: ampliar `collect-demand-observations` para capturar amostras textuais mais ricas quando a rodada exigir linguagem real, mantendo tudo em `data/research/demand_content_samples.jsonl`. O coletor passa a aceitar contexto estruturado em `articles`, `items`, `hits`, listagens sociais e objetos JSON genéricos com `title/headline` mais campos como `abstract`, `fullText`, `comments`, `answers`, `description`, `text`, `body`, `snippet` e equivalentes. A coleta textual continua separada da observação metadata-only e nunca alimenta ranking, rascunho, HTML, CTA, sitemap ou manifesto publicado.

Motivo: metadados, títulos e snippets estreitos não bastam quando a decisão editorial depende de vocabulário real, dúvida completa, contexto humano ou risco de duplicidade. O projeto precisa de insumo suficiente para o Codex reescrever com autoria própria, sem virar clone nem texto mecânico, e precisa de prova executável de que a amostra está alinhada ao serviço jurídico digital pesquisado.

Consequencia: `ContentSampleRecord` agora guarda tipo de conteúdo, modo de extração, orçamento de trecho, termos de alinhamento com a oportunidade, motivo editorial e `full_text_stored=false`. O CLI expõe `--max-content-samples-per-opportunity`, `--max-content-sample-runes` e `--max-response-bytes` para rodadas mais fortes e controladas. O parser normaliza HTML, deduplica por hash, rejeita idioma incompatível, exige reescrita autoral/revisão jurídico-editorial e mantém `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false` e `public_path=""`. Os wrappers `check-demand-content-samples` e `check-demand-surface-collection-attempts` também passam a usar `GOCACHE=/tmp/opt-wiki-go-cache`, corrigindo a ferramenta em vez de documentar falha de ambiente.

Autocrítica: O que podemos melhorar, e por que? A próxima melhoria deve operar uma superfície real permitida que entregue amostras válidas, porque o schema e os testes provam capacidade, mas o arquivo atual ainda tem 0 amostras aceitas. É seguro? Sim: a mudança só amplia a camada bloqueada, com hashes, limites, `full_text_stored=false`, flags públicas falsas e revisão obrigatória. É otimização real? Sim: aumenta o sinal editorial disponível sem aumentar CPU de produção nem permitir publicação automática. É teste real sem falso positivo ou negativo? Os testes cobrem parser genérico, campos estruturados, idioma, ausência/desalinhamento e CLI; ainda há risco de falso negativo em idioma ou alinhamento com dados reais, que deve ser corrigido com novas amostras e heurística explicável, não com relaxamento.

## 2026-06-13 - Revisao semantica prioritaria zera por reescrita autoral

Decisao: resolver os seis recortes vivos dos três pares semânticos remanescentes por reescrita autoral substantiva nos campos de documentos, fonte e risco, mantendo a cadeia bloqueada. O contrato de similaridade passa a aceitar `priority_similarity_semantic_reviews` vazio quando o relatório agregado recalculado não tiver par acima de 0.60; vazio por baixo risco calculado é diferente de vazio por ausência de dado ou relaxamento de teste.

Motivo: o gerador já havia reduzido a fila, mas ainda faltava distinção material em pares de acidente de trabalho e aposentadoria especial. A correção correta era melhorar o conteúdo autoral e recalcular downstream, não baixar threshold, remover amostra ou mascarar contador. Depois da regeneração, `priority_similarity_report` manteve 38 registros e maior score 0.5972, abaixo do limiar semântico.

Consequencia: foram regeneradas as camadas de `priority_authorial_drafts` até `priority_similarity_semantic_reviews`. O estado atual é 177 rascunhos prioritários bloqueados, 162 revisões finais bloqueadas, 37 relatórios de similaridade, 0 revisões semânticas, 8 lane informativa, `published_manifest=0`, `publication_allowed=0`, sem tocar `public/`, `content/pages.json` ou sitemap real. Se novo conteúdo autoral, CTA, title/meta, fonte ou revisão final mudar, as camadas derivadas devem ser recalculadas e qualquer par que volte ao limiar deve reaparecer como blocker.

Autocrítica: O que podemos melhorar, e por que? A próxima melhoria deve transformar essa abertura em expansão externa/conteúdo autoral de alta intenção ou publicação segura com gate completo, porque zerar pares semânticos não cria páginas públicas nem aproxima sozinho as 10 mil URLs. É seguro? Sim: a resolução é por texto autoral versionado e recálculo, com publicação zero e flags fechadas. É otimização real? Sim: reduz risco mensurável de near-duplicate sem enfraquecer o algoritmo. É teste real sem falso positivo ou negativo? Os testes focados exigem marcadores materiais por lado e os checks recalculam a cadeia; o risco residual é o Jaccard não capturar paráfrase semântica profunda, então amostragem futura deve crescer quando novos lotes aparecerem.

## 2026-06-13 - Diagnostico textual persistido prevalece sobre sucesso metadata-only

Decisao: quando uma rodada exigir amostra textual, a tentativa da superfície precisa registrar o requisito e a causa da falha mesmo que a mesma resposta tenha metadados parseáveis. Feed/RSS, agregador ou busca que entrega só título, fonte, link, snippet raso ou descrição que duplica o título permanece metadata-only; não entra em `demand_content_samples`, não satisfaz `--require-content-samples` e deve persistir `content_samples_required=true`, `valid_content_samples=0`, `required_surface_satisfied=false` e diagnóstico sanitizado como `content_sample_absent_for_metadata_success` ou equivalente.

Motivo: o ciclo real operou RSS/Google News e confirmou que o endpoint podia devolver itens úteis como metadados, mas sem corpo textual suficiente para orientar reescrita autoral. Aceitar título/fonte como amostra criaria falso positivo editorial, poluiria a camada aceita e poderia induzir clone, paráfrase linear ou expansão 10k+ baseada em contexto raso.

Consequencia: `internal/demandobservations` valida amostras antes da escrita, filtra amostras inválidas no merge, rejeita RSS title-only, registra `last_failure_detail` sanitizado e faz o merge de tentativas preferir diagnóstico textual exigido sobre sucesso metadata-only antigo. `data/research/demand_content_samples.jsonl` tem 2 registros aceitos e bloqueados no estado atual, enquanto `demand_surface_collection_attempts` guarda 13 tentativas em 7 superfícies, incluindo a tentativa RSS/Google News textual como falha bloqueada e a tentativa gov.br/ANS RSS/RDF como `surface_attempt_completed_with_textual_samples`, não como ranking, rascunho ou publicação.

Autocrítica: O que podemos melhorar, e por que? A próxima melhoria deve operar superfície permitida que entregue perguntas/corpos em PT-BR com contexto suficiente ou criar adaptador específico com política clara, porque a ferramenta agora falha corretamente mas ainda não gerou amostra aceita. É seguro? Sim: a correção remove amostras inválidas da camada aceita, mantém texto externo segregado e não toca `public/`, `content/pages.json`, `published_manifest` ou sitemap. É otimização real? Sim: reduz retrabalho e evita falso verde de RSS/metadata-only sem aumentar custo de produção. É teste real sem falso positivo ou negativo? Os testes cobrem merge, diagnóstico persistido, RSS com contexto suficiente e RSS title-only rejeitado; o risco residual é falso negativo em feed legítimo com descrição curta porém útil, que deve ser tratado por heurística explicável e amostra real, não por afrouxamento silencioso.

## 2026-06-13 - Documentacao textual elimina leitura passiva de amostra

Decisao: reforcar a documentacao operacional para que "amostra textual" seja requisito de rodada quando a decisao editorial depender de linguagem real, nao permissao opcional. A documentacao passa a separar quatro estados: camada `demand_content_samples` vazia porque texto nao foi exigido; metadata-only aceito e restrito a observacao/tentativa; amostra textual aceita e validada em PT-BR; ou requisito textual nao satisfeito com tentativa e diagnostico persistidos.

Motivo: frases como "pode capturar", "pode orientar" e "amostra pequena" ainda podiam ser lidas como autorizacao para chamar metadata-only de coleta textual parcial ou para aceitar camada vazia como sucesso. A proxima macrocamada precisa operar superficie textual/PT-BR com `--require-content-samples` quando texto for requisito; tentativa persistida nao e observacao aceita, e metadata-only aceito nao e amostra textual.

Consequencia: `docs/DATA_SOURCES.md`, `docs/LAB_VALIDATION.md` e `docs/ROADMAP_P0_P5.md` agora usam linguagem imperativa para requisito textual, deixam claro que RSS/feed/title-only deve registrar `valid_content_samples=0`, e impedem que `demand_content_samples` vazio seja citado como sucesso de rodada textual. A proxima execucao deve operar superficie permitida que entregue corpo/pergunta em PT-BR ou corrigir parser/filtro/adaptador/orcamento; se nenhuma alternativa responsavel produzir amostra valida, o blocker P0 precisa citar superficie, politica, flags, contadores metadata-only, zero amostras validas, causa e proximo comando tecnico.

Autocritica: a mudanca e segura porque altera apenas documentos operacionais, sem tocar dados reais, codigo, `public/`, `content/pages.json`, `published_manifest` ou sitemap. Ela reduz falso verde documental, mas ainda nao prova amostras PT-BR reais nem aumenta cobertura externa. A validacao proporcional deve ser textual e por diff; o risco residual e que algum comando ou check de codigo ainda permita relatorio ambiguo, entao o proximo passo executavel e operar `./tools/collect-demand-observations` com `--require-content-samples` em superficie permitida ou fortalecer o check se a saida contradisser estes estados.

## 2026-06-13 - Catalogo textual bloqueado vira ponte para conector operado

Decisao: criar `data/research/demand_textual_surface_catalog.jsonl` e o check `demand-textual-surface-catalog` para registrar superficies textuais candidatas antes de operar coleta. O catalogo guarda documentacao, politica, campos textuais, aderencia PT-BR, revisao de termos/atribuicao, proxima acao e flags publicas falsas; ele nao coleta corpo externo, nao alimenta ranking, nao cria rascunho e nao publica.

Motivo: somente metadata de endpoint nao basta para escolher onde buscar linguagem real, mas guardar texto externo sem politica e sem conector validado cria risco de clone, spam e falso positivo. O catalogo transforma pesquisa de superficie em decisao executavel: candidato pronto deve virar conector operado com `--require-content-samples`, tentativa versionada e amostra bloqueada validada.

Consequencia: `internal/demandsurfacecatalog`, `tools/check-demand-textual-surface-catalog`, `content/storage_contract.json`, `internal/checks` e `internal/storage` passam a validar a camada. O coletor tambem aceita uma superficie textual exigida satisfeita por amostra PT-BR valida sem mascarar isso como observacao metadata-only: o attempt fica `surface_attempt_completed_with_textual_samples`, `accepted_records=0`, `valid_content_samples>0` e flags publicas fechadas.

Autocrítica: O que podemos melhorar, e por que? O próximo avanço deve operar um candidato do catálogo contra superfície permitida real, porque catálogo é ponte de engenharia e não substitui amostra aceita. É seguro? Sim: a camada é planning-only, `raw_text_stored=false`, sem render, sitemap, `public_path` ou publicação, e o coletor mantém texto externo em `demand_content_samples` bloqueado. É otimização real? Sim: reduz tentativa cega, orienta conector e permite macrocamada textual sem empurrar CPU para produção. É teste real sem falso positivo ou negativo? Os testes cobrem catálogo público/passivo inválido, check integrado, sample-only sem metadata e bloqueio de ranking por amostra; ainda precisa de operação real para calibrar falso negativo de payload/política.

## 2026-06-16 - Codex 2 escopa coleta por frontier e grava decisões de fonte

Decisao: a frente Codex 2 deixa de tratar cobertura externa como comando global e passa a operar por `--frontier-id` e `--opportunity-id` em `collect-demand-observations`. Rodada por frontier exige `--merge-existing`, `--focus-unobserved`, `--exhaust-selected-opportunities` e pelo menos um `--require-surface`; frontier desconhecida, oportunidade desconhecida ou oportunidade fora da frontier falham. As tentativas passam a preservar escopo por hash para não sobrescrever tentativa de outra frontier.

Motivo: os 4.800 itens da frontier Codex 2 estavam selecionados, mas sem evidência por frontier. Coleta global podia aumentar contadores gerais e ainda deixar a seleção Codex 2 sem observação real. A solução é gravar o escopo da coleta, gerar relatório permanente por frontier e separar fonte oficial metadata-only de aprovação final.

Consequencia: `codex2_frontier_collection_report` entra como camada permanente em `data/research/codex2_frontier_collection_report.jsonl`, com 120 frontiers, 4.800 oportunidades selecionadas, 5 observadas e 4.795 pendentes no estado vivo. `codex2_source_resolution_decisions` entra em `data/research/codex2_source_resolution_decisions.jsonl`, com 209 decisões metadata-only: 57 candidatos prontos para live recheck, 151 exigindo revisão editorial contextual e 1 exigindo alternativa mais específica. Os wrappers `./tools/generate-codex2-frontier-collection-report`, `./tools/check-codex2-frontier-collection-report`, `./tools/generate-codex2-source-resolution-decisions` e `./tools/check-codex2-source-resolution-decisions` ficam registrados no check global e no ledger de performance. Nenhuma decisão aprova fonte final, scraping, ingestão, rascunho, render, sitemap, `content/pages.json`, `published_manifest` ou publicação.

Autocrítica: a melhoria é segura porque só altera coleta/dados bloqueados e mantém flags públicas fechadas. É otimização real porque transforma uma frente de 4.800 oportunidades em execução mensurável por frontier e reduz falso verde de coleta global. A validação prova comandos, schema, contadores, ausência pública e checks focados; ainda não prova cobertura suficiente, fonte final auditada nem página pública. O próximo avanço Codex 2 deve continuar ondas de 2 a 10 frontiers, recalcular prioridade e decisões, e registrar tentativa bloqueada ou observação real por superfície exigida antes de qualquer promoção editorial.

## 2026-09-09 - Turbo com teto de potência, e prioridade de CPU por slice em vez de nice

Decisao: (1) o TLP passa a ser a única autoridade sobre governor/EPP/turbo do host (`ops/tlp.d/10-wikijuridica-cpu.conf`), o `tuned` é desativado, e `wikijuridica-energia.service` grava RAPL PL1=17 W / PL2=25 W nas duas zonas (MSR e MMIO) com turbo ligado. (2) Três slices irmãs no root do cgroup v2 — `wikijuridica.slice` (servir, CPUWeight=1000, MemoryLow=2G), `wikijuridica_alimentacao.slice` (ollama, cérebro, coletas; 100) e `wikijuridica_lote.slice` (timers; 30) — com drop-in de prefixo `wikijuridica-.service.d/` e exceções por nome completo. (3) Chrome nasce em `desktopleve.slice` (user manager, peso 30, MemoryHigh=6G) via override do `.desktop`. Sem cota, sem pinagem de núcleo, sem suspensão: S3 pararia o túnel; o "dormir" do host é tela apagada.

Motivo: medido em 2026-09-09, `no_turbo=1` (escrita manual, sem persistência) prendia o i7-8565U em 1,8 GHz como resposta ao throttle de 09-04, e o `tuned` ainda forçava `min_perf_pct=100`. Em cgroup v2, `Nice=19` nos lotes não protegia nada: nice só ordena dentro do mesmo cgroup, e cada service tinha peso 100 igual ao servidor. Onze lotes não tinham nem isso. `user.slice` e `system.slice` empatavam em 100. Nomes com hífen foram evitados porque o systemd aninha por hífen e o peso é hierárquico — a versão aninhada daria ao LLM ~8× o Claude Code, invertendo `c35d40a8`.

Consequencia: com llama-server a 400 %, o regime sustentado foi de 1,8 GHz/9,8 W/67 °C para 2,3–2,4 GHz/17 W/82–84 °C sem crescimento de throttle (20 W chegou a 87 °C subindo; PL2=30 W deu 90 °C). Sob contenção (llama + lote grafo-juridico + wrk em user.slice): 6 126 req/s, p50 3,1 ms, p99 39 ms em `/`, `cpu.pressure some` de `wikijuridica.slice` 27,8 contra 47,5 de `user.slice`. Tudo em `ops/`, symlink em `/etc`, `ops/host-state/CHECKLIST-REBOOT.md` §(a2) lista item × persiste × prova. Série contínua em `data/ops/energia_cpu.jsonl`.

Autocrítica: PL1=17 W é o ponto medido em uma hora, não em uma semana de verão; a série decide se sobe a 18 ou desce a 15 — o critério é pacote < 85 °C sustentado e throttle sem crescer. `MemoryHigh` da slice de lote ficou de fora de propósito até haver `memory.peak` de 24 h. A instância de Chrome aberta antes da mudança segue na sessão antiga até reabrir. Não há lock de tela (xfce4-screensaver sem config, light-locker ausente): risco físico registrado, fora deste escopo.

