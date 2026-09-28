# Ultraplano — Fábrica jurídica real, P0 → P5 (wikijuridica.com.br)

## Contexto

O dono pediu: investigar o repo, diagnosticar por que os comandos são pesados demais para a escala (a mesma máquina compilou 30M de páginas com cache em outro projeto; aqui <10k trava com 3-4 agentes), e entregar um **ultraplano em formato de prompt** para a próxima sessão do Claude Code levar o projeto do P0 (10.000 páginas públicas) até o P5 (traffic-ready), mantendo qualidade e regras — com autorização explícita para mudar arquitetura e atualizar documentos que proíbam.

**Investigação executada**: leitura direta dos contratos (GOAL, ROADMAP, DECISIONS DEC-001→015, BUGLOG, WRITING/INGEST_SPEC, STATUS/PLAN) + 3 agentes Explore (dados editoriais, hotspots de peso, cadeia de publicação) + 1 agente Plan validando as decisões contra o código + pesquisa web em fontes oficiais do Google (spam policies / scaled content abuse / helpful content).

## Diagnóstico consolidado (tudo medido, 2026-07-08)

### A máquina nunca teve culpa — o peso é da camada de processo do Codex

| Causa | Evidência medida |
|---|---|
| `.git` **16,8 GiB, 21.090 objetos soltos, 0 packs** | nunca houve repack; `git gc` simples recupera >15 GB |
| `.worktrees/` **26 GB** (17 worktrees mortas) + `.artifact-quarantine/` 1,1 GB + ~330 MB de `*.test` na raiz | resíduo de agentes, não é produto |
| **231 binários main** em cmd/ (162 `generate-*`) | religação de `go build ./...` ≈ 5 min; **mas** `tools/run-go-cmd-cached` já compila binários cacheados — o problema real é o **cache em `/tmp`** (evapora a cada boot; estava vazio na medição) |
| Monólito `internal/checks` | checks.go 10.575 linhas importa 234/278 pacotes internos; checks.test = 178 MB |
| Arquivo gigante | `refinedpublicprose/refined.go` = 42.137 linhas |
| Cadeia acoplada por **mtime** | 6 pontos (`readiness.go:923`, `quality_vectors.go:425/908/953`, `checks.go:9875/9900`); writers usam temp+rename → todo re-run avança mtime mesmo sem mudança → cascata de falso-stale (o "cold-start deadlock") |
| **N=10000 literal** remanescente | `refined.go:21339/21402/5813` (count gates via const), `verdict.go:80` (oráculos são PULADOS abaixo de 10k), `public_prose_candidate.go:41`; o resto já é manifest-driven (DEC-014 parcial) |
| O(n²) residual | caminho `global_all_pairs_compared` e all-pairs quando n≤250 |

**O produto em si é leve**: render 412 linhas (string builder), httpserver 777, ondemand 356. Servir/gerar HTML nunca foi o gargalo.

### Estado da fábrica de conteúdo (o caminho crítico real)

- Portfólio v2: **6.517 intents** / tetos ≈ 12.300 → **faltam ~3.483 intents** de curadoria (ondas suplementares parciais: glossário 702/1400, leis 339/600, súmulas 189/350, consumidor 249/700, bancário 295/700…).
- Páginas escritas: **632** (9,7% do portfólio; 4 de 30 áreas tocadas; trabalhista e saúde 100%); throughput real ≈ **200–350 págs/dia de sessão**; filas idempotentes de escrita/revisão funcionam.
- **Ingestão parada no piloto**: só 34/632 ingeridas; fila de reescrita com 36 registros, **32 rejeitados por piso antigo de 4 seções** (contraria DEC-013 — verbete ≥2) → bug/estado a investigar antes de reescrever.
- Instrumentação não-durável: auditor canônico só imprime stdout; `v2_source_provenance.jsonl` prometido pelo STATUS/WRITING_SPEC **não existe em disco**.
- Estoque v1 (10.000): confirmado doorway (DEC-004), papel = taxonomia + 23.366 deep-links de fonte.

### Cadeia de publicação (verificada no código)

- BUG-001 corrigido de verdade: `ApprovePromotionManifestForPublicWrite` existe e está wired no promote CLI (`main.go:317`); revalida verdict de cada registro.
- `p0-cycle-close-indexable-10k` exige **exatamente 10.000** (deficit E overrun) e revalida cada HTML ponta-a-ponta.
- Todos os 9 geradores da cadeia existem; ordem de bootstrap conhecida (DEC-015); oráculos PT-BR instalados e **já auto-escalam** pelo manifesto (`effectiveMinimumRecords`).
- **Colisão de porta 8081**: LanguageTool × nginx.
- **P3 CONCLUÍDO** (bench 1M real + evidência; STATUS desatualizado). **P4 pendente** (`releases/` não existe; nginx aponta root inexistente; rollback só em código). **P5 preparado** (ops completo sem credencial; Bleve v2.6.0 no go.mod com swap atômico mas não servido; CTA com placeholder).

## Abordagem recomendada (validada contra o código pelo agente Plan)

**Estratégia-mestra: provar a cadeia cedo, escrever em fluxo contínuo, publicar uma vez.** Em vez de esperar 10.000 páginas para descobrir se a cadeia fecha (aposta da DEC-015), fechar os restos da DEC-014 e **ensaiar a cadeia inteira em N=632 até o verdict + dry-run de aprovação** — prova ponta-a-ponta em 1-3h de máquina, antes de investir semanas de redação. Depois disso a fábrica vira rotina: curar → escrever → revisar → ingerir → auditar, até selecionar exatamente 10.000 e promover.

Frentes (E = engenharia, C = conteúdo, P = fases do goal):

- **E1 — Higiene de disco/git (janela ociosa)**: `git gc` (repack, sem reescrita de história — DEC-006 mantida); inspecionar e remover `.worktrees/` mortas (integrando qualquer trabalho único antes), quarentena e `*.test` da raiz; **atualizar CLAUDE.md/docs que protegem esses artefatos** (autorizado pelo dono, registrando DEC). Ganho: ~45 GB e I/O da máquina compartilhada.
- **E2 — Cache persistente (quick-win nº1)**: `WIKI_GO_CMD_BIN_CACHE` e `GOCACHE` de `/tmp` → `/opt/wiki/.cache/` (mudança de ~1 linha em `tools/run-go-cmd-cached` e wrappers). Mata o cold-start recorrente que hoje religa geradores a cada boot. Busybox adiado (religaria tudo a cada edit e perderia guard-rails — veredito do agente Plan).
- **E3 — Destravar regeneração em qualquer N**: (a) ferramenta de bootstrap com a ordem topológica da DEC-015; (b) guard *write-if-unchanged* (não sobrescrever JSONL byte-idêntico) nos writers da cadeia — estanca o ripple de mtime; (c) fechar DEC-014: `refined.go` count gates e `verdict.go:80` viram manifest-driven com o padrão `EffectiveReleaseMinimum` (piso 10.000 preservado sem manifesto); (d) migração mtime→fingerprint elo a elo como hardening posterior.
- **E4 — Instrumentação durável**: auditor canônico persiste relatório em `data/ops/v2_audit_report.jsonl`; ingestão persiste `data/source-audit/v2_source_provenance.jsonl` (cumprir o que o WRITING_SPEC §7 já promete); corrigir o gate de ingestão para DEC-013 (piso proporcional por page_type) e reprocessar a fila de 36.
- **E5 — Ensaio N=632** (depende de E3): ingestão total das 632 → regenerar cadeia completa → oráculos ligados (LanguageTool em **:8082**, resolvendo a colisão) → `verdict_passed=632` → dry-run de aprovação via `BuildPromotionPlan` (public write continua bloqueado <10k por design). Critério: cadeia provada ponta-a-ponta.
- **C1 — Completar portfólio a ~10.500** (ondas suplementares WAVE_BRIEFS, teste contrafactual, sem cartesiano) + merge consolidado com dedupe global.
- **C2 — Ondas de escrita/revisão contínuas** (motor existente: filas idempotentes, máx 3 agentes, circuit breaker, auditor canônico) com **ingestão a cada onda** (nunca mais acumular 598 páginas não ingeridas).
- **P0-close**: selecionar exatamente 10.000 aprovadas → regenerar em N=10.000 → verdict → approve → promote `--allow-public-write` → `published_manifest=10.000` → check verde + smoke + **leitura de amostras por área** (obrigatória).
- **P1**: ≥100.000 candidatos governados (metadados + lineage, bloqueados; o excedente do portfólio já alimenta).
- **P2**: cobertura de fontes oficiais (conectores metadata-only: INPI, Receita, PGFN, ANPD, SUSEP, ANS, BCB, consumidor.gov.br, Anatel, DataJud, tribunais, Câmara, Senado) com proveniência.
- **P3**: concluído — atualizar STATUS e re-rodar benchmark após E2/E3 para manter evidência fresca.
- **P4**: opção (ii) validada — novo cmd pequeno `snapshot-public-release` (hardlink `public/` → `releases/<id>/public`, verificação SHA-256 contra o promotion manifest, symlink `releases/current` com rename atômico) + **drill de rollback real** + runbook. Não mexer no núcleo transacional.
- **P5**: servir Bleve em `/buscar/` (noindex) pelo Go :8080; nginx :8081 com root agora existente; tunnel/systemd prontos; checklist de launch para o dono (WhatsApp real no `cta_policy.json`, credencial Cloudflare, DNS) — domínio NÃO ativado.

### Arquivos críticos

- `internal/refinedpublicprose/refined.go:21339,21402,5813` + `internal/scaledcontentreleaseverdict/verdict.go:80,512` + `internal/publicprosecandidate/public_prose_candidate.go:41` — fechar DEC-014 (padrão em `internal/authorialmassstock/stock.go` `ExpectedTotalContents`/`EffectiveReleaseMinimum`).
- `tools/run-go-cmd-cached` (linhas 123-125, 741-745, 947-953) — cache persistente.
- `internal/authorialmassreadiness/readiness.go:923`, `internal/authorialmassqualityvectors/quality_vectors.go:425,908,953`, `internal/checks/checks.go:9875,9900` — pontos mtime.
- `internal/v2ingest/` + `tools/audit_v2_pages.py` — DEC-013 no gate, persistência de relatório/proveniência.
- `internal/publicrelease/publicrelease.go:3379,3418-3446` — fronteira do D4 (não tocar; snapshot é greenfield).
- `ops/nginx/wikijuridica.conf`, `ops/setup-oracle-tools.sh` — mapa de portas (Go :8080, nginx :8081, LanguageTool :8082).

### Verificação (por frente)

- E1: `git count-objects -vH` (packs>0, size <3 GB); `df` antes/depois; docs atualizados com DEC.
- E2: reboot-safe — segundo run de um gerador qualquer sem recompilar (medir com `time`).
- E3/E5: cadeia N=632 fecha do zero (log do bootstrap); re-run é no-op (write-if-unchanged); `verdict_passed=632`; dry-run de approval sem erro; testes dos pacotes tocados verdes.
- E4: `data/ops/v2_audit_report.jsonl` e `data/source-audit/v2_source_provenance.jsonl` existem e crescem por lote; fila de reescrita reprocessada.
- C1/C2: contadores por onda no STATUS; auditor 0-defeito por lote; ingest report accepted=escrito.
- P0: `./tools/go-modern run ./cmd/check p0-cycle-close-indexable-10k` verde; `./tools/check-http-smoke`; amostras lidas por área.
- P4: drill executado — promover release, derrubar, rollback via symlink, provar com curl no nginx local.
- P5: `/buscar/` respondendo do índice Bleve; smoke completo via nginx; checklist de launch entregue ao dono.

---

## O ULTRAPROMPT (colar na próxima sessão do Claude Code)

```text
Você é o maestro-engenheiro e editor jurídico da fábrica wikijuridica.com.br (/opt/wiki).
Missão: concluir P0→P5 — 10.000 páginas jurídicas públicas aprovadas, únicas, indexáveis
(published_manifest=10.000, check p0-cycle-close-indexable-10k verde) e fábrica/servidor
prontos para tráfego, sem ativar domínio. Trabalhe multi-sessão: as filas são idempotentes
e docs/goal/STATUS.md é o estado vivo — atualize-o a cada marco e retome dele.

LEITURA OBRIGATÓRIA (nesta ordem, antes de agir):
docs/goal/STATUS.md → docs/goal/DECISIONS.md → docs/goal/BUGLOG.md → CLAUDE.md →
docs/goal/WRITING_SPEC.md + INGEST_SPEC.md → este prompt de novo.
Precedência: regra mais restritiva vence; DEC-002 substitui a burocracia histórica do
AGENTS.md/GOAL.md; o dono autorizou mudar arquitetura E atualizar qualquer documento que
proíba melhoria — toda mudança de regra vira DEC nova em DECISIONS.md, nunca mudança muda.

REGRAS DURAS INEGOCIÁVEIS:
1. Servidor compartilhado de 8 cores (TRAVOU em 2026-07-08; causa-raiz — commit pesado
   religando 504 pacotes Go — resolvida em 2026-07-10, DEC-016/pre-commit condicional):
   subagentes SEM teto artificial (regra do dono 2026-07-29: nao existe teto de agentes; agente LLM-bound nao consome nucleo, e o limite do harness e POR WORKFLOW — escala real vem de MUITOS workflows simultaneos). Dimensionar pelo trabalho real;
   1 commit por vez (serialização evita corromper índice, não é mais CPU); NUNCA dois
   bootstrap-chain em paralelo sobre os mesmos JSONL (corrompe dados); comando pesado só o
   maestro, um por vez, via nice/flock; python de agente com nice -n 19; timeout recorrente
   = medir uptime/load e REDUZIR carga.
2. Git só para frente: proibido reset/checkout/restore/revert/stash/clean; sem reescrita
   de história (DEC-006). git gc/repack é permitido em janela ociosa sem agentes.
3. Qualidade não relaxa NUNCA: cadeia completa da regra de ouro (CLAUDE.md); reprovado vira
   correção do elo, não afrouxamento do gate; ler amostras reais antes de avançar lote.
   Zero stub/fake/fraude; PT-BR perfeito no que é público; ética OAB (Provimento 205/2021);
   proibido inventar lei/decisão/prazo; fonte oficial é proveniência, nunca corpo.
4. Publicação: nenhuma URL pública fora da transação aprovada; lane informativa (BPC/LOAS,
   gratuidade) sem CTA comercial; paid-intent no corpo; exatamente 10.000 na promoção P0.
5. Honestidade operacional: nunca declarar feito sem prova medida; STATUS.md só recebe
   número verificado (a investigação de 2026-07-08 achou 2 claims falsos no STATUS —
   corrija-os: P3 está CONCLUÍDO e v2_source_provenance.jsonl NÃO existia).

ESTADO REAL MEDIDO EM 2026-07-08 (confie nisto, verifique se mudou):
- Portfólio v2: 6.517/10.000+ intents (tetos ≈12.300; faltam ~3.483 — ondas WAVE_BRIEFS).
- Escritas: 632 páginas (4/30 áreas; trabalhista+saúde 100%); ingeridas: SÓ 34;
  fila de reescrita: 36 (32 por bug de piso de seções — DEC-013 não aplicada no gate).
- published_manifest=0; verdict_passed=0; cadeia nunca fechou ponta-a-ponta em N nenhum.
- Peso: .git 16,8GiB solto (0 packs); .worktrees 26GB mortas; cache de binários em /tmp
  (evapora); mtime causa falso-stale em cascata; N=10000 literal em refined.go:21339/21402,
  verdict.go:80, public_prose_candidate.go:41 (resto já é manifest-driven).
- P3 concluído (bench 1M + evidência). P4: releases/ não existe (nginx aponta root
  inexistente). P5: ops pronto sem credencial; Bleve no go.mod não servido; CTA placeholder.
- Colisão de porta: LanguageTool e nginx ambos em 8081 → mover LT para 8082.

PLANO DE EXECUÇÃO (frentes; ordene por dependência, paralelize C com E quando seguro):

E1 HIGIENE (janela ociosa, sem agentes ativos):
  nice -n 19 git gc (repack simples; meta .git <3GB); git worktree list → inspecionar cada
  .worktrees/* por trabalho único não integrado (integrar antes de remover), depois remover
  e git worktree prune; remover *.test da raiz e .artifact-quarantine/ APÓS atualizar
  CLAUDE.md/docs que os protegem (registrar DEC com justificativa). Meta: ~45GB livres.

E2 CACHE PERSISTENTE (quick-win, ~1 linha por wrapper):
  WIKI_GO_CMD_BIN_CACHE e GOCACHE: /tmp → /opt/wiki/.cache/go-cmd-bin e ~/.cache/go-build
  em TODOS os wrappers (tools/run-go-cmd-cached:123, tools/lab-cycle). Prova: 2º run de
  gerador qualquer = 0 recompilação. Busybox NÃO (validado: perderia cache incremental).

E3 REGENERAÇÃO EM QUALQUER N (destrava tudo):
  a) tools/bootstrap-chain: roda a ordem topológica DEC-015 (qv-from-stock → readiness →
     candidate → refined → oráculos → legal_reviews → evidence → transaction → manifest →
     verdict) com log e stop-on-fail.
  b) write-if-unchanged nos writers da cadeia (não renomear temp sobre arquivo byte-igual)
     — estanca o ripple de mtime.
  c) Fechar DEC-014: refined.go:21339/21402/5813 e verdict.go:80/512 e
     public_prose_candidate.go:41 → manifest-driven via EffectiveReleaseMinimum (padrão em
     authorialmassstock/stock.go; piso 10.000 preservado sem manifesto). Testes dos
     pacotes tocados verdes. NÃO tocar ValidateExactP0TransactionPreflight (10k-only é
     proteção correta).
  d) (hardening posterior) mtime→fingerprint elo a elo: readiness.go:923,
     quality_vectors.go:425/908/953, checks.go:9875/9900.

E4 INSTRUMENTAÇÃO DURÁVEL:
  Corrigir gate de ingestão para DEC-013 (piso proporcional: verbete/pergunta ≥2,
  procedimento ≥3, guia ≥4) — investigar por que rejeitou com minimum=4; reprocessar a
  fila de 36. Auditor tools/audit_v2_pages.py passa a persistir data/ops/v2_audit_report.jsonl.
  Ingestão passa a persistir data/source-audit/v2_source_provenance.jsonl (WRITING_SPEC §7
  já promete). needs_source_research=true (35 págs) → fila de verificação de fonte.

E5 ENSAIO N=632 (a prova antecipada — rodar assim que E3 fechar):
  Ingerir TODAS as v2_pages auditadas → stock_manifest N≈632 → subir LanguageTool :8082
  (ajustar endpoint nos geradores/config) → tools/bootstrap-chain → verdict_passed=632
  com oráculos EXIGIDOS (não pulados) → dry-run de aprovação via BuildPromotionPlan
  (SEM --allow-public-write; preflight 10k continua fechado por design). Custo ~1-3h
  serializado. Se travar: corrigir o elo, nunca o gate. Cadeia provada = risco do P0
  cai de "aposta de semanas" para "rotina".

C1 PORTFÓLIO → 10.500:
  Ondas suplementares (WAVE_BRIEFS.md): glossário +698, leis +261, súmulas +161,
  consumidor +451, bancário +405, imobiliário, procedimentos, família, empresarial,
  cidadania, digital, autônomos, investimentos, educação, criminal. Teste contrafactual
  por intent (só cria página o que muda regra/prazo/documento/risco/fonte); proibido
  cartesiano. Gerar merge consolidado com dedupe global de intents.

C2 ESCRITA/REVISÃO/INGESTÃO EM FLUXO (caminho crítico, multi-sessão):
  Motor existente: bash ops/relaunch-writing.sh (fila de escrita) alternando com
  ops/relaunch-review.sh (fila de revisão via auditor canônico --global); máx 3 agentes;
  circuit breaker (janela ~toda falhando = rate limit → parar e retomar depois);
  NUNCA resumeFromRunId. Throughput real ≈200-350 págs/dia de sessão — planeje ~30-40
  dias-sessão para ~9.400 páginas; otimize prompts por page_type (verbetes 350-700
  palavras rendem lotes maiores). A CADA onda concluída: auditar --global → ingerir
  (cmd/ingest-v2-pages) → commitar. Nunca acumular páginas não ingeridas de novo.

P0-CLOSE (quando estoque aprovado ≥10.000):
  Selecionar EXATAMENTE 10.000 (excedente fica bloqueado → alimenta P1) → regenerar cadeia
  em N=10.000 (bootstrap-chain; oráculos ligados) → verdict 10.000 passed →
  cmd/approve-public-release/promote --allow-public-write --expected-manifest-records=10000
  → published_manifest=10.000 → check p0-cycle-close-indexable-10k VERDE + check-http-smoke
  + leitura de amostras estratificadas POR ÁREA (obrigatória antes de declarar P0).

P1 (≥100k candidatos governados): expandir a maquinaria do portfólio para ≥100.000 intents
  com lineage/status/gates computáveis, tudo bloqueado/noindex; dedupe por
  simhash/HNSW+banding (já no repo), NUNCA all-pairs — remover o caminho
  global_all_pairs_compared O(n²) como gate.

P2 (fontes oficiais): registrar conectores/políticas metadata-only por órgão (INPI,
  Receita, PGFN, ANPD, SUSEP, ANS, BCB, consumidor.gov.br, Anatel, DataJud, tribunais,
  Câmara, Senado) em source_registry, com proveniência (URL, data, hash) e liveness
  UA-de-navegador (WAF gov.br bloqueia UA custom — decisão já documentada).

P3: já concluído (cmd/bench-scale-1m + evidência 1M). Atualizar STATUS.md; re-rodar após
  E2/E3 para manter a evidência fresca.

P4 (operação): novo cmd pequeno snapshot-public-release: hardlink public/ →
  releases/<id>/public + verificação SHA-256 contra promotion_manifest + symlink
  releases/current por rename atômico (greenfield; NÃO mexer no núcleo transacional
  publicrelease.go:3379+). Executar DRILL DE ROLLBACK real (promover, trocar symlink de
  volta, provar com curl no nginx local). Runbook em ops/README.md.

P5 (traffic-ready, domínio NÃO ativado): servir Bleve em /buscar/ (noindex) pelo Go :8080
  (internal/codex2bleveindex já tem build+swap atômico); nginx :8081 com root
  releases/current/public agora existente; LanguageTool :8082; systemd/cloudflared prontos
  sem credencial. Checklist final para o dono: (1) WhatsApp real em content/cta_policy.json;
  (2) credencial do Cloudflare Tunnel; (3) ativação de DNS. Entregar o checklist e PARAR —
  launch é decisão do dono.

LOOP OPERACIONAL DE CADA SESSÃO:
1. Ler STATUS.md + git log desde o último marco; medir contadores reais (não confiar).
2. Escolher a maior fatia segura da frente mais atrasada do caminho crítico.
3. Executar com no máx 3 agentes; maestro audita amostras em tempo real (ler o que os
   agentes escrevem ENQUANTO escrevem; corrigir prompt/reorientar sem matar frente).
4. Auditar → ingerir → commitar (1 por vez) → atualizar STATUS.md com números medidos.
5. Repetir até acabar a sessão; deixar filas em estado retomável (idempotência por
   conjunto, tombstones honestos).

DEFINIÇÃO DE PRONTO GLOBAL: p0-cycle-close-indexable-10k verde + amostras lidas e aprovadas
por área + P1 inventário ≥100k + P2 conectores registrados + P3 evidência fresca + P4 drill
de rollback provado + P5 smoke completo via nginx + checklist de launch entregue. Nada de
"depois": o que couber na sessão, faz na sessão; o que não couber, deixa retomável e medido.
```

## Notas finais

- **Sem dependência nova**: tudo que o plano usa já está no repo (bleve, pebble, hnsw, simhash, LanguageTool, Vale, oráculos python). Dependência nova só com ADR (regra do go.mod mantida).
- **Documentos a atualizar** (autorizado pelo dono, via DEC): CLAUDE.md (proteção de `*.test`/quarentena → removida com justificativa; regra de artefatos de worktree), STATUS.md (P3 concluído; claim de proveniência corrigido), DECISIONS.md (novas DECs: cache persistente, write-if-unchanged, ensaio N=632, snapshot P4, mapa de portas).
- **O que NÃO fazer**: reescrita de história git (DEC-006); busybox (validado como regressão); relaxar qualquer gate de qualidade; ativar DNS/domínio.
