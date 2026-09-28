# Varredura: pisos e tetos numéricos que barram conteúdo (somente leitura)

Sessão 2026-09-15. Todas as medições abaixo são próprias, reproduzíveis, e a
replicação em Python foi validada por controle positivo contra o Go
(60.221 lidos / 49.807 agravo / 4.500 ementa curta / 1.151 sem âncora / 4.763
candidatos — batem exatamente com `-seco`).

## Fato estrutural

`data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` NÃO EXISTE. O gerador
tem UM commit (`45d33ee8`, 2026-09-10) e nunca gravou nada. 0 de 4.763
candidatos no disco.

## O que de fato decide publicação hoje (medido em v2_publication_severity.jsonl, 11.206 linhas)

- severidade: 10.337 médio, 100 crítico, 769 limpo. Publica: 11.106; não publica: 100.
- ÚNICO motivo crítico vivo: `intencao_pulada_deliberadamente` (100).
- `corpo_entre_250_e_400_palavras`: 1.695 páginas — MÉDIO, publicam.
- `batch_global_similarity_refutado_por_medicao`: 5.600 — o gate de similaridade
  global já foi refutado por medição em 5.600 páginas e elas publicaram.
- `fonte_insuficiente` (<2 fontes): 2.323 — MÉDIO, publicam. `sem_fonte_oficial`: 100.
- Nenhum piso/teto numérico bloqueia publicação hoje.

## Régua contra régua

| constante | local | valor | gate que decide | divergência |
|---|---|---|---|---|
| tetoPalavras | acordao:83 / lei-artigo:64 | 700 duro | v2ingest band 350–700 com ±10% ⇒ efetivo 315–770 | gerador 10% mais severo no teto |
| pisoPalavras | acordao:82 | 350 duro | efetivo 315 | 11% mais severo |
| tetoCitado | acordao:89 | 0,42 | check-derived-authorial-floor:263 = 0,55 | nunca chega a valer (ver abaixo) |
| pisoAutoral | acordao:92 | 250 | mesmo gate :262 = 250 | alinhado |
| minimoCitacaoOficial | acordao:96 | 25 | mesmo gate :264 = 25 | alinhado |
| limiarMolde/shingleMold | acordao:102-103 | 0,70 / 3-grama com dígito neutralizado | EIXO 3 do gate: 0,70 / 3-grama SEM neutralizar, e a família `stj-acordao-derivado` NÃO está em FAMILIAS_CANAIS_DERIVADOS (:279) | gate não mediria esta família |
| limiarSimilaridade | 5 irmãos | 0,60 / 3-grama, dígitos PRESERVADOS | — | confirmado |

## Orçamento em montaPagina (acordao :1633-1661) — CONFIRMADO

base = corpo autoral + FAQ + headings, montado ANTES da citação.
orcamento = min(700 − base, 294).

Medido em `-seco -limite 500` (500 páginas montadas de 1.260 iteradas):
- corpo: min 588 mediana 683 max 700
- autoral: min 409 mediana 556 max 632 (piso 250)
- citado: min 42 mediana 116 max 284 (mínimo 25)

Como o menor autoral aceito é 409 e 700−406=294, **o teto 0,42 nunca foi o
limitante em nenhuma das 500 páginas**: o limitante foi sempre 700 − base.
A camada autoral mediana é 2,2× o piso que precisa cumprir, e come 556 das 700
palavras; sobram ~144 para o texto oficial, contra uma corrida transcritível de
mediana 371 palavras (medida no corpus).

Recusas de montaPagina: molde 532, citacao_abaixo_do_minimo 123,
ementa_sem_item_transcritivel 84, camada_autoral_nao_deixa_espaco 21.
As 144 (123+21) são a cauda em que base passou de ~625.

## Piso de ementa (acordao:402, pisoEmentaPalavras = 250)

Barra 4.500 registros hoje. Destes, **2.477 têm âncora legal substantiva** (com
a sobreposição do cérebro aplicada) — ou seja, 2.477 acórdãos elegíveis em tudo
menos no tamanho da ementa, contra 4.763 candidatos atuais (+52%).
Distribuição das 2.477: min 21, p25 134, mediana 175, p75 212, p90 234, max 249.
Liberação por piso: 200 ⇒ +800; 180 ⇒ +1.154; 150 ⇒ +1.646; 100 ⇒ +2.243.

## Teto da citação vs. material disponível (medido nos 4.763 candidatos)

- 682 candidatos sem item transcritível (item 1 já em versal ou sem item numerado).
- corrida transcritível: mediana 371, p75 489, p90 628 palavras.
- 2.852 de 4.081 (69,9%) têm corrida maior que o teto duro de 294 palavras.
- primeiro item: mediana 40 palavras; só 5 de 4.081 passam de 294.

## Pisos dos cinco irmãos (impacto medido nos logs de 2026-09-15)

- `pisoDeItens = 4` (noticia:63): 116 grupos, **58 barrados** (50,0%), 58 montadas, 2 inéditas.
- `pisoDeMunicipios = 6` (diario:81): 126 grupos, **69 barrados** (54,8%), 49 montadas, 0 acrescentadas.
- `pisoDePalavras = 270` (tema:57, sumula:46, stf:56, noticia:65, diario:82): finas = 0 em todos. Barra ZERO hoje.
- `limiarSimilaridade = 0,60`: diarios 8 puladas; stf-informativo 5 puladas; tema 98 irmãos pulados (log 09-10).
- `tetoDeTextoCitado = 0,35` (diario:912-913): máxima observada 13,5%. Não vale hoje.
- `tetoInternoDeCitacao = 0,50` (tema/excertos_comentados.go:126): 2 de 1.074 acima. `tetoDeElisao = 0,53` (:152).
- `tetoDeMunicipiosListados = 40` (diario:104), `tetoDeTeseEmBlocoUnico = 250` (stf:1333), `pisoOcorrencias = 3` (lei-artigo:1557).

## CORREÇÕES APÓS REVISÃO (join correto, pelo portfólio)

O `page_type` que o validador usa é o do PORTFÓLIO (validate.go:605/620), não o do
shard. Join portfolio × severity sobre as 11.106 publicadas:

| page_type | n | mediana | banda nominal | fora do nominal | fora do efetivo |
|---|---|---|---|---|---|
| guia_problema | 3.851 | 719 | 700–1400 | 1.534 abaixo + 12 acima | 12 |
| verbete | 2.516 | 424 | 350–700 | 223 abaixo + 54 acima | 3 |
| pergunta | 2.509 | 480 | 400–800 | 311 abaixo + 82 acima | 10 |
| procedimento | 874 | 568 | 500–1000 | 174 abaixo + 21 acima | 0 |
| tema_repetitivo 1.074, sumula 112, julgado 60, noticia 59, diario-oficial 51 | 1.356 | — | SEM banda | — | — |

**2.411 de 9.750 páginas publicadas com banda (24,7%) estão fora da banda NOMINAL
e dentro da efetiva. Só 25 estão fora da efetiva.** A tolerância de ±10% que o
gerador de acórdão descarta é o que segura um quarto do acervo.

`base == autoral` está PROVADO, não inferido: `blocoEmenta("")` e
`blocoDispositivo("")` (main.go:1829-1839) emitem a MESMA moldura da versão
preenchida, mudando só o texto entre as aspas curvas; e `corpoAutoral`
(:2176-2177) remove exatamente esse span. Logo o teto 0,42 (294 palavras) só
poderia governar página com base < 406, e o menor autoral aceito foi 409.

Distribuição de palavras autorais/FAQ das 123+21 recusadas: **NÃO MEDIDO** — exige
instrumentar `montaPagina`, vedado nesta sessão (somente leitura). Limites
deriváveis: 21 ⇒ base > 675; 123 ⇒ 25 ≤ orçamento < tamanho da 1ª frase do item 1
(mediana do item 1 = 40 palavras) ⇒ base ≈ [650, 675]. Inferência rotulada.
FAQ na página mediana do `-seco` (n=1): 3 itens, 170 palavras de 683 (24,9%),
emitidas pelo template; teto do ingest `maxFAQItems = 4`.

Viés de amostra: as 500/532/123/84/21 vêm de **1.260 candidatos iterados após
`ordenaPorEvidencia`** (os mais ricos em âncora), não dos 4.763. Mais âncora ⇒
`blocoDispositivosLegais` maior ⇒ base maior ⇒ mais recusa por orçamento.

Nem `generate-acordao-pages` nem `generate-lei-artigo-pages` são invocados por
`tools/run-daily-content` (GERADORES, :368-373) ou por unit em `ops/`. Impacto em
produção HOJE = 0. `cmd/ingest-v2-stock` também não está na onda: o caminho vivo
é gerar → check derived-body-repetition + text-truncation → severidade →
publish-v2-direct. Logo `internal/v2ingest/validate.go` não decide publicação.

lei-artigo `-seco -limite 500`: 38 montadas, **184 recusadas por molde** (82,9%
das 222 que chegaram ao detector), 5 por `texto_oficial_nao_cabe_na_banda`.

## Tetos do ingest (v2ingest/validate.go)

- `defaultOfficialSourceMaximum = 5` (current_legal_facts_telecom_energia01.go:470): mas **99 páginas publicadas têm mais de 5 fontes** (até 18).
- `validSources < 2` reprova (:783): mas 2.423 páginas publicadas têm 0 ou 1 fonte.
- `OfficialSourceVerificationMaxAgeDays = 90` (validation_as_of.go:29).
- `duplicatePhraseNgramSize = 12` (:22), `maxLegalCitationSpanWords = 40` (:41),
  `maxFAQItems = 4` (:26), `minDiacriticsRatio = 0,01` (:25),
  `headingReusePercentDivisor = 100` / `headingReuseFloor = 2` (:29-30).
- `wordCountBands` (:56): verbete 350–700, pergunta 400–800, procedimento 500–1000,
  guia_problema 700–1400; page_type fora do mapa reprova no portfólio (:620).
  Mas 1.356 páginas publicadas usam page_type SEM banda (tema_repetitivo 1.074,
  sumula 112, julgado 60, noticia 59, diario-oficial 51).
  Entre as 326 verbete publicadas medidas no shard: 24 acima de 700, 2 acima de 770.

## internal/quality

`nearDuplicateThreshold = 0,82` (:84), `minLexicalDiversity = 0,38` (:85),
`minIndexableWords = 90` (:24), `nearDuplicateStemmedFallbackThreshold = 0,20` (:92),
`repeatedPhraseMechanicalMinRepeat = 3` (:942), `...MinWords = 6` (:946),
`...MaxSpan = 45` (:949), `...DominanceRatio = 0,04` (:952).
`internal/v2bodyneardup`: ShingleSize 5, DefaultThreshold 0,70, QualityThreshold 0,82.
