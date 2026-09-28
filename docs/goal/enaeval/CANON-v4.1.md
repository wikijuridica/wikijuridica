# CANON v4.1 — NÚMEROS E DECISÕES CANÔNICAS DA WIKI JURÍDICA IA-FIRST / EnaEval

**Data-base 22/09/2026 · ID FIX-B · substitui `CANON-v4.md` e, por ele, `CANON.md` (v3) integralmente.**

**O que a v4.1 muda em relação à v4** (arbitragem do orquestrador no ADENDO de `DECISOES-ORQUESTRADOR.md`
depois dos 19 achados do crítico H01; as 12 decisões viraram 17):
| # | Mudança | Origem |
|---|---|---|
| 1 | Orçamento com **DOIS PERFIS do escalonador** (`regime` 36.185 = 79,4% · `construcao` com o backlog) | D-10' · H01 G1 |
| 2 | **Debate é UM produto com dois perfis de custo**; "1.000 rodadas × 9,25" e "599 threads + 120 rodadas" morrem | D-10' · H01 G1 |
| 3 | **6,41 GB (5,97 GiB)** bruto — o "6,41 GiB" era erro de unidade | D-15 · H01 G15a |
| 4 | **Receita do 8B** explícita (artefato `nvidia/Qwen3-8B-NVFP4` + fallback numérico) | D-15 · H01 G18 |
| 5 | **Toolchain `go 1.25` pinado** (go-sdk exige ≥ 1.25); "Go 1.27" era alvo sem artefato | D-16 · H01 §5(a) |
| 6 | **4 personas / 4 pubkeys** (advogado tem sub-papel autor/réu com a MESMA identidade) | D-15 |
| 7 | **`cache_state_digest`** em todo recibo; verificação com `cache_salt` por requisição | D-2' · H01 G10 |
| 8 | **τ nunca hardcoded**: `verify_config` é a fonte única em SQL, Go e JSON | D-13.3 · H01 G7 |
| 9 | **`resolution.oracle_receipt` NOT NULL** com cadeia DataJud C1+; payout só por Plano-T | D-13.3 · H01 G11 |
| 10 | **G03 fase B**: "1,2 M núcleo-s/dia" era erro de unidade ⇒ total DE FASE | D-10' · H01 G2 |
| 11 | **RAM nova (3.030 MiB) no envelope rotativo**, nunca residente | D-10' · H01 G3 |
| 12 | **Zero cronograma**: F04 §4.2, F11 (SOB-0…SOB-4), G02, G04 e §4 deste arquivo reescritos | D-11' · H01 §4 |
| 13 | **SCHEMA-v4.1** substitui SCHEMA-v4; catálogo do G06 substituído pelo gerador (D-5') | D-13.3/D-14 · D-5' |
| 14 | **Qwen3.5 = Experimento E1 com três portões**; o EnaEval nasce em Qwen3-8B denso | D-1 |
| 15 | **OPD → RLVR** em duas etapas com portão G5/WJ-Retro entre elas | D-4 |
| 16 | **Eviction proibida em ⟨PROVA⟩; quantização certificada permitida** (WitCert) | D-3 |
| 17 | **λ_gpu vira vetor `[classe][hora]`** | D-9 |

Este arquivo é a **fonte única de verdade**. Qualquer relatório em `research/` ou `research-v4/` que conflite com ele está superado. A síntese e a tasklist consomem **este** arquivo, não os relatórios.

**Hierarquia de autoridade:**
`CORRECOES-DONO.md` > **medição ao vivo com evidência reproduzível (script/log)** > `E04` (auditoria) > reconciliações (`E02`/`E07`/`F04`) > demais relatórios.
Onde dois relatórios mediram valores diferentes, prevalece o mais recente **com evidência reproduzível**.

**Companheiros normativos deste arquivo:**
`research-v4/LEDGER-CORRECOES.md` (62 decisões da reconciliação + os 19 achados do H01, G1–G19) ·
`research-v4/SCHEMA-v4.1.sql` (schema consolidado; **SCHEMA-v4.sql fica como histórico**) ·
`research-v4/ATAQUES-v4.1.sql` + `ATAQUES-v4.1-resultado.txt` (**94 recusas / 13 aceites / 0 falhas**) ·
`research-v4/fixes/g01_schema_v41.sql` + `fixes/g01_ataques_v41.sql` (**33 recusas / 0 violações de integridade**) ·
`research-v4/fixes/g02_schema_v41.sql` (o G02 não tinha SQL — H01 G6) ·
`research-v4/orcamento/orcamento_v4.py` (**os dois perfis, toda linha com fonte**) ·
`research-v4/fixes/grep_cronograma.sh` (varredura D-11': **24 → 0 violações**) ·
`research-v4/tools/catalog.json` (saída do gerador `cmd/enaeval-catalog` — o catálogo manual do G06 morreu, D-5').

**Regras de redação que valem para todo documento derivado deste:**
1. **Nome do bot: EnaEval.** Nunca "a plataforma", "a casa" ou "o bot".
2. **Nada em dias, semanas ou meses como CRONOGRAMA.** Fases e objetivos com critério de pronto. Onde aparecer "dia" neste arquivo, é **unidade de medida de compute ou prazo normativo** (SLA, quarentena, vigência) — nunca plano.
3. **Hardware exato.** Sem nuvem, sem aluguel, sem compra. Se um cálculo não fecha, a resposta é engenharia de alocação.
4. **Nenhum número do dono é reaberto, "validado" ou relativizado.**
5. **Contagem de teste é resultado de execução, nunca de resumo** — toda contagem aqui traz o comando que a produz.

---

## §0 · IDENTIDADE

- **EnaEval** — o bot soberano da Wiki Jurídica. Pequeno, montado com o melhor de cada IA aberta componente a componente, compactado para o hardware exato, **100% local em inferência**, código auditável.
- Emissor de chaves e recibos: **a PJ**, `did:web:wikijuridica.com.br` (fixado por CHECK no schema, nunca a PF).
- Servidor MCP em produção: `br.com.wikijuridica/acervo-juridico` v1.2.0, registrado no MCP Registry oficial.
- **Quatro personas, quatro pubkeys** (D-15). Cada uma é uma linha da tabela `agent` com `pubkey` e
  `rep_wjr` visíveis externamente: **advogado, juiz, promotor, jurista**. O **advogado tem sub-papel
  `autor`/`réu` com a MESMA identidade e a MESMA chave** — lado é atributo do lance (`arena_agent_role.lado`),
  não identidade. O 5º DID `agent:adversario` de `G02-code/personas.go:31-35` está **REVOGADO**: duplicava
  reputação da mesma persona e permitia que a casa lucrasse contra si mesma sem que o log mostrasse.
- **Assinatura de exemplo nunca parece real** (D-15): todo placeholder recebe prefixo `EXEMPLO-` e `kid`
  `example`; `payout_batch.frost_kid = 'example'` é recusado pelo banco.

---

## §1 · BASELINE E META (dono, 22/09/2026 — não se reabre)

| Canal | Valor canônico | Origem |
|---|---|---|
| **Citações por IAs** | **≥ 3.300/dia** (quase 100.000 em menos de 30 dias, com servidor **instável**; migração para o servidor novo em curso ⇒ vai crescer) | CORREÇÕES §7 |
| **Crawls de IA** | **6.086/dia** (42.601 leituras verificadas em 7 dias; GPTBot 27.685/semana) — canal **distinto** da citação | CORREÇÕES §5 |
| **Tráfego humano** | substancial; **terceiro canal**, modelado à parte | CORREÇÕES §5 |
| **API da rede social** | **~10.000 requisições/mês, hoje SEM conteúdo** — o contrato de payload é entrega obrigatória | CORREÇÕES §7 |
| **Acervo** | **18.774 páginas** (`llms.txt`; +69% sobre as 11.106 de 16/09); sitemap com 60 partições e 18.815 URLs; `/changes.json` com `content_sha256` por URL | F06 §1 [M] |
| **Rendimento atual** | **0,176 citação/página/dia** (3.300 ÷ 18.774) | derivado |
| **Meta** | **100.000 citações/dia** ⇒ fator **≈ 30×**; a 18.774 páginas seriam 5,33 citação/página/dia | derivado |

**Não existe teto de crescimento.** Toda curva é **piso**, nunca teto. É proibido escrever "platô", "limite do mercado" ou "saturação" como restrição do projeto. Expansão (PT/África, espanhol/LatAm, common law pelo mesmo motor) é caminho, não hipótese.

### Já no ar (a camada de protocolo é de classe mundial — o sistema nasce EM CIMA disso)
`/mcp` com 15 ferramentas · agent-card A2A · ai-catalog · `api-catalog` (`application/linkset+json`, RFC 9727) · `openapi.json` (13 operações) · `/api/v1/lote` NDJSON · `/api/v1/citacoes` (= `/verify`) · 6 datasets abertos com sha256 (585.592 registros) · `llms.txt` · CSL-JSON · `repr_digest` RFC 9530 · `feed.xml` (Atom, 1.000 entradas) · `rss.xml` · `security.txt` · `politica-de-uso.json` · `mcp/server-card.json`.

### Defeitos MEDIDOS a corrigir (F06 §1, n=80 estratificado por `lastmod`)
| Defeito | Medição |
|---|---|
| Dois títulos por página | **87,5% (70/80)**, IC95 [78,2%; 93,8%] ⇒ ~16,4 mil páginas |
| Markdown diferente pelas duas portas (`Accept:` × `/index.md`) | **60% (12/20)**, IC95 [36%; 81%]; nos 12, o `version` da porta negociada é órfão |
| HTML sem `ETag` | **80/80** |
| HTML sem `Link rel="cite-as"` | **80/80** (o Markdown tem, 80/80) |
| Ferramentas MCP sem `title` | **15/15** (MCP 2026-07-28 exige) |
| `Last-Modified` ≠ sitemap | 2/80 (páginas `/diarios/`: cabeçalho = hora do build) |
| 404 que deveriam ser 200 | `/.well-known/http-message-signatures-directory` · `rsl.xml` · chave IndexNow · `did.json` · `lar/checkpoint` · `scitt-keys` |
| `robots.txt` | 3.501 B; `Content-Usage` **sem `ai-use`**; grupo Bingbot/adidxbot sem sinais; sem diretiva RSL `License:` |
| `security.txt` | faltam `Policy`, `Encryption`, `Acknowledgments` e a assinatura OpenPGP |
| Camada de bytes | **0/80 violações** de `html_sha256`/`markdown_sha256`/`version`/`Repr-Digest` — o problema é de **identidade**, não de hash |
| Outros | IndexNow 404; Googlebot lê 10,9 páginas/dia; Claude = 0 leituras de crawler (chega por MCP connector / web_search); nenhuma rota devolve 402 |

---

## §2 · HARDWARE EXATO (CORREÇÕES §6 — definitivo; não há upgrade, compra ou nuvem)

| Peça | Especificação canônica |
|---|---|
| CPU | **AMD Ryzen 7 9800X3D** — 8C/16T, L3 96 MB (3D V-Cache), AVX-512 |
| GPU | **NVIDIA RTX 5060 Ti 16 GB** — GB206, sm_120 (Blackwell), 36 SM, GDDR7 128 bit × 28 Gbps = **448 GB/s**, TGP 180 W, PCIe 5.0 x8 no slot Gen5 x16 |
| RAM | **32 GB DDR5-6000 dual-channel (2×16)** — **NÃO SERÁ AMPLIADA** |
| Armazenamento | **NVMe 4 TB, ~6.000 MB/s** (perfil Kingston NV3 4 TB: 6.000/5.000 MB/s, 1.280 TBW, DRAM-less) — é a **terceira camada de memória**: mmap, offload de KV, índice em disco, hot-swap de modelo |
| Placa-mãe | ASRock B850 Pro-A ATX |
| Energia | Nobreak. **Power limit mínimo desta placa = 150 W** (não 160) |
| Extras | Notebook antigo como nó secundário (roda serviço e é **testemunha** do log). Cloudflare ativo |

**Hierarquia de memória em 4 camadas:** L3 96 MB → VRAM 16 GiB → RAM 32 GiB → NVMe 4 TB.
Restaurar do NVMe um prefixo de 8k custa **78 ms (9,54 µs/token)**; recomputar custa **4,70 s**. A carga é assíncrona e se sobrepõe à fila: o **TTFT p95 de 423 ms em c=16 se mantém** mesmo com o prefixo vindo do NVMe.

**Energia:** 272 W em regime = **R$ 252,46/mês**; 302 W e R$ 279,88 em construção.
**Nobreak (Peukert, não linear):** **6,3–19,7 min a plena carga** (o cálculo linear do D07 dizia 15,2/39,1 — era o dobro). Consequência: entra **escada de alívio de carga em bateria**, não um desligamento único.

---

## §3 · COMPUTE (24/7 contínuo — números do F04, `orcamento32.py`)

**A máquina roda 24 h/dia, 7 dias/semana.** Não existe "janela noturna". Orçamento de GPU = **86.400 GPU-s/dia**, não 28.800.

### RAM — fecha em 32.768 MiB
| Item | Valor |
|---|---|
| Comprometido (Perfil N, regime 24/7) | **25.854 MiB = 25,25 GiB** (alvo ≤ 28 GiB) |
| Margem | **2.818 MiB** |
| Piso de page cache protegido | **4.096 MiB** |
| Reservado antes do userspace | 2.034 MiB (UEFI/ACPI/PSP+iGPU 662; `memmap` 512; kernel 60; kernel dinâmico ~800) |
| Disponível para userspace + page cache | **30.734 MiB** |
| **Envelope arrendável** | **6.656 MiB**, **um locatário por vez** |

O E02 pedia 60,60 GB residentes. **Saem 49,3 GB** (15,95 de backup de sleep; 12 de `shared_buffers` — de 16 ficam 4; 9,0 do LightGBM; 3,2 do índice denso; 5,05 da plataforma; 1,48 do CSR; 1,35 da trie; 0,75 do ONNX; 0,5 dos serviços Go). **Entram 7,9 GiB** que o E02 não contava (host do vLLM 3,5; staging de KV 1,0; reranker 0,375; ingestão 1,0; kernel 1,99).

**A RAM não é partição estática.** Locatários do envelope, um por vez: professor P0, LightGBM, OCR, embeddings, QLoRA, BitNet em failover, TTS. Árbitro: **`wj-memd`**, leilão com preço-sombra **λ_ram**, imposto pelo kernel via **cgroup v2**. Todo trabalho que o v3 queria residente em paralelo roda, na mesma RAM, **em sequência**.

**RAM NOVA declarada pelos relatórios F/G: 3.030 MiB** (F01 389 · F02 1.229 · F07 1.024 · G01 300 ·
G02 24 · G04 64). Como **residente** seria **108% da margem elástica** — estoura em 212 MiB (H01 G3).
**Decisão D-10': entra no ENVELOPE ROTATIVO (45,5% dele), nunca como residente.** O maior locatário
isolado (F02, 1.229 MiB) ocupa 18,5% do envelope: cabe com um locatário por vez.
**Regra nova e obrigatória: nenhum relatório declara RAM sem linha no `F04-code/orcamento32.py`.**

### Professor — dois regimes (Gemma-4-26B-A4B)
| Regime | Como | Custo | Quando |
|---|---|---|---|
| **P0** (co-residente) | podado por **REAP a 64 experts/camada** (arXiv 2510.13999), experts **IQ4_XS = 6.263 MiB** no envelope, parte densa na partição MPS; **o 8B nunca sai da GPU** | escalada T2–T4 em **11,6 s** (SLA 30 s) | **toda escalada paga** |
| **P2** (troca) | EXL3 3,2 bpw (10,35 GB) entra na VRAM com o 8B em sleep nível 2 | round-trip **5,81 s** | construção e campanhas curtas |

**Resultado que define a política:** a fração de pedidos pagos preemptados é limitada pela fração do tempo em P2. Com ε = 1%, o P2 dispõe de **≤ 864 GPU-s/dia** em regime, qualquer que seja o tráfego. A troca só compensa com lote **N ≥ 47** itens de 1.000 tokens. O 8B serve sozinho quando a aceitação do professor supera a do 8B em **menos de 4,8%**.

### CPU
**255.256 de 691.200 núcleo-s/dia = 36,9%.** Folga: **435.944 núcleo-s/dia = 5,046 núcleos**
(o "436.320" da v4 era 5,05 × 86.400 arredondado; a subtração exata é a fonte — `orcamento_v4.py`).
**Demanda em regime: 85.917 = 19,7% da folga** (F01 54.106 · F03 290 · F07 30.000 · G01 716 · G02 805).
**G03 fase B não soma**: o "~1,2 M núcleo-s/dia" do G03 §6 era **ERRO DE UNIDADE** (1,74× a CPU inteira,
H01 G2). O correto é **1,2 M núcleo-s TOTAL DE FASE** (backfill de inteiro teor); em regime o trabalho
é o mesmo que o F01 já orça em 46.440/dia. Total de construção do G03 = **2,34 M núcleo-s = 6,69 CPU-dias
de máquina** no residual; backlog de CPU do F04 = 2,79 M = **6,4 CPU-dias de máquina**. Nenhum trabalho de lote divide núcleo físico com o caminho de latência. Conjunto quente no L3: **70,1 MB de 96**.

### GPU — **DOIS PERFIS DO ESCALONADOR** (D-10'; fonte executável: `orcamento/orcamento_v4.py`)
**Folga final: 45.600 GPU-s/dia (52,8%).** O orçamento **não é uma lista aditiva**: a leitura literal do v4
dava **101,0%** da folga (H01 §1, cenário A) porque três documentos contavam o MESMO produto três vezes.

**Regra que fecha o buraco:** *uma thread de caso S1/S2/S3 do G02 **É** uma rodada de arena do G01* —
mesmos 4 papéis, mesmo commit-reveal, mesmo mercado ancorado em `/predict`. É **UM produto** (`debate`)
com **dois perfis de custo**: `leve` **18,29 GPU-s** (lote ×4, sem os papéis assimétricos) e `arena`
**41,0 GPU-s** medidos (46,9 com parecer do MP).

**Perfil `regime`** — o 8B jurídico serve:

| Item | GPU-s/dia | % da folga | Fonte |
|---|---:|---:|---|
| F01 fluxo diário (30k decisões, DJEN, doutrina, ling. simples, 200 units) | 10.622 | 23,3% | F01 §—:431 |
| F03 paradigmas 310 + casos difíceis 612 | 922 | 2,0% | F03 §—:338 |
| F02 doutrina em regime (está DENTRO dos 5.501 do F01; contado por conservadorismo) | 580 | 1,3% | F02 §—:437 |
| G01 premeditação: extrator 4B em 11.600 chamadas/dia | 3.480 | 7,6% | G01 §—:307 |
| **DEBATE: 479 × 18,29 (leve) + 120 × 41,0 (arena) = 599 debates/dia** | **13.681** | **30,0%** | D-10' |
| F07 30 serviços, modo máximo (0 no modo padrão) | 2.900 | 6,4% | F07 §—:482 |
| G03 OCR de backfill, classe 4 preemptível (**substitui** os 600 de regime, não soma) | 4.000 | 8,8% | G03 §6 · H01 G19 |
| **TOTAL** | **36.185** | **79,4%** | |
| **SOBRA para treino de manutenção** | **9.415** | **20,6%** | |

**Perfil `construcao`** — o 8B jurídico ainda está sendo construído e **não serve**; treino e indexação
são classe 1; semeadura a **25% (150 debates/dia)**; OCR a **50%**; F07 em modo padrão:

| Item | GPU-s/dia | Fonte |
|---|---:|---|
| deltas que sempre rodam (OCR 600 + mídia 110 + embeddings 100) | 810 | F04 §4.1 |
| DEBATE a 25%: 120 × 18,29 + 30 × 41,0 | 3.425 | D-10' |
| G03 OCR de backfill a 50% | 2.000 | D-10' |
| F07 em modo padrão | 0 | F07 §—:482 |
| **Reservado** | **6.235** | |
| **LIVRE para treino/indexação** | **80.165** | |

**Backlog de construção: 3.052.330 GPU-s**, 100% local (F04 2.365.989 + F02 545.000 + F03 65.270 +
G02 semente 36.571 + G03 C/D/E 39.500) ⇒ **zera em 38,1 GPU-dias de máquina** no perfil `construcao`
(35,7 sem a semeadura e o OCR — F04 §4.1). Em `regime` levaria **324,2 GPU-dias de máquina**: é por isso
que a ORDEM é **construir o modelo antes de ligar G01/G02 em regime** (H01 §7, obj. 8 antes de 11 e 12).
**A transição `construcao` → `regime` é OBJETIVO com critério de pronto (backlog = 0), nunca data.**
Unidade sempre em **GPU-dias de máquina** (medida física, D-11'), nunca "em X dias".

### Escalonador (design do E02, implementação do F04)
- **CONTÍNUO com preempção por prioridade**, nunca "dia serve / noite treina".
- Ordem: **tráfego pago > geração de answer unit > treino > OCR > mídia**. Treino roda em toda folga.
- Serving e lote **co-residentes** (MPS + vLLM `--scheduling-policy priority`). Preempção = **1 step (50–100 ms) sem perder KV**.
- O lote **FREIA** (20% → 5% dos SMs); **não desliga**. `vllm.Sleep` só para troca de modelo.
- **Sinal LATCHADO**, contínuo — o defeito do A05 (perda de requisição paga por sleep antes de checar fila) é estruturalmente impossível.
- TLA+ verificado: `EscalonadorGPU.tla`, **1.936 estados, 0 erros**. O `.tla` entra no CI.

### VRAM (16 GiB) — mapa canônico
Residente: **wj-llm-8b NVFP4 compactado (4,90 GB / 4,56 GiB)** + **wj-nli-54M** + reranker + auxiliares. **KV 5,00 GiB = 124.830 tokens** (c = 15,2 sessões de 8k, ou bloco CAG de 377.924 tokens). Lote 2,80 GiB. **Total 15,23 GiB ≤ 15,3 alvo.**
**Prefix caching é CONDIÇÃO DE VIABILIDADE**: sem ele o teto cai de 11.615 para 3.768 chamadas/dia.
**SWA 5:1 (BOSCH)**: 1,71× em 8k, 5,19× em 128k — **exige plugin vLLM** (§4).

### NVMe
**122,6 GB/dia de escrita** (WAL 6; WAL-G 2; Parquet 0,5; Victoria 4; **tier de KV 106,9**; swap 2; checkpoints 1; journald 0,2) ⇒ **28,6 anos a 1.280 TBW** (17,9 a 800 TBW). **Sem o portão λ_tbw, só o tier de KV gastaria o disco em 8,2 anos.**
Cotas: `corpus` 700 GiB, `pg` 1.700 GiB (entre outras).
**Úteis PARA DADOS: 3.606 GiB** (3.726 − 120 de SO/logs/swap; o F04 dizia 3.726 — H01 §1 adota 3.606).
Plano do G03 reproduzido (`G03-code/armazenamento/plano.py`): **1.847,3 GiB = 49,6% do disco e 51,2%
do útil**, com poda λ_disco só a 82%. O "ano-5 = 2,90 TB" do F08 conta **o mesmo corpus**: não soma.

### Preços-sombra (fonte única: tabela `shadow_price`)
O **λ_gpu deixa de ser preço de mercado** — não há mercado, o transbordo foi revogado — e vira **vetor interno**: **(λ_gpu, λ_cpu, λ_ram, λ_tbw)**.
- `λ_gpu = R$ 0,00090/GPU-s` (**custo de OPORTUNIDADE**, multiplicador de Lagrange do BwK; faixa do BwK [0,0005; 0,0030]).
- O número do B02 (**R$ 0,000060031/GPU-s**) continua vivo com **outro nome e outro uso**: custo de **energia**, conta 4.1.1 do ledger, margem contábil. **Nunca no leilão** — semear o leilão com energia trata GPU como quase-livre e aloca mal por 15×.
- **D-9: `λ_gpu` deixa de ser escalar e vira `λ_gpu[classe][hora]`.** Sob congestão, rotear ao 4B pode
  AUMENTAR o gasto por citação verificada (arXiv:2608.23986): um preço único mente sobre o custo marginal.
  Fonte única continua `econ.LambdaGPU()` (E07), agora com assinatura `(classe, hora)`. A mochila B do
  seletor do G02 passa a LER `shadow_price`, nunca uma constante.
- `λ_gpu` decide **fila, tiering e compactação**. Não decide compra: **o menu de capex sai da ADP** (§11).

---

## §4 · MODELOS (F11 corrige I.10.2, I.8.6 e o CANON v3)

### Tamanhos REAIS (medidos, não estimados)
| Componente | Bruto real | Servido (compactado) | Como |
|---|---|---|---|
| **wj-llm-8b** (Qwen3-8B, Apache-2.0) | 16,38 GB BF16 → **NVFP4 = 6.408.489.038 B = 6,41 GB (5,97 GiB)** | **4,90 GB (4,56 GiB)** | cirurgia de vocabulário **151.936 → 80.916** (o domínio jurídico usa 8.193 de 37.059 tokens) + `lm_head` **FP8** |
| **wj-llm-4b** (aluno, fast path após G1–G5) | 8,04 GB | **2,46 GB** NVFP4, V=80.916 | poda do 8B; contexto nativo 262.144 |
| **wj-llm-fast-1.7b** | **1,42 GB** (não 0,95) | **1,12 GB** | mesmo tokenizer de toda a pilha |
| **wj-teacher-gemma4** (Gemma-4-26B-A4B, Apache-2.0) | 51,6 GB BF16 | **10,35 GB** EXL3 3,2 bpw · ou **2,54 GB GPU + 12,13 GB** experts IQ4_XS | 30 camadas (25 SWA W=1.024 + 5 globais), 128 experts top-8, 25,23 B texto / ~3,82 B ativos |
| **wj-cpu-monitor** (BitNet-b1.58-2B-4T, MIT) | — | **GGUF i2_s 1,19 GB** | ternário nativo, 29 ms/token em CPU, 0,028 J/token |
| **wj-emb-query** (Qwen3-Embedding-0.6B) | 1,19 GB | **0,55 GB** ONNX int8 | Matryoshka MRL-512 |
| **wj-rerank** (Qwen3-Reranker-0.6B) | 1,19 GB | **0,61 GB** int8, V=80.916 | head de 2 linhas via `Qwen3ForSequenceClassification` |
| **wj-late** (próprio) | — | resíduo 2 bits 58 GB no NVMe; encoder de consulta 0,13 GB | tronco truncado a 6 camadas + projeção 64d, KL sobre Qwen3-Reranker-4B |

**"6,41 GiB" era ERRO DE UNIDADE (H01 G15a).** 6.408.489.038 B = **6,41 GB = 5,97 GiB**. Serviço = 4,90 GB = 4,56 GiB.
O **4,60 GB** do v3 saiu de circulação (LEDGER C3) e o **1,7B = 0,95 GiB** também (é 1,42 GB → 1,12 GB).

### Receita do 8B — o que baixar e em que ordem (D-15 · H01 G18)
O CANON v4 lia "6,41 → 4,90" como se fosse derivação do artefato pronto. **Não é.** A receita executável
está em `F11-code/recipes/` e tem dois caminhos, ambos locais e sem egresso na inferência:

1. **Caminho canônico (preferido):** partir do artefato **`nvidia/Qwen3-8B-NVFP4`** (hash no BOM, S3 da
   cadeia de licença) → `vocab_trim.py` (151.936 → 80.916) → `lm_head` **FP8** ⇒ **4,90 GB (4,56 GiB)**,
   mapa de VRAM **15,23 GiB ≤ 15,3**. O artefato da NVIDIA é também a **referência de KLD (R-eq, S4)**:
   o portão exige **KLD ≤ 10⁻³** contra ele.
2. **Fallback documentado (se o artefato sumir do índice local):** `Qwen/Qwen3-8B` **BF16 16,38 GB** →
   `vocab_trim.py` → `nvfp4_modelopt.py --head fp8` (low-memory + offload NVMe). **Se o loader
   "NVFP4 + `lm_head` FP8" não subir no vLLM** (não verificado no F11), cai para `--head bf16` =
   **5,23 GB (4,87 GiB)** ⇒ mapa **15,54 GiB > 15,3**: **o KV desce para 4,69 GiB (~117 k tokens, c ≈ 14)**.
   Esse número é registrado no recibo e no `promotion_gate`, não escondido.
**O portão G1 roda nos DOIS artefatos.** Nunca se serve um artefato que não passou G1 quantizado.

A cirurgia de vocabulário **se paga três vezes**: vale para o 8B, o 4B e o reranker (mesma família Qwen, mesmo tokenizer).

### Verificador — ÚNICO
**wj-nli-54M** = mmBERT-small (MIT) podado 140M → 54M, **cross-encoder**, **τ_NLI = 0,906** por controle conformal (Clopper–Pearson), **fail-closed no serializador**. **E7 = relevância obrigatória.**
O τ mora **numa só tabela** (`conformal_calibration` → `verify_config`, SCHEMA-v4.1), com
`CHECK (ub95 <= alpha)`: calibração que não controla o risco é inexprimível. **Nunca hardcoded, nunca por
cron** — recalibra pelo martingale de Ville (S_t ≥ 20 recalibra; S_t ≥ 100 retreina).
**D-13.3 item 5 (H01 G7): o 906 estava HARDCODED em quatro lugares** — `G01-code/go/arena/arena.go:267`
(`const TauNLI`), `g01_schema.sql:177` (`CHECK (entail_milli >= 906)`), `G02-code/verify.go:21`
(`const TauMilli`) e `G02-code/social-schemas.json:58` (`"tau_milli": {"const": 906}`). **Constante de
código não recalibra:** o martingale sobe e o τ fica onde estava. No SCHEMA-v4.1 a fonte única é a tabela
`verify_config`, a função `verify_cfg_vigente(escopo, at)` resolve o valor, e todo recibo (`citation_receipt`,
`prediction_receipt`) e todo lance que resolve (`arena_move`) apontam `cfg_id`. **Portão de CI:
`grep -rn "906" wj/ --include=*.go --include=*.sql --include=*.json` fora de `wj/verify/testdata` = 0.**

### Treino
- **BF16 real na 5060 Ti = 47,4 TFLOPS** (whitepaper Blackwell escalado) — **não ~200**. QLoRA-8B: **334 tok/s** em BF16.
- **FP8 (94,8 TFLOPS) é o PADRÃO de treino**: QLoRA-8B a **668 tok/s**.
- Pós-treino (**D-4, duas etapas SEQUENCIAIS, nunca simultâneas**): **etapa 1 = OPD** (on-policy
  distillation com IER, arXiv:2609.24432) → **portão G5/WJ-Retro OBRIGATÓRIO entre as etapas** →
  **etapa 2 = RLVR GSPO-DrC** (GSPO + Dr.GRPO + Clip-Higher). O portão é invariante, não recomendação:
  arXiv:2608.14610 mostra que RL geral **piora raciocínio temporal**, e vigência é o produto. Vigência
  como **PENALIDADE −0,60** elevada a INVARIANTE, piso 2/8 rollouts não-correntes.
  **`Scale-QLoRA` (arXiv:2609.04526) é OBRIGATÓRIO** para merge sobre NVFP4 — merge ingênuo perde até 39 pp.
  **GrowMTP entra como experimento**, nunca no caminho de promoção. **Quarentena de 30 dias antes de tocar peso.**
- Recompensa: **0,35 URN + 0,30 NLI + 0,10 formato + 0,10 concisão + E7 relevância − 0,60 vigência errada − 1,0 citação inventada**. Invariante: **alucinação ⇒ recompensa negativa**.
- Replay retemporalizado 25%; mistura 55/25/15/5. **Knowledge editing PROIBIDO em produção.** **S-LoRA + roteador discreto** (X-LoRA morto).
- Regra de transplante ("o melhor de cada IA"): **pesos só dentro da família**; **arquitetura só quando há método treino-livre** (BOSCH 5:1); **receitas sempre**; tokenizer e componentes inteiros só com portão medido; destilação entre famílias por sequência (Gemma) e por token (wj-8b).

### Contexto
**BOSCH SWA 5:1, W=4096** (1,71× em 8k, 5,19× em 128k). **O vLLM 0.29.0 de estoque NÃO serve BOSCH**:
o `Qwen2Model` aborta com `layer_types` misto ⇒ exige **plugin fora-da-árvore (~40 L, sala limpa)**.
**BOSCH é FASE PRÓPRIA COM PORTÃO (H01 G16), não pré-requisito do canário.** O canário sobe **sem**
BOSCH, com atenção plena e **KV 5,00 GiB = 124.830 tokens** — esse número já é o número sem-BOSCH.
Portão do BOSCH: G1 igual ao denso + **TTFT p95 < 500 ms**.

**D-3 — a regra de KV em ⟨PROVA⟩ foi REESCRITA.** Era "compressão de KV proibida em ⟨PROVA⟩". Passa a:
**EVICTION de token é PROIBIDA em ⟨PROVA⟩; quantização preservadora de cobertura é PERMITIDA sob
certificado** (WitCert, arXiv:2607.28699), com **fingerprint do certificado no recibo**. Ganho medido:
**1,88× tokens na mesma memória** sem perder o suporte da cadeia (arXiv:2608.01631). O serializador
verifica `evict ∩ span = ∅` — despejar um token do span é inexprimível, não "desaconselhado".

### Egresso zero em TRÊS camadas (S2 — fail-closed)
Três bibliotecas da pilha telefonam para casa **por padrão**: vLLM → `stats.vllm.ai`; FlashInfer → cubins de `edge.urm.nvidia.com`; Unsloth → README do HF.
1. **Kernel**: `IPAddressDeny=any` (cgroup-BPF) nas unidades dos Planos C e T.
2. **Opt-outs verificados no código-fonte**: `VLLM_NO_USAGE_STATS`, `FLASHINFER_CUBIN_DIR`, `HF_HUB_OFFLINE`, `UNSLOTH_DISABLE_STATISTICS`.
3. **Sonda**: `comp.EgressProbe` no boot e **a cada 5 min** contra 6 alvos (HF, stats.vllm.ai, edge.urm.nvidia.com, PyPI, 1.1.1.1, 8.8.8.8). **Um único `connect` que passe derruba o serving** (SEV1). No schema, "conectou sem incidente" é **inexprimível**.

### Soberania (S1–S6, cada um com teste que bloqueia merge ou serving)
S1 pesos locais · S2 egresso zero na inferência · S3 cadeia de licença auditável · S4 build reprodutível (**R-bit** para Go/GGUF/ONNX/tokenizer/trie; **R-eq** para NVFP4/EXL3/treino, KLD ≤ 10⁻³) · S5 ≥ 2 implementações por interface crítica · S6 quarentena de 30 dias.
**BOM: 27 componentes, 56 implementações.** Nenhum projeto de terceiro é ponto único. Toda resposta carrega **`bom_sha`**.
**Índice de soberania: 0,39 (estado SOB-0, hoje) → 0,87 (ao fechar SOB-4)**, sem nuvem.
**D-11': o roteiro por trimestre do F11 (Q4/2026 … Q4/2027) está REVOGADO.** As fases de soberania são
**SOB-0 … SOB-4**, cada uma com critério de pronto binário (F11 §—, tabela reescrita):
SOB-1 tokenizer e verificador próprios (L4/L3) · SOB-2 aluno 4B + `wj-rerank-54M` · SOB-3 encoder próprio
L4 (CPT MLM 20 B tokens ≈ **4,2 GPU-dias de máquina** em GPU cheia, ~7,6 na folga) · SOB-4 CPT do 4B e do
8B e professor próprio (5 B tokens ≈ **156 GPU-dias de folga** em FP8).

### Experimento E1 — Qwen3.5 (D-1): candidato com TRÊS PORTÕES, nunca base
O **EnaEval nasce em Qwen3-8B denso**, porque o pipeline LoRP/Minitron/EXL3/ModelOpt-NVFP4 foi validado
em denso (F11), não em híbrido. A evidência a favor do Qwen3.5 é grande demais para ignorar (G05, lendo
o `config.json` ao vivo): **KV/token 4,5× menor (16,0 KiB vs 72,0 KiB)**, MTP nativo, 262k de contexto,
Apache-2.0, BFCL-V4 66,1 / TAU2 79,1. A evidência contra também: **prefix caching — condição de
viabilidade deste CANON — não se aplica ao estado recorrente GDN sem Tail-Replay** (arXiv:2608.30310),
e o vocabulário de 248.320 obriga refazer a cirurgia do D04.
**E1 entra pelo registry (C05/G06) com três portões, todos obrigatórios:**
1. Tail-Replay (ou equivalente) mantendo **TTFT p95 < 500 ms** com cache quente em vLLM ≥ 0.30 em sm_120;
2. QLoRA/FP8 e quantização W4A4 NVFP4 funcionando no híbrido com **KL de calibração jurídica ≤ a do 8B denso**;
3. **não-inferioridade G2** no WikiJurídica-Bench **+ G1 no artefato quantizado**.
Se passar, substitui o residente e o KV liberado vai para concorrência. A proibição "Qwen3.5-4B como base"
fica restrita ao **VERIFICADOR** (que é mmBERT) e ao pipeline de poda **até E1 fechar**.

---

## §5 · STACK E VERSÕES (todas as correções aplicadas)

### Núcleo
Go (monorepo `module wj`, **`go 1.25` no `go.mod` + `toolchain go1.25.x` PINADO no BOM** — D-16; o
"Go 1.27" da v4 era alvo sem artefato, e `G04-code/enaeval/go.mod` já exigia `go 1.25.0` enquanto os
demais módulos diziam 1.24: com `GOTOOLCHAIN=local` e Go 1.24.7 o G04 **não compila**, e só compilou no
H01 porque `GOTOOLCHAIN=auto` **baixou** um toolchain — egresso silencioso em build, que o S4 proíbe.
`go-sdk` exige ≥ 1.25, e é esse o piso. Os módulos de pesquisa mantêm seus `go.mod` até a migração
(objetivo da tasklist). CI roda com **`GOTOOLCHAIN=local`**; 25 pacotes, `deps.yml` verificado por
`depcheck` **antes** de `go test`) · **Eino v0.9.19** (grafo de agente; o CI proíbe `schema.Jinja2` — template é código) · **River v0.47.0** (filas, MPL-2.0) · Task v3.51.1 · **hugot v0.7.8** + ORT 1.29 (ONNX em Go) · leaves (LambdaMART).

### Dados
**PostgreSQL 18** + **Apache AGE 1.8.0** + **pgvector** + **pgvectorscale** (StreamingDiskANN + SBQ + filtro por rótulo) + **pg_textsearch** (BM25 k1/b, Block-Max WAND).
- **VectorChord (`vchordrq`, `vchord_bm25`) REVOGADO** — AGPLv3-OU-ELv2; as duas saídas do dual-license são proibidas para serviço de rede.
- **AGE: `create_graph('wjg')`**. `create_graph('wj')` **FALHA** (`MIN_GRAPH_NAME_LEN = 3`). Sem *list comprehension* em Cypher no AGE 1.5.
- **AGE VLE PROIBIDO** (~14,3 GB por backend) → **CSR compacto em Go** (≤ 3 GB para 900 M arestas, forward push).
- Schema consolidado: **`research-v4/SCHEMA-v4.1.sql`** — carregado em banco NOVO em PG 16.13 + AGE 1.5.0
  (**123 tabelas, 11 views, 127 FKs, 23 triggers, 375 CHECKs**, exit 0), forward-compatible com 18.
  Com `fixes/g01_schema_v41.sql` e `fixes/g02_schema_v41.sql` por cima: **131 tabelas, 11 views, 139 FKs, 25 triggers, 402 CHECKs**.
  **`SCHEMA-v4.sql` fica como histórico.** O `g01_schema.sql` ORIGINAL **não carrega** sobre a v4.1
  (`cannot create index on relation "prediction"` — `prediction` virou VIEW, D-14): é por isso que existe
  a versão ajustada em `fixes/`.
- **Invariantes novos da v4.1** (todos atacados): `I-ORACLE-1/2` (resolução exige captura DataJud C1+;
  desfecho derivado do TPU) · `I-ARENA-3/4` (payout ≤ `b` do mercado por FK composta; só em lote FROST) ·
  `I-SOC-2/3/4` (comentário não afirma direito; ≥ 1 claim por post que afirma; segmento não verificado
  recusado sob escopo de selo) · `I-QUOTA-1/2/3` (cota por DID em PG) · `I-VERIFY-5` (τ com fonte única) ·
  `R7'` (`norm_rule` é tabela com FK; `wj-norm/f5-cspm@1` morreu).

### Serving e quantização
**vLLM 0.29.0 + FlashInfer 0.6.14** (sm_120) · **llama.cpp com CUDA 12.8** (13.1 quebra MMQ) · **ExLlamaV3 v1.4.8** · **ModelOpt** (NVFP4 PTQ) · **llm-compressor** como quantizador alternativo (o quantizador é superfície de ataque — AGENTQ, arXiv:2609.14060) · **bitnet.cpp** · **xgrammar** (compilação ~0,01 s vs 3,5–8 s do Outlines) · **DeepSpeed ZeRO-Infinity** (estados do otimizador no NVMe) · **MergeKit** (`della`/`model_stock`, LGPL-3.0 — ferramenta offline).

### Protocolos
**MCP go-sdk v1.8.0** (revisão 2026-07-28; `resources/subscribe` REMOVIDO; `$ref` de rede **proibido** em `outputSchema`; `title` obrigatório) · **A2A v1.0.0** · **x402** `x402-foundation/x402/go/v2` @v2.26.0 **em processo isolado `wj-x402d`** (o SDK puxa `go-ethereum` LGPL-3.0; o binário Go principal não pode linká-lo) · **Cedar** via `cedar-go v1.8.0` (**2 bundles**: `WJ::Compliance` 17 políticas + `WJ::Autoral` 20 políticas) · **Web Bot Auth** `draft-ietf-webbotauth-httpsig-protocol-00` · **SCITT RFC 9943** + **COSE Receipts RFC 9942** + **COSE Hash Envelope RFC 9995** · **LEX URN = RFC 9676** · versionamento por **RFC 5829** (não Memento) · Memento RFC 7089 só para `original`/`timegate`/`timemap`/`memento`.

### Documento e OCR (cascata, decide se recoleta em melhor qualidade)
| Estágio | Ferramenta canônica | Substituiu |
|---|---|---|
| 0 — determinístico | **PDFium via `go-pdfium` em WebAssembly/wazero** (PDF hostil analisado dentro de sandbox Wasm) | **MuPDF/go-fitz REVOGADO** (AGPL-3.0) |
| 1 — VLM leve | **PaddleOCR-VL-0.9B** ou **`opendatalab/MinerU2.5-Pro-2605-1.2B`** — **só os PESOS** (Apache-2.0), servidos pelo vLLM | o **pacote de CÓDIGO do MinerU** é licença própria com limiares de MAU/receita e rescisão automática ⇒ **REVOGADO**; a variante **2509 é AGPL ⇒ PROIBIDA** |
| 2 — escalada | **DeepSeek-OCR-2 (Apache-2.0) + PP-OCRv5** | **Chandra-OCR-2 REVOGADO** (OpenRAIL com teto de US$ 2 M) |
| 3 | fila humana | — |

Layout: **PP-DocLayout-L**. TTS: **Kokoro-82M + Chatterbox**. Vídeo: **LTX-Video 2B**. Áudio: **CTranslate2 / whisper.cpp** (int8).

### Log de transparência e integridade
**Tessera v1.0.4 (Apache-2.0)** como **escritor do log** (POSIX) · nota C2SP tlog-checkpoint · RFC 9162 · `model-signing` (OpenSSF) em modo chave privada · `modelscan`/`picklescan` **só na sandbox**.

### Observabilidade
VictoriaMetrics/Logs/Traces + **OTel Go v1.46** (GenAI) · MLflow 3.16.0 · WAL-G · Cloudflare Tunnel.

### Quarentena de cadeia de suprimentos
Nada de terceiro chega a produção com **< 30 dias de exposição pública do mesmo digest**. Em 22/09/2026, **14 pins do BOM ainda estão em quarentena** (7 deles vindos do CANON v3), incluindo **vLLM 0.29.0 (libera 09/10)**; liberação entre 23/09 e 18/10/2026. **Promoção bloqueada, desenvolvimento não.** Exceção única: CVE, caminho rápido ≤ 72 h com conformidade + Cedar + rollback armado.
**Pickle nunca entra no host de serving** (não existe como valor no schema). **Chat template nunca é executado** e nunca vem embutido no artefato.

---

## §6 · DIREITO (direito como código — eixo central)

### Correções normativas canônicas (F05, conferidas em fonte oficial)
| Tema | Regra canônica |
|---|---|
| **CPC art. 927** | Ganhou **III-A** (REsp por **relevância**) pela **Lei 15.484/2026, vigência 03/09/2026**. **NÃO** herda os efeitos dos arts. 311, 332, 496, 521 e 1.022. `N_RELEVANCIA_NEGADA` = CPC 1.035-A + 1.039 p.ú. |
| **Taxa legal (CC art. 406)** | **Res. CMN 5.171/2024**: `TL_m = Max[(Fator_Selic / Fator_IPCA-15) − 1 ; 0] × 100`, **defasagem de 1 mês** no IPCA-15. Reproduz **26/26 meses**. A leitura literal "Selic − IPCA" diverge **17,07% vs 16,279894%** oficial em 24 meses |
| **TR** | **SGS 7811 (mensal)**. **SGS 226 é diária e está ERRADA** para TR mensal (soma 2024: 0,9128% × 0,8112%) |
| **ITCMD-RJ** | **LC 227/2026** (DOU 14/01/2026) exige **alíquota progressiva por quinhão**; a lei estadual não foi adaptada ⇒ o motor devolve **`Instavel = true`** |
| **CP art. 115 / art. 65 I** | **Lei 15.160/2025** (DOU 04/07/2025) acrescentou a ressalva "salvo se o crime envolver violência sexual contra a mulher" — intertemporal, com marco no código. É a **mudança real** que provou o portão WJL007 |
| **TST E-ED-RR-713** | O acórdão cita "art. 406, parágrafo único"; a **Lei 14.905/2024 extinguiu o parágrafo único** — o correto é **§1º** |
| **INSS (RPS art. 33)** | Diverge do INPC em **1 ponto**: 02/2008 = 0,51% (RPS) × 0,48% (INPC). Divergência **bloqueia o cálculo** (`ErrDivergencia`), não vira nota de rodapé |
| **RJ Lei 7.174/2015 art. 26, I** | **Defeito no TEXTO OFICIAL**: numeral "4,0%" ≠ extenso "quatro e meio por cento" ⇒ intervalo + leitura adotada (WJL013) |
| **HTML do Planalto** | Nota editorial **sem parêntese fechado** quebra o parsing (CLT art. 146; Lei 9.873 art. 2º) ⇒ regra `incisos_reiniciados` |
| Outras que quebram tabelas | Lei 15.397/2026 (roubo 6–10, furto 1–6, receptação 2–6, latrocínio 24–30 — a NT TJDFT 10/2023 fica obsoleta **só para fatos posteriores**); Lei 15.159/2025 (agravante CP 61 II *m*); Lei 14.994/2024 (CP 129 §9º → 2–5); Lei 14.939/2024 (vício de feriado local vira sanável); **Lei 15.040/2024** (novo regime prescricional do seguro, *dies a quo* na recusa expressa — vigência **10 ou 11/12/2025**, tratada como `IntervaloData`) |

### Convenção de código
**WJ-LIT-1** — *literate law-as-code* em **Go**: importa-se a **semântica do Catala** (granularidade por artigo, padrão-com-exceção, gabarito oficial como teste), **recusa-se a cadeia de compilação OCaml**.
- **Âncora normativa é dado, não comentário**: cada função carrega URN LexML + SHA-256 da redação canônica + o texto + a fonte oficial.
- Linter **`wjlint`**, **17 regras (WJL001–017)**. A crítica é **WJL007 "REGRA DESATUALIZADA"**: hash da lei embutida ≠ vigente na data ⇒ **CI vermelho na regra exata** e, em produção, `regra_confirmada = false` **sem recompilar** (fail-closed).
- **Todo motor devolve `[mín, máx]` + a leitura adotada + o motivo** onde a lei admite mais de uma leitura. Número único que esconde a escolha é **defeito**, não simplificação.
- **Intertemporalidade é primeira classe**: cominação pela data do fato (CF 5º XL); redação histórica com `//wj:vigencia`; marco ambíguo vira `IntervaloData`.
- **Série oficial entra conferida adversarialmente ou não entra**: taxa legal 26/26 meses; fator previdenciário 733/733 células; RPS × INPC reconciliados.
- **O motor é o verificador da recompensa** ("LLM propõe, verificador dispõe"): os 15 motores + a Guarda são o erro **E5** e a recompensa **−1,0**.
- Execução verificada nesta sessão: `gofmt` limpo · `go vet` limpo · `go test` **11/11 pacotes OK** · `wjlint` **14 pacotes, 60 regras, 270 âncoras, 396 versões, 0 erros, 49 avisos** — idêntico ao declarado.

### Forma canônica de texto
**WJ-CANON-1** — byte-idêntica em **Python (ingestão), Go (linter e runtime) e PL/pgSQL (dentro do banco)**: **0 divergência** em 20 vetores + 396 registros. Sequência: **NFC** → remove tags → colapsa espaço → `º`/`°`.
**A composição NFC é obrigatória e verificada**: o HTML do CC/2002 tem 10 entidades de diacrítico **decomposto** (ex.: `ido&#770;neas`). O "NFC asserido" do A03/E07 vira **NFC verificado**.

---

## §7 · CONHECIMENTO — KNOWLEDGE CLAIM (F01, com as correções de F03/F06/F07)

**7 tipos, imutáveis, endereçados por conteúdo** (`ni:///sha-256` sobre o JCS do núcleo):
`NormClaim · HoldingClaim · ThesisClaim · DoctrineClaim · ProcedureClaim · DefinitionClaim · ConflictClaim`.

### Verificação por tipo (fail-closed)
`extractive` (substring do span canônico) é o **default**; `attributed_quote`; **`paraphrase` exige `quote_in_span` ∧ NLI ≥ τ**; `templated` exige toda evidência verificada; `computed` exige `deterministic_replay`. **O `verdict` só existe se a política passou**, e é sempre `span_entails_claim` — nunca "verificado", nunca "verdadeiro no mundo".

### Correções aplicadas ao modelo do F01
| Campo | Correção | Pedido por |
|---|---|---|
| `forca927` | **+ `III_A_resp_relevancia`** (Lei 15.484/2026) | F03 |
| `forca927` | **+ `administrativa_vinculante`** (súmula CARF/TCU, parecer AGU LC 73/93 art. 40 §1º) | F07 |
| `legalTime.mode` | **+ `condicional`** (eficácia dependente de evento futuro verificável — meta fiscal da LDO, regulamento pendente) | F07 |
| `DefinitionClaim.kind` | **+ `oficial_tpu`** | F07 |
| novo campo | **`assertion_es`** (≤ 600 chars) — a expansão para espanhol/LatAm é caminho, não hipótese | F07 |
| perfil | **`cp1`** — projeção compacta, default | F07 |
| `thesis.estado` | **8 → 15 estados** (Portaria CNJ 116/2022, Anexos I e IV) | F03 |
| âncora LexML | fragmento de parágrafo único de artigo hifenizado = **`!art59-1_par1`** | F01 §I.5 |
| `spans-medidos.json` | `man_len`/`man_sha256` são os **PÓS-normalização F5**, não os bytes brutos | F06 |
| registro de URN | **`wj`** para **súmula, enunciado e informativo** (não existem no registro LexML): cunhados pela gramática LexML, resolvem em `/k/urn`. `lexml` para o resto | F01 D5 |

### Span DUPLO (obrigatório)
`raw` = bytes como servidos (offset, len, sha256) **+** `text` = SHA-256 do texto canônico UTF-8 **NFC** com `canon: "wj-canon-1"`. Resolve fonte cp1252/PDF e torna o hash reproduzível por terceiro.

### Normalização de fonte — nome canônico
**`wj-norm/f5-cspm-tail-v1`** (o F08 chamava `wj-norm/f5-cspm@1`; vence o F06 porque o contrato **C26** já publica `/.well-known/lar/norms/f5-cspm-tail-v1` e o nome entra **assinado** em `man_norm` dentro de cada recibo).
**O que a regra faz:** o balanceador F5 do Planalto injeta, no fim de ~5/7 das respostas, um `<script id="f5_cspm">` de **1.559 B** com token por resposta. Oito cópias da CLT deram **7 SHA-256 brutos distintos e 1 normalizado** (`82499b3d…`, 3.529.642 B = o próprio campo de tamanho do `ETag` do servidor, 0x35DBAA). Sem a regra, `man_sha256` é irreprodutível, `egress_agree` dá falso negativo e o monitor de frescor dispara à toa.

### Serialização e economia de contexto
Quatro serializações: **JSON-LD 1.1 · Markdown · CSL-JSON · GP/1**.
**GP/1 padrão (5 claims) = 1.322 tokens** (1.077 com o vocabulário estendido) × **9.176** do contexto jurídico ao vivo × **16.290** de 5 páginas `.md` ⇒ **−85,6% / −91,9%**.
Answer Unit v2 com linter próprio.

### Cobertura-com-cota (ausência)
Só se afirma "não há norma/decisão" **dentro de célula coberta** e **só com o `permitted_statement` da célula**. `world = closed` admite prova de exclusão; **`world = open` só admite cota (1−ρ)^m**, ρ = 0,905. No schema, célula aberta sem cota é **inexprimível**.

### Frescor e invalidação
Feeds de invalidação: **push + query assinada + WebSub**. `wj.must_watch` obriga quem cacheia a assinar o feed. **AI Source Card** publicado em `/.well-known/ai-source-card.json`.

### Fluxo diário (custo)
0,63 núcleo (**12,5% da folga de 5,05**) · **10.622 GPU-s** (**23,3% da folga de 45.600**) · 0,38 GB de RAM. A CPU livre sozinha processaria ~277 mil decisões/dia.

---

## §8 · CONFIANÇA OPERACIONAL — O CONTRATO C01–C26 (F06)

**Princípio (D1):** confiança não é persuasão do LLM; é **elegibilidade + consistência + verificabilidade**. O LLM escolhe por relevância e ignora sinais de estilo (arXiv:2402.11782); formato Q&A sozinho não aumenta absorção (arXiv:2604.25707, 21.143 citações medidas). Quatro camadas: **L1 descoberta · L2 seleção · L3 citação · L4 verificação**. Cada IA lê um subconjunto diferente.

**Alavanca de maior retorno sob controle total: CONSISTÊNCIA** — e ela falha hoje de forma sistêmica (§1). Correção: **tupla de identidade de fonte única por página** + portão **`wjconsist` fail-closed** (pré-publicação e pós-deploy). Demonstrado ao vivo: **5 FAIL → 5 PASS** após regenerar de fonte única.

**Identidade de citação em três níveis:** URN LexML (*o quê*) · URL genérica canônica (*onde*, indexável) · **URI de versão imutável `/{área}/{slug}/@v/{sha12}/`** (*quais bytes*).

| # | Contrato | Exigência canônica |
|---|---|---|
| C01 | URN estável | `legislationIdentifier` em JSON-LD, `data-urn`, MCP `grafo`; LexML Parte 2 + fragmento Parte 3 (alinhar ao padrão do F01: `!art59-1_par1`) |
| C02 | URL canônica imutável | `<link rel="canonical">` + `Link: rel="canonical"` no MD; **nunca muda nem redireciona** |
| C03 | URI de versão | `GET /{área}/{slug}/@v/{sha12}/`, corpo imutável, `Cache-Control: public, max-age=31536000, immutable`, `X-Robots-Tag: noindex` |
| C04 | cite-as | `Link: rel="cite-as"` em HTML **e** MD, **um só alvo** (RFC 8574) |
| C05 | Signposting nível 2 | linkset RFC 9264 com `cite-as`, `describedby`, `alternate`, `license`, `type`, `author` |
| C06 | Memento | `timegate`/`timemap`; na versão, `rel="original latest-version"` e `rel="predecessor-version prev memento"` |
| C07 | Norma em data D | `GET /norma/{urn}?em=D` → 302 → `?em={início do intervalo}&modo=vigencia&tx={tx}` + cabeçalho `Legal-Time`; conjunto **finito** de URIs; `Allow: /norma/` antes de `Disallow: /*?` para o grupo de treino |
| C08 | Validador forte | **`ETag`** (32 hex de sha256) em **toda** representação + `Repr-Digest` também no HTML |
| C09 | Frescor declarado | `Last-Modified` = `dateModified` = `date_modified` = sitemap `lastmod` = `/changes.json revised_on` = **data da última mudança de `content_sha256`**, nunca data de build |
| C10 | Frescor da fonte | por fonte: `checked_at`, `man_sha256` (normalizado), `raw_sha256`, `man_norm`, `warc_record` |
| C11 | Retenção de cache | `max-age=3600, s-maxage=604800, stale-while-revalidate=86400, stale-if-error=604800` |
| C12 | Licença legível | `Link: rel="license"` (cardinalidade 0–1) + `License:` no robots + `rsl.xml` separando texto autoral (CC-BY) de lei e decisão (art. 8º IV) |
| C13 | Preferência de uso | robots **e** cabeçalho: `Content-Usage: train-ai=y, ai-use=y, search=y` + `Content-Signal: ai-train=yes, search=yes, ai-input=yes` — **um só struct gera tudo** |
| C14 | Identidade da casa | `/.well-known/http-message-signatures-directory` **assinado**, molde byte a byte do diretório do ChatGPT |
| C15 | Identidade de entrada | RFC 9421 no edge + faixa IP publicada + rDNS: **três classes** (assinado, IP verificado, não verificado) |
| C16 | Cota por bot verificado | verificados: sempre 200/304 do edge, **nunca 429**; API/MCP: 100/dia grátis por DID, acima **402 só em rota `noindex`**; não verificados: token bucket por /24+ASN |
| C17 | SLA público | `/status.json` assinado e no log diário; SLO **99,9%** para `/mcp` e `/api/v1/citacoes` |
| C18 | Política de segurança | `security.txt` com `Policy`, `Encryption`, `Acknowledgments` e assinatura OpenPGP (RFC 9116 §2.3); escopo inclui prompt injection, forja de recibo e bifurcação do log |
| C19 | Log público | `/.well-known/lar/checkpoint` + tiles; **MMD 60 s**; nota C2SP assinada |
| C20 | Verificador | `lar.go` publicado com vetores (472 linhas não-branco, SHA-256 `5f57fe20…d92f`) + regra `man_norm` + checagem estrutural |
| C21 | Recibo com vínculo de página | `stmt.doc{url,title,html_sha256}` e `claims[].{man_uri,man_sha256,man_len,man_norm,locator}` — **trocar o título invalida a assinatura** |
| C22 | Transparência de qualidade | `/transparencia/qualidade.json`: `n_emitidas`, `n_INVALID`, `n_RX`, cobertura com **denominador**, HCR com UCB95 Clopper–Pearson (teto **2%**) |
| C23 | AI Source Card | `Link: </.well-known/ai-source-card.json>; rel="describedby"` na home e no api-catalog |
| C24 | Errata | `/feeds/errata.atom` (RFC 4287) + arquivos RFC 5005 + hub WebSub próprio + `POST /receipts/expired`; **≤ 60 s** |
| C25 | MCP | toda ferramenta com **`title`** + dicas; `fetch` com `cite_as`, `version_sha256`, `markdown_sha256`, `date_modified`, `status` e `resource_link` |
| C26 | Normalização de fonte | `/.well-known/lar/norms/f5-cspm-tail-v1` com regex e vetores |

### Errata e retratação (nunca apaga)
Claim novo + `status.successor` + **Retraction Statement no log** + propagação por **6 canais em ≤ 60 s**.
**SLA por severidade: S1 ≤ 4 h · S2 ≤ 24 h · S3 ≤ 72 h · S4 ≤ 14 dias.**
Taxa de **erro próprio** publicada **com denominador** e limite superior Clopper–Pearson. Evento do mundo (norma mudou) **não conta** como erro nosso — a distinção está no schema (`is_error` GENERATED).
Verificado: `errata.sql` **6/6 recusados + 2/2 aceitos**.

### Testemunhas e quórum
**N = 5 testemunhas, k = 4** para checkpoint publicável (notebook em AS distinto, parceiros, agente externo que rode `lar-go`, relay **Nostr**). **Bounty de equivocação (bifurcação do log): R$ 5.000.**
Verificado no schema: 3 de 5 ⇒ `publicavel = false`; 4 de 5 ⇒ `true`.
**Revogado**: "VPS em terceiro AS" como testemunha (CORREÇÕES §6 — nuvem).

### Medição sem API dos motores (D8)
Entram: fetchers de tempo real · `utm_source=chatgpt.com` · `Referer` · **Citation Share oficial do Bing** · condicionais/304 · latência de descoberta · 404 de URL alucinada · absorção medida no próprio `/verify` · **experimento em cunha escalonada** (4 ondas de 25% por `hash(path)`, estimador Callaway–Sant'Anna com CUPED) que prova causalidade **sem desligar nada que cita**. Potência: 839 páginas/braço a 0,10 citação/página/dia; com 4.000/braço o efeito mínimo detectável é 6,9%. O acervo de 18.774 sobra.
**Revogado**: a sonda ativa paga do III.12 §9(d) (CORREÇÕES §6 — sem serviço pago como dependência).

### O que NÃO fazer (escrito pelos próprios operadores)
4xx/402 em URL indexável = conteúdo inexistente para o Google · 429/5xx derruba o crawl do host inteiro · prompt injection rebaixa ou deslista no Bing · dado estruturado que não bate com o visível gera ação manual · FAQPage e ClaimReview são decorativos no Google · **atribuir revisão humana a texto gerado por máquina é sinal falso**.
**Corrigido**: "Claude-User ignora robots.txt" (C06) é **FALSO**.

---

## §9 · DOUTRINA VERIFICÁVEL (F02)

**DoctrineClaim = posição + trecho ≤ 300 chars + paráfrase.** **Nunca texto integral, salvo licença que permita.**

**O limite de 300 chars é empírico**, não arbitrário: **85,4% das citações doutrinárias reais têm ≤ 300 chars, p50 = 191**. Combina com **anti-mosaico** (≥ 2.000 chars entre trechos da mesma edição, ou nunca a mesma página nem a adjacente) e **cota por obra (≤ 1% da obra**, piso 2, teto 50 trechos).

**Cedar `WJ::Autoral` — 20 políticas D01–D20**, separadas das 17 de compliance. **39/39 vetores conformes, 0 erro em modo estrito.** Default deny; `forbid` vence `permit`; todo limiar **legal** é literal (provável por análise), todo limiar **estatístico** (τ) vem do contexto.

**14 invariantes de banco (I-DOC-1…14)**, entre eles: `rights_info` verbatim obrigatório (art. 107 III) · fonte lícita obrigatória (art. 107; CUB 10(1)) · **texto integral só existe para regime aberto** (FK composta com coluna GENERATED) · voz própria obrigatória · n-grama comum < 12 (art. 47) · polaridade verificada (art. 24 IV) · **atribuição por FK composta** — "o autor do claim é autor DESTA obra, o trecho é DESTA obra, a posição responde a ESTA questão" ⇒ atribuição a autor alheio é **inexprimível**.

**Licença vem da ORIGEM, nunca do agregador**: BDTD e OasisBR propagam **0% de licença CC (0/240)**. Classificador por precedência: Crossref > URI de CC > frase conhecida > `license.txt` > desconhecido.

**Corrente doutrinária** = posterior **Dirichlet/Beta por voto de autor**, meia-vida 10 anos. **"Majoritária" exige P(θ > ½) ≥ 0,90** — no schema, `rotulo = 'majoritaria'` com `p_maioria_milli < 900` é inexprimível.

**Grafo de doutrina**: estende o AGE com 7 classes (Autor, Obra, Posicao, Argumento, DoctrineClaim, Questao, Corrente). **Chave de questão TIPADA** (`BASE_CALC(icms,pis)`) resolve conflitos onde TF-IDF falha.

**Custo**: backlog ~545k GPU-s; regime diário ~580 GPU-s/dia (**1,3% da folga**); +15 GB no NVMe (0,4%).
Verificado: `doutrina.sql` + `ataques.sql` **32/32 (25 recusados + 7 aceitos)**; `go test` **9/9**.

---

## §10 · INTEGRIDADE DO CONHECIMENTO (F08)

### Cadeia evidencial
**WARC/1.1** + **in-toto Statement v1 (DSSE), predicado `acquisition/v2`** + **COSE Hash Envelope (RFC 9995)** na trilha **SCITT**. Escritor do log: **Tessera v1.0.4** (POSIX, Apache-2.0).
**SXG REJEITADO** — o Google encerra a emissão em 30/09/2026.

### Níveis de captura C0–C3 (nível **é** evidência, não rótulo)
| Nível | Significado | Imposto no schema |
|---|---|---|
| C0 | fetch simples | — |
| C1 | fetch com normalização declarada e WARC | `norm_ok` OU `served = origin` |
| C2 | **duas vantagens de egresso concordam** | `n_vantages >= 2` obrigatório |
| C3 | **a própria fonte assina** (o DOU assina em ICP-Brasil) | `src_sig_ok` obrigatório |

**`man_sha256` REDEFINIDO** = hash da **representação de ORIGEM** (pós-normalização declarada), não dos bytes como servidos.
**PDF do DOU**: assinado em ICP-Brasil (`adbe.pkcs7.detached`), cadeia validada até **AC Raiz v5**, **sem timestamp TSA** ⇒ a **âncora temporal é o log de transparência**.

### Retenção e capacidade
**K1** (perpétuo, tudo que é citado — nunca despeja; a FK do recibo **congela** o K1) e **K2** (despejável).
Recompressão sem perda dos PDFs de K1: **1,268× medido**. Cenário canônico (P1, 1×/1×): **K1 0,256 TB/ano, log 15 GB/ano, ano 5 = 2,90 TB (72% de 4 TB), 6 anos até 80%**. A 10× de ingestão: ano 5 = 3,18 TB (80%). A 10×/3×: 4,58 TB ⇒ aciona **L5** (dedup por fragmento) e **L6** (custódia federada em espelhos de parceiros).

### Determinismo R0/R1/R2
| Nível | O quê | Onde vale |
|---|---|---|
| **R0** | bit-exato por construção | HTML/PDF, **SLSA Build L3** |
| **R1** | bit-exato no serving | **NÃO disponível**: `VLLM_BATCH_INVARIANT=1` é BETA e NVFP4 está fora da lista testada |
| **R2** | **votação 3-run + NLI determinística** | **é o que vale em produção** — campo `determinism` no recibo |

**D-2' — R2 sob prefix caching (H01 G10).** Prefix caching é condição de viabilidade do serving
(sem ele o teto cai de 11.615 para 3.768 chamadas/dia), mas ele **quebra a reprodutibilidade**
(arXiv:2609.04748): a mesma pergunta com cache diferente pode dar saída diferente. Três regras:
1. **O caminho de VERIFICAÇÃO** (V⁴, extração para claims, votação 3-run) roda com prefix caching
   **DESLIGADO POR REQUISIÇÃO**. O mecanismo real do vLLM não é uma flag: é **`cache_salt` aleatório
   por requisição** em `SamplingParams` (≥ 0.9). Custa **< 3%** do orçamento (a verificação é CPU/54M;
   só a extração no 8B é afetada).
2. **Todo `citation_receipt` e todo `prediction_receipt` carrega `cache_state_digest`** (SCHEMA-v4.1):
   `'none'` quando o caminho rodou sem cache, ou o **sha256 hex de `cache_salt ‖ engine_config`**.
   Valor fora dessas duas formas é **inexprimível** (CHECK). `lar.go` v1.1 valida a presença do campo.
3. **Serving comum mantém prefix caching.** Sem essa separação, R2 é uma afirmação falsa no recibo.

### Reprodutibilidade de build (S4)
**R-bit** para binários Go (`-trimpath`, `-mod=vendor`), GGUF com imatrix fixa, ONNX int8, tokenizer e trie — bit a bit. **R-eq** para quantização em GPU e treino: mesmo recipe + insumos ⇒ **KLD ≤ 10⁻³** e bench dentro do IC BCa. Job semanal de rebuild compara sha (R-bit) ou KLD (R-eq).

### Sete desfechos de verificação — nunca booleano
O verificador jamais devolve "verdadeiro/falso". Os erros são tipados **E1–E7** (URN não resolve · âncora inexistente · NLI abaixo do τ · fora de vigência · divergência de motor · contradição · irrelevante) e entram no `gap_queue` como insumo do submodular.

### Privacidade
Chave por documento selada ao TPM + **Erasure Statement**: apagar = **destruir a chave** (crypto-shredding). No schema, captura com Erasure e chave viva é inexprimível; **purga de backup ≤ 15 dias** (LGPD art. 19 II). Vende-se **MÁSCARA com taxa residual medida em ppm**, nunca "anonimizado" (LGPD art. 12 §1º).

### Contribuição da comunidade
Entra em **retrieval**, **nunca em treino** (`elegivel_treino = false` por CHECK; `taint` nunca 0). **Quarentena de 30 dias.** A **ordem no log** prova que a verificação veio depois da contribuição (`contribution_leaf < verification_leaf < leaf_index`).

Verificado: `go run . -n=10` reproduz **94 linhas idênticas** ao `run.log`; **9 cenários de ataque detectados**; `ataques_f08.sql` **20/20 recusados + 10/10 aceitos**; `tbv` detectou **7 ataques criptográficos reais**.

---

## §11 · ECONOMIA

| Item | Valor canônico |
|---|---|
| Tarifa (ANEEL REH 3.571/2026) | R$ 0,88056/kWh sem tributos; **R$ 1,27125** com bandeira + gross-up |
| Energia em regime | **R$ 252,46/mês** (272 W) |
| Custo fixo | R$ 1.199,26/mês |
| Break-even | **5.034 `/verify`/dia** OU 1 knowledge pack OU 2 feeds |
| Piso `/verify` | R$ 0,00135/chamada |
| Produtos | 9; **só 3 tocam GPU** (e no catálogo de ferramentas, **35 das 37 nunca tocam**) |
| Tesouraria (ADP) | colchão de 6 meses (R$ 7.195,58), hurdle 0,9150%/mês, payback ≤ 18 meses, **quarter-Kelly** |
| Fiscal | LC 123 art. 18 §14 (exportação zera Cofins + PIS + ISS); USDC converte em D+0; **a PJ emite a chave**, nunca a PF |
| Negociação | SAOP `t_max = 6`; **o número nunca sai do LLM** (antitruste, ρ = +0,053); posted price + bandit para avulso |
| Transação | **É OPÇÃO, não obrigação.** O conhecimento verificável básico é o que faz a IA voltar. **Confiança primeiro, transação como camada opcional.** 100 chamadas grátis por DID |

**O menu de capex SAI da ADP.** O λ_gpu não compara mais com preço de mercado — não há mercado. Ele arbitra **dentro da máquina** e decide três coisas: **ordem da fila**, **tiering** (o que vai para NVMe, o que fica em RAM, o que vai para GPU) e **compactação** (qual projeto interno de poda/destilação/quantização se paga em GPU-s). Exemplo canônico: o aluno 4B se paga em 48 dias-de-compute.

**Trilhos de pagamento:** `x402` (self-hosted, processo isolado `wj-x402d`) · `l402` · `pix` · `gratis`.
**Pay-per-Crawl da Cloudflare SAI como trilho primário** (closed beta + dependência de terceiro, CORREÇÕES §6). Permanece, no máximo, como canal oportunista se e quando abrir.

---

## §12 · EnaEval — PREMEDITAÇÃO, ARENA E REDE SOCIAL VIVA

### Premeditação (previsão **baseada em dados**, nunca "prever o futuro")
**Quando uma IA pesquisa, a resposta JÁ VEM com a chance de êxito/perda em porcentagem, com banda de confiança.** Isso é produto central.

- **Alvo**: hazard discreto multinomial *person-period* em **LightGBM**, 4 classes/mês {nada, sentença, acordo, extinção}. Rejeitados: Cox/DeepSurv (PH falso — metas do CNJ geram pico sazonal), RSF/DeepHit (sem serving Go), Fine–Gray (só checagem offline).
- **Base**: DataJud (**14 campos**, sem valor da causa, partes, advogado, juiz ou texto do fato) — é sobrevivência sobre o fluxo TPU. 59 M processos × ~24 meses → case-cohort 1:4 (Horvitz–Thompson) → **~180 M linhas**, 28 bins trimestrais, CPU.
- **Anti-vazamento é invariante de schema**: `FeatureSpec{Name, Source, AvailableAt, LeakClass}`; o CI falha se `LeakClass == 2` ou `eval(AvailableAt) > t_corte`. Quatro modelos, Δ ∈ {0, 30, 90, 180} dias.
- **Calibração**: split conformal (garantia distribution-free) + **conformal Mondrian** por célula κ = (tribunal, classe_L2, assunto_L2, ano), `n_cal ≥ 200`, backoff `ltree`. **Cobertura marginal nacional é inútil** (90% médio pode ser 99% no cível e 55% no trabalhista). Sob deriva, **ACI**. Gatilho de retreino = **martingale de Ville**, nunca cron.
- **`skill_vs_baserate` é OBRIGATÓRIO** no contrato: acertar 72% com base-rate de 70% vale zero.
- **Regulação executável**: Res. CNJ 615/2025 art. 10 II/III; anexo classifica jurimetria como **BR3, baixo risco**. Engenharia: **zero `judge_id`**, **k-anon n ≥ 50** com veto Cedar P18, detector de ataque de diferenciação por DID; `/predict` nunca devolve ranking de vara, só distribuição do foro.
- **Completeness counter**: contador estritamente crescente por endpoint, registrado em cada previsão e num Counter Statement diário — impede reservar previsão e publicá-la depois de saber o desfecho. **No schema: `UNIQUE (celula, counter)`.**
- **Simulação**: MOMDP semi-markoviano, sufixo de ordem 3, **MCTS 20.000 sims ≈ 12 ms em 1 núcleo, 0 GPU** ⇒ `/simulate` é **Tier Edge**. Três classes contrafactuais com **rótulo obrigatório**: C1 preditiva (identificável); C2 intervencional (identificável **só** onde o IV passa); **C3 trajetória NÃO identificável** (arXiv:2301.09031) — só visualização, com `worst_case_cf_error`. Ressalva contratual de **Priest–Klein** obrigatória.
- **Lacuna fechada pelo v4**: a % passa a ter lugar na resposta. Entra um **bloco `[P#]` na gramática do GP/1** e uma **frase-padrão para humano** que traduz `{p_milli, base_p_milli, skill_milli, alpha, n_cal}` respeitando a Res. 615/2025 — **nunca "você vai ganhar"**, sempre com banda e taxa-base. **G01 escreve a gramática e a frase.**

### Arena de debate
**Primitivo único: Alegação Comprometida** (`commit-reveal`, evidência com URN + `quote_sha256` + `receipt_id`, folha no log). **Zero primitivo social** — não há curtida, seguidor ou comentário solto.
- **LMSR (Hanson)**: `C(q) = b·lnΣexp(qᵢ/b)`, `pᵢ = exp(qᵢ/b)/Σexp(qⱼ/b)`, grampeado [0,02; 0,98]. Estritamente própria.
- **Reputação = riqueza**: `R_{j,t+1} = R_{j,t}·p_{j,t}(y_t)/p̄_t(y_t)`. Garantia de arrependimento: `−Σln p̄_t(y_t) ≤ min_j −Σln p_{j,t}(y_t) + lnN` (N=200 ⇒ 0,005 nat/questão).
- **Dinheiro**: `pago_j = b_q(1 − BS_j)`, payoff **∈ [0, b_q]**, **nunca negativo** (Lei 14.790/2023 art. 3º + DL 3.688/41 art. 50 §3º). Elegível = LB95% do log-score > 0 em ≥ 50 resoluções.
- **Três fluxos de caso** (vazamento impossível por construção): **S1** prospectivo 1º grau (gatilho: saneamento CPC 357) · **S2** prospectivo STJ (gatilho: distribuição do REsp) · **S3** retrospectivo LIVE (**nunca pontua leaderboard**).
- **Pseudonimização** (CNJ 615/2025 + LGPD): sem nº CNJ, nomes, OAB, juiz ou comarca; datas ±15 d; recuperação só por `corpus.search(as_of = D_gatilho)`.
- **5 camadas anti-trapaça**: L1 prospectivo + Merkle · L2 pseudonimização · L3 `as_of` · L4 gap Δ > 0,05 (p < 0,01, n = 477) · L5 5% de pares contrafactuais. Falha ⇒ congela + quarentena.
- **Papéis**: os **quatro do dono** — advogado, juiz, promotor, jurista. **`promotor` e `jurista` não existiam** em A01 nem B07: **G02 escreve o protocolo de turnos, a agregação e a pontuação para N > 2 participantes** (o B07 só tem bilateral autor × réu, 3 turnos simultâneos, ≤ 1.200 tokens/turno).
- **`S_lit` = 0,4(CRR × SP) + 0,4·BT_side + 0,2·HP**; juiz por **Brier + Murphy**; **Índice de Sofisma** = P(juiz escolhe o lado perdedor | litigante daquele lado no quartil superior de BT).
- **Ponte nova (v4)**: o mercado **abre ancorado no `desfecho` calibrado do `/predict`** (campo `abertura_p_milli`), não em p uniforme. G01 e G02 detalham.
- **Custo (D-10' — a linha "1.000 rodadas/dia = 9.250" está REVOGADA por dupla contagem, H01 G1)**:
  **rodada de arena ≡ thread de caso** (G02 S1/S2/S3). Volume-alvo **599 debates/dia**, dos quais **120
  em perfil `arena`**: 479 × 18,29 + 120 × 41,0 = **13.681 GPU-s/dia = 30,0% da folga**. O custo por
  rodada em perfil arena é **41,0 GPU-s MEDIDO** (G01), não os 9,25 derivados; o 18,29 do G02 vale para
  o perfil leve com lote ×4. **A mochila B do seletor do G02 é PARÂMETRO LIDO de `shadow_price`
  (λ_gpu[classe][hora]), nunca constante**: quando o custo medido passa de 25 GPU-s, o seletor reduz o
  volume (faixa 230–510/dia) sozinho. Lote preemptível 24/7, **sem "noite"**.
- **Dinheiro exige cadeia evidencial (D-13.3 item 3 / H01 G11)**: `resolution.oracle_receipt` é
  **NOT NULL** e aponta, por **FK composta**, uma `capture` cuja chave GENERATED só existe quando
  `fonte='datajud'` **e** `level ≥ C1` **e** K1 não despejada **e** `norm_ok`. O **desfecho é DERIVADO**
  da tabela `tpu_outcome` — `winner` deixa de ser parâmetro de função. O **`payout` só entra em lote do
  Plano-T assinado por FROST 2-de-3** (`payout_batch.frost_sig`), com **`brl ≤ b` do MERCADO da aposta**
  (FK composta, não número reescrito na linha). **Texto da internet nunca chega a dinheiro.**
- **Balcão de Verificação**: `bounty.post(argumento, stake)`; achar a falha ganha o stake, **sem humano no meio**.
- **Terminalidade**: `origin ∈ {planalto, lexml, stj, stf, cnj/djen, camara, senado}`. **`AI_DERIVED` nunca é fonte.**

### Rede social viva (obrigatória e vale ouro)
- **Identidade**: `did:web` + JWKS + Web Bot Auth (RFC 9421) + **um único log Merkle** (SCITT) para chaves, proveniência e recibos — retrodatar chave é impossível por construção.
- **MeritRank**: EigenTrust com teleporte só a pré-confiáveis (a = 0,15); `w_ij = min(√v_ij, κ·R(i))` — **reputação ANTES da raiz quadrada** (a √ ingênua amplifica Sybil 31,6× em k = 1.000). **α = 0,40, β = 0,60**, derivados de `amp = (1−α)/α·(1−β) < 1` (os valores "de manual" 0,30/0,50 davam amp = 1,167: ataque lucrativo). Meia-vida 49 dias; `bond_rep = max(R$ 250, 49·R(i)·V_dia)`; slashing confisca 100%.
- **Feeds**: MCP `wj://feed/cases`, `/resolutions`, `/prices/{tema}`; HTTP `GET /feed/events?since=<cursor>` em JSONL com ETag/304 no edge; espelho **Nostr** (30411 caso, 30412 preço, 30413 resolução).
- **As 4 personas do EnaEval são linhas da tabela `agent`**, cada uma com `pubkey` e `rep_wjr` próprios e
  visíveis: **4 personas, 4 pubkeys** (D-15). O advogado tem sub-papel `autor`/`réu` com a MESMA chave —
  o lado é coluna do lance. O 5º DID `agent:adversario` está REVOGADO. A casa deixa de ser bloco único e
  passa a ser **quatro interlocutores identificáveis**.
- **Três lacunas que G02 fecha, e que o v3 não tinha**: (1) **motor de semeadura** — o serviço que decide, todo dia, quais casos reais viram debate público (o B07 só tinha um *patch* de market maker; o auto-jogo do D06 gera episódios para RL, não para publicação); (2) **volume-alvo diário**; (3) **formato diário** — `caso_do_dia` / `resumo_do_dia`, a unidade de feed que hoje não existe (GP/1 resolve pergunta-a-pergunta; JSONL de rodada, boletim e pack Parquet não são unidade de feed).
- **A API de ~10k req/mês precisa de contrato de payload** — hoje não existe em relatório nenhum. **É entrega obrigatória de G02.**
- **Invariantes no schema (SCHEMA-v4.1, D-13.3 item 4 / H01 G12)**: post da casa que afirma direito
  **carrega claim verificado** (`I-SOC-1` + trigger `I-SOC-3`, ≥ 1 linha em `social_post_claim`); opinião
  sem claim só existe como `comentario` e **não pode declarar que afirma direito** (`I-SOC-2`).
  **Segmento `text` cai de 1.200 para 280 caracteres** — é tecido conectivo, não parágrafo: parágrafo
  assertivo sobre direito ou vira `claim` com recibo, ou vira `opinion` com `basis`. O selo declara
  **escopo** (`verification_scope`), e sob `claims_and_gloss` um segmento não verificado é recusado
  (`I-SOC-4`). Sem isso, "a orientação atual do tribunal é que o consumidor perde a indenização" saía
  assinada com `v4: pass` — lavagem de citação interna dentro de casa.

### Stickiness (requisito, não desejo)
Ferramentas de **alta relevância, seguras e confiáveis, que as IAs sempre voltam a usar**. Três travas: cache da IA chaveado por `receipt_id` · **WJR intransferível** · `skill_vs_baserate` público. Primeira semana de um agente externo (D0–D7) está fechada e não é lacuna.

---

## §13 · GRAFO E VIGÊNCIA

- **Tri-temporal**: vigência × eficácia × transação. `EXCLUDE USING gist` garante ≤ 1; **totalidade por CONSTRAINT TRIGGER** com `unnest` (não `cardinality(datemultirange)`, que não existe em PG 16/17/18).
- **Revogação é versão de texto vazio, nunca ausência de linha.** A linha do tempo termina em +∞ ou o COMMIT falha.
- Escala: **40,6 M nós / 301,4 M arestas**. **Citação bruta FICA FORA do AGE** (tabela relacional particionada por `data_julg`, BRIN).
- **PPR por forward push (6,7 ms)**, nunca power iteration. **AGE VLE PROIBIDO** → CSR compacto em Go.
- **Grafo AGE = `wjg`**. `'wj'` falha.
- **Apelido normativo = f(string, DATA do documento citante)**, não constante. `INTERPRETA(acórdão → redação@sha)`.
- **Consolidação adversarial** com forma canônica **D0–D3** entre BNP × CKAN × portal.
- **Fontes oficiais são adversariais** (F03, medido): `historico` do BNP replicado em **1.479/1.479** temas de RG; **2,00%** de teses degeneradas; **25,7%** sem tese; STJ CKAN com **29 duplicatas byte-a-byte**. Replay de 1.473 registros STJ: **1.470 aceitos (99,80%), 3 anomalias em quarentena** (datas erradas nos Temas 1.282/1.337/1.459 **oficiais**).
- **Superação tácita NUNCA é certeza sem ato oficial** — `claim.warn`, não `claim.dead`; no schema, `grau_certeza < 1` ou `confirmado_por IS NOT NULL`.
- **Tese tem versões E variantes**: o Tema 69 tem **4 variantes oficiais** (registro do tema, certidão de julgamento, item 3 da ementa, ementa dos ED). Uma canônica por versão.
- **Modulação** com **intervalo nominal/estrito** ("desde D" × "após D") + ressalva de protocolo.
- **Ementas têm padrão detectável**: Rec. CNJ 154/2024 já está em **37,9%** das ementas STJ de 2026 (36,0% em 2025; 17,6% em 2024) ⇒ parser **ZERO-LLM**: **19.537 questões, 247 clusters ≥ 3 acórdãos, 53 cruzando ≥ 2 tribunais**.
- **Direito-como-código**: 4.626 linhas (C03) + 14.944 (F05) em Go, 0 dependências externas, 50 ms, 0 GPU; intervalo nominal/estrito; `big.Rat` **nunca float**.

---

## §14 · QUALIDADE E SEGURANÇA

- **WikiJurídica-Bench**: 2.700 itens, 8 trilhas (+ trilha 9 de negociação), 7 programáticas. Portões **G1–G5**; **G1 roda no artefato QUANTIZADO** (a coluna que ligaria bench a checkpoint BF16 **não existe** — o furo é irrepresentável). **HCR ≤ 2%, ASR = 0**; `N_real = 1,07 × N_Connor`; BCa clusterizado.
- **G2 (jurimetria)**: `R ≥ 0,15` sobre o KM da célula e cobertura ∈ [0,88; 0,93], BCa por vara.
- Função objetivo **J em R$/dia**; **κ = 49**; **risco é restrição, não termo**. Autonomia L0–L5; tesouraria com teto **L3**.
- **3 planos físicos (D/C/T)**; **FROST 2-de-3** acima de R$ 2,50; **dead-man invertido 180 s**; float = orçamento diário.
- **Invariantes**: 24 catalogados no v3; **no SCHEMA-v4 são 32 famílias = 59 invariantes individuais, todos no banco** (tipo/constraint/prova — nenhum em convenção). **FK composta como prova de pertinência** é o padrão da casa.
- **Θ_frozen**: o que nunca muda sozinho é **inexprimível como config auto-ajustável** (`hcr_max`, `asr_max`, `tau_nli`, `lambda_abst`, `cap_spend`, `frost_k`, `deadman_s`, `panel_private`, `terminal_nodes`, `epsilon_floor`).
- **Promoção**: exige os **5 portões DAQUELE artefato sob o MESMO bundle Cedar** (TOCTOU fechado por FK composta com `policy_set_version`).
- **Normas**: Res. CNJ 615/2025 (alt. 674/2026) **vigente**; 332/2020 **revogada**; **PL 2338/2023 NÃO é lei**; jurimetria = baixo risco (anexo BR3); **Lei 9.610 art. 8º IV: lei e decisão não têm direito autoral**.

---

## §15 · WORLD MODEL

15 macro-eventos (coarsening determinístico do TPU, κ: TPU → E, sha256; o CI quebra se um estado absorvente sumir). **H(k=3) = 1,326 bit/evento** (k=4 só +1,0%). Kernel **58 × 15** (58 de 4.096 contextos, n ≥ 30, **94,6% da massa**) = 3,5 kB/célula, **17,4 MB nacionais**; satura em 800–1.200 casos/célula. **MCTS 12 ms em CPU.** **Transformer PROIBIDO até bater 1,326 bit no holdout BCa** — até lá, VOMM ordem 3 com backoff Jelinek–Mercer (α = 0,4).
Medido: 49,1% dos intervalos < 0,5 dia; eventos decisórios (219/220/221) são **0,33%** dos eventos; o coarsening descarta 48,1% sem perder decisório.
**Auto-jogo**: autor × réu escolhem ações e **o modelo do mundo é o árbitro** (sorteia e′, Δt); **o LLM só redige** (`sim/core ↛ sim/llm`). Sinal `0,6·r_cit + 0,4·r_traj`, `r_traj = −KL(simulado ‖ real)`.

---

## §16 · REVOGADO — o que do v3 MORREU (lista fechada)

Nenhum item abaixo pode reaparecer em documento derivado. Cada linha traz quem o matou.

### Hardware e capacidade
| Morto | Quem matou |
|---|---|
| **RAM de 96 GB no dia 0** (e os 60,60 GB residentes do E02) | CORREÇÕES §6 · F04 |
| **Transbordo para Vast.ai / RunPod / Lambda** e qualquer GPU alugada | CORREÇÕES §6 |
| **Compra da 3090 24 GB** ("1 serve, 1 treina", gatilho treino > 48%) | CORREÇÕES §6 |
| **Segunda RTX 5060 Ti** | CORREÇÕES §6 |
| **ρ_job (bytes/GPU-s)** como regra de transbordo, e o preço spot R$ 0,301/GPU-h | CORREÇÕES §6 (sem mercado, sem regra de mercado) |
| **Espelho ZFS em 2º NVMe** | F04 §6 |
| **`restic` off-site em terceiro** | CORREÇÕES §6 · F04 §6 |
| **Backlog de 11,9 dias com R$ 241,29 de transbordo** | F04 (27,6 dias-de-compute, 100% local) |
| **Folga de GPU de 47.861 GPU-s/dia** | F04 (45.600) |
| **Folga de CPU de 5,41 núcleos** | F04 (5,05) |
| **Piso de power limit de 160 W** | F04 (150 W) |
| **Autonomia linear de nobreak (15,2 / 39,1 min)** | F04 (Peukert: 6,3 / 19,7 min) |
| **"Janela noturna" de 6–8 h / 28.800 GPU-s** | CORREÇÕES §2 (24/7 = 86.400 GPU-s) |

### Modelos
| Morto | Quem matou |
|---|---|
| **Bespoke-MiniCheck-7B** (sem licença) e **MiniCheck** (só inglês) | E04/D01 — verificador único é o wj-nli-54M |
| **Qwen3.5-4B como base** (híbrido) | E04 |
| **X-LoRA** | CANON v3 → S-LoRA + roteador discreto |
| **Wan 2.2** (exige 24 GB) | E04 → LTX-Video 2B |
| **XTTS** | E04 → Kokoro-82M + Chatterbox |
| **"14B FP8"** como perfil de serving | E04/F04 — não cabe no envelope |
| **Qwen3-8B-NVFP4 = 4,60 GB** | F11 (6,41 GB = 5,97 GiB real → 4,90 GB compactado) |
| **Fast path 1,7B = 0,95 GiB** | F11 (1,42 GB → 1,12 GB) |
| **BF16 ≈ 200 TFLOPS** e o cronograma I.8.6 com overflow para nuvem | F11 (47,4 TFLOPS; FP8 é o padrão) |
| **BOSCH servível pelo vLLM de estoque** | F11 (exige plugin) |

### Documento, OCR e layout
| Morto | Quem matou |
|---|---|
| **DocLayout-YOLO** · **LayoutLMv3** · **Granite-Docling** | E04 → PP-DocLayout-L |
| **MinerU-2509** (AGPL) e o **pacote de CÓDIGO do MinerU** (licença própria com limiar de receita) | E04 · F11 — só os PESOS (Apache-2.0) |
| **MuPDF / go-fitz** (AGPL-3.0) | F11 → PDFium em WebAssembly/wazero |
| **Chandra-OCR-2** (OpenRAIL com teto de US$ 2 M) | F11 → DeepSeek-OCR-2 + PP-OCRv5 |

### Dados e infraestrutura
| Morto | Quem matou |
|---|---|
| **VectorChord / `vchordrq` / `vchord_bm25`** (AGPLv3-OU-ELv2) | F11 → pgvectorscale + pg_textsearch |
| **AGE VLE** (caminho de comprimento variável) | F04 → CSR compacto em Go |
| **`create_graph('wj')`** | F03 → `'wjg'` |
| **SDK Go do x402 dentro do binário principal** (puxa go-ethereum LGPL) | F11 → processo isolado `wj-x402d` |
| **SXG como atestação** | F08 (Google encerra em 30/09/2026) → RFC 9995 + Tessera |
| **R1 (bit-exato) no serving NVFP4** | F08 → R2 |

### Protocolo, negócio e método
| Morto | Quem matou |
|---|---|
| **Pay-per-Crawl da Cloudflare como trilho PRIMÁRIO** | CORREÇÕES §6 (closed beta, dependência de terceiro) → x402 self-hosted |
| **Sonda ativa paga (III.12 §9(d))** | F06 D8 · CORREÇÕES §6 |
| **"VPS em terceiro AS" como testemunha/egresso** | CORREÇÕES §6 → notebook + parceiros + testemunhas externas |
| **`latest-version`/`predecessor-version` como Memento/RFC 7089** | F06 (é RFC 5829) |
| **`$ref` de rede em `outputSchema` de ferramenta MCP** | F07 (MCP 2026-07-28) |
| **`citation_receipt` em 4 versões** · **`tese_versao` em 2** · **`policy_decision_log` em 3** | G06 (§2 do LEDGER) |
| **`research/D09-drafts/`** | G06 → `E01-drafts` é canônico |
| **`research/E02-code/escalonador.go`** como implementação | G06 → superado por `F04-code/go` (o `.tla` do E02 permanece) |
| **Piso fixo `nli >= 0.850`** (`D10-code/invariantes.sql`) | G06 → `tau_milli` dinâmico + I-VERIFY-1 |
| **Planejar em dias, semanas, meses ou "180 dias"** | CORREÇÕES §7 — fases e objetivos com critério de pronto |
| **Chamar o bot de "a plataforma", "a casa" ou "o bot"** | CORREÇÕES §7 — o nome é **EnaEval** |
| **Contar ferramentas por narrativa ("19 → 24", "19 → 30", "+8")** | G06 → `tools/catalog.json` é a única base |
| **"Teto de crescimento", "platô", "saturação", "limite do mercado"** | CORREÇÕES §5 |

### Revogado pela v4.1 (arbitragem do H01 — 19 achados)
| Morto | Quem matou | Substituto |
|---|---|---|
| **`wj_arena_settle`** e **`wj_social_reputation`** — nomes INVENTADOS pelo G04, sem spec em lugar nenhum | D-5' · H01 G5 | o gerador `cmd/enaeval-catalog` lendo `G01-code/schemas/mcp-g01.json` e `G02-code/mcp-social-tools.json` |
| **`research-v4/tools/catalog.json` MANUAL do G06** (37 + 20 reservados) | D-5' · H01 G5 | saída do gerador: **53 ferramentas com schema + 8 reservadas**; os 12 reservados colidentes viram `aliases` |
| **τ = 906 HARDCODED** em `arena.go:267`, `g01_schema.sql:177`, `G02/verify.go:21`, `social-schemas.json:58` | D-13.3 · H01 G7 | tabela `verify_config` + `verify_cfg_vigente()`; CI com grep = 0 |
| **`resolution.oracle_receipt` NULLABLE** (JSON do DataJud virando `payout.brl` sem captura) | D-13.3 · H01 G11 | NOT NULL + FK composta para `capture` datajud C1+ |
| **`winner` e `tpuCode` como PARÂMETROS de `Resolve()`** (`G02-code/score.go:79`) | D-13.3 · H01 G11 | tabela `tpu_outcome`; desfecho derivado por trigger |
| **`payout` sem lote e sem teto** | D-13.3 · H01 G11 | `payout_batch` com FROST 2-de-3 + `brl ≤ market.b` por FK composta |
| **CANON §12 "1.000 rodadas/dia = 9.250 GPU-s"** | D-10' · H01 G1 | 599 debates/dia = 13.681 GPU-s (479 leves + 120 arena) |
| **D-10 "599 threads/dia **e** 120 rodadas de arena/dia"** (dupla contagem) | D-10' · H01 G1 | é UM produto com dois perfis de custo |
| **"6,41 GiB" como tamanho bruto do 8B** | D-15 · H01 G15a | **6,41 GB (5,97 GiB)** |
| **"Folga de GPU de 47.861"** ainda viva em F01:31, F02:29, F03:338 | H01 G15c | **45.600** |
| **5 personas / 5 DIDs** (`G02-code/personas.go` com `agent:adversario`) | D-15 · H01 G15d | **4 personas, 4 pubkeys**; lado é coluna do lance |
| **`wj-norm/f5-cspm@1`** (`G03-code/canon/canon.go:36`) e a regex que aceitava `@N` | D-12' · H01 G8 | só `wj-norm/f5-cspm-tail-v1`, registrado na tabela `norm_rule` (FK) |
| **"Go 1.27"** como toolchain do monorepo | D-16 · H01 §5(a) | **`go 1.25` + `toolchain go1.25.x` pinado**, CI com `GOTOOLCHAIN=local` |
| **"G03 fase B ≈ 1,2 M núcleo-s/DIA"** (1,74× a CPU inteira) | D-10' · H01 G2 | 1,2 M núcleo-s **TOTAL DE FASE**; regime = 46.440/dia já no F01 |
| **RAM nova (3.030 MiB) como RESIDENTE** | D-10' · H01 G3 | envelope rotativo de 6.656 MiB, um locatário por vez |
| **"OCR em regime = 4.000 GPU-s/dia"** somando aos 600 | H01 G19 | 600 canônico; os 4.000 são **pico de backfill classe 4 e SUBSTITUEM** os 600 |
| **Roteiro de soberania por trimestre (Q4/26 → Q4/27)** | D-11' · H01 §4 | fases **SOB-0…SOB-4** com critério de pronto |
| **F04 §4.2 "Cronograma local — Etapa \| Dia"** | D-11' · H01 §4 | "Ordem de dependência e custo acumulado — GPU-dias de máquina" |
| **G02 "22.252/dia em 180 dias"** e **G04 "resolvidas em 180 d" / "7 dias de log"** | D-11' · H01 §4 | "ao atingir 126.594 páginas"; "dentro do horizonte H"; "7 ciclos diários" |
| **`chave HMAC do requestState` aleatória por processo** e **cota por DID em memória** | D-6' · H01 G13 | `HKDF(K_root, "wj/requestState/v1")` + tabela `quota_did` |
| **`serverInfo.version` "0.1.0"** com `server.json` 1.3.0 | H01 G15e | `serverInfo.version` = `catalog_version` |
| **BOSCH como pré-requisito do canário** | H01 G16 | fase própria com portão; o canário sobe sem BOSCH |
| **"compressão de KV proibida em ⟨PROVA⟩"** (regra cega demais) | D-3 | **eviction** proibida; **quantização certificada** (WitCert) permitida com fingerprint no recibo |
| **λ_gpu escalar único** | D-9 | `λ_gpu[classe][hora]` |
| **`assinatura placeholder` sem prefixo** (`wjsig ed25519:…`, `Sig …PROTOTIPO`, `kid wj-2026-09`) | D-15 · H01 G17 | prefixo `EXEMPLO-`, `kid` `example`, e `payout_batch` recusa `frost_kid='example'` |

---

## §17 · EVIDÊNCIA DE EXECUÇÃO DESTE CANON

| Artefato | Comando | Resultado |
|---|---|---|
| `SCHEMA-v4.1.sql` | `bash fixes/run_schema_v41.sh` (banco NOVO `wj_v41`) | **exit 0** · 123 tabelas · 11 views · 127 FKs · 23 triggers · 375 CHECKs · grafo AGE `wjg` |
| `fixes/g01_schema_v41.sql` + `fixes/g02_schema_v41.sql` POR CIMA | idem | **exit 0, 0 colisão** · total 131 tabelas · 139 FKs · 25 triggers · 402 CHECKs |
| `ATAQUES-v4.1.sql` | idem | **94 ataques recusados · 13 caminhos felizes aceitos · 0 falhas** (32 novos: 26 recusas + 6 aceites) |
| `fixes/g01_ataques_v41.sql` | idem | **33 ataques recusados · 0 violações de integridade** nas 17 consultas finais (total com ATAQUES-v4.1: **127 recusas / 27 aceites / 0 falhas**) |
| `orcamento/orcamento_v4.py` | `python3 orcamento/orcamento_v4.py` | **regime 36.185 = 79,4% · sobra 9.415 · construcao 38,1 GPU-dias de máquina** |
| `fixes/grep_cronograma.sh` | `bash fixes/grep_cronograma.sh` | **24 → 0 violações de cronograma** (D-11') |
| `enums/gen.py --check` (fonte única de enums, FIX-A) | `python3 enums/gen.py --check` | **35 alvos conferem, 0 divergências** contra `SCHEMA-v4.1.sql` |
| `tools/catalog.json` | gerador `cmd/enaeval-catalog` (D-5') | **53 ferramentas com schema + 8 reservadas** · 0 `$ref` de rede · 0 nome inventado |
| Ambiente de validação | `psql --version`; `pg_available_extensions` | PG **16.13** · AGE **1.5.0** · pgvector e pgvectorscale **ausentes** (o prelúdio degrada para `real[]` e suprime só os índices vetoriais; o DDL de produção é o mesmo arquivo) |

Prova direta do CPC art. 927 III-A, rodada no banco:
```
efeitos de V_RESP_RELEVANCIA em 2026-09-02 =                          (vazio: III-A ainda não vigia)
efeitos de V_RESP_RELEVANCIA em 2026-09-03 = SOBRESTAMENTO_NACIONAL   (sem 311/332/496/521/1022)
```
