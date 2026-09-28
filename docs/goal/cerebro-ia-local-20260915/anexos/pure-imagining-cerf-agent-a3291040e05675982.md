# Varredura 4 — RISCO OPERACIONAL E ROLLBACK POR FRENTE

Sessão 2026-09-15, PLAN MODE (somente leitura). Tudo abaixo foi medido nesta
sessão, com o comando ao lado. Onde não medi, está escrito "não medido".

## 0. Estado de partida, medido agora

| fato | valor medido | comando |
|---|---|---|
| índice git | **0 arquivos staged** | `git diff --cached --name-only` |
| `go.mod`/`go.sum` | **limpos** | `git status --porcelain go.mod go.sum` |
| atestação do validador | **VERDE** `sha256:beb3ac7e…` | `./tools/check-validator-attestation` |
| `published_manifest.jsonl` | 11.106 linhas / 11.106 `unique_intent_id` | `./tools/check-contrato-vs-medicao` |
| CLAUDE.md declara | 11.039 páginas | idem |
| último commit do manifesto | **2026-09-10 17:06** `315ac61b` (11.039 registros) | `git log -1 -- data/editorial/published_manifest.jsonl` |
| delta não-commitado do manifesto | **+10.946 / −10.879 linhas** | `git diff --numstat` |
| flock pesado `/tmp/opt-wiki-agent-heavy.lock` | LIVRE, inode **39454263** | `flock -n` + `stat -c %i` |
| bancada diária | 2026-09-15 04:48:12 → 05:48:54 = **60 min 42 s**, segura o flock | `systemctl show wikijuridica-qualidade-diaria.service` |
| próxima bancada | **2026-09-16 04:47:17 -03** | `systemctl show …timer` |
| grafo do validador | **98 pacotes** `portaljuridico/*` | `go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` |
| `check-units-instaladas` | VERDE, 126 units, 3 avisos de cópia | `./tools/check-units-instaladas` |
| `check-units-alarme` | VERDE; 64 .service, 55 exigem OnFailure, **22** mascaram exit | `./tools/check-units-alarme` |
| `check-lastmod-causalidade` | **VERDE**: 11.116 rotas, 2.215 revisões reais, **0 datas fabricadas** | `./tools/check-lastmod-causalidade` |
| `check-frescor-canal-diario` | **exit 1** (PIPESTATUS), 1 canal estagnado | `./tools/check-frescor-canal-diario` |

## 1. O pre-commit: o que compila, quanto custa, e o que obriga

`.githooks/pre-commit`, 811 linhas, `core.hooksPath=.githooks`. Ordem real
(linhas sem comentário):

1. **:158** `git diff --cached --quiet -- .` → se há QUALQUER coisa staged
   (conteúdo inclusive) materializa e roda
   `tools/check-go-index-compile-closure` sobre o **índice inteiro**, não sobre
   o pathspec. Orçamento `90 s × fator de carga (1..4)`, wall = orçamento + 5 s.
   O fator sai de `/proc/loadavg ÷ nproc`, arredondado para cima, capado em 4.
   → **É por isso que índice sujo custa o orçamento de quem commitar depois:
   o trabalho é "compilar a closure do índice", e o índice é compartilhado.**
2. **:187 `check-contrato-vs-medicao` — INCONDICIONAL.** Lê o
   `published_manifest.jsonl` **da worktree** e o `CLAUDE.md` da worktree.
3. **:195** `check-produto-nao-some-do-worktree` — incondicional.
4. **:204** `check-bin-versao-do-toolchain` — incondicional.
5. **:210** `check-sca-govulncheck-evidence` — só se `go.mod|go.sum|tools/sca/go.*`.
6. **:221 `check-atestacao-grafo-no-commit` — INCONDICIONAL.**
7. **:229** `check-digest-do-bundle-no-commit` — incondicional.
8. **:237** analytics (`check-analytics-loader` + `check-analytics-contract`)
   disparados por `internal/(webanalytics|pageinline|webmcp|seo|render|htmlpolicy|httpserver)/`
   ou `ops/nginx/security-headers.conf`.
9. **:300 `check-redesocial-completude`** disparado por **qualquer** `^internal/`
   ou `^cmd/`. Exit 75 = lock de outra sessão (vira aviso, não barra).
10. **:340** teste focado dos pacotes tocados. **Teto de 6 pacotes**: acima
    disso ele AVISA e **não roda nada** (falso conforto). Timeout
    `780 s × fator`.
11. **:345** caso especial: `internal/v2ingest` tocado só pela atestação →
    `-run 'Attestation|Fingerprint'` (86 s medidos contra 611 s da suíte).

**O que isso obriga na ordem dos commits deste plano:**

- **Esvaziar o índice entre commits.** Está vazio agora (medido). Commit com
  `git add <caminho exato>` e `git commit -F <arquivo>` em comandos separados.
- **Commits de Go e de dado nunca no mesmo índice**: um commit de dado paga a
  closure do Go que estiver staged junto.
- **P0 (CLAUDE.md) antes de P6 (publicação em massa)** — ver §3.
- Commits pesados (Go) fora da janela 04:47–05:50 −03, quando a bancada segura
  `/tmp/opt-wiki-agent-heavy.lock` por 60 min 42 s.
- Em qualquer commit que toque >6 pacotes Go, o teste focado **não roda**: a
  suíte dos pacotes tem de ser rodada à mão antes de considerar verificado.

## 2. Reatestação do grafo — quem entra, e como se descobre

`tools/check-atestacao-grafo-no-commit` (lido inteiro): lê só o **índice** do
commit; ignora `*_test.go`; **`go.mod` e `go.sum` contam SEMPRE**; para os
demais `.go` resolve o diretório e compara com
`go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock`. Escape: se
`check-validator-attestation` já está verde contra o disco, passa.

Medição desta sessão (98 pacotes no grafo):

| pacote do plano | no grafo? | frente |
|---|---|---|
| `internal/quality` | **SIM** | P4 (limiar 0,82 em `quality.go:84`) |
| `internal/seo` | **SIM** | P1b (datas), P0 |
| `internal/publishedmanifest` | **SIM** | P1b, P6 |
| `internal/content` | **SIM** | P1b |
| `internal/structureddata` | **SIM** | P1b (JSON-LD) |
| `internal/editorial` | **SIM** | P5 |
| `internal/agentsurface` | **SIM** | — |
| `internal/lexml` | **SIM** | P5 |
| `internal/legalsignature` | **SIM** | P4 |
| `internal/cerebro` | não | P5, P9, P12 |
| `internal/ollama` | não | P12 |
| `internal/checks` | não | P3 |
| `internal/codex2policyenforcement` | não | P7 |
| `internal/render` / `htmlcontract` / `htmlpolicy` / `pageinline` | não | P0, P4 |
| `internal/httpserver` / `sitemap` / `crawl` / `publicrelease` | não | P6 |
| `cmd/generate-acordao-pages` | não | P4, P8 |
| `cmd/generate-lei-artigo-pages` | não | P8 |
| `cmd/publish-v2-direct` | não | P1b |

**Consequência operacional de P4:** mudar o limiar em
`cmd/generate-acordao-pages/main.go:102` (`limiarMolde = 0.70`) **não** exige
atestação. Mover a régua para `internal/quality` (onde vive
`nearDuplicateThreshold = 0.82`, `quality.go:84`) **exige**, no mesmo commit:
`./tools/go-modern generate ./internal/v2ingest` +
`git add internal/v2ingest/validator_fingerprint_attestation_generated.go`.
Custo declarado no próprio gate: ~2,2 s de `go list` + ~10 min de compilação de
25+ testes se reprovar.

## 3. `check-contrato-vs-medicao`: o teto exato de P6

Lido em `tools/check-contrato-vs-medicao:190-200`:
`folga = max(200, int(publicadas × 0,05))`.

Medido agora: publicadas 11.106, declarado 11.039, folga = **555**, divergência
atual = 67.

→ **O gate reprova quando `publicadas > 11.039 + 555 = 11.594`.** Sobram
**488 páginas** de margem. P6 tem 2.488 montáveis no poço.

**Pior desfecho realista:** P6 publica ~2.488 páginas, o manifesto da worktree
vai a ~13.594, e **todo `git commit` de toda sessão neste repositório passa a
reprovar**, porque o gate é incondicional e lê a worktree — inclusive commits
que não têm nada a ver com publicação. O bloqueio aparece como
"CLAUDE.md afirma um volume publicado que o published_manifest desmente".

**Rollback:** não existe rollback "para trás" (o contrato proíbe reverter). O
desbloqueio é **para frente, uma linha**: atualizar
`CLAUDE.md` §3 "Estado atual (medido em AAAA-MM-DD): N páginas públicas no ar"
e commitar. Custo: um commit leve.

**O que isso obriga:** **P0 atualiza a linha de volume ANTES de P6 publicar**, ou
P6 atualiza a linha no MESMO commit em que grava o manifesto. Não é opcional.

**Armadilha de P0 no mesmo gate:** as 14 regras novas de P0 não podem conter, em
linha que não se declare histórica, `publicação zero`, `nenhuma página jurídica
pública`, `published_manifest=0`, `deficit_to_10000=10000` ou
`publication_allowed=0`. As marcas que isentam estão em `_e_registro_historico`:
`afirmou`, `trazia até`, `até 2026-`, `foi superada`, `regra antiga`, linha
iniciada por `>`, ou `vencido`. O gate varre também `GOAL.md` e `AGENTS.md`.

## 4. P1b — a frente com o dano de SEO mais próximo, e o que já está no ar

### 4.1 O defeito, medido por mim (não herdado do plano)

```
published_manifest.jsonl: 11.106 linhas
  approved_at == 2026-09-15 : 944
  reviewed_at < approved_at : 942   (cronologia impossível)
  por canal: /jurisprudencia/ 875 · /leis/ 38 · /sumulas/ 29
```

**E está SERVIDO.** `curl` com UA de sonda interna contra produção:

```
https://wikijuridica.com.br/jurisprudencia/stf-adi-4376/
  HTTP/2 200 · cf-cache-status: HIT · age: 27822
  last-modified: Sat, 05 Sep 2026 00:00:00 GMT
  "datePublished":"2026-09-15"   "dateModified":"2026-09-05"
```

### 4.2 O que NÃO tem rollback

A data de estreia já foi **reescrita quatro vezes** para a mesma URL, e cada
passada anunciou a anterior como falsa:

| commit | data | `approved_at` de `jur-stf-adi-4376` |
|---|---|---|
| `49100f75` | 2026-08-27 | AUSENTE |
| `dbce0520` | 2026-08-30 | AUSENTE |
| `3f7d6d63` | 2026-09-05 | **2026-09-05** |
| `a286f5e6` | 2026-09-08 | **2026-09-08** |
| `315ac61b` | 2026-09-10 | **2026-09-10** |
| worktree | 2026-09-15 | **2026-09-15** |

O que já foi entregue ao Google não se desfaz. **O rollback é só para frente.**

### 4.3 O relógio de decaimento — e por que P1b tem de commitar o manifesto PRIMEIRO

`data/editorial/first_published_at.json`: 10.107 chaves, `mtime 2026-08-28
17:26`, fonte declarada `"histórico git do published_manifest (data do commit,
não approved_at)"`.

Medido: **0 de 944** rotas corrompidas têm estreia registrada nesse arquivo.

Medido contra o último commit (`315ac61b`, 2026-09-10, 11.039 registros):
**900 das 944** já existiam lá — e lá já valiam `2026-09-10`. **44 nunca
apareceram em commit nenhum.**

→ Para as 900, `generate-first-published-at` recupera a estreia na granularidade
do commit (para a `adi-4376`, 2026-09-05). Para as **44**, a estreia verdadeira
**não existe em lugar nenhum** e o melhor disponível passa a ser a data do
primeiro commit que as incluir.

→ **Cada dia que `published_manifest.jsonl` fica não-commitado joga mais rotas
no balde irrecuperável.** O primeiro comando de P1b não é gerar estreia: é
**commitar `data/editorial/published_manifest.jsonl`**, para congelar a
evidência antes de qualquer outra coisa.

### 4.4 A armadilha que o plano NÃO nomeia: a purga não acontece sozinha

`tools/generate-page-content-revision` (docstring, linhas 30-36):

> "O hash cobre só o que um autor escreve (título, meta, H1, abertura, seções,
> FAQ) e **ignora deliberadamente as datas**."

Ele lê `content/pages.json`, não o HTML servido. Logo, corrigir `datePublished`:

- **não** move `content_revised_at` → **não** move `lastmod` → **não** dispara
  re-anúncio ao Googlebot. `--ressemear` é desnecessário aqui (e a linha
  "JSON-LD = --ressemear" da memória **não se aplica a mudança só de data**);
- e, pelo mesmo motivo, **`--purge-targets` devolve ZERO rotas**, o deploy
  imprime "nada a purgar", e a borda continua servindo o JSON-LD errado por
  `s-maxage=604800` = **7 dias** (medido: `cf-cache-status: HIT`, `age 27822`).

**É a mesma classe da linha "script inline" da matriz do §6 do contrato.**

**O que P1b obriga, então:** purga **dirigida por URL** das 944 rotas após o
deploy, e reaquecimento:

```
./tools/purge-edge-cache --url <…>      # --teto-por-url default 3000 > 944: cabe em seletiva
./tools/warm-edge-cache --rps 12 --concorrencia 4
```

Verificação imediata, sem esperar janela: repetir o `curl` da §4.1 e exigir
`cf-cache-status: MISS` seguido de `datePublished` == estreia e
`datePublished ≤ dateModified`.

### 4.5 Pior desfecho realista de P1b, e o rollback

**Pior desfecho: o Go não sobe.** `internal/httpserver/httpserver.go:967` chama
`publishedmanifest.Validate` no boot.
`internal/publishedmanifest/publishedmanifest.go:1456-1470`:

```go
staticArtifactOnlyIssueCodes = { public_html_missing, html_sha256_mismatch,
  sitemap_sha256_mismatch, public_html_parse_failed,
  public_html_robots_not_indexable, public_html_lang_not_ptbr }
bootSameCodeAbortThreshold = 10
bootTotalAbortThreshold    = 25
```

Se as 944 páginas tiverem o HTML reescrito sem o `HTMLSHA256` do manifesto ser
recalculado na mesma passada, saem **944 × `published_manifest_html_sha256_mismatch`**
— muito acima de 10 — e `BootBlockingIssues()` devolve TUDO. O handler não
constrói e `cmd/server` morre.

Consequência exata: o **acervo estático continua no ar** (nginx serve
`root public/`), mas **morre o canal de máquina inteiro** — gêmea Markdown,
`/api/v1/*`, MCP, A2A, descritores, `openapi.json` — que é o produto do §12.
O `proxy_cache wj_dyn` com `use_stale` segura a última resposta boa enquanto
durar, e `check-portal-health` (que sonda só `127.0.0.1`) **não** distingue.

**Como não cair nisso:** `cmd/publish-v2-direct/main.go:3837-3846` grava
`HTMLSHA256` e `SitemapSHA256` no mesmo registro em que grava `ApprovedAt`.
P1b tem de passar pelo publicador, nunca por patch fora dele.

**Rollback:** não há "voltar". O caminho é: corrigir
`first_published_at.json` → republicar pelo publicador (que reescreve HTML +
sitemap + manifesto coerentes) → `sudo -n systemctl restart wikijuridica-server`.
Enquanto isso, o servidor está em `Restart=always` com `RestartUSec=5s` e
**`StartLimitIntervalUSec=0`** (medido) → laço infinito de 5 s, e
**`OnFailure=` vazio** (medido): **ninguém é avisado**.

## 5. Quem pode DERRUBAR o portal (não apenas falhar)

Ordem por probabilidade × alcance.

### 5.1 `cmd/social` em laço de boot — P11 e qualquer toque em `content/social_policy.json`
`wikijuridica-social.service`: `Type=notify`, `Restart=always`,
`RestartUSec=5s`, **`StartLimitIntervalUSec=0`**, `OnFailure=wikijuridica-alerta@%N`.
A própria unit documenta o mecanismo em `ops/systemd/wikijuridica-social.service:57-59`:
"Restart=always + StartLimitIntervalSec=0 com ExecStart falhando em laço … e
OnFailure **NÃO** dispara. A unit nunca entra em failed."
Campo novo no `social_policy.json` sem o binário novo ⇒ `log.Fatalf` ⇒ laço
eterno, **sem alerta**. Precedente datado no contrato: 2026-09-09,
`habitualidade_modo` e `destrava_abrir_thread: 0`.
**Rollback:** editar o JSON de volta (edição pontual, não rewrite) e
`sudo -n systemctl restart wikijuridica-social`. É rápido — mas só se alguém
olhar, porque o alerta não vem.

### 5.2 O binário Go novo — P6, P9, P12
`wikijuridica-server.service` = `Type=notify` + `Requires=wikijuridica-server.socket`.
Precedente no cabeçalho de `tools/check-units-instaladas:12-24`: em 2026-09-01
o `Requires=` entrou apontando para socket não instalada, `Restart=always` ficou
inerte (NRestarts=0) e **o serviço passou 17 h em `failed`; toda rota dinâmica
devolveu 503 a todo bot, e o watchdog tentou 448 restarts fúteis.**
Regras vivas do gate que fecham isso: `notify_binario` (ExecStart sem a string
`NOTIFY_SOCKET` ⇒ nunca manda READY=1) e `socket_binario` (binário sem
`LISTEN_FDS` ⇒ EADDRINUSE em laço com a porta em LISTEN).
**Rollback:** `bin/wikijuridica-server` é um arquivo; `deploy-binario-go` faz
binário → socket → serviço. O caminho de volta é recompilar do commit anterior
e repetir o deploy — **nunca** `git checkout`.

### 5.3 A folha de CSS única com CSP por URL exata — P0 e P4 só se tocarem `internal/render`
Medido em produção agora, byte a byte alinhado:

```
style-src https://wikijuridica.com.br/assets/wj-5b082578c84d2407.css
<link rel="stylesheet" href="/assets/wj-5b082578c84d2407.css">
public/assets/wj-5b082578c84d2407.css  (12.117 bytes)
```

Mecanismo: o nome carrega o hash do conteúdo
(`internal/render/stylesheet.go:76`, `^/assets/wj-[0-9a-f]{16}\.css$`). **Um
byte de CSS muda a URL de todas as 11.106 páginas**, e a CSP fica em
`ops/nginx/security-headers.conf:52`, que é emitida pelo **nginx**, não pelo Go.
Divergiu ⇒ o navegador recusa a folha ⇒ **nenhuma página tem estilo**, com 200 em
tudo e todos os gates de conteúdo verdes.

Três guardas medidas, e os limites de cada uma:
- `tools/check-csp-style-hashes` / `cmd/check csp-style-hashes` confere o
  arquivo byte a byte e o `<link>` em cada HTML — **mas roda na suíte, não no
  caminho do deploy** (o próprio contrato diz isso).
- `deploy-publico:532` calcula `CAMADA_ATUAL = sha256(sha256(binário) +
  sha256(ingress))`. O CSS é compilado **dentro** do binário ⇒ mudança de CSS
  move a camada ⇒ purga ampla automática. **Essa é a guarda que de fato
  funciona.**
- `deploy-publico:~805` roda `/usr/sbin/nginx -t` **sem sudo** antes do reload e
  prova o reload pela ausência de `[emerg]/[alert]` no error log do ingresso.

Detalhe medido que **reduz** o risco: nem `internal/build/build.go:234` nem
`cmd/publish-v2-direct/main.go:903` apagam a folha antiga (nenhum `Remove` em
`cmd/build`), então HTML velho cacheado na borda continua resolvendo a URL
antiga. E `check-csp-style-hashes` só percorre `*.html`, então folha órfã em
`public/assets/` não o deixa vermelho.

### 5.4 O script inline único e a CSP por hash — P0 e P4
`internal/pageinline.Script` = `webmcp.Script + webanalytics.Loader`, isento
byte a byte em `htmlcontract.go:189`. **Segundo script reprova em oito gates.**
O pre-commit dispara `check-analytics-loader` + `check-analytics-contract`
automaticamente para `internal/(webanalytics|pageinline|webmcp|seo|render|htmlpolicy|httpserver)/`
e `ops/nginx/security-headers.conf` (`.githooks/pre-commit:237`) — essa é a
guarda mais forte do conjunto, e ela **está no caminho do commit**.

### 5.5 `check-units-instaladas` bloqueando TODO deploy — P9, P10, P12
As units principais são **symlink** para o repositório (verificado:
`/etc/systemd/system/wikijuridica-{server.service,server.socket,social.service,cerebro.service}`
→ `/opt/wiki/ops/systemd/…`). Logo **editar `ops/systemd/*.service` já muda o
que o systemd lê**, e marca `NeedDaemonReload=yes`.
`tools/check-units-instaladas` reprova nessa condição (regra `daemon_reload`), e
`deploy-publico:282` faz `fail` no passo **0a/7** quando ele reprova.

→ **P9/P10/P12 editando units bloqueiam o deploy de TODAS as outras frentes até
alguém rodar `sudo systemctl daemon-reload`.** Hoje está verde (126 units, 3
avisos de cópia: `wikijuridica-backup-restore.timer`,
`wikijuridica-disk-headroom.timer`, `wikijuridica-efeito-deploy.timer`).
**Rollback:** `sudo systemctl daemon-reload` (ou desfazer a edição para frente).

### 5.6 P9 e a ordem obrigatória do `BindReadOnlyPaths`
`internal/cerebro/carga_linux.go:17-18` abre o lock com `os.O_CREATE|os.O_RDWR`;
`ops/systemd/wikijuridica-cerebro.service:72` tem `PrivateTmp=true`. Medido:
lock do host = inode **39454263**. A unit é symlink para o repo, então uma
edição que ponha `BindReadOnlyPaths=/tmp/opt-wiki-agent-heavy.lock` **antes** do
`tmpfiles.d` criar o arquivo derruba o cérebro em laço com **226/NAMESPACE** —
e `RestartUSec=15s` contra `StartLimitIntervalUSec=10s` torna o burst
inalcançável, então o laço é eterno e `OnFailure` **nunca** dispara.
Medido também: **não existe `ops/tmpfiles.d` para esse lock** (só
`cpu-energia.conf` e `thp.conf`), e `/usr/lib/tmpfiles.d/tmp.conf:11` tem
`D /tmp 1777 root root -`, que esvazia `/tmp` no boot.
**Rollback:** uma linha removida do arquivo da unit + `daemon-reload` + restart.
Rápido, porque a unit é symlink — mas **ninguém avisa que caiu**.

## 6. Risco de SEO irreversível — o que guarda o quê

| eixo | guarda | estado medido | vale para |
|---|---|---|---|
| re-datação em massa | `--ressemear` + `generate-page-content-revision` (hash sobre `content/pages.json`, **ignora datas**) | — | P4, P0 (markup) |
| causalidade `lastmod` | `tools/check-lastmod-causalidade` | **VERDE**: 11.116 rotas, 2.215 revisões, **0 fabricadas**, 0 sitemap divergente | — |
| coerência de artefato | `publishedmanifest.Validate` no boot, tetos 10/25 | boot OK | P1b, P6 |
| volume declarado | `check-contrato-vs-medicao` (pre-commit, incondicional) | folga 555, restam **488** páginas | P6 |
| sitemap × ledger | dentro do `check-lastmod-causalidade` | 11.113 URLs conferidas, 0 divergentes | P6 |
| purga por camada | `deploy-publico:532` fingerprint por componente | — | P4, P0 |

**A conclusão que importa:** o `check-lastmod-causalidade` está **VERDE hoje**,
com produção servindo `datePublished: 2026-09-15` e `dateModified: 2026-09-05`
na mesma página. Ele mede `lastmod`/`content_revised_at`; a corrupção vive em
`approved_at`/`datePublished`, que o hash de revisão ignora por construção.
**Nenhum gate deste repositório detecta a cronologia impossível.**
Prova positiva adicional: o sitemap de `stf-adi-4376`
(`public/sitemaps/pages-0093.xml`) diz `<lastmod>2026-09-05</lastmod>` — ou
seja, a corrupção **não** re-anunciou o acervo; o dano é de credibilidade do
campo de data, não de re-crawl em massa. Isso torna P1b **menos urgente que o
plano sugere e mais barato de corrigir**, desde que a purga dirigida aconteça.

## 7. P2 — verificado no disco, e um efeito a mais que o plano não tem

Confirmado por leitura: `tools/run-daily-content:337,338,345,346,347` com
`[stj - precedentes]` etc.; `:38` liga `SECO=1` e o laço `:99-108` não conhece
`--seco`, caindo no `*)` com `exit 2` em `:105`.
Teste em `bash -c` isolado: a chave literal vira `"stj - precedentes"` (com
espaços) e o **valor permanece intacto** — logo os coletores ainda rodam; o que
quebra é quem casa pelo NOME.

Prova direta no ledger (`data/ops/daily_content_collect.jsonl`, últimas 40
linhas): **as duas grafias coexistem** — 15 linhas com os nomes antigos e 25 com
os corrompidos. A série está partida exatamente como o plano diz.

`check-frescor-canal-diario` (`CANAIS`, linhas 65-88) tem os nomes antigos
`stj-precedentes`, `stf-informativo`, `noticias-oficiais`,
`diarios-municipais`. Saída de hoje:
`jurisprudencia … stj-precedentes (2026-09-10)` e `sumulas … (2026-09-10)`
marcados **[OK]** sobre registro de 5 dias atrás — **falso verde por canal
dentro de um vermelho global** (exit real 1, medido com redirecionamento, não
com pipe).

**Achado novo (não está no plano):** o gate compara com **hoje em UTC**
(`hoje 2026-09-16` na saída, contra `2026-09-15 21:14 -03` local). Com
`TOLERANCIA_DIAS_CADENCIA = 1`, **a partir das 21:00 local o canal `noticias`
queima a tolerância inteira só pelo fuso** — hoje ele passou com
`gap 1d ≤ tolerância 1d`, exatamente na borda. É alarme falso latente.

**Pior desfecho de P2:** corrigir as chaves parte a série de novo (terceira
grafia) e o gate volta a mentir. **Rollback:** nenhum, e não é preciso — o
ledger é append-only; a correção é para frente e tem de tratar as duas grafias
como sinônimos na leitura, não renomear o passado.

## 8. P10 — o gate está VERDE e é isso que o torna perigoso

Medido ao vivo: `wikijuridica-daily-content.service` com
`SuccessExitStatus=0 1`, **`ExecMainStatus=1` E `Result=success`**, última saída
2026-09-15 04:42:10 −03, e
`wikijuridica-alerta@wikijuridica-daily-content.service` com
`InactiveEnterTimestamp=` vazio — **nunca disparou.** A prova viva que o plano
alega está confirmada.

`./tools/check-units-alarme` sai **0**: "64 .service · exigem OnFailure 55 · com
OnFailure real 55 · SuccessExitStatus: **22** unit(s) mascaram exit · 22 com
razão registrada ao lado". **O plano diz 20; o número medido é 22.**

O critério do gate é "a máscara tem razão registrada ao lado", não "a máscara se
justifica". **Pior desfecho de P10:** endurecer o critério vira **22 unidades
vermelhas de uma vez**, e como o gate roda em `run-qualidade-diaria:1050` a
bancada inteira fica vermelha — o padrão "gate vermelho por estoque que nada
drena". **Rollback:** para frente — reprovar por **fluxo** (máscara nova) e não
por nível, e datar o estoque existente.

## 9. P3 / P6 — duas lacunas de fato

- **`tools/publicar-estoque` NÃO EXISTE.** `ls tools/ | grep -iE "publicar|estoque"`
  devolve `publicar`, `publicar-mcp-registry`, `publicar-perfis-sociais`,
  `check-censo-acompanha-estoque`, `generate-censo-acompanha-estoque`,
  `generate-first-published-at`. As etapas que P6 quer recortar são as de
  `tools/run-daily-content`: `2.5/9` baseline · `3/9` preservação · `4/9`
  integridade · `5/9` commit da INTENÇÃO · `6/9` pareamento intenção × página ·
  `7/9` censo · `7.9/9` data de revisão · `8/9` publicação transacional ·
  `8.5/9` brotli · `8.6/9` a onda avançou · `8.7/9` gates da onda · `9/9` prova
  em HTTP. **Recortar as 2.5–9 significa reescrever 480 linhas de shell com
  ordem obrigatória, não "chamar uma ferramenta".**
- **A ordem 5/9 → 6/9 é contratual**: o gate de pareamento recusa página cujo
  `intent_id` não esteja no portfólio do commit **pai**. Um publicador autônomo
  que inverta isso reprova sempre.
- **`deploy-publico:307` (passo 0a-bis)** barra deploy com
  `data/editorial/v2_pages` ou `portfolio_v2` sujos. Um publicador autônomo
  rodando em paralelo com uma sessão de edição **vai** encontrar isso. A válvula
  é `WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1` — e usá-la por padrão num oneshot
  automático publicaria trabalho não-commitado de outra sessão, que é
  exatamente o acidente de 2026-08-29 (158 shards).
- **P3 (gate `produtor-orfao`)**: `internal/checks/checks.go` tem a lista de
  nomes (~:801) e o `switch` (~:1679); `internal/checks/dispatcher_orfao_test.go`
  cobra a coerência entre os dois. `internal/checks` **não** está no grafo do
  validador → sem atestação. Mas o pre-commit rodará a suíte inteira de
  `./internal/checks/` (timeout 780 s × fator).

## 10. P7 — risco menor do que parece

`internal/codex2policyenforcement` **não** está no caminho de boot: os chamadores
são `cmd/generate-codex2-policy-enforcement`, `cmd/check-codex2-policy-enforcement`,
`cmd/generate/*` e `internal/checks/checks.go:3499,7537,9312`. Nenhum deles é
`httpserver` nem `cmd/server`. **P7 não pode derrubar o portal.**
A lista viva em `policy.go:4507-4515` já autoriza `internal/datajud*`,
`internal/codex2datajud*`, `cmd/social/`, `internal/consultapublica/` e
`cmd/*datajud*`. O gate usa `ValidateWithBaseline` — mexer na lista sem
regenerar o baseline deixa o gate vermelho na bancada. **Rollback:** regenerar o
baseline; nada some.

## 11. P12 — premissas conferidas ao vivo

`systemctl show ollama.service`: `MemoryMax=12884901888` (= 12 GiB exatos),
`CPUWeight=60`, `Nice=5`, `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_PARALLEL=1`,
`OLLAMA_KEEP_ALIVE=15m`, `OLLAMA_CONTEXT_LENGTH=8192`,
`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`,
`OLLAMA_LLM_LIBRARY=cpu`. Drop-in em
`/etc/systemd/system/ollama.service.d/wikijuridica-tuning.conf` → **symlink**
para `/opt/wiki/ops/ollama/ollama.service.d/wikijuridica-tuning.conf`, idêntico.
`NeedDaemonReload=no`. Todas as premissas de P12 batem com o disco.

`internal/cerebro/saude.go:88-92`: `LockPesadoPadrao =
"/tmp/opt-wiki-agent-heavy.lock"`, `CargaMaxPadrao = 12.0`,
`TetoBytesResidentesPadrao = 9 << 30`.

**Lacuna medida:** `tools/check-units-instaladas:72` tem
`DIR_UNITS = RAIZ + "ops/systemd"`, e **nenhum arquivo em `tools/` ou
`internal/checks/` menciona `ops/ollama`** (`grep -rln "ops/ollama"` = vazio).
→ **A custódia do drop-in do Ollama não tem gate nenhum.** Se o symlink virar
cópia, ou se uma edição deixar `NeedDaemonReload=yes` em `ollama.service`, nada
acusa — e P12 é exatamente a frente que vai reescrever esse arquivo.

## 12. Lacunas a nomear (falta gate ou sonda)

1. **Cronologia `datePublished ≤ dateModified` não tem gate.** Provado:
   `check-lastmod-causalidade` VERDE com 942 páginas impossíveis servidas.
   Falta um gate que leia `approved_at`/`reviewed_at` do manifesto **e** o
   JSON-LD servido, e reprove `reviewed_at < approved_at`. Custo: uma passada
   sobre 11.106 linhas (medi em <5 s em Python).
2. **Não há gate de purga para mudança que o hash de revisão não vê.**
   `--purge-targets` devolve 0 por construção nesses casos; a decisão fica com
   quem opera. Falta um gate que compare o `datePublished` **servido pela
   borda** com o do disco, por amostra determinística.
3. **`ops/ollama` fora de toda custódia** (§11).
4. **`wikijuridica-server.service` sem `OnFailure` e com
   `StartLimitIntervalUSec=0`**: o serviço que serve o canal de máquina é o
   único daemon sem alerta. `check-units-alarme` o isenta ("daemon com
   Restart="). Falta sonda de vivacidade que não dependa de `failed`:
   `NRestarts` crescente, ou `/healthz` pelo **nginx**, não por `127.0.0.1:8089`.
5. **Fuso do `check-frescor-canal-diario`**: UTC contra tolerância de 1 dia
   queima a folga após as 21:00 local (§7).
6. **`check-contrato-vs-medicao` não avisa quando a folga está acabando.** Ele é
   binário: verde até 11.594, vermelho depois, e o vermelho cai em TODA sessão.
   Falta aviso a, digamos, 80% da folga.
7. **`published_manifest.jsonl` não-commitado não tem gate.** `deploy-publico`
   barra `v2_pages`/`portfolio_v2` sujos (passo 0a-bis) mas **não** o manifesto,
   que é justamente de onde a estreia se deriva (§4.3).

## 13. CORREÇÕES APÓS O ADVISOR (medidas, não aceitas de palavra)

### 13.1 §4.4 confirmada no CÓDIGO, não na docstring (R1)

Lido `tools/generate-page-content-revision:185-186`:

```python
CAMPOS_DE_CONTEUDO = ("title", "meta_description", "heading", "summary",
                      "body_sections", "faq")
```

**Nenhum campo de data.** E o segundo hash, `conteudo_servido()` (:363), aplica
`neutraliza_datas(bruto)` — "com toda data ISO neutralizada". Os DOIS hashes
cegam data por construção.
→ §4.4 fica **mais forte**: mudança só-de-data é invisível a
`content_sha256` E a `served_sha256`; `--purge-targets` devolve 0;
`--ressemear` é desnecessário; **a purga dirigida das 944 URLs é obrigatória**.

### 13.2 ACHADO NOVO — o remédio de P1b, como está escrito, NÃO fecha o defeito

Percorri os **50 commits** de `data/editorial/published_manifest.jsonl`
(2026-06-09 → 2026-09-10) e reconstruí a primeira aparição de cada
`unique_intent_id` — o mesmo algoritmo de `tools/generate-first-published-at`
(`commits_do_manifesto` :51, `intents_no_commit` :66, data do **commit**, não
`approved_at`).

```
ids com primeira aparição em commit          : 11.039
das 944 corrompidas: com histórico            : 900
                     sem histórico nenhum     :  44
AINDA IMPOSSÍVEL após a recuperação           : 900 de 900
  estreia recuperada: 2026-09-10 (894) · 2026-09-05 (6)
  reviewed_at real  : 2026-09-09 (894) · 2026-09-01 (6) · 2026-09-11 (42) · 2026-09-15 (2)
```

**Rodar `generate-first-published-at` não corrige uma única das 900.** A estreia
recuperada (2026-09-10) continua POSTERIOR ao `reviewed_at` (2026-09-09), e a
cronologia impossível permanece — só muda de data.

**Causa raiz:** o gerador deriva a estreia do commit do **manifesto**, e o
manifesto é commitado DEPOIS da passada (hoje, 5 dias depois). O commit é sempre
≥ a publicação real.

**A correção de engenharia, com a fonte medida ao lado:**
`data/editorial/v2_pages` **é** commitado diariamente (`62d71de0` e `06caad54`
em 2026-09-15; `a523b322` em 2026-09-14). O commit do **shard** é um limite
superior muito mais apertado e anterior ao do manifesto. Então P1b precisa de
uma das duas, e as duas são verificáveis agora:
1. derivar a estreia do primeiro commit do **shard de `v2_pages`** que contém o
   `unique_intent_id`; ou
2. manter a fonte atual e aplicar **piso**:
   `datePublished = min(estreia_recuperada, reviewed_at)`.

Sem isso, a lacuna #1 (gate de cronologia) **reprovaria a própria correção**.

**E os 44 são um vazamento permanente.** `generate-first-published-at` só grava
id que apareceu em algum commit (:132-136) e **mescla** com o arquivo existente
(`carrega_existente` :92) — nunca reescreve. Id ausente ⇒ `publish-v2-direct`
:3837 cai em `primeiroNaoVazio(page.PublicationDate, opts.publishedAt)` ⇒
**data de hoje, de novo, em toda passada**. Enquanto o manifesto não for
commitado, o balde dos 44 cresce todo dia.

### 13.3 §8 corrigida: o número e o recorte

`grep SuccessExitStatus= ops/systemd/*.service` (sem comentários), contagem
exata: **22 no total** — `=0 1` ×12, `=1` ×7, `=0` ×2, `=75` ×1.
→ **19 casam o padrão que o plano nomeia (`=0 1` / `=1`)**; os outros 3 são
`wikijuridica-previsao` (`=0`) e `wikijuridica-moderacao-transparencia` (`=75`,
que é código de lock, não máscara de falha). O "20" do plano está perto; o
recorte correto é 19 de 22.

### 13.4 P0 — o segundo laço do mesmo gate

`tools/check-contrato-vs-medicao:57`:
```python
DECLARACAO = re.compile(r"Estado atual[^:]*:\s*\*{0,2}([\d.  ]+)\s*páginas? públicas?", re.IGNORECASE)
```
Se as 14 regras de P0 **reformatarem essa linha** (mudar "páginas públicas",
tirar os dois-pontos, quebrar a linha), o gate cai no ramo `elif publicadas > 0`
e reprova com "não declara volume publicado em forma verificável" — e reprova
em **todo commit de toda sessão**. A linha é frágil por regex, não por número.

E o §10 do contrato é cobrado por
`internal/contract/misc/peer_governance_test.go` em quatro documentos: P0
editando aquela seção tem de rodar esse teste no mesmo passo (o próprio contrato
manda, BUG-171).

### 13.5 Frentes que faltavam (P-1, P5, P8)

- **P-1** (gravar o plano em `docs/goal/` e commitar): risco quase nulo. Nenhum
  gate do pre-commit varre `docs/goal/*.md`, exceto
  `check-buglog-status-coerente`, disparado só por `docs/goal/BUGLOG.md` ou
  `p0_frontboard.jsonl` (`.githooks/pre-commit:263`). **Rollback:** nenhum
  necessário; é o commit mais barato do plano e por isso deve ser o primeiro.
  Único cuidado: não escrever no documento nenhuma das frases-zero do §3.

- **P5** (fechar a atribuição; rebaixar para refino): **o pior desfecho é
  despublicar**. O rebaixamento tem de mudar severidade para MÉDIO
  (`tools/generate-v2-publication-severity`), nunca para crítico — crítico não
  publica (§5 do contrato) e 3.101 das 3.201 entradas da fila são **páginas
  VIVAS**. Rebaixar para crítico tiraria do ar até 3.101 URLs indexadas, e
  `publishedmanifest.Validate` passaria a acusar
  `sitemap_loc_without_manifest`, que **não** está na allowlist tolerada → **o
  Go não sobe**. Atestação: `internal/editorial` e `internal/lexml` **estão no
  grafo** → reatestar no mesmo commit. `internal/cerebro` (triagem.go:195-230)
  está fora. **Rollback:** para frente — republicar com a severidade correta.

- **P8** (aproveitar os 49.807 agravos como contador agregado): **esta é a
  frente com o maior risco de SEO de todo o plano, maior que P1b.**
  `cmd/generate-lei-artigo-pages/main.go:1481` injeta a frase "A classe
  processual mais frequente é …" no **corpo** da página. Corpo é
  `body_sections`, que **está** em `CAMPOS_DE_CONTEUDO` → `content_sha256` muda
  → a re-datação é **verdadeira** → `lastmod` avança → o sitemap re-anuncia.
  Em 3.481 páginas isso é uma re-datação em massa **legítima**, e por isso
  `--ressemear` é **proibido** nessa passada (suprimi-la esconderia do buscador
  conteúdo que mudou de fato).
  O preço medido já catalogado no contrato: a publicação seguinte zera mtime e
  ETag, e os bots que revalidam rebaixam o acervo junto (medido duas vezes com
  `meta-externalagent`). **Mitigação obrigatória:** agrupar numa publicação só e
  medir a taxa de 304 depois com `tools/check-efeito-nos-bots`.
  Agravante: `cmd/generate-lei-artigo-pages` é **órfão** (P3) — nenhum runner o
  chama e nenhum gate roda depois dele. **Rollback:** nenhum para o `lastmod` já
  anunciado; é para frente.

### 13.6 Ajuste de §6

Retiro o juízo "menos urgente que o plano sugere". O fato do sitemap
(`<lastmod>2026-09-05</lastmod>`, sem re-anúncio) continua válido; a urgência é
o **relógio de decaimento** de §4.3 e §13.2 — 44 rotas hoje, mais a cada dia em
que o manifesto não for commitado.

## 14. O que o advisor mudou

1. **Exigiu prova de código para §4.4.** Eu tinha concluído por docstring.
   Li `CAMPOS_DE_CONTEUDO` e `conteudo_servido()`: a conclusão **se manteve** e
   ficou mais forte (dois hashes cegam data, não um).
2. **Apontou que a recuperação podia não fechar a cronologia.** Medi: é pior do
   que ele supôs — **900 de 900** continuam impossíveis. Isso **derruba o
   remédio de P1b como escrito** e é o achado mais importante desta varredura.
3. **Cobrou P-1, P5 e P8**, que eu não tinha coberto. P8 revelou-se a frente de
   maior risco de SEO do plano.
4. **Cobrou o laço do regex de `check-contrato-vs-medicao` e o
   `peer_governance_test.go`** em P0.
5. **Recusou meu "plano diz 20, medido 22" sem recorte.** Contei por padrão:
   22 no total, **19** casam `=0 1`/`=1`.
6. **Mandou cortar o juízo de §6.** Cortado.
Nenhum fato que eu havia medido foi contrariado.
