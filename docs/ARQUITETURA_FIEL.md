# Arquitetura fiel: como ler este repositório sem ser enganado

Documento permanente, ordem do dono em 2026-08-12. Leitura obrigatória para
qualquer sessão do Claude Code e para qualquer agente que vá medir, concluir ou
alterar algo aqui.

Ele não substitui `docs/ARCHITECTURE.md`, que descreve os módulos e o desenho.
Este descreve outra coisa: **onde a leitura ingênua deste repositório produz uma
conclusão falsa**, e qual é o método que não produz.

---

## 1. Por que este documento existe

Em 2026-08-12, numa única sessão, **doze conclusões erradas** foram produzidas —
por agentes especializados e pelo próprio engenheiro-chefe. Nenhuma foi apanhada
por gate. Todas tinham a mesma causa:

> O artefato foi lido pela chave, pela posição ou pela camada que alguém
> **supôs**, em vez da que ele realmente tem.

O inventário completo, porque cada linha custou tempo real:

| # | O que se supôs | O que era |
|---|---|---|
| 1 | corpo da página na chave `text` ou `body` | `opening` + `sections[].{heading,text}` + `faq[].{q,a}` |
| 2 | linhas do ledger de borda somáveis | são **snapshots cumulativos** desde a meia-noite; somar deu 1.000.002.017.077 requisições |
| 3 | `word_count` divergente em 88 de 189 páginas | pela fórmula real do produtor (regex + 10% de tolerância): **0 de 189** |
| 4 | 10 linhas impossíveis no ledger = defeito novo | já estavam quarentenadas, com o motivo gravado |
| 5 | 20 colisões de rota no acervo | já tombadas; colisões vivas: zero |
| 6 | "7.504 páginas novas" por `git grep` | o grep só casa a forma compacta da chave; eram **30** |
| 7 | `Last-Modified` regrediu para a data do deploy | era o ramo correto: os bytes de todas as páginas tinham mudado |
| 8 | `intent_id` no `published_manifest` | a chave é **`unique_intent_id`**; a busca deu zero e quase fez concluir que uma citação legal falsa não estava no ar — estava, inclusive no JSON-LD |
| 9 | 19.253 linhas de Googlebot falso sem marca | quarentenadas desde antes, com o emissor nomeado |
| 10 | ledger de túnel vazio = túnel caiu | o vigia **nasceu naquele dia**; ausência de medição não é medição de ausência |
| 11 | `portal_health` 57/57 OK prova que o túnel não caiu | ele sonda **só `127.0.0.1`**, que responde 200 com o túnel caído |
| 12 | dois blobs base64 divergentes = projeção corrompida | comparação **por posição**: o segundo blob era outro schema. O bug não existia — e eu o commitei como fato |

Os casos 8 e 11 são os mais caros: o primeiro quase enterrou um erro jurídico
publicado; o segundo produziu um veredito causal falso que contradizia o dono —
e o dono estava certo.

**A conclusão que este documento existe para tornar permanente:** neste
repositório, gate verde não é prova, gate vermelho não é veredito, comentário
não é fonte, e relatório de agente é alegação. O que vale é o dado real, lido
pela camada certa.

---

## 2. O método, em cinco movimentos

1. **Antes de medir, abra um registro cru** e enumere as chaves reais. Uma linha
   de `python3 -c "import json; print(list(json.loads(open(P).readline()).keys()))"`
   custa segundos e teria evitado quatro dos doze erros acima.
2. **Procure a camada de saneamento antes de ler o arquivo cru.** Vários ledgers
   deste repo têm um leitor canônico que deduplica, descarta o impossível e
   aplica a quarentena. Ler o `.jsonl` direto é pular a camada que existe
   justamente porque alguém já se enganou ali.
3. **Pergunte o que o instrumento ALCANÇA, não o que o nome dele promete.** Uma
   sonda de `127.0.0.1` não prova nada sobre a borda. Um verificador de origem
   avisa, no próprio texto, que "a borda não foi consultada".
4. **Compare por identidade, nunca por posição ou por nome de arquivo.** Casar
   página com página é por `intent_id` + hash do corpo; casar blob com blob é
   pelo formato do payload decodificado.
5. **Ausência de dado tem duas causas, e elas se distinguem por uma linha:**
   `git log --diff-filter=A -- <arquivo>` diz quando o produtor nasceu. Antes
   dessa data, vazio significa "não media", não "não aconteceu".

Um sexto movimento, que vale por todos: **tente derrubar a própria conclusão
antes de escrevê-la.** Nesta sessão, um crítico adversarial derrubou o veredito
causal do engenheiro-chefe abrindo um arquivo que ele não tinha aberto. A
concordância entre agentes não é verificação; refutação tentada e falhada é.

---

## 3. A topologia real do serviço, e o que cada sonda enxerga

O acervo é servido **de disco pelo nginx**, não pelo binário Go. O Go atende as
rotas dinâmicas e o fallback. Tudo atrás de um Cloudflare Tunnel.

```
  crawler / leitor
        │
   Cloudflare  ── cache de borda, Edge TTL, tiered cache
        │
   cloudflared  ── frota de instâncias, 4 conexões cada
        │
      nginx 127.0.0.1:8088  ── serve public/ de disco
        ├──────────────────────────────┐
       Go 127.0.0.1:8089    ── /buscar/, /healthz, contato, @fallback
                                       │
                        cmd/social 127.0.0.1:8091  ── /redesocial/,
                                       /api/v1/redesocial/
```

**São DUAS origens atrás do mesmo nginx**, e é isso que invalida sonda em porta
única: medido em 2026-09-05, `/redesocial/` responde 200 na 8088 e na 8091 e
**404 na 8089**; `/familia/` responde 200 na 8088 e na 8089 e **404 na 8091**.
Só a 8088 enxerga as duas.

**Isto é o que mais engana**, e é a raiz do erro nº 11:

| instrumento | o que ele bate | o que ele NÃO pode provar |
|---|---|---|
| `tools/check-portal-health` | `127.0.0.1:8088` e `127.0.0.1:8089` | qualquer coisa sobre o túnel ou a borda |
| `tools/check-what-bots-see` | a origem (ele mesmo avisa) | bloqueio ou erro servido pela borda |
| `tools/check-http-smoke` e `check-googlebot-smoke` | **nada na rede**: montam o handler em memória e usam `httptest.NewRecorder` | qualquer coisa sobre o servidor vivo, o nginx ou o `public/` — provam o código-fonte desta worktree |
| o smoke 7/7 do `deploy-publico` | a **borda** (`https://wikijuridica.com.br`) | corrigido em 2026-08-12: com Edge TTL de 7 dias um HIT passava com a origem quebrada. Passou a conferir **também** `127.0.0.1:8088` com o `Host` do domínio |
| `tools/check-internal-link-integrity` | `public/` em disco; e, **só quando há destino fora dele**, `127.0.0.1:8088` (nginx) com UA próprio e `X-Warming-Request` | que a rota exista na borda; e nada quando o acervo está íntegro, porque aí ele não abre socket nenhum. Sondar `:8089` daria 404 falso em `/redesocial/`, e por isso a sonda é na 8088 |
| `data/ops/crawler_error_budget.jsonl` | status servido **pela borda** a **bot verificado** | — é este o instrumento certo para a pergunta acima. As linhas **não se somam**: cada uma é uma janela própria; leia a última com o par `(window_hours, breached)` |

Uma consequência do primeiro caso que engana com frequência: **"smoke verde" não é
"produção sã"**. Os dois smokes de `cmd/check` não abrem socket nenhum — um `grep`
por `http.Get`, `http.Client`, `net.Dial` e `httptest.NewServer` em
`internal/checks/*.go` (fora de `_test`) devolve zero. Para o servidor vivo, o
instrumento é `curl` contra `127.0.0.1:8088` e `127.0.0.1:8089`.

E o arquivo de configuração do nginx **não é o nginx que está rodando**: o próprio
`ops/nginx/wikijuridica.conf` admite, em comentário, um trecho nunca verificado em
produção. Confirme a diretiva com `curl` contra a origem antes de afirmar que ela
vale.

**O mesmo vale para o binário, e é a armadilha mais fácil de esquecer:
`bin/wikijuridica-server` não é o código da worktree.** Ele foi compilado no
último deploy; todo commit posterior existe no fonte e **não** em produção.
Medição desta sessão: uma correção de rota entrou às 19:21 e o processo, subido às
17:43, continuava servindo o comportamento antigo — o fonte aceitava, a origem
devolvia 403. Ler o roteador em `internal/httpserver/` descreve o que o servidor
fará **no próximo deploy**, não o que ele faz agora.

Consequência prática: para perguntar *"o site esteve no ar para o Googlebot?"*,
o instrumento é o orçamento de erro da borda. `portal_health` responde outra
pergunta — *"o processo local está de pé?"* — e responder uma com a outra foi
exatamente o erro cometido.

---

### 3.9 Caminhos exatos — a tabela que evita meia hora de tateio

Esta subseção nasceu de erro medido em 2026-08-19: procurei o serviço do portal
como `wikijuridica-portal.service` (não existe), procurei o binário como
`./server` na raiz (existe, mas é outro arquivo, de 04/08, que NÃO é o que roda),
e só cheguei ao real depois de ler o `systemctl cat`. O custo foi tempo e token
do dono. Nome plausível não é nome real, e adivinhar caminho é a mesma classe de
defeito que ler artefato pela chave suposta.

**Regra de uso: isto é ORIENTAÇÃO, não verdade.** Código muda. Cada linha abaixo
tem âncora em `docs/arquitetura_fiel_ancoras.tsv`, então o gate acusa quando o
símbolo morre — mas o gate prova que o símbolo EXISTE, não que a prosa em volta
continua descrevendo bem o que ele faz. Antes de agir sobre qualquer linha,
confirme com o comando da última coluna.

| o que | caminho real | como CONFIRMAR (não confie na tabela) |
|---|---|---|
| serviço do portal | `wikijuridica-server.service` | `systemctl cat wikijuridica-server.service` |
| binário que roda | `/opt/wiki/bin/wikijuridica-server` | `ls -l /proc/$(systemctl show wikijuridica-server.service -p MainPID --value)/exe` |
| revisão SERVIDA agora | embutida no binário | `./tools/go-modern version -m bin/wikijuridica-server \| grep vcs.revision` |
| origem Go | `127.0.0.1:8089` | `ss -ltnp \| grep 8089` |
| nginx do wiki | `127.0.0.1:8088` | `ss -ltnp \| grep 8088` |
| config do nginx | `ops/nginx/standalone/nginx.conf` | `systemctl cat wikijuridica-nginx.service` |
| config MORTA que parece viva | `ops/nginx/standalone/server.conf` e `ops/nginx/wikijuridica.conf` | `grep -n include ops/nginx/standalone/nginx.conf` — o vivo só inclui `mime.types` e `security-headers.conf` |
| superfície de habilidades | servida pelo BINÁRIO, nunca de `public/` | `ls public/.well-known/` tem só `security.txt`; ver `docs/AGENT_SKILLS_DISCOVERY.md` |
| serviço do nginx | `wikijuridica-nginx.service` | dedicado, isolado do nginx do sistema |
| robots servido ao bot | `public/robots.txt` (DISCO) | `./tools/check-public-robots-drift` |
| daemon de IA local (cérebro) | `wikijuridica-cerebro.service`, binário `bin/cerebro` de `cmd/cerebro` | `systemctl cat wikijuridica-cerebro.service` |

**O `cerebro` é um quinto processo do host, e não fica na cadeia de servir HTML.**
`wikijuridica-cerebro.service` consome uma fila SQLite (`data/ai/fila.sqlite`) com
um único worker e chama o Ollama local (`ollama.service`, CPU-only, DEC-058) para
embeddings do acervo, medição de modelo e, nas fases seguintes, extração de
entidades e propostas de reescrita — tudo o que produz é dado em `data/ai/` e
medição em `data/ops/ia_local_daily.jsonl`. **Ele nunca escreve em `public/`,
`content/` nem `data/editorial/`**: publicação continua sendo só a cadeia
transacional do §5 do `CLAUDE.md`. Antes de cada lote ele sonda, só leitura, o
que o vigia sonda — a home, `/healthz` e `/buscar/` pelo nginx, `NRestarts` do
servidor e `/api/version` do Ollama (`internal/cerebro/saude.go`, `Verifica`) —
e pausa se algo sair do lugar; **não executa `tools/check-portal-health`**,
porque o script grava `data/ops/portal_health_state.json` e zeraria a memória
de reparos do watchdog (achado de 2026-09-08). Quando o acervo inteiro está
embutido, o cérebro grava `data/ai/embeddings/ativo.json` e é o **systemd** quem
reinicia o servidor: `wikijuridica-server-reload.path` observa esse arquivo
(`PathChanged`) e dispara `wikijuridica-server-reload.service`; o daemon
continua sem privilégio (`NoNewPrivileges=true`). O servidor, no boot, lê o
mesmo `ativo.json` (ferramenta MCP `buscar_semantico`, armada só se o Ollama
responder) e `data/ai/grafo_vizinhanca.jsonl` (`internal/grafo`, `Carregar`;
ferramentas `grafo` e `impacto`); os dois artefatos são derivados e ausentes
significam ferramenta fora de `tools/list`, nunca stub.

**Duas armadilhas de leitura de config, medidas em 2026-08-20.** A primeira: existem
**três** arquivos que parecem ser a config do nginx, e só um é carregado. `nginx.conf`
do diretório `standalone/` é o vivo; `server.conf`, ao lado dele, é **config morta** —
nada o inclui —, e `ops/nginx/wikijuridica.conf` é o vhost legado, que entra apenas no
`ingress_sha256` do fingerprint de deploy. Ler o arquivo errado e concluir sobre
produção a partir dele é conclusão sobre um arquivo que ninguém executa. O teste de
contrato já fixa o certo: `internal/contract/public/nginx_agent_surface_test.go:25`
declara `const vhostPath = "../../../ops/nginx/standalone/nginx.conf"`.

A segunda: **`brotli_vary` não existe** no módulo brotli instalado. `strings` no
`.so` lista `brotli`, `brotli_buffers`, `brotli_comp_level`, `brotli_min_length`,
`brotli_ratio`, `brotli_types` e `brotli_window` — e nada mais. Escrever a diretiva faz
`nginx -t` reprovar e **trava o reload no meio do deploy**. Quem precisar de `Vary` em
resposta comprimida por brotli tem de emiti-lo por `more_set_headers`, no padrão "UM
Vary, não dois" que a config já pratica.

**A armadilha que essas linhas escondem, e que custou o dia:** o nginx serve
`public/` do DISCO por `try_files`, e o Go só responde no `@fallback`. Duas
consequências que já morderam:

1. **Arquivo do disco vence o renderizador.** O `Content-Signal` estava correto no
   código e ausente no ar porque `public/robots.txt` era de 13/08. O comentário do
   próprio nginx registra o incidente gêmeo — a borda serviu por DIAS um robots de
   2.818 bytes contra 1.670 do disco. Corrigir código sem regravar o artefato não
   muda nada para o bot; `check-public-robots-drift` é quem prova.
2. **Header novo no Go é inerte nas rotas de disco.** Negociação por `Accept` na
   home e nos hubs não funciona só porque o Go passou a saber respondê-la: aquelas
   URLs nunca chegam ao binário. Já a gêmea `/…/index.md` funciona, porque não
   existe em disco e cai no fallback.

**E a terceira, que é a mais fácil de esquecer:** commit não é deploy. Em
2026-08-19 o binário no ar era de 13/08 — **54 commits atrás**. Tudo o que a
sessão havia corrigido existia no git e não existia para nenhum bot. `mtime` do
arquivo não mede isso; `vcs.revision` do binário em execução mede.

### 3.9 O log de acesso do nginx tem DOIS caminhos, e um deles está morto desde 2026-08-06

Custou uma conclusão errada em 2026-08-27, e a conclusão era grave: *"o Googlebot
fez ZERO requisições em 8 dias"*. Era falsa. O Googlebot rastreia todos os dias
(21 a 33 requisições/dia, verificadas pela Cloudflare), e o bingbot faz de 160 a
672.

**O erro teve duas camadas, e a segunda é a que este documento existe para evitar.**

A primeira é a armadilha A2, já catalogada aqui: `data/ops/access/*.jsonl` é o
ledger do **processo Go**, e o acervo é servido **estático pelo nginx**
(`root /opt/wiki/public` mais `try_files $uri $uri/index.html`). Página de acervo
não chega ao Go — nem por cache de borda, mas na própria origem. Ler aquele
ledger para responder "quem rastreou o acervo" mede a camada errada.

A segunda camada é nova e mais traiçoeira: ao ir buscar o log do nginx para
corrigir a primeira, o caminho óbvio dentro do repositório está MORTO.

    var/nginx/wikijuridica.access.log        48 KB, mtime 2026-08-06, só bot_sim=true
    /var/log/nginx/wikijuridica/access.log   8,5 MB, escrito agora   ← o vivo

O motivo é que `ops/nginx/standalone/server.conf` — que declara o caminho morto
em duas linhas — **não é carregado**. A unit executa
`nginx -c /opt/wiki/ops/nginx/standalone/nginx.conf`, e é o `nginx.conf` (81 KB)
que declara o caminho vivo. `server.conf` é fragmento histórico: config que
mente, na forma que o R1 do Contrato do Dado Real proíbe.

**A regra que fica:** para saber quem rastreou o acervo, a ordem das fontes é

1. `data/ops/edge_bot_agents_daily.jsonl` — Cloudflare, com
   `authenticity: cloudflare_verified_bot_category`. Ledger **cumulativo
   intradiário**: há várias linhas por data, e só o ÚLTIMO snapshot de cada
   `(data, agente)` vale. Somar as linhas infla a contagem.
2. `/var/log/nginx/wikijuridica/access.log` — a origem de verdade, com o IP.
3. `data/ops/crawl_coverage_daily.jsonl` — cobertura acumulada por crawler.
4. `data/ops/access/*.jsonl` — **só** rotas dinâmicas (`/buscar/`, API, MCP,
   `.md` gerado sob demanda). Nunca o acervo estático.

`tools/check-nginx-log-vivo` reprova se o caminho declarado na config efetiva
deixar de ser o que está sendo escrito, para que este parágrafo não vire a
próxima config que mente.

## 4. Os instrumentos de medição e sua camada obrigatória

A regra: **para cada pergunta há um leitor canônico. Ler o `.jsonl` cru é pular
a camada que existe porque alguém já se enganou ali.**

### Tráfego de bot na borda
- Arquivo: `data/ops/edge_bot_agents_daily.jsonl`
- **As linhas são snapshots CUMULATIVOS desde a meia-noite** — `window_start`
  fixo, `window_end` avançando. **Somar as linhas de um dia multiplica a
  contagem.**
- Leitor canônico: `tools/edgetelemetry.py` → `serie_saneada(root)`, que devolve
  `(por_chave, descartadas)`, deduplica por `(date, agent_key)` mantendo a
  **última** linha, e descarta a linha fisicamente impossível com o motivo.
- O teto de plausibilidade não é fixo: deriva do tamanho do acervo em tempo de
  execução, para não virar falso positivo quando o portal crescer.

### Acesso: são TRÊS camadas, não duas

Colapsar duas delas em "a origem" é erro de ~100× de população:

| camada | arquivo | o que contém |
|---|---|---|
| nginx | `/var/log/nginx/wikijuridica/access.log` | **tudo** que atravessou o túnel |
| binário Go | `data/ops/access/access-AAAA-MM-DD.jsonl` | **só o que chegou a :8089** — cerca de 1% |
| borda | GraphQL da Cloudflare | o que a Cloudflare viu |

**`data/ops/access/*.jsonl` NÃO é o log de acesso do site.** Ele é escrito pelo
binário Go, e 99% das URLs saem do disco pelo nginx sem nunca chegar ao Go.
Ausência de linha ali **não** é ausência de rastreio — é ausência de rota
dinâmica. E o próprio escritor **descarta linha quando o canal enche**, com
contador de `dropped`: o arquivo é um piso, nunca um total.

Duas consequências que enganam:

- **Ele não tem campo de IP.** Autenticidade de bot não se responde ali — o
  `bot_rule` vem da string de User-Agent. A pergunta de autenticidade se responde
  em `data/ops/origin_bot_traffic_daily.jsonl`, que tem `requests_authentic`,
  `forged`, `unverifiable` e o `verification_method`.
- **Os dois ledgers de acesso usam relógios diferentes**: o do Go grava `ts` em
  UTC; o de origem usa cursor na hora **local** do nginx (UTC−3). Correlacionar
  sem converter desloca tudo em três horas e faz um evento sumir da janela.

A camada de saneamento (`data/ops/access_ledger_quarantine.jsonl`, via
`tools/accessledger.py`) sanea **o ledger do Go**, não o log do nginx. A linha
ruim **continua no arquivo** — o ledger é append-only e não se apaga linha; a
quarentena registra, por hash, que ela não entra em conta nenhuma. Um veredito da
quarentena é **topológico**, não estatístico: rota que o nginx bloqueia no ingress
mas aparece no log nasceu dentro do processo — não há limiar a calibrar nem falso
positivo possível enquanto o ingress bloquear.

### Contagem de linha de ledger envelhece dentro da própria sessão

Ledger com timer cresce enquanto se audita. Medições desta sessão divergiram
entre HEAD e worktree em todos os arquivos observados, e o próprio repositório já
registrou o fenômeno duas vezes em comentário ("foi de 4.321 para 4.495 linhas
entre o commit e a auditoria").

**Regra: número de linha de ledger só vale com o hash do commit ou com o comando
que o reproduz.** Arquivo fechado por dia (`access-2026-08-11.jsonl`) é estável e
pode ser citado; o do dia corrente, não.

### Cobertura de rastreio — o indicador principal
- Arquivos: `data/ops/crawl_coverage_never_requested.json`,
  `crawl_coverage_state.json`, `crawl_coverage_daily.jsonl`
- Produtor: `tools/measure-crawl-coverage`
- Conta **bot verificado pela Cloudflare** (`verifiedBotCategory`, rDNS + faixa
  de IP publicada), nunca string de User-Agent — contar por UA soma as nossas
  próprias sondas de auditoria, e a inflação medida chegou a 258×.
- O número é declaradamente um **piso, duas vezes**: exclui requisição real que
  a Cloudflare não autenticou, e o dataset é amostrado.
- **"0%" para um bot que a Cloudflare não verifica significa não-mensurável, não
  ausência.** Comparar no mesmo ranking bot verificado com bot não-verificável
  mistura duas coisas diferentes.
- "Requisições por dia" mede atividade; **cobertura do acervo mede descoberta**.
  A régua completa é cobertura + taxa de descoberta de URL nova por dia +
  orçamento de erro da borda: cobertura sozinha não distingue "crawler que
  terminou" de "crawler que desistiu".

### Jurisprudência: ementas de acórdão do STJ

- Coletor: `cmd/collect-stj-acordaos` (wrapper `tools/collect-stj-acordaos`,
  timer `ops/systemd/wikijuridica-stj-acordaos-coleta.timer`, semanal).
- Fonte: os dez datasets `espelhos-de-acordaos-*` do CKAN de dados abertos do
  STJ, um por órgão julgador, com um arquivo JSON por mês. Licença "Creative
  Commons Atribuição" declarada na página e conferida a cada execução.
- Camada: `data/corpus/jurisprudencia/stj-espelhos/`. Os `registros-AAAA-MM.jsonl`
  ficam fora do git; `manifest.jsonl` e `cursor.json` entram, porque são o que
  prova o que foi coletado, quando e com que hash.
- Leitor canônico: `internal/stjacordaos`. Ler o `.jsonl` cru pula a projeção
  que normaliza as duas datas que a fonte escreve em formato próprio
  (`20250630` e `DJEN       DATA:04/07/2025`) e o filtro de sigilo.
- **Este canal traz ementa, não inteiro teor**, e não declara nível de sigilo.
  As armadilhas e o porquê de cada campo vazio estão em
  `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`, seção 4k.

---

## 5. O modelo de dado editorial

### O registro de página (`data/editorial/v2_pages/*.jsonl`)

Chaves de topo, lidas de registro real: `intent_id`, `title`, `meta_description`,
`h1`, `opening`, `sections`, `faq`, `official_sources`, `internal_link_topics`,
`lane`, `word_count`.

**Não existe chave `text` nem `body` no topo.** O corpo se monta assim:

```
opening
  + para cada item de sections:  heading e text
  + para cada item de faq:       q e a          (não "question"/"answer")
```

### `word_count`

A fórmula canônica vive em `tools/generate_v2_review_queue.py`
(`computed_word_count`): tokeniza o corpo acima pelo regex
`[0-9A-Za-zÀ-ÖØ-öø-ÿ]+` e a tolerância do gate é de **10%** —
`abs(declarado − computado) * 10 > computado` reprova.

Contar com `.split()` e tolerância de duas palavras produz divergência falsa em
metade do acervo. Foi o erro nº 3.

**Cuidado com a colisão de nome:** existem **duas** grandezas chamadas
word_count, e elas caem em guardas **opostas**. O campo declarado `word_count` do
registro está na allowlist do refresh de pino; mas o `ComputedWordCount` —
recontado do corpo pelo contrato material — **reprova** com "recomputed word
count changed and requires a new editorial review". Ler "word_count está na
allowlist" e concluir que mexer no número de palavras passa é erro: só passa se o
texto visível não mudou, porque aí o recomputado não se move.

### `published_manifest.jsonl`

Chaves: `manifest_id`, **`unique_intent_id`**, `path`, `canonical_url`, `title`,
`index_policy`, `page_status`, `approved_at`, `reviewed_at`, `author`,
`reviewer`, `release_gate_id`, `html_sha256`, `sitemap_sha256`,
`source_provenance`.

**A chave do intent é `unique_intent_id`.** Procurar `intent_id` devolve zero e
faz parecer que a página não está publicada. Foi o erro nº 8, o mais caro.

### Linha do estoque não é página

Medição própria de 2026-08-12 sobre `data/editorial/v2_pages/*.jsonl`:

```
  9.833 linhas
    9.712 páginas com corpo
      121 tombstones (skipped=true), 19 deles de supersessão
        0 linhas que não sejam uma coisa nem outra
```

Contar `wc -l` dos shards e chamar de "número de páginas" superestima em 121.
O filtro honesto é presença de `opening`.

### E `intent_id` **não é único** no estoque

Consequência direta do item acima, e ela morde em silêncio: os 19 tombstones de
supersessão carregam o **mesmo `intent_id`** do registro canônico que os
substituiu, em shard diferente. São 9.833 registros para **9.814 `intent_id`
distintos**.

```python
{r["intent_id"]: r for r in registros}      # ERRADO: sobrescreve em silêncio
```

Pior que sobrescrever: **a ordem alfabética do glob decide qual sobrevive**, e a
lápide costuma ganhar. `imob-dupla-venda-mesmo-imovel` existe como tombstone em
`imobiliario-10.jsonl` e com corpo em `imobiliario-05.jsonl`; indexado
ingenuamente, o dicionário devolve "página sem corpo" para as 19.

**Regra: filtre por presença de `opening` ANTES de indexar por `intent_id`.**

O censo de severidade tem o mesmo descasamento, nos dois sentidos:
`v2_publication_severity.jsonl` tem 9.801 linhas para 9.782 intents distintos, 121
deles de tombstone, e **32 páginas com corpo não têm linha de severidade**. Quem
fizer join 1:1 entre censo e estoque erra nas duas direções sem receber aviso
nenhum.

### Onde vive a política de publicação

`index_policy`, `publication_allowed`, `render_allowed`, `sitemap_allowed` e
`public_path` **não estão no registro do estoque** — vêm `None` porque a chave
não existe. A decisão de publicar é da camada de release (censo de severidade +
promoção transacional), não do JSONL.

---

## 6. Gates, travas e sequenciamento

### O que não pode rodar junto

Aprendido a duras penas hoje, com três deploys derrubados:

| se está rodando | não rode | sintoma da colisão |
|---|---|---|
| `tools/deploy-publico` (ingest) | qualquer escrita em `data/editorial/v2_pages/` | `v2 ingest read snapshot changed` ou `acquired an additional hard link during read` |
| um aquecimento de borda | outro aquecimento | dois processos varrendo as mesmas ~9.900 URLs; hoje deu load 20,6 |
| um commit que toca Go | outro commit que toca Go | o pre-commit religa pacotes; serializar |

As três falhas de ingest foram **o sistema funcionando**: ele recusou publicar
com o estoque mudando debaixo dele. Falha de gate aqui costuma ser proteção, não
defeito — leia a mensagem antes de contornar.

### Duas instâncias do servidor sobre o mesmo `cacheDir` destroem o índice de busca

Aprendido em 2026-08-19, em produção, e o gatilho fui eu: subi uma segunda
instância do binário em `127.0.0.1:8199` (via `WIKI_HTTP_ADDR`) para auditar o
HEAD **sem trocar o diretório de cache**. O `WorkingDirectory` da unit é
`/opt/wiki`, então as duas instâncias passaram a compartilhar
`var/on-demand-cache` — e o nome do diretório vem de `searchIndexCacheDirName`,
em `internal/httpserver/httpserver.go`.

O que quebrou, medido minutos depois:

- `tools/call` de `buscar_paginas` no MCP devolvia `isError: true` com
  `segment: var/on-demand-cache/search-index.tmp/store/000000000011.zap persist
  err: ... no such file or directory` — na borda **e** na origem;
- a busca HUMANA morreu junto: `/buscar/?q=...` respondia 200 com "Nenhum
  resultado", que é o pior formato de falha (parece vazio legítimo);
- `A2A SendMessage` com texto livre devolvia `-32603`, porque a skill declarada
  no AgentCard depende do mesmo índice.

Duas propriedades do código transformaram uma corrida transitória em
indisponibilidade permanente: o diretório temporário de build era **fixo**
(`indexPath + ".tmp"`), sem exclusão entre processos — só um `sync.Mutex`, que é
in-process —, e a falha ficava **latchada** (`built = true`, `pages = nil`), sem
nova tentativa até o restart. O serviço só voltou porque foi reiniciado.

Regra que fica: **instância de auditoria usa `cacheDir` próprio, sempre.** Para
conferir o comportamento do HEAD, ou se aponta o binário novo para um diretório
temporário, ou se testa por unit test — nunca por segunda instância sobre o
cache vivo. A correção de código (lock de arquivo, temporário único por
processo, erro não latchado, degradação para índice em memória) reduz o dano;
ela **não** autoriza o gatilho.

### `gzip_types` casa o `Content-Type` INTEIRO — e parâmetro não é `charset`

Medido em 2026-08-19: `/.well-known/api-catalog` saía **sem** `Content-Encoding`
com `Accept-Encoding: gzip, br`, enquanto `/openapi.json` e
`/.well-known/ai-catalog.json` saíam com gzip. O corpo tem 1.186 bytes, acima do
`gzip_min_length` de 1024 — não era tamanho.

A causa é o parâmetro do media type. O catálogo emite `linksetContentType`
(`internal/httpserver/descritores.go`), que é
`application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"`,
porque o §4.2 do RFC 9727 obriga. O nginx compara o `Content-Type` inteiro
contra a lista e descasca apenas `charset=` de resposta proxiada — nenhum outro
parâmetro. Com `profile`, nunca casa. Reproduzido em harness nginx isolado, com
a mesma versão e os mesmos módulos: sem o parâmetro comprime, com o parâmetro
não.

A armadilha real não é o byte perdido — é ler a diretiva e **acreditar** que a
entrada na lista resolve. Ela está lá de propósito, e o comentário no arquivo
diz que hoje é inócua. Ao auditar compressão neste portal, meça o header; a
presença do tipo em `gzip_types` não prova nada.

### Receptor por valor congela o `Server`: a ordem das atribuições em `New()` é comportamento

`mcpHandler()` e `novoServidorMCP()` têm receptor **por valor**
(`func (s Server)`), então o `*mcp.Server` é construído sobre uma cópia do
`Server` tirada no instante da chamada. Enquanto `servidor.mcp` era atribuído
antes de `armaRegistroDeRelatos` (`internal/httpserver/httpserver.go`), a cópia
congelava `relatos == nil` para sempre e a ferramenta MCP `relatar_defeito`
**nunca** era registrada — medido em produção: `tools/list` devolvia só
`buscar_paginas` e `ler_pagina`, mesmo com o OAuth armado e
`POST /api/v1/relatos` respondendo 401 com `WWW-Authenticate` correto.

O que torna isto catalogável, e não anedota: o teste do pacote **passava**,
porque o helper recriava `servidor.mcp` depois de armar `relatos` — o teste
contornava o defeito e o comentário dele descrevia o contorno como natural. Um
gate que passa por reconstruir o objeto sob teste não prova nada sobre o objeto
que o `New()` entrega. A trava correta é exercitar `New()` de ponta a ponta
(`TestNovoOrdenaRelatosAntesDoTransporteMCP`).

### Gates que reprovam por motivo que não é conteúdo

Existem, e confundem quem lê o veredito sem ler a causa:

- **Decurso de calendário.** Um limite de idade de proveniência reprovava a
  validação semântica e travava a escrita do acervo inteiro sem que ninguém
  editasse nada. Corrigido em 2026-08-12: idade virou higiene; data **futura**
  continua reprovando, porque é conferência que não pode ter acontecido.
- **Cache de fábrica obsoleto.** O auditor reprovava com a mesma forma e o mesmo
  código de saída de um defeito editorial real. Corrigido: falha de ambiente sai
  com código próprio, stdout vazio e o motivo no stderr.

### Identidade do estoque

O contrato semântico pina o SHA-256 exato do registro de página. Quando os bytes
mudam, há duas situações **que não se confundem**:

- **movimento não-semântico** (uma URL de fonte trocada, o sentido intacto) →
  refrescar o pino é correto, e existe canal próprio para isso;
- **reescrita** (título novo, corpo trocado) → refrescar o pino seria autenticar
  reescrita como movimento de bytes. O caminho é supersessão.

Hoje o guarda barrou exatamente esse caso e estava certo: uma página fora
reescrita por engano, e o pino recusou.

---

## 7. Conteúdo jurídico: a classe de defeito que nenhum gate pega

**Citação legal mal atribuída é P1 permanente.** Nenhuma medição automática a
detecta, e é a única classe com risco real sob o Provimento OAB 205/2021.

Três casos reais desta sessão, todos achados por leitura e conferência na fonte
primária, nenhum por gate:

1. Três páginas afirmavam — no corpo e no JSON-LD servido — que a **Resolução
   BCB 96/2021 instituiu o MED do Pix**. A norma é de 19 de maio de 2021, trata
   de contas de pagamento, e não menciona o MED uma vez sequer. A correta é a
   **103/2021, art. 41-B**. Estava publicado.
2. Uma página nova atribuía ao **art. 159 da Lei 14.133** a instauração do
   processo e um prazo "de 15 a 25 dias úteis fixado no edital". É o **art.
   158**, com 15 dias úteis fixados pela lei — e o art. 159 determina o
   **oposto** do que a página dizia: processos apurados e julgados
   **conjuntamente, nos mesmos autos**.
3. Uma página inteira apresentava a **Súmula 366 do TST** como regra vigente. Ela
   foi cancelada por perda de eficácia em 11.11.2017. A regra material dos 5/10
   minutos sobrevive — mas por outro fundamento, o art. 58 §1º da CLT.

**A lição de método:** um gate que confere "a norma citada" decide errado nos
dois sentidos. A mesma Resolução 96 era citada **corretamente** por outra página,
pelo encerramento de conta. O gate tem de operar **por citação**, exigindo que o
dispositivo reclamado por *aquela* frase apareça no texto do destino.

**E fonte que responde 200 não é fonte conferível.** Portais de governo servem
aplicação JavaScript: a URL responde 200 com ~23 caracteres de texto visível.
Verificar por status é falso-verde; o critério é **texto visível** com piso de
caracteres e marcas de dispositivo. Onde não houver endereço que entregue texto,
**fail-closed**: registra-se pendência nominal. Fonte errada é pior que fonte
inconferível.

---

## 8. Como este documento se prova

Documentação apodrece — este repositório já teve comentário mentindo em código
de produção, corrigido como bug. Por isso as afirmações ancoradas aqui têm um
gate:

```
tools/check-arquitetura-fiel
```

Ele lê `docs/arquitetura_fiel_ancoras.tsv` e prova que cada arquivo citado existe
e que cada símbolo citado ainda aparece nele. A âncora é **por símbolo, nunca por
número de linha**: linha apodrece na primeira edição acima dela, e gate que grita
no dado bom é gate que o operador aprende a ignorar.

O que ele **não** faz, e é honesto dizer: não prova que a prosa interpretou o
símbolo corretamente. Ele prova que a prosa aponta para algo que existe. É o
piso, não o teto — o teto continua sendo ler o código.

**Ao alterar arquitetura, altere este documento e a âncora junto.** Remover a
âncora sem corrigir a prosa transforma o gate em teatro.

---

## 9. Documentos irmãos

- `docs/CONTRATO_DADO_REAL.md` — as dez regras vinculantes de dado real
- `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` — o catálogo detalhado de comandos e
  dados que já mentiram, com o diagnóstico de cada um
- `docs/ARCHITECTURE.md` — módulos e desenho do sistema
- `docs/SEO_CRAWL_INDEXING.md` — contrato de HTML leve e indexação
- `docs/CONTENT_QUALITY.md` — gates editoriais
