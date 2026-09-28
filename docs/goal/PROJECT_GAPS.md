# PROJECT_GAPS.md — O que falta para wikijuridica.com.br virar classe mundial

Análise de lacunas INTERNA (do código vivo, não da web), redigida pelo Claude Code em
2026-07-11 para combinar com o relatório externo do `/deep-research`. Framing do dono:
o que falta em **regras, código, API, open source e engenharia**. Priorizado por impacto
no P0 (10k páginas únicas publicadas) e no padrão (páginas que Google + bots de IA
reconhecem como autoridade).

## P0 — Bloqueadores diretos de "sair do papel" (publicar)

1. ~~**Cadeia de release dormente (o maior gap).**~~ **RESOLVIDO — verificado em 2026-08-19.**
   Este item descrevia `published_manifest.jsonl` **vazio** e a cadeia nunca tendo produzido
   `verdict_passed>0`. Medição de 2026-08-19: o manifest tem **9.710 linhas** (9.710
   `unique_intent_id` distintos), `public/` tem 9.930 HTMLs, o sitemap servido expõe 9.926
   URLs e o portal responde 200 em produção desde 13/08. O texto abaixo é de 2026-07-11 e
   fica como registro histórico — não como estado.
   *(Redação original: `scaled_content_release_verdict.jsonl` ausente, `published_manifest.jsonl`
   vazio, o mecanismo ingest → verdict → manifest → promoção nunca produziu `verdict_passed>0`.)*
   **Ação:** provar a cadeia ponta-a-ponta num corpus limpo (a frente do Codex está em
   `internal/v2ingest`/`sourceliveevidence`; validar `go test ./internal/v2ingest/` VERDE
   antes de promover — hoje está VERMELHO por `current_legal_facts.go` WIP).
2. **Auditor não escala (`tools/audit_v2_pages.py`, ~6666 linhas).** É gabarito hardcoded
   por intent (regras `current_legal_fact_*` por página) — cobre poucas intents, tem
   falso-positivo (já corrigi o de número de artigo em forma sólida) e falso-negativo, e
   não cobre 10k. **Ação:** substituir por gate SEMÂNTICO de fato jurídico (chaves
   conceituais + verificação de citação contra fonte viva), não string exata por intent.
3. **Provenência incompleta (`verified_at`/`http_status`).** ~1859 fontes sem verificação
   (33% do corpus) — o gate `official_source_verified_at_invalid` do Codex apanhou.
   **Ação:** completar (workflow de provenência rodando) + gate que exija verified_at.

## Regras editoriais NOVAS (descobertas nesta sessão)

4. **Vigência JURISPRUDENCIAL (não só a lei positivada).** Achado grave: o art. 19 do
   Marco Civil estava como vigente pleno em 5 páginas, mas o STF (Tema 987, 26/06/2025) o
   declarou parcialmente inconstitucional. Verificamos o texto do Planalto, NÃO a
   jurisprudência vinculante. **Regra nova:** toda citação de dispositivo sujeito a
   controle concentrado/repercussão geral/súmula vinculante exige checagem de modulação
   STF/STJ. Precisa de dado (lista de dispositivos modulados) + gate.
5. **Fonte estável, nunca índice genérico.** `processo.stj.jus.br/repetitivos/temas_repetitivos`
   retorna 200 mas é LISTA, não prova o tema. Regra reforçada no prompt de escrita; falta
   o GATE mecânico que reprove URLs de índice/instáveis (portal.stf `.asp?`, PDFs de sessão).
6. **Acento em todo texto visível — inclusive `official_sources[].name`** (o render mostra
   na seção Fontes; `render.go:180`). Falta gate de presença de acento no auditor.

## Código / módulos NOVOS a criar

7. **Monitor de mudança de norma** (`cmd/monitor-source-changes` + `internal/sourcewatch`):
   detectar quando lei/súmula/tema muda (feeds oficiais) e marcar páginas afetadas para
   reescrita. Hoje é reativo (achamos o Tema 987 por acaso na fiscalização).
8. ~~**Busca pública `/buscar/`** (P5, pendente)~~ **JÁ CONSTRUÍDA E TESTADA** (verificado
   2026-07-29): `internal/search` (bleve v2.6.0 + analyzer PT-BR), `internal/search/manager.go`
   (índice on-demand com cache, filtra por `editorial.IsIndexable`), endpoint em
   `internal/httpserver/httpserver.go:411-417`, render em `internal/render/render.go:42`
   (`SearchResultsPage`, zero `<script>`). Noindex garantido em 3 camadas: `content/pages.json`
   (`index_policy=noindex`), header `X-Robots-Tag: noindex,follow`, meta `robots` inline;
   excluída do sitemap via `editorial.IsIndexable` (`Status=="published" && IndexPolicy=="index"`).
   Testes em `internal/httpserver/httpserver_test.go:39-83` e `internal/search/index_test.go`.
   Benchmark real em `data/ops/search_backend_benchmark.jsonl` (10k registros, bleve
   `query_p95_ms=3`, pior modo bm25 `p95=21ms`). SQLite-FTS5 foi COMPARADO e descartado
   (`docs/goal/RESEARCH_FINDINGS.md:351-353`: stemmer só Porter/inglês, PT exigiria extensão C).
   Restante do gap: nada estrutural — só falta publicação real (P0 zero) para o índice ter
   corpus de páginas publicadas em vez de 0.
9. **API pública** (`cmd/server` + `/api/`): lookup de verbete/lei/súmula em JSON, com
   rate-limit e schema estável. Diferencia como plataforma (e alimenta bots de IA).
10. **IndexNow + sitemap incremental**: descoberta rápida por Googlebot/Bing quando páginas
    novas/atualizadas entram. (IndexNow já autorizado no CLAUDE.md.)

## Dados estruturados / SEO (parcialmente feito hoje)

11. **JSON-LD nas páginas públicas — FEITO hoje** (`render.go` StaticPage
    `includeStructuredData=true`; Article + citações às fontes). **Expandir:** schema
    `Legislation` para verbetes de lei, `FAQPage` para as FAQ, `BreadcrumbList` para a
    trilha /area/slug, `sameAs` para a fonte oficial, `dateModified` real (vigência).
12. **Sinais de frescor/vigência no HTML**: `dateModified`, "verificado em <data>" já
    renderizado — ligar ao monitor de mudança (item 7) para ser verdadeiro, não estático.

## Open source a integrar (MIT/BSD/Apache, self-hosted — conforme contrato)

13. **NER jurídico PT-BR / parser de citação** (ex.: extrair "Lei 8.245 art. 22 II" de
    forma estruturada) para o gate de citação e para os dados estruturados — reduz
    dependência de regex frágil.
14. **LexML / dados abertos** (Planalto, DOU, LexML, DataJud CNJ) como fonte de vigência e
    de novas normas (item 7) — protocolo aberto, sem SaaS.
15. Oráculos PT-BR (LanguageTool, Vale, spaCy/Stanza) já instalados — manter e cobrir 100%
    do corpus no gate de release (hoje alguns rodam em amostra).

## Engenharia / robustez

16. **Escala do auditor e da cadeia a 10k/100k** com benchmark real (não O(n²)); o P3 (1M)
    já tem benchmark, mas o auditor per-intent hardcoded não escala.
17. **Portfólio 6.6k → 10k**: curadoria de ~3.4k intents novos (por problema/documento/
    risco/cenário, anti-template) para fechar o piso P0.
18. **Estabilidade de workflow no harness**: descoberto o bug #9935 (tui:fullscreen +
    tmux congela); mitigado com `tui:default`. Amplificadores a reduzir sem limitar
    trabalho: fan-out de 6 hooks por Bash, lock global único, idle-timeout de 30min.

---

> Este documento é a metade INTERNA. A metade EXTERNA (como os melhores portais jurídicos
> do mundo fazem conteúdo único, E-E-A-T, SEO técnico) vem do `/deep-research` em curso e
> será fundida aqui num roadmap priorizado.
