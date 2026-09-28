# ADR: Colly para probe local de metadados de demanda

Data: 2026-07-01

## Decisão

Adotar `github.com/gocolly/colly/v2` v2.3.0 somente no adapter interno `internal/collydemandmetadata`, com uso limitado a probe local `httptest`, respeito a `robots.txt`, concorrência controlada e armazenamento apenas de hashes/contadores de metadados. A evidência fica em `data/research/colly_demand_metadata_probe_evidence.jsonl` e não autoriza scraping, ingestão textual, renderização, sitemap, manifesto publicado ou publicação.

## Comparação

- Colly: projeto Go, licença Apache-2.0, API de coletor com callbacks, limites por domínio, delays, concorrência, cache e suporte a robots. Não duplica goquery/gofeed/trafilatura: entra como orquestrador controlado de coleta metadata-only.
- ProjectDiscovery Katana: Go e adequado para descoberta de endpoints, inclusive modo headless. Para esta frente é mais pesado e orientado a crawling/segurança; não era a menor integração para provar política de demanda bloqueada.
- Crawlee: Apache-2.0 e maduro para crawling, mas é Node/TypeScript e traz superfície operacional/browser maior que o necessário para um repositório Go-first.

## Contrato

O adapter rejeita rede externa por padrão, usa apenas fixture local, prova bloqueio por robots e persiste somente:

- hashes de URL, título, descrição e canonical;
- host/path hash, status HTTP e contadores de H1/links;
- flags públicas e de ingestão fechadas.

Qualquer uso fora de `internal/collydemandmetadata/` deve reprovar em `codex2-policy-enforcement`. Qualquer evidência com `publication_allowed`, `render_allowed`, `sitemap_allowed`, `approval`, `raw_text_stored`, `full_text_stored`, `scraping_allowed` ou `ingestion_allowed` reprova.

## Fontes

- https://github.com/gocolly/colly
- https://pkg.go.dev/github.com/gocolly/colly/v2
- https://docs.projectdiscovery.io/opensource/katana/overview
- https://github.com/apify/crawlee
