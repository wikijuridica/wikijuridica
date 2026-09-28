# Refutação adversarial — "gate estatístico vira sinal, não veredito"

VEREDITO: **CAI.** A tese repousa numa inversão da medição que o próprio
repositório já gravou, no arquivo que o desenho cita para pegar `bandaInicial`.

## O que derruba

1. **cmd/measure-molde-trigrama/main.go:10-21** (medição do repo, 2026-09-09,
   205 páginas de Tema, 20.910 pares): 5-grama máximo **0,5904, ZERO pares**
   acima de 0,70; 3-grama neutralizado máximo **0,7304, CINCO pares**.
   Literal: *"O gate passava; o molde estava lá."*
   E `data/ops/molde_trigrama.jsonl` (ledger, 2 linhas, `shingle:3`):
   **1.070 páginas, 571.915 pares, máximo 0,6627, `pares_acima: 0`.**
   A régua "severa" passa um lote de 1.070 páginas da MESMA família de gerador
   derivado sem marcar nada. Logo 532/1.260 no acórdão não é detector
   descalibrado — é o produtor do acórdão ser mais repetitivo que o de Tema.
   O desenho nunca pergunta por que a mesma régua dá 0% num canal e 42% no outro.

2. **`s_gate` não é régua de nada.** Produção é `internal/quality/quality.go:84`
   `nearDuplicateThreshold = 0.82`; `internal/v2bodyneardup/neardup.go:66-69` se
   autodeclara base e nomeia 0,82 como "o gate de produção";
   `tools/check-derived-authorial-floor:288` fixa 3-grama e **recusa o 5**
   ("3-gramas sobrevivem ao numero intercalado; 5 nao");
   `internal/contract/authorial/authorial_mass_content_expansion_refinement_test.go:128`
   fixa **4-grama @0,70 por teste**. São quatro réguas. `s_residual` seria a quinta.

3. **main_test.go:261-279** `TestAntiMoldeRecusaIrmaQuaseIdentica` prende
   exatamente a régua que o desenho trocaria (controle positivo = mesma página,
   dígitos trocados; comentário :272-274). Sob T1 essa página publica como MÉDIO.

## Correção determinística que a ordem do dono de fato pede

`corpoDaPagina` (:2153, usado em :294/:711/:795) inclui os 7 headings
interpolados. `v2bodyneardup.AssembleBody` (:153-175) **exclui headings de
propósito** e é a especificação de corpo da produção. Trocar a composição por
essa é a emenda mínima, já justificada por comentário no repo, sem LLM, sem
máscara, sem fila, sem bandas. **Não está medido que ela mova os 532** — é a
primeira coisa a medir. Se o molde persistir, o defeito é `perguntas()`
(:1990-2046) e os construtores de seção, e o conserto é no produtor (CLAUDE.md §5).

Instrumentação salvável de graça: gravar `(intent_id, s_hoje, vizinho, score)`
do jaccard que o laço **já calcula**, em JSONL de `data/ops/`, fora de `-seco`.
