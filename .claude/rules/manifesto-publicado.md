---
paths:
  - "data/editorial/published_manifest.jsonl"
  - "internal/publishedmanifest/**/*.go"
  - "tools/check-shard-preservation"
  - "tools/run-daily-content"
  - "tools/generate-*"
---

# `published_manifest.jsonl` — chaves reais e por que ele derruba o servidor

Memoria de origem: `gerador-nao-apaga-publicada.md` (a secao do estoque). O
`paths:` inclui `tools/generate-*` porque o defeito nasce no gerador de pagina,
nao neste arquivo.

A chave do intent e' **`unique_intent_id`**, nao `intent_id`. Procurar por
`intent_id` devolve zero e faz parecer que a pagina nao esta publicada. Foi
assim que quase se declarou que uma citacao legal falsa nao estava no ar —
estava, inclusive no JSON-LD.

Outras chaves do registro: `path`, `canonical_url`, `html_sha256`,
`sitemap_sha256`, `release_gate_id`.

**Contar paginas publicadas** = distintos por `unique_intent_id`, nao linhas.

## `publishedmanifest.Validate` roda no BOOT

Uma unica issue neste arquivo impede o processo Go de subir — nao e' um aviso em
background. Coerencia de artefato e' o invariante que impede 404 e pagina orfa no
indice do buscador: toda pagina aqui tem HTML em `public/`, entrada no sitemap e
registro no indice de release, com os SHA-256 batendo.

## Pagina publicada nunca sai do estoque

Nem por piso de palavras, nem por assinatura de tese, nem por similaridade.
Esses filtros impedem que uma pagina ruim seja PUBLICADA; retira-la depois
quebra a coerencia do manifesto. Para tirar do ar existe a supersessao, que
preserva o texto.

Dono da rota = intersecao entre o shard commitado do proprio gerador
(`git show HEAD:<shard>`) e este manifesto. O prefixo do `intent_id` nao
distingue: as 122 sumulas antigas usam `sum-stj-` tanto quanto as novas.

**O caso, medido em 2026-08-20:** os geradores de pagina derivada liam `public/`
e pulavam toda rota existente — guarda de colisao correta **ate eles
publicarem**. Depois da primeira publicacao passaram a ver as PROPRIAS paginas
como rota alheia: o shard de sumulas caiu de 80 para 18 e **62 paginas redigidas
sumiram, sem erro**. A onda diaria rodaria isso toda madrugada.

Terceira regra que ficou junto: **o teto de paginas governa quanto se
ACRESCENTA** — duas passadas explicitas, publicadas primeiro sem teto. Ordenar e
cortar no limite ainda deixava escapar.

**A guarda:** `tools/check-shard-preservation` compara cada shard com HEAD e
reprova se registro ATIVO desapareceu. E' a etapa 3 de 8 de
`tools/run-daily-content` e PARA a onda antes de qualquer commit. Provou-se no
primeiro uso achando **34 paginas TROCADAS com as contagens intactas** (80->80 e
200->200): contador nao acusa troca.

Procedimento de publicacao: skill `publicar-lote`.
