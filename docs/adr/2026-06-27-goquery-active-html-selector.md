# ADR: goquery como seletor HTML ativo interno

## Decisao

`github.com/PuerkitoBio/goquery` v1.8.0 fica adotado como dependencia runtime interna ativa, com escopo restrito a `internal/demandobservations`.

O uso aprovado e apenas parsing por seletor de HTML ja obtido e limitado em memoria, para produzir amostras textuais de pesquisa bloqueadas. A biblioteca nao pode buscar URL, seguir links, rastrear fonte, copiar texto para pagina publica, abrir `public/`, `content/pages.json`, `published_manifest`, sitemap real, render publico ou qualquer flag de publicacao.

## Motivo

A camada de demanda textual precisa extrair corpo util de HTML oficial ou publico permitido quando a pagina usa containers como `[role=main]`, `.conteudo-principal`, `#content` ou estruturas equivalentes. O fallback antigo por tags `main/article/body` podia cair em `body` e misturar menu, aside e rodape, gerando falso diagnostico textual ou rejeicao de amostra aproveitavel.

`goquery` ja estava no grafo como dependencia indireta e oferece seletores CSS maduros sobre `x/net/html`. A adocao direta remove a ambiguidade de politica: e uso ativo da fabrica, nao backlog, com escopo de import e evidencia versionados.

## Escopo

- pacote permitido: `internal/demandobservations`
- entrada: `[]byte` ja limitado por `max_response_bytes`
- saida: `demand_content_samples` bloqueado, limitado, hashado e sem publicacao
- proibido: `ParseURL`, cliente HTTP da biblioteca, crawler, fetch de links, texto bruto integral, publicacao, render, sitemap e manifest publico

## Validacao

- teste de parser com `[role=main]` e remocao de chrome
- teste de politica permitindo import apenas em `internal/demandobservations`
- teste de politica rejeitando import fora do escopo
- `check-codex2-policy-enforcement`
- prova de diff publico vazio antes de commit
