---
paths:
  - "data/editorial/first_published_at.json"
  - "data/ops/page_content_revision.jsonl"
  - "tools/generate-first-published-at"
  - "tools/generate-*"
  - "cmd/publish-v2-direct/**/*.go"
---

# Campo derivado tem UM produtor — carimba-lo a mao faz a data RETROCEDER

Memoria de origem: `campo-derivado-nao-se-carimba.md`. O `paths:` inclui
`tools/generate-*` de proposito: o caso medido nao foi neste arquivo, foi num
gerador datado qualquer — a licao vale ao escrever QUALQUER gerador que grave
campo de data.

`data/editorial/first_published_at.json` e' gerado por
`tools/generate-first-published-at`, e a fonte declarada no proprio arquivo e' o
**historico git do `published_manifest`** (data do commit, nao `approved_at`).
Escrever aqui a mao cria uma segunda verdade, e a que perde e' a escrita a mao.

O caso irmao, medido em 2026-09-10: um gerador datado escreveu
`content_revised_at` junto com uma mudanca de markup. No diff a data
**retrocedeu** de 2026-09-10 para 2026-09-06, porque o publicador reescreve o
campo com o `revised_on` de `page_content_revision.jsonl` — e esse ledger so
avanca DEPOIS da purga (`deploy-publico:1240`), com defasagem de um ciclo por
desenho declarado.

`check-lastmod-causalidade` reprova o **avanco** sem mudanca de conteudo; o
**retrocesso** passa silencioso. Nao ha gate que apanhe este erro.

## Antes de gravar qualquer campo de data num gerador

```
grep -rn "<campo>" tools/ cmd/ internal/
```

Se houver produtor, **nao escreva**. Deixe o produtor produzir.
Teste de regressao do caso: `test_nao_carimba_content_revised_at`.

Quem le e escreve este arquivo hoje: `tools/generate-first-published-at`
(produtor), `cmd/publish-v2-direct`, `internal/checks/publication_chronology_gate.go`,
`tools/check-cronologia-de-publicacao`, `tools/measure-time-to-first-crawl`,
`tools/generate-crawl-never-requested-refresh` e `tools/check-convite-ao-crawler`.
