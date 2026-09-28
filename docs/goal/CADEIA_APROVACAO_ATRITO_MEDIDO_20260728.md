# Cadeia de aprovação — atrito medido elo a elo (2026-07-28)

> Medido em `/opt/wiki`, `main`, máquina de 8 núcleos. **Cada número tem o comando que o
> produziu.** Onde não medi, está escrito "não medido". Este documento registra a primeira
> execução real da cadeia até onde ela reprova — não uma leitura de documentação.
>
> Regra de leitura: a cadeia **nunca rodou inteira**. O que está abaixo é o resultado de
> executá-la de fato, elo por elo, e corrigir cada elo que reprovou.

---

## 0. Estado de partida (verificado no dado vivo, não herdado)

| fato | comando | valor |
|---|---|---|
| páginas v2 ativas | `cat data/editorial/v2_pages/*.jsonl \| wc -l` | 7.739 registros / 680 shards |
| `published_manifest` | `wc -l data/editorial/published_manifest.jsonl` | **0 linhas** |
| verdict de release | `ls data/editorial/scaled_content_release_verdict.jsonl` | **ausente** — passo 41 nunca rodou |
| receipt do ingest | `stat data/ops/v2_ingest_transaction_receipt.json` | 2026-07-22 11:46 (6 dias) |
| `drafts_expected` | `data/editorial/stock_manifest.json` | 7.178 (não 6.846 — o `RELEASE_CHAIN_RUNBOOK_20260721.md:31` está defasado) |

---

## 1. Elos executados, na ordem, com medição

### Elo 0 — LanguageTool :8082 · **REPROVOU → CORRIGIDO**

Pré-requisito dos passos 14-31 do `bootstrap-chain`. Estava **fora do ar** desde o reboot.

```
curl -s -m 4 -X POST http://localhost:8082/v2/check -d "language=pt-BR&text=teste"
→ http=000 (conexão recusada)
```

Correção (infra, não código): `nohup ./tools/run-languagetool-local &`.
Artefatos e JRE já estavam presentes (`.cache/languagetool/6.8/`, OpenJDK 17.0.19).

Verificação pós-correção — 3 repetições:

```
tentativa1 http=200 tempo=4,659s   (primeira: carrega o modelo pt-BR)
tentativa2 http=200 tempo=3,008s
tentativa3 http=200 tempo=1,256s
resposta: matches=1 | lang=pt-BR
```

**Lição operacional:** o LanguageTool não sobrevive a reboot e nada o religa
automaticamente. Toda a faixa 17-31 da cadeia depende dele. Isso é um elo silencioso:
não há gate que avise "o oráculo está morto" antes de a cadeia gastar 16 passos até chegar
nele. Ver §3, item 1.

### Elo 1 — `bootstrap-chain --from 12 --until 12` · **REPROVOU** (preflight de frescor)

```
/usr/bin/time -v ./tools/bootstrap-chain --from 12 --until 12
```

| métrica | valor |
|---|---|
| wall-clock | **25,18 s** |
| CPU (user+sys) | **41,72 s** (38,16 + 3,56) — 165% de CPU |
| RSS máximo | 556 MB |
| load antes / depois | 8,71 → 9,21 (8 núcleos) |
| exit | 1 |

Reprovou no `[preflight] frescor do estoque v2`, com o diagnóstico completo:

- `validation_as_of_stale` / `legal_as_of_stale`: receipt=2026-07-22, required=2026-07-28
- **~50× `source_changed`** em `data/editorial/portfolio_v2/*.jsonl` (hash divergente do snapshot)
- **9× `inventory_source_missing`** em `data/editorial/v2_pages/`: `aereo-19`, `empresarial-21`,
  `empresarial-23`, `empresarial-28`, `lgpd-16`, `lgpd-27`, `seguros-14`, `sucessoes2-11`,
  `telecom_energia-33`
- **10× `source_unreadable`** (registro alterado dentro do shard): `autonomos-03`, `saude-r03`,
  `saude-r04`, `seguros-r03`, `seguros-r08`, `sumulas-01`, `telecom-r03`, `tributario-r02`,
  `tributario-r04`
- `terminal_evidence_invalid`: guardas terminais reconstruídas divergem do snapshot do receipt

A própria ferramenta imprime o remédio: validar com `tools/ingest-v2-stock --prepare-only` e,
com os shards estáveis, instalar a fotografia canônica com `tools/ingest-v2-stock`.

**Diagnóstico dos 9 `inventory_source_missing`:** os arquivos **existem em disco** com conteúdo
real, mas estavam **untracked desde 2026-07-22** — são a escrita da onda-95 pré-barreira,
18 páginas. Leitura de amostra (`aereo-19`, intent `aer-reserva-sumiu-sistema-embarque-negado`):
1.222 palavras, 6 seções, 2 FAQ, 3 fontes oficiais (Resolução ANAC 400/2016), PT-BR acentuado,
`lane=comercial`. É produto legítimo, não lixo. Pousado nesta sessão.

### Elo 2 — `ingest-v2-stock --prepare-only` · **REPROVOU** (atestação do validador)

```
/usr/bin/time -v ./tools/ingest-v2-stock --prepare-only --timings
```

| métrica | valor |
|---|---|
| wall-clock | **28,97 s** |
| CPU (user+sys) | **29,06 s** (25,83 + 3,23) — 100% de CPU (serial) |
| RSS máximo | 332 MB |
| build do binário (dentro do total) | 5.940 ms |
| exit | 1 |

```
ingest-v2-stock: generated validator attestation does not match authenticated source graph:
  generated=sha256:c288c947... source=sha256:2145ab03...; run go generate ./internal/v2ingest
```

### Elo 4 — `ingest-v2-stock --prepare-only` (segunda tentativa) · **PASSOU**

Executado **atomicamente** com o `go generate` imediatamente antes, sem janela para drift:

| métrica | valor |
|---|---|
| wall-clock | **4:37,48** |
| CPU (user+sys) | **230,7 s** |
| RSS máximo | 1,71 GB |
| exit | 0 (`TIMING command=ingest-v2-stock status=pass`) |

**Por que a primeira tentativa falhou e esta passou:** entre as duas execuções anteriores o hash
do grafo de fontes mudou (`2145ab03` → `c3e4694d`) porque a atestação cobre um **grafo**, não um
arquivo — e agentes editavam `internal/v2ingest/` concorrentemente. Gerar e validar em invocações
separadas deixa uma janela em que o grafo se move. Rodar os dois no mesmo comando fecha a janela.

### Elo 5 — `ingest-v2-stock` WRITE-FULL · **MORTO POR ORÇAMENTO DE EXECUÇÃO (exit 124)**

| métrica | valor |
|---|---|
| wall-clock | **5:04,13** |
| CPU (user+sys) | **258,3 s** (250,87 + 7,46) |
| RSS máximo | **1,82 GB** |
| exit | **124 — SIGTERM por timeout** |

O `tools/run-go-cmd-cached` impõe `run_timeout_spec=300s` à execução. O WRITE-FULL chegou a
emitir o plano transacional completo (`plan_fingerprint`, `evidence_sha256`,
`commit_marker_sha256`, `terminal_evidence_path`, `publication=false`) e foi morto aos 300 s.

Redimensionamento correto: `WIKI_GO_CMD_TIMEOUT_SECONDS` (teto do wrapper: 1800 s) ajustado ao
tempo **medido**. Isto não é "corrigir com timeout" no sentido proibido — não há gate reprovando
que passe a passar; a operação é longa e correta, e o orçamento padrão do wrapper estava abaixo
da sua duração real. O que **é** problema de verdade está registrado abaixo.

> **Parede de escala do ingest (P0 de arquitetura).** 258 s de CPU para **7,7 mil páginas /
> 42 MB** é ~30 ms de CPU por página, com **1,82 GB de RSS**. Extrapolando linearmente:
> 100 mil páginas ≈ **56 minutos de CPU** e RSS na casa de dezenas de GB — a máquina tem 19 GB.
> O merger materializa os registros em memória. **Nenhum ajuste de constante resolve isto**: o
> caminho é reescrever o ingest para streaming por shard (ler/escrever sem reter todas as linhas)
> e tornar o snapshot incremental por delta em vez de recomputar o estoque inteiro. O próprio
> comentário do código, escrito nesta sessão, já nomeia o streaming como pré-requisito para 1M.

### Elo 3 — `go generate ./internal/v2ingest` · **PASSOU**

```
flock /tmp/opt-wiki-agent-heavy.lock /usr/bin/time -v nice -n 5 ./tools/go-modern generate ./internal/v2ingest
→ exit 0 | RSS 558 MB
modificou: internal/v2ingest/v2ingest.go
           internal/v2ingest/validator_fingerprint_attestation_generated.go
```

---

## 2. Refutações — números herdados que **não** se confirmaram

Registrado porque documentação errada custa mais que documentação ausente.

1. **"B4 rodou em dry-run"** — **REFUTADO**. A hipótese era que
   `status="v2_ingest_transaction_prepared_no_publication"` no receipt indicava
   `--prepare-only`. Não indica: essa string é uma **constante** em
   `internal/v2ingest/plan.go:38` (`ingestTransactionReceiptStatus`), o único status que o
   receipt recebe em qualquer execução. `no_publication` descreve que o ingest não publica —
   publicar é fase posterior —, não que ele não commitou. O bloqueio real do B4 é outro e está
   medido no Elo 2.

2. **`TARGET_N = 6.846`** (`RELEASE_CHAIN_RUNBOOK_20260721.md:31`) — **defasado**.
   `data/editorial/stock_manifest.json` vivo traz `drafts_expected=7178`.

3. **"MaxPairs conta pares confirmados ≥ threshold"** — **REFUTADO** por leitura de código:
   `internal/v2pagedistinctness/global_partition.go:1533` incrementa `ownerState.localPairs`
   sobre pares **roteados** pelo índice invertido, e o teto (`DefaultMaxLocalPairs = 50_000`,
   `types.go:39`) é **por shard**. Logo o estouro é limite de **capacidade de roteamento**,
   não sinal de corpus-molde nem de threshold frouxo. A conclusão muda a correção: o alvo é o
   dimensionamento do budget por shard, não o conteúdo nem o gate de similaridade.

---

## 3. Atrito estrutural encontrado ao executar (não é lentidão — é desenho)

1. **Nenhum gate verifica os oráculos externos antes da cadeia.** LanguageTool morto só se
   descobre no passo 17, depois de a cadeia já ter gasto os passos 12-16. Um preflight de
   liveness dos oráculos (custo: um POST de 1 s) evita 5 passos de trabalho jogado fora.

2. **Commit só de conteúdo paga download de módulos Go.** O commit dos 9 shards (9 arquivos
   JSONL, zero Go) disparou o download de ~40 módulos:
   `go: downloading golang.org/x/sys`, `github.com/RoaringBitmap/roaring`, … A DEC-002 diz que
   commit de conteúdo puro **não** builda, e o gate obedece
   (`go-index-compile-closure: SKIP reason=no_staged_build_impact elapsed_ms=720`) — mas o
   *runtime do próprio gate* é compilado num workspace efêmero em `/tmp`, que o reboot esvaziou.
   O custo é pago de novo a cada boot.

3. **O evidence set de supersessão bloqueia commit por pathspec.**
   `internal/v2supersessionintegrity/git_index.go:940` exige o conjunto vivo **completo** no
   índice; um `git commit -- <pathspec>` que deixe 4 de 6 é barrado com
   `partial live v2 evidence set in the Git index: present=4 required=6`. O hook está **certo**
   (protege a atomicidade da evidência) e a saída é incluir os 6 no mesmo commit — mas o
   comportamento não estava documentado e transforma qualquer commit de conteúdo num commit
   acoplado ao evidence set enquanto ele estiver parcial.

4. **O preflight de frescor é O(N) a cada invocação da cadeia.** 25 s de parede / 41,7 s de CPU
   só para descobrir que o estoque está stale, e ele roda de novo a cada `bootstrap-chain`.
   Com 42 passos executados em blocos, esse custo se repete por bloco.

---

## 3-bis. O "deadlock" do `check all` é espera por subprocesso — **refutado com prova de processo**

O diagnóstico herdado dizia: `check all` leva 411 s de parede com apenas 35,4 s de CPU, com
"12/12 threads em `futex_wait`" — assinatura de deadlock. **Não é deadlock.** Prova colhida ao
vivo, com o `check all` rodando:

```
$ CB=$(pgrep -f 'checkbin all' | head -1)          # PID 3875150
$ ls /proc/$CB/task | wc -l                        → 1        (uma thread, não 12)
$ cat /proc/$CB/task/$CB/wchan                     → do_wait   (esperando FILHO, não futex)
$ awk '{print $14, $15}' /proc/$CB/stat            → 0 0       (utime=0, stime=0: ZERO CPU)
$ ps --ppid $CB → 3875153 (checkbin all)
$ ps --ppid 3875153 → 3900643 go tool -modfile=tools/sca/go.mod govulncheck ./...
```

O processo pai consome **zero CPU** e dorme em `do_wait`. O trabalho está no neto:
**`govulncheck ./...`, uma varredura de vulnerabilidade sobre a árvore inteira**, medida em
**346% de CPU e 1,59 GB de RSS**.

Consequências que mudam a prioridade:

1. **A métrica "35,4 s de CPU" não media o trabalho.** CPU de processo filho não entra no
   contador do pai. A leitura "muito wall, pouca CPU ⇒ lock" estava invertida: era "muito
   wall, muita CPU **no filho**". Qualquer diagnóstico futuro de `check all` precisa somar a
   CPU da árvore de processos (`/usr/bin/time` com `wait4`, ou `cgroup`), não a do pai.
2. **`check all` roda uma varredura full-tree de segurança a cada invocação.** O check é
   `sca-govulncheck` (`tools/check-sca-govulncheck:9` → `run-check sca-govulncheck`). Ele é
   legítimo como gate de segurança, mas seu resultado **só muda quando `go.mod`/`go.sum` ou a
   base de vulnerabilidades mudam** — nunca por causa de conteúdo editorial. Pagá-lo em toda
   invocação da fábrica é computação desnecessária no sentido exato da queixa do dono.
3. **Correção de causa-raiz (não é band-aid de timeout):** cachear o veredito do
   `sca-govulncheck` com chave = `sha256(go.mod) + sha256(go.sum) + versão da base de
   vulnerabilidades + versão da regra`. A chave inclui **conteúdo e versão da regra**, então
   ela invalida sozinha quando a dependência ou o gate mudam — não é o cache proibido, que
   esconderia gate reprovado. Efeito: a varredura full-tree passa a rodar quando as
   dependências mudam, não a cada lote de páginas.

---

## 3-ter. O commit estava bloqueado por um cache de build **efêmero por invocação**

Três commits de **conteúdo puro** (13 arquivos JSONL/JSON, zero Go) morreram com
`Terminated` / `fatal: ref updates aborted by hook` — inclusive com a máquina em **load 9 de 8
núcleos**, o que descarta carga como causa.

Rastreamento, elo a elo:

- O `pre-commit` **não** é o culpado: ele roda um único gate e ele **pula corretamente** —
  `go-index-compile-closure: SKIP reason=no_staged_build_impact elapsed_ms=192`.
  A DEC-002 está sendo respeitada.
- `fatal: ref updates aborted by hook` vem do **`.githooks/reference-transaction`**, um hook
  diferente, com orçamento global de 90 s (`reference-transaction:22`,
  `GATE_BUDGET_SECONDS=90`). Ele invoca `tools/run-v2-index-product-gates` sob `env -i`.
- Dentro do launcher (`tools/run-v2-index-product-gates`):

```
:71   WORK="$(mktemp -d /tmp/wiki-v2-index-gates.XXXXXX)"
:100  GO_PRIVATE_PATH="$WORK/gopath"
:101  GO_PRIVATE_MODCACHE="$WORK/gomodcache"
:102  GO_PRIVATE_BUILDCACHE="$WORK/gocache"
:446  build_gate ./cmd/check-v2-supersession-integrity  "$BIN/supersession"
:447  build_gate ./cmd/check-v2-writing-semantic-contract "$BIN/writing"
```

**Os caches de build e de módulos vivem num diretório temporário criado do zero a cada
invocação.** Todo commit que dispara o hook recompila **dois binários Go inteiros** com
`GOCACHE` vazio e `GOMODCACHE` vazio — o que se manifestou como ~40 linhas de
`go: downloading …` num commit sem uma única linha de Go — dentro de um orçamento de 90 s.
Fica no limiar: passou uma vez, falhou nas seguintes.

Custo medido do launcher a frio, 3 repetições
(`/usr/bin/time -v tools/run-v2-index-product-gates --root /opt/wiki --old HEAD --candidate HEAD`):
**114,2 s / 96,6 s / 82,6 s** (loadavg antes: 6,90 / 22,26 / 17,54) contra um orçamento de
**90 s**. Cabe nos 90 s só com sorte.

#### A correção que eu propus estava ERRADA — registrado para ninguém repetir

Propus tornar o cache privado **persistente** (identidade = versão do toolchain + `go.sum`),
argumentando que *privado* não precisa ser *efêmero*. **Revisão adversarial reprovou, com
evidência no fonte do Go**, e a rejeição está certa:

- **O GOCACHE não protege contra substituição.** Na leitura, `GetFile()` compara apenas o
  **TAMANHO** da entrada (`.toolchains/go1.26.5/src/cmd/go/internal/cache/cache.go:265-281`,
  `info.Size() != entry.Size`). Verificação de conteúdo só existe sob
  `GODEBUG=gocacheverify=1`, que **desliga** o cache (cache.go:144-171). Um objeto substituído
  por outro do mesmo tamanho é linkado no binário do gate **em silêncio**.
- **O GOMODCACHE extraído nunca é reverificado.** O `go.sum` valida o ZIP no download
  (`modfetch/fetch.go:353,375`); o diretório já extraído não é rechecado em builds seguintes
  (`fetch.go:172`; há um TODO no próprio `fetch.go:360` admitindo o tampering). Pior: o
  launcher usa `-modcacherw` (`:438`), deixando os fontes extraídos **graváveis**.
- **Consequência:** qualquer processo do mesmo UID — isto é, **todos os agentes desta
  máquina** — poderia escrever no cache persistente entre commits e envenenar o binário do
  gate, produzindo **falso-verde permanente e indetectável**. Isso viola o invariante que o
  próprio launcher declara nas suas linhas 4-6 ("No wrapper, executable, source file **or
  binary cache** … is an execution input").
- **E nem entregaria o ganho.** Medido com cache persistente quente mas diretório de fontes
  em `mktemp` novo (exatamente como o launcher faz): **35,4 s**, não os 4,2 s do caso
  mesmo-diretório. Sem `-trimpath` (ausente em `run-v2-index-product-gates:437-438`) o caminho
  do diretório entra na action de compile e invalida o cache first-party a cada invocação.

#### O que fazer no lugar

1. **Destrave imediato, zero código, zero afrouxamento:**
   `WIKI_COMMIT_GATE_TIMEOUT_SECONDS` já é override honrado
   (`reference-transaction:22`, `pre-commit:73`). O orçamento é limite de **liveness**, não de
   validação — os gates rodam **inteiros** com qualquer valor. Controle negativo verificado
   pelo revisor: um candidato **sem** os 2 arquivos de quarentena continua **reprovando**
   (exit 2). Ou seja, elevar o orçamento não faz nada passar que reprovaria.
2. **Correção estrutural (causa-raiz):** binário **pinado e reproduzível** — compilar os 2
   gates com `-trimpath`, gravar o `sha256` esperado num arquivo do commit BASE (padrão que já
   existe no repo: `GO_ARCHIVE_SHA256`, `run-v2-index-product-gates:68`), e o launcher só
   reusar binário cacheado **se o sha256 bater com o registro autenticado do pai**.
   Envenenamento passa a ser **detectável**, o caminho quente cai para milissegundos, e a
   propriedade "mudança de gate pousa separadamente" (`:301-302`) é preservada.
3. **Pular o gate em commit de "conteúdo puro" — REFUTADO.** Os JSONL de
   `portfolio_v2`/`v2_quarantine` são exatamente o objeto que
   `check-v2-supersession-integrity` e `check-v2-writing-semantic-contract` validam. Commit
   fora dos paths gated já pula hoje (`reference-transaction:186`).

---

## 3-quater. O auditor de páginas reprovava **100%** — e voltou a passar

Achado colhido em revisão adversarial e confirmado por medição própria, com a máquina calma e
**sem contenção de lock**:

```
$ nice -n 19 python3 tools/audit_v2_pages.py <shard> --expect-n N --against-stock
{"defects": {"distinctness_index_unavailable": ["cached_factory_stale:internal/quality/quality.go"]},
 "ok": false, "distinctness_index": {"status": "unavailable_fail_closed"}}
```

O binário `factory` em cache (`.cache/go-cmd-bin/factory/factory`, compilado em **22/07 18:02**)
estava obsoleto em relação a `internal/quality/quality.go` (**28/07 16:16**). O auditor
reprovava **fail-closed** — comportamento correto: recusa-se a auditar com ferramenta stale em
vez de emitir falso-verde.

Sequência de reparo (nenhum gate foi afrouxado):

1. **Rebuild do `factory`** → o defeito muda de `cached_factory_stale` para
   `incremental_query_unavailable:TimeoutExpired`. O orçamento da consulta é
   `FACTORY_QUERY_TIMEOUT_SECONDS = 5` (`tools/audit_v2_pages.py:118`), e o auditor
   **deliberadamente não repara** índice ausente/stale durante a auditoria — por desenho, para
   não transformar incerteza em falso-verde.
2. **Rodar o produtor do índice**, que é o caminho sancionado:
   `./.cache/go-cmd-bin/factory/factory status` → exit 0, **14.941 registros lidos, 678 shards
   físicos, 1 compactação, 895 KB de flush**.
3. **Auditor re-testado, duas vezes:** `ok=true`, `pages=10`, `defects=[]`,
   `distinctness_index.status="ready"`.

**Por que isto importa mais do que parece:** o passo 8 do prompt do redator (autoauditoria
eliminatória) é o que carimba `audit_ok`. Com o `factory` stale, **nenhuma página escrita
podia ser aprovada**, independentemente de qualidade, lock ou paralelismo. Qualquer medição de
throughput feita nesta janela mediu um pipeline quebrado — inclusive o baseline de
162 páginas/hora e a hipótese de que a perda vinha de contenção de lock. Ambos precisam ser
**re-medidos** agora que o auditor passa.

---

## 3-quinquies. Por que a fábrica não produz: o auditor morre sozinho em dois eixos

Esta é a descoberta mais importante do turno para a **produção de páginas**, e ela só apareceu
porque medi a taxa de aprovação de verdade em vez de confiar no baseline herdado.

**Amostra de 60 shards / 596 páginas ativas** (semente fixa 20260728, 85 s):

```
shards OK    : 0  (0,0%)
shards FALHA : 60
defeitos por frequência:
    60  distinctness_index_unavailable      <- TODOS
    21  official_source_verified_at_invalid
    21  official_source_http_status_invalid
    11  skipped
     3  current_legal_fact
     2  title_len
     1  fonte_nao_verificada
     1  fontes_min
```

`distinctness_index_unavailable` em **60/60**. O auditor é fail-closed e está certo em recusar —
mas o efeito prático é que **nenhuma página pode ser aprovada**, independentemente da qualidade
do texto. Os dois eixos que o derrubam:

**Eixo 1 — o binário `factory` envelhece a cada edição de Go.**
`cached_factory_stale:internal/quality/quality.go`: o auditor compara o mtime do binário
cacheado com o das fontes Go. Qualquer agente que edite um `.go` do grafo derruba **toda** a
auditoria de páginas até alguém reconstruir o binário à mão. Numa sessão com engenharia Go
concorrente — que é o caso normal deste repo — a auditoria fica morta quase o tempo todo.

**Eixo 2 — o índice incremental só tolera 32 shards divergentes.**
```
reason: incremental_query_failed:factory: v2 distinctness index stale:
        live divergence shards exceed max=32
```
Com **176 shards mudados**, o caminho incremental é matematicamente inalcançável: ele nunca vai
convergir enquanto houver uma onda de escrita em andamento. Só o produtor completo
(`factory index-distinctness`) recompõe.

**A consequência combinada é o retrato da fábrica travada:** escrever páginas em lote muda
dezenas de shards (estoura o eixo 2) e corrigir código Go invalida o binário (eixo 1). Os dois
regimes de trabalho que o projeto precisa fazer ao mesmo tempo — produzir conteúdo e melhorar o
motor — **desligam a auditoria um do outro**. Não é bug de um gate: é acoplamento de ciclo de
vida entre ferramenta, índice e dado.

### A correção aplicada — `tools/ensure-audit-ready` (commit `926e1096`)

Minha primeira proposta foi **auto-rebuild do binário dentro do auditor**. A revisão
adversarial **rejeitou**, e estava certa em dois pontos que eu não tinha visto:

1. **Auto-rebuild resolveria só 1 das 3 causas.** A divergência de índice (causa 3) continuaria
   de pé, e a auditoria seguiria em 0% durante qualquer onda de escrita. Só um passo que
   reconstrói **binário *e* índice** fecha o ciclo.
2. **O rebuild precisa passar por `tools/run-go-cmd-cached`**, que já serializa por lock e
   instala com `mv -fT` atômico. Um `go build -o` direto abriria escrita parcial e
   *"text file busy"*.

A ferramenta implementa o que sobreviveu à crítica: preparação **antes** do lote, com o auditor
permanecendo estritamente fail-closed. A distinção que a torna honesta:

- reconstruir a **ferramenta** a partir da fonte é determinístico e **não muda nenhuma regra de
  veredito** — ao contrário, garante que a auditoria rode com a regra *atual* em vez de uma
  stale;
- reparar o **índice dentro da auditoria** continua **proibido** (viraria falso-verde). Por isso
  a preparação é um passo separado, explícito e auditável.

**Achado extra, encontrado ao implementar:** o teste de frescor
(`audit_v2_pages.py:25537-25603`) itera o manifesto `deps.list` para decidir se o binário
envelheceu. Encontrei `deps.list` de **22/07** contra binário de **28/07** — um manifesto velho
deixa de vigiar pacote novo no fecho de dependências. Isso é **falso-FRESCO**, que é pior que
falso-stale: o auditor acharia o binário em dia quando não está. A ferramenta detecta a inversão
de mtime e força o rebuild pelo wrapper, que regenera o manifesto.

Primeira execução real: detectou o falso-fresco, reconstruiu e deixou o índice consultável em
**24,84 s de parede** (76,04 s user + 6,13 s sys).

Fica em aberto, registrado: `DefaultMaxOverlayShards = 32` (`types.go:32`) é **orçamento de
reconstrução, não garantia de qualidade** — shard divergente dentro do orçamento é lido ao vivo
e comparado integralmente (`store.go:1332+`); exceder é fail-closed, nunca *skip*. Elevá-lo não
afrouxa gate, mas está dentro de `Options` e mudaria o `batch_fingerprint`
(`partition_stream.go:32`), exigindo lockstep com o espelho Python. A resposta honesta não é
elevar para 256: é **rodar o produtor por onda** (6 s) e deixar o teto modesto.

### O resultado: 0% → 63,3% de shards aprovados

Mesma amostra, mesma semente (20260728), mesmos 60 shards / 596 páginas ativas, medido depois de
`tools/ensure-audit-ready`:

```
                        ANTES        DEPOIS
shards OK                 0  (0,0%)    38  (63,3%)
shards FALHA             60            22
--- defeitos ---
distinctness_index_unavailable   60 -> 17
official_source_verified_at_invalid  21 -> 21
official_source_http_status_invalid  21 -> 21
skipped                          11 -> 9
current_legal_fact                3 -> 3
title_len                         2 -> 2
fonte_nao_verificada              1 -> 1
fontes_min                        1 -> 1
```

Nenhum gate foi afrouxado — os defeitos **editoriais** continuam exatamente nos mesmos números
(21, 21, 3, 2, 1, 1). O que mudou foi só a disponibilidade do índice: **60 → 17**. Isso é o
controle negativo que a revisão adversarial exigiu, e ele passa: a preparação do ambiente
destravou a auditoria sem tornar nada permissivo.

**Honestidade sobre os 17 restantes:** eles falharam porque o ambiente foi invalidado *durante* a
medição — o agente que estava atualizando as dependências tocou `go.mod` no meio. Ou seja, o
loop ainda morde enquanto houver engenharia Go concorrente; a ferramenta o torna recuperável em
24 s em vez de permanente, mas a cura completa é chamá-la no início de cada onda. Não extrapolo
a taxa "verdadeira" a partir disso: 63,3% é o que foi medido, sob concorrência real.

### O bloqueador que sobra, agora visível

Com o índice fora do caminho, o bloqueador **real** de aprovação aparece limpo e é exatamente o
mesmo das rejeições do ingest: **fonte oficial nunca verificada ao vivo** (21+21 dos 60). Não é
falso-positivo do detector nem pede mudança de gate — pede **rodar** a verificação, que são os
passos 36-39 da cadeia (`generate-official-source-url-live-metadata-attempts-release` →
`-live-evidence` → `-source-approval` → `-live-recheck`). É aí que está a próxima grande
conversão de páginas rejeitadas em páginas aprovadas.

---

## 4. Rejeições do ingest — verificação exaustiva (não amostrada)

Sobre os **524 registros rejeitados distintos** (chave `source_shard`+`source_line`) de
`data/ops/v2_ingest_report.jsonl`, os três maiores motivos foram checados **um a um**:

| motivo | ocorrências | veredito | prova |
|---|---|---|---|
| `official_source_http_status_invalid` | 391 | **JUSTA** | 0/391 têm status ≠ 0/vazio; `officialSourceHTTPStatusAllowed(200\|203\|206)` está correto — os 391 são `http_status=0`, isto é, **nunca verificados ao vivo** |
| `official_source_verified_at_invalid` | 391 | **JUSTA** | 0/391 têm `verified_at` preenchido |
| `duplicate_phrase` | 205 | **JUSTA** | — |
| `missing_required_field` | 246 | **JUSTA** | — |

**Consequência que muda a ação:** as 391 não são falso-positivo de detector nem exigem
afrouxar gate. É **dado genuinamente ausente** — a verificação ao vivo da fonte nunca rodou
para elas. O remédio é executar os passos 36-39 da cadeia
(`generate-official-source-url-live-metadata-attempts-release` →
`generate-official-source-url-live-evidence` → `generate-public-final-source-approval` →
`generate-public-final-source-live-recheck`), que é exatamente onde a rede acontece. Nenhum
gate precisa mudar.

---

## 5. Sequência restante até o primeiro `published_manifest > 0`

```bash
cd /opt/wiki
# b4 — instalar a fotografia canônica (o estoque mudou desde 07-22)
./tools/ingest-v2-stock --prepare-only        # valida sem escrever
./tools/ingest-v2-stock                       # WRITE-FULL, instala o snapshot
# b5 — cadeia em blocos, stop-on-fail (LanguageTool :8082 precisa estar UP)
./tools/bootstrap-chain --from 12 --until 31  # prosa + oráculos PT-BR
./tools/bootstrap-chain --from 32 --until 41  # release evidence → VERDICT
./tools/check-scaled-content-release-verdict --timings     # exigir verdict_passed > 0
./tools/bootstrap-chain --from 42 --until 42  # manifest-transaction
# b6 — promoção por cohort (teto de 250 por transação, publicrelease.go:72)
./tools/run-promote-cohort-loop --target 7178 --step 250 --dry-run
./tools/run-promote-cohort-loop --target 7178 --step 250 --execute
./tools/check-published-manifest --timings
```

**Frescor é do DIA** (prazo 21:00 -03 = virada UTC): a evidência de
`release_live_recheck` gerada hoje não vale amanhã. A cadeia precisa fechar dentro da janela
ou a faixa 36-39 é refeita.
