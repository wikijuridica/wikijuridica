---
name: snapshot-de-medicao-completo
description: Raiz de snapshot para medição comparativa tem de conter TODA entrada que o binário lê — faltar uma derruba o número sem erro nenhum
metadata:
  type: feedback
---

Antes de medir sobre uma raiz de snapshot (`-raiz /tmp/...`), derive as entradas
do próprio binário — `grep -n "filepath.Join(raiz" <main.go>` — e copie **todas**.
Entrada ausente não dá erro: dá um número menor.

**Why:** em 2026-09-16, no P6a, montei a raiz com corpus + `legal-corpus` +
`editorial` e esqueci `data/ai/dispositivos_promovidos.jsonl`.
`stjacordaos.CarregaSobreposicao` trata arquivo ausente como sobreposição vazia
**por desenho** (corpus sem promoção é estado legítimo), então as 35.151
promoções do cérebro sumiram em silêncio: candidatos **7.591 → 4.116** e
`sem_ancora_legal_substantiva` **3.961 → 7.462**. A passada rodou 165 s, saiu
exit 0 e o relatório parecia perfeito. Quase virou "o gerador regrediu".

**How to apply:** vale para qualquer `-raiz`/`--root` de ensaio. Três passos:
(1) liste os `filepath.Join(raiz, ...)` e os `*Glob` do fonte; (2) copie o que é
dado vivo e faça symlink só do que é imutável e grande; (3) compare um número
conhecido da raiz real contra a de snapshot **antes** de confiar na série — se
divergir, é o snapshot, não o código. Symlink para diretório de produção dentro
da raiz de rascunho só sobrevive enquanto a execução for `-seco`: apague-o assim
que a medição terminar. Ver [[medir-com-a-regua-do-pacote]].
