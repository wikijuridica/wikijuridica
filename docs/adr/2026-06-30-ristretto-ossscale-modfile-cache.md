# 2026-06-30 - Ristretto para caches de escala OSS e PT-BR

Decisao: adotar `github.com/dgraph-io/ristretto` `v0.2.0` em caches bounded de alta escala: `internal/ossscaleintegration` para parse de `go.mod`/diretivas `tool` durante o check `oss-scale-integration-coverage`, e `internal/refinedpublicprose` para normalizacao repetida de slots PT-BR no refinamento publico bloqueado.

Motivo: o fan-in OSS valida muitas integrações em conteúdo, código, engenharia, performance, PT-BR, crawl, release e SCA. Reparsear o mesmo `go.mod`/tool file e renormalizar o mesmo texto publico em dezenas de estagios vira custo repetido conforme a matriz cresce para 10k/100k/1M. Ristretto fornece cache in-memory thread-safe com TinyLFU/Sampled-LFU; os adapters usam chave exata, cache bounded e flags publicas fechadas.

Escopo permitido: `internal/ossscaleintegration`, `internal/refinedpublicprose`, `data/ops/ristretto_ossscale_cache_evidence.jsonl`, `go.mod` e `go.sum`. A dependência não pode escrever `public/`, `content/pages.json`, `published_manifest`, sitemap, robots ou `.release-staging`, não baixa dados externos e não aprova publicação.

Licença e risco: Apache-2.0. O risco técnico é esconder arquivo stale ou transformacao textual incorreta por cache; mitigação obrigatória é fingerprint de arquivo para `go.mod`/tool, chave `kind+texto_exato` para slots publicos, limite de custo, fallback para computacao normal em miss/rejeicao e testes `TestParseGoModIntegrationFileCachesByFingerprint`, `TestNormalizePublicTextSlotPTBRStoresRistrettoCacheForRepeatedSlots` e `TestCodex2PolicyEnforcementRejectsRistrettoOutsideApprovedCachePackages`.
