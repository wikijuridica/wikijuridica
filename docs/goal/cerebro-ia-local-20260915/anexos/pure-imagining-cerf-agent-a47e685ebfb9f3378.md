# LACUNA 1 — A TRAVESSIA INEDITA (familia stj-acordao-derivado)

Investigacao read-only. /opt/wiki. 2026-09-15. Nada foi escrito no repositorio.

VEREDITO: **GRAVE**, com UM achado BLOQUEANTE e a maior parte da cadeia
**CONTROLADA por medicao**. A travessia nao tem ovo-e-galinha e nao exige elo
novo: exige DUAS linhas de registro (uma num gate, uma num runner), UMA correcao
de campo no gerador e UMA ordem de comandos que ja existe escrita.

Por que so UM e bloqueante, pela definicao da tarefa ("quebra a execucao"):
- **A (`lane`) e BLOQUEANTE** nao porque impeca a geracao, mas porque
  consertar DEPOIS de publicar muda o valor da `<meta name="wj-pagina">` sem
  mudar o texto — **mudanca de atributo servido**, que pela matriz do §6 exige
  `./tools/deploy-publico --ressemear` sobre 2.488 paginas, com re-datacao do
  acervo e re-anuncio ao Googlebot. Antes de publicar custa uma linha; depois
  custa uma passada de ressemeadura.
- **B (mapa do `check-derived-authorial-floor`) e GRAVE**, nao bloqueante: uma
  linha, sem republicacao. Estava rotulado bloqueante na primeira redacao e
  fica corrigido aqui.

---

## 0. Fato de partida, confirmado

```
$ ls data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
ls: nao foi possivel acessar: Arquivo ou diretorio inexistente
$ git log --all -- data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
(vazio)
```
Nem no disco, nem em HEAD, nem em nenhum ref. O portfolio par
`data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl` tambem nao existe
(69 arquivos em portfolio_v2, nenhum com esse nome; 879 em v2_pages).

Gerador: `cmd/generate-acordao-pages/main.go`, 2.376 linhas, entrou em
`45d33ee8` (2026-09-10), commit que declara "NAO PUBLICA NADA NESTE COMMIT".
`-seco` **confirmado read-only** no codigo (main.go:214-219: `relata()` +
`imprimeAmostra()` + `return nil` ANTES de `gravaPortfolio`/`gravaShard`).

---

## 1. O PRECEDENTE REAL — como duas familias nasceram (git, nao imaginacao)

### Familia STJ (tema + sumula), 2026-08-20, 280 paginas

| # | commit | hora | o que entrou |
|---|---|---|---|
| 1 | `288d3e16` | 11:18:11 | `internal/content/content.go` + `derived_page_types_test.go` — v2CanonicalPageTypes ganha julgado/tema_repetitivo/norma/sumula |
| 2 | `dbb73e2a` | 11:19:37 | `internal/content/content.go` + teste — `CTALaneDerivada = "derivada_de_fonte_oficial"`, `LaneAutorizaCTA`, `LaneConhecida` |
| 3 | `5998cc47` | 12:03:43 | os GERADORES + `internal/checks/checks.go` + gate novo + **`internal/render/home_areas.go` (+1 linha)** + **`tools/generate-v2-publication-severity` (+28)** |
| 4 | `376e4de4` | 12:04:42 | **SO** `portfolio_v2/{jurisprudencia-stj-derivada-01,sumulas-stj-derivada-01}.jsonl` (200 + 80) |
| 5 | `e9b354dd` | 12:05:27 | **SO** `v2_pages/{stj-tema-derivado-01,stj-sumula-derivada-01}.jsonl` (200 + 80) |

`git rev-parse 376e4de4^` = `5998cc47`; `e9b354dd^` = `376e4de4`. Pai-filho
direto, **45 s** entre o commit de intencao e o de pagina.

### Familia STF (informativo), 2026-08-20, 50 paginas

| # | commit | hora | o que entrou |
|---|---|---|---|
| 1 | `ceb2481a` | 12:28:35 | `cmd/generate-stf-informativo-pages/main.go` (648 l.) **+** `portfolio_v2/jurisprudencia-stf-derivada-01.jsonl` (50), MESMO commit |
| 2 | `a62c27e1` | 12:30:32 | **SO** `v2_pages/stf-informativo-derivado-01.jsonl` (50) |

`a62c27e1^` = `ceb2481a`. Codigo do gerador e portfolio couberam juntos; o que
NUNCA cabe junto e portfolio + pagina.

### A razao, escrita pelo proprio commit `376e4de4`

> "Este commit traz SO as intencoes -- as paginas vem no proximo, e a ordem nao
> e estilo: e exigencia do gate v2-finalized-reference [...] 'The parent
> portfolio is deliberately the membership authority. A candidate cannot add
> its own portfolio row and consume it in the same transaction.' Quatro
> tentativas de commitar intencao e pagina JUNTAS foram recusadas [...] e o
> diagnostico so fechou lendo tools/check-v2-finalized-commit:1341 —
> members = portfolio_membership(OLD), o commit PAI."

**Nota de leitura:** a linha :1341 que o contrato cita hoje esta em
`anchored_membership_additions`; a linha viva da autoridade e
**`check-v2-finalized-commit:1379`** (`members = portfolio_membership(old)`),
dentro de `check_finalized_product`. O deslocamento e de arquivo que cresceu,
nao de regra que mudou.

---

## 2. Ovo-e-galinha: **NAO EXISTE.** Medido no codigo.

`tools/check-v2-finalized-commit:1378-1382`:
```python
if set(old) == {"0"}:
    raise GuardError("produto v2 nao aceita commit raiz sem parent auditavel")
members = portfolio_membership(old)          # old = commit PAI
additions = anchored_membership_additions(new, changed, members)
```
Na primeira travessia:
- **commit 1** toca so `portfolio_v2/` — nenhum path casa
  `FINALIZED = r"data/editorial/v2_pages/[a-z0-9_]+(?:-[a-z0-9_]+)+\.jsonl"`
  (:33), entao `check_finalized_product` nao e chamado. A familia nao precisa
  existir em lugar nenhum.
- **commit 2** toca so `v2_pages/` — o pai JA tem as linhas de portfolio.

`portfolio_membership` so aborta com "portfolio_v2 candidato esta vazio" (:972)
se o portfolio INTEIRO estiver vazio — nao e o caso (11.438 intents
commitados, medido). Nao ha bootstrap especial a pedir, nao ha excecao a
autorizar, nao ha `--force`. **CONTROLADO.**

Os nomes novos passam as duas regex de path por construcao:
`stj-acordao-derivado-01.jsonl` casa `FINALIZED` (:33) e o portfolio homonimo
casa `PORTFOLIO = r"data/editorial/portfolio_v2/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl"`
(:34). O intent `jur-stj-resp-1674372` casa
`CANONICAL_INTENT_ID = r"[a-z0-9]+(?:-[a-z0-9]+)*"` (:52).

Tetos do gate, contra o lote de 2.488 (medido: 3.899 B/linha na familia
derivada mais parecida, `stj-tema-derivado-01`, 1.074 linhas / 4.187.968 B):
shard projetado ~9,7 MB contra `MAX_FILE_BYTES = 64 MB` (:76) e
`MAX_GIT_BYTES = 128 MB` (:75); 2.488 registros contra
`MAX_RECORDS = 2.000.000` (:77). **Folga de 6,6x no pior teto.**

---

## 3. Cada elo da cadeia, e o que e especifico de familia

### 3.1 `shardpreserve` — no-op correto na estreia (CONTROLADO, com ressalva)

`internal/shardpreserve/shardpreserve.go:79-83`:
```go
saida, err := gitenv.Command(raiz, "show", "HEAD:"+shardRel).Output()
if err != nil { return nil }        // shard inexistente em HEAD: zero preservados
```
Na estreia o `git show` falha, `Completa` devolve `(montado, 0)` e o gerador
**nao imprime** "shard: N pagina(s) preservada(s)". Correto: nao ha nada a
preservar. `tools/check-shard-preservation` usa o mesmo criterio (o commit),
entao produtor e gate concordam sobre o que e perda.

**A ressalva, e ela e real:** o MESMO caminho de erro cobre "arquivo nao existe
em HEAD" e "git falhou" (GIT_DIR poluido, objeto ausente, worktree trocado —
riscos que o proprio pacote documenta em `CompletaDestino`). Da segunda passada
em diante, a ausencia da linha impressa deixa de ser esperada e passa a ser
alarme — e nada no codigo distingue os dois casos. Para uma familia que nascera
com 2.488 linhas, a segunda passada com `-limite 30` (o default) e um git
quebrado reescreveria o shard com 30 registros e nao diria nada.

### 3.2 `tools/check-v2-portfolio-pairing` — family-agnostic (CONTROLADO)

Globa `portfolio_v2/*.jsonl` (:113) e `v2_pages/*.jsonl` (:123). Sem lista,
prefixo ou mapa de familia. Espelha a regra do gate (autoridade = `HEAD`;
pendente = disco, ou `--index`) e imprime os dois comandos na ordem certa.

Baseline medido agora (exit 0):
```
paginas   : 11106 intents ATIVOS em data/editorial/v2_pages (tombstones fora)
portfolio : 11438 intents ja COMMITADOS, 11438 no estado atual
pareamento OK: toda pagina tem intencao 1:1 ja no commit pai.
```

### 3.3 O censo de severidade — CONTROLADO, com dupla cobertura

`tools/generate-v2-publication-severity` enumera por `glob.glob(PAGES_GLOB)`
(:629, :645) — family-agnostic. E a area resolve por DOIS caminhos independentes:
- `CATALOG` (:55-74) ja contem `"jurisprudencia"` (:67), acrescentada em
  `5998cc47` por esta exata armadilha;
- `INTENT_PREFIX_AREA` (:77-86) ja contem `"jur": "jurisprudencia"` (:86).

`derive_area(shard, intent, practice_area)` (:428): **passo 1** devolve a
`practice_area` declarada quando ela esta no CATALOG — e o gerador declara
`practiceArea = "jurisprudencia"` (main.go:77). O **fallback** tambem acerta:
`stj-acordao-derivado-01` -> sufixo `-01` descartado -> `stj-acordao-derivado`
fora do CATALOG -> `stj` fora -> prefixo do intent `jur` -> `jurisprudencia`
(:467). **Nenhuma linha nova a acrescentar aqui** — ao contrario do que a
armadilha de 2026-08-20 faria supor.

Idem para os catalogos-irmaos: `internal/render/home_areas.go` e
`content/area_hub_editorial.json` ja tem `jurisprudencia` (medido).

### 3.4 `internal/v2ingest` — a familia NAO PASSA por ele

`internal/v2ingest/validate.go:57-67`:
```go
var wordCountBands = map[string]wordCountBand{
  "verbete":{350,700}, "pergunta":{400,800},
  "guia_problema":{700,1400}, "procedimento":{500,1000}}
var validLanes = map[string]bool{"comercial":true, "informativa":true}
```
Distribuicao medida nos 5 shards derivados que existem:

| shard | practice_area | page_type | lane | n |
|---|---|---|---|---|
| stj-tema-derivado-01 | jurisprudencia | `tema_repetitivo` | `derivada_de_fonte_oficial` | 1.074 |
| stf-informativo-derivado-01 | jurisprudencia | `julgado` | `derivada_de_fonte_oficial` | 60 |
| stj-sumula-derivada-01 | sumulas | `sumula` | `derivada_de_fonte_oficial` | 112 |
| noticias-oficiais-01 | noticias | `noticia` | `derivada_de_fonte_oficial` | 59 |
| diarios-municipais-01 | diarios | `diario-oficial` | `derivada_de_fonte_oficial` | 51 |

**5 de 5** usam page_type sem banda em `wordCountBands` e lane fora de
`validLanes`; amostra de `stj-tema-derivado-01` traz `word_count: 802`, acima
do teto de qualquer banda. Conclusao: os canais derivados vao por
`cmd/publish-v2-direct` (o nome diz), nao por `v2ingest`. Nao ha validacao
por familia, nao ha `pageType` a registrar, nao ha banda a acrescentar.

O gerador de acordao, porem, foi escrito PARA a banda do v2ingest
(main.go:82-83, "Banda do `verbete` em internal/v2ingest/validate.go:56",
piso 350 / teto 700) e declara `lane = "informativa"` — a unica lane que
`validLanes` aceitaria. **Ele conforma a um validador que a familia dele nao
usa, e paga por isso no 3.5.**

### 3.5 ACHADO BLOQUEANTE A — `lane = "informativa"` desliga tres instrumentos

`cmd/generate-acordao-pages/main.go:78`. Os 5 irmaos declaram
`derivada_de_fonte_oficial` (grep confirma nos 5 geradores). O commit
`45d33ee8` **nao da nenhuma justificativa** para a divergencia — e descreve o
conteudo como derivado ("AS DUAS CAMADAS (DEC-032)", "o RESULTADO so aparece
CITADO"). `dbb73e2a` criou `CTALaneDerivada` exatamente para isto e escreveu
por que as duas nao se fundem: *"as duas nunca recebem convite comercial, mas
respondem a perguntas diferentes [...] Fundir as duas apagaria a distincao
justamente onde ela serve"*.

`content.LaneConhecida()` aceita `informativa` (content.go:278), entao **nada
reprova** — e essa e a gravidade: o defeito atravessa todos os gates.
`internal/v2publish/v2publish.go:377` propaga sem traduzir:
`CTALane: strings.TrimSpace(page.Lane)`.

Consequencias, por arquivo:linha:

1. **`internal/checks/derived_repetition.go:92`**
   ```go
   if p.Skipped || p.Lane != "derivada_de_fonte_oficial" || p.Opening == "" { continue }
   ```
   O gate anti-repeticao de pagina derivada pula por LANE. As 2.488 ficam
   invisiveis; o gate segue VERDE sem ler nenhuma. O cabecalho do arquivo
   registra que ele nasceu porque "82 das 358 paginas derivadas repetiam ao
   menos uma frase de acordao entre blocos" — o risco exato desta familia, que
   monta a pagina a partir de ementa + dispositivo + tema + FAQ.

2. **`internal/checks/text_truncation.go:132`**
   ```go
   if p.Lane == "derivada_de_fonte_oficial" { ... titulojuridico.Valido(sufixo) }
   ```
   A regua EXTRA de titulo derivado (oracao relativa pendurada, verbo solto,
   numeracao de item, caixa alta do catalogo) so roda nessa lane. O titulo do
   acordao e EXTRAIDO do texto do tribunal (classe + processo + rubrica da
   ementa em versal — `cabecalhoDaEmenta`, main.go:1307) — exatamente o que a
   regua cobre, e nao sera medido.

3. **`internal/seo/seo.go:126`** — a dimensao `lane` da `<meta name="wj-pagina">`
   (GA4 `content_group` + Clarity) reportaria 2.488 paginas derivadas como
   `informativa`, contra as 399 derivadas de hoje: a serie de retorno por
   agente, que e a metrica que vale no §12, perde a unica dimensao que separa
   conteudo derivado — e o comentario do proprio arquivo diz que a lane e o
   unico sinal que **nao** sai de heuristica.

**Conserto:** `lane = "derivada_de_fonte_oficial"` (uma linha). O piso/teto de
palavras do gerador sao constantes proprias (main.go:82-83), independentes do
page_type — trocar a lane **nao muda quantas paginas passam**.

4. **`cmd/generate-acordao-pages/main_test.go:124` NAO PEGA ISSO, e nunca
   pegaria.** A asserçao e
   `if pagina.PageType != pageType || pagina.PracticeArea != practiceArea || pagina.Lane != lane`
   — compara o campo com a PROPRIA CONSTANTE. E tautologia (o padrao "rotulo de
   executor e tautologia" da memoria do projeto): qualquer valor que a constante
   assuma deixa o teste verde. A bancada de 1.106 linhas tem zero ocorrencia do
   literal `derivada_de_fonte_oficial`. O conserto precisa de um teste que
   assere o LITERAL, ou melhor, que compare esta familia com os 5 shards irmaos
   no disco.

### 3.6 ACHADO GRAVE B — `check-derived-authorial-floor:279` tem LISTA de familia, e a nossa nao esta nela

```python
# FAMILIA NOVA ENTRA AQUI OU NASCE FORA DO GATE, e isso ja quase aconteceu: em
# 2026-09-10 o motor de paginas de artigo de norma (`leis-motor-*`) produziu 44
# paginas com camada citada e camada autoral distintas — exatamente o objeto da
# DEC-032 — e o mapa nao a conhecia. Sem a linha abaixo, o EIXO 3 nao a mediria
# nem depois de publicada: o gate ficaria verde sobre uma familia que ele nao
# olha, que e o modo mais silencioso de um detector mentir.
FAMILIAS_CANAIS_DERIVADOS = {
    "diarios-municipais":       "diarios-municipais-*.jsonl",
    "leis-motor":               "leis-motor-*.jsonl",
    "noticias-oficiais":        "noticias-oficiais-*.jsonl",
    "stf-informativo-derivado": "stf-informativo-derivado-*.jsonl",
    "stj-sumula-derivada":      "stj-sumula-derivada-*.jsonl",
    "stj-tema-derivado":        "stj-tema-derivado-*.jsonl",
}
```
`stj-acordao-derivado` **ausente**: 6 familias, 0 cobrem a nova. O aviso esta
escrito no codigo pelo autor anterior, e e literalmente o nosso caso. E
agravante: **o gerador declara seguir a regua deste gate "byte a byte"**
(main.go:85-101 cita :262, :263, :264, :274) — ele obedece a um gate que nunca
vai olhar para ele.

**E o EIXO 3 nao escala.** `pares_quase_identicos` (:491) e O(n^2) sem
amostragem, e a docstring esta desatualizada: diz *"a maior familia tem 205
paginas — 20.910 pares"*; a maior hoje tem **1.074 linhas** (576.201 pares).

Medido nesta sessao, com os shingles de 3-gramas do proprio
`stj-tema-derivado-01` (mediana 274 shingles/pagina) — **composicao de corpo
APROXIMADA** (`opening + sections[].text`), nao a `corpo_editorial()` do gate,
que le o `<main>` do HTML e e maior; o custo por par, portanto, e piso, nao
teto —, 200.000 pares reais em Python puro **sob load 13,15** (declaro a carga:
o numero e teto superior em tempo, nao taxa livre):

```
64,16 us/par
n=1.074  ->    576.201 pares ->  37,0 s
n=2.488  ->  3.093.828 pares -> 198,5 s
n=4.763  -> 11.340.703 pares -> 727,6 s   (se o poco inteiro virar pagina)
```
E `todos.append(...)` guarda TODOS os pares antes de `todos.sort()`. Memoria
medida diretamente com 3.093.828 tuplas reais: **308 MB, 437 MB apos o sort**.
Sobrevive nos 7 GiB disponiveis, mas entra na mira do earlyoom junto com o
Ollama, e a bancada diaria ja segura o flock por ~70 min.

**Conserto:** a linha no mapa e obrigatoria (senao o gate mente). O eixo 3
precisa, no mesmo passo, de um teto: guardar so os pares acima de um piso
(`if score >= limiar_de_relato`) em vez de todos, ou bandear por LSH. Guardar
3,1 milhoes de tuplas para relatar algumas dezenas e desperdicio, e ele so
aparece quando a familia e grande.

### 3.7 Colisao de rota e de intent — CONTROLADO, medido em quatro eixos

`v2-cross-shard-collision` (atalho de 22 linhas para o gate Go
`internal/v2crossshardcollision`) e `v2-public-path-collision`
(`internal/v2publicpathcollision`) sao **globais sobre o estoque**, sem lista de
familia. `v2publish.SelectPublishable:425-434` tambem recusa rota colidente
dentro da onda ("rota_colidente:<path>").

Medicao propria sobre o corpus real
(`data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl`, 60.221 registros
— o corpus cresceu: o commit do gerador citava 37.085), aplicando o filtro de
classe do gerador (`classesProcedimentais`, main.go:314) e a `publicpath.Slug`
verdadeira (main.go:25-37):

```
registros de merito (nao-procedimentais)         10.414
intent_id candidatos distintos                   10.410
COLISAO candidato x portfolio_v2 (11.438)             0
COLISAO candidato x v2_pages    (11.206)              0
COLISAO candidato x published_manifest (11.106)       0
COLISAO DE ROTA candidato x /jurisprudencia/ (1.134)  0
```
Zero nos quatro. As 4 colisoes internas ao corpus
(`jur-stj-resp-{2023898,2083153,1963819,2012233}`, 8 registros, mesmo par
classe+numero) sao tratadas pelo proprio gerador em `main.go:283-288` como
recusa contada `rota_duplicada_no_corpus` — **nao** como sobrescrita silenciosa,
que foi o defeito da familia de tema. E `intentsPublicados` (main.go:735-762)
globa todos os shards **exceto o prefixo proprio**, o que cobre a colisao com
familia irma sem depender de `shardpreserve.IdsDeOutrosShards` (que o gerador
nao chama).

Ressalva: `protegidos` cobre `v2_pages/`, **nao** `portfolio_v2/`. Intent que ja
existisse no portfolio sem pagina viraria linha duplicada e
`portfolio_membership` abortaria o commit inteiro com "intent_id duplicado no
portfolio" (:967). Medido: **0 de 10.410** — hoje nao morde.

### 3.8 Sitemap e `published_manifest` — CONTROLADO por desenho

`sitemap.PortalPlanOptionsAlocandoRegistry` (sitemap.go:126-142): so o
PUBLICADOR aloca numero; o servidor e o `cmd/build` leem. A particao agrupa por
**(data de revisao, area)** com `minCohortURLs = 50` e
`PortalMaxURLsPerShard = 5000`.

As 2.488 paginas novas sao UMA coorte `<data>|jurisprudencia#0` — 2.488 < 5.000,
entao **um shard novo**, numero novo do registry, **zero deslocamento** dos 119
arquivos existentes. E o mecanismo ja e exercitado para esta area: o registry
vivo (`data/ops/sitemap_shard_registry.json`, `next_id: 110`, 63 coortes) tem
`retired` com `2026-09-06|jurisprudencia#0`, `2026-09-08|jurisprudencia#0` e
`2026-09-09|jurisprudencia#0`. A memoria "ordinal posicional some quando o
plano encolhe" descreve o plano ENCOLHENDO; aqui ele cresce, e o registry
existe precisamente para isso (`por_que`: "O numero pertence a COORTE, nao a
posicao dela no plano").

Familia nova **nao** exige shard de sitemap declarado a mao. **CONTROLADO.**

### 3.9 O UNICO passo de ordem que a travessia exige, e ele ja tem gate

`internal/v2publish/v2publish.go:398-401`:
```go
row, ok := severity[page.IntentID]
if !ok { skipped[page.IntentID] = "sem_linha_no_censo"; continue }
```
Pagina que o censo nunca viu **nao publica, em silencio**. E o censo
(`data/editorial/v2_publication_severity.jsonl`) e um derivado de mtime:
`tools/check-censo-acompanha-estoque` compara o mtime do censo com o do shard
mais novo e reprova. Seu cabecalho documenta o incidente exato:
*"agentes regeneraram 390 paginas as ~10:00; o censo era das 04:36; a
publicacao manual das 11:00 recusou 5 paginas com sem_linha_no_censo"*.

`tools/publicar` ja embute isso como **passo 2 de 5** (`censo_em_dia`, :110-141)
e regenera quando atrasado. Entao a "ordem topologica de ~9 artefatos" que
custou 31 dias **nao se aplica** a esta travessia: os demais insumos do censo
(`quality`, `readiness`, `rewrite_queue`, vereditos) sao consultados por
`.get(intent, {})` com default, de modo que pagina nova ausente deles nao gera
critico — apenas nao gera motivo.

### 3.10 O motivo critico que poderia zerar a familia em silencio — medido, e nao morde

Dos onze criticos vivos em `generate-v2-publication-severity`, os que dependem
do DADO da familia:
- `area_nao_derivavel` (:785): coberto em duplicidade (3.3). **0.**
- `defeito_de_encoding` (:720, `MOJIBAKE_RE` :110 + `MOJIBAKE_C1_RE` :130 —
  a terceira classe entrou em `daf1e99a`, 2026-09-10): medido sobre os 10.414
  registros de merito, campos ementa/dispositivo/tema/relator/orgao/classe/
  jurisprudencia_citada — **0 byte C1 cru (0,00%), 0 U+FFFD, 1 ocorrencia de
  mojibake latin1**. Essa 1 vira 1 pagina critica, nao um lote.
- `corpo_abaixo_de_250_palavras`: o gerador impoe piso 350 por construcao.
- `intent duplicado entre shards`: **0** (3.7).
- `reprovada_por_auditor` / `veredito_conflitante` / `campo_obrigatorio_ausente`:
  derivam de artefatos indexados por intent que nao conhecem os ids novos.

**CONTROLADO por medicao.** O censo nao vai engolir a familia.

### 3.11 ACHADO GRAVE — o canal de maquina nao nasce com a familia

`cmd/publish-v2-direct` **nao reinicia o servico** (grep: zero `systemctl`,
zero `restart`; so purga de borda, :2155). Quem reinicia e
`tools/deploy-publico` (:738 `systemctl stop`, :884 `start`), e e ele — no
**passo 2.6/7**, :677 — que regenera `content/legal_cocitation_index.jsonl`.
O comentario do proprio script fixa a janela:

> "o indice deriva de content/pages.json, que o passo 1 acabou de reescrever, e
> e lido UMA vez no BOOT do servidor."

Consequencia para a estreia: publicar com `tools/publicar` (que roda
`publish-v2-direct --allow-public-write`, :143-156, e **nao** o deploy) poe
2.488 HTMLs estaticos no ar e deixa o processo Go com o `pages.json` antigo em
memoria — **sem gemea Markdown, sem `/api/v1`, sem MCP `ler_pagina`, sem A2A**
para nenhuma das 2.488 rotas, num projeto cujo §12 diz que "o portal e um
servico para IA" e que a metrica que vale e retorno e citacao por agente.

A degradacao dos "Percursos por fundamento legal" e honesta e ja defendida em
duas camadas (artefato ausente => secao omitida;
`httpserver.filtraPercursosServiveis` descarta destino nao servido) — mas a
AUSENCIA DA ROTA no canal de maquina nao e degradacao aditiva: e 404.

**Conserto:** a estreia fecha por `./tools/deploy-publico`, nunca por
`tools/publicar` sozinho. E a familia estreia mudando TEXTO (paginas novas),
logo **sem `--ressemear`** — a re-datacao e verdadeira.

### 3.12 ACHADO GRAVE — a fonte nao declara sigilo, e o filtro de excecao taxativa nao existe

`internal/stjacordaos/registro.go:52,99`: `NivelSigilo *int` fixado em `nil`, e
`registro_test.go:49-50` **assere** que tem de sair nulo — *"o espelho nao
declara nivel de sigilo"*. Medicao propria: `nivel_sigilo` NULO em **10.414 de
10.414 (100,0%)**.

Isto corrige uma leitura minha anterior nesta mesma investigacao, e o erro e o
da memoria "varredura com campo inexistente": contar `nivel_sigilo != 0` devolve
zero, e zero ali **nao e evidencia de ausencia de segredo** — e evidencia de que
o canal nao carrega o campo. O §2 do contrato diz que o barrado "na API do CNJ
[...] vem marcado — `nivelSigilo > 0`, e o campo existe para ser respeitado".
**Neste canal ele nao existe**, e o gerador nao tem nenhuma linha de sigilo,
anonimizacao ou excecao taxativa (grep em `cmd/generate-acordao-pages`: zero).

O que muda o risco de lugar, e e a diferenca entre esta familia e as 5 irmas:
tese, sumula e informativo sao atos ABSTRATOS; esta familia publica a ementa de
um PROCESSO CONCRETO. `internal/publicidadenome` existe e cobre isso — mas por
glob fixo `diarios-municipais-*.jsonl` (:180), com early-return
*"sem estoque de diario neste checkout: nada a cobrar"*.

Medicao que dimensiona o risco, sobre os 10.414:

| sinal | ocorrencias | leitura |
|---|---|---|
| CPF formatado / CNPJ | **0 / 0** | o identificador que o §2 manda remover nao esta la |
| rotulo de parte na ementa ("Recorrente:", "Autor:"...) | **4** | a ementa do STJ e abstrata; nome de parte nao circula nela |
| `11\.?340` / "Maria da Penha" / "violencia domestica" | **8** | 2 dos 2 amostrados sao caso genuino — excecao taxativa do §2 |
| "segredo de justica" / "sigilo" no texto | 46 | mencao, nao marcador; exige leitura |
| padrao de ECA/adocao | 326 (3,13%) | **medicao NAO CONFIAVEL**: os 2 amostrados sao "adocao de providencia" e "adocao de entendimento" — o verbo comum, nao o instituto. Numero real nao medido |

Ou seja: o achado NAO e "vaza PII" (medido: nao vaza). O achado e que **as
excecoes taxativas do §2 nao tem filtro nenhum neste canal**, a ordem de
grandeza e de dezenas em 10.414, e o unico numero que eu produzi para ECA/adocao
e um falso positivo que eu mesmo preciso declarar como nao medido.

### 3.13 Onde a familia precisa entrar num runner

`tools/run-daily-content:369-373` tem os 5 geradores derivados num array, com
teto por variavel de ambiente:
```bash
[stj - tema]=".../generate-stj-tema-pages -limite ${WIKI_LIMITE_STJ_TEMA:-200}"
[stj - sumula]=".../generate-stj-sumula-pages -limite ${WIKI_LIMITE_STJ_SUMULA:-80}"
[stf - informativo]=".../generate-stf-informativo-pages -limite ${WIKI_LIMITE_STF_INFORMATIVO:-60}"
[noticias]=".../generate-noticia-pages -limite ${WIKI_LIMITE_NOTICIAS:-40}"
[diarios]=".../generate-diario-pages -limite ${WIKI_LIMITE_DIARIOS:-30}"
```
`generate-acordao-pages` **ausente** (confirma o P6). A onda ja roda censo no
passo 7/9 (:640-645) e publicacao no 8/9, na ordem que o 3.9 exige.

### 3.14 A onda diaria JA faz a danca de dois commits, e JA encena arquivo novo (CONTROLADO — e muda a Fase 1)

`tools/run-daily-content:614` e `:631`:
```bash
[[ -n "$(git ls-files --others --exclude-standard data/editorial/portfolio_v2)" ]]
    git add data/editorial/portfolio_v2
    git commit -q -m "chore(portfolio): intencoes da onda diaria de $HOJE" -- data/editorial/portfolio_v2
...
[[ -n "$(git ls-files --others --exclude-standard data/editorial/v2_pages)" ]]
    git add data/editorial/v2_pages
    git commit -q -m "chore(paginas): estoque da onda diaria de $HOJE" -- data/editorial/v2_pages
```
`--others --exclude-standard` e **exatamente** o teste de arquivo UNTRACKED.
Entao a onda encena e commita um shard inedito — o produto **nao** ficaria
untracked, e `HEAD` confirma o par vivo (`7ac3dff5 chore(portfolio)` ->
`62d71de0 chore(paginas)`, 2026-09-15). Etapa `3.5/9 produto untracked (avisa,
nao para)` cobre o resto. **CONTROLADO.**

**Duas consequencias operacionais, e elas mudam o plano:**
1. Se a edicao #4 (registrar o gerador no runner) entrar na Fase 1, a **proxima
   onda faz a estreia sozinha**, com `-limite ${WIKI_LIMITE_STJ_ACORDAO:-200}` —
   nao com as 2.488. Isso nao quebra nada (a familia nasce com 200 e cresce),
   mas e uma decisao, nao um acidente: para a estreia grande, a edicao #4 vai
   num commit **depois** da Fase 5.
2. A onda faz `git add data/editorial/v2_pages` **por diretorio**. Shard gerado
   a mao e nao commitado dentro da janela da onda e **varrido** para o commit
   dela — a armadilha "git add por diretorio varre outra sessao". Janela medida
   agora (`systemctl list-timers`, timer `active`/`enabled`):

| timer | proximo disparo medido |
|---|---|
| `wikijuridica-daily-content.timer` | **Wed 2026-09-16 04:31:33 -03** |
| `wikijuridica-qualidade-diaria.timer` (flock heavy ~70 min) | Wed 2026-09-16 04:47:17 -03 |
| `wikijuridica-daily-content-noticias.timer` | Wed 2026-09-16 12:20:55 -03 |

Fazer as Fases 3 a 5 **fora de 04:31-06:00 e de 12:20**.

### 3.15 Nao ha guarda de epoca/frescor de estoque no caminho do publicador (CONTROLADO — medido como zero)

A armadilha nomeada na tarefa ("fingerprint mismatch", ~9 artefatos, 31 dias
parados) foi procurada no PUBLICADOR, nao so no censo:

```
grep -nE "stockmanifest|stock_manifest|epoch|Epoch|freshness|Freshness|
          fingerprint|Fingerprint|StockRead|lease|Lease"
  cmd/publish-v2-direct/main.go   -> nenhuma validacao; os 2 hits sao
                                     comentario alheio (:1230 fingerprint de
                                     410, :2033 check-edge-discovery-freshness)
  internal/v2publish/*.go         -> ZERO ocorrencias
```
`tools/check-v2-stock-epoch` e `check-v2-stock-freshness` existem, mas **nao
estao no caminho de `publish-v2-direct`**. E a lista de 8 etapas da onda
(`run-daily-content:12-24`) nao tem nenhum passo de regeneracao de artefato de
estoque entre `2. gerar` e `6. censo` — so `3. preservar` e `4. parear`, que sao
conferencias. O `releaseGateID` (`:3754`) e derivado por `intent_id` e o indice
de release e **escrito** pela transacao (`:2115-2118`), nao exigido antes.

Logo, o unico derivado de ordem obrigatoria nesta travessia e o censo (3.9).
**A cadeia de 9 artefatos nao entra aqui.**

### 3.16 Reatestacao do grafo do validador — NAO e exigida (CONTROLADO)

O grafo hasheia o diretorio `internal/v2ingest` + `go.mod`/`go.sum`. Imports
internos de `internal/v2ingest` (medido, sem testes): authorialmasscontentexpansion,
authorialmassdrafts, finalizedjsonl, hostnamespace, lexml,
officialsourcespecificity, **ptbrtext**, **publicpath**, publishedmanifest,
stockmanifest, strictjson, v2portfolioindex, v2portfoliomigration, v2readguard.

Os consertos propostos tocam `cmd/generate-acordao-pages/main.go` (package
`main`: nada o importa, logo fora do grafo por construcao),
`tools/check-derived-authorial-floor` (Python) e `tools/run-daily-content`
(shell). **Nenhum** entra no fecho. `internal/content` tambem nao esta na lista.

**Guardrail:** se o conserto derivar para `internal/ptbrtext` ou
`internal/publicpath`, a atestacao passa a ser obrigatoria no mesmo commit
(`./tools/go-modern generate ./internal/v2ingest`), com `git status go.mod
go.sum` limpo antes.

---

## 4. Resumo do veredito por elo

| elo | especifico de familia? | estado |
|---|---|---|
| ordem portfolio -> pagina (commit pai) | nao | **CONTROLADO** (regra global, sem bootstrap) |
| regex de path e de intent do gate | nao | **CONTROLADO** (casa por construcao) |
| tetos do gate (bytes, registros) | nao | **CONTROLADO** (folga 6,6x) |
| `shardpreserve` | nao | **CONTROLADO** na estreia; sinal ambiguo depois |
| `check-v2-portfolio-pairing` | nao | **CONTROLADO** |
| censo: CATALOG / INTENT_PREFIX_AREA | **sim** | **CONTROLADO** — ja cobre, em duplicidade |
| `internal/v2ingest` | **sim** (bandas, lanes) | **NAO SE APLICA** — canal derivado nao passa por ele |
| `lane` | **sim** | **BLOQUEANTE A** — desliga 2 gates + 1 dimensao; conserto pos-publicacao exige `--ressemear` |
| bancada do gerador (`main_test.go:124`) | **sim** | **GRAVE** — asserçao tautologica: nunca pegaria o A |
| `check-derived-authorial-floor` | **sim** (mapa fixo) | **GRAVE B** — familia fora do gate + O(n^2) sem teto |
| colisao de intent / rota | nao | **CONTROLADO** — 0 em 4 eixos, medido |
| sitemap (registry de coorte) | nao | **CONTROLADO** — 1 shard novo, 0 deslocamento |
| censo mais novo que o shard | nao | **CONTROLADO** — `check-censo-acompanha-estoque` |
| criticos do censo sobre o dado | **sim** | **CONTROLADO** — 1 pagina, nao um lote |
| canal de maquina (restart + 2.6) | nao | **GRAVE** — estreia por `publicar` deixa 2.488 rotas 404 na maquina |
| excecao taxativa / sigilo | **sim** | **GRAVE** — canal sem `nivelSigilo`, sem filtro |
| runner | **sim** | **GRAVE** — gerador orfao, `-limite` default 30 |
| onda encena arquivo novo (`??`) | nao | **CONTROLADO** — `ls-files --others`; mas `git add` por diretorio cria janela |
| guarda de epoca/frescor no publicador | nao | **CONTROLADO** — medido: zero ocorrencias |
| commit dos derivados da transacao | nao | **GRAVE** — 6 caminhos, nenhuma fase os commitava (Fase 7b) |
| atestacao do grafo | nao | **CONTROLADO** — fora do fecho |
| duracao do pre-commit com 2.488 registros | nao | **NAO MEDIDO** — exigiria commitar |

---

## 5. A SEQUENCIA EXATA DA PRIMEIRA TRAVESSIA

Derivada de `5998cc47 -> 376e4de4 -> e9b354dd` e de
`ceb2481a -> a62c27e1`, com os consertos dos achados encaixados no commit de
CODIGO (que e onde `5998cc47` os pos).

### Fase 0 — antes de tudo

```bash
./tools/check-load-headroom --max 12
./tools/check-coord-status
./tools/check-coord-inbox --agent <ID> --last 15
git status --short data/editorial/portfolio_v2 data/editorial/v2_pages
git diff --cached --name-only            # o indice TEM de estar vazio
```
Janela 09:40-10:20 e a da bancada diaria (flock ~70 min). Commit de codigo
Go serializa em `flock /tmp/opt-wiki-commit.lock`.

### Fase 1 — COMMIT DE CODIGO (o equivalente do `5998cc47`)

Edicoes, todas fora do fecho da atestacao (3.16). A edicao do runner **sai
desta fase** e vai para a Fase 7c, pelo motivo medido em 3.14.

1. `cmd/generate-acordao-pages/main.go:78` -> `lane = "derivada_de_fonte_oficial"`
2. `cmd/generate-acordao-pages/main.go:76` -> `pageType = "julgado"` (decidido,
   ver §6)
3. `cmd/generate-acordao-pages/main_test.go:124` -> trocar a asserçao
   tautologica por uma que assere os LITERAIS `"julgado"` e
   `"derivada_de_fonte_oficial"`, mais um caso que leia os 5 shards irmaos do
   disco e exija a mesma lane. Prova por mutacao: com `lane = "informativa"` o
   teste tem de ficar VERMELHO (hoje fica verde).
4. `tools/check-derived-authorial-floor:279` -> acrescentar
   `"stj-acordao-derivado": "stj-acordao-derivado-*.jsonl"`
5. `tools/check-derived-authorial-floor:491` -> teto no eixo 3: guardar so pares
   `>= piso de relato` em vez de todos, e corrigir a docstring (205 -> 1.074 hoje
   -> 2.488 previstos). Sem isso o gate aloca 308 MB (437 MB apos o sort) e gasta
   ~198 s so no eixo 3 — medido.
6. teste de regressao para 4, provado por mutacao: removendo a linha do mapa, o
   teste fica VERMELHO.

```bash
./tools/go-modern build ./internal/... ./cmd/...
./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/
git add cmd/generate-acordao-pages/main.go
git add cmd/generate-acordao-pages/main_test.go
git add tools/check-derived-authorial-floor
flock /tmp/opt-wiki-commit.lock git commit -F /tmp/msg-codigo.txt
```

### Fase 2 — PASSADA SECA (nada gravado, confirmado em codigo)

```bash
./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000
```
Leia as recusas nomeadas e confirme o poco (2.488 + 1.405 + 682 + 165 + 22 + 1
= 4.763). Observacao do P4 que vale aqui: as recusas sao `Recusas[motivo]++`
num map (main.go:275-297) — nenhum `intent_id` vai a disco, entao nenhuma pode
ser nomeada nem refutada. Para a ESTREIA isso nao bloqueia; para o §5 do
contrato, bloqueia.

### Fase 3 — GERAR (escreve os DOIS arquivos de uma vez)

```bash
./tools/go-modern run ./cmd/generate-acordao-pages -limite 2500
```
`executar` grava portfolio (:222) e **depois** shard (:225), no mesmo processo.
Confira que a linha "shard: N pagina(s) preservada(s)" **NAO** aparece — na
estreia isso e correto (3.1).

```bash
./tools/check-v2-portfolio-pairing
# esperado: exit 1, "ORDEM DE COMMIT PENDENTE: N intencao(oes) [...] nao no commit pai"
# e ele imprime os dois comandos seguintes
```

### Fase 4 — COMMIT 1: SO O PORTFOLIO (o `376e4de4`)

```bash
git add data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
git commit -F /tmp/msg-portfolio.txt -- data/editorial/portfolio_v2
```
Commit de DADO: leve, sem build. Nao use `git add` por diretorio.

### Fase 5 — COMMIT 2: SO AS PAGINAS (o `e9b354dd`)

```bash
./tools/check-v2-portfolio-pairing        # exit 0: "pode commitar"
git add data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
./tools/check-v2-portfolio-pairing --index    # <1 s, ANTES de o pre-commit compilar
git commit -F /tmp/msg-paginas.txt -- data/editorial/v2_pages
```
O `--index` materializa o proprio `git write-tree` e responde em menos de um
segundo — e a ferramenta nasceu porque quatro tentativas queimaram um
pre-commit inteiro cada. Se o gate recusar com "intent fora/ambiguo no
portfolio candidato", **nao insista**: a autoridade e o pai.

**ESTA E A UNICA ETAPA DA SEQUENCIA NAO EXERCITADA NESTA ESCALA.** Maior commit
de estreia no precedente: 200 paginas (`e9b354dd`); maior shard de hoje: 1.074,
crescido incrementalmente ao longo de 3 semanas. `check_page_product`
(`check-v2-finalized-commit:1417`) valida CADA registro do shard alterado
dentro do pre-commit. **Duracao do pre-commit com 2.488 registros novos: NAO
MEDIDO** — nao foi medido porque medir exigiria encenar e commitar, que o modo
somente-leitura desta investigacao proibe. Encene com um lote pequeno
(`-limite 50`) antes de ir a 2.488 se quiser o numero.

### Fase 6 — CENSO E GATES, antes de publicar

```bash
./tools/check-censo-acompanha-estoque            # espera: ATRASADO (exit 1)
python3 tools/generate-v2-publication-severity --write
./tools/check-censo-acompanha-estoque            # espera: exit 0
./tools/check-v2-cross-shard-collision
./tools/check-v2-public-path-collision
./tools/check-shard-preservation
./tools/go-modern run ./cmd/check derived-body-repetition
./tools/go-modern run ./cmd/check text-truncation
./tools/generate-check-selection-profiles --paths <os 5 arquivos tocados>
```
Confirme no log do censo que as 2.488 sairam como `jurisprudencia` e que
`area_nao_derivavel` nao apareceu.

### Fase 7 — PUBLICAR PELO DEPLOY, nao pelo `publicar`

```bash
./tools/deploy-publico            # SEM --ressemear: texto novo, re-datacao verdadeira
```
E ele que faz o passo 2.6 (co-citacao) na janela entre republicacao e restart, e
o stop/start que poe as 2.488 rotas no canal de maquina (3.11). Quando o deploy
imprimir `purgando tudo`, **nao purgue de novo** (leia o MOTIVO impresso).

### Fase 8 — PROVA, depois

```bash
./tools/check-http-smoke
./tools/check-paridade-go-nginx
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/jurisprudencia/stj-resp-<n>/
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  http://127.0.0.1:8088/jurisprudencia/stj-resp-<n>/index.md | head -40
./tools/check-derived-authorial-floor          # agora ELE OLHA a familia
./tools/check-csp-style-hashes
```
A gemea `.md` e a prova de que o 3.11 foi resolvido: 200 e corpo, nao 404.

### Fase 7b — COMMITAR OS DERIVADOS DA TRANSACAO (a fase que faltava)

A Fase 7 reescreve artefatos RASTREADOS que ninguem commita. Este e o mecanismo
que o P1b nomeia: `published_manifest.jsonl` esta `M` ha 5 dias, e e dele que o
gerador de estreia derivaria a data. Cada caminho, exato:

```bash
git add content/pages.json
git add content/legal_cocitation_index.jsonl
git add data/editorial/published_manifest.jsonl
git add data/editorial/stock_manifest.json
git add data/editorial/v2_publication_severity.jsonl
git add data/ops/sitemap_shard_registry.json     # sitemap.RegistryRelPath, salvo em :3699
git commit -F /tmp/msg-derivados.txt -- content data/editorial data/ops
```
`git add` por caminho exato, nunca por diretorio (3.14, consequencia 2).
Confirme com `git status --short` que nao sobrou produto untracked.

**Relacao com o P1b, e ela e assimetrica:** no DIA 1 esta familia e
P1b-neutra — nenhum dos 2.488 intents esta em `first_published_at.json`, o
`publish-v2-direct:3837` cai no fallback `-published-at HOJE`, e HOJE **e** a
data de estreia verdadeira. No DIA 2 o mesmo fallback volta a gravar HOJE para
paginas que estrearam ontem, e a familia entra na conta das 944. Portanto:
**P1b e pre-requisito da SEGUNDA publicacao desta familia, nao da primeira** —
e o `git add data/editorial/published_manifest.jsonl` desta fase e a metade do
conserto do P1b que esta travessia pode entregar de graca.

### Fase 7c — REGISTRAR NO RUNNER (depois de a familia existir em HEAD)

```bash
# tools/run-daily-content:373
[stj - acordao]="./cmd/generate-acordao-pages -limite ${WIKI_LIMITE_STJ_ACORDAO:-200}"
git add tools/run-daily-content
git commit -F /tmp/msg-runner.txt -- tools/run-daily-content
```
Depois da Fase 5, e nao antes: com o shard ja em HEAD, `shardpreserve` passa a
funcionar de verdade (3.1) e a onda ACRESCENTA 200/dia em vez de fazer a
estreia por conta propria com 200 (3.14, consequencia 1).

### Fase 9 — o que NAO fazer

- `--ressemear` nesta passada (so quando muda markup/CSS/atributo sem texto).
- purga ampla manual: nenhum script inline nem malha de links mudou.
- `cmd/check` sem argumento.
- `git add` por diretorio.

---

## 6. `page_type`: DECIDIDO — `julgado`

O gerador declara `verbete` -> canonical `wiki`
(`content.go:314`). O irmao STF, que publica o MESMO objeto (um julgado),
declara `julgado` -> `jurisprudencia` (`content.go:328`). Medido: nenhum
acoplamento estrutural entre area e tipo em `internal/render` ou
`internal/seo`, e os dois caem fora de `allowed_page_types`
(`content/legal_marketing_policy.json` = `["artigo","pergunta"]`), entao o CTA
fica desligado pelos dois caminhos. A consequencia de manter `verbete` e de
MEDICAO e de exatidao editorial, nao de quebra: a dimensao `tipo` da
`<meta name="wj-pagina">` chamaria 2.488 acordaos de verbete de referencia.
Trocar para `julgado` nao muda o piso/teto de palavras (constantes proprias do
gerador) — e portanto nao muda quantas paginas passam.

**DECISAO: `julgado`.** A evidencia fecha sozinha e nao ha por que devolve-la:
`stf-informativo-derivado-01` publica o MESMO objeto (um julgado) como
`page_type: "julgado"` em **60 de 60** registros, na MESMA area
`jurisprudencia`, e passa por todos os gates hoje. Chamar um acordao de
`verbete` de referencia e afirmacao editorial errada numa pagina assinada por
advogado, e corrompe a dimensao `tipo` da medicao por agente.

Custo: **zero paginas**. Piso/teto de palavras sao constantes proprias do
gerador (main.go:82-83), independentes do `page_type`. Unico efeito colateral:
`main_test.go:110` e `:540` citam "a banda do verbete" em mensagem de erro —
texto de diagnostico a ajustar, nao logica.

---

## O que o advisor mudou

Cinco coisas, e quatro viraram medicao nova:

1. **Mandou procurar guarda de epoca/frescor no PUBLICADOR, nao so no censo** —
   a armadilha do "fingerprint mismatch" que custou 31 dias. Eu tinha fechado o
   assunto com os `.get()` default do censo, que e um programa diferente. Medido
   depois: **zero ocorrencias** de `stockmanifest|epoch|freshness|fingerprint|
   lease` validando em `cmd/publish-v2-direct` e em `internal/v2publish`, e
   nenhum passo de regeneracao de estoque entre `2. gerar` e `6. censo` nas 8
   etapas da onda. Virou a secao **3.15**: a afirmacao "a cadeia de 9 artefatos
   nao se aplica" passou de inferencia a medicao.

2. **Perguntou como a onda encena arquivo NOVO (`??`, nao ` M`)** — eu nao tinha
   olhado. Medido: `run-daily-content:614,631` usam
   `git ls-files --others --exclude-standard`, o teste exato de untracked, e a
   onda commita **por diretorio**. Isso derrubou uma hipotese de risco (produto
   nao fica untracked) **e criou duas consequencias que mudaram o plano**: a
   edicao do runner saiu da Fase 1 para a **Fase 7c**, e as Fases 3-5 ganharam
   janela proibida com os horarios medidos dos timers (04:31:33 / 04:47:17 /
   12:20:55). Virou a secao **3.14**.

3. **Apontou que a sequencia terminava sem commitar os derivados da transacao**,
   e ligou isso ao P1b. Virou a **Fase 7b** com os 6 caminhos exatos — incluindo
   `data/ops/sitemap_shard_registry.json`, que eu confirmei ser salvo pelo
   publicador (`internal/sitemap` :3699, via `RegistryRelPath` :91) — mais a
   leitura assimetrica que eu nao tinha feito: **P1b e pre-requisito da SEGUNDA
   publicacao desta familia, nao da primeira**, porque no dia 1 o fallback
   `HOJE` acerta a data de estreia.

4. **Mandou fechar a decisao de `page_type`** em vez de devolve-la — "plano com
   'decisao aberta' e passo que quem executa pula". Fechada em `julgado`, com o
   precedente 60/60 e o custo medido (zero paginas).

5. **Recalibrou a classificacao contra a definicao da propria tarefa.** O achado
   B (mapa do gate) nao quebra execucao: **desceu de BLOQUEANTE para GRAVE**. O A
   (`lane`) continua bloqueante, mas eu nao tinha escrito o motivo — consertar
   DEPOIS de publicar muda atributo servido sem mudar texto, o que pela matriz do
   §6 obriga `--ressemear` sobre 2.488 paginas. E marcou como **nao medida** a
   duracao do pre-commit com 2.488 registros (medir exigiria commitar) e como
   **aproximada** a composicao de corpo dos 64,16 us/par.

O que eu **nao** mudei por causa dele: nada. Nenhum ponto conflitou com medicao
que eu ja tinha — os quatro primeiros eram lacuna de cobertura, o quinto era
rotulo.

**Achado que nasceu ao verificar o ponto 4 e que ele nao pediu:**
`main_test.go:124` compara `pagina.Lane != lane` — o campo contra a PROPRIA
CONSTANTE. E tautologia: fica verde para qualquer valor, e por isso a bancada de
1.106 linhas nunca denunciaria `lane = "informativa"`. Entrou como item 4 do
achado A, e e o motivo pelo qual o conserto precisa de um teste que assere o
LITERAL.
