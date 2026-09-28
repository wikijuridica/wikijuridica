# Correção dos avisos de dados estruturados do GSC — QAPage (2026-08-20)

## O que o dono reportou

Painel "Melhorar o aspecto de itens" do Search Console, 7 avisos:
`upvoteCount`, `author`, `url`, `datePublished` ausentes em `mainEntity.acceptedAnswer`;
`author`, `text`, `datePublished` ausentes em `mainEntity`.

## Medição própria (reprodutível)

| Fato | Valor | Como medi |
|---|---|---|
| Páginas que emitem `QAPage` | **441** | `grep -rl '"@type":"QAPage"' public --include=*.html` |
| Delas em `/glossario/` | **401** | mesmo grep, agregado pelo 1º segmento do path |
| Delas com bloco `faq[]` visível | **0** | interseção QAPage ∩ FAQPage no HTML |
| `Question.name` em forma interrogativa | **64** (17 com `?`) | varredura do `name` no JSON-LD |
| `Question.name` que é termo/título, não pergunta | **377** | complemento |
| `acceptedAnswer.text` vs `Article.abstract` | **idênticos** | leitura do JSON-LD de `/glossario/aberratio-ictus/` |
| Google detecta o rich result | **sim, PASS** | URL Inspection API, `/servidor/pad-excesso-de-prazo-de-conclusao/` |

Os 7 avisos são, um a um, os campos **recomendados de QAPage** — não de FAQPage.
Origem no código: `internal/structureddata/structured_data.go:1435` (`RenderQAPageScript`),
acionado em `internal/render/render.go:590`.

## Por que preencher os campos seria a correção errada

Diretriz oficial, verbatim
(https://developers.google.com/search/docs/appearance/structured-data/qapage, lida em 2026-08-20):

> "Users must be able to submit answers to the question. Don't use `QAPage` markup for content
> that has only one answer for a given question with no way for users to add alternative answers."

E, entre os casos inválidos listados:

> "An FAQ page written by the site itself with no way for users to submit alternative answers"

O portal emite `answerCount: 1` com uma única `acceptedAnswer` e não tem submissão de respostas
por usuários: a descrição do caso inválido é literal. Preencher `upvoteCount`, `author`, `url` e
`datePublished` gastaria uma mudança em produção para tornar a violação **mais legível** — o
`author` do Answer seria o próprio autor do site, que é justamente o que a diretriz veda. Além
disso `upvoteCount` só poderia ser `0` (não há votação), sinal vazio.

Havia ainda um risco de implementação concreto: `faqAnswerJSONLD` é struct COMPARTILHADO entre
`QAPage` e `FAQPage`. Preencher campos ali vazaria para os **8.207** `FAQPage` do acervo — churn
de 84% das páginas por engano.

**O risco de ação manual, com a régua certa:** marcação inelegível é tipicamente **ignorada**
pelo buscador. "Spammy structured markup" existe como classe de ação manual documentada, mas não
há caso público específico de `QAPage`, e o cenário site-wide é o extremo, não o esperado. Esta
correção **não depende** de inflar esse risco: bastam a violação literal e a redundância byte a
byte com o `Article.abstract`.

**A única exceção da doc foi verificada e não se aplica:** existe um carve-out para
*"Education-related Q&A pages, where the primary focus is to provide a correct answer to a
user-submitted homework question"*, que admite resposta única de especialista da casa. Verbete de
glossário jurídico não é pergunta de dever de casa submetida por usuário, e 377 dos 441
`Question.name` sequer são perguntas.

## Por que FAQPage também não serve como substituto

A doc de QAPage **não** nomeia FAQPage como alternativa (verificado na fonte). E FAQPage exige
o par pergunta/resposta **visível na página** — regra que este repo já impõe em
`internal/structureddata/structured_data.go:250` ("FAQPage descreve conteúdo presente, nunca
oculto"). Nenhuma das 441 tem bloco `faq[]`; o par seria H1 + resumo, ou seja título + abstract.
Marcar FAQPage aí seria afirmar uma pergunta que não está na página — FAQ fabricado, vedado pelo
contrato anti-fraude.

## A correção

1. **Retirar `QAPage` das 441 páginas.** Marcação que viola a diretriz e é redundante: seu
   `acceptedAnswer.text` é byte a byte o `Article.abstract` da mesma URL. Zero informação perdida.
2. **Emitir `DefinedTerm` nos 401 verbetes de `/glossario/`** — tipo canônico do schema.org para
   verbete, alimentado pelos mesmos campos visíveis (H1 → `name`, resumo → `description`), com
   `inDefinedTermSet` apontando para o hub.
3. **Embutir o `DefinedTermSet` em cada verbete**, auto-contido (`@type`, `@id`, `name`, `url`),
   apontando para a hub real `/glossario/`. NÃO como nó separado na hub: ela emite exatamente um
   `ld+json` por contrato verificado em `internal/render/area_hub_test.go`, e apontar para um
   `@id` que ela não declara deixaria referência pendurada.
4. **40 páginas não-glossário**: nada substitui o QAPage. O `Article` delas já traz `author`,
   `reviewedBy`, `datePublished`, `dateModified`, `publisher`, `citation` e `mentions`. Nada é
   inventado para preencher espaço.

## Efeito honesto

Isto **remove uma violação de diretriz e um nó redundante**. Não é alavanca de ranking, e não
será apresentado como tal. O ganho mensurável é: os 7 avisos deixam de existir porque o item
deixa de existir; o risco de ação manual por dados estruturados sai; e o glossário passa a
declarar a entidade que ele de fato é.

## Governança

Registrado como **DEC-033** em `docs/goal/DECISIONS.md`, como exceção NOMEADA à **DEC-027** — que
mandou manter `FAQPage`/`HowTo` e contou estes mesmos 441 `QAPage`. A DEC-027 protege contra
remoção motivada por "o rich result foi extinto"; o motivo aqui é inelegibilidade por diretriz,
que ela própria declara fora do seu escopo e classifica como defeito P0. Os 8.207 `FAQPage` e os
292 `HowTo` FICAM.

## Não termina no commit — e regerar fora da transação derruba o portal

`publishedmanifest.Validate` roda no BOOT (`internal/httpserver/httpserver.go:541` →
`cmd/server/main.go:54` `log.Fatal`) e compara `record.HTMLSHA256` com o arquivo real
(`internal/publishedmanifest/publishedmanifest.go:986`) e com a transação (`:1098`). HTML regerado
por fora = hash divergente = **servidor recusa subir**.

Ordem obrigatória: **código → transação `cmd/publish-v2-direct` (reescreve os dois hashes) →
purga de borda → conferência na URL ao vivo.** Origem correta e borda correta são fatos
diferentes (`[[edge-cache-serve-erro-velho]]`).
