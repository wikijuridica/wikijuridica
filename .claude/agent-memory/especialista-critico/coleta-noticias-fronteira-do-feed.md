---
name: coleta-noticias-fronteira-do-feed
description: A Justiça Estadual brasileira quase não publica RSS — a ampliação do canal de notícias esbarra em ausência de feed, não em código nosso
metadata:
  type: project
---

Medido em 2026-09-16 com o UA canônico do projeto, sobre 40 candidatas (27 TJs, TRF2–5, cinco
TRTs, TSE, STM, CNMP, MPF), com descoberta em três passos (declaração na raiz, declaração na
seção de notícias, caminhos convencionais do CMS validados por elemento raiz): a **maioria não
serve feed**. Não é ausência de notícia; é ausência de FEED — os portais migraram para front-end
em JavaScript e o HTML servido ao robô não declara `<link rel="alternate">`.

**Why:** a desproporção de áreas do acervo (previdenciário/tributário/criminal concentrados) foi
atribuída a "coleta quebrada" no §1.15 do plano do cérebro. A parte que é nossa foi consertada
(matriz virou dado; teto por fonte em vez de global). A parte que sobra é externa e medida: o
tribunal não publica feed, ou o robots.txt nega, ou o TLS do host não fecha com o pool do sistema.

**How to apply:** antes de prometer cobertura da Justiça Estadual pelo canal de feeds, leia o
laudo mais recente ([[referencia-matriz-fontes-noticias]]). A hipótese que aumenta o rendimento —
e é frente própria — é **extração da listagem HTML da seção de notícias** pelo mesmo
`internal/sourcecollect`, para os hosts cujo robots permite e cuja seção já está localizada no
laudo. Três classes menores têm destrava nossa, não externa: envelope Atom/RDF (ensinar o parser),
TLS `unknown authority` (intermediário em `content/certs/`, precedente em
`cmd/collect-stf-informativo`), e órgão de Ministério Público (o gerador conhece três naturezas e
MP não é nenhuma).
