# ADR: x/sync errgroup para pipeline bloqueado

Data: 2026-06-24

## Decisao

Adotar `golang.org/x/sync v0.21.0` somente atras do adapter interno `internal/pipeline`, usando `errgroup` para paralelismo limitado, cancelamento por contexto e saida deterministica por indice.

## Escopo permitido

- `go.mod` e `go.sum`, somente na versao fixa `v0.21.0`.
- `internal/pipeline/`, como unico pacote autorizado a importar `golang.org/x/sync`.
- `data/ops/pipeline_errgroup_evidence.jsonl`, como evidencia bloqueada sem publicacao.

## Racional tecnico

O repo possui varios pools manuais com `sync.WaitGroup` e canais em caminhos de 10k conteudos. Isso dificulta ordenacao estavel, cancelamento, coleta de erro por indice e limite uniforme de concorrencia. `errgroup.SetLimit` e `errgroup.WithContext` resolvem essa base sem adicionar servico externo, fila distribuida ou runtime publico.

## Gates

- Import direto de `golang.org/x/sync` fora de `internal/pipeline/` deve falhar em `codex2-policy-enforcement`.
- O adapter deve manter saida ordenada pelo indice de entrada e ter modo fail-fast e modo all-errors.
- A dependencia nao aprova conteudo, nao altera `published_manifest`, nao renderiza HTML publico e nao escreve sitemap.

## Licenca e risco

Licenca BSD-3-Clause como modulo complementar oficial do Go. Risco principal e paralelismo mascarar erro parcial ou gerar saida fora de ordem; o adapter e os testes mitigam esse risco antes de migrar produtores massivos.
