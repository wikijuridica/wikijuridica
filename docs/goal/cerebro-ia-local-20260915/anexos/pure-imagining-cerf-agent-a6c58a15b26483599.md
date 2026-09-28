# Refutação adversarial — "o cérebro julga o que é juízo"

**Veredito: CAI.**

O desenho supõe que a publicação passa pelo piso determinístico do `internal/v2ingest`.
Ela não passa. `cmd/publish-v2-direct/main.go:316` chama `v2publish.LoadPages(root)`, que
glob-a `data/editorial/v2_pages/*.jsonl` (`internal/v2publish/v2publish.go:179,194-224`) —
os SHARDS, direto. O único portão é `severity[intent].Publish`
(`v2publish.go:399-409`), e `publish = not critical` (`tools/generate-v2-publication-severity:799`).

O ingest e a `v2_rewrite_queue.jsonl` são canal LATERAL, e os três testes que os ligariam
à decisão de publicação disparam **zero** — medido nesta sessão sobre as 3.201 linhas da
fila: `"missing_required_field" in queue_reasons` casa 0 (500 linhas têm
`missing_required_field:` com prefixo), `official_sources_insufficient` 0 de 2.461,
`duplicate_phrase_with_page` 0 de 1.259.

Consequências:
1. Tirar a morte de `main.go:294` publica as 532 SEM nada pegar as corridas de 81
   palavras que o próprio autor mediu (`main.go:1857`). O juiz as manda a MÉDIO
   ("Nunca CRÍTICO") — publica igual.
2. A linha na `v2_rewrite_queue.jsonl` é inconstruível: um escritor só
   (`internal/v2ingest/v2ingest.go:34,993`), formato de envelope de run de ingest, e
   compactação que descarta linha não-última por intent (`:975-988`).
3. O defeito original (réguas divergentes) não fecha: `s_gate` é intra-área
   (1.134 de 11.225 páginas medidas), o gate real varre os 11.225.

Conserto mínimo, sem um token de LLM: o produtor usa o motor do gate
(`internal/v2bodyneardup`, `AssembleBody` + `FindNearDuplicatesInCorpus`) sobre o corpus
do gate, em `main.go:294`. E consertar os três `x in lista` da severidade ANTES de
afrouxar qualquer coisa.

Detalhe completo: os 10 ataques no StructuredOutput desta sessão.
