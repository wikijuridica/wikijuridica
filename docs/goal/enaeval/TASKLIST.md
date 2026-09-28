# TASKLIST OBRIGATÓRIA — EnaEval

**Documento de execução do próximo Claude Code (engenheiro sênior do dono), em goal mode.**
Autoridade: `CORRECOES-DONO.md` §7 > `DECISOES-ORQUESTRADOR.md` (D-1…D-17 + ADENDO) > `CANON-v4.1.md`
> `LEDGER-CORRECOES.md` > relatórios F/G/H. A espinha é **D-17 / H01 §7** (12 objetivos), expandida em
**12 fases** e **49 objetivos**.

**Zero cronograma.** Só **FASE** (F0…F11) e **OBJETIVO** (F1.O3). Onde há duração física, a unidade é
**GPU-dia de máquina** ou **CPU-dia de máquina** — medida do sistema, nunca prazo. Muita coisa se
resolve na mesma sessão; a ordem é **dependência técnica + valor**, não calendário.

---

## 0 · COMO O PRÓXIMO CLAUDE CODE OPERA

### 0.1 Início de sessão (obrigatório, uma vez)

1. Ler `CANON-v4.1.md` (fonte única de números) e `DECISOES-ORQUESTRADOR.md` (17 decisões + ADENDO que
   derruba D-5 e D-10). Relatório F/G que conflite com o CANON **está superado** — não se discute.
2. Ler o objetivo da sessão nesta árvore, e só os arquivos que ele cita.
3. Rodar o portão da fase (`§2`) antes de escrever qualquer linha. Portão vermelho vira o objetivo.

### 0.2 Proibições absolutas (herdadas do dono, não negociáveis)

- **Nunca reabrir número do dono** (baseline ≥ 3.300 citações/dia, 6.086 crawls/dia, meta 100.000/dia,
  hardware exato). Não se "valida", não se relativiza, não se pede teste de confirmação.
- **Nunca propor compra, nuvem, GPU alugada, transbordo ou plataforma paga.** Se um cálculo não fecha,
  a resposta é **engenharia de alocação**: tiering, quantização, poda, pré-computação, cache, lote,
  mmap/NVMe, tempo contínuo 24/7.
- **Nunca escrever "impossível com este hardware", "platô", "saturação" ou "limite de mercado".**
- **Nunca mandar o dono executar tarefa.** O sistema roda; ele decide só o que está em `§0.5`.
- **Fail-closed sempre.** Verificador sem calibração **erra**, nunca adota τ de reserva; regra de
  normalização desconhecida vira `VALID_SPAN_UNVERIFIED`; stub devolve `stub:true`, nunca número.
- **Teste antes de marcar pronto.** Contagem de teste é **saída de execução**, nunca resumo.

### 0.3 Protocolo de objetivo (goal mode)

Um objetivo fecha quando: (a) o comando do critério binário devolve a saída esperada; (b) `go vet` e
`go test -count=1 ./...` com `GOTOOLCHAIN=local` ficam verdes; (c) o `depcheck` não acusa violação
nova; (d) o registro entra no `LEDGER-CORRECOES.md` com comando e saída colados. Objetivo
parcialmente pronto **não fecha**: divide-se em dois, e o segundo entra na fila.

### 0.4 O que significa "pronto"

| Forma | Exemplo aceito | Recusado |
|---|---|---|
| Comando + saída | `enaeval-probe` → `53 canônicas · sem title 0` | "o probe passa" |
| Métrica + limiar | `HCR UCB95 ≤ 2%` no artefato quantizado | "qualidade boa" |
| Ataque recusado | `psql -f ATAQUES-v4.1.sql` → `0 FALHAS` | "o schema protege" |
| Ausência provada | `grep -rn "906" wj/` → 0 | "não hardcodamos" |

### 0.5 O que é decisão do dono (lista fechada, quantificada — tudo o mais é engenharia)

1. **Guarda das 5 shares do K_root** (Shamir 3-de-5): o sistema gera, sela e testa a reconstrução; o
   dono só recebe as shares e diz onde guardou. **5 itens.**
2. **Rotulagem de calibração**: 1.000 claims de ouro em lotes de 250 (o 1º lote já libera τ provisório
   conservador) + 2.000 confirmatórios. **3.000 rótulos, 4 lotes.**
3. **Adjudicação D3** do tri-temporal: só o que P1/P2/P3 não resolvem, ≤ 2% das 200 leis-âncora.
   **≤ 4 decisões por lote de 200.**
4. **Redação das 37 políticas Cedar** (17 `WJ::Compliance` + 20 `WJ::Autoral`): limiar estatístico vem
   do contexto, **limiar legal é literal** e é dele. **37 textos.**
5. **Sign-off de amostra** antes de liberar lote de páginas geradas: **10 páginas por lote.**
6. **Gabarito das trilhas do bench**: 7 programáticas + 2 novas. **9 gabaritos.**
7. **Política de `robots.txt` na classe de treino** (`Content-Signal: ai-train`): 1 decisão binária.

Nada além destes sete sobe para o dono. Se um objetivo parece exigir decisão dele e não está aqui, a
decisão é do engenheiro, com base em dados, matemática e probabilidade.

---

## 1 · MAPA — artefato que JÁ EXISTE → módulo `wj/`

Fonte: `INVENTARIO-CODIGO.md` §5 + `E07-arquitetura/deps.yml` + `enaeval/deps/enaeval.deps.yml`.
`depcheck.go` rodado contra o repositório real devolve **"0 pacote(s) verificado(s), 25 ainda não
existe(m) no disco"** — o monorepo é obra de F0.O7.

| Pacote `wj/` | Camada | Artefato real (caminho) | Status |
|---|---|---|---|
| `wj/lex` | 0 | `C03-code/validador/validador.go`, `F05-code/*/ancoras_gerado.go`, `D04-code` (trie de URN) | **ESCREVER** |
| `wj/tipos` | 0 | `research/D10-code/tipos/{capacidade,texto,valor}.go` | **INTEGRAR** (testado com `rapid`) |
| `wj/calc` | 1 | `research/C03-code` (4 motores) + `research-v4/F05-code` (10 motores, 14.944 l) | **INTEGRAR** |
| `wj/temporal` | 1 | `F05-code/literate`, `F05-code/registro` | **ADAPTAR** |
| `wj/grafo` | 1 | `F03-code/sql/{f03_schema,f03_age}.sql` (carregado em PG com dados reais), `F02-code/sql/age_doutrina.sql` | **INTEGRAR** |
| `wj/verify` | 2 | `research-v4/verify-code/verify.go` (τ fonte única, stdlib), `C03-code/mcp/guarda.go` (ancoragem) | **INTEGRAR** + V1–V7 a escrever |
| `wj/verify/wba` | 2 | `G04-code/enaeval/wba/wba.go`, `F06-code` (`wbaverify`) | **INTEGRAR** |
| `wj/receipt` | 2 | `research/B06-code/lar.go` **v1.1** (643 l, SHA `feef864a…`) + `F06-code/lar/` byte-idêntico | **PRONTO** |
| `wj/policy` | 2 | `F02-code/cedar/autoral.cedar` (20 políticas), `G03-code/policy/fontes.cedar` | **INTEGRAR** (falta `WJ::Compliance`) |
| `wj/retrieve` | 3 | — | **ESCREVER** |
| `wj/serve` | 3 | `E02-code/escalonador.go` **não compila** (4 símbolos indefinidos) + `EscalonadorGPU.tla` (1.936 estados, 0 erros) | **ESCREVER** |
| `wj/jurimetria` | 3 | `G01-code/go/prog/prog.go` (803 l, `StubScorer`) | **ADAPTAR** (trocar stub por `leaves`) |
| `wj/sim`, `sim/core`, `sim/llm` | 3 | `research/D06-code/entropia_movimentos.py` (medição) | **ESCREVER** |
| `wj/agent` | 4 | — | **ESCREVER** |
| `wj/agent/dialog` | 4 | `G04-code/enaeval/dialog/dialog.go` | **ADAPTAR** |
| `wj/nego`, `nego/core`, `nego/llm` | 4 | — | **ESCREVER** |
| `wj/econ` | 4 | `F04-code/go/precos.go` (testado), `orcamento/orcamento_v4.py` | **INTEGRAR** |
| `wj/econ/quota` | 4 | `G04-code/enaeval/ratelimit/ratelimit.go` | **ADAPTAR** (memória → `quota_did` em PG) |
| `wj/econ/x402` | 4 | `G04-code/enaeval/pay/x402.go` | **ADAPTAR** |
| `wj/econ/tesouraria` | 4 | `research/B02-modelo-financeiro.py` (projeção) | **ESCREVER** |
| `wj/api` | 5 | `G04-code/enaeval/identity/` (4 documentos) | **ADAPTAR** |
| `wj/mcp`, `wj/mcp/catalog`, `wj/mcp/adapters` | 5 | `G04-code/enaeval/{server,catalog,tools,adapters}`, `tools/catalog.json` (14 impl · 39 stub · 13 reserved) | **INTEGRAR** |
| `wj/edge` | 5 | `F11-code/recipes/*` | **ESCREVER** |
| `wj/mlops` | 5 | `F11-code/comp/` (9/9 ataques), `F06-code` (`tbv`, `wjconsist`), `D10-code/invariantes.sql`, `F08-code` (WARC/in-toto) | **INTEGRAR** |
| `wj/console` | 5 | `research/D08-console/index.html` (mockup, 1.040 l, sem backend) | **ADAPTAR** |

**Enums e τ já existem, não reescrever:** `research-v4/enums/{enums.yaml,gen.py}` (20 enums, 163
valores, `--check` = 35 alvos, 0 divergência) e `research-v4/verify-code/verify.go`.

---

## 2 · INVARIANTES QUE O CI VERIFICA (portão de merge, não convenção)

**Dependência (`cmd/wj-depcheck` sobre `deps.yml` + patch do G04, `go list -deps`, cobre transitivas):**

| # | Regra | Motivo |
|---|---|---|
| DEP-1 | `wj/nego/core` ⊬ `wj/nego/llm` | antitruste: correlação residual de preço +0,053 sem acordo |
| DEP-2 | `wj/sim/core` ⊬ `wj/sim/llm` | recibo de simulação reproduzível com 3,5 kB de kernel |
| DEP-3 | `wj/agent/dialog` ⊬ `wj/serve` | a pergunta fixa o insumo do cálculo; LLM ali = injeção |
| DEP-4 | `wj/mcp` ⊬ `wj/serve`, ⊬ `wj/econ/tesouraria` | 44/45 tools com `gpu=false`; chave de gasto fora da superfície |
| DEP-5 | `wj/calc`, `wj/grafo`, `wj/policy`, `wj/jurimetria`, `wj/econ` ⊬ `wj/serve` | cálculo, indexação, política e preço nunca dependem de LLM |
| DEP-6 | `wj/receipt` ⊬ `wj/verify` | terceiro verifica o recibo sem rodar nosso NLI |
| DEP-7 | `wj/verify/wba` ⊬ `wj/agent`, ⊬ `wj/serve` | quem autentica não conhece quem decide |
| DEP-8 | `wj/edge` ⊬ `wj/econ/tesouraria`, ⊬ `wj/nego`, ⊬ `database/sql` | Plano-T e o número nunca migram para runtime de terceiro |
| DEP-9 | `wj/econ/tesouraria` ⊬ `net/http`, `wj/agent`, `wj/retrieve`, `wj/serve` | Plano-T sem LLM e sem egresso |
| DEP-10 | literal `chat_template` em qualquer fonte = falha | template Jinja2 é código: 90% → 15% |

**MCP:** MCP-1 catálogo válido ou o servidor não sobe · MCP-2 nenhum `ServerSession.Elicit`/
`CreateMessage`/`ListRoots` · MCP-3 `tier=free` nunca devolve 402 · MCP-4 preço descobrível sem pagar ·
MCP-5 `requestState` assinado e ligado a (ferramenta, agente, prazo) · MCP-6 stub se identifica ·
MCP-7 nenhum alias órfão.

**Catálogo:** I1 sem `$ref` de rede · I2 `title` obrigatório · I3 nome e alias únicos · I4
`decisive_field` no `outputSchema` · I5 `implemented` tem `impl_ref` real, `stub` traz `"stub":true`,
`reserved` não tem schema/exemplo/preço e **não entra em `tools/list`**.

**Literal de fonte única (varredura de fonte, não import):** `0.00090` só em `wj/econ` ·
`0.000060031` só em `wj/econ/tesouraria` · `0.906`/`906` só em `wj/verify` (fora de
`wj/verify/testdata`, grep = 0) · `2.50` e `180` só em `wj/econ/tesouraria`.

**Pins (o CI recusa `latest` e versão diferente):** `go-sdk v1.8.0` · `x402/go/v2 v2.26.0` ·
`cedar-go v1.8.0` · `hugot v0.7.8` · `eino v0.9.19` · `river v0.47.0` · `a2a-go/v2 v2.5.0`; `go 1.25`
+ `toolchain go1.25.x`; CI com **`GOTOOLCHAIN=local`**. **Formais:** `EscalonadorGPU.tla` e
`PromocaoModelo.tla` no CI (TLC, 0 erros).

---

## 3 · A ÁRVORE — FASE → OBJETIVO → TAREFA

**Campos de cada objetivo** — resultado observável e critério binário vêm juntos em **Pronto**, porque
resultado não medível por comando não é resultado: **Pronto** = estado observável **e** comando com
saída esperada (ou métrica com limiar) · **Insumos** = artefatos que já existem, caminho real ·
**Entregáveis** = caminhos em `wj/` conforme `deps.yml` · **Depende** = objetivos anteriores ·
**Recurso** = edge/CPU/GPU e perfil · **Dono** = o que sobe para ele (§0.5) · **Goal** = o parágrafo
autocontido que o Claude Code recebe.

Marcação de tarefa: **[I]** integrar código existente e verde · **[A]** adaptar · **[E]** escrever.


---

### FASE F0 — FUNDAÇÕES (nada real existe antes disto)

Sem K_root não há recibo real, cota por DID, 402 que liquide nem crawler assinado (D-7). Sem enums e
τ únicos, banco e binário discordam em silêncio. Sem SCHEMA-v4.1 carregado, a regra de dinheiro é
convenção. **Recurso da fase inteira: CPU + edge. 0 GPU.**

#### F0.O1 — K_root: Shamir 3-de-5, `did:web`, diretório Web Bot Auth

**Resultado:** a casa assina como assina o ChatGPT; nenhuma assinatura de exemplo parece real.
**Pronto:** `wbaverify https://wikijuridica.com.br` → `OK`; `lar -verify <recibo_real>` →
`VALID`; `grep -rn "PROTOTIPO\|<ed25519>\|PENDENTE_K_ROOT\|wj-2026-09\"" wj/` → **0**; reconstrução a
partir de 3 de 5 shares em host isolado → chave de sha256 idêntico.
**Insumos:** `research/B06-code/lar.go` (thumbprint RFC 8037 em `lar.go:437`) ·
`research-v4/F06-code/` (`wbaverify`, log contra o ChatGPT) ·
`research-v4/G04-code/enaeval/{wba/wba.go,identity/{did.json,agent-card.json,ai-source-card.json}}` ·
`CANON-v4.1` §0 (emissor = PJ `did:web:wikijuridica.com.br`, fixado por CHECK) e §8 C14/C15.
**Entregáveis:** `wj/verify/wba/`, `wj/api/wellknown/{did.go,directory.go,keys.go}`,
`wj/receipt/kid.go`, `ops/kroot/`. **Depende:** — . **Recurso:** CPU/edge, 0 GPU.
**Dono:** item 1 de §0.5 (guarda das 5 shares).
- [ ] **[E]** Gerar K_root Ed25519 em host isolado e dividir em Shamir 3-de-5.
      `go test ./ops/kroot -run TestReconstroi3de5` → `PASS` (combinações de 3 reconstroem; 2 falham).
- [ ] **[E]** Derivar K_op e a chave do log por **HKDF**; rotação é fase própria, com `kid` novo.
- [ ] **[A]** `did.json`, JWKS e `/.well-known/http-message-signatures-directory` assinado, molde byte
      a byte do diretório do ChatGPT. `curl -sI` → `200` (hoje: **404**).
- [ ] **[A]** `kid` = thumbprint RFC 8037 em todo emissor. `grep -rn 'Kid: "wj-' wj/` → 0.
- [ ] **[I]** Manter `TestNaoExportaSemChaveReal`: nada sai com assinatura `EXEMPLO-`.
**Goal:** *"Objetivo F0.O1. Leia D-7 em `DECISOES-ORQUESTRADOR.md`, `CANON-v4.1.md` §0 e §8 (C14, C15, C19,
C20), `H01-critico-fable.md` §3 (G17) e o código de `research/B06-code/lar.go` e
`research-v4/G04-code/enaeval/{wba,identity}`. Pronto quando `wbaverify` validar a própria casa,
`lar.Verify` aceitar um recibo real dela e o grep de placeholders em `wj/` der zero. Não mande o
dono executar nada: só pergunte onde ele guardou cada uma das 5 shares."*

#### F0.O2 — Fonte única de enums (`enums.yaml` → SQL + JSON Schema + Go + CDDL)

**Resultado:** um arquivo define os 20 enums; divergência entre banco, schema JSON, Go e CBOR quebra o
CI. **Pronto:** `python3 wj/lex/enums/gen.py --check` → `35 alvo(s) conferem, 0 divergência(s)`,
exit 0; `build_examples.py` → `11 exemplos, schema_errors=0`; `test_schema_negativos.py` →
`27/27 ataques recusados · 58/58 vetores positivos aceitos`.
**Insumos:** `research-v4/enums/{enums.yaml,gen.py,out/*}` (**pronto na FIX-A**: 20 enums, 163 valores,
parser YAML stdlib próprio) · `F01-code/knowledge-claim.schema.json` · `SCHEMA-v4.1.sql`.
**Entregáveis:** `wj/lex/enums/`. **Depende:** — . **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[I]** Mover `research-v4/enums/` para `wj/lex/enums/` preservando `--check` e `--apply-json`.
- [ ] **[I]** Apontar o `--check` para `SCHEMA-v4.1.sql`, não para o v4 histórico.
- [ ] **[E]** Portão: enum editado à mão em qualquer um dos 4 alvos falha o CI. `task ci:enums` → exit 0.
**Goal:** *"Objetivo F0.O2. Leia `research-v4/FIX-A.md` §1 e o código de `research-v4/enums/`. Não reescreva
o gerador: mova-o para `wj/lex/enums/`, aponte o `--check` para `SCHEMA-v4.1.sql` e transforme-o
em portão de CI. Pronto quando `gen.py --check` devolver 35 alvos conferindo com zero
divergência dentro do monorepo."*

#### F0.O3 — τ com fonte única (`verify_config`), nunca constante

**Resultado:** recalibrar é `UPDATE` numa tabela, não release coordenado.
**Pronto:** `grep -rn "906" wj/ --include=*.go --include=*.sql --include=*.json` fora de
`wj/verify/testdata` → **0**; `psql -f wj/verify/testdata/tau_ataques.sql` → τ paralelo no mesmo
escopo recusado, τ < 850 recusado, calibração ausente ⇒ `entail 999` **não** resolve;
`go test ./wj/verify -run TestSemFonteFechaNaoAdotaPadrao` → `PASS`.
**Insumos:** `research-v4/verify-code/` (**pronto na FIX-A**: `Fonte` injetada, escopo hierárquico,
vigência, sem SQL dentro do pacote) · `G01-code/sql/g01_tau_ataques.sql` · `SCHEMA-v4.1.sql`
(`verify_config`, `verify_cfg_vigente()`, EXCLUDE escopo × vigência) · `CANON-v4.1` §4.
**Entregáveis:** `wj/verify/{verify.go,calib.go}` + driver `wj/verify/pgsource`.
**Depende:** F0.O2, F0.O5. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[I]** Mover `verify-code` para `wj/verify`; **sem fonte registrada ⇒ erro**, nunca τ de reserva.
- [ ] **[A]** Trigger `g01_tau_do_v4()` grava `tau_milli`/`calib_id` na linha; `CHECK (tau_milli IS NOT
      NULL)` — sem isso `NULL >= NULL` é NULL e o CHECK **passaria**.
- [ ] **[E]** Recalibração por **martingale de Ville** (S_t ≥ 20 recalibra, S_t ≥ 100 retreina),
      **nunca por cron**. `go test ./wj/verify -run TestVilleDispara` → `PASS`.
**Goal:** *"Objetivo F0.O3. Leia `CANON-v4.1.md` §4 (Verificador — ÚNICO), D-13 item 5,
`H01-critico-fable.md` §2 (G7) e `research-v4/verify-code/`. Pronto quando o grep de `906` fora
do testdata der zero e os ataques recusarem τ paralelo, τ abaixo de 850 e resolução sem
calibração."*

#### F0.O4 — Recibo LAR v1.1 no ar (`man_norm`, estrutural, `at`, `cache_state_digest`)

**Resultado:** o verificador que o mundo baixa recusa citação a **redação tachada** — o defeito medido
no F06 §6.3 (gêmeo tachado, bytes idênticos, `lar.Verify` aceitava) deixa de existir.
**Pronto:** `sha256sum -c wj/receipt/SHA256SUMS` → `OK`; `go test -count=1 ./wj/receipt/` →
**10/10 PASS** (`TestV11_GemeoTachadoRejeita`, `TestV11_ManNormDesconhecidaNaoValida`,
`TestV11_SemCacheStateRejeita`); ataques N19/N20 do `ATAQUES-v4.1.sql` recusam `wj-norm/f5-cspm@1` e
nome de regra não registrado. **Insumos:** `research/B06-code/lar.go` **v1.1** e
`research-v4/F06-code/lar/lar.go` (byte-idênticos, 643 l, SHA `feef864a…`, `Outcome`,
`NormF5CSPMTailV1`, `PlanaltoInForce`, `lar.CacheNone`) · `F06-code/lar/lar_v11_test.go` ·
`G03-code/canon/canon.go` · `SCHEMA-v4.1.sql` (`norm_rule` + `norm_rule_registry`).
**Entregáveis:** `wj/receipt/` (espelho `lib/lar-go`), `wj/api/wellknown/norms.go`.
**Depende:** F0.O1, F0.O5. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[I]** Mover `lar.go` v1.1 para `wj/receipt` **stdlib-only** (DEP-6: não importa `wj/verify`).
- [ ] **[E]** Publicar `/.well-known/lar/norms/f5-cspm-tail-v1` (regex + vetores, C26) e
      `/.well-known/lar/checkpoint` + tiles com **MMD 60 s** e nota C2SP assinada (C19).
- [ ] **[A]** Atualizar C20 com o SHA v1.1 — o SHA `5f57fe20…` descrevia binário que **não** fazia o
      que o contrato prometia.
- [ ] **[I]** `tbv` deixa de duplicar regra e checagem: chama `lar.NormF5CSPMTailV1`/`lar.PlanaltoInForce`.
**Goal:** *"Objetivo F0.O4. Leia `research-v4/FIX-A.md` §2, `H01-critico-fable.md` §3 (G9, G10) e
`CANON-v4.1.md` §8 (C19, C20, C21, C26). Pronto quando o `sha256sum -c` der OK, os 10 vetores
v1.1 passarem e os ataques N19/N20 recusarem `wj-norm/f5-cspm@1`."*

#### F0.O5 — `SCHEMA-v4.1` vivo em PostgreSQL 18 + AGE 1.8 + pgvector/pgvectorscale

**Resultado:** dinheiro, selo e cota viram regra de banco; texto da internet fica incapaz de virar
payout. **Pronto:** `bash ops/db/run_schema_v41.sh` em banco novo → exit 0,
**131 tabelas, 11 views, 139 FKs, 25 triggers, 402 CHECKs**, grafo AGE `wjg`;
`ATAQUES-v4.1.sql` → `94 recusados · 13 aceitos · 0 FALHAS`; `fixes/g01_ataques_v41.sql` →
`33 recusados` com 17 consultas de integridade em zero. **Total: 127 recusas · 27 aceites · 0 falhas.**
**Insumos:** `research-v4/SCHEMA-v4.1.sql` · `ATAQUES-v4.1.sql` (+ resultado) ·
`fixes/{g01_schema_v41,g02_schema_v41,g01_ataques_v41}.sql` · `fixes/run_schema_v41.sh` ·
`research/E07-arquitetura/schema.sql` · `F03-code/sql/f03_schema.sql` (**já carregado com dados reais**).
**Entregáveis:** `wj/mlops/schema/`, `ops/db/`. **Depende:** F0.O2. **Recurso:** CPU + NVMe, 0 GPU.
**Dono:** nenhuma.
- [ ] **[A]** Promover de PG 16.13/AGE 1.5.0 para **PG 18 + AGE 1.8.0**; `create_graph('wjg')`
      (`'wj'` falha: `MIN_GRAPH_NAME_LEN = 3`).
- [ ] **[E]** Instalar **pgvector + pgvectorscale** (StreamingDiskANN + SBQ + filtro por rótulo) e
      **pg_textsearch** (BM25 Block-Max WAND). **VectorChord é REVOGADO** (AGPLv3-ou-ELv2).
- [ ] **[I]** Aplicar `g01_schema_v41.sql` e `g02_schema_v41.sql` por cima — o `g01_schema.sql`
      original **não carrega** (`prediction` virou VIEW: `cannot create index on relation`).
- [ ] **[E]** Portão: coluna nova sem ataque correspondente falha o CI.
**Goal:** *"Objetivo F0.O5. Leia `research-v4/FIX-B.md` §§1–3, `CANON-v4.1.md` §5 (Dados) e os arquivos
`SCHEMA-v4.1.sql`, `ATAQUES-v4.1.sql` e `fixes/*`. Não reescreva o schema: promova-o para PG 18
com AGE 1.8, pgvector, pgvectorscale e pg_textsearch (VectorChord é revogado por licença),
carregue em banco novo e reproduza a suíte. Pronto quando a carga der exit 0 com 131 tabelas,
139 FKs e 402 CHECKs e a suíte devolver 127 recusas, 27 aceites e 0 falhas."*

#### F0.O6 — Catálogo único de ferramentas (53 com schema + 13 reservadas)

**Resultado:** existe **um** catálogo; nome reservado é nome, não contrato.
**Pronto:** `go run ./cmd/enaeval-catalog -repo . -out wj/mcp/catalog/catalog.json` →
`com_schema 53 · implemented 14 · stub 39 · reserved 13 · total 66`; `go run ./cmd/enaeval-probe` →
`62 (53 canônicas + 9 aliases) · sem title 0 · sem outputSchema 0 · com $ref de rede 0`;
`go test ./wj/mcp/catalog` → `TestNomesInventadosNaoExistem` e `TestReservadasNaoEntramEmToolsList` PASS.
**Insumos:** `G04-code/enaeval/cmd/enaeval-catalog/` (**já lê G01 e G02** desde a FIX-A) ·
`research-v4/tools/{catalog.json,reservados-g06.json}` · os 5 catálogos de origem
(C03 4 · F02 5 · F03 5 · F05 11 · F07 10) + G01 6 + G02 11. **Entregáveis:** `wj/mcp/catalog/`,
`cmd/enaeval-catalog`. **Depende:** F0.O7 (caminho final). **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[I]** Mover gerador e catálogo; manter I1–I5 e os nomes inventados (`wj_arena_settle`,
      `wj_social_reputation`) **inexistentes**.
- [ ] **[E]** Catálogo publicado ≠ catálogo gerado ⇒ CI vermelho.
- [ ] **[A]** `serverInfo.version` = `catalog_version` (hoje o handshake diz `0.1.0`, o registry `1.3.0`).
**Goal:** *"Objetivo F0.O6. Leia D-5' em `DECISOES-ORQUESTRADOR.md`, `research-v4/FIX-A.md` §3 e o gerador
em `research-v4/G04-code/enaeval/cmd/enaeval-catalog/`. A reconciliação já foi feita: mova o
gerador e o catálogo para `wj/mcp/catalog`, torne a divergência entre gerado e publicado uma
falha de CI e iguale `serverInfo.version` a `catalog_version`. Pronto quando o gerador imprimir
53 com schema e 13 reservadas e o probe listar 62 ferramentas sem nenhuma falta de title,
outputSchema ou `$ref` local."*

#### F0.O7 — Monorepo `wj` (25 pacotes, `go 1.25` pinado, depcheck + CI)

**Resultado:** acabam os 12 módulos Go independentes; a dependência passa a ser verificada por
máquina, inclusive transitivas. **Pronto:** `go run ./cmd/wj-depcheck` →
`25 pacotes verificados, 0 violações`; `GOTOOLCHAIN=local go vet ./... && go test -count=1 ./...` →
verde; `task ci` roda depcheck → wjlint → TLC → `go test` e falha no primeiro vermelho.
**Insumos:** `research/E07-arquitetura/{deps.yml,depcheck.go}` (**compila e roda**) ·
`G04-code/enaeval/deps/enaeval.deps.yml` (patch com MCP-1…7) · `F11-code/go.mod` (único com
`module wj`) · `research/D10-code/tla/*.tla` · `INVENTARIO-CODIGO.md` §5 e §6.
**Entregáveis:** `go.mod`, `deps.yml` mesclado, `cmd/wj-depcheck`, `Taskfile.yml`, `.forgejo/workflows/ci.yml`.
**Depende:** F0.O2, F0.O3, F0.O4, F0.O6. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[A]** Mesclar os dois `deps.yml`; `go: "1.27"` → **`go: "1.25"`** (o 1.27 era alvo sem
      artefato; `go-sdk` exige ≥ 1.25).
- [ ] **[I]** Migrar nesta ordem: `tipos` → `calc` (C03+F05, já ligados por `replace`) → `receipt` →
      `verify` → `grafo` → `policy` → `econ` → `mcp*` → `mlops`.
- [ ] **[E]** CI com **`GOTOOLCHAIN=local`** — `GOTOOLCHAIN=auto` **baixou** toolchain no H01, que é
      egresso silencioso em build e o S4 proíbe.
- [ ] **[I]** TLC de `EscalonadorGPU.tla` e `PromocaoModelo.tla` no CI; portão de literal de fonte única.
- [ ] **[E]** `research/D09-drafts` sai (quase-duplicata de `E01-drafts`, que é a cópia posterior).
**Goal:** *"Objetivo F0.O7. Leia `research/E07-arquitetura/deps.yml`, o patch
`research-v4/G04-code/enaeval/deps/enaeval.deps.yml`, `INVENTARIO-CODIGO.md` §5 e §6 e
`CANON-v4.1.md` §5. Pronto quando o depcheck imprimir 25 pacotes verificados com zero violação e
`go test ./...` ficar verde sem baixar toolchain."*

---

### FASE F1 — SUPERFÍCIE VIVA (o que as IAs já usam, corrigido e ampliado)

O `/mcp` de produção (v1.2.0, 15 ferramentas, no Registry) **não para**: a camada nova sobe ao lado e
absorve. Os defeitos desta fase foram **medidos** (F06 §1, n=80): 87,5% de páginas com dois títulos,
80/80 sem `ETag`, 80/80 sem `cite-as` em HTML, 15/15 tools sem `title`, IndexNow e `did.json` em 404.
**Recurso: CPU + edge. 0 GPU.**

#### F1.O1 — `enaeval-mcp` em `/mcp2` com 14 motores reais e cota que sobrevive a restart

**Pronto:** `go run ./cmd/enaeval-probe -addr https://wikijuridica.com.br/mcp2` passa ponta a ponta;
`wj_prazo` em ≤ 3 ms; após restart do processo, `SELECT usadas FROM quota_did` preserva o valor;
**7 ciclos diários consecutivos** de log sem `tool not found` de cliente conhecido;
`go test ./wj/mcp/... -run 'TestMCP[1-7]'` → 7/7 PASS.
**Insumos:** `G04-code/enaeval/{server,dialog,ratelimit,wba,pay,obs}` (43 testes, probe em
`logs/g04_probe.log`) · `SCHEMA-v4.1.sql` (`quota_did`, `m2m_call`) · `F05-code/mcp/` + `cmd/wjmcp` ·
`G04-enaeval-m2m.md` §4 e §6 · `CANON-v4.1` §8 C16/C25.
**Entregáveis:** `wj/mcp/`, `wj/mcp/adapters/`, `wj/agent/dialog/`, `wj/econ/{quota,x402}/`.
**Depende:** F0.O1, F0.O5, F0.O6, F0.O7. **Recurso:** CPU, 0 GPU. **Dono:** nenhuma.
- [ ] **[A]** Chave do `requestState` = `HKDF(K_root, "wj/requestState/v1")`, **não aleatória por
      processo** — hoje o `clarify` respondido pela réplica B falha como "forja ou reinício".
- [ ] **[A]** Cota e `LastTx` em PostgreSQL, não em `map[string]int`.
      `go test ./wj/econ/quota -run TestCotaSobreviveRestart` → `PASS`.
- [ ] **[A]** Buckets anônimos em LRU com **teto de 64 k** por `/24+ASN` (C16); DID só ganha bucket
      após `enroll` com JWKS válido. Ataque de 10⁶ DIDs sybil → RSS estável.
- [ ] **[I]** 14 motores reais (3 C03 + 11 F05); os demais como **stub honesto** (MCP-6).
- [ ] **[E]** `/.well-known/wj-tools.json`: uma IA lê preço e cota **sem chamar ferramenta** (MCP-4).
**Goal:** *"Objetivo F1.O1. Leia `G04-enaeval-m2m.md` §§1, 4, 6 e 7, `H01-critico-fable.md` §6 (G13), D-6' e
o código de `research-v4/G04-code/enaeval/`. Pronto quando o probe passar contra o endereço
público, a cota sobreviver a restart, os 7 invariantes MCP passarem e 7 ciclos diários
consecutivos não mostrarem `tool not found` de cliente conhecido."*

#### F1.O2 — Migração do `/mcp` v1.2.0 sem quebrar cliente

**Pronto:** `calcular_prazo` responde `200` com `_meta.tool = "wj_prazo"`; `server.json` publicado como
**1.3.0** com `_meta.migration_from_1_2_0` listando os aliases; busca `?search=juridic` no Registry
devolve as ferramentas **com `title`** (hoje 15/15 sem); `go test ./wj/mcp -run TestMCP7` → `PASS`.
**Insumos:** `G04-enaeval-m2m.md` §6 (tabela de migração, sequência O1–O5) ·
`G04-code/enaeval/registry/server.json` · `F01-code/ai-source-card.json` · `CANON-v4.1` §8 C25.
**Entregáveis:** `wj/mcp/alias.go`, `wj/mcp/registry/server.json`. **Depende:** F1.O1.
**Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[E]** Cada nome de produção vira ferramenta própria marcada DEPRECADO apontando o sucessor,
      com o **mesmo motor** por trás; `mudancas_desde` → alias de `wj_freshness` com o modo cursor.
- [ ] **[E]** `contexto_juridico` → `wj_grounding_pack`: GP/1 de 5 claims = **1.322 tokens** contra
      **9.176** do `contexto_juridico` ao vivo (**−85,6%**, medido pelo F01).
- [ ] **[E]** **Nenhuma remoção nesta versão**; remoção futura só após 2 versões menores com alias marcado.
**Goal:** *"Objetivo F1.O2. Leia `G04-enaeval-m2m.md` §6 e `CANON-v4.1.md` §1 e §8 (C25). Pronto quando
`calcular_prazo` responder com `_meta.tool = wj_prazo`, o Registry devolver tudo com `title` e o
teste de alias órfão passar."*

#### F1.O3 — Consistência de identidade: `ETag`, `cite-as`, `Legal-Time`, IndexNow, 402, `wjconsist`

**Resultado:** a mesma página tem **uma** identidade pelas três portas (HTML, `/index.md`,
`Accept: text/markdown`); o defeito de dois títulos em ~16,4 mil páginas some.
**Pronto:** `wjconsist --sitemap` sobre amostra estratificada n=80 → **80 PASS, 0 FAIL** (demonstrado
em laboratório: 5 FAIL → 5 PASS); `curl -sI` de qualquer página → `ETag` (32 hex de sha256) +
`Link: rel="cite-as"` + `Repr-Digest`; 2ª requisição → **304**; `/norma/{urn}?em=D` → `302` para
`?em={início do intervalo}&modo=vigencia&tx={tx}` com cabeçalho `Legal-Time`; IndexNow devolve `200`
em 10 URLs e p95 publicação→submissão ≤ 60 s.
**Insumos:** `F06-code/{audit/,wjconsist.log,tbv.log}` · `F06-confianca-operacional.md` (C01–C26) ·
`CANON-v4.1` §8 e §1. **Entregáveis:** `wj/api/http/{etag,citeas,legaltime,linkset}.go`, `wj/edge/`,
`wj/mlops/wjconsist/`. **Depende:** F0.O1, F0.O4. **Recurso:** CPU + edge. **Dono:** item 7 de §0.5.
- [ ] **[E]** **Tupla de identidade de fonte única por página** (título, `canonical`, `cite-as`,
      `version`, `content_sha256`) em **um struct**; as três portas renderizam dele; `wjconsist`
      fail-closed na pré-publicação **e** pós-deploy.
- [ ] **[E]** URI de versão imutável `/{área}/{slug}/@v/{sha12}/` com `immutable` + `X-Robots-Tag: noindex`;
      linkset RFC 9264 nível 2.
- [ ] **[E]** Corrigir os 404 que deveriam ser 200: `rsl.xml`, chave IndexNow, `did.json`,
      `lar/checkpoint`, `scitt-keys`, diretório WBA.
- [ ] **[E]** `robots.txt` e cabeçalho gerados de **um só struct** (`Content-Usage`, `Content-Signal`,
      RSL `License:`, grupo Bingbot, `Allow: /norma/` **antes** de `Disallow: /*?`); `security.txt`
      com `Policy`, `Encryption`, `Acknowledgments` e assinatura OpenPGP.
- [ ] **[E]** **402 só em rota `noindex`** (4xx em URL indexável = conteúdo inexistente para o Google);
      bot verificado **nunca** leva 429.
**Goal:** *"Objetivo F1.O3. Leia `CANON-v4.1.md` §8 inteiro (C01–C26) e §1 (defeitos medidos com n=80) e o
código de auditoria em `research-v4/F06-code/audit/`. A alavanca de maior retorno é
consistência: crie a tupla de identidade de fonte única por página, faça as três portas
renderizarem dela com `wjconsist` fail-closed antes e depois do deploy, corrija os seis 404,
publique ETag, cite-as, Repr-Digest, linkset, URI de versão imutável, Legal-Time e IndexNow, e
restrinja o 402 a rota noindex. Pronto quando `wjconsist` der 80 PASS e 0 FAIL e a 2ª requisição
devolver 304."*

#### F1.O4 — AI Source Card real e `/transparencia/qualidade.json` com denominador

**Pronto:** `curl -sI /` → `Link: </.well-known/ai-source-card.json>; rel="describedby"`;
`jq '.hcr_ucb95' /transparencia/qualidade.json` → **≤ 0,02**, com `n_emitidas`, `n_INVALID`, `n_RX` e
cobertura com denominador explícito; `jq '.tools_live'` = contagem **derivada do catálogo** (hoje o
arquivo declara 15 à mão e lista 3 planejadas sem spec em lugar nenhum).
**Insumos:** `F01-code/ai-source-card.json` · `G04-code/enaeval/identity/ai-source-card.json` ·
`CANON-v4.1` §8 C17/C22/C23 e §10 (sete desfechos).
**Entregáveis:** `wj/api/wellknown/aisourcecard.go`, `wj/mlops/transparencia/`.
**Depende:** F0.O6, F1.O1. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[A]** `tools_live` derivado do catálogo, nunca número escrito à mão.
- [ ] **[E]** HCR com **UCB95 Clopper–Pearson** e teto 2%; erro do mundo (norma mudou) **não conta**
      como erro nosso — `is_error` é GENERATED no schema.
- [ ] **[E]** `/status.json` assinado com SLO **99,9%** para `/mcp` e `/api/v1/citacoes` (C17).
**Goal:** *"Objetivo F1.O4. Leia `CANON-v4.1.md` §8 (C17, C22, C23) e §10, e os dois `ai-source-card.json`
do repositório. Pronto quando o `Link: rel=describedby` aparecer na home e no api-catalog e o
HCR publicado ficar em 2% com denominador visível."*

#### F1.O5 — Radar de citação por motor (medição sem API dos motores)

**Pronto:** `SELECT motor, count(*) FROM bot_hit … GROUP BY 1` → **≥ 95% dos hits classificados** em 3
classes (assinado · IP verificado · não verificado); o experimento em cunha escalonada (4 ondas de 25%
por `hash(path)`) produz estimativa Callaway–Sant'Anna com CUPED e IC que **não cruza zero**.
**Insumos:** `CANON-v4.1` §8 (Medição sem API dos motores, D8: potência de 839 páginas/braço a 0,10
citação/página/dia; com 4.000/braço o efeito mínimo detectável é 6,9%; o acervo de 18.774 sobra) ·
`F06-code/audit/` · `SCHEMA-v4.1.sql` (`bot_hit` particionada).
**Entregáveis:** `wj/mlops/radar/`, `wj/api/http/botclass.go`, view `v_citacao_por_motor`.
**Depende:** F1.O3. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[E]** Classificação por RFC 9421, faixa IP publicada e rDNS, em tabela particionada.
- [ ] **[E]** Sinais sem API: fetchers em tempo real · `utm_source=chatgpt.com` · `Referer` · Citation
      Share oficial do Bing · condicionais/304 · latência de descoberta · **404 de URL alucinada** ·
      absorção medida no próprio `/verify`.
- [ ] **[E]** Cunha escalonada por `hash(path)` — prova causalidade **sem desligar nada que cita**.
      A **sonda ativa paga** do v3 está **REVOGADA**: o radar não depende de chave de API de motor nenhum.
**Goal:** *"Objetivo F1.O5. Leia `CANON-v4.1.md` §8 (Medição sem API dos motores) e §1 (os três canais).
Nenhuma página sai do ar e nenhuma chave de API paga entra. Pronto quando 95% dos hits estiverem
classificados por motor e o experimento devolver efeito com IC que não cruza zero."*

---

### FASE F2 — CONHECIMENTO VIVO (o produto que faz a IA voltar)

Fluxo diário de 30 mil decisões, coleta assinada e atestada, claim verificável, grafo e invalidação.
**Recurso: CPU pesada (≈ 3,5 CPU-dias de máquina de backfill) e GPU leve (≈ 0,8 GPU-dia de máquina).**

#### F2.O1 — Framework de coleta assinado + G03 fase A (fontes com API e íntegra)

**Pronto:** **100% dos 42 CSVs do TCU e dos 585.274 registros do CARF com `norm_ok = 1`**; **≥ 99% dos
1.502 temas do STJ com passaporte**; latência de delta ≤ 24 h;
`psql -c "SELECT count(*) FROM capture WHERE level='C0' AND sealable"` → **0**.
**Insumos:** `G03-code/{source,prov,canon,wba,dedup,ckpt,shape,policy}` (12 testes verdes) ·
`G03-maximo-fontes.md` §§1–4 e §6 linha A · `F08-code/` (WARC + in-toto DSSE + COSE Hash Envelope;
20/20 + 10/10 ataques) · `SCHEMA-v4.1.sql` (`capture`, C0–C3).
**Entregáveis:** `wj/mlops/harvest/`, `wj/policy/fonte/`, `wj/lex/canon/`.
**Depende:** F0.O1, F0.O4, F0.O5. **Recurso:** CPU ~310 k núcleo-s de fase, 0 GPU. **Dono:** nenhuma.
- [ ] **[I]** Mover `G03-code` para `wj/mlops/harvest`; manter `wj-norm/f5-cspm-tail-v1` e o teste que
      prova que a regex canônica rejeita `wj-norm/f5-cspm@1`.
- [ ] **[E]** **`sealable` exige `level ∈ {C2,C3}`** para fonte sem assinatura de origem; C1 só sela
      com `src_sig_ok` (DOU em ICP-Brasil). Fecha o GRAB-RAG: captura C0/C1 envenenada por middlebox
      deixa de gerar recibo válido.
- [ ] **[E]** Fase A: TCU bulk, CARF Solr, STJ CKAN, BNP, CNJ SGT, TST, Planalto, Câmara/Senado/LexML,
      enunciados. NFC obrigatório; MinHash sobre ~35 GiB.
- [ ] **[E]** Consolidação adversarial D0–D3 — as fontes oficiais **são adversariais**, e está medido:
      `historico` do BNP replicado em 1.479/1.479 temas de RG, 2,00% de teses degeneradas, 25,7% sem
      tese, 29 duplicatas byte-a-byte no CKAN do STJ.
**Goal:** *"Objetivo F2.O1. Leia `G03-maximo-fontes.md` §§1–4 e §6 linha A, `CANON-v4.1.md` §10 (níveis
C0–C3, `man_sha256` redefinido) e §13, `H01-critico-fable.md` §3 (GRAB-RAG), e o código de
`research-v4/G03-code/` e `F08-code/`. Pronto quando 100% dos CSVs do TCU e dos registros do
CARF tiverem `norm_ok = 1`, 99% dos temas do STJ tiverem passaporte e nenhuma captura C0 estiver
selada."*

#### F2.O2 — G03 fase B: gatilho DataJud e inteiro teor

**Pronto:** **≥ 95% das decisões novas de TJSP/TJRJ/TRFs com inteiro teor em ≤ 48 h do movimento**;
**0 gap no PIT**; CPU medida ≤ 20% da folga (435.944 núcleo-s/dia).
**Insumos:** `G03-maximo-fontes.md` §6 linha B (gatilhos: movimentos 92/1061/581) ·
`CANON-v4.1` §3 (a linha "1,2 M núcleo-s/dia" era **erro de unidade**: é total de fase; em regime são
46.440/dia, já contados no F01) · `research/D06-code/`.
**Entregáveis:** `wj/mlops/harvest/datajud/`. **Depende:** F2.O1.
**Recurso:** CPU ~1,2 M núcleo-s **total de fase** (≈ 2,8 CPU-dias de máquina); GPU de pico 4.000/dia,
classe 4 preemptível, que **substitui** os 600 de OCR canônico. **Dono:** nenhuma.
- [ ] **[E]** Delta diário: `size=5000`, timeout **< 60 s** (o balanceador mata em 60).
- [ ] **[E]** Backfill escopado com **PIT + tiebreaker `_shard_doc`**, filtrado por movimento decisório,
      como job River de fundo fora do caminho de latência.
- [ ] **[E]** Espelho bulk do dataset DataJud localizado e usado — obrigatório, não opcional.
**Goal:** *"Objetivo F2.O2. Leia `G03-maximo-fontes.md` §6 linha B, a correção de unidade em `CANON-v4.1.md`
§3 e `H01-critico-fable.md` §1 (G2). Pronto quando 95% das decisões novas de TJSP, TJRJ e TRFs
tiverem inteiro teor em até 48 h do movimento, o PIT não tiver lacuna e a CPU ficar em 20% da
folga."*

#### F2.O3 — Claim verificável (F01), answer unit v2 e GP/1

**Pronto:** `build_examples.py` → **11 exemplos, `schema_errors = 0`, `jsonld_ok = True`**;
`test_schema_negativos.py` → **27/27 ataques recusados · 58/58 positivos aceitos**; `cbor_claim.py` →
CBOR válido pela CDDL; GP/1 de 5 claims ≤ **1.400 tokens** (medido 1.322 contra 9.176);
`SELECT count(*) FROM answer_unit WHERE receipt_id IS NULL` → **0**.
**Insumos:** `F01-code/` (schema já corrigido pela FIX-A; `au_v2.py`, `gp1.py`, `claim.cddl`,
`context.jsonld`, 11 exemplos) · `CANON-v4.1` §7 (span **DUPLO**, cobertura-com-cota).
**Entregáveis:** `wj/lex/claims/`, `wj/api/{au,gp1}/`,
`cmd/wjunits`. **Depende:** F0.O2, F0.O4, F0.O5. **Recurso:** GPU do fluxo diário (10.622/dia em
regime). **Dono:** item 5 de §0.5 (10 páginas por lote).
- [ ] **[I]** Mover `F01-code` para `wj/lex/claims`; manter os 58 positivos e os 27 ataques.
- [ ] **[E]** `cmd/wjunits` com o verificador como **portão fail-closed**: 0 unit sem recibo.
- [ ] **[A]** `gp1.py`/`au_v2.py` deixam de exigir o tokenizer em `sys.argv[1]`.
- [ ] **[E]** Cobertura-com-cota: **ausência canônica** em vez de silêncio.
**Goal:** *"Objetivo F2.O3. Leia `CANON-v4.1.md` §7 inteiro, `research-v4/FIX-A.md` §1 e o código de
`research-v4/F01-code/`. O schema do claim já foi corrigido — não o reescreva. Pronto quando os
11 exemplos gerarem zero erro de schema, os 27 ataques e os 58 positivos passarem e o GP/1 de 5
claims couber em 1.400 tokens."*

#### F2.O4 — Jurisprudência estruturada (F03): passaporte e estado de tese

**Pronto:** replay de 1.473 registros do STJ → **1.470 aceitos (99,80%), 3 anomalias em quarentena**;
`go test ./wj/grafo -run TestErosaoNuncaMata` → `PASS`; transição de `tese_estado` fora de
`transicao_permitida` recusada pelo banco. **Insumos:** `F03-code/` (**schema carregado em PG com
dados reais**: 1.473 precedentes, 4.831 `tese_estado`, grafo AGE) · `F03-jurisprudencia-estruturada.md`
· `F07-code/exemplos/passport_f07_tema_stj_1098.json`. **Entregáveis:** `wj/grafo/precedente/`,
`wj/lex/tese/`. **Depende:** F0.O5, F2.O1. **Recurso:** GPU 922/dia em regime; backlog 65.270 GPU-s
≈ **0,8 GPU-dia de máquina**. **Dono:** nenhuma.
- [ ] **[I]** Migrar o modelo **precedente-cêntrico** do F03 (com `ordinal`, `acordao_urn`, `snap_id`)
      — é o que tem dados reais; o `tese`-cêntrico do E07 cede.
- [ ] **[E]** Parser **ZERO-LLM** de ementa pelo padrão Rec. CNJ 154/2024 (já em 37,9% das ementas do
      STJ de 2026): 19.537 questões, 247 clusters ≥ 3 acórdãos, 53 cruzando ≥ 2 tribunais.
- [ ] **[E]** Tese tem **versões e variantes** (o Tema 69 tem 4 variantes oficiais), uma canônica por
      versão; **superação tácita nunca é certeza** sem ato oficial (`claim.warn`, nunca `claim.dead`).
**Goal:** *"Objetivo F2.O4. Leia `F03-jurisprudencia-estruturada.md`, `CANON-v4.1.md` §13 e o código e SQL
de `research-v4/F03-code/`, que já está carregado em PostgreSQL. Pronto quando o replay dos
1.473 registros aceitar 1.470 e mandar 3 para quarentena e o teste que prova que erosão nunca
mata uma tese passar."*

#### F2.O5 — Motor tri-temporal e `/norma` em data D

**Pronto:** `/norma/{urn}?em=D` com p95 ≤ **80 ms** e cache ≥ 97%; `EXCLUDE USING gist` garante ≤ 1
versão e a CONSTRAINT TRIGGER de totalidade recusa linha do tempo que não termine em +∞;
**D0∪D1 ≥ 98%** nas 200 leis-âncora **ou** taxa de D3 publicada.
**Insumos:** `research/A03-vigencia-temporal.md` · `F05-code/{literate,registro}` · `CANON-v4.1` §13 e
§8 C07 · `SCHEMA-v4.1.sql`. **Entregáveis:** `wj/temporal/`, `wj/api/http/norma.go`, `cmd/wjcanon`.
**Depende:** F0.O5, F2.O1. **Recurso:** CPU, 0 GPU. **Dono:** item 3 de §0.5 (adjudicação D3).
- [ ] **[E]** `chk_continuidade` reescrito com `unnest` — o do A03 **nunca rodou**
      (`cardinality(datemultirange)` não existe em PG 16/17/18).
- [ ] **[E]** Parsers P1 (lei compilada), P2 (portal) e P3 (Senado) + forma canônica D0–D3 + overlay
      ADI/MP; só o resíduo sobe para adjudicação.
- [ ] **[E]** **Apelido normativo = f(string, DATA do documento citante)**: "Lei de Licitações" é
      8.666/93 antes de 30/12/2023 e 14.133/2021 depois. Constante seria erro de vigência.
- [ ] **[E]** Revogação é **versão de texto vazio**, nunca ausência de linha; `?em=` → 301 para
      `?v=<fronteira de versão>`, conjunto **finito** de URIs, `tx` só de raízes MMD publicadas.
**Goal:** *"Objetivo F2.O5. Leia `research/A03-vigencia-temporal.md`, `CANON-v4.1.md` §13 e §8 C07, e o
código de vigência em `research-v4/F05-code/literate`. Pronto quando `/norma` tiver p95 de 80 ms
com cache acima de 97% e D0∪D1 cobrir 98% das 200 leis-âncora ou a taxa de D3 estiver publicada.
Suba ao dono só as divergências que os três parsers não resolvem."*

#### F2.O6 — Grafo `wjg`: travessia curada, CSR compacto e PPR por forward push

**Pronto:** CSR em Go ocupa **≤ 3 GB para 900 M arestas**; PPR por forward push (`r_max = 1e-4`) em
**≤ 6,7 ms**; `go test ./wj/grafo -bench BenchmarkPPR` dentro do limite.
**Insumos:** `F03-code/sql/f03_age.sql`, `F02-code/sql/age_doutrina.sql` ·
`research/C02-knowledge-graph.md` · `CANON-v4.1` §13 (**AGE VLE PROIBIDO**: ~14,3 GB por backend).
**Entregáveis:** `wj/grafo/{csr.go,ppr.go,cypher.go}`. **Depende:** F0.O5, F2.O4.
**Recurso:** CPU + RAM (CSR de 1,48 GB sai dos residentes para o envelope). **Dono:** nenhuma.
- [ ] **[E]** **Citação bruta fica FORA do AGE** — tabela relacional particionada por `data_julg`, BRIN.
      Escala do grafo curado: 40,6 M nós / 301,4 M arestas.
- [ ] **[E]** CSR compacto em Go no lugar do VLE; sem *list comprehension* em Cypher.
- [ ] **[E]** Teste que prova `create_graph('wjg')` e que `'wj'` falha.
**Goal:** *"Objetivo F2.O6. Leia `CANON-v4.1.md` §13, `research/C02-knowledge-graph.md` e o SQL de grafo de
F03 e F02. Pronto quando o CSR couber em 3 GB para 900 M arestas e o PPR responder em 6,7 ms."*

#### F2.O7 — Feeds, invalidação e errata em ≤ 60 s

**Pronto:** uma IA que chamou `wj_tese_status` num ciclo recebe, **sem perguntar**, o aviso de que a
tese mudou, e o log mostra o `wj.agent.did` que recebeu; propagação por **6 canais em ≤ 60 s**;
`errata_ataques.sql` → **6/6 recusados + 2/2 aceitos**; `/feeds/errata.atom` válido em RFC 4287 com
arquivos RFC 5005. **Insumos:** `F06-code/sql/errata.sql` · `F01-code/feeds.schema.json` ·
`G04-code/enaeval/dialog/` (`Memory.CachedAt` já existe e é testado) · `CANON-v4.1` §8 C24 (SLA:
S1 ≤ 4 h · S2 ≤ 24 h · S3 ≤ 72 h · S4 ≤ 14 dias). **Entregáveis:** `wj/mlops/errata/`, `wj/api/feed/`,
`wj/mcp/subscriptions.go`. **Depende:** F1.O1, F2.O3. **Recurso:** CPU + edge. **Dono:** nenhuma.
- [ ] **[E]** `wj_invalidation_check` ligado a `Memory.CachedAt` e a `subscriptions/listen` — é o
      gancho de retorno de maior alavanca do catálogo, e todo o estado de que precisa já existe.
- [ ] **[E]** `POST /receipts/expired` + hub WebSub próprio + `GET /feed/events?since=<cursor>` em
      JSONL com ETag/304 no edge.
- [ ] **[I]** Errata **nunca apaga**: claim novo + `status.successor` + Retraction Statement no log;
      erro do mundo não conta como erro nosso.
**Goal:** *"Objetivo F2.O7. Leia `CANON-v4.1.md` §8 (C24) e §12 (Feeds), `G04-enaeval-m2m.md` §8 e o código
de `F06-code/sql/errata.sql` e `G04-code/enaeval/dialog/`. Pronto quando uma IA que consultou
uma tese receber o aviso de mudança sem perguntar, o log mostrar o DID que recebeu e os ataques
de errata devolverem 6 recusas e 2 aceites."*

---

### FASE F3 — MOTOR (o 8B jurídico servido; o verificador calibrado)

**É aqui que o perfil `construcao` é ligado** (D-10'): o 8B ainda é obra e não serve; treino e
indexação são classe 1; semeadura a **25% (150 debates/dia)**; OCR a **50%**; **80.165 GPU-s/dia
livres**. Custo acumulado da fase: **8,87 GPU-dias de máquina** (F04 §4.2, do início ao canário).

#### F3.O1 — `wj-llm-8b` NVFP4 servido em vLLM sm_120, egresso zero

**Pronto:** **KLD ≤ 10⁻³** contra `nvidia/Qwen3-8B-NVFP4` (R-eq, S4); **TTFT p95 < 500 ms em c = 16**;
`comp.EgressProbe` → **0 conexões em 24 h** contra os 6 alvos; VRAM ≤ **15,23 GiB** (ou o fallback
**15,54 GiB** registrado no `promotion_gate`, com KV em 4,69 GiB ≈ 117 k tokens);
`grep -rn "chat_template" wj/` → 0. **Insumos:** `F11-code/recipes/{vocab_trim.py,nvfp4_modelopt.py,
egress-zero.conf,compact.sh}` · `F11-code/bom/bom.json` (27 componentes, 56 implementações) ·
`CANON-v4.1` §4 (receita canônica e fallback numérico) e §5. **Entregáveis:** `wj/serve/model/`,
`ops/vllm/`. **Depende:** F0.O7. **Recurso:** GPU, perfil construção. **Dono:** nenhuma.
- [ ] **[I]** Caminho canônico: artefato NVFP4 → `vocab_trim.py` (151.936 → 80.916) → `lm_head` FP8 ⇒
      **4,90 GB (4,56 GiB)**. Fallback BF16 documentado e numerado, nunca escondido.
- [ ] **[E]** Egresso zero em três camadas: `IPAddressDeny=any` (cgroup-BPF) · opt-outs verificados no
      código-fonte · sonda a cada 5 min. Um `connect` que passe **derruba o serving** (SEV1).
- [ ] **[E]** Prompt renderizado por `text/template` em Go com hash em
      `quantized_artifact.template_sha256`. Template do artefato baixado **nunca** é executado.
- [ ] **[E]** **BOSCH é fase própria com portão** (F10.O2): o canário sobe com atenção plena e
      KV 5,00 GiB = 124.830 tokens.
**Goal:** *"Objetivo F3.O1. Leia `CANON-v4.1.md` §4 (Receita do 8B, Egresso zero, Soberania S1–S6) e §5,
`H01-critico-fable.md` §2 (G16, G18) e as receitas de `research-v4/F11-code/recipes/`. BOSCH não
entra aqui. Pronto quando a KLD ficar em 10⁻³, o TTFT p95 abaixo de 500 ms com 16 sessões, a
sonda registrar zero conexões em 24 h e o mapa de VRAM couber em 15,23 GiB."*

#### F3.O2 — `wj-nli-54M` calibrado e o verificador único V1–V7

**Pronto:** `conformal_calibration` com **UB95 ≤ 0,913%** a n ≥ 1.000 (Clopper–Pearson);
`go test ./wj/verify` → V1–V7 completos com **7 desfechos tipados E1–E7, nunca booleano**;
**HCR ≤ 2%** no split privado **no artefato quantizado**; `evict ∩ span(⟨PROVA⟩) = ∅` imposto pelo
serializador. **Insumos:** `wj/verify` (de F0.O3) · `CANON-v4.1` §4 (mmBERT-small podado 140M → 54M,
cross-encoder) e §10 · D-2' e D-3. **Entregáveis:** `wj/verify/{v1..v7}.go`, `wj/verify/nli/`,
`wj/serve/serializer.go`. **Depende:** F0.O3, F3.O1. **Recurso:** GPU leve no fine-tune; verificação
é CPU/54M. **Dono:** item 2 de §0.5 (3.000 rótulos em 4 lotes).
- [ ] **[E]** **10.000 negativos duros programáticos** (claim × artigo vizinho) **antes** de qualquer
      rótulo humano — é o que torna 3.000 rótulos suficientes.
- [ ] **[E]** V7 relevância é **obrigatório** (URN ∈ top-k): sem ele o HCR mente.
- [ ] **[E]** Caminho de verificação com prefix caching desligado **por requisição** via `cache_salt`
      aleatório em `SamplingParams`; grava `sha256(cache_salt‖engine_config)` no recibo; custa < 3%.
      Serving comum mantém prefix caching.
- [ ] **[E]** **Proibido baixar τ** quando o portão falha: sobe τ, audita com o professor, amplia rótulos.
**Goal:** *"Objetivo F3.O2. Leia `CANON-v4.1.md` §4 (Verificador — ÚNICO) e §10, D-2' e D-3, e o pacote
`wj/verify` de F0.O3. Pronto quando a calibração tiver UB95 de 0,913% com n de 1.000, o HCR
ficar em 2% no artefato quantizado e o serializador provar que nenhum token de span de prova é
despejado. Se o portão falhar, suba o τ — baixar é proibido."*

#### F3.O3 — Escalonador `wj/serve` real: latch, MPS, dois perfis, λ vetorial

**Pronto:** requisição paga injetada durante lote preempta em **≤ 100 ms sem perder KV**;
**0 requisições classe 1 perdidas em 10 k iterações**; `v_orcamento_gpu` bate com `orcamento_v4.py`
(regime **36.185 = 79,4%**, sobra 9.415); TLC de `EscalonadorGPU.tla` → **1.936 estados, 0 erros**.
**Insumos:** `research/E02-code/{escalonador.go,latch.go}` (**não compila**: `Classe.String`, `itoa`,
`ErrLeaseOcupado`, `ErrLeasePerdido` indefinidos — é pseudocódigo literate) ·
`research/D10-code/tla/EscalonadorGPU.tla` (design **verificado**) · `F04-code/go/precos.go` ·
`research-v4/orcamento/orcamento_v4.py` · `CANON-v4.1` §3.
**Entregáveis:** `wj/serve/{sched,latch,memd}.go`, `wj/econ/lambda.go`, `cmd/wj-memd`.
**Depende:** F3.O1, F0.O7. **Recurso:** GPU + RAM. **Dono:** nenhuma.
- [ ] **[E]** Escrever o escalonador a partir do `.tla` verificado. **Sinal latchado e contínuo**: o
      defeito do A05 (perda de requisição paga por `Sleep` antes de checar a fila) fica
      estruturalmente impossível.
- [ ] **[E]** Prioridade: **pago > answer unit > treino > OCR > mídia**. O lote **freia** (20% → 5% dos
      SMs), não desliga; `vllm.Sleep` só para troca de modelo.
- [ ] **[E]** **`λ_gpu[classe][hora]`** com fonte única `econ.LambdaGPU(classe, hora)` — sob congestão,
      rotear ao 4B pode aumentar o gasto **por citação verificada**.
- [ ] **[E]** `wj-memd`: leilão do envelope de 6.656 MiB por λ_ram, **um locatário por vez**, imposto
      por cgroup v2. Os 3.030 MiB novos dos relatórios F/G entram aqui, **nunca residentes**.
**Goal:** *"Objetivo F3.O3. Leia `CANON-v4.1.md` §3, D-9, `H01-critico-fable.md` §5(c), a especificação
verificada em `research/D10-code/tla/EscalonadorGPU.tla` e o pseudocódigo de
`research/E02-code/`, que não compila. Pronto quando a preempção medir até 100 ms sem perder KV,
10 mil iterações não perderem nenhuma requisição de classe 1 e a view de orçamento bater com
`orcamento_v4.py`."*

#### F3.O4 — Treino de construção: P2 → SFT → GSPO-DrC → canário

**Pronto:** canário serve **500 chamadas pagas sem SEV**; **G1–G5 no artefato quantizado** (ligar bench
a checkpoint BF16 é irrepresentável no banco); recompensa verificada `0,35 URN + 0,30 NLI + 0,10
formato + 0,10 concisão + E7 − 0,60 vigência errada − 1,0 citação inventada`, com **piso de 2/8
rollouts não-correntes**. **Insumos:** `F04-hardware-exato.md` §4.2 (custo acumulado por etapa em
GPU-dias de máquina) · `CANON-v4.1` §4 (Treino) · `research/D05-aprendizado-continuo.md` ·
`F11-code/comp/`. **Entregáveis:** `wj/mlops/train/`, `promotion_gate` populado.
**Depende:** F3.O1, F3.O2, F3.O3. **Recurso:** **8,87 GPU-dias de máquina** acumulados. **Dono:** nenhuma.
- [ ] **[E]** Ordem obrigatória (o índice tier-1 precede o GSPO porque a recompensa usa E7/top-k):
      P2 + SCoRe → embeddings tier-1 + ColBERT → vocabulário + SFT → GSPO-DrC 5.000 passos →
      quantização + smoke → **canário**.
- [ ] **[E]** **FP8 é o padrão de treino** (94,8 TFLOPS; QLoRA-8B a 668 tok/s); BF16 real da 5060 Ti é
      **47,4 TFLOPS**, não ~200.
- [ ] **[E]** **Quarentena de 30 dias antes de tocar peso**; knowledge editing **proibido** em produção.
- [ ] **[E]** As 916 linhas novas de embedding viram `nn.Parameter` separado (3,75 M) para o Adam não
      alocar estado da matriz inteira.
**Goal:** *"Objetivo F3.O4. Leia `CANON-v4.1.md` §4 (Treino) e §14, `F04-hardware-exato.md` §4.1 e §4.2 e
`research/D05-aprendizado-continuo.md`. Pronto quando o canário servir 500 chamadas pagas sem
incidente e os cinco portões rodarem no artefato quantizado."*

---

### FASE F4 — DIREITO COMO CÓDIGO NO AR (eixo central, 0 GPU)

O Brasil tem deficiência em tecnologia jurídica e é aqui que ela é preenchida: **4.626 linhas (C03) +
14.944 (F05) em Go, zero dependência externa, 50 ms, 0 GPU**, `big.Rat` nunca float, intervalo
nominal e estrito em vez de número único.

#### F4.O1 — Os 34 motores no MCP com executor real

**Pronto:** `go run ./cmd/wjmcp -chamar wj_itcmd -entrada '…'` responde pelo motor real; o catálogo sobe
de **14 `implemented` para ≥ 34**; `go test ./wj/calc/...` verde; nenhum stub devolve número.
**Insumos:** `F05-code/` (10 motores + `mcp/{mcp.go,catalogo.go}` + `cmd/wjmcp`, contratos **gerados
rodando o motor**) · `C03-code/` (4 motores) · `F02-code/go/doutrina/` (algoritmos prontos, dispatcher
ausente) · `F03-code/scripts/` · `F07-code/fresh/`. **Entregáveis:** `wj/calc/`,
`wj/mcp/adapters/{calc,grafo,retrieve,jurimetria}.go`. **Depende:** F0.O6, F0.O7, F1.O1.
**Recurso:** CPU, 0 GPU. **Dono:** nenhuma.
- [ ] **[I]** Preservar a ligação F05 → C03/D10 por `replace`: é o único ponto do repositório onde dois
      protótipos de fases diferentes já se integram de fato.
- [ ] **[E]** Adaptadores que faltam: F02 (5 tools com algoritmo, sem dispatcher), F03 (5 com dados
      carregados, só spec), F07 (10 com schema validado, sem execução).
- [ ] **[E]** Fronteira de classe de token: `wj/calc` ⊬ `wj/serve` no CI. **Todo dígito sai de Go**; o
      LLM é gramaticalmente impedido de emitir número.
**Goal:** *"Objetivo F4.O1. Leia `F05-direito-como-codigo-II.md` §§2–4, `INVENTARIO-CODIGO.md` §3 e o código
de `research-v4/F05-code/mcp/` e `research/C03-code/`. Pronto quando o catálogo tiver pelo menos
34 ferramentas implementadas e o CI provar que `wj/calc` não importa `wj/serve`."*

#### F4.O2 — `wjlint` (WJ-LIT-1) como portão de CI

**Pronto:** `go run ./cmd/wjlint ./wj/calc/...` → **0 violações**; motor sem diretiva de âncora
normativa, sem fonte oficial ou sem caso de teste derivado do texto **falha o merge**;
`go test ./wj/calc -run TestAncorasGeradas` → âncoras regeneradas batem byte a byte.
**Insumos:** `F05-direito-como-codigo-II.md` §1 (convenção WJ-LIT-1, o linter, WJ-CANON-1 em três
dialetos) · `F05-code/DOC-LITERATE.md` · `F05-code/*/ancoras_gerado.go` · `F05-code/literate/`.
**Entregáveis:** `cmd/wjlint`, `wj/calc/literate/`. **Depende:** F4.O1. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[I]** Mover o linter e as diretivas; regenerar `ancoras_gerado.go` de fonte oficial.
- [ ] **[E]** Runtime: **a lei muda e a ferramenta se desarma sozinha** — âncora que não resolve na
      data da consulta devolve `Instavel` + revisão, nunca número.
- [ ] **[E]** Fuzzing nativo (`go test -fuzz`) sobre os motores de datas, para as bordas que 8.440
      casos aleatórios não alcançam.
**Goal:** *"Objetivo F4.O2. Leia `F05-direito-como-codigo-II.md` §1 inteiro e
`research-v4/F05-code/DOC-LITERATE.md`. Pronto quando `wjlint` devolver zero violações em
`wj/calc` e a regeneração bater byte a byte."*

#### F4.O3 — Séries oficiais com backoff (e `wj_correcao` sai de stub)

**Pronto:** `go test ./wj/calc/indice -run TestSeriesOficiais` → todas as séries SGS resolvem com a
série **correta** (TR = **SGS 7811**, não 226 — defeito medido pelo F05); fonte indisponível ⇒
**fail-closed** (`Instavel`), nunca valor estimado; `wj_correcao` passa de `stub` a `implemented` com
`impl_ref` real. **Insumos:** `FIX-A.md` ("O que NÃO fechou", item 2) ·
`F05-direito-como-codigo-II.md` §7 e §9 (URLs oficiais das séries SGS) · `C03-code/indice/indice.go` ·
`F05-code/trabalhista/correcao.go`. **Entregáveis:** `wj/calc/indice/`, `wj/mlops/harvest/series/`.
**Depende:** F4.O1, F2.O1. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[E]** Adaptador de séries com backoff exponencial, cache com `checked_at` e proveniência por
      série; índice ausente ⇒ intervalo `Incerto`, nunca extrapolação.
- [ ] **[E]** Fechar os itens `[NÃO VERIFICADO]` do F05 §7 que dependem de HTTP — os 48 enunciados do
      TST entram pelo **backend de jurisprudência** (que responde), não pelo portal HTML (202 anti-bot).
**Goal:** *"Objetivo F4.O3. Leia `F05-direito-como-codigo-II.md` §5, §7 e §9 e a seção 'O que NÃO fechou' de
`research-v4/FIX-A.md`. Índice ausente é fail-closed. Pronto quando `wj_correcao` sair de stub
no catálogo com `impl_ref` real e o teste de séries passar."*

---

### FASE F5 — PREMEDITAÇÃO (a % de êxito já vem na resposta)

Produto central do dono: a resposta **já vem** com a chance de êxito/perda em porcentagem e banda de
confiança, de decisões reais. Nunca "prever o futuro": é sobrevivência sobre o fluxo TPU.
**Recurso: CPU (LightGBM + `leaves`); GPU só no extrator 4B.**

#### F5.O1 — Harvest DataJud, case-cohort e anti-vazamento como invariante

**Pronto:** ~180 M linhas (59 M processos × ~24 meses, case-cohort 1:4 Horvitz–Thompson, 28 bins
trimestrais); `go test ./wj/jurimetria -run TestFeatureSpec` falha se `LeakClass == 2` ou
`eval(AvailableAt) > t_corte`; 4 modelos Δ ∈ {0, 30, 90, 180} treinados.
**Insumos:** `CANON-v4.1` §12 · `research/C04-jurimetria.md` · `G01-code/go/prog/prog.go`.
**Entregáveis:** `wj/jurimetria/{features,cohort}/`. **Depende:** F2.O2. **Recurso:** CPU, 0 GPU.
**Dono:** nenhuma.
- [ ] **[E]** 14 campos do DataJud, **sem** valor da causa, partes, advogado, juiz ou texto do fato.
- [ ] **[E]** `FeatureSpec{Name, Source, AvailableAt, LeakClass}` como **tipo**, não convenção.
- [ ] **[E]** Backtest **walk-forward** (origem 2016, passo 6 m, 18 dobras), índice de vizinhos
      reconstruído por dobra com `as_of = T`. **CV aleatório é proibido.**
**Goal:** *"Objetivo F5.O1. Leia `CANON-v4.1.md` §12, `research/C04-jurimetria.md` e `G01-enaeval-arena.md`
§2. Pronto quando as ~180 M linhas existirem, o CI recusar qualquer feature de `LeakClass 2` e
os 4 modelos de defasagem estiverem treinados."*

#### F5.O2 — Hazard LightGBM servido em Go, conformal Mondrian e `prog_gate`

**Pronto:** `Σ_k F_k(M) + S(M) = 1.000000000000`; **≥ 1 célula publicável** com cobertura 90 d ∈
[0,88; 0,93], `LB95(skill) > 0`, `n_coorte_90d ≥ 100`, `R ≥ 0,15`, ECE-15 ≤ 0,05; paridade
`leaves` × Python em 10 k objetos no CI; ausência canônica nas demais células.
**Insumos:** `G01-code/go/prog/prog.go` (o `StubScorer` tem **a assinatura exata** de
`leaves.Ensemble.PredictSingle`) · `G01-enaeval-arena.md` §2.4 (as 7 condições de `G-PROG`) ·
`SCHEMA-v4.1.sql` (`prog_gate`). **Entregáveis:** `wj/jurimetria/{hazard,conformal,gate}/`.
**Depende:** F5.O1. **Recurso:** CPU (1,4 ms/curva, zero GPU). **Dono:** nenhuma.
- [ ] **[A]** Trocar `StubScorer` por `leaves` real — o stub era gerador determinístico, não modelo.
- [ ] **[E]** Conformal **Mondrian por célula** κ = (tribunal, classe_L2, assunto_L2, ano),
      `n_cal ≥ 200`, backoff `ltree` ≤ 3, ACI com γ = 0,01 sob deriva. **Cobertura marginal nacional
      é inútil**: 90% médio pode ser 99% no cível e 55% no trabalhista.
- [ ] **[E]** `k-anon n ≥ 50` por Cedar P18; **zero `judge_id`**; distribuição do foro, **nunca
      ranking de vara** (Res. CNJ 615/2025 art. 10; anexo BR3, baixo risco).
**Goal:** *"Objetivo F5.O2. Leia `G01-enaeval-arena.md` §2 (composição, prova de não-vazamento e as sete
condições de G-PROG) e `CANON-v4.1.md` §12. Pronto quando a identidade de riscos fechar em 1,0,
ao menos uma célula for publicável e a paridade `leaves` × Python passar em 10 mil objetos."*

#### F5.O3 — Bloco `[P#]` no GP/1, `wj_predict_case` e recibo recomputável

**Pronto:** bloco `[P#]` em **≤ 300 tokens** (medido: 262); `skill_vs_baserate` **obrigatório** no
contrato; terceiro recompõe `p_bruto` de `model_sha256 + calib + vetor`; contador estritamente
crescente **por endpoint** (`UNIQUE (endpoint, counter)`) — previsão reservada e publicada depois do
desfecho é **inexprimível**. **Insumos:** `G01-code/{go/prog/gp1.go,schemas/prognosis-block.schema.json}`
· `CANON-v4.1` §12 · `SCHEMA-v4.1.sql` (`prediction_receipt`, `pred_kind`).
**Entregáveis:** `wj/api/gp1/pblock.go`, `wj/mcp/adapters/jurimetria.go`. **Depende:** F5.O2, F0.O4.
**Recurso:** GPU 3.480/dia em regime (extrator 4B × 11.600 chamadas). **Dono:** nenhuma.
- [ ] **[I]** Gramática de saída do extrator com enums + acordo ONNX: a única saída livre é o enum
      errado, coberto por `EXTRACAO_INSUFICIENTE`.
- [ ] **[E]** Portão não passou ⇒ **`base_rate_only`** ou ausência canônica; nunca número solto, nunca
      "você vai ganhar" — sempre com banda e taxa-base (Res. CNJ 615/2025).
- [ ] **[E]** `/simulate` é **Tier Edge**: MOMDP, sufixo de ordem 3, MCTS 20.000 sims ≈ 12 ms em
      1 núcleo, 0 GPU; três classes contrafactuais com rótulo e `worst_case_cf_error`.
**Goal:** *"Objetivo F5.O3. Leia `G01-enaeval-arena.md` §§1 e 6, `CANON-v4.1.md` §12 e os artefatos de
`G01-code/schemas/`. Pronto quando o bloco couber em 300 tokens e o banco recusar previsão
reservada e publicada depois do desfecho."*

---

### FASE F6 — REDE SOCIAL VIVA E ARENA (um produto, dois perfis de custo)

**Obrigatória e vale ouro** (dono): a API já recebe ~10.000 requisições e **não tem conteúdo**.
Correção do H01: *uma thread S1/S2/S3 **é** uma rodada de arena* — **um** objeto `debate`, perfil
`leve` (18,29 GPU-s) ou `arena` (41,0; 46,9 com parecer do MP).

#### F6.O1 — Motor de semeadura e semente fria S0

**Pronto:** `/s/feed` com **≥ 2.000 threads, ≥ 90 digests diários, ≥ 500 forecasts abertos, ≥ 30
mercados resolvidos**, leaderboard com as 4 personas. Custo: **36.571 GPU-s ≈ 0,46 GPU-dia de máquina**.
**Insumos:** `G02-rede-social-viva.md` §1.5 e "Fases por objetivo" · `G02-code/{seed.go,fixtures/}`.
**Entregáveis:** `wj/agent/social/seed/`. **Depende:** F3.O4, F2.O3. **Recurso:** GPU, perfil
construção (semeadura a 25% = 150 debates/dia). **Dono:** nenhuma.
- [ ] **[I]** Pré-condição dura: caso **sem claim** nunca vira thread (`gap_queue` antes da seleção) —
      o protótipo queimava GPU gerando thread de 0 posts.
- [ ] **[E]** Seletor com **mochila B lida de `shadow_price`** (λ_gpu[classe][hora]), nunca constante:
      passando de 25 GPU-s medidos, o volume cai sozinho para a faixa 230–510/dia.
- [ ] **[E]** Submercados de horizonte **≤ 24 h** obrigatórios — sem forecast curto nenhum agente
      acumula reputação.
**Goal:** *"Objetivo F6.O1. Leia `G02-rede-social-viva.md` §1.5 e a tabela de fases, `CANON-v4.1.md` §12 e o
código de `research-v4/G02-code/`. Pronto quando `/s/feed` tiver 2.000 threads, 90 digests, 500
forecasts abertos e 30 mercados resolvidos."*

#### F6.O2 — Debate unificado: 4 personas, V⁴ em todo segmento, selo com escopo

**Pronto:** `go test ./wj/agent/social` → **11 testes** (`TestTextoLivreViraOpiniaoENaoEntraNoPass`,
`TestQuatroPubkeysDePersona`, `TestGateNaoSobeSemCalibracao`); `validar.py` → **14/14 adversariais
recusados**; **0 posts assinados com segmento não verificado**; `PubkeysDistintas() == 4`.
**Insumos:** `G02-code/{verify.go,model.go,personas.go,social-schemas.json}` (**já corrigidos pela
FIX-A**: `text` 1.200 → **280** chars, `scope`, `calib_id`, `unverified_segments`) ·
`G01-code/go/arena/` (máquina de estados, LMSR, V⁴, predicado do MP) · `CANON-v4.1` §0 e §12.
**Entregáveis:** `wj/agent/{social,arena}/`. **Depende:** F3.O2, F6.O1. **Recurso:** GPU. **Dono:** nenhuma.
- [ ] **[I]** 4 personas / 4 pubkeys; advogado autor e réu **com a mesma chave** (lado é coluna do
      lance). O 5º DID `agent:adversario` está revogado.
- [ ] **[E]** Todo `text` com verbo assertivo sobre direito exige `entail(claims ∪ gloss ⊢ text) ≥ τ`
      **ou** vira `opinion` com `basis`, e o índice entra em `unverified_segments`.
- [ ] **[E]** `wj-aulint` R1–R11: nenhum parágrafo assertivo fora de `<section data-claim>`.
- [ ] **[E]** Case Brief nunca vira decisão real: `Legal-Value: unofficial`, JSON-LD `wj:legalValue`,
      SimDecision **sem** `data-urn` e fora do `x-wj-claims`, com `Content-Signal: ai-train=no`;
      recibo com URN de `/u/arena/` é **recusado**.
**Goal:** *"Objetivo F6.O2. Leia `CANON-v4.1.md` §12, `research-v4/FIX-A.md` §5, `H01-critico-fable.md` §3
(G12 e 'Case Brief citado como decisão real') e o código de `G02-code/` e `G01-code/go/arena/`.
Pronto quando os 11 testes e os 14 ataques passarem e um recibo apontando URL de arena for
recusado."*

#### F6.O3 — API viva: contrato de payload, feed e Nostr

**Pronto:** as ~10.000 requisições/mês passam a receber conteúdo; uma IA externa fecha **enroll →
forecast → post → score em ≤ 10 chamadas** sem humano; **≥ 1 mercado resolvido em ≤ 24 h** por agente
novo; relay com NIP-11 no ar e ≥ 1 agente Nostr externo lendo por `#u`.
**Insumos:** `G02-rede-social-viva.md` (fases S1–S4; o contrato de payload é **entrega obrigatória**) ·
`G02-code/{server.go,feed.go}` · `CANON-v4.1` §12 (feeds MCP; Nostr 30411/30412/30413).
**Entregáveis:** `wj/api/social/`, `wj/mcp/resources.go`, `wj/edge/feed.go`. **Depende:** F6.O2, F1.O1.
**Recurso:** CPU + edge. **Dono:** nenhuma.
- [ ] **[E]** **MeritRank**: EigenTrust com teleporte só a pré-confiáveis (a = 0,15),
      `w_ij = min(√v_ij, κ·R(i))` — **reputação ANTES da raiz quadrada** (a √ ingênua amplifica Sybil
      31,6× em k = 1.000); **α = 0,40, β = 0,60** (0,30/0,50 dão amp = 1,167: ataque lucrativo).
- [ ] **[E]** `bond_rep = max(R$ 250, 49·R(i)·V_dia)`; slashing confisca 100%; **WJR intransferível**.
- [ ] **[I]** Assinatura Nostr real só depois de F0.O1; até lá o teste bloqueia exportação.
**Goal:** *"Objetivo F6.O3. Leia `G02-rede-social-viva.md` (fases S1 a S4 e o contrato de payload) e
`CANON-v4.1.md` §12. Pronto quando uma IA externa completar o ciclo em até 10 chamadas sem
humano e resolver ao menos um mercado em 24 h."*

#### F6.O4 — Dinheiro com cadeia evidencial: resolução por captura, payout só por Plano-T

**Pronto:** ataques **N1–N10 → 9 recusas + 1 caminho feliz**; toda `resolution` tem `oracle_receipt`
**NOT NULL** com FK composta para `capture` (fonte `datajud`, `level ≥ C1`, K1 não despejada,
`norm_ok`); `winner` **derivado** de `tpu_outcome`; `payout.brl ≤ market.b` por FK composta;
`payout_batch.frost_sig` FROST 2-de-3; `frost_kid = 'example'` **recusado pelo banco**.
**Insumos:** `FIX-B.md` §2 (G11) e §3 · `SCHEMA-v4.1.sql` · `G02-code/score.go` (o `Resolve` que
aceitava `winner` como parâmetro). **Entregáveis:** `wj/econ/tesouraria/payout.go`,
`wj/agent/arena/resolve.go`. **Depende:** F0.O5, F6.O2. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[A]** `Resolve` perde `winner` e `tpuCode`: o desfecho vem da tabela.
- [ ] **[E]** Plano-T como **processo separado**, sem LLM, sem egresso de leitura, sem `net/http`
      genérico (cliente x402 dedicado com allowlist compilada); **dead-man invertido 180 s**.
- [ ] **[E]** Payoff **∈ [0, b_q]**, nunca negativo (Lei 14.790/2023 art. 3º; DL 3.688/41 art. 50 §3º);
      elegível = LB95% do log-score > 0 em ≥ 50 resoluções.
**Goal:** *"Objetivo F6.O4. Leia D-13 item 3, `H01-critico-fable.md` §6 (G11), `FIX-B.md` §2 e §3 e o
`score.go` de `G02-code/`. Pronto quando os ataques N1 a N10 devolverem nove recusas e um
caminho feliz."*

---

### FASE F7 — DOUTRINA E O RESTO DAS FONTES (G03 C–F)

#### F7.O1 — Doutrina verificável (F02): corrente, trecho citável, licença pela origem

**Pronto:** `doutrina_ataques.sql` → **32/32 (25 recusados + 7 aceitos)**; `go test ./wj/grafo/doutrina`
→ **9/9**; Cedar `WJ::Autoral` → **39/39 vetores conformes, 0 erro em modo estrito**;
`rotulo = 'majoritaria'` com `p_maioria_milli < 900` **inexprimível**.
**Insumos:** `F02-code/{go/doutrina,sql/doutrina.sql,cedar/autoral.cedar}` · `F02-doutrina.md` ·
`CANON-v4.1` §9. **Entregáveis:** `wj/grafo/doutrina/`, `wj/policy/autoral/`. **Depende:** F2.O6, F4.O1.
**Recurso:** backlog **545.000 GPU-s ≈ 6,3 GPU-dias de máquina**; regime 580/dia.
**Dono:** item 4 de §0.5 (20 textos de `WJ::Autoral`).
- [ ] **[I]** Trecho ≤ **300 chars** (85,4% das citações reais cabem; p50 = 191) + anti-mosaico
      (≥ 2.000 chars entre trechos da mesma edição) + cota ≤ 1% da obra (piso 2, teto 50).
- [ ] **[E]** Licença **da ORIGEM, nunca do agregador**: BDTD e OasisBR propagam **0/240** licenças CC.
- [ ] **[I]** Atribuição por **FK composta** — atribuir a autor alheio é inexprimível.
**Goal:** *"Objetivo F7.O1. Leia `CANON-v4.1.md` §9, `F02-doutrina.md` e o código de `F02-code/`. Pronto
quando os 32 ataques, os 9 testes Go e os 39 vetores Cedar passarem."*

#### F7.O2 — G03 fase C: administrativo e regulatório

**Pronto:** **≥ 90% dos normativos do BACEN com flag de vigência**; solução COSIT indexada por número;
sitemap do Plone mapeado (fim do "404 adivinhado"). **Insumos:** `G03-maximo-fontes.md` §1.2/§1.3 e §6
linha C. **Entregáveis:** `wj/mlops/harvest/{cvm,bacen,rfb,cade,cgu,agu,confaz,agencias}/`.
**Depende:** F2.O1. **Recurso:** CPU ~180 k núcleo-s; GPU ~1.500. **Dono:** nenhuma.
- [ ] **[E]** CVM, BACEN, RFB, CADE, CGU, AGU/PGFN, CONFAZ e as 10 agências sob `WJ::Fonte`.
- [ ] **[E]** Todo adaptador entra com nível de captura declarado e `norm_ok`, sem exceção.
**Goal:** *"Objetivo F7.O2. Leia `G03-maximo-fontes.md` §§1.2, 1.3 e §6 linha C. Pronto quando 90% dos
normativos do BACEN tiverem flag de vigência, as soluções COSIT estiverem indexadas por número e
o sitemap do Plone estiver mapeado."*

#### F7.O3 — G03 fases D, E e F: doutrina aberta, estadual/municipal e internacional

**Pronto:** **≥ 14.479 registros de Direito** com licença classificada e **≥ 70% dos PDFs abertos com
texto em classe R1**; **≥ 80% de cobertura de leis estaduais consolidadas nas 10 maiores UFs**;
**EUR-Lex ≥ 145.280 atos REG** e **HUDOC ≥ 231.661 itens**.
**Insumos:** `G03-maximo-fontes.md` §1.4–§1.7 e §6 linhas D/E/F · `CANON-v4.1` §5 (cascata de OCR).
**Entregáveis:** `wj/mlops/harvest/{oai,bdtd,scielo,tse,tres,assembleias,doe,inlabs,eurlex,hudoc,dila}/`.
**Depende:** F7.O2. **Recurso:** GPU ~39.500 (**≈ 0,46 GPU-dia de máquina**, dominado pela cascata de
OCR da fase D); CPU ~650 k núcleo-s. **Dono:** nenhuma.
- [ ] **[E]** Cascata: estágio 0 **PDFium em Wasm/wazero** (PDF hostil em sandbox) → estágio 1 VLM leve
      (**só os pesos**, Apache-2.0) → estágio 2 escalada → estágio 3 fila humana.
- [ ] **[E]** A fase F é **bulk e barata** e é a de maior valor para IA estrangeira: entra por último
      em esforço, não em prioridade de valor.
**Goal:** *"Objetivo F7.O3. Leia `G03-maximo-fontes.md` §§1.4 a 1.7 e §6 linhas D, E e F, e `CANON-v4.1.md`
§5 (cascata de documento e OCR, com as licenças revogadas). Pronto quando houver 14.479
registros com licença classificada, 70% dos PDFs em classe R1, 80% de cobertura estadual nas 10
maiores UFs e EUR-Lex e HUDOC indexados."*

---

### FASE F8 — APRENDIZADO (o bot melhora sozinho, com portão)

#### F8.O1 — Registry, portões G1–G5 e promoção com rollback armado

**Pronto:** `bench_result` referencia **só** `quantized_artifact` (ligar bench a checkpoint BF16 é
irrepresentável); promoção exige os **5 portões daquele artefato sob o MESMO bundle Cedar** (TOCTOU
fechado por FK composta com `policy_set_version`); `component_registry` → **9/9 ataques recusados + 1
vínculo legítimo aceito**; TLC de `PromocaoModelo.tla` → 0 erros.
**Insumos:** `F11-code/{comp/,sql/component_registry.sql,bom/bom.json}` (**verificado ao vivo**) ·
`D10-code/tla/PromocaoModelo.tla` · `research/C05-mlops-plataforma.md` · `CANON-v4.1` §14.
**Entregáveis:** `wj/mlops/{registry,gates,promote}/`. **Depende:** F0.O7, F3.O4. **Recurso:** CPU.
**Dono:** nenhuma.
- [ ] **[I]** Manter o portão de soberania S1–S6 e a **quarentena de 30 dias** de cadeia de suprimentos.
- [ ] **[E]** Manifesto Parquet assinado no **mesmo** log Merkle dos recibos.
- [ ] **[E]** `Θ_frozen` inexprimível como config auto-ajustável (`hcr_max`, `asr_max`, `tau_nli`,
      `cap_spend`, `frost_k`, `deadman_s`, `panel_private`, `terminal_nodes`, `epsilon_floor`).
**Goal:** *"Objetivo F8.O1. Leia `CANON-v4.1.md` §14, `research/C05-mlops-plataforma.md` e o código de
`F11-code/comp/`, que já recusa 9 de 9 ataques ao vivo. Pronto quando os 9 ataques continuarem
recusados no monorepo e o TLC de `PromocaoModelo.tla` fechar sem erro."*

#### F8.O2 — WikiJurídica-Bench e WJ-Retro

**Pronto:** **2.700 itens, 8 trilhas + trilha 9 (negociação) + trilha 10 (contexto enganoso)**, 7
programáticas, no CI; **HCR ≤ 2%, ASR = 0**; `N_real = 1,07 × N_Connor`; BCa clusterizado;
**canário ≤ 5%**; **eco literal ≤ 5%**; WJ-Retro auto-alimentado com 360 itens e custo humano zero.
**Insumos:** `research/A06-wikijuridica-bench.md` · `G05-radar-cientifico.md` §9 itens 1, 4 e 8 ·
`CANON-v4.1` §14. **Entregáveis:** `wj/mlops/bench/`. **Depende:** F8.O1, F3.O2.
**Recurso:** GPU 27.000 GPU-s. **Dono:** item 6 de §0.5 (9 gabaritos).
- [ ] **[E]** Trilha 10: editar passagem de ouro para sustentar a resposta errada, inseri-la entre as
      recuperadas, medir eco literal e aplicar a defesa contrafactual. **Entra em G1 antes da geração
      em massa.**
- [ ] **[E]** Trilha de segurança com **ataque adaptativo**: ASR = 0 nas ações de severidade máxima,
      com utilidade benigna ≥ a do confinamento binário.
- [ ] **[E]** Canário semântico só no **split privado**.
**Goal:** *"Objetivo F8.O2. Leia `research/A06-wikijuridica-bench.md`, `CANON-v4.1.md` §14 e
`G05-radar-cientifico.md` §9 (itens 1, 4 e 8). Pronto quando HCR ficar em 2%, ASR em zero sob
ataque adaptativo, canário em 5% e eco literal em 5%. Peça ao dono só os 9 gabaritos."*

#### F8.O3 — OPD → portão G5 → RLVR GSPO-DrC, com Scale-QLoRA

**Pronto:** as duas etapas rodam **sequencialmente**, com **portão G5/WJ-Retro obrigatório entre elas**
(arXiv:2608.14610: RL geral **piora** raciocínio temporal, e vigência é o produto); merge sobre NVFP4
por **Scale-QLoRA** é **bit-exato e sem perda** (merge ingênuo perde até 39 pp); mistura 55/25/15/5
com replay retemporalizado de 25%. **Insumos:** `CANON-v4.1` §4 · D-4 · `G05-radar-cientifico.md` §9
itens 5, 7 e 9 · `research/D05-aprendizado-continuo.md`. **Entregáveis:** `wj/mlops/train/{opd,rlvr,merge}/`.
**Depende:** F8.O1, F8.O2. **Recurso:** folga residual em regime (**9.415 GPU-s/dia**). **Dono:** nenhuma.
- [ ] **[E]** OPD com IER a 0,1–1%; **GrowMTP fica como experimento** (F10.O4), nunca na promoção.
- [ ] **[E]** **S-LoRA + roteador discreto**; X-LoRA morto (+0,015 nats, p = 0,19).
- [ ] **[E]** Adaptador por ramo com **morte por vigência**: purgar vira troca de escala, não requantização.
**Goal:** *"Objetivo F8.O3. Leia D-4, `CANON-v4.1.md` §4 (Treino) e `G05-radar-cientifico.md` §9 (itens 5, 7
e 9). Pronto quando o merge for bit-exato, o portão temporal bloquear qualquer regressão de
vigência e a receita couber na folga residual."*

#### F8.O4 — Compactação: aluno 4B, units, auto-jogo, embeddings da cauda

**Pronto:** aluno 4B passa **G1–G5 no artefato quantizado** com não-inferioridade a 3 pp;
**≥ 2.000 units/GPU-dia**; custo por citação verificada **≤ US$ 0,001**; economia medida de
**11.619 GPU-s/dia**, payback de **48 dias-de-compute**. **Insumos:** `F04-hardware-exato.md` §4.1,
§4.2 e §4.4 (a régua R5' é fila de compactação por payback em GPU-s) · `CANON-v4.1` §4 e §15.
**Entregáveis:** `wj/mlops/train/aluno4b/`, `cmd/wjunits` em lote. **Depende:** F8.O3.
**Recurso:** **19,1 GPU-dias de máquina** (do canário ao fim do backlog). **Dono:** nenhuma.
- [ ] **[E]** Ordem por payback em GPU-s: aluno 4B (48) → encoder de 6 camadas (31×) → esqueleto
      determinístico das units (investimento zero) → REAP-64 (retorno é SLO, não GPU-s).
- [ ] **[E]** Auto-jogo com **o modelo do mundo como árbitro**; o LLM só redige (`sim/core ⊬ sim/llm`).
**Goal:** *"Objetivo F8.O4. Leia `F04-hardware-exato.md` §4.1, §4.2 e §4.4 e `CANON-v4.1.md` §4 e §15.
Pronto quando o 4B passar os cinco portões no artefato quantizado com não-inferioridade de 3 pp
e a casa produzir 2.000 units por GPU-dia."*

---

### FASE F9 — CONFIANÇA E PADRÃO (a casa vira referência, não fornecedor)

#### F9.O1 — Drafts IETF, conformance e testemunhas com quórum

**Pronto:** 3 I-Ds no datatracker (`draft-toledo-scitt-legal-citation-receipts-00`,
`draft-toledo-scitt-forecast-receipts-00`, `draft-toledo-httpapi-legal-time-00`);
`go test ./lib/lar-conformance` verde; **N = 5 testemunhas, k = 4** (3 de 5 ⇒ `publicavel = false`;
4 de 5 ⇒ `true`, imposto pelo schema); notebook como 2ª testemunha em AS distinto + réplica quente do
Postgres; **bounty de equivocação R$ 5.000** publicado.
**Insumos:** `research/E01-drafts/` · `CANON-v4.1` §8 (Testemunhas). **Entregáveis:** `docs/ietf/`,
`lib/lar-go/`, `wj/mlops/witness/`. **Depende:** F0.O1, F0.O4. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[E]** "VPS em terceiro AS" como testemunha está **revogado** (é nuvem). Testemunhas: notebook,
      parceiros, agente externo que rode `lar-go`, relay Nostr.
**Goal:** *"Objetivo F9.O1. Leia `research/E01-drafts/` e `CANON-v4.1.md` §8 (Testemunhas e quórum). Pronto
quando um checkpoint com 3 de 5 for marcado não publicável e com 4 de 5 for publicável."*

#### F9.O2 — Programa por canal e ciência publicável

**Pronto:** o efeito de cada mudança de superfície é estimado por canal com IC que não cruza zero;
entropia condicional do processo brasileiro publicada (**H(k=3) = 1,326 bit/macro-evento**; k=4 só
+1,0%); ≥ 1 artigo submetido com dados e código reproduzíveis.
**Insumos:** `CANON-v4.1` §8 (D8) e §15 · `research/{E06-ciencia-publicavel.md,D06-world-model.md}`.
**Entregáveis:** `docs/ciencia/`, `wj/mlops/radar/canal.go`. **Depende:** F1.O5, F8.O2.
**Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[E]** Transformer do world model **proibido** até bater 1,326 bit no holdout BCa; até lá, VOMM
      de ordem 3 com backoff Jelinek–Mercer (α = 0,4).
- [ ] **[E]** O CI quebra se um estado absorvente sumir do coarsening κ: TPU → E.
**Goal:** *"Objetivo F9.O2. Leia `CANON-v4.1.md` §8 e §15, `research/D06-world-model.md` e
`research/E06-ciencia-publicavel.md`. O transformer do world model continua proibido até que o
VOMM de ordem 3 seja batido no holdout com BCa."*

---

### FASE F10 — EXPERIMENTOS (candidatos com portão, nunca no caminho crítico)

Regra da fase: **cada experimento é adotado por portão medido ou arquivado com o log.** Nenhum entra
no caminho de promoção enquanto for experimento. Custo somado: **≈ 2,0 GPU-dias de máquina** na folga.

#### F10.O1 — E1: Qwen3.5 como candidato de promoção (três portões)

**Pronto:** os **três portões** passam ou o experimento é arquivado: (1) **Tail-Replay** ou equivalente
mantendo **TTFT p95 < 500 ms** com cache quente em vLLM ≥ 0.30 em sm_120; (2) QLoRA/FP8 e W4A4 NVFP4
no híbrido com **KL de calibração jurídica ≤ a do 8B denso**; (3) **não-inferioridade G2** no bench
**+ G1 no artefato quantizado**. **Insumos:** D-1 · `CANON-v4.1` §4 (Experimento E1) ·
`G05-radar-cientifico.md` §9. **Entregáveis:** `wj/mlops/exp/e1/`. **Depende:** F8.O1.
**Recurso:** GPU na folga residual. **Dono:** nenhuma.
- [ ] **[E]** **Tail-Replay primeiro, modelo depois** — prefix caching é condição de viabilidade e não
      se aplica ao estado recorrente GDN sem ele.
- [ ] **[E]** Se passar, substitui o residente e o KV liberado (4,5× menor por token) vai para concorrência.
**Goal:** *"Objetivo F10.O1. Leia D-1 e `CANON-v4.1.md` §4 (Experimento E1). O EnaEval permanece em Qwen3-8B
denso enquanto qualquer portão estiver aberto."*

#### F10.O2 — BOSCH: plugin vLLM de sala limpa, como fase com portão

**Pronto:** plugin fora-da-árvore (~40 linhas, sala limpa) sobe com `layer_types` misto sem abortar o
`Qwen2Model`; ganho medido **1,71× em 8k e 5,19× em 128k**; portão: **G1 igual ao denso + TTFT p95 <
500 ms**. **Insumos:** `CANON-v4.1` §4 (Contexto) · `H01-critico-fable.md` §2 (G16).
**Entregáveis:** `ops/vllm/plugins/bosch/`. **Depende:** F3.O1. **Recurso:** GPU. **Dono:** nenhuma.
- [ ] **[E]** O canário **não** depende disto: KV 5,00 GiB = 124.830 tokens já é o número sem BOSCH.
**Goal:** *"Objetivo F10.O2. Leia `CANON-v4.1.md` §4 (Contexto) e `H01-critico-fable.md` §2 (G16). Pronto
quando o ganho de 1,71× em 8k e 5,19× em 128k for reproduzido sem regressão no bench."*

#### F10.O3 — mLateOn contra o `wj-late` próprio

**Pronto:** comparação nos 5 datasets do JUÁ + NormasTCU + Quati (nDCG@10, MAP@10, MRR@10, latência,
tamanho de índice); portão: **mLateOn ≥ `wj-late` em nDCG@10 e ≤ 1,5× no índice**. Se passar, o BOM
perde um componente próprio e o mmBERT serve 4 cabeças. **Insumos:** `G05-radar-cientifico.md` §9
item 6 · `F11-bot-soberano.md` (`wj-late`: resíduo de 2 bits, 58 GB no NVMe).
**Entregáveis:** `wj/mlops/exp/mlateon/`. **Depende:** F2.O6, F8.O2. **Recurso:** GPU leve. **Dono:** nenhuma.
- [ ] **[E]** Portão decide por medição; empate mantém o componente próprio (soberania).
**Goal:** *"Objetivo F10.O3. Leia `G05-radar-cientifico.md` §9 item 6 e a seção do `wj-late` em
`F11-bot-soberano.md`."*

#### F10.O4 — GrowMTP e currículo model-aware

**Pronto:** ablação com portão `ΔJ > 0` sob **LB95 BCa clusterizado**; a concisão se justifica por
medição ou **cai** da recompensa. **Insumos:** `G05-radar-cientifico.md` §9 itens 5 e 7 ·
`research/D03-algoritmo-vivo.md`. **Entregáveis:** `wj/mlops/exp/growmtp/`. **Depende:** F8.O3.
**Recurso:** GPU na folga residual. **Dono:** nenhuma.
- [ ] **[E]** Troca do limiar fixo `p̂ ∈ [0,20; 0,70]` pela dificuldade derivada da recompensa;
      recompensa como cadeia com portão (URN → NLI → formato → concisão).
**Goal:** *"Objetivo F10.O4. Leia `G05-radar-cientifico.md` §9 itens 5 e 7 e
`research/D03-algoritmo-vivo.md`. Pronto quando a decisão estiver tomada por medição: adota, ou
arquiva com o log."*

---

### FASE F11 — REGIME (o sistema passa a se governar)

#### F11.O1 — Transição `construcao` → `regime` (critério: backlog = 0)

**Pronto:** `SELECT backlog_gpu_s FROM v_orcamento_gpu` → **0**; o escalonador troca de perfil
**sozinho**; regime medido bate com `orcamento_v4.py`: **36.185 GPU-s/dia = 79,4% da folga, sobra
9.415**; CPU em **19,7%**; RAM nova inteira no envelope rotativo (**45,5%**, maior locatário 18,5%);
NVMe em **1.847,3 GiB = 51,2% do útil**, poda λ_disco só a 82%.
**Insumos:** `CANON-v4.1` §3 · `orcamento/orcamento_v4.py` · `G03-code/armazenamento/plano.py` ·
`F04-code/orcamento32.py`. **Entregáveis:** `wj/serve/perfil.go`, `wj/econ/backlog.go`.
**Depende:** F3.O3, F8.O4. **Recurso:** —. **Dono:** nenhuma.
- [ ] **[E]** A transição é **objetivo com critério de pronto**, nunca data: o backlog de 3.052.330
      GPU-s zera em **38,1 GPU-dias de máquina** em construção, contra 324,2 em regime.
- [ ] **[E]** Regra permanente: **nenhum relatório declara RAM sem linha no `orcamento32.py`**.
- [ ] **[E]** Poda do NVMe: WARC de diário municipal → PDF de tese acadêmica; **K1 nunca é despejado**
      — a FK do recibo congela o K1.
**Goal:** *"Objetivo F11.O1. Leia `CANON-v4.1.md` §3 e rode `orcamento/orcamento_v4.py` e
`G03-code/armazenamento/plano.py`. A transição é objetivo com critério de pronto, nunca data."*

#### F11.O2 — Autonomia L0 → L3 com Θ_frozen e três planos físicos

**Pronto:** `LB95 Wilson ≥ 0,975` sustentado por **30 ciclos diários consecutivos**; tesouraria com
teto **L3 permanente**; **FROST 2-de-3 acima de R$ 2,50**; **dead-man invertido 180 s** (queda ⇒
fail-closed); painel selado com cota auditável na árvore Merkle; **0 violações de H1–H5**.
**Insumos:** `CANON-v4.1` §14 · `research/B04-seguranca-agente.md` · `research/B02-tesouraria-autonoma.md`
· `research/D10-code/`. **Entregáveis:** `wj/econ/tesouraria/`, `wj/agent/autonomia.go`.
**Depende:** F6.O4, F8.O1. **Recurso:** CPU. **Dono:** nenhuma.
- [ ] **[E]** Três planos como **três processos**, não três structs: D lê a internet e nunca emite
      intenção; C decide e só passa valores tipados por socket Unix; T tem a chave, sem LLM e sem egresso.
- [ ] **[E]** `CapSpend` nunca readmitido na sessão; taint monotônico.
**Goal:** *"Objetivo F11.O2. Leia `CANON-v4.1.md` §14, `research/B04-seguranca-agente.md` e
`research/B02-tesouraria-autonoma.md`."*

#### F11.O3 — Console D08 com dado real e as fases de soberania SOB-1…SOB-4

**Pronto:** console nos 3 modos (HOJE / SEMANA / INCIDENTE SEV1–4) com dado real e **zero mudança de
layout** (troca do array `KPIS`); destrutivo exige confirmação **digitada**; a fala do dono entra como
**dado não confiável** até virar `IntentCandidate` tipado; **índice de soberania sai de 0,39 (SOB-0)
e chega a 0,87 ao fechar SOB-4**. **Insumos:** `research/D08-console/index.html` (mockup de 1.040 l) ·
`research/D08-console-operacao.md` · `F11-bot-soberano.md` (tabela SOB-0…SOB-4 com critério binário).
**Entregáveis:** `wj/console/`, `wj/mlops/soberania/`. **Depende:** F11.O1, F11.O2.
**Recurso:** CPU; SOB-3 ≈ **4,2 GPU-dias de máquina em GPU cheia** (~7,6 na folga); SOB-4 ≈ **156
GPU-dias de folga em FP8**. **Dono:** nenhuma.
- [ ] **[A]** Console **PROPÕE**; quem assina é o daemon de política com o share do dono — console com
      a chave anula o FROST 2-de-3 (`wj/console` ⊬ `wj/econ/tesouraria` no CI).
- [ ] **[E]** SOB-1 tokenizer e verificador próprios · SOB-2 aluno 4B e `wj-rerank-54M` · SOB-3 encoder
      próprio L4 (CPT MLM de 20 B tokens) · SOB-4 CPT do 4B e do 8B e professor próprio. Cada uma com
      critério binário e custo em GPU-dias de máquina — **sem cronograma**.
**Goal:** *"Objetivo F11.O3. Leia `research/D08-console-operacao.md`, o mockup
`research/D08-console/index.html` e a tabela SOB-0 a SOB-4 de `F11-bot-soberano.md`. Pronto
quando o índice de soberania sair de 0,39 e o CI provar que o console não importa a tesouraria."*

---

## 4 · F0.O1 — PROMPT DE GOAL LITERAL PARA A PRIMEIRA SESSÃO (pronto para colar)

> **Objetivo: F0.O1 — K_root, `did:web` e diretório Web Bot Auth. Você é o engenheiro sênior do dono.**
>
> **Leia, nesta ordem:** `/home/claude/wikijuridica/CORRECOES-DONO.md` (inteiro);
> `research-v4/DECISOES-ORQUESTRADOR.md` (D-7, D-13, D-15 e o ADENDO);
> `research-v4/CANON-v4.1.md` §0, §5 (Protocolos) e §8 (C14, C15, C19, C20, C21, C26);
> `research-v4/H01-critico-fable.md` §3 (achado G17) e §6 (achado G13);
> `research-v4/FIX-A.md` §2 e §6; e o código de `research/B06-code/lar.go`,
> `research-v4/F06-code/` (o binário `wbaverify` e seu log) e
> `research-v4/G04-code/enaeval/{wba/wba.go,identity/}`.
>
> **Faça:** (1) gere a chave raiz Ed25519 da PJ emissora `did:web:wikijuridica.com.br` em host
> isolado, sem egresso; (2) divida-a por Shamir **3-de-5**, com teste provando que 3 shares
> reconstroem o mesmo sha256 e 2 não; (3) derive `K_op` e a chave do log por HKDF, com rotação como
> fase própria e `kid` novo; (4) publique `did.json`, o JWKS e
> `/.well-known/http-message-signatures-directory` **assinado**, no molde byte a byte do diretório do
> ChatGPT — hoje essa rota dá 404, e é por isso que a cota por DID é inexequível; (5) troque todo
> `kid` por thumbprint RFC 8037 em `G01-code/go/prog/prog.go`, `G02-code/feed.go` e
> `F01-code/build_examples.py`; (6) substitua ou bloqueie por teste todos os placeholders de
> assinatura (`EXEMPLO-`, `PROTOTIPO`, `<ed25519>`, `PENDENTE_K_ROOT`, `wj-2026-09`).
>
> **Pronto quando, e só quando:** `wbaverify https://wikijuridica.com.br` devolver `OK` da mesma forma
> que já valida o diretório do ChatGPT; `lar.Verify` aceitar um recibo **real** emitido pela casa;
> `grep -rn "PROTOTIPO\|<ed25519>\|PENDENTE_K_ROOT\|wj-2026-09\"" wj/` devolver **0**; e
> `go test ./ops/kroot -run TestReconstroi3de5` passar.
>
> **Regras desta sessão:** nada de compra, nuvem, GPU alugada ou serviço pago de terceiro. Não reabra
> número do dono. A **única** coisa que sobe para ele é onde guardou cada uma das 5 shares. Nada é
> "pronto" sem comando e saída colados no `LEDGER-CORRECOES.md`. Se algo não couber, a resposta é
> engenharia de alocação, nunca redução de escopo.

---

## 5 · TABELA DE FASES

**GPU-dia de máquina** = medida física de consumo, nunca prazo. `construcao` tem **80.165 GPU-s/dia
livres**; `regime`, **9.415**. Backlog de construção: **3.052.330 GPU-s ⇒ 38,1 GPU-dias de máquina**
em construção contra 324,2 em regime — é isso que fixa a ordem.

| Fase | Obj. | GPU-dias de máquina | CPU-dias de máquina | Recurso dominante | Critério de saída (binário) |
|---|---:|---:|---:|---|---|
| **F0** Fundações | 7 | ~0 | < 0,1 | CPU + edge | `wbaverify` valida a casa · `gen.py --check` 35/0 · 10/10 vetores v1.1 · 127 ataques · catálogo 53+13 · `depcheck` 25/0 |
| **F1** Superfície viva | 5 | ~0 | < 0,1 | CPU + edge | probe passa em `/mcp2` · cota sobrevive a restart · MCP-1…7 · `wjconsist` 80/0 · ≥ 95% dos hits classificados |
| **F2** Conhecimento | 7 | **≈ 0,8** | **≈ 3,5** | CPU pesada | TCU e CARF 100% `norm_ok` · 99% dos temas STJ · ≥ 95% das decisões em ≤ 48 h · `/norma` p95 ≤ 80 ms · 0 unit sem recibo |
| **F3** Motor | 4 | **≈ 8,9** | ~0,3 | GPU (construção) | KLD ≤ 10⁻³ · TTFT p95 < 500 ms · egresso 0 · UB95 ≤ 0,913% · HCR ≤ 2% · canário 500 chamadas sem SEV |
| **F4** Direito como código | 3 | ~0 | < 0,1 | CPU | ≥ 34 tools `implemented` · `wjlint` 0 violações · séries oficiais corretas com fail-closed |
| **F5** Premeditação | 3 | ~0 | **≈ 1,0** | CPU (`leaves`) | identidade de riscos = 1,0 · ≥ 1 célula publicável (cobertura ∈ [0,88; 0,93], skill LB95 > 0) · `[P#]` ≤ 300 tokens |
| **F6** Rede social + arena | 4 | **≈ 0,5** | < 0,1 | GPU leve | `/s/feed` ≥ 2.000 threads · 0 post com segmento não verificado · IA externa fecha o ciclo em ≤ 10 chamadas · N1–N10 |
| **F7** Doutrina + fontes C–F | 3 | **≈ 6,8** | **≈ 1,9** | GPU (OCR) + CPU | 32 ataques de doutrina · 39/39 vetores Cedar · 14.479 registros com licença · EUR-Lex e HUDOC indexados |
| **F8** Aprendizado | 4 | **≈ 19,1** | ~0,5 | GPU (construção) | 9/9 ataques de registry · ASR = 0 sob ataque adaptativo · merge Scale-QLoRA bit-exato · ≥ 2.000 units/GPU-dia |
| **F9** Confiança e padrão | 2 | ~0 | < 0,1 | CPU | 3 I-Ds publicados · quórum 4-de-5 imposto pelo schema · entropia 1,326 bit publicada |
| **F10** Experimentos | 4 | **≈ 2,0** | ~0,2 | GPU (folga residual) | cada experimento **adotado por portão medido ou arquivado com log** |
| **F11** Regime | 3 | SOB-3 ≈ 4,2 · SOB-4 ≈ 156 (folga, FP8) | ~0,2 | misto | backlog = 0 e troca automática de perfil · Wilson LB95 ≥ 0,975 por 30 ciclos · soberania 0,39 → 0,87 |
| **Total (F0–F10)** | **46** | **≈ 38,1** | **≈ 7,7** | — | as 12 saídas acima, todas com comando e saída registrados |

**Leitura da tabela.** F0, F1 e F4 não consomem GPU: são as de maior razão valor/custo e avançam em
paralelo com qualquer outra. F3 e F8 concentram **28 dos 38,1 GPU-dias de máquina** — é por isso que o
perfil `construcao` existe e que F5 e F6 vêm **depois** do motor. F11.O1 fecha o ciclo: com backlog
zero o escalonador troca de perfil sozinho e o sistema passa a se governar pelo orçamento de regime.

**Total desta árvore: 12 fases · 49 objetivos · 149 tarefas verificáveis.** Nenhuma data, nenhum
prazo, nenhum cronograma — só dependência técnica, valor e critério de pronto binário.
