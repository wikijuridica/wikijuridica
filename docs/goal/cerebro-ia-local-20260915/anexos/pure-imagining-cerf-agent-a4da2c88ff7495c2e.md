# RUNBOOK OPERACIONAL — BLOCO P6 + P8 + P7

**Escopo**: publicar as páginas de acórdão que já passam nos gates, ligar a
agregação dos agravos nas páginas de artigo de norma, e destravar o DataJud.
Este bloco **escreve em produção**. É onde um erro custa mais.

**Como ler cada passo**: OBJETIVO → ANTES (medir) → AÇÃO → DEPOIS (medir) → SE
NÃO VIER → ROLLBACK (sempre para frente; `git reset/checkout/stash/clean/revert`
são PROIBIDOS).

**Marcação de todo número**:
`MEDIDO` = medi nesta sessão, com o comando ao lado · `DERIVADO` = aritmética
sobre um MEDIDO · `DIAGNÓSTICO` = veio do enunciado, confirmei por leitura de
código mas não re-medi · `A MEDIR` = só existe na execução.

---

## 0. OS DEZ FATOS QUE REORDENAM ESTE BLOCO

Todos medidos ou lidos nesta sessão. Cada um muda um passo do plano original.

**F1 — O shard de acórdãos NÃO EXISTE.** `MEDIDO`:
`ls data/editorial/v2_pages/ | grep -i acordao` → vazio; idem
`portfolio_v2/`. `cmd/generate-acordao-pages` declara
`shardRel = data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` (main.go:73)
e **nunca gravou**. Consequências: `shardpreserve` não tem o que preservar,
`shinglesDoProprioShard` devolve vazio na primeira passada, e a primeira
gravação é a que cria a família inteira.

**F2 — A COTA DO LOTE ESTÁ QUEBRADA NESTE GERADOR, e é o defeito que
`internal/tetodelote` existe para impedir.** `MEDIDO por leitura`:

- `intentsPublicados()` (main.go:732-764) **pula o próprio shard** pelo prefixo
  `stj-acordao-derivado-` (main.go:741). Logo página do próprio shard **não**
  entra em `protegidos`.
- `parecidaComPrevia(..., exceto: intentID)` (main.go:720-730) deixa a rota
  remontar a si mesma.
- O laço fecha com `if len(passada.Paginas) >= limite { break }` (main.go:265),
  e `passada.Paginas` **inclui as remontadas**.

Resultado: com o shard já contendo N páginas, a próxima passada com `-limite N`
remonta as mesmas N e acrescenta **zero**. É literalmente o defeito de
2026-09-09 descrito no cabeçalho de `internal/tetodelote` — que corrigiu os
outros cinco geradores (`generate-noticia-pages:337`,
`generate-stf-informativo-pages:391`, `generate-stj-tema-pages:380`,
`generate-stj-sumula-pages:398`, `generate-diario-pages:448`) e **não** este,
porque este nunca esteve na onda. `grep -rn tetodelote cmd/generate-acordao-pages`
→ vazio (`MEDIDO`).

**F3 — `-limit` do publicador é RECUSADO junto com `--allow-public-write`.**
`MEDIDO por leitura`, cmd/publish-v2-direct/main.go:351-358:

```
--limit não pode ser usado com --allow-public-write: ele corta a lista de
páginas e o manifesto é REESCRITO a partir dela
```

Logo **o lote de travessia NÃO se faz do lado do publicador**. Ele se faz do
lado do **gerador**, com `-limite`. O publicador sempre reescreve o manifesto
inteiro a partir de tudo que o censo aprova.

**F4 — `tools/reload-wiki-server` REINICIA o Go e prova por predicado.**
`MEDIDO por leitura`: `subprocess.run(["sudo","-n","systemctl","restart",
"wikijuridica-server"])`, espera **por predicado** (`markdown_responde`) com teto
de 90 s, e re-mede a divergência depois. `--check` é read-only (exit 1 se
divergente). Isto **fecha a lacuna "o oneshot do P6 não reinicia o Go"** da
varredura sonda: a ferramenta existe, a onda já a chama (run-daily-content:857),
e ela é idempotente (sem divergência, sai 0 sem tocar em nada).
Correção de nome: **`tools/publicar-estoque` não existe**; as ferramentas reais
são `tools/publicar` (prepara + publica, NÃO reinicia) e `tools/reload-wiki-server`
(reinicia + prova).

**F5 — A folga do contrato é de 488 páginas, e ela para TODA sessão.** `MEDIDO`:
`wc -l data/editorial/published_manifest.jsonl` = 11.106 linhas / 11.106
`unique_intent_id` distintos. `tools/check-contrato-vs-medicao:190-200`:
`folga = max(200, int(publicadas*0.05))` = **555**; CLAUDE.md declara **11.039**.
`DERIVADO`: reprova quando o manifesto passar de **11.594** → restam **488**
páginas. O gate é **incondicional** no pre-commit (`.githooks/pre-commit:187`) e
lê a **worktree**, não o índice. Publicar 2.488 sem corrigir a linha do CLAUDE.md
faz **todo commit de toda sessão** falhar — inclusive os que nada têm com
publicação. E como ele lê a worktree, **editar a linha no disco já destrava**;
o commit vem depois.

**F6 — Dois shards de sitemap vencem em 2026-09-16T07:50Z, e publicar é o que
os varre.** `MEDIDO agora` (`./tools/sweep-sitemap-carencia-expirada --seco`):

```
ATENCAO: pages-0094.xml vence em 2026-09-16 07:50Z — menos de 48h.
ATENCAO: pages-0095.xml vence em 2026-09-16 07:50Z — menos de 48h.
carencia: 6 shard(s) fora do indice | 0 vencido(s) | 2 vencendo em menos de 48h
```

`publishedmanifest.go:495-513` recusa no **boot** shard fora do índice com
carência vencida — "é o portal fora do ar". E o cabeçalho de
`tools/sweep-sitemap-carencia-expirada` diz quem varre: **`cmd/publish-v2-direct`**.
Portanto: **publicar RESOLVE**; reiniciar sem publicar depois do vencimento
DERRUBA. Vira pré-condição dura de todo passo que reinicie o Go (§ passo 9).

**F7 — Custo medido do gerador em escala.** `MEDIDO`:
`./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000` →
`real 12m27,9s · user 11m9,3s`, exit 0, sob `loadavg1` entre 11,8 e 14,4.
O teto por gerador na onda é `timeout 900` (run-daily-content:471) — ou seja,
**747,9 s contra 900 s: cabe, com 17% de folga sob carga alta**. A causa do
custo é o anti-molde `parecida(assinatura, aceitas)` (main.go:288), que compara
cada página nova contra **todas** as já aceitas: O(n²) no tamanho do lote.
Isto obriga o oneshot a declarar orçamento próprio e a medir o tempo (passo 5).

**F8 — AREsp: 308 páginas de mérito, e o AgInt NÃO se classifica por regex
(retratação minha).** `MEDIDO` sobre o corpus real (60.221 registros):

| medida | valor |
|---|---|
| registros no corpus | **60.221** (o comentário do gerador diz 37.085 — desatualizado) |
| `procedimental()==true` | **49.807 (82,7%)** — bate com o diagnóstico |
| não-procedimentais | 10.414 |
| classe EXTERNA (1º token antes de " NO/NOS ") | AGINT 32.837 · ARESP 11.553 · RESP 10.023 · EDCL 5.285 · HC 149 · PET 68 |
| AREsp puro, dispositivo decide o RECURSO | **5.705** |
| AREsp puro, dispositivo só "não conhecer do recurso" | 5.848 |
| AREsp puro que menciona "agravo interno" | **0 de 11.553** |
| AREsp de mérito **e** ementa ≥ 250 palavras **e** evidência substantiva | **308** |
| barrados (qualquer família) que passariam o piso de evidência | **2.691** (o diagnóstico dizia 2.902; critério meu declarado abaixo) |

Critério de "evidência substantiva" que usei: pelo menos uma URN fora de
`dispositivosDeAdmissibilidade` (main.go:353-370) **ou** uma súmula fora de
`sumulasProcessuais` (main.go:327-330) — a mesma régua do gerador.

**RETRATAÇÃO, e ela é o achado mais importante do P8**: apliquei o mesmo
classificador de dispositivo ao AgInt e ele devolveu **30.127 "mérito"**, o que é
**falso** — em AgInt "lhe negar provimento" é o agravo interno, não o mérito do
especial. Três tentativas minhas de classificar por regex deram **17, 392 e
5.705** para o mesmo conjunto de AREsp. Conclusão de engenharia: **não existe
régua medida para separar AgInt por texto de dispositivo**, e escrever uma no
gerador seria exatamente o "detector que acusou 46 páginas e as 46 eram falso
positivo" do §5 do contrato. Por isso o passo 3 admite **só** o AREsp externo,
com teste de falso positivo sobre amostra por stride, e **mantém o AgInt barrado**
— ele entra como agregado pelo P8, que é onde o plano já o queria.

**F8-bis — AS 2.488 PÁGINAS EXISTEM, E EU AS CONTEI.** `MEDIDO nesta sessão`,
`./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000`, saída
literal:

```
corpus: 60221 acórdãos lidos, 4763 candidatos de mérito com evidência suficiente
anti-molde: 1134 página(s) publicada(s) de /jurisprudencia/ e 0 do próprio shard entram na comparação
páginas montadas: 2488
  corpo:    min 487  mediana 681  max 700 (banda do verbete: 350-700)
  autoral:  min 355  mediana 525  max 632 (piso do gate: 250)
  citado:   min 42  mediana 151  max 292 (mínimo oficial: 25)
```

Três leituras que mudam o runbook:

- **2.488 confere com o diagnóstico, ao número** — `MEDIDO`, duas passadas
  independentes. E os **4.763** candidatos também, `MEDIDO`.
  **Mas a decomposição das recusas (1.405 molde + 682 + 165 + 22 + 1) continua
  `DIAGNÓSTICO`, não `MEDIDO` por mim**: a tabela de recusas sai depois do
  relatório e a segunda passada ainda a estava calculando (o `relata()` refaz
  distâncias de molde, O(n²) outra vez) quando fechei a sessão. Ela soma
  corretamente com os dois números que eu medi — o que a torna plausível, não
  medida. O passo 8 a lê da execução real.
- **`0 do próprio shard`** é a confirmação empírica de F1: o shard não existe.
- **As três bandas do gate autoral passam por construção**: `autoral min 355`
  contra piso **250**, `citado min 42` contra mínimo **25**, `corpo min 487`
  contra piso **350**. Mas `corpo max 700` é **exatamente** `tetoPalavras`
  (main.go:96) e a banda do `verbete` em `internal/v2ingest/validate.go:56` —
  margem **zero** no teto. Qualquer acréscimo de prosa no gerador (inclusive o
  bloco do passo 13) empurra páginas para fora da banda. O DEPOIS do passo 8
  tem de conferir `corpo max <= 700`.

**F9 — Não é preciso rotacionar shard.** `MEDIDO`: maior shard hoje é
`stj-tema-derivado-01.jsonl`, 4.187.968 B / 1.074 linhas = **3.900 B/linha**.
2.488 linhas ≈ **9,7 MB**. `grep` por teto de leitura em `internal/v2ingest/`,
`cmd/publish-v2-direct/`, `internal/v2publish/` devolve tetos **por linha**
(`scanner.Buffer(64 KiB, …)`) e agregados de **64 MiB**
(`reusable_semantics_memo.go:80`, `reconcile_v2_strict_source_stock.py:33`) —
**nenhum teto por arquivo abaixo de 10 MB**. E `intentsPublicados()` já pula
**todo** arquivo com o prefixo `stj-acordao-derivado-` (main.go:741), então um
`-02` futuro não colidiria. **Decisão: NÃO rotacionar.** `shardRel` é `const`;
rotacionar é mudança de código Go sem necessidade medida. Se algum dia o arquivo
passar de ~40 MB, aí sim.

**F10 — O enforcer do DataJud casa por prefixo SEM barra final, e é o único do
arquivo que faz isso.** `MEDIDO por leitura`,
`internal/codex2policyenforcement/policy.go:4507-4515`:

```go
return strings.HasPrefix(rel, "internal/datajud")       // SEM barra
    || strings.HasPrefix(rel, "internal/codex2datajud") // SEM barra
    || strings.HasPrefix(rel, "cmd/social/")            // COM barra
    || strings.HasPrefix(rel, "internal/consultapublica/") // COM barra
    || (strings.HasPrefix(rel, "cmd/") && strings.Contains(rel, "datajud"))
```

O enunciado diz que "internal/datajud NÃO EXISTE". Está certo como diretório e
**errado como consequência**: o prefixo **funciona hoje por acidente**, porque
casa `internal/datajudfila` e `internal/datajudtpubatch`. O defeito real é
outro, e é o mesmo que o SQLite do MESMO arquivo já corrigiu: sem barra final,
um futuro `internal/datajudrender` entraria na allowlist sozinho.
`TestSQLiteAllowlistCasaDiretorioInteiro`
(datajud_trava_estrutural_test.go) existe **para o SQLite** e **não tem
equivalente para o DataJud**. É esse o buraco a fechar (passo 14).

---

## 1. INSTRUMENTOS A CRIAR — cada um é passo deste runbook

| # | instrumento | o que mede | exit | onde grava | passo |
|---|---|---|---|---|---|
| I1 | `tetodelote` em `cmd/generate-acordao-pages` | cota conta só o que ACRESCENTA | n/a (produtor) | o shard | 2 |
| I2 | classe EXTERNA + AREsp de mérito + teste de falso positivo | quem é agravo de verdade | n/a (produtor) | o shard | 3 |
| I3 | `tools/check-publicado-no-ar` | as 5 superfícies servem o que foi publicado | 0 ok · 1 divergente · 2 não mediu | `data/ops/publicado_no_ar.jsonl` só com `--gravar` | 6 |
| I4 | `tools/measure-coorte-de-publicacao` | descoberta e leitura da coorte, por agente, sem janela mínima | 0 sempre (é medida) | `data/ops/coorte_de_publicacao.jsonl`, reescrito por coorte | 7 |
| I5 | `ops/systemd/wikijuridica-estoque-acordaos.{service,path}` | o oneshot autônomo do P6 | do script | ledger próprio | 12 |
| I6 | barra final + controle negativo + prova por mutação sobre `Sigiloso()` | a trava do DataJud casa diretório, não começo de nome | gate | baseline | 14 |
| I7 | runner + gate a jusante de `cmd/generate-lei-artigo-pages` | o produtor deixa de ser órfão | do script | o shard `leis-motor-01` | 13 |

---

## 2. ORDEM DE EXECUÇÃO, E POR QUÊ ESTA

```
  P6 ┌ 1  janela e pré-voo (leitura)
     │ 2  I1: cota (Go, sob flock)          ─┐ um commit Go só
     │ 3  I2: AREsp + teste FP (Go)         ─┘
     │ 4  I3: check-publicado-no-ar (novo gate)
     │ 5  lote de TRAVESSIA: -limite 5, a cadeia INTEIRA
     │ 6  prova ao vivo das 5 superfícies (I3)
     │ 7  I4 + primeira leitura de bot da coorte de 5
     │ 8  lote cheio
     │ 9  publicação + varredura de carência + reinício
     │ 10 linha do CLAUDE.md + manifesto + estreia
     │ 11 borda: purga dirigida + reaquecimento
     └ 12 I5: o oneshot que repete tudo isso sozinho
  P8   13 lei-artigo: runner + agravo como agregado
  P7   14 DataJud: os dois enforcers + prova por mutação
```

**Por que a travessia primeiro**: o achado que reordena tudo é que há páginas
prontas **com os gates como estão**. Se eu corrigir régua e publicar no mesmo
movimento, um defeito no ar é atribuível aos dois. O lote de 5 exercita
**todos** os elos — preservação de shard, pareamento contra o commit **pai**,
pre-commit, censo, transação, smoke, reinício, borda — pagando 5 páginas de
risco em vez de 2.488.

**Por que a cota ANTES da travessia**: sem I1, a segunda passada do gerador
acrescenta **zero** (F2). Um oneshot construído sobre isso funciona uma vez e
morre em silêncio. Corrigir depois exigiria remontar o shard inteiro.

---

# PASSO 1 — Janela e pré-voo

**OBJETIVO** Saber, antes de tocar em nada, quem mais está trabalhando, quanto
o disco já tem, e se algum vermelho é meu ou herdado.

**ANTES** (tudo read-only)

```bash
cd /opt/wiki
date -u +%Y-%m-%dT%H:%M:%SZ ; date +%Y-%m-%dT%H:%M:%S%z
cat /proc/loadavg
./tools/check-load-headroom --max 12
systemctl list-timers 'wikijuridica-daily-content*' 'wikijuridica-qualidade-diaria*' \
  'wikijuridica-sitemap-shard-grace*' --all --no-pager
./tools/check-coord-inbox --agent P6P8P7 --last 15
./tools/check-coord-status
git status --porcelain data/editorial/v2_pages data/editorial/portfolio_v2 | head
git status --porcelain go.mod go.sum
git log --oneline -1
wc -l data/editorial/published_manifest.jsonl
./tools/sweep-sitemap-carencia-expirada --seco | tail -4
ls -la data/ops/.publish-v2-direct.lock 2>&1
```

**Números esperados AGORA**

| leitura | esperado | marcação |
|---|---|---|
| `wc -l published_manifest` | **11.106** | MEDIDO |
| `git status go.mod go.sum` | **vazio** (a atestação lê o DISCO) | MEDIDO |
| `git status v2_pages portfolio_v2` | **vazio** (deploy-publico:307 barra estoque sujo) | MEDIDO |
| `sweep --seco` | `0 vencido(s)`, **2 vencendo** (0094, 0095, em 07:50Z) | MEDIDO |
| `check-load-headroom --max 12` | exit 0 | A MEDIR |
| `daily-content.timer` | próxima **04:31:33 -03 = 07:31:33Z** | MEDIDO |
| `qualidade-diaria.timer` | próxima **04:47:17 -03**, segura o flock pesado ~60 min | MEDIDO |
| `.publish-v2-direct.lock` | **ausente** | A MEDIR |

**SE NÃO VIER**
- `go.mod`/`go.sum` sujos → **PARE**. A atestação do grafo lê o disco e já
  atestou contra `go.mod` sujo duas vezes (2026-09-08). Descubra quem sujou
  (`git diff go.mod`) e trate com a frente dona; não limpe por conta.
- `v2_pages`/`portfolio_v2` sujos → outra sessão está gerando. Trabalhe outra
  frente; **nunca** `WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1` por padrão (o acidente
  de 2026-08-29 publicou 158 shards a meio caminho).
- `.publish-v2-direct.lock` presente → leia o PID gravado
  (`cat data/ops/.publish-v2-direct.lock`) e `ls /proc/<pid>`. Vivo ⇒ outra
  publicação em curso, **espere ou trabalhe outra frente**. Morto ⇒
  `tools/publicar` remove órfão com PID comprovadamente morto; use ele, nunca
  `rm` à mão.
- `sweep --seco` dizendo `N vencido(s)` com N>0 → **não reinicie o Go** até
  publicar (F6).

**ROLLBACK** Nenhum: passo só de leitura.

---

# PASSO 2 — I1: a cota do lote (Go)

**OBJETIVO** Fazer `cmd/generate-acordao-pages` contar só o que ACRESCENTA, para
que a segunda passada avance e o oneshot do passo 12 não morra em silêncio.

**ANTES**

```bash
cd /opt/wiki
grep -n 'len(passada.Paginas) >= limite' cmd/generate-acordao-pages/main.go
grep -rn tetodelote cmd/generate-acordao-pages/ || echo "NAO USA (esperado)"
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock | grep -c generate-acordao
git status --porcelain go.mod go.sum
```

Esperado: a linha existe em **main.go:265** `MEDIDO`; `grep tetodelote` vazio
`MEDIDO`; contagem no grafo do validador = **0** (`cmd/generate-acordao-pages`
está FORA do grafo — sem reatestação) `DIAGNÓSTICO, confirmado pela varredura
risco`; `go.mod`/`go.sum` limpos.

**AÇÃO**

1. Editar `cmd/generate-acordao-pages/main.go`:
   - importar `portaljuridico/internal/tetodelote`;
   - em `roda()`, antes do laço: `teto := tetodelote.Novo(limite)`;
   - trocar `if len(passada.Paginas) >= limite { break }` por, **dentro** do
     laço e **depois** de resolver `intentID` e o `jaNoShard`:
     `if !teto.Admite(jaNoShard) { continue }` — `continue`, nunca `break`,
     porque adiante ainda vêm rotas do próprio shard a preservar;
   - `teto.Conta(jaNoShard)` **depois** de todos os descartes (rota duplicada,
     molde, `montaPagina` recusou), como manda o comentário de
     `internal/tetodelote/tetodelote.go` (`Conta`);
   - `jaNoShard` vem de `previas` (`shinglesDoProprioShard`, main.go:694), que
     já é um mapa por `intentID` — nenhuma leitura nova de disco;
   - no `relata()`, imprimir `teto.Acrescentadas()` ao lado de
     `len(paginas)`, que é o número que `tools/check-onda-avanca` confronta.

2. Teste **provado por mutação** em `cmd/generate-acordao-pages/main_test.go`:
   um shard sintético com 3 rotas já montáveis + corpus com 5 candidatos,
   `-limite 2`. Asserção: `len(Paginas) == 5` (3 preservadas + 2 novas) **e**
   `Acrescentadas() == 2`. **Mutação obrigatória**: revertendo a linha para
   `>= limite { break }`, o teste tem de ficar VERMELHO com
   `Acrescentadas()==0`. Rode a mutação e **cole a saída vermelha** antes de
   aplicar a correção — o precedente do repo é que teste escrito antes de ver o
   mutante morrer fica verde com a regra desligada.

3. Commit, sob o lock pesado, com `add` e `commit` em comandos **separados**:

```bash
flock -w 3600 /tmp/opt-wiki-agent-heavy.lock \
  ./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/
git add cmd/generate-acordao-pages/main.go
git add cmd/generate-acordao-pages/main_test.go
printf '%s\n' \
 'fix(acordaos): a cota do lote conta so o que acrescenta' '' \
 'O gerador de acordaos ficou de fora da correcao de 2026-09-09 que criou' \
 'internal/tetodelote, porque nunca esteve na onda. intentsPublicados pula o' \
 'proprio shard (main.go:741), parecidaComPrevia deixa a rota remontar a si' \
 'mesma, e o laco fechava em len(passada.Paginas) >= limite: a segunda passada' \
 'remontava as N do shard e acrescentava ZERO.' '' \
 'Teste provado por mutacao: com o >= limite de volta, Acrescentadas() cai a 0.' '' \
 'Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>' \
 'Claude-Session: https://claude.ai/code/session_01UakZequrJAvHZg8aVg98y1' \
 > .agents/runtime/msg-cota-acordao.txt
flock -w 3600 /tmp/opt-wiki-agent-heavy.lock \
  git commit -F .agents/runtime/msg-cota-acordao.txt -- cmd/generate-acordao-pages
```

**DEPOIS**

```bash
./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/
git log --oneline -1
```

Esperado: `ok portaljuridico/cmd/generate-acordao-pages`, `PASS` na bancada do
pacote (não só no gate — precedente de 2026-09-05: um gate passou verde e 14 de
17 testes do pacote quebraram). `A MEDIR`.

**SE NÃO VIER**
- Pre-commit reprova por `check-go-index-compile-closure` estourando orçamento →
  o índice está sujo com `internal/v2ingest` de outra frente. **Esvazie o índice
  do que não é seu** (`git status --porcelain --cached`) e refaça; nunca
  `--no-verify`. Medido pelo contrato: 77,6 s com v2ingest no índice contra
  14,9 s limpo.
- Pre-commit dispara `check-redesocial-completude` (`.githooks/pre-commit:300`
  casa **qualquer** `^cmd/`): exit **75** é lock de build de outra sessão e vira
  **aviso**, não barra.
- O mutante **não** fica vermelho → seu teste não testa o que você acha. Imprima
  `Acrescentadas()` e `len(Paginas)` no teste antes de asserir.

**ROLLBACK** Edição para frente: um segundo commit que restaure o
comportamento anterior, **nunca** `git revert`. Como o shard ainda não existe,
o raio de dano é zero.

---

# PASSO 3 — I2: separar AREsp de AgInt, com teste de falso positivo

**OBJETIVO** Recuperar as **308** páginas de mérito que hoje o rótulo de classe
barra por substring, sem admitir nenhum agravo interno.

**ANTES** — reproduzir a minha medição, para que o número tenha dono:

```bash
cd /opt/wiki
nice -n 19 python3 - <<'PY'
import json,glob,re,unicodedata,collections
fold=lambda s:"".join(c for c in unicodedata.normalize("NFD",s.lower()) if unicodedata.category(c)!="Mn")
ext=collections.Counter(); aresp=collections.Counter()
for f in sorted(glob.glob("data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl")):
    for l in open(f,encoding="utf-8"):
        l=l.strip()
        if not l: continue
        try: r=json.loads(l)
        except Exception: continue
        c=(r.get("classe") or "").strip().upper()
        ext[re.split(r"\s+N[OA]S?\s+",c)[0].strip()]+=1
        if c=="ARESP":
            d=fold(r.get("dispositivo") or "")
            aresp["nao_conhece" if "nao conhecer do recurso" in d else "decide"]+=1
print(ext.most_common(6)); print(dict(aresp))
PY
```

Esperado `MEDIDO`: `[('AGINT',32837),('ARESP',11553),('RESP',10023),('EDCL',5285),
('HC',149),('PET',68)]` e `{'decide': 5705, 'nao_conhece': 5848}`.

**AÇÃO**

1. Em `cmd/generate-acordao-pages/main.go`, trocar `procedimental(classe)`
   (main.go:316-324) por duas funções, **nomeadas pelo que decidem**:

```go
// classeExterna é o recurso que ESTÁ SENDO JULGADO — o primeiro token antes de
// " NO "/" NOS "/" NA "/" NAS ". "AGINT NO ARESP" é agravo interno, não AREsp:
// o strings.Contains anterior casava os dois e barrava os 11.553 AREsp puros
// junto com os 32.837 AgInt. Medido em 2026-09-16 sobre 60.221 registros.
func classeExterna(classe string) string

// procedimental barra o recurso cujo objeto é o CABIMENTO. AREsp externo sai
// da lista: conhecido o agravo, o STJ julga o próprio especial — medido, 5.705
// de 11.553 dispositivos decidem o recurso e ZERO deles menciona agravo interno.
func procedimental(classe string) bool   // AGINT, AGRG, AGREG, AGRESP, EDCL, EDV, EARESP

// arespDeMerito só admite o AREsp externo cujo DISPOSITIVO decide o recurso.
// "não conhecer do recurso" é admissibilidade e continua barrado.
func arespDeMerito(r stjacordaos.Registro) bool
```

2. **Teste de falso positivo obrigatório** (§5 do contrato: "detector novo nasce
   com teste de falso positivo sobre amostra real"), em
   `main_test.go`, sobre **amostra por stride determinístico** do corpus real
   — nunca prefixo:

   - `n = 30`, `stride = len(bareAResp)/30`, semente fixa;
   - asserção positiva: dos 30, todos os admitidos têm dispositivo contendo
     provimento/negativa **do recurso**;
   - asserção negativa (controle): **0 de 30** menciona "agravo interno";
     `MEDIDO na população`: 0 de 11.553;
   - asserção de vizinhança, no molde de `TestSQLiteAllowlistCasaDiretorioInteiro`:
     `classeExterna("AGINT NO ARESP") == "AGINT"` e
     `classeExterna("EDCL NO AGINT NO ARESP") == "EDCL"` — se qualquer um casar
     `ARESP`, o filtro voltou a ser por substring.
   - **mutação**: trocando `classeExterna` de volta por `strings.Contains`,
     o teste tem de ficar vermelho. Cole a saída vermelha.

3. Commit no **mesmo** lote do passo 2, ou logo depois, com a mesma disciplina.

**DEPOIS**

```bash
./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/
nice -n 19 ./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000 \
  > /opt/wiki/.agents/runtime/acordao-seco-pos-aresp.log 2>&1 ; echo "exit=$?"
grep -E 'candidatos de mérito|páginas montadas|recusas|molde_acima' \
  /opt/wiki/.agents/runtime/acordao-seco-pos-aresp.log
```

Esperado: candidatos **sobem** em relação à linha de base do passo 5, e a alta é
de **até 308** `DERIVADO` (308 é o piso de evidência já aplicado; o anti-molde
pode recusar parte deles — é o número a medir).

**SE NÃO VIER** Se a alta for muito maior que 308, o classificador está
admitindo AgInt: rode o controle de vizinhança do item 2 e leia a distribuição
de `classeExterna` das novas. Se for **zero**, `arespDeMerito` está recusando
tudo: imprima 5 dispositivos admitidos e 5 recusados antes de mexer no regex
(precedente "imprima os spans com o mutante ANTES de escrever a asserção").

**ROLLBACK** Edição para frente. O shard ainda não existe; nada publicado.

---

# PASSO 4 — I3: `tools/check-publicado-no-ar`

**OBJETIVO** Criar o comando único que hoje **não existe** e responde:
"a produção está servindo o que eu acabei de publicar, e está certo?".
Sem ele, a verificação do passo 6 é uma sequência de `curl` à mão, e o modo de
falha mais provável do P6 (Go servindo o acervo pré-publicação, 200 em tudo)
não tem detector.

**ANTES**

```bash
ls tools/check-publicado-no-ar 2>&1   # esperado: No such file
grep -n "buildAPIPublishedPages" internal/httpserver/httpserver.go | head -3
systemctl show wikijuridica-server -p ExecMainStartTimestamp --value
```

`MEDIDO pela varredura sonda`: `buildAPIPublishedPages` roda **dentro de
`New()`** (httpserver.go:1071) — as cinco superfícies de máquina são **retrato
do boot**.

**AÇÃO** — criar `tools/check-publicado-no-ar`, read-only por padrão
(§4 do contrato / BUG-236: `check-*` só grava com `--gravar`).

Entrada, todas explícitas, **sem default de dia** (a armadilha UTC/local já
mordeu): `--rota <path>` (repetível) · `--de-arquivo <lista>` ·
`--dia AAAA-MM-DD` (obrigatório quando não houver `--rota`).

**Leitura 0, e ela vem primeiro — classe `go_desatualizado`:**

```
GET http://127.0.0.1:8089/api/v1/lote?limite=1   → linha {"tipo":"fim"}.total
compara com  wc -l data/editorial/published_manifest.jsonl
e            ExecMainStartTimestamp(wikijuridica-server)
             contra o mtime mais novo de public/<rota>/index.html
```

Se o Go carregou **menos** rotas que o disco, o veredito é
`go_desatualizado` e a instrução impressa é **"reinicie pela cadeia
(`./tools/reload-wiki-server`); NÃO republique, NÃO purgue"**. Sem esta leitura,
o oráculo `/api/v1/citar` devolve 404 na janela pós-publicação e o gate manda
republicar o que já está no disco — o conserto errado.

**Leituras 1 a 5, por rota** (todas com
`wikijuridicabot.AplicaSondaInterna`, que escreve o UA do projeto **e**
`X-Warming-Request: true`):

| # | superfície | oráculo | comparação |
|---|---|---|---|
| 1 | HTML pela borda | `GET /api/v1/citar/<rota>` → `html_sha256` | sha do corpo servido **e** sha de `public/<rota>/index.html` |
| 2 | gêmea `<rota>index.md` pela borda | `markdown_sha256` do mesmo oráculo | sha do corpo |
| 3 | variante `Accept: text/markdown` da MESMA URL | idem | sha do corpo — **terceiro objeto de cache**, medido pela varredura sonda (`age` 113.684 contra 113.980 do HTML) e que `check-edge-frescor` declara não sondar |
| 4 | `POST /mcp` `tools/call ler_pagina` | idem | sha do `markdown` devolvido |
| 5 | `POST /a2a/v1` `SendMessage` | idem | sha do `parts[0].text` |

Pegadinhas de transporte já medidas, que o código tem de embutir: A2A exige
header `A2A-Version: 1.0` (sem ele, `-32009`) e o método é **`SendMessage`**, não
`message/send`; MCP responde **sem** `initialize` e em `text/event-stream` (o
JSON vem na linha `data: `), e pede
`Accept: application/json, text/event-stream`.

Exit: **0** tudo coerente · **1** divergente (imprime rota, superfície e os dois
sha) · **2** não conseguiu medir (borda fora, Go fora) — porque "não medi" e
"medi e deu zero" não podem sair pelo mesmo código.

`--gravar` acrescenta uma linha por execução em `data/ops/publicado_no_ar.jsonl`.

**DEPOIS** — controle positivo **e** negativo antes de confiar nele:

```bash
./tools/check-publicado-no-ar --rota /previdenciario/maternidade-homem/ ; echo "exit=$?"
WIKI_ORIGEM=http://127.0.0.1:9 ./tools/check-publicado-no-ar --rota /previdenciario/maternidade-homem/ ; echo "exit=$?"
```

Esperado: **0** no primeiro (a varredura sonda já provou 4 vias × 1 rota nessa
mesma rota, `html 10f3b349… / md 14554d1a…`) e **2** no segundo. Gate que nunca
reprovou não está provado.

**SE NÃO VIER** exit 1 no controle positivo com divergência só na leitura 3 →
a variante `Accept` tem objeto de cache próprio e pode estar velha; é achado
legítimo, **não** relaxe a leitura: purgue aquela URL e releia.

**ROLLBACK** Ferramenta nova, read-only: remover do runner. Nada a desfazer.

---

# PASSO 5 — O LOTE DE TRAVESSIA (5 páginas)

**OBJETIVO** Exercitar **todos** os elos com 5 páginas de risco: preservação de
shard, pareamento contra o commit **pai**, pre-commit, censo, transação, smoke,
reinício e borda.

**ANTES**

```bash
cd /opt/wiki
ls data/editorial/v2_pages/stj-acordao-derivado-01.jsonl 2>&1   # esperado: No such file
wc -l data/editorial/published_manifest.jsonl                   # esperado 11.106
./tools/check-v2-portfolio-pairing | tail -3
git log --oneline -1
```

Esperado `MEDIDO`: shard ausente (F1), manifesto 11.106,
`check-v2-portfolio-pairing` OK em **3,45 s** (11.106 intents em v2_pages,
11.438 no portfólio).

**AÇÃO**

> **A partir de 5a, TUDO MUTA.** Os passos 1 a 4 e o ANTES deste são leitura.
> 5a escreve o shard e o portfólio; **5g também escreve** (o ledger de revisão) —
> `generate-page-content-revision` **sem flag** está na lista MUTA, e é assim que
> tem de ser aqui: é a etapa 7.9 da onda, e é dela que o publicador lê o
> `content_revised_at` que carimba o `<lastmod>`.

```bash
# 5a. [MUTA] gerar 5
nice -n 19 timeout 1800 ./tools/go-modern run ./cmd/generate-acordao-pages -limite 5 \
  | tee .agents/runtime/acordao-travessia.log
# 5b. preservação e colisão ANTES de qualquer commit
./tools/check-shard-preservation
./tools/go-modern run ./cmd/check v2-cross-shard-collision
./tools/go-modern run ./cmd/check text-truncation
./tools/go-modern run ./cmd/check derived-body-repetition
./tools/check-derived-authorial-floor
# 5c. PORTFÓLIO PRIMEIRO — a autoridade do pareamento é o commit PAI
git add data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
printf '%s\n' 'chore(portfolio): intencoes do lote de travessia de acordaos do STJ' '' \
 'Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>' \
 'Claude-Session: https://claude.ai/code/session_01UakZequrJAvHZg8aVg98y1' \
 > .agents/runtime/msg-portfolio-travessia.txt
git commit -F .agents/runtime/msg-portfolio-travessia.txt -- data/editorial/portfolio_v2
# 5d. só agora o pareamento pode passar
./tools/check-v2-portfolio-pairing
# 5e. PÁGINAS DEPOIS
git add data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
printf '%s\n' 'chore(paginas): lote de travessia de acordaos do STJ (5 paginas)' '' \
 'Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>' \
 'Claude-Session: https://claude.ai/code/session_01UakZequrJAvHZg8aVg98y1' \
 > .agents/runtime/msg-paginas-travessia.txt
git commit -F .agents/runtime/msg-paginas-travessia.txt -- data/editorial/v2_pages
# 5f. censo (sem --write primeiro: ele é read-only sem a flag)
nice -n 19 python3 tools/generate-v2-publication-severity | tail -20
nice -n 19 python3 tools/generate-v2-publication-severity --write | tail -20
# 5g. [MUTA o ledger] data de revisão ANTES de publicar — o publicador lê dela o
#      content_revised_at que carimba o HTML, o <lastmod> e o Last-Modified.
#      Rodar DEPOIS faria a data nova só alcançar o público na passada seguinte.
nice -n 19 ./tools/generate-page-content-revision | tail -8
# 5h. baseline de CONJUNTO (não de contagem de shard)
./tools/check-onda-avanca --antes --rotulo "travessia-acordaos"
# 5i. transação
nice -n 10 timeout 1800 ./tools/go-modern run ./cmd/publish-v2-direct \
  -reviewed-at "$(date -u +%F)" -allow-public-write \
  | tee .agents/runtime/publica-travessia.log
./tools/check-onda-avanca --depois --minimo 5 --rotulo "travessia-acordaos"
```

**Por que NÃO passo `-published-at`**: `ApprovedAt = primeiroNaoVazio(
page.PublicationDate, opts.publishedAt)` (main.go:3837) e `page.PublicationDate`
vem de `first_published_at.json`. Para rota **nova** não há estreia, então a flag
vale — e o default `defaultRevisionDate()` (main.go:156-158) já é
`time.Now().UTC()`. Passar a flag explicitamente só acrescenta a chance de
carimbar dia errado quando o relógio local e o UTC divergem (agora são
21:5x -03 = 00:5x Z: **dias diferentes**). `-reviewed-at` fica explícito porque
`revisaoAnterior` (main.go:428-435) só preserva a data de quem já estava no ar.

**Por que NÃO uso `-limit 5`**: F3 — é recusado com `--allow-public-write`, e o
motivo está escrito no próprio erro: o manifesto é REESCRITO a partir da lista
cortada, o que produz `sitemap_loc_without_manifest` em massa e **o servidor não
sobe**.

**DEPOIS**

| leitura | esperado |
|---|---|
| `wc -l data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` | **5** |
| `check-shard-preservation` | exit 0 |
| `check-v2-portfolio-pairing` (depois de 5c) | OK, **sem** `so_no_candidato` |
| `check-onda-avanca --depois --minimo 5` | exit 0, **novas: 5** |
| `wc -l published_manifest.jsonl` | **11.111** `DERIVADO` |
| tamanho do shard | ~**19,5 KB** (5 × 3.900 B) `DERIVADO` |

**SE NÃO VIER**
- `check-v2-portfolio-pairing` com `so_no_candidato` → você inverteu 5c e 5e.
  A correção é **commitar o portfólio** e reconferir; não é sobre o conteúdo, é
  sobre a ordem (custou 6 dias de fábrica e deixou o IndexNow mudo de 20/08 a
  26/08).
- publicador com `sem_linha_no_censo` → o censo é mais velho que o shard. Rode
  5f de novo; é exatamente o que `tools/publicar` conserta sozinho.
- publicador **exit != 0** → **PARE e NÃO reinicie o servidor**. Transação
  interrompida deixa sitemap sem manifesto, e essa condição aborta o boot com
  `Restart=always` sem teto. Leia o log, conserte a causa, republique.
- `check-onda-avanca --depois` com `novas: 0` → outra sessão publicou entre o
  `--antes` e o `--depois`; leia `git log --oneline -3 -- data/editorial` antes
  de concluir qualquer coisa.

**ROLLBACK** **Não há rollback para trás, e é preciso saber disso antes de
apertar.** `writeRollbackSnapshot` (main.go:3988-4058) copia **3 arquivos**
(`content/pages.json`, `published_manifest.jsonl`, o rehearsal jsonl) e **não**
cobre `public/` nem `public/sitemaps/`. Desfazer 5 páginas é: retirar as 5 linhas
do shard **por edição para frente** (`tools/retirar-pagina-do-ar` é o caminho
sancionado) e republicar. Com 5 páginas o custo é trivial — e é exatamente por
isso que a travessia vem antes do lote cheio.

---

# PASSO 6 — Prova ao vivo das cinco superfícies

**OBJETIVO** Provar, **pela produção**, que as 5 rotas existem e servem o mesmo
byte em HTML, gêmea, variante `Accept`, MCP e A2A.

**ANTES**

```bash
./tools/reload-wiki-server --check ; echo "exit=$?"
./tools/sweep-sitemap-carencia-expirada --seco | tail -3
```

Esperado: `--check` **exit 1** ("DIVERGENCIA: publicado no disco, invisível no
canal de máquina") — porque acabamos de publicar e o Go ainda tem o `pages.json`
do boot anterior. Exit 0 aqui seria o sinal de que **a publicação não escreveu
nada**. E `sweep --seco` tem de dizer **`0 vencido(s)`** (F6) antes de qualquer
reinício.

**AÇÃO**

```bash
./tools/reload-wiki-server          # reinicia e prova por predicado (teto 90 s)
./tools/check-publicado-no-ar --de-arquivo <(python3 - <<'PY'
import json
for l in open('/opt/wiki/data/editorial/v2_pages/stj-acordao-derivado-01.jsonl'):
    r=json.loads(l); print('/jurisprudencia/'+r['intent_id'].removeprefix('jur-')+'/')
PY
) --gravar
```

**DEPOIS**

| leitura | esperado |
|---|---|
| `reload-wiki-server` | `OK: as N rota(s) da amostra respondem no canal de máquina (Xs até servir)` |
| tempo até servir | **32 s e 23 s** foram os dois boots medidos em 2026-09-15 pela varredura sonda; teto do próprio script = 90 s |
| `check-publicado-no-ar` | exit **0**, 5 rotas × 5 superfícies |
| `curl -sI https://wikijuridica.com.br/jurisprudencia/<uma das 5>/` | `HTTP/2 200`; `cf-cache-status` **MISS** na primeira leitura (rota nova, nunca cacheada) |
| `GET /api/v1/citar/<rota>` | `cf=DYNAMIC` (a Cache Rule exclui `/api/`), `html_sha256` == sha do disco |

Prova de que a borda **não** precisa de purga aqui: rota **nova** nunca esteve
no cache; `s-maxage=604800` só prende conteúdo **já servido**. O que precisa de
purga são os artefatos de **descoberta** (passo 11).

**SE NÃO VIER**
- `check-publicado-no-ar` devolvendo `go_desatualizado` **depois** do reload →
  o restart não pegou. `systemctl show wikijuridica-server -p NRestarts -p
  ExecMainStatus -p ActiveState`. Atenção: essa unit tem `OnFailure=` **vazio**,
  `StartLimitIntervalUSec=0` e `WatchdogUSec=0` (`MEDIDO pela varredura risco`) —
  ela pode ficar em laço de 5 s **para sempre sem alertar ninguém**. Leia
  `journalctl -u wikijuridica-server --since "-5min" | head -30`.
- 404 numa das 5 na borda e 200 em `127.0.0.1:8088` → é o túnel/borda, não a
  publicação. `./tools/check-edge-live --sem-alerta` (ele **grava** o ledger sem
  flag; o `--sem-alerta` evita acordar o dono à toa).

**ROLLBACK** Nenhum: passo de leitura + um restart idempotente.

---

# PASSO 7 — I4 + a primeira leitura de bot da coorte

**OBJETIVO** Responder **agora**, sem esperar janela, "as 5 páginas foram
descobertas e lidas, e por quem". Hoje **não existe** instrumento de coorte — e
o que existe (`tools/measure-time-to-first-crawl`) lê
`first_published_at.json`, congelado em 10.107 chaves contra 11.106 do
manifesto.

**ANTES**

```bash
ls tools/measure-coorte-de-publicacao 2>&1     # esperado: No such file
LC_ALL=C grep -c . /var/log/nginx/wikijuridica/access.log
ls -la data/ops/access/nginx-$(date -u +%F).jsonl data/ops/access/access-$(date -u +%F).jsonl
```

**AÇÃO** — criar `tools/measure-coorte-de-publicacao`, read-only.

- **Entrada**: `--diff-manifesto BASE..HEAD` · `--coorte-de <arquivo de rotas>` ·
  `--desde-indexnow <ts>`.
- **Âncora por rota, nesta ordem de preferência**:
  1. **smoke do release** em `data/ops/access/access-AAAA-MM-DD.jsonl`, linhas
     com `bot_class == "self_simulation_probe"` — precisão de **segundo**, e a
     varredura de bots provou 898 de 898 rotas em **15 s**
     (2026-09-09T14:20:34Z→14:20:49Z);
  2. `indexnow_url_state.submitted_at` (microssegundo);
  3. primeiro 200 na origem.
  **NUNCA o commit** (erra 21h09, medido) e **NUNCA o mtime** (carimbo
  determinístico 00:00:00Z).
- **Duas camadas, declaradas em cada linha** (a skill `medir-bots` é explícita:
  escolher o ledger pelo que estiver à mão já produziu 7 requisições do
  Googlebot onde havia 269):
  - **origem** = `/var/log/nginx/wikijuridica/access.log` (lag **zero**) e
    `data/ops/access/nginx-*.jsonl` (lag ≤ 1 h, **incremental, somável**);
  - **borda** = `data/ops/crawl_coverage_state.json` → `crawlers_verified.<bot>.
    paths_first_seen` — a **única** fonte que prova leitura que a origem não vê
    (gptbot: 686 rotas do lote de 898 lá, **0** na origem).
- **Saída**: uma linha por `(coorte, agent_key)` com `rotas_tocadas`,
  `cobertura_pct`, `latencia_s` p05/p50/p95/max, `hora_utc_do_primeiro_contato`,
  `rotas_nunca_tocadas`, `camada`, `janela_s`. **Sem janela mínima**: roda 1
  minuto depois de publicar e devolve o que há; **nunca** imprime INCONCLUSIVO.
- **Grava** `data/ops/coorte_de_publicacao.jsonl` **reescrito por coorte**, no
  molde de `tools/generate-bot-return-series` — nunca append cumulativo.

**Armadilhas que o código tem de embutir, todas medidas**:
`LC_ALL=C` no log (`date -d ... +%b` devolve `set` em pt_BR e o nginx escreve
`Sep`) · contar **linha** com `grep -c`, nunca ocorrência com `grep -oE` (o UA do
PetalBot casa duas vezes) · `data/ops/access/` bucketiza por **UTC**: "hoje"
local atravessa **dois** arquivos · o smoke tem `warming:false`, então filtrar
só por `warming` conta 898 requisições internas como visita real — filtre
**também** por `bot_class`/`bot_simulation`.

**DEPOIS**

```bash
./tools/measure-coorte-de-publicacao --coorte-de <as 5 rotas> --camada ambas
LC_ALL=C awk -v d="$(LC_ALL=C date -u -d '-30 min' '+%d/%b/%Y:%H')" '$0 ~ d' \
  /var/log/nginx/wikijuridica/access.log | grep -c 'jurisprudencia/stj-resp'
```

Esperado `A MEDIR` na primeira execução, com estes pisos **derivados de medição
histórica**, não de calendário:

| agente | p50 até o 1º contato (lote limpo de 898, origem) | hora UTC do 1º contato |
|---|---|---|
| cloudflare-ai-search | **1,6 h** (897 de 898 = 99,9%) | 68% em 15h–16h |
| yandexbot | p05 **5 min**, p50 22,7 h | — |
| perplexitybot | 22,6 h | 67% em 14h–15h |
| petalbot | 75,4 h | — |
| amazonbot | 100,7 h | pico 19h |
| gptbot | **0 na origem**, 686 rotas na borda | **97% em 01h–02h** |

**A espera é externa e tem número. E tem atalho.** O bot não reage ao anúncio:
ele varre em **agenda fixa**. O atalho **não é esperar**, é **mover a hora da
publicação**: a onda publica ~07h UTC e o gptbot varre 01h–02h UTC — são **18 h
de espera auto-infligida** no agente que mais rastreia. O oneshot do passo 12
deve disparar **antes de 01h UTC** para a coorte cair na varredura da mesma
noite. Segundo atalho, que dispensa o timer:
`nice -n 19 python3 tools/measure-crawl-coverage` roda **sob demanda** (é
consulta GraphQL), em vez de esperar as 01:11 locais do
`wikijuridica-crawl-coverage.timer`.

**SE NÃO VIER** cobertura 0 em **todas** as camadas depois de o
`measure-crawl-coverage` sob demanda ter rodado → confira se as rotas entraram
no sitemap (`grep -c "<loc>" public/sitemaps/*.xml` e
`./tools/check-sitemap-shard-grace`). Bot não pede URL que não descobriu; "zero
404 no lote" **não** limita a publicação.

**ROLLBACK** Ferramenta de medição, read-only. Nada a desfazer.

---

# PASSO 8 — O LOTE CHEIO

**OBJETIVO** Montar tudo o que os gates já aprovam, num shard só.

**ANTES**

```bash
cd /opt/wiki
wc -l data/editorial/v2_pages/stj-acordao-derivado-01.jsonl      # esperado 5
./tools/check-load-headroom --max 12
systemctl list-timers wikijuridica-daily-content.timer --no-pager
nice -n 19 ./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000 \
  > .agents/runtime/acordao-seco-lote-cheio.log 2>&1 ; echo "exit=$?"
grep -E 'candidatos de mérito|anti-molde|páginas montadas' .agents/runtime/acordao-seco-lote-cheio.log
grep -A 20 'recusas' .agents/runtime/acordao-seco-lote-cheio.log
```

Esperado, **tudo MEDIDO por mim nesta sessão** (duas passadas independentes):

```
corpus: 60221 acórdãos lidos, 4763 candidatos de mérito com evidência suficiente
anti-molde: 1134 página(s) publicada(s) de /jurisprudencia/ e 0 do próprio shard
páginas montadas: 2488
  corpo:    min 487  mediana 681  max 700 (banda do verbete: 350-700)
  autoral:  min 355  mediana 525  max 632 (piso do gate: 250)
  citado:   min 42  mediana 151  max 292 (mínimo oficial: 25)
exit 0, real 12m27,9s / user 11m9,3s, sob loadavg1 entre 11,8 e 14,4
```

Depois do passo 3, `candidatos` sobe e `páginas montadas` sobe em **até 308**
`DERIVADO` — parte dos 308 pode morrer no anti-molde, e o número é o que se mede
aqui. Se `páginas montadas` vier **exatamente 2.488** depois do passo 3, o
classificador de AREsp não está sendo consultado: confira com
`grep -c 'jur-stj-aresp-' `no relatório.

**Atenção ao teto**: `corpo max 700` é **exatamente** `tetoPalavras` e o teto da
banda do `verbete` (`internal/v2ingest/validate.go:56`). Margem zero.

**AÇÃO — e aqui há uma decisão de engenharia que o teto do contrato impõe.**

`DERIVADO de F5`: a folga é de **488** páginas. Publicar 2.488 de uma vez leva o
manifesto a ~13.594 contra 11.039 declarados — e `check-contrato-vs-medicao`
reprova **todo commit de toda sessão**, inclusive os que nada têm com
publicação. **Não é motivo para fatiar por calendário**: a régua é declarar o
número certo. A ordem obrigatória é:

```bash
# 8a. gerar o lote inteiro
nice -n 19 timeout 2400 ./tools/go-modern run ./cmd/generate-acordao-pages -limite 5000 \
  | tee .agents/runtime/acordao-lote-cheio.log
# 8b. gates de estoque, antes de qualquer commit
./tools/check-shard-preservation
./tools/go-modern run ./cmd/check v2-cross-shard-collision
./tools/go-modern run ./cmd/check text-truncation
./tools/go-modern run ./cmd/check derived-body-repetition
./tools/check-derived-authorial-floor
# 8c. portfólio, depois páginas — comandos SEPARADOS, caminho EXATO
git add data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
git commit -F .agents/runtime/msg-portfolio-lote.txt -- data/editorial/portfolio_v2
./tools/check-v2-portfolio-pairing
git add data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
git commit -F .agents/runtime/msg-paginas-lote.txt -- data/editorial/v2_pages
```

**`timeout 2400`, e não 900**: o gerador é O(n²) no tamanho do lote
(main.go:288) e **já custou 748 s** com o shard vazio; com 2.488 páginas no
próprio shard, `shinglesDoProprioShard` acrescenta 2.488 assinaturas à
comparação. O orçamento é 3,2× o medido — e a medição do tempo real entra no
DEPOIS, porque "lentidão em 10k é bug P0" e **não se conserta aumentando
timeout**: se passar de ~2.400 s, o conserto é indexar as assinaturas (MinHash /
banda), não esticar o teto.

**DEPOIS**

| leitura | esperado |
|---|---|
| `wc -l data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` | **N** (A MEDIR; diagnóstico diz 2.488 + até 308) |
| `du -h` do shard | ~**9,7 MB** para 2.488 `DERIVADO` (3.900 B/linha MEDIDO) |
| `check-shard-preservation` | exit 0, e as **5** da travessia entre as preservadas |
| `check-v2-cross-shard-collision` | exit 0 |
| tempo de parede do 8a | **A MEDIR** — registre-o; é a linha de base do oneshot |

**SE NÃO VIER**
- `páginas montadas` muito abaixo de 2.488 → leia a tabela de **recusas** do
  próprio relatório (`molde_acima_do_limiar`, `rota_ja_publicada`,
  `numero_de_processo_nao_derivavel`). O diagnóstico já decompôs: 1.405 morrem
  pelo anti-molde, e a régua do gerador (3-gramas, dígitos neutralizados,
  limiar 0,70) é **estritamente dominada** pela régua real do gate (5-gramas,
  dígitos preservados, limiar 0,82): dos 135 pares que ela recusa, a régua real
  aprova **135 de 135**. **Isso é P4 e NÃO é deste bloco** — registre o número e
  siga; não mexa na régua no mesmo movimento em que publica, ou o defeito deixa
  de ser atribuível.
- `check-shard-preservation` reprova → um gerador apagou página redigida.
  **PARE**. O texto está no git (`git show HEAD:<shard>`), mas commitar este
  estado o tornaria a nova verdade.

**ROLLBACK** Nada foi ao ar ainda: o shard está commitado, o manifesto não mudou.
Desfazer é regenerar com `-limite` menor e deixar `shardpreserve` preservar — ele
**nunca reduz** o shard, então a correção é sempre para frente.

---

# PASSO 9 — Publicar, varrer a carência, reiniciar

**OBJETIVO** Pôr o lote no ar e provar coerência de artefato.

**ANTES**

```bash
./tools/sweep-sitemap-carencia-expirada --seco | tail -4
wc -l data/editorial/published_manifest.jsonl
ls -la data/ops/.publish-v2-direct.lock 2>&1
systemctl list-timers wikijuridica-daily-content.timer --no-pager
./tools/check-onda-avanca --antes --rotulo "lote-acordaos"
nice -n 19 python3 tools/generate-v2-publication-severity --write | tail -20
nice -n 19 ./tools/generate-page-content-revision | tail -8
```

Esperado: `0 vencido(s)` **MEDIDO agora**, com pages-0094/0095 vencendo em
**2026-09-16T07:50Z** (F6); manifesto **11.111** `DERIVADO`; lock ausente;
censo com `PUBLICAVEIS` cobrindo as N novas.

**AÇÃO**

```bash
nice -n 10 timeout 3600 ./tools/go-modern run ./cmd/publish-v2-direct \
  -reviewed-at "$(date -u +%F)" -allow-public-write \
  | tee .agents/runtime/publica-lote.log
./tools/check-onda-avanca --depois --minimo 1 --rotulo "lote-acordaos"
nice -n 19 ./tools/generate-brotli-static --jobs 4
./tools/sweep-sitemap-carencia-expirada --seco | tail -3
./tools/reload-wiki-server
```

**`timeout 3600`**: a onda usa 1800 s para o corpus de 11.106; este publica
~13.600. A publicação é **content-addressed** — a última mediu 10.040 páginas
INALTERADAS contra 28 reescritas —, então o custo é o das novas, mas o orçamento
tem de ter folga e o tempo real entra no DEPOIS.

**A ORDEM `publicar → varrer → reiniciar` NÃO SE INVERTE.** `publish-v2-direct`
é quem varre shard de carência vencida; reiniciar antes de publicar, depois de
07:50Z, encontra `pages-0094.xml` vencido e `publishedmanifest.Validate` recusa
no **boot** — "é o portal fora do ar", nas palavras do próprio arquivo
(publishedmanifest.go:495-513). O `sweep --seco` entre a publicação e o reinício
é a prova de que a janela fechou.

**DEPOIS**

| leitura | esperado |
|---|---|
| `wc -l published_manifest.jsonl` | 11.106 + N `DERIVADO` |
| `check-onda-avanca --depois` | exit 0, `novas: N`, `sumiram: 0` |
| `sweep --seco` | **`0 vencido(s)`** e **0 vencendo em menos de 48h** |
| `reload-wiki-server` | `OK: as N rota(s) ... (Xs até servir)` — 32 s e 23 s foram os boots medidos |
| `./tools/go-modern run ./cmd/check http-smoke` | exit 0 (isolado: `os.MkdirTemp` + `NewParaVerificacao`) |
| `./tools/check-served-vs-manifest` | exit 0 |
| `./tools/check-public-sem-lixo` | exit 0 |
| `./tools/check-csp-style-hashes` | exit 0 (orçamento declarado 20 s) |

**SE NÃO VIER**
- publicador **exit != 0** → **PARE, NÃO reinicie**. A transação escreve sitemap
  e manifesto em momentos distintos; interrompida, o disco fica com
  `published_manifest_sitemap_loc_without_manifest` e o boot **aborta** com
  `Restart=always` e `StartLimitIntervalUSec=0` — laço eterno, `OnFailure=`
  vazio, ninguém avisado. Leia `tail -40 .agents/runtime/publica-lote.log`,
  conserte, republique.
- `SIGTERM` durante a transação (unit oneshot, `KillSignal=15`,
  `TimeoutStopUSec=90s`): **não há `signal.Notify` em `cmd/publish-v2-direct`,
  `internal/publicrelease` nem `cmd/build`** — os defers não rodam, o lock fica
  órfão e `public/`+sitemap ficam a meio caminho. Se acontecer: `tools/publicar`
  remove lock com PID morto, e **republique** (o snapshot de rollback cobre 3
  arquivos e **não** cobre `public/`).
- `check-served-vs-manifest` vermelho em massa → hashes fora de sincronia.
  `publishedmanifest.Validate` no boot tem teto de **10 por código** e **25 no
  total** (publishedmanifest.go:1464-1470): mais que isso e o Go não sobe. Não
  reinicie; republique.

**ROLLBACK** Só para frente: republicar. Com a linha do CLAUDE.md ainda
desatualizada, o commit seguinte falha — o que é a razão de o passo 10 vir
imediatamente, e não "depois".

---

# PASSO 10 — A linha do contrato, o manifesto, e a estreia

**OBJETIVO** Fechar as três consequências que este bloco cria para os outros:
o teto do contrato, o manifesto não-commitado, e o buraco de estreia que
transformaria as N páginas novas nas próximas vítimas do P1b.

**ANTES**

```bash
./tools/check-contrato-vs-medicao ; echo "exit=$?"
grep -n "Estado atual" CLAUDE.md
git log --oneline -1 -- data/editorial/published_manifest.jsonl
python3 -c "
import json;d=json.load(open('/opt/wiki/data/editorial/first_published_at.json'))
print('chaves em first_published_at:',len(d.get('first_published_at',{})))"
```

Esperado **MEDIDO**: antes da publicação, exit 0 com
`published_manifest : 11106 linhas, 11106 unique_intent_id` e
`CLAUDE.md declara : 11039 páginas`. **Depois** da publicação do lote cheio,
**exit 1**. Último commit do manifesto: **2026-09-10 (315ac61b)** — **5 dias**
sem commit. `first_published_at.json`: **10.107** chaves contra 11.106 rotas.

**AÇÃO**

```bash
# 10a. a linha do contrato — EDIÇÃO PONTUAL, nunca rewrite (o bloco P0 edita o
#      MESMO arquivo; rewrite apagaria o trabalho dele)
#      trocar SÓ os dois campos da linha:
#      "Estado atual (medido em AAAA-MM-DD): N.NNN páginas públicas no ar"
./tools/check-contrato-vs-medicao ; echo "exit=$?"   # tem de voltar a 0 JÁ, pelo disco

# 10b. commitar o manifesto — é DAQUI que a estreia se deriva
#      pathspec MEDIDO: os três já são commitados juntos pelos commits de deploy
#      (315ac61b, b8c5fc65, 09f40536). content/pages.json tem 84.122.261 B e está
#      marcado `-diff` no .gitattributes (o git imprime "Binary files differ"),
#      então o commit é grande mas o diff não vai para o contexto de ninguém.
#      Está ` M ` desde 2026-09-10; a publicação de agora é quem o reescreveu,
#      logo é desta sessão que ele sai.
git add data/editorial/published_manifest.jsonl
git add content/pages.json
git add data/ops/page_content_revision.jsonl
git commit -F .agents/runtime/msg-manifesto-lote.txt -- \
  data/editorial/published_manifest.jsonl content/pages.json data/ops/page_content_revision.jsonl

# 10c. AGORA a estreia enxerga o commit
python3 tools/generate-first-published-at --dry-run
python3 tools/generate-first-published-at
git add data/editorial/first_published_at.json
git commit -F .agents/runtime/msg-estreia.txt -- data/editorial/first_published_at.json

# 10d. e a linha do contrato entra no mesmo movimento
git add CLAUDE.md
git commit -F .agents/runtime/msg-contrato.txt -- CLAUDE.md
```

**Por que 10b ANTES de 10c, e não o contrário**: `generate-first-published-at`
percorre `git log --reverse -- data/editorial/published_manifest.jsonl` e anota
em qual commit cada `unique_intent_id` aparece pela **primeira** vez (linhas
52-62 e 130-133). **Rota que não está em commit nenhum não tem estreia
recuperável** — e é exatamente isso que produziu as **44 rotas sem histórico**
que a varredura de risco mediu. Sem 10b, as N páginas deste bloco entram nesse
balde e, na próxima publicação, recebem `datePublished = hoje` outra vez, que é o
P1b se reproduzindo por minha causa.

**Por que 10a ANTES de qualquer commit**: `check-contrato-vs-medicao` é
**incondicional** no pre-commit e lê a **worktree**. Com a linha velha no disco,
10b já falharia. Editar o arquivo destrava **antes** de commitar — o commit é a
formalização, não a correção.

**DEPOIS**

| leitura | esperado |
|---|---|
| `./tools/check-contrato-vs-medicao` | exit **0**, `CLAUDE.md declara : <N novo>` |
| `generate-first-published-at --dry-run` | `intents com data recuperada` ≥ **11.106 + N** |
| `git status --porcelain data/editorial` | **vazio** |
| `./tools/check-untracked-product-inventory` | exit 0 |
| `internal/contract/misc/peer_governance_test.go` | só se você tocou a §10 do CLAUDE.md — não é o caso aqui |

**SE NÃO VIER**
- `check-contrato-vs-medicao` com "não declara volume em forma verificável" →
  você quebrou o formato. O regex é
  `Estado atual[^:]*:\s*\*{0,2}([\d.  ]+)\s*páginas? públicas?` (tool:53-55).
  Mantenha **exatamente** "Estado atual (medido em AAAA-MM-DD): N.NNN páginas
  públicas no ar."
- O gate varre **também `GOAL.md` e `AGENTS.md`** (`CONTRATOS_EXTRA`, via
  `varre_contrato_extra`). Se ele reprovar numa **linha de GOAL.md ou
  AGENTS.md**, isso **não é deste bloco**: é do P0. Registre a linha exata em
  `docs/goal/MAESTRO_CODEX_LOG.md` e **não toque** — editar contrato de outra
  frente no meio de uma publicação é como se apaga trabalho concorrente.
- Se você tocar a **§10** do CLAUDE.md (governança entre pares), o contrato
  manda rodar `./tools/go-modern test -count=1 ./internal/contract/misc/`
  (BUG-171: a condensação de `64832bdd` apagou o parágrafo e deixou o teste
  vermelho). A linha do volume está na **§3** — não é o caso, mas confira antes
  de commitar.
- `generate-first-published-at` ainda com 10.107 → o commit de 10b não pegou o
  manifesto. `git log --oneline -1 -- data/editorial/published_manifest.jsonl`.

**ROLLBACK** Uma linha, para frente. Se o número declarado ficar errado, corrija
a linha e recommite; o gate mede o disco e responde em < 1 s.

---

# PASSO 11 — Borda: purga dirigida e reaquecimento

**OBJETIVO** Fazer a descoberta chegar aos bots sem jogar fora o aquecimento do
acervo.

**ANTES**

```bash
tail -2 data/ops/edge_cache_purge.jsonl
grep -E 'purgando|nada a purgar' .agents/runtime/publica-lote.log
./tools/check-edge-discovery-freshness ; echo "exit=$?"
curl -s -o /dev/null -D - \
  -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' https://wikijuridica.com.br/sitemap.xml | grep -iE 'cf-cache-status|age|cache-control'
```

**O que precisa de purga, e o que não precisa** — e a distinção é medida:

| artefato | precisa purgar? | porquê |
|---|---|---|
| as N rotas NOVAS | **NÃO** | nunca estiveram no cache; `s-maxage` só prende o que já foi servido. A primeira leitura vem `MISS` (verificado no passo 6) |
| `/sitemap.xml`, `/sitemaps/pages-*.xml` | **SIM** | mudaram, e é por eles que o bot descobre |
| `/`, `/feed.xml`, `/rss.xml`, `/robots.txt`, `/llms.txt`, `/llms-full.txt` | **SIM** | são os 7 artefatos de descoberta que a onda já purga (run-daily-content:877-878) |
| `/jurisprudencia/` (índice de área) e a gêmea `/jurisprudencia/index.md` | **SIM** | o índice de área lista **todos** os membros (§7 do contrato) e acabou de ganhar N |

**AÇÃO**

```bash
# 11a. ORIGEM primeiro — a borda repopula DA ORIGEM
./tools/purge-origin-cache --rota /jurisprudencia/index.md
nice -n 19 ./tools/warm-origin-cache --rps 80 --concorrencia 8 | tail -3
# 11b. lista explícita, com --teto-por-url = tamanho da lista
# um CAMINHO por linha (a ferramenta prefixa a base: `base + c if c.startswith("/")`)
python3 - > .agents/runtime/purga-descoberta-acordaos.txt <<'PY'
import glob, os
alvos = ["/", "/sitemap.xml", "/feed.xml", "/rss.xml", "/robots.txt",
         "/llms.txt", "/llms-full.txt", "/jurisprudencia/", "/jurisprudencia/index.md"]
alvos += ["/sitemaps/" + os.path.basename(p)
          for p in sorted(glob.glob("/opt/wiki/public/sitemaps/pages-*.xml"))]
print("\n".join(alvos))
PY
wc -l .agents/runtime/purga-descoberta-acordaos.txt   # esperado ~66 (57 shards ativos MEDIDO + 9)
LISTA=.agents/runtime/purga-descoberta-acordaos.txt
TETO="$(( $(wc -l < "$LISTA") + 1 ))"
./tools/purge-edge-cache --de-arquivo "$LISTA" --teto-por-url "$TETO" --dry-run
./tools/purge-edge-cache --de-arquivo "$LISTA" --teto-por-url "$TETO"
# 11c. reaquecer só o que foi purgado
./tools/warm-edge-cache --de-arquivo "$LISTA" --rps 12 --concorrencia 4
# 11d. anunciar
timeout 600 python3 tools/generate-indexnow-incremental-submit 2>&1 | tail -4
echo "exit real=${PIPESTATUS[0]}"
```

**Três armadilhas, todas já catalogadas e todas ativas aqui:**

1. **`--teto-por-url` default é 3000 e degrada em SILÊNCIO para
   `purge_everything`** (`tools/purge-edge-cache:137`, `:209`). Passar o teto
   igual ao tamanho da lista é o que impede a purga total, que jogaria fora
   ~870 s de aquecimento.
2. **Purga só por `--tag` quebra com `NameError` no caminho de SUCESSO**
   (`purge-edge-cache:249` usa `alvos`, atribuído só dentro de `if seletivo:`
   em `:191-196`). Enquanto não for corrigido, **toda purga por tag precisa de
   pelo menos um `--url` junto** — e este runbook usa `--de-arquivo`, que não
   cai nesse ramo.
3. **Origem antes de borda.** Invertido, a borda repopula o Tiered Cache com o
   conteúdo **VELHO** — medido em 2026-09-05: `age 0`, `HIT`, `campos=0`, cinco
   tentativas seguidas; com a ordem certa, `campos=3` de primeira.

E **leia o ledger antes**: se o próprio publicador já gravou `scope: "tudo"` em
`data/ops/edge_cache_purge.jsonl`, purgar de novo é desperdício.

**DEPOIS**

```bash
curl -s -o /dev/null -D - -A 'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; sonda-interna)' \
  -H 'X-Warming-Request: true' https://wikijuridica.com.br/sitemap.xml \
  | grep -iE 'cf-cache-status|age'
curl -s -A '...' -H 'X-Warming-Request: true' https://wikijuridica.com.br/sitemap.xml \
  | grep -c '<loc>'
./tools/check-edge-discovery-freshness ; echo "exit=$?"
tail -1 data/ops/edge_cache_purge.jsonl
tail -1 data/ops/indexnow_direct_submissions.jsonl
```

| leitura | esperado |
|---|---|
| `cf-cache-status` do sitemap | **MISS** logo após a purga, **HIT** com `age` pequeno após o warm |
| `<loc>` no índice de sitemap | número de shards ativos (era **57** MEDIDO; sobe com o lote) |
| `check-edge-discovery-freshness` | exit 0 |
| `edge_cache_purge.jsonl` última linha | `scope` = "N URL(s) em M lote(s)", **nunca** "tudo" |
| `indexnow_direct_submissions.jsonl` última | `http_status 200`, `success true`, `ownership_proof_verified_over_http true` |

**SE NÃO VIER**
- `cf-cache-status: HIT` com `age` grande no sitemap depois da purga → a purga
  não alcançou. Leia o `scope` gravado no ledger. **Não repita em laço**: purga
  repetida contra um defeito que não é de cache já escondeu a injeção do
  Cloudflare Web Analytics por dias.
- IndexNow com `exit != 0` → leia `PIPESTATUS[0]`, nunca o do `tail`.

**ROLLBACK** Purga não tem rollback e não precisa: o pior efeito é borda fria,
que `warm-edge-cache` desfaz. **Nunca** purgue "tudo" para consertar uma purga
dirigida.

---

# PASSO 12 — I5: o oneshot que repete tudo isso sozinho

**OBJETIVO** Tirar a publicação de acórdãos da onda diária e das mãos de
alguém, sem devolver decisão a ninguém.

**ANTES**

```bash
./tools/check-units-instaladas ; echo "exit=$?"
systemctl show wikijuridica-server -p Type -p Restart -p OnFailure -p WatchdogUSec -p StartLimitIntervalUSec
ls -la /etc/systemd/system/wikijuridica-cerebro.service
```

Esperado `MEDIDO pela varredura risco`: `check-units-instaladas` exit 0, 126
units, 3 avisos de cópia; `wikijuridica-server` com `OnFailure=` **vazio**,
`StartLimitIntervalUSec=0`, `WatchdogUSec=0`; units principais são **symlink**
para o repo — editar `ops/systemd/*.service` marca `NeedDaemonReload=yes` e
**para o deploy de todas as frentes** (`deploy-publico:282`, passo 0a/7).

**AÇÃO** — criar `tools/publicar-estoque-acordaos` (shell) + a unit:

**O LOCK: a memória desta máquina descreve um `/tmp/opt-wiki-commit.lock` que
NÃO EXISTE no repositório.** `MEDIDO`:
`grep -rn 'opt-wiki-commit.lock' tools/ .githooks/ ops/` → **vazio**; e
`.githooks/pre-commit` **não toma flock nenhum** (as únicas menções a lock são o
diagnóstico do guardião da rede social, que sai **75** e vira aviso). Portanto
**não referencie um lock que não existe**. O desenho correto, e ele segue a
letra do contrato ("commit de conteúdo, dado ou doc é **leve** — deve ser
frequente e concorrente, com retry curto no `index.lock`"):

- **lock próprio** `/tmp/opt-wiki-estoque-acordaos.lock` em volta do oneshot
  **inteiro** — exclusão contra uma segunda cópia de si mesmo, que o gatilho
  `.path` torna provável;
- **nenhum** lock pesado no corpo do oneshot: ele não toca Go. Tomar
  `/tmp/opt-wiki-agent-heavy.lock` por horas bloquearia a bancada diária e o
  commit Go de toda outra sessão;
- em cada `git commit`, **retry curto** no `.git/index.lock` (5 tentativas,
  espera crescente), porque o índice é compartilhado;
- o lock pesado aparece **só** nos passos 2 e 3 deste runbook, que são os que
  tocam Go.

```
TimeoutStartSec=18000   # DERIVADO da soma dos tetos abaixo (13.590 s) + 32% de folga.
                        # Sem isto a unit é morta no meio da transação por SIGTERM,
                        # e NÃO HÁ signal.Notify em cmd/publish-v2-direct: os defers
                        # não rodam, o lock fica órfão e public/+sitemap ficam parciais.

ExecStart, na ordem, com os tetos:
  1. flock -n /tmp/opt-wiki-estoque-acordaos.lock (exclusão contra si mesmo)
  2. ./tools/go-modern run ./cmd/generate-writeback-extracoes -raiz /opt/wiki   (600 s)
  3. ./tools/go-modern run ./cmd/generate-acordao-pages -limite ${LIMITE:-300} (2400 s)
  4. ./tools/check-shard-preservation                                  (PARA se falhar)
  5. ./tools/go-modern run ./cmd/check text-truncation                 (PARA)
  6. ./tools/go-modern run ./cmd/check derived-body-repetition         (PARA)
  7. git add <portfolio exato> ; git commit -F <arquivo>               (comandos separados)
  8. ./tools/check-v2-portfolio-pairing                                (PARA)
  9. git add <v2_pages exato>  ; git commit -F <arquivo>
 10. python3 tools/generate-v2-publication-severity --write            (900 s)
 11. ./tools/generate-page-content-revision                            (900 s, NÃO para)
 12. ./tools/check-onda-avanca --antes --rotulo "estoque-acordaos"
 13. ./tools/go-modern run ./cmd/publish-v2-direct -reviewed-at <UTC> -allow-public-write (3600 s, PARA com exit 2)
 14. ./tools/check-onda-avanca --depois --minimo 1
 15. ./tools/generate-brotli-static --jobs 4
 16. ./tools/sweep-sitemap-carencia-expirada --seco   (exige 0 vencidos ANTES do 17)
 17. ./tools/reload-wiki-server
 18. ./tools/check-publicado-no-ar --desde-ledger --gravar
 19. purga dirigida de descoberta + warm (passo 11)
 20. python3 tools/generate-indexnow-incremental-submit                (600 s)
 21. git add published_manifest + pages.json ; commit
 22. python3 tools/generate-first-published-at ; git add ; commit         (300 s)
 23. ./cmd/generate-lei-artigo-pages -limite ${LIMITE_LEIS:-60}          (2400 s, passo 13)
 24. ./tools/measure-coorte-de-publicacao --coorte-de <as novas>
```

**A soma dos tetos, para o `TimeoutStartSec` acima** `DERIVADO`:
600 + 2400 + 300 + 300 + 900 + 900 + 3600 + 900 + 90 + 300 + 600 + 300 + 2400 =
**13.590 s (3 h 47 min)**. `TimeoutStartSec=18000` dá 32% de folga. O tempo real
da primeira execução entra no ledger e **substitui** este número — se a execução
real encostar no teto, o conserto é indexar as assinaturas do anti-molde
(MinHash/banda), **nunca** esticar o teto ("lentidão em 10k é bug P0, e é
proibido corrigir aumentando timeout").

**O que o oneshot NÃO pode ter, e cada um tem causa medida:**

- **`SuccessExitStatus=0 1` ou `=1`**: mascara o exit 1. Prova viva `MEDIDA`:
  `wikijuridica-daily-content.service` da execução de hoje tem
  `ExecMainStatus=1` **e** `Result=success`, e `OnFailure` **não** disparou. São
  **22** units com máscara hoje (`=0 1` ×12, `=1` ×7, `=0` ×2, `=75` ×1).
- **`WIKI_DEPLOY_PERMITE_ESTOQUE_SUJO=1` por padrão**: publicaria trabalho
  não-commitado de outra sessão (acidente de 2026-08-29, 158 shards a meio
  caminho).
- **o lock pesado da bancada**: `wikijuridica-qualidade-diaria.service:19` toma
  `/tmp/opt-wiki-agent-heavy.lock` no próprio `ExecStart` e o segurou **60 min
  42 s** hoje (04:48:12→05:48:54). O oneshot usa lock **próprio**, e `flock -w`
  **espera sem spin** (`until` sem sleep é busy-wait: 82% de um núcleo atrasando
  o job esperado).
- **`Restart=` num oneshot**: a publicação não é idempotente a meio caminho.

**O que o oneshot PRECISA ter:**

- `OnFailure=wikijuridica-alerta@%N.service` e **nenhuma** máscara de exit;
- `Type=oneshot`, `TimeoutStartSec=` maior que a soma dos tetos;
- **gatilho por `.path`**, não só por `.timer`: `PathChanged=` sobre
  `data/corpus/jurisprudencia/stj-espelhos/manifest.jsonl` — o estoque é
  consequência da coleta, não do relógio;
- `.timer` de segurança com `OnCalendar` **antes de 01:00 UTC** — não por
  calendário, mas porque **97% dos primeiros contatos do gptbot caem em
  01h–02h UTC** `MEDIDO`, e publicar às 07h UTC é 18 h de espera
  auto-infligida (§ passo 7).

**DEPOIS**

```bash
sudo -n systemd-analyze verify ops/systemd/wikijuridica-estoque-acordaos.service
./tools/check-units-instaladas ; echo "exit=$?"
./tools/check-units-alarme ; echo "exit=$?"
systemctl show wikijuridica-estoque-acordaos.service -p SuccessExitStatus -p OnFailure -p Type
```

Esperado: `check-units-instaladas` exit 0 e **sem** `NeedDaemonReload` pendente
(senão o deploy de **toda** frente para); `check-units-alarme` exit 0 com a
unit nova **exigindo** `OnFailure` e **tendo**; `SuccessExitStatus` **vazio**.

**SE NÃO VIER** `check-units-instaladas` reprovando por `daemon_reload` →
`sudo systemctl daemon-reload`. As duas outras regras dele valem aqui:
`notify_binario` (ExecStart sem `NOTIFY_SOCKET` nunca manda `READY=1`) e
`socket_binario` (binário sem `LISTEN_FDS` = `EADDRINUSE` em laço com a porta em
`LISTEN`) — não se aplicam a um oneshot, mas se aplicam se alguém "melhorar" a
unit para `Type=notify`.

**ROLLBACK** `systemctl disable --now` a unit nova + `daemon-reload`, e a
publicação volta a ser manual por este runbook. Nada do que já foi ao ar muda.

---

# PASSO 13 — P8: lei-artigo deixa de ser órfão, e o agravo vira agregado

**OBJETIVO** Fazer os **49.807** registros hoje barrados por rótulo de classe
renderem conteúdo — como **evidência agregada** nas páginas de artigo de norma,
que é onde o próprio gerador de acórdãos diz que eles pertencem.

**ANTES**

```bash
cd /opt/wiki
grep -n "generate-lei-artigo-pages" tools/run-daily-content ops/systemd/*.service | grep -v '^.*#'
wc -l data/editorial/v2_pages/leis-motor-01.jsonl
ls -la data/editorial/motor/tier_a_artigos.jsonl
nice -n 19 ./tools/go-modern run ./cmd/generate-lei-artigo-pages -seco -limite 5000 \
  > .agents/runtime/lei-artigo-seco.log 2>&1 ; echo "exit=$?"
grep -n "A classe processual mais frequente" .agents/runtime/lei-artigo-seco.log | head -3
```

Esperado `MEDIDO`: **zero** invocação real (só comentários em
run-daily-content:446-447) → órfão confirmado; `leis-motor-01.jsonl` com **38**
linhas, mtime 2026-09-10 (já rodou à mão alguma vez); a frase
"A classe processual mais frequente é ..." sai de `main.go:1481`.

**MEDIÇÃO QUE MUDA O DESENHO** `MEDIDO por leitura`: o laço de indexação por URN
(main.go:483-508) **não tem** filtro `procedimental()` — ele já conta **todo**
registro, agravo inclusive, em `a.Classes[nome]++`. Ou seja: **o agravo já é
contador hoje**. "Promover a conteúdo agregado" é um delta concreto, não uma
ligação nova.

**AÇÃO**

1. **O delta de conteúdo** — acrescentar, na página de artigo, um bloco que
   diga o que os agravos **decidiram**, não só quantos são. Só afirmação
   verificável por contagem, na linha do que o gerador já faz:
   - quantos dos N julgados que invocam o artigo são de **mérito** e quantos de
     **cabimento**, pela classe EXTERNA do passo 3 (a única régua medida);
   - **NÃO** afirmar "índice de reforma", "chance de êxito" nem nada que
     dependa do classificador de dispositivo que eu retratei (F8);
   - a redação sai do gerador, nunca à mão.

2. **Ligar o produtor** — acrescentar ao oneshot do passo 12 (não à onda
   diária, que já está no teto de 900 s por gerador):
   `./cmd/generate-lei-artigo-pages -limite ${LIMITE_LEIS:-60}`, e confirmar que
   ele usa `internal/tetodelote` como os outros cinco (`grep -n tetodelote
   cmd/generate-lei-artigo-pages/main.go` — **A MEDIR**; se não usar, é o mesmo
   defeito do passo 2 e a correção é a mesma).

3. **Gate a jusante** — o produtor não pode voltar a ser órfão: acrescentar
   `check-derived-authorial-floor` e `text-truncation` logo depois dele no
   oneshot, com `PARA`.

**DEPOIS**

| leitura | esperado |
|---|---|
| `wc -l data/editorial/v2_pages/leis-motor-01.jsonl` | 38 + o que acrescentar `A MEDIR` |
| `./tools/generate-page-content-revision --purge-targets` | lista **não vazia** para as páginas de artigo alteradas |
| `check-lastmod-causalidade` | exit 0 |

**A DIFERENÇA QUE ESTE PASSO TEM DE TODOS OS OUTROS, e é o maior risco de SEO do
bloco:** o texto novo entra em `body_sections`, que **está** em
`CAMPOS_DE_CONTEUDO` (`generate-page-content-revision:185`). Logo
`content_sha256` muda, a **re-datação é VERDADEIRA**, `lastmod` avança e o
sitemap re-anuncia — em até **3.481** páginas `DIAGNÓSTICO`.

- **`--ressemear` é PROIBIDO nesta passada.** Suprimir a re-datação esconderia do
  buscador conteúdo que **de fato** mudou (§1 e §6 do contrato).
- Agrupe **todas** as mudanças de corpo numa publicação só. A publicação seguinte
  zera `mtime` e `ETag` de tudo, e os bots que revalidam rebaixam o acervo junto
  (medido duas vezes com o `meta-externalagent`).
- Meça a taxa de 304 depois. `tools/check-efeito-nos-bots` exige **14 dias PRÉ +
  14 POS** e ≥100 requisições autenticadas em cada janela — o que é a "janela de
  horas" proibida, elevada a semanas. **O atalho existe e não está no runbook de
  ninguém**: `WIKI_EFEITO_NOS_BOTS_LOG=<fixture>` exercita o veredito contra log
  **já gravado**, sem esperar bot nenhum. Use-o, e mantenha a série de 14 dias
  como leitura de longo prazo — **encurtar a janela** geraria alarme falso, que é
  o que faz alguém desligar o gate.

**SE NÃO VIER** `--purge-targets` devolvendo **zero** para páginas que você sabe
que mudaram de corpo → o hash não viu a mudança. Isso significa que o texto novo
caiu **fora** de `CAMPOS_DE_CONTEUDO` (num heading de navegação, por exemplo) e a
página **não** será re-anunciada. Confira onde o gerador escreveu antes de
concluir qualquer coisa sobre a borda.

**ROLLBACK** Para frente: regerar sem o bloco e republicar. **Não há rollback
para o `lastmod` já anunciado** — por isso o agrupamento numa publicação só é
requisito, não estilo.

---

# PASSO 14 — P7: os dois enforcers do DataJud, com prova por mutação

**OBJETIVO** Fazer a trava do DataJud casar **diretório**, não começo de nome, e
provar que o filtro de `nivelSigilo` é o que sustenta a publicidade.

**ANTES**

```bash
cd /opt/wiki
sed -n '4493,4516p' internal/codex2policyenforcement/policy.go
ls -d internal/datajud* internal/codex2datajud* 2>&1
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock \
  | grep -c codex2policyenforcement
./tools/go-modern test -count=1 ./internal/codex2policyenforcement/
./tools/go-modern test -count=1 ./internal/datajudfila/
```

Esperado `MEDIDO`: os diretórios reais são **`internal/datajudfila`**,
**`internal/datajudtpubatch`**, **`internal/codex2datajudobservations`**,
**`internal/codex2datajudfrontiersignalreport`** — `internal/datajud` **não
existe**, e o prefixo sem barra casa todos eles **por acidente**;
`codex2policyenforcement` **fora** do grafo do validador (contagem **0**) → sem
reatestação; as duas bancadas verdes (baseline).

**AÇÃO**

1. **Enforcer de runtime** (`policy.go:4507-4515`) — trocar os dois prefixos sem
   barra por **diretórios nomeados**, exatamente como o vizinho do SQLite no
   mesmo arquivo já faz:

```go
return strings.HasPrefix(rel, "internal/datajudfila/") ||
       strings.HasPrefix(rel, "internal/datajudtpubatch/") ||
       strings.HasPrefix(rel, "internal/codex2datajudobservations/") ||
       strings.HasPrefix(rel, "internal/codex2datajudfrontiersignalreport/") ||
       strings.HasPrefix(rel, "cmd/social/") ||
       strings.HasPrefix(rel, "internal/consultapublica/") ||
       (strings.HasPrefix(rel, "cmd/") && strings.Contains(rel, "datajud"))
```

2. **O teste** (`datajud_trava_estrutural_test.go`) — três acréscimos:
   - `TestTravaDoDatajudPermiteConsumidorLegitimo` passa a nomear os **quatro
     pacotes reais** (hoje lista `internal/datajudtpubatch`,
     `internal/codex2datajudobservations`,
     `internal/codex2datajudfrontiersignalreport`, `cmd/social`,
     `cmd/import-datajud-tpu-catalog` — **falta `internal/datajudfila`**, que é
     onde vive `Sigiloso()`);
   - **controle negativo novo**, no molde exato de
     `TestSQLiteAllowlistCasaDiretorioInteiro`:
     `internal/datajudrender`, `internal/datajudpublicador`,
     `internal/codex2datajudhtml` **não** podem ser autorizados. Hoje os três
     **seriam**, e é esse o defeito;
   - o `TestCaminhoDePublicacaoNaoImportaDatajud` já varre por AST e fica como
     está.

3. **Prova por mutação do filtro de sigilo** — o que de fato protege:
   `internal/datajudfila/cliente.go:106-108`

```go
func (r Resposta) Sigiloso() bool { return r.NivelSigilo > 0 }
```

   Mutante: `return false`. **Tem de ficar VERMELHO** em, no mínimo:
   - `internal/datajudfila/superficie_test.go:476-481` (`nivelSigilo 0` não é
     segredo; `nivelSigilo > 0` é);
   - `internal/datajudfila/superficie_test.go:214` e `:234` (a transição
     `NivelSigilo 3 → 0`);
   - e nas **três camadas independentes** que `cmd/social/processo.go:59-62`
     declara: `Consulta` não copia o corpo, `Guarda` não persiste,
     `DetalheDaResposta` recusa traduzir — mais os dois desfechos de
     `cmd/social/processotela.go:164` e `:340`.

   **Se alguma dessas camadas ficar VERDE com o mutante, ela não está provada** —
   e a correção é acrescentar o teste que falta, não relaxar a afirmação.
   Rode e **cole a saída vermelha** antes de aplicar qualquer mudança.

4. **Baseline** — o gate usa `ValidateWithBaseline`. Mexer na lista sem
   regenerar deixa vermelho:

```bash
./tools/go-modern run ./cmd/generate-codex2-policy-enforcement \
  --metadata-only --allow-approved-runtime-dependency --no-publication
./tools/go-modern run ./cmd/check-codex2-policy-enforcement
```

5. Commit único, `add` e `commit` separados, sob `flock`.

**DEPOIS**

| leitura | esperado |
|---|---|
| `./tools/go-modern test -count=1 ./internal/codex2policyenforcement/` | PASS, com o controle negativo novo |
| `./tools/go-modern test -count=1 ./internal/datajudfila/` | PASS |
| mutante `Sigiloso() → false` | **≥ 3 testes VERMELHOS**, em pacotes diferentes |
| `./tools/go-modern run ./cmd/check-codex2-policy-enforcement` | exit 0, **zero** `codex2_policy_datajud_import_scope_escape` |
| `./tools/go-modern build ./internal/... ./cmd/...` | sem erro |

**SE NÃO VIER**
- O gate acusa `datajud_import_scope_escape` num pacote legítimo → você esqueceu
  um dos quatro diretórios reais. A mensagem imprime `<arquivo>:<import>`; leia
  o caminho e acrescente **o diretório**, com barra.
- O mutante **não** fica vermelho em nenhuma camada → a trava é decorativa. Esse
  é o achado, e ele vale mais que a mudança: escreva o teste que faltava **antes**
  de tocar no enforcer.

**ROLLBACK** Regenerar o baseline e reverter a lista por edição para frente.
`internal/codex2policyenforcement` **não** está no caminho de serviço — os
chamadores são `cmd/generate-codex2-policy-enforcement`,
`cmd/check-codex2-policy-enforcement`, `cmd/generate/*` e
`internal/checks/checks.go:3499,7537,9312`; **nenhum** é `httpserver` nem
`cmd/server`. Este passo **não pode derrubar o portal**.

---

# 15. AS ESPERAS INEVITÁVEIS, COM NÚMERO E ATALHO

Nenhuma delas é passo do runbook. Todas são externas, medidas, e todas têm
atalho.

| espera | número medido | por que é externa | atalho |
|---|---|---|---|
| **TTL da borda no acervo** | `s-maxage=604800` = **7 dias**; leitura viva de hoje: `HIT`, `age 27291` | é a Cache Rule da Cloudflare | **rota nova não espera nada** (nunca esteve no cache — passo 6 mede `MISS`). Para artefato de descoberta: purga dirigida do passo 11 |
| **agenda de varredura do gptbot** | **97%** dos primeiros contatos em **01h–02h UTC** (n=3.608) | é o calendário de um terceiro | **mover a hora da publicação**, não esperar: o `.timer` do passo 12 dispara antes de 01h UTC. Publicar às 07h UTC custa **18 h** auto-infligidas |
| **perplexitybot** | 67% em **14h–15h** UTC; p50 no lote limpo **22,6 h** | idem | idem |
| **cloudflare-ai-search** | **1,6 h** p50, 897 de 898 rotas (99,9%) | é a CDN indexando o próprio cliente — pertence à tabela, nunca à manchete | nenhum necessário |
| **`crawl_coverage_state.paths_first_seen`** | timer 1×/dia, **01:11 local** ⇒ até **24 h** de atraso | é o nosso timer | `nice -n 19 python3 tools/measure-crawl-coverage` roda **sob demanda** (GraphQL) |
| **`data/ops/access/nginx-*.jsonl`** | timer de hora em hora (última 21:08, próxima 22:08) ⇒ ≤ **1 h** | é o nosso timer | `/var/log/nginx/wikijuridica/access.log` tem lag **ZERO** — a linha existe no instante da requisição. Use `LC_ALL=C` |
| **`check-efeito-nos-bots`** | exige **14 dias PRÉ + 14 POS** e ≥100 req autenticadas em cada janela | é o desenho do gate | `WIKI_EFEITO_NOS_BOTS_LOG=<fixture>` exercita o veredito contra log já gravado |
| **retenção do `httpRequestsAdaptiveGroups`** | **8 dias**, duro | é a Cloudflare | nenhum. É o **único** teto físico real de toda a frente |
| **carência de shard de sitemap** | **8 dias**; pages-0094/0095 vencem **2026-09-16T07:50Z** | é o nosso mecanismo, mas a data já correu | **publicar varre** (`cmd/publish-v2-direct`). `sweep --seco` responde em < 1 s |
| **bancada diária segura o flock pesado** | **60 min 42 s** hoje (04:48:12→05:48:54 local), próxima **04:47:17 -03** | outra unit | `flock -w` **espera sem spin**; o oneshot usa lock **próprio**, não o da bancada |
| **boot do Go depois do restart** | **32 s** e **23 s** medidos em 2026-09-15 | carrega 11 mil páginas em memória | `reload-wiki-server` espera **por predicado**, não por relógio (teto 90 s) |

---

# 16. AS PROVAS DESTE BLOCO — comando + número esperado

| # | prova | comando | número esperado |
|---|---|---|---|
| 1 | a cota acrescenta | `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/` | PASS; com o mutante `>= limite {break}`, `Acrescentadas()==0` e VERMELHO |
| 2 | AREsp não admite AgInt | mesmo teste | `classeExterna("AGINT NO ARESP")=="AGINT"`; **0 de 30** da amostra por stride menciona "agravo interno" |
| 3 | o estoque não encolheu | `./tools/check-shard-preservation` | exit 0 |
| 4 | não há colisão entre shards | `./tools/go-modern run ./cmd/check v2-cross-shard-collision` | exit 0 |
| 5 | intenção precede página | `./tools/check-v2-portfolio-pairing` | OK em **3,45 s** MEDIDO, `so_no_candidato` vazio |
| 6 | a onda acrescentou de fato | `./tools/check-onda-avanca --depois --minimo 1` | `novas: N`, `sumiram: 0` |
| 7 | coerência manifesto↔disco↔borda | `./tools/check-publicado-no-ar --de-arquivo <as novas>` | exit 0; `html_sha256` do `/api/v1/citar` == corpo da borda == disco |
| 8 | as 5 superfícies de máquina | idem, leituras 1–5 | mesmo sha nas 5; A2A com `A2A-Version: 1.0` e método `SendMessage` |
| 9 | o Go carregou o que publicamos | `./tools/reload-wiki-server --check` | exit 0 **depois** do reload (exit 1 **antes** é o esperado) |
| 10 | o boot não vai travar | `./tools/sweep-sitemap-carencia-expirada --seco` | **`0 vencido(s)`** |
| 11 | o contrato declara o número certo | `./tools/check-contrato-vs-medicao` | exit 0; `11.106 → N` MEDIDO ANTES |
| 12 | a estreia das novas é recuperável | `python3 tools/generate-first-published-at --dry-run` | `intents com data recuperada` ≥ 11.106 + N (era **10.107** MEDIDO) |
| 13 | a borda serve a descoberta nova | `curl -D - .../sitemap.xml \| grep cf-cache-status` | `MISS` pós-purga, depois `HIT` com `age` pequeno |
| 14 | a purga foi dirigida, não total | `tail -1 data/ops/edge_cache_purge.jsonl` | `scope` = "N URL(s)", **nunca** "tudo" |
| 15 | os bots acharam a coorte | `./tools/measure-coorte-de-publicacao --coorte-de <novas>` | cloudflare-ai-search p50 **1,6 h**; gptbot só na **borda** |
| 16 | nada saiu disfarçado | `./tools/go-modern test -count=1 ./internal/wikijuridicabot/` | `TestNenhumPontoDeSaidaSaiDisfarcado` PASS |
| 17 | o sigilo é o que protege | mutante `Sigiloso() → false` | **≥ 3** testes vermelhos em pacotes distintos |
| 18 | a trava casa diretório | `./tools/go-modern test -count=1 ./internal/codex2policyenforcement/` | controle negativo recusa `internal/datajudrender` |
| 19 | o produtor não é mais órfão | `grep -n generate-lei-artigo-pages tools/publicar-estoque-acordaos` | 1 ocorrência real (hoje: **0**) |
| 20 | a unit alerta quando falha | `./tools/check-units-alarme` | exit 0; `SuccessExitStatus` da unit nova **vazio** |

---

# 17. O QUE FICA NOMEADO COMO LACUNA (não é deste bloco, mas morde nele)

1. **A régua do anti-molde do gerador é estritamente dominada** pela do gate:
   3-gramas/dígitos neutralizados/limiar 0,70 contra 5-gramas/dígitos
   preservados/limiar 0,82 — dos 135 pares que ela recusa, a real aprova **135
   de 135**; sob a régua real o máximo da família é **0,5193** contra limiar
   0,70. Mata **1.405 páginas (29,5%)**. É **P4**; este bloco **registra o
   número e não toca**, para que um defeito publicado seja atribuível.
2. **Não existe ferramenta read-only que emita a lista de purga a partir do diff
   CRU de `html_sha256` do manifesto.** `rotas_com_bytes_novos()`
   (generate-page-content-revision:440-478) já computa, mas só está cabeada a
   `--desde-commit`, que **força re-datação** e é proibido na mesma passada.
   Sem ela, toda correção que o hash neutraliza fica sem lista de purga.
3. **`tools/deploy-publico` não tem modo seco** (só `--sem-republicar`,
   `--so-cache`, `--ressemear`, e os três mutam). `deploy-binario-go --seco`
   prova que o padrão é viável.
4. **`purge-edge-cache` quebra com `NameError` no caminho de SUCESSO** quando a
   purga é só por `--tag` (`:249` usa `alvos`, atribuído só em `:191-196`).
   Conserto de uma linha: `alvos = []` antes do ramo, com teste que exercite
   `--tag` sem `--url`.
5. **`deploy-publico:463` remove `.publish-v2-direct.lock` sem conferir vida do
   PID** — abre janela para dois publicadores concorrentes.
6. **Não há `signal.Notify` em `cmd/publish-v2-direct`, `internal/publicrelease`
   nem `cmd/build`**, e a unit é oneshot com `KillSignal=15`/
   `TimeoutStopUSec=90s`: SIGTERM no meio da transação não roda os defers.
7. **`writeRollbackSnapshot` não cobre `public/` nem `public/sitemaps/`** — é
   snapshot de metadado, não rollback transacional.
8. **`wikijuridica-server.service` não tem sonda de vivacidade que não dependa de
   `failed`**: `OnFailure=` vazio, `StartLimitIntervalUSec=0`, `WatchdogUSec=0`.
9. **`check-frescor-canal-diario` compara com "hoje" em UTC** contra
   `TOLERANCIA_DIAS_CADENCIA = 1`: a partir das 21:00 locais o canal queima a
   folga inteira só pelo fuso. Alarme falso latente toda noite.
10. **Nenhum gate mede `creation_time_upstream` das faixas de IP** —
    `check-bot-ip-ranges-frescor` mede só `fetched_at` e ficaria verde para
    sempre com lista upstream de uma década (`perplexitybot.json`:
    upstream 2025-02-07, **8 prefixos**).

---

# 18. O QUE O ADVISOR MUDOU

Duas chamadas. Nada do que ele disse contrariou uma medição minha; onde ele
apontou e eu medi, a medição **fortaleceu** o apontamento. Nove mudanças, todas
incorporadas:

**Primeira chamada (antes de escrever uma linha do runbook):**

1. **Derrubou meu excesso de cautela no AREsp.** Eu estava a caminho de exigir um
   oráculo rotulado à mão para separar AgInt — e o bloco nunca pediu admitir
   AgInt, só **separá-lo** do AREsp. Adotado: o passo 3 admite **só** o AREsp
   externo, mantém o AgInt barrado, e o que o contrato de fato exige é o **teste
   de falso positivo sobre amostra por stride**, que virou item 2 do passo 3.
2. **Promoveu a correção da cota de nota para passo 0.** Eu tinha o defeito
   documentado como achado (F2); ele apontou que o oneshot do P6 **morre na
   segunda partida** sem ele, e que corrigir depois exigiria remontar o shard.
   Virou o **passo 2**, antes de qualquer gravação.
3. **Mandou ler a semântica de `-limit` do publicador antes de desenhar o lote de
   travessia.** Li: é **recusado** com `--allow-public-write`
   (main.go:351-358), com o motivo escrito no próprio erro. Isso mudou a
   especificação do passo 5: a travessia é do lado do **gerador** (`-limite 5`),
   nunca do publicador.
4. **Mandou checar teto de leitura por arquivo antes de planejar rotação de
   shard.** Não há teto abaixo de 10 MB (só por linha e agregados de 64 MiB).
   Virou F9: **não rotacionar**, com o número (3.900 B/linha, ~9,7 MB) em vez de
   uma mudança de código sem necessidade medida.
5. **Mandou nomear o `file:line` da recusa por `nivelSigilo` antes de escrever
   "prova por mutação".** Achei: `internal/datajudfila/cliente.go:106-108`
   (`Sigiloso()`), com as três camadas declaradas em `cmd/social/processo.go:59-62`
   e os dois desfechos em `processotela.go:164` e `:340`. O passo 14 agora nomeia
   o mutante e os testes que têm de ficar vermelhos.
6. Apontou que o tempo de parede do gerador é **load-bearing** contra o teto de
   900 s da onda. Medi: **747,9 s** sob load 11,8–14,4 — cabe com 17% de folga,
   e é por isso que o oneshot tem orçamento próprio de 2.400 s.

**Segunda chamada (com o runbook escrito e o 2.488 medido):**

7. **Pegou um lock que não existe.** Eu escrevi "flock no lock de commit" apoiado
   na memória da máquina; `grep -rn 'opt-wiki-commit.lock'` devolve **vazio** e o
   `pre-commit` não toma flock nenhum. Reescrito: lock **próprio** para o
   oneshot, **retry curto no `.git/index.lock`** para os commits de dado (que é
   o que o contrato manda para commit leve), e o lock **pesado** só nos passos 2
   e 3, que tocam Go.
8. **Cobrou o número do `TimeoutStartSec`.** Somei os tetos: **13.590 s
   (3 h 47 min)** → `TimeoutStartSec=18000`. Sem esse número a unit morre no meio
   da transação por SIGTERM — e **não há `signal.Notify`** em
   `cmd/publish-v2-direct`, então os defers não rodam.
9. **Cobrou o pathspec do `content/pages.json`.** Medi: **84.122.261 B**, marcado
   `-diff` no `.gitattributes`, e já commitado junto com o manifesto pelos
   commits de deploy (315ac61b, b8c5fc65, 09f40536). Fica no pathspec do passo
   10b, com o tamanho e a razão escritos ao lado.

Mais três correções menores dele que entraram: marcar **onde o estado começa a
mudar** no passo 5 (5a e 5g, os dois); dizer que `check-contrato-vs-medicao`
varre **também GOAL.md e AGENTS.md** e que reprovação lá **não é deste bloco**; e
rebaixar a decomposição das recusas de `MEDIDO` para `DIAGNÓSTICO`, porque a
tabela não terminou de sair.

**O que ele elogiou e eu confirmo que importa**: `corpo max 700` é **exatamente**
`tetoPalavras` e o teto da banda do `verbete` — margem zero. Uma página a mais
de prosa no gerador (inclusive o bloco do passo 13) reprova a transação inteira.
Está no DEPOIS do passo 8 e no aviso do passo 13.
