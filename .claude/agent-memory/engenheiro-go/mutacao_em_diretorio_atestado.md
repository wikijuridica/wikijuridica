---
name: mutacao-em-diretorio-atestado
description: Prova por mutação em arquivo de PRODUÇÃO do grafo do validador (cmd/ingest-v2-stock, internal/v2ingest e o fecho de imports) exige regerar a atestação por mutante; _test.go está fora do grafo e não exige
metadata:
  type: project
---

Em `cmd/ingest-v2-stock` e `internal/v2ingest`, escrever no arquivo **já invalida a atestação do
grafo do validador**, e os testes que usam o harness de transação (`newFinalizeFixture`) morrem em
`generated validator attestation does not match authenticated source graph` **antes** de alcançar o
predicado mutado. Regere entre a mutação e o teste, e de novo depois de restaurar:
`./tools/go-modern generate ./internal/v2ingest` (~15 s, envelopado).

**Why:** em 2026-09-16 três mutantes foram dados como mortos e dois derrubaram testes que não
alcançam. Parecia instabilidade sob carga (load ~12); era o gate de atestação matando tudo. Mutante
que morre pelo motivo errado não prova nada, e a explicação "flakiness" é a que ninguém confere.
O mesmo mecanismo explica testes que passam numa hora e falham na seguinte sem mudança de lógica:
alguém regerou a atestação no intervalo.

**How to apply:** antes de contar mutante morto nesses diretórios, leia a **mensagem** da falha, não
só o exit code. E ao entregar, declare que a atestação foi regerada e vai no MESMO commit de
`cmd/ingest-v2-stock` — `internal/checks` é outro commit. Ver
[[medir-a-premissa-do-briefing]]: aqui também a explicação fácil estava errada.

**Refinamento medido em 2026-09-16:** o grafo **exclui `_test.go`**
(`internal/v2ingest/validator_fingerprint_graph.go:669`), e as entradas são
`validatorFingerprintEntryDirs` mais o fecho de imports locais — `internal/v2supersessionintegrity`
entra por aí. Consequências: correção **só de teste** nesses diretórios **não** exige reatestar; e
mutante em arquivo de produção do fecho exige. Nem todo caminho alcança o validador: em
`cmd/ingest-v2-stock`, o gate de supersessão/recibo reprova **antes** de `PrepareTransactionPlan`,
então mutante ali morre pela mensagem do próprio gate. **Leia a mensagem: ela diz qual dos dois foi.**
