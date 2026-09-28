# Codex 2 Source Resolution Matrix

## Escopo

`codex2_source_resolution_matrix` agrega `data/research/codex2_source_audit_queue.jsonl` por host oficial, perfil de caminho e decisão de auditoria. Ela é uma macrocamada bloqueada de resolução/deduplicação de fonte oficial: reduz 4.800 tarefas em 7 grupos acionáveis, sem publicar, renderizar, copiar texto oficial, fazer scraping ou alimentar rascunho.

Ela existe para transformar 4.800 tarefas de auditoria oficial Codex 2 em grupos rastreáveis de fonte:
- lacunas que ainda exigem URL oficial mais especifica;
- metadados oficiais existentes que precisam de verificacao;
- oportunidades que apontam para a mesma autoridade, norma, orgao, canal oficial ou documento;
- blockers que impedem rascunho, readiness, review, render, sitemap ou publicacao.

## Politica

A matriz e bloqueada por definicao. Ela nao faz scraping, nao busca corpo bruto, nao armazena texto oficial, nao copia trechos, nao cria rascunho editorial, nao alimenta `content/pages.json`, nao escreve em `public/`, nao altera `data/editorial/published_manifest.jsonl`, nao entra em sitemap real e nao libera render.

Cada registro deve preservar linhagem suficiente para auditoria sem misturar papeis: `codex2_source_audit_queue_id`, oportunidade, seed/area/cenario/contexto quando existirem, autoridade oficial esperada, URL/hash ou host oficial quando disponivel, status de resolucao, motivo de deduplicacao, blocker acionavel e flags publicas falsas. URL oficial continua referencia/proveniencia, nao alvo de clonagem ou ingestao.

O check `codex2-source-resolution-matrix` exige `tasks=4800`, `needs_specific_audit=3930`, `verify_existing=870`, `hosts=4` e `publication_allowed=0` no estado vivo atual. Esses contadores derivam da audit queue regenerada e nao devem ser congelados em testes quando a frontier evoluir.

## Trabalho concorrente

Codex 2 pode desenvolver a camada em branch ou worktree independente para isolar diff grande, mas a integracao ao `main` deve editar os arquivos vivos para frente. Arquivo compartilhado nao deve ser substituido por snapshot da branch. Se `docs/`, `GOAL.md`, `CHECKPOINT.md`, `content/storage_contract.json`, `internal/checks` ou qualquer contrato comum tiver mudanca concorrente, a regra e ler os dois lados, preservar evolucao valida e aplicar forward-edit minimo; nao usar `git restore`, `checkout`, `reset`, `revert`, limpeza ou sobrescrita.

## Proximo comando executavel

Quando o gerador/check da branch Codex 2 estiver presente no workspace de integracao, a proxima validacao deve rodar:

```bash
./tools/generate-codex2-source-resolution-matrix
./tools/check-codex2-source-resolution-matrix
GOCACHE=/tmp/opt-wiki-go-cache go run ./cmd/check codex2-source-resolution-matrix --timings
git diff -- public content/pages.json data/editorial/published_manifest.jsonl .release-staging
git diff --check
```

Se qualquer comando produzir registros publicos, `render_allowed=true`, `sitemap_allowed=true`, `publication_allowed=true`, `public_path` preenchido ou texto oficial bruto armazenado, o estado correto e blocker P0 e correcao para frente da ferramenta antes de qualquer merge.
