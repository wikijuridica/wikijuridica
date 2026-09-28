# Arquitetura de escala da fábrica — 10k hoje, 1M depois

Documento executável para o próximo Claude Code. Escrito a partir de 10 frentes de medição com refutação adversarial. **Nenhuma das 10 frentes sobreviveu com medição confirmada E solução válida ao mesmo tempo** — 3 têm medição confirmada (`formato-de-dados`, `build-go`, `qualidade-sem-custo`), 1 tem solução válida (`estado-da-arte`), nenhuma tem as duas. Isso não invalida o diagnóstico: define como ele deve ser lido.

**Convenção de confiança usada em todo o documento:**

| Marca | Significado |
|---|---|
| `[V]` | Verificado por mim nesta sessão, no código ou no corpus. Primário. |
| `[C]` | Medição confirmada por reprodução independente da frente adversarial. |
| `[D]` | Direção confirmada, magnitude contestada. Uso o intervalo, nunca o extremo. |
| `[R]` | Refutado. Registrado para o próximo agente não repetir o erro. |
| `[NM]` | Não medido. |

**Contaminação sistemática a corrigir na próxima rodada de medição:** boa parte dos números originais foi colhida com load average entre 106 e 125 numa caixa de 8 cores, com agentes irmãos vivos. Wall-time sob essa carga é ficção. **Toda medição de performance neste repo deve reportar `/proc/loadavg` do instante, ≥3 repetições, e CPU-time (user+sys) como número primário.** Onde as duas medições divergem, uso a de menor carga.

---

## 1. Diagnóstico em números — onde o tempo vai hoje, e onde é a parede

### 1.1 O corpus (integral, não amostrado) `[V]`

```
ls data/editorial/v2_pages/*.jsonl | wc -l          → 680 shards
cat data/editorial/v2_pages/*.jsonl | wc -lc        → 7.739 linhas / 40.219.025 bytes
```

- 5.197 bytes por página, 11,38 páginas por shard
- 4.313.759 palavras somadas de `word_count` → **557,4 palavras/página** `[C]`
- 20.569 URLs somadas de `official_sources` → **2,66 fontes/página** `[C]`
- 0 arquivos `*.partial.jsonl` (glob limpo) `[C]`
- Os gates processam 7.675 das 7.739 (64 registros filtrados a montante) `[C]`

### 1.2 A cadência real — o número que responde ao dono `[C]`

Extraído de `git log --format='C|%H|%ct' --numstat -- data/editorial/v2_pages/`: 379 commits entre 2026-07-07 e 2026-07-22; somando apenas os intervalos < 60 min (tempo ativo, descontando gaps):

- **47,64 horas ativas de produção → 162 páginas/hora ativa**
- **252 s (4,2 min) de wall por shard de 11 páginas**

Aritmética direta sobre esses números:

| Meta | Páginas a produzir | Horas ativas | Leitura |
|---|---|---|---|
| 10.000 | 2.261 | **14 h** | alcançável nesta semana |
| 100.000 | 92.261 | 570 h | 24 dias corridos de produção ininterrupta |
| 1.000.000 | 992.261 | **6.125 h** | **255 dias corridos, 24/7** |

O dono está certo e o número prova: a 162 páginas/hora, 1M é impossível — mas **1M também é impossível por um motivo pior que lentidão, e é esse motivo que domina este documento.**

### 1.3 As três paredes duras — a fábrica não fica lenta, ela FALHA (C já falha hoje; A e B em ~200-300k)

Esta é a resposta a "a partir de quantas páginas trava". Não é wall-clock. São três muros de construção, cross-corroborados por frentes independentes, e todos chegam MUITO antes de 1M.

**MURO A — limite de entradas por diretório.** `[V]`

```go
// internal/v2readguard/guard.go:38
maxDirectoryEntries = 20_000
```

Constante de compilação, usada em `guard.go:83`, `:98-99` e `:1080`. A 11,38 páginas/shard, 20.000 shards = **~227.600 páginas**. Passou disso, o guard rejeita a leitura do diretório — o pipeline não desacelera, ele para com erro.

**MURO B — memória das estruturas globais do near-dup.** `[C]`, triangulado por 3 frentes.

`candidatePairsExactPrefix` (`internal/v2bodyneardup/neardup.go:184`) constrói três estruturas dimensionadas pelo número de shingles **distintos do corpus inteiro** `[V]`, li o código: `frequencies map[uint64]int`, `ordered []shingleFrequency`, `rank map[uint64]int`. Custo ~96 B por shingle distinto (dois maps Go a ~32-48 B/entrada + slice a 16 B).

Medições convergentes de três frentes sobre o mesmo corpus de 7.675 páginas:

| Fonte | RSS medido |
|---|---|
| `similaridade-e-dedupe` (`/usr/bin/time -v`) | 507.040 kB (495 MiB) |
| `formato-de-dados` | 456 MB |
| `estado-da-arte` (contagem analítica: 4.452.772 distintos × 96 B) | 427 MB |

→ **66,0 KB de RAM por página.** Shingles distintos por página: 575, decrescendo (668 → 639 → 583 → 575 conforme N cresce de 1.000 a 7.739).

Cruzamento de OOM, com a conta explícita: a ~500 distintos/página no limite e 96 B/distinto, 12 GB ÷ 96 B ≈ 125M distintos ≈ **200-300k páginas**; em 19 GB, ≈ **290.000 páginas**.

**As paredes A e B convergem na mesma faixa: 200-300k; a parede C já morde hoje em amostra.** A parede está no caminho, não no destino. Otimizar wall-clock sem mover essas constantes entrega uma fábrica que produz mais rápido até bater no muro na mesma página.

**MURO C — já batido hoje, em amostra.** `[C]` `internal/v2bodysemanticdedup` estoura `confirmed pair budget exceeded: pairs>250000` numa amostra **aleatória cross-vertical de 772 páginas** (aéreo, autônomos, bancário, cidadania, educação, seguros): de 772×771/2 = 297.606 pares possíveis, >84% ficam acima do corte. Isso não é custo quadrático — é **saída quadrática**. O gate não fica lento, ele não termina. E não é uma projeção: acontece hoje, com 10% do corpus.

> **Verificação de código 2026-07-28 (revisão adversarial cowork):** o caminho vivo NÃO é all-pairs — `confirmCandidatePairs` usa índice invertido com filtro de prefixo (`dedup.go:613`); `MaxPairs=250_000` (`dedup.go:116`) conta pares **CONFIRMADOS** ≥ threshold (`dedup.go:657-659`); o O(n²) real é só o oráculo de teste, com cap de 3.000 páginas (`dedup.go:100-102`). Estourar com 772 páginas ⇒ >84% dos pares CONFIRMADOS como near-dup: ou o corpus é molde demais (problema de CONTEÚDO) ou o confirm/threshold está frouxo (bug de GATE) — o diagnóstico decide o fix; subir `MaxPairs` segue proibido. A mesma verificação achou paredes NÃO listadas acima: `internal/v2ingest/v2ingest.go:41` `TransactionalStockMaxRecords=20_000` (limite DIRETO em registros — morde logo após 10k) e `internal/v2internallinkgraph/loader.go:24` `maxPageFiles=16_384` (≈186k págs na densidade atual, mais apertado que o MURO A).

### 1.4 Onde o tempo vai hoje, por categoria

**(a) Cerimônia de invocação — o que o dono sente como "os comandos demoram mesmo com cache".**
Quatro frentes mediram, com pares no mesmo run (wrapper vs binário cacheado direto):

| Frente | Wrapper | Binário direto | Razão |
|---|---|---|---|
| `perfil-dos-gates` | 8,535 s | 0,198 s | 43x |
| `throughput-real` | 8,4 s | 0,078 s | 108x |
| `cache-e-incremental` | 6,60 s REAL / 5,79 s USER | 0,25 s REAL / 0,18 s USER | 26x |
| `quick-wins` | 7,90 CPU-s | 0,18 CPU-s | 43x |

Refutações (em máquina calma, load ~2, ≥3 repetições) derrubam para **~2,6 a 4,4 s** `[R]` nos extremos. **Intervalo honesto a usar: 2,6-8,5 s de cerimônia para 0,08-0,25 s de trabalho útil.** A razão sobrevive à refutação em todas as medições: **entre 15x e 108x de overhead**.

Componente isolado e reprodutível: `sha256sum` do binário cacheado de **241.109.536 bytes** custa **2,39-3,03 s** por invocação `[C]`. O resto é `go env`, `python3` de build-identity, 7 comandos `git` de repo_awareness, `stat`, sha256 do próprio `go-modern` e do toolchain, e um re-exec sob `timeout`.

Volume: **1.186 chamadas em 17 dias ≈ 70/dia** `[C]` (`~/.claude/audit-log.txt`, 58.396 linhas). `tools/run-go-cmd-cached` é caminho quente de 1.507 invocações de `go-modern`, 616 de `audit_v2_pages.py`, 599 de `run-heavy-throttled`.

**Custo fixo por INVOCAÇÃO que escala com o tamanho do REPO, não com o tamanho do trabalho.** É a assinatura desse gargalo, e explica por que "mesmo com cache" não ajuda: o cache que existe é de compilação, não de veredito.

**(b) A suíte de gates.** 304 checks (`var Names`, `internal/checks/checks.go:277`) `[V]`.

- `check all` no caminho serial: **552,55 s de wall / 1.112,82 CPU-s / MAXRSS 7,85 GB**, paralelismo efetivo 2,01x numa caixa de 8 cores `[C]`
- Numa outra rodada, `check all` **não terminou em 411 s** tendo consumido **35,4 s de CPU** — 8,6% de um core. `cat /proc/PID/wchan` = `futex_wait_queue`, 12/12 threads em S. Isso é **bloqueio**, não contenção `[C]` (contador interno ao processo, imune a load externo)
- 112 de 157 checks (71%) rodam em <1 s `[C]`. Os gates individualmente **não** são o gargalo
- **Nenhum dos 304 gates chama modelo**: `grep -rln "anthropic|claude-|api.anthropic" internal/ --include=*.go | grep -v _test` → ZERO `[C]`. Todos determinísticos, CPU-bound

**(c) O build Go.** `[C]`, a frente mais bem medida. E a premissa comum sobre ele está desatualizada:

- **424 pacotes**, não 504 (`./tools/go-modern list ./... | wc -l`)
- **25 main packages**, não 303 — 278 dirs de `cmd/` já estão atrás de `//go:build devcmds` (469 arquivos). *A "unificação de binários em cmd/" já foi feita.*
- Com `-x`: num build para alvo novo, `pkg/tool/linux_amd64/link` **executa com ZERO invocações de `compile`** (1.349 packagefiles vindos do cache) e ainda assim gasta 19,2 s de CPU. **O gargalo é o LINK, não a compilação.**
- Agregado warm: **26,9 s wall / 85,5 s CPU** por `go build ./...` sem nenhuma mudança de código. `cmd/check` sozinho = 19,2 s de CPU
- GOCACHE 5,2 GB com 312 GB livres → saudável, não é fator
- **O(1) em páginas**: linkar binário não lê JSONL. O custo é N_ciclos × 85,5 s CPU, não N_páginas

**(d) O formato de dados — resultado negativo, e ele reorienta a frente inteira.** `[C]`

Ler+parsear os 680 shards inteiros:

| Método | Tempo | Vazão |
|---|---|---|
| scan `bufio` puro | 22,8 ms | 1.762 MB/s |
| `goccy/go-json`, par=8 | 107 ms | 377 MB/s |
| `goccy/go-json` serial | 286 ms | — |
| `encoding/json` tipado | 953 ms | 42,2 MB/s (8.118 rec/s) |

Extrapolação linear a 1M páginas (5,20 GB): **13,8 s com goccy, 124 s com `encoding/json`**. **O container JSONL nunca será o custo dominante, nem aos 10M.** `goccy/go-json v0.10.6` já está no `go.mod` (linha 53) `[V]` — só não está nos caminhos v2.

Corolário executivo: **manter JSONL como fonte da verdade.** Parquet, SQLite e formato binário próprio estão DESCARTADOS como fonte da verdade — quebram review linha-a-linha em git, que é requisito de contrato. Servem só como índice derivado (precedente já existe: `internal/contentinventoryparquet`).

### 1.5 A causa-raiz de tudo: não existe instrumentação

`data/ops/check_performance_ledger.jsonl` tem 303 registros e 28 campos `[V]`, verifiquei as chaves:

```
check_name, record_status, check_group, p0_relevance, coverage_scope, cost_class,
expected_duration_ms, budget_ms, heavy_contract, always_run, requires_probe_before_heavy,
root_cause_required, required_trigger, timing_command, proportional_command,
coverage_preserved_by, optimization_action, slow_command_policy, throughput, stop_condition,
use_policy, index_policy, publication_allowed, render_allowed, sitemap_allowed, public_path,
approval, checked_at
```

**Nenhum é duração observada.** `expected_duration_ms` e `budget_ms` são política escrita à mão. Soma declarada: 14.420.000 ms = 4h00.

E esse metadado fictício **governa o escalonador**: `loadParallelSafeChecks` (`internal/checks/run_context_parallel.go:40`) lê exatamente esses campos declarados para decidir o que paraleliza `[V]`.

Erro medido entre declarado e real `[C]`:

| Check | Declarado | Medido | Erro |
|---|---|---|---|
| `anti-spam-scale-index` | 150.000 ms | 799 ms | **188x** |
| `authorial-mass-release-evidence` | 360.000 ms | 2.013 ms | **179x** |
| `authorial-mass-legal-reviews` | 360.000 ms | 2.359 ms | **152x** |
| `scaled-content-release-verdict` | 180.000 ms | 6.384 ms | **28x** |

**O escalonador da fábrica é dirigido por números inventados, errados em duas ordens de grandeza.** Esse é o único fato que explica simultaneamente: (a) por que a paralelização classifica errado, (b) por que 10 frentes de medição produziram números contestados entre si, (c) por que "otimizar" sem instrumentar seria adivinhação. **É a primeira coisa a consertar.**

### 1.6 O motor paralelo existe e está desligado nos dois entrypoints sancionados `[V]`

```go
// internal/checks/run_context_parallel.go:121
group.SetLimit(runAllParallelism)          // = 6
// cmd/check/main.go:122-123
func allModeMustRunSerial(opts options) bool {
	return opts.serial || opts.maxDuration > 0 || opts.timings || opts.failFast
}
```

O comentário em `main.go:112-121` diz que "o modo `all` nu (a invocação canônica do lab-cycle/maestro, sem flags) segue paralelo". **Isso não é verdade na prática.** Verifiquei os dois chamadores:

```
tools/lab-cycle:31   run_step check-all-contracts ./tools/go-modern run ./cmd/check all --timings
tools/check-all:33   run_step check-all-contracts ./tools/run-check all --timings
```

Ambos passam `--timings` → `allModeMustRunSerial` devolve `true` → o pool de 6 é **código morto em produção**. 246 de 304 checks estão classificados como parallel-safe e nunca rodam em paralelo.

**Instrumentar hoje = desligar o paralelismo.** É um trade-off absurdo que ninguém escolheu — é um acoplamento acidental entre duas flags. Corrigir custa pouco e destrava a observabilidade de todo o resto.

---

## 2. O que é O(n²) — a lista completa, com arquivo:linha

Complexidade quadrática é o único teto que hardware não resolve. Mas a lista precisa de três categorias distintas, porque confundi-las manda o próximo agente otimizar o laço errado.

### 2.1 Quadrático ATIVO — falha hoje

**`internal/v2bodysemanticdedup` (`cmd/check-v2-body-semantic-duplicates`)** — `[C]`
Saída quadrática, não custo quadrático. Em amostra aleatória cross-vertical de 772 páginas estoura `confirmed pair budget exceeded: pairs>250000`; >84% dos 297.606 pares possíveis ficam acima do corte. **Não termina no estoque real.** É o único quadrático que já quebra a fábrica hoje.
O oráculo tem cap: `DefaultAllPairsPageCap = 3_000` (`internal/v2bodysemanticdedup/dedup.go:102`) `[V]` — mas o cap protege o oráculo, não o gate.

### 2.2 Quadrático LATENTE — O(n²) no código, hoje fora do caminho quente

**`topPairsFor` — `internal/authorialmasssimilarity/similarity.go:315-343`** `[V]`, li o laço:

```go
for i := 0; i < len(records); i++ {
    for j := i + 1; j < len(records); j++ {
        score := jaccard(recordNgrams[i], recordNgrams[j])
```

All-pairs cego, sem filtro de candidatos. Constante medida: **78,6 µs de CPU por par** (calibrada a 751 4-gramas por corpo) `[D]`:

| N | Pares | CPU |
|---|---|---|
| 7.178 (hoje) | 25.755.253 | 2.024 s = **33,7 min** |
| 10.000 | 49.995.000 | 3.930 s = **65,5 min** |
| 1.000.000 | 5×10¹¹ | inviável por qualquer margem |

Assinatura quadrática visível: 1,39x de páginas → 1,94x de custo.

**Ressalva que muda a prioridade `[R]`:** a refutação estabelece que este é um **gerador legado que roda fora do ciclo**, e que os checks que consomem sua saída custam **1,15 s**. Ou seja: **não é o custo de hoje.** É um teto latente que precisa ser eliminado antes de qualquer aumento de escala que o coloque no caminho quente. Trate como dívida arquitetural, não como emergência.

### 2.3 Quadrático CAPADO — por construção, nunca dispara em lote

- `DefaultAllPairsPageCap = 2_000` — `internal/v2bodyneardup/neardup.go:54` `[V]`
- `DefaultAllPairsPageCap = 3_000` — `internal/v2bodysemanticdedup/dedup.go:102` `[V]`

Oráculos O(n²) que existem para validar o caminho rápido contra o exaustivo. Capados, corretos, não mexer. Não contam como teto.

### 2.4 NÃO é quadrático — e é importante registrar, porque parece

**`candidatePairsExactPrefix` (`internal/v2bodyneardup/neardup.go:184`).** Expoente medido de 784 → 7.675 páginas: **1,02 (linear)** `[C]`. Zero pares candidatos, zero posting scans no corpus real — o corpus é genuinamente distinto, então a comparação de pares não custa nada. **O custo é 100% construção de índice, e a parede é MEMÓRIA, não tempo** (§1.3, MURO B).

**O tier determinístico inteiro é linear, e o pedaço relacional é SUB-linear** — expoente medido **0,91** `[C]`. Base: 0,176 ms/página (estrutural) + 0,26 ms/página (relacional). O repo já resolveu a parte quadrática do dedupe com winnowing 5-gram + postings invertidos em pebble (`INCREMENTAL_CANDIDATE_GENERATION`, `tools/audit_v2_pages.py:196`).

**Veredito da seção:** só existe **um** quadrático que impede escala hoje (§2.1) e **um** que a impedirá amanhã (§2.2). O resto do custo é constante-por-invocação e memória — não complexidade.

---

## 3. Arquitetura alvo para 1M de páginas

Cinco mudanças estruturais. Nenhuma inventa algoritmo novo: quatro das cinco já existem no repo e simplesmente não estão no caminho quente.

### 3.1 Índice em vez de varredura

O JSONL continua sendo a fonte da verdade (diffável, revisável em git, auditável — requisito de contrato). O que muda é que **nenhum gate relacional pode reconstruir estrutura global do zero a cada rodada**.

- **Gate lexical → `legalsignature.StreamDeduper`** (`internal/legalsignature/streamdedup.go:195`, cascata em `cascade.go:61-73`) `[V]`. Motor streaming já testado até 300k, **shardável e mergeável** (`Merge` reduz por banda, `streamdedup.go:26`), cascata Bloom (duplicata exata) → MinHash+LSH → telemetria. Hoje só é alcançável por `internal/fiscalization` → `cmd/fiscalize`; **não está em `internal/checks` nem em `tools/`**. Falta exatamente: (a) adaptador `v2ingest.LoadPages` → `StreamDeduper.AddWithID`, (b) evidência A/B contra o gate atual, (c) `case` em `internal/checks/checks.go` + wrapper `tools/check-*`. **Zero algoritmo novo.** Memória: **1,48 KB/página** (medido em 300k) contra 66,0 KB/página do gate atual = **45x**.
- **`topPairsFor` → prefix filter de Jaccard** já implementado em duas variantes no repo: `candidatePairsExactPrefix` (`neardup.go:184`) e o invertido paralelo de `internal/authorialmassglobalsimilarity`, sobre `internal/densepairset` (bitset denso até 64M pares, roaring64 acima, sparse depois).
- **Decoder `goccy/go-json` nos 16 caminhos v2** (`grep -rln LoadPages --include=*.go`). Já no `go.mod`.

### 3.2 Veredito cacheado por hash

Existem ~9 GB de cache no repo — GOCACHE 5,2 GB, `.cache/go-cmd-bin` 2,4 GB, factorygraph 1,2 GB + 568 MB, `languagetool_quality_cache.jsonl` 449 MB `[C]` — e **nenhum byte deles guarda veredito de gate por página**. O cache cobre compilação e sub-fases; o julgamento é refeito 100% a cada rodada.

**Sidecar de veredito, chaveado por `sha256(registro) + fingerprint(algoritmo)`.** `internal/v2ingest/validator_fingerprint_graph.go` **já implementa** o fingerprint do algoritmo com walk limitado `[C]` — falta ligá-lo ao caminho quente.

Gate-neutro por construção, e este é o argumento que sustenta: **cache hit só ocorre quando o registro é byte-idêntico E o algoritmo do validador é idêntico.** Qualquer mudança no conteúdo ou no gate invalida a entrada. Não é reuso de julgamento entre páginas diferentes — é evitar recomputar o mesmo julgamento sobre o mesmo byte com o mesmo código. Isso converte a auditoria de corpo de **O(N) para O(delta)**, que é a diferença entre re-auditar 1M de páginas e re-auditar as 300 que mudaram.

### 3.3 Gates por tipo

| Tipo | Exemplos (nomes reais em `checks.Names`) | Custo medido | Estratégia em 1M |
|---|---|---|---|
| **Estrutural O(1)/página** | `canonicals`, `crawlability`, `seo`, `seo-oracles`, `sitemaps`, `content-quality`, `robots-drift`, `html-readability`, `html-minify`, `p2-thin-content-gate`, `ptbr-unicode-quality`, `ptbr-text-segmentation`, `ptbr-confusables-quality`, `legal-oab-compliance`, `v2-stock-freshness` | 1.761 ms/10k = **0,176 ms/pág** | **100% sempre.** Streaming por shard, uma passada, sem índice. Já é O(1). |
| **Relacional** | near-dup lexical, semantic dedup, similaridade global | 0,26 ms/pág, expoente 0,91 | **100%, via índice incremental.** Nunca all-pairs. Delta-only por sidecar. |
| **Semântico (juízo de modelo)** | nenhum gate Go — é o **agente de escrita/revisão** | custo em tokens, não em CPU | **Amostragem estatística com rejeição de LOTE.** Ver §4. |

**Conta do tier determinístico a 1M:** (0,176 + 0,26) ms × 10⁶ = 436 s ≈ **7,3 min em 1 core**; com a paralelização real (§3.4), **~1 min**. A frente `qualidade-sem-custo` chega a ~28 min em 1 core somando os gates estruturais completos e ~5 min em 8 cores `[C]`. **Em qualquer das duas contas, os 304 gates determinísticos NÃO são o obstáculo a 1M.** O obstáculo é memória (§1.3) e cerimônia (§1.4a).

### 3.4 Paralelismo real

Três destravamentos, em cascata:

1. **Desacoplar `--timings` de `allModeMustRunSerial`** (`cmd/check/main.go:123`). Instrumentar o próprio `runAllPhased`: cada goroutine já envolve o check em `runCheckRecovered` — cronometrar ali e emitir num slice indexado por posição de `Names` (mesma técnica determinística já usada para os `Results`). Isso preserva byte a byte os três contratos observáveis documentados em `main.go:112-121` (ordem de saída = ordem de `Names`; passes seguidos de falhas; exit code).
2. **Reclassificar `parallel_safe` a partir de duração OBSERVADA**, não declarada (§1.5).
3. **Paralelizar os 15 checks de supply-chain/toolchain** — 4.230.000 ms declarados, 38,5% do custo serializado de hoje, e **O(1) em páginas** `[C]`. Em 1M essa fatia colapsa para ruído; hoje domina.

Nota de honestidade sobre a escala: os 38,5% de supply-chain são um número de HOJE. Em 1M de páginas, o trabalho de corpus vira ~100% do custo e otimizar SCA não move nada. **Priorize SCA para a produção de hoje, não para a arquitetura de 1M.**

### 3.5 Build incremental

O link é o custo, não a compilação (§1.4c). Duas mudanças:

- **`-ldflags="-w -s"` no wrapper `tools/go-modern`** (não só no `.githooks/pre-commit` — aplicar só no hook cria alternância de fingerprint do binário e piora o cache de invocação). Remove DWARF e symtab, que são artefatos de debug e não entram em decisão de check nenhum.
- **Reduzir o grafo de `cmd/check`**: sqlite/pebble/parquet/zoekt inflam o binário para 241 MB. **ATENÇÃO — a rota óbvia está DESCARTADA** `[R]`: `checks.Names` (`checks.go:277-390`) e o dispatch acoplam esses três pacotes como gates vivos; um `//go:build` ali ou quebra a compilação ou **remove check do `RunAll`** — o que seria enfraquecer gate. A rota correta é extrair os gates que dependem desses pacotes para binários satélites invocados pelo runner, mantendo os 304 no `RunAll`. Esforço maior do que parecia, ganho estimado `[NM]`.

---

## 4. Qualidade em escala — a resposta explícita ao dono

> "Os conteúdos e a engenharia é feita por IA, mas tem como manter qualidade, sem deixar tudo lento?"

**Tem. E a resposta não passa por amostrar gate.** Passa por três fatos medidos:

**Fato 1 — a qualidade determinística é praticamente de graça.** Os 304 gates custam **0,436 ms por página** somando estrutural + relacional `[C]`. A 1M de páginas isso é ~7 min em 1 core. **A qualidade determinística não é o que deixa a fábrica lenta.** O que deixa lenta é a cerimônia de invocação (2,6-8,5 s para 0,18 s de trabalho) e a memória do near-dup — **nenhum dos dois é qualidade, os dois são engenharia mal-feita ao redor da qualidade.** Corrigir os dois não toca em um único limiar.

**Fato 2 — o que custa dinheiro é o tier semântico, e ele não é um gate Go.** Zero dos 304 checks chama modelo `[C]`. O julgamento semântico está no **agente que escreve e revisa**, e o custo dele é em tokens por página, não em CPU. A 162 páginas/hora ativa, esse é literalmente o custo de produção da fábrica.

**Fato 3 — a lentidão percebida é 90% overhead constante.** Um check de 0,198 s custando 8,5 s é a frase inteira do dono ("os comandos demoram, mesmo com cache") traduzida em número.

### 4.1 O que NUNCA pode ser amostrado, e por quê

Esta lista é vinculante. Amostrar qualquer item abaixo é fraude operacional, não otimização.

| Nunca amostrar | Razão técnica |
|---|---|
| **Proveniência de fonte oficial** (URL, data, hash) | É verificação **por página**, não relacional. Amostrar significa publicar página cuja fonte ninguém verificou. Custo O(1)/página — amostrar não economiza nada mensurável. |
| **Unicidade / duplicidade** | O dano de um falso-negativo é uma **doorway page indexada**. E o gate é sobre o **par** — amostrar páginas amostra pares quadraticamente pior. Deve ser 100% via índice (§3.1), nunca por amostra. |
| **Title / meta / canonical / robots / H1 / sitemap** | O(1)/página, dentro dos 0,176 ms. Um canonical errado numa página não amostrada é uma URL quebrada em produção. Custo de amostrar ≈ custo de rodar. |
| **PT-BR, thin content, OAB/Provimento 205, paid-intent** | Idem: estrutural O(1). Uma promessa de resultado numa página não amostrada é risco disciplinar real, não estatístico. |
| **`published_manifest` / cadeia de release** | Transacional por definição. Amostrar uma transação não significa nada. |

**Regra geral:** gate O(1) por página **nunca** se amostra, porque amostrar não economiza. Só faz sentido discutir amostragem onde o custo por unidade é alto — e no repo isso é exatamente **um** lugar.

### 4.2 O único lugar onde amostragem é legítima: o tier semântico, com rejeição de LOTE

O juízo semântico de modelo (o agente lendo o texto e julgando se é bom conteúdo jurídico) é o único componente cujo custo por página é caro em dinheiro e que **não tem gate determinístico equivalente**. Para ele, e só para ele:

**Amostragem estatística com rejeição de LOTE — que é MAIS estrita que revisão por página, não menos.**

- Amostra aleatória de tamanho estatisticamente determinado por lote de produção
- **Se a amostra reprova, o LOTE INTEIRO volta.** Nenhuma página do lote publica.
- Não existe "página aprovada por não ter sido sorteada": o veredito é do lote, e o lote só passa inteiro ou volta inteiro
- Todas as páginas do lote continuam passando pelos **304 gates determinísticos, 100%, sem exceção**

Por que isso **não** é afrouxar gate: sob revisão semântica por página, uma página ruim reprova só a si mesma e as outras 10 do shard publicam. Sob rejeição de lote, uma página ruim **derruba as 11**. A pressão sobre o gerador é maior, não menor. O que a amostragem economiza é o custo do **julgamento**, não o rigor do **critério**.

Isto já tem precedente no repo: o contrato diz *"reprovar o lote inteiro se a amostra indicar molde"*. A arquitetura só torna sistemático o que a política já manda.

### 4.3 O que está proibido, explicitamente

- Aumentar timeout para "resolver" lentidão — proibido por contrato
- Mover qualquer limiar (similaridade < 0.70, thin content, paid-intent, PT-BR)
- Remover check de `RunAll` para acelerar build (é a armadilha do §3.5)
- Trocar prefix filter exato por SimHash/LSH **no gate lexical de veredito** sem A/B — LSH tem falso-negativo probabilístico; o prefix filter não tem (ver §5, fase 3, item 13)
- Publicar lote não verificado "para refinar depois"

---

## 5. Plano por fases

### FASE 1 — Quick wins (dias). Zero mudança de gate, zero algoritmo novo.

| # | Mudança | Arquivo | Ganho | Confiança | Risco |
|---|---|---|---|---|---|
| 1 | **Duração observada no ledger.** Sink de tempo em `runCheckRecovered`, campo `observed_duration_ms` em `check_performance_ledger.jsonl` | `internal/checks/run_context_parallel.go` | Nenhum direto — **é pré-requisito de tudo** | `[V]` que o campo não existe | nulo |
| 2 | **Desacoplar `--timings` do modo serial** | `cmd/check/main.go:123` + sink do item 1 | 1,25x na suíte por Amdahl; **destrava o pool de 6, hoje código morto** | `[V]` (grep em `lab-cycle:31`, `check-all:33`) | baixo — 3 contratos observáveis a preservar, documentados em `main.go:112-121` |
| 3 | **Lote de checks via `--checks a,b,c`** (flag já existe: `main.go:220`, `parseCheckList:284`) em vez de N invocações | `data/ops/check_performance_ledger.jsonl` (`timing_command`), wrappers `tools/check-*` | **4,1x medido** (8 checks: 56,21 → 13,65 s CPU) | `[C]` | baixo |
| 4 | **`-ldflags="-w -s"`** — uma linha | `tools/go-modern` (wrapper, **não** só o hook) | **-40% wall / -50% CPU** medido: 26,9 → 14,3-17,1 s wall; 85,5 → 39,5-46,4 s CPU; `cmd/check` 17,6 → 7,8 s | `[C]` | baixo — verificar `internal/factoryinventoryindex` que inspeciona o binário |
| 5 | **Identidade por inode** `(dev,ino,size,mtime_ns,ctime_ns)` no lugar do SHA-256 do binário de 241 MB, com hash completo só em divergência — técnica **já usada** em `tools/audit_v2_pages.py:141` para shards | `tools/run-go-cmd-cached` | **-2,4 a -3,0 CPU-s por invocação** × 70/dia | `[C]` | baixo — mantém verificação de frescor em toda invocação, só troca o método |
| 6 | **Tirar o wrapper do caminho quente do writing** — invocar `.cache/go-cmd-bin/<cmd>/<cmd>` direto, verificando frescor pelo `build-binary.sha256` que já existe | `scripts/workflows/writing-mass.js` (regra 7, 3-5 invocações por lote, todas sob `flock` global) | **-25 a -42 s por lote**; -90 a -150 s quando dispara rebuild | `[D]` (razão sobrevive, magnitude contestada) | médio — o lock global fail-fast anula a janela de 6 agentes; revisar junto |
| 7 | **Seleção proporcional dos 15 SCA** (mantendo-os obrigatórios quando o diff toca dependência/toolchain/workflow) | `tools/generate-check-selection-profiles` | **88,1 s por rodada de conteúdo**, medidos check a check | `[C]` | baixo |

**Validação da fase 1:** com o item 1 pronto, rodar `check all` antes/depois de cada item e comparar `observed_duration_ms` por check. Critério de aceite: **conjunto de checks executados idêntico, mesmos vereditos, mesmas mensagens**. Qualquer divergência de veredito reverte o item.

**Ganho agregado esperado da fase 1:** os comandos do dia-a-dia de ~8,5 s para <1 s (o que o dono sente primeiro), a suíte de 552 s para a faixa de 200-300 s. **Não move nenhuma parede.**

### FASE 2 — Índices e cache de veredito (semanas). Tira O(N) do caminho quente.

| # | Mudança | Ganho | Confiança | Risco |
|---|---|---|---|---|
| 8 | **Sidecar de veredito por `sha256(registro) + fingerprint(algoritmo)`**, usando `internal/v2ingest/validator_fingerprint_graph.go` que já existe | Auditoria de corpo de **O(N) → O(delta)**. Hoje 448 s por passada completa | `[C]` que o fingerprint existe; ganho `[NM]` em delta real | baixo — gate-neutro por construção (§3.2). **Exige teste de invalidação: mudar o gate DEVE invalidar todas as entradas.** |
| 9 | **`StreamDeduper` no gate lexical v2** — adaptador `v2ingest.LoadPages` → `AddWithID`, A/B contra o gate atual, `case` em `checks.go` + wrapper | Memória **66,0 → 1,48 KB/página = 45x**. Teto na mesma caixa de 19 GB: **~290k → ~13M páginas** | `[C]` (1,48 KB medido em 300k) | médio — **exige evidência A/B antes de substituir**: a cascata é Bloom (exato) → MinHash+LSH; provar recall ≥ atual sobre o corpus real, senão não substitui |
| 10 | **Decoder `goccy` nos 16 caminhos v2** | Decode é ~1/3 dos 12,93 s CPU do gate; 3,3x nesse terço = **-23% do gate**. 1M: 28 → 21,5 min | `[C]` | baixo — troca de biblioteca de parse, sem semântica |
| 11 | **Prefix filter em `topPairsFor`** (`similarity.go:315-343`), usando `internal/densepairset` + o filtro de `neardup.go:184` | Referência medida no próprio repo: `check-v2-body-near-duplicates` faz 7.675 páginas com `strategy=exact_prefix` em **12,84 s user CPU**, contra os **2.024 s (33,7 min)** do all-pairs cego | `[D]` — a constante de 78,6 µs/par é derivada, não cronometrada ponta a ponta | **baixo, e este ponto é crítico:** o prefix filter de Jaccard (PPJoin) **não é heurística probabilística** — dado um limiar t, descarta apenas pares que **provadamente** não podem alcançar t. Zero falso-negativo. É troca **exatamente equivalente**, não aproximação. |
| 12 | **Elevar `maxDirectoryEntries`** de 20.000 e/ou introduzir hierarquia de subdiretórios | Move o MURO A de ~227k para onde se quiser | `[V]` que a constante existe; novo teto `[NM]` | médio — o guard existe por razão de segurança; ler `internal/v2readguard` antes de mexer, **não** simplesmente aumentar o número |

**Validação da fase 2:** A/B obrigatório em cada gate substituído — mesmo corpus, comparar conjunto de pares reportados. O item 9 só entra se o recall for **≥** o atual. Instrumentar `pages/s` e `RSS/página` antes e depois.

### FASE 3 — Arquitetura de 1M (a partir do momento em que 100k estiver estável)

| # | Mudança | Ganho | Confiança | Risco |
|---|---|---|---|---|
| 13 | **Count-Min Sketch no lugar de `frequencies`+`rank`** no near-dup | **96 B → 16 B por shingle distinto = 12x**. 1M: de **OOM em 48 GB numa caixa de 19 GB** para **~4,0 GB**. Destrava a faixa 200k-1M, hoje impossível | `[C]` na medição de memória; **é a única solução das 10 frentes marcada VÁLIDA** | **nenhum ao gate**, e a prova é específica: `exactPrefixLength` (`neardup.go:227`) depende apenas de `\|shingles\|` e do threshold, **nunca de frequência**. O lema do prefix filter não tem falso-negativo sob **qualquer ordem total consistente** — a ordenação por frequência é heurística de redução de candidatos (Chaudhuri/Bayardo), não requisito de correção. O CMS dá uma ordem total determinística (`est(h)`, desempate por hash). |
| 14 | **Resolver a saída quadrática do semantic dedup** (`internal/v2bodysemanticdedup`) — o `pairs>250000` que já estoura em 772 páginas | Sem isso o gate semântico **não termina** nem em 10k | `[C]` na falha | alto — é redesenho do critério de confirmação de par, não otimização. **Não pode virar "aumentar o budget"**: isso seria descartar pares sem julgá-los. |
| 15 | **Shard + merge distribuído do `StreamDeduper`** (`Merge` reduz por banda, já implementado) | Dedupe cross-shard sem materializar estrutura global. Habilita produção paralela real por vertical | `[C]` que o `Merge` existe | médio |
| 16 | **Extrair gates sqlite/pebble/parquet/zoekt para binários satélites**, mantendo os 304 em `RunAll` | Reduz os 241 MB e o link de 19,2 s CPU de `cmd/check` | `[NM]` | médio-alto — ver a armadilha do §3.5 |

**IMPORTANTE sobre o item 13:** apesar de ser a única solução validada, **não pertence à fase 1**. A sua própria refutação estabelece a prioridade correta: *o gate inteiro custa 16,2 s; otimizá-lo devolve ~10 s ao dono.* **Aos 10k, o CMS não compra ganho perceptível.** Ele compra a faixa 200k-1M, que é onde a fábrica hoje simplesmente morre. Fazer na ordem errada é gastar semanas para economizar 10 s.

---

## 6. Ordem de execução, por (ganho × escala destravada) / esforço

**Regra de ouro desta ordem: instrumentar antes de otimizar.** Dez frentes mediram e produziram números contestados entre si porque a fábrica não se mede. Otimizar sem o item 1 é adivinhar.

1. **Item 1 — duração observada no ledger.** Esforço baixo, ganho direto zero, **desbloqueia tudo**. O escalonador está sendo dirigido por metadado errado em 152-188x. Nada abaixo é confiável sem isso.
2. **Item 2 — desacoplar `--timings`.** Esforço baixo. Enquanto não existir, o pool de 6 é código morto e nenhuma otimização de paralelismo é sequer **observável**. Fecha o par com o item 1.
3. **Item 4 — `-ldflags="-w -s"`.** Uma linha, -40% wall / -50% CPU, medição confirmada. **Melhor razão ganho/esforço do documento inteiro.**
4. **Itens 3 + 5 + 6 — matar a cerimônia de invocação.** É literalmente a queixa do dono. 4,1x no lote, -2,4 CPU-s no hash, -25 a -42 s por lote de escrita. Esforço baixo-médio.
5. **Item 7 — seleção proporcional dos SCA.** 88,1 s por rodada, esforço baixo.
6. **Item 9 — `StreamDeduper` no gate lexical.** Primeiro item que **move uma parede**: 290k → 13M. Esforço médio (o motor existe e está testado), risco controlado por A/B.
7. **Item 8 — sidecar de veredito.** Converte O(N) em O(delta). É o que torna re-auditoria viável a 1M.
8. **Item 12 — `maxDirectoryEntries`.** Move o outro muro. Ler o guard antes.
9. **Itens 10 + 11 — goccy e prefix filter em `topPairsFor`.** Elimina o quadrático latente antes que ele entre no caminho quente.
10. **Item 13 — CMS.** Quando 100k estiver estável, para abrir 1M.
11. **Item 14 — saída quadrática do semantic dedup.** Redesenho; caro; mas sem ele não há gate semântico determinístico em escala nenhuma.
12. **Itens 15 + 16.** Últimos.

**Por que esta ordem e não "atacar o O(n²) primeiro":** porque a medição diz que o quadrático ativo é **um só** (§2.1) e o latente está **fora do ciclo** (§2.2), enquanto o custo que o dono sente hoje é **constante por invocação** (§1.4a) e a parede que mata 1M é **memória** (§1.3). Ordenar por "quadrático primeiro" seria ordenar pela intuição, não pelo número.

---

## 7. Como medir progresso

Hoje **não existe instrumentação de duração observada** (§1.5). Esta seção é a contrapartida executável do item 1 — sem ela, o próximo agente repete o mesmo ciclo de números contestados.

### 7.1 Métricas de topo (o painel do dono)

| Métrica | Baseline medido | Alvo fase 1 | Alvo 1M | Onde instrumentar |
|---|---|---|---|---|
| **Páginas/hora ativa** | **162** | 400+ | 5.000+ | derivado de `git log --numstat -- data/editorial/v2_pages/`, gaps < 60 min |
| **Wall por shard de 11 páginas** | **252 s (4,2 min)** | < 90 s | < 8 s | idem |
| **Cerimônia por invocação (CPU-s)** | **2,6-8,5 s** (trabalho útil: 0,08-0,25 s) | < 1,0 s | < 0,3 s | `tools/run-go-cmd-cached`, log de `%U+%S` por chamada |
| **Wall do ciclo completo (`check all`)** | **552,55 s / 1.112,82 CPU-s / 7,85 GB RSS** | < 250 s | < 120 s | sink do item 1 |
| **Gate por página (determinístico)** | **0,436 ms** (0,176 estrutural + 0,26 relacional) | manter | manter | idem, dividido por `pages` |
| **RSS por página no near-dup** | **66,0 KB** | 66,0 KB (não muda na fase 1) | **1,48 KB** | `/usr/bin/time -v`, `Maximum resident set size ÷ pages` |
| **Páginas até o muro** | **~200-300k** (min entre MURO A e MURO B) | ~227k | > 10M | cálculo derivado, recomputar a cada mudança em `maxDirectoryEntries` ou no near-dup |
| **Build agregado warm** | **26,9 s wall / 85,5 s CPU** | 14-17 s / 40-46 s | idem (O(1) em páginas) | `time ./tools/go-modern build ./...` sob envelope |

### 7.2 Onde instrumentar, concretamente

1. **`internal/checks/run_context_parallel.go`** — cada goroutine já envolve o check em `runCheckRecovered`. Cronometrar ali, emitir num slice indexado por posição de `Names` (mesma técnica determinística já usada para os `Results`). Isso serve simultaneamente ao `--timings` e ao ledger, e é o que permite desacoplar a flag do modo serial (item 2).
2. **`data/ops/check_performance_ledger.jsonl`** — adicionar `observed_duration_ms`, `observed_at`, `observed_loadavg`, `observed_pages`. **Manter `expected_duration_ms` separado**: a divergência entre declarado e observado é ela mesma um sinal de saúde (hoje: 152x). `loadParallelSafeChecks` (`run_context_parallel.go:40`) deve passar a ler o campo **observado**.
3. **`tools/run-go-cmd-cached`** — emitir uma linha por invocação com `%U+%S` de cerimônia vs `%U+%S` do binário. Esta é a métrica que responde diretamente à queixa "os comandos demoram mesmo com cache".
4. **Todo gate relacional** — emitir `pages=`, `pairs=`, `candidates=`, `posting_scans=`, `rss_kb=`, `elapsed=` (o `check-v2-body-near-duplicates` **já faz isso** com `--timings`: `load=... scan=... pages=7675 pairs=0 strategy=exact_prefix elapsed=...` — padronizar esse formato para os demais).

### 7.3 Disciplina de medição (vinculante)

- **Sempre** reportar `/proc/loadavg` do instante da medição
- **Sempre** ≥3 repetições, reportar mínimo (não média — a média sob carga é ruído)
- **CPU-time (user+sys) é o número primário.** Wall-time só vale em máquina calma e deve ser rotulado
- **Nunca** comparar wall medido sob load 106 com wall medido sob load 2. Metade das divergências entre as 10 frentes veio exatamente disso

### 7.4 Lacunas conhecidas — `[NM]`, a fechar

- Ganho real do sidecar de veredito em delta típico (quantas páginas mudam por rodada)
- Novo teto seguro para `maxDirectoryEntries` (depende de ler o racional do guard)
- Ganho do item 16 (binários satélites)
- Custo por token do tier semântico por página — **é o custo de produção real e ninguém mediu**
- Recall comparado `StreamDeduper` vs gate lexical atual sobre o corpus real (o A/B do item 9)

---

*Documento durável em `/tmp/claude-1000/-opt-wiki/031af06c-5857-47a3-b518-fee816243066/scratchpad/ARQUITETURA_ESCALA_FABRICA.md`. Verificações primárias feitas nesta sessão: `internal/v2readguard/guard.go:38`, `internal/checks/run_context_parallel.go:40,121`, `cmd/check/main.go:122-123,220,284`, `internal/checks/checks.go:277`, `internal/v2bodyneardup/neardup.go:54,184`, `internal/v2bodysemanticdedup/dedup.go:102`, `internal/authorialmasssimilarity/similarity.go:315-343`, `internal/legalsignature/streamdedup.go:26,195`, `tools/lab-cycle:31`, `tools/check-all:33`, corpus integral (680 shards / 7.739 linhas / 40.219.025 B), 28 campos do ledger.*