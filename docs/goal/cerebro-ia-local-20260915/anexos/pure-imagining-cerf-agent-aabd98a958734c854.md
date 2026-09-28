# Modo de operação do cérebro ao vivo — varredura 5/5

Sessão em PLAN MODE. Tudo abaixo foi **lido ou medido** em 2026-09-15/16 nesta
máquina. Nada foi executado do que o roteiro manda executar. Onde diz "não
medido", não foi medido, e o motivo está escrito.

---

## 0. O que está no ar AGORA (medido, com hora)

| grandeza | valor medido | como |
|---|---|---|
| unit | `active (running)`, `MainPID=926445`, `NRestarts=1`, `Result=success` | `systemctl show wikijuridica-cerebro.service` |
| de pé desde | `2026-09-14 04:40:57 -03` (≈ 40 h) | `ExecMainStartTimestamp` |
| `WatchdogUSec` | **0** — worker travado fica `active (running)` para sempre | `systemctl show -p WatchdogUSec` |
| `RestartUSec` / StartLimit | `15s` / `10s` e `5` (defaults do manager, **não** declarados na unit) | `systemctl show` |
| fila | 34.217 `pendente` · 3 `executando` · 8.271 `concluida` · 39 `erro` (extrair_dispositivos/qwen3.5:4b) | `sqlite3 file:…?mode=ro` (1,018 s) |
| embeddings | 11.248 `concluida` · 5 `erro` (qwen3-embedding:0.6b) | idem |
| último item concluído | `2026-09-16T00:08:36Z`, 63 s antes da leitura | idem |
| concluídas em 24 h | **1.993** | idem |
| residente no Ollama | `qwen3.5:4b`, `size=3.227.894.413` (3,01 GiB), `size_vram=0`, `context_length=8192`, `expires_at` +10 min | `GET /api/ps` (0,064 s) |
| modelos no disco | 9, maior `qwen2.5-coder:14b` 8,99 GB | `GET /api/tags` (0,020 s) |
| ocupação do Ollama pelo cérebro | **93,3 % em 24 h · 90,7 % em 168 h** | Σ`custo_segundos_maquina` ÷ span, `data/ops/ia_local_daily.jsonl` |
| custo por tarefa | **43,6 s** (24 h, 1.850 tarefas com chamada real) · 29,1 s (168 h, 18.784) · 56,3 s (série inteira, 8.145) | idem |
| prefill / decode | p50 **13,6** / **5,4** tok/s (série) — **caiu para ~8–11 / ~3,0–3,9** na última hora | idem + journal |
| `bin/cerebro` | `vcs.revision=3dd00bd2` (2026-09-11T05:03Z), `vcs.modified=true`; HEAD é `62d71de0` | `go-modern version -m` |
| `check-binario-vs-fonte` | **verde para `cerebro`** (nenhum commit tocou o fecho desde 3dd00bd2); vermelho pré-existente para `server` e `social` (commit `a666aca4`) | execução read-only, exit 1 |
| loadavg durante a varredura | 15,84 → 8,55 (cinco varreduras paralelas) | `/proc/loadavg` |

**Fato operacional que muda a leitura de qualquer número desta sessão:** às
`20:57:04 -03` o journal registra
`pausa: … loadavg de 1 min em 12.46, acima do teto de 12.00`, com retomada
`1m55s` depois. O teto `--carga-max 12` (`saude.go:89`, `CargaMaxPadrao`) estava
**mordendo**, e o decode caiu de 5,6 para 3,0 tok/s na mesma janela. Número de
tok/s medido hoje é **teto inferior**, não a capacidade da máquina. Declare a
carga junto com o número, sempre.

---

## 1. O conjunto mínimo que responde em segundos

Cinco perguntas, quatro comandos, **2,1 s somados** (medidos). Nenhum muta
estado. Ordem: do mais barato ao mais caro.

### 1.1 `cerebro status` NÃO serve — e isso é achado, não preferência

`status()` (`cmd/cerebro/main.go:404`) chama `cerebro.Abrir`, que abre o banco
**sem `mode=ro`** (`fila.go:286`, `DSN()` em `fila.go:267-273`), roda
`EsquemaSQL` (`CREATE TABLE IF NOT EXISTS`, `fila.go:291`), depois
`precisaMigrarParaV2` (`fila.go:294`) e `registraVersaoSeVazio` (`fila.go:302`).
É caminho de **escrita**: toma o lock de escrita e roda DDL a cada chamada,
contra o banco que o worker está usando. `cerebro status --triagem` ainda varre
o `payload` de **todas** as 34.214 pendentes (`fila.go:550`) — 54.170.394 bytes,
medidos.

O padrão read-only que **já existe no repo** é
`cmd/medir-prompt-sumula-pareado/main.go:348`:
`sql.Open("sqlite", "file:"+caminho+"?mode=ro")`.

> Armadilha de PATH: o `sqlite3` desta máquina é
> `/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3` (3.50.6).
> Unit ou gate com `PATH=/usr/bin:/bin` — como `restartsDoServico`
> (`saude.go:268-272`) usa — **não o encontra**. Ferramenta de verdade usa
> `modernc.org/sqlite`, que já está no `go.mod`; o shell só serve para o
> operador no terminal.

### 1.2 Os quatro comandos

```bash
# (a) 0,02 s — o worker existe e desde quando; o watchdog está desligado
systemctl show wikijuridica-cerebro.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result \
  -p ExecMainStartTimestamp -p WatchdogUSec --no-pager

# (b) 0,064 s — qual modelo está residente, quanto ocupa, e quando expira
curl -s --max-time 5 http://127.0.0.1:11434/api/ps
# campos que importam: .models[].name  .size  .size_vram  .context_length  .expires_at
# (expires_at - agora) contra o keep_alive da tarefa (10m em extrair_dispositivos,
#  cmd/cerebro/main.go:780) diz há quanto tempo NÃO há chamada, sem tocar o banco.

# (c) 0,02 s — o modelo da tarefa EXISTE no disco  ← a sonda que a Saude NÃO faz
curl -s --max-time 5 http://127.0.0.1:11434/api/tags

# (d) 1,02 s — fila, progresso, travamento (UM roundtrip, read-only)
sqlite3 "file:/opt/wiki/data/ai/fila.sqlite?mode=ro" <<'SQL'
.timeout 5000
SELECT 'contagem', tipo, modelo, estado, COUNT(*) FROM tarefa GROUP BY 2,3,4;
SELECT 'ultima_concluida', MAX(concluida_em) FROM tarefa WHERE estado='concluida';
SELECT 'concluidas_10min', COUNT(*) FROM tarefa
  WHERE estado='concluida' AND concluida_em >= strftime('%Y-%m-%dT%H:%M:%SZ','now','-10 minutes');
SELECT 'concluidas_60min', COUNT(*) FROM tarefa
  WHERE estado='concluida' AND concluida_em >= strftime('%Y-%m-%dT%H:%M:%SZ','now','-60 minutes');
-- TRAVADO: lote estourado. prazoDoLote = max-lote(3) x PrazoPorTarefaPadrao(300s) = 900 s
-- (worker.go:205 e worker.go:207-216). Linha `executando` mais velha que isso
-- só existe se o worker morreu sem Recuperar rodar, ou se foi congelado.
SELECT 'travada', id, iniciada_em, worker, tipo, modelo FROM tarefa
  WHERE estado='executando' AND iniciada_em < strftime('%Y-%m-%dT%H:%M:%SZ','now','-900 seconds');
SELECT 'executando', id, iniciada_em, tentativas FROM tarefa WHERE estado='executando';
SQL
```

Tradução das saídas em veredito, **hoje, sem código novo**:

| observação | veredito |
|---|---|
| `SubState=running` + `concluidas_10min > 0` | vivo e trabalhando |
| `running` + `concluidas_60min = 0` + `pendente > 0` + journal diz `pausa:` | vivo e **pausado** (carga, lock, portal, Ollama) |
| `running` + `concluidas_60min = 0` + `pendente = 0` | vivo e **ocioso** — fila vazia, não defeito |
| linha em `travada` + processo em `/proc/$PID/status` `State: T` | **congelado** (SIGSTOP) |
| linha em `travada` + processo ausente ou `NRestarts` subindo | **morto/laço** |
| `/api/ps` vazio + `concluidas_10min = 0` | Ollama descarregou (keep_alive) **ou** caiu — desempate em (c) e no journal |

O `.timeout 5000` espelha o `busy_timeout(5000)` do daemon (`fila.go:269`): o
leitor espera em vez de falhar quando o worker está no meio de `Reivindicar`.

### 1.3 Uma linha só, para o terminal

```bash
cd /opt/wiki && systemctl show wikijuridica-cerebro.service -p SubState -p NRestarts --value | tr '\n' ' ' \
 && curl -s --max-time 5 localhost:11434/api/ps | python3 -c 'import json,sys;d=json.load(sys.stdin);print(" ".join("%s/%.2fGiB"%(m["name"],m["size"]/2**30) for m in d["models"]) or "sem-residente")' \
 && sqlite3 "file:data/ai/fila.sqlite?mode=ro" ".timeout 5000" \
    "SELECT (SELECT COUNT(*) FROM tarefa WHERE estado='pendente')||' pend '||(SELECT COUNT(*) FROM tarefa WHERE estado='erro')||' erro ult='||(SELECT MAX(concluida_em) FROM tarefa WHERE estado='concluida');"
```

---

## 2. O batimento (P9) — formato, gate, limiares, veredito

### 2.1 O molde já existe no repo, e ele falha FECHADO

`internal/checks/djen_coleta.go:30-69` + `internal/djen/heartbeat.go` são o
precedente exato: JSONL append, leitura que **erra em linha corrompida em vez de
pular** (`heartbeat.go:89-91`), janela de **duas cadências**
(`heartbeat.go:112-124`, com o motivo escrito: vermelho permanente é vermelho que
o operador ignora), e ausência de arquivo = "atrasada", nunca "saudável"
(`djen_coleta.go:33-37`). O batimento do cérebro copia essa forma. Registrar o
gate em `internal/checks/checks.go` custa duas linhas: o nome em `Names`
(`checks.go:298`) e um `case` no switch (padrão de `checks.go:1956`).

### 2.2 Onde o arquivo mora — e por que não em `/tmp`

`data/ops/` é o único lugar: está em
`ReadWritePaths=/opt/wiki/data/ai /opt/wiki/data/ops`
(`wikijuridica-cerebro.service:75`) e **não** está sob `PrivateTmp`. Escrever o
batimento em `/tmp` repetiria exatamente o defeito do flock provado na §3(f).

- **estado, sobrescrito a cada batida:** `data/ops/cerebro_batimento.json`
  (arquivo temporário no mesmo diretório + `rename(2)`, para o leitor nunca ver
  meio JSON).
- **série, append:** `data/ops/cerebro_batimento.jsonl`, **uma linha por
  transição de estado e no máximo uma por minuto** — não uma por passo. Com o
  `--ocioso 30s` atual, uma linha por passo daria ~2.900 linhas/dia; a série que
  já existe (`ia_local_daily.jsonl`) chegou a 2,8 MB / 6.589 linhas. O `.jsonl`
  entra no `.gitignore` junto com `data/ai/fila.sqlite`; o `.json` de estado é
  efêmero e também fica fora do git. Quem já grava série permanente por lote é o
  `Medidor` (`medicao.go:109`), e o batimento não o duplica.

### 2.3 Formato

```jsonc
{
  "schema_version": "cerebro_batimento_v1",
  "ts": "2026-09-16T00:08:36Z",              // UTC, RFC3339, como Medicao.TS
  "proximo_batimento_ate": "2026-09-16T00:25:56Z", // ← declarado PELO WORKER
  "worker": "cerebro-1",
  "pid": 926445,
  "vcs_revision": "3dd00bd2dc9ef6472e17ea54895ecfdb93c5cb43",
  "estado": "trabalhando",                   // trabalhando | ocioso | pausado
  "pausa_motivo": "",                        // texto do ErrPausado quando pausado
  "executando_ids": [41901,41902,41903],
  "executando_desde": "2026-09-16T00:08:36Z",
  "prazo_do_lote_s": 900,                    // prazoDoTarefa x len(lote) REAL, pos-claim
  "pendentes": 34217,
  "elegiveis_agora": 34217,                  // pendente AND disponivel_em <= agora
  "em_erro": 39,
  "ultimo_lote_ts": "2026-09-16T00:08:36Z",
  "ultimo_lote_resultado": "ok",
  "modelo_residente": [{"nome":"qwen3.5:4b","bytes":3227894413}],
  "loadavg1": 8.55
}
```

**Duas escritas por iteração, não uma.** No topo da iteração de `Roda`
(`worker.go:156-175`) o worker ainda não sabe o tamanho do lote — `Reivindicar`
só devolve em `worker.go:71`. Então:

1. **antes do `Passo`:** `estado`, `proximo_batimento_ate` calculado com
   `max-lote` (pior caso), `pendentes`, `elegiveis_agora`, `pausa_motivo`;
2. **depois do claim e antes de `executor(ectx, lote)` (`worker.go:98-99`):**
   `executando_ids`, `executando_desde`, `prazo_do_lote_s` com o `len(lote)`
   **real**.

A linha "travado" da tabela de veredito depende inteiramente da escrita (2).
`elegiveis_agora` existe porque `Reivindicar` filtra por
`disponivel_em <= agora` (`fila.go:379`): sem ele, a linha "ocioso com fila"
dispararia falso justamente depois da prova (a), quando tudo está em backoff.

**`proximo_batimento_ate` é derivado, não escolhido.** O worker o calcula das
**próprias** flags:

```
proximo_batimento_ate = agora
  + 3 sondas HTTP × saude-prazo (20 s)         // saude.go:98 Verifica, rotas / /healthz /buscar/
  + 2 sondas do Ollama × saude-prazo (20 s)    // Versao + Residentes
  + prazoDoLote(max-lote) = 3 × 300 s = 900 s  // worker.go:205, :207-216
  + ocioso (30 s)
  + 20 % de margem
  = 100 + 900 + 30 = 1.030 s → 1.236 s ≈ 20,6 min
```

Por que a folga é grande e **não** pode ser `2 × ocioso`: a série tem dois lotes
de **900.010 ms** (2026-09-10T08:24:40Z e 08:59:32Z — exatamente o prazo do lote)
e um de **202.900 ms** hoje. Um prazo de "2 × ocioso = 60 s" declararia morto um
worker que está trabalhando, em toda ementa longa. O número acompanha as flags:
mudar `--max-lote` ou `--ocioso` muda o prazo **sozinho**, porque o worker o
escreve.

### 2.4 O gate: `cerebro-batimento`

Lê **só o arquivo**. Não conhece flag nenhuma do daemon — o prazo vem de dentro
do JSON. Não chama `systemctl`, não abre a fila, não fala com o Ollama: gate que
depende de três superfícies fica vermelho por indisponibilidade de uma delas.

| condição, na ordem | veredito | mensagem |
|---|---|---|
| arquivo ausente | **FALHA — morto** | "nenhum batimento registrado; o worker nunca escreveu. Fila parada e fila vazia produzem a MESMA contagem." |
| JSON ilegível / linha corrompida | **FALHA** | erro nomeado (nunca pulado — `heartbeat.go:89`) |
| `agora > proximo_batimento_ate` | **FALHA — morto ou congelado** | "último batimento em T, prazo declarado até T+Δ, vencido há N. Confira `SubState` e `/proc/PID/status State`." |
| `estado="pausado"` há mais de **4 × prazo** (≈ 82 min) | **FALHA — pausa crônica** | ecoa `pausa_motivo` |
| `estado="trabalhando"` e `agora − executando_desde > prazo_do_lote_s × 1,5` | **FALHA — travado** | "lote #ids executando há N s, acima de 1,5 × o prazo que o próprio worker declarou" |
| `estado="ocioso"` e `elegiveis_agora = 0` | **OK — fila vazia** (ou tudo em backoff) | é a distinção que o gate existe para fazer; `pendentes > 0` com `elegiveis_agora = 0` sai como nota, não como falha |
| `estado="ocioso"` e `elegiveis_agora > 0` por mais de **2 × prazo** | **FALHA — não reivindica** | há trabalho elegível e o worker não o pega: `Reivindicar` está falhando |
| resto | **OK** | |

Limiares, todos derivados: **1 prazo** para vivo/morto (é o pior caso declarado);
**1,5 prazo** para travado (dá uma folga de escrituração sem esconder um
congelamento); **2 prazos** para ocioso-com-fila (duas oportunidades perdidas de
reivindicar); **4 prazos** para pausa crônica (a pausa por carga medida hoje
durou 1m55s — 82 min é fora de qualquer pausa legítima já observada).

A janela de julgamento do `.jsonl` é de **duas cadências**, pelo mesmo motivo
escrito em `heartbeat.go:99-111`.

### 2.5 Teto de degradação, no mesmo gate

Com `pendentes` e `ultimo_lote_ts` na mão, o gate calcula a vazão da janela e a
compara com a linha medida hoje (43,6 s/tarefa, 24 h). Vazão abaixo de **1/3**
dela com `estado="trabalhando"` e `loadavg1 < CargaMax` é degradação a nomear —
não é "o host está ocupado", porque o próprio batimento carrega o loadavg.

---

## 3. As sete provas negativas — roteiro, sem esperar

Regras que valem nas sete: **nenhuma produz tarefa em estado de `erro`
terminal**; o cronômetro começa no comando; a leitura é sempre `?mode=ro`; e
antes de cada uma grava-se a linha de base (§1.2) para o "depois" ter contra o
que ser comparado.

`sudo -n -l` conferido: `(ALL) NOPASSWD: ALL` — todos os comandos abaixo são
executáveis sem senha. O worker roda como `rafael` (unit:47), então `kill` nele
dispensa `sudo`.

### 3.0 A trava que torna (a), (b) e (d) DESTRUTIVAS contra o worker de produção

`Worker.Passo` devolve `len(lote), nil` depois de falhar um lote inteiro
(`worker.go:100-112`). Em `Roda` (`worker.go:156-175`) isso cai no `default:`,
e `if n > 0 { continue }` (`worker.go:173-175`) **pula o
`time.After(intervaloOcioso)`**. Erro de conexão ou 404 do Ollama volta em
milissegundos; `Reivindicar` + 3 × `Falhar` também. Resultado: **laço apertado**.
E o veredito de saúde está em cache por `--saude-a-cada 60s`
(`worker.go:62-69`), então a pausa só chega no próximo recheck.

Consequência medida por aritmética sobre o código, não por execução:

- **(a) Ollama caído:** até 60 s de laço a ~20–50 ms por lote ⇒ **milhares** de
  tarefas com `tentativas+1` e milhares de linhas `resultado:"erro"` no
  `ia_local_daily.jsonl` (append-only, `medicao.go:109`) antes da pausa.
- **(b) modelo removido:** nada interrompe o laço — `Saude` não confere o modelo.
  As 34.217 pendentes entram em backoff em poucos minutos; rodada 2 em +5 min,
  rodada 3 em +10 min ⇒ **a fila inteira em `estado='erro'` em ~30 min**, mais
  ~100 mil linhas de ledger. A volta é `cerebro reabrir --tipo
  extrair_dispositivos`, que **também** reabre os 39 erros legítimos —
  `Fila.Reabrir` (`fila.go:477-490`) não filtra por id.

**Por isso (a), (b) e (d) rodam SÓ no padrão de unit volátil de (e)**, com o
worker de produção **parado antes** (`sudo -n systemctl stop
wikijuridica-cerebro.service` — parada explícita de `Type=simple` é limpa e não
dispara `OnFailure`), porque o Ollama é compartilhado e o worker vivo sofreria o
mesmo evento. O ensaio precisa de `--root` próprio e completo: `c.resolve()`
exige `content/pages.json` (`main.go:111-113`) e o extrator faz append em
`data/ai/extracoes_dispositivos.jsonl` **relativo ao `--root`**. A unit volátil
leva `-p ProtectSystem=strict -p ReadWritePaths=<ensaio>` para que qualquer
escrita fora do ensaio falhe alto em vez de vazar.

**A correção que estas três provas cobram são DUAS, e uma sozinha não basta:**
(i) classificar erro de **transporte** (connection refused, EOF, DNS) e 5xx do
Ollama como `ErrPausado` em vez de `Falhar`; e (ii) um **disjuntor de lotes
consecutivos** no `Worker` — N falhas de lote em sequência ⇒ `ErrPausado` +
recheck forçado de saúde. Sem (ii), um 404 (que é erro de conteúdo, não de
transporte) continua queimando a fila no mesmo laço.

> **Distinção que decide o veredito das sete:** `Recuperar` (`fila.go:466-472`, e
> `restartsDoServico` que a `Saude` usa está em `saude.go:268`)
> devolve a `pendente` e **grava texto no campo `erro`**
> (`'recuperada apos reinicio do worker'`) sem mudar `estado`. Contar
> `erro <> ''` mede a coisa ao lado. O critério é `estado='erro'`, sempre.
> E `tentativas` é incrementado no claim (`fila.go:409`) e **não** é zerado por
> `Recuperar` — três `kill -9` no mesmo lote consomem as três tentativas
> (`--tentativas 3`) e a quarta falha real vira terminal.

### (a) Derrubar o Ollama — **worker de produção parado, ensaio de pé**

```bash
sudo -n systemctl stop wikijuridica-cerebro.service        # parada explícita: não dispara OnFailure
# ... sobe a unit volátil do ensaio (padrão de (e)), com --fila <cópia> --root <ensaio> ...
# CRASH, não stop: `systemctl stop` NUNCA aciona Restart=; a unit ficaria parada.
sudo -n kill -9 "$(systemctl show ollama.service -p MainPID --value)"
```
- **Observar:** journal do ensaio; `SELECT COUNT(*) FROM tarefa WHERE estado='erro'` na **cópia**, antes/depois; `NRestarts` do `ollama.service`.
- **Correto:** se a queda cair **entre lotes**, `Saude.Verifica` (`saude.go:98`) falha em `Versao` → `ErrPausado` → journal `pausa: … ollama fora do ar` → **zero tarefa tocada**, dentro de `--saude-a-cada 60s`.
- **Incorreto, e é o que se espera hoje:** se cair **no meio de um lote**, o executor recebe erro de conexão → `Fila.Falhar` no lote inteiro (`worker.go:103`) e **laço apertado** por até 60 s (§3.0). A prova mede exatamente quantas tarefas e quantas linhas de ledger isso custa.
- **Tempo:** `ollama.service` tem `Restart=always`, `RestartSec=3s` (medido) e volta sozinho em ~3 s; a primeira chamada seguinte paga o load do modelo (p50 3 ms com residente, pior caso medido 234,2 s numa troca fria).
- **Correção que a prova cobra:** as duas de §3.0, transporte **e** disjuntor.

### (b) Remover o modelo — **mesmo enquadramento de (a)**

```bash
ollama cp qwen3.5:4b qwen3.5:4b.backup   # falam com a API; NUNCA rm sem cópia
ollama rm qwen3.5:4b
```
- **Observar:** `/api/tags` (some), `/api/ps` (descarrega), journal, contagem de `estado='erro'` **na cópia**.
- **Correto:** o cérebro pausa com `modelo qwen3.5:4b ausente no Ollama`, sem tocar tarefa. **Hoje não é o que acontece:** `Saude.Verifica` checa `Versao` e `Residentes` e **nunca confere se o modelo da tarefa existe no disco** — 404 do `/api/generate` é erro de **conteúdo**, atravessa a classificação de transporte e só o disjuntor o para.
- **Tempo, sem as correções:** fila inteira em `estado='erro'` em ~30 min (§3.0). É por isso que a prova roda contra a cópia.
- **Correção:** `Saude` ganha `ModelosExigidos []string`, alimentado pelos modelos com tarefa pendente e conferido contra `/api/tags` — mais o disjuntor.
- **Reverter:** `ollama cp qwen3.5:4b.backup qwen3.5:4b && ollama rm qwen3.5:4b.backup`.

### (c) `kill -9` no worker

É a única das sete que **pode** rodar contra produção: ela exercita o caminho de
recuperação, não o de falha de tarefa.

```bash
kill -9 "$(systemctl show wikijuridica-cerebro.service -p MainPID --value)"   # roda como rafael; sudo dispensável
```
- **Observar:** `NRestarts` (+1), journal `N tarefas recuperadas de worker anterior` (`main.go:174`), `estado='erro'` (sem mudança), `estado='executando'` (volta a 0 e depois a 3).
- **Correto:** `Recuperar` (`fila.go:466-472`) devolve as `executando` a `pendente`; no pior caso um lote é refeito, nunca perdido. Zero terminal.
- **Tempo:** `RestartSec=15s` + boot (`Versao` do Ollama + `CarregaAcervo` de 11 mil páginas + `Abrir` sobre 139 MB). **Não medido**: a linha de boot de 2026-09-14 04:40:57 **já rotacionou do journal** — o registro mais antigo da unit é de 2026-09-15T04:20:08. Medir na hora, capturando `journalctl -u wikijuridica-cerebro.service --since "-90s" | head -3` **imediatamente** depois do kill; a retenção do journal não guarda essa linha para depois.
- **Custo escondido a registrar:** as 3 tarefas do lote voltam com `tentativas` já em 1 — `Recuperar` não zera o contador.

### (d) `kill -STOP` (travado, não morto)

Roda contra o **ensaio**, não contra produção: o `SIGCONT` tardio custa uma
tentativa de cada tarefa do lote (ver o efeito colateral abaixo).

```bash
PID=$(systemctl show cerebro-prova-congelado -p MainPID --value)
kill -STOP "$PID"
```
- **Observar:** `systemctl show -p ActiveState -p SubState` → continua `active (running)`; `/proc/$PID/status` → `State: T (stopped)`; a query `travada` da §1.2; o `.json` do batimento **para de avançar**.
- **Correto (depois de P9):** o gate `cerebro-batimento` reprova em `proximo_batimento_ate` vencido, ≈ 20,6 min. Com `WatchdogSec` na unit, o systemd mata e reinicia em `WatchdogUSec`.
- **Hoje:** `WatchdogUSec=0` — **nada** detecta. A unit fica `active (running)` para sempre. É o pior modo de falha do conjunto, porque todo instrumento diz verde.
- **Retomar:** `sudo -n kill -CONT "$PID"`.
- **Efeito colateral a esperar e a registrar:** os timers do Go usam relógio de parede; no `SIGCONT`, se o prazo do lote já passou, o `ctx` já está expirado e o lote falha **imediatamente** — `tentativas+1` mesmo na recuperação "correta". Suspenda por menos que `prazo_do_lote_s` (900 s) na prova, ou aceite a tentativa gasta e registre-a.

### (e) Corromper a fila — **nunca no banco real**

```bash
cp /opt/wiki/data/ai/fila.sqlite  /opt/wiki/.agents/runtime/prova-fila/fila-corrompida.sqlite
printf 'XXXX' | dd of=/opt/wiki/.agents/runtime/prova-fila/fila-corrompida.sqlite bs=1 seek=0 count=4 conv=notrunc

# a prova roda numa unit VOLÁTIL, com as MESMAS diretivas da unit real, e some depois:
sudo -n systemd-run --unit=cerebro-prova-corrompida --collect \
  -p Restart=always -p RestartSec=15 -p OnFailure=wikijuridica-alerta@%N.service \
  -p User=rafael -p WorkingDirectory=/opt/wiki \
  -p Environment=WIKI_OLLAMA_URL=http://127.0.0.1:11434 \
  /opt/wiki/bin/cerebro servir --root /opt/wiki \
    --fila /opt/wiki/.agents/runtime/prova-fila/fila-corrompida.sqlite --worker prova-1
```
- **Observar:** `journalctl -u cerebro-prova-corrompida`, `systemctl show cerebro-prova-corrompida -p NRestarts -p ActiveState -p Result`, e se `wikijuridica-alerta@cerebro-prova-corrompida.service` **rodou** (`systemctl show … -p ExecMainStartTimestamp`).
- **Correto:** `Abrir` falha em `EsquemaSQL`/`PRAGMA index_list` **antes de qualquer reivindicação** (`fila.go:291-304`) → `main.go:81` `os.Exit(1)`.
- **O que a prova estabelece:** com `Restart=always` + `RestartSec=15` + StartLimit `10s/5`, nenhuma janela de 10 s contém duas partidas ⇒ o burst é **inalcançável** ⇒ a unit nunca entra em `failed` ⇒ **`OnFailure` nunca dispara**. Isso é exatamente o que `tools/check-units-alarme:83-111` já mediu neste systemd 252 (caso (A)), com o precedente de produção dos 87 restarts da rede social.
- **Perigo a barrar por escrito:** um segundo `cerebro servir` com `--root /opt/wiki` e uma fila que **abre** trabalharia o corpus real e faria append em `data/ai/extracoes_dispositivos.jsonl`. A corrupção tem de ser do **cabeçalho**, para o `Abrir` falhar antes de tudo.
- **Encerrar:** `sudo -n systemctl stop cerebro-prova-corrompida` (é volátil, `--collect` a descarta) e `rm` da cópia.
- **Tempo:** veredito em 2 ciclos de restart ≈ 35 s.

### (f) Segurar o flock

```bash
flock -x /tmp/opt-wiki-agent-heavy.lock tail -f /dev/null &   # `sleep` é barrado por hook
```
- **Observar:** journal do cérebro por dois ciclos de saúde (120 s); contagem de lotes na janela.
- **Correto:** `pausa: /tmp/opt-wiki-agent-heavy.lock tomado: compilacao ou commit de Go em curso`.
- **Hoje, medido e provado nesta sessão:** **nada acontece.** O host tem o lock em inode **39454263**; o daemon, sob `PrivateTmp=true` (unit:72), tem **outro arquivo** no seu `/tmp` privado, inode **39739472**, criado às 04:40 de 14/09 (a hora do boot da unit) — namespaces `mnt:[4026531841]` (host) × `mnt:[4026532461]` (daemon). `lockTomado` abre com `O_CREATE|O_RDWR` (`carga_linux.go:18`) e por isso **fabrica** o arquivo que deveria observar. A guarda nunca guardou nada.
- **Ordem obrigatória da correção** (inverter vira laço de boot com `226/NAMESPACE`):
  1. `carga_linux.go:18` passa a `os.OpenFile(caminho, os.O_RDONLY, 0)` — `flock(LOCK_EX)` sobre fd `O_RDONLY` funciona no Linux — **e, no mesmo passo, `errors.Is(err, fs.ErrNotExist) ⇒ return false, nil`, com teste.** Sem essa cláusula o passo 1 **trava o worker para sempre**: `carga_linux.go:19-21` devolve `(false, err)` e `Verifica` embrulha qualquer erro como pausa (`saude.go`, ramo `lock pesado %s: %w`), então o `/tmp` privado recém-criado, que não tem o arquivo, daria `ENOENT ⇒ ErrPausado` eterno. E isso reincide a cada boot: com o prefixo `-` do passo 3, o bind é **pulado** quando o arquivo do host não existe no momento da partida da unit;
  2. snippet `tmpfiles.d` cria o lock no boot — `/usr/lib/tmpfiles.d/tmp.conf:11` tem `D /tmp 1777 root root -`, que **esvazia** `/tmp` no boot (conferido no disco);
  3. só então `BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock` na unit (o `-` torna a ausência tolerável) — ele **convive** com `PrivateTmp=true`.
- **Efeito colateral a anunciar:** segurar o lock pesado **bloqueia build e commit de Go de toda outra sessão** e a bancada diária. Time-box de ≤ 120 s e aviso por `tools/generate-coord-message` antes.
- **Encerrar:** `kill %1`.

### (g) Forçar o teto de residentes a 1 byte

- **Não é executável hoje.** `guardaDeSaude` (`main.go:121-126`) só repassa
  `LockPesado` e `CargaMax`; `Saude.TetoBytesResidentes` (`saude.go:67`, padrão
  `TetoBytesResidentesPadrao = 9<<30` em `saude.go:92`) não tem flag e só é
  alcançável por `saude_test.go`. `servir` não expõe `--teto-bytes-residentes`.
- **Precondição:** flag `--teto-bytes-residentes` (0 = `TetoBytesResidentesPadrao`), ligada em `guardaDeSaude`, no binário, por `tools/deploy-cerebro`.
- **Aí sim:**
  ```bash
  sudo -n systemd-run --unit=cerebro-prova-teto --collect -p User=rafael \
    -p WorkingDirectory=/opt/wiki -p Environment=WIKI_OLLAMA_URL=http://127.0.0.1:11434 \
    /opt/wiki/bin/cerebro servir --root /opt/wiki --fila <cópia> --teto-bytes-residentes 1
  ```
- **Correto:** com `qwen3.5:4b` residente (3.227.894.413 B medidos), a soma passa de 1 B → `ErrPausado` com a mensagem de `saude.go` nomeando os residentes → **zero tarefa tocada**, e a unit segue `active`.
- **Tempo:** primeiro ciclo de saúde, ≤ 60 s.
- **O que a prova impede:** o par do incidente de 2026-09-08 12:04:53 (14b + 9b = 16 GB) continuar passando por engano quando alguém mudar `OLLAMA_MAX_LOADED_MODELS`.

### Ordem de execução e regra de parada

`(f)` → `(g)` → `(a)` → `(b)` → `(c)` → `(d)` → `(e)`: das que **não** tocam
tarefa para as que tocam; `(e)` fica por último porque roda em unit própria.
Entre cada uma, reler a §1.2 e conferir que `COUNT(*) WHERE estado='erro'` não
subiu. **Se subiu, a prova achou o defeito** — que é o que ela existe para
achar; a correção entra antes da prova seguinte.

Depois de (c) e (d), `tools/deploy-cerebro` já garante o resto: build para
`.novo`, conferência de `vcs.revision` contra HEAD, `mv -f` (rename atômico) e
restart — com `Fila.Recuperar` no boot. **Ordem que não se inverte:** binário
primeiro, unit depois (precedente `socket-systemd-binario-antes`); pôr
`Type=notify`/`WatchdogSec` numa unit cujo binário ainda não manda `READY=1`
produz timeout de partida e laço de restart.

---

## 4. Ganho de prompt ou de modelo, sem refazer o corpus

### 4.1 O bloqueio é real, e o próprio código o admite

`ImpressaoDoTexto` (`extracao.go:829-834`) é `sha256(TrimSpace(texto))` — função
**só do texto**. A identidade da fila é `UNIQUE(tipo, chave, impressao, modelo)`
(`fila.go:88`). Logo, **trocar o prompt com o mesmo modelo cai em
`INSERT OR IGNORE`** (`fila.go:330`) e nunca executa. O comentário de
`extracao.go:134-136` diz isso com todas as letras:

> "as extracoes ja concluidas NUNCA voltam a fila — `UltimaExtracaoPorChaveEModelo`
> chaveia por `chave+modelo`, nao por versao de prompt"

O cache de enfileiramento tem a mesma cegueira: `ChaveExtracaoCache{Chave,Modelo}`
(`extracao.go:870-873`) comparado contra `TextoSHA256Cortado` (`main.go:759-763`).
`Extracao.VersaoDoPrompt` **existe** (`extracao.go:91-94`, valor
`"sem_sumula_v2"` em `:210`) mas nenhuma chave a usa.

### 4.2 A correção é rodar FORA da fila — e a ferramenta já existe

`cmd/medir-prompt-sumula-pareado` (473 linhas) é exatamente o lote pareado
pedido, e não precisa de nada da fila além de leitura:

- abre a fila `?mode=ro` (`:348`), lê `chave, payload` das **pendentes**;
- amostra por **stride determinístico** sobre o total (`:361`), com guarda de
  volume que aborta se a população for implausível (`:124-126` — "sorteio que
  devolve pouco mede o próprio SELECT");
- **intercala** controle e variante item a item (`:148-153`), com o motivo
  escrito: o host tem carga variável e uma passada inteira num período carregado
  viraria "a versão B é mais lenta" — hoje isso não é hipótese, é o que a §0
  mediu;
- o **controle é a constante viva** `cerebro.SistemaDaExtracao` (`:149`), nunca
  uma cópia, para as duas não divergirem na primeira edição;
- reproduz a chamada de produção byte a byte (`:162-171`): mesmo `EsquemaJSON`,
  `Think=false`, `Temperatura=0`, `PenalidadeDePresenca=0`, `NumPredict=512`;
- classifica o resultado com a **mesma régua da produção**
  (`cerebro.URNDaCitacaoPublica`, `:194`) em vez de substring própria;
- grava em `data/ops/`, **não** em `data/ai/extracoes_dispositivos.jsonl`, não
  toca a fila, não muda estado de tarefa: rodar duas vezes mede duas vezes;
- tem `--so-com-sumula`, que **condiciona** a amostra pelo parser determinístico
  sobre o texto de **entrada** (`:427-441`), nunca pelo resultado — e obriga o
  relatório a dizer que o veredito passa a valer condicionado (`:330-346`).

**A correção é generalizá-lo**, não trocar a identidade da fila:
`cmd/medir-variante-pareado --controle <id> --variante <id> --modelo-a --modelo-b`,
com as redações num registro versionado e o relatório carimbando
`versao_controle`/`versao_variante` (que o schema `medicao_prompt_sumula_pareado/v1`
já carrega, `:216-240`). Troca de **modelo** já é comparável pela fila hoje
(`modelo` está no `UNIQUE` desde 2026-09-09, `fila.go:63-67`), mas pagaria a
extração inteira de novo; o harness pareado responde com n=30.

**Régua antes do número.** `.agents/runtime/regua/20260911-desobediencia-do-modelo-a-sumula.md`
é o precedente: resultado → veredito → ação, escritos **antes** de qualquer
chamada nova. Variante nova nasce com régua nova.

**Veredito em tokens, não em parede.** Com `OLLAMA_NUM_PARALLEL=1`
(drop-in do Ollama:22), cada chamada do harness entra na fila do Ollama **atrás**
do lote do worker — que mede até 900 s. `parede_ms` do harness mede a fila,
não o modelo. As grandezas são `prompt_tokens`, `eval_tokens`, contagem de
súmulas/URNs e `prompt_tok_s_liquido` (`medicao.go:122-128`, que já tira o
`load_duration`).

### 4.3 Se alguém quiser mesmo pôr o prompt na identidade — o raio de explosão

Precondição a medir **antes**, não depois:

```sql
SELECT COUNT(*) FROM tarefa
 WHERE tipo='extrair_dispositivos' AND estado IN ('pendente','executando');
-- medido 2026-09-16T00:09Z: 34.220
```

Esse é o número de **linhas duplicadas** que o próximo `enfileirar-extracoes`
inseriria, porque `impressao` mudaria para todas. A `chave` é a mesma, o
`payload` é o mesmo, e o worker faria 34.220 chamadas a 43,6 s = **17,3 dias** de
Ollama para reprocessar o que já está feito. Se a mudança for adotada mesmo
assim, ela vem **junto** com uma migração que carimbe a impressão antiga nas
linhas existentes — nunca sozinha.

---

## 5. Custo real de uma passada — medido na série que já existe

Fonte: `data/ops/ia_local_daily.jsonl`, 6.589 linhas, uma por lote, campos
`prompt_tokens`, `eval_tokens`, `prompt_tok_s`, `prompt_tok_s_liquido`,
`eval_tok_s`, `parede_ms`, `ollama_total_ms`, `load_ms`,
`custo_segundos_maquina` (`medicao.go:23-52`).

Só entram lotes com `resultado='ok'` **e** `custo_tokens > 0` — o critério que
`custoMedidoPorTarefa` (`main.go:486-524`) já usa, e pelo motivo dele: desde a
triagem, um lote pode concluir com parede zero, e incluí-lo faria a média dizer
que a extração ficou barata quando o que aconteceu foi **não ter sido feita**.
Na janela de 24 h são **58 de 679 lotes** (`modelo=""` = triagem pura).

```bash
cd /opt/wiki && python3 - <<'PY'
import json, datetime, statistics
L=[json.loads(l) for l in open('data/ops/ia_local_daily.jsonl') if l.strip()]
def t(m): return datetime.datetime.fromisoformat(m['ts'].replace('Z','+00:00'))
def janela(h, tipo='extrair_dispositivos'):
    fim=t(L[-1]); ini=fim-datetime.timedelta(hours=h)
    jan=[m for m in L if t(m)>=ini]
    span=(fim-(t(jan[0])-datetime.timedelta(milliseconds=jan[0]['parede_ms']))).total_seconds()
    ocupado=sum(m['custo_segundos_maquina'] for m in jan)
    real=[m for m in jan if m['tipo']==tipo and m['resultado']=='ok' and m['custo_tokens']>0]
    tar=sum(m['lote'] for m in real); seg=sum(m['custo_segundos_maquina'] for m in real)
    print(f"{h}h lotes={len(jan)} triagem_pura={len([m for m in jan if m['modelo']==''])} "
          f"ocupacao={100*ocupado/span:.1f}% tarefas={tar} s/tarefa={seg/tar:.1f} "
          f"prefill_p50={statistics.median([m['prompt_tok_s'] for m in real]):.2f} "
          f"decode_p50={statistics.median([m['eval_tok_s'] for m in real if m['eval_tok_s']>0]):.2f} "
          f"load_soma={sum(m['load_ms'] for m in real)/1000:.0f}s")
for h in (1,6,24,168): janela(h)
PY
```

**Medido (2026-09-16T00:1xZ):**

| janela | lotes | ocupação do Ollama | s/tarefa | prefill p50 | decode p50 |
|---|---|---|---|---|---|
| 1 h | 59 | 98,2 % | 25,1 | — | — |
| 6 h | 251 | 99,3 % | 33,6 | — | — |
| **24 h** | 675 | **93,3 %** | **43,6** | 14,5 | 5,6 |
| 168 h | 6.419 | 90,7 % | 29,1 | 13,6 | 5,4 |
| série inteira (8.145 tarefas) | 2.715 | — | 56,3 | 13,6 | 5,4 |

**`embed_pagina`** (3.719 lotes, 11.263 tarefas): **9,2 s/tarefa**, prefill p50
**63,25 tok/s** — 4,6 × o da extração, porque embedding é só prefill.

**Drenagem, com o número de hoje:** 34.217 pendentes × 43,6 s = **1.491.861 s =
414,4 h = 17,3 dias** à taxa medida **sob a carga medida** (loadavg 15,84 no pico
da varredura; decode em 3,0–3,9 tok/s contra os 5,4 da série). Com a máquina
livre a taxa da janela de 168 h (29,1 s) dá **11,5 dias**. **Os dois números são
tetos superiores diferentes, não uma previsão** — declare sempre a carga junto.
E os 43,6 s são por tarefa **com chamada real**: **8,5 % dos lotes da janela
(58 de 679) são triagem pura** e custam ≈ 0. A drenagem real é menor na mesma
proporção da fração de triagem das 34.217 pendentes, que não foi medida aqui
(`fila.TriagemDosPendentes`, `fila.go:549-568`, é quem a responde — e é a mesma
régua do executor, não uma regex copiada).

**Custo de troca de modelo, medido:** `load_ms` somado é 1.209,3 s em
`extrair_dispositivos` e 531,7 s em `embed_pagina`; o **pior caso é 234.198 ms**
(234,2 s) — um único evento. p50 = 3 ms (o modelo fica residente por
`keep_alive=10m`). É o número que justifica `OLLAMA_MAX_LOADED_MODELS=2`.

**Taxa de falha parcial, medida:** 34 de 679 lotes da janela de 24 h trazem
`nota: "N de 3 tarefas do lote falharam"` — 35 tarefas devolvidas a `pendente`
com backoff, **não** terminais. Os 39 `estado='erro'` da fila são o acumulado de
toda a história. Qualquer painel tem de separar as duas grandezas.

**Prazo do lote, medido:** dois lotes de `900.010 ms` = `3 × PrazoPorTarefaPadrao`
(`worker.go:205`, `:207-216`). O prazo **existe e morde**; ele é o número que
`proximo_batimento_ate` tem de cobrir (§2.3).

**Isto substitui "esperar para ver":** a série já tem 6.589 lotes e 167,6 h de
parede. Nenhuma pergunta de custo do cérebro precisa de janela nova.

---

## 6. Lacunas — o que falta EXISTIR

Em ordem de custo de não ter:

1. **Nada detecta worker congelado.** `WatchdogUSec=0` + `Restart=always` +
   StartLimit inalcançável = `active (running)` para sempre. Falta o batimento
   (§2) e, depois dele, `Type=notify` + `WatchdogSec` — **nessa ordem**, binário
   antes da unit.
2. **`Saude` não confere se o modelo da tarefa existe** (`/api/tags`): 404 do
   Ollama vira falha da tarefa, não pausa.
3. **Erro de transporte do Ollama é cobrado da tarefa** em vez de pausar
   (`worker.go:100-112`), **e não há disjuntor**: `Roda` não dorme depois de um
   lote falho (`worker.go:173-175`, `if n > 0 { continue }`), então uma falha
   sistêmica queima a fila em laço apertado durante a janela de cache da saúde
   (60 s). Faltam as duas peças: classificação de transporte **e** disjuntor de
   lotes consecutivos.
4. **A guarda do flock é muda** — provada muda nesta sessão por inode e
   namespace. Correção em três passos de ordem obrigatória (§3f).
5. **`--teto-bytes-residentes` não existe**: a guarda de memória não tem prova
   negativa possível hoje.
6. **`cerebro status` escreve** — falta um subcomando `status --somente-leitura`
   (ou `--fila-ro`) que abra com `?mode=ro`.
7. **`internal/ollama.Residente` é cego para `size_vram` e `context_length`**
   (`cliente.go:275-281`), campos que o `/api/ps` **entrega hoje** (medido). É a
   pré-condição do P12.
8. **O harness pareado é de uma variante só** — falta a generalização
   `--controle/--variante` (§4.2).
9. **Não há timer nem gate de cérebro** entre os 55 `wikijuridica-*` timers
   instalados.
10. **`.agents/runtime/prova-fila/` não existe** — e o roteiro precisa mais do
    que ele: um `--root` de **ensaio completo** (com `content/pages.json`, que
    `main.go:111-113` exige, e `data/ai/` próprio, que é onde o extrator faz
    append) para (a), (b), (d) e (e) rodarem sem tocar produção.
11. **`cerebro reabrir` não filtra por id** (`fila.go:477-490`): depois de uma
    falha sistêmica, reabrir o tipo reabre junto os 39 erros legítimos. Falta
    `reabrir --id` / `--desde`.
12. **`elegiveis_agora` não é observável por nenhum instrumento** hoje —
    `Contagens` (`fila.go:517`) agrupa por estado e não olha `disponivel_em`,
    então "34.217 pendentes" e "34.217 elegíveis" são a mesma linha mesmo quando
    tudo está em backoff.
13. **A retenção do journal não cobre o uptime do daemon:** o registro mais
    antigo de `wikijuridica-cerebro.service` é de 2026-09-15T04:20:08, e a unit
    subiu em 2026-09-14 04:40:57 — a linha de boot com
    `N tarefas recuperadas` (`main.go:174`) **já se perdeu**. Quem quer o número
    de recuperação captura no ato; quem quer a série precisa dele no batimento.

## 7. Vermelhos pré-existentes (baseline, não desta frente)

- `check-binario-vs-fonte`: **FAIL**, exit 1 — `server` e `social` com o commit
  `a666aca4` fora do binário. `cerebro` está **verde**: `bin/cerebro` declara
  `3dd00bd2` e nenhum commit tocou o fecho de `./cmd/cerebro` desde então.
- `vcs.modified=true` em todos os binários: é dado (`data/ops/` reescrito pelos
  timers), não código. O gate já trata isso por desenho e não reprova por ele.

---

## 8. O que o advisor mudou

Duas chamadas: uma antes de escrever, uma com o arquivo já no disco.

**Antes de escrever, ele acrescentou:**
1. `/api/tags` como comando próprio — é o discriminador da prova (b), e a
   `Saude` não o consulta.
2. A armadilha do `PATH`: o `sqlite3` desta máquina está no SDK do Android;
   unit ou gate com `PATH=/usr/bin:/bin` não o acha. Gate usa `modernc`.
3. A query `travada` (`executando` com `iniciada_em` mais velho que 900 s)
   cruzada com `/proc/$PID/status` — responde "travado × morto" **hoje**, sem
   deploy, e cobre a lacuna até o batimento existir.
4. A aritmética do `proximo_batimento_ate` derivada das flags, com a prova de
   que "2 × ocioso" declararia morto um worker trabalhando (os dois lotes de
   900.010 ms na série).
5. Que a prova (g) **não tem knob**: `guardaDeSaude` não repassa
   `TetoBytesResidentes`. Virou lacuna, não roteiro.
6. Que o caminho certo do item 4 é o harness **fora da fila** que já existe,
   não mexer na identidade — com o raio de explosão (34.220 linhas duplicadas)
   como pré-condição escrita, caso alguém insista.
7. Confirmar que a unit principal é **symlink** para `ops/systemd/` (custódia),
   não cópia.

**Com o arquivo no disco, ele derrubou três coisas que eu havia escrito:**
1. **(a) e (b) eram destrutivas contra produção, e eu subestimei em ordens de
   grandeza.** `Roda` não dorme depois de lote falho (`worker.go:173-175`), e o
   veredito de saúde fica em cache por 60 s: (a) queima milhares de tarefas, (b)
   põe **a fila inteira** em `erro` em ~30 min. As três provas passaram a rodar
   só contra unit volátil com `--root` de ensaio, com o worker de produção
   parado — e a correção virou **duas** (classificação de transporte **mais**
   disjuntor de lotes consecutivos), porque 404 é erro de conteúdo e a primeira
   sozinha não o segura.
2. **`systemctl stop ollama.service` não "volta sozinho em 3 s"** — `Restart=`
   nunca se aplica a parada explícita. A simulação de queda é `kill -9` no
   `MainPID`.
3. **O passo 1 da correção do flock, como eu escrevi, travaria o worker para
   sempre.** `carga_linux.go:19-21` devolve `(false, err)` e `Verifica` embrulha
   erro como pausa; trocar para `O_RDONLY` sem tratar `ENOENT` dá pausa eterna
   no `/tmp` privado — e reincide a cada boot por causa do prefixo `-` do
   `BindReadOnlyPaths`. A cláusula `errors.Is(err, fs.ErrNotExist) ⇒ false, nil`
   entrou no mesmo passo, com teste.

**E acrescentou:** a segunda escrita do batimento (pós-claim, sem a qual a linha
"travado" não tem dado), o campo `elegiveis_agora` (sem o qual "ocioso com fila"
dispara falso depois de (a)), a checagem de `sudo -n -l` (é `NOPASSWD: ALL`,
então tudo é executável, e `kill` no worker dispensa `sudo` porque ele roda como
`rafael`), o time-box de 120 s em (f) com aviso pelo bus de coordenação, e a
ressalva de que os 43,6 s/tarefa ignoram a fração de triagem.

**O que eu medi e ele não contestou:** ocupação de 93,3 %/90,7 % (contra os
"~86 %" do enunciado — o número do enunciado não foi adotado), os inodes e
namespaces do flock, e o veredito verde de `check-binario-vs-fonte` para
`cerebro`.

**Uma coisa que eu tentei medir e não consegui:** o tempo de boot do daemon. A
linha de 2026-09-14 04:40:57 já rotacionou do journal. Está escrita como "não
medido", com o comando para medir no ato.
