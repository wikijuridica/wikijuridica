# Varredura: como se mede o comportamento dos bots de IA com o dado que JÁ ESTÁ NO DISCO

Medido em 2026-09-15/16, entre 21:00 e 22:40 -03. Somente leitura.
Todo número foi produzido nesta sessão contra o disco vivo. Onde não medi, está
escrito "não medido" e o porquê. Amostra pequena vai declarada como "N de M".

---

## 0. Os três achados que reordenam a frente

### 0.1 O instrumento oficial de latência está cego para o conteúdo novo

`tools/measure-time-to-first-crawl:39` lê `data/editorial/first_published_at.json`,
que tem **10.107 chaves, data máxima 2026-08-27, mtime 2026-08-28 17:26**. O
manifesto de trabalho tem **11.106** rotas. **999 rotas publicadas são invisíveis
ao único instrumento de latência do repositório** — entre elas as 898 do lote de
2026-09-10. É o artefato órfão do P1b: **consertar o P1b conserta o instrumento de
latência de graça**.

Dois defeitos somados: `dias_entre()` (`:70-71`) opera em `date.fromisoformat`
— **granularidade de dia por construção**; e o `máx` de 39/40 dias que ele reporta
para os 10 bots é o **tamanho da janela de registro** (2026-08-05..2026-09-15 = 41
dias), artefato de borda, não medição.

### 0.2 Os bots NÃO reagem ao anúncio: chegam em VARREDURA AGENDADA

Histograma da hora UTC do primeiro contato (n = rotas com anúncio IndexNow):

```
gptbot                n=3608   01h:2500  02h:1018  03h:53   -> pico 01h = 69% do total
perplexitybot         n=5865   14h:2313  15h:1635  03h:473  -> pico 14h = 39%
cloudflare-ai-search  n=1773   16h:703   15h:494   06h:174  -> pico 16h = 40%
yandexbot             n=459    16h:128   07h:107   14h:101  -> pico 16h = 28%
bingbot               n=1492   23h:179   22h:138   21h:125  -> pico 23h = 12%
amazonbot             n=999    19h:72    13h:60    22h:60   -> pico 19h =  7%
anuncio IndexNow (hora UTC):  07h:4710  12h:1700  08h:1249  20h:1000  14h:993
```

`gptbot` concentra **97% dos primeiros contatos em 01h–02h UTC**. Sua banda
"apertada" de p05 4,2h → p95 6,0h **não é responsividade**: é a subtração entre
duas agendas fixas (lote de anúncio das 20h UTC menos varredura da 01h UTC = ~5h,
e o p50 medido foi 4,7h). O mesmo vale para perplexitybot (67% em 14h–15h) e
cloudflare-ai-search (68% em 15h–16h).

> **Consequência de engenharia, e é alavanca que o plano não tem: a latência é
> dominada pela DISTÂNCIA entre a hora em que publicamos e a hora da varredura de
> cada agente. Escolher a hora da publicação é a variável de controle — não
> "fazer o bot vir mais rápido".** A onda diária publica às ~07h UTC; gptbot varre
> às 01h UTC. São **18 horas de espera auto-infligida** para o agente que mais
> rastreia.

### 0.3 A origem NÃO prova ausência — e a magnitude é de ordem de grandeza

`gptbot` fez **36.609 requisições à origem em 2026-09-09**, o próprio dia da
publicação do lote, e **zero delas tocou as 898 rotas novas**. A borda registrou
**686 rotas do lote** para ele em 2026-09-10 (`crawl_coverage_state.paths_first_seen`).
`perplexitybot`: **855 rotas na borda contra 127 na origem — a origem vê 14,9%**.

---

## 1. As SEIS séries, suas convenções e as armadilhas de contagem

Não existe UMA série confiável. São seis fontes com convenções **diferentes e
incompatíveis**. Misturá-las é a armadilha documentada em
`tools/generate-bot-return-series:38-66`.

### 1.1 `/var/log/nginx/wikijuridica/access.log` — LATÊNCIA ZERO, resolução de SEGUNDO
- Linha crua nginx `wj_main`. **Incremental.** Legível: `id` → grupo `adm`; arquivo `www-data:adm 0660`.
- **Retenção medida**: `/etc/logrotate.d/wikijuridica` → `daily`, `rotate 30`, `maxsize 200M`.
  No disco: `access.log` (62 MB) + `.1` + `.2.gz`..`.30.gz` = **223 MB, de 2026-08-16 a hoje**.
- **Armadilha A — LOCALE.** `date -d '20 min ago' +%b` devolve `set` em pt_BR; o nginx
  escreve `Sep`. A comparação falha **em silêncio, devolvendo zero linhas**. Errei isto
  nesta sessão. **Sempre `LC_ALL=C date`.**
- **Armadilha B — `grep -oE` conta OCORRÊNCIA, não requisição.** O UA do PetalBot contém
  `PetalBot` e `petalbot` (na URL): medi 13+13 para 13 requisições. **Conte linha (`grep -c`).**
- **Armadilha C — a unit mente sobre a retenção.** `ops/systemd/wikijuridica-bot-telemetry.service`
  justifica a cadência de 30 min com "rotaciona de hora em hora, guarda 14 → 13h33min".
  Isso vale para `/var/log/nginx/*.log` — config do **projeto vizinho**
  (`/etc/logrotate.d/nginx`, cabeçalho "DIVORCIO HARDENING", `hourly`+`rotate 14`) — que
  **não casa o subdiretório**. A migração está em `tools/generate-bot-traffic-origin:11-16`.
  Comentário desatualizado, não defeito. A retenção real é 30 dias.

### 1.2 `data/ops/access/nginx-YYYY-MM-DD.jsonl` — ledger derivado, lag ≤ 1 h
- Produtor `tools/generate-origin-access-ledger:133` (`WIKI_NGINX_ACCESS_LOG`), timer
  `wikijuridica-origin-access-ledger.timer` **de hora em hora** (medido 21:08 → 22:08).
- `{ts, agent_key, path, status, origin_cache_status, ip_verificacao, ip_verificacao_metodo,
  bot_allow, superficie, route_class, warming, bot_simulation, remote_addr(_forma), cf_ray,
  referer, conditional_inm/ims}`, `origin_access_nginx_v2`. **Incremental, 1 linha = 1 req.**
- **É a série que usei em toda medição de latência abaixo.**
- **Armadilha D — rotação por data UTC.** Às 21:08 local de 09-15 já existia
  `nginx-2026-09-16.jsonl`. "Hoje" local **atravessa dois arquivos**. Leia sempre o par.
- **Armadilha E — `agent_key: null`.** UA não catalogado (medido: `AionBot/1.0` dentro de
  um UA de Chrome) vira `null`. Filtrar por `agent_key` **apaga bot novo** — que é o que
  `tools/generate-bot-registry-candidates` existe para achar.

### 1.3 `data/ops/access/access-*.jsonl` (ledger do processo Go) — **a âncora de publicação**
- Não serve para rastreio (o acervo não passa pelo Go), **mas grava o smoke do release**.
- Medido sobre o lote de 898 rotas em 2026-09-09: **1.817 linhas** =
  `898 route_class=page, warming=False, UA vazio, bot_class=self_simulation_probe` (smoke do
  release, **1 por rota**) + `898 route_class=markdown, warming=True,
  wikijuridica-cache-warm/1.0` (aquecimento de origem) + `21 wikijuridica-reload-check/1.0`.
- **O smoke cobriu 898 de 898 rotas em 15 segundos: 14:20:34Z → 14:20:49Z.**
  É o instante de publicação, preciso ao segundo.
- **Armadilha F — o smoke tem `warming: False`.** Filtrar tráfego próprio só por `warming`
  **conta o smoke do release como visita real**. Filtre também por `bot_class`/`bot_simulation`.

### 1.4 `data/ops/origin_bot_traffic_daily.jsonl` — **INCREMENTAL: SOME, não deduplique**
- Produtor `tools/generate-bot-traffic-origin` (regra declarada em `:70-85`), 1º ExecStart
  da `wikijuridica-bot-telemetry.service`, **a cada 30 min**.
- **Só descobri esta série pela skill `medir-bots`** (`/opt/wiki/.claude/skills/medir-bots`),
  que o enunciado mandava consultar. Ela não aparece em nenhum dos arquivos que eu havia lido.
- **CONFIRMADO com número**: 8.753 linhas, 582 chaves `(date, agent_key)`.
  **SOMANDO (correto) = 233.488. Última linha por chave (errado) = 11.744. Subcontagem 19,9×.**
  (A skill registra 38× no caso isolado do Googlebot: 7 onde havia 269.)
- **Armadilha G — 64 linhas têm `summable: false`**: são sentinelas
  `agent_key: "_zero_observation"`, `requests: 0`, marcando "janela observada, nada visto".
  Somá-las não muda o total, mas **elas são a diferença entre "medi e deu zero" e "não medi"**.
- Top somado: semrushbot 46.490 · amazonbot 39.077 · **gptbot 38.285** · perplexitybot 20.893
  · meta-externalagent 16.060 · oai-searchbot 11.196 · googlebot 9.379 · bingbot 6.667.

### 1.5 `data/ops/edge_bot_agents_daily.jsonl` — **CUMULATIVO: última linha por chave**
- Produtor `tools/generate-bot-agents-daily --dias 2`, timer de **30 min** (21:03 → 21:34).
- **CONFIRMADO com número**:
```
linhas ............................ 35.538      chaves (date, agent_key) ....... 757
linhas por chave ..... min 1 | mediana 56 | máx 96
SOMA de todas as linhas ... 1.000.150.479.083   (inclui o trilhão forjado)
SOMA da última por chave ..           489.003   (a leitura correta)
inflação ao somar linhas ......... 2.045.285x   | realista (só plausíveis) ... 48,0x
```
  Monotonicidade verificada em `('2026-09-02','applebot')`, 96 linhas:
  `5, 9, 13, 19, 27, 29 … 86, 86, 86` → **não-decrescente = True**. Cada linha é o
  TOTAL DO DIA até aquele instante.
- **Leitor obrigatório**: `tools/edgetelemetry.serie_saneada` (`edgetelemetry.py:270-311`).
  Rodei: `chaves=757, descartadas=10`.
- **Armadilha H — a chave é `requests_estimated`, não `requests`.** `.get('requests')`
  devolve **0 para todos** e parece "nenhum bot passou" (skill `medir-bots` §2).
- **Armadilha I — denominador inflado.** `edgetelemetry.acervo_urls:87-116` conta `<loc>`
  com `findall` **sem deduplicar** → **12.651**. Distintas reais: **11.147**. O teto
  `MAX_REQUISICOES_POR_URL_DIA × acervo` fica **13,5% mais frouxo**. `measure-crawl-coverage:238`
  usa `set()` e reporta `sitemap_total: 11.142`. **Dois instrumentos do mesmo repo discordam
  do tamanho do acervo em ~1.509 URLs.** Causa em §6 — e é POR DESENHO.
- **Retenção da fonte**: `httpRequestsAdaptiveGroups` da Cloudflare = **8 dias**
  (`tools/measure-crawl-coverage:110`, `RETENCAO_DIAS = 8`, medido contra a API: dia mais
  velho devolve `code: quota`). **É o único teto de espera de causa física externa.**

### 1.6 `crawl_coverage_daily.jsonl` + `crawl_coverage_state.json` — cobertura por URL, lag ≤ 24 h
- Produtor `tools/measure-crawl-coverage`, timer **1×/dia** (medido 2026-09-15 01:12).
- **CUMULATIVO E DUPLICADO**: 2.858 linhas para **420** chaves `(date, crawler)`;
  **410 (97,6%) com mais de uma linha**; mediana 8, **máx 21**.
- **Leitor obrigatório**: `tools/crawlcoverage.serie_saneada` (`crawlcoverage.py:30-52`):
  dedup por `(crawler,date)` mantendo a última; **v2/v3 vence v1** (v1 conta string de UA;
  inflação medida de **258×** no caso Googlebot: 2.053 de 2.061 linhas eram `bot_sim=true`).
- **DO DIA (somáveis)**: `paths_requested_that_day`, `new_sitemap_urls_that_day`.
  **ACUMULADOS (nunca somar entre datas)**: `cumulative_sitemap_coverage`, `cumulative_coverage_pct`.
- **`crawl_coverage_state.crawlers_verified.<bot>.paths_first_seen`** = `{rota: dia da 1ª visita}`.
  Medido: amazonbot 31.870 · gptbot 19.001 · perplexitybot 18.148 · oai-searchbot 12.254 ·
  yandexbot 11.662 · bingbot 7.962 · googlebot 7.475 · googleother 3.305 · claudebot 2.799 ·
  chatgpt-user 1.848.
- **Armadilha J — use `crawlers_verified`, NUNCA `crawlers`.** O balde `crawlers` está
  congelado (`identity: user_agent_unverified`, contaminado por sonda própria) — skill §4.
- **Armadilha K — só 10 bots**, e não os que mais aparecem na origem:
  `cloudflare-ai-search`, `petalbot`, `semrushbot`, `ahrefsbot`, `applebot`, `mj12bot`,
  `dotbot` **não existem** nesta série.
- **Armadilha L — rota lixo.** `amazonbot.paths_first_seen` contém `'/):'` e
  `'/.well-known/agent-skills/index.json):'` — artefato de parse do produtor.
- **Armadilha M — zero não é ausência.** Linha de yandexbot em 2026-09-15 traz
  `no_groups_returned: true` **e** `paths_requested_that_day: 0`: a API não devolveu grupo.

### 1.7 `ai_citation_signal_daily.jsonl` — **INCREMENTAL: SOME por (date, layer, key)**
- Produtor `tools/measure-ai-citation` (1.017 linhas). 987 linhas para **374 chaves**,
  mediana 2, máx 5. **`summable: true` em 987 de 987.** Deduplicar SUBCONTA.
  `window_fields_are_summable: false` → `distinct_ips_in_window` e `distinct_paths_in_window`
  **não se somam**.
- Medido agora (36 dias, 2026-08-11..2026-09-15):
```
requests 94.931 | is_citation_interest 40.481
camadas: treinamento 54.450 | crawl 37.762 | fetch 2.638 | clique_de_volta 81
top: amazonbot 37.775 | perplexitybot 20.768 | meta-externalagent 15.302 | bingbot 6.485
     oai-searchbot 4.329 | applebot 2.875 | chatgpt-user 2.507 | yandexbot 2.031
```
- **A ressalva é do próprio arquivo**: toda linha traz `is_citation_count: false` e
  `is_lower_bound: true`. Os ~40 mil de `is_citation_interest` são **limite inferior de
  INTERESSE, jamais contagem de citação**. A única camada que mede humano chegando de
  assistente é `clique_de_volta`: **81 requisições em 36 dias**. O arquivo lista cinco
  coisas que declaradamente não mede (citação sem clique — "provavelmente o MAIOR
  componente, zero-clique ~68%", resposta por memória do modelo, fetch descartado, clique
  com referer suprimido, conversão).

### 1.8 `bot_return_daily.jsonl` + `bot_return_state.json` — derivado, reescrito por inteiro
- `tools/generate-bot-return-series`, 3º ExecStart da bot-telemetry (prefixo `-`).
- **NÃO é append-only**: reescrito byte a byte a cada execução (`:28-33`), de propósito,
  para não herdar o cumulativo. 757 linhas.
- **É a única série desenhada contra ABANDONO.** Cobertura acumulada só cresce e por
  construção nunca acusa abandono (GPTBot caiu a 1 req/dia em 08/08 e meta-externalagent
  sumiu em 23/08 sem alarme).
- **Armadilha N**: `requisicoes: 0` com `sem_cobertura_por_url` presente **não é ausência** —
  o campo existe porque zero afirmaria algo que não foi medido.

### VEREDITO da §1
> **Para "o bot X voltou e leu a rota nova" use o PAR: `data/ops/access/nginx-*.jsonl`
> (quem bateu na origem, no segundo) × `crawl_coverage_state.paths_first_seen` (quem bateu
> na borda, no dia).** Nenhuma sozinha basta: a origem vê 0 do gptbot no lote e a borda vê
> 686; a borda não conhece cloudflare-ai-search e a origem registra 897 rotas dele.

---

## 2. LATÊNCIA REAL publicar → observar rastreio, POR AGENTE — MEDIDA

### 2.1 O lote e a âncora, ambos provados

Diff do manifesto: `a286f5e6` (09-08, 10.141) → `6d3623c2` (09-10, 11.039) = **898 rotas
novas** (`/jurisprudencia` 865, `/sumulas` 29, `/noticias` 3, `/diarios` 1).
Worktree hoje: 11.106 → **67 rotas nunca commitadas** (o `M` de 5 dias do P1b).

**Âncora autoritativa**: smoke do release no ledger do Go, **898 de 898 rotas em 15 s**:
`2026-09-09T14:20:34Z → 14:20:49Z`.

**O commit NÃO é o instante da publicação**: `6d3623c2` é `2026-09-10T11:29:54Z` —
**21h 09min depois**. **O mtime também não**: `public/jurisprudencia/stj-iac-1/index.html`
tem mtime `2026-09-10T00:00:00Z` exato (carimbo determinístico do build; ctime é 09-15 12:28).
*(Nota: "zero 404 no lote" NÃO bounda a publicação — bot não pede URL que não descobriu.)*

### 2.2 Latência sobre o lote limpo de 898 rotas, âncora por rota, ORIGEM

```
agente                  rotas   cob.%        p05        p50        p95
cloudflare-ai-search      897   99,9%      85min       1,6h       1,8h
petalbot                  770   85,7%      26,4h      75,4h     102,8h
amazonbot                 315   35,1%      67,8h     100,7h     143,3h
semrushbot                269   30,0%      96,9h     145,5h     152,9h
yandexbot                 180   20,0%       5min      22,7h      41,4h
perplexitybot             127   14,1%      22,5h      22,6h     117,4h
oai-searchbot              57    6,3%      41,3h      76,5h     137,6h
applebot                   13    1,4%      75,1h     130,9h     153,6h
chatgpt-user                1    0,1%      92,9h      92,9h      92,9h
gptbot / googlebot / bingbot / claudebot / googleother:  ZERO no lote, na ORIGEM
```

**`cloudflare-ai-search` é a CDN, não um assistente de terceiro.** UA medido:
`Cloudflare-AI-Search-External (https://developers.cloudflare.com/ai-search; ai-search@cloudflare.com)`,
`ip_verificacao: unverifiable/none`, classificado `"search"` em `tools/botagents.py:258`,
mapeado em `ops/nginx/wikijuridica.conf:251`. É o Cloudflare AI Search indexando o próprio
cliente. **Pertence à tabela, nunca à manchete.**

### 2.3 O mesmo lote na BORDA (`paths_first_seen ∩ lote`)

```
perplexitybot   855   09-09:406  09-10:443  09-11:2  09-12:4
gptbot          686   09-10:686
amazonbot       527   09-11:58 09-12:151 09-13:171 09-14:132 09-15:15
oai-searchbot   226   09-09:1 09-10:43 09-11:20 09-12:127 09-13:29 09-14:6
yandexbot       215   09-09:56 09-10:99 09-11:42 09-12:2 09-13:11 09-14:5
googlebot 1 | chatgpt-user 1 | bingbot 0 | claudebot 0 | googleother 0
```

### 2.4 Lote CONTAMINADO (10.304 rotas com anúncio IndexNow) — só como contraste

`data/ops/indexnow_url_state.jsonl`: **13.649 linhas**, uma por URL, `submitted_at` em
**microssegundo**, 2026-09-04..2026-09-15. Cruzado com o primeiro hit por `(agent_key, path)`:
p50 → cloudflare-ai-search 105min · gptbot 4,7h · ahrefsbot 13,0h · yandexbot 7,9h ·
perplexitybot 27,3h · bingbot 49,8h · chatgpt-user 50,5h · googlebot 55,9h · oai-searchbot 58,2h ·
semrushbot 78,1h · petalbot 83,0h · amazonbot 103,5h · applebot 123,1h. mj12bot e claude-user: 0.

**NÃO use estes números como latência.** Os lotes de 1.000 URLs das 07:4x são **re-anúncio de
URL antiga**: misturam 1º rastreio com re-rastreio. E §0.2 mostra que as bandas apertadas são
subtração entre agendas. Serve só para mostrar que o instrumento existe e roda em segundos.

### 2.5 Agentes NOMEADOS pelo dono — presença na origem, 2026-09-01..09-16

```
agente                total    dias   último contato na ORIGEM
gptbot                37.750     13   2026-09-15T02:05:34Z   (36.609 = 97% num só dia, 09-09)
perplexitybot         20.412     15   2026-09-15T23:56:26Z
amazonbot             12.629     13   2026-09-15T22:32:06Z
oai-searchbot          8.693     15   2026-09-15T23:58:16Z
bingbot                3.815     16   2026-09-16T00:05:25Z
chatgpt-user           1.687     16   2026-09-16T00:01:50Z
googlebot                417     15   2026-09-15T23:54:27Z   (a maior parte dele vai pela borda)
meta-externalagent        31      6   2026-09-15T08:04:32Z   ** COLAPSO **
claude-user               27      5   2026-09-11T13:07:01Z
claudebot                  4      1   2026-09-08T00:34:38Z   ** AUSENTE **
```

- **`meta-externalagent`**: 15.302 requisições na série de 36 dias, mas **31 em 16 dias** na
  origem, em 6 dias distintos. Consistente com o abandono de 23/08 registrado em
  `generate-bot-return-series`. **É achado, não silêncio.**
- **`claudebot`**: 4 requisições, num único dia (09-08), nada desde então. Zero no lote, na
  origem e na borda. `claude-user`: 27, último 09-11.
- **`gptbot`**: varredura de 36.609 requisições em 09-09 (dia da publicação) **sem tocar
  nenhuma das 898 rotas novas na origem**; pegou 686 delas na borda em 09-10.

### 2.6 RESPOSTA À ORDEM DO DONO
> "não tem desculpas de janelas de horas para medir"

**Correto, e medido.** Com o dado já no disco: `cloudflare-ai-search` fecha 99,9% de um lote
de 898 rotas em **menos de 2 horas** (p95 = 1,8h); `yandexbot` bate em **5 minutos** no p05.
O que **não** responde em minutos: `amazonbot` (p50 100,7h), `petalbot` (75,4h),
`applebot` (130,9h) — **e o número é esse, com fonte**, não desculpa.
**Nenhuma dessas medições exigiu esperar**: todas saíram de arquivo local em minutos.
**O único teto de espera de causa física externa é a retenção de 8 dias da Cloudflare.**

---

## 3. O que se verifica IMEDIATAMENTE depois de publicar, sem depender de bot de terceiro

Nove provas. As sete primeiras rodei nesta sessão contra `/jurisprudencia/stj-iac-1/`.

| # | prova | comando | esperado | medido agora |
|---|---|---|---|---|
| 1 | origem 200 | `curl -s -o /dev/null -w '%{http_code} %{size_download}\n' -A "$UA" -H 'X-Warming-Request: true' -H 'Host: wikijuridica.com.br' http://127.0.0.1:8088$R` | 200, ≤ 51200 B | **200, 25.311 B** |
| 2 | gêmea Markdown | idem + `${R}index.md` | 200 `text/markdown` | **200, 11.351 B, `text/markdown; charset=utf-8`** |
| 3 | borda 200 | `curl -sI -A "$UA" -H 'X-Warming-Request: true' https://wikijuridica.com.br$R` | `HTTP/2 200` | **200, `cf-cache-status: HIT`, `age: 27822`, `s-maxage=604800`** |
| 4 | rota no sitemap | `grep -l "<loc>…$R</loc>" public/sitemaps/*.xml \| wc -l` | 1 ativo (+ shards em carência) | **2** — `pages-0100` está em CARÊNCIA (§6) |
| 5 | lastmod | `grep -A1 -F "$R</loc>" public/sitemaps/*.xml \| grep lastmod` | data da publicação | **`2026-09-10`** ✓ |
| 6 | IndexNow aceitou | `tail -1 data/ops/indexnow_direct_submissions.jsonl \| python3 -m json.tool` | `http_status 200`, `success true`, `ownership_proof_verified_over_http true` | **200 / true / true, 6 URLs, `2026-09-15T15:32:40.521044Z`** |
| 7 | a URL exata no lote | `grep -F '"url": "https://wikijuridica.com.br'$R'"' data/ops/indexnow_url_state.jsonl \| tail -1` | linha com `submitted_at` | 13.649 linhas, per-URL |
| 8 | paridade humano×bot | `./tools/check-what-bots-see` | exit 0 | não rodado nesta sessão (sai à rede) |
| 9 | replay sem esperar | `WIKI_EFEITO_NOS_BOTS_LOG=<fixture> ./tools/check-efeito-nos-bots` | veredito sobre log gravado | flag confirmada em `check-efeito-nos-bots:106` |

`$UA` = `Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)`.
Com `X-Warming-Request: true` a sonda sai da métrica
(`regras_de_exclusao_de_trafego_proprio`, `ai_citation_signal_daily`).

`check-what-bots-see` compara **SHA-256** (não inspeção de código): prova anti-cloaking.
Contra `127.0.0.1` usa o UA do bot real (testa o roteamento por classe do nginx); contra host
remoto troca para `wikijuridica-superficie-probe/1.0 (simula: <perfil>)` com
`X-Warming-Request: true` — correção de 2026-09-03, porque a **borda não lê `X-Bot-Simulation`**
e a Cloudflare contava a sonda como visita real de Googlebot.

`WIKI_EFEITO_NOS_BOTS_LOG` (`:106`) e `WIKI_NGINX_ACCESS_LOG` (`generate-origin-access-ledger:133`)
apontam os dois para fixture. **É o atalho que a ordem do dono pede**: o veredito se exercita
contra log já gravado, sem esperar bot nenhum.

---

## 4. O log de origem NÃO prova ausência — CONFIRMADO

| mecanismo | número medido |
|---|---|
| **cache de borda** | gptbot **686 rotas na borda, 0 na origem**; perplexitybot **855 × 127 = origem vê 14,9%**. Schema: *"origem <= borda SEMPRE: HIT na borda nao toca a origem"*. `s-maxage=604800` medido no header |
| **rotação** | origem guarda **30 dias**; o ledger `data/ops/access/` não rotaciona. Mas a **BORDA** retém só **8 dias** — a janela curta hoje é a da borda, invertendo a premissa antiga |
| **agrupamento por UA** | `agent_key: null` para UA não catalogado (`AionBot/1.0` dentro de UA de Chrome) |
| **aquecimento próprio** | já foi **93,2% do tráfego da borda** (29.552 de 31.708; audiência real 2.156) — skill §7 |

**Qual fonte prova PRESENÇA:**

| afirmação | fonte | por quê |
|---|---|---|
| "o bot X pediu a rota R" | `access/nginx-*.jsonl` com `ip_verificacao ≠ unverifiable`, ou `crawl_coverage_state.paths_first_seen[X][R]` | faixa de IP oficial ou `verifiedBotCategory` |
| "o bot X veio hoje" | `bot_return_state.json`/`bot_return_daily.jsonl` `veio_hoje` | derivado da borda, que vê HIT e MISS |
| "o bot X leu N rotas no dia D" | `edgetelemetry.serie_saneada` (última por `(D,X)`) | nunca somando linhas |
| "quantas requisições o bot X fez à origem" | `origin_bot_traffic_daily.jsonl` **SOMADO** | incremental; a última linha subconta **19,9×** |
| "um humano chegou de assistente" | `ai_citation_signal_daily`, camada `clique_de_volta` | **81 em 36 dias** — e mesmo ela é limite inferior |
| **"o bot X NÃO veio"** | **nenhuma fonte prova isto** | ausência na origem = cache; na borda = retenção de 8 dias + `no_groups_returned` |

**Corolário**: nenhum gate pode reprovar por "bot não veio" lendo só a origem.

**Correção de uma suspeita minha, para não propagar erro**: quase reportei as faixas de IP
como vencidas. **Não estão.** Cada arquivo tem DOIS campos: `fetched_at` (nossa coleta) e
`creation_time_upstream` (data em que o OPERADOR publicou).
`./tools/check-bot-ip-ranges-frescor` → **OK, 14 faixas, a mais velha com 0,62 dia,
limiar 3 dias, exit 0**. O que É verdade e ninguém mede: `creation_time_upstream` de
`perplexitybot.json` é **2025-02-07** (19 meses, **8 prefixos**) e de `bingbot.json` é
**2024-01-03** (20 meses, 28 prefixos). O gate mede a NOSSA coleta e ficaria verde para sempre
com lista upstream de uma década. → lacuna **L4**.

---

## 5. A LACUNA — o instrumento que falta

### 5.1 Nomeando: não existe COORTE

*"As N páginas que publiquei foram descobertas e lidas, e por quem?"* — nenhuma ferramenta responde.

| ferramenta | responde | por que não serve |
|---|---|---|
| `measure-time-to-first-crawl` | agregado por bot | numerador congelado em **10.107 de 11.106**; granularidade de dia; máx = tamanho da janela |
| `crawl_coverage_state.paths_first_seen` | rota × bot | só **10 bots**; refresco **1×/dia**; sem instante |
| `generate-bot-return-series` | bot × dia | **não tem rota** |
| `check-efeito-nos-bots` | Googlebot agregado | exige **14+14 dias** e ≥100 req autenticadas em cada janela; antes disso imprime INCONCLUSIVO |
| `check-efeito-deploy-bots` | pré/pós deploy | agregado por bot, não por rota |
| `measure-ai-citation` | interesse por agente/dia | sem rota, sem coorte |
| `check-crawl-coverage-stall` | cobertura parou? | não separa "não achou" de "achou e recusou" |

**Ninguém consegue dizer hoje quem leu as 898 rotas de 2026-09-10.** Eu consegui — cruzando
cinco arquivos à mão, em ~40 min de sessão. Isso é o instrumento que falta.

### 5.2 Especificação: `tools/measure-coorte-de-publicacao`

```
tools/measure-coorte-de-publicacao \
  --coorte-de <arquivo> | --diff-manifesto BASE..HEAD | --desde-indexnow TS \
  [--json] [--serie]
```

**ENTRADA — três formas, todas já disponíveis**: `--diff-manifesto a286f5e6..6d3623c2` → 898
rotas (provado); `--desde-indexnow <ts>` → URLs de um lote; `--coorte-de <arquivo>`.

**ÂNCORA por rota, na ordem (a primeira que existir):**
1. **Smoke do release** — `access-*.jsonl` com `bot_class: self_simulation_probe`, 1 req/rota.
   **Precisão de segundo, provado: 898/898 em 15 s.**
2. `indexnow_url_state.jsonl:submitted_at` — microssegundo, 13.649 linhas.
3. Primeira resposta 200 na origem.
4. `first_published_at.json` — **só depois do P1b**, e ainda assim só dia.
**Nunca o commit** (erra 21h09, medido) e **nunca o mtime** (carimbo determinístico 00:00:00Z).

**SAÍDA — uma linha por `(coorte, agent_key)`:**
```json
{"schema_version":"coorte_de_publicacao_v1","coorte_id":"…","coorte_n":898,
 "ancora":"release_smoke","ancora_ts":"2026-09-09T14:20:34Z","janela_s":123456,
 "agent_key":"cloudflare-ai-search","identidade":"unverifiable",
 "fonte":"origem|borda|ambas","rotas_tocadas":897,"cobertura_pct":99.9,
 "latencia_s":{"p05":5100,"p50":5760,"p95":6480,"max":…},
 "hora_utc_do_primeiro_contato":{"16":703,"15":494},
 "status":{"200":1310},"rotas_nunca_tocadas":["…"],
 "limite":"superior: HIT na borda esconde contato anterior; origem <= borda SEMPRE",
 "cobertura_borda_ausente":false}
```

**REGRAS (cada uma paga uma armadilha medida):**
- Origem por `access/nginx-*.jsonl` **+ o arquivo do dia UTC seguinte** (D); fallback ao log
  vivo com `LC_ALL=C` (A).
- Borda por `crawlcoverage.serie_saneada` e `edgetelemetry.serie_saneada` — **nunca reimplementa
  dedupe** (1.5, 1.6). Volume de origem por `origin_bot_traffic_daily` **SOMADO** (1.4).
- Chave da borda é `requests_estimated`, não `requests` (H). Balde `crawlers_verified`, nunca
  `crawlers` (J).
- Conta **linha**, nunca ocorrência de regex (B). Exclui tráfego próprio por `warming` **E**
  `bot_class`/`bot_simulation` (F).
- Agente ausente na borda → `cobertura_borda_ausente: true`, **nunca 0** (N, M).
- `agent_key: null` → balde `nao_classificado` com amostra de UA, alimentando
  `generate-bot-registry-candidates` (E).
- **`hora_utc_do_primeiro_contato` é campo de primeira classe** — é o que revela varredura
  agendada (§0.2) e é a variável de controle da latência.
- **Sem janela mínima.** Roda 1 min depois de publicar; `janela_s` diz quanto passou.
  **Nunca "INCONCLUSIVO".**
- Série em `data/ops/coorte_de_publicacao.jsonl`, **derivada e reescrita por coorte** (modelo
  `bot_return_daily`), nunca append cumulativo.

**GATE PAREADO `coorte-descoberta`** (`internal/checks/checks.go`): reprova quando, decorrido
o prazo derivado da **p95 histórica DO PRÓPRIO AGENTE** (nunca calendário fixo), a cobertura
da coorte fica abaixo do piso da coorte anterior. Piso e prazo saem da série. É assim que o
portão é **prova medida**, não calendário.

**DERIVADO IMEDIATO — `tools/sugerir-hora-de-publicacao`**: da distribuição de
`hora_utc_do_primeiro_contato` por agente, escolhe a hora de publicação que minimiza a soma
ponderada das esperas. Hoje a onda publica ~07h UTC e gptbot varre 01h UTC: **18 h de espera
auto-infligida** no agente que mais rastreia.

### 5.3 As outras cinco lacunas
- **L1 — `first_published_at.json` órfão** (P1b). Congela o instrumento de latência em 10.107
  de 11.106. Consertar o P1b desbloqueia sem código novo.
- **L2 — `check-efeito-nos-bots` exige 14+14 dias.** É a "janela de horas" proibida, elevada a
  semanas. Conserto: **acrescentar** o veredito de coorte (§5.2), mantendo o de 14 dias como
  série de longo prazo. O gate já tem `OnFailure` → alerta ao dono.
- **L3 — `crawl_coverage` roda 1×/dia** (timer 01:11 local): `paths_first_seen` com até 24 h de
  atraso. Nada impede `measure-crawl-coverage` sob demanda (consulta GraphQL) — o runbook de
  publicação deve chamá-lo, não esperar o timer.
- **L4 — nenhum gate mede `creation_time_upstream`.** perplexitybot upstream de 2025-02-07 com
  **8 prefixos**; identidade fraca exatamente no agente que mais interessa.
- **L5 — dois denominadores de acervo divergentes**: 12.651 × 11.142 × 11.147 reais (§6).

---

## 6. `edgetelemetry.acervo_urls` conta as locs em carência — POR DESENHO, e o conserto é de uma linha

Medi 63 shards, **12.651 `<loc>`**, **11.147 URLs distintas**, **1.217 URLs em mais de um
shard**, **1.504 locs excedentes**.

**Não é defeito de sitemap.** `data/ops/sitemap_shard_grace.jsonl`, inventário de
2026-09-15T08:19:57Z, commit `06caad54`:

```
shards_em_disco 63 | shards_no_indice 57 | shards_fora_do_indice 6 | shards_em_carencia 6
shards_vencidos 0  | locs_ativas 11.145  | locs_em_carencia 1.504
locs_carencia_divergentes 0 | locs_carencia_orfas 0
carencia: pages-0088, pages-0094, pages-0095, pages-0097, pages-0098, pages-0100
```

**`locs_em_carencia: 1.504` = exatamente as 1.504 locs excedentes que medi.** E `pages-0100`,
um dos dois shards onde achei `/jurisprudencia/stj-iac-1/`, está na lista de carência. O
mecanismo funciona e é auditado à unidade: shard antigo fica vivo para o bot que já o buscou
não tomar 404. **Reconciliação exata**: `11.147 = 11.106 (manifesto) + 41 (índices e
institucionais)`, e **zero rotas do manifesto ausentes do sitemap**.

**O que resta como defeito real, e só isto**: `edgetelemetry.acervo_urls:87-116` conta as locs
em carência porque usa `findall` sobre todos os `*.xml` do diretório. Conserto:
`len(set(...))`, ou melhor, ler `locs_ativas` do inventário de carência. Efeito: o teto de
plausibilidade deixa de ser **13,5% mais frouxo** e os três instrumentos passam a concordar.

**Retratação registrada**: minha primeira leitura chamou isto de "defeito" e levantou custo de
orçamento de rastreio. Está errado e foi o advisor que apontou. O mecanismo é intencional,
medido e verde.

---

## 7. Runbook pós-publicação — comando a comando, com o que fazer quando o número não vem

```bash
cd /opt/wiki
UA='Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)'
R=/jurisprudencia/stj-iac-1/

# 1. ANTES: linha de base (~3 s) — os DOIS leitores canonicos, nunca soma crua
python3 - <<'PY'
import sys; sys.path.insert(0,'tools')
import edgetelemetry as et, crawlcoverage as cc
p,d=et.serie_saneada('.');  print('borda: chaves',len(p),'descartadas',len(d))
q,e=cc.serie_saneada('.');  print('cobertura: chaves',len(q),'descartadas',len(e))
print('acervo(locs, INFLADO por carencia):',et.acervo_urls('.'))
PY

# 2. Origem e gemea  (esperado 200/200, HTML <= 51200 B)
curl -s -o /dev/null -w 'origem %{http_code} %{size_download}B\n' -A "$UA" \
  -H 'X-Warming-Request: true' -H 'Host: wikijuridica.com.br' "http://127.0.0.1:8088$R"
curl -s -o /dev/null -w 'gemea  %{http_code} %{size_download}B %{content_type}\n' -A "$UA" \
  -H 'X-Warming-Request: true' -H 'Host: wikijuridica.com.br' "http://127.0.0.1:8088${R}index.md"

# 3. Borda (MISS logo apos purga, HIT depois)
curl -sI -A "$UA" -H 'X-Warming-Request: true' "https://wikijuridica.com.br$R" \
  | grep -iE '^HTTP|^cf-cache-status|^age|^last-modified|^cache-control'

# 4. Sitemap: ativo + carencia (nao "1"; confira contra o inventario)
grep -l "<loc>https://wikijuridica.com.br$R</loc>" public/sitemaps/*.xml
tail -1 data/ops/sitemap_shard_grace.jsonl | python3 -m json.tool \
  | grep -E 'locs_ativas|locs_em_carencia|shards_vencidos|carencia_orfas'
grep -A1 -F "$R</loc>" public/sitemaps/*.xml | grep lastmod | head -2

# 5. IndexNow
tail -1 data/ops/indexnow_direct_submissions.jsonl | python3 -m json.tool \
  | grep -E 'http_status|success|ownership_proof|url_count|submitted_at'

# 6. Paridade humano x bot por SHA-256
./tools/check-what-bots-see

# 7. ANCORA da publicacao, ao segundo: o smoke do release (1 req/rota)
python3 -c "
import json,glob
r=[json.loads(l) for f in glob.glob('data/ops/access/access-\$(date -u +%F).jsonl') for l in open(f)]
s=[x['ts'] for x in r if x.get('bot_class')=='self_simulation_probe']
print('smoke:',len(s),'rotas |',min(s),'->',max(s)) if s else print('sem smoke hoje')"

# 8. AGORA: quem ja bateu, no segundo, do log VIVO.  LC_ALL=C OBRIGATORIO.
CUT=$(LC_ALL=C date -d '30 minutes ago' '+%d/%b/%Y:%H:%M:%S')
tail -n 200000 /var/log/nginx/wikijuridica/access.log \
 | awk -v cut="$CUT" '{if(match($0,/\[[^]]+\]/)){t=substr($0,RSTART+1,RLENGTH-2);sub(/ .*/,"",t)}else next} t>=cut' \
 | grep -cF "$R"        # conta LINHA, nunca ocorrencia de regex

# 9. Par de arquivos UTC (hoje E amanha) — "hoje" local atravessa dois
ls data/ops/access/nginx-$(date -u +%F).jsonl data/ops/access/nginx-$(date -u -d tomorrow +%F).jsonl

# 10. Volume na origem por agente: SOMAR, nunca ultima linha (subconta 19,9x)
python3 -c "
import json,collections
s=collections.Counter()
for l in open('data/ops/origin_bot_traffic_daily.jsonl'):
    r=json.loads(l)
    if r.get('summable') is True and r.get('date')=='$(date -u +%F)': s[r['agent_key']]+=r.get('requests',0)
print(s.most_common(12))"

# 11. Forcar o refresco da borda em vez de esperar o timer das 01:11 (retencao CF: 8 dias)
./tools/measure-crawl-coverage --help
```

| sintoma | causa medida | ação |
|---|---|---|
| passo 8 devolve 0 linhas | locale pt_BR: `set` vs `Sep` | reexecutar com `LC_ALL=C` |
| origem 200, borda erro | túnel ou Cache Rule | `check-portal-health` sonda só 127.0.0.1 e passa verde com túnel caído → usar `check-edge-live` |
| agente some da origem pós-deploy | regressão na gêmea/negociação | hipótese 2 do `check-efeito-nos-bots`; já derrubou `.md` por 30 min |
| `paths_requested_that_day: 0` | `no_groups_returned: true` | dado ausente, **não** ausência de bot; reexecutar coleta |
| soma da borda absurda | somou linhas em vez de `serie_saneada` | inflação **48×** realista, **2.045.285×** com linha forjada |
| volume de origem baixo demais | pegou a última linha | **some**: subcontagem medida de **19,9×** |
| bot some do ledger de borda | chave errada | é `requests_estimated`, não `requests` (dá 0 para todos) |
| cobertura do lote = 0 p/ gptbot na origem | HIT na borda | ver `paths_first_seen`: lá são **686** |
| `check-efeito-nos-bots` diz INCONCLUSIVO | exige 14+14 dias | usar coorte (§5.2); replay via `WIKI_EFEITO_NOS_BOTS_LOG` |

---

## 8. Resumo: as seis séries e como somá-las

| arquivo | chave | convenção | leitor obrigatório | lag |
|---|---|---|---|---|
| `/var/log/nginx/wikijuridica/access.log` | requisição | incremental cru | direto, `LC_ALL=C` | **0** |
| `access/nginx-*.jsonl` | requisição | incremental | direto (par de dias UTC) | ≤ 1 h |
| `access/access-*.jsonl` (Go) | requisição | incremental | `bot_class=self_simulation_probe` = âncora | ≤ 1 h |
| `origin_bot_traffic_daily.jsonl` | `(date, agent_key)` | **incremental — SOME** | soma; pular `summable:false` | ≤ 30 min |
| `edge_bot_agents_daily.jsonl` | `(date, agent_key)` | **cumulativo — última** | `edgetelemetry.serie_saneada` | ≤ 30 min |
| `crawl_coverage_daily.jsonl` | `(date, crawler)` | **cumulativo** + v2 vence v1 | `crawlcoverage.serie_saneada` | ≤ 24 h |
| `ai_citation_signal_daily.jsonl` | `(date, layer, key)` | **incremental — SOME** | soma; `window_*` não soma | ≤ 6 h |
| `bot_return_daily.jsonl` | `(date, agent_key)` | derivado, reescrito | direto | ≤ 30 min |
| `crawl_coverage_state.json` | bot → rota → dia | estado | `crawlers_verified` apenas | ≤ 24 h |
| `indexnow_url_state.jsonl` | url | incremental, µs | direto | imediato |

---

## 9. O que o advisor mudou

Mudou quatro coisas, três delas materiais:

1. **§6 virou retratação.** Eu havia reportado 1.217 URLs duplicadas no sitemap como
   **defeito**, com custo de orçamento de rastreio. O advisor mandou ler
   `data/ops/sitemap_shard_grace.jsonl` antes. O inventário de 2026-09-15 traz
   `locs_em_carencia: 1504` — **exatamente** as 1.504 locs excedentes que medi — com
   `shards_vencidos: 0` e `carencia_orfas: 0`. **É mecanismo intencional, medido e verde.**
   Sobrou só o conserto de uma linha em `edgetelemetry.acervo_urls`.
2. **§0 foi reescrito.** Eu ia liderar com "yandexbot p25 = 2 min", número vindo da amostra
   contaminada por re-anúncio. O advisor mandou histogramar a hora do primeiro contato.
   Resultado: **gptbot concentra 97% em 01h–02h UTC**; a banda "apertada" dele é subtração
   entre duas agendas fixas, não responsividade. Isso **virou o achado principal** (§0.2) e
   gerou uma alavanca que eu não tinha: escolher a hora de publicação.
3. **`cloudflare-ai-search` saiu da manchete.** UA medido:
   `Cloudflare-AI-Search-External`, `ip_verificacao: unverifiable`. É a CDN indexando o
   próprio cliente, não assistente de terceiro.
4. **A âncora de publicação virou autoritativa.** O advisor mandou checar `route_class` do
   burst no ledger do Go. Eram **898 linhas `bot_class: self_simulation_probe`** — o smoke do
   release, 1 por rota, **898/898 em 15 segundos**. Substituiu o "primeiro 200 de qualquer
   cliente" e é agora a âncora #1 de §5.2.

Mandou também carregar a skill `medir-bots`, que o enunciado citava. **Ela revelou uma sexta
série que eu não tinha examinado**: `data/ops/origin_bot_traffic_daily.jsonl`, incremental,
que **subconta 19,9× quando lida com a regra da borda** (medi: 233.488 somando × 11.744 pela
última linha). E os agentes nomeados pelo dono ganharam linha própria (§2.5): **meta-externalagent
em colapso (31 requisições em 16 dias contra 15.302 na série de 36 dias) e claudebot ausente
desde 2026-09-08**.

**Não contradisse nenhuma medição minha** — todas as correções foram confirmadas por medição
nova nesta sessão, e cada uma está com o número acima.
