---
name: cadeia-de-pagina-tem-dois-trilhos
description: O ingest NAO esta no caminho da publicacao — recusa no v2ingest nao impede a pagina de ir ao ar; quem decide public/ e o censo + SelectPublishable
metadata:
  type: reference
---

Antes de afirmar por que uma página v2 "não publicou", saiba que
`data/editorial/v2_pages/*.jsonl` alimenta **dois consumidores independentes**:

- **estoque** — `v2ingest` → `authorial_mass_drafts.jsonl` (o que ~20 gates leem)
- **publicação** — censo de severidade → `v2publish.SelectPublishable` → `public/`

`cmd/publish-v2-direct` e `internal/v2publish` **não importam** `internal/v2ingest`.
Logo, recusa do ingest **não** impede publicação — ela só mantém a página fora do
estoque canônico. Medido em 2026-09-16: 7.982 no estoque contra 11.116 no
`published_manifest`, e 1.366 páginas recusadas por lane estavam no ar.

**Onde está escrito:** `docs/CADEIA_DE_ADMISSIBILIDADE_DA_PAGINA.md` (mapa dos 9
elos com `arquivo:linha`), e a linha de gatilho por ato na tabela do `CLAUDE.md`.

**Como consultar em vez de adivinhar:** `./tools/oraculo-de-admissibilidade
--pagina <arquivo.jsonl>` roda os decisores REAIS numa raiz de ensaio
descartável (`cmd/ingest-v2-pages` + o censo com sha256 conferido) e devolve os
`reasons` deles. `--fiel` copia o acervo e avalia também as regras de lote; o
modo padrão imprime quais códigos ficaram por avaliar.

Relacionado: [[regua-do-jsonl-nao-e-a-regua-do-html]].
