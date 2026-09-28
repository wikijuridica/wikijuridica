# P0 Goal - Authorial Mass Promotion Candidate Lane

Este documento registra o prompt operacional do ciclo P0 para retomada segura do `/goal`.
Ele nao substitui `AGENTS.md`, `GOAL.md` ou `CHECKPOINT.md`; em conflito, vale a regra
mais restritiva para qualidade juridica, fonte, publicacao, indexacao e continuidade.

## Objetivo

Implementar uma macrocamada permanente e bloqueada para os melhores candidatos autorais
dos 10.000 conteudos internos, conectando anti-template global, fonte oficial especifica,
demanda externa, OAB/CTA, SEO/crawl e release gates, sem publicar nada indevido.

## Baseline a Revalidar Antes de Editar

- `published_manifest=0`; deficit publico juridico atual: 10.000.
- `authorial_mass_candidate_selection=10000`; `authorial_mass_drafts=300`;
  `authorial_mass_content_expansion=9700`; `authorial_mass_publication_readiness=10000`.
- 674 registros passam paid-intent sem issue, contexto sem issue e search appearance sem issue,
  mas continuam bloqueados por anti-template, fonte, OAB, HTML/Googlebot, manifest,
  sitemap/canonical/robots e release gate.
- Auditoria global atual: 10.000 conteudos, 49.995.000 pares esperados,
  1.712.308 pares candidatos comparados, 651 high-risk e max similarity 0.683374.
- `authorial_mass_source_profiles=27`; 22 perfis ainda tem gap de fonte:
  lei/artigo a auditar, pagina oficial contextual a revisar ou fonte oficial ampla demais.
- Demanda externa atual: 1.519 observacoes, 326 oportunidades observadas de 12.960,
  22 seeds, superficies Bing, Google, social trend e public questions.

## Implementacao Obrigatoria

1. Criar testes primeiro para uma camada sugerida como
   `authorial_mass_promotion_candidate_lane`, seguindo padrao local de pacote, CLI,
   wrappers `tools/`, storage contract e registry de checks.
2. Materializar `data/editorial/authorial_mass_promotion_candidate_lane.jsonl` com no minimo
   os 674 candidatos mais proximos de promocao, preservando identidade, seed, area,
   cenario, contexto, evidence de demanda, source gap, similarity blockers, OAB/CTA,
   status de servico digital, risco de promessa, next actions e flags publicas falsas.
3. Fortalecer anti-template em escala com indice explicavel de pares candidatos
   inspirado em simhash/minhash/LSH/bitmap. Manter stdlib se for suficiente; adicionar
   dependencia Go open source permissiva somente com licenca verificada, teste e beneficio
   tecnico mensuravel.
4. Cruzar fonte oficial nos 674 por seed, priorizando gaps vivos. Pesquisa oficial deve ser
   metadata-only, sem scraping, sem copia de texto oficial e sem liberar fonte final por atalho.
5. Reforcar regra OAB/CTA: servico juridico 100% online, sem sair de casa, celular ou
   computador e realidade operacional permitida; promessa proibida e resultado, prazo,
   exito, decisao favoravel, concessao, ressarcimento certo, valores, desconto, gratuidade
   ou captacao indevida.
6. Regenerar somente a cadeia derivada proporcional quando os dados mudarem. Nao tocar
   `public/`, `content/pages.json`, `published_manifest`, `.release-staging`,
   `public/sitemap.xml` ou `public/sitemaps` antes de gate publico completo.
7. Usar subagentes quando disponiveis para auditoria de fonte/OAB, algoritmo open source
   e gates SEO/release, registrando tudo em `.agents/agent_context_ledger.jsonl`.

## Validacao Minima

- Testes Go focados nos novos pacotes, CLI e contratos.
- `./tools/check-authorial-mass-promotion-candidate-lane`.
- Checks autorais relacionados: global similarity, contextual compatibility, source profiles,
  publication readiness, legal reviews, release evidence, release transaction,
  manifest transaction e controlled promotion.
- `./tools/check-ops-check-performance-ledger` e `./tools/check-agent-context-ledger`
  quando subagentes forem usados.
- `git diff --check`.
- Diff publico critico vazio para `public/`, `content/pages.json`,
  `data/editorial/published_manifest.jsonl`, `.release-staging`, `public/sitemap.xml`
  e `public/sitemaps`.

## Criterio de Sucesso do Ciclo

Camada permanente bloqueada cobrindo os candidatos proximos de promocao com anti-template,
fonte, OAB/CTA, demanda e release gates integrados em dados reais; nenhuma publicacao real
indevida; commit de rastreabilidade; continuidade imediata do `/goal`.
