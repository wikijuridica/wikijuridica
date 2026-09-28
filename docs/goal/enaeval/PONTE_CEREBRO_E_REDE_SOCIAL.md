# PONTE — o cérebro (Ollama) e o serving do EnaEval; o `PLANO_REDE_SOCIAL.md` e a rede social viva do CANON

**Data:** 2026-09-24 · **Onda:** `enaeval-aterrissagem` · **Redação:** O5 (Opus 5.5), sob o chefe Fable 5.1 ·
**Decisões aplicadas:** D-D e D-E do chefe (barramento da onda, "Decisões do chefe para a onda 1"),
registradas em `docs/goal/DECISIONS.md` como **DEC-062** · **Achado que motivou:** S4 §2.1 e §2.4 — o
`CANON-v4.1.md` e a `TASKLIST.md` não citam Ollama, cérebro, `PLANO_REDE_SOCIAL.md` nem `cmd/social`
(`rg -n -i` nos dois arquivos inteiros → zero), então a ponte entre o que roda hoje e o que o CANON manda
não estava escrita em lugar nenhum.

Redação pelas regras do CANON v4.1 (`CANON-v4.1.md:43-48`): o nome é EnaEval; nenhuma linha é
cronograma (duração só aparece como medida física); hardware exato. Toda medição abaixo foi feita no host
`wikijuridica` (`/opt/wiki`, usuário `rafael`) em 2026-09-24, só leitura e medição: nenhum serviço, unit,
drop-in ou modelo foi alterado, nenhum `ollama pull` rodou, nada foi reiniciado. Os comandos e as saídas
literais estão na §7. Os estudos em `docs/goal/enaeval/` são imutáveis (D-H): o objetivo novo F3.O0 mora
aqui e no `ESTADO` do EnaEval, não na `TASKLIST.md`.

---

## 1. O que existe hoje

### 1.1 O cérebro

| peça | onde | medido em 2026-09-24 |
|---|---|---|
| binário | `cmd/cerebro/main.go` (1.125 linhas) | cabeçalho `:1-16` ("daemon de IA local do portal (CLAUDE.md §12, DEC-058)"; nunca escreve em `public/`, `content/` ou `data/editorial/`); importa `portaljuridico/internal/ollama` (`:39`); `modeloEmbeddingsPadrao = "qwen3-embedding:0.6b"` (`:46`); extração em `qwen3.5:4b` (`:964`); `servir` cria `ollama.Novo(ollama.URLDoAmbiente())` (`:176`); flags de `servir` em `:150-166` — `--max-lote 3`, `--puxar-modelo-ausente=false`, `--publicar=false`. Nenhuma flag de GPU ou de VRAM |
| cliente | `internal/ollama/cliente.go` (598 linhas) | `URLPadrao = "http://127.0.0.1:11434"` (`:99`), `WIKI_OLLAMA_URL` (`:102`); `Residente` (`:345-368`) já lê `size_vram` e `context_length` como ponteiros (nil = não medido) e `SoCPU()` (`:374`) — o bloqueador §2.1 de `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` está fechado no código |
| unit do cérebro | `ops/systemd/wikijuridica-cerebro.service` | `ExecStart=/opt/wiki/bin/cerebro servir --root /opt/wiki --worker cerebro-1 --max-lote 3 --ocioso 30s --saude-a-cada 60s` (`:105`); `Wants=… ollama.service`; `active running` desde 16:09:32 -03, `NRestarts=0` |
| unit do Ollama | `/etc/systemd/system/ollama.service` + drop-in `ollama.service.d/wikijuridica-tuning.conf` → `/opt/wiki/ops/ollama/ollama.service.d/wikijuridica-tuning.conf` (versionado) | `ExecStart=/usr/local/bin/ollama serve`, `User=ollama`; `active running` desde 16:09:13 -03, `NRestarts=0`; `ollama version is 0.33.3` |
| ambiente vivo | `systemctl show ollama.service -p Environment` | `OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_NUM_PARALLEL=1 OLLAMA_KEEP_ALIVE=15m OLLAMA_CONTEXT_LENGTH=8192 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 OLLAMA_LLM_LIBRARY=cpu OLLAMA_NO_CLOUD=1`; no drop-in: `MemoryMax=12G`, `MemorySwapMax=2G`, `OOMScoreAdjust=800`, `CPUWeight=60`, `Nice=5`, `Slice=wikijuridica_alimentacao.slice` (`:29-36`, `:56`, `:61`, `:69-71`) |
| runners no disco | `/usr/local/lib/ollama/` | `cuda_v12` (`libcudart.so.12.8.90`, `libcublas.so.12.8.5.5`, `libggml-cuda.so` 418.116.128 B), `cuda_v13` (`libcudart.so.13.0.96`, `libcublas.so.13.1.1.3`, `libggml-cuda.so` 253.862.336 B), `vulkan/` e as variantes de CPU (entre elas `libggml-cpu-zen4.so`) |
| modelos | `ollama list` | nove: `wj-extracao-sonda`, `qwen3:4b`, `qwen3-embedding:4b`, `qwen3.5:4b`, `qwen3-embedding:0.6b`, `guoxuter/ov_intent_analysis_sft:v7_q8`, `qwen3.5:9b`, `qwen3-embedding:8b`, `qwen2.5-coder:14b` — nenhum é artefato do CANON |

**CPU-only, medido.** No boot o journal do Ollama registra
`msg="inference compute" id=cpu library=cpu … total="29.9 GiB"` e
`msg="vram-based default context" total_vram="0 B" default_num_ctx=4096`. Com modelo carregado:
`ollama ps` → `100% CPU`; `/api/ps` → `"size_vram":0`;
`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` → só o cabeçalho; GPU em
`1 MiB, 0 %`, `P8`.

**A placa já está pronta no nível do driver.** RTX 5060 Ti, 16.311 MiB, `compute_cap` 12.0, driver
580.178.04 com **NVIDIA UNIX Open Kernel Module** (`/proc/driver/nvidia/version`), `/dev/nvidia*` em
`crw-rw-rw-` (o usuário `ollama` alcança a placa sem grupo extra). O bloqueador §2.3 do
`IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` (módulo aberto; driver ≥ 570.26 para `cuda_v12`, ≥ 580.65.06 para
`cuda_v13`) está fechado no host, e a unit não isola dispositivo (`DevicePolicy=auto`, `PrivateDevices=no`,
nenhum `DeviceAllow` na unit nem na slice). **No que se mede no host, o único impedimento para o Ollama usar
a placa é a linha `OLLAMA_LLM_LIBRARY=cpu` do drop-in (`:35`).**

**Pausa manual e prazo dela.** `data/ops/cerebro_pausa_manual.json`, declarada em
2026-09-23T06:30:07-03:00 por `claude-fable-carga-transplante-20260923`, com
`"ate": "2026-10-07T23:59:59-03:00"`. Motivo, literal: *"carga transitoria antes do transplante do servidor: a
extracao de 105.524 acordaos pendentes a ~4,9 tok/s de eval levaria ~50 dias nesta CPU (qwen3.5:4b, 3,5
nucleos, 9,2 GB residentes, pacote a 95-97 C, NVMe a 83,8 C) e a GPU da maquina nova faz o mesmo 17,8x
mais rapido; o Ollama fica de pe para o buscar_semantico. Retirar este arquivo retoma; vencido, o gate
cerebro-saude fica vermelho de proposito."* Batimento (`data/ops/cerebro_batimento.json`,
2026-09-24T23:08:07Z): `estado` `pausado_a_pedido`, `pendentes` 105.512, `concluidas` 30.558, `erros` 0,
`pausada_desde` 2026-09-24T19:09:35Z (o boot pós-transplante). Pausa vencida nunca se auto-limpa
(`.claude/rules/fila-do-cerebro.md`).

**A premissa da pausa foi medida na CPU velha.** O "~4,9 tok/s de eval" é do notebook. Na CPU da torre,
hoje, com as requisições da §4.2 (§7.3): `qwen3.5:4b` decodifica a **15,78–16,22 tok/s** e faz prefill de
789 tokens a **198,8–207,2 tok/s**; `qwen3-embedding:0.6b` embute a **687,7–785,0 tok/s**. A série
`data/ops/ia_local_daily.jsonl` (10.320 linhas) termina em 2026-09-23T09:37:16Z, ainda no notebook
(`prompt_tok_s` 5,261, `eval_tok_s` 3,604): **nenhuma linha da série foi medida na torre**. O "17,8x" é a
afirmação da pausa contra a CPU velha; não foi re-medido.

**A guarda de RAM e o número dela.** `internal/cerebro/saude.go:203`: `TetoBytesResidentesPadrao int64 =
9 << 30` (9 GiB = 9.663.676.416 B). Soma o campo `size` de `/api/ps` (`bytesResidentes`, `:453`) e pausa o
worker acima do teto (`:294-298`). Justificativa (`:271-293`): o incidente de 2026-09-08 12:04:53 —
`qwen2.5-coder:14b` (9,9 GB) e `qwen3.5:9b` (6,1 GB) residentes, 16 GB num host de 19,4 GiB, RAM livre em
4,7%, earlyoom matando `llama-server` e os servidores MCP das sessões; o teto só faz sentido junto de
`OLLAMA_MAX_LOADED_MODELS=2` (`:290`). As âncoras são da árvore de trabalho: o arquivo tem 64 linhas
acrescentadas e não commitadas por outra frente desde 2026-09-17 ("pausa por estrato"; `git diff --numstat`,
§7.1), e quem executar o F3.O0 mexe nele por cima disso. O que a medição de hoje mostra sobre essa guarda:

| fato medido | número | consequência |
|---|---|---|
| `size` soma VRAM e RAM numa grandeza só (`IA_LOCAL…` §2.1) | — | com a placa em uso, a guarda contaria bytes de VRAM como RAM |
| `size` subestima a RAM real | `qwen3.5:4b` em CPU: `size` 3.227.894.413 B; `anon` do cgroup 4.637.728.768 B (**1,44×**); `VmRSS` do runner 4.530.708 kB | a grandeza que o earlyoom enxerga é `anon`, não `size` |
| `memory.current` do cgroup também não é RAM em risco | sem modelo nenhum: 3.763.707.904 B, dos quais `file` 3.744.858.112 B (99,5% page cache) e `anon` 13.029.376 B | ler `memory.current` pausaria por cache recuperável |
| o par do comentário `:201-202` ("0.6b + 4b = 3,87 GB") usa o blob do 0.6b | `/api/ps` hoje: `qwen3-embedding:0.6b` com `size` 2.417.491.967 B em contexto 8192 | o par soma 5,65 GB em `size`; ainda abaixo de 9 GiB, mas o número do comentário não é o que a guarda lê |

**O plano de GPU que já existe.** `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` (828 linhas, 2026-09-16,
frente P12 do plano do cérebro — `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md:3925`): quatro
bloqueadores (§2.1–§2.4), protocolo de migração (§7.2), gates 0/1/2 (§8), armadilha do reprocessamento
(§9), reversão (§10). Estado de cada bloqueador hoje: §2.1 fechado no código; §2.3 fechado no host; §2.2
aberto (guarda não re-derivada); §2.4 aberto — `ollama#18232` (RTX 5060 Ti 16 GB + Ollama 0.33.3 + runner
`cuda_v13`, falha em `cudaFuncSetAttribute`, contorno `num_ctx` 2048) segue **open** upstream, lida em
2026-09-24, e nunca foi testada na torre.

**Descrições do host velho que ficaram no disco.** `.claude/rules/ollama-e-earlyoom.md:15` ("Host: 19,4
GiB de RAM, 4 nucleos fisicos / 8 threads, sem GPU util (MX110 sem driver…") e o cabeçalho do drop-in
(`:1`, "em 19,4 GiB de RAM"). Não se tocam nesta ponte; entram como entregáveis de F3.O0 (§4).

### 1.2 A rede social

- **Código vivo:** `cmd/social/` (89 entradas), servido por `wikijuridica-social.service` (`active`,
  `127.0.0.1:8091`), com os pacotes `internal/social*` e afins (22 diretórios, §7.4).
- **Plano vivo:** `docs/goal/PLANO_REDE_SOCIAL.md` (2.434 linhas antes da nota desta ponte, 2.446 depois).
  Entregas em `content/redesocial_entregas.json`: **164** — 150 `entregue`, 11 `pendente`, 3 `suspenso` —,
  cobradas por `tools/check-redesocial-completude`. As fases do plano (F0, F0.5, F1…F6, FD, P0) **não** são as
  fases da TASKLIST (F0…F11): "F6" nomeia coisas diferentes nos dois documentos, e todo texto que citar uma
  delas qualifica de qual documento é.
- **A cláusula da linha 2240 está implementada e entregue:** entrega `F2-anti-abuso-camadas-2-a-6` (fase
  F2 do plano, `entregue`: "Quarentena de conta nova (7 dias e 3 posts, sem link externo), orcamento diario
  PERSISTIDO por conta, reputacao que nunc[a…]"); tipo `Reputacao` em `internal/socialpolicy/policy.go:122-132`
  com `ExibidaPublicamente` (`:131`); o validador `social_policy_reputacao_exibida` (`:749-756`, mensagem
  *"reputacao exibida publicamente vira ranking de advogado, contra o Provimento CFOAB 205/2021 art. 5o"*);
  `content/social_policy.json:109` → `"exibida_publicamente": false`; cobrança em
  `internal/socialpolicy/policy_test.go:204`, `internal/socialantiabuso/camadas_test.go:167` e no gate
  `social-policy` (`internal/checks/checks.go:517`, `case` em `:1981`).
- **Agente de IA na rede de hoje só lê.** O anel 2 do `REDE_SOCIAL_DE_IA_RASCUNHO.md:566` (agente
  credenciado que escreve) não existe no código: `rg -n 'redesocial:comentar' -g '*.go' .` → exit 1;
  `rg -n -i client_id cmd/social/` → exit 1. O cérebro é o anel 1 (socket Unix + HMAC, "construído e
  desligado", `:565`).

---

## 2. O que o CANON manda

### 2.1 F3 — o motor

- **Serving:** vLLM 0.29.0 + FlashInfer 0.6.14 em sm_120 (`CANON-v4.1.md:371`). No host: vLLM 0.28.0 e
  FlashInfer 0.6.16.post3 em `/opt/wiki/.venv-tools311` (S3, `2026-09-24-enaeval-host-e-runtime.md` §2).
- **Modelo:** `wj-llm-8b` (Qwen3-8B, Apache-2.0) servido em NVFP4 compactado, **4,90 GB (4,56 GiB)**
  (`:241`), pela receita que parte de `nvidia/Qwen3-8B-NVFP4` (`:257-259`).
- **Mapa de VRAM (`:212-215`):** residentes (`wj-llm-8b` + `wj-nli-54M` + reranker + auxiliares) + **KV 5,00
  GiB = 124.830 tokens** + **lote 2,80 GiB** = **15,23 GiB ≤ 15,3 alvo**.
- **RAM (`:125-143`):** fecha em 32.768 MiB; comprometido 25.854 MiB; disponível para userspace + page
  cache 30.734 MiB; **envelope arrendável 6.656 MiB, um locatário por vez** (professor P0, LightGBM, OCR,
  embeddings, QLoRA, BitNet em failover, TTS); **D-10': RAM nova entra no envelope, nunca como residente**
  (`DECISOES-ORQUESTRADOR.md:83-94`).
- **Egresso zero em três camadas** (`:310-314`) e soberania S1–S6 (`:316-319`).
- **F3.O1** (`TASKLIST.md:603-623`): KLD ≤ 10⁻³ contra `nvidia/Qwen3-8B-NVFP4`, TTFT p95 < 500 ms em c = 16,
  `comp.EgressProbe` com 0 conexões em 24 h, VRAM ≤ 15,23 GiB; depende de F0.O7; recurso GPU, perfil
  `construcao` (ligado na abertura da F3, `:597-601`).
- **Embedding do EnaEval:** `wj-emb-query` = Qwen3-Embedding-0.6B em ONNX int8, 0,55 GB (`:246`) — o mesmo
  modelo-base do `qwen3-embedding:0.6b` do cérebro, em outro formato e outro serving.
- **Nenhuma linha do CANON cita Ollama**, nem o §16 (revogado): a coexistência é matéria desta ponte.

### 2.2 F6 — rede social viva e arena

- **Debate é um produto com dois perfis de custo** (`:166-169`, `:658-664`; D-10').
- **Quatro personas, quatro pubkeys, `rep_wjr` visíveis externamente** (`:57-61`, `:678-681`); o emissor de
  chaves e recibos é a **PJ**, `did:web:wikijuridica.com.br`, "nunca a PF" (`:55`).
- **Reputação = riqueza** (`:650`); **MeritRank** com α = 0,40, β = 0,60 (`:676`); **WJR intransferível**
  (`:694`); **zero primitivo social** — nem curtida, nem seguidor, nem comentário solto (`:648`).
- **Leaderboard público:** F6.O1 só fica pronto com "leaderboard com as 4 personas" (`TASKLIST.md:826-827`);
  o fluxo S3 retrospectivo "nunca pontua leaderboard" (`:652`).
- **O que fica fora:** Res. CNJ 615/2025 art. 10 II/III — **zero `judge_id`**, e `/predict` "nunca devolve
  ranking de vara, só distribuição do foro" (`:642`); pseudonimização sem nº CNJ, nomes, OAB, juiz ou comarca
  (`:653`).

---

## 3. Decisão D-D — convivência até F3.O1

**O que a decisão diz** (chefe, barramento da onda): *"O cérebro (Ollama, CPU) não é o EnaEval nem vira:
mantém o plano próprio até F3.O1 trocar o backend de LLM. Objetivo novo, F3.O0 — Ollama na GPU (…),
locatário transitório que sai quando F3.O1 pousa."*

**Por que são dois sistemas.** Nenhum `.go` do repositório referencia vLLM (`rg -ln 'vllm|vLLM' -g '*.go'
internal cmd` → 0, S1); o cérebro é alimentação — embeddings do acervo, extração de dispositivos das ementas
do STJ, comentário e notícia autorais —, com fila, gates e série de medição próprios; o EnaEval é serving,
verificador e treino (CANON §3–§4). O que os liga é a placa: os dois querem a mesma VRAM, e a ordem entre
eles é o que esta seção fixa.

**O plano próprio do cérebro** continua sendo `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` (nota de
2026-09-24 na linha 3, ponteiro para cá), com o placar em `docs/goal/ESTADO.md` e o runbook de GPU em
`docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md`. Retirar a pausa manual é ato desse plano, não desta ponte.

**O que "sai quando F3.O1 pousar" quer dizer na operação:**

1. **O primeiro passo de F3.O1 que mede na GPU** (KLD, TTFT em c = 16, mapa de 15,23 GiB) começa devolvendo
   o Ollama à CPU: drop-in com `OLLAMA_LLM_LIBRARY=cpu` e sem `OLLAMA_GPU_OVERHEAD`. F3.O1 não mede com
   locatário na placa. É o mesmo movimento que o Pronto de F3.O0 prova (item 8), então a saída já chega
   testada.
2. **A geração do cérebro** (extração, comentário, notícia) passa a ser servida pelo serving do F3.O1 e entra
   na fila sob **nome de modelo novo**. A identidade da tarefa inclui o modelo (`internal/cerebro/fila.go`;
   `.claude/rules/fila-do-cerebro.md`), então nada se mistura com o que o `qwen3.5:4b` já extraiu: a
   comparação é o Gate 2 pareado por chave (`tools/generate-comparacao-modelos-extracao`;
   `IA_LOCAL…` §8 e §9), e a adoção segue a régua pré-registrada de lá (âncora literal em 100,0000%,
   `dispositivos_por_acordao`, `descarte_pct`).
3. **O embedding de consulta** (`buscar_semantico`) segue no Ollama em CPU com `qwen3-embedding:0.6b`,
   medido hoje a 687,7–785,0 tok/s na CPU da torre. A troca por `wj-emb-query` é índice novo por modelo e
   passa pelo `cerebro ativar` (flags em `cmd/cerebro/main.go:754-755`), mecanismo que já existe.
4. **A classe do cérebro no escalonador** é decisão de F3.O3 (`wj/serve`, `wj-memd`). Até lá, o cérebro
   nunca fica à frente de classe que o CANON §3 ordena (pago > answer unit > treino > OCR > mídia,
   `CANON-v4.1.md:205-207`).

**O que sobrevive à troca** (não se reescreve, não se apaga): o pipeline STJ
(`cerebro enfileirar-extracoes --dir data/corpus/jurisprudencia/stj-espelhos`, `main.go:963`); a fila
`data/ai/fila.sqlite` com a cura por causa, lease e lápides; os gates `tools/check-cerebro-vivo`,
`tools/check-cerebro-batimento`, `tools/check-extracao-do-cerebro`, `tools/check-extracoes-dispositivos`,
`internal/checks/cerebro_batimento_gate_test.go` e `internal/checks/cerebro_extracao_gate.go`; as extrações e
propostas append-only em `data/ai/`; o índice de embeddings em `data/ai/embeddings/` e o `cerebro ativar`; a
série `data/ops/ia_local_daily.jsonl` (mesmo esquema: tokens de entrada e saída e tempo de parede por
chamada); a pausa declarada e o batimento; a régua dos gates 0/1/2.

**O que F3.O1 substitui:** o backend de geração do cérebro (`internal/ollama`, `Gerar`) pelo serving do
F3.O1; os modelos de geração (`qwen3.5:4b`, `wj-extracao-sonda`) por `wj-llm-8b`, sob nome novo na fila; a
ocupação da GPU pelo Ollama (F3.O0 termina); a conta de VRAM da guarda (o teto volta a 0, sem GPU
declarada). A arbitragem de GPU e do envelope de RAM passa ao escalonador de F3.O3.

---

## 4. Objetivo F3.O0 — Ollama na GPU

Objetivo novo por D-D, no formato da TASKLIST §3 (`TASKLIST.md:149-156`). Não altera nenhum critério de
F3.O1–F3.O4.

#### F3.O0 — Ollama na GPU: locatário transitório até F3.O1

**Resultado:** o cérebro volta a ter para onde crescer sem encostar no que o EnaEval vai ocupar — o Ollama
roda na RTX 5060 Ti dentro da fatia do mapa de VRAM que só ganha dono com F3.O1, a guarda mede VRAM e RAM
em contas separadas e na grandeza certa, e o motivo técnico declarado na pausa manual (a CPU) deixa de
existir.

**Pronto** (cada item é comando com saída esperada; antes/depois colados no `LEDGER` do EnaEval, TASKLIST
§0.3 d):
1. `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` **lista o processo do
   Ollama** (o runner filho de `ollama serve`) com `used_memory` > 0 enquanto `qwen3-embedding:0.6b` e
   `qwen3.5:4b` estão carregados — hoje devolve só o cabeçalho (§7.1). `ollama ps` → `100% GPU` nos dois,
   com `CONTEXT` igual ao `OLLAMA_CONTEXT_LENGTH` do drop-in; `curl -s 127.0.0.1:11434/api/ps` →
   `size_vram` > 0 em cada residente.
2. A linha `msg="inference compute"` do journal do `ollama.service` deixa de ser `id=cpu library=cpu` (§7.1)
   e nomeia a RTX 5060 Ti com `cuda_v12` entre as bibliotecas.
3. **tok/s antes e depois, com as mesmas requisições da §4.2**, na mesma sessão — antes com
   `OLLAMA_LLM_LIBRARY=cpu`, depois com `cuda_v12`, mesmos digests (`ac6da0dfba84…`, `2a654d98e6fb…`) e
   mesmas `options`: `qwen3-embedding:0.6b` por `/api/embed` = `prompt_eval_count ÷ (total_duration −
   load_duration) × 10⁹` (a resposta de embed não traz `eval_*`; `/api/generate` não serve modelo de
   embedding); `qwen3.5:4b` por `/api/generate` = `eval_count ÷ eval_duration × 10⁹` (fórmula da
   documentação oficial) e `prompt_eval_count ÷ prompt_eval_duration × 10⁹`. Passa quando **depois > antes**
   nos três números, rodada a rodada, com `cat /proc/loadavg` ao lado de cada série. Referência medida hoje
   em CPU (§7.3): embed 687,7–785,0 tok/s; decode 15,78–16,22 tok/s; prefill de 789 tokens 198,8–207,2 tok/s.
4. **`#18232` testado:** com `OLLAMA_CONTEXT_LENGTH=8192` e `OLLAMA_FLASH_ATTENTION=1`, as requisições da
   §4.2 — inclusive a de prompt acima de 2.048 tokens — completam, e
   `journalctl -u ollama --since <troca> | rg -c cudaFuncSetAttribute` → `0`. Reprovando em 8192, o
   objetivo se divide (TASKLIST §0.3): F3.O0 fecha
   em contexto 2048 com `TetoCharsExtracao` parado (`IA_LOCAL…` §2.4), e "contexto 8192 na GPU" vira objetivo
   próprio com o `#18232` como insumo.
5. **Guarda re-derivada para os 29 GiB do host e para a VRAM**, em `internal/cerebro/saude.go`, com a
   derivação da §4.1 no comentário: conta de VRAM `Σ size_vram` de `/api/ps` ≤ `teto_vram`, com `teto_vram
   ≤ 12,43 GiB`; conta de RAM `anon` de `memory.stat` do cgroup `wikijuridica_alimentacao.slice/ollama.service`
   ≤ `teto_ram`, com `teto_ram ≤ 6.656 MiB` e `teto_ram < MemoryMax` do drop-in; o comentário cita `MemTotal`
   medido (30.649 MiB). `size_vram = 0` só vira pausa ("fallback total para CPU") quando há GPU declarada
   (`teto_vram > 0`, flag nova de `cerebro servir`), nunca pelo valor do campo sozinho.
   `tools/check-load-headroom --max 12 && ./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./internal/cerebro/`
   → `ok`, com casos que provam: `size` somando acima de 9 GiB com `anon` abaixo do teto **não** pausa; `anon` acima do
   teto pausa; `Σ size_vram` acima do teto pausa; GPU declarada + `size_vram = 0` pausa com diagnóstico
   nomeado; sem GPU declarada + `size_vram = 0` não pausa.
6. **Drop-in atualizado com as variáveis documentadas pelo Ollama** (fonte oficial em cada linha do
   comentário — `ollama serve --help` do 0.33.3 e `envconfig/config.go` na tag v0.33.3, §7.2):
   `OLLAMA_LLM_LIBRARY=cuda_v12`; `OLLAMA_GPU_OVERHEAD` = `memory.total − teto_vram` em bytes (§4.1);
   `OLLAMA_CONTEXT_LENGTH` explícito (o padrão do 0.33.3 é "4k/32k/256k based on VRAM"); `OLLAMA_FLASH_ATTENTION=1`
   junto de `OLLAMA_KV_CACHE_TYPE=q8_0`; `OLLAMA_MAX_LOADED_MODELS` (agora "per GPU"), `OLLAMA_NUM_PARALLEL` e
   `OLLAMA_KEEP_ALIVE` re-derivados do `load_duration` medido; `OLLAMA_IGPU_ENABLE` ausente. Valores superados
   ficam no comentário com data e motivo. `systemctl show ollama.service -p Environment` → os valores novos.
7. **Teto respeitado na placa:** com o par que o cérebro alterna carregado, `used_memory` do processo do
   Ollama em `nvidia-smi --query-compute-apps` ≤ `teto_vram` e `Σ size_vram` ≤ `teto_vram`. Se o runner
   passar, `LLAMA_ARG_FIT_TARGET` (MiB) entra com a mesma margem do `OLLAMA_GPU_OVERHEAD` e a medição se
   repete.
8. **Saída provada:** `OLLAMA_LLM_LIBRARY=cpu` restaurado uma vez → com modelo carregado,
   `--query-compute-apps` volta a devolver só o cabeçalho e `ollama ps` volta a `100% CPU`; volta a `cuda_v12`
   e o item 1 passa de novo.

**Insumos:** `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` (§2.1–§2.4, §3.2, §3.5, §5, §7.2, §8–§10, §12) ·
`docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` §P12 (`:3925`; `cuda_v12` em `:4012`; `#18232` em `:4015`) ·
`ops/ollama/ollama.service.d/wikijuridica-tuning.conf` (`:29-36`, `:56`, `:61`, `:69-71`) ·
`ops/systemd/wikijuridica-cerebro.service` (`:105`) · `internal/cerebro/saude.go` (`:103-107`, `:201-203`,
`:256-298`, `:444-463`) · `internal/ollama/cliente.go` (`:345-379`) · `cmd/cerebro/main.go` (`:147-176`,
`:528-537`) · `tools/generate-comparacao-modelos-extracao`, `tools/check-extracoes-dispositivos`,
`tools/generate-medicao-runner-local`, `tools/check-cerebro-vivo`, `tools/check-load-headroom` ·
`/usr/local/lib/ollama/{cuda_v12,cuda_v13}` e `/usr/local/bin/ollama` (0.33.3) ·
`data/ops/cerebro_pausa_manual.json`, `data/ops/cerebro_batimento.json`, `data/ops/ia_local_daily.jsonl` ·
`CANON-v4.1.md` §3 (`:125-143`, `:212-215`) e D-10' · documentação oficial da §7.2.

**Entregáveis:** `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` · `internal/cerebro/saude.go` e o teste
da guarda em `internal/cerebro/` · `cmd/cerebro/main.go` (flag do teto de VRAM; 0 = sem GPU declarada) e o
`ExecStart` de `ops/systemd/wikijuridica-cerebro.service` · `.claude/rules/ollama-e-earlyoom.md:15` (linha do
host com a medição da torre; T1 ≤ 6.000 caracteres, hoje 5.372) · antes/depois no `LEDGER` do EnaEval.
**Depende:** — . **Recurso:** GPU transitório — no máximo a fatia do mapa de VRAM sem dono antes de F3.O1
(§4.1); sai quando F3.O1 pousar (§3). **Dono:** nenhuma.
- [ ] **[A]** Drop-in: `OLLAMA_LLM_LIBRARY=cpu` → `cuda_v12`, nunca vazio — `cuda_v13` é PTX puro e paga JIT a
      cada carga (`IA_LOCAL…` §2.3) — mais `OLLAMA_GPU_OVERHEAD` e contexto explícito.
- [ ] **[E]** Medir antes (CPU) e depois (GPU) com as requisições da §4.2, na mesma sessão.
- [ ] **[E]** Testar `#18232` sob `cuda_v12` com contexto 8192 e flash attention ligado.
- [ ] **[A]** Guarda em duas contas, flag do teto de VRAM e comentário com a derivação — **antes** de o
      cérebro voltar a trabalhar (`IA_LOCAL…` §7.2, passo 5).
- [ ] **[E]** Provar a saída para `cpu` uma vez e voltar.
- [ ] **[A]** Regra `ollama-e-earlyoom.md` com o host medido na torre.
**Goal:** *"Objetivo F3.O0. Leia `docs/goal/enaeval/PONTE_CEREBRO_E_REDE_SOCIAL.md` §1, §3 e §4,
`docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` §2 e §7.2, `CANON-v4.1.md` §3 (mapa de VRAM e envelope de
RAM), o drop-in `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` e `internal/cerebro/saude.go`. Troque a
biblioteca do Ollama de `cpu` para `cuda_v12`, meça antes e depois com as requisições fixas da ponte, teste o
`#18232` com contexto 8192, re-derive a guarda em duas contas — VRAM até 12,43 GiB, a fatia do mapa que só
ganha dono com F3.O1; RAM pelo `anon` do cgroup até 6.656 MiB, o envelope do CANON — e prove a volta para
`cpu`. Pronto quando `nvidia-smi` listar o processo do Ollama, os tok/s na GPU superarem os da CPU nas mesmas
requisições, o journal não tiver `cudaFuncSetAttribute`, os testes da guarda passarem e a volta para `cpu`
estiver medida. O Ollama sai da GPU quando F3.O1 pousar."*

### 4.1 Os dois tetos, derivados

**VRAM.** O mapa do CANON (`CANON-v4.1.md:212-215`) é residentes + KV 5,00 GiB + lote 2,80 GiB = 15,23 GiB ≤
15,3. Residentes e KV são entregáveis de F3.O1 e F3.O2: antes deles, não têm dono. O lote pode ter dono antes
— a fase F2 declara "GPU leve" (`TASKLIST.md:452`) e F2.O2 "GPU de pico 4.000/dia, classe 4 preemptível"
(`:488-489`). O que o CANON deixa livre antes de F3.O1 é, portanto, a fatia residentes + KV:

```
teto_vram ≤ 15,23 − 2,80 = 12,43 GiB = 12.728 MiB
OLLAMA_GPU_OVERHEAD = memory.total − teto_vram = (16.311 − 12.728) MiB = 3.583 MiB = 3.757.047.808 B
```

O par que o cérebro alterna soma hoje, em `size` de `/api/ps` e em CPU, 2.417.491.967 + 3.227.894.413 =
5.645.386.380 B (5,26 GiB): cabe com folga. A medição em VRAM (item 7 do Pronto) substitui esta conta.

**RAM.** `MemTotal` medido: 30.649 MiB (`free -m`), contra 30.734 MiB que o CANON dá como disponível para
userspace + page cache (`CANON-v4.1.md:132`) — diferença de 85 MiB (0,28%): o plano de RAM do CANON vale para
esta máquina como medida. Nele, RAM fora do orçamento residente entra no envelope arrendável, um locatário por
vez (`:133`, `:137`, `:139-143`, D-10'). O Ollama do cérebro não está no orçamento residente do CANON; logo é
locatário do envelope:

```
teto_ram ≤ 6.656 MiB, medido como `anon` de memory.stat do cgroup wikijuridica_alimentacao.slice/ollama.service
invariante: teto_ram < MemoryMax do drop-in (hoje 12G = 12.884.901.888 B) — a guarda pausa antes de o kernel matar
```

`size` não serve para esta conta (subestima 1,44× na torre) e `memory.current` também não (99,5% page cache
sem modelo algum) — §1.1 e §7.1. Em CPU o `qwen3.5:4b` sozinho mede 4.637.728.768 B de `anon` (4.423 MiB),
dentro do teto; com os pesos na placa, a parcela em RAM cai. Até F3.O3 não existe `wj-memd` arbitrando o
envelope: quem garante o teto é esta guarda.

### 4.2 As requisições fixas de medição

Prefixo `[i]` diferente em cada rodada de propósito: com a mesma entrada repetida, o cache de prompt devolve
7.508–7.880 "tok/s" de embed (§7.3) e mede a coisa ao lado. Texto `T` (sem acento, como foi enviado):

```
A coisa julgada material torna imutavel e indiscutivel a decisao de merito nao mais sujeita a recurso, nos termos do art. 502 do Codigo de Processo Civil. A decisao que julgar total ou parcialmente o merito tem forca de lei nos limites da questao principal expressamente decidida, conforme o art. 503. Nao fazem coisa julgada os motivos, ainda que importantes para determinar o alcance da parte dispositiva da sentenca, nem a verdade dos fatos, estabelecida como fundamento da sentenca, segundo o art. 504. Nenhum juiz decidira novamente as questoes ja decididas relativas a mesma lide, salvo nas hipoteses do art. 505. A sentenca faz coisa julgada as partes entre as quais e dada, nao prejudicando terceiros, nos termos do art. 506.
```

| requisição | endpoint | corpo (Python sobre `T`, `P`, `Q`) | rodadas |
|---|---|---|---|
| E — embed | `/api/embed` | `{"model":"qwen3-embedding:0.6b","input":"["+i+"] "+T,"keep_alive":"60s"}` | i = 1…4 |
| G1 — curta | `/api/generate` | `{"model":"qwen3.5:4b","prompt":"["+i+"] "+P,"stream":false,"think":false,"keep_alive":"60s","options":{"temperature":0,"seed":42,"num_predict":128,"num_ctx":8192}}` | i = 1…4 |
| G2 — longa (789 tokens) | `/api/generate` | `{"model":"qwen3.5:4b","prompt":"["+i+"] "+"\n\n".join([T]*4)+"\n\n"+Q,"stream":false,"think":false,"keep_alive":"60s","options":{"temperature":0,"seed":42,"num_predict":64,"num_ctx":8192}}` | i = 1…3 |
| G3 — acima de 2.048 tokens (só para o `#18232`) | `/api/generate` | igual a G2 com `[T]*16` | i = 1 |

`P` = `Resuma em cinco frases, em portugues, o regime da coisa julgada nos arts. 502 a 508 do Codigo de Processo Civil.` ·
`Q` = `Pergunta: qual artigo do texto acima trata dos limites subjetivos da coisa julgada? Responda em uma frase.`
O laço exato que produziu a referência de hoje está na §7.3.

---

## 5. Decisão D-E — reputação

**A cláusula, literal** (`docs/goal/PLANO_REDE_SOCIAL.md:2240-2242`, §15.4 "Anti-abuso sem CAPTCHA de
terceiro"):

> 4. **Reputação** como regulador interno, **nunca exibida como ranking** — placar público
>    esbarra no Prov. 205 art. 5º e na linha `ordenacao_por_conversao` de §10.1. Destrava link
>    externo (≥5), DM a desconhecido (≥10), abrir thread (≥20).

**Leitura, pelo que está no disco.** O objeto da cláusula é a **conta humana** da rede:

1. O contexto é a lista de travas de **conta** do §15.4 — quarentena de conta nova (`:2232`), limite por
   conta (`:2237`), e-mail verificado (`:2261`), `contas.papel` e selo de OAB (`:2280`), SSE por conta
   (`:2287`); linhas depois da nota desta ponte — e as três destravas da própria cláusula (link externo,
   DM, thread) são atos de conta.
2. O fundamento é o Prov. 205 art. 5º, que o próprio plano lê como *"mata destaque pago e ranking pago de
   advogado"* (`:218-219`) e classifica como analogia que "mira anuário e prêmio editorial" (`:1100`); a
   segunda base, `ordenacao_por_conversao`, é boa prática do CED art. 39 (`:1102`). Advogado é pessoa.
3. O código diz o mesmo: *"reputacao exibida publicamente vira ranking de advogado"*
   (`internal/socialpolicy/policy.go:749-756`); a entrega é `F2-anti-abuso-camadas-2-a-6`, "por conta".
4. Reputação de agente de IA foi deixada **em aberto** pelo plano de rede social de IA: *"a reputação da rede
   social hoje é por conta (…). Um `client_id` de agente não é uma pessoa e a mesma organização pode ter mil.
   A régua tem de ser escrita antes: reputação por `client_id`, por organização declarada, ou por
   verificabilidade do que a peça cita (…). Isto é escolha do próximo executor, não deste rascunho."*
   (`docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:573-578`). E nenhum agente de IA escreve na rede hoje (§1.2).

**Veredito:** a linha 2240 **não abrange agente de IA**. Convivem: a cláusula segue em vigor para a
reputação por conta humana, e a F6 da TASKLIST executa como escrita — `rep_wjr` e MeritRank públicos para as
quatro personas do EnaEval e para agentes externos fecham exatamente a decisão que o rascunho deixou aberta.
A nota datada aplicada no plano (`PLANO_REDE_SOCIAL.md:2244`, §7.5) é de **convivência**, não de superação.
Precisão sobre o texto do barramento: o objeto da cláusula é a conta humana — advogado antes de todos —, não
"juiz, vara"; juiz e vara ficam fora de ranking por outra norma (abaixo). A conclusão é a mesma.

**O que a F6 herda do plano vivo** (cada linha é verificável):
- `rep_wjr` e MeritRank moram na tabela `agent` do `SCHEMA-v4.1` (F0.O5), nunca na escada `.reputacao` de
  `cmd/social`; o gate `social-policy` continua verde com `"exibida_publicamente": false`.
- A persona `advogado` do EnaEval é papel no debate, com chave da PJ (`CANON-v4.1.md:55`): nunca nome, número
  de OAB ou assinatura de pessoa física.
- Conta humana da rede, a do dono inclusive, nunca entra no leaderboard da F6.
- "F6" do plano de rede social ≠ "F6" da TASKLIST; todo texto novo qualifica.

**Fora nos dois regimes:** ranking de vara ou de juiz, `judge_id` e qualquer placar de magistrado — Res. CNJ
615/2025 art. 10 II/III, que o CANON executa com "zero `judge_id`" e `/predict` sem ranking de vara
(`CANON-v4.1.md:642`).

---

## 6. O que não muda

- `CANON-v4.1.md`, `TASKLIST.md` e `DECISOES-ORQUESTRADOR.md` (imutáveis por D-H; SHA-256 conferidos na §7.5):
  F3.O0 não entra neles.
- Os critérios de F3.O1–F3.O4 (VRAM ≤ 15,23 GiB, KLD ≤ 10⁻³, TTFT p95 < 500 ms em c = 16, egresso zero) e de
  F6.O1–F6.O4 (leaderboard, 4 pubkeys, MeritRank, payout só por Plano-T).
- A cláusula `PLANO_REDE_SOCIAL.md:2240` para conta humana, o validador `social_policy_reputacao_exibida` e
  `content/social_policy.json:109`.
- O plano do cérebro, o `IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` e a DEC-058; a pausa manual (`ate`
  2026-10-07T23:59:59-03:00) — esta ponte não a retira.
- Nenhum serviço, unit, drop-in ou modelo foi alterado por esta ponte: `ollama.service` e
  `wikijuridica-cerebro.service` seguem com `NRestarts=0`, o drop-in segue com `OLLAMA_LLM_LIBRARY=cpu`, e
  `ollama ps` voltou a vazio depois da medição (§7.3).
- O bloco canônico do `CLAUDE.md` e as regras de `.claude/` (a linha do host em
  `ollama-e-earlyoom.md` é entregável de F3.O0, não desta ponte).

---

## 7. Evidência

Host `wikijuridica`, via Desktop Commander, cwd `/opt/wiki`. Saídas literais; `…` marca trecho omitido.

### 7.1 Host, Ollama e cérebro

```
$ whoami && pwd && date -Iseconds && hostname
rafael
/opt/wiki
2026-09-24T20:00:35-03:00
wikijuridica

$ systemctl cat ollama
# /etc/systemd/system/ollama.service
…
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
…
# /etc/systemd/system/ollama.service.d/wikijuridica-tuning.conf -> /opt/wiki/ops/ollama/ollama.service.d/wikijuridica-tuning.conf
# WikiJuridica — tuning do Ollama para conviver com nginx + Go + Claude Code em 19,4 GiB de RAM.
…
ConditionPathExists=/usr/local/bin/ollama
…
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_KEEP_ALIVE=15m"
Environment="OLLAMA_CONTEXT_LENGTH=8192"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_LLM_LIBRARY=cpu"
Environment="OLLAMA_NO_CLOUD=1"
…
OOMScoreAdjust=800
…
Slice=wikijuridica_alimentacao.slice
…
MemoryMax=12G
MemorySwapMax=2G
CPUWeight=60
IOWeight=60
Nice=5
--- exit=0

$ systemctl show ollama.service -p ActiveState -p SubState -p NRestarts -p ActiveEnterTimestamp -p MemoryCurrent -p MemoryMax -p MainPID -p UnitFileState -p Environment
ActiveState=active
SubState=running
UnitFileState=enabled
ActiveEnterTimestamp=Thu 2026-09-24 16:09:13 -03
MainPID=2549
NRestarts=0
MemoryCurrent=3763707904
MemoryMax=12884901888
Environment=PATH=/home/rafael/.npm-global/bin:… OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_NUM_PARALLEL=1 OLLAMA_KEEP_ALIVE=15m OLLAMA_CONTEXT_LENGTH=8192 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 OLLAMA_LLM_LIBRARY=cpu OLLAMA_NO_CLOUD=1

$ systemctl show wikijuridica-cerebro.service -p ActiveState -p SubState -p NRestarts -p ActiveEnterTimestamp -p MemoryCurrent -p MainPID -p UnitFileState -p Wants -p After
Wants=-.mount tmp.mount ollama.service
After=network-online.target wikijuridica_alimentacao.slice … ollama.service basic.target tmp.mount
ActiveState=active
SubState=running
UnitFileState=enabled
ActiveEnterTimestamp=Thu 2026-09-24 16:09:32 -03
MainPID=6955
NRestarts=0
MemoryCurrent=643694592

$ rg -n 'ExecStart=' ops/systemd/wikijuridica-cerebro.service
105:ExecStart=/opt/wiki/bin/cerebro servir --root /opt/wiki --worker cerebro-1 --max-lote 3 --ocioso 30s --saude-a-cada 60s

$ ollama --version
ollama version is 0.33.3

$ ls -la /usr/local/lib/ollama/cuda_v12/ /usr/local/lib/ollama/cuda_v13/
--- cuda_v12
total 1256868
drwxr-xr-x 2 root root      4096 Sep  2 14:01 .
drwxr-xr-x 5 root root      4096 Sep  7 16:33 ..
lrwxrwxrwx 1 root root        21 Sep  2 14:01 libcublas.so.12 -> libcublas.so.12.8.5.5
-rwxr-xr-x 1 root root 116388640 Jul  7  2015 libcublas.so.12.8.5.5
lrwxrwxrwx 1 root root        23 Sep  2 14:01 libcublasLt.so.12 -> libcublasLt.so.12.8.5.5
-rwxr-xr-x 1 root root 751775824 Jul  7  2015 libcublasLt.so.12.8.5.5
lrwxrwxrwx 1 root root        20 Sep  2 14:01 libcudart.so.12 -> libcudart.so.12.8.90
-rwxr-xr-x 1 root root    728800 Jul  7  2015 libcudart.so.12.8.90
-rwxr-xr-x 1 root root 418116128 Sep  2 14:01 libggml-cuda.so
--- cuda_v13
total 830444
drwxr-xr-x 2 root root      4096 Sep  2 13:59 .
drwxr-xr-x 5 root root      4096 Sep  7 16:33 ..
lrwxrwxrwx 1 root root        21 Sep  2 13:59 libcublas.so.13 -> libcublas.so.13.1.1.3
-rwxr-xr-x 1 root root  54177976 Jul  7  2015 libcublas.so.13.1.1.3
lrwxrwxrwx 1 root root        23 Sep  2 13:59 libcublasLt.so.13 -> libcublasLt.so.13.1.1.3
-rwxr-xr-x 1 root root 541607888 Jul  7  2015 libcublasLt.so.13.1.1.3
lrwxrwxrwx 1 root root        20 Sep  2 13:59 libcudart.so.13 -> libcudart.so.13.0.96
-rwxr-xr-x 1 root root    704288 Jul  7  2015 libcudart.so.13.0.96
-rwxr-xr-x 1 root root 253862336 Sep  2 13:59 libggml-cuda.so
(em /usr/local/lib/ollama/ também: vulkan/, libggml-cpu-{alderlake,…,zen4}.so, llama-server, llama-quantize, libllama*.so)

$ nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version,compute_cap,pstate --format=csv
name, memory.total [MiB], memory.used [MiB], utilization.gpu [%], driver_version, compute_cap, pstate
NVIDIA GeForce RTX 5060 Ti, 16311 MiB, 1 MiB, 0 %, 580.178.04, 12.0, P8

$ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
pid, process_name, used_gpu_memory [MiB]

$ cat /proc/driver/nvidia/version
NVRM version: NVIDIA UNIX Open Kernel Module for x86_64  580.178.04  Release Build  (dvs-builder@U22-I3-AE18-16-4)  Tue Jul  7 12:18:12 UTC 2026

$ ls -la /dev/nvidia*
crw-rw-rw- 1 root root 195, 254 Sep 24 16:09 /dev/nvidia-modeset
crw-rw-rw- 1 root root 508,   0 Sep 24 16:09 /dev/nvidia-uvm
crw-rw-rw- 1 root root 508,   1 Sep 24 16:09 /dev/nvidia-uvm-tools
crw-rw-rw- 1 root root 195,   0 Sep 24 16:09 /dev/nvidia0
crw-rw-rw- 1 root root 195, 255 Sep 24 16:09 /dev/nvidiactl
…

$ systemctl show ollama.service -p DevicePolicy -p PrivateDevices -p DeviceAllow -p ProtectKernelModules -p NoNewPrivileges; systemctl show wikijuridica_alimentacao.slice -p DevicePolicy -p DeviceAllow; id ollama
DevicePolicy=auto
PrivateDevices=no
ProtectKernelModules=no
NoNewPrivileges=no
DevicePolicy=auto
uid=995(ollama) gid=978(ollama) groups=978(ollama)

$ journalctl -u ollama --since '2026-09-24 16:09' --no-pager | rg -i 'inference compute|library|compute|gpu|vram|cuda|looking for compatible|discover' | head -12   # 1ª linha
Sep 24 16:09:13 wikijuridica ollama[2549]: time=2026-09-24T16:09:13.196-03:00 level=INFO source=routes.go:1955 msg="server config" env="map[CUDA_VISIBLE_DEVICES: GGML_VK_VISIBLE_DEVICES: … LLAMA_ARG_FIT: LLAMA_ARG_FIT_TARGET: … OLLAMA_CONTEXT_LENGTH:8192 OLLAMA_DEBUG:INFO … OLLAMA_FLASH_ATTENTION:true OLLAMA_GO_TEMPLATE:true OLLAMA_GPU_OVERHEAD:0 OLLAMA_HOST:http://127.0.0.1:11434 OLLAMA_IGPU_ENABLE: OLLAMA_KEEP_ALIVE:15m0s OLLAMA_KV_CACHE_TYPE:q8_0 OLLAMA_LLM_LIBRARY:cpu OLLAMA_LOAD_TIMEOUT:5m0s OLLAMA_MAX_LOADED_MODELS:2 OLLAMA_MAX_QUEUE:512 … OLLAMA_MODELS:/usr/share/ollama/.ollama/models … OLLAMA_NO_CLOUD:true OLLAMA_NUM_PARALLEL:1 … OLLAMA_SCHED_SPREAD:false OLLAMA_VULKAN:true …]"

$ journalctl -u ollama --since '2026-09-24 16:09' --no-pager | rg 'inference compute|vram-based default context'; echo "exit=$?"
Sep 24 16:09:13 wikijuridica ollama[2549]: time=2026-09-24T16:09:13.211-03:00 level=INFO source=types.go:50 msg="inference compute" id=cpu library=cpu compute="" name=cpu description=cpu libdirs=ollama driver="" pci_id="" type="" total="29.9 GiB" available="28.4 GiB"
Sep 24 16:09:13 wikijuridica ollama[2549]: time=2026-09-24T16:09:13.211-03:00 level=INFO source=routes.go:2062 msg="vram-based default context" total_vram="0 B" default_num_ctx=4096
exit=0

$ ollama ps; ollama list; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
NAME                                     ID              SIZE      MODIFIED
wj-extracao-sonda:latest                 c68b6fe0216a    3.4 GB    2 weeks ago
qwen3:4b                                 359d7dd4bcda    2.5 GB    2 weeks ago
qwen3-embedding:4b                       df5bd2e3c74c    2.5 GB    2 weeks ago
qwen3.5:4b                               2a654d98e6fb    3.4 GB    2 weeks ago
qwen3-embedding:0.6b                     ac6da0dfba84    639 MB    2 weeks ago
guoxuter/ov_intent_analysis_sft:v7_q8    5e0d6bb12290    811 MB    2 weeks ago
qwen3.5:9b                               6488c96fa5fa    6.6 GB    2 weeks ago
qwen3-embedding:8b                       64b933495768    4.7 GB    2 weeks ago
qwen2.5-coder:14b                        9ec8897f747e    9.0 GB    2 weeks ago
memory.used [MiB], utilization.gpu [%]
1 MiB, 0 %

$ cat data/ops/cerebro_pausa_manual.json
{
  "motivo": "carga transitoria antes do transplante do servidor: a extracao de 105.524 acordaos pendentes a ~4,9 tok/s de eval levaria ~50 dias nesta CPU (qwen3.5:4b, 3,5 nucleos, 9,2 GB residentes, pacote a 95-97 C, NVMe a 83,8 C) e a GPU da maquina nova faz o mesmo 17,8x mais rapido; o Ollama fica de pe para o buscar_semantico. Retirar este arquivo retoma; vencido, o gate cerebro-saude fica vermelho de proposito.",
  "ate": "2026-10-07T23:59:59-03:00",
  "declarada_por": "claude-fable-carga-transplante-20260923 (sessao Claude Code, goal do dono de 2026-09-23)",
  "declarada_em": "2026-09-23T06:30:07-03:00"
}

$ cat data/ops/cerebro_batimento.json
{"ts":"2026-09-24T23:08:07Z","estado":"pausado_a_pedido",…,"pendentes":105512,"elegiveis_agora":105512,"executando":0,"erros":0,"lapides":8,"concluidas":30558,…,"classe_pausa":"manual","sonda_pausa":"pausa_manual",…,"pausada_desde":"2026-09-24T19:09:35Z"}

$ tail -c 600 data/ops/ia_local_daily.jsonl; wc -l data/ops/ia_local_daily.jsonl
…{"schema_version":"ia_local_daily_v1","ts":"2026-09-23T09:37:16Z","date":"2026-09-23","worker":"cerebro-1","tipo":"extrair_dispositivos","modelo":"qwen3.5:4b","lote":3,…,"prompt_tokens":2201,"eval_tokens":1171,"prompt_tok_s":5.261,"prompt_tok_s_liquido":5.261,"eval_tok_s":3.604,"parede_ms":418379,…,"resultado":"ok"}
10320 data/ops/ia_local_daily.jsonl

$ CG=$(systemctl show ollama.service -p ControlGroup --value); echo "cgroup=$CG"; rg '^(anon|file|file_mapped|shmem|kernel) ' /sys/fs/cgroup$CG/memory.stat; cat /sys/fs/cgroup$CG/memory.current   # sem modelo carregado
cgroup=/wikijuridica_alimentacao.slice/ollama.service
anon 13029376
file 3744858112
kernel 5820416
shmem 0
file_mapped 19251200
3763707904

$ free -m; uptime; nproc
               total        used        free      shared  buff/cache   available
Mem:           30649       12173        3548        4204       19586       18475
Swap:          19420        1425       17995
 20:08:08 up  3:59,  1 user,  load average: 1.18, 1.40, 1.57
16

$ ls -la --time-style=full-iso internal/cerebro/saude.go && git diff --numstat -- internal/cerebro/saude.go
-rw-r--r-- 1 rafael rafael 23196 2026-09-17 11:17:41.426395734 -0300 internal/cerebro/saude.go
64	0	internal/cerebro/saude.go

$ rg -n 'TetoBytesResidentes int64|TetoBytesResidentesPadrao int64|A GUARDA PESA BYTES|if soma := bytesResidentes|^func bytesResidentes|ELE SO FAZ SENTIDO' internal/cerebro/saude.go
107:	TetoBytesResidentes int64
203:	TetoBytesResidentesPadrao int64 = 9 << 30
271:		// A GUARDA PESA BYTES, NAO CONTA MODELOS (2026-09-10).
290:		// ELE SO FAZ SENTIDO COM OLLAMA_MAX_LOADED_MODELS=2 no drop-in
294:		if soma := bytesResidentes(residentes); soma > s.tetoBytesResidentes() {
453:func bytesResidentes(residentes []ollama.Residente) int64 {

$ rg -n '^const URLPadrao|^const EnvURL|^type Residente|^func \(r Residente\) SoCPU|TamanhoVRAMBytes \*int64|PontosDeContexto \*int64' internal/ollama/cliente.go
99:const URLPadrao = "http://127.0.0.1:11434"
102:const EnvURL = "WIKI_OLLAMA_URL"
345:type Residente struct {
367:	TamanhoVRAMBytes *int64 `json:"size_vram"`
368:	PontosDeContexto *int64 `json:"context_length"`
374:func (r Residente) SoCPU() (bool, bool) {

$ rg -n 'cliente := ollama.Novo|modeloEmbeddingsPadrao =|"portaljuridico/internal/ollama"|func servir|func enfileirarMedicao|"max-lote"|"puxar-modelo-ausente"|"publicar"' cmd/cerebro/main.go
39:	"portaljuridico/internal/ollama"
46:	modeloEmbeddingsPadrao = "qwen3-embedding:0.6b"
147:func servir(args []string) error {
151:	maxLote := fs.Int("max-lote", 3, …
157:	puxarModelo := fs.Bool("puxar-modelo-ausente", false, …
164:	publicar := fs.Bool("publicar", false, …
176:	cliente := ollama.Novo(ollama.URLDoAmbiente())
528:func enfileirarMedicao(args []string) error {

$ rg -n '^Host:' .claude/rules/ollama-e-earlyoom.md; wc -m .claude/rules/ollama-e-earlyoom.md
15:Host: 19,4 GiB de RAM, 4 nucleos fisicos / 8 threads, sem GPU util (MX110 sem
5372 .claude/rules/ollama-e-earlyoom.md
```

### 7.2 Documentação oficial do Ollama (fonte das variáveis `OLLAMA_*`)

```
$ ollama serve --help
…
Environment Variables:
      OLLAMA_DEBUG                  Show additional debug information (e.g. OLLAMA_DEBUG=1)
      OLLAMA_HOST                   IP Address for the ollama server (default 127.0.0.1:11434)
      OLLAMA_CONTEXT_LENGTH         Context length to use unless otherwise specified (default: 4k/32k/256k based on VRAM)
      OLLAMA_KEEP_ALIVE             The duration that models stay loaded in memory (default "5m")
      OLLAMA_MAX_LOADED_MODELS      Maximum number of loaded models per GPU
      OLLAMA_MAX_TRANSFER_STREAMS   Maximum parallel transfer streams for safetensors model pulls/pushes (default 4)
      OLLAMA_MAX_QUEUE              Maximum number of queued requests
      OLLAMA_MODELS                 The path to the models directory
      OLLAMA_NUM_PARALLEL           Maximum number of parallel requests
      OLLAMA_NO_CLOUD               Disable Ollama cloud features (remote inference and web search)
      OLLAMA_NOPRUNE                Do not prune model blobs on startup
      OLLAMA_ORIGINS                A comma separated list of allowed origins
      OLLAMA_SCHED_SPREAD           Always schedule model across all GPUs
      OLLAMA_FLASH_ATTENTION        Enabled flash attention
      OLLAMA_KV_CACHE_TYPE          Quantization type for the K/V cache (default: f16)
      OLLAMA_LLM_LIBRARY            Set LLM library to bypass autodetection
      OLLAMA_GPU_OVERHEAD           Reserve a portion of VRAM per GPU (bytes)
      OLLAMA_IGPU_ENABLE            Enable integrated GPUs
      LLAMA_ARG_FIT                 Enable llama.cpp automatic fit of unset memory options (default "on")
      LLAMA_ARG_FIT_TARGET          Target free VRAM margin per device for llama.cpp fit (MiB)
      OLLAMA_LOAD_TIMEOUT           How long to allow model loads to stall before giving up (default "5m")
--- exit=0
```

- Código-fonte da mesma versão: https://github.com/ollama/ollama/blob/v0.33.3/envconfig/config.go —
  `LLMLibrary = String("OLLAMA_LLM_LIBRARY")`, `GpuOverhead = Uint64("OLLAMA_GPU_OVERHEAD", 0)`,
  `ContextLength = Uint("OLLAMA_CONTEXT_LENGTH", 0)`, `MaxRunners = Uint("OLLAMA_MAX_LOADED_MODELS", 0)`,
  `NumParallel = Uint("OLLAMA_NUM_PARALLEL", 1)`, com as mesmas descrições do `--help`.
- https://docs.ollama.com/troubleshooting — "You can set OLLAMA_LLM_LIBRARY to any of the available LLM
  libraries to bypass autodetection". As bibliotecas disponíveis neste host são os diretórios de
  `/usr/local/lib/ollama/` (§7.1).
- https://docs.ollama.com/gpu — compute capability 12.0 = "GeForce RTX 50xx … `RTX 5060 Ti`"; seleção de
  placa NVIDIA por `CUDA_VISIBLE_DEVICES` (com uma placa só, desnecessário).
- https://docs.ollama.com/faq — configuração do servidor Linux por `systemctl edit ollama.service` e
  `Environment=`; `ollama ps` coluna PROCESSOR ("100% GPU", "100% CPU", divisão); `OLLAMA_NUM_PARALLEL`
  multiplica o contexto; `OLLAMA_KV_CACHE_TYPE` `q8_0` ≈ metade da memória de `f16`; `OLLAMA_NO_CLOUD=1`.
- https://github.com/ollama/ollama/blob/main/docs/api.md — `/api/generate`: "divide `eval_count` /
  `eval_duration` * `10^9`"; `/api/embed` devolve `total_duration`, `load_duration`, `prompt_eval_count`;
  `/api/ps` traz `size` e `size_vram`.
- https://github.com/ollama/ollama/issues/18232 — "CUDA crash on Blackwell RTX 5060 Ti due to Flash Attention
  MMA kernel shared memory allocation", Ollama 0.33.3, runner `cuda_v13`, `cudaFuncSetAttribute`, contorno
  `num_ctx` 2048; estado **open** na leitura de 2026-09-24; o relato não diz nada sobre `cuda_v12`.

### 7.3 tok/s de referência na CPU da torre (o "antes" medido hoje)

```
$ tools/check-load-headroom --max 12; echo "exit=$?"; cat /proc/loadavg; date -Iseconds
headroom OK: load1=1.09 < max=12
exit=0
1.09 1.45 1.63 1/2514 383565
2026-09-24T20:17:55-03:00

# E sem prefixo (mesma entrada 4 vezes): mostra o cache de prompt
$ E=$(python3 -c 'import json,sys;print(json.dumps({"model":"qwen3-embedding:0.6b","input":sys.argv[1],"keep_alive":"60s"}))' "$T"); printf '%s' "$E" | sha256sum; for i in 1 2 3 4; do curl -s 127.0.0.1:11434/api/embed -d "$E" | python3 -c 'import sys,json;d=json.load(sys.stdin);t=d["total_duration"];l=d["load_duration"];n=d["prompt_eval_count"];print("run",'$i',"prompt_eval_count",n,"total_ns",t,"load_ns",l,"dims",len(d["embeddings"][0]),"tok_s",round(n/((t-l)/1e9),1))'; done; echo '--- ps'; ollama ps; curl -s 127.0.0.1:11434/api/ps; echo; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv; cat /proc/loadavg
be3b00cdadd0970ee28a613f09f794df9f9985479b41011915c1a3b93e77dce2  -
run 1 prompt_eval_count 221 total_ns 1261049471 load_ns 777549254 dims 1024 tok_s 457.1
run 2 prompt_eval_count 221 total_ns 29981500 load_ns 741932 dims 1024 tok_s 7558.3
run 3 prompt_eval_count 221 total_ns 28678878 load_ns 635050 dims 1024 tok_s 7880.5
run 4 prompt_eval_count 221 total_ns 30062873 load_ns 628648 dims 1024 tok_s 7508.3
--- ps
NAME                    ID              SIZE      PROCESSOR    CONTEXT    UNTIL
qwen3-embedding:0.6b    ac6da0dfba84    2.4 GB    100% CPU     8192       59 seconds from now
{"models":[{"name":"qwen3-embedding:0.6b","model":"qwen3-embedding:0.6b","size":2417491967,"digest":"ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d","details":{…,"parameter_size":"595.78M","quantization_level":"Q8_0"},"expires_at":"2026-09-24T20:19:05.489279399-03:00","size_vram":0,"context_length":8192}]}
pid, process_name, used_gpu_memory [MiB]
1.08 1.44 1.62 9/2561 384551

# E — com prefixo por rodada
$ for i in 1 2 3 4; do E=$(python3 -c 'import json,sys;print(json.dumps({"model":"qwen3-embedding:0.6b","input":"["+sys.argv[2]+"] "+sys.argv[1],"keep_alive":"60s"}))' "$T" "$i"); curl -s 127.0.0.1:11434/api/embed -d "$E" | python3 -c 'import sys,json;d=json.load(sys.stdin);t=d["total_duration"];l=d["load_duration"];n=d["prompt_eval_count"];print("run",'$i',"prompt_eval_count",n,"total_ns",t,"load_ns",l,"tok_s",round(n/((t-l)/1e9),1))'; done; cat /proc/loadavg; date -Iseconds
run 1 prompt_eval_count 224 total_ns 326313543 load_ns 593091 tok_s 687.7
run 2 prompt_eval_count 224 total_ns 288093861 load_ns 622897 tok_s 779.2
run 3 prompt_eval_count 224 total_ns 285979478 load_ns 618699 tok_s 785.0
run 4 prompt_eval_count 224 total_ns 296383668 load_ns 627095 tok_s 757.4
1.80 1.56 1.65 8/2528 385943
2026-09-24T20:18:31-03:00

# G1 — laço literal no fim desta seção
run 1 load_ns 2813352184 prompt_eval_count 49 prompt_eval_ns 285643000 eval_count 128 eval_ns 7906915000 done length prompt_tok_s 171.54 eval_tok_s 16.19
run 2 load_ns 583013 prompt_eval_count 49 prompt_eval_ns 306322000 eval_count 128 eval_ns 7895147000 done length prompt_tok_s 159.96 eval_tok_s 16.21
run 3 load_ns 568575 prompt_eval_count 49 prompt_eval_ns 306751000 eval_count 128 eval_ns 7892907000 done length prompt_tok_s 159.74 eval_tok_s 16.22
run 4 load_ns 584766 prompt_eval_count 49 prompt_eval_ns 409158000 eval_count 128 eval_ns 8111809000 done length prompt_tok_s 119.76 eval_tok_s 15.78
5.20 2.43 1.94 9/2571 388190
2026-09-24T20:19:18-03:00

# G2 — prompt longo
$ Q='Pergunta: qual artigo do texto acima trata dos limites subjetivos da coisa julgada? Responda em uma frase.'; for i in 1 2 3; do G=$(python3 -c 'import json,sys;t=sys.argv[1];print(json.dumps({"model":"qwen3.5:4b","prompt":"["+sys.argv[3]+"] "+"\n\n".join([t]*4)+"\n\n"+sys.argv[2],"stream":False,"think":False,"keep_alive":"60s","options":{"temperature":0,"seed":42,"num_predict":64,"num_ctx":8192}}))' "$T" "$Q" "$i"); curl -s --max-time 170 127.0.0.1:11434/api/generate -d "$G" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("run",'$i',"load_ns",d["load_duration"],"prompt_eval_count",d["prompt_eval_count"],"prompt_eval_ns",d["prompt_eval_duration"],"eval_count",d["eval_count"],"eval_ns",d["eval_duration"],"done",d.get("done_reason"),"prompt_tok_s",round(d["prompt_eval_count"]/d["prompt_eval_duration"]*1e9,2),"eval_tok_s",round(d["eval_count"]/d["eval_duration"]*1e9,2))'; done; cat /proc/loadavg; ollama ps; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv; date -Iseconds
run 1 load_ns 617017 prompt_eval_count 789 prompt_eval_ns 3937814000 eval_count 44 eval_ns 2746700000 done stop prompt_tok_s 200.36 eval_tok_s 16.02
run 2 load_ns 638498 prompt_eval_count 789 prompt_eval_ns 3968443000 eval_count 44 eval_ns 2767533000 done stop prompt_tok_s 198.82 eval_tok_s 15.9
run 3 load_ns 597911 prompt_eval_count 789 prompt_eval_ns 3808164000 eval_count 35 eval_ns 2170342000 done stop prompt_tok_s 207.19 eval_tok_s 16.13
5.65 2.82 2.09 8/2508 389992
NAME          ID              SIZE      PROCESSOR    CONTEXT    UNTIL
qwen3.5:4b    2a654d98e6fb    3.2 GB    100% CPU     8192       59 seconds from now
pid, process_name, used_gpu_memory [MiB]
2026-09-24T20:19:59-03:00

# memória com qwen3.5:4b residente em CPU (o runner é o pid 386228; os outros dois casam o padrão por acaso)
$ date -Iseconds; curl -s 127.0.0.1:11434/api/ps; echo; CG=$(systemctl show ollama.service -p ControlGroup --value); rg '^(anon|file) ' /sys/fs/cgroup$CG/memory.stat; cat /sys/fs/cgroup$CG/memory.current; for p in $(pgrep -f 'llama-server|ollama runner' ); do printf 'pid %s ' $p; rg 'VmRSS' /proc/$p/status; done
2026-09-24T20:20:19-03:00
{"models":[{"name":"qwen3.5:4b","model":"qwen3.5:4b","size":3227894413,"digest":"2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd","details":{…,"parameter_size":"4.7B","quantization_level":"Q4_K_M"},"expires_at":"2026-09-24T20:20:59.121502887-03:00","size_vram":0,"context_length":8192}]}
anon 4637728768
file 807845888
5462822912
pid 1925 VmRSS:	    2288 kB
pid 386228 VmRSS:	 4530708 kB
pid 391513 VmRSS:	    3760 kB

# modelo de embedding não gera: por isso o tok/s dele é medido em /api/embed
$ curl -s 127.0.0.1:11434/api/generate -d '{"model":"qwen3-embedding:0.6b","prompt":"x","stream":false,"keep_alive":0}'; echo; echo "exit=$?"; ollama ps
{"error":"\"qwen3-embedding:0.6b\" does not support generate"}
exit=0
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL

$ date -Iseconds; ollama ps; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv; cat /proc/loadavg   # estado devolvido
2026-09-24T20:24:57-03:00
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
memory.used [MiB], utilization.gpu [%]
1 MiB, 0 %
1.56 1.92 1.89 1/2419 403299
```

`T` nos laços acima é o texto da §4.2, atribuído com `T='…'` no início de cada comando.

O laço de G1, exatamente como rodou:

```
P='Resuma em cinco frases, em portugues, o regime da coisa julgada nos arts. 502 a 508 do Codigo de Processo Civil.'
for i in 1 2 3 4; do
  G=$(python3 -c 'import json,sys;print(json.dumps({"model":"qwen3.5:4b","prompt":"["+sys.argv[2]+"] "+sys.argv[1],"stream":False,"think":False,"keep_alive":"60s","options":{"temperature":0,"seed":42,"num_predict":128,"num_ctx":8192}}))' "$P" "$i")
  curl -s --max-time 170 127.0.0.1:11434/api/generate -d "$G" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("run",'$i',"load_ns",d["load_duration"],"prompt_eval_count",d["prompt_eval_count"],"prompt_eval_ns",d["prompt_eval_duration"],"eval_count",d["eval_count"],"eval_ns",d["eval_duration"],"done",d.get("done_reason"),"prompt_tok_s",round(d["prompt_eval_count"]/d["prompt_eval_duration"]*1e9,2),"eval_tok_s",round(d["eval_count"]/d["eval_duration"]*1e9,2))'
done
```

### 7.4 Rede social

```
$ awk 'NR>=2225 && NR<=2242 {print NR": "$0}' docs/goal/PLANO_REDE_SOCIAL.md   # antes da nota
2225: ### 15.4 Anti-abuso sem CAPTCHA de terceiro
…
2232: 2. **Quarentena de conta nova**: 7 dias **e** 3 posts sobrevividos. 5 posts/dia, 20
…
2237: 3. **Rate limit por conta no Go** (`x/time/rate`, já no `go.mod`) **mais contador diário
…
2240: 4. **Reputação** como regulador interno, **nunca exibida como ranking** — placar público
2241:    esbarra no Prov. 205 art. 5º e na linha `ordenacao_por_conversao` de §10.1. Destrava link
2242:    externo (≥5), DM a desconhecido (≥10), abrir thread (≥20).

$ rg -n 'reputa|ranking|leaderboard' docs/goal/PLANO_REDE_SOCIAL.md docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md | head -40   # antes da nota
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:307:### 1.6 `gptbot` no ranking: o briefing está defasado, e é preciso dizer os dois estados
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:314:Ou seja: a premissa do briefing (*"o ranking é cego para o gptbot"*) é **verdadeira em `HEAD`**
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:566:| **2 — agente credenciado** | agente externo que quer escrever | `/agent/auth` → `client_credentials` → Bearer, cota 20/dia | **um escopo novo** (ex.: `redesocial:comentar`) ao lado de `relatos:escrever`; e a decisão de arquitetura sobre reputação por `client_id` |
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:573:**Decisão de arquitetura, em aberto e nomeada:** a reputação da rede social hoje é **por conta**
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:574:(`social_policy.json` → `.reputacao`, escada de 0 a 20 com `destrava_abrir_thread: 20`). Um
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:576:escrita antes: reputação por `client_id`, por organização declarada, ou por
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:763:| contagem de curtidas, seguidores, "em alta" | mede volume, não verificabilidade; e `.reputacao.exibida_publicamente` **já é `false`** `[disco]` | **taxa de citação resolvida por peça** |
docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md:933:git show HEAD:cmd/cerebro/comentarios.go | grep -n gptbot     # o ranking mudou desde este doc?
docs/goal/PLANO_REDE_SOCIAL.md:218:- **Art. 5º** — **vedado pagamento por "aparição em rankings, prêmios ou qualquer tipo de
docs/goal/PLANO_REDE_SOCIAL.md:219:  recebimento de honrarias"**. → **mata destaque pago e ranking pago de advogado.**
docs/goal/PLANO_REDE_SOCIAL.md:263:| Destaque pago / topo de lista | **configurável** (§10.1) | Prov. 205 art. 5º — analogia, o artigo mira prêmio e ranking editorial |
docs/goal/PLANO_REDE_SOCIAL.md:316:(Python) já produziu `data/research/datajud/ranking_nacional.json` com **283.415.422
docs/goal/PLANO_REDE_SOCIAL.md:1100:| `destaque_pago` | configurável | Prov. 205 art. 5º (pagar por "rankings, prêmios ou honrarias") | **analogia** — o artigo mira anuário e prêmio editorial, não posição em plataforma |
docs/goal/PLANO_REDE_SOCIAL.md:1722:`social-policy` varre o DDL por esses radicais. As colunas de `destaque`/`ranking`/`plano`
docs/goal/PLANO_REDE_SOCIAL.md:2240:4. **Reputação** como regulador interno, **nunca exibida como ranking** — placar público
docs/goal/PLANO_REDE_SOCIAL.md:2342:tem cota e âncora; denúncia infundada repetida custa reputação; e o relatório publica a razão
docs/goal/PLANO_REDE_SOCIAL.md:2419:essa medição verde. Se a medição reprovar, o problema é de reputação de IP e de DNS, e se
--- exit=0

$ awk 'NR>=573 && NR<=578 {print NR": "$0}' docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md
573: **Decisão de arquitetura, em aberto e nomeada:** a reputação da rede social hoje é **por conta**
574: (`social_policy.json` → `.reputacao`, escada de 0 a 20 com `destrava_abrir_thread: 20`). Um
575: `client_id` de agente **não é uma pessoa** e a mesma organização pode ter mil. A régua tem de ser
576: escrita antes: reputação por `client_id`, por organização declarada, ou por
577: **verificabilidade do que a peça cita** — e a terceira é a que casa com a métrica do §12 do
578: contrato. Isto é escolha do próximo executor, não deste rascunho.

$ ls cmd/social internal | rg -i 'social|reput'
cmd/social:
redesocialcompletude
socialantiabuso
socialautoridade
socialbackup
socialborda
socialcard
socialconexao
socialconteudo
socialdb
socialheaders
socialindexnow
socialisolation
socialmail
socialmarkdown
socialmedia
socialpapeis
socialpiso
socialpolicy
socialpurga
socialrender
socialrestore
socialtema
--- exit=0
$ ls cmd/social | wc -l
89

$ rg -n 'placar publico de advogado|social_policy_reputacao_exibida|type Reputacao struct|ExibidaPublicamente  ' internal/socialpolicy/policy.go
122:type Reputacao struct {
131:	ExibidaPublicamente           bool `json:"exibida_publicamente"`
749:	// Reputacao exibida vira placar publico, e placar publico de advogado
753:			Code:    "social_policy_reputacao_exibida",
$ rg -n 'social_policy_reputacao_exibida|ExibidaPublicamente' --glob '!data/**' --glob '!*.md' .
./internal/socialantiabuso/camadas_test.go:167:	if viva.Reputacao.ExibidaPublicamente {
./internal/socialpolicy/policy.go:131:	ExibidaPublicamente           bool `json:"exibida_publicamente"`
./internal/socialpolicy/policy.go:751:	if r.ExibidaPublicamente {
./internal/socialpolicy/policy.go:753:			Code:    "social_policy_reputacao_exibida",
./internal/socialpolicy/policy_test.go:204:		{"reputacao exibida", func(p *Policy) { p.Reputacao.ExibidaPublicamente = true }, "social_policy_reputacao_exibida"},
$ rg -n '"social-policy"' internal/checks/checks.go
517:	"social-policy",
1981:	case "social-policy":

$ python3 -c "import json;d=json.load(open('content/social_policy.json'));print(json.dumps(d.get('reputacao'),ensure_ascii=False))"; rg -n '"exibida_publicamente"' content/social_policy.json
{"inicial": 0, "post_sobrevive_30_dias": 1, "resposta_marcada_util": 3, "denuncia_procedente": -20, "remocao_judicial": -100, "destrava_link_externo": 5, "destrava_mensagem_a_desconhecido": 10, "destrava_abrir_thread": 20, "exibida_publicamente": false}
109:    "exibida_publicamente": false

$ python3 - <<'EOF'   # contagem por estado (trecho do script)
import json,collections
d=json.load(open('content/redesocial_entregas.json'))
ents=d.get('entregas') or []
print(len(ents), dict(collections.Counter(e.get('estado') for e in ents)))
EOF
164 {'entregue': 150, 'pendente': 11, 'suspenso': 3}
$ python3 - <<'EOF'   # entregas que citam reputação
import json
d=json.load(open('content/redesocial_entregas.json'))
for e in d['entregas']:
    s=json.dumps(e,ensure_ascii=False)
    if 'reputa' in s.lower():
        print(e.get('id'), e.get('fase'), e.get('estado'), '|', (e.get('titulo') or '')[:120])
EOF
F2-anti-abuso-camadas-2-a-6 F2 entregue | Quarentena de conta nova (7 dias e 3 posts, sem link externo), orcamento diario PERSISTIDO por conta, reputacao que nunc
FP-quarentena-nao-trava-o-produto F2 entregue | fonte_url de dominio oficial (planalto, lexml, *.jus.br, in.gov.br) NAO conta como link externo para a quarentena, e abr

$ rg -n 'redesocial:comentar' -g '*.go' .; echo "exit=$?"; rg -n -i 'client_id' cmd/social/; echo "exit=$?"
exit=1
exit=1
```

### 7.5 Notas aplicadas nos dois planos e estudos intactos

```
$ sha256sum docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md docs/goal/PLANO_REDE_SOCIAL.md   # antes das notas
276789474f766dc690c930b10ac2d13ed3c745f0f7bf12c8e7c9da5670e0a4cb  docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md
324ec85d33455407029fdc29c1985130db65d4d61a7d77ebaaf144f8aa58efec  docs/goal/PLANO_REDE_SOCIAL.md

$ rg -n 'Nota de 2026-09-24' docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md docs/goal/PLANO_REDE_SOCIAL.md
docs/goal/PLANO_REDE_SOCIAL.md:2244:   > **Nota de 2026-09-24.** Esta cláusula continua em vigor e tem objeto certo: a reputação
docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md:3:> **Nota de 2026-09-24.** O plano do EnaEval (`docs/goal/enaeval/`) fixa a convivência deste cérebro com o serving do EnaEval até F3.O1 e o objetivo F3.O0 (Ollama na GPU): ver `docs/goal/enaeval/PONTE_CEREBRO_E_REDE_SOCIAL.md` e DEC-062.

$ git diff --numstat -- docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md docs/goal/PLANO_REDE_SOCIAL.md
2	0	docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md
12	0	docs/goal/PLANO_REDE_SOCIAL.md

$ sha256sum docs/goal/enaeval/CANON-v4.1.md docs/goal/enaeval/TASKLIST.md docs/goal/enaeval/DECISOES-ORQUESTRADOR.md
1db688af35f81f749e662cebc802c3dc14c4cfd9212d31df75a97b32464dcdb1  docs/goal/enaeval/CANON-v4.1.md
d3524fb283fdfdb1af35d75bf9d5610a0749dc3caad7fa687681def00a8e1c5c  docs/goal/enaeval/TASKLIST.md
2fa6907bf805901635f5dc0b577ff7a9b28fd23251d2ddfde93d9c86cdc58652  docs/goal/enaeval/DECISOES-ORQUESTRADOR.md
```

Só acréscimo: nenhuma linha removida nos dois planos. A nota do plano do cérebro desloca em duas linhas tudo
o que vem depois dela (o §P12 estava em `:3923` e está em `:3925`); a do plano de rede social desloca o que
vem depois de `:2242`.

### 7.6 Varredura de cronograma deste arquivo

```
$ rg -n -i '\b(em|dentro de)\s+\d+\s+(dias?|semanas?|meses?)\b|\bQ[1-4]/20|\bsemana\s+\d' docs/goal/enaeval/PONTE_CEREBRO_E_REDE_SOCIAL.md
(saída vazia; exit 1)
```
