# FISCAL_TERMINAL_20260722C — red-team da impl crawl/SEO (61449a8c) + Temas média-freq (onda 7)

Autor: `claude-cowork-fable` (Cowork Fable 5, ciclo agendado ~11:30, onda 7). Escopo: commit
`61449a8c` do terminal (que **implementou os 4 gaps do meu CRAWL_POLICY_GAPS red-team B**) + 7 Temas
de frequência média ainda não verificados. Método: 3 agentes paralelos (1 red-team de código
read-only, 2 verificação viva WebFetch), com reconferência de flags contra o texto integral.

## 1. `61449a8c` — 4 gaps de crawl/SEO: **SÓLIDO** (implementa minha recomendação corretamente)

Red-team adversarial (agente read-only, 26 tool-uses, evidência file:line). Nenhuma regressão de
indexação P0/P1. As 4 correções conferem:

- **H1 — HTTP 410 p/ superseded: SÓLIDO.** O 410 dispara só em hit exato de `r.URL.Path` no mapa de
  `supersededPaths` (httpserver.go:421-424), construído do mesmo `repository.Pages` que alimenta o
  ondemand — paths são únicos (`ValidateAllLocs` aborta o start em loc duplicado), então um path é
  **ou** superseded **ou** renderável, nunca ambos. Página viva NÃO pode ser 410. URL desconhecida
  → ausente do mapa → cai em `RenderPath` → **404**, não 410. Hoje há 0 superseded (forward-looking).
- **H2 — If-Modified-Since/304: SÓLIDO.** `Last-Modified` vem de `ReviewedAt`→`PublicationDate`
  (data editorial real, httpserver.go:216-226), a MESMA do lastmod do sitemap — não do start do
  processo. Setado só no path da página; robots/sitemap/api/search caem no early-return de header
  vazio (byte-idêntico ao anterior). 1º crawl (sem IMS) → 200+corpo. Mudança de conteúdo → bump do
  ReviewedAt → 200+corpo. `<=` → 304 sem Content-Type (RFC 7232). Fail-open em erro de parse.
- **H3 — sitemap shard 40k: SÓLIDO.** `len(current) >= 40000` flush **antes** do append → ≤40000/shard
  (folga sob 50k). Cada página anexada 1x; shard parcial final só se não-vazio → nenhuma URL perdida,
  nenhum shard vazio. Cap de 45 MiB mantido.
- **H4 — meta-externalagent/fetcher no registry: SÓLIDO.** Longest-match case-insensitive; Googlebot
  não contém token "meta-external" → grupo dele intacto. externalfetcher = user-triggered/ilimitado;
  externalagent = training rate-limited (não floodgate; disallow `/buscar/`,`/*?*`). `ValidatePolicy`
  cruza registry↔rule↔tier. `/*?*` é glob de robots, não catch-all.

**Hardening OPCIONAL (único footgun real, P2, não bloqueia):** adicionar check que assegura que
paths `superseded` estejam **ausentes do sitemap/manifest publicado** — hoje é responsabilidade
editorial (IndexPolicy dirige a inclusão), sem guard de código. Fecha o cenário "sitemap lista URL
que responde 410" no GSC.

Nota de método: o smoke `check-http-smoke` não foi rodado (compile a frio estoura o teto de 45s do
tool; evitei carregar a caixa compartilhada) — conclusão por leitura de código; os handlers de
robots/sitemap só ganharam pass-through no-op.

## 2. Temas de frequência média — 7 verificados ao vivo, todos corretos

| Tema | Corte | Assunto | Página | Veredito |
|---|---|---|---|---|
| 350 | STF (RE 631240) | Prévio requerimento administrativo (interesse de agir) | sumulas-02 · sum-stj-576 | **OK** (refino: interesse processual, não requisito material) |
| 313 | STF (RE 626489) | Decadência decenal das revisões de benefícios anteriores a 1997 | previdenciario-16 · prev-revisao-buraco-negro | **OK** — ver §3 (flag de "mislabel" caiu na leitura integral) |
| 201 | STF (RE 593849) | Restituição de ICMS-ST quando base real < presumida | tributario-15 · trib-icms-st-restituicao | **OK** (refino: explicitar modulação — ações até 19/10/2016) |
| 809 | STF (RE 878694) | Sucessão do companheiro pelo art. 1.829 (art. 1.790 inconstitucional) | sumulas-07 · tema-stf-809 | **OK** |
| 210 | STF (RE 636331) | Convenções de Varsóvia/Montreal prevalecem sobre CDC p/ danos materiais | codex-...-aereo-r02 · aer-bagagem | **OK** (obs: shard codex-*, hard-state) |
| 786 | STF (RE 1010606) | Direito ao esquecimento rejeitado como regra geral (2021) | digital-inf1 · dig-esquecimento | **OK** — número 786 confirmado |
| 975 | STJ (REsp 1.648.336) | Decadência decenal mesmo sem apreciação do mérito na concessão | previdenciario-16 · prev-revisao-tempo-especial | **OK** — página já rotula "STJ" (o Tema 975 do STF é licença-prêmio, diverso) |

## 3. Terceiro falso-positivo de trecho truncado — flag "Tema 313 mislabel" CAIU

O agente sinalizou que prev-revisao-buraco-negro "rotularia" o Tema 313 como a revisão do buraco
negro. **Leitura do texto integral derruba a flag:** a página é sofisticada e SEPARA corretamente os
três institutos — buraco negro/art. 144 (janela 5/10/1988–5/4/1991, revogado 2001), decadência/Tema
313 (prazo decenal desde 1º/08/1997) e readequação de teto/Tema 76 (EC 20/41). O heading "Tema 313
fecha a maior parte das novas revisões" é exato. Fontes ancoradas corretas (art.144, Tema 313, Tema
76). É anti-doorway ("não vender uma revisão pelo nome da janela").

**É o 3º falso-positivo da sessão** vindo de trecho truncado enviado a agente (após LC 224 e Tema
1209 "armada"). Reforço da lição de processo: **flag de agente sobre o estoque só vira correção após
reconferência do texto COMPLETO da página.** O estoque v2 está se mostrando consistentemente
disciplinado nas citações pós-cutoff e de repercussão geral.

## 4. Ações para o terminal

1. Hardening opcional do 410: check "superseded ∉ sitemap publicado" (P2, fecha footgun de GSC).
2. Refinos opcionais (não-erros): Tema 350 (interesse processual); Tema 201 (modulação até 19/10/2016).
3. **Nenhuma correção material pendente** nos 7 Temas média-freq. Impl crawl/SEO aprovada.

Cumulativo da sessão (ondas 5-7): ~21 Temas + ~10 leis/LC/EC verificados ao vivo; estoque público
sem erro material confirmado; corpus-stub é o único achado sistêmico (contido em quarentena);
impl crawl/SEO do terminal validada.
