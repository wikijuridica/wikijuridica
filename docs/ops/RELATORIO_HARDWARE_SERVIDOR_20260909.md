# Relatório de hardware — a máquina que serve o wikijuridica.com.br e a que deve substituí-la

**Data:** 2026-09-09 · **Escopo:** o host físico de `/opt/wiki` (servir, IA local, Claude Code, compilação Go) · **Estado:** diagnóstico medido; recomendação de compra em três faixas

Este documento registra o que foi medido na máquina atual, o que a carga real
exige, e qual máquina comprar. Toda afirmação numérica tem fonte: comando,
arquivo do repositório ou URL vista na data indicada. Preço de mercado é
volátil: a coluna "data vista" é parte do dado, não decoração.

---

## 1. O que a máquina atual é, de fato

O dono descreveu a máquina como "8 cores, 20 GB, SSD". A medição corrige três
pontos e confirma um:

| item | medido | fonte |
|---|---|---|
| chassi | **Lenovo IdeaPad S145-15IWL (81S9) — um notebook de entrada**, não um desktop | `dmidecode -t system` |
| CPU | Intel i7-8565U Whiskey Lake-U (2018): **4 núcleos físicos / 8 threads**, base 1,8 GHz, classe 15 W | `lscpu` |
| teto de potência | PL1 17 W / PL2 25 W via RAPL; regime sustentado 2,3–2,4 GHz a 85 °C com `pkg_throttle_count=250` | `wikijuridica-energia.service`, `data/ops/energia_cpu.jsonl` 10:55–10:59 |
| ISA | AVX2 + FMA. Sem AVX-512, sem AMX, sem VNNI — o llama.cpp fica no caminho lento | `lscpu` flags |
| RAM | 19,4 GiB = SODIMM 16 GB (Crucial) + 4 GB (Smart Brazil), DDR4-2400, **descasada** — só 8 GB rodam em dual-channel | `dmidecode -t memory` |
| banda de memória | **~18 GB/s** efetivos (DDR4-2400 single-channel = 19,2 GB/s teóricos) | `CLAUDE.md` §IA local, medido 2026-09-08 |
| swap | 12 GiB (zram 4,9 G + partição); **1 327 181 páginas gravadas em swap em 18 h** de uptime (~5,3 GB) | `/proc/vmstat` `pswpout` |
| load | 10,03 / 8,70 / 7,88 em 8 threads | `uptime` 10:51 |
| pressão de CPU | `some avg300=19,79` — em 20 % do tempo alguma tarefa esperou CPU | `/proc/pressure/cpu` |
| earlyoom | 2026-09-08 12:04:53: dois modelos residentes levaram RAM livre a 4,7 %; earlyoom matou `llama-server` **e os servidores MCP do Claude Code** | `CLAUDE.md` §IA local, journal |
| GPU | Intel UHD 620 + NVIDIA GeForce MX110 2 GB (GM108M, Maxwell 2017). Sem driver (`nvidia-smi` falha). Ollama forçado a `OLLAMA_LLM_LIBRARY=cpu` | `lspci`, `ollama.service` |
| disco 1 | NVMe **Kingston SNV3S 1 TB** (SSD de entrada, sem DRAM): `/` 618 G (322 G usados) + `/storage` 276 G (178 G usados) | `lsblk`, `df` |
| disco 2 | HDD WD10SPZX 1 TB SATA 5 400 rpm, 18 729 h — espelho do backup (`wikijuridica-backup`) | `lsblk`, `smartctl` |
| rede | **WiFi** Intel 3165 (1 cadeia espacial), 5 GHz ch 52/80 MHz, 433 Mbit/s, -47 dBm. **Não há porta Ethernet.** | `iw dev wlp2s0 link` |
| SO | Debian 12.15, kernel 6.1.0-52, sem backports | `/etc/debian_version`, `apt-cache policy` |

### 1.1 Achado urgente: o SSD está sendo consumido

```
Model Number:      KINGSTON SNV3S1000G
Percentage Used:   49%
Data Units Written: 264,062,970 [135 TB]
Power On Hours:    3,624
Temperature:       61 Celsius   (sensor 2 na série de energia: 83,8 °C)
```

135 TB gravados em 3 624 h = **894 GB/dia**. O TBW nominal do SNV3S 1 TB é
320 TB. No ritmo atual o disco esgota a garantia de escrita em **~207 dias**.
As fontes de escrita são estruturais desta carga — swap (5,3 GB/18 h), cache de
compilação Go (fechamentos de ~10 min), `.cache/*.pebble`, blobs do Ollama,
`.git` de 11 GB, `data/` de 6,5 GB regravado pelos lotes. Isso não é defeito de
software a corrigir: é a razão de o próximo disco ter de ser de classe alta
(≥ 1 200 TBW por 2 TB) e de a RAM ter de ser grande o bastante para o swap
voltar a zero.

---

## 2. O que a carga real exige

Medido na mesma janela (2026-09-09, 10:50–11:00), com todas as frentes vivas:

| frente | o que roda | medido | o que isso pede do hardware |
|---|---|---|---|
| **servir** | nginx dedicado + `wikijuridica-server` (Go, 500 MB RSS) + 5 processos `cloudflared` | borda: 80 668 req/dia, 60 056 orgânicos, 716 únicos, 349 MB (até 10:58). Origem sob contenção: **6 126 req/s, p50 3,1 ms, p99 39 ms** em `/` (DEC 2026-09-09) | quase nada. O Cloudflare absorve; a origem em Go é barata por desenho. **Servir não é o gargalo.** O que servir exige é *rede cabeada* e *disponibilidade*, não CPU |
| **IA local** | Ollama 0.33.3 CPU-only, 1 modelo residente, `MemoryMax=15G`; cérebro `--max-lote 3` | `qwen2.5-coder:14b` **1,85 tok/s**; `qwen3.5:9b` 2,9 tok/s; `qwen3.5:4b` 5,2 tok/s de geração e 18 tok/s de prompt; `qwen3-embedding:0.6b` 40–74 tok/s de prompt. Lote de 3 embeddings: 23–39 s. Lote de 3 extrações (`extrair_dispositivos`): **1 min 28 s a 1 min 52 s**. `llama-server` a 392 % de CPU | **banda de memória** (tok/s ≈ banda ÷ bytes do modelo). Fila em `data/ai/fila.sqlite`: **5 156 embeddings + 3 736 extrações pendentes** ≈ 14 h + 35 h de trabalho no ritmo atual, com 10 mil páginas em produção alimentando a fila. A máquina nova precisa multiplicar essa banda por 20–50×, o que só VRAM ou memória unificada fazem |
| **Claude Code** | 9 processos `claude` vivos, MCP servers, `bg-spare`, daemon | ~1,5 GB RSS somados; **US$ 1 033 em tokens só hoje** (582 M cache-read) | RAM de folga (o earlyoom já matou MCP), muitos núcleos para `go test`/`go build` disparados pelos agentes em paralelo |
| **Go** | 487 pacotes, 197 448 linhas | fechamento de compilação ~10 min (`CLAUDE.md` linha 33); `checks.test` a 328 % de CPU e 1 GB RSS na medição | núcleos e cache L3; compilação Go escala quase linear até 16 núcleos |
| **desktop** | Chrome (~2 GB RSS em `desktopleve.slice`), Xfce, kitty | picos de `user.slice` 16,2 GB e `system.slice` 18,1 GB — **cada um sozinho já beira os 19,4 GiB físicos** | RAM |

### 2.1 Por que o teto é a banda de memória, não o número de núcleos

Um modelo de 9 B em Q4 pesa ~5,5 GB. Cada token gerado lê o modelo inteiro:
18 GB/s ÷ 5,5 GB ≈ 3,3 tok/s — o medido foi 2,9. Um 14 B Q4 (~9 GB): 18 ÷ 9 = 2
tok/s — medido 1,85. A fórmula bate. Dobrar os núcleos sem mudar a memória não
muda nada na geração. O que muda:

| memória | banda típica | 14 B Q4 (9 GB) | 32 B Q4 (20 GB) | 70 B Q4 (40 GB) |
|---|---|---|---|---|
| DDR4-2400 single (hoje) | 18 GB/s | **1,85 (medido)** | 0,8 | não cabe |
| DDR5-6000 dual-channel (AM5) | ~85 GB/s | ~8,5 | ~3,8 | ~1,8 (se 64 GB+) |
| DDR5 12 canais (EPYC 9004) | 460–490 GB/s | ~32 | **14 (medido)** | **7,1 (medido)** |
| DDR4-3200 8 canais (EPYC 7003 Milan) | 204,8 teóricos; **~70 efetivos** no llama.cpp (7763: Llama-2 7B Q4 a 15 tok/s ⇒ 0,87 × B ÷ 4 GB) | ~7 | ~3 | ~1,5 |
| Strix Halo 128 GB unificado | ~256 GB/s | ~14 (24 B medido) | ~11 | **5,0 (medido)** |
| RTX 3090 24 GB | 936 GB/s | ~46 | **~30–33** | 5,2 (40 % em RAM) |
| RTX 4090 24 GB | 1 008 GB/s | **49,1 (medido)** | ~32–45 | não cabe inteiro |
| RTX 5090 32 GB | 1 792 GB/s | ~78 | ~45–57 | não cabe inteiro (~7,5 com offload) |
| 2 × RTX 3090 (48 GB) | 2 × 936 | — | — | **~19–20** |

Regra calibrada: tok/s ≈ 0,85–0,90 × banda ÷ bytes do modelo. O coeficiente foi
confirmado por dois sistemas independentes: esta máquina (14 B a 1,85 tok/s ⇒
0,87) e um Ryzen 5950X DDR4-3600 medido em `llamafile` (Mistral-7B Q6_K a 8,24
tok/s ⇒ 0,85). "Medido" = número primário publicado com saída de benchmark
visível; o resto é a regra aplicada. Fontes na seção 4. Mais RAM em CPU resolve
o "cabe"; só VRAM, memória unificada ou 8–12 canais resolvem o "fluido".

> **SUPERADO EM 2026-09-16, quanto ao COEFICIENTE — e só quanto a ele. O parágrafo
> acima não se apaga: ele descreve corretamente como as linhas de CPU desta tabela
> foram construídas.**
>
> O motivo é medido. `k` **não é constante do método: é propriedade da CLASSE de
> hardware.** Derivando `k = tok/s × 9 ÷ banda` de cada célula da própria linha
> "14 B Q4 (9 GB)" acima: **0,925** (DDR4-2400, 18 GB/s, medido aqui), 0,900 (DDR5 dual e
> EPYC 8 canais), 0,492 (Strix Halo, 256 GB/s), 0,606 (EPYC 9004, 475 GB/s), **0,442**
> (3090), **0,438** (4090, medido), 0,392 (5090). Ou seja: as células de GPU desta tabela
> **nunca** usaram 0,85–0,90 — elas já embutem 0,39–0,44. É o **texto da regra** que não
> se transfere, não os números.
>
> **E isto NÃO é uma curva monotônica** — entre a Strix Halo (256 GB/s → 0,492) e o EPYC
> 9004 (475 GB/s → 0,606) o coeficiente **sobe** com a banda. São três patamares por
> classe (CPU de banda baixa 0,90–0,93; memória larga sem GPU 0,49–0,61; GPU de topo
> 0,39–0,44), não uma função de uma variável só. Interpolar entre eles é inventar.
>
> Consequência prática, e é ela que custa: quem ler a regra enunciada e a aplicar a um
> cartão novo — como este parágrafo convida a fazer — **erra para cima em ~2×**. A
> aferição direta fecha o caso: a RTX 5060 Ti 16 GB (448 GB/s) foi medida em
> **59,0 tok/s** num Llama 3.1 8B Q4_K_M (4,92 GB) e **32,9 tok/s** num Qwen2.5 14B
> Q4_K_M (8,99 GB) — `k` de **0,648** e **0,660**, não 0,85. Placa com menos banda
> satura melhor, e o 0,65 dela cai exatamente onde a curva acima o põe.
>
> **A regra que substitui esta, para qualquer hardware futuro:** use
> `tok/s = k × banda ÷ bytes` **com o `k` da CLASSE DE BANDA em questão**, e trate o
> resultado como estimativa até `medir_modelo` rodar na máquina real. A derivação
> completa, a tabela refeita, os três regimes (residente, spill e MoE) e o protocolo de
> migração estão em **`docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md`**. O `k` da 5060 Ti
> (0,648–0,660) fica **acima** dos dois patamares de banda vizinha, e é medição, não
> interpolação.


---

## 3. Restrições que o pedido implica e não diz

| restrição | por quê | o que entra no orçamento |
|---|---|---|
| **Nobreak** | O notebook tem bateria: hoje uma queda de luz não derruba o túnel nem corrompe o SQLite. Desktop não tem. `wikijuridica-server`, `cerebro` (fila SQLite), nginx com cache em disco e Ollama com blobs de 30 GB precisam de desligamento ordenado | Nobreak **senoidal** de 1 200–1 500 VA com USB (NUT/apcupsd) para o host mandar `poweroff` quando a bateria cair a 30 %. Está em cada faixa da seção 5 |
| **Energia** | Hoje o host inteiro consome ~17 W (RAPL medido: 16,95 W). Um desktop de 16 núcleos com GPU de 24 GB fica em 80–130 W ocioso e 500–650 W de pico. A 24/7 isso é dinheiro | À tarifa residencial média de 2026 (R$ 0,79–0,85/kWh, projeção ANEEL de R$ 849/MWh no fim do ano): 17 W = 12 kWh/mês ≈ **R$ 10**; desktop a 150 W médios = 108 kWh/mês ≈ **R$ 90**; com GPU trabalhando 8 h/dia a 350 W somados ≈ 200 kWh/mês ≈ **R$ 165**. Precisa caber no negócio |
| **Sistema operacional** | Debian 12 tem kernel 6.1 (2022). Ryzen 9000 (Zen 5), Core Ultra 200, RTX 50 e Strix Halo pedem kernel ≥ 6.11–6.14 e Mesa/firmware novos. Não há backports habilitado hoje | Instalação limpa de **Debian 13 "trixie"** (estável desde 2025-08-09, kernel 6.12, systemd 257, nginx 1.26) na máquina nova. A pilha inteira — units, slices, drop-ins em `ops/`, hooks, symlinks em `/etc` — é reproduzível a partir de `ops/host-state/CHECKLIST-REBOOT.md`, que já existe para isso |
| **Driver de GPU** | Hoje não existe driver NVIDIA instalado (`nvidia-smi` falha) e o Ollama está forçado a `OLLAMA_LLM_LIBRARY=cpu`. Nenhum dos dois está no estado "só plugar" | NVIDIA: `nvidia-driver` do `non-free` + CUDA; remover o `OLLAMA_LLM_LIBRARY=cpu` do drop-in em `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`. AMD: Vulkan (o Ollama já tem `OLLAMA_VULKAN:true` no log) ou ROCm. É item de migração, não de compra |
| **Sem macOS** | Mac Studio tem a melhor banda unificada do mercado (até 800 GB/s), mas a plataforma inteira é systemd, cgroup v2, RAPL, nginx com drop-ins, earlyoom, `ai-pane`/tmux e hooks em bash. Nada disso roda igual em macOS | **Descartado.** Não é falta de desempenho; é reescrever a operação |
| **Sem notebook** | Pedido do dono; e a medição concorda: 15 W, sem Ethernet, SODIMM descasada, SSD sem DRAM, NVMe a 84 °C | Torre com fluxo de ar. Tamanho de gabinete importa porque GPU de 24 GB tem 3 slots e 30+ cm |
| **Dois discos físicos** | `wikijuridica-backup.service` é "espelho do repositório em disco físico separado" — regra do repositório, não preferência | 2 × NVMe (sistema 2 TB de alta TBW + backup 1–2 TB), ou NVMe + SATA SSD |
| **Rede cabeada** | Produção roda em WiFi de 1 cadeia espacial (433 Mbit/s). O relatório de rede de 2026-08-19 mediu jitter de até 109 ms num salto de LAN por retransmissão de camada 2 | Placa-mãe com **2,5 GbE** e cabo até o roteador. É a melhoria mais barata de disponibilidade que existe nesta lista |
| **Sem RAM descasada** | 16 + 4 GB hoje derruba a banda para single-channel em 12 dos 20 GB | Kit **casado de 2 módulos**. Em AM5, 4 DIMMs de DDR5 caem para 3 600–4 800 MT/s — comprar 2 × 48 ou 2 × 64, nunca 4 × 16 |
| **RAM mínima 64 GB** | Picos medidos: `user.slice` 16,2 GB + `system.slice` 18,1 GB; earlyoom já disparou; swap gravou 5,3 GB em 18 h; um 32 B Q4 para CPU ocupa 20 GB; 70 B Q4 ocupa 40 GB | 64 GB é o piso para parar de gravar swap. 96–128 GB se a IA local for rodar 70 B ou dois modelos residentes |

---

## 4. O que a IA local ganha por classe de hardware (números publicados)

Pesquisa de 2026-09-09 sobre benchmarks primários de `llama.cpp`/Ollama. Onde
um agregador contradisse a física (banda ÷ bytes), o número foi descartado.

| conclusão | evidência | fonte |
|---|---|---|
| **32 B fluido (> 20 tok/s) exige GPU de 24 GB.** Nenhuma CPU chega: mesmo EPYC 9554 com 12 canais DDR5 (460–490 GB/s) fica em 14 tok/s no QwQ-32B | RTX 4090: Qwen2.5-14B a 49,1 tok/s e 8 B a 91 tok/s, medido | [localscore.ai](https://www.localscore.ai/accelerator/77) · [ahelpme EPYC 9554](https://ahelpme.com/ai/llm-inference-benchmarks-with-llamacpp-with-amd-epyc-9554-cpu/) |
| **70 B utilizável (> 5 tok/s) exige 2 × 24 GB** (~19–20 tok/s) ou servidor de 12 canais (7,1 tok/s). GPU única de 24 GB com 40 % do modelo em RAM cai para 5,2 tok/s — ~30 % do que faria inteira em VRAM, não os "60–70 %" que se lê por aí | 2 × 4090 medido em 20,97 tok/s; 3090 única com spill 5,2 | [sergeynog 2×4090](https://sergeynog.substack.com/p/mac-m3-vs-2-x-nvidia-4090-a-performance) · [gigagpu 3090 70B](https://gigagpu.com/llama-3-70b-on-rtx-3090-benchmark/) |
| **RTX 5090 é 1,58 × a 4090**, medido — mas 32 GB ainda não cabem 70 B Q4 (40–42 GB de pesos + KV) | Phoronix, llama.cpp | [Phoronix RTX 5090](https://www.phoronix.com/review/nvidia-rtx5090-llama-cpp/2) |
| **Strix Halo (Ryzen AI Max+ 395, 128 GB)**: 8 B a 42 tok/s, 24 B a 14,3, 70 B a 5,0 — tudo medido. Cabe 70 B e cabe gpt-oss-120b (MoE, 5,1 B ativos), que roda bem mais rápido que 70 B denso, mas os três números publicados para ele (31–55 tok/s) divergem e nenhum é primário | Level1Techs, saída real de benchmark | [L1Techs Strix Halo](https://forum.level1techs.com/t/strix-halo-ryzen-ai-max-395-llm-benchmark-results/233796) |
| **DDR5 dual-channel sem GPU** (7950X/9950X, ~85 GB/s): só extrapolação calibrada — 8 B ~14, 14 B ~8,5, 32 B ~3,8, 70 B ~1,8 tok/s. Só o 8 B é utilizável | Ryzen 5950X DDR4-3600 medido em `llamafile` e escalado pela banda | [llamafile #450](https://github.com/mozilla-ai/llamafile/discussions/450) |
| **VRAM**: 32 B Q4_K_M = ~20 GB de pesos + KV q8_0 (8 k ≈ 1 GB, 32 k ≈ 4,3 GB) + ~1 GB. Cabe em 24 GB até ~16 k de contexto. 70 B Q4 = 46–48 GB com 32 k | conta de KV cache | [dev.to KV cache](https://dev.to/plasmon_imp/q4-kv-cache-fit-32k-context-into-8gb-vram-only-math-broke-209k) |
| **Energia em idle** (Linux headless): 3090/4090 5–8 W com undervolt, 15–25 W sem; 5090 3–5 W. Carga: 3090 350 W, 4090 450 W. Strix Halo: sistema inteiro ~100 W médios sob carga, pico ~180 W, idle 10–20 W | medido | [L1Techs idle](https://forum.level1techs.com/t/some-gpu-5090-4090-3090-a600-idle-power-consumption-headless-on-linux-fedora-42-and-some-undervolt-overclock-info/237064) · [ServeTheHome Framework Desktop](https://www.servethehome.com/framework-desktop-review-a-solid-amd-strix-halo/5/) |
| **AMD no Debian**: ROCm 7.2 (mar/2026) certifica só Ubuntu 22.04/24.04 e RHEL. Vulkan/RADV mede 20–30 % mais rápido que ROCm em RDNA3/RDNA4; RX 9070 XT ainda tem bug de `rocBLASLt` no carregamento. O Ollama daqui já tem `OLLAMA_VULKAN:true` — caminho AMD viável é Vulkan puro | | (pesquisa de GPU, 2026-09-09) |
| **Ranking PT-BR de modelos abertos**: o [Open Portuguese LLM Leaderboard](https://huggingface.co/spaces/eduagarcia/open_pt_llm_leaderboard) está arquivado e não cobre Qwen3/Gemma 3/gpt-oss. Não existe fonte independente atualizada; a escolha de modelo fica para a bancada própria (`medir_modelo` já existe na fila do cérebro) | | |

---

## 5. Mercado brasileiro em 2026-09-09

Preço é dado perecível. Cada linha diz onde foi visto e se a página foi aberta
ao vivo ("ao vivo") ou só lida no título indexado pelo buscador ("indexado").
Mercado Livre e Pichau bloqueiam leitura automatizada (HTTP 403 e página de
verificação): preços deles são indexados, e a compra exige abrir o anúncio à
mão e confirmar.

### 5.1 GPU — a peça que decide a IA local

| GPU | VRAM | banda | TDP | preço R$ | onde | como visto |
|---|---|---|---|---|---|---|
| **RTX 3090 24 GB usada** | 24 GB | 936 GB/s | 350 W | **4 999 – 6 350** (faixa geral 5 500–6 999; anúncios se declaram "ex-mineração, 60 dias a 7 meses") | Mercado Livre: [MLBU3248753633](https://www.mercadolivre.com.br/placa-de-video-geforce-rtx-3090-nvidia-24gb/up/MLBU3248753633) · [MLB16071004](https://www.mercadolivre.com.br/placa-de-video-nvidia-geforce-rtx-30-series-rtx-3090-24gb/p/MLB16071004) · [MLBU3803649302](https://www.mercadolivre.com.br/placa-de-video-gamer-geforce-rtx-3090-trinity-24gb-seminova/up/MLBU3803649302) | indexado |
| RTX 4090 24 GB | 24 GB | 1 008 GB/s | 450 W | 13 660 – 14 249, **esgotada** ao abrir | Terabyte: [22561](https://www.terabyteshop.com.br/produto/22561/placa-de-video-msi-nvidia-geforce-rtx-4090-gaming-trio-24gb-gddr6x-dlss-ray-tracing) | indexado |
| RTX 5090 32 GB | 32 GB | 1 792 GB/s | 575 W | 22 222 – 26 667 | Kabum: [714538](https://www.kabum.com.br/produto/714538/placa-de-video-asus-tuf-rtx5090-o32g-gaming-nvidia-32gb-gddr7-512bits-90yv0ly0-m0na00) · [713218](https://www.kabum.com.br/produto/713218/placa-de-video-rtx-5090-gaming-oc-32g-gigabyte-nvidia-geforce-32gb-gddr7-512bits-rgb-dlss-ray-tracing-gv-n5090gaming-oc-32gd) | ver nota abaixo |
| RTX 5080 16 GB | 16 GB | 960 GB/s | 360 W | 12 599,99 – 13 999,99 | Kabum: [690382](https://www.kabum.com.br/produto/690382/placa-de-video-asus-rtx-5080-prime-oc-16g-nvidia-geforce-16gb-gddr7-g-sync-ray-tracing-dlss-4-hdr-90yv0lx0-m0na00) | ao vivo (agente) |
| RTX 5070 Ti 16 GB | 16 GB | 896 GB/s | 300 W | **10 799,91** à vista, em estoque (agregadores listam 7 124) | Kabum: [753243](https://www.kabum.com.br/produto/753243/placa-de-video-gigabyte-geforce-rtx-5070-ti-gaming-oc-16gb-gddr7-256-bits-gv-n507tgaming-oc-16gd) | **ao vivo, conferido pelo autor** |
| RX 7900 XTX 24 GB | 24 GB | 960 GB/s | 355 W | ~7 000 – 9 570; **7 SKUs esgotados** na Kabum | [busca Kabum](https://www.kabum.com.br/busca/placa-de-video-radeon-rx-7900-xtx) | indexado |
| RX 9070 XT 16 GB | 16 GB | 640 GB/s | 304 W | 4 899,89 – 5 699,99, 30 un. em estoque | Kabum: [725947](https://www.kabum.com.br/produto/725947/placa-de-video-xfx-swift-rx-9070-xt-triple-fan-gaming-edition-with-amd-radeon-16gb-gddr6-hdmi-3xdp-rdna-4-rx-97tswf3b9) | ao vivo (agente) |
| 2 × RTX 3090 (48 GB) | 48 GB | 2 × 936 | 700 W | 10 000 – 12 700 | mesmos anúncios da linha 1 | indexado |

**Leitura.** Toda placa de 16 GB sai do objetivo "32 B fluido" por VRAM, não por
preço: 20 GB de pesos não cabem, e offload para RAM reintroduz o gargalo de
banda que motivou a troca. Entre as de 24 GB, a **RTX 3090 usada custa R$ 208–265
por GB de VRAM** — a 4090 e a 5090 entregam o mesmo "cabe" por 2,5–5 × o preço.
O risco da usada é real (mineração, sem garantia de fábrica) e se mitiga com
garantia do vendedor, teste de `nvidia-smi -q -d TEMPERATURE,POWER` sob carga e
troca de pasta térmica. RX 7900 XTX seria a alternativa nova de 24 GB, mas está
esgotada e o driver AMD no Debian é caminho Vulkan sem certificação ROCm.

### 5.2 Máquina pronta — o que existe à venda no Brasil

| opção | CPU | RAM | GPU | disco | preço R$ | onde | como visto |
|---|---|---|---|---|---|---|---|
| **Servidor EPYC 7413** (torre) | EPYC 7413, 24 c / 48 t, Zen 3, SP3 | **256 GB DDR4 ECC RDIMM** (8 DIMMs — 8 canais) | nenhuma; **5 × PCIe 4.0 x16 + 2 × x8 livres** | 1 TB NVMe (Kingston NV3, o mesmo modelo que está morrendo aqui); **2 × M.2 PCIe 4.0** | **25 950**, 1 em estoque; DDR4-3200; fonte 850 W Gold; 2 × 1 GbE; placa-mãe, garantia e cooler não informados na página | Hard Leste: [servidor-amd-epyc-7413](https://hardleste.com.br/produto/servidor-amd-epyc-7452-2-35ghz-32-core-02-x-processadores-128gb-memoria-ssd-2tb-sata/) | **ao vivo, conferido pelo autor** (o slug da URL é de outro produto; a página é do 7413) |
| PC do Yoda | Ryzen 9 7950X3D, 16 c | 32 GB DDR5 (título) / 64 GB (agente) | RTX 4090 24 GB | 2 TB NVMe | 19 241,59 — **esgotado** | Terabyte: [26751](https://www.terabyteshop.com.br/produto/26751/pc-do-yoda-amd-ryzen-9-7950x3d-nvidia-geforce-rtx-4090-32gb-ddr5-ssd-nvme-2tb) | indexado; Terabyte devolve 403 |
| PC Gamer Kabum | Ryzen 9 7900X, 12 c | 64 GB DDR5 | RTX 4090 24 GB | 1 TB NVMe, fonte 1 000 W | 33 099,90 — **indisponível** | Kabum: [544924](https://www.kabum.com.br/produto/544924/pc-gamer-amd-ryzen-9-7900x-64gb-ddr5-placa-rtx-4090-24gb-ssd-1tb-m2-nvme-placa-mae-x670p-fonte-1000w-water-cooler-240mm-windows-11-pro) | API pública da Kabum (estoque 0 real) |
| PC Gamer Hyte Y70 | Ryzen 9 9900X, 12 c | 64 GB DDR5 | RTX 4090 24 GB | 2 TB NVMe, fonte 1 200 W | 46 550 à vista — **indisponível** | Kabum: [669949](https://www.kabum.com.br/produto/669949/pc-gamer-hyte-y70-touch-black-amd-ryzen-9-9900x-tuf-gaming-x670e-plus-rtx-4090-24gb-64gb-ram-ddr5-fury-2tb-m-2-nvme-fury-1200w-gold-tt-water-cooler-lcd-360mm) | API pública da Kabum |
| PC Gamer Ultimate | Ryzen 9 9950X3D, 16 c | 64 GB DDR5 | RTX 5090 32 GB | 2 TB NVMe, fonte 1 200 W | 66 357,50 à vista — **indisponível** | Kabum: [770056](https://www.kabum.com.br/produto/770056/pc-gamer-ultimate-amd-ryzen-9-9950x3d-rtx-5090-gigabyte-x870-aorus-elite-wifi7-ice-64gb-ddr5-rgb-2tb-nvme-fonte-1200w-80-plus-gold-water-cooler-360mm-rgb) | API pública da Kabum |
| Dell Precision 5860 | Xeon W3-2525, **8 c** | configurável | RTX A1000 8 GB | configurável | a partir de 22 698 | [Dell BR](https://www.dell.com/pt-br/shop/computadores-all-in-ones-e-workstations/workstation-em-torre-precision-5860/spd/precision-5860-workstation) | ao vivo (agente); não cumpre 12 c |
| Dell Precision 7875 | Threadripper PRO | até 2 TB | até 2 × 300 W | configurável | **sob consulta**, sem venda online | [Dell BR](https://www.dell.com/pt-br/shop/computadores-all-in-ones-e-workstations/workstation-em-torre-precision-7875/spd/precision-t7875-workstation) | ao vivo (agente) |
| Workstation Threadripper 7960X | TR 7960X, 24 c | 128 GB DDR5 | RTX PRO 2000 16 GB | 1 TB NVMe | 75 150 à vista | [Atainfo](https://www.atainformatica.com.br/workstation-ryzen-threadripper-7960x-128gb-ssd-1tb-quadro-rtx-pro-2000-16gb) | ao vivo (agente) |
| Rocketz Heavy V IA | Threadripper PRO até 96 c | até 256 GB+ ECC | 1–4 × RTX PRO 6000 96 GB | até 15 TB | a partir de 75 899 | [rocketz.com.br/pc-para-ia](https://rocketz.com.br/pc-para-ia) | ao vivo (agente) |
| Framework Desktop | Ryzen AI Max+ 395, 16 c | **128 GB LPDDR5X unificada** | Radeon 8060S integrada | NVMe configurável | US$ 1 999 ≈ **21 100 importado** (II 60 % + ICMS 17 %, câmbio 5,09); **não vende no Brasil** | [frame.work/desktop](https://frame.work/br/en/desktop) | ao vivo; página não mostra preço nem envio ao Brasil |
| Beelink GTR9 Pro / GMKtec EVO-X2 | Ryzen AI Max+ 395 | 128 GB LPDDR5X | Radeon 8060S; EVO-X2 tem OCuLink para eGPU | 2 TB NVMe | US$ 1 999 – 3 499 ≈ 21 100 – 27 700 importado | [Amazon US](https://www.amazon.com/Beelink-GTR9-Crucial-Computer-DeepSeek/dp/B0FPQQYWQ1) · [Amazon BR](https://www.amazon.com.br/GMKtec-EVO-X2-computadores-LPDDR5X-qu%C3%A1drupla/dp/B0F53MLYQ6) | indexado |

**Não recuperado, e por isso fora da tabela:** Pichau (Highflyer, WorkStation WS388/WS379) e Lenovo ThinkStation P3/P5 devolvem 403 a qualquer leitura automatizada; Overclock Extreme 7950X + 4090 + 64 GB a 52 800 redireciona para `loja_indisponivel`. Nenhum preço foi inventado para preencher lacuna.

**Leitura.** Todo PC "gamer" pronto com 4090/5090 e 64 GB está esgotado ou
indisponível hoje, e quando existe custa 19–66 mil com Windows, RGB e
water-cooler que não servem para nada aqui. A única máquina pronta **em
estoque** que cumpre núcleos e RAM é o servidor EPYC 7413: 24 núcleos, 256 GB
ECC em 8 canais, fonte de 850 W e slots PCIe 4.0 livres — falta a GPU, que se
compra à parte. Strix Halo tem a melhor relação "cabe 70 B por real", mas não
se vende no Brasil, exige kernel ≥ 6.16.9 (acima do 6.12 do Debian 13) e RMA
para o exterior.

### 5.3 Peças para montar (AM5) — e a crise de memória

Pesquisa em Kabum, Pichau, Terabyte e rastreadores de preço. **Contexto que
domina esta tabela:** o mercado está no pico de uma escassez global de DRAM e
NAND (TrendForce: DRAM +90–95 % no 1T26, +63 % projetado no 2T26). No Brasil
isso aparece como kit de 64 GB DDR5 a R$ 9 mil e quase todo SKU premium de RAM,
NVMe e fonte (Corsair, Seasonic, KC3000, SN850X, Noctua) **esgotado** nos três
varejistas — confirmado por leitura direta de ~25 páginas, não por bloqueio.

| item | modelo | preço R$ | onde | como visto |
|---|---|---|---|---|
| CPU 16 c | **Ryzen 9 9950X** (Zen 5, 4,3/5,7 GHz, 170 W) | **3 399,99**, 48 un. em estoque | Kabum: [609951](https://www.kabum.com.br/produto/609951/processador-amd-ryzen-9-9950x-4-3-ghz-5-7-ghz-max-turbo-cache-64mb-16-nucleos-32-threads-am5-sem-video-integrado-100-100001277wof) | **ao vivo, conferido pelo autor** |
| CPU 12 c | Ryzen 9 9900X | 2 399,99, em estoque | Kabum: [609952](https://www.kabum.com.br/produto/609952/processador-amd-ryzen-9-9900x-4-4-ghz-5-6-ghz-cache-64-mb-12-nucleos-24-threads-am5-100-100000662wof) | ao vivo (agente) |
| CPU 16 c | Ryzen 9 7950X (Zen 4) | 3 771,66 — mais caro que o 9950X | Kabum: [390981](https://www.kabum.com.br/produto/390981/processador-amd-ryzen-radeon-9-7950x-2200mhz-cache-80mb-1hexa-core-am5-video-integrado-100-100000514wof) | ao vivo (agente) |
| CPU Intel | Core Ultra 9 285K (24 c) / Ultra 7 265K (20 c) | ~3 340 / ~2 706 — **esgotados** | Kabum: [645177](https://www.kabum.com.br/produto/645177/processador-intel-core-ultra-9-285k-5-7ghz-ate-24-nucleos-com-suporte-a-pcie-5-0-e-4-0-e-suporte-a-ddr5-bx80768285k) | indexado |
| placa AM5 | Gigabyte X870 Gaming WF6 (3 × M.2 Gen4, 2,5 GbE, USB4) | 1 899,00, em estoque | Kabum: [706416](https://www.kabum.com.br/produto/706416/placa-mae-gigabyte-x870-gaming-wifi6-amd-am5-atx-bluetooth-ddr5-x870-gaming-wf6) | ao vivo (agente) |
| placa AM5 | Gigabyte B650M Gaming WiFi (2 × M.2 Gen4, 2,5 GbE) | 982,21, em estoque | Kabum: [573210](https://www.kabum.com.br/produto/573210/placa-mae-gigabyte-b650m-gaming-wifi-1-0-am5-ddr5-m-2-nvme) | ao vivo (agente) |
| RAM 64 GB | Kingston Fury Beast 2 × 32 GB DDR5-6000 CL30 | **8 999,99 – 10 999,99**; mínimo histórico 7 999,99; **sem estoque** | Kabum via [radarram](https://radarram.com.br/produto/kingston-fury-beast-ddr5-6000-2x32gb/) | rastreador, atualizado 2026-09-09, conferido pelo autor |
| RAM 96 GB | Corsair Vengeance 2 × 48 GB DDR5-6000 CL30 | 3 810 em loja pequena, **esgotado e sem data** — preço pré-crise, não confiável | [LiveStore](https://www.livestoreonline.com.br/produtos/memoria-ram-corsair-vengeance-96gb-2x-48gb-preta-ddr5-cl-30-6000-mhz-cmk96gx5m2b6000z30/) | indexado |
| RAM 128 GB | Crucial Pro 2 × 64 GB DDR5-5600 CL46 | 15 990,00 (junho/2026, tende a subir) | Kabum via [achapromo](https://achapromo.com.br/produto/memoria-ddr5-128gb-crucial-pro-2x64gb-5600mhz-cp2k64g56c46u5/176aaa45-8e3f-456b-8461-633227eb2b60) | rastreador, 2026-06-06 |
| NVMe 2 TB | Kingston NV3 2 TB (SNV3S/2000G) — **640 TBW**, sem DRAM | **2 349,99**, em estoque | Kabum: [621163](https://www.kabum.com.br/produto/621163/ssd-kingston-nv3-2tb-m-2-2280-pcie-4-0-x4-nvme-leitura-6000-mb-s-gravacao-5000-mb-s-azul-snv3s-2000g) | **ao vivo, conferido pelo autor** |
| NVMe 1 TB | Kingston NV2 1 TB (backup) | 1 044,05, em estoque | Kabum: [594176](https://www.kabum.com.br/produto/594176/ssd-m-2-pcie-nvme-kingston-1-tb-leitura-3500-mb-s-e-gravacao-2100-mb-s-snv2s-1000g) | ao vivo (agente) |
| NVMe premium | KC3000 2 TB (1 600 TBW), SN850X 2 TB (1 200 TBW), 990 Pro 2 TB (1 200 TBW) | **esgotados** | Kabum | ao vivo (agente) |
| fonte 850 W | Redragon 850 W 80+ Gold full-modular | 887,20, em estoque | Kabum: [524411](https://www.kabum.com.br/produto/524411/fonte-redragon-atx-850w-80-plus-gold-rgb-pfc-ativo-full-modular-preto) | ao vivo (agente) |
| fonte 1 000 W | Redragon Master 1 000 W 80+ Gold ATX 3.1 | 1 124,41, em estoque | Kabum: [884982](https://www.kabum.com.br/produto/884982/fonte-1000w-80-plus-gold-redragon-master-rgms-atx-3-1-full-modular-black-gc-ms03) | ao vivo (agente) |
| fonte premium | Corsair RM850x/RM1000x, Seasonic Focus GX-850, MSI MAG A850GL | **esgotadas** | Kabum | ao vivo (agente) |
| gabinete | Redragon Wideload Pro (mid tower ATX) | 349,99 | Kabum: [518940](https://www.kabum.com.br/produto/518940/gabinete-gamer-redragon-wideload-pro-mid-tower-atx-lateral-e-frontal-em-vidro-temperado-preto-ca-604b-pro) | ao vivo (agente) |
| cooler | Gigabyte Eagle 360 ARGB (AIO 360 mm) | 359,99 | Kabum: [1019513](https://www.kabum.com.br/produto/1019513/water-cooler-gigabyte-eagle-360-argb-360mm-amd-e-intel-preto-gp-gigabyte-eagle-360) | ao vivo (agente) |
| **nobreak** | **SMS Premium 1 500 VA senoidal, 8 tomadas, bivolt** | **2 320,90**, em estoque | Kabum: [472207](https://www.kabum.com.br/produto/472207/nobreak-sms-premium-1500va-8-tomada-bivolt-0029501) | ao vivo (agente) |

**Banda real de DDR5-6000 em AM5:** 96 GB/s teóricos; medido em AIDA64 ≈ 59 GB/s
([ocinside.de](https://www.ocinside.de/review/crucial_pro_overclocking_2x16gb_ddr5_6000_white/4/)),
porque o Infinity Fabric não acompanha acima de ~2 000 MHz. Para IA em CPU, AM5
entrega ~3 × a máquina atual — não 5 ×.

**Orçamentos de montagem (sem GPU, sem nobreak):**

| montagem | CPU | placa | RAM | NVMe 2 TB + 1 TB | fonte | gabinete + cooler | total R$ |
|---|---|---|---|---|---|---|---|
| 64 GB / 12 c | 9900X 2 399,99 | B650M 982,21 | 64 GB 8 999,99 | 3 394,04 | 850 W 887,20 | 709,98 | **17 373** |
| 96 GB / 16 c | 9950X 3 399,99 | X870 1 899,00 | 96 GB ~12 500 (estimado) | 3 394,04 | 1 000 W 1 124,41 | 709,98 | **~23 000** |
| 128 GB / 16 c | 9950X 3 399,99 | X870 1 899,00 | 128 GB 15 990 (junho) | 3 394,04 | 1 000 W 1 124,41 | 709,98 | **≥ 26 500** |

RAM é 52–60 % de cada orçamento. Sem a crise, as mesmas montagens custariam
R$ 7–10 mil. **Nenhuma placa AM5 pesquisada confirma ECC funcional.** E 4 DIMMs
em AM5 caem para 3 600–4 800 MT/s: comprar sempre 2 módulos.

---

## 6. Ranking: do 1º ao 5º, todos com caminho de upgrade

Critérios, em ordem: (1) resolve os três gargalos medidos — banda de memória
para a IA, RAM para parar o swap e o earlyoom, núcleos para Go e agentes; (2)
aceita hardware posterior sem trocar a base (slots PCIe, DIMMs livres, fonte com
folga, socket com futuro); (3) está à venda no Brasil hoje; (4) preço total com
GPU, disco de alta escrita e nobreak — não o preço de vitrine.

Em todas as opções a GPU é a mesma: **RTX 3090 24 GB usada** (R$ 5 000–6 350).
É a única placa de 24 GB em estoque no país e a de menor R$/GB. Cabe 32 B Q4 a
~30 tok/s (16 × o que a máquina atual faz com um 14 B). A segunda 3090, quando
vier, destrava 70 B a ~19–20 tok/s.

### 1º — Servidor EPYC 7413 (Hard Leste) + RTX 3090 usada — ≈ R$ 36 000

| componente | preço R$ | fonte |
|---|---|---|
| Servidor EPYC 7413, 24 c / 48 t, **256 GB DDR4-3200 ECC RDIMM em 8 canais**, 5 × PCIe 4.0 x16 + 2 × x8, 2 × M.2, fonte 850 W Gold, torre, 1 TB NVMe | 25 950 | [Hard Leste](https://hardleste.com.br/produto/servidor-amd-epyc-7452-2-35ghz-32-core-02-x-processadores-128gb-memoria-ssd-2tb-sata/), 1 em estoque |
| RTX 3090 24 GB usada | 5 000 – 6 350 | Mercado Livre (§5.1) |
| NVMe 2 TB de alta escrita para sistema (NV3 2 TB, 640 TBW, em estoque; trocar por KC3000/990 Pro quando voltar ao estoque) — o NV3 1 TB que vem no servidor vira o disco de **backup** | 2 350 | Kabum (§5.3) |
| Nobreak SMS 1 500 VA senoidal | 2 321 | Kabum (§5.3) |
| Placa 2,5 GbE PCIe (o servidor tem 2 × 1 GbE) | ~150 | opcional: o uplink doméstico raramente passa de 1 Gbit |
| **Total** | **≈ 35 800 – 37 100** | |

**Por que é o 1º — e o que a refutação tirou dele.** Durante a crise de
DRAM, AM5 para em 128 GB sem ECC por R$ 16 mil e sem estoque; este servidor
traz **256 GB ECC já instalados**, no preço, em estoque. É isso que compra:
12 × a RAM de hoje (swap e earlyoom deixam de existir; dois ou três modelos
residentes ao lado das 9 sessões de Claude Code), ECC para uma fila SQLite e um
grafo que rodam 24/7 sem ninguém olhando, e 7 slots PCIe para a IA crescer.

O que **não** compra, e a primeira versão deste relatório afirmava errado:
**CPU.** O Ryzen 9 9950X (16 c) vence o EPYC 7413 (24 c) em single-thread por
2 × (PassMark 4 727 contra 2 400) **e em multi-thread por 30 %** (65 702 contra
50 641) — [7413](https://www.cpubenchmark.net/cpu.php?cpu=AMD+EPYC+7413&id=4346)
· [9950X](https://www.cpubenchmark.net/cpu.php?cpu=AMD+Ryzen+9+9950X&id=6211).
Os "3,6 GHz" do título são boost; a base é 2,65 GHz. Compilação Go e testes
ficam mais lentos aqui do que no 2º lugar. A banda de memória em CPU tampouco é
argumento: os 8 canais DDR4 dão 204,8 GB/s teóricos, mas o llama.cpp em Milan
mede ~57–70 GB/s efetivos (EPYC 7763, Llama-2 7B Q4 a 15 tok/s; o link de cada
CCD ao I/O die é o teto —
[Chips and Cheese](https://chipsandcheese.com/p/pushing-amds-infinity-fabric-to-its) ·
[llama.cpp #3167](https://github.com/ggml-org/llama.cpp/discussions/3167)).
Quem dá fluidez à IA é a RTX 3090; os 256 GB dão *capacidade* (MoE grande,
contexto longo, vários modelos), não velocidade.

**A bifurcação, dita sem rodeio.** Se o dono pesa **RAM hoje** (parar o swap, o
earlyoom, ter folga para IA e agentes ao mesmo tempo) e a chance de ter dois
GPUs, o 1º vence. Se pesa **velocidade de compilação, latência interativa e
plataforma com futuro de CPU**, o 2º vence — e a RAM entra quando o mercado
permitir. Este relatório escolhe o 1º porque o gargalo medido nesta máquina é
RAM e banda de IA, não single-thread, e porque o kit de RAM do 2º não está à
venda hoje.

**Caminho de upgrade — largo em GPU e RAM, fechado em CPU.** 7 slots PCIe
4.0 (128 lanes da CPU): 2ª RTX 3090 para 70 B, 3ª e 4ª se um dia fizer sentido,
10 GbE, HBA. RAM: 8 DIMMs povoados com 32 GB; o realista é ir a **512 GB** com
8 × 64 GB RDIMM (2 TB exigiria LRDIMM de 256 GB, impraticável). **Socket SP3 é
fim de linha**: Milan foi a última geração; o único passo é um 7763/7773X usado.
Em contraste, AMD confirmou AM5 até 2029, com Zen 6 e Zen 7
([Tom's Hardware](https://www.tomshardware.com/pc-components/cpus/amd-confirms-am5-support-through-2029-zen-4-and-5-platform-will-likely-see-two-more-generations-at-least)).
E a DDR4 também subiu 50 % em 2026
([hardware.com.br](https://www.hardware.com.br/noticias/preco-memoria-ddr4-alta-50-2026/)).

**O caminho para 70 B custa mais do que a 2ª placa.** 2 × 3090 (350 W cada;
Strix/FTW3/Suprim chegam a 400–450 W e 3 × 8-pin) + 180 W de CPU + ~100 W de
placa e 8 RDIMMs ≈ 980–1 050 W: a fonte de 850 W não segura. Exige fonte
≥ 1 200 W (R$ 1 500–2 500) **e** nobreak de 2 000–3 000 VA no lugar do de
1 500 VA (~900 W úteis). O caminho completo até 70 B fica em **≈ R$ 47 mil**,
não R$ 36 mil + uma placa.

**O que confirmar com o vendedor antes de pagar.** Primeiro: **a unidade
existe a esse preço?** A URL da página é de outro produto reaproveitado (slug
"epyc-7452… 128gb") — "1 em estoque" pode ser resíduo. Ligar ou mandar WhatsApp,
pedir foto do equipamento e nota fiscal, e checar CNPJ e reputação da Hard Leste
antes de qualquer outro passo. A mesma loja vende a versão de 128 GB + Windows por R$ 28 990 — R$ 3 040 **mais
cara** que esta de 256 GB — e avisa que ofertas são "sujeitas à análise de dados
e confirmação": risco de reprecificação, então travar preço por escrito. A loja
em si não levanta bandeira: domínio de 22 anos, loja física no Tatuapé (SP),
política de trocas só de produto novo, garantia de balcão
([política](https://hardleste.com.br/politica-trocas-devolucoes/) ·
[avaliações](https://avaliacoesbrasil.com/loja-de-informatica/sao-paulo/hard-leste-tecnologia/)),
e o preço é plausível para peças novas (7413 lista US$ 1 375; RDIMM 32 GB
US$ 63–150; placa ~US$ 600). Depois, o que a página não informa: modelo da placa-mãe (a ficha bate literalmente com a **Supermicro H12SSL-i**, ATX, 7 slots, 2 M.2,
IPMI — [Supermicro](https://www.supermicro.com/en/products/motherboard/h12ssl-i)), garantia e nota fiscal, se o processador é novo ou
retirado de servidor, se a fonte de 850 W tem **3 conectores PCIe 8-pin** livres
para a 3090, se o gabinete comporta placa de 31–34 cm de comprimento e 3 slots
de altura, e **qual é o cooler**: a H12SSL-i aceita cooler torre SP3 (Noctua NH-U14S
TR4-SP3), habitável em escritório; se vier blower 4U de 80 mm, não é. A licença do Windows 11 não tem uso aqui.

**Custos de operação.** H12SSL-i + Milan com 8 DIMMs mede ~105 W em idle na
tomada ([STH](https://forums.servethehome.com/index.php?threads/amd-epyc-milan-idle-power-consumption.34118/)),
contra ~60 W de um AM5: Δ 70 W × 8 760 h × R$ 0,85 ≈ R$ 520/ano, R$ 1 560 em
3 anos — menos de 5 % do preço, não inverte o ranking. A R$ 0,85/kWh e 24/7, com a 3090 trabalhando parte do
dia: ~180 W médios = 130 kWh/mês ≈ **R$ 110/mês**, contra R$ 10 do notebook.

### 2º — AM5 Ryzen 9 9950X + 96–128 GB DDR5 + RTX 3090 usada — ≈ R$ 31 000 – 35 000

| componente | preço R$ |
|---|---|
| Montagem 16 c / 96–128 GB (§5.3): 9950X 3 400 + X870 1 899 + RAM 12 500–15 990 + NVMe 2 TB + 1 TB 3 394 + fonte 1 000 W 1 124 + gabinete e cooler 710 | 23 000 – 26 500 |
| RTX 3090 usada | 5 000 – 6 350 |
| Nobreak 1 500 VA | 2 321 |
| **Total** | **≈ 30 300 – 35 200** |

**Por que é o 2º e não o 1º.** É a máquina mais rápida da lista em CPU —
2 × o EPYC 7413 em single-thread e 30 % acima dele em multi-thread (PassMark,
§6 1º), com AM5 garantido até 2029 — compilação de um pacote isolado,
testes serializados e a resposta interativa do Claude Code ficam melhores que no
EPYC. Plataforma de 2025: PCIe 5.0, DDR5, 2,5 GbE e USB4 na placa, idle de ~60 W.
Mas a RAM está **sem estoque** e custa R$ 12–16 mil por 96–128 GB, sem ECC, e a
placa só aceita 2 módulos em velocidade cheia: 128 GB é o teto prático. Um só
slot x16 real — a 2ª GPU vai num x4, o que serve para inferência dividida, mas
não para mais nada.

**Caminho de upgrade.** AMD garante AM5 até pelo menos 2027: Zen 6 entra no
mesmo socket. GPU troca livre (PCIe 5.0 x16). RAM: se começar com 2 × 48 GB,
o passo seguinte é vender e comprar 2 × 64 GB — não há 3º e 4º slots úteis.

### 3º — AM5 Ryzen 9 9900X + 64 GB + RTX 3090 usada — ≈ R$ 25 000

Montagem 12 c / 64 GB (§5.3) R$ 17 373 + 3090 R$ 5 000–6 350 + nobreak R$ 2 321
= **≈ 24 700 – 26 000**. É o piso que ainda resolve os três gargalos: 64 GB
zera o swap de hoje, 12 núcleos triplicam a compilação, a 3090 dá a IA fluida.
O que se perde: folga de RAM para dois modelos residentes ao lado de 9
sessões de Claude Code — 64 GB é o mínimo da §3, não o confortável. Caminho de
upgrade igual ao 2º (mesma placa X870 se escolher desde já; a B650M do
orçamento tem 2 M.2 e 2,5 GbE mas menos lanes). Faz sentido só se o dinheiro
for a restrição dura hoje e a RAM for trocada quando os preços normalizarem
(TrendForce fala em 2028).

### 4º — Strix Halo 128 GB (Framework Desktop / GMKtec EVO-X2, importado) — ≈ R$ 23 000 – 30 000

Ryzen AI Max+ 395: 16 núcleos Zen 5 + Radeon 8060S com **128 GB unificados** a
~256 GB/s teóricos (180 GB/s medidos). É a única opção da lista que cabe 70 B
Q4 **e** gpt-oss-120b sem GPU dedicada, consumindo ~100 W de sistema em carga.
Medido: 8 B a 42 tok/s, 24 B a 14, 70 B a 5,0 tok/s. Por que fica em 4º apesar
disso: **não se vende no Brasil** (US$ 1 999 → ≈ R$ 21 100 com II 60 % + ICMS,
RMA para EUA/China), exige **kernel ≥ 6.16.9** — acima do 6.12 do Debian 13, o
que obriga backports —, e o caminho de upgrade é o mais estreito de todos: RAM
soldada, sem slot x16 (Framework tem 1 × PCIe x4; EVO-X2 tem OCuLink para eGPU
externa). É a melhor máquina de IA *por real* e a pior em "adaptável a hardware
posterior", que foi um dos dois critérios do dono.

### 5º — PC pronto Ryzen 9 7950X3D + 64 GB + RTX 4090 (Terabyte "PC do Yoda") — R$ 19 241, hoje esgotado

Quando estava em estoque, era anomalia: a 4090 sozinha custa R$ 13 660. Vem com
16 núcleos Zen 4, 64 GB, 2 TB NVMe e a GPU nova mais rápida que a 3090 (49 tok/s
no 14 B, medido). Fica em 5º porque **não está à venda** — nenhum PC pronto com
4090/5090 e 64 GB estava disponível em 2026-09-09 (Kabum confirma estoque zero
pela API; Terabyte esgotado). Se reaparecer nesse preço, é compra imediata:
trocar o NVMe por um de alta TBW, somar nobreak (R$ 2 321) e vender a licença de
Windows. Upgrade: AM5 (Zen 6), 2 DIMMs livres na maioria das placas X670 (mas com
a queda de velocidade da §5.3), 2ª GPU no x4.

### O que ficou de fora, e por quê

- **RTX 5090 / 4090 novas**: R$ 22–27 mil e R$ 13,7 mil, esgotadas; 32 GB ainda não cabem 70 B. A 3090 dá o mesmo "cabe 32 B" por 1/4 do preço.
- **RTX 5070 Ti / 5080 / RX 9070 XT (16 GB)**: em estoque e mais baratas por placa, mas 16 GB não cabem 32 B Q4 — o objetivo "IA mais inteligente" morre nelas.
- **RX 7900 XTX 24 GB**: esgotada; driver AMD no Debian só por Vulkan, sem certificação ROCm.
- **Radeon AI PRO R9700 32 GB nova, R$ 12 999** ([Full Info](https://www.fullinfoinformatica.com.br/placa-de-video-power-color-amd-radeon-ai-pro-r9700-32gb-gddr6-pci-e-50-x16-256bit-ai-pro-r9700-32g-b), Pix, "30 dias úteis" = importação sob encomenda): apareceu na refutação. Cabe 32 B Q4 com 12 GB de folga, 300 W, blower de 266 mm, **com garantia** — a alternativa para quem recusa placa ex-mineração. Contra: 640 GB/s (−32 % contra a 3090), RDNA4 exige kernel ≥ 6.13 e ROCm por dkms (Debian 13 traz 6.12: backports), e 2,3 × o preço da 3090.
- **Threadripper 7960X (Atainfo, R$ 75 mil) e Rocketz Heavy V (R$ 76 mil+)**: 2–3 × o preço do 1º pela mesma classe de resultado.
- **Dell Precision 5860 (8 c) / 7875 (sob consulta) / Lenovo ThinkStation (403)**: não cumprem núcleos, não têm preço público ou não puderam ser lidos.
- **Mac Studio**: descartado por regra (§3) — a operação inteira é systemd.
- **Intel Core Ultra 9 285K**: esgotado; P/E-cores pedem kernel ≥ 6.14 para agendar bem; AMD homogêneo é mais previsível para compilação e agentes.

---

## 7. Depois de comprar: o que a migração exige

1. **Debian 13 limpo** (kernel 6.12). Reproduzir o host a partir de `ops/host-state/CHECKLIST-REBOOT.md`: units, slices, drop-ins, symlinks em `/etc`, earlyoom, TLP. O `wikijuridica-energia.service` (RAPL do i7-8565U) não se aplica à máquina nova — desativar, não portar.
2. **Driver NVIDIA** do `non-free` + CUDA; remover `Environment="OLLAMA_LLM_LIBRARY=cpu"` de `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`; subir `OLLAMA_MAX_LOADED_MODELS` para 2–3 e `MemoryMax` do Ollama de 15 G para o que a RAM nova permitir. Remedir `qwen2.5-coder:14b`, `qwen3.5:9b` e um 32 B com `medir_modelo` e gravar em `CLAUDE.md` §IA local no lugar dos 1,85 tok/s.
3. **Disco**: sistema no NVMe de alta TBW; o disco de backup fica **físico separado** como manda `wikijuridica-backup.service`. Monitorar `Percentage Used` do novo disco desde o dia 1 (`smartctl`), porque os 894 GB/dia vêm da carga, não do disco velho.
4. **Rede**: cabo até o roteador. Os 5 `cloudflared` continuam iguais; `wikijuridica-network-health` perde as métricas de WiFi e ganha as de link Ethernet.
5. **Nobreak**: `apcupsd` ou NUT com desligamento ordenado a 30 % de bateria — `cerebro` e `wikijuridica-server` param por SIGTERM (já tratado, `TimeoutStopSec=240`).
6. **Cérebro**: com GPU, `--max-lote 3` e um worker deixam de ser o teto. Subir workers e lote com a fila de 8 892 tarefas pendentes como bancada de medição.
7. **Notebook atual**: vira réplica fria do backup ou máquina de teste de `CHECKLIST-REBOOT.md`. O SSD dele (49 % usado) não deve receber carga nova.

---

## 8. Proveniência

- Medições locais: comandos citados na §1 e §2, executados em 2026-09-09 entre 10:50 e 11:10 (-03) por esta sessão.
- Preços: quatro pesquisas paralelas em 2026-09-09 (GPU; plataforma AM5; máquinas prontas e Strix Halo; benchmarks), cada linha com URL. O autor abriu ao vivo e conferiu: Kabum 5070 Ti (R$ 10 799,91, em estoque), Kabum 5090 (esgotada), Kabum 9950X (R$ 3 399,99, 48 un.), Kabum NV3 2 TB (R$ 2 349,99), Hard Leste EPYC 7413 (R$ 25 950, 1 un., especificação completa), radarram Fury Beast 64 GB (R$ 8 999,99–10 999,99, sem estoque), Debian 13 (kernel 6.12), Kingston NV3 (320 TBW), ANEEL (R$ 849/MWh projetado). Mercado Livre devolve página de verificação a leitura automatizada: os preços de RTX 3090 são do título indexado e exigem abrir o anúncio à mão.
- Refutação adversarial (agente independente, 2026-09-09, 58 consultas): derrubou o argumento "24 núcleos" (PassMark: 9950X vence em ST e MT) e o custo do caminho 70 B (fonte ≥ 1 200 W + nobreak maior); enfraqueceu a banda de Milan (~57–70 GB/s efetivos), o "adaptável" (SP3 fim de linha, AM5 até 2029), a ficha da oferta (base 2,65 GHz, reprecificação) e acrescentou a R9700 32 GB; não derrubou a legitimidade do vendedor, a conta de energia (Δ R$ 520/ano), a exclusão das placas de 16 GB (Qwen2.5-32B Q4_K_M = 19,85 GB, IQ4_XS = 17,69 GB — [bartowski](https://huggingface.co/bartowski/Qwen2.5-32B-Instruct-GGUF)) nem a crise de DRAM (DDR5 +500 % a/a em ago/2026 — [ultimaficha](https://ultimaficha.com.br/2026/08/17/ddr5-precos-aumento-2026/)). Tudo o que sobreviveu está na §6 com URL.
- Benchmarks: fontes primárias listadas na §4; regra banda ÷ bytes calibrada em 0,85–0,90 contra esta máquina e contra um 5950X medido.
  **Superado em 2026-09-16 quanto ao coeficiente:** 0,85–0,90 vale para as linhas de CPU; as de GPU desta tabela já embutem 0,39–0,44, e a RTX 5060 Ti foi medida em 0,648–0,660. Ver a nota datada sob a §2.1 e `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md`.
