# COWORK_FABLE_DIVISION.md — Divisão vinculante: Claude Code (terminal) × Cowork Fable 5

Criado: 2026-07-22 por `claude-cowork-fable` (sessão Cowork desktop do dono, modelo Fable 5).
Status: **VINCULANTE** para as duas sessões Claude até revisão registrada aqui ou no `MAESTRO_CODEX_LOG.md`.
**Leitura obrigatória** do Claude Code terminal no início de cada ciclo `/goal`.
Precedência: `AGENTS.md` → `GOAL.md` → `CHECKPOINT.md` → este arquivo. Regra mais restritiva vence.

> **Superado em parte em 2026-09-22 (ordem do dono; revisão registrada na DEC-060 e no
> `MAESTRO_CODEX_LOG.md`).** O orquestrador de toda sessão deste projeto — terminal e Cowork —
> passa a ser o Fable 5.1, sob `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md`. Cai o ponto
> "o Cowork nunca edita": a sessão Cowork orquestra e integra como a do terminal. **Fica** a
> interface anti-conflito do §4 — bus de coordenação, presença, pathspec restrito nos commits,
> nenhuma edição à mão em shard de `data/editorial/v2_pages/` (editorial só por gerador),
> nenhuma edição em arquivo com mtime recente de outra sessão, comando pesado só no terminal do
> host. O resto deste arquivo fica como foi escrito.

## 1. Por que existe

O dono opera agora DUAS sessões Claude em paralelo sobre este repo: o **Claude Code no terminal**
(com Workflow/subagentes, canal sancionado de escrita v2, oráculos locais em :8082) e o
**Cowork Fable 5** (app desktop, com **web fetch/browser reais e irrestritos** — o que o terminal
não tem: lá WebFetch/WebSearch estão banidos por ECONNRESET e o redator vive de `curl`).
Pelo próprio contrato do repo (`CLAUDE.md` §orquestração), **Fable 5 = crítico adversarial + fiscal**.
Esta divisão aloca cada sessão no que ela faz melhor, sem disputa de artefato.

## 2. Estado lido em 2026-07-22 (evidência, não memória)

- `published_manifest = 0`. Nenhuma página pública. Este é O nó do projeto.
- Estoque v2: **671 shards, 7.722 linhas**; dry-run de ingest VERDE em 133s: **6.846 aceitas, 857 rejeitadas**
  (484 `dup_phrase`, **391 fonte stale**, 46 `draft-schema`, 25 `legal_fact`).
- Gap até 10k aceitas ≈ **3.2k páginas novas** + drenagem das 857.
- Throughput recente: ~1.5k linhas/semana (última semana), ~10.5k/2 semanas (inclui recuts).
- Cadeia b4→b6 pronta (ingest WRITE-FULL → bootstrap-chain → verdict → cohort ~250 → promote).
  Destrave: pousar unidade editorial (317 arquivos), 2 gates de supersessão, decisão `--allow-public-write`.
- Hard-state: 121 shards `codex-*` sem rota normal (re-run sancionado, piloto família `aereo`).
- D4.8: RCA do loop grave de 2026-07-21 pendente (obrigatória antes do fecho P0).

## 3. Divisão de trabalho

### Claude Code (terminal) — dono de: escrita sancionada, engenharia, release
1. **Toda escrita/reescrita de páginas v2** via `scripts/workflows/writing-mass.js` — único canal sancionado.
   O Cowork NUNCA escreve página.
2. **Cadeia b4→b6 até o primeiro cohort ~250 promovido** (`published_manifest > 0`). Prioridade máxima.
3. Gates, perf O(delta), ingest/attestation, supersessão, RCA D4.8, re-run `codex-*`.
4. Drenagem das filas 857 — para as 391 de fonte stale, **consumir o insumo verificado do Cowork** (§4).

### Cowork Fable 5 (esta sessão) — dono de: verificação viva, crítica adversarial, pesquisa
1. **Re-verificação VIVA das 391 fontes stale** com HTTP real → entrega em
   `data/source-audit/cowork_source_recheck_YYYYMMDD.jsonl` (metadata-only: url, status, verified_at,
   redirect final, título da página oficial; NUNCA corpo/conteúdo copiado).
2. **Red-team pré-promote**: leitura adversarial de amostra do cohort candidato ANTES de qualquer
   `--allow-public-write` → verdict em `docs/goal/cowork/PROMOTE_REDTEAM_YYYYMMDD.md`.
   O Claude Code **deve ler o verdict mais recente antes do primeiro promote** (não é veto — é evidência).
3. **Adjudicação de molde** nos shards piores (empresarial-p1 ~75%, procedimentos ~71%) → specs
   executáveis de reescrita em `docs/goal/cowork/`.
4. **Pesquisa SEO/indexação 2026** (scaled content abuse, site reputation, thresholds de indexação
   de site novo) → checklist pré-launch.
5. **Pesquisa de demanda/intent metadata-only** para os 2.341 intents ausentes do portfólio e canal P1 100k.
6. **Fiscalização contínua** do trabalho de ambos os pares (papel Fable do contrato).

## 4. Interface anti-conflito (obrigatória)

- Cowork **NUNCA edita**: shards `data/editorial/v2_pages/`, camadas derivadas, código Go em edição
  ativa (mtime recente), artefatos públicos/release.
- Cowork **escreve apenas**: `data/source-audit/cowork_*.{jsonl,md}`, `docs/goal/cowork/*`, este arquivo,
  e mensagens no bus (`--from claude-cowork-fable`).
- Claude Code trata `cowork_*` como **insumo verificado com proveniência** e o integra pelo canal
  sancionado (ex.: recheck de fonte alimenta `audit-v2-source-provenance`/fila de revisão).
- Presença do Cowork pode falhar no mount (renameat2 EINVAL) — o **bus.jsonl é o canal garantido**.
- Commits do Cowork: sempre pathspec restrito aos próprios arquivos `cowork_*`/`docs/goal/cowork/`.

## 5. P0–P5 do Cowork Fable

- **P0**: 391 fontes stale re-verificadas ao vivo (primeiro lote no mesmo dia) + red-team do primeiro promote.
- **P1**: adjudicação de molde dos shards piores + specs de reescrita para a fila `dup_phrase` (484).
- **P2**: dossiê SEO/indexação 2026 + demanda metadata-only para fechar os 2.341 intents e alimentar P1 100k.
- **P3**: pesquisa de conectores oficiais (DataJud 401: requisitos reais da chave pública CNJ; export STF;
  LexML/normas.leg.br) → briefs executáveis para o terminal implementar.
- **P4**: fiscalização contínua dos pares + manutenção deste arquivo e dos verdicts.
- **P5**: intel de launch (DNS/host/TLS/Cloudflare Tunnel, DEC-010) quando a fábrica estiver completa.

## 6. P0 do Claude Code (ordem recomendada; detalhe no /goal do dono)

1. Pousar a unidade editorial (317 arquivos) pelo canal sancionado `commit-verified-v2-workflow-results`.
2. Fechar os 2 gates de supersessão (`receipt.go:267` dual-claim; forward evidence) + attestation v2ingest.
3. Re-run sancionado dos `codex-*` (piloto `aereo`), preservando trabalho válido.
4. **b4→b6 até o fim**: ingest WRITE-FULL → bootstrap-chain → verdict>0 → cohort ~250 → **PRIMEIRO PROMOTE**
   (ler antes o `PROMOTE_REDTEAM_*` mais recente do Cowork).
5. Ondas de escrita para o gap ~3.2k + drenar 857 (fonte stale: esperar/consumir `cowork_source_recheck_*`;
   se o insumo ainda não chegou, drenar primeiro `dup_phrase`/`draft-schema`/`legal_fact`).
6. Perf O(delta) (ingest 133s→s; contract 403s→~120s) + RCA D4.8. Nunca ocioso; nunca esperar notificação.
