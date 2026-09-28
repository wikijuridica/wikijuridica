# Rota do commit do fix Go de portabilidade (O_TMPFILE / renameat2) — 2026-07-31

Investigação medida no sandbox Cowork (2 núcleos, `/sessions/wonderful-inspiring-pascal/mnt/wiki`
= bind mount de `/opt/wiki`). Toda medição abaixo foi executada, não estimada. Nenhum comando
alterou índice, worktree, refs ou objetos do repo — as provas usam snapshots descartáveis em
`/tmp` reconstruíveis em segundos (`git archive`), nunca produto.

**Estado vivo de referência: HEAD `6b48b48c`.** Durante a própria investigação o HEAD avançou
(`5f1bb540` → `6b48b48c`) e a frente concorrente **reescreveu `transaction_safe_io.go` às
08:38** (endurecimento contra temp órfão `.v2txn-install-*`, `retireOrphanNamedInstallTemp`).
Todos os números abaixo foram **refeitos sobre os bytes atuais**; a conferência de sha256 do
passo 1 da rota existe exatamente para pegar esse tipo de deriva — foi ela que pegou.

## 0. Veredito

1. **O pre-commit NÃO roda `go build ./...`.** Ele roda uma *compile closure* do índice
   candidato: gofmt dos blobs staged + `go list -deps -test -export` só dos pacotes afetados.
   Nada de vet, nada de teste, nada de linkedição. Para este fix a rota é a **direta**
   (só `internal/v2ingest`), medida em **22,9 s a frio / 2,3 s a quente** com 2 núcleos.
   Orçamento default do hook: **90 s**. Cabe com folga — não precisa de warm-up, não precisa
   elevar timeout.
2. **O commit tem que ser parcial por pathspec.** O índice já tem centenas de arquivos de dados
   staged por outra frente (mais 2 arquivos Go). `git commit -- <paths>` monta a árvore
   candidata como HEAD + esses paths, não toca a worktree nem o resto do índice, e ainda evita
   acordar os gates pesados de produto v2 do hook `reference-transaction`.
3. **Achado P0 fora do escopo original:** o `validator_fingerprint_attestation_generated.go`
   está **stale no HEAD** desde `d101c5e3` — a atestação commitada não corresponde ao grafo
   commitado. Isso deixa ~10 testes de `internal/v2ingest` vermelhos em checkout limpo e é
   exatamente a classe de erro que o gate de stock-freshness converte em bloqueio de ingest.
   Nenhum check/gate guarda esse arquivo; o pre-commit não o enxerga. **O commit deste fix é a
   oportunidade barata de fechar essa dívida** (a constante já está calculada abaixo).

## 1. O que o `.githooks/pre-commit` realmente executa

Ordem real (arquivo lido inteiro, 232 linhas):

1. Autentica os binários confiáveis (`git`, `nice`, `env`, `timeout`, `python3`, …) — exige dono
   root **ou** uid de overflow 65534 sob userns com root não mapeado (correção 2026-07-29 que
   destravou commit no sandbox).
2. `git diff --cached --quiet -- .` → **se não há delta staged, não faz nada**.
3. Havendo delta, materializa `tools/check-go-index-compile-closure` **do blob do índice
   candidato** (não da worktree — outra frente editando o checker não impede o commit) e o
   executa com `--budget-seconds` (default 90) sob `timeout` externo de `budget+5`.
4. O checker roteia:
   - delta que não cai em nenhum diretório de pacote Go → **SKIP**
     (`go-index-compile-closure: SKIP reason=no_staged_build_impact`), sub-segundo — medições
     registradas no repo: `elapsed_ms=192` e `elapsed_ms=720`
     (`docs/goal/CADEIA_APROVACAO_ATRITO_MEDIDO_20260728.md:193,259`);
   - delta Go → **gofmt** de cada `.go` staged (blob do índice, não a worktree) e depois
     classificação estrutural da superfície de API (helper Go com AST, `direct_only`):
     - só mudança de corpo / adição **privada** → rota **direta**: compila apenas os pacotes
       alterados;
     - superfície exportada mexida / arquivo adicionado ou removido / mudança de `go.mod` →
       rota **reversa**: compila também todos os dependentes reversos (`go list -test -json ./...`
       para descobrir);
   - o compile em si é `tools/check-go-compile-closure`:
     `go list -tags=devcmds -deps -test -export -mod=readonly -buildvcs=false <pacotes>` —
     compila e type-checka produção + `devcmds` + variantes de teste, **sem linkar executável**.
5. Revalida índice, blobs e runtime depois da compilação (nada mudou durante o gate) e imprime
   `go-index-compile-closure: PASS files=… affected_packages=… closure_mode=direct|reverse …`.

### O que o hook NÃO faz
`go vet` — não roda. Testes — não rodam. Linkedição de `cmd/` — não roda. `go build ./...` —
não roda (é justamente o que a DEC-002 removeu; o comentário do hook registra o motivo: 504
pacotes, ~5 min de CPU mesmo a quente por causa da religação dos `cmd/`). Checks processuais
antigos — removidos (DEC-001/DEC-002).

## 2. Variáveis de ambiente sancionadas (as únicas; `grep WIKI_` no hook e no checker)

| Variável | Default | Efeito |
|---|---|---|
| `WIKI_COMMIT_GATE_TIMEOUT_SECONDS` | `90` | orçamento lógico do checker; o `timeout` externo vira `budget+5`. Vale também para o hook `reference-transaction`. |
| `WIKI_GO_COMPILE_PARALLELISM` | vazio (Go usa a afinidade/cgroup) | vira `-p=N` no `go list`. Serve para não afogar a máquina com agentes rodando; **não** existe para "acelerar". |

**Não existe env de skip.** `--no-verify` é proibido pelo contrato e, além disso, não pula o
hook `reference-transaction`. Se o gate reprovar, a correção é a causa, nunca o bypass.

## 3. Segundo gate no caminho: `.githooks/reference-transaction`

Roda na transação de ref (não é pulável por `--no-verify`), com o mesmo
`WIKI_COMMIT_GATE_TIMEOUT_SECONDS`. Ele só engata os gates pesados de produto v2
(`tools/run-v2-index-product-gates`, `tools/check-v2-finalized-commit`) quando o delta
`BASE..candidate` toca `data/editorial/v2_pages`, `portfolio_v2`, `v2_superseded`,
`v2_semantic_superseded`, `v2_quarantine`, `v2_writing_semantic_contract.json` ou os arquivos
`data/ops/v2_*` listados. **Commit só-Go não toca nada disso → caminho rápido (`continue`).**
Corolário operacional: commitar o fix Go por pathspec é barato; varrer junto os dados staged
acordaria a bateria pesada de produto.

## 4. Custo medido (sandbox, 2 núcleos, `nice -n 19`)

| Operação | Tempo real |
|---|---|
| `go build ./internal/v2ingest/` (cache quente do path) | **2,5 s** |
| **Closure direta do gate** (`check-go-compile-closure --package portaljuridico/internal/v2ingest`), 1ª vez no path | **22,9 s** |
| Mesma closure, 2ª vez (cache quente) | **2,3 s** |
| Closure no snapshot candidato (path novo, cache frio para os 86 pacotes) | ~**50 s** em 2 fatias de ≤36 s |
| Closure do bundle B no snapshot (já morno) | **25,6 s** |
| `go test -c` (linka o binário de teste do pacote) | **24,3 s** frio / **5,2 s** morno |
| Gerador da atestação de fingerprint | **4,6 s** |
| `git archive HEAD go.mod go.sum internal cmd \| tar -x` (44 MB) | **4,3 s** |

Registro histórico no repo, com 8 núcleos: `check-go-index-compile-closure` validou o commit
`0204bb14` de **1.057 arquivos em 16,5 s** (`docs/goal/CHECKPOINT_DIGEST.md:28`); commit de
conteúdo puro sai em SKIP de 0,2–0,7 s. **Não há registro de `go build ./...` a frio** — o único
número documentado é "~5 min de CPU mesmo com cache quente" (comentário do hook e `CLAUDE.md`),
e ele não está no caminho do commit.

Sobre warm-up: **é viável e funciona em fatias** (cada fatia de 36 s que morre no `timeout`
deixa no `GOCACHE` tudo que já compilou — foi assim que a closure no path novo fechou em 2
fatias). Mas para este commit **é desnecessário**: a rota direta custa ~23 s a frio contra 90 s
de orçamento. Atenção: o `GOCACHE` do sandbox
(`/sessions/wonderful-inspiring-pascal/.cache/go-build`, 369 MB) **não é** o do host
(`/home/rafael/.cache/go-build`); aquecer aqui não aquece o commit lá.

## 5. Por que a rota é commit parcial por pathspec

`git status` no momento da investigação: **2 arquivos Go já staged** —
`internal/v2ingest/transaction_lock.go` e `internal/v2stockepoch/lease.go` — mais centenas de
arquivos de `data/editorial/**` (incluindo `v2_pages`, `portfolio_v2` e `v2_claims`). Os 2
arquivos Go do fix (`transaction_safe_io.go`, `terminal_artifact_vault.go`) estão **unstaged**.

`internal/v2ingest/stock_freshness_snapshot.go` também está sujo, mas **fica fora do bundle de
propósito**: é outro assunto (mensagem de repin do gate de stock freshness, mtime de 07-29) e
adiciona a constante **exportada** `StockFreshnessRepinCommand` — o classificador de superfície
do gate deixaria de usar a rota direta e passaria a compilar toda a closure reversa de
`internal/v2ingest` (commit mais caro, sem necessidade). As constantes de atestação desta nota
foram calculadas **sem** ele.

- `git commit -m …` (sem pathspec) commitaria a massa de dados + os 2 Go staged e **não**
  incluiria o fix. Errado, e acordaria os gates pesados de produto v2.
- `git add` dos arquivos do fix + `git commit` teria o mesmo problema (varre o índice inteiro).
- `git commit -m … -- <paths>` monta a árvore candidata como **HEAD + esses paths (conteúdo da
  worktree)**, ignora o resto do índice, **não altera a worktree** e é exatamente a forma
  autorizada pelo `CLAUDE.md` ("commit parcial com pathspec … que NÃO toca a worktree").
  É a rota. Nada de `add`/`reset`/`restore`/`stash`.

Prova de que o candidato compila: montei `HEAD + os 2 arquivos do fix` em snapshot e rodei o
comando exato do gate → `go-compile-closure: PASS`. Idem para o bundle de 4 arquivos.

## 6. Achado P0 — atestação do grafo do validador stale no HEAD

`internal/v2ingest/validator_fingerprint_attestation_generated.go` guarda
`compiledValidatorCodeGraphFingerprint`, hash de **todo o fecho de imports de
`internal/v2ingest` + `cmd/ingest-v2-stock` + `go.mod`/`go.sum`** (86 pacotes; o próprio arquivo
gerado é excluído do grafo — verificado por reexecução idempotente).

Medições (gerador rodado sobre árvores materializadas por `git archive`):

| Árvore | Fingerprint calculado | Constante commitada |
|---|---|---|
| commit `b0f2d0dd` (última regeneração) | `sha256:8cb0a13c…` | `sha256:8cb0a13c…` ✅ |
| **HEAD puro** (`5f1bb540` e `6b48b48c`, medido 2×) | **`sha256:9034ae1c…`** | `sha256:8cb0a13c…` ❌ **stale** |
| worktree vivo (16 arquivos sujos no grafo) | `sha256:129d206c…` | — |
| **HEAD `6b48b48c` + bundle A** (2 arquivos, bytes de 08:38) | **`sha256:3b00135afbb2d9481ad74b12927474c7ecca1e5475f72ed422e330e25bd891ad`** | — |
| **HEAD `6b48b48c` + bundle B** (4 arquivos, bytes de 08:38) | **`sha256:ffffe6b27ce1cfa111d544c6287afc07628431a292679d9c3e2149fc34decf5f`** | — |

Confirmação independente do valor do bundle B: rodando a suíte no snapshot candidato **sem**
gravar a atestação, o teste reporta exatamente
`source=sha256:ffffe6b27ce1cfa111d544c6287afc07628431a292679d9c3e2149fc34decf5f`; gravando a
constante, o mesmo conjunto fecha **12 PASS / 0 FAIL / 1 SKIP**.

> Constantes anteriores desta mesma investigação (`8624256b…` para A, `41989f00…` para B)
> ficaram **obsoletas** quando a frente concorrente reescreveu `transaction_safe_io.go` às
> 08:38. Estão registradas aqui só como precedente do risco: **a constante é função dos bytes
> exatos; se o sha256 do passo 1 não bater, recompute — não copie.**

Metodologia validada: o gerador rodado sobre a worktree viva reproduz exatamente o
`source=129d206c9d0b322edf522e247bb13298c09bf76af6a1ac4169d0a0d6bf77d8df` que o teste
`stock_freshness_terminal_v5_test.go:300` reporta.

**RCA:** entre `b0f2d0dd` e HEAD, só dois arquivos do grafo mudaram —
`internal/v2supersessionintegrity/git_index.go` e `internal/v2writingsemantic/git_index.go` —
ambos no commit **`d101c5e3`** ("fix(gate): host-root sob userns … + fallback renameat2 no
install do sidecar de proveniencia"), que **não regenerou a atestação**. Como o pre-commit só
compila e não há check dedicado (`grep` em `internal/checks/`, `tools/`: nada), a staleness
passou. Sintoma: ~10 testes de `internal/v2ingest` falham com
`generated validator attestation does not match authenticated source graph … run go generate ./internal/v2ingest`.

**Armadilha a evitar:** rodar `go generate ./internal/v2ingest` na worktree suja grava
`129d206c…`, que corresponde a uma árvore que **nunca será commitada** (12 arquivos de outras
frentes estão sujos no grafo). A atestação tem que ser calculada sobre a **árvore candidata**.
Receita na seção 8.

## 7. Rota recomendada — bundle B (fecha o fix e a dívida da atestação)

Conteúdo do bundle (4 Go + 1 gerado). Os dois staged são da **mesma família de portabilidade**
(uid de overflow 65534 sob user namespace) e já estão prontos no índice:

| Arquivo | Estado | Papel |
|---|---|---|
| `internal/v2ingest/transaction_safe_io.go` | unstaged | fallback nomeado quando não há `O_TMPFILE`; `renameTransactionNoReplaceAt` emula `RENAME_NOREPLACE` |
| `internal/v2ingest/terminal_artifact_vault.go` | unstaged | passa os 4 `Renameat2` diretos pelo helper com fallback |
| `internal/v2ingest/transaction_lock.go` | **staged** | aceita `/tmp` com uid 65534 sob userns sem root mapeado (mantém exigência de modo 01777) |
| `internal/v2stockepoch/lease.go` | **staged** | mesma correção de userns no lease |
| `internal/v2ingest/validator_fingerprint_attestation_generated.go` | precisa ser reescrito | constante do grafo candidato |

Evidência de que o bundle B é o que destrava o sandbox: com os 4 arquivos aplicados, os testes
que falhavam com `logical transaction lock namespace must be root-owned mode 01777`
**passam** (`TestPrepareTransactionPlanV5ReusesStoredTerminalIDAfterSameByteInodeReplacement`
7,59 s, `TestRejectedOnlyDiagnosticsV5RequiresAndReusesTerminalEvidence` 6,97 s,
`TestPrepareTransactionPlanSnapshotsModuleIdentityWithProjectReader` 1,77 s).

### Comandos exatos (host `/opt/wiki`)

```bash
cd /opt/wiki

# 1. Conferir HEAD e que os insumos não mudaram desde a medição (2026-07-31, bytes de 08:38 BRT).
git rev-parse --short HEAD    # medido em 6b48b48c
sha256sum internal/v2ingest/transaction_safe_io.go \
          internal/v2ingest/terminal_artifact_vault.go \
          internal/v2ingest/transaction_lock.go \
          internal/v2stockepoch/lease.go
# esperado:
# d75e0d1a0174746ab84a90eb02743c54dc90b8806f7b4f620b179f2e4a5f9a70  transaction_safe_io.go
# 71be48593ffefb548b9113ff6fda0ac56b803dbd3d4e6dfc1cec92015c431815  terminal_artifact_vault.go
# 489fd7d4c17612f8a9ff2f0ad847308a90c4a7234e68d4dff109a22f9731a627  transaction_lock.go
# 3da8c8a022f4432d548d132917224b28d92492195c27f339356fa41e42bb7519  lease.go
# Qualquer divergência (ou HEAD != 6b48b48c) => a constante do passo 3 muda; o próprio comando
# do passo 3 já a recalcula e imprime — basta NÃO usar o valor esperado como se fosse fixo.

# 2. gofmt (o gate reprova blob staged não formatado). Já verificado limpo aqui.
.toolchains/go1.26.5/bin/gofmt -l internal/v2ingest/transaction_safe_io.go \
    internal/v2ingest/terminal_artifact_vault.go internal/v2ingest/transaction_lock.go \
    internal/v2stockepoch/lease.go            # saída vazia = ok

# 3. Materializar a árvore candidata (descartável) e regenerar a atestação SOBRE ELA.
SNAP="$(mktemp -d /tmp/wiki-candidate-XXXXXX)"
git archive HEAD go.mod go.sum internal cmd | tar -x -C "$SNAP"
cp internal/v2ingest/transaction_safe_io.go internal/v2ingest/terminal_artifact_vault.go \
   internal/v2ingest/transaction_lock.go "$SNAP/internal/v2ingest/"
cp internal/v2stockepoch/lease.go "$SNAP/internal/v2stockepoch/"
./tools/go-modern run ./internal/v2ingest/cmd/generate-validator-fingerprint-attestation \
   -root "$SNAP" -output internal/v2ingest/validator_fingerprint_attestation_generated.go
# com HEAD 6b48b48c e os bytes acima imprime:
#   validator_fingerprint_attestation=sha256:ffffe6b27ce1cfa111d544c6287afc07628431a292679d9c3e2149fc34decf5f
# (forma validada no sandbox; -root manda no grafo, -output só no destino. O valor impresso é a
#  autoridade — se divergir do acima, é porque algum insumo mudou; siga com o valor impresso.)

# 4. Pré-voo do gate, opcional mas barato (~25 s), sobre a MESMA árvore candidata:
./tools/check-go-compile-closure --root "$SNAP" --package portaljuridico/internal/v2ingest
# esperado: go-compile-closure: PASS

# 5. Commit parcial por pathspec (não toca worktree nem o resto do índice).
git commit -m "fix(v2ingest): portabilidade O_TMPFILE/renameat2 e lock namespace sob userns + reancora atestacao do grafo do validador" -- \
  internal/v2ingest/transaction_safe_io.go \
  internal/v2ingest/terminal_artifact_vault.go \
  internal/v2ingest/transaction_lock.go \
  internal/v2stockepoch/lease.go \
  internal/v2ingest/validator_fingerprint_attestation_generated.go

# 6. Descartar o snapshot (é meio, não produto).
rm -rf "$SNAP"
```

Se a máquina estiver com muitos agentes e for preciso limitar CPU do gate:
`WIKI_GO_COMPILE_PARALLELISM=4 git commit …`. Se (e só se) o gate estourar orçamento:
`WIKI_COMMIT_GATE_TIMEOUT_SECONDS=240 git commit …`. Nunca `--no-verify`.

## 8. Rota mínima — bundle A (só os 2 arquivos do escopo original)

Mesma sequência, trocando o passo 3/5 pelos 2 arquivos. A atestação do candidato A sobre
HEAD `6b48b48c` é **`sha256:3b00135afbb2d9481ad74b12927474c7ecca1e5475f72ed422e330e25bd891ad`**
(medida). Compila: `go-compile-closure: PASS`.

Custo de escolher A: os arquivos de userns continuam pendurados no índice e o sandbox segue
reprovando `logical transaction lock namespace must be root-owned mode 01777`; e quem commitar
`transaction_lock.go`/`lease.go` depois terá de regenerar a atestação de novo.

**Receita geral de recomputo** (use sempre que os insumos ou o HEAD mudarem): passos 3 do
bloco acima, ajustando quais arquivos são copiados sobre o `git archive HEAD`. A regra é uma
só: **a atestação vale para a árvore que vai ser commitada, nunca para a worktree suja**.

## 9. Evidência de teste (fatias de ≤38 s, sandbox)

- `go build ./internal/v2ingest/` → **verde**, 2,5 s.
- Comando exato do gate (`go list -deps -test -export`, produção + devcmds + variantes de
  teste) → **PASS**, 22,9 s a frio, 2,3 s a quente; **PASS** sobre o snapshot candidato A, sobre
  o candidato B e **de novo sobre o bundle B com os bytes de 08:38** (2 fatias: 32 s + 16,7 s no
  path novo, cache frio).
- **Conjunto-alvo com os bytes atuais + atestação candidata: 12 PASS / 0 FAIL / 1 SKIP**
  (`Rename|NoReplace` + `TestPrepareTransactionPlanV5ReusesStoredTerminalIDAfterSameByteInode
  Replacement` 6,15 s + `TestPrepareTransactionPlanSnapshotsModuleIdentityWithProjectReader`
  1,53 s). Sem a atestação candidata, esses dois últimos falham só por drift de fingerprint.
- `gofmt -l` nos 5 arquivos → limpo.
- `go test -c` do pacote → **linka** (24,3 s).
- `go test -count=1 -run 'Rename|NoReplace'` → **ok, 1,148 s** (não existe `TestRename` exato no
  pacote; o padrão cobre 11 testes de rename/NOREPLACE, entre eles
  `TestReplaceBytesDurableUsesNoReplaceForAbsentCAS` e
  `TestTerminalArtifactVaultResumesForwardAfterRetainedRename`).
- Suíte do pacote sobre o candidato B, fatiada: `Vault|Terminal|ValidateInstalledCanonicalStockSnapshot`
  → **3 PASS / 0 FAIL** depois de copiar `data/editorial` para o snapshot.
- Suíte completa **não roda íntegra no sandbox** e não deve ser usada como veredito aqui: das 74
  falhas da primeira fatia, **100 % têm causa ambiental** — (a) `no such file or directory` em
  `data/editorial/v2_pages/*.jsonl` porque o snapshot só tinha `internal cmd go.mod go.sum`; (b)
  `logical transaction lock namespace must be root-owned mode 01777`, que é **exatamente o bug
  que `transaction_lock.go` staged corrige** (com ele aplicado, os mesmos testes passam). Zero
  falhas atribuíveis ao fix de `transaction_safe_io.go`/`terminal_artifact_vault.go`.
  O veredito íntegro da suíte tem que sair no host (`./tools/go-modern test -count=1
  ./internal/v2ingest/`), onde `/tmp` é root:root 1777 e `data/` está inteiro.
- Fatos de ambiente medidos: `O_TMPFILE` **ENOTSUP** no mount do repo
  (`/sessions/…/mnt/wiki`), **OK** em `/tmp` e no home do sandbox — confirma a premissa do fix.
  `/tmp` do sandbox é `uid=65534 mode=1777` — confirma a premissa do fix de userns.

## 10. Riscos e o que não fazer

- **Não** rodar `go generate ./internal/v2ingest` na worktree suja (grava `129d206c…`, árvore
  que não existe em commit nenhum).
- **Não** usar `git add`/`git commit` sem pathspec: varre a massa de dados staged de outra
  frente e acorda `run-v2-index-product-gates` no `reference-transaction`.
- **Não** usar `git reset/checkout/restore/stash` — proibido pelo contrato e há trabalho vivo de
  outras frentes na worktree.
- Depois deste commit a worktree continua com 12 arquivos sujos dentro do grafo do validador, ou
  seja, **os testes de atestação seguem vermelhos na worktree** até que essas frentes commitem e
  regenerem. Isso é esperado: a atestação só pode estar verde numa árvore consistente.
- **`internal/v2ingest/transaction_safe_io.go` é arquivo QUENTE** (foi reescrito às 08:38 no meio
  desta investigação). Rode a conferência de sha256 imediatamente antes do commit e leia o
  arquivo antes de congelá-lo — o contrato proíbe commitar versão em meio-evolução de outra
  frente. Se o sha mudar, só o passo 3 precisa ser refeito (≈5 s).
- **Dívida de engenharia identificada:** não existe check que prove
  `compiledValidatorCodeGraphFingerprint == fingerprint(HEAD)`. Enquanto isso, qualquer commit
  que toque um dos 86 pacotes do grafo pode reintroduzir a staleness silenciosamente (foi o que
  `d101c5e3` fez). Um `check-validator-fingerprint-attestation` no `cmd/check` (ou no perfil
  proporcional de release) fecha o buraco por ~5 s de execução.

## 11. Execução da rota (2026-07-31, 10:12 BRT) — o que a medição acima NÃO previu

Rota executada sobre HEAD `eb949c25`. **Commit entregue: `d3edc3e4`** (3 arquivos, gate
`PASS … closure_mode=direct surface_reason=body_or_proven_private_delta_only elapsed_ms=12980`).
Correções de fato às seções 5–8 — todas medidas, não estimadas:

1. **O bundle B NÃO é rota direta.** As seções 4–8 mediram só o compile interno
   (`check-go-compile-closure`), nunca o classificador de superfície do gate
   (`api-surface-helper`, dentro de `check-go-index-compile-closure`). Rodando o classificador
   real, arquivo a arquivo, sobre os bytes de 08:38:
   - `validator_fingerprint_attestation_generated.go` → `generated_file_changed` (o helper usa
     `ast.IsGenerated`; **qualquer** arquivo com o marcador "Code generated … DO NOT EDIT" força
     reversa). Logo **bundle A e bundle B são REVERSOS**, não diretos;
   - `internal/v2ingest/transaction_lock.go` → `imports_changed` (adiciona `"strings"`);
   - `internal/v2stockepoch/lease.go` → `private_delta_reaches_exported_surface`;
   - `transaction_safe_io.go`, `terminal_artifact_vault.go`, `v2semanticrecut/forward.go` →
     `body_or_proven_private_delta_only` (**direto**, os três juntos).
2. **A closure reversa é inviável neste sandbox: 570 de 1.594 pacotes** (inclui `cmd/check` e
   centenas de `cmd/*`), contra 2 pacotes da direta. Só a descoberta
   (`go list -tags=devcmds -test -json ./...`, 21 MB de JSON) custa 30 s a frio / 6,8 s morna
   contra um teto **fixo de 20 s** (`_remaining_timeout(20)`, que **não** escala com
   `WIKI_COMMIT_GATE_TIMEOUT_SECONDS`).
3. **Custo real do gate aqui:** ~20 s fixos antes de qualquer compilação (materialização +
   autenticação blob a blob, Python single-thread; o `git` em si leva ~3 s), depois classificação
   (~2 s morna) e compile. Direta morna: **12,98 s de gate / 15,2 s de commit inteiro**; direta
   fria no path novo: 38 s.
4. **O gerador da atestação não escreve dentro do mount do repo.** O mount é
   `fuse … default_permissions` que devolve **modo 0600 para tudo e ignora `chmod`**, e o gerador
   exige stage `S_IFREG|0644` → `unsafe attestation stage`. Sintoma histórico: 8 órfãos
   `.validator_fingerprint_attestation_generated.go.stale-cas-*` (7 deles de 15–17/07). Rota que
   funciona: `-output /tmp/<dir>/validator_fingerprint_attestation_generated.go` (o `-root` é
   quem manda no grafo; o basename precisa ser o canônico) e copiar o arquivo para o repo.
   `unlink` também é **EPERM** no mount — por isso todo `git` local vaza `index.lock` /
   `next-index-*.lock` / `HEAD.lock`: rodar `tools/clear-orphan-git-lock --allow-nonempty 2`
   **antes e depois** de cada git, inclusive dos read-only (`git diff` também toma `index.lock`).
5. **Atestação: valor confirmado e ainda válido.** Sobre HEAD `eb949c25` + os 4 arquivos do
   bundle B o gerador imprimiu exatamente
   `sha256:ffffe6b27ce1cfa111d544c6287afc07628431a292679d9c3e2149fc34decf5f` — idêntico ao medido
   sobre `6b48b48c`, o que prova (a) que os commits entre os dois HEADs não tocaram o grafo e
   (b) que `v2semanticrecut/forward.go` **não pertence** ao grafo do validador. Como `d3edc3e4`
   só levou arquivos fora do grafo, **`ffffe6b2…` continua sendo o valor correto para
   `HEAD + transaction_lock.go + lease.go`** e já está gravado na worktree — não recalcule.
6. **Falta commitar (rota reversa; barata no host de 8 núcleos, inviável aqui):**
   `internal/v2ingest/transaction_lock.go` e `internal/v2stockepoch/lease.go` (ambos **staged**)
   + `internal/v2ingest/validator_fingerprint_attestation_generated.go` (worktree, já com
   `ffffe6b2…`). Aviso ao próximo commit de dados: **os 2 Go staged acordam a closure reversa**
   para quem varrer o índice inteiro.
7. **Restrições do harness Cowork medidas:** processo em background **não sobrevive** ao fim da
   chamada bash (`setsid` + `nohup` + `disown` são reapados) — o commit inteiro tem de caber em
   uma chamada (~44 s); e `/sessions` chegou a **100 % cheio** (ENOSPC gravando no `GOCACHE`, que
   mora lá), resolvido liberando ~800 MB do próprio cache.
