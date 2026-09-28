# Medição read-only: motor de acórdãos + fila do cérebro (2026-09-15)

MODO: somente leitura. `-seco` confirmado não-gravante por leitura (`executar`,
main.go:213-219, retorna antes de `gravaPortfolio`/`gravaShard`, os ÚNICOS
`os.WriteFile` do arquivo — :2244 e :2265).

## ACRÉSCIMO DO COORDENADOR — divergência das réguas (PRIORIDADE)

### Não são 2 divergências, são 5 (todas para o lado severo)

| # | eixo | GERADOR (`cmd/generate-acordao-pages`) | GATE (`internal/v2bodyneardup` / `internal/quality`) |
|---|---|---|---|
| 1 | janela | 3-gramas (`shingleMold=3`, :103) | 5-gramas (`ShingleSize=5`, neardup.go:62) |
| 2 | dígitos | `[0-9]+` → `"N"` (:2187-2196) | preservados (BUG-137 corrigiu p/ NÃO partir número) |
| 3 | stopwords | mantidas (`strings.Fields` cru) | **removidas** (`legalsignature.Tokenize`, 33 stopwords + tokens de 1 char) |
| 4 | headings | **incluídos** (`corpoDaPagina`) | **excluídos de propósito** (`AssembleBody`, neardup.go:152-154) |
| 5 | limiar | 0,70 | 0,70 (base) e **0,82** no gate vivo (`quality.go:84`) |

As nº 3 e nº 4 não constavam do acréscimo e são as que mais pesam.

### Medição (população: as 1.134 páginas publicadas de /jurisprudencia/ — 1.074
`stj-tema-derivado-01` + 60 `stf-informativo-derivado-01` — que o PRÓPRIO gerador
carrega como base de comparação; 642.411 pares). Parse validado: 1.134 páginas
(o gerador declarou 1134) e paridade de `word_count` mediana |dif| = 0.

| régua | p50 | p90 | p99 | máx | pares ≥0,70 |
|---|---|---|---|---|---|
| GERADOR (3-gram, dígito→N, com heading, sem stopword-drop) | 0,3802 | 0,5205 | 0,6145 | **0,7701** | **135** |
| GATE real (5-gram, dígito preservado, sem heading, stopword-drop) | 0,1291 | 0,2020 | 0,2640 | **0,5193** | **0** |

O MÁXIMO sob a régua real (0,5193) fica abaixo do p90 da régua do gerador.
Sob o limiar do gate vivo (0,82): zero pares, sob as duas réguas.

### Item 1 — a MATRIZ (condicional), sobre os 135 pares que a régua do gerador recusa

| | régua real aprova (<0,70) | régua real recusa |
|---|---|---|
| **gerador recusa (≥0,70)** | **135 de 135** | 0 |
| gerador aprova | — | **0** |

Score desses 135 pares SOB A RÉGUA REAL: min 0,2113 · p50 0,3034 · **máx 0,5193**.
Nenhum chega a 0,18 do limiar de 0,70, nem a 0,30 do limiar vivo de 0,82.
O inverso é ZERO: a régua real nunca recusa o que o gerador aprova. A régua do
produtor é estritamente mais severa, sem nenhum ganho compensatório.

### Item 4 — um defeito de cada vez (base 135 pares ≥0,70)

| variante | p50 | máx | pares ≥0,70 |
|---|---|---|---|
| régua do gerador, como está | 0,3802 | 0,7701 | 135 |
| **sem neutralizar dígito** (resto igual) | 0,3188 | 0,6879 | **0** |
| **com stopword-drop** (resto igual) | 0,3149 | 0,7273 | **1** |
| **5-gram** (resto igual) | 0,3279 | 0,7414 | 6 |
| **sem heading** (resto igual) | 0,3313 | 0,7377 | 14 |

Cada um dos QUATRO defeitos, corrigido sozinho, elimina de 121 a 135 das 135
recusas. A neutralização de dígito a zera.

### Item 2 — decomposição por camada (régua do gerador, isolada)

| camada | p50 | p90 | máx | pares ≥0,70 |
|---|---|---|---|---|
| só headings | **1,0000** | 1,0000 | 1,0000 | 557.002 |
| só FAQ (q+a) | **0,6867** | 0,8193 | 1,0000 | 292.228 |
| só opening | 0,4412 | 0,7778 | 1,0000 | 92.126 |
| **só sections.text (a camada autoral)** | **0,2469** | 0,3983 | 0,7162 | **1** |

Hipótese do coordenador CONFIRMADA: o score é dominado pela mobília do template
(headings idênticos, FAQ), e a única camada onde unicidade importa é invisível.

### Efeito do dígito no template de ACÓRDÃO é maior que na população medida
Os 6 headings do gerador embutem o número do processo (main.go:1597-1628:
`"A fundamentação do " + sigla + " " + numero + ", ..."`). Com dígito→N, os 6
viram string idêntica em TODA página de acórdão. Na página-amostra mediana
(n=1, `jur-stj-resp-2112099`): 11,5% dos tokens do corpo contêm dígito, 28
números distintos colapsam em "N", e 20,6% da assinatura de 3-gramas contém o
"N" colapsado. Logo o efeito medido nas 1.134 é PISO para a família acórdão.

### Evidência na PRÓPRIA família acórdão (sob a régua do gerador)
A linha `molde:` que o gerador imprime dá mediana **0,4780** (500 aceitas) e
**0,4478** (2.488 aceitas), máximo 0,6999 em toda passada. Isso é medido **entre
páginas que já passaram no corte <0,70** — distribuição truncada —, e ainda
assim a mediana supera a das páginas tema NÃO truncadas sob a MESMA régua
(0,3802). Consistente com o colapso do número do processo.

### Limite honesto desta medição
Os corpos das 1.405 recusadas por molde NÃO são reconstruíveis em modo leitura:
o `-seco` só imprime a amostra mediana e o motor descarta a página recusada.
A matriz 135 de 135 é sobre a população MEDIDA (as 1.134 publicadas). Para o
template de acórdão a direção é a mesma ou mais forte (os 6 headings embutem
`sigla + numero`, main.go:1597-1628; 20,6% da assinatura da amostra contém o "N"
colapsado). Por isso NÃO extrapolo um número para as 1.405 além da faixa
declarada: **2.488 ≤ rendimento ≤ 3.893**.

## TAREFA 1 — curva de rendimento

| passada | candidatos iterados | páginas | rendimento | parede | exit |
|---|---|---|---|---|---|
| `-limite 500` | 1.260 | 500 | 39,7% | **98,6 s** (RSS 190 MB) | 0 |
| `-limite 1000` | 2.365 | 1.000 | 42,3% | **3 min 21 s** | 0 |
| `-limite 2000` | (em curso) | 2.000 | — | — | — |
| `-limite 5000` | **4.763 (exauriu)** | **2.488** | **52,2%** | **12 min 15 s** (RSS 359 MB) | 0 |

Todas as passadas imprimiram a MESMA base (60.221 acórdãos / 4.763 candidatos /
1.134 publicadas): a base não se moveu entre as medições, e o rendimento é
determinístico. **O tempo de parede, não**: só a l500 foi medida limpa. A l5000
teve a medição de réguas em Python concorrente (load 5,14 → 17,54), a l1000 teve
o relançamento do Python, e a l2000 teve um shell de espera meu em busy-wait
(erro meu: `read -t N < /dev/zero` gira a CPU; o certo é `sleep`). Os tempos são
TETO SUPERIOR, não medida limpa.

**Prova de exaustão**: 2488 + 1405 + 682 + 165 + 22 + 1 = **4763** = o total de
candidatos. A passada não parou por limite.

**A premissa de que 39,7% é TETO está REFUTADA pela medição.** O rendimento SOBE
com a profundidade: nos primeiros 1.260 candidatos, 39,7%; nos 3.503 restantes,
1.988/3.503 = **56,8%**. O motor não degrada com a fatia mais pobre.

Rendimento por SEGMENTO da fila (cada passada é independente e determinística):

| candidatos | páginas no segmento | rendimento | molde no segmento |
|---|---|---|---|
| 1 – 1.260 | 500 | 39,7% | 532 (42,2%) |
| 1.261 – 2.365 | 500 | 45,2% | 461 (41,7%) |
| 2.366 – 4.763 | 1.488 | **62,1%** | 412 (**17,2%**) |

Causa medida da inversão: o `molde_acima_do_limiar` é FRONT-LOADED. A fatia mais
rica por evidência compartilha as mesmas âncoras de alta frequência (art. 85 §2º
do CPC etc.), então é lá que a régua do molde mais morde — e é lá que ela está
errada. Na direção oposta, `ementa_sem_item_transcritivel` é BACK-loaded (6,7%
no primeiro segmento, 20,1% no terceiro): à medida que a evidência afina, a
ementa deixa de ter item transcritível. São defeitos diferentes em pontas
diferentes da fila.

### Recusas de `montaPagina` sobre o poço inteiro (4.763)
| motivo | n | % dos candidatos |
|---|---|---|
| `molde_acima_do_limiar` | **1.405** | 29,5% |
| `ementa_sem_item_transcritivel` | 682 | 14,3% |
| `citacao_abaixo_do_minimo_oficial` | 165 | 3,5% |
| `camada_autoral_nao_deixa_espaco_para_citacao` | 22 | 0,5% |
| `rota_duplicada_no_corpus` | 1 | 0,02% |

O molde sozinho é a MAIOR perda do motor — e é a régua que a medição das seções
acima mostra estar calibrada errado.

### Resposta: quantas páginas o motor entrega hoje
**2.488 páginas montadas** sobre o corpus de 60.221 acórdãos. Ressalvas:
- *montadas ≠ publicáveis*: a cadeia do §5 (severidade, auditor, release) não
  rodou sobre elas. 2.488 é o TETO do publicável, não o número final.
- Faixa se a régua do molde for corrigida: **2.488 ≤ rendimento ≤ 3.893**
  (2.488 + os 1.405 recusados por molde).
- O tempo de parede de 12 min 15 s foi medido SOB CARGA (load 5,14 no início,
  17,54 no fim — a medição de réguas em Python rodava junto). É teto superior.
- A nota de `main_test.go:583-589` ("n=1.569 não terminou em 10 minutos") fica
  superada **no fato** (2.488 páginas em 12 min 15 s, exit 0, não empacou), mas
  **não no aviso de desenho**: o custo é O(n²) com DOIS laços que crescem. Numa
  passada real (não-seca), o shard de 2.488 alimenta `previas`, e `roda` passa a
  rodar DUAS comparações por candidato — `parecida` contra as 1.134 `aceitas` e
  `parecidaComPrevia` contra as 2.488 do shard —, custo por candidato ~×2,1;
  `distanciaDeMolde` é n²/2 à parte. Indexar o anti-molde (bucket por shingle ou
  MinHash) continua sendo a correção certa.

### Parcela atribuível à IA local (DERIVADA, não medida)
Não há flag para desligar a sobreposição (`main.go:184-187`: só `-raiz`,
`-limite`, `-seco`), e mexer em arquivo é proibido — então é derivação declarada.
Com sobreposição: 4.763 candidatos → 2.488 páginas. Sem: 2.560 candidatos.
Aplicando o rendimento medido aos 2.203 candidatos que só existem por causa da IA:
- piso (rendimento da fatia rica, 39,7%): **~875 páginas**
- ponto (rendimento global, 52,2%): **~1.151 páginas**
- teto (rendimento da cauda, 56,8%): **~1.251 páginas**

A derivação é aproximada porque a sobreposição também muda a ORDEM: ela injeta
peso mediano 6 em `ordenaPorEvidencia` (`peso = 3×dispositivos + 3×súmulas +
precedentes`; sobreposição = 35.082 acórdãos, mediana 1 dispositivo + 1 súmula,
p90 = 4 e 3, máx 30 e 9), então o candidato resgatado sobe na fila e a sequência
do anti-molde muda junto.

## BUG DE GRANDEZA no piso de 250 palavras — CONFIRMADO E MEDIDO

Código: `pisoEmentaPalavras = 250` (main.go:402) é aplicado em :532 a
`contaPalavras(r.Ementa)` — a **ementa de ENTRADA sozinha**. O outro 250 do
arquivo, `pisoAutoral = 250` (main.go:92), é o piso da **camada autoral da
PÁGINA**. Mesmo número, duas grandezas diferentes. O que a ementa precisa de
fato entregar é a camada citada, cujo mínimo é `minimoCitacaoOficial = 25`
(main.go:96) — **dez vezes menor**.

Replicação validada contra os contadores do próprio gerador, exatamente:
corpus 60.221 ✓ · procedimental 49.807 ✓ · ementa curta 4.500 ✓ ·
5.914 − 1.151 (`sem_ancora`) = 4.763 candidatos ✓.

Das **4.500** barradas por `ementa_curta_demais_para_duas_camadas`:
- mediana 161 palavras, p90 231, máx 249, mín 1
- **4.496 de 4.500** têm ≥ 25 palavras (o mínimo duro da camada citada)
- **4.476 de 4.500** têm ≥ 42 palavras — e 42 é a MENOR camada citada entre as
  2.488 páginas que o motor ACEITOU (l5000: `citado: min 42`)
- só **4** têm menos de 25 palavras

Faixas: [0,25)=4 · [25,42)=20 · [42,100)=691 · [100,150)=1.204 ·
[150,200)=1.402 · [200,250)=1.179.

A camada autoral não sai da ementa: sai dos metadados (órgão, relator,
dispositivos, precedentes, contagens do acervo). Na passada exaustiva (2.488
aceitas) ela tem **mínimo 355 palavras** (nas passadas de 500 e 1.000 o mínimo
foi 409) — sozinha já supera o `pisoAutoral` de 250. Logo o piso
de 250 na ENTRADA barra 4.476 acórdãos cuja ementa é mais longa que a menor
citação que de fato produziu página aprovada.

**Ressalva não medida**: parte dos 4.476 cairia depois em
`ementa_sem_item_transcritivel` (o corte é por item numerado, não por palavra) —
quantos, não é medível sem rodar `montaPagina` sobre eles, o que exigiria mudar
código. O número medido é o do piso, não o rendimento final deles.

## TAREFA 2 — fila `data/ai/fila.sqlite` (o prompt dizia `var/cerebro/`: não existe)
Taxonomia conferida: 36 `resposta cortada`, 3 `HTTP 500`, 5 `embed_pagina`.

### Veredito: (b) ementa densa demais para o teto — NÃO é laço degenerado
1. **Dose-resposta monótona** da taxa de falha por tamanho da entrada:
   0-1k **0,00%** (0/1632) · 1-2k 0,07% · 2-3k 0,35% · 3-4k **1,22%** ·
   4-5k **1,94%** · 5-6k **5,56%**. Laço degenerado não teria dose-resposta.
2. **O teto é realmente atingido por trabalho legítimo**: entre as 5.930
   concluídas com `eval=` no resumo, o máximo é **1.010 tokens** (teto 1.024),
   163 passaram de 512 e 8 chegaram a ≥900 — devolvendo 16 a 29 dispositivos.
   Não há vão entre as concluídas e as 36: são a continuação da cauda.
3. **As 36 são a cauda superior**: entrada mediana 3.715 chars (p89 das
   concluídas) vs 1.640 das concluídas; 30 menções de dispositivo legal
   (p91,6) vs 5. 31 de 36 trazem ementa estruturada CNJ ("I. CASO EM EXAME")
   contra 2.038 de 7.689 (26,5%) das concluídas.
4. **O padrão do laço degenerado NÃO aparece**: laço se apresenta como muitos
   tokens com POUCOS itens. As 8 concluídas que chegaram a 900-1.010 tokens
   devolveram 16, 17, 18, 20, 21, 23, 23 e 29 dispositivos — 32 a 58 tokens por
   item. Nenhuma das 5.930 exibe alto-token/baixo-item. (Este é o argumento que
   exclui (a) na fronteira; a dose-resposta sozinha não excluiria, porque um
   laço também pode correlacionar com o tamanho da entrada.)

Correção que a evidência indica: **partir a entrada por item numerado**
(não "terminal na primeira falha", que era a correção da hipótese (a)).

**Ressalva de desenho**: 7 das 36 têm ZERO item numerado (distribuição:
0,0,0,0,0,0,0,1,1,1,4,5,6,7,7,7,8,8,8,9,9,9,9,9,9,10,10,11,11,11,11,11,11,12,12,12).
Partir por item numerado não alcança essas 7 — elas pedem corte por parágrafo ou
por dispositivo. E a contribuição MARGINAL do modelo sobre o parser (que já
entregou 2 a 18 dispositivos para cada uma das 39) **não foi medida**.

Ressalva medida contra (b) puro: 63,2% das concluídas (4.863) têm entrada ≥ o
PISO das 36 (1.307 chars) e concluíram, e 45 concluídas têm entrada ≥ o MAIOR
das 36. Tamanho é necessário, não suficiente — o que decide é a densidade de
dispositivos, não o número de caracteres.

### Custo já pago e a pagar
- 36 tarefas × 3 tentativas × (512+1024) de decode = **4,74 h de parede**
  queimadas (pior caso 15,0 min; média 7,9 min/tarefa). 3 HTTP500: 17,4 min.
- Estoque pendente: 34.796. Aplicando as taxas medidas por faixa:
  **~63 falhas projetadas ≈ 8 h de CPU** a queimar sem correção.

### Os 3 HTTP 500 e as 5 lápides
- **5 de 5 lápides CONFIRMADAS**: cada uma tem irmã `concluida` com o hash NOVO
  do texto, e a irmã concluiu ANTES (02:37-04:40) de o erro ser gravado (08:24).
  Zero trabalho perdido.
- **3 HTTP 500**: `956683`, `957550`, `957684`, em 2026-09-14 às 16:22, 20:27 e
  23:04 — espalhados por ~7 h, NÃO um evento único do Ollama. Não têm irmã na
  fila (n=1 cada) e não há pendente para elas.
- **Conteúdo NÃO se perdeu nas 39**: todas as 36 + as 3 já constam em
  `data/ai/extracoes_dispositivos.jsonl` por `modelo: "parser"`
  (`revisao: parser_regenerado_v4`), com 2 a 18 dispositivos cada. O que se
  perdeu foi a contribuição MARGINAL do modelo sobre o parser, mais a CPU.
