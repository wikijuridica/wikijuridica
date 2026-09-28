---
name: verificar-citacao-legal
description: Use ao escrever ou auditar página que cite lei, artigo, súmula ou decisão judicial.
---

# Verificar citação legal

## Por que esta é a classe P1 permanente do projeto

Citação legal mal atribuída aparece em **~8% das páginas auditadas por humano** e
**nenhuma medição automática a detecta**: o texto está bem escrito, o número do
artigo existe, a lei existe — só que o artigo não diz aquilo. É o único defeito
com risco real sob a ética da OAB, e por isso não prescreve: continua P1 mesmo
depois de a página estar publicada.

Nenhum gate verde deste repositório cobre esta classe. A verificação é
procedimento, não check.

## Passo 1 — nunca cite de memória

Modelo de linguagem reproduz número de artigo plausível com fluência total. Toda
citação de lei, artigo, inciso, súmula ou decisão sai de **consulta viva à fonte
oficial**, feita agora, ou não sai.

Fontes oficiais primárias aceitas: `planalto.gov.br` (texto consolidado),
`in.gov.br` (Diário Oficial), `normas.leg.br` e `legis.senado.leg.br` (Rede
LexML/Senado), `stf.jus.br`, `stj.jus.br`, `atos.cnj.jus.br`, além das 54
entradas auditadas em `content/source_registry.json`:

```bash
python3 -c "
import json
for s in json.load(open('content/source_registry.json',encoding='utf-8'))['sources'][:10]:
    print(f\"{s['source_id']:<26}{s['base_url'][:64]}\")
"
```

## Passo 2 — resolva pelo gerador sancionado

`tools/generate_source_hint_catalog_normas_legbr.py` resolve a norma na API
pública de dados abertos do Senado (LexML) e **verifica ao vivo**. O que ele faz,
e que a verificação manual precisa reproduzir (`resolve_act`, linhas 94-127):

1. Consulta `legis.senado.leg.br/dadosabertos/legislacao/{tipo}/{numero}/{ano}`.
2. Exige resposta com **exatamente um** documento — ambiguidade é recusa.
3. Confere que o número devolvido **bate** com o número pedido, ignorando zeros
   à esquerda. É esta guarda que impede a má atribuição.
4. Exige que a URL final esteja sob `https://normas.leg.br/`.
5. `verify_url_live()` confirma **HTTP 200** ao vivo (HEAD, com fallback GET só
   para status; nunca lê nem armazena o corpo).
6. Falhando qualquer etapa, devolve `None` e **não registra nada**.

A docstring é o contrato: *"Nunca registra URL não verificada."*

## Passo 3 — registre a proveniência

Toda citação carrega **URL + data da consulta + status HTTP**. Sem os três, a
citação não é verificável e não entra na página.

```bash
curl -s -o /dev/null -w "%{http_code}  %{url_effective}\n" -L --max-time 20 \
  "https://normas.leg.br/?urn=urn:lex:br:federal:lei:1990-09-11;8078"
date -u +%Y-%m-%dT%H:%M:%SZ
```

Medido em 2026-08-19: essa URN devolve `200`, e a API do Senado
(`legis.senado.leg.br/dadosabertos/legislacao/lei/8078/1990?formato=json`)
também. Registre o par URL + data que você mediu, não o que esperava medir.

## Passo 4 — fonte inacessível: pule e registre, nunca invente

Órgão público brasileiro derruba consulta automatizada por WAF, 403 ou timeout
com frequência. Caso real medido em 2026-08-19, nesta mesma sessão:

```
https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm  ->  000 (exit 28, timeout)
https://normas.leg.br/?urn=urn:lex:br:federal:lei:1990-09-11;8078  ->  200
```

O Planalto não respondeu; a Rede LexML respondeu. Fonte inacessível **não**
autoriza escrever a citação de memória "porque eu sei que é assim" — autoriza
tentar outra fonte oficial e, não havendo nenhuma, não citar.

O procedimento correto é o mesmo do gerador: **não registrar**. Escreva a página
sem a citação, ou com a afirmação em forma que não dependa dela, e registre a
tentativa falha. Uma página com uma afirmação a menos é sã; uma página com uma
citação inventada é um defeito jurídico publicado — e o JSON-LD o propaga.

Vale a regra do contrato: fonte oficial com URL e data, **ou escreva "sem fonte
oficial"**. Nunca a terceira via.

## Passo 5 — o que auditar numa página já escrita

1. Todo número de lei/artigo/súmula do corpo tem proveniência registrada?
2. O artigo citado **diz** o que a frase afirma, ou só existe? Abra e leia.
3. A norma está **vigente** nessa redação? Revogação e alteração posterior são a
   causa mais comum de citação certa que virou errada.
4. Súmula e decisão: número, tribunal e teor conferem entre si?
5. A fonte é a **oficial primária**, não notícia, blog jurídico ou agregador.

## Proibições

- Proibido inventar decisão, ementa, artigo, citação, data ou resultado.
- Fonte oficial é **referência e proveniência, nunca corpo**: nada de cópia,
  espelho, scraping de conteúdo ou paráfrase mecânica. O texto é autoral.
- Proibido promessa de resultado (Provimento OAB 205/2021).
- Achou citação errada numa página no ar → é correção da mesma sessão, por
  gerador datado, nunca editando JSONL à mão, e nunca descartando a página.
