# CHECKPOINT_DIGEST.md — resumo vivo de continuidade

> **Como este arquivo foi gerado.** Extraído mecanicamente de `CHECKPOINT.md` em **2026-07-28**, a partir da nota de precedência (linhas 1-3) e das **6 entradas mais recentes** (2026-07-21 → 2026-07-23), bloco medido em **17.592 bytes**, obtido por
> `awk '/^## /{n++} n>6{exit} {print}' CHECKPOINT.md`.
> **Nada aqui foi inventado**: todo fato abaixo está no `CHECKPOINT.md`; nenhum número, commit ou estado veio de outra fonte.
>
> **`CHECKPOINT.md` continua sendo a evidência integral e a fonte de verdade** (2.464.348 bytes, 387 entradas). Este digest é **índice de entrada**, não substituto: ele não tem valor probatório, o `CHECKPOINT.md` tem.
>
> **Defasagem conhecida (fato, não opinião).** A entrada mais recente do `CHECKPOINT.md` é de **2026-07-23**; o HEAD do git está à frente. Para o estado VIVO use os comandos da §4 — nunca presuma que este digest é o presente.

---

## 0. PONTEIRO 2026-08-26 — plano vivo da superfície de bots, e o que este digest afirma de errado

**Leia antes de usar qualquer número deste digest.**

- **Plano vigente:** `docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md` — 3.567 linhas, aprovado
  pelo dono em 2026-08-26. **10 fases (0 a 9), 92 tarefas, 16+ gates**, ordenadas **por
  dependência, não por severidade**. Evidência bruta das 8 ondas de auditoria (8 journals
  + 24 relatórios de agente) em `data/ops/agent_reports/onda_bots_20260826/`, com README
  mapeando onda → run id.
- **⚠ A §2 abaixo está FACTUALMENTE ERRADA hoje.** Ela diz *"Publicação zero preservada:
  `published_manifest=0`, nenhum artefato público tocado"*. **Medido em 2026-08-26: há
  9.710 páginas públicas no ar**, `published_manifest` com **10.070 linhas**, sitemap
  servindo **10.294 URLs**, domínio no ar desde antes de 2026-08-13. A afirmação de
  publicação zero foi superada pela política **PUBLICAR E CORRIGIR** de 2026-08-06.
  **Ela fica aqui porque este digest é extração mecânica de entradas de julho — mas quem
  a ler como presente conclui errado.**
- **Diagnóstico que governa o trabalho atual:** o portal **não tem problema de descoberta,
  tem problema de RETORNO** — os bots varreram uma vez e não voltaram (**54,8%** dos
  clientes distintos não-warm vieram um único dia). Cache Rule da borda apagada em
  2026-08-22, revalidação condicional morta (**0,2%** de 304), fábrica diária **nunca**
  completou uma execução, e **24.367 `anchor_claim` verificados** não chegam à página.
- **Registro de engenharia da sessão:** entrada de 2026-08-26 no topo de
  `docs/goal/MAESTRO_CODEX_LOG.md`, incluindo as **três correções que causariam dano se
  aplicadas na ordem escrita** e os **cinco erros de medição próprios** desta auditoria.

---

## 1. Precedência (condensado das linhas 1-3 do CHECKPOINT.md — LEIA ANTES DE USAR QUALQUER ENTRADA ANTIGA)

Ciclos antigos registram decisões **históricas** de P0 que **NÃO governam o estado atual** quando conflitam com `AGENTS.md`, `GOAL.md`, o anexo obrigatório do `/goal` e decisões recentes. São legado, entre outras: "não publicar 10 mil páginas durante P0", empurrar tipos de página para fases posteriores, operar agentes em 10/5, 10+5 ou 12/8, e substituir agente lento.

**Contrato vigente:** P0 não publica sem gate completo, **mas DEVE promover página pública aprovada** quando fonte, revisão, paid-intent/CTA (ou bloqueio explícito), qualidade, SEO/crawl, HTML leve, `published_manifest`, sitemap/canonical/robots, smoke HTTP/Googlebot e release gate passarem. Subagente lento/travado é **reorientado** — nunca morto/reiniciado/substituído por conveniência. Todo achado de subagente é integrado **na mesma sessão** ou vira blocker P0 comprovado. O `/goal` continua até no mínimo **10 mil páginas jurídicas públicas aprovadas, únicas, indexáveis e verificadas**, com caminho de escala maior.

> Consequência prática: ao dar `grep` no meio do `CHECKPOINT.md`, você vai cair em regra legada. Reveja esta seção antes de obedecê-la.

## 2. Estado do P0 (nas 6 entradas mais recentes)

- **Publicação zero preservada**: `published_manifest=0`, nenhum artefato público tocado (registrado em 2026-07-21 e 2026-07-22).
- **Marco 2026-07-22: pouso sancionado do semantic-recut geração 2** — commit `3d97d239` criado pelo próprio committer via CAS (`audit_merit_verified=true`, `identity_verified=true`, 2.714 dependências, `publication_allowed=false`), fechando 8 paths. Caminho até o verde: 3 fixes forward (`6e69183b` generation-aware, `649601a3` `-tags devcmds` no gate privado, `ae38a45f` contrato do auditor canônico).
- **Forward evidence VERDE**: gerador destravado (authority==HEAD pós-pouso), 81 rows, `check-v2-supersession-forward-evidence` verde. Item 2 do goal fechado (`75653248` + `4a8b0e2e`).
- **B4 WRITE-FULL COMMITTED**: **7.178 aceitas / 524 rejeitadas**. Rejeições drenando (FAQ 21 itens normalizados em dado `36fe8fb4`; reconcile 95 flags-órfãs; stale-skip 1). Projeção com Tune-1 dup-phrase: ~7,55-7,6k aceitas.
- **TOP-12 do plano destrava pousado integral** (6 commits: `86d48c41`, `17f59262`, `61a5fd6c`, `7eacdd98`, `cc2d2fc2`); fiscal: zero violação.
- **Fecho Go de 2026-07-21**: 11 commits, entre eles `0204bb14` (1.057 arquivos, validado por `check-go-index-compile-closure` em 16,5s), `337da4d5` corpus-oráculo (4.992 blobs CAS, DEC-021), `8d34224d` (determinismo JSD — bug latente real), `5f047f07` (jsoniter, 2,18s→1,77s/op medido).
- **Auditoria de conteúdo com leitura real** (12 amostras / 8 famílias + varredura N=7.722): **texto APTO** — 0 vocabulário interno, 0 thin ativo, meta 100%.
- **Enforcer P4 novo**: `release_live_recheck_required` era universal (7.178 pgs) e **sem consumidor** — implementado em `authorialmassmanifesttransaction` (exclusão por página, frescor = dia UTC). Evidência já cobre 2.976 páginas.
- **restamp-391 FECHADO**: evidência v6 fresca em 41/41 shards (390/391 refs), recheck vivo Cowork 513/513, 5 v5-stale re-verificados ao vivo.
- **Catálogo** 121 → 208 intents; onda-4 (top-150 slugs, 1.059 intents) em staging `.agents/runtime/staging/onda4_out/`; merge previsto **pós-cohort** (quiescência).
- **Pós-reboot 2026-07-23 ~09:12**: workflows/LT mortos, reconciliados por onda read-only + fiscal red-team; LT :8082 religado; staging da onda-3 **recuperado byte-exato dos transcripts** (54/54) em `227e2834`.

## 3. Em aberto (última sequência registrada — entrada 2026-07-23)

**Sequência da cadeia até o primeiro `published_manifest>0`:**
fix das 3 falhas `v2ingest` → **commit Go serializado** → pouso staged pelo committer → warming freshness → **B4** → **B5 1-41** → audit-do-dia → 42 → hold-intersection → **onda-2 QA** (10 agentes leem o TEXTO das ~250 candidatas + reconciliam o hold) → **cohort-1 `--execute`** → resume da onda-95 (`wf_3f8f0857-2d5`, 12 lotes em cache).

Pendências e riscos registrados:

- **Frescor é do DIA**: evidência `release_live_recheck` de ontem **não vale hoje** (prazo 21:00 -03, virada UTC) — daí `ops/audit-cohort-do-dia.sh` + flag `-dump-cohort` no checker.
- **Hold-list do cohort-1: 213 páginas** (dedup 216→213), com `check-promote-hold-intersection`. Holds nomeados: ~30 erratas lote-3, 13 penais, leis-inf2:8.
- **3 bloqueios de conteúdo pré-B4→B6** (2026-07-21): (1) **molde estrutural** — virou política executável (8 arquétipos determinísticos, `WRITING_SPEC` §3; shards mais moldados: empresarial-p1 75%, procedimentos-15/09 71%); (2) citações pós-cutoff — **RESOLVIDO**, todas confirmadas na fonte oficial; (3) **21 titles >65 chars** em fila de reescrita mecânica.
- **57 tombstones 0-byte** staged por buraco de glob (`.gitignore` corrigido; guard v2 bloqueia remoção crua do index); **6 arquivos com dupla-versão** staged(Jul-18) × worktree(Jul-22) — **pousar ambas em sequência, nunca perder nenhuma**.
- **Arquitetura descoberta**: o evidence set de supersessão **NÃO pousa isolado** (o hook exige archive aéreo + source shards juntos) — pousa tudo na **transação única do committer**.
- **Corpus**: Partes A/C íntegras (censo 10/10 + 21/21); **Parte B esbarra na fronteira de vigência** (`ReviewEvidenceVerifier`).
- **Contingência de modelo**: limite do Fable 5 foi atingido mid-flight (2 especialistas mortos); adversarial foi re-roteado para Opus.

## 4. Navegação bounded do CHECKPOINT.md (NÃO leia integral — são ~616k tokens)

**A ordenação NÃO é uniforme:** as entradas recentes ficam no **TOPO** (mais nova primeiro), e depois há uma região de legado com ordenação própria (por volta das linhas 6767-7147 estão entradas de 2026-06-13, e o fim do arquivo volta a subir até 2026-06-28). **Por isso `tail` está errado**: `tail -n 200` devolve ~81 KB de legado de junho, não o estado atual. Sempre navegue pelo índice, nunca por posição presumida.

```bash
# índice das 20 entradas mais recentes (barato, ~2 KB)
grep -n '^## ' CHECKPOINT.md | head -20

# bloco recente completo — 6 entradas, ~17,6 KB — auto-ajustável (não depende de nº de linha)
awk '/^## /{n++} n>6{exit} {print}' CHECKPOINT.md

# só a entrada mais nova (~4 KB)
awk '/^## /{n++} n>1{exit} {print}' CHECKPOINT.md

# uma seção específica, pelo nº de linha obtido no índice acima
sed -n '<inicio>,<fim>p' CHECKPOINT.md

# achar um assunto sem carregar o corpo
grep -n 'cohort-1' CHECKPOINT.md | head -20
```

**Estado VIVO (o digest e o checkpoint são pistas, não o presente):**

```bash
git log --oneline -12
git status --short | head -40

# plano de tasks vivo — SÓ o que está aberto (5.385 B medidos; o `cat` cru custa 35.710 B / ~9k tok)
jq -r 'select(.status!="done" and .status!="superseded")
       | "\(.priority) \(.status)\t\(.id)\t\(.front[0:110])"' \
  .agents/runtime/p0_frontboard.jsonl | sort -n

# a `note` de uma task (é o campo caro — puxe uma, nunca todas)
jq -r 'select(.id=="<id>") | .note' .agents/runtime/p0_frontboard.jsonl
```

## 5. Custo dos contratos (medido em 2026-07-28)

`CHECKPOINT.md` 2.464.348 B (~616k tok) · `AGENTS.md` 168.213 (~42k) · `GOAL.md` 139.188 (~34,8k) · `P0_OPERATIONAL_RUNBOOK.md` 87.468 (~21,9k) · `p0_frontboard.jsonl` 35.710 (~8,9k — use o filtro da §4, 5.385 B) · `DECISIONS.md` 32.515 (~8,1k) · `CLAUDE.md` 31.248 (~7,8k; sob poda ativa hoje, remeça se o número importar) · `ROADMAP_P0_P5.md` 30.966 (~7,7k) · `V1_V2_CONTENT_LINEAGE.md` 15.993 (~4k) · **este digest ~8,7k B (~2,2k tok)**.

O `CHECKPOINT.md` sozinho não cabe em nenhuma janela de contexto. Ler este digest (~2k tokens) e só então descer ao trecho específico é o método obrigatório.
