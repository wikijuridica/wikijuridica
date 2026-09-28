---
paths:
  - "go.mod"
  - "go.sum"
  - "internal/v2ingest/**"
  - "cmd/ingest-v2-stock/**"
  - "internal/lexml/**"
  - "internal/content/**"
  - "data/ops/*_witness.json"
  - "tools/ensaio-instancia"
---

# A atestação do validador hasheia o DISCO — quem toca o grafo leva a atestação

Memorias de origem: `atestacao-grafo-inclui-gomod.md`,
`gomod-sujo-invalida-atestacao.md`, `atestacao-serializa-duas-frentes.md`,
`commit-reatestacao-com-cerebro-parado.md`,
`corrigir-dado-exige-reatestar-junto.md`,
`ensaio-hardlink-codigo-quebra-atestacao.md`. (Da
`commit-reatestacao-com-cerebro-parado.md` vale a atestação no pathspec; o "parar o
cérebro" dela foi superado em 2026-09-17 — ver a nota do passo 5.)

Os casos medidos (datas, hashes, tempos) e o que ficou superado estao em
`docs/ops/ATESTACAO_DO_GRAFO_CASOS.md` (movidos literais em 2026-09-23). Aqui fica
so' o veredito, a ordem e o comando.

## O grafo nao e' fixo: meça antes de assumir que um pacote esta fora

`internal/v2ingest/validator_fingerprint_graph.go` hasheia `internal/v2ingest` E
`cmd/ingest-v2-stock` (`validatorFingerprintEntryDirs`), o fecho transitivo dos
imports deles, e **`go.mod` e `go.sum`**; `_test.go` fica de fora. **Todo import novo
nesses dois pacotes amplia o grafo em silencio** (em 2026-09-16 `internal/content`
entrou assim). O `paths:` desta regra e' atalho e sempre estara' um import atras:

```
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock
```

## Antes de commitar sob o grafo (ordem)

1. `git status --porcelain --untracked-files=all` nos **dois** diretorios mais
   `go.mod`/`go.sum`. `go generate` le o DISCO, nunca o indice, e o pre-commit confere
   a atestação contra o disco: sujeira de outra frente => **um** commit so', com
   **uma** reatestação. Agentes que tocam o grafo sao uma frente de commit; nunca dois
   `go generate` concorrentes.
2. `git status --short go.mod go.sum`: sujo e sem uso (grep dos modulos nos `.go` = 0 e
   build passando com o `-modfile` do HEAD) => preserve copia em `.agents/runtime/` e
   `git show HEAD:go.mod > go.mod`. `go.mod` sujo entra na atestação.
3. `stat -c %h go.mod` tem de dar **1**; 2 = ensaio antigo hardlinkado
   (`tools/ensaio-instancia destruir NOME`).
4. A atestação e' a **ultima** coisa, depois do gofmt: qualquer reescrita de arquivo do
   grafo, mesmo cosmetica, invalida o hash.
   `./tools/go-modern generate ./internal/v2ingest` e inclua
   `internal/v2ingest/validator_fingerprint_attestation_generated.go` no pathspec.
5. O orcamento do pre-commit e' `WIKI_COMMIT_GATE_TIMEOUT_SECONDS=90` e **subir
   timeout e' proibido**: a carga e' nossa, entao pausar o consumidor e' a correcao,
   nao o knob — `systemctl stop wikijuridica-cerebro.service` antes do commit e `start`
   depois. A atestação puxa `./internal/v2ingest/` (~700 s) para o pre-commit e segura
   o `.git/index.lock` ~12 min: commit em background sob `flock`, e trabalhe outra
   frente.
   *Superado em 2026-09-17:* não se para o cérebro para commitar; o remédio para o
   pre-commit lento é a slice de peso maior (`fila-do-cerebro.md`, seção "Politica
   vigente: nao travar por saturacao nem por CPU"). Até 2026-10-07 a pausa declarada
   pelo dono (`tools/cerebro-pausar`) torna a questão moot.

## Derivado atestado: corrigir o byte e reatestar no MESMO commit

Testemunho (`data/ops/*_witness.json`) carrega `records`, `corpus_sha256` e
**`corpus_bytes`** — os tres se reatestam no commit da correcao, preservando
`generated_at`. Gate reprovando por VOLUME sobre derivado atestado: **meça a
atestação antes de aceitar a divida** — `corpus_bytes` contra `stat -c%s` do arquivo,
e `git cat-file -s` em cada commit que tocou o blob.

## Ensaio: TUDO por copia (`cp -a`)

`tools/ensaio-instancia` espelha `public/`, `content/`, `data/` e o codigo por copia
integral. Symlink de codigo faz o gerador "do ensaio" escrever em producao
(`.resolve()` segue o link); hardlink de fonte Go trava a atestação (e todo commit Go);
hardlink de `public/` reescreve o HTML de producao (`os.WriteFile` e' in-place). Origem
incoerente depois de acidente se corrige PARA FRENTE com
`./tools/deploy-publico --ressemear`, nunca revertendo. O servidor de ensaio leva ~30 s
para `/healthz`: `curl --retry-connrefused`, nunca `sleep` fixo.
