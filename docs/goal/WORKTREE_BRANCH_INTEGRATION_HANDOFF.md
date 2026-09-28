# Handoff — trabalho não integrado em worktrees e branches órfãos

> **Para o próximo Claude Code.** Este documento existe para você decidir e executar sem
> ter que refazer a investigação. Leia a seção 1 e a 2 antes de tocar em qualquer coisa.
>
> Levantado em 2026-07-28. `main` no momento do levantamento: `42e29f88`.
> Status das seções 5 e 6: preenchidas por revisão com agentes (ver marcação em cada uma).

---

## 1. O que você precisa saber antes de agir

O repositório acumulou duas camadas de trabalho que **nunca entraram no `main`**:

| camada | quantidade | onde | risco de perda |
|---|---|---|---|
| worktrees com alterações **não commitadas** | 11 (+1 fora do repo) | `/opt/wiki/.worktrees/`, `~/.config/superpowers/worktrees/wiki/` | **era alto** — já mitigado, ver §3 |
| branches com **commits** que não estão no `main` | 24 | refs locais do repo | baixo (commit não se perde) |

Tudo isso foi produzido pelo agente **Codex**, que o dono **desativou em 2026-07-21**. Desde
então, todo o trabalho é do Claude Code.

### A restrição que define como integrar

As bases desse trabalho são de **19/06 a 03/07/2026**. O `main` de hoje está
**1005 a 1201 commits à frente**. São cerca de quatro semanas de evolução do repositório,
incluindo a substituição do estoque editorial v1 pelo v2 (DEC-004 / 09-07).

Por isso o dono determinou, e este documento repete como regra dura:

> **Integrar é reescrever a intenção no código de hoje — editando para frente.**
> É **proibido** `merge`, `cherry-pick`, `rebase`, `reset`, `checkout`, `restore` e `stash`
> (contrato do repositório; há hook que bloqueia). Também é proibido "aplicar o patch":
> com 1000+ commits de defasagem, aplicar diff reintroduz arquitetura morta e quebra o que
> hoje funciona.

Na prática: você lê o que o trabalho **pretendia resolver**, confirma que o problema ainda
existe no código atual, e escreve a solução nos arquivos de hoje.

---

## 2. Triagem já feita — não refaça

### 2.1 Branches órfãos: 10 dos 24 dependem de linhagem morta

Dez branches alteram `data/editorial/authorial_mass_*` / `content_expansion`, que é o
**v1 cartesiano condenado** pela DEC-004 (doorway/duplicado, substituído em 2026-07-09 pelo
estoque canônico v2 em `data/editorial/v2_pages/`). Integrar qualquer um deles ressuscitaria
exatamente o que foi condenado.

**Descartados por padrão** (não investigue de novo sem motivo novo):

```
codex1-p0-algorithmic-approval            codex2-p0-refinement-cache
codex2-p0-anti-template-risk-refinement   codex2-p0-source-demand-governance
codex2-p0-authorial-scale-shards          codex2-p0-timing-promotion-storage
codex2-p0-authorial-shard-refinement-plan codex55-p0-10k-storage-sitemap-dedupe
codex2-p0-labor-negative-formal           codex2-p0-opensource-datajud-gate
```

### 2.2 Uma premissa que morreu sozinha

Vários desses branches existem para **coordenar dois agentes** (Codex + Claude): filas de
handoff, locks entre pares, auditoria de sobreposição, log de divergência. Com o Codex
desativado, esse trabalho é obsoleto por definição — não porque o código seja ruim, mas
porque o problema que ele resolvia deixou de existir.

Ao avaliar qualquer item, pergunte primeiro: **isso só faz sentido com dois agentes?**
Se sim, descarte e registre.

---

## 3. O trabalho não commitado já está preservado

Antes de qualquer decisão sobre espaço em disco, o conteúdo das worktrees foi extraído:

```
~/.config/ai-terminal-backups/worktree-work-20260728-075936/
└── <nome-da-worktree>/
    ├── modificados.patch   # git diff HEAD (inclui staged e unstaged)
    ├── untracked.lista     # arquivos novos não rastreados
    ├── untracked/          # cópia deles
    ├── base-commit.txt     # commit em que o trabalho foi feito
    └── branch.txt          # nome do branch
```

**2,3 MB preservam o que estava preso em ~24 GB de worktrees.** O trabalho não depende
mais das árvores existirem.

> Os patches servem como **referência de intenção**, não para aplicar. Leia-os para
> entender o que se pretendia; escreva a solução no código de hoje.

---

## 4. Inventário factual

### 4.1 Worktrees (todas com alterações não commitadas)

| worktree | base | commits atrás | arquivos no patch |
|---|---|---|---|
| `codex-p0-engineeringnow-missing-path-20260703` | `1b098d1c` (03/07) | 1005 | 2 |
| `codex-task2-public-prose-perf` | `1b098d1c` (03/07) | 1005 | 2 |
| `codex-task4-workreuse-20260703093112` | `1b098d1c` (03/07) | 1005 | 2 |
| `codex2-p0-public-final-source-live-recheck` | `7d19da8b` (19/06) | 1201 | 5 |
| `codex384-legal-signature` | `df6450ba` (19/06) | 1200 | 2 novos |
| `faraday-ptbr-text-shape-release` | `3b7ae51f` (30/06) | 1025 | 11 |
| `kepler-publicrelease-seooracles` | `3b7ae51f` (30/06) | 1025 | 2 |
| `linnaeus-roaring-postings` | `3b7ae51f` (30/06) | 1025 | 25 |
| `lorentz-parquet-lt-399` | `3b7ae51f` (30/06) | 1025 | 6 |
| `p0-anchor-join-fix-20260627072738` | `bc585ad7` (25/06) | 1178 | 2 |
| `ptolemy-ckan-oracle-cycle399` | `3b7ae51f` (30/06) | 1025 | 8 |

Todas com **0 commits à frente do `main`** — o valor está apenas no working tree, e é por
isso que a preservação da §3 era urgente.

### 4.2 Branches órfãos de infraestrutura Go (candidatos reais)

Os 14 que **não** dependem do v1. Datas de 15 a 16/06/2026.

```
codex2-mass-scale-coordination         (7 commits, 19 arquivos .go)
codex2-p0-check-performance-ledger     codex2-p0-source-candidate-pack
codex2-p0-check-selection              codex2-p0-source-codex-lock-decision
codex2-p0-checks-proportional-unit     codex2-p0-source-evidence-gate
codex2-p0-frontier-source-bridge       codex2-p0-source-final-lock
codex2-p0-frontier-wave-runner         codex2-p0-source-live-recheck
codex2-p0-go-policy-enforcement        codex2-p0-source-resolution
                                       codex2-p0-source-specificity-recheck
```

Inventário detalhado, com commits e arquivos por branch, em
`/tmp/claude-1000/-opt-wiki/*/scratchpad/branches-orfaos.txt` (efêmero) e a classificação
consolidada em `branches-classificados.txt` do mesmo diretório. Se tiverem sumido,
reproduza com:

```bash
cd /opt/wiki
git for-each-ref --format='%(refname:short)' refs/heads/ | while read -r br; do
  n=$(git rev-list --count "main..$br" 2>/dev/null || echo 0)
  [ "$n" -gt 0 ] && echo "$br: $n commits únicos"
done
```

---

## 5. Veredito por worktree — **NENHUMA precisa ser integrada**

> Revisão concluída em 2026-07-28: um agente independente por worktree, mais refutação
> adversarial. **11 de 11 já estão no `main`.** Detalhamento completo, com a evidência de
> cada uma: **[`WORKTREES_REVISAO_20260728.md`](WORKTREES_REVISAO_20260728.md)**.

### O que explica todas as 11

O Codex **commitava o trabalho no `main` por outra rota** — tipicamente no mesmo dia, em um
caso 74 minutos depois da base — e a worktree ficava para trás segurando apenas a **cópia de
staging não commitada**. O que parecia "1000 commits de trabalho perdido" é resíduo de
trabalho **já entregue**.

### Provas mais fortes (reproduzíveis)

| worktree | prova |
|---|---|
| `codex-task2-public-prose-perf` | `git apply --check --reverse <patch>` **sai 0** — o patch já está no `main`, verbatim |
| `ptolemy-ckan-oracle-cycle399` | integrado **byte-idêntico** em `9142bf84` |
| `codex-task4-workreuse-20260703093112` | `recordHasConcreteArtifactClaimEvidence` em `ledger.go:6951`, corpo idêntico — e o guard do `main` é **mais restritivo** que o do patch |
| `codex-p0-engineeringnow-missing-path-20260703` | a função que o patch removia **já não existe**; o `main` evoluiu a assinatura e aplicar **quebraria a compilação** |

### Consequência prática

- **Não edite nada no código por causa das worktrees.** A integração correta é não fazer nada.
- **Não rode gate/teste "para conferir".** Nada mudou; suíte verde não prova nada aqui e custa CPU.
- **O risco aqui não é perder trabalho — é reintroduzir trabalho velho.** Todo patch é
  ancestral do código de hoje; aplicá-lo é regressão. Vários nem compilam contra o `main`.
- Os **20 GB podem ser liberados sem perda** (ver §8), mas a decisão é do dono.

---

## 6. Veredito por branch órfão — **nenhum dos 14 precisa ser integrado**

> Revisão concluída em 2026-07-28: um agente por branch, mais refutação adversarial.
> **0 de 14** sobreviveram. Mesmo padrão das worktrees.

### Correção de uma premissa deste documento

A triagem da §4.2 dizia "commits que **nunca** entraram no `main`", calculado por SHA
(`git log main..branch`). **Isso estava errado como conclusão:** ausência de SHA não prova
ausência de conteúdo. O Codex commitava na worktree e, minutos depois, commitava **o mesmo
trabalho** no `main` como commit separado ("integrate …") — a política do próprio branch era
`no_early_merge_manual_contextual_edit_forward_only`. Treze dos 14 são **snapshots
pré-integração**, não trabalho perdido.

**Receita de triagem barata** (use antes de investigar qualquer ref):

```bash
git log --format='%T %H' main > /tmp/maintrees.txt
t=$(git rev-parse <branch>^{tree})
grep -m1 "^$t " /tmp/maintrees.txt   # achou = commit gêmeo no main, conteúdo 100% presente
```

Limite: achar gêmeo **prova presença**; não achar **não prova ausência** (5 dos 14 tinham
árvore idêntica; os outros 9 caíram por comparação arquivo a arquivo).

### Por que não integrar (motivos agrupados)

| motivo | exemplos |
|---|---|
| já no `main`, e o `main` está à frente | `checkselection`: 107 KB hoje vs 15 KB do branch (69 commits a mais) |
| reaplicar **enfraqueceria gate** | `batchdraftgen` do branch usa `PassedSamples=len(items)` em vez de `passed` — o gate passaria por construção. Isso é fraude operacional, proibida |
| reaplicar **não compilaria** | re-registrar check duplica `case` no `switch` de `run()` e nome em `Names` |
| premissa morta | `codex2-mass-scale-coordination` (+7.934 linhas) é coordenação entre **duas instâncias Codex** — o Codex foi desativado em 2026-07-21 |

### Armadilha de leitura (documente antes de duvidar)

Testes de contrato parecem "ausentes" no `main` porque `eecffb2f` (2026-07-21) **shardou**
`internal/contract` em 17 subpacotes. `git diff main:internal/contract/<x>_test.go` falha com
*does not exist in main* — **falso negativo**, não perda de cobertura.

---

## 6-B. Bugs vivos encontrados durante a revisão — ESTES são o trabalho real

A revisão não achou nada a integrar, mas achou **defeitos no `main` de hoje**, ao verificar
se o conteúdo dos branches ainda funcionava.

### 6-B.1 ✅ CORRIGIDO — 11 wrappers `tools/check-*` apontavam para pacote sem `.go`

`eecffb2f` (2026-07-21) shardou `internal/contract` em 17 subpacotes e **esvaziou a raiz**;
os 11 wrappers continuaram chamando `go test … ./internal/contract`. Com `set -euo pipefail`,
abortavam com exit 1 **antes** de chegar ao gate.

Corrigido em 2026-07-28: cada wrapper passou a apontar para o subpacote onde o teste
realmente vive (verificado com `grep -rln "func <Teste>" internal/contract/`). Backup em
`~/.config/ai-terminal-backups/20260728-064215/tools-check-wrappers/`.

| destino | wrappers |
|---|---|
| `internal/contract/authorial` | `check-authorial-mass-contextual-compatibility`, `check-authorial-mass-global-similarity-audit` |
| `internal/contract/codex2` | `check-codex2-datajud-frontier-signal-report`, `check-codex2-datajud-observations`, `check-codex2-source-audit-queue`, `check-codex2-source-candidate-pack`, `check-codex2-source-codex-lock-decision`, `check-codex2-source-frontier`, `check-codex2-source-resolution-matrix` |
| `internal/contract/checkmeta` | `check-ops-check-performance-ledger`, `check-ops-check-selection-profiles` |

**Pendência conhecida (hunk próprio, não misturar):** 5 wrappers ainda usam `go test` cru,
ignorando a toolchain fixada em `.toolchains/` — `check-codex2-datajud-observations:21`,
`check-ops-check-selection-profiles:13`, `check-codex2-datajud-frontier-signal-report:10`,
`check-ops-check-performance-ledger:13`, `check-codex2-source-codex-lock-decision:10`.
Trocar para `go-modern test` em commit separado, para que regressão de toolchain não se
confunda com a correção de caminho.

### 6-B.2 ⚠️ ABERTO — dado de demanda 19 dias fora do schema (estava mascarado)

Corrigir o wrapper acima **revelou** uma falha que estava escondida: o gate
`codex2-source-frontier` reprova, e não por causa da correção.

```
demand_expansion_invalid_json: line=1..18228
jsoncodec: required field semantic_compatibility_family is absent or null
```

| fato | evidência |
|---|---|
| arquivo | `data/research/demand_expansion_opportunities.jsonl` — 43 MB, 18.228 linhas |
| linhas com o campo | **0 de 18.228** |
| campo exigido em | `internal/demandexpansion/demandexpansion.go:62` |
| campo virou obrigatório | `87f07e13` — 2026-07-21 (*fix(factory): centralize semantic intent admission*) |
| dado atualizado pela última vez | `34d6df3d` — 2026-07-02 |

São **19 dias de divergência silenciosa**, e ela só passou despercebida porque o mesmo
commit que a criou (`eecffb2f`, do mesmo dia) quebrou o wrapper que a detectaria.

**Não corrigido de propósito.** O campo faz parte de um trio (`semantic_compatibility_family`,
`_policy_version`, `_policy_fingerprint_sha256`) introduzido pela centralização de admissão
semântica; regerar 43 MB / 18.228 registros de demanda tem efeito em cascata na fábrica, e
fazer isso sem entender o impacto seria imprudente. **Afrouxar o campo para opcional está
descartado** — seria enfraquecer gate, proibido pelo contrato.

Rota provável (validar antes de executar): `tools/generate-demand-expansion-plan` é o gerador
da camada. Antes de rodar: (a) confirmar que ele preenche o trio semântico na versão atual;
(b) verificar que consumidores a jusante aceitam o formato novo; (c) rodar em lote pequeno e
comparar amostra; (d) só então regenerar. Validar com
`./tools/go-modern test -count=1 ./internal/contract/codex2 -run TestCodex2SourceFrontierMaps`.

---

## 7. Como validar cada integração

Depois de reescrever qualquer coisa, valide **de forma proporcional** — nunca com suíte
global, que custa ~5 min de CPU e é desnecessária para mudança localizada:

```bash
# teste focado no pacote tocado
./tools/go-modern test -count=1 ./internal/<pacote>/

# se você adicionou um check, rode só ele
./tools/go-modern run ./cmd/check <nome-do-check>

# comando pesado (full-tree) SÓ envelopado — há hook que bloqueia o contrário
./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./...
```

Um check novo precisa de três coisas para existir de fato:
`case` em `internal/checks/checks.go`, entrada em `Names`, e `_test.go` ao lado do pacote.

---

## 8. O que fazer com as worktrees depois

**Não apague nada por conta própria.** Situação atual:

- o trabalho não commitado está preservado (§3);
- os branches continuam no repositório — qualquer worktree é recriável com
  `git worktree add <caminho> <branch>`;
- as árvores ocupam ~20 GB em `/opt/wiki/.worktrees` e ~3,9 GB em
  `~/.config/superpowers/worktrees`.

Ou seja: o espaço **pode** ser liberado sem perda, mas a decisão é do dono. Se ele
autorizar, o caminho seguro é `git worktree remove` (que recusa árvore suja — sinal de que
sobrou trabalho não preservado), nunca `rm -rf`.

---

## 9. Ordem de execução recomendada

1. Leia §1 e §2 — elas eliminam a maior parte do trabalho antes de começar.
2. Comece pelos itens marcados **CONFIRMADO** nas §5/§6, do menor esforço para o maior:
   entrega valor cedo e cria familiaridade com as áreas.
3. Para cada item: releia o patch/diff como *referência de intenção*, confirme no código de
   hoje que o problema persiste, escreva a solução, rode o teste focado da §7.
4. Commit por frente, com escopo próprio (`git commit -m "..." -- <paths>`), lendo os
   arquivos antes — nunca congelar arquivo em meio-evolução de outra sessão.
5. Registre no `docs/goal/MAESTRO_CODEX_LOG.md` o que integrou e o que descartou, com a
   razão. O próximo a passar por aqui merece o mesmo favor que este documento faz a você.
