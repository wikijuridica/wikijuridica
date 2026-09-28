# RUNBOOK — P4 (arquitetura de gates: fato × publicidade × juízo) e P5 (atribuição)

Sessão 2026-09-15, PLAN MODE: nada abaixo foi executado. MEDIDO = medido por mim
nesta sessão, read-only, com o comando ao lado. DERIVADO = do diagnóstico.

---

## 0. CORREÇÕES AO DIAGNÓSTICO — leia antes do passo 1

### 0.1 São DOIS gates bloqueantes, ambos a 0,70 — e há um SEXTO eixo: o ESCOPO

| régua | arquivo | n-grama | dígitos | corpo | escopo da comparação | limiar |
|---|---|---|---|---|---|---|
| `check-v2-body-near-duplicates` | `cmd/check-v2-body-near-duplicates/main.go:41` → `internal/v2bodyneardup` | **5** | preservados | `AssembleBody` (sem heading) | estoque todo | **0,70** |
| `check-derived-authorial-floor` EIXO 3 | `tools/check-derived-authorial-floor:288-289` | **3** | preservados | `corpo_v2` (sem heading) | **por FAMÍLIA de shard** | **0,70** |
| gerador de acórdãos | `cmd/generate-acordao-pages/main.go:102-103` | 3 | **→ "N"** | `corpoDaPagina` (**COM heading**) | **`/jurisprudencia/` inteira, sem separar família** | 0,70 |

O 0,82 é `internal/quality:84` — o relatório de qualidade. MEDIDO: `grep` de
`neardup|NearDuplicate` em `internal/v2ingest/*.go` devolve **zero** — o ingest
**não** aplica near-dup. Não há terceiro gate.

**Sexto eixo, MEDIDO por mim** (`practice_area == "jurisprudencia"` sobre os 879
shards, excluindo o prefixo do próprio gerador): o gerador compara contra **1.134
páginas num poço só** (1.074 `stj-tema-derivado-01` + 60 `stf-informativo-derivado-01`);
o gate compara **1.074 / 60 / 0 separadamente**. O gerador produz pares
**cross-família** (acórdão × tema) que o gate nunca forma — e é justamente entre
famílias diferentes que a mobília compartilhada pesa mais.

### 0.2 ACHADO BLOQUEANTE: o gate é CEGO para esta família

`tools/check-derived-authorial-floor:279-287` (`FAMILIAS_CANAIS_DERIVADOS`) lista
`diarios-municipais`, `leis-motor`, `noticias-oficiais`, `stf-informativo-derivado`,
`stj-sumula-derivada`, `stj-tema-derivado`. **Não há `stj-acordao-derivado`.**
MEDIDO: `grep -n stj-acordao tools/check-derived-authorial-floor` → zero linhas.
E o shard `data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` (main.go:70)
**não existe** — 879 shards no disco, nenhum `stj-acordao-*`: este gerador nunca
gravou uma página.

O próprio gate avisa em `:271-278`: *"FAMÍLIA NOVA ENTRA AQUI OU NASCE FORA DO
GATE"*. Alinhar a régua sem registrar a família produz gerador correto medido por
gate que não olha para ele. **Registro é pré-requisito, não consequência.**

### 0.3 Dominância estrita: MEDIDA por mim, em população independente

Python sobre `stj-tema-derivado-01.jsonl`, stride determinístico, **150 de 1.074
páginas** = 11.175 pares, ~4 s:

| variante | p50 | p95 | máx | pares ≥ 0,70 |
|---|---|---|---|---|
| **A** gerador como está (3g, +head, digN, FAQ intercalado) | 0,3905 | 0,5583 | **0,7226** | **3** |
| **B** só tira HEADINGS | 0,3440 | 0,5149 | 0,6877 | **0** |
| **C** só tira neutralização de dígito | 0,3280 | 0,4635 | 0,6126 | **0** |
| **D** só ordem do FAQ | 0,3884 | 0,5558 | 0,7226 | 3 |
| **E** régua do gate (3g, −head, +dig, ordem do gate) | 0,2784 | 0,4153 | **0,5697** | **0** |
| **F** gate-irmão 5-gramas | 0,1971 | 0,3074 | 0,4229 | 0 |
| **camada HEADINGS sozinha** | **1,0000** | 1,0000 | 1,0000 | **10.658 de 11.175** |

Dos 3 pares que a régua do gerador recusa, a do gate aprova **3 de 3**; o inverso
é **0**. Máximo sob a régua real 0,5697 contra limiar 0,70: **o limiar nunca
morde.** Reproduz o diagnóstico em população diferente da dele. A ordem do FAQ
(D) é praticamente **inerte** — 0,3905 → 0,3884, mesmos 3 pares: corrigi-la é
fidelidade, **não** recupera página, e não pode ser creditada por ganho.

### 0.4 CORREÇÃO DE ROTA: tire os HEADINGS, MANTENHA os dígitos

O enunciado manda "alinhar nos cinco eixos". A medição diz que isso é mais do que
o necessário e **quebra uma guarda legítima**:

- `main_test.go:274-277` troca todo dígito por `4242` e exige que o anti-molde
  **pegue** a irmã. Tirar a neutralização deixa esse teste vermelho — e ele existe
  pelo defeito real "Tema 1154" × "Tema 4" (`cmd/measure-molde-trigrama/main.go:17-21`).
- `internal/legalsignature/signature.go:93-111` documenta o defeito OPOSTO
  (BUG-137): partir "2.204" em "2" e "204" criava molde onde não havia.

Variante **B** já zera as recusas mantendo a neutralização e o teste que a prova.
Heading é mobília (p50 = 1,0000): medi-lo é medir o template, e **esse** é o
defeito. Dígito é severidade legítima.

**Enunciado honesto, e é assim que vai escrito no código**: depois da correção o
**corpo e a tokenização** do gerador são os **mesmos** do gate; a neutralização de
dígito permanece como **severidade extra declarada e testada**. Não se escreve
"régua idêntica" — quem ler isso e achar o delta do dígito desconfia do runbook
inteiro. Escreve-se "mesmo corpo, mesma tokenização, um eixo a mais, com teste".

### 0.5 `corpoDaPagina` NÃO pode mudar

Ela alimenta `WordCount` e as bandas de `:1664`, `:1678`, `:1681`, e é o espelho
declarado de `v2ingest.bodyWordCount` (headings incluídos — correto para contagem).
Mexer nela move a banda 350–700 e os cortes de saída ao mesmo tempo que a régua, e
o antes/depois deixa de atribuir. **Função nova, não edição.**

### 0.6 Dois instrumentos existentes NÃO servem como oráculo

- `cmd/measure-molde-trigrama/main.go:137` imprime "dígitos neutralizados"
  **incondicionalmente**: a neutralização não é atada a `-shingle`, então
  `-shingle 5` ali **não** é a régua do gate.
- **DEFEITO NOVO, MEDIDO**: `main.go:61-64` lê o FAQ como `question`/`answer`; o
  JSONL v2 e o gate usam **`q`/`a`** (MEDIDO: `sorted(faq[0].keys())` → `['a','q']`).
  Ele tem medido corpos **sem FAQ nenhum** — os números dele (máx 0,7304, 32 pares)
  são de outra população. I1 **não** reusa esse carregador.

O oráculo do gate é `./tools/check-derived-authorial-floor` e
`./tools/check-v2-body-near-duplicates`. MEDIDO: não existe
`tools/test_check_derived_authorial_floor*`.

---

## 1. PROIBIÇÕES DESTE BLOCO

| proibido | por quê |
|---|---|
| editar `internal/quality` ou `internal/legalsignature` | **no grafo do validador** (MEDIDO: `go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` = 98 pacotes, ambos presentes). Obriga `generate ./internal/v2ingest` + atestação no mesmo commit e 25+ testes após ~10 min. **Importar é livre; editar não.** |
| `cmd/check` sem argumento | roda TODOS os gates; já levou o load a 52 |
| padrão full-tree (`./` + três pontos) | hook aborta exit 2; use `./internal/... ./cmd/...` |
| `git reset/checkout/stash/clean/revert` | contrato; rollback é sempre **para frente** |
| `-limite` default (30) em censo | `roda()` faz `break` no limite (main.go:271): as recusas contadas são só as de antes dele. Censo exige `-limite 99999` |
| baixar `limiarMolde` para passar | fraude operacional (`unicidade_test.go:92-94`) |
| filtrar itens no P5 | P5 **classifica e rebaixa**, não trava (passo 14) |

MEDIDO fora do grafo: `internal/v2bodyneardup`, `internal/cerebro`,
`internal/checks`, `cmd/generate-acordao-pages`, `cmd/generate-revisao-extracoes`,
`internal/stjacordaos`. **P4 e P5 não pagam reatestação** se a proibição acima valer.

**Janela de commit Go**: a bancada diária segura `/tmp/opt-wiki-agent-heavy.lock`
das ~04:47 às ~05:50 -03 (`ops/systemd/wikijuridica-qualidade-diaria.service:19`).
Commit que toca Go vai sob `flock -w 600 /tmp/opt-wiki-agent-heavy.lock`, com
`git add` e `git commit -F` em **comandos separados** e o índice vazio antes: o
pre-commit compila a closure do ÍNDICE, não do pathspec.

---

## 2. INSTRUMENTOS A CRIAR

| # | nome | mede | exit | grava |
|---|---|---|---|---|
| I1 | `cmd/measure-regua-molde` | a mesma amostra sob as 3 réguas + a matriz de dominância (recusa-A × aprova-B) + a camada heading isolada. FAQ por **`q`/`a`**. Aceita `-familia` (isola) e `-area` (o poço do gerador) para medir o **eixo do escopo** | 0 sempre (mede, não reprova) | `data/ops/regua_molde.jsonl`; `-ledger ""` = nada |
| I2 | `TestCorpoParaMoldeEspelhaOGate` em `cmd/generate-acordao-pages/` | `corpoParaMolde(p)` **byte a byte** igual a um `corpoCanonicoDoGate(p)` escrito **à mão no teste**, sobre amostra por stride de páginas reais | falha = divergência | — |
| I3 | `tools/check-familia-no-mapa-do-gate` | todo shard de `v2_pages` cuja `practice_area` seja canal derivado tem família em `FAMILIAS_CANAIS_DERIVADOS` | 1 se órfã | — |
| I4 | `cmd/measure-atribuicao-dispositivo` | contra o gabarito: % com o artigo dentro do `texto_citado`, % que só passa pela folga do texto inteiro, % sem nenhum, + `fora_do_corpus` | 0 sempre | `data/ops/atribuicao_dispositivo.jsonl`; `-ledger ""` = nada |
| I5 | `gabarito-atribuicao-<data>.jsonl` | 100 dispositivos por stride, conferidos **mecanicamente** contra `data/legal-corpus` | — | `.agents/runtime/gabarito/`, com `sha256`, data, método e stride |
| I6 | `TestFallbackDeItensNaoMudaOEstrito` | fixture de ementas que HOJE parseiam: saída de `itensTranscritiveis` byte a byte igual depois do fallback | falha = regressão | `cmd/generate-acordao-pages/testdata/` |

Nenhum pede credencial, cadastro, decisão ou revisão de conteúdo.

---

## 3. LINHA DE BASE

### 1. Bancadas verdes antes de qualquer edição
- **ANTES**: `cat /proc/loadavg`; se load1 ≥ 12, `./tools/check-load-headroom --max 12`
  sai 1 e manda **avançar outra frente**, nunca esperar. MEDIDO hoje: 9,98 → 12,55.
- **AÇÃO**: `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/`
  e `./tools/go-modern test -count=1 ./internal/cerebro/ ./internal/v2bodyneardup/ ./internal/quality/`
- **DEPOIS**: 4 linhas `ok`. MEDIDO hoje: `generate-acordao-pages` **27,131 s**,
  `cerebro` 1,338 s, `v2bodyneardup` 2,238 s, `quality` 2,781 s. **33 `func Test`**
  em `main_test.go` (MEDIDO por `grep -c`).
- **SE NÃO VIER**: vermelho aqui é **pré-existente**. Date o teste contra
  `git log -1 --format=%h <arquivo>` antes de atribuí-lo a este bloco (precedente
  "vermelho conhecido é atribuição"). Não edite até saber.
- **ROLLBACK**: n/a (leitura).

### 2. Censo com o poço inteiro, e com tempo de parede
- **ANTES**: `ls -la data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` →
  **MEDIDO: não existe**, logo `shinglesDoProprioShard` devolve vazio (main.go:697-700).
- **AÇÃO**: `time ./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 99999 2>&1 | tee /tmp/censo-antes.txt; echo "EXIT=${PIPESTATUS[0]}"`
  (`-seco` é read-only: `executar` retorna antes de `gravaPortfolio`/`gravaShard`,
  main.go:214-218 — VERIFICADO por leitura.)
- **DEPOIS**: soma esperada 4.763 = 2.488 montáveis + 1.405 `molde_acima_do_limiar`
  + 682 `ementa_sem_item_transcritivel` + 165 + 22 + 1 (DERIVADO; **A MEDIR**).
  **Anote o tempo de parede**: o runner dá **900 s por gerador**
  (`run-daily-content`), e o anti-molde é Jaccard par-a-par O(n²) contra 1.134
  páginas mais as aceitas (`main_test.go:583-589` fixou lote=40 por custo medido).
- **SE NÃO VIER**: se a soma divergir, **vale o seu número** — o do diagnóstico é
  de outra data e o corpus tem cursor. Preserve `/tmp/censo-antes.txt` em
  `.agents/runtime/regua-molde/<data>/` no primeiro commit: produto não mora em `/tmp`.
- **ROLLBACK**: n/a.

> **Compare CONTADOR, nunca identidade de página.** `parecida()` compara contra
> `aceitas`, que **cresce** a cada aceita (main.go:296-299): o filtro é guloso e
> dependente de ordem. "Estas 1.405 páginas serão destravadas" é afirmação que a
> medição não sustenta; "o contador `molde_acima_do_limiar` cai de X para Y" é.

---

## 4. P4 — CORREÇÃO 1: a régua

### 3. Registrar a família no mapa do gate (pré-requisito)
- **ANTES**: `grep -n "stj-acordao" tools/check-derived-authorial-floor` → **MEDIDO: zero.**
- **AÇÃO**: acrescentar `"stj-acordao-derivado": "stj-acordao-derivado-*.jsonl"` a
  `FAMILIAS_CANAIS_DERIVADOS` (`:279-287`); criar I3.
- **DEPOIS**: `./tools/check-derived-authorial-floor` continua exit 0.
  **VERIFICADO por leitura** (`:457-462`): família cujo glob não casa arquivo dá
  `shards = []` → `corpus[familia] = []` → `pares_quase_identicos` itera `range(0)`.
  Entra com 0 páginas, **não** quebra. `./tools/check-familia-no-mapa-do-gate` sai 0.
- **SE NÃO VIER**: vermelho **agora** não é desta linha (não há páginas) — leia o
  log da etapa antes de herdar a causa. Não há teste do gate para rodar (MEDIDO:
  `tools/test_check_derived_authorial_floor*` não existe).
- **ROLLBACK**: para frente — remover a chave e a linha do I3.
- **NOTA**: I3 só **vê** a família de acórdãos depois que o P6 gravar o shard.
  Até lá ele prova a ausência de órfã nas famílias que existem.

### 4. `corpoParaMolde` — tirar a mobília, manter o dígito
- **ANTES**: `./tools/go-modern run ./cmd/measure-regua-molde -familia stj-tema-derivado -ledger ""`
  (I1, criado aqui). Esperado, **MEDIDO por mim**: régua do gerador p50 0,3905 máx
  0,7226 com **3** pares ≥ 0,70; régua do gate p50 0,2784 máx 0,5697 com **0**;
  headings sozinhos p50 **1,0000**.
- **AÇÃO**: em `cmd/generate-acordao-pages/main.go`, função nova espelhando
  `v2bodyneardup.AssembleBody` (opening, `sections[].text`, todas as perguntas,
  todas as respostas — **sem heading**). Trocar `corpoDaPagina` por `corpoParaMolde`
  nos **quatro** produtores de assinatura, num commit só: `:294` (`roda`),
  `:715` (`shinglesDoProprioShard`), `:799` (`shinglesPublicados`), `:2318` (`relata`).
  **Não** tocar `corpoDaPagina`, `shinglesNeutralizados`, `jaccard`, `parecida`.
  Escrever I2.
- **DEPOIS**: I1 de novo com `-familia stj-tema-derivado` → p50 ≈ **0,3440**, máx
  ≈ **0,6877**, **0** pares ≥ 0,70 (variante B, **MEDIDO em tema × tema**).
  **Sobre os candidatos de acórdão o número é A MEDIR no passo 8** — a população do
  gerador é outra (acórdão × 1.134 de `/jurisprudencia/`, cross-família).
  `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/` verde, **incluindo**
  `main_test.go:274-277`.
- **SE NÃO VIER**: (a) teste de dígito vermelho ⇒ você mexeu em
  `shinglesNeutralizados`; desfaça, não é da correção. (b) se sobrarem pares
  ≥ 0,70, **não baixe o limiar** — vá ao passo 8, que tem a regra de decisão.
  (c) mudar só parte dos quatro call sites é "guarda pela metade": I2 fica vermelho.
- **ROLLBACK**: para frente — `corpoParaMolde` volta a delegar a `corpoDaPagina`
  numa linha, com I2 documentando o vermelho.

### 5. Provar a equivalência de corpo, não "ser melhor"
- **AÇÃO**: I2 reimplementa o corpo do gate **à mão dentro do teste** — nunca
  chamando a função do gerador. É o desenho de
  `cmd/generate-stj-tema-pages/unicidade_test.go:36-39`, com o motivo escrito lá:
  *"se a normalização do gerador divergir da do gate, é ESTE teste que tem de ficar
  vermelho, e um teste que chamasse a função do gerador não notaria a divergência"*.
  Asserção: **igualdade de string** entre `corpoParaMolde(p)` e `corpoCanonicoDoGate(p)`.
- **DEPOIS**: verde. **Prova por mutação, as duas obrigatórias**: reinserir o
  heading ⇒ vermelho; intercalar o FAQ ⇒ vermelho. Sem as duas o teste não prova nada.
- **SE NÃO VIER**: divergência residual provável no separador (`"\n"` no gate,
  `AssembleBody:165-176`) ou no `TrimSpace`. Alinhe **no `corpoParaMolde`**, nunca no gate.
- **ROLLBACK**: para frente.

---

## 5. P4 — CORREÇÃO 2: o piso de entrada da ementa

### 6. Tirar o piso de 250 e deixar a saída decidir
- **ANTES**: no censo do passo 2, ler `ementa_curta_demais_para_duas_camadas`
  (main.go:533), e confirmar que os cortes de saída nunca dispararam:
  `grep -cE "corpo_abaixo_da_banda_do_verbete|comentario_proprio_abaixo_do_piso" /tmp/censo-antes.txt`
  — esperado **0** (DERIVADO; **A MEDIR**).
- **AÇÃO**: em `elegivel()` (main.go:532-534), remover o corte por
  `pisoEmentaPalavras`. O piso vira **medição**, não barreira: `:1679`, `:1681`,
  `:1652` e `:1656` já decidem com o corpo montado. **No mesmo commit**, corrigir
  os comentários de `:20` e `:400-402` que afirmam "1.674 candidatos" — passam a
  mentir (R1: comentário que mente é bug).
- **DEPOIS**: recensear (passo 8) **com `time`**. Esperado:
  `ementa_curta_demais_para_duas_camadas` → **0**; parte reaparece em `Paginas`,
  parte nos cortes de saída, que **passam a disparar** — isso é o desenho.
- **SE NÃO VIER**: (a) `texto_oficial_nao_cabe_na_banda` explodindo ⇒ o gargalo é
  `citacaoPorItens` contra `tetoPalavras=700`, e o conserto é o teto, não repor o
  piso. (b) `comentario_proprio_abaixo_do_piso` em massa ⇒ o piso de entrada estava
  certo **para aquela fatia**; mantenha a remoção e registre o número — recusar na
  saída, com o corpo real, é medição melhor que a proxy da ementa. (c) **se o tempo
  de parede passar de 900 s, é bug P0 de escala**: indexe o anti-molde (bucket por
  shingle ou MinHash), **nunca** aumente o timeout.
- **ROLLBACK**: para frente — repor o `if`, com o número medido no comentário.

---

## 6. P4 — CORREÇÃO 3: itens transcritíveis, como FALLBACK

### 7. Derivar o regex largo do dado, não do palpite
- **ANTES**: **MEDIDO por mim**, stride de **6 de 52** arquivos de
  `data/corpus/jurisprudencia/stj-espelhos/`: 7.695 registros lidos, **2.658**
  ACÓRDÃO com ementa ≥ 250 palavras, dos quais **141 (5,3%)** sem item pelo estrito
  `(?m)^[ \t]*\d{1,2}\s*\.\s` (main.go:1106). Formas nesses 141:
  **`\d{1,2}\.` inline, fora de início de linha — 77 (54,6%)**;
  **romano + ponto — 59 (41,8%)**; **`\d{1,2}` + hífen — 23 (16,3%)**;
  **nenhuma das três — 5 (3,5%)**. As categorias se sobrepõem.
- **AÇÃO**: escrever a fixture I6 **ANTES** do fallback — colher por stride ~200
  ementas que HOJE produzem itens e congelar a saída de `itensTranscritiveis` em
  `testdata/`. Só então o fallback em `itensDaEmenta`, acionado **apenas** quando
  o estrito devolve zero posições (`if len(posicoes) == 0`, main.go:1113).
- **DEPOIS**: I6 verde (o estrito não mudou para ninguém) **e**
  `ementa_sem_item_transcritivel` cai no recenseio.
- **SE NÃO VIER**: o risco nomeado é o inline — `\d{1,2}\.\s+[A-ZÀ-Ý]` casa
  "art. 5. A" e frase terminada em número. I6 vermelho ⇒ **o fallback vazou para o
  caminho estrito**: o `if` está no lugar errado. O diagnóstico registra que a
  regra larga isolada quebraria 29 de 4.079 — I6 é a prova de que ela não é isolada.
- **ROLLBACK**: para frente — devolver `itensDaEmenta` ao estrito puro; I6 continua
  verde e passa a ser a prova de que nada se perdeu.

### 8. Recensear, comparar contador a contador, e decidir sobre o resíduo
- **AÇÃO**: `time ./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 99999 2>&1 | tee /tmp/censo-depois.txt; echo "EXIT=${PIPESTATUS[0]}"`
  e `diff <(grep -oE '[a-z_]+ +[0-9]+' /tmp/censo-antes.txt) <(grep -oE '[a-z_]+ +[0-9]+' /tmp/censo-depois.txt)`
- **DEPOIS**: `molde_acima_do_limiar` cai; `ementa_curta_demais_para_duas_camadas`
  → 0; `ementa_sem_item_transcritivel` cai; `len(Paginas)` sobe. **Números exatos
  A MEDIR NA EXECUÇÃO.**
- **SE NÃO VIER — regra de decisão PRÉ-REGISTRADA** (antes de ver o número, para
  não escolher a leitura depois dele). Se `molde_acima_do_limiar` continuar alto,
  rode `./tools/go-modern run ./cmd/measure-regua-molde -area jurisprudencia -top 20 -ledger ""` e leia os pares:
  - pares **cross-família** (acórdão × tema/informativo) ⇒ o defeito é o **ESCOPO**
    (§0.1), não a régua: `shinglesPublicados` (main.go:790-800) passa a separar por
    família, como o gate faz. É correção de escopo, e não afrouxa nada.
  - pares **acórdão × acórdão** que diferem **só em dígito** ⇒ a questão é o eixo do
    dígito. Se ele for removido, é com `main_test.go:274-277` **atualizado** para a
    nova semântica, **nunca apagado** — e o número que justifica a troca vai no commit.
  - soma dos contadores + páginas tem de bater com o total de candidatos; se não
    bater, algum `continue` novo não incrementa contador, e recusa sem contador é o
    ponto cego que este censo existe para não ter.
- **ROLLBACK**: n/a (leitura).

### 9. Fechar P4: build, bancada, gates, commit
- **ANTES**: `git status go.mod go.sum` **limpos** (MEDIDO hoje: limpos, atestação
  verde `sha256:beb3ac7e`). Índice vazio.
- **AÇÃO**: `./tools/go-modern build ./internal/... ./cmd/...` ·
  `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/` ·
  `./tools/check-derived-authorial-floor` · `./tools/check-v2-body-near-duplicates` ·
  `./tools/check-familia-no-mapa-do-gate` · depois, **separados**:
  `git add <caminho exato>` e
  `flock -w 600 /tmp/opt-wiki-agent-heavy.lock git commit -F <mensagem>`
- **DEPOIS**: 33+ testes verdes; os três gates exit 0.
- **SE NÃO VIER**: pre-commit reprovando por orçamento da closure = **índice sujo**,
  não carga (o contrato mediu 77,6 s com índice sujo × 14,9 s limpo, e duas sessões
  erraram esse diagnóstico). Esvazie o índice. Nunca `--no-verify`.
- **ROLLBACK**: para frente, commit novo.

---

## 7. FRONTEIRA COM P6 — o que se mede na PRODUÇÃO ao vivo

P4 não publica: muda o gerador. O primeiro byte no ar vem do P6.

### 10. Provar que a produção serve o que foi publicado
- **ANTES**: `curl -s -o /dev/null -w '%{http_code} %{time_total}\n' -D - -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' -H 'X-Warming-Request: true' https://wikijuridica.com.br/healthz`
  — esperado **200 + `cf-cache-status: DYNAMIC`** (MEDIDO na varredura de hoje:
  200, 0,202 s, DYNAMIC). HIT/MISS ⇒ a Cache Rule derivou e toda sonda de saúde mente.
- **AÇÃO** (depois de o P6 publicar **e reiniciar o Go**):
  `curl -s https://wikijuridica.com.br/api/v1/citar<rota>` e comparar `html_sha256`
  com `sha256sum public/<rota>/index.html`.
- **DEPOIS**: hashes idênticos.
- **SE NÃO VIER**: **404 em `/api/v1/citar` não é "não publicou"** —
  `buildAPIPublishedPages` roda dentro de `httpserver.New()` (httpserver.go:1071):
  as cinco superfícies de máquina são **retrato do BOOT**. O conserto é reiniciar
  pela cadeia, **não** republicar nem purgar.
- **ROLLBACK**: n/a (leitura).

### 11. Ver o bot de IA sem esperar janela nenhuma
- **AÇÃO**: `LC_ALL=C grep -icE 'GPTBot|PerplexityBot|ClaudeBot|OAI-SearchBot|Googlebot' /var/log/nginx/wikijuridica/access.log`
  (`LC_ALL=C` obrigatório: `date +%b` devolve "set" em pt_BR e o nginx escreve "Sep";
  a comparação falha **em silêncio** devolvendo zero.)
- **DEPOIS**: linhas com `warm=false`. **Lag ZERO** — a linha existe no instante da
  requisição. O ledger derivado tem 1 h de atraso e não é o caminho.
- **SE NÃO VIER**: ausência na origem **não é ausência** — com `s-maxage=604800` a
  maior parte do rastreio nunca toca a origem (MEDIDO: gptbot 686 rotas na borda
  contra **0** na origem, no mesmo lote). A população está em
  `data/ops/crawl_coverage_state.json` → `crawlers_verified.<bot>.paths_first_seen`,
  e `tools/measure-crawl-coverage` roda **sob demanda** (GraphQL): não se espera o
  timer de 1×/dia.
- **ESPERA FÍSICA, com número**: a única aqui é a **retenção de 8 dias** do
  `httpRequestsAdaptiveGroups` da Cloudflare — externa, do operador. E a agenda do
  crawler é externa e **medida**: gptbot faz **97%** dos primeiros contatos entre
  01h–02h UTC; perplexitybot **67%** em 14h–15h; a onda publica ~07h UTC.
  **Atalho: mudar a hora da publicação, não esperar.**
- **ROLLBACK**: n/a.

---

## 8. P5 — A RÉGUA ANTES DO NÚMERO

### 12. Congelar o gabarito de 100 — mecânico, sem passo humano
- **ANTES**: `grep -c "" data/ai/extracoes_dispositivos.jsonl` → **MEDIDO: 44.153
  linhas.** Corpus conferível: **MEDIDO: 29 arquivos** em `data/legal-corpus/`.
- **AÇÃO**: I5. Amostra por **stride determinístico** sobre os itens com `urn` não
  vazio — nunca prefixo, nunca amostra "de suspeitos" (precedente: amostra
  enriquecida mede o enriquecimento). Conferência **mecânica**, reusando o que já
  está em produção em `tools/check-anchor-claim-sustenta-dispositivo`:
  `carregar_corpus()` (`:96-106`) devolve `diplomas` por `slug` e `por_url` por
  `normalizar_url`; `texto_do_artigo(dados, artigo)` (`:109-115`) normaliza
  `[ºo°\s.]` e busca em `dados["articles"]`; `termos()` (`:85-94`) compara por
  **radical truncado em 6**, não palavra inteira.
  **MEDIDO: `data/legal-corpus/*.json` NÃO tem campo `urn`** — as chaves são
  `slug`, `nome`, `source_url`, `citation_url`, `conference_url`, `declared_url`.
  Logo a ponte é `norma` → `slug`/`nome` (ou a URL da fonte, quando houver),
  **nunca** URN → diploma direto. E honre
  `confiavel_para_acusar_divergencia`: diploma marcado como não confiável entra em
  `fora_do_corpus`, não em acusação.
  Congelar em `.agents/runtime/gabarito/gabarito-atribuicao-<data>.jsonl` com
  `sha256`, data, método e o **stride** escritos dentro.
- **DEPOIS**: 100 linhas; `sha256sum` registrado. **Controle positivo obrigatório**:
  injete 3 itens sabidamente errados e confirme que o gabarito os marca — sem isso
  o zero não distingue "medi e deu zero" de "não medi".
- **SE NÃO VIER**: se a cobertura do corpus sobre a amostra for baixa, **não** troque
  a amostra por uma que ele cobre — seria escolher a população depois do número.
  Declare `fora_do_corpus` como classe à parte, como o gate irmão faz com
  `fora_do_registry`.
- **ROLLBACK**: gabarito é append; versão nova com data nova, a antiga fica.

### 13. Medir a atribuição de HOJE contra o gabarito
- **ANTES**: `./tools/check-extracoes-dispositivos` (read-only por declaração de cabeçalho).
- **AÇÃO**: I4 com `-ledger ""`.
- **DEPOIS**: esperado (DERIVADO; **A MEDIR**) **15,51%** sem o número do artigo
  dentro do próprio `texto_citado`; **19,0%** só pela folga de
  `NormaAtestadaNoTexto` (triagem.go:195-230, que testa a norma no texto **inteiro**);
  **13,1%** sem artigo nem norma no trecho.
- **SE NÃO VIER**: divergência grande = populações diferentes (item × acórdão ×
  linha). Declare o denominador em toda linha, no formato **"N de M"**.
- **ROLLBACK**: n/a.

---

## 9. P5 — A CORREÇÃO

### 14. Atestar a norma DENTRO do trecho citado — classificando, nunca filtrando
- **AÇÃO**: em `internal/cerebro/extracao.go`, campo novo em `DispositivoExtraido`
  (`:50-56`): `Atestacao string json:"atestacao,omitempty"`, com três valores —
  `trecho` (a norma ocorre dentro do `texto_citado`), `texto_inteiro` (só no texto
  completo: a folga de hoje), `nenhuma`. Em `:547`, chamar
  `NormaAtestadaNoTexto(d.Norma, d.TextoCitado)` **primeiro**; se falhar, manter a
  chamada atual contra `texto` e carimbar `texto_inteiro`. **O `continue` de `:549`
  não muda: o item continua entrando.**
  A conferência do **artigo** dentro do `texto_citado` reusa `semMilhar` e
  `reNumeroDeNorma` de `triagem.go:222-227` — **não** um regex novo, para os dois
  produtores não divergirem no mesmo texto.
- **DEPOIS**: `./tools/go-modern test -count=1 ./internal/cerebro/` verde (base
  MEDIDA: 1,338 s). I4 devolve a **mesma contagem total de itens** de antes — só a
  distribuição de `atestacao` muda.
- **SE NÃO VIER**: **se a contagem total de itens CAIR, você filtrou.** É o erro que
  torna a regra de parada inmensurável, porque muda a população. Desfaça o `continue`
  novo e mantenha só o campo.
- **ROLLBACK**: para frente — o campo é `omitempty`; parar de escrevê-lo devolve o
  arquivo à forma anterior sem tocar linha gravada.

### 15. Revisão v9 — a reabertura é AUTOMÁTICA
- **ANTES**: `grep -c '"revisao":"norma_nomeada_no_artigo_v8"' data/ai/extracoes_dispositivos.jsonl`
  → **MEDIDO: 45**. Distribuição MEDIDA: `uniao_do_parser_v2` 33.763,
  `parser_regenerado_v4` 1.272, `uniao_do_parser_v1` 546, `v8` 45, `v6` 41, `v5` 19,
  `v1` 19, `v3` 12, `v7` 1. Constantes vivas v1…v8 em
  `extracao.go:128,147,159,169,181,188,199,205`.
- **AÇÃO**: **CORREÇÃO AO ENUNCIADO** — `cmd/generate-revisao-extracoes/main.go:131`
  pula apenas `e.Revisao == cerebro.RevisaoNormaNomeadaNoArtigo` (a corrente) e
  `ExecutorTriagem`. O comentário de `:121-123` diz literalmente: *"CADA REVISAO
  NOVA REABRE O QUE AS ANTERIORES FECHARAM: so nao volta o que ja passou por ESTA."*
  Logo **não** se "inclui a v8 entre as que a v9 reprocessa" — isso é redundante.
  Basta criar `RevisaoNormaNoTrechoCitado = "norma_no_trecho_citado_v9"` e trocar
  as referências de `RevisaoNormaNomeadaNoArtigo` para ela em `main.go` (`:131`,
  `:154`, `:375`, `:629`); a v8 fica como **constante histórica**, que é o padrão
  declarado em `extracao.go:151`. A reabertura das outras ~44.100 linhas é automática.
  Rodar **em ensaio primeiro**: `./tools/go-modern run ./cmd/generate-revisao-extracoes`
  **sem** `--aplicar` (`:52` — sem a flag é ensaio: mede e imprime).
- **DEPOIS**: o ensaio imprime quantas linhas mudariam, e `ExtracoesLidas`,
  `SemTextoNoCorpus`, `HashDivergente`, `PelaFila`, `Recarimbadas`. Só então
  `--aplicar`, que preserva o original em `.agents/runtime/revisao-extracoes/`
  (`--preservar-em`, `:51`).
- **SE NÃO VIER**: ensaio dizendo "0 linhas" ⇒ alguma referência à constante velha
  ficou em `:131`. Confira **lendo**, não re-rodando. E `HashDivergente` alto é
  esperado e **não** é defeito desta passada: `:106-114` registra 602 de 35.012
  linhas nessa condição, revisadas pela fila.
- **ROLLBACK**: o arquivo é **append-only** e o original fica em `--preservar-em`
  com data. Reverter é acrescentar uma v10 que desfaz, **nunca apagar**.

### 16. REGRA DE PARADA — pré-registrada
- **AÇÃO**: I4 de novo, contra o **mesmo** gabarito congelado do passo 12.
- **DEPOIS**: `trecho` sobe; `texto_inteiro` + `nenhuma` descem. Veredito escrito
  **antes** de ver o número (precedente "régua do veredito antes do número"):
  melhora ⇒ segue; empate dentro do erro da amostra de 100 ⇒ segue **sem creditar
  ganho**; **piora ⇒ reverte-se a mudança do P5 — NÃO a publicação.**
- **SE NÃO VIER (piorou)**: desfazer o passo 14 **para frente** (parar de carimbar,
  manter a chamada antiga), mantendo gravados os passos 12 e 13, e abrir o achado
  com o número. Páginas no ar **não saem**: P5 é qualidade e rebaixa para refino
  (§5 do contrato), e tirar 3.101 páginas vivas faria `publishedmanifest.Validate`
  acusar `sitemap_loc_without_manifest` — fora da allowlist tolerada, o que
  **impede o boot do Go** e derruba o canal de máquina inteiro.
- **ROLLBACK**: acima.

### 17. Rota de refino — o que o carimbo aciona
- **ANTES**: `grep -c "" data/editorial/v2_rewrite_queue.jsonl`
- **AÇÃO**: `tools/generate-v2-publication-severity` passa a ler `atestacao` e a
  classificar `texto_inteiro`/`nenhuma` como **MÉDIO** (publica e refina depois),
  nunca crítico.
- **DEPOIS**: a fila cresce; a contagem de **críticos** não muda.
- **SE NÃO VIER**: item virando crítico ⇒ a página não publica, e 3.101 das 3.201
  entradas da fila são páginas **VIVAS**. Volte a médio na mesma sessão.
- **ROLLBACK**: para frente.

---

## 10. NÃO MEDIDO, E POR QUÊ

| não medido | por quê |
|---|---|
| censo `-seco -limite 99999` e seu tempo de parede | load1 chegou a **12,55** e `check-load-headroom --max 12` saiu 1 mandando avançar outra frente, não esperar. É o passo 2. |
| tempo de `check-derived-authorial-floor` / `check-v2-body-near-duplicates` | não executados; `run-qualidade-diaria:679` dá **600 s** de orçamento ao segundo |
| 675/682 e 29/4.079 da correção 3 | **fonte primária não localizada** em `.agents/runtime/` nem `docs/goal/`. Por isso o passo 7 **deriva o regex do corpus** e **congela a fixture antes**, em vez de herdar o número |
| 15,51% / 19,0% / 13,1% do P5 | herdados do diagnóstico; o passo 13 os remede com denominador declarado |
| `measure-molde-trigrama` executado | `-ledger ""` o torna read-only, mas ele não é oráculo do gate e lê o FAQ pela chave errada (§0.6) |
