# Varredura: classificador de severidade de publicacao (/opt/wiki) — 2026-09-15

SOMENTE LEITURA. Nada foi editado no repositorio.

## Resposta direta a pergunta do chefe

**Quantas paginas estao paradas hoje por motivo de classe JUIZO no classificador
de severidade: ZERO.**

Medido em `data/editorial/v2_publication_severity.jsonl` (11.206 linhas,
regravado 2026-09-15 12:24):

| severidade | paginas |
|---|---|
| limpo | 769 |
| medio (publica) | 10.337 |
| critico (nao publica) | 100 |
| **publish=true** | **11.106** |

As 100 criticas tem UM unico motivo, e ele nao e juizo nem defeito:
`intencao_pulada_deliberadamente` (100 ocorrencias, 100% das criticas).
Sao tombstones — registros `skipped: true`, sem corpo por construcao, que
registram uma decisao editorial de NAO redigir aquela intencao. Nao ha pagina
presa ali.

`publish=true` = 11.106 — exatamente o numero de paginas publicas do portal.
O classificador nao esta segurando nada.

**Cadeia fechada ate o ar (medido):** `published_manifest.jsonl` tem 11.106
linhas e 11.106 `unique_intent_id` distintos. Interseccao com o censo:
publish=true sem linha no manifesto = **0**; no manifesto e nao-publish = **0**.
Tudo que o censo aprova esta no ar, e nada no ar escapou do censo. O "zero"
vale ponta a ponta, nao so na camada do classificador.

**O publicador ja PULA gate estatistico por desenho**
(cmd/publish-v2-direct/main.go:3957, campo `skipped_statistical_gates`):
`batch_global_similarity:refutado_por_tools/measure-v2-uniqueness` e
`anti_template_review_required:refutado_por_medicao_de_molde`. E exatamente o
mecanismo do CLAUDE.md secao 5 — gate estatistico refutado por medicao e pulado
com a evidencia gravada. O precedente para calibrar molde ja existe e ja roda.

**O gate de near-dup nao esta no caminho de publicacao.** `v2bodyneardup`
(5-gramas, digitos PRESERVADOS, limiar 0,70) so e chamado por
`cmd/check-v2-body-near-duplicates`, e o unico executor dele e
`tools/run-qualidade-diaria:679` (bancada diaria). `tools/deploy-publico` e
`.githooks/pre-commit` nao o mencionam (grep: zero ocorrencias). Ou seja: o
gerador de acordao aplica uma regua de 3-gramas com digitos neutralizados,
MAIS severa que um gate de 5-gramas que sequer decide publicacao.

## Recomputacao independente (nao confiei no artefato)

Executei os detectores vivos do proprio gerador sobre os 11.225 registros de
`data/editorial/v2_pages/*.jsonl`, hoje:

```
registros v2_pages: 11225 | intents distintos: 11206 | intents com >1 registro: 19
  skipped_tombstone     119   (119 - 19 suprimidos com irma real = 100 criticas) OK
  sem_corpo               0
  falta_title/meta/h1/opening  0
  corpo_abaixo_250        0
  encoding (qualquer)     0
  promessa_oab            0
  corpo_250_400        1695   (medio, publica)
```

Zero defeito FATO no estoque inteiro. O censo do disco esta fresco e correto.

## Onde a fabrica trava de verdade

Nao e aqui. O censo so classifica o que JA esta em `v2_pages`. Pagina que morre
no gerador (ex.: `molde_acima_do_limiar` 532 de 1.260 no gerador de acordao)
nunca ganha linha no censo — some antes de existir. O classificador e inocente;
o estrangulamento e a montagem.

## Cinco detectores MORTOS (medidos, nao inferidos)

1. `campo_obrigatorio_ausente` (CRITICO) — tools/generate-v2-publication-severity:747
   `"missing_required_field" in queue_reasons` e membership EXATA em lista cujos
   elementos sao `missing_required_field:title`. Medido: exata=0, prefixo=100.
   Impacto hoje 0 (os 100 sao os mesmos tombstones ja criticos).
2. `promessa_oab:sinalizada_pelo_pipeline` (CRITICO) — :716
   Le `promise_risk_detected` em authorial_mass_publication_readiness.jsonl.
   Medido: a chave nao existe em NENHUMA das 7.959 linhas. Guarda de etica OAB
   morta — e esta e a classe que o dono disse que nao se afrouxa.
3. `antitemplate_review_required_refutado_por_medicao` (medio) — :761
   Compara com `"review_required"`; os valores reais sao
   `page_antitemplate_review_required` (2.031) e `page_antitemplate_ready` (5.941).
   Nunca casa. 2.031 paginas sem rotulo.
4. `frase_repetida_entre_paginas` (medio) — :768
   Mesma membership exata. Medido: exata=0, prefixo=1.259. As 1.259 publicam.
5. `official_sources_insufficient` (metade de :757) — mascarado por `len(sources)<2`,
   que ainda funciona (2.323 medios). Medido: exata=0, prefixo=2.461.

## Vereditos de auditoria

- `reprovada_em_auditoria_humana` (:739) e `veredito_conflitante` (:744):
  **0 ocorrencias hoje**. Ja foram desarmados em 2026-08-07 pela exigencia de
  justificativa (`justified_verdicts`, :599-600).
- Dado real: 133 intents com `human_verdict: [REPROVADA]` e 2 com
  `[APROVADA, REPROVADA]`. Viraram 131 `reprovada_por_agente_sem_justificativa`
  (medio, publica) + 4 `reprovacao_superada_por_reparo_verificado`.
- Quem escreve: nenhum tool nomeado. Sao JSON ad-hoc de agentes de sessoes
  anteriores, varridos por `os.walk(ROOT)` (:520-537) em ~3.788 arquivos sob
  `.agents/`. Amostras lidas (`.agents/runtime/audits/lote35_banda2_veredito.json`,
  `.agents/runtime/qa-banda1/lote41_veredito.json`) confirmam: campo `veredito`
  com valor cru, sem campo de justificativa. Os codigos sobreviventes aparecem
  em `data/ops/v2_verified_repairs.jsonl`: `REPROVADA:5` (3), `REPROVADA:4` (1).
  A memoria do projeto esta correta.

## Custo estrutural do gerador

`os.walk(ROOT)` a cada execucao varre /opt/wiki inteiro — 105 entradas de topo,
289 clones untracked, ~96 GB — excluindo so `.git`, `node_modules`, `.toolchains`.
Qualquer `*result*.json` dentro de um clone com `intent_id` + `veredito` entraria
como veredito de producao.

## Motivos vivos: 13 criticos no censo + 3 no seletor Go

Censo (tools/generate-v2-publication-severity):
intencao_pulada_deliberadamente :693 · sem_corpo :696 · falta_{title,
meta_description,h1,opening} :699 · corpo_abaixo_de_250_palavras :701 ·
intent_duplicado_entre_shards :711 · promessa_oab:<tag> :715 ·
promessa_oab:sinalizada_pelo_pipeline :718 · encoding:<defeito> :721 ·
reprovada_em_auditoria_humana :739 · veredito_conflitante :744 ·
campo_obrigatorio_ausente :748 · area_nao_derivavel :786 · rota_duplicada :847

Seletor Go (internal/v2publish/v2publish.go:391 SelectPublishable):
sem_linha_no_censo :401 · area_indefinida :415 · rota_colidente :427

O CLAUDE.md secao 5 diz "onze". Sao 13 no censo, mais 3 no seletor.
