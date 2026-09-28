# Catálogo de APIs — RFC 9727 no wikijuridica.com.br

**Cópia normativa literal:** [`docs/rfc/rfc9727-api-catalog.txt`](rfc/rfc9727-api-catalog.txt)
(33.086 bytes, 835 linhas — texto integral, sem uma vírgula alterada).
**Fonte oficial primária:** <https://www.rfc-editor.org/info/rfc9727> — *api-catalog: A
Well-Known URI and Link Relation to Help Discovery of APIs*, K. Smith (Vodafone), IETF,
Standards Track, **junho de 2025**, ISSN 2070-1721.

Este documento é a leitura de engenharia do RFC 9727 aplicada a **este** portal: o que a
norma obriga, o que o ar cumpre hoje (medido, não suposto), o que ainda não cumpre, e o
que dela **não se aplica** aqui — para ninguém "implementar por cargo-culting" uma seção
escrita para publicador com portfólio espalhado por dez domínios.

---

## 1. Por que a cópia literal está versionada no repo

A referência normativa de uma rota que já está no ar não pode depender de um host de
terceiro responder. `rfc9727-api-catalog.txt` é **congelado e imutável**: quem for
auditar `/.well-known/api-catalog` lê a norma no próprio repositório, offline, na versão
exata que sustentou as decisões desta implementação. As três consequências práticas:

- **É referência, nunca fonte a editar.** Alterar aquele `.txt` para "ficar de acordo"
  com o que o código faz inverte a relação e cria a mentira que o
  `docs/CONTRATO_DADO_REAL.md` (R1) proíbe: quem manda é a norma, e a divergência é
  defeito **nosso** a corrigir. Extensão `.txt` justamente para não convidar renderização
  nem reformatação.
- **Licença.** O RFC é publicado sob BCP 78 / IETF Trust Legal Provisions. Reprodução
  integral com aviso de copyright preservado é o uso previsto; os *Code Components* dos
  exemplos carregam a Revised BSD License, declarada no próprio texto copiado.
- **Data importa.** RFC 9727 é de junho de 2025 e é *Standards Track* — não é rascunho,
  não é convenção de fato. `/openapi.json` sozinho é convenção; `/.well-known/api-catalog`
  é norma registrada na IANA (§7.1).

## 2. O que a norma obriga (por seção)

| § | Grau | Obrigação |
|---|---|---|
| 2 | **MUST** | O catálogo se chama `api-catalog` em local *well-known* (RFC 8615). |
| 2 | **SHALL** | `GET /.well-known/api-catalog` devolve um documento de catálogo. |
| 2 | **SHALL** | `HEAD /.well-known/api-catalog` devolve resposta **com header `Link`** contendo a(s) relação(ões) da §3 — e a §3 define exatamente uma: `api-catalog`. |
| 3 | — | A relação `api-catalog` identifica a lista de APIs do publicador do contexto do link; pode ser emitida em header **e/ou** no corpo HTML. |
| 3.1 | — | Dentro do catálogo, `item` (RFC 6573) identifica uma API que é membro do catálogo. |
| 4.1 | **MUST** | O catálogo **inclui hyperlinks para os endpoints de API**. |
| 4.1 | RECOMMENDED | Incluir metadado útil (política de uso, versão, link para o OpenAPI); se não vier no catálogo, **SHOULD** estar disponível nas URIs listadas. |
| 4.2 | **MUST** | Publicar em Linkset `application/linkset+json` (RFC 9264 §4.2). |
| 4.2 | **SHOULD** | O Linkset inclui parâmetro `profile` com o Profile URI `https://www.rfc-editor.org/info/rfc9727`. |
| 4.2 | MAY | Outros formatos por content negotiation — mas o Linkset **MUST** existir de todo modo. |
| 4.3 / 5.3 | MAY | Catálogo pode apontar outros catálogos pela própria relação `api-catalog` (agrupamento para portfólio grande). |
| 5.1 | RECOMMENDED | Publicar o well-known em **cada** domínio de API, com um canônico e redirecionamento dos demais. |
| 5.4 | RECOMMENDED | Disponibilidade, tempo de resposta, **remoção de entrada obsoleta no ciclo de release**, validação de sintaxe e revisão de metadado. |
| 6.1 | **SHALL** | O sufixo vai sob o prefixo `/.well-known/`. |
| 6.2 | **MUST** | A localização suporta `application/linkset+json`. |
| 7.1–7.3 | — | Registros IANA: well-known URI (permanente), link relation, e o Profile URI. |
| 8 | **SHOULD** | TLS exclusivo; revisão de segurança/privacidade antes de publicar; **somente leitura** para requisição externa; rate limit; auditoria para não vazar API interna nem manter "API zumbi". |

## 3. O que este portal cumpre — medição de 2026-08-19/20

Medido na origem Go (`127.0.0.1:8089`) e na borda pública (`https://wikijuridica.com.br`),
com corpo **idêntico byte a byte** entre as duas (`diff` vazio), ETag
`"6e22bf1caf3a65210e3ff4f837b633e2"`, 877 bytes, `cf-cache-status: HIT` na borda.

| Obrigação | Estado | Evidência medida |
|---|---|---|
| §2 GET → catálogo | ✅ | `200`, `Content-Type: application/linkset+json`, `Cache-Control: public, max-age=300` |
| §2 HEAD → `Link` com `rel="api-catalog"` | ✅ | `HEAD` devolve `Link: <…/.well-known/api-catalog>; rel="api-catalog", <…/openapi.json>; rel="service-desc"; type="application/json"` |
| §3 relação anunciada fora do catálogo | ✅ | `Link: …; rel="api-catalog"` (+ `alternate` markdown) medido na home pela **origem** e pela **borda** (`cf-cache-status: HIT`), e também nos hubs de acervo servidos do disco pelo nginx (`/administrativo/` = `200`) |
| §3.1 uso de `item` | ✅ | primeira âncora usa `item` para os endpoints; `service-desc`/`status` (RFC 8631) nas âncoras específicas |
| §4.1 hyperlinks para endpoints | ✅ | `item`: `/api/v1`, `/mcp`; âncoras com `service-desc` para `/openapi.json` e `/.well-known/mcp/server-card.json`, `status` para `/api/v1/health` |
| §4.1 metadado nas URIs listadas | ✅ | `/openapi.json` = `200`, `/api/v1/health` = `200`, `/.well-known/mcp/server-card.json` = `200` |
| §4.2 / §6.2 media type Linkset | ✅ | `application/linkset+json` (sem `charset` — correto: o registro não define o parâmetro e JSON é UTF-8 por definição) |
| §4.2 parâmetro `profile` | ❌ | **ausente** — ver §4 abaixo |
| §6.1 sufixo sob `/.well-known/` | ✅ | rota literal `/.well-known/api-catalog` |
| §8 TLS exclusivo | ✅ | HSTS `max-age=31536000; includeSubDomains`; borda só HTTPS |
| §8 somente leitura | ✅ | `Access-Control-Allow-Methods: GET`; nenhum método de escrita na rota |
| §8 rate limit | ✅ | `limit_req zone=wj_generic burst=600 nodelay`, `limit_req_status 429` (nginx do wiki) |
| §8 sem vazar API interna | ✅ | o catálogo lista apenas rotas públicas do próprio domínio |
| §5.4 dado corrente | ✅ | ver §4: o catálogo servido lista só o que o ar atende |

Consumo cross-origin é o propósito destes documentos, e os headers refletem isso:
`Access-Control-Allow-Origin: *`, `Cross-Origin-Resource-Policy: cross-origin`,
`X-Robots-Tag: noindex` (descritor não é conteúdo editorial e não entra em índice de
busca).

## 4. Lacunas medidas

**(a) O parâmetro `profile` do §4.2 não é emitido.** O `Content-Type` servido é
`application/linkset+json` puro; a norma pede
`application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"` — é um
**SHOULD**, tem registro IANA próprio (§7.3) e aparece nos três exemplos do Apêndice A.
Serve para o cliente **sinalizar e reconhecer** que aquele Linkset é um catálogo de APIs,
e não um linkset qualquer. A correção é uma linha em `linksetMediaType`
(`internal/httpserver/descritores.go`); o teste `TestApiCatalogSegueORFC9727` usa
`strings.HasPrefix` no media type, então não quebra. Fica registrado aqui como achado
datado, para ser executado na frente que o dono determinar — nesta missão o escopo era a
versão normativa e esta leitura.

**(b) O binário em produção está atrás do source — e o catálogo está certo.** O
`apiCatalogDocument` no disco monta **quatro** âncoras e **três** `item` (inclui
`/a2a/v1` e o `service-desc` apontando `/.well-known/agent-card.json`). O ar serve
**três** âncoras e **dois** `item`. Medido: `/a2a/v1` = `404` na origem e
`/.well-known/agent-card.json` = `404` — ou seja, o catálogo servido **não anuncia
endpoint que não existe**, que é exatamente o que a §5.4 ("Current data") e a regra de
transparência do repositório exigem. O descompasso é de **deploy pendente** da frente
A2A/OAuth, não defeito do catálogo. Anunciar antes de o endpoint responder seria
documentar contrato que o ar não cumpre.

## 5. O que da norma NÃO se aplica aqui

- **§5.1 (APIs em múltiplos domínios) — não se aplica.** Há **um** domínio,
  `wikijuridica.com.br`, travado em `content/site.json`. Não existe segundo host de API,
  logo não existe instância secundária do well-known para redirecionar nem catálogo de
  terceiro para linkar. Implementar redirecionamento aqui seria inventar topologia.
- **§4.3 e §5.3 (aninhamento e agrupamento) — não se aplica.** O catálogo tem 877 bytes e
  três protocolos. Aninhar catálogo por categoria resolve custo de rede de portfólio
  grande; aqui só acrescentaria um salto de descoberta e uma superfície a manter. A
  compressão e o cache que a §5.3 recomenda já existem (`max-age=300`, ETag forte com
  `304`, HIT de borda).
- **§5.2 (APIs privadas em rede interna) — não se aplica.** Não há catálogo interno; a
  rota é pública e somente leitura.
- **§5.5 (integração com framework de API management) — não se aplica.** Não existe
  framework de terceiro produzindo o portfólio: o catálogo é derivado no boot da **mesma
  lista** que o índice de serviço anuncia (`apiServiceIndexPayload`), então não há
  segunda lista de endpoints capaz de divergir do roteador — e o teste exige bijeção nos
  dois sentidos. Isso cumpre o espírito da §5.5 (refresh no ciclo de release) por
  construção, em vez de por processo manual.

## 6. Âncoras verificáveis no código

Por **símbolo**, não por número de linha — linha apodrece, símbolo não.

| Símbolo / artefato | Arquivo | Papel |
|---|---|---|
| `apiCatalogPath` | `internal/httpserver/descritores.go` | a rota literal `/.well-known/api-catalog` |
| `linksetMediaType` | `internal/httpserver/descritores.go` | `application/linkset+json` (§4.2/§6.2) — ponto único onde o `profile` entraria |
| `descritorCacheControl` | `internal/httpserver/descritores.go` | `public, max-age=300` (§5.3/§5.4) |
| `apiCatalogDocument` | `internal/httpserver/descritores.go` | monta o Linkset: `item`, `service-desc`, `status` |
| `writeStaticJSONDoc` | `internal/httpserver/descritores.go` | validadores **antes** do corpo → `304` e `HEAD` sem ramo especial |
| `linkDoCatalogo` | `internal/httpserver/markdown.go` | o `Link: rel="api-catalog"` reaproveitado pelas rotas de conteúdo (§3) |
| `case apiCatalogPath` | `internal/httpserver/httpserver.go` | emite o `Link` obrigatório da §2 **e** o `service-desc` extra |
| `TestApiCatalogSegueORFC9727` | `internal/httpserver/descritores_test.go` | trava media type, `linkset` como array e o alvo do `service-desc` |
| `more_set_headers … rel="api-catalog"` | `ops/nginx/wikijuridica.conf`, `ops/nginx/standalone/nginx.conf` | anúncio da relação nas páginas servidas do disco pelo nginx |
| sonda `well-known/api-catalog` | `tools/check-agent-surface-live` | prova no ar: `200` + prefixo do media type, e que a borda **não** redireciona a rota |

## 7. Armadilhas desta rota (medidas, não hipotéticas)

1. **`/mcp` responde `405` a GET — e está correto.** Medido: `GET /mcp` = `405`,
   `POST /mcp` (JSON-RPC `initialize`) = `200`. O `item` do catálogo aponta **identidade
   de recurso**, não "URL que devolve 200 em GET". Auditoria que valide o catálogo com
   GET em cada `href` conclui erradamente que o endpoint está quebrado.
2. **Disco vence Go no nginx.** `try_files $uri` resolve antes do proxy: criar um arquivo
   homônimo em `public/.well-known/api-catalog` tornaria a rota inalcançável e
   congelaria o descritor, livre para divergir do roteador. Por isso o catálogo é servido
   **do Go**, derivado do estado real a cada boot.
3. **A Single Redirect de barra final da borda é capaz de matar a rota.** Escrita
   ingenuamente, ela transforma `/api`, `/mcp` e `/.well-known/api-catalog` em
   `301 → 404`. A sonda `check-agent-surface-live` prova, a cada execução, que os sete
   caminhos protegidos continuam fora da regra — porque uma edição futura nela não avisa
   ninguém. Medido em 2026-08-19/20: `/a2a/v1` recebe `301 → /a2a/v1/` na borda e **não**
   está nessa lista de exclusão (frente A2A, ainda em deploy).
4. **Gate verde não é prova (R2 do contrato).** A sonda confere status e prefixo de media
   type; ela **não** confere o parâmetro `profile`, e por isso o `profile` ausente passou
   verde. Foi a leitura da norma literal — não o gate — que achou a lacuna da §4.2.

## 8. Relação com os outros descritores do domínio

O RFC 9727 é o **ponteiro padronizado**: dele um agente chega ao contrato sem adivinhar
caminho. Ele não substitui, e não é substituído por, os demais artefatos de descoberta
servidos aqui — `/openapi.json` (contrato REST), `/.well-known/ai-catalog.json` (ARD,
manifesto de capacidades com consultas representativas),
`/.well-known/mcp/server-card.json` (transporte e ferramentas MCP),
`/.well-known/agent-card.json` (A2A), `/.well-known/agent-skills/index.json`,
`/llms.txt` e `/auth.md`. A §4.1 é a régua que decidiu incluir `/mcp` (e, no source,
`/a2a/v1`) entre os `item`: "the API catalog MUST include hyperlinks to API endpoints" —
e um endpoint MCP é endpoint de API tanto quanto `/api/v1`.
