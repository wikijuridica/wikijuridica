# Varredura: o mecanismo de refutação de gate por medição — existe, foi usado uma vez, e virou constante

Sessão read-only (PLAN MODE). Tudo abaixo é leitura de disco medida em 2026-09-15, load 5,96.

## 1. O mecanismo existe e tem nome: `skipped_statistical_gates`

Origem contratual: `docs/PRECEDENTES_DAS_ORDENS.md:141` — *"O salto fica registrado por página em `skipped_statistical_gates`."*

Única implementação no repositório: `cmd/publish-v2-direct/main.go:3899` (campo) e `:3957` (escrita).

```go
SkippedStatisticalGates: []string{
    "batch_global_similarity:refutado_por_tools/measure-v2-uniqueness",
    "anti_template_review_required:refutado_por_medicao_de_molde",
},
```

É um **literal hardcoded dentro do laço `for _, page := range pages`**. Não lê nada da página, não consulta medição, não varia.

**Medido** em `data/editorial/authorial_mass_manifest_transaction_rehearsal.jsonl`:
- 11.106 linhas
- **11.106 de 11.106** carregam exatamente o mesmo par de strings — 1 valor distinto, zero variação
- `checked_at`: 1 valor distinto (`2026-09-15`) em 11.106 linhas

O contrato diz "registrado por página". O que existe é uma constante carimbada em todas.

## 2. Exercido uma vez, em 2026-08-06, nunca mais

| artefato | commits | estado |
|---|---|---|
| `tools/measure-v2-uniqueness` | **1** (`ce0764bc`) | escrito no dia da refutação |
| `data/ops/v2_uniqueness_20260806.json` | **1** | mtime ago 6 14:17; `documents_compared: 9620` |
| `cmd/measure-molde-trigrama` | **1** (`d952eca4`) | **produtor órfão** |

`grep -rn "measure-molde-trigrama"` em `tools/ ops/ .githooks/ internal/ docs/ cmd/ .agents/` → nenhum invocador. Os únicos hits fora do próprio diretório são logs de compilação da bancada diária (`.agents/runtime/qualidade-diaria/*/suite-completa.log:3923`, `[no test files]`) e rascunhos da sessão de 2026-09-09 que o rodou à mão. **Nada o agenda e nada consome sua saída.**

## 3. A refutação é carimbada em páginas que a medição nunca viu

`measure-v2-uniqueness` comparou **9.620** documentos em 2026-08-06. O rehearsal carimba a refutação em **11.106**.

Subconjunto exato e defensável — seções abertas **depois** de 2026-08-06 (`tools/generate-v2-publication-severity`, comentários do CATALOG: `jurisprudencia` e `noticias` abertas em 2026-08-20, `diarios` idem):

- `jur-*`: **1.134** páginas
- `not-*`: **59**
- `dia-*`: **51**
- **total 1.244 páginas** que não existiam quando a medição refutadora rodou, todas carregando `refutado_por_tools/measure-v2-uniqueness`

Limite inferior geral: 11.106 − 9.620 = **1.486**. Diferença exata não medível: o artefato de unicidade não lista os documentos comparados.

As 1.134 páginas `jur-` são precedente qualificado derivado de fonte oficial do STJ — **a mesma família do corpus de acórdãos desta frente**.

## 4. Três réguas incomensuráveis na mesma cadeia

| elo | arquivo:linha | shingle | limiar | dígitos |
|---|---|---|---|---|
| refutação (evidência) | `tools/measure-v2-uniqueness:50` | **8** | — | preservados |
| gate citado no achado | `internal/v2bodyneardup/neardup.go:62,65` | 5 | 0,70 | preservados |
| **gate que decide publicação** | `internal/quality/quality.go:84,743` | 5 | **0,82** | preservados |
| gerador de acórdão | `cmd/generate-acordao-pages/main.go:102,103,2187` | **3** | 0,70 | **neutralizados** |

Dois pontos que corrigem o enunciado da frente:

1. **Nenhuma dessas réguas recusa publicação hoje.** Medido no `v2_publication_severity.jsonl` (11.206 linhas): `critical_reasons` contém **um único motivo**, `intencao_pulada_deliberadamente` (100). Similaridade aparece só em `medium_reasons` — `batch_global_similarity_refutado_por_medicao` (5.600) e `blocker_pipeline:anti_template` (2.089) — e **médio publica**. E `cmd/publish-v2-direct` **não chama `internal/quality`** (grep por `quality.`/`neardup`/`nearDuplicate` no arquivo devolve só um comentário em `:755`; o único chamador de `quality.AnalyzeText` fora de teste é `cmd/content-lab/main.go:31`). O 0,82 de `internal/quality/quality.go:84` morde na suíte, **não no caminho de publicação**.

   Então a divergência real é esta: **o publicador classifica similaridade como MÉDIO e publica; o gerador recusa, a 0,70 em 3-gramas com dígitos neutralizados, conteúdo que o publicador aceitaria — 532 de 1.260 candidatos.** O elo mais severo da cadeia é o produtor, e ele é o único que não passou por calibração.
2. **A evidência que refutou o gate usou a régua mais permissiva das três** (8-gramas). "Zero pares similares" a 8-gramas não fala sobre 3-gramas: janela maior casa menos.

## 5. A medição órfã já refuta a régua do gerador

`data/ops/molde_trigrama.jsonl` — 2 linhas, ambas 2026-09-09, ambas sobre `stj-tema-derivado-01.jsonl`:

```
shingle 3, limiar 0,70, dígitos neutralizados
1.070 páginas · 571.915 pares · máximo 0,6627 · pares_acima = 0
```

A mesma régua (3-gramas, dígitos neutralizados, 0,70) que **não acusa nenhum par em 571.915** comparações de páginas de Tema já publicadas recusa **532 de 1.260** candidatos de acórdão (42,2%) dentro de `cmd/generate-acordao-pages`.

**Uma diferença de montagem está medida no código.** `cmd/measure-molde-trigrama/main.go:216-226` monta o corpo como `Opening + Sections[].Text + FAQ.pergunta + FAQ.resposta`. `cmd/generate-acordao-pages/main.go:2153-2169` (`corpoDaPagina`) monta o mesmo **mais `secao.Heading`** (`:2158`) — rótulo emitido pelo template, idêntico entre páginas da mesma família. O gerador inflaciona o próprio score com uma camada que o instrumento de medição não conta. **Magnitude do efeito: não medida.**

**Confundidor honesto:** as populações também diferem (1.070 páginas de Tema já publicadas × 1.260 candidatos de acórdão). Não é possível atribuir os 42,2% só à montagem sem rodar a régua do gerador sobre o corpus de Tema — **não medido nesta sessão** (read-only, e exigiria passada de geração).

O comentário de `cmd/measure-molde-trigrama/main.go:15-16` afirma 32 pares ≥ 0,70 em 43 páginas sobre 10.141 páginas vivas (0,4%). **Essa passada não está no JSONL** — o artefato só tem as duas linhas de um shard. Número do comentário: não reproduzível pelo ledger.

## 6. Precedente das 46 (e das 29): consertou-se o DETECTOR

O caso do contrato está em `docs/PRECEDENTES_DAS_ORDENS.md:273` e `docs/goal/MAESTRO_CODEX_LOG.md:4527`: detector de promessa OAB acusou 46 páginas, as 46 eram falso positivo (página *negando* promessa, ou *citando* anúncio abusivo de terceiro).

Há um **segundo caso, medido e documentado no código**: `tools/generate-v2-publication-severity:225-236` — **29 páginas bloqueadas, 29 falso positivo**, e *"Onze delas já tinham human_verdict APROVADA — o detector contradisse auditoria humana já feita."*

**Como foi resolvido, nos dois casos: corrigindo o detector na causa.**

- **As 29**: commit `4797226d fix(oab): detector de promessa parava 29 paginas boas — as 29 eram falso positivo`. Correção nomeada: *"olhar a SENTENÇA INTEIRA, não a vizinhança imediata"* → `NEGATION_IN_SENTENCE` (:238) e `LEGAL_GUARANTEE_TERM` (:250), que isenta "garantia real/legal/contratual" — vocabulário jurídico, não promessa.
- **As 46**: `MAESTRO_CODEX_LOG.md:4527` as registra como *"erros próprios, achados e corrigidos antes de publicar"* — corrigidas na causa antes de qualquer publicação. **Commit específico não localizado nesta sessão**; não atribuo o mesmo hash aos dois casos.

**Nenhuma exceção por página foi criada. Nenhuma página foi publicada com o defeito em aberto.** O precedente deste repositório é: detector errado se conserta, não se contorna.

## 7. O único override por página existe e foi exercido 4 vezes

`tools/generate-v2-publication-severity:733` e `:742` — `reprovacao_superada_por_reparo_verificado`.

Régua (linhas 728-731): `todos_reparados = bool(reprovacoes) and reprovacoes.issubset(reparados)` — *"Reparo parcial NÃO libera: se o auditor apontou dois defeitos e só um sumiu, a página segue reprovada."*

Medido no JSONL: **4 páginas de 11.206**. Criado em `3252e4e5 feat(auditoria): reparo verificado — o caminho de volta que nao existia`.

É o único mecanismo do repositório que aceita evidência **por página** contra um veredito. A porta existe; 4 páginas passaram por ela.

## 8. O instrumento de severidade mente sobre si mesmo em dois lugares

`data/ops/v2_publication_severity_summary.json` e `data/editorial/v2_publication_severity.jsonl` têm **mtime idêntico ao nanossegundo** (2026-09-15 12:24:28.372740013) — mesma execução. Mesmo assim:

| campo | summary | contagem linha a linha do JSONL |
|---|---|---|
| `critico` | 119 | **100** |
| `intencao_pulada_deliberadamente` | 119 | **100** |
| `sem_fonte_oficial` | 119 | **100** |
| `batch_global_similarity_refutado_por_medicao` | 5.603 | **5.600** |
| `records` | 11.206 | 11.206 ✓ |

`by_severity` do summary soma 11.225 ≠ `records` 11.206. A contagem linha a linha fecha exato: 769 + 10.337 + 100 = 11.206. Os contadores vivem em `:801-807` (`counters[severity] += 1`, `reasons_count[...] += 1`) e o summary os consome em `:913`, enquanto `records` sai de `len(rows)` (`:912`) — duas fontes distintas para o mesmo fato. **Causa exata da divergência de 19: não lida nesta sessão.** A divergência em si é FATO, medida dos dois lados.

E `tools/generate-v2-publication-severity:911` grava `"generated_at": "2026-08-06"` como **literal hardcoded**, num arquivo regenerado hoje. Quem lê o summary para saber quantas páginas estão travadas lê 119 (erro de +19) com data de 40 dias atrás.

## 9. `intencao_pulada_deliberadamente` não é refutação de gate

Convém separar, porque o enunciado da frente põe os dois lado a lado.

`internal/v2ingest/v2ingest.go:130-135` — `Skipped bool` / `SkipReason string` é o **tombstone de honestidade do redator**: a intenção foi deliberadamente não escrita por falta de fonte. `internal/v2ingest/validate.go:559-560` reprova com `intent_skipped_by_writer:<motivo>`. `tools/generate-v2-publication-severity:693` promove a crítico.

São **100 lápides, não 100 páginas boas travadas**. Não há corpo para publicar. Nada a refutar aqui.

## 10. Nenhum gate consulta a IA local

`grep -rln "11434|ollama|Ollama"` em `internal/checks/ internal/quality/ internal/v2ingest/ internal/publicrelease/ internal/v2bodyneardup/` → **zero arquivos**.

- `internal/factorymetrics/factorymetrics.go:12` descreve a cascata como *"T0/T1/T2 sem LLM/rede"*.
- `internal/v2bodysemanticdedup/dedup.go:24-31` diz de si que é **TIER 1, "ZERO dependência nova"**, e que o TIER 2 (embeddings ONNX) *"exige ADR/licença/benchmark"* — é upgrade-path documentado, **não construído**. `DefaultCosineThreshold = DefaultRawTFCosineThreshold = 0.55` (`:89`, `:93`): o default é cosseno de TF cru, não embedding.
- `cmd/publish-v2-direct/main.go:2508` lê `data/ai/embeddings/ativo.json` (escrito pelo cérebro), mas só para decidir se o `llms.txt` **anuncia** a ferramenta `buscar_semantico` (`buscaSemanticaArmadaNoDisco`, :2513-2516). Não decide nada sobre conteúdo.
- `internal/fiscalization/t4.go:27-29` diz de si mesmo: *"Mesmo quando aprova, o resultado significa somente que essas rubricas não encontraram o defeito que procuram; nunca é decisão de publicação"*. As duas lentes (`GroundedRefuter`, `RubricJudge`) são determinísticas.
- `internal/cerebro/gate.go` é o **inverso** do que a pergunta procura: é gate determinístico (regex + `oabgate.CheckResposta` + verificação de citação em mundo fechado) aplicado **sobre** o que a IA produz, no caminho da rede social. A IA é julgada, nunca consultada.

**O trilho offline que existe** são os vereditos de agente que o censo lê de `.agents/runtime/` (`generate-v2-publication-severity:517-518`, `os.walk` e não `glob`, porque `glob` ignora componentes com ponto): 141 arquivos, 1.742 intents. Deles saem `reprovada_em_auditoria_humana`, `veredito_conflitante` e os 131 `reprovada_por_agente_sem_justificativa`. É julgamento por contexto — assíncrono, gravado em arquivo, fora do caminho do gate.

## Síntese

O contrato abriu a porta ("gate estatístico refutado por medição é pulado, com a evidência gravada"). Alguém passou por ela **uma vez**, em 2026-08-06, com uma medição de corpus inteiro — e o que ficou no código foi uma **constante de duas strings** carimbada em todas as páginas desde então, inclusive em 1.244 que a medição nunca viu.

O caminho **por página** existe (`reprovacao_superada_por_reparo_verificado`) e tem 4 usos: medir caso a caso é trabalho que não escala.

O instrumento que mede exatamente a divergência desta frente (`cmd/measure-molde-trigrama`) foi construído, rodou duas vezes num shard, e é órfão.

O precedente das 46 e das 29 diz o que é aceitável aqui: **detector que produz falso positivo se conserta na causa** — não se contorna por exceção, e não se publica com o defeito em aberto.
