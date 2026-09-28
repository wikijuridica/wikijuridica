# Crawlers e bots — política e evidência (investigação 2026-08-11)

Este documento registra a política vigente de acesso de bots ao portal
`wikijuridica.com.br` e a evidência que a fundamenta, apurada durante a
FASE 3/6 do plano `docs/plans/2026-08-11-recuperacao-crawl.md`. Não substitui
esse plano (que é o registro cronológico da investigação) — é a referência
estável para quem chegar depois e precisar saber "qual é a regra hoje e por
quê", sem reconstruir a investigação inteira.

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

## Quem tem autoridade sobre volume de bot (Regra 15, 2026-09-15)

As tabelas por bot deste documento foram apuradas no **log de origem**, e é assim que se leem:
recorte de origem, com a data da janela. Origem é **piso**; a autoridade sobre volume, alcance e
retorno de bot é a **borda**, porque o acervo sai de `public/` com `s-maxage=604800` e o `HIT`
na Cloudflare não chega ao processo Go. O procedimento de medição na borda — credencial,
consulta e fatiamento da janela — está em `docs/MEDICAO_DE_AUDIENCIA.md`, seção *"Como se mede
volume na borda"*.

O que a origem continua respondendo com autoridade: rota dinâmica, gêmea Markdown, `/api/v1`,
MCP e descritores de máquina, em `data/ops/access/*.jsonl` — e a política por bot de
`content/crawl_policy.json`, que não é questão de volume. Toda afirmação de volume neste
documento declara a camada medida.

## A regra que rege tudo: bloqueio nunca é por User-Agent (DEC-023)

**Decisão vigente (2026-08-04, ordem direta do titular do conteúdo):** o
portal é **permissivo com bots**. Nenhum User-Agent recebe `403`, `Disallow: /`
ou qualquer outra forma de bloqueio só por se identificar como um bot
específico — nem mesmo bots de treinamento de IA (GPTBot, ClaudeBot, CCBot,
Bytespider, Amazonbot, meta-externalagent, Applebot-Extended, Google-Extended).
Todos recebem `Allow: /` em `robots.txt`, com os únicos `Disallow` sendo de
**higiene de indexação**, e desde 2026-08-11 eles são **diferentes por classe**:

| classe | `Allow` | `Disallow` |
|---|---|---|
| bots valiosos de busca/usuário (13) | `/` e `/buscar/` | **nenhum** |
| treinamento, tokens de controle e `*` (10) | `/` | `/buscar/` e `/*?*` |

O bot valioso deixou de ter `Disallow: /*?*` porque esse padrão bloqueava
**qualquer** URL com query string — inclusive `?utm_source=`. Pela resolução por
comprimento do REP, ele (2) vencia o `Allow: /` (1), e o Googlebot ficava
proibido de buscar URL de campanha: o canonical na URL limpa nunca era lido e a
URL tendia a virar "indexed, though blocked by robots.txt". Quem consolida
parâmetro que não altera o corpo é o canonical, não o robots.txt.

E o bot valioso **mantém `/buscar/` rastreável de propósito** — é assim que ele
enxerga o `noindex` da rota em vez de adivinhar. Bloqueá-la ali recriaria o
mesmo anti-padrão, e na URL que recebe link interno de todas as páginas.

O que existe no lugar de bloqueio por identidade é **proteção de
disponibilidade por path/método**: rate limit por IP em `ops/nginx/*.conf`
(duas pistas — genérica e "bot valioso", esta última ilimitada de verdade,
com chave de zona vazia) e, quando um agente hostil
aparece (ver seção do IP forjado abaixo), bloqueio pelo **path que ele ataca**
(`/@fs/`, `/shell`, `/.env`, método `POST` — o site inteiro é GET/HEAD), nunca
pelo nome que ele declara no `User-Agent`. Um `User-Agent` é uma alegação do
cliente, não uma credencial; puni-lo é punir o nome, que qualquer scanner pode
trocar a cada requisição (é exatamente o que o IP abaixo faz).

`internal/crawl` é a fonte única dessa política (`HTTPDeniedBots()` vazio,
`content/crawl_policy.json` sem `Disallow: /` por identidade); espelhada em
`ops/nginx/wikijuridica.conf` (sem `if (...) return 403` por UA) e em
`public/robots.txt` (gerado por `cmd/generate-public-robots` / regenerado por
`cmd/publish-v2-direct`). Reintroduzir qualquer negação por UA exige nova DEC
— ver `docs/goal/DECISIONS.md` DEC-023 para o racional completo e os três
lugares que mudaram juntos.

## Tabela por bot — 2 dias completos, 2026-09-02/03 (substitui a de 11/08)

Medição de 2026-09-03, com DUAS fontes independentes e a identidade verificada
em cada uma. A tabela de 11/08 (mantida abaixo como registro histórico) foi
levantada quando a única fonte era o log do Go, que não vê o acervo HTML — e por
isso ela subestimava todo bot que lê páginas, que é a maioria.

**Fonte 1 — log do nginx** (`data/ops/access/nginx-*.jsonl`, produzido por
`tools/generate-origin-access-ledger` desde 03/09; vê TODA requisição, inclusive
o acervo estático). Tráfego próprio já descontado. Dois dias:

| Bot | requisições | páginas HTML | gêmea `.md` | 5xx recebidos |
|---|---:|---:|---:|---:|
| PerplexityBot | 2.088 | 2.085 | 0 | 0 |
| OAI-SearchBot | 754 | 621 | 133 | 0 |
| bingbot | 562 | 498 | 54 | 0 |
| ChatGPT-User | 103 | 103 | 0 | 0 |
| Applebot | 74 | 74 | 0 | 0 |
| Googlebot | 35 | 12 | 0 | 0 |
| Amazonbot | 23 | 23 | 0 | 0 |
| GPTBot | 13 | 2 | 10 | 0 |
| YandexBot | 6 | 4 | 0 | 0 |

**Fonte 2 — borda da Cloudflare** (GraphQL, amostrado), com a lane de identidade
por faixa de IP oficial que entrou em 03/09: a Cloudflare NÃO verifica o
PerplexityBot, e até esta data toda série do repositório o contava como zero.
Cobertura acumulada do sitemap por bot verificado (30 dias, 10.177 URLs):
amazonbot 99,1 %, yandexbot 99,8 %, googlebot 70,7 %, gptbot 52,5 %, bingbot
43,8 %, perplexitybot 35,2 %, oai-searchbot 30,8 %, claudebot 24,1 %,
chatgpt-user 4,2 %.

**O que esta tabela corrige na leitura do projeto:**

- O maior rastreador de IA do portal é o **PerplexityBot**, e ele estava
  invisível: `edge_bot_agents_daily` gravava `requests_sampled=0`, a cobertura
  dizia "0 verificado / 10.173 nunca pedidas" e o error budget rotulava as
  requisições dele como "sonda deste repo". Nada disso era verdade — 100 % dos
  IPs estão nos 8 prefixos que a Perplexity publica.
- O **Googlebot é quem rastreia pouco** (12 páginas em 2 dias), e não por
  transporte: no mesmo período o Bing pediu 498 páginas e o PerplexityBot 2.085
  pela mesma infraestrutura. Das 35 requisições dele, 22 foram de sitemap —
  todas com `If-Modified-Since` e todas respondidas 304, isto é, metadado barato.
- A **gêmea Markdown tem leitor real**: OAI-SearchBot (133) e GPTBot (10) a
  pedem; ChatGPT-User, Perplexity e Applebot leem o HTML.
- **Zero 5xx a bot** depois das correções de 02-03/09. Antes delas, `/mcp`
  respondeu 452 × 503 em 2 dias, e o canal Markdown 10.179 × 503 numa única
  passada do aquecedor.

## Tabela por bot — 14h de log íntegro, 2026-08-11 (HISTÓRICO)

> Mantida porque a análise do IP forjado abaixo se apoia nela. Os números de
> volume estão superados pela tabela de 03/09; o método (rDNS forward-confirmed
> e faixa oficial) continua valendo e é o mesmo que a lane de IP usa hoje.


Medição sobre a janela de log sem gap disponível em 2026-08-11, com
verificação **forward-confirmed rDNS** (resolver o IP de origem e confirmar
que o hostname resolvido aponta de volta para o mesmo IP) e, quando o
provedor não publica rDNS estável, **faixa oficial de IP** documentada pelo
próprio operador do bot. Probes internos marcados `X-Bot-Simulation: true`
foram excluídos da contagem.

| Bot | Requests no log | Autênticos (rDNS/faixa) | Forjados | Como foi verificado |
|---|---:|---:|---:|---|
| Googlebot | 47 | 47 | 0 | rDNS forward-confirmed |
| Bingbot | 9 | 9 | 0 | rDNS `search.msn.com` |
| YandexBot | 14 | 14 | 0 | rDNS |
| Amazonbot | 1.585 | 1.389 | 196 | rDNS `crawl.amazonbot.amazon` |
| ChatGPT-User | 171 | 17 | 154 | faixa oficial OpenAI |
| OAI-SearchBot | 99 | 53 | 46 | faixa oficial OpenAI |
| PerplexityBot | 45 | 2 | 43 | faixa oficial Perplexity |
| GPTBot | 55 | **0** | 55 | faixa oficial OpenAI — nenhum request bate |
| ClaudeBot | 41 | **0** | 41 | faixa oficial Anthropic — nenhum request bate |
| Google-Extended | 40 | **0** | 40 | rDNS — nenhum request bate |
| Applebot | — | 0 | — | veio uma vez em 08-06, zero desde então |
| DuckDuckBot | — | 0 | — | zero desde 08-06 |

**Leitura que essa tabela corrige.** A leitura corrente do projeto até
2026-08-11 — "os bots de IA vêm e desistem" — misturava tráfego forjado com
real e por isso estava errada. GPTBot, ClaudeBot e Google-Extended **reais**
nas 14h medidas: **zero**. O que existe de tráfego de IA genuíno e saudável é
**OAI-SearchBot** (53 requests autênticos, 100% status 200/304, o único bot de
IA com presença constante) e **ChatGPT-User** (17 autênticos, volume baixo
porque é *fetch* sob demanda, não varredura). GPTBot e ClaudeBot varreram o
acervo pesadamente em 08-07 (16.461 e 43.057 requests respectivamente — 1,7×
e 4,4× o tamanho do acervo, ponderado pela amostragem do
`generate-bot-agents-daily`) e pararam; não há sinal de recrawl desde então.
Amazonbot é hoje o **crawler mais ativo do site** (1.389 requests autênticos
na janela, ritmo de ~2.437/dia).

## O IP único que forjou seis User-Agents de crawler de IA

**Fato apurado.** Todo o tráfego forjado de GPTBot, ClaudeBot, Google-Extended
e parte do tráfego "ChatGPT-User"/"OAI-SearchBot"/"PerplexityBot" que não bate
com a faixa oficial vem de **um único IP: `35.196.168.160`**
(`OrgName: Google LLC`, `NetName: GOOGLE-CLOUD`) — uma VM alugada no Google
Cloud, não o Googlebot real (que tem faixa e rDNS próprios, verificados à
parte). Esse IP roda um **scanner de credenciais/RCE**, trocando de
`User-Agent` a cada requisição, contra caminhos que não existem no portal:

- `/@fs/root/.env?raw??`
- `/@fs/root/.aws/credentials`
- `/@fs/var/run/secrets/kubernetes.io/serviceaccount/token`
- `POST /shell`
- `POST /api/exec`
- `POST /?%ADd+allow_url_include%3d1…` (tentativa de RCE via PHP-CGI)

Total: **575 requests forjados** na janela medida, todos batendo `404`/`405`
(o site não expõe nenhum desses paths nem aceita `POST`). O impacto real não
é de segurança — nada respondeu 200, o portal é 100% estático/GET — é de
**telemetria contaminada**: sem separar autêntico de forjado, qualquer relatório
de "que bot visita o site" soma o scanner como se fosse GPTBot/ClaudeBot reais
e produz uma leitura de produto errada (foi exatamente o que gerou o
diagnóstico incorreto "bots de IA desistem").

**Por que isso não vira bloqueio por User-Agent.** Bloquear "GPTBot" para
parar esse IP puniria o GPTBot real (que hoje tem zero presença, mas pode
voltar) e não pararia o scanner, que já finge ser seis bots diferentes e
trocaria para um sétimo nome sem custo. A resposta correta, coerente com
DEC-023, é **path e método**: uma regra WAF (Cloudflare custom rule, gratuita)
bloqueando `http.request.uri.path contains "/@fs/"`, `http.request.method eq
"POST"` (o site inteiro é GET/HEAD) e os caminhos de credencial — nunca o
campo `User-Agent`.

## Applebot-Extended não está sob restrição ampla

Verificado em `public/robots.txt`: `Applebot-Extended` (bot de treinamento,
`training_tier_strict` em `content/crawl_policy.json`) recebe `Allow: /` com
apenas os dois `Disallow` de higiene (`/buscar/`, `/*?*`) — a mesma regra de
qualquer outro bot de treinamento sob DEC-023, não uma restrição especial.

> **Atualizado em 2026-09-02 — a divergência acima foi fechada em 2026-08-26 e
> este parágrafo ficou para trás.** Os tiers de rate **estão aplicados** no
> nginx: `content/crawl_policy.json` declara `training_tier_standard` 600 r/m
> (burst 300) e `training_tier_strict` 300 r/m (burst 150), e
> `tools/generate-nginx-rate-tiers` os materializa nos maps `wj_tier_training_*`
> e nas diretivas `limit_req` de `ops/nginx/wikijuridica.conf` (linhas ~485–511 e
> ~747–749; commits ce0a191e/498b779c). O curinga `*` continua na zona genérica
> `wj_generic` (3000 r/m, burst 600, chave por IP). Medido em 02/09 sobre
> 635.148 linhas do nginx e toda a série de borda: **zero 429** a qualquer bot —
> a aplicação existe e nunca precisou disparar. Os números "60 r/m / 20 r/m" da
> redação anterior eram de uma versão antiga do registry. Um gate que compare os
> r/m citados aqui com `rate_tiers` está no plano de 2026-09-02 (Fase 3.5).
Não há alavanca de submissão documentada pela Apple para acelerar a chegada
do Applebot; a via de influência disponível é sinal de frescor (lastmod do
sitemap coerente, feed Atom atualizado) e saúde de host (uptime, TTFB,
ausência de 5xx), não uma ação direta de "pedir" o rastreamento.

## Ferramentas

- `./tools/check-what-bots-see` — read-only, confirma o que cada classe de
  bot recebe hoje (título, meta, canonical, corpo, ausência de runtime
  cliente) sem depender de telemetria de terceiros.
- `data/ops/access/access-*.jsonl` — log de acesso íntegro por dia, campo
  `bot_sim` marca probe interno (excluído desta medição).
- `content/crawl_policy.json` — fonte única da política por bot
  (`internal/crawl.LoadDefaultPolicy`), espelhada em `public/robots.txt`.

## O que este documento NÃO cobre

Não cobre a ponderação por amostragem (`sampleInterval`) da série diária de
`tools/generate-bot-agents-daily.py`/`tools/botagents.py`, nem o check novo
`bot-telemetry-honesty` que separa `requests_authentic` de `requests_forged`
na telemetria persistida — ambos em progresso em outra frente no momento
desta escrita (2026-08-11/12); ver `docs/plans/2026-08-11-recuperacao-crawl.md`,
seções de FASE 6, para o estado vivo dessa parte.
