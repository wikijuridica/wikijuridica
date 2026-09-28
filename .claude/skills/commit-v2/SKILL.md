---
name: commit-v2
description: Use ao commitar páginas ou portfólio do acervo v2 — o commit ordinário é recusado por desenho anti-fraude.
---

# Commit de páginas v2

`.githooks/pre-commit` **recusa qualquer commit ordinário** que tenha
`data/editorial/v2_pages/*.jsonl` no delta staged. No repositório principal
`private_v2_gate_capability` sempre falha (exige `.git` como arquivo regular,
isto é, worktree hardened), então o único caminho é
`tools/commit-verified-v2-workflow-results`, que roda o gate ele mesmo por git
plumbing num índice privado.

É lock rígido e legítimo. Em 2026-07-16 um workflow independente escreveu
**404 páginas boas** fora deste pipeline: pularam proveniência, CAS, namespace e
verificação, e ficaram **órfãs do commit**. Texto pago que não entrou no ar.
A ordem foi *adaptar à arquitetura, nunca construir paralelo*.

## Ordem dentro do commit

**`portfolio_v2/` primeiro, `v2_pages/` depois.** O gate recusa página cujo
`intent_id` não esteja no portfólio do commit **pai** — e a conferência local dá
1:1 mesmo assim, o que faz parecer que está tudo certo.

```
./tools/check-v2-portfolio-pairing        # ANTES de qualquer coisa
```

## O pipeline sancionado

1. `tools/generate_v2_review_queue.py` — módulo Python, sem CLI; entra por
   `build_todo()`. Gera os lotes com `slug=area-NN`, `portfolio_sha256`,
   `semantic_contract_sha256`, `source_hint_catalog_sha256`,
   `preserved_record_sha256`, `target_sha256`. CAS idempotente, **não forjável**
   à mão — forjar lote é repetir as 404 órfãs.
2. `scripts/workflows/writing-mass.js` — preflight CAS → escreve no WORKDIR
   privado → promoção CAS atômica → proveniência LIVE
   (`tools/audit-v2-source-provenance --live --apply`) → auditor
   `audit_v2_pages.py --against-stock`.
3. `tools/verify-v2-workflow-results --kind mass --results <json>` — relê os
   bytes e autentica.
4. `tools/commit-verified-v2-workflow-results` — commita a projeção autenticada.

## Medir o gap certo

O produto são **páginas**, não intents:
`intents(portfolio_v2) − intents_com_pagina(v2_pages)`.

Coordene a fatia de intents pelo bus `.agents/runtime/coordination/` antes de
escalar, para não colidir no namespace `area-NN`/`-rNN`.
