# Investigação: quatro gates do `cmd/generate-acordao-pages` (2026-09-15)

MODO SOMENTE LEITURA. Nada gravado em `data/` nem em `content/`.
Baseline `git status --short data/ content/` = sha256 `11ecba7b4d0830f11ee11105c3d2bc4d370c6cf24ffa4f028af128f4ec5e4d0e` (158 linhas).
Scratch de medição fora do repo: `/tmp/wj-gates/`.

## Medição autoritativa (binário, passada COMPLETA)

`-seco` confirmado read-only em `executar` (main.go:206-225): `relata` +
`imprimeAmostra` e `return nil` ANTES de `gravaPortfolio`/`gravaShard`.
Corrida `-seco -limite 5000`, EXIT=0, `/tmp/acordao-medicao/l5000.out`:

```
corpus: 60221 lidos, 4763 candidatos
páginas montadas: 2488       <-- limite 5000 não atingido: passada COMPLETA
  corpo:   min 487 mediana 681 max 700   (banda 350-700)
  autoral: min 355 mediana 525 max 632   (piso do gate: 250)
  citado:  min 42  mediana 151 max 292   (mínimo oficial: 25)
recusas: agravo 49807 · ementa_curta 4500 · molde 1405 · sem_ancora 1151
         · ementa_sem_item_transcritivel 682 · citacao_min 165
         · camada_autoral_sem_espaco 22 · rota_duplicada 1
```
57.733 + 2.488 = 60.221. Contabilidade fecha.
**2.488 páginas já montáveis hoje** — o gerador só grava `-limite` por execução (default 30).

Replicação Python validada contra o binário em SEIS totais de controle, todos
exatos: 60.221 · 4.763 · 49.807 · 4.500 · 1.151 · **682**.

## ITEM 2 (prioridade 1) — piso de 250 na grandeza errada

- `main.go:402` `pisoEmentaPalavras=250` → EMENTA DE ENTRADA.
- `tools/check-derived-authorial-floor:262` `PISO_AUTORAL=250` → palavras de
  comentário próprio no `<main>` da PÁGINA (`corpo_editorial`, :313-316).
- `main.go:2176` `corpoAutoral(p)` = corpo inteiro MENOS o que está entre aspas
  curvas ⇒ a camada autoral é construída de METADADO (órgão, relator, URNs,
  súmulas, precedentes, contagens do acervo, FAQ), não da ementa.
  Único texto autoral dependente da ementa: `quantidadeDeItens` (~3 palavras) e
  a frase de `assunto` (~10-15), esta derivada do CABEÇALHO em versal, que a
  ementa curta também tem.
- O que a ementa precisa entregar de verdade: `minimoCitacaoOficial=25` (:1655).

**Números medidos sobre os 4.500 barrados:**
| corte | N |
|---|---|
| têm âncora substantiva (passam o OUTRO corte de `elegivel`) | **2.477** |
| + citação ≥ 25 palavras, regra de item ATUAL | 1.930 |
| + citação ≥ 25 palavras, regra de item CORRIGIDA | **2.426** |
| peso de evidência ≥ mínimo dos 4.763 candidatos aceitos | 2.477 de 2.477 |
| peso ≥ p25 dos candidatos | 1.542 |
Palavras da ementa nos 4.500: min 1 · p25 117 · mediana 161 · p75 202 · max 249.
Citação disponível nos curtos com âncora (regra corrigida): mediana 135, máx 234.

**A PROVA DE QUE OS PISOS DE SAÍDA NÃO MORDEM**: na passada completa sobre os
4.763 candidatos — de peso 3 (o mínimo) ao máximo — os cortes de saída
`corpo_abaixo_da_banda_do_verbete` (:1679), `comentario_proprio_abaixo_do_piso`
(:1682), `sem_duas_fontes_oficiais_verificaveis`, `title_fora_da_faixa_de_seo`,
`meta_description_fora_da_faixa` e `fragmento_terminal_em_campo_visivel`
dispararam **ZERO vezes**. Nenhum deles aparece na lista de recusas.

BRUTO ≠ LÍQUIDO: os 2.477 ainda enfrentam `molde_acima_do_limiar`, que na
passada medida recusou 1.405 de 3.893 que o alcançaram (36,1%). Os curtos têm
citação menor (mediana 135 vs 151) e peso menor (p25 3 vs 6), então tendem a
sair pior, não melhor. **Líquido estimado ~1.500-1.600** (ESTIMATIVA); o número
exato só sai do binário com a constante trocada.

## ITEM 1 — regex de itens: 682, e 0 de 682 são ementa ruim

`reItemDeEmenta = (?m)^[ \t]*\d{1,2}\s*\.\s` (main.go:1106) exige marcador
**no início de linha**, com **ponto**, seguido de **espaço**.
- 682 de 682 têm `\n`; largura máxima de linha mediana 68 (a fonte quebra em ~65).
- 667 de 682 têm marcador `N. ` em ALGUMA posição — só não no início de linha.
- **0 de 682 estão sem marcador numerado em forma alguma.**

Forma real do marcador nos 682:
| forma | N | % |
|---|---|---|
| meio de linha, depois de espaço (quebra da fonte caiu no lugar errado) | 368 | 54,0% |
| ponto sem espaço no início de linha (`1.Não há violação…`) | 186 | 27,3% |
| hífen no início de linha (`1- Recurso especial…`) | 99 | 14,5% |
| colado na pontuação anterior (`DESPROVIDO.1. A controvérsia…`) | 18 | 2,6% |
| outras | 11 | 1,6% |

Taxa por arquivo de origem — o gate mede a QUEBRA DE LINHA do coletor:
`registros-2025-11` 74,3% · `2025-12` 32,8% · `2026-03` 18,8% · `2026-04` 0,6%
· `2026-06` 0,3% · `2026-07` 0,0% · `2026-08` 0,0%.
344 de 682 são a ementa ESTRUTURADA do STJ ("I. Caso em exame", "II. Questão em
discussão"), cujo cabeçalho romano gruda no item 1. 570 de 682 são páginas que a
IA local destravou.

**25 de 25 amostradas por stride são ementas legítimas, bem formadas e
substantivas. 0 de 25 inaproveitáveis.**

Regra substituta medida (sequência consecutiva 1,2,3…, separador ponto OU hífen,
com ou sem espaço, fronteira à direita que não seja dígito):
**675 de 682 recuperados** com corrida ≥ 25 palavras (mediana 332).

REGRESSÃO MEDIDA sobre os 4.079 candidatos que HOJE funcionam: a regra nova
sozinha **quebra 29** (0,71%) — ementas cuja numeração não começa em "1".
Logo ela NÃO substitui: entra como FALLBACK (ou escolhe-se a maior das duas
corridas). Nessa forma: 675 recuperados, **0 regressões por construção**, e
ainda 107 dos 4.079 ganham citação MAIOR (3.937 idênticas, 35 menores).

PROVENIÊNCIA DO 250: nasceu num único commit, `45d33ee8` (2026-09-10, cinco
dias atrás), nunca revisado. O comentário :400-402 diz o critério real —
"com 250 palavras sobram 1.674 candidatos" — ou seja, foi calibrado para o
TAMANHO DO POOL, não por necessidade da máquina.

## ITEM 4 — listas de admissibilidade nunca veem os 49.807

`elegivel:515-517` retorna em `procedimental` na PRIMEIRA linha;
`dispositivosSubstantivos`/`sumulasSubstantivas` só rodam em :538-539, :550,
:1735, :1894, :2020 — todos depois do return ou dentro de `montaPagina`.
Nenhum outro call site em `cmd/ internal/ tools/`.
Cobertura das listas sobre os 60.221: 18.889 com URN de admissibilidade,
34.662 com súmula processual, 41.006 com qualquer dos dois.
Agravos/embargos com ementa ≥ 250 palavras: **17.616**. Sobre eles:

| sinal | N | % |
|---|---|---|
| LISTAS (súmula processual ou art. de admissibilidade em campo estruturado) | 14.757 | 83,8% |
| TEXTO da ementa acusa óbice (detector de prosa, meu) | 14.047 | 79,7% |
| união (descartáveis por óbice) | **15.746** | 89,4% |
| sem nenhum sinal de óbice | 1.870 | 10,6% |
| ... destes, com âncora substantiva | 1.388 | 7,9% |

RESSALVA MEDIDA: amostra por stride de 8 dos 1.388 — **5 de 8 ainda carregam
óbice que meu detector de prosa não pegou** ("SÚMULAS Nºs 5 E 7/STJ" no plural,
"PREQUESTIONAMENTO. IMPRESCINDIBILIDADE", "FALTA DE PROCURAÇÃO",
"representação processual"). Só 3 de 8 são mérito de fato. O resíduo real de
mérito é materialmente menor que 1.388 — ordem de poucas centenas (ESTIMATIVA
de amostra de 8, não população).

## Prova de não-mutação
`git status --short data/ content/` antes e depois: sha256 idêntico
`11ecba7b4d0830f11ee11105c3d2bc4d370c6cf24ffa4f028af128f4ec5e4d0e`, diff vazio.

## ITEM 3 — a fila: alegação refutada

`v2_rewrite_queue.jsonl`: 3.201 linhas, TODAS `queued_at` 2026-09-11 (HEAD:
3.200, todas 2026-09-10). Artefato REGENERADO por inteiro a cada ingest
(`reconcileRewriteQueue`, v2ingest.go:934) — a data é a da última regeneração.
Severidade: 10.337 médio / 769 limpo / 100 crítico.
**Médios esperando publicação: ZERO — os 10.337 já estão no ar.**
Fila ∩ publicados: 3.101 de 3.201 são páginas VIVAS com defeito nomeado.
Produtor: `internal/v2ingest`. Leitores: `generate-v2-publication-severity`
(classificador) + 2 gates de sitemap. **Nenhum consumidor reescreve página.**
55 timers `wikijuridica-*`; nenhum de ingest, reescrita ou refino.
