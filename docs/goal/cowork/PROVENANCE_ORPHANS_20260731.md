# Órfãos de proveniência em `data/editorial/v2_pages/` — mapa e rota sancionada

**Data:** 2026-07-31 · **Sessão:** cowork (agente de investigação) · **Escopo:** read-only, zero mutação
**Alvo do brief:** transação de proveniência morta em 2026-07-30 22:26, journal `phase=prepared`, seleção exata `data/editorial/v2_pages/telecom_energia-27.jsonl`

---

## Veredito em uma linha

O shard alvo está **íntegro e byte-idêntico ao `original_fingerprint` do journal** (a transação nunca trocou o arquivo); o produtor **tem** recuperação de journal, ela está **desbloqueada** para esta seleção, e os ~275 dotfiles **não são de uma única transação morta** — são recibos autenticados acumulados de **11 dias de execuções distintas**, inertes entre si por escopo de token. **Nada foi deletado. Nada precisa ser deletado à mão.**

---

## 1. Censo exato dos dotfiles

`data/editorial/v2_pages/` tem **286 dotfiles** (excluídos `.` e `..`), assim distribuídos:

### 1.1 Namespace de apply de proveniência — 276 arquivos

| Tipo | Padrão do nome | Qtd |
|---|---|---|
| Recibo `retired` por seleção | `.v2_source_provenance_apply_retired_<64hex>_transaction_selection-<64hex>.tmp` | **199** |
| Recibo `archived` por seleção | `.v2_source_provenance_apply_archived_<64hex>_transaction_selection-<64hex>.tmp` | **68** |
| Recibo `retired` do journal all-finalized | `.v2_source_provenance_apply_retired_<64hex>_transaction_fixed.tmp` | **1** |
| Quarentena de artefato (seleção `a52d501e`) | `.v2_source_provenance_apply_quarantine_<64hex>_selection-{journal×2,output,backup}_a52d501e…-<32hex>.tmp` | **4** |
| Journal vivo (seleção `a52d501e`) | `.v2_source_provenance_apply_selection_a52d501e….journal.json` | **1** |
| Output preparado (seleção `a52d501e`) | `…_output_3da04d86e270fc2facb83ab6450d182f.tmp` | **1** |
| Backup preparado (seleção `a52d501e`) | `…_backup_0771d76713846b7ebbe49d29576056a9.tmp` | **1** |
| Lock do apply | `.v2_source_provenance_apply.lock` (0 bytes, 2026-07-11 09:15) | **1** |

O glob `.v2_source_provenance_apply_*` casa **275** (o lock tem `.` e não `_` após `apply`, por isso fica de fora) — é exatamente o "~275" do brief.

### 1.2 Fora do namespace de proveniência — 10 arquivos

| Tipo | Padrão | Qtd | Nota |
|---|---|---|---|
| Drift CAS staged | `.<shard>.jsonl.stale-cas-dependency-drift-staged-<32hex>` | **6** | glossario-10/14, procedimentos-03, seguros-07, telecom_energia-16 (×2) — **outro subsistema**, não é proveniência |
| Tombstone de transação v2ingest | `.<shard>.jsonl.v2txn-retired-v2-<hex>-<hex>-<hex>.tombstone` | **4** | mtime **2026-07-31** — produzidos hoje pela aposentadoria sancionada da reserva órfã (`retire-v2-ingest-reservation`) |

### 1.3 A premissa "275 órfãos de uma transação morta" é FALSA

Histograma por data dos 275 (`ls --time-style=+%Y-%m-%d`):

```
2026-07-11:   1     2026-07-16:  10     2026-07-29:   6
2026-07-12:  24     2026-07-21:   1     2026-07-30:   7
2026-07-13:   6     2026-07-22:   7
2026-07-14: 159     2026-07-28:   4
2026-07-15:  50
```

**Só 7 arquivos são da transação de 2026-07-30**, e os 7 carregam o mesmo token de seleção `a52d501e0c654df5c1f81fca9ad813d8d07ebd069ee229d58b5b5a439748d7a8`:

```
22:25  10163 B  …_quarantine_267a6f6d…_selection-output_a52d501e…-e82fad7c….tmp
22:25  10073 B  …_quarantine_34dae8b2…_selection-backup_a52d501e…-33650224….tmp
22:25   1423 B  …_quarantine_8cb24c28…_selection-journal_a52d501e…-ae644cce….tmp
22:26   1435 B  …_quarantine_bb1d470c…_selection-journal_a52d501e…-c40fed9d….tmp
22:26   1423 B  .v2_source_provenance_apply_selection_a52d501e….journal.json   <- journal vivo
22:26  10073 B  …_selection_a52d501e…_backup_0771d767….tmp
22:26  10163 B  …_selection_a52d501e…_output_3da04d86….tmp
```

Os outros **268** são recibos de execuções anteriores (pico em 2026-07-14, 159 recibos). O grosso é **acúmulo histórico normal do protocolo**, não escombro de uma falha.

---

## 2. Integridade do shard alvo — CONFIRMADA

```
telecom_energia-27.jsonl          10073 B  mtime 2026-07-30 20:04  1 linha JSON válida
sha256 = eefa68b84a7ae19c9a82df91f369d2798cfab5a7bdaee1143de2bed2da026c1d
```

O journal declara:

```json
"phase":"prepared", "items":[{ "state":"staged",
  "original_fingerprint":"sha256:eefa68b84a7ae19c9a82df91f369d2798cfab5a7bdaee1143de2bed2da026c1d",
  "output_fingerprint":"sha256:505358720b0cebe1333677eb16007296e2e04156a460a10ccb4fc18102909fa6",
  "original_inode":27957307, "output_inode":27957366, "backup_inode":27957367 }]
```

Verificação de hash em disco:

| Arquivo | sha256 | Bate com |
|---|---|---|
| `telecom_energia-27.jsonl` | `eefa68b8…` | **`original_fingerprint`** ✔ |
| `…_backup_0771d767….tmp` | `eefa68b8…` | `original_fingerprint` ✔ (cópia fiel) |
| `…_output_3da04d86….tmp` | `50535872…` | **`output_fingerprint`** ✔ |

**Conclusão:** a transação parou entre `prepare` e `commit`. O `exchange` para o arquivo canônico **nunca aconteceu** — o shard está no estado pré-transação, íntegro, e o output preparado também está íntegro. Não há perda de dado nem estado meio-escrito.

---

## 3. Inspeção read-only executada

O binário já existe pré-buildado (**não foi preciso build**):

```
.cache/go-cmd-bin/audit-v2-source-provenance/audit-v2-source-provenance   (2026-07-30 22:28)
```

`internal/v2sourceprovenance/check.go` não tem **nenhuma** chamada de mutação (`os.WriteFile`/`os.Rename`/`os.Remove`/`OpenFile`/`exchange`) — o caminho `--check` é comprovadamente read-only. Executado com guarda de hash antes/depois:

```bash
./.cache/go-cmd-bin/audit-v2-source-provenance/audit-v2-source-provenance \
  -root /opt/wiki -check -file data/editorial/v2_pages/telecom_energia-27.jsonl
```

Saída (exit 0):

```
v2-source-provenance: check=current-selection-pass release_eligible=false scope=incomplete
  records=2 verified=2 blocked=0
  path=data/source-registry/v2_source_provenance_live_evidence_sets/exact-a52d501e….jsonl
  publication=false
```

Guarda: hash do shard **idêntico** antes e depois; contagem de entradas do diretório **idêntica** (1036). Zero mutação.

**Achado:** o conjunto de evidências da seleção exata **existe, é válido e está verde** (`verified=2, blocked=0`), no mesmo token `a52d501e`. A transação morta não deixou a evidência inconsistente.

---

## 4. O produtor tem recovery de journal? SIM — e está desbloqueado

`internal/v2sourceprovenance/apply.go:274` chama `recoverApplyJournalForSelection(projectRoot, requestedSelection, operations)` **como primeiro passo** de `ApplyWithOptions`, antes de validar evidência. A recuperação é keyed pela seleção: `applyJournalPathForSelection` (apply.go:804) só enxerga o journal cujo token bate com a seleção pedida.

### 4.1 As três guardas de entrada — todas passam para `a52d501e`

`applyJournalReceiptGlob` (apply.go:1445-1451) monta `prefix + "*_transaction_" + token + ".tmp"`, e `applyArtifactKindToken` (apply.go:1284-1290) mapeia o journal de seleção para `kind="transaction", token="selection-a52d501e…"`.

| Guarda | Glob efetivo | Matches | Resultado |
|---|---|---|---|
| `validateArchivedApplyJournals` (1828) | `…_archived_*_transaction_selection-a52d501e….tmp` | **0** | passa |
| `validateAbortedApplyJournals` (1857) | `…_aborted_*_transaction_selection-a52d501e….tmp` | **0** | passa |
| `recoverFixedApplyJournalFromQuarantine` (1989) | `…_quarantine_*_transaction_selection-a52d501e….tmp` | **0** | passa (`len(matches)==0 → return nil`) |

**Ponto crítico verificado:** as 4 quarentenas de `a52d501e` têm `kind` = `selection-journal` / `selection-output` / `selection-backup` (apply.go:1300-1311), **não** `transaction`. Portanto **não** disparam o `fmt.Errorf("fixed journal coexists with transaction quarantine …")` da linha 2009 nem o `"multiple transaction journal quarantines found"` da linha 2012. Esse era o único risco de fail-closed terminal e ele **não se aplica**. As 4 caem no glob de artefato (`applyQuarantineGlobForArtifactPrefix`, 2262-2270, que exclui `kind=="transaction"`) e são **restauradas**, não bloqueantes — e as 2 quarentenas de journal restauram para paths **distintos** (sufixos `ae644cce` vs `c40fed9d`), sem colisão de `RENAME_NOREPLACE`.

### 4.2 Trajetória prevista da recuperação

Com `phase=prepared` (≠ `committed`), o laço de rollback (apply.go:1670+) roda por item:

1. `regularFileStateIfExists(target)` → presente, regular ✔
2. `authenticatedOriginalState(targetState, item)` → **TRUE** (hash+device+inode batem com `original_*`)
3. `findUnexpectedRecoveryArtifact(outputPath, backupPath, item)` → output autentica como `output_fingerprint`, backup autentica como `original_fingerprint` → **`unexpected=false`**
4. → `continue` → finaliza sem conflito; journal fechado e artefatos da seleção varridos por `cleanupOrphanApplyArtifacts` (2149) / `cleanupReservedApplyArtifacts` (2158)

Ou seja: **rollback limpo, sem tocar no conteúdo do shard** (ele já está no estado original), seguido da re-execução da transação com a evidência verde.

### 4.3 Os 268 recibos antigos são INERTES

Cada recibo `retired`/`archived` carrega o token da **sua** seleção no nome (`_transaction_selection-<64hex>.tmp`) e só é lido pelo glob daquela seleção. Nenhum deles casa o glob de `a52d501e`. Eles **não bloqueiam** a recuperação do alvo nem qualquer outra seleção que não seja a própria. O único de escopo global é `…_retired_<64hex>_transaction_fixed.tmp` (token `fixed`, apply.go:1286), que pertence ao journal all-finalized `.v2_source_provenance_apply.journal.json` e é tratado por `recoverRetiredApplyJournal` (1745) — relevante apenas para um `--apply` **sem** `-file`.

---

## 5. Rota sancionada de recuperação

Não existe (nem deve existir) flag de "recovery" isolada: a recuperação é acoplada ao entrypoint de apply, por desenho. A rota é **re-executar o apply da mesma seleção exata**.

### Comando exato

```bash
cd /opt/wiki && ./tools/go-modern run ./cmd/audit-v2-source-provenance \
  -root /opt/wiki -apply \
  -file data/editorial/v2_pages/telecom_energia-27.jsonl
```

Equivalente sem build (binário pré-existente de 2026-07-30 22:28) — **ver ressalva em 5.2**:

```bash
cd /opt/wiki && ./.cache/go-cmd-bin/audit-v2-source-provenance/audit-v2-source-provenance \
  -root /opt/wiki -apply \
  -file data/editorial/v2_pages/telecom_energia-27.jsonl
```

**Não executado nesta sessão** — `--apply` **muta** dado editorial (enriquece campos de fonte no shard) e está fora do mandato read-only deste levantamento.

### 5.1 O `-file` é obrigatório e tem que ser idêntico

O token de seleção é derivado do conjunto de arquivos (`applySelectionToken`). Rodar `--apply` **sem** `-file`, ou com outro conjunto, calcula **outro** `journalPath` e **não** recupera o journal `a52d501e` — ele continuaria órfão. O caminho `--apply` também exige que `LoadEvidenceForFiles` case a mesma seleção (`inputSelectionsEqual`, apply.go:282-289), e isso já foi confirmado verde no §3.

### 5.2 Ressalva de portabilidade no sandbox Cowork

`cmd/audit-v2-source-provenance/main.go:184-200` chama `v2ingest.VaultTerminalV2Artifacts` **depois** de `ApplyWithOptions`. O binário em `.cache/go-cmd-bin/` é de 2026-07-30 22:28 e **não contém** o patch de portabilidade `O_TMPFILE`/`renameat2` que está hoje no worktree não-commitado (`internal/v2ingest/transaction_safe_io.go` +178 linhas, `transaction_lock.go` +36, fallback para `EOPNOTSUPP`/`EPERM` medido no mount do sandbox). Consequência prática:

- a **recuperação + apply já terão sido concluídos** quando o passo de vault rodar (ordem no `main.go`);
- mas o vault pode falhar com `EOPNOTSUPP` no sandbox, produzindo `fail("terminal artifact vault … ")` e **exit ≠ 0 enganoso**.

**Recomendação:** rodar pela rota `./tools/go-modern run` (rebuilda com o worktree corrigido) **ou** rodar no host, onde o filesystem suporta `O_TMPFILE`. Isso liga esta rota à task `go-fix-v2ingest-portabilidade-pendente-commit` do frontboard.

### 5.3 O que NÃO fazer

- **Não deletar** nenhum dotfile à mão. Os recibos são **autenticados** (`applyStateAttestation` compara sha256 embutido no nome com o conteúdo); apagá-los destrói prova e pode deixar uma seleção futura sem o recibo que a sua própria recuperação espera.
- **Não forjar** journal, tombstone ou recibo — mesmo princípio já registrado na task `reserva-orfa-bloqueia-ingest` ("PROIBIDO fabricar o tombstone à mão … forjar um seria fraude").
- **Não aumentar timeout** como "correção".
- **Não** rodar `--apply` sem `-file` esperando que ele limpe o alvo: varre outro token.

### 5.4 Sobre o lock de 2026-07-11

`.v2_source_provenance_apply.lock` tem **0 bytes** e mtime **2026-07-11 09:15**. É o lock do namespace de apply. Sem processo vivo há 20 dias, é resíduo — mas **não bloqueia** (o `--check` de hoje rodou normalmente com ele em disco). Deixado intacto.

---

## 6. Dívida de engenharia identificada (não bloqueante hoje)

1. **Sem GC de recibos.** 268 recibos `retired`/`archived` acumulados em 11 dias, sem lane de coleta. Em ritmo de 10k páginas isso vira dezenas de milhares de entradas de diretório em `data/editorial/v2_pages/` — e `internal/v2ingest/transaction.go:65` tem `transactionGuardMaxDirectoryEntries=20_000` (já registrado na task `envelope-incoerente-pos-raise`). **Os recibos contam para esse teto.** Vale um GC offline sancionado que preserve no vault antes de remover, no mesmo padrão da aposentadoria de reserva.
2. **Journal órfão não é observável.** Nenhum check reporta "existe journal `prepared` sem dono". O `.gitignore:60` (`data/editorial/v2_pages/.v2_source_provenance_apply*`) esconde tudo do `git status`, então um journal parado fica invisível indefinidamente — este ficou 1 dia sem ninguém notar. Um `check-*` read-only que liste journals `phase != committed` com idade > N horas seria barato e fecharia o buraco.
3. **`--apply` acopla vault e transação.** Falha do vault mascara sucesso do apply com exit ≠ 0 (§5.2).

---

## 7. Evidência reproduzível

```bash
# censo
ls -a /opt/wiki/data/editorial/v2_pages | grep -c '^\.'                       # 288 (inclui . e ..)
ls -a /opt/wiki/data/editorial/v2_pages | grep -c '^\.v2_source_provenance_apply_'   # 275
ls -a /opt/wiki/data/editorial/v2_pages | grep -c 'a52d501e0c654df5c1f81fca9ad813d8d07ebd069ee229d58b5b5a439748d7a8'  # 7

# integridade do alvo
sha256sum /opt/wiki/data/editorial/v2_pages/telecom_energia-27.jsonl
# eefa68b84a7ae19c9a82df91f369d2798cfab5a7bdaee1143de2bed2da026c1d  == original_fingerprint

# inspeção read-only (exit 0, zero mutação)
/opt/wiki/.cache/go-cmd-bin/audit-v2-source-provenance/audit-v2-source-provenance \
  -root /opt/wiki -check -file data/editorial/v2_pages/telecom_energia-27.jsonl
```

Referências de código: `internal/v2sourceprovenance/apply.go` linhas 274 (entrada da recuperação), 804-825 (paths/prefixos por seleção), 1284-1314 (`applyArtifactKindToken`), 1398-1418 (`parseApplyQuarantinePath`), 1445-1451 (`applyJournalReceiptGlob`), 1638-1743 (`recoverApplyJournalForSelection`), 1828-1884 (validação de archived/aborted), 1989-2030 (`recoverFixedApplyJournalFromQuarantine`), 2149-2182 (cleanup de órfãos), 2230-2270 (recuperação de quarentena por prefixo); `cmd/audit-v2-source-provenance/main.go` linhas 139-176 (`--check`, read-only) e 177-204 (`--apply` + vault).
