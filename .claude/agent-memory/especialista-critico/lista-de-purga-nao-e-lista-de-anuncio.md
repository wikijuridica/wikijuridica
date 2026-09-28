---
name: lista-de-purga-nao-e-lista-de-anuncio
description: Reusar a lista de chaves de cache da borda como payload do IndexNow duplicou metade do anuncio; conjuntos com semantica diferente nao se reaproveitam por conveniencia
metadata:
  type: project
---

Uma lista so pode ser reusada por outro consumidor se os dois tiverem o MESMO
criterio de pertinencia. Reusar por conveniencia — "ja esta pronta, tem as
rotas que mudaram" — e erro de categoria, e ele nao aparece como erro: aparece
como volume a mais.

**O caso medido (2026-09-16).** `tools/generate-page-content-revision
--purge-targets` emite DUAS linhas por rota (`generate-page-content-revision:738-741`):
`/x/` e `/x/index.md`. Para a purga isso e correto — sao duas chaves de cache
distintas na borda, e a gemea so sai de la por nome. `tools/deploy-publico:1506`
reusa essa lista VERBATIM como payload do IndexNow. A borda tem um objeto por
chave; o indice do buscador tem uma entrada por documento canonico. Conjuntos
diferentes.

Medido na origem (`data/ops/indexnow_url_state.jsonl`, uma linha por URL por
lote POSTado): 2.422 de 13.941 eventos eram `.md` (17,4%), em 1.968 URLs
distintas, TODAS com HTTP 200. No lote de 15:50:19: 254 URLs = 127 HTML + 127
gemeas, com as 127 maes no mesmo lote — 50% exato de duplicata. E a gemea
declara o proprio veredito: serve `link: <.../x/>; rel="canonical"`.

**Why:** o defeito nasceu de uma correcao legitima e estreita demais no lugar
errado. Em 2026-09-10 (commit `224fb9ba`) a guarda `e_gemea_de_rota_conhecida`
passou a ACEITAR a gemea para reentregar NOVE URLs que tinham tomado 503. Antes
dela o valor era zero por construcao: a lista com gemea reprovava inteira. Uma
capacidade pedida para 9 URLs virou o padrao de uma lista que traz a gemea
SEMPRE, e rendeu 1.968. As duas pontas estavam erradas — recusar tudo calava o
canal em todo deploy; aceitar poluia metade.

**How to apply:** antes de passar uma lista de um produtor para um consumidor
novo, escreva o criterio de pertinencia dos DOIS e compare. Se diferirem, o
consumidor PARTICIONA (`particiona_pedidas` em
`tools/generate-indexnow-direct-submit`) em vez de aceitar-ou-recusar, imprime
quantas descartou e grava o numero na evidencia do lote
(`dropped_markdown_twins`). Foi a ausencia desse contador que deixou o defeito
viver seis dias: a submissao dizia "254 URLs" e nao dizia que 127 eram
duplicata. Capacidade excepcional vira flag nomeada
(`--incluir-gemea-markdown`), nunca padrao.

Ver [[gate-de-mao-dupla-le-o-ledger-nao-o-estado]] — o gate que deveria ter
apanhado isto era cego pelo mesmo motivo estrutural.
