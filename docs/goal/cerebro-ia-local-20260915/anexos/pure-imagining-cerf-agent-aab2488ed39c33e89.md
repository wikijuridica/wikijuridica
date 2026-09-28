# Varredura: família de detectores de similaridade / molde / near-dup — /opt/wiki

Sessão read-only (PLAN MODE). Medido em 2026-09-15. Nada foi escrito no repo.

## Achado central, medido

**Nenhum detector estatístico desta família decide publicação hoje.** O único que
efetivamente mata conteúdo é o do PRODUTOR, e ele é o mais severo de todos.

Cadeia real de publicação:

| ponto | arquivo:linha | o que faz com similaridade |
|---|---|---|
| produtor acórdão | `cmd/generate-acordao-pages/main.go:294` | **RECUSA** (532/1260 na passada `-seco -limite 500`) |
| seleção a montante | `internal/v2publish/v2publish.go:391` | nenhum eixo de similaridade |
| gate do publish | `cmd/publish-v2-direct/qualitygate.go:21-31` | `near_duplicate_content` **não está** na lista crítica ⇒ MÉDIO, publica |
| partição por severidade | `tools/generate-v2-publication-severity:761-766` | anti-template e `batch_global_similarity` já são **MÉDIO** |
| deploy | `tools/deploy-publico` | **nenhum** gate de similaridade invocado |
| bancada diária | `tools/run-qualidade-diaria:679` | `v2-body-near-duplicates` roda **fora** do caminho de publicação |

Medição própria sobre `data/editorial/v2_publication_severity.jsonl`
(11.206 linhas, `json.loads` + Counter sobre todas as linhas — população, não amostra):

```
CRITICOS: intencao_pulada_deliberadamente 100   <- unico critico; nenhum de similaridade
MEDIOS  : batch_global_similarity_refutado_por_medicao 5600
          blocker_pipeline:anti_template               2089
          fonte_insuficiente                           2323
          corpo_entre_250_e_400_palavras               1695
```

7.689 marcações de similaridade/molde no estoque publicado, **todas médias, todas
no ar**. O produtor recusa com régua mais severa do que qualquer coisa a jusante.

### Dois executores verificados que poderiam desmentir isso — e não desmentem

**`cmd/build` reprova duro, mas está fora do deploy.** `internal/build/build.go:182`
faz `if !report.Passed() { return Result{}, errors.New(...) }` — falha em
**qualquer** issue, inclusive `near_duplicate_content` e `doorway_pattern`
(`quality.go:674-675`). Mas `tools/deploy-publico` **não invoca `cmd/build`**:
publica por `cmd/publish-v2-direct` (`:464`), que particiona. Os únicos
importadores de `internal/build` são `cmd/build/main.go` e `internal/checks`.
⚠️ **Armadilha latente**: `cmd/build public` é o comando **documentado no
CLAUDE.md §4**. Quem o rodar encontra 0,82 sobre `PlainText()` como bloqueio
duro — e `PlainText()` inclui `LegalNotice` e `PublicationPurpose`, que são
boilerplate idêntico do template em todas as páginas.

**`v2-acervo-similaridade` não tem executor de rotina.** Registrado em
`checks.go:407` e `:2004`, ausente de `deploy-publico`, de
`run-qualidade-diaria` e do pre-commit. O `.githooks/pre-commit` **não invoca
`cmd/check` em nenhum ponto** (só o menciona num comentário, `:604`). Mesma
situação para `content-quality` (0,82): alcançável por
`tools/check-content-quality` → `tools/run-check` e pelos perfis de
`checkselection.go:255,936`, mas fora da bancada diária, do deploy e do commit.

## A incoerência está DENTRO do próprio arquivo do acórdão

`cmd/generate-acordao-pages/main.go` já tem a régua por camada e não a usa no molde:

- `:2176 corpoAutoral(p)` — desconta os trechos entre aspas curvas (camada 1 oficial).
- `:1681` usa `corpoAutoral` para o **piso autoral** (250 palavras). Correto.
- `:294`, `:715`, `:799`, `:2318` usam `corpoDaPagina(pagina)` para o **molde** —
  corpo inteiro: opening + **headings** + texto + **FAQ** + ementa citada (camadas 1+2+3).

O irmão faz certo: `cmd/generate-diario-pages/main.go:1400` mede o molde sobre
`semTrechoCitado(corpoDaPagina(pagina))` — a camada citada sai **antes** do
shingling, com o motivo escrito em `:1394-1397`.

## Neutralização de dígito: o gerador desfaz uma correção medida

`internal/legalsignature/NormalizeText` (`signature.go:91-131`) **preserva dígito** e
ainda conserta separador de milhar — BUG-137, 2026-08-29, cujo caso medido é
exatamente um falso positivo de molde por número de edição (`n. 2.204/2.205/2.206`
colapsando no mesmo 6-grama).

`cmd/generate-acordao-pages/main.go:2180,2187` faz
`reDigito.ReplaceAllString(limpo, "N")` — desfaz essa correção em corpus onde o
dígito É o conteúdo (`REsp 1.794.991` ≡ `REsp 2.150.333`).

## Matriz de divergência (n-grama / limiar / normalização / população)

| # | detector | n | limiar | normalização | população | corpo |
|---|---|---|---|---|---|---|
| 1 | acordao `:102-103` | **3** | 0.70 | **dígito→N**, sem acento-fold | run + shards da mesma área | **inteiro (1+2+3)** |
| 2 | lei-artigo `:78-79` | 3 | 0.70 | idem | idem | inteiro |
| 3 | diario `:96-97` | 3 | **0.60** | lower+Fields | lote | **sem citação** |
| 4 | noticia `:79-80`, stf-inf `:65-66`, sumula `:64-65`, tema `:642-643` | 3 | 0.60 | lower+Fields | lote | varia |
| 5 | `v2bodyneardup:62,65` | **5** | 0.70 | `NormalizeText` (dígito preservado) | estoque v2 | `AssembleBody` — **exclui headings** |
| 6 | `quality.go:84` | 5 | **0.82** | `NormalizeText` | acervo construído | **`PlainText()`** — inclui title/meta/heading/legalNotice/publicationPurpose |
| 7 | `quality.go:92` fallback | 5 | 0.82 sobre **stemmed** | dispara para todo par ≥ **0.20** | idem | idem |
| 8 | `v2acervosimilarity:58` | **3 E 5**, `PiorCaso` | 0.70 | `ToLower`+`Fields`, **pontuação presa** | intra-família (2,0% dos pares) | corpo |
| 9 | `v2pagedistinctness:22,28` | 5 | 0.70 + span 40 + densidade 0.15 | `legalsignature`+`ptbrtext` | estoque, incremental | corpo |
| 10 | `portfoliov2distinctness:53-55` | **4 + 3** | 7/10 exato | fold | portfólio | **intenção, não corpo** |
| 11 | `streamdedup.go:55,70` | 5 | 0.70 | `NormalizeText` | — | **sem executor de produção** |
| 12 | `templateaudit:24` | **6** | freq. documental | fold | massa autoral | corpo |
| 13 | `v2ingest/validate.go:22` | **12 exato** | identidade | — | lote | **isenta citação ancorada ≤40 palavras** |
| 14 | `globalsimilarity:34` | 4 | 0.60 | xxhash64 | fronteira de candidatos | campos truncados |
| 15 | `cerebro/gate.go:139` | 5 | 0.70 | — | **contra o texto-fonte** (espelho) | peça |
| 16 | `publicproselanguagepatterns:51-56` | 5..8 dinâmico | 0.92 | fold | corpus dinâmico | superfície curta |
| 17 | `infogain/doorway.go:51` | SimHash/Hamming 16 | 0.50 planta | — | cluster | esqueleto de seções |
| 18 | `audit_v2_pages.py:268` | 12 exato | identidade | isenções de calendário | estoque | corpo |

**Sete famílias de n-grama convivem: 3, 4, 5, 6, 8, 12 e "3 e 5 simultâneos".**
**Cinco limiares: 0.60, 0.70, 0.82, 0.92, 7/10.**
**Quatro normalizações incompatíveis** (dígito→N; `NormalizeText` preservando dígito;
`ToLower`+`Fields` com pontuação presa; stemming PT-BR).

## Comentário que mente (R1 — bug a corrigir, não a citar)

`internal/v2bodyneardup/neardup.go:12-18` afirma que o score é "diretamente
comparável ao gate de produção" e que `internal/quality` usa 0.82 "sobre esta
mesma métrica". **Não é a mesma métrica**: `AssembleBody` (`:157-176`) exclui
deliberadamente os headings; `quality.go:743` usa `Page.PlainText()`
(`internal/content/content.go:523`), que inclui Title, MetaDescription, Heading,
Summary, **LegalNotice**, **PublicationPurpose** e os títulos de seção — ou seja,
a camada 3 emitida pelo template, idêntica por construção em todas as páginas.
`wordWindowHash` é de fato byte-idêntica; o corpo montado não é.

Além disso `quality` é **aproximado** (bucket de 48, 4 vizinhos, bottom-k 64) e
`v2bodyneardup` é **exato** (AllPairs com filtro de prefixo): mesma régua, recall
diferente.

## A lane do cérebro é a MAIS severa do acervo (DEC-059)

`internal/ponteeditorial/ponteeditorial.go:117 LimiarDeRecorrencia = 0.60` —
**abaixo** do 0,70 do acervo, deliberadamente (`:106-116`). Tokenização por
`v2acervosimilarity.Trigramas` (`indice.go:152,174,178`): 3-gramas,
`ToLower`+`Fields`, pontuação presa, **corpo inteiro, citação incluída**,
comparado contra **todo o acervo** (`indice.go:102 CorposDoAcervo`).

Ou seja: o texto que o cérebro escreve é julgado a **0,60 em 3-gramas contra
10k+ páginas, sem separação de camada**. É exatamente a queixa do dono aplicada
ao cérebro.

## Qual régua roda em que ponto do trajeto — resposta direta

1. **`CONTENT_QUALITY` não é gate.** É `docs/CONTENT_QUALITY.md`, documento de
   contrato. `v2bodyneardup:64` chama 0,70 de "limiar do contrato CONTENT_QUALITY".
2. **0,70** é implementado por `v2bodyneardup` (só bancada diária,
   `run-qualidade-diaria:679`) e por `v2acervosimilarity` (sem executor de rotina).
3. **0,82** é `quality.go:84`, e roda em dois pontos: no **publish**
   (`publish-v2-direct/qualitygate.go:78`) como **MÉDIO**, e no **build**
   (`build.go:182`) como **bloqueio duro** — mas o build não está no deploy.
4. **0,60 em 3-gramas** é a régua do cérebro (`ponteeditorial:117`) e dos cinco
   geradores derivados — a mais severa que roda de verdade, junto com a do acórdão.

As duas réguas de `neardup.go:16` (0,82 e 0,70) convivem porque **medem objetos
diferentes**: 0,82 sobre `content.Page` construída, 0,70 sobre o JSONL do estoque v2.

## Precedentes do próprio repo para a régua por camada

**Direção importa, e um revisor hostil vai atacar isso primeiro.** Em
`diario:1394-1397` a citação sai para que ela **não compre unicidade** (o gate
fica MAIS severo). No acórdão, tirar a ementa forense compartilhada torna o score
MENOS severo. O princípio comum não é a direção — é **medir a camada autoral
sozinha**: no diário a citação inflava distinção, no acórdão ela infla
similaridade, e nos dois casos a soma mede a coisa errada. O ancoradouro mais
limpo, porque já é na direção permissiva, é `v2ingest/validate.go:37-40`.

1. `cmd/generate-diario-pages/main.go:1394-1400` — citação sai antes do shingling.
2. `internal/v2ingest/validate.go:37-40` — isenção de duplicidade para citação
   legal ancorada em dispositivo, até 40 palavras.
3. `internal/legalsignature/signature.go:91-113` — BUG-137: dígito preservado
   justamente para não acusar variação numérica legítima como molde.
4. `internal/blocosunicos` — guarda por conteúdo que **não** toca repetição
   interna do texto oficial, porque "reescrevê-la seria adulterar citação".
5. `tools/generate-page-content-revision` — neutraliza blocos estruturais antes
   de hashear.

## Impacto — só o que foi medido

- **acórdão**: 532 de 1.260 iteradas recusadas por `molde_acima_do_limiar`
  (42,2% das iteradas; 70,0% das 760 recusas de `montaPagina`). Número da
  medição `-seco -limite 500` já dada, não recontado aqui.
- **severity**: 0 críticos de similaridade, 5.600 + 2.089 médios em 11.206 linhas
  (medição própria desta sessão).
- **publish**: 0 páginas bloqueadas por similaridade, **por construção** —
  `near_duplicate_content` não está em `criticalQualityCodes`.
- **todas as outras 18 réguas da matriz**: impacto **não medido** (exigiria
  passada sobre o estoque, que é escrita/carga, proibida em PLAN MODE).

## Não medido, e por quê

- `cmd/measure-molde-trigrama` grava `data/ops/molde_trigrama.jsonl` — é escrita;
  não rodei em PLAN MODE. Os números abaixo são **lidos do cabeçalho dele
  (`:11-16`), medição de 2026-09-09 por outra sessão — não medidos por mim**:
  5-gramas máx 0,5904 / zero pares ≥0,70; 3-gramas com dígito neutralizado máx
  0,7304 / cinco pares; 32 pares ≥0,70 em 43 páginas sobre 10.141 vivas (0,4%).
- Não recontei o corpus de acórdãos (532/1260 vem da medição `-seco` já dada).
- Divergência numérica par-a-par entre as 18 réguas: não medida (exigiria passada
  sobre o estoque, que é escrita/carga).
