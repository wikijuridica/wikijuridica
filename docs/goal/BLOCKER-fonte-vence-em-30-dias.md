# BLOCKER — o gate de frescor de fonte trava o commit de conteúdo, sozinho, com o tempo

Descoberto em 2026-08-12 tentando commitar a correção de **uma** página.

## O sintoma

Qualquer commit que toque `data/editorial/v2_pages/*.jsonl` é recusado pelo hook:

```
check-v2-supersession-integrity: audit materialized Git index: authenticate
writing-semantic successor provenance: semantic resolution
fam-pensao-morte-uniao-estavel-prova official source date is invalid, stale, or
future
fatal: ref updates aborted by hook
```

A página citada **não era a que eu estava editando**. O gate valida o estoque
inteiro, então o defeito de qualquer página bloqueia o commit de qualquer outra.

## A causa

`internal/v2writingsemantic/material.go:16`

```go
const maxOfficialSourceAgeDays = 30
```

e `:197-200`, que reprova quando `verified_at` é anterior a `hoje − 30 dias`.

A fonte da página citada tem `verified_at: "2026-07-10"`. Em 2026-08-12 isso são
**33 dias**. O gate não foi violado por ninguém: **ele venceu sozinho**.

## O alcance, medido

Varredura de `data/editorial/v2_pages/*.jsonl` em 2026-08-12:

| | |
|---|---|
| fontes com `verified_at` | **23.456** |
| vencidas (> 30 dias) | **12.287 (52%)** |
| páginas afetadas | **4.413** |
| distribuição | 20.660 verificadas em 2026-07, 2.796 em 2026-08 |

E **piora todo dia**: as 2.796 de agosto vencem ao longo de setembro. Em poucas
semanas o estoque inteiro estará bloqueado para escrita.

## Por que isto não se resolve afrouxando o número

A tentação é subir os 30 dias. Seria errado pelo motivo certo: o gate existe
para garantir que a citação aponta para endereço vivo e conferido, e trocar o
número por conveniência é exatamente o afrouxamento que o contrato proíbe.

Mas o gate também está calibrado para a coisa errada. A maioria esmagadora das
fontes é **texto de lei consolidado no Planalto** — a Lei 8.213/1991 é a mesma
hoje e há 33 dias. Tratar "lei consolidada" e "notícia de decisão recente" com o
mesmo prazo de validade confunde duas perguntas: *"a URL ainda responde?"* e
*"o conteúdo dela mudou?"*.

## As três saídas, e o custo de cada uma

1. **Re-verificar de fato** (correto, caro): um gerador datado que faz requisição
   real a cada URL, confirma o status e atualiza `verified_at`. São ~12,3 mil
   requisições a órgãos públicos — precisa de throttle sério e de janela
   planejada; o `CLAUDE.md` já registra WAF em `gov.br`. Não é coisa de rodar às
   pressas.
2. **Separar o prazo por tipo de fonte** (correto, exige decisão): lei
   consolidada revalida em intervalo longo; jurisprudência e notícia, em curto.
   Muda a política, então precisa de DEC.
3. **Subir o número** (errado): resolve a tela vermelha e não a pergunta.

## Estado

**Não resolvido, e deliberadamente não contornado.** A correção editorial da
página `trib-simples-distribuicao-lucros-isenta` está aplicada no estoque em
disco e **publicada** (o HTML no ar já reflete), mas
`data/editorial/v2_pages/tributario-03.jsonl` segue **fora do git** por causa
deste hook — trabalho não commitado, que é risco registrado.

Não usei `--no-verify`: o contrato proíbe, e burlar o gate esconderia justamente
o achado que importa aqui.
