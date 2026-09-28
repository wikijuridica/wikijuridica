---
name: commit-go
description: Use ao commitar mudança em Go, go.mod ou go.sum neste repositório — serialização, índice limpo e atestação do grafo.
---

# Commit de Go

## A sequência

```
flock /tmp/opt-wiki-commit.lock bash -c '...'   # commits Go serializam aqui
git add caminho/exato/do/arquivo.go             # chamada separada
git commit -F /caminho/da/mensagem.txt          # chamada separada
```

`add` e `commit` **no mesmo comando** fazem o pre-commit reprovar com *"índice
mudou durante compilação"*. `add` **por diretório** já varreu trabalho de outra
sessão três vezes. Mensagem por `-F` sempre, nunca `-m` com heredoc — e nunca
capture a saída do hook (`2>&1`) no mesmo arquivo passado a `-F`: isso sobrescreve
a mensagem e é irreversível. Hooks barram as três formas.

O lock de commit (`/tmp/opt-wiki-commit.lock`) é **separado** do lock pesado
(`/tmp/opt-wiki-agent-heavy.lock`), que a bancada diária segura por 70–90 min.

## O índice sujo é o que custa o orçamento

`go-index-compile-closure` compila o **ÍNDICE**, não o seu pathspec. Medido:
**77,6 s** com `internal/v2ingest` sentado no índice, **14,9 s** com o índice
limpo. Duas sessões atribuíram isso à carga e relançaram esperando load baixo —
diagnóstico errado nas duas: a máquina ociosa chega ao mesmo teto.

Esvazie o índice antes de pedir a vez a outra frente. E esperar no lock é
justamente a janela em que o índice muda: confira `git diff --cached --name-only`
**depois** de tomar o lock.

## Tocou o grafo do validador? A atestação vai no mesmo commit

Arquivo de `internal/v2ingest`, `cmd/ingest-v2-stock`, `go.mod` ou `go.sum`:

```
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock   # quem está no grafo (custo ~0)
git status go.mod go.sum                                                 # o disco tem de estar limpo
./tools/go-modern generate ./internal/v2ingest                           # atestação, no MESMO commit
```

O grafo hasheia o **diretório** e o `go.mod`/`go.sum` — até um `_test.go` novo
invalida, e 25+ testes reprovam **depois de ~10 min** de compilação. Em
2026-09-08 dois commits atestaram contra um `go.mod` sujo de um `go get` que
ninguém usava.

## Pre-commit reprovou

Corrija a causa. `--no-verify` é proibido e um hook o barra. Para escopar um
commit sem tocar a worktree, use pathspec: `git commit -F msg -- <paths>`.

Páginas v2 têm pipeline próprio: skill `commit-v2`.
