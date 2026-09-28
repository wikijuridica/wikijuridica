# INGEST_SPEC.md — Ingestão de páginas v2 no estoque (Fase B)

Ferramenta: `cmd/ingest-v2-pages` (a criar após o retrofit de URL). Converte páginas escritas (WRITING_SPEC §7, em `data/editorial/v2_pages/<area>.jsonl`) para o estoque canônico da cadeia authorial_mass.

## Mapeamento de campos (v2 → estoque)

| v2 (WRITING_SPEC) | Estoque (drafts schema) |
|---|---|
| intent_id | derivar `seed_term_id`/`scenario_id`/`context_id` de forma que `PublicPagePath(...)` = `/{practice_area}/{intent-slug}/`; `unique_intent_id = intent_id` |
| title | title_draft |
| meta_description | meta_description_draft |
| h1 | h1_draft |
| opening | opening |
| sections[] {heading,text} | body_sections[] {heading,text} (FAQ vira seção final "Perguntas frequentes sobre ..." com pares pergunta/resposta em texto corrido, apenas se houver faq) |
| official_sources[].url | official_source_urls[] |
| lane | contractual_intent_status: comercial → high_intent…; informativa → lane informativa/paid blocked coerente |
| (portfólio) long_tail_query | long_tail_query |
| (portfólio) reader_problem | reader_problem |

Flags sempre: `index_policy=noindex`, `publication_allowed=false`, `render_allowed=false`, `sitemap_allowed=false`, `public_path=""` até release.

## Invariantes a ajustar

- `authorialmassdrafts.InitialBlockedBatchSize` (300) e `authorialmasscontentexpansion.ExpansionRecordCount` (9.700) são constantes de contagem do estoque velho. **Resolvido (2026-07-06):** as invariantes de contagem do estoque agora são dirigidas pelo manifesto versionado `data/editorial/stock_manifest.json` (`{schema_version, drafts_expected, expansion_expected, updated_at, note}`, pacote `internal/stockmanifest`). Sem manifesto, valem as constantes históricas (comportamento antigo intacto); com manifesto, ele manda (`authorialmassstock.ValidateRecordsForRoot`), e manifesto inválido reprova (`authorial_mass_stock_manifest_invalid`), nunca cai em fallback silencioso. No regime do manifesto os limiares fixos de diversidade do corpus v1 (cenário/contexto cartesianos) deixam de se aplicar, porque a tripla v2 é `{seed_term_id = intent_id sem prefixo de área, scenario_id="", context_id=""}` por design. A ferramenta `cmd/ingest-v2-pages` atualiza o manifesto a cada lote aceito.
- `authorial_mass_content_expansion_section_chunks.jsonl` (corpos externalizados) fica vazio/regenerado — v2 mantém corpo inline (corpos de 700–1400 palavras cabem na linha).

## Validações da ingestão (reprova a página, nunca "conserta" silenciosamente)

1. JSON válido, campos obrigatórios presentes, word_count coerente com o corpo (±10%).
2. Faixas de extensão por page_type (WRITING_SPEC §3).
3. title 20–65 chars; meta 70–160; h1 única e ≠ title.
4. `intent_id` existe no portfólio v2 consolidado; não pode haver duas páginas ativas com o mesmo identificador em nenhum shard finalizado. `audit_v2_pages.py --global` reprova todas as ocorrências por `intent_id_dup_global`. Uma cópia histórica só deixa o estoque ativo por tombstone `duplicate_intent_consolidated` com arquivo original preservado e `superseded_by` validado contra exatamente um vencedor ativo do mesmo intent; o merge transacional reprova alvo ausente, ambíguo, divergente ou no próprio shard.
5. PT-BR: sem mojibake, sem vocabulário interno (rascunho, CTA, seed, gate, release...), acentuação presente (heurística: proporção de palavras acentuadas plausível) e sem conectivo mecânico terminal como `, com RGST, CDC e LGT continuam aplicáveis.`. Python e Go reprovam esse falso-verde por `ptbr_conectivo_mecanico` / `visible_text_malformed_ptbr_conjunction`; a redação natural usa uma relação sintática completa, como `enquanto ... continuam aplicáveis`.
6. Fontes: 2–5 URLs oficiais https, hosts em allowlist (planalto.gov.br, gov.br, *.jus.br, bcb.gov.br, ans.gov.br, anatel.gov.br, aneel.gov.br, susep.gov.br, inpi.gov.br, receita, anpd, consumidor.gov.br...). O Python e a ingestão Go espelham a exceção fechada 6/6 apenas para `tel-linha-no-meu-cpf-fraude` e `tel-roaming-internacional-conta-alta`, condicionada a exatamente seis classes obrigatórias na matriz canônica; qualquer 7ª fonte e qualquer 6ª fonte fora desses intents reprovam.
7. Lane × conteúdo: página informativa não pode ter linguagem de contratação; comercial precisa do sinal paid-intent no corpo.

Saída: relatório JSONL por lote (aceitos/reprovados + razões) em `data/ops/v2_ingest_report.jsonl`; reprovados vão para fila de reescrita `data/editorial/v2_rewrite_queue.jsonl`.
