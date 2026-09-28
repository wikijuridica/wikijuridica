# LACUNA 6 — A migração no meio da execução: estado, medição pré-desligamento e ordem do dia um

Investigação somente-leitura em /opt/wiki, 2026-09-15. Todo número abaixo é medição
própria desta sessão, com o comando ou o arquivo:linha ao lado. O que não foi medido
está marcado **não medido** com o motivo.

## VEREDITO

**BLOQUEANTE**, por três achados que a lacuna não continha e que quebram a execução:

1. **`public/` (683 MB, `.gitignore:/public/`) está DELIBERADAMENTE fora do único backup
   do projeto, e perdê-lo derruba o processo Go no boot** — não só o acervo estático.
   **As duas formas de errar levam ao mesmo lugar, e eu li o caminho de cada uma:**
   - **`public/` AUSENTE:** `Validate` chama `collectPublicFiles` (:177), que faz
     `filepath.WalkDir` sobre `<root>/public` (:1246-1249); diretório inexistente devolve
     erro, e :178-180 devolve um Report com **uma** issue de código
     `published_manifest_public_scan_failed`. Esse código **não está** em
     `staticArtifactOnlyIssueCodes` (:1456-1463) — logo é **blocking desde a primeira
     ocorrência** e `novoHandler` devolve erro (`internal/httpserver/httpserver.go:967`,
     `:980-982`). O servidor Go **não sobe**.
   - **`public/` PRESENTE mas reconstruído com bytes diferentes:**
     `published_manifest_html_sha256_mismatch` (:1020) e
     `published_manifest_public_html_missing` (:1018) são códigos *tolerados*, mas
     `bootSameCodeAbortThreshold = 10` (:1469) aborta acima de 10 do MESMO código e
     `bootTotalAbortThreshold = 25` acima de 25 no total. Com 11.106 páginas, qualquer
     rebuild que mude um byte por página estoura os dois tetos.

   Ou seja: "reconstruir `public/` na máquina nova" significa nginx 404 no acervo **e**
   servidor Go que não sobe, nas duas variantes.
2. **A fila e o índice de vetores são UMA unidade, e o código só sabe se curar por um dos
   dois lados.** Medido agora: 11.248 tarefas `embed_pagina` concluídas na fila contra
   11.248 pares `(path, sha256_texto)` no índice — **0 órfãs**. `EnfileiraEmbeddings`
   (`internal/cerebro/tarefas.go:255-283`) só pula por presença no ÍNDICE; quando não
   pula, chama `Fila.Enfileirar`, que é `INSERT OR IGNORE` e ignora tarefa igual **em
   qualquer estado** (`internal/cerebro/fila.go:313-317`). Levar `fila.sqlite` sem
   `data/ai/embeddings/` = buraco permanente e SILENCIOSO de até 11.248 páginas no índice
   semântico, que nenhum gate detecta (grep em `tools/check-*` e `internal/checks/checks.go`:
   nenhum compara a fila com o índice).
3. **O teto de 9 GiB da guarda de saúde pausa o cérebro no primeiro residente grande — não
   no boot, e é isso que torna a migração inútil para o que ela serve.**
   `internal/cerebro/saude.go:90-92` (`TetoBytesResidentesPadrao = 9 << 30` = 9.663.676.416 B)
   soma o campo `size` de `/api/ps` (`saude.go:204-205`), e
   `internal/ollama/cliente.go:276-281` não lê `size_vram` — o campo existe e hoje vale 0
   porque tudo está em CPU.
   **Aritmética, para não exagerar a severidade:** os dois residentes de hoje somam
   3.227.894.413 + 2.417.491.967 = **5.645.386.380 B (5,65 GB)**, abaixo do teto — e
   continuariam abaixo na GPU, porque `size` é a pegada total independentemente de onde ela
   mora. Logo o dia um **não** começa pausado. O que pausa é o primeiro par grande que a
   GPU passa a permitir: `/api/ps` reporta `size` bem acima do tamanho da tag (o
   `qwen3-embedding:0.6b` tem tag de 639.150.858 B e `size` de 2.417.491.967 B por causa do
   KV cache de 8192), então um par `qwen3.5:9b` + `qwen3.5:4b` passa dos 9 GiB com folga de
   VRAM sobrando. Aí `Verifica` devolve erro, `Worker.Passo` entra em `ErrPausado` a cada
   ciclo, e o sintoma ("ollama com 2 modelos residentes somando X GiB, acima do teto de
   9,00 GiB") parece defeito do Ollama. O próprio drop-in avisa do acoplamento: "subir o
   MAX sem este teto pausaria o worker para sempre".

O resto da lacuna é **CONTROLADO** em grande parte, com evidência: existe backup noturno
em disco físico separado com verificação e ENSAIO DE RESTAURAÇÃO, e ele já cobre segredos,
banco social com `VACUUM INTO` e registro de acesso.

---

## 1. INVENTÁRIO DO ESTADO NÃO-VERSIONADO

O critério do backup existente é **"o git não guarda E não está ignorado"**
(`tools/generate-backup-wiki`, cabeçalho: "TODO arquivo untracked E NAO IGNORADO"). Logo,
**tudo que está no `.gitignore` está fora do backup**, salvo as três exceções nominais que
o script abre (`.env*`, `var/social/*.db`, `var/ops/access-{raw,keys}`).

Estado do backup, medido em `data/ops/backup_wiki.jsonl` (última linha, 2026-09-15T02:31:28Z):
14.283.032 KB no destino, 55 arquivos untracked / 546.786.620 bytes, `problema: ""`,
`lgpd.db` e `social.db` com `integrity_check: ok` e `sal: copiado`.
Ensaio de restauração em `data/ops/backup_restore_ensaio.jsonl` (2026-09-13T04:23:33Z):
19.270 arquivos verificados, 3.328.257.060 bytes, `ausentes: []`, `divergentes: []`,
segredos presentes `.env.local`, `.env.local.example`, `.env.social`, `access-keys`,
`access-raw`. `/mnt/hdd`: 915 G, 140 G usados, **766 G livres**.

| item | tamanho medido | sobrevive ao reboot? | versionado? | no backup? | como se transporta | custo de perder |
|---|---|---|---|---|---|---|
| `data/ai/fila.sqlite` + `-wal` + `-shm` | 139.546.624 B (34.069 páginas × 4096) + 1.005.312 B + 32.768 B; 53.786 linhas | sim (arquivo) | **não** (`.gitignore:689-690`) | **não** | `VACUUM INTO` (ver §3) | ver §3: baixo p/ extração, **catastrófico se separado do índice de vetores** |
| `data/ai/embeddings/qwen3-embedding-0.6b/vetores.f32` + `indice.jsonl` | 46.071.808 B + 3.631.556 B; 11.248 pares, 11.118 paths, dim 1024 | sim | **não** (`.gitignore:693-694`); só `ativo.json` é versionado | **não** | `cp -p` (imutável append-only; parar o cérebro antes) | **28,7 h** de parede medidos (§2, cálculo abaixo) |
| `data/ai/grafo.sqlite` | 302.379.008 B | sim | **não** (`.gitignore:691`) | **não** | `VACUUM INTO` | não medido (derivado de corpus versionado; `grafo_manifest.json` é versionado) |
| `data/ai/grafo_vizinhanca.jsonl` | 235.778.943 B | sim | **não** (`.gitignore:701`) | **não** | regenerável | nulo — o `.gitignore:700` diz "o servidor tolera ausência" |
| `public/` | 683 MB; **22.982 arquivos, 11.358 `.html`** medidos por `find` (o CLAUDE.md §6 diz "10.369 arquivos de public/" — número **desatualizado**) | sim | **não** (`.gitignore:/public/`) | **NÃO, por decisão escrita** | **tem de ir byte-a-byte** (rsync com checksum) | **derruba o boot do Go** acima de 10 divergências + 404 em todo o acervo |
| `var/social/*.db` + `.sal` | `social.db` 2.703.360 B, `lgpd.db` 49.152 B | sim | não | **SIM** (VACUUM INTO + `cmp` do sal) | já coberto | dado de usuário, insubstituível — mas está coberto |
| `var/ops/access-raw`, `var/ops/access-keys` | dentro dos 2,4 GB de `var/` | sim | não | **SIM** | já coberto | único lugar com IP em claro |
| resto de `var/` (2,4 GB: `nginx`, `on-demand-cache`, `deploy-binario`, `ensaio`…) | 2,4 GB total | sim | não | não | regenerável | cache de runtime |
| `~/.local/state/wikijuridica/perfil-navegador` | **275 MB** | sim | não | **NÃO — está FORA da árvore do repo**, logo fora até do critério "untracked" | `cp -a` preservando modos; NUNCA versionar (cookie de sessão) | **relogin no Facebook/LinkedIn, e reautenticar exige a GUI do dono** (`tools/publicador-social/perfil.mjs:29-38`) |
| blobs do Ollama `/usr/share/ollama/.ollama/models` | **29 GB**, dono `ollama`, 9 tags | sim | não | **não** | `ollama pull` por tag (os digests provam identidade — §2) ou `rsync` do diretório | horas de download; **e sem os digests salvos, "o mesmo modelo" nas duas máquinas é fé** |
| **instalação do Ollama**: `/usr/local/bin/ollama` + `/usr/local/lib/ollama` | 39.521.328 B + **2,1 GB** (runners `cpu-*`, `cuda_v12`, `cuda_v13`, `vulkan`) | sim | não | **não** | reinstalar **fixando 0.33.3** ou `rsync`; se reinstalar, **repetir o grep de `-arch sm_*`** do §4(c) — o achado do `sm_120a` vale para ESTE build | um runner `cuda_v12` sem SASS nativo de Blackwell = JIT de PTX a cada load, ou nada |
| `data/editorial/v2_artifact_vault/{objects,retained}` | **63 MB + 94 MB** (o comentário do `.gitignore` diz "podem somar muitos GiB"; hoje não somam) | sim | **não** | **não** | `rsync` (o manifesto content-addressed e o recibo terminal são versionados) | baixo — mas o cofre é content-addressed e o manifesto versionado aponta para ele |
| `/etc/systemd/system/ollama.service` | 798 B, arquivo REAL de root | sim | **não** | **não** — `backup-host-state` só captura `wikijuridica*`/`cloudflared*` | copiar à mão (é o único elo do Ollama sem custódia no repo) | `ExecStart`, `User=ollama` e o `PATH` da unit |
| drop-in do Ollama | `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` | sim | **SIM** | sim | **symlink** de `/etc/systemd/system/ollama.service.d/` para o repo — custódia correta, verificada | nulo |
| `/etc/default/earlyoom` | symlink → `ops/earlyoom/default` | sim | **SIM** | sim | já no git | nulo |
| `/tmp/opt-wiki-go-cache` (o GOCACHE real) | **3,9 GB** | **NÃO — `/tmp` é apagado** | não | não | não se transporta | ver achado #7: orçamento do pre-commit |
| `.cache/` do repo | **18 GB** (go-cmd-bin 2,7 G; oss-python-venv 1,8 G; factorygraph-uid-1000 1,8 G; gate-build 1,6 G; …) | sim | não | não | regenerável | recompilação/reinstalação de venvs |
| `.toolchains/` | 1,7 GB | sim | não | não | re-baixável (versão fixada) | download |
| `.agents/` rastreado + untracked-não-ignorado | dos 16 GB totais | sim | parcialmente | **SIM** (28.955 arquivos untracked no ensaio de 09-13) | git + backup | — |
| `.agents/` **ignorado** | **15.001.500 KB = 14,3 GiB**, 193 entradas, **202.130 arquivos** (194.907 só em `tmp_rescue/*/tmp/`) | sim | **não** | **não** | ver nota abaixo | **CONTROLADO por desenho documentado**, com uma ressalva |
| `~/.claude` (contrato de máquina, hooks, memória, transcripts) | **4,5 GB** — `projects/` 3,9 GB; `hooks/` 236 KB em **30 arquivos**; `projects/-opt-wiki/memory/` 768 KB em **167 notas**; `CLAUDE.md` 16 KB; `settings.json` 16 KB; `agents/` 16 KB; `plans/` 5,0 MB | sim | **não** (fora do repo) | **NÃO** — fora do repo, logo fora até do critério "untracked" | `rsync -a` do diretório inteiro | **as 8 guardas automáticas, o contrato de máquina e 167 lições que "cada uma custou uma sessão"** |
| `data/` | 8,4 GB | sim | quase tudo | sim | git | — |

**Nota sobre os 14,3 GiB ignorados de `.agents/` — não é descuido, é desenho, e eu conferi
a justificativa em vez de acusar.** O `.gitignore` explica cada classe:
`:232-242` ignora `pages.json.pre-*`, `published_manifest.jsonl.pre-*`,
`first_published_at.json.pre-*` porque **o original é rastreado** e
`git show <sha>:<arquivo>` devolve qualquer versão ("Medido hoje: 525 entradas untracked em
.agents/runtime somavam 778 MB, e 393 MB eram CINCO copias de content/pages.json");
`:244-246` ignora o payload de `tmp_rescue/**` mas **versiona o catálogo**
(`!.agents/runtime/tmp_rescue/*/MANIFESTO.jsonl`); `:458-470` ignora `AGENTS.md.pre-*` e
`GOAL.md.pre-*` pelo mesmo motivo — e abre exceção nominal, medida, para os DOIS que
divergem do HEAD (`nginx.conf.pre-etagoff`, `wikijuridica.conf.pre-etagoff`: 179 e 122
linhas de diretiva de produção nunca commitada) mandando-os **para o git**.
**A ressalva:** a rota de recuperação do payload de `tmp_rescue` (194.907 arquivos) é,
segundo a memória do repositório, o transcript `agent-*.jsonl` — que mora em `~/.claude`,
que **também não tem backup nenhum**. Os dois acervos sem cópia se "cobrem" um ao outro e
estão no MESMO NVMe: perder o disco perde os dois. Daí `~/.claude` entrar na lista de
transporte obrigatório do dia zero.

**Confirmação da memória "checklist pós-reboot":** o que ela diz continua verdadeiro para
`/tmp` (o `ops/host-state/CHECKLIST-REBOOT.md` §b.1 chama isso de "o maior efeito") mas
**está superada num ponto**: ela afirma que o GOCACHE `~/.cache/go-build` sobrevive.
Medido hoje: `~/.cache/go-build` = **0 bytes**, `~/go/pkg/mod` = **0 bytes**, e
`/tmp/opt-wiki-go-cache` = **3,9 GB**. O cache que o repositório usa de fato mora em
`/tmp` e **morre a cada reboot**.

**E o `CHECKLIST-REBOOT.md` (741 linhas) é de OUTRO hardware.** Ele foi auditado sobre este
host — Intel WhiskeyLake-U, `intel_pstate`, TLP como autoridade de governor/EPP, RAPL
`intel-rapl:0` + `intel-rapl-mmio:0` com PL1 17 W, thermald, perfil WiFi "MURILO 5G",
quatro camadas de bloqueio de suspensão de tampa de notebook, painel xfce. Num Ryzen
9800X3D de desktop, as seções (a) e (a2) inteiras deixam de descrever a máquina: `amd_pstate`
em vez de `intel_pstate`, sem RAPL MSR Intel, sem TLP de bateria, sem tampa. **Ele não se
copia: se re-deriva**, e a versão antiga fica no git com data e motivo (regra de contrato
"parágrafo superado ganha data e motivo; não se apaga").

---

## 2. PROTOCOLO DE MEDIÇÃO **PRÉ**-DESLIGAMENTO

Regra que vale para todos: **pareado de verdade**. O próprio repositório já refutou um
"pareado" por não controlar hora, carga concorrente e janela térmica
(`ops/host-state/CHECKLIST-REBOOT.md`, ressalva de 2026-09-10: 193 amostras contra 1.738,
`load1` mediana 6,16 vs 4,36, e a frase sobre throttle **invertida na série crua**). Cada
medição abaixo grava a carga (`load1`) e a hora local junto do número, ou o número é só
teto superior.

### 2.1 Baseline pareado de extração — instrumento JÁ EXISTE
`tools/generate-comparacao-modelos-extracao` compara dois JSONL de extração **pareados por
`chave`** e devolve cinco números, dos quais dois existem exatamente para pegar modelo que
responde vazio (cabeçalho: "O gate anterior media descarte, URN e respostas cortadas. Os
tres APROVARIAM um modelo que responde sempre `{"dispositivos":[]}`"):
descarte, %URN, cortadas (`done_reason == "length"`), **`dispositivos_por_acordao`** e
**`eval_tokens_mediano`**. Saída em `data/ops/extracao_dispositivos_amostra_daily.jsonl`
(schema `extracao_dispositivos_amostra_daily_v2`).
Argumentos: `--a`, `--b`, `--rotulo`, `--dry-run` (linhas 81-84).

**Como medir antes de desligar:** congelar uma amostra determinística de acórdãos, rodar a
extração com o modelo de produção (`qwen3.5:4b`) e **preservar o JSONL da passada em
`.agents/runtime/migracao-<data>/extracao_baseline_maquina_velha.jsonl`, commitado** — o
arquivo é o lado `--a` do pareado depois da migração. Sem esse congelamento não há `--a`:
`data/ai/extracoes_dispositivos.jsonl` continua crescendo e o "antes" some dentro do
"depois".

### 2.2 Piso de determinismo — o que é obtenível, e o que NÃO é
- Temperatura já é 0 por ordem: `internal/cerebro/extracao.go:417` (`temperatura := 0.0`) e
  `:424` (`semPenalidade := 0.0`, porque o Modelfile do `qwen3.5:4b` traz
  `presence_penalty 1.5` e ele chegava ao sampler).
- **Não há campo de seed** em `ollama.Geracao` (`internal/ollama/cliente.go:160-175`
  expõe `Temperatura` e `PenalidadeDePresenca`; nenhum `Seed`). Logo o determinismo não é
  fixado por semente: depende de greedy decoding e da aritmética do backend.
- **Consequência que muda o protocolo:** o backend MUDA na migração. Hoje o Ollama carrega
  um `libggml-cpu-*.so` de família Intel (`/usr/local/lib/ollama` tem
  alderlake/icelake/cascadelake/skylakex/…; para Zen 5 seria `libggml-cpu-zen4.so`), e na
  máquina nova o alvo é CUDA. **Identidade de saída entre backends diferentes não se supõe
  — se mede como CONCORDÂNCIA.** Portanto: duas passadas na MESMA máquina, temperatura 0,
  sobre a mesma amostra, dão o **piso** (quanto o modelo varia consigo mesmo); a comparação
  velha×nova é sempre acima desse piso, e só é regressão o que passar dele.
  Sem o piso medido ANTES, qualquer diferença depois é inatribuível.

### 2.3 Identidade do modelo — mais barato que hashear 29 GB
`ollama --version` = **0.33.3** (medido). E `/api/tags` já devolve um **digest de conteúdo
por tag** — hasheá-los de novo é redundante. Os 9 do disco, medidos hoje:

```
wj-extracao-sonda:latest          3389984299  c68b6fe0216a815f  Q4_K_M
qwen3:4b                          2497293931  359d7dd4bcdab3d8  Q4_K_M
qwen3-embedding:4b                2496704041  df5bd2e3c74cd8d0  Q4_K_M
qwen3.5:4b                        3389983735  2a654d98e6fba55d  Q4_K_M   <- extração
qwen3-embedding:0.6b               639150858  ac6da0dfba84a81f  Q8_0     <- embeddings
guoxuter/ov_intent_analysis_sft:v7_q8  811843744  5e0d6bb12290581a  Q8_0
qwen3.5:9b                        6594474711  6488c96fa5faab64  Q4_K_M
qwen3-embedding:8b                4676805193  64b933495768fbd3  Q4_K_M
qwen2.5-coder:14b                 8988124298  9ec8897f747e246e  Q4_K_M
```

Guardar esta tabela **num arquivo commitado** (não só no transcript) e, na máquina nova,
conferir digest a digest. Para o SASS/PTX é `sha256sum` do blob que responde, mas o digest
do manifesto já é content-addressed: o blob divergente aparece como digest divergente.
**Guardar também os parâmetros do Modelfile** (`ollama show --modelfile qwen3.5:4b`): o
`presence_penalty 1.5` do Modelfile é exatamente o tipo de coisa que "vem junto com o
modelo" e mudou o sampler sem ninguém pedir (precedente de 2026-09-08 citado em
`extracao.go:418-423`). **Não medido nesta sessão:** o conteúdo dos Modelfiles — `ollama show`
não foi executado; é uma chamada de leitura, cabe no dia zero.

### 2.4 Recall semântico — instrumento JÁ EXISTE
`tools/medir-recall-semantico` grava uma linha em
`data/ops/recall_semantico_daily.jsonl` (schema `recall_semantico_v1`) com modelo,
dimensão, tamanho do índice, N, k, **recall@1/@5/@10 e MRR do vetor e da busca lexical
(bleve) ao lado**, mais tokens e tok/s. Conjunto de avaliação: a primeira pergunta de FAQ
de cada página, amostra por passo determinístico. Rodar **antes** de desligar é o que dá o
"antes" — o índice de vetores viaja, então o recall deve ficar IGUAL; se cair, o que
quebrou foi o transporte do `vetores.f32`, e essa é a leitura que o número compra.

### 2.5 Throughput por tarefa — a série já existe, e o cálculo do custo de perder
`data/ops/ia_local_daily.jsonl`, 6.609 linhas, 9 dias (2026-09-08 → 2026-09-16), agregado
por mim agora:

| tipo | lotes | tarefas | parede | tok "custo" | erro |
|---|---|---|---|---|---|
| `embed_pagina` | 3.732 | 11.299 | **103.246,9 s = 28,7 h** | 6.315.294 | 7 |
| `extrair_dispositivos` | 2.877 | 8.631 | **463.089,6 s = 128,6 h** | 6.833.708 | 0 |

Daí: **perder `data/ai/embeddings/` custa 28,7 h de parede medida** nesta CPU — é o número
que justifica transportá-lo. Perder a fila **não** custa as 128,6 h (§3). E esta tabela é
o "antes" do ganho de GPU: a mesma agregação na máquina nova, sobre a mesma amostra, mede
o ganho real em vez de citar TFLOPS de folheto.

### 2.6 O experimento do lock (75 s × 29 s) — e a armadilha de refazê-lo
A origem está em `cmd/cerebro/main.go:116-119`: "Sem elas o cerebro competia com o
`go build` de quem esta commitando pelos mesmos 4 nucleos — **75 s de pre-commit contra
29 s com ele parado**". As duas sondas que essa medição justificou estão vivas em
`internal/cerebro/saude.go`: `LockPesadoPadrao = "/tmp/opt-wiki-agent-heavy.lock"` (:87) e
`CargaMaxPadrao = 12.0` (:89), aplicadas em `Verifica` (:175-185).

**Como medir:** cronometrar o `go-index-compile-closure` do pre-commit com (i) o cérebro
ativo e (ii) o cérebro pausado, com o **índice do git vazio** nas duas passadas (o contrato
mede 77,6 s com `internal/v2ingest` no índice contra 14,9 s com índice limpo — é o mesmo
número mudando por outra causa).
**A armadilha:** o orçamento de 14,9 s foi medido com **3,9 GB de GOCACHE quente em
`/tmp`**. Depois do reboot/migração o cache é zero, e a primeira passada paga compilação
fria. Repetir o experimento pós-migração sem aquecer o cache mede a partida a frio, não a
contenção — e duas sessões já atribuíram esse mesmo número à carga e relançaram esperando
load baixo (precedente no CLAUDE.md §1). Portanto: **aquecer o cache com um build completo
antes de cronometrar**, nas duas máquinas, e declarar o estado do cache no registro.

### 2.7 O que mais só existe agora (e precisa de linha datada antes do desligamento)
- **A física do §12 do CLAUDE.md deixa de valer.** O contrato deriva geração ≈ 18 GB/s ÷
  bytes do modelo (medido: `qwen2.5-coder:14b` 1,85 tok/s, `qwen3.5:9b` 2,9 tok/s, prompt
  ~5 tok/s) e MemoryMax/teto de residentes da RAM de **19,4 GiB** deste host. Com DDR5 e
  16 GB de VRAM a fórmula, o teto e a escolha "modelo de 0,6 a 4B em massa, 14b só em lote
  noturno" mudam de premissa. **Medir os tok/s por modelo ANTES** é o que permite escrever
  a linha superada com número, e não com adjetivo.
- **Digests + versão do Ollama** (§2.3) e **tabela de tamanhos residentes** (`/api/ps`
  medido hoje: `qwen3.5:4b` `size` 3.227.894.413 B, `size_vram` 0; `qwen3-embedding:0.6b`
  `size` 2.417.491.967 B, `size_vram` 0, `context_length` 8192 nos dois) — esta é a
  fotografia que prova o achado (a) e calibra o (b).

---

## 3. A FILA: transporte, "executando" e o que de fato se perde

### 3.1 `VACUUM INTO` é o caminho, e o repositório já o provou
`data/ai/fila.sqlite` está em WAL (`PRAGMA journal_mode` = `wal`, medido), com
`-wal` de 1.005.312 B vivo e o worker escrevendo agora (medi `executando=3` e, segundos
depois, `executando=0` com `concluida` indo de 19.576 para 19.579 — o lote fechou entre as
duas leituras). O precedente está escrito em `tools/generate-backup-wiki`:

> `VACUUM INTO`, NUNCA `cp`. Com WAL ligado, o .db sozinho e uma foto ANTERIOR ao ultimo
> checkpoint, e copiar .db + -wal + -shm em tres instantes diferentes produz um arquivo que
> **ABRE E MENTE** — a pior forma de backup que existe.

Três detalhes desse precedente que valem para a fila:
1. **`VACUUM INTO` recusa destino existente** ("output file already exists") — daí o padrão
   do script: escrever em `<destino>.parcial-$$` e **publicar por `mv`** (atômico no mesmo
   filesystem).
2. **Sem `sqlite3` no PATH a cópia NÃO cai para `cp`: falha e avisa.** Mesma regra aqui.
3. **Conferir a cópia com `PRAGMA integrity_check` e `PRAGMA foreign_key_check`** antes de
   confiar (o script trata `!= "ok"` como erro). A fila não tem sidecar tipo `.sal`; o
   `social.db` tem, e a lição é a mesma: **sidecar tem de viajar byte-idêntico**.

Alternativa aceitável e mais simples: **parar `wikijuridica-cerebro.service`** (SIGTERM;
`TimeoutStopSec=240`, o worker termina o lote em curso e sai), rodar
`sqlite3 fila.sqlite "PRAGMA wal_checkpoint(TRUNCATE);"` e então copiar os três arquivos.
Com o daemon parado não há escritor, e o checkpoint zera o `-wal`. `VACUUM INTO` continua
preferível porque não depende de ninguém ter parado nada.

### 3.2 "Executando" quando a máquina morre: há recuperação, **não** há lease
- `Fila.Recuperar` (`fila.go:466-472`) devolve a `pendente` **tudo** que estiver
  `executando`, zerando `worker` e carimbando `erro = "recuperada apos reinicio do worker"`
  quando vazio.
- Ele é chamado em **um** lugar de produção: `cmd/cerebro/main.go:170`, dentro de `servir`,
  **antes** do primeiro `Reivindicar` (grep em `internal/` e `cmd/`: 3 ocorrências, sendo
  uma o teste e uma a própria definição).
- **Não existe lease nem TTL.** `Reivindicar` seleciona só `estado='pendente'`
  (`fila.go:378-380`), então linha presa em `executando` é invisível a todo mundo até um
  boot de `servir`. Como a unit tem `Restart=always` e `RestartSec=15`
  (`ops/systemd/wikijuridica-cerebro.service`), isso se resolve sozinho no primeiro boot.
- **Risco real, e é pequeno:** até `--max-lote 3` tarefas ficam presas entre o crash e o
  próximo `servir`, cada uma já com `tentativas` incrementado (`fila.go:409-410`), contra
  `--tentativas 3` e backoff de 5 min × n. Se alguém rodar `enfileirar-*` na máquina nova
  **antes** de subir o `servir`, as presas continuam presas — mas nenhum dado se perde.
  **Conclusão: CONTROLADO.**

### 3.3 O que se perde de fato ao descartar a fila — e o que NÃO se perde
**Extração: quase nada.** As extrações concluídas nunca voltam à fila porque o cache de
enfileiramento lê o **arquivo de saída versionado**, não o banco:
`UltimaExtracaoPorChaveEModelo` (`extracao.go:875-899`) lê
`data/ai/extracoes_dispositivos.jsonl` — **rastreado no git** (`git ls-files data/ai/`
confirma; 42.084.234 B hoje) — e devolve `(chave, modelo) → texto_sha256`. O comentário de
`extracao.go:133-137` diz isso com todas as letras: "as extracoes ja concluidas NUNCA
voltam a fila". Logo, descartar a fila **não** refaz as 128,6 h: refaz só a ORDEM de
prioridade dos 34.163 pendentes (reconstruível — `enfileirar-extracoes` recalcula
prioridade por ano, `--reprioritizar` default true) e **perde os 44 diagnósticos da coluna
`erro`** (39 de `extrair_dispositivos`, 5 de `embed_pagina`), que é o que o `status`
mostra para dizer o que está travando.

**Embeddings: aqui a fila é insubstituível OU letal, e depende do que viaja com ela.**
Medição desta sessão (script Python sobre `indice.jsonl` + `fila.sqlite?mode=ro`):

```
índice:  11.248 pares (path, sha256_texto);  11.118 paths distintos
fila:    11.248 embed_pagina concluídas;  0 pendentes/executando;  5 erro
concluídas SEM vetor no índice (par exato): 0 de 11.248
```

Coerência perfeita hoje (as 130 de diferença entre 11.248 e 11.118 são páginas re-embutidas
com hash novo: o índice é append-only com `offset`, guarda as duas linhas). Os três
cenários de transporte:

| levo | resultado |
|---|---|
| fila **+** `embeddings/` | correto. Nada re-executa, recall preservado. |
| **só** `embeddings/` (fila nova) | auto-cura. `indice.Tem(path,hash)` pula as 11.248; custo zero. |
| nada | auto-cura, custo **28,7 h** de parede. |
| **só a fila** (sem `embeddings/`) | **BURACO SILENCIOSO**. `EnfileiraEmbeddings` não acha o índice, tenta enfileirar, `INSERT OR IGNORE` bate na UNIQUE da linha `concluida` e conta a página como `ja_na_fila`. Nada re-executa. Só `ReabrirConcluidas("embed_pagina")` conserta, e ela "nunca acontece sozinha" (`fila.go:492-495`). Sintoma: `buscar_semantico` degradado — produto pelo §12 —, não erro. **Nenhum gate detecta.** |

---

## 4. OS QUATRO BLOQUEIOS DO DIA UM — verificação e ORDEM

### (a) `size_vram` não é lido — **CONFIRMADO**
`internal/ollama/cliente.go:276-281`:
```go
type Residente struct {
	Nome         string    `json:"name"`
	Modelo       string    `json:"model"`
	TamanhoBytes int64     `json:"size"`
	Ate          time.Time `json:"expires_at"`
}
```
Sem `size_vram` e sem `context_length`. E `/api/ps` **devolve os dois** hoje (medido:
`"size_vram":0,"context_length":8192` nos dois residentes). Correção: acrescentar
`VRAMBytes int64 \`json:"size_vram"\`` (e `context_length`, que é grátis e serve à
medição), sem remover `size` — `size` continua sendo o total.

### (b) O teto de 9 GiB tem de virar duas contas — **CONFIRMADO, e é o que pausa o cérebro**
`internal/cerebro/saude.go:90-92` + `:204-205` (`bytesResidentes` soma `TamanhoBytes`).
Com GPU, `size` inclui o que está em VRAM; somar tudo contra 9 GiB confunde duas memórias
distintas. As duas contas certas são as propostas na lacuna:
`sum(size_vram) ≤ 13 GiB` (VRAM, folga de 3 GiB nos 16 do 5060 Ti) e
`sum(size − size_vram) ≤ 2 GiB` (o que ainda pesa na RAM do host).
**Isto precisa entrar no MESMO commit que (a)**, e é o par que o próprio drop-in descreve
("as duas mudancas sao uma so"). O par do incidente continua barrado: 14b+9b = 16 GB de
VRAM > 13 GiB.
**Guarda de regressão obrigatória** (contrato: correção + teste provado por mutação): teste
com `/api/ps` sintético de GPU — dois residentes com `size_vram` somando 12 GiB e `size −
size_vram` somando 1 GiB **passa**; mesmos modelos com `size_vram` 0 e `size` 16 GB
**reprova**. Sem o segundo caso, a mutação "trocar o teto de VRAM por 99 GiB" sobrevive.

### (c) `cuda_v12` × `cuda_v13` e o driver — **METADE CONFIRMADA, METADE REFUTADA**

**Confirmado, por proveniência embutida nos próprios `.so`** (grep de `-arch sm_*` no
binário, contagem exata):

| runner | `-arch sm_120a` | `-arch sm_100` | toolkit |
|---|---|---|---|
| `/usr/local/lib/ollama/cuda_v12/libggml-cuda.so` (418.116.128 B) | **8** | 29 | `release 12.8` |
| `/usr/local/lib/ollama/cuda_v13/libggml-cuda.so` (253.862.336 B) | **0** | 0 | nenhuma string |

Os 8 registros do v12 são literalmente `ptxas ... -arch sm_120a -m 64` — cubin nativo de
Blackwell consumer (o sufixo `a` é arch-specific). O v13 não traz registro de `ptxas` para
arquitetura nenhuma neste teste. Portanto: **`OLLAMA_LLM_LIBRARY=cuda_v12` é a escolha
certa, e não basta "sumir" com a variável** — hoje ela está **explicitamente** `cpu` no
drop-in vivo (`systemctl show ollama.service -p Environment` confirma
`OLLAMA_LLM_LIBRARY=cpu`), então tem de ser TROCADA.
*Ressalva honesta: meu teste mede proveniência de `ptxas` em ASCII; não desmontei fatbin.
Ele não prova que o v13 seja PTX puro, prova que o v13 não carrega cubin com esse registro.*

**REFUTADO — a premissa do driver está errada para ESTE host.** A lacuna diz "Debian trixie
tem 550.163". Medido:
- `/etc/os-release`: **Debian GNU/Linux 12 (bookworm)**, não trixie.
- `apt-cache policy nvidia-driver`: **Instalado 610.57.04-1**, candidato 615.71.09-2, do
  repositório `https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64`.
- `dpkg -l`: `nvidia-driver`, `nvidia-driver-cuda`, `nvidia-driver-libs`,
  `nvidia-kernel-dkms`, `nvidia-kernel-support`, `nvidia-opencl-icd`, todos 610.57.04-1.
- `modinfo /lib/modules/6.1.0-52-amd64/updates/dkms/nvidia.ko` → `version: 610.57.04`,
  122.193.613 B, **já compilado para o kernel em execução**.

Ou seja: **o piso de ≥ 570.26 já está satisfeito por pacote instalado**; não há instalação
de driver a fazer no dia um, e a versão nem vem do Debian, vem do repo da NVIDIA.
**O que NÃO está de pé, e é o que precisa de verificação:** o módulo não está carregado —
`lsmod | grep nvidia` vazio, `/proc/driver/nvidia/version` inexistente, existe só
`/dev/nvidiactl` (sem `/dev/nvidia0`), `nvidia-smi` responde "couldn't communicate with the
NVIDIA driver" e `nvidia-persistenced` está **enabled mas failed**. A causa mais provável é
que a única GPU NVIDIA presente é uma **GeForce MX110 (GM108M, Maxwell)** —
`lspci`: `01:00.0 3D controller: NVIDIA Corporation GM108M [GeForce MX110]` — e o ramo 610
não suporta mais Maxwell. Na máquina nova, a RTX 5060 Ti (Blackwell) **é** suportada por
610, e essa mesma pilha deve passar a funcionar. **Não medido:** não tentei carregar módulo
nem confirmar a matriz de suporte do ramo 610 em fonte oficial da NVIDIA — isso é uma
leitura de release notes que cabe no dia zero, e a alternativa (o módulo carregar e
`nvidia-smi` responder) é verificável em um comando no dia um.
`/etc/modprobe.d/nvidia.conf` já traz `blacklist nouveau`, `blacklist nova-core` e as três
opções de power management — **arquivo de root, fora do `ops/host-state`**: copiar.

### (d) `ollama#18232` (FLASH_ATTENTION=1 + CONTEXT_LENGTH=8192) — **CONFIGURAÇÃO CONFIRMADA, ISSUE NÃO VERIFICADA**
O drop-in vivo tem **exatamente** a combinação citada (medido em
`systemctl show ollama.service -p Environment`):
`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_CONTEXT_LENGTH=8192`, `OLLAMA_KV_CACHE_TYPE=q8_0`,
`OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_KEEP_ALIVE=15m`,
`OLLAMA_NO_CLOUD=1`, `OLLAMA_LLM_LIBRARY=cpu`.
**Não medido:** o conteúdo da issue #18232 e a afirmação de que desligar flash attention
rebaixa `q8_0` para `f16` em silêncio — não busquei a fonte nesta sessão e não há como
medir isso sem a placa. É a única das quatro que entra no dia um como **hipótese a testar**,
e ela é testável em uma requisição: subir com `cuda_v12`, um modelo pequeno, e ler o journal
do `ollama` procurando a linha de tipo do KV cache. O contorno publicado (`num_ctx 2048`)
conflita com `OLLAMA_CONTEXT_LENGTH=8192`, que é o que `/api/ps` reporta hoje como
`context_length` dos dois residentes — logo, mexer nele muda o produto (janela de prompt da
extração), não só a estabilidade.

### ORDEM EXATA DO DIA UM

Antes de qualquer coisa de GPU, o portal tem de estar no ar — o acervo não passa pelo Go,
mas o Go não sobe com `public/` divergente nem ausente (achado #1).

**−1. A PRIMEIRA BIFURCAÇÃO, que decide metade do resto: o NVMe MUDA DE MÁQUINA ou o SO é
reinstalado?** A refutação do §4(c) ("driver 610.57.04 já instalado, piso de 570.26 já
satisfeito") **só vale se o NVMe for**. Em instalação nova não viaja nada de:
`apt` (os 7 pacotes `nvidia-*` 610.57.04-1 e o repositório
`developer.download.nvidia.com/.../debian12`), `/etc` (as 42 units `enabled` medidas em
`ops/host-state/units-habilitadas.txt`, `/etc/modprobe.d/nvidia.conf`,
`/etc/systemd/system/ollama.service`, os symlinks para `ops/`), `/usr/local/bin/ollama` +
`/usr/local/lib/ollama` (2,1 GB de runners), Node (o publicador social), `sqlite3` (sem ele
o backup do banco social **falha e avisa**, por desenho), `/usr/local/go`.
Nesse caso `ops/host-state/units-habilitadas.txt` + `units-copiadas.txt` são a lista de
re-link, e o §4(c) volta a ser "instalar driver ≥ 570.26 com módulos open".
**Decidir e escrever qual dos dois ANTES de desligar** — os dois caminhos têm ordens
diferentes e ninguém descobre isso no meio.
*Nota de kernel, a conferir no dia um:* este host roda 6.1.0-52-amd64 com
`CONFIG_X86_AMD_PSTATE=y` (medido em `/boot/config-`), e hoje o driver ativo é
`intel_pstate`. **Não medido:** se o `amd_pstate` liga de fato num Zen 5 sob 6.1 ou se cai
para `acpi-cpufreq` — ler `/sys/devices/system/cpu/cpufreq/policy0/scaling_driver` na
máquina nova responde, e é isso que decide qual parte da seção (a2) do
`CHECKLIST-REBOOT.md` se re-deriva.

0. **(véspera, máquina velha)** parar `wikijuridica-cerebro`; `VACUUM INTO` da fila e do
   grafo; `cp -p` de `data/ai/embeddings/`; `rsync -a --checksum` de `public/`;
   `rsync -a` de **`~/.claude`** (contrato de máquina + 30 hooks + 167 notas de memória +
   transcripts, 4,5 GB) e dos 14,3 GiB ignorados de `.agents/`;
   `cp -a` do `~/.local/state/wikijuridica/perfil-navegador`; copiar
   `/etc/systemd/system/ollama.service` e `/etc/modprobe.d/nvidia.conf`; rodar
   `tools/generate-backup-wiki` e `tools/check-backup-restauravel`; gravar a tabela de
   digests (§2.3), o piso de determinismo (§2.2) e o baseline pareado (§2.1) **commitados**.
1. **Sistema de arquivos e git**: repo em `/opt/wiki`, `git status` idêntico ao da véspera
   (141 modificados / 39 untracked hoje — qualquer diferença é perda de transporte).
2. **`public/` byte-a-byte**: `tools/check-http-smoke` + verificar que
   `cmd/check published-manifest` (nome exato a ler em `internal/checks/checks.go`) não
   acusa `published_manifest_html_sha256_mismatch`. **Mais de 10 do mesmo código e o Go não
   sobe.** Este passo é anterior a tudo de IA.
3. **nginx + CSP**: conferir que a URL de `ops/nginx/security-headers.conf` é byte a byte a
   de `render.StylesheetPath()` (`tools/check-csp-style-hashes`), senão nenhuma página tem
   estilo. `nginx -t` **sem sudo**.
4. **Túnel/borda**: `tools/check-tunnel-health`, `tools/check-tunnel-replica-fleet`
   (frota de **5**, não 25), `tools/check-edge-live`. Só aqui a nova "assumiu" (§5).
5. **Driver**: `nvidia-smi` responde e reporta 610.57.04 (ou o que estiver instalado);
   `/dev/nvidia0` existe; `nvidia-persistenced` sai de `failed`. Se não: nada de GPU até
   resolver, e o Ollama continua em `OLLAMA_LLM_LIBRARY=cpu` — **degradado é aceitável,
   pausado para sempre não é**.
6. **Código antes da configuração** — (a) + (b) no MESMO commit, com o teste de mutação do
   §4(b), antes de qualquer residente grande existir. Se a configuração for primeiro, o
   cérebro pausa no primeiro par grande e o sintoma parece bug do Ollama.
   **Custo de commit medido, e é boa notícia:**
   `./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` **não** lista
   `portaljuridico/internal/ollama` nem `portaljuridico/internal/cerebro` — logo este
   commit **não** exige `go-modern generate ./internal/v2ingest` nem a atestação no mesmo
   commit (nem os ~10 min de compilação e os 25+ testes). **Mas `internal/publishedmanifest`
   ESTÁ no grafo** — então se alguém for tentado a mexer nos tetos de boot do achado #1
   (o que seria afrouxar gate, proibido), aquele commit **sim** carrega a atestação.
   Conferido também: `git status` de `go.mod`, `go.sum`, `internal/ollama`,
   `internal/cerebro` e `internal/publishedmanifest` está **vazio** hoje — o índice e o
   worktree estão limpos para esse commit, e o `flock /tmp/opt-wiki-commit.lock` vale
   porque o commit toca Go.
7. **Configuração do Ollama**: no drop-in versionado
   (`ops/ollama/ollama.service.d/wikijuridica-tuning.conf`, que é symlink de `/etc` — custódia
   já correta): `OLLAMA_LLM_LIBRARY=cuda_v12`; revisar `MemoryMax=12G`/`MemorySwapMax=2G`
   (derivados de 19,4 GiB de RAM; com 32 GB são outra conta) e `OOMScoreAdjust=800` (a
   justificativa medida — Chrome com badness maior — é deste desktop, re-medir).
   `daemon-reload` + restart do Ollama.
8. **Teste do (d)**: uma requisição com `qwen3-embedding:0.6b`, ler o journal do Ollama
   procurando o tipo do KV cache e erro de flash attention. Se bater a #18232, o contorno é
   parâmetro (`num_ctx`), e ele **muda o produto** — registrar a decisão, não silenciar.
9. **Cérebro**: subir `wikijuridica-cerebro`, ver no log a linha
   `fila ... (N tarefas recuperadas de worker anterior)` (`main.go:172`), e conferir
   `embed_pagina` com `ja_no_indice = 11.248` no primeiro `enfileirar-embeddings`. Se vier
   `novas > 0` em volume, o `vetores.f32` não chegou.
10. **Re-medir**: `tools/medir-recall-semantico` (tem de EMPATAR com a véspera),
    `tools/generate-comparacao-modelos-extracao --a <baseline> --b <nova>`, a agregação de
    `ia_local_daily.jsonl` e o experimento do lock **com cache aquecido** (§2.6).
11. **Reescrever para frente**: §12 do CLAUDE.md (18 GB/s, MemoryMax, "modelo residente"),
    o cabeçalho de `ops/systemd/wikijuridica-cerebro.service` (ver #8 abaixo) e
    `ops/host-state/CHECKLIST-REBOOT.md` — com data, motivo e número medido.

---

## 5. ROLLBACK: até quando a velha serve, e o critério de "a nova assumiu"

**A velha continua útil enquanto o NVMe dela estiver intacto** — e o critério para não
apagá-la não é tempo, é medição. O rollback é barato porque o que serve o portal é o
conjunto (repo + `public/` + túnel), e a velha já o tem: basta subir `cloudflared` de novo lá.

**Critério medido de "a nova assumiu" (todos verdadeiros, medidos NA BORDA, não em
localhost):**
1. `tools/check-edge-live` verde e `tools/check-tunnel-replica-fleet` com as **5**
   instâncias — o `tools/check-portal-health` **não serve** para isto: ele sonda só
   `127.0.0.1` e passa verde com o túnel caído (CLAUDE.md §3).
2. `publishedmanifest` sem nenhuma ocorrência de `published_manifest_html_sha256_mismatch`
   nem `published_manifest_public_html_missing` (teto de 10 por código,
   `publishedmanifest.go:1469`).
3. `wikijuridica-server` de pé com `LISTEN_FDS=1` herdado do socket (o precedente do
   `EADDRINUSE` em laço de 5 s está no CLAUDE.md §1) e `systemctl --failed` vazio.
4. `recall@10` e `MRR` iguais aos da véspera dentro do piso de determinismo (§2.2/2.4).
5. Fila drenando: `concluida` crescendo e `erro` estável em 44 ou menos.
6. Publicação social: uma passada `--dry-run` de `tools/publicar-perfis-sociais` que **não
   peça login** — é a prova de que o perfil de 275 MB chegou íntegro.

**Só depois dos seis, e com um ciclo de backup noturno completo na nova
(`data/ops/backup_wiki.jsonl` com `problema: ""` e `check-backup-restauravel` verde), a
velha pode ser desligada — e o disco dela não se apaga: fica como cópia até o segundo
ensaio de restauração passar na nova.** (Regra do repositório: nunca descartar trabalho.)

---

## 6. ACHADOS EXTRA (não estavam na lacuna e valem passo)

7. **O GOCACHE real mora em `/tmp` (3,9 GB) e morre no reboot**, contra
   `~/.cache/go-build` = 0 B e `~/go/pkg/mod` = 0 B. `go env GOCACHE` responde
   `~/.cache/go-build`, e 10 ferramentas de `tools/` exportam
   `GOCACHE="${GOCACHE:-$HOME/.cache/go-build}"`.
   **Não medido: o produtor da variável.** Procurei por `opt-wiki-go-cache` em
   `tools/go-modern`, `tools/run-heavy-throttled`, `.claude/settings.json` (campo `env`
   vazio), `.git/hooks/*`, `~/.claude/hooks/*`, `~/.bashrc`, `~/.profile` e no `env` do
   shell — **nenhum hit**. Ou seja, é export ambiente de quem lança a sessão/unit, e
   descobrir quem é vale um passo. Consequência para o dia um: o orçamento do
   `go-index-compile-closure` (14,9 s com índice limpo) foi medido com cache quente; frio,
   ele reprova por orçamento e o diagnóstico vai dizer "carga".
8. **O cabeçalho de `ops/systemd/wikijuridica-cerebro.service` está MENTINDO** e é o
   documento que alguém vai ler no dia da migração: afirma "O teto de UM modelo residente
   mora no drop-in do ollama.service (`OLLAMA_MAX_LOADED_MODELS=1`)" e "MemoryMax=15G no
   proprio drop-in". Medido no host: `OLLAMA_MAX_LOADED_MODELS=2` e `MemoryMax=12G`
   (12.884.901.888 B) desde 2026-09-10. Pela R1 do contrato do dado real, comentário que
   mente é bug — e aqui ele faz o orçamento de memória da GPU ser dimensionado sobre uma
   premissa que não existe mais.
9. **`/etc/systemd/system/ollama.service` é o único elo do Ollama sem custódia**: arquivo
   real de 798 B em `/etc`, fora do repo e fora do `backup-host-state` (cujo glob é
   `wikijuridica*`/`cloudflared*`). O drop-in ao lado é symlink para o repo. Correção
   permanente: virar symlink para `ops/ollama/ollama.service` (ou capturá-lo no
   `backup-host-state`) — precedente `custodia-ops-em-symlink`.
11. **As oito guardas automáticas do contrato são 30 arquivos em `~/.claude/hooks/` sem
    cópia nenhuma.** `block-sleep.sh`, `git-guard.sh`, `block-heavy-cmds.sh`,
    `block-masking.sh`, `block-empty-catch.sh`, `protect-bot-ratelimit.{sh,py}`,
    `merge-conflict-check.sh`, `snapshot-antes-de-escrever.py` — mais os testes pareados
    (`git-guard-test.py`, `block-sleep-test.py`, `snapshot-antes-de-escrever-test.py`,
    `hooks-parse-equivalence-test.py`). Na máquina nova sem eles, `git reset --hard`,
    `sleep` como espera, `npm run build` e mascaramento de erro voltam a ser executáveis, e
    o contrato passa a depender de o agente lembrar. Transportar `~/.claude` inteiro é o
    passo; a correção permanente é versioná-los (repo próprio ou `ops/claude-code/`).
12. **`content/legal_cocitation_index.jsonl` só cabe no passo 2.6 do `deploy-publico`** e
    hoje está modificado no worktree. Na máquina nova, republicar sem respeitar a janela
    (republicação reescreve `pages.json` → 2.6 regenera o índice → restart lê) deixa
    `httpserver.filtraPercursosServiveis` como única defesa contra link morto nos quatro
    canais. Não é achado novo do contrato; é um passo que a ordem do dia um tem de conter.

---

## 7. O QUE O ADVISOR MUDOU

Cinco cobranças, todas respondidas por leitura/medição nova. Duas mudaram conclusão.

1. **Cobrou que eu tinha citado `publishedmanifest.go:332` (`os.Stat` + `IsNotExist`) de
   grep sem ter lido, e que o caso "`public/` AUSENTE" podia ter early-return silencioso.**
   Li: aquele `:332` é de `emptyManifestOrphanPublicHTMLIssues`, o caminho de manifesto
   VAZIO — não governa nada aqui. O caminho real é `:177` →
   `collectPublicFiles` → `filepath.WalkDir` num diretório inexistente devolve erro →
   `:178-180` emite `published_manifest_public_scan_failed`, código **fora** de
   `staticArtifactOnlyIssueCodes`, logo **blocking na primeira ocorrência**. O achado #1
   ficou mais forte, não mais fraco, e agora tem as DUAS variantes provadas.
2. **Cobrou exagero na severidade do achado #3.** Correto, e corrigi com aritmética: os
   residentes de hoje somam 5.645.386.380 B, abaixo dos 9.663.676.416 B do teto, e
   continuariam abaixo na GPU porque `size` é pegada total. O dia um **não** começa
   pausado; o que pausa é o primeiro par grande — que é exatamente o que a migração existe
   para permitir. A ordem (6 antes de 7) sobrevive; a urgência virou honesta.
3. **Cobrou o custo de atestação do passo 6.** Medido com a linha que o contrato indica:
   `internal/ollama` e `internal/cerebro` **não** estão no grafo de `v2ingest` → sem
   `generate`, sem atestação, sem os ~10 min. Mas `internal/publishedmanifest` **está** —
   registrei o alerta para quem for mexer nos tetos de boot. Isso **removeu** um custo que
   eu ia carregar por precaução.
4. **Cobrou a bifurcação que eu não tinha escrito: NVMe migra ou SO reinstalado.** Virou o
   passo **−1** da ordem, com a lista do que não viaja em instalação nova, e a ressalva de
   que a refutação do driver 610 é condicional ao NVMe ir. Acrescentei também a instalação
   do Ollama (39,5 MB + 2,1 GB de runners) à tabela de transporte, fixada em 0.33.3, porque
   o achado do `sm_120a` é deste build e se reinstalar tem de ser re-medido pelo mesmo grep.
5. **Cobrou dois buracos de inventário.** `v2_artifact_vault/{objects,retained}` medidos
   (63 MB + 94 MB — o comentário do `.gitignore` fala em "muitos GiB" e hoje não é o caso),
   e o produtor do GOCACHE procurado em 8 lugares mais (`.git/hooks`, `~/.claude/hooks`,
   `~/.bashrc`, `~/.profile`, `env`): **nenhum hit**, então "não medido" ficou com o método
   registrado em vez de solto.
6. **Não bloqueante que ele levantou e eu medi em parte:** `CONFIG_X86_AMD_PSTATE=y` neste
   kernel 6.1.0-52 (hoje rodando `intel_pstate`); se o `amd_pstate` liga num Zen 5 sob 6.1
   continua **não medido**, e virou verificação nomeada do passo −1.
