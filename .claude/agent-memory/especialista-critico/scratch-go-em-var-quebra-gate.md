---
name: scratch-go-em-var-quebra-gate
description: Arquivo .go solto em var/ vira pacote do módulo e reprova o gate de escopo do govulncheck; renomear para .go.txt resolve
metadata:
  type: feedback
---

Programa de medição de uma vez (one-off) NUNCA nasce como `.go` dentro da árvore
do módulo — nem sob `var/`, que é gitignored.

**Why:** em 2026-09-16 escrevi `var/oraculo_djen.go` para consultar
`v2ingest.ValidateBatchReasons` uma vez. Mesmo com `//go:build ignore`, o
`go list ./...` passou a enxergar o pacote `portaljuridico/var`, e
`TestSCAGovulncheckPackagesCobremTodoOModulo` (`internal/checks/sca_memo_test.go:532`)
reprovou com *"pacotes Go do módulo raiz fora do escopo do govulncheck
([./internal/... ./cmd/...]): [var]"*. O gate cobre o módulo inteiro; o escopo
declarado do govulncheck é só `internal` e `cmd`. `.gitignore` não protege de
nada aqui — quem enxerga é o `go list`, não o git.

**How to apply:** para rodar uma medição única que precisa de pacotes internos,
use `./tools/go-modern run caminho/arquivo.go` com o arquivo salvo como
`.go.txt` e copiado para um nome `.go` só durante a execução, ou aceite o
`.go.txt` como forma de arquivo (o `go run` exige `.go`, então a cópia é
necessária). Terminada a medição, o que fica no disco é o `.go.txt` e o
RESULTADO — nunca um pacote novo. Vale o mesmo para `testdata/`: o `go list`
ignora, mas caminho explícito ainda compila.

Relacionado: [[censo-de-detector-orfao]] (alcançabilidade é o que conta, não
menção) e a regra do projeto de rodar a bancada do pacote, não só o gate —
neste caso quem apanhou foi `./internal/checks/`, que eu só rodei porque o
advisor mandou.
