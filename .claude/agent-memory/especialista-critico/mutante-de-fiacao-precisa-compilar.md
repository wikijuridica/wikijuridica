---
name: mutante-de-fiacao-precisa-compilar
description: Mutar só o ponto de chamada costuma não compilar (variável resolvida fica sem uso) e isso ISENTA a asserção de fiação da prova; mute a regressão inteira
metadata:
  type: feedback
---

Para provar por mutação uma asserção de **fiação** (o chamador usa o valor
derivado, não o cru), mutar só a linha da chamada normalmente **não compila** —
a variável resolvida vira `declared and not used`. Mutante que não compila não
conta, então a asserção fica **sem prova** e você não percebe: o relatório
mostra três mutantes mortos e um "não compila", que parece detalhe.

O mutante certo é a **regressão realista inteira**: remova também o bloco que
produz o valor (`x, err := resolve(...)` + o `if err != nil`) e reverta a
chamada. Aí compila, e a asserção de fiação morre ou sobrevive de verdade.

**Why:** medido em 2026-09-16 em `cmd/cerebro/comentarios.go` — trocar
`hostDoCabecalho` por `*host` na chamada deu `declared and not used`; removendo
junto o bloco de resolução, compilou e o teste de fiação ficou vermelho, que é
a prova. Sem isso eu teria entregue uma asserção não provada junto de três
provadas, e é a não provada que segura a regressão silenciosa (ali, cabeçalho
`Host` vazio, que não quebra build nenhum).

**How to apply:** ao montar a tabela de mutantes, classifique cada um em
`morreu` / `sobreviveu` / `não compila`, e trate **`não compila` como trabalho
pendente**, nunca como linha da tabela. Para cada asserção que só um mutante
não-compilável atingia, escreva o mutante realista. Vale para qualquer par
"função nova + ponto de chamada trocado". Relacionado:
[[metodo-payload-de-gerador-datado]].
