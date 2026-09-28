# `v2_pages` — casos medidos e parágrafos superados

> Movido de `.claude/rules/v2-pages.md` em 2026-09-23. A rule passou do teto de 6.000
> caracteres que `tools/check-modo-operacional` cobra (T1) e foi condensada para
> veredito, ordem dos passos e comando de medição (plano
> `docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8, frente 4, item 6). **Nada foi
> apagado:** a seção "Texto integral" abaixo é a rule exatamente como estava no commit
> `31c917e1`, sem o frontmatter `paths:` (que continua na rule). Os casos medidos, as
> tabelas de tempo e os parágrafos marcados SUPERADO ficam aqui como evidência; o que
> vale como ordem é a rule.
>
> Este arquivo não carrega em sessão nenhuma: é lido quando a rule manda ou quando
> alguém precisa do número que sustentou o veredito.

## O que só está aqui

- **2026-07-16** — um workflow independente escreveu 404 páginas boas fora do pipeline e elas ficaram órfãs do commit.
- **`word_count`** — com `.split()` e tolerância de 2 palavras "aparecem" 88 divergências em 189 páginas; pela régua real, 0.
- **`d1285f55`** — o `umask 077` do `run-heavy-throttled` herdava para binários de teste (histórico do item 6 da arquitetura do pouso).

## Texto integral da rule até 2026-09-23 (commit `31c917e1`)

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

E' lock rigido e legitimo. Em 2026-07-16 um workflow independente escreveu **404
paginas boas** fora deste pipeline: pularam proveniencia, CAS, namespace e
verificacao, e ficaram **orfas do commit** — texto pago que nao entrou no ar.
A ordem foi *adaptar a arquitetura, nunca construir paralelo*.

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

O corpo e' `opening`, mais `heading`+`text` de cada item de `sections`, mais
`q`+`a` de cada item de `faq` — nao `question`/`answer`, nao `paragraphs`.
A formula canonica de `word_count` esta em `tools/generate_v2_review_queue.py`
(~linha 437): tokeniza por `[0-9A-Za-zÀ-ÖØ-öø-ÿ]+`, tolerancia de 10%. Com
`.split()` e tolerancia de 2 palavras "aparecem" 88 divergencias em 189 paginas;
pela regra real sao 0.

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

`cmd/finalize-v2-semantic-recut` **nao** e' ferramenta generica de reescrita: ela
finaliza uma *recut requirement* ja registrada em
`data/editorial/v2_writing_semantic_contract.json` e serve a supersessao de
intents duplicados. Para intent que continua existindo ela recusa
(`FAIL: semantic recut intent is not a contract requirement: <intent>`), e
fabricar a requirement para contornar seria manufaturar a propria autorizacao que
o gate existe para conferir — fraude operacional.

Depois de qualquer correcao, **reingerir** (`tools/ingest-v2-stock`, ~4 min): o
gate le o espelho `authorial_mass_drafts.jsonl`, nao o `v2_pages` direto. E o
`word_count` declarado tem de reproduzir `bodyWordCount`
(`internal/v2ingest/validate.go:984`), senao o ingest rejeita com
`declared_word_count_incoherent` e a pagina some do estoque sem ninguem ter
pedido.

## A arquitetura do pouso (2026-07-21, validada por execucao)

1. **Nunca por porcelain**: `tools/check-v2-finalized-commit:983` exige
   author+committer == `WORKFLOW_IDENTITY` e binds de ambiente
   (`WIKI_V2_AUTHENTICATED_COMMIT_OID` etc.) que so o
   `commit-verified-v2-workflow-results` produz. Quem roda os gates e' o hook
   `.githooks/reference-transaction`, quando o delta toca os paths do grafo v2
   (v2_pages, portfolio_v2, v2_superseded, v2_semantic_superseded, v2_quarantine,
   contrato semantico, authority/recovery/forward em `data/ops`).
2. **Trust-root anti-auto-autorizacao**: os gates do hook sao materializados do
   **BASE** (pai do commit) — mudanca de codigo de gate e dado que ela valida
   **nao entram juntos**. Ordem: commit do CODIGO primeiro sob o gate velho (dado
   inalterado no candidato), depois o DADO sob o gate novo.
3. **Pins acoplam evidencia**: `gitIndexLiveEvidencePaths` +
   `defaultTrustedArchiveSHA256` (`integrity.go:40`) exigem os arquivos pinados
   presentes em qualquer candidato auditado, e os archives exigem seus
   `source_shards` no estoque do candidato — a unidade pousa com a cadeia
   inteira.
4. **Recut tem ancora fixa**: `--kind semantic-recut` exige delta NOVO do
   finalizer na ancora
   `data/editorial/v2_semantic_superseded/writing-semantic-recuts-20260715.jsonl`;
   fecho de escrita em massa e' outra classe (`--kind mass` com `--results` do
   `verify-v2-workflow-results`). `argv` nao acrescenta paths.
5. **O committer tem loader SELADO**: `sys.path` stdlib-only + allowlist
   `PYTHON_HELPERS` de blobs do HEAD. Dependencia Python nova do produtor (ex.
   `tools/v2_stock_epoch.py`) precisa entrar em `PYTHON_HELPERS` + mapa de modos,
   senao "No module named".
6. **`umask 077` do `run-heavy-throttled`** herdava para binarios de teste (fix
   `d1285f55`: o comando roda com o umask do chamador; `WIKI_HEAVY_CHILD_UMASK`
   sobrepoe; artefatos do wrapper seguem 077).
