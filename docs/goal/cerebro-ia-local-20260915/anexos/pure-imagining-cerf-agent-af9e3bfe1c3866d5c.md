# Unicidade por camada — medir só o que tem de ser único

Ângulo: a métrica está certa, a POPULAÇÃO está errada. Desenho de partição por
camada para `cmd/generate-acordao-pages` e para o gate `internal/v2bodyneardup`.

Sessão SOMENTE-LEITURA. Tudo abaixo é desenho + medição própria; nada foi editado.

---

## 0. As duas medições que este desenho produziu (e que corrigem o enunciado)

### M1 — camadas sobre as páginas VIVAS de /jurisprudencia/

População: 1.134 páginas ativas com `practice_area == "jurisprudencia"` em
`data/editorial/v2_pages/*.jsonl` (stj-tema-derivado-01 + stf-informativo-derivado-01)
— exatamente a população que `shinglesDoProprioShard`/`previas`
(`cmd/generate-acordao-pages/main.go:715,:799`) compara. Amostra por stride
determinístico 5, n=200, 19.900 pares. 3-gramas, Jaccard.

Tamanho por camada (palavras):

| camada | min | p25 | mediana | p75 | max |
|---|---|---|---|---|---|
| corpo `AssembleBody` | 277 | 345,0 | 376,5 | 421,8 | 1.389 |
| CITADA (aspa curva ≥25 palavras + contexto de ato oficial) | 0 | 49,0 | 74,0 | 103,8 | 619 |
| AUTORAL (corpo − citada) | 238 | 277,2 | 292,5 | 324,0 | 791 |
| headings de seção | 34 | 43,0 | 43,0 | 48,0 | 79 |

13 de 200 páginas não têm camada citada reconhecida.

Distribuição de Jaccard por régua, mesmos 19.900 pares:

| régua | mediana | p90 | p99 | max | ≥0,70 | ≥0,60 | páginas tocadas ≥0,70 |
|---|---|---|---|---|---|---|---|
| **A** gerador HOJE (`corpoDaPagina` + headings, dígito NEUTRALIZADO, 3g) | 0,3782 | 0,5254 | 0,6198 | 0,7258 | 4 | 375 | 7 |
| **B** corpo inteiro (`AssembleBody`, dígito preservado, 3g) | 0,2669 | 0,3862 | 0,4678 | 0,5645 | 0 | 0 | 0 |
| **C** AUTORAL só (dígito preservado, 3g) | 0,3744 | 0,5170 | 0,6272 | **0,7583** | 18 | 376 | 19 |
| **D** AUTORAL só (dígito NEUTRALIZADO, 3g) | 0,4684 | 0,6548 | 0,7864 | 0,9262 | **1.068** | 3.651 | **160** |
| **E** CITADA só (dígito preservado, 3g) | 0,0000 | 0,0032 | 0,0153 | 0,4561 | 0 | 0 | 0 |
| **F** corpo inteiro 5g = `v2bodyneardup` | 0,1867 | 0,2818 | 0,3516 | 0,4380 | 0 | 0 | 0 |

### M2 — a camada citada no corpus REAL de acórdãos

`data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl`
(`internal/stjacordaos/registro.go:21`). 60.221 registros lidos; 49.807
agravo/embargo; 4.645 ementa < 250 palavras; 2.818 com âncora bruta. Amostra por
stride, n=200, 19.900 pares. Réplica do corte de
`itensTranscritiveis` (`main.go:1152-1163`): corrida contígua de itens numerados
(`reItemDeEmenta`, `:1106`) que termina no primeiro item em versal
(`integralmenteEmCaixaAlta`, `:1134`).

| texto | mediana | p90 | p99 | max | ≥0,70 | ≥0,60 |
|---|---|---|---|---|---|---|
| ementa inteira (com preâmbulo forense) | 0,0065 | 0,0360 | 0,0852 | 0,2062 | 0 | 0 |
| **preâmbulo VERSAL sozinho** ("EMENTA. RECURSO ESPECIAL. PROCESSUAL CIVIL…") | 0,0016 | 0,0597 | 0,1600 | 0,4194 | 0 | 0 |
| itens transcritíveis = camada CITADA que a página usa | 0,0050 | 0,0308 | 0,0825 | 0,2052 | 0 | 0 |

Tamanhos: ementa mediana 434,5 palavras; preâmbulo versal mediana 42 (9,7%);
itens transcritíveis mediana 367. 12 de 200 sem item transcritível.

**Ressalva de replicação, declarada:** meus filtros de elegibilidade são
aproximados (contagem por `str.split()` contra `ptbrtext.BodyWords`, e teste de
âncora sem `dispositivosSubstantivos`), então 2.818 ≠ 4.763 do Go. Os números de
SIMILARIDADE são robustos a isso (a amostra é de acórdãos de mérito nos dois
casos); as CONTAGENS de elegibilidade não são medição minha e não as reivindico.

### O que as duas medições estabelecem

1. **A camada citada não é o molde — é o que mais distingue.** Em acórdão real,
   nenhum par de 19.900 chega a 0,60 nem mesmo no preâmbulo forense isolado
   (max 0,4194; mediana 0,0016). O vocabulário forense é compartilhado; as
   SEQUÊNCIAS de 3 palavras não são. A premissa "o score é dominado pela camada 1"
   é falsa como afirmação quantitativa.
2. **Tirar a citação torna o gate MAIS severo, não menos** (B→C: mediana
   0,2669→0,3744; 0→18 pares ≥0,70; 0→19 páginas). Reproduz o achado já registrado
   em `tools/check-derived-authorial-floor:341-399` (3 pares no corpo inteiro
   contra 4.223 no autoral). O que carrega a distinção é o texto citado; o que
   sobra é esqueleto.
3. **O que mata as 532 é a neutralização de dígito, não a mistura de camadas**
   (C→D: 18 → 1.068 pares, 19 → 160 de 200 páginas, 59× em pares e 8,4× em
   páginas). É o maior fator isolado de severidade medido nesta frente.

**Logo: este ângulo não destrava a fábrica sozinho. Ele faz o eixo que destrava
significar alguma coisa.** Com as camadas misturadas, um score alto é ilegível.
Separadas, um score alto no eixo autoral diz sempre a mesma coisa — "a NOSSA
prosa se repete" — que é defeito consertável no produtor e nunca na fonte.

---

## 1. A partição: três camadas, e o que a define

| camada | o que é | como se reconhece | régua |
|---|---|---|---|
| 1 CITADA | texto oficial transcrito (DEC-032) | aspa curva de abertura/fechamento, ≥25 palavras, contexto de ato oficial nos 140 caracteres anteriores | **fidelidade**, nunca unicidade |
| 2 AUTORAL | tudo o mais do corpo: opening, `sections[].text` fora das aspas, FAQ inteiro | resto por subtração | **unicidade**, 3-gramas, dígito PRESERVADO |
| 3 MOLDURA | `sections[].heading` | projeção de campo | fora de todo score; eixo próprio de reuso |

**FAQ é camada 2, não camada 3** — e isso é decisão já paga pelo repositório.
`tools/check-derived-authorial-floor:107-113` registra que `shinglesDoCorpo`
EXCLUIR o FAQ foi o bug de divergência ("as duas réguas divergiam por construção,
e por isso o gerador ficava verde com o gate vermelho").
`v2bodyneardup.AssembleBody` (`neardup.go:157-176`) inclui FAQ. Reclassificar FAQ
como moldura para baixar o score seria afrouxar por definição, que o §5 do
contrato chama de fraude operacional. FAQ molde é defeito do FAQ.

**Camada 3 é só heading** — 43 de 376,5 palavras (11,4% do corpo, M1), e
`neardup.go:153-156` já os exclui por escrito ("deliberadamente EXCLUÍDOS para
não inflar a similaridade via títulos templatizados"). O gerador os INCLUI
(`main.go:2153-2168`). Isso é divergência pura, e some com uma linha.

---

## 2. Regra pinada da camada 1, e por que UMA só

Hoje existem **quatro** extratores de aspa curva em Go, com **três** regras, e um
em Python com a regra medida:

| sítio | regra | falha |
|---|---|---|
| `cmd/generate-acordao-pages/main.go:2171` `reAspas` = `“[^”]*”` | sem mínimo, sem contexto | termo de 5 palavras entre aspas vira "citação" |
| `cmd/generate-lei-artigo-pages/main.go:1881` `reAspas` | idem | idem |
| `cmd/generate-diario-pages/citacao.go:691` `semTrechoCitado` | varredura por runa, sem mínimo, sem contexto | idem |
| `cmd/generate-stj-tema-pages/excertos_comentados.go:164` `citacaoNoCorpo` = `“([^”]{10,})”` | mínimo de 10 CARACTERES | ainda pega título de matéria |
| `tools/check-derived-authorial-floor:257,262-264` | `“([^”]{10,})”` + ≥25 PALAVRAS + `ATO_OFICIAL` em 140 chars | **a regra medida** |

A regra do gate Python é a única com falso positivo medido e fechado
(`check-derived-authorial-floor`, armadilhas #1 e #2): aspa RETA produz falso
positivo em massa (755 ocorrências, casando 459 palavras de texto autoral como
citação) e aspa curva sem contexto pega título de matéria e status de cadastro.
**É essa que se pina.**

`internal/v2bodylayers` é, portanto, uma **consolidação de quatro sítios
existentes**, não uma invenção.

---

## 3. Transporte: como a camada sobrevive até `v2bodyneardup`

`v2bodyneardup` recebe `Page{Shard, IntentID, Body}` (`neardup.go:129-134`) — o
corpo já montado, sem marcação. Três rotas:

### (a) campo novo no JSONL (`quoted_spans`) — REJEITADA
Custo: toca `internal/v2publish.Page` (`v2publish.go:30-43`),
`internal/v2ingest`, o censo e os 877 shards; e os 11.106 registros publicados
ficariam com o campo ausente, deixando o gate CEGO sobre o acervo vivo até
regeneração — que re-data o acervo (§6, matriz).
**O argumento que a mata está no próprio arquivo:** `v2publish.go:44-55` documenta
`publication_date`, um campo que EXISTIA no dado e que `json.Unmarshal`
DESCARTAVA em silêncio porque o struct não o declarava — resultado medido: 20
notícias empatadas no sitemap. Um `quoted_spans` faria exatamente isso com todo
consumidor não atualizado, **sem erro**.

### (b) marcador in-band (aspa curva) — **ESCOLHIDA**
Custo: zero de schema, zero de migração, retroativo sobre as 11.106 páginas já
publicadas, e idêntico nos quatro canais (HTML, gêmea Markdown, MCP/A2A,
`/api/v1`) porque a aspa viaja no texto.
**E o gerador já escreve o marcador PARA ESTE reconhecedor**, por escrito em
`main.go:1825-1836`:

> "A frase que antecede a aspa nomeia o ato oficial ("acórdão", "ementa") de
> propósito: é a janela de 140 caracteres que tools/check-derived-authorial-floor
> examina para reconhecer citação de ato oficial (ATO_OFICIAL, :288)."

Cobertura medida: 187 de 200 páginas vivas (93,5%, M1) e 188 de 200 acórdãos do
corpus (94,0%, M2) têm camada citada reconhecível.
**Direção da falha: severidade.** Página sem marcador (as 13/200; e as 368 de
`/leis/`, que têm zero aspa curva — armadilha #3 do gate) tem todo o texto contado
como AUTORAL, isto é, medida com a régua mais estrita. Nunca o contrário.

### (c) índice lateral em `data/ops/` — REJEITADA
Custo: mais um derivado numa cadeia que já tem ~9 artefatos com ordem topológica
obrigatória e que ficou **31 dias parada** por `fingerprint mismatch` (§1 do
contrato). E um índice envelhece contra o shard vivo sem dizer — o precedente
"gate de igualdade exata sobre diretório vivo". Um gate não pode depender de
artefato cuja frescura ninguém guarda.

---

## 4. Onde a partição vive, e o que muda em cada arquivo

### 4.1 `internal/v2bodylayers` (novo, ~120 linhas) — fonte única
```go
type Layers struct{ Citada, Autoral, Moldura string }
func Split(opening string, sections []Section, faq []FAQ) Layers
func SpansCitados(texto string) [][2]int   // regra pinada do §2
```
- Ordem de concatenação **byte-idêntica** a `v2bodyneardup.AssembleBody`
  (`neardup.go:157-176`): opening, `sections[].text`, FAQ perguntas, FAQ respostas.
- `AssembleBody` passa a ser um wrapper sobre `Split` (`Citada + Autoral` na
  ordem original) — assim as duas não PODEM divergir, que é o defeito original.
- `Moldura` = `sections[].heading`, já fora de `AssembleBody` hoje.

### 4.2 `internal/v2bodyneardup` — o gate passa a ver a partição
- `Page` ganha `Layer` derivado; `BuildCorpus` passa a aceitar
  `BuildCorpusLayered(pages, v2bodylayers.Autoral)`.
- `shingleHashes` (`neardup.go:181`) NÃO muda: mesma normalização,
  `ShingleSize=5`, dígito preservado. O que muda é o TEXTO que entra.
- O eixo histórico de corpo inteiro **continua reportado** — é a série da bancada
  diária (`tools/run-qualidade-diaria:679`) e não pode mudar de valor em silêncio.
- Comentário `neardup.go:16` alega paridade de métrica com `internal/quality` que
  **não existe** (`AssembleBody` exclui headings; `quality` usa `Page.PlainText()`,
  `internal/content/content.go:523`, que inclui `LegalNotice` e
  `PublicationPurpose`). R1: comentário que mente é bug — corrigir no mesmo commit.

### 4.3 `cmd/generate-acordao-pages/main.go` — o produtor para de divergir
| linha | hoje | passa a ser |
|---|---|---|
| `:2153` `corpoDaPagina` | opening + **heading** + text + FAQ | mantida só para `contaPalavras` (espelha `v2ingest.bodyWordCount`) |
| `:294,:715,:799` eixo de molde | `shinglesNeutralizados(corpoDaPagina(p))` | `v2bodylayers.Split(...).Autoral`, 3-gramas, **dígito preservado** |
| `:2171` `reAspas` | `“[^”]*”` | `v2bodylayers.SpansCitados` (regra pinada) |
| `:2176` `corpoAutoral` | `reAspas` sobre corpo com headings | `Split(...).Autoral` |
| `:2187-2196` `shinglesNeutralizados` | régua do veredito | **move para o eixo esqueleto** (§6) |
| `:99-101` comentário | "a mais severa das duas" | substituído pela medição M1/M2 |

### 4.4 Rastro — o furo que nenhuma camada conserta sozinha
`relata` (`main.go:2268-2313`) grava `map[string]int`: só nome do motivo e
contagem. As 532 recusas não têm `intent_id` nem número de processo em lugar
nenhum. **Toda recusa passa a emitir linha em
`data/editorial/v2_layer_uniqueness.jsonl`**: `intent_id`, score por camada, par
mais próximo (`intent_id` + score), e a assinatura da partição (§7). Sem isso,
calibrar é opinar.

---

## 5. Dígito: move, não morre

O repositório JÁ resolveu "número intercalado quebra o n-grama" com **tamanho de
janela**, não com apagamento — `check-derived-authorial-floor:273`:

> `TAMANHO_SHINGLE_UNICIDADE = 3   # 3-gramas sobrevivem ao numero intercalado; 5 nao`

Apagar dígito é uma SEGUNDA correção, redundante, para o mesmo problema — e
destrutiva: `reNaoPalavra` roda antes de `reDigito` (`main.go:2188-2189`), então
"REsp 1.794.991" vira `resp N N N` e colapsa com "REsp 2.150.333"; número de
artigo, de lei e data caem junto. `internal/legalsignature/signature.go:91`
(BUG-137, 2026-08-29) preserva dígito e ainda conserta separador de milhar
exatamente para não acusar variação numérica como molde; o gerador de acórdão
desfaz essa correção num corpus onde o dígito é o conteúdo.

- **Eixo de veredito:** 3-gramas, dígito **preservado**. Medido C: max 0,7583.
- **Eixo esqueleto (diagnóstico):** 3-gramas, dígito **neutralizado** — a leitura
  responde outra pergunta: *"esta prosa difere da irmã apenas por números?"*
  Medido D: 160 de 200 páginas vivas (80,0%). MÉDIO, nunca bloqueio; ordena a fila
  de enriquecimento. Produtor: `cmd/measure-molde-trigrama` (hoje órfão, 1 commit,
  nenhum invocador), que já computa exatamente esta leitura.

Dupla leitura tem precedente no repo: `internal/quality/quality.go:92` reavalia
com shingles stemizados acima de um gatilho.

---

## 6. Camada 1 não tem eixo de unicidade — tem eixo de FIDELIDADE

Marcador in-band é **spoofável**: prosa autoral entre aspas curvas com "acórdão"
por perto escaparia do eixo autoral. Fechamento mecânico, com o dado que já está
no disco:

> Span entre aspas que **não for substring literal do texto-fonte** não é citação:
> reclassifica-se como AUTORAL e emite-se `citacao_nao_confere_com_fonte`.

A fonte existe e é hasheada: `registros-*.jsonl` traz `ementa`, `dispositivo`,
`id_fonte` e `sha256_conteudo` (`internal/stjacordaos/registro.go:21`), e
`blocoEmenta` já carrega `r.IDFonte` na proveniência (`main.go:1831`). É a única
guarda mecânica que o repositório teria para a classe "citação legal mal
atribuída", hoje declarada P1 permanente sem detector.

Os outros dois eixos da camada 1 já existem e ficam: proporção citada
(`tetoCitado`) e mínimo de citação (`minimoCitacaoOficial`).

---

## 7. Constantes: nenhuma nova no produtor

Régua: **o produtor anota, o censo classifica.** Por quê:

- C max = 0,7583 é o máximo de uma amostra de 200 sobre 1.134. Máximo é a
  estatística mais sensível à amostragem, e R3 proíbe amostra como população.
- 19 de 200 páginas **já publicadas e limpas nos dois gates vivos** cruzam 0,70 no
  eixo autoral. Qualquer limiar bloqueante ≤0,7583 condena o acervo vivo.
- O caminho que decide publicação não recusa por similaridade
  (`cmd/publish-v2-direct/qualitygate.go:21`, 9 códigos, nenhum estatístico), e o
  censo já trata similaridade como MÉDIO em 5.600 + 2.089 páginas no ar.

Então:
1. **Produtor:** única recusa terminal por molde é **identidade** — camada autoral
   normalizada byte-igual a uma já aceita. `emitidos`/`rota_duplicada_no_corpus`
   (`main.go:281-286`) já faz metade disso por rota.
2. **Censo:** `tools/generate-v2-publication-severity` ganha
   `esqueleto_autoral_acima_do_p99` (MÉDIO) e
   `citacao_nao_confere_com_fonte` (CRÍTICO — é FATO, não juízo).
3. **Limiares:** derivados da passada de POPULAÇÃO INTEIRA (1.134 páginas, 642.411
   pares — barato em Go), não da amostra; gravados com data e contagem no JSONL
   do §4.4, no padrão `skipped_statistical_gates` de
   `cmd/publish-v2-direct/main.go:3957`, mas **por página de verdade**.

Se uma trava numérica tiver de ficar no produtor, ela é calibrada ao **máximo da
população inteira**, datada, e versionada pela assinatura do §8.

---

## 8. Reuso do padrão de neutralização — e onde ele NÃO serve

`tools/generate-page-content-revision` é o precedente pedido, e presta em duas
metades:

**SERVE — a assinatura da fórmula** (`:385-411`): `assinatura_da_formula()`
hasheia, com sha256, os `.pattern` dos blocos MAIS o `inspect.getsource` da função
de neutralização, e `confere_formula` PARA o gerador quando a fórmula mudou sem
cerimônia. O comentário registra por que a meia-assinatura falhou: a mudança de
2026-08-27 entrou sem disparar nada porque não tocou nenhum pattern.
→ Em Go, o equivalente é um **teste de fixture dourada** sobre a saída de
`v2bodylayers.Split` para um corpus de amostra: qualquer edição na partição muda a
fixture e obriga a cerimônia. Trocar a régua da unicidade não pode ser efeito
colateral de um commit sobre outra coisa.

**NÃO SERVE — a implementação por regex de HTML** (`:310-355`:
`<section aria-labelledby=…>`, `<nav class="perfis-oficiais">`, `<script>` sem
atributo). O JSONL v2 não tem HTML: os blocos estruturais já são CAMPOS
(`sections[].heading`, `faq[].q`), então neutralizar ali é **projeção de campo**,
não regex. A única coisa genuinamente in-band no JSONL é a citação, e ela não tem
campo — só a aspa curva. Daí a divisão honesta: **estrutura por projeção de campo,
citação por marcador in-band.**

---

## 9. Consequência que este ângulo expõe (não a resolvo aqui)

A camada que carrega a distinção é a camada que o orçamento mata de fome.
`main.go:1636-1660` monta a camada autoral e o FAQ PRIMEIRO e dá à citação o que
sobrar: `orcamento = 700 − base`. Medido no `-seco` (dossiê): autoral mediano 556,
citado mediano 116, sobrando ~144 palavras — contra uma corrida transcritível de
**mediana 367 palavras** medida por mim no corpus (M2). E `tetoCitado = 0,42`
(294 palavras) nunca vinculou em nenhuma das 500 páginas, porque o menor autoral
aceito foi 409.

Com M1 e M2 juntas: cortar a camada citada aumenta a similaridade (B→C) e a
camada citada é a mais distintiva que existe (E max 0,4561; M2 max 0,2052). Logo
**o orçamento invertido fabrica o molde que o gerador depois recusa.** É frente
de produtor, com número medido para cobrar — não a redesenho aqui.
