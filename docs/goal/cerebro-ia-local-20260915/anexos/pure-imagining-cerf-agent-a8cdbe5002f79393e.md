# LACUNA 4 — escala no sitemap, no IndexNow e na borda ao publicar 2.488 de uma vez

Investigação somente-leitura. Data: 2026-09-15. Repo: /opt/wiki.

## VEREDITO: BLOQUEANTE — mas por UM motivo só, e não é nenhum dos cinco suspeitos

O sitemap, o IndexNow, a borda e a revalidação de bot estão **CONTROLADOS** e
medidos. Quatro das cinco preocupações da lacuna se descartam com número.

O que quebra é outro: **o teto de churn de `tools/generate-page-content-revision`
conta rota NOVA como re-datação**, e `tools/deploy-publico:1403` trata a recusa
dele como `exit 1`. 2.488 páginas novas = 18,29% > teto de 5% ⇒ **deploy aborta
no passo 6→7, com o acervo já no ar e a borda já purgada**.

---

## 1. SITEMAP — CONTROLADO

- Partição viva: `ShardPartitionAreaRevision` (`internal/sitemap/sitemap.go:86`),
  chave de coorte `<data-de-revisão>|<área>`, teto `PortalMaxURLsPerShard = 5000`
  (`sitemap.go:69`).
- **O ordinal NÃO é mais posicional.** `data/ops/sitemap_shard_registry.json`
  atribui o número à CHAVE da coorte (`shard_registry.go`), nunca à posição.
  Medido no disco: `next_id=110`, 63 chaves atribuídas, 35 tombstones, 6
  aposentadas. A memória "ordinal posicional some quando o plano encolhe"
  descreve o defeito **pré-registry** — foi fechado.
- Estado servido, contado por mim: **11.147 URLs em 57 shards**; maior shard
  `pages-0103.xml` = **1.005 URLs** de 5.000.
- **Efeito de +2.488:** as páginas de acórdão têm rota `/jurisprudencia/`
  (`cmd/generate-acordao-pages/main.go:810`). Publicadas num dia, formam **UMA
  coorte** `<hoje>|jurisprudencia` de 2.488 URLs ⇒ `⌈2488/5000⌉ = 1 shard novo`,
  número novo do registry. **Zero shards existentes mudam de URL.**
- Reordenação: não ocorre. As três condições que deslocam ordinal
  (`shard_partition.go:110-120`) são coorte esvaziar, cruzar `minCohortURLs=50`
  para baixo, ou a chave coalescida de uma data nascer/morrer. Uma coorte NOVA e
  GRANDE não dispara nenhuma.
- Guarda extra já existente: `conciliaRegistryDeShard`
  (`cmd/publish-v2-direct/main.go:3667`) **recusa** publicação que aposente mais
  de `atribuídas/4` coortes (hoje 63/4 = 15) sem `--permitir-churn-de-shard`.
  Publicar páginas novas aposenta zero.
- Custo de descoberta MELHORA: 11.147/57 = 195 URLs por shard hoje; com o shard
  novo, 13.635/58 = 235.
- Carência: `internal/sitemapgrace.Period = 8 * 24h` — shard aposentado serve 200
  fora do índice por 8 dias e só então é tombado. Não interage com página nova.

## 2. INDEXNOW — CONTROLADO, e o "1.000/dia" do plano é leitura errada

- `MAX_URLS = 1000` em `tools/generate-indexnow-direct-submit:256` é o teto **por
  REQUISIÇÃO**, não por dia. O laço de 462-463 fatia a lista inteira em lotes de
  1.000 e submete todos na mesma execução.
- **Medido no ledger** `data/ops/indexnow_direct_submissions.jsonl` (109 lotes,
  72.653 URLs):

  | dia | lotes | URLs | lotes aceitos |
  |---|---|---|---|
  | 2026-08-06 | 11 | 18.800 | 10 |
  | **2026-08-07** | **20** | **19.669** | **20 de 20** |
  | 2026-08-19 | 11 | 10.351 | 11 de 11 |
  | 2026-09-10 | 10 | 5.620 | 10 de 10 |

  O único 403 histórico (`SiteVerificationNotCompleted`) foi o lote ÚNICO de
  9.400 URLs em 2026-08-06 — tamanho de lote, não volume diário.
- **Custo real de descoberta de 2.488: 3 requisições, uma execução, zero dias de
  fila.** O portal já anunciou 19.669 URLs num dia com 20/20 aceitos.
- Canal separado e este sim limitado: `SubmitUrlBatch` do Bing Webmaster
  (`tools/generate-bing-submit-batch`) — cota lida ao vivo no ledger de hoje:
  `cota_diaria: 100`, `cota_mensal: 1600`. 2.488 páginas = **25 dias** nesse
  canal. É suplementar (pede rastreio de URL que o Bing nunca visitou) e **não
  governa publicação**; o sitemap e o IndexNow descobrem antes.
- O Google **não** participa do IndexNow (declarado no cabeçalho da ferramenta):
  para ele o canal é o sitemap, item 1.

## 3. BORDA — CONTROLADO

- `tools/warm-edge-cache`: default `--rps 25`, `--concorrencia 12`, metade do teto
  de 50/s da zona. O deploy chama a **12 rps / concorrência 4**
  (`deploy-publico:1094`).
- Throughput real, do ledger `data/ops/edge_cache_warm.jsonl` (255 passadas):
  **23.714 URLs em 1.976,1 s a 12,00 r/s, 0 falhas, 23.714 × HTTP 200**; passadas
  típicas de 11.2xx URLs em 934-939 s. O ritmo pedido é entregue exatamente.
- **Aquecer 2.488 = 207 s a 12 r/s (99 s a 25 r/s).** Com a gêmea Markdown,
  414 s — mas a passada Markdown é **opcional e desligada por padrão**
  (`warm-edge-cache:742`, `args.markdown`) e o deploy **não** a liga.
- Orçamento do deploy: `AQUECER_ORCAMENTO = URLs × 1,6 / 12`, piso 300 s, teto
  3.600 s (`deploy-publico:1090-1092`). Como a passada real custa `URLs/12`, ela
  usa sempre **62,5% do orçamento** — margem constante, independente da escala.
  Medido: hoje `AQUECER_URLS` (glob de `public/sitemaps/*.xml`) = 12.651 ⇒
  orçamento 1.686 s contra 1.054 s reais. Com +2.488: 15.139 ⇒ 2.018 s contra
  1.262 s. O teto de 3.600 s só passa a apertar acima de **43.200 URLs**.
- `s-maxage=604800` (7 dias) em `ops/nginx/wikijuridica.conf:1367`, e a Cache Rule
  viva é `edge_ttl.mode=respect_origin` (conf:968) — a borda honra esse valor.
- Expiração sincronizada **não é risco novo**: `HIT` não renova TTL, então o
  acervo já expira em bloco a partir da última busca na origem, e é a **purga do
  deploy** que zera o relógio de todos ao mesmo tempo. As 2.488 entram na mesma
  coorte de TTL que as 11.118. O timer `wikijuridica-edge-warm.timer` passa a cada
  12 h (04:25 e 16:21 UTC, conferido em `systemctl list-timers`), muito abaixo dos
  7 dias.
- Purga não degrada para `purge_everything`: `PURGE_TETO = max(TODOS_N, 3000) + 1`
  (`deploy-publico:1252-1254`), sempre maior que a lista.

## 4. GOOGLEBOT E AGENTES DE IA — CONTROLADO

- A regressão que o contrato cita (mtime/ETag zerados ⇒ revalidação em massa) foi
  **corrigida e a correção está medida**. Taxa de 304, contada por mim em
  `data/ops/access/nginx-2026-09-1{3,4,5}.jsonl`:

  | dia | Googlebot req | 304 | taxa | Bingbot | 304 | taxa |
  |---|---|---|---|---|---|---|
  | 09-13 | 30 | 16 | 53,3% | 59 | 9 | 15,3% |
  | 09-14 | 22 | 12 | 54,5% | 55 | 8 | 14,5% |
  | 09-15 | 38 | 23 | 60,5% | 133 | 7 | 5,3% |

  Contra a linha de base do defeito: `meta-externalagent` tinha **1 único 304 em
  15.697 requisições**. n pequeno por dia (22-38 no Googlebot) — declarado.
- **+2.488 páginas novas não re-datam as 11.118 existentes.** A republicação
  preserva mtime/ETag do que não mudou (`gravaDatado`), então os bots que
  revalidam continuam colhendo 304 no acervo antigo. O gatilho da regressão é
  mudança de **script inline / markup em todas as páginas**, não acréscimo de
  rota.
- `tools/check-efeito-nos-bots` mede exatamente isto, do log do **nginx** (nunca
  do ledger do Go, porque o acervo é estático e não passa pelo Go): taxa de 304
  (`inm=`/`ims=` no formato de log), canal Markdown por bot, e cobertura do
  Googlebot. Janela 14 dias, lag 14 dias, `N_MINIMO=100`, `EFEITO_MINIMO=0.20`.
  Read-only confirmado (nenhuma escrita no arquivo).

## 5. LASTMOD, CAUSALIDADE E A PURGA OBRIGATÓRIA — aqui está o BLOQUEANTE

### 5a. Os gates de re-datação, e por que passam

- `tools/check-lastmod-causalidade`: 1 causalidade (data não anda com hash igual),
  2 precisão honesta (nenhum INSTANTE ao segundo com ≥ `LOTE_MINIMO = 50` rotas),
  3 coerência com o sitemap servido, 4 `reviewed_at` não avança sem hash novo.
  **Passa:** o gerador degrada o carimbo para DIA quando o lote ≥ 50
  (`generate-page-content-revision:580-581`, `em_lote`), então 2.488 páginas novas
  gravam `AAAA-MM-DD` e não criam instante compartilhado.
- `tools/check-sitemap-lastmod-dispersion`: McNemar pareado do excesso de
  concentração do sitemap sobre o ledger, tolerância `max(3σ, deriva)`, e o ramo
  de reprovação só existe com `b ≥ 50` discordantes. **Passa:** as 2.488 entram no
  ledger com a mesma data com que entram no sitemap ⇒ `b = c = 0`, excesso zero.
- Pendência conhecida e benigna: `check-lastmod-causalidade` sai **exit 2
  (PENDENTE)** porque o ledger é gravado DEPOIS da purga, então o `<lastmod>` do
  ciclo entra no sitemap no ciclo seguinte. É desenho declarado, fecha na
  republicação seguinte.

### 5b. O BLOQUEANTE: o teto de churn conta rota NOVA como re-datação

`tools/generate-page-content-revision`:

```
115: LOTE_MINIMO = 50
135: TETO_CHURN_FRACAO = 0.05

568:  quantas_mudam = 0
569:  for caminho, digest in atual.items():
570:      entrada = anterior.get(caminho)
571:      if entrada is None:
572:          quantas_mudam += 1      # ← ROTA NOVA CONTA COMO CHURN
573:          continue
...
580:  em_lote = quantas_mudam >= LOTE_MINIMO
586:  total_rotas = len(atual)
587:  fracao = (quantas_mudam / total_rotas)
596:  if not args.ressemear and not args.purge_targets and fracao > TETO_CHURN_FRACAO:
599:      print("RECUSADO: o teto de churn barrou uma re-datacao em massa.")
608:      return 1
```

**PROVA DIRETA, rodada agora** (`tools/generate-page-content-revision --dry-run`
— o ramo `--dry-run` retorna na linha 764, antes de `escrita_atomica` e de
`grava_assinatura`, então não escreve nada):

```
carimbo  : instante UTC (3 rota(s) mudam; lote a partir de 50)
=== DATA DE REVISÃO POR CONTEÚDO ===
rotas publicadas    : 11118
rotas no registro   : 11116
novas               : 2
conteúdo mudou      : 1
--dry-run: nada escrito.
EXIT=0
```

`3 rota(s) mudam` = `novas 2` + `conteúdo mudou 1`. **A pré-passada conta rota
nova como churn — verificado no comportamento, não só na leitura do código.**
Hoje 3/11.118 = 0,03% e passa; com 2.488 novas o mesmo contador dá 18,29%.

Medido por mim: `content/pages.json` tem **11.118 rotas**.

| lote novo | total | fração | teto | resultado |
|---|---|---|---|---|
| 585 | 11.703 | 5,00% | 5% | último que passa |
| **2.488** | **13.606** | **18,29%** | 5% | **RECUSADO** |
| 3.893 (2.488+1.405 do P4) | 15.011 | 25,93% | 5% | RECUSADO |
| 4.763 (poço inteiro) | 15.881 | 29,99% | 5% | RECUSADO |

E `tools/deploy-publico:1403-1412` **aborta o deploy** nessa recusa:

```
1403: revisao_saida=$(tools/generate-page-content-revision "${revisao_args[@]}" 2>&1)
1405: if [[ $revisao_codigo -ne 0 ]]; then
1407:   if printf '%s' "$revisao_saida" | grep -q 'RECUSADO'; then
1409:     echo "  A guarda do gerador recusou deliberadamente. Deploy interrompido..."
1410:     exit 1
```

**O ponto do dano é a ordem.** A linha 1403 fica no fim do passo 6, depois de
tudo que sai para o mundo:

| linha | passo | já aconteceu quando a recusa dispara? |
|---|---|---|
| 460 | 1. republicar (`public/` reescrito) | **sim** |
| 877 | 5. subir | **sim** |
| 1047 | purga da borda | **sim** |
| 1094 | reaquecimento (12 r/s) | **sim** |
| 1255 | purga por lista + teto | **sim** |
| 1327 | reaquecimento dirigido | **sim** |
| 1372 | IndexNow (`--de-arquivo`) | **sim** |
| **1403** | **gravar `page_content_revision.jsonl`** | **RECUSA, exit 1** |
| 1414 | 7. conferir | **não roda** |

Consequência concreta: as 2.488 páginas ficam **no ar, anunciadas e aquecidas,
mas sem linha no ledger de revisão**. Três danos, nesta ordem de gravidade — e
o `<lastmod>` **não** é um deles: rota sem ledger cai no elo seguinte de
`content.Page.FreshnessDate` (**ContentRevisedAt → ReviewedAt →
PublicationDate**), e para página publicada hoje *hoje é a data certa*. O defeito
de 2026-08-28 foi re-datar 10.331 páginas **existentes**; aqui o fallback acerta.

1. **Laço permanente.** Sem linha de base no ledger, o `--purge-targets` do
   deploy SEGUINTE lista as 2.488 de novo, `quantas_mudam` volta a ≥ 18% e a
   recusa se repete — em todo deploy, até a guarda ser corrigida ou contornada
   à mão. É o dano que não se resolve esperando.
2. **Passo 7 (conferir) nunca roda**, então nada audita a publicação que acabou
   de ir ao ar.
3. **Dano colateral nas outras rotas do mesmo deploy:** qualquer rota
   legitimamente re-datada naquele ciclo também perde a atualização do ledger,
   porque a escrita é do arquivo inteiro (`escrita_atomica(LEDGER, payload)`,
   linha 770) e a recusa acontece antes dela.

### 5b-bis. A guarda JÁ foi contornada duas vezes, e não deixou rastro

Contado no ledger vivo, separando carimbo de DIA (lote) de carimbo de INSTANTE:

| dia | rotas com carimbo de DIA | fração de ~11.05x | teto |
|---|---|---|---|
| 2026-08-29 | 1.489 | 13,40% | 5% |
| **2026-09-10** | **1.400** | **12,67%** | 5% |
| 2026-09-11 | 456 | 4,10% | passou legitimamente |

E `content/pages.json` tinha **11.051 rotas em 09-09 e as mesmas 11.051 em
09-10** (conferido com `git show <commit>:content/pages.json`), então aquelas
1.400 eram rotas **existentes** re-datadas — exatamente o evento que o teto
existe para barrar. Duas rotas de contorno explicam, e **não consigo dizer qual
foi**:

- `--ressemear`, que é **isento por construção** (linha 596) e que o deploy sabe
  passar;
- `--redatacao-em-massa='<motivo>'`, manual.

Não consigo distinguir porque **o motivo nunca é gravado**. O comentário da linha
132 afirma que ele "fica GRAVADO no ledger"; o código apenas o **imprime**
(linhas 597-609), e cada registro do ledger tem só
`path`/`content_sha256`/`revised_on`/`served_sha256`. É comentário que mente
sobre produção — bug a corrigir pela regra do próprio projeto, e o motivo pelo
qual uma autorização de re-datação em massa hoje é inauditável.

**A armadilha derivada, e ela é séria:** `--ressemear` dodge o teto, e alguém sob
pressão vai usá-lo para fazer as 2.488 passarem. Não use. Sob `--ressemear` o
ramo de IndexNow do deploy fica **calado por construção** (`deploy-publico:1365`
exige `RESSEMEAR -eq 0`), então 2.488 páginas **novas** iriam ao ar sem nenhum
anúncio — e a matriz do §6 já classifica página nova como mudança de texto
editorial, para a qual `--ressemear` é o flag errado.

O diagnóstico preciso: **a guarda mede a coisa ao lado.** O laço principal já
distingue `novas` de `mudadas` (linhas 649-656), mas a pré-passada que alimenta
`fracao` não faz essa distinção. Rota nova não é re-datada — ela não tem data
anterior para mover; `revised_on = hoje` é a verdade para uma página publicada
hoje. O teto existe contra "re-datação em massa ACIDENTAL e SILENCIOSA" (o
ida-e-volta de 8.245 URLs de 2026-08-28) e está acertando um evento que é
legítimo por construção.

Precisão do conserto: a contagem tem **dois consumidores com requisitos
opostos**, e por isso não se pode simplesmente excluir as novas do laço:
- `em_lote` (linha 580) **deve** continuar contando as novas — é ele que degrada
  o carimbo para DIA e evita 2.488 instantes idênticos ao segundo (é o que faz
  `check-lastmod-causalidade` passar);
- `fracao` (linha 587) **não deve** contar as novas — só re-datação é churn.

**E o denominador tem de mudar junto, ou a correção abre um ponto cego.** Manter
`total_rotas = len(atual)` e só tirar as novas do numerador faria 600 re-datações
reais desaparecerem sob um lote grande: `600 / 13.606 = 4,4%` passaria, quando
`600` re-datações em `11.118` rotas datáveis são 5,4% e devem reprovar. O
denominador honesto é o conjunto que **podia** ser re-datado:

```
redatadas = rotas com entrada no ledger cujo content_sha256 ou served_sha256 mudou
fracao    = redatadas / len(anterior)          # rotas já no ledger, não len(atual)
```

### 5c. Purga ampla obrigatória pela matriz do contrato

Pela matriz do §6, publicar página nova é **mudança de texto editorial**: deploy
**sem** `--ressemear`, e "a purga do deploy basta". Não há purga ampla manual
obrigatória neste evento — ela é exigida por **script inline** e por **malha de
links / bloco de relacionados**. Atenção ao efeito colateral: as 2.488 páginas
entram no `content/legal_cocitation_index.jsonl` (passo 2.6, `deploy-publico:652`)
e portanto no bloco `## Percursos por fundamento legal` da gêmea Markdown de
páginas **já publicadas**. Isso é alteração de malha nas vizinhas — o servido
muda, o texto autoral não. O `served_sha256` enxerga; quem decide a purga é a
lista de `--purge-targets`, que já cobre bytes servidos.

---

## O EFEITO MEDIDO DE PUBLICAR 2.488 DE UMA VEZ

| eixo | efeito | veredito |
|---|---|---|
| shards de sitemap | +1 shard (2.488 de 5.000); 0 shards renomeados | controlado |
| índice de sitemap | 57 → 58 entradas; 195 → 235 URLs/shard | melhora |
| churn de ordinal | 0 deslocamentos (registry por chave) | controlado |
| IndexNow | 3 requisições, 1 execução, 0 dias de fila | controlado |
| Bing SubmitUrlBatch | 25 dias a 100/dia (canal suplementar) | não governa |
| aquecimento de borda | +207 s a 12 r/s; orçamento usa 62,5% | controlado |
| TTL da borda | mesma coorte de expiração já existente | controlado |
| 304 dos bots | acervo antigo não é re-datado; 304 do Googlebot 53-60% | controlado |
| gates de lastmod | causalidade e dispersão passam (carimbo vira DIA) | controlado |
| **teto de churn** | **18,29% > 5% ⇒ deploy exit 1 no passo 6→7** | **BLOQUEANTE** |

## A SEQUÊNCIA QUE MINIMIZA DANO DE DESCOBERTA SEM FREAR A PUBLICAÇÃO

Não há freio a propor: nenhum dos canais de descoberta é o gargalo. O que a
sequência precisa garantir é que o ledger de revisão **exista** para as rotas
novas no mesmo ciclo em que elas vão ao ar.

1. **Corrigir o teto de churn antes de publicar em lote** (é o único passo
   obrigatório): separar as duas contagens em
   `tools/generate-page-content-revision` — `em_lote` conta novas + re-datadas;
   `fracao = redatadas / len(anterior)` conta só re-datadas (`entrada is not
   None` e `content_sha256`/`served_sha256` mudou). Teste de regressão por
   mutação: lote de 600 novas + 10 re-datadas **passa**; lote de 600 re-datadas
   sobre 11.118 no ledger (5,4%) **continua recusando**; e com a correção
   desligada o primeiro caso volta a recusar (senão o teste não testa nada).
1b. **No mesmo commit, gravar o motivo da autorização.** Hoje
   `--redatacao-em-massa` só imprime (linhas 597-609) enquanto o comentário da
   linha 132 afirma que ele "fica GRAVADO no ledger". Acrescentar o motivo ao
   artefato — ou corrigir o comentário — é o que torna auditável uma re-datação
   em massa autorizada, e é o que falta para eu poder dizer hoje como 09-10 e
   08-29 passaram.
1c. **Proibir explicitamente `--ressemear` como rota para o lote.** Ele é isento
   do teto (linha 596) e cala o IndexNow (`deploy-publico:1365`): usá-lo mandaria
   2.488 páginas novas ao ar sem anúncio.
2. Publicar o lote pelo pipeline sancionado, deploy **sem** `--ressemear`.
3. Deixar o deploy purgar e reaquecer (não purgar de novo; se ele imprimir
   `purgando tudo`, ler o MOTIVO antes de agir).
4. Deixar o IndexNow do próprio deploy anunciar (3 lotes de 1.000).
5. Conferir, em ordem: `tools/check-sitemap-shard-churn --max-deslocamento 0`,
   `tools/check-sitemaps`, `tools/check-lastmod-causalidade` (exit 2 PENDENTE é
   esperado neste ciclo), `tools/check-sitemap-lastmod-dispersion`,
   `tools/check-sitemap-discovery-cost`.
6. Confirmar no disco que `data/ops/sitemap_shard_registry.json` ganhou a chave
   `<data>|jurisprudencia#0` e **commitá-lo**. O boot **não** corre risco: o
   servidor lê o arquivo do DISCO (`PortalPlanOptionsLendoRegistry(repository.Root)`)
   e `publish-v2-direct:3699` grava antes de emitir qualquer artefato, por
   desenho declarado ("Salva ANTES dos artefatos"). O risco é outro e é real:
   hoje o arquivo está `M` (não commitado), com `next_id` 101 → 110 só no working
   tree, e ele é a **única memória dos 35 tombstones** — números que já
   responderam 410 e não podem voltar. Perder o working tree é perder essa
   memória, e é também a violação de "produto não fica untracked".
7. Medir o efeito 14 dias depois com `tools/check-efeito-nos-bots`.

**Se a correção do passo 1 não for feita nesta sessão**, há só duas rotas, e
nenhuma é uma flag do deploy:

- **Fatiar em lotes de ≤ 585 rotas novas por deploy** (5% de 11.703) — 5 deploys
  para as 2.488. Honesto, e o número sobe a cada ciclo porque o denominador
  cresce.
- **Rodar o gerador à mão depois do deploy ter saído com exit 1**, com
  `--redatacao-em-massa='<motivo>'`. Atenção: **`deploy-publico` não sabe passar
  essa flag** — `revisao_args` (linhas 1398-1402) carrega apenas `--ressemear`.
  Não é "um parâmetro a acrescentar no deploy": é intervenção manual depois de o
  deploy já ter abortado, com a borda purgada e o passo 7 não executado. E o
  motivo é só **impresso**, não gravado no ledger (linhas 597-609), então não
  deixa rastro auditável — além de descrever o evento errado: não houve
  re-datação, houve publicação.

Corrigir a guarda é o certo, e destrava também o P4 (1.405 páginas ⇒ 25,93%) e o
P8 (49.807), que estão muito além de qualquer fatiamento viável.

## O que o advisor mudou

1. **Exigiu o teste que discrimina, e eu não o tinha feito.** Apontou que o
   registry e o ledger já mostravam dias acima de 5% (09-10 com 1.428, 08-29 com
   1.489) e que, sem explicá-los, meu veredito era leitura de código, não
   medição. Fui atrás: rodei `--dry-run` (write-free, confirmado na linha 764) e
   ele imprimiu `3 rota(s) mudam` = `novas 2 + mudou 1`, **provando no
   comportamento** que rota nova conta como churn. Depois separei carimbo de DIA
   de INSTANTE (1.400 em 09-10) e conferi por `git show` que as rotas de
   `pages.json` não cresceram naquele dia — então foram re-datações de
   existentes, passadas por `--ressemear` ou `--redatacao-em-massa`. O veredito
   se confirmou e ganhou a seção 5b-bis, que antes não existia.
2. **Corrigiu um dano que eu tinha exagerado.** Eu escrevia que a falta de linha
   no ledger jogaria o `<lastmod>` no fallback e repetiria o desastre de
   2026-08-28. Errado: aquele defeito foi re-datar páginas **existentes**; para
   página nova, hoje É a data certa e o fallback acerta. Substituí por os três
   danos reais — o **laço permanente** (todo deploy seguinte recusa de novo), o
   passo 7 que não roda, e a perda do ledger das outras rotas re-datadas no mesmo
   ciclo, porque a escrita é do arquivo inteiro.
3. **Fechou um ponto cego na minha própria proposta de conserto.** Eu tirava as
   novas do numerador e mantinha `total_rotas = len(atual)` no denominador — o
   que faria 600 re-datações reais (5,4% das datáveis) passarem como 4,4% sob um
   lote grande de páginas novas. O denominador honesto é `len(anterior)`.
4. **Apontou que `--redatacao-em-massa` não é flag do deploy.** `revisao_args`
   só carrega `--ressemear`, então aquela "opção" é intervenção manual **depois**
   do `exit 1`, com a borda já purgada. Reescrevi a alternativa nesses termos.
5. **Corrigiu minha afirmação sobre o boot.** Eu dizia que o registry não
   commitado arriscava derrubar o boot; o servidor lê o **disco**, e
   `publish-v2-direct:3699` grava antes dos artefatos. O risco é perda dos 35
   tombstones e a violação de "produto não fica untracked" — não o boot.
6. **Pediu a varredura de outras guardas no publicador.** Feita:
   `grep -n RECUSADO cmd/publish-v2-direct/main.go` devolve um único ponto (3675,
   aposentadoria de shard), que publicar página nova não toca. Nenhuma guarda de
   volume extra a incluir na sequência.

Confirmou sem mudanças os quatro eixos controlados (sitemap, IndexNow,
aquecimento, série de 304) e o `PURGE_TETO` que nunca degrada.
