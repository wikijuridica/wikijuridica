# Varredura 5 — COMO SE VERIFICA O PORTAL AO VIVO, AGORA

Modo de operação para a produção. Tudo abaixo foi **medido em 2026-09-15 entre
20:55 e 21:15 -03**, com sonda honesta (UA próprio + `X-Warming-Request: true`).
Onde não medi, está escrito "não medido" e por quê.

Sessão em PLAN MODE: nada foi mutado. Todas as leituras foram GET/POST read-only,
`git show`, `systemctl list-timers`, leitura de arquivo e leitura do log cru do nginx.

---

## 0. O mapa das três camadas, medido

```
Cloudflare (colo GIG)  →  cloudflared ×5  →  nginx 127.0.0.1:8088  →  Go 127.0.0.1:8089
   cf-cache-status         /ready 20243       root public/ (acervo)     socket systemd
   s-maxage 604800                            proxy_cache wj_dyn        SÓ rota dinâmica
```

Medições de agora, uma por camada:

| alvo | comando | resultado medido |
|---|---|---|
| Go `:8089` | `GET /healthz` | `200`, **0,99 ms** |
| nginx `:8088` | `GET /` com `Host: wikijuridica.com.br` | `200`, **25.364 bytes**, 7,2 ms |
| nginx `:8088` | `GET /familia/index.md` | `200`, **65.351 bytes** |
| borda | `GET https://wikijuridica.com.br/healthz` | `200`, **0,202 s**, `cf-cache-status: DYNAMIC`, ray `a3bba5d25ac02eda-GIG` |
| borda | `GET https://wikijuridica.com.br/` | `200`, **`cf-cache-status: HIT`, `age: 31065`** (8 h 37), `cache-control: public, max-age=86400, s-maxage=604800` |

**A linha que resume a pergunta 1 está na última célula**: a home responde `200`
servida do cache da borda com 8 h 37 de idade. Ela responderia igual com a origem
inteira apagada.

---

## 1. Qual instrumento alcança o quê — confirmado, com arquivo:linha

### `tools/check-http-smoke` — NÃO toca rede nenhuma do acervo
`tools/check-http-smoke:30` só executa `tools/run-check http-smoke`; a implementação
é Go (`internal/checks/checks.go`, `checkHTTPSmoke`) e o cabeçalho do próprio
arquivo (`tools/check-http-smoke:6-11`) declara que ele **monta `httpserver.New`
em processo**. O único socket real que ele disca é a rede social:
`internal/checks/http_smoke_redesocial.go:56` (`baseDaRedeSocial = "http://127.0.0.1:8091"`),
`net.DialTimeout` em `:200`.
→ **Fica verde com o túnel caído E com o nginx caído.** Ele prova o handler, não o portal.

### `tools/check-portal-health` — só 127.0.0.1, confirmado
Alvos, exaustivos: `:319` `/`, `:320` `/previdenciario/maternidade-homem/`,
`:321` `/sitemap.xml`, `:331` `/buscar/?q=usucapiao`, `:346` `/familia/index.md`,
`:347` `/.well-known/agent-card.json`, `:364-365` `/redesocial/` e `/redesocial/index.md`
— **todos contra `NGINX = "http://127.0.0.1:8088"` (`:56`)**; e `:330` contra
`GO = "http://127.0.0.1:8089"` (`:58`), a única chamada ao Go direto.
`grep 'wikijuridica.com.br'` no arquivo devolve **apenas** o `SNI` do header `Host` (`:57`).
→ **Zero requisições à produção. CONFIRMADO: passa verde com o túnel caído.**

O caso "o Go respondia e o proxy não" **ele pega**: separa `proxy_quebrado` de
`go_fora`/`busca_fora` (`:456`) e tem reparo próprio para a causa conhecida —
dono errado em `var/nginx/*` depois de `sudo nginx -t`, curado com
`chown -R` + `systemctl reload wikijuridica-nginx` (`:456-473`).

### ⚠ `check-portal-health` GRAVA E ZERA `reparo_ultimo` SEM `--repair` — CONFIRMADO
`:601` `reparo = ""` · `:602-610` grava `ESTADO` **incondicionalmente**, com
`"reparo_ultimo": reparo`. Numa execução sem `--repair`, `reparo` nunca sai de `""`.
Não existe `--nao-gravar`; `argparse` só tem `--repair` (`:310`) e `--json` (`:312`).

Consequência, com a linha que a sofre: a guarda anti-laço lê
`reparo_anterior = anterior.get("reparo_ultimo","")` (`:453`) e só suprime um
segundo disparo de deploy quando `reparo_anterior.startswith("binario_desatualizado")`
(`:470-472`). **Uma execução de diagnóstico entre dois `--repair` apaga essa memória
e o segundo `--repair` volta a disparar `disparar_deploy`.** Também reescreve
`nrestarts`, que é a linha-base da DERIVADA de restart — exatamente a medição que o
vigia existe para fazer (`:17-24`). `reparo_falhas_seguidas` sobrevive (vem de
`anterior`); `reparo_ultimo` não.

**Regra operacional:** durante incidente, **não rode `check-portal-health` à mão**.
Leia a última linha de `data/ops/portal_health.jsonl` ou repita os `curl` você mesmo.
Capacidade que falta: `--nao-gravar`.

### `tools/check-arquitetura-fiel` — estático, zero rede
Lê `docs/arquitetura_fiel_ancoras.tsv` e prova, por âncora, (1) que o arquivo citado
existe e (2) que o símbolo ainda aparece nele (`:18-31`). `grep '127.0.0.1\|8088\|8089\|tunnel'`
no arquivo devolve **zero**. Ele impede a documentação de apodrecer; não diz nada
sobre o portal estar no ar. O próprio cabeçalho declara o limite (`:32-35`).

### `tools/check-tunnel-health` — de dentro, nunca do site público
Lê métricas locais do cloudflared em `127.0.0.1:20243` (`/ready`), o journal atrás de
`network is unreachable` e a derivada de `cloudflared_tunnel_request_errors`.
Cabeçalho: "este vigia NÃO faz requisição ao site publico".

### ✅ `tools/check-edge-live` — **este é o que prova a produção**
`:50` `BASE = "https://wikijuridica.com.br"` · `:52` `ROTA_ORIGEM = "/healthz"`.
A escolha é o ponto: `/healthz` está **excluída da Cache Rule** — conferido na
expressão de `ops/cloudflare/cache-rules.json`
(`… and not starts_with(http.request.uri.path, "/healthz") …`) — então volta sempre
`DYNAMIC` e a requisição **atravessa borda → túnel → nginx → Go** toda vez.
Ele ainda lê **uma URL do acervo sorteada do ÍNDICE** (`uma_pagina_do_acervo`, `:99-115` —
de `wikiuniverso.urls_publicas`, não do diretório `public/sitemaps/`, que tem 62
arquivos dos quais só 34 estão anunciados), para separar "borda viva" de "origem viva".

Timer medido: **a cada 2 min** (`wikijuridica-edge-live.timer`: 21:13:12 → 21:15:12).

⚠ Ele **grava sem pedir**: `data/ops/edge_live.jsonl` em `:232-233`, sem `--gravar`
(o `argparse` tem só `--json` e `--sem-alerta`, `:146-147`). Rodar à mão acrescenta
ponto à série. Use `--sem-alerta` para não notificar o dono num teste.

---

## 1.1 O COMANDO que prova que a produção está no ar

```bash
curl -sS -o /dev/null --max-time 20 \
  -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' \
  -w 'http=%{http_code} t=%{time_total} cf=%header{cf-cache-status} ray=%header{cf-ray}\n' \
  https://wikijuridica.com.br/healthz
```

**Esperado:** `http=200 … cf=DYNAMIC`. **Medido agora:** `http=200 t=0.202136 cf=DYNAMIC ray=a3bba5d25ac02eda-GIG`.

Régua do veredito, pré-registrada:

| o que vier | o que significa | o que fazer |
|---|---|---|
| `200` + `DYNAMIC` | caminho inteiro de pé | segue |
| `200` + **`HIT`/`MISS`/`EXPIRED`** | a Cache Rule derivou e passou a cachear `/healthz`; **a sonda virou mentira** | `tools/check-edge-rule-drift`; não confie em nenhuma leitura de saúde pela borda até corrigir |
| `530` | túnel desconectado (erro 1033) — 530 para **todo** visitante, crawler incluído | `tools/check-tunnel-health`; `systemctl status cloudflared*` |
| `curl` exit 28 | timeout | repetir 1×; se persistir, `check-tunnel-health` + `check-network-health` |
| `200` na home **mas** falha aqui | **a origem caiu e o cache está mascarando** | é o estado exato que `check-edge-live` existe para nomear |

Forma empacotada, com série e alerta: `tools/check-edge-live --json` (grava; `--sem-alerta` para não notificar).

**O sufixo do `cf-ray` é o colo** (`-GIG` = Rio). **O cache da borda é por colo**: um
`MISS` daqui não é `MISS` para um crawler que pousa em outro. Por isso todo veredito
de frescor compara **hash**, nunca a palavra `cf-cache-status`.

---

## 2. Conferir que uma página publicada está servida — os quatro canais e a paridade

### A pedra angular que eu não esperava achar: `/api/v1/citar/{path}` é o ORÁCULO
`internal/httpserver/api_citar.go:65-67` devolve `html_sha256` e `markdown_sha256`;
`:78` devolve `repr_digest` (RFC 9530). E o `html_sha256` **vem do
`published_manifest`**, não de reler o disco: `internal/httpserver/httpserver.go:1426`
(`HTMLSHA256: record.HTMLSHA256`). Logo, comparar esse campo com o corpo servido
pela borda **é a checagem de coerência de artefato de ponta a ponta — manifesto ↔ disco ↔ borda —
numa comparação só**.

### Medido agora, `/previdenciario/maternidade-homem/`, tudo pela borda

| canal | comando | sha256 medido |
|---|---|---|
| **oráculo** `/api/v1/citar` (origem) | `GET 127.0.0.1:8088/api/v1/citar<path>` | html `10f3b349…0d6e` · md `14554d1a…4d89` · repr `sha-256=:EPOzSdNpMZiSug3IYNxFIJXCka8a59kmnwduD81QDW4=:` |
| **HTML pela borda** | `curl -H 'Accept-Encoding: identity' https://…<path> \| sha256sum` | `10f3b349…0d6e` ✅ · `cf=HIT` `age=113980` (31 h 39) |
| **disco** | `sha256sum public<path>index.html` | `10f3b349…0d6e` ✅ |
| **gêmea pela borda** | `curl …<path>index.md \| sha256sum` | `14554d1a…4d89` ✅ · `cf=MISS` · `repr-digest` do header confere |
| **MCP pela borda** | `POST /mcp` `tools/call` `ler_pagina` | `14554d1a…4d89` ✅ · 9.832 bytes · `cf=DYNAMIC` |
| **A2A pela borda** | `POST /a2a/v1` `SendMessage` | `14554d1a…4d89` ✅ |
| **lote pela borda** | `GET /api/v1/lote?desde=…` | **estrutura confirmada, hash NÃO comparado para esta rota** — ver abaixo |
| **variante `Accept: text/markdown`** em `<path>` | `curl -H 'Accept: text/markdown' https://…<path>` | `14554d1a…4d89` ✅ · `content-type: text/markdown` · **`vary: Accept-Encoding, Accept`** · `cf=HIT` **`age=113684`** |

**Paridade de 4 vias (gêmea × MCP × A2A × variante `Accept`), contra o oráculo do
manifesto, provada na produção hoje — sobre 1 rota de 11.106.** Não é a população;
é a prova de que o instrumento funciona pela borda.
**O lote não entra nessa conta**: a rota-alvo não estava no lote lido
(`area=previdenciario` truncou em 199 de 638) e o lote por `desde=` só trouxe as notícias
do dia — **hash do lote para esta rota: não medido**.

**Achado de bônus, medido:** a variante `Accept: text/markdown` de `<path>` tem
**`age=113684`** contra **`age=113980`** do HTML da mesma URL. Idades diferentes provam
que são **dois objetos de cache independentes** — exatamente o terceiro objeto que
`check-edge-frescor` declara não sondar. E ele **existe, responde e cacheia**.

### As pegadinhas que custaram uma rodada cada — vão no runbook

- **MCP** responde `tools/call` **sem `initialize`**, e devolve `text/event-stream`:
  o JSON está na linha `data: `. Nome da ferramenta `ler_pagina`
  (`internal/httpserver/mcp.go:61`), argumento `caminho`. Mande
  `Accept: application/json, text/event-stream`.
- **A2A**: o caminho é **`/a2a/v1`** (`internal/httpserver/a2a.go:71`) e o método é
  **`SendMessage`**, não `message/send` (`a2a.go:134`). Sem `A2A-Version: 1.0` o
  servidor recusa com **-32009** (medido). Nome errado de método → **-32601** (medido).
  A resposta está em `result.message.parts[0].text`; **a part vem SEM a chave `kind`**
  e com `role: "ROLE_AGENT"` (medido) — parser que chaveia por `kind` lê nada.
- **`/api/v1/lote` não tem filtro por caminho.** O filtro é `desde`, `area`,
  `limite`, `cursor` (`internal/httpserver/api_lote.go:173-175`). Medido:
  `?area=previdenciario&limite=200` devolveu **199 páginas de 638**, com
  `truncado_por: "orcamento_bytes"` (teto **2.097.152 bytes**) — e a página-alvo
  **não estava nele**. Pescar uma página antiga custa paginação de cursor.
  **Para página recém-publicada o instrumento certo é `desde=`, e resolve em UMA chamada**:
  medido `?desde=2026-09-14&limite=5` → exatamente as 5 páginas do período,
  `total: 5, restantes: 0`, todas `/noticias/`.
- **Compare corpo com `Accept-Encoding: identity` no CLIENTE.** Isso **não** chega à
  origem: o log cru registrou `ae="gzip, br"` para a minha requisição `identity`
  (medido em `/var/log/nginx/wikijuridica/access.log`), porque a Cloudflare reescreve
  o `Accept-Encoding` a montante. Compare bytes no cliente; nunca infira a variante
  da origem pelo seu próprio header.

### ⚠⚠ O ORÁCULO É UM RETRATO DO BOOT — e isso muda a especificação
`buildAPIPublishedPages` é chamada **dentro de `httpserver.New()`**:
`internal/httpserver/httpserver.go:1071`, e `New()` roda **uma vez, no boot**
(`:929`). `agentsurface.go:86-87` diz o mesmo do lote: *"resolve o índice do acervo
uma vez no boot"*. Logo **as cinco superfícies de máquina — `/api/v1/citar`,
`/api/v1/lote`, a gêmea `.md`, MCP `ler_pagina` e A2A `SendMessage` — estão congeladas
no retrato do boot** até o processo reiniciar. O nginx, ao contrário, serve
`public/` **do disco, a cada requisição**.

**Medido hoje, e a janela é real:**

| evento | instante medido |
|---|---|
| `public/noticias/stj-20260915/index.html` escrito | **12:28** -03 |
| `wikijuridica-server` parado | **12:29:55** -03 (journal) |
| subiu | **12:30:27** -03 → **32 s de boot** |
| `sudo systemctl restart wikijuridica-server` (explícito, `PWD=/opt/wiki`) | **12:30:27** -03 |
| subiu de novo | **12:30:50** -03 → **23 s de boot** |
| `NRestarts` | **0** (reinício limpo pela cadeia, não laço) |

→ Entre **12:28 e 12:30:50** (≈ 2 min 50 s) o nginx já servia o HTML novo e as cinco
superfícies de máquina ainda não conheciam a página. Hoje isso fechou porque a cadeia
reiniciou o Go. **Boot medido: 23–32 s** — é a janela em que `/mcp`, `/a2a`, `/api/*` e
a gêmea dependem do `use_stale` do `proxy_cache wj_dyn`.

**E aqui está o defeito que isso revela no P6, com dois fatos medidos:**
1. **`tools/publicar-estoque` NÃO EXISTE** (`ls`: "Arquivo ou diretório inexistente").
   A ferramenta real é **`tools/publicar`**. O P6 nomeia um binário inexistente.
2. **`tools/publicar` não reinicia o Go**: `grep -n "systemctl\|restart\|deploy-publico\|wikijuridica-server"`
   devolve **zero**. Ele prepara o terreno e publica (lock órfão, censo, gêmeas `.br`),
   e só. Quem reinicia é o `tools/deploy-publico` (`:37` `SERVICE=wikijuridica-server`,
   `:847-850`, `:867`).

→ **O oneshot do P6, como está desenhado, gravaria as páginas em `public/` e deixaria
as cinco superfícies de máquina servindo o acervo PRÉ-publicação por tempo indefinido.**
O canal humano ficaria certo e o canal de máquina — que o §12 declara ser o produto —
ficaria velho, com `200` em tudo e nenhum instrumento acusando. O P6 precisa de um passo
de reinício pela cadeia, e o `check-publicado-no-ar` precisa da **leitura 0** abaixo.

### A confissão do CLAUDE.md §7 está SUPERADA — com uma ressalva que é a lacuna real
`internal/httpserver/mcp_paridade_tres_vias_test.go`, `TestParidadeQuatroViasGemeaLoteMCPA2A`,
compara **gêmea × lote × MCP × A2A byte a byte**, sobre uma rota escolhida por ter
FAQ + Percursos + Relacionados (as três seções condicionais que divergem primeiro).
**Mas ele roda em memória** (`servidorDeCaminhosPai(t)`, `httptest`). A paridade de
quatro vias está provada no handler e **nunca pela borda**.

---

## 3. Cache de borda: TTL, estados, e leitura fresca sem purgar tudo

### TTL medido na linha
`cache-control: public, max-age=86400, s-maxage=604800` — **7 dias** para cache
compartilhado, 1 dia para o navegador. Emitido pelo nginx em
`ops/nginx/wikijuridica.conf:1367` (`more_set_headers -s '200 304'`).
A borda usa `edge_ttl.mode: "respect_origin"` (`ops/cloudflare/cache-rules.json`),
então honra `s-maxage` onde existe e `max-age` onde não (300 s: sitemap,
descritores `.well-known`, oauth/jwks, robots) — sem lista de rota por superfície.
`status_code_ttl`: 400–428 e 430–499 → **60 s**; 500–599 → **-1 (no-store)**;
**429 fora de propósito** (cachear rate limit pregaria 60 s de recusa por URL e por colo,
inclusive ao Googlebot).

### Os estados
- **HIT** — servido do cache **deste colo**, sem tocar a origem.
- **MISS** — não está neste colo; buscou na origem (possivelmente no tier superior do Tiered Cache).
- **EXPIRED** — estava, o TTL venceu, revalidou com a origem.
- **DYNAMIC** — a Cache Rule **não cacheia** esse caminho. Prefixos excluídos, da própria
  expressão: `/buscar/`, `/contato/`, `/healthz`, `/readyz`, `/livez`, `/metrics`,
  `/api/`, `/mcp`, `/a2a`, e `/.well-known/agent-card.json`.
- **BYPASS** — regra 2, sessão em `/redesocial/` (cookie `wjsession`).

**Prova medida de que HIT não é frescor:** `/` com `age=31065` (8 h 37) e
`/previdenciario/maternidade-homem/` com `age=113980` (31 h 39), ambos `HIT`, ambos
com `s-maxage=604800` — qualquer um dos dois pode estar **até 7 dias** atrás do disco.

### Leitura FRESCA sem purgar — duas formas, a primeira é de graça
1. **Leia por uma rota que a regra exclui.** `/api/v1/citar<path>`, `/api/v1/lote`,
   `/mcp` e `/a2a/v1` são **DYNAMIC por regra** (medido: os quatro voltaram `DYNAMIC`).
   Então **a verdade fresca do Markdown de uma página está sempre a uma chamada de
   distância, sem purga nenhuma.** Só o HTML do acervo e a gêmea `<path>index.md`
   são cacheáveis.
2. **Purga dirigida**, quando o que precisa ficar fresco é o HTML para o visitante/crawler:
   `tools/purge-edge-cache --url <URL absoluta>` (repetível) · `--tag area-<nome>` ou
   `--tag wj-acervo` · `--de-arquivo <lista>` · sempre `--dry-run` antes.
   Lotes de **100 por chamada** (`tools/purge-edge-cache:17-26`, citando a doc oficial).
   Plano Free: **5 chamadas/min**, bucket 25, para tag/prefixo/everything.

### ⚠ O TETO que já fez a purga virar "tudo": `--teto-por-url`, default **3000**
`tools/purge-edge-cache:137`. **Acima dele o programa degrada para
`{"purge_everything": True}` (`:209`)** — e `check-edge-frescor` documenta que ele o faz
**em silêncio**, razão pela qual passa `--teto-por-url` igual ao tamanho da lista.
→ **Regra: toda vez que entregar uma lista ao `purge-edge-cache`, passe
`--teto-por-url` = tamanho da lista.** Senão uma lista grande purga as ~11 mil rotas
e joga fora ~870 s de aquecimento.

Um segundo teto, diferente e a montante: `tools/generate-page-content-revision --purge-targets`
já caiu em teto de churn com exit 1, e o deploy então imprimiu
"registro de revisao indisponivel" e purgou tudo (`tools/deploy-publico:929`, `:1358-1359`;
corrigido, com teste). **Antes de purgar à mão, leia `data/ops/edge_cache_purge.jsonl`.**
Medido agora, as duas últimas linhas: `scope: "10 URL(s) em 1 lote(s)"` e
`"29 URL(s) em 1 lote(s); 1 tag(s) em 1 lote(s)"` — dirigidas, não "tudo". Se o deploy
já gravou purga total, **purgar de novo joga fora o aquecimento**.

### ORDEM OBRIGATÓRIA: origem primeiro, borda depois
`tools/purge-origin-cache --rota <path>` (repetível; tem `--gemeas-de-area` e `--seco`)
→ `tools/purge-edge-cache --url … --teto-por-url <len>` → **reler**.
Invertido, purgar só a borda **repopula o Tiered Cache com o conteúdo VELHO**
(CLAUDE.md §1, medido 2026-09-05: `HIT`, `age: 0`, campos = 0, 5×).
`check-edge-frescor --purgar` já implementa essa ordem.

Depois da purga: `tools/warm-edge-cache --de-arquivo <lista> --rps 12 --so-frios`
(`--so-frios` faz HEAD antes do GET e pula o que a borda já serve em HIT; o default
de `--rps` é 25, metade do teto de 50/s da zona). O timer `wikijuridica-edge-warm`
passa só às 04:20 e 16:20 UTC — medido: próximo às 01:25 -03.

---

## 4. A sonda não pode fraudar a métrica — confirmado nos dois gravadores

`internal/wikijuridicabot/bot.go:143-149`, `AplicaSondaInterna(req)`, escreve **duas** coisas:

```
User-Agent: Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)
X-Warming-Request: true
```

(UA montado por `UserAgentComProposito(PropositoSondaInterna)`, `:122-127`; o prefixo
`Mozilla/5.0 (compatible;` é `:76` e é o que o WAF do gov.br exige, não disfarce.)

**A exclusão tem DOIS gravadores, e isso importa porque o acervo não passa pelo Go:**
- **Go** — `internal/httpserver/access_log.go`, campo `Warming bool \`json:"warming"\``;
  `tools/accessledger.py:249` e `:374` descartam todo registro com `warming` ou
  `bot_simulation` verdadeiros, e `:516-517` os contabiliza em `warming_excluded`.
- **nginx** — `log_format wj_main` carrega **`warm=$http_x_warming_request`**
  (`ops/nginx/wikijuridica.conf:61`). **É este que cobre as ~11 mil páginas estáticas**,
  que nunca chegam ao Go.

**PROVADO na linha, agora:** minhas sondas estão em
`/var/log/nginx/wikijuridica/access.log` com `warm=true` — p.ex.
`"GET /api/v1/lote?desde=2026-09-14&limite=5 HTTP/1.1" 200 57580 "…sonda-interna)" … warm=true ae="gzip, br" ocs=MISS`.
(1.932 linhas com `sonda-interna` hoje no log cru, as minhas entre elas.)

`X-Bot-Simulation: true` é o marcador **separado** para ensaio de "o que o Googlebot vê"
(`bot_sim=$http_x_bot_simulation` no mesmo `log_format`). Nunca sair à rede com UA de bot
real; simular Googlebot só é legítimo contra o nosso handler, em `httptest`.

### ⚠ Achado: três UA escritos à mão no caminho de sonda
Medidos no log de hoje e no código: `wikijuridica-watchdog/1.0 (+interno; nao-indexar)`
(`tools/check-portal-health:76`), `wikijuridica-edge-audit/1.0` (`tools/check-edge-live:54`),
`wikijuridica-superficie-probe/1.0` (`tools/check-corpo-integro-na-borda:57`).
**Nenhum dos três é a identidade canônica de `internal/wikijuridicabot`.** Não são
desonestos (identificam-se e levam `X-Warming-Request`), mas são três fontes de verdade
onde o CLAUDE.md §11 manda haver uma. Correção barata: fazer as três derivarem de
`UserAgentComProposito(PropositoSondaInterna)`.

---

## 5. A lacuna, e a especificação do que falta

### O que JÁ existe, e é mais do que o plano supunha: `tools/check-edge-frescor`
50.106 bytes, 2026-09-11. Por rota, **5 leituras**: HTML pela borda · gêmea pela borda ·
gêmea no **Go :8089** · gêmea no nginx :8088 nas **duas** variantes de `Accept-Encoding`
que a borda pede (`"gzip, br"` e vazia). E **3 comparações contra a VERDADE, nunca contra
o que um cache diz de si**:
- HTML pela borda × `sha256(public<path>/index.html)`, com **`published_manifest.html_sha256`
  como oráculo do disco**; disco ≠ manifesto → classe `disco_diverge_do_manifesto`, e
  **não purga** (purgar traria à borda um arquivo que ninguém atestou);
- gêmea pela borda × bytes do **processo Go** (não do nginx: ler `:8088` com `identity`
  devolve o Go fresco e mente sobre o que a borda recebe — medido 2026-09-09);
- `Repr-Digest` de cada variante × hash do Go → `origem_cache_velha`.

Exit **0** fresco / **1** velho ou disco divergente / **2** não mediu.
**Read-only sem `--gravar`.** `--purgar` faz origem → borda → relê, e se a purga não
surtiu efeito o exit é 2 ("purga que não purga é instrumento quebrado, não veredito").
Sonda honesta, concorrência 4, ≤ 8 req/s à borda.

Três janelas: `--dia`, `--desde-horas N`, `--desde-ledger SNAPSHOT`.

**Duas armadilhas de janela, uma já guardada e outra não:**
- *Janela vazia* — já tem guarda. `alcance_do_ledger` (`:250-284`) separa "nada mudou"
  de "o ledger não alcança o dia" e devolve **exit 2** com mensagem explícita
  (`:1020-1038`). Isso importa **hoje**: `--dia` sem argumento é "hoje **em UTC**", e às
  21:08 -03 já é 09-16 UTC (medido: `data/ops/access/nginx-2026-09-16.jsonl` existe, 44 KB,
  com 09-15 ainda correndo localmente). Depois das 21:00 BRT a execução sem argumento
  pergunta pelo dia errado — e cai em exit 2, **não** em verde falso.
- *Janela do conjunto errado* — **não tem guarda, por construção** (`:300-307`). Depois de
  um `deploy-publico --ressemear`, os bytes servidos mudam **sem** avançar `revised_on`:
  `--dia`/`--desde-horas` conferem as rotas da véspera, acham tudo fresco e saem **verdes
  sobre o conjunto errado**. Só `--desde-ledger` enxerga, e ele exige um **snapshot tirado
  ANTES da publicação** — que não se recupera depois:
  ```bash
  cp data/ops/page_content_revision.jsonl        .agents/runtime/edge-frescor/ledger_antes_<rotulo>.jsonl
  cp data/ops/page_content_revision_formula.txt  .agents/runtime/edge-frescor/ledger_antes_<rotulo>.formula.txt
  ```
  (precedente no disco: `ledger_antes_ressemear_20260911.jsonl`, 2,7 MB, + `.formula.txt`).

### O que ele NÃO responde — a lacuna exata
1. **Não tem modo por rota.** `argparse` (`:834-844`) só tem `--dia`, `--desde-horas`,
   `--desde-ledger`, `--max` (default **2000**), `--purgar`, `--gravar`. **Não há `--rota`.**
   "Acabei de publicar estas 14 URLs, estão certas?" não tem como ser perguntado.
2. **Cobre 2 dos canais de máquina.** MCP `ler_pagina`, A2A `SendMessage` e `/api/v1/lote`
   ficam de fora. A paridade das quatro vias existe, mas **só em memória**.
3. **Ele nomeia o próprio ponto cego**: a variante `Accept: text/markdown` de `<path>` é um
   **terceiro objeto de cache** (a regra declara `vary.headers.accept` com `media_types:
   ["text/markdown"]`) e **não é sondada**.
4. Não olha o lado do bot.

**→ Não existe hoje um comando único que responda "a produção está servindo o que eu
acabei de publicar, e está certo".** Existem todas as peças e nenhuma composição.

---

### ESPECIFICAÇÃO — `tools/check-publicado-no-ar`

> Dado um conjunto de caminhos recém-publicados, prova que a borda serve exatamente o
> que o manifesto atesta, nas seis superfícies, e diz o que purgar.

**Entrada**, nesta precedência:
- `--rota <path>` (repetível) — **a primitiva que o repo não tem**
- `--de-arquivo <lista>` — o mesmo arquivo que `deploy-publico` já monta em `PURGE_ALVOS`
  a partir de `generate-page-content-revision --purge-targets` (`deploy-publico:929`),
  para o deploy entregar a própria lista
- `--desde-ledger <snapshot>` — delega a janela ao `check-edge-frescor`
- `--dia AAAA-MM-DD` — **obrigatório e explícito, sem default**, precisamente para a
  armadilha UTC/local não poder disparar calada

**Por rota, 6 leituras e 6 asserções:**

| # | leitura | asserção | classe quando falha |
|---|---|---|---|
| **0** | **`GET borda /api/v1/lote?limite=1` → `fim.total`, contra a contagem do `published_manifest.jsonl` no disco; e `ExecMainStartTimestamp` do `wikijuridica-server` contra o mtime mais novo de `public/<rota>/index.html`** | **o Go carregou DEPOIS da publicação** | **`go_desatualizado`** — tratamento **"reiniciar pela cadeia, NÃO republicar, NÃO purgar"**. Sem esta leitura, a leitura 1 devolve 404 e o gate diagnostica `fora_do_manifesto`, que manda republicar uma página que já está no disco — **o conserto errado** |
| 1 | `GET {origem}/api/v1/citar<path>` | responde 200 | `fora_do_manifesto` (a publicação não pousou) — **só válido depois de a leitura 0 passar** |
| 2 | `sha256(public<path>index.html)` | `== html_sha256` | `disco_diverge_do_manifesto` — **NÃO purgar**, republicar |
| 3 | `GET borda <path>` (`Accept-Encoding: identity`) | `== html_sha256` | `borda_html_velha`; grava `cf-cache-status`, `age`, colo do `cf-ray` |
| 4 | `GET borda <path>index.md` **e** `GET borda <path>` com `Accept: text/markdown` | `== markdown_sha256` | `borda_gemea_velha` / `borda_variante_accept_velha` ← **fecha o ponto cego 3** |
| 5 | `POST borda /mcp` `ler_pagina` **e** `POST borda /a2a/v1` `SendMessage` (`A2A-Version: 1.0`) | `== markdown_sha256` | `mcp_divergente` / `a2a_divergente` |
| 6 | `GET borda /api/v1/lote?desde=<dia>&limite=200`, paginando `proximo_cursor` enquanto `restantes>0`, teto `--max-lotes` | toda rota de entrada presente, `markdown` com `== markdown_sha256` | `lote_ausente` / `lote_divergente`; registrar `truncado_por` |

As leituras 5 e 6 são **DYNAMIC por regra**: medem a ORIGEM pelo túnel e **nunca podem
ser "cache velho"**. Divergência ali é divergência real de código entre canais — a coisa
que o teste em memória não pega em produção.

**Exit codes**, na mesma gramática do `check-edge-frescor`:
- **0** — toda rota, toda superfície, bate com o manifesto. *(nunca 0 com zero rotas conferidas)*
- **1** — mediu e está errado. Subclassificado, porque o tratamento difere:
  `borda_*_velha` → purga (origem → borda → relê); `disco_diverge_do_manifesto` → republicar,
  **jamais purgar**; `mcp|a2a|lote_divergente` → defeito de código, purga não cura;
  `fora_do_manifesto` → a publicação não pousou.
- **2** — não mediu: manifesto/arquivo ausente, origem fora, sonda incompleta, lista acima
  de `--max`, `--dia` não informado, purga pedida que não surtiu efeito.

**Escrita:** nada sem `--gravar` (CLAUDE.md §4 / BUG-236). Com `--gravar`, uma linha por
execução em `data/ops/publicado_no_ar.jsonl`, schema `publicado_no_ar_v1`, com o par de
sha por rota e o colo — para "estava certo quando publiquei" continuar provável depois.

**Identidade:** `wikijuridicabot.AplicaSondaInterna` — **não** uma quarta string à mão.
**Limitador:** o do `check-edge-frescor` (concorrência 4, ≤ 8 req/s à borda); leituras
locais sem limite.
**Purga:** nunca chamada de API própria. Delega a `purge-origin-cache --rota` e
`purge-edge-cache --url … --teto-por-url <len(lista)>` — teto explícito, para lote grande
não degradar para `purge_everything` em silêncio.

**Onde entra no runbook:**
- passo **9.5 do `tools/deploy-publico`**, depois da purga do próprio deploy e **ANTES da
  submissão ao IndexNow** — anunciar a um buscador uma URL que a borda ainda serve velha é
  a única ordem que não se desfaz;
- gate que o **oneshot publicador autônomo do P6** roda antes de declarar sucesso,
  alimentado pela lista de caminhos que ele mesmo gravou.

---

## 6. "Comportamento dos bots de IA, AGORA" — o atalho, e o limite dele

**O ledger tem lag de uma hora; o log cru não tem lag nenhum.**
`data/ops/access/nginx-*.jsonl` é derivado por `wikijuridica-origin-access-ledger.timer`,
que roda **de hora em hora** (medido: última 21:08, próxima 22:08). Essa é a "janela de
horas" — e o atalho é `/var/log/nginx/wikijuridica/access.log`, que tem a linha no
instante em que a requisição pousa.

Medido agora, janela **20:00–21:14 -03 de 2026-09-15**, **950 linhas de origem**.
Tabela de **bots de busca E de IA**, não só de IA — Applebot (sem o sufixo
`-Extended`) é Siri/Spotlight, busca, não treino:

| agente | linhas |
|---|---|
| Applebot | 37 |
| bingbot | 4 |
| Perplexity | 3 |
| OAI-SearchBot | 3 |
| ChatGPT-User | 3 |
| Googlebot | 2 |

**O limite honesto desse número, que tem de ir escrito junto:** o log de origem só vê o
que **deu MISS na borda**. Ausência ali **não é ausência** — o acervo tem `s-maxage` de 7
dias e a maior parte do rastreio é servida pela Cloudflare sem tocar a origem. A
população está na série de borda `data/ops/edge_bot_agents_daily.jsonl` (34 MB, escrita às
21:03 hoje), que é **cumulativa**: lê-se a **última linha por `date`**, nunca a soma das
linhas.

---

## 7. Cadência medida dos instrumentos vivos (`systemctl list-timers`, 21:14 -03)

| unit | cadência medida | o que alcança |
|---|---|---|
| `wikijuridica-tunnel-health` | **30 s** | cloudflared local (`:20243`) |
| `wikijuridica-edge-live` | **2 min** | **a produção pela borda** (`/healthz` DYNAMIC) |
| `wikijuridica-watchdog` (`check-portal-health`) | **2 min** | só `127.0.0.1` (`:8088`/`:8089`/`:8091`) |
| `wikijuridica-origin-access-ledger` | **1 h** | deriva `data/ops/access/*.jsonl` do log cru |
| `wikijuridica-origin-warm` | **3 h** | enche o `proxy_cache wj_dyn` (sem ele o `use_stale` não tem o que servir) |
| `wikijuridica-edge-warm` | **04:20 e 16:20 UTC** | aquecimento da borda |
| `wikijuridica-edge-frescor` | **diária** (~06:40 -03) | frescor de borda+origem das rotas carimbadas |

*(Cada cadência acima vem de UM intervalo observado em `systemctl list-timers` às
21:14 -03 — é a cadência declarada pelo systemd, não uma média de execuções.)*

---

## 7.1 ⏱ RISCO DATADO, MEDIDO AGORA — não é margem de calendário, é expiração no disco

Encontrado ao ler o journal do reinício de hoje. `tools/sweep-sitemap-carencia-expirada`,
executado agora (read-only), diz:

```
ATENCAO: pages-0094.xml vence em 2026-09-16 07:50Z — menos de 48h.
         Sem publicacao ou varredura ate la, o boot do servidor trava.
ATENCAO: pages-0095.xml vence em 2026-09-16 07:50Z — menos de 48h.
carencia: 6 shard(s) fora do indice | 0 vencido(s) | 2 vencendo em menos de 48h
```

**Confirmado no código, com as palavras do próprio arquivo** —
`internal/publishedmanifest/publishedmanifest.go:495-513`:

> *"Como esta validação roda no boot (httpserver.go:479-482 → New devolve erro e o
> servidor não sobe), reprovar aqui não é um aviso: **é o portal fora do ar**."*

Mecânica: shard em `public/sitemaps/` que não esteja em `public/sitemap.xml` reprova em
`:513`; o único escape é o `continue` de `:509`, condicionado a
`sitemapgrace.ValidRetirement(data, time.Now().UTC())`. **Vencida a carência, o escape
deixa de valer e o boot falha.**

**A aritmética, medida (`date -u` = 2026-09-16T00:23:03Z):**

| evento | instante UTC | relação |
|---|---|---|
| **agora** | 00:23:03Z | — |
| `wikijuridica-daily-content.timer` (a onda publica e reinicia o Go) | **07:31:33Z** | 18 min **antes** do vencimento |
| **vencimento de `pages-0094` e `pages-0095`** | **07:50:00Z** | **T+7h27m** |
| `wikijuridica-sitemap-shard-grace.timer` (a varredura) | **08:19:09Z** | **29 min DEPOIS do vencimento** |

E a onda de ontem reiniciou o Go às **15:29:55Z**, ~8 h depois de começar às 07:24:45Z —
isto é, **o reinício da onda cai muito depois de 07:50Z**.

**Consequência se nada renovar a carência antes:** o próximo boot do Go falha, e cai o
**canal dinâmico inteiro** — busca, gêmea Markdown, `/api/v1/*`, MCP, A2A. O nginx
continua servindo o acervo estático, então **`check-http-smoke` e a home pela borda
ficariam verdes**; quem acusaria é `check-portal-health` (`busca_fora`) e
`check-edge-live` (`/healthz` é DYNAMIC e atravessa até o Go).

**Não medido, e é o que decide se o risco se realiza:** se o passo de publicação da onda
das 07:31Z renova a carência desses dois shards antes de reiniciar o Go. A mensagem da
própria ferramenta diz "sem **publicação** ou varredura" — ou seja, publicar também
resolve. Mas a **ordem** (publicar → reiniciar → varrer 29 min depois) é apertada, e o
teto é físico e datado. Verificar isto **antes** de disparar qualquer passo de P1b/P6 que
reinicie o Go.

**Nada aqui obriga a esperar horas.** As duas sondas que dizem "a produção está no ar"
rodam a cada 2 min, e as duas podem ser repetidas à mão em menos de meio segundo.

---

## 8. Resumo do que falta EXISTIR

0. **Passo de reinício do Go no oneshot do P6** — e a correção do nome: o plano manda
   rodar `tools/publicar-estoque`, **que não existe**; a ferramenta é `tools/publicar`,
   e ela **não reinicia o Go**. Sem reinício, as cinco superfícies de máquina servem o
   acervo pré-publicação indefinidamente.
1. `tools/check-publicado-no-ar` — especificado acima, **com a leitura 0
   (`go_desatualizado`)**. **É a lacuna central.**
2. `--rota` em `tools/check-edge-frescor` (ou o item 1 o absorve).
3. `--nao-gravar` em `tools/check-portal-health` — hoje toda execução de diagnóstico
   apaga `reparo_ultimo` e reescreve a linha-base de `nrestarts`.
4. `--gravar` em `tools/check-edge-live` — hoje grava sempre, contra a regra do §4 / BUG-236.
5. Paridade dos 4 canais **contra a produção**, não só em `httptest` (item 1, leituras 5-6).
6. Sonda da variante `Accept: text/markdown` de `<path>` — **terceiro objeto de cache
   confirmado por medição** (`vary: Accept-Encoding, Accept`; `age=113684` contra
   `age=113980` do HTML da mesma URL), hoje não sondado por ninguém (item 1, leitura 4).
9. Renovar/varrer a carência de `pages-0094.xml` e `pages-0095.xml` **antes de 07:50Z de
   2026-09-16** — ou provar que o passo de publicação da onda das 07:31Z a renova. Ver §7.1.

## 9. O que o advisor mudou

Chamado com o entregável já no disco. Mudou **três coisas**, todas verificadas por
medição própria antes de eu adotar:

1. **Mudou a especificação (bloqueante).** Apontou que o oráculo `/api/v1/citar` e os
   quatro canais de máquina são **retrato do boot**, e que meu gate classificaria
   "Go desatualizado" como `fora_do_manifesto` — mandando republicar uma página que já
   está no disco. **Verifiquei e confirmei**: `buildAPIPublishedPages` em
   `httpserver.go:1071`, dentro de `New()`; página escrita 12:28, Go reiniciado
   12:29:55 e 12:30:27→12:30:50; boot de 23–32 s. Ele mandou eu procurar em vez de
   adivinhar se o publicador reinicia o Go — **procurei, e achei mais do que ele previa**:
   `tools/publicar-estoque` **não existe** e `tools/publicar` **não reinicia o Go**.
   Resultado: **leitura 0 / classe `go_desatualizado`** na especificação, e o item 0 das
   lacunas (defeito no desenho do P6).
2. **Corrigiu um exagero meu.** Eu escrevi "paridade de 5 vias provada na produção".
   Eram **4 vias sobre 1 rota de 11.106**, e o **hash do lote para aquela rota nunca foi
   comparado**. Corrigido no texto; a cadência dos timers também passou a dizer que é a
   declarada pelo systemd, não uma média.
3. **Mandou medir o que eu só havia especificado.** A variante `Accept: text/markdown`
   de `<path>`: eu a colocara na leitura 4 sem nunca ter confirmado que existe.
   **Medi**: existe, responde `text/markdown`, tem `vary: Accept-Encoding, Accept` e
   `age` próprio — **é mesmo um terceiro objeto de cache**, e agora está provado em vez
   de suposto.

**O que eu NÃO mudei por causa dele:** nada foi trocado em silêncio, e não houve
conflito com medição minha. O rótulo da tabela de bots (Applebot é busca, não treino)
eu acatei como escrito.

**O que ele não viu, e nasceu de verificar o ponto 1:** o risco datado do §7.1 —
`pages-0094.xml`/`pages-0095.xml` vencem em **2026-09-16 07:50Z** e travam o **boot** do
servidor, com a varredura agendada **29 min depois** do vencimento.
7. As três sondas com UA escrito à mão derivando de
   `wikijuridicabot.UserAgentComProposito(PropositoSondaInterna)`.
8. Pré-passo obrigatório do runbook de `--ressemear`: snapshot de
   `page_content_revision.jsonl` + `.formula.txt` **antes** da publicação — sem ele
   `check-edge-frescor` fica verde sobre o conjunto errado, e não se recupera depois.
