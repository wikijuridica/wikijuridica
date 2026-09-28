# WRITING_SPEC.md — Padrão editorial das páginas públicas (Fase B)

Autoridade: DEC-004/DEC-007. Este é o contrato de qualidade que cada página escrita deve cumprir. Redator (humano ou agente) que não cumprir qualquer item reprova a página inteira.

## 1. Princípio

Cada página é um artigo autoral que um advogado experiente escreveria para responder UMA consulta real. O leitor deve terminar a página sabendo: o que a lei diz de verdade sobre o problema dele, o que fazer agora, que documentos importam, que prazos correm e quando vale procurar advogado. Quem lê duas páginas do portal em sequência não pode reconhecer molde.

## 2. Substância obrigatória (o que separa artigo de doorway)

Toda página DEVE conter, integrado ao texto (não em listas mecânicas):
- **Base legal específica**: lei e artigo (ex.: "art. 477, §6º, da CLT"), súmula, resolução ou norma aplicável — correta e verificada. Citar o dispositivo no corpo, explicando em linguagem humana o que ele significa. Proibido inventar.
- **Prazos reais** quando existirem (prescrição, decadência, prazos procedimentais), com o cuidado técnico de indicar termo inicial.
- **Documentos que importam** para aquele problema específico e por que cada um importa.
- **Caminho prático**: via extrajudicial quando existir (reclamação no órgão, notificação, plataforma oficial) e via judicial (qual ação, qual justiça, juizado ou vara), sem juridiquês vazio.
- **O outro lado**: quando o pedido costuma NÃO prosperar; exceções; riscos. Artigo honesto tem contrapeso — é isso que constrói confiança e é exigência ética.
- **Exemplo concreto genérico** (sem caso identificável): situação hipotética curta que ancora o problema na vida real.

## 3. Naturalidade e variação (anti-molde)

- **Proibido esqueleto fixo.** A ordem e a quantidade de seções variam por página conforme o assunto pede. Página de prazo começa pelo prazo; página de negativa de plano começa pela negativa; verbete começa pela definição. Nada de "toda página abre com triagem de documentos".
- **Headings próprios do assunto**, informativos e variados ("Quando a justa causa pode ser revertida", "O que a Lei 9.656 diz sobre urgência e emergência"). Proibido reutilizar o mesmo heading em mais de ~1% das páginas; proibidos headings genéricos de molde ("Provas iniciais", "Triagem digital", "Contexto prático").
- **Frases-molde proibidas.** Nenhuma frase completa pode se repetir entre páginas (será verificado por n-gram). Fórmulas como "A busca X traz este problema", "sem afirmar prazo, valor ou resultado" estão banidas.
- **Extensão variável por substância**: verbetes 350–700 palavras; perguntas 400–800; guias de problema 700–1400; procedimentos 500–1000. Página não deve ser esticada nem truncada.
- **Parágrafos de verdade**: 2–5 frases, ritmo variado, conectivos naturais. Voz direta ao leitor ("você") com sobriedade. Sem bullet points em excesso; lista só quando lista é a forma certa (documentos, etapas).
- **PT-BR impecável**: acentuação, concordância, regência, crase e conectivos que formem uma relação sintática completa. Construção mecânica como `, com RGST, CDC e LGT continuam aplicáveis.` reprova; escreva, conforme o sentido, `, enquanto RGST, CDC e LGT continuam aplicáveis.`. Terminologia jurídica correta (ex.: "rescisão indireta", não "demissão indireta do empregado por culpa do empregador esclarecida"; "benefício por incapacidade temporária" com menção ao nome antigo "auxílio-doença" quando ajudar o leitor).
- **Arquétipos estruturais (anti-molde de POSIÇÃO, medição 2026-07-21 em N=7.722 —
  `data/ops/v2_structural_mold_measurement_20260721.json`).** O molde real detectado não é
  sequência dominante (top-20 ≤ 10,3%) e sim clones de heading exato (32× "documentos que
  sustentam o pedido", 23× "um exemplo prático") e FUNÇÃO fixa em posição fixa (341 páginas =
  4,4% fecham com "quando vale buscar advogado/orientação/apoio"; 26 variantes parafraseadas de
  caveat-negativa na penúltima seção). Regras executáveis pelo gerador:
  1. Cada página nasce com um de 8 arquétipos, escolhido por `hash(intent_id) mod len(subset)`
     sobre o subconjunto compatível com o `page_type` (determinístico, reprodutível):
     resposta-primeiro; passo-a-passo; tabela-critérios; cenários-de-risco; checklist-documental;
     linha-do-tempo; objeção-refutação; glossário-contextual.
  2. A caveat jurídica muda de POSIÇÃO/FORMA conforme o arquétipo (exceção embutida, passo que
     falha, desfecho por cenário, corpo da linha-do-tempo) — nunca é removida quando necessária,
     e nunca vira seção padrão de penúltima posição.
  3. Nenhuma FUNÇÃO de seção (caveat-negativa, fecho-advogado, exemplo-prático) pode ocupar a
     mesma posição relativa em mais de 5% do estoque; heading exato repetido continua limitado a
     ~1% e os campeões medidos ("documentos que sustentam o pedido", "um exemplo prático",
     "quando vale buscar orientação jurídica", "documentos que costumam ser exigidos", "por que a
     diferença importa na prática", "quando o pedido [de indenização] não prospera/avança/tende a
     não prosperar/não costuma prosperar") ficam BANIDOS para páginas novas e entram na fila de
     reescrita dos shards mais moldados (empresarial-p1 75%, procedimentos-15/09 71%,
     empresarial-r01, consumidor-r01/r03, bancario-p1, leis-06).

## 4. Lanes e CTA (ética OAB — Provimento 205/2021)

- **Lane comercial** (`guia_problema` e algumas perguntas): o corpo deve deixar claro, de forma natural, que o problema comporta atuação de advogado particular com atendimento 100% digital (triagem por WhatsApp, envio de documentos digitais, procuração eletrônica, atuação em todo o Brasil quando aplicável). Esse sinal fica NO CORPO (requisito paid-intent), integrado ao texto — nunca como panfleto. Sem promessa de resultado, sem prazo garantido, sem valores, sem "especialista nº 1", sem urgência artificial.
- **Lane informativa** (verbetes, BPC/LOAS, gratuidade, temas assistenciais): zero CTA comercial. Pode informar canais públicos (Defensoria, INSS, Procon, consumidor.gov.br).
- **Aviso informativo**: toda página tem nota de que o conteúdo é informativo e não substitui consulta jurídica individual (o template insere; o redator não precisa escrever).
- Autoria institucional: Rafael Toledo, OAB/RJ 227191 (vem de `content/site.json`; nunca escrever no corpo).

## 5. Fontes

- Toda afirmação material sobre lei/prazo/procedimento se ancora em fonte oficial específica listada em `official_source_urls` (planalto.gov.br com âncora de artigo, ANS, gov.br, TST, STJ etc.). Fonte é referência e proveniência — **nunca** copiar, parafrasear mecanicamente ou espelhar texto da fonte.
- 2–5 fontes por página, todas realmente usadas no texto. Exceção fechada: `tel-linha-no-meu-cpf-fraude` e `tel-roaming-internacional-conta-alta` podem ter exatamente 6 porque o gate jurídico vivo exige 6 classes canônicas distintas; a exceção só vale enquanto a matriz continuar 6/6, nunca se propaga por quantidade de `source_hints`, e a 7ª fonte sempre reprova. Fora desses dois recortes, artigos do mesmo diploma devem ser consolidados numa única referência quando isso preservar a proveniência, sem duplicar a fonte para contornar o teto.

## 6. SEO on-page

- `title`: 20–65 caracteres, único, com o termo da consulta de forma natural; sem clickbait.
- `meta description`: 70–160 caracteres, única, que responda "o que eu ganho lendo isto".
- `h1`: única, próxima da consulta mas não idêntica ao title.
- Headings h2 (e h3 quando fizer sentido) informativos.
- 3–6 links internos contextuais para páginas irmãs (o pipeline injeta candidatos; o redator indica âncoras temáticas).
- HTML final ≤ 50 KB, zero scripts (o renderizador garante; o redator entrega texto).

## 7. Formato de entrega do redator (por página)

```json
{
  "intent_id": "...",
  "title": "...",
  "meta_description": "...",
  "h1": "...",
  "opening": "1-2 parágrafos de abertura (sem heading)",
  "sections": [{"heading": "...", "text": "parágrafos separados por \n\n; lista com linhas iniciadas por '- ' quando apropriado"}],
  "faq": [{"q": "...", "a": "..."}],
  "official_sources": [{"url": "...", "name": "...", "anchor_claim": "que afirmação do texto essa fonte ancora"}],
  "internal_link_topics": ["tema-1", "tema-2"],
  "lane": "comercial|informativa",
  "word_count": 0
}
```
`faq` é opcional (0–4 itens) e só quando as perguntas forem reais e não repetirem o corpo.

Campos de honestidade de fonte (consumidos pelo gate de ingestão):
- `verified_at`/`http_status` em cada fonte são resultado de evidência HTTP da ferramenta, não declaração do redator. Fonte nova fica sem esses campos; fonte preservada só conserva o par completo quando a URL exata não mudou. Se um dos campos estiver ausente ou inválido, `--apply` substitui os dois pela data e pelo status da mesma tentativa live. Depois que os JSONL estabilizam, a operação obrigatória é: auditoria live `--scope incomplete`, `--apply`, nova auditoria live `--scope all` e check da evidência atual por `tools/audit-v2-source-provenance`, sempre com `--metadata-only --no-content-copy` nas chamadas live. Sem `--file`, a evidência do inventário global finalizado fica no singleton `data/source-registry/v2_source_provenance_live_evidence.jsonl` e termina com `--check --strict-current`. Com uma seleção exata de `--file`, a ferramenta grava um sidecar determinístico e independente em `data/source-registry/v2_source_provenance_live_evidence_sets/exact-<sha256-da-seleção>.jsonl` e termina com `--check` usando a mesma seleção; `--strict-current` é deliberadamente global e reprova `exact_files`. O sidecar exato não substitui a prova global nem autoriza release (`release_eligible=false`). A ingestão persiste a proveniência da página em `data/source-audit/v2_source_provenance.jsonl`. Metadata preenchida por memória, cópia entre URLs diferentes ou suposição de status reprova a revisão.
- `needs_source_research` (bool, top-level) + `source_research_note`: o redator NÃO conseguiu verificar uma fonte/claim. A página **reprova na ingestão** (`source_unverified_research_pending`) e vai para a fila de reescrita — nunca entra no estoque como auditada.
- Tombstone de intenção pulada (linha no lugar da página): `{"intent_id": "...", "skipped": true, "skip_reason": "..."}` — melhor pular do que inventar fonte. A ingestão reprova com `intent_skipped_by_writer` (fila de reescrita), preservando a contagem do lote. A única exceção no consolidador global é uma duplicata histórica preservada com `skip_reason=duplicate_intent_consolidated` e `superseded_by=<shard-finalizado.jsonl>`: `audit_v2_pages.py --global` e `ingest-v2-stock` exigem que outro shard finalizado contenha exatamente um registro ativo do mesmo `intent_id`; o original integral fica em `data/editorial/v2_superseded/`, com hash e flags públicas falsas. Tombstone comum, alvo ausente, autoapontamento ou intent divergente continuam reprovados e nunca reduzem silenciosamente o estoque.
- `word_count` usa a fórmula do gate (`bodyWordCount`): opening + headings + textos das seções + FAQ (q e a), tolerância ±10%.

Auditor canônico pré-ingestão: `python3 tools/audit_v2_pages.py <arquivo> [--expect-n N]` (ou `--global` para o estoque inteiro) espelha o gate — redatores e revisores validam com ele, nunca com auditor improvisado.
