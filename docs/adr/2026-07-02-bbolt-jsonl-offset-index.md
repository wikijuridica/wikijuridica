# ADR: bbolt para índice derivado de offsets JSONL

`go.etcd.io/bbolt` v1.4.0 fica aprovado somente atrás de `internal/jsonloffsetindex`.

O uso é um sidecar derivado em `data/ops/refined_public_prose_source_content_id.bbolt`: ID -> offset, length e SHA-256 da linha JSONL. O JSONL continua sendo fonte de verdade; o índice acelera lookup pontual e valida drift por hash antes de qualquer uso.

Riscos: índice stale, lock de arquivo local e uso indevido como fonte primária. Mitigação: adapter restrito, `ReadAt` com hash por linha, comparação de SHA-256 e bytes do JSONL completo contra o resumo gravado, erro explícito para índice ausente, fingerprint determinístico sem duração de build, flags públicas fechadas, teste de drift e política sem render, sitemap, manifesto ou publicação.

A evidência material em `data/ops/jsonl_offset_index_bbolt_evidence.jsonl` deve declarar `source_stale_detected=true`, `missing_index_detected=true`, `readat_sha256_mismatch_detected=true`, `deterministic_record_fingerprint_excludes_build_duration=true`, `jsonl_canonical=true`, `no_public_artifacts_touched=true` e `index_policy="noindex"`.
