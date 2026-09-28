# MODO DE OPERAÇÃO

Procedência desta seção: escrita em **2026-09-15 22:51–23:10 -03 / 2026-09-16 01:51–02:10Z**, PLAN MODE,
nada mutado. `HEAD 62d71de0`, índice de git **VAZIO**, `go.mod`/`go.sum` **limpos**, `loadavg1 4,90`
— os quatro **MEDIDOS por mim agora**, independentemente dos cinco runbooks (que mediram entre
21:30 e 22:55). Onde os dois conjuntos de medição coincidem, o número tem **dupla procedência** e está
marcado `[M×2]`.

Marcação em todo o documento: **[M]** = executei o comando nesta sessão · **[M×2]** = eu e um runbook
medimos o mesmo número em execuções independentes · **[D]** = aritmética sobre um [M] · **[A MEDIR]** =
só na execução, e o passo diz qual comando o fecha.

---

## §0 · AS OITO DECISÕES QUE FECHAM OS CONFLITOS ENTRE RUNBOOKS

Os cinco runbooks se contradizem em oito pontos. Cada um está decidido aqui, com o critério, e
**não se re-litiga dentro dos passos**.

### D1 — Ordem P4 × travessia do P6: **travessia (5 páginas) → P4/P5 → recenseio → lote cheio**

O bloco PUBLICAR escreve *"travessia antes de corrigir régua"*; o plano manda `P4 → P6`. A **dominância
estrita** resolve: o conjunto que o gerador aceita hoje está **contido** no que o gate aceita (dos 135
pares que a régua do gerador recusa, a real aprova **135 de 135**; o inverso é **0**). Logo as 5 páginas
escolhidas hoje, sob a régua **mais estrita**, continuam válidas depois do P4 — a travessia não precisa
ser refeita. E o lote cheio **tem** de vir depois, porque o P4 muda a população: os `4.763 candidatos` e
as `2.488 páginas montadas` deixam de ser os números do gerador e viram **[A MEDIR]** no recenseio.

**Consequência escrita nos passos:** o `SE NÃO VIER` do lote cheio **não** compara com 2.488; compara com
o recenseio pós-P4, e a decomposição `2.488+1.405+682+165+22+1` sai de todo veredito.

> **Procedência da D1, declarada**: a dominância 135/135 foi medida na família **`stj-tema-derivado`**, não na
> de acórdãos, que é população outra e maior. Isto é **inferência por contenção, a confirmar no recenseio
> (P-b1)** — não é medição sobre acórdãos, e não se cita como tal. Se o recenseio pós-P4 mostrar páginas da
> travessia caindo, a inferência falhou e o certo é refazer a travessia, não forçar o número.

### D2 — O teto do contrato é **11.621 / 11.691**, e o P0 compra **70 páginas**, não 555 nem 488

`tools/check-contrato-vs-medicao:191-192` [M]: `folga = max(200, int(publicadas * 0.05))` — a folga sai do
número **MEDIDO**, não do declarado. Com `declarado = 11.039`: reprova quando `0,95 × publicadas > 11.039`,
isto é **publicadas ≥ 11.621** (margem de 514 sobre as 11.106 de hoje). Com `declarado = 11.106`:
**publicadas ≥ 11.691** (margem 584). **Ganho do P0 = 70 páginas** [D].

ESTANCAR dizia `11.594 → 11.661 (555)` e PUBLICAR dizia `11.594 (488)`. **Os dois estão errados** e os
parágrafos que os contêm ficam superados nesta data. O lote cheio do P6 leva o manifesto a ~13.594 [D],
que **reprova sob as duas declarações** — por isso a reescrita da linha 128 do `CLAUDE.md` é
**etapa 20-bis do oneshot**, não um passo manual que alguém esquece.

### D3 — A regra de piso da estreia é a do refutador (`approved_at` só nas órfãs), e é **comportamento padrão, não flag**

ESTANCAR propôs a regra **C'** = `min(estreia_git, dateModified_servido)`. O refutador mediu que C'
carimba estreia `2026-09-15` em **3 páginas que estrearam em 2026-09-14** (`/noticias/stf-20260914/`,
`/noticias/stj-20260914/`, `/noticias/tst-20260914/`), e o carimbo é **permanente** — `carrega_existente`
+ `setdefault` faz a primeira gravação vencer para sempre.

**Regra adotada:** estreia = data do primeiro commit do manifesto que contém o `unique_intent_id`; **para
as órfãs** (sem entrada no arquivo **e** sem estreia no git) usa-se `approved_at`, **nunca** a data de hoje,
**nunca** `min(…, approved_at)` genérico (essa antecipa estreia em `/diarios/`, onde `approved_at` é a data
do **diário**, não da publicação). Resultado medido pelo refutador: **0 impossíveis, dia-1 = exatamente as
2 legítimas, 23 rotas alteradas, nenhuma entrada existente tocada**.

**E é padrão, não `--piso-por-conteudo`:** com a regra atrás de uma flag, o conflito **C4** existe (PUBLICAR
10c e a etapa 22 do oneshot chamam o gerador **sem** a flag e o piso decai em silêncio). Como padrão, o
conflito **dissolve**.

### D4 — `wikijuridica-server-reload.path` é parado em **toda** transação, como linha de pré-condição

`ActiveState=active` [M], observando `data/ai/embeddings/ativo.json`, `data/ai/grafo_vizinhanca.jsonl` e
`data/ai/risco_superacao.jsonl`, disparando `systemctl restart wikijuridica-server.service`
**incondicional** [M]. O cérebro escreve `ativo.json` a cada lote. `sitemap.xml` sai em `main.go:1128` e o
manifesto só em `:2120`: reiniciar entre os dois dá `published_manifest_sitemap_loc_without_manifest` e o
**boot é recusado** — com `OnFailure=` vazio e `StartLimitIntervalUSec=0`, o laço é **mudo**.

Não vira um "P-0.6" separado (que alguém pula): vira **uma linha de pré-condição e uma de pós** em **todo**
passo que roda `-allow-public-write` — P1b-8, P6-5i, P6-9 e a etapa 13 do oneshot.

### D5 — `--gravar`, nunca `--nao-gravar`, no vigia

DAEMON A7 propôs `--nao-gravar` em `check-portal-health`. **BUG-236** e o §4 do contrato fixam o inverso:
`check-*` é read-only por padrão e grava **só com `--gravar`** (6 ferramentas já seguem). Adotado `--gravar`,
com a consequência escrita: `ops/systemd/wikijuridica-watchdog.service` passa a **passar a flag**, e como a
unit é symlink, o passo carrega `daemon-reload` + `check-units-instaladas` no mesmo movimento.

### D6 — `--seco` de `run-daily-content` **sai** do bloco COLETA

Consertá-lo faz a onda gerar páginas e sujar `v2_pages`/`portfolio_v2` — e o **passo 1 do PUBLICAR exige os
dois VAZIOS**, com `deploy-publico` parando no 0a-bis **para todas as frentes**. Hoje `--seco` cai no `*)`
e sai 2 antes do trap: o estado atual é o seguro. Fica registrado como defeito conhecido, com a condição
para consertá-lo (prefixo de ensaio ou `WIKI_ONDA_ENSAIO=1`), fora deste plano.

### D7 — `purge-edge-cache:191` é editado **uma vez**, no P1b

Pedido por ESTANCAR (I-4) e PUBLICAR (lacuna 4). Feito no P1b; o PUBLICAR **confere por grep** e não
re-edita. E a descrição do defeito fica correta: o **NameError** ocorre **só com `--tag` sem `--url`**;
lista **acima do teto sem tag** cai em `purge_everything` com `purga_total=True`, o `or` curto-circuita e
**não há crash — há purga total silenciosa com exit 0** [M, lido em `:192`, `:205-210`, `:245-247`]. Os dois
são defeitos; são defeitos **diferentes**.

### D8 — `internal/ptbrtext` entra na lista de proibição do bloco GATES

`go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` = **452 deps** [M]. **DENTRO** do grafo do
validador: `internal/quality`, `internal/legalsignature` e **`internal/ptbrtext`** [M]. **FORA**: `cerebro`,
`ollama`, `checks`, `v2bodyneardup`, `tetodelote`, `stjacordaos`, `codex2policyenforcement`,
`shellscriptquality`, `sourceresolve`, `datajudfila` [M]. A tabela §1 do GATES proibia só os dois primeiros
— e `ptbrtext` é chamado em `cmd/generate-acordao-pages/main.go:859`, exatamente onde o `SE NÃO VIER` do
passo 5 mandava mexer. **Editar `ptbrtext` custa `generate ./internal/v2ingest` + atestação no mesmo commit
+ 25 testes depois de ~10 min.** Importar é livre.

---

## §0-bis · TRÊS ACHADOS DESTA SESSÃO QUE MUDAM INSTRUMENTO E JANELA

**N1 — O `ETag` da gêmea Markdown É o `sha256[:32]` do corpo. [M, na origem E na borda]**

```
origem :8089  Etag: "b0ccb5c9ec443093951389823e44cd73"   sha256 corpo = b0ccb5c9ec443093951389823e44cd73 1ece764c…
borda         etag:  "f4fe9c65040161dbb44562fd97436084"   sha256 corpo = f4fe9c65040161dbb44562fd97436084 47ae7a63…
```
Logo **a paridade do canal de máquina se verifica por `HEAD`**, comparando `etag` com
`markdown_sha256[:32]` de `/api/v1/citar` — **sem baixar corpo**. Isso torna `check-publicado-no-ar`
barato o bastante para amostra de 100+ rotas em vez de 6. O **HTML na borda não tem ETag** (só
`last-modified: Sat, 05 Sep 2026 00:00:00 GMT`, que é a data **editorial** e não muda) [M] — para HTML a
prova continua sendo **por corpo**.

**N2 — São SEIS units que tomam `/tmp/opt-wiki-agent-heavy.lock`, não três. [M por grep em `ops/systemd/*.service`]**

| unit | próxima | duração medida | teto |
|---|---|---:|---|
| `wikijuridica-qualidade-longa` | **hoje 02:11:26 -03** (02:10 + 90 s) | **34 min 06 s** | 75 min |
| `wikijuridica-official-source-url-inventory-refresh` | 04:22:06 -03 (04:20 + 5 min) | **1 min 46 s** | 15 min |
| `wikijuridica-qualidade-diaria` | 04:47:17 -03 | **60 min 42 s** | 90 min |
| `wikijuridica-noticias-coleta` | **07:15 · 11:50 · 16:20 · 21:50** -03 (4×/dia) | **14 s** | 20 min |
| `wikijuridica-qualidade-race` | dom 2026-09-20 03:43:45 | não medida | **5 h** |
| `wikijuridica-corpus-oraculo-recoleta` | seg 2026-09-21 04:19 | não medida | — |

Os cinco runbooks nomeiam **só** a `qualidade-diaria` (04:47–05:50). A `qualidade-longa` de **02:11 de hoje**
(≈3 h 20 daqui) segura 34 min, e o `flock -w 600` que o bloco GATES prescreve **desiste dentro dela**,
deixando `.go` no índice — que passa a custar a closure de **77,6 s** a toda sessão que commitar depois.

**N3 — PC-1 é risco vivo amanhã, e publicar NÃO o resolve. [M]**

`cmd/publish-v2-direct/main.go:1242` remove shard órfão **só** no ramo `carencia_vencida`; fora dele,
`:1288` faz `orfaosEmCarencia++`. Estado agora [M]: `6 shard(s) fora do indice | 0 vencido(s) | 2 vencendo em
menos de 48h`, com `pages-0095.xml` vencendo **2026-09-16 07:50Z** e `pages-0097/0098/0100` em
2026-09-18 13:44Z. A afirmação do ESTANCAR (*"a própria publicação renova a carência, resolve PC-1 de graça"*)
é **falsa por código**.

A janela real: a onda dispara **04:31:33 -03 = 07:31:33Z** e termina recarregando o servidor **entre 07:41Z e
07:50Z** — as 4 durações medidas (1.091, 576, 1.044, 759 s) põem a recarga em 07:49:44 · 07:41:09 · 07:48:57 ·
07:44:12Z, e **duas das quatro ficam a menos de 2 min do vencimento** [D sobre as durações medidas]. A margem
é apertada, não confortável;
`wikijuridica-sitemap-shard-grace` passa **05:19:09 -03 = 08:19:09Z**, 29 min **depois**, e é
**inventário**, não varredura. Entre **07:50Z e a próxima publicação (12:20 -03 = 15:20Z)** qualquer
reinício do Go falha **em silêncio** — e o `.path` do D4 dispara 3×/dia.

**Fecho, que é engenharia e não espera:** rodar `./tools/sweep-sitemap-carencia-expirada` (sem `--seco`)
**a partir de 07:50Z** e antes de qualquer reinício; e criar `wikijuridica-sitemap-shard-sweep.timer` a
**07:52Z**, porque antes do vencimento a varredura **não remove nada**.

---

## §1 · OS INSTRUMENTOS QUE SE CONSTROEM PRIMEIRO

Sem estes, nada é verificável na hora — e quatro deles são pedidos por **mais de um** bloco com a mesma
descrição. Constroem-se **uma vez**, antes do primeiro passo de qualquer runbook, em **dois commits**
(um leve de `tools/`, um pesado de Go). Nenhum pacote tocado está no grafo do validador [M] ⇒ **sem
reatestação**.

| # | instrumento | o que mede | exit | grava | quem depende |
|---|---|---|---|---|---|
| **I-1** | `tools/check-publicado-no-ar` | coerência das **6** serializações de uma rota contra o oráculo `/api/v1/citar` **no Go `:8089`** | 0 coerente · 1 divergente · 2 não mediu | nada; `--gravar` → `data/ops/publicado_no_ar.jsonl` | ESTANCAR I-1 2ª perna · PUBLICAR I-3 · GATES 10 · COLETA §25 |
| **I-2** | `tools/measure-coorte-de-publicacao` | descoberta e leitura por agente de uma coorte, em **duas camadas** (origem e borda) | 0 sempre (mede) | `data/ops/coorte_de_publicacao.jsonl`, reescrito por coorte | PUBLICAR I-4 · ESTANCAR §5 · GATES 11 · COLETA §27 |
| **I-3** | `tools/generate-alvos-por-manifesto` | diff **cru** de `approved_at`/`html_sha256` entre duas versões do manifesto → rotas + gêmeas | 0 leu · 2 não leu | **nada**, só stdout | ESTANCAR I-3 · PUBLICAR lacuna 2 |
| **I-4** | `tools/check-cronologia-jsonld` | `dateModified < datePublished` no JSON-LD servido, disco **e** borda por stride | 0 · 1 · 2 | nada; `--gravar` → `data/ops/cronologia_jsonld.jsonl` | ESTANCAR (é o ANTES/DEPOIS do bloco) |
| **I-5** | correção em `tools/purge-edge-cache:191` | `alvos: list[str] = []` antes do ramo + **aborto** quando a lista excede o teto | herda | herda | ESTANCAR I-4 · PUBLICAR lacuna 4 (**D7**) |
| **I-6** | `--de-arquivo` em `tools/purge-origin-cache` | purga de origem em lote (hoje só `--rota`/`--gemeas-de-area`/`--seco` [M]) | herda | herda | ESTANCAR 12 · PUBLICAR 11a |
| **I-7** | `ESTADO` por rótulo em `tools/check-onda-avanca` | baseline **namespaceado** por coorte | herda | `antes-<rotulo>.txt` | PUBLICAR 5h/9 · ESTANCAR (não usa, mas a onda usa) |

### I-1 `tools/check-publicado-no-ar` — o comando único que hoje não existe

**Oráculo:** `GET /api/v1/citar/<rota>` **no Go em `127.0.0.1:8089`**, nunca em `:8088` — o nginx serve
`/api/v1/*` pela zona `proxy_cache wj_dyn` com `s-maxage=3600`, e uma resposta de até 1 h de idade faria o
instrumento acusar a unit por um defeito de cache.

**LEITURA 0 — classe `go_desatualizado`, e vem primeiro.** `/api/v1/lote?limite=1` → `fim.total` contra
`wc -l published_manifest.jsonl`, e `ExecMainStartTimestamp` contra o mtime mais novo de
`public/<rota>/index.html`. `buildAPIPublishedPages` roda dentro de `httpserver.New()`
(`httpserver.go:1071`): as superfícies de máquina são **retrato do boot**. Veredito literal:
*"reinicie pela cadeia (`./tools/reload-wiki-server`); NÃO republique, NÃO purgue."*
**Terceira classe obrigatória, `origem_cacheada`:** quando `:8089` e `:8088` divergem, o remédio é
`./tools/purge-origin-cache`, **não** reiniciar.

**LEITURAS 1–6 por rota:**
1. HTML da **borda**, por **corpo** (a borda não emite ETag no HTML [M]).
2. HTML do **disco**, `sha256sum public/<rota>/index.html`.
3. HTML da borda com **`Accept-Encoding: br`** — o nginx serve `.br` de disco, e o `curl` sem
   `--compressed` lê o `identity` e passa verde enquanto o bot recebe o corpo antigo.
4. Gêmea `<rota>index.md` da **borda**, **por `HEAD`**, comparando `etag` a `markdown_sha256[:32]` (**N1**).
5. Variante **`Accept: text/markdown`** da MESMA URL — **terceiro objeto de cache** (`vary: Accept-Encoding,
   Accept`), que `check-edge-frescor` declara não sondar e ninguém sonda.
6. `POST /mcp` `tools/call ler_pagina` **e** `POST /a2a/v1` `SendMessage` — duas requisições de loopback,
   ~1 s. Pegadinhas medidas a embutir: A2A exige header `A2A-Version: 1.0` (sem ele `-32009`) e o método é
   **`SendMessage`**, não `message/send`; MCP responde **sem** `initialize`, em `text/event-stream` (o JSON
   vem na linha `data: `) e pede `Accept: application/json, text/event-stream`.

Entrada `--rota` (repetível) / `--de-arquivo` / `--dia AAAA-MM-DD` **obrigatório e explícito** (sem default,
para a armadilha UTC/local não disparar calada). Toda saída por `wikijuridicabot.AplicaSondaInterna`.

**Controle positivo E negativo, os dois obrigatórios:**
```bash
./tools/check-publicado-no-ar --rota /jurisprudencia/stf-adi-4376/ ; echo "EXIT=$?"   # 1 HOJE [M]
WIKI_ORIGEM=http://127.0.0.1:9 ./tools/check-publicado-no-ar --rota /jurisprudencia/stf-adi-4376/ ; echo "EXIT=$?"   # 2
```
A rota acima **tem** de sair **1 hoje**, na leitura 4: `/api/v1/citar` declara
`markdown_sha256 = b0ccb5c9ec443093…`, a origem `:8089` serve exatamente esse corpo, e a **borda** serve
`f4fe9c6504016 1db…` com `cf-cache-status: HIT`, `age 2232` e `date_published "2026-09-11"` [M].
**Gate que nunca reprovou não está provado.**

### I-2 `tools/measure-coorte-de-publicacao`

Âncora por rota, **nesta ordem**: (1) smoke do release em `data/ops/access/access-*.jsonl` com
`bot_class == "self_simulation_probe"` — precisão de **segundo**, e já provou 898 de 898 rotas em **15 s**;
(2) `indexnow_url_state.submitted_at`; (3) primeiro 200 na origem. **Nunca o commit** (erra 21 h 09) e
**nunca o mtime** (carimbo determinístico `00:00:00Z`).

Duas camadas **declaradas em cada linha**: origem (`/var/log/nginx/wikijuridica/access.log`, lag **ZERO**) e
borda (`crawl_coverage_state.crawlers_verified.<bot>.paths_first_seen`, a **única** fonte que prova leitura
que a origem não vê — gptbot **686 rotas lá contra 0 na origem** no mesmo lote). Saída: 1 linha por
`(coorte, agent_key)` com `rotas_tocadas`, `cobertura_pct`, `latencia_s` p05/p50/p95/max,
`hora_utc_do_primeiro_contato`, `camada`, `janela_s`. **Sem janela mínima**, e **nunca** imprime
`INCONCLUSIVO`.

**Correção medida a embutir:** o predicado de tráfego real é **`warm=-`**, nunca `warm=false` —
`ops/nginx/wikijuridica.conf:61` é `warm=$http_x_warming_request` e cabeçalho ausente renderiza `-`.
Quem filtrar por `warm=false` lê **zero** e conclui que nenhum bot de IA está entrando.
Mais: `LC_ALL=C` obrigatório (`date +%b` dá `set` em pt_BR e o nginx escreve `Sep`); contar **linha** com
`grep -c`, nunca ocorrência com `grep -oE` (o UA do PetalBot casa 2×); `data/ops/access/` bucketiza por
**UTC**, então "hoje" local atravessa **dois** arquivos; o smoke tem `warming:false`, então filtrar só por
`warming` conta 898 requisições internas como visita real.

### I-3 `tools/generate-alvos-por-manifesto`

Diff **cru** (`--base <ref-ou-arquivo>` × worktree): rotas cujo `approved_at` **ou** `html_sha256` mudou,
mais a gêmea `<rota>index.md` de cada uma. **Obrigatório porque `--purge-targets` devolve zero por
construção** — o `content_sha256` não tem campo de data e `neutraliza_datas` apaga toda ISO; e a cegueira é
da **família inteira** (`--purge-targets`, passo 6 do `deploy-publico`, IndexNow incremental,
`check-lastmod-causalidade`, `check-edge-frescor`), cujos seletores `--dia/--desde-horas/--desde-ledger` são
todos sobre rota **carimbada**. `rotas_com_bytes_novos():440-478` já computa quase isto, mas só está cabeada
a `--desde-commit`, que **força re-datação** e é proibido na mesma passada do `--ressemear`.

### I-4 `tools/check-cronologia-jsonld`

Lê `public/<rota>/index.html` de cada rota do manifesto, extrai `"datePublished"`/`"dateModified"`
**ancorado no bloco `application/ld+json`**, reprova quando `dateModified < datePublished`.
**Segundo invariante, e ele é campo próprio da saída `--json`, `estreia_acima_do_modificado`**: para cada
rota, `first_published_at[uid] > dateModified`. É o que o **P1b-5** lê — sem declará-lo aqui, o DEPOIS
daquele passo nomearia um campo que instrumento nenhum produz.
2ª perna: stride determinístico (`i % passo == 0`, **nunca prefixo**) contra a **borda**, comparando com o
disco. Teste de nascença com **prova por mutação**: inverter o `<` tem de matar o teste — **nos dois
invariantes**.

**O baseline de hoje, que eu medi e é o controle negativo grátis** [M×2]:
```
rotas no manifesto: 11106
cronologia impossivel (dateModified < datePublished): 942
sem JSON-LD/arquivo: 0
canais: {'/jurisprudencia/': 875, '/leis/': 38, '/sumulas/': 29}
datePublished dos impossiveis: {'2026-09-15': 942}
```
**Justificativa medida por execução de que ele não é redundante:** `./tools/check-lastmod-causalidade` sai
**EXIT=0** com `datas FABRICADAS (hash igual) 0` enquanto essas 942 servem cronologia impossível — ele mede
`lastmod`/`content_revised_at`, e a corrupção vive em `approved_at`/`datePublished`, que o hash de revisão
ignora **por construção**.

### I-5 · I-6 · I-7 — três correções de uma linha cada, com teste

- **I-5** `purge-edge-cache:191`: `alvos: list[str] = []` antes do ramo `if seletivo:`, **mais** um aborto
  explícito quando `caminhos` excede `--teto-por-url` (hoje isso degrada **em silêncio** para
  `purge_everything` com **exit 0** [M]). Teste que exercite `--tag` **sem** `--url` (NameError) e lista
  acima do teto **sem** tag (purga total silenciosa). São **dois** defeitos distintos (**D7**).
- **I-6** `purge-origin-cache --de-arquivo`: irmão exato do I-5. Sem ele, o passo de purga de origem do
  ESTANCAR nomeia **uma** rota de exemplo e não tem mecanismo para as ~942 necessárias. Alternativa
  aceitável no passo, se a flag não entrar: `xargs -a lista -n1 -I{} ./tools/purge-origin-cache --rota {}`
  com exit conferido por iteração.
- **I-7** `check-onda-avanca`: `ESTADO="$ESTADO_DIR/antes-${ROTULO}.txt"` com **fallback de leitura** em
  `antes.txt`, para não quebrar a onda em voo. Hoje `ESTADO` é um arquivo **único global** (`:36-37`) e
  `--rotulo` só alimenta o `echo` (`:64`, `:115`) [M] — então o `--antes` deste plano **sobrescreve** o
  baseline da onda, e o `--depois` dela passa a reportar `novas: 0`, que é o falso negativo exato que
  `internal/tetodelote` existe para tornar visível. `.agents/runtime/onda-avanca/antes.txt` já está ` M`:
  **é estado compartilhado**, e o passo registra presença por `tools/generate-coord-presence`.

---

## §2 · ORDEM GLOBAL E PONTOS DE SERIALIZAÇÃO

```
P-0.5  DEFEITO VIVO, 3 comandos, zero espera, nenhuma dependência
P-0.6  I-1 … I-7  (dois commits: um leve de tools/, um pesado de Go)
P-1    plano em docs/goal/ + commit
P0     CLAUDE.md com o teto correto (11.691) e as 14 regras
P1b    estancar as 942 + brotli + co-citação + temas sociais + pathspec de 10
P2/P1/P3   coleta: shfmt, quarentena do STJ, diários, órfãos   ║ concorrente com P4/P5
P4/P5  gates: régua, piso de ementa, fallback de itens, atribuição ║ concorrente com P2/P1/P3
P6-a   TRAVESSIA de 5 páginas  (antes do P4 — dominância, D1)
       ── P4/P5 aqui ──
P6-b   RECENSEIO pós-P4 → lote cheio → publicar → oneshot
P8     lei-artigo deixa de ser órfão, agravo vira agregado
P7     DataJud: barra final + controle negativo + mutação
P9     cérebro independente (portão de P12)
P10    tirar a máscara de exit
P12    migração para a GPU
```

### Por que cada posição

- **P-0.5 primeiro** porque são **três defeitos vivos agora**, cada um com gate vermelho medido, e o conserto
  de cada um é **um comando**: `check-social-temas-espelhados` **EXIT=1, 67 páginas** anunciando tema 404
  [M]; `legal_cocitation_index.jsonl` de **2026-09-11 03:08:12** contra `content/pages.json` de
  **2026-09-15 12:28:56** — **4 dias atrás da fonte** [M]; `check-brotli-static-fresco` **EXIT=1**, 1 `.br`
  mais velho que o fonte [M]. Nenhum depende de instrumento novo.
- **P-0.6 antes de P-1** porque o I-4 é o ANTES **e** o DEPOIS do P1b, e o I-1 é o ANTES **e** o DEPOIS de
  toda publicação dos cinco blocos. Instrumento que nasce depois do passo mede o mundo já mexido.
- **P0 antes de P1b** porque o gate do contrato é **incondicional no pre-commit** (`.githooks/pre-commit:283-286`)
  e **lê a worktree**: com a linha velha no disco depois de publicar, **todo commit de toda sessão reprova**.
- **P1b antes de tudo que publica** porque cada passada da onda recarimba `datePublished = hoje` (já foram
  quatro: 09-05, 09-08, 09-10, 09-15) e **não há rollback para trás** — a data errada já foi entregue ao
  buscador.
- **P2/P1/P3 concorrente com P4/P5**: tocam arquivos **disjuntos** (`tools/run-daily-content`,
  `internal/stjacordaos`, `internal/sourceresolve`, `internal/shellscriptquality` de um lado;
  `cmd/generate-acordao-pages`, `internal/cerebro` do outro). **Serializam só no commit**, pelo flock pesado.
- **P6-a (travessia) antes do P4** e **P6-b depois**: **D1**.
- **P9 antes de P12**: virar `LLM_LIBRARY=cpu → cuda_v12` com runner ruim produz a falha que a varredura
  provou — `worker.go:173-175` não dorme depois de lote falho e a saúde fica em cache 60 s ⇒ **34.217
  pendentes viram `erro` em ~30 min** [D]. Portão explícito: **B2 (com `Fila.Devolver`) + B3 no binário vivo
  e a prova C-b verde** — **C-b, não C-a**: o modo de falha do E3 é *"Ollama de pé, `generate` falhando"*, e
  `Saude.Verifica` só chama `Versao` e `Residentes`, os dois **200** nesse caso; C-a fica verde **antes** das
  correções e seria portão tautológico.

### O que pode rodar concorrente, e o que não pode

| pode | não pode |
|---|---|
| P2/P1/P3 ‖ P4/P5 (arquivos disjuntos) | **dois commits de Go ao mesmo tempo** — flock pesado |
| leitura/medição de qualquer bloco a qualquer hora | **qualquer coisa** durante uma transação `-allow-public-write` |
| construção dos I-1…I-7 ‖ P-0.5 | **editar `tools/run-daily-content`** fora do `flock -n 9 /tmp/wiki-daily-content.lock` |
| P8 depois do P6-b | **editar `tools/check-portal-health`** sem `py_compile` + harness (timer de 2 min o executa **do disco**) |

### Os seis pontos de serialização, com hora

1. **Flock pesado `/tmp/opt-wiki-agent-heavy.lock`** — **SEIS** units, não uma (**N2**). Regra:
   **pegar o lock ANTES do `git add`**, com espera do tamanho de quem o segura, e `add`+`commit` **dentro**
   dele:
   ```bash
   flock -w 5400 /tmp/opt-wiki-agent-heavy.lock bash -c 'cd /opt/wiki && git add <caminho exato> && git commit -F <msg> -- <os MESMOS caminhos>'
   ```
   `flock -w 600` (o que o GATES prescrevia) **desiste dentro da `qualidade-longa`** e deixa o índice sujo.
   `flock -w` **bloqueia sem spin** — `until` sem `sleep` é busy-wait de 82% de um núcleo, atrasando
   justamente o job esperado.
2. **Índice de git** — o `go-index-compile-closure` compila o **ÍNDICE**, não o pathspec (**77,6 s** sujo
   contra **14,9 s** limpo). Conferir `git diff --cached --name-only` **depois** de obter o lock, não só
   antes. **E o `git commit <pathspec>` não commita o índice: commita a árvore de trabalho** dos arquivos
   que casam — por isso o pathspec do commit é o **mesmo caminho exato** do `add`, nunca o diretório.
   **Proibido**: `git reset`, `restore`, `checkout --`, `stash`, `clean`, `revert` — barrados por
   `~/.claude/hooks/git-guard.sh` e pelo contrato. Índice sujo se resolve **corrigindo a causa e
   recommitando**, ou commitando por pathspec exato, que não passa pelo índice.
3. **`/tmp/wiki-daily-content.lock`** — a onda lê `tools/run-daily-content` **do disco no disparo**
   (04:31:33 e 12:20:55 -03). Editar segurando `flock -n 9`; tomado ⇒ **a onda está rodando: não editar**.
4. **`data/ops/.publish-v2-direct.lock`** — um publicador por vez. Lock presente ⇒ **conferir vida do PID**
   (`ls /proc/<pid>`) antes de qualquer coisa; `deploy-publico:463` o apaga **sem conferir** e abre janela
   para dois publicadores — **não imitar**.
5. **`wikijuridica-server-reload.path`** — parado durante toda transação (**D4**).
6. **`wikijuridica-watchdog.timer`, a cada 2 min** — executa `check-portal-health` **do disco**. O bloco
   DAEMON edita esse arquivo: a edição **é** o deploy.

### Pré-voo único, antes de qualquer bloco (< 5 s)

```bash
cd /opt/wiki
date '+%F %T %z'; date -u '+%FT%TZ'; cat /proc/loadavg
git status --porcelain go.mod go.sum; git diff --cached --name-only
git status --porcelain data/editorial/v2_pages data/editorial/portfolio_v2
systemctl list-timers 'wikijuridica-qualidade-*' 'wikijuridica-daily-content*' \
  'wikijuridica-noticias-coleta*' 'wikijuridica-official-source-url-inventory-refresh*' \
  'wikijuridica-stj-acordaos-coleta*' 'wikijuridica-sitemap-shard-grace*' --all --no-pager
systemctl show wikijuridica-server-reload.path -p ActiveState --value
./tools/sweep-sitemap-carencia-expirada --seco | tail -2
cat data/ops/.publish-v2-direct.lock 2>/dev/null || echo "sem lock de publicacao"
./tools/check-load-headroom --max 12; ./tools/check-coord-inbox --agent MODO-OPERACAO --last 15
```
**Esperado agora** [M]: go.mod/go.sum sem linha · índice vazio · `v2_pages`/`portfolio_v2` vazios ·
`.path` `active` · `0 vencido(s)` · sem lock · load1 4,90.
**Barreiras**: `go.mod` sujo ⇒ **PARE** (a atestação lê o **disco**; já atestou contra `go.mod` sujo 2× em
2026-09-08). `v2_pages` sujo ⇒ outra sessão gera; **nunca** `WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1`.

---

## §3 · OS RUNBOOKS

Formato de todo passo: **OBJETIVO / ANTES / AÇÃO / DEPOIS / SE NÃO VIER / ROLLBACK**. Emendas dos
refutadores estão **aplicadas no corpo do passo** e marcadas `[emenda: …]`; o texto do ataque não se
reproduz. Todo rollback é **para frente**.

### Proibições que valem em TODOS os passos

`--ressemear` no `deploy-publico` · `--tag` sozinho no `purge-edge-cache` · `--desde-commit` na mesma passada
do `--ressemear` · editar HTML/manifesto fora do `publish-v2-direct` · `git reset|checkout|restore|stash|clean|revert`
· `sudo nginx -t` · `cmd/check` sem argumento · padrão full-tree em Go · `--no-verify` · `pkill` de processo
alheio · baixar limiar de gate para passar · editar `internal/quality`, `internal/legalsignature` ou
**`internal/ptbrtext`** (**D8**) · `WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1` · `-skip-edge-purge` em publicação
real · aumentar timeout para "consertar" lentidão.

---

## RUNBOOK P-0.5 — OS TRÊS DEFEITOS VIVOS (não dependem de nada)

Três gates vermelhos **agora**, três comandos, e um deles tem bot de IA batendo no vazio **neste momento**.
Este runbook **não publica página nenhuma**: regenera derivados que a publicação por `publish-v2-direct`
nunca regenera.

**P05-1 · Semear os temas sociais que 67 páginas já anunciam**

- **OBJETIVO** parar de mandar crawler para 404 em `/redesocial/tema/…`.
- **ANTES** `./tools/check-social-temas-espelhados > /tmp/temas.txt 2>&1; echo "EXIT=$?"; head -4 /tmp/temas.txt`
  → **EXIT=1**, `67 pagina(s) publicadas anunciam um tema que devolve 404` [M].
  E o dano no log vivo: `LC_ALL=C grep -a 'redesocial/tema' /var/log/nginx/wikijuridica/access.log | grep -c ' 404 '`.
  **Único semeador no repositório** [M por grep em `tools/ ops/systemd/ .githooks/ cmd/publish-v2-direct/`]:
  `tools/deploy-publico:714`. **Publicar por `publish-v2-direct` nunca semeia** — é por isso que o defeito
  existe e por isso ele volta a cada publicação fora do `deploy-publico`.
- **AÇÃO** ensaio primeiro (sem `-aplicar` o comando **só ENSAIA**, conferido no `--help` [M]):
  ```bash
  ./tools/go-modern run ./cmd/generate-social-temas
  ./tools/go-modern run ./cmd/generate-social-temas --aplicar
  ```
- **DEPOIS** `./tools/check-social-temas-espelhados; echo "EXIT=$?"` → **0**, `FALTANDO tema: 0` [A MEDIR].
  Amostra ao vivo de 3 dos 67: `curl -sS -o /dev/null -w '%{http_code}\n' -A "$UA_SONDA" -H 'X-Warming-Request: true' https://wikijuridica.com.br/redesocial/tema/diarios/sp-20260912/` → **200**.
- **SE NÃO VIER** ainda 404 com o gate verde ⇒ é a **borda** servindo o 404 cacheado: purgar **aquelas URLs**
  com `--de-arquivo` e `--teto-por-url` igual ao tamanho da lista. Gate ainda 1 ⇒ leia a lista: se as rotas
  mudaram, o manifesto avançou entre o ensaio e o `--aplicar`.
- **ROLLBACK** nenhum — o comando **não remove nada**, órfãos são só relatados (está escrito na própria
  saída do gate [M]).

**P05-2 · Tirar o índice de co-citação dos 4 dias de atraso**

- **OBJETIVO** devolver a seção `## Percursos por fundamento legal` — a de maior densidade do canal de
  máquina, **76,7% de links cross-área** contra 11,4% da malha do HTML — ao estado da fonte.
- **ANTES** `ls -la --time-style=+%F_%T content/legal_cocitation_index.jsonl content/pages.json`
  → índice **2026-09-11_03:08:12**, `pages.json` **2026-09-15_12:28:56** [M]: **4 dias atrás da fonte**.
  E o ponto cego: `./tools/check-percursos-fundamento-legal` sai **0** — ele mede **densidade, não frescor**.
- **AÇÃO** `./tools/go-modern run ./cmd/generate-legal-cocitation` (o passo 2.6 do `deploy-publico:678`;
  custo ~16 s ociosa, ~29 s sob carga).
- **DEPOIS** mtime do índice **> mtime de `pages.json`** ; `./tools/check-percursos-fundamento-legal` → 0 com
  `paginas` e `links` **acima** do baseline (hoje `paginas=5815 links=31102`, 78,1% cross-área).
  **E o índice é lido UMA vez no BOOT** — ele só chega às quatro superfícies depois de
  `./tools/reload-wiki-server`.
- **SE NÃO VIER** índice **encolhendo** ⇒ `pages.json` está parcial (outra frente publicando): **não
  commite**, releia depois. Erro de boot do Go depois do reload ⇒ artefato **corrompido** (o desenho é
  falhar no boot, nunca meio índice em silêncio): regenere antes de reiniciar de novo.
- **ROLLBACK** para frente — artefato ausente ⇒ **nenhuma seção**, canal como era (degradação honesta por
  desenho); regenerar de novo.

**P05-3 · Fechar o `.br` já vermelho**

- **OBJETIVO** que o corpo que o nginx entrega a quem pede `Accept-Encoding: br` — **inclusive à
  Cloudflare, que o distribui** — seja o corpo atual.
- **ANTES** `./tools/check-brotli-static-fresco > /tmp/br.txt 2>&1; echo "EXIT=$?"; head -3 /tmp/br.txt`
  → **EXIT=1**, `11455 arquivo(s) .br | frescos: 11454 | stale: 1 | orfaos: 0`, cobertura **100,0%** [M].
- **AÇÃO** `nice -n 19 ./tools/generate-brotli-static --jobs 4 2>&1 | tail -3` (passo 2.5 do
  `deploy-publico:646`).
- **DEPOIS** `./tools/check-brotli-static-fresco; echo "EXIT=$?"` → **0**, `stale: 0`.
  Prova ao vivo, que é a que importa: `curl -sS -H 'Accept-Encoding: br' -A "$UA_SONDA" -H 'X-Warming-Request: true' -D - -o /dev/null http://127.0.0.1:8088/jurisprudencia/stf-adi-4376/ | grep -i content-encoding`
  → `br`, e o tamanho **menor** que o `identity` (medido numa rota: 25.422 B `identity` contra 6.731 B `br`).
- **SE NÃO VIER** `stale` subindo ⇒ outra frente reescreveu HTML durante a passada; re-rode. **Atenuação
  medida, declarada para ninguém tratar como eterno**: `wikijuridica-brotli-cobertura.timer` é **horário**
  (`RandomizedDelaySec=5min`, próxima 23:01:13 -03 [M]) e roda `repair-brotli-cobertura` ⇒ a janela de
  falso-verde é de **≤65 min**, não infinita. Isso **não** dispensa o passo: o `curl` de verificação do P1b,
  **sem `--compressed`**, lê o `identity` e passa **verde** enquanto o bot recebe o corpo antigo.
- **ROLLBACK** para frente; `.br` mais novo que o fonte nunca é servido errado.

**P05-4 · Commitar (leve, sem Go no índice)**

- **ANTES** `git diff --cached --name-only | wc -l` → **0** [M].
- **AÇÃO** `git add content/legal_cocitation_index.jsonl` ; depois
  `git commit -F /tmp/msg-p05.txt -- content/legal_cocitation_index.jsonl`.
  `public/**.br` **não entra**: `public/` é gitignored (`.gitignore:3:/public/` [M]). O banco social
  (`var/social/social.db`) também não é produto de commit — é estado de runtime.
- **DEPOIS** `git log -1 --stat --format='%H %s' | head -4` → 1 arquivo.
- **SE NÃO VIER** reprovação na closure com índice sem Go ⇒ índice sujo de outra sessão; pathspec exato
  resolve (`git commit -F msg -- <path>` não passa pelo índice). **Nunca `--no-verify`.**
- **ROLLBACK** commit é checkpoint; correção é commit novo.

---

## RUNBOOK P-1 / P0 / P1b — GRAVAR O CONTRATO E ESTANCAR O DADO CORROMPIDO SERVIDO

**P1b-0 · Pré-condições, todas leitura (segundos)**

| # | comando | esperado |
|---|---|---|
| PC-1 | `./tools/sweep-sitemap-carencia-expirada --seco \| tail -2` | `0 vencido(s)` [M]. **Publicar NÃO renova** (**N3**): é **restrição**, não espera — nenhum reinício do Go entre **07:50Z** e a varredura. |
| PC-2 | `git diff --cached --name-only \| wc -l` | **0** [M] |
| PC-3 | `systemctl show wikijuridica-server-reload.path -p ActiveState --value` | `active` [M] ⇒ o passo 8 **para** essa `.path` (**D4**) |
| PC-4 | `systemctl list-timers 'wikijuridica-qualidade-*' --all --no-pager` | fora de 02:11–02:46 e 04:47–05:50 -03 (**N2**) |
| PC-5 | `cat /proc/loadavg` | < 12 (`saude.go:89` pausa o cérebro acima) |
| PC-6 | `cat data/ops/.publish-v2-direct.lock 2>/dev/null` | ausente; presente ⇒ `ls /proc/<pid>` **antes** de qualquer coisa |

**P1b-1 · Gravar o plano (ação número 1)**

- **OBJETIVO** o plano no repositório, versionável, commitado na mesma sessão.
- **ANTES** `ls docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` → inexistente [M].
- **AÇÃO** escrever o `.md`; `git add docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`;
  `git commit -F /tmp/msg-p-1.txt -- docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`
  (comandos **separados**; `-F` sempre; **nunca** capturar a saída do hook no mesmo arquivo do `-F`, que a
  sobrescreve e é irreversível).
- **DEPOIS** `git log -1 --stat` → 1 arquivo em `docs/goal/` ; `./tools/check-contrato-vs-medicao; echo "EXIT=$?"` → **0**.
- **SE NÃO VIER** reprovação em `check-contrato-vs-medicao` ⇒ o texto tem **frase-zero** (`publicação zero`,
  `publicacao zero`, `nenhuma página jurídica pública` — as três literais em `FRASES_ZERO` [M]): marcar a
  linha como histórica com marca que `_e_registro_historico` reconhece (`afirmou`, `trazia ate`, `ate 2026-`,
  `foi superada`, `regra antiga`, linha iniciada por `>`). Custo do pre-commit com índice limpo: ~15–20 s [D].
- **ROLLBACK** nenhum gate varre `docs/goal/*.md`; se preciso, editar para frente.

**P1b-2 · A linha do contrato, com o teto certo**

- **OBJETIVO** declarar 11.106 e comprar as **70** páginas de margem (**D2**), sem quebrar o casamento do regex.
- **ANTES** `grep -n "Estado atual" CLAUDE.md` → linha **128**, `11.039` [M] ;
  `./tools/check-contrato-vs-medicao` → `11106 linhas, 11106 unique_intent_id` / `declara 11039` / **EXIT=0** [M].
- **AÇÃO** **edição pontual**, só número e data:
  `- **Estado atual (medido em 2026-09-15): 11.106 páginas públicas no ar**,`
  **NÃO reformatar a linha**: o regex é
  `r"Estado atual[^:]*:\s*\*{0,2}([\d.  ]+)\s*páginas? públicas?"` [M] — com acento, e `\*{0,2}` só cobre o
  `**` à esquerda. Perder o casamento cai em *"não declara volume em forma verificável"* e **reprova todo
  commit de toda sessão**. Acrescentar as regras novas (lista no fim deste runbook). Parágrafo superado ganha
  data e motivo; **não se apaga**.
- **DEPOIS** `./tools/check-contrato-vs-medicao` → `declara 11106` / **EXIT=0**. Mexeu na **§10** ⇒
  `./tools/go-modern test -count=1 ./internal/contract/misc/ -run TestPeerGovernance` (BUG-171).
  Então `git add CLAUDE.md` ; `git commit -F /tmp/msg-p0.txt -- CLAUDE.md`.
- **SE NÃO VIER** *"não declara volume em forma verificável"* ⇒ o regex parou de casar: restaurar a forma
  literal, editando **para frente**. `CONTRATOS_EXTRA` também varre `GOAL.md` e `AGENTS.md` — reprovação
  **lá não é deste bloco**: registre em `docs/goal/MAESTRO_CODEX_LOG.md` e **não toque**.
- **ROLLBACK** uma linha, para frente; o gate mede o disco em < 1 s.

> **As regras novas do P0** — cada uma custou uma correção nesta sessão, e cada uma tem o número ao lado:
> (1) `datePublished` é **neutralizado** pelo hash de revisão ⇒ correção de data **não gera lista de purga**;
> a lista vem do diff cru do manifesto (I-3). (2) o ramo `dd/mm/aaaa` de `neutraliza_datas` apaga data de
> **PROVENIÊNCIA** quando ela passa a coincidir com o ISO do documento — **60 rotas medidas** ⇒ correção de
> data roda com `--ressemear`. (3) `dateModified` **não** é `reviewed_at` (`content.go:444-460` começa em
> `ContentRevisedAt`). (4) `datePublished > reviewed_at` é **normal**; o impossível é `> dateModified`.
> (5) `check-lastmod-causalidade` **não pega** data-only (EXIT=0 com 942 impossíveis no ar). (6)
> `purge-edge-cache --tag` sem `--url` dá **NameError no caminho de sucesso**, e lista acima do teto **sem**
> tag dá **purga total silenciosa com exit 0** (**D7**). (7) `Last-Modified` é a data **editorial**
> (`gravaDatado`) e **não muda** ⇒ prova por **corpo**, nunca por cabeçalho. (8) carência de shard **trava o
> BOOT**, e **publicar não a renova** (**N3**). (9) `publish-v2-direct` **não** semeia tema social, **não**
> regenera co-citação e **não** recomprime brotli ⇒ quem publica fora do `deploy-publico` roda os três
> (P-0.5). (10) o `ETag` da gêmea é o `sha256[:32]` ⇒ paridade por `HEAD` (**N1**). (11) a folga do contrato
> sai do número **medido**: teto 11.621/11.691 (**D2**). (12) **seis** units tomam o flock pesado (**N2**).
> (13) `check-onda-avanca --rotulo` **não** namespaceia o baseline (I-7). (14) `git commit <pathspec>`
> commita a **árvore de trabalho**, não o índice ⇒ pathspec = caminho exato do `add`.

**P1b-3 · Commitar o `published_manifest.jsonl` que há 5 dias não é commitado**

- **OBJETIVO** dar âncora de estreia às rotas — é **daqui** que `generate-first-published-at` deriva a data.
- **ANTES** `git log -1 --format='%h %ad' --date=short -- data/editorial/published_manifest.jsonl`
  → `315ac61b 2026-09-10` (5 dias) ; `git diff --numstat HEAD -- data/editorial/published_manifest.jsonl`
  → `10946 10879`.
- **AÇÃO** o pathspec são **10 arquivos**, medidos em `git show --name-only 315ac61b`
  [emenda: o refutador do PUBLICAR mediu 7 e o crítico mediu 10 — **vale 10**, e os dois que faltavam nos
  dois runbooks são os recibos de transação]:
  ```bash
  git add data/editorial/published_manifest.jsonl content/pages.json content/legal_cocitation_index.jsonl \
          data/editorial/stock_manifest.json data/editorial/authorial_mass_drafts.jsonl \
          data/ops/page_content_revision.jsonl data/ops/page_content_revision_formula.txt \
          data/ops/edge_cache_purge.jsonl data/ops/edge_cache_warm.jsonl \
          data/ops/v2_ingest_transaction_receipt.json
  git commit -F /tmp/msg-manifesto.txt -- <os MESMOS 10 caminhos>
  ```
  Os `data/ops/v2_ingest_terminal_receipts/<id>.terminal.json` **untracked** entram no mesmo commit
  (produto não fica untracked); `data/ops/v2_ingest_transaction_receipt.json` é lido por
  `internal/v2readguard/guard.go:35`.
- **DEPOIS** `git diff --numstat HEAD -- data/editorial/published_manifest.jsonl` → **vazio** ;
  `./tools/check-untracked-product-inventory; echo "EXIT=$?"` → 0.
- **SE NÃO VIER** `check-produto-nao-some-do-worktree` reclamando ⇒ é outra frente com produto untracked:
  **não deletar nada** — classificar no `.gitignore` se for ruído, ou commitar o produto da frente que o
  gerou. **Baseline a datar antes deste commit** [M]: `authorial_mass_drafts.jsonl` mtime
  **2026-09-10 23:41** contra `authorial_mass_publication_readiness.jsonl` **2026-08-05 19:38** — saída
  **36 dias mais velha que a entrada**, que é a forma exata que `readiness.go:1060` emite. **Não é deste
  bloco**: datar como vermelho conhecido, senão o bloco herda a culpa. **E não "regenerar a cadeia"** — os
  13 elos são `authorial_mass_*` e os 5 detectores `older_than` **não leem `v2_pages`**; a rota certa é
  `ops/relaunch-writing.sh`, e confundir as duas é o erro dos **31 dias**.
- **ROLLBACK** nenhum — commit é checkpoint.

**P1b-4 · Preservar o que não se recupera depois (antes de gerar nada)**

- **OBJETIVO** ter o ledger e a fórmula **de antes**, porque depois de um `--ressemear` os seletores
  `--dia`/`--desde-horas` de `check-edge-frescor` ficam **verdes sobre o conjunto errado** e só
  `--desde-ledger` enxerga — e ele exige este snapshot.
  [emenda: este passo veio **antes** do gerador de estreia, que o ESTANCAR punha depois — lá a "preservação"
  copiava o estado **novo**.]
- **ANTES** `sha256sum data/ops/page_content_revision_formula.txt` ; `wc -l data/ops/page_content_revision.jsonl` → **11.116**.
- **AÇÃO**
  ```bash
  D=.agents/runtime/p1b-20260915 && mkdir -p "$D"
  cp -a data/ops/page_content_revision.jsonl "$D"/page_content_revision.antes.jsonl
  cp -a data/ops/page_content_revision_formula.txt "$D"/formula.antes.txt
  cp -a data/editorial/first_published_at.json "$D"/first_published_at.antes.json
  git show HEAD:data/editorial/published_manifest.jsonl > "$D"/manifesto.antes.jsonl
  ./tools/check-cronologia-jsonld --json > "$D"/cronologia.antes.json
  ```
- **DEPOIS** `cat "$D"/formula.antes.txt` → `29055289b861d603f90fccfe78ea6db1f1e010cb8e8c2a5c8520b64445f5eac0`.
- **SE NÃO VIER** fórmula **divergente** ⇒ outra frente editou `neutraliza_datas`/`BLOCOS_DE_NAVEGACAO`.
  **PARE**: o `--ressemear` do passo 12 absorveria **duas** mudanças de fórmula e o DEPOIS deixa de ser
  atribuível. Rode `./tools/generate-page-content-revision --dry-run` e leia o **RECUSADO**.
  Rota de recuperação real, que é leitura e não reversão: `git show HEAD:data/editorial/first_published_at.json`
  (o arquivo está **limpo** em HEAD).
- **ROLLBACK** n/a — é snapshot.

**P1b-5 · Reconstruir a estreia com a regra das órfãs**

- **OBJETIVO** que `datePublished` deixe de cair no fallback `hoje`, **sem** carimbar estreia falsa em
  página nenhuma.
- **ANTES** `python3 -c "import json;d=json.load(open('data/editorial/first_published_at.json'));fp=d.get('first_published_at',d);print(len(fp),max(fp.values()))"`
  → **10.107 · 2026-08-27** [M] ; flags reais hoje: só `--saida` e `--dry-run` [M].
  Cadeia causal fechada: arquivo órfão desde 08-28 ⇒ as 944 sem entrada ⇒ `loadFirstPublished`
  (`main.go:3575-3591`) não cobre ⇒ `PublicationDate` vazio (`:500-507`) ⇒
  `ApprovedAt = primeiroNaoVazio(page.PublicationDate, opts.publishedAt)` (`:3837`) cai no fallback ⇒ a onda
  chama `-published-at "$HOJE"` (`run-daily-content:685`) e o default já é hoje (`:182`).
- **AÇÃO** implementar a regra da **D3** como **padrão** (sem flag), com `intents_no_commit` rendendo
  `(uid, path)` — hoje ele descarta o `path` e o piso precisa dele
  [emenda: o refutador mostrou que o patch original supunha um dado que o gerador joga fora].
  Regra escrita para HTML ausente: cai em `estreia_git`, ou em `approved_at` nas órfãs; **NUNCA em hoje**.
  Teste de nascença com fixture de rota supersedida **sem** HTML. Então:
  `./tools/generate-first-published-at --dry-run` e, conferido, sem a flag.
- **DEPOIS** `commits percorridos: 50` · `intents ja conhecidos: 10107` · `intents com data recuperada: 11106`.
  **O invariante, não a magnitude** [emenda: o "900 de 944" do ESTANCAR era a contagem de rotas **que têm**
  estreia, rotulada como impossíveis; o número certo da regra pura é **44 de 944**]:
  ```bash
  ./tools/check-cronologia-jsonld --json | python3 -c 'import sys,json;d=json.load(sys.stdin);print("estreia > dateModified:",d.get("estreia_acima_do_modificado","A MEDIR"))'
  ```
  → **0**. E `dia1 == 2` (as duas legítimas de `/noticias/` com `reviewed_at == approved_at == 2026-09-15`).
  Então `git add data/editorial/first_published_at.json` ; `git commit -F /tmp/msg-estreia.txt -- data/editorial/first_published_at.json`.
- **SE NÃO VIER** recuperadas < 11.106 ⇒ o passo 3 não entrou. **Qualquer** rota com estreia **maior** que o
  `dateModified` dela ⇒ o piso não foi aplicado: **pare e corrija o gerador** — publicar aqui carimbaria o
  erro de novo, e `setdefault` o torna **permanente**. `dia1 > 2` ⇒ a regra genérica de `min` voltou;
  use `approved_at` **só nas órfãs**.
- **ROLLBACK** `"$D"/first_published_at.antes.json` e `git show HEAD:…`; restauração por **cópia para
  frente**, nunca `git checkout`.

**P1b-6 · Ensaio da publicação, sem escrever um byte**

- **OBJETIVO** ler a linha que decide, antes de mutar.
- **ANTES** `cat data/ops/.publish-v2-direct.lock 2>/dev/null` → ausente.
- **AÇÃO** o ensaio é o **mesmo caminho** sem `-allow-public-write` (renderiza e compara; sem lock, sem
  snapshot, sem uma syscall de escrita):
  ```bash
  ./tools/go-modern run ./cmd/publish-v2-direct -published-at 2026-09-15 -reviewed-at 2026-09-15 2>&1 | tail -40
  echo "EXIT=${PIPESTATUS[0]}"
  ```
- **DEPOIS** a linha que decide: `data de estreia       : 11106 de 11106 páginas`.
  **E leia de graça o veredito do registry de shard** — `conciliaRegistryDeShard` roda
  **independentemente** de `-allow-public-write`: a saída já diz `registry de shard: N aposentada(s)` ou
  devolve o **RECUSADO** por churn. Teto medido: `max(6, assigned/4)` com `assigned=63` ⇒ **15**.
- **SE NÃO VIER** `indisponivel (...)` ⇒ `loadFirstPublished` não leu o arquivo. `N de 11106` com N<11106 ⇒
  faltam entradas: volte ao passo 5; **seguir aqui carimbaria hoje nas que faltam**. Lock presente ⇒
  **confira vida do PID** antes de remover.
- **ROLLBACK** n/a — nada escrito.

**P1b-7 · Publicar (a única rota que não quebra o boot)**

- **OBJETIVO** reescrever os 942 HTML **com os hashes recalculados no mesmo registro**.
- **ANTES** `./tools/check-cronologia-jsonld; echo "EXIT=$?"` → **1, 942** [M×2] ;
  `systemctl show wikijuridica-server -p ActiveState -p NRestarts -p ExecMainStatus` → active/0/0 ;
  **e as duas linhas da D4**:
  ```bash
  sudo -n systemctl stop wikijuridica-server-reload.path
  systemctl show wikijuridica-server-reload.path -p ActiveState --value   # inactive
  ```
- **AÇÃO**
  ```bash
  nice -n 10 ./tools/go-modern run ./cmd/publish-v2-direct \
    -published-at 2026-09-15 -reviewed-at 2026-09-15 -allow-public-write 2>&1 | tee /tmp/p1b-publica.log
  echo "EXIT=${PIPESTATUS[0]}"
  ```
  **Sem `timeout`** [emenda: o `timeout 1800` do ESTANCAR manda SIGTERM numa transação **sem
  `signal.Notify`** — `grep -rn 'signal.Notify' cmd/publish-v2-direct/ internal/publicrelease/ cmd/build/`
  devolve **zero linhas** — então os defers não rodam, o lock fica órfão e `public/`+sitemap ficam parciais,
  que `writeRollbackSnapshot` (3 arquivos) **não cobre**. O teto da unit, único, basta e é observável.]
  **O que este passo faz sozinho, e o runbook original não dizia**: recompressão brotli (`:2192`), **purga de
  borda por tag/URL** (`:2229`) e recarga do servidor (`:2257`). A purga interna promove a **área inteira** a
  `--tag` quando ≥30 rotas mudam (`limiarDeTag=30`): `area-jurisprudencia` (1.134 no manifesto, 875 mudam) e
  `area-leis` (406, 38 mudam) ⇒ **1.540 objetos** purgados quando 913 bastariam, e **627 páginas ficam frias**
  e **não** estão na lista de alvos. **Elas entram no aquecimento do passo 12.**
  **POR QUE NÃO EDITAR HTML/MANIFESTO À MÃO:** `:3837-3849` grava `ApprovedAt`, `HTMLSHA256` e
  `SitemapSHA256` no **mesmo** registro. 942 HTML reescritos sem recalcular o hash = 942
  `published_manifest_html_sha256_mismatch`, contra limiares de boot de **10 por código e 25 no total**
  (`publishedmanifest.go:1464-1470`) ⇒ **o Go não sobe**: morrem gêmea, `/api/v1/*`, MCP, A2A e descritores; o
  acervo estático **continua no ar** e `check-portal-health` (só `127.0.0.1`) passa **VERDE**.
- **DEPOIS** `./tools/check-cronologia-jsonld; echo "EXIT=$?"` → **0** ; contagem de `approved_at` por dia →
  **2026-09-15 cai de 944 para 2** [M×2 do ANTES; o DEPOIS é A MEDIR].
- **SE NÃO VIER** exit ≠ 0 ⇒ **NÃO RECARREGUE O SERVIDOR.** A transação escreve `sitemap.xml` em `:1128` e o
  manifesto em `:2120`; interrompida, fica `sitemap_loc_without_manifest`, que **aborta o boot** com
  `Restart=always` e `StartLimitIntervalUSec=0` ⇒ laço de 5 s eterno, a unit **nunca** entra em `failed` e
  `OnFailure` é **vazio**: ninguém é avisado. Leia o log, corrija a causa, republique.
  **RECUSADO por churn de shard** ⇒ o acervo **já está no disco**: não é rollback, é fatiar a próxima
  mudança de corpo pelo teto de 15 — e **nunca** `--permitir-churn-de-shard`.
- **ROLLBACK** **não existe para trás, e é honesto dizer**: a data errada já foi entregue ao buscador em
  quatro passadas. `writeRollbackSnapshot` (`:3988-4058`) cobre **3 arquivos** e **não** cobre `public/` nem
  `public/sitemaps/`. A recuperação é **republicar para frente**.

**P1b-8 · Os três derivados que a publicação não regenera, e só então reiniciar**

- **OBJETIVO** que o reinício encontre os derivados no estado da fonte — porque **três deles são lidos uma
  vez, no boot**.
  [emenda: o refutador do PUBLICAR e o crítico convergiram — `publish-v2-direct` **não** semeia tema social,
  **não** regenera co-citação e **não** recomprime `.br`; o P1b reescreve 942 HTML e o ESTANCAR não rodava
  nenhum dos três.]
- **ANTES** `./tools/reload-wiki-server --check; echo "EXIT=$?"` → **1** esperado (acabamos de publicar;
  **exit 0 aqui seria o sinal de que a publicação não escreveu nada**). **Amostra do detector: 6 rotas de
  11.106** [M, `:268 "amostradas"`] — declarado, para ninguém ler 6/11.106 como convergência.
- **AÇÃO**, nesta ordem:
  ```bash
  nice -n 19 ./tools/generate-brotli-static --jobs 4 2>&1 | tail -3
  ./tools/go-modern run ./cmd/generate-legal-cocitation
  ./tools/go-modern run ./cmd/generate-social-temas --aplicar
  ./tools/sweep-sitemap-carencia-expirada --seco | tail -2      # exige "0 vencido(s)"
  ./tools/reload-wiki-server
  sudo -n systemctl start wikijuridica-server-reload.path       # fecha a D4
  ```
  `reload-wiki-server` é **idempotente e auto-verificável**: mede a divergência pedindo o markdown de uma
  rota do manifesto, **só reinicia se houver divergência** (reiniciar à toa derruba a busca e zera o índice
  quente), verifica depois pelo mesmo predicado e grava `data/ops/server_reload.jsonl`. Boots medidos em
  2026-09-15: **32 s** e **23 s**; teto do script **90 s**.
- **DEPOIS** `systemctl show wikijuridica-server -p ActiveState -p SubState -p ExecMainStatus` →
  active/running/0 ; `./tools/reload-wiki-server --check` → 0 ; `./tools/check-brotli-static-fresco` → 0 ;
  `./tools/check-social-temas-espelhados` → 0 ; `./tools/check-percursos-fundamento-legal` → 0 ;
  `tail -1 data/ops/server_reload.jsonl`.
- **SE NÃO VIER** `/api/v1/citar` devolve **404** para rota que está no disco ⇒ **não é "não publicou", é Go
  desatualizado**: reiniciar **pela cadeia**, NÃO republicar, NÃO purgar. **Gêmea velha com HTML certo ⇒
  cache de ORIGEM, e restart não conserta**: `./tools/purge-origin-cache` [emenda: o `SE NÃO VIER` original
  mandava reiniciar, e o modo de falha realmente observado hoje é origem suja]. Unit em laço ⇒
  `journalctl -u wikijuridica-server --since "-5min"`; o laço é **mudo**, confira
  `sitemap_loc_without_manifest` e a carência.
- **ROLLBACK** para frente. **Nunca `systemctl stop`** de oneshot em execução (marca `failed` e dispara
  alerta falso ao dono).

**P1b-9 · Purgar origem → borda, com a lista que `--purge-targets` não sabe montar**

- **OBJETIVO** que o corpo servido seja o novo, em **todas** as serializações — e que a verificação seja
  imediata, não uma espera de 7 dias.
- **ANTES** `./tools/generate-page-content-revision --purge-targets | wc -l` → 0 ou pouquíssimas, **e isso
  NÃO é "nada a purgar"**: é o hash cego à data. `tail -2 data/ops/edge_cache_purge.jsonl` — se a última
  linha trouxer `scope` "tudo" recente, **não purgue de novo** (joga fora ~870 s de aquecimento).
- **AÇÃO**
  ```bash
  ./tools/generate-alvos-por-manifesto --base HEAD~1 > /tmp/p1b-alvos.txt
  test -s /tmp/p1b-alvos.txt || { echo "lista VAZIA — ABORTE"; exit 2; }
  wc -l /tmp/p1b-alvos.txt                       # 1.884 esperado [D: 942 HTML + 942 index.md]
  # ORIGEM primeiro — a borda repopula DA ORIGEM
  ./tools/purge-origin-cache --de-arquivo /tmp/p1b-alvos.txt --seco
  ./tools/purge-origin-cache --de-arquivo /tmp/p1b-alvos.txt
  nice -n 19 ./tools/warm-origin-cache --rps 80 --concorrencia 8 | tail -3
  # BORDA depois, fatiada em <=100 (LOTE=100; 19 lotes gravam UMA linha de ledger)
  split -l 100 -d /tmp/p1b-alvos.txt /tmp/p1b-alvos-
  for f in /tmp/p1b-alvos-*; do
    N=$(wc -l < "$f")
    ./tools/purge-edge-cache --de-arquivo "$f" --teto-por-url $((N+1)) --dry-run | grep -q 'URL(s) em' || exit 2
    ./tools/purge-edge-cache --de-arquivo "$f" --teto-por-url $((N+1)); echo "$f exit=$?"
  done
  ```
  [emenda: fatiar em ≤100 é do refutador — `LOTE=100`, o laço **sobrescreve `status`** e grava **uma** linha
  de ledger com o `http_status` do **último** lote; uma falha no 19º devolve exit 1 com 18 lotes **já
  purgados** e o ledger não diz quais.]
  **Três armadilhas, todas ativas aqui:** `--teto-por-url` ≥ tamanho da lista (acima do teto, default 3000,
  degrada **em silêncio** para `purge_everything`, **exit 0**); **nunca `--tag` sozinho** (NameError no
  caminho de sucesso); **origem antes de borda** — invertido, o Tiered Cache promove o **VELHO** (medido
  2026-09-05: `age 0`, `HIT`, `campos=0`, 5×; com a ordem certa `campos=3` de primeira).
- **DEPOIS** a **prova é por CORPO** (e eu medi por quê): `Last-Modified` servido é
  `Sat, 05 Sep 2026 00:00:00 GMT` — a data **editorial**, carimbada por `gravaDatado` — e **não muda**;
  com `If-Modified-Since` da data atual a origem devolve **304**, sem o cabeçalho **200 / 20.584 bytes** [M].
  ```bash
  curl -sS -A "$UA_SONDA" -H 'X-Warming-Request: true' -D /tmp/h.txt https://wikijuridica.com.br/jurisprudencia/stf-adi-4376/ | grep -o '"datePublished":"[^"]*"'
  grep -iE 'cf-cache-status|^age' /tmp/h.txt
  ```
  → `MISS` (ou `EXPIRED`) e `"datePublished":"2026-09-10"`. Gêmea, **por `HEAD` e ETag** (**N1**):
  `etag` da borda == `markdown_sha256[:32]` de `/api/v1/citar` em `:8089`.
  **Origem também por CORPO**, não por cabeçalho [emenda: `127.0.0.1:8088` **não emite** `X-Cache` nem
  `Age` [M] — o `grep` original voltava **vazio** e ausência de sinal seria lida como sucesso]: comparar
  `date_published` de `:8088` com o de `:8089` e com o disco.
- **SE NÃO VIER** `HIT` com `age` alto ⇒ a purga não alcançou: leia `tail -1 data/ops/edge_cache_purge.jsonl`
  (`success`, `http_status`, `scope`) e **repurgue só o que faltou**, nunca a lista inteira. `MISS` com
  `datePublished` antigo ⇒ a **origem** ainda serve o velho. **Não repita purga em laço**: purga repetida
  contra defeito que não é de cache já esconde causa por dias.
- **ROLLBACK** purga não tem e não precisa; o pior efeito é borda fria, que o aquecimento desfaz.
  **Nunca purgue "tudo" para consertar purga dirigida.**

**P1b-10 · Reassentar o ledger (ROTA B) e reaquecer, incluindo as 627 colaterais**

- **OBJETIVO** não fabricar frescor em página cujo texto não mudou, e não deixar a borda fria.
- **ANTES** `./tools/generate-page-content-revision --dry-run 2>&1 | tail -20` → acusaria ~**60** rotas
  "mudadas", **todas por data, nenhuma por texto**.
  **A decisão, com o critério medido:** ROTA B (`--ressemear`) redata **0**; ROTA A redata **60**
  (0,54% de 11.106) — e o gate **não pegaria** (`check-lastmod-causalidade:289-293` aceita `served` mudado
  como causa legítima), o que é exatamente por que tem de ficar escrito. **Custo do `--ressemear` hoje = 0**:
  ele rebaixa instante para dia só quando o mesmo instante se repete em ≥ `LOTE_MINIMO=50`, e o mais
  repetido no ledger é `2026-09-12T15:26:42Z` com **47**.
- **AÇÃO**
  ```bash
  ./tools/generate-page-content-revision --ressemear
  # as 627 colaterais que a purga interna do passo 7 esfriou e NAO estao em /tmp/p1b-alvos.txt
  python3 - > /tmp/p1b-warm.txt <<'PY'
  import json
  vis=set(open('/tmp/p1b-alvos.txt').read().split())
  for ln in open('data/editorial/published_manifest.jsonl',encoding='utf-8'):
      try: d=json.loads(ln)
      except: continue
      p=d.get('path') or ''
      if p.startswith(('/jurisprudencia/','/leis/')) and p not in vis: print(p)
  PY
  wc -l /tmp/p1b-warm.txt        # ~627 esperado [D: (1134-875)+(406-38)]
  ./tools/warm-edge-cache --de-arquivo /tmp/p1b-alvos.txt --rps 12 --concorrencia 4
  ./tools/warm-edge-cache --de-arquivo /tmp/p1b-warm.txt  --rps 12 --concorrencia 4
  ```
- **DEPOIS** `./tools/check-lastmod-causalidade --json` → `datas_fabricadas_hash_igual_data_avancou = 0` e
  `sitemap_divergente_do_ledger = 0` ; contagem de `revised_on == 2026-09-15` no ledger → **o mesmo valor
  de antes do passo 7**. `wc -l data/ops/page_content_revision.jsonl` → **11.118**, não 11.116
  [emenda: são as **2** notícias de hoje que ainda não tinham entrada — **esperado, não defeito**].
- **SE NÃO VIER** `RECUSADO: a formula do served_sha256 mudou…` ⇒ outra frente editou o produtor entre o
  passo 4 e agora: **pare e reconcilie**. `--ressemear` indisponível ⇒ **ROTA A**: rodar normal, aceitar as
  **60** re-datações, **declará-las no commit com a lista**, e purgar+reaquecer também essas 60 (aí sim
  entram em `--purge-targets`).
- **ROLLBACK** ledger e fórmula anteriores em `.agents/runtime/p1b-20260915/`; restauração por **cópia para
  frente**.

**P1b-11 · Commitar e fechar**

- **AÇÃO** `git add` dos 10 caminhos exatos (passo 3) ;
  `git commit -F /tmp/msg-p1b.txt -- <os MESMOS 10>`.
  > **`public/` NÃO é rastreado** [M]: `git check-ignore -v` devolve `.gitignore:3:/public/`. O HTML servido
  > não entra em commit nenhum: a coerência git/disco é garantida **só** pelo `html_sha256` do manifesto —
  > que é exatamente por que o passo 7 tem de passar pelo `publish-v2-direct`.
- **DEPOIS** `./tools/check-cronologia-jsonld` → 0 · `./tools/check-contrato-vs-medicao` → 0 ·
  `./tools/check-v2-portfolio-pairing` (3,45 s) → 0 · `./tools/check-csp-style-hashes` (orçamento 20 s) ·
  `./tools/check-publicado-no-ar --de-arquivo <amostra por stride de 100 das 942>` → **0**.
- **SE NÃO VIER** `check-csp-style-hashes` vermelho logo após publicar é **esperado** enquanto `public/` não
  republicou a folha — avisa que falta deploy, não é defeito. Persistindo, comparar **byte a byte**
  `ops/nginx/security-headers.conf:52` com `render.StylesheetPath()`: divergiu ⇒ **nenhuma página tem
  estilo**, com 200 em tudo e todos os gates de conteúdo verdes.
- **ROLLBACK** para frente.

---

## RUNBOOK P2 / P1 / P3 — COLETA

Concorrente com o bloco GATES (arquivos disjuntos); serializa **só no commit**.
**Este bloco não publica página nenhuma** — mas **rearma** um caminho automático que publica (a onda das
12:20), e por isso o passo 8 verifica a primeira execução sem esperar por ela.

**C-1 · Criar o gate ANTES da correção — o disco de hoje é o controle negativo**

- **OBJETIVO** que a chave corrompida não possa voltar em silêncio.
- **ANTES** `grep -cE '^[[:space:]]*\[[A-Za-z0-9_]+ - ' tools/run-daily-content` → **8** [M] ;
  `grep -c 'shell_script_chave_associativa' internal/shellscriptquality/quality.go` → 0.
  **BASELINE DE VERMELHO CONHECIDO, a datar antes de tocar em nada** [emenda: o gate **já está vermelho**
  por 4 motivos alheios — `script_set_sha256` obsoleto e `shfmt_unformatted=5` em
  `ops/host-state/etc/{du,find,hdd-safety-net.sh,lsof,purga-lenta}`, **tracked e ` M` de outra frente** —,
  então **o exit do gate não discrimina nada neste bloco**]:
  ```bash
  timeout 130 ./tools/check-shell-script-quality > /tmp/shellq-antes.txt 2>&1; echo "EXIT=$?"
  grep -oE '^[a-z_]+:' /tmp/shellq-antes.txt | sort -u
  ```
- **AÇÃO** regra `shell_script_chave_associativa_nao_aspeada` em `internal/shellscriptquality` (o gate
  `shell-script-quality` **já está registrado** em `checks.go:390`/`:1820`). **Predicado ESTREITO**: só
  subscritos em `declare -A NOME=( … )` e leituras `${NOME[…]}` de nomes `-A` do **mesmo arquivo**; acusa
  ` - ` e não-aspeado com char fora de `[A-Za-z0-9_]`. O amplo dispararia em `${a[i+1]}` nos 108 scripts de
  produto. 4 fixtures: `[a - b]=`→1 · `[a-b]=`→1 · `["a-b"]=`→0 · `${v[i+1]}` indexado→**0**.
  **A regra emite `Issue` e NÃO toca `EvidenceRecord`** [emenda: campo novo no struct faz o
  `record_fingerprint_sha256` commitado deixar de casar (`quality.go:315-316,:322`) e o gate ganha um
  **quinto** vermelho, `…_fingerprint_invalid`; e `internal/ossscaleintegration/coverage.go:245,:1453,:1473`
  lê o mesmo arquivo].
- **DEPOIS** `./tools/go-modern test -count=1 ./internal/shellscriptquality/` → ok. O gate ao vivo lê-se
  **por código, nunca por exit**: `./tools/check-shell-script-quality 2>&1 | grep -c 'chaves_associativas_nao_aspeadas'`
  → **1** antes do passo 2, **0** depois.
- **SE NÃO VIER** o código novo não aparece ⇒ o enumerador não alcança o arquivo; imprima `scripts` (vem de
  `git ls-files --cached --others --exclude-standard`, e `--others` inclui **untracked**) antes de culpar a
  regra. **Não tocar `ops/host-state/etc/*`** (worktree de outra frente) e **não regenerar a evidência**
  nesta frente: congelaria bytes não-commitados de terceiro.
- **ROLLBACK** para frente; falso positivo ⇒ **estreitar** o predicado, nunca desligar.

**C-2 · Corrigir as 8 chaves com subscrito ASPEADO (não repondo o hífen)**

- **OBJETIVO** que `shfmt` não re-corrompa o conserto.
- **ANTES** `bash -n tools/run-daily-content` **aprova o errado** ; e o par que **discrimina** (por stdin,
  porque `shfmt -d tools/run-daily-content` **já sai 0 hoje**, com as chaves corrompidas — o arquivo está
  shfmt-normalizado justamente porque o shfmt o corrompeu) [emenda: o DEPOIS original não discriminava nada]:
  ```bash
  printf 'declare -A M=(\n[stj-precedentes]=x\n)\n'   | .cache/tools/shfmt-v3.13.1 -d - ; echo "hifen=$?"     # 1, com diff "[stj - precedentes]"
  printf 'declare -A M=(\n["stj-precedentes"]=x\n)\n' | .cache/tools/shfmt-v3.13.1 -d - ; echo "aspeado=$?"   # 0
  ```
  **E editar segurando o lock da onda** [emenda: a unit lê `tools/run-daily-content` **do disco** no
  disparo — 04:31:33 e 12:20:55 -03]: `flock -n 9 /tmp/wiki-daily-content.lock` ; tomado ⇒ **não editar**.
- **AÇÃO** 10 linhas lidas **uma a uma**: `[stj - precedentes]`→`["stj-precedentes"]`,
  `[stf - informativo]`→`["stf-informativo"]` (duas ocorrências: COLETORES e GERADORES),
  `[normas - federais]`, `[diarios - municipais]`, `[noticias - oficiais]`, `[stj - tema]`, `[stj - sumula]`,
  mais `[noticias]`/`[diarios]` aspeadas.
- **DEPOIS** `bash -n` OK ; `grep -cE '^[[:space:]]*\["[a-z-]+"\]=' tools/run-daily-content` → **10** ;
  `grep -cE '^[[:space:]]*\[[A-Za-z0-9_]+ - '` → **0** ; `.cache/tools/shfmt-v3.13.1 -d tools/run-daily-content` → exit 0.
- **SE NÃO VIER** `shfmt -d` exit 1 em **outra** linha é dívida preexistente — rode `shfmt -d` **antes** de
  editar para separar.
- **ROLLBACK** para frente (`git show HEAD:tools/run-daily-content` para **ler** o anterior).

**C-3 · `check-frescor-canal-diario`: sinônimos e as TRÊS pontas de data**

- **OBJETIVO** que o gate deixe de citar `2026-09-10` na saída de hoje sem inventar gap negativo.
- **ANTES** `./tools/check-frescor-canal-diario; echo "EXIT=$?"` → **1**, com `jurisprudencia` e `sumulas`
  em `[OK]` citando **2026-09-10**.
  **Diagnóstico correto, que muda o `SE NÃO VIER`** [emenda: a onda de hoje **coletou e gravou** —
  `data/ops/daily_content_collect.jsonl` tem `2026-09-15T07:29:11 'noticias - oficiais' exit 0` e
  `'stj - precedentes' exit 0 (304)`; a data velha no gate é **só o nome**, porque `CANAIS` (`:65-86`) tem as
  grafias canônicas hardcoded e o ledger passou a gravar a forma com espaços]:
  ```bash
  grep -c '"fonte": "stj - precedentes"' data/ops/daily_content_collect.jsonl
  python3 -c "import json;[print(d['medido_em'],d['fonte']) for d in map(json.loads,open('data/ops/daily_content_collect.jsonl'))][-6:]" 2>/dev/null | tail -6
  ```
- **AÇÃO** (i) em `status_por_fonte_por_dia`, normalizar com `re.sub(r'\s*-\s*','-',fonte)` — **nunca
  reescrever o ledger** (linhas de 09-10 e anteriores são canônicas; as duas grafias viram **sinônimo**);
  (ii) converter as **TRÊS** pontas para `America/Sao_Paulo` — dia do ledger (`medido_em[:10]`, gravado em
  UTC), **data do nome do arquivo de coleta** (também UTC) e `hoje` (`:337`)
  [emenda: trocar só `hoje` cria o erro **inverso**, e o arquivo que o dispara já está no disco —
  `data/research/daily/noticias-oficiais/2026-09-16.jsonl`, escrito às 21:51 **locais de 15/set**].
- **DEPOIS** `./tools/check-frescor-canal-diario --hoje 2026-09-15` e `--hoje 2026-09-16`, **exigindo
  `gap >= 0` nos dois** (a flag `--hoje` já existe e é o atalho que **dispensa esperar a virada do dia**) ;
  `jurisprudencia`/`sumulas` citando a data de **hoje** ; `diarios` segue REPROVA (§C) ;
  **e o selftest, que a bancada roda sozinha às 04:47**: `python3 tools/check-frescor-canal-diario-selftest` → 0
  [emenda: mudar o gate sem rodar o selftest de 300+ linhas é o padrão "gate verde, bancada quebrada"].
- **SE NÃO VIER** ainda `2026-09-10` **com linha de hoje no ledger** ⇒ o defeito é a **normalização do
  gate**, nunca a coleta: **não volte ao passo 2**.
- **ROLLBACK** para frente.

**C-4 · `tools/test_run_daily_content_chaves.sh` (descoberto pelo glob `tools/test_*.sh`)**

- **ANTES** arquivo não existe.
- **AÇÃO** extrai os blocos por `sed -n '/^declare -A COLETORES=(/,/^)/p'` e avalia em **subshell** —
  **nunca** `source` do arquivo inteiro (ele toma flock e roda a onda). Assere 5+5 chaves canônicas, filtro
  `--somente-noticias` → 1+1, e `shfmt -d` exit 0. Exit 0/1/2(=não extraiu).
- **DEPOIS** `bash tools/test_run_daily_content_chaves.sh` → 0 ; **mutação em CÓPIA**:
  `cp tools/run-daily-content /tmp/mut.sh && sed -i 's/\["stj-precedentes"\]/[stj - precedentes]/' /tmp/mut.sh && WIKI_ALVO=/tmp/mut.sh bash tools/test_run_daily_content_chaves.sh` → **1**.
  **E o arquivo novo entra no corpus do gate antes de ser commitado** (`--others` inclui untracked)
  [emenda], então **no mesmo passo**: `.cache/tools/shfmt-v3.13.1 -d tools/test_run_daily_content_chaves.sh` → 0
  e shellcheck limpo.
- **SE NÃO VIER** mutante vivo ⇒ o teste **reimplementa** a leitura; imprima as chaves extraídas **antes** da
  asserção.
- **ROLLBACK** para frente.

**C-5 · Commits (leve e pesado, separados)**

- **AÇÃO** leve: `git add tools/run-daily-content tools/check-frescor-canal-diario tools/test_run_daily_content_chaves.sh` ;
  `git commit -F /tmp/msg-p2-shell.txt -- <os 3 caminhos>`.
  Pesado, **com o lock tomado ANTES do `add`** (**§2**):
  ```bash
  flock -w 5400 /tmp/opt-wiki-agent-heavy.lock bash -c 'cd /opt/wiki && git diff --cached --name-only && git add internal/shellscriptquality/quality.go internal/shellscriptquality/quality_test.go && git commit -F /tmp/msg-p2-gate.txt -- internal/shellscriptquality/quality.go internal/shellscriptquality/quality_test.go'
  ```
- **DEPOIS** `git log -1 --stat` ; `./tools/check-shell-script-quality 2>&1 | grep -c 'chaves_associativas'` → 0.
- **SE NÃO VIER** reprovação na closure com índice sem Go ⇒ índice sujo de outra sessão. **Nunca `--no-verify`.**
- **ROLLBACK** commit novo.

**C-6 · A quarentena do STJ: uma competência ilegível não derruba o dataset**

- **OBJETIVO** que 1 arquivo quebrado **na fonte desde 2024-03-07** pare de matar os 7 datasets seguintes.
- **ANTES** `python3 -c "import json;d=json.load(open('data/corpus/jurisprudencia/stj-espelhos/cursor.json'));print({k:len(v) for k,v in d['datasets'].items()})"`
  → **4 datasets**: `primeira-turma 3 · quarta-turma 52 · segunda-secao 21 · terceira-turma 52` [M×2].
  `./tools/go-modern test -count=1 ./internal/stjacordaos/` → ok (**1,61 s**).
  O arquivo culpado: **599 bytes**, `sha256 ea2537c3…9b46`, `[ { … } } ]`, e é **SENTINELA**
  (`"Obs":"Sem lançamentos para o mês de fevereiro/2024"`, `ementa:""`) ⇒ **quarentenar não perde nada**.
- **AÇÃO, 6 peças no mesmo commit:**
  1. Fixture em **LF** (`core.autocrlf=input` transformaria 599 → 576 no blob; `.gitattributes` **proíbe**
     `-text`), com o teste **reconstruindo** `\n`→`\r\n` e asserindo o sha original.
  2. `internal/stjacordaos/quarentena.go`: `LinhaQuarentena{Dataset,Competencia,URL,ETag,LastModified,SHA256,Bytes,Erro,QuarentenadoEm}`
     + `CarregaQuarentena`. **O cursor NÃO é tocado** — cursor significa "coletado".
  3. Em `coleta.go`, no erro de `ParseEspelhos`: gravar quarentena, `rel.Ilegiveis++`, `continue`.
     **`rel.RecursosLidos++` FICA** [emenda: retirá-lo quebra o **único** controle de custo — o ilegível
     custou 1 requisição + 10 s de Crawl-Delay; com N ilegíveis a execução estoura
     `WIKI_GO_CMD_TIMEOUT_SECONDS=1500` e o cursor para de avançar. O teto é de recursos **buscados**].
  4. **Mesmo tratamento para erro transitório de REDE** [emenda: `coleta.go:167-168` faz
     `return rel, fmt.Errorf(...)` no erro de `cli.Busca` e reproduz o defeito idêntico na recoleta de 392
     competências], com **corte por N falhas CONSECUTIVAS** no mesmo dataset.
  5. **Revalidação condicional** da quarentena por `If-None-Match`/`If-Modified-Since`: 304 ⇒
     `Quarentenados++`, 1 requisição e 0 bytes/dia; 200 com sha novo ⇒ parsear de novo.
  6. **Resumo por execução** em `execucoes.jsonl`, gravado **inclusive em execução toda-304** — hoje
     `coleta.go:169-172` faz `continue` **antes** de gravar o manifesto, e "timer desligado" e "nada novo"
     ficam indistinguíveis.
- **DEPOIS** `-run TestUmaCompetenciaIlegivel` → **FALHA** contra o código de hoje (controle negativo
  grátis), **ok** depois ; `./tools/go-modern build ./internal/... ./cmd/...` ;
  `./tools/go-modern test -count=1 ./internal/stjacordaos/` → ok, **todos**.
- **SE NÃO VIER** `TestColetaRespeitaOTetoDeRecursosPorExecucao` quebrando ⇒ você mexeu em
  `RecursosLidos`: desfaça (peça 3).
- **ROLLBACK** para frente; `internal/stjacordaos` está **fora** do grafo [M] ⇒ sem reatestação.

**C-7 · Gate `coleta-stj-cobertura`, com veredito por FLUXO**

- **AÇÃO** registro em `Names` **e** no `case` (o `dispatcher_orfao_test.go` varre AST nos dois sentidos).
  Lê cursor/manifest/quarentena/`execucoes.jsonl` + `DatasetsEspelhos`; **grava nada**.
  Linha informativa `cobertura: N/10; faltam M` **nunca reprova sozinha**. REPROVA se (a) última execução
  > 2× o período do timer; (b) rodou e `recursos_lidos+nao_modificados == 0` com `faltam>0`; (c) dataset
  canônico com 0 competências **e sem quarentena que explique**; (d) quarentena não revalidada na última
  execução. **Controle positivo obrigatório**: imprimir os 10 slugs e as chaves do cursor **antes** de
  qualquer zero, e `len(recursos)` **por dataset** [emenda: os "392 competências / 67 min" são **DERIVADOS**
  de supor 52 meses em cada um dos 6 datasets nunca coletados — marcar como DERIVADO e não herdar a suposição].
- **DEPOIS** `./tools/go-modern run ./cmd/check coleta-stj-cobertura; echo "EXIT=$?"` → **1 hoje**, por (c),
  veredito **certo** ; `./tools/go-modern test -count=1 ./internal/checks/` → ok.
  **Gate e produtor no MESMO commit** [emenda: registrar em `Names` antes de o produtor existir soma um
  vermelho por dívida aos que a bancada já tem].
- **SE NÃO VIER** exit 0 hoje ⇒ cursor/lista errados; imprima `len(DatasetsEspelhos)`=10 e chaves do cursor=4.

**C-8 · A CADEIA DE EXTRAÇÃO VEM ANTES DA RECOLETA — 81,4% do ganho sem esperar 67 min**

- **OBJETIVO** colher o ganho que **não depende da coleta**: o parser roda sobre os **60.221 registros já no
  disco**, e responde por **28.559 de 35.082** promoções (**81,4%**) contra 6.523 do `qwen3.5:4b`.
- **ANTES** — **e o worker do cérebro apenda no MESMO arquivo que o parser apenda e o writeback decodifica**
  [emenda: o runbook analisava a corrida só contra o **coletor**; `generate-extracao-por-parser/main.go:78→:162→:228`
  resolve para `cerebro.ArquivoExtracoes` = `data/ai/extracoes_dispositivos.jsonl`, e
  `wikijuridica-cerebro.service` está `active/running` escrevendo 24/7]:
  ```bash
  systemctl show wikijuridica-cerebro.service -p ActiveState --value    # anote
  sudo -n systemctl stop wikijuridica-cerebro.service
  wc -l data/ai/dispositivos_promovidos.jsonl data/ai/extracoes_dispositivos.jsonl   # ANOTE O VALOR LIDO AGORA
  cat data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl | wc -l              # 60.221
  ```
  [emenda: o ANTES original trazia `44.160` como **constante** e o arquivo tem escritor vivo — medi 44.189
  na mesma sessão. O ANTES **grava o número lido na hora**; o DEPOIS exige "maior que o ANTES".]
  `sqlite3` desta máquina é `/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3`, sempre com
  `?mode=ro` — **nunca** `cerebro status`, que abre sem `mode=ro` e roda DDL no banco do worker vivo.
- **AÇÃO** `./tools/go-modern run ./cmd/generate-extracao-por-parser` (ensaio) → `-aplicar` →
  `./cmd/generate-writeback-extracoes -raiz "$PWD" -dry-run` → sem a flag →
  `./cmd/cerebro enfileirar-extracoes` → `sudo -n systemctl start wikijuridica-cerebro.service`.
- **DEPOIS** `pendente` **NÃO cai** (a `Fila` não apaga nem cancela tarefa): as provas são
  `wc -l data/ai/dispositivos_promovidos.jsonl` **> o ANTES**; o share por `modelo` **subindo**; e a linha
  `writeback: N promoção(ões)…, M aplicada(s)` (`cmd/cerebro/main.go:710-714`) com **M > 0**.
- **SE NÃO VIER** `M == 0` ⇒ promoção sem acórdão casado é **dado órfão**: confira `CarregaSobreposicao` e a
  chave (`id_fonte`/`texto_sha256`) antes de culpar o parser.
- **ROLLBACK** append-only, "última linha por chave vence" ⇒ desfazer é promover de novo.

**C-9 · Recoleta, um dataset por chamada, fora da janela do timer**

- **ANTES** preservar `cursor.json` e `manifest.jsonl` em `.agents/runtime/` com data
  [emenda: `registros-*.jsonl` são gitignored (`.gitignore:697`) e **não têm rollback por git** — o rollback
  para frente declarado é `tools/collect-stj-acordaos --aplicar --refazer --dataset <d>`].
  Janela do timer: `wikijuridica-stj-acordaos-coleta` **09:51:24 -03** [M] + `RandomizedDelaySec=20min` +
  ~17 min ⇒ **09:51–10:28**; à mão aí, espera `WIKI_HEAVY_LOCK_WAIT_SECONDS=600` e **sai 75**.
- **AÇÃO** ensaio no dataset que morre (a forma com hífen é aceita):
  `tools/collect-stj-acordaos --dataset espelhos-de-acordaos-segunda-secao --desde 2024-02-01 --ate 2024-04-30 --max-recursos 5 --timings`
  → depois `--aplicar --max-recursos 60`. Os 7 restantes, **um por chamada**, via `ai-pane run NOME 'cmd'`
  ou em background [emenda: um `for` de 7 × ~530 s no foreground **morre no meio** — o Bash desta sessão tem
  teto de 120 s — com o `--aplicar` já tendo escrito parte do cursor e sem exit code visível].
  **Nunca `--max-recursos 400`**: 3.920 s estoura `WIKI_GO_CMD_TIMEOUT_SECONDS=1500` e
  `WIKI_HEAVY_TIMEOUT_SECONDS=1800`. Elevar timeout é mascaramento — e é desnecessário: o cursor torna a
  execução **retomável**.
- **DEPOIS** a saída cita `20240229` como **quarentenada** e **segue** ; `echo $?` = 0 ;
  `git status --porcelain data/corpus/` **VAZIO** depois do ensaio (ensaio que grava é ensaio que mente) ;
  competências de `segunda-secao` no cursor → **51** [D: 52−1] ; `wc -l quarentena.jsonl` → 1 ;
  ao fim, 10 datasets no cursor e `./cmd/check coleta-stj-cobertura` → **0**.
- **SE NÃO VIER** parou em **outra** competência ⇒ há um **segundo** arquivo quebrado; `quarentena.jsonl`
  traz sha e erro de cada um: **siga**. Exit **75** = lock alheio ⇒ reoriente para o bloco GATES e volte;
  **nunca mate o dono do lock**.
- **ROLLBACK** `--refazer` (acima); `shardpreserve` nunca reduz.

**C-10 · Diários: é TLS **deles**, e a causa raiz é nossa, no meio**

- **ANTES** — **e a premissa "morta desde 2026-08-29" é falsa** [emenda: em **2026-09-13** a coleta saiu
  **exit 0 com 403 edições inéditas**; de 09-06 a 09-12 a falha é a guarda de **marca d'água**, não TLS; TLS
  só aparece em 09-14 e 09-15]. O comando que lê certo (o `tail -2` do runbook original devolvia 0 porque as
  duas últimas linhas **não são de diários**):
  ```bash
  python3 -c "import json;[print(d['medido_em'],d['saida'][:120]) for d in map(json.loads,open('data/ops/daily_content_collect.jsonl')) if 'diarios' in d['fonte']]" | tail -3
  ```
  Causa medida: `api.queridodiario.ok.org.br` tem **SNI aposentado, deles** — mesmo IP, SNI `ok.org.br`
  fecha TLSv1.3 com `verify 0`, SNI `api.…` recebe `alert number 40` **sem certificado**, igual em TLS
  1.2/1.3 e IPv4/IPv6 ⇒ **não é nossa OpenSSL, não é rota**. O host vivo `api.queridodiario.org.br`
  **cumpre o contrato** (200 com `total 311`, `territory_id 2909307`, `scraped_at 2026-09-14T22:20:35`) e
  **oscila** (1 de 7 em 200; medi também um `curl: (28) timeout` — **erro de transporte, não de status**).
- **AÇÃO, 4 peças:** (1) retentar transitório **por status (429/5xx) E por transporte** (timeout, TLS, reset)
  [emenda: o predicado só-por-status **não cobre** a falha medida — `resolve.go:205-209` trata erro de
  transporte por `prova.ErroDeRede` + `continue`, **fora** do ramo de status de `:210-214`], com
  **orçamento TOTAL de resolução** (~120 s) em vez de 4 tentativas por candidato, contra o `timeout 900` de
  `run-daily-content:422`; (2) registrar **cada** tentativa na `Evidencia` (hoje só a última sobrevive);
  (3) falha de resolução **não** cai em `apiBase` (o host morto): cai na **última base confirmada** em
  `data/ops/diarios_api_base.json`, e sem ela **falha honesto**; (4) corrigir o comentário de
  `collect-diarios-municipais/main.go:52` que afirma robots 200 — medi **404**, que é permissão total
  (RFC 9309 §2.3.1.4) e `robotstxt` já trata; comentário que mente é bug (R1).
- **DEPOIS** `./tools/go-modern test -count=1 ./internal/sourceresolve/ ./internal/sourcecollect/` ;
  ensaio com a invocação **real** do COLETORES: `./cmd/collect-diarios-municipais -seco -limite 300 -com-texto 0`
  (**não** `-limite 5`: é **tamanho de página**, e 311 gazetas exigiriam 63 páginas contra `tetoPaginas=12`).
  **A prova é a base resolvida impressa (`api.queridodiario.org.br`) e a trilha com status/content-type/sha
  por candidato** — **exit 0 é consequência da fonte, não do conserto** [emenda: com o resolvedor já certo,
  a marca d'água de 2026-09-13T03:56 pode devolver "janela sem inédita" e exit 1 **legitimamente**].
- **SE NÃO VIER** `tls: handshake fail` persistindo ⇒ o fallback ainda aponta para `apiBase`; imprima a
  trilha. "Janela não esgotou" ⇒ **não** suba `tetoPaginas` (é a guarda que impede a marca d'água passar por
  cima de edição não coletada).
- **ROLLBACK** para frente. **Registry no MESMO commit do código** (`content/source_registry.json:1036,:1038`
  ainda declaram o host morto), senão há janela em que o registry aponta para host que o binário não resolve.
  E o gate de alcançabilidade dá veredito por **k de n**, nunca 1 de 1 — a oscilação faria o gate piscar e
  alguém o desligaria.

**C-11 · P3: matar a família dos produtores órfãos**

- **ANTES** `ls cmd | grep -cE '^generate-.*-pages$'` → **8** [M], dos quais 5 com invocação real em
  `run-daily-content:369-373` e **TRÊS** órfãos: `generate-acordao-pages`, `generate-lei-artigo-pages` e
  **`generate-entity-pages`** (não nomeado pelo plano).
- **AÇÃO** `ops/produtores-de-pagina.jsonl` com `produtor, artefato, runner, gate_a_jusante, estado
  (ativo|orfao_declarado|aposentado), motivo, medido_em` — **10 linhas** (os 8 + `generate-propostas-reescrita`
  + `generate-first-published-at`). Gate `produtor-orfao` em `internal/checks`, registro em `Names` **e**
  `case`, **escopo FECHADO** a esse conjunto (o amplo repetiria "gate vermelho por estoque que nada drena").
  **Casa POSIÇÃO DE COMANDO, não menção**: `$GO run ./cmd/<n>`, `ExecStart=…<n>`, `"$ROOT/tools/<n>"`,
  `./cmd/<n>` como primeira palavra — **sem** depender de remover comentário
  [emenda: são **5** sítios de menção medidos, e 2 **não** são comentário `#`:
  `tools/check-writeback-do-cerebro-nao-atrasa:8` está dentro de docstring `"""` e
  `tools/test_generate_motor_tier_a.py:308` é string Python; um predicado que "descarta `#`" trata docstring
  como **código** e conta como invocação — o falso **negativo** que faz os três órfãos passarem].
- **DEPOIS** `./tools/go-modern run ./cmd/check produtor-orfao; echo "EXIT=$?"` → **0** com as 10 linhas ;
  controle negativo com **os 5 sítios medidos** numa cópia em `/tmp` ⇒ **REPROVA** ;
  `./tools/go-modern test -count=1 ./internal/checks/` → ok.
- **ROLLBACK** para frente.

---

## RUNBOOK P4 / P5 — GATES (fato × publicidade × juízo) E ATRIBUIÇÃO

Concorrente com COLETA. **Roda depois da travessia de 5 páginas do P6** (**D1**).
**Proibições extras deste bloco**: editar `internal/quality`, `internal/legalsignature` **ou
`internal/ptbrtext`** (**D8**) · `-limite` default (30) em censo (`roda()` faz `break` no limite:
conta só as recusas de **antes** dele) · baixar `limiarMolde` (fraude operacional).

**G-1 · Linha de base: bancadas verdes antes de qualquer edição**

- **ANTES** `cat /proc/loadavg`; se load1 ≥ 12, `./tools/check-load-headroom --max 12` sai 1 e manda
  **avançar outra frente**, nunca esperar.
- **AÇÃO** `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/` e
  `./tools/go-modern test -count=1 ./internal/cerebro/ ./internal/v2bodyneardup/ ./internal/quality/`
- **DEPOIS** 4 linhas `ok` (base: 27,131 s / 1,338 / 2,238 / 2,781; **33** `func Test`).
- **SE NÃO VIER** vermelho aqui é **pré-existente**: date o teste com `git log -1 --format=%h <arquivo>`
  antes de atribuí-lo a este bloco. Não edite até saber.

**G-2 · Registrar a família no mapa do gate (pré-requisito, não consequência)**

- **ANTES** `grep -c "stj-acordao" tools/check-derived-authorial-floor` → **0**: `FAMILIAS_CANAIS_DERIVADOS`
  (`:279-287`) não tem `stj-acordao-derivado`, e o **EIXO 3 é cego para o canal inteiro**. O próprio gate
  avisa em `:271-278`: *"FAMÍLIA NOVA ENTRA AQUI OU NASCE FORA DO GATE"*.
- **AÇÃO** acrescentar `"stj-acordao-derivado": "stj-acordao-derivado-*.jsonl"`; criar
  `tools/check-familia-no-mapa-do-gate`.
- **DEPOIS** — **e aqui a D1 mudou este passo, que os runbooks traziam como inócuo**: sob a ordem
  `travessia → P4`, o shard **JÁ EXISTE** com as **5 páginas** da travessia quando o G-2 roda. Logo o gate
  **não** entra com 0 páginas: entra com 5, ou seja **10 pares**, e o selftest com
  `PARES_REPROVADOS_CONHECIDOS == 0` passa a correr contra acórdãos **reais** no instante do registro.
  `./tools/check-derived-authorial-floor` → 0, com `stj-acordao-derivado: 5 paginas | mediana … | max …`
  **[A MEDIR]** — espera-se bem abaixo de 0,70, mas **não se declara "continua 0"**.
  `./tools/check-derived-authorial-floor-selftest` → 0 ; `./tools/check-familia-no-mapa-do-gate` → 0.
  **Se qualquer um dos 10 pares vier ≥ 0,70, é a S10 disparando sobre a própria travessia**: o conserto é
  **escopo** (separar família em `shinglesPublicados`) ou **indexação**, **nunca** subir a constante nem o
  limiar. (A nota antiga — "glob sem arquivo ⇒ `shards=[]` ⇒ `range(0)`" — só valeria se o P4 viesse antes
  da travessia, que a **D1** decidiu que não vem.)
  **E o selftest entra na lista de gates deste bloco** [emenda: `tools/check-derived-authorial-floor-selftest`
  **existe** (313 linhas) e `:231-238` assere `PARES_REPROVADOS_CONHECIDOS == 0` **como teto E piso** —
  o runbook declarou "não há teste do gate" porque grepou só o padrão `tools/test_*`]:
  `./tools/check-derived-authorial-floor-selftest` → 0.
- **SE NÃO VIER** vermelho **agora** não é desta linha (não há páginas): leia o log da etapa antes de herdar
  a causa.
- **ROLLBACK** para frente.

**G-3 · `corpoParaMolde`: tirar a mobília, MANTER o dígito**

- **OBJETIVO** parar de medir o template. A camada **HEADINGS sozinha** tem `p50 = 1,0000` e **10.658 de
  11.175** pares ≥ 0,70 — o detector mede a mobília.
- **ANTES** `./tools/go-modern run ./cmd/measure-regua-molde -familia stj-tema-derivado -ledger ""`.
  **Números da POPULAÇÃO, não da amostra** [emenda: o `max 0,5697` do runbook vem de stride de 150 de 1.074
  páginas = 1,9% dos pares; rodando o **gate real** (1m46s) a população dá
  `stj-tema-derivado: 1074 paginas | mediana 0.2799 | max 0.6657 (limiar 0.70)` e
  `stf-informativo-derivado max 0.6787`. A folga até 0,70 é **0,0343**, não 0,1303 — cinco vezes menor, e
  *"o limiar nunca morde"* **não se sustenta** para a família de acórdãos, que é população outra e maior].
- **AÇÃO** **função nova** espelhando `v2bodyneardup.AssembleBody` (opening, `sections[].text`, todas as
  perguntas, todas as respostas — **sem heading**). Trocar `corpoDaPagina` por `corpoParaMolde` nos
  **quatro** produtores de assinatura, **num commit só** — `roda()`, `shinglesDoProprioShard()`,
  `shinglesPublicados()` e `relata()`; **localize por símbolo, não por linha**
  (`grep -n 'func shinglesDoProprioShard\|func shinglesPublicados\|func relata' cmd/generate-acordao-pages/main.go`)
  [emenda: as linhas citadas nos runbooks derivaram]. **Não** tocar `corpoDaPagina` (alimenta `WordCount` e
  as bandas), `shinglesNeutralizados`, `jaccard`, `parecida`.
  **MANTER a neutralização de dígito**: `main_test.go:274-277` troca todo dígito por `4242` e exige que o
  anti-molde **pegue** a irmã (defeito real "Tema 1154" × "Tema 4"); tirar os headings **já zera** as recusas.
- **DEPOIS** `p50 ≈ 0,3440`, **0** pares ≥ 0,70 em tema × tema; sobre os candidatos de **acórdão** é
  **[A MEDIR]** no censo — a população do gerador é outra (cross-família). Bancada verde, **incluindo**
  `main_test.go:274-277`.
- **SE NÃO VIER** teste de dígito vermelho ⇒ mexeu em `shinglesNeutralizados`: desfaça. Sobrando pares
  ≥ 0,70 ⇒ **não baixe o limiar**: vá ao G-6, que tem a regra de decisão.
- **ROLLBACK** para frente — `corpoParaMolde` volta a delegar numa linha.

**G-4 · Provar equivalência de CORPO, não "ser melhor"**

- **AÇÃO** `TestCorpoParaMoldeEspelhaOGate` **reimplementa o corpo do gate à mão dentro do teste**, nunca
  chamando a função do gerador (desenho de `cmd/generate-stj-tema-pages/unicidade_test.go:36-39`, cujo
  motivo está escrito lá). Asserção: **igualdade de string**.
  **O oráculo é UM, e é o `corpo_v2` do `check-derived-authorial-floor`** [emenda: os dois gates **não**
  montam o mesmo corpo — `check-derived-authorial-floor:402-420` faz `.strip()` em **cada parte** e descarta
  vazias; `neardup.go:157-176` descarta vazias e **não** faz strip; os tokenizadores também divergem
  (`[^\w\s]` do Python **mantém** o `_`; `[^\p{L}\p{N}\s]` do Go **troca** por espaço). O gerador copia
  `limiarMolde` e `shingleMold` **desse** gate, então é ele o oráculo].
- **DEPOIS** verde. **Prova por mutação, as duas obrigatórias**: reinserir o heading ⇒ **vermelho**;
  intercalar o FAQ ⇒ **vermelho**. Sem as duas o teste não prova nada.
- **SE NÃO VIER** divergência residual no separador ou no `TrimSpace` ⇒ alinhe **no `corpoParaMolde`**,
  nunca no gate. **E não estique a mão para `internal/ptbrtext`** (**D8**).

**G-5 · Tirar o piso de 250 da ementa de ENTRADA e deixar a saída decidir**

- **ANTES** no censo, `ementa_curta_demais_para_duas_camadas` e
  `grep -cE "corpo_abaixo_da_banda_do_verbete|comentario_proprio_abaixo_do_piso"` — esperado **0** [DERIVADO].
- **AÇÃO** remover o corte por `pisoEmentaPalavras` em `elegivel()`; o piso vira **medição** (os cortes de
  saída já decidem com o corpo montado). **No mesmo commit**, corrigir os comentários que afirmam "1.674
  candidatos" — passam a mentir (R1).
- **DEPOIS** `ementa_curta_demais_para_duas_camadas` → **0**; parte reaparece em `Paginas`, parte nos cortes
  de saída, **que passam a disparar** — isso é o desenho.
- **SE NÃO VIER** `texto_oficial_nao_cabe_na_banda` explodindo ⇒ o gargalo é `citacaoPorItens` contra
  `tetoPalavras=700`; conserto é o teto, **não repor o piso**. `comentario_proprio_abaixo_do_piso` em massa
  ⇒ o piso estava certo **para aquela fatia**: mantenha a remoção e registre o número — recusar na saída,
  com o corpo real, é medição melhor que a proxy da ementa.
- **ROLLBACK** para frente — repor o `if`, com o número medido no comentário.

**G-6 · Itens transcritíveis como FALLBACK, e TRÊS censos com uma causa cada**

- **ANTES** regex derivado do **dado**, não do palpite (stride de 6 de 52 arquivos — **refazer sobre os 54
  de hoje** [emenda]): 7.695 registros, **2.658** ACÓRDÃO com ementa ≥ 250 palavras, dos quais **141 (5,3%)**
  sem item pelo estrito. Formas: `\d{1,2}.` **inline** 77 (54,6%) · romano+ponto 59 (41,8%) ·
  `\d{1,2}`+hífen 23 (16,3%) · nenhuma das três 5 (3,5%).
- **AÇÃO** escrever a fixture `TestFallbackDeItensNaoMudaOEstrito` **ANTES** do fallback (congelar a saída de
  `itensTranscritiveis` sobre ~200 ementas que **hoje** produzem itens). Só então o fallback em
  `itensDaEmenta`, acionado **apenas** quando o estrito devolve zero posições.
  **E TRÊS censos, um por correção** [emenda: um censo só depois das três perde a atribuição — a correção 2
  aumenta a população que chega ao anti-molde, e `aceitas` cresce dentro da passada, então o contador se
  move por **dois** motivos ao mesmo tempo]:
  ```bash
  for etapa in pos-regua pos-piso pos-fallback; do
    time ./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 99999 2>&1 | tee /tmp/censo-$etapa.txt
    echo "EXIT=${PIPESTATUS[0]}"
  done
  ```
  (`-seco` é read-only: `executar` retorna **antes** de `gravaPortfolio`/`gravaShard`.)
- **DEPOIS** fixture verde (o estrito não mudou para ninguém) **e** `ementa_sem_item_transcritivel` caindo.
  **Compare CONTADOR, nunca identidade de página**: `parecida()` compara contra `aceitas`, que **cresce** a
  cada aceita — o filtro é **guloso e dependente de ordem**. "Estas 1.405 serão destravadas" não se
  sustenta; "o contador `molde_acima_do_limiar` cai de X para Y" sim.
- **SE NÃO VIER — regra de decisão PRÉ-REGISTRADA** (escrita **antes** de ver o número): se
  `molde_acima_do_limiar` continuar alto, rode `measure-regua-molde -area jurisprudencia -top 20 -ledger ""`
  e leia os pares. **Cross-família** (acórdão × tema/informativo) ⇒ o defeito é o **ESCOPO**:
  `shinglesPublicados` passa a separar por família, como o gate — é correção de escopo e **não afrouxa nada**.
  **Acórdão × acórdão diferindo só em dígito** ⇒ é o eixo do dígito; se for removido, é com
  `main_test.go:274-277` **atualizado, nunca apagado**, e o número que justifica vai no commit.
  Soma dos contadores + páginas **tem** de bater com o total de candidatos; se não bater, algum `continue`
  novo não incrementa contador — e recusa sem contador é o ponto cego que este censo existe para não ter.
  **Tempo > 900 s é bug P0 de escala**: indexe o anti-molde (bucket por shingle ou MinHash), **nunca**
  aumente o timeout.

**G-7 · Fechar P4: build, bancada, gates, commit**

- **AÇÃO** `./tools/go-modern build ./internal/... ./cmd/...` ·
  `test -count=1 ./cmd/generate-acordao-pages/` · `./tools/check-derived-authorial-floor` ·
  **`./tools/check-derived-authorial-floor-selftest`** · `./tools/check-v2-body-near-duplicates` ·
  `./tools/check-familia-no-mapa-do-gate` · commit com o lock tomado **antes** do `add` (**§2**).
- **DEPOIS** 33+ testes verdes; os quatro gates exit 0.
- **SE NÃO VIER** pre-commit reprovando por orçamento da closure = **índice sujo**, não carga (duas sessões
  erraram esse diagnóstico; a máquina ociosa chega ao mesmo teto).
- **ROLLBACK** para frente, commit novo.

**G-8 · P5: o gabarito de 100, congelado por IDENTIDADE**

- **ANTES** `grep -c "" data/ai/extracoes_dispositivos.jsonl` → **anote o valor lido agora** (o arquivo tem
  escritor vivo) ; `ls data/legal-corpus/*.json | wc -l` → **29**.
- **AÇÃO** stride **determinístico** sobre os itens com `urn` não vazio — nunca prefixo, nunca amostra "de
  suspeitos". Conferência **mecânica**, reusando `carregar_corpus()`, `texto_do_artigo()` e `termos()` de
  `tools/check-anchor-claim-sustenta-dispositivo` (localize por símbolo). **`legal-corpus/*.json` NÃO tem
  campo `urn`** (chaves: `slug`, `nome`, `source_url`, `citation_url`, `conference_url`, `declared_url`) ⇒ a
  ponte é `norma` → `slug`/`nome` ou a URL da fonte, **nunca** URN → diploma direto. Honre
  `confiavel_para_acusar_divergencia`: diploma não confiável entra em `fora_do_corpus`, **não** em acusação.
  **O gabarito grava a IDENTIDADE de cada item (`texto_sha256` + norma + artigo) dentro do arquivo, e o I4
  seleciona por esse conjunto, nunca por índice** [emenda: stride **posicional** sobre arquivo append-only
  que cresce entre a medição e a remedição atribui à correção uma diferença de **população** — e o próprio
  G-9, com `--aplicar`, acrescenta ~44k linhas **entre** as duas]. Item desaparecido conta como **classe à
  parte**, não é substituído.
- **DEPOIS** 100 linhas; `sha256sum` registrado. **Controle positivo obrigatório**: injete 3 itens
  sabidamente errados e confirme que o gabarito os marca — sem isso o zero não distingue "medi e deu zero"
  de "não medi".
- **SE NÃO VIER** cobertura baixa ⇒ **não** troque a amostra por uma que o corpus cobre (seria escolher a
  população depois do número). Declare `fora_do_corpus` como classe à parte.
- **ROLLBACK** gabarito é append; versão nova com data nova, a antiga fica.

**G-9 · Atestar a norma DENTRO do trecho — classificando, nunca filtrando**

- **AÇÃO** **uma função só**, `cerebro.AtestacaoDaNorma(norma, textoCitado, texto)`, chamada nos **TRÊS**
  sítios [emenda: o runbook editava só o caminho do **modelo** (`extrai()`), enquanto a revisão do G-10
  reprocessa o acervo por **outro** caminho (`revisa()` e `regeneraLinhaDoParser()`) que **80,5%** das linhas
  percorrem — o campo nunca apareceria e a regra de parada leria "empate", concluindo "a ideia é inerte"
  quando o fato é "editei a função errada"]. É o que o comentário de `extracao.go` já exige: *"Mesma funcao
  do parser — uma forma so no projeto, senao os dois produtores divergem no mesmo texto."*
  Campo `Atestacao string json:"atestacao,omitempty"` com três valores: `trecho` · `texto_inteiro` (a folga
  de hoje, que testa a norma no texto **inteiro**) · `nenhuma`. **O `continue` não muda: o item continua
  entrando.** A conferência do **artigo** reusa `semMilhar` e `reNumeroDeNorma` de `triagem.go`, **não** um
  regex novo.
- **DEPOIS** `./tools/go-modern test -count=1 ./internal/cerebro/` verde ; o medidor devolve a **mesma
  contagem total de itens** — só a distribuição muda.
- **SE NÃO VIER** **se a contagem total CAIR, você filtrou.** É o erro que torna a regra de parada
  inmensurável, porque muda a população. Desfaça o `continue` novo e mantenha só o campo.
- **ROLLBACK** para frente — o campo é `omitempty`.

**G-10 · Revisão v9: a reabertura é AUTOMÁTICA, e o dataset público vai junto**

- **ANTES** distribuição por revisão no disco (`uniao_do_parser_v2` 33.763, `parser_regenerado_v4` 1.272,
  `uniao_do_parser_v1` 546, v8 45, v6 41, v5 19, v1 19, v3 12, v7 1).
- **AÇÃO** **não** "incluir a v8 entre as que a v9 reprocessa" — é redundante: `main.go:131` pula **apenas** a
  revisão **corrente** e `ExecutorTriagem`, e o comentário diz *"CADA REVISAO NOVA REABRE O QUE AS ANTERIORES
  FECHARAM"*. Basta criar `RevisaoNormaNoTrechoCitado = "norma_no_trecho_citado_v9"` e trocar as referências
  (localize por símbolo); a v8 fica **constante histórica**. Rodar **em ensaio primeiro** (sem `--aplicar`).
  **No MESMO commit, regenerar o dataset público** [emenda: `public/datasets/extracoes-dispositivos-*.jsonl.gz`
  é **servido ao público** e `tools/test_datasets_publicos.py:146-160` compara o dataset com a **última linha
  por chave** do arquivo-fonte, via `json.dumps(r, sort_keys=True)` do registro **inteiro**: o campo novo faz
  o teste ficar vermelho e o `.gz` no ar passa a ser versão anterior do dado, **em silêncio** — e nem
  `run-qualidade-diaria` nem `run-daily-content` invocam esse teste]:
  ```bash
  ./tools/generate-datasets-publicos && python3 tools/test_datasets_publicos.py; echo "EXIT=$?"
  ```
  (`.jsonl.gz` já existe em `public/` ⇒ **não** há questão de allowlist nova.)
- **DEPOIS** o ensaio imprime `ExtracoesLidas`, `SemTextoNoCorpus`, `HashDivergente`, `PelaFila`,
  `Recarimbadas`. Só então `--aplicar`, que preserva o original em `--preservar-em` com data.
- **SE NÃO VIER** ensaio dizendo "0 linhas" ⇒ ficou referência à constante velha; confira **lendo**, não
  re-rodando. `HashDivergente` alto é **esperado** (602 de 35.012 registrados nessa condição).
- **ROLLBACK** append-only e original preservado; reverter é acrescentar uma **v10** que desfaz, **nunca
  apagar**.

**G-11 · A rota de refino que o carimbo aciona — e a junção que precisa existir antes**

- **ANTES** `grep -nE "dispositivos|extracoes|atestacao" tools/generate-v2-publication-severity` → **ZERO**
  [emenda: o passo estava escrito como ajuste de uma linha e é **irrealizável** assim — a severidade é por
  **PÁGINA**, a atestação é por **ITEM** de extração de acórdão, e não existe junção item→`intent_id` nesse
  gerador].
- **AÇÃO** **declarar a chave que liga item a `intent_id` ANTES** de prometer a classificação. O elo
  candidato é `internal/stjacordaos/writeback.go` (escreve URNs no registro do corpus): conferir se carrega
  `texto_citado`/atestação. **Se a junção não existir, o passo certo é**: a atestação vira **sinal na fila de
  refino** (`data/editorial/v2_rewrite_queue.jsonl`), **não** campo de severidade.
- **DEPOIS** a fila cresce; a contagem de **críticos não muda**.
- **SE NÃO VIER** item virando **crítico** ⇒ a página não publica, e **3.101 das 3.201** entradas da fila são
  páginas **VIVAS**. Volte a médio **na mesma sessão**.
- **ROLLBACK** para frente.

---

## RUNBOOK P6 / P8 / P7 — PUBLICAR

**Ordem interna** (**D1**): `P-a travessia (5) → [P4/P5] → P-b recenseio → lote cheio → publicar → oneshot →
P8 → P7`.

**P-a1 · A cota do lote, que neste gerador está quebrada**

- **OBJETIVO** que a 2ª passada **acrescente**. Hoje `intentsPublicados()` pula o próprio shard pelo prefixo,
  `parecidaComPrevia(..., exceto: intentID)` deixa a rota **remontar-se**, e o laço fecha em
  `len(passada.Paginas) >= limite { break }` contando **as remontadas**: com N no shard, a passada seguinte
  com `-limite N` acrescenta **zero** — e o oneshot morreria em silêncio. É o defeito que
  `internal/tetodelote` corrigiu nos outros **cinco** geradores e **não** neste
  (`grep -rn tetodelote cmd/generate-acordao-pages/` → vazio).
- **ANTES** `ls data/editorial/v2_pages/ | grep -ci acordao` → **0** [M]: o shard **nunca foi gravado**; a
  primeira gravação cria a família. `./tools/go-modern list -deps … | grep -c generate-acordao` → 0 (**fora**
  do grafo, sem reatestação) [M].
- **AÇÃO** importar `internal/tetodelote`; `teto := tetodelote.Novo(limite)`.
  **A guarda entra DEPOIS do switch de protegidos/emitidos, não no lugar do `break`** [emenda: no ponto do
  `break` o `intentID` ainda **não existe** — vem na linha seguinte — e `jaNoShard` deriva de
  `previas[intentID]`; como escrito, **não compila**]:
  `jaNoShard := previas[intentID] != nil` ; `if !teto.Admite(jaNoShard) { continue }` (**continue**, nunca
  `break`, porque adiante vem rota do próprio shard a preservar) ; `teto.Conta(jaNoShard)` **depois** de
  todos os descartes ; imprimir `teto.Acrescentadas()` no `relata()`.
  Nota de fronteira a escrever no código: `shinglesDoProprioShard` descarta páginas com corpo < 50 palavras —
  uma linha do shard abaixo disso não entra em `previas`, seria tratada como inédita e consumiria cota
  (hoje inócuo com `corpo min 487`, mas é a fronteira implícita que faz a regra divergir depois).
- **DEPOIS** **teste provado por MUTAÇÃO**: shard sintético com 3 remontáveis + 5 candidatos, `-limite 2` ⇒
  `len(Paginas)==5` **e** `Acrescentadas()==2`; com o `>= limite {break}` de volta, **VERMELHO** com
  `Acrescentadas()==0`. **Cole a saída vermelha antes de aplicar.** Depois, a **bancada do pacote**:
  `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/` → PASS (gate verde não é "não quebrei
  nada": em 2026-09-05 um gate passou VERDE com 14 de 17 testes dele quebrados).
- **ROLLBACK** segundo commit para frente. O shard não existe: **dano zero**.

**P-a2 · Separar AREsp de AgInt, com teste de falso positivo**

- **OBJETIVO** recuperar até **308** páginas de mérito hoje barradas por **rótulo de classe**
  (`procedimental()` casa por `strings.Contains`, sem olhar o texto).
- **ANTES** reproduzir: `AGINT 32.837 · ARESP 11.553 · RESP 10.023 · EDCL 5.285`; AREsp puro cujo dispositivo
  decide o recurso **5.705**; que mencionam "agravo interno" **0 de 11.553**; com ementa ≥250 + evidência
  substantiva, **308**.
- **AÇÃO** três funções nomeadas **pelo que decidem**: `classeExterna(classe)` (1º token antes de
  ` NO / NOS / NA / NAS `), `procedimental()` **sobre a classe EXTERNA** (AGINT, AGRG, AGREG, AGRESP, EDCL,
  EDV, EARESP — **AREsp sai**), e `arespDeMerito(registro)` ("não conhecer do recurso" fica barrado).
  **RETRATAÇÃO herdada, e ela fica**: o mesmo classificador aplicado ao **AgInt** devolveu 30.127 "mérito" e
  é **FALSO** — ali "lhe negar provimento" é o agravo interno; três tentativas deram 17, 392 e 5.705 para o
  mesmo conjunto. **Não existe régua medida para o AgInt**: ele fica barrado e entra como **agregado** no P8.
- **DEPOIS** teste de falso positivo (§5 do contrato): amostra por **stride determinístico**, n=30 — todo
  admitido tem provimento/negativa **do recurso**; **0 de 30** menciona "agravo interno"; controle de
  vizinhança `classeExterna("AGINT NO ARESP")=="AGINT"` e `classeExterna("EDCL NO AGINT NO ARESP")=="EDCL"`;
  **mutação**: voltando a `strings.Contains`, **vermelho**.
- **SE NÃO VIER** alta muito maior que 308 ⇒ está admitindo AgInt: rode o controle de vizinhança e leia a
  distribuição de `classeExterna` das novas. Zero ⇒ imprima 5 dispositivos admitidos e 5 recusados **antes**
  de mexer no regex.

**P-a3 · A TRAVESSIA de 5 páginas**

- **ANTES** shard ausente [M] · manifesto **11.106** [M] · `./tools/check-v2-portfolio-pairing` OK (3,45 s) ·
  `git status --porcelain data/editorial/v2_pages data/editorial/portfolio_v2` **vazio** [M] ·
  `sudo -n systemctl stop wikijuridica-server-reload.path` (**D4**) ·
  `./tools/check-onda-avanca --antes --rotulo "travessia-acordaos"` **imediatamente antes**.
  **Este passo EXIGE o I-7 já construído**: sem ele, `ESTADO` é um arquivo único global e o `--antes` daqui
  **sobrescreve o baseline da onda das 04:31**, cujo `--depois` passa a reportar `novas: 0` — o falso
  negativo exato que `internal/tetodelote` existe para tornar visível. Com I-7, o `--depois --minimo 5` lê o
  baseline **desta** coorte; sem ele, o número é o acumulado de quem passou por último.
- **AÇÃO**
  ```bash
  nice -n 19 ./tools/go-modern run ./cmd/generate-acordao-pages -limite 5 | tee .agents/runtime/acordao-travessia.log
  ./tools/check-shard-preservation
  ./tools/go-modern run ./cmd/check v2-cross-shard-collision
  ./tools/go-modern run ./cmd/check text-truncation
  ./tools/go-modern run ./cmd/check derived-body-repetition
  ./tools/check-derived-authorial-floor && ./tools/check-derived-authorial-floor-selftest
  # PORTFOLIO PRIMEIRO — a autoridade do pareamento e o commit PAI
  git add data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
  git commit -F .agents/runtime/msg-portfolio.txt -- data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
  ./tools/check-v2-portfolio-pairing
  git add data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
  git commit -F .agents/runtime/msg-paginas.txt -- data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
  nice -n 19 python3 tools/generate-v2-publication-severity | tail -20
  nice -n 19 python3 tools/generate-v2-publication-severity --write | tail -20
  nice -n 19 ./tools/generate-page-content-revision | tail -8
  nice -n 10 ./tools/go-modern run ./cmd/publish-v2-direct -reviewed-at "$(date -u +%F)" -allow-public-write | tee .agents/runtime/publica-travessia.log
  echo "EXIT=${PIPESTATUS[0]}"
  ```
  **Pathspec do commit = o MESMO caminho exato do `add`, nunca o diretório** [emenda: `git commit <pathspec>`
  commita a **árvore de trabalho** de tudo que casa, então `-- data/editorial/portfolio_v2` levaria junto o
  que outra frente deixou modificado durante a geração].
  **Por que NÃO passo `-published-at`**: `ApprovedAt = primeiroNaoVazio(page.PublicationDate, opts.publishedAt)`;
  para rota nova não há estreia, e o default já é `time.Now().UTC()` — passar a flag só acrescenta a chance
  de carimbar **dia errado** (22:5x -03 = 01:5x Z, dias diferentes). **Por que NÃO `-limit 5`**: com
  `--allow-public-write` ele é **RECUSADO** ("corta a lista e o manifesto é REESCRITO a partir dela"): o lote
  de travessia é do lado do **gerador**.
- **DEPOIS** shard **5 linhas** · preservação 0 · pairing sem `so_no_candidato` ·
  `./tools/check-onda-avanca --depois --minimo 5 --rotulo "travessia-acordaos"` → `novas: 5`, `sumiram: 0` ·
  manifesto **11.111** [D].
- **SE NÃO VIER** `so_no_candidato` ⇒ inverteu a ordem portfólio/páginas (custou 6 dias de fábrica e
  IndexNow mudo de 20/08 a 26/08): commite o portfólio e reconfira. `sem_linha_no_censo` ⇒ censo mais velho
  que o shard: refaça. **Publicador exit ≠ 0 ⇒ PARE E NÃO REINICIE** (sitemap sem manifesto aborta o boot,
  com `Restart=always` **sem teto**).
- **ROLLBACK — saiba antes de apertar**: `writeRollbackSnapshot` copia **3 arquivos** e **não** cobre
  `public/` nem `public/sitemaps/`. Desfazer 5 páginas é `tools/retirar-pagina-do-ar` + republicar. **Com 5 o
  custo é trivial — e é por isso que a travessia vem antes.**

**P-a4 · Os derivados, o reinício, e a prova ao vivo das SEIS superfícies**

- **AÇÃO** exatamente o **P1b-8** (brotli → co-citação → temas sociais → sweep → reload → `start` da `.path`),
  depois `./tools/check-publicado-no-ar --de-arquivo <as 5 rotas> --gravar`.
- **DEPOIS** `OK: as N rota(s) … (Xs até servir)` (boots medidos: **32 s** e **23 s**; teto 90 s) ;
  `check-publicado-no-ar` exit **0** ; `curl -sI` da rota nova → 200 com `cf-cache-status: MISS` (rota nova
  **nunca esteve** no cache; `s-maxage=604800` só prende o que já foi servido) ; `/api/v1/citar` →
  `cf=DYNAMIC` (a Cache Rule exclui `/api/`) ; **zero 404 em `/redesocial/tema/`** para as 5.
- **SE NÃO VIER** `go_desatualizado` **depois** do reload ⇒
  `systemctl show wikijuridica-server -p NRestarts -p ExecMainStatus -p ActiveState` e
  `journalctl -u wikijuridica-server --since "-5min"`. **Essa unit tem `OnFailure=` VAZIO,
  `StartLimitIntervalUSec=0` e `WatchdogUSec=0`**: fica em laço de 5 s **para sempre sem alertar ninguém**.
  404 na borda e 200 em `:8088` ⇒ é o **túnel**: `./tools/check-edge-live --sem-alerta`.

> ### ── AQUI RODA O BLOCO P4/P5 (D1) ──

**P-b1 · RECENSEIO pós-P4 (o número velho sai de todo veredito)**

- **ANTES** os três censos do G-6 já no disco.
- **AÇÃO** `time ./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000 2>&1 | tee /tmp/censo-pos-p4.txt; echo "EXIT=${PIPESTATUS[0]}"`
- **DEPOIS** **[A MEDIR]** — `páginas montadas`, `candidatos`, e a tabela de recusas. Baseline **anterior ao
  P4**, para comparar e **não** para exigir: `4763 candidatos`, `2488 páginas montadas`, `real 12m27,9s` sob
  `loadavg1 11,8–14,4`, com `corpo min 487 mediana 681 max 700`. **`corpo max 700` é EXATAMENTE `tetoPalavras`
  e o teto da banda do `verbete`: margem ZERO** — confira `corpo max <= 700` em toda passada.
- **SE NÃO VIER** o tempo passar de 2.400 s ⇒ **indexar** as assinaturas (MinHash/banda), **nunca** esticar o
  teto ("lentidão em 10k é bug P0, e é proibido corrigir aumentando timeout").
- **ROLLBACK** n/a (`-seco` é read-only).

**P-b2 · O LOTE CHEIO**

- **ANTES** shard = 5 · `./tools/check-load-headroom --max 12` · `.path` **parada** · `--antes` próprio
  (I-7) · `./tools/sweep-sitemap-carencia-expirada --seco | tail -2` → **`0 vencido(s)`**
  [emenda: **asserir sobre o contador de vencidos no texto, nunca sobre "vencendo" nem sobre o exit**, que é
  0 nos dois casos; exigir "0 vencendo" é **inalcançável** e travaria o oneshot por dois dias].
- **AÇÃO** `nice -n 19 timeout 2400 ./tools/go-modern run ./cmd/generate-acordao-pages -limite 5000 | tee .agents/runtime/acordao-lote-cheio.log` ;
  os mesmos 6 gates ; portfólio e depois páginas, com pathspec **exato**.
  `timeout 2400`, não 900: é O(n²) no tamanho do lote e já custou 748 s com o shard **vazio**; com N no
  próprio shard, `shinglesDoProprioShard` acrescenta N assinaturas à comparação.
- **DEPOIS** shard **N linhas** [A MEDIR] (~3.900 B/linha ⇒ 2.488 ≈ 9,7 MB; **não rotacionar**: nenhum teto
  de leitura por arquivo abaixo de 10 MB, e `intentsPublicados()` já pula todo `stj-acordao-derivado-*`) ·
  preservação 0 **com as 5 da travessia entre as preservadas** · colisão 0 · **tempo de parede registrado**
  (é a linha de base do oneshot).
- **SE NÃO VIER** `páginas montadas` muito abaixo do recenseio ⇒ leia a **tabela de recusas** do próprio
  relatório; a decomposição antiga (`1.405 molde + 682 + 165 + 22 + 1`) **não vale mais** (**D1**).
- **ROLLBACK** nada no ar; `shardpreserve` **nunca reduz** o shard ⇒ correção é sempre para frente.

**P-b3 · Publicar, regenerar os derivados, varrer, reiniciar**

- **AÇÃO**
  ```bash
  nice -n 10 ./tools/go-modern run ./cmd/publish-v2-direct -reviewed-at "$(date -u +%F)" -allow-public-write | tee .agents/runtime/publica-lote.log
  echo "EXIT=${PIPESTATUS[0]}"
  ./tools/check-onda-avanca --depois --minimo 1 --rotulo "lote-acordaos"
  nice -n 19 ./tools/generate-brotli-static --jobs 4
  ./tools/go-modern run ./cmd/generate-legal-cocitation
  ./tools/go-modern run ./cmd/generate-social-temas --aplicar && ./tools/check-social-temas-espelhados
  ./tools/sweep-sitemap-carencia-expirada --seco | tail -2      # exige "0 vencido(s)"
  ./tools/reload-wiki-server
  sudo -n systemctl start wikijuridica-server-reload.path
  ```
  **Sem `timeout` no publicador** (mesma razão do P1b-7: zero `signal.Notify`).
  **A ordem `publicar → derivados → varrer → reiniciar` não se inverte.**
  **`generate-social-temas --aplicar` é obrigatório aqui e é o achado mais caro do bloco**: sem ele, N
  páginas novas saem com N âncoras `/redesocial/tema/…` para **404**, e o precedente medido está no próprio
  `deploy-publico:687-699` — *"o banco tinha 10.141 temas para 11.039 páginas publicadas. As 898 páginas sem
  tema geraram 1.161 requisições 404 de bots valiosos em 10 dias (GPTBot 817, PerplexityBot 339)"*.
- **DEPOIS** manifesto 11.111+N · `onda-avanca` `novas: N`, `sumiram: 0` · `sweep` **0 vencidos** ·
  `./tools/go-modern run ./cmd/check http-smoke` 0 · `./tools/check-served-vs-manifest` 0 ·
  `./tools/check-public-sem-lixo` 0 · `./tools/check-csp-style-hashes` 0 ·
  `./tools/check-publicado-no-ar --de-arquivo <amostra por stride de 100 das novas>` → **0**.
- **SE NÃO VIER** `served-vs-manifest` vermelho **em massa** ⇒ `publishedmanifest.Validate` no boot tem teto
  de **10 por código** e **25 no total**: acima disso **o Go não sobe**. **Não reinicie; republique.**
- **ROLLBACK** só para frente: republicar.

**P-b4 · Contrato, manifesto e estreia — nesta ordem, e por quê**

- **AÇÃO**
  1. **Edição pontual** da linha 128 do `CLAUDE.md` para o número medido — **antes de qualquer commit**,
     porque o gate é incondicional e lê a **worktree**. `./tools/check-contrato-vs-medicao` → **0 já**.
  2. `git add` + `git commit -F … -- <os 10 caminhos exatos>` (P1b-3).
  3. `python3 tools/generate-first-published-at --dry-run` → sem a flag → commit.
  4. `git add CLAUDE.md` ; `git commit -F … -- CLAUDE.md`.
- **Por que 2 antes de 3**: `generate-first-published-at` percorre
  `git log --reverse -- published_manifest.jsonl` e anota o **primeiro** commit de cada `unique_intent_id`.
  **Rota que não está em commit nenhum não tem estreia recuperável** — e é isso que produziu as órfãs do
  P1b. Sem o passo 2, as N páginas deste bloco entram nesse balde e, na publicação seguinte, recebem
  `datePublished = hoje` **outra vez**: o P1b se reproduzindo por causa deste bloco.
- **DEPOIS** `check-contrato-vs-medicao` 0 · `--dry-run` da estreia ≥ 11.106+N ·
  `git status --porcelain data/editorial` **vazio** · `check-untracked-product-inventory` 0.

**P-b5 · Borda: purga dirigida e reaquecimento**

- **O que precisa de purga**: `/sitemap.xml`, `/sitemaps/pages-*.xml`, os 7 artefatos de descoberta,
  `/jurisprudencia/` e `/jurisprudencia/index.md` (o índice de área lista **todos** os membros, §7 do
  contrato). **O que NÃO precisa**: as N rotas **novas** — nunca estiveram no cache.
- **AÇÃO** — **derivar a lista dos `<loc>` de `public/sitemap.xml`, não do glob de disco** [emenda: o glob
  varre **63** arquivos, incluindo os 6 em carência que o índice **não** anuncia, e o número esperado "~66"
  era medição **pré**-publicação apresentada como expectativa **pós**]:
  ```bash
  LISTA=.agents/runtime/purga-descoberta-acordaos.txt
  { printf '%s\n' / /sitemap.xml /feed.xml /rss.xml /robots.txt /llms.txt /llms-full.txt /jurisprudencia/ /jurisprudencia/index.md
    grep -oE '<loc>[^<]+</loc>' public/sitemap.xml | sed -E 's#.*(/sitemaps/[^<]+)</loc>#\1#'; } > "$LISTA"
  test -s "$LISTA" || { echo "lista vazia — ABORTE"; exit 2; }
  test "$(wc -l < "$LISTA")" -eq "$(( $(grep -c '<loc>' public/sitemap.xml) + 9 ))" || echo "CONFIRA a derivacao"
  ./tools/purge-origin-cache --rota /jurisprudencia/index.md
  nice -n 19 ./tools/warm-origin-cache --rps 80 --concorrencia 8 | tail -3
  TETO=$(( $(wc -l < "$LISTA") + 1 ))
  ./tools/purge-edge-cache --de-arquivo "$LISTA" --teto-por-url "$TETO" --dry-run | grep -q 'URL(s) em' || exit 2
  ./tools/purge-edge-cache --de-arquivo "$LISTA" --teto-por-url "$TETO"
  ./tools/warm-edge-cache --de-arquivo "$LISTA" --rps 12 --concorrencia 4
  timeout 600 python3 tools/generate-indexnow-incremental-submit 2>&1 | tail -4; echo "exit real=${PIPESTATUS[0]}"
  ```
  A guarda `test -s` + o `grep -q 'URL(s) em'` no `--dry-run` são o que impede o caso silencioso: lista vazia
  ⇒ `caminhos` vazio ⇒ `seletivo` falso ⇒ **`purge_everything` com exit 0** (**D7**).
- **DEPOIS** `cf-cache-status` do sitemap **MISS** pós-purga e **HIT** com `age` pequeno pós-warm ·
  `<loc>` no índice = shards ativos (era **57** [M], sobe com o lote) · `check-edge-discovery-freshness` 0 ·
  última linha do ledger com `scope` = `"N URL(s) em M lote(s)"`, **nunca** "tudo" · IndexNow
  `http_status 200`, `success true`, `ownership_proof_verified_over_http true`.
- **SE NÃO VIER** `HIT` com `age` grande pós-purga ⇒ leia o `scope` gravado. **Não repita em laço.**
- **ROLLBACK** o pior efeito é borda fria, que o aquecimento desfaz.

**P-b6 · O oneshot autônomo**

- **ANTES** `./tools/check-units-instaladas` → 0 [baseline: 126 units, 3 avisos de cópia]. Units principais
  são **symlink** para o repo: editar `ops/systemd/*.service` marca `NeedDaemonReload=yes`, o gate reprova e
  **`deploy-publico` (passo 0a/7) para o deploy de TODAS as frentes**.
- **AÇÃO** `tools/publicar-estoque-acordaos` (**`tools/publicar-estoque` NÃO existe** [M]; as reais são
  `tools/publicar` e `tools/reload-wiki-server`) + `.service`/`.path`/`.timer`.
  **As etapas são LINHAS DE COMANDO literais, não nomes** [emenda: `tools/generate-writeback-extracoes` não
  existe — o real é `cmd/generate-writeback-extracoes` **com `-raiz`**, como em `run-daily-content:456`], e
  **todas as 26 têm teto explícito** [emenda: 13 das 24 ficavam sem teto — o flock, os 6 gates, os 3 commits,
  os 2 `onda-avanca`, o `check-publicado-no-ar` (que faz **rede**) e o `measure-coorte`; com
  `TimeoutStartSec` alto a unit **pendura horas segurando o próprio flock** e morre por SIGTERM].
  Ordem: flock próprio → writeback → gerador → 6 gates (**PARA**) → portfólio → pairing (**PARA**) →
  páginas → severity → revision → `--antes` → **`stop` da `.path`** → publish (**PARA em exit ≠ 0**) →
  `--depois` → **brotli** → **co-citação** → **temas sociais + gate (PARA)** → sweep (**exige `0 vencido(s)`**)
  → reload → **`start` da `.path`** → `check-publicado-no-ar --gravar` → purga+warm → IndexNow →
  **20-bis: reescrever a linha 128 do `CLAUDE.md` e commitá-la, com `check-contrato-vs-medicao` 0 como
  pré-condição** → commit dos 10 → estreia → lei-artigo (P8) → `measure-coorte`.
  **`TimeoutStartSec` derivado da soma REAL dos tetos + 32%** — e a soma se recalcula com os 13 tetos novos,
  não se herda ("13.590" era aritmética errada; a lista dava 12.990).
  **Lock PRÓPRIO** `/tmp/opt-wiki-estoque-acordaos.lock` em volta do oneshot inteiro (exclusão contra si
  mesmo, que o `.path` torna provável); **nenhum** lock pesado no corpo (tomá-lo por horas bloquearia o
  commit Go de toda sessão); retry curto no `.git/index.lock` em cada commit.
  **PROIBIDO na unit**: `SuccessExitStatus` (a onda de hoje tem `ExecMainStatus=1` **e** `Result=success` com
  `OnFailure` que **não disparou**) · `WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1` · `Restart=` num oneshot.
  **OBRIGATÓRIO**: `OnFailure=wikijuridica-alerta@%N.service` · gatilho por `.path` sobre
  `data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl` **com guarda de não-reentrância** (e declarado
  que o **`.timer` é o gatilho efetivo**: o arquivo observado não muda há 5 dias) · `.timer` **antes de
  01:00 UTC**, porque **97% dos primeiros contatos do gptbot caem em 01h–02h UTC** e publicar às 07h UTC são
  **18 h de espera auto-infligida**.
- **DEPOIS** `systemd-analyze verify` · `./tools/check-units-instaladas` 0 **e sem `NeedDaemonReload`** ·
  `./tools/check-units-alarme` 0 com a unit nova exigindo e tendo `OnFailure` ·
  `systemctl show … -p SuccessExitStatus` **VAZIO**.
- **ROLLBACK** `systemctl disable --now` + `daemon-reload`; a publicação volta a ser manual por este runbook
  e **nada do que está no ar muda**.

**P8 · `generate-lei-artigo-pages` deixa de ser órfão, e o agravo vira agregado**

- **ANTES** `grep -n generate-lei-artigo-pages tools/run-daily-content ops/systemd/*.service` → **zero
  invocação real** (só comentários) ; `wc -l data/editorial/v2_pages/leis-motor-01.jsonl` → **38**.
  **Medição que muda o desenho**: o laço de indexação por URN **não tem** filtro `procedimental()` — já conta
  **todo** registro em `a.Classes[nome]++`. **O agravo já é contador hoje**; "promover a conteúdo agregado" é
  um **delta**, não uma ligação nova.
- **AÇÃO** (1) bloco que diga quantos dos N julgados que invocam o artigo são de **mérito** e quantos de
  **cabimento**, pela classe **EXTERNA** do P-a2 — a **única** régua medida. **Proibido** "índice de reforma"
  ou "chance de êxito", e proibida qualquer afirmação que dependa do classificador que foi **retratado**.
  (2) ligar o produtor no **oneshot** (não na onda, já no teto de 900 s/gerador), conferindo
  `grep -n tetodelote cmd/generate-lei-artigo-pages/main.go` [A MEDIR: se não usar, é o mesmo defeito do
  P-a1]. (3) gate a jusante no oneshot com **PARA**.
- **O MAIOR RISCO DE SEO DO BLOCO**: o texto novo entra em `body_sections`, que **está** em
  `CAMPOS_DE_CONTEUDO` ⇒ `content_sha256` muda, a **re-datação é VERDADEIRA**, `lastmod` avança e o sitemap
  re-anuncia — em até **3.481** páginas. `--ressemear` é **PROIBIDO** nesta passada (suprimir a re-datação
  esconderia do buscador conteúdo que **de fato** mudou).
  **E antes de agrupar, rode a publicação SECA para ler o veredito do registry de graça** [emenda:
  `conciliaRegistryDeShard` roda **independentemente** de `-allow-public-write`; a chave é
  `(coorte, ordinal)` e a coorte **não precisa esvaziar, basta encolher** — a ~32 URLs/shard, 3.481 páginas
  encolhem coortes em ~109 ordinais [D] contra o teto `max(6, assigned/4) = 15` [M: `assigned=63`]. O
  agrupamento que o runbook **mandatava** maximiza a recusa, e a recusa cai **depois** de o acervo estar no
  disco]. Se `fora > 15`: **fatiar a mudança de corpo em publicações dimensionadas pelo teto** — nunca
  `--permitir-churn-de-shard`.
- **DEPOIS** `leis-motor-01.jsonl` = 38 + N ·
  `./tools/generate-page-content-revision --purge-targets` com lista **não vazia** ·
  `./tools/check-lastmod-causalidade` 0 · `corpo max <= 700`.
  Meça a taxa de 304 depois: `check-efeito-nos-bots` exige **14 dias PRE + 14 POS** e ≥100 req autenticadas
  em cada janela — **o atalho existe e não está no runbook de ninguém**:
  `WIKI_EFEITO_NOS_BOTS_LOG=<fixture>` exercita o veredito contra log **já gravado**. **Encurtar a janela**
  geraria alarme falso, que é o que faz alguém desligar o gate.
- **SE NÃO VIER** `--purge-targets` **zero** para página que mudou de corpo ⇒ o texto caiu **fora** de
  `CAMPOS_DE_CONTEUDO` e a página **não será re-anunciada**. Confira onde o gerador escreveu.
- **ROLLBACK** para frente. **Não há rollback para o `lastmod` já anunciado** — por isso o dimensionamento
  pelo teto é requisito, não estilo.

**P7 · DataJud: os dois enforcers, o coringa, e a prova por mutação**

- **ANTES** `ls -d internal/datajud* internal/codex2datajud*` → os reais são **`datajudfila`**,
  **`datajudtpubatch`**, **`codex2datajudobservations`**, **`codex2datajudfrontiersignalreport`**;
  **`internal/datajud` NÃO existe** e o prefixo sem barra casa todos **por acidente**.
  `list -deps … | grep -c codex2policyenforcement` → **0**: **fora** do grafo, sem reatestação [M].
- **AÇÃO** (1) trocar os dois prefixos **sem barra** por **diretórios nomeados com barra**, como o vizinho do
  SQLite no mesmo arquivo. (2) **trocar o CORINGA** — a última cláusula autoriza **qualquer** arquivo sob
  `cmd/` cujo caminho **contenha** a substring `datajud`, inclusive um `cmd/build-datajud-pages` ou
  `cmd/publish-datajud`, **dentro do caminho de publicação**, que é a única propriedade que a trava existe
  para garantir [emenda: os três controles negativos propostos não exercitavam essa cláusula, e I6
  entregaria gate verde com o buraco **maior** intacto]. (3) o teste passa a nomear os **quatro** reais
  (hoje **falta `internal/datajudfila`**, onde vive `Sigiloso()`), com controle negativo recusando
  `internal/datajudrender`, `internal/datajudpublicador`, `internal/codex2datajudhtml` **e
  `cmd/build-datajud-pages`**. (4) **prova por mutação** de `Sigiloso()` → `return false`.
  (5) regenerar o baseline: `./cmd/generate-codex2-policy-enforcement --metadata-only
  --allow-approved-runtime-dependency --no-publication` ; (6) commit único sob `flock`.
- **DEPOIS** as duas bancadas PASS · mutante ⇒ **≥3 testes VERMELHOS em pacotes distintos**, cobrindo as três
  camadas que `cmd/social/processo.go:59-62` declara (`Consulta` não copia o corpo, `Guarda` não persiste,
  `DetalheDaResposta` recusa traduzir) e os dois desfechos de `processotela.go` ·
  `./tools/go-modern run ./cmd/check-codex2-policy-enforcement` 0, **zero**
  `codex2_policy_datajud_import_scope_escape` · `build ./internal/... ./cmd/...` sem erro.
- **SE NÃO VIER** escape em pacote legítimo ⇒ faltou um dos quatro diretórios (a mensagem imprime
  `<arquivo>:<import>`). **Mutante SEM vermelho ⇒ a trava é decorativa: esse é o achado, e vale mais que a
  mudança.**
- **ROLLBACK** regenerar o baseline + edição para frente. `codex2policyenforcement` **não está no caminho de
  serviço** (chamadores: os dois `cmd/` dele, `cmd/generate/*` e `internal/checks`; **nenhum** é `httpserver`
  nem `cmd/server`): **este passo não pode derrubar o portal.**

---

## RUNBOOK P9 / P10 / P12 — DAEMON

**Estado medido agora** [M]: `wikijuridica-cerebro.service` `active/running`, `Type=simple`, `NRestarts=1`,
`WatchdogUSec=0`, `RestartUSec=15s`, `StartLimitIntervalUSec=10s`, `StartLimitBurst=5` (**nenhum declarado na
unit** — são defaults do manager, invisíveis ao grep), `TimeoutStopUSec=4min`, `PrivateTmp=yes`.
`/api/ps`: `qwen3.5:4b`, `size=3.227.894.413`, **`size_vram=0`**, **`context_length=8192`** [M].

**Ordem obrigatória** (inverter = laço de boot):
`D-1 boot → D-2 transporte+Devolver → D-3 disjuntor → D-4 modelos → D-5 flock p1 → D-6 flock p2 → D-7 flock p3 → D-8 StartLimit → D-9 watchdog`.
**Ordem única de deploy** [emenda: cumprir "uma edição só da unit" é impossível com D-5 e D-9(i) exigindo
build antes, e editar a unit antes do binário é o precedente de `Type=notify` que já custou laço de boot]:
`D-1..D-5 + D-9(i)` → **commit** → **`./tools/deploy-cerebro`** → `D-6` (tmpfiles) → **UMA** edição da unit
com `D-7+D-8+D-9(ii)+D-10` → `daemon-reload` → `restart`.
**E o `deploy-cerebro` é o ÚLTIMO comando do bloco, depois do commit** [emenda: ele exige
`vcs.revision == HEAD` e termina chamando `check-binario-vs-fonte`; deploy antes do commit faz o **próprio
script** sair ≠ 0 no último passo, e `binario-vs-fonte` **já está vermelho** na bancada de hoje].

**D-0 · Os instrumentos do bloco (nada muta produção, com DUAS exceções declaradas)**

`A1` `Residente` ganha `SizeVRAMBytes`/`ContextLength` (hoje decodifica só `name/model/size/expires_at` e é
**cego** para os dois campos que `/api/ps` já entrega [M]) · `A2` `cerebro status --somente-leitura`
(`?mode=ro` + `busy_timeout`) — **e a AÇÃO é um caminho que NÃO chama `Abrir`** [emenda: `Abrir` executa
`EsquemaSQL`, `sqlitepool.Aplica` e `registraVersaoSeVazio` — **três escritas** — antes de qualquer leitura,
então `mode=ro` falha no primeiro `ExecContext`; o conserto estava relegado ao `SE NÃO VIER`] ·
`A3` `Fila.Elegiveis` (`pendente AND disponivel_em<=now`) · `A4` batimento · `A5` gate `cerebro-batimento` ·
`A6` `tools/check-mascara-de-exit` · `A7` **`--gravar`** em `check-portal-health` (**D5**) ·
`A8` detector `cerebro_nrestarts*` no vigia, **com chaves próprias** [emenda: o reparo do vigia é uma cadeia
`if/elif` **exclusiva** sobre `(reparo_ultimo, reparo_falhas_seguidas)`, e um ramo novo **apagaria a memória
anti-laço do reparo do PORTAL**, que chega a `chown var/nginx` + reload e a reiniciar o Go — use
`reparo_cerebro_*`, fora da cadeia exclusiva] · `A9` `--teto-bytes-residentes` · `A10` `--root` de ensaio ·
`A11` `NotificaWatchdog()` reusando o `notifica()` privado (**não** uma terceira implementação) ·
`A12` `cerebro reabrir --id/--desde` · `A13` `tools/medir-baseline-gpu`.

> **As duas exceções a "nada muta"**: `A7` e `A8` editam `tools/check-portal-health`, que um timer de **2 min**
> executa **do disco** — a edição **é** o deploy, e a unit declara `SuccessExitStatus=0 1`, então um traceback
> (exit 1) no código novo mata o **vigia do portal** a cada 2 min com `Result=success` e **zero alerta**.
> [emenda] **Procedimento obrigatório**: editar **cópia**, `python3 -m py_compile`, rodar os harness
> `tools/test_portal_health_*.sh`, e trocar por `mv` atômico. **Nunca** provar rodando o vigia (ele grava
> state e zera `reparo_ultimo`, e uma execução de diagnóstico entre dois `--repair` faz o 2º **redisparar o
> deploy**).

**D-1 · O boot não morre sem Ollama**

- **ANTES** `main.go:157-159` faz `cliente.Versao` ⇒ `return err` ⇒ `os.Exit(1)` [M].
- **AÇÃO** trocar por `log.Printf` e seguir — `Saude.Verifica` **já** pausa com "ollama fora do ar" a cada
  ciclo. `CarregaAcervo` e `Abrir` continuam **FATAIS** (acervo ausente e fila corrompida não são
  transitórios).
- **DEPOIS** com o Ollama parado: `ActiveState=active`, **`NRestarts` sem crescer**; journal com
  "pausa: … ollama fora do ar".
- **SE NÃO VIER** se ainda morrer, o `os.Exit(1)` veio de **outro** erro do boot — leia a linha do journal,
  não presuma.
- **Pré-requisito de D-8**: sem D-1, um restart transitório do Ollama no boot **queima o burst** e deixa o
  cérebro em `failed` para sempre.

**D-2 · Erro de TRANSPORTE = pausa — e `Fila.Devolver`, sem a qual isto PERDE TAREFA**

- **OBJETIVO** que um outage do Ollama não consuma tentativas nem sumia com tarefa.
- **ANTES** `worker.go:100-112` cobra `Falhar` de **todas** as tarefas do lote no erro geral.
- **AÇÃO** [emenda — **sem esta, o passo vira QUEBRA: perda de dado silenciosa**]: as duas metades do runbook
  original ("sem `Falhar` e sem incrementar `tentativas`") são **impossíveis** — (1) o incremento já
  aconteceu no **claim** (`fila.go:409` `UPDATE … estado='executando', tentativas=tentativas+1`); (2) sem
  `Falhar`, as até 3 linhas do lote ficam `estado='executando'`, e o **único** caminho
  `executando → pendente` é `Fila.Recuperar`, chamado **só no boot** — e D-1+D-3 existem justamente para o
  daemon **não** reiniciar. `Reivindicar` só lê `estado='pendente'`. **Resultado: 3 tarefas somem da fila por
  outage, para sempre**, e `A12`/`Reabrir` **não as alcança** (toca só `estado='erro'`).
  **Instrumento novo, obrigatório**:
  `Fila.Devolver(ctx, ids)` → `UPDATE tarefa SET estado='pendente', worker='', tentativas=MAX(tentativas-1,0), disponivel_em=<agora> WHERE id IN (…) AND estado='executando'`,
  chamado no ramo de transporte, **com teste**. Em `internal/ollama`, classificar `connection refused`, `EOF`,
  DNS e 5xx como `ErrTransporte`; 404 (modelo ausente) é erro de **CONTEÚDO** e continua em `Falhar` — quem
  o segura é D-3/D-4.
- **DEPOIS** prova **C-a**: `executando == 0` **e** `pendente de volta ao valor de antes`; `tentativas` do
  lote **não muda**; journal diz "pausa" [emenda: o DEPOIS original — "contagem por estado INALTERADA" —
  **esconde** exatamente essa fuga, porque a contagem **total** não muda: a linha só troca de coluna].
- **ROLLBACK** para frente. `internal/cerebro` está **fora** do grafo [M] ⇒ sem reatestação.

**D-3 · Disjuntor de lotes consecutivos falhos — portão do P12**

- **ANTES** `worker.go:156-180` `if n > 0 { continue }` **pula o `time.After` mesmo com lote FALHO**; saúde em
  cache 60 s ⇒ modelo removido leva a fila inteira a `erro` em ~30 min [D].
- **AÇÃO** `Worker.lotesFalhosSeguidos`: lote com erro geral **não** entra no `continue` (dorme
  `IntervaloOcioso`) e incrementa; ≥3 seguidos ⇒ `w.ultimaSaude = time.Time{}` (força reconsulta) e pausa
  `IntervaloOcioso × 2^min(n,5)` (30 s → 16 min [D]), com log nomeando o disjuntor. Lote OK zera.
- **DEPOIS** prova **C-b**, com a janela certa [emenda: `Falhar` só marca `erro` quando
  `tentativas >= maxTentativas` (3) e o backoff é `backoff × tentativas` com `--backoff 5m` ⇒ a 3ª falha só é
  alcançável em **≥15 min**; em 10 min o crescimento de `erro` é **ZERO** com e sem as correções, e
  "`<=9`" e "`0`" **não se distinguem**]. Portanto: janela **>15 min**, **ou** unidade volátil com
  `--backoff 5s --tentativas 1`; e **o observável é o par `(estado, tentativas)`** da fila-cópia, nunca o
  crescimento de `erro`.
- **Portão do P12**: **C-b verde**, não C-a [emenda: o modo de falha do E3 é *"Ollama de pé, `generate`
  falhando"*, e `Saude.Verifica` só chama `Versao` e `Residentes` — **200 nos dois** nesse caso; C-a fica
  verde **antes** das correções].

**D-4 · `Saude.ModelosExigidos` contra `/api/tags`**

- **ANTES** `grep -c 'api/tags' internal/cerebro/saude.go` → 0; `/api/tags` responde em 0,020 s e lista 9
  modelos, **cada um com `digest`** = identidade portável, sem sudo.
- **AÇÃO** `Cliente.Modelos(ctx)` + `Saude.ModelosExigidos` alimentado pelos modelos com tarefa **elegível**
  (A3). Ausente ⇒ `ErrPausado` "modelo X ausente no Ollama", **nunca `Falhar`**.
- **DEPOIS** prova C-b: pausa limpa em ≤60 s [D]; `estado='erro'` **inalterado**.
- **SE NÃO VIER** pausou com a fila vazia ⇒ está lendo `pendente` em vez de **elegível**.

**D-5 · D-6 · D-7 — o flock que nunca guardou nada, na ordem que não vira laço de boot**

- **ANTES, a prova estrutural instantânea**:
  ```bash
  stat -c 'inode=%i owner=%U mode=%a' /tmp/opt-wiki-agent-heavy.lock
  sudo -n nsenter -t "$(systemctl show wikijuridica-cerebro.service -p MainPID --value)" -m \
    stat -c 'inode=%i owner=%U mode=%a' /tmp/opt-wiki-agent-heavy.lock
  ```
  → inodes **diferentes** (host `39454263`, daemon `39739472`; namespaces mnt `4026531841` × `4026532461`):
  `saude.go:87` usa o caminho, `carga_linux.go:17-18` abre com `O_CREATE`, e a unit tem `PrivateTmp=yes` [M]
  ⇒ **o daemon cria o próprio lock no seu `/tmp` privado**.
- **D-5** `carga_linux.go` → `os.OpenFile(caminho, os.O_RDONLY, 0)`. **No mesmo commit e obrigatório**:
  `if errors.Is(err, fs.ErrNotExist) { return false, nil }` **antes** do `return false, err` — sem isso
  `ENOENT` vira `ErrPausado` **eterno**, e o prefixo `-` do D-7 faz reincidir a cada boot. Teste com caminho
  inexistente exigindo `(false, nil)`.
- **D-6** `ops/tmpfiles.d/wikijuridica-agent-heavy-lock.conf` com **uma** linha
  `f /tmp/opt-wiki-agent-heavy.lock 0644 rafael rafael -` (casa o `rafael 644` medido). Instalar **por
  SYMLINK**, não cópia (`/etc/tmpfiles.d/cpu-energia.conf` é **cópia** — é a deriva invisível que o contrato
  manda evitar): `sudo -n ln -sf /opt/wiki/ops/tmpfiles.d/…  /etc/tmpfiles.d/` e
  `sudo -n systemd-tmpfiles --create /etc/tmpfiles.d/wikijuridica-agent-heavy-lock.conf`.
  Existe porque `/usr/lib/tmpfiles.d/tmp.conf` traz `D /tmp 1777 root root -`: **esvazia `/tmp` no boot**.
- **D-7** em `[Service]`, **mantendo `PrivateTmp=true`** (fonte primária `src/core/namespace.c`, systemd
  **252.39-1~deb12u2**: bind mounts **convivem** com `PrivateTmp`), acrescentar
  `BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock` — o `-` é o que impede o laço se o arquivo faltar.
  **No mesmo passo**: `daemon-reload` + `restart`.
- **DEPOIS** os dois `stat` devolvem o **MESMO inode** ; `NeedDaemonReload=no`.
- **E um DETECTOR CONTÍNUO, senão a guarda volta a ser muda** [emenda: basta o arquivo não existir no instante
  do start para o bind ser pulado **em silêncio** — é o que o `-` faz — e o daemon voltar ao estado de hoje;
  a prova C-f é pontual e nada detecta a recaída]: o batimento (A4) grava `lock_pesado_inode` (um `stat`,
  custo zero) e o gate A5 **reprova** quando ele é 0 ou **diverge do inode do host**.
- **SE NÃO VIER** `226/NAMESPACE` ⇒ o arquivo não existe no host: volte ao D-6. **Inverter D-6 e D-7 é laço
  de boot.** `ENOENT` virando pausa eterna ⇒ a cláusula do D-5 não entrou.
- **ROLLBACK** para frente (apagar a linha + `daemon-reload` + `restart`). A unit é **symlink**: a edição já
  muda o que o systemd lê, e **ninguém avisa que caiu** — por isso o DEPOIS é no mesmo passo.

**D-8 · `StartLimitIntervalSec` em `[Unit]`, e quem tira do `failed`**

- **ANTES** `10s` / burst `5` / `RestartUSec=15s` [M]: com 15 s entre partidas, **nenhuma janela de 10 s tem
  duas partidas** ⇒ burst **inalcançável** ⇒ `failed` **nunca** ⇒ `OnFailure` é **decoração**. Precedente:
  **87 restarts** da rede social em produção, sem alerta.
- **AÇÃO** em **`[Unit]`** (em `[Service]` o systemd **ignora em silêncio** — só `systemctl show` revela):
  `StartLimitIntervalSec=300` e `StartLimitBurst=5`. Com `RestartSec=15`, 5 partidas custam ~75 s [D] ⇒ cabem
  em 300 s ⇒ **`failed` alcançável**.
  **Recuperação NOMEADA, não deixada em aberto**: `failed` dá **alerta**, não recuperação; o ramo de reparo
  vai em `check-portal-health --repair` (timer de 2 min) — vendo `ActiveState=failed` há >10 min e
  `cerebro_restart_loop=false`, executa
  `sudo -n systemctl reset-failed wikijuridica-cerebro.service && sudo -n systemctl start …`, **no máximo
  1×/hora**, gravando nas **chaves próprias** do A8. (`sudo -n -l` = `(ALL) NOPASSWD: ALL` [M].)
  **E `tools/deploy-cerebro` ganha `sudo -n systemctl reset-failed "$UNIT" || true` ANTES do `restart`, no
  mesmo commit** — senão dois deploys em 5 min batem no limite novo.
- **DEPOIS** `systemctl show … -p StartLimitIntervalUSec -p StartLimitBurst` → `5min` e `5`.
- **SE NÃO VIER** continuar `10s` ⇒ a diretiva foi para `[Service]`.
  `Failed to restart: start request repeated too quickly` **depois de um deploy é o limite funcionando, não
  defeito**: `reset-failed` e repita.

**D-9 · `Type=notify` + `WatchdogSec` + `TimeoutStartSec` — binário ANTES da unit**

- **AÇÃO (i)**, em `cmd/cerebro/main.go`: `sdactivation.NotificaPronto()` **depois de `Abrir`+`Recuperar`**
  (o daemon está pronto quando a fila abriu, não quando o Ollama respondeu — ver D-1), e
  `NotificaWatchdog()` **nos mesmos dois call sites do batimento**, dentro de `Worker.Passo`, **nunca** de
  goroutine com ticker cego (que continuaria batendo com o worker travado). Subir por `deploy-cerebro`
  **antes** de tocar a unit. (Antecipar (i) é **grátis**: `NotificaPronto()` sob `Type=simple` é **no-op**,
  `notifica` devolve `(false,nil)` sem `NOTIFY_SOCKET`.)
- **AÇÃO (ii)**, só então, em `[Service]`: `Type=notify`, `WatchdogSec=1500`, **`TimeoutStartSec=300`**.
  · **1500 s [D]**: 5 sondas × `--saude-prazo 20s` (100) + `prazoDoLote` 900 + escrituração/backoff (~30)
  ≈ **1.030 s**, com 45% de folga. Baixar para ~450 s exigiria bater por **tarefa** dentro do extrator
  (uma chamada ao Ollama **por tarefa** [M]), mudando a assinatura de `Executor` nos 4 executores — fica
  registrado como **refinamento com o custo nomeado**, não prometido.
  · **`TimeoutStartSec=300`**: com `Type=notify` o default de 90 s governa o prazo do `READY=1`, e o tempo de
  boot **não foi medido** (a linha já rotacionou do journal); 300 s evita que a 1ª partida estoure e
  **queime uma vaga do burst**.
- **DEPOIS** `Type=notify`, `WatchdogUSec=25min`, `TimeoutStartUSec=5min`, `NRestarts` sem crescer em 30 min.
- **SE NÃO VIER** `Job … timed out` na partida ⇒ `READY=1` não saiu: volte a `Type=simple` (edição para
  frente + `daemon-reload`) e conserte o **binário** antes de reinsistir.
- **D-10** (mesma edição): corrigir o cabeçalho da unit, que ainda diz `MemoryMax=15G` e
  `MAX_LOADED_MODELS=1` contra `12G`/`2` no drop-in vivo [M]. Parágrafo superado ganha data e motivo.

**D-11 · AS SETE PROVAS NEGATIVAS**

Regra comum: **C-a, C-b, C-d, C-e, C-g** em **unit VOLÁTIL** com cópia da fila e `--root` de ensaio, com o
worker de produção **parado explicitamente** (`stop` é limpo: `Restart=` não se aplica e `OnFailure` não
dispara). **C-c** é a única segura contra produção. **C-f roda contra a unit de PRODUÇÃO**, depois do D-7
[emenda: o molde `systemd-run` **não tem `PrivateTmp`**, então o volátil veria o `/tmp` do host, o lock seria
o mesmo inode e a pausa aconteceria **hoje**, com o defeito intacto — falso positivo por construção].

**Molde** [emenda: `-p StartLimitIntervalSec=300 -p StartLimitBurst=5` são obrigatórios, senão a volátil
herda o StartLimit do **manager** (10 s/5) e **reproduz o baseline**, fazendo o operador concluir que D-8
falhou]:
```bash
sudo -n systemd-run --unit=cerebro-prova --collect -p Restart=always -p RestartSec=15 \
  -p StartLimitIntervalSec=300 -p StartLimitBurst=5 -p 'OnFailure=prova-alerta@%N.service' \
  -p User=rafael -p WorkingDirectory=/opt/wiki \
  /opt/wiki/bin/cerebro servir --root <ensaio> --fila <copia> --worker prova-1
systemctl show cerebro-prova -p StartLimitIntervalUSec   # PRIMEIRO comando depois de subir: tem de ser 5min
```
**A cópia da fila é por `VACUUM INTO`** (ou os três arquivos WAL com o worker já parado) + `PRAGMA
integrity_check` **antes** de subir a volátil [emenda: `cp` do arquivo principal sem `-wal` dá cópia
incompleta, `Abrir` falha, e a volátil entra em laço **sem alerta nenhum**].
**O `--root` de ensaio é symlink SOMENTE-LEITURA de `content/` e `data/corpus/`, com `data/ai/` e
`data/ops/` próprios** [emenda: `resolve()` confere **só** `content/pages.json`, mas `servir` lê do `--root`
`CarregaAcervo`, `content/cerebro_publicacao.json`, `content/site.json`, política de habitualidade, ledger de
publicações e `NovoExtrator(c.root)`; ensaio incompleto **passa** o resolve e falha depois, em laço mudo.
**E `data/ai` do ensaio NUNCA aponta para o de produção**: o executor gravaria `ativo.json` e **dispararia a
`.path` que reinicia o servidor**]. DEPOIS do A10: `./bin/cerebro status --root <ensaio> --somente-leitura`
saindo 0 **antes** de qualquer volátil subir.

| prova | ação | DEPOIS esperado |
|---|---|---|
| **C-a** Ollama cai | `sudo -n kill -9 $(systemctl show ollama.service -p MainPID --value)` — **nunca `stop`**, que não aciona `Restart=` | pausa "ollama fora do ar" ≤60 s; **`executando==0` e `pendente` de volta** (D-2); Ollama volta em ~3 s |
| **C-b** modelo removido | `ollama cp qwen3.5:4b …backup` **antes**, depois `ollama rm` | pausa "modelo ausente" ≤60 s; **par `(estado, tentativas)`** parado; janela **>15 min** ou `--backoff 5s --tentativas 1` |
| **C-c** `kill -9` no worker (**única segura em produção**) | `kill -9 $(systemctl show wikijuridica-cerebro.service -p MainPID --value)` | journal capturado **imediatamente** com "N tarefas recuperadas"; **`NRestarts` delta +1** medido logo antes, nunca o literal "1→2" |
| **C-d** `kill -STOP` | suspender por **MENOS** que `prazo_do_lote_s` (900 s) | `State: T (stopped)` com `systemctl` dizendo `active (running)`; gate A5 reprova em ≤1.236 s; **restart por watchdog em ≤29 min, NÃO `failed`** |
| **C-e** fila corrompida | `dd if=/dev/zero of=<copia> bs=1 seek=0 count=4 conv=notrunc` (CABEÇALHO de **cópia**) | `failed` em ~75 s [D] e **linha nova no ledger de alerta** — leia o **ledger**, não `systemctl status` (o `--collect` descarta a unit ao falhar) |
| **C-f** segurar o flock | **contra PRODUÇÃO**, depois do D-7: `timeout 120 flock -x /tmp/opt-wiki-agent-heavy.lock tail -f /dev/null &`, com aviso prévio por `generate-coord-message` | pausa "lock pesado tomado" ≤120 s. **Baseline de hoje: NADA acontece** [M] |
| **C-g** teto a 1 byte | volátil com `--teto-bytes-residentes 1` (exige A9) | pausa no 1º ciclo com "…somando 3,01 GiB, acima do teto de **0.00 GiB**" — **ponto decimal**, e a mensagem termina em `(incidente de 2026-09-08 12:04:53, CLAUDE.md paragrafo 12): %s` |

**C-d é restart, não `failed`, e o canal de alerta é outro** [emenda: um timeout de watchdog custa
`WatchdogSec` (1500) + escalada SIGABRT→SIGKILL limitada por `TimeoutStopSec=240` [M] — e processo em SIGSTOP
**não atende SIGABRT**, logo a escalada é a regra: até **1.740 s por ocorrência**; `failed` exigiria 5
partidas em 300 s, o que levaria **~2 h 6 min**. O canal do congelamento é o **gate A5 (≤1.236 s)** e o
**`cerebro_nrestarts_delta` (A8)**, escrito como tal].

**A volátil usa alvo e chave de alerta PRÓPRIOS, com prefixo `prova-`, e o último passo de C-e resolve a
chave** [emenda: `OnFailure=wikijuridica-alerta@%N` grava `--chave 'unit-falhou-cerebro-prova'` com evidência
`systemctl status cerebro-prova` — e o `--collect` **já descartou a unit**: `wikijuridica-alertas-abertos`
carregaria esse alerta **indefinidamente**, sem ninguém poder fechá-lo].

**C-h · Registrar as sete** em `.agents/runtime/prova-fila/<carimbo>/provas.jsonl` com
`prova, antes, acao, depois, esperado, obtido, veredito` — é o que impede a próxima sessão depender de prosa.
**E conferir `tools/list` por loopback antes e depois de C-a** [emenda: `buscar_semantico` fala com o Ollama
e a decisão de anunciá-la é tomada **no BOOT**; durante o outage as chamadas falham, e se algo reiniciar o
servidor na janela, a ferramenta **desaparece** do canal de máquina até o próximo restart, sem alerta].

**D-12 · P10: tirar a máscara sem inundar o dono**

- **ANTES, censo medido por mim agora**: **22** diretivas `SuccessExitStatus` não comentadas e
  **DEZ** units com `ExecMainStatus=1` **e** `Result=success` [M] — **não nove**: à lista do runbook
  (`alertas-abertos`, `daily-content`, `daily-content-noticias`, `efeito-nos-bots`, `untracked-inventory`,
  `corpus-oraculo-recoleta`, `fontes-alcancaveis`, `qualidade-diaria`, `qualidade-longa`) soma-se
  **`wikijuridica-bot-telemetry`**.
- **O DISCRIMINADOR É OUTRO** [emenda: "tem canal próprio (`grep notify-owner`)" mede a coisa ao lado, e o
  baseline "exatamente 4 silenciosas" é **erro do instrumento**. Em 3 das 4 a escalada está escrita no código
  e é o **exit 2 NÃO mascarado** — `run-qualidade-diaria:299-300` diz literalmente *"Este exit 1 NAO alerta o
  dono: a unit declara SuccessExitStatus=1, entao o OnFailure so dispara em exit 2"*, e
  `wikijuridica-corpus-oraculo-recoleta.service:41-43` diz *"Exit 1 = o gate ficou vermelho, que é o PRODUTO
  desta unit … Exit 2 = algum canal oficial falhou e ISSO chega ao dono"*].
  **Discriminador adotado, verificável por grep**: *a máscara é legítima quando existe um exit **não
  mascarado** que alcança `OnFailure` e o código o emite* — `grep 'exit 2'` no ExecStart **e** ausência do 2
  na máscara.
- **DEPOIS** sob essa régua, as 4 "silenciosas" **saem da lista** e sobra `check-fontes-alcancaveis` como
  único caso real.
- **E `qualidade-diaria`/`qualidade-longa` SAEM DO PILOTO** [emenda: trocar `=1` por `=0 4` põe **as duas** em
  `failed` na próxima passada e dispara alerta **DIÁRIO** até os **12 gates vermelhos** de hoje ficarem
  verdes — `data/ops/qualidade_diaria.jsonl` de 2026-09-15 lista 12, entre eles `binario-vs-fonte`. É a
  enxurrada que o bloco D existe para evitar, e `test_notify_owner_mordaca.sh` existe para travar. A partição
  delas **já está correta**: 1 = veredito, 2 = não rodou, e o 2 **não** é mascarado].
- **TRÊS códigos, não dois** [emenda: a partição de dois ignora o **terceiro** significado que o exit 1 já
  tem — `nao_medidos` (relógio/exit 124 e infra ausente/`EX_TEMPFAIL 75`), e sem casa para ele todo dia com
  um "infra" viraria alerta]: **4** = nível conhecido (estoque, nenhuma entrada nova desde a linha datada) ·
  **75** (`EX_TEMPFAIL`, já usado no repo) = não medido · **1** = **regressão nova**. **3 está tomado** com o
  sentido "catálogo remoto indisponível" em `check-api-catalog-usage` [M].
- **ORDEM por raio de dano**: (1) `check-fontes-alcancaveis` (timer curto, menor raio) — e **o veredito se
  verifica na hora** rodando a ferramenta à mão e por **mutação na fixture** (injetar entrada nova ⇒ exit 1);
  o ciclo de timer serve só para provar que a unit não vai a `failed` no agendamento real. **Atalho para não
  esperar 24 h**: `sudo -n systemctl start <unit>.service` roda **AGORA** com o `SuccessExitStatus`,
  `OnFailure`, `flock` e `Nice` reais, e `systemctl show -p Result -p ExecMainStatus` dá o veredito em
  segundos.
- **DEPOIS** `./tools/check-mascara-de-exit` → 0, 22 classificadas, **0 silenciosas** ;
  `./tools/check-units-alarme` → 0 ; `./tools/test_units_alarme.sh` verde ; `NeedDaemonReload=no`.
- **SE NÃO VIER** unit indo a `failed` depois ⇒ a ferramenta devolveu 1 **de verdade**: **leia a saída antes
  de recolocar a máscara**.

**D-13 · P12: migração para a RTX 5060 Ti — os quatro bloqueios, na ordem em que mordem**

**Portão**: D-2 (com `Devolver`) + D-3 no binário vivo e **prova C-b verde**.
**Reconciliação medida** [M]: o bloqueio #3 do plano (*"Debian trixie tem 550.163, nenhum repo serve"*) está
**superado neste host** — `/etc/debian_version` = **12.15 bookworm**, o repo CUDA da NVIDIA para debian12
**já está** em `sources.list.d` com chave em `/usr/share/keyrings/`, e `nvidia-kernel-open-dkms` tem candidato
**615.71.09-2**. **Não há credencial nova nem cadastro**: é repositório apt. O pacote instalado é **errado por
classe, não por versão**: Blackwell (GB206/sm_120) exige os **módulos open**, e `nvidia-kernel-dkms`
(proprietário) não serve em versão nenhuma. **NÃO MEDIDO**: por que `dkms status` está vazio neste laptop —
a GPU atual é MX110/Maxwell, sem suporte no 610.x; pode ser isso, pode ser header ausente. Irrelevante para o
alvo: **E2 replica o apt e mede LÁ**.

- **E1 BASELINE PAREADO ANTES de desligar a máquina velha.** `tools/medir-baseline-gpu` grava
  `ollama --version`, os **9 `digest`** de `/api/tags` (identidade portável, sem sudo, sem ler blob), N=30
  saídas de `medir-prompt-sumula-pareado` a **temperatura 0** classificadas por `cerebro.URNDaCitacaoPublica`,
  e prefill/decode tok/s **com o `loadavg` declarado ao lado de cada número**. Sem baseline, "o mesmo modelo
  nas duas máquinas" é **fé**.
- **E2 driver.** `nvidia-smi; echo $?` **SEM pipe** — `nvidia-smi | head; echo $?` imprimiu **0** com o
  comando falhando, exit real **9** (erro meu nesta sessão, virou regra); `dkms status` com linha para o
  kernel em execução; `ls /proc/driver/nvidia`; `nvidia-smi --query-gpu=name,memory.total --format=csv` →
  `NVIDIA GeForce RTX 5060 Ti, 16384 MiB`. **SE NÃO VIER**: candidato <570.26 ⇒ repo errado; `dkms` vazio ⇒
  falta `linux-headers-$(uname -r)`; `nvidia-smi` ≠0 com dkms ok ⇒ Secure Boot (`mokutil --sb-state`).
- **E3 runner.** Remover `LLM_LIBRARY=cpu` **não basta**: `grep -c sm_120` dá **8** em `cuda_v12` e **0** em
  `cuda_v13` (PTX puro), então `OLLAMA_LLM_LIBRARY=cuda_v12` explícito. **O cérebro está parado neste passo.**
  DEPOIS: `/api/ps` com **`size_vram > 0`** (hoje **0** [M]).
- **E4 flash attention × `num_ctx` (ollama#18232).** O drop-in vivo tem `FLASH_ATTENTION=1` **e**
  `CONTEXT_LENGTH=8192` — **4× o contorno publicado (2048)**. Um `generate` com 8192 **esperando a falha**
  (`cudaFuncSetAttribute`/shared memory), para **datar** o bloqueio neste host; depois 2048. **Não desligar
  `FLASH_ATTENTION`**: sem ele `KV_CACHE_TYPE=q8_0` degrada para f16 **em silêncio** e o KV dobra. Se 8192
  **funcionar**, grave a evidência e **não** baixe o contexto.
- **E5 a guarda vira DUAS contas, derivadas em RUNTIME** (não por coordenação de commit — um é leve, outro
  pesado): se **todo** residente tem `size_vram == 0` ⇒ regime CPU, `sum(size) <= 9 GiB`; se **algum** tem
  `size_vram > 0` ⇒ regime GPU, `sum(size_vram) <= 13 GiB` **e** `sum(size - size_vram) <= 2 GiB`.
  **O predicado "`size_vram < size`" como sinal de spill pausaria o cérebro HOJE para sempre**: em CPU puro é
  verdadeiro em **todo** residente [M]. Três casos de teste: CPU de hoje (3,01 GiB, vram 0) ⇒ **passa**; par
  do incidente (14b+9b=16 GB em RAM) ⇒ **barra**; GPU com 14 GiB em VRAM ⇒ **barra**.
- **E6 o piso de determinismo, em duas partes** — temperatura 0 CPU→GPU **não** é byte-idêntico (kernel e
  ordem de acumulação mudam), e exigir igualdade seria um piso impossível que alguém desligaria:
  (1) **auto-consistência N/N em cada máquina** (3 repetições da mesma entrada ⇒ saída idêntica) — **tem** de
  ser 100%; (2) **paridade de classificação** por `URNDaCitacaoPublica` ⇒ mesmo conjunto de URNs em **≥29 de
  30**, com cada divergência lida à mão. Identidade: `ollama --version` fixado em **0.33.3 por tarball
  versionado** e os **9 `digest`** idênticos aos de E1.
- **E7 ganho medido, não prometido.** A projeção de terceiros (prefill 74–130×, decode 17–23×, k de
  0,648/0,660 na própria 5060 Ti contra 0,44 da 4090) entra como **expectativa citada**, nunca como medição
  nossa. E **todo tok/s de CPU medido é TETO INFERIOR**: as varreduras levaram o `loadavg` a 15,84, o teto
  `--carga-max 12` mordeu e o decode caiu de 5,6 para 3,0.
- **E8 custódia do `ops/ollama`** — a lacuna que morde justo nesta frente: `check-units-instaladas` olha
  **só** `ops/systemd`; o drop-in do Ollama é symlink e idêntico hoje, mas **nada acusa** se virar cópia ou
  ficar com reload pendente, e P12 é a frente que **reescreve esse arquivo**. Estender para
  `ops/ollama/ollama.service.d/` e `ops/tmpfiles.d/`, com as mesmas regras (symlink, conteúdo idêntico,
  `NeedDaemonReload=no`).

---

## §4 · VERIFICAÇÃO AO VIVO DA PRODUÇÃO — o procedimento único

**Roda-se DEPOIS de qualquer ação que toque o acervo**, em todos os cinco runbooks. É o `check-publicado-no-ar`
(I-1) mais estas cinco leituras à mão quando o gate reprova e é preciso saber **onde**.

```bash
UA='Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)'
S=(-sS -A "$UA" -H 'X-Warming-Request: true' --max-time 25)
R=/jurisprudencia/stf-adi-4376/          # troque pela rota alvo
```

| # | camada | comando | veredito |
|---|---|---|---|
| 0 | **processo** | `curl "${S[@]}" "http://127.0.0.1:8089/api/v1/lote?limite=1"` → `fim.total` × `wc -l published_manifest.jsonl` ; `systemctl show wikijuridica-server -p ExecMainStartTimestamp` × mtime do HTML | divergiu ⇒ **`go_desatualizado`**: reinicie **pela cadeia**; NÃO republique, NÃO purgue |
| 1 | **oráculo** | `curl "${S[@]}" "http://127.0.0.1:8089/api/v1/citar$R"` → `html_sha256`, `markdown_sha256` | é a verdade do **manifesto**; **`:8089`, nunca `:8088`** (lá há `wj_dyn` com `s-maxage=3600`) |
| 2 | **disco** | `sha256sum "public${R}index.html"` | ≠ oráculo ⇒ manifesto e disco divergem: **republicar**, não reiniciar |
| 3 | **origem** | `curl "${S[@]}" "http://127.0.0.1:8088${R}index.md"` × `:8089` | divergiu ⇒ **`origem_cacheada`**: `purge-origin-cache`, **restart não conserta**. Prova **por CORPO**: `:8088` **não emite** `X-Cache` nem `Age` [M] |
| 4 | **borda HTML** | `curl "${S[@]}" -D /tmp/h "https://wikijuridica.com.br$R" \| grep -o '"datePublished":"[^"]*"'` ; `grep -iE 'cf-cache-status\|^age' /tmp/h` | prova **por CORPO**: `Last-Modified` é a data **editorial** e não muda (`304` com `If-Modified-Since`, `200/20.584 B` sem) [M] |
| 5 | **borda `.br`** | o mesmo com `-H 'Accept-Encoding: br'` | sem isto o `curl` lê o `identity` e passa **verde** enquanto o bot recebe o corpo antigo |
| 6 | **gêmea (HEAD)** | `curl "${S[@]}" -I "https://wikijuridica.com.br${R}index.md" \| grep -i etag` × `markdown_sha256[:32]` | **N1** — parem por cabeçalho, sem baixar corpo |
| 7 | **variante `Accept`** | `curl "${S[@]}" -H 'Accept: text/markdown' "https://wikijuridica.com.br$R"` | **terceiro objeto de cache** (`vary: Accept-Encoding, Accept`), que ninguém sonda hoje |
| 8 | **MCP** | `POST /mcp` `tools/call ler_pagina`, com `Accept: application/json, text/event-stream` | responde **sem** `initialize`; JSON na linha `data: ` |
| 9 | **A2A** | `POST /a2a/v1` `SendMessage`, com header **`A2A-Version: 1.0`** | sem o header, `-32009`; o método **não** é `message/send` |

**O estado de hoje, que é o controle negativo do instrumento** [M, 2026-09-15 22:5x -03]:
```
:8089 /api/v1/citar   html_sha256=ed329c6e…  markdown_sha256=b0ccb5c9…
disco                 sha256=ed329c6e…                       BATE
:8089 gemea           sha256=b0ccb5c9…  date_published 2026-09-15   BATE
borda gemea           sha256=f4fe9c65…  etag "f4fe9c65…"  age 2232  HIT  date_published 2026-09-11   NAO BATE
```
**Amostra por stride determinístico, medida por mim com o próprio instrumento do N1 (só `HEAD`):
`10 de 10 divergem`, sobre as 875 rotas de `/jurisprudencia/` com `approved_at=2026-09-15`** — amostra, **não
população** (o crítico mediu 13 de 13 em amostra independente ⇒ **[M×2]**, dois conjuntos disjuntos, nenhuma
coincidência). O agente que confere o `markdown_sha256` que **nós** publicamos recebe **mismatch, agora** — e
é o §12 do contrato, que chama isto de produto. **De quebra, esta medição é o controle positivo do I-1**: o
predicado por `ETag` detectou a divergência em 10 de 10 **sem baixar um único corpo**. Mecanismo: gêmea sai com `s-maxage=604800` e **ninguém a purga** (o `--purge-targets` é cego à
data; a purga interna do publicador é por **tag de área e URL de página**, e `--url /rota/` **não casa**
`/rota/index.md`).

**Sequência quando algo diverge, e ela não se inverte:**
`disco ≠ oráculo → republicar` · `origem ≠ oráculo → purge-origin-cache` ·
`borda ≠ origem → purge-edge-cache dirigida + warm` · `superfície de máquina 404 com rota no disco →
reload-wiki-server`. **Reiniciar por causa de TTL é o erro que o instrumento existe para não deixar acontecer.**

---

## §5 · A OBSERVAÇÃO DOS BOTS DE IA

### O que se mede, em qual série, com qual granularidade

| série | granularidade | lag | o que só ela responde |
|---|---|---|---|
| `/var/log/nginx/wikijuridica/access.log` | requisição | **ZERO** | tudo que **tocou a origem**; retenção real **30 dias** |
| `data/ops/access/nginx-AAAA-MM-DD.jsonl` | requisição, derivada | ≤ 1 h (timer) | bucketiza por **UTC** — "hoje" local atravessa **dois** arquivos |
| `crawl_coverage_state.crawlers_verified.<bot>.paths_first_seen` | rota × bot | ≤ 24 h (timer 01:11), **mas roda sob demanda** | **leitura que a origem NUNCA vê** — gptbot: **686 rotas lá contra 0 na origem** no mesmo lote |
| `data/ops/edge_bot_agents_daily.jsonl` | dia × agente, **CUMULATIVO** | diário | volume na borda. **Ler a ÚLTIMA linha por `date`, chave `requests_estimated`** — **somar infla até 2.045.285×** |
| Cloudflare `httpRequestsAdaptiveGroups` | — | — | **retenção dura de 8 dias**, do operador |

### Os comandos, com as armadilhas embutidas

```bash
LOG=/var/log/nginx/wikijuridica/access.log
H=$(LC_ALL=C date -d '60 min ago' '+%d/%b/%Y:%H')
for b in GPTBot PerplexityBot ClaudeBot OAI-SearchBot ChatGPT-User Googlebot bingbot Applebot Amazonbot; do
  printf '%-16s %s\n' "$b" "$(LC_ALL=C grep -a "$H" "$LOG" | grep -c -i "$b")"
done
LC_ALL=C grep -a "$H" "$LOG" | grep -iE 'GPTBot|PerplexityBot|Applebot' | grep -c 'warm=-'   # trafego REAL
LC_ALL=C grep -a 'redesocial/tema' "$LOG" | grep -c ' 404 '                                   # o dano do P-0.5
nice -n 19 python3 tools/measure-crawl-coverage      # SOB DEMANDA (GraphQL), nao espera o timer de 01:11
python3 tools/edgetelemetry.py serie_saneada          # ultima linha por dia, nunca a soma
```
- **`LC_ALL=C` é obrigatório**: `date +%b` devolve `set` em pt_BR e o nginx escreve `Sep` — a comparação
  falha **em silêncio** devolvendo **zero**.
- **Contar LINHA (`grep -c`), nunca ocorrência (`grep -oE`)**: o UA do PetalBot casa **2×** por requisição.
- **O predicado de tráfego real é `warm=-`, NUNCA `warm=false`** [M: `ops/nginx/wikijuridica.conf:61` é
  `warm=$http_x_warming_request`, e cabeçalho ausente renderiza `-`; conferido em linhas reais de bot].
  Quem exigir `warm=false` lê **zero** e conclui que nenhum bot de IA está entrando — o inverso da verdade.
- **Ausência na origem NÃO é ausência**: com `s-maxage=604800` a maior parte do rastreio **nunca toca a
  origem**; a população está na camada de borda.
- O smoke do release tem `warming:false`: filtrar **só** por `warming` conta **898 requisições internas**
  como visita real — filtre também por `bot_class`.

### Leitura ao vivo desta sessão [M, janela `15/Sep/2026:22` local = 01h UTC]

```
Amazonbot 281 · Applebot 25 · bingbot 7 · GPTBot 6 · PerplexityBot 3 · ChatGPT-User 2 · OAI-SearchBot 1
ClaudeBot 0 · Googlebot 0 · e 21 requisicoes a /redesocial/tema/... -> 404
```
O **GPTBot aparecendo agora** é a confirmação ao vivo do histograma: **97% dos primeiros contatos dele caem
em 01h–02h UTC** (n=3.608), e são **01h UTC**.

### Latência real por agente, e a espera que é do terceiro

Pisos derivados do lote limpo de **898** rotas, camada de origem salvo indicação: `cloudflare-ai-search`
**p50 1,6 h** (897 de 898 = 99,9%) · `yandexbot` **p05 5 min** · `perplexitybot` **p50 22,6 h** ·
`petalbot` 75,4 h · `amazonbot` 100,7 h · **`gptbot` 0 na origem, 686 na borda**.
Histograma da hora UTC do **primeiro contato**: `gptbot` 97% em 01h–02h (n=3.608) · `perplexitybot` 67% em
14h–15h (n=5.865) · `cloudflare-ai-search` 68% em 15h–16h · `bingbot` pico 23h · `amazonbot` pico 19h.

**Os bots NÃO reagem ao anúncio — chegam em varredura agendada.** A onda publica ~**07h UTC**, contra a
varredura do gptbot às **01h UTC**: **18 h de espera AUTO-INFLIGIDA** no agente que mais rastreia.
**O atalho não é esperar: é mover a HORA DA PUBLICAÇÃO** — o `.timer` do oneshot dispara **antes de
01:00 UTC**, e a hora é a **variável de controle**.
`cloudflare-ai-search` pertence à **tabela** e **nunca à manchete**: é a própria CDN indexando o cliente
(UA `Cloudflare-AI-Search-External`, `ip_verificacao 'unverifiable'`).

**E o que se verifica enquanto a agenda do terceiro não chega, sem esperar nada:** as rotas entraram no
sitemap (bot não pede URL que não descobriu; "zero 404 no lote" **não** limita a publicação); o IndexNow saiu
com `ownership_proof_verified_over_http true`; `measure-crawl-coverage` rodou **sob demanda**; e o smoke do
release já provou **898 de 898 rotas em 15 s**, com precisão de **segundo**.

---

## §6 · A OBSERVAÇÃO DO CÉREBRO

### O conjunto mínimo que responde em segundos

```bash
systemctl show wikijuridica-cerebro.service -p ActiveState -p SubState -p NRestarts \
  -p Type -p WatchdogUSec -p StartLimitIntervalUSec -p RestartUSec -p PrivateTmp
curl -sS --max-time 8 http://127.0.0.1:11434/api/ps   | python3 -m json.tool | head -20
curl -sS --max-time 8 http://127.0.0.1:11434/api/tags | python3 -c 'import sys,json;[print(m["name"],m["digest"][:12]) for m in json.load(sys.stdin)["models"]]'
./bin/cerebro status --root /opt/wiki --somente-leitura          # depois do A2; NUNCA `cerebro status` sem a flag
/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3 "file:$PWD/data/ai/fila.sqlite?mode=ro" \
  ".timeout 5000" "SELECT tipo,estado,COUNT(*) FROM tarefa GROUP BY 1,2 ORDER BY 3 DESC;"
python3 -c "import json;d=json.load(open('data/ops/cerebro_batimento.json'));print(d['estado'],d['pausa_motivo'],d['pendentes'],d['elegiveis_agora'],d['prazo_do_lote_s'],d['lock_pesado_inode'])"
cat /proc/loadavg
```
**Esperado hoje** [M]: `active/running`, `NRestarts=1`, `Type=simple`, `WatchdogUSec=0`,
`StartLimitIntervalUSec=10s`, `PrivateTmp=yes`; residente `qwen3.5:4b` **3.227.894.413 B**, `size_vram=0`,
`context_length=8192`; 9 modelos com `digest`.
**Declare a carga junto de qualquer tok/s**: `CargaMax=12` **mordeu** nesta sessão (loadavg 12,77 medido pelo
bloco DAEMON, 15,84 durante varreduras) — **tudo medido sob carga é TETO INFERIOR**.
`sqlite3` desta máquina está em `/home/rafael/android-vm-lab/…` e **unit ou gate com `PATH=/usr/bin:/bin`
não o acha** — ferramenta de verdade usa `modernc.org/sqlite`, já no `go.mod`.

### As sete provas negativas

Roteirizadas no **D-11**, com o molde de unit volátil (que **precisa** de
`-p StartLimitIntervalSec=300 -p StartLimitBurst=5`), a cópia da fila por `VACUUM INTO` + `integrity_check`, e
o `--root` de ensaio com `data/ai` **próprio** (senão o executor grava `ativo.json` e **dispara a `.path` que
reinicia o servidor**). Resumo dos vereditos:

| prova | o que se prova | baseline de HOJE |
|---|---|---|
| C-a Ollama cai | pausa limpa, **`executando==0`**, `tentativas` parado | a fila perde 3 tarefas por outage (**D-2**) |
| C-b modelo removido | par `(estado, tentativas)` parado; janela **>15 min** | fila inteira em `erro` em ~30 min |
| C-c `kill -9` no worker | "N tarefas recuperadas"; **delta de `NRestarts` +1** | já funciona |
| C-d `kill -STOP` | **restart por watchdog ≤29 min**, e alerta pelo **gate A5 (≤1.236 s)** | `active (running)` **para sempre** |
| C-e fila corrompida | `failed` ~75 s + **linha no ledger de alerta** | `activating/auto-restart` eterno, **zero alerta** |
| C-f flock pesado (**produção**, pós-D-7) | pausa "lock tomado" ≤120 s | **NADA acontece** — inodes 39454263 × 39739472 [M] |
| C-g teto a 1 byte | pausa no 1º ciclo, "acima do teto de **0.00 GiB**" | **não executável** (falta A9) |

Cada uma grava linha em `.agents/runtime/prova-fila/<carimbo>/provas.jsonl` com
`prova, antes, acao, depois, esperado, obtido, veredito`, e `tools/list` por loopback é conferido antes e
depois de C-a.

---

## §7 · AS ESPERAS LEGÍTIMAS

Só entra aqui o que tem **causa física externa** e **número medido**. Tudo o mais tem instrumento.

| espera | número | por que é externa | atalho |
|---|---|---|---|
| **TTL da borda no acervo** | `s-maxage=604800` = **7 dias**; medido `HIT age 33.551` [M] | Cache Rule da Cloudflare, honrando o header da origem | **purga dirigida** (`--teto-por-url` = tamanho da lista) + `warm-edge-cache --rps 12`; verificação **imediata** por **CORPO**. Rota **nova** não espera nada: `MISS` na 1ª leitura |
| **TTL da zona `wj_dyn` na origem** | `s-maxage=604800` na gêmea, **3600** em `/api/v1/*` [M] | nosso nginx, mas é TTL | `purge-origin-cache`; e o oráculo **sempre** em `:8089`, que não tem cache |
| **Agenda de varredura de terceiro** | gptbot **97% em 01h–02h UTC** (n=3.608) · perplexitybot 67% em 14h–15h · cloudflare-ai-search 68% em 15h–16h | calendário de outro operador; o bot **não reage ao IndexNow** | **mover a HORA DA PUBLICAÇÃO** — `.timer` do oneshot antes de 01:00 UTC. A onda às 07h UTC são **18 h auto-infligidas** |
| **Retenção do `httpRequestsAdaptiveGroups`** | **8 dias**, duro | limite do operador | **nenhum** — e é o **único** sem atalho. O que existe é não depender dele: origem guarda 30 dias e `edge_bot_agents_daily` já tem a série no disco |
| **Crawl-Delay do STJ** | **10 s**, declarado no `robots.txt`; 392 competências ⇒ **3.920 s ≈ 67 min** [**DERIVADO** de supor 52 meses × 6 datasets nunca coletados] | teto do operador; acelerar seria desrespeitar o `robots.txt` | **inverter a ordem**: a extração roda **antes** e entrega **81,4%** do ganho sobre os 60.221 registros já no disco; e a coleta vai em **8 execuções retomáveis**, uma por dataset |
| **Vazão do modelo na CPU** | 43,6 s/tarefa sob a carga de hoje ⇒ baseline de 60 chamadas ≈ **44 min** | banda de memória, 4 núcleos, ~18 GB/s | a **carga** é a variável: `check-load-headroom --max 12` antes ⇒ ~29 s/tarefa ⇒ **~29 min** |
| **Boot do processo Go** | **32 s** e **23 s** medidos; teto do script 90 s | carrega ~11 mil páginas e monta as superfícies de máquina em `New()` | `reload-wiki-server` espera **por PREDICADO**, nunca por relógio, e re-mede depois |
| **Retomada do Ollama após `kill -9`** | ~**3 s** (`Restart=always`, `RestartSec=3s`) | unit de terceiro | nenhum necessário |
| **Carência de shard de sitemap** | `pages-0095` vence **2026-09-16 07:50Z**; 6 em carência, 0 vencidos [M] | prazo do nosso próprio registry | **NÃO é espera, é restrição** (**N3**): publicar **não** renova; rodar o sweep **a partir de 07:50Z** e **nenhum reinício** entre 07:50Z e a varredura |

**Janelas que restringem COMMIT, não medição** (não são esperas — são os 6 relógios da **N2** mais a onda):
`qualidade-longa` 02:11 (34 min) · `official-source-url-inventory-refresh` 04:22 (2 min) ·
`daily-content` 04:31 · `qualidade-diaria` 04:47 (61 min) · `sitemap-shard-grace` 05:19 ·
`noticias-coleta` 07:15/11:50/16:20/21:50 (14 s) · `stj-acordaos-coleta` 09:51 (+20 min de jitter, ~17 min) ·
`daily-content-noticias` 12:20 · `qualidade-race` dom 03:43 (teto **5 h**) · `corpus-oraculo-recoleta` seg 04:19.
**Atalho**: `flock -w 5400` **bloqueia sem spin**, e commit de **dado/doc** é leve e não paga o lock.

**O que NÃO é espera e por isso não entra:** a drenagem da fila do cérebro (34.217 × 43,6 s = **17,3 dias**,
ou 11,5 dias na taxa de 168 h) são **dois TETOS SUPERIORES**, não previsões, e **não são portão de passo
nenhum**. Todo veredito de P9/P10/P12 fecha por leitura de arquivo local, `systemctl show`, `curl` de
loopback ou prova negativa dirigida.

---

## §8 · AS REGRAS DE PARADA — decididas ANTES do número

| # | gatilho medido | ação | o que se reverte |
|---|---|---|---|
| **S1** | `publish-v2-direct` sai ≠ 0 | **PARE e NÃO REINICIE** | nada — ler o log, corrigir a causa, **republicar para frente**. Reiniciar com `sitemap_loc_without_manifest` trava o boot em laço **mudo** |
| **S2** | `check-served-vs-manifest` vermelho **em massa** (>10 por código ou >25 no total) | **não reinicie** | republicar. Acima do limiar o Go **não sobe** |
| **S3** | sweep com **≥1 vencido** | **nenhum reinício** até varrer | rodar o sweep (sem `--seco`); e **nunca** asserir sobre "vencendo" nem sobre o exit |
| **S4** | `--dry-run` do `purge-edge-cache` **não** imprime `URL(s) em` | **não purgue** | a lista está vazia ou acima do teto ⇒ seria `purge_everything` **com exit 0** |
| **S5** | fórmula do `served_sha256` **divergente** do snapshot | **PARE e reconcilie** | outra frente editou o produtor: o `--ressemear` absorveria **duas** mudanças e o DEPOIS deixa de ser atribuível |
| **S6** | estreia > `dateModified` em **qualquer** rota | **PARE antes de publicar** | corrigir o gerador. `setdefault` torna o carimbo **permanente** |
| **S7** | contagem **total** de itens **cai** depois do P5 | **você filtrou** | desfazer o `continue` novo, manter só o campo. Filtrar muda a população e torna a regra de parada inmensurável |
| **S8** | P5 **piora** contra o gabarito congelado | reverte-se **a mudança do P5**, **não a publicação** | páginas no ar **não saem**: P5 é qualidade e rebaixa para refino; retirar 3.101 páginas vivas daria `sitemap_loc_without_manifest` e **impediria o boot** |
| **S9** | empate dentro do erro da amostra de 100 | **segue, sem creditar ganho** | nada |
| **S10** | par de acórdãos ≥ 0,70 no `check-derived-authorial-floor-selftest` | **PARE**: `PARES_REPROVADOS_CONHECIDOS` é teto **E** piso | corrigir por **escopo** (separar família) ou **indexação**; **nunca** subindo a constante nem o limiar |
| **S11** | censo passa de **2.400 s** | **bug P0 de escala** | indexar o anti-molde (MinHash/banda); **proibido** aumentar timeout |
| **S12** | mutante `Sigiloso() → return false` **sem** ≥3 testes vermelhos | **PARE**: a trava é decorativa | **esse é o achado**, e vale mais que a mudança |
| **S13** | cérebro pausando em CPU depois do E5 | seletor de regime invertido | imprimir o regime escolhido no erro; **nunca** o predicado `size_vram < size` |
| **S14** | `qualidade-diaria`/`qualidade-longa` iriam a `failed` com a máscara nova | **saem do piloto** | a partição delas já está certa; trocar dispararia alerta **diário** |
| **S15** | lock de publicação presente com **PID vivo** | **trabalhe outra frente** | nunca derrubar o dono do lock; nunca `rm` do lock à mão |
| **S16** | `go.mod`/`go.sum` sujos no pré-voo | **PARE** | a atestação lê o **disco**; já atestou contra `go.mod` sujo 2× |

**Em todas: reverter é EDITAR PARA FRENTE.** `git reset|checkout|restore|stash|clean|revert` são proibidos e
barrados por hook. Para ler estado antigo, `git show HEAD:arquivo`. Trabalho de agente ou de outra frente
**nunca se descarta**.

---

## §9 · O QUE CONTINUA NÃO VERIFICÁVEL SEM EXECUTAR

Declarado sem maquiagem, com o teste que fecha cada um.

| # | não verificável | por quê | o teste que fecha |
|---|---|---|---|
| 1 | **Parede do `publish-v2-direct` sobre 11.106 páginas** | rodar = mutar | medir na travessia de 5 e no lote cheio, com `time`, **antes** de escolher qualquer teto do oneshot. O `3600` dos runbooks é **palpite**, não medição |
| 2 | **O censo pós-P4** (`candidatos`, `páginas montadas`, tabela de recusas) | só o gerador produz | `generate-acordao-pages -seco -limite 99999`, **três vezes**, uma por correção (G-6) |
| 3 | **Quantas das 942 ficam com `.br` divergente depois de publicar** | exige publicar | `check-brotli-static-fresco` + `curl -H 'Accept-Encoding: br'` na amostra; a **mecânica** e a janela de ≤65 min estão medidas |
| 4 | **Taxa de colisão da `.path` com a transação** | os "12,5%" são **DERIVADOS** de 3 disparos/24 h × 3.600 s | irrelevante depois da **D4**: com a `.path` parada a taxa é **0** por construção |
| 5 | **Quantos registros os 7 datasets novos do STJ trazem**, e se o parser mantém **81,4%** sobre o corpus ampliado | os 6 datasets nunca foram coletados; o share atual é MEDIDO, o futuro depende dos órgãos criminais | o gate `coleta-stj-cobertura` imprime `len(recursos)` **por dataset** como controle positivo; o share se remede depois do C-8 |
| 6 | **Se há um segundo arquivo quebrado nos 392** | fonte remota | `quarentena.jsonl` passa a responder, com sha e erro de cada um |
| 7 | **Taxa de êxito do host do Querido Diário ao longo do dia** | 7 requisições em ~3 min, 1 êxito = **amostra, não população** | veredito por **k de n** no gate de alcançabilidade, nunca 1 de 1 |
| 8 | **Tempo de boot do daemon do cérebro** | a linha já rotacionou do journal | medir na 1ª partida com `Type=notify` (journal `Started`→`READY`) e **só então** apertar o `TimeoutStartSec=300` |
| 9 | **Fração de triagem das 34.217 pendentes** e qualquer número de `cerebro status` | `Abrir` roda DDL — é caminho de **escrita** | depois do **A2** (`--somente-leitura` que **não chama `Abrir`**) |
| 10 | **Por que `dkms status` está vazio neste laptop** | GPU atual é MX110/Maxwell, sem suporte no 610.x | irrelevante para o alvo: **E2 replica o apt e mede na máquina nova** |
| 11 | **Determinismo CPU↔GPU** | não é mensurável antes de existir a GPU | o piso do **E6** é desenhado para **não** exigir igualdade byte a byte |
| 12 | **Custo do `check-derived-authorial-floor` depois que o P6 popular a família** | os **106,3 s** medidos são a passada **inteira** (inclui abrir 11.357 arquivos para os eixos 1 e 2): é **TETO SUPERIOR** da parte quadrática | cronometrar **só** `pares_quase_identicos` importando o módulo, com a família populada por shard de ensaio **fora** de `v2_pages/` |
| 13 | **Se os 67 temas faltantes são das 944 de hoje ou herdados** | a lista não foi paginada | `check-social-temas-espelhados` imprime as rotas; cruzar com `approved_at` do manifesto |
| 14 | **Se existe junção item→`intent_id`** para o G-11 | `grep` em `generate-v2-publication-severity` devolve **ZERO** | ler `internal/stjacordaos/writeback.go` **antes** de prometer a classificação; sem junção, a atestação vira sinal na **fila de refino** |

---

## §10 · O QUE O ADVISOR MUDOU

**Chamei uma vez, com a orientação toda medida e antes da primeira linha escrita.** Cinco mudanças entraram,
e as três primeiras alteraram o documento de forma material:

1. **C1 resolvido pela dominância, não por preferência.** Eu ia manter a ordem do plano (`P4 → P6`) e
   registrar o conflito. Ele apontou que a contenção medida (gerador-aceito ⊂ gate-aceito, 135/135, inverso
   0) **decide**: as 5 páginas da travessia, escolhidas sob a régua **mais estrita**, sobrevivem ao P4 —
   então `travessia → P4 → recenseio → lote` satisfaz os **dois** runbooks. Virou a **D1**.
2. **A regra de piso da estreia trocou de C' para a do refutador, e virou PADRÃO em vez de flag.** Eu ia
   adotar C' (que o ESTANCAR mediu) e manter o `--piso-por-conteudo`. Ele lembrou que C' carimba estreia
   09-15 em **3 notícias que estrearam 09-14**, permanentemente via `setdefault`, e que como **padrão** o
   conflito **C4** (PUBLICAR chamando o gerador sem a flag) **dissolve**. Virou a **D3**.
3. **Elevou os três achados desta sessão a instrumento e a janela**: o `ETag` = `sha256[:32]` reescreveu a
   2ª perna do I-1 (paridade por `HEAD`, amostra de 100+ em vez de 6); as **seis** units de flock pesado
   reescreveram a §2; e o PC-1 deixou de ser "espera" e virou **restrição datada** com o fecho de engenharia
   (`sweep` ≥07:50Z + timer novo a 07:52Z).
4. **`stop` da `.path` virou linha de pré-condição em cada transação**, em vez de um "P-0.6" separado que
   alguém pularia (**D4**).
5. **Mecânica de escrita**: `§1-§2` primeiro como esqueleto durável, depois um runbook por `Edit`, e as
   emendas dos refutadores **aplicadas no corpo** com marca de uma frase em vez de reproduzir o ataque.

**Da 2ª chamada (com o documento já durável), quatro correções, todas aplicadas:**

6. **G-2 deixou de ser inócuo por causa da própria D1** — o ponto cego do documento. Sob `travessia → P4`, o
   shard **já tem 5 páginas** quando a família é registrada, então o selftest com
   `PARES_REPROVADOS_CONHECIDOS == 0` corre contra **10 pares de acórdãos reais**, e o DEPOIS não pode dizer
   "continua 0": é **[A MEDIR]**, com a **S10** valendo sobre a própria travessia.
7. **O P1b-5 nomeava um campo que instrumento nenhum produzia** (`estreia_acima_do_modificado`): virou
   **segundo invariante declarado do I-4**, com a prova por mutação exigida nos **dois**.
8. **O P-a3 depende do I-7** e isso não estava escrito: sem baseline namespaceado, o `--antes` dele
   **sobrescreve** o da onda das 04:31.
9. **A janela do N3 estava otimista**: não são "19 min antes", são **07:41Z–07:50Z**, com **duas das quatro**
   passadas medidas a **menos de 2 min** do vencimento.
10. **Procedência da D1 declarada**: a dominância 135/135 foi medida na família **tema**, não na de acórdãos
    ⇒ é **inferência por contenção, a confirmar no recenseio**, e não se cita como medição sobre acórdãos.

**Nada que eu medi foi contradito**, então não houve necessidade de reconciliar. E **duas correções são
minhas, não dele, e corrigem os cinco runbooks**: são **SEIS** units de flock pesado (não três) e **DEZ**
units mascarando exit ≠ 0 agora (não nove — falta `wikijuridica-bot-telemetry` na lista do bloco DAEMON).
Mais uma terceira, medida com o próprio instrumento novo: **10 de 10 gêmeas divergem** na minha amostra por
stride, em conjunto **disjunto** do que o crítico amostrou — e o predicado por `ETag` as pegou **sem baixar
um único corpo**, o que valida o I-1 antes de ele existir.
