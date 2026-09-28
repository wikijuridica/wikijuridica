# LACUNA 2 — O GRAFO DE ATESTAÇÃO (investigação read-only, 2026-09-15)

## Veredito: CONTROLADO para o plano, com UM ponto cego GRAVE na guarda

Nenhum dos seis pacotes que o plano propõe mudar está no grafo. A guarda de
commit existe, está ligada e cobre go.mod/go.sum. Mas ela tem um ponto cego
provado: `_test.go` dentro de `internal/strictjson` ENTRA no hash e a guarda o
descarta por construção — e o selftest afirma esse descarte como correto.

## 1. Quem está no grafo hoje — 98 pacotes, medido

`./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` →
98 pacotes in-module, 5,65 s medidos (contrato dizia ~2,2 s; gate escrito em
2026-08-29 dizia 96 pacotes — cresceu 2).

O grafo NÃO é o diretório: é a **closure transitiva de import** a partir dos
dois entry dirs (`validatorFingerprintEntryDirs`,
`validator_fingerprint_graph.go:29-32`), restrita a imports `portaljuridico/*`.

### Prova de que `go list -deps` é proxy EXATO do walker

Repliquei a BFS do walker (`validatorCodeGraphInputsFromSourceWithPolicy`,
:629-790) em Python read-only, com parser de bloco `import` real:

- walker replicado: **98 diretórios**, 207 arquivos
- `go list -deps` in-module: **98**
- só no walker: **[]** · só no go list: **[]** → **divergência zero**

A primeira tentativa (regex `"portaljuridico/…"` sobre o arquivo inteiro) deu
362 diretórios e incluiu `internal/datajud`, que **não existe** — a regex casou
string de dado, não import. Registro o erro porque ele é o jeito natural de
errar esta medição.

### Prova definitiva: reproduzi o digest gravado

Hashei os 207 arquivos como o Go hasheia (`rel` + NUL + bytes + NUL, ordenado):

```
replicado: sha256:beb3ac7eb196629720213f923077a46ccddcc3c411b1c0343875cdb6349cfe17
gravado  : sha256:beb3ac7eb196629720213f923077a46ccddcc3c411b1c0343875cdb6349cfe17  → BATE
```

Isso prova o conjunto exato de entrada, não o estima.

## 2. Os pacotes do plano × grafo — 0 de 6 dentro

| pacote do plano | no grafo? |
|---|---|
| `cmd/generate-acordao-pages` (P4/P6) | **fora** |
| `internal/cerebro` (P9) | **fora** |
| `internal/stjacordaos` (P8) | **fora** |
| `internal/ollama` (P12) | **fora** |
| `internal/checks` (gates novos) | **fora** |
| `internal/v2bodyneardup` (P4) | **fora** |
| `tools/run-daily-content` | não é Go |

Motivo estrutural: **o hash depende das arestas de SAÍDA do grafo, não das de
entrada.** Os seis só são importados por `cmd/*` main (nada os importa de
dentro) e por `internal/httpserver`/`internal/semantica`/`internal/cerebro` —
todos fora do grafo. Medido com grep reverso de import.

P1b também está fora: `first_published_at` vive em `cmd/publish-v2-direct`
(fora), `tools/generate-first-published-at` (shell) e `internal/httpserver`
(fora).

### Os vizinhos perigosos — DENTRO do grafo, e o plano passa perto

**`internal/lexml` — a colisão mais provável do plano.** Está no grafo (medido) e
já custou: precedente `commit-reatestacao-com-cerebro-parado.md` — em 2026-09-08 o
commit `fb1d5fb6` (lexml CTN/CP/CPP) foi recusado **duas** vezes: primeiro porque
`internal/lexml/knowncodes.go` está no grafo e a atestação não ia junto; depois
porque, **com a atestação no índice**, `go-index-compile-closure` vira
`closure_mode=reverse affected_packages=410` e, sob load 9–10 da extração LLM do
cérebro, estourou os **75,3 s** concedidos. Com o cérebro parado passou em **29,3 s**.
P8 (agregação por URN, `generate-lei-artigo-pages:485-500`) e P9 (dispositivos com
URN LexML) são exatamente as frentes que descem para parsing de URN.

Demais: `internal/publishedmanifest` (P1b), `internal/stockmanifest` (P6),
`internal/v2portfolioindex` (P4/P6), `internal/quality`, `internal/seo`,
`internal/editorial`, `internal/strictjson`, `internal/siteicon`.

Se qualquer correção descer para um desses, a atestação passa a ser obrigatória
no mesmo commit. Foi assim que o deploy das 21:34 de 2026-08-29 morreu:
`internal/structureddata`, `internal/legalfacts`, `internal/legalcorpusindex` —
três pacotes que ninguém associa ao ingest, todos no grafo.

## 3. O mecanismo: o que hasheia, onde grava, quem valida

**O que hasheia** (207 arquivos, medido):
- 203 `.go` de produção nos 98 diretórios
- **`go.mod` e `go.sum`** (semeados em `seenFiles`, :641; go.mod ainda é parseado
  por `modfile` para extrair module path e **recusar `replace` local**, :1003)
- **2 `_test.go` de `internal/strictjson`**, trazidos pelo passe de `//go:embed *.go`
- exclui o próprio arquivo gerado (auto-referência), exclui `.`/`_` prefixados,
  exclui `_test.go` em todos os outros 97 pacotes

**Hasheia o WORKTREE, não o commit.** É alvo móvel com duas sessões editando.

**Onde grava**: `internal/v2ingest/validator_fingerprint_attestation_generated.go`
— 5 linhas, uma const `compiledValidatorCodeGraphFingerprint`.

**Quem valida**:
- runtime: `plan.go:855` e `adjudicate_shard.go:289` →
  `attestCompiledValidatorCodeFingerprint` → `ErrValidatorBinarySourceMismatch`.
  `ingest-v2-stock` recusa publicar; **nenhum deploy passa**.
- disco: `tools/check-validator-attestation` (read-only de verdade: gerador
  escreve em `mktemp`, compara por `cmp`).
- commit: `tools/check-atestacao-grafo-no-commit`, ligado em
  `.githooks/pre-commit:366` (`core.hooksPath=.githooks`).

**Recusas duras do walker**: `vendor/`, `go.work` em qualquer ancestral, `GOWORK`
explícito, `import "C"`, `//go:linkname`, embed de diretório ou de asset não-Go,
`replace` local, fontes C/asm.

**Precedente go.mod sujo — achado.** `memory/gomod-sujo-invalida-atestacao.md`:
em 2026-09-08 o worktree tinha go.mod/go.sum modificados desde 09:33 (20 módulos,
nenhum importado); as atestações de **16:06 e 16:56** foram geradas contra o
go.mod sujo e HEAD ficou inconsistente para um checkout limpo. Precedente irmão
(`atestacao-grafo-inclui-gomod.md`): adotar `yeqown/go-qrcode` invalidou a
atestação **sem tocar um .go do v2ingest** → 25 testes vermelhos após ~10 min de
compilação. E em 2026-09-11 a atestação ficou para trás porque o **gofmt** do
arquivo gerado o reescreveu depois → 10 testes vermelhos após ~5 min.

## 4. O PONTO CEGO — GRAVE, provado

`tools/check-atestacao-grafo-no-commit` filtra `*_test.go` de `CANDIDATOS`
**antes** de consultar o grafo, com este comentário:

> `*_test.go) ;;` — "Teste nao entra no grafo (validator_fingerprint_graph.go:669
> descarta *_test.go)."

Verdadeiro em 97 dos 98 pacotes. **Falso em `internal/strictjson`**, onde
`implementation_fingerprint.go:14` tem `//go:embed *.go` e o passe de embed
(:703-738) casa contra TODAS as entradas do diretório **sem reaplicar o corte de
`_test.go`**. Os dois arquivos que entram só por aí:
`internal/strictjson/decode_bench_test.go` e `internal/strictjson/strictjson_test.go`
— e sem eles o digest **não fecha** (medi: `7fd00442…` sem, `beb3ac7e…` com).

Consequência: commit que toque só `internal/strictjson/*_test.go` recebe
`OK: o commit nao toca Go de producao nem o modulo`, exit 0, atestação fica
STALE, e **todo deploy seguinte morre** com `ingest-v2-stock` recusando publicar.

Pior: `tools/check-atestacao-grafo-no-commit-selftest:104` **afirma esse exit 0
como correto** (`verifica "so teste do grafo passa" 0 stale …`), e escolhe
`DENTRO` pelo primeiro dir do grafo com .go de produção — então nunca exercita
`internal/strictjson`. Um detector cujo selftest consagra o ponto cego.

### Ponto cego menor (já documentado por precedente)
O passo 1 do gate faz curto-circuito na **presença** do arquivo de atestação, não
na sua **correção**: atestação stale incluída no commit passa. É exatamente o
caso gofmt de 2026-09-11.

## 5. Custo, medido hoje

| operação | custo | fonte |
|---|---|---|
| `go list -deps` dos 2 entry dirs | **5,65 s** | medido hoje |
| gerar + comparar atestação (`check-validator-attestation`) | **7,62 s**, exit 0 | medido hoje |
| estado da atestação agora | **VERDE**, `sha256:beb3ac7e…` | medido hoje |
| `go.mod`/`go.sum` no worktree | **limpos**; índice **limpo** | medido hoje |
| pre-commit, v2ingest tocado SÓ pela atestação | **86 s** (`-run 'Attestation|Fingerprint'`) | `.githooks/pre-commit:691`, medido no repo |
| pre-commit, v2ingest com qualquer outro .go | **611 s** (também 698 s e 621 s) | pre-commit:673 + precedente |
| commit nesse caso segura `.git/index.lock` | **~12 min** | `atestacao-grafo-inclui-gomod.md` |
| closure de compilação, índice limpo × sujo | **14,9 s × 77,6 s**, orçamento **90 s** | contrato 2026-09-05 + `--budget-seconds 90` |

**Não medi** `go-modern generate ./internal/v2ingest` isolado: ele ESCREVE o
arquivo e a sessão é read-only. O 7,62 s é o limite superior justo — é o mesmo
gerador, mais um `cmp`.

## 6. REGRA OPERACIONAL

**R0 — Pergunte ao grafo antes de montar o pathspec.** 5,65 s contra 611 s pagos
pela pessoa errada:
`./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock | sed -n 's|^portaljuridico/||p' | grep -xF <seu_dir>`

**R1 — Commits do plano que levam atestação: NENHUM, como o plano está.** P1b, P4,
P6, P8, P9, P12 tocam só pacotes fora do grafo. Incluir a atestação nesses
commits é ERRADO: puxa `./internal/v2ingest/` para o teste focado e custa 86 s (ou
611 s) sem necessidade — e o precedente manda "se você não tocou nada do grafo,
tire a atestação do seu commit".

**R2 — Passa a levar atestação se, e só se, o commit tocar:** `go.mod`, `go.sum`,
qualquer `.go` de produção num dos 98, **ou** `internal/strictjson/*_test.go`.
Reavalie a cada onda: o grafo cresceu de 96 → 98 em 17 dias.

**R3 — Gatilho novo que o plano cria:** se P8/P9 descerem para **`internal/lexml`**
(URN — o caso mais provável), se a paridade do P4 mover a régua para dentro de
`internal/quality`, ou se P1b/P6 descerem para `internal/publishedmanifest` /
`internal/stockmanifest` / `internal/v2portfolioindex`, o commit passa a ser de
grafo. Decida isso ANTES de editar: manter a correção em
`cmd/generate-acordao-pages` e `internal/v2bodyneardup` mantém todos os commits do
plano baratos.

**R3b — Teto de 6 pacotes: acima dele o teste focado NÃO roda.**
`.githooks/pre-commit` tem `TETO_DE_PACOTES=6` e, acima disso, apenas AVISA
("o teste focado NAO rodou nesta passada") e **deixa o commit passar**. Os seis
pacotes do plano batem exatamente no teto: agrupá-los num commit só — ou juntá-los
com a atestação — faz os testes focados sumirem em silêncio. Cada commit Go do
plano fica em **≤ 6 pacotes**, e um commit de grafo vai sozinho.

**R4 — Ordem dentro de um commit de grafo** (só se R2 disparar):
1. **O worktree inteiro do grafo tem de estar limpo de trabalho alheio**, não só o
   go.mod: a atestação hasheia o WORKTREE, então edição não-commitada de outra
   sessão em qualquer um dos 98 entra no hash.
   `git status --short -- go.mod go.sum $(./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock | sed -n 's|^portaljuridico/||p')`
   → só os SEUS arquivos podem aparecer. go.mod sujo e sem uso: preservar em
   `.agents/runtime/` e restaurar com `git show HEAD:go.mod > go.mod` (nunca
   `checkout`). Este é o passo que faltou em 2026-09-08.
1b. **Pausar o cérebro** (`systemctl stop wikijuridica-cerebro.service`) — com ele
   rodando, o closure reverso de 410 pacotes estourou 75,3 s; parado, 29,3 s.
   Religar depois do commit. Relevante porque P9/P12 é o próprio cérebro.
2. Terminar TODA edição de arquivo do grafo, **gofmt incluído**.
3. `./tools/go-modern generate ./internal/v2ingest` — **último passo antes do add**.
4. `./tools/check-validator-attestation` → exigir `OK` (7,6 s). **Este é o veredito,
   não o passo 1 do gate de commit.**
5. `git add <caminhos exatos>`; `git add internal/v2ingest/validator_fingerprint_attestation_generated.go`
6. `git diff --cached --name-only | grep -E '^internal/v2ingest/.*\.go$' | grep -v attestation_generated`
   → **vazio** garante a rota de 86 s; não-vazio custa 611 s e ~12 min de index.lock.
7. Esvaziar o índice de outras frentes antes (closure compila o ÍNDICE: 14,9 s × 77,6 s
   contra orçamento de 90 s), serializar com `flock /tmp/opt-wiki-commit.lock`,
   `git add` e `git commit -F` em comandos SEPARADOS.

**R5 — Conserto do ponto cego, como passo do plano** (é achado a corrigir, não
observação): em `tools/check-atestacao-grafo-no-commit`, trocar o descarte cego de
`*_test.go` por descarte que **consulte os padrões `//go:embed` dos pacotes do
grafo** — ou, mínimo verificável, deixar de descartar `_test.go` cujo diretório
esteja no grafo E tenha `//go:embed` casando `.go`. Acrescentar ao
`-selftest` o caso `internal/strictjson/*_test.go` com veredito **1** (hoje o
selftest afirma 0), provando o detector por mutação antes e depois.

## 7. O que o advisor mudou

1. **Veredito: de GRAVE para CONTROLADO.** Eu ia rotular o conjunto GRAVE por
   causa do ponto cego do `strictjson`. O advisor apontou que o schema define o
   veredito contra a execução DO PLANO, e o plano não toca `internal/strictjson`
   — o defeito vai em `achados` com o seu conserto, mas não custa retrabalho ao
   plano. Rotular GRAVE inverteria o que a tarefa pediu.
2. **`internal/lexml` — acrescentado, e é a colisão mais provável do plano.** Eu
   tinha o pacote na lista dos 98 e não o destaquei. Fui ao precedente e ele é
   mais caro do que o advisor supunha: recusa DUPLA em `fb1d5fb6`, closure
   reverso de **410 pacotes**, **75,3 s estourados sob o cérebro** contra
   **29,3 s** com ele parado. Virou R3 + o passo novo R4.1b (pausar o cérebro).
3. **`TETO_DE_PACOTES=6` — eu havia LIDO e não usado.** Acima de 6 pacotes o
   pre-commit só avisa e deixa passar sem teste focado. Os seis pacotes do plano
   batem no teto exato. Virou R3b.
4. **R4 passo 1 alargado de go.mod/go.sum para os 98 diretórios.** O mecanismo de
   2026-09-08 é "atesta o worktree": edição não-commitada de outra sessão em
   qualquer pacote do grafo entra no hash. Conferir só go.mod deixava o buraco
   aberto.
5. **Verifiquei a linha que sustenta o veredito** em vez de supor:
   `.githooks/pre-commit:371` termina em `exit 1` — a guarda **aborta** o commit,
   não é advisória. Sem isso, CONTROLADO cairia para GRAVE.
