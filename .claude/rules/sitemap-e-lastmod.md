---
paths:
  - "internal/sitemapgrace/**"
  - "tools/check-sitemap-shard-churn"
  - "tools/check-sitemap-shard-grace"
  - "tools/check-lastmod-causalidade"
  - "data/ops/page_content_revision.jsonl"
---

# Shard de sitemap e `lastmod` — o nome e' posicional, e o registro anda um ciclo atras

Memorias de origem: `sitemap-shard-carencia.md`,
`lastmod-entra-no-sitemap-no-ciclo-seguinte.md`.

## O nome do shard e' o ordinal, e ele some quando o plano encolhe

O nome e' `/sitemaps/pages-%04d.xml` e a particao e' por (data de revisao, area):
quando uma coorte nasce, esvazia ou cruza `minCohortURLs=50`, o **conjunto** de
shards muda e o ordinal do fim some. Isso e' aceito de proposito (o `lastmod`
acionavel vale 468x), mas ate 2026-08-13 `cmd/publish-v2-direct` apagava o orfao
na hora — e o comentario de la alegava fechar a janela de 404 escrevendo o indice
primeiro, o que fecha **metade** dela: protege quem ler o indice dali em diante,
nao quem ja leu o anterior.

Medido: `pages-0032.xml` respondeu **200 as 13:50:43** e **410 as 13:58:07**, com
o **Googlebot levando 410 as 14:08:31** — ele leu o indice VERDADEIRO e caiu num
buraco aberto 8 minutos depois. Em 08-12 a mesma mecanica deu 14x404 ao Bingbot
(`pages-0032..0045`).

Desde entao existe `internal/sitemapgrace`: shard retirado sai do indice na hora
e **continua servivel 8 dias** (TTL de borda do indice, 604.800 s, + 1 dia). A
marca vive **dentro do XML** — nunca em ledger — porque `publishedmanifest`
recusa shard fora do indice e `<loc>` duplicada no **boot**
(`httpserver.go:480`), e um registro externo perdido poria o portal fora do ar.

Tres rotas foram descartadas por medicao antes desta: renomear os 31 shards (o
proprio churn autoinfligido), encurtar o TTL de borda (reintroduz o colapso de
08-11) e acoplar purga (ja existia).

Ao mexer em particao ou nome de shard, rode `tools/check-sitemap-shard-churn`
(mede quantas revisoes faltam para a proxima coorte cruzar o piso — 37 paginas de
`autonomos` derrubam 29 dos 31 shards) e `tools/check-sitemap-shard-grace`
(coerencia do diretorio; roda no deploy). O 4xx do painel **nao zera**: 410
tambem e' 4xx e a memoria do crawler dura mais que qualquer prazo. A metrica e'
**nenhum nome novo extinto sem carencia**.

## `check-lastmod-causalidade` exit 2 e' PENDENCIA, nao defeito

`tools/deploy-publico` grava `data/ops/page_content_revision.jsonl` **depois** da
purga, por desenho declarado no comentario do passo 7: o registro e' a memoria de
"o que ja foi ao ar com esta versao", e atualiza-lo antes apagaria a lista do que
precisa sair do cache. Como `cmd/publish-v2-direct` le esse registro para emitir
`<lastmod>` e `content_revised_at`, a data gravada neste ciclo entra no sitemap
servido so no ciclo **seguinte**.

Medido em 2026-09-10: ledger `2026-09-10` para 1.457 rotas, `<lastmod>` no disco
`2026-08-26`/`2026-09-09`. O gate sai com exit 2 e a palavra e' PENDENTE — as
quatro contagens que denunciariam sinal fabricado (revisoes reais, datas
fabricadas, precisao falsa, revisao afirmada sem conteudo mudar) deram **todas
zero**. Nao ha recursao a temer: `served_sha256` neutraliza datas, entao a
publicacao seguinte nao conta a data nova como churn.

Tratar esse exit 2 como defeito leva a mexer no gate ou no gerador. O remedio e'
uma republicacao, e ela normalmente ja esta agendada por outro motivo: leia a
frase do gate — "PENDENTE … falta republicar pelo pipeline sancionado" fecha no
proximo deploy sem custo extra.
