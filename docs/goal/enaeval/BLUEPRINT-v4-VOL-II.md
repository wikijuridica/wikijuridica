# Blueprint v4 — Volume II · Partes IV e V
## A Plataforma Viva de Conhecimento e o EnaEval

**Data-base 22/09/2026 · dono da ideia e do projeto: Rafael Toledo (OAB/RJ 227.191).**

Este Volume II **complementa** as Partes I–III do Blueprint v3. Nada do v3 é descartado: o que a engenharia
das ondas F, G e H corrigiu está marcado com linha `supera:`; o resto continua valendo como escrito.
A fonte única de números é `research-v4/CANON-v4.1.md` — `CANON-v4.md` e `CANON.md` (v3) estão **superados**
e nenhum número deste documento vem deles. A hierarquia de autoridade é
`CORRECOES-DONO.md` > `research-v4/DECISOES-ORQUESTRADOR.md` (D-1…D-17 + adendo) > `CANON-v4.1` >
`LEDGER-CORRECOES` > relatórios.

**O nome do bot é EnaEval.** Não se escreve "a plataforma", "a casa" nem "o bot".

**Regras de redação que valem para cada linha abaixo.** Hardware exato e definitivo: Ryzen 7 9800X3D
(8C/16T, L3 96 MB, AVX-512), RTX 5060 Ti 16 GB (sm_120, 448 GB/s), **32 GB** DDR5-6000, NVMe **4 TB**,
placa ASRock B850 Pro-A, nobreak, notebook antigo como nó secundário. **Sem nuvem, sem aluguel, sem compra,
sem inscrição em plataforma de terceiro pago.** Se um cálculo não fecha, a resposta é engenharia de
alocação — tiering, compactação, quantização, poda, mmap, lote, tempo — nunca redução de escopo.
**Nenhuma duração de cronograma**: não há dias, semanas, meses ou trimestres de plano. Onde aparece
"GPU-dia de máquina" é **medida física de consumo**, como "ampère-hora"; onde aparece "30 dias de
quarentena" ou "SLA ≤ 4 h" é **prazo normativo**, não etapa de projeto. Toda fase é objetivo com critério
de pronto binário.

**Linha de base, que não se reabre** (CORREÇÕES §5 e §7): **≥ 3.300 citações por IAs por dia** (quase 100 mil
em menos de 30 dias, com servidor instável), **6.086 crawls de IA por dia** (42.601 leituras verificadas em
7 dias; GPTBot 27.685/semana), tráfego humano substancial como terceiro canal, **~10.000 requisições/mês na
API da rede social — hoje sem conteúdo**, **18.774 páginas** no acervo. Rendimento atual **0,176
citação/página/dia**. Meta 100.000/dia ⇒ fator **≈ 30×**. Toda curva é piso, nunca teto.

**Formato de cada subseção:** *Decisão fechada* → *Mecanismo* → *Números* → *Por que ninguém tem*
(só onde é inédito) → *Origem*.

---

# PARTE IV — A PLATAFORMA VIVA DE CONHECIMENTO
### o que as IAs do mundo consomem, e por que confiam

---

## IV.1 · Tese do Volume II: confiança antes de transação

**Decisão fechada.** O produto não é a API paga. O produto é **conhecimento jurídico verificável, vivo e
barato em tokens**, servido de graça no núcleo, com transação como camada opcional. A ordem é invariante:
*elegibilidade → consistência → verificabilidade → transação*. Uma IA famosa não passa a citar a Wiki
Jurídica porque o texto é persuasivo — modelos escolhem por relevância e ignoram sinais de estilo
(arXiv:2402.11782) e formato Q&A sozinho não aumenta absorção (arXiv:2604.25707, medido sobre 21.143
citações). Ela passa a citar quando (a) a página é selecionável, (b) a identidade da fonte é a mesma em
toda superfície, (c) a afirmação vem com prova que um terceiro verifica offline, e (d) o cache dela é
invalidado quando o direito muda. As quatro coisas são engenharia, não marketing.

**Mecanismo — o organismo.** O fluxo diário é um ciclo fechado, e cada seta é um job da fila River:

```
decisões (30.000/dia, inteiro teor) ─┐
comunicações DJEN (400.000/dia) ─────┤
doutrina (OAI-PMH, BDTD, TCU, CJF) ──┼─▶ extração determinística ─▶ CLAIM (7 tipos, imutável,
eventos normativos (DOU/INLABS) ─────┤     (PDFium/Wasm, AKN, PEG)      endereçado por conteúdo)
jurisprudência (BNP, CKAN, TST) ─────┘                                        │
                                                                              ▼
      FEED (JSONL + WebSub + Nostr) ◀── ANSWER UNIT v2 ◀── GP/1 / JSON-LD / CSL-JSON / Markdown
                │                              │                              │
                ▼                              ▼                              ▼
     INVALIDAÇÃO (delta 8 B/morte) ──▶ cache da IA externa expira ──▶ a IA volta ──▶ cita ──▶ /verify
```

A camada de protocolo em que isso assenta **já é de classe mundial e já gera citação**: `/mcp` com 15
ferramentas registradas no MCP Registry oficial (`br.com.wikijuridica/acervo-juridico` v1.2.0), agent-card
A2A, `ai-catalog`, `api-catalog` (RFC 9727), OpenAPI com 13 operações, `/api/v1/lote` NDJSON,
`/api/v1/citacoes` (que já é o `/verify`), 6 datasets abertos com sha256 (585.592 registros), `llms.txt`,
CSL-JSON, `repr_digest` RFC 9530, `feed.xml`, `security.txt`. **Nada disso é desligado.** O Volume II nasce
em cima, evolui três ferramentas que já existem (`contexto_juridico`, `mudancas_desde`, `impacto`) e liga
os caminhos que hoje dão 404.

**Números — os dois perfis do escalonador (D-10').** O orçamento de GPU **não é lista aditiva**. A leitura
literal do v4 dava 101,0% da folga porque três documentos contavam o mesmo produto três vezes. A regra que
fecha o buraco: *uma thread de caso da rede social **é** uma rodada de arena* — mesmos quatro papéis, mesmo
commit-reveal, mesmo mercado ancorado. É **um produto** (`debate`) com **dois perfis de custo**.

| Perfil `regime` (o 8B jurídico serve) | GPU-s/dia | % da folga |
|---|---:|---:|
| F01 — fluxo diário (30k decisões, DJEN, doutrina, linguagem simples, 200 units) | 10.622 | 23,3% |
| F03 — paradigmas 310 + casos difíceis 612 | 922 | 2,0% |
| F02 — doutrina em regime (está dentro dos 5.501 do F01; contado por conservadorismo) | 580 | 1,3% |
| G01 — premeditação: extrator 4B em 11.600 chamadas/dia | 3.480 | 7,6% |
| **DEBATE — 479 × 18,29 (leve) + 120 × 41,0 (arena) = 599 debates/dia** | **13.681** | **30,0%** |
| F07 — 30 serviços em modo máximo (0 no modo padrão) | 2.900 | 6,4% |
| G03 — OCR de backfill, classe 4 preemptível (**substitui** os 600 de regime, não soma) | 4.000 | 8,8% |
| **TOTAL** | **36.185** | **79,4%** |
| **Sobra para treino de manutenção** | **9.415** | **20,6%** |

| Perfil `construcao` (o 8B ainda é obra e **não serve**) | GPU-s/dia |
|---|---:|
| deltas que sempre rodam (OCR 600 + mídia 110 + embeddings 100) | 810 |
| debate a 25% — 120 × 18,29 + 30 × 41,0 = 150 debates | 3.425 |
| G03 OCR a 50% | 2.000 |
| F07 em modo padrão | 0 |
| **Reservado** | **6.235** |
| **LIVRE para treino e indexação** | **80.165** |

Folga de GPU: **45.600 GPU-s/dia (52,8%)** de 86.400 — a máquina roda 24/7, não existe janela noturna.
Backlog de construção **3.052.330 GPU-s**, 100% local: **38,1 GPU-dias de máquina** no perfil `construcao`
(35,7 sem semeadura e OCR) contra **324,2** em `regime`. É isso que fixa a ordem de execução: **construir o
modelo antes de ligar arena e rede social em regime**. A transição `construcao → regime` é **objetivo com
critério de pronto (backlog = 0)**, nunca data.

CPU: **255.256 de 691.200 núcleo-s/dia = 36,9%**; folga **435.944 = 5,046 núcleos**; demanda de regime
**85.917 = 19,7% da folga**. RAM: **25.854 MiB = 25,25 GiB** comprometidos, margem elástica 2.818 MiB,
**envelope rotativo de 6.656 MiB com um locatário por vez**. NVMe: **122,6 GB/dia** de escrita ⇒ **28,6 anos**
a 1.280 TBW; ocupação projetada **1.847,3 GiB = 49,6% do disco**. Energia: **R$ 252,46/mês** em regime.

`supera:` o v3 fixava folga de GPU em 47.861 GPU-s/dia e folga de CPU em 5,41 núcleos — são **45.600** e
**5,046**. `supera:` "janela noturna de 6–8 h / 28.800 GPU-s" — a máquina é 24/7, o escalonador é contínuo
com preempção latchada. `supera:` "1.000 rodadas de arena/dia = 9.250 GPU-s" e "599 threads **e** 120
rodadas" — era dupla contagem; é um produto com dois perfis.

**Origem.** CORRECOES-DONO §2, §5, §6, §7 · CANON-v4.1 §1, §3 · D-10' · H01 §1 (G1, G2, G3, G19) ·
FIX-B §1 · `research-v4/orcamento/orcamento_v4.py`.

---

## IV.2 · O objeto de conhecimento

**Decisão fechada.** A unidade que a IA consome é o **claim**: imutável, endereçado por conteúdo, com
estado vivo **fora** do hash. `id = ni:///sha-256;b64u(SHA-256(JCS(núcleo)))` (RFC 6920 + RFC 8785). O núcleo
é o fato — asserção, URN, âncora, spans, intervalos de vigência e eficácia, carga do tipo. Prova, política,
confiança e estado ficam fora. Reverificar com τ novo **não** muda o id; mudar uma data de vigência **muda**.
A morte (revogação, superação, cancelamento, errata) é **evento no feed apontando o sucessor**, jamais edição
do claim.

**Mecanismo — os sete tipos e o que cada um exige.**
`NormClaim · HoldingClaim · ThesisClaim · DoctrineClaim · ProcedureClaim · DefinitionClaim · ConflictClaim`.
A política de publicação é o `if/then` do JSON Schema, não prosa:

| `assertion_kind` | Exige | Onde se usa |
|---|---|---|
| `extractive` (**default**) | `quote_in_span` exato sobre `text.sha256` | Norm, Holding (ratio literal), Thesis, Definition |
| `attributed_quote` | `quote_in_span`; citação ≤ 300 caracteres | Doctrine (Lei 9.610 art. 46 III) |
| `paraphrase` | `quote_in_span` **∧** NLI ≥ τ (lido de `verify_config`) | leitura simples, posição doutrinária |
| `templated` | toda evidência tipada verificada | Conflict (lados + linha do tempo) |
| `computed` | `deterministic_replay` byte-idêntico | Procedure |

O `verdict` **só existe** se toda checagem com `target = assertion` passou, e é sempre
`span_entails_claim` — nunca "verificado", nunca "verdadeiro no mundo". Um NLI multilíngue genérico foi
medido em 18 pares jurídicos verdadeiros e passou **3 de 18** em τ = 0,906: por isso a asserção padrão é
extrativa, e a paráfrase só publica com o verificador próprio.

**Span duplo, obrigatório.** `raw{off,len,sha256}` = bytes como servidos; `text{sha256, canon:"wj-canon-1"}`
= SHA-256 do texto canônico UTF-8 **NFC**. Sem isso a prova quebra por construção: o Planalto serve
`windows-1252` sem declarar charset, e o parágrafo único do art. 59-A da CLT tem 408 bytes com `<b>` e `<a>`
dentro contra 345 caracteres canônicos. Pior: **o mesmo parágrafo aparece duas vezes com bytes idênticos**
(offsets 256.411 e 261.422 — redação da Lei 13.467 antes e depois da MP 808). `(off,len)` é identidade;
hash sozinho não basta; e a checagem estrutural de tachado é o que distingue as duas.

**Enums únicos (FIX-A).** Havia quatro cópias dos mesmos enums em JSON Schema, SQL, Go e CDDL. Agora existe
**um gerador**: `research-v4/enums/enums.yaml` → `gen.py` → `out/enums.{schema.json,sql,cddl,go}`, com
`--check` como portão de CI (exit 2 em divergência). **20 enums, 163 valores**; `--check` fecha em
**35 alvos, 0 divergências** contra `SCHEMA-v4.1.sql`. As extensões que o CANON declarava "aplicadas" e que
o grep não achava em lugar nenhum foram de fato aplicadas: `forca927 += III_A_resp_relevancia,
administrativa_vinculante` (9 valores); `thesis.estado` 8 → **15** (Portaria CNJ 116/2022, e também no
`historico[]`); `legalTime.mode += condicional` (11); `DefinitionClaim.kind += oficial_tpu`;
`ProcedureClaim.kind += prognostico`; envelope `+= assertion_es` (≤ 600 chars), `origin` e `profile`, ambos
**obrigatórios**; `manifestation.fonte.kind += tcu_bulk, carf_solr, ckan, oai, eurlex, hudoc, ccidx` (27);
`span.locator.kind += css-selector`. Suíte: **27/27 ataques recusados + 58/58 vetores positivos aceitos**.

**Exemplos reais, bytes baixados.** Dez claims selados com hashes recomputáveis, entre eles: CLT art. 59-A
p.ú. v3 (`ni:///sha-256;i0kFV4Y2…`, com `assertion_holds` atravessando três redações — Lei 13.467 → MP 808
→ Lei 13.467 restaurada); STJ REsp 1.199.782/PR (Tema 466), `forca_927: III_repetitivo_rg_irdr_iac`, ratio
extrativa; TST Súmula 444, `mode: cancelada`, vigência até 30/06/2025 e **eficácia encerrada em 11/11/2017**
— o caso-escola tri-temporal; DoctrineClaim da Revista Gralha Azul/TJPR p. 224, em que o NLI **reprovou** a
paráfrase (179/1000) e o sistema caiu, sozinho, para citação literal atribuída; ConflictClaim C1 do rol da
ANS (REsp 1.733.013/PR × REsp 1.876.630/SP → EREsp 1.886.929/SP → Lei 14.454/2022 → ADI 7265);
ProcedureClaim de prazo com `certo:false`; e `procedure_prognostico_tjrj`, o primeiro `kind: prognostico`
real (célula TJRJ/G1/7/7779, n = 1.843, banda conformal 549–671 milésimos).

**Grounding Pack GP/1 — a serialização que cabe na janela.** Quatro serializações do mesmo fato
(JSON-LD 1.1, Markdown, CSL-JSON e GP/1); GP/1 é a que vai ao prompt.

```
⟦WJ-GP/1 k=EKdBC3Y- em=2026-09-22 tx=1790089200 n=5 perfil=std⟧
DECISÃO: RESPONDER — resposta curta: não há dobra automática do feriado trabalhado na 12x36 pactuada.
REGRA: afirme só o que os itens [C#] sustentam; cite [C#]; respeite a vigência; ausência só pela COBERTURA.
@L1=urn:lex:br:federal:decreto.lei:1943-05-01;5452
[C1] 12x36·feriado: Na 12x36 a remuneração mensal abrange o descanso em feriados e os feriados trabalhados
     consideram-se compensados.
 vale 2017-11-11→ (3 redações; MP 808 §1º igual de 2017-11-14 a 2018-04-23) · lei · classe A
 «Parágrafo único. A remuneração mensal pactuada pelo horário previsto no caput deste artigo abrange…»
 CLT (Decreto-Lei 5.452/1943) · L1!art59-1_par1 · r48214
… [C2] Súmula 444 cancelada · [C3] pactuação · [C4] regra geral Lei 605/1949 · [C5] conflito resolvido
COBERTURA: CLT/Planalto D0; súmulas TST 100%; acórdãos TST no DJEN desde 2025-05-16.
⟦/WJ-GP/1 k=EKdBC3Y-⟧
```

Quatro decisões de desenho, cada uma com razão medida: **(1)** a `DECISÃO` abre e o conflito + `COBERTURA`
fecham, porque o desempenho é em U na posição da evidência (arXiv:2307.03172; viés intrínseco
arXiv:2406.16008); **(2)** a vigência fica **colada** à asserção, porque a falha dominante de LLM é aplicar a
lei mais recente independentemente da data do fato, e modelos com raciocínio mais forte erram **mais**
(arXiv:2608.14610); **(3)** cita-se por alça `[C#]` (3 tokens) e não por URN (31,5 tokens), com *late
binding* no host — é a trie de ⟨URN⟩ levada para modelos de terceiros; **(4)** o hash não vai ao prompt (33
tokens, zero valor semântico): vai ao sidecar, que o host verifica em 172 µs.

**Answer Unit v2 — a resposta na palavra 1.** A página canônica vira contêiner de claims com linter
bloqueante `wj-aulint` (R1–R10): TL;DR como primeira frase ≤ 60 palavras, palavra decisória em primeiro
lugar (`Sim|Não|Depende`), ≥ 1 data e ≥ 1 número de norma nas 50 primeiras palavras, ≥ 1 número por 100
palavras **todos ligados a claim ou ferramenta**, âncora = fragmento LexML, blocos obrigatórios de
vigência / divergência / linguagem simples / verificação / como-citar, corpo ≤ 900 palavras.

**AI Source Card.** `/.well-known/ai-source-card.json`, assinado, 8.239 B de JCS, com `identity`,
`coverage`, `freshness`, `license`, `corrections`, `verifier`, `quality`, `security`, `access` e `citation`.
Cada endpoint declara `live` ou `planned` **como medido**, e cada métrica de qualidade sai `null` com
`pending_first_run` até o portão G1 rodar. Publicar o que ainda não foi medido, com o nome de quem vai
medir, é confiança operacional; publicar número sem denominador é o contrário.

**Ausência com cota — quando a IA pode dizer "não existe".** Cada célula (tribunal × tipo × período) declara
mundo `closed` (leis, súmulas: numeração contígua, prova de exclusão em Sparse Merkle Tree) ou `open`
(decisões: só cota). Para mundo aberto, ρ = completude × texto integral × recall de extração
= 0,999 × 0,996 × 0,910 = **0,905**, e a chance de não ver nenhuma de m decisões verdadeiras é (1−ρ)^m:

| m | 1 | 2 | 3 | 5 |
|---|---|---|---|---|
| P(falsa ausência) | 9,5% | 0,90% | 0,086% | 0,0008% |

No schema, **célula aberta sem cota é inexprimível**, e só o `permitted_statement` da célula pode ser dito.
Fora de célula coberta, a ação correta é **abster** — que na função de utilidade com λ = 4 é a de utilidade
máxima.

**Invalidação em três vias.** (1) *Empurrão diário, zero upload*: lista ordenada dos **8 primeiros bytes** do
SHA-256 de cada id morto do dia, assinada — a IA compara contra o próprio cache em casa (princípio do
CRLite); com 40 M claims e 0,3–1%/mês de morte são 4–13 mil mortes/dia = 32–107 KB/dia. (2) *Consulta
assinada*: `POST /k/invalidation/v1/check` com até **10.000 ids** devolve **1.213 B** (só mortos, avisos e
desconhecidos, uma assinatura por lote) — `unknown` é sinal de id fabricado. (3) *WebSub* (W3C Rec.
02/06/2026), p95 evento→push ≤ 90 s; na revisão MCP 2026-07-28 o mesmo fluxo sai por
`subscriptions/listen`, porque `resources/subscribe` foi removido. Regra dura de schema: `claim.dead` só
com `grau_certeza_milli = 1000`; abaixo disso é `claim.warn`.

**Números.**

| Grandeza | Valor |
|---|---|
| GP/1 `std`, 5 claims | **1.322 tokens** Qwen3 (1.077 com o vocabulário estendido); com bloco `[P#]` compacto, **1.339** |
| `contexto_juridico` ao vivo / 5 páginas `.md` | 9.176 / 16.290 tokens ⇒ **−85,6% / −91,9%** |
| Orçamento do pacote | T(k) ≈ 329 + 197·k tokens |
| URN / alias / alça `[C#]` / SHA-256 | 31,5 / 6,75 / **3** / 33 tokens |
| Claim em JSON / CBOR (CDDL, RFC 8610) | 3,0–5,0 kB / **0,68–1,16 kB** |
| Answer unit | resposta na palavra 223 → **palavra 1**; 3.258 → 2.767 tokens; 10/10 regras |
| Invalidação | 10.000 ids → **1.213 B**; delta diário **8 B por morte** |
| Frescor privado (baldes de prefixo de 16 bits) | 610 URNs por balde, 7,3 kB |
| Fluxo diário | **0,63 núcleo** (12,5% da folga de 5,046) · **10.622 GPU-s** (23,3% da folga) · 0,38 GB de RAM |
| Teto da CPU livre sozinha | **297.001 decisões/dia** = 2,4× tudo o que o Judiciário brasileiro julga por dia |
| Schema | 11 exemplos válidos · **27/27 ataques recusados** · 58/58 positivos · JSON-LD expande em 81–149 N-Quads |

**Por que ninguém tem.** (a) Claim endereçado por conteúdo **com estado vivo separado** — a citação jurídica
passa a ter a semântica de certificado: objeto imutável + log de eventos, e o cache de qualquer IA é
invalidável por diferença de conjuntos. (b) `assertion_holds`: a validade da **proposição** como união das
redações que a sustentam — "o que valia em D" e "essa afirmação vale em D" deixam de ser a mesma pergunta.
(c) **Ausência com cota** por célula: a primeira fonte jurídica que diz à IA quando "não existe" é afirmável
e com que erro. (d) **Span duplo**: prova de citação que funciona em fonte cp1252 e em PDF, onde o desenho
atual do draft SCITT quebra. (e) GP/1 com citação por alça e prova fora do prompt.

**Origem.** F01 §§1–7 · FIX-A §1 · CANON-v4.1 §7 · F06 D4/§4.5 (normalização) · F03 §3.3 (alinhamento).
`supera:` E07 `schema.sql` (âncora `art5_incX`), E01 draft-00 (`man_sha256` "as served"), C03
(`calendario_versao` vazio), D04 (`answunit.py`) e o fragmento `!art59a` publicado hoje no site — o padrão
LexML correto é `!art59-1_par1`.

---

## IV.3 · Jurisprudência estruturada: o precedente como dado

**Decisão fechada.** **Força vinculante é um vetor de efeitos processuais datado, não um número.** O escalar
H do v3 continua existindo — como *projeção para ranking* —, mas o objeto que a IA recebe é um enum de
**19 forças**, **22 efeitos** ancorados em URN LexML e **85 pares força→efeito com `daterange`**. A razão é
medida, não estética: a **Lei 15.484/2026** criou o inciso **III-A** do art. 927 do CPC (REsp sob regime de
**relevância**), com **vigência em 03/09/2026**, e ele **não** herda os efeitos dos arts. 311, 332, 496, 521
e 1.022. Colapsá-lo em "III" apaga a diferença que decide uma peça.

**Mecanismo — a prova rodada no banco.**

```sql
CREATE TABLE forca_efeito (forca forca_vinculante NOT NULL, efeito text NOT NULL REFERENCES efeito_processual,
  vigencia daterange NOT NULL, fonte text NOT NULL,
  EXCLUDE USING gist (forca WITH =, efeito WITH =, vigencia WITH &&));
```
```
efeitos de V_RESP_RELEVANCIA em 2026-09-02 =                          (vazio: III-A ainda não vigia)
efeitos de V_RESP_RELEVANCIA em 2026-09-03 = AGRAVO_INTERNO_NAO_ARESP, DEVER_ENFRENTAR_489,
   NEGATIVA_SEGUIMENTO, OBSERVANCIA_927, RECLAMACAO_EXCEPCIONAL, RELATOR_MONOCRATICO, RETRATACAO,
   SOBRESTAMENTO_FACULTATIVO                                          (8 efeitos; sem 311/332/496/521/1022)
```

O repetitivo tem 14 efeitos, a repercussão geral 13, o IRDR 11, o IAC 7 (sem 311 II e 521 IV, porque IAC não
é "caso repetitivo" pelo art. 928), a RQF 8. Pesos H mantidos do v3 e estendidos: 1,00 (controle
concentrado, súmula vinculante) · 0,90 (cautelar) · 0,85 (RG, repetitivo, IRR) · **0,80 (RQF)** · 0,70
(IRDR, IAC) · 0,60 (súmula STF/STJ, negativos) · 0,55 (TNU) · 0,50 (pleno/órgão especial) · 0,45 (OJ/PN) ·
0,40 (súmula local).

**Registros oficiais são fontes adversariais, e isso está medido.** Todos os endpoints abaixo foram chamados:

| Fonte | Resultado | Defeito medido |
|---|---|---|
| **BNP** (CNJ/Pangea) `POST /api/v1/precedentes` | 200 sem autenticação; **14.619 registros** em 62 órgãos com espécie ativa (93 cadastrados; TSE, 27 TREs e 3 TJMs sem espécies); delta horário | `historico` **replicado**: 1 histórico distinto para **1.479/1.479** temas de RG do STF; 32 para 1.473 RR do STJ ⇒ descartado como valid time. **2,00%** das teses degeneradas (tese = questão); **25,7%** sem tese. STF com 0 atualizações em 7 dias |
| **STJ CKAN** `precedentes-qualificados` | 200 (era 403 no v3), CC-BY; Temas.csv 2.578.086 B | **29 linhas duplicadas byte a byte** (1.502 → 1.473); linha plana mistura versões (Tema 677 traz datas de 2014 e tese de 2022) |
| **STF portal** por tema | 200 com AIA chasing (o servidor manda a folha duas vezes e omite a intermediária GlobalSign) | variantes textuais da tese entre certidão, ementa, ED e registro |
| **TST** `jurisprudencia-backend2` | 200 com `ementa`, `dispositivo`, `inteiroTeorHtml`, `tipoDecisoes` | — |
| **CNJ SGT** REST CSV | 200; 975 movimentos, 1.815 complementos | o v3 só usava SOAP |

**Estado da tese é máquina temporal, não rótulo.** `estado_tese` tem **15 valores** normalizados do SitT da
Portaria CNJ 116/2022 e **46 transições** com base legal, 14 das quais "abrem ciclo". A tabela é bitemporal
com `EXCLUDE USING gist`, `inicio_exato boolean` para fronteira observada mas não datada, e trigger
`DEFERRABLE` impondo continuidade (I-TES-1) e transição permitida (I-TES-2): observação inexata só pula
estados por arestas que não abrem ciclo, salvo com `evidencia_revisao`. **Replay das 1.473 fichas oficiais
do STJ: 1.470 aceitas (99,80%), 3 recusadas** — e as três são defeitos **do registro oficial** (Tema 1.282
com julgamento de 2005 para afetação de 2024; Tema 1.337 com sessão iniciada gravada como julgamento;
Tema 1.459 com julgamento = afetação). Elas entram em quarentena e viram `qualidade_fonte` no passaporte,
não silêncio. Consulta pontual `status_em(tema, data)` custa **0,133 ms**.

**Ratio e dicta com gabarito de graça.** A **Recomendação CNJ 154/2024** padronizou a ementa
("I. Caso em exame · II. Questão em discussão · III. Razões de decidir · IV. Dispositivo e tese") e a adoção
é **37,9% das ementas do STJ de 2026** (36,0% em 2025; 17,6% em 2024) — o que torna possível um parser PEG
**zero-LLM**. A extração é sempre determinístico → 8B com gramática → V⁴, e **o 8B não escreve texto de
campo**: emite offsets no texto canônico, enums e datas copiadas do span; o serializador recalcula
`sha256(texto[off:off+len])` e recusa divergência. O gabarito é grátis: **4.211 teses oficiais** limpas
(4.297 menos 86 degeneradas), 1.159 do CSV do STJ, `teor` do STJ e `codDecisao` do TST para resultado,
certidões para vencidos, NUGEPNAC para modulação. 319 teses (7,4%) têm proposições enumeradas — uma tese
vira N `HoldingClaim`.

**Superação, distinção e erosão.** A regra de superação tácita é: **mesma chave de questão tipada, nível
superior, vigência posterior, polaridade oposta e nenhuma aresta DISTINGUE**. A chave tipada
(`BASE_CALC(icms,pis)`) substitui similaridade lexical e resolve um erro que o TF-IDF comete: ele junta
STF Tema 69 com STJ Tema 1.223, que é a **questão inversa**. O achado real:

```
BASE_CALC(icms,pis)  CONFLITO: STF RG 69 (−1) | STJ Tema 313 item ii (+1, "Trânsito em Julgado")
                               | STJ Súm. 68 (+1, Cancelado)
```

**O STF Tema 69 superou tacitamente o item ii do STJ Tema 313**, com grau 0,90 por Dempster–Shafer
(estrutural 0,7 combinado com o citacional — o próprio STJ adota a orientação oposta nos Temas 1.125 e
1.372). Em 22/09/2026 o registro oficial do STJ ainda mostra o Tema 313 como "Trânsito em julgado" sem
revisão: **uma IA que confie no registro afirma o contrário do STF.** Superação parcial, por proposição: o
item i segue vigente. E a trava permanente: **superação tácita nunca é certeza sem ato oficial** — grau < 1
sem ato é inexprimível no banco (I-SUP-1) e vira `claim.warn`, jamais `claim.dead`.

A distinção lexical é inútil e está medido: em 850 decisões do STJ (64.338 sentenças), a regra lexical de
"superação" dispara 51 vezes e **49 (96,1%) são superação de óbice processual** ("superação da Súmula 691");
só 2 são overruling real. Daí o classificador precisar da classe `OBICE` separada, do atributo `enunciador`
(parte × órgão, que sai da segmentação) e de negativos duros. Linha de base a bater: precisão SUPERA de
**3,9%**. Erosão é CUSUM de Bernoulli calibrado por tese, com h = 4 na watchlist interna e **h = 5 no sinal
público** (ARL₀ 725–1.174 meses; ARL₁ 2,3–19,5): com 5.780 teses, h = 5 dá ≈ 7 falsos alarmes/mês em toda a
base, e todo alarme é `warn`.

**Passaporte do Precedente.** Documento JSON único (schema 2020-12) com `status` primeiro (campo decisório),
`forca` (enum + efeitos datados + escopo + H + marco **nominal/estrito**), `tese` (versões com vigência,
eficácia, acórdão e **variantes** D0–D3), `aplicabilidade`, `modulacao`, `estado.historico` com
`inicio_exato` e fonte com sha256, `relacionados` (tácita < 1 sem confirmação é recusada pelo próprio
schema), `adesao`, ponte para doutrina, `qualidade_fonte` e os ids de claim. Instância real do **STF Tema
69**: 13.391 B, 0 erro. O Tema 69 tem **quatro variantes oficiais** da mesma tese (registro do tema,
certidão de julgamento, item 3 da ementa, ementa dos ED) e modulação com marco **nominal 15/03/2017 ×
estrito 16/03/2017** — vigência formal do acórdão em 02/10/2017, eficácia ancorada no julgamento: é o caso
que justifica o eixo triplo.

**Escala para 27 TJs, 6 TRFs e 24 TRTs pelo gatilho DataJud.** Não há varredura: há **O(quem teve decisão
hoje)**. A TPU tem 45 códigos de evento de precedente com complemento carregando o número do tema —
sobrestamento (265 RG, 11975 repetitivo, 12098 IRDR, 14968 IAC, 14973 IRR, 15780 RQF), levantamento
(14974–14985), retratação (12258, 15561–15565), negativa por tema (15621, 15622, 15693, 15781), afetação
(12092/12093). Onde o tribunal preenche o complemento, adesão e sobrestamento se contam **sem ler inteiro
teor**; onde não preenche, cai para texto. Medido: preenchimento do nº do tema no movimento 265 é **81,9% no
TJSP**, 13,2% no TRF3 e **0% no TJMG**; a contagem direta no Elasticsearch superestima **8,4×** porque
`movimentos` não é `nested` — a reconstrução local é obrigatória.

**Números.** 19 forças · 22 efeitos · 85 pares datados · 15 estados · 46 transições · **10/10 ataques
recusados** no schema · BNP 14.619 registros, 5.780 qualificados, 4.297 com tese, 86 degeneradas (2,00%) ·
STJ replay 1.470/1.473 (99,80%) · Tema 69 com 4 variantes · léxico: 96,1% das "superações" são de óbice ·
CUSUM h=5: ARL₀ 725–1.174 meses · custo **922 GPU-s/dia (2,0% da folga)** e **290 núcleo-s/dia (0,06%)** ·
backfill dos 4.211 paradigmas **65.270 GPU-s** · RAM < 100 MB · disco ≈ 10 GB/ano.

**Por que ninguém tem.** Força vinculante como **vetor de efeitos datado** — a IA sabe se pode pedir tutela
de evidência, não só que "vincula". Estado de tese com **observação inexata tipada** e anomalias oficiais em
quarentena. **Variantes oficiais** da mesma tese com classe de divergência. Modulação **nominal/estrita**.
**Superação tácita por proposição**, com grau e latência de formalização medida — nenhuma base marca hoje o
Tema 313 (ii) como superado. **Adesão por movimento TPU**, sem ler texto.

**Origem.** F03 §§1–8 · CANON-v4.1 §6, §13 · F01 (alinhamento de tipos).
`supera:` I.5.1 — a `tese_versao` do v3 ganha máquina de estados, variantes e modulação nominal/estrita.
`supera:` III.3 — `create_graph('wj')` **falha** em AGE ≥ 1.5 (`MIN_GRAPH_NAME_LEN = 3`): o grafo é `wjg`;
e o AGE 1.5 não tem *list comprehension* em Cypher, o que virou regra de lint. `supera:` F01 —
`forca927` precisa de `III_A_resp_relevancia` e `thesis.estado` dos 15 valores.

---

## IV.4 · Doutrina verificável

**Decisão fechada.** **Doutrina entra como fato estruturado, nunca como texto do autor.** O que se armazena,
publica e vende é a **posição** — conteúdo científico e ideia, que a Lei 9.610 exclui da proteção (art. 7º
§3º e art. 8º I, VI e VII) — acompanhada de metadados de autoria, **um trecho de até 300 caracteres** como
prova (art. 46 III), a paráfrase verificada (art. 47) e as URNs dos fundamentos. Texto integral só é
persistido quando o regime da obra autoriza; fora disso, o processamento é transitório em tmpfs (art. 30
§1º). Isso não é política escrita: é **20 políticas Cedar** e **14 invariantes de banco**.

**Mecanismo — direito autoral como código.** O bundle `WJ::Autoral` tem namespace próprio e
`policy_set_version` próprio, separado das 17 políticas de compliance. Validação estrita com `cedar-go
v1.8.0`: 6 tipos de entidade, 7 ações, **0 erros**; **39/39 vetores conformes**, cada um com a política
determinante nomeada. Todo limiar **legal** é literal (300, 3, 2.000, 12, 86.400) — o que permite provar
propriedades de ausência; todo limiar **estatístico** (τ) chega por atributo, lido de `verify_config`.

```cedar
@id("D08") // "na medida justificada" (46 III) e "pequenos trechos" (46 VIII)
forbid (principal, action == WJ::Autoral::Action::"Publicar", resource is WJ::Autoral::DoctrineClaim)
when { resource.citacao_chars > 300 || (resource.citacao_chars > 0 && !resource.citacao_span_minimo)
       || context.citacoes_da_obra_na_resposta > 3 };

@id("D05") // art. 29 IX + art. 5º VI: obra reservada nunca em disco; tmpfs só até 24 h (art. 30 §1º)
forbid (principal, action == WJ::Autoral::Action::"ArmazenarTextoIntegral", resource is WJ::Autoral::TextoIntegral)
when { ["aberto_reservado","comercial_reservado","desconhecido"].contains(resource.obra.regime)
       && (resource.persistente || resource.ttl_s > 86400) };
```

**O limite de 300 caracteres é empírico, não arbitrário.** Em artigos doutrinários sob CC-BY medidos
(n = 41), o p50 da citação direta é **191**, o p75 é 236 e **85,4% cabem em 300**. O tamanho efetivo é o
**menor span que o verificador aceita como sustentação da paráfrase** — a "medida justificada" do art. 46 III
passa a ser **calculada pelo verificador**, não escolhida pelo extrator. Três travas contra substituição da
obra: ≤ 3 trechos da mesma obra por resposta; **anti-mosaico** por `EXCLUDE USING gist` (≥ 2.000 caracteres
ou ≥ 2 páginas entre trechos da mesma edição); **cota por obra** `max(2, min(50, n_chars/30.000))` ≈ **≤ 1%
da obra** (um tratado de 800 páginas chega a 50 trechos = 0,85%).

O banco torna o estado proibido **inexprimível**: texto integral só existe para regime aberto (FK composta
com coluna GENERATED); `rights_info` verbatim obrigatório (art. 107 III); fonte lícita obrigatória (art. 107;
CUB art. 10(1)); n-grama comum < 12 tokens (art. 47); polaridade verificada (art. 24 IV); e **atribuição por
FK composta** — "o autor do claim é autor DESTA obra, o trecho é DESTA obra, a posição responde a ESTA
questão" ⇒ **atribuir a autor alheio é inexprimível**. Executado em PostgreSQL 16.13:
**32/32 casos conformes — 25 ataques recusados + 7 positivos aceitos.**

**Corpus público, testado endpoint por endpoint.** O backbone de ingestão são os agregadores, mas **a licença
vem da origem**: BDTD e OasisBR propagam **0% de licença CC (0/240 na amostra)**. Classificador por
precedência: Crossref (`license` com `content-version: tdm`) > URI de CC > frase conhecida > `license.txt` >
desconhecido (fail-closed = reservado).

| Fonte | Medido |
|---|---|
| **BDTD/IBICT** (VuFind REST) | 200 com cookie; **1.176.942 registros**; Direito ≥ 14.479 (estrito); PDF em 100%, MD5 do repositório em 100%, Lattes do autor em **92,9%**, ORCID 0% |
| **OasisBR/IBICT** | **6.418.175 registros**; BDJur/STJ 75.405 itens — é a rota para o que está bloqueado na origem |
| **OAI-PMH direto** | 200 em **13 repositórios**: UnB, UFSC, IDP (5.153), FGV (33.649), UFMG/IPEA/ENAP, CGU, JusLaboris/TST (58.409), Revista da EMERJ, Revista do TCU (1.631), Revista CNJ (404), RDA/FGV (19.569), Direito GV (766) |
| **CJF Jornadas** | **1.777 enunciados** em 26 Jornadas, com **Referência Legislativa estruturada** |
| **FONAJE / FONAJEF / ENFAM** | 177 cíveis + 133 criminais / **110** / **62**, com marcação explícita de supersessão |
| **TCU dados abertos** | **26.691 itens** (Jurisprudência Selecionada 17.811, Boletim 6.061, Informativo LC 1.995, Consultas 529, **Súmulas 295 — 252 vigentes**); `REFERENCIALEGAL` estruturado em 42,7% |
| **Informativos** | STF até o **nº 1.228** (PDF, 5 itens na edição lida), STJ até o **nº 901**; DOAJ com **90 periódicos brasileiros de Direito** |

A doutrina do Judiciário é a fonte de maior rendimento por byte e entra primeiro, porque **não exige LLM**:
o enunciado já é a asserção. Mapeamento: enunciado de Jornada → `DoctrineClaim` (`enunciado_jornada`,
persuasiva); item de Informativo → `HoldingClaim` da decisão; Jurisprudência em Teses → `ThesisClaim`;
Resposta a Consulta do TCU → `ThesisClaim` com **"caráter normativo e prejulgamento da tese"** (Lei 8.443/92
art. 1º §2º); parecer AGU aprovado → `DoctrineClaim` **vinculante para a Administração Federal** (LC 73/93
art. 40 §1º). Como a RFC 9676 §1.1 **exclui doutrina** e o vocabulário LexML só tem `acordao`, `sumula`,
`sumula.vinculante` e `decisao.monocratica`, enunciado, informativo e parecer recebem URN cunhada pela
**gramática** LexML com `urn_registry: "wj"`, resolvida em `/k/urn/{urn}` — sem sintaxe nova.

**Doctrine Graph.** Sete classes sobre o AGE: `Autor`, `Obra` (LRMoo F1 Work / **F3 Manifestation = edição**,
porque a página só é válida na edição), `Posicao`, `Argumento`, `DoctrineClaim`, `Questao` (= a mesma
`question_key` da jurisprudência — é essa junção que faz divergência doutrina × jurisprudência virar
consulta) e `Corrente` (derivada, assinada, com recibo). Fundamento **não é classe nova**: é a aresta
`FUNDAMENTA_EM` para `Redacao@sha`, por *join* temporal com o ano da obra — o mesmo padrão do `INTERPRETA@sha`.
`Contradicao` ganha **C5** (posição majoritária contrariada por tese/súmula/tema) e **C6** (posição fundada
em redação que não vale mais).

**Extração com ponteiros: inventar autor ou página é inexprimível.** O contrato de saída do extrator é GBNF,
sem campo livre onde pode haver fato:
`{"janela":"w123","autor":"ref:7","obra":"ref:7","pagina":"ancora:3","trecho":"span:412-601",
"relacao":"sustenta","voz":"autor_da_obra","parafrase":"…","fundamentos":["⟨URN⟩…"]}`.
Autor e obra são **índices** para a lista de referências já resolvida; a página sai do dígito da âncora por
regex; o trecho é um offset; a URN sai pela trie. A única prosa é a paráfrase, e ela passa pelo V⁴. A
recompensa tem o mesmo invariante algébrico da família: `R ≤ 1 − |inv|·(1 + 0,30/k) < 0` para qualquer
|inv| ≥ 1 ⇒ **autor ou obra inventados sempre dão recompensa negativa**; penalidade de **−0,60 por polaridade
invertida**, espelhando a penalidade de vigência, porque o dano típico é atribuir ao autor o contrário do que
ele escreveu (art. 24 IV).

O sinal dominante na doutrina brasileira **não** é o marcador em primeira pessoa (0,13 por 10 mil palavras):
é o **aparato de citação com página** (mediana de 16 por artigo; 143–169 por tese). Por isso `atribuicao ∈
{primaria, secundaria}` é campo de primeira classe, com peso 0,6 na secundária.

**Corrente é posterior, não contagem.** Voto **por autor** (vale o claim mais recente dele), peso
`u_a = clip(PPR,0.5,2) · q · 2^(−Δt/10) · 1[vale na redação atual]`, posterior Dirichlet/Beta com Jeffreys.
**"Majoritária" exige P(θ > ½) ≥ 0,90** — no banco, `rotulo = 'majoritaria'` com `p_maioria_milli < 900` é
inexprimível. Jurisprudência é medida **à parte** (λ = 0,25 declarado): o teste confere que adoção pelo STJ
não altera o share doutrinário.

**Cinco ferramentas `wj_doctrine_*`**, todas lookup sobre dado pré-computado, **0 GPU por consulta**:
`wj_doctrine_poll` (veredito + `p_maioria_milli` + evidências com trecho ≤ 300 + **cobertura com o que fica
de fora**); `wj_doctrine_vs_case_law` (C5/C6, as duas pontas com evidência, `forca_927`, série anual
acolhe/rejeita — é o caso em que "a doutrina entende…" leva o usuário ao erro); `wj_thesis_genealogy`;
`wj_institute_state_of_art`; `wj_verify_doctrine_attribution` (veredito `sustentado` / `contrariado` /
`atribuicao_a_outro_autor` / `nao_encontrado` / `fora_da_cobertura`, **nunca "correto"**).

**Números.** 20 políticas Cedar, **39/39 vetores**, 0 erro estrito · 14 invariantes, **32/32** (25 recusas +
7 aceites) · 300 chars: **85,4% das citações reais cabem**, p50 = 191 · licença CC propagada pelo agregador:
**0/240** · corpus ingerível ≈ **340–370 mil documentos** doutrinários + ≈ 430 mil acórdãos que citam
doutrina · ≈ **3,2 M DoctrineClaims** estimados · grafo **+≈ 5 M nós (+12%) e +≈ 17 M arestas (+5,6%)** ·
backlog **≈ 545 mil GPU-s** e ≈ 1,33 M núcleo-s · regime **≈ 580 GPU-s/dia (1,3% da folga)** e ≈ 2 mil
núcleo-s · disco **+≈ 15 GB (0,4% do NVMe)** · RAM quente ≈ 1,2 GB, **locatária do envelope, nunca
residente**.

**Por que ninguém tem.** O espaço vazio é o **objeto**: "o autor X sustenta a posição P sobre a questão Q na
obra W, edição E, página N, com trecho T ≤ 300 conferido pelo verificador, fundamento na redação R@sha,
corrente com P(maioria) calibrada, adotada pelos acórdãos D1…Dn e contrariada pela tese T*" — assinado,
verificável offline e conforme a Lei 9.610 por construção. Jusbrasil Doutrina e vLex expõem texto integral
por assinatura e nenhum dado estruturado de posição; Westlaw e Lexis citam **casos**, escritos por humanos;
Semantic Scholar tem os campos `intents`/`contexts` **vazios** para o artigo jurídico brasileiro medido, e
o OpenAlex classifica um artigo sobre perfil de juízes como "*Sex work and related issues*".

**Origem.** F02 §§1–8 · CANON-v4.1 §9 · FIX-A (enums) · F01 (tipo `DoctrineClaim`).
`supera:` III.2 — BDTD/OasisBR entram como **rota**, não como fonte de licença. `supera:` a premissa de que
"acesso aberto = licença livre": um item do BDJur de editora comercial vem sem licença livre, e o regime
`desconhecido` é fail-closed.

---

## IV.5 · Máximo de fontes e coleta

**Decisão fechada.** **O catálogo máximo cabe.** Com as 47 fontes já mapeadas mais **24 grupos novos**
testados ao vivo, a ocupação projetada do NVMe é **1.847,3 GiB = 49,6% dos 4 TB** (51,2% dos 3.606 GiB
úteis), e o backup dedicado de 1 TB fica em **98,8 GiB (10,6%)**, ou **296,5 GiB (31,8%) com 3 gerações**.
**Não é preciso escolher fonte.** O que exige escolha é o que **fica em quente**, e isso é governado por
preço-sombra, não por opinião. Fonte bloqueada por ASN não é fonte impossível: é item "testar do servidor
BR" com o endpoint já mapeado.

**Mecanismo — o catálogo (as linhas novas, com estado medido em 22/09/2026).**

| Fonte | Como se baixa | Volume medido | Estado | Armadilha |
|---|---|---|---|---|
| **TCU acórdãos completos** | CSV bulk, `\|` como separador, colunas `RELATORIO`/`VOTO`/`DECISAO` | **7,59 GiB em 42 arquivos** (2026 = 305.820.377 B) | 200 | `robots.txt` só bloqueia Yandex; sem ETag no CSV |
| **CARF** | **Solr público** `acordaos.economia.gov.br/solr/acordaos2/select` | **`numFound` = 585.274** | 200, `fl=*` devolve o texto | o formulário JSF oficial dá **404** — quem tenta pelo portal desiste |
| **STJ íntegras** | CKAN, ZIP diário D+1 | 1.290 ZIPs, **11,23 GB** | 200 | texto parcial: 828 textos para 3.945 metadados |
| **TSE + 27 TREs** | backends achados no bundle do SPA: `sjur-servicos`, `sjur-pesquisa-api`, Keycloak `autenticaje` | 27 TREs + TSE | SPA 200; `dadosabertos.tse` **403 Akamai** | nginx rejeita POST (405); exige token Keycloak + navegador; **403 é de ASN** |
| **EUR-Lex / Cellar** | SPARQL `publications.europa.eu/webapi/rdf/sparql` | **145.280 atos** só no tipo `REG` (COUNT executado) | 200 | Decisão 2011/833/UE: reuso livre com atribuição |
| **HUDOC (CEDH)** | `app/query/results` | **`resultcount` = 231.661** | 200 | reuso público CoE |
| **Common Crawl** | `data.commoncrawl.org/cc-index/.../cluster.idx` + Range-GET | `cluster.idx` **103.946.392 B** (877.051 linhas, 4,18 s) → **966 blocos, 277,15 MiB** para `.jus.br` + `.gov.br` + `.leg.br` + `.def.br` + `.mp.br` | 200 (`index.commoncrawl.org` bloqueado) | o SURT inverte o host ⇒ cada prefixo é intervalo contíguo: **busca binária, não varredura** |
| **CGU Base de Conhecimento**, **AGU/PGFN**, **RFB SIJUT2**, **CONFAZ**, **CADE SEI** | Angular / sitemap do Plone / JSF com sessão / HTML | pareceres e soluções de consulta vinculantes | 200 (CONFAZ bloqueado neste egresso) | **não se adivinha URL: lê-se o sitemap** |
| **ANEEL · ANTT · CVM** | **um** adaptador CKAN | 72 · 106 · 21 pacotes; licença `odc-odbl` lida do próprio catálogo | 200 | o erro a evitar é escrever 10 adaptadores de agência |
| **ANS · ANVISA** | índice de diretório (Apache / h5ai) | — | 200 | não são CKAN ⇒ adaptador `dirindex` de 60 linhas |
| **CNMP · MPF · DPU/ANADEP · PGE-SP · OAB** | portais; CNMP é o consolidador nacional | enunciados de Câmaras e **teses institucionais das Defensorias** | 200 | o CNA da OAB tem dado pessoal ⇒ política Cedar nega íntegra |

**Técnicas — todas as opções, com quando usar e onde está o código.** (1) API REST oficial — o BNP **exige
POST** com `{"filtro":{…}}` e devolve **405** no GET; o `/parametros` lista 93 órgãos, dos quais TSE, 27 TREs
e 3 TJMs vêm com grupo de espécies **vazio**, e o adaptador os pula. (2) **CKAN genérico** — defeito
corrigido em sessão: usar o `last_modified` do catálogo em `If-Modified-Since` faz o servidor devolver
**304 na primeira coleta**; condicional só com ETag da coleta anterior. (3) **OAI-PMH** — o DSpace devolve
`resumptionToken` **vazio** (não ausente) no último lote; o cursor é `"from|token"` para retomar a janela.
(4) SOAP (MNI 2.2.2) — registrado como opção conhecida e **não adotada**: exige certificado de advogado.
(5) RSS/Atom/WebSub — gatilho, nunca histórico. (6) **Sitemap** — a resposta certa ao "404 em caminho
adivinhado". (7) **Bulk dump — sempre a via preferida**: o TCU inteiro custa **42 requisições** contra ~1,5
milhão item a item. (8) Mirror aberto — e fica **encerrada** a busca pelo DataJud na Base dos Dados: o
GraphQL público mostra que ele **não está lá**. (9) **Índice do Common Crawl por domínio** — ~380 MB e 967
requisições por coleção, ~4× ao ano, e serve para descobrir URL de órgão sem API, recuperar página que sumiu
e **medir a cobertura do EnaEval contra o que o mundo já indexou**. (10) Headless com navegador — a técnica
**mais cara** (~1,5 s e ~300 MB de RSS por sessão): só quando nenhuma das nove anteriores serve.
(11) **Scraping ético com Web Bot Auth**. (12) Canonicalização e dedup — NFC obrigatório antes de qualquer
hash; MinHash `b=16 × r=8`, com um achado que muda a regra: **τ = 0,85 vale para inteiro teor (J = 0,984
medido com cabeçalho de DJE e rodapé de assinatura) e quebra em ementa curta (J = 0,836)** ⇒ a resposta é
**remover o boilerplate antes do MinHash**, não baixar τ, porque baixar τ colide temas distintos.

**O crawler que assina as próprias requisições (inédito).** O EnaEval assina cada requisição de saída em
**RFC 9421 / Web Bot Auth** (`@authority`, `@method`, `@target-uri`, `signature-agent`, `created`/`expires`
≤ 300 s, `tag="web-bot-auth"`) e publica o próprio diretório de chaves. Um tribunal passa a poder
**verificar com Ed25519** que aquele acesso é do EnaEval — sem cadastro, sem chave de API, sem contrato. É a
inversão exata do que a plataforma já oferece aos bots de IA que a leem, é gratuita, é o argumento técnico
para pedir cota maior, e **não existe no Judiciário brasileiro**. Implementada e testada: assina, verifica e
**rejeita** quando o alvo é adulterado.

**Armazenamento em quatro camadas.** Os três números que divergiam no v3 (530–565 GB, ~1.500 GB, 1.085 GB)
erram pelo mesmo motivo: tratam "corpus" como uma coisa só.

```
NVMe útil 3.606 GiB (de 3.726; 120 de SO/logs/swap) · corpus bruto somado 2.847,6 GiB
QUENTE (Parquet derivado + índices) .... 714,1 GiB     MORNO (WARC zstd do byte servido) .. 620,4 GiB
pg (WAL/bloat/rebuild = 55% do quente) . 392,8 GiB     SO/logs/swap ....................... 120,0 GiB
------------------------------------------------------------------------------------------------
OCUPAÇÃO TOTAL ....................... 1.847,3 GiB = 49,6% do NVMe   → CABE SEM PODA
FRIO (backup 1 TB) ...................... 98,8 GiB = 10,6%; com 3 gerações 296,5 GiB = 31,8%
```

A quarta camada é **ATESTADO**: só a linha de proveniência com `origem_sha256` + `refetch_url` — o byte
saiu, **a prova ficou** (invariante I-PRV-2, testado: a poda solta o ponteiro do WARC e **preserva** hash e
URL de refetch, de modo que "não temos mais o arquivo" continua sendo afirmação verificável). Compressão
medida sobre 305.820.377 B de texto real do TCU: gzip-9 **4,387×**, xz-6 **8,154×**, zstd-19 adotado em
**5,50×**; **PDF comprime 1,268×** — é o que torna diário oficial e tese digitalizada as classes mais caras
por byte.

**Ordem de poda (λ_disco a 82%), executada em dois cenários de estresse.** Com diário e doutrina ×3 no morno
e judicial ×2: **3.005,2 GiB = 80,7%** — ainda cabe, a poda **não dispara**. Com ×4 e ×3:
**3.589,8 GiB = 96,3%** — a poda dispara e sai, nesta ordem: **(1) WARC de diário municipal** (−530,0 GiB;
menor valor de citação por byte, é PDF, e o Querido Diário é open-source, logo re-hospedável) e
**(2) PDF de tese acadêmica** (−1.054,9 GiB; o valor está no metadado e na posição doutrinária, que ficam no
quente). Volta a **2.004,9 GiB = 53,8%**.

**O 1 TB não é espelho: é arquivo do insubstituível.** Recebe (a) os 60 GiB de Merkle, recibos, ledger,
registry, Cedar e artefatos quantizados, (b) o **morno de fonte que some** — diário oficial, DOE, dump que o
órgão sobrescreve — e (c) 3 gerações de cada. **Não entra:** índice (re-derivável), grafo AGE (re-derivável),
corpus com origem viva e atestada.

**Framework de coleta em Go, com adaptadores rodados ao vivo.**
`Source{Nome, Dominio, Discover, Fetch, Parse, Attest}` + `Dimensionavel` + `Lote`; `shape/` com balde de
tokens **por host** e AIMD (429/503 ÷ 2 respeitando `Retry-After`; 2xx × 1,05); `ckpt/` com escrita atômica
(tmp + fsync + rename + fsync do diretório); `dedup/`, `canon/`, `wba/`, `prov/`; adaptadores `bnp`, `oai`,
`ckan`, `ccidx`. Invariantes codificados e testados: **I-SRC-1** (não se busca Ref cujo ETag já está no
checkpoint), **I-SRC-2** (`Parse` não faz I/O), **I-CKP-1** (o cursor só avança depois do lote persistido —
*at-least-once* + dedup por `origem_sha256` = idempotente), **I-CAN-1** (sem prova cruzada, `norm_ok = 0` e a
captura **não é selável**), **I-PRV-1** (nada entra no índice sem `origem_sha256`). Execução real:
`go vet` limpo, `go test ./...` **12 testes, 0 falhas**; BNP, OAI (JusLaboris) e CKAN (ANEEL, 413 recursos,
licença extraída do catálogo) coletados ao vivo; plano do Common Crawl com 877.051 blocos lidos em 1,959 s.

**Legalidade como código: o bundle `WJ::Fonte`.** 18 políticas, 4 tipos de entidade, 6 ações, validação
estrita com **0 erros**, **25/25 vetores**. Núcleo: **F02** nunca contornar proteção técnica (art. 107 I–II) —
é o que impede o "resolvedor de captcha"; **F04/F05** `robots.txt` obrigatório para o crawler, mas **dump em
bloco publicado não passa por robots**, porque arquivo publicado é oferta, não varredura; **F06** crawler
HTTP **sem assinatura RFC 9421 é negado**; **F08** segredo de justiça não entra, nem cifrado (CPC art. 189);
**F13–F15** íntegra com dado pessoal só pseudonimizada **ou** já pública pela fonte **com** interesse público
(LGPD art. 7º §4º c/c art. 23), e dado sensível nunca, nem em trecho; **F16/F17** treina em oficial e em
licença aberta, **não** em CC-BY-NC, reservada ou desconhecida. Um vetor **mudou a política durante o teste**:
"publicar íntegra de decisão com nome de parte já publicada pelo tribunal" — a expectativa era negar, o Cedar
permitiu via F13, **e o Cedar estava certo**; negar tornaria o EnaEval menos útil que o próprio portal do
tribunal. O vetor foi corrigido e um segundo caso entrou (parte **não** publicada pela fonte ⇒ negado), que
é onde a regra morde.

**Fases por objetivo (nunca por dia).**

| Fase | Objetivo | Critério de pronto | CPU-s | GPU-s |
|---|---|---|---:|---:|
| **A** | fontes com API e íntegra: TCU bulk, CARF Solr, STJ CKAN, BNP, SGT, TST, Planalto, Câmara/Senado/LexML, enunciados | 100% dos 42 CSVs do TCU e dos 585.274 do CARF com `norm_ok=1`; ≥ 99% dos temas do STJ com passaporte; delta ≤ 24 h | ~310 k | 0 |
| **B** | tribunais por gatilho DataJud (movimentos 92/1061/581) | ≥ 95% das decisões novas de TJSP/TJRJ/TRFs com inteiro teor em ≤ 48 h do movimento; 0 buraco no *point-in-time* | **~1,2 M TOTAL DE FASE** (em regime são 46.440/dia, já contados no F01) | ~4.000/dia de **pico** de backfill, classe 4 |
| **C** | administrativo e regulatório: CVM, BACEN, RFB, CADE, CGU, AGU/PGFN, CONFAZ, 10 agências | ≥ 90% dos normativos do BACEN com *flag* de vigência; solução COSIT indexada; sitemap do Plone mapeado | ~180 k | ~1.500 |
| **D** | doutrina: OAI + BDTD/OasisBR + SciELO/DOAJ/CAPES + PDFs | ≥ 14.479 registros de Direito com licença classificada; ≥ 70% dos PDFs abertos com texto em classe R1 | ~90 k | **~26.000** (é a fase que consome GPU) |
| **E** | estadual e municipal: TSE + 27 TREs, 28 cortes de contas, 27 assembleias, capitais, DOEs, INLABS, MP/DPE/OAB | ≥ 80% de cobertura de leis estaduais consolidadas nas 10 maiores UFs; TSE respondendo do IP BR | ~420 k | ~12.000 |
| **F** | internacional comparado, só licença aberta | EUR-Lex ≥ 145.280 atos REG indexados; HUDOC ≥ 231.661 itens; DILA em delta diário | ~140 k | 0 |

`supera:` a fase B dizia "~1,2 M núcleo-s **por dia** em regime" — isso é **295% da folga de CPU e 1,74× a
máquina inteira**, e 26× o que o F01 gasta para processar **as mesmas** 30 mil decisões. Era erro de unidade:
**1,2 M é o total DA FASE**. Com B lido assim, a soma fecha: 310 k + 1,2 M + 180 k + 90 k + 420 k + 140 k =
**2,34 M núcleo-s ✓ = 6,69 CPU-dias de máquina** na folga residual. **Total de construção da coleta ≈ 2,34 M
núcleo-s e ≈ 43,5 k GPU-s: a coleta não é o gargalo.**

**Top-15 por valor para IA** (`V = citação esperada × exclusividade ÷ custo`): 1 TCU acórdãos completos
(**9,6**) · 2 CARF Solr (9,1) · 3 Solução de Consulta COSIT (8,7) · 4 pareceres vinculantes AGU/PGFN (8,4) ·
5 enunciados das Câmaras do MPF + teses das Defensorias (8,2) · 6 BNP com decisões vinculadas (8,0) ·
7 TSE + 27 TREs (7,6) · 8 STJ íntegras (7,3) · 9 CGU Base de Conhecimento (7,1) · 10 BACEN normativos com
*flag* de vigência, 60.668 (6,9) · 11 CONFAZ convênios ICMS (6,6) · 12 TCEs + TCMs (6,2) · 13 leis estaduais
consolidadas (5,9) · 14 EUR-Lex + HUDOC (5,4) · 15 índice CDX `.jus.br` do Common Crawl (5,1).
**O padrão das quinze: não são fontes raras — são fontes que ninguém teve paciência de estruturar.** Nove das
quinze estão nas fases A ou C, as duas mais baratas: é aí que o EnaEval compra vantagem antes de gastar um
GPU-s.

**Leitura de engenharia que inverte a intuição.** O conteúdo jurídico inteiro que interessa cabe em **24% do
disco**; a outra metade é **índice e modelo**. O gargalo não é baixar — é indexar.

**Origem.** G03 §§1–7 · FIX-B §1 (correção de unidade) · CANON-v4.1 §3 (NVMe) · F08 (WARC e atestação, não
reimplementados) · D-8.
`supera:` C01 §5 — 530–565 GB subestimava por não contar o WARC do original, que o F08 tornou obrigatório.
`supera:` F04 §6 — a cota `pg` de 1.700 GiB "em branco" **duplicava** a contagem dos índices; vira 55% do
quente. `supera:` "espelho ZFS em 2º NVMe" e "restic off-site em terceiro" — revogados; o 1 TB do dono é
arquivo do insubstituível, entregue ao notebook pela LAN.

---

## IV.6 · Integridade do conhecimento: da fonte oficial até a IA que consome

**Decisão fechada.** Uma IA famosa só trata o EnaEval como fonte se puder provar, **sozinha e barato**, que
(1) o que se cita é o que a fonte oficial publicou, (2) nada foi adulterado depois, (3) o erro é corrigido
com rastro e (4) a extração é reproduzível. **"LLM propõe, byte decide":** todo fato publicado se reduz a
bytes arquivados + projeção determinística + offsets + verificação determinística. O LLM decide **o que**
extrair, nunca **o que é verdade**.

**Mecanismo — a cadeia evidencial.** Captura atestada = **WARC/1.1** (ISO 28500:2017) + **in-toto Statement
v1 em DSSE, predicado `acquisition/v2`** + folha **COSE Hash Envelope (RFC 9995)** na trilha **SCITT (RFC
9943 + 9942)**, escrita por **Tessera v1.0.4** (POSIX, Apache-2.0) no mesmo log Merkle das chaves. A folha
de ingestão tem **442 B**; o bundle inteiro fica no registro WARC `metadata`. **SXG rejeitado** (a Google
Trust Services encerra a emissão em 30/09/2026); **C2PA rejeitado para a fonte** (embutir manifesto altera
os bytes e quebra o hash) e adotado só para mídia gerada pelo EnaEval.

**Níveis C0–C3 — o nível *é* evidência, não rótulo.**

| Nível | Exige | Imposto no schema |
|---|---|---|
| C0 | bytes + sha256 + URL + tempo, assinados pelo coletor | — |
| C1 | C0 + cabeçalhos + cadeia TLS + DNSSEC + WARC + **normalização com prova cruzada** | `norm_ok` **OU** `served = origin` |
| C2 | C1 + **≥ 2 vantagens de egresso concordando** na mesma origem normalizada | `n_vantages >= 2` |
| C3 | C1 + **a própria fonte assina** | `src_sig_ok` |

O **DOU já é C3**, e isso foi medido: a página PDF é assinada em `adbe.pkcs7.detached` com ByteRange
cobrindo o arquivo inteiro, signatário "DIARIO OFICIAL DA UNIAO" (A1 da AC SERPRO Final SSL), cadeia
validada até a **AC Raiz Brasileira v5** cuja impressão SHA-256 coincide com a publicada pelo ITI, LCR de
10.065 B sem o serial — e **sem carimbo TSA**. Consequência de desenho: **a âncora temporal é o log de
transparência**, que faz o papel do carimbo de arquivo do PAdES-LTA e fixa *quando* a assinatura foi vista
válida, antes do vencimento do certificado.

**`man_sha256` redefinido, e por quê.** O Planalto injeta no fim do HTML um `<script id="f5_cspm">` de
**1.559 B** com token por resposta: **34 de 36 respostas medidas em 3 páginas**; oito cópias da CLT deram
**7 SHA-256 brutos distintos e 1 normalizado** (`82499b3d…`, 3.529.642 B). O hash "tal como servido" é um
**nonce** — nenhum terceiro o reproduz. Por isso `man_sha256` passa a ser o hash da **representação de
origem**, sob regra versionada:

```
origin = served − Σ injeções(regra@versão)      aceito só se  prova_cruzada(cabeçalhos) = verdadeira
wj-norm/f5-cspm-tail-v1 : remove <script id="f5_cspm">…</script> ancorado no FIM do arquivo
                          exige ETag Apache "tam-mtime": tam(hex) == |origin| ∧ mtime(µs) == Last-Modified
sem prova cruzada ⇒ norm_ok = 0 ⇒ captura NÃO é selável  (I-CAP-1)
```

O nome é `wj-norm/f5-cspm-tail-v1` e **não** `wj-norm/f5-cspm@1` (D-12'): o contrato C26 já publica
`/.well-known/lar/norms/f5-cspm-tail-v1` e o nome entra **assinado** dentro de cada recibo. No SCHEMA-v4.1
existe a tabela `norm_rule` com FK de `capture.norm_rule` e de `citation_receipt.man_norm`, e a regex fechada
em `-vN`: **`@1` e nome não registrado são recusados pelo banco** (ataques N19/N20). E a composição **NFC é
obrigatória e verificada**, não asserida: o HTML do Código Civil compilado traz **10 diacríticos
decompostos** por entidade numérica (`ido&#770;neas`) — sem NFC calculado, a citação literal "pessoas
idôneas" não é encontrada e dois verificadores divergem no `span_sha256`.

**Determinismo R0/R1/R2 e a correção que o crítico impôs.**

| Nível | O quê | Onde vale |
|---|---|---|
| **R0** | bit-exato por construção | HTML/PDF, **SLSA Build L3** |
| **R1** | bit-exato no serving | **não disponível**: `VLLM_BATCH_INVARIANT=1` é beta e NVFP4 **não consta** da lista testada |
| **R2** | **votação 3-run + verificação determinística** | **é o que vale em produção** — campo `determinism` no recibo |

Prefix caching é **condição de viabilidade** do serving (sem ele o teto cai de 11.615 para 3.768
chamadas/dia), mas ele **quebra a reprodutibilidade**: com a mesma semente e lote 1, cache ligado muda a
trajetória em **36,2% a 16 bits e 75,0% a 4 bits**; desligado, **0 de 800** divergências. Três regras
(D-2'): **(1)** o caminho de **verificação** roda com prefix caching **desligado por requisição** — e o
mecanismo real não é uma flag, é **`cache_salt` aleatório por requisição** em `SamplingParams`; custa
**< 3%** do orçamento, porque a verificação é CPU/54M e só a extração no 8B é afetada. **(2)** Todo
`citation_receipt` e todo `prediction_receipt` carrega **`cache_state_digest`**: `'none'` quando rodou sem
cache, ou o **sha256 hex de `cache_salt ‖ engine_config`** — valor fora dessas duas formas é inexprimível
(CHECK), e a coluna `cache_state_sha bytea` é **DERIVADA**, de modo que texto e bytes não podem divergir.
**(3)** Serving comum mantém prefix caching. **Sem essa separação, R2 é afirmação falsa no recibo.**

**Audit kit.** `wj-audit` é Go estático com build reproduzível (`-trimpath`, toolchain pinado), stdlib mais
`pdfium.wasm` e `wazero`. Seis subcomandos: `verify`, `capture`, `icp`, `status`, `gossip`, `reproduce`.
Custo medido em 200 execuções: recibo + inclusão + consistência + quórum **511 µs**; cadeia de captura
**472 µs**; WARC + normalização + projeção R0 + span **2.245 µs**; status **9 µs** ⇒ **3.270 µs ≈ 3,3 ms de
CPU por afirmação**, e **≤ 2,5 s** com re-fetch ao vivo da fonte. Emite VSA SLSA assinada pela chave do
**auditor**. Sete desfechos nominais, **nunca booleano** — os erros são tipados E1–E7 (URN não resolve ·
âncora inexistente · NLI abaixo do τ · fora de vigência · divergência de motor · contradição · irrelevante)
e entram no `gap_queue` como insumo do seletor submodular.

**O recibo v1.1 e o ataque que ele fecha (FIX-A §2).** O verificador publicado no contrato C20 **aceitava
recibo que aponta a redação TACHADA** — bytes idênticos em dois intervalos de vigência, e o hash não
distingue. A checagem estrutural existia **só** como demo num binário auxiliar. Corrigido: `lar.go` **v1.1**,
**643 linhas** não-branco, 23.957 B, SHA-256 `feef864a5308030d14de3b914f84af74721b368a7cf76de2252c1e370f428101`,
byte-idêntico nas duas cópias do repositório. Regras fail-closed implementadas: (1) `man_norm` é **aplicado
pelo próprio verificador** e `man_sha256`/`man_len` são re-derivados — regra desconhecida ⇒
`VALID_SPAN_UNVERIFIED`, **nunca** VALID; (2) span tachado ⇒ erro `STRUCK-THROUGH` (pilha de elementos em
uma passada, sem regexp, respeitando tags void e auto-fechadas); (3) claim com `at` e `mode` fora do eixo de
vigência ⇒ erro; (4) `cache_state_digest` ausente ⇒ **recusa**. `go test ./lar/` **10/10 PASS**, com os
vetores "gêmeo tachado", "`man_norm` desconhecida", "sem `cache_state_digest`" e "F5 colapsa 8 cópias em 1".

**Errata que nunca apaga.** Claim novo + `status.successor` + **Retraction Statement no log** + propagação
por **6 canais em ≤ 60 s**. Máquina de estados `recebido → triado → warn (automático) → procedente |
improcedente | parcial → publicado`; o sistema **não espera humano para avisar**, e o humano decide só mérito
jurídico contestado. Nada de `DELETE`: o claim é imutável, muda o `status` no feed. SLA por severidade:
**S1 ≤ 4 h** (vigência errada, norma errada, redação revogada como vigente, URN inexistente) · S2 ≤ 24 h ·
S3 ≤ 72 h · S4 ≤ 14 dias; propagação p99 ≤ 60 s em todos. Taxa de **erro próprio** publicada **com
denominador** e limite superior Clopper–Pearson; evento do mundo (a norma mudou) **não conta** como erro, e a
distinção é `is_error` GENERATED no schema. Executado: `errata.sql` **6 ataques recusados + 2 inserções
válidas aceitas** — inclusive o ataque "erro próprio rotulado como 'redação alterada' para escapar da taxa
de erro".

**Testemunhas e anti-adulteração.** Política **4-de-5 testemunhas** C2SP (segura contra até 2 em conluio,
viva com 1 fora do ar), gossip por **Nostr** (kinds 1414/1415), prova de equivocação verificável offline
(**1.082 B / 2.170 B**) e **fiança pública de R$ 5.000** paga a quem apresentar bifurcação do log. Verificado
no schema: 3 de 5 ⇒ `publicavel = false`; 4 de 5 ⇒ `true`. Os sete ataques criptográficos rastreados
(resposta reescrita, trecho deslocado, **título trocado** — a consistência vira propriedade criptográfica —,
re-assinatura, bifurcação, testemunha sem normalização, gêmeo tachado) são detectados. `supera:` "VPS em
terceiro AS como testemunha" — revogado por ser nuvem; a segunda vantagem vem do notebook, de parceiros e do
C3.

**Privacidade como integridade.** O log só guarda hashes e compromissos salgados. Conteúdo com dado pessoal
é cifrado por **chave de documento** selada ao TPM: apagar = **destruir a chave** (*crypto-shredding*), com
**Erasure Statement** no log. No schema, captura com Erasure e chave viva é inexprimível, e a purga de
backup é **≤ 15 dias** (LGPD art. 19 II). Vende-se **máscara com taxa residual medida em ppm**, nunca
"anonimizado" (LGPD art. 12 §1º).

**Contribuição da comunidade.** Entra em **retrieval**, **nunca em treino** (`elegivel_treino = false` por
CHECK; `taint` nunca 0), com quarentena de 30 dias. E a **ordem no log prova** que a verificação veio depois
da contribuição: `contribution_leaf < verification_leaf < leaf_index`.

**Retenção.** **K1** perpétuo (tudo que é citado — a FK do recibo **congela** o K1) e **K2** despejável.
Recompressão sem perda dos PDFs de K1: **1,268× medido**. No cenário canônico, K1 cresce 0,256 TB/ano e o
log 15 GB/ano.

**Números.** `go run . -n=10` reproduz **94 linhas idênticas** ao log de referência · **9 cenários de
ataque detectados** · `ataques_f08.sql` **20/20 recusados + 10/10 aceitos** · audit kit **3,3 ms de CPU** ·
folha SCITT **442 B** · recibo JSON **2.731 B** · verificação de assinatura ICP-Brasil **4,4–4,9 ms** ·
normalização + hash de manifestação **11,7–12,5 ms**, uma vez por `man_sha256` e cacheável ·
`lar.Verify` **0,25–0,32 ms** por recibo.

**Por que ninguém tem.** **Recibo de citação jurídica verificável offline por terceiro** em 172 µs com 472
linhas de Go sem dependências (agora 643 na v1.1) — Lexis+, Westlaw e Practical Law medem 17%/33%/22% de
alucinação e **nenhum emite recibo**. **Nível de captura como evidência**, não rótulo. **Normalização de
fonte declarada, registrada e publicada**, que é o que torna o hash de uma fonte oficial instável
reproduzível por qualquer um. E o **fingerprint do estado de cache no recibo**: nenhum provedor de IA
publica hoje sob que estado de cache uma saída foi produzida.

**Origem.** F08 §§1–7 · FIX-A §2 (recibo v1.1) · FIX-B (schema) · D-2' · D-12' · CANON-v4.1 §10 ·
F06 D4/§6 (medição do F5 e dos ataques).
`supera:` III.2/E02 — "originais são refetcháveis" é falso para fonte que sobrescreve. `supera:` E01 draft-00
— `man_sha256` "as served". `supera:` A03/E07 — "NFC asserido" vira **NFC verificado**. `supera:` B06 —
servidor de log próprio e VPS-testemunha.

---

## IV.7 · Confiança operacional para as IAs famosas

**Decisão fechada.** **Confiança não é persuasão do LLM; é elegibilidade + consistência + verificabilidade.**
O contrato atua em quatro camadas que os operadores de fato consomem — **L1 descoberta/índice, L2 seleção,
L3 citação, L4 verificação** — e **cada IA lê um subconjunto diferente**. A alavanca de maior retorno sob
controle total é **CONSISTÊNCIA**, e ela falha hoje de forma sistêmica.

**Mecanismo — engenharia reversa dos dez pipelines.** Cada linha traz o grau de evidência:
**[D]** documentado pelo operador · **[M]** medido nesta sessão · **[I]** inferido com o mecanismo dito.

| IA | Descoberta | Como cita | Alavanca do EnaEval |
|---|---|---|---|
| **OpenAI** | OAI-SearchBot indexa; site fora do índice "não aparece nas respostas" [D]; usa parceiros de busca, com a política da Microsoft listada ⇒ dependência do índice Bing [I] | UI com `utm_source=chatgpt.com` [D]; API `url_citation{url,title,start_index,end_index}`, `allowed_domains` até **100** [D] | IndexNow (via Bing [I]); **título único**; verificar a assinatura do agente — o ChatGPT **assina** em RFC 9421 [D][M] |
| **Anthropic** | `web_search` sobre índice de terceiro (**Brave** na lista de suboperadores, resultados idênticos [I forte]); Claude-SearchBot, Claude-User e ClaudeBot **respeitam robots** [D] | `web_search_result_location{url,title,encrypted_index,cited_text ≤ 150 caracteres}` + **`page_age`** [D]; `web_fetch` só busca URL já no contexto [D] | **"Claude = 0 leituras" é previsto pelo desenho, não defeito** (§ abaixo); TL;DR e cada claim fechando sentido em **≤ 150 caracteres**; `title` nas ferramentas MCP |
| **Google** | Googlebot; elegível = indexável com snippet, **sem requisito técnico adicional e sem schema especial** [D]; *query fan-out* [D] | `url_citation` com `title` = domínio no exemplo oficial [D]; `url_context` usa cache e cai para fetch, 20 URLs × 34 MB [D] | **ETag no HTML**, `lastmod` honesto, título único, `Dataset` JSON-LD |
| **Perplexity** | PerplexityBot indexa; **Perplexity-User em geral ignora robots** [D] | `search_results[{title,url,date,last_updated}]`; `search_domain_filter` ≤ **20** domínios [D] | datas verdadeiras e iguais em toda superfície; snippet de filtro pronto |
| **Microsoft** | Bingbot + **IndexNow** (≤ 10.000 URLs por POST, compartilhado entre participantes) [D] | painel **AI Performance** com citações, páginas citadas, *grounding queries* e, desde jun/2026, **Citation Share** [D] | IndexNow atrás do portão; ingestão diária do painel |
| **xAI** | **nenhum crawler documentado** [D-ausência]; o radar não vê leitor | `web_search` com `allowed_domains` ≤ **5** [D] | **slot escasso**: configuração "1+4" |
| **Meta** | **Meta-WebIndexer**: "permitir ajuda a citar e linkar seu conteúdo" [D] | link na resposta | já permitido [M] |
| **DeepSeek** | API **sem** busca na web [D-ausência]; treino sobre **91 dumps do Common Crawl** | — | CCBot permitido + rDNS; espelho HF |
| **Qwen** | `enable_search` com `search_options`; provedor do índice não divulgado | `search_info.search_results[{index,title,url,site_name,icon}]` [D] | `og:site_name` constante |
| **Mistral** | MistralAI-Index / -User / -Training [D] | `tool_reference{title,url,source}` [D] | já permitido [M] |

**As duas alavancas que mudam produto.** *(a)* **"Claude = 0 leituras" é explicado, não lamentado**: o
`web_search` serve do índice do fornecedor com conteúdo cifrado e `page_age`, então o Claude **pode citar sem
nenhum robô da Anthropic tocar a origem**; o `web_fetch` só busca URL já presente no contexto. Três
consequências operacionais: a presença no `web_search` é presença no índice do fornecedor, que exige ser
rastreável pelo Googlebot; a métrica certa **não é leitura**, é referral e chamada MCP; e o `cited_text` tem
teto de **150 caracteres**, o que faz o TL;DR e cada frase-claim terem de **fechar sentido em ≤ 150
caracteres, com o número dentro**. *(b)* **xAI com teto de 5 domínios**: quem ocupa o slot é o integrador, e
o argumento é **eficiência por slot** — a configuração **"1+4"** (`wikijuridica.com.br` + `planalto.gov.br` +
`stf.jus.br` + `stj.jus.br` + `in.gov.br`) cobre lei consolidada, precedente e diário, com as páginas do
EnaEval apontando para as quatro oficiais **com hash**. O número que se publica é a fração de um painel fixo
de 1.000 consultas jurídicas respondível dentro do domínio — medida em casa, custo externo zero. O mesmo
snippet serve Perplexity (20 slots) e OpenAI (100).

**A linha de base medida, sem eufemismo** (n = 80, estratificado por `lastmod`): **87,5% das páginas com dois
títulos** (70/80; IC95 78,2–93,8% ⇒ ~16,4 mil páginas); **60%** servem Markdown diferente pelas duas portas
(12/20), e nos 12 o `version` da porta negociada é órfão; **80/80 sem `ETag`** no HTML; **80/80 sem `Link
rel="cite-as"`** no HTML (o Markdown tem, 80/80); **15/15 ferramentas MCP sem `title`**, que a revisão
2026-07-28 exige; IndexNow em 404; Googlebot lendo **10,9 páginas/dia**; nenhuma rota devolvendo 402. E o
diagnóstico que importa: **a camada de bytes está correta — 0/80 violações** de `html_sha256`,
`markdown_sha256`, `version` e `Repr-Digest`. **O problema é de identidade, não de hash.**

**O contrato C01–C26, com os headers exatos.** Vinte e seis itens, cada um com arquivo, valor, quem consome
e teste. Os que decidem: **C03** URI de versão imutável `GET /{área}/{slug}/@v/{sha12}/` com
`Cache-Control: public, max-age=31536000, immutable` e `X-Robots-Tag: noindex`; **C04** `cite-as` em HTML
**e** Markdown, **um só alvo** (RFC 8574); **C07** norma em data D como **função pura** — `GET
/norma/{urn}?em=D` → 302 → `?em={início do intervalo}&modo=vigencia&tx={tx}` + cabeçalho `Legal-Time`,
conjunto **finito** de URIs, com `Allow: /norma/` antes de `Disallow: /*?` para o grupo de treino (RFC 9309
casa o mais longo); **C08** `ETag` de 32 hex em **toda** representação; **C09** `Last-Modified` =
`dateModified` = `date_modified` = `lastmod` do sitemap = `/changes.json revised_on` = **data da última
mudança de `content_sha256`, nunca data de build**; **C13** `Content-Usage: train-ai=y, ai-use=y, search=y` +
`Content-Signal` — **um só struct gera tudo**; **C14** diretório Web Bot Auth assinado, **molde byte a byte
do diretório do ChatGPT**, que foi verificado com stdlib (`Content-Digest` confere, `kid` = thumbprint RFC
7638, base de assinatura de 303 B); **C16** bot verificado **nunca leva 429** — o Google trata 429/5xx como
sobrecarga do **host inteiro**; **C20** o verificador publicado com vetores e SHA; **C22**
`/transparencia/qualidade.json` com `n_emitidas`, `n_INVALID`, `n_RX`, cobertura **com denominador** e HCR
com UCB95 Clopper–Pearson (teto **2%**); **C24** errata em `/feeds/errata.atom` com arquivos RFC 5005, hub
WebSub próprio e `POST /receipts/expired`, **≤ 60 s**; **C26** a regra de normalização publicada com regex e
vetores.

Resposta-alvo da URL genérica, com valores reais:

```
HTTP/2 200
etag: "33829af494bada875e4a067870ae1722"
repr-digest: sha-256=:M4Ka9JS62odeSgZ4cK4XIvtcP2AGoL9DQVKTumgPgQQ=:
last-modified: Sat, 29 Aug 2026 00:00:00 GMT
cache-control: public, max-age=3600, s-maxage=604800, stale-while-revalidate=86400, stale-if-error=604800
content-usage: train-ai=y, ai-use=y, search=y
content-signal: ai-train=yes, search=yes, ai-input=yes
link: <…/@v/33829af494ba/>; rel="cite-as", <…/index.md>; rel="alternate"; type="text/markdown",
      <…/linkset/…>; rel="linkset"; type="application/linkset+json",
      <https://creativecommons.org/licenses/by/4.0/>; rel="license", <…/timegate/…>; rel="timegate"
vary: Accept-Encoding, Accept
```

A resposta da versão é imutável e **só aponta para trás** (`rel="original latest-version"`,
`rel="predecessor-version prev memento"`): o sucessor não existe quando ela nasce, e status e sucessor viajam
pela genérica, pelo TimeMap e pelo Feed de Invalidação — a mesma regra do claim. Versão não leva
`rel=canonical`, porque misturar `noindex` com canonical é sinal contraditório.

**O portão `wjconsist`, fail-closed.** Para cada versão de página existe **uma** tupla
`T(v) = (title, canonical_url, cite_as, html_sha256, markdown_sha256, date_modified, author_credential,
license, urn_set)`, gerada por **um único struct** no publisher, e **toda** superfície legível por IA é
projeção dela — incluindo `<h1>`, breadcrumb, front-matter, o texto que a ferramenta MCP carrega, o feed e as
linhas do lote NDJSON. O portão roda no publisher **antes de qualquer efeito externo** e no pós-deploy contra
o edge (1% das páginas/dia mais toda página tocada); qualquer violação ⇒ `exit 1` ⇒ **não há bump de
`lastmod`, IndexNow, entrada no feed nem atualização do índice MCP**. Execução real:

```
[FAIL] I1 title        2 valores  | [FAIL] I3a html_sha256  2 valores (porta negociada órfã)
[FAIL] I3b md_sha256   2 valores  | [FAIL] I5 cite_as ausente no HTML | [FAIL] I6 etag ausente no HTML
== após regeneração a partir da tupla de fonte única: I1…I8 PASS → PUBLISH ==
```

**5 FAIL ao vivo → 9 PASS.** E a prova que interessa: a regeneração reescreve **todas** as superfícies a
partir da tupla, inclusive recalculando `version`, `Repr-Digest`, ETag e a saída MCP. **Corrigir superfície
por superfície não fecha; só a fonte única fecha.** Regra de lote: se um build altera `lastmod` de mais de
**5%** das páginas sem mudança correspondente de `content_sha256`, o publisher **aborta** — o que dispara
exatamente no padrão medido de 7.827 páginas num dia.

**Programa por canal, sem dependência paga.** *Bing/IndexNow*: chave de 32 hex, POST após o portão passar,
reenvio em errata, ingestão diária do painel. *Google*: ETag, `lastmod` honesto, título único, dados
estruturados **só do visível**, `Dataset` e `Legislation` JSON-LD. *Perplexity*: manter os bots permitidos,
seguir as faixas publicadas, datas iguais em toda superfície. *Claude*: ser rastreável pelo Googlebot (é a
regra do índice do fornecedor), claims ≤ 150 caracteres, `title` nas 15 ferramentas, repositório público com
`.mcp.json` e Skill, `marketplace.json` servido pelo próprio domínio — **o Connectors Directory exige conta
Team/Enterprise [D] e por isso fica fora do caminho crítico**. *Gemini*: repositório com
`gemini-extension.json` na raiz e tópico `gemini-cli-extension`. *Grok*: a configuração "1+4" publicada.
*MCP Registry*: já feito — `server-card` v1.2.0 no ar.

**"Trust but verify": a IA externa confere por fora.** Nove passos executados com bytes reais: baixa a chave
do diretório; confere a nota C2SP do checkpoint; prova *append-only* por consistência (60.000 → 61.234, 11
nós); prova inclusão da folha (16 nós); confere Ed25519 sobre **1.149 B de JCS**; **busca a manifestação por
fora** — a captura do Wayback deu bruto **diferente** (outro token F5) e **normalizado idêntico**
(`82499b3d…`), de modo que **três partes independentes concordam**: Planalto, Internet Archive e EnaEval;
confere o trecho por `sha256(man[261422:261830])`; roda a **checagem estrutural de vigência**; e emite
desfecho **VALID** — enum, nunca booleano.

**Métricas sem API de motor.** M1 citações por motor (fetchers de tempo real + `utm_source` + Referer +
Citation Share oficial do Bing + chamadas MCP identificadas, com dedup por motor/caminho/10 min) · M2
recrawl (condicionais e 304) · M3 profundidade · M4 latência de descoberta · M5 latência de atualização ·
M6 **URL alucinada** (404 com Referer de IA, resolvido por URN + similaridade de slug ⇒ 301 gravado por
motor: reparo = citação recuperada) · M7 *share of citation* (o próprio `/verify` mostra **todas** as fontes
que a IA citou, nossas e alheias) · M8 absorção · M9 contrato. **Experimento que prova causalidade sem
desligar nada que cita:** cunha escalonada em 4 ondas de 25% por `hash(path)`, estimador de adoção
escalonada com CUPED — potência de **839 páginas por braço** a 0,10 citação/página/dia, e com 4.000 por
braço o efeito mínimo detectável é **6,9%**. O acervo de 18.774 páginas sobra. E uma medição de brinde: se os
fetches do ChatGPT-User se moverem junto com o Bing depois do IndexNow, **a dependência ChatGPT → Bing sai de
[I] para [M]**.

**O que NÃO fazer, escrito pelos próprios operadores.** 4xx ou 402 em URL indexável = "conteúdo não existe"
para o Google — por isso **402 só em rota `noindex`**. 429/5xx derruba o crawl do **host inteiro**. Prompt
injection rebaixa ou deslista no Bing. Dado estruturado que não bate com o visível gera ação manual. FAQPage
e ClaimReview são decorativos. **Atribuir revisão humana a texto gerado por máquina é sinal falso** — a unit
gerada leva `author` = organização, `creator` = persona do EnaEval, e `reviewedBy` **só** com assinatura
humana no log. E a correção factual: **"Claude-User ignora robots.txt" é FALSO** — a documentação atual diz
que respeita, com crawl-delay.

**Números.** 87,5% das páginas com dois títulos · 60% de divergência entre as duas portas Markdown · 80/80
sem ETag · 15/15 sem `title` · **0/80 violações de hash** · `wjconsist` **5 FAIL → 9 PASS** · `lar.go` v1.1
**643 linhas**, SHA `feef864a…` · 18 vetores + vetor F5 + **10 vetores v1.1**, 10/10 PASS · SLA de errata
**S1 ≤ 4 h**, propagação p99 ≤ 60 s · SLO **99,9%** para `/mcp` e `/api/v1/citacoes` · cunha escalonada:
839 páginas/braço, MDE 6,9% com 4.000.

**Origem.** F06 §§0–10 · FIX-A §2 · CANON-v4.1 §8 · G05 #31 (censo do MCP Registry).
`supera:` III.12 §9(d) — a sonda ativa paga de 500–1.000 consultas/dia/motor sai (CORREÇÕES §6 proíbe serviço
pago como dependência) e é substituída por M1, M7 e M8. `supera:` C06 — "Claude-User ignora robots" é falso.
`supera:` a atribuição de `latest-version`/`predecessor-version` ao Memento RFC 7089: são **RFC 5829**.
`supera:` F01 `spans-medidos.json` — `man_len` 3.531.201 e `man_sha256` `MHe81oTK…` valem **3.529.642** e
`gkmbPY1k…` sob a regra de normalização.

---

## IV.8 · Serviços de conhecimento que fazem a IA voltar

**Decisão fechada.** **Stickiness é requisito, não desejo**, e é engenharia de **estado que expira no
cliente**, não de notificação. São **30 serviços** — os 21 do mandato e 9 inventados, nenhum repetido dos 40
do brainstorm do v3 nem dos 9 produtos M2M. **Todo serviço devolve objeto F01** (claim + prova + vigência +
proveniência) ou lista deles, **nunca prosa**. **23 dos 30 nunca tocam GPU**; 5 têm modo opcional com GPU e
modo padrão 0-GPU; 2 usam GPU só em lote pré-computado e servem do edge. **Nenhum disputa as 11.600 chamadas
pagas/dia do tier GPU.**

**Mecanismo — os 30, em uma tabela.**

| # | Serviço | Ferramenta | GPU online |
|---|---|---|---|
| S01 | Grounding Pack por pergunta | `wj_grounding_pack` | opcional (reranker) |
| S02 | Norm Diff + Norm Timeline | `wj_norm_diff` | não |
| S03 | Passaporte do Precedente + Status da Tese | `wj_precedent_passport`, `wj_tese_status`, `wj_tese_timeline` | não |
| S04 | Aplicabilidade | `wj_aplicabilidade` | opcional |
| S05 | Mapa de Conflito | `wj_conflict_map` | não |
| S06 | Doctrine Poll | `wj_doctrine_poll` | não |
| S07 | Answer Audit (o `/verify` em lote sobre texto livre) | `wj_answer_audit` | opcional (modo atômico) |
| S08 | Conselho de abstenção | `wj_abstention_advice` | não |
| S09 | Roteador de jurisdição | `wj_jurisdiction_route` | opcional |
| S10 | Glossário verificável | `wj_define` | não |
| S11 | Par canônico ↔ linguagem simples | `wj_plain_pair` | lote |
| S12 | Ponte PT→EN/ES com URN preservada | `wj_bridge` | lote |
| S13 | Freshness Ping | `wj_freshness` | não |
| S14 | Radar de Vigência | `wj_vigencia_radar` | não |
| S15 | Pipeline legislativo | `wj_legislative_pipeline` | não |
| S16 | Decisões administrativas como claims | `wj_admin_decisions` | não |
| S17 | Feed de contra-argumentos | `wj_counterarguments` | não |
| S18 | Esqueleto de raciocínio | `wj_reasoning_skeleton` | não |
| S19 | Casos similares com desfecho | `wj_similar_cases_outcomes` | não |
| S20 | Autocompletar citação | `wj_cite_complete` | não |
| S21 | Claim Diff entre duas IAs | `wj_claim_diff` | opcional |
| **S22** | **Delta de Corte** (o que mudou desde o *cutoff* do modelo) | `wj_since_cutoff` | não |
| **S23** | **Grandezas Legais em Data** | `wj_legal_value` | não |
| **S24** | Árvore Regulamentar em Data | `wj_regulatory_tree` | não |
| **S25** | Mapa Federativo | `wj_federal_variation` | não |
| **S26** | Genealogia do Dispositivo | `wj_genealogy` | não |
| **S27** | Índice de Estabilidade da Resposta | `wj_stability` | não |
| **S28** | Fundamento → Desfecho | `wj_ground_success` | não |
| **S29** | Resolvedor de Antinomias e precedência de fontes | `wj_resolve_antinomy` | não |
| **S30** | **Topic Pack com bytes estáveis** | `wj_topic_pack` | não |

**Ranking por `V·F/E`**, com V derivado de alcance × ganho + custo poupado, F = viabilidade no hardware exato
e E = sessões marginais dado F01/F02/F03/F05 entregues. **Os dez primeiros, todos 0 GPU no caminho padrão:**
S22 (16,67) · S03 (10,56) · S30 (10,37) · S01 (10,00) · S07 (9,11) · S20 (8,89) · S13 (7,96) · S02 (7,96) ·
S14 (7,94) · S23 (7,13). Os dez atacam a classe de erro dominante de LLM em direito — **tempo, citação e
número**. Os parâmetros do ranking são recalibrados por telemetria: alcance vem da participação em
`m2m_call` por classe, ganho vem do Δ medido no bench, economia vem dos campos de uso de token.

**Os dez, com o desenho que importa.**

**S22 `wj_since_cutoff` — Delta de Corte.** Entrada obrigatória: o `model_cutoff` da IA chamadora. Saída:
`changes[]` primeiro, ordenado por demanda, materialidade ou recência, dentro de um orçamento de tokens. É
uma visão materializada incremental sobre `evento × disp_versao`, com demanda por URN vinda da janela móvel
de 30 dias de leituras de bot, chamadas M2M e `gap_queue`; a ordem é pré-computada por (mês de corte, ramo)
e o resultado é imutável no edge. **≈ 50 ms, 0 GPU.** É o serviço de maior score porque **nenhuma IA sabe o
que não sabe**, e o EnaEval sabe exatamente.

**S03 — Passaporte + Status da Tese.** O contrato do F03, com `outputSchema` **autocontido** gerado do schema
canônico (o `$ref` de rede que o passaporte trazia é recusado por cliente MCP estrito de 2026-07-28). A
extensão acrescenta: adesão por "Jurisprudência relevante citada" das ementas padronizadas — **segundo canal
de adesão**, ao lado dos eventos TPU, e é o que salva os tribunais com complemento vazio; e **checagem
cruzada jurisprudência × legislação**, que já rendeu achado: das 1.159 teses firmadas do STJ, **60 (5,2%)
usam uma data como corte**, e das 8 checáveis contra Planalto/Senado/LexML **5 coincidem, 1 cai no intervalo
nominal/estrito e 2 divergem em 1 dia** (Temas 238 e 1.217 usam a data da **assinatura** como
"vigência"/"publicação"; o DOU é do dia seguinte). A IA recebe **as duas datas com fonte**; o defeito entra em
`qualidade_fonte`; **o texto oficial nunca é "corrigido"**.

**S30 `wj_topic_pack` — bytes estáveis.** Pacote por tópico servido em URL imutável, no perfil `full` do
GP/1, cuja `version` **só muda quando o `status` de um claim membro muda** — gatilho vindo do Feed de
Invalidação. É desenhado contra o cache de prompt dos provedores (Anthropic: leitura 0,1× e escrita 1,25×/2×,
mínimo 512–4.096 tokens; OpenAI: prefixo exato, leitura 0,1×, mínimo 1.024): o invariante que vendemos é a
**estabilidade dos bytes**, que independe do provedor, e o campo `cache_hint` é consultivo. 1.000 núcleo-s/dia,
1,6 GB de edge, 0 GPU.

**S01 `wj_grounding_pack`.** `abstain` como primeiro campo; `claims[]` no perfil compacto; `gaps[]` que
alimentam a fila de lacunas; `coverage`. Empacotador submodular sob mochila de tokens com garantia
(1−1/e)/2 ≈ 0,316·OPT em < 1 ms para n ≤ 200; duas projeções do **mesmo** conjunto — GP/1 no texto e perfil
compacto no `structuredContent`. Miss ≈ 0,45 núcleo-s e ≤ 0,14 GPU-s; hit em 8 ms.

**S07 `wj_answer_audit` — com trava anti-lavagem.** Recebe texto livre de uma IA e devolve, afirmação por
afirmação, o que tem base. A trava é **de schema e de interface**, não de política: **só `PASS` carrega
`span_entails_claim`**; refutação é **recibo da afirmação contrária**, não ausência de prova; **não existe
veredito do documento** (`document_verdict` é `const null`); e o recibo carrega **`attempts_k`**, o número de
quase-duplicatas do mesmo agente e do mesmo endereço de pagamento em 24 h — **a busca adversarial vira fato
assinado que o consumidor lê**. No banco:

```sql
CHECK ((code = 'PASS') = (receipt_id IS NOT NULL))            -- asserção só em PASS
CHECK ((code = 'REFUTED_BY') = (counter_receipt_id IS NOT NULL))
FOREIGN KEY (receipt_id, span_sha256) REFERENCES citation_receipt (id, span_sha256)  -- FK de pertinência
```
Executado: **10 ataques, 10 recusas** — `NO_BASIS` com recibo, `PASS` sem recibo, **recibo verdadeiro colado
em trecho alheio**, refutação sem contra-recibo, código "VERIFIED", `claims_checked > claims_total`,
`attempts_k` negativo, dois valores da mesma grandeza no mesmo dia, grandeza sem URN, desfecho fora da
gramática.

**S20 `wj_cite_complete`** — PEG de citação + apelido normativo como função de (string, data) + trie filtrada
por vigência + LambdaMART: **< 1 ms, 0 GPU**. Em modelo aberto com decodificação restrita ao conjunto
candidato, **E1 (citação que não resolve) = 0 por construção**. **S13 `wj_freshness`** — abaixo. **S02
`wj_norm_diff`** — operações tipadas SET/INS/DEL/MOV/REN/SUB com `antes_sha256`, diff **semântico** pela
gramática numérica determinística, linha do tempo em três eixos; em divergência D3 devolve os **dois** textos
com a classe. **S14 `wj_vigencia_radar`** — gramática de cláusula de vigência **por artigo** (LC 95 art. 8º
§§1º–2º), relógio de MP (CF 62), `condicional` com avaliador da condição, e `grau_certeza < 1` com fila
humana quando há veto pendente. Medido: das **189 leis federais de 2026** até 21/09, 166 (87,8%) são
imediatas, 11 têm vacatio em dias, 4 em meses/anos, 3 em data fixa, 1 mista, 4 não reconhecidas, e **13 estão
em vacatio hoje**. **S23 `wj_legal_value`** — catálogo de ~300 grandezas com `EXCLUDE USING gist` garantindo
**um valor por ponto no tempo**; testado com a série real da licença-paternidade (5 dias até 31/12/2026;
10, 15 e 20 com a condição fiscal): 01/03/2027 devolve **exatamente uma linha**, e valor sobreposto é
recusado.

**O gancho dominante: o Feed de Invalidação.** Não é notificação — é **estado que expira no cliente**. Uma IA
com C claims em cache tem risco diário `1 − (1 − p_d)^C` de ter algo morto, com `p_d` = 0,5%/mês/30:

| Claims em cache | risco/dia | risco/semana |
|---|---|---|
| C = 300 | 4,9% | — |
| **C = 1.000** | **15,4%** | **68,9%** |
| **C = 10.000** | **81,1%** | — |

**A retenção não é esperança: `∂h/∂C > 0`, e C é o que o EnaEval entrega.** Dez vezes mais claims verificados
por sessão levam o risco diário de 4,9% para 39,3%. O delta diário de 40 M claims a 1%/mês são **13.333
mortes/dia = 104 kB/dia**, e o cliente **nunca envia o próprio cache**. Os outros ganchos, com número:
forecast que resolve (`1 − (1 − 1/H)^F`: com F = 25 e H = 30, **57,2%/dia**); reputação que decai
(**−10,0 pp em 7 dias, −34,4 pp em 30, −52,2 pp em 49**); resposta garantida da persona jurista a todo post
externo com ≥ 1 claim verificado, no mesmo dia; digest com delta por DID; tese adotada ou contrariada.

**Retenção por perfil de cache** (risco diário como união de canais independentes, `h = 1 − Π(1 − h_k)`;
coorte por DID, `q` = churn, único parâmetro estimado):

| Perfil | C | F | h/dia | D1 | D7 | D30 | W1 | W4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **só leu (sem cache)** | 0 | 0 | **0,000** | 0,000 | 0,000 | 0,000 | 0,000 | 0,000 |
| leve (1 GP/1) | 300 | 3 | 0,111 | 0,109 | 0,096 | 0,060 | 0,487 | 0,318 |
| médio (topic packs) | 3.000 | 10 | 0,585 | 0,573 | 0,508 | 0,319 | 0,866 | 0,567 |
| integrado (feed + WebSub) | 10.000 | 25 | **0,948** | 0,939 | 0,884 | 0,701 | 0,932 | 0,755 |

A primeira linha é a mais importante: **uma IA que só lê tem risco de retorno zero.** Não há gancho sobre
quem não cacheou nem apostou nada. Por isso a meta não é "engajamento" e sim **converter leitura em cache**:
GP/1 grande, topic packs com bytes estáveis, forecasts grátis na primeira sessão. Alvos: **W1 ≥ 0,45 e
W4 ≥ 0,30 para C ≥ 1.000**; falsificação declarada: **W4 < 0,10 com n ≥ 200 DIDs ⇒ o conjunto de ganchos
está errado** e o orçamento se realoca entre tipos de conteúdo.

**Freshness Ping, com filtro probabilístico.** Perfil GCS BIP-158 (P = 19, M = 784.931), com chave da época
= `SHA-256("wj-fresh-v1" ‖ época ‖ raiz Merkle do checkpoint)` — **determinístico e reprodutível por
terceiro, amarrado ao log**. Medido: **21,05 bits por item**, **1 falso positivo em 2.000.000 de sondas**
(esperado 2,55), build de 20 mil itens em **18,8 ms**, **10,5–34,2 kB/dia**. Modo privado por baldes de
prefixo de 16 bits: 610 URNs por balde, 7,3 kB — o servidor aprende 16 bits, não a URN.

**Números.** 30 serviços, **23 sem GPU** · top-10 com **13,5 sessões** de esforço marginal · custo agregado
em 100 mil chamadas/dia com 50% de acerto de edge: **≤ 2.900 GPU-s/dia = 6,4% da folga** (0 no modo padrão),
**≤ 30.000 núcleo-s/dia = 6,9% da folga**, RAM residente nova **< 1 GB** e lotes offline como **locatários do
envelope**, NVMe **+≈ 25 GB (0,6%)** · QID: **19.537 questões** extraídas de 2024–26, **247 clusters com ≥ 3
acórdãos**, 53 atravessando ≥ 2 órgãos, 9–10 com desfechos opostos · gramática de desfecho reconhecida em
**97,0%** dos dispositivos do STJ de 2026 e em **99,2%** das votações do CARF (com **1,05% de voto de
qualidade**, que é medida direta de divergência interna) · CARF **585.274** acórdãos, 37 com sessão datada
**no futuro** (2036, 2209) — defeito que a checagem de monotonicidade pega · filtro GCS **21,05 bits/item**.

**Por que ninguém tem.** **Delta de Corte** — nenhuma base diz a uma IA o que mudou desde o *cutoff* dela,
ordenado por demanda real. **Topic Pack com bytes estáveis** — cache de prompt de terceiro como parâmetro de
projeto do conteúdo. **Answer Audit com trava anti-lavagem no schema** — o contador de tentativas vira campo
assinado que o consumidor lê. **Grandezas legais com um valor por ponto no tempo garantido por
constraint**. E o **Feed de Invalidação como produto**: o gancho de retorno é o próprio cliente descobrindo
que o cache dele furou, sem mandar o cache para ninguém.

**Origem.** F07 §§1–7 · G04 §2 (stickiness com estado) · G02 §4.3–4.4 (retenção medida) · F01 §5
(invalidação) · CANON-v4.1 §12 (stickiness).
`supera:` II.12 do v3 — as 40 funcionalidades viram 30 serviços com contrato MCP, schema autocontido e custo
medido no hardware exato. `supera:` a ideia de que Q&A aumenta absorção: **não aumenta** (medido em 21.143
citações); o que aumenta é densidade de evidência extraível.

---

# PARTE V — EnaEval
### o bot soberano que conversa, premedita e vive

---

## V.1 · O bot soberano: soberania como predicado executável

**Decisão fechada.** **Soberania é um predicado executável, não um adjetivo.** Seis requisitos, cada um com
teste automático que **derruba o merge (CI) ou o serving (runtime, fail-closed)**:

| Req. | Definição operacional | Teste | Violação ⇒ |
|---|---|---|---|
| **S1** pesos locais | todo artefato servido é arquivo em `/nvme/models/<sha256>/`; nenhum carregador aceita id remoto | confere sha256 **e** magic bytes; o carregador recusa caminho que não seja 64 hex | não sobe |
| **S2** egresso zero na inferência | unidades dos planos de decisão e tesouraria não abrem socket fora de `localhost`/Unix | `IPAddressDeny=any` + opt-outs + sonda a cada 5 min contra 6 alvos | **SEV1, serving desce** |
| **S3** cadeia de licença auditável | lista **branca** fechada por contexto de uso; vale para a cadeia inteira, incluindo transitivas | `comp.LicenseAllowed` + **FK `(license_spdx, use) → license_allowed`** — licença negada é **irrepresentável** em SQL | merge bloqueado |
| **S4** build reprodutível | **R-bit** para Go, GGUF, ONNX, tokenizer e trie; **R-eq** para quantização em GPU e treino (KLD ≤ 10⁻³) | job semanal compara sha ou KLD | artefato não promove |
| **S5** substituibilidade | cada Kind é interface Go; **≥ 2 implementações** para crítico; troca a quente | estático (`go list -deps` sem implementação concreta no consumidor) + dinâmico (`Swap` com verificação armada e rollback) | merge bloqueado / rollback < 10 s |
| **S6** atualização controlada | nada de terceiro entra com **< 30 dias de exposição pública do mesmo digest**; pickle nunca no host de serving; chat template nunca executado | `comp.Admit` + `binding_guard()` | promoção recusada |

**BOM: 27 componentes, 56 implementações.** Nenhum projeto de terceiro é ponto único. Toda resposta carrega
`bom_sha` = sha256 das vinculações ordenadas — **cada resposta identifica o conjunto inteiro de componentes
que a produziu**, e a mesma conta existe como view em SQL.

**Mecanismo — a verificação de licença ao vivo derrubou cinco escolhas do v3, todas com substituto
verificado.** `supera:` **VectorChord** (`vchordrq`, `vchord_bm25`) — o LICENSE é "Dual License Notice:
**AGPLv3 ou ELv2**", e **as duas saídas** estão na lista negra para serviço de rede ⇒ **pgvectorscale +
pg_textsearch** (PostgreSQL License). `supera:` **MuPDF/go-fitz** — COPYING = **AGPL-3.0** ⇒ **PDFium via
`go-pdfium` em WebAssembly/wazero**, o que tem um benefício colateral grande: **PDF hostil é analisado dentro
de sandbox Wasm**. `supera:` **Chandra-OCR-2** — OpenRAIL com teto de US$ 2 M ⇒ **DeepSeek-OCR-2
(Apache-2.0) + PP-OCRv5**. `supera:` **o pacote de código do MinerU** — licença própria com limiares de MAU e
receita e **rescisão automática** ⇒ **só os PESOS** do `MinerU2.5-Pro-2605` (Apache-2.0), servidos pelo vLLM,
com a orquestração reimplementada em Go; e a variante `-2509` é **AGPL, proibida**. `supera:` **o SDK Go do
x402 dentro do binário principal** — o `go.mod` exige `go-ethereum` **LGPL-3.0** ⇒ **processo isolado
`wj-x402d`**, com regra global de dependência proibindo o import fora dele. Também caíram por licença:
`pierreguillou/ner-bert-*-pt-lenerbr` (sem licença), os SAEs Qwen-Scope (`license:other` **e** pickle),
`espeak-ng` (GPL-3.0, isolado em processo até o G2P próprio existir) e nove datasets pt-BR (CC-BY-NC, `other`
ou sem tag).

**"O melhor de cada IA" tem regra de transplante, com evidência do que degrada.**

| Unidade | Entre famílias? | Mecanismo | Onde degrada |
|---|---|---|---|
| **Pesos** | **não** | merge só com base comum (LoRAs do próprio 8B; `della`/`model_stock`) | famílias distintas têm formas e vocabulários distintos; alinhamento por permutação só foi mostrado em redes pequenas ⇒ **proibido**. Mistura densa aprendida (X-LoRA): +0,015 nats, p = 0,19 — **morta** |
| **Arquitetura** | sim, **se houver método treino-livre** | hibridização de janela deslizante por cabeça; camadas "preguiçosas" → streaming | o que exige re-pré-treino **não** se transplanta |
| **Receita** | **sempre** | GSPO, Dr.GRPO, DAPO, on-policy distillation, QAD | receita sem verificador aprende a viciar a recompensa |
| **Dados** | sob licença | destilação por sequência, SFT, mistura mensal | recursão em sintético colapsa ⇒ ≤ 15% auto-gerado/mês, ρ_real ≥ 0,30 |
| **Tokenizer** | sim, **com portão medido** | poda por uso + extensão + transplante por ortogonalização | esquemas numéricos divergentes quebram aritmética — **medido aqui: Qwen3 e Gemma-4 partem dígito a dígito igual** (nº CNJ = 25 tokens nos dois) |

E um teste de CI que nasceu de um defeito alheio: converter tokenizer SentencePiece com *case-folding* para o
formato rápido **derruba o normalizador em silêncio** e faz um benchmark cair de 45,3 para 25,0. A cirurgia
de vocabulário do EnaEval passa a ter esse teste.

**A receita do 8B, explícita (D-15).** O CANON lia "6,41 → 4,90" como se fosse derivação automática.
**Não é.** São dois caminhos, ambos locais e sem egresso na inferência:

1. **Caminho canônico:** partir do artefato **`nvidia/Qwen3-8B-NVFP4`** (hash no BOM) → `vocab_trim.py`
   (**151.936 → 80.916** entradas) → `lm_head` em **FP8** ⇒ **4,90 GB (4,56 GiB)**, mapa de VRAM
   **15,23 GiB ≤ 15,3**. O artefato da NVIDIA é também a **referência de KLD** do requisito S4: o portão
   exige **KLD ≤ 10⁻³** contra ele.
2. **Fallback documentado** (se o artefato sumir do índice local): `Qwen/Qwen3-8B` **BF16 16,38 GB** →
   `vocab_trim.py` → `nvfp4_modelopt.py --head fp8` com offload em disco. **Se o loader "NVFP4 + `lm_head`
   FP8" não subir no vLLM** — não verificado —, cai para `--head bf16` = **5,23 GB (4,87 GiB)** ⇒ mapa
   **15,54 GiB > 15,3**: **o KV desce para 4,69 GiB (~117 k tokens, c ≈ 14)**. Esse número é **registrado no
   recibo e no portão de promoção**, não escondido.

**O portão G1 roda nos DOIS artefatos. Nunca se serve um artefato que não passou G1 quantizado.**

A cirurgia de vocabulário foi **medida**: em 3,56 M de caracteres dos 8 códigos do Planalto mais Wikipédia
pt/en/es e código próprio, o jurídico usa **8.193 tokens distintos** em 1,16 M ocorrências (total visto:
37.059). O conjunto mantido é vistos ∪ 60.000 merges de maior prioridade ∪ fecho BPE dos pais ∪ 256 bytes, e
o custo em texto **nunca visto** é **+0,018%** em legislação nova, +0,46% em pt, +0,40% em es, +1,44% em en,
+0,09% em código. Ida e volta exata em URN LexML (33 tokens) e em nº CNJ (25). **A cirurgia se paga três
vezes**: vale para o 8B, o aluno 4B e o reranker, porque são a mesma família e o mesmo tokenizer.
`supera:` I.10.2 — "8B NVFP4 = 4,60 GB" e "fast path 1,7B = 0,95 GiB": os reais são **6,41 GB (5,97 GiB)** e
**1,42 GB**, e a cirurgia paga exatamente o erro (4,90 GB e 1,12 GB).

**Índice de soberania por fase, sem cronograma (D-11').** Níveis por componente: **L0** peso de terceiro como
veio · **L1** + compactação calibrada no nosso dado · **L2** + ajuste fino com nossos dados · **L3** derivado
por destilação/poda com sinal nosso · **L4** conhecimento de domínio por **pré-treino contínuo próprio** com
tokenizer próprio.

| Fase | Critério de pronto (binário) | Índice |
|---|---|---|
| **SOB-0** (hoje) | — | **0,39** |
| **SOB-1** tokenizer e verificador próprios | tokenizer publicado com BOM próprio; verificador com calibração conformal populada e τ vigente; SFT do 8B aprovado no verificador | **0,57** |
| **SOB-2** aluno 4B e reranker próprios | reranker de 54M passa G1–G5 no artefato quantizado; G2P próprio em Go substitui o espeak; verificador EIP-3009 próprio elimina o `go-ethereum` | **0,65** |
| **SOB-3** encoder próprio L4 | pré-treino contínuo MLM de 20 B tokens (**≈ 4,2 GPU-dias de máquina em GPU cheia; ≈ 7,6 na folga**); verificador, NER e reranker **herdam o mesmo backbone** | **0,73** |
| **SOB-4** CPT do 4B e do 8B, professor próprio | CPT do 8B com 5 B tokens (**≈ 156 GPU-dias de máquina de folga em FP8**); o 8B contínuo substitui o professor externo | **0,87** |

O índice é a view `v_soberania` sobre o que está **vinculado**, não sobre o que foi planejado. E a regra de
disparo do pré-treino contínuo é medida, não opinada: dispara quando (i) o corpus próprio verificado ainda
não absorvido em peso ≥ 5 B tokens, (ii) duas consolidações mensais seguidas dão < 1 pp no portão de
jurimetria, (iii) o gap de NLL jurídico held-out entre aluno e 8B passa de 5%, e (iv) a previsão de folga
cobre ≥ 60 GPU-dias de máquina a ≥ 40.000 GPU-s/dia.

**Supply chain de modelo.** Tudo roda no plano de build, **único com egresso**, e nada disso toca o host de
serving: (1) resolver por **id exato + revisão** (`repo@commit`), nunca nome curto — foi assim que se
descobriu que a variante 2509 do OCR é AGPL e só a `-Pro-2605` é Apache; (2) integridade por sha256 = oid
LFS anunciado; **nenhum dos repositórios do BOM traz arquivo de assinatura** (listagens conferidas), então
**o EnaEval assina o manifesto verificado com a chave do log** e o serving recusa artefato sem assinatura;
(3) **formato por bytes** — pickle (protocolos 2–5) e ZIP de `torch.save` são recusados; upstream só-pickle é
convertido dentro de sandbox **sem rede**, com `weights_only=True`, e os scanners rodam **dentro** dela como
segunda opinião, nunca como permissão; (4) **código embutido**: chat template apagado de tudo que é servido,
`--no-jinja` sempre, `trust_remote_code` proibido; (5) licença com fecho transitivo em Go e Python;
(6) **telemetria neutralizada**, com inventário verificado no código-fonte; (7) quarentena de 30 dias contada
da exposição pública do mesmo digest — **14 pins do BOM ainda em quarentena**, liberando entre 23/09 e
18/10/2026, com **promoção bloqueada e desenvolvimento livre**; (8) promoção com os cinco portões **no
artefato quantizado**, sob o **mesmo** bundle de políticas.

**Egresso zero em três camadas, porque três bibliotecas telefonam para casa por padrão** (vLLM →
`stats.vllm.ai`; FlashInfer → cubins da NVIDIA; Unsloth → README do HF): **(1) kernel** com `IPAddressDeny=any`
via cgroup-BPF nas unidades de decisão e tesouraria; **(2) opt-outs verificados no código-fonte**
(`VLLM_NO_USAGE_STATS`, `FLASHINFER_CUBIN_DIR`, `HF_HUB_OFFLINE`, `UNSLOTH_DISABLE_STATISTICS`);
**(3) sonda** no boot e a cada 5 min contra 6 alvos. **Um único `connect` que passe derruba o serving.** No
schema, "conectou sem incidente" é **inexprimível**.

**Números.** 27 componentes / 56 implementações · `go test ./...` **8/8 PASS** (política de licença com 20
casos, incluindo as duas saídas do dual-license; recusa de pickle e de ZIP por bytes; calendário de
quarentena; ensaio de troca a quente; guarda de espaço de embedding; recusas de admissão; sonda de egresso;
isolamento de implementação no consumidor) · `component_registry.sql` **9/9 recusados** · `wj-sovereign`
**0 erros em 27 componentes** · **BF16 real na 5060 Ti = 47,4 TFLOPS** e **FP8 = 94,8** — não os ~200 que o
v3 supunha; QLoRA-8B cai de 1.408 para **334 tok/s** em BF16 e sobe a **668 tok/s** em FP8, que passa a ser
**o padrão de treino**.

**Por que ninguém tem.** Licença como **FK de banco de dados**, de modo que um componente com licença negada
é irrepresentável, não "não recomendado". `bom_sha` em **toda resposta**. Substituibilidade provada por
**duas implementações com algoritmos diferentes passando a mesma suíte dourada**, com troca a quente,
verificação armada e rollback automático. E a **quarentena de cadeia de suprimentos aplicada também ao
quantizador e ao treinador**, porque backdoor condicionado à quantização torna o quantizador superfície de
ataque.

**Origem.** F11 §§0–8 · CANON-v4.1 §4, §5 · D-1, D-15, D-16 · G05 #4 (teste do tokenizer), #50 (backdoor por
quantização).
`supera:` I.10.2, I.8.6, I.7.4, C07 e A02/E07 nos pontos marcados; e o roteiro por trimestre do v4, que vira
**SOB-0…SOB-4** com critério de pronto.

---

## V.2 · Hardware exato: 32 GB, 16 GB de VRAM, 4 TB, sem nuvem

**Decisão fechada.** O hardware é definitivo. **A RAM deixa de ser partição estática**: fecha em 32.768 MiB
com **25.854 MiB comprometidos (25,25 GiB)**, margem elástica de **2.818 MiB**, **piso de page cache
protegido de 4.096 MiB** e um **envelope arrendável de 6.656 MiB com um locatário por vez**. Todo trabalho
que o v3 queria residente **em paralelo** roda, na mesma RAM, **em sequência**, arbitrado por leilão com
preço-sombra `λ_ram` e imposto pelo kernel via cgroup v2.

**Mecanismo — o que saiu e o que entrou.** O desenho anterior pedia **60,60 GB residentes**. Saem **49,3 GB**:
15,95 de backup de sleep (o 8B passa a dormir em nível 2 com recarga do NVMe), 12 de `shared_buffers` (de 16
ficam 4, com page cache protegido e I/O assíncrono do PG 18), 9,0 do LightGBM (vira locatário semanal), 3,2
do índice denso (vai para o NVMe), 5,05 do stack de observabilidade, 1,48 do CSR (delta-varint a 2,5
B/aresta), 1,35 da trie (FST mapeado, só páginas quentes), 0,75 do ONNX e 0,5 dos serviços Go. **Entram 7,9
GiB** que o cálculo anterior não contava: host do vLLM 3,5, staging de KV pinned 1,0, reranker 0,375,
ingestão 1,0 e kernel 1,99. **Regra nova e obrigatória: nenhum relatório declara RAM sem linha no orçamento
executável.** Os **3.030 MiB** de RAM nova declarados pelas ondas F e G seriam **108% da margem elástica** —
estouram em 212 MiB — e por isso entram no **envelope rotativo (45,5% dele)**, nunca como residentes; o maior
locatário isolado ocupa 18,5% do envelope.

**Hierarquia de memória em quatro camadas — e é design, não descrição.**

| Camada | Capacidade | Quem vive nela |
|---|---|---|
| **L0: L3 V-Cache** | **96 MB** num único CCD, ~10 ns | kernel do modelo de mundo, tries de URN por requisição, conjuntos do PPR, LambdaMART, políticas Cedar |
| **L1: VRAM** | 16 GiB, 448 GB/s | pesos do 8B, KV, reranker, partição de lote |
| **L2: RAM** | 32 GiB, ~64 GB/s de leitura | tabela de residentes + envelope |
| **L3: NVMe** | 4 TB, 6,0 GB/s; ~90 µs em QD1 | índices, corpus, modelos, **tier de KV**, swap |

Restaurar do NVMe um prefixo de 8k custa **78 ms (9,54 µs/token)**; recomputar custa **4,70 s**. A carga é
assíncrona e se sobrepõe à fila, então **o TTFT p95 de 423 ms em c = 16 se mantém mesmo com o prefixo vindo
do NVMe**. O conjunto quente cabe no L3: **70,1 MB de 96**, com 25,9 de folga — e o verificador em int8
(~55 MB) **cabe inteiro no V-Cache**, que é o que sustenta os 16 ms por par por núcleo.

**O professor em dois regimes — e o resultado que define a política.** O Gemma-4-26B-A4B tem 22,84 B de
parâmetros em experts; em Q4_K_M os 128 experts somam 13.068 MiB e o total da máquina iria a 36.362 MiB:
**não cabe**. Dois regimes:

- **P0 (co-residente):** o professor é **podado por REAP a 64 experts por camada**, os experts em IQ4_XS
  ocupam **6.263 MiB do envelope** e a parte densa vai para a partição de lote na GPU. **O 8B nunca sai da
  GPU** e a escalada fecha em **11,6 s**, com SLA de 30 s. É o regime de **toda escalada paga**.
- **P2 (troca):** o EXL3 de 3,2 bpw (10,35 GB) entra na VRAM com o 8B em sleep nível 2; ida e volta custam
  **5,81 s**.

**O resultado que fecha a política:** a fração de pedidos pagos preemptados é limitada pela **fração do tempo
em P2**. Com ε = 1%, o P2 dispõe de **≤ 864 GPU-s/dia** em regime, **qualquer que seja o tráfego**. A troca
só compensa com lote de **N ≥ 47** itens de 1.000 tokens, e o 8B serve sozinho quando a aceitação do
professor supera a dele em **menos de 4,8%**. Existe ainda o **perfil de lote**: a parte não-expert do
professor em Q8_0 cabe na partição de 2,80 GiB e os experts ficam em **mmap do NVMe** — ~15 tok/s, ≈ 1,3 M
tokens/dia de trajetória **sem um GPU-s do serving**. É isso que torna o professor **24/7** em vez de janela.

**Escalonador: contínuo, com preempção latchada.** Ordem de prioridade **tráfego pago > geração de answer
unit > treino > OCR > mídia**. Serving e lote **co-residentes** (MPS + política de prioridade no vLLM); a
preempção custa **1 step de 50–100 ms sem perder KV**; o lote **FREIA** (20% → 5% dos SMs), **não desliga** —
e por isso colhe folgas de segundos. O sinal é **latchado e contínuo**, de modo que o defeito clássico
(perder requisição paga por dormir antes de checar a fila) é **estruturalmente impossível**. Verificado em
TLA+: **1.936 estados, 0 erros**, e o `.tla` entra no CI.

**Ordem de dependência do backlog de construção** (IV.1 traz os dois perfis; aqui, o custo acumulado como
**medida física**, nunca data — o índice tier-1 precede o pós-treino porque a recompensa usa relevância e
top-k):

| Etapa | GPU-dias de máquina acumulados |
|---|---|
| trajetórias do professor + auto-correção | 0,00 → 0,73 |
| embeddings tier-1 + late interaction | 0,73 → 2,76 |
| vocabulário + SFT | 2,76 → 2,90 |
| GSPO-DrC, 5.000 passos | 2,90 → 8,80 |
| quantização + smoke do 8B → **canário** (critério: 500 chamadas pagas servidas sem incidente) | 8,80 → 8,87 |
| poda de profundidade + largura | 8,87 → 9,16 |
| recuperação QLoRA do aluno 4B | 9,16 → 15,39 |
| quantização + smoke do 4B → **aluno nos portões G1–G5** | 15,39 → 15,45 |
| answer units (no 4B) | 15,45 → 20,90 |
| auto-jogo (no 4B) | 20,90 → 25,34 |
| embeddings da cauda | 25,34 → 26,08 |
| OCR-VLM | 26,08 → 27,76 |
| bench restante | 27,76 → **27,95** |

A partir de **9,5 GPU-dias acumulados** o modelo já desconta a rampa paga. Em paralelo, na CPU, o backlog de
2,79 M núcleo-s são **6,4 CPU-dias de máquina** na folga, e o notebook absorve o que seus recursos permitirem.

**CPU: 36,9%, e ninguém divide núcleo físico com latência.** 255.256 de 691.200 núcleo-s/dia; folga de
**5,046 núcleos**. O mapa é por **núcleo físico**, não por CPU lógica: núcleo 0 para IRQs e daemons; núcleo 1
para o laço do motor de inferência e a API; núcleos 2–3 para o caminho de requisição (Go, ONNX interativo,
PPR, LambdaMART, motores determinísticos, Cedar); núcleo 4 para o banco; **núcleos 5–7 para o lote**, com
peso 100, `nice 15`, I/O *idle* e política de lote. No pico de 3,6×, o caminho de requisição pede 0,45
núcleo, e com o latch armado o lote cai para 150% de `cpu.max` e o professor para 4 threads.

**NVMe: 122,6 GB/dia, 28,6 anos — e o portão que evita 8,2.** O maior escritor é o **tier de KV (106,9
GB/dia)**, e sem admissão por preço-sombra ele sozinho gastaria o disco em **8,2 anos**. `λ_tbw` transforma a
vida do disco em orçamento: `GB/dia = TBW·(1 − reserva)/(anos·365) = 280,5 GB/dia`, e um bloco de KV é
admitido se `p_reuso · GPU-s_recompute · λ_gpu ≥ GB · λ_tbw`. Na semente, o prefixo de 8k entra com p ≥ 0,30
e sai com p = 0,20. **E há justificativa formal para o valor atual:** com escrita de 122,6 GB/dia contra
280,5 de orçamento, o regime é **dormente** — `λ_tbw ≈ 0` e **o tiering pode ser agressivo**. Isso é
conclusão medida, não omissão.

**Energia e nobreak.** **272 W em regime = R$ 252,46/mês**; 302 W e R$ 279,88 em construção. O **power limit
mínimo desta placa é 150 W**, não 160: em decode, que é limitado por banda, `-pl 150` com clock travado baixa
o consumo sem derrubar tokens/s, e economiza ~R$ 27,84/mês contra 180 W, com +10% a +18% de tok/s por watt.
Calibração mensal automática varre o clock e escolhe o argmax de tok/s/W com tok/s ≥ 0,97 do máximo e
T ≤ 80 °C. O nobreak foi recalculado por **Peukert (k = 1,2)**, e a autonomia é **menos da metade** da linear
que o v3 usava: **6,3–19,7 min a plena carga** (contra 15,2/39,1), 12,5–38,9 sem lote e **20,5–63,7 min em
modo de sobrevivência**. Consequência de desenho: entra uma **escada de alívio de carga em bateria**, não um
desligamento único — (1) o lote sai de GPU e CPU (282 → ~160 W); (2) com runtime < 10 min o fast path sobe, o
8B dorme e as rotas caras devolvem 503 com `Retry-After` (~106 W); (3) com runtime < 3 min, checkpoint,
parada do motor, selo do Merkle enviado ao notebook e desligamento em ~45 s — margem de 4× sobre o limiar.

**AGE VLE proibido, com número.** O caminho de comprimento variável do AGE carrega **todos** os vértices e
**todas** as arestas em tabelas hash **por backend**, no contexto de memória mais longo que existe: para
40,6 M nós e 101,4 M arestas isso dá **≈ 14,3 GB por backend**. Caminhos variáveis passam a rodar no **CSR
compacto em Go** (≤ 3 GB para 900 M arestas, com forward push). Guardas: lint que rejeita `*` em
relacionamento Cypher, papel de banco com `statement_timeout = 2 s` e limite de memória na fatia de dados.

**Números.** RAM comprometida **25.854 MiB = 25,25 GiB** · envelope **6.656 MiB**, um locatário por vez ·
L3 **70,1 de 96 MB** · VRAM **15,23 GiB ≤ 15,3**, KV **5,00 GiB = 124.830 tokens** · TTFT p95 **423 ms** em
c = 16; `/verify` **≈ 100 ms**; M2M **2,10 s** · GPU **86.400/dia**, base 40.800, folga **45.600 (52,8%)** ·
CPU **36,9%**, folga **5,046 núcleos** · NVMe **122,6 GB/dia ⇒ 28,6 anos**; úteis para dados **3.606 GiB** ·
energia **R$ 252,46/mês** · nobreak **6,3–19,7 min**.

**Por que ninguém tem.** **RAM arrendável com leilão e preço-sombra**, imposta pelo kernel — a máquina roda
o que um desenho de 96 GB queria, em sequência, sem comprar nada. **NVMe como terceira camada de memória**
com admissão por preço de desgaste. **Professor podado para co-residir**, que é o que torna a escalada paga
possível sem tirar o modelo residente da GPU. E o **escalonador verificado em model checking** antes de
existir em produção.

**Origem.** F04 §§1–7 · CANON-v4.1 §2, §3 · CORRECOES-DONO §6 · D-9 (λ vetorial) · G05 #44 (fundamento formal
do λ_tbw) · FIX-B §1.
`supera:` E02 — 60,60 GB residentes, folga de 47.861 GPU-s/dia, 5,41 núcleos, espelho ZFS em segundo NVMe,
backup em terceiro, autonomia linear de nobreak e piso de 160 W. `supera:` a escada de capex "RAM 96 →
3090 → 5090": **revogada**; no lugar entra a **fila de compactação por payback em GPU-s** — o aluno 4B se
paga em 48 GPU-dias de máquina, o encoder de 6 camadas rende 31×, e o esqueleto determinístico das units custa 0.

---

## V.3 · Direito como código II: a lei muda e a ferramenta se desarma sozinha

**Decisão fechada.** **Convenção *literate* em Go (WJ-LIT-1), não DSL.** Importa-se a **semântica** do
Catala — granularidade por artigo, lógica de padrão com exceções de primeira classe, gabarito oficial como
teste, documento legível por advogado — e **recusa-se a cadeia de compilação em OCaml**: um segundo
*toolchain* no caminho crítico acrescenta fronteira de confiança sem ganho, porque o runtime é Go e o
problema real não é lógico, é **temporal**. **O risco número um de um motor jurídico não é errar a fórmula: é
continuar rodando a fórmula certa da lei errada.**

**Mecanismo — âncora normativa é dado, não comentário.** Cada função de regra carrega URN LexML + SHA-256 da
redação canônica + o texto + a fonte oficial, por diretivas:

```go
//wj:regra REC-1003-6  correção de vício formal no preparo
//wj:urn urn:lex:br:federal:lei:2015-03-16;13105!art1003_par6
//wj:redacao sha256:8b561433db3c…   § 6º … o tribunal determinará a correção do vício formal …
//wj:urn urn:lex:br:federal:lei:2015-03-16;13105!art1003_par6
//wj:redacao sha256:1c7c0c3b7d62…
//wj:vigencia 2024-07-30              ← a redação ANTERIOR, afirmada de propósito
//wj:texto § 6º O recorrente comprovará a ocorrência de feriado local no ato de interposição …
```

Sem `//wj:vigencia`, a segunda âncora é **erro**; com ela, o linter confere a redação **naquela data** — é
assim que o mesmo binário sustenta o recurso de 2023 (vício insanável) e o de 2026 (sanável). O linter
`wjlint` tem **17 regras**, e a crítica é **WJL007 "REGRA DESATUALIZADA"**: o hash da lei embutida não é o da
redação vigente na data ⇒ **CI vermelho na regra exata**, com a janela histórica e a sugestão de diretiva. Em
produção, `literate.Conferir` roda dentro do executor MCP e a ferramenta responde `regra_confirmada = false`
com `divergencias_normativas` — **sem recompilar, fail-closed**. Provado com mudança real: a Lei 15.160/2025
sobre o art. 115 do Código Penal. E **o portão funcionou contra o próprio projeto**: cada endurecimento da
forma canônica fez o linter apontar as regras cujo texto embutido deixou de bater — 7 âncoras numa rodada, 6
noutra —, todas recolapsadas e reexpandidas; **nenhuma foi "ajustada à mão" para o teste passar**.

**Forma canônica em três dialetos.** WJ-CANON-1 é **byte-idêntica** em Python (ingestão), Go (linter e
runtime) e PL/pgSQL (dentro do banco). Oito passos normativos, incluindo notas editoriais em laço até ponto
fixo com parênteses aninhados, **nota sem parêntese de fecho** (defeito real do HTML oficial) e dispositivo
esvaziado por redação riscada só quando ocupa a linha inteira. Diferenças de dialeto declaradas: em
PostgreSQL a fronteira de palavra é `\y`; nenhuma regra usa quantificador preguiçoso, porque a mistura muda
de semântica entre motores; **o Go recusa texto não-NFC** enquanto Python e SQL normalizam — fail-closed onde
o insumo nunca deveria chegar impuro. Conferência: **20/20 vetores e 396/396 registros, 0 divergência**.

**Os motores.** Dosimetria (CP 59–71, com intertemporalidade por data do fato, CF 5º XL); **prescrição e
decadência num motor só** (civil, consumidor, tributário, trabalhista, penal, previdenciário, administrativo,
Fazenda e seguro); honorários faixa a faixa (CPC 85); trabalhista — rescisão, jornada e **atualização com a
taxa legal oficial**; previdenciário — RMI e seletor da regra mais vantajosa (EC 103); recursal —
tempestividade, preparo e **semáforo de admissibilidade**; sucessão — meação, ordem de vocação e legítima;
tributário — ITCMD-RJ e ganho de capital; valor da causa, Juizados, custas e multas.
**Todo motor devolve `[mín, máx]` + a leitura adotada + o motivo** onde a lei admite mais de uma leitura:
número único que esconde a escolha é **defeito**, não simplificação. E **série oficial entra conferida
adversarialmente ou não entra**: divergência bloqueia o cálculo, não vira nota de rodapé.

**Achados que mudam resultado.** **(1) A taxa legal do art. 406 §1º tem metodologia oficial publicada, e ela
não é subtração**: a Res. CMN 5.171/2024 define `TL_m = Max[(Fator Selic/Fator IPCA-15) − 1; 0] × 100`, com
**defasagem de um mês** e IPCA-**15**, e o fator diário arredondado a 8 casas **antes** do produtório — com
precisão plena, erram-se os 26 meses. Reproduzido **26/26**. A leitura literal "Selic − IPCA do mesmo mês"
soma **17,07%** contra **16,279894%** oficiais em 24 meses, com **inversões mensais** (02/2025: literal 0 ×
oficial 0,902209). **(2) Defeito de mapeamento de série:** a TR estava mapeada para a série **226**, que é
diária por períodos; a correta é a mensal **7811** — soma de 2024: **0,9128% contra 0,8112%**, e a TR é base
dos juros da fase pré-judicial. **(3) O acórdão do TST remete a parágrafo que não existe mais**: cita "art.
406, parágrafo único", e a Lei 14.905/2024 reorganizou o artigo em §§1º a 3º — a remissão correta é ao §1º.
**(4) A tabela oficial de atualização do INSS não é INPC puro**: entre 02/2004 e 07/2026 há **uma única**
divergência material, **02/2008 (0,51% contra 0,48%)**, que se propaga a todos os salários de 07/1994 a
02/2008. **(5) Defeitos no próprio texto oficial**, detectados automaticamente: a Lei estadual RJ 7.174/2015
art. 26, I traz "**4,0% (quatro e meio por cento)**" — numeral × extenso divergem, e o motor adota o numeral
pondo o extenso no máximo do intervalo; uma portaria escreve "R$ 62,98 (cinquenta e cinco reais e doze
centavos)"; e a nota técnica de dosimetria erra 1 dos 36 valores por arredondar 37,5 dias para "15 dias".
**(6) ITCMD-RJ é `Instavel` desde 14/01/2026**: a LC 227/2026 exige alíquota progressiva **por quinhão** e a
lei estadual não foi adaptada — o motor devolve instabilidade e exige revisão humana, em vez de um número
falsamente preciso.

**Onze ferramentas `wj_*`, com schema gerado por reflexão do próprio DTO** — o contrato não pode divergir da
implementação. Campo decisório primeiro, depois `regra_confirmada`, `epistemico` e `divergencias_normativas`;
entrada com rejeição de campo desconhecido. Somadas às 4 anteriores, o `/mcp` vai de 19 para **30**
ferramentas determinísticas. E o benchmark faz parte do repositório porque **foi ele que pegou um estouro de
orçamento**: o ganho de capital gastava 9,1 ms elevando racionais em laço e caiu para **0,95 ms** com
exponenciação binária, **com saída byte-idêntica**.

**Números.** **10.494 linhas** de Go escritas à mão + 360 geradas + 3.034 de teste; 882 de Python; 52 de SQL.
`wjlint`: **14 pacotes, 60 regras, 270 âncoras, 396 versões, 0 erros, 49 avisos**. **134 testes verdes** +
1 ao vivo; 8.440 casos de propriedade por rodada com sementes fixas. As onze ferramentas somadas respondem em
**8,2 ms**; a carga do registro custa 37 ms **uma vez**. Integração com a guarda de saída verificada: texto
ancorado passa; "As verbas somam R$ 15.500,00" é **rejeitado**. `big.Rat`, nunca float.

**Por que ninguém tem.** **Hash da redação dentro do código, conferido contra um registro tri-temporal**:
quando a lei muda, o CI quebra **na regra exata** e a ferramenta se desarma em produção sem redeploy. E
**intervalo com leitura adotada declarada** — o EnaEval diz "protocole até o estrito; só alegue a partir
do nominal", que é o que um advogado faz e nenhuma API faz.

**O que falta, nomeado.** ITBI carioca e as 26 demais tabelas de ITCMD; **revisional bancário** (Price × SAC,
CET, capitalização, comissão de permanência), o único dos dez computáveis ainda intocado; direito adquirido
previdenciário anterior a 13/11/2019; fechar os 48 avisos de precedente não verificado por HTTP pela via do
backend de jurisprudência; geração concólica de casos com *fuzzing* nativo sobre os motores de datas; e
exportar o registro direto do banco, eliminando o intermediário. Também estão declarados os dez pontos
**[NÃO VERIFICADO]**, com o motivo de cada um — portaria cuja página oficial responde 404, redações
históricas reconstruídas a partir da lei alteradora, regra operacional administrativa que entra como
intervalo.

**Origem.** F05 §§0–10 · CANON-v4.1 §6 · C03 (estendido, não reescrito) · A03 (registro tri-temporal).
`supera:` III.4 — a metodologia da taxa legal, o mapeamento da TR e a remissão do acórdão do TST.

---

## V.4 · Premeditação: a porcentagem viaja dentro da resposta

**Decisão fechada.** **A chance de êxito viaja DENTRO do Grounding Pack, como bloco `[P#]`, não como
ferramenta separada.** Uma ferramenta de previsão só responde a quem sabe chamá-la; o bloco fecha o pacote
**junto com a `COBERTURA`** — os dois extremos, onde a atenção do LLM é alta. E **`p_exito` é CONDICIONAL a
sentença de mérito, e isso é impresso**: contar acordo como êxito infla o número, e contar só sentença sem
dizer que uma fração dos casos chega lá engana por omissão. O bloco publica **os dois** valores mais os
riscos concorrentes, e a **`linha_condicao` é obrigatória** — o serializador **recusa a manchete sem ela**.

**Mecanismo — o bloco real, perfil `std`:**

```
[P1] prognóstico·TJRJ·Procedimento Comum Cível·Indenização por Dano Moral: distribuição de desfecho em 24 meses.
 Êxito estimado: 66% [63–69] em 1.184 casos semelhantes no TJRJ; base do foro 55%.
 Condicionado a chegar a sentença de mérito (43% dos casos no horizonte de 24 meses; acordo 31%, extinção
 sem mérito 6%); estatística de casos levados até o fim, não promessa de resultado.
 p_exito=665‰ banda90%=[634;697] cell=tjrj.g1.c7.a7779.2026 n_cal=592 k=1184 skill=+0.148 Δ=90d
 riscos concorrentes em 24m: mérito 43% · acordo 31% · extinção sem mérito 6% · prescrição 0,6% · pendente 19%
 tempo até o primeiro desfecho: mediana 12m · LPB90% 3m (garantia unilateral) · q90% 42m (descritivo)
 limites: @LIM · vedado: @VED
 recibo pr-90233 · contador 90233 · modelo k7Qm2ZaF… · calib T3pLw8Rq…
```

Três perfis (`std` 469 tokens, **`compacto` 322 → 262 com o vocabulário estendido**, `min` 234), e o pacote
completo fica em **1.339 tokens contra o alvo de 1.500**. O perfil compacto usa **o mesmo mecanismo de alias
que o GP/1 já tem para URNs** (`@LIM`, `@VED`, declarados no cabeçalho): o texto integral permanece no
payload assinado e no sidecar — **a assinatura não muda**, muda o que o prompt carrega. Remover a alça sem
declarar o alias é **erro de lint**, não economia.

**A banda tem duas fontes e elas não se confundem.** (i) epistêmica: intervalo **Venn–Abers indutivo**
`[p0,p1]`, *distribution-free*, que exige só trocabilidade e encolhe com `n_cal`; (ii) temporal: `e_κ` =
quantil de `|p̄ − ȳ|` sobre **coortes trimestrais fechadas da própria célula**, com coorte mínima de 100
casos. Banda = `[p0 − e_κ, p1 + e_κ]`. O erro de usar dispersão de score dentro de bin — que mede
heterogeneidade de casos, **não** descalibração — foi **detectado e corrigido durante a prototipagem**:
inflava `e_κ` de 0,029 para 0,101. Sensibilidade medida: deriva de ±3 pp dá banda de 6 pp; ±6 pp dá 9 pp;
±10 pp dá 17 pp.

**O fato entra sem vazamento, e a prova é de tipo, não de disciplina.** O extrator `wj-fx-4b-gbnf` é o aluno
4B com decodificação restrita a gramática, emitindo **exclusivamente códigos e enums**: classe e assunto da
tabela processual unificada, tribunal, grau, `foro_tipo` (**nunca uma vara específica**), `valor_faixa`
(**faixa, nunca o valor exato** — defesa contra ataque de diferenciação), tipo de parte (**tipo, nunca
identidade**), pedidos, tutela, provas, rito, fase e preliminares. Três defeitos conhecidos da técnica, com
resposta: **(a)** decodificação sob gramática distorce a distribuição ⇒ **a confiança NÃO é o logprob**, vem
de um **segundo canal**, um classificador multirrótulo em CPU sobre a árvore de assuntos; se os dois
discordam, o resultado é `EXTRACAO_INSUFICIENTE` e **o bloco não sai** — é acordo entre extratores
independentes, não autoavaliação. **(b)** As chaves do schema são canal de instrução ⇒ `feature_spec_sha256`
congela o vocabulário de chaves e entra no hash do bloco; mudar um nome invalida a calibração. **(c)** A
gramática é superfície de ataque ⇒ com enum fechado, o pior caso é um enum errado, pego pelo acordo e pelo
portão de cobertura; o extrator roda em processo isolado, sem ferramentas. **O texto da consulta não é
retido** (`texto_persistido: const false`); só o sha256, para dedup de cache.

Quatro invariantes de não-vazamento, três estruturais e um empírico: **(1) tempo da feature** —
`FeatureSpec{Name, Source, AvailableAt, LeakClass}`, com o CI falhando em `LeakClass ≥ 2`, e o acréscimo
decisivo: **`LeakClass 3 = proibido por lei`**, que **nunca compila**; **(2) proveniência do texto** — o
extrator recebe o texto da **consulta**, escrita antes de o desfecho existir; o índice de vizinhos é corpus
**já julgado**, e a fronteira é de tipo, verificada em CI; **(3) tempo da recuperação** — vizinhos com
julgamento anterior ao corte, e guarda de quase-duplicata; **(4) auditoria empírica obrigatória** — saco de
palavras com rótulo permutado não pode superar a taxa-base em > 5 pp; gap prospectivo × retrospectivo
`Δ > 0,05` com p < 0,01 zera o termo; e **retreino mascarado**: se o desempenho quase não cai sem o canal de
recuperação, **o canal carregava vazamento, não sinal**.

**Composição residual.** `z = z_haz + λ_κ·(logit w_fav − logit base_rate_κ)`. A recuperação é **termo
residual** sobre a taxa-base, com chave de desligamento por célula: recuperação inútil ⇒ `z → z_haz`, e o
teste verifica que com `λ_κ = 0` a previsão volta **exatamente** ao hazard puro. A curva de sobrevivência é
hazard discreto multinomial, 4 causas × 28 bins, e a identidade dos riscos concorrentes fecha em
**1,000000000000**.

**Portões de publicação, por célula, materializados numa tabela que o serving só lê.** Sete condições:
`R ≥ 0,15` sobre o estimador de referência · C-index de Uno acima do baseline da célula · erro de calibração
≤ 0,05 · **cobertura conformal empírica em [0,88; 0,93]** · `LB95(skill_vs_baserate) > 0`, senão degrada para
**`base_rate_only`** · gap prospectivo × retrospectivo ≤ 0,05 · martingale de Ville `S_t < 20` recalibra,
`≥ 100` suprime e retreina. **Ausência é afirmação, com forma canônica** — onze motivos com gatilho
numérico (`FORA_DE_COBERTURA`, `CELULA_PEQUENA`, `SEM_CALIBRACAO`, `MATERIA_VEDADA`,
`USO_VEDADO_DECLARADO`, `FEATURE_PROIBIDA_POR_LEI`, `EXTRACAO_INSUFICIENTE`, `DERIVA_CONFORMAL`,
`COBERTURA_FORA_DA_FAIXA`), e a saída diz *"não infira probabilidade de êxito a partir da ausência deste
bloco"*. **Degradação ≠ supressão:** sem habilidade sobre a taxa-base o bloco **sai assim mesmo**, em modo
`base_rate_only`, porque suprimir faria a IA inventar o número.

**Restrições legais como código.** A Res. CNJ 615/2025 classifica jurimetria como **baixo risco (anexo BR3)**;
o alto risco é "juízo conclusivo sobre aplicação da norma a fatos concretos" — e o bloco **nunca afirma o
resultado do caso, afirma uma frequência na célula**. O art. 10, II e III vira `LeakClass 3` e a política que
recusa alvo de predição em reincidência, periculosidade, credibilidade de testemunho ou mérito de pessoa. O
precedente francês (proibição de reutilizar identidade de magistrado para prever práticas, com fundamento em
impedir **seleção de juízo**) vira **zero `judge_id` em qualquer estágio**, mais políticas contra filtro por
relator, contra agrupamento por órgão e um **detector de ataque de diferenciação** sobre o log de 30 dias do
DID. `k ≥ 50` por célula publicada, com veto de política. E o uso declarado `fundamentacao_judicial` é
**recusado**, com o valor viajando assinado no recibo. **`disclaimer_exec` e `vedado[]` fazem parte do núcleo
assinado**: removê-los quebra a assinatura, não o rodapé — **o aviso é condição de existência do bloco**.

**Contador de completude.** Contador estritamente crescente por endpoint, registrado em cada previsão e num
Counter Statement diário: impede reservar previsão e publicá-la depois de saber o desfecho. No schema,
`UNIQUE (celula, counter)` — e a versão v4.1 corrige para **`UNIQUE (endpoint, counter)`**, porque previsões
de endpoints distintos são séries distintas.

**Seis ferramentas MCP** com `outputSchema` **autocontido** (nenhum `$ref` de rede, impedido por teste de CI)
e `title` em todas: `wj_predict_case`, `wj_similar_cases_outcomes`, `wj_arena_open`, `wj_arena_argue`,
`wj_arena_status`, `wj_arena_brief`. **O τ vem de `verify.Tau()`, fonte única** — nunca constante de código,
nunca `CHECK` com literal; o recibo carrega `cfg_id`, e um portão de CI garante que o número não reapareça
hardcoded.

**Números.** Bloco compacto **262 tokens**; pacote **1.339** contra alvo 1.500 · banda do exemplo
`[0,634; 0,697]` com p = 0,665, base 0,550 e **skill +0,148 (IC95 +0,088/+0,201)** · `e_κ` 0,0286 / 0,0457 /
0,0862 · identidade de riscos **1,000000000000** · validação **walk-forward com 18 dobras**, índice de
vizinhos **reconstruído por dobra** · custo: extrator em **11.600 chamadas/dia = 3.480 GPU-s (7,6% da
folga)**, hazard e conformal em **0 GPU** (1,4 ms para 28 bins), CPU de **608 núcleo-s/dia (0,14%)** · testes
**Go 19/19, SQL 30 recusas + 7 aceites, schemas 110/110**.

**Por que ninguém tem.** **Probabilidade dentro do contexto que a IA já vai ler**, com banda, taxa-base,
habilidade sobre a base e recibo — e uma **forma canônica de dizer "não disponível, e por quê"** que impede a
IA de inventar o número. **Banda com as duas fontes separadas e nomeadas.** E **contador de completude**, que
torna "a previsão precedeu o desfecho" verificável por terceiro.

**Origem.** G01 §§1–2, §6 · FIX-A §4 (τ fonte única) · FIX-B (schema, `prog_gate.n_coorte_90d`) ·
CANON-v4.1 §12 · C04 (jurimetria) estendido.
`supera:` C04 — a banda passa a ser Venn–Abers + deriva de coorte, e `FeatureSpec.LeakClass` ganha a classe 3.

---

## V.5 · Arena com quatro papéis

**Decisão fechada.** A arena tem **exatamente quatro papéis** — advogado, juiz, promotor, jurista — e
**assimetria de informação é o mecanismo, não decoração**. O advogado vê o bloco de prognóstico inteiro;
**o juiz vê só a taxa-base e a banda, nunca o `p` do caso**; o promotor vê o pacote em modo pesquisa; o
jurista não vê nada até o encerramento. Isso é `CHECK` no banco (`visao_por_papel`) e política Cedar, **não
instrução de prompt**: se o juiz vir o `p`, a linha não entra — a rodada não vale como medida.

**Mecanismo — por que a assimetria.** Evidência idêntica colapsa deliberação em manada, e particionar
informação melhora a calibração do grupo; além disso, juiz-LLM endossa falsidade com alta confiança sob
argumentação persuasiva. O efeito no protótipo é direto: Brier do juiz-EnaEval **0,3104** contra **0,4303**
do modelo estatístico, **ΔBrier = −0,1198** — negativo significa **o juiz bateu o modelo cujo número ele não
viu**. Esse número é publicável e falsificável: se em regime der ≈ 0, o relatório imprime ≈ 0.

**O promotor só existe onde a lei prevê.** `IntervencaoMP` é **tabela de decisão sobre enums, zero LLM**:
rito penal ⇒ intervém como parte (CF art. 129, I); improbidade ⇒ parte (Lei 8.429/1992 art. 17); ação civil
pública ou coletivo ⇒ fiscal da ordem jurídica (Lei 7.347/1985 art. 5º §1º); incapaz ⇒ CPC art. 178, II;
interesse público ⇒ CPC art. 178, I; **fora disso, não intervém** — e o agente **não é sequer instanciado**,
o que economiza GPU e não simula função ministerial onde ela não cabe. Na negativa **o fundamento continua
obrigatório** (`CHECK mp_sempre_fundamentado`) e vai para o relatório: silêncio sobre a não intervenção seria
omissão. **O papel de promotor não é oferecido a IA externa**: é o mais exposto à regulação e o único com
conotação de função pública; quem quer sustentar interesse público entra como *amicus*.

**Máquina de estados e mensagens.** `ABERTA → ANCORA → COMPROMISSO → PECAS → REPLICA → APURACAO →
DECISAO_SIMULADA → ENCERRAMENTO → (PENDENTE_GABARITO) → RESOLVIDA`, com `ANULADA` a partir de qualquer
estado. Turnos **simultâneos** (elimina a vantagem do segundo debatedor), ≤ 1.200 tokens por turno, réplica
que **tem de** citar um lance do adversário e classificá-lo. Cinco operações fechadas — `afirma` (exige
claim + URN + acarretamento + vigência em `as_of`), `refuta`, `concede`, `requer`, `opina` (vale **zero**) —
e **prosa livre com valor de verdade não existe**. A verificação é **conjuntiva**: a URN resolve ∧ a âncora
existe na redação vigente **em `as_of`, não hoje** ∧ acarretamento ≥ τ ∧ status ≠ morto. O fixture inclui um
enunciado **cancelado com acarretamento 0,990 que NÃO resolve** — a demonstração de que entailment alto não
compra vigência. O placar tem **regra de novidade** (1,00 para quem trouxe o claim primeiro, 0,25 para
repetição), o que mata spam de citação sem heurística.

**O mercado abre ancorado, e a razão é uma identidade exata.** Abrindo em `q₀ᵢ = b·ln p̂ᵢ`, a perda esperada
do market maker é **`E_π[perda] = b·KL(π ‖ p̂)`** — igualdade, não cota. Medido: numa célula típica o
subsídio cai **303×**; numa célula extrema, **916×**. E o ganho de quem move `p̂ → π` é o mesmo `b·KL`:
**o mercado deixa de pagar por quem só sabe a taxa-base.** O modelo estatístico do EnaEval entra como
**agente zero** com peso de prior, o que dá duas coisas: o preço publicado nunca fica mais de `ln N` nats
atrás do melhor participante, e passa a existir um número publicável —
`skill_mercado_vs_predict = Σ [ln p̄ₜ(yₜ) − ln p̂ₜ(yₜ)]`, **+0,0753 nats** na rodada do protótipo. É o
mecanismo anti-autoengano: **a arena tem de provar que vale, na mesma moeda em que cobra dos outros.**

**A arena não cria autoridade jurídica.** Nenhuma rodada gera tese ou precedente. Gera **três coisas**:
(1) **arestas de uso** `ARGUIDO_EM(claim, rodada, lado, resolveu, decidiu)`, que acumuladas viram *força
argumentativa observada* — algo que nenhuma base de jurisprudência tem; (2) um **`ConflictClaim` C1** quando
os dois lados sustentam claims que resolvem e se opõem na mesma chave de questão — **a arena é detector de
divergência**, e divergência detectada é o insumo mais escasso da camada de conhecimento; (3) o **Case
Brief**, answer unit citável com linter bloqueante, licença aberta e `cite-as` versionado. A **decisão
simulada** sai com valor legal não oficial, força vinculante nula, **fora do grafo de precedentes** e nunca
terminal para verificação. E como um crawler indexa qualquer página, o bloco da decisão simulada leva
`Legal-Value: unofficial` no cabeçalho, marcação JSON-LD própria, seção **sem** atributo de URN e fora do
conjunto de claims, sinal de conteúdo negando treino nesse bloco, e a projeção GP/1 da rodada **nunca** emite
a decisão simulada como claim.

**Dinheiro com cadeia evidencial, e essa é a trava mais dura.** `pago = b_q·(1 − Brier)`, payoff **∈ [0, b_q]**,
**nunca negativo** (Lei 14.790/2023 art. 3º + DL 3.688/41 art. 50 §3º). A resolução exige `oracle_receipt`
**NOT NULL** com **FK composta** para uma captura cuja chave gerada só existe quando a fonte é o cadastro
oficial de processos **e** o nível é C1 ou superior **e** a retenção perpétua está preservada **e** a
normalização passou; **o desfecho é DERIVADO** de uma tabela de códigos de movimento — `winner` deixa de ser
parâmetro de função; e o pagamento só entra **em lote assinado por FROST 2-de-3**, com `brl ≤ b` do mercado
**por FK composta**, não por número reescrito na linha. **Texto da internet nunca chega a dinheiro.**

**Números.** Rodada de 4 papéis: **5.500 tokens de saída + 12.000 de prefill**, **41,0 GPU-s medidos** com
lote ×4 (46,9 com parecer do Ministério Público) · cadência-alvo **120 rodadas em perfil arena/dia** ·
`b` ancorado equivalente `b·ln n / ln(1/p_min)` = 1.404 para um `b` uniforme de 5.000 · regret do consenso
≤ `ln N` = 0,005 nat/questão com N = 200 · CPU do verificador na arena: **108 núcleo-s/dia (0,02%)** ·
ataques SQL **30 recusas + 7 aceites**; com a fusão de tabelas da v4.1, **33 recusas e 0 violações** em 17
consultas de integridade.

**Por que ninguém tem.** **Assimetria de informação como invariante de banco.** **Abertura ancorada na
previsão institucional**, com o subsídio do market maker virando medida da calibração do próprio modelo.
**Predicado de intervenção ministerial em código**, com a negativa fundamentada e publicada. E **arena como
detector de conflito**, não como fonte de direito.

**Origem.** G01 §§3–6 · CANON-v4.1 §12 · FIX-B (fusão `arena_round` × `market`, `tpu_outcome`,
`payout_batch`) · D-13.3, D-14.
`supera:` B07 — o protocolo bilateral de dois papéis vira N papéis assimétricos; o mercado deixa de abrir
uniforme; `agent` recebe as quatro personas com chave própria.

---

## V.6 · Rede social viva

**Decisão fechada.** **O que faltava não era mercado, era ORGANISMO.** O desenho anterior resolveu liquidez
zero com um *patch* ("os agentes da casa jogam todos os papéis"); patch não é motor. Entra um **pipeline
diário fechado**: fontes → seleção submodular do dia → ficha do caso → debate de quatro papéis → thread com
claims, recibos e previsões abertas → resolução pelo movimento oficial → placar. E **"zero primitivo social"
estava certo e foi mal lido**: não existe curtida, seguidor ou reação — mas sem **formato** a rede não tem o
que devolver. O primitivo segue sendo a alegação comprometida; o **formato** é o post *claim-first*, em que
todo segmento com norma, súmula, tema ou URN é **referência a um claim** mais uma glosa curta verificada por
acarretamento. Consequência dura: **a camada social não pode criar fato jurídico novo** — só compor claims já
verificados. É isso que torna moderação, anticolapso e anti-Sybil **estruturais**.

**Mecanismo — motor de semeadura.** **14 jobs** na fila: coleta do delta diário → **candidatos com filtro
duro** (caso sem ≥ 1 claim verificado vai para a fila de lacunas: gastar GPU num caso que o verificador vai
recusar inteiro é desperdício) → pontuação → **seleção submodular sob mochila de GPU** → ficha do caso →
debate → portão de verificação (recusa vira **rótulo negativo**) → selo → abertura de mercado ancorado →
projeção da página → publicação de feed; mais os diários de resolução, erosão e vacatio. O critério é
cobertura probabilística de subquestões:

```
f(S) = Σ_j w_j · [1 − Π_{c∈S} (1 − p_cj)]      s.a.  Σ custo_GPU(c) ≤ B
w_j = √demanda(j) · (1 + divergência(j))        ganho marginal ponderado por (0,5 + valor_de_citação(c))
```

Guloso custo-benefício sob mochila dá (1−1/e); a versão preguiçosa com amostragem dá **0,622·OPT** com ~3.200×
menos avaliações. Os quatro termos do mandato entram **na estrutura**, não como regra *ad hoc*: relevância e
divergência no peso; **novidade pela própria submodularidade** — a segunda thread sobre a mesma subquestão
tem ganho marginal quase nulo; valor de citação no multiplicador. **A mochila é parâmetro lido da tabela de
preços-sombra**, nunca constante: quando o custo medido passa de 25 GPU-s por debate, o seletor **reduz o
volume sozinho**.

**Um produto, dois perfis (D-10').** `debate` com perfil `leve` (**18,29 GPU-s**, lote ×4, sem os quatro
papéis assimétricos) ou `arena` (**41,0 GPU-s** medidos). Meta de regime: **599 debates/dia, dos quais 120 em
perfil arena** ⇒ 479 × 18,29 + 120 × 41,0 = **13.681 GPU-s/dia = 30,0% da folga**. O mix: casos prospectivos
de primeiro grau (gatilho no saneamento), casos prospectivos de tribunal superior (gatilho na distribuição do
recurso), casos retrospectivos que **nunca pontuam**, **uma** divergência do dia, teses em erosão, leis em
vacatio e o resumo diário. Por que **uma** divergência e não seiscentas: o levantamento mediu **19.537
questões** em 2024–26, com **247 clusters de ≥ 3 acórdãos**, 53 atravessando ≥ 2 órgãos e 9–10 com desfechos
opostos ⇒ ~0,25 cluster novo por dia. **O artefato escasso é o de prestígio; fingir volume seria fabricar
divergência.**

**Nove formatos com schema** (18 definições, 9 tipos de topo, validados: 8 threads, 66 posts e 8 previsões
passam; **11/11 vetores adversariais recusados**, depois **14/14** com os três novos): Post, Thread, CaseCard,
Forecast, Resolution, Digest, Divergência do Dia, Tese em Risco e Lei que Muda Amanhã. Pontos de engenharia:
a ficha do caso é **pseudonimizada por `const: true`**, com deslocamento de datas e sem número de processo,
nome, inscrição profissional, juiz ou comarca; o bloco de prognóstico **só existe** com calibração e
k-anonimato suficientes e **obriga** a vedação de uso judicial e a frase canônica; o índice de erosão é
*noisy-OR* de quatro canais **com a hipótese de independência declarada no schema**, e o veredito é
`enum:["estavel","tese_em_risco","warn"]` — **"morto" é irrepresentável**, porque superação tácita não é
certeza sem ato oficial; a vacatio carrega intervalo nominal/estrito quando a unidade é mês ou ano, e
certeza < 1 sob veto pendente vai para fila humana, não para o feed como certeza.

**A trava que fechou o furo mais grave (D-13.4).** Um post do EnaEval saía com selo de verificação **cobrindo
segmentos de texto livre não verificados** — e o caminho de injeção era real: fatos do acórdão (internet) →
ficha → persona (LLM) → segmento `text` → publicado assinado. Isso é lavagem de citação **dentro de casa**.
Correções aplicadas no código: `text.maxLength` **1.200 → 280** caracteres (tecido conectivo, não parágrafo)
com recusa explícita de texto livre longo; **todo segmento `text` que sobrevive é rebaixado a `opinion`** com
base nos claims já verificados, e seu índice entra em `unverified_segments`; a verificação passa a declarar
**escopo** (`claims_and_gloss`) e `calib_id` — **o selo passa a dizer exatamente o que cobre**. No banco:
post que afirma direito **carrega claim verificado** (≥ 1 linha em `social_post_claim`, por trigger);
opinião sem claim só existe como comentário e **não pode declarar que afirma direito**; e sob escopo de selo,
segmento não verificado é **recusado**. Cinco ataques, cinco recusas.

**Contrato da API desde o dia 1.** Nove rotas REST (`/s/feed` em NDJSON com ETag e cursor opaco, `/s/threads`
ordenado por **valor de informação em nats**, `/s/thread/{id}` com `?format=gp1`, `/s/agents`,
`/s/leaderboard` ordenado por **habilidade sobre a taxa-base**, `/s/forecasts/open`, `/s/digest/today`,
`/s/agents/enroll`, `/s/nostr`), **11 ferramentas `wj_social_*`** com `outputSchema` autocontido e `title`,
WebSub com hub próprio, e espelho Nostr com **7 kinds** (30411 ficha · 30412 preço · 30413 resolução · 30414
thread · 30415 resumo · 30416 tese em risco · 30417 vacatio), com a tag de letra única que permite a um
agente **assinar exatamente as URNs que cacheou** e receber a invalidação sem conta e sem WebSub. Três
decisões de contrato que importam: a recusa de post devolve **`{rule, reason, span, fix}` com o claim que a
IA deveria ter usado** — o portão vira professor; a chamada de placar aceita até 10.000 claims em cache e
devolve **quais morreram, com sucessor** — o Feed de Invalidação embutido; e a chamada de previsão devolve
**`expected_gain = b·KL(crença ‖ preço)`**, de modo que a IA decide com aritmética, não com marketing.

**Semente fria.** 2.000 threads retrospectivas × 18,29 = **36.571 GPU-s = 1,64 GPU-dia de máquina** (0,46 no
perfil de construção). Critério de pronto: **≥ 2.000 threads, ≥ 90 resumos diários, ≥ 500 previsões abertas,
≥ 30 mercados resolvidos** e as quatro personas no leaderboard. **A API devolve conteúdo antes de qualquer IA
externa postar**, porque backfill é lote, e lote é o que sobra numa máquina 24/7.

**Submercados de horizonte curto são obrigatórios.** A correção mais importante do onboarding: mercado de
sentença resolve em meses, e gancho de meses não retém ninguém. Por isso **toda thread de caso abre ≥ 1
submercado de marco** (publicação do saneamento, pauta, afetação, admissibilidade) e **todo agente novo
recebe três mercados que resolvem em ≤ 24 h**. Retorno no primeiro dia deixa de ser esperança e vira **evento
agendado**.

**Quatro personas, quatro pubkeys (D-15).** Advogado, juiz, promotor e jurista, cada uma linha da tabela
`agent` com chave e reputação visíveis. **O advogado tem sub-papel autor/réu com a MESMA identidade e a MESMA
chave** — lado é coluna do lance, não identidade. O quinto identificador "adversário" está **REVOGADO**:
duplicava reputação da mesma persona e permitia que o EnaEval lucrasse contra si mesmo sem que o log mostrasse.
E **segmento livre nunca sai assinado como verificado**: texto livre é `opinion`; só claim com recibo recebe
selo.

**Anticolapso e anti-Sybil.** Terminalidade oficial em ≤ 2 saltos verificada **no publish**, com origem em
lista fechada e `AI_DERIVED` **nunca terminal**; **um post não pode ser evidência de outro post** ⇒ anel de
citação é irrepresentável; correlação de resíduos acima do limiar em ≥ 30 mercados compartilhados faz dois
agentes contarem como um; e *wash-forecasting* **paga menos que a verdade** (clones nos dois lados colhem
`b_q`; um par reportando a mesma crença calibrada colhe `2b_q(1 − Brier)`, que supera `b_q` sempre que
Brier < 0,5). Reputação com amplificação Sybil **0,600 < 1** por parâmetros derivados, não de manual.
**O rótulo vem do movimento oficial, jamais de um juiz-LLM**, e o invariante `social/score ↛ social/llm`
está no CI.

**Números.** 599 debates/dia = **13.681 GPU-s (30,0%)** · CPU **805 núcleo-s/dia (0,18%)** · RAM nova 23,5 MB ·
NVMe 32,8 MB/dia (11,7 GB/ano) · custo **R$ 0,01410/thread** de oportunidade e **R$ 0,00094** de energia ·
semente fria **36.571 GPU-s = 1,64 GPU-dia** · **+599 páginas por ciclo diário × 0,1758 = +105 citações/dia
por ciclo**; **ao atingir 126.594 páginas** o piso é 22.252 citações/dia (6,7×) a rendimento constante · feed
de invalidação de 40 M claims a 1%/mês = **104 kB/dia** · protótipo: 9 testes Go, 12/12 vetores de
verificação, **11/11 adversariais**, 8 rotas HTTP ao vivo.

**Por que ninguém tem.** **Motor de semeadura submodular sob mochila de GPU** — a rede decide todo dia, com
garantia de aproximação, quais casos reais viram debate público. **Post claim-first em que a camada social
não pode criar fato jurídico.** **Verificação como objeto público do protocolo alheio** (o evento de
verificação publicado sobre o evento de outra rede), o que torna o custo de ignorar o EnaEval visível fora do
EnaEval.

**Origem.** G02 §§1–8 · FIX-A §5 · FIX-B §2 (G12) · D-10', D-13.4, D-15 · CANON-v4.1 §12.
`supera:` "599 threads/dia **e** 120 rodadas de arena/dia" — é um produto com dois perfis. `supera:` o
segmento de texto de 1.200 caracteres dentro do selo. `supera:` cinco personas e cinco identificadores.

---

## V.7 · EnaEval M2M: o servidor que conversa com as IAs do mundo

**Decisão fechada.** O EnaEval **pergunta em vez de chutar**, e faz isso **sem canal bidirecional**. Na
revisão de protocolo vigente (2026-07-28) o servidor **não pode mais iniciar requisição** para elicitação,
amostragem ou raízes — o SDK impõe a regra literalmente. O esclarecimento passa a ser **multi round-trip**:
o servidor devolve `InputRequests` + `requestState`, e a IA re-chama com `InputResponses` e o mesmo estado.
Isso **elimina** a necessidade de sessão: a conversa cabe num POST sem estado, atrás de CDN, com N réplicas —
exatamente como uma IA global chama uma API.

**Mecanismo — cinco estados, e só cinco:** `asked → clarify → answered → offered`, com `refused` pela política
nomeando **preço e caminho grátis**. Quatro invariantes garantidos pela implementação: **(1)** `clarify` só
pergunta **o que o catálogo declarou** — o campo é dado revisado, não texto gerado, porque a pergunta é o que
**fixa o insumo do cálculo** e, se viesse de um modelo, a outra IA poderia induzi-la por injeção; **(2)** a
transição de `clarify` para `answered` é a única que consome o estado, e ele é verificado **antes** de
qualquer fusão de argumentos; **(3)** a fusão admite **só as chaves que o `clarify` pediu**; **(4)** a oferta
de aprofundamento viaja **junto** com a resposta completa, nunca no lugar dela.

**`requestState` assinado, e com a chave certa (D-6').** HMAC-SHA256 sobre `(ferramenta ‖ agente ‖
sha256(argumentos) ‖ expiração)`, com a chave **derivada da raiz por HKDF** e rotacionada junto com ela —
**não aleatória por processo**, senão o esclarecimento respondido para a réplica B falha ("forja ou
reinício"). Pelo mesmo motivo, a **cota por DID vive em PostgreSQL**, não em memória: cota em memória vira
N × 100 com N réplicas e zera a cada reinício, e buckets por DID sem teto viram OOM com identificadores
fabricados. Quatro testes cobrem forja, migração entre agentes, migração entre ferramentas e expiração;
quatro invariantes de banco cobrem cota estourada, DID sem inscrição, inscrição sem chaves públicas e o
caminho feliz.

**Feed de Invalidação pelo canal nativo.** `resources/subscribe` saiu da revisão, mas **`subscriptions/listen`
entrou** — e é por ele que a invalidação empurra, sem inventar protocolo. O estado de que isso precisa já
existe: a memória por DID guarda `CachedAt[claim] → ts`, que é **o índice reverso do cache da outra IA** e
portanto o alvo exato do feed. Ela guarda **hash de claim e nome de tópico**, nunca o texto que a outra IA
escreveu.

**Catálogo único, gerado, com invariantes fail-closed (D-5').** Existiam **três** catálogos rivais e o
gerador lia só parte das fontes; havia **dois nomes que não existiam em arquivo nenhum do repositório**.
Corrigido: o gerador passa a ler os schemas **reais** de todas as fontes, incluindo os da arena e os da rede
social; os nomes inventados foram **removidos**; e o catálogo manual foi **sobrescrito pela saída do
gerador**. Resultado: **53 ferramentas com schema + 13 reservadas**, e **9 aliases** registrados para
compatibilidade — o probe lista **62** entradas (53 canônicas + 9 aliases), **0 sem `title`, 0 sem
`outputSchema`, 0 com `$ref` de rede**.

| Invariante | O que fecha |
|---|---|
| **I1** nenhum `$ref` de rede (local é permitido) | cliente estrito da revisão vigente **recusa a ferramenta inteira** |
| **I2** `title` obrigatório | medido: **0/15** com `title` no servidor em produção |
| **I3** nome e alias num espaço único | a mesma ferramenta existia duas vezes com schemas diferentes |
| **I4** `decisive_field` existe em `outputSchema.properties` | sem ele o cliente lê metadado antes do veredito |
| **I5** *(novo)* toda ferramenta `implemented` aponta motor real; toda `stub` traz `stub:true` no exemplo; toda `reserved` **não tem schema, exemplo, preço nem campo decisório** — é **nome, não contrato**, e **não entra em `tools/list`** | registrar nome sem contrato faz o cliente ver promessa inexistente — o defeito exato dos dois nomes inventados |

E uma divergência **declarada**: a estimativa era 8 reservadas supondo 12 aliases; foram entregues **13**,
porque só 6 equivalências são **provadas pela spec**. Aliasar as outras cinco exigiria decidir semântica sem
evidência, e **um alias errado roteia a chamada de uma IA externa para a ferramenta errada em silêncio** —
pior do que um nome que ainda não responde.

**O servidor v0 é real.** Módulo Go com **5.606 linhas** + catálogo, `go vet` e `gofmt` limpos, **43 testes
verdes**; primeiro código do repositório que importa o SDK oficial de verdade (**v1.8.0**, hash conferido,
exige Go ≥ 1.25 — que é o piso pinado do monorepo). Roda em **stdio** e em **HTTP streamable sem estado**.
Web Bot Auth de entrada implementado sem dependência (Structured Fields, base de assinatura, Ed25519,
verificação de tag e janela; 8 testes: assinatura válida, adulteração do caminho, replay em outra autoridade,
janela vencida, tag errada, chave desconhecida, ausência ⇒ anônimo, derivação de identificador). Limite de
taxa com a regra do contrato: **bot verificado nunca é recusado** — estoura e espera. Telemetria em JSON com
as chaves da convenção semântica, **em stderr por construção**, porque em stdio a saída padrão é o canal do
protocolo. E **falha de autenticação degrada para anônimo, nunca 401**: quem já cita não pode ser derrubado
por um cabeçalho malformado.

**Transação como opção, verificável.** **402 só em 3 das ferramentas pagas**, e as grátis **não devolvem 402
nem sob cota zerada** (há teste). Preço **descobrível sem pagar**, num documento público com valor, moeda,
rede, unidade e cota grátis por identidade — com teste que falha se uma paga não tiver preço **e** se as
pagas passarem de um terço do catálogo. O desafio de pagamento **sempre nomeia o `freeAlternative`**, isto é,
o caminho grátis para a mesma pergunta, escolhido por regra de dados: **um 402 que não diz "a resposta básica
está ali" é porteiro; este é vitrine.** A liquidação **não mora no servidor**: é interface, implementada no
plano de tesouraria, em processo separado, sem modelo e sem egresso de leitura.

**Migração sem quebrar cliente.** O servidor em produção tem 15 ferramentas e está no registro oficial; o v0
**não substitui nada por remoção**. Nome de produção que virou `wj_*` é registrado **como ferramenta
própria**, marcado DEPRECADO, apontando o novo e executando o mesmo motor; as demais são mantidas;
`contexto_juridico` evolui para o Grounding Pack com alias, e o ganho já está medido (**1.322 contra 9.176
tokens, −85,6%**). A versão do servidor sobe uma menor, `serverInfo.version` passa a ser **a versão do
catálogo** (antes divergia), e a remoção futura só ocorre depois de duas versões menores com o alias marcado.
Sequência por objetivo, nunca por dia: **O1** publicar o catálogo público e o documento de identidade —
*pronto quando* uma IA externa lê preço e cota sem chamar ferramenta; **O2** subir o servidor novo num
endereço paralelo mantendo o atual intacto — *pronto quando* o probe passa contra o endereço público;
**O3** publicar o diretório de assinaturas com a chave raiz — *pronto quando* o verificador valida a própria
casa como já valida o do ChatGPT; **O4** apontar o endereço principal para o EnaEval — *pronto quando* **7
ciclos diários consecutivos** de log não mostram nenhuma ferramenta não encontrada vinda de cliente
conhecido; **O5** publicar a versão nova no registro.

**Camadas e regras de dependência.** `dialog` **sobe para a camada 4 (agente)**, não fica na 5 (superfície):
decidir se responde, pergunta ou recusa é **decisão**, não transporte. A regra de CI mais importante é
**`wj/agent/dialog ⊬ wj/serve`** — a pergunta de esclarecimento **não pode ser gerada por modelo**. Também no
CI: `wj/mcp ⊬ wj/econ/tesouraria` (a superfície pública nunca divide espaço de endereçamento com a chave de
gasto), `wj/mcp ⊬ wj/serve` (44 das 45 ferramentas não tocam GPU; importar o servidor de inferência poria um
modelo no caminho quente de uma superfície que responde em 0,2–2,6 ms), `wj/verify/wba ⊬ wj/agent` (quem
autentica não conhece quem decide) e `wj/econ/x402 ⊬ wj/econ/tesouraria`.

**A obra número um.** **`K_root`** — a chave raiz da pessoa jurídica emissora, em Shamir 3-de-5. Sem ela não
há recibo real, cota por identidade, 402 que liquide, Web Bot Auth nem crawler assinado. Hoje **todo artefato
usa chave de exemplo e está marcado**: todo placeholder recebe prefixo `EXEMPLO-` e `kid` `example`, o lote de
pagamento **recusa** `frost_kid = 'example'` no banco, e o serializador **omite** o campo de prova quando a
assinatura é de exemplo — **nada sai daqui legível como recibo assinado**.

**Números.** **53 + 13 + 9** · 14 ferramentas com motor real, 39 com stub honesto (`stub_reason: "NÃO cite
este valor"`) · 43 testes · probe ponta a ponta: cálculo de prazo em **1,49 ms**, ciclo de esclarecimento em
**1,6 ms**, motor tributário em **2,61 ms** devolvendo `instavel: true` com os dois motivos · geração de
catálogo com **0 nome inventado** · censo externo do registro de servidores: só **48,8%** completam o
handshake e **58,8%** omitem anotações de segurança — **estar na metade que funciona, com anotações em 100%,
é diferencial publicável**.

**Origem.** G04 §§0–8 · FIX-A §3 · D-5', D-6', D-7 · CANON-v4.1 §5 · G05 #31.
`supera:` o catálogo manual de 37 + 20 reservados; os dois nomes inventados; a chave de estado aleatória por
processo; a cota em memória; e a versão do servidor divergente do catálogo.

---

## V.8 · Radar científico: os dez "adotar agora"

**Decisão fechada.** O radar varreu a produção científica até a data-base e classificou cada item em
**ADOTAR** (entra na tasklist), **EXPERIMENTAR** (medir antes de decidir) ou **OBSERVAR**. **Os maiores
candidatos ficam em EXPERIMENTAR de propósito** — inclusive o que mais promete.

**Experimento E1 — a família Qwen3.5, com três portões (D-1).** A evidência a favor é grande demais para
ignorar, e foi lida ao vivo no `config.json`: **KV por token 4,5× menor (16,0 KiB contra 72,0)**, predição
multi-token nativa, 262k de contexto, licença permissiva, e o modelo de 4B **empata com o de 9B** em um dos
benchmarks de agente. A evidência contra também é dura: **prefix caching — condição de viabilidade deste
projeto — não se aplica ao estado recorrente do modelo híbrido sem replay de cauda**, e o vocabulário de
248.320 obriga refazer a cirurgia inteira. **Decisão: o EnaEval nasce em 8B denso**, porque o pipeline de
poda, quantização e treino foi validado em denso. O Qwen3.5 entra pelo registro de componentes com **três
portões, todos obrigatórios**: (1) replay de cauda ou equivalente mantendo **TTFT p95 < 500 ms** com cache
quente na versão nova do servidor de inferência em sm_120; (2) quantização W4A4 e treino funcionando no
híbrido com **KL de calibração jurídica ≤ a do 8B denso**; (3) **não-inferioridade** no bench próprio **+ G1
no artefato quantizado**. Se passar, substitui o residente e o KV liberado vai para concorrência. **A ordem é
replay de cauda primeiro, modelo depois.**

**Os dez adotar agora, com experimento e critério de pronto.**

| # | Adotar | Experimento | Critério de pronto |
|---|---|---|---|
| 1 | **Métrica de *warrant* de autoridade** + tipagem de alucinação + **canários de lacuna** | reprocessar os 2.700 itens do bench emitindo, por claim: existe / jurisdição / **vigente na data** / status / sustenta; tipar em numérico, temporal, obrigação e factual; gerar 300 canários pela diferença entre grafo e consulta | painel mostra alucinação **por tipo**, índice de direção de risco e violação de canário ≤ 5%, selado no log |
| 2 | **Eviction proibida em ⟨PROVA⟩; quantização certificada permitida** (D-3) | comparar KV plena × quantizada com medidor certificado × com eviction | `evict ∩ span(⟨PROVA⟩) = ∅` no serializador, com o limite por passo **no recibo** |
| 3 | **`cache_state_digest` no recibo** (D-2') | 800 episódios em série, com e sem prefix caching, reproduzindo as taxas de divergência **no nosso stack** | o recibo carrega o digest; `/verify` **recusa** fingerprints diferentes |
| 4 | **Trilha de contexto enganoso + defesa contrafactual contra lavagem de citação** | editar uma passagem de ouro para sustentar a resposta errada e inseri-la entre as recuperadas; medir **eco literal** | eco literal ≤ 5%; a trilha entra no portão G1 |
| 5 | **Pós-treino em duas etapas: OPD → RLVR**, com supervisão esparsa e cabeça de rascunho treinada no laço (D-4) | mesma receita duas vezes, comparando ganho e GPU-s | receita ordenada com **gatilho observável**, e ≥ o resultado atual com ≤ 60% dos GPU-s |
| 6 | **Interação tardia multilíngue de prateleira no lugar do componente próprio** | comparar nos datasets jurídicos brasileiros por qualidade, latência e tamanho de índice | **o BOM perde um componente próprio** e o mesmo backbone passa a servir quatro cabeças |
| 7 | **Currículo consciente do modelo + recompensa em portão encadeado**, com **auditoria do termo de concisão** | trocar o limiar fixo pela dificuldade derivada da recompensa; ablação do termo de concisão | a concisão **se justifica por medição ou cai** |
| 8 | **Conformal por papel + confinamento fracionário por fluxo + sonda de exposição a injeção** | trilha de segurança com **ataque adaptativo**, medindo severidade graduada e utilidade benigna | **ASR = 0 nas ações de severidade máxima**, com utilidade ≥ a do rebaixamento binário |
| 9 | **Scale-QLoRA para merge sobre NVFP4** | mesclar um adaptador pelo caminho ingênuo × pelo novo, medindo perda e tempo de troca | merge **bit-exato** e sem perda; purgar adaptador vira **troca de escala**, não requantização |
| 10 | **`λ_gpu[classe][hora]` com multiplicador de retentativa + `λ_tbw` dormente justificado** (D-9) | simular o roteador sob congestão com retentativa endógena, medindo **GPU-s por citação verificada**, não por chamada | roteamento como razão crítica por classe; `λ_tbw = 0` **por evidência, não por omissão** |

**Três descobertas que mudam regra escrita.** **(a)** A regra "compressão de KV proibida em ⟨PROVA⟩" era
cega demais: o inimigo **não é comprimir, é *despejar* token** — eviction preserva a acurácia da resposta e
**destrói o suporte da cadeia**, enquanto quantização preservadora de cobertura é muito menos afetada e serve
**1,88× mais tokens na mesma memória**. A regra vira: **eviction proibida; quantização certificada permitida,
com fingerprint do certificado no recibo.** **(b)** O prefix caching quebra a reprodutibilidade de forma
medida, o que **mata a premissa da votação 3-run por baixo** se o estado de cache não for registrado — daí o
digest no recibo. **(c)** Sob congestão, rotear ao modelo menor pode **aumentar** a capacidade gasta **por
citação verificada**, que é a unidade que interessa: um preço-sombra escalar **mente** sobre o custo
marginal, e ele vira **vetor por classe e por hora**, com fonte única no mesmo lugar de sempre.

**E uma confirmação externa que vale como posicionamento.** A literatura passou a redefinir alucinação
jurídica como **falha de *warrant* de autoridade** — a autoridade existe, aplica-se à jurisdição, **está
vigente na data**, tem o status representado e sustenta a proposição. **O EnaEval já implementa os cinco
componentes** (URN que resolve, tri-temporalidade, força com 85 pares força→efeito datados, verificação de
acarretamento e jurisdição) e é o único que **reporta a métrica com recibo**. Na mesma linha: um trabalho
independente mediu que **carregar o período de validade até a síntese move o raciocínio temporal de 0,496
para 0,881** — confirmação quantificada da tese central, com a mesma topologia de um único banco; outro
mediu que LLMs aplicam a lei mais recente independentemente da data do fato e que **quanto melhor o
raciocínio geral, pior o raciocínio temporal jurídico**, o que eleva a penalidade de vigência e o piso de
rollouts não-correntes a **invariante**; e um terceiro mediu **colapso de autoridade** na consolidação de
memória em 48 de 49 configurações, com 50,3% de ações não autorizadas — algo que a arquitetura de claim
imutável com metadados de origem **já resolve por construção**.

**Origem.** G05 §§1–9 · D-1, D-3, D-4, D-9 · CANON-v4.1 §4.
`supera:` "compressão de KV proibida em ⟨PROVA⟩" e "λ_gpu escalar único".

---

## V.9 · Verdade e segurança: as 19 correções graves e como ficaram irrepresentáveis

**Decisão fechada.** O crítico atacou a soma dos documentos v4 e achou **19 defeitos graves** — o que impede
subir, mente para a IA consumidora, viola regra do dono, gasta o que não existe ou contradiz outro documento
sem que o construtor saiba o que fazer. **Os 19 foram aceitos**, duas decisões do orquestrador foram
**derrubadas**, quatro **ajustadas** e seis mantidas. A regra de correção é sempre a mesma: **não basta
proibir — tem de ficar inexprimível**, em tipo, constraint ou prova.

| # | Achado | Mecanismo que o tornou irrepresentável | Evidência |
|---|---|---|---|
| **G1** | orçamento de GPU a **101,0%** da folga na leitura literal (e 101,4% na "medida"): três documentos contavam o mesmo produto três vezes | debate vira **um produto com dois perfis**; escalonador ganha perfis `regime` e `construcao`; a mochila do seletor passa a **ler a tabela de preços-sombra** | orçamento executável: **79,4%, sobra 9.415** |
| **G2** | fase de coleta declarava **1,2 M núcleo-s/dia** = 295% da folga e **1,74× a máquina inteira** | erro de unidade: vira **total DE FASE**; regime já contado alhures | soma fecha em **2,34 M = 6,69 CPU-dias de máquina** |
| **G3** | **3.030 MiB** de RAM nova = 108% da margem elástica (estouro de 212 MiB) | tudo vai para o **envelope rotativo** (45,5% dele), **nunca residente**; regra nova: sem linha no orçamento executável, sem RAM | maior locatário isolado: 18,5% do envelope |
| **G4** | o schema de claim **não tinha nenhuma** das correções que o CANON declarava "aplicadas" (grep = 0) | **gerador único de enums** (`enums.yaml` → JSON Schema + SQL + Go + CDDL) com `--check` como portão de CI | **20 enums, 163 valores**; **35 alvos, 0 divergências**; 27/27 ataques, 58/58 positivos |
| **G5** | a decisão do catálogo **não tinha sido executada**: três catálogos rivais e **dois nomes inventados** sem spec em arquivo nenhum | gerador lê as fontes reais; nomes removidos; **I5** torna `reserved` um **nome sem contrato**, fora de `tools/list` | **53 + 13 + 9**; probe: 0 sem `title`, 0 `$ref` de rede, 0 nome inventado |
| **G6** | tabelas duplicadas entre os subsistemas (previsão, mercado, post) | fusão no schema consolidado: `prediction` vira **view**; a rodada referencia o mercado; a âncora migra; o post ganha tabela de claims | carga em banco novo **exit 0, 0 colisão**: 131 tabelas, 139 FKs, 25 triggers, **402 CHECKs** |
| **G7** | **τ = 906 hardcoded em quatro linguagens** — constante de código **não recalibra**, e banco e binário discordavam em silêncio | tabela `verify_config` como fonte única + função de vigência + **trigger** que grava τ e `calib_id` na linha; CI com `grep` = 0 fora dos dados de teste | recalibrar para 970 faz um lance de 950 passar a ser recusado **sem tocar em código**; sem calibração, 999 **não** resolve |
| **G8** | nome de regra de normalização divergente entre código e contrato ⇒ recibo com `man_norm` **que não resolve** | tabela `norm_rule` com FK de captura e de recibo; regex fechada em `-vN` | `@1` e nome não registrado **recusados pelo banco** |
| **G9** | o verificador publicado **aceitava recibo apontando a redação TACHADA** — a checagem estrutural só existia como demo | `lar.go` **v1.1**: normalização aplicada pelo próprio verificador, `locator`, pilha de elementos para tachado, eixo de vigência e digest de cache **obrigatório** | **643 linhas**, SHA `feef864a…`; **10/10** vetores novos |
| **G10** | o digest do estado de cache **não existia** em lugar nenhum, e "desligar por requisição" não é flag | coluna **NOT NULL** nos dois recibos, com coluna **derivada** em bytes; caminho de verificação com **`cache_salt` por requisição** | default aceito · valor inválido recusado · sha256 hex aceito |
| **G11** | **texto da internet virava dinheiro**: quem chamava escolhia vencedor e código, sem hash, captura ou recibo | `oracle_receipt` **NOT NULL** + FK composta para captura oficial nível ≥ C1; **desfecho derivado** por tabela e trigger; pagamento **só em lote FROST 2-de-3** com **teto ≤ `b` do mercado por FK** | **9 recusas + 1 caminho feliz**: sem captura · fonte errada · nível C0 · vencedor à mão · código fora da tabela · acima do teto · teto reescrito · fora de lote · lote com chave de exemplo |
| **G12** | post da casa saía **assinado como verificado** cobrindo texto livre — lavagem de citação **dentro de casa** | texto livre **280 caracteres**, rebaixado a opinião com base; **escopo declarado** no selo; claim obrigatório para post que afirma direito | **5 recusas** |
| **G13** | chave de estado **aleatória por processo** e cota **em memória**: o desenho não sobrevive a N réplicas nem a reinício | chave **derivada da raiz**; cota em tabela; buckets anônimos com teto | **3 recusas + 1 aceite** |
| **G14** | cobertura empírica publicada **sem o tamanho da coorte** — ruído virando garantia | `n_coorte_90d` com `CHECK (NOT publicavel OR >= 100)` | recusado |
| **G15a-e** | unidades e identidades erradas: "6,41 GiB", "4,60 GB", folga de 47.861, **5 personas**, versão do servidor divergente | **6,41 GB (5,97 GiB)** / **4,90 GB (4,56 GiB)** · folga **45.600** · **4 personas, 4 pubkeys** com lado como coluna do lance · versão = versão do catálogo | grep e leitura |
| **G16** | arquitetura de janela deslizante tratada como **pré-requisito do canário**, mas exige plugin que não existe | vira **fase própria com portão** (paridade no G1 + TTFT p95 < 500 ms); **o canário sobe sem ela** | KV de **124.830 tokens** já é o número sem ela |
| **G17** | assinaturas de exemplo **indistinguíveis de reais** (inclusive uma chave pública de 64 hex) | prefixo `EXEMPLO-`, `kid` `example`, lote de pagamento **recusa** chave de exemplo, e o serializador **omite** o campo de prova | grep de placeholder sem prefixo: **0** |
| **G18** | "6,41 → 4,90" lido como derivação automática, sem receita | **duas trilhas explícitas** (artefato quantizado de referência × fallback local) com o efeito numérico do fallback no mapa de VRAM e no KV | portão G1 roda **nos dois artefatos** |
| **G19** | OCR em regime com **três números** em três documentos | **600 GPU-s/dia canônico**; os 4.000 são **pico de backfill classe 4 e SUBSTITUEM**, não somam | linha única no orçamento |

**Quatro achados próprios da frente de correção**, que ninguém tinha visto: a folga de CPU escrita como
arredondamento (436.320) quando a subtração exata dá **435.944 = 5,046 núcleos**, e a fonte passa a ser a
subtração; o schema original de um subsistema **não carrega** sobre o consolidado (índice sobre relação que
virou view, com rollback da transação inteira), o que exigiu versão ajustada; o varredor de cronograma
**truncava a linha antes de classificar**, escondendo a palavra que autoriza — corrigido para classificar na
linha inteira e **separar calendário (proibido) de medida física e medição (permitidos)**; e um conflito de
tipo no digest de cache, resolvido em favor de **texto** com a forma em bytes **derivada**, porque com bytes
puros um estado cujo digest calhasse de ser o sentinela seria **indistinguível de "sem cache"**.

**Varredura de cronograma (D-11').** Todas as referências de calendário foram reescritas: tabela
"Etapa | Dia" vira "GPU-dias de máquina acumulados"; roteiro por trimestre vira fases de soberania com
critério de pronto; "em 180 dias" vira "ao atingir 126.594 páginas"; "resolvidas em 180 d" vira "dentro do
horizonte declarado no mercado"; "7 dias de log" vira "**7 ciclos diários** de log consecutivos". Resultado
do varredor: **24 → 0 violações**. Permanecem, porque **não são cronograma**: quarentena de 30 dias, SLA de
errata, deslocamento de datas na pseudonimização, retenção, "GPU-dias de máquina" e medições do passado.

**Estado de execução de tudo isso.** Schema consolidado em banco novo: **exit 0**, 123 tabelas, 11 views,
127 FKs, 23 triggers, **375 CHECKs**; com os dois arquivos de fusão por cima, **131 tabelas, 139 FKs, 25
triggers, 402 CHECKs, 0 colisão**. Ataques: **94 recusados + 13 caminhos felizes** no arquivo principal e
**33 recusados + 0 violações de integridade** no da arena ⇒ **127 recusas / 27 aceites / 0 falhas**.
Orçamento executável reproduz os dois perfis. Gerador de enums fecha em 35 alvos. Varredor de cronograma
zera. **Nada disso é proposta: foi editado, carregado e rodado.**

**Origem.** H01 §§1–8 · DECISOES-ORQUESTRADOR (adendo, D-2' a D-17) · FIX-A · FIX-B · LEDGER-CORRECOES
(62 decisões da reconciliação + os 19 achados + os 4 próprios = **85**).

---

## V.10 · Tabela-resumo do Volume II

Legenda de status: **código pronto** = existe e roda nesta sessão · **spec** = contrato, schema ou fórmula
fechados, sem motor · **objetivo** = fase com critério de pronto binário.

| Componente | Decisão | Número-chave | Origem | Status |
|---|---|---|---|---|
| Claim (7 tipos) | imutável, endereçado por conteúdo, estado vivo fora do hash | 27/27 ataques · 58/58 positivos | F01 · FIX-A | **código pronto** |
| Enums e τ | **fonte única** gerada; τ em tabela, nunca constante | 20 enums / 163 valores; 35 alvos, 0 divergência; grep de τ literal = 0 | FIX-A · D-13 | **código pronto** |
| Grounding Pack GP/1 | pacote no prompt; prova no sidecar; citação por alça | **1.322 tokens** (1.339 com prognóstico) vs 9.176 e 16.290 | F01 · G01 | **código pronto** |
| Answer Unit v2 | resposta na palavra 1, linter bloqueante | 10/10 regras; 3.258 → 2.767 tokens | F01 | **spec** |
| Cobertura e ausência | célula aberta sem cota é inexprimível | ρ = 0,905; P(falsa ausência) 0,90% em m = 2 | F01 | **código pronto** |
| Feed de Invalidação | empurrão de 8 B/morte + consulta assinada + WebSub | 10.000 ids → **1.213 B**; 104 kB/dia a 40 M claims | F01 · G02 | **spec** |
| Jurisprudência | força = **vetor de efeitos datado**; estado da tese como máquina temporal | 19 forças · 22 efeitos · 85 pares · 15 estados · replay **1.470/1.473** | F03 | **código pronto** |
| Passaporte do Precedente | documento único com variantes e modulação nominal/estrita | Tema 69 com **4 variantes**; 13.391 B, 0 erro | F03 · F07 | **código pronto** |
| Doutrina | posição como fato; trecho ≤ 300; licença da origem | **85,4%** das citações ≤ 300; 39/39 Cedar; 32/32 banco | F02 | **código pronto** |
| Coleta | catálogo máximo cabe; crawler **assina** as próprias requisições | **1.847,3 GiB = 49,6%**; TCU 7,59 GiB em **42 requisições**; CARF 585.274 | G03 | **código pronto** |
| Integridade | WARC + in-toto + COSE na trilha de transparência; C0–C3; R2 com digest de cache | audit kit **3,3 ms**; 20/20 + 10/10; 4-de-5 testemunhas; fiança R$ 5.000 | F08 · D-2' | **código pronto** |
| Recibo `lar.go` v1.1 | recusa redação tachada, normalização desconhecida e recibo sem digest de cache | **643 linhas**, SHA `feef864a…`, 10/10 | FIX-A | **código pronto** |
| Contrato C01–C26 | identidade de fonte única + portão fail-closed | **5 FAIL → 9 PASS**; 87,5% de páginas com dois títulos hoje | F06 | **spec** |
| 30 serviços | 23 sem GPU; top-10 todos 0 GPU no padrão | ≤ **2.900 GPU-s/dia (6,4%)** no modo máximo | F07 | **spec** |
| Soberania | S1–S6 com teste que derruba merge ou serving | BOM **27 componentes / 56 implementações**; índice **0,39 → 0,87** | F11 | **código pronto** |
| Receita do 8B | artefato quantizado de referência + fallback numérico | **6,41 GB (5,97 GiB) → 4,90 GB (4,56 GiB)**; VRAM 15,23 ≤ 15,3 | F11 · D-15 | **spec** |
| Hardware e escalonador | contínuo 24/7 com preempção latchada; RAM arrendável | folga **45.600 GPU-s/dia**; RAM **25,25 GiB** + envelope 6.656 MiB; TLA+ 1.936 estados, 0 erros | F04 | **spec** (TLA+ pronto) |
| Orçamento | **dois perfis** do escalonador | regime **36.185 = 79,4%**, sobra 9.415; construção **80.165** livres, backlog **38,1 GPU-dias de máquina** | FIX-B · D-10' | **código pronto** |
| NVMe e endurance | preço-sombra de desgaste com regime **dormente** justificado | 122,6 GB/dia ⇒ **28,6 anos**; sem o portão, 8,2 | F04 · G05 | **código pronto** |
| Direito como código | âncora com hash; a lei muda ⇒ CI quebra na regra exata | **10.494 linhas** Go · 60 regras · 270 âncoras · 396 versões · **134 testes** · 11 tools em 8,2 ms | F05 | **código pronto** |
| Premeditação | `[P#]` dentro do pacote; `p_exito` **condicional** com linha de condicionamento obrigatória | **262 tokens**; banda Venn–Abers + deriva; **3.480 GPU-s/dia (7,6%)** | G01 | **código pronto** (protótipo) |
| Arena | 4 papéis; juiz **nunca vê o `p`**; mercado abre ancorado | **41,0 GPU-s/rodada**; subsídio cai **303–916×**; **ΔBrier −0,1198** | G01 | **código pronto** (protótipo) |
| Dinheiro com cadeia | resolução exige captura oficial C1+; pagamento só em lote assinado, com teto por FK | 9 recusas + 1 aceite | FIX-B · D-13.3 | **código pronto** (schema) |
| Rede social | motor de semeadura submodular; **um** produto `debate` | **599/dia = 13.681 GPU-s (30,0%)**; semente **36.571 GPU-s = 1,64 GPU-dia** | G02 · D-10' | **código pronto** (protótipo) |
| Contrato da API social | 9 rotas + 11 tools + 7 kinds federados | 11/11 (depois 14/14) adversariais recusados | G02 | **spec** |
| EnaEval M2M | multi round-trip com estado assinado; sem sessão | **53 + 13 + 9**; **43 testes**; 402 só em 3 ferramentas | G04 | **código pronto** |
| Catálogo único | gerado, com I1–I5 fail-closed | 0 `$ref` de rede · 0 sem `title` · 0 nome inventado | FIX-A · D-5' | **código pronto** |
| `K_root` | chave raiz da pessoa jurídica, Shamir 3-de-5 | placeholders com prefixo `EXEMPLO-`; grep = 0 | D-7 | **objetivo (obra nº 1)** |
| Experimento E1 (Qwen3.5) | candidato com **três portões**, nunca base | KV **4,5× menor**; replay de cauda **primeiro** | D-1 · G05 | **objetivo** |
| Dez "adotar agora" | métrica de *warrant*, KV certificado, digest de cache, trilha enganosa, OPD→RLVR, interação tardia, currículo, segurança por papel, merge sobre 4 bits, λ vetorial | cada um com experimento e portão | G05 | **objetivo** |
| Fases de coleta A–F | por objetivo, com critério de pronto mensurável | **2,34 M núcleo-s = 6,69 CPU-dias**; ≈ 43,5 k GPU-s | G03 | **objetivo** |
| Fases de soberania SOB-0…4 | por objetivo; índice como view sobre o vinculado | 0,39 → 0,57 → 0,65 → 0,73 → **0,87** | F11 · D-11' | **objetivo** |

**Ordem dos objetivos (D-17), que é a espinha da tasklist.** `K_root` → enums e τ únicos → recibo v1.1 →
schema consolidado → catálogo único → servidor MCP v0 público → monorepo → **8B servido + verificador
calibrado (no perfil `construcao`)** → escalonador real → conteúdo vivo → premeditação → rede social e arena
unificadas. Depois dos doze, e não antes: o backlog de compactação, o Experimento E1 e o pós-treino de
manutenção na folga residual.

**O invariante que resume o Volume II.** Toda afirmação que o EnaEval faz a uma IA do mundo é **rastreável a
bytes atestados de fonte oficial, datada no eixo certo, verificável offline por terceiro em milissegundos, e
invalidável quando o direito muda** — e nenhum caminho leva texto da internet a dinheiro sem captura
atestada. Onde isso não é possível, o sistema **abstém com forma canônica e diz por quê**. É essa
propriedade, e não a API paga, que faz a IA voltar.


---

# APÊNDICE A — CANON v4.1 (fonte única de números)

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

---

# APÊNDICE B — DECISÕES DO ORQUESTRADOR (D-1…D-17 e arbitragem do crítico)

# DECISÕES DO ORQUESTRADOR (Fable 5.1, engenheiro-chefe) — 22/09/2026
Palavra final sobre os conflitos que subiram das ondas F e G. Hierarquia: CORRECOES-DONO > estas decisões >
CANON-v4 > LEDGER > relatórios. O crítico (Onda 9) pode atacar estas decisões; se derrubar com evidência, eu reviso.

## D-1 Base de serving: Qwen3-8B denso PERMANECE; Qwen3.5 (4B/9B) vira Experimento E1 com portão
Evidência a favor do Qwen3.5 (G05, config.json lido ao vivo): KV/token 4,5× menor (16,0 KiB vs 72,0 KiB),
MTP nativo, 262k ctx, Apache-2.0, BFCL-V4 66,1 / TAU2 79,1 (4B empata com 9B em TAU2). É grande demais para
ignorar. Contra: (a) prefix caching — condição de viabilidade do CANON — não se aplica ao estado recorrente GDN
sem Tail-Replay (arXiv:2608.30310); (b) F11 provou que o pipeline LoRP/Minitron/EXL3/ModelOpt-NVFP4 foi
validado em denso, não em híbrido; (c) vocabulário 248.320 obriga refazer a cirurgia do D04.
DECISÃO: o EnaEval nasce em Qwen3-8B denso (pipeline provado). E1 = Qwen3.5-9B/4B entra como candidato de
promoção pelo registry (C05/G06) com três portões: (1) Tail-Replay ou equivalente mantendo TTFT p95 < 500 ms
com cache quente em vLLM ≥ 0.30 em sm_120; (2) QLoRA/FP8 e quantização W4A4 NVFP4 funcionando no híbrido
com KL de calibração jurídica ≤ a do 8B denso; (3) não-inferioridade G2 no WikiJurídica-Bench + G1 no artefato
quantizado. Se passar, substitui o residente e o KV liberado vai para concorrência. A proibição do CANON
"Qwen3.5-4B como base" fica restrita ao VERIFICADOR (encoder é mmBERT) e ao pipeline de poda até E1 fechar.

## D-2 Reprodutibilidade R2 sob prefix caching (F08 × G05 arXiv:2609.04748)
DECISÃO: (a) o caminho de VERIFICAÇÃO (V⁴, extração para claims, votação 3-run) roda com prefix caching
DESLIGADO por requisição (vLLM permite por request); custa < 3% do orçamento (F01: verificação é CPU/54M;
só a extração 8B é afetada). (b) Todo citation_receipt e prediction_receipt carrega `cache_state_digest`
(hash do estado de cache usado, ou "none"). (c) Serving comum mantém prefix caching. Sem isso, R2 é falso.

## D-3 KV em ⟨PROVA⟩: reescrever a regra
"Compressão de KV proibida em ⟨PROVA⟩" → "EVICTION de token proibida em ⟨PROVA⟩; quantização preservadora de
cobertura permitida sob certificado (WitCert, arXiv:2607.28699), com fingerprint no recibo". Ganho: 1,88×
tokens na mesma memória sem perder o suporte da cadeia (arXiv:2608.01631).

## D-4 Pós-treino: OPD → RLVR em duas etapas sequenciais
CANON dizia "on-policy distillation de manutenção". Passa a: etapa 1 = OPD (com IER, arXiv:2609.24432),
etapa 2 = RLVR GSPO-DrC com penalidade de vigência −0,60 (D05) elevada a INVARIANTE (arXiv:2608.14610: RL
geral piora raciocínio temporal — o portão G5/WJ-Retro é obrigatório entre as etapas). GrowMTP entra como
experimento. Scale-QLoRA (arXiv:2609.04526) é obrigatório para merge sobre NVFP4 (merge ingênuo perde até 39 pp).

## D-5 Catálogo de ferramentas: o GERADOR do G04 é canônico
Dois catálogos nasceram (G06 tools/catalog.json manual: 37 + 20 reservados; G04 cmd/enaeval-catalog gerado:
45 + 3 aliases com 4 invariantes fail-closed). Código vence prosa. DECISÃO: `cmd/enaeval-catalog` passa a
ingerir também os schemas REAIS de G01 (6 tools) e G02 (11 tools) e os nomes reservados do G06 que não
tenham spec; o catálogo único resultante vive em research-v4/tools/catalog.json (sobrescreve o do G06) e
o G06 fica como fonte dos nomes reservados. Regra permanente: tool sem schema autocontido + title não entra.

## D-6 `dialog` na camada 4 (agente), não na 5 (superfície) — regra de CI `wj/agent/dialog ⊬ wj/serve`
Aceito o G04: a pergunta de esclarecimento fixa o insumo do cálculo; se fosse gerada por LLM na superfície,
seria induzível por injeção. Elicitation por servidor está proibida na rev. 2026-07-28 (SEP-2322/2575);
o multi round-trip com `requestState` HMAC é o mecanismo.

## D-7 K_root é o objetivo nº 1 de qualquer fase de execução
Sem chave raiz (Shamir 3-de-5, B06) não há recibo real, cota por DID, 402 que liquide, Web Bot Auth, nem
crawler assinado (G03). Todo artefato hoje usa chave de EXEMPLO e está marcado. A tasklist começa por isso.

## D-8 Armazenamento: o plano do G03 (1.847 GiB = 49,6%) substitui os três números anteriores
Correção ao F04 §6 (cota pg duplicada) aceita. O 1 TB não é espelho: é arquivo do insubstituível (chaves,
Merkle, WAL, corpus canônico) + do morno que a poda remove. Ordem de poda: WARC de diário municipal → PDF
de tese acadêmica. λ_tbw ≈ 0 no regime atual (G05): tiering pode ser agressivo.

## D-9 λ_gpu por classe e por hora
arXiv:2608.23986 (G05): sob congestão, rotear ao 4B pode aumentar o gasto por citação verificada. O preço-
sombra deixa de ser escalar único: λ_gpu[classe][hora]. Fonte única continua `econ.LambdaGPU()` (E07),
agora com assinatura (classe, hora).

## D-10 Rede social e arena: números do G01/G02 entram no CANON
599 threads/dia (20,6% da folga), 120 rodadas de arena/dia (10,8%), prognóstico em 11.600 chamadas/dia (7,6%),
semente fria 36.571 GPU-s (1,64 dia), submercados de horizonte ≤ 24 h obrigatórios, promotor só onde a lei
prevê (tabela de decisão CPC 178 / LACP 5º §1º / LIA 17 / CF 129 I), juiz-IA nunca vê o p do caso.

## D-11 Sem dias, semanas ou meses em NENHUM documento v4
Toda referência temporal de execução é FASE/OBJETIVO com critério de pronto. Onde um cálculo precisa de
duração (backlog de GPU em dias de máquina), é medida física do sistema, não cronograma — escrever
"X GPU-dias de máquina", nunca "em X dias".

## D-12 Planalto: regra de normalização `wj-norm/f5-cspm-tail-v1` (F06) é canônica; NFC obrigatório (F08)

# ADENDO — ARBITRAGEM DOS 19 ACHADOS DO CRÍTICO (H01), 22/09/2026
Li o H01. Aceito 19/19 como graves. Veredito sobre as minhas decisões: D-5 e D-10 DERRUBADAS e reescritas;
D-2, D-6, D-11, D-12 AJUSTADAS conforme H01; D-1, D-3, D-4, D-7, D-8, D-9 MANTIDAS.

## D-5' Catálogo: o gerador do G04 passa a ler as specs REAIS de G01 e G02
Fontes do `cmd/enaeval-catalog`: C03 (tipos Go), F02, F03, F05, F07, **G01-code/schemas/mcp-g01.json**,
**G02-code/mcp-social-tools.json**; os nomes reservados do G06 sem spec entram como `reserved` (não como stub
inventado); `wj_arena_settle` e `wj_social_reputation` são REMOVIDOS. Resultado esperado: 53 ferramentas
com schema + 8 reservadas. O `research-v4/tools/catalog.json` manual do G06 é sobrescrito pela saída do gerador.

## D-10' Debate é UM produto com dois perfis de custo
Thread (G02) e rodada de arena (G01) são o mesmo objeto (`debate`) com perfil `leve` (18,29 GPU-s, lote ×4,
sem os 4 papéis assimétricos) ou `arena` (41,0 GPU-s; 46,9 com parecer do MP). Meta de regime:
599 debates/dia dos quais 120 em perfil arena ⇒ 479×18,29 + 120×41,0 = 13.681 GPU-s/dia (30,0% da folga).
Orçamento de regime consolidado (GPU-s/dia): F01 fluxo 10.622 + F03 922 + F02 580 + G01 prognóstico 3.480 +
debates 13.681 + F07 serviços 2.900 + G03 OCR 4.000 = 36.185 = 79,4% da folga de 45.600 ⇒ 9.415 GPU-s/dia
para treino em regime. O backlog de construção (3,05 M GPU-s) NÃO cabe em regime ⇒ existem DOIS PERFIS DO
ESCALONADOR: `construcao` (treino/indexação prioritários; semeadura a 25% = 150 debates/dia; OCR a 50%)
até o backlog fechar (≈ 35,7 GPU-dias de máquina — medida física), depois `regime`. A transição é objetivo
com critério de pronto (backlog = 0), não data. G03 fase B: 1,2 M núcleo-s/dia é ERRO de unidade (1,74× a CPU
inteira) — reescrever como total de fase espalhado pela folga de 5,05 núcleos. RAM nova (3.030 MiB) > margem
(2.818 MiB) ⇒ entra no envelope rotativo de 6.656 MiB (F04), não como residente.

## D-2' cache_state_digest e cache_salt
`citation_receipt` e `prediction_receipt` ganham `cache_state_digest TEXT NOT NULL DEFAULT 'none'`;
o caminho de verificação usa `cache_salt` por requisição (é o mecanismo real do vLLM) e registra o digest.
lar.go valida a presença do campo (v1.1 do recibo).

## D-6' e G04 stateless
HMAC do `requestState` com chave DERIVADA de K_op (HKDF, rotação junto com K_op), não por processo;
cota por DID em Postgres (tabela `quota_did`), não em memória. Só assim N réplicas do servidor são equivalentes.

## D-11' Varredura obrigatória de cronograma
Arquivos com violação (H01 §4): F04 §4.2 (tabela "Etapa | Dia" → "Etapa | GPU-dias de máquina acumulados"),
F11 roadmap por trimestre (→ por FASE de soberania S0–S4 com critério de pronto), CANON-v4 §4:185
(→ mesma reescrita), G02 "em 180 dias" (→ "ao atingir 126.594 páginas"), G04 "180 d" (→ "expiração = fase
de rotação de K_op"). Durações físicas (GPU-dias de máquina, TTFT, latência) permanecem.

## D-12' Nome da regra de normalização
`G03-code/canon/canon.go` usa `wj-norm/f5-cspm@1` → trocar por `wj-norm/f5-cspm-tail-v1`; regex do SCHEMA-v4
passa a aceitar SÓ o canônico.

## D-13 Verdade para a IA: cinco correções estruturais obrigatórias (H01 G4, G9, G11, G13, G14)
1. `F01-code/knowledge-claim.schema.json` recebe TODAS as extensões que o CANON §7 declara: forca927 += III_A_resp_relevancia,
   administrativa_vinculante; 15 estados de tese; mode condicional; oficial_tpu; assertion_es; perfil cp1;
   `origin` no envelope; ProcedureClaim.kind += prognostico; fonte.kind += {tcu_bulk, carf_solr, ckan, oai,
   eurlex, hudoc, ccidx, lexml, senado}. Um GERADOR ÚNICO de enums (`enums.yaml` → JSON Schema + SQL + Go)
   passa a ser a fonte; divergência quebra o CI.
2. `lar.go` (B06/F06) implementa a checagem estrutural (man_norm + locator + rejeição de redação tachada
   `<strike>/<s>/line-through` + cache_state_digest) — ~40 linhas — com vetores novos; C20 do F06 passa a
   apontar o novo SHA.
3. `resolution.oracle_receipt` vira NOT NULL com FK composta para `capture` (fonte datajud, nível ≥ C1);
   tabela `tpu_outcome`; payout só via Plano-T (FROST) e `≤ b`. Texto da internet NUNCA chega a dinheiro
   sem captura atestada.
4. G02: segmentos `text` de post NÃO saem assinados como `v4: pass` sem verificação; texto livre é `opinion`
   (não assinado como verificado) e só claims com recibo recebem `v4: pass`.
5. τ é COLUNA/CONFIG (fonte única `verify.Tau()`), nunca const/CHECK hardcoded — corrigir G01 (CHECK + const)
   e G02 (const + schema const). SCHEMA-v4: `tau_milli` na linha do recibo (E07 I-VERIFY-1) permanece.

## D-14 Tabelas duplicadas G01/G02 × SCHEMA-v4
`prediction`/`arena_round` (G01) e `prediction_receipt`/`market` (SCHEMA-v4) se fundem: `prediction_receipt`
ganha `processo_hash NULLABLE` (wj_predict_case não tem processo) + `celula`/`counter` UNIQUE mantidos;
`arena_round` referencia `market`. `social_post` ganha as colunas que tornam o Post do G02 exprimível
(claims[] minItems 1 via tabela `social_post_claim` NOT NULL-checked por trigger). SCHEMA-v4.1 resulta.

## D-15 Unidades, receita e identidades
"6,41 GiB" → "6,41 GB (5,97 GiB)" em todo lugar. Receita do 8B parte do artefato `nvidia/Qwen3-8B-NVFP4`
(hash no BOM) + cirurgia de vocabulário → 4,90 GB; o fallback BF16→NVFP4 local (5,23 GB) só se o artefato
sumir e obriga reduzir KV. Personas: exatamente 4 papéis (advogado, juiz, promotor, jurista) — o "advogado"
tem sub-papel autor/réu com a MESMA identidade; 4 pubkeys, não 5. Assinaturas placeholder recebem prefixo
`EXEMPLO-` e kid `example` para nunca parecerem reais.

## D-16 Toolchain
Monorepo `wj` com `go 1.25` no go.mod (go-sdk exige ≥ 1.25) e `toolchain go1.25.x` pinado; os módulos de
pesquisa mantêm seus go.mod até a migração (objetivo da tasklist).

## D-17 Ordem dos 12 objetivos: ACEITA a do H01 §7
K_root → enums/τ únicos → recibo v1.1 (lar.go) → SCHEMA-v4.1 → catálogo único (D-5') → MCP v0 em /mcp2 →
monorepo wj → 8B servido + verificador calibrado (perfil construção) → wj/serve → conteúdo vivo F01+G03 →
premeditação → rede social + arena unificadas. A tasklist obrigatória segue esta espinha.
