# Crítica de completude — o que as três arquiteturas NÃO cobrem

Medição própria, somente leitura, 2026-09-15. Réplica em Python do `elegivel`
de `cmd/generate-acordao-pages/main.go:515-546` **com** a sobreposição do
cérebro (`internal/stjacordaos/writeback.go:70 CarregaSobreposicao`, aplicada
em `main.go:413`). A réplica reproduz os quatro números do `-seco` **exatos**:
49.807 agravo/embargo · 4.500 ementa curta · 1.151 sem âncora · 4.763
candidatos. Réguas: `BodyWords` = `[^\W_]+`; sha256 nos shingles.

## 1. O achado que nenhuma das três produziu: 12.302 páginas boas a mais

`elegivel` roda `procedimental(r.Classe)` (`:516`) **antes** das duas medidas
diretas de "tem tese" — ementa ≥250 (`:532`) e âncora substantiva (`:538`).
Medido: **12.302** registros passam TODOS os outros filtros e morrem só no
`strings.Contains` da sigla (`:316-324`). É **2,58×** o pool inteiro de hoje
(4.763).

| | |
|---|---|
| procedimental + ACÓRDÃO + campos + ementa≥250 + âncora substantiva | **12.302** |
| ementa: mediana / p90 / max (palavras) | 371 / 634 / 1.543 |
| em formato CNJ estruturado ("QUESTÃO EM DISCUSSÃO") | **6.035 (49,1%)** |
| classe `AREsp` pura | 4.881 (3.000 em formato CNJ) |
| "RECURSO ESPECIAL (PARCIALMENTE) PROVIDO" na ementa | 215 |

Sem o overlay do cérebro seriam 2.902; o writeback (35.082 promoções, 58,3% do
corpus) é o que leva a 12.302 — e é o mesmo mecanismo que levou o pool de
mérito de **1.674** (número do commit `45d33ee8`, ainda no comentário
`:399-402`) a 4.763 sem tocar filtro nenhum.

## 2. A justificativa do descarte, e as duas afirmações que a medição derruba

Único lugar onde a exclusão é fundamentada: mensagem de `45d33ee8`.
> "QUEM NAO VIRA PAGINA: os 82,9% de agravo e embargo. O que eles decidem e o
> cabimento do recurso, nao a materia; pagina propria para cada um seria
> doorway (…) Eles entram como evidencia agregada nas paginas de artigo de
> norma, trabalho do gerador irmao `cmd/generate-lei-artigo-pages`."

**(a) "decidem cabimento, não matéria" — falso para 12.302.** A classe é a dos
AUTOS, não da decisão. Evidência primária, medida no corpus (não citação de
lei, que eu não conferi em fonte oficial nesta sessão): **373** dessas ementas
trazem "AGRAVO … CONHECIDO" e **215** trazem "RECURSO ESPECIAL (PARCIALMENTE)
PROVIDO" — o STJ julga o mérito do especial sob a classe do agravo.

**(b) "seria doorway" — refutado por medição.** Stride n=199 de cada pool,
19.701 pares, Jaccard 3-grama da ementa, dígito preservado, pares intra-caso
excluídos:

| pool | mediana | p99 | max | pares ≥0,70 |
|---|---|---|---|---|
| atual (4.763) | 0,0067 | 0,0838 | **0,9836** | **1** |
| agravo/embargo (12.302) | 0,0135 | 0,0930 | **0,4948** | **0** |

O pool recusado é MENOS duplicado que o que já se publica. Intra-caso: 457
pares, mediana 0,107; dos 17 ≥0,70, **16 são da MESMA classe+número** (mesmo
`intentID`, já barrados por `rota_duplicada_no_corpus`, `:286`) e **1 é
cross-classe e sobrevive**: `AgInt nos EDcl no REsp 2004720` ×
`AgInt no REsp 2004720`. Colisão de rota entre os dois pools: **0** (o slug
carrega a classe, `:814-830`).
Precedente do repo que fixa a régua: `docs/goal/MAESTRO_CODEX_LOG.md:4187`
— "Entidade = distinta por construcao (URN LexML unica); doorway so em colisao
de URN".

**(c) "entram como evidência agregada" — a rota existe e joga o mérito fora.**
`cmd/generate-lei-artigo-pages/main.go:164-165`, por escrito: *"Aplicacao é o
que o corpus diz sobre um artigo (…) **Nunca guarda o mérito do julgado**"*. O
índice é por URN (`:483`), então **20.521 dos 49.807 (41,2%)**, sem uma única
URN nem após o overlay — 4.159 deles com ementa ≥250 — contribuem **zero** para
qualquer página. Descartados sem rota.

## 3. Pontos de recusa que NENHUMA das três cobre

| arquivo:linha | o que é | por que importa |
|---|---|---|
| `main.go:516` `procedimental` | recusa 49.807 | o maior de todos; SEVERIDADE o **promove a FATO-impeditivo** |
| `internal/v2ingest/validate.go:1106-1166` `classifyDuplicatePhrases` + `isLegalCitationExempt` | 12-grama idêntico, com isenção por citação ancorada, teto de 40 palavras, guarda anti-hub (red-team Fable 2026-07-22) | **é exatamente o que CAMADAS quer construir e o que CEREBRO quer que um LLM julgue — já existe em Go, determinístico… e NÃO TEM INVOCADOR** |
| `validate.go:450` `heading_reuse_above_global_limit` (teto ~1%, piso 2) | idem, sem invocador | CAMADAS tira heading de todo score sem saber que há gate |
| `validate.go:653/:657/:812` title/meta/diacríticos | idem, sem invocador | SEVERIDADE cita `qualitygate.go` e não vê esta camada |
| `tools/check-derived-authorial-floor:279-287` | família `stj-acordao-derivado` ausente do mapa | gate cego sobre o canal, com o aviso escrito em `:271-278` |
| `tools/check-internal-link-block:321` | doorway Jaccard>0,50 mesma área | baseline já vermelho (5.564→2.104); nenhuma das três |
| `tools/check-writeback-do-cerebro-nao-atrasa` | idade do writeback que alimenta `main.go:413` | é a torneira do pool; nenhuma das três |
| `tools/run-daily-content:368-373` | 5 geradores; o de acórdão não está | **nada invoca o gerador** |

**Verificação decisiva:** `v2ingest.Run` tem UM chamador,
`cmd/ingest-v2-pages/main.go:46`, que por sua vez não é invocado por
`tools/`, `.githooks/` nem `ops/`; `AdjudicateShard` (`adjudicate_shard.go:295`)
tem ZERO chamadores fora do próprio pacote. A onda diária é
gerador → censo (`run-daily-content:640`) → `publish-v2-direct` (`:683`).
Logo `internal/v2ingest/validate.go` **não está na trajetória** — o que explica
`main.go:1861-1862` ("os três shards em produção estouram o mesmo teto").

## 4. Interação perigosa entre as três

CAMADAS §7.1 (terminal só por identidade byte) + SEVERIDADE ("nada morre") +
CEREBRO (veredito que expira publicando) → **nenhum eixo bloqueante de molde
sobrevive**. Com `v2ingest` fora da trajetória e `check-derived-authorial-floor`
cego para a família, resta apenas `internal/quality` a 0,82/5-gramas, que o
próprio pool já satisfaz. O caso concreto que passa: o par cross-classe
`AgInt nos EDcl no REsp 2004720` × `AgInt no REsp 2004720` (Jaccard 3-grama da
ementa ≥0,70, mesmo caso, rotas distintas, sobrevive a `:286`).

## 4-bis. NÃO MEDIDO, declarado

Rendimento de `montaPagina` sobre os 12.302 (`:1554 ementa_sem_item`,
`:1560 sem_duas_fontes` dependem da cobertura de `leManifesto`) — exige passada
`-seco`, vetada nesta sessão. 12.302 é elegibilidade, não páginas prontas.
E 25.139 registros (41,7% do corpus) ainda não têm promoção do cérebro: a fila
é a torneira que resta.

## 5. Próximos passos (trabalho, não relatório)

1. Trocar `procedimental` de recusa de ELEGIBILIDADE por sinal: a régua é
   ementa≥250 + âncora substantiva, que já existe e é o que mede tese.
   Guarda a acrescentar: dedupe por `numero_processo`, não só por intent.
2. Pôr `stj-acordao-derivado` em `FAMILIAS_CANAIS_DERIVADOS` no mesmo commit.
3. Medir `duplicate_phrase` sobre o lote antes de qualquer arquitetura de
   camada — é o gate terminal real.
4. Rota para os 20.521 sem URN e os 4.500 de ementa curta: página agregada por
   dispositivo/tese, não página própria.
