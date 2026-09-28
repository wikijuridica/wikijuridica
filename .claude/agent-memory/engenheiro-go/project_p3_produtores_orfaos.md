---
name: project-p3-produtores-orfaos
description: Estado das famílias "produtor órfão" (P3) e "conteúdo parado" (P8) em 2026-09-16 — o que fechou, o que sobrou e quem é dono do resto
metadata:
  type: project
---

Duas frentes do plano `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` tocam a mesma família: P3
(produtores órfãos) e P8 (nenhum conteúdo parado).

**Fechado em 2026-09-16:**

- Lado **Go** do P3: registro executável `ops/produtores-de-pagina.jsonl`, gate `produtor-orfao` e
  religamento de `generate-lei-artigo-pages` na onda diária.
- `tools/generate-propostas-reescrita` **deixou de ser órfão E passou a terminar**. O órfão era o
  sintoma; o defeito era o índice por **norma inteira** (10⁸ cossenos). Índice por **dispositivo**:
  166,8 s, 467.479 pares, 5.998 candidatas, zero precedentes sem artigo em comum (eram 37/100).
  Entrou como **etapa 8.8/9** de `tools/run-daily-content`.
- `tools/generate-first-published-at` (etapa 7.95/9).

**Aberto, e não é "detalhe":**

- `cmd/generate-acordao-pages`: defeito do teto de lote **não corrigido** — conflito de edição
  concorrente, devolvido ao maestro. Gatilho `publicador-cerebro`, então não publica hoje.
- `tools/generate-motor-tier-a` seguia órfão até 2026-09-16, quando virou a **etapa 1.9/9**; confira
  antes de confiar nesta linha.
- **Fila de refino sem consumidor** (`data/editorial/v2_rewrite_queue.jsonl`): 3.201 linhas, 2.461
  com `official_sources_insufficient`, das quais **2.320 têm exatamente UMA fonte válida** e **602
  não têm nenhum outro defeito** — uma segunda fonte oficial verificada as limpa inteiras.

**Dois fatos de arquitetura que economizam meia hora de busca:**

- O escritor sancionado de `v2_pages` para **refino** (não para página nova) já existe:
  `internal/v2sourceresearchreconcile` — `PatchTopLevelFields` (patch byte a byte de uma linha JSONL,
  preserva formatação) + `Apply` (CAS por shard, rename atômico). Ele **não** importa `shardpreserve`
  e por isso está corretamente fora do gate `produtor-orfao`, que marca produtores de página.
- O validador de página do `internal/v2ingest` **não é exportado**, e o pacote está no grafo da
  atestação. Prova "o motivo sumiu" feita de dentro dele custa atestação + ~10 min + 25 testes.

**Why:** o custo do órfão não é a página que deixou de nascer — é que a correção dos irmãos nunca
chega a ele, porque código que não roda não aparece em incidente. E "órfão" costuma ser o sintoma
visível de um defeito de escala escondido: o de propostas-reescrita não era agendamento, era um laço
que não terminava.

**How to apply:** confira o estado real antes de confiar nesta nota
(`./tools/go-modern run ./cmd/check produtor-orfao`, `grep` de invocação nos runners **lendo o
contexto**). E não force linha em `ops/produtores-de-pagina.jsonl` para produtor que não escreve shard
de página: os campos `shard`/`portfolio` seriam falsos, e registro executável com campo falso mente com
autoridade de gate. Ver [[feedback-parar-em-arquivo-concorrente]].
