# LACUNA 5 — Concorrência e serialização na execução do plano de 14 frentes

Investigação somente-leitura em /opt/wiki, 2026-09-15 21:50–22:10 -03.
Toda medição abaixo tem comando e amostra. Onde há uma amostra só, está escrito.

## VEREDITO: GRAVE

Nada na execução do plano é *bloqueado* por lock. O risco real é o inverso do que o
briefing supõe: **quase nada serializa de verdade**, e o único mecanismo que age
sozinho sobre o trabalho do plano não é um lock — é a onda diária, que faz
`git add` **por diretório** nos dois diretórios que P4/P6 escrevem e em seguida
**publica**. Duas premissas do briefing estão erradas e três preocupações são
CONTROLADAS com evidência.

---

## 1. Correções de premissa (medidas)

### 1.1 A janela 09:40–10:20 NÃO é a bancada

`systemctl show wikijuridica-stj-acordaos-coleta.timer` → `OnCalendar=*-*-* 09:40:00`,
`RandomizedDelayUSec=20min`. Quem vive nessa janela é o **coletor do STJ**, que
durou **1 min 05 s** (09:58:12 → 09:59:17) e **falhou**:

```
collect-stj-acordaos: dataset espelhos-de-acordaos-segunda-secao competencia 20240229:
stjacordaos: decodificando o arquivo mensal de espelhos: invalid character '}' after array element
status=1/FAILURE   Consumed 6.112s CPU time
```

É defeito de dado a montante (JSON malformado do STJ), não contenção. Consome 6,1 s de
CPU. **Não é janela de risco.** Fica registrado para P8 (é o coletor da frente dele) e
sai do escopo desta lacuna.

A bancada real é **04:40–05:49**. Medições (1 amostra cada, `ExecMainStartTimestamp` /
`ExecMainExitTimestamp` de 2026-09-15):

| unit | OnCalendar + rand | início→fim medido | duração | lock |
|---|---|---|---|---|
| `qualidade-longa` | 02:10 + 1m30s | 02:11:22 → 02:45:28 | **34m06s** | `/tmp/opt-wiki-agent-heavy.lock` |
| `official-source-url-inventory-refresh` | 04:20 + 5min | 04:23:19 → 04:25:05 | 1m46s | heavy |
| `daily-content` | 04:20 + 15min | 04:24:45 → 04:42:10 | **17m25s** | `/tmp/wiki-daily-content.lock` |
| `qualidade-diaria` | 04:40 + 10min | 04:48:12 → 05:48:54 | **60m42s** | heavy |
| `noticias-coleta` | 07:15/11:50/16:20/21:50 + 1min | 21:50:48 → 21:51:02 | 14s | heavy |
| `qualidade-race` | dom 03:40 + rand | (semanal) | não medido | heavy |
| `corpus-oraculo-recoleta` | seg 04:10 + rand | (semanal) | não medido | heavy |

**Dois clusters de risco, não um: 02:10–02:45 e 04:20–05:49.** 55 timers
`wikijuridica-*` de 66 no host.

**N de M, honesto:** duração medida em **8 de 55** units (a tabela acima). Que os
outros 47 **não tomam o lock pesado** está apurado por grep — `flock` aparece em
exatamente **6** arquivos de `ops/systemd/*.service`. Que sejam *curtos*, **não está
medido**. Quatro deles ocupam justamente as janelas que declaro livres na §7 e ficam
como ocupantes de duração **não medida**: `backup` 23:22 (I/O), `datajud-fila` 00:37,
`edge-warm` 01:25 (~11 mil URLs a 12 r/s ≈ 15 min de rede), `origin-warm` a cada 3 h
com `--rps 80`. Nenhum toma lock; todos disputam disco ou rede.

### 1.2 `run-heavy-throttled` não usa o lock pesado, e **não espera**

Duas coisas erradas na premissa "sai com código 75 no mesmo escopo de lock":

**(a) Escopo.** `tools/run-heavy-throttled:80-107` deriva o próprio lock:

```
lock_root = /run/user/$UID/portaljuridico-heavy-$uid-<sha256 de dev:inode da raiz do repo>
lock_key  = sha256("command:" + argv)      # ou sha256("scope:" + WIKI_HEAVY_LOCK_SCOPE)
lock_dir  = $lock_root/$lock_key.lock      # mkdir(2) como primitiva
```

Vivo: `/run/user/1000/portaljuridico-heavy-1000-a71eccce29e301a464c5318569b8ea9abf6d400c09447682b58931bfcc6e6bed`
(existe, vazio às 21:55 — nenhum comando pesado em voo). **Ele nunca toca
`/tmp/opt-wiki-agent-heavy.lock`.** Consequência: `run-heavy-throttled` **não
serializa contra a bancada**, e dois comandos pesados *diferentes* sob o wrapper
rodam 100% concorrentes por desenho — a chave é o argv. O `exit 75` do briefing vem
de outro lugar: `cmd/wiki-ops/exec.go:41,48` (`flock -w N -E 75` sobre o lock pesado).

**(b) Espera.** O laço de 600 s (`:1417-1441`, `WIKI_HEAVY_LOCK_WAIT_SECONDS=600`) é
**inalcançável por padrão**. Na primeira contenção roda
`validate_lock_wait_classification_or_exit` (`:1424`), cujo `case` default é
(`:1293-1296`):

```
run-heavy-throttled: active lock requires WIKI_HEAVY_WAIT_CLASSIFICATION=critical_dependency
with dependency_id/owner_pid/timeout_ms/ultima_evidencia/comando_reorientacao
or non_critical_wait reorientation; refusing passive sleep
exit 75
```

**Padrão = exit 75 imediato.** Esperar exige `WIKI_HEAVY_WAIT_CLASSIFICATION=critical_dependency`
mais as **5 variáveis** do envelope, todas validadas por literal:

| variável | validador (`:1258-1262`) |
|---|---|
| `WIKI_HEAVY_DEPENDENCY_ID` | não vazio, não casa `*placeholder*`/`*later*` |
| `WIKI_HEAVY_OWNER_PID` | inteiro **e** igual ao `pid`/`child_pid` do meta do lock vivo (`:1277-1282`) |
| `WIKI_HEAVY_WAIT_TIMEOUT_MS` | inteiro 1..86400000 |
| `WIKI_HEAVY_LAST_EVIDENCE` | não vazio/placeholder |
| `WIKI_HEAVY_REORIENTATION_COMMAND` | não vazio/placeholder |

`non_critical_wait` também sai 75, com a mensagem "reoriente para frente P0
independente". Isto é **guarda correta**, não bug: o repo proíbe espera passiva.
Mas muda a regra operacional: **quem chama `run-heavy-throttled` tem de tratar 75 como
"vá fazer outra frente", nunca como falha do comando.**

Terceiro número que importa: `WIKI_HEAVY_TIMEOUT_SECONDS=540` (`:121`) **mata o
comando em 9 min**. A suíte do `internal/v2ingest` custa 611 s medidos (comentário do
pre-commit `:668-672`) — ela **morre** sob o wrapper com o default. O coletor do STJ
já roda com o teto elevado (`budget_ms=1800000` no journal) e com
`WIKI_HEAVY_LOCK_SCOPE` explícito (`scope:collect:stj-acordaos:gocache:...`) — é o
modelo a copiar.

---

## 2. Mapa dos locks (quem segura o quê, por quanto tempo, e o que acontece com quem chega)

`lslocks` às 21:55 (únicos locks do repo detidos):

```
sqlite3          2008821  POSIX READ  /opt/wiki/data/ai/grafo.sqlite      (agente irmão)
cerebro           926445  POSIX READ  /opt/wiki/data/ai/fila.sqlite
wikijuridica-se  1715804  FLOCK WRITE /opt/wiki/var/on-demand-cache/search-index.lock
wikijuridica-so  3379981  POSIX READ  /opt/wiki/var/social/social.db
```

| lock | tomado por | duração medida | quem chega depois |
|---|---|---|---|
| `/tmp/opt-wiki-agent-heavy.lock` | `qualidade-diaria` (60m42s), `qualidade-longa` (34m06s), `official-source-url-refresh` (1m46s), `noticias-coleta` (14s ×4/dia), `qualidade-race` e `corpus-oraculo-recoleta` (semanais); e todo commit Go por convenção | até **61 min** | `flock` **sem `-w`** = espera indefinida e silenciosa. É o modo de falha real: um commit Go às 04:48 fica pendurado até 05:49 sem dizer por quê |
| `/tmp/opt-wiki-commit.lock` | **ninguém** | — | **NÃO EXISTE como mecanismo.** O arquivo está no disco (0 bytes, criado 2026-09-10 05:41:29 por `flock` ad-hoc de uma sessão), mas `git grep opt-wiki-commit` = **0 ocorrências** em todo o repo versionado. A memória que registra "commits Go em /tmp/opt-wiki-commit.lock" descreve uma intenção **não implementada**; os documentos vivos continuam mandando no heavy (`docs/OPERACAO_COMANDOS_E_CAMINHOS.md:415`, `.claude/settings.local.json:24`) |
| `/tmp/wiki-daily-content.lock` | `run-daily-content` (17m25s às 04:20; 2ª passada 12:20 `--somente-noticias`) | 17 min | `flock -n 9 \|\| exit 0` (`:78-81`) → **pula em silêncio e o systemd registra `Result=success`**. Segurar esse lock às 04:20 **cancela as páginas do dia sem nenhum alarme** |
| `data/ops/.publish-v2-direct.lock` | `cmd/publish-v2-direct` | passo 8/9, `timeout 1800` | `O_CREATE\|O_EXCL` (`main.go:3976-3982`) → **falha na hora**: "promoção já em curso; remova o arquivo se for órfão". Nunca espera; órfão exige `rm` manual |
| `data/ops/.deploy-em-curso.lock` | `tools/deploy-publico:127-129` | vida do deploy (46 min medidos em 2026-09-10) | **NÃO é mutex.** `: >"$DEPLOY_LOCK"` cria/trunca sem condição. É declaração de janela de manutenção para o watchdog, com batida de 30 s e regra de órfão de 30 min. **Dois deploys simultâneos interleavam livremente** — só a convenção os separa |
| lock do cérebro | `internal/cerebro/saude.go:87` sonda `/tmp/opt-wiki-agent-heavy.lock` | — | **MORTO por namespace.** `systemctl show wikijuridica-cerebro.service -p PrivateTmp` → `PrivateTmp=yes`. O `/tmp` do cérebro é privado, então o caminho que ele sonda nunca é o do host: a sonda de lock responde "livre" para sempre |
| `/tmp/opt-wiki-v2-<sha256>.transaction.lock` | dezenas de arquivos, todos datados 02:31–02:33 | — | lixo: nenhum aparece em `lslocks`. Criados dentro da janela do `qualidade-longa` |
| `/run/user/1000/portaljuridico-heavy-*/<sha256>.lock` | `run-heavy-throttled`, chave = argv | por comando | exit 75 imediato (§1.2) |

---

## 3. O índice git: a premissa é verdadeira só para o commit sem pathspec

O contrato diz "o pre-commit compila o ÍNDICE, não o seu pathspec". **Lido no código,
isso vale para `git add` + `git commit`, e não vale para `git commit -- <paths>`.**

`GIT_INDEX_FILE` é honrado ponta a ponta:

- `.githooks/pre-commit:163-171` — `trusted_git()` propaga `GIT_INDEX_FILE` quando ele
  está definido (e só ele; o resto do ambiente é zerado com `env -i`).
- `.githooks/pre-commit:185-193` — `trusted_nice()` propaga o mesmo para o checker.
- `tools/check-go-index-compile-closure:843` — injeta `GIT_INDEX_FILE` nas chamadas git.
- `:912-914` — `_canonical_index_path` só cai em `rev-parse --git-path index`
  quando **não** há argumento nem env.
- `:925-928` — comentário explícito: *"Partial commits and linked worktrees may place
  their authoritative index outside the primary gitdir. Location is not authority"*.
- `tools/test_check_go_index_compile_closure.py:399` —
  `test_partial_commit_index_may_live_outside_git_directory`. É contrato testado.

Num `git commit -- <paths>`, o git monta um índice temporário (HEAD + os paths) e
exporta `GIT_INDEX_FILE` para o hook. **O gate compila a closure desse índice
temporário**, não o `.git/index` compartilhado. Logo:

- **Commit com pathspec isola.** É a primitiva de isolamento que o repo já tem, e é
  também a que o `~/.claude/CLAUDE.md` já manda usar por outro motivo (não tocar a worktree).
- **Commit sem pathspec, não.** Aí o gate lê o `.git/index` real e paga pelo que a
  outra frente deixou lá — **consistente com** os 77,6 s contra 14,9 s do contrato (a
  forma de comando usada em 2026-09-05 não é observável hoje; não medido).
  E é o caso que a operação documentada produz: o `~/.claude/CLAUDE.md` descreve o
  fluxo como `git add <caminho exato>` + `git commit -F <arquivo>` — **forma sem
  pathspec**. Ou seja, o default documentado é exatamente o que paga por índice
  sujo alheio, e a forma com pathspec, que o mesmo arquivo cita como recurso de
  *escopo*, é a que isola. **A regra a escrever é: o pathspec deixa de ser só
  "escopo" e passa a ser o isolamento do gate.**
- **Contrapartida do pathspec, e é uma restrição real:** `git commit -- <paths>`
  commita o conteúdo da **worktree** desses paths, não o que está staged. Arquivo que
  outra sessão esteja editando no momento, se cair no seu pathspec, entra **pela
  metade**. Para arquivo Go de dono único (o caso de P1b e P4) é seguro; para
  `data/editorial/` compartilhado, não.
- Estado agora: `git diff --cached --name-only` = **0 arquivos** (índice limpo),
  180 arquivos modificados não-staged.

**Orçamento do gate, medido.** `.githooks/pre-commit:90,140-151`:
`COMMIT_GATE_BUDGET_SECONDS = 90 × FATOR`, `WALL = BUDGET + 5`, com
`FATOR = max(1, min(4, int(load/nucleos) + (1 se load%nucleos senão 0)))`.

| load 1min medido | fator | orçamento | wall |
|---|---|---|---|
| 7,18 (21:58, irmão terminou) | 1 | 90 s | 95 s |
| 12,90 (21:56) | 2 | 180 s | 185 s |
| ≥ 32 | 4 (teto) | 360 s | 365 s |

O fator **vira no limiar de 8** — atravessar 8,0 dobra o orçamento. Acima de load 32
o teto de 4 é atingido e **commit correto passa a ser recusado**, exatamente o
incidente de 2026-08-12 citado no próprio hook.

**O `git add` por diretório continua perigoso, e o pior reincidente é a própria onda** — §4.

---

## 4. A onda diária é varredora E publicadora — o único item que bloqueia *ordem*

`tools/run-daily-content`, passos 5/9 e 6/9 (`:615-616,632-633`):

```
git add data/editorial/portfolio_v2
git commit -q -m "chore(portfolio): intencoes da onda diaria de $HOJE" -- data/editorial/portfolio_v2
git add data/editorial/v2_pages
git commit -q -m "chore(paginas): estoque da onda diaria de $HOJE"   -- data/editorial/v2_pages
```

`git add` **por diretório** — o padrão que o contrato proíbe por ter varrido trabalho
alheio três vezes. Depois vem 7.9/9 (`generate-page-content-revision`), **8/9
`publish-v2-direct` (`timeout 1800`)** e 9/9 IndexNow. Rodou **duas vezes hoje**
(`7ac3dff5`+`62d71de0` às 04:24, `053793f7`+`06caad54` às 12:20).

Agora cruze com o que P4/P6 escreve. `cmd/generate-acordao-pages/main.go:67-72`:

```go
corpusRel    = "data/corpus/jurisprudencia/stj-espelhos"
manifestoRel = "data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl"
legalCorpus  = "data/legal-corpus"
shardRel     = "data/editorial/v2_pages/stj-acordao-derivado-01.jsonl"      // ESCREVE
portfolioRel = "data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl"  // ESCREVE
v2PagesGlob  = "data/editorial/v2_pages/*.jsonl"                            // LÊ TODO O ESTOQUE
```

Os dois arquivos que P6 escreve caem **exatamente** nos dois diretórios que a onda
faz `git add <dir>`. Confirmado que nenhum existe ainda: nem no disco, nem em HEAD.
Estoque atual: 877 shards em `v2_pages`, 69 em `portfolio_v2`.

**Consequência, e é a pior da lacuna:** shard de P6 deixado na worktree ao atravessar
04:20+15min ou 12:20 é **commitado sob mensagem de onda diária e em seguida
publicado**. Seja preciso sobre o mecanismo, porque a versão errada engana quem
implementar: o pareamento **não** é burlado — a onda commita `portfolio_v2` em 5/9 e
`v2_pages` em 6/9, nessa ordem, e 6/9 *é* a conferência de pareamento; com os dois
shards de P6 no disco, o pareamento fica **satisfeito**. O que a varredura burla é
outra coisa, e é pior:

1. **A decisão de publicação de P6 deixa de existir** — páginas geradas sob a régua
   *anterior* a P4 são publicadas pela onda como se tivessem sido aprovadas.
2. **Corrida de escrita no mesmo shard** se P6 estiver no meio de uma passada às
   04:20 — o próprio script dá o argumento: *"duas execuções escrevem os mesmos
   shards e o vencedor é o último a fechar o arquivo — perda silenciosa de trabalho
   pago"*.

Nota de uma linha: os dois commits usam `-m`, não o `-F <arquivo>` que o contrato
manda. Fora do escopo desta lacuna, mas é o mesmo arquivo a corrigir.

---

## 5. O cérebro durante a execução: uma guarda morta, uma viva

- **Sonda de lock: morta.** `PrivateTmp=yes` (§2). Nunca vê o lock do host.
- **Sonda de carga: VIVA e medida.** `internal/cerebro/saude.go:87-92`,
  `CargaMaxPadrao = 12.0`; `/proc/loadavg` não é afetado por `PrivateTmp`. Hoje:
  **6 pausas, 5 retomadas, 562 lotes**. Duas na última hora:

```
20:57:04 pausa: loadavg de 1 min em 12.46, acima do teto de 12.00
20:58:59 retomado depois de 1m55s de pausa
21:38:43 pausa: loadavg de 1 min em 12.46, acima do teto de 12.00
21:41:49 retomado depois de 3m6s de pausa
```

  **Isto descarta a preocupação: o backstop funciona.** Mas ele é grosso — a sonda roda
  por `Passo` (`--saude-a-cada 60s`) e **não interrompe lote em voo**. Lotes medidos
  hoje: 50 s a **5m18s** (21:16:26). Então "pausar o cérebro" pelo load entrega, no
  pior caso, 5 min de contenção depois da decisão.

- **Frente do plano que precisa de snapshot de `data/ai/`: nenhuma.**
  `grep` em `cmd/generate-acordao-pages/main.go` por `extracoes_dispositivos`,
  `dispositivos_promovidos` e `data/ai` → **zero ocorrências**. P4/P6 leem o corpus do
  STJ e o estoque `v2_pages`, não a saída do cérebro. Quem lê `data/ai` é outra
  família (`generate-writeback-extracoes`, `generate-revisao-extracoes`,
  `generate-grafo-juridico`, `generate-datasets-publicos`). **A colisão de P4/P6 é com
  a ONDA, não com o cérebro.**
  Para referência: `extracoes_dispositivos.jsonl` tem 44.167 linhas / 42 MB e mtime
  **21:53** (cresce agora); `dispositivos_promovidos.jsonl` tem mtime 12:20 — escrito
  pelo passo 1.5/9 da onda, estável entre ondas.

- **Custo de parar o cérebro.** `Type=simple`, `Restart=always`,
  `KillMode=control-group`, `TimeoutStopUSec=4min`,
  `OnFailure=wikijuridica-alerta@wikijuridica-cerebro.service`, `NRestarts=1`.
  `systemctl stop` é respeitado (Restart não religa em stop explícito) e **nada em
  `run-qualidade-diaria` nem em `run-daily-content` para ou reinicia o cérebro** —
  `grep` = zero. O custo é: até **4 min** para o SIGTERM vencer um lote em voo, e o
  ganho é o do contrato — pre-commit de **75 s com o cérebro trabalhando contra 29 s
  pausado** (2026-09-09). Trocar 4 min de parada por 46 s de commit só paga em
  sequência de vários commits Go; para um commit isolado, **não paga**.

---

## 6. Carga agora, e o que ela implica

Duas leituras, 2 min de intervalo, 8 núcleos:

```
21:51  load 14.39 12.22 10.06   MemAvailable 6 GB    (irmão rodando -seco -limite 5000)
21:58  load  7.18 11.01 10.88   MemAvailable 7,35 GB (irmão terminou)
```

Ou seja: **os agentes desta sessão valem ~7 pontos de load**. Medido em voo:
`generate-acordao-pages -seco -limite 5000` a 76% CPU (PID 2016470 — um irmão desta
mesma leva; **não repetir essa passada**), `sqlite3 ...grafo.sqlite?mode=ro` a 89%,
`check-tmp-product-leak`, `du -sh var/ .agents/ data/ public/ ...`, um censo
`/tmp/stj-census` de vida longa com `sleep 11` entre requisições, e
`tools/generate-tmp-product-rescue` disparado por hook. 13 processos `claude` vivos.

**A baseline em repouso não foi medida** — não há janela sem agentes nesta sessão.

**Memória, não CPU, é o recurso apertado.** `MemTotal` 20,36 GB, `MemAvailable`
7,35 GB (36,1%), swap 2,0 de 13,5 GB em uso. `ollama.service`:
`MemoryCurrent` 8,54 GB de `MemoryMax` 12 GB; llama-server somou **6,70 GiB** em 2
processos (um de 6.858 MB + um subindo). `ops/earlyoom/default`:

```
-m 10,5   → SIGTERM a 10% (2,04 GB), SIGKILL a 5% (1,02 GB) de MemAvailable
-s 100,100 → limiar de swap efetivamente desligado
--avoid '^(sshd|systemd.*|...|cloudflared.*|nginx|wikijuridica.*|...)$'
--prefer '^(llama-server|ollama.*|chrome.*|...)$'
```

Folga atual sobre o SIGTERM: **5,3 GB**. Um `go build` da closure cabe. O que mudou a
favor desde 2026-09-08 é o `OOMScoreAdjust=800` herdado pelo llama-server: hoje o
earlyoom mata primeiro o runner do modelo (pausa barata, o Ollama recarrega na
requisição seguinte) em vez dos servidores MCP das sessões vivas — `--prefer` dá o
mesmo bônus a todos e **não ordena** nada.

---

## 7. A MATRIZ DE SERIALIZAÇÃO

### Pode rodar junto (sem guarda necessária)

| A | B | por quê |
|---|---|---|
| leitura/medição de qualquer frente | qualquer coisa | read-only não toma lock |
| `run-heavy-throttled <cmd A>` | `run-heavy-throttled <cmd B>` | chaves de lock diferentes (sha256 do argv) — concorrem por CPU, não por lock |
| cérebro | commit **de conteúdo** (não-Go) | commit leve não builda; `index.lock` ~1 s |
| cérebro | P4/P6 (`generate-acordao-pages`) | conjuntos de arquivos disjuntos (§5) |
| sondas dos 48 timers curtos | tudo | não tomam lock |

### NÃO pode rodar junto

| A | B | o que quebra |
|---|---|---|
| **qualquer trabalho não-commitado em `v2_pages`/`portfolio_v2`** | onda diária 04:20+15min ou 12:20 | a onda faz `git add <dir>` e **publica** o trabalho alheio (§4) — **o item que bloqueia ordem** |
| commit Go | bancada 04:40–05:49 ou 02:10–02:45 | `flock` sem `-w` espera até 61 min em silêncio |
| dois commits **sem pathspec** | entre si | índice compartilhado; o gate compila o do outro (§3) |
| dois `publish-v2-direct` | entre si | `O_EXCL` → o 2º **falha**, não espera |
| dois `deploy-publico` | entre si | **sem mutex nenhum** — só convenção |
| segurar `/tmp/wiki-daily-content.lock` | onda das 04:20 | a onda **pula em silêncio** com `Result=success` |
| suíte do `v2ingest` (611 s) | `run-heavy-throttled` default | morre em 540 s |
| passada 10k de P6 | bancada | disputa 8 núcleos com 61 min de suíte |

### Ordem que minimiza espera

Janelas livres dos dois clusters e dos timers médios:
**06:00–09:15**, **10:05–11:45**, **13:00–21:45**, **22:00–02:05**.
Evitar: 02:10–02:45, 04:20–05:49, 09:18 (`efeito-deploy`), 09:40–10:00
(`stj-acordaos-coleta`), 11:50/16:20/21:50 (`noticias-coleta`, 14 s), domingo 03:40,
segunda 04:10.

1. **Índice vazio** (`git diff --cached --name-only` = 0) — invariante de entrada e de saída de cada passo.
2. **P4 primeiro (paridade de régua + evidência de recusa), porque é só Go.** Um
   commit Go, com pathspec, na janela 13:00–21:45. Nada em `v2_pages` na worktree.
3. **P1b depois**, também Go + `first_published_at.json`. Precede P6: sem a data de
   estreia certa, cada página nova de P6 nasce com o mesmo defeito de cronologia que
   P1b existe para consertar.
4. **P1b tem a MESMA lacuna estrutural que P6, e ela tem de virar passo.**
   `published_manifest.jsonl` é **escrito** por `publish-v2-direct` (passo 8/9) e por
   `deploy-publico`, e **nunca commitado por ninguém**: `grep published_manifest
   tools/run-daily-content` devolve só comentários (`:495`, `:700`). É por isso que ele
   está `M` há 5 dias. Commitá-lo à mão às 14:00 **não resolve** — a onda das 04:20 o
   deixa `M` outra vez na manhã seguinte, e `generate-first-published-at` volta a ler
   um arquivo que divergiu de HEAD. O conserto é o mesmo de P6: **o commit do
   `published_manifest.jsonl` entra DENTRO de `run-daily-content`, depois de 8/9 e
   antes de 9/9 (IndexNow)** — a mesma ordem que o próprio script já defende para o
   IndexNow (anunciar URL de transação que falhou é pior que não anunciar).
5. **P6 por último, e como PASSO DENTRO de `run-daily-content`**, sob
   `/tmp/wiki-daily-content.lock` — não como runner novo. Apurado: a onda **não** o
   chama hoje (`grep generate-acordao-pages tools/run-daily-content` → só um
   comentário em `:447`), então o gerador é órfão de fato, como o plano diz. Isso
   resolve três coisas de uma vez: elimina a corrida de §4 (o produtor passa a rodar
   *dentro* do lock que já serializa quem escreve esses shards), herda a ordem
   portfólio→página de 5/9→6/9, e fecha a lacuna do `-limite 30` sem inventar timer.

   **Duas condições de contorno, sem as quais o conserto cria um problema novo:**

   - **O passo tem de ser pulado quando `SOMENTE_NOTICIAS=1`** (a passada das 12:20),
     ou o portal passa a publicar páginas de acórdão **duas vezes por dia**.
   - **A onda já quase toca a bancada, e P6 faz ela tocar.** Hoje a onda começa
     04:20+rand15 e durou 17m25s → termina entre 04:42 e 04:57; a `qualidade-diaria`
     começa 04:40+rand10 → entre 04:40 e 04:50. **Em 2026-09-15 elas não se sobrepuseram
     por 6 minutos de sorte** (04:42:10 contra 04:48:12), e **não há lock entre as
     duas** (locks diferentes, §2). Pendurar na onda a geração de P6 mais a publicação
     de 2.488 páginas mais o brotli torna a sobreposição **sistemática**, em CPU, com
     61 min de suíte do outro lado. Então: **medir a duração nova da onda antes de
     ativar o passo** e, conforme o número, ou antecipar o `OnCalendar` da onda (ela é
     a produtora; a bancada é a auditora), ou reduzir o `RandomizedDelayUSec=15min`
     que é o que hoje empurra o fim dela para dentro da janela da bancada. Aceitar a
     sobreposição sem nomeá-la é o que não pode.
6. **Nunca atravessar 04:20 nem 12:20 com trabalho não-commitado** em
   `data/editorial/v2_pages` ou `data/editorial/portfolio_v2`.
7. **Deploy/publicação em último lugar**, um por vez, conferindo
   `data/ops/.deploy-em-curso.lock` e `data/ops/.publish-v2-direct.lock` antes —
   nenhum dos dois protege contra concorrência de verdade.

**Acoplamento a registrar, uma linha:** `wikijuridica-cerebro-enfileirar.path` observa
`PathChanged=/opt/wiki/content/pages.json` e
`PathChanged=/opt/wiki/data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl` — os
**dois** escritos pela onda (o 1º por `publish-v2-direct`, o 2º pelo coletor do STJ).
É isso que disparou o enfileirar às 12:28:56, 8 min depois da onda das 12:20, e não o
timer das 03:05. Consequência para o plano: **toda publicação de P6 reenfileira o
cérebro automaticamente** — desejável, mas significa que a carga do cérebro sobe
*depois* de cada passada de P6, não durante. E confirmado com grep mais amplo:
`tools/deploy-binario-go` e `tools/deploy-publico` **não** param nem reiniciam o
cérebro (zero ocorrências), então a §5 vale como escrita.

---

## 8. Descartado com medição (vale tanto quanto confirmar)

| preocupação do briefing | veredito | evidência |
|---|---|---|
| "janela 09:40–10:20 é a de risco" | **falsa** | é o coletor do STJ, 1m05s, 6,1 s de CPU, e falhou por JSON malformado |
| "run-heavy-throttled sai 75 no mesmo escopo do lock pesado" | **falsa** | lock próprio em `/run/user/…`, chave = argv; nunca toca o heavy |
| "`/tmp/opt-wiki-commit.lock` não existe" | **meia** | o arquivo existe (0 B, 2026-09-10 05:41); o **mecanismo** não: 0 ocorrências em `git grep` |
| "lock do cérebro está morto por PrivateTmp" | **confirmada, e inofensiva** | sonda de lock morta, mas `CargaMax=12` viva: 6 pausas hoje |
| "alguma frente precisa de snapshot de `data/ai/`" | **falsa para P4/P6** | `grep` em `generate-acordao-pages`: zero referências a `data/ai` |
| "o pre-commit sempre compila o índice compartilhado" | **só sem pathspec** | `GIT_INDEX_FILE` honrado em 4 pontos + teste `test_partial_commit_index_may_live_outside_git_directory` |
| "publicação concorrente corrompe dado" | **CONTROLADO** | `O_CREATE\|O_EXCL` falha na hora (`publish-v2-direct/main.go:3976`) |
| "lock órfão travaria a execução" | **CONTROLADO** | `reclaim_stale_lock` com heartbeat de 30 s e stale de 180 s / 21600 s |

---

## O que o advisor mudou

Chamado depois da orientação e antes de escrever. Sete verificações discriminantes;
**duas inverteram conclusão minha**:

1. **`run-heavy-throttled` espera ou sai?** Eu havia lido o laço de 600 s (`:1417-1441`)
   e ia escrever "espera 600 s e sai 75". O advisor mandou ler `:1250,1300`. O default
   é **`exit 75` imediato** — o laço é inalcançável sem as 5 variáveis do envelope.
   Era a resposta direta à sub-pergunta 2, e eu a teria dado errada.
2. **`GIT_INDEX_FILE`**: eu ia repetir o contrato ("compila o índice, não o pathspec")
   como verdade geral. O grep que ele pediu mostrou o env propagado em 4 pontos e um
   teste nomeado — então **commit com pathspec isola**, e a regra do contrato vale só
   para o commit sem pathspec. Virou a §3 e a primitiva recomendada do passo 1.
3. Apontou que eu contaria as pausas do cérebro errado (meu `grep -ciE 'pausa|carga|load'`
   dava 8 porque casava as linhas de "retomado"); a contagem exata é **6 pausas /
   5 retomadas / 562 lotes**.
4. Mandou medir memória como recurso apertado (earlyoom `-m 10,5` contra `MemAvailable`),
   não só CPU — virou a §6.
5. Impediu que eu re-rodasse `generate-acordao-pages -seco -limite 5000` para "confirmar"
   os 2.488: um irmão já o estava rodando (PID 2016470), e uma segunda passada idêntica
   é exatamente o que esta matriz proíbe.
6. Sugeriu a conclusão de que o publicador de P6 deve ser **passo dentro de
   `run-daily-content`** em vez de runner novo — adotado no passo 4 da ordem, porque o
   lock que resolve §4 é justamente o que a onda já segura.
7. Fixou a forma do veredito (GRAVE, com o item da onda bloqueando *ordem* e não
   *execução*) e mandou dizer explicitamente quais premissas caíram — virou a §8.

Segunda chamada, com o arquivo já no disco, mudou mais seis coisas:

8. **Mandou um grep antes de eu fixar "P6 como passo da onda"**: verificar se a onda já
   chamava `generate-acordao-pages`. Não chama (só um comentário em `:447`) — a
   recomendação sobreviveu, mas o grep era obrigatório por R1 e eu não o tinha feito.
9. **Achou a mesma lacuna estrutural em P1b**: `published_manifest.jsonl` é escrito por
   `publish-v2-direct` e por nenhum commit — por isso está `M` há 5 dias. Commitá-lo à
   mão não resolve; ele tem de entrar como passo da onda entre 8/9 e 9/9. Virou o
   passo 4 da ordem, que eu não tinha.
10. **Corrigiu um mecanismo que eu descrevi errado na §4**: eu escrevi que a varredura
    burla o pareamento portfólio→página. Não burla — 5/9 e 6/9 fazem o pareamento na
    ordem certa e os dois shards de P6 o *satisfazem*. O que a varredura burla é a
    decisão de publicação de P6 e a corrida de escrita no shard. A conclusão fica, o
    mecanismo estava errado e teria enganado quem implementasse.
11. **Cobrou o N de M que a tarefa exige**: eu disse "os 48 restantes são sondas curtas"
    sem ter medido nenhuma. Agora está "8 de 55 medidos; 47 não tomam lock por grep;
    duração não medida", com os quatro ocupantes não medidos das janelas livres nomeados.
12. **Derrubou duas afirmações fortes demais na §3**: os 77,6 s viraram "consistente
    com" (a forma do comando de 09-05 não é observável), e entrou a contrapartida que
    eu havia omitido — `git commit -- <paths>` leva a **worktree**, então arquivo que
    outra sessão edita entra pela metade se cair no pathspec.
13. **Apontou a sobreposição onda×bancada que eu não tinha calculado**: 04:42 contra
    04:48 hoje é 6 minutos de sorte, e pendurar P6 na onda torna o encontro
    sistemático. Virou condição de contorno explícita do passo 5.
