# CRAWL_POLICY_GAPS_20260722 — Auditoria crawl/SEO do código vs dossiê 2026 (Cowork Fable 5)

Auditados por inteiro: `content/crawl_policy.json` (466 l), `internal/sitemap/sitemap.go`,
`internal/httpserver/httpserver.go`, `internal/render/render.go`, `internal/structureddata/`.

## CONFORME (nada a fazer)

- Search-bots de IA já liberados: OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User,
  PerplexityBot, Perplexity-User = `unlimited`; GPTBot/ClaudeBot = training_tier_standard;
  CCBot = strict; Google-Extended allow (decisão de treino preservada ao dono).
- `<lastmod>` REAL por página: `sitemap.go:337-341` usa `page.ReviewedAt`→`PublicationDate`
  (dado, não build). ✓ doc oficial de crawl budget.
- E-E-A-T completo: byline autor+OAB de config (`render.go:396-414`, autenticado por
  `authorMatchesConfiguredIdentity`), data de revisão visível, JSON-LD Article+Person com @id
  estável (`structured_data.go:452-490,834-839`).

## GAPS (fila executável para o terminal)

1. **`meta-externalagent` AUSENTE** de bot_registry/rules/access_rules (0 ocorrências no repo).
   Fix: adicionar em `content/crawl_policy.json` + `internal/crawl/crawl.go:124-144`
   (DefaultBotRegistry) como training_tier_standard; avaliar `meta-externalfetcher` (user-triggered).
2. **Shard do sitemap 45k > 40k recomendado**: `DefaultMaxURLsPerShard=45000`
   (`sitemap.go:18`) → reduzir para 40000 (margem sob o teto 50k do protocolo).
3. **SEM 410 para tombstone de URL**: zero `StatusGone` no repo; página supersedida cairia em 404.
   Fix: branch `http.StatusGone` para status "superseded" antes do RenderPath
   (`httpserver.go:387-391`). Relevante p/ crawl budget e supersessão DEC-020 em produção.
4. **SEM If-Modified-Since/304**: nenhum suporte condicional em `httpserver.go`/`ondemand`.
   Fix: emitir `Last-Modified` (ReviewedAt) e tratar If-Modified-Since em writeBody/writeBytes
   (`httpserver.go:431-443`). Doc oficial recomenda explicitamente para crawl budget.
5. Nota: rate-limit dos training bots é DECLARATIVO (registry validado por checks; robots.txt não
   emite Crawl-delay e o server não tem limiter). Decidir: implementar Crawl-delay/middleware OU
   documentar como política declarativa. Perplexity-User ignora robots de qualquer forma (fato
   documentado) — sem ação possível além de já estar em unlimited.
