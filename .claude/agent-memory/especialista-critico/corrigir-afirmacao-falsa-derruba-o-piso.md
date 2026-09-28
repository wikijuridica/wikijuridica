---
name: corrigir-afirmacao-falsa-derruba-o-piso
description: Remover uma afirmação falsa do corpo encolhe a página e pode derrubá-la abaixo do piso de palavras — o volume cai e isso se registra, nunca se recupera com texto de enchimento
metadata:
  type: feedback
---

Quando a correção **apaga texto** (superlativo falso, bloco inalcançável, claim não
medido), meça o rendimento ANTES e DEPOIS e **relate a queda como resultado**. É
proibido recuperar o volume reescrevendo prosa para reencher a banda.

**Why:** medido em 2026-09-16 em `cmd/generate-lei-artigo-pages`. O FAQ emitia
"o enunciado que mais aparece é a Súmula X" escolhendo `SumulasNaoProcessuais[0]`
— a ordem *alfabética* da seleção, não a frequência medida. Trocada a régua pela
medida (piso de 3 ocorrências), a pergunta deixou de sair na maioria dos casos e
a passada seca caiu de **93 para 86 páginas**: 6 ficaram abaixo do piso de 350
palavras e 1 passou a colidir no anti-molde. Essas 6 só alcançavam a banda por
causa da frase falsa. Reencher seria trocar fraude de conteúdo por fraude de
volume — e é exatamente o `§1.17 defeito 4` do plano pelo avesso ("escreve texto
próprio demais e depois mata a página por falta de espaço").

**How to apply:** rode a passada seca antes e depois de toda correção que remova
texto do corpo; se o rendimento cair, o número cai no relatório com a causa
nomeada. A queda é evidência de que a correção mordeu, não de que falhou. Vale
para qualquer gerador com banda de palavras ou piso autoral. O par disso é
[[censo-de-detector-orfao]]: régua que ninguém consulta e régua que afirma o que
não mediu são a mesma família — o produtor decidindo sozinho o que o gate decide.
