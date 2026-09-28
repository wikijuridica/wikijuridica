# RUNBOOK P-1 / P0 / P1b — commitar o plano, gravar o contrato, estancar o JSON-LD corrompido

Medido em 2026-09-15 21:36 -03 / 2026-09-16 00:36Z. HEAD `62d71de0`. Índice VAZIO, `go.mod`/`go.sum` limpos (MEDIDO).
Tudo abaixo foi medido nesta sessão em PLAN MODE (leitura), salvo o que estiver marcado DERIVADO ou A MEDIR NA EXECUÇÃO.

---

## 0. A RESPOSTA QUE O BLOCO PEDE: o `datePublished` entra no hash?

**Resposta curta: NÃO entra por construção, MAS vaza em 60 das 942 rotas — e o vazamento não é pelo dia 1, é pela proveniência.**

Não é opinião: reproduzi o produtor e hasheei os dois estados.

### 0.1 Os dois hashes, lidos no código

- `content_sha256` — `tools/generate-page-content-revision:185-187`:
  `CAMPOS_DE_CONTEUDO = ("title","meta_description","heading","summary","body_sections","faq")`.
  **Nenhum campo de data.** O próprio comentário de `conteudo_atual()` explica o porquê: datar pelo hash criaria laço.
  ⇒ a correção de `datePublished` **nunca** move `content_sha256`. (MEDIDO por leitura.)
- `served_sha256` — `conteudo_servido():361-384`: `neutraliza_datas(bruto)` e depois `BLOCOS_DE_NAVEGACAO`.
  `neutraliza_datas():267-307` faz **três** substituições: ISO `AAAA-MM-DD` → `@DATA@`; o extenso PT-BR de cada ISO
  encontrado; e a forma `dd/mm/aaaa` de cada ISO encontrado.

### 0.2 A medição (a minha, sobre o disco real)

Simulei a correção nas **942** rotas defeituosas — trocando `article:published_time`, `"datePublished"` e o
`<time datetime=…>` do rodapé, com o extenso exatamente como `internal/render/dates.go:70-81` o emite (inclusive o
ordinal `1º` do dia 1) — e comparei `served_sha256` antes/depois:

| resultado | rotas | MEDIDO |
|---|---:|---|
| `served_sha256` **inalterado** | **882** | sim |
| `served_sha256` **mudou** | **60** | sim |
| rodapé `<time>` não encontrado | 0 | sim |

**Causa dos 60, diagnosticada por diff da forma neutralizada** (em `/jurisprudencia/stj-iac-15/`):

```
-Verificado em 10/09/2026 · Fonte oficial usada como referência e proveniência.
+Verificado em @DATA@   · Fonte oficial usada como referência e proveniência.
```

A página traz `Verificado em 10/09/2026` — data de **proveniência**, conteúdo jurídico real. Hoje o conjunto ISO do
documento é `{2026-09-09, 2026-09-11, 2026-09-15, …}` e **não** contém `2026-09-10`, então essa data sobrevive à
neutralização e conta como conteúdo — correto. Ao corrigir `datePublished` para `2026-09-10`, o ISO passa a existir no
documento, o ramo `dd/mm/aaaa` de `neutraliza_datas:303-305` apaga a proveniência do hash, e o `served_sha256` muda.

> O docstring de `neutraliza_datas:302` afirma que esse falso positivo "custa uma redatação a MENOS, nunca uma a MAIS".
> **Medido: custa uma a mais.** 60 rotas. A afirmação do comentário está errada nesta direção.

### 0.3 Achado adjacente, MEDIDO, que NÃO se corrige neste bloco

`neutraliza_datas` também apaga o extenso e o `dd/mm/aaaa` das **URNs LexML**. Em `stj-iac-15` o conjunto ISO inclui
`1988-10-05`, `2015-03-16`, `2014-11-13`, `2019-11-12` — datas de normas citadas. Logo "5 de outubro de 1988" e
`05/10/1988` saem do hash: trocar a norma citada por outra que difira só na data **não redata a página**.
Segundo achado: `internal/render/dates.go:78` emite `1º` no dia 1, e o extenso que o Python gera é `1 de …` (sem `º`) —
**medido**: com `1º` o hash muda, com `1` não muda. **203 de 11.357** `index.html` trazem `1º de` (MEDIDO).
Nenhum dos dois é P1b. Ambos mudam a **fórmula** (`assinatura_da_formula:405-412` inclui `inspect.getsource(neutraliza_datas)`)
e exigem cerimônia própria de `--ressemear`. Ficam **registrados como lacuna nomeada** no §7, não executados aqui.

### 0.4 A decisão, com o critério medido

O bloco pede as duas rotas e o critério. São estas:

| | ROTA A — sem `--ressemear` | ROTA B — com `--ressemear` na passada seguinte |
|---|---|---|
| rotas redatadas | **60** (MEDIDO) | **0** (MEDIDO: `--ressemear` força `mudou_o_servido=False`, :683-692) |
| sitemap re-anuncia | 60 URLs | 0 |
| `check-lastmod-causalidade` reprova? | **NÃO** — `:289-293` aceita `servido_a != servido_d` como causa legítima e conta em `revisao_real` (VERIFICADO POR LEITURA) | não |
| custo colateral do `--ressemear` | — | **0 rotas rebaixadas** (MEDIDO: maior instante repetido no ledger = **47** < `LOTE_MINIMO = 50`, :115) |
| verdade | redata 60 páginas cujo **texto não mudou** = frescor fabricado | não redata nada = fiel ao fato |

**ESCOLHA: ROTA B.** O critério não é preferência: é que o conteúdo das 60 **não mudou**, o gate **não pegaria** o
erro, e o custo medido do `--ressemear` hoje é **zero rotas rebaixadas**. ROTA A fica como degradação aceitável só se
o `--ressemear` recusar (§5, passo 14, ramo SE NÃO VIER).

**E fica decidido também o que NÃO fazer:** não é mudança de markup (o `--ressemear` aqui **não** existe para suprimir
re-datação de markup, e sim para reassentar a linha de base do `served_sha256`), e **não** se re-anuncia o acervo.

---

## 1. Diagnóstico fechado — os números deste bloco, todos MEDIDOS hoje

| fato | número | como medi |
|---|---:|---|
| rotas no `published_manifest.jsonl` (worktree) | **11.106** | contagem de `unique_intent_id` |
| `approved_at == 2026-09-15` | **944** | varredura do manifesto |
| **`dateModified < datePublished` no HTML SERVIDO** | **942** | regex sobre os 11.106 `public/**/index.html` — 0 sem JSON-LD |
| canais dos 942 | `/jurisprudencia/` 875 · `/leis/` 38 · `/sumulas/` 29 | idem |
| as 2 restantes das 944 | `/noticias/`, `reviewed_at == approved_at == 2026-09-15` — **legítimas, não se tocam** | idem |
| rotas das 944 presentes em `first_published_at.json` | **0 de 944** | leitura do JSON |
| `first_published_at.json` | **10.107** chaves, data máxima **2026-08-27**, mtime **2026-08-28 17:26** | `ls` + JSON |
| commits que tocaram o manifesto | **50**, de 2026-06-09 a **2026-09-10** | `git log --reverse -- <manifesto>` |
| último commit do manifesto | `315ac61b` (2026-09-10); worktree **+10.946 / −10.879** | `git log -1` + `git diff --numstat HEAD` |
| ledger de revisão | **11.116** linhas, **11.116** com `served_sha256` | leitura |
| assinatura da fórmula gravada == calculada | `29055289b861d603…` (igual) | execução do módulo |
| produção AGORA | `datePublished 2026-09-15` / `dateModified 2026-09-05`, `cf-cache-status HIT`, `age 29171`, `s-maxage=604800` | curl com UA do projeto |
| `Last-Modified` servido | `Sat, 05 Sep 2026 00:00:00 GMT` (= data editorial) | idem |

### 1.1 A cadeia causal, fechada

`first_published_at.json` está órfão desde 2026-08-28 → as 944 não têm entrada →
`loadFirstPublished` (`cmd/publish-v2-direct/main.go:3575-3591`) não cobre a rota →
`pages[i].PublicationDate` fica vazio (`:500-507`) →
`ApprovedAt: primeiroNaoVazio(page.PublicationDate, opts.publishedAt)` (`:3837`) cai em `opts.publishedAt` →
a onda chama `-published-at "$HOJE"` (`tools/run-daily-content:685`) e o default já é hoje (`main.go:182`) →
**`datePublished = hoje` em toda passada**, enquanto `dateModified = content.LastModified()` (`internal/content/content.go:452-460`,
precedência `ContentRevisedAt → ReviewedAt → PublicationDate`) fica na data real.

### 1.2 O remédio do plano, como escrito, NÃO fecha o defeito — MEDIDO

Reconstruí a estreia pelos 50 commits, exatamente como `tools/generate-first-published-at:51-64,132-136`
(data do **commit**, `setdefault`, a primeira vez vence). Resultado sobre as 944:

| regra | ainda cronologicamente impossível | cai em dia 1 |
|---|---:|---:|
| **A** — estreia pura do commit do manifesto (o que o gerador faz hoje) | **900 de 944** | 0 |
| **C** — piso `min(estreia, reviewed_at)` | 0 | 6 |
| **C′** — piso `min(estreia, dateModified SERVIDO)` | **0** | **0** |

A regra A falha porque o manifesto é commitado **depois** da passada: a estreia recuperada dá `2026-09-10` contra
`dateModified 2026-09-09`. A regra C usa o campo errado — `dateModified` **não** é `reviewed_at`
(`content.go:444-460`: a precedência começa em `ContentRevisedAt`); medido em `stf-adi-4376`: `reviewed_at 2026-09-01`,
`dateModified 2026-09-05`.

**A regra correta é C′**, e é a única que fecha o invariante que o próprio publicador declara proibido
(`main.go:485-492`). Distribuição das datas novas sob C′ (MEDIDO): `2026-09-02`: 2 · `2026-09-05`: 4 ·
`2026-09-10`: 894 · `2026-09-12`: 42 · `2026-09-15`: 2 (as 2 legítimas, que não mudam).

> `datePublished > reviewed_at` **não** é defeito: página escrita e revisada em 09-09 e publicada em 09-10 é o fluxo
> editorial normal. O impossível é `datePublished > dateModified` — afirmar que o documento foi modificado antes de existir.

---

## 2. PRÉ-CONDIÇÕES — conferir ANTES do passo 1, todas em segundos

**PC-1 — janela de boot travado (FÍSICA, com hora medida).**
```bash
cd /opt/wiki && ./tools/sweep-sitemap-carencia-expirada --seco
```
MEDIDO agora: `pages-0094.xml` e `pages-0095.xml` vencem **2026-09-16 07:50Z**; agora são 00:36Z ⇒ **T+7h14m**.
Vencida a carência, `internal/publishedmanifest/publishedmanifest.go:495-513` **trava o boot do Go**.
Não é espera a aguardar: **a publicação do P1b renova a carência** — o próprio relatório diz "sem publicação ou
varredura até lá, o boot do servidor trava". Portanto **este runbook, executado antes de 07:50Z, resolve PC-1 de
graça**. Se por qualquer motivo o P1b não puder rodar até 07:50Z, rodar `./tools/sweep-sitemap-carencia-expirada`
(sem `--seco`) antes de qualquer restart.

**PC-2 — nada de `--tag` sozinho na purga.** `tools/purge-edge-cache:191-196` só atribui `alvos` dentro de
`if seletivo:`, e `:249` usa `len(alvos)` no caminho de **sucesso**, depois de a purga ter sido aceita.
Com `--tag` sem `--url`, `purga_total` é falso e o `or` não curto-circuita ⇒ **NameError com a purga já feita**
(VERIFICADO POR LEITURA, não executado). Este runbook **nunca** usa `--tag`. Usa `--de-arquivo`.

**PC-3 — índice de git vazio.**
```bash
git status --porcelain --untracked-files=no | head; git diff --cached --name-only | wc -l   # esperado 0
```
MEDIDO agora: 0. O pre-commit compila a **closure do índice**, não o pathspec: índice sujo custa o orçamento
(contrato: 77,6 s com `internal/v2ingest` no índice contra 14,9 s limpo).

**PC-4 — janela da bancada pesada.** `ops/systemd/wikijuridica-qualidade-diaria.service` toma
`/tmp/opt-wiki-agent-heavy.lock` no `ExecStart` e o segura ~60 min; próxima passada **2026-09-16 04:47 -03**.
Todo commit **Go** deste runbook vai sob `flock`. Commits de **dado e doc** são leves e não precisam.

**PC-5 — carga.** `cat /proc/loadavg`. MEDIDO nesta sessão: `11.46`. O cérebro pausa em `loadavg > 12`
(`internal/cerebro/saude.go:89`). Não é bloqueio; é o motivo de qualquer tok/s medido hoje ser teto inferior.

---

## 3. INSTRUMENTOS A CRIAR — os quatro, com spec fechada

Nenhum existe hoje; sem eles o bloco não é verificável na hora. Cada um é criado como passo do runbook.

### I-1 `tools/check-cronologia-jsonld` — o gate que faltava (read-only)
- **Mede:** para cada rota do `published_manifest.jsonl`, lê `public/<rota>/index.html` e extrai `"datePublished"` e
  `"dateModified"` do bloco `application/ld+json`. Reprova quando `dateModified < datePublished`.
  Segunda perna: amostra por **stride determinístico** (`i % passo == 0`, nunca prefixo) de N rotas contra a **borda**,
  com `wikijuridicabot` + `X-Warming-Request`, e compara o `datePublished` servido com o do disco.
- **Exit:** `0` conforme · `1` cronologia impossível ou borda divergente · `2` não mediu (sem `public/`, sem manifesto).
- **Grava:** NADA por padrão (contrato §4 / BUG-236). `--gravar` opcional → `data/ops/cronologia_jsonld.jsonl`.
- **Flags:** `--json`, `--listar N`, `--amostra-borda N` (default 0 = só disco), `--gravar`.
- **Por que primeiro:** é o ANTES/DEPOIS do bloco inteiro. Vermelho com **942**, verde com **0**.
- **Por que não serve `check-lastmod-causalidade` — MEDIDO POR EXECUÇÃO, não por leitura.** Rodei-o agora:
  ```
  rotas no ledger 11116 · revisoes REAIS 2215 · datas FABRICADAS (hash igual) 0
  instantes com precisao falsa 0 · sitemap divergente do ledger 0
  OK: todo avanco de data tem mudanca de conteudo por tras…      EXIT=0
  ```
  **Verde, com 942 páginas servindo cronologia impossível.** Ele mede `lastmod`/`content_revised_at`, e `:289-293`
  aceita `servido_a != servido_d` como causa legítima. A corrupção vive em `approved_at`/`datePublished`, que o hash
  de revisão ignora por construção. É a prova de que o I-1 não é redundante: o instrumento existente **não** cobre
  esta classe, e seu verde é indistinguível de "não há defeito".
- **Teste de nascença obrigatório:** fixture com um par `datePublished > dateModified` e um par `==`; prova por mutação
  (inverter o `<` tem de matar o teste).

### I-2 `--piso-por-conteudo` em `tools/generate-first-published-at`
- Flags reais hoje (MEDIDO): `--dry-run`, `--saida`. A nova é `--piso-por-conteudo`.
- **Faz:** depois de reconstruir a estreia pelos commits, aplica `estreia_final = min(estreia_git, dateModified_servido)`,
  lendo `dateModified` do `public/<rota>/index.html`. Rota sem estreia no git recebe `dateModified_servido`.
- **Onde vive:** Python, no gerador — **não** em `publish-v2-direct:503`. Motivo medido: o gerador é dado, commit leve;
  tocar `cmd/publish-v2-direct` dispara `.githooks/pre-commit:300` (`check-redesocial-completude` para qualquer
  `^cmd/`) e o build de ~5 min sob `flock`. O publicador já consome o arquivo sem mudança (`main.go:3575-3591`).
- **Armadilha que o código já tem e precisa continuar tendo:** `carrega_existente` + `setdefault` — a primeira vez
  vence e nunca se sobrescreve. Logo o piso tem de ser aplicado **antes** de gravar. As 10.107 entradas existentes
  estão corretas (MEDIDO: a varredura das 11.106 achou 942 defeitos e **todos** têm `datePublished 2026-09-15`,
  nenhum vem do arquivo de estreia).
- **Exit:** `0` gravou · `1` nenhum commit tocou o manifesto.

### I-3 `tools/generate-alvos-por-manifesto` — a lista de purga que não existe
- **Mede:** diff **CRU** entre duas versões do `published_manifest.jsonl` (`--base <ref-ou-arquivo>` × worktree) e
  imprime as rotas cujo `approved_at` **ou** `html_sha256` mudou, mais a gêmea `<rota>index.md` de cada uma
  (a gêmea é outro objeto na borda — `generate-page-content-revision:733-739` documenta isso).
- **Por que é obrigatório:** `--purge-targets` devolve **0** para o P1b por construção — provei que o `served_sha256`
  não muda em 882 das 942, e sob ROTA B nenhuma entra em `novas|mudadas`. A cegueira é da família inteira
  (`--purge-targets`, passo 6 do `deploy-publico`, IndexNow incremental, `check-lastmod-causalidade`,
  `check-edge-frescor`, cujos seletores são `--dia/--desde-horas/--desde-ledger`, todos sobre rota **carimbada**).
- **Grava:** NADA. Só `stdout`. `rotas_com_bytes_novos():440-478` já computa quase isto, mas só está cabeada a
  `--desde-commit`, que **força re-datação** e é proibido na mesma passada (`:431-432`).
- **Exit:** `0` sempre que conseguiu ler as duas pontas; `2` se não conseguiu.

### I-4 correção de `tools/purge-edge-cache:191` — `alvos = []` antes do ramo
- Uma linha: inicializar `alvos: list[str] = []` antes de `if seletivo:`, com teste que exercite `--tag` sem `--url`.
- Não está no caminho crítico deste runbook (usamos `--de-arquivo`), mas é defeito no **caminho de sucesso** e o
  contrato manda corrigir na mesma sessão em que se acha. Entra no commit de ferramentas (passo 3).

---

## 4. P-1 e P0 — os dois commits baratos, nesta ordem

### Passo 1 — P-1: gravar o plano e commitar (ação número 1)

**OBJETIVO:** tornar o plano durável no repositório antes de qualquer mutação.

**ANTES**
```bash
cd /opt/wiki && ls docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md 2>&1   # esperado: inexistente (MEDIDO agora)
git diff --cached --name-only | wc -l                                   # esperado: 0
```

**AÇÃO** — escrever `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` com o plano P-1..P12 e este runbook como anexo, e:
```bash
git add docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md
git commit -F /tmp/msg-p-1.txt
```
(`add` e `commit` em comandos **separados**; mensagem por `-F`, nunca `-m`; nunca capturar a saída do hook no
mesmo arquivo passado a `-F`.)

**DEPOIS**
```bash
git log -1 --stat --format='%H %s' | head -5     # 1 arquivo, docs/goal/, HEAD novo
./tools/check-contrato-vs-medicao; echo "EXIT=$?"  # esperado EXIT=0
```

**SE NÃO VIER:** se o pre-commit reprovar em `check-contrato-vs-medicao`, é porque o documento contém uma frase-zero
que o varredor caça (`publicacao zero`, `published_manifest=0`, `deficit_to_10000=10000`, `publication_allowed=0`).
Marcar a linha como histórica com uma das marcas que `_e_registro_historico` reconhece (`afirmou`, `trazia até`,
`até 2026-`, `foi superada`, `regra antiga`, linha iniciada por `>`). **Nunca** `--no-verify`.
Custo esperado do pre-commit: ele materializa a closure do índice mesmo para commit de doc — orçamento 90 s × fator de
carga 1..4 (`.githooks/pre-commit:158`); com índice vazio e carga atual, DERIVADO ~15-20 s.

**ROLLBACK:** nenhum necessário (nenhum gate varre `docs/goal/*.md`). Se preciso, editar para frente em commit novo.

---

### Passo 2 — P0: as regras novas no `CLAUDE.md`, sem quebrar a linha de volume

**OBJETIVO:** gravar no contrato as regras que esta sessão pagou, **sem** derrubar o commit de todas as outras frentes.

**ANTES**
```bash
grep -n "Estado atual" CLAUDE.md          # MEDIDO: linha 128, "11.039 páginas públicas no ar"
./tools/check-contrato-vs-medicao         # MEDIDO agora: 11.106 medidas, 11.039 declaradas, EXIT=0
```

**AÇÃO** — editar `CLAUDE.md` acrescentando as regras. As que este bloco prova e que **não** estão no contrato:
1. `datePublished` é **neutralizado** pelo hash de revisão — correção de data não gera lista de purga; a lista vem do
   diff cru do manifesto (I-3).
2. O ramo `dd/mm/aaaa` de `neutraliza_datas` apaga **data de proveniência** quando ela passa a coincidir com o ISO do
   documento: 60 rotas medidas. Correção de data roda com `--ressemear` na passada seguinte.
3. `dateModified` **não** é `reviewed_at` — `content.LastModified()` começa em `ContentRevisedAt`.
4. `datePublished > reviewed_at` é normal; o impossível é `datePublished > dateModified`.
5. `check-lastmod-causalidade` **não** pega data-only: aceita `served_sha256` mudado como causa legítima.
6. `tools/purge-edge-cache` com `--tag` sem `--url` dá NameError no caminho de sucesso.
7. `Last-Modified` das páginas é a data **editorial** (`gravaDatado`): prova de correção é **por corpo**, nunca por cabeçalho.
8. Carência de shard de sitemap trava o **boot**; publicação renova.
… e as demais regras do plano-mãe.

**REGRAS DE EDIÇÃO — cada uma custou uma sessão:**
- **NÃO reformatar a linha 128.** O regex é
  `r"Estado atual[^:]*:\s*\*{0,2}([\d.  ]+)\s*páginas? públicas?"` — com acento, e `\*{0,2}` só cobre o `**` à
  esquerda. Perder o casamento cai no ramo "não declara volume em forma verificável" e **reprova todo commit de toda
  sessão**. Atualizar **só o número e a data**: `**Estado atual (medido em 2026-09-15): 11.106 páginas públicas no ar**`.
- Mexeu na **seção 10** (governança entre pares)? Rodar
  `./tools/go-modern test -count=1 ./internal/contract/misc/ -run TestPeerGovernance` (BUG-171).
- Parágrafo superado **ganha data e motivo; não se apaga**.

**DEPOIS**
```bash
./tools/check-contrato-vs-medicao; echo "EXIT=$?"
# esperado: "published_manifest : 11106 linhas, 11106 unique_intent_id" / "CLAUDE.md declara: 11106 páginas" / EXIT=0
git add CLAUDE.md && git commit -F /tmp/msg-p0.txt
```

**SE NÃO VIER:** mensagem "não declara volume em forma verificável" ⇒ o regex deixou de casar: restaurar a forma
literal da linha 128 (editando para frente). Mensagem "declara N; o manifest mede M" ⇒ diferença acima da folga
`max(200, 5%) = 555` (MEDIDO/DERIVADO): corrigir o número declarado para o medido.

**ROLLBACK:** uma linha, para frente.

> **TETO QUE O P0 ABRE PARA O P6, e é por isso que o P0 vem antes:** declarando **11.106**, a folga passa a
> `max(200, 5% de 11.106) = 555` e o gate só reprova acima de **11.661** (DERIVADO). Com a declaração antiga de 11.039
> o teto era 11.594 — restavam 488 páginas. Atualizar a linha agora devolve ~555 de margem ao publicador autônomo.

---

## 5. P1b — estancar as 942 páginas servidas com cronologia impossível

### Passo 3 — criar os instrumentos I-1, I-2, I-3, I-4 e commitar

**OBJETIVO:** existir o que mede, antes de mudar o que é medido.

**ANTES**
```bash
ls tools/check-cronologia-jsonld tools/generate-alvos-por-manifesto 2>&1   # esperado: inexistentes
grep -c 'piso-por-conteudo' tools/generate-first-published-at              # esperado: 0
```

**AÇÃO** — escrever I-1, I-2, I-3 e a linha do I-4, com os testes de nascença. Depois:
```bash
git add tools/check-cronologia-jsonld tools/generate-alvos-por-manifesto \
        tools/generate-first-published-at tools/purge-edge-cache
git commit -F /tmp/msg-instrumentos.txt
```

**DEPOIS**
```bash
./tools/check-cronologia-jsonld --listar 5; echo "EXIT=$?"
# ESPERADO: EXIT=1, "cronologia impossível: 942" — /jurisprudencia/ 875, /leis/ 38, /sumulas/ 29   (MEDIDO)
```

**SE NÃO VIER:**
- Deu **0** ⇒ o gate está lendo a chave errada. Controle positivo obrigatório antes de acreditar: rodar contra
  `public/jurisprudencia/stf-adi-4376/index.html`, que **MEDI** servindo `datePublished 2026-09-15` /
  `dateModified 2026-09-05`. Zero sem controle positivo é "não mediu", não é "está limpo".
- Deu número **muito maior** que 942 ⇒ provável casamento de `"datePublished"` fora do bloco `ld+json`. Ancorar no
  bloco, não no documento inteiro.

**ROLLBACK:** ferramentas novas são aditivas; nenhum gate existente as executa ainda. Correção para frente.

---

### Passo 4 — commitar o `published_manifest.jsonl` que há 5 dias não é commitado

**OBJETIVO:** parar a sangria que cria rota **sem estreia recuperável**.

**ANTES**
```bash
git log -1 --format='%h %ad' --date=short -- data/editorial/published_manifest.jsonl
# MEDIDO: 315ac61b 2026-09-10 (5 dias)
git diff --numstat HEAD -- data/editorial/published_manifest.jsonl
# MEDIDO: 10946  10879
```

**AÇÃO**
```bash
git add data/editorial/published_manifest.jsonl
git commit -F /tmp/msg-manifesto.txt
```

**DEPOIS**
```bash
git diff --numstat HEAD -- data/editorial/published_manifest.jsonl   # esperado: vazio
git log -1 --format='%h %ad' --date=short -- data/editorial/published_manifest.jsonl  # esperado: HEAD, 2026-09-15
```

**SE NÃO VIER:** o pre-commit roda 5 gates incondicionais (`.githooks/pre-commit:187`) — se
`check-produto-nao-some-do-worktree` reclamar, é outra frente com produto untracked: **não** deletar nada; classificar
no `.gitignore` se for ruído, ou commitar o produto da frente que o gerou.

**ROLLBACK:** nenhum — commitar dado já produzido não é reversível nem precisa ser. Commit é checkpoint.

> **Por que ANTES do gerador:** `setdefault` — a primeira aparição vence e **nunca** é sobrescrita. As 44 rotas sem
> histórico (MEDIDO) só ganham âncora quando o manifesto entra no git. Sem este commit elas voltam ao fallback
> `-published-at HOJE` na próxima passada, e o defeito reincide amanhã.
> Este commit **não** muda o resultado de hoje (sob C′ as 44 recebem `dateModified` = 2026-09-12 de qualquer modo);
> ele fecha a reincidência.

---

### Passo 5 — reconstruir `first_published_at.json` com o piso por conteúdo

**OBJETIVO:** dar ao publicador a data de estreia correta das 11.106 rotas.

**ANTES**
```bash
python3 -c "
import json;d=json.load(open('data/editorial/first_published_at.json'));fp=d.get('first_published_at',d)
print(len(fp), max(fp.values()))"
# MEDIDO: 10107 2026-08-27
```

**AÇÃO**
```bash
./tools/generate-first-published-at --piso-por-conteudo --dry-run
```
**DEPOIS (do ensaio)** — números esperados, todos MEDIDOS por mim na reconstrução:
```
commits percorridos        : 50            (2026-06-09 .. 2026-09-15 após o passo 4)
intents já conhecidos      : 10107
intents com data recuperada: 11106
```
e na distribuição, para as 944 tocadas: `2026-09-02: 2 · 2026-09-05: 4 · 2026-09-10: 894 · 2026-09-12: 42 · 2026-09-15: 2`.

Conferido o ensaio, gravar:
```bash
./tools/generate-first-published-at --piso-por-conteudo
git add data/editorial/first_published_at.json
git commit -F /tmp/msg-estreia.txt
```

**SE NÃO VIER:**
- `intents com data recuperada` < 11.106 ⇒ o passo 4 não entrou; conferir `git log` do manifesto.
- Alguma data nova **maior** que o `dateModified` da rota ⇒ o piso não foi aplicado: o gerador está gravando
  `estreia_git` pura. Isso reproduz a regra A, que **MEDI** deixando 900 de 944 ainda impossíveis. Corrigir o gerador
  antes de seguir — publicar aqui carimbaria o erro de novo.

**ROLLBACK:** o arquivo anterior fica preservado em `.agents/runtime/` (ver passo 6) e em `git show HEAD~1:…`.
Correção é para frente: regravar com o piso certo.

---

### Passo 6 — preservar o estado que NÃO se recupera depois

**OBJETIVO:** não perder a linha de base que o `--ressemear` do passo 14 torna irrecuperável.

**ANTES/AÇÃO**
```bash
D=.agents/runtime/p1b-20260915 && mkdir -p "$D"
cp data/ops/page_content_revision.jsonl          "$D"/page_content_revision.antes.jsonl
cp data/ops/page_content_revision_formula.txt    "$D"/formula.antes.txt
cp data/editorial/first_published_at.json        "$D"/first_published_at.antes.json
./tools/check-cronologia-jsonld --json > "$D"/cronologia.antes.json
git show HEAD:data/editorial/published_manifest.jsonl > "$D"/manifesto.antes.jsonl
```

**DEPOIS**
```bash
wc -l "$D"/page_content_revision.antes.jsonl   # esperado: 11116  (MEDIDO)
cat  "$D"/formula.antes.txt                    # esperado: 29055289b861d603f90fccfe78ea6db1f1e010cb8e8c2a5c8520b64445f5eac0 (MEDIDO)
```

**SE NÃO VIER:** formula divergente da medida ⇒ outra frente editou `neutraliza_datas` ou `BLOCOS_DE_NAVEGACAO`
entre a minha medição e a execução. **Parar**: o `--ressemear` do passo 14 passaria a absorver *duas* mudanças de
fórmula ao mesmo tempo e o DEPOIS deixa de ser atribuível. Rodar
`./tools/generate-page-content-revision --dry-run` e ler o RECUSADO antes de decidir.

**Motivo (do `check-edge-frescor:300-307`, sem guarda):** depois de um `--ressemear`, os seletores `--dia` e
`--desde-horas` ficam **verdes sobre o conjunto errado**; só `--desde-ledger` enxerga, e ele exige o snapshot tirado
**antes**. Não se recupera depois.

**ROLLBACK:** n/a (é a própria rede de segurança).

---

### Passo 7 — ensaio da publicação, sem escrever um byte

**OBJETIVO:** ver o publicador reconhecer as 11.106 estreias antes de deixá-lo escrever.

**ANTES**
```bash
cat data/ops/.publish-v2-direct.lock 2>/dev/null   # esperado: inexistente; se existir, ver SE NÃO VIER
```

**AÇÃO** — o ensaio é o **mesmo caminho**, sem `-allow-public-write` (o publicador renderiza e compara sem lock,
sem snapshot e sem uma syscall de escrita):
```bash
./tools/go-modern run ./cmd/publish-v2-direct -published-at 2026-09-15 -reviewed-at 2026-09-15 2>&1 | tail -40
```

**DEPOIS** — a linha que decide:
```
data de estreia       : 11106 de 11106 páginas
```
**SE NÃO VIER:**
- `data de estreia : indisponível (…)` ⇒ `loadFirstPublished` não leu o arquivo (`main.go:3575-3591`); conferir
  caminho e que `first_published_at` não está vazio.
- `N de 11106` com N < 11106 ⇒ faltam entradas; voltar ao passo 5. **Seguir aqui carimbaria hoje nas que faltam.**
- Lock presente ⇒ **conferir vida do pid antes de remover**: `ps -p <pid>` / `ls /proc/<pid>`. `deploy-publico:463`
  apaga esse lock **sem** conferir vida, o que abre janela para dois publicadores concorrentes — não imitar.

**ROLLBACK:** n/a (nada foi escrito).

---

### Passo 8 — publicar (a única rota que não quebra o boot)

**OBJETIVO:** gravar o `datePublished` correto no HTML, no manifesto e no sitemap, **com os SHA-256 batendo**.

**ANTES**
```bash
./tools/check-cronologia-jsonld; echo "EXIT=$?"     # esperado: EXIT=1, 942
systemctl show wikijuridica-server -p ActiveState -p NRestarts -p ExecMainStatus
# esperado: active / NRestarts=0 / ExecMainStatus=0   (MEDIDO na varredura)
```

**AÇÃO**
```bash
timeout 1800 nice -n 10 ./tools/go-modern run ./cmd/publish-v2-direct \
  -published-at 2026-09-15 -reviewed-at 2026-09-15 -allow-public-write 2>&1 | tee /tmp/p1b-publica.log
echo "EXIT=${PIPESTATUS[0]}"
```

**POR QUE NÃO EDITAR O HTML/MANIFESTO À MÃO:** `main.go:3837-3849` grava `ApprovedAt`, `HTMLSHA256` e `SitemapSHA256`
no **mesmo registro**. Reescrever os 942 HTML sem recalcular `HTMLSHA256` produz 942
`published_manifest_html_sha256_mismatch`; os limiares de boot são **10 por código e 25 no total**
(`internal/publishedmanifest/publishedmanifest.go:1464-1470`) ⇒ **o Go não sobe**, morrem gêmea, `/api/v1/*`, MCP, A2A
e descritores, o acervo estático **continua no ar** e `check-portal-health` (só `127.0.0.1`) passa **verde**.

**DEPOIS**
```bash
./tools/check-cronologia-jsonld; echo "EXIT=$?"     # ESPERADO: EXIT=0, "cronologia impossível: 0"
python3 -c "
import json,collections
c=collections.Counter()
for ln in open('data/editorial/published_manifest.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if ln: c[(json.loads(ln).get('approved_at') or '')[:10]]+=1
print(sorted(c.items())[-6:])"
# ESPERADO: 2026-09-15 cai de 944 para 2   (MEDIDO: as 2 legítimas de /noticias/)
```

**SE NÃO VIER:**
- Publicação falhou (exit ≠ 0) ⇒ **NÃO recarregar o servidor**. A transação escreve sitemap e manifesto em momentos
  distintos; interrompida, o disco fica com `sitemap_loc_without_manifest`, condição que **aborta o boot**, com
  `Restart=always` e `StartLimitIntervalUSec=0` ⇒ laço de 5 s eterno, a unit nunca entra em `failed` e **OnFailure é
  vazio**: ninguém é avisado. É exatamente o ramo que `run-daily-content:690-700` documenta. Ler `/tmp/p1b-publica.log`,
  corrigir a causa, republicar.
- `cronologia impossível` continua > 0 ⇒ o piso do passo 5 não chegou ao HTML; conferir a linha
  `data de estreia : N de 11106` no log.

**ROLLBACK:** **não existe para trás, e é honesto dizer** — a data errada já foi entregue ao buscador em quatro
passadas (09-05, 09-08, 09-10, 09-15). O snapshot de `writeRollbackSnapshot` (`main.go:3988-4058`) cobre **3 arquivos**
(`pages.json`, manifesto, ensaio) e **não** cobre `public/` nem `public/sitemaps/`: chamar aquilo de rollback
transacional é otimista. A recuperação é **republicar para frente**.

---

### Passo 9 — provar a carência de sitemap renovada (PC-1 fechada)

**OBJETIVO:** confirmar que a publicação tirou `pages-0094/0095` da beira do vencimento.

**ANTES:** ver PC-1 — `vence em 2026-09-16 07:50Z`, T+7h14m (MEDIDO).

**AÇÃO/DEPOIS**
```bash
./tools/sweep-sitemap-carencia-expirada --seco; echo "EXIT=$?"
```
**ESPERADO:** `0 vencido(s)` e **0 vencendo em menos de 48h**, ou `pages-0094/0095` fora da lista de carência.

**SE NÃO VIER:** rodar `./tools/sweep-sitemap-carencia-expirada` (sem `--seco`) **antes** do restart do passo 11.
A varredura agendada roda **08:19:09Z**, 29 min **depois** do vencimento — não serve.

---

### Passo 10 — montar a lista de purga (a que `--purge-targets` não sabe montar)

**OBJETIVO:** ter as URLs exatas a purgar, sem tocar o ledger.

**ANTES**
```bash
./tools/generate-page-content-revision --purge-targets | wc -l
# ESPERADO: 0 ou pouquíssimas — e isso NÃO é "nada a purgar": é o hash cego à data (provado no §0)
```

**AÇÃO**
```bash
./tools/generate-alvos-por-manifesto --base HEAD~1 > /tmp/p1b-alvos.txt
wc -l /tmp/p1b-alvos.txt
```
**ESPERADO:** **1.884** linhas — 942 rotas HTML + 942 gêmeas `index.md` (DERIVADO das 942 medidas).

**DEPOIS**
```bash
head -4 /tmp/p1b-alvos.txt        # rotas iniciando por /jurisprudencia/, /leis/, /sumulas/
grep -c 'index.md$' /tmp/p1b-alvos.txt   # esperado: 942
grep -c '^/noticias/' /tmp/p1b-alvos.txt # ESPERADO: 0 (as 2 legítimas não mudaram)
```

**SE NÃO VIER:** lista vazia ⇒ o `--base` apontou para o commit errado (tem de ser o manifesto **antes** do passo 8).
Usar o snapshot: `--base .agents/runtime/p1b-20260915/manifesto.antes.jsonl`.

**ROLLBACK:** n/a (só stdout).

---

### Passo 11 — recarregar o Go (as 5 superfícies de máquina são retrato do BOOT)

**OBJETIVO:** fazer o canal de máquina conhecer o que o disco já tem.

**ANTES**
```bash
./tools/reload-wiki-server --check; echo "EXIT=$?"
curl -sS -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' https://wikijuridica.com.br/api/v1/citar/jurisprudencia/stf-adi-4376/ | head -c 300
```
**ESPERADO no ANTES:** `html_sha256` **diferente** do sha do arquivo em `public/` recém-escrito — porque
`buildAPIPublishedPages` roda dentro de `httpserver.New()` (`internal/httpserver/httpserver.go:1071`) e o índice é
retrato do boot.

**AÇÃO**
```bash
./tools/reload-wiki-server
```
É a cadeia sancionada (a onda a usa na etapa 9/9) e é **idempotente e auto-verificável** por construção, conforme o
próprio cabeçalho do arquivo: (1) mede a divergência pedindo o markdown de uma rota que existe no manifesto do disco;
(2) **só reinicia se houver divergência** — reiniciar sem motivo derruba a busca e zera o índice quente;
(3) verifica depois pelo mesmo predicado; (4) grava evidência em `data/ops/server_reload.jsonl`.
Sem divergência, sai `0` sem tocar em nada — então rodá-la é seguro mesmo que o passo 8 já tenha recarregado.

**DEPOIS**
```bash
systemctl show wikijuridica-server -p ActiveState -p SubState -p NRestarts -p ExecMainStatus
# ESPERADO: active / running / ExecMainStatus=0
tail -1 data/ops/server_reload.jsonl      # evidência própria da ferramenta: divergência medida + verificação pós
./tools/reload-wiki-server --check; echo "EXIT=$?"   # ESPERADO: EXIT=0, sem divergência
sha=$(sha256sum public/jurisprudencia/stf-adi-4376/index.html | cut -c1-16)
curl -sS -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' https://wikijuridica.com.br/api/v1/citar/jurisprudencia/stf-adi-4376/ \
  | grep -o '"html_sha256":"[^"]*"'
# ESPERADO: bate com $sha  (A MEDIR NA EXECUÇÃO)
```

**SE NÃO VIER:**
- `/api/v1/citar` devolve **404** para rota que está no disco ⇒ **não é "não publicou"**: é Go desatualizado.
  Tratamento certo: **reiniciar pela cadeia — NÃO republicar, NÃO purgar.**
- Unit em laço ⇒ ler `journalctl -u wikijuridica-server --since "-5min"`. `OnFailure` é **vazio** e
  `StartLimitIntervalUSec=0`: o laço é mudo, ninguém avisa. Conferir primeiro
  `published_manifest_sitemap_loc_without_manifest` e a carência do passo 9.

**ROLLBACK:** para frente — corrigir a causa do boot e recarregar. Nunca `systemctl stop` de unit oneshot em execução
(marca `failed` e dispara alerta falso ao dono).

---

### Passo 12 — purgar a ORIGEM antes da BORDA (a ordem que 2026-09-05 fixou)

**OBJETIVO:** impedir que a borda repopule com o conteúdo velho da zona `wj_dyn`.

**ANTES**
```bash
tail -2 data/ops/edge_cache_purge.jsonl
# se a última linha trouxer scope "tudo" recente, NÃO purgar de novo (joga fora ~870 s de aquecimento)
```

**AÇÃO** — só as gêmeas `.md`, que são servidas **pelo Go** e passam pelo `proxy_cache wj_dyn`:
```bash
grep 'index.md$' /tmp/p1b-alvos.txt | sed 's#index.md$##' > /tmp/p1b-areas.txt
./tools/purge-origin-cache --seco --rota /jurisprudencia/stf-adi-4376/   # ensaio primeiro
# depois, dirigido, por rota
```

**DEPOIS**
```bash
curl -sS -o /dev/null -D - -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' http://127.0.0.1:8088/jurisprudencia/stf-adi-4376/index.md | grep -i 'x-cache\|age'
```
**ESPERADO:** MISS na origem (A MEDIR NA EXECUÇÃO).

**SE NÃO VIER / POR QUE ESTA ORDEM:** medido em 2026-09-05 (`.agents/runtime/mensagens/msg-deploy-binario.txt:18-22`):
purgar a borda **antes** de invalidar/aquecer a origem faz o Tiered Cache promover o conteúdo VELHO —
`age 0`, `cf-cache-status HIT`, `campos=0`, cinco tentativas seguidas; com a ordem certa, `campos=3` de primeira.
Se este runbook rodar por `deploy-publico`, o passo 4 dele já apaga `var/nginx/cache` e o 5b reaquece — aí a origem
está resolvida e só falta a borda. Por `publish-v2-direct` solto (que é o caso aqui), **ninguém** toca `wj_dyn`:
este passo é obrigatório.

**ROLLBACK:** cache é regenerável; o passo 14 reaquece.

---

### Passo 13 — purgar a BORDA, dirigida, com o teto casado à lista

**OBJETIVO:** tirar da borda o JSON-LD errado que ela serve há 8 h.

**ANTES**
```bash
curl -sS -o /tmp/b.html -D /tmp/h.txt \
  -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' https://wikijuridica.com.br/jurisprudencia/stf-adi-4376/
grep -iE '^(cf-cache-status|age|cache-control):' /tmp/h.txt
grep -o '"datePublished":"[^"]*"\|"dateModified":"[^"]*"' /tmp/b.html
```
**MEDIDO AGORA:** `cf-cache-status: HIT`, `age: 29171`, `s-maxage=604800`,
`"datePublished":"2026-09-15"` / `"dateModified":"2026-09-05"`.

**AÇÃO**
```bash
N=$(wc -l < /tmp/p1b-alvos.txt)
./tools/purge-edge-cache --de-arquivo /tmp/p1b-alvos.txt --teto-por-url $((N+1)) --dry-run
./tools/purge-edge-cache --de-arquivo /tmp/p1b-alvos.txt --teto-por-url $((N+1))
```

**DUAS ARMADILHAS, as duas medidas:**
- **`--teto-por-url` tem de ser ≥ o tamanho da lista.** Acima do teto (default **3000**) a ferramenta degrada **em
  silêncio** para `{"purge_everything": True}` (`:209`) e joga fora ~870 s de aquecimento. Com 1.884 alvos o default
  já acomodaria, mas passar o teto explícito é a regra.
- **NUNCA `--tag` sozinho** (PC-2): NameError em `:249` **depois** de a purga ter sido aceita.

**DEPOIS**
```bash
grep -iE '^(cf-cache-status|age):' /tmp/h.txt   # após repetir o curl do ANTES
grep -o '"datePublished":"[^"]*"' /tmp/b.html
```
**ESPERADO:** `cf-cache-status: MISS` (ou `EXPIRED`) e `"datePublished":"2026-09-10"`.

**A PROVA TEM DE SER POR CORPO, e isto eu medi:** `gravaDatado` carimba o mtime a partir da data **editorial**, então
o `Last-Modified` servido é `Sat, 05 Sep 2026 00:00:00 GMT` e **não muda** com a correção. Medi: com
`If-Modified-Since` da data atual a origem devolve **304**; sem o cabeçalho, **200 / 20.584 bytes**.
⇒ `grep datePublished` no corpo, **nunca** um cabeçalho de data.

**SE NÃO VIER:** continua `HIT` com `age` alto ⇒ a purga não alcançou aquela URL (conferir
`tail -1 data/ops/edge_cache_purge.jsonl`: `success`, `http_status`, `scope`). Continua `datePublished 2026-09-15`
com `MISS` ⇒ a **origem** ainda serve o velho: voltar ao passo 12.

**ROLLBACK:** não se desfaz purga; reaquece-se (passo 14).

---

### Passo 14 — reassentar o ledger de revisão (ROTA B) e reaquecer a borda

**OBJETIVO:** impedir as 60 re-datações fabricadas e devolver a borda ao quente.

**ANTES**
```bash
./tools/generate-page-content-revision --dry-run 2>&1 | tail -20
```
**ESPERADO:** ele acusaria ~**60** rotas "mudadas" (MEDIDO por simulação) — todas por data, nenhuma por texto.

**AÇÃO**
```bash
./tools/generate-page-content-revision --ressemear
./tools/warm-edge-cache --de-arquivo /tmp/p1b-alvos.txt --rps 12 --concorrencia 4
```

**DEPOIS**
```bash
./tools/check-lastmod-causalidade --json | python3 -c "
import sys,json;d=json.load(sys.stdin)
print({k:d[k] for k in d if 'fabricad' in k or 'divergente' in k or 'conferidas' in k})"
# ESPERADO: datas_fabricadas_hash_igual_data_avancou = 0, sitemap_divergente_do_ledger = 0
python3 -c "
import json,collections
c=collections.Counter()
for ln in open('data/ops/page_content_revision.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if ln: c[json.loads(ln)['revised_on'][:10]]+=1
print(c.get('2026-09-15',0))"
# ESPERADO: o mesmo valor de ANTES do passo 8 (nenhuma rota nova carimbada hoje)
```

**CUSTO DO `--ressemear`, MEDIDO e igual a zero hoje:** ele rebaixa carimbo de instante para dia **só** quando o mesmo
instante se repete em ≥ `LOTE_MINIMO = 50` rotas (`:115`, `:701-717`). Medi o ledger: **115** entradas com instante,
**11.001** com dia, e o instante mais repetido é `2026-09-12T15:26:42Z` com **47** ocorrências — **abaixo de 50**.
⇒ **0 rotas rebaixadas**.

**SE NÃO VIER (e é aqui que ROTA A entra):**
- `RECUSADO: a fórmula do served_sha256 mudou…` ⇒ outra frente editou o produtor entre o passo 6 e agora.
  **Parar** e reconciliar: o `--ressemear` absorveria duas mudanças e o DEPOIS deixa de ser atribuível.
- `--ressemear` indisponível por qualquer motivo ⇒ **ROTA A**: rodar `./tools/generate-page-content-revision` normal,
  aceitar **60** re-datações (0,54% do acervo), **declará-las** no commit com a lista, e purgar+reaquecer também essas
  60 (elas entram em `--purge-targets`, aí sim). Não é catástrofe — não é re-anúncio em massa —, mas é frescor
  fabricado que o gate **não** pegaria, então tem de ficar escrito.

**ROLLBACK:** o ledger e a fórmula anteriores estão em `.agents/runtime/p1b-20260915/` (passo 6). Restauração é por
**cópia para frente**, nunca `git checkout`.

---

### Passo 15 — commitar o resultado e fechar o ciclo

**ANTES**
```bash
git status --porcelain data/editorial/published_manifest.jsonl data/ops/page_content_revision.jsonl \
  data/ops/page_content_revision_formula.txt content/pages.json | head
```

**AÇÃO** — `add` por caminho exato, `commit` em comando separado:
```bash
git add data/editorial/published_manifest.jsonl
git add data/ops/page_content_revision.jsonl data/ops/page_content_revision_formula.txt
git add content/pages.json
git commit -F /tmp/msg-p1b.txt
```
> **`public/` NÃO é rastreado** — MEDIDO: `git check-ignore -v` devolve `.gitignore:3:/public/`, e
> `git ls-files --error-unmatch` sobre um `index.html` responde "did not match any file(s) known to git".
> Logo o HTML servido **não entra em commit nenhum** e a coerência entre git e disco é garantida só pelo
> `html_sha256` do manifesto — que é exatamente por que o passo 8 tem de passar pelo `publish-v2-direct`.

**DEPOIS**
```bash
./tools/check-cronologia-jsonld; echo "EXIT=$?"          # ESPERADO: 0
./tools/check-contrato-vs-medicao; echo "EXIT=$?"        # ESPERADO: 0 (11.106 declaradas no passo 2)
./tools/check-v2-portfolio-pairing                       # MEDIDO: 3,45 s, pareamento OK
./tools/check-csp-style-hashes; echo "EXIT=$?"           # orçamento DECLARADO 20 s
```

**SE NÃO VIER:** `check-csp-style-hashes` vermelho logo após publicar é **esperado** enquanto `public/` não
republicou a folha — ele avisa que falta deploy, não é defeito a consertar. Se persistir depois, comparar byte a byte
`ops/nginx/security-headers.conf:52` com `render.StylesheetPath()`: divergiu ⇒ **nenhuma página tem estilo**, com
200 em tudo e todos os gates de conteúdo verdes.

**ROLLBACK:** para frente.

---

## 6. O QUE SE MEDE NOS BOTS — sem esperar janela

O portão é prova medida. Três leituras, todas sobre dado que **já existe no disco**:

**B-1 — latência ZERO, log cru do nginx** (o atalho para a "janela de horas"):
```bash
LC_ALL=C grep -c 'stf-adi-4376' /var/log/nginx/wikijuridica/access.log
LC_ALL=C grep -iE 'GPTBot|PerplexityBot|ClaudeBot|OAI-SearchBot|Googlebot|bingbot' \
  /var/log/nginx/wikijuridica/access.log | grep -c 'jurisprudencia'
```
- `LC_ALL=C` é obrigatório: `date +%b` devolve `set` em pt_BR e o nginx escreve `Sep` — a comparação falha **em
  silêncio** devolvendo zero.
- `grep -c` conta **linha**; `grep -oE` conta **ocorrência** e o UA do PetalBot casa duas vezes.
- **Ausência aqui não é ausência:** com `s-maxage=604800` a maior parte do rastreio nunca toca a origem. Medido:
  GPTBot teve **686 rotas na borda contra 0 na origem** no mesmo dia em que fez 36.609 requisições.

**B-2 — o que a borda viu** (cumulativo: ler a ÚLTIMA linha por `date`, **nunca** somar; somar infla até 2.045.285×,
e a chave é `requests_estimated`, não `requests`):
```bash
python3 -c "
import sys;sys.path.insert(0,'tools');import edgetelemetry
s=edgetelemetry.serie_saneada()
print(len(s))" 2>/dev/null || tail -1 data/ops/edge_bot_agents_daily.jsonl
```

**B-3 — cobertura sob demanda, sem esperar o timer diário:**
```bash
./tools/measure-crawl-coverage      # consulta GraphQL; NÃO precisa esperar as 01:11
```
`crawl_coverage_state.paths_first_seen` é a **única** fonte que prova leitura que a origem não viu.

**A espera que é física, com o número e o atalho:**
- **TTL de borda `s-maxage=604800` = 7 dias.** Externo (Cloudflare honra o header da origem). **Atalho: a purga
  dirigida do passo 13** — mede-se na hora, `MISS` + corpo novo.
- **Agenda dos crawlers de terceiro.** Medido no histograma de hora UTC do primeiro contato: **GPTBot 97% entre
  01h-02h UTC**; perplexitybot 67% em 14h-15h; cloudflare-ai-search 68% em 15h-16h. Externo — nenhum instrumento nosso
  muda a agenda de outro operador. **Atalho: não esperar.** Agora são **00:36Z**; a varredura do GPTBot começa em
  ~**25 min**. Publicar antes dela é a diferença entre observar hoje e observar amanhã — e é por isso que a hora de
  publicação é variável de controle, não detalhe.
- **Retenção de 8 dias** do `httpRequestsAdaptiveGroups` da Cloudflare: único teto duro de arqueologia na borda.
  O log de origem guarda **30 dias** (medido: 223 MB, `access.log` + 30 rotações).

---

## 7. LACUNAS NOMEADAS — achadas neste bloco, NÃO executadas aqui

1. **`neutraliza_datas` apaga data de PROVENIÊNCIA e data de NORMA (URN LexML).** Medido: 60 rotas mudam de hash por
   coincidência do ramo `dd/mm/aaaa`; e `1988-10-05`, `2015-03-16` entram na neutralização, de modo que trocar a norma
   citada por outra que difira só na data **não redata a página**. O comentário de `:239-244` afirma "7 ocorrências
   ISO, todas metadado de data" — medi **12 e 14**. Correção muda a **fórmula** ⇒ passada própria com `--ressemear`.
2. **Ordinal `1º` não é neutralizado.** `internal/render/dates.go:78` emite `1º`; o Python gera `1 de …`.
   **203 de 11.357** páginas afetadas (MEDIDO). Mesma passada da lacuna 1.
3. **`check-lastmod-causalidade` não pega data-only** (`:289-293` aceita `served_sha256` mudado como causa legítima).
   O I-1 cobre o buraco, mas o gate antigo continua anunciando verde onde há defeito.
4. **`published_manifest.jsonl` não commitado não tem gate.** `deploy-publico:307` barra `v2_pages` e `portfolio_v2`
   sujos e **não** o manifesto — que é justamente de onde a estreia é derivada. Cada dia sem commit joga mais rotas no
   balde irrecuperável: **44 hoje** (MEDIDO).
5. **`tools/deploy-publico` não tem modo seco** e **`run-daily-content --seco` está morto** desde 2026-09-09
   (`:36` liga `SECO=1`, o laço de `:99-108` não conhece `--seco`, cai no `*)` e sai com exit 2 em `:105`, **antes**
   do trap). Não há ensaio seguro da onda hoje.
6. **`writeRollbackSnapshot` não cobre `public/` nem `public/sitemaps/`** (`main.go:3988-4058`): o nome promete mais do
   que o mecanismo entrega.
7. **Sem `signal.Notify`** em `cmd/publish-v2-direct`, `internal/publicrelease` e `cmd/build`; a unit é oneshot com
   `KillSignal=15` e `TimeoutStopUSec=90s` ⇒ SIGTERM no meio da transação não roda defers: lock órfão e
   `public/`+sitemap parciais, condição que aborta o boot.
8. **`wikijuridica-server.service` tem `OnFailure` vazio, `StartLimitIntervalUSec=0` e `WatchdogUSec=0`**: laço de 5 s
   eterno, sem alerta, no serviço que serve o canal de máquina inteiro.

---

## 8. RESUMO EXECUTÁVEL — a ordem, sem prosa

| # | ação | prova imediata |
|---|---|---|
| PC | `sweep-sitemap-carencia-expirada --seco` · índice vazio · `/proc/loadavg` | 0 vencidos · 0 staged |
| 1 | escrever plano → `add` → `commit -F` | `check-contrato-vs-medicao` EXIT=0 |
| 2 | `CLAUDE.md` (linha 128 → **11.106**) → commit | EXIT=0, "declara 11106" |
| 3 | criar I-1/I-2/I-3/I-4 → commit | `check-cronologia-jsonld` EXIT=1, **942** |
| 4 | `add`+`commit` do `published_manifest.jsonl` | `git diff --numstat HEAD` vazio |
| 5 | `generate-first-published-at --piso-por-conteudo` (`--dry-run` antes) | 11.106 de 11.106 |
| 6 | snapshot para `.agents/runtime/p1b-20260915/` | ledger 11.116 · fórmula `29055289…` |
| 7 | ensaio `publish-v2-direct` **sem** `-allow-public-write` | `data de estreia: 11106 de 11106` |
| 8 | publicar com `-allow-public-write` | `check-cronologia-jsonld` EXIT=0, **0** |
| 9 | `sweep-sitemap-carencia-expirada --seco` | 0 vencendo em 48 h |
| 10 | `generate-alvos-por-manifesto --base HEAD~1` | **1.884** linhas |
| 11 | `reload-wiki-server` | `/api/v1/citar` bate com o sha do disco |
| 12 | `purge-origin-cache` nas gêmeas | MISS em `127.0.0.1:8088` |
| 13 | `purge-edge-cache --de-arquivo --teto-por-url N+1` | borda: `MISS` + `datePublished 2026-09-10` |
| 14 | `generate-page-content-revision --ressemear` + `warm-edge-cache --rps 12` | `datas_fabricadas = 0` |
| 15 | `add` por caminho exato + `commit -F` | `check-cronologia-jsonld` e `check-contrato-vs-medicao` EXIT=0 |

**Proibido neste bloco:** `--ressemear` no `deploy-publico` (a fórmula não mudou e a re-datação não é verdadeira) ·
`--tag` sozinho no `purge-edge-cache` · `--desde-commit` na mesma passada do `--ressemear` · editar HTML ou manifesto
fora do `publish-v2-direct` · `git reset/checkout/stash/clean/revert` · `sudo nginx -t` · `cmd/check` sem argumento ·
padrão full-tree em Go.
