# SEO_INDEXACAO_2026_DOSSIE — Indexação máxima + citação por IA (Cowork Fable 5, 2026-07-22)

Pesquisa viva (WebSearch/WebFetch) priorizando documentação oficial. FATO = documentado; [SEO] = consenso
de mercado sem doc oficial. Objetivo: lançar 10k+ páginas de wikijuridica.com.br com indexação máxima.

## 1. Spam policies (a única ameaça real ao modelo)
- FATO: scaled content abuse = muitas páginas cujo propósito primário é manipular ranking sem ajudar
  usuários, "no matter how it's created" (IA/humano irrelevante). Proteção = exatamente o que os gates do
  repo exigem: valor único por página, autoria real, fonte citada, intenção atendida.
  https://developers.google.com/search/docs/essentials/spam-policies
- FATO: site reputation abuse (update 19/11/2024) mira conteúdo de TERCEIROS no host — risco marginal
  para portal 100% autoral de um autor OAB.
- FATO: spam update 26/08–22/09/2025 (SpamBrain) reforçou enforcement; 2025-26 sem política nova.

## 2. Ritmo de publicação (valida a estratégia de cohorts ~250)
- FATO: crawl budget só preocupa em 1M+ páginas (ou 10k+ com mudança diária); site novo começa com limite
  conservador que sobe com crawl health (latência estável, sem 5xx/429); QUALIDADE influencia alocação.
  Recomendações oficiais: sitemap com `<lastmod>` correto, suportar 304, 404/410 para removidos, zero
  soft-404. https://developers.google.com/crawling/docs/crawl-budget
- FATO (Mueller): 10k URLs são rastreadas "pretty quickly" (~1 dia); 100k não afeta crawl budget.
- FATO: NÃO existe doc do Google mandando publicar gradualmente; o gargalo real de domínio novo é
  "Discovered – currently not indexed" (avaliação de qualidade pós-crawl).
- [SEO] Cohorts progressivos com validação por lote no Search Console antes do próximo lote é a prática
  prudente para domínio sem histórico — coincide com a promoção por cohorts ≤250 já decidida (W6).

## 3. E-E-A-T YMYL jurídico
- FATO: QRG vigente = setembro/2025 (regras para conteúdo IA + YMYL expandido). Conteúdo assistido por IA
  é aceito SE revisado e atribuído a especialista nomeado com credencial verificável → autor advogado
  identificado (OAB/RJ 227191 via config), revisão declarada, datas visíveis, fontes primárias linkadas —
  tudo em TODA página. Structured data Person/author com credencial: documentado, usar.
- [SEO] Core dez/2025 teria atingido páginas jurídicas <800 palavras sem atribuição de advogado.

## 4. Bots de IA (para ser citado — ajustar crawl_policy.json)
- FATO OpenAI: `OAI-SearchBot/1.4` (busca ChatGPT — PERMITIR), `GPTBot/1.4` (treino), `ChatGPT-User`
  (ação de usuário; robots "may not apply"). IPs: openai.com/searchbot.json.
- FATO Anthropic (doc 04/2026): `ClaudeBot` (treino), `Claude-SearchBot` (busca — PERMITIR),
  `Claude-User`. Honram robots.txt e Crawl-delay. IPs: claude.com/crawling/bots.json.
- FATO Perplexity: `PerplexityBot` (busca — PERMITIR); `Perplexity-User` geralmente IGNORA robots.txt.
- FATO: `Google-Extended` é token de robots (não crawler); bloqueá-lo NÃO tira dos AI Overviews (que usam
  Googlebot normal). Decisão de treino vs. visibilidade Gemini é independente da busca.
- FATO: **llms.txt NÃO é padrão real** — Google não usa (guia oficial de IA atualizado 15/06/2026:
  desnecessário criar arquivos novos); nenhum provedor grande confirmou; adoção ~10%, 97% sem requests.
  NÃO gastar engenharia nisso. O que gera citação: HTML server-side completo e leve + fatos citáveis com
  fonte + search-bots liberados — exatamente a arquitetura já contratada.

## 5. Core updates 2025-26 (contexto)
2025: March core (13-27/03), June core (30/06-17/07), spam (26/08-22/09), December core (11-29/12).
2026: Discover (05-27/02), March core (27/03-08/04) + spam março, May core (21/05-02/06).

## Checklist executável pré-launch (derivado, para o terminal)
1. `content/crawl_policy.json`: garantir allow explícito OAI-SearchBot, Claude-SearchBot, PerplexityBot,
   Bingbot; manter rate-limit em GPTBot/ClaudeBot (treino) conforme política já decidida.
2. Sitemap index com shards ≤40k e `<lastmod>` REAL por página (não data do build) — crawl budget doc.
3. Zero soft-404; 410 para tombstones de supersessão; suportar If-Modified-Since/304 no server Go.
4. E-E-A-T por página: autor+OAB (config), data de revisão visível, fontes primárias como links.
5. Promoção por cohorts ≤250 com validação de indexação por lote no Search Console antes do próximo.
6. Não implementar llms.txt; não bloquear Google-Extended sem decisão explícita do dono (treino Gemini).
