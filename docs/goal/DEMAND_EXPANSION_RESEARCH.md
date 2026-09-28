# Pesquisa de demanda e expansão do portfolio rumo a 10k

> Artefato durável de pesquisa (claude-infra). Persiste o contexto para não se
> perder entre sessões. O relatório do deep-research (web, metadata-only) é
> anexado ao final quando o workflow `wf_79cc817d-ea1` conclui.

## Estado do funil P0 (medido 2026-07-15)

- Estoque v2_pages: **~6.408 páginas ativas** (6.487 intents escritos; 39 needs_source_research; 57 tombstones).
- Portfolio_v2 (demanda planejada): **6.624 intents**, essencialmente todos escritos **exceto telecom_energia** (137 faltantes, em escrita agora — lotes 04–14).
- Déficit real até 10k: **~3.376 intents NOVOS** além do portfolio atual → exige EXPANSÃO, não só escrita do existente.
- Público: **0 páginas** (`published_manifest`=0); cadeia de release sob lock do v2ingest (codex-eng). Gargalo P0 = promoção transacional (não a contagem).

## Mecanismo sancionado de expansão (6.624 → 10.000)

- **Portfolio-Wave3** é o único mecanismo transacional que alimenta `portfolio_v2` diretamente:
  - `scripts/workflows/portfolio-wave3.js` (curadoria automática por área, propõe intents estruturados respeitando caps).
  - `./tools/generate-portfolio-wave3 <candidates.json>` valida (anti-dup similaridade <0.70, caps por área) e materializa atomicamente em `data/editorial/portfolio_v2/<area>.jsonl` via `v2ingest.ApplyTransaction`.
  - Contrato do intent novo: `intent_id` kebab único, `page_type`, `family` w3-*, `long_tail_query` de demanda real, `working_title` 20–65 chars, `reader_problem`, `lane` comercial|informativa, `source_hints` ≥1, `needs_source_research=true`, `distinct_because`.
  - Depois: `scripts/workflows/writing-mass-full.js` escreve o conteúdo dos intents Wave3.
- Capacidade confirmada (`internal/portfoliowave3/model.go`): caps totais **12.150**; headroom **~5.526 > 3.376** necessário (margem 63%). Maiores absorvedores: glossário (+1.068), leis (+153).
- **Intent ≠ Página**: Wave3 grava intent bloqueado (sem conteúdo, sem render, fora do sitemap). Página pública exige escrita + gates + release transacional.
- Laboratório paralelo (NÃO alimenta portfolio_v2 diretamente): `demand_expansion_opportunities` (18.228 metadata-only) → `authorial_mass_candidate_selection` (10.000) → `authorial_mass_drafts` (~590 com conteúdo bloqueado). Falta conversor validado para virar intent de portfolio.

## Contrato de conteúdo (uma página nova deve passar)

- Estrutura: `intent_id`, title 20–65 PT-BR, meta 70–160, h1≠title, opening, sections 2–4 por page_type, faq opcional, `word_count` ±10% (fórmula `bodyWordCount`).
- Fontes: **≥2** oficiais, hosts `*.gov.br/*.jus.br/*.leg.br/*.mp.br` (+ 8 hosts exatos), HTTPS, **paths específicos** (não homepage), `anchor_claim` verificável. `verified_at/http_status` só pela ferramenta `audit-v2-source-provenance` — **nunca o redator** (violação de contrato pega em fiscalização).
- Anti-molde: nenhuma frase de ≥12 palavras repetida (intra-lote + global `--global`), headings únicos/informativos, sem fragmentos terminais.
- Ética OAB: informativo, sem promessa de resultado, sem captação; jornada 100% digital é modo de atendimento, não promessa. BPC/LOAS/gratuidade → lane informativa sem CTA comercial.
- Auto-auditoria: `python3 tools/audit_v2_pages.py <file>` e `--global`; `ingest-v2-stock --prepare-only`.

## Restrição de demanda (sem quebrar contrato)

- Coleta externa de demanda é **metadata-only** (proibido scraping de conteúdo, cópia, paráfrase mecânica).
- A pesquisa produz o **mapa de intenção/tema** (o que humanos buscam, valor comercial, fonte oficial provável) — nunca texto público.
- O conteúdo da página é escrito do zero a partir da **fonte oficial específica**, separada da pesquisa de demanda.

## Fila em execução (2026-07-15)

- Escrita telecom_energia 04–14 (137 págs) — workflow `wf_fc813a4f-e89`.
- Deep-research de demanda alta-intenção — workflow `wf_79cc817d-ea1` (relatório abaixo quando concluir).
- Gate telecom03 exige âncoras ANATEL específicas (URLs canônicas capturadas em `internal/v2ingest/current_legal_facts_telecom_energia03.go`: `.../consumidor/quer-reclamar/reclamacao`, `.../reclamacao-denuncia-ou-outras-manifestacoes`, MOP31, PPP-guide, Accord389, franquia pending/caution).

---

## Relatório deep-research de demanda (wf_79cc817d-ea1, 2026-07-15)

_Fan-out de 102 agentes com verificação adversarial. Métricas confiáveis = contagens litigiosas/vítimas (STJ/STF, Predictus, Turivius, Datafolha/FBSP), não volume de busca de blogs SEO (não confiável — 2 refutados)._


### Sumário

Para uma advocacia 100% digital brasileira em 2025-2026, a demanda jurídica de MAIOR volume e MAIOR intenção comercial não está nos nichos "de prestígio" vendidos a advogados (LGPD/tributário/ESG), e sim no litígio de consumo e fraude digital — temas de dor real, contratação paga (banco/plataforma/seguradora indeniza), fluxo documental replicável (extrato + B.O. + jurisprudência-modelo) e triagem 100% remota. As quatro tendências emergentes mais fortes, medidas por dados litigiosos reais (não por keyword-permutação): (1) golpes digitais / golpe do Pix — judicialização +1.195% em ~4 anos, ~24 milhões de vítimas/ano e responsabilidade objetiva do banco (Súmula 479 + CDC art. 14); (2) ações contra casas de apostas (bets) — 10.000+ processos, apostador vence 59,2%; (3) superendividamento (Lei 14.181/2021), apontado como o grande tema de 2026, impulsionado por bets e crédito predatório; (4) planos de saúde — negativa de cobertura e reajuste abusivo, ações +83% em 10 anos no TJ-SP, muitas com liminar emergencial. Tributário e LGPD/direito-digital são de alto valor mas predominantemente B2B/corporativos, menos aderentes ao modelo individual por WhatsApp; imobiliário de nicho (usucapião extrajudicial) tem alta intenção e representação obrigatória por lei. Alerta metodológico: os números de volume de BUSCA que circulam em blogs de SEO jurídico se mostraram não confiáveis (dois foram refutados) — as métricas confiáveis aqui são contagens litigiosas e de vítimas de estudos como Predictus, Turivius, Datafolha/FBSP, Geps/USP e relatórios oficiais STJ/STF.


### Achados verificados (9)


**1. [high]** Golpes digitais / fraude eletrônica é a tendência emergente de maior crescimento e alta intenção comercial (áreas: bancário, consumidor, digital). A judicialização cresceu +1.195% em pouco mais de 4 anos (fev/2022 a mar/2026), de 154 para 1.994 decisões mensais em tribunais estaduais, com custo médio por ação condenada de R$20 mil a R$50 mil pago pela plataforma/instituição. A violação de dados que alimenta os golpes já gera 'uma onda de processos com pedidos de indenização'. Intenção humana concreta: 'fui vítima de golpe, quero meu dinheiro de volta / indenização'. Fonte oficial provável: CDC art. 14, Súmula 479 STJ, Anuário do Fórum Brasileiro de Segurança Pública.

   - Voto adversarial: 3-0 nas contagens/tendência; 2-1 no ticket R$20k-50k

   - Fontes: https://www.conjur.com.br/2025-dez-24/superendividamento-e-seguranca-de-dados-devem-pautar-direito-do-consumidor-em-2026/; https://www.noticiasdiarias.com.br/2026/07/13/judicializacao-de-golpes-digitais-registra-aumento-de-1-195-em-pouco-mais-de-quatro-anos/


**2. [high]** Golpe do Pix / boleto falso é demanda de MASSA com base jurídica sólida de contratação paga (área: bancário/consumidor). Estimativa de 24 milhões de vítimas entre jul/2024 e jun/2025, prejuízo agregado ~R$29 bilhões, perda média R$1.198/vítima. O banco responde OBJETIVAMENTE (CDC art. 14 + Súmula 479 STJ) quando houve falha de segurança (não bloqueio de transação atípica) ou conta-laranja aberta sem KYC adequado — o que transforma o ressarcimento em caso viável, não causa perdida. Entrega altamente replicável (fluxo documental + modelos de petição). Ticket típico ~R$2.000-8.000.

   - Voto adversarial: 3-0 (mescla de 3 claims)

   - Fontes: https://joaocoelho.adv.br/golpe-do-pix/; https://blog.landingpageadv.com.br/2026/01/22/nichos-de-sustentacao-advocacia-2026/


**3. [high]** Ações de apostadores contra casas de apostas (bets) são tendência emergente explosiva de alta intenção comercial (área: consumidor/digital). 10.000+ processos; 5.488 novos em 2025 e 4.037 só em jan-mai/2026. Apostador vence total (589) ou parcialmente (1.446) em 59,2% dos 3.438 casos julgados. Intenções PROBLEMÁTICAS concretas (não permutação de palavra-chave): conta bloqueada (636), alteração unilateral de regras (629), cláusula contratual abusiva (541), golpe de terceiro via Pix (518), bloqueio de saque (429), falha no dever de cuidado (353) — queixa recorrente 'o dinheiro do prêmio não sai'. Fonte oficial provável: Lei das Bets (Lei 14.790/2023), CDC, regulamentação SPA/MF; STF ADPFs 1005/1006/1097.

   - Voto adversarial: 3-0 (mescla de 3 claims)

   - Fontes: https://www.terra.com.br/noticias/brasil/a-explosao-de-processos-de-brasileiros-contra-bets-para-receber-premio-dinheiro-nao-sai,2663cadeb7efdc1b5c3a837e134b8230pgqi3unc.html


**4. [high]** Superendividamento é apontado como O GRANDE tema do direito do consumidor em 2026 (área: consumidor/bancário), impulsionado especificamente pelo avanço das casas de aposta e da concessão predatória de crédito. Efetivar a Lei do Superendividamento (Lei 14.181/2021) é o desafio central — sinal de demanda emergente por repactuação/renegociação de dívidas. Atenção ao gate paid-intent: renegociação de dívida de consumidor com renda é lane paga, mas há sobreposição com vulnerabilidade/gratuidade que exige triagem.

   - Voto adversarial: 3-0

   - Fontes: https://www.conjur.com.br/2025-dez-24/superendividamento-e-seguranca-de-dados-devem-pautar-direito-do-consumidor-em-2026/


**5. [high]** Litígios contra planos de saúde são nicho de alta demanda e ALTA intenção de contratação particular (área: consumidor/saúde suplementar) — o cliente já paga o plano (demografia pagante, não SUS/gratuidade), tem urgência e baixa tolerância a erro. Ações em 2ª instância no TJ-SP cresceram 83% em 10 anos (11.347 em 2015 → 20.771 em 2025). Problemas concretos dominantes: negativa/recusa de cobertura (30,4%) e reajuste abusivo (16,6%); também rescisão unilateral e redução de rede. Muitos casos exigem liminar emergencial (deferida em 24-48h). Ticket típico R$3.000-12.000. Fonte oficial provável: Lei 9.656/98, CDC, Rol ANS, STJ (cobertura fora do Rol com indicação médica), STF ADI 7.265.

   - Voto adversarial: 3-0 (mescla de 4 claims)

   - Fontes: https://jornaldebrasilia.com.br/noticias/economia/acoes-judiciais-contra-planos-de-saude-crescem-83-em-dez-anos-em-sao-paulo/; https://oab.estrategia.com/portal/areas-de-atuacao-na-advocacia-com-alta-demanda-e-pouca-concorrencia-em-2026/; https://blog.landingpageadv.com.br/2026/01/22/nichos-de-sustentacao-advocacia-2026/


**6. [high]** Direito tributário é apontado como o epicentro da litigiosidade em 2026 (área: empresarial/tributário) e a Reforma Tributária de 2025 pode TRIPLICAR a carga processual tributária atual (STJ projeta novas ações tributárias subindo de 28.764 para 86.000+). Forte demanda emergente em contencioso fiscal. RESSALVA de aderência: é lane predominantemente B2B/corporativa, menos aderente ao modelo individual por WhatsApp que o consulente-consumidor.

   - Voto adversarial: 3-0

   - Fontes: https://turivius.com/portal/areas-direito-maior-litigiosidade-2026/; https://www.stj.jus.br


**7. [medium]** Direito digital / proteção de dados (LGPD) é apontado como nicho de alta demanda e baixa concorrência QUALIFICADA (compliance, gestão de incidentes, defesa administrativa na ANPD), porque poucos advogados dominam o tema de forma técnica e aplicada (área: digital/LGPD). RESSALVA forte: é lane B2B/corporativa (DPO, empresa, ANPD), não o modelo consumidor-individual por WhatsApp que a pergunta mira.

   - Voto adversarial: 2-1

   - Fontes: https://oab.estrategia.com/portal/areas-de-atuacao-na-advocacia-com-alta-demanda-e-pouca-concorrencia-em-2026/


**8. [high]** Direito imobiliário de nicho (usucapião extrajudicial, regularização fundiária, distratos, atuação preventiva em contratos) é área de alta demanda e alta intenção comercial (área: imobiliário) — demandas de alto valor patrimonial com 'pouca disposição do cliente para testar advogado barato'. Usucapião extrajudicial exige advogado POR LEI (art. 216-A da Lei de Registros Públicos, Lei 14.382/2022), o que garante representação paga.

   - Voto adversarial: 3-0

   - Fontes: https://oab.estrategia.com/portal/areas-de-atuacao-na-advocacia-com-alta-demanda-e-pouca-concorrencia-em-2026/


**9. [high]** NICHO SUBATENDIDO POR CONTEÚDO: as listas de 'áreas jurídicas lucrativas/de crescimento em 2026' que circulam para advogados focam quase exclusivamente em nichos B2B/regulatórios (LGPD, tributário, ambiental/ESG, propriedade intelectual, imobiliário) e OMITEM completamente as demandas de consumo de alta intenção (golpes digitais, bets, superendividamento, planos de saúde, revisão de benefícios/INSS). Apesar do enorme volume litigioso real desses temas de consumo, eles são relativamente subatendidos pelo conteúdo/'guias de nicho' — sinalizando oportunidade de captação por SEO informativo.

   - Voto adversarial: 3-0

   - Fontes: https://lawgieai.com/artigos/qual-nicho-juridico-atuar-e-lucrar-em-2026-confira-aqui


---

## Plano de execução Wave3 (próxima fase — expansão 6579→10k)

**Estado (2026-07-15 pós-telecom):** estoque ativo **6579** páginas, déficit **3421**, needs_source_research **5**. Portfolio existente essencialmente escrito (telecom fechada, +~135 págs).

**Mecanismo:** `tools/generate-portfolio-wave3 -input <candidatos.json>` (`-prepare-only` valida sem instalar) → valida anti-dup (similaridade <0.70) + caps + materializa transacional em `portfolio_v2` → `writing-mass-full.js` escreve.

**Schema do candidato (estrito, `internal/portfoliowave3/demand_evidence.go`):** exige DEMAND-EVIDENCE, não curadoria narrativa — campos: `source_signal_id`, `unique_intent_id`, `observed_query`, `long_tail_query`, `human_problem`, `source_surface`, `source_url` + `source_url_hash`, `demand_intent`, `official_source_urls`, `official_source_required`, `source_specificity_required`, `intent_id`, `family` (w3-*). O investigador apontou gap: o modo de curadoria local aceita sem observation_ids/superfícies, mas a via correta quer evidência de demanda com hash de fonte.

**Headroom por área de maior intenção comercial (da pesquisa):**
- consumidor 288/700 (**+412**) — bets, superendividamento, golpes de consumo
- bancario 316/700 (**+384**) — golpe do Pix, responsabilidade objetiva do banco
- glossario 702/1400 (**+698**) — verbetes (ForceInformative/ForceVerbete)
- saude 207/350 (**+143**) — negativa de cobertura, reajuste
- previdenciario 483/650 (**+167**) — revisão de benefícios
- Total nessas 5 ≈ 1.804; headroom global ≈ 5.526 > 3.421 necessário.

**Mapeamento demanda→candidato (do relatório verificado):** priorizar os temas de maior volume×intenção comercial que casam com jornada 100% digital: (1) golpe do Pix/boleto/conta-laranja (bancario, CDC 14 + Súmula 479 STJ + REsp 2.222.059/2.229.519/2.124.423); (2) bets — conta bloqueada, saque negado, regra alterada, cláusula abusiva (consumidor, Lei 14.790/2023 + SPA/MF + STF ADPFs 1005/1006/1097); (3) superendividamento — repactuação, plano de pagamento, mínimo existencial (consumidor/bancario, Lei 14.181/2021); (4) planos de saúde — negativa de cobertura por rol, reajuste por faixa, liminar (saude, Lei 9.656/1998 + ANS + STJ). Cada intent com fonte oficial ESPECÍFICA (não homepage) e lane comercial (sinal paid-intent no corpo) exceto gratuidade.

**Próxima ação executável:** workflow de curadoria que produz candidatos Wave3 válidos por tema (schema estrito acima, anti-dup contra os 6.624 existentes, fonte oficial específica), valida com `generate-portfolio-wave3 -prepare-only`, materializa em lote, e alimenta `writing-mass-full.js`. Piloto por tema (fraude digital/Pix) antes de escalar aos 3.421.

---

## Snapshots Wave3 bloqueados (2026-07-15) — revisão obrigatória antes de materializar

Os seis arquivos `data/ops/wave3_candidates_*.json` preservam 108 ideias curadas como insumo interno, não como candidatos prontos. A revisão cruzada atual encontrou 108 `opportunity_id` únicos e 288 observações referenciadas, mas todas as 108 oportunidades estão em `demand_confirmation_state=unobserved_gap`, com `authenticated_observation_count=0` e `release_blocker=true`. As superfícies reivindicadas colapsam majoritariamente em autosuggest; Google News não é demand-bearing e a observação isolada de Reddit não prova duas famílias independentes.

Os snapshots também exigem recuração editorial e jurídica antes de qualquer `--prepare-only`: remover funil de contratação/recortes permutacionais; revisar premissas de prazo, fontes e artigos; resolver duplicidades; e obter fontes oficiais específicas. Os 101 valores incorretos `needs_source_research=false` foram corrigidos para `true`, coerentes com o materializador fail-closed. O estoque permanece preservado e não é publicação, fila executável nem autorização para escrita em `portfolio_v2`.

BLOQUEADOR: `internal/portfoliowave3/demand_evidence.go` exige `response_receipt` autenticado por observação e independência de superfície. É proibido fabricar recibo, reinterpretar autosuggest como família independente ou afrouxar o gate. A próxima ação é recurar os elos apontados e coletar evidência demand-bearing permitida com receipts duráveis; só depois executar uma validação `--prepare-only` única e corrigir o que ainda reprovar.
