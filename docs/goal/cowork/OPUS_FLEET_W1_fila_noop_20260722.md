# OPUS_FLEET_W1 — `fila-noop-filter` (P1): filtrar lotes no-op (reuse==n) no produtor da fila

Onda Cowork Opus (W1), 2026-07-22. **READ-ONLY / NOOP** — nenhuma edição aplicada ao disco.
O patch abaixo é a ENTREGA para o main aplicar após o regen atual liberar o flock.

Frontboard: `{"id":"fila-noop-filter","priority":1}` — "Produtor da fila: filtrar lotes no-op
(reuse==n, 24/64 na part1) — nao queimar redator em reescrita byte-identica; resolver claim sem
agente. Alvo: generate_v2_review_queue.py (sob flock ate o regen atual terminar). Com o breaker
>=5 falhas/janela, no-ops em bloco param a fila."

---

## SCOPE

Um "lote no-op" é um lote de escrita cujo slice inteiro já está materializado no shard —
`reuse` (as páginas já válidas e preserváveis byte a byte) cobre TODOS os `n` intents esperados —
e que não tem nenhuma mutação estrutural pendente (sem raw-recovery, sem migração integral, sem
remoção de relocação semântica). Como o contrato da fila de escrita **obriga a preservar cada
página reusada byte a byte** (`preserved_record_sha256`, autenticado no CAS), esse lote **não pode
autorar nem corrigir nada**: o staged sairia idêntico ao alvo. Lançar um redator nele (a) queima um
agente à toa e (b) alimenta o circuit breaker (detalhe na ROOT CAUSE). O objetivo é **resolver o
claim sem agente** e **nunca deixá-lo chegar à janela do breaker**, preservando 100% do trabalho
real (raw-recovery, migração, relocação, reuse parcial continuam indo ao redator).

---

## WHAT I READ (file:line)

- **`tools/generate_v2_review_queue.py`** (produtor da fila, o alvo nomeado; 5.897 linhas):
  - `L88-89` `DEFAULT_EXACT_COMPONENT_WAVE_MEMBERS=24`, `MAX_EXACT_COMPONENT_WAVE_MEMBERS=31` (teto).
  - `L155-160` `class BatchCompletion(complete, reusable_expected, authenticated_extras)`.
  - `L2816-2962` `classify_batch_completion(...)` → devolve `complete` (presença estrutural exata:
    ordem == slice+extras) e `reusable_expected` (intents preserváveis byte a byte).
  - `L1900-1959` `derive_writing_raw_recovery_projection(...)` → projeção raw-recovery (`reuse` =
    subconjunto seguro reconstruído); `L2240-2569` `verify_staged_writing_source_resolution(...)`
    autentica o staged do redator e **exige `preserved_record_sha256` byte a byte** para o reuse.
- **`ops/relaunch-writing.sh`** (emissor da fila; importa `producer`, sob o mesmo flock):
  - `L629-632` inicialização dos contadores (`excluded_batches`, `deferred_supersession_batches`).
  - `L714-727` init por-lote: `have_valid=[]`, `raw_recovery=writing_raw_recovery.get(f)`; se
    raw-recovery, `have_valid=list(raw_recovery['reuse'])`.
  - `L761-817` chama `producer.classify_batch_completion(...)`; `have_valid =
    list(completion.reusable_expected)`; **`L817` `ok = completion.complete and not
    semantic_relocation_removals`**.
  - `L823-824` **`if ok: return ('ready', None)`** (único caminho hoje que resolve sem redator).
  - `L825-864` monta o `item` do redator: **`L845` `item['reuse'] = have_valid`** → `return
    ('queued', item)`.
  - `L871-889` laço "reportar-tudo": agrega `excluded`/`deferred`/`ready`/`queued`.
  - `L1035` linha de resumo.
- **`scripts/workflows/writing-mass.js`** / **`writing-mass-todo-part1.js`** (consumidor; o breaker):
  - `L731` **`CHUNK = 6`**; `L763-771` **`hardFails >= Math.max(2, Math.ceil(window.length*0.75))`
    → `= Math.max(2, 5) = 5`** dispara o `CIRCUIT BREAKER` e para a fila.
  - `L658` claim válido exige `written === n`; `L676-680` **`wellFormedBatchProgress` exige
    `result.audited_sha256 !== batch.target_sha256`** (tem de haver mudança real).
  - `L523-526` prompt de reuse: "PRESERVE cada linha byte a byte ... escreva APENAS as intencoes
    faltantes do slice."

**Ground truth (parse read-only do `writing-mass-todo-part1.js` vigente):** 48 lotes; **17 com
`reuse.length === n`** (o frontboard citou 24/64 de um regen anterior — mesma classe, número varia
por regen). Dos 17: 15 têm `writing_recovery` (reconstrução real → NÃO são no-op), 2 são
byte-idênticos completos (`imobiliario-10` n=9/reuse=9/disk=17 com 8 extras; `imobiliario-22`
n=12/reuse=12/disk=14 com 2 extras) — no-op puro. `disk_lines == n(+extras)` em todos.

---

## ROOT CAUSE

O único curto-circuito "sem redator" hoje é `L823 if ok:` com `ok = completion.complete and not
semantic_relocation_removals` (`relaunch-writing.sh:817`). Ele só dispara na igualdade estrutural
ESTRITA (`complete`: ordem exata == slice+extras). Lotes cujo slice já está **inteiramente
materializado** (`reuse==n`) mas que **não** satisfazem `complete` (ordem/posição de extras, ou a
fila foi gerada antes de as páginas assentarem) **escapam como `('queued', …)`** e viram job de
redator com `item['reuse'] = have_valid` (todos os n).

Por que isso **para a fila** (mecanismo exato, não hipótese):
1. O contrato da fila **proíbe** o redator de alterar página reusada (`preserved_record_sha256`
   autenticado byte a byte no CAS, `verify_staged...:2556-2559`). Logo, um lote `reuse==n` produz
   staged **byte-idêntico ao alvo** → `audited_sha256 === target_sha256`.
2. O consumidor só conta "progresso" quando `wellFormedBatchProgress` é verdadeiro, e este **exige
   `audited_sha256 !== target_sha256`** (`writing-mass*.js:679`). Um no-op **nunca** consegue
   progresso — por definição.
3. Quando as páginas pré-existentes ainda carregam **qualquer** defeito do auditor (o motivo comum
   de o shard estar na fila), o claim sai `audit_ok=false`; sem progresso possível → **hard-fail
   garantido**.
4. `CHUNK=6` ⇒ breaker em `hardFails >= 5`. Um bloco de no-ops (17 aqui, 24 no regen do fiscal)
   distribuído nas janelas de 6 leva alguma janela a `>=5` → `halted=true` → **descarta os lotes
   BONS restantes** ("parando para nao desperdicar os N lotes restantes").

Ou seja: o produtor emite trabalho que é estruturalmente **incapaz de progredir** e que o breaker
foi desenhado para matar — um falso-positivo do breaker causado pela emissão. Correção de conteúdo
das páginas existentes **não é** tarefa da fila de escrita (que as preserva byte a byte); é da fila
de review (`ops/relaunch-review.sh`). Portanto **dropar o lote no-op não perde trabalho algum**.

---

## PATCH (diff)

Dois hunks aditivos: (1) a lógica-filtro canônica e testável no **produtor nomeado**
(`generate_v2_review_queue.py`); (2) o wiring mínimo de emissão no **emissor** que importa o
produtor (`ops/relaunch-writing.sh`). Nada existente muda de semântica — só um novo status `'noop'`
que resolve o claim antes do `if ok:`.

### Hunk 1 — `tools/generate_v2_review_queue.py` (nova função pura, após `classify_batch_completion`)

```diff
@@ -2959,6 +2959,66 @@ def classify_batch_completion(
         reusable_expected=tuple(
             intent for intent in reusable if occurrences[intent] == 1),
         authenticated_extras=tuple(extras),
     )
 
 
+def writer_noop_batch(
+    reusable_expected: Iterable[str],
+    expected_n: int,
+    *,
+    semantic_relocation_removals: Iterable[Any] = (),
+    authenticated_replacement: bool = False,
+    writing_recovery: Any = None,
+) -> bool:
+    """True quando o redator não teria NADA a autorar (no-op byte-idêntico).
+
+    Um lote de escrita só é no-op quando o slice inteiro já está materializado
+    no shard — ``reusable_expected`` (o ``reuse`` do lote) cobre os
+    ``expected_n`` intents esperados — e não resta mutação estrutural para um
+    redator: nenhuma remoção de relocação semântica (que apaga linhas), nenhuma
+    substituição/migração integral autenticada e nenhuma reconstrução
+    raw-recovery (que reescreve linhas corrompidas). O contrato da fila obriga a
+    PRESERVAR cada página reusada byte a byte (``preserved_record_sha256`` no
+    CAS), logo um lote reuse==n não pode autorar nem corrigir nada: o staged
+    sairia idêntico ao alvo (``audited_sha256 == target_sha256``) e jamais
+    satisfaz o ``wellFormedBatchProgress`` do consumidor — com qualquer defeito
+    residual do auditor vira hard-fail garantido e alimenta o circuit breaker
+    (>=5 por janela de 6). A fila deve RESOLVER esse lote sem agente; defeitos
+    de qualidade das páginas existentes seguem pela fila de review, nunca por um
+    redator de volume proibido de tocá-las. Função pura (sem I/O), aditiva: não
+    afrouxa nenhum gate — apenas evita emitir trabalho incapaz de progredir.
+    """
+    if (not isinstance(expected_n, int) or isinstance(expected_n, bool) or
+            expected_n < 0):
+        raise ValueError("expected_n deve ser inteiro não negativo")
+    # Qualquer mutação estrutural pendente = trabalho real → NÃO é no-op.
+    if authenticated_replacement or writing_recovery is not None:
+        return False
+    if tuple(semantic_relocation_removals):
+        return False
+    reuse = tuple(reusable_expected)
+    if any(not isinstance(intent, str) or _INTENT_ID.fullmatch(intent) is None
+           for intent in reuse):
+        raise ValueError("reusable_expected deve conter intents canônicos")
+    if len(set(reuse)) != len(reuse):
+        raise ValueError("reusable_expected não pode repetir intent")
+    # No-op ⟺ o reuse já cobre todo o slice esperado e nada mais precisa ser
+    # escrito. expected_n>0 evita marcar um lote vazio como resolvido.
+    return expected_n > 0 and len(reuse) == expected_n
+
+
 def _parse_ngram_target(raw_target: str) -> tuple[str, str]:
     """Parse the auditor's symmetric ``intent~peer`` edge notation."""
     if raw_target.count("~") != 1:
```

*(`Iterable`, `Any` e `_INTENT_ID` já são símbolos do módulo — nenhum import novo.)*

### Hunk 2 — `ops/relaunch-writing.sh` (wiring de emissão: novo status `'noop'`)

**2a — contador (após L630):**

```diff
@@ -629,6 +629,7 @@ excluded_batches = 0
 excluded_batches = 0
 deferred_supersession_batches = 0
+noop_batches = 0
 supersession_projection_unavailable = False
 supersession_projection_issue_count = 0
```

**2b — filtro no-op ANTES de `if ok:` (após L822, no ponto onde `have_valid`, `raw_recovery`,
`migration_authorization` e `semantic_relocation_removals` já estão TODOS ligados nos dois ramos):**

```diff
@@ -820,6 +821,20 @@ def process_batch(b):
         except (OSError, json.JSONDecodeError):
             ok = False
+    # NO-OP: lote cujo slice inteiro já está materializado (reuse cobre os n
+    # esperados) e sem reconstrução raw-recovery, migração integral ou remoção
+    # de relocação NÃO tem nada para um redator autorar. Emiti-lo queima um
+    # agente e, como o staged sairia byte-idêntico (audited_sha256 ==
+    # target_sha256), nunca satisfaz o wellFormedBatchProgress do consumidor:
+    # com qualquer defeito residual do auditor vira hard-fail garantido e
+    # dispara o circuit breaker (>=5/janela de 6). Resolve-se sem agente; a
+    # página já existe e o defeito residual segue pela fila de review
+    # (ops/relaunch-review.sh), não por um redator de volume.
+    if producer.writer_noop_batch(
+            have_valid, b['n'],
+            semantic_relocation_removals=semantic_relocation_removals,
+            authenticated_replacement=(migration_authorization is not None),
+            writing_recovery=raw_recovery):
+        return ('noop', None)
     if ok:
         return ('ready', None)
     item = dict(b)
```

**2c — agregação do novo status (no laço L882-889):**

```diff
@@ -883,6 +898,8 @@ for b in batches:
     if status == 'excluded':
         excluded_batches += 1
     elif status == 'deferred':
         deferred_supersession_batches += 1
+    elif status == 'noop':
+        noop_batches += 1
     elif status == 'ready':
         prontos += 1
     elif status == 'queued':
         todo.append(payload)
```

**2d — resumo (L1035): acrescentar o token (sem remover nada):**

```diff
@@ -1035 +1052 @@ print(
-print(f"prontos={prontos} faltantes={len(todo)} lotes_com_reuso={com_reuso} lotes_raw_recovery={com_raw_recovery} lotes_adiados_sem_epoch_dec020={deferred_supersession_batches} issues_epoch_dec020={supersession_projection_issue_count} lotes_excluidos_por_area={excluded_batches}")
+print(f"prontos={prontos} faltantes={len(todo)} lotes_noop={noop_batches} lotes_com_reuso={com_reuso} lotes_raw_recovery={com_raw_recovery} lotes_adiados_sem_epoch_dec020={deferred_supersession_batches} issues_epoch_dec020={supersession_projection_issue_count} lotes_excluidos_por_area={excluded_batches}")
```

*(2d é reescrita de 1 linha; mantém `paginas_faltantes=...` e todos os tokens existentes — só
insere `lotes_noop=`. `com_reuso` cai naturalmente porque os no-op puros deixam `todo`.)*

---

## TEST

### Unidade da função pura (harness estilo `internal/contract/v2/v2_review_queue_producer_test.go`, Python-in-Go)

```python
from tools import generate_v2_review_queue as producer

# no-op: reuse cobre todo o slice, sem trabalho estrutural
assert producer.writer_noop_batch(['a-1', 'a-2'], 2)
assert producer.writer_noop_batch(['a-1', 'a-2', 'a-3'], 3)
# reuse parcial ou zero -> redator real
assert not producer.writer_noop_batch(['a-1'], 2)
assert not producer.writer_noop_batch([], 3)
assert not producer.writer_noop_batch([], 0)          # lote vazio nunca é "no-op resolvido"
# qualquer mutação estrutural com reuse==n ainda é trabalho real
assert not producer.writer_noop_batch(['a-1', 'a-2'], 2, writing_recovery={'reuse': ['a-1']})
assert not producer.writer_noop_batch(['a-1', 'a-2'], 2, authenticated_replacement=True)
assert not producer.writer_noop_batch(['a-1', 'a-2'], 2,
                                      semantic_relocation_removals=[{'intent_id': 'x-9'}])
# entradas não canônicas / duplicadas são recusadas fail-closed
for bad in (lambda: producer.writer_noop_batch(['a-1', 'a-1'], 2),
            lambda: producer.writer_noop_batch(['A B'], 1),
            lambda: producer.writer_noop_batch(['a-1'], True)):
    try:
        bad(); assert False
    except (ValueError, TypeError):
        pass
```

### Cenário 64 lotes → 40 redatores, 0 breaker, 24 no-op (o alvo pedido)

Monte um inventário sintético de **64 lotes**: **24** com `reuse==n` e sem
raw/migração/relocação; **40** com trabalho real (mix de `reuse<n`, `reuse==0` e alguns com
`writing_recovery`). Rode a classificação de emissão de `process_batch` (ou chame direto
`producer.writer_noop_batch` no ponto de emissão). Asserções:

- **`noop_batches == 24`** e nenhum desses 24 aparece em `todo`.
- **`len(todo) == 40`** (todos os lotes com trabalho real emitidos como job de redator, inclusive
  os `writing_recovery` de `reuse==n`, que o filtro NÃO derruba).
- **`prontos`/`excluded`/`deferred` inalterados** vs. baseline sem o filtro (o `'noop'` só
  intercepta o que antes ia para `'queued'` como job incapaz de progredir).
- **0 breaker trips:** como os 24 no-ops nunca entram em `runnableBatches`, nenhuma janela de 6 do
  consumidor recebe hard-fail de no-op; `halted` permanece `false` ao processar os 40 reais.
  (Contraprova pré-fix: com 24 no-ops incapazes de progresso, `ceil(24/…)` janelas atingiriam
  `hardFails>=5` e `halted=true` descartaria a cauda de lotes bons.)

Regressão barata recomendada: incluir 1 dos no-ops reais do part1 (`imobiliario-10`) como fixture
para provar `writer_noop_batch(reuse_de_9, 9, ...) is True`.

---

## SAFE-APPLY NOTE (flock / regen)

- `generate_v2_review_queue.py` **e** `ops/relaunch-writing.sh` estão sob M/diff ao vivo e o regen
  atual segura `/tmp/opt-wiki-agent-heavy.lock` (ANEXO_SUBSISTEMAS §4 "CRÍTICO transversal";
  frontboard: "sob flock ate o regen atual terminar"). **Aplicar SÓ depois de o regen liberar o
  flock**, coordenando por `.agents/runtime/coordination/` (`tools/generate-coord-presence` +
  `check-coord-inbox`) e `tools/check-load-headroom --max 12` antes de qualquer comando. O
  frontboard pede aplicar **junto com o repin pós-catálogo** — casar as duas edições no mesmo
  ciclo.
- **Sem rebuild Go:** patch é 100% Python + shell; o pre-commit leve (DEC-002) não builda (não toca
  Go/go.mod/go.sum) — commit de conteúdo, leve e frequente.
- **Purga dos no-ops já emitidos:** após aplicar, **re-emitir** a fila via `ops/relaunch-writing.sh`
  regenera `writing-mass-todo-part1.js` sem os 17 lotes `reuse==n` (idempotente, re-tenta só o que
  falta). Enquanto não re-emitir, o `writing-mass-todo-part1.js` vigente ainda contém os no-ops — se
  ele rodar, o breaker pode disparar (comportamento atual). Preferir re-emitir antes de nova onda.
- **Validação proporcional:** rodar só o teste do produtor
  (`./tools/go-modern test -count=1 -run 'TestV2WritingQueue' ./internal/contract/v2/`) + um dry-run
  de `ops/relaunch-writing.sh` conferindo `lotes_noop=` no resumo. Sem `lab-cycle`.

---

## COLLISION-SAFETY NOTE

- **Aditivo, sem sobrescrever evolução concorrente.** Novo símbolo `writer_noop_batch` (grep
  repo-wide: **zero** colisão), novo status `'noop'` (zero colisão em `tools/`/`scripts/`), novo
  contador `noop_batches`, novo token `lotes_noop=`. `classify_batch_completion` e o CAS de
  `verify_staged...` ficam **byte-idênticos** — a fronteira anti-fraude e os gates de conteúdo do
  §2 do plano-mãe não são tocados.
- **Nenhuma linha existente muda de semântica.** O único ponto sensível é inserir o `if
  writer_noop_batch(...)` ANTES do `if ok:` — para lotes NÃO no-op o caminho é idêntico ao de hoje
  (`ready`/`queued`). Lotes raw-recovery caem no ramo `raw_recovery is not None` (L721), chegam ao
  filtro com `writing_recovery=raw_recovery` (não-None) → `writer_noop_batch` retorna `False` →
  seguem como `queued`. Migração autenticada retorna `BatchCompletion(False,(),())` (L2883) →
  `have_valid==[]` → `False`. Shard novo (sem preimagem) → `have_valid==[]` → `False`.
- **Edição pontual** em ambos os arquivos concorrentes: hunks pequenos, sem rewrite, preservando
  qualquer escrita não-commitada em voo. Se `L817`/`L823`/`L1035` tiverem drift no momento de
  aplicar (arquivo sob diff), reancorar pelos marcadores textuais (`ok = completion.complete`,
  `if ok:\n        return ('ready', None)`, `prontos={prontos} faltantes=`) em vez do número de
  linha.
- **Opcional (defesa em profundidade, NÃO no patch mínimo):** no consumidor, tratar claim com
  `audited_sha256 === target_sha256 && written === n` como no-op resolvido (não hard-fail) —
  cinto-e-suspensório caso um no-op residual escape de uma fila antiga. O fix primário (produtor)
  já garante que no-op nenhum chega à janela do breaker.
