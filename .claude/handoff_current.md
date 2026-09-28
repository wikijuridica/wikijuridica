# wiki — session handoff (auto-generated)

**Generated:** 2026-09-08 20:03 UTC

<!-- HANDOFF_ROOT: /opt/wiki in_git=1 -->
<!-- HANDOFF_WRITER: sid=7acffc9d-a6de-4b38-9e7e-b85e3eca0eec t=1788897818 -->

Auto-written by the claude-code-handoff plugin's `bin/write_handoff.sh`
(called from the `/handoff` skill + the `SessionEnd` hook wired in the
plugin's own `hooks/hooks.json`, not `~/.claude/settings.json`).
Auto-loaded into the next session by the `SessionStart` hook in that same
file. Running from `/home/rafael/.claude/plugins/cache/claude-code-handoff/claude-code-handoff/0.18.2/bin`. Lives at `<root>/.claude/handoff_current.md`, where
`<root>` is resolved from the Claude Code project dir (falling back to
the hook payload's cwd, then the process cwd) and then anchored on that
dir's git toplevel — the same resolution the loader uses, recorded in the
`HANDOFF_ROOT` comment above. The previous handoff is rotated to
`.claude/handoff_history/` before
overwrite (last 5 retained; override via `HANDOFF_HISTORY_KEEP`).
Run `/handoff-more` in a fresh session to pull older handoffs into context.

---

## Repo: wiki

**HEAD:** `1a6dc393` — data(corpus): Terceira Turma do STJ coletada (8.337 acordaos); grafo, risco e propostas regenerados

**Branch:** `main` (main...origin/main [ahead 3276])

### Recent commits

```
1a6dc393 data(corpus): Terceira Turma do STJ coletada (8.337 acordaos); grafo, risco e propostas regenerados
296ce2bb fix(propostas): um acordao por chave nos candidatos de precedente; descartados no resumo
153b39c1 feat(propostas): precedente so com similaridade textual medida; coleta do STJ diaria e com direito privado primeiro
816e518a chore(claude-code): settings do projeto sem regra invalida e sem defaultMode que anulava o bypass do usuario
675b1b4e feat(ops): serie diaria de retorno por porta de maquina a partir do evento unificado
c5e721cd feat(mcp): risco_de_superacao medido por pagina e agregado em contexto_juridico (P3)
e6007ba0 feat(lexml,cerebro): CTN, CP e CPP resolvem pela sigla; sumulas no plural e vinculantes viram chaves do grafo
fb1d5fb6 fix(cerebro): norma estadual nunca vira URN federal; reabrir concluidas para refazer um lote defeituoso
d52bf0d0 fix(cerebro): o que o 1o lote real de extracao ensinou -- precedente nao e norma, artigo dentro da norma, resposta cortada
0eaf7b1d feat(cerebro): extracao de dispositivos por LLM so nas ementas sem referencia estruturada
```

### Working tree

```
 M .agents/runtime/generate-wrapper-claims/generate-agent-skill-archives.jsonl
 M .agents/runtime/medicao-precommit/trace-20260905.txt
 M .agents/runtime/tmp_rescue/20260830/MANIFESTO.jsonl
 M .env.local.example
M  AI-first-wikijuridica.bot
 M content/legal_cocitation_index.jsonl
 M content/pages.json
 M data/editorial/authorial_mass_drafts.jsonl
 M data/editorial/authorial_mass_manifest_transaction_rehearsal.jsonl
 M data/editorial/published_manifest.jsonl
 M data/editorial/stock_manifest.json
 M data/editorial/v2_publication_severity.jsonl
 M data/editorial/v2_rewrite_queue.jsonl
 M data/ops/access/access-2026-09-05.jsonl
 M data/ops/access/nginx-2026-09-05.jsonl
 M data/ops/ai_citation_signal_cursor.json
 M data/ops/ai_citation_signal_daily.jsonl
 M data/ops/backup_restore_ensaio.jsonl
 M data/ops/backup_wiki.jsonl
 M data/ops/bcb_normativo_servable_address_20260812.jsonl
 M data/ops/bing_webmaster_daily.jsonl
 M data/ops/bing_webmaster_state.json
 M data/ops/bot_ip_ranges/anthropic.json
 M data/ops/bot_ip_ranges/applebot.json
 M data/ops/bot_ip_ranges/bingbot.json
 M data/ops/bot_ip_ranges/duckassistbot.json
 M data/ops/bot_ip_ranges/duckduckbot.json
 M data/ops/bot_ip_ranges/google-special-crawlers.json
 M data/ops/bot_ip_ranges/google-user-triggered.json
 M data/ops/bot_ip_ranges/googlebot.json
 M data/ops/bot_ip_ranges/openai-adsbot.json
 M data/ops/bot_ip_ranges/openai-chatgpt-user.json
 M data/ops/bot_ip_ranges/openai-gptbot.json
 M data/ops/bot_ip_ranges/openai-searchbot.json
 M data/ops/bot_ip_ranges/perplexity-user.json
 M data/ops/bot_ip_ranges/perplexitybot.json
 M data/ops/bot_registry_candidates.jsonl
 M data/ops/bot_return_daily.jsonl
 M data/ops/bot_return_state.json
 M data/ops/clarity_insights_daily.jsonl
 M data/ops/clarity_insights_state.json
 M data/ops/crawl_coverage_daily.jsonl
 M data/ops/crawl_coverage_never_requested.json
 M data/ops/crawl_coverage_state.json
 M data/ops/crawler_error_budget.jsonl
 M data/ops/daily_content_collect.jsonl
 M data/ops/daily_content_runs.jsonl
 M data/ops/datajud_latencia_percebida.jsonl
 M data/ops/deploy_binario_go.jsonl
 M data/ops/deploy_layer_fingerprint.json
 M data/ops/disk_growth.jsonl
 M data/ops/disk_headroom.jsonl
 M data/ops/djen_coleta_heartbeat.jsonl
 M data/ops/edge_bot_agents_daily.jsonl
 M data/ops/edge_bot_status_daily.jsonl
 M data/ops/edge_cache_coverage.jsonl
 M data/ops/edge_cache_purge.jsonl
 M data/ops/edge_cache_warm.jsonl
 M data/ops/edge_live.jsonl
 M data/ops/edge_probe_requests.jsonl
 M data/ops/edge_rule_apply.jsonl
 M data/ops/edge_traffic_daily.jsonl
 M data/ops/eventos/cursor.json
 M data/ops/eventos/eventos-2026-09-08.jsonl
 M data/ops/fontes_alcancaveis.jsonl
 M data/ops/gates_rotativos.jsonl
 M data/ops/ia_local_daily.jsonl
 M data/ops/incidents.jsonl
 M data/ops/indexnow_direct_submissions.jsonl
 M data/ops/indexnow_submission_state.json
 M data/ops/indexnow_url_state.jsonl
 M data/ops/network_health.jsonl
 M data/ops/network_health_state.json
 M data/ops/origin_bot_routes_daily.jsonl
 M data/ops/origin_bot_traffic_cursor.json
 M data/ops/origin_bot_traffic_daily.jsonl
 M data/ops/origin_cache_purge.jsonl
 M data/ops/origin_cache_warm.jsonl
 M data/ops/owner_alerts.jsonl
 M data/ops/owner_alerts_state.json
 M data/ops/page_content_revision.jsonl
 M data/ops/portal_health.jsonl
 M data/ops/portal_health_state.json
 M data/ops/qualidade_diaria.jsonl
 M data/ops/qualidade_por_decil.jsonl
 M data/ops/qualidade_race.jsonl
 M data/ops/retorno_por_rota_daily.jsonl
 M data/ops/serie_404_bots.jsonl
 M data/ops/server_reload.jsonl
 M data/ops/sitemap_shard_grace.jsonl
 M data/ops/sitemap_shard_registry.json
 M data/ops/social_humano_daily.jsonl
 M data/ops/superficie_bots_live.jsonl
 M data/ops/time_to_first_crawl_daily.jsonl
 M data/ops/tunnel_gaps.jsonl
 M data/ops/tunnel_health.jsonl
 M data/ops/tunnel_health_state.json
 M data/ops/v2_ingest_report.jsonl
 M data/ops/v2_ingest_transaction_receipt.json
 M data/ops/v2_publication_severity_summary.json
 M data/ops/websub_ping_state.json
 M data/ops/websub_pings.jsonl
 M data/research/daily/diarios-municipais/2026-09-04.jsonl
 M data/research/daily/noticias-oficiais/_estado.json
 M data/research/daily/stj-precedentes/_estado.json
 M data/source-audit/v2_source_provenance.jsonl
M  docs/goal/MAESTRO_CODEX_LOG.md
 M go.mod
 M go.sum
 M internal/httpserver/access_log.go
 M internal/httpserver/httpserver.go
 M internal/httpserver/oauth.go
 M internal/legalfacts/norma.go
M  internal/lexml/knowncodes_ctn_test.go
M  internal/lexml/planalto.go
A  internal/structureddata/legislation_url_test.go
M  internal/structureddata/structured_data.go
M  internal/v2ingest/validator_fingerprint_attestation_generated.go
 M ops/host-state/CHECKLIST-REBOOT.md
 M ops/host-state/GERADO_EM.txt
 M ops/host-state/etc/du
 M ops/host-state/etc/find
 M ops/host-state/etc/sysctl.conf
 M ops/host-state/sysctl-declarado.txt
 M ops/host-state/units-copiadas.txt
 M ops/host-state/units-habilitadas.txt
 M scripts/workflows/writing-mass-todo-sem-telecom.js
 M scripts/workflows/writing-mass-todo.js
 M tools/check-nginx-standalone-parity
 M tools/generate-evento-unificado
 M tools/generate-retorno-por-rota
 M tools/test_evento_unificado.py
 M tools/test_retorno_por_rota.py
 M tools/test_run_tdd_guard_test.sh
?? .agents/runtime/2026-09-05/
?? .agents/runtime/aifirst/agente-H/
?? .agents/runtime/aifirst/agente-I/
?? .agents/runtime/aifirst/aplicar-automode-allow.py
?? .agents/runtime/aifirst/attest-lexml.log
?? .agents/runtime/aifirst/attest-lexml2.log
?? .agents/runtime/aifirst/coleta-turmas-privadas.log
?? .agents/runtime/aifirst/commit-artigos.log
?? .agents/runtime/aifirst/commit-cerebro-2.log
?? .agents/runtime/aifirst/commit-cerebro.log
?? .agents/runtime/aifirst/commit-coleta3t.log
?? .agents/runtime/aifirst/commit-contexto.log
?? .agents/runtime/aifirst/commit-extracao.log
?? .agents/runtime/aifirst/commit-extracao2.log
?? .agents/runtime/aifirst/commit-extracao3.log
?? .agents/runtime/aifirst/commit-extracao4.log
?? .agents/runtime/aifirst/commit-extracao5.log
?? .agents/runtime/aifirst/commit-extracao6.log
?? .agents/runtime/aifirst/commit-lexml-url.log
?? .agents/runtime/aifirst/commit-medicao.log
?? .agents/runtime/aifirst/commit-msg-artigos.txt
?? .agents/runtime/aifirst/commit-msg-cerebro.txt
?? .agents/runtime/aifirst/commit-msg-coleta3t.txt
?? .agents/runtime/aifirst/commit-msg-contexto.txt
?? .agents/runtime/aifirst/commit-msg-extracao.txt
?? .agents/runtime/aifirst/commit-msg-extracao2.txt
?? .agents/runtime/aifirst/commit-msg-extracao3.txt
?? .agents/runtime/aifirst/commit-msg-extracao4.txt
?? .agents/runtime/aifirst/commit-msg-lexml-url.txt
?? .agents/runtime/aifirst/commit-msg-medicao-mcp.txt
?? .agents/runtime/aifirst/commit-msg-medicao.txt
?? .agents/runtime/aifirst/commit-msg-oauth-ledger.txt
?? .agents/runtime/aifirst/commit-msg-onda2.txt
?? .agents/runtime/aifirst/commit-msg-onda5.txt
?? .agents/runtime/aifirst/commit-msg-p2.txt
?? .agents/runtime/aifirst/commit-msg-p2b.txt
?? .agents/runtime/aifirst/commit-msg-refutacao.txt
?? .agents/runtime/aifirst/commit-msg-retorno.txt
?? .agents/runtime/aifirst/commit-msg-risco.txt
?? .agents/runtime/aifirst/commit-onda2.log
?? .agents/runtime/aifirst/commit-p2.log
?? .agents/runtime/aifirst/commit-p2b.log
?? .agents/runtime/aifirst/commit-refutacao.log
?? .agents/runtime/aifirst/commit-retorno.log
?? .agents/runtime/aifirst/commit-risco.log
?? .agents/runtime/aifirst/commit-risco2.log
?? .agents/runtime/aifirst/commit-risco2.sh
?? .agents/runtime/aifirst/commit-risco3.log
?? .agents/runtime/aifirst/deploy-binario-20260908-2.log
?? .agents/runtime/aifirst/deploy-binario-20260908-3.log
?? .agents/runtime/aifirst/deploy-binario-20260908.log
?? .agents/runtime/aifirst/deploy-risco.log
?? .agents/runtime/aifirst/deploy-risco2.log
?? .agents/runtime/aifirst/extracao_4b_amostra.log
?? .agents/runtime/aifirst/medicao_threads_20260908.log
?? .agents/runtime/aifirst/onda2-paths.txt
?? .agents/runtime/aifirst/pos-coleta.log
?? .agents/runtime/aifirst/pos-coleta.sh
?? .agents/runtime/aifirst/recoleta-stj-20260908-2.log
?? .agents/runtime/aifirst/recoleta-stj-20260908.log
?? .agents/runtime/aifirst/settings.json.antes-tdd-guard-20260908
?? .agents/runtime/aifirst/stj-espelhos-antes-artigo/
?? .agents/runtime/aifirst/test-lexml-url.log
?? .agents/runtime/aifirst/test-oauth-log.log
?? .agents/runtime/aifirst/test-risco.log
?? .agents/runtime/aifirst/testar_extracao_4b.py
?? .agents/runtime/aifirst/valida_candidato.py
?? .agents/runtime/backup-lgpd-20260905/
?? .agents/runtime/binarios/
?? .agents/runtime/commit-tdd-guard-20260908.txt
?? .agents/runtime/completude.go.com-guarda-20260905
?? .agents/runtime/completude.go.otimizado-20260905
?? .agents/runtime/derivados-antes-20260905/
?? .agents/runtime/fase0/
?? .agents/runtime/fase1/
?? .agents/runtime/fila-escrita-antes-20260905/
?? .agents/runtime/frontier-antes-20260905/
?? .agents/runtime/frontiers-antes-20260905/
?? .agents/runtime/generate-wrapper-claims/generate-authorial-mass-manifest-transaction.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-codex2-coverage-frontier.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-codex2-external-collection-wave.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-codex2-mass-scale-plan.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-codex2-policy-baseline.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-codex2-policy-enforcement.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-languagetool-quality.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-noticia-pages.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-pkgsite-module-audit.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-priority-authorial-claim-graph.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-sqlite-fts5-corpus-evidence.jsonl
?? .agents/runtime/generate-wrapper-claims/generate-vale-public-prose-lint.jsonl
?? .agents/runtime/institucional-source-verification-backup/
?? .agents/runtime/intake-desenho-anterior-20260905/
?? .agents/runtime/malha/
?? .agents/runtime/medicao-precommit/gitleaks-tools.txt
?? .agents/runtime/medicao-precommit/redesocial-depois.txt
?? .agents/runtime/medicao-precommit/redesocial.txt
?? .agents/runtime/medicao-precommit/trace-depois-20260905.txt
?? .agents/runtime/medicao-precommit/vermelhos-20260905.txt
?? .agents/runtime/medicao-race/demandobservations.go.antes-do-bot
?? .agents/runtime/mensagens/
?? .agents/runtime/migracao_finalidades.jsonl
?? .agents/runtime/msgs/
?? .agents/runtime/nginx-standalone.antes-assets-20260905
?? .agents/runtime/nginx-standalone.antes-bot-20260905
?? .agents/runtime/pages-json-antes/
?? .agents/runtime/pre-commit.antes-baseline-redesocial-20260905
?? .agents/runtime/preservado-molde-20260904/
?? .agents/runtime/qualidade-race/
?? .agents/runtime/site-json-antes/
?? .agents/runtime/staging/rca-classificador-lote-20260905/
?? .agents/runtime/stf-informativo-derivado-01.jsonl.antes-20260904
?? .agents/runtime/tmp_rescue/20260901/
?? .agents/runtime/tmp_rescue/20260902/
?? .agents/runtime/tmp_rescue/20260903/
?? .agents/runtime/tmp_rescue/20260904/
?? .agents/runtime/tmp_rescue/20260905/
?? .agents/runtime/tmp_rescue/20260906/
?? .agents/runtime/tmp_rescue/20260908/
?? .agents/runtime/v2-artigo-ponto-antes-20260905/
?? .agents/runtime/wikijuridica.conf.antes-bot-20260905
?? .agents/skills/
?? .claude-flow/
?? .claude/.handoff_current.6twyfq
?? .claude/.handoff_current.Ovythn
?? .claude/.handoff_skel.F8WZUb
?? .claude/.handoff_skel.omxHCq
?? .claude/.proven-config-version
?? .claude/proven-config.json
?? .claude/rules/
?? .github/workflows/playwright.yml
?? .omc/
?? 3D-Machine-Learning/
?? AegisFlow/
?? Aetheris/
?? Auto-claude-code-research-in-sleep/
?? Awesome-Deblurring/
?? Awesome-Learning-with-Label-Noise/
?? Awesome-Machine-Learning-in-Biomedical-Healthcare-Imaging/
?? Awesome-Neuron-Segmentation-in-EM-Images/
?? Awesome-Visual-Transformer/
?? Awesome-explainable-AI/
?? Awsome-Deep-Learning-for-Video-Analysis/
?? Awsome-GAN-Training/
?? Awsome_Deep_Geometry_Learning/
?? Awsome_Delineation/
?? CyberChef/
?? Deep-Learning-for-Tracking-and-Detection/
?? FckSignups/
?? Flat-UI/
?? FunASR/
?? Gito/
?? GoModel/
?? GovCMS/
?? Java/
?? Lucee/
?? MaxKB/
?? OpenMythos/
?? Python/
?? Scheduled/painel-banca-toledo/
?? Scrapling/
?? ShareX/
?? Singular/
?? ToolJet/
?? TrendRadar/
?? TypeScript/
?? Vale/
?? WTFJHT/
?? abnt-citation/
?? action-center-platform/
?? activepieces/
?? adobe.github.com/
?? aflare
?? agent-sdk-go/
?? agentops/
?? agents-party/
?? agy-mcp/
?? ai-gateway/
?? ai-maestro/
?? ai/
?? alacritty/
?? algo/
?? ally.js/
?? angular/
?? api-umbrella/
?? appsmith/
?? arscontexta/
?? asreview/
?? atmos/
?? aurelia/
?? autoharness/
?? awesome-action-recognition/
?? awesome-adversarial-examples-dl/
?? awesome-adversarial-machine-learning/
?? awesome-anomaly-detection/
?? awesome-claude-plugins/
?? awesome-computer-vision/
?? awesome-dataset-tools/
?? awesome-deep-learning/
?? awesome-deep-vision/
?? awesome-document-understanding/
?? awesome-domain-adaptation/
?? awesome-embodied-vision/
?? awesome-fairness-in-ai/
?? awesome-generative-modeling/
?? awesome-graphics/
?? awesome-human-pose-estimation/
?? awesome-implicit-representations/
?? awesome-jupyter/
?? awesome-machine-learning-interpretability/
?? awesome-machine-learning-on-source-code/
?? awesome-machine-learning/
?? awesome-medical-imaging/
?? awesome-neural-rendering/
?? awesome-nlp/
?? awesome-object-detection/
?? awesome-php/
?? awesome-public-datasets/
?? awesome-rl/
?? awesome-robotics-datasets/
?? awesome-robotics/
?? awesome-scene-understanding/
?? awesome-vision-language-pretraining-papers/
?? backend-security-skill/
?? bash-it/
?? bat/
?? beeswithmachineguns/
?? betterspecs/
?? bootstrap/
?? budibase/
?? bus.jpg
?? cardkit/
?? cc-safety-net/
?? censusreporter/
?? chapel/
?? checkov/
?? cheerio/
?? chromem-go/
?? chronline/
?? claude-code-prompt-plan/
?? claude-code-settings/
?? claude-d2-diagrams/
?? claude-extensions/
?? claude-languages/
?? claude-octopus/
?? claude-plugins/
?? claude-sandbox/
?? claude-services/
?? claude-status/
?? collect-stj-acordaos
?? collect-stj-precedentes-qualificados
?? commit-sage-cli/
?? consul/
?? content/internal_link_mesh_shards/internal-link-mesh-f30e920ce71f11b4/
?? courses/
?? cpython/
?? crewai-go/
?? csharplang/
?? cue/
?? cython/
?? d3/
?? dakera-go/
?? data.gov/
?? data/ai/embeddings/
?? data/ai/extracoes_dispositivos.jsonl
?? data/editorial/v2_raw_recovery_preimages/b85000dc5c5e346b35c5931937ba787a55b7b17d648de526d8c3fa4b815b6773.raw
?? data/ops/access/access-2026-09-06.jsonl
?? data/ops/access/access-2026-09-07.jsonl
?? data/ops/access/access-2026-09-08.jsonl
?? data/ops/access/nginx-2026-08-22.jsonl
?? data/ops/access/nginx-2026-08-23.jsonl
?? data/ops/access/nginx-2026-08-24.jsonl
?? data/ops/access/nginx-2026-08-25.jsonl
?? data/ops/access/nginx-2026-08-26.jsonl
?? data/ops/access/nginx-2026-08-27.jsonl
?? data/ops/access/nginx-2026-08-28.jsonl
?? data/ops/access/nginx-2026-08-29.jsonl
?? data/ops/access/nginx-2026-08-30.jsonl
?? data/ops/access/nginx-2026-08-31.jsonl
?? data/ops/access/nginx-2026-09-01.jsonl
?? data/ops/access/nginx-2026-09-06.jsonl
?? data/ops/access/nginx-2026-09-07.jsonl
?? data/ops/access/nginx-2026-09-08.jsonl
?? data/ops/datajud_atraso_atualizacao.jsonl
?? data/ops/social_indexnow_state.json
?? data/ops/v2_ingest_terminal_receipts/v2-rewrite-v5-399474f712ef868ca1312058ad756ddb.terminal.json
?? data/ops/v2_ingest_terminal_receipts/v2-rewrite-v5-526f93a3d2418361725c1e10f9551841.terminal.json
?? data/research/daily/diarios-municipais/2026-09-05.jsonl
?? data/research/daily/diarios-municipais/2026-09-06.jsonl
?? data/research/daily/diarios-municipais/2026-09-07.jsonl
?? data/research/daily/normas-federais/2026-09-04.jsonl
?? data/research/daily/normas-federais/2026-09-05.jsonl
?? data/research/daily/normas-federais/2026-09-06.jsonl
?? data/research/daily/normas-federais/2026-09-07.jsonl
?? data/research/daily/normas-federais/2026-09-08.jsonl
?? data/research/daily/noticias-oficiais/2026-09-04.jsonl
?? data/research/daily/noticias-oficiais/2026-09-05.jsonl
?? data/research/daily/noticias-oficiais/2026-09-06.jsonl
?? data/research/daily/noticias-oficiais/2026-09-07.jsonl
?? data/research/daily/noticias-oficiais/2026-09-08.jsonl
?? data/research/daily/stj-precedentes/2026-09-04.jsonl
?? data/research/daily/stj-precedentes/2026-09-05.jsonl
?? data/research/daily/stj-precedentes/2026-09-06.jsonl
?? data/research/daily/stj-precedentes/2026-09-07.jsonl
?? data/research/daily/stj-precedentes/2026-09-08.jsonl
?? datagov-11ty/
?? datajud-fila
?? decisiontree/
?? deeplake/
?? deeplearning4j/
?? deja-vu/
?? dem/
?? demand-progress/
?? deployer/
?? design-extract/
?? devtron/
?? diffy/
?? dlib/
?? dmd/
?? dsa/
?? e2e/
?? elasticsearch/
?? eleva/
?? ember.js/
?? engine/
?? engram/
?? enumerate-federal-norms
?? ergo/
?? fabric/
?? fairfield-programming.github.io/
?? fastapi_mcp/
?? foundation-sites/
?? framework/
?? frontend/
?? gatsby/
?? git-imerge/
?? go-sdk/
?? go/
?? goai/
?? goakt/
?? goaltree/
?? google.github.io/
?? gpt-researcher/
?? grafana/
?? groovy/
?? guides/
?? habitus/
?? harness/
?? haxe/
?? helm-dashboard/
?? hivemind/
?? hollywood/
?? hotplex/
?? html-pipeline/
?? html-proofer/
?? hubot/
?? i-have-adhd/
?? imba/
?? internal/httpserver/access_log_oauth_test.go
?? jargo/
?? java-sdk/
?? javascript-algorithms/
?? jbot/
?? jenkins/
?? jq/
?? jshint/
?? jsonview/
?? jsoup/
?? jule/
?? julia/
?? k3s/
?? knockout/
?? knowledge-work-plugins/
?? kong/
?? kotlin-sdk/
?? kotlin/
?? kubeedge/
?? kubernetes/
?? langchaingo/
?? lapce/
?? linguist/
?? logstash/
?? markitdown/
?? marko/
?? material/
?? maxun/
?? medical-data/
?? meme/
?? memsearch/
?? mesos/
?? microsoft.github.io/
?? mithril.js/
?? moby/
?? mocha/
?? moderacao-revisar-prazos
?? modular/
?? monitor-source-changes
?? monoscope/
?? my-app/
?? my-crawler/
?? my-crew/
?? neo/
?? netdata/
?? next.js/
?? nix-config/
?? nomad/
?? notebooks/
?? notfair-plugin/
?? ocaml/
?? ohmyzsh/
?? openapi-directory/
?? opensource-website/
?? openstack/
?? ops/divorcio-desativacao/ai-ping-20260904.bak
?? ops/divorcio-desativacao/crontab-root-20260904-antes-desativar.bak
?? ops/divorcio-desativacao/etc-audit-20260904.tar.gz
?? ops/divorcio-desativacao/etc-divorcio-20260904.tar.gz
?? ops/host-state/systemd/wikijuridica-corpus-oraculo-recoleta.service.link
?? ops/host-state/systemd/wikijuridica-corpus-oraculo-recoleta.timer.link
?? ops/host-state/systemd/wikijuridica-datajud-fila.service.link
?? ops/host-state/systemd/wikijuridica-datajud-fila.timer.link
?? ops/host-state/systemd/wikijuridica-djen-coleta.service.link
?? ops/host-state/systemd/wikijuridica-djen-coleta.timer.link
?? ops/host-state/systemd/wikijuridica-lgpd-expurgo.service.link
?? ops/host-state/systemd/wikijuridica-lgpd-expurgo.timer.link
?? ops/host-state/systemd/wikijuridica-moderacao-revisar-prazos.service.link
?? ops/host-state/systemd/wikijuridica-moderacao-revisar-prazos.timer.link
?? ops/host-state/systemd/wikijuridica-official-source-url-inventory-refresh.service.link
?? ops/host-state/systemd/wikijuridica-official-source-url-inventory-refresh.timer.link
?? ops/host-state/systemd/wikijuridica-qualidade-race.service.link
?? ops/host-state/systemd/wikijuridica-qualidade-race.timer.link
?? ops/host-state/systemd/wikijuridica-social.service.link
?? ops/host-state/systemd/wikijuridica-social.socket.link
?? package-lock.json
?? package.json
?? php-sdk/
?? php-src/
?? picard/
?? playbook/
?? playwright.config.ts
?? pm-skills/
?? preact/
?? preevy/
?? pro-workflow/
?? probe/
?? prometheus/
?? protoactor-go/
?? puppet/
?? python-sdk/
?? qwik/
?? rails/
?? react/
?? red/
?? redis/
?? refine/
?? responsively-app/
?? ring/
?? ripgrep/
?? robots/
?? rocq/
?? roslyn/
?? ruby-sdk/
?? ruby/
?? runs/
?? rust-sdk/
?? rust/
?? scikit-learn/
?? scroll-craft/
?? sdk/
?? seemple/
?? selenium/
?? semantic-kernel/
?? semaphore/
?? servers/
?? skills-lock.json
?? skills/
?? skip/
?? solid/
?? spack/
?? spark/
?? spine/
?? spinnaker/
?? sprockets/
?? stylelint/
?? supremeworkflow-orchestrator/
?? svelte/
?? swift-sdk/
?? swift/
?? taskPlane/
?? tensorflow/
?? terra/
?? terraform/
?? tf-idf-similarity/
?? todomvc/
?? tons-of-skills-marketplace/
?? trigger.dev/
?? trivy/
?? typescript-sdk/
?? v/
?? validator/
?? verify-sumula-precedents
?? whatiscode/
?? wiki-ops
?? xiaohongshu-mcp/
?? yarn.lock
?? yelp.github.io/
?? yolo26n.pt
?? zabbix/
?? zaproxy/
?? zoxide/
```

## In-flight (untracked or modified .md under `docs/`)

- `docs/goal/MAESTRO_CODEX_LOG.md`

<!-- HANDOFF_BIND_BEGIN -->
## Verify state matches reality

Run this now, before anything else this session, and say what you found:

```bash
git -C /opt/wiki status && git -C /opt/wiki log --oneline -5
```
<!-- HANDOFF_BIND_END -->

<!-- HANDOFF_BIND_BEGIN -->
## Rules (fences — carried into the next session)

<!-- HANDOFF_RULES_PLACEHOLDER: /handoff may replace this comment with explicit scope fences. Only content inside the BIND markers loads as binding (and only when provenance verifies); leave this comment in place for none. -->
<!-- HANDOFF_BIND_END -->

---

## Notes from this session

<!-- HANDOFF_PLACEHOLDER: keep until /handoff replaces this block -->

_The /handoff skill should replace this entire block (sentinel
comment included) with curated decisions, in-flight tracks, open
questions, and "next session should start with X" notes. The auto-
snapshot above captures git state; the prose below captures intent
that only the conversation knows. The sentinel above is how the
SessionEnd safety-net detects whether curation has happened._
<!-- HANDOFF_SKEL_HMAC: ba87ca6e1a59f1c328d4e4c01c5d593cd66abb3b07a14969b742ed5e48910455 -->
<!-- HANDOFF_HMAC: 4d7e729aeb6a08ad32290b6950e76b3c4d2417904287a531f836f7cadd2a60fe -->
