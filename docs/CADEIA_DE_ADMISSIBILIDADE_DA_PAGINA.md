# A cadeia de admissibilidade da página v2

**Para quem produz página** — o cérebro, os seis geradores derivados, qualquer
agente que escreva em `data/editorial/v2_pages/`. Responde uma pergunta só:
**o que precisa ser verdade para o que eu escrevo chegar a `public/`** — e
onde, exatamente, cada recusa nasce.

Antes de escrever o primeiro registro, a pergunta se responde por medição, não
por leitura:

```bash
./tools/oraculo-de-admissibilidade --pagina <candidato.jsonl>
```

O oráculo não tem régua própria: ele roda os decisores de verdade numa raiz de
ensaio descartável e devolve os `reasons` deles, caractere por caractere.
Este documento existe para o que o oráculo **não** decide — e para explicar
por que a cadeia tem dois trilhos.

---

## 1. A cadeia NÃO é uma linha: são dois trilhos a partir do mesmo arquivo

Medido em 2026-09-16. `cmd/publish-v2-direct` e `internal/v2publish` **não
importam** `internal/v2ingest` — zero ocorrências. A consequência é
contraintuitiva e explica quase todo o histórico de surpresa neste caminho:

```
                     data/editorial/v2_pages/<shard>.jsonl
                     data/editorial/portfolio_v2/<...>.jsonl
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
   TRILHO A — ESTOQUE                        TRILHO B — PUBLICAÇÃO
   quem decide: internal/v2ingest            quem decide: o censo + v2publish
              │                                           │
   tools/ingest-v2-stock                     tools/generate-v2-publication-severity
   → cmd/ingest-v2-stock                     → data/editorial/v2_publication_severity.jsonl
   → v2ingest.Run (v2ingest.go:358)                       │
   → validateBatch (validate.go:263)         cmd/publish-v2-direct (main.go:316-325)
   → validatePage  (validate.go:594)         → v2publish.LoadPages   (v2publish.go:194)
              │                              → v2publish.LoadSeverity(v2publish.go:239)
   data/editorial/authorial_mass_drafts.jsonl→ SelectPublishable     (v2publish.go:391)
   data/ops/v2_ingest_report.jsonl                        │
   data/editorial/v2_rewrite_queue.jsonl          public/ + published_manifest.jsonl
                                                          │
                                                 tools/deploy-publico (7 passos)
```

**Recusa no trilho A não impede a página de ir ao ar.** Ela impede que a
página entre no estoque canônico — que é o que mais de vinte gates deste
repositório leem como se fosse o acervo.

Medido em 2026-09-16: **7.982** registros em `authorial_mass_drafts.jsonl`
contra **11.116** no `published_manifest.jsonl`. Das 1.396 páginas que o
ingest recusou por `lane`/`page_type` naquele dia, **1.366 estavam
publicadas** — `/jurisprudencia/stj-tema-4/`, `/sumulas/stj-419/`,
`/noticias/tst-20260915/`, `/diarios/sp-20260912/` e as demais.

Isso é **DIVERGÊNCIA** no sentido do §P4 do plano do cérebro: dois
instrumentos afirmam medir a mesma coisa (admissibilidade da página) e não
medem. Não é fato nem juízo — é bug, e se fecha fazendo um chamar o outro.

---

## 2. Os elos, com arquivo:linha e o que cada um recusa

| # | elo | arquivo:linha | o que recusa | terminal? |
|---|---|---|---|---|
| 1 | produtor escreve página + intenção | `cmd/generate-acordao-pages/main.go:189` · `generate-stj-tema-pages/main.go:1210` · `generate-stj-sumula-pages/main.go:707` · `generate-stf-informativo-pages/main.go:777` · `generate-diario-pages/main.go:963` · `generate-noticia-pages/main.go:787` | nada — é aqui que a régua é **adivinhada** | — |
| 2 | pareamento intenção ↔ página | `tools/check-v2-portfolio-pairing` (a autoridade é o commit **PAI**, :8 e :159) | intent da página sem registro no portfólio do commit pai | sim (commit) |
| 3 | ordem de commit | portfólio **primeiro**, páginas **depois** | inverter reprova no elo 4 | sim |
| 4 | shard finalizado entrando na história | `.githooks/reference-transaction:240-244` → `tools/check-v2-finalized-commit` | shard v2 finalizado sem revisão; **fail-closed, e a recusa não aparece no log do pre-commit** | sim |
| 5 | ingestão no estoque canônico | `tools/ingest-v2-stock` → `cmd/ingest-v2-stock` → `v2ingest.Run` (`v2ingest.go:358`) → `validateBatch` (`validate.go:263`) → `validatePage` (`validate.go:594`) | campo ausente, lane, page_type, banda de palavras, title/meta/h1, fonte oficial, frase duplicada, reuso de heading, fonte revogada, fato jurídico vencido | **NÃO** para publicação — só para o estoque |
| 6 | censo de severidade | `tools/generate-v2-publication-severity` → `data/editorial/v2_publication_severity.jsonl` | crítico **não publica**; médio **publica e refina** | sim |
| 7 | seleção do publicável | `internal/v2publish.SelectPublishable` (`v2publish.go:391`); `sem_linha_no_censo` em `:400` | página sem linha no censo; `publish:false`; área indefinida; rota colidente | sim |
| 8 | transação de publicação | `cmd/publish-v2-direct/main.go:316-325`; `--allow-public-write` em `:176` | incoerência entre HTML, sitemap, manifesto e SHA-256 | sim |
| 9 | deploy | `tools/deploy-publico`: `0/7` ingest (`:425`), **`0.5/7` censo (`:495`)**, `1/7` publicação (`:503`) | qualquer passo que falhe: **nada vai para o ar** | sim |

### O elo 7 é o que mais cala

`SelectPublishable` pula a página **sem linha no censo** e continua. O motivo
sai impresso, e só. Em 2026-09-16 isso apagou, em silêncio, as 30 primeiras
páginas de acórdão do cérebro:

```
shard stj-acordao-derivado-01.jsonl  gravado  12:32:25
censo v2_publication_severity.jsonl  gravado  12:22:53
publicação (tools/deploy-publico)    rodou    ~13:01
sem_linha_no_censo                             30      ← .agents/runtime/p1b/deploy4_20260916.log
```

As 30 estavam corretas, commitadas e pareadas. O censo é **derivado** dos
shards: censo mais velho que um shard significa que a publicação vai descartar
exatamente o conteúdo novo. O passo `0.5/7` de `tools/deploy-publico` existe
desde esta data para fechar isso, e delega a
`tools/generate-censo-acompanha-estoque`, que delega a
`tools/check-censo-acompanha-estoque`.

---

## 3. O que o oráculo decide, e o que ele não decide

`./tools/oraculo-de-admissibilidade --pagina <arquivo.jsonl>`

**Decide olhando só o registro** (modo padrão, segundos): campos obrigatórios,
`lane`, `page_type`, banda de palavras, `title`/`meta_description`/`h1`, fonte
oficial (host, `verified_at`, `http_status`, mínimo de duas), promessa de
resultado, defeito de encoding, área derivável, piso de palavras do censo.

**Decide contra o acervo inteiro** (`--fiel`, ~1 min): `duplicate_phrase_*`,
`heading_reuse_*`, `intent_id_*`/`public_path_*` contra lote e estoque,
`intent_duplicado_entre_shards`, `rota_colidente`.

**NÃO decide** — e o oráculo imprime esta lista em toda execução, com o comando
de quem decide: pareamento contra o commit pai, shard finalizado no git,
colisão entre shards, rota já publicada, similaridade de corpo, coerência do
artefato publicado.

> **Rota já publicada é um caso à parte.** Hoje cada produtor decide sozinho,
> em três cópias: `cmd/generate-acordao-pages/main.go:628`,
> `cmd/generate-lei-artigo-pages/main.go:272` e `tools/generate-motor-tier-a:511`.
> É a mesma família de defeito deste documento, ainda aberta.

---

## 4. A família do defeito, para não a repetir

Toda regra desta cadeia existe hoje em duas ou mais cópias, e o produtor
**reimplementa** em vez de **consultar**:

| regra | cópias medidas em 2026-09-16 | efeito |
|---|---|---|
| `lane`/`page_type` admissíveis | 6 produtores × `v2ingest.validLanes` | 1.396 páginas recusadas no estoque; 1.366 delas **no ar** |
| censo acompanha o estoque | `check-censo-acompanha-estoque` (0 chamadores até esta data) × `tools/publicar:110` × `tools/deploy-publico` (não tinha cópia nenhuma) | 30 páginas do cérebro fora do ar, em silêncio |
| rota já publicada | 3 produtores, cada um com a sua | fila de candidatos divergente entre geradores |
| anti-molde | `internal/v2bodyneardup` (limiar 0,70; máximo medido 0,3217 na família de acórdão) × `v2ingest` `duplicate_phrase_with_page` (12-gramas idênticos) | a mesma família passa num e reprova no outro |
| piso de palavras | gerador (entrada) × censo `MIN_WORDS_HARD` (página) × `v2ingest` `wordCountBands` (página) | 4.500 acórdãos barrados por medir a grandeza errada (§P4) |

**A correção é sempre a mesma**, e é a do §P4: um instrumento **chama** o
outro. O oráculo é a forma executável disso para quem produz; o passo `0.5/7`
do deploy é a forma executável para quem publica.

---

## 5. Gatilho por ato

| Antes de… | Rode |
|---|---|
| gravar um shard novo em `data/editorial/v2_pages/` | `./tools/oraculo-de-admissibilidade --pagina <arquivo>` |
| commitar páginas v2 | `./tools/check-v2-portfolio-pairing` (e commite o portfólio **antes**) |
| publicar fora da onda diária | `./tools/generate-censo-acompanha-estoque` |
| afirmar que uma página "não publicou por causa do ingest" | meça: o ingest **não** está no caminho da publicação (§1) |

*Documento aberto em 2026-09-16. Parágrafo superado ganha data e motivo; não se
apaga (CLAUDE.md §12).*
