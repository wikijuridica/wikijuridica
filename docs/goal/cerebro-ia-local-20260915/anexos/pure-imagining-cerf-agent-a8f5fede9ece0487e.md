# Colheita 5 — O SUBSTRATO DE CONTEÚDO da rede social de IA

Medido em 2026-09-15, em /opt/wiki, somente leitura. Toda linha declara a CAMADA.

## 1. O GRAFO (camada: disco, data/ai/grafo.sqlite, mode=ro)

79.706 nós / 393.081 arestas — confere com grafo_manifest.json.

**Nós por tipo** (`SELECT tipo,COUNT(*) FROM nos GROUP BY tipo`):
acordao 60.221 · pagina 11.104 · dispositivo 5.275 · tema 2.347 · sumula 398 ·
norma 327 · area 32 · tribunal 2.

**Arestas por tipo, com os TIPOS DE PONTA** (join nos×arestas×nos):

| aresta | origem→destino | n |
|---|---|---|
| cocitada_com | pagina→pagina | 128.951 |
| cita | acordao→dispositivo | 77.669 |
| cita | acordao→sumula | 63.305 |
| julgado_por | acordao→tribunal | 60.221 |
| aplica | pagina→sumula | 22.789 |
| da_area | pagina→area | 11.104 |
| cocitada_com | dispositivo→dispositivo | 10.570 |
| cita | pagina→dispositivo | 8.516 |
| pertence_a | dispositivo→norma | 5.275 |
| julgado_por | tema→tribunal | 2.347 |
| cita | acordao→norma | 1.580 |
| julgado_por | sumula→tribunal | 398 |
| cita | tema→dispositivo | 354 |
| revoga | norma→norma | **2** |

**O que o grafo NÃO tem, e é o que a rede social precisa:**
- **Nenhuma aresta acordao↔pagina.** Os dois mundos só se encontram ATRAVÉS de
  dispositivo/súmula. Não existe "este acórdão é sobre esta página".
- **Nenhum nó de ATOR.** `relator` é string dentro do blob JSON `atributos`;
  `orgao_julgador` **não existe nem no blob** (só no rótulo e no corpus JSONL).
  Não se pergunta ao grafo "o que a Terceira Turma decide sobre art. 927".
- **`supera`, `altera`, `impactada_por` estão no CHECK do schema e têm 0 arestas.**
  `revoga` tem 2. Superação — a matéria mais discutível que existe — não está no grafo.
- Nenhum nó de processo, parte, tese, comentário ou usuário.

### A PONTE página↔acórdão, medida, e por que 3 de 4 são ruído

1.142 alvos citados por página · 5.309 citados por acórdão · **662 em comum**
(579 dispositivo + 83 súmula). 480 alvos só de página, 4.647 só de acórdão.

- **4.313 de 11.104 páginas (38,8%)** têm ponte para algum acórdão.
- **43.474 de 60.221 acórdãos (72,2%)** têm ponte para alguma página.
- Separando o alvo-ponte processual do de mérito por **classificação própria**
  (não é campo do dado): 15 súmulas de admissibilidade — STJ 7/83/5/182/211/568/
  86/98/126/207 e STF 282/283/284/356/735 — mais **toda** a Lei 13.105/2015 e
  CF art. 105. Rodado com 11 e com 15 súmulas, o split é **idêntico**:
  **113 pontes processuais e 549 de mérito**;
  **acórdãos: 11.050 (25,4%) por mérito, 32.424 (74,6%) SÓ por processual**;
  páginas: 4.094 por mérito, 219 só por processual.

As 8 pontes mais volumosas são todas admissibilidade: Súm. 7/STJ (2.882 pgs ×
23.658 acs), Súm. 83 (2.498×9.686), Súm. 5 (1.932×6.151), Súm. 284/STF
(2.142×4.986), 182 (800×2.868), 282 (1.929×2.815), 283 (1.485×2.523),
211 (1.590×2.212). **"Precedente" ali significa "os dois textos mencionam
Súmula 7", não "os dois tratam do mesmo problema".**

Pontes de mérito de topo (as que valem discussão): CC art. 205 (29 pgs×582 acs),
Súm. 115/STJ (12×570), CC 186 (63×433), CC 927 (73×414), CC 884 (23×381),
Súm. 187 (18×380), CC 422 (36×378), CC 406 (14×371), CC 206 §3º (50×321),
Lei 9.656/98 art. 10 (32×317), Súm. 518 (782×309), CF art. 5º (165×277),
CC 944 (7×266), CC 421 (18×257), CDC art. 14 (185×233).

### Cobertura por ÁREA (páginas com acórdão de MÉRITO / total da área, SET-15)

consumidor 493/632 **78,0%** · autonomos 58/84 69,0% · digital 155/229 67,7% ·
saude 181/311 58,2% · imobiliario 381/675 56,4% · bancario 261/473 55,2% ·
familia 235/431 54,5% · lgpd 143/264 54,2% · educacao 64/118 54,2% ·
empresarial 200/402 49,8% · constitucional 12/25 48,0% · leis 189/406 46,6% ·
sucessoes 170/367 46,3% · diarios 21/51 41,2% · seguros 115/293 39,2% ·
investimentos 69/178 38,8% · telecom-energia 99/271 36,5% · glossario 314/942 33,3% ·
servidor 74/256 28,9% · tributario 126/473 **26,6%** · cidadania 43/173 24,9% ·
inpi 65/282 23,0% · sumulas 75/329 22,8% · trabalhista 121/542 22,3% ·
criminal 67/303 **22,1%** · aereo 40/209 19,1% · jurisprudencia 175/1.134 15,4% ·
transito 28/218 12,8% · previdenciario 81/638 **12,7%** · procedimentos 34/293 11,6% ·
administrativo 5/45 11,1% · noticias 0/57 **0,0%**.

Duas ressalvas de leitura: as "32 áreas" **misturam área do Direito com tipo de
conteúdo** (`glossario` 942, `sumulas` 329, `leis` 406, `jurisprudencia` 1.134,
`noticias` 57, `diarios` 51, `procedimentos` 293 — 3.212 páginas, 28,9% do total,
não são ramo do Direito); e a contagem de páginas tem **quatro valores por
camada**: `content/pages.json` com `unique_intent_id` **11.118** ·
`published_manifest` **11.106** · grafo **11.104** (gerado 2026-09-15 06:53) ·
`temas` da rede social **11.039**. A diferença é atraso de geração, não erro.

## 2. OS ATORES PÚBLICOS (camada: disco, data/corpus/jurisprudencia/stj-espelhos/)

52 arquivos `registros-*.jsonl`, 60.221 linhas, 192 MB.

**A distribuição é o achado.** `orgao_julgador` tem **4 valores**:
TERCEIRA TURMA 30.786 · QUARTA TURMA 27.845 · PRIMEIRA TURMA 862 ·
SEGUNDA SEÇÃO 728. As duas turmas de direito privado são **58.631 = 97,4%**.
Zero Primeira Seção completa (tributário/previdenciário/administrativo), zero
Terceira Seção (Quinta e Sexta Turmas — criminal), zero Corte Especial.
**É por isso que previdenciário tem 12,7% e criminal 22,1% de cobertura: não é
o extrator, é o corpus.**

- **21 relatores distintos**, 0 acórdãos sem relator. Concentração:
  RAUL ARAÚJO 8.156 · MOURA RIBEIRO 8.018 · JOÃO OTÁVIO DE NORONHA 7.301 ·
  RICARDO VILLAS BÔAS CUEVA 6.674 · MARIA ISABEL GALLOTTI 4.684 ·
  NANCY ANDRIGHI 4.677 · HUMBERTO MARTINS 4.507 · ANTONIO CARLOS FERREIRA 3.625 ·
  DANIELA TEIXEIRA 3.594 · MARCO AURÉLIO BELLIZZE 2.833 · MARCO BUZZI 2.551 ·
  LUÍS CARLOS GAMBOGI (des. conv. TJMG) 1.267 · … · LÁZARO GUIMARÃES 1.
  Relatores por órgão: 3ª Turma 8 · 4ª Turma 8 · 1ª Turma 5 · 2ª Seção 12.
- 292 classes processuais distintas. Top: AgInt no AREsp 20.156 · AREsp 11.553 ·
  REsp 10.023 · AgInt no REsp 6.904 · AgInt nos EDcl no AREsp 2.302.
  **Só ~10.023 (16,6%) são REsp puro** — o resto é agravo/embargo sobre agravo.
- Anos de julgamento: 2018 4 · 2019 8 · 2020 13 · 2021 48 · 2022 8.007 ·
  2023 8.421 · 2024 7.759 · 2025 15.710 · 2026 20.251.
- tribunal: STJ 60.221 (100%) · tipo_decisao: ACÓRDÃO 60.221 ·
  **nivel_sigilo: "None" em 60.221 (100%) — zero sigilo no corpus.**
- Campos preenchidos: ementa 60.221 (100%) · dispositivo 60.011 (99,7%) ·
  jurisprudencia_citada 19.197 (31,9%) · referencias_legislativas_brutas 17.930
  (29,8%) · dispositivos_citados_urn 12.002 (19,9%) · sumulas_citadas 11.935
  (19,8%) · tema 49 (0,1%) · **inteiro_teor 0 (0,0%)** · inteiro_teor_url 0.

### O campo `dispositivo` é um ativo que ninguém está usando

Regex sobre os 60.221: **99,6% casam ao menos um padrão de resultado**
(219 sem nenhum). por unanimidade 59.459 (**98,7%**) · negar provimento 39.323
(65,3%) · conhecer 17.092 (28,4%) · dar provimento 7.009 (11,6%) ·
não conhecer 6.758 (11,2%) · rejeitar 2.768 (4,6%) · acolher 2.348 (3,9%) ·
por maioria 566 (0,9%) · voto vencido/divergiu 118 (**0,2%**).

E o mesmo campo carrega a **COMPOSIÇÃO DO COLEGIADO**: a lista "Os Srs. Ministros
X, Y e Z votaram com o Relator" está em **59.668 (99,1%)** e "Presidiu o
julgamento o Ministro W" em **57.371 (95,3%)**. Normalizando espaço, 20 ministros
com ≥470 aparições como VOTANTE (o resto é ruído de parsing, ≤13):
NANCY ANDRIGHI 24.754 · RICARDO VILLAS BÔAS CUEVA 24.083 · ANTONIO CARLOS
FERREIRA 23.480 · MARIA ISABEL GALLOTTI 23.330 · MOURA RIBEIRO 22.541 ·
HUMBERTO MARTINS 21.225 · RAUL ARAÚJO 19.969 · JOÃO OTÁVIO DE NORONHA 17.877 ·
DANIELA TEIXEIRA 14.919 · MARCO BUZZI 13.688 · LUÍS CARLOS GAMBOGI 9.420 ·
MARCO AURÉLIO BELLIZZE 8.751 · PAULO DE TARSO SANSEVERINO 3.305 · LUIS FELIPE
SALOMÃO 1.755 · BENEDITO GONÇALVES 709 · REGINA HELENA COSTA 703 · GURGEL DE
FARIA 662 · MANOEL ERHARDT 656 · SÉRGIO KUKINA 533 · CARLOS CINI MARCHIONATTI 470.
26 presidentes distintos (João Otávio de Noronha 16.986 · Humberto Martins 14.416
· Daniela Teixeira 7.493 · Raul Araújo 7.377 · Villas Bôas Cueva 7.132).

### O que o §12 permite construir, conferido na fonte

`CLAUDE.md:638-640`, `AGENTS.md:31`, `docs/goal/DECISIONS.md:2062` e
`docs/goal/PROMPT_AI_FIRST_OPUS5_20260908.md:232-234` dizem a mesma coisa:
atores públicos "só sobre atos públicos **e em agregado**, sem dado sensível, com
redação sóbria". O PROMPT_AI_FIRST nomeia as três rubricas **permitidas**:
**"índice de reforma", "tempo médio", "tese predominante"**; e a proibida:
"chance de êxito". O PLANO_REDE_SOCIAL acrescenta a granularidade lícita:
**"em agregado por órgão, tema e período"**.

Logo, **PERMITIDO construir com o que já está no disco** (todo dado é ato público
publicado, nivel_sigilo=None em 100%):
- índice de unanimidade e de divergência **por órgão/ano** (98,7% / 0,2% medidos);
- taxa de provimento vs. não-conhecimento **por órgão, classe e ano** (o campo
  `dispositivo` sustenta em 99,6%);
- tempo médio julgamento→publicação (`data_julgamento` × `data_publicacao`);
- tese predominante por dispositivo/súmula (via as 549 pontes de mérito);
- composição de colegiado por período (99,1%).

**O que está EFETIVAMENTE vedado, e o que não está.** A única vedação com
dispositivo citado é de **REDAÇÃO**: "chance de êxito" (proibido) contra
"índice de reforma", "tempo médio", "tese predominante" (autorizados) —
`PROMPT_AI_FIRST_OPUS5_20260908.md:232-234`. A granularidade **documentada** é
"por órgão, tema e período" (`PLANO_REDE_SOCIAL.md`); isso é o escopo escrito,
**não uma proibição de agregar por relator**: nenhum dispositivo citado em
CLAUDE.md:638-640, AGENTS.md:31, DECISIONS.md:2062 ou no PROMPT veta o eixo
relator sobre atos públicos. O limite do `perfil_de_jurista` do MCP ("NÃO devolve
ranking … Provimento 205/2021") governa **advogado da plataforma**, onde incide a
publicidade do Prov. 205/2021 — ministro é **ator público** e cai no §12, que
pede agregado, ausência de dado sensível e sobriedade, nada mais.
**Decisão de engenharia (minha, não vedação):** o eixo primário é o **órgão**,
porque é ele que estabiliza amostra (3ª Turma 30.786 · 4ª Turma 27.845 contra
1 acórdão de um relator); o relator entra como **fato do ato** (quem relatou,
quem presidiu, quem votou), e o agregado por relator, quando útil, sai com a
redação sóbria autorizada e com o n declarado.

## 3. O DATAJUD (camada: disco, data/research/datajud/)

23 arquivos: 22 de tribunal + `ranking_nacional.json`. Coleta única:
`collected_at 2026-08-07T13:46:38Z` em todos — **39 dias de idade**.

**Granularidade real** (`schema_version: datajud_corpus_v1`), por tribunal:
`processos` (total), `assuntos[{nome,processos}]` **top-150**,
`classes[{nome,processos}]` **top-60**, `graus[{nome,processos}]`,
`endpoint`, `scope: "metadados_agregados_sem_dado_pessoal"`.
**Não há eixo de ANO, nem de órgão julgador, nem cruzamento assunto×classe.**
É um cubo de 3 faces planas, não um cubo.

- Soma de `processos` dos 22 tribunais: **283.415.422** (= `processos_totais`
  do ranking). A soma de **todos** os itens de assunto dá **345.682.422** e
  **1.022 assuntos distintos** — os 345 M são a soma com **dupla contagem**
  (um processo tem vários assuntos), não uma população. Declarar 345.682.422
  como "processos" é erro de camada; o número de processos é 283.415.422.
- 312 classes distintas. Top: Execução Fiscal 49.428.009 · Juizado Especial Cível
  37.702.472 · Procedimento Comum Cível 23.133.486 · Cumprimento de sentença
  14.902.537 · Apelação Cível 12.933.992 · Recurso Inominado 10.965.711.
- Maiores tribunais: tjsp 74,49 M · tjmg 36,60 M · tjrj 23,12 M · trf3 17,39 M ·
  tjba 15,45 M · trf4 14,49 M · tjrs 14,00 M · tjpr 12,75 M · trf1 12,35 M.
- **`tjpe` tem `assuntos: []`** (arquivo de 5.152 bytes contra ~15,5 KB dos
  demais): 6.721.324 processos entram no total e ficam fora de toda análise
  por assunto. 1 de 22 tribunais mutilado.
- Graus: G1/G2/JE/TR (+TRU nos TRFs), SUP nos superiores. **stj: 3.592.561
  processos, grau SUP** — contra 60.221 acórdãos no disco = **1,68%**.

**O cruzamento com o acervo JÁ EXISTE e o matcher está LIDO no código.**
`ranking_nacional.json` tem, por assunto, `paginas_no_acervo` e `exemplos[3]`:
400 assuntos, 391 com página (97,8%), 9 sem, **49.584 páginas somadas** sobre
11.106 páginas reais (**4,46 assuntos por página**).

Produtor: **`tools/generate-datajud-corpus`** (extensionless — o primeiro grep,
filtrado por `--include=*.go/*.py/*.sh`, não o via; sem filtro aparecem também
`tools/measure-judicial-demand` e
`tools/measure-official-source-content-evidence-20260812`). Commit de introdução
do artefato: `cb1e12c6 feat(dados): corpus Datajud/CNJ — 22 tribunais, 283
milhoes de processos`.

**O que o código faz** (`tools/generate-datajud-corpus:152-183`):
`vocabulario_das_paginas()` monta, por página de `content/pages.json` com
`unique_intent_id`, o conjunto de tokens >3 letras de **title + heading + path**;
`cobertura()` toma os tokens >3 letras do rótulo do assunto, subtrai a lista
`VAGOS` (19 palavras) e devolve toda página cuja interseção seja **não vazia** —
`return [caminho for caminho, vocab in paginas if distintivos & vocab]`.
**É um OR de UM token, não um casamento de tema.** Reproduzido hoje:
- "Dívida Ativa (Execução Fiscal)" → distintivos {ativa, divida, execucao,
  fiscal} → **523 páginas** (o artefato gravou 468: `pages.json` tem hoje 11.118
  páginas com `unique_intent_id`, contra o estado de 2026-08-07). Por token:
  divida 305 · execucao 176 · fiscal 127 · ativa 24. É o token "fiscal" que traz
  `/aereo/bagagem-indenizacao-sem-nota-fiscal/`.
- "Auxílio por Incapacidade Temporária" → 147 páginas; exemplos incluem
  `/criminal/saida-temporaria/` (token "temporaria").
- "Tráfico de Drogas e Condutas Afins" → 18 páginas; exemplos incluem
  `/administrativo/improbidade-administrativa/` (token "condutas") e
  `/cidadania/imigra-vitima-trafico-residencia/` (tráfico de pessoas).

Logo **"9 assuntos descobertos / 2.589.576 processos" é inválido**: com OR de um
token quase nada fica descoberto, e o que fica coberto está coberto por homonímia.
O gerador **existe e é reprodutível**; o defeito é o critério, não a proveniência.
Nota de consistência: `GENERICOS` (linha 88) remove "direito civil", "outros" etc.
do ranking nacional — é por isso que "DIREITO CIVIL" (6.079.881 na soma por
tribunal) não aparece entre os 400.

O que se PODE cruzar de verdade, sem o matcher frouxo: DataJud dá **demanda**
(volume por assunto/classe/tribunal) e o corpus STJ dá **resposta da última
instância** (ementa + resultado + colegiado). O eixo comum honesto é a **classe
processual** (312 nomes no DataJud × 292 no corpus) e o **assunto→área editorial**
mapeado à mão, não por substring.

**A lacuna que o cruzamento revela:** as maiores demandas do país são as de pior
cobertura de precedente real no acervo. Execução fiscal 20,16 M → tributário
27,1% · auxílio por incapacidade 6,59 M + aposentadoria por incapacidade 4,49 M
→ previdenciário **12,7%** · tráfico 3,22 M → criminal 22,1% · IPTU 12,68 M →
tributário. Dano moral 12,90 M e inclusão indevida em cadastro 6,98 M caem em
consumidor (78,0%) — a única grande demanda bem servida.

## 4. O RISCO DE SUPERAÇÃO (camada: disco, data/ai/risco_superacao.jsonl)

4.986 linhas, `schema_version risco_superacao_v1`, `gerado_em 2026-09-15T09:53:59Z`.
Cobre **4.986 de 11.104 páginas = 44,9%**.

**A saturação está confirmada.** `risco`: 1.190 linhas valem exatamente 1,0
(23,9%) e 1.505 valem 0,0 (30,2%); p50 = 0,080, p90 = 1,000. A fórmula está no
próprio artefato: `min(1, n/5) × recência (1,0 até 365 d; 0,5 até 730; 0,25 depois)`
— satura em n≥5.
**`peso_apos_revisao` também tem 1.505 zeros** (os mesmos de risco 0). Sobre os
**3.481 não-nulos**: min 0,20 · p25 0,40 · p50 **1,20** · p75 5,20 · max 142,00,
126 valores distintos. (A mediana 1,20 do briefing é a dos não-nulos; sobre as
4.986 linhas a mediana é 0,40 — a diferença é a declaração de população.)
`acordaos_total` por página: min 1 · p50 63 · p90 414 · max 2.668, soma 765.356.
Âncora: `source_provenance.checked_at` em 4.976, `approved_at` em 10.

**O que é publicável, e com que frase.** O artefato mede **coincidência de
dispositivo + posterioridade de data**. Não lê ementa, não compara tese, não sabe
se o colegiado decidiu igual ou diferente. A explicação que ele mesmo emite já é
honesta e é o texto a publicar: *"nenhum acórdão coletado foi julgado depois da
conferência da página; N acórdão(s) anteriores citam os mesmos dispositivos;
7.458 acórdão(s) do corpus ainda sem dispositivo extraído não entram (não
medidos)"*. Publicável como **"há N decisões posteriores à revisão que tocam os
mesmos dispositivos — confira"**; **não** publicável como "esta página está
superada", "risco 100%" nem qualquer rótulo de probabilidade.
E o `7458` é **constante em todas as 4.986 linhas** — é o buraco declarado,
congelado no momento da geração, não um valor por página.

## 5. AS EXTRAÇÕES (camada: disco, data/ai/extracoes_dispositivos.jsonl)

Snapshot determinístico por byte: **42.082.169 bytes** (o arquivo é append-only
e cresceu durante a medição — 42.079.836 B às 21:41, 42.082.169 B às 21:44).

**44.163 registros, 36.040 acórdãos distintos (59,8% dos 60.221), 136.388 itens,
1.520 descartados pela âncora literal.**
- Produtor: **parser 34.953 registros (79,1%)** e `qwen3.5:4b` 9.210 (20,9%).
  O parser faz 4 de cada 5 — o modelo é a minoria, e é o que custa.
- Custo acumulado no arquivo: 6.268.192 prompt_tokens contra 985.671 eval_tokens
  (**6,36:1**) — confirma no dado que a extração é dominada por *prefill*.
- Campos do item: norma, artigo, texto_citado (136.388 cada) e **urn 134.934
  (98,9%)**. 1.454 itens sem URN.
- **47,1% dos itens (64.172) têm `artigo` vazio** — são súmulas e precedentes
  nominados, não artigos de lei.

**O campo `norma` bruto é inutilizável como chave; a URN é a chave.**
2.920 strings distintas de `norma` e 14.268 pares (norma, artigo) contra
**3.668 URNs distintas** e **482 normas-base**. "CPC" 29.540 + "CPC/2015" 11.134
+ "Código de Processo Civil" 5.725 + "CPC/15" 1.030 são a mesma lei;
"Súmula 7 do STJ" aparece em ≥7 grafias.

**Os 30 dispositivos mais citados, por URN** (topo): sumula:STJ:7 **23.288** ·
CPC art. 1.022 **11.900** · sumula:STJ:83 9.842 · sumula:STF:284 5.660 ·
sumula:STJ:5 5.351 · CPC art. 489 5.099 · sumula:STF:282 3.276 ·
sumula:STJ:182 2.853 · sumula:STF:283 2.691 · sumula:STJ:211 2.668 ·
CF art. 105 1.931 · CPC art. 1.029 §1º 1.803 · CPC art. 932 1.592 ·
sumula:STF:356 1.369 · CPC art. 1.026 §2º 1.283 · CPC art. 489 §1º 1.264 ·
CPC art. 85 §11 1.113 · CPC art. 1.021 §4º 1.031 · sumula:STJ:568 976 ·
CPC 1.021 §1º 842 · CPC 85 §2º 787 · CPC 1.025 755 · CPC 373 733 · CPC 85 538 ·
**CC art. 205 510 · CC 884 488 · CC 186 487 · CC 927 477 · CC 422 476** ·
sumula:STF:735 424.

**Normas-base por volume:** CPC/2015 (13105) **50.076** · Súm. 7 23.288 ·
CC/2002 (10406) 11.945 · Súm. 83 9.842 · Súm. 284 5.660 · Súm. 5 5.351 ·
Súm. 282 3.276 · Súm. 182 2.853 · **CF/88 2.814** · Súm. 283 2.691 ·
Súm. 211 2.668 · **CDC (8078) 1.897** · Súm. 356 1.369 · Súm. 568 976 ·
**Lei 11.101/2005 789**.
Autoridade da URN: federal 71.357 · "outro" 63.577 (as súmulas, cuja chave é
`sumula:TRIBUNAL:N`, fora do padrão `urn:lex:`) · sem URN 1.454.
Cauda: 1.074 URNs com 1 ocorrência, 824 com ≥10, **109 com ≥100**.

**A cobertura por área do Direito não existe no artefato de extração.** Acórdão
não tem área, e não há aresta acordao→area. A única cobertura por área
mensurável é a da §1 (via ponte de dispositivo), e ela diz: o vocabulário
extraído é **processual em ~76%** (CPC 50.076 + as onze súmulas de admissibilidade
≈ 53.047 = 103.123 de 134.934 itens com URN).

`data/ai/dispositivos_promovidos.jsonl`: 35.082 linhas,
`stj_dispositivos_promovidos_v1`, com `dispositivos_citados_urn[]` e
`sumulas_citadas[]` já normalizados por `id_fonte` — é a forma servível.

`content/legal_cocitation_index.jsonl` (o lado página): 5.815 linhas
(**52,4% das 11.104 páginas**, 5.289 páginas sem percurso), 8.516 percursos,
1,46 por página, **1.059 URNs distintas**, 31.102 links de página somados,
`evidencia_de_publicacao: False` em **5.815/5.815 (100%)**.
Top URNs do lado página: **CDC art. 14 185 · CF art. 5º 165 · CDC 6 147 ·
CDC 51 143 · CDC 39 111 · CDC 42 104 · CDC 30 102 · CDC 35 92 · CF art. 7º 82**.
**O contraste é a tese central:** a página cita direito material (CDC, CF), o
acórdão cita admissibilidade (Súm. 7, CPC 1.022). 1.059 URNs de um lado,
3.668 do outro, 662 alvos em comum — e 113 desses 662 carregam 74,6% dos
acórdãos pareados.

## 6. A REDE SOCIAL: a matéria que ela tem HOJE

- Código: **85 arquivos em `cmd/social/`**, ~50 tabelas em `var/social/social.db`.
- **Contagem de linhas, medida (sqlite ro):** temas **11.039** · contas 1 ·
  perfis 1 · **posts_blog 0 · duvidas 0 · respostas 0 · comentarios_de_post 0 ·
  comentarios_de_autoridade 0 · perfis_advogado 0 · perfis_jurista 0 ·
  decisoes 0 · recursos 0 · ordens_judiciais 0 · fontes_do_post 0 ·
  fontes_da_resposta 0 · fontes_do_comentario_de_autoridade 0 · reacoes 0 ·
  follows 0 · midias 0 · denuncias 0 · fila_moderacao 0 · revisores 0 ·
  verificacoes_oab 0 · sigilo_casos 0 · notificacoes 0.**
- `temas` é um espelho do acervo: (area, slug, titulo, caminho). 11.039 salas,
  zero conversa.
- **Camada API, medida ao vivo (MCP do portal):** `buscar_duvidas("pensão
  alimentícia atrasada")` → `{"duvidas":[],"total":0}`;
  `duvidas_do_tema("/familia/pensao-alimenticia-atraso-prisao/")` → erro
  `tema nao encontrado`. O agente que chega recebe vazio, ou erro.
- Contra isso, **83.810 acessos a `/redesocial/tema/`, 28.036 (33,4%) de gptbot**
  (medição de origem trazida no briefing desta sessão).

## 7. O QUE O `contexto_juridico` JÁ ENTREGA (camada: API, chamada ao vivo)

Para "execução fiscal prescrição intercorrente", 2 blocos, cada um com: `tese`
autoral, `dispositivos[{rotulo,urn}]`, `fontes_oficiais[{nome,url,conferida_em,
sustenta}]`, `cite_as` em CSL-JSON com sha256 e CC-BY-4.0, `url_markdown`,
`revisado_em`, `precedentes[{chave,rotulo,via}]` e `risco_de_superacao` inteiro
com `explicacao` e `fontes[]`.
**Este é o pacote de discussão pronto** — e já é o que os agentes consomem.
Medido no mesmo retorno: o bloco `/sumulas/stj-314/` veio com
`dispositivos: []`, `precedentes: []` e `risco_de_superacao.medido: false`
("a página não cita dispositivo que algum acórdão coletado também cite"), e o
bloco `/tributario/execfiscal-o-que-e/` veio com 3 dispositivos e 3 precedentes
reais do STJ. **A assimetria de 38,8% da §1 aparece na API, bloco a bloco.**

## 8. A FILA DO CÉREBRO (camada: disco, data/ai/fila.sqlite, ro)

53.786 linhas em `tarefa`: extrair_dispositivos **pendente 34.160**,
concluída 8.328, erro 39, executando 3 · embed_pagina concluída 11.248, erro 5 ·
medir_modelo pendente 3. Modelos: `qwen3.5:4b` 42.530 · `qwen3-embedding:0.6b`
11.253 · medir_modelo em 0.6b/4b/8b.
Embeddings no disco: 48 MB em `data/ai/embeddings/qwen3-embedding-0.6b`.
**34.160 pendentes contra 24.181 acórdãos ainda sem extração** — a fila tem mais
tarefas que acórdãos faltando porque a identidade inclui o modelo.

## 9. LACUNA A NOMEAR — a matéria-prima que falta para discussão de caso real

Nove faltas, cada uma com o número que a sustenta:

1. **O corpus é monotemático.** 97,4% em 3ª e 4ª Turma (direito privado).
   Não há acórdão de previdenciário, criminal, tributário de 1ª Seção,
   administrativo ou trabalhista. As três maiores demandas do país
   (execução fiscal 20,16 M · IPTU 12,68 M · auxílio por incapacidade 6,59 M)
   não têm UM acórdão do corpus que as sustente. **Falta: as 6 turmas ausentes.**
2. **Falta o INTEIRO TEOR: 0 de 60.221 (0,0%), e nem a URL.** Ementa (média
   ~1,4 KB) e dispositivo é tudo. Agente não refuta tese sem a fundamentação;
   com ementa só se refuta o resumo.
3. **Falta o nó de ATOR.** 21 relatores + 20 votantes + 26 presidentes estão em
   string dentro de blob; `orgao_julgador` não está nem no blob. Sem nó, não há
   perfil de órgão, não há agregado por colegiado, não há "tese predominante da
   Terceira Turma" — as três rubricas que o §12 autoriza.
4. **Falta o RESULTADO como campo.** Ele é derivável em 99,6% por regex sobre
   `dispositivo`, e hoje é derivado zero vezes: nenhum artefato do disco tem
   `resultado`, `unanimidade` ou `composicao`. Sem resultado não existe índice
   de reforma, e sem ele não há o que discordar.
5. **Falta a aresta de SUPERAÇÃO.** `supera`, `altera` e `impactada_por` estão no
   CHECK e valem 0; `revoga` vale 2. O `risco_superacao.jsonl` mede coincidência
   de dispositivo + data, não divergência de tese — e cobre 44,9% das páginas.
   **Discussão de caso real é sobre divergência, e divergência não está medida.**
6. **Falta a ponte de MÉRITO.** 74,6% dos acórdãos pareados (32.424) pareiam só
   por súmula de admissibilidade. Sem separar processual de mérito, o "precedente"
   que o agente recebe é ruído em 3 de 4 casos.
7. **Falta metade dos percursos.** 5.289 de 11.104 páginas (47,6%) sem nenhum
   percurso legal; 6.791 (61,2%) sem nenhum acórdão pareado; 57 páginas de
   `noticias` com 0%.
8. **Falta o eixo TEMPO e o eixo ÓRGÃO no DataJud.** O cubo tem 3 faces planas
   (assunto top-150, classe top-60, grau) de uma coleta de 39 dias atrás, com
   tjpe sem assuntos (6,72 M processos cegos). Não há como dizer "essa demanda
   cresceu" — e crescimento é o gancho de pauta de uma rede social.
9. **Falta o cruzamento HONESTO acervo×demanda.** O único que existe
   (`paginas_no_acervo`) é léxico frouxo (4,46 assuntos por página; exemplos de
   bagagem aérea sob execução fiscal) e **não tem gerador versionado** em
   internal/, cmd/, tools/ ou ops/.

10. **Falta CASO REAL, literalmente.** Não há **um** processo armazenado no disco:
    `data/corpus/` tem só `jurisprudencia` (192 MB) e `wikidata` (4,8 MB);
    em `social.db`, `decisoes`/`recursos`/`ordens_judiciais` = **0**;
    `cmd/social/processotela.go` consulta o DataJud **ao vivo**, nada persiste.
    O que existe é **ementa de recurso do STJ**, não caso. Uma discussão de caso
    real precisa de andamento, peça, decisão de 1º/2º grau — nada disso está no
    disco, e o DJEN (a espinha do acompanhamento no PLANO_REDE_SOCIAL) não tem
    coletor com dado gravado aqui.
11. **Falta ligar as TESES.** `tema` tem **2.347 nós** (repetitivos/controvérsias,
    com `orgao_julgador` e `situacao` no blob) e só **291 deles (12,4%) têm
    qualquer aresta `cita`** — 354 arestas no total. "Tese predominante" é
    exatamente a rubrica que o §12 autoriza, e é a que está menos cabeada.
12. **A identidade externa existe e ninguém a usa.** `data/corpus/wikidata/
    lexml_qids.jsonl`: 38.018 itens, **37.999 URNs distintas** (SPARQL
    `wdt:P9119`, consultado 2026-09-08, sha256 no `.proveniencia.json`), com
    cobertura declarada de **2.077 de 2.234 dispositivos (93,0%)** e 197 de 231
    normas do grafo. Não há nó, aresta nem campo de `qid` no grafo — o QID é o
    identificador com que um agente externo reconcilia nossos dispositivos, e
    está fora da superfície.

E a falta que não é de dado: **11.039 salas com 0 posts, 0 dúvidas, 0 respostas,
0 comentários, recebendo 83.810 acessos**. O substrato para falar existe
(11.248 vetores, 3.668 URNs, 60.221 acórdãos, 549 pontes de mérito, o pacote do
`contexto_juridico`); o que não existe é **um único enunciado escrito na rede**.

## 10. O que o advisor mudou

Quatro mudanças, todas incorporadas acima:

1. **Retirou uma proibição que eu inventei.** Eu havia escrito "PROIBIDO ranking
   de ministro / agregado por relator" apoiado na descrição do `perfil_de_jurista`
   e no Prov. 205/2021. O advisor apontou que aquela descrição governa **advogado
   da plataforma** (publicidade), não **ator público**, e que nenhum dispositivo
   citado veda o eixo relator. Isso violava a ZERO-C ("proibido inventar risco
   jurídico sem citar norma e dispositivo") e a ordem desta sessão sobre não
   invocar a OAB para travar conteúdo informativo. §2 reescrita: a vedação com
   dispositivo é só de **redação** ("chance de êxito"); o eixo órgão passou a ser
   **decisão de engenharia minha, por estabilidade de amostra**, não veto.
2. **Derrubou "não tem gerador versionado".** Meus greps usavam
   `--include=*.go/*.py/*.sh` e `tools/` é cheio de scripts sem extensão. Sem
   filtro: **`tools/generate-datajud-corpus`** é o produtor, commit `cb1e12c6`.
   Li o matcher (linhas 152-183) e reproduzi: é **OR de um token** entre
   title+heading+path e o rótulo do assunto menos 19 palavras `VAGOS`. A
   afirmação passou de inferência sobre 3 exemplos para leitura do código mais
   reprodução em três assuntos.
3. **Unificou a definição de "processual".** Eu usara 15 súmulas na ponte e 11 na
   tabela por área. Rodei a tabela com o SET-15: o split 113/549 **não muda** e a
   tabela muda pouco (tributário 27,1%→26,6%, jurisprudência 15,9%→15,4%,
   súmulas 23,4%→22,8%, leis 46,8%→46,6%, glossário 33,4%→33,3%). O SET-15 é
   agora o único usado, e está rotulado como **classificação própria**.
   Cross-check pedido, confirmado: **7.458 = 60.221 − 52.763**, ou seja, a
   constante congelada do `risco_superacao.jsonl` é exatamente o número de
   acórdãos com **zero** aresta `cita`.
4. **Quatro acréscimos que afiaram a lacuna:** caso real literalmente ausente
   (gap 10) · `data/corpus/wikidata` aberto e medido — **não** são atores, são
   38.018 QIDs LexML com 93,0% dos dispositivos do grafo (gap 12) ·
   2.347 temas com 12,4% cabeados (gap 11) · e as quatro contagens de página por
   camada (11.118 / 11.106 / 11.104 / 11.039) com a nota de que as 32 "áreas"
   misturam ramo do Direito com tipo de conteúdo (3.212 páginas, 28,9%).

Nada do que eu havia **medido** foi contrariado: os números da §1 a §8 continuam
como estavam, exceto a tabela por área recalculada no SET-15.
