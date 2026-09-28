# PORTFOLIO_BRIEF.md — Brief-mestre do portfólio editorial v2 (DEC-007)

Este documento instrui a construção do portfólio de intenções do portal (fase B do PLAN.md). Cada agente-pesquisador produz um arquivo JSONL de intenções para sua área, seguindo exatamente estas regras. O portfólio é laboratório bloqueado: nada aqui é público.

## O que é uma intenção válida

Uma intenção = um problema/pergunta/instituto/procedimento jurídico **materialmente distinto**, que uma pessoa real digitaria no Google em português brasileiro. Teste contrafactual obrigatório antes de criar a intenção: ela só existe se a resposta útil (regra, procedimento, documento, prazo, risco, fonte, decisão) for **diferente** da resposta de qualquer outra intenção já listada. Se a diferença for só de palavras ("com documentos", "em PDF", "urgente", "empresa com CNPJ"), NÃO criar — isso é doorway e é proibido.

## Tipos de página

- `guia_problema` — problema com intenção de contratação de advogado (lane `comercial`): a pessoa tem um conflito concreto e busca solução, possivelmente contratando atendimento 100% digital.
- `pergunta` — pergunta jurídica específica de cauda longa (lane conforme o caso): resposta direta e completa a uma dúvida pontual.
- `verbete` — instituto/termo jurídico explicado (lane `informativa`): o que é, base legal, quando se aplica, efeitos.
- `procedimento` — como fazer X pela via digital (lane conforme o caso): passo a passo real por canal oficial (gov.br, Meu INSS, consumidor.gov.br, e-notariado, juizado especial etc.).

## Regras jurídicas e de negócio

1. **Direito brasileiro correto e atual.** Terminologia técnica precisa. Nada de inventar prazo, artigo ou procedimento; se não tiver certeza da fonte, registre `source_hint` genérico do órgão correto e marque `needs_source_research=true`.
2. **BPC/LOAS, gratuidade e assistência pública**: lane `informativa`, nunca comercial.
3. **Ética OAB (Provimento 205/2021)**: nenhuma intenção pode pressupor promessa de resultado, ranking, preço ou captação sensacionalista.
4. **Jornada 100% digital é real**: intenções comerciais devem ser compatíveis com atendimento remoto (triagem WhatsApp, documentos digitais). Não é promessa falsa; é o modo de atendimento do escritório.
5. **Sem áreas de risco disciplinar**: nada de criminal sensacionalista; nada de caso concreto identificável.

## Schema do registro (uma linha JSONL por intenção)

```json
{
  "intent_id": "slug-ascii-unico-curto",
  "page_type": "guia_problema|pergunta|verbete|procedimento",
  "practice_area": "area-canonica",
  "family": "subgrupo-tematico",
  "long_tail_query": "consulta natural em PT-BR como digitada no Google",
  "working_title": "título de trabalho em PT-BR correto e acentuado",
  "reader_problem": "uma frase: quem busca isso e o que precisa",
  "lane": "comercial|informativa",
  "source_hints": ["orgao-ou-lei-1", "orgao-ou-lei-2"],
  "needs_source_research": true,
  "distinct_because": "meia frase: o que muda materialmente vs. vizinhas"
}
```

Regras do registro:
- `intent_id`: ASCII, kebab-case, prefixado pela área (ex.: `trab-verbas-rescisao-sem-justa-causa`), único no arquivo.
- `long_tail_query` e `working_title`: PT-BR natural com acentuação perfeita.
- `distinct_because`: obrigatório; é a prova do teste contrafactual.
- Proibido: pares de intenções que difiram apenas por urgência, formato de documento, canal de contato, cidade/UF (exceto quando a jurisdição muda a regra material), ou sinônimos.

## Qualidade da consulta

Boas: "empresa não depositou FGTS o que fazer", "diferença entre guarda compartilhada e guarda unilateral", "plano de saúde negou home care", "o que é usucapião extraordinária", "como registrar marca no INPI sem despachante", "voo cancelado direito a reembolso ou reacomodação".
Ruins (proibidas): "verbas rescisórias advogado online com envio de documentos em PDF", "guarda compartilhada urgência hoje protocolo de atendimento".

## Distribuição alvo

Cada agente recebe a área, subfamílias e a meta numérica. A meta é teto, não obrigação: se a área não sustentar N intenções materialmente distintas, entregue menos e explique — inflar com permutação é a única falha inaceitável.
