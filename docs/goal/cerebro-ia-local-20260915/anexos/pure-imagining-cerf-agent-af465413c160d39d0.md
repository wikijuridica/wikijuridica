# Fechamento das quatro lacunas — migração para RTX 5060 Ti 16 GB

**Data:** 2026-09-15 · **Modo:** somente leitura · **Host medido:** Debian 12.15,
kernel 6.1.0-52, Ollama 0.33.3 CPU-only, 19,4 GiB de RAM.

Marcação de cada número: **[MEDIDO AQUI]** = comando rodado nesta máquina ·
**[TERCEIRO]** = publicado por outro, com URL e data · **[DERIVADO]** = conta,
com a fórmula à vista.

---

## Veredito em uma linha

| # | lacuna | veredito |
|---|---|---|
| 1 | `size_vram` existe na API 0.33.3? | **FECHADA — existe.** Prova direta no JSON cru do host |
| 2 | o que `size` conta com CUDA? | **FECHADA na mecânica.** Premissa do plano erra em unidade; a guarda proposta tem defeito que a faria pausar hoje. **Sub-item ABERTA:** se o `size` do caminho de GPU inclui KV/grafo não se decide sem a placa → **teste 1** |
| 3 | k = 0,85 transfere para GPU? | **CONFIRMADA a refutação.** k é 0,44 na 4090 medida do próprio relatório; k da 5060 Ti é **0,65–0,85**, faixa medida. **Sub-item ABERTA:** 30B-A3B MoE não tem medição pública nesta placa → **teste 7** |
| 4 | driver/CUDA/Blackwell | **FECHADA — e achei um bloqueador de dia um** nesta placa exata com esta versão exata de Ollama |

As duas ABERTAS são abertas **por natureza**: precisam da GPU no barramento.
Nenhuma outra lacuna ficou para depois.

---

## LACUNA 1 — `size_vram` existe? **FECHADA**

Obtive a prova de força máxima — a **(b)** da lista, JSON cru do processo vivo,
não o struct Go:

```
$ curl -s -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna-ollama)' \
       -H 'X-Warming-Request: true' http://127.0.0.1:11434/api/ps
{"models":[{"name":"qwen3.5:4b",...,"size":3227894413,...,
            "expires_at":"2026-09-15T17:04:54.934171539-03:00",
            "size_vram":0,"context_length":8192}]}
```

**[MEDIDO AQUI]** O campo `size_vram` é emitido. Vale `0` porque o host é
CPU-only — que é exatamente o valor de contrato para "nada em VRAM".

Prova (a) como corroboração: `strings` no binário acha `size_vram` 8 vezes
(`/usr/local/bin/ollama`, `ollama version is 0.33.3`). **[MEDIDO AQUI]**

Há ainda um **segundo** campo que o struct Go descarta: `context_length`.

`internal/ollama/cliente.go:275-280` declara:

```go
type Residente struct {
	Nome         string    `json:"name"`
	Modelo       string    `json:"model"`
	TamanhoBytes int64     `json:"size"`
	Ate          time.Time `json:"expires_at"`
}
```

`encoding/json` ignora campo desconhecido em silêncio — por isso o struct
"funciona" e mesmo assim é cego. **A correção é uma linha** (`SizeVRAM int64
\`json:"size_vram"\`` + `ContextLength int \`json:"context_length"\``). Não a
apliquei: modo somente leitura.

---

## LACUNA 2 — o que `size` conta com CUDA? **FECHADA**

### Mecânica confirmada

- `size` = memória **total** do runner (VRAM + RAM), `size_vram` = a parcela em
  VRAM. Offload completo ⇒ `size_vram == size`; offload parcial ⇒
  `size_vram < size`; CPU puro ⇒ `size_vram == 0` **[MEDIDO AQUI, confere]**.
- `saude.go:162` soma **só** `size` e compara com `TetoBytesResidentesPadrao =
  9 << 30` (`saude.go:92`). `bytesResidentes` (`saude.go:201`) ignora
  `size_vram` porque o struct nem o carrega.
- Estourar devolve `ErrPausado` (`worker.go:68`); `Roda` dorme `IntervaloOcioso`
  e tenta de novo (`worker.go:161`). Não é pausa eterna literal — é **laço**:
  pausa → não chama o Ollama → `KEEP_ALIVE=15m` expira → guarda passa → carrega
  → estoura → pausa. Ciclo de 15 min com trabalho útil perto de zero.

### Correção da premissa do plano (erro de unidade)

O plano afirma que 14b (9,0 GB) + 0.6b (0,64 GB) = 9,6 GB estoura o teto.
**Não estoura — por 36 MB.** `9 << 30` = 9.663.676.416 B = **9,664 GB decimais**,
e a soma é 9,627 GB. **[DERIVADO]** A premissa comparou GB com GiB.

O **risco é real assim mesmo**, com outros pares do disco desta máquina
(`/api/tags`, **[MEDIDO AQUI]**):

| par residente | soma | teto 9 GiB | teto 13 GiB |
|---|---|---|---|
| 14b + embedding 0.6b | 9,63 GB (8,97 GiB) | passa (margem +36 MB) | passa |
| 14b + 4b | 12,38 GB (11,53 GiB) | **ESTOURA** | passa |
| 9b + 4b | 9,98 GB (9,30 GiB) | **ESTOURA** | passa |
| 14b + embedding 4b | 11,48 GB (10,70 GiB) | **ESTOURA** | passa |
| 14b + 9b | 15,58 GB (14,51 GiB) | **ESTOURA** | **ESTOURA** (correto) |

Ou seja: a direção do plano está certa (o teto pausa o cérebro por uma condição
que na máquina nova é inofensiva), só o exemplo escolhido é o único que passa.

E há uma incerteza que **só a máquina nova fecha**: no host atual `size`
(3.227.894.413) é **menor** que o tamanho em disco (3.389.983.735) para
`qwen3.5:4b` **[MEDIDO AQUI]** — logo `size` não é "arquivo + KV". Se no caminho
de GPU `size` passar a incluir a alocação estática de KV/grafo, um 14b **sozinho**
a 8k de contexto já chega perto de 9 GiB e pode estourar o teto **sem
companhia**. Teste de dia um na seção final.

### O defeito da guarda que o plano não viu

`size` nunca foi a grandeza que o `earlyoom` enxerga, e isso é mensurável hoje:

| grandeza | valor | fonte |
|---|---|---|
| `/api/ps` `size` de `qwen3.5:4b` | 3,01 GiB | **[MEDIDO AQUI]** |
| RSS real do `llama-server` (pid 1811489) | 4,75 GiB | **[MEDIDO AQUI]** `/proc/<pid>/status` |
| `MemoryCurrent` do cgroup `ollama.service` | 5,83 GiB | **[MEDIDO AQUI]** |

`size` **subestima o RSS em 1,58×**. A causa é conhecida a montante: `size` /
`size_vram` não contabilizam o prompt cache que o `llama-server` acumula por
requisição ([ollama#18264](https://github.com/ollama/ollama/issues/18264)) — e a
minha medição local bate com isso de forma independente.

**Hipótese a testar, não achado** (n=1, e KV escala com camadas×contexto, não com
bytes de peso): se o fator 1,58× valesse para dois residentes, um `sum(size)` de
9 GiB corresponderia a ~14,2 GiB de RSS, acima do `MemoryMax=12G` do drop-in — o
cgroup mataria o runner **antes** de a guarda disparar. Testar com dois
residentes antes de tratar como fato.

### O teto correto a re-derivar

**A resposta não é "subir o 9 GiB". É parar de apontar uma guarda só para duas
memórias diferentes.** Na máquina nova há dois recursos e eles falham de modos
opostos: estourar VRAM causa *spill* (lentidão silenciosa); estourar RAM causa
OOM (morte). Um número não cobre os dois.

VRAM disponível: 16 GB nominais, **15 GB reportados pelo LocalScore na própria
placa** [TERCEIRO]. Orçar a partir de ~15 GiB, não de 16.

| guarda | campo | valor proposto | por quê |
|---|---|---|---|
| **VRAM** | `sum(size_vram)` | **13 GiB** | 15 GiB úteis − ~2 GiB para KV, grafo e reserva do driver. Passa 14b+0.6b (8,97 GiB) e 14b+4b (11,53 GiB); barra 14b+9b (14,51 GiB) |
| **RAM do host** | `sum(size − size_vram)` | **2 GiB** | com offload completo isto é ~0; 2 GiB tolera o embedding ficar em CPU sem mascarar spill grande |
| **spill** | ver abaixo | defeito, não teto | pega o que os dois tetos não pegam |

Os 9 GiB atuais ficam **só** como fallback para host sem GPU — e mesmo aí devem
ser re-derivados do `MemoryMax` do cgroup do Ollama, não da RAM total do host.
Melhor ainda: para a pergunta de RAM, ler `memory.stat` (anon) do cgroup do
`ollama.service` contra o seu `MemoryMax`, que é a grandeza que mata de verdade —
`size` demonstradamente não é.

### O predicado de spill do plano está errado como escrito

A hipótese do plano — *pausar quando `size_vram < size` em algum residente* —
**pausaria o cérebro hoje, para sempre**: neste host CPU-only `size_vram == 0` em
todo residente **[MEDIDO AQUI]**, logo `0 < size` é sempre verdade. Também
pausaria durante toda a janela de migração antes do driver entrar.

E a variante óbvia `0 < size_vram < size` erra para o outro lado: com a placa
instalada, `size_vram == 0` num residente significa **fallback total para CPU** —
pior que spill — e o predicado a deixaria passar. Esse modo de falha existe em
campo ([ollama#13338](https://github.com/ollama/ollama/issues/13338), VRAM
reportada como 0 B).

**O predicado tem de depender da configuração, não só do campo:**

```
se o host está configurado como GPU-esperada:
    qualquer residente com size_vram < size − tolerância  ⇒ DEFEITO
    (size_vram == 0 é o caso mais grave: fallback total)
senão (CPU-only):
    não avaliar spill
```

A `tolerância` calibra-se no dia um, medindo o delta real de um modelo 100%
offloaded — parte do scratch pode legitimamente ficar no host.

---

## LACUNA 3 — a aritmética de throughput. **CONFIRMADA (a sua leitura)**

### O relatório se contradiz, e dá para mostrar com a própria tabela dele

`docs/ops/RELATORIO_HARDWARE_SERVIDOR_20260909.md` §2.1 escreve a regra como
universal: *"tok/s ≈ 0,85–0,90 × banda ÷ bytes do modelo"*, calibrada em **dois
sistemas de CPU** (esta máquina, 0,87; um 5950X em `llamafile`, 0,85).

Recalculei o k implícito de **cada linha da tabela dele** (k = tok/s × 9,0 ÷
banda, para a coluna 14 B) **[DERIVADO]**:

| linha da tabela §2.1 | banda | 14 B tok/s | **k implícito** |
|---|---|---|---|
| DDR4-2400 single (hoje) | 18 | 1,85 (medido) | **0,93** |
| DDR5-6000 dual (AM5) | 85 | ~8,5 | **0,90** |
| DDR4-3200 8ch EPYC | 70 | ~7 | **0,90** |
| DDR5 12ch EPYC 9004 | 475 | ~32 | 0,61 |
| Strix Halo unificado | 256 | ~14 | 0,49 |
| **RTX 3090** | 936 | ~46 | **0,44** |
| **RTX 4090** | 1008 | **49,1 (medido)** | **0,44** |
| **RTX 5090** | 1792 | ~78 | **0,39** |

As linhas de CPU ficam em 0,90–0,93 — a regra declarada. **As linhas de GPU
ficam em 0,39–0,44 — metade.** O relatório aplica em silêncio um coeficiente
diferente do que anuncia.

**Confirmo a sua conta:** 49,1 × 9,0 ÷ 1008 = **0,438**. E ela não é um ponto
solto: o próprio §4 do relatório cita a mesma fonte medindo **8 B a 91 tok/s** na
4090 → 91,0 × 4,92 ÷ 1008 = **0,444**. Dois pontos medidos, mesma placa, mesma
bancada, k = 0,44 nos dois. **A leitura está certa, e 0,85 é coeficiente de CPU.**

Verifiquei a fonte eu mesmo, não pelo relatório:
[localscore.ai/accelerator/77](https://www.localscore.ai/accelerator/77) —
RTX 4090 24 GB: Llama 3.2 1B Q4_K_M **202** tok/s, Llama 3.1 8B Q4_K_M **91,0**,
Qwen2.5 14B Q4_K_M **49,1**. [TERCEIRO, acesso 2026-09-15]

### k empírico da RTX 5060 Ti — medido na placa, não derivado de outra

[localscore.ai/accelerator/860](https://www.localscore.ai/accelerator/860) —
**RTX 5060 Ti, 15 GB**, **a mesma bancada e os mesmos três modelos/quantizações
da página da 4090**. [TERCEIRO, acesso 2026-09-15]

| modelo Q4_K_M | GB | 5060 Ti | **k** | 4090 | k | razão 5060/4090 |
|---|---|---|---|---|---|---|
| Llama 3.2 1B | 0,81 | **213** | 0,384 | 202 | 0,162 | 1,05 |
| Llama 3.1 8B | 4,92 | **59,0** | **0,648** | 91,0 | 0,444 | 0,648 |
| Qwen2.5 14B | 8,99 | **32,9** | **0,660** | 49,1 | 0,438 | 0,670 |

Três leituras que o plano precisa levar:

1. **k não é constante de hardware.** É 0,44 na 4090 e **0,65 na 5060 Ti**, nos
   mesmos modelos e na mesma bancada. Placa com menos banda **satura melhor** o
   que tem; a 4090 tem banda demais para o que o llama.cpp consegue ocupar em
   decode batch-1.
2. **A razão de desempenho não é a razão de banda.** Banda: 448/1008 = **0,444**.
   Desempenho real: **0,65–0,67** em 8B e 14B. Planejar pela razão de banda
   **subestima a placa nova em ~47%**.
3. **Em 1 B as duas empatam** (213 × 202 — 5%, dentro do ruído de um agregado
   comunitário). O ponto que interessa sobrevive sem forçar a leitura: abaixo de
   ~2 GB o regime não é de banda, é de overhead por token, e a banda da placa
   deixa de explicar o resultado. `qwen3-embedding:0.6b` mora nesse regime.

### Modelo melhor que k constante

Ajustando `t_token = bytes/B_efetiva + t_overhead` aos pontos de 1B e 8B da
5060 Ti **[DERIVADO]**:

- **B_efetiva = 335,6 GB/s = 74,9% do pico de 448** · **t_overhead = 2,29 ms/token**
- previsão para o 14 B: 34,4 tok/s contra 32,9 medidos → **resíduo +4,5%**

Três pontos dentro de 5% — bem melhor que qualquer k único.

*Não* apresento isso como corroborado pelo #28196. O título daquele issue fala em
"76% do roofline" em sm_120 no Linux nativo, número de **ordem de grandeza
compatível**, mas é um **k** (tok/s ÷ banda ÷ bytes) de um modelo só, não uma
`B_efetiva` de ajuste, e o **corpo** que busquei traz outros números (4090 a 86%
do próprio teto; 5090/Windows a 28%), em placa e modelo diferentes. Registro a
compatibilidade, não a uso como prova.

(O mesmo ajuste na 4090 dá resíduo de +20%. Não sei a causa: pode ser ruído da
agregação comunitária, pode ser o próprio modelo de duas parcelas falhando
naquela banda, onde operações não limitadas por memória passam a pesar. Motivo a
mais para não transportar k de lá — não uma explicação medida.)

### Divergência entre fontes — a faixa, com cada ponta nomeada

| modelo Q4_K_M | ponta baixa | ponta alta | razão |
|---|---|---|---|
| Llama 3.1 8B | **59,0** (k 0,65) — LocalScore | **75,1** (k 0,82) — ComputingForGeeks | 1,27× |
| Qwen2.5 14B | **32,9** (k 0,66) — LocalScore | **42,3** (k 0,85) — ComputingForGeeks | 1,29× |

- ponta baixa: [localscore.ai/accelerator/860](https://www.localscore.ai/accelerator/860) — agregado da comunidade, SO não declarado.
- ponta alta: [computingforgeeks.com/rtx-5070-ti-vs-5060-ti-local-ai](https://computingforgeeks.com/rtx-5070-ti-vs-5060-ti-local-ai/) — **Ubuntu 22.04, Docker, CUDA 12.8**, instâncias vast.ai, junho/2026; tok/s de `eval_count/eval_duration`; **só tabela, sem saída crua**.

As duas fontes são internamente coerentes (a razão é 1,27 e 1,29 — diferença
**sistemática**, não ruído). A hipótese mais provável para o degrau, apoiada por
[llama.cpp#28196](https://github.com/ggml-org/llama.cpp/issues/28196): o caminho
**Linux nativo + CUDA 12.8** fica no topo e o agregado misto (com Windows dentro)
no fundo — o mesmo issue mede o caminho Windows/Ollama **1,5–1,6× mais lento** em
sm_120. Se for isso, **este host — Debian, CUDA 12.8 fixado — é a configuração da
ponta alta**.

Terceiro ponto, **menor confiança**, fora da faixa:
[runaihome.com](https://runaihome.com/blog/rtx-5060-ti-ollama-llama2-mistral-deepseek-benchmark-2026/)
(2026-05-13) dá Mistral 7B Q4_K_M a 90,17 e DeepSeek-Coder 6.7B a 101,44 (k 0,88
e 0,91) — mas é **Windows 11, Ollama 0.23.2, sem saída crua, modelos diferentes**.
Registro e não uso.

**Recomendação: planejar com k = 0,65 (conservador) e tratar 0,85 como teto de
oportunidade.** Nunca um valor único sem a faixa.

### Sem medição para 30B-A3B MoE

**Não encontrei medição pública de `Qwen3-30B-A3B` nem de `gpt-oss-20b` na RTX
5060 Ti.** Não substituo por outra placa. O que se sabe por construção: MoE lê só
os pesos **ativos** por token, então o k deve ser calculado sobre os bytes ativos
(~3 B), não sobre o arquivo — e o arquivo inteiro ainda precisa **caber** nos
16 GB. Isso se fecha com `llama-bench` na própria placa, no dia um.

### Projeção para os modelos deste disco

Bytes reais de `/api/tags` **[MEDIDO AQUI]**; tok/s **[DERIVADO]** por
k = 0,65 e k = 0,85; "hoje" é medição do relatório §2.

| modelo | GB | hoje | k=0,65 | k=0,85 | ganho mínimo |
|---|---|---|---|---|---|
| `qwen2.5-coder:14b` | 8,99 | 1,85 | **32,4** | 42,4 | **17,5×** |
| `qwen3.5:9b` | 6,59 | 2,90 | **44,2** | 57,8 | **15,2×** |
| `qwen3.5:4b` | 3,39 | 5,20 | **85,9** | 112,3 | **16,5×** |
| `qwen3-embedding:0.6b` | 0,64 | — | **~238** (roofline) | — | regime de overhead |

Para o 0.6b usei o ajuste roofline, não o k constante: `0,65 × 448 ÷ 0,64` daria
456 tok/s, que o ponto medido de 1 B (213) refuta. **k constante superestima
modelos pequenos** — é a mesma armadilha da lacuna 3, na outra ponta.

### O ganho que importa não é o decode — é o prefill

O `CLAUDE.md` §12 diz que a extração é **dominada pelo prefill** (700–1.100
tokens de entrada contra ~100 de saída). Então a métrica certa é a de prompt:

| | hoje | 5060 Ti | fator |
|---|---|---|---|
| decode 14 B | 1,85 | 32,4–42,4 | 17–23× |
| **prompt processing** | **~18 tok/s** (4b) [relatório §2] | **1.329** (14B) / **2.365** (8B) / **9.418** (1B) [TERCEIRO, LocalScore] | **≥ 74–130×** |

Esse fator é **piso**, não estimativa central: compara o 4b de hoje com os pontos
de 8B e 14B da placa, e um 4B na placa seria mais rápido que o 8B. O ponto exato
do 4B nesta GPU não está medido em lugar nenhum que eu tenha achado.

Duas consequências para o plano:

- A meta do relatório §2 — *"multiplicar essa **banda** por 20–50×"* — **é
  cumprida**: 448 ÷ 18 = **24,9×** de banda [DERIVADO]. O que **não** acompanha é
  o decode (17–23×), e a razão é precisamente o achado da lacuna 3: **k cai de
  ~0,90 (CPU) para ~0,65 (esta GPU)**, então ganho de banda não vira ganho de
  tok/s na proporção. A meta do relatório está certa; a inferência tácita de que
  banda × 25 vira tok/s × 25 é que não está.
- **Na métrica que governa o custo real do cérebro, o ganho é de duas ordens de
  grandeza.** O relatório erra a ênfase, não só o coeficiente. A fila de 5.156
  embeddings + 3.736 extrações (≈ 14 h + 35 h hoje) é prefill-bound, e é aí que a
  placa paga.

---

## LACUNA 4 — driver, CUDA e Blackwell. **FECHADA**

### A prova mais forte estava no disco, não na web

Os runners CUDA vêm no pacote. Parseei a seção `.nv_fatbin` dos dois
`libggml-cuda.so` instalados e li o campo de arquitetura de **cada entrada**
(kind 1 = PTX, kind 2 = SASS/cubin). **[MEDIDO AQUI]**

**`/usr/local/lib/ollama/cuda_v12/libggml-cuda.so`** (cuBLAS 12.8.5.5, cudart
12.8.90, PTX ISA 8.7 = CUDA 12.8), 143 unidades de tradução:

| sm_ | PTX | **SASS nativo** |
|---|---|---|
| 50, 52 | sim | — |
| 60, 61, 70, 75, 80, 86, 89, 90, 100 | sim | **sim** |
| **120** | sim | **SIM — 143 cubins** |

**`/usr/local/lib/ollama/cuda_v13/libggml-cuda.so`** (cuBLAS 13.1.1.3, PTX ISA
9.0 = CUDA 13): sm_75, 80, 86, 87, 89, 90, 100, 103, 110, 120, 121 — **todos
kind=1, PTX puro, zero SASS.**

Duas conclusões que mudam o plano:

1. **O Ollama 0.33.3 JÁ tem sm_120 compilado nativo** — no runner `cuda_v12`.
   Não há JIT, não há custo de primeira carga, **não é preciso atualizar o Ollama
   por causa de arquitetura**. Isso **refuta** a alegação de que o cuda_v12 não
   cobre sm_120.
2. **O runner `cuda_v13` é PTX puro.** Se o Ollama escolher o v13 — o que um
   driver 580+ habilita — **todo kernel do ggml-cuda é compilado por JIT na
   primeira carga**. O custo exato do JIT e o tamanho do cache
   (`ComputeCache`, sob o `HOME` do usuário do serviço — `/usr/share/ollama/`,
   não o do dono) **não medi**: é risco a evitar por construção, não número que
   eu tenha. É custo e risco evitáveis de graça, fixando o v12.

O binário confirma que a filtragem existe: contém as mensagens
`compute capability not in compiled architectures`, `NVIDIA driver too old` e o
símbolo `discover.filterOldCUDADriver`. **[MEDIDO AQUI]** Com sm_120 presente no
v12, a placa passa nesse filtro.

Corroboração cruzada bonita: a NVIDIA removeu Maxwell/Pascal/Volta do CUDA 13 —
e o fatbin do `cuda_v13` começa **exatamente** em sm_75. As duas evidências,
independentes, contam a mesma história.

### Exigências oficiais

| item | exigência | fonte |
|---|---|---|
| sm_120 no nvcc | **CUDA 12.8** — *"This release adds compiler support for the following Nvidia Blackwell GPU architectures: SM_100, SM_101, SM_120"* | [CUDA 12.8 Release Notes](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html) [acesso 2026-09-15] |
| driver p/ CUDA 12.8 (runner `cuda_v12`) | **≥ 570.26** (Linux x86_64) | idem, Tabela 3 |
| driver p/ CUDA 13.0 (runner `cuda_v13`) | **≥ 580.65.06** | [CUDA 13.0 Release Notes](https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html) |
| módulo de kernel | **open kernel modules OBRIGATÓRIO** — *"Maxwell, Pascal, Volta, Turing, and later GPUs until Blackwell. **Blackwell and later are only supported by the open kernel modules**"* | [NVIDIA driver README, kernel_open](https://download.nvidia.com/XFree86/Linux-x86_64/580.95.05/README/kernel_open.html) |
| Debian 12 bookworm | `nvidia-driver` **535.x** → insuficiente — **não conferi eu mesmo**, e é indiferente: a rota é trixie | alegação de subagente, não verificada |
| Debian 13 trixie | `nvidia-driver` **550.163.01-2** → **insuficiente** (< 570.26) | [packages.debian.org/trixie/nvidia-driver](https://packages.debian.org/trixie/nvidia-driver) [conferido 2026-09-15] |

**Consequência:** **nenhum repositório Debian entrega driver suficiente** —
nem trixie. O driver tem de vir do repositório CUDA da NVIDIA ou do instalador
`.run`, com os módulos **open** (`--kernel-open`, ou `-M` para forçar). O
relatório §3 diz "`nvidia-driver` do non-free + CUDA"; **isso não basta** e a
linha precisa ser corrigida.

### Resposta direta: basta remover `OLLAMA_LLM_LIBRARY=cpu`? **NÃO.**

1. Sem driver ≥ 570.26 com módulos open, não há GPU para enxergar.
2. Removida a variável, o Ollama fica livre para escolher **`cuda_v13`**, que é
   PTX puro → JIT em toda carga fria.

**Troque a variável, não a remova:** `OLLAMA_LLM_LIBRARY=cuda_v12` — o único
runner com SASS nativo de sm_120, e (não por acaso) CUDA 12.8, a mesma
configuração da ponta **alta** da faixa de throughput da lacuna 3.

### BLOQUEADOR DE DIA UM — esta placa, esta versão, esta config

[**ollama#18232**](https://github.com/ollama/ollama/issues/18232) — aberto em
2026-09-04, **sem correção**. [TERCEIRO, acesso 2026-09-15]

- **RTX 5060 Ti 16 GB**, compute capability 12.0 — a placa exata da compra.
- **Ollama 0.33.3** — a versão exata deste host.
- runner **CUDA v13** — o runner PTX puro que o parse local identificou.
- Falha: `CUDA error: shared object initialization failed`.
- Causa: a memória compartilhada dinâmica do kernel MMA de **Flash Attention
  escala com `num_ctx`**; passando do limiar, `cudaFuncSetAttribute` falha.
- Contorno confirmado pelo relator: **`num_ctx` 2048** (contra ~4096 padrão).

**O drop-in deste projeto tem os dois ingredientes**
(`ops/ollama/ollama.service.d/wikijuridica-tuning.conf`) **[MEDIDO AQUI]**:

```
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_CONTEXT_LENGTH=8192"
```

8192 é **4× o contorno publicado**. Alta probabilidade de a IA local não subir no
dia um, com um erro que não diz "contexto grande demais".

Mitigação — e note que ela **coincide** com a correção do runner: fixar
`cuda_v12` tira o caminho do v13 do jogo; se ainda assim falhar, `num_ctx` menor
ou `OLLAMA_FLASH_ATTENTION=0` isolam o kernel culpado.

**Os dois botões estão acoplados — não gire um sozinho.** O KV cache quantizado
exige flash attention ligada; com `OLLAMA_FLASH_ATTENTION=0`, o
`OLLAMA_KV_CACHE_TYPE=q8_0` do drop-in **degrada em silêncio para f16** e o KV
dobra (ordem de ~0,8 → ~1,5 GiB a 8k no 14b [DERIVADO]) — comendo justamente a
folga de ~2 GiB que sustenta o teto de VRAM de 13 GiB da lacuna 2. Preferir
reduzir `num_ctx` a desligar a flash attention; se desligar, re-derivar o teto.

### Riscos vizinhos, menores mas na mira desta pilha

| issue | o que é | exposição aqui |
|---|---|---|
| [llama.cpp#24399](https://github.com/ggml-org/llama.cpp/issues/24399) | store fora de faixa em `mul_mat_q<Q8_0>` em sm_120 (**estado aberto/fechado não conferido** — a busca devolveu causa e contorno, não o estado) | `qwen3-embedding:0.6b` é **Q8_0** e o drop-in usa `OLLAMA_KV_CACHE_TYPE=q8_0` |
| [ollama#18276](https://github.com/ollama/ollama/issues/18276) | `qwen3moe` + sm_120: flash attention automática quebra no warmup | se o plano adotar 30B-A3B |
| [llama.cpp#23385](https://github.com/ggml-org/llama.cpp/issues/23385) | MMQ quebra em Blackwell por `sharedMemPerBlockOptin` | mesma família do #18232 |
| [ollama#13338](https://github.com/ollama/ollama/issues/13338) | VRAM reportada como "0 B" → fallback para CPU | é o modo de falha que o predicado de spill tem de pegar (lacuna 2) |

### Sequência de instalação que a evidência sustenta

1. Debian 13 trixie (kernel 6.12). **O motivo não é a GPU** — os módulos open da
   NVIDIA são out-of-tree e compilam contra o 6.1. Quem pede kernel novo é o
   **Ryzen 7 9800X3D (Zen 5)**: `amd_pstate` e o escalonamento de cache X3D. A
   escolha do relatório §3 está certa; a justificativa dele é que precisa trocar.
2. Driver **≥ 570.26**, **módulos open**, do repo CUDA da NVIDIA ou do `.run`
   com `--kernel-open`. **Não** do `nvidia-driver` do Debian.
3. Trocar no drop-in: `OLLAMA_LLM_LIBRARY=cpu` → **`cuda_v12`**.
4. Antes de subir carga: baixar `OLLAMA_CONTEXT_LENGTH` ou desligar
   `OLLAMA_FLASH_ATTENTION`, até o #18232 ser medido nesta placa.
5. Re-derivar os tetos da lacuna 2 **antes** de religar o cérebro — senão o
   worker entra no laço de 15 min.

**Não é preciso trocar de Ollama por causa de sm_120** (o 0.33.3 tem o SASS). Mas
o #18232 é *contra* o 0.33.3: se ele reproduzir e o contorno incomodar, aí sim
subir de versão vira a rota, e a decisão precisa de medição na placa, não de fé.

---

## Testes do dia um (fecham o que esta máquina não fecha)

| # | teste | fecha |
|---|---|---|
| 1 | Carregar **só** o 14b, ler `/api/ps` cru. Comparar `size` com 8.988.124.298 B. Delta positivo ⇒ `size` inclui KV/grafo ⇒ um 14b sozinho pode estourar 9 GiB | a única parte aberta da lacuna 2 |
| 2 | Com o 14b 100% offloaded, conferir `size_vram == size`. O delta residual **é** a tolerância do predicado de spill | calibra a guarda |
| 3 | Ler no log do Ollama qual runner foi escolhido (`cuda_v12` vs `cuda_v13`), com e sem a variável fixada | confirma a escolha de runner |
| 4 | `llama-bench` Q4_K_M em 4B / 8B / 14B, contexto 8k, e comparar com a faixa 0,65–0,85 | resolve a divergência entre fontes na própria placa |
| 5 | Subir com `FLASH_ATTENTION=1` e `CONTEXT_LENGTH=8192` e ver se o #18232 reproduz | o bloqueador |
| 6 | Dois residentes: `sum(size)` contra RSS anônimo do cgroup — confirma ou derruba o 1,58× | tira a hipótese n=1 do ar |
| 7 | `llama-bench` em Qwen3-30B-A3B | o dado MoE que não existe publicado |

---

## Correções que o repositório deve receber (não aplicadas — modo leitura)

1. `internal/ollama/cliente.go:279` — adicionar `SizeVRAM` e `ContextLength`.
2. `internal/cerebro/saude.go:90-92,162,201` — separar guarda de VRAM (13 GiB
   sobre `size_vram`) de guarda de RAM (2 GiB sobre `size − size_vram`), mais o
   predicado de spill **gated por configuração**.
3. `ops/ollama/ollama.service.d/wikijuridica-tuning.conf` —
   `OLLAMA_LLM_LIBRARY=cuda_v12`; rever `FLASH_ATTENTION`/`CONTEXT_LENGTH` à luz
   do #18232; `MemoryMax` re-derivado dos 32 GB.
4. `docs/ops/RELATORIO_HARDWARE_SERVIDOR_20260909.md` §2.1 — a regra 0,85–0,90 é
   **de CPU**; as linhas de GPU da própria tabela usam 0,39–0,44. §3 — driver do
   Debian não serve para Blackwell.
5. `CLAUDE.md` §12 — a física "banda ÷ bytes do modelo" vale para CPU; com GPU
   entra `B_efetiva ≈ 75% do pico` mais overhead por token, e o ganho do cérebro
   é de **prefill**, não de decode.
