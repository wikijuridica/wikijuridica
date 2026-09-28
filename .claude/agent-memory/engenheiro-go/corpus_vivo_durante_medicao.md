---
name: corpus-vivo-durante-medicao
description: data/corpus/jurisprudencia/stj-espelhos cresce enquanto se mede; antes/depois só vale se as duas passadas lerem o mesmo total
metadata:
  type: project
---

O corpus do STJ (`data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl`) é
**escrito ao vivo** pelo coletor. Medido em 2026-09-16: 60.221 registros às 09h36,
66.764 ementas às 10h03, 72.815 às 10h10 e 78.791 às 11h05 — crescimento de 30%
em 90 minutos.

**Why:** a frente P1 destravou a coleta do STJ, e o timer roda junto com o
trabalho de quem está medindo. Toda comparação "antes e depois" feita sobre esse
corpus muda de população entre as duas passadas se elas não forem próximas.

**How to apply:** ao medir um gerador que lê esse corpus, registre o
`corpus: N acórdãos lidos` que a própria passada imprime e só compare passadas
com o MESMO N — foi assim que a paridade de régua do P4 ficou defensável
(60.221 nas duas). Se o N mudou, diga isso no relatório em vez de apresentar a
diferença como efeito da mudança de código. Relacionado:
[[ferramenta-seco-gerador-envelope]].
