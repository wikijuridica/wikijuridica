# Medição de audiência — GA4 e Microsoft Clarity

Este documento é o contrato da medição de audiência do portal. Ele existe porque
as decisões abaixo **não são deriváveis do código**: quase todas nasceram de uma
medição em navegador real que contradisse o que a documentação sugeria, e um
agente que não as conhecer vai refazer o mesmo erro — ou, pior, "corrigir" o
código para o estado que já foi medido como quebrado.

Precedência: este documento é subordinado a `CLAUDE.md` e a
`docs/CONTRATO_DADO_REAL.md`. **Vence a regra mais restritiva.**

---

<!-- BLOCO-CANONICO-REGRAS-DO-DONO: inicio — replicado palavra por palavra; internal/contract/misc/regras_do_dono_test.go reprova cópia ausente ou divergente -->

## Regras do dono — bloco canônico (2026-09-15)

Sete vereditos adotados, um por linha, em vigor desde 2026-09-15. O argumento, o caso medido e
o prejuízo de cada um ficam em `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` §P0, nos blocos
*"Texto do item N"*, e em `docs/PRECEDENTES_DAS_ORDENS.md`; aqui fica só a ordem. Este bloco é
replicado palavra por palavra em `CLAUDE.md`, `AGENTS.md`, `GOAL.md`, `CHECKPOINT.md`,
`docs/CONTRATO_DADO_REAL.md`, `docs/MEDICAO_DE_AUDIENCIA.md`, `docs/CRAWLERS_E_BOTS.md`,
`docs/CONTENT_QUALITY.md`, `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` e
`docs/DATA_SOURCES.md` — cópia divergente ou ausente reprova
`./tools/go-modern test -count=1 ./internal/contract/misc/`. Nenhuma linha daqui carrega número
de estado: o contrato diz onde medir, e quanto é se mede na hora.

**Regra 8 — nenhuma decisão volta para o dono (2026-09-15).** Decida e execute a decisão técnica, inclusive a ambígua, pela rota mais conservadora que ainda entrega e com a suposição escrita no commit; é vedado devolver decisão ao dono, desenhar revisão humana como etapa de esteira de conteúdo ou travar frente à espera de aprovação.

**Regra 9 — dado público vai até o fim da cadeia, e o DataJud está destravado (2026-09-15).** DataJud, API Pública do CNJ, DJEN, LexML, `normas.leg.br`, Planalto, diários oficiais e portais da transparência entram em página publicada com número, classe, órgão, relator, andamento e nome das partes, retirado o identificador (CPF, RG); a linha que fica é `nivelSigilo > 0`, ECA, Maria da Penha, adoção e o art. 5º, II da LGPD, e quem propuser trava, gate, allowlist ou regime de "só sinal interno" cita a norma e o dispositivo — sem dispositivo citado, a rota segue aberta.

**Regra 13 — a ética da OAB tem três regimes, e o deste portal é o do conteúdo informativo (2026-09-15, precisada em 2026-09-16).** Regime A, publicidade profissional — anúncio, oferta, perfil, captação —, é o que CED arts. 39, 40, 44, 45 e 46 e Provimento 205/2021 arts. 3º, 5º e 6º disciplinam, e esses gates ficam como estão; regime B, conteúdo informativo, é permitido com deveres de forma — CED art. 41 (não induzir a litigar), art. 42, I (não responder consulta de caso concreto em canal público), art. 42, IV e art. 43 (sem sensacionalismo), Provimento art. 4º e Anexo Único — e é o regime de página, verbete, comentário de acórdão e dataset deste portal; regime C, a exatidão técnica da informação jurídica, está fora da disciplina, então erro de conteúdo se trata como defeito de qualidade: conserta-se o produtor, mede-se antes e depois, e a página publica e refina. O canal de contato tem autorização expressa no Provimento art. 4º, §3º, que equipara ao e-mail os aplicativos de mensagens instantâneas; jurisprudência pública de terceiro fica, e resultado obtido pelo próprio autor em causa que patrocina sai, mesmo anonimizado (Provimento art. 4º, §2º). Quem invocar risco disciplinar contra conteúdo informativo cita o dispositivo, e o texto literal conferido em fonte primária está em `docs/goal/JURIDICO_BASE.md` §1.1; sem dispositivo citado, a rota segue aberta.

**Regra 15 — tráfego, alcance e retorno de bot medem-se na borda (2026-09-15).** Com `s-maxage=604800` na Cloudflare o `HIT` não toca o Go, então `data/ops/access/*.jsonl` é piso e só tem autoridade sobre o que existe apenas na origem (rota dinâmica, gêmea Markdown, `/api/v1`, MCP, descritores); volume se lê por `tools/cloudflare_auth.py` — `cf.zona_id("wikijuridica.com.br")` e `cf.graphql(...)` sobre `httpRequestsAdaptiveGroups` com dimensão `userAgent`, fatiando a janela em um dia por chamada no plano Free (`JANELA_MAXIMA_DIAS_FREE = 1`) —, toda afirmação de volume declara a camada medida, e série cumulativa como `edge_bot_agents_daily` se lê por último-por-dia, sem somar linhas.

**Regra 16 — não estreitar o projeto com número curto (2026-09-15).** Antes de escrever que uma frente é pequena, marginal, não escala ou não vale a pena, meça na fonte com autoridade sobre aquela grandeza; instrumento que declara a própria limitação é ordem de trocar de instrumento, e volume baixo confirmado entra com a camada declarada e com a hipótese do que o aumentaria, não como veredito de encerramento.

**Regra 18 — é proibido limitar este projeto (2026-09-15).** A plataforma cresce, é indexada e é citada, e o papel da engenharia é acelerar: todo teto nomeia a causa física externa e medida — `Crawl-Delay` publicado pelo operador remoto, tok/s do modelo, cota de requisições da API —, toda recusa de frente vem com a medição que a sustenta e com a hipótese do que a reverteria, e margem de prudência própria não é teto, é atraso.

**Regra 20 — bug anterior não trava trabalho, e não se contorna (2026-09-15).** Defeito encontrado no caminho se conserta no caminho, com agentes, na mesma sessão: "já estava quebrado antes" não é licença para parar, contorno vira a próxima peça quebrada, e medição que não caiu na rodada é passo de runbook — item que chegue ao fim da execução sem medição é falha de execução.

<!-- BLOCO-CANONICO-REGRAS-DO-DONO: fim -->

## Como se mede volume na borda (Regra 15, 2026-09-15)

A Regra 15 acima é a ordem; este é o procedimento. A credencial já existe no ambiente e não se
pede nenhuma.

- `tools/cloudflare_auth.py` é a fonte única da credencial e resolve por escopo, menor
  privilégio primeiro: `CLOUDFLARE_ZONE_TOKEN` (Bearer, lê Analytics) e, só onde ele não
  alcança, `CLOUDFLARE_EMAIL` + `CLOUDFLARE_API_TOKEN` — que, apesar do nome, é a Global API Key
  e autentica somente pelos cabeçalhos `X-Auth-Email` / `X-Auth-Key`. Mandar a Global Key como
  `Authorization: Bearer` não autentica, e foi essa confusão que fez o repositório registrar a
  credencial como "inválida" por meses (`tools/cloudflare_auth.py:177`).
- O recorte por agente sai de `httpRequestsAdaptiveGroups` com dimensão `userAgent`, via
  `cf.zona_id("wikijuridica.com.br")` e `cf.graphql(consulta, variaveis, "leitura")`.
- O plano Free recusa janela maior que um dia por chamada — `JANELA_MAXIMA_DIAS_FREE = 1`,
  `tools/cloudflare_auth.py:69`. Fatia-se a consulta; não se desiste dela nem se publica o
  número curto (Regra 16).
- A origem continua sendo autoridade sobre o que existe apenas nela: rota dinâmica, gêmea
  Markdown, `/api/v1`, MCP e descritores de máquina, em `data/ops/access/*.jsonl`. Para o acervo
  estático, servido de `public/` com `s-maxage=604800`, ela é piso.
- Série cumulativa não se soma: `data/ops/edge_bot_agents_daily.jsonl` é último-por-dia e se lê
  por `serie_saneada` (`tools/edgetelemetry.py:270`).

## O que está instalado

Uma tag só, para as duas ferramentas, dentro do **único** `<script>` inline que a
página emite (`internal/pageinline.Script` = `webmcp.Script + webanalytics.Loader`).

| | |
|---|---|
| GA4 | `G-H6FQ8CQJNR` — `internal/webanalytics.MeasurementID` |
| Clarity | `y8lzjnjpay` — `internal/webanalytics.ClarityProjectID` |
| Carregador | `internal/webanalytics.Loader`, teto `LoaderBudget` |
| CSP | derivada por `internal/pageinline.CSPSource()`, allowlist fechada em `internal/httpserver/security_headers.go` |

**Nunca acrescente um segundo `<script>`.** `internal/htmlcontract` isenta
exatamente uma constante Go, byte a byte, sem atributos. Uma tag separada reprova
em oito gates e seis testes. Medição nova entra **dentro** do `Loader`.

---

## `target="_blank"` é instrumento de medição, não preferência de navegação

Esta é a política que mais provavelmente será desfeita por engano, então ela vem
primeiro e com a prova junto.

### O que foi medido (2026-08-29)

`clarity("event", nome)` **não envia nada**. Ele bufferiza e agenda um flush com
atraso entre 100 ms e 30 s (`clarity.js` 0.8.69, servido). A fila é **memória
pura**: sem persistência, sem `sendBeacon`, sem erro visível. Se a página for
destruída antes do flush, o evento some sem deixar rastro.

Todos os alvos instrumentados **navegavam para fora na mesma aba**. Resultado, com
clique real do Playwright e navegação real:

| Cenário | Payloads | `whatsapp_click` chega? |
|---|---|---|
| Sem `target`, clique imediato | 0 | **NÃO** |
| Sem `target`, clique com a tag carregada há 4 s | 1 | **NÃO** |
| Com `target="_blank"`, clique imediato | 1 | **SIM** |
| Com `target="_blank"`, após 4 s | 2 | **SIM** |

Não é "o primeiro clique se perde": o evento **nunca chegava**, nem com a tag
carregada. O que o painel mostrava como "parou de contabilizar" era um zero
estrutural.

### A regra que isso parecia violar — e como ela é atendida

`internal/accessibilityaudit/rules.go` tem `ruleNewTab` (WCAG 3.2.5, técnica
G201): `target="_blank"` **sem aviso** é achado. Ela aceita o aviso no texto
visível **ou** no `aria-label`, procurando `"abre em"`, `"nova aba"` ou
`"nova janela"`.

A saída **não** é burlar a regra (pôr o `target` por JavaScript no `pointerdown`
passaria despercebido, porque a auditoria lê o HTML servido e não o DOM — e o
defeito de acessibilidade seria real para quem usa leitor de tela). A saída é
**atender** a regra:

```
<a class="wa-float-link" href="…" target="_blank" rel="nofollow noopener"
   aria-label="Falar com o advogado pelo WhatsApp, abre em nova aba">
```

O aviso vai no `aria-label` e não no texto visível **de propósito** nos links de
proveniência: o texto do link é o nome da fonte (`"Lei 9.610/98"`), e emendar
"(abre em nova aba)" nele poluiria a leitura em mais de 10 mil páginas. Quem usa
leitor de tela recebe o aviso; quem enxerga vê o nome limpo.

### O sanitizador foi corrigido junto, e por quê

`internal/htmlpolicy` removia `target` de todo `<a>` — **não por decisão, por
ausência**. O efeito era um falso "o repo proíbe": o atributo sumia do corpo
sanitizado e `html_policy_sanitized_differs` travava a release.

Hoje `target` é permitido em `<a>` com o token fechado `^_blank$`
(`targetBlankToken`). Os dois papéis ficaram separados, que é como deviam estar:

- **`htmlpolicy` julga segurança de markup** — o risco de `_blank` é o
  `window.opener` (reverse tabnabbing), fechado por `rel="noopener"`, que os dois
  emissores carregam. Nome de janela arbitrário, `_self`, `_parent` e `_top`
  continuam fora.
- **`accessibilityaudit` julga acessibilidade** — é ela que cobra o aviso.

**Onde `target="_blank"` está aplicado, e só aí:** `renderWhatsAppFloat` e os
links de fonte oficial de `renderProvenance` — os dois alvos **instrumentados**
que destruíam a página. Links externos inline no corpo (`<a rel="external">` no
meio do texto) **não** têm `target` porque não disparam evento: a abertura se
justifica pela medição, e sem medição não há motivo para mudar o comportamento de
navegação do leitor.

---

## O que o GA4 mede bem e o Clarity não

**O GA4 não tem este problema.** O gtag usa `sendBeacon`, e o evento chega mesmo
com a página sendo destruída — medido: `whatsapp_click=SIM` com navegação real,
já com as cinco dimensões junto. **O GA4 é a fonte de verdade dos eventos de
negócio deste portal.**

As chamadas ao Clarity ficam porque custam pouco e agora chegam. Mas o que o
Clarity faz melhor não são os eventos customizados, e sim:

- as **etiquetas** (`clarity("set", …)`), que chegam sempre — provado no payload;
- o **smart event nativo de clique**, que já captura o botão com o texto
  (`"Falar com o advogado"` apareceu no payload sem instrumentação nossa);
- **Reader type** e **Reading behavior**, filtros nativos exclusivos de portais de
  conteúdo, que para um acervo de 10 mil artigos respondem mais que qualquer
  evento manual — e não custam um byte.

---

## Eventos instrumentados

| Evento | Gatilho (seletor) | Navega? |
|---|---|---|
| `whatsapp_click` | `[data-wj-cta],.wa-float-link` | sim → `_blank` |
| `fonte_oficial` | `.prov a` | sim → `_blank` |
| `indice_click` | `nav.toc a` | **não** (âncora `#sec-…`) |
| `relacionado_click` | `[aria-labelledby=conteudos-relacionados] a` | sim, interno |
| `busca_interna` | `submit` em `.search-form` | sim, interno |

**Em `/buscar/` o Clarity não é injetado** (`if(!buscando)`), mas a página serve
`wa-float-link` e `search-form`. Por isso a guarda vive dentro de `ev()`:

```js
function ev(nome){ if(!buscando)W.clarity("event",nome); g("event",nome) }
```

O GA4 continua recebendo sempre, inclusive ali. Sem essa guarda, o evento entra
numa fila que **jamais será drenada**.

### O que fica de fora, de propósito

| API / evento | Por quê |
|---|---|
| `clarity("upgrade", …)` | **No-op provado.** `data/upgrade.ts`: `if (core.active() && config.lean)`, e `config.lean` é `false`. Nunca apareceu em payload. |
| `transport_type:"beacon"` | Conceito do Universal Analytics. O gtag não o reconhece e o repassa como `ep.transport_type` — dimensão sem sentido colada em todo evento. Nunca cobriu o Clarity. |
| `identify()` | Não há login. Fabricar id seria fingerprinting. |
| `metadata()` | Não documentada. Útil só para depuração, e o painel já dá o mesmo caminho. |
| `event(chave, valor)` de 2 args | Existe no fonte, sem contrato público de exibição. |
| `stop` / `pause` / `resume` | `stop` torna `core.active()` falso e **descarta todo evento seguinte**. |
| `consent(true/false)` v1 | Em depreciação; usa-se `consentv2`. O `consent(false)` do opt-out fica: é a forma documentada de apagar cookies. |
| `leitura_completa` | Redundante: Clarity tem *Reading behavior* nativo e o GA4 mede `scroll` a 90%. |
| `search` com `search_term` real | É exatamente o vazamento que a redação de `q` fecha. |

---

## Privacidade — o que não pode ser afrouxado

- **GPC honrado**: `navigator.globalPrivacyControl === true` desliga a medição
  antes de qualquer carga, e a página de opt-out diz isso ao visitante.
- **Redação de `q`**: em `/buscar/`, `page_location` sai com `q=@redigido@`. A
  redação do Loader alcança só `page_location`; o resto é a Data Redaction do
  stream, no painel.
- **`data-clarity-mask="true"`** no formulário de busca e
  **`data-clarity-unmask="true"`** no `<main>` (o texto público é conteúdo
  jurídico, sem PII, e sem isso o replay fica ilegível no modo Balanced, que
  mascara números — e o acervo é feito de artigos e leis numerados).
- **Guarda de bot**: nove User-Agents reais testados (WebView de WhatsApp,
  in-app de Instagram e Facebook, Chrome Android, Safari iPhone, Samsung
  Internet, o CUBOT que já foi falso positivo) — todos **passam**; Googlebot e
  GPTBot **barram**. Se mexer no padrão, refaça esse teste.

---

## Gates, e o que cada um consegue provar

| Ferramenta | O que prova | O que **não** prova |
|---|---|---|
| `tools/check-analytics-loader` | executa o JS em Node: guardas, seletores, redação, opt-out | nada sobre rede: nenhum script injetado roda, e **não há navegação** |
| `tools/check-analytics-contract` | hosts, CSP e as páginas servidas contra a constante | comportamento em runtime |
| `tools/check-medicao-no-navegador` | Chromium real com a CSP de produção; o cenário `RUNNER_PAYLOAD` **deixa a navegação acontecer** e afirma o conteúdo do payload | — |
| `tools/check-csp-hash-servido` | que o header servido autoriza o script servido | — |

**A armadilha do `check-analytics-loader`**: por construção ele não consegue
detectar "enfileirado e perdido porque a página navegou", que era o modo de falha
de todos os eventos. Foi por isso que 101 verificações verdes conviveram com zero
evento chegando. **Asserção sobre rede só vale no `check-medicao-no-navegador`.**

Duas armadilhas de implementação lá, ambas custaram tempo real:

1. O gate abortava `*.clarity.ms` (`r.abort()`). Com o `/collect` abortado, a fila
   **não é drenada** — dá falso negativo. O cenário de payload precisa de
   `r.continue()`, `postDataBuffer()` e **`gunzip`**: o payload do Clarity é gzip
   (`\x1f\x8b\x08`), e lido cru parece vazio.
2. Deixar passar significa **uma sessão real por execução** no painel. A sessão
   se identifica com `clarity("set","diagnostico","gate")` antes do clique.

---

## Publicar mudança de medição — a sequência, e o que cada passo evita

Mudar o `Loader` muda o hash da CSP **e** o HTML de todas as páginas.

1. `./tools/go-modern run ./cmd/generate-csp-nginx` — propaga o hash novo.
2. Republicar (`cmd/publish-v2-direct --allow-public-write`).
3. **`systemctl reload wikijuridica-nginx`** — sem isto o disco serve o script
   novo e o header recusa o hash antigo: o script morre **em silêncio**.
   `./tools/check-csp-hash-servido` é o que apanha.
4. **`tools/generate-page-content-revision --ressemear`** quando a mudança tocar
   algo **fora** dos blocos neutralizados. O `<script>` sem atributo é
   neutralizado; **`<meta>` e atributos não são**. Mudar `internal/seo` re-data o
   acervo inteiro e re-anuncia o sitemap ao Googlebot.
   `tools/deploy-publico:741` chama o gerador **sem** a flag — e `--desde-commit`
   fica proibido nesse deploy.
5. Trocar o binário do Go e **limpar `var/on-demand-cache`** — as rotas dinâmicas
   servem do cache e continuam entregando o script anterior com
   `X-Portal-Cache: HIT`.
6. `./tools/purge-edge-cache` **sem argumentos**. A purga por conteúdo é **cega
   para mudança de script** por desenho (deriva da comparação neutralizada, e
   devolve zero rotas). Medido: acervo novo na origem e borda servindo a versão
   anterior com `cf-cache-status: HIT` e `age: 18797` — a resposta viva declara
   `s-maxage=604800`, sete dias.

A purga é segura: cada resposta cacheada carrega a própria CSP, então página
velha vem com hash velho e funciona.

---

## Sonda de navegador polui o painel — e por isso ela se DECLARA

Diagnosticar medição exige carregar a página num navegador de verdade e deixar o
upload subir. Cada execução dessas vira **uma sessão real** no painel. Com ~25
sessões humanas por dia, uma tarde de diagnóstico distorce a leitura da semana.

A sonda **não pode** se marcar por header ou User-Agent próprio: o navegador é
que emite o UA, e um UA próprio faria a guarda de bot do próprio Loader barrar a
sonda — o teste mediria o nada. A saída honesta é a contrária: **declarar a
janela**, com apuração vinda do access.log.

```bash
tools/generate-medicao-artefato --motivo "por que a sonda rodou"
```

Ele grava em `data/ops/medicao_sessoes_artefato.jsonl` a janela, a contagem por
rota e o critério. O critério isola exatamente "navegador dirigido contra
127.0.0.1": UA de Chrome **e** `cf_ray=-` (não passou pela borda — visitante real
sempre tem `cf_ray`) **e** sem `warm=true`. Rode depois de cada sessão de
diagnóstico, e desconte a janela ao ler o painel do dia.

Primeira declaração: **2026-08-29, 03:22–04:09, 87 requisições** em 5 rotas.

---

## Leituras externas — o que expira se ninguém coletar

| Ferramenta | Como | Janela |
|---|---|---|
| Clarity Data Export API | `tools/collect-clarity-insights` (JWT em `.env.local`) | **1 a 3 dias**, 10 requisições/dia — o coletor faz **2 por execução** (dimensão pedida + `URL`) e se recusa a passar de **8/dia**. **Não exporta eventos.** |
| Bing Webmaster Tools | `tools/collect-bing-webmaster` (chave 32 hex, não confundir com o JWT) | histórico próprio |

A chave do Bing é `32` caracteres hexadecimais; a do Clarity é um **JWT**. Trocar
uma pela outra devolve **403 com corpo vazio** — sintoma que não diz nada.

### Clarity por URL — a segunda requisição, e o teto de 8 (2026-09-09)

**O defeito.** A unit `wikijuridica-medicao-externa.service` pede só
`--dimensoes Device`. Doze dias de série diziam quantas sessões humanas houve
por dispositivo e **nenhuma** dizia em quais páginas — a única linha com `URL`
era uma coleta manual de 2026-08-29. Sem isso o portal não sabe que página
recebe gente, e não compara o que o Clarity vê com o que a borda e o `nginx`
registram.

**O que mudou, sem tocar na unit** (o `daemon-reload` estava proibido por outra
frente publicando): `tools/collect-clarity-insights` faz agora **até duas
requisições por execução** — a das dimensões pedidas, byte a byte como antes
(`numOfDays=3&dimension1=Device`, mesmos cabeçalhos, mesmo esquema de linha), e
mais uma com `dimension1=URL`. `--sem-url` desliga a segunda; ela também não
acontece quando `URL` já está nas dimensões pedidas.

**Regras que a bancada `tools/test_collect_clarity_insights.py` trava** (19
testes, sem rede, `busca` injetada):

- **Teto próprio de 8/dia**, contra os 10 da API: as duas restantes ficam para
  `curl` manual. O cursor `data/ops/clarity_insights_state.json` conta **cada**
  requisição que chegou à API, inclusive 400/401/429 (a Microsoft as conta
  também), em `requisicoes` e na lista `requisicoes_hoje`. O guarda foi provado
  por mutação: sem ele, `test_teto_do_coletor` fica vermelho com `2 != 1`.
- **A falha da segunda requisição não muda o exit.** A unit é `Type=oneshot`
  com dois `ExecStart` sem `-` e `OnFailure=` para o dono: um exit 1 por dado
  opcional pularia o coletor do Bing e acionaria o alerta. A extra que falha
  fica no journal (`REPROVADO`) e em `ultimo_erro` do cursor. A primária mantém
  o contrato de sempre (exit 1 em 4xx/rede).
- **Orçamento de tempo:** 60 s para a primária, 40 s para a extra, ~1,5 s para
  carregar `content/pages.json` (83 MB, 337 MB de RSS medidos) — o pior caso
  cabe no `timeout 120` da unit.
- **Linha idêntica não se regrava:** mesma janela e mesmas `metricas` da última
  linha do mesmo dia UTC com as mesmas dimensões não entram de novo no ledger
  (a requisição conta mesmo assim). `pages.json` que mudou no meio do dia não é
  coleta nova e não regrava. A leitura do ledger para na primeira linha de dia
  anterior — sem isso a primeira execução do dia faria o parse do histórico
  inteiro (~80 MB de JSON por ano de linhas de URL).
- **A requisição é contada antes de qualquer derivação**, e a derivação nunca
  derruba a coleta: `pages.json` ausente ou ilegível (é reescrito pela
  publicação, e a unit roda enquanto outras frentes publicam) grava a linha de
  URL só com as `metricas` cruas e `derivacao_urls: {"erro": …}`, com
  `REPROVADO` no journal e o exit da primária preservado. Linha crua não é
  idêntica a linha derivada: a execução seguinte com o acervo de volta grava o
  `top_urls` do dia em vez de ser suprimida pela falha anterior.

**A linha de URL** entra em `data/ops/clarity_insights_daily.jsonl` com
`dimensoes: ["URL"]`, as `metricas` cruas e dois campos derivados:

- `top_urls`: até 100 entradas ordenadas por `sessoes` desc, `usuarios` desc,
  `url` asc. A URL vira **path** — sem esquema, host, query, fragmento, com
  percent-decoding; caixa e barra final ficam como vieram. Variantes que
  colapsam no mesmo path (`#sec-…`, `?utm_…`) somam-se e contam em
  `variantes`. `sessoes` é `totalSessionCount` (inclui bot; `sessoes_bot` ao
  lado); `usuarios` é a **soma** de `distinctUserCount` das variantes — teto,
  não contagem distinta. `paginas_por_sessao`, `tempo_total_s`, `tempo_ativo_s`,
  `scroll_medio` (ponderado por sessão) e os contadores de clique vêm das
  demais métricas. **A API não dá pageviews por URL** — o `pagesViews` das
  métricas de clique é o das sessões com aquele defeito — e nenhum campo finge
  que dá. `no_acervo` é "o path está em `content/pages.json`" (todo status,
  inclusive `noindex`; `/x` casa com `/x/`).
- `derivacao_urls`: `paths_distintos`, `linhas_sem_url` (o Clarity devolve uma
  linha com `Url: null`), `linhas_max_por_metrica`, `truncado_1000`,
  `acervo_paths`, `fora_do_acervo`.

**Por que `URL` sozinha e não `URL`+`Device`.** A doc oficial (relida em
2026-09-09) aceita até 3 dimensões, mas a resposta para em **1.000 linhas, sem
paginação e sem ordem documentada**. Cruzar com `Device` multiplica cada URL por
até 4 faixas e encosta no teto 3 a 4 vezes antes; um `top_urls` calculado sobre
resposta truncada em ordem desconhecida seria número inventado. Quando o teto
chegar, `truncado_1000: true` marca a linha e o `top_urls` passa a ser amostra.
**Armadilha de grafia:** a dimensão se pede como `URL` e volta como `Url` na
linha — o agregador casa a chave sem caixa.

**Primeira medição com a linha da unit, 2026-09-09 14:33 UTC**, janela de 3
dias: 122 linhas em `Traffic`, 147 sessões (15 de bot), **117 paths distintos**,
1 linha sem URL, `truncado_1000: false`, cursor de 1 para 3/8. Top 5 por sessões:
`/` 15 (9 bot, 22 usuários) · `/tributario/mei-alvara-taxas-municipais/` 3 ·
`/familia/o-que-curatelado-pode-fazer/` 3 ·
`/tributario/irpf-isencao-doenca-previdencia-privada/` 3 · `/leis/clt-art-484-a/`
2. Os 4 paths `fora_do_acervo` são índices de área (`/telecom-energia/`,
`/aereo/`, `/bancario/`, `/trabalhista/`): existem no ar, mas não constam de
`content/pages.json` — o campo diz o que diz, não "404".

**Custo que o consumidor paga:** a linha de URL tem ~223 KB (117 paths × 9
métricas + `top_urls`), e `tools/generate-evento-unificado` embute **todas** as
coletas do dia na linha diária do evento unificado. Com 1.000 linhas por
métrica ela chega perto de 2 MB/dia. O consumidor não foi tocado nesta frente;
quem o revisar deve embutir só `top_urls` e `derivacao_urls` da linha de URL.

---

## Painel — o que nenhum byte de código compra

**GA4 (não há backfill: o relatório só começa 24–48 h depois do registro):**

1. Registrar **QUATRO** dimensões — `lane`, `tipo`, `superficie`, `fontes` —
   como *event-scoped* no Admin. Sem isso elas são coletadas e **descartadas**.
   `content_group` **não entra na conta**: é dimensão nativa do relatório *Pages
   and screens* e reporta sozinha — foi por isso que `area` foi renomeada.
   Folga: 4 registros contra 50 slots event-scoped, e 6 parâmetros custom por
   hit contra o teto de 25 por evento.
2. Enhanced Measurement: `scroll`, outbound `click`, `view_search_results`,
   `file_download`.
3. **Data Redaction** do stream cadastrando `q` — a redação do Loader alcança só
   `page_location`; a do painel cobre `page_referrer`, `page_path`, `link_url` e
   `form_destination`.
4. Retenção para **14 meses** (retroativo).
5. `whatsapp_click` como **evento-chave**.
6. Vincular o **Search Console**.

**Clarity:** Settings → Smart events → New event → categoria **API events**. Se
`whatsapp_click` aparece na lista, o Clarity **recebeu** — é o teste que separa
"não chegou" de "não é exibido".

---

## Bing Webmaster por URL, pedido de rastreio e o que a API NÃO tem (2026-09-09)

**O defeito medido.** `GetCrawlStats` de 2026-09-08 diz `InIndex: 4667` para um
acervo de 10.141 páginas publicadas (11.039 ao fim do dia, depois da onda). O
IndexNow anuncia o que **mudou**; página que o Bing nunca rastreou não muda e
por isso nunca era anunciada. Os cinco blocos originais de
`tools/collect-bing-webmaster` respondem sobre o **site**; `GetPageStats` é um
topo capado (114 linhas), não o acervo. Faltava o dado **por URL**.

**O que a API entrega, sondado ao vivo em 2026-09-09** (base
`https://ssl.bing.com/webmaster/api.svc/json`, GET com `siteUrl` e `apikey`;
datas em `/Date(ms)/`): `GetQueryStats`, `GetPageStats`,
`GetRankAndTrafficStats`, `GetCrawlStats`, `GetCrawlIssues`,
`GetQueryTrafficStats`, `GetLinkCounts`, `GetUrlSubmissionQuota`
(`DailyQuota: 100, MonthlyQuota: 2200`), `GetUrlInfo?url=` (AnchorCount,
DiscoveryDate, DocumentSize, HttpStatus, IsPage, LastCrawledDate,
TotalChildUrlCount), `GetQueryPageStats?query=`, `GetPageQueryStats?page=`,
`GetUrlTrafficInfo?url=`. `SubmitUrlBatch` é POST JSON
`{"siteUrl": "...", "urlList": ["..."]}` com `apikey` na query, teto de 500
URLs por lote e resposta `{"d": null}` (doc oficial: learn.microsoft.com,
`IWebmasterApi.SubmitUrlBatch`; o exemplo JSON de lá grafa o caminho como
`SubmitUrlbatch` — a ferramenta usa `SubmitUrlBatch`, e um 404 no primeiro run
real fica no ledger com `http_status`).

**URL nunca rastreada** vem com `DateTime.MinValue`
(`/Date(-62135596800000)/`) em `LastCrawledDate` e `DiscoveryDate`;
`normaliza` grava `null`, nunca `0001-01-01`. URL que o Bing não conhece
responde 200 com os mesmos nulos, não 404.

**Limite de requisições, medido e não suposto:** 10 aceitas por janela de
60 s; a 11ª devolve `HTTP 400 {"ErrorCode":5,"Message":"ERROR!!! ThrottleHost"}`,
as recusadas não estendem a janela, e a 10ª aceita libera a próxima ~59 s
depois da primeira. O coletor segura o passo em 10 por 62 s (`Ritmo`), recua a
janela inteira e repete o item uma vez se um ThrottleHost chegar mesmo assim, e
corta por `--tempo-maximo` (padrão 100 s, abaixo do `timeout 120` da unit de
medição externa) gravando o cursor.

**Três blocos novos no mesmo ledger** (`data/ops/bing_webmaster_daily.jsonl`,
`schema: bing_webmaster_v1`, cada linha com `tipo` e `coletado_em`; linha
idêntica não se regrava, última observação por URL vence):

| bloco | tipo | como |
|---|---|---|
| `urlinfo` | `url_info` | 200 URLs por dia UTC, por *stride*: manifesto ordenado por `sha256(path)`, início `(ordinal_do_dia × 200) mod N`; ~51 dias para o acervo inteiro |
| `consulta_pagina` | `consulta_pagina` | as 50 consultas com mais impressões somadas em `GetQueryStats` → `GetQueryPageStats`; campos `Consulta` e `Pagina` |
| `pagina_consulta` | `pagina_consulta` | as 50 páginas com mais impressões em `GetPageStats` → `GetPageQueryStats`; idem |

O cursor `data/ops/bing_webmaster_state.json` guarda a janela do dia
(`urlinfo.feitas`), as chaves já consultadas dos dois blocos de enriquecimento
e o gasto (`requisicoes`): o run seguinte **do mesmo dia UTC** retoma de onde
parou, e o run cheio (~305 chamadas, ~31 min) fica na unit noturna.

**Pedido de rastreio: `tools/generate-bing-submit-batch`.** Seleciona até
`min(--max, DailyQuota, MonthlyQuota, 500)` URLs — cota lida ao vivo — entre
páginas publicadas que (a) não têm `url_info` com `LastCrawledDate` nos
últimos 30 dias ou (b) nunca tiveram submissão aceita; ordem determinística:
nunca rastreada (mais antiga publicada primeiro) → sem `url_info` → rastreio
com mais de 30 dias → rastreada há menos de 30 dias e nunca submetida; desempate
por `sha256(path)`. **A mesma URL nunca é submetida duas vezes em 30 dias**
(só submissão **aceita**, HTTP 200, conta; recusa fica no ledger com
`aceita: false` e a URL volta no dia seguinte). Ledger:
`data/ops/bing_submit_ledger.jsonl` (`schema: bing_submit_v1`, uma linha por
URL com `motivo`, `lote_id`, `http_status`, `aceita`, `resposta`, cota do dia).
`--dry-run` lista sem submeter nem gravar. Exit: 0 ok, 1 POST recusado ou ledger
não gravado, 2 sem credencial ou cota ilegível.

**Unit:** `ops/systemd/wikijuridica-bing-submit.{service,timer}` — 03:10 UTC
diário (`OnCalendar=*-*-* 03:10:00 UTC`, `Persistent=true`), coletor cheio com
`--tempo-maximo 2400` e depois a submissão; sem drop-in próprio, como as
vizinhas (o drop-in de prefixo `wikijuridica-.service.d/10-recursos.conf` a põe
em `wikijuridica_lote.slice`). Criada em 2026-09-09 **sem instalar**: a primeira
submissão real é decisão do dono.

**Testes, sem rede:** `tools/test_collect_bing_webmaster.py` (17: datas do
WCF, stride, cursor, topo, ritmo, throttle, teto de requisições e de tempo,
descarga por bloco) e
`tools/test_generate_bing_submit_batch.py` (11: seleção, prioridade, cota,
ledger, exit). A regra dos 30 dias é provada por **mutação**: com a linha
`if aceita_em is not None and (hoje - aceita_em).days < janela` removida numa
cópia (`WIKI_BING_SUBMIT_ALVO=<cópia>`), 3 testes ficam vermelhos.

**O que NÃO existe — e o que é proibido no lugar.** Não há endpoint de
"AI Performance", citações do Copilot ou tráfego de assistente na API do Bing
Webmaster: seis nomes sondados em 2026-09-09 devolveram 404. O painel web mostra
esse dado, mas **é proibido raspá-lo com o cookie de sessão do dono** — sessão
autenticada de pessoa não é canal de máquina, viola os termos do serviço e
expõe a conta que administra o domínio. Citação por IA se mede com dado nosso:
`data/ops/ai_citation_signal_daily.jsonl` e a borda (`verifiedBotCategory`),
como em `docs/ARQUITETURA_FIEL.md`. Referência apenas:
`data/ops/bing_webmaster_fora_do_indice_20260908.csv` (22 URLs exportadas à mão
do painel em 2026-09-08) — a lista viva sai do `url_info`, não desse arquivo.

---

## Previsão de audiência a 30/90/180 dias e ranking de áreas (2026-09-09)

**O que é.** `tools/generate-previsao-audiencia` ajusta, por série diária,
`log(y + 1) = a + b·t + Σ dummies(dia da semana)` por mínimos quadrados sobre
os últimos 60 dias (`--dias`) e projeta o valor diário esperado em 30, 90 e
180 dias com intervalo de **previsão** a 80 % e 95 % pela distribuição t
(graus de liberdade = n − posto(X)). A tendência sai como taxa semanal
`(e^(7b) − 1)`, com intervalo pelo erro-padrão de b. As séries e a regra de
leitura de cada uma — copiadas do painel e dos leitores canônicos, nunca
reinterpretadas:

| série | fonte e regra |
|---|---|
| `borda.organic_requests`, `borda.uniques` | `edge_traffic_daily.jsonl`, última linha por `date`; dia provisório pela regra do painel fica fora — **inclusive 2026-08-13**, que ficou preso em `organic_requests_basis: provisional_…` e nunca fechou |
| `bots.total`, `bots.valiosos`, `bots.<agente>` (perplexitybot, oai-searchbot, chatgpt-user, bingbot, amazonbot, googlebot, claudebot, claude-user, perplexity-user) | `edge_bot_agents_daily.jsonl` **só** por `tools/edgetelemetry.serie_saneada` (última linha por `(date, agent_key)`, 10 linhas impossíveis descartadas), campo `requests_sampled`; dia posterior ao último completo da borda é provisório, porque o ledger é cumulativo intradiário |
| `bing.impressions`, `bing.clicks` | `bing_webmaster_daily.jsonl`, `busca_diaria`, última coleta por `Date` |
| `bing.rastreio` (CrawledPages), `bing.indexadas` (InIndex) | idem, `rastreio_diario`; InIndex leva `teto_fisico` = páginas publicadas e a projeção acima dele vem marcada `acima_do_teto` |

Dia ausente é ausente, nunca zero; menos de 21 dias com dado na janela é
`sem_serie_suficiente`; 50 % ou mais de zeros é `serie_esparsa` (relata, não
projeta). Saída: `data/ops/previsao_daily.jsonl` (`schema_version:
previsao_v1`, uma linha por execução; linha idêntica à última fora `gerado_em`
não se regrava) e `data/ops/painel/previsao.json` (o mesmo objeto, que o painel
lê na seção **Previsão** — o painel só lê, nunca grava esse arquivo). Sem
`--gravar` a ferramenta só imprime (`--dry-run` idem). Unit
`ops/systemd/wikijuridica-previsao.{service,timer}`, diária às 07:10 UTC,
criada em 2026-09-09 **sem instalar**. Bancada:
`python3 tools/test_generate_previsao_audiencia.py` — 11 testes, sem ledger
real; a exclusão do dia provisório é provada por **mutação** (sem o guarda
`d not in provisorios`, a série sintética passa de n = 56 e +1,91 %/semana
para n = 58 e +6,82 %).

**Ranking de áreas** (`areas[]` da mesma saída): leituras dos 9 agentes
valiosos no ledger de **origem** (`data/ops/access/nginx-AAAA-MM-DD.jsonl`)
nos 14 dias completos, só `route_class ∈ {page, markdown}` com `status ∈ {200,
304}` (os 9.371 `outro/301` dos 14 dias — 26/08 a 08/09, agentes valiosos —
são redirect de barra final, e a segunda requisição já conta como 200), sem `bot_simulation` e sem `warming`; área =
primeiro segmento do path, `/redesocial/tema/<área>/` → a área do tema;
`paginas_publicadas` por primeiro segmento de `content/pages.json` (status
`published`); `valor_esperado = leituras × (1 + taxa semanal de bots.total)`,
e o campo `fator_serie` diz qual série deu o fator.

**Como ler — primeira execução real, 2026-09-09 16:35 UTC, janela 2026-07-12
→ 2026-09-09.** n por série: organic 24, uniques 32, bots.total e
bots.valiosos 36, oai-searchbot 36, chatgpt-user 33, bingbot 35, googlebot 35,
amazonbot 27, claudebot 25, Bing 28–29. Taxa semanal com IC80 e r² no log:
organic **+86,8 %** (36,5 a 155,6; r² 0,33) · uniques **+97,7 %** (68,9 a
131,4; r² 0,63) · bots.total **+52,1 %** (21,4 a 90,6; r² 0,33) ·
bots.valiosos +85,4 % (41,3 a 143,3; r² 0,30) · oai-searchbot +233,7 % (198,8
a 272,7; r² 0,88) · chatgpt-user +143,8 % (120,4 a 169,8; r² 0,86) · bingbot
+193,9 % (147,6 a 248,9; r² 0,72) · googlebot **−26,0 %** (−41,6 a −6,4; r²
0,16) · claudebot −40,2 % (−61,6 a −6,7) · bing.impressions +959 % (712 a
1.282; r² 0,87) · bing.clicks +163 % · bing.rastreio +140 % · bing.indexadas
+1.381 %. Projeção de 30 dias (ponto; IC80): organic 3,69 mi (0,28 a 47,8 mi)
· uniques 122 mil (19 mil a 767 mil) · bots.total 152 mil (10 mil a 2,23 mi)
· bing.impressions 111 mi. Sem série: `bots.claude-user` (10 dias com dado) e
`bots.perplexity-user` (3); esparsa: `bots.perplexitybot` (20 zeros em 28 —
antes do esquema v4, de 2026-09-02, a borda gravava 0 para ele). Top 10 áreas
(leituras em 14 dias; por página): glossario 3.421 (3,6) · imobiliario 2.593
(3,8) · previdenciario 2.027 (3,2) · consumidor 1.924 (3,0) · leis 1.802 (4,9)
· bancario 1.728 (3,7) · tributario 1.624 (3,4) · trabalhista 1.341 (2,5) ·
empresarial 1.335 (3,3) · procedimentos 1.307 (4,5); 33.178 leituras em 42
áreas do acervo, 58 fora dele; fator 1,521. Custo medido: 5,5 s de parede e
167 MB de RSS (host com load 10).

**O que NÃO é.** Não é destino, é tendência com barra de erro. A janela de 60
dias contém a **rampa de lançamento** (organic começa em 12/08 com 12 mil e
passa de 200 mil no fim de agosto), e um log-linear sobre rampa devolve taxa
alta, r² baixo e um 180 dias absurdo (1,1 × 10¹² requisições/dia) — o próprio
intervalo denuncia: o IC80 de 30 dias da borda abrange duas ordens de grandeza.
A taxa é sensível à janela: com `--dias 28` (só impressão) organic dá +78 %
(r² 0,3), **uniques cai para +7,7 % (−6,2 a 23,6)** e bots.total para +19,4 %
(2,9 a 38,7). A leitura útil é a de curto prazo com o intervalo, nunca o ponto
de 180 dias. O ponto é a mediana condicional (e^ŷ − 1), não a média. As
leituras por área vêm da origem: a borda absorve o que estava em cache, então
são piso, não total. E `bots.total` inclui SEO, scanner e social — é o
multiplicador que o plano mandou, e `bots.valiosos` fica ao lado para quem
quiser o outro.
