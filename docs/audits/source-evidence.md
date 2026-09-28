# Evidência de fontes oficiais

Este índice registra fontes oficiais usadas para derivar gates. Ele não copia texto oficial para conteúdo publicável e mantém publication_allowed=0.

## Google Search Central - spam policies

- URL: https://developers.google.com/search/docs/essentials/spam-policies?hl=pt-br
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Deriva gates anti-spam, doorway, keyword stuffing, conteúdo próprio e revisão antes de indexação.
- gates: doorway_pattern, keyword_stuffing, scaled_content_abuse, scraping_block

## Google Search Central - robots meta

- URL: https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag?hl=pt-br
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Mantém candidatos bloqueados como noindex,follow e impede esconder página reprovada por robots.txt.
- gates: canonical_sitemap_robots_noindex

## Google Search Central - sitemaps

- URL: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap?hl=pt-br
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Sitemap real só recebe URL aprovada e canônica.
- gates: sitemap_public_only, canonical

## Google Search Central - title links

- URL: https://developers.google.com/search/docs/appearance/title-link?hl=pt-br
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Deriva budget e bloqueio de title/meta/H1 repetidos.
- gates: boilerplate_title_meta_h1

## OAB Provimento 205/2021

- URL: https://www.oab.org.br/leisnormas/legislacao/provimentos/205-2021
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Deriva gates de CTA, OAB, autoria/revisor e bloqueio de gratuidade/BPC como comercial.
- gates: oab_compliance, paid_intent_cta_or_block

## CNJ DataJud API Pública

- URL: https://datajud-wiki.cnj.jus.br/api-publica/
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Permite evidência agregada metadata-only, sem dado pessoal sensível nem publicação de caso individual.
- gates: datajud_metadata_only

## ANS dados e indicadores

- URL: https://www.gov.br/ans/pt-br/acesso-a-informacao/perfil-do-setor/dados-e-indicadores-do-setor
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Permite evidência oficial de demanda/problema humano em saúde suplementar, sem copiar texto para corpo autoral.
- gates: official_source_specific, demand_evidence

## MDS BPC

- URL: https://www.gov.br/mds/pt-br/acoes-e-programas/suas/beneficios-assistenciais/beneficio-assistencial-ao-idoso-e-a-pessoa-com-deficiencia-bpc
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Mantém BPC/LOAS em lane informativa bloqueada, sem CTA comercial.
- gates: public_assistance_block, informational_lane

## Bleve v2 Go Packages

- URL: https://pkg.go.dev/github.com/blevesearch/bleve/v2
- acesso: 2026-06-21
- status: obrigatorio
- impacto: Autoriza uso como índice interno bloqueado para auditoria, não como busca pública P0.
- gates: bleve_nearest_neighbor_internal_blocked

## OpenAI Codex glossary

- URL: https://developers.openai.com/codex/glossary
- acesso: 2026-06-21
- status: contextual
- impacto: Deriva rastreabilidade operacional, subagentes e respeito ao contrato do repo.
- gates: audit_report, automated_tests

