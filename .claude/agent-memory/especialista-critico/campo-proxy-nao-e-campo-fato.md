---
name: campo-proxy-nao-e-campo-fato
description: Campo gravado no trap EXIT diz "completa" quando o script morreu por exit 1 direto de gate; e "a cadeia completou" não é o critério para cobrar tentativa de uma peça
metadata:
  type: project
---

Antes de ler um campo de ledger como fato, veja **quem o escreve e em que caminho de saída**.

Medido em `/opt/wiki` (2026-09-16, 17:52): `tools/run-daily-content` grava a linha de evidência
num `trap EXIT` e escrevia `escopo: "completa"` sempre que a variável de escopo estivesse vazia —
que é exatamente o estado de um `registra "<falha>"; exit 1` disparado por gate no meio da cadeia.
Resultado: o consumidor (`tools/publicar-estoque`) imprimia `cadeia completou: sim` para uma
cadeia parada na etapa 4/9, e quem leu o journal concluiu que o alerta era falso quando ele era
verdadeiro.

**Why:** o campo era um *proxy* ("nada marcou escopo especial, então deve ter completado"), não um
fato ("cheguei ao fim"). Proxy é verdadeiro no caminho felizes e mente no caminho de abort.

**How to apply:**
- Fato positivo se marca no ponto onde ele acontece: variável setada **depois** da última etapa, e
  o produtor só grava `completa` com ela. Campo separado para "onde parei".
- Para decidir se uma peça **merece a tentativa contada**, o critério é "o produtor dela rodou"
  (etapa de geração concluiu), nunca "a cadeia chegou ao fim": um gate global que para a cadeia
  depois da geração congelaria a contagem para sempre — laço silencioso — e uma parada antes da
  geração puniria a peça por culpa alheia.
- Ao dividir um rótulo de pendência em duas causas, discrimine pelo **artefato** (o identificador
  aparece ou não no estoque), nunca replicando a regra de nomeação do produtor: isso vira a
  terceira cópia da mesma régua. Relacionado: [[commit-por-pathspec-leva-o-d-do-vizinho]],
  [[ajudante-ausente-deixa-bancada-verde]].
