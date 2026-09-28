# Legenda dos vereditos de auditoria humana (`REPROVADA:N`)

Os arquivos de auditoria deste repositório reprovam páginas com um código
numérico — `REPROVADA:3`, `REPROVADA:1,5` — e **a legenda não existia em lugar
nenhum**. O censo de severidade lê o rótulo e marca a página como crítica; quem
fosse recuperar as 133 páginas reprovadas não tinha como saber o que consertar.

Reconstruída em 2026-08-06 a partir das justificativas em texto que sobreviveram
soltas, principalmente em `.agents/runtime/tmp_rescue/20260806/tmp/final37.py` e
nos arquivos de veredito de lote. Cada linha abaixo traz o exemplo literal que
sustenta a definição — nenhuma é suposição.

| código | defeito | exemplo literal do próprio acervo |
|---|---|---|
| **1** | erro de língua portuguesa — concordância, vírgula solta, frase truncada | *"abertura com erro de concordância 'Já são a terceira ou quarta vez'"*; *"vírgula solta antes do parêntese"* |
| **2** | abreviação corrompida | *"Abreviação corrompida: 'O artigo. 1.614 do Código Civil confirma…'"* — o ponto depois de "artigo" |
| **3** | repetição de conteúdo entre seções | *"seção 3 e seção 5 repetem o mesmo conteúdo (transacional x marketing)"* |
| **4** | auto-referência editorial no corpo visível | *"Esta página não deve ser usada como atalho…"*; *"A página é informativa e não promete reconhecimento"* |
| **5** | **erro de citação legal** — dispositivo trocado ou numeração errada | *"O que o artigo 560 do CPC exige para a reintegração — rol e conteúdo são do art. 561"*; *"'art. 1723 do Código Civil' (sem separador de milhar)"* |
| **6** | erro de enquadramento jurídico | aparece sempre combinado (`5,6`); o caso lido discutia a aplicação do art. 14 do CDC a serviço gratuito |
| **8**, **11** | **sem justificativa localizada** | não confie: leia a página antes de agir |

## Como usar isto

**O código 5 é o mais grave e o mais frequente** (61 ocorrências). É erro de
citação legal — a classe que engana o leitor sobre o próprio direito. O exemplo
canônico é uma página que atribuía ao art. 560 do CPC um rol probatório que é do
art. 561.

**Os códigos 1, 2 e 3 são de forma**, não de conteúdo jurídico: corrigíveis por
gerador datado, com teste de falso positivo. O 2 e parte do 5 (numeração) já
foram corrigidos — ver `tools/generate-v2-separador-milhar-citacao-20260806`.

**O código 4 é sutil e vale explicar**: o texto não pode falar de si mesmo. "Esta
página é informativa" quebra a ilusão de conteúdo editorial e, pior, costuma
aparecer como muleta para desqualificar a própria afirmação anterior.

## O que ainda falta

Das 133 páginas reprovadas, **só 12 têm padrão mecânico detectável**. As outras
121 precisam de leitura jurídica caso a caso — o código diz a CLASSE do defeito,
não o trecho.

E há um problema de fluxo que precisa de decisão: **corrigir o texto não
desfaz o veredito**. O censo lê os arquivos de auditoria, não o conteúdo atual.
Uma página corrigida continua marcada `REPROVADA` até que exista um registro de
re-auditoria — e, se alguém apenas acrescentar um `APROVADA`, o resultado é
`veredito_conflitante`, que também é crítico.

O caminho honesto é um registro de **reparo verificado** que cite o veredito
original, o defeito apontado e a correção aplicada com evidência, permitindo ao
censo tratar o veredito antigo como superado. Isso ainda não existe.

## O que os reparos verificados revelaram sobre o código 5 (2026-08-20)

Quatro reparos foram registrados até esta data, e as quatro classes de defeito
são **diferentes entre si** — o que diz mais sobre o acervo do que a legenda
sozinha:

| # | intent | veredito | classe real do defeito |
|---|---|---|---|
| 1 | `fam-uniao-homoafetiva` | `REPROVADA:5` | artefato de formatação: `art. 1723` sem separador de milhar |
| 2 | `imob-juros-multa-cota-atrasada` | `REPROVADA:5` | idem, `artigo 1336, §1º` |
| 3 | `banc-consignado-clt-como-funciona` | `REPROVADA:5` | **afirmação de percentual em subtítulo sem lastro no corpo** |
| 4 | `proc-titulo-regularizar` | `REPROVADA:4` | **afirmação no presente ancorada em data que envelhece sozinha** |

**A leitura que importa:** o código 5 foi tratado até aqui como se fosse sempre
formatação — e a ferramenta de reparo em massa que existe
(`generate-v2-separador-milhar-citacao-20260806`) só resolve esse subtipo. Os
casos 3 e 4 mostram que o mesmo código cobre defeitos de natureza distinta, que
**nenhum reparo mecânico alcança**:

- o **caso 3** é um subtítulo afirmando "O limite de 40%" enquanto o corpo se
  recusa a cravar percentual, por saber que o teto do consignado mudou. Quem só
  passa os olhos nos subtítulos sai com um número que a página não sustenta;
- o **caso 4** é uma frase no presente ancorada num dia ("Em 11 de julho de
  2026, o cadastro eleitoral está fechado"). Verdadeira quando escrita, e falsa
  por conta própria em 3 de novembro, quando o cadastro reabre — sem gate
  nenhum acusando.

**Consequência prática:** as 121 páginas reprovadas que "precisam de leitura
jurídica caso a caso" não são um resíduo homogêneo à espera de um script melhor.
Cada uma pode ser uma classe diferente, e o código diz a CLASSE do defeito, não
o trecho — nem o tipo de conserto que ele exige.

**Regra que fica:** todo reparo verificado registra a classe real do defeito em
`defect_class`, e não apenas o código. `tools/check-verified-repair` reavalia o
predicado de cada um; reparo cujo defeito voltou deixa de valer sozinho, e a
onda diária confere isso antes de qualquer commit.

