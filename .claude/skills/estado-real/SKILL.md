---
name: estado-real
description: Use antes de confiar em qualquer número que a documentação do repositório afirme sobre o estado do portal.
---

# Estado real

Documentação envelhece; o disco e o ar não. Antes de repetir um número que um
`.md` afirma, meça.

## O precedente que originou esta skill

Medido em 2026-08-19, o `CLAUDE.md` do repo afirmava, na linha 72:

> **Estado atual: publicação zero.** [...] nenhuma página jurídica pública.

Na mesma data havia **9.710 páginas no ar**, servidas em produção. A mesma
linha 117 ancorava o boot em `httpserver.go:243`, que é **linha de comentário**
sobre paginação — a âncora real é `httpserver.go:479-482`.

Duas afirmações do contrato mais lido do projeto, ambas falsas, nenhuma apanhada
por gate. **Divergência entre doc e medição é BUG a corrigir, não curiosidade.**

## Passo 1 — quantas páginas o manifest declara

A chave é `unique_intent_id`. **Não existe** `intent_id`: procurar por ele
devolve vazio e sugere manifest quebrado.

```bash
python3 -c "
import json
ids, n = set(), 0
for l in open('data/editorial/published_manifest.jsonl',encoding='utf-8'):
    l = l.strip()
    if l:
        n += 1; ids.add(json.loads(l)['unique_intent_id'])
print('linhas:', n, '| unique_intent_id distintos:', len(ids))
"
```

Em 2026-08-19: 9.710 linhas, 9.710 ids distintos (zero duplicata).

## Passo 2 — quantos HTMLs existem no disco

```bash
cd /opt/wiki && find public -name '*.html' -type f | wc -l
```

Em 2026-08-19: 9.930.

## Passo 3 — o que o sitemap SERVIDO realmente lista

Baixe do ar, não do disco: o que importa é o que o buscador recebe.

```bash
curl -s https://wikijuridica.com.br/sitemap.xml --max-time 20 \
  | grep -o 'https://[^<]*\.xml' \
  | while read s; do curl -s "$s" --max-time 25; done \
  | grep -o '<loc>[^<]*</loc>' | sed 's|<[^>]*>||g;s|https://wikijuridica.com.br||' \
  | sort -u > /tmp/sitemap_paths.txt
wc -l < /tmp/sitemap_paths.txt
```

`sitemap.xml` é um **sitemapindex**: contar `<loc>` nele devolve o número de
shards (dezenas), não de páginas. É preciso descer aos shards. Em 2026-08-19:
9.926 URLs.

## Passo 4 — compare os CONJUNTOS, não as contagens

Três cardinalidades iguais não provam que são o mesmo conjunto.

```bash
cd /opt/wiki && python3 -c "
import json
sm = set(open('/tmp/sitemap_paths.txt',encoding='utf-8').read().split())
man = set()
for l in open('data/editorial/published_manifest.jsonl',encoding='utf-8'):
    l = l.strip()
    if l: man.add(json.loads(l)['path'])
print('manifest:', len(man), '| sitemap:', len(sm))
print('manifest - sitemap (TEM QUE SER 0):', len(man - sm))
print('extras no sitemap:', len(sm - man), sorted(sm - man)[:5])
"
```

Resultado em 2026-08-19: `manifest (9.710) ⊆ sitemap (9.926) ⊆ public (9.930)`,
com `manifest - sitemap = 0` e `manifest - public = 0`. Os 216 extras do sitemap
são a home, os hubs de área e a paginação; os 220 extras de `public/` incluem
ainda as páginas de erro. `public > manifest` é esperado, não defeito.

## Passo 5 — amostre o ar com `curl`

```bash
u=$(sed -n '3p' /tmp/sitemap_paths.txt)
curl -s -o /dev/null -w "%{http_code} %{size_download}B\n" "https://wikijuridica.com.br$u" --max-time 20
```

Em 2026-08-19, `/administrativo/anulacao-revogacao-ato-administrativo/` devolveu
`200` com 26.222 bytes. Status **e** tamanho: 200 com 0 byte é página vazia
servida com cara de sucesso.

## Regras

1. Comentário e README não são fonte. O arquivo e o ar são.
2. Achou divergência → corrija na mesma sessão. Documentar não substitui resolver.
3. Toda afirmação numérica traz o método e o denominador. Sem isso é boato.
4. Gate verde não é prova; gate vermelho não é veredito. Leia a implementação do
   detector antes de decidir por ele.
5. Ausência de linha ≠ ausência do fato.
