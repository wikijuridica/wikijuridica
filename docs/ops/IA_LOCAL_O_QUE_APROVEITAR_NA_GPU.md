# IA local — o que aproveitar, o que aposentar e como migrar quando a GPU chegar

**Frente P12 de `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`.**
Escrito em **2026-09-16**, na máquina velha, com a placa ainda **não** instalada.

Destino imediato: **RTX 5060 Ti 16 GB + 32 GB DDR5 + Ryzen 7 9800X3D**. *(2026-09-23: o dono informa Ryzen 7 7800X3D; resolve-se por lscpu no 1º boot da nova — os dois têm 8c/16t e 96 MB de L3, e as contas não mudam)* Mas este
documento é escrito para valer em **qualquer** servidor futuro: o que está fixado aqui é
**o método e a ordem dos passos**, não o modelo da placa. Onde um número depende do
hardware, ele aparece como *fórmula com o coeficiente declarado*, e o dia um substitui a
estimativa por medição.

## Como ler este documento

Três marcas, e elas são levadas a sério em todas as tabelas:

- **MEDIDO** — número primário desta casa, com data e comando ao lado. Vale como fato.
- **PROJETADO** — aritmética explícita a partir de um número medido. Vale como hipótese.
- **NÃO MEDIDO** — não se fecha aqui com honestidade; fica na lista final, com o comando
  que o fecha no dia um.

Regra 19 do plano, que este documento obedece: **o contrato diz onde medir, não quanto é.**
Nenhum número de estado aparece sem a data e o comando que o produz.

---

## 1. O que a GPU muda, e o que ela não muda

**A GPU é para a ALIMENTAÇÃO, não para o serving.** O portal serve o acervo estático
direto do disco pelo nginx; o Go só atende rota dinâmica. Nada disso encosta em modelo de
linguagem, e nada disso melhora com placa de vídeo.

| grandeza | valor | data | comando |
|---|---|---|---|
| requisições/dia na borda (bruto) | **88.033** | 2026-09-15, citado na regra 15 do plano | `./tools/check-edge-traffic` |
| destas, aquecimento gerado pelo próprio servidor | **~59.000/dia** | declarado no cabeçalho da própria ferramenta | idem — a série separa em coluna distinta |
| p50 de latência na origem | **3,1 ms** | citado no §P12; **não re-medido nesta sessão** | `./tools/generate-live-route-latency-evidence` |

**O número bruto de 88 mil inclui o aquecimento** — o cabeçalho de `check-edge-traffic`
diz isso com todas as letras, e a série tem colunas separadas para tráfego real e para
aquecimento. A conclusão não muda em nenhuma das duas leituras: **servir não precisa de
GPU**, e nada neste documento autoriza tocar no caminho de serving por causa da placa.

O que a GPU compra é a **capacidade de refazer**. A extração é dominada pelo *prefill*, e
prefill é limitado por **cálculo**, não por banda — é a metade da conta que mais melhora
com placa. Corpus que se pode reprocessar sob prompt novo é corpus que se pode **auditar**;
hoje reprocessar é proibitivo, e é por isso que o prêmio não é vazão.

---

## 2. Os quatro bloqueadores de dia um

Cada um vira passo do protocolo da §7. Nenhum deles é opcional, e **três deles se
resolvem antes de o cérebro subir**.

### 2.1 O cliente é cego para `size_vram` e `context_length`

**MEDIDO 2026-09-16**, `curl -s http://127.0.0.1:11434/api/ps`:

```json
{"models":[{"name":"qwen3.5:4b","model":"qwen3.5:4b","size":3227894413,
  "digest":"2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
  "details":{"parameter_size":"4.7B","quantization_level":"Q4_K_M"},
  "expires_at":"2026-09-16T08:44:16.023680789-03:00",
  "size_vram":0,"context_length":8192}]}
```

O struct que lê essa resposta é `internal/ollama/cliente.go:275-280`:

```go
type Residente struct {
    Nome         string    `json:"name"`
    Modelo       string    `json:"model"`
    TamanhoBytes int64     `json:"size"`
    Ate          time.Time `json:"expires_at"`
}
```

Quatro campos. `size_vram` e `context_length` **não estão ali**, e `encoding/json`
descarta campo desconhecido **em silêncio** — é exatamente por isso que o struct
"funciona" e mesmo assim não enxerga nada. Confirmado por `strings` no binário do Ollama
(8 ocorrências de `size_vram`), registrado no §P12.

**Semântica, para não errar a leitura no dia um:**

| campo | significa |
|---|---|
| `size` | total do residente — **VRAM + RAM somadas** |
| `size_vram` | a **parcela** que está em VRAM |
| `size - size_vram` | a parcela que ficou em RAM do host |
| em CPU puro | `size_vram == 0`, que é o que se mede aqui hoje |

⇒ **Passo de dia um:** acrescentar os dois campos ao struct **antes** de re-derivar o
teto. Sem eles, a guarda continua somando uma grandeza só, e nenhuma decisão de VRAM é
observável pelo cérebro.

### 2.2 O teto de residentes tem de ser re-derivado, e o predicado óbvio está errado

Três correções, todas do §P12, e duas medições novas desta sessão.

**(a) Erro de unidade — a guarda de hoje NÃO barra o par que se acreditava barrar.**
`internal/cerebro/saude.go:92` define `TetoBytesResidentesPadrao int64 = 9 << 30`.

```
9 << 30 = 9 × 2^30 = 9.663.676.416 B = 9,664 GB decimais
```

Pesos em disco **MEDIDOS 2026-09-16** (leitura dos manifests em
`/usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/*/*`):

Os digests abaixo são **completos, 64 hexadecimais** — é este o registro que torna "o
mesmo modelo nas duas máquinas" verificável (§7.1, item 5). O comando que os reemite
está na §13.

| modelo | digest do blob (é o sha256) | bytes |
|---|---|---|
| `qwen2.5-coder:14b` | `sha256:ac9bc7a69dab38da1c790838955f1293420b55ab555ef6b4615efa1c1507b1ed` | 8.988.110.784 (8,988 GB) |
| `qwen3.5:9b` | `sha256:dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c` | 6.594.462.816 (6,594 GB) |
| `qwen3-embedding:8b` | `sha256:3fcd3febec8b3fd64435204db75bf0dd73b91e8d0661e0331acfe7e7c3120b85` | 4.676.804.928 (4,677 GB) |
| `qwen3.5:4b` | `sha256:81fb60c7daa80fc1123380b98970b320ae233409f0f71a72ed7b9b0d62f40490` | 3.389.971.840 (3,390 GB) |
| `qwen3:4b` | `sha256:3e4cb14174460404e7a233e531675303b2fbf7749c02f91864fe311ab6344e4f` | 2.497.280.480 (2,497 GB) |
| `qwen3-embedding:4b` | `sha256:2b0cf8f17b4c723c27303015383c27ec4bf2d8314bb677d05e920dd70bb0f16b` | 2.496.703.776 (2,497 GB) |
| `qwen3-embedding:0.6b` | `sha256:06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439` | 639.150.592 (0,639 GB) |
| `wj-extracao-sonda:latest` | `sha256:81fb60c7daa80fc1123380b98970b320ae233409f0f71a72ed7b9b0d62f40490` | 3.389.971.840 — **o mesmo blob do `qwen3.5:4b`** |

Logo, 14b + 0.6b = 9.627.261.376 B = **9,627 GB**, contra o teto de **9,664 GB**:
**passa, por 36,4 MB.** O par que o comentário da guarda diz barrar, ela **não** barra.

O risco existe, mas por **outros** pares: 14b + 4b = 12,378 GB; 9b + 4b = 9,984 GB;
14b + embedding 4b = 11,485 GB. Esses três estouram.

**MEDIÇÃO NOVA, 2026-09-16, e ela torna o "por 36 MB" ainda mais frágil:** a guarda não
soma bytes de blob, soma o campo `size` de `/api/ps`. E para o `qwen3.5:4b`:

```
size (/api/ps)    3.227.894.413 B   =  3,0062 GiB
blob em disco     3.389.971.840 B   =  3,1572 GiB
size / blob       0,9522  →  size está 4,78% ABAIXO dos pesos em disco
```

⇒ **A margem de 36,4 MB (0,38% do teto) está dentro do ruído da grandeza que a guarda de
fato lê.** Ela não é uma folga confiável em nenhuma das duas direções, e nenhuma decisão
deve se apoiar nela.

**(b) O predicado de spill pausaria o cérebro HOJE, para sempre.** Neste host CPU-only,
`size_vram < size` é verdadeiro em **todo** residente — `size_vram` é sempre 0. E o
predicado oposto, `0 < size_vram < size`, erra para o outro lado: **com placa instalada,
`size_vram == 0` significa fallback total para CPU**, que é pior que spill parcial e é
precisamente o estado que se quer detectar.

⇒ **O predicado tem de ser gated por configuração** — "existe GPU declarada nesta
máquina?" —, nunca pelo valor do campo sozinho. Um campo cujo valor 0 significa duas
coisas opostas em duas máquinas diferentes não pode ser o único critério.

**(c) A guarda já mede a grandeza errada, hoje — e agora são duas observações.**

| observação | `size` | RSS do `llama-server` | cgroup `ollama.service` | RSS/`size` |
|---|---|---|---|---|
| §P12 (n=1) | 3,01 GiB | 4,75 GiB | 5,83 GiB | **1,58×** |
| **esta sessão, 2026-09-16** | **3,0062 GiB** | **5,0496 GiB** | **6,5787 GiB** | **1,680×** |

Comandos da linha nova: `curl -s 127.0.0.1:11434/api/ps` · `awk '/VmRSS/{print $2}'
/proc/<pid do llama-server>/status` · `systemctl show ollama.service -p MemoryCurrent`.

Duas observações, mesma direção, magnitude 1,58–1,68×. A causa provável é o prompt cache,
que `size` não conta (bate com `ollama#18264`). **Continua hipótese** — n = 2 com um único
modelo residente é indício, não população. Mas a consequência para o desenho da guarda já
é segura: **`size` subestima o consumo real em ~1,6–1,7×, e a razão contra o cgroup chega
a 2,19×.**

**⇒ O teto a re-derivar não é "subir o 9 GiB". É parar de apontar uma guarda para duas
memórias.** Com placa, o orçamento se parte em dois, e cada metade tem a sua conta:

```
sum(size_vram)          ≤ 13 GiB    (15 GiB úteis do cartão de 16 − 2 de folga)
sum(size − size_vram)   ≤  2 GiB    (a parcela que sobrou na RAM do host)
```

**E a segunda linha carrega o defeito de (c):** 2 GiB medidos em unidades de `size` são
**~3,2–3,4 GiB de RSS real**, pelo fator 1,6–1,7× acima. Duas saídas honestas, e uma delas
tem de ser escolhida no dia um:

1. **Deflacionar o orçamento** — escrever o teto da parcela em RAM já corrigido pelo fator
   medido, com o fator citado no comentário; ou
2. **Ler `memory.current` do cgroup do `ollama.service`** para a metade em RAM, e deixar
   `/api/ps` responder só pela metade em VRAM.

A opção 2 é a que mede a coisa certa: quem mata o host é o RSS, não o campo `size`. A
opção 1 é a barata. **Nenhuma das duas pode ficar implícita** — o defeito de hoje é
exatamente uma guarda cuja unidade ninguém declarou.

### 2.3 `sm_120` exige CUDA 12.8+, driver ≥ 570.26 e módulos de kernel OPEN

Exigências oficiais, registradas no §P12: `sm_120` (Blackwell) é suportado **a partir do
CUDA 12.8**; driver **≥ 570.26** para o runner v12 e **≥ 580.65.06** para o v13; e os
módulos de kernel têm de ser os **open** — *"Blackwell and later are only supported by the
open kernel modules"*. **Nenhum repositório Debian serve: trixie tem 550.163.**

**A prova de qual runner serve está no disco desta máquina.** Parseando o `.nv_fatbin` dos
runners instalados (§P12):

| runner | conteúdo do fatbin |
|---|---|
| `cuda_v12` | **SASS nativo de sm_120 — 143 cubins** |
| `cuda_v13` | **PTX puro, zero SASS** (começa em sm_75, coerente com o CUDA 13 ter removido Maxwell/Pascal/Volta) |

PTX puro significa **compilação JIT a cada load**. Os dois diretórios existem e são
**MEDIDO 2026-09-16** por `ls /usr/local/lib/ollama/` — `cuda_v12` e `cuda_v13` são,
literalmente, os valores que `OLLAMA_LLM_LIBRARY` seleciona.

⇒ **Remover `OLLAMA_LLM_LIBRARY=cpu` NÃO basta. Tem de virar `OLLAMA_LLM_LIBRARY=cuda_v12`**
— senão o Ollama pode escolher o v13 e pagar JIT em todo carregamento.

### 2.4 `ollama#18232` é bloqueador NOMINAL desta placa

Aberto em **2026-09-04**, exatamente **RTX 5060 Ti 16 GB + Ollama 0.33.3 + runner CUDA
v13**. A memória compartilhada do kernel MMA de *flash attention* escala com `num_ctx`, e
`cudaFuncSetAttribute` falha. **Contorno publicado: `num_ctx` = 2048.**

O drop-in deste projeto (`ops/ollama/ollama.service.d/wikijuridica-tuning.conf`, conferido
contra o serviço vivo com `systemctl show ollama.service -p Environment`, **MEDIDO
2026-09-16**) traz:

```
OLLAMA_CONTEXT_LENGTH=8192      ← 4× o contorno
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
```

**Os dois botões são acoplados:** desligar flash attention **degrada `KV_CACHE_TYPE=q8_0`
para `f16` em silêncio**, dobrando o KV cache e comendo a folga do teto de 13 GiB da §2.2.
Não existe "desligo o flash attention e sigo igual".

**⚠ E aqui está a colisão que este documento não deixa passar em branco.** A §6 lista
`TetoCharsExtracao = 3000` como o **maior ganho de qualidade que a GPU compra**. Os dois
fatos batem de frente:

```
orçamento de contexto de UMA extração, hoje:
  ementa cortada em 3.000 chars   ≈   800 tokens   (comentário de extracao.go:41-49)
  SistemaDaExtracao                ≈   210 tokens   (~800 caracteres, medido no fonte)
  EsquemaDaExtracao (JSON schema)  ≈   100 tokens   (ESTIMATIVA, e provavelmente ZERO:
                                                  o Ollama aplica o esquema como gramática
                                                  via xgrammar, não injetando no prompt.
                                                  A conclusão vale nos dois casos)
  NumPredict (saída)               =   512 tokens   (extracao.go:334; teto de retry 1024)
                                   ------------------
                                   ≈ 1.622 tokens, com pico de 2.134 no retry
```

**Sob o contorno `num_ctx = 2048`, a configuração de hoje já raspa o teto, e
`TetoCharsExtracao` NÃO PODE SUBIR.** Dobrá-lo para 6.000 chars levaria o prompt a
~1.910 tokens de entrada (1.600 de ementa + 210 de sistema + ~100 de esquema) e o
contexto total a **~2.420 com os 512 de saída — acima do teto de 2.048.**

⇒ **Passo de dia um, obrigatório e nesta ordem:** o bug é nominalmente contra o **runner
v13**, e a §2.3 já manda forçar o **v12**. Portanto: **testar se `cuda_v12` evita
`#18232` com `CONTEXT_LENGTH=8192` e `FLASH_ATTENTION=1`.** Só se o teste passar é que
`TetoCharsExtracao` pode subir. **É proibido listar os dois como ganhos independentes.**
Se o v12 também reproduzir o bug, a ordem é: contexto em 2048, `TetoCharsExtracao` fica
onde está, e a subida do teto espera a correção upstream.

---

## 3. A tabela de tok/s, refeita com o método declarado

### 3.1 O coeficiente `k`, e por que ele não é constante de hardware

O §P12 mediu `k` **na própria 5060 Ti**, na mesma bancada e com os mesmos modelos da
página da 4090 que o relatório interno já citava:

| Q4_K_M | 5060 Ti (448 GB/s) | k | 4090 (1.008 GB/s) | k |
|---|---|---|---|---|
| Llama 3.1 8B (4,92 GB) | **59,0 tok/s** MEDIDO | **0,648** | 91,0 MEDIDO | 0,444 |
| Qwen2.5 14B (8,99 GB) | **32,9 tok/s** MEDIDO | **0,660** | 49,1 MEDIDO | 0,438 |

`k` = tok/s × bytes ÷ banda. **A razão de banda entre as placas é 0,444, mas a razão de
desempenho medida é 0,65–0,67: planejar pela banda subestima a máquina nova em ~47%.**
Faixa entre fontes públicas: 0,65 (LocalScore) a 0,85 (ComputingForGeeks, Ubuntu + CUDA
12.8) — degrau sistemático de 1,27–1,29×, provavelmente Linux/CUDA 12.8 contra agregado
que inclui Windows. **Este documento adota 0,65, a ponta conservadora do medido.**

**Corroboração que nenhuma análise anterior fez** — derivar `k` de cada célula da linha
"14 B Q4 (9 GB)" do próprio `RELATORIO_HARDWARE_SERVIDOR_20260909.md` §2.1, por
`k = tok/s × 9 ÷ banda`:

| linha do relatório | banda | tok/s impresso | `k` implícito |
|---|---|---|---|
| DDR4-2400 single (esta máquina) | 18 | 1,85 MEDIDO | **0,925** |
| DDR5-6000 dual (AM5) | 85 | 8,5 | 0,900 |
| EPYC 7003, 8 canais | 70 | 7 | 0,900 |
| Strix Halo unificado | 256 | 14 | 0,492 |
| EPYC 9004, 12 canais | 475 | 32 | 0,606 |
| RTX 3090 | 936 | 46 | 0,442 |
| RTX 4090 | 1.008 | 49,1 MEDIDO | 0,438 |
| RTX 5090 | 1.792 | 78 | 0,392 |

**`k` agrupa por CLASSE de hardware, e NÃO forma curva monotônica.** Esta frase é uma
retratação, escrita aqui porque a tabela acima refuta o que uma leitura apressada dela
sugere:

| classe | banda | `k` |
|---|---|---|
| CPU de banda baixa | 18–85 GB/s | **0,90 – 0,93** |
| memória larga sem GPU | 256–475 GB/s | **0,49 – 0,61** — e **a ordem se inverte aqui**: a Strix Halo a 256 GB/s dá 0,492 e o EPYC 9004 a 475 GB/s dá 0,606, *mais alto com mais banda* |
| GPU de topo | 936–1.792 GB/s | **0,39 – 0,44** |

⇒ **É proibido ler isto como "`k` cai monotonicamente com a banda".** Ele não cai: entre
256 e 475 GB/s ele **sobe**. O que a tabela sustenta é mais modesto, e é o suficiente:
**`k` é propriedade da classe de hardware, não constante do método** — e a frase do §P12
("placa com menos banda satura melhor") vale como comparação **entre GPUs**, que é onde ela
foi medida, não como lei geral.

E o **`k` = 0,65 medido na 5060 Ti a 448 GB/s não "cai onde a curva o põe": ele fica ACIMA
dos dois pontos de banda vizinha** (0,492 e 0,606). Isso é o que se mede, não o que se
interpola. O que autoriza usar 0,65 como projeção é ele ter sido **medido nesta placa, em
dois modelos** — não caber numa curva, que não existe.

### 3.2 Regime 1 — o modelo cabe INTEIRO na VRAM

Método, explícito: **tok/s = k × B ÷ bytes**, com `k = 0,65` e `B = 448 GB/s`
(GDDR7, 128 bits). Constante única: **0,65 × 448 = 291,2**.

Bytes = **os pesos do blob**, medidos nesta máquina em 2026-09-16 (§2.2) — cada token
gerado lê o modelo inteiro.

| modelo | bytes (GB) | hoje, CPU | aritmética | GPU, residente | ganho |
|---|---|---|---|---|---|
| `qwen3-embedding:0.6b` | 0,639 | 40–74 tok/s de **prefill** MEDIDO | 291,2 ÷ 0,639 | **455,7** ⚠ | ver nota |
| `qwen3:4b` / `qwen3-embedding:4b` | 2,497 | — | 291,2 ÷ 2,497 | **116,6** PROJETADO | — |
| **`qwen3.5:4b`** (extração) | 3,390 | **5,2** MEDIDO | 291,2 ÷ 3,390 | **85,9** PROJETADO | **16,5×** |
| `qwen3-embedding:8b` | 4,677 | — | 291,2 ÷ 4,677 | **62,3** PROJETADO | — |
| `qwen3.5:9b` | 6,594 | **2,9** MEDIDO | 291,2 ÷ 6,594 | **44,2** PROJETADO | **15,2×** |
| `qwen2.5-coder:14b` | 8,988 | **1,85** MEDIDO | 291,2 ÷ 8,988 | **32,4** ≈ **32,9 MEDIDO** | **17,5×** |

Origem dos "hoje": `data/ops/ia_local_daily.jsonl`, 2026-09-08/09, comentários de
`ops/ollama/ollama.service.d/wikijuridica-tuning.conf` e `internal/cerebro/extracao.go:41-49`.
Comando que os relê: `./bin/cerebro status` e `./tools/check-extracoes-dispositivos`.

**Duas correções que esta tabela faz contra a do §P12:**

1. **`qwen3.5:4b` dá ~86 tok/s, não ~79.** A tabela antiga imprimia 79 com bytes de 3,4 GB,
   e 291,2 ÷ 3,4 = 85,6. Os ~79 não fecham com o próprio método declarado — eram resíduo de
   uma derivação anterior por banda. Valor correto: **85,9** com os 3,390 GB medidos.
2. **A linha do 14b não é projeção, é praticamente medição.** 291,2 ÷ 8,988 = **32,4**, e a
   bancada da própria 5060 Ti mediu **32,9** num Qwen2.5 14B Q4_K_M de 8,99 GB — mesma
   arquitetura, mesma quantização, mesmo tamanho. A projeção erra por **1,5% para baixo**.
   É a melhor âncora que esta tabela tem.

⚠ **Nota sobre os modelos de embedding.** `tok/s` de *decode* é a métrica errada para eles:
embedding não gera token, só faz prefill. Os 455,7 e 62,3 são o que a fórmula devolve, e
**não descrevem o trabalho real**. O que importa para `embed_pagina` é o throughput de
prefill em páginas por segundo. **NÃO MEDIDO** — mede-se no dia um com
`./bin/cerebro enfileirar-medicao --modo embed --modelo qwen3-embedding:0.6b --amostra 8`.

### 3.3 Regime 2 — o modelo TRANSBORDA da VRAM

**Aqui a banda da VRAM deixa de valer, e o §P12 misturava os dois regimes sem declarar
qual.** A fração que ficou na RAM anda a **~80 GB/s** de DDR5 dual channel, não a 448.

Método, explícito — **média harmônica das bandas ponderada pelas frações do modelo**:

```
B_efetiva = 1 / ( f_vram / B_vram  +  f_ram / B_ram )
tok/s     = k × B_efetiva ÷ bytes_totais
```

Orçamento de VRAM assumido: **13 GiB = 13,959 GB** para pesos + KV (§2.2).

**Denso 32B Q4 — 20 GB de pesos, KV a 8k q8_0 ≈ 1 GB**

```
pesos em VRAM = 13,959 − 1 = 12,96 GB  →  f_vram = 0,648
pesos em RAM  = 20 − 12,96 = 7,04 GB   →  f_ram  = 0,352
B_efetiva = 1 / (0,648/448 + 0,352/80) = 1 / (0,0014464 + 0,004400) = 171,0 GB/s
tok/s     = 0,65 × 171,0 ÷ 20 = 5,56
```

**Denso 70B Q4 — 40 GB de pesos, KV a 8k q8_0 ≈ 1,7 GB**

```
pesos em VRAM = 13,959 − 1,7 = 12,26 GB  →  f_vram = 0,3065
pesos em RAM  = 40 − 12,26 = 27,74 GB    →  f_ram  = 0,6935
B_efetiva = 1 / (0,3065/448 + 0,6935/80) = 1 / (0,000684 + 0,008669) = 106,9 GB/s
tok/s     = 0,65 × 106,9 ÷ 40 = 1,74
```

**E agora a parte honesta: este método é um PISO, não uma projeção.** Testado contra o
único ponto de spill medido que o repositório cita — `RELATORIO_HARDWARE_SERVIDOR_20260909.md`
§4, RTX 3090 24 GB rodando 70B Q4 com 40% em RAM, **medido em 5,2 tok/s**:

```
f_vram = 0,6 · B_vram = 936 · f_ram = 0,4
  com RAM a 40 GB/s (DDR4-3200 dual, efetivo):
    B_ef = 1/(0,6/936 + 0,4/40)  =  93,98  →  0,65 × 93,98 ÷ 40 = 1,53 tok/s
  com RAM a 80 GB/s (hipótese generosa):
    B_ef = 1/(0,6/936 + 0,4/80)  = 177,3   →  0,65 × 177,3 ÷ 40 = 2,88 tok/s
```

**O método prevê 1,53–2,88; o medido é 5,2. Ele subestima o spill em 1,8× a 3,4×.**

Causas plausíveis (nenhuma verificada aqui): o `llama.cpp` mantém KV e tensores mais lidos
em VRAM e transborda camadas inteiras, o `-ngl` real pode ter sido maior que os 60%
supostos, e a banda de RAM daquela máquina não está publicada.

⇒ **Toda linha de spill deste documento é NÃO MEDIDA.** Os números 5,56 e 1,74 são o que a
aritmética declarada devolve, servem como **piso**, e o valor real fica entre eles e
~3× isso. Mede-se no dia um, e o comando está na §11.

### 3.4 Regime 3 — MoE, que a tabela do §P12 subestima

Num 30B-A3B, apenas ~3B parâmetros são lidos por token — **~2 GB em Q4**, contra os 18,6 GB
do modelo inteiro. Se todo especialista roteado estiver em VRAM:

```
tok/s = 291,2 ÷ 2 = 145,6
```

**Mas esse número é um TETO SUPERIOR, e ele não se realiza nesta placa por conta própria.**
Um Qwen3-30B-A3B Q4_K_M pesa ~18,6 GB e **não cabe** no orçamento de 13,959 GB da §3.3:
~75% dos pesos entram, ~4,6 GB de especialistas ficam na RAM. Toda vez que o roteador
escolhe um especialista frio, o token paga 80 GB/s em vez de 448.

A vazão real é, portanto, função da **taxa de acerto de especialista em VRAM**, que
depende do texto e do roteador e é **impossível de estimar a priori**.

⇒ **MoE: NÃO MEDIDO.** O que se pode afirmar com honestidade é a forma: *MoE é a classe que
melhor casa com esta máquina, porque desacopla capacidade (30B) de bytes lidos por token
(~2 GB); o ganho real depende de quantos especialistas cabem, e isso se mede, não se
projeta.* Os 96 MB de L3 do 9800X3D ajudam roteamento e prefill — também **não medido**. *(2026-09-23: o dono informa Ryzen 7 7800X3D; resolve-se por lscpu no 1º boot da nova — os dois têm 8c/16t e 96 MB de L3, e as contas não mudam)*

### 3.5 O prefill, que é onde está o prêmio

O §12 do contrato registra que a extração é **dominada pelo prefill**: 700–1.100 tokens de
entrada contra ~100 de saída. **MEDIDO** nesta máquina (`data/ops/ia_local_daily.jsonl`,
tipo `extrair_dispositivos`, modelo `qwen3.5:4b`, 2026-09-09):

- prefill (`prompt_tok_s`): **13,7 a 19,3 tok/s**, a maioria entre 15 e 19
- decode (`eval_tok_s`): **~5,2 tok/s**, estável

O §P12 cita ganho de **74–130× no prefill** contra 17–23× no decode, a partir de fontes
públicas. **Esses 74–130× não foram re-verificados nesta sessão** e ficam marcados como
**NÃO MEDIDO** — mede-se no dia um, e é a medição que mais muda o desenho do cérebro,
porque prefill é limitado por **cálculo**, e cálculo é o que a placa realmente entrega.

---

## 4. Correção ao `RELATORIO_HARDWARE_SERVIDOR_20260909.md`

O relatório está em **`docs/ops/`**, não em `docs/goal/` — a frente P12 escreve o caminho
errado, e quem for procurá-lo por lá não o acha.

O §2.1 enuncia: *"tok/s ≈ 0,85–0,90 × banda ÷ bytes do modelo"*, calibrado em **dois
sistemas de CPU** (esta máquina a 0,87 e um Ryzen 5950X a 0,85).

**O §P12 diz que aplicar 0,85 aos 448 GB/s superestimaria o ganho em ~2×. Isso é
verdadeiro como afirmação sobre a REGRA ENUNCIADA, e é preciso ser exato sobre o que ele
NÃO quer dizer:** as células de GPU daquela mesma tabela **não** foram construídas com
0,85. A derivação célula a célula da §3.1 acima mostra `k` implícito de **0,39 a 0,44** nas
linhas de GPU, contra **0,90 a 0,93** nas de CPU. Os números da tabela estão internamente
coerentes; **é o texto da regra que não se transfere.**

O defeito real, portanto, é este: **`k` é função da banda, não constante do método.** Quem
ler a regra enunciada e a aplicar a um cartão novo — como o §2.1 convida a fazer — vai
errar para cima em ~2×. Quem copiar as células de GPU acerta a ordem de grandeza e erra
para baixo em ~47% no caso específico da 5060 Ti, que satura melhor.

**Nota de superação aplicada ao relatório** (edição pontual, nada apagado): parágrafo
datado sob o §2.1 e uma linha na §8 (Proveniência), onde a regra é repetida como
proveniência do método.

---

## 5. O que fica obsoleto no dia um, com arquivo e linha

Nada desta lista se apaga hoje. Cada item é uma constante ou variável cujo **motivo
declarado deixa de existir** quando a máquina muda — e a maioria delas tem, no próprio
comentário, a frase que a amarra ao hardware velho.

| o que | onde | por que morre | o que entra no lugar |
|---|---|---|---|
| `OLLAMA_LLM_LIBRARY=cpu` | `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` | enquanto existir, a placa **não é usada** | **`cuda_v12`** — não basta remover (§2.3) |
| `CargaMax = 12` → `CargaMaxPadrao` | `internal/cerebro/saude.go:89`, doc em `:50-60` | o comentário deriva o número de *"o próprio Ollama roda com 4 threads nos 4 núcleos desta máquina"* — **frase que descreve máquina que deixará de existir** (9800X3D tem 8 núcleos / 16 threads, e na GPU o `llama-server` quase não usa CPU) *(2026-09-23: o dono informa Ryzen 7 7800X3D; resolve-se por lscpu no 1º boot da nova — os dois têm 8c/16t e 96 MB de L3, e as contas não mudam)* | re-derivar do loadavg medido com o cérebro trabalhando sozinho na máquina nova |
| `PrazoPorTarefa = 300 s` | `internal/cerebro/worker.go:200-205` | comentário: *"a extração por qwen3.5:4b mede ~90-105 s POR TAREFA"*. Ver a aritmética abaixo: vira **115–135× o tempo real** | re-derivar como ~3× o p99 medido na máquina nova |
| `OLLAMA_KEEP_ALIVE=15m` | drop-in do Ollama | existe para não repagar o load; o load hoje custa **21–48 s** e cai junto com tudo | re-derivar depois de medir `load_duration` na GPU |
| `OLLAMA_MAX_LOADED_MODELS=2` + teto de 9 GiB | drop-in + `saude.go:92` | a restrição migra de **RAM do host** para **VRAM**, e passa a ter duas contas (§2.2) | `sum(size_vram) ≤ 13 GiB` **e** `sum(size − size_vram) ≤ 2 GiB` (com a correção de unidade da §2.2c) |
| `OLLAMA_NUM_PARALLEL=1` | drop-in do Ollama | escolhido porque a fila do Ollama serializava e o cliente MCP corta em 60 s; com VRAM sobrando, slots paralelos passam a caber — **ao custo de um KV cache por slot**, que disputa o mesmo orçamento de 13 GiB | subir com o custo de KV declarado, não por padrão |
| **`TetoCharsExtracao = 3000`** | `internal/cerebro/extracao.go:41-49` | o comentário deriva o corte do **custo de prefill** (13,7–19,3 tok/s). Com prefill 74–130× mais rápido, **o corte deixa de ser econômico e passa a ser só perda de informação**. É o **maior ganho de qualidade que a GPU compra** | **⚠ BLOQUEADO por `#18232`** — só sobe depois do teste da §2.4 |
| `NumPredict = 512` | `internal/cerebro/extracao.go:334`, teto de retry `tetoMaximoDaExtracao = 1024` em `:813` | 512 existe para economizar decode; na GPU decode custa ~1/17 | começar em 1024 e medir `done_reason == "length"` |
| `MemoryMax=12G` / `MemorySwapMax=2G` / `OOMScoreAdjust=800` | drop-in do Ollama | os três foram derivados do incidente de **2026-09-08 12:04:53**, em que dois residentes somaram 16 GB num host de 19,4 GiB. Com 32 GB e pesos em VRAM, o RSS do host despenca | re-derivar do RSS medido na máquina nova; o `OOMScoreAdjust` só se mantém se o earlyoom continuar instalado |
| `CPUWeight=60` / `Nice=5` / `Slice=wikijuridica_alimentacao.slice` (peso 20) | drop-in do Ollama + `ops/systemd/` | derivados da contenção medida em 4 núcleos: pre-commit a **75 s** com o cérebro trabalhando contra **29 s** parado (2026-09-09). Em 8 núcleos com inferência na GPU, a contenção de CPU praticamente desaparece | **repetir o experimento do lock na máquina nova** antes de mexer — é a única forma de saber se a contenção sumiu ou só mudou de lugar |
| `--max-lote 3` | `ops/systemd/wikijuridica-cerebro.service`, `ExecStart` | derivado de *"um lote de 8 páginas no 0.6b leva 100-170 s nesta CPU"* contra o corte de 60 s do cliente MCP | na GPU o mesmo lote cai para a casa de 10–17 s (**PROJETADO** pelo fator da §3.2); re-derivar do tempo medido, não do fator |

### 5.1 A aritmética do `PrazoPorTarefa`, que não se repete de cor

O §P12 afirma "viraria 100× o tempo real". Eis a conta, com as suposições declaradas.

Uma tarefa de extração hoje: ~800 tokens de prompt e ~100 de saída.

```
HOJE (MEDIDO):    prefill 800 ÷ 17 tok/s   = 47,1 s
                  decode  100 ÷ 5,2 tok/s  = 19,2 s
                                            ------- 66,3 s de cálculo
                  medido fim a fim: 90-105 s (a diferença é load + overhead do lote)
                  → prefill é 71% do cálculo, o que confere com o "⅔" do §12

GPU (PROJETADO, prefill 74× e decode ×16,5 da §3.2):
                  prefill 800 ÷ (17 × 74)   = 0,64 s
                  decode  100 ÷ 85,9        = 1,16 s
                                             ------- 1,80 s
GPU (PROJETADO, prefill 130×):
                  prefill 800 ÷ (17 × 130)  = 0,36 s
                  decode                    = 1,16 s
                                             ------- 1,52 s

PrazoPorTarefa = 300 s  ÷  1,52 a 1,80 s  =  167× a 197× o tempo de cálculo
```

Mesmo somando um overhead de lote tão grande quanto o de hoje (~35 s escalados por 17× ≈
2 s), o prazo fica em **~90× a 115×** o tempo real. **O "100×" do §P12 é a ordem de
grandeza certa**, e a conta acima é o que a sustenta. As duas suposições que a carregam
— prefill 74–130× e o ⅔/⅓ da divisão de custo — são as duas coisas que o dia um mede.

---

## 6. O parágrafo do §12 do `CLAUDE.md` que fica superado

**Este documento NÃO edita o `CLAUDE.md`.** O texto abaixo é a redação proposta, pronta
para o titular aplicar, e **só entra em vigor quando o baseline da §7 e o Gate 1 da §8
estiverem gravados** — não na data da compra, não na data da instalação da placa.

O parágrafo vigente do §12 fixa:

> *"Trabalho em massa (embeddings, extração, classificação) vai em modelos de 0,6 a 4B; o
> 14b só em lote noturno com entrada curta."*

Texto de superação, no formato que o contrato exige (data, motivo, nada apagado):

> **Até 2026-09-16 este parágrafo restringia o trabalho em massa a modelos de 0,6 a 4B e
> confinava o 14b a lote noturno com entrada curta. A restrição fica superada na data em
> que o Gate 1 da migração for gravado, e o motivo é medido, não preferido: ela derivava
> da banda de memória do host antigo (~18 GB/s de DDR4 single channel), onde o 14b rendia
> 1,85 tok/s e uma tarefa de extração custava 90–105 s. Com os pesos residentes em VRAM a
> 448 GB/s, o mesmo 14b mede 32,9 tok/s na bancada da própria placa — mais rápido do que o
> `qwen3.5:4b` rodava no host antigo — e o custo de prefill, que dominava a extração, cai
> uma a duas ordens de grandeza. O critério deixa de ser o TAMANHO do modelo e passa a ser
> o ORÇAMENTO DE MEMÓRIA declarado em duas contas (`sum(size_vram) ≤ 13 GiB` e
> `sum(size − size_vram) ≤ 2 GiB`) mais o veredito do bake-off pareado, que mede trabalho
> feito (`dispositivos_por_acordao`) contra invenção (`descarte_pct`), nunca velocidade.
> Velocidade passa a ser piso, não prêmio. O parágrafo anterior não se apaga: ele descreve
> corretamente a máquina que o projeto operou até esta data.**

---

## 7. Protocolo de migração

### 7.1 ANTES de desligar a máquina velha — nada disto se refaz depois

Esta lista é a que se perde para sempre se for esquecida. Cada item existe porque, sem
ele, uma comparação futura deixa de ser interpretável.

1. **Gabarito de atribuição.** O conjunto rotulado contra o qual toda extração futura se
   mede. Sem ele, "melhorou" é opinião.
2. **Correções determinísticas do P5, medidas na máquina velha.** O que o parser resolve
   sem LLM tem de ter o seu número **antes**, ou o ganho do parser e o ganho da placa se
   confundem num só.
3. **Piso de determinismo — é o Gate 0, e é o item mais esquecido da lista.** Duas passadas
   do **mesmo modelo**, na **mesma máquina**, a **temperatura 0**, sobre o **mesmo
   conjunto**. A diferença entre as duas passadas é o ruído do próprio sistema. **Sem esse
   piso, nenhuma diferença A/B futura é interpretável** — não se sabe se 0,9 contra 1,0
   dispositivo por acórdão é sinal ou é o mesmo modelo discordando de si mesmo.
4. **Baseline de extração com o conjunto COMPLETO de métricas.** Não bastam descarte, URN e
   cortadas: os três **aprovariam um modelo que responde sempre `{"dispositivos":[]}`**
   (descarte 0%, URN 100%, 0 cortadas). Tem de incluir `dispositivos_por_acordao` e
   `eval_tokens_mediano`. O produtor é `tools/generate-comparacao-modelos-extracao`, que já
   grava exatamente esse conjunto em
   `data/ops/extracao_dispositivos_amostra_daily.jsonl`.
5. **`sha256` do blob de cada modelo e `ollama --version`.** **Sem isto, "o mesmo modelo"
   nas duas máquinas é fé, não fato** — uma tag do Ollama pode apontar para outro blob a
   qualquer momento, e a diferença apareceria como "a GPU mudou a qualidade".
   **Custo zero, e já está feito nesta sessão:** *o nome do arquivo de blob **é** o sha256*
   (`/usr/share/ollama/.ollama/models/blobs/sha256-<digest>`), e a tabela da §2.2 traz os
   oito digests **completos, 64 hexadecimais**, medidos em 2026-09-16, e o comando que os
   reemite está na §13. `ollama --version` = **0.33.3**, MEDIDO 2026-09-16.
6. **O experimento do lock.** Pre-commit **com** e **sem** o cérebro trabalhando: **75 s
   contra 29 s**, medido em 2026-09-09. É a linha de base da contenção de CPU, e é o único
   jeito de saber, depois, se a contenção sumiu com a GPU ou só mudou de lugar (para o
   barramento PCIe, por exemplo).
7. **Cópias dos ledgers e `VACUUM INTO` da fila.** `data/ai/`, `data/ops/ia_local_daily.jsonl`
   e `data/ai/fila.sqlite`. O `VACUUM INTO` produz cópia consistente **sem parar o daemon**
   — copiar o arquivo `.sqlite` a quente com o worker escrevendo dá banco corrompido.

### 7.2 DEPOIS, e a ordem importa

Cada passo só começa quando o anterior mediu verde. **Inverter a ordem custa o que a
§2.2 e a §2.4 descrevem.**

1. **Driver e `nvidia-smi`.** Módulos de kernel **open**, driver **≥ 570.26**, CUDA ≥ 12.8
   (§2.3). Hoje, **MEDIDO 2026-09-16**, `nvidia-smi` existe em `/usr/bin` e falha com
   *"couldn't communicate with the NVIDIA driver"* — não há driver. Critério de passagem:
   `nvidia-smi` lista a placa e reporta 16 GB.
2. **Só então trocar `OLLAMA_LLM_LIBRARY`.** De `cpu` para **`cuda_v12`**, nunca para
   vazio (§2.3). Conferir no log do Ollama qual runner foi escolhido.
3. **Acrescentar `size_vram` e `context_length` ao struct** de `internal/ollama/cliente.go:275-280`
   e conferir `/api/ps` (§2.1). Critério de passagem: `size_vram > 0` num modelo carregado.
   **`size_vram == 0` com placa instalada é fallback total para CPU — para tudo e volte ao
   passo 2.**
4. **Testar `#18232` sob `cuda_v12`** com `CONTEXT_LENGTH=8192` e `FLASH_ATTENTION=1`
   (§2.4). O resultado deste teste **decide** se `TetoCharsExtracao` pode subir.
5. **Re-derivar o teto de residentes — ANTES de subir o cérebro.** As duas contas da §2.2,
   com a unidade da parcela em RAM resolvida (deflacionar ou ler o cgroup). **Se o cérebro
   subir antes, ele trabalha a noite inteira com uma guarda apontada para a memória
   errada.**
6. **`medir_modelo` em cada modelo.** `./bin/cerebro enfileirar-medicao --modo gerar
   --modelo <m> --prompt <p>` e `--modo embed --amostra 8`. É daqui que sai a tabela de
   tok/s **medida** que substitui a §3 inteira.
7. **Gate 0 e Gate 1** (§8). O Gate 1 é a comparação CPU × GPU do **mesmo** modelo.
8. **Re-derivar as constantes da §5**, cada uma do número que a substitui — nunca por
   fator, sempre por medição.
9. **Gate 2** — o bake-off de modelos, e só agora (§8).
10. **Drenar e reprocessar**, com a armadilha da §9 respeitada.

---

## 8. O critério de adoção, pré-registrado

**Velocidade é piso, não prêmio.** Na GPU todo candidato é rápido; escolher por tok/s
escolheria o pior modelo que responde depressa.

O que decide é **`dispositivos_por_acordao`** (quanto trabalho foi de fato FEITO) contra
**`descarte_pct`** (invenção bruta — item cujo `texto_citado` **não** ocorre literalmente
na ementa), com a **âncora literal como invariante em 100,0000%**.

**O repositório já refutou uma troca por leitura agregada, e o precedente vale como
régua.** Em **2026-09-08**, o `qwen3:4b` apresentava URN de 100% e **extraía metade**:
**0,524 contra 1,0 dispositivo por acórdão**, com descarte **5× maior**. Veredito
registrado: **NÃO TROCAR.** O cabeçalho de `tools/generate-comparacao-modelos-extracao`
guarda a lição em duas frases: o agregado não decide (o ensaio do candidato usava
`--so-sem-referencias`, que seleciona as ementas mais difíceis por construção), e as três
métricas antigas **aprovariam um modelo que responde sempre vazio**.

### Os três gates, em ordem, e nenhum se pula

**Gate 0 — piso de determinismo, na máquina VELHA.**
Duas passadas do mesmo modelo, temperatura 0, mesmo conjunto. Produz **o número abaixo do
qual nenhuma diferença significa nada.** Sem ele, os Gates 1 e 2 são teatro.
*Este gate só existe antes do desligamento. Perdeu, perdeu.*

**Gate 1 — paridade de hardware, MESMO modelo, CPU contra GPU.**
Espera-se saída **praticamente idêntica**. **Divergência acima do piso do Gate 0 é
quantização, kernel ou spill — NÃO é sinal de inteligência**, e tratá-la como melhoria é
o erro que este gate existe para impedir. Reprovar aqui manda de volta para os passos 2–5
da §7.2, nunca para "o modelo novo é melhor".

**Gate 2 — bake-off de modelos, pareado por chave, e só depois dos dois anteriores.**

```
./tools/generate-comparacao-modelos-extracao --a <jsonl do modelo A> \
    --b <jsonl do modelo B> --rotulo <nome do ensaio> [--dry-run]
```

A ferramenta pareia **por chave** — só os acórdãos que os dois lados viram entram na
conta —, e recusa comparar um modelo consigo mesmo. Grava em
`data/ops/extracao_dispositivos_amostra_daily.jsonl`.

**Régua do veredito, pré-registrada aqui para não ser escolhida depois do número:**

| resultado | veredito |
|---|---|
| âncora literal < 100,0000% | **REPROVA**, sem discussão. É fato, não juízo |
| `dispositivos_por_acordao` do candidato abaixo do incumbente além do piso do Gate 0 | **NÃO TROCAR** — é o caso do `qwen3:4b` em 2026-09-08 |
| `descarte_pct` do candidato acima do incumbente | **NÃO TROCAR** |
| trabalho feito igual ou maior **e** descarte igual ou menor | **TROCAR**; velocidade só desempata |
| diferença dentro do piso do Gate 0 | **EMPATE** — fica o incumbente, e o mais barato desempata |

---

## 9. A armadilha do reprocessamento, verificada

**Subir `TetoCharsExtracao` NÃO reprocessa nada.** O mecanismo, lido no código:

- `ImpressaoDoTexto` (`internal/cerebro/extracao.go:831`) — a **identidade da tarefa na
  fila** — hasheia o texto **INTEIRO**, sem corte.
- `TextoSHA256Cortado` (`:860`, doc a partir de `:839`) — o hash gravado em `Extracao.TextoSHA256` — hasheia o
  texto **CORTADO** em `TetoCharsExtracao` runas, que é o que o modelo de fato viu.
- O cache de enfileiramento (`UltimaExtracaoPorChaveEModelo`, usado em
  `cmd/cerebro/main.go:760`) compara contra o **cortado**.
- E `Fila.Enfileirar` usa `INSERT OR IGNORE`: a linha concluída já está lá, sob a mesma
  identidade de tarefa.

Resultado: muda-se o teto, o texto que vai ao modelo passa a ser outro, **e nenhuma tarefa
volta para a fila**. O acervo fica meio extraído sob o teto velho e meio sob o novo, sem
ninguém notar.

**Duas saídas, e uma delas é melhor:**

```
./bin/cerebro reabrir --tipo extrair_dispositivos --concluidas
```

devolve as concluídas do tipo para pendente (`cmd/cerebro/main.go:586-608`). Funciona, mas
**destrói o par de comparação**: a extração velha é sobrescrita e o A/B deixa de existir.

**O caminho certo é rodar sob OUTRO NOME DE MODELO.** A identidade da fila inclui o modelo
(`internal/cerebro/fila.go`), então o mesmo acórdão sob outro nome é tarefa nova — e a
saída já nasce **pareada por chave**, que é exatamente o que o Gate 2 consome.

**E esse caminho já está aberto no disco desta máquina.** **MEDIDO 2026-09-16**: o modelo
`wj-extracao-sonda:latest` aponta para o digest `sha256:81fb60c7daa80fc1123380b98970b320ae233409f0f71a72ed7b9b0d62f40490` — **o mesmo blob do
`qwen3.5:4b`**. Mesmos pesos, identidade de fila diferente. É o instrumento do Gate 1
pronto: rodar `wj-extracao-sonda` na GPU contra o `qwen3.5:4b` já extraído na CPU dá a
comparação de hardware, e `generate-comparacao-modelos-extracao` aceita os dois JSONL
diretamente.

⚠ **Com uma ressalva que se confere ANTES do Gate 1, não depois.** O que é idêntico byte a
byte são os **pesos**. A sonda tem **camada de Modelfile própria** (blob de 11.355 bytes,
datado de 2026-09-09 no diretório de blobs), e Modelfile carrega `template`, `num_ctx` e
parâmetros de sampler. A extração já sobrepõe `temperature`, `think` e `presence_penalty` a
cada chamada (`internal/cerebro/extracao.go:415-428`), então o resíduo é pequeno — mas
`template` ou `num_ctx` divergentes contaminariam a paridade CPU × GPU e apareceriam como
"a GPU mudou a qualidade", que é exatamente o erro que o Gate 1 existe para impedir.

```
ollama show wj-extracao-sonda --modelfile    # conferir contra:
ollama show qwen3.5:4b        --modelfile
```

Havendo divergência em `template` ou `num_ctx`: use o **mesmo** modelo dos dois lados e
separe os JSONL por arquivo, em vez de separar por nome de modelo.

---

## 10. Critério de reversão

**A máquina velha fica de pé** — ligada, com o cérebro capaz de voltar a trabalhar — até
que **as três condições** estejam satisfeitas:

1. **Gate 1 passou** (paridade CPU × GPU dentro do piso do Gate 0);
2. **a fila drenou um dia inteiro sem `ErrPausado`** — nenhuma pausa por saúde, carga,
   lock ou teto de residentes (`./bin/cerebro status`);
3. **a âncora literal continua em 100,0000% num lote de 500 tarefas reais** — não amostra
   conveniente, não prefixo: 500 tarefas do fluxo normal
   (`./tools/check-extracoes-dispositivos --json`).

Falhou qualquer uma: **o cérebro volta para a máquina velha** enquanto a causa é atacada.
Isto não é excesso de cautela — é o que torna a migração reversível, e reversível é o que
permite migrar depressa.

---

## 11. Limites honestos

**16 GB de VRAM não rodam um 70B inteiro.** Q4 são 40 GB de pesos, 46–48 GB com KV a 32k.
Mas com 32 GB de DDR5 ele **roda por offload** — piso calculado de **1,74 tok/s** (§3.3),
provavelmente mais, porque o método é piso. É lote noturno viável: o 14b roda hoje a 1,85.

**32B cabe com offload leve e vira modelo diário.** Piso calculado de **5,56 tok/s**
(§3.3) — mais rápido do que o `qwen3.5:4b` roda **hoje** (5,2), com oito vezes os
parâmetros.

**Contexto longo compete com o tamanho do modelo pelo mesmo orçamento.** KV cache mora na
mesma VRAM que os pesos: um 32B a 32k de contexto paga ~4,3 GB de KV em q8_0, e esses
4,3 GB saem dos 13 GiB da §2.2. **E `KV_CACHE_TYPE=q8_0` só vale enquanto o flash
attention estiver ligado** (§2.4) — desligá-lo dobra o KV em silêncio. As três decisões —
tamanho do modelo, comprimento de contexto e flash attention — são **uma só conta**.

**Servir não precisa de GPU** (§1). A GPU é para a **alimentação**.

**E uma limitação de método, não de hardware:** todo número projetado deste documento
supõe que `k` medido em dois modelos densos Q4_K_M se aplica aos demais. **Isso não foi
verificado para MoE, para quantizações diferentes de Q4_K_M, nem para modelos de
embedding.**

---

## 12. O que este documento NÃO conseguiu fechar

Nomeado, com o comando que fecha cada um no dia um. **O documento vale mais dizendo o que
não sabe.**

| não fechado | por quê | comando que fecha, no dia um |
|---|---|---|
| **Semântica de `size_vram` com placa presente** | a placa não existe aqui; hoje o campo é sempre 0 | acrescentar o campo ao struct e `curl -s 127.0.0.1:11434/api/ps` com modelo carregado |
| **O `k` real desta placa nesta casa** | 0,65 vem da bancada pública da 5060 Ti, não desta instalação | `./bin/cerebro enfileirar-medicao --modo gerar --modelo <m> --prompt <p>` em cada modelo, e recalcular `k = tok/s × bytes ÷ 448` |
| **Se `size` inclui o KV cache quando o modelo está em VRAM** | n = 2 em CPU, sempre 1,6–1,7× abaixo do RSS; em VRAM a contabilidade pode ser outra | comparar `size` e `size_vram` de `/api/ps` com `nvidia-smi --query-gpu=memory.used --format=csv` com o modelo carregado |
| **Se `#18232` se manifesta sob `cuda_v12`** | o bug é nominal contra o v13, e disso depende `TetoCharsExtracao` | subir com `OLLAMA_LLM_LIBRARY=cuda_v12`, `CONTEXT_LENGTH=8192`, `FLASH_ATTENTION=1` e rodar uma extração real |
| **Toda linha de spill (32B, 70B)** | o método harmônico da §3.3 subestima o único ponto medido em 1,8–3,4× | `medir_modelo` com o modelo denso real carregado e `-ngl` declarado |
| **Taxa de acerto de especialista em VRAM (MoE)** | depende do texto e do roteador; não se estima | `medir_modelo` num 30B-A3B real sobre ementas reais |
| **Ganho real de prefill (os "74–130×")** | número de fonte pública, não re-verificado | `prompt_tok_s` de `data/ops/ia_local_daily.jsonl` depois do primeiro lote na GPU |
| **Throughput de embedding em páginas/s** | tok/s de decode é métrica errada para embedding (§3.2) | `./bin/cerebro enfileirar-medicao --modo embed --modelo qwen3-embedding:0.6b --amostra 8` |
| **p50 de 3,1 ms na origem** | citado no §P12; não re-medido nesta sessão | `./tools/generate-live-route-latency-evidence` |
| **Se a contenção de CPU some ou muda de lugar** | 75 s vs 29 s é da máquina velha, em 4 núcleos | repetir o experimento do lock na máquina nova (§7.1, item 6) |

---

## 13. Proveniência

Tudo o que este documento mede foi medido em **2026-09-16**, na máquina velha, sem
reiniciar o Ollama nem o cérebro (havia trabalho em curso). Só leitura.

| medição | comando |
|---|---|
| `/api/ps` cru, com `size_vram` e `context_length` | `curl -s http://127.0.0.1:11434/api/ps` |
| versão do Ollama (0.33.3) | `curl -s http://127.0.0.1:11434/api/version` · `ollama --version` |
| ausência de driver NVIDIA | `nvidia-smi -L` |
| RSS do `llama-server` (5.294.876 kB) | `awk '/VmRSS/{print $2}' /proc/<pid>/status` |
| memória do cgroup (7.063.789.568 B) | `systemctl show ollama.service -p MemoryCurrent` |
| ambiente vivo do Ollama | `systemctl show ollama.service -p Environment` |
| digests e bytes dos 8 modelos | leitura dos manifests em `/usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/*/*` |
| reemitir os digests completos | `ls /usr/share/ollama/.ollama/models/blobs/` — **o nome do arquivo É o sha256**; o mapa nome→digest sai dos manifests acima |
| runners instalados (`cuda_v12`, `cuda_v13`) | `ls /usr/local/lib/ollama/` |

Números **herdados** do §P12 e do `RELATORIO_HARDWARE_SERVIDOR_20260909.md`, marcados como
tal no corpo e **não re-verificados nesta sessão**: `k` de 0,648/0,660 da bancada da
5060 Ti, ganho de prefill de 74–130×, `size`/RSS/cgroup da observação n = 1, parse do
`.nv_fatbin` dos runners, exigências de driver e CUDA para `sm_120`, `ollama#18232` e
`ollama#18264`, 5,2 tok/s do par 3090/70B, 88.033 requisições/dia na borda, p50 de 3,1 ms,
e os 75 s vs 29 s do experimento do lock.

**Arquivos lidos e não alterados por este documento:** `internal/ollama/cliente.go`,
`internal/cerebro/saude.go`, `internal/cerebro/worker.go`, `internal/cerebro/extracao.go`,
`internal/cerebro/fila.go`, `cmd/cerebro/main.go`,
`ops/ollama/ollama.service.d/wikijuridica-tuning.conf`,
`ops/systemd/wikijuridica-cerebro.service`, `tools/generate-comparacao-modelos-extracao`,
`tools/check-extracoes-dispositivos`, `tools/check-edge-traffic`.

**Nenhum código, unit ou configuração foi alterado.** A única edição fora deste arquivo é
a nota de superação datada em `docs/ops/RELATORIO_HARDWARE_SERVIDOR_20260909.md` (§4), que
acrescenta e não apaga.
