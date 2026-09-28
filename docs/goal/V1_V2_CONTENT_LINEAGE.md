# V1 vs V2 — Linhagem do Conteúdo Editorial (referência permanente)

> **Documento canônico de esclarecimento.** Vale para QUALQUER agente — Claude Code ou Codex — que toque `data/editorial/`, os gates, a cadeia de release ou os números de estoque. Existe para acabar com a confusão recorrente entre o estoque **v1** (legado condenado) e o estoque **v2** (canônico, autoral). Em conflito com a leitura solta de `DECISIONS.md`, **este documento reflete o estado EXECUTADO do worktree**, verificado em 2026-07-15. Correção só para frente: se o estado mudar, atualize este arquivo — nunca reintroduza a ambiguidade.

## Regra de ouro (leia isto antes de qualquer coisa)

1. **v1 é legado MORTO, recuperável somente no git.** Nunca é fonte de conteúdo. Proibido copiar, parafrasear, "re-autorar fielmente" ou reintroduzir qualquer corpo, `opening`, `meta`, `heading` ou `reader_problem` do v1 — é *doorway* condenado (DEC-004). Reintroduzir texto v1 é regressão P0 e fraude editorial.
2. **v2 é a ÚNICA fonte-alvo dos 10.000.** Vive em `data/editorial/v2_pages/*.jsonl`. Todo intent novo dos 10k nasce v2 (formato `WRITING_SPEC.md` §7), passa pelo auditor canônico e é ingerido para `authorial_mass_drafts.jsonl`.
3. **Nunca confundir os dois números.** `v2_pages/*.jsonl` = **FONTE** canônica (**7.675** páginas ativas em 2026-07-28 — 7.739 linhas − 64 skipped, 680 shards; cresce). `authorial_mass_drafts.jsonl` = **ESTOQUE** derivado re-ingerido (**7.178** linhas em 2026-07-28, 100% `draft_status=authorial_mass_draft_blocked`, 0 aprovadas). A distância entre eles é **ingestão/aprovação pendente**, não conflito v1/v2.
4. **As constantes `300` e `9700` no código Go são do v1** e só valem como *fallback* quando NÃO existe `stock_manifest.json`. Com manifesto, o manifesto manda. Número v1 hardcoded ≠ verdade do estoque.
5. **A virada v1→v2 já foi EXECUTADA (2026-07-09), não é pendente.** As DECs a descrevem no futuro/condicional ("será substituído"); o worktree prova que está feita. Este documento existe para fechar exatamente essa lacuna de tempo verbal.

---

## 1. O que foi o v1 (o estoque cartesiano condenado)

O v1 era a primeira "fábrica de 10.000 páginas": um **produto cartesiano** de apenas **27 seed terms × cenário (30) × contexto (21)**, materializado em três arquivos:

| Arquivo | Linhas v1 | Papel |
| --- | --- | --- |
| `data/editorial/authorial_mass_drafts.jsonl` | 300 | rascunhos iniciais |
| `data/editorial/authorial_mass_content_expansion.jsonl` | 9.700 | expansão cartesiana |
| `data/editorial/authorial_mass_content_expansion_section_chunks.jsonl` | 133.327 | corpos externalizados |

`scenario` e `context` eram **modificadores de entrega/formato** (`prazo-urgente`, `whatsapp-advogado`, `documentos-pdf`, `sem-sair-casa`, `cartorio-digital`) — não tópicos jurídicos distintos. Isso gerava ~360 páginas por seed diferindo só por modificadores genéricos, inclusive combinações **juridicamente sem sentido** ("guarda compartilhada cobrança indevida com comprovantes").

**Condenação (mérito editorial, não infra):** registrada em **DEC-004** (`docs/goal/DECISIONS.md:35`) como advogado e editor-chefe — os 10.000 textos são permutação de molde: **12 headings idênticos ×4.599 registros, 14.327 pares near-duplicate, distância de Hamming mínima 0, frases mecânicas em 100% da amostra, 27 seed terms para 10.000 páginas**. Publicá-los violaria as diretrizes do Google (*scaled content abuse / doorway*) e o próprio `/goal` ("never mechanical, templated or AI-sounding"), além de risco disciplinar (Provimento OAB 205/2021). **DEC-007** (`DECISIONS.md:53`) reforça: a expansão cartesiana é proibida (seção 16 do anexo do goal) e substitui a taxonomia por intenções **materialmente distintas** com teste contrafactual. Medições independentes das investigações confirmam o *doorway*: páginas irmãs de mesmo seed/mesmo cenário têm 2º heading **byte-idêntico** e citam **uma única fonte idêntica**; Jaccard 5-gram médio 0.312 (baseline cross-seed 0.107).

**v1 não foi apagado — foi condenado e substituído.** Continua **integralmente recuperável no git**, nada removido da história:
- Commit `9a5495b9` (2026-07-06, "portfolio v2 nao cartesiano") — v1 intacto (drafts=300, expansion=9.700, section_chunks=133.327). Âncora de recuperação citada na **DEC-012**.
- Commit `34d6df3d` ("Reforca gates P0") — último commit com v1 íntegro (`git show 34d6df3d:.../authorial_mass_content_expansion.jsonl` = 9.700 linhas).

---

## 2. O que é o v2 (o estoque canônico e autoral)

O v2 é a fábrica redesenhada (**DEC-007**, **DEC-009** em `DECISIONS.md:73`, **DEC-011** em `DECISIONS.md:88`). A diferença estrutural: **a qualidade nasce na FONTE**, não em reescrita mecânica.

- **Formato** (`WRITING_SPEC.md` §7, linhas 49–72): um JSON por página com `intent_id`, `title`, `meta_description`, `h1`, `opening`, `sections[]{heading,text}`, `faq[]`, `official_sources[]{url,name,anchor_claim}`, `internal_link_topics[]`, `lane` (comercial|informativa), `word_count`.
- **Anti-molde** (`WRITING_SPEC.md` §3): proibido esqueleto fixo; headings reutilizados ≤1%; nenhuma frase completa repetida (n-gram); extensão variável por `page_type`.
- **Intenções materialmente distintas** (DEC-007, teste contrafactual): a dimensão só vira página se mudar **regra, procedimento, documento, prazo, risco, fonte ou resposta útil** — nunca permutação de keyword. Quatro tipos de página: guias de problema (lane comercial, CTA WhatsApp contextual), perguntas jurídicas específicas (Q&A de cauda longa), verbetes de institutos/termos, guias de procedimento digital.
- **Controle em escala pelos GATES** (**DEC-017**, `DECISIONS.md:134`): o subsistema de reescrita mecânica do v1 está DESLIGADO no v2; redator-agente escreve com fontes oficiais, o auditor canônico (`python3 tools/audit_v2_pages.py`) confere, similaridade de corpo < 0.70, e a fila de revisão de agentes trata as falhas. **Máquina nunca inventa prosa pública.**
- **Honestidade de fonte** (WRITING_SPEC §7): `verified_at`/`http_status` vêm de evidência HTTP, não de declaração; `needs_source_research=true` reprova na ingestão (`source_unverified_research_pending`). Fonte oficial é proveniência, nunca corpo.

**Estado medido do v2 hoje (worktree, 2026-07-15):**

| Métrica | Valor |
| --- | --- |
| Arquivos `data/editorial/v2_pages/*.jsonl` | 445 |
| Finalizados / `.partial` (ruído efêmero) | 441 / 4 (48 linhas) |
| Linhas finalizadas | 6.641 |
| **Páginas ATIVAS (sem `skip_reason`)** | **6.584** |
| Skipped | 57 = 17 tombstones DEC-020 + 40 skips editoriais honestos |
| `intent_id` distintos | 6.624 (reconcilia 1:1 com `portfolio_v2`) |
| Colisões `active+active` | **0** (unicidade global limpa) |
| Passe dos gates estruturais determinísticos | ~99,7% (~18 falhas: 9 title, 9 meta, 1 word_count) |

> Nota de contagem: "6.689" é o total de **linhas cruas** (finalizadas + `.partial`). O número operacional é **6.584 ativas**.
>
> **Atualização 2026-07-28:** 680 shards, 7.739 linhas, 64 skipped ⇒ **7.675 ativas**; `authorial_mass_drafts.jsonl` re-ingerido = **7.178 linhas** (100% `draft_status=authorial_mass_draft_blocked`; `publication_allowed:true` = 0). A tabela acima é o snapshot histórico de 2026-07-15.

---

## 3. A virada foi EXECUTADA (correção do tempo verbal)

**Esta é a raiz da confusão entre as IAs.** A **DEC-012** (`DECISIONS.md:92-94`) descreve a virada em **futuro/condicional**: *"quando a fatia vertical piloto validar a cadeia, o estoque v1 (300 drafts + 9.700 expansões cartesianas) será substituído no worktree pelo estoque v2..."*. Uma IA lendo só a DEC conclui que a virada está **pendente**. **O worktree prova que já aconteceu:**

- `authorial_mass_content_expansion.jsonl` = **0 linhas** (era 9.700). Zerado no commit `dcc560fa`.
- `authorial_mass_content_expansion_section_chunks.jsonl` = **0 linhas** (era 133.327). Zerado no mesmo `dcc560fa`.
- `authorial_mass_drafts.jsonl` = **590 linhas de schema v2** (rampa `a7cfb6e4`→`72009d93`). O `head -1` de hoje tem `page_type=guia_problema` e `unique_intent_id=banc-golpe-pix-como-pedir-devolucao-med` — **v1 não tinha `page_type`** (discriminador objetivo de schema).
- `data/editorial/stock_manifest.json`: `updated_at=2026-07-09T15:56:09Z`, `note="v2 ingest mode=rewrite batch=e5_pages.jsonl accepted=590 rejected=0"`.

**DECLARAÇÃO INEQUÍVOCA (tempo passado/presente):** A virada v1→v2 foi **EXECUTADA em 2026-07-09**. O **v2 é o único estoque canônico**. O **v1 é history-only**, recuperável em `9a5495b`/`34d6df3d`. Ignorar as constantes v1 sempre que houver `stock_manifest.json`.

---

## 4. FONTE vs ESTOQUE (a confusão dos números)

Dois números NÃO podem ser confundidos:

| | FONTE canônica | ESTOQUE derivado |
| --- | --- | --- |
| Arquivo | `data/editorial/v2_pages/*.jsonl` | `data/editorial/authorial_mass_drafts.jsonl` |
| Número | **6.584 ativas** (cresce) | **590** (STALE) |
| Origem | redator-agente v2 | último `ingest-v2-stock` (run `e5_pages.jsonl`, 2026-07-09) |
| Papel | onde o conteúdo NASCE | o que a cadeia de release consome |

O `590` do estoque e o `drafts_expected=590` do `stock_manifest.json` refletem um run **antigo**, não os 6.641 finalizados atuais. **A distância 6.584 → 590 é INGESTÃO PENDENTE, não conflito v1/v2.** Quem olhar só `authorial_mass_drafts.jsonl` ou o manifesto vê 590 e conclui, errado, que quase nada foi escrito. O caminho para materializar o estoque canônico é `./tools/ingest-v2-stock` (o `--prepare-only` é write-free e mede o gap sem escrever).

---

## 5. A armadilha das constantes v1 no código

As contagens do v1 **seguem vivas no código Go** como *fallback* do manifesto — fonte latente de confusão para quem lê código sem manifesto:

- `internal/authorialmassdrafts/drafts.go:28` — `InitialBlockedBatchSize = 300`
- `internal/authorialmasscontentexpansion/content_expansion.go:35` — `ExpansionRecordCount = TargetTotalContents - InitialDraftCount` (= 9.700)
- `internal/stockmanifest/stockmanifest.go:6-7` — comentário documentando ambas

**Regra (INGEST_SPEC.md:22-25):** desde 2026-07-06 as invariantes de contagem são dirigidas pelo manifesto versionado `data/editorial/stock_manifest.json` via `authorialmassstock.ValidateRecordsForRoot`. **Com manifesto, ele manda**; manifesto inválido reprova com `authorial_mass_stock_manifest_invalid` — **nunca cai em fallback silencioso**. As constantes 300/9700 só valem se o manifesto estiver ausente (comportamento histórico). **Portanto: número v1 hardcoded ≠ verdade do estoque; consulte o `stock_manifest.json`, não a constante.**

---

## 6. Veredito sobre reuso do v1

**Para reuso de CONTEÚDO: NADA — tudo é duplicado ou já coberto.**

- **(a) TEXTO v1 → DESCARTAR.** Copiar/parafrasear qualquer corpo, `opening`, `meta` ou `heading` do v1 reintroduz doorway/scaled-content-abuse, reprova nos próprios gates de similaridade e viola Google + OAB. Nunca reusar `body_sections`/`opening`/`reader_problem` do v1.
- **(b) TÓPICOS v1 → NADA DE NOVO.** Os "9.700 intents únicos" são 27 tópicos-raiz × eixo de permutação (scenario/context = modo de entrega). Os **27 seeds já estão 100% cobertos no v2**, com mais profundidade (ex.: revisão de aposentadoria decomposta em Art. 103 da Lei 8.213, Tema 1102 STF, revisão da vida toda, servidor). Re-autorar os "intents" v1 fielmente **reproduz o doorway**. Não há tópico legítimo do v1 ausente no v2.
- **(c) PROVENIÊNCIA/METADADOS v1 → REUSAR (já em curso).** A própria **DEC-004** nomeia a keep-list: **taxonomia de intenções + fontes oficiais específicas (23.366 deep-links auditados) + metadados de demanda**. Isso é proveniência, **nunca corpo**, e já flui para o v2 em `data/source-audit/v2_source_provenance.jsonl` (1,46 MB, vivo).

> **"Nada" refere-se a texto/tópicos, não às fontes auditadas.** A camada de proveniência é a exceção nomeada — descartá-la contradiria a DEC-004.

**Novos intents dos 10k vêm de deep-research/Wave3 sobre lei viva e demanda real, nunca do estoque v1.**

---

## 7. Caminho para os 10.000 (resumo estratégico)

- **Meta P0:** 10.000 páginas públicas indexáveis aprovadas (DEC-005), regeneradas **all-or-nothing em N=10.000** (**DEC-015**, `ValidateExactP0TransactionPreflight` exige exatamente 10.000).
- **Gap:** piso MEDIDO = 10.000 − 6.584 = **3.416**; band realista **~3.430–3.900** após atrito semântico/proveniência que só é medível com `./tools/ingest-v2-stock --prepare-only` (write-free, maestro-run). Nunca reportar um número único confiante.
- **Motor de volume:** **escrita continuada de v2_pages em lote por família (DEC-011)** — única fonte que escala aos ~3.300+. Reusa o **mesmo pipeline v2, nunca um fork**.
- **Espinha anti-molde (não é adendo):** teste contrafactual DEC-007 + lote por família DEC-011 + auditor canônico `audit_v2_pages.py` + similaridade < 0.70 + WRITING_SPEC §3. Sem isso, "escrever mais páginas" reproduz o fracasso do v1.
- **Fontes por segurança:** (1) escrita continuada em lote; (2) deep-research de intents de alta conversão com receipt de demanda real; (3) Wave3 (108 curados, zero-dup medido, ~3% do gap); (4) re-autoria v1 = **descartada**.

> **v2 é a arquitetura correta e o alvo canônico — NÃO é "pronto/limpo comprovado".** As investigações não auditaram a qualidade interna do v2 (near-dup próprio) e há sinal vivo de falso-verde de citação em shards. A qualidade por-página é **garantida por gate e está em produção**, não concluída. Este documento não licencia pular auditorias.

---

## 8. Onde cada coisa vive (mapa de arquivos)

| Camada | Caminho | Estado |
| --- | --- | --- |
| **FONTE canônica v2** | `data/editorial/v2_pages/*.jsonl` | 6.584 ativas, cresce |
| Estoque derivado (ingerido) | `data/editorial/authorial_mass_drafts.jsonl` | 590, STALE |
| Manifesto de contagem | `data/editorial/stock_manifest.json` | manda sobre as constantes Go |
| Proveniência v2 (fontes) | `data/source-audit/v2_source_provenance.jsonl` | 1,46 MB, vivo |
| Tombstones DEC-020 | `data/editorial/v2_superseded/` | 17 originais preservados |
| Expansão v1 (morta) | `authorial_mass_content_expansion.jsonl` | 0 linhas |
| Section chunks v1 (morta) | `authorial_mass_content_expansion_section_chunks.jsonl` | 0 linhas |
| v1 íntegro (recuperação) | git `9a5495b` / `34d6df3d` | history-only |
| Auditor canônico | `tools/audit_v2_pages.py` | pré-ingestão, espelha o gate |
| Ingestão | `tools/ingest-v2-stock` (`--prepare-only` = write-free) | Go, maestro-run |

---

## 9. Evidência (DEC / arquivo / git)

- **DEC-004** (`DECISIONS.md:35`) — condenação do v1: métricas de molde (12 headings ×4.599, 14.327 near-dup, Hamming 0, 27 seeds→10k) + keep-list (taxonomia, 23.366 deep-links, demanda).
- **DEC-005** (`DECISIONS.md:44`) — P0 = 10.000 páginas indexáveis aprovadas.
- **DEC-007** (`DECISIONS.md:53`) — portfólio não-cartesiano, teste contrafactual, 4 tipos de página.
- **DEC-009** (`DECISIONS.md:73`) — retrofit da cadeia com estoque v2.
- **DEC-011** (`DECISIONS.md:88`) — redação em lotes por família.
- **DEC-012** (`DECISIONS.md:92-94`) — virada v1→v2, história preservada (`9a5495b`). *Redação em futuro — corrigida por este doc para tempo passado.*
- **DEC-015** (`DECISIONS.md:115`) — P0 regenera em N=10.000, all-or-nothing.
- **DEC-017** (`DECISIONS.md:134`) — reescrita mecânica DESLIGADA no v2.
- **DEC-020** (`DECISIONS.md:188`) — `intent_id` ativo globalmente único; 17 duplicatas consolidadas em tombstone (`data/editorial/v2_superseded/`).
- **WRITING_SPEC.md** §3 (anti-molde) e §7:49-72 (formato de entrega + honestidade de fonte).
- **INGEST_SPEC.md:22-25** — manifesto manda sobre as constantes; sem fallback silencioso.
- **Código:** `internal/authorialmassdrafts/drafts.go:28`; `internal/authorialmasscontentexpansion/content_expansion.go:35`; `internal/stockmanifest/stockmanifest.go:6-7`.
- **Worktree (2026-07-15):** v2_pages = 445 arquivos / 6.641 finalizadas / 6.584 ativas; drafts = 590 (stale, schema v2); expansion = 0; section_chunks = 0; `stock_manifest.json` updated 2026-07-09.

*Última atualização: 2026-07-15. Manter em tempo passado/presente. Correção só para frente.*