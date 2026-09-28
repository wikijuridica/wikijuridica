---
paths:
  - "content/pages.json"
  - "content/*.json"
  - "content/*.jsonl"
  - "data/ai/extracoes_dispositivos.jsonl"
  - "data/ai/*.jsonl"
  - "data/editorial/*.jsonl"
  - "content/legal_cocitation_index.jsonl"
  - "tools/generate_v2_review_queue.py"
---

# JSON/JSONL escrito por Go — reserializar em Python infla o diff

Memorias de origem: `jsonl-de-produtor-go-reserializado-em-python.md`,
`pages-json-escapa-html-como-o-go.md`. O `paths:` foi alargado porque o caso das
7.959 linhas aconteceu em `data/editorial/refined_public_prose.jsonl`, que a
primeira versao desta regra **nao casava** — regra que nao carrega no arquivo do
proprio incidente nao protege ninguem.

Estes arquivos sao produzidos pelo `encoding/json` do Go. Regrava-los com o
default do Python muda **todas** as linhas sem mudar nada de conteudo, e o diff
deixa de dizer a verdade exatamente quando ele mais importa: no commit por
pathspec sobre arquivo que outra sessao tambem edita.

Duas diferencas, as duas medidas em 2026-09-10:

**Escape de HTML** (`content/pages.json` e todo JSON do `Encoder` do Go, que tem
`SetEscapeHTML(true)` por padrao): Go escreve `&`, `<` e `>` escapados; o
`json.dump` do Python nao escapa nenhum dos tres, nem com `ensure_ascii=False`.
Um gerador que trocou **2 campos** de proposito gravou **1.838 linhas** de diff,
porque 1.834 `&` de `source_url` de acordao do STF viraram a forma nao escapada.

**Separadores** (JSONL): Go escreve `{"a":"b"}`; o default do Python escreve
`{"a": "b"}`. Um gerador que trocava **um caractere** em
`data/editorial/refined_public_prose.jsonl` reserializou as 7.959 linhas e o
arquivo foi de 86.519.454 para 88.321.072 bytes.

## Como gravar

```python
json.dumps(registro, ensure_ascii=False, separators=(",", ":"))
```

e, para JSON com corpo HTML, trocar depois `&`→`&`, `<`→`<`, `>`→`>`
no texto (seguro: os tres nao aparecem na sintaxe do JSON, so dentro de strings).

Acrescente reparo idempotente que devolva os escapes se o disco ja tiver os
literais, compare o conteudo montado com o disco antes de gravar, e **prove por
teste que o numero de linhas mudadas e' o numero de campos declarados** — e' o
teste que mata o mutante.

Churn de arquivo inteiro tambem invalida atestacao de corpus
(`refinedcorpusfloor.Piso` compara `records`, `corpus_bytes` e `corpus_sha256` e
falha fechada). Confira o diff contra a copia preservada em `.agents/runtime/`
ANTES de commitar.

`content/legal_cocitation_index.jsonl` tem uma janela propria: ele e' regenerado
no **passo 2.6 do `deploy-publico`**, entre a republicacao (que reescreve
`pages.json`) e o restart (que le o indice). Fora dessa janela, regravar a mao
descasa o indice do que o processo serve.
