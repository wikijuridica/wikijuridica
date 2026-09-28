# Plano de recuperação do v1 — veredito com evidência

Investigação de 2026-07-28, 9 frentes independentes + refutação adversarial + reconferência direta.
Destinatário: o próximo Claude Code, que vai executar. Tudo abaixo é read-only e reproduzível de `/opt/wiki`.

---

## 0. Correção de premissa — leia isto antes de qualquer coisa

As 9 frentes caíram na mesma armadilha e todas se corrigiram. Ela vai te pegar também se você não fixar o discriminador agora:

**`data/editorial/authorial_mass_drafts.jsonl` (7.178 linhas, 41 MB) NÃO é v1.** É o próprio v2 reprojetado no schema de draft. Medido: 7.178/7.178 `unique_intent_id` contidos nos `intent_id` do `v2_pages`; 7.178/7.178 `title` e `opening` **byte-idênticos** à página v2 correspondente; as 5.641 divergências de corpo são 100% explicadas por uma seção extra "Perguntas frequentes" (o `faq` do v2 achatado pelo conversor). Divergência genuína de prosa: **0**. `draft_id` literal: `authorial-mass-draft-v2-serv-acao-regressiva-estado-cobra-servidor`.

**Discriminador de um comando** (decore, é o que separa as duas linhagens):

| campo | v1 real | v2 (inclusive `authorial_mass_drafts.jsonl`) |
|---|---|---|
| id | contém `::` (`seed::cenário::contexto`) | plano, sem `::` |
| `scenario_id` / `context_id` | preenchidos | `""` |
| `page_type` | ausente | presente (`guia_problema`/`pergunta`/`verbete`/`procedimento`) |
| onde vive | **só em git** (`git show 34d6df3d:`) | worktree |

```bash
head -1 data/editorial/authorial_mass_drafts.jsonl | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('V2' if d.get('page_type') and not d.get('scenario_id') else 'V1')"
```

Se você "recuperar" esse arquivo para o v2, você duplica o v2 dentro do v2 — cria near-duplicate exato onde não havia, e infla o inventário para 14.853 fazendo a meta parecer batida com metade sendo cópia. Esse é o pior desfecho possível desta frente.

**O v1 de verdade só existe em git**, e nenhum byte dele está vivo no worktree:
```
git show 34d6df3d:data/editorial/authorial_mass_content_expansion.jsonl | wc -l   → 9700   (~170 MB)
git show 34d6df3d:data/editorial/authorial_mass_drafts.jsonl            | wc -l   →  300
git show 34d6df3d:data/editorial/authorial_mass_section_chunks.jsonl    | wc -l   → 133327
```
Sobrevivem no disco só duas cascas **sem corpo**: `authorial_mass_candidate_selection.jsonl` (10.000 ids cartesianos, 0 registros com texto) e `authorial_mass_signature_applied_rewrites.jsonl` (8.248 registros com `raw_text_stored: False`). Mais dois ledgers de metadado: `commercial_content_factory_bridge.jsonl` (10.000 ids v1, 0 com corpo) e `priority_authorial_claim_graph.jsonl` (3.960, 0 com corpo).

---

## 1. Resposta direta ao dono

**Não há valor recuperável no texto do v1. Zero páginas. Não é uma estimativa conservadora — é 0 medido.**

A conta, com os gates determinísticos aplicados às 9.700 páginas do blob `34d6df3d` (n = 9.700, não amostra):

| gate determinístico | reprovam |
|---|---|
| `title` começando em minúscula | 9.700 (100,0%) |
| `meta_description` sem pontuação final (truncada) | 9.646 (99,4%) |
| menos de 2 fontes oficiais | 3.312 (34,1%) |
| conjuntos de fonte **distintos** para as 9.700 páginas | **27** |
| **passam em todos** | **0 (0,00%)** |

Nenhuma página v1 entra no v2 sem reescrita integral do título, da meta, do corpo e da pesquisa de fonte. Reescrever a partir do v1 é **mais caro** que escrever do zero, porque herda a moldura que causou o defeito.

**O que sobra de aproveitável, honestamente medido:** as intenções e a proveniência — e os dois valem quase nada, porque **já estão cobertos**:

- Os 9.700 ids do v1 são 27 seeds × 30 cenários × 21 contextos. São **27 temas**, não 10.000. Os 27 estão **todos** cobertos no v2, com mais profundidade (`aposentadoria-especial-negada` → 23 páginas v2, ex.: `prev-epi-eficaz-negativa`, `lei-8213-art-57`). Lacuna de tema: **0/27**.
- A keep-list da DEC-004 fala em "23.366 deep-links auditados". Contados os **distintos**: **45 URLs**. O v2 já tem **6.388** URLs distintas com proveniência completa. A keep-list superestimou o próprio ativo por não desduplicar — registre isso, é o achado que poupa a próxima pessoa de garimpar links.

### A conta real da meta (esta é a parte que muda o plano)

Números reconferidos hoje, direto do disco:

```
v2_pages:      680 shards, 7.739 linhas, 7.720 intent_id únicos
               → 7.675 ATIVAS (com sections, sem skipped)  |  64 skipped
portfolio_v2:  61 arquivos, 10.041 intents distintos, 0 com corpo
backlog:       10.041 − 7.675 = 2.366 intents especificados e NÃO escritos
teto do pipeline atual: 7.675 + 2.366 = 10.041
aprovação hoje: approval=true → 0 de 7.675
```

**Escrever todo o backlog do portfólio dá 10.041 páginas — 41 acima do piso de 10.000, margem de 0,4%.** Isso não fecha a meta: a meta é 10.000 **aprovadas**, e hoje há **zero** aprovadas. Qualquer atrito de gate (semântico, proveniência, banda de word count) derruba abaixo do piso.

*Nota de precisão sobre os `approval`:* das 7.675 ativas, 7.135 não têm o campo `approval` e 540 têm `approval: false`. Conferi a distribuição dos 540: são 10–13 por shard, uniformemente espalhados — é **flag de bloqueio por default da geração, não veredito de reprovação adjudicada**. Não reporte "540 reprovadas". O fato duro é o outro e é pior: **0 aprovadas**, ou seja, o atrito real ainda é **desconhecido e não medido**.

**Conclusão operacional:** o gargalo não é falta de conteúdo v1. É (a) 2.366 páginas por escrever e (b) 0 páginas adjudicadas. E o portfólio precisa de folga: planeje **+1.000 a +1.500 intents novos** especificados (não cartesianos, DEC-007) além dos 2.366, dimensionados quando o atrito real for medido no primeiro lote adjudicado. Sem essa folga, o executor escreve 2.366 páginas, chega a ~9,6k aprovadas e descobre o buraco depois de semanas.

---

## 2. O que exatamente foi condenado — e o que era bom

### O defeito é estrutura E texto, não só estrutura

DEC-004 (`docs/goal/DECISIONS.md:35`), literal:

> "os 10.000 textos bloqueados atuais reprovam no mérito editorial — são permutação de molde (12 headings idênticos ×4.599 registros, 14.327 pares near-duplicate, distância de Hamming mínima 0, frases mecânicas em 100% da amostra, 27 seed terms para 10.000 páginas). Publicá-los violaria as diretrizes do Google (scaled content abuse / doorway) e o próprio `/goal`. […] reaproveitando do estoque atual apenas o que tem valor: a taxonomia de intenções, as fontes oficiais específicas (23.366 deep-links auditados) e os metadados de demanda."

E o racional jurídico, que costuma ser esquecido: *"texto-molde em massa também é risco reputacional/disciplinar, não só risco de SEO"* (Provimento OAB 205/2021).

### A prova em texto cru — duas páginas irmãs

`git show 34d6df3d:data/editorial/authorial_mass_content_expansion.jsonl`, linhas 2400 e 2401. Elas diferem **apenas** no terceiro eixo do produto cartesiano:

```
[L2400] busca-apreensao-veiculo::brasileiro-exterior::cronologia-fatos
 title:  'busca e apreensão de veículo: brasileiro, cronologia fatos'
 h1:     'busca e apreensão de veículo: brasileiro exterior em cronologia fatos'
 meta:   'Entenda documentos, fonte oficial e riscos de busca e apreensão de veículo em
          brasileiro exterior e cronologia fatos; confira documento específico'
 opening:'No tema busca e apreensão de veículo com brasileiro no exterior e cronologia fatos,
          a leitura inicial confere contrato de financiamento, parcelas, notificação, mandado
          ou decisão, comprovantes de pagamento e dados do veículo antes'
 sec[0].heading: 'Provas iniciais de busca e apreensão de veículo em brasileiro no exterior e cronologia fatos'
 sec[0].text:    'A busca "busca e apreensão de veículo brasileiro no exterior atendimento online
                  cronologia dos fatos" descreve este problema: a pessoa esta fora do Brasil e
                  precisa entender como iniciar triagem remota com documentos digitais; …'
 fontes: ['https://www.planalto.gov.br/ccivil_03/decreto-lei/1965-1988/del0911.htm']

[L2401] busca-apreensao-veiculo::brasileiro-exterior::documentos-pdf
 title:  'busca e apreensão de veículo: brasileiro, documentos em PDF'
 h1:     'busca e apreensão de veículo: brasileiro exterior em documentos em PDF'
 meta:   'Entenda documentos, fonte oficial e riscos de busca e apreensão de veículo em
          brasileiro exterior e documentos em PDF; confira PDF completo, páginas'
 opening:'No tema busca e apreensão de veículo com brasileiro no exterior e documentos em PDF,
          a leitura inicial confere contrato de financiamento, parcelas, notificação, mandado
          ou decisão, comprovantes de pagamento e dados do veículo ante'
 sec[0].heading: 'Provas iniciais de busca e apreensão de veículo em brasileiro no exterior e documentos em PDF'
 sec[0].text:    'A busca "busca e apreensão de veículo brasileiro no exterior atendimento online
                  documentos em PDF" descreve este problema: a pessoa esta fora do Brasil e
                  precisa entender como iniciar triagem remota com documentos digitais; …'
 fontes: ['https://www.planalto.gov.br/ccivil_03/decreto-lei/1965-1988/del0911.htm']
```

Mesma fonte única, mesmo tronco de frase, mesma estrutura de heading, mesmo `human_problem` literal repetido. São a **mesma página duas vezes** com uma variável trocada. Um par irmão medido tem 32,3% das sentenças byte-idênticas e Jaccard 0.4015.

Some a isso o descuido de superfície, também em texto real:
- `'contestação Pix MED negada pelo: urgência, protocolo'` — o título corta em "pelo", falta "banco" (L4800).
- `'…a pessoa esta fora do Brasil…'` / `'segunda opiniao'` / `'juros abusivos credito pessoal'` — acentuação faltando em texto voltado ao público (L2400, L9000). Isso sozinho já é falha P0 do contrato PT-BR.

### O que era bom e NÃO deve ser descartado

1. **A taxonomia de intenção como conceito** — já foi absorvida e superada pelo `portfolio_v2` (10.041 intents com `distinct_because`).
2. **A disciplina de proveniência** — o v1 não tinha; o v2 tem, e é o principal ativo herdado do fracasso. Ver seção 7.
3. **Os section_chunks** (133.327 registros, corpos externalizados de 5.101 páginas): **valor só forense**. Se você algum dia medir o v1, mescle os chunks antes — 5.101 páginas têm `body_sections: null` e o corpo mora nos chunks (mediana 3.675 palavras, 24–30 seções). Medir sem mesclar reporta essas 5.101 como "thin de 188 palavras" e produz um veredito errado.

---

## 3. Rota recomendada — uma só

**ROTA D: não recuperar nada do texto. Do inventário de demanda, recuperar apenas o que for barato e verificadamente ausente do v2 — o que, medido, é ~nada. Fechar formalmente a frente v1 e realocar 100% do esforço para escrever o backlog do portfólio + expandi-lo com folga.**

Diga ao dono com todas as letras: **não vale recuperar o texto; e mesmo "só as intenções" rende praticamente zero, porque as 27 intenções-raiz já estão cobertas no v2.**

Por que as alternativas morrem:

**(A) Importação direta do texto v1 → MORTA.** 0/9.700 passam nos gates determinísticos. 100% dos títulos em minúscula, 99,4% das metas truncadas. E não passa nem no schema: o v1 grava `official_source_urls[]` como **array de strings cruas**; o v2 exige, por fonte por página, `{url, name, anchor_claim, verified_at, http_status}`. O gate é hard-reject em código — `internal/v2ingest/adjudicate_shard.go:711` declara `required: ["anchor_claim","name","url"]` e `internal/v2ingest/validate.go:666` emite `official_source_anchor_claim_missing:index=%d`. Um array de strings nem desserializa como objeto de fonte. Reprovação 9.700/9.700, não amostral.

**(B) Matéria-prima para reescrita → MORTA por custo negativo.** O corpo é mail-merge de 3 slots; não há frase aproveitável (ver L2400/L2401 acima). Reescrever o texto custa o mesmo que escrever do zero, mas **carrega a moldura** — o redator ancorado no v1 tende a reproduzir a estrutura de 24–30 seções repetidas. Pior: a fonte teria de ser pesquisada do zero de qualquer jeito (45 URLs para 9.700 páginas ⇒ ~102 afirmações distintas ancoradas na mesma URL, o que é fabricação de `anchor_claim` = **fraude de proveniência**, não engenharia).

**(C) Só as intenções → MORTA por redundância medida.** 27 seeds, 27/27 já cobertos no v2. O que o v1 tinha a mais eram permutações de cenário/contexto — que é exatamente o eixo proibido pela DEC-007 (portfólio não-cartesiano). Reimportar as permutações reintroduz o defeito na origem.

**(D) Nada + realocar → ESCOLHIDA.** É a única que produz página nova. O backlog de 2.366 intents já está especificado, limpo e anti-template por construção.

---

## 4. Plano de execução

### Fase 0 — Fechar a frente v1 (1 ciclo curto, barato, alto valor)

Não é burocracia: os contratos hoje **induzem o erro** que as 9 frentes cometeram.

**0.1 Corrigir `docs/goal/V1_V2_CONTENT_LINEAGE.md`.** Ele é a autoridade designada para esta pergunta e está stale. Linhas a corrigir e os valores medidos hoje:

| linha | diz hoje | valor real (medido 2026-07-28) |
|---|---|---|
| 9 | v2_pages = 6.584 ativas; drafts = 590 STALE | 7.675 ativas; drafts = **7.178** (já ingerido, não stale) |
| 49 | arquivos v2_pages = 445 | **680** |
| 52 | páginas ativas = 6.584 | **7.675** (7.720 ids, 7.739 linhas, 64 skipped) |
| 82 | 6.584 ativas vs 590 STALE | 7.675 vs 7.178 |
| 119 | gap = 10.000 − 6.584 = 3.416 | gap = **2.325** para o piso, mas o **teto do portfólio é 10.041** — ver §1 |
| 132 | 6.584 ativas | 7.675 |
| 159 | worktree 2026-07-15: 445 arquivos / 6.584 ativas / drafts 590 | atualizar para o estado de hoje |

**0.2 Adicionar ao mesmo doc a seção "authorial_mass_drafts.jsonl é v2, não v1"** com o discriminador da §0 e a prova (7.178/7.178 opening byte-idêntico).

**0.3 Registrar em `docs/goal/DECISIONS.md`** um DEC de encerramento: *o texto v1 não é recuperável; a keep-list da DEC-004 foi medida e vale 45 URLs distintas (v2 já tem 6.388) e 27 temas (27/27 cobertos); a frente v1 está encerrada; o blob `34d6df3d` fica como referência forense.* Sem isso, alguém reabre a pergunta em três semanas.

**0.4 Anotar em `MAESTRO_CODEX_LOG.md`** o quê/porquê, com o hash do blob.

### Fase 1 — Escrever o backlog de 2.366 (frente principal)

**Entrada:** os 2.366 intents do `portfolio_v2` que não estão no `v2_pages`. Todos já vêm com especificação completa — conferido: `distinct_because` 2.366/2.366, `reader_problem` 2.366/2.366, `long_tail_query` 2.366/2.366, `source_hints` 2.366/2.366, `lane` 2.366/2.366 (comercial 1.968 / informativa 398), `needs_source_research=true` em 1.311. Corpo: 0/2.366.

Exemplo real de spec de entrada:
```json
{"intent_id":"proc-regcivil-mudanca-nome-extrajudicial","page_type":"procedimento",
 "practice_area":"procedimentos","family":"registro-civil-online",
 "long_tail_query":"mudar meu nome direto no cartório sem processo judicial",
 "working_title":"Mudança de nome no cartório: como alterar prenome e sobrenome sem ação judicial",
 "reader_problem":"Pessoa maior de idade quer trocar o prenome ou incluir um sobrenome de família diretamente no cartório, sem passar pela Justiça.",
 "lane":"informativa","source_hints":["Lei 14.382/2021","LRP 6.015/1973 art. 56","LRP 6.015/1973 art. 57"],
 "needs_source_research":false,
 "distinct_because":"alteração imotivada de nome pela via administrativa uma única vez, procedimento distinto da retificação de erro e da averbação de divórcio"}
```

**Ferramentas — todas já existem, nenhuma a criar:**

| passo | ferramenta | papel |
|---|---|---|
| montar fila | `python3 tools/generate_v2_review_queue.py` | backlog portfolio_v2 → fila de escrita |
| medir gap sem escrever | `./tools/ingest-v2-stock --prepare-only` | write-free |
| escrever | pipeline sancionado de writing-mass **por família** (DEC-011) | conhecimento embutido no lote |
| auditar | `python3 tools/audit_v2_pages.py` | auditor canônico |
| finalizar | `tools/finalize-v2-review`, `tools/finalize-v2-review-wave` | adjudicação |
| commitar | `tools/commit-verified-v2-workflow-results` | **único** caminho de commit de `v2_pages` |

**Saída:** um registro por página em `data/editorial/v2_pages/<familia>-<shard>.jsonl` com o schema v2 completo: `intent_id, title, meta_description, h1, opening, sections[{heading,text}], faq[{q,a}], official_sources[{url,name,anchor_claim,verified_at,http_status}], internal_link_topics, lane, needs_source_research, word_count`.

**Lote:** por **família**, nunca por contagem arbitrária (DEC-011 — o conhecimento jurídico vive no lote). Famílias do backlog: 61 arquivos de portfólio; dimensione 1 workflow por família, com fiscal Fable vigiando os transcripts. Não misture famílias no mesmo lote: é assim que o vocabulário vaza entre páginas e o `ngram_dup_global` acende.

**Bandas de word count (gate, `tools/audit_v2_pages.py:236`)** — o redator precisa saber antes de escrever:
`verbete 350–700 · pergunta 400–800 · guia_problema 700–1400 · procedimento 500–1000`; mínimo de seções: `verbete 2, pergunta 2, procedimento 3, guia_problema 4`; `MAX_FAQ = 4`.

**Onde entra cada gate:**
1. na escrita — banda de word count, mínimo de seções, PT-BR acentuado, `distinct_because` honrado no corpo;
2. `audit_v2_pages.py` — anti-template (`ngram_dup_global`, NGRAM=12), thin, fonte;
3. `check-v2-body-near-duplicates` + `check-v2-body-semantic-duplicates` — duplicidade cross-shard;
4. `check-portfolio-v2-intent-distinctness` — distinção de intenção;
5. `check-v2-portfolio-source-hints` / `audit-v2-source-provenance` — proveniência;
6. `internal/v2ingest` (adjudicate_shard.go / validate.go) — hard-reject de schema e `anchor_claim`;
7. `finalize-v2-review` → `commit-verified-v2-workflow-results`.

**Como validar antes de escalar:** rode **uma família inteira** (não uma amostra) do começo ao fim, incluindo adjudicação, e **meça o atrito real** — quantas das N escritas chegam a `approval=true`. Esse número é a variável mais importante do projeto hoje e ninguém a tem. Só depois dimensione as ondas seguintes.

### Fase 2 — Expandir o portfólio com folga (em paralelo, não depois)

Com o atrito medido na Fase 1, especifique **+1.000 a +1.500 intents novos** sob a DEC-007 (não-cartesiano, misto, com teste contrafactual). Origem legítima: problema/documento/risco/etapa/cenário reais, não permutação. Cada intent nasce com `distinct_because` que sobrevive ao teste: *"se eu apagar esta página, o leitor perde uma resposta que nenhuma outra página do estoque dá?"* Se a resposta for não, o intent não nasce.

### Fase 3 — Adjudicação (o gargalo real)

0 de 7.675 páginas escritas estão aprovadas. Isso é uma frente inteira por si só e provavelmente precede a Fase 1 em prioridade: **não adianta escrever 2.366 páginas novas se o pipeline de aprovação não passa nenhuma**. Abra a Fase 3 como task independente e rode-a em paralelo desde o primeiro dia.

---

## 5. Guarda-corpos — obrigatórios

O estoque v2 é o produto. O que impede conteúdo v1 (ou lixo equivalente) de entrar sem gate:

1. **Caminho único de escrita.** `data/editorial/v2_pages/*.jsonl` só é escrito por `tools/commit-verified-v2-workflow-results`, ao fim do pipeline sancionado (`generate_v2_review_queue` → writing-mass → proveniência → verify → commit). Workflow paralelo que escreva direto no shard produz páginas órfãs sem adjudicação. Nunca editar `v2_pages` à mão.

2. **`ngram_dup_global` é intocável sem DEC.** `tools/audit_v2_pages.py:241`, `NGRAM = 12`. É o **único** gate que pega o defeito do v1 (500/500 na amostra medida). Ele dispara bastante em corpus jurídico (listas de documentos, janelas de datas — o código já tem uma exceção estreita e justificada para duas datas completas ligadas por marcador de intervalo). Quando um lote grande travar nele, a tentação será "calibrar". **Regra dura: afrouxar, elevar o NGRAM ou desligar exige DEC formal com evidência; nunca por conveniência de lote.** Afrouxar esse gate é literalmente reabrir a porta pela qual o v1 entrou.

3. **`anchor_claim` não se fabrica.** Gerador que lê a URL e escreve uma afirmação plausível é **fraude de proveniência**, não automação. `anchor_claim` só se escreve depois de ler a fonte específica daquela página. Um sinal de alarme mensurável: se a razão *páginas por URL distinta* subir muito acima da do v2 hoje (6.388 URLs para 7.675 páginas ≈ 1,2), é porque a pesquisa de fonte por página parou de acontecer. O v1 tinha 45 URLs para 9.700 páginas (215×) — esse é o número da doença.

4. **Falso-verde ativo no estoque canônico — não confie nele.** `data/editorial/authorial_mass_global_similarity_audit.jsonl` reporta `max_similarity: 0` e `high_risk_pair_count: 0`, mas com `compared_pairs: 80` de `expected_pairs: 23430435` e `global_all_pairs_compared: false` — **0,00034% de cobertura**. O próprio registro admite o escopo: `max_similarity_scope: "candidate_frontier_similarity_not_global_top_when_global_all_pairs_compared_false"`. Ler "0 pares de alto risco" como "estoque limpo" é exatamente o erro que criou o v1. Se precisar de veredito de duplicidade, use `check-v2-body-near-duplicates` / `check-v2-body-semantic-duplicates`.

5. **Contar intent, nunca linha.** O v1 tinha 10.000 linhas e 27 temas. Todo número de estoque neste projeto se conta em `intent_id` distinto **com corpo e ativo**. Se um relatório disser "X páginas disponíveis", exija o comando que produziu X.

6. **Nada entra por conversão de schema.** Não existe conversor v1→v2 legítimo, e não deve existir. Se alguém propuser um, a resposta é a tabela da §1: 0/9.700 passam.

---

## 6. O que NÃO fazer

| não fazer | evidência do porquê |
|---|---|
| Tratar `authorial_mass_drafts.jsonl` como estoque v1 a recuperar | 7.178/7.178 `opening` byte-idênticos ao v2; `drafts − pages = 0` (subconjunto estrito). Recuperar = duplicar o v2 dentro do v2. |
| Somar 7.178 (drafts) + 7.675 (v2) = 14.853 | É o mesmo conteúdo contado duas vezes. |
| Ler "10.000" do `authorial_mass_candidate_selection.jsonl` como páginas | 10.000 linhas, **0 com texto**; são 27×30×21 permutações. É a grade doorway condenada, não estoque. |
| Reingerir o blob `db6c8eb0`/`34d6df3d` "porque são 9.700 páginas prontas" | 0/9.700 passam nos gates determinísticos; schema de fonte incompatível por design (`validate.go:666`). |
| Re-autorar os 9.700 intents v1 | 27/27 seeds já cobertos no v2; os eixos extras são cenário/contexto — proibidos pela DEC-007. |
| Escrever anchor_claims em massa a partir das URLs do v1 | 45 URLs para 9.700 páginas ⇒ ~102 afirmações por URL, genéricas por construção = fraude. |
| Afrouxar `ngram_dup_global` para destravar lote | É o único gate que pega o defeito do v1 (500/500). |
| Declarar a meta fechada ao escrever os 2.366 | Teto = 10.041 (margem 0,4%), com 0 aprovadas hoje e atrito não medido. |
| Confiar no `authorial_mass_global_similarity_audit` | 80 pares de 23.430.435; `global_all_pairs_compared: false`. |
| Medir o v1 sem mesclar os `section_chunks` | 5.101 das 9.700 têm `body_sections: null`; sem mesclar, reportam-se como thin de 188 palavras (falso). |

---

## 7. Lição de engenharia — regras derivadas, para o contrato

A linha do tempo do v1 é a lição inteira:

```
2026-06-14 18:09  e1028afc  gera 300 drafts
2026-06-15 11:39  80c91b68  "p0 add 10k blocked authorial content stock" → 9.700 páginas
2026-07-06 10:31  09b150c9  DEC-004 condena o estoque
2026-07-09 11:30  dcc560fa  expansion e section_chunks zerados
```

**21 dias e 10.000 páginas entre GERAR e LER.** O erro não foi o gerador ruim — foi ninguém ter lido a saída antes de multiplicá-la por 10.000.

Regras para o contrato (`AGENTS.md` / `CLAUDE.md`):

1. **Ler antes de multiplicar.** Nenhum lote acima de ~50 páginas é gerado sem que 10 amostras do lote anterior tenham sido lidas por inteiro — o corpo, não o resumo do check. Check verde não substitui leitura. (Já está no contrato; o v1 é a prova do custo de ignorá-lo.)

2. **Eixo de multiplicação é doença, não escala.** Gerador que pega N seeds e multiplica por eixos de cenário/contexto produz N URLs sobre o mesmo assunto por construção. Escala legítima vem de **mais intenções reais distintas**, nunca de mais eixos sobre as mesmas. Teste contrafactual obrigatório por intent (DEC-007): *apagando esta página, o leitor perde uma resposta que nenhuma outra dá?*

3. **Densidade de fonte é métrica de primeira classe.** Razão *páginas por URL oficial distinta* é o indicador precoce mais barato do defeito: v1 = 215×, v2 = 1,2×. Medir por onda, alarmar quando subir.

4. **Proveniência é campo estruturado, nunca string.** `{url, name, anchor_claim, verified_at, http_status}` com hash. O v1 só tinha URL crua, e é por isso que ele é irrecuperável mesmo se o texto fosse bom — não há como auditar o que ele afirmava com base em quê.

5. **Métrica que não cobriu o domínio deve dizer isso no próprio registro.** O `global_all_pairs_compared: false` salvou esta investigação porque estava lá. Todo auditor amostral deve gravar cobertura e escopo no registro; auditor que reporta `0` sem cobertura declarada é falso-verde por design.

6. **Nome de arquivo não é linhagem.** `authorial_mass_drafts.jsonl` tem nome de v1 e conteúdo v2, e enganou 9 investigações independentes. Linhagem se prova por **discriminador de campo** (`page_type` presente + `scenario_id` vazio + ausência de `::`), nunca por nome ou por doc. E o doc de linhagem, quando stale, é pior que doc nenhum — por isso a Fase 0.1 não é opcional.

7. **Fracasso caro se encerra por escrito, com número.** A DEC-004 disse "reaproveitar 23.366 deep-links" sem desduplicar: eram 45. Toda keep-list de um fracasso precisa vir com a contagem distinta, ou vira promessa de valor que custa semanas para alguém descobrir que não existe.
