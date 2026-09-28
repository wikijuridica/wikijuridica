# Atestação do grafo do validador — casos medidos e parágrafos superados

> Movido de `.claude/rules/atestacao-do-grafo.md` em 2026-09-23. A rule passou do teto de 6.000
> caracteres que `tools/check-modo-operacional` cobra (T1) e foi condensada para
> veredito, ordem dos passos e comando de medição (plano
> `docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8, frente 4, item 6). **Nada foi
> apagado:** a seção "Texto integral" abaixo é a rule exatamente como estava no commit
> `197ea62b`, sem o frontmatter `paths:` (que continua na rule). Os casos medidos, as
> tabelas de tempo e os parágrafos marcados SUPERADO ficam aqui como evidência; o que
> vale como ordem é a rule.
>
> Este arquivo não carrega em sessão nenhuma: é lido quando a rule manda ou quando
> alguém precisa do número que sustentou o veredito.

## O que só está aqui

- **2026-09-05** — a adoção de `yeqown/go-qrcode` invalidou uma atestação recém-gerada sem tocar nenhum `.go` do v2ingest: 25 testes vermelhos depois de ~10 min de compilação (seção "O que entra no hash").
- **2026-09-05, SUPERADO em 2026-09-16** — a lista "Medido: … ESTÃO no grafo; … NÃO estão" dizia que `internal/content` estava fora; em 2026-09-16 `internal/v2ingest/validate.go` passou a importá-lo e ele entrou (bloco do topo). A lista vale só como retrato daquela data: a régua é `./tools/go-modern list -deps`.
- **2026-09-16** — commit de `cmd/cerebro` + `internal/content/content.go` reprovado pelo grafo ampliado em silêncio (bloco do topo).
- **2026-09-16** — `go generate` lê o disco: commit de `cmd/ingest-v2-stock` reprovado com `undefined: validLanes` por edição concorrente em `validate.go` (+94 −13).
- **2026-09-08** — `go.mod`/`go.sum` sujos desde 09:33 (20 módulos, nenhum importado) entraram nas atestações das 16:06 e 16:56.
- **2026-09-11** — atestação feita antes do gofmt do `.go` gerado: 10 testes vermelhos depois de ~5 min.
- **2026-09-08, SUPERADO em 2026-09-17 no remédio** — orçamento de 90 s: com a atestação no índice, `closure_mode=reverse affected_packages=410` estourou os 75,3 s sob load 9-10 da extração; com o cérebro parado, 29,3 s; `./internal/v2ingest/` sozinho leva 621-698 s. A ordem do dono de 2026-09-17 ("nunca pausar a inteligência", `fila-do-cerebro.md`) supera o "parar o cérebro antes do commit": o remédio para o pre-commit lento passou a ser a slice de peso maior. Nota acrescentada em 2026-09-23.
- **2026-09-11** — `48008cb9` trocou 1 byte (U+0435 por `e`) sem reatestar `corpus_bytes`; `refinedcorpusfloor.Piso` falhou fechado e o vermelho `records=7959 minimum=10000` foi lido como volume ("2.041 páginas a produzir").
- **2026-09-01** — ensaio: symlink de código fez o gerador escrever em produção (churn de 30% devolveu 0,6%); hardlink de fonte Go travou a atestação; hardlink de `public/` reescreveu os 10.359 HTML de produção.

## Texto integral da rule até 2026-09-23 (commit `197ea62b`)

> **O grafo CRESCEU em 2026-09-16, e o alcance novo pegou um commit meu.** Ao fechar a
> divergência de vocabulário, `internal/v2ingest/validate.go` passou a importar
> `internal/content` — três ocorrências — para tirar lane e `page_type` da fonte única em
> vez da cópia pobre. **Consequência que ninguém declarou: `internal/content` entrou no
> grafo do validador.** Um commit que tocava só `cmd/cerebro` e `internal/content/content.go`
> reprovou com *"1 arquivo(s) deste commit estao no grafo de fonte do validador, e o
> atestado nao entra junto"*.
>
> **A lição é de método, não de caminho:** a lista de pacotes no grafo **não é fixa** —
> ela é o fecho transitivo dos imports de `internal/v2ingest` e `cmd/ingest-v2-stock`, e
> **todo import novo nesses dois pacotes amplia o grafo em silêncio**. Antes de assumir
> que um pacote está fora, meça: `./tools/go-modern list -deps ./internal/v2ingest` e
> procure o seu. O `paths:` desta regra é um atalho útil e **sempre estará um import
> atrás** do código.

# A atestação do validador hasheia o DISCO — quem toca o grafo leva a atestação

Memorias de origem: `atestacao-grafo-inclui-gomod.md`,
`gomod-sujo-invalida-atestacao.md`, `atestacao-serializa-duas-frentes.md`,
`commit-reatestacao-com-cerebro-parado.md`,
`corrigir-dado-exige-reatestar-junto.md`,
`ensaio-hardlink-codigo-quebra-atestacao.md`.

## O que entra no hash (e a surpresa: `go.mod` e `go.sum`)

`internal/v2ingest/validator_fingerprint_graph.go` hasheia `internal/v2ingest` E
`cmd/ingest-v2-stock` juntos (`validatorFingerprintEntryDirs`, linhas 29-32) e,
alem deles, **`go.mod` e `go.sum`** (linhas 977 e 990). `_test.go` fica de fora
(`:669`).

Em 2026-09-05 uma sessao adotou `yeqown/go-qrcode` e isso invalidou, **sem tocar
em nenhum arquivo Go do v2ingest**, uma atestação recem-regenerada: 25 testes de
`internal/v2ingest` vermelhos com `generated=… source=…; run go generate
./internal/v2ingest`, depois de ~10 min de compilacao no pre-commit.

Descobrir quem esta no grafo custa uma linha:

```
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock
```

Medido: `internal/wikijuridicabot` e `internal/lexml/knowncodes.go` ESTAO no
grafo; `internal/render`, `internal/content`, `internal/pagemarkdown`,
`internal/checks`, `internal/codex2coveragefrontier` e
`internal/authorialmassqualityvectors` NAO estao. Sao 0,1 s contra ~700 s pagos
pela pessoa errada.

## `go generate` le o DISCO, nunca o indice — e isso serializa duas frentes

Medido em 2026-09-16: uma tentativa de commitar `cmd/ingest-v2-stock` enquanto
outra frente editava `internal/v2ingest/validate.go` (+94 −13) e deixava
`?? lane_e_page_type_canonicos_test.go` na worktree falhou com
`undefined: validLanes`, e o commit reprovou com
`generated=sha256:585f049f… source=sha256:0171798f…`. O `_test.go` estar fora do
hash **nao** salva: o pre-commit roda a bancada, e ela confere a atestação contra
o disco.

Antes de commitar sob um diretorio do grafo, rode
`git status --porcelain --untracked-files=all` nos **dois** diretorios mais
`go.mod`/`go.sum`. Sujeira de outra frente => **nao ha commit separado**: os dois
trabalhos saem num commit so, com **uma** reatestação, e quem chegar primeiro
espera ou coordena por mensagem. Agentes que tocam o grafo sao **uma** frente de
commit, e nunca dois `go generate` concorrentes.

## `go.mod` sujo entra na atestação

Em 2026-09-08 o worktree carregava `go.mod`/`go.sum` modificados desde 09:33 (20
modulos, nenhum importado, origem nao identificada). As atestações commitadas as
16:06 e 16:56 foram geradas contra o `go.mod` sujo, e HEAD ficou inconsistente
para um checkout limpo. Antes de `go-modern generate ./internal/v2ingest`, rode
`git status --short go.mod go.sum`; sujo e sem uso (grep dos modulos nos `.go` =
0 e build completo passando com o `-modfile` do HEAD), preserve copia em
`.agents/runtime/` e regrave com `git show HEAD:go.mod > go.mod`.

## A atestação e' a ULTIMA coisa antes do commit — inclusive depois do gofmt

Em 2026-09-11: atestei, o pre-commit reprovou porque o `.go` GERADO nao estava
formatado, corrigi o gerador, ele reescreveu o arquivo — e a atestação ja feita
ficou para tras (`generated=sha256:c025c6a2… source=sha256:2b4eadc1…`, 10 testes
vermelhos depois de ~5 min de compilacao). **Qualquer reescrita de arquivo do
grafo, mesmo cosmetica, invalida o hash.**

## O orcamento do pre-commit e' de 90 s, e a carga do cerebro o estoura

Em 2026-09-08 o commit de `internal/lexml` foi recusado duas vezes: primeiro por
faltar a atestação no pathspec (remedio:
`./tools/go-modern generate ./internal/v2ingest` e incluir
`internal/v2ingest/validator_fingerprint_attestation_generated.go`); depois
porque, com a atestação no indice, o `go-index-compile-closure` vira
`closure_mode=reverse affected_packages=410` e, sob load 9-10 da extracao LLM,
estourou os 75,3 s concedidos. Com `systemctl stop wikijuridica-cerebro.service`
antes e `start` depois, passou em **29,3 s**. O orcamento e'
`WIKI_COMMIT_GATE_TIMEOUT_SECONDS=90` e **subir timeout e' proibido**: a carga
era nossa, entao pausar o consumidor e' a correcao certa, nao o knob.

Incluir a atestação puxa `./internal/v2ingest/` para o teste do pre-commit, e
esse pacote leva ~700 s sozinho (medido: 698 s e 621 s): o commit segura o
`.git/index.lock` por ~12 min e **nenhuma outra sessao commita** nesse intervalo.
Commit em background sob `flock`, e trabalhe outra frente.

## Derivado atestado: corrigir 1 byte sem reatestar inventa 2.041 paginas de trabalho

Derivado com testemunho (`data/ops/*_witness.json`) carrega `records`,
`corpus_sha256` e **`corpus_bytes`** — os tres se reatestam no MESMO commit da
correcao, preservando `generated_at` (a geracao nao foi refeita, so o byte).

Caso de 2026-09-11: `48008cb9` trocou um `U+0435 CYRILLIC SMALL LETTER IE` (2
bytes) por um `e` latino (1 byte) numa pagina publicada — correcao certa. O
corpus foi de 86.519.453 para 86.519.452 bytes e o testemunho ficou com o tamanho
antigo. `refinedcorpusfloor.Piso` **falha fechada** (correto) e devolveu o piso de
producao, 10.000; oito pacotes leem esse piso. O vermelho que chegou a triagem
foi `ptbr_confusables_minimum_records_missing: records=7959 minimum=10000`, que
**se le como volume** — duas sessoes concluiram "a fabrica tem de produzir 2.041
paginas" antes de alguem medir. O commit anterior sobre o mesmo corpus
(`f44aaf65`) tinha feito certo.

Ao ver gate reprovando por VOLUME sobre derivado atestado, **meca a atestação
antes de aceitar a divida**: `corpus_bytes` do testemunho contra `stat -c%s` do
arquivo, e `git cat-file -s` em cada commit que tocou o blob.

## Ensaio: TUDO por copia (`cp -a`) — hardlink trava a atestação e symlink escreve em producao

`tools/ensaio-instancia` (2026-09-01) espelha `public/`, `content/`, `data/` e o
codigo por copia integral (5,7 GB, ~1 min). As tres alternativas baratas
quebraram no mesmo dia, em ordem crescente de dano:

- **symlink de codigo**: os geradores resolvem
  `ROOT = Path(__file__).resolve().parent.parent`, e `.resolve()` segue o link —
  ROOT vira `/opt/wiki` e o gerador "do ensaio" ESCREVE em producao. Apanhado
  porque um teste de churn de 30% devolveu 0,6%.
- **hardlink de fonte Go**: todo fonte passa a ter dois links e
  `internal/v2ingest/cmd/generate-validator-fingerprint-attestation` recusa
  ("expected a regular file with one link"). Com um ensaio vivo, **nenhum commit
  que toque Go passa no pre-commit**.
- **hardlink de `public/` e dados (o pior)**: o Go grava com `os.WriteFile`, que
  escreve IN-PLACE (sem rename atomico), e um `cmd/build public` no ensaio
  hardlinkado **reescreveu os 10.359 HTML de producao**, deixando `.br` e
  `published_manifest` incoerentes (a borda seguiu servindo o velho por HIT).

Antes de commitar Go, `stat -c %h go.mod` tem de dar **1**; se der 2, ha ensaio
antigo — `tools/ensaio-instancia destruir NOME`. Origem incoerente depois de
acidente assim se corrige PARA FRENTE com `./tools/deploy-publico --ressemear`,
nunca revertendo. E o servidor de ensaio leva ~30 s para responder `/healthz`:
`curl --retry-connrefused`, nunca `sleep` fixo.
