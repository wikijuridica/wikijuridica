# `docs/goal/enaeval/` — raiz de pesquisa do EnaEval no host (aterrissada em 2026-09-24)

Esta pasta é a **árvore de pesquisa** que a TASKLIST chama de `research-v4/` e que o prompt
operacional (§2) mandou criar no host quando não existisse. Ela nasceu em contêiner efêmero de
sessão Cowork (22/09/2026, `/home/claude/wikijuridica/`), e do contêiner só a **prosa** chegou ao
Projeto claude.ai. Em 2026-09-24 o chefe (Fable 5.1, sessão Cowork) copiou para cá **tudo** o que o
Projeto guarda: 9 documentos e 1 PDF. Nada foi resumido, cortado ou "melhorado": cada arquivo
carrega origem, data e SHA-256 em `MANIFESTO.json` (fidelidade auditada por transcrição
independente — `nota_fidelidade` do manifesto). Decisões da aterrissagem: DEC-061 e DEC-062 **redigidas** em
`.agents/runtime/20260924-enaeval-aterrissagem/appends/decisions_add.md` (com a entrada de PRECEDENTES, a do
MAESTRO e as seções §2.1-A/§7.2 do `JURIDICO_BASE`), pendentes de aplicação pelo dono na sessão do host —
a sessão Cowork de 2026-09-24 não pôde gravá-las nos registros.

**Ordem do dono (2026-09-24):** "o plano todo, o estudo TODO, deve virar realidade, não tem mais ou
menos". Esta pasta é o insumo; a TASKLIST é o plano; o CANON é a fonte única de números.

## 1. Hierarquia de autoridade (não se reabre)

`CORRECOES-DONO` (perdido; o que dele sobreviveu está citado no CANON como "CORREÇÕES §n")
> `DECISOES-ORQUESTRADOR.md` (D-1…D-17 + ADENDO)
> `CANON-v4.1.md` (fonte única de números)
> `LEDGER.md` da frente (prova de execução; substitui o `LEDGER-CORRECOES.md` perdido — a criar na
sessão Claude Code do host, ver §5)
> `BLUEPRINT-v4-VOL-II.md` > `BLUEPRINT-v3.md` > `RELATORIO-ENGENHARIA-v2-20260915.pdf`.

Fora desta pasta continua valendo o contrato do repositório: `CLAUDE.md` (regra mais restritiva
vence; código vivo e dado no disco vencem qualquer documento) e
`docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md` (o mandato; a cópia do host é a canônica — tem o
parágrafo do editor que o doc do Projeto ainda não tem). Onde a TASKLIST e o `CLAUDE.md` tratam do
mesmo ato, vale o mais restritivo dos dois. Base jurídica de tudo o que se publica:
`docs/goal/JURIDICO_BASE.md` (§2.1-A e §7.2 reconferidos em 2026-09-24).

## 2. O que está aqui

| arquivo | bytes | sha256 (prefixo) | papel |
|---|---:|---|---|
| `CANON-v4.1.md` | 82947 | `1db688af35f81f74…` | fonte única de números e decisões (§0–§17) |
| `DECISOES-ORQUESTRADOR.md` | 12090 | `2fa6907bf8059016…` | D-1…D-17 + ADENDO; acima do CANON |
| `TASKLIST.md` | 92363 | `d3524fb283fdfdb1…` | 12 fases · 49 objetivos · 149 tarefas, goal mode |
| `BLUEPRINT-v4-VOL-II.md` | 279236 | `1e1bd2ae2416cadd…` | Partes IV e V + Apêndices A (CANON) e B (decisões) |
| `BLUEPRINT-v3.md` | 308140 | `a777cb94364761b7…` | Volume I (Partes I–III); vale onde o CANON §16 não revogou |
| `RELATORIO-ENGENHARIA-v2-20260915.pdf` | 421460 | `8263a36b8ae9ee62…` | relatório v2 (15/09), 21 páginas |
| `RELATORIO-ENGENHARIA-v2-20260915.txt` | 49033 | `ffc88f5cc95c6434…` | texto do PDF (pdftotext -layout), para grep |
| `INSTRUCOES-DO-PROJETO-20260922.md` | 5246 | `6c24ccb2a70f8f62…` | texto do campo Instruções do Projeto |
| `PESQUISA-PROFUNDA-BRIEF.md` | 503 | `b7f442dc587c1f49…` | brief do dono (15/09) que originou o PDF |
| `CANON-v3-SUPERADO.md` | 793 | `d5fe225fcd075dbd…` | aviso de superação (v3 → v4.1) |
| `CHECKLIST-v3-SUPERADO.md` | 427 | `24df648836157f86…` | aviso de superação (105 itens → 49 objetivos) |
| `MANIFESTO.json` | — | — | origem, data e SHA-256 de cada linha acima |
| `PONTE_CEREBRO_E_REDE_SOCIAL.md` | — | fora do manifesto (documento vivo) | ponte cérebro (Ollama) → EnaEval (vLLM); F3.O0; reputação (DEC-062 proposta) |

Hash completo e origem literal: `MANIFESTO.json`. Conferência:
`python3 -c "import json;[print(a['sha256']+'  docs/goal/enaeval/'+a['arquivo']) for a in json.load(open('docs/goal/enaeval/MANIFESTO.json'))['arquivos']]" | sha256sum -c`.

## 3. Regra de imutabilidade

Os arquivos do manifesto **não se editam**. Erro, superação ou correção entram, com data e motivo,
em `docs/goal/DECISIONS.md` (DEC-nnn), `docs/PRECEDENTES_DAS_ORDENS.md` (ordem literal do dono), no
`ESTADO.md`/`LEDGER.md` da frente ou em nota datada. Parágrafo superado ganha data e motivo; não se
apaga (`CLAUDE.md`). O teste de contrato que reprova hash divergente é item de abertura da sessão do
host (§5).

## 4. O que a TASKLIST cita e NÃO existe no host (medido em 2026-09-24)

`find /opt/wiki /home/rafael -maxdepth 6` por `research`, `research-v4`, `wj`, `CANON-v4*`, `SCHEMA-v4*`,
`lar.go`, `CORRECOES-DONO*`, `H01-critico*`, `FIX-A*`, `LEDGER-CORRECOES*` → **nenhum**. Portanto:

| citado na TASKLIST | situação | onde a substância sobreviveu |
|---|---|---|
| `CORRECOES-DONO.md` | perdido | citado por seção no CANON ("CORREÇÕES §2, §5, §6, §7") e na regra nº 4 do CANON |
| `LEDGER-CORRECOES.md` (62 decisões + G1–G19) | perdido | CANON §16 ("Revogado pela v4.1") e §17; D-13 lista as 5 correções estruturais |
| `H01-critico-fable.md` (19 achados) | perdido | CANON §16 (tabela "Revogado pela v4.1", coluna "Quem matou") e ADENDO de DECISOES |
| `FIX-A.md`, `FIX-B.md`, `INVENTARIO-CODIGO.md` | perdidos | CANON §17 (evidência de execução) e TASKLIST §1 (mapa artefato → pacote) |
| `SCHEMA-v4.1.sql`, `ATAQUES-v4.1.sql`, `fixes/*.sql` | perdidos | CANON §5 (Dados) e §17 (131 tabelas · 139 FKs · 402 CHECKs; 127 recusas · 27 aceites · 0 falhas) — critério de pronto de F0.O5 |
| `enums/{enums.yaml,gen.py}` | perdido | CANON §7 e Blueprint IV.2 (20 enums, 163 valores, 35 alvos) — critério de F0.O2 |
| `verify-code/verify.go`, `lar.go` v1.1, `orcamento_v4.py`, `catalog.json`, `*.tla` | perdidos | CANON §4/§8/§3/§17 e Blueprint V.7 — critérios de F0.O3, F0.O4, F0.O6, F3.O3 |
| todo `*-code/` (C03, F01–F11, G01–G04) | perdido | prosa dos Blueprints e do CANON |

Consequência (DEC-061): todo objetivo cujo Insumo era código passa de **[I]/[A]** para **[E] recriar a
partir da prosa**, e o **critério de pronto não muda** — os números do CANON são a régua do que se
recria. Recriar com número menor não é "pronto"; é objetivo dividido em dois (TASKLIST §0.3). Mapa
objetivo a objetivo: `.agents/runtime/contexto/2026-09-24-enaeval-insumos-por-objetivo.md`.

Caminhos: `research-v4/X` na TASKLIST ⇒ `docs/goal/enaeval/X` (esta pasta); `wj/` ⇒ `/opt/wiki/wj/`
(árvore do módulo `portaljuridico`, import `portaljuridico/wj/<pacote>`, DEC-061 — já existe com
`deps.yml`, `wj-depcheck` e `tools/wj-ci`); `/home/claude/wikijuridica/` (§4 da TASKLIST) ⇒ esta pasta.

## 5. Estado em 2026-09-24 e itens de abertura da sessão Claude Code no host

Feito nesta aterrissagem, com prova no host: os estudos (11/11 hashes OK); `wj/` com 31 pacotes,
`wj/deps.yml`, `wj-depcheck` (`31 pacotes verificados, 0 violações`; mutação DEP-6 detectada; 148
casos de teste) e `tools/wj-ci` em `tools/run-qualidade-diaria`; a `PONTE_CEREBRO_E_REDE_SOCIAL.md`
com F3.O0 especificado e medido; DEC-061/062 redigidas (pendentes); base jurídica reconferida em fonte primária (textos e hashes nos appends). Contexto colhido em
`.agents/runtime/contexto/2026-09-24-enaeval-*.md` (barramento e cinco fatias).

Placar enquanto o `ESTADO.md` não existe: as caixas `- [ ]` da `TASKLIST.md` (149 tarefas) e o mapa
por objetivo em `.agents/runtime/contexto/2026-09-24-enaeval-insumos-por-objetivo.md`. Objetivos
sem dependência aberta: F0.O2 (enums), F0.O7 (em curso — `wj/` iniciado), F0.O1 (K_root), F0.O5
(Postgres, instalação de fonte oficial), F3.O0 (Ollama na GPU — PONTE §4), F1.O3 (identidade das
três portas).

A sessão Cowork de 2026-09-24 não gravou arquivos de configuração de agente nem o placar da frente.
Itens de abertura da próxima sessão Claude Code no `/opt/wiki`, nesta ordem: (1) `ESTADO.md` (50
objetivos: 49 da TASKLIST + F3.O0; colunas objetivo · status · depende · insumos · próxima ação ·
pronto · evidência · lacuna; status ∈ pendente · em curso · feito · bloqueado-com-rota) e `LEDGER.md`
(só acréscimo: comando, saída literal, exit); (2) a política de execução da frente, derivada da
TASKLIST §0 e do mandato §§4, 6, 7 e 11; (3) a skill `enaeval-objetivo` e a linha na tabela "Antes
de agir" do `CLAUDE.md`; (4) `internal/contract/misc/enaeval_test.go` cobrando o MANIFESTO, a forma
do ESTADO/LEDGER e a ausência de cronograma nos derivados; gate `enaeval-contrato` em
`internal/checks` e `tools/check-enaeval`; (5) aplicar, por decisão do dono, os registros redigidos em
`.agents/runtime/20260924-enaeval-aterrissagem/appends/` (o `aplicar.py` só acrescenta e é idempotente).
Depois, o primeiro objetivo da lista acima.
