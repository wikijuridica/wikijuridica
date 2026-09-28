---
name: oraculo-vivo-move-e-o-gate-nao-converge
description: Gate que compara bytes cacheados contra um render VIVO nunca converge se o render tem bloco derivado do acervo; meça quanto o oráculo se moveu antes de culpar a purga
metadata:
  type: feedback
---

Antes de tratar "cache velho" como falha de purga, **meça se o oráculo se moveu**:
releia o alvo de comparação e confronte com o valor que o próprio ledger gravou
horas antes.

**Why:** medido em 2026-09-16, as 6 rotas da janela do `check-edge-frescor`
tinham `sha_go` DIFERENTE do `sha_esperado` que o ledger gravara 9 h antes —
6 de 6. O diff de `/diarios/rs-20260914/index.md` ficou inteiro dentro de
`## Conteúdos relacionados`, que é derivado de um acervo que cresce o dia todo.
O canal HTML do mesmo gate nunca sofre disso porque compara com o **disco**
(oráculo estável, atestado pelo manifesto), e `generate-page-content-revision`
já neutraliza a seção equivalente no HTML para não re-datar o acervo. O gate
irmão tinha a resposta; a gêmea nunca a recebeu.

**How to apply:** o número honesto separa as duas causas em vez de escolher uma.
Na mesma medição, 125 gêmeas velhas na borda tinham só **9** divergindo apenas
no bloco que se move — as outras 116 eram bytes de antes da publicação, defeito
real. Conte o fenômeno num campo próprio (`velhas_so_relacionados`) e **não mude
a definição de velha**: afrouxar a classe para o gate fechar é falso-verde. Se um
dia espelhar o gate irmão, o controle a nomear é "gêmea com uma linha de corpo
alterada continua VELHA" — e o recorte tem de preservar o que vem DEPOIS do
bloco (o JSON de citação e a versão canônica moram no fim do documento).
