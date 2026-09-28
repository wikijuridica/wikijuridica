---
name: purgar-e-aquecer-borda
description: Use antes de purgar ou aquecer o cache de borda — a purga errada custa ~870 s de aquecimento e deixa o acervo velho por 7 dias.
---

# Purgar e aquecer a borda

## Primeiro: leia o ledger

```
tail -3 data/ops/edge_cache_purge.jsonl
```

Se o deploy já gravou `scope: "tudo"`, **purgar de novo joga fora ~870 s de
aquecimento** e deixa a borda em `MISS`. Quando o `deploy-publico` imprime
`purgando tudo`, não purgue de novo — mas **leia o MOTIVO impresso**:
*"registro de revisao indisponivel"* já foi mentira (em 2026-09-08 era
`--purge-targets` caindo no teto de churn com exit 1). Antes de purgar à mão,
rode o comando do passo e leia o **exit real**.

## Quando a purga ampla é obrigatória

Mudou **script inline** ou a **malha de links / bloco de relacionados**:
`--purge-targets` deriva de hash **neutralizado** e devolve **zero rotas**, então
a borda serviria o acervo velho por 7 dias (`s-maxage=604800`).

```
./tools/purge-edge-cache          # purga ampla manual
./tools/warm-edge-cache --rps 12  # EM SEGUIDA, sempre
```

O timer de aquecimento só passa às **04:20 e 16:20 UTC** — sem o aquecimento
manual a borda fica fria até lá.

## A ordem importa

Purgar a borda **antes** de invalidar e aquecer a origem repopula o Tiered Cache
com o conteúdo **VELHO**. Medido em 2026-09-05: `HIT`, `age: 0`, campos = 0,
cinco vezes seguidas. A ordem é binário → socket → serviço → **invalidar
origem** → **purgar borda**.

`tools/warm-origin-cache` enche o `proxy_cache wj_dyn`; sem ele o `use_stale`
não tem o que servir quando o Go cai.

## Depois

Borda fria em `edge_cache_coverage` é **esperado**, não defeito. `HIT` **não
renova TTL**: o acervo expira junto e há janela fria diária.

A purga ampla é segura porque cada resposta cacheada carrega a própria CSP —
página velha vem com hash velho e funciona.

Mexer no script inline muda o HTML de todas as páginas e a publicação seguinte
zera mtime e ETag de tudo; os bots que revalidam rebaixam o acervo junto. Agrupe
mudanças de script numa publicação só e meça depois com
`tools/check-efeito-nos-bots`.
