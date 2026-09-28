# Volume real do corpus STJ pós-recuperação — medição

Sessão: retomada do agente morto por limite. Data: 2026-09-15. **Somente leitura.**
Registro durável — atualizado ao longo da sessão.

## 0. Como cada número está marcado

- **MEDIDO** — leitura própria de disco ou resposta HTTP desta sessão.
- **DERIVADO** — aritmética sobre MEDIDOs, sem hipótese nova.
- **PROJETADO** — MEDIDO × hipótese declarada (linearidade, taxa transportada).

---

## 1. REFUTAÇÕES de contexto herdado (MEDIDO)

### 1.1 A contagem de recursos do outro agente está errada em 6 de 6

Fonte: página HTML de cada dataset, buscada nesta sessão
(`/tmp/stj-census/page-*.html`, HTTP 200, UA `WikijuridicaBot/1.0 … coleta-oficial`),
contando `/download/AAAAMMDD.json` distintos.

| dataset | alegado pelo outro agente | **MEDIDO** |
|---|---|---|
| quinta-turma | 48 | **52** |
| corte-especial | 44 | **52** |
| primeira-secao | 51 | **52** |
| terceira-secao | 51 | **52** |
| segunda-turma | 62 | **51** |
| sexta-turma | 48 | **52** |

Todos os 10 datasets cobrem **20220531 … 20260831** — a MESMA janela de 52
competências que a 3ª e a 4ª Turma já têm completas. `segunda-turma` tem 51.
Licença conferida em corte-especial:
`Creative Commons Atribuição` / `opendefinition.org/licenses/cc-by`.

**Consequência**: a extrapolação "9 meses ±30%" do plano estava errada na base.
Não faltam 9 meses de 6 datasets — faltam **52 competências de 6 datasets**,
mais 31 da 2ª Seção e 49 da 1ª Turma. Total a recuperar: **391 competências**.

A falta de 1 competência na `segunda-turma` é **lacuna REAL da fonte**, não erro
de parser (MEDIDO): a competência ausente é **20221031**, e a varredura de TODO
`/download/` da página não achou nenhum `.json` que a regex `\d{8}\.json` deixe
passar (só `20220508.zip`, `dicionario-espelhodoacordao.csv` e um `___`).

### 1.2 O CKAN API é PROIBIDO por robots.txt (MEDIDO)

`https://dadosabertos.web.stj.jus.br/robots.txt` (102 bytes, HTTP 200):

```
User-agent: *
Disallow: /dataset/rate/
Disallow: /revision/
Disallow: /dataset/*/history
Disallow: /api/
Crawl-Delay: 10
```

`Disallow: /api/` fecha `package_show`. O coletor falha fechado nisso
(`internal/stjacordaos/cliente.go:116`), e `dataset.go:33` já diz que a regex de
recurso "NAO casa /api/ nem /revision/ por construcao". **A rota de medição é a
página HTML + `HEAD` na URL de download** — não existe atalho por API.
A página HTML **não** declara tamanho (só `font-size` de CSS). Não há DCAT
(`.rdf`/`.jsonld`/`.ttl`) anunciado.

### 1.3 Amostragem por stride NÃO fecha a lacuna (MEDIDO — motivo do censo integral)

Teste offline contra as duas séries 100% medidas (52 competências cada), variando
o offset do stride e sempre incluindo primeiro e último mês:

| stride | n amostra | erro % — 3ª Turma | erro % — 4ª Turma |
|---|---|---|---|
| 2 | 27 | −6,72 … +8,83 | −3,68 … +9,57 |
| 3 | 18 | −12,29 … **+28,50** | −19,70 … **+42,22** |
| 4 | 14 | −6,18 … **+21,67** | −3,34 … **+26,83** |
| 6 | 10 | −24,97 … **+53,03** | −24,78 … **+58,81** |
| 8 | 8 | −21,34 … **+61,42** | −0,60 … **+62,91** |

Causa MEDIDA: o volume mensal tem **CV de 101,0%** (3ª Turma) e **124,9%**
(4ª Turma) — um mês (2025-12: 11,37 MB) vale 11× o mês mediano. Estimador de
média sobre cauda assim não converge com amostra esparsa.

**Portanto**: uma amostra por stride devolveria banda ±27% a ±59% — igual ou PIOR
que os ±30% que o plano já tem. A ordem "lacuna não fica sem medição" só se cumpre
com **censo integral por `HEAD`**: 391 requisições, 1 por competência faltante.

---

## 2. Estado MEDIDO do que já está no disco

`manifest.jsonl` tem 138 linhas brutas; deduplicado por `(dataset, competencia)`
mantendo a última → **128 linhas únicas**, que reproduzem o `cursor.json`
exatamente (60.221 registros). As 10 linhas extras são recoletas.

| dataset | competências | registros | MiB fonte | reg/mês | MiB/mês | **reg/MiB** | B/reg |
|---|---|---|---|---|---|---|---|
| terceira-turma | 52 (completo) | 30.786 | 88,527 | 592,0 | 1,702 | **347,76** | 3.015 |
| quarta-turma | 52 (completo) | 27.845 | 86,826 | 535,5 | 1,670 | **320,70** | 3.270 |
| segunda-secao | 21 (para em 20240131) | 728 | 2,296 | 34,7 | 0,109 | **317,05** | 3.307 |
| primeira-turma | 3 (para em 20220731) | 862 | 2,749 | 287,3 | 0,916 | **313,62** | 3.343 |
| **TOTAL** | **128** | **60.221** | **180,398** | — | — | **333,82** | 3.141 |

Descartes na coleta: `excluidos_sigilo` **1**, `descartados_sem_ementa` **49**
(sobre as 128 linhas únicas). Ou seja o `registros` do manifesto já é líquido.

### 2.0 A soma por dataset é legítima: NÃO há sobreposição (MEDIDO)

Antes de somar 10 datasets é preciso saber se um acórdão aparece em mais de um.
Sobre os 60.221 registros de disco:

- `id_fonte` **distintos: 60.221 — zero duplicados**;
- pares `(classe, numeroProcesso)` distintos: 59.728, com **493 repetições**, que
  são acórdãos DIFERENTES no mesmo processo (ex.: `AgInt nos EDcl no AREsp
  2208042`, 4 vezes) — e o gerador já trata isso na deduplicação por `intent`.

Logo a projeção pode **somar** os datasets sem descontar interseção.

### 2.0.1 ⚠ CORREÇÃO: a conclusão de §2.1 ficou SUPERADA pela medição direta

A seção 2.1 abaixo concluiu, sobre os **4 datasets em disco**, que a razão
reg/MiB não varia por tipo de órgão (313,6–347,8, CV 4,16%). Com as amostras
baixadas dos datasets AUSENTES, essa conclusão **não se sustenta**:

| dataset | razão MEDIDA | fonte |
|---|---|---|
| terceira-turma (cível) | 347,8 | disco, 52 meses |
| **corte-especial** | **326,4** | amostra, 3 meses, 593 registros |
| quarta-turma (cível) | 320,7 | disco, 52 meses |
| segunda-secao | 317,1 | disco, 21 meses |
| primeira-turma | 313,6 | disco, 3 meses |
| **sexta-turma** | **325,6** | amostra, 3 meses, 2.298 registros |
| **quinta-turma** | **295,4** | amostra, 3 meses, 1.920 registros |
| **segunda-turma** | **252,5** | amostra, 3 meses, 898 registros |
| **terceira-secao** | **236,8** | amostra, 3 meses, 259 registros |
| **primeira-secao** | **220,9** | amostra, 3 meses, 404 registros |

A faixa real é **220,9 a 347,8** — o dobro da dispersão que os 4 datasets de
disco mostravam. Transportar a média de 324,78 teria **superestimado a 1ª Seção
em 47%**.

**A lição é do método, não do número**: os 4 datasets em disco são 2 Turmas
cíveis, 1 Turma e 1 Seção com amostra fininha — não cobriam o espaço. Foi exatamente
por isso que o encargo mandou medir por tipo de órgão em vez de usar média global,
e por isso as fases C3/D/E/F/G existiram. **O §2.1 abaixo fica preservado como
registro do que a medição parcial dizia, e superado nesta data por esta seção.**

### 2.1 (SUPERADA por 2.0.1) A razão reg/MiB não varia por tipo de órgão

Dispersão das 4 razões agregadas: média **324,78**, sd **13,50**, **CV 4,16%**,
faixa 313,62–347,76. Isto **refuta** a hipótese do encargo de que Turma, Seção e
Corte Especial exigiriam razões diferentes para converter MiB→acórdãos.

Mecanismo MEDIDO (média de bytes por registro, por campo, sobre os 60.221 do disco):

| órgão | n | linha JSONL (B) | ementa | dispositivo | jurisp. citada | ref. legisl. | URN/reg | súmula/reg |
|---|---|---|---|---|---|---|---|---|
| TERCEIRA TURMA | 30.786 | 3.199 | 1.517 | 475 | 92 | 53 | 0,42 | 0,20 |
| QUARTA TURMA | 27.845 | 3.459 | 1.730 | 490 | 101 | 58 | 0,44 | 0,23 |
| PRIMEIRA TURMA | 862 | 3.508 | 1.592 | 502 | 207 | 101 | 0,66 | 0,37 |
| SEGUNDA SEÇÃO | 728 | 3.410 | **1.260** | **628** | **242** | **140** | **1,32** | 0,26 |

A Seção tem a ementa **mais curta** (1.260 contra 1.517/1.730) e ainda assim o
registro mais pesado que a 3ª Turma: o que ela perde em ementa ganha em
dispositivo (+32%), jurisprudência citada (2,6×) e referência legislativa (2,6×).
É por isso que reg/MiB fica estável. **Usar uma razão por tipo aqui seria
introduzir dispersão que a medição não mostra.**

Controle contra a distribuição mensal: a Seção julga **34,7 acórdãos/mês**
(MEDIDO, 21 meses) contra 535–592 das Turmas cíveis. O que separa os tipos é o
**volume mensal**, não a densidade por byte — e o volume mensal vem do censo de
`HEAD`, não de razão nenhuma.

---

## 3. Elegibilidade — réplica CALIBRADA contra o oráculo do binário

`elegivel()` em `cmd/generate-acordao-pages/main.go:514` é função pura dos campos
do registro. Reimplementei-a em Python (filtros de `main.go:316,342,389,402,514`,
`internal/stjacordaos/sigilo.go:MotivoBarrado`,
`internal/ptbrtext/text.go:728 BodyWords`) e a **calibrei contra os dois números
autoritativos do próprio binário**:

| passada | réplica | autoritativo informado | veredito |
|---|---|---|---|
| base (só o corpus) | **2.560** | 2.560 | **idêntico** |
| com sobreposição da IA local (`data/ai/dispositivos_promovidos.jsonl`, 35.082 chaves) | **4.763** | 4.763 | **idêntico** |

Réplica que reproduz os dois números exatos sobre 60.221 registros não é
reimplementação cega — tem oráculo independente. O recorte por órgão abaixo é
portanto **MEDIDO**:

| órgão | n | candidatos base | % base | candidatos c/ IA | % c/ IA |
|---|---|---|---|---|---|
| TERCEIRA TURMA (cível) | 30.786 | 1.494 | **4,85%** | 2.752 | **8,94%** |
| QUARTA TURMA (cível) | 27.845 | 1.008 | **3,62%** | 1.941 | **6,97%** |
| PRIMEIRA TURMA (público) | 862 | 12 | **1,39%** | 19 | **2,20%** |
| SEGUNDA SEÇÃO | 728 | 46 | **6,32%** | 51 | **7,01%** |
| **TOTAL** | **60.221** | **2.560** | **4,25%** | **4.763** | **7,91%** |

Recusas globais (base): `agravo_ou_embargo` **49.807 (82,71%)**,
`ementa_curta` **4.500 (7,47%)**, `sem_ancora_legal` **3.354 (5,57%)**.

**A taxa VARIA 4,5× entre órgãos** (1,39% na 1ª Turma contra 6,32% na 2ª Seção).
Aplicar a taxa global de 4,25% aos órgãos ausentes seria o erro que o encargo
manda evitar. Duas observações medidas:

- O que puxa a 2ª Seção para cima é âncora legal: **1,32 URN/registro** contra
  0,42 da 3ª Turma. Menos registros cai em `sem_ancora_legal`.
- O que derruba a 1ª Turma (direito público) é outro perfil de classe
  processual — a medir no censo, porque 862 registros de 3 meses é amostra fina.
- A coluna "c/ IA" **não é transportável** aos órgãos ausentes sem trabalho novo:
  o writeback tem 35.082 chaves e cobre só registros já em disco. A linha base
  (2.560 / 4,25%) é o **piso que não depende de computar nada**.

**Mas o custo desse recálculo é MUITO menor do que "rodar o cérebro sobre 130 mil
acórdãos"** — medido em `data/ai/dispositivos_promovidos.jsonl`:

| produtor do writeback | entradas | % |
|---|---|---|
| **`parser`** (determinístico, zero Ollama) | **28.559** | **81,4%** |
| `qwen3.5:4b` (LLM) | 6.523 | 18,6% |

E, entre os **2.203 resgates** que levam 2.560 → 4.763 (registro que estava em
`sem_ancora_legal` e virou candidato):

| produtor | resgates | % |
|---|---|---|
| **`parser`** | **1.400** | **63,5%** |
| `qwen3.5:4b` | 803 | 36,5% |

Cobertura do writeback: 35.082 de 60.221 (**58,3%**); dos 3.354 `sem_ancora`,
**78,7%** têm entrada e **83,4% desses foram resgatados**.

Logo: **~64% do ganho da camada "c/IA" é parser**, que roda sobre o corpus novo
sem fila de LLM. O terço restante depende do Ollama e é o único pedaço
genuinamente condicional — e é por isso que a projeção "c/IA" sai como
**linha condicional**, não como número fechado.

### 3.0.2 Como medir a taxa nos órgãos AUSENTES sem reimplementar o `lexml`

Problema: o arquivo mensal da fonte traz `referenciasLegislativas` em REPLEG
bruto; `dispositivos_citados_urn` e `sumulas_citadas` são **derivados** por
`internal/stjacordaos/referencias.go` via `lexml.BuildURN`, que depende de tabela
canônica de códigos. Replicar isso às cegas produziria taxa errada.

Solução: um **proxy** sobre o bloco REPLEG bruto (`LEG:FED <SIGLA>:<num>
ANO:<ano>` + `ART:`, e `SUM(STF|STJ)` + `SUM:`), com a mesma lista de
dispositivos de admissibilidade — **calibrado contra o campo derivado que já está
em disco**, que serve de oráculo:

| conferência do proxy de âncora | valor |
|---|---|
| concordância sobre 60.221 registros | **99,16%** |
| recall / precisão | 97,15% / 98,61% |
| perde âncora (real=T, proxy=F) | 341 |
| inventa âncora (real=F, proxy=T) | 164 |
| **viés líquido na contagem** | **−1,48%** |

E o **pipeline inteiro** (procedimental → tipo de decisão → sigilo → campos
obrigatórios → piso de 250 palavras → âncora por proxy) rodado sobre o disco:

| | candidatos |
|---|---|
| pipeline com proxy | **2.548** |
| autoritativo (binário) | 2.560 |
| **erro do proxy** | **−0,47%** |

Instrumento com erro medido de −0,47% sobre 60.221 registros pode ser aplicado
aos arquivos brutos das fases C3/D/E/F. **A taxa de candidato dos órgãos ausentes
sai MEDIDA sobre registros reais**, com esse viés declarado — não transportada da
turma cível.

**Teste de round-trip do caminho que vai rodar de verdade.** O arquivo baixado da
fonte usa nomes camelCase (`siglaClasse`, `nomeOrgaoJulgador`, `ministroRelator`,
`dataDecisao`, `tipoDeDecisao`, `decisao`, `referenciasLegislativas`), não os do
JSONL convertido. Converti os 60.221 registros de disco de volta para o formato da
FONTE e rodei **o mesmo código que vai ler os arquivos baixados**:

```
round-trip disco -> formato-fonte sobre 60221 registros
  net=60221  proc=49807  nproc=10414  cand=2548  com_item=2438
  AUTORITATIVO base=2560  ->  erro -0,47%
```

**E o primeiro round-trip estava ERRADO — o defeito só apareceu no dado real.**
O round-trip inicial mapeou os NOMES dos campos, mas não os FORMATOS: em disco
`data_julgamento` é `"2023-12-04"` (10 caracteres), e **na fonte `dataDecisao` é
`"20250806"` (8)**. Meu filtro exigia `len >= 10` e, no primeiro passe sobre os
arquivos baixados de verdade, **rejeitou 100% dos registros** — as 4 amostras
saíram com `cand=0`, que é o sintoma que denunciou o defeito.

A correção espelha `internal/stjacordaos/registro.go:118 dataCompacta` (exige
exatamente 8 caracteres, valida `AAAAMMDD`, devolve `AAAA-MM-DD`), e o round-trip
foi **refeito com a data no formato compacto da fonte** — voltando aos mesmos
2.548 (−0,47%). Sem o dado real, o teste de round-trip teria me dado confiança
falsa: ele validava o mapa de nomes contra um dado que já estava convertido.

---

### 3.0 O que REALMENTE governa a taxa de candidato (MEDIDO)

A taxa bruta varia 4,5× entre órgãos, mas ela se decompõe em dois fatores, e só
um deles varia de verdade:

```
candidatos = n × (1 − parcela_procedimental) × P(candidato | não-procedimental)
```

| órgão | n | **% procedimental** | não-proc | %≥250 palavras \| np | **% cand base \| np** | **% cand c/IA \| np** | % cand c/IA \| n |
|---|---|---|---|---|---|---|---|
| TERCEIRA TURMA | 30.786 | 80,0% | 6.151 | 56,4% | **24,3%** | **44,7%** | 8,94% |
| QUARTA TURMA | 27.845 | 85,3% | 4.097 | 57,5% | **24,6%** | **47,4%** | 6,97% |
| PRIMEIRA TURMA | 862 | **95,9%** | 35 | 82,9% | 34,3% | 54,3% | 2,20% |
| SEGUNDA SEÇÃO | 728 | 82,0% | 131 | 45,0% | 35,1% | 38,9% | 7,01% |

`procedimental()` (`main.go:316`) descarta AGINT/AGRG/AGREG/EDCL/ARESP/EARESP/
EDV/AGRESP e sozinho come **80,0% a 95,9%** do corpus. O que sobra converte com
taxa **muito mais estável**: as duas amostras grandes (n=6.151 e n=4.097) dão
**24,3% e 24,6%** base — praticamente idênticas. As duas pequenas (n=35, n=131,
órgãos não-cíveis) dão 34,3% e 35,1%, mas com n desses tamanhos o intervalo é
largo. IC 95% de Wilson, MEDIDO:

| órgão | P(cand base \| não-proc) | IC 95% |
|---|---|---|
| TERCEIRA TURMA | 1.494/6.151 = 24,29% | [23,23% ; 25,38%] |
| QUARTA TURMA | 1.008/4.097 = 24,60% | [23,31% ; 25,95%] |
| SEGUNDA SEÇÃO | 46/131 = 35,11% | [27,47% ; 43,61%] |
| PRIMEIRA TURMA | 12/35 = 34,29% | [20,83% ; 50,85%] |

Os IC da 2ª Seção e das Turmas cíveis **não se sobrepõem**: a diferença é real,
não ruído de amostra pequena.

**Consequência para a projeção**: o que precisa ser medido nos órgãos ausentes é
a **parcela procedimental** — que se mede com poucas centenas de registros — e
não a taxa bruta, que precisaria de milhares. Isso torna a amostragem da fase C3
suficiente para o item 4 do encargo.

### 3.0.3 MEDIDO nas amostras: a hipótese sobre a turma criminal estava INVERTIDA

Eu havia previsto que a 5ª e a 6ª Turma teriam parcela procedimental **menor**
que as cíveis, porque `classesProcedimentais` não inclui HC nem RHC e turma
criminal é HC-pesada. A medição sobre os arquivos baixados diz o contrário:

| dataset | n da amostra | **% procedimental** | **% candidato base** |
|---|---|---|---|
| **primeira-secao** | 404 | **63,9%** | **13,86%** |
| terceira-secao | 259 | 87,6% | 6,18% |
| segunda-turma | 898 | 90,9% | 3,45% |
| corte-especial | 752 | 91,0% | 3,32% |
| sexta-turma | 2.298 | 89,1% | 2,61% |
| **quinta-turma** | 1.920 | **98,6%** | **0,68%** |

A 5ª Turma é **98,6% procedimental** — a mais alta de todo o acervo, acima até da
1ª Turma (95,9%). O motivo está na distribuição de classe MEDIDA nas amostras:

| 5ª Turma (n=1.920) | | 6ª Turma (n=2.299) | | 1ª Seção (n=404) | |
|---|---|---|---|---|---|
| **AgRg no HC** | **51,5%** | **AgRg no HC** | **45,9%** | REsp | 11,1% |
| AgRg no AREsp | 21,1% | AgRg no AREsp | 17,5% | AgInt no CC | 8,2% |
| AgRg no RHC | 9,4% | AgRg no RHC | 9,1% | ProAfR no REsp | 7,2% |
| AgRg no REsp | 5,7% | AgRg no REsp | 7,6% | AgInt no PUIL | 6,9% |
| AREsp | 1,1% | **HC (autônomo)** | **5,9%** | AgInt nos EREsp | 6,7% |
| AgRg nos EDcl no HC | 1,0% | **RHC (autônomo)** | **2,2%** | AgInt no MS | 6,2% |

Eu supus que HC escaparia do filtro. Escapa — mas **o habeas corpus não chega ao
STJ como HC: chega como `AgRg no HC`**, e `AGRG` está em
`classesProcedimentais`. Metade de cada turma criminal é isso. A 6ª Turma tem
8,1% de HC/RHC autônomos e por isso fica em 89,1% em vez de 98,6%.

Resultado: a 5ª Turma é o **maior** dataset em bytes (124,9 MiB) e o **menor** em
taxa de candidato (0,68%). A 1ª Seção, ao contrário, tem `REsp` e `ProAfR no
REsp` (afetação de repetitivo) no topo — matéria de mérito, com âncora legal
densa.

E a 1ª Seção é o oposto: só 63,9% procedimental e **13,86% de candidatos** — a
maior taxa medida no projeto inteiro, quase 3× a da 3ª Turma. É a Seção de
direito público (tributário/administrativo), que julga tema repetitivo com
fundamentação legal densa.

**A faixa de taxa de candidato vai de 0,68% a 13,86% — vinte vezes.** Aplicar a
taxa global de 4,25% aos órgãos ausentes seria exatamente o erro que o encargo
mandou evitar, e teria errado para os dois lados ao mesmo tempo.

### 3.0.1 O piso de 250 palavras cai no meio da distribuição (MEDIDO)

Palavras da ementa (`ptbrtext.BodyWords`) nos registros NÃO-procedimentais:

| órgão | n | mediana | 200–249 palavras | 250–299 |
|---|---|---|---|---|
| TERCEIRA TURMA | 6.151 | 276 | 717 (**11,7%**) | 754 (12,3%) |
| QUARTA TURMA | 4.097 | 297 | 442 (**10,8%**) | 320 (7,8%) |
| SEGUNDA SEÇÃO | 131 | 232 | 17 (**13,0%**) | 9 (6,9%) |
| PRIMEIRA TURMA | 35 | 416 | 3 (8,6%) | 4 (11,4%) |

`pisoEmentaPalavras = 250` (`main.go:402`) cai praticamente **na mediana**, e
~11% dos registros ficam na faixa imediatamente abaixo. Isso torna a taxa de
candidato **sensível ao comprimento típico da ementa do órgão**: um deslocamento
de 10% na distribuição move a taxa vários pontos.

É mais um motivo para medir os órgãos ausentes em vez de transportar taxa —
ementa de HC/RHC (turmas criminais) não tem o mesmo comprimento típico da ementa
de REsp cível, e a fase C3/E mede exatamente isso.

### 3.1 De candidato a página: o afunilamento NÃO é dedup (MEDIDO)

Reproduzi `intentDoAcordao` (`main.go:814`) sobre os 4.763 candidatos:

| etapa | valor | marca |
|---|---|---|
| candidatos (c/ IA) | 4.763 | MEDIDO |
| `numero_de_processo_nao_derivavel` | **0** | MEDIDO |
| `intent` distintos | **4.762** | MEDIDO |
| perdidos por colisão de rota | **1** | MEDIDO (casa com o comentário de `main.go:283`) |
| `rota_ja_publicada` (∩ `published_manifest`) | **0** | MEDIDO |
| **teto de páginas** | **4.762** | DERIVADO |
| páginas montadas na passada exaustiva | 2.488 | informado |

Logo o corte de 4.763→2.488 (**47,7%**) **não** é deduplicação nem rota já
publicada: é `montaPagina` + `molde_acima_do_limiar` (`main.go:291-295`). O
shard `data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` está **vazio** —
2.488 é número de relatório, não artefato em disco, então o rendimento POR ÓRGÃO
não é medível offline.

Dois mecanismos MEDIDOS empurram o rendimento em sentidos opostos, e nenhum é
linear:

- `molde_acima_do_limiar` compara cada página com as já **aceitas nesta passada**
  (`aceitas`) e com o próprio shard. É filtro sequencial: quanto maior o conjunto
  aceito, mais duro fica. Contra o rendimento, superlinearmente.
- Os órgãos ausentes trazem matéria nova (criminal na 5ª/6ª Turma, direito público
  na 2ª Turma e 1ª/3ª Seção), logo menos colisão de molde que acrescentar mais
  meses de Turma cível. A favor do rendimento.

**E o gate de "duas fontes oficiais" NÃO é o limitador** (MEDIDO na leitura de
`fontesOficiais`, `main.go:2075`): as duas primeiras fontes são o próprio espelho
(`FonteURL`) e a página do conjunto — ambas presentes em todo registro com
`coletado_em`. O corpus de normas (`data/legal-corpus`, **29 diplomas**) só entra
a partir da terceira fonte. Cobre `codigo_penal.json`, `cpp.json`,
`lei_9099_1995.json`, `lei_11340_2006.json` e `eca.json`, mas **não** a Lei de
Drogas (11.343/2006), a LEP (7.210/1984) nem os Crimes Hediondos (8.072/1990) —
os três diplomas mais citados em turma criminal. Isso não bloqueia a página;
empobrece a lista de fontes dela. Vale como item de trabalho separado, não como
risco à projeção de páginas.

Logo o afunilamento de 47,7% é `ementa_sem_item_transcritivel` +
`molde_acima_do_limiar` — e o **primeiro eu consigo medir**, porque
`itensTranscritiveis` (`main.go:1152`) é função pura da ementa (regex de item
`^[ \t]*\d{1,2}\s*\.\s` e corte no primeiro item em versal):

| etapa | valor | marca |
|---|---|---|
| candidatos (c/IA) | 4.763 | MEDIDO (réplica = oráculo) |
| **reprovados em `ementa_sem_item_transcritivel`** | **682 (14,3%)** | **MEDIDO** |
| com item transcritível — teto real antes do anti-molde | **4.081 (85,7%)** | **MEDIDO** |
| páginas na passada exaustiva | 2.488 | informado |
| ⇒ corte do **anti-molde e resto** | 1.593 de 4.081 = **39,0%** | DERIVADO |

Por órgão, a taxa de item transcritível também varia (e é medível em amostra):

| órgão | candidatos | sem item | % | itens/página |
|---|---|---|---|---|
| TERCEIRA TURMA | 2.752 | 455 | 16,5% | 7,5 |
| QUARTA TURMA | 1.941 | 221 | 11,4% | 7,8 |
| SEGUNDA SEÇÃO | 51 | 5 | 9,8% | 7,3 |
| PRIMEIRA TURMA | 19 | 1 | 5,3% | 7,4 |

O modelo de página fica, então:

```
páginas = candidatos × P(tem item transcritível)   × P(sobrevive ao anti-molde)
                       ↑ MEDIDO, 85,7% global        ↑ 61,0% DERIVADO, ordem-dependente
```

Só o segundo fator não é transportável, e é justamente o que a matéria nova dos
órgãos ausentes tende a **aliviar**.

O saldo só se resolve rodando o gerador — escrita, fora deste encargo
somente-leitura. Por isso o número de páginas sai como **PROJEÇÃO LINEAR
declarada**, com o teto MEDIDO de intents ao lado.

---

## 4. ACHADO NOVO: o arquivo histórico `20220508.zip` (MEDIDO)

Todos os **10** datasets publicam, além dos 52 mensais, **um `20220508.zip`**. A
regex do coletor (`dataset.go:33 reRecurso`) casa só `\d{8}\.json` — o ZIP nunca
foi visitado. `Content-Length` por `HEAD` (MEDIDO nesta sessão):

| dataset | zip (bytes) | zip (MiB) |
|---|---|---|
| quinta-turma | 115.233.866 | 109,9 |
| segunda-turma | 95.529.644 | 91,1 |
| sexta-turma | 73.143.663 | 69,8 |
| primeira-turma | 68.235.713 | 65,1 |
| quarta-turma | 47.368.021 | 45,2 |
| terceira-turma | 19.664.693 | 18,8 |
| primeira-secao | 16.556.603 | 15,8 |
| corte-especial | 10.627.511 | 10,1 |
| terceira-secao | 9.138.719 | 8,7 |
| segunda-secao | 5.437.525 | 5,2 |
| **TOTAL (comprimido)** | **460.935.958** | **439,6** |

Note a assimetria: as duas turmas **criminais** (5ª: 109,9 MiB; 6ª: 69,8 MiB) e a
2ª Turma (91,1 MiB) dominam o acervo histórico, enquanto a 3ª Turma — a maior do
acervo mensal — tem só 18,8 MiB. O passivo histórico está justamente nos órgãos
que a coleta nunca alcançou.

### 4.1 E agora está MEDIDO, sem baixar os 439,6 MiB

`Range` na cauda de cada ZIP (256 KiB, HTTP **206** nos 10 — o servidor honra
range mesmo sem anunciar `Accept-Ranges`) devolve o *central directory*, que
declara o tamanho **não comprimido** de cada entrada. Custo total: 10
requisições de 256 KiB = 2,5 MiB, contra 439,6 MiB de download.

| dataset | ZIP MiB | **descomprimido MiB** | razão | entradas |
|---|---|---|---|---|
| quinta-turma | 109,9 | **475,5** | 4,33 | 7 |
| segunda-turma | 91,1 | **394,5** | 4,33 | 5 |
| sexta-turma | 69,8 | **308,8** | 4,43 | 6 |
| primeira-turma | 65,1 | **295,6** | 4,54 | 5 |
| quarta-turma | 45,2 | **211,5** | 4,68 | 5 |
| terceira-turma | 18,8 | **88,4** | 4,71 | 5 |
| primeira-secao | 15,8 | **66,6** | 4,22 | 5 |
| corte-especial | 10,1 | **46,4** | 4,58 | 5 |
| terceira-secao | 8,7 | **41,8** | 4,80 | 5 |
| segunda-secao | 5,2 | **24,7** | 4,75 | 5 |
| **TOTAL** | **439,6** | **1.953,7 MiB (1,91 GiB)** | **4,44** | **53** |

**E o conteúdo não é "pré-maio-de-2022": é o acervo desde ~2000.** Os nomes das
entradas são baldes plurianuais:

```
20001231.json  20051231.json  20101231.json  20151231.json
20181231.json  20201231.json  20211231.json  20220508.json
```

Aplicando a razão MEDIDA de registros/MiB (313,62 a 347,76):

| razão usada | acórdãos PROJETADOS no arquivo histórico |
|---|---|
| 313,62 (menor medida) | **612.720** |
| 324,78 (média dos 4 datasets) | **634.523** |
| 347,76 (maior medida) | **679.419** |

**Isso é ~5,6× o corpus inteiro pós-recuperação mensal.** Mesma licença (CC-BY),
mesmo host, mesmo caminho permitido pelo robots — a única razão de nunca ter sido
lido é a regex `\d{8}\.json` de `dataset.go:33`.

Isto está **FORA** da conta de "pós-recuperação" (o coletor corrigido continua não
lendo ZIP) e é reportado como **frente própria**, não como parte da projeção.

---

## 4.5 TENSÃO ABERTA: o controle de 68/mês da Corte Especial

Corte Especial é o primeiro dataset ausente com o **censo fechado (52 de 52
MEDIDOS)**:

- MiB fonte total: **12,869 MiB** (MEDIDO)
- MiB/mês: **0,2475**, CV mensal **56,1%** (MEDIDO)
- registros PROJETADOS com a razão transportada (313,62–347,76): **4.036–4.475**,
  central 4.180 → **77,6–86,1 acórdãos/mês**, central **80,4**

O controle herdado é **~68/mês**. A projeção fica **+14% a +27% acima** dele. Só
há duas leituras, e a diferença entre elas importa:

1. **A razão transportada é alta para a Corte Especial.** Para cair em 68/mês a
   razão teria de ser **274,7 reg/MiB = 3.817 B/registro** — 14% mais pesado que
   o registro mais pesado MEDIDO em disco (1ª Turma, 3.343 B). É plausível: a
   tendência MEDIDA é que órgão de composição maior tem registro mais pesado
   (2ª Seção: dispositivo 628 B contra 475 da 3ª Turma, 1,32 URN/reg contra
   0,42), e a Corte Especial é o maior colegiado do tribunal.
2. O ~68/mês herdado mediu outra coisa, ou outro período.

**Não vou ajustar a razão para casar com o controle** — isso seria carimbar
número derivado. A tensão se resolve por medição: a **fase D baixa as 52
competências inteiras** da Corte Especial (12,869 MiB) e CONTA os registros.

### 4.5.1 RESOLVIDO — o controle estava certo e a MINHA razão estava errada

Fase D concluída, **52 de 52 competências baixadas e contadas** (MEDIDO):

```
CORTE ESPECIAL COMPLETA: 52 competencias, 3.637 acordaos, 12,869 MiB
  razao MEDIDA  = 282,6 reg/MiB
  media MEDIDA  = 69,9 acordaos/mes      [controle do encargo: ~68]
```

| | valor | erro contra o controle |
|---|---|---|
| projeção com a razão transportada (324,78) | 80,4/mês | **+18%** |
| **medição direta (52 de 52)** | **69,9/mês** | **+2,8%** |

**O controle de ~68/mês do encargo estava certo.** O que estava errado era a
razão que eu transportei dos 4 datasets de disco: a real da Corte Especial é
**282,6 reg/MiB**, 13% abaixo da média transportada. Registro isto como a lição
central da sessão — o encargo mandou usar o controle exatamente para isto, e o
desvio que eu havia anotado em §4.5 era sintoma do meu instrumento, não da fonte.

Se eu tivesse aceito a projeção transportada e fechado o relatório em §4.5, teria
entregue **+15% de acórdãos inexistentes** na Corte Especial — e o mesmo viés em
todos os 6 datasets ausentes, que é o que a §2.0.1 mostra que aconteceria.

---

## 4.6 De onde sai a BANDA (dispersão MEDIDA, não arbitrada)

A projeção é `registros_d = MiB_d × razão_d`. As duas parcelas têm erro de
natureza diferente, e só uma delas tem erro:

**MiB_d — erro ZERO, e isso está PROVADO, não suposto.** Não é amostra: é
`Content-Length` de TODAS as 391 competências faltantes, uma a uma.

O risco era de **régua diferente**: o coletor Go conta `len(corpo)` *depois* da
descompressão transparente do `net/http` (`cliente.go:202`, `Transport` nil ⇒ o Go
manda `Accept-Encoding: gzip` sozinho), enquanto o meu `curl -sSI` não manda
`Accept-Encoding` nenhum. Se a fonte comprimisse, os dois números mediriam coisas
diferentes e TODA projeção sairia errada pelo fator de compressão.

Fase C1, `HEAD` em três recursos que o coletor JÁ leu (**MEDIDO**):

| dataset | competência | `Content-Length` (HEAD) | `bytes_baixados` (manifesto) | igual? |
|---|---|---|---|---|
| terceira-turma | 20251231 | **6.479.931** | 6.479.931 | **sim** |
| segunda-secao | 20240131 | **32.821** | 32.821 | **sim** |
| quarta-turma | 20260831 | **4.493.197** | 4.493.197 | **sim** |

3 de 3 batem byte a byte, `content-encoding` vazio nos três. As duas medições
estão na mesma régua: **o censo não contribui erro nenhum** à projeção, e toda a
banda vem só da razão.

**razão_d — erro MEDIDO do próprio estimador.** Testei os estimadores que vou
usar contra as 3 séries de razão agregada conhecida:

| dataset | razão agregada REAL | estimada pelos **3 maiores** meses | erro | estimada por **3 quartis** | erro |
|---|---|---|---|---|---|
| terceira-turma | 347,76 | 353,54 | **+1,66%** | 339,11 | **−2,49%** |
| quarta-turma | 320,70 | 285,55 | **−10,96%** | 341,81 | **+6,58%** |
| segunda-secao | 317,05 | 315,54 | **−0,48%** | 317,83 | **+0,25%** |

**A banda é essa: −11,0% a +6,6%, típica ±2,5%.** Não é chute, é o erro que estes
estimadores cometeram contra verdade conhecida.

Motivo MEDIDO do viés: a correlação entre tamanho do mês e razão é **negativa**
(ρ de log-bytes contra razão: −0,128 / −0,628 / −0,361). Mês grande tem registro
mais pesado, logo menos registros por MiB. Por isso amostrar só os maiores meses
**subestima** a razão (os −10,96% da 4ª Turma), e por isso a fase E busca também o
mês de 2026 das turmas ausentes — é lá que está a massa e é lá que a razão
derrapou.

Deriva temporal MEDIDA da razão (por ano, dentro do dataset):

| dataset | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| terceira-turma | 347,87 | 333,05 | 344,97 | 349,89 | 353,15 |
| quarta-turma | 363,48 | 352,95 | 378,34 | 340,46 | **283,29** |

E a massa migrou para 2026: a 4ª Turma tem **12.037 registros em 8 meses de 2026**
contra 4.836 em 12 meses de 2025 (2,5× ao mês). Um único número global aplicado a
52 meses erraria justamente onde pesa.

**Corte Especial não paga essa banda**: a fase D baixa as 52 competências
(12,869 MiB MEDIDOS) e conta os registros. Para ela o resultado é MEDIDO, não
projetado — e é ela o controle que o encargo nomeou.

---

## 5. Censo em andamento

Script: `/tmp/stj-census/` (heredoc, nada gravado em `/opt/wiki`).
Log: `/tmp/stj-census/censo.log`; resultado: `/tmp/stj-census/sizes.jsonl`.
Pacing **11 s** entre requisições (acima do `Crawl-Delay: 10`), uma única fila
serializada para o host. UA exato:
`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; coleta-oficial)`.

Ordem: 10 ZIPs (feito) → corte-especial, primeira-secao, terceira-secao,
segunda-turma, quinta-turma, sexta-turma (52 cada) → segunda-secao (31) →
primeira-turma (49). Total **391 HEAD + 10 HEAD de zip ≈ 74 min**.

### 5.0 CENSO FECHADO — 391 de 391 competências (MEDIDO)

`Content-Length` de **todas** as competências faltantes, uma requisição por
competência. **Zero** respostas != 200, zero sem `Content-Length`, zero
duplicatas, `content-disposition` exato em 100%.

| dataset | competências medidas | **MiB fonte** | MiB/mês |
|---|---|---|---|
| quinta-turma | 52 | **124,920** | 2,4023 |
| sexta-turma | 52 | **86,155** | 1,6568 |
| segunda-turma | 51 | **62,854** | 1,2324 |
| primeira-turma | 49 | **33,958** | 0,6930 |
| primeira-secao | 52 | **17,152** | 0,3298 |
| corte-especial | 52 | **12,869** | 0,2475 |
| terceira-secao | 52 | **7,127** | 0,1370 |
| segunda-secao | 31 | **5,172** | 0,1668 |
| **TOTAL A RECUPERAR** | **391** | **350,206 MiB** | — |

Para comparar: o que já está em disco são **180,398 MiB** em 128 competências.
Ou seja, a recuperação quase **triplica** o corpus em bytes de fonte.

Qualidade do censo até aqui: **zero** respostas != 200, **zero** sem
`Content-Length`, **zero** duplicatas `(dataset, competência)`, **100%** de
`content-disposition` exato, **nenhum** arquivo abaixo de 3 KB.

Observação de escala: a **quinta-turma (criminal) é o maior dataset do acervo
mensal** — ~2,3 MiB/mês no regime cheio contra 1,70 da 3ª Turma —, o que confirma
no canal mensal a mesma assimetria que o ZIP histórico já mostrava.

### 5.0.1 ACHADO: a 5ª Turma tem uma JANELA RALA que as turmas cíveis não têm

quinta-turma fechou com **52 competências e 124,92 MiB** — o maior dataset do
acervo mensal. Mas a série não é homogênea (MEDIDO, `Content-Length` de hoje):

| competência | MiB | competência | MiB |
|---|---|---|---|
| 20250331 | 6,001 | 20260131 | **0,069** |
| 20250831 | 3,726 | 20260228 | **0,044** |
| 20250930 | 2,984 | 20260331 | **0,461** |
| 20251031 | 1,303 | 20260430 | **0,570** |
| 20251130 | **0,380** | 20260531 | **0,375** |
| 20251231 | **0,355** | 20260630 | **13,773** |
| | | 20260731 | 2,066 |
| | | 20260831 | 9,976 |

Duas coisas distintas, e a diferença importa:

1. **Janela rala de 7 competências (20251130–20260531)**, entre 0,04 e 0,57 MiB.
   As turmas cíveis **não** têm essa janela: no `manifest.jsonl` (coletado
   2026-09-08/10, seis dias antes deste censo) a 3ª Turma vai de 1,7 a 11,2 MiB e
   a 4ª de 2,0 a 12,7 MiB nas mesmas competências. É específico deste dataset.
2. **20260630 é um pico em TODOS os datasets** — 13,77 MiB na 5ª Turma, 11,24 na
   3ª, 12,71 na 4ª. Parece publicação em lote pela fonte, possivelmente com
   retroação de competências que ficaram ralas.

Não vou afirmar a CAUSA (atraso de indexação? republicação em lote? menos
julgamento?) — nada que medi decide entre elas, e chamar de "atraso" seria
inventar mecanismo. O que a medição autoriza dizer:

- o censo mede **o que a fonte serve HOJE**, que é exatamente o que o coletor
  corrigido vai baixar — número certo para "volume e custo da recuperação agora";
- para a 5ª Turma esse número é um **piso**, porque 7 de 52 competências estão
  ralas por motivo que não é o volume de julgamento das turmas vizinhas;
- se as 7 competências ralas convergirem para a média dos 45 meses restantes
  (2,74 MiB/mês), a 5ª Turma iria a ~142 MiB em vez de 124,9 — **+14%**. Registro
  isso como cenário rotulado, não como a estimativa central.

**O pico de 2026-06 é geral** (competência ÷ mediana do próprio dataset, MEDIDO):

| dataset | 2026-05 | **2026-06** | 2026-07 | 2026-08 |
|---|---|---|---|---|
| quarta-turma | 4,18× | **12,02×** | 3,61× | 4,05× |
| terceira-turma | 1,66× | **8,15×** | 2,97× | 1,95× |
| quinta-turma | 0,20× | **7,36×** | 1,10× | 5,33× |
| segunda-turma | 0,80× | **5,56×** | 2,62× | 3,04× |
| terceira-secao | 2,79× | 2,37× | 1,39× | 3,21× |
| corte-especial | 2,54× | 1,85× | 0,85× | 3,26× |
| primeira-secao | 1,43× | 0,96× | 0,40× | 1,16× |

As competências recentes carregam massa desproporcional em quase todo dataset, o
que casa com o crescimento já medido em §4.6 (a 4ª Turma faz 2,5× registros/mês em
2026 contra 2025). **O corpus está crescendo na fonte**, então qualquer número de
volume é um retrato datado — e o único valor de 2026-05 abaixo de 0,80× é
justamente o da 5ª Turma, na janela rala.

Fases encadeadas (cada uma espera a anterior fechar; fila única, 11 s):

| fase | o quê | req | motivo |
|---|---|---|---|
| **B** (censo) | `HEAD` das 391 competências faltantes | 391 | MiB exato, erro zero |
| **C1** | `HEAD` de 3 recursos que o coletor JÁ leu | 3 | **prova de escala**: `Content-Length` ≟ `bytes_baixados` |
| **C2** | `Range` na cauda dos 10 ZIPs → *central directory* | 10–20 | volume histórico não comprimido, sem baixar 460 MB |
| **C3** | 18 mensais: 3 maiores das Seções/Corte, 3 quartis das turmas ausentes | 18 | razão e taxa de candidato MEDIDAS nos perfis sem disco |
| **D** | **as 52 competências da corte-especial** (12,9 MiB) | 52 | resolve o controle de 68/mês: vira MEDIDO, não projetado |
| **E** | mês **2026** de segunda/quinta/sexta-turma | 3 | a razão derrapa em 2026 e é lá que está a massa |
| **F** | mês 2026 de primeira-turma, segunda-secao, terceira-secao | 4 | a razão de disco dessas é de 2022–2024 só |
| **G** | mês 2026 e 2024 da primeira-secao | 2 | os "3 maiores" da C3 subestimam a razão até −11% |
| **H** | 20260131 e 20260228 da 5ª e da 6ª Turma | 4 | colisão EXATA de `Content-Length`: testar se a fonte duplica payload |

### 5.0.3 ⚠ CONFIRMADO POR HASH: a fonte serve o ARQUIVO ERRADO em 4 recursos

Fase H baixou os 4 arquivos (119 KB) e comparou sha256 **e o órgão de dentro**:

```
quinta-turma 20260131  sha256=591363b3eac2a6e2…  23 registros  orgao=['PRIMEIRA TURMA']
sexta-turma  20260131  sha256=591363b3eac2a6e2…  23 registros  orgao=['PRIMEIRA TURMA']
quinta-turma 20260228  sha256=336f96f661c05a0d…  15 registros  orgao=['PRIMEIRA TURMA']
sexta-turma  20260228  sha256=336f96f661c05a0d…  15 registros  orgao=['PRIMEIRA TURMA']
```

Não é só payload duplicado entre as duas turmas criminais: **o conteúdo é da
PRIMEIRA TURMA**, servido sob os recursos da 5ª e da 6ª. Defeito da fonte.

Conferi então **todos os 82 arquivos** que baixei, comparando
`nomeOrgaoJulgador` com o dataset de origem: **78 coerentes, 4 errados** — e os 4
são exatamente estes.

**Escopo da verificação, dito com precisão** (não afirmo mais do que medi): 4 de 4
arquivos da colisão estão com órgão errado; 78 de 78 dos demais baixados estão
coerentes; e **5 das 7 competências da janela rala da 5ª Turma
(20251130, 20251231, 20260331, 20260430, 20260531) NÃO foram baixadas e portanto
NÃO foram verificadas**. Pode haver mais recursos com conteúdo trocado cujo
tamanho não colide com nada — o teste de tamanho só acha o caso em que o arquivo
errado é servido a DOIS datasets.

**Consequência de engenharia, e ela é de correção, não de volume:** o coletor
**não valida** que o órgão de dentro do arquivo bate com o dataset de onde veio.
Se rodar como está, grava 38 acórdãos da 1ª Turma dentro dos shards da 5ª e da 6ª
— e os mesmos 38 vêm ainda pelo dataset da 1ª Turma, ou seja **triplicados**.
Isso quebra a aditividade que verifiquei em §2.0 (zero `id_fonte` duplicado hoje).
O volume envolvido é ínfimo (38 registros), a integridade não é. A guarda certa é
uma linha: recusar (ou marcar) o lote cujo `nomeOrgaoJulgador` não corresponde ao
slug do dataset — e o teste de regressão já tem a fixture pronta, com URL e hash.

### 5.0.2 COLISÃO de tamanho entre 5ª e 6ª Turma (como foi detectada)

Entre as 305 competências medidas até aqui há **exatamente 2** colisões de
`Content-Length`, e as duas são entre os **mesmos dois datasets criminais**, nas
**mesmas duas competências** da janela rala:

| competência | quinta-turma | sexta-turma |
|---|---|---|
| 20260131 | **72.153 B** | **72.153 B** |
| 20260228 | **46.435 B** | **46.435 B** |

Coincidência de byte exato duas vezes, no mesmo par de datasets e no mesmo par de
meses, é improvável. Se o conteúdo for idêntico, a fonte está servindo o mesmo
payload para os dois órgãos nessas competências — e isso **quebraria a
aditividade** que verifiquei em disco (§2.0: zero `id_fonte` duplicado), porque o
coletor gravaria os mesmos acórdãos duas vezes. Volume envolvido é pequeno
(~119 KB), mas a integridade não é.

A fase H baixa os 4 arquivos (119 KB) e compara **sha256** e o
`nomeOrgaoJulgador` de dentro. É a única forma de decidir; tamanho igual não é
prova de conteúdo igual.

Total ≈ **482 requisições**. Tudo em `/tmp`; nada escrito em `/opt/wiki`.
Script de fechamento pronto e testado: `/tmp/stj-census/final.py`.

---

## 5.1 Confirmações independentes do contexto herdado

**A falha 7 de 7 é VERIFICADA** — mas não pelo journal, que só retém o boot atual
(`journalctl --list-boots` devolve 1 boot, desde 2026-09-15 04:13). A prova está em
`data/ops/owner_alerts.jsonl`: **7 alertas** `Unit wikijuridica-stj-acordaos-coleta
falhou`, em 2026-09-09, 09-10, 09-11, 09-12, 09-13, 09-14 e 09-15 (mais uma linha
`condicao normalizada` em 09-10). O timer é **DIÁRIO**
(`OnCalendar=*-*-* 09:40:00`, `RandomizedDelaySec=20min`) e a unit está `failed`
agora.

Do journal do boot atual, a mensagem exata (MEDIDO):

```
set 15 09:58:12 Starting wikijuridica-stj-acordaos-coleta.service...
set 15 09:58:17 robots: /dataset/ permitido, Crawl-Delay 10s
set 15 09:59:17 collect-stj-acordaos: dataset espelhos-de-acordaos-segunda-secao
                competencia 20240229: stjacordaos: decodificando o arquivo mensal
                de espelhos: invalid character '}' after array element
set 15 09:59:17 Failed with result 'exit-code'.
```

A execução inteira durou **65 s** — aborta cedo e desperdiça a janela diária toda.

**O "7 datasets seguintes nunca visitados" confere exatamente.** A ordem da unit é
terceira-turma, quarta-turma, **segunda-secao (3º)**, primeira-turma, segunda-turma,
primeira-secao, corte-especial, quinta-turma, sexta-turma, terceira-secao. Com
`return` no 3º (`coleta.go:176`), os que ficam para trás são exatamente **7**.

**O alinhamento do parser, reconferido em n muito maior.** O encargo trazia 21/21
por `content-disposition`. Sobre as competências já medidas nesta sessão:
**99 de 99 EXATAS** no formato `attachment; filename=<competencia>.json`. Zero
divergências.

**O arquivo de 599 B está CONFIRMADO, com o valor exato**:

```
espelhos-de-acordaos-segunda-secao  20240229   599 B   http=200
```

E é praticamente o único do gênero. Sobre 321 competências medidas, **só três**
ficam abaixo de 10 KB:

| dataset | competência | bytes |
|---|---|---|
| **segunda-secao** | **20240229** | **599** ← o que derruba a unit |
| terceira-secao | 20240229 | 6.184 |
| segunda-secao | 20240731 | 9.242 |

Os outros dois podem ou não decodificar — tamanho não é prova de malformação —,
mas a lista é curta e é exatamente o que quem for corrigir o `coleta.go:176`
precisa para escrever o teste de regressão. Nenhuma outra competência das 391 é
candidata a essa classe de defeito.

## 5.2 Cronograma de recuperação (DERIVADO do código e da unit)

`coleta.go:145` pula sem requisição o que já está no cursor (`RecursosPulados`), e
só a **última** competência de cada dataset leva GET condicional (304, 1
requisição, 0 byte). `MaxRecursos` conta `RecursosLidos`, que só sobe em leitura
real. Com `--max-recursos 100` e 391 competências faltantes:

- por disparo: 10 páginas de dataset + até 100 mensais + até 10 condicionais 304
  ≈ **120 requisições × 10 s ≈ 1.200 s**, dentro do envelope de 1.800 s do wrapper
  e do `TimeoutStartSec=2100`;
- **4 disparos** para drenar as 391 → com timer diário, **4 dias** depois de a
  causa ser corrigida.

A correção é no **chamador**, não no parser: `coleta.go:176` faz `return` no erro
de `ParseEspelhos`. Um `continue` com o motivo registrado (e a competência marcada
como ilegível, não como coletada) transforma "1 arquivo podre derruba 7 datasets"
em "1 arquivo podre perde 1 competência".

---

## 6. Estado das pendências

- [x] refutar a contagem de recursos herdada — 52 (segunda-turma 51), não 44/48/51/62
- [x] identificar a competência ausente na `segunda-turma` → **20221031**, lacuna real da fonte
- [x] provar que amostragem por stride não fecha a lacuna (CV mensal 101–125%)
- [x] confirmar o arquivo de 599 B (`segunda-secao 20240229`) e listar os < 10 KB
- [x] confirmar as 7 falhas por `owner_alerts.jsonl` (journal só tem 1 boot)
- [x] razão reg/MiB por dataset, dispersão e deriva temporal
- [x] refutar a hipótese de razão por tipo de órgão, com o mecanismo (§2.1)
- [x] aditividade: zero `id_fonte` duplicado em disco (§2.0)
- [x] réplica de `elegivel()` calibrada — reproduz 2.560 e 4.763 EXATOS
- [x] proxy de âncora sobre REPLEG calibrado (99,16%, viés −0,47% no pipeline)
- [x] round-trip do caminho que lê o formato da fonte (2.548, −0,47%)
- [x] decomposição candidato→página: `sem_item` 14,3% MEDIDO, anti-molde 39,0%
- [x] achado do `20220508.zip` (439,6 MiB comprimidos nos 10 datasets)
- [x] achado da janela rala da 5ª Turma e do pico geral de 2026-06
- [x] achado da colisão de `Content-Length` entre 5ª e 6ª Turma
- [x] censo integral por `HEAD` das 391 competências — **em fechamento**
- [ ] fases C1 (escala), C2 (ZIP), C3/D/E/F/G (razão e taxa), H (hash da colisão)
- [x] fase C1 — **escala PROVADA**, 3 de 3 `Content-Length` == `bytes_baixados`
- [x] fase C2 — ZIPs: **1.953,7 MiB descomprimidos**, baldes desde 2000
- [x] fase C3 — 18 amostras; razão real 220,9–347,8 (§2.0.1 corrige o §2.1)
- [x] bug do formato de data (`AAAAMMDD` × `AAAA-MM-DD`) achado e corrigido
- [x] fase D — Corte Especial EXATA: 3.637 acórdãos, 69,9/mês (controle ~68 ✓)
- [x] fases E/F/G/I — amostras de período recente nos datasets de razão fina
- [x] fase H — colisão confirmada por sha256: **a fonte serve arquivo da 1ª Turma**
- [x] rodar `/tmp/stj-census/final.py` → §7 (`/tmp/stj-census/RESULTADO.txt`)
- [x] chamar `advisor` e registrar "O que o advisor mudou" → §8

---

## 8. O que o advisor mudou

Duas chamadas: uma antes da campanha de rede, outra com o entregável já durável.

**Mudou de fato — e uma delas era um defeito real no número:**

1. **`EXATO` não estava exato.** A linha da Corte Especial agregava 55 arquivos
   (os 52 da fase D **mais** os 3 da fase C3, que estão noutro diretório e
   entravam duas vezes), dando 14,686 MiB contra os 12,869 do censo e projetando
   3.704 registros onde a contagem direta dá **3.634**. Corrigido: a linha agora
   conta só os 52, e a razão caiu de 287,8 para **282,4**. Rótulo "exato" é
   afirmação, e estava errado em 1,9%.
2. **A projeção de candidatos não tinha banda.** Agora cada dataset leva **IC 95%
   de Wilson** e o bloco novo sai como 1.443–2.590 (total 4.003–5.150). Importa:
   a 1ª Seção, segunda maior contribuinte, tem 75 acertos em 558 — 534 candidatos
   viram 431–656.
3. **Escopo da verificação de órgão dito com precisão.** Eu ia escrever "o defeito
   está confinado a 4 arquivos"; o correto é que 5 das 7 competências da janela
   rala da 5ª Turma não foram baixadas nem verificadas, e o teste por tamanho só
   pega o caso servido a dois datasets.
4. **Antes da campanha**: fazer a prova de escala C1 (`Content-Length` vs
   `bytes_baixados`) — ela passou 3/3, então **confirmou** em vez de mover número,
   mas sem ela a projeção inteira ficaria apoiada numa suposição; ler o *central
   directory* dos ZIPs por `Range` em vez de estimar compressão, o que trocou o
   chute "5–8×" por **1.953,7 MiB medidos**; escolher os meses de amostra a partir
   do censo em vez de stride; e listar os arquivos < 3 KB.

**Onde o advisor errou, e a medição corrigiu:** ele previu (e eu concordei) que as
turmas criminais teriam parcela procedimental **menor**, porque HC e RHC não estão
em `classesProcedimentais`. A medição inverteu: o habeas corpus não chega ao STJ
como HC, chega como **`AgRg no HC`** — 51,5% da 5ª Turma —, e `AGRG` está na
lista. Resultado: 99,1% procedimental, a maior do acervo. Está em §3.0.3.

**O que não veio do advisor:** a fase D (baixar as 52 competências da Corte
Especial), que é o que vindicou o controle de ~68/mês e expôs o erro da razão
transportada; o bug do formato de data, que só apareceu no dado real; e a
verificação por sha256 que achou a fonte servindo arquivo da 1ª Turma.

## 7. RESULTADO FINAL

Saída íntegra em `/tmp/stj-census/RESULTADO.txt`.

### 7.1 Tabela por dataset

| dataset | recursos (censo) | período | **MiB fonte** | **razão reg/MiB** | origem da razão | **acórdãos novos** |
|---|---|---|---|---|---|---|
| quinta-turma | 52 | 20220531–20260831 | **124,920** | 276,1 | amostra 4 arq / 4.549 reg | **34.492** |
| sexta-turma | 52 | 20220531–20260831 | **86,155** | 344,9 | amostra 4 arq / 4.587 reg | **29.715** |
| segunda-turma | 51 | 20220531–20260831 (falta 20221031) | **62,854** | 290,0 | amostra 4 arq / 1.998 reg | **18.226** |
| primeira-turma | 49 | 20220831–20260831 | **33,958** | 362,8 | amostra 5 arq / 1.513 reg | **12.320** |
| primeira-secao | 52 | 20220531–20260831 | **17,152** | 231,5 | amostra 5 arq / 558 reg | **3.971** |
| corte-especial | 52 | 20220531–20260831 | **12,869** | **282,4** | **EXATO — 52/52 contadas** | **3.634** |
| terceira-secao | 52 | 20220531–20260831 | **7,127** | 236,8 | amostra 3 arq / 259 reg | **1.688** |
| segunda-secao | 31 | 20240229–20260831 | **5,172** | 331,3 | amostra 3 arq / 283 reg | **1.714** |
| **TOTAL NOVO** | **391** | | **350,206** | | | **105.760** |
| *(já em disco)* | *128* | *20220531–20260831* | *180,398* | *—* | *MEDIDO* | *60.221* |

A linha da Corte Especial é **contagem**, não projeção: as 52 competências foram
baixadas e os registros contados — 3.637 brutos, 3 sem ementa, **3.634 líquidos**
(o que o coletor grava). Os bytes baixados batem com o censo em **0,0004%**.

### 7.2 Corpus total pós-recuperação

| | acórdãos | marca |
|---|---|---|
| em disco hoje | **60.221** | **MEDIDO** |
| novos da recuperação | **105.760** | **PROJETADO** (MiB exato × razão medida) |
| **TOTAL** | **165.981** | |
| piso da banda | **154.747** | |
| teto da banda | **172.721** | |

**Banda −11,0% / +6,6%, e ela é MEDIDA**: é o erro que os estimadores de razão de
3 meses cometeram contra as 3 séries de razão agregada conhecida (§4.6). Ela
incide só sobre os 102.126 registros cuja razão veio de amostra; os **3.634 da
Corte Especial são EXATOS** e não pagam banda. O censo de MiB não contribui erro
nenhum — a escala está provada (§4.6, C1: 3 de 3 `Content-Length` ==
`bytes_baixados`, mais os 82 downloads em que o tamanho baixado bateu com o
`Content-Length` anunciado).

**O plano falava em "~210.000". A medição diz 165.981 (154.747–172.721): o plano
está ~26% alto**, e a extrapolação de 9 meses com ±30% errava por dois motivos
independentes — faltavam 52 competências por dataset (não 9) e a razão
transportada era alta demais para 4 dos 6 datasets ausentes.

### 7.3 Custo de download

| | valor | marca |
|---|---|---|
| competências a baixar | **391** | MEDIDO |
| bytes | **350,2 MiB** | **MEDIDO** (soma exata de `Content-Length`) |
| disco ocupado em JSONL | **370,9 MiB** | DERIVADO (×1,059 medido em disco) |
| requisições | 391 mensais + 40 páginas de dataset + 40 condicionais 304 | DERIVADO |
| tempo a `Crawl-Delay: 10` | **4.710 s = 78,5 min** | DERIVADO |
| por disparo (`--max-recursos 100`) | ~1.200 s = 20 min (envelope do wrapper: 1.800 s) | DERIVADO |
| disparos | **4** → **4 dias** com o timer diário | DERIVADO |

A banda não é o limitador: 350 MiB é irrelevante para a máquina (266 GB livres em
`/opt`). O limitador é o `Crawl-Delay`, e ele é obedecido.

### 7.4 Elegibilidade — a projeção linear seria MUITO errada

| | linear global (4,25% / 7,91%) | **por dataset, taxa MEDIDA** | diferença |
|---|---|---|---|
| candidatos base | 7.056 | **4.485** | **−36%** |
| com item transcritível | 11.248 | **4.091** | — |
| páginas | 6.857 | **3.496** | **−49%** |

Detalhe por dataset — taxa base MEDIDA sobre os arquivos baixados, com **IC 95%
de Wilson** sobre o número de candidatos:

| dataset | acórdãos novos | taxa base | IC 95% da taxa | candidatos | IC dos candidatos | páginas |
|---|---|---|---|---|---|---|
| primeira-secao | 3.971 | **13,44%** | 10,86–16,52% | 534 | 431–656 | 260 |
| segunda-turma | 18.226 | 2,25% | 1,69–3,00% | 411 | 308–547 | 178 |
| sexta-turma | 29.715 | 1,37% | 1,08–1,75% | 408 | 319–521 | 241 |
| corte-especial | 3.634 | **4,02%** | 3,43–4,71% | **146** (EXATO) | 125–171 | 83 |
| primeira-turma | 12.320 | 0,99% | 0,60–1,63% | 122 | 74–201 | 65 |
| quinta-turma | **34.492** | **0,35%** | 0,22–0,57% | **121** | 75–197 | 69 |
| terceira-secao | 1.688 | 6,18% | 3,84–9,80% | 104 | 65–165 | 64 |
| segunda-secao | 1.714 | 4,59% | 2,70–7,70% | 79 | 46–132 | 48 |
| **novos** | **105.760** | **1,82%** | | **1.925** | **1.443–2.590** | **1.008** |
| em disco (oráculo) | 60.221 | 4,25% | — | 2.560 | — | 2.488 |
| **TOTAL** | **165.981** | | | **4.485** | **4.003–5.150** | **3.496** |

**É PROJEÇÃO LINEAR, e digo onde ela é frágil:**

1. A taxa de candidato é **MEDIDA por dataset** sobre registros reais — isso não é
   linearidade, é medição. A fragilidade está no n de cada amostra (de 259 a 4.587
   registros); as duas Seções pequenas têm IC largo.
2. O passo **candidato → página** é que é linear de verdade: uso o rendimento
   anti-molde de **61,0%** derivado do disco (2.488 de 4.081). Esse filtro é
   **sequencial e ordem-dependente** (§3.1), então não escala linearmente. Dois
   efeitos medidos puxam em sentidos opostos: o conjunto `aceitas` cresce (contra)
   e a matéria nova reduz colisão de molde (a favor). Não resolvo isso sem rodar o
   gerador, o que é escrita e está fora deste encargo.
3. A camada da IA local multiplica por **1,861** em disco (2.560→4.763). **Não
   aplico esse multiplicador aos novos**: o writeback cobre só registros já em
   disco. Se valer igual, o total c/ IA iria a ~8.328 — número **CONDICIONAL**, e
   ~64% desse ganho é parser (barato), ~36% é fila de Ollama.

**E sim, há motivo MEDIDO para a taxa diferir nos órgãos ausentes** — é a
resposta direta ao item 4 do encargo: §3.0.3. A 5ª Turma é 99,1% procedimental
(`AgRg no HC` = 51,5% dela) e rende **0,35%**; a 1ª Seção é 67,4% procedimental e
rende **13,44%**. Trinta e oito vezes de diferença. A 5ª Turma sozinha traz
**33% dos acórdãos novos e 6% dos candidatos novos**.

### 6.1 Como TERMINAR isto se a sessão morrer antes

Tudo o que a medição produziu está em `/tmp/stj-census/` (regenerável, mas custa
~80 min de crawl-delay para refazer — **não apague sem necessidade**):

| arquivo | conteúdo |
|---|---|
| `sizes.jsonl` | uma linha por competência: dataset, competência, `Content-Length`, `content-disposition`, `Last-Modified`, URL |
| `escala.json` | prova de escala da fase C1 (`Content-Length` vs `bytes_baixados`) |
| `zips.jsonl` | central directory dos 10 ZIPs: entradas, bytes descomprimidos, razão |
| `amostras/*.json` | arquivos mensais brutos das fases C3/E/F/G (`<dataset>__<competência>.json`) |
| `corte-especial/*.json` | as 52 competências da Corte Especial (fase D) |
| `colisao/*.json` | os 4 arquivos da fase H |
| `censo.log`, `faseC..H.log` | log de cada fase, com http e exit |
| **`final.py`** | **agregador pronto e testado — `python3 /tmp/stj-census/final.py` imprime tudo** |

Passos que faltam: (1) `python3 /tmp/stj-census/final.py`; (2) colar a tabela
final nesta seção; (3) `advisor`; (4) relatório. As seções 1 a 5 deste arquivo já
estão fechadas e não dependem do que falta.
