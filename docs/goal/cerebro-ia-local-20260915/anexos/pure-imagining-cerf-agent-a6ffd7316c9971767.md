# REFUTAÇÃO ADVERSARIAL — frente "ALAVANCAGEM IA-FIRST"
Sessão read-only, 2026-09-15. Toda evidência abaixo foi lida por mim no código/dado real.

VEREDITO: IMPLEMENTAVEL_COM_EMENDA.
Sobrevivem: P1, P2, P3, C1(parcial), C3, C4, C5, P16, P17.
Caem como escritos: **C2/P5/P6** (impossível por construção), P4 (bloqueado por ciclo de import + gate duplicado),
P11 (custeio refutado pelas flags do coletor), P12/P13 (dimensionados por contador que o repo documenta como mentiroso),
P15 (alvo sem produtor), §2 (+448/dia é artefato de janela).

---

## A1 — KILLER: C2/P5 é matematicamente impossível e refuta o gate do próprio P4

P5 põe `version: "sha256:<html_sha256>"` dentro do JSON-LD do HTML. P4 nasce com o gate
"versão emitida == sha256 dos bytes servidos".

`internal/publicrelease/publicrelease.go:812-817`:
```
htmlText, htmlReport := releaseHTMLForPage(page)
htmlHash := bytesSHA256([]byte(htmlText))
plan.ManifestRecords[index].HTMLSHA256 = htmlHash
```
O hash é do HTML renderizado a partir de `page` — que passaria a conter o próprio valor anunciado.
Satisfazer o gate exige `h = SHA256(f(h))`: busca de pré-imagem, inviável.
Geração N embute `h_{N-1}`; os bytes hasheiam `h_N ≠ h_{N-1}`. Nunca converge.

`reusableHTMLArtifactHash` (publicrelease.go:968-979) não amortece: ele descarta o hash reusado
quando o render fresco da página difere — e a página difere justamente porque `ContentSHA256` mudou.

MEDIDO POR MIM em `/autonomos/cobranca-prescricao/` (curl com UA do projeto + X-Warming-Request):
- bytes servidos = `3a8343a18a839395…`
- `public/.../index.html` = `3a8343a18a839395…`
- `published_manifest.html_sha256` = `3a8343a18a839395…`  ← os três batem
- gêmea anuncia `version: "sha256:6cf95fe42ca49770…"` ← diverge (M0 confirmado independentemente)
- `grep -c sha256` no HTML servido = **0** (hoje o valor NÃO está no artefato hasheado — é isso que P5 quebraria)

**E é pior que "gate vermelho": o gate de P4 fica VERDE mascarando o defeito.** Caminhe a geração N
depois de P5: o build lê o manifesto da geração N-1 → o JSON-LD carrega `h_{N-1}` → os bytes hasheiam
`h_N` → o manifesto grava `h_N` → o serviço reinicia → a gêmea anuncia `h_N`. O gate, como escopado
(versão da gêmea × bytes servidos), compara `h_N == h_N` e **passa** — enquanto o JSON-LD DENTRO
desses mesmos bytes diz `h_{N-1}`. O resultado é divergência permanente entre canais (gêmea `h_N`,
HTML `h_{N-1}`) exatamente da classe que o CLAUDE.md §7 descreve como "uma divergência entre eles
nenhum teste de paridade enxerga".

EMENDA MÍNIMA: C1 sim, **C2 não como escrito**. O html_sha256 só pode viver onde não entra no
próprio hash: gêmea, CSL-JSON, `/api/v1/citar`, cabeçalho HTTP. Se o HTML precisa de identidade,
emita `identifier` = `unique_intent_id` (estável) e, se quiser `version`, que ela seja hash do
**payload editorial**, não dos bytes do HTML — e então corrija a promessa de
`internal/content/content.go:186-188` ("baixar a página e recalcular o sha256 do HTML tem de dar o
mesmo número"), que passaria a ser falsa para esse campo.

## A2 — P5 reintroduz, em regime permanente, o defeito de lastmod que o repo já pagou

`tools/generate-page-content-revision:335-355` neutraliza `<script>` **sem atributo**. O comentário
é explícito: o JSON-LD "tem atributo, entao NAO casa — e ele e conteudo juridico, cuja mudanca
DEVE redatar a pagina".

Com o hash da geração anterior dentro do JSON-LD, **todo deploy** muda o JSON-LD das 11.106 páginas
→ `content_revised_at` avança no acervo inteiro → sitemap reanuncia tudo, para sempre.
A única saída é `--ressemear` em todo deploy (`tools/deploy-publico:1400-1401`: "regrava a linha de
base SEM carimbar data nova") — mas `--ressemear` é flag **da passada**, não da página: qualquer
deploy que leve texto editorial real teria a re-datação legítima suprimida junto, que é exatamente
o que o CLAUDE.md §6 proíbe. `internal/content/content.go:165-173` documenta a versão de 9.622 URLs
desse mesmo defeito ("o buscador aprende que o campo é ruído").

EMENDA: mesma de A1. Nenhum valor auto-referente no JSON-LD.

## A3 — "1 fonte de dado" em P4 está bloqueado por ciclo de import

`internal/publishedmanifest/publishedmanifest.go:24` importa `portaljuridico/internal/content`.
Logo `internal/content/anchorclaim.go:213-214` **não pode** importar `publishedmanifest`.
`internal/content` hoje importa só `contentstore` e `jsoncodec`.

EMENDA: pacote-folha (path → html_sha256) importado pelos dois, ou injeção do mapa no call site.
Nunca um segundo parser do manifesto dentro de `content`.

## A4 — não crie ferramenta paralela: o instrumento que já faz essa busca e esse sha existe e já roda

`tools/check-served-vs-manifest` já baixa os **bytes servidos** e compara com
`published_manifest.html_sha256`, separando `ok` / `render_de_servico` / `disco_incoerente` / `http`,
com UA interno + `X-Warming-Request`. E já está na lista de gates de `tools/run-daily-content:844`.

EMENDA: acrescentar a coluna "versão anunciada pela gêmea" a ESSE instrumento.
Criar `tools/check-versao-confere-com-artefato` é detector paralelo do mesmo assunto.

## A5 — "+448/dia" e o fechamento em 09-22 são artefato de janela

Medido por mim em `data/ops/bing_webmaster_daily.jsonl`, `tipo=rastreio_diario`, 33 linhas:
09-02 = 2.939 → 09-13 = 7.158, **11 dias** → **383,5/dia**, não 448.
448,0 é exatamente a média dos **últimos 7** deltas — janela diferente da dos extremos citados.
E ela é inflada por um outlier: 09-13 = **+858**, ~2× os vizinhos (420, 428). Sem ele, média de 6 dias = **379,7**.
Há dois dias de delta zero (08-29, 09-06) e **2026-08-21 está ausente da série**.
Fechamento real a ~380/dia: 3.948/380 ≈ 10,4 d → **09-23/24**.

Consequência para a régua: "InIndex cai contra o dia anterior → exit 1" compara **através do buraco**
quando falta um dia.

EMENDA: declarar a taxa com a janela; usar mediana dos deltas com o outlier marcado; gate ciente de
lacuna (exit 2 quando o dia anterior não existe).

## A6 — o §2 do plano derruba o próprio eixo VOLUME, e confunde "citação" com "demanda que responde"

O §2 mede que o Bing absorve a taxa fixa sem alavanca nossa, backlog 3.948. Páginas novas de
V1/V2/V3 entram **atrás** desse backlog: o retorno delas em citação no Copilot atrasa
(backlog + novas)/~380 dias. O plano nunca desconta isso e ainda assim chama V1/V2/V3 de régua de crescimento.
Observação que reforça: em 09-08/09-09 `CrawledPages` caiu a 80 e 79 e o InIndex seguiu subindo
(+349, +382) — o que sobe é processamento de backlog, não rastreio fresco.

E os ~23.000 são do painel do Bing = **um** consumidor (Copilot). Os 3.352 req/24 h da classe que
responde são majoritariamente outro canal: oai-searchbot e PerplexityBot têm índice próprio,
ChatGPT-User e Applebot buscam ao vivo. O teto do índice do Bing não é teto deles.

EMENDA: separar o numerador por consumidor. Declarar o teto do índice só para o numerador Copilot, e
justificar V1/V2/V3 pelo canal de busca ao vivo, onde a página é legível no dia em que sobe.

## A7 — o custeio de P11 é refutado pelas flags do próprio coletor

`cmd/collect-stj-acordaos/main.go:62`: `-max-recursos` default **100**, com a doc
"com Crawl-Delay 10 cada arquivo custa ~10s e o comando pesado tem teto de 1.800s".
P11 pede uma passada de "~361 req ≈ 1 h" = 3.610 s: **2× o teto de 1.800 s** e **3,6× o cap padrão**.
Como escrito, o comando para em 100 recursos.
(Confirmado o resto: 10 datasets em `internal/stjacordaos/fonte.go:22-33`; `-dataset` em `:58`;
cursor real em `data/corpus/jurisprudencia/stj-espelhos/cursor.json`.)

EMENDA: N invocações de ≤170 recursos sob `run-heavy-throttled`, retomando por cursor, com a
contagem por passada declarada.

## A8 — P13 não é "duas linhas", e P12 mede com o contador que o repo documenta como mentiroso

`tools/run-daily-content:471` embrulha cada gerador em `timeout 900`. Os geradores têm `-limite`
default 30 (`generate-lei-artigo-pages/main.go:183`, `generate-acordao-pages/main.go:185`).
Subir a env para perseguir as 2.488 do dossiê arrisca a morte em 900 s, que cai como
`registra "geracao:$gerador"` (falha), não como sucesso parcial.

E o SINAL DE SUCESSO de P13 é um contador que o repo documenta como mentiroso:
`run-daily-content:490-494` — "`paginas_geradas` conta o SHARD REMONTADO, que inclui tudo o que ja
estava no ar: em 2026-09-09 ele imprimiu 415 com ZERO paginas novas, e a fabrica ficou 5 dias parada
sem um unico vermelho".

Sobre P12 eu **verifiquei e retiro** a objeção maior: `cmd/generate-acordao-pages/main.go:206-220`
mostra que `-seco` imprime `relata(passada.Paginas, …)`, que é o lote que ESTA passada acrescentaria
— não o shard remontado. O que resta, e é real: `passada.Paginas` é limitado por `limite`, cujo
default é **30**. P12 como escrito ("V2/V3 com `--seco` para MEDIR o estoque real") mediria o próprio
teto, não o estoque.

EMENDA: P12 roda `-seco -limite <alto>` explícito, senão mede 30. P13 afere sucesso por diferença de
conjunto de `unique_intent_id` (`tools/check-onda-avanca`), nunca por `paginas_geradas`; e
`WIKI_LIMITE_*` calibrado para caber nos 900 s, ou backfill fora do runner diário.

## A9 — a fila de /redesocial/ nasce sem dreno nomeado (estoque que nada drena)

Retiro a forma forte: a métrica já diz "0 rota 404 … **e ausente da fila de produção**", então ela é
satisfeita por enfileirar, não por produzir. O que sobrevive é outra coisa, e é o padrão que este
repo já nomeou: P13 emite `/leis/…` e páginas de acórdão; **nada** sob `/redesocial/`. P15 é gate
read-only + ledger. Logo a fila `data/ops/demanda_de_agente_pendente.jsonl` nasce com entrada
(754 slugs distintos já medidos) e **sem nenhum passo do plano que a consuma** — o gate fica verde
porque a rota "está na fila", e a fila cresce para sempre.

EMENDA: nomear o dreno de `/redesocial/tema/<slug>` no mesmo passo que cria a fila, e fazer o gate
reprovar por FLUXO (entrada nova sem saída em N dias), não por "está enfileirado" — que é
exatamente a régua registrada em "gate vermelho por estoque que nada drena".

## A10 — superfície de abuso: tempestade de 404 chega ao Go sem cache, e a resposta do plano é um ledger

`/redesocial/` não tem location própria; cai em `@fallback`, que tem `proxy_cache wj_dyn`
(ops/nginx/wikijuridica.conf, bloco @fallback: `proxy_cache`, `proxy_cache_lock`,
`proxy_cache_background_update`). Mas **não há `proxy_cache_valid` em lugar nenhum do vhost**
(grep sobre o arquivo inteiro): o cache depende só do Cache-Control do upstream.
**MEDIDO POR MIM, não inferido** — `curl -i` com UA do projeto + `X-Warming-Request` em
`/redesocial/tema/nao-existe-xyz-teste/` devolveu `404` com **`Cache-Control: no-store`**.
Com `no-store` o nginx não guarda nada: **cada slug inexistente distinto chega ao processo Go, sempre**.
Já existem 754 slugs inexistentes distintos medidos. O limite é por tier
com burst 600 (`:681-687`) e as zonas casam `$http_user_agent`, que qualquer cliente escolhe.

Esta é a que a ordem do dono torna crítica: a rede social é a superfície **dinâmica** e a ordem
antecipa viralização.

EMENDA: antes de P13/P15, cachear o negativo (`proxy_cache_valid 404` escopado ao prefixo social) e
tornar o caminho de 404 barato. Ledger é medição, não defesa.

## A11 — o plano quase não arquiteta o que o dono mandou arquitetar

Ordem literal: rede social para bots de IA, com advogados, leigos, juristas, juízes, promotores,
discussão de casos reais, comentários, refutação e **o cérebro como moderador**.
O plano entrega P15 (um gate de link) e nada mais para isso.
`var/social/social.db` já tem `denuncias`, `fila_moderacao`, `ordens_judiciais`, com estados
`recebida_para_triagem` / `em_triagem` — triagem humana embutida no schema, enquanto a ordem em vigor
proíbe desenhar revisão humana como etapa de esteira.
`cmd/cerebro/comentarios.go:42-50` confirma o vocabulário fechado do ranking; a única produção do
cérebro em código é comentário de autoridade.

EMENDA: a rede social é frente própria, com medição própria; e os estados de moderação que pressupõem
triagem humana precisam de um decisor nomeado não-humano, ou contrariam a ordem em vigor.

## A12 — a janela de 14 dias é portão de calendário

"exit 2 enquanto a série < 14 dias" e "calibrados nos primeiros 14 dias" é período de espera.
A ordem da sessão: portão é PROVA MEDIDA, nunca calendário.

EMENDA: gatear por critério de estabilidade medido (dispersão da variação dia-a-dia abaixo de um
limiar pré-registrado), que pode fechar em 6 dias ou em 30.

## A13 — a emenda mínima de C4, como escrita, abre um buraco novo

`internal/pagemarkdown/render.go:484`: `b.WriteString(" — \`" + escapaTexto(urn) + "\`")`.
`escapaTexto` (blocks.go:100-113) escapa `\ \` * _ [ ]`. Tirar a chamada inteira de dentro do code
span remove também o escape de **crase**: uma URN com crase encerraria o span.

EMENDA: dentro de code span não escapar, mas alargar a cerca conforme a maior sequência de crases do
valor (regra do próprio CommonMark), ou normalizar/recusar URN com crase. Mantido o teste por mutação
imprimindo os spans ANTES da asserção.

## A14 — P5 precisa de controle positivo porque a falha dele é silenciosa

`internal/structureddata/structured_data.go:2528-2536` registra que, quando o schema reprova,
"o render simplesmente NÃO EMITIA o bloco … e nada no relatório de publicação acusava".
O plano acerta em exigir struct + schema no mesmo commit (`additionalProperties: false` confirmado em
`:2511`; struct em `:114-127`), mas não assere que o Article continue **existindo** depois.

EMENDA: após publicar, afirmar `"@type":"Article"` presente em N de M páginas servidas.

---

## O que NÃO consegui derrubar (verificado e de pé)
- C5: `AddResourceTemplate` existe em `go-sdk@v1.7.0/mcp/server.go:596`; a capability aparece sozinha
  em `:645-652`; o transporte já trata `case "resources/read":` lendo `params.uri`. Citações corretas.
- C3: `primeiroNaoVazio(page.Heading, page.Title)` confirmado em `internal/pagemarkdown/render.go:284`.
- C4: `escapaTexto(urn)` dentro de crases confirmado em `render.go:484`; `_` → `\_` em `blocks.go:100-113`.
- A trava do OAB é falso alarme para C2: `author_credential_test.go:39-41` conta sobre
  `semDadoEstruturado(html)` — JSON-LD está fora por construção. O plano já concluiu isso.
- P16: 5.815 linhas com **5.815 `public_path` distintos** em `content/legal_cocitation_index.jsonl`
  (minha primeira sonda usou a chave errada e deu zero — corrigido antes de virar achado falso).
- Fila: `extrair_dispositivos` pendente **34.067** hoje (plano dizia 34.118; está drenando).
- GERADORES: 5 no mapa (`run-daily-content:368-374`); os dois propostos só no comentário `:446-447`.
- `corpus_sem_acordao_para_a_urn` confirmado em `cmd/generate-lei-artigo-pages/main.go:247-253`.
- O `-seco` do gerador de acórdão NÃO herda a armadilha do shard remontado
  (`cmd/generate-acordao-pages/main.go:206-220`) — objeção retirada, ver A8.

---

## O que o advisor mudou

Quatro mudanças, todas por achado dele, e duas custaram medição nova:

1. **A9 foi derrubada na forma forte e reescrita.** Eu havia acusado "alvo sem produtor"; o advisor
   apontou que a própria métrica do plano diz "**e ausente da fila de produção**", ou seja, ela se
   satisfaz por enfileirar. Ship como estava me daria uma refutação limpa contra e custaria
   credibilidade em A1. Reescrita como "estoque que nada drena", com a emenda no gate por FLUXO.
2. **A8 perdeu metade — eu tinha inferido sem ler.** Fui medir
   `cmd/generate-acordao-pages/main.go:206-220`: `-seco` imprime `passada.Paginas` (o lote que a
   passada acrescentaria), não o shard remontado. Objeção retirada e substituída pela que sobrevive
   à leitura: `passada.Paginas` é limitado por `limite` default **30**, então P12 mediria o próprio
   teto. A armadilha do `paginas_geradas` continua valendo, mas contra P13, não contra P12.
3. **A10 deixou de ser inferência.** Eu havia deduzido de `proxy_cache_valid` ausente.
   Medi: `404` com `Cache-Control: no-store` → nginx não cacheia → cada slug inexistente chega ao Go.
4. **A1 ganhou a frase que a sustenta.** Não é só "gate vermelho": o gate de P4, como escopado
   (gêmea × bytes), fica **verde** comparando `h_N == h_N` enquanto o JSON-LD dentro desses bytes diz
   `h_{N-1}` — divergência permanente entre canais, da classe que o CLAUDE.md §7 diz que nenhum teste
   de paridade enxerga.

Também acatei o rebaixamento de A4 (de "duplica" para "estenda este, não crie paralelo": a
comparação é outra — manifesto×servido contra anunciado×servido — ainda que a busca e o sha sejam os
mesmos) e a ordem de severidade. A12 fica por último de propósito: piso de amostra é discutivelmente
medição, não calendário. Nada do que ele disse contradisse medição minha, então não houve
reconciliação a fazer.
