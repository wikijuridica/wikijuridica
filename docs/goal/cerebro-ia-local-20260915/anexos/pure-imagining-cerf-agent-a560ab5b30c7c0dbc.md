# LACUNAS CRITICAS DE EXECUCAO — o que ainda pode quebrar

Seção final do plano. Seis lacunas investigadas, refutadas adversarialmente e
**re-verificadas nesta sessão contra o disco**. Tudo abaixo é leitura; nada foi
executado, editado nem commitado.

**Convenção de procedência, aplicada a cada número desta seção:**

- **[M]** — *medido nesta sessão*, contra `/opt/wiki` em HEAD `62d71de0`
  (2026-09-15 12:22:09 -03), índice do git **vazio** (`git diff --cached
  --name-only` = 0 arquivos), entre 22:35 e 22:55 de 2026-09-15.
- **[H]** — *herdado* do dossiê da lacuna indicada, **não re-medido aqui**. Vale
  como alegação verificada por quem a produziu, não como medição minha. Onde um
  [H] é load-bearing para um passo destrutivo, o passo traz o teste que o fecha
  (§10).

Um [H] nunca vira [M] por concordância entre dossiês. **Dois [H] caíram nesta
revisão** e estão retratados abaixo (§2, C4).

---

## 1. Tabela de vereditos

| # | Lacuna | Veredito | Consequência em uma linha |
|---|---|---|---|
| L1 | **escala-descoberta** — teto de churn conta rota nova como re-datação | **BLOQUEANTE** | `deploy-publico` sai com exit 1 **depois** de publicar, purgar, aquecer e anunciar ao IndexNow, e o laço se repete em todo deploy seguinte. |
| L2 | **travessia** — `lane = "informativa"` desliga três instrumentos | **BLOQUEANTE** | Consertar depois de publicar é atributo servido sem texto novo: obriga `--ressemear` sobre 2.488 rotas, re-data o acervo e re-anuncia tudo ao Googlebot. |
| L3 | **migracao-no-meio** — `public/` fora do backup por decisão escrita (**detalhe em §8**) | **BLOQUEANTE** | Perder ou reconstruir `public/` derruba o **boot do Go**, não só o acervo estático; com nginx `root public/` é queda total no dia um. |
| L4 | ~~família não nasce no canal de máquina~~ → **família nasce sem a seção de percursos** | **CONTROLADO com ressalva** *(era GRAVE; **retratado nesta revisão**, §2 C4)* | `publish-v2-direct --allow-public-write` **reinicia o servidor** (`main.go:2257-2264`), então a gêmea nasce viva; o que falta sem o deploy é o **passo 2.6**, e isso já é a L5. |
| L5 | **cadeia-topologica** — a Cadeia B (publicação v2) não está declarada e três passos faltam na onda | **GRAVE** | 67 de 67 rotas novas sem co-citação e sem tema social; 88 respostas 404 de bot medidas em 4 dias. |
| L6 | **concorrencia** — onda faz `git add` **por diretório** nos dois dirs que o P6 escreve, e publica | **GRAVE** | Shard deixado na worktree ao atravessar 04:20±15min ou 12:20 é commitado sob mensagem de onda e publicado sem decisão. |
| L7 | **grafo-atestacao** — ponto cego do `strictjson` na guarda de commit | **GRAVE** | Commit que toque só `internal/strictjson/*_test.go` passa verde e deixa a atestação stale: `ingest-v2-stock` recusa publicar e nenhum deploy passa. |
| L8 | **travessia** — nenhuma fase commitava os derivados da transação | **GRAVE** | `published_manifest.jsonl` M há 5 dias; é dele que o gerador de estreia do P1b deriva a data, então o P1b nunca sai do lugar. |
| L9 | **travessia** — canal STJ não carrega `nivelSigilo` e não há filtro de exceção taxativa | **GRAVE** | 10.414 de 10.414 (100,0%) com `nivel_sigilo` nulo; 8 casam Maria da Penha e não há recusa nomeada. |
| L10 | **travessia** — gerador órfão, `-limite` default 30, onda faria a estreia sozinha | **GRAVE** | Nada drena o poço; e se o runner entrar antes da geração manual, a onda estreia a família com 200 páginas em vez das 2.488. |
| L11 | **cadeia** — índice de co-citação sem nenhum detector de frescor | **GRAVE** | `check-percursos-fundamento-legal` sai **exit 0** contra índice 4 dias e 5.291 rotas atrás. |
| — | grafo: os 6 pacotes do plano estão no grafo do `v2ingest`? | **CONTROLADO** | **Medido: 0 de 6.** Evidência em §9 C-2 e §5. |
| — | sitemap: ordinal posicional desloca shards? | **CONTROLADO** | Registry ancora o número na **coorte**, não na posição. Evidência em §9 C-3. |
| — | IndexNow: teto de 1.000/dia? | **CONTROLADO** | `MAX_URLS=1000` é **por requisição**; 19.669 URLs num dia, 20 de 20 lotes aceitos. Evidência em §9 C-4. |
| — | borda / TTL / aquecimento | **CONTROLADO** | 2.488 = 207 s a 12 r/s; o orçamento usa 62,5% em qualquer escala. Evidência em §9 C-5. |
| — | revalidação em massa de bot | **CONTROLADO** | Acréscimo de rota não re-data as 11.118 existentes; 304 do Googlebot em 53–60%. Evidência em §9 C-6. |
| — | ovo-e-galinha no pareamento portfólio × páginas | **CONTROLADO** | `FINALIZED` (:33-34) só casa `v2_pages/`; commit 1 não aciona `check_page_product`. Evidência em §9 C-1 e §4. |
| — | Cadeia A (`authorial_mass_*`, a dos "31 dias") é tocada pelo P6? | **CONTROLADO** | Acoplamento **zero** medido. Evidência em §6. |
| — | snapshot de `data/ai/` para P4/P6 | **CONTROLADO** | `grep` no gerador por `data/ai` = **0**. Evidência em §7. |

---

## 2. Correções que esta verificação impôs aos dossiês

Quatro fatos **[M]** mudam passos que os dossiês davam por fechados. **C4 é uma
retratação**: derruba um GRAVE inteiro.

### C1 — `pageType` hoje é `"verbete"`, não `"julgado"`, e trocá-lo tem custo medido

Medido (`cmd/generate-acordao-pages/main.go:76-78`):

```
pageType     = "verbete"
practiceArea = "jurisprudencia"
lane         = "informativa"
```

`internal/v2ingest/validate.go:56-66` define o vocabulário que o ingest aceita:

```
wordCountBands = { "verbete":{350,700}, "pergunta":{400,800},
                   "guia_problema":{700,1400}, "procedimento":{500,1000} }
validLanes     = { "comercial":true, "informativa":true }
```

E `validate.go:617-623` reprova o que está fora:
`portfolio_lane_invalid` quando `!validLanes[record.Lane]`, e
`portfolio_page_type_invalid` quando o `page_type` não está em `wordCountBands`.

**Consequência medida, que nenhum dossiê nomeou:** `generate-acordao-pages` é
hoje **o único gerador derivado com valores que o `v2ingest` aceita**. Os cinco
irmãos usam `page_type` próprio (nenhum em `wordCountBands`) e lane
`derivada_de_fonte_oficial` (não está em `validLanes`). Medição no último run do
relatório (`data/ops/v2_ingest_report.jsonl`, run único
`v2-ingest-20260911T050000Z`, 11.185 linhas):

| lane | accepted | rejected |
|---|---|---|
| `comercial` | 3.803 | 1.304 |
| `informativa` | 4.181 | 556 |
| **`derivada_de_fonte_oficial`** | **0** | **1.335** |
| (vazio) | 0 | 6 |

`page_type` das 1.335: `tema_repetitivo` 1.074, `sumula` 112, `julgado` 60,
`noticia` 48, `diario-oficial` 41.

**Decisão (não devolvida ao dono):** troca-se **os dois**, e pelo motivo do L2 —
a lane liga três instrumentos que existem para esta família, e consertar depois
custa `--ressemear` sobre 2.488 rotas. `"julgado"` é o valor que a irmã que
publica decisão judicial (`stf-informativo-derivado-01`, medido no disco) já usa
para o mesmo objeto. O preço é conhecido e aceito: o pool reprovado pelo ingest
vai de 1.335 para 3.823 (+186%) — e o ingest **não está no caminho da
publicação** (`internal/v2publish/v2publish.go:179`, `PagesGlob =
"data/editorial/v2_pages/*.jsonl"`, lido direto).

**`"julgado"` foi conferido no mapa canônico antes de a decisão ser escrita [M]**
— é o que decide se o *fail-open* da R10 morde. `internal/content/content.go:310-331`:

```
"verbete": "wiki",   "sumula": "wiki",   "noticia": "noticia-juridica",
"diario-oficial": "noticia-juridica",    "julgado": "jurisprudencia",
"tema_repetitivo": "precedente",         "norma": "legislacao",
"pergunta": "pergunta",  "guia_problema": "artigo",  "procedimento": "artigo"
```

`"julgado"` **existe** e traduz para `"jurisprudencia"` — logo
`CanonicalPageType` devolve `ok=true` e `v2publish.go:347-350` **não** cai no
default `"artigo"`. E `content/legal_marketing_policy.json:11` fixa
`"allowed_page_types": ["artigo", "pergunta"]`, conferido contra
`internal/legalmarketingpolicy/policy.go:181`
(`cta_page_type_not_allowed`): `jurisprudencia` fica **fora**. O comentário de
`content.go:305-309` declara essa intenção por escrito — *"conteúdo derivado de
fonte oficial informa, não convida… a regra editorial é aplicada por ESTRUTURA,
não por lembrete"*.

**Isto reforça a decisão em vez de ameaçá-la:** com `pageType = "julgado"` o CTA
comercial passa a ser barrado por **dois** mecanismos independentes — a lane
(`CommercialCTAAllowed()`) **e** o `page_type` (allowlist) —, exatamente como nas
cinco irmãs. Hoje, com `"verbete"` → `"wiki"`, ele é barrado só pelo segundo,
porque a lane `informativa` é a que o L2 mostra estar errada.

**O que entra junto, obrigatoriamente, no mesmo commit:** o comentário de
`main.go:82-83` diz *"Banda do `verbete` em internal/v2ingest/validate.go:56"* e
`pisoPalavras=350 / tetoPalavras=700` é exatamente a banda `verbete` `{350,700}`.
Com `page_type = "julgado"`, `validate.go:674` deixa de casar e a banda vira
constante **local do gerador**. Manter o comentário como está é comentário que
mente sobre produção — a classe que a R1 do contrato manda corrigir. **Proibido
"consertar" editando `validate.go`: ele está dentro de `internal/v2ingest` e
arrastaria a atestação do grafo (§5).**

### C2 — o teto de churn tem uma válvula que os dossiês não nomearam, e a onda falha ao contrário do deploy

Lido em `tools/generate-page-content-revision:596-609`: a recusa só retorna 1
**quando `--redatacao-em-massa` vem vazio**. Com motivo declarado, imprime
`re-datacao em massa AUTORIZADA` e **segue**. E a isenção de `:596` cobre
`--ressemear` **e** `--purge-targets` (a R4 já corrigira isso).

O que muda o plano é a **assimetria entre os dois runners**, medida:

| runner | ordem | falha do gerador |
|---|---|---|
| `tools/run-daily-content:674` → `:684` | revisão **antes** do publish, **sem argumentos** | **não reprova a onda** (`:678-681`: "a onda segue, o carimbo fica velho") |
| `tools/deploy-publico:464` → `:1403` | publish **antes**, revisão **depois** | `grep -q RECUSADO` → **exit 1**, com o acervo já no ar, já purgado e já anunciado |

`revisao_args` (`deploy-publico:1398-1402`) carrega **só** `--ressemear` — o
deploy não sabe passar `--redatacao-em-massa`.

**Consequência:** a travessia publica pelo **deploy** (é ele que faz o passo 2.6,
§5). Logo herda o modo perigoso. **A L1 é pré-requisito duro da FASE 7 da
travessia** — não uma frente paralela.

### C3 — `internal/content` está DENTRO do grafo do `v2ingest`

Medido nesta sessão (`./tools/go-modern list -deps ./internal/v2ingest
./cmd/ingest-v2-stock`, 98 pacotes in-module, exit 0):

| DENTRO (atestação obrigatória) | FORA (atestação proibida) |
|---|---|
| `internal/content`, `internal/seo`, `internal/quality`, `internal/publishedmanifest`, `internal/lexml`, `internal/ptbrtext`, `internal/publicpath`, `internal/strictjson`, `internal/v2portfolioindex`, `internal/stockmanifest` | `cmd/generate-acordao-pages`, `cmd/publish-v2-direct`, `internal/httpserver`, `internal/v2publish`, `internal/sitemap`, `internal/shardpreserve`, `internal/render`, `internal/pagemarkdown`, `internal/htmlcontract`, `internal/legalmarketingpolicy`, `internal/v2bodyneardup`, `internal/checks`, `internal/cerebro`, `internal/ollama`, `internal/stjacordaos`, `internal/legalcocitation`, `internal/webanalytics` |

O dossiê do grafo listou `internal/content` como alvo do P1b sem notar que ele é
membro. A R7 corrigiu o símbolo: **`content.Page.FreshnessDate` não existe**;
é `LastModified()` em `internal/content/content.go:453` (grep por
`FreshnessDate` em `internal/` = **0 ocorrências**) [M]. Ou seja: **a única
função que o P1b naturalmente tocaria fica dentro do grafo.** Ver a regra em §5.

### C4 — RETRATAÇÃO: `publish-v2-direct` **reinicia** o servidor

O dossiê da travessia classificou como GRAVE que *"publish-v2-direct NÃO
reinicia o serviço (grep: zero systemctl/restart)"*. **É falso, e o grep que o
sustentava estava errado** [M]: `grep -c 'systemctl\|reload-wiki-server'
cmd/publish-v2-direct/main.go` devolve **4**, não zero.

- `cmd/publish-v2-direct/main.go:2257-2264` — sob `-allow-public-write`, chama
  `recarregarServidor(root, os.Stdout)`.
- `:2321-2334` — `recarregarServidor` executa `tools/reload-wiki-server`.
- `tools/reload-wiki-server:245` — `["sudo","-n","systemctl","restart",SERVICO]`,
  **restart real**, precedido de medição de divergência e seguido de verificação
  pelo mesmo predicado ("reiniciar não é provar").
- `tools/publicar:148-149` passa `--allow-public-write` — logo **o caminho
  `tools/publicar` também recarrega**.

E o comentário de `:2240-2256` documenta o defeito que o dossiê previu **como já
corrigido**, com a medição de origem: *"Medido logo após publicar 280 páginas:
markdown de página ANTIGA HTTP 200, markdown de página NOVA HTTP 404… o canal que
o ClaudeBot consome AGORA ficava cego justamente para o conteúdo mais fresco."*

**O que sobra de verdadeiro, e vale o passo:** `cmd/generate-legal-cocitation`
(passo 2.6) continua tendo **um único chamador**, `tools/deploy-publico:678` [M].
Publicar por `tools/publicar` põe as 2.488 rotas no canal de máquina **vivas** —
gêmea, `/api/v1`, MCP, A2A — porém **sem a seção "Percursos por fundamento
legal"**, que é degradação **aditiva e honesta** (artefato ausente ⇒ seção
omitida; `filtraPercursosServiveis` descarta destino não servível), **não 404**.

Isso é exatamente a L5, já medida (67 de 67). **A L4 deixa de ser um achado
próprio e vira um caso da L5** — e a razão para usar `deploy-publico` muda de
"senão dá 404" para "senão as 2.488 nascem sem percursos, como as 67 de hoje".
Continua sendo a razão certa; deixa de ser uma emergência.

---

## 3. As lacunas BLOQUEANTES e GRAVES, com evidência e passos

### L1 — BLOQUEANTE — o teto de churn conta rota nova como re-datação

**Evidência (lida nesta sessão):**
- `tools/generate-page-content-revision:135` — `TETO_CHURN_FRACAO = 0.05`
- `:569-572` — `entrada = anterior.get(caminho); if entrada is None: quantas_mudam += 1; continue`
- `:586-587` — `total_rotas = len(atual)` e `fracao = quantas_mudam / total_rotas` (denominador = conjunto **atual**, não o anterior)
- `:580` — `em_lote = quantas_mudam >= LOTE_MINIMO` (mesmo contador, consumidor oposto: é ele que degrada o carimbo para DIA)
- `:596` — `if not args.ressemear and not args.purge_targets and fracao > TETO_CHURN_FRACAO:`
- `:604` — `return 1`
- `tools/deploy-publico:1403-1410` — captura, `grep -q RECUSADO`, `exit 1`

**Aritmética, medida agora** (`content/pages.json` = **11.118** rotas;
`data/ops/page_content_revision.jsonl` = 11.116 linhas):

| lote de rotas novas | fração | veredito |
|---|---|---|
| 585 | 5,00 % | passa (teto exato) |
| 586 | 5,01 % | **recusa** |
| **2.488** (P6) | **18,29 %** | **recusa** |
| 1.405 (P4 sozinho) | 11,22 % | recusa |
| 3.893 (P6+P4) | 25,93 % | recusa |
| 4.763 (poço inteiro) | 29,99 % | recusa |

**Passos executáveis — L1 é o PASSO 1 de todo o plano:**

1. Editar `tools/generate-page-content-revision`, separando os dois consumidores
   que hoje compartilham `quantas_mudam`:
   - `:580` (`em_lote`) **continua** contando novas + re-datadas — é ele que
     evita 2.488 instantes idênticos ao segundo e o que faz
     `check-lastmod-causalidade` passar.
   - `:587` (`fracao`) passa a contar **só re-datadas** (`entrada is not None` e
     `content_sha256`/`served_sha256` mudou) sobre o denominador
     **`len(anterior)`**, nunca `len(atual)` — senão 600 re-datações reais
     (5,4 % das rotas datáveis) somem como 4,4 % sob um lote grande de novas.
2. No mesmo commit, o teste provado por mutação, com os **três** casos:
   - 600 novas + 10 re-datadas → **passa**;
   - 600 re-datadas sobre 11.118 no ledger (5,4 %) → **recusa**;
   - com a correção desligada, o primeiro caso volta a recusar — sem este
     terceiro o teste não testa a correção.
3. No mesmo commit, fechar o comentário que mente: `:132` afirma que o motivo de
   `--redatacao-em-massa` *"fica GRAVADO no ledger"*, e `:597-609` apenas o
   **imprime**; o registro (`:716-719`) tem só `path`, `content_sha256`,
   `revised_on`, `served_sha256`. **Gravar o motivo** (campo próprio ou ledger de
   eventos ao lado) — é o que torna auditáveis os dois contornos históricos
   (2026-08-29: 1.489 rotas = 13,40 %; 2026-09-10: 1.400 = 12,67 %).
4. Escrever no passo de publicação do P6 que **`--ressemear` é proibido para o
   lote**: ele é isento do teto (`:596`) e cala o ramo de IndexNow do deploy
   (`deploy-publico:1365`, `[ "$RESSEMEAR" -eq 0 ]`), mandando 2.488 páginas
   novas ao ar sem anúncio.
5. **Verificação depois:** `tools/generate-page-content-revision --dry-run`
   (write-free, retorna em `:764` antes de `escrita_atomica`/`grava_assinatura`)
   e conferir que imprime a contagem sem `RECUSADO`.

**Contingência se o passo 1 não couber na sessão:** fatiar em lotes de **no
máximo 585 rotas novas por deploy** (5 deploys para as 2.488). Não contar com
`--redatacao-em-massa`: o deploy não sabe passá-lo, e usá-lo à mão seria depois
do exit 1, com a borda já purgada e o passo 7 não executado.

---

### L2 — BLOQUEANTE — `lane = "informativa"` desliga três instrumentos

**Evidência (lida nesta sessão):**
- `cmd/generate-acordao-pages/main.go:78` — `lane = "informativa"`
- Os cinco irmãos, **no código e no disco**, declaram `derivada_de_fonte_oficial`:
  `generate-stj-tema-pages:1210`, `generate-stj-sumula-pages:707,1026`,
  `generate-stf-informativo-pages:777,1127`, `generate-noticia-pages:787,1418`,
  `generate-diario-pages:963,1366`; e a primeira linha de cada shard confirma:

| shard | n | lane | page_type |
|---|---|---|---|
| `stj-tema-derivado-01` | 1.074 | `derivada_de_fonte_oficial` | `tema_repetitivo` |
| `stj-sumula-derivada-01` | 112 | `derivada_de_fonte_oficial` | `sumula` |
| `stf-informativo-derivado-01` | 60 | `derivada_de_fonte_oficial` | **`julgado`** |
| `noticias-oficiais-01` | 59 | `derivada_de_fonte_oficial` | `noticia` |
| `diarios-municipais-01` | 51 | `derivada_de_fonte_oficial` | `diario-oficial` |

- Os três consumidores que a lane liga/desliga:
  - `internal/checks/derived_repetition.go:92` —
    `if p.Skipped || p.Lane != "derivada_de_fonte_oficial" || p.Opening == "" { continue }`
    → o gate anti-repetição fica **verde sem ler nenhuma das 2.488**;
  - `internal/checks/text_truncation.go:121,132` — `if p.Lane ==
    "derivada_de_fonte_oficial"` liga a régua extra de título derivado, e o
    título do acórdão é extraído do texto do tribunal;
  - `internal/seo/seo.go:126` — o comentário nomeia o defeito de "nunca
    distinguir a lane derivada_de_fonte_oficial (399 páginas)"; 2.488 páginas
    derivadas reportando `informativa` corrompem a única dimensão do GA4 que não
    sai de heurística.
- Propagação: `internal/v2publish/v2publish.go:379` — `CTALane:
  strings.TrimSpace(page.Lane)`.
- Nada reprova hoje: `internal/content/content.go:261,276-278` —
  `LaneConhecida` aceita `comercial`, `informativa` e `derivada_de_fonte_oficial`.

**Por que é BLOQUEANTE e não GRAVE:** consertar depois de publicar muda atributo
servido **sem mudar texto** → pela matriz do §6 obriga `deploy-publico
--ressemear` sobre 2.488 rotas, com re-datação do acervo e re-anúncio ao
Googlebot.

**Risco adjacente medido (R10, confirmado):** `internal/v2publish/v2publish.go:347-350`
faz *fail-open* — `pageType := "artigo"` quando `content.CanonicalPageType`
devolve `ok=false`, e `artigo` é um dos dois tipos que abrem CTA comercial. Hoje
não morde porque a lane derivada mantém `CommercialCTAAllowed()` falso
(`content.go:463-466`), **mas a FASE 1 edita exatamente essa constante**.

**Passos executáveis:**

1. `cmd/generate-acordao-pages/main.go:78` → `lane = "derivada_de_fonte_oficial"`.
2. `main.go:76` → `pageType = "julgado"` (o valor que a irmã do mesmo objeto já
   usa). **Nunca um valor inventado** (`"acordao"`, `"decisao"`): pelo fail-open
   de `v2publish:347-350` ele viraria `"artigo"` e poria 2.488 decisões
   judiciais sob a política de convite comercial.
3. No mesmo commit, corrigir o comentário de `main.go:82-83` — a banda 350/700
   deixa de ser a do `v2ingest` e passa a ser constante local do gerador (C1).
   **Não editar `internal/v2ingest/validate.go`** (grafo; §5).
4. `cmd/generate-acordao-pages/main_test.go:124` — substituir a asserção
   tautológica `pagina.Lane != lane` (compara o campo com a própria constante;
   fica verde para qualquer valor) por asserção dos **literais**
   `"julgado"` / `"derivada_de_fonte_oficial"`, mais um caso que leia os 5
   shards irmãos do disco e exija a mesma lane. **Prova por mutação:** com
   `lane = "informativa"` o teste tem de ficar **VERMELHO** (hoje fica verde; a
   bancada de 1.106 linhas tem zero ocorrência do literal).
5. **Verificação depois:**
   `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/`, e depois da
   publicação `./tools/go-modern run ./cmd/check derived-body-repetition` e
   `./tools/go-modern run ./cmd/check text-truncation` — que agora **leem** a
   família. (Nomes conferidos em `internal/checks/checks.go:451` e `:452`.)

---

### L4 — RETRATADO para CONTROLADO com ressalva — ver §2 C4

O achado original (rotas nascendo 404 no canal de máquina) **não se sustenta**:
`publish-v2-direct:2257-2264` → `:2321-2334` → `tools/reload-wiki-server:245`
fazem `systemctl restart` real sob `-allow-public-write`, e `tools/publicar:148-149`
passa essa flag [M]. O que resta é a falta do **passo 2.6**, cujo único chamador
é `deploy-publico:678` [M] — degradação aditiva, e já contabilizada na L5.

**Passo (mantido, com a razão corrigida):** a estreia fecha por
**`./tools/deploy-publico`**, **SEM `--ressemear`** (texto novo; a re-datação é
verdadeira) — não porque as rotas ficariam mortas, mas porque é ele que roda o
passo 2.6 na janela entre a republicação e o restart, e porque essa é a janela
que a L5 manda fechar de vez dentro da onda.
**Verificação depois:** o curl da gêmea no §4 (FASE 8), **com o controle
positivo** — sem ele, "sem seção" não distingue rota nova de instrumento quebrado.

---

### L5 — GRAVE — a Cadeia B não está declarada e três passos faltam na onda

**Evidência medida nesta sessão, por diferença de conjunto** (campo `path` do
manifesto, campo `public_path` do índice — os nomes foram lidos do primeiro
registro de cada arquivo antes de contar, para não repetir a armadilha
"varredura com campo inexistente", que na primeira tentativa me devolveu 0):

- `published_manifest.jsonl`: **11.106** no disco, **11.039** em HEAD → **67
  rotas novas** desde o último commit (`315ac61b`, 2026-09-10 17:06:46).
- `content/legal_cocitation_index.jsonl`: 5.815 linhas, 5.815 `public_path`
  distintos, mtime **2026-09-11 03:08:12** contra `content/pages.json`
  **2026-09-15 12:28:56**.
- **67 de 67 (100%)** das rotas novas **sem entrada** no índice.
- Taxa-base honesta: **5.224 de 11.039 (47,3 %)** das que já existiam também não
  têm — mas por **critério** do gerador (só indexa quem cita dispositivo com
  vizinha servível), não por ordem. O déficit atribuível à ordem é 67 de 67.
- Integridade em repouso intacta: **0 de 5.815** destinos fora do manifesto. O
  modo de falha é **ausência silenciosa**, não link morto.
- Chamadores: `grep` em `tools/ ops/ cmd/ internal/` →
  `cmd/generate-legal-cocitation` tem **um único** chamador,
  `tools/deploy-publico:678`; `cmd/generate-social-temas --aplicar` idem,
  `tools/deploy-publico:714`. **Nenhum dos dois aparece em
  `tools/run-daily-content`.**
- `internal/legalcocitation/artefato.go:53-54` promete no comentário que o
  `entrada_sha256` *"não impede leitura de artefato velho — impede que ela passe
  despercebida"*; `:162-167` só compara registros **do mesmo arquivo**. O campo
  existe no disco (medido na primeira linha do artefato). Resultado:
  `check-percursos-fundamento-legal` sai **exit 0** contra índice de 4 dias atrás
  → **L11**.

**Passos executáveis (entram na sequência do publicador autônomo, §6):**

1. **PASSO 0, documentação, antes de codar:** declarar a Cadeia B num documento
   próprio, no molde de `docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md`, com
   bloco legível por máquina, e fazer o §1 do `CLAUDE.md` apontar **as duas**,
   dizendo qual é de quem: *mtime → `authorial_mass`*, *runner/CAS → publicação
   v2*. Sem isso o próximo implementador repete a leitura errada (§6).
2. Inserir na onda, na janela que já existe entre o publish (`:684`) e a recarga
   (`:862`): `./tools/go-modern run ./cmd/generate-legal-cocitation` (custo
   ~16 s ocioso / ~29 s sob carga, linear no acervo; não aborta — artefato
   ausente ⇒ seção omitida, e `httpserver.filtraPercursosServiveis` descarta
   destino não servível).
3. Inserir, **antes da recarga e antes do IndexNow**:
   `./tools/go-modern run ./cmd/generate-social-temas --aplicar` seguido de
   `./tools/check-social-temas-espelhados`. Anunciar URL cuja âncora dá 404 é
   pior que não anunciar (88 respostas 404 em `/redesocial/tema/` medidas em 4
   dias; 1.161 em 10 dias no precedente de `deploy-publico:698-704`).
4. Estender `tools/check-percursos-fundamento-legal` com (a) comparação do
   `entrada_sha256` do artefato contra o `impressaoDoInsumo` do acervo vivo — a
   função já existe em `cmd/generate-legal-cocitation/main.go:117,219-222` e o
   campo já vai ao disco, **falta só o lado que compara** — e (b) piso de
   cobertura sobre as rotas do manifesto que satisfazem o critério. Detector novo
   nasce com teste de falso positivo sobre amostra real (§5 do contrato).
5. Pendurar os dois gates órfãos num runner:
   `check-cadeia-editorial-ordem-declarada` na bancada diária e
   `check-percursos-fundamento-legal` nos gates de resultado da onda (hoje só
   `internal/checks/crawl_recovery_gates.go:161` o alcança).
6. **Verificação depois:** `./tools/check-social-temas-espelhados` (exit 0) e o
   curl da gêmea com **controle positivo** — `/autonomos/b2b-escopo-alterado/index.md`
   responde 200 **com** a seção, então uma rota nova sem ela é ausência, não
   instrumento quebrado.

---

### L6 — GRAVE — a onda varre e publica trabalho não-commitado

**Evidência (lida nesta sessão):**
- `tools/run-daily-content:613-616` — `git add data/editorial/portfolio_v2` **por
  diretório**, seguido de `git commit -q -m ... -- data/editorial/portfolio_v2`
- `:631-633` — o mesmo para `data/editorial/v2_pages`
- `:684` — `publish-v2-direct ... -allow-public-write`, timeout 1800
- Os alvos exatos do P6: `cmd/generate-acordao-pages/main.go:70-71`
  (`data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` e o portfólio homônimo)
- Janelas medidas agora (`systemctl show`):
  `wikijuridica-daily-content.timer` `OnCalendar=*-*-* 04:20:00`
  `RandomizedDelayUSec=15min` (próximo disparo 2026-09-16 04:31:33);
  `wikijuridica-qualidade-diaria.timer` `04:40:00` `RandomizedDelayUSec=10min`
  (próximo 04:47:17); `wikijuridica-daily-content-noticias.timer` próximo
  12:20:55; `wikijuridica-qualidade-longa.timer` `02:10:00`.
- Estado agora: `git status --short` em `data/editorial/portfolio_v2` e
  `data/editorial/v2_pages` = **0 arquivos**; índice = **0**. Janela **vazia, não
  fechada**.

**Passos executáveis:**

1. **Invariante de entrada e saída de todo passo:** `git diff --cached
   --name-only` vazio.
2. Nunca atravessar **04:20+15min** nem **12:20** com trabalho não-commitado em
   `data/editorial/v2_pages` ou `data/editorial/portfolio_v2`.
3. Todo `git add` e todo pathspec do plano usa **caminho exato de arquivo**,
   nunca diretório — inclusive nas fases de commit da travessia (§4), que os
   dossiês escreviam por diretório.
4. Registrar o P6 como **passo dentro de `run-daily-content`**, sob o
   `/tmp/wiki-daily-content.lock` que já existe, **pulado quando
   `SOMENTE_NOTICIAS=1`** (senão o portal publica acórdão duas vezes ao dia), e
   **depois** de a família existir em HEAD.
5. **Antes de ativar esse passo, medir a duração nova da onda**: hoje ela termina
   04:42–04:57 e a bancada começa 04:40–04:50, **sem lock entre as duas** — em
   2026-09-15 foram 04:24:45→04:42:10 contra 04:48:12→05:48:54, 6 min de folga
   por sorte. Conforme o número, antecipar o `OnCalendar` da onda ou reduzir o
   `RandomizedDelayUSec=15min`.

---

### L7 — GRAVE — ponto cego do `strictjson` na guarda de atestação

**Evidência:** `tools/check-atestacao-grafo-no-commit`, bloco 2, descarta
`*_test.go` **antes** de consultar o grafo; mas os dois `_test.go` de
`internal/strictjson` **entram no hash** pelo passe de `//go:embed *.go`
(`internal/strictjson/implementation_fingerprint.go:14`,
`internal/v2ingest/validator_fingerprint_graph.go:703-738`), que não reaplica o
corte de teste. Provado por medição, não estimado: com os dois `_test.go` o
digest é `sha256:beb3ac7e…` (o **gravado**); sem eles, `7fd00442…`.
O selftest **consagra o ponto cego**:
`tools/check-atestacao-grafo-no-commit-selftest:104` afirma veredito 0 para
`_test.go` do grafo.

**Passos:**

1. Trocar o descarte cego de `*_test.go` por descarte que consulte os padrões
   `//go:embed` dos pacotes do grafo — mínimo: **não descartar** `_test.go` cujo
   diretório esteja no grafo **e** tenha `//go:embed` casando `.go`.
2. No mesmo commit, mudar `…-selftest:104` para o caso nomeado
   `internal/strictjson/*_test.go` com **veredito 1**, mantendo veredito 0 para
   `_test.go` de pacote do grafo **sem** embed. Provar por mutação antes e depois.
3. Este commit **toca o grafo** ⇒ vai **sozinho** e leva a atestação (§5).

---

### L8, L9, L10, L11 — GRAVES restantes, em forma curta

**L8 — derivados da transação sem committer.** `published_manifest.jsonl` está M
desde `315ac61b` (2026-09-10 17:06). `grep published_manifest
tools/run-daily-content` devolve só comentários (`:495`, `:700`): **produtor sem
committer**. E `data/editorial/first_published_at.json` (mtime **2026-08-28
17:26**, 18 dias) tem `total = 10.107` chaves contra **11.106** no manifesto, e
`tools/generate-first-published-at` reconstrói a estreia **percorrendo o
histórico do git do manifesto** — logo manifesto não-commitado é exatamente o
que trava o P1b. `grep` por `generate-first-published-at` em `tools/ ops/ cmd/
.githooks/` acha só um **comentário** em `cmd/publish-v2-direct/main.go:3558`:
gerador **órfão**, confirmado.
**Passo:** Fase 7b — seis `git add` por caminho exato
(`content/pages.json`, `content/legal_cocitation_index.jsonl`,
`data/editorial/published_manifest.jsonl`, `data/editorial/stock_manifest.json`,
`data/editorial/v2_publication_severity.jsonl`,
`data/ops/sitemap_shard_registry.json`) e um commit de derivados logo após o
deploy; e, estruturalmente, esse commit entra **dentro de `run-daily-content`**,
depois do 8/9 e antes do 9/9, senão a onda da manhã seguinte o deixa M de novo.

**L9 — exceção taxativa sem filtro.** *(Números **[H]**, dossiê travessia — os
arquivo:linha foram conferidos, as contagens sobre as 10.414 ementas não.)*
`internal/stjacordaos/registro.go:52,99`
fixa `NivelSigilo *int` em `nil` e `registro_test.go:49-50` **assere** que sai
nulo. Medido: `nivel_sigilo` nulo em **10.414 de 10.414 (100,0 %)**. `grep` por
`sigilo|anonim|publicidadenome` em `cmd/generate-acordao-pages` = **zero**;
`internal/publicidadenome/publicidadenome.go:180` tem glob fixo
`diarios-municipais-*.jsonl` com early-return. O risco **não** é PII e isso está
medido: 0 CPF formatado, 0 CNPJ, 4 de 10.414 ementas com rótulo de parte. O risco
é a exceção taxativa: **8 de 10.414** casam Lei 11.340/Maria da Penha, e 2 de 2
amostrados são caso genuíno.
**Passo:** filtro de exceção taxativa no gerador **antes da estreia**, com recusa
**nomeada em disco**, e triagem manual das ~8. O detector de ECA/adoção **tem de
nascer com controle de falso positivo**: o regex da investigação deu 326 (3,13 %)
e os 2 amostrados são *"adoção de providência"* e *"adoção de entendimento"* — o
verbo comum, não o instituto. **Esse detector não serve** e o número real fica
em aberto (§10, N2).

**L10 — gerador órfão e `-limite` default 30.** `tools/run-daily-content:369-373`
tem os cinco derivados e **não** `generate-acordao-pages`;
`cmd/generate-acordao-pages/main.go:185` — `flag.IntVar(&limite, "limite", 30, …)`.
**Passo:** registrar
`[stj - acordao]="./cmd/generate-acordao-pages -limite ${WIKI_LIMITE_STJ_ACORDAO:-200}"`
num commit **depois** do commit das páginas (Fase 7c), nunca antes — com o shard
já em HEAD o `shardpreserve` passa a funcionar de verdade e a onda **acrescenta**
200/dia em vez de fazer a estreia sozinha com 200. E **nunca rodar o gerador sem
`-limite` explícito.**

**L11 — o gate de co-citação não tem detector de frescor.** Evidência e conserto
em L5, itens 4 e 5.

---

## 4. A sequência da PRIMEIRA TRAVESSIA do shard inédito

Derivada do commit real que criou outra família. **Precedente verificado por
`git`, não por memória** (`git log -1 --format='%ci %s'` e `git rev-parse` em
cada um):

```
288d3e16  2026-08-20 11:18:11  feat(tipos)      pageType
   └─ dbb73e2a  11:19:37        feat(lane)       lane
        └─ 5998cc47  12:03:43   fix(juridico)    geradores + censo
             └─ 376e4de4  12:04:42  feat(portfolio)  SÓ portfolio_v2  (2 arquivos, 280 linhas)
                  └─ e9b354dd  12:05:27  feat(escala)     SÓ v2_pages      (2 arquivos, 280 linhas)
```
`rev-parse 376e4de4^` = `5998cc47` · `e9b354dd^` = `376e4de4` — pai-filho, **45 s**
entre um e outro. A segunda família repete o padrão em dois commits:
`ceb2481a` (gerador + portfólio) → `a62c27e1` (só páginas), `a62c27e1^` = `ceb2481a`.

**Ovo-e-galinha: NÃO EXISTE, e a prova é a regex.**
`tools/check-v2-finalized-commit:33-34` — `FINALIZED =
re.compile(r"data/editorial/v2_pages/[a-z0-9_]+(?:-[a-z0-9_]+)+\.jsonl")`. Commit
1 toca **só** `portfolio_v2/` ⇒ nenhum path casa `FINALIZED` ⇒
`check_page_product` não roda. Commit 2 acha o pai pronto, e `:1379` —
`members = portfolio_membership(old)` — lê o portfólio do **pai**. Nenhuma
exceção a pedir. *(Nota de contrato: a citação `:1341` está deslocada; `:1341`
hoje é `anchored_membership_additions`. Corrigir para `:1379`.)*

### FASE 0 — pré-voo

```bash
./tools/check-load-headroom --max 12
./tools/check-coord-status
./tools/check-coord-inbox --agent SEU_ID --last 15
git status --short data/editorial/portfolio_v2 data/editorial/v2_pages   # tem de dar VAZIO
git diff --cached --name-only                                            # tem de dar VAZIO
```
O índice vazio não é zelo: `go-index-compile-closure` compila o **índice**, não o
pathspec — 77,6 s com `internal/v2ingest` sentado nele contra 14,9 s limpo,
orçamento nominal 90 s. Evitar **04:20–06:00** e **12:20** (timers medidos em §7).

### FASE 1 — COMMIT DE CÓDIGO (o equivalente do `5998cc47`)

Editar, todos **fora** do grafo do `v2ingest` (§5):
- (a) `cmd/generate-acordao-pages/main.go:78` → `lane = "derivada_de_fonte_oficial"`
- (b) `main.go:76` → `pageType = "julgado"` (nunca valor inventado — L2, passo 2)
- (c) `main.go:82-83` → corrigir o comentário da banda (C1)
- (d) `main_test.go:124` → asserção dos literais + caso que lê os 5 shards irmãos;
  **mutação: `lane="informativa"` ⇒ VERMELHO**
- (e) `tools/check-derived-authorial-floor:279` → acrescentar
  `"stj-acordao-derivado": "stj-acordao-derivado-*.jsonl"` ao
  `FAMILIAS_CANAIS_DERIVADOS` (hoje **6 famílias**, chaves lidas literalmente
  [M]: `diarios-municipais`, `leis-motor`, `noticias-oficiais`,
  `stf-informativo-derivado`, `stj-sumula-derivada`, `stj-tema-derivado` — e o
  comentário de `:273-278` avisa por escrito que família nova "entra aqui ou
  nasce fora do gate"); **mutação: sem a linha ⇒ VERMELHO**
- (f) `:491` → teto no eixo 3: guardar só pares `>= piso de relato` em vez dos
  3.093.828, e corrigir a docstring (205 → 1.074 → 2.488). Custo medido do eixo
  O(n²) sem amostragem: 64,16 µs/par ⇒ n=2.488 = 3.093.828 pares = **198,5 s** e
  **308 MB** (437 MB após `sort()`) — na mira do earlyoom junto com o Ollama
- (g) filtro de exceção taxativa (Lei 11.340 / ECA / adoção / segredo) com recusa
  **nomeada em disco**, e detector com controle de falso positivo sobre amostra
  real (L9)

**GUARDRAIL:** se o conserto derivar para `internal/ptbrtext`,
`internal/publicpath`, `internal/content`, `internal/seo`, `internal/quality` ou
`internal/lexml`, a atestação passa a ser obrigatória **no mesmo commit** (§5).

### FASE 1b — provar e commitar o código

```bash
./tools/go-modern build ./internal/... ./cmd/...
./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/
git add cmd/generate-acordao-pages/main.go
git add cmd/generate-acordao-pages/main_test.go
git add tools/check-derived-authorial-floor
flock -w 300 /tmp/opt-wiki-agent-heavy.lock git commit -F /tmp/msg-codigo.txt -- \
  cmd/generate-acordao-pages/main.go \
  cmd/generate-acordao-pages/main_test.go \
  tools/check-derived-authorial-floor
```
`add` e `commit` em comandos **separados**; `flock` **com `-w`**, nunca nu
(o lock nu pendura até 05:49 em silêncio se a bancada o tomou). ≤ 6 pacotes Go
(`TETO_DE_PACOTES=6`: acima do teto o pre-commit **avisa e deixa passar sem teste
focado**).
**Confere depois:** `git log -1 --stat` mostra só os 3 arquivos; `git diff
--cached --name-only` vazio.

### FASE 2 — PASSADA SECA

```bash
./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000
```
Read-only **confirmado no código**, não suposto:
`cmd/generate-acordao-pages/main.go:206-219` — `executar()` chama `relata()`,
`imprimeAmostra()` e **`return nil` ANTES** de `gravaPortfolio` (`:222`) e
`gravaShard` (`:225`).
**Confere:** o poço (2.488 + 1.405 + 682 + 165 + 22 + 1 = 4.763). Registrar que
toda recusa é `passada.Recusas[motivo]++` num map (`main.go:277,280,286,291,296`),
**sem `intent_id` em disco** — para a estreia não bloqueia; para o §5 do contrato
("gate refutado por medição é pulado, **com a evidência gravada**") bloqueia, e é
o defeito que o P4 nomeia.
*(Se a passada já foi feita nesta sessão por outra frente, **não repetir**: ~8 min
de CPU por um número já medido.)*

### FASE 3 — GERAR os DOIS arquivos

```bash
./tools/go-modern run ./cmd/generate-acordao-pages -limite 2500
./tools/check-v2-portfolio-pairing        # esperado exit 1, "ORDEM DE COMMIT PENDENTE"
```
`executar()` grava portfólio (`:222`) e **depois** shard (`:225`), no mesmo
processo. **Confere:** a linha `shard: N pagina(s) preservada(s)` **NÃO** aparece
— na estreia isso é **correto** e tem de ser **registrado como esperado**:
`internal/shardpreserve/shardpreserve.go:81-83` faz `git show HEAD:<shard>` e
`if err != nil { return nil }`, e o mesmo caminho de erro cobre "não existe em
HEAD" e "git quebrado". Da segunda passada em diante a ausência dessa linha
**vira alarme**. Conferir à mão a contagem de registros do shard contra o que o
gerador relatou — `tools/check-shard-preservation:145` monta a lista com
`git ls-tree HEAD` e é **cego exatamente uma vez**: na vez em que o shard nasce.

### FASE 4 — COMMIT 1: SÓ O PORTFÓLIO (o `376e4de4`)

```bash
git add data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
git commit -F /tmp/msg-portfolio.txt -- data/editorial/portfolio_v2/stj-acordao-derivado-01.jsonl
```
**Caminho exato nos dois lados** — a correção R6 vale aqui: os dossiês escreviam
`-- data/editorial/portfolio_v2`, e a onda escreve nesse diretório 2×/dia.
Commit de dado: leve, sem build.
**Confere:** `git show --stat HEAD` = 1 arquivo.

### FASE 5 — COMMIT 2: SÓ AS PÁGINAS (o `e9b354dd`)

```bash
./tools/check-v2-portfolio-pairing                 # agora exit 0
git add data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
./tools/check-v2-portfolio-pairing --index         # < 1 s, ANTES de o pre-commit compilar
git commit -F /tmp/msg-paginas.txt -- data/editorial/v2_pages/stj-acordao-derivado-01.jsonl
```
Se recusar com "intent fora/ambíguo no portfólio candidato", **não insistir**: a
autoridade é o pai (`:1379`).
**Esta é a única etapa não exercitada nesta escala** — maior estreia do
precedente: 280 páginas em 2 arquivos; maior shard de hoje: 1.074. E
`check_page_product` valida **cada** registro no pre-commit. **Encenar com
`-limite 50` primeiro** para ter o número antes de arriscar o lote (N1, §10).

**O ensaio tem duas consequências que precisam estar escritas antes de rodá-lo:**

1. Com 50 páginas em HEAD, a **onda das 04:20 as publica** — ela lê o glob
   (`v2publish.go:179`) e chama `reload-wiki-server`, então elas **entram vivas no
   canal de máquina**, só que **sem o passo 2.6** (C4/L5). Ou o ensaio e a
   passada real cabem **entre duas ondas**, ou se aceita 50 páginas estreando pelo
   caminho da onda, sem percursos, a serem corrigidas no deploy seguinte.
2. A partir daí a linha `shard: N pagina(s) preservada(s)` **passa a ser
   obrigatória** na FASE 3 real — ela tem de imprimir `shard: 50 pagina(s)
   preservada(s)`. É a inversão que o §4/FASE 3 anuncia: na estreia a **ausência**
   da linha é correta; depois do primeiro commit, a ausência é **alarme**, e
   `shardpreserve.go:81-83` não distingue "não existe em HEAD" de "git quebrado".

### FASE 6 — CENSO E GATES antes de publicar

```bash
./tools/check-censo-acompanha-estoque            # espera ATRASADO, exit 1
python3 tools/generate-v2-publication-severity --write
./tools/check-censo-acompanha-estoque            # espera exit 0
./tools/check-v2-cross-shard-collision
./tools/check-v2-public-path-collision
./tools/check-shard-preservation
./tools/go-modern run ./cmd/check derived-body-repetition
./tools/go-modern run ./cmd/check text-truncation
./tools/generate-check-selection-profiles --paths <os arquivos tocados>
```
Nomes de gate conferidos em `internal/checks/checks.go:451` (`text-truncation`) e
`:452` (`derived-body-repetition`). **NUNCA `cmd/check` sem argumento.**
**Confere:** no log do censo, que as 2.488 saíram como `jurisprudencia` e que
`area_nao_derivavel` **não** apareceu.

### FASE 7 — PUBLICAR PELO DEPLOY

**Pré-requisito duro: a L1 já pousada** (senão o deploy sai com exit 1 em
`:1403`, depois de o acervo já estar no ar e a borda já purgada).

```bash
./tools/deploy-publico          # SEM --ressemear
```
É ele que faz o passo 2.6 (`:678`) na janela entre a republicação (`:464`) e o
restart (`:738`/`:884`). As rotas entrariam no canal de máquina mesmo por
`tools/publicar` (C4) — o que **só** o deploy entrega é a seção de percursos.
Quando imprimir
`purgando tudo`, **não purgar de novo**; ler o MOTIVO impresso — *"registro de
revisao indisponivel"* já foi diagnóstico falso.

### FASE 7b — COMMITAR OS DERIVADOS (a fase que faltava)

```bash
git add content/pages.json
git add content/legal_cocitation_index.jsonl
git add data/editorial/published_manifest.jsonl
git add data/editorial/stock_manifest.json
git add data/editorial/v2_publication_severity.jsonl
git add data/ops/sitemap_shard_registry.json
git commit -F /tmp/msg-derivados.txt -- content/pages.json \
  content/legal_cocitation_index.jsonl data/editorial/published_manifest.jsonl \
  data/editorial/stock_manifest.json data/editorial/v2_publication_severity.jsonl \
  data/ops/sitemap_shard_registry.json
```
**Confere:** `git status --short` sem produto untracked, e
`data/ops/sitemap_shard_registry.json` com a chave `<data>|jurisprudencia#0`. Este
`git add` do `published_manifest.jsonl` é metade do conserto do P1b, de graça.

### FASE 7c — REGISTRAR NO RUNNER, depois de a família existir em HEAD

```bash
git add tools/run-daily-content
git commit -F /tmp/msg-runner.txt -- tools/run-daily-content
```
Acrescentando em `:373`
`[stj - acordao]="./cmd/generate-acordao-pages -limite ${WIKI_LIMITE_STJ_ACORDAO:-200}"`.
**Prazo que a R11 fixou:** *o P1b pousa antes deste commit, ou antes da primeira
onda depois do P6 — o que vier primeiro.* No **dia 1** a família é P1b-neutra
(nenhum dos 2.488 intents está em `first_published_at.json`, o fallback
`publish-v2-direct:3838` grava HOJE, e HOJE **é** a estreia verdadeira). No **dia
2** o mesmo fallback grava HOJE para páginas que estrearam ontem — e a família
entra na conta das 944.

### FASE 8 — PROVA, com sonda própria

```bash
./tools/check-http-smoke
./tools/check-paridade-go-nginx
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/jurisprudencia/stj-resp-<n>/
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  http://127.0.0.1:8088/jurisprudencia/stj-resp-<n>/index.md | head -40
./tools/check-derived-authorial-floor     # agora ELE OLHA a familia
./tools/check-csp-style-hashes
```
A gêmea é a prova de que o canal de máquina nasceu: **200 e corpo, não 404**.
Controle positivo obrigatório na mesma passada:
`/autonomos/b2b-escopo-alterado/index.md` responde 200 **com** a seção de
percursos — sem esse controle, "sem seção" não distingue rota nova de
instrumento quebrado.

### FASE 9 — o que NÃO fazer

`--ressemear` (só para markup/CSS/atributo sem texto) · purga ampla manual
(nenhum script inline nem malha de links mudou) · `cmd/check` sem argumento ·
`git add` por diretório · `sudo nginx -t` ·
`git reset/checkout/stash/clean/revert/cherry-pick`.

---

## 5. A regra de atestação do grafo de `internal/v2ingest`

**Grafo medido nesta sessão:** `./tools/go-modern list -deps ./internal/v2ingest
./cmd/ingest-v2-stock` → **98 pacotes in-module**, exit 0. O gate escrito em
2026-08-29 dizia 96: cresceu **2 em 17 dias**. É closure **transitiva de
import**, não o diretório. O digest gravado, `sha256:beb3ac7e…`, cobre **207
arquivos**: 203 `.go` de produção + `go.mod` + `go.sum` + **2 `_test.go` de
`internal/strictjson`** (sem eles dá `7fd00442…` e não fecha). A frase do
`CLAUDE.md` *"até um `_test.go` novo invalida"* é verdadeira em **1 de 98**
pacotes e falsa nos outros 97 — e é onde a guarda é cega (L7).

### R0 — pergunte ao grafo antes de montar o pathspec (5,65 s contra 611 s)

```bash
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock \
  | sed -n 's|^portaljuridico/||p' | grep -xF <seu_dir>
```

### R1 — como o plano está, NENHUM commit leva a atestação

Medido, **0 de 6**: `cmd/generate-acordao-pages`, `internal/cerebro`,
`internal/stjacordaos`, `internal/ollama`, `internal/checks`,
`internal/v2bodyneardup` — todos **fora**. E também fora, medido nesta sessão:
`cmd/publish-v2-direct`, `internal/httpserver`, `internal/v2publish`,
`internal/sitemap`, `internal/shardpreserve`, `internal/render`,
`internal/pagemarkdown`, `internal/htmlcontract`, `internal/legalmarketingpolicy`,
`internal/legalcocitation`, `internal/webanalytics`. Razão estrutural: o hash
depende das arestas de **saída** do grafo, e esses pacotes só são importados por
`cmd/*` main e por `httpserver`/`semantica`/`cerebro`, todos fora.
**Incluir a atestação nesses commits é ERRADO** — puxa `./internal/v2ingest/`
para o teste focado e custa 86 s (ou 611 s) sem necessidade.

### R2 — a atestação é obrigatória se, e só se, o commit tocar

`go.mod` · `go.sum` · qualquer `.go` **de produção** num dos 98 pacotes ·
**ou `internal/strictjson/*_test.go`** (o ponto cego). **Reavaliar a cada onda.**

### R3 — decida ANTES de editar que a correção não desce para o grafo

Os membros que o plano tem mais chance de tocar, **medidos DENTRO**:
`internal/content` (o P1b: `LastModified()` em `content.go:453` — e note que
`content.Page.FreshnessDate` **não existe**, grep = 0), `internal/seo`,
`internal/quality` (paridade do P4), `internal/publishedmanifest` (P1b),
`internal/lexml` (P8 URN, P9 URN LexML), `internal/publicpath`,
`internal/ptbrtext`, `internal/v2portfolioindex`, `internal/stockmanifest`.
Manter a régua em `cmd/generate-acordao-pages` e `internal/v2bodyneardup`, e o
P1b em `cmd/publish-v2-direct` + `tools/`, mantém **todos** os commits do plano
baratos e fora do grafo.

### R3b — cada commit Go em ≤ 6 pacotes

`TETO_DE_PACOTES=6`: acima do teto o pre-commit **avisa e deixa passar sem teste
focado** ("o teste focado NAO rodou nesta passada"), e o contrato já registra o
precedente de gate verde com 14 de 17 testes quebrados. **Commit que toca o grafo
vai sozinho.**

### R4 — se R2 disparar, nesta ordem

1. `git status --short -- go.mod go.sum $(./tools/go-modern list -deps
   ./internal/v2ingest ./cmd/ingest-v2-stock | sed -n 's|^portaljuridico/||p')` —
   **só os seus arquivos podem aparecer**. A atestação hasheia o **worktree**
   (`validator_fingerprint_graph.go:641,977` semeiam `go.mod`/`go.sum` em
   `seenFiles`), então edição não-commitada de outra sessão em qualquer um dos 98
   diretórios entra no hash. `go.mod` sujo e sem uso: preservar cópia em
   `.agents/runtime/` e restaurar com `git show HEAD:go.mod > go.mod`
   (**nunca `checkout`**).
2. `systemctl stop wikijuridica-cerebro.service` — o closure reverso de 410
   pacotes estourou 75,3 s sob a extração LLM e passou em 29,3 s com ele parado.
   Vale duplamente porque **P9/P12 é o próprio cérebro**.
3. Terminar **toda** edição de arquivo do grafo, `gofmt` incluído, **antes** de
   gerar (precedente de 2026-09-11: o pre-commit reprovou por gofmt do arquivo
   **gerado**, o gerador o reescreveu, e a atestação ficou para trás — 10 testes
   vermelhos depois de ~5 min).
4. `./tools/go-modern generate ./internal/v2ingest` como **último** passo antes
   do `git add`.
5. `./tools/check-validator-attestation` e **exigir OK** (7,6 s medidos).
   **ESTE é o veredito** — o passo 1 do gate de commit faz curto-circuito na
   **presença** do arquivo (`[[ $arquivo == "$ATESTADO" ]] && exit 0`), não na
   sua correção.
6. `git add <caminhos exatos>` e `git add
   internal/v2ingest/validator_fingerprint_attestation_generated.go`, em comando
   **separado** do commit; mensagem por `-F`.
7. Conferir que a rota barata de 86 s está valendo:
   `git diff --cached --name-only | grep -E '^internal/v2ingest/.*\.go$' | grep
   -v attestation_generated` deve sair **VAZIO**. Não-vazio custa 611 s e ~12 min
   de `.git/index.lock`, durante os quais nenhuma outra sessão commita.
8. Esvaziar o índice de outras frentes antes de pedir a vez e serializar com
   `flock -w <N> /tmp/opt-wiki-agent-heavy.lock`.

### R5 — o conserto do ponto cego é passo do plano, não observação

L7, itens 1–3. Vai **sozinho**, com a atestação.

---

## 6. O DAG da cadeia editorial, e onde o publicador autônomo entra

**São DUAS cadeias, e o contrato §1 aponta para a errada.**

### Cadeia A — `authorial_mass_*` (a dos "~9 artefatos" e dos "31 dias"), ordenada por **mtime**

`grep -rn older_than internal/ --include=*.go` devolve exatamente **5**
detectores, os mesmos 5 de 09-08. O DAG **já está escrito** em
`docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md` (13 elos, blocos legíveis por
máquina) e `./tools/check-cadeia-editorial-ordem-declarada` **passa** (exit 0,
"5 detectores, todos declarados").

**Evidência do descarte, para ninguém reabrir:** `grep -rl v2_pages
internal/authorialmass*/ cmd/generate-authorial-mass-*` = **0 arquivos**. O P6
**não a toca**. Estado hoje: 11 de 11 derivados atrás da fonte
(`authorial_mass_drafts.jsonl` = 2026-09-10 23:41) — e **nenhum** alcança página
publicada (todos `noindex` / `publication_allowed:false`). Quem rodar os 13 (ou
os 40 da `bootstrap-chain`, com teto **duro** de 600 s em `tools/bootstrap-chain:298`
e recusa de valor maior em `:302`) perde a sessão sem tocar em nada que o P6
invalida — e passada parcial deixa o estado **espalhado**, mais caro de
diagnosticar do que a dívida que tentava pagar.

### Cadeia B — a cadeia de publicação v2, ordenada por **CAS e sequência de runner**

É a que o P6 perturba, e **não está declarada em lugar nenhum** — por isso o
PASSO 0 de L5 é documentação, antes de código.

```
 1  check-shard-preservation                     ← a onda PARA aqui se o shard perdeu texto
 2  check-untracked-product-inventory
 3  git add/commit  portfolio_v2/<arquivo>       ← PRIMEIRO. autoridade = commit PAI
 4  check-v2-portfolio-pairing                   ← DEPOIS do commit do portfolio, nunca antes
 5  git add/commit  v2_pages/<arquivo>
 6  generate-v2-publication-severity --write     ← censo
 7  generate-page-content-revision               ← ANTES do publish (carimba content_revised_at)
 8  ingest-v2-stock                  [FALTA HOJE, condicional]
 9  publish-v2-direct -allow-public-write        ← FALHA AQUI = PARE a onda
10  generate-legal-cocitation        [FALTA HOJE]  ← a janela e AQUI: depois do 9, antes do 13
11  generate-social-temas --aplicar  [FALTA HOJE]  ← antes do reload e antes do IndexNow
       + check-social-temas-espelhados
12  git add/commit dos derivados da transacao    [FALTA HOJE]  ← fecha o P1b (L8).
       DEPOIS do 9 e ANTES do IndexNow, pela mesma regra que o script ja defende:
       nao se anuncia URL de transacao cujo produto nao esta em HEAD.
13  generate-brotli-static --jobs 4              ← depois do publish, antes do IndexNow
14  reload-wiki-server                           ← restart real; o boot rele o indice do passo 10
15  check-onda-avanca --depois --minimo 1 + gates de resultado
       (ACRESCENTAR: check-percursos-fundamento-legal, check-social-temas-espelhados)
16  generate-indexnow-incremental-submit         ← ULTIMO. exit real por PIPESTATUS[0]
```

*(O passo 9 já recarrega por dentro — C4 —, então o passo 14 é a recarga que
enxerga o **índice do passo 10**, não a primeira do ciclo.)*

**Onde o publicador autônomo entra:** como **passo de geração antes do 1**,
dentro de `run-daily-content`, sob o `/tmp/wiki-daily-content.lock` que já existe
— **não** como runner novo nem timer novo. Pulado quando `SOMENTE_NOTICIAS=1`.

**Ordem é propriedade do runner, e os dois runners são OPOSTOS** (R3, medido):
`run-daily-content:674` revisão → `:684` publish; `deploy-publico:464` publish →
`:1403` revisão. A travessia publica pelo deploy e **herda a ordem do deploy** —
é daí que sai a L1.

**Ponto 8, condicional, com a condição exata do deploy:**
`find data/editorial/v2_pages -name '*.jsonl' -newer
data/editorial/stock_manifest.json -print -quit`. Hoje o backlog está aberto
(`stock_manifest.json` = 2026-09-11 02:59, e o relatório do ingest tem **um único
run**, `v2-ingest-20260911T050000Z`). Não é pré-requisito de `publish-v2-direct`
(que lê o glob direto, `v2publish.go:179`) — **e é por isso que deriva calado**.
**Passa a ser pré-requisito DURO** do passo 13 se a release sharded do
contentstore for ativada: `internal/content/content.go:855-884` — `loadPages`
**prefere** o contentstore e só cai em `pages.json` como ramo **legado**; hoje o
legado está ativo porque os quatro artefatos estão ausentes (`content/page_index.jsonl`,
`content/page_release_manifest.json`, `content/page_shards`,
`content/page_release_journal.jsonl`), mas `:866-884` devolve **erro** se
manifesto/journal/diretório existirem sem o índice — e release parcial vira
**erro de boot**, não fallback, com `Restart=always` e sem teto.

---

## 7. A matriz de serialização

**O risco é o INVERSO da premissa: quase nada serializa de verdade.** Nenhuma
frente do plano fica bloqueada por lock; o que age sozinho sobre o trabalho é a
**onda diária**.

*Timers, locks e o índice do git: **[M]**. Durações de execução (60m42s da
bancada, 34m06s da longa, 1m05s do coletor), memória e as pausas do cérebro:
**[H]** do dossiê de concorrência.*

### Duas premissas caíram

1. **09:40–10:20 não é a bancada.** É `wikijuridica-stj-acordaos-coleta`
   (próximo disparo medido: 2026-09-16 09:51:24), 1m05s, 6,1 s de CPU. A bancada
   é **04:40–05:49** (`qualidade-diaria` 04:48:12→05:48:54 = 60m42s). Cluster
   real: **02:10–02:45** (`qualidade-longa` 34m06s) e **04:20–05:49**.
2. **`run-heavy-throttled` nunca toca `/tmp/opt-wiki-agent-heavy.lock`.** Lock
   próprio em `/run/user/1000/portaljuridico-heavy-*`, chave = `sha256(argv)`:
   não serializa contra a bancada, e dois comandos diferentes rodam 100 %
   concorrentes. **E não espera:** `:1293-1296` é o `case default` de
   `validate_lock_wait_classification_or_exit`, chamado em `:1424` **antes** do
   laço de `:1417-1441` — o laço de 600 s é código morto por padrão e o default é
   **exit 75 imediato**.

### Locks, medidos

| lock | estado real |
|---|---|
| `/tmp/opt-wiki-commit.lock` | arquivo existe (0 B, 2026-09-10 05:41), **mecanismo não existe**: `git grep opt-wiki-commit` = 0 ocorrências |
| `/tmp/wiki-daily-content.lock` | `flock -n 9 \|\| exit 0` — **pula em silêncio** com `Result=success`, indistinguível de onda que rodou |
| `deploy-publico` | **sem mutex**: `: >"$DEPLOY_LOCK"` incondicional (`:127-129`); é janela de manutenção para o watchdog, não exclusão |
| `publish-v2-direct` | `O_EXCL`, falha na hora — **CONTROLADO** |
| sonda de lock do cérebro | **inerte**: `PrivateTmp=yes` ⇒ `saude.go:45,87` nunca enxerga o lock do host |
| `CargaMax=12` do cérebro | **viva**: 6 pausas / 5 retomadas / 562 lotes hoje |

### Índice do git

A regra do contrato vale **só para commit sem pathspec**. `GIT_INDEX_FILE` é
honrado em `.githooks/pre-commit:163-171,185-193` e
`tools/check-go-index-compile-closure:843,912-914`, com teste nomeado
(`test_partial_commit_index_may_live_outside_git_directory`). Logo **`git commit
-F <arquivo> -- <caminhos exatos>` isola o gate**. Restrição: o pathspec leva o
conteúdo da **worktree** — nunca incluir arquivo que outra frente esteja
editando. Orçamento = 90 s × fator; load 12,90 ⇒ fator 2 (180 s); ≥ 32 ⇒ teto 4 e
commit correto é recusado.

### Ordem que minimiza espera

| ordem | frente | por quê |
|---|---|---|
| 1 | **L1** (teto de churn) | Python puro; destrava a FASE 7 da travessia e o P4 e o poço inteiro de uma vez |
| 2 | **P4** (paridade de régua + evidência de recusa com `intent_id`) | só Go, fora do grafo; um commit com pathspec |
| 3 | **P1b** (`datePublished`/`first_published_at`) | **antes do P6**: sem a estreia correta, cada página nova do P6 nasce com o mesmo defeito |
| 3b | commit do `published_manifest.jsonl` **dentro** de `run-daily-content` | fecha a lacuna estrutural: hoje tem produtor e nenhum committer |
| 4 | **P6** FASES 1→8 | por último, e o deploy por último dentro dele |
| 5 | **L7** (ponto cego da guarda) | commit de grafo, **sozinho**, com o cérebro parado |

**Janelas livres:** 06:00–09:15 · 10:05–11:45 · **13:00–21:45** · 22:00–02:05 —
com a ressalva de que `backup` 23:22, `datajud-fila` 00:37, `edge-warm` 01:25 e
`origin-warm` (a cada 3 h, `--rps 80`) as ocupam com duração **não medida**
(nenhum toma lock; disputam disco e rede).
**Evitar:** 02:10–02:45 · 04:20–05:49 · 09:18 · 09:40–10:00 · 11:50/16:20/21:50 ·
domingo 03:40 · segunda 04:10.

### Regras que caem de tudo isso

- Trocar todo `flock /tmp/opt-wiki-agent-heavy.lock` **nu** por `flock -w <N>`.
- Tratar **exit 75** de `run-heavy-throttled` como *"reoriente para outra
  frente"*, nunca como falha do comando. Para esperar de fato:
  `WIKI_HEAVY_WAIT_CLASSIFICATION=critical_dependency` + `DEPENDENCY_ID` +
  `OWNER_PID` (igual ao do meta do lock vivo) + `WAIT_TIMEOUT_MS` +
  `LAST_EVIDENCE` + `REORIENTATION_COMMAND`. **`WIKI_HEAVY_TIMEOUT_SECONDS=540`
  mata a suíte do `v2ingest`**, que custa 611 s medidos.
- **Não parar o cérebro para commit Go isolado**: `CargaMax=12` já pausa sozinho e
  o `stop` custa até 4 min de `TimeoutStopUSec` contra lote em voo. Parar só antes
  de **sequência** de commits Go (ganho medido 75 s → 29 s).
- **Não pedir snapshot de `data/ai/`** para P4/P6 — evidência do descarte: `grep`
  em `cmd/generate-acordao-pages/main.go` por `extracoes_dispositivos`,
  `dispositivos_promovidos` e `data/ai` devolve **zero**. O gerador lê o corpus do
  STJ e `v2_pages/*.jsonl` (**877 shards**, contados). Quem lê `data/ai` é outra
  família (`generate-writeback-extracoes`, `generate-revisao-extracoes`,
  `generate-grafo-juridico`, `generate-datasets-publicos`).
- **Vigiar memória, não CPU**, antes de passada pesada: `MemAvailable` 7,35 de
  20,36 GB (36 %), `llama-server` 6,70 GiB em 2 processos, `ollama`
  `MemoryCurrent` 8,54 de 12 GB, `earlyoom -m 10,5` (SIGTERM a 2,04 GB), folga
  5,3 GB. `OOMScoreAdjust=800` faz o `llama-server` ser o **primeiro** alvo
  (pausa barata) em vez dos servidores MCP das sessões.
- **Uma linha para o P8, fora desta lacuna:** `wikijuridica-stj-acordaos-coleta`
  está FAILED desde 09:59:17 por `invalid character '}' after array element` no
  mensal de `espelhos-de-acordaos-segunda-secao` competência 20240229 — **defeito
  de dado a montante**, não contenção.

---

## 8. O protocolo pré-migração

*Toda a §8 é **[H]** do dossiê migracao-no-meio, exceto onde marcado [M]. Os
arquivo:linha de `publishedmanifest`, `httpserver`, `saude.go`, `cliente.go`,
`tarefas.go` e `fila.go` são conferíveis por leitura; as contagens de bytes,
horas de parede e o estado do driver **não foram re-medidos aqui** e têm de ser
reconfirmados no dia, porque descrevem um host que vai mudar.*

### Por que é BLOQUEANTE (três achados que a lacuna não continha)

1. **`public/` (683 MB; 22.982 arquivos, 11.358 `.html`, 11.357 `index.html` —
   o `CLAUDE.md` §6 diz 10.369 e está desatualizado) está no `.gitignore` e
   deliberadamente fora do único backup** (`tools/generate-backup-wiki`: *"NÃO
   entra public/ nem var/"*). Perdê-lo **derruba o boot do Go** nas duas
   variantes: ausente ⇒ `collectPublicFiles`
   (`internal/publishedmanifest/publishedmanifest.go:177,1246-1249`) falha e emite
   `published_manifest_public_scan_failed`, código **fora** de
   `staticArtifactOnlyIssueCodes` (`:1456-1463`) ⇒ **blocking na 1ª ocorrência**
   (`internal/httpserver/httpserver.go:967,980-982`); reconstruído com bytes
   diferentes ⇒ `html_sha256_mismatch` (`:1020`) estoura
   `bootSameCodeAbortThreshold=10` (`:1469`). Somado ao nginx (`root public/`)
   servindo 404, é **queda total no dia um**.
2. **Fila e índice de vetores são UMA unidade.** Medido: **11.248** `embed_pagina`
   concluídas == **11.248** pares `(path,sha256)` no índice, **0 órfãs**.
   `internal/cerebro/tarefas.go:255-283` só faz short-circuit **pelo índice**;
   `fila.go:313-317` é `INSERT OR IGNORE` "em qualquer estado". Levar a fila sem
   `data/ai/embeddings/` = buraco **silencioso** de até 11.248 páginas, **sem gate
   que detecte** (grep em `tools/check-*` e `internal/checks/checks.go`: zero).
3. **Teto de 9 GiB pausa o cérebro no primeiro par grande.**
   `internal/cerebro/saude.go:90-92` (`TetoBytesResidentesPadrao = 9<<30`) soma
   `size` (`:204-205`), e `internal/ollama/cliente.go:276-281` **não lê
   `size_vram`**, que `/api/ps` já devolve. Hoje os residentes somam
   5.645.386.380 B < 9.663.676.416 B — o dia um **não** começa pausado; pausa
   **quando a GPU permitir 9b+4b**, que é o motivo da migração.

### O que TEM de ser medido antes de a máquina velha desligar

Tudo commitado em `.agents/runtime/migracao-<data>/`, e **todo registro leva
`load1` e hora local** — o repositório já refutou um "pareado" sem esses controles.

1. **Amostra determinística congelada** de acórdãos + passada de extração com
   `qwen3.5:4b` como lado `--a` de `tools/generate-comparacao-modelos-extracao`.
2. **Piso de determinismo**: DUAS passadas da mesma amostra **na mesma máquina**,
   temperatura 0 (`extracao.go:417`) e `presence_penalty` 0 (`:424`). **Não existe
   campo `Seed` em `ollama.Geracao`** e o backend muda na migração
   (`libggml-cpu` Intel → zen4/CUDA): mede-se **concordância**, nunca identidade.
   Sem este piso, qualquer diferença depois vira ruído inatribuível.
3. `tools/medir-recall-semantico` → `recall@1/5/10` + MRR em
   `data/ops/recall_semantico_daily.jsonl`.
4. `ollama --version` (0.33.3), a tabela dos **9 digests** de `/api/tags`,
   `ollama show --modelfile` de `qwen3.5:4b` e `qwen3-embedding:0.6b` (o
   `presence_penalty 1.5` vem do Modelfile) e a fotografia de `/api/ps` com
   `size`/`size_vram`/`context_length`.
5. Agregar `data/ops/ia_local_daily.jsonl` (6.609 linhas / 9 dias) como "antes":
   hoje `embed_pagina` 11.299 tarefas / 103.246,9 s; `extrair_dispositivos` 8.631
   / 463.089,6 s.
6. **Custos que dizem o que se perde:** embeddings = **28,7 h** de parede;
   extração já feita = **128,6 h** — esta **preservada pelo git**
   (`UltimaExtracaoPorChaveEModelo` lê o JSONL versionado,
   `extracao.go:133-137,875-899`), logo descartar a fila **não** refaz as 128,6 h.

### Ordem do dia um (resumo executável)

- **PASSO -1 — DECIDIDO, não devolvido: o NVMe MIGRA.** Não é preferência: é a
  única das duas rotas em que o piso de driver já está satisfeito hoje, e a
  refutação de que faltaria driver **só vale nessa rota**. Reinstalar o SO custa
  re-satisfazer o piso ≥ 570.26, re-habilitar 42 units e re-linkar todos os
  symlinks de `ops/` — trabalho inteiramente evitável. A lista de reinstalação
  fica abaixo como **contingência**, não como segunda porta. **REFUTADO** que
  "Debian trixie tem 550.163": este host é **Debian 12 bookworm** com `nvidia-driver`
  **610.57.04-1 já instalado** (7 pacotes, repo
  `developer.download.nvidia.com/.../debian12`, candidato 615.71.09-2) e `.ko` de
  122 MB compilado para o kernel vivo — **piso de 570.26 já satisfeito,
  condicionado a o NVMe migrar**. Confirmado por proveniência do `ptxas`:
  `cuda_v12/libggml-cuda.so` tem 8 cubins `-arch sm_120a` + 29 `sm_100`
  (toolkit 12.8); `cuda_v13` tem **zero**. Em instalação nova **não viajam**: os 7
  pacotes nvidia e o repo, as **42 units enabled**
  (`ops/host-state/units-habilitadas.txt`), `/etc/modprobe.d/nvidia.conf`,
  `/etc/systemd/system/ollama.service`, os symlinks para `ops/`,
  `/usr/local/{bin,lib}/ollama`, Node do publicador social, `sqlite3` (sem ele o
  backup do banco social falha por desenho) e `/usr/local/go`. **Se a
  contingência for acionada**, repetir o grep de `-arch sm_*` nos runners para
  reconfirmar o `sm_120a` do `cuda_v12` (o achado é deste build 0.33.3) e tratar
  o driver como instalação a fazer, com piso ≥ 570.26 e módulos open.
- **PASSO 0 (véspera):** parar o cérebro (SIGTERM, `TimeoutStopSec=240`);
  `VACUUM INTO` da fila e do grafo escrevendo em `<dest>.parcial-$$` e publicando
  por `mv` (`VACUUM INTO` **recusa destino existente**), conferindo com
  `PRAGMA integrity_check` e `foreign_key_check`; `cp -p` de
  `data/ai/embeddings/`; **`rsync -a --checksum` de `public/`**; `rsync -a` de
  `~/.claude` (4,5 GB) e dos 14,3 GiB ignorados de `.agents/`; `cp -a` de
  `~/.local/state/wikijuridica/perfil-navegador` (275 MB); copiar
  `/etc/systemd/system/ollama.service` e `/etc/modprobe.d/nvidia.conf`;
  `tools/generate-backup-wiki` + `tools/check-backup-restauravel`.
- **PASSO 1:** `git status` idêntico ao da véspera — qualquer diferença é perda de
  transporte, não ruído.
- **PASSO 2 (antes de qualquer coisa de IA):** provar `public/` byte a byte —
  `tools/check-http-smoke` e o gate `published-manifest`
  (`internal/checks/checks.go:763`) sem `published_manifest_public_scan_failed`,
  sem `public_html_missing` e sem `html_sha256_mismatch`. **Proibido "resolver"
  subindo os tetos de boot**: seria afrouxar gate, e aquele commit ainda
  arrastaria a atestação do grafo.
- **PASSO 3:** `tools/check-csp-style-hashes` — a URL de
  `ops/nginx/security-headers.conf` byte a byte igual à de
  `render.StylesheetPath()`, senão **nenhuma página tem estilo**. `nginx -t`
  **sem `sudo`**.
- **PASSO 4:** `check-tunnel-health`, `check-tunnel-replica-fleet` (frota de
  **5**, não 25), `check-edge-live`. **`check-portal-health` não serve como
  critério**: sonda só `127.0.0.1` e passa verde com o túnel caído — e **escreve**
  `portal_health_state.json`.
- **PASSO 5:** driver — `nvidia-smi` responde, `/dev/nvidia0` existe (hoje só há
  `/dev/nvidiactl`), `nvidia-persistenced` sai de `failed`. Se não:
  `OLLAMA_LLM_LIBRARY` fica em `cpu` — degradado é aceitável, **pausado para
  sempre não é**.
- **PASSO 6 (código antes da configuração, UM commit):** acrescentar
  `VRAMBytes int64 \`json:"size_vram"\`` (e `context_length`) a
  `internal/ollama/cliente.go:276-281` **sem remover `size`**, e trocar
  `saude.go:90-92` pelo par `sum(size_vram) <= 13 GiB` e
  `sum(size - size_vram) <= 2 GiB`. **Teste por mutação com os dois casos:**
  `/api/ps` sintético de GPU com 12 GiB de VRAM + 1 GiB de host **passa**; os
  mesmos modelos com `size_vram=0` e `size=16 GB` **reprova** — sem o segundo, o
  mutante "teto de VRAM = 99 GiB" sobrevive. **Medido: `internal/ollama` e
  `internal/cerebro` NÃO estão no grafo** ⇒ sem atestação.
- **PASSO 7 (configuração, no drop-in versionado
  `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`):**
  `OLLAMA_LLM_LIBRARY=cuda_v12` — hoje está explicitamente `cpu`, tem de ser
  **trocada, não apagada**; re-derivar `MemoryMax`/`MemorySwapMax` (12G/2G vinham
  de 19,4 GiB de RAM) e a justificativa de `OOMScoreAdjust=800`.
- **PASSO 8:** testar a hipótese **não medida** — uma requisição com modelo
  pequeno e leitura do journal procurando o tipo do KV cache e erro de flash
  attention, com `FLASH_ATTENTION=1` + `CONTEXT_LENGTH=8192` + `KV_CACHE_TYPE=q8_0`.
  Se bater a issue #18232, o contorno é `num_ctx` e ele **muda o produto** (janela
  de prompt da extração): registrar a decisão com número, nunca silenciar.
- **PASSO 9:** subir o cérebro, confirmar no log
  `fila ... (N tarefas recuperadas de worker anterior)`
  (`cmd/cerebro/main.go:170-172`) e rodar `cerebro enfileirar-embeddings`
  conferindo **`ja_no_indice=11.248`**; `novas>0` em volume **prova que o
  `vetores.f32` não chegou**.
- **PASSO 10:** re-medir contra o "antes" — `medir-recall-semantico` tem de
  **empatar**; `generate-comparacao-modelos-extracao --a <véspera> --b <nova>`
  com os cinco números (incluindo `dispositivos_por_acordao` e
  `eval_tokens_mediano`, que existem para pegar modelo que responde vazio);
  reagregar `ia_local_daily.jsonl`. **Repetir o experimento do lock (75 s × 29 s)
  com índice do git vazio E cache Go aquecido nas duas passadas** — o GOCACHE que
  o repositório usa de fato é **`/tmp/opt-wiki-go-cache` (3,9 GB)**, e
  `~/.cache/go-build` tem **0 B**, ao contrário do que a nota de memória afirma:
  frio, a primeira passada reprova por orçamento e o diagnóstico vai dizer
  "carga" — erro que duas sessões já cometeram.
- **PASSO 11 (critério medido de "a nova assumiu", tudo NA BORDA):**
  `check-edge-live` verde + 5 instâncias de túnel · zero
  `html_sha256_mismatch`/`public_html_missing` · `wikijuridica-server` de pé com
  `LISTEN_FDS=1` herdado do socket e `systemctl --failed` vazio · `recall@10` e
  MRR dentro do piso de determinismo · fila drenando com erro estável em ≤ 44 ·
  `tools/publicar-perfis-sociais --dry-run` que **não pede login**.
- **PASSO 12 (rollback):** a máquina velha fica de pé e o disco **não se apaga**
  até que a nova complete um ciclo noturno de `generate-backup-wiki` com
  `problema:""` e **dois** ensaios de `check-backup-restauravel` verdes.
- **PASSO 13 (consertos permanentes que a migração expõe):** criar o gate
  fila × índice de embeddings; **versionar os 30 hooks de `~/.claude/hooks`** (são
  as 8 guardas que o contrato trata como regra escrita em código); virar
  `/etc/systemd/system/ollama.service` symlink para `ops/` (ou capturá-lo em
  `tools/backup-host-state`, cujo glob hoje só pega `wikijuridica*`/`cloudflared*`);
  avaliar incluir `data/ai/{fila,grafo}.sqlite` e `data/ai/embeddings/` no backup
  (766 G livres em `/mnt/hdd` contra 46 MB + 133 MB + 302 MB); **editar para
  frente** o §12 do `CLAUDE.md`, o cabeçalho da unit do cérebro — que afirma
  `OLLAMA_MAX_LOADED_MODELS=1` e `MemoryMax=15G` quando o host mede **2** e
  **12884901888 B** desde 2026-09-10, comentário que mente sobre produção — e as
  seções (a)/(a2) de `ops/host-state/CHECKLIST-REBOOT.md`, que descrevem um
  notebook Intel com TLP/RAPL/Optimus/tampa, nada disso existente num Ryzen
  9800X3D de desktop.
- **PASSO 14 (janela):** respeitar 02:10–02:45 e 04:20–05:49, e o passo 2.6 do
  `deploy-publico` se houver republicação.

---

## 9. Evidência do descarte — as lacunas CONTROLADO

Registradas para ninguém reabrir. **C-1 e C-2 são [M]; C-3 a C-8 são [H]** dos
dossiês de escala e travessia, com a fonte nomeada em cada linha — nenhum deles
sustenta passo destrutivo sozinho, e todos são re-conferíveis por ferramenta
read-only já existente (a de cada item está no próprio item).

**C-1 — Ovo-e-galinha no pareamento.** `tools/check-v2-finalized-commit:33-34`,
`FINALIZED` só casa `data/editorial/v2_pages/…jsonl`; commit 1 (só portfólio) não
aciona `check_page_product`; `:1379` lê `portfolio_membership(old)`. Precedente
`376e4de4`→`e9b354dd` verificado por `git rev-parse`.

**C-2 — Grafo do `v2ingest`.** 98 pacotes in-module medidos; **0 de 6** pacotes do
plano dentro. `go list -deps` é proxy **exato** do walker (98 = 98, divergência
zero nos dois sentidos). Custos medidos: `go list` 5,65 s; gerar+comparar
atestação 7,62 s (exit 0, verde); `go.mod`/`go.sum` e índice limpos.

**C-3 — Sitemap.** Partição viva é `ShardPartitionAreaRevision`
(`sitemap.go:86`); tetos **5.000 URLs e 9 MB** (`sitemap.go:69-70`). O ordinal
**não é mais posicional**: `data/ops/sitemap_shard_registry.json` atribui número à
**chave de coorte** (`next_id=110`, 63 chaves, 35 tombstones, 6 aposentadas).
Servido hoje: 11.147 URLs em 57 shards, maior shard `pages-0103.xml` com 1.005 de
5.000. As 2.488 são `/jurisprudencia/` e formam **uma** coorte (a coorte é o
**dia**, `shard_partition.go:152-155`) = **1 shard novo, zero renomeados**; custo
de descoberta **melhora** (195 → 235 URLs/shard). Tetos do gate com folga 6,6×
(9,7 MB vs 64 MB). A memória "ordinal posicional some" descreve o defeito
**pré-registry**, já fechado. *Emenda da R9: o gerador **não carimba data
nenhuma** — ela vem de `publish-v2-direct:3838` — logo o P1b tem de **preservar o
fallback `opts.publishedAt`** para rota sem registro de estreia.*

**C-4 — IndexNow.** `MAX_URLS=1000` (`generate-indexnow-direct-submit:256`) é
**por requisição**, e o laço `:462-463` submete a lista toda. Ledger (109 lotes,
72.653 URLs): 2026-08-07 mandou **19.669 URLs em 20 lotes, 20 de 20 aceitos**;
08-19 mandou 10.351, 11 de 11. O único 403 histórico foi o lote **único** de
9.400 — tamanho de lote, não volume. Custo real de 2.488: **3 requisições, 1
execução, 0 dias de fila.**

**C-5 — Borda.** Ledger `edge_cache_warm.jsonl` (255 passadas): 23.714 URLs em
1.976,1 s a 12,00 r/s, 0 falhas. Aquecer 2.488 = **207 s**. Orçamento do deploy =
`URLs × 1,6 / 12` e a passada custa `URLs/12` ⇒ usa sempre **62,5 %** — margem
constante; o teto de 3.600 s só aperta acima de 43.200 URLs.
`PURGE_TETO = max(TODOS_N,3000)+1` nunca degrada para `purge_everything`.

**C-6 — Revalidação de bot.** Taxa de 304 em
`data/ops/access/nginx-2026-09-1{3,4,5}`: Googlebot 53,3 % (16/30), 54,5 %
(12/22), 60,5 % (23/38); Bingbot 15,3 %, 14,5 %, 5,3 %. Contra a linha de base do
defeito (`meta-externalagent` com **1** único 304 em 15.697). +2.488 páginas
novas **não re-datam** as 11.118 existentes ⇒ não disparam revalidação em massa;
o gatilho é script inline/markup em **todas**, não acréscimo de rota. O gerador
degrada o carimbo para **DIA** quando o lote ≥ 50 (`:580`), logo nenhum instante
compartilhado por ≥ 50 rotas.

**C-7 — Colisão de rota.** Medido no corpus real (60.221 registros): 10.414 de
mérito, 10.410 intents distintos, **4** colisões tratadas como recusa contada
(`main.go:283-288`, `Recusas["rota_duplicada_no_corpus"]++`). Colisão em 4 eixos =
**0** (10.410 candidatos × 11.438 portfólio × 11.206 shards × 11.106 manifesto ×
1.134 rotas). Ressalva: `protegidos` cobre `v2_pages` e **não** `portfolio_v2` —
medido **0 de 10.410**, hoje não morde.

**C-8 — Encoding.** 0 byte C1 em 10.414, 1 mojibake.

**C-9 — Cadeia A e `data/ai`.** Ver §6 e §7 — `grep` = 0 arquivos nos dois casos.

**C-10 — `check-v2-portfolio-pairing` é family-agnostic** (exit 0 hoje), e o censo
já tem `"jurisprudencia"` no `CATALOG` (`:67`) **e** `"jur"` no
`INTENT_PREFIX_AREA` (`:86`) — dupla cobertura, **zero linha nova**.

---

## 10. O que continua NÃO VERIFICÁVEL sem executar

Declarado sem maquiagem, cada um com o teste que o fecha.

| # | Não medido | Por que não deu | Teste que fecha |
|---|---|---|---|
| N1 | **Duração do pre-commit com 2.488 registros novos** | exigiria **commitar** | FASE 5 encenada com `-limite 50`, cronometrando `git commit`; extrapolar linearmente e **confirmar** no lote real. Maior estreia do precedente: 280 em 2 arquivos; maior shard de hoje: 1.074 |
| N2 | **Incidência real de ECA/adoção no corpus** | meu regex deu **326 (3,13 %)** e os **2 de 2** amostrados são falso positivo (*"adoção de providência"*, *"adoção de entendimento"*) — **o detector não serve** | Detector com âncora de instituto (ECA + artigo, "adoção" adjacente a "criança/adolescente/infante"), validado sobre amostra aleatória de 30 com revisão manual, **antes** de virar filtro. §5 do contrato exige o teste de falso positivo |
| N3 | **O poço de 4.763** (2.488 montáveis) | proibido repetir a passada de ~8 min já feita nesta sessão; número **herdado**, não re-medido por mim | FASE 2 (`-seco -limite 5000`), lendo as recusas nomeadas |
| N4 | **`./tools/go-modern generate ./internal/v2ingest` isolado** | **escreve**, e a sessão é read-only | 7,62 s (gerar+comparar) é **limite superior justo**: mesmo gerador + `cmp` |
| N5 | **Duração nova da onda com o passo do P6** | exigiria rodar a onda | Uma execução manual cronometrada de `run-daily-content` fora da janela, **antes** de ativar o passo (§7, ordem 4) |
| N6 | **Raio de ação do backlog do contentstore** em `internal/search`, `internal/publicrelease`, `internal/scaleindex` | não medido — **declarado como não medido** | O risco grave é condicional (§6, passo 8) e só morde se a release sharded for ativada |
| N7 | **Duração de `backup` 23:22, `datajud-fila` 00:37, `edge-warm` 01:25, `origin-warm`** | nenhum toma lock; não cronometrados | `systemd-analyze` / `journalctl -u <unit>` sobre as últimas 7 execuções, antes de usar as janelas 22:00–02:05 |
| N8 | **Hipótese do KV cache / flash attention na GPU** | a GPU ainda não existe neste host | PASSO 8 da migração, com leitura do journal |

---

## 11. O que o advisor mudou

**1. Exigiu a verificação que faltava, e ela mudou o sinal de uma decisão.** Eu
havia confirmado que `content.CanonicalPageType` **existe** (`content.go:336-339`)
sem nunca ler o **mapa** que ela consulta — e a FASE 1(b) inteira dependia disso
pelo *fail-open* da R10. Li `v2CanonicalPageTypes` (`:310-331`): `"julgado"` →
`"jurisprudencia"`, `ok=true`, fora de `allowed_page_types`. A decisão **fica de
pé e sai mais forte**: passa a ter duas barreiras independentes de CTA em vez de
uma. Se o mapa não tivesse a chave, a FASE 1(b) teria de mudar — eu teria
publicado uma instrução que põe 2.488 decisões judiciais sob política de convite
comercial.

**2. Isso me levou a um `grep -c` que derrubou um GRAVE (C4).** Ao conferir
`tools/publicar` no mesmo lote, contei as ocorrências de `systemctl` em
`cmd/publish-v2-direct/main.go`: **4**, não zero. O dossiê da travessia afirmava
"grep: zero systemctl/restart" e construía sobre isso o GRAVE de que 2.488 rotas
nasceriam 404 no canal de máquina. O código diz o contrário
(`:2257-2264` → `:2321-2334` → `reload-wiki-server:245`), e o comentário de
`:2240-2256` documenta esse mesmo defeito **como já corrigido**, com a medição de
origem. A L4 virou CONTROLADO com ressalva e colapsou dentro da L5. Não foi o
advisor que achou — foi o advisor que me mandou verificar a vizinhança de um
fato, e o segundo caiu junto.

**3. Bloqueou a entrega por uma seção ausente.** Esta. O pedido a exigia e eu a
havia omitido.

**4. Cobrou procedência em vez de aceitar a do refutador.** Eu abri a seção com
"re-verificadas nesta sessão contra o disco", o que era verdade para a maior parte
e **falso** para os números de Maria da Penha, ECA, colisões, µs/par, ledgers de
borda e IndexNow, taxas de 304, memória, digests de atestação e toda a migração.
Entrou a convenção **[M]/[H]**, aplicada item a item. Marcar herdado como medido
é exatamente a falha que a memória do projeto registra como *"'Medi' só depois de
rodar"*.

**5. Pegou o plano se contradizendo três vezes** — pathspec por diretório na FASE
1b contra a minha própria regra da L6; o commit de derivados **depois** do
IndexNow no DAG contra "antes do 9/9" na prosa e no §7; e `stf-informativo-derivada`
onde a chave real é `-derivado` (num documento cuja tese é que um byte errado
custa a sessão, o erro não é cosmético).

**6. Fechou duas portas que eu deixara abertas.** O ensaio de `-limite 50` ganhou
as duas consequências que ele dispara (a onda publica as 50; e a linha de
preservação inverte de "ausência esperada" para "ausência é alarme"). E o PASSO -1
da migração deixou de ser pergunta: **o NVMe migra**, com a reinstalação
rebaixada a contingência — o contrato proíbe devolver a escolha ao dono, e eu
havia escrito "decidir e escrever qual dos dois", que é a mesma pergunta com outro
verbo.

**O que eu não mudei, e por quê.** Mantive a decisão do C1 de trocar **os dois**
valores (lane e pageType) mesmo sabendo que isso leva 2.488 páginas ao pool
reprovado pelo `v2ingest` (1.335 → 3.823, +186 %): o ingest não está no caminho da
publicação (`v2publish.go:179`, medido), e as três instrumentações que a lane liga
valem mais que uma validação que hoje já não alcança nenhuma das cinco famílias
irmãs. E mantive a L1 como passo 1 absoluto, apesar de existir a válvula
`--redatacao-em-massa`: usá-la seria mascarar a guarda em vez de corrigir a causa,
e o deploy nem sabe passá-la.

---

*Todo comando citado foi conferido no repositório [M]: as 58 ferramentas de
`tools/` existem (`test -e`, zero faltando), os 4 gates existem em
`internal/checks/checks.go` (`text-truncation:451`, `derived-body-repetition:452`,
`published-manifest:763`, `percursos-fundamento-legal:793`), e as flags citadas
foram lidas no código-fonte de cada ferramenta.*
