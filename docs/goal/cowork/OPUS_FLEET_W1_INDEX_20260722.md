# OPUS FLEET — Onda 1 — Manifesto de Integração (adjudicado pelo Fiscal Fable)

- Data: 2026-07-22 · Autoria: `claude-cowork-opus-fleet` (Cowork, ordem do dono `destrava-fabrica-plano`)
- HEAD observado no fecho: `b599b7ed` (subiu de `2956359d` durante a onda; FAQ fix landou em `36fe8fb4`)
- Fiscal adversarial: `OPUS_FLEET_W1_FISCAL_FABLE_20260722.md` — 5 GREEN / 4 YELLOW / 1 RED
- 10 drops UNTRACKED em `docs/goal/cowork/OPUS_FLEET_W1_*.md`

## Como landar (regras)
Landar por **pathspec** (commit leve DEC-016, sem build). Correções de **conteúdo** entram pela **fila de revisão sancionada**, nunca edição à mão em `data/editorial` (frescor B5). Patches de **código/tool** o main aplica e commita (build pesado serializado). Minha VM não commita de forma confiável (EPERM em `.git/`), por isso o handoff.

## Veredito por drop

### GREEN — landar as-is
- **poscutoff_penal** — 20 pgs citando leis de 2026; **19 CLEAR, 1 HOLD**, 0 lei alucinada. HOLD = `crim-quanto-cumprir-para-progredir`: reconciliar art. 112 LEP **vigente** (Lei 15.402 vetos IV–X + suspensão Moraes ADIs 7.966/7.967 — CONFIRMADA live) antes do promote. `15.575/15.632` = falso-positivo numérico (CDC art. 26 / nº REsp).
- **erratas_lote3** — **3 erratas reais que BLOQUEIAM promote**: (1) `crim-quanto-cumprir` (15.402 sem ressalva da suspensão STF); (2) `banc-fver-liminar-deferida-sem-ouvir-devedor` (super-atribuição ao Tema 1.279); (3) `lei-maria-da-penha` (título executivo = **Lei 15.412/2026 §10 art. 22**, CONFIRMADO — não 15.384; sem proveniência atual). ~27 pgs cleared como falso-positivo.
- **prosas4** — 4 correções em `data/ops/entity_prose_grounded_20260721.jsonl` (idx3 CDC art.5; idx21 CLT art.3; idx27 L8245 art.59; idx52 L8213 art.74) — **4/4 verificadas live** no Planalto. Aplicar pela fila; ficam quarentenadas/noindex até o corpus-stub ser saneado.
- **fila_noop** — PATCH pronto: novo predicado `writer_noop_batch(...)` em `generate_v2_review_queue.py`, wire no emissor como status `'noop'` (resolve claim sem agente, fora da janela do breaker `>=5`). Aplicar **após** o regen liberar `/tmp/opt-wiki-agent-heavy.lock`, depois re-emitir p/ purgar no-ops já enfileirados. Raiz também em `ops/relaunch-writing.sh:823` + `writing-mass.js:679`.

### YELLOW — landar com ressalva
- **mold_disclaimer** — 28 rewrites únicos prontos, MAS o molde real é **75 pgs / 47 shards** (variante "guia é informativo"): drenar por **regex/percentil**, não pelos 28 fixos. 4 extra-flags com fix exato (paid-signal `prev-acumular`/`pi-acao-nulidade`; lane reclass `dig-remocao-video-intimo`; fonte `proc-enotariado` Res. CNJ 571).
- **seguros244** — landar, mas **corrigir dimensionamento**: "10 de dezembro de 2025" → "**11 de dezembro de 2025**" ocorre **3×/página** (não 1); data confirmada por manifestação SUSEP. 3 pgs bloqueiam promote. Substância (arts. 10 par.ún.I, 89, 94, 116, 118, 120, 126, 132, 133) verificada OK.
- **restamp391** — 2 patches de código corretos (`specificity.go:45-48` → deep-link Tema 1.390/STJ; `main.go:36-49` → `checked_at_stale` fail-closed). ❌ **VETO DO FISCAL**: NÃO relabelar refs `websearch_confirmed` como `cowork-fable-live-*`/verdict-ok — é **fabricação de proveniência**. Normalizar wave2 → arquivo-manhã sancionado sem forjar método.

### SUPERSEDED — não landar
- **catalogo_hints_onda2** — o main já landou onda-2 em `b599b7ed` (3.323 slugs); fiscal: 52/52 chaves já presentes. Arquivar. Bônus ainda válido: bug latente `normalize_https_url` usa `parse_qsl(strict_parsing=True)` sem guard de query vazia (quebra em py3.11).

### RED — NÃO landar
- **prosas33_grounding FIX-1** — **REFUTADO AO VIVO**: art. 59 da L8213 CONTÉM §§2º–5º (recluso em regime fechado, suspensão, até 60 dias — Lei 13.846/2019). A "alucinação" apontada é **lei vigente**; a correção apagaria conteúdo correto. **Descartar FIX-1.** Manter só FIX-2 (art. 71 CLT: intervalo de 15 min exige gatilho ">4 horas") se validado. 38/50 seguem sem veredito semântico (residual para próxima onda).

## Achado estratégico (o mais importante para os 10k)
Fila de rejeição viva = **524** (não 857 — 857 era dry-run 07-21 stale). 7.178 aceitas + FAQ fix (`36fe8fb4`) → re-ingest ganha +8. **TOP-2 alavancas limpam ~399 pgs (76%)**: restamp `verified_at`/`http_status` (~214) + gate-tune `isLegalCitationExempt` (`validate.go:1040`, ~194, sem rewriter). **PORÉM:** estoque v2 total ≈ **7.703 candidatos** → mesmo promovendo TUDO, teto ≈ **7.663 aprovadas = ~2.300 ABAIXO de 10k**. A fila sozinha NÃO fecha o piso. **Geração NET-NEW é obrigatória em paralelo** (frontboard `ondas-gap-2345`). A Onda 2 do fleet ataca exatamente esse gap.
