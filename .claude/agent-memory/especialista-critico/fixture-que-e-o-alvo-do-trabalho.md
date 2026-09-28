---
name: fixture-que-e-o-alvo-do-trabalho
description: Teste que copia do disco vivo o mesmo arquivo que a correção vai mudar passa a medir a si mesmo depois do primeiro --aplicar; use o registro preservado, conferido por CAS
metadata:
  type: feedback
---

Teste de ferramenta de reparo **não pode montar o fixture copiando o arquivo
vivo que o reparo altera**. Congele o estado anterior e confira-o contra o hash
que o plano da ferramenta declara.

**Why:** medido em 2026-09-16. A bancada do
`generate-v2-letra-solta-na-abertura-repair-20260916` copiava
`data/editorial/v2_pages/*.jsonl` para uma raiz temporária e passava 12/12. No
instante em que rodei `--aplicar` no estoque real, 7 dos 12 viraram "já
reparado": o fixture tinha virado o estado FINAL, e os testes deixaram de medir
o reparo sem ficarem vermelhos. Verde que some de significado é pior que
vermelho.

**How to apply:** o próprio gerador já preserva o registro anterior em
`.agents/runtime/<nome>/<data>/` (a regra de `v2-pages` exige) — use esse
arquivo como fixture da linha alvo e **falhe o teste** se o sha256 dele não for
o `linha_sha256_antes` do plano. As linhas IRMÃS podem vir do disco vivo (são o
controle real de "não toquei em mais nada"), mas afirme N de M com piso, nunca
um número chumbado como "29". Mesmo cuidado em qualquer teste que leia
`data/editorial/`, `content/pages.json` ou `public/`. Ver
[[metodo-payload-de-gerador-datado]].
