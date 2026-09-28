# Gates de publicação P0

Estado: published_manifest=0, deficit_to_10000=10000, publication_allowed=0.

Nenhum registro entra em `published_manifest` se qualquer gate falhar. Os gates bloqueantes atuais são:

- human_score
- ai_like
- thin_content
- keyword_stuffing
- low_lexical_diversity
- repeated_ngram
- boilerplate_title_meta_h1
- doorway_pattern
- shingle_jaccard
- bleve_nearest_neighbor_internal_blocked
- official_source_specific
- own_useful_answer
- human_problem
- required_documents
- legal_risk
- oab_compliance
- google_spam_compliance
- canonical_sitemap_robots_noindex
- automated_tests
- audit_report

Blockers atuais:

- published_manifest=0_deficit_10000
- anti_template_ready=0
- codex_review_ready=0
- paid_intent_blocked_0
- manifest_quality_blocked_1737
- external_demand_coverage_initial_1242_of_12960

Próximas ações executáveis:

- refinar doorway/anti-template nos shards de maior risco antes de publicar
- resolver fonte oficial especifica final e manter raw_text_stored=false
- recalcular readiness/release/manifest quando corpo, CTA, fonte, title ou meta mudarem
- executar promocao publica somente com gate completo e transacao aprovada
