# CRÍTICO DE COMPLETUDE OPERACIONAL — o que falta para OPERAR

Medido por mim em 2026-09-15 22:33–22:50 -03 / 2026-09-16 01:33–01:50Z, PLAN MODE
(nada mutado). HEAD `62d71de0`, índice VAZIO, loadavg1 8,27.
`MEDIDO` = executei o comando nesta sessão. `DERIVADO` = aritmética sobre MEDIDO.

---

## RESUMO EXECUTIVO — os 6 achados que viram trabalho

| # | achado | classe | medido |
|---|---|---|---|
| **A1** | `wikijuridica-server-reload.path` reinicia o Go **sem guarda** quando o cérebro escreve 3 arquivos; disparou **3×/24 h**, e a de 12:29:55 caiu **58 s depois** do fim do publish da onda | **QUEBRA PRODUÇÃO** | sim |
| **A2** | `check-social-temas-espelhados` **VERMELHO AGORA**: 67 páginas anunciam tema 404; Amazonbot 7 e GPTBot 2 já bateram nesses 404 no log vivo | defeito vivo, nenhum runbook mede | sim |
| **A3** | O descritor `/api/v1/citar` declara `markdown_sha256` que **NÃO bate** com a gêmea servida na borda: **13 de 13** rotas por stride | defeito vivo no canal de máquina | sim |
| **A4** | Nenhum runbook roda `generate-brotli-static` depois de publicar (só P6); o `.br` é o que o nginx serve a `Accept-Encoding: br` | falso-verde de até ~65 min | sim |
| **A5** | **TRÊS** units tomam o flock pesado, não uma — e a próxima é `qualidade-longa` às **02:11 -03 de hoje** | serialização não declarada | sim |
| **A6** | O teto do `check-contrato-vs-medicao` é **11.621** (declarando 11.039) / **11.691** (declarando 11.106) — ganho de **70** páginas, não 555/488; e P6 publica **2.488**, que estoura os dois | número errado em 2 runbooks | sim |

---

## 1. PASSO OBRIGATÓRIO DO REPOSITÓRIO QUE NENHUM RUNBOOK EXECUTA

### 1.1 Reatestação do grafo de `internal/v2ingest` — **COBERTA, e a pergunta se fecha**

`MEDIDO`: `./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` = **98**
pacotes `portaljuridico/*`. Conferi pacote a pacote o que os cinco blocos tocam:

FORA do grafo (sem reatestação): `internal/sdactivation`, `internal/cerebro`,
`internal/ollama`, `internal/checks`, `internal/shellscriptquality`,
`internal/sourceresolve`, `internal/sourcecollect`, `internal/stjacordaos`,
`internal/codex2policyenforcement`, `internal/datajudfila`, `internal/v2bodyneardup`,
`internal/tetodelote`.
DENTRO: `internal/quality`, `internal/legalsignature`, `internal/ptbrtext`,
`internal/seo`, **`internal/publishedmanifest`**.

E o passo não falta porque **o pre-commit já o cobra incondicionalmente**:
`.githooks/pre-commit:366-368` → `tools/check-atestacao-grafo-no-commit`, que lê
o ÍNDICE do commit (`:52` `git diff --cached --name-only --diff-filter=ACMR`),
resolve o grafo com `go list -deps` (`:83`) e trata **`go.mod`/`go.sum` como
sempre-no-grafo** (`:93-95`).

**O que sobra, e é o que vale escrever:** a tabela §1 do `CLAUDE.md` do bloco
GATES proíbe editar `internal/quality` e `internal/legalsignature` e **esquece
`internal/ptbrtext`** — que está no grafo e é chamado em
`cmd/generate-acordao-pages/main.go:859` (`contaPalavras`). O "SE NÃO VIER" do
passo 5 do GATES manda resolver divergência de separador/`TrimSpace`, que é
exatamente onde se estica a mão para `ptbrtext`. Acrescentar `internal/ptbrtext`
e `internal/publishedmanifest` à linha de proibição.

### 1.2 Pareamento de portfólio contra o commit PAI — **COBERTO, por hook que nenhum runbook cita**

`MEDIDO`: `tools/check-v2-finalized-commit` **não** está no `pre-commit` (grep =
0 linhas). Quem o invoca é `.githooks/reference-transaction:240-248`, e ele lê o
checker **do `$BASE`** (`trusted_git show "$BASE:tools/check-v2-finalized-commit"`)
— o trust-root no commit PAI. Orçamento `WIKI_COMMIT_GATE_TIMEOUT_SECONDS:-90`
(`:25`). `core.hooksPath=.githooks` `MEDIDO`.

Consequência operacional que nenhum runbook escreve: **é fail-closed em
`update-ref`, então `--no-verify` não o contorna** — e, ao contrário do que o
"SE NÃO VIER" do passo 5 do PUBLICAR sugere, a recusa não vem do `pre-commit` e
a mensagem não sai no mesmo lugar. Quem for depurar o 5c/5e vai procurar no log
errado.

### 1.3 Ordem topológica da cadeia editorial — **NÃO SE APLICA, e isso tem de ficar escrito**

`docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md:25-80` abre com o aviso: a cadeia
dos 13 elos (§2, passos 1–13) é `authorial_mass_*` e **não** é a cadeia de
`data/editorial/v2_pages/*.jsonl`. Os cinco detectores `older_than` (bloco
`<!-- cadeia:detectores -->`, `MEDIDO`, 5 entradas) não leem `v2_pages`.

Logo: **nenhum dos cinco blocos precisa dos 13 passos.** Escrever isso é trabalho
— porque a tentação de "regenerar a cadeia" ao ver `fingerprint mismatch` é o
erro que custou os 31 dias, e o documento diz que a reconciliação certa para
`v2_pages` é `ops/relaunch-writing.sh` (contrato semântico por `dependency_sha256`),
nunca o §2.

**Mas há um vermelho latente que nenhum runbook viu.** `MEDIDO` por `ls`:
`authorial_mass_drafts.jsonl` mtime **2026-09-10 23:41:47** contra
`authorial_mass_publication_readiness.jsonl` mtime **2026-08-05 19:38:27** — a
saída é **36 dias mais velha** que uma entrada da própria família. Isso é
exatamente a forma `saída older_than entrada` que `readinessCurrentInputFreshnessIssues`
(`internal/authorialmassreadiness/readiness.go:1060`) emite. E
`authorial_mass_drafts.jsonl` está ` M` na worktree. Antes de qualquer bloco
commitar dado editorial, rodar
`./tools/check-authorial-mass-publication-readiness` e **datar o vermelho como
baseline conhecido** — senão o primeiro commit dos blocos herda a culpa
(precedente `vermelho-conhecido-e-atribuicao`).

### 1.4 `content/legal_cocitation_index.jsonl` no passo 2.6 — **FALTA NOS DOIS BLOCOS QUE PUBLICAM**

`tools/deploy-publico:652-684` (comentário) e `:678` (`./tools/go-modern run
./cmd/generate-legal-cocitation`). O comentário é literal: *"o indice deriva de
content/pages.json, que o passo 1 acabou de reescrever, e e lido UMA vez no BOOT
do servidor. Entao ele tem de nascer DEPOIS da republicacao e ANTES de o servico
voltar a atender."*

`MEDIDO` agora:

```
content/legal_cocitation_index.jsonl   mtime 2026-09-11 03:08:12   (M)
content/pages.json                     mtime 2026-09-15 12:28:56   (M)
```

**O índice está 4 dias atrás da fonte de que deriva.** Nem o bloco ESTANCAR
(passo 8 publica + passo 11 reinicia) nem o PUBLICAR (passo 9) rodam o 2.6 — o
refutador do PUBLICAR o achou (A2); **o do ESTANCAR não**, e o ESTANCAR também
reescreve `pages.json` e reinicia.

E a ausência é **invisível ao gate**: `MEDIDO`,
`./tools/check-percursos-fundamento-legal` → **EXIT=0**,
`paginas=5815 links=31102 cross_area=24295 (78.1%)`. Ele mede densidade, não
frescor. As 944 rotas de hoje — e as 2.488 do P6 — ficam sem a seção de maior
densidade do canal de máquina e **nenhum gate diz nada**.

### 1.5 Esvaziar o índice git — **os cinco prescrevem, e o comando é PROIBIDO**

Os cinco runbooks trazem, no "SE NÃO VIER", alguma variante de *"esvazie o
índice"*. Nenhum nomeia o comando, e os dois comandos óbvios estão barrados:

`~/.claude/hooks/git-guard.sh:64-75` bloqueia `git reset --hard`,
`git reset HEAD~`, `git reset HEAD^`, `git restore `, `git restore --staged`,
`git checkout -- `, `git clean`, `git revert `, `git stash` (`:119`).
`~/.claude/CLAUDE.md` proíbe **nominalmente** `git reset` e `git restore` inteiros.

E a condição é alcançável em todos os blocos: COLETA §A-7/§B-12/§C-21/§D-24,
GATES 9, PUBLICAR 2, DAEMON "ordem de commit" fazem
`flock … 'git add internal/… && git commit …'`. **Se o commit reprova, os `.go`
ficam staged**, e `go-index-compile-closure` passa a compilar a closure deles em
TODO commit de TODA sessão (77,6 s contra 14,9 s, número do contrato).

**A saída sancionada, que precisa virar linha de runbook:** não deixar o índice
sujar — `git commit -F <msg> -- <caminhos exatos>` commita da **worktree** sem
passar pelo índice (é o remédio que `~/.claude/CLAUDE.md:102` nomeia). Quando já
sujou, a única rota para frente é **corrigir a causa e commitar o mesmo
pathspec** — nunca desfazer. Escrever isso, com o comando, nos cinco.

### 1.6 `generate-brotli-static` (passo 2.5) — **FALTA NO ESTANCAR**  ⟵ achado novo

`MEDIDO`: `public/` tem **11.358** `.html.br` para **11.357** `index.html`.
`brotli_static on` serve o `.br` de disco a quem manda `Accept-Encoding: br` —
que é Googlebot, GPTBot e todo navegador.

Prova ao vivo, na origem, agora:

```
Accept-Encoding: identity → 25.422 B, datePublished 2026-09-15
Accept-Encoding: br       →  6.731 B, Content-Encoding: br, datePublished 2026-09-15
```

Hoje batem, porque o último `deploy-publico` rodou o 2.5. **O bloco ESTANCAR
reescreve 942 HTML por `publish-v2-direct` e nunca roda o 2.5.** O `.br` fica com
os bytes velhos, e a verificação do passo 13 do ESTANCAR (`grep datePublished` por
`curl` sem `--compressed`) lê o **identity** — passa VERDE enquanto o bot recebe
o corpo antigo.

**Atenuação medida, e ela não apaga o achado:**
`ops/systemd/wikijuridica-brotli-cobertura.timer` é `OnCalendar=hourly`,
`RandomizedDelaySec=5min`, e roda `tools/repair-brotli-cobertura` →
`generate-brotli-static --jobs 4`. Então a janela é de **até ~65 min**, não
eterna. E ela existe **agora**: `MEDIDO`,
`./tools/check-brotli-static-fresco` → **EXIT=1**, *"1 .br MAIS VELHO(S) que o
fonte … public/datasets/radar-ia.json.br (atras por 1.0 h)"*, com a própria
mensagem dizendo *"O nginx serve esse corpo a quem pede Accept-Encoding: br,
inclusive a Cloudflare, que o distribui"*.

Correção: no ESTANCAR, `./tools/generate-brotli-static --jobs 4` entre o passo 8
(publicar) e o 11 (reiniciar), e o DEPOIS do passo 13 passa a mandar
`curl --compressed` (ou `-H 'Accept-Encoding: br'`) — provar por CORPO no
encoding que o bot usa, não só em identity.

### 1.7 Recibos da transação v2ingest no pathspec — **falta nos dois blocos**

`MEDIDO`, `git show --name-only 315ac61b` (o último commit do manifesto): o
commit de deploy leva **10** arquivos, não 3 (ESTANCAR passo 15) nem 3
(PUBLICAR 10b) nem 7 (a emenda do refutador):

```
content/legal_cocitation_index.jsonl · content/pages.json
data/editorial/authorial_mass_drafts.jsonl · data/editorial/published_manifest.jsonl
data/editorial/stock_manifest.json · data/ops/edge_cache_purge.jsonl
data/ops/edge_cache_warm.jsonl · data/ops/page_content_revision.jsonl
data/ops/v2_ingest_terminal_receipts/<id>.terminal.json
data/ops/v2_ingest_transaction_receipt.json
```

`MEDIDO`: `data/ops/v2_ingest_transaction_receipt.json` está ` M`, último commit
**2026-09-10**; e **3 recibos terminais estão UNTRACKED** (`??`) em
`data/ops/v2_ingest_terminal_receipts/` (51 arquivos no diretório). O recibo é
lido por `internal/v2readguard/guard.go:35` (`ReceiptRelPath`) — é artefato
portante, não ruído. `33` arquivos untracked em `data/` no total.

---

## 2. VERIFICAÇÃO AO VIVO NA PRODUÇÃO QUE NENHUM DELES FAZ

### 2.1 A paridade entre os quatro canais — e ela está QUEBRADA agora

Sondei com o UA do projeto + `X-Warming-Request: true`, rota
`/jurisprudencia/stf-adi-4376/`:

| leitura | resultado `MEDIDO` |
|---|---|
| HTML na borda | `cf-cache-status: HIT`, `age 32610`, `datePublished 2026-09-15` / `dateModified 2026-09-05` |
| gêmea `/index.md` na borda | `HIT`, `age 1307`, `date_published "2026-09-11"` |
| `Accept: text/markdown` na MESMA URL | `HIT`, `age 31671`, `vary: Accept-Encoding, Accept`, `date_published "2026-09-11"` |
| gêmea no Go `:8089` | `date_published "2026-09-15"`, sha `b0ccb5c9…` |
| gêmea no nginx `:8088` | `date_published "2026-09-15"`, sha `b0ccb5c9…` (a origem **reconciliou** desde a medição do refutador às 01:1xZ) |
| `/api/v1/citar` (`:8089`) | `markdown_sha256 = b0ccb5c9…`, `html_sha256 = ed329c6e…` |
| sha do HTML em disco | `ed329c6e…` — **bate** |
| sha da gêmea **na borda** | `f4fe9c65…` — **NÃO bate com o declarado** |

**Amostra por stride determinístico sobre as 944 rotas de hoje, 13 rotas:
13 de 13 divergem** entre o `markdown_sha256` que o descritor declara e o sha da
gêmea que a borda serve. `MEDIDO`, saída integral na sessão.

Isto é o §12 do contrato ("o produto é o contexto para IA"): **um agente que
verifique o hash que nós mesmos publicamos recebe mismatch, hoje, em 13 de 13.**
E a cronologia impossível vive nos DOIS canais com datas DIFERENTES: HTML
`09-15 > 09-05`, Markdown `09-11 > 09-05`.

Nenhum runbook mede isso hoje: o I-1 do ESTANCAR lê só `public/**/index.html`; o
passo 10 do GATES compara só `html_sha256`; o I-3 do PUBLICAR **propõe** as cinco
leituras mas é instrumento a construir.

**O mecanismo, medido, e ele não se resolve sozinho em tempo útil:** a gêmea sai
da origem com `Cache-Control: public, max-age=600, s-maxage=604800` (`MEDIDO` em
`:8088`) e `Etag: "b0ccb5c9…"` — o ETag da origem **é** o sha declarado, então a
origem está certa e só a borda está velha. Sete dias de `s-maxage` na gêmea, e
**ninguém purga a gêmea**: `--purge-targets` deriva do hash neutralizado, a purga
interna do publicador é por tag de área e por URL de página (nenhuma casa
`/rota/index.md`), e `tools/purge-origin-cache` só aceita `--rota`/`--gemeas-de-area`.
Nota de operação que caiu junto: `:8088` **não emite `X-Cache` nem `Age`**
(`MEDIDO`, dump completo) — o DEPOIS do passo 12 do ESTANCAR procura cabeçalho
que não existe e lê vazio como sucesso.

### 2.2 MCP e A2A — ninguém sonda, e os dois respondem

`MEDIDO`, contra `:8089`:
- `POST /mcp` `tools/call ler_pagina` → `event: message` + `data: {…}` com o
  markdown (precisa de `Accept: application/json, text/event-stream`; responde
  **sem** `initialize`).
- `POST /a2a/v1` `SendMessage` com `A2A-Version: 1.0` → `result.message.parts[0].text`
  com o mesmo frontmatter.

Os dois estão de pé e **nenhum dos cinco runbooks os sonda**. São 2 requisições
de loopback, ~1 s. O I-3 do PUBLICAR é o único que os prevê.

### 2.3 O comportamento dos bots, agora, com lag ZERO

`MEDIDO` em `/var/log/nginx/wikijuridica/access.log` (70,5 MB, escrito às
22:43:08), janela `15/Sep/2026:21`, contando **linha** com `LC_ALL=C`:

```
Applebot=20 · bingbot=5 · ChatGPT-User=3 · OAI-SearchBot=2 · PerplexityBot=1
```

E o dano concreto, no mesmo log: **20 requisições a `/redesocial/tema/…` com
404**, das quais **Amazonbot 7 e GPTBot 2** com `warm=-` (tráfego real). Caminhos
distintos incluem `/redesocial/tema/leis/cc-art-167/`,
`/redesocial/tema/jurisprudencia/stf-adi-7888/feed.xml`,
`/redesocial/tema/diarios/mg-20260911/`.

Causa medida: `./tools/check-social-temas-espelhados` → **EXIT=1**,
*"67 pagina(s) publicadas anunciam um tema que devolve 404 … paginas /area/slug/
no manifesto: 11106 … FALTANDO tema: 67"*.

Quem semeia é `cmd/generate-social-temas --aplicar`, e `MEDIDO` por grep em
`tools/ ops/systemd/ .githooks/ cmd/publish-v2-direct/`: o **único** chamador é
`tools/deploy-publico:714`. Publicar por `publish-v2-direct` (que é o que os dois
blocos fazem) nunca semeia.

**Isto é trabalho para HOJE e não é dos 2.488 do futuro: são 67 páginas já no ar,
com bots já batendo no vazio, e a correção é uma linha.**

---

## 3. ONDE AINDA SE PEDE ESPERA QUE TEM ATALHO

### 3.1 DAEMON D2 — "um ciclo inteiro de timer" é calendário disfarçado

O bloco DAEMON escreve: *"Cada uma só avança depois de a anterior ter passado UM
CICLO INTEIRO de timer dela"*, e defende como blast radius. Mas o ciclo de
`wikijuridica-qualidade-diaria` é **diário** — é literalmente a "margem de 1 dia"
que a ordem do dono proíbe.

**O atalho está no próprio bloco e não foi aplicado:** `sudo -n systemctl start
<unit>.service` executa a unit AGORA, com o `SuccessExitStatus`, o `OnFailure`, o
`flock` e o `Nice` reais, e `systemctl show -p Result -p ExecMainStatus` dá o
veredito em segundos. O DAEMON já usa `systemd-run` para as voláteis do bloco C —
é a mesma técnica. Espera eliminada: de 24 h para o tempo da própria passada.

### 3.2 ESTANCAR PC-1 — a carência não é renovada por publicar, e o atalho não existe

O ESTANCAR afirma que "a própria publicação do passo 8 renova a carência". O
refutador do PUBLICAR já provou o contrário por código
(`cmd/publish-v2-direct/main.go:1206-1235` só remove carência **vencida**).
`MEDIDO` agora: `./tools/sweep-sitemap-carencia-expirada --seco` → *"6 shard(s)
fora do indice | 0 vencido(s) | 2 vencendo em menos de 48h"*, `pages-0095.xml`
vencendo `2026-09-16 07:50Z`, e `pages-0097/0098/0100` em `2026-09-18 13:44Z`.

`MEDIDO`: a ferramenta tem **uma só flag**, `--seco` (`:197`). **Não há atalho
para varrer antes do vencimento** — e isso é honesto dizer, não esconder.

**A forma correta de escrever o passo**, que troca espera por restrição:
a pré-condição de todo reinício do Go é `0 vencido(s)` (asserir sobre o contador
no texto, nunca sobre o exit, que é 0 nos dois casos); e **entre 07:50Z e a
varredura, nenhum reinício**. A varredura agendada é
`wikijuridica-sitemap-shard-grace.timer` às **05:19:09 -03 = 08:19:09Z** `MEDIDO`
— 29 min DEPOIS do vencimento —, e a onda dispara **04:31:33 -03 = 07:31:33Z**
`MEDIDO`, 19 min ANTES. Quem quiser eliminar a janela roda
`./tools/sweep-sitemap-carencia-expirada` (sem `--seco`) às 07:52Z, não antes.

### 3.3 O que já tem atalho e está certo (não mexer)

COLETA: parser antes da recoleta (81,4% sem esperar os 67 min de Crawl-Delay).
PUBLICAR: mover a HORA da publicação em vez de esperar o GPTBot das 01h UTC.
PUBLICAR/GATES: `WIKI_EFEITO_NOS_BOTS_LOG=<fixture>` para o gate de 14+14 dias.
Todos: `tools/measure-crawl-coverage` sob demanda em vez do timer de 01:11.

---

## 4. O INSTRUMENTO QUE OS CINCO PEDEM EM COMUM

**Dois instrumentos, quatro blocos cada. Constroem-se UMA vez, primeiro.**

**I-COMUM-1 — `tools/check-publicado-no-ar`** (nome do PUBLICAR; adotar esse).
Pedido por: ESTANCAR (I-1, 2ª perna), PUBLICAR (I-3), GATES (passo 10),
COLETA (§25, forma degenerada: só `/healthz` + `DYNAMIC`).
Escopo mínimo, já justificado por medição minha: por rota, comparar o oráculo
`GET /api/v1/citar/<rota>` (do Go em **`:8089`**, nunca `:8088`, que tem
`proxy_cache wj_dyn` com `s-maxage=3600`) contra **cinco** corpos —
HTML da borda, HTML do disco, `<rota>index.md` da borda, a variante
`Accept: text/markdown` da MESMA URL (terceiro objeto de cache: `vary: Accept-Encoding, Accept`,
`age` 31.671 contra 32.610 do HTML `MEDIDO`), e MCP `ler_pagina` + A2A `SendMessage`.
Acrescentar o que nenhum dos três previu: ler o HTML **também com
`Accept-Encoding: br`**, porque é o `.br` de disco que o nginx entrega ao bot (§1.6).
Exit 0/1/2, grava só com `--gravar`.
**Controle negativo obrigatório**, senão o gate nunca reprovou: hoje ele tem de
sair **1** em 13 de 13 rotas da amostra que eu medi.

**I-COMUM-2 — `tools/measure-coorte-de-publicacao`** (nome do PUBLICAR).
Pedido por: PUBLICAR (I-4), ESTANCAR (§5 B-1/B-2/B-3), GATES (passo 11),
COLETA (§27). Os quatro escrevem o MESMO `LC_ALL=C grep -c -iE` sobre o mesmo
log, com as mesmas três armadilhas (locale, linha vs ocorrência, bucket UTC).
Uma implementação, quatro chamadores.
Correção medida a embutir: o predicado de tráfego real é **`warm=-`**, nunca
`warm=false` — o nginx renderiza cabeçalho ausente como `-`
(`ops/nginx/wikijuridica.conf:61`, `warm=$http_x_warming_request`), e eu confirmei
`warm=-` nas linhas de Amazonbot/GPTBot que medi.

Terceiro instrumento, pedido por **dois** blocos com o mesmo diagnóstico:
**`tools/generate-alvos-por-manifesto`** (ESTANCAR I-3) = a "lacuna 2" do
PUBLICAR, palavra por palavra. Uma só.

E a correção de uma linha em `tools/purge-edge-cache:191` (`alvos = []`) é pedida
por ESTANCAR (I-4) **e** PUBLICAR (lacuna 4). Fazer no primeiro bloco que rodar;
o segundo confere por `grep` e não re-edita.

---

## 5. CONFLITOS ENTRE RUNBOOKS

### C1 (grave) — P4 invalida o número central do P6, e os dois declaram ordens opostas

A ordem do plano é `… P4 P5 P6 …`. Mas o PUBLICAR escreve, na seção ORDEM:
*"Travessia antes de corrigir regua: com os dois no mesmo movimento, um defeito
no ar deixa de ser atribuivel."* — quer publicar **antes** do P4.

E é material: o GATES passo 4 troca `corpoDaPagina` por `corpoParaMolde` nos
quatro produtores de assinatura (`cmd/generate-acordao-pages/main.go:294`,
`:711`, `:795`, `:2318` — `MEDIDO`, o runbook diz `:715`/`:799`), e o passo 6
remove o corte de `pisoEmentaPalavras` em `:532` (`const` em `:402`, `MEDIDO`).
Os dois mudam a população que chega ao anti-molde. Depois do P4, os **4.763
candidatos** e as **2.488 páginas montadas** do F8-bis do PUBLICAR **não são mais
os números do gerador** — e o PUBLICAR ainda manda, no passo 8, conferir a
decomposição `2.488 + 1.405 + 682 + 165 + 22 + 1`.

Resolução (é decisão de engenharia, não do dono): **P4 primeiro, e o P6 recenseia
antes de publicar**. O motivo é o C2.

### C2 (grave) — o teto do contrato: os dois blocos erram o número, e P6 o estoura

`MEDIDO` lendo `tools/check-contrato-vs-medicao:191-192`
(`folga = max(200, int(publicadas * 0.05))`, sobre **publicadas**) e calculando:

| declarado | reprova a partir de | margem sobre 11.106 |
|---|---:|---:|
| 11.039 (hoje) | **11.621** | **515** |
| 11.106 (depois do P0) | **11.691** | **585** |

O P0 compra **70 páginas**, não os "555" que o ESTANCAR anuncia nem os "488" do
PUBLICAR. E o lote do P6 é **2.488** → manifesto **13.594** → reprova com as duas
declarações. Com o P4 antes (até +1.405), **14.999**.

Consequência que nenhum dos dois escreve em conjunto: o gate é **incondicional**
no `pre-commit` (`.githooks/pre-commit:283-286`) e lê a **worktree**. Entre o
publish e a edição da linha 128 do `CLAUDE.md`, **todo commit de toda sessão
reprova**. O passo 10a do PUBLICAR cobre isso; o oneshot do passo 12 **não**
(o refutador achou); e o ESTANCAR, que declara 11.106 no P0, deixa o P6 com uma
margem que ele acha ser 555 e é 70.

### C3 (grave) — COLETA §A-3 ressuscita `--seco`, que trava o pré-voo do PUBLICAR

O COLETA conserta `tools/run-daily-content --seco`. O próprio bloco avisa que
`--seco` **gera páginas** e deixa `v2_pages`/`portfolio_v2` sujos, parando o
`deploy-publico` no 0a-bis. O que ele não diz: **o passo 1 do PUBLICAR exige
`git status --porcelain data/editorial/v2_pages data/editorial/portfolio_v2`
VAZIO**, e o 5b/5c commita esses shards. Exercitar `--seco` depois do COLETA
bloqueia o P6 — e o P6 é o bloco que publica.

### C4 — P1b constrói `--piso-por-conteudo`; P6 roda o gerador sem a flag

ESTANCAR I-2 cria `--piso-por-conteudo` em `tools/generate-first-published-at`.
PUBLICAR passo 10c roda `python3 tools/generate-first-published-at --dry-run` e
depois sem flag; o oneshot (etapa 22) idem. Como o gerador é
`carrega_existente` + `setdefault`, as 11.106 entradas do P1b sobrevivem — mas o
piso deixa de ser aplicado às rotas novas, e o instrumento decai em silêncio. Uma
palavra em dois lugares.

### C5 — dois blocos editam a mesma linha de `tools/purge-edge-cache:191`

ESTANCAR I-4 e PUBLICAR lacuna 4 propõem o mesmo `alvos = []`. Quem rodar segundo
encontra o arquivo já corrigido e o `git add` sem diferença; sem uma linha
dizendo "confira por grep, não re-edite", vira diagnóstico de falha.

### C6 (o mais perigoso) — o cérebro reinicia o servidor NO MEIO da transação de publicação

Ver §6.1. É conflito entre o bloco DAEMON (que é o **último** do plano) e os
blocos ESTANCAR/PUBLICAR (que são os que publicam), e a ordem do plano o deixa
sem guarda exatamente durante as duas publicações.

---

## 6. PRECEDENTE QUE CONTRADIZ UM PASSO

### 6.1 O precedente é o próprio código: `wikijuridica-server-reload.path`

`MEDIDO`, `ops/systemd/wikijuridica-server-reload.path` (unit **`active`**):

```
PathChanged=/opt/wiki/data/ai/embeddings/ativo.json
PathChanged=/opt/wiki/data/ai/grafo_vizinhanca.jsonl
PathChanged=/opt/wiki/data/ai/risco_superacao.jsonl
Unit=wikijuridica-server-reload.service
```
e `wikijuridica-server-reload.service`:
`Type=oneshot`, `ExecStart=/usr/bin/systemctl restart wikijuridica-server.service`
— **incondicional, sem guarda, sem conferir lock de publicação**.

`cmd/cerebro/main.go:276-278` confirma o desenho por escrito: *"Quem reinicia o
servidor e o systemd: wikijuridica-server-reload.path observa ativo.json e
dispara o restart."*

`MEDIDO` no journal das últimas 72 h — **disparou 3 vezes em 24 h**:

```
set 15 04:40:01 → 04:40:27   (restart, ~26 s)
set 15 06:53:51 → 06:54:19   (~28 s)
set 15 12:29:55 → 12:30:27   (~32 s)
```

E a de **12:29:55** caiu **58 segundos** depois de `content/pages.json` ser
reescrito pela onda (mtime **12:28:56**). Foi uma quase-colisão, em produção,
hoje.

**O que isso quebra, e é a razão de o veredito ser alto:** ESTANCAR passo 8 e
PUBLICAR passo 9 rodam `publish-v2-direct` por centenas a milhares de segundos
(o PUBLICAR prescreve `timeout 3600`). Um lote do cérebro dentro dessa janela
reinicia o Go com `public/` e o sitemap **parcialmente escritos** — que é
exatamente o `sitemap_loc_without_manifest` que os dois runbooks descrevem como
**laço de 5 s eterno e MUDO**. `MEDIDO`:
`wikijuridica-server.service` → `OnFailure=` **vazio**,
`StartLimitIntervalUSec=0`, `WatchdogUSec=0`, `NRestarts=0`, ativo desde
12:30:27.

**Autorrefutação, e ela SUSTENTA o achado.** Tentei derrubá-lo pela atomicidade:
`escreveAtomico` (`cmd/publish-v2-direct/main.go:3131-3155`) usa `os.Rename`, então
**arquivo nenhum fica rasgado**. Mas o risco não é por arquivo, é pela TRANSAÇÃO,
e ela tem uma janela medida em linhas: o `sitemap.xml` sai em **`:1128`**
(`escritor.grava`) e o manifesto só em **`:2120`** (`writeManifest`), ~992 linhas
de fluxo depois — e o próprio `:332` avisa: *"writeManifest faz os.Create no
published_manifest.jsonl"*, isto é, **trunca-e-escreve, fora do funil atômico**
(`:2096`: *"`pages.json`/`published_manifest` não passam por aquele funil"*).
Reiniciar entre `:1128` e `:2120` dá sitemap anunciando rota que o manifesto não
tem = `published_manifest_sitemap_loc_without_manifest`
(`internal/publishedmanifest/publishedmanifest.go:215` e `:300`) = boot recusado
(`:355`, *"o servidor não sobe"*), com `Validate` chamado no boot (`:2103`).

`DERIVADO` da frequência medida: 3 disparos/dia contra uma janela de 3.600 s
≈ **12,5%** de chance de colisão por publicação longa.

**Nenhum dos cinco runbooks pausa o cérebro antes de publicar.** O bloco que o
trata (DAEMON/P9) é o último do plano.

**A correção, e não devolve decisão nenhuma ao dono:** antes do primeiro
`-allow-public-write` de qualquer bloco, `sudo -n systemctl stop
wikijuridica-server-reload.path` (parada explícita é limpa: não há `Restart=`
numa `.path`), publicar, reiniciar pela cadeia, e religar com `start`. Registrar
o par no ledger. Alternativa equivalente: `systemctl stop
wikijuridica-cerebro.service` durante a transação — mas parar a `.path` é o
menor raio, porque o cérebro continua trabalhando.

### 6.2 BUG-236 contradiz o A7 do bloco DAEMON

Memória `check-tools-gravar-precedente` (BUG-236) e `CLAUDE.md` §4:
`tools/check-*` com série própria são **read-only por padrão** e gravam só com
`--gravar` — `check-edge-cache-coverage`, `check-disk-growth`,
`check-fontes-alcancaveis`, `check-internal-link-block`,
`check-superficie-bots-live` seguem isso.

O DAEMON A7 propõe **`--nao-gravar`** em `check-portal-health` — mantém a escrita
por padrão e cria um opt-out. É o inverso do precedente. A forma certa é
`--gravar`, com `ops/systemd/wikijuridica-watchdog.service` passando a flag —
mesma linha, sentido invertido, e aí o gate para de zerar `reparo_ultimo` em toda
execução de diagnóstico.

### 6.3 "Produto não fica untracked" contra o estado de HEAD

`~/.claude/CLAUDE.md`: *"Produto não fica untracked. Arquivo novo entra no commit
da própria frente na sessão em que nasce."* `MEDIDO`: **33** arquivos untracked
em `data/`, entre eles **3 recibos terminais** de transação v2ingest e cinco dias
de `data/ops/access/*.jsonl`. E `data/ops/v2_ingest_transaction_receipt.json`,
lido por `internal/v2readguard/guard.go:35`, está ` M` desde **2026-09-10**.

Nenhum runbook classifica esses 33 no `.gitignore` nem os commita. O pathspec de
§1.7 resolve a parte de produto; os `access/*.jsonl` precisam de veredito
declarado (ruído classificável ou série a commitar) — e a regra proíbe deletar.

### 6.4 O `dispatcher_orfao_test.go` e os três gates novos

COLETA §B-11/§D-23 e DAEMON A5 registram gates novos em `internal/checks`. O
próprio COLETA avisa que `dispatcher_orfao_test.go` varre AST nos **dois**
sentidos (`Names` **e** `case`). O que nenhum escreve: registrar em `Names`
**antes** de o produtor existir põe o gate a reprovar por dívida, não por
regressão — e ele entra na bancada diária, que já tem **12 vermelhos**. O
precedente do repositório é `check-csp-style-hashes`, que **nasce com carência
declarada**. Os três gates novos nascem com a mesma carência escrita, ou entram
no mesmo commit do produtor.

---

## 7. UMA SESSÃO SÓ? — não, e a serialização é maior do que os runbooks declaram

**São TRÊS units que tomam `/tmp/opt-wiki-agent-heavy.lock`, não uma.** `MEDIDO`
por `grep ExecStart ops/systemd/*.service` + `systemctl list-timers`:

| unit | ExecStart | próximo | duração medida | teto |
|---|---|---|---|---|
| `wikijuridica-qualidade-longa` | `flock /tmp/opt-wiki-agent-heavy.lock … run-qualidade-diaria` | **hoje 02:11:26 -03** | 34 min 06 s (02:11:22→02:45:28) | 75 min |
| `wikijuridica-qualidade-diaria` | idem | 2026-09-16 04:47:17 -03 | **60 min 42 s** (04:48:12→05:48:54) | 90 min |
| `wikijuridica-qualidade-race` | `flock … run-qualidade-race` | dom 2026-09-20 03:43:45 -03 | não medida | **5 h** |

Os cinco runbooks nomeiam **só** a janela 04:47–05:50. A `qualidade-longa` de
**02:11 de hoje** — daqui a ~3 h 30 min — não aparece em nenhum, e ela segura o
mesmo lock por até 75 min. O `flock -w 600` que o bloco GATES prescreve
**desiste** dentro dessa janela e deixa o índice staged (§1.5).

Demais fronteiras medidas:
- `wikijuridica-daily-content.timer` → 04:31:33 -03 (= 07:31:33Z), lê
  `tools/run-daily-content` **do disco** no disparo → o bloco COLETA edita esse
  arquivo e **não** o inclui no pré-voo. Editar durante o disparo entrega script
  meio editado. A trava própria é `run-daily-content:76-82`
  (`flock -n 9 /tmp/wiki-daily-content.lock`) — editar **segurando** esse lock.
- `wikijuridica-daily-content-noticias.timer` → 12:20:55 -03, mesmo arquivo.
- `wikijuridica-stj-acordaos-coleta.timer` → 09:51:24 -03, colide com o §B-15/16
  do COLETA pelo `scope:collect:stj-acordaos`.
- `wikijuridica-watchdog.timer` → a cada 2 min, roda `check-portal-health --repair`
  do disco: o A7/A8 do DAEMON edita **o vigia vivo**, sem janela de ensaio.
- `wikijuridica-server-reload.path` → ativo, 3 disparos/dia (§6.1).
- `wikijuridica-brotli-cobertura.timer` → horário, `RandomizedDelaySec=5min`.

**Veredito:** o plano **não** é executável por uma sessão só como está escrito —
não por falta de mãos, mas porque cinco units automáticas escrevem nos mesmos
arquivos e reiniciam o mesmo serviço. O que o torna executável, e é engenharia,
não espera:

1. Pré-voo único e compartilhado, que lista os **seis** relógios acima (não dois).
2. `flock -w 5400` (não 600) em todo commit de Go, pegando o lock **antes** do
   `git add` — e `git commit -F <msg> -- <caminhos exatos>` para o índice nunca
   sujar.
3. `systemctl stop wikijuridica-server-reload.path` durante toda transação de
   publicação, com `start` no fim e linha no ledger.
4. Editar `tools/run-daily-content` segurando `flock -n 9 /tmp/wiki-daily-content.lock`.
5. Presença registrada por `tools/generate-coord-presence` antes de cada bloco, e
   `tools/check-coord-inbox` a cada ciclo — o arquivo `.agents/runtime/onda-avanca/antes.txt`
   é estado **compartilhado** e já está ` M` na worktree.

---

## 8. A ORDEM QUE ISSO IMPÕE (o que muda no plano)

```
P-0.5  NOVO, hoje, 3 comandos, sem esperar nada:
       (a) generate-social-temas --aplicar          -> 67 páginas param de mandar bot a 404
       (b) generate-legal-cocitation                -> índice sai dos 4 dias de atraso
       (c) generate-brotli-static --jobs 4          -> fecha o .br stale já vermelho
       depois: check-social-temas-espelhados / check-percursos / check-brotli-static-fresco == 0
P-0.6  NOVO: stop wikijuridica-server-reload.path antes de qualquer publish (§6.1)
I-COMUM-1 e I-COMUM-2  construídos UMA vez, antes de P1b (§4)
P-1, P0  (P0 com o teto correto: 11.691, ganho de 70)
P1b      + brotli (§1.6) + 2.6 (§1.4) + pathspec de 10 arquivos (§1.7)
P2/P1/P3 COLETA, com `--seco` fora do bloco (C3) e o pré-voo de 6 relógios (§7)
P4/P5    GATES, com internal/ptbrtext na proibição (§1.1)
P6/P8/P7 PUBLICAR, recenseando DEPOIS do P4 (C1) e com 10a antes de qualquer commit (C2)
P9/P10   DAEMON, com A7 como `--gravar` e não `--nao-gravar` (§6.2)
P12      GPU
```

---

## 9. O QUE NÃO MEDI, E POR QUÊ

- Quantas das 942 rotas do P1b têm `.br` divergente **depois** de publicar: exige
  publicar. O que medi é a mecânica (`brotli_static` serve o `.br`; o gate está
  vermelho por 1 arquivo com 1,0 h de atraso) e a janela do reparo (~65 min).
- A probabilidade exata de colisão do `.path` com a transação: os 12,5% são
  `DERIVADO` de 3 disparos/dia × 3.600 s; a distribuição real dos disparos é
  ligada aos lotes do cérebro, que não modelei.
- Tempo de parede de `publish-v2-direct` sobre 11.106 páginas: rodar = mutar.
- Quantas páginas o P4 devolve ao P6: exige rodar o censo `-seco -limite 99999`,
  que é o passo 2 do bloco GATES.
- Se os 67 temas faltantes cobrem as 944 de hoje ou são herdados: a saída do gate
  mostra `/diarios/` na amostra, mas não paginei a lista inteira.
