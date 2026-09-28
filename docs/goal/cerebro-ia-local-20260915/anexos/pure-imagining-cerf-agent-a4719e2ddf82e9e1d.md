# REFUTAÇÃO ADVERSARIAL — as seis lacunas do plano de produção

Sessão read-only (PLAN MODE), /opt/wiki, 2026-09-15. Tudo abaixo é leitura de
código, dado ou git de hoje. Onde não medi, está escrito **NÃO MEDIDO** e por quê.

**Veredito global:** as seis investigações são muito boas em comando e em linha.
O ataque 3 (comando inventado) **FALHA**: 46 de 46 ferramentas existem, os nomes
de gate existem, todas as flags existem. O que sobrevive ao ataque são **um
conflito real de ordem**, **duas premissas descartadas com evidência errada**,
**uma edição sem justificativa** e **duas colisões entre frentes**.

**Uma das minhas próprias conclusões caiu na verificação e está retratada
abaixo (R5).** Ela é a lição mais cara deste dossiê.

---

## R1 [MÉDIO] "v2ingest NÃO está no caminho" — a conclusão operativa está certa, a premissa não

**Alvo:** travessia, bloco CONTROLADO.

O v2ingest **roda, ingere essas shards e grava a reprovação**. O que não
acontece — e é o que a travessia de fato precisa — é a reprovação *barrar* a
publicação: `publish-v2-direct` lê o glob (`internal/v2publish/v2publish.go:179`).

**Medido** em `data/ops/v2_ingest_report.jsonl` (11.185 linhas, mtime 2026-09-11
02:57:38), contagem própria:

| família | reprovadas | linhas | % |
|---|---|---|---|
| stj-tema-derivado | 1.074 | 1.074 | 100,0% |
| stj-sumula-derivada | 112 | 112 | 100,0% |
| stf-informativo-derivado | 60 | 60 | 100,0% |
| noticias-oficiais | 48 | 48 | 100,0% |
| diarios-municipais | 41 | 41 | 100,0% |
| **total** | **1.335** | **1.335** | **100,0%** |

Três códigos por registro: `portfolio_lane_invalid`,
`portfolio_page_type_invalid`, `lane_invalid` (1.335 cada). Réguas:
`internal/v2ingest/validate.go:64-67` (`validLanes = {comercial, informativa}`),
`:56-61` (`wordCountBands` = verbete/pergunta/guia_problema/procedimento),
`:618-621`, `:674`.

Hoje `(verbete, informativa)` passa nessas **duas** réguas — a FASE 1 a move para
o pool reprovado: **1.335 → 3.823 (+186%)**. E a cadeia-topologica PASSO 8 manda
**rodar** esse ingest no mesmo ciclo.

Ressalva de honestidade: verifiquei lane e page_type. As demais reprovações
possíveis (hosts de fonte, comprimento de title/meta, seções ≥ 2) são **NÃO
MEDIDAS** para uma shard que ainda não existe.

**Emenda:** declarar a reclassificação no commit. **Não** consertar
`validLanes`/`wordCountBands`: isso cai dentro de `internal/v2ingest` → commit de
grafo com atestação (~611 s, 25+ testes), o custo que grafo-atestacao mostrou que
o plano evita.

---

## R2 [GRAVE] FASE 1(b) `pageType → "julgado"` — mantenha a edição, mas ela está sem justificativa e leva uma perda silenciosa junto

**Alvo:** travessia FASE 1(b). Nenhum dos 9 achados dela menciona pageType; o
BLOQUEANTE trata só de lane.

**Investiguei se era para remover, e a resposta é não — a edição está
semanticamente certa:**
- `internal/content/content.go:310-331`: `"verbete"→"wiki"`,
  `"julgado"→"jurisprudencia"`. Ambos em `LegalPageTypes` (`:40-50`).
- `content/legal_marketing_policy.json`: `allowed_page_types = ['artigo',
  'pergunta']` — **lido da fonte, não do comentário**. `wiki` e `jurisprudencia`
  estão os dois fora; nenhum habilita CTA.
- A irmã que publica decisão de tribunal (`stf-informativo-derivado-01`) usa
  exatamente `page_type: "julgado"`. Um acórdão tipado como *verbete de
  glossário* é, com boa probabilidade, o defeito que o autor corrigiu e esqueceu
  de justificar.

**O que ela leva junto, e ninguém escreveu:** `"julgado"` não está em
`wordCountBands`, então `validate.go:674` — `if band, known :=
wordCountBands[verdict.PageType]; known` — **vira no-op**: a banda de 315–770
palavras deixa de ser verificada por máquina. E o comentário de `main.go:82-83`
("*Banda do `verbete` em internal/v2ingest/validate.go:56*") passa a **mentir**
sobre a origem de `pisoPalavras=350`/`tetoPalavras=700` — R1 do contrato.

**Emenda:** **manter (b)**, acrescentar a justificativa ao commit, reescrever o
comentário de `:82-83` para dizer que a banda passa a ser garantida só pelo
gerador, e registrar a perda.

---

## R3 [GRAVE] Conflito real: a ordem da revisão de conteúdo. Os dois runners têm ordens OPOSTAS e nenhum dossiê diz qual manda

**Alvo:** cadeia PASSO 7 (*"OBRIGATORIAMENTE ANTES do publish"*) × escala
(*"corrigir o teto e não a ordem; o registro só avança depois da purga"*).

**Medido — os dois estão certos, sobre runners diferentes:**
- `tools/run-daily-content:674` revisão → `:684` publish. O comentário :652-667
  diz que `publish-v2-direct` lê o carimbo para o HTML, o `<lastmod>` e o
  `Last-Modified`. **Na onda, ANTES.**
- `tools/deploy-publico:464` publish → `:1403` revisão. **No deploy, DEPOIS.**

**A falha é do plano combinado:** travessia FASE 7 publica pelo **deploy**. Quem
ler os três dossiês roda a revisão à mão antes do deploy (PASSO 7), e o deploy a
roda **de novo** em `:1403`.

**Emenda:** a ordem é **propriedade do runner**, não do artefato. O P6 publica
pela FASE 7 e herda a ordem do **deploy** — e por isso depende do R4.

---

## R4 [BLOQUEANTE] travessia FASE 7 não cita o bloqueante da escala-descoberta, e morre nele

`tools/generate-page-content-revision:569-572` conta `entrada is None` (rota
nova) como churn; `:587` `fracao = quantas_mudam / total_rotas`; `:135`
`TETO_CHURN_FRACAO = 0.05`; `:596` `if not args.ressemear and not
args.purge_targets and fracao > TETO_CHURN_FRACAO` → `:604 return 1`. Chamado em
`deploy-publico:1403`, **depois** de republicar (:464), purgar, aquecer e
anunciar ao IndexNow.

Correção de leitura: a isenção de `:596` cobre **`--ressemear` E
`--purge-targets`** (a escala citou só o primeiro). Conclusão dela inalterada.

**Emenda:** FASE 7 fica **bloqueada por escala PASSO 1**, escrito no passo.

---

## R5 [RETRATADO] "P1b e P6 não podem compartilhar um deploy" — eu estava errado, e o motivo importa

Eu havia afirmado que consertar `datePublished`/`dateModified` no JSON-LD mudaria
`served_sha256` de 944 rotas (8,49% > 5%) e exigiria `--ressemear`. **Fui
verificar antes de entregar e a premissa é falsa.**

`tools/generate-page-content-revision:266-307` — `neutraliza_datas()` — substitui
**toda data ISO** por `@DATA@` antes de hashear, e a docstring nomeia exatamente
`article:modified_time`, `dateModified`, `datePublished` e `<time datetime>`
(`DATA_ISO_NO_HTML`, `:246`). Neutraliza também a mesma data por extenso em PT-BR
e em `dd/mm/aaaa`, com fronteira de palavra. `conteudo_servido()` (`:362-380`)
aplica isso a todo HTML servido.

**Consequência:** o conserto de datas do P1b produz **zero** mudança de
`served_sha256` e **zero** churn. Não dispara o teto, não precisa de
`--ressemear`, e P1b e P6 **podem** dividir um deploy.

O que fica de valioso, invertido: **quem reagir ao achado 3 da escala
(*"--ressemear é bypass"*) usando `--ressemear` no deploy do P1b vai calar o
IndexNow (`deploy-publico:1365` exige `RESSEMEAR -eq 0`) e proibir
`--desde-commit`, em troca de nada** — a isenção que ele daria já é dada pela
neutralização. Registre no passo do P1b: **sem `--ressemear`**.

Ressalva: isso vale para mudança **só de datas**. Alteração *estrutural* de
JSON-LD (campo novo, URL de Legislation) muda bytes não-ISO, aí sim conta como
churn — é o caso que a memória do projeto registra.

---

## R6 [GRAVE] Pathspec e `git add` por DIRETÓRIO, contra o contrato e contra a própria concorrencia

**Alvo:** travessia FASE 4 (`git commit -F … -- data/editorial/portfolio_v2`) e
FASE 5 (`-- data/editorial/v2_pages`); cadeia PASSO 3 e 5 (`git add
data/editorial/portfolio_v2` — **add** por diretório).

Contra o CLAUDE.md de máquina (*"`git add <caminho exato>`, nunca por
diretório"*) e contra a concorrencia (*"o pathspec leva o conteudo da WORKTREE"*).
A onda escreve nesses dois diretórios e faz `git add` por diretório lá
(`run-daily-content:615,632`), duas vezes por dia (04:20+rand15 e 12:20).

**Medido — a janela está vazia, não fechada:** `git status --short
data/editorial/portfolio_v2 data/editorial/v2_pages` = **0 arquivos**;
`git diff --cached --name-only` = **0**.

**Emenda:** caminho exato nos **dois** lados
(`…/stj-acordao-derivado-01.jsonl`), e reconferir `git status --short` nesses
dois diretórios imediatamente antes de cada commit.

---

## R7 [MÉDIO] Três números que não conferem com o repositório de hoje

1. **`content.Page.FreshnessDate` não existe** — `grep -rn FreshnessDate
   internal/` = **0**. A função real é `content.Page.LastModified()`
   (`internal/content/content.go:453`), precedência `ContentRevisedAt →
   ReviewedAt → PublicationDate` documentada em `:444`. A *cadeia* que a escala
   descreve está certa; o **nome**, não. Importa porque `LastModified()` alimenta
   a chave de coorte do sitemap (`revisedOn + "|" + area`,
   `internal/sitemap/shard_registry.go:317`, via `shard_partition.go:147`) e passa
   por `validateRevisionDate` (`shard_partition.go:601-617`), **que roda no
   BOOT** — o comentário :606-610 diz que recusar ali *"derruba o processo"*.
2. **`public/`: o contrato está desatualizado, a migracao está certa.** Medido:
   `find public -name index.html | wc -l` = **11.357**; `*.html` = **11.358**.
   CLAUDE.md §6 diz 10.369.
3. **A citação `:274` do próprio gerador está obsoleta.** `main.go:96-101` cita
   `check-derived-authorial-floor:274` para limiar e shingle de unicidade; hoje
   são `TAMANHO_SHINGLE_UNICIDADE = 3` em **:288** e `LIMIAR_UNICIDADE = 0.70` em
   **:289** — `:274` é linha de comentário. A travessia repetiu sem conferir.

**O resto da paridade CONFERE**, uma a uma: `PISO_AUTORAL 250` :262 ✓,
`TETO_CITADO 0.55` :263 ✓, `MINIMO_CITACAO_OFICIAL 25` :264 ✓,
`FAMILIAS_CANAIS_DERIVADOS` :279-286 com 6 famílias ✓, `pares_quase_identicos`
:491 ✓, docstring *"205 páginas — 20.910 pares"* ✓ (obsoleta, como ela diz). A
maior família que medi no ingest é **stj-tema-derivado = 1.074** — o mesmo número
que a travessia usa.

**O grafo confere: 98 pacotes**, recomputado com `go-modern list -deps`.
**DENTRO:** publicpath, ptbrtext, quality, lexml, strictjson, publishedmanifest,
seo, content. **FORA:** v2bodyneardup, sitemap, legalcocitation, stjacordaos,
cerebro, ollama, checks, render. Os 6 que grafo-atestacao declarou fora estão
fora, e o R3 dele já nomeia publishedmanifest/quality/lexml como pacotes a
evitar. **Investigação sólida.**

**NÃO MEDIDO:** (a) o poço `2.488+1.405+682+165+22+1 = 4.763` — a concorrencia
proíbe repetir a passada de ~8 min, já feita nesta sessão; herdado. (b) duração
do pre-commit com 2.488 registros — exigiria commitar.

---

## R8 [ATAQUE 3 — falha] Os comandos executam. Verifiquei 46

Todas as 46 ferramentas citadas existem em `tools/`. Nomes de gate em
`internal/checks/checks.go`: `text-truncation` (:451,:1908),
`derived-body-repetition` (:452,:1910), `percursos-fundamento-legal`
(:793,:1669), `published-manifest` (:763,:2296). Flags conferidas: `--index`,
`--depois`/`--minimo`, `--max-deslocamento`, `--jobs`, `--write`, `--max`,
`--agent`/`--last`, `-seco`/`-limite` (default **30**, `main.go:185-186`).
`tools/check-derived-authorial-floor` tem **zero** chamada de escrita → read-only
de fato. Ressalva de forma: cadeia PASSO 9 escreve `-allow-public-write` e o
deploy usa `--allow-public-write` — o `flag` do Go aceita as duas.

---

## R9 [MÉDIO] O sitemap "CONTROLADO" sobrevive, mas não pelo motivo declarado

Confirmei o mecanismo: a coorte é o **dia** (`content.RevisionDay(lastMod)`,
`shard_partition.go:152-155`) e os tetos do portal são **5.000 URLs e 9 MB**
(`sitemap.go:69-70`) — a escala citou só o de URLs; 2.488 entradas ficam muito
abaixo de 9 MB. Conclusão dela mantida.

O que a sustenta: o gerador **não carimba data nenhuma** (grep por
`ReviewedAt|PublicationDate|published_at` em `cmd/generate-acordao-pages/main.go`
devolve só `VerifiedAt` de fonte, :120, e `FetchedAt` de norma, :160). A data vem
de `cmd/publish-v2-direct/main.go:3838` —
`primeiroNaoVazio(page.PublicationDate, opts.publishedAt)`.

**Emenda (restrita):** o P1b tem de **preservar o fallback `opts.publishedAt`
para rota sem registro de estreia**. É ele que dá às 2.488 um único dia e, com
isso, uma única coorte.

---

## R10 [MÉDIO — achado novo] `v2publish` faz *fail-open* de page_type desconhecido para `"artigo"`, que é o tipo que ABRE o CTA comercial

Encontrado ao verificar o R2, e nenhuma das seis o cobre.

`internal/v2publish/v2publish.go:347-350`:
```go
pageType := "artigo"
if canonical, ok := content.CanonicalPageType(page.PageType); ok {
    pageType = canonical
}
```
`allowed_page_types = ['artigo', 'pergunta']`, e
`internal/legalmarketingpolicy/policy.go:181` testa
`allowed(policy.AllowedPageTypes, page.PageType)` **sobre o tipo canônico**. Logo
**todo page_type fora de `v2CanonicalPageTypes` vira `"artigo"` e passa a ser
admitido pela política de CTA comercial** — fail-open no elo de ética.

Hoje não morde, e digo por quê para não exagerar: `"verbete"` e `"julgado"` são
os dois conhecidos, e a lane `derivada_de_fonte_oficial` mantém
`CommercialCTAAllowed()` falso (`content.go:466-468`, que lê `CTALane`).
**Mas a FASE 1(b) edita exatamente essa constante.** Um typo, ou um
`"acordao"` inventado em vez de `"julgado"`, põe 2.488 páginas de decisão
judicial sob a política que admite convite comercial — Provimento OAB 205/2021.

**Emenda:** ao editar `main.go:76`, usar **só** valor presente em
`v2CanonicalPageTypes` e provar por teste que `content.CanonicalPageType(pageType)`
devolve `ok == true`.

---

## R11 [GRAVE] Ordem P1b × P6: as duas investigações se contradizem, e o prazo real é a FASE 7c

- **concorrencia:** *"Executar P1b … antes de P6: sem a data de estreia correta,
  cada pagina nova de P6 nasce com o mesmo defeito."*
- **travessia:** *"P1b e pre-requisito da SEGUNDA publicacao desta familia, nao
  da primeira"* — no dia 1 o fallback HOJE **é** a data verdadeira.

A travessia está certa sobre o dia 1 (as 2.488 não têm chave em
`first_published_at.json` em nenhuma ordenação). Mas ninguém escreveu o prazo:
**FASE 7c registra a família no runner com `-limite 200`**, o que torna a
**segunda** publicação automática na próxima onda das 04:20.

**Emenda / reconciliação:** *P1b tem de pousar **antes** do commit da FASE 7c —
ou antes da primeira onda após o P6, o que vier primeiro.* Depois disso, cada
página nova nasce com o defeito de cronologia e a família entra na conta das 944.

---

## Ordem mínima que este ataque impõe

1. **escala PASSO 1** (teto de churn) antes de qualquer deploy em lote — R4.
2. Manter FASE 1(b), com justificativa + comentário `:82-83` reescrito + prova de
   `ok == true` em `CanonicalPageType` — R2, R10.
3. Declarar no commit da lane a reclassificação 1.335 → 3.823; **não** tocar
   `internal/v2ingest` — R1.
4. Caminho **exato** em todo `git add` e todo pathspec — R6.
5. Deploy do P6 **sem** `--ressemear`; deploy do P1b **também sem** — R5.
6. **P1b antes do commit da FASE 7c** — R11.
7. Declarar que a ordem da revisão é do **runner** — R3.

## O que o advisor mudou

Cinco correções, e uma delas derrubou a minha melhor conclusão:

1. **Mandou verificar no código a premissa do meu R5**, que eu havia inferido da
   prosa do §6 do CLAUDE.md ("script sem atributo") sem ler a neutralização. Li:
   `neutraliza_datas()` apaga **toda data ISO** antes de hashear. **R5 retratado.**
   Era exatamente o erro que o contrato chama de "comentário/prosa não é fonte" —
   eu teria entregue uma regra de dois deploys sem mecanismo por trás.
2. **Mandou checar o que o tipo canônico dirige antes de recomendar remover a
   FASE 1(b).** Dirige o CTA via `legalmarketingpolicy:181`, e `julgado` é o que a
   irmã que publica decisão usa. **R2 invertido: manter a edição**, não removê-la.
   E a verificação produziu o **R10**, que eu não teria encontrado.
3. **Rebaixou R1 de BLOQUEANTE para MÉDIO**: a minha própria medição prova que a
   reprovação nunca barrou publicação, então o que resta é declaratório. Manter o
   grau alto diluiria R4 e R6, que bloqueiam de verdade.
4. **Cortou o excesso do R9**: as 2.488 não têm registro de estreia em nenhuma
   ordenação, então a coorte é única de qualquer forma; a emenda virou preservar
   o fallback `opts.publishedAt`.
5. **Apontou que eu havia afirmado a ordem P6→P1b sem dizer que ela contradiz a
   concorrencia.** Virou o **R11**, com o prazo concreto (o commit da FASE 7c).
