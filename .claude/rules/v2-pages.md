---
paths:
  - "data/editorial/v2_pages/**"
  - "data/editorial/portfolio_v2/**"
  - "data/editorial/v2_superseded/**"
  - "data/editorial/v2_semantic_superseded/**"
  - "tools/commit-verified-v2-workflow-results"
  - "tools/verify-v2-workflow-results"
  - "tools/check-v2-portfolio-pairing"
  - "tools/check-v2-finalized-commit"
  - "tools/ingest-v2-stock"
  - ".githooks/reference-transaction"
---

# `v2_pages` — commit ordinario e' recusado, e o motivo e' anti-fraude

Memorias de origem: `gerador-datado-cas-correcao-v2.md`,
`v2-landing-arquitetura-gates.md`.

`.githooks/pre-commit` recusa **qualquer commit ordinario** que tenha
`data/editorial/v2_pages/*.jsonl` no delta staged:
*"shards v2 exigem tools/commit-verified-v2-workflow-results; commit ordinario
recusado"*. No repositorio principal `private_v2_gate_capability` sempre falha
(ele exige `.git` como arquivo regular, ou seja worktree hardened), entao o
unico caminho e' `tools/commit-verified-v2-workflow-results`, que roda o gate
ele mesmo por git plumbing num indice privado.

E' lock rigido e legitimo: pagina escrita fora deste pipeline pula proveniencia, CAS,
namespace e verificacao e fica **orfa do commit**. A ordem e' *adaptar a arquitetura,
nunca construir paralelo*. Casos medidos: `docs/ops/V2_PAGES_CASOS.md` (movidos
literais em 2026-09-23).

## Ordem dentro do commit

`portfolio_v2/` primeiro, `v2_pages/` depois. O gate recusa pagina cujo
`intent_id` nao esteja no portfolio do commit **pai** — e a conferencia local da
1:1 mesmo assim. Rode `./tools/check-v2-portfolio-pairing` **antes**.

## Pipeline sancionado (a unica forma de produzir pagina committavel)

1. `tools/generate_v2_review_queue.py` (modulo Python, sem CLI; entra por
   `build_todo()`) gera os lotes com `slug=area-NN`, `portfolio_sha256`,
   `semantic_contract_sha256`, `source_hint_catalog_sha256`,
   `preserved_record_sha256` e `target_sha256` — CAS idempotente, nao forjavel.
2. `scripts/workflows/writing-mass.js`: preflight CAS → escreve no WORKDIR
   privado → promocao CAS atomica → proveniencia LIVE
   (`tools/audit-v2-source-provenance --live --apply`) → auditor
   `audit_v2_pages.py --against-stock`.
3. `tools/verify-v2-workflow-results --kind mass --results <json>` rele os bytes
   e autentica.
4. `tools/commit-verified-v2-workflow-results` commita a projecao autenticada.

## Estrutura do corpo (nao ha chave `text` nem `body` no topo)

`opening`, mais `heading`+`text` de cada item de `sections`, mais `q`+`a` de cada
item de `faq` — nao `question`/`answer`, nao `paragraphs`. `word_count` canonico:
`tools/generate_v2_review_queue.py` (~linha 437), tokeniza por
`[0-9A-Za-zÀ-ÖØ-öø-ÿ]+`, tolerancia de 10% (`.split()` inventa divergencia).

Pagina redigida nunca se descarta: reprovada significa **consertar**. Antes de
tocar arquivo com texto redigido, preserve o anterior em `.agents/runtime/` com
data.

## Corrigir pagina JA escrita: gerador datado com CAS, nunca JSONL na mao

Frase antietica, titulo fora de faixa, eixo editorial errado — o conserto e' um
**gerador datado auto-contido**, no padrao de
`tools/generate-v2-title-length-repair-20260804`. Esqueleto obrigatorio:

- `canonical_stock_write_lease(ROOT)` (de `tools/v2_stock_epoch`) — o argumento
  e' o **ROOT**, nao o nome do produtor;
- `flock` exclusivo proprio + escrita atomica (`mkstemp` -> `fsync` ->
  `os.replace` -> `fsync` do diretorio), modo 0644;
- **CAS pelo sha256 da LINHA atual** (aborta se outra frente tocou o registro) e,
  em troca de trecho, CAS tambem **pelo trecho exato**;
- demais linhas do shard preservadas byte a byte; idempotente;
- payload embutido no proprio gerador, com o racional no docstring.

`cmd/finalize-v2-semantic-recut` **nao** reescreve: finaliza *recut requirement* ja
registrada em `data/editorial/v2_writing_semantic_contract.json` (supersessao de
intent duplicado) e recusa intent vivo; fabricar a requirement para contornar e'
manufaturar a autorizacao que o gate confere — fraude operacional.

Depois de qualquer correcao, **reingerir** (`tools/ingest-v2-stock`, ~4 min): o gate
le o espelho `authorial_mass_drafts.jsonl`, e o `word_count` declarado tem de
reproduzir `bodyWordCount` (`internal/v2ingest/validate.go:984`), senao
`declared_word_count_incoherent` tira a pagina do estoque.

## A arquitetura do pouso (2026-07-21, validada por execucao)

1. **Nunca por porcelain**: `tools/check-v2-finalized-commit:983` exige
   author+committer == `WORKFLOW_IDENTITY` e binds (`WIKI_V2_AUTHENTICATED_COMMIT_OID`
   etc.) que so' o `commit-verified-v2-workflow-results` produz; os gates rodam no
   `.githooks/reference-transaction` quando o delta toca o grafo v2 (v2_pages,
   portfolio_v2, v2_superseded, v2_semantic_superseded, v2_quarantine, contrato
   semantico, authority/recovery/forward em `data/ops`).
2. **Trust-root**: os gates sao materializados do **BASE** — codigo de gate e dado
   que ele valida **nao entram juntos**: CODIGO primeiro (sob o gate velho), DADO
   depois (sob o novo).
3. **Pins acoplam evidencia**: `gitIndexLiveEvidencePaths` +
   `defaultTrustedArchiveSHA256` (`integrity.go:40`) exigem os pinados e os
   `source_shards` dos archives no candidato — a unidade pousa com a cadeia inteira.
4. **Recut tem ancora fixa**: `--kind semantic-recut` exige delta NOVO do finalizer
   em `data/editorial/v2_semantic_superseded/writing-semantic-recuts-20260715.jsonl`;
   escrita em massa e' `--kind mass` com `--results`. `argv` nao acrescenta paths.
5. **Loader SELADO**: `sys.path` stdlib-only + allowlist `PYTHON_HELPERS` de blobs do
   HEAD; dependencia Python nova do produtor (ex. `tools/v2_stock_epoch.py`) entra em
   `PYTHON_HELPERS` + mapa de modos, senao "No module named".
6. O comando do `run-heavy-throttled` roda com o umask do chamador
   (`WIKI_HEAVY_CHILD_UMASK` sobrepoe).
