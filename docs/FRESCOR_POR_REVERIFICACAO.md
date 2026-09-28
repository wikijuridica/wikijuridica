# Frescor sem expirar conteúdo — investigação e desenho, 2026-08-12

Frente aberta por ordem do dono: *"os conteúdos não podem expirar. Eles devem
parecer novo para o googlebot, mas sem expirar. Investigue isso como causa
independente."*

## A resposta honesta, antes de tudo

**Não existe caminho honesto para uma página inalterada parecer nova para os
sistemas de data do Google.** Com todas as letras, e com a fonte:

- `lastmod` deve refletir *"the date and time of the last **significant**
  update"*, e a doc exclui explicitamente o carimbo: *"an update to the
  copyright date is not"* (developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap,
  consultada em 2026-08-12).
- O Google só usa `lastmod` *"if it's consistently and verifiably (for example by
  comparing to the last modification of the page) accurate"* — ou seja, **ele
  confere o campo contra a última modificação real da página**.
- Não há documento do Google declarando que ele leia `lastReviewed`.

Qualquer mecanismo que prometa rejuvenescer conteúdo intocado ou é ignorado, ou
destrói a confiança no campo. E o campo é caro: perdê-lo é perder a via rápida de
recrawl para as mudanças que **são** reais.

## O bug que a investigação encontrou, e que é o mais urgente daqui

**O `Last-Modified` HTTP que servimos é o mtime do deploy, não a data
editorial.** Medido: **9.844 de 9.844 `index.html` com mtime de hoje**, enquanto
o JSON-LD, o `<lastmod>` do sitemap e o rodapé visível dizem `2026-08-06`.

Isso é exatamente a comparação que a doc descreve como teste de confiança — e
hoje ela dá **contradição em ~9,8 mil URLs**, com o header alegando um frescor
que o conteúdo não teve. `internal/httpserver` monta o header a partir da data
editorial; a produção estática, servida pelo nginx do disco, nunca vê esse
código.

Consequência dupla: todo deploy invalida a revalidação do acervo inteiro (o
crawler que teria ganho `304` recebe `200` com o corpo de volta), e o sinal de
`lastmod` fica sob suspeita justamente quando precisamos dele — há 2.401 páginas
corrigidas esperando para ser recrawleadas.

**Passo 0, antes de qualquer outra coisa:** fixar o mtime do arquivo a partir de
`Page.LastModified()` na publicação, ou emitir o header por rota. Enquanto o
header seguir o mtime do deploy, qualquer sinal novo é varrido pela mesma
contradição.

## A partição — o que move data e o que não move

| caso | move `dateModified` / `lastmod`? | o que move |
|---|---|---|
| **1.** Fonte reconferida, impressão normativa **idêntica** | **NÃO** | `lastReviewed` no JSON-LD + linha visível "fontes conferidas em DD/MM/AAAA" + registro na evidência |
| **2.** Fonte mudou → **texto e links ajustados** | **SIM** | o hash de conteúdo muda, o ledger data, e os quatro sinais movem juntos |
| **3.** Fonte mudou, texto **NÃO** ajustado | **NADA move** | abre blocker fail-closed; a página não pode ser republicada nem receber revisão |

O caso 1 é honesto porque o que se afirma é literalmente o que se fez —
*conferimos a fonte nesta data e ela não mudou* — e é a definição textual de
`schema.org/lastReviewed`: *"Date on which the content on this web page was last
reviewed for accuracy and/or completeness."* É verdade para o leitor humano e
para quem audita o portal, **independentemente** de o buscador ler ou não. Não é
alavanca de ranking, e afirmar que é seria mentir.

O caso 3 é o risco que o dono nomeou: detectar que a lei mudou e não corrigir
produz conhecimento de defeito sem correção. Por isso a detecção **não** move
data nenhuma e **impede** a republicação — o único estado honesto para uma página
que se sabe defeituosa é continuar anunciando a data em que ela foi de fato
correta. Detecção, reparo e publicação fecham no mesmo ciclo; varredura que só
detecta é proibida.

## O detector: impressão normativa, não sha256 do HTML

Portal de governo muda banner, sessão e rodapé sem mudar norma — o byte-hash
daria falso positivo em massa e viraria ruído que ninguém atende.

O detector correto é a **impressão normativa**: conjunto de âncoras do documento
+ conjunto de normas alteradoras extraídas das notas do corpo (`(Redação dada
pela Lei nº X, de ANO)`) + ano máximo de alteração. O `sha256` do corpo continua
sendo gravado, mas como **evidência de auditoria**, nunca como gatilho.

A semente já existe: a conferência de 2026-08-12 gravou 694 documentos com
`sha256` do corpo, 310 com âncoras extraídas e 283 com ano máximo apurado
(`data/editorial/v2_planalto_anchor_conference_20260812.jsonl`).

## Cadência: os números do repo, não um número inventado

`sourceregistryv2.ttlDays` já define 30 dias para política OAB e de qualidade de
busca, 90 para legislação federal, 60 no default; `OfficialSourceVerificationMaxAgeDays`
é o teto de 90. Cada URL é reconferida **antes de vencer a TTL da própria
família**, em lote diário do mais antigo para o mais novo, **escalonado para nada
vencer em bloco** — vencimento em bloco foi exatamente o defeito que o commit
`8792460d` corrigiu nesta mesma manhã.

Com 4.380 URLs distintas e teto de 90 dias, o regime estacionário é de **~50 a
150 URLs por dia**, respeitando 1 requisição por segundo por host; o host mais
lento dita o relógio.

## Evidência a gravar, auditável por terceiro

Por documento e por rota: `url`, `consultado_em`, `http_status`, `method`,
`sha256_documento`, `bytes`, `ancoras_no_documento`, `normas_alteradoras`,
`ano_max_alteracao`, `impressao_normativa_anterior`, `mudou`, e o gerador datado
que produziu a linha. Qualquer pessoa re-baixa a URL, recalcula e confere.

## Como conversa com a partição do sitemap por (data, área)

A favor. No caso 1 o hash não muda, a página fica na mesma coorte, o ordinal do
shard não se desloca e **nenhum `<lastmod>` de shard se move** — a varredura de
verificação é invisível para o crawler, que é o correto. No caso 2 a página migra
para a coorte da data nova e **só o shard novo anuncia data nova**.

Requisito derivado: `sitemap.xml`, os shards e o `feed.xml` precisam entrar na
purga de borda a cada publicação — correção na origem não existe para o mundo
até a purga.

## O que seria fraude, e por isso está fora

- Carimbar `lastmod`/`dateModified` por decurso de tempo, por varredura de
  verificação, ou "porque faz tempo que não muda".
- **A brecha que alguém vai tentar:** a doc lista *"an update to the structured
  data"* como significativo, logo mexer no `lastReviewed` "atualiza structured
  data" e justificaria mover o `lastmod`. **Rejeitado.** A frase se refere a
  mudar o dado que descreve a página — autor, preço, tipo —, não a inserir um
  carimbo cujo único propósito é mudar. `lastmod` que se move por causa de uma
  data é o caso do copyright, não o caso do structured data.
- Deixar a data de revisão entrar nos campos de conteúdo que compõem o hash. Se
  entrar, cada varredura muda o hash, move o ledger e move o `lastmod` — e o
  mecanismo anti-fraude vira a fraude. O campo nasce **fora** do hash.
- "Reconferido" sem requisição real. Precedente vivo do risco: há **7.965**
  registros com `release_live_recheck_required: true` e **zero**
  `ingest_live_recheck_performed` — um campo que promete uma ação nunca
  executada. O desenho ou o cumpre ou o remove; deixá-lo como está é afirmação
  sem lastro.

## O que o mecanismo compra de verdade

Ele não faz o velho parecer novo. Ele garante que **o que é novo seja
acreditado** e que **o que envelheceu de verdade seja consertado antes de o
leitor tropeçar**:

1. Um `lastmod` que continua acreditado — logo, as 2.401 páginas corrigidas hoje
   são recrawleadas depressa quando forem publicadas.
2. `Last-Modified` e `304` corretos, hoje errados em ~9,8 mil páginas.
3. `lastReviewed` com `sha256` auditável, verdadeiro para o leitor e para quem
   fiscaliza.
4. Reparo rápido quando a lei muda — **a única fonte legítima de "novo" num
   acervo jurídico**.

Se o objetivo for movimento constante de data, a via honesta é editorial: o
direito muda o tempo todo, e **4.413 páginas já têm fonte fora do prazo de
higiene**. Há trabalho real de sobra para gerar datas novas legítimas.

## Ordem recomendada

1. `Last-Modified` derivado da data editorial (o passo 0 acima).
2. Publicar as 2.401 páginas já corrigidas e as 39 rotas em que o ledger está à
   frente de `content/pages.json`.
3. Linha de base de impressão normativa por documento (as 694 de hoje são a
   semente).
4. As **1.684 páginas sem proveniência nenhuma** (17% do acervo informativo, a
   família `/aereo/` inteira entre elas) e as **135 fontes sem `verified_at`**.
5. Só então o laço periódico com `lastReviewed`.
