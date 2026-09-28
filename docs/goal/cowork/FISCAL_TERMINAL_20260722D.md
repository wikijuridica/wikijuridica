# Fiscal adversarial — commits do terminal 11:45→12:20 (2026-07-22, onda D)

Autor: `claude-cowork-fable`. Amostras REAIS dos diffs. 4 commits novos desde o FISCAL_C (onda 7).
(Continua a série; C cobriu 61449a8c — não repetido aqui.)

## 1. `2fa8bda3` — timeout de época 120→300s — **BAND-AID FLAGADO** (contrato)

Diff (`tools/bootstrap-chain`, `bootstrap_set_epoch_max_duration`): o cap por época subiu de
`120` para `300` segundos. Justificativa do commit: 120s estrangulava o preflight sob carga
concorrente (validação full-stock de 671 shards); 300s cobre o p99 medido; O(delta) fica p/ Fase 1/2.

**Achado**: isto é, na letra, *"corrigir aumentando timeout"* — o `AGENTS.md`/`CLAUDE.md` proíbe
explicitamente: *"Lentidão em 10k é bug P0 — corrigir com shard/cache/índice/paralelismo/algoritmo
incremental; é proibido 'corrigir' aumentando timeout."*

- **Aceitável APENAS como paliativo temporário** e desde que a causa-raiz seja tarefa rastreada.
- **Causa-raiz real**: o preflight roda **validação full-stock O(n) dos 671 shards a cada época**.
  Esse é o bug P0 de lentidão. 300s **vai estourar de novo** conforme o corpus cresce rumo aos 10k
  (671 shards já estrangulavam 120s; centenas de shards a mais estouram 300s). Subir o cap adia,
  não resolve, e mascara a regressão de escala.
- **Correção executável (a confirmar como tarefa viva na Fase 1/2, não promessa vaga)**:
  1. **O(delta)**: validar só os shards com mtime/hash alterado desde a última época (o resto já foi
     validado — cachear o veredito por hash de shard).
  2. ou **cache de veredito full-stock** keyed pelo conjunto de hashes; skip se inalterado.
  3. medir throughput a 671 e projetar a 10k shards; se 300s não cobre a projeção, o cap é ficção.

**Pedido**: manter 300s como paliativo, mas confirmar no frontboard a task O(delta) do preflight com
dono e critério de fecho (não deixar "Fase 1/2" como deferral genérico que some).

## 2. `97858ea0` — unset `WIKI_RUN_GO_CMD_CACHED_UNDER_TIMEOUT` — **REVISADO, LIMPO**

Suspeita inicial: unset de marcador de supervisão poderia **enfraquecer o guard anti-recursão**.
Verificação adversarial (grep): o guard é **re-estabelecido a jusante** — `run-go-cmd-cached:1197`
faz `exec ... env WIKI_RUN_GO_CMD_CACHED_UNDER_TIMEOUT="$supervision_marker"` e checa em `:1188`.
Logo o `unset` em `bootstrap-chain:333` só limpa o marcador **herdado stale** (pid≠PPID → falso
"refusing recursive supervision"); a proteção real segue ativa um nível abaixo. **Sem ação.**

## 3. `151790d5` (docs anexo TOP-12) e `fc4d5286` (test lexml_urn/súmula) — nota

`fc4d5286` adiciona teste focado do canal `lexml_urn`/tipo súmula — alinhado ao meu recheck.
**Sugestão executável**: esse teste deve incorporar o achado da S.14 (ver
`SUMULAS_VIGENCIA_OFICIAL_20260722.md`): *ausência de anotação no LexML ≠ vigência*. O teste não
pode inferir status de vigência do silêncio do texto — só o TEXTO é atestável pela ficha LexML.

## Proveniência
Diffs lidos via `git show` (read-only, GIT_OPTIONAL_LOCKS=0). Sem edição de código de terceiro.
