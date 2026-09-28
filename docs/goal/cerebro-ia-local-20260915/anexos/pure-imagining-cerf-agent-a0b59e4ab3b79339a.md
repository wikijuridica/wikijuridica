# RUNBOOK OPERACIONAL — P9 / P10 / P12
## Cérebro independente · CI sobre o produto do cérebro · migração para a RTX 5060 Ti

Gerado em 2026-09-15/16, PLAN MODE (somente leitura, nada mutado).
**[M]** = medido nesta sessão contra disco/processo vivo · **[D]** = derivado de número medido · **[X]** = a medir na execução.

---

## 0. MEDIÇÕES DESTA SESSÃO (base de todo número esperado)

| fato | valor | fonte |
|---|---|---|
| unit do cérebro | active/running, MainPID 926445, NRestarts=1, Result=success, ExecMainStatus=0, de pé desde 2026-09-14 04:40:57 -03 | `systemctl show` [M] |
| `WatchdogUSec` | **0** — worker congelado fica `active (running)` para sempre | [M] |
| RestartUSec / StartLimit | 15 s · `StartLimitIntervalUSec=10s` · `StartLimitBurst=5`, **nenhum declarado na unit** (default do manager, invisível ao grep). Com RestartSec=15 nenhuma janela de 10 s tem duas partidas ⇒ burst inalcançável ⇒ `failed` nunca ⇒ `OnFailure` é decoração | [M] |
| flock mudo | host `inode=39454263 rafael 644`; daemon via `nsenter -m` `inode=39739472 rafael 644` | [M] |
| /tmp | `/usr/lib/tmpfiles.d/tmp.conf` → `D /tmp 1777 root root -` ⇒ esvazia no boot | [M] |
| custódia tmpfiles | `/etc/tmpfiles.d/cpu-energia.conf` é **CÓPIA** de `ops/host-state/etc/`, idêntica hoje (`diff` limpo) — precedente de deriva invisível | [M] |
| unit | `/etc/systemd/system/wikijuridica-cerebro.service` → symlink p/ `/opt/wiki/ops/systemd/` | [M] |
| `/api/ps` | `qwen3.5:4b`, size=3.227.894.413 (3,01 GiB), **`size_vram=0`**, **`context_length=8192`**, digest `2a654d98e6fba55d…` | [M] |
| `ollama.Residente` | decodifica só `name/model/size/expires_at` — **cego** para `size_vram`/`context_length` que o endpoint já entrega (cliente.go:275-281) | [M] |
| `/api/tags` | 9 modelos, **cada um com `digest`** = identidade portável, sem sudo | [M] |
| ollama | 0.33.3, `/usr/local/bin/ollama` | [M] |
| executor da extração | **uma chamada ao Ollama POR TAREFA** dentro do lote (extracao.go:341-343) | [M] |
| prazoDoLote | `PrazoPorTarefaPadrao=300s` × `--max-lote 3` = **900 s**; dois lotes reais de 900.010 ms no ledger | [M] |
| laço apertado | worker.go:173-175 `if n > 0 { continue }` não dorme depois de lote FALHO; saúde em cache 60 s (worker.go:62-69) | [M] |
| morte no boot | main.go:157-159 `cliente.Versao` ⇒ `return err` ⇒ main.go:80-81 `os.Exit(1)` | [M] |
| máscaras de exit | **22** diretivas não comentadas: `=0 1`×12, `=1`×7, `=0`×2, `=75`×1 | [M] |
| máscara mordendo AGORA | **9 de 22** units com `ExecMainStatus=1` **e** `Result=success` | [M] |
| edge-frescor | `ExecMainStatus=2`/`Result=exit-code` — a máscara `=0 1` não cobre o 2, o OnFailure disparou | [M] |
| GPU | Debian **12.15 bookworm**; repo `developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64` **já configurado**; `nvidia-kernel-open-dkms` candidato **615.71.09-2**; instalado o **proprietário** `nvidia-kernel-dkms 610.57.04-1`; `dkms status` vazio; `nvidia-smi` **exit 9**; `/proc/driver/nvidia` ausente | [M] |
| runners CUDA | `cuda_v12` e `cuda_v13` presentes; `grep -c sm_120` = **8** em v12 e **0** em v13 (método diferente do "143 cubins" do diagnóstico: corrobora, não reproduz) | [M] |
| drop-in Ollama | MemoryMax=12G, MAX_LOADED_MODELS=2, NUM_PARALLEL=1, KEEP_ALIVE=15m, CONTEXT_LENGTH=8192, FLASH_ATTENTION=1, KV_CACHE_TYPE=q8_0, LLM_LIBRARY=cpu, OOMScoreAdjust=800 | [M] |
| comentário obsoleto | cabeçalho da unit do cérebro ainda diz `MemoryMax=15G` e `MAX_LOADED_MODELS=1` | [M] |
| sdactivation | `NotificaPronto()` público + `notifica(amb,msg)` privado (:204). `cmd/server/main.go:175-204` já tem uma **segunda** implementação — não criar terceira | [M] |
| nome de gate livre | zero checks `cerebro-*`/`ollama-*` em `internal/checks/checks.go` | [M] |
| sudo | `(ALL) NOPASSWD: ALL` ⇒ `systemctl reset-failed` é possível | [M] |
| lock de commit | `grep -rln 'opt-wiki-commit.lock' tools/ docs/ .githooks/ internal/` → **VAZIO**: o lock separado que a memória descreve **não existe no repo** | [M] |
| exit 3 | já tomado com o sentido "catálogo remoto indisponível" em `check-api-catalog-usage:487-506`; **4 é livre** nas 3 ferramentas do piloto (0,0,0) | [M] |
| grafo do validador | `internal/cerebro`, `internal/ollama`, `internal/checks` estão **FORA** ⇒ sem reatestação | diagnóstico |

**Armadilha de medição que eu pisei e que vira regra:** `nvidia-smi \| head; echo $?` imprimiu **0** com o comando falhando; o exit real era **9**. Em pipeline, `${PIPESTATUS[0]}`.

---

## 1. RECONCILIAÇÃO — P12 bloqueio #3 está SUPERADO

O plano diz: *"driver ≥ 570.26 com módulos open (Debian trixie tem 550.163, nenhum repo serve)"*. A segunda metade é **falsa neste host [M]**: `/etc/debian_version`=12.15 (bookworm, não trixie); o repo CUDA da NVIDIA para debian12 **já está** em `sources.list.d` com chave em `/usr/share/keyrings/cuda-archive-keyring.gpg`; `nvidia-kernel-open-dkms` candidato **615.71.09-2**. Não há credencial nova nem cadastro: é repositório apt, mesma classe do `deb.debian.org`.
O pacote instalado é **errado por classe, não por versão**: Blackwell (GB206/sm_120) exige os **módulos open**; `nvidia-kernel-dkms` (proprietário) não serve a 5060 Ti em versão nenhuma.
**NÃO MEDIDO:** por que `dkms status` está vazio neste laptop (a GPU atual é MX110/Maxwell, sem suporte no 610.x — pode ser isso, pode ser header ausente). Não medi, não afirmo. Irrelevante para o alvo. A verificação na máquina nova **não é fé nesta medição**: o passo E2 replica o apt e **mede lá**.

## 2. DEPENDÊNCIA DURA QUE O PLANO NÃO DECLARA — P9 antes de P12

Virar `LLM_LIBRARY=cpu → cuda_v12` com driver/runner ruim produz a falha que a varredura provou: worker.go:173-175 sem sono + saúde em cache 60 s ⇒ **34.217 pendentes viram `erro` em ~30 min [D]**. **Portão:** nenhum passo de E3 em diante roda antes de **B2** e **B3** estarem no binário vivo e a **prova C-a** verde.

## 3. ORDEM OBRIGATÓRIA DE P9 (inverter = laço de boot)

```
B1 boot não morre sem Ollama ──┐ (senão B8 queima o burst)
B2 transporte = pausa          │
B3 disjuntor de lotes falhos ──┘ (portão de P12)
B4 Saude.ModelosExigidos (/api/tags)
B5 flock p1: O_RDONLY SEM O_CREATE + ENOENT⇒(false,nil)
B6 flock p2: tmpfiles.d cria o lock        ← fonte primária: src/core/namespace.c, 252.39-1~deb12u2
B7 flock p3: BindReadOnlyPaths=-/tmp/... mantendo PrivateTmp=true
B8 StartLimitIntervalSec em [Unit] + reset-failed no vigia
B9 NotificaWatchdog + Type=notify + WatchdogSec + TimeoutStartSec
```
B6↔B7 invertidos ⇒ `226/NAMESPACE` em laço de boot. B5 depois de B7 ⇒ `ENOENT` vira `ErrPausado` eterno (carga_linux.go:19-21 devolve `(false,err)` e `Verifica` embrulha como pausa).

## 4. INSTRUMENTOS A CRIAR

| # | instrumento | mede | exit | grava |
|---|---|---|---|---|
| A1 | `ollama.Residente` + `SizeVRAMBytes`/`ContextLength` | spill CPU↔GPU e ctx efetivo | lib | — |
| A2 | `cerebro status --somente-leitura` (`?mode=ro`) | contagens sem DDL no banco vivo | 0 | — |
| A3 | `Fila.Elegiveis` (`pendente AND disponivel_em<=now`) | separa pendente de elegível | lib | — |
| A4 | batimento do worker | estado vivo do daemon | — | `data/ops/cerebro_batimento.json` (tmp+rename) e `.jsonl` |
| A5 | gate `cerebro-batimento` | morto/congelado/travado/pausa crônica/não-reivindica | 0/1 | — |
| A6 | `tools/check-mascara-de-exit` | máscara que esconde exit≠0 **sem** canal próprio | 0/1/2 | `data/ops/mascara_de_exit.jsonl` só com `--gravar` |
| A7 | `--nao-gravar` em `check-portal-health` | diagnosticar sem zerar `reparo_ultimo` | herda | nada com a flag |
| A8 | detector `cerebro_nrestarts*` no vigia | laço de restart abaixo do burst | herda | chaves aditivas |
| A9 | `--teto-bytes-residentes` em `cerebro servir` | torna a guarda de memória provável | — | — |
| A10 | `--root` de ensaio + `.agents/runtime/prova-fila/` | provas sem tocar produção | — | só o ensaio |
| A11 | `sdactivation.NotificaWatchdog()` | WATCHDOG=1 de dentro do laço | lib | — |
| A12 | `cerebro reabrir --id/--desde` | reabrir só o que a falha queimou (hoje reabre os 39 erros legítimos) | 0 | fila |
| A13 | `tools/medir-baseline-gpu` | baseline pareado ANTES de desligar a máquina velha | 0/1/2 | `data/ops/baseline_migracao_gpu.jsonl` |

---

# O RUNBOOK

**ORDEM GLOBAL — 43 passos, executados nesta sequência:**
`1–13` = A1…A13 · `14–23` = B1…B10 · `24–31` = C-a, C-b, C-c, C-d, C-e, C-f, C-g, C-h · `32–35` = D1…D4 · `36–43` = E1…E8.
Portões que não se pulam: **A4 antes de A5** · **B1 antes de B8** · **B5→B6→B7 nessa ordem** · **B9 só com o binário novo já no ar** · **B2+B3+C-a antes de qualquer passo de E3 em diante** · **D2 na ordem de raio de dano declarada lá**.

## BLOCO A — INSTRUMENTOS (nada muta produção)

**A1. `Residente` enxerga `size_vram` e `context_length`**
ANTES: `curl -s 127.0.0.1:11434/api/ps` tem `"size_vram":0` e `"context_length":8192` [M]; `grep -c 'size_vram' internal/ollama/cliente.go` → **0** [M].
AÇÃO: acrescentar `SizeVRAMBytes int64 \`json:"size_vram"\`` e `ContextLength int \`json:"context_length"\`` a cliente.go:275-281, com teste usando o JSON real como fixture.
DEPOIS: `./tools/go-modern test -count=1 ./internal/ollama/` → `ok`; `grep -c size_vram` ≥1.
SE NÃO VIER: campo ausente no fixture ⇒ confira `curl …/api/ps \| jq '.models[0]\|keys'` antes de mudar o struct.
ROLLBACK: para frente — campo a mais não quebra decodificação.

**A2. `cerebro status --somente-leitura`**
ANTES: `grep -c 'mode=ro' cmd/cerebro/main.go` → **0** [M]; `status()` chama `Abrir` (fila.go:276), que roda DDL no banco que o worker usa.
AÇÃO: flag abrindo `file:<fila>?mode=ro` com `busy_timeout(5000)`, no padrão de `cmd/medir-prompt-sumula-pareado/main.go:348`. Sem a flag, nada muda.
DEPOIS: `./bin/cerebro status --root /opt/wiki --somente-leitura` → exit 0; `stat -c %Y data/ai/fila.sqlite` idêntico antes/depois [X].
SE NÃO VIER: `attempt to write a readonly database` ⇒ migração ainda no caminho; isole a DDL atrás de `if !somenteLeitura`.
ROLLBACK: para frente.

**A3. `Fila.Elegiveis`**
ANTES: `Contagens` (fila.go:513) agrupa por estado e **não** olha `disponivel_em` [M] — 34.217 pendentes e 34.217 elegíveis saem iguais mesmo com tudo em backoff.
AÇÃO: `SELECT COUNT(*) FROM tarefa WHERE estado='pendente' AND disponivel_em <= ?`, mesmo `now` de `Reivindicar` (fila.go:379).
DEPOIS: teste com 2 tarefas, 1 no futuro ⇒ `Elegiveis`=1, `Contagens[pendente]`=2.
SE NÃO VIER: iguais ⇒ `Falhar` grava `disponivel_em` nulo; leia o backoff antes de mexer na query.
ROLLBACK: para frente.

**A4. BATIMENTO — `data/ops/cerebro_batimento.json` + `.jsonl`**
ANTES: `ls data/ops/cerebro_batimento*` → ausente [X]; `WatchdogUSec=0` [M] ⇒ hoje **nada** detecta worker congelado.
AÇÃO: `internal/cerebro/batimento.go` no molde de `internal/djen/heartbeat.go`. Campos: `schema_version, ts, proximo_batimento_ate, worker, pid, vcs_revision, estado(trabalhando|ocioso|pausado), pausa_motivo, executando_ids, executando_desde, prazo_do_lote_s, pendentes, elegiveis_agora, em_erro, recuperadas_no_boot, ultimo_lote_ts, ultimo_lote_resultado, modelo_residente[], loadavg1`. **DUAS escritas por iteração**, e são os dois ÚNICOS call sites (um helper só, para ninguém acrescentar um terceiro): (1) topo de `Worker.Passo` (worker.go:60, antes da saúde); (2) **depois de `Reivindicar`, antes de `executor(ectx,…)`** (entre worker.go:71 e :98) — só ela conhece `executando_ids/desde/prazo_do_lote_s`. `.json` por tmp+`rename(2)`; `.jsonl` só em transição de estado, ≤1/min (1 por passo daria ~2.900/dia [D]). `proximo_batimento_ate = agora + 5×saude-prazo(20s) + prazoDoLote(900s) + ocioso(30s) + 20%` = **1.236 s [D]**, derivado das flags do próprio worker. Grava em `data/ops/` (já em `ReadWritePaths`), **nunca em /tmp** — é o defeito do flock.
DEPOIS: `python3 -c "import json;d=json.load(open('data/ops/cerebro_batimento.json'));print(d['estado'],d['pendentes'],d['elegiveis_agora'],d['prazo_do_lote_s'])"` → estado válido, `prazo_do_lote_s`=900 [D], `pendentes`≈34.217 decrescendo [M].
SE NÃO VIER: arquivo ausente com unit `active` ⇒ a 1ª escrita ficou depois da saúde e o worker está pausado; mova para o topo absoluto. JSON truncado ⇒ faltou `rename(2)`.
ROLLBACK: para frente; classificar os dois caminhos no `.gitignore` (ruído efêmero se classifica, não se deleta).

**A5. Gate `cerebro-batimento`**
ANTES: `grep -c '"cerebro' internal/checks/checks.go` → **0** [M], nome livre.
AÇÃO: registrar em `var Names` (checks.go:298+) e o `case` no switch, molde `djen-coleta-heartbeat` (checks.go:1956 + `internal/checks/djen_coleta.go`). **Falha FECHADA**: ausente/ilegível⇒"morto"; `agora > proximo_batimento_ate`⇒"morto-ou-congelado"; `pausado` há >4 prazos (~82 min [D])⇒"pausa crônica"; `trabalhando` com `agora-executando_desde > 1,5×prazo_do_lote_s` (1.350 s [D])⇒"travado"; `ocioso` com `elegiveis_agora=0`⇒OK; `ocioso` com `elegiveis_agora>0` por >2 prazos⇒"não reivindica". Janela do `.jsonl` = **duas cadências** (djen/heartbeat.go:99-124). **Não** chama systemctl, **não** abre a fila, **não** fala com o Ollama.
DEPOIS: `./tools/go-modern run ./cmd/check cerebro-batimento` → exit 0 [X]; `./tools/go-modern test -count=1 ./internal/checks/` → ok (`dispatcher_orfao_test.go` reprova nome sem case).
SE NÃO VIER: exit 1 "morto" na 1ª execução ⇒ o gate foi compilado antes do binário do cérebro; A4 no ar primeiro.
ROLLBACK: para frente; `internal/checks` está fora do grafo do validador ⇒ sem reatestação.

**A6. `tools/check-mascara-de-exit` — o censo do P10**
ANTES: 22 máscaras [M]; 9 units com `ExecMainStatus=1`+`Result=success` [M].
AÇÃO: criar READ-ONLY (grava só com `--gravar`, BUG-236). Por unit: máscara declarada, `ExecMainStatus`/`Result` vivos, `ExecStart`, e se a ferramenta tem canal próprio (`grep -c 'notify-owner\|avisar_dono'`). Exit **1** = máscara escondendo exit≠0 **sem** canal próprio; exit **2** = não mediu.
DEPOIS: exit 1 nomeando exatamente **4 units**: corpus-oraculo-recoleta, fontes-alcancaveis, qualidade-diaria, qualidade-longa [M].
SE NÃO VIER: >4 ⇒ a heurística casa comentário; ancore em linha não-comentada, como `check-units-alarme` faz.
ROLLBACK: para frente.

**A7. `--nao-gravar` em `check-portal-health`**
ANTES: :601-610 grava `portal_health_state.json` **incondicionalmente**, com `reparo_ultimo:""` sem `--repair` [M]. A guarda anti-laço (:453,:470-472) lê esse campo: **uma** execução de diagnóstico entre dois `--repair` faz o 2º **redisparar o deploy**.
AÇÃO: flag que pula state, histórico e `avisar_dono`. Padrão inalterado.
DEPOIS: `md5sum data/ops/portal_health_state.json` idêntico antes/depois de `./tools/check-portal-health --nao-gravar` [X].
SE NÃO VIER: md5 mudou ⇒ há 2ª escrita (histórico, :615) fora da guarda.
ROLLBACK: para frente.

**A8. Detector `NRestarts` do CÉREBRO no vigia**
ANTES: `grep -c 'cerebro' tools/check-portal-health` → **0** [M]: cobre `server` e `social`, não o cérebro.
AÇÃO: bloco **aditivo** (:545-548 exige não mudar chave existente): `cerebro_service_state`, `cerebro_nrestarts`, `cerebro_nrestarts_delta`, `cerebro_restart_loop`. `cerebro_nrestarts` **tem de PERSISTIR** no `json.dump` de :607-609 — sem isso o delta compara o contador consigo mesmo e dá zero para sempre (o defeito que :604-606 narra para a rede social). Chave de alerta `cerebro-loop-restart`, severidade **alta** (não `critica`: o acervo não cai).
DEPOIS: prove **por harness, nunca rodando o vigia**: `./tools/test_portal_health_reparo_unit_ausente.sh` verde + teste irmão injetando NRestarts 3→7 exigindo `cerebro_restart_loop=true` e `delta=4`.
SE NÃO VIER: delta sempre 0 ⇒ a chave não foi persistida no dump.
ROLLBACK: para frente; chave aditiva não quebra leitor.

**A9–A13 (mesma disciplina, condensados)**
A9 `--teto-bytes-residentes` em `servir`: `guardaDeSaude` (main.go:121-126) só repassa `LockPesado` e `CargaMax` [M], então `TetoBytesResidentes` (saude.go:67) só é alcançável por `saude_test.go` ⇒ a guarda de memória **não tem prova negativa possível**. DEPOIS: prova C-g executável.
A10 `--root` de ensaio em `.agents/runtime/prova-fila/<carimbo>/` com `content/pages.json` (exigido por main.go:111-113 [M]) e `data/ai/` próprio. Sem ele as provas C-a/b/d/e não têm onde rodar.
A11 `sdactivation.NotificaWatchdog()` reusando `notifica(ambienteDoProcesso(),"WATCHDOG=1")` (:204) [M]. **Não** criar terceira implementação.
A12 `cerebro reabrir --id/--desde`: hoje não filtra por id (fila.go:477-490) [M] e reabre junto os **39 erros legítimos** [M].
A13 `tools/medir-baseline-gpu`: ver E1.

## BLOCO B — P9, NA ORDEM DO §3

**B1. Boot não morre sem Ollama**
ANTES: main.go:157-159 `cliente.Versao` ⇒ `return err` ⇒ `os.Exit(1)` (:80-81) [M].
AÇÃO: trocar por `log.Printf` e seguir — `Saude.Verifica` (saude.go:120-122) **já** pausa com "ollama fora do ar" a cada ciclo. `CarregaAcervo` e `Abrir` continuam FATAIS: acervo ausente e fila corrompida não são transitórios.
DEPOIS: com o Ollama parado, `systemctl show … -p ActiveState -p NRestarts` → `active`, NRestarts **sem crescer** [X]; journal traz "pausa: … ollama fora do ar".
SE NÃO VIER: se ainda morrer, o `os.Exit(1)` veio de outro erro do boot — leia a linha do journal, não presuma.
ROLLBACK: para frente.

**B2. Erro de TRANSPORTE = pausa, não falha de tarefa**
ANTES: worker.go:100-112 cobra `Falhar` de **todas** as tarefas do lote no erro geral [M].
AÇÃO: em `internal/ollama`, classificar `connection refused`, `EOF`, DNS e 5xx como `ErrTransporte`; em `Passo`, `errors.Is(...)` ⇒ `ErrPausado` **sem** `Falhar` e **sem** incrementar `tentativas`. 404 (modelo ausente) é erro de CONTEÚDO e continua em `Falhar` — quem o segura é B3.
DEPOIS: prova C-a — `tentativas` do lote **não muda**, journal diz "pausa".
SE NÃO VIER: `tentativas` subiu ⇒ a classificação não alcançou o erro; imprima `%#v` do erro na prova antes de ajustar.
ROLLBACK: para frente.

**B3. DISJUNTOR de lotes consecutivos falhos — portão de P12**
ANTES: worker.go:156-180 `if n > 0 { continue }` pula o `time.After` mesmo com lote FALHO [M]; saúde em cache 60 s [M]. [D] Ollama fora ⇒ milhares tocadas em 60 s; modelo removido ⇒ fila inteira em `erro` em ~30 min.
AÇÃO: `Worker.lotesFalhosSeguidos`. Lote com erro geral ⇒ **não** entra no `continue` (dorme `IntervaloOcioso`) e incrementa; ≥3 seguidos ⇒ `w.ultimaSaude = time.Time{}` (força reconsulta) e pausa `IntervaloOcioso × 2^min(n,5)` (30 s → 16 min [D]), com log nomeando o disjuntor. Lote OK zera.
DEPOIS: prova C-b — com o modelo removido, em 10 min `estado='erro'` cresce **no máximo 9** (3 lotes × max-lote 3) [D]. Consulta: `sqlite3 "file:<ensaio>/data/ai/fila.sqlite?mode=ro" "SELECT estado,COUNT(*) FROM tarefa GROUP BY estado"`.
SE NÃO VIER: passou de 9 ⇒ o `continue` ainda está no caminho do erro; o `switch` de `Roda` trata `default:` sem distinguir lote OK de falho — `Passo` precisa devolver o sinal.
ROLLBACK: para frente.

**B4. `Saude.ModelosExigidos` contra `/api/tags`**
ANTES: `grep -c 'api/tags' internal/cerebro/saude.go` → **0** [M]; `/api/tags` responde em **0,020 s** e lista 9 modelos [M].
AÇÃO: `Cliente.Modelos(ctx)` + `Saude.ModelosExigidos` alimentado pelos modelos com tarefa **elegível** (A3). Ausente ⇒ `ErrPausado` "modelo X ausente no Ollama", nunca `Falhar`.
DEPOIS: prova C-b — pausa limpa em ≤60 s [D, `--saude-a-cada 60s`], `estado='erro'` **inalterado**.
SE NÃO VIER: pausou com a fila vazia ⇒ está lendo `pendente` em vez de elegível.
ROLLBACK: para frente.

**B5. flock p1 — `O_RDONLY` sem `O_CREATE`, com ENOENT tratado**
ANTES: `stat -c 'inode=%i owner=%U mode=%a' /tmp/opt-wiki-agent-heavy.lock` → `39454263 rafael 644` [M]; `sudo -n nsenter -t $(systemctl show wikijuridica-cerebro.service -p MainPID --value) -m stat -c 'inode=%i' /tmp/opt-wiki-agent-heavy.lock` → `39739472` [M]. Inodes diferentes = **a guarda nunca guardou nada**.
AÇÃO: carga_linux.go:18 → `os.OpenFile(caminho, os.O_RDONLY, 0)`. **No mesmo commit e obrigatório:** `if errors.Is(err, fs.ErrNotExist) { return false, nil }` antes do `return false, err` de :19-21 — sem isso ENOENT vira `ErrPausado` **eterno**, e o prefixo `-` do B7 faz reincidir a cada boot. Teste com caminho inexistente exigindo `(false, nil)`.
DEPOIS: `./tools/go-modern test -count=1 ./internal/cerebro/` → ok; com o binário no ar, batimento (A4) segue `trabalhando`.
SE NÃO VIER: `pausado` com motivo `lock pesado … no such file` ⇒ a cláusula ENOENT não entrou.
ROLLBACK: para frente.

**B6. flock p2 — tmpfiles.d cria o lock**
ANTES: `/usr/lib/tmpfiles.d/tmp.conf` → `D /tmp 1777 root root -` [M]: /tmp é esvaziado no boot. `ls /etc/tmpfiles.d/` → só `cpu-energia.conf`, `thp.conf` [M].
AÇÃO: criar `ops/tmpfiles.d/wikijuridica-agent-heavy-lock.conf` com UMA linha `f /tmp/opt-wiki-agent-heavy.lock 0644 rafael rafael -` (casa o `rafael 644` medido, que é quem a bancada e as sessões usam). Instalar **por SYMLINK**, não cópia: `sudo -n ln -sf /opt/wiki/ops/tmpfiles.d/wikijuridica-agent-heavy-lock.conf /etc/tmpfiles.d/` — `cpu-energia.conf` é cópia [M] e é a deriva invisível que o contrato manda evitar. Aplicar: `sudo -n systemd-tmpfiles --create /etc/tmpfiles.d/wikijuridica-agent-heavy-lock.conf`.
DEPOIS: `stat -c '%i %U %a' /tmp/opt-wiki-agent-heavy.lock` → `rafael 644`, inode **inalterado** se já existia (tmpfiles não recria o existente); `ls -l /etc/tmpfiles.d/` mostra **symlink**.
SE NÃO VIER: erro de permissão ⇒ `/tmp` precisa ser 1777 (é). Arquivo sumindo após reboot ⇒ o snippet não foi lido; confira o nome e re-rode `--create`.
ROLLBACK: para frente — remover o symlink não apaga o arquivo já criado.

**B7. flock p3 — `BindReadOnlyPaths` com `PrivateTmp=true`**
ANTES: `systemctl show … -p PrivateTmp --value` → `yes` [M]; **B5 e B6 concluídos** (a ordem é obrigatória: bind sobre caminho inexistente = `226/NAMESPACE` em laço de boot).
AÇÃO: em `[Service]`, **mantendo `PrivateTmp=true`** (fonte primária `src/core/namespace.c`, systemd 252.39-1~deb12u2: bind mounts convivem com PrivateTmp), acrescentar `BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock` — o `-` é o que impede o laço se o arquivo faltar. **No mesmo passo:** `sudo -n systemctl daemon-reload && sudo -n systemctl restart wikijuridica-cerebro.service`.
DEPOIS: os dois `stat` do B5 devolvem **o MESMO inode** [X — hoje 39454263 ≠ 39739472]; `systemctl show … -p NeedDaemonReload --value` → `no`.
SE NÃO VIER: `226/NAMESPACE` ⇒ o arquivo não existe no host, volte ao B6. `NeedDaemonReload=yes` ⇒ `deploy-publico` passo 0a/7 falha **para todas as frentes** — rode o reload já.
ROLLBACK: para frente — apagar a linha + `daemon-reload` + `restart`. A unit é symlink: a edição já muda o que o systemd lê, e ninguém avisa que caiu; por isso o DEPOIS é no mesmo passo.

**B8. `StartLimitIntervalSec` em [Unit] + quem tira do `failed`**
ANTES: `StartLimitIntervalUSec=10s`, `Burst=5`, `RestartUSec=15s` [M], **nenhum declarado na unit**. Burst inalcançável ⇒ `failed` nunca ⇒ `OnFailure` é decoração. Precedente: 87 restarts da rede social em produção, sem alerta.
AÇÃO: em **[Unit]** (em [Service] o systemd **ignora em silêncio** — `wikijuridica-server.service:55-62` narra que só `systemctl show` revelou): `StartLimitIntervalSec=300` e `StartLimitBurst=5`. Com RestartSec=15, 5 partidas custam ~75 s [D] ⇒ cabem em 300 s ⇒ burst **alcançável** ⇒ `failed` ⇒ `OnFailure=wikijuridica-alerta@%N` dispara. **Pré-requisito: B1 pronto**, senão um restart transitório do Ollama no boot queima o burst. **Recuperação nomeada, não deixada em aberto:** `failed` dá ALERTA, não recuperação; o ramo de reparo vai em `check-portal-health --repair` (timer de 2 min) — vendo `ActiveState=failed` há >10 min e `cerebro_restart_loop=false`, executa `sudo -n systemctl reset-failed wikijuridica-cerebro.service && sudo -n systemctl start wikijuridica-cerebro.service`, **no máximo 1×/hora**, gravando em `reparo`. `sudo -n -l` confirma `(ALL) NOPASSWD: ALL` [M]. **E `tools/deploy-cerebro` ganha `sudo -n systemctl reset-failed "$UNIT" || true` ANTES do `restart`, no mesmo commit** — senão dois deploys em 5 min batem no limite.
DEPOIS: `systemctl show … -p StartLimitIntervalUSec -p StartLimitBurst` → `5min` e `5` [X]; prova C-e mostra `failed` + alerta instanciado + linha nova em `data/ops/owner_alerts.jsonl`.
SE NÃO VIER: `StartLimitIntervalUSec` continuar `10s` ⇒ a diretiva foi para [Service] — a falha muda que o comentário do `server.service` narra. E `Failed to restart: start request repeated too quickly` **depois de um deploy é o limite funcionando, não defeito**: `sudo -n systemctl reset-failed wikijuridica-cerebro.service` e repita.
ROLLBACK: para frente — apagar as duas linhas + `daemon-reload`.

**B9. `Type=notify` + `WatchdogSec` + `TimeoutStartSec` — binário ANTES da unit**
ANTES: `systemctl show … -p Type -p WatchdogUSec` → `simple`, `0` [M]. A4 no ar. `NotificaPronto` em sdactivation.go:200 [M].
AÇÃO, em duas partes **nesta ordem**: (i) em `cmd/cerebro/main.go`, `sdactivation.NotificaPronto()` **depois de `Abrir`+`Recuperar`** (o daemon está pronto quando a fila abriu, não quando o Ollama respondeu — ver B1), e `sdactivation.NotificaWatchdog()` **nos mesmos dois call sites do batimento (A4)**, dentro de `Worker.Passo`, **nunca** de goroutine com ticker cego (que continuaria batendo com o worker travado). Subir por `./tools/deploy-cerebro` **antes** de tocar a unit. (ii) só então, em [Service]: `Type=notify`, `WatchdogSec=1500`, **`TimeoutStartSec=300`**.
  · **1500 s [D]**: intervalo máximo entre batidas = 5 sondas × `--saude-prazo 20s` (100) + `prazoDoLote` 900 + escrituração/backoff sqlite (~30) ≈ **1.030 s**; 1500 dá 45% de folga. Baixar para ~450 s exigiria bater por tarefa dentro de extracao.go:341-343 (uma chamada ao Ollama por tarefa [M]), o que muda a assinatura de `Executor` nos 4 executores — fica registrado como refinamento, não como este passo.
  · **`TimeoutStartSec=300`**: com `Type=notify` o default de 90 s governa o prazo do READY=1, e o tempo de boot do cérebro **não foi medido** (a linha já rotacionou do journal — §7) sobre `CarregaAcervo` de 11k páginas + `Abrir` de 139 MB + `Recuperar`. 300 s evita que a primeira partida estoure e **queime uma vaga do burst do B8**. Medir na 1ª partida (journal `Started`→READY) e apertar depois [X].
DEPOIS: `systemctl show … -p Type -p WatchdogUSec -p TimeoutStartUSec -p NRestarts` → `notify`, `25min`, `5min`, NRestarts sem crescer em 30 min [X]. Prova C-d: `kill -STOP` ⇒ `failed` por watchdog em ≤25 min, contra **nunca** hoje.
SE NÃO VIER: `Job … timed out` na partida ⇒ READY=1 não saiu; volte a unit para `Type=simple` (edição para frente + `daemon-reload`) e conserte o binário antes de reinsistir — é o precedente de socket/`Type=notify` que já custou laço de boot aqui.
ROLLBACK: para frente — `Type=simple`, remover `WatchdogSec`, `daemon-reload`, `restart`.

**B10. Limpar os comentários que mentem na unit**
ANTES: cabeçalho diz `MemoryMax=15G` e `OLLAMA_MAX_LOADED_MODELS=1` [M]; o drop-in vivo diz `12G` e `2` [M].
AÇÃO: corrigir **na mesma edição** de B7/B8/B9 (não abrir edição extra sobre arquivo de unit). Parágrafo superado ganha data e motivo; não se apaga.
DEPOIS: `grep -c '15G\|MAX_LOADED_MODELS=1' ops/systemd/wikijuridica-cerebro.service` → 0 fora de linha datada [X].
SE NÃO VIER: n/a. ROLLBACK: para frente.

## BLOCO C — AS SETE PROVAS NEGATIVAS

Regra comum: **C-a, C-b, C-d, C-e, C-f, C-g rodam em unit VOLÁTIL** com cópia da fila e `--root` de ensaio (A10), com o worker de produção parado por `sudo -n systemctl stop wikijuridica-cerebro.service` (parada explícita é limpa: `Restart=` não se aplica e `OnFailure` não dispara). Só **C-c** é segura contra produção. Molde:
`sudo -n systemd-run --unit=cerebro-prova --collect -p Restart=always -p RestartSec=15 -p 'OnFailure=wikijuridica-alerta@%N.service' -p User=rafael -p WorkingDirectory=/opt/wiki /opt/wiki/bin/cerebro servir --root <ensaio> --fila <copia> --worker prova-1`

**C-a. Ollama cai.** ANTES: `systemctl show ollama.service -p Restart -p RestartUSec -p NRestarts` → `always`, `3s`, `0` [M]. AÇÃO: `sudo -n kill -9 $(systemctl show ollama.service -p MainPID --value)` — **não** `systemctl stop`, que nunca aciona `Restart=` e viraria outra prova. DEPOIS: "pausa: … ollama fora do ar" em ≤60 s [D]; contagem por estado e `tentativas` inalterados (B2); Ollama volta em ~3 s [M]. SE NÃO VIER: `erro` crescendo ⇒ B2 não classificou; imprima `%#v`. ROLLBACK: `sudo -n systemctl start ollama.service`; `systemctl stop cerebro-prova`.

**C-b. Modelo removido.** ANTES: `/api/tags` → **9 modelos** [M]. AÇÃO: `ollama cp qwen3.5:4b qwen3.5:4b.backup` **antes**, depois `ollama rm qwen3.5:4b` (falam com a API; dispensa `sudo -u ollama`). DEPOIS: pausa "modelo ausente" em ≤60 s (B4); `erro` cresce **≤9** se só o B3 pegar [D]; **0** se o B4 pegar. SE NÃO VIER: milhares em erro ⇒ nem B3 nem B4 no binário vivo; `./tools/go-modern version -m bin/cerebro | grep vcs.revision` contra o HEAD. ROLLBACK: `ollama cp qwen3.5:4b.backup qwen3.5:4b && ollama rm qwen3.5:4b.backup`.

**C-c. `kill -9` no worker — ÚNICA segura em produção.** ANTES: `NRestarts` → **1** [M]. AÇÃO: `kill -9 $(systemctl show wikijuridica-cerebro.service -p MainPID --value)` (roda como `rafael`; dispensa sudo). DEPOIS: **capture o journal IMEDIATAMENTE** — `journalctl -u wikijuridica-cerebro.service --since "-90s" --no-pager | head -5` — exigindo "N tarefas recuperadas de worker anterior" (main.go:174); NRestarts → **2** [D]; `erro` inalterado. SE NÃO VIER: a retenção não guarda essa linha para depois (registro mais antigo é 2026-09-15T04:20:08 contra boot de 2026-09-14 04:40:57 [M]) — por isso o número entra no batimento (`recuperadas_no_boot`), não no log. ROLLBACK: nenhum; volta em 15 s.

**C-d. `kill -STOP` — congelado, não morto.** ANTES: `WatchdogUSec=0` [M], **nada** detecta. AÇÃO: `kill -STOP <pid do volátil>`, suspendendo por **MENOS que `prazo_do_lote_s` (900 s)** — os timers do Go usam relógio de parede e, no `SIGCONT`, prazo vencido falha o lote na hora, gastando `tentativas` numa recuperação "correta". DEPOIS: `/proc/<pid>/status` → `State: T (stopped)` enquanto `systemctl` diz `active (running)`; o `.json` para de avançar; com B9, `failed` em ≤25 min [D]; o gate A5 reprova em ≤1.236 s [D]. SE NÃO VIER: `systemctl show -p WatchdogUSec` decide se falta a diretiva ou o `WATCHDOG=1`. ROLLBACK: `kill -CONT <pid>`.

**C-e. Fila corrompida ⇒ o alerta finalmente dispara.** ANTES: `Abrir` falha em `EsquemaSQL/PRAGMA index_list` (fila.go:291-304) antes de qualquer reivindicação e `main.go:81` faz `os.Exit(1)`; com burst inalcançável, laço eterno **sem alerta** [M]. AÇÃO: corromper o **CABEÇALHO** de uma **CÓPIA**: `dd if=/dev/zero of=<copia> bs=1 seek=0 count=4 conv=notrunc`. Nunca no banco real, e tem de ser o cabeçalho: um 2º `cerebro servir` com `--root /opt/wiki` e uma fila que **abre** trabalharia o corpus real e faria append em `data/ai/extracoes_dispositivos.jsonl`. DEPOIS: com B8, `failed` em ~75 s [D: 5×15 s] e **linha nova em `data/ops/owner_alerts.jsonl`** [X] — leia o **ledger de alerta**, não `systemctl status cerebro-prova`: o `--collect` descarta a unit volátil quando ela falha, por desenho. Sem B8 (baseline de hoje): `activating/auto-restart` para sempre, zero alerta. SE NÃO VIER: `failed` sem alerta ⇒ `OnFailure` foi para [Service] (R-D) ou o alvo não existe (R-B). ROLLBACK: apagar a cópia.

**C-f. Segurar o flock pesado.** ANTES: B5+B6+B7 concluídos e inodes **iguais**. AÇÃO: avise as frentes por `./tools/generate-coord-message` **antes** (esse lock bloqueia build e commit de Go de toda sessão e a bancada) e **time-box**: `timeout 120 flock -x /tmp/opt-wiki-agent-heavy.lock tail -f /dev/null &` — `sleep` como forma de esperar é barrado por hook. DEPOIS: journal com "pausa: /tmp/opt-wiki-agent-heavy.lock tomado: compilacao ou commit de Go em curso" em ≤2 ciclos (120 s [D]). **Baseline de hoje: NADA acontece** [M, por inode/namespace]. SE NÃO VIER: nada no journal ⇒ inodes voltaram a divergir; repita `stat`/`nsenter` do B5. ROLLBACK: `kill %1`.

**C-g. Teto de bytes residentes a 1 byte.** ANTES: **não executável hoje** — `guardaDeSaude` não repassa `TetoBytesResidentes` [M]. Exige A9. AÇÃO: unit volátil com `--teto-bytes-residentes 1`. DEPOIS: pausa no 1º ciclo (≤60 s [D]) com "ollama com 1 modelos residentes somando 3,01 GiB, acima do teto de 0,00 GiB" [M: o residente de hoje é 3.227.894.413 B]. SE NÃO VIER: não pausou ⇒ o teto não chegou à `Saude`. ROLLBACK: parar a volátil.

**C-h. Registrar as sete.** Cada prova grava linha em `.agents/runtime/prova-fila/<carimbo>/provas.jsonl` com `prova, antes, acao, depois, esperado, obtido, veredito`. É o que impede a próxima sessão depender de prosa — a medição de 2026-09-05 que fixa a ordem 6→7→8 só existe como mensagem de commit; não repetir o erro.

## BLOCO D — P10: TIRAR A MÁSCARA SEM INUNDAR O DONO

Censo medido — das 22 máscaras, **9 units estavam com `ExecMainStatus=1` mascarado para `success`** [M]:

| unit | ExecStart | canal próprio (`notify-owner`/`avisar_dono`) | veredito |
|---|---|---|---|
| alertas-abertos | `generate-alertas-reconciliados` | **1** | legítima — documentar |
| daily-content | `run-daily-content` | **4** | legítima |
| daily-content-noticias | `run-daily-content --somente-noticias` | **4** | legítima |
| efeito-nos-bots | `check-efeito-nos-bots --horas 24 --notificar` | **3** | legítima |
| untracked-inventory | `check-untracked-e-alertar` | **2** | legítima |
| **corpus-oraculo-recoleta** | `flock … run-recoleta-corpus-oraculo` | **0** | **silenciosa — piloto** |
| **fontes-alcancaveis** | `check-fontes-alcancaveis --gravar` | **0** | **silenciosa — piloto** |
| **qualidade-diaria** | `flock … run-qualidade-diaria` | **0** | **silenciosa — piloto** |
| **qualidade-longa** | `flock … run-qualidade-diaria` | **0** | **silenciosa — piloto** |

Discriminador, verificável por grep e não por prosa: *a máscara é legítima se e somente se a ferramenta tem canal próprio de alerta que dispara no código mascarado*.

**D1. Censo antes de qualquer edição de unit.** ANTES: 22 máscaras, 9 mordendo [M]; `./tools/check-units-alarme` → exit 0 hoje (o critério atual é só "registrou o porquê ao lado") [M]. AÇÃO: criar A6 e rodar. DEPOIS: exit 1 nomeando **4 units / 3 ferramentas** [M]. SE NÃO VIER: ver A6. ROLLBACK: n/a (read-only).

**D2. Código de saída próprio nas 3 ferramentas, NESTA ORDEM de blast radius.**
ANTES: canal próprio nas três → **0, 0, 0** [M]; último exit das 4 units → 1,1,1,1 [M].
AÇÃO: separar **NÍVEL** de **FLUXO**: exit **4** = "veredito de nível: estoque conhecido, nenhuma entrada nova desde a linha datada"; exit **1** = **regressão nova**. O nível vira linha datada no ledger da própria ferramenta. **4 e não 3:** a convenção do repo é 0/1/2/75 e o **3 já significa "catálogo remoto indisponível"** em `check-api-catalog-usage:487-506` [M]; o 4 é livre nas três (0,0,0) [M]. **Ordem obrigatória:** (1) `check-fontes-alcancaveis` (timer curto, menor raio); (2) `run-recoleta-corpus-oraculo`; (3) `run-qualidade-diaria` **por último** — ele é a bancada, roda sob `flock heavy` por 60+ min e às 04:47 -03; um exit 1 indevido ali dispara alerta de madrugada. Cada uma só avança depois de a anterior ter passado **um ciclo inteiro de timer** limpa.
DEPOIS: exit **4** com "nível N, sem entrada nova" [X]; **prova por mutação**: injete uma entrada nova na fixture e exija exit **1**.
SE NÃO VIER: continuar 1 sem entrada nova ⇒ a ferramenta não tem noção de "anterior"; crie a linha datada primeiro — sem ela o exit 4 seria invenção.
ROLLBACK: para frente.

**D3. Trocar a máscara nas 4 units.** ANTES: `=1`, `=0 1`, `=1`, `=1` [M]. AÇÃO: `SuccessExitStatus=0 4` **com o comentário adjacente** que a R-E de `check-units-alarme` exige, nomeando o que é 4, o que é 1, e a medição de 2026-09-15; `sudo -n systemctl daemon-reload` no mesmo passo. DEPOIS: `./tools/check-units-alarme` → exit 0 [X]; `./tools/test_units_alarme.sh` verde; `./tools/check-mascara-de-exit` → exit 0 [X]; `NeedDaemonReload=no` nas 4. SE NÃO VIER: reprovar por R-E ⇒ comentário não adjacente. Unit indo a `failed` depois ⇒ a ferramenta devolveu 1 de verdade: **leia a saída antes de recolocar a máscara**. ROLLBACK: para frente — voltar a `=0 1` + `daemon-reload`.

**D4. Documentar as 5 legítimas e fechar o gate.** ANTES: canal próprio medido (1,4,4,3,2) [M]. AÇÃO: comentário registrando **o canal próprio como razão** (não "é veredito", que é vago): "mascarado porque `<ferramenta>` chama `notify-owner` no caminho do exit N; OnFailure aqui duplicaria o alerta". Endurecer A6 para exigir essa forma. DEPOIS: `./tools/check-mascara-de-exit` → exit 0, 22 classificadas, **0 silenciosas** [X]. SE NÃO VIER: sobrou alguma ⇒ a ferramenta alerta em caminho diferente do código mascarado; trate como piloto (D2). ROLLBACK: para frente.

## BLOCO E — P12: MIGRAÇÃO PARA A RTX 5060 Ti 16 GB

**Portão de entrada:** B2+B3 no binário vivo e prova C-a verde (§2). Com `LLM_LIBRARY=cpu` nenhum dos quatro bloqueios morde; eles mordem **na virada**, nesta ordem: **(1) driver → (2) runner carrega → (3) flash-attn/#18232 → (4) guarda de memória cega**.

**E1. BASELINE PAREADO ANTES de desligar a máquina velha.**
ANTES: `/api/tags` → 9 modelos com `digest` [M]; `ollama --version` → **0.33.3** [M]; prefill p50 13,6–14,5 tok/s, decode p50 5,4–5,6 (diagnóstico).
AÇÃO: criar `tools/medir-baseline-gpu` e rodar na máquina velha, gravando `data/ops/baseline_migracao_gpu.jsonl`: (i) `ollama --version`; (ii) o `digest` de cada modelo vindo de `/api/tags` — **é a identidade portável, sem sudo e sem ler blob** [M]; (iii) N=30 saídas de `cmd/medir-prompt-sumula-pareado` a temperatura 0, amostra por stride determinístico, classificadas por `cerebro.URNDaCitacaoPublica` (a régua do executor); (iv) tok/s de prefill e decode **com o `loadavg` declarado ao lado de cada número**.
DEPOIS: arquivo com **9 digests** [M] + N=30 pares; `sha256sum` do próprio arquivo registrado.
SE NÃO VIER: sem baseline, "o mesmo modelo nas duas máquinas" é **fé**. Não avance.
ROLLBACK: n/a (só ledger).
ESPERA FÍSICA, com número e atalho: N=30 = 60 chamadas; a ~44 s cada sob a carga de hoje [M] ⇒ ~44 min. É **vazão do modelo em tok/s**, causa física declarada, não espera de terceiro. **Atalho:** a carga é a variável — `./tools/check-load-headroom --max 12` antes, e o custo cai para ~29 s/chamada (taxa de 168 h [M]) ⇒ ~29 min.

**E2. Bloqueio 1 — driver com módulos OPEN.**
ANTES (na máquina nova): `cat /etc/debian_version`; `apt-cache policy nvidia-kernel-open-dkms`; `dpkg -l | grep nvidia-kernel`; `nvidia-smi; echo $?`. Na velha medi: bookworm 12.15, candidato **615.71.09-2** do repo debian12 já configurado, instalado o **proprietário** 610.57.04-1, `dkms status` vazio, `nvidia-smi` **exit 9** [M].
AÇÃO: replicar `/etc/apt/sources.list.d/cuda*.list` + `/usr/share/keyrings/cuda-archive-keyring.gpg`; `sudo apt update`; **exigir** candidato **≥ 570.26**; `sudo apt install nvidia-kernel-open-dkms nvidia-driver` e remover `nvidia-kernel-dkms` se presente.
DEPOIS: `nvidia-smi; echo $?` → **0** (sem pipe: `nvidia-smi | head; echo $?` imprimiu 0 com o comando falhando [M, erro meu nesta sessão]); `dkms status` com linha para o kernel em execução; `ls /proc/driver/nvidia` existe; `nvidia-smi --query-gpu=name,memory.total --format=csv` → `NVIDIA GeForce RTX 5060 Ti, 16384 MiB` [X].
SE NÃO VIER: candidato <570.26 ⇒ repo errado. `dkms status` vazio ⇒ falta `linux-headers-$(uname -r)`. `nvidia-smi` ≠0 com dkms ok ⇒ Secure Boot barrando módulo não assinado: `mokutil --sb-state`.
ROLLBACK: para frente; o Ollama segue em `LLM_LIBRARY=cpu` e o cérebro não para — nada foi virado ainda.

**E3. Bloqueio 2 — o runner CUDA carrega de fato.**
ANTES: `cuda_v12` e `cuda_v13` presentes; `grep -c sm_120` → **8** em v12, **0** em v13 [M]. Remover `LLM_LIBRARY=cpu` **não basta**: sem alvo explícito o Ollama pode escolher o v13, que é PTX puro.
AÇÃO: no drop-in `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`, `OLLAMA_LLM_LIBRARY=cuda_v12`; `sudo -n systemctl daemon-reload && sudo -n systemctl restart ollama.service`. **O cérebro está parado neste passo** (portão do §2).
DEPOIS: um `generate` curto e `curl -s .../api/ps` → **`size_vram > 0`** [X — hoje é 0 [M]]; `journalctl -u ollama --since -5min | grep -i 'cuda\|runner'` nomeando o v12.
SE NÃO VIER: `size_vram=0` com driver ok ⇒ caiu para CPU; leia o journal do Ollama, **não** aumente timeout. Acusou PTX JIT ⇒ é o v13: `systemctl show ollama.service -p Environment`.
ROLLBACK: para frente — `LLM_LIBRARY=cpu` + `daemon-reload` + `restart` volta ao estado medido de hoje.

**E4. Bloqueio 3 — flash attention × `num_ctx` (ollama#18232).**
ANTES: o drop-in vivo tem `FLASH_ATTENTION=1` **e** `CONTEXT_LENGTH=8192` [M] — **4× o contorno publicado (2048)** para 5060 Ti + Ollama 0.33.3 + runner CUDA; `/api/ps` confirma `context_length: 8192` em uso [M].
AÇÃO: um `generate` único com ctx 8192 **esperando a falha** (`cudaFuncSetAttribute`/shared memory), para datar o bloqueio neste host; depois `OLLAMA_CONTEXT_LENGTH=2048` e repetir. **Não desligar `FLASH_ATTENTION`**: sem ele o `KV_CACHE_TYPE=q8_0` degrada para f16 **em silêncio** e o KV dobra.
DEPOIS: com 2048, `generate` conclui e `/api/ps` mostra `context_length: 2048` e `size_vram > 0` [X]. O `ContextLength` do A1 é o que torna isso observável por instrumento, não por olho.
SE NÃO VIER: se 8192 **funcionar**, grave a evidência (versão, driver, saída) no ledger de E1 e **não** baixe o contexto — o contorno é do issue, não deste host. Se 2048 também falhar, não é #18232: leia o erro real.
ROLLBACK: para frente — `CONTEXT_LENGTH=8192` + `daemon-reload` + `restart`.

**E5. Bloqueio 4 — a guarda de memória vira DUAS contas, derivadas em RUNTIME.**
ANTES: saude.go:90-92 `TetoBytesResidentesPadrao = 9<<30`, somando só `size` [M]; `Residente` cego para `size_vram` [M] (corrigido em A1).
AÇÃO: substituir a conta única por duas, **selecionadas pelo próprio `/api/ps`, não por coordenação de commit**: se **todo** residente tem `size_vram == 0` ⇒ regime CPU, vale `sum(size) <= 9 GiB` (o teto de hoje, que passa com os 3,01 GiB medidos); se **algum** tem `size_vram > 0` ⇒ regime GPU, valem `sum(size_vram) <= 13 GiB` e `sum(size - size_vram) <= 2 GiB`. Assim a guarda se autocorrige na virada do E3 — o drop-in é commit leve e o Go é commit pesado, e exigir que andassem juntos era frágil. **O predicado "`size_vram < size`" como sinal de spill pausaria o cérebro HOJE para sempre**: em CPU puro ele é verdadeiro em todo residente [M].
DEPOIS: `./tools/go-modern test -count=1 ./internal/cerebro/` com 3 casos: (i) CPU de hoje (3,01 GiB, vram 0) ⇒ **passa**; (ii) par do incidente (14b+9b=16 GB em RAM) ⇒ **barra**; (iii) GPU com 14 GiB em VRAM ⇒ **barra**.
SE NÃO VIER: worker pausando em CPU depois da mudança ⇒ o seletor de regime está invertido; imprima o regime escolhido no erro.
ROLLBACK: para frente.

**E6. O PISO DE DETERMINISMO — e por que não é igualdade byte a byte.**
ANTES: baseline de E1 no disco.
AÇÃO: rodar `cmd/medir-prompt-sumula-pareado` na máquina nova com a **mesma** amostra por stride, temperatura 0, `Think=false`, `NumPredict=512`, `PenalidadeDePresenca=0` — os parâmetros do executor de produção.
DEPOIS, piso em duas partes (temperatura 0 CPU→GPU **não** é byte-idêntico: kernel e ordem de acumulação mudam, e exigir igualdade seria um piso impossível que alguém desligaria):
 1. **auto-consistência N/N em cada máquina** — 3 repetições da mesma entrada na mesma máquina ⇒ saída idêntica. Essa **tem** de ser 100%.
 2. **paridade de classificação** — `cerebro.URNDaCitacaoPublica` sobre as N=30 saídas das duas máquinas ⇒ mesmo conjunto de URNs em **≥29 de 30** [X, piso a fixar com o baseline na mão], com cada divergência lida à mão e registrada.
 E a identidade: `ollama --version` **fixado em 0.33.3 por tarball versionado**, não pelo script de instalação, e os **9 `digest`** de `/api/tags` idênticos aos de E1 [M].
SE NÃO VIER: auto-consistência <N/N ⇒ há sampler ativo; leia o Modelfile (precedente: `presence_penalty` do Modelfile chega ao sampler). Digest diferente ⇒ **não é o mesmo modelo** e a comparação de qualidade não vale nada.
ROLLBACK: n/a.

**E7. Ganho medido, não prometido.** ANTES: prefill p50 13,6–14,5 e decode p50 5,4–5,6 tok/s na CPU (diagnóstico), com a ressalva [M] de que as cinco varreduras desta sessão levaram o loadavg a 15,84, o teto `--carga-max 12` mordeu às 20:57:04 (pausa de 1m55s) e o decode caiu de 5,6 para 3,0 ⇒ **todo tok/s de CPU medido hoje é teto inferior**. AÇÃO: repetir na máquina nova com `loadavg` declarado ao lado. DEPOIS: registrar o fator observado; a projeção de terceiros (prefill 74–130×, decode 17–23×, k de 0,648/0,660 na própria 5060 Ti contra 0,44 da 4090 — planejar pela banda subestima ~47%) entra como **expectativa citada**, nunca como medição nossa. SE NÃO VIER: ganho muito abaixo ⇒ volte ao E3 (`size_vram`) antes de culpar o modelo. ROLLBACK: n/a.

**E8. Custódia do `ops/ollama` — a lacuna que morde justo nesta frente.** ANTES: `grep -rln 'ops/ollama' tools/ internal/checks/` → **VAZIO**; `check-units-instaladas:72` tem `DIR_UNITS = RAIZ + 'ops/systemd'` (diagnóstico). O drop-in vivo é symlink e idêntico hoje [M], mas **nada acusa** se virar cópia ou ficar com reload pendente — e P12 é a frente que reescreve esse arquivo. AÇÃO: estender `DIR_UNITS` (ou gate irmão) para `ops/ollama/ollama.service.d/` e `ops/tmpfiles.d/`, com as mesmas regras: instalado por symlink, conteúdo idêntico, `NeedDaemonReload=no`. DEPOIS: `./tools/check-units-instaladas` → exit 0 com a contagem subindo de 126 (diagnóstico) para 126 + os novos [X]. SE NÃO VIER: reprovar por "cópia" ⇒ troque por symlink (precedente `cpu-energia.conf`). ROLLBACK: para frente.

## ORDEM DE COMMIT

1. **Go** (`internal/ollama`, `internal/cerebro`, `internal/checks`, `cmd/cerebro`, `internal/sdactivation`) sob **`flock /tmp/opt-wiki-agent-heavy.lock`** — o lock que o §1 do contrato nomeia. **Correção de premissa [M]:** `grep -rln 'opt-wiki-commit.lock' tools/ docs/ .githooks/ internal/` devolve **VAZIO** — o lock separado que a memória descreve **não existe no repo**, e usar o nome inexistente daria um `flock` sobre arquivo novo, que não serializa nada. **Janela proibida [M]:** a bancada diária toma esse mesmo lock no `ExecStart` e o segurou 60 min 42 s hoje (04:48:12→05:48:54); próxima em 2026-09-16 04:47:17 -03.
2. **Índice vazio antes** — `go-index-compile-closure` compila o ÍNDICE, não o pathspec (77,6 s com `internal/v2ingest` no índice contra 14,9 s limpo).
3. `git add <caminho exato>` e `git commit -F <arquivo>` em **comandos separados**.
4. Nenhum pacote tocado está no grafo do validador ⇒ **sem reatestação**. Confirme com `./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` se tocar algo novo.
5. Units e tmpfiles: commit **leve**, sempre com o `daemon-reload` já executado — `NeedDaemonReload=yes` faz `deploy-publico` falhar no passo 0a/7 para **todas** as frentes.
6. Rodar a **bancada do pacote**, não só o gate: `./tools/go-modern test -count=1 ./internal/cerebro/ ./internal/ollama/ ./internal/checks/` — gate verde não é "não quebrei nada" (precedente: gate verde com 14 de 17 testes quebrados e defeito em HEAD).

---

## O QUE NÃO FOI MEDIDO, E POR QUÊ
- **Tempo de boot do daemon do cérebro:** a linha de 2026-09-14 04:40:57 já rotacionou (registro mais antigo da unit: 2026-09-15T04:20:08). É por isso que B9 leva `TimeoutStartSec=300` em vez do default de 90 s.
- **Fração de triagem das 34.217 pendentes:** `TriagemDosPendentes` exige abrir a fila pelo binário, que é caminho de **escrita** (`Abrir` roda DDL) — só depois de A2.
- **Qualquer número de `cerebro status`:** mesmo motivo.
- **Por que `dkms status` está vazio neste host:** ver §1.
- **Determinismo CPU↔GPU:** não é mensurável antes de existir a GPU; o piso de E6 é desenhado para não exigir igualdade byte a byte.
- **Tempo de parede de `deploy-cerebro`:** rodar = mutar (build + restart).
- **`grep -c sm_120`** conta linhas binárias, não cubins: corrobora o achado do diagnóstico por método diferente, não o reproduz.

## REGRAS QUE VALEM EM TODO PASSO
1. `sqlite3` desta máquina é `/home/rafael/android-vm-lab/android-sdk/platform-tools/sqlite3` (3.50.6); unit ou gate com `PATH=/usr/bin:/bin` **não o acha** — ferramenta de verdade usa `modernc.org/sqlite`, já no `go.mod`.
2. Go **sempre** por `./tools/go-modern`; escopo amplo é `./internal/... ./cmd/...`, nunca full-tree (hook aborta com exit 2).
3. `cmd/check` **sempre** com nome.
4. Toda edição de `ops/systemd/*` (symlink para `/etc`) exige `sudo -n systemctl daemon-reload` **no mesmo passo**.
5. Antes de comando pesado: `./tools/check-load-headroom --max 12`; antes de segurar o flock: `./tools/generate-coord-message`.
6. Em pipeline, `${PIPESTATUS[0]}`.
7. Nunca `sudo nginx -t`; nunca `check-portal-health` à mão antes de A7 existir.

## O QUE O ADVISOR MUDOU

**Adotado da 1ª chamada (tudo verificado por medição antes de entrar):**
1. **O reconcile do P12 #3** — ele mandou surfacear, não obedecer nem trocar em silêncio. Medi `/etc/debian_version`=12.15, o repo CUDA já em `sources.list.d`, `nvidia-kernel-open-dkms` candidato 615.71.09-2, o instalado sendo o **proprietário**, `dkms status` vazio e `nvidia-smi` exit 9. Virou o §1, e a verificação na máquina nova passou a **medir lá** em vez de confiar nisto.
2. **B1 antes de B8** — sem isso um restart transitório do Ollama no boot queimaria o burst e deixaria o cérebro em `failed` para sempre. Virou portão explícito no §3.
3. **O portão P9→P12** — B2+B3+prova C-a antes de qualquer virada de `LLM_LIBRARY`, com o número (34.217 em `erro` em ~30 min).
4. **Quem tira do `failed`** — ele recusou deixar aberto: `failed` dá alerta, não recuperação. Nasceu o ramo de reparo no `check-portal-health --repair` com `reset-failed`, 1×/hora; conferi `sudo -n -l` = `(ALL) NOPASSWD: ALL`.
5. **Reuso do `sdactivation`** — `NotificaWatchdog()` sobre o `notifica()` já existente, e **não** uma terceira implementação (a de `cmd/server/main.go:175-204` já é a segunda).
6. **Discriminador do P10 por canal próprio de alerta** — medi `grep -c notify-owner` nas 9 units: 5 legítimas (1,4,4,3,2) e **4 silenciosas (0,0,0,0)**, que viraram o piloto.
7. **`--nao-gravar` no vigia** e **prova por harness, nunca rodando o vigia** (ele grava state e zera `reparo_ultimo`).
8. **Checar se o executor chama o Ollama por tarefa** antes de dimensionar `WatchdogSec` — medi (extracao.go:341-343, por tarefa), e por isso o refinamento para ~450 s ficou **nomeado com o custo** em vez de prometido.
9. **A armadilha do pipeline** (`nvidia-smi | head; echo $?` → 0 com exit real 9) virou regra do runbook.

**Adotado da 2ª chamada:**
10. **Teto de 400 linhas** — comprimi A9–A13, C-a/b/g e E7; o arquivo fechou em 368.
11. **B8 × `deploy-cerebro`** — dois deploys em 5 min batem no limite novo: `deploy-cerebro` ganha `reset-failed` antes do `restart`, no mesmo commit, e o `SE NÃO VIER` diz que "start request repeated too quickly" depois de um deploy é o limite funcionando.
12. **`TimeoutStartSec=300` junto com `Type=notify`** — o default é 90 s, o boot do cérebro **não foi medido** (journal rotacionado) e um timeout de partida queimaria vaga do burst do B8.
13. **Os dois pings e as duas escritas são os MESMOS dois call sites** (um helper), explícito para ninguém acrescentar um terceiro.
14. **E5 derivado em runtime** — em vez de exigir que o commit do drop-in e o do Go andassem juntos (frágil: um é leve, outro pesado), o regime CPU/GPU é escolhido pelo próprio `/api/ps`: todo residente com `size_vram==0` ⇒ teto de RAM 9 GiB; algum com `size_vram>0` ⇒ as duas contas de GPU.
15. **C-e lê o ledger de alerta, não `systemctl status`** — o `--collect` descarta a unit volátil quando ela falha, por desenho.
16. **D2 ordenado por raio de dano** — `check-fontes-alcancaveis` primeiro, `run-qualidade-diaria` **por último** (é a bancada, sob `flock heavy`, 60+ min, às 04:47 -03).

**Achado meu que o advisor não tinha, e que corrigiu o runbook:**
17. **`/tmp/opt-wiki-commit.lock` não existe no repositório** (`grep` em `tools/ docs/ .githooks/ internal/` → VAZIO). Eu havia escrito a ordem de commit com esse lock, o que daria um `flock` sobre arquivo novo — serializando nada. Trocado pelo `/tmp/opt-wiki-agent-heavy.lock` que o §1 do contrato nomeia, com a janela da bancada declarada.
18. **Exit 3 já está tomado** com o sentido "catálogo remoto indisponível" em `check-api-catalog-usage:487-506`; o código do P10 passou a ser **4**, livre nas três ferramentas do piloto (0,0,0).
19. **`sudo -n -l` = `(ALL) NOPASSWD: ALL`**, o que torna o ramo `reset-failed` executável de fato.

**Nada que eu medi foi contradito, e nada foi trocado em silêncio.**
