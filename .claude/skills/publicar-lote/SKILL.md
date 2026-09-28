---
name: publicar-lote
description: Use quando for promover páginas do acervo v2 para o ar.
---

# Publicar lote

## AVISO CRÍTICO: uma única issue no manifest derruba o servidor

`publishedmanifest.Validate` roda **no boot**, não em background. A cadeia real,
verificada no código:

1. `internal/publishedmanifest/publishedmanifest.go:982-984` — se a página do
   manifest não tem HTML em `public/`, acrescenta a issue
   `published_manifest_public_html_missing` (o vizinho `:979-981` faz o mesmo
   para ausência no sitemap, e `:986-988` para SHA-256 divergente).
2. `internal/httpserver/httpserver.go:479-482` — `New()` chama
   `publishedmanifest.Validate(...)` e, se `!Passed()`, devolve `errors.New(...)`.
3. `cmd/server/main.go:36` — o erro de `httpserver.New` cai em `log.Fatal`.

Ou seja: **uma linha órfã no manifest não degrada uma página, ela impede o
processo de subir.** Publicar sem coerência de artefato tira o portal inteiro do
ar. Por isso a coerência é pré-condição inegociável, e não um gate de estilo.

> `CLAUDE.md` cita esse mecanismo como `httpserver.go:243`. Aquela linha é
> **comentário** sobre paginação. A âncora real é `:479-482`.

## Passo 1 — a chave é `unique_intent_id`

O `published_manifest.jsonl` **não tem** campo `intent_id`. Procurar por ele
devolve vazio e faz parecer que o manifest está quebrado.

```bash
head -1 data/editorial/published_manifest.jsonl | python3 -m json.tool | head -20
```

Campos reais: `unique_intent_id`, `manifest_id`, `release_gate_id`, `path`,
`canonical_url`, `html_sha256`, `sitemap_sha256`, `index_policy`, `page_status`,
`author`, `reviewer`, `approved_at`, `reviewed_at`.

## Passo 2 — prove a coerência ANTES e DEPOIS

A regra é `manifest ⊆ sitemap ⊆ public`, com os SHA-256 batendo.

```bash
cd /opt/wiki && python3 -c "
import json, os
man = {}
for l in open('data/editorial/published_manifest.jsonl',encoding='utf-8'):
    l = l.strip()
    if l:
        r = json.loads(l); man[r['path']] = r['html_sha256']
pub = set()
for dirpath, _, files in os.walk('public'):
    for f in files:
        if f == 'index.html':
            rel = os.path.relpath(dirpath, 'public')
            pub.add('/' if rel == '.' else '/' + rel + '/')
        elif f.endswith('.html'):
            pub.add('/' + os.path.relpath(os.path.join(dirpath, f), 'public'))
print('manifest:', len(man), '| public:', len(pub))
print('manifest - public (TEM QUE SER 0):', len(set(man) - pub))
print('extras em public (hubs/paginacao/erro):', len(pub - set(man)))
"
```

Medido em 2026-08-19: manifest 9.710 ⊆ sitemap servido 9.926 ⊆ public 9.930;
`manifest - public = 0` e `manifest - sitemap = 0`. Os 220 extras são a home, os
hubs de área, a paginação e as páginas de erro — legítimos, e é por isso que
`public > manifest` não é defeito.

## Passo 3 — a promoção é transacional

O caminho real é `cmd/publish-v2-direct` (`main.go`, 2.106 linhas), que usa
`internal/publicrelease`. A ordem que `run()` executa:

1. Carrega `content/site.json` e **aborta** se a identidade editorial (nome +
   OAB) estiver incompleta — nunca hardcode o autor.
2. Regenera o índice de fontes a partir da proveniência real e **substitui** a
   rota institucional (anexar produziria `duplicate_content_route` na segunda
   execução e abortaria a promoção; o gerador é idempotente).
3. `acquireLock(root)` (`main.go:2029`) serializa a promoção — duas execuções
   concorrentes se atropelariam.
4. `writeRollbackSnapshot(root)` (`:2049`) copia o estado público **antes** de
   qualquer escrita.
5. `writeRehearsal(...)` (`:1960`) e só então `writeManifest(...)` (`:1873`).

Flags reais (`main.go:138-146`):

```bash
cd /opt/wiki && ./tools/go-modern run ./cmd/publish-v2-direct -limit 25 -mesh-report /tmp/mesh.json
```

- `-allow-public-write` — **default `false`**. Sem ela nada é escrito em
  `public/`: é o ensaio. Só passe quando a coerência do passo 2 estiver provada.
- `-limit N` (0 = todas) · `-published-at` / `-reviewed-at` (AAAA-MM-DD) ·
  `-root` · `-mesh-report`.

## Passo 4 — partição por severidade

Publica o que não tem erro grave ou crítico; o médio publica e refina depois.

- **Crítico, não publica:** sem corpo · campo obrigatório ausente · promessa de
  resultado (Provimento OAB 205/2021) · defeito de encoding · rota colidente ·
  reprovada por auditor · veredito conflitante.
- **Médio, publica:** fonte insuficiente · `word_count` entre 250 e 400 · gate
  estatístico refutado por medição reproduzível.
- Nunca afrouxe um gate para passar. Gate só se pula com medição própria
  commitada, e o salto fica gravado em `skipped_statistical_gates`.
- Página reprovada é **consertada**, jamais descartada: texto redigido foi pago.
