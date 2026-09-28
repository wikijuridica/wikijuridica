# Frescor Diário — WikiJurídica como fonte viva para bots de busca e agentes de IA

> Plano de engenharia. Tudo aqui é para **esta sessão**. Nenhum item é "depois", "futuro" ou
> "próxima sessão". Onde faltar ferramenta, ela é construída aqui. **Zero stub** (§12).
>
> **★ BLOQUEADOR SE RESOLVE NESTA SESSÃO — pré-existente ou não (ordem do dono, 2026-08-20).**
> *"O produto tem que ser completo, se não perde a lógica."* Não existe "isso já estava quebrado
> antes" nem "isso depende de outra frente": defeito encontrado no caminho **entra no escopo e é
> corrigido aqui**. As fases são ordem de **dependência**, nunca cronograma. Concretamente, isto
> significa que entram nesta sessão, e não como ressalva: a causa da queda do Googlebot (§1.0), o
> `checked_at` mentindo (§1.2, item d), o `--since` seguro (§7, item 6), o modelo do sumarizador (§5), o gate de
> citação legal e o anonimizador de PII (§6), o churn de coorte de sitemap (§10.2) e a via de
> retirada de página publicada (§10.2 item 10).

## Sumário — o que a investigação achou e o que muda

Investigação com **26 agentes** em 3 ondas + crítica adversarial Fable + crítica Opus 5 + advisor,
tudo verificado por medição própria no disco e no log cru. Seis conclusões governam o plano:

1. **O conteúdo é bom e não é o problema.** H2 por página de 5 a 14, mediana de 697 palavras, malha
   com profundidade máxima 3 e **1 órfã** em 9.929, zero rastro de doorway. (§1.3)
2. **Os bots não são bloqueados — eles leem e param.** O GPTBot fez 224 requisições em 12/08,
   cobriu 51,6 % do acervo e não voltou. O ClaudeBot está lendo o acervo **em markdown,
   ~1 página/hora, agora**. E o **Googlebot desistiu no meio da varredura**: parou de descobrir em
   12/08 com **72 %** de cobertura, deixando **2.778 URLs que nunca pediu**. (§1.0, §1.1-bis, §1.1-ter)
3. **Os sinais de frescor estão quebrados, e em direções opostas** — o sitemap diz "nada mudou desde
   06/08" enquanto o HTTP diz "9.711 páginas mudaram hoje". Isso é o teste exato que a doc do Google
   descreve para **parar de acreditar** no `lastmod`. Por isso existe uma **Fase 0**. (§1.2)
4. **Há um defeito ético a corrigir antes de tudo:** 9.710 páginas afirmam *"Verificado em
   20/08/2026"* e a última verificação real foi em **04/08**. (§1.2, item d)
5. **As fontes existem, são públicas e foram medidas** — Informativo STF (11.582 linhas com tese e
   resumo, licença expressa de reprodução), STJ CC-BY (4.680 documentos/dia), `normas.leg.br`
   (`Allow: /`), Querido Diário (295 diários/dia), 5 UFs com API JSON, DOU (2.956 matérias/dia). (§3)

6. **★ Os quatro defeitos de sinal têm UMA causa-raiz, e a correção é de duas linhas.** Os defaults
   `-published-at` e `-reviewed-at` são `time.Now()`; essas datas são **injetadas no HTML**, os bytes
   mudam, os 9.711 arquivos são reescritos, o ETag rotaciona e o **304 nunca acontece**. Fazer as
   datas derivarem do conteúdo em vez do relógio conserta os quatro de uma vez — e a verificação de
   segurança mostrou que **nada no sistema quebra** com isso. (§12.0)

**Três erros meus foram apanhados e corrigidos no caminho** — todos com a mesma assinatura: ler um
campo pela semântica suposta em vez da real. Um deles quase enterrou o diagnóstico (medi 7
requisições do Googlebot onde havia 269). Estão documentados como armadilha permanente, e a Fase 0
corrige a skill que induziu o primeiro. (§1, §1.1-bis, §10.2)

**O que este plano NÃO promete:** trazer o PerplexityBot (que nunca pediu uma URL) ou produzir
citação por IA — a citação depende de ranqueamento, não de acesso, e hoje é **zero**. O plano
entrega frescor verificável, sinal honesto e conteúdo diário real; a citação é consequência
possível, não garantida, e será **medida**, não afirmada.

---

## 1. Context — por que esta mudança

O `wikijuridica.com.br` tem **9.710 páginas públicas** de acervo jurídico autoral no ar. É um acervo
bom e **parado**. A consequência disso não é opinião — está medida:

**Baseline — e a armadilha de leitura que quase enterrou o diagnóstico.**

> **Erro cometido e corrigido nesta sessão, registrado para não se repetir.** Existem **dois**
> ledgers de tráfego de bot, com semânticas **opostas**:
> - **borda** (`edge_bot_agents_daily.jsonl`) é **cumulativo** → dedup por `(date, agent_key)`
>   mantendo a última linha. Somar multiplica a contagem.
> - **origem** (`origin_bot_traffic_daily.jsonl`) é **incremental** (`summable: true`, uma linha por
>   janela de cursor de ~30 min — medido: **35 linhas/dia** só de googlebot) → **soma**.
>
> Aplicar o método da borda ao ledger da origem produziu "Googlebot = 7 requisições em 7 dias".
> O número correto é **269**. A causa-raiz é um artefato do próprio repo:
> **`.claude/skills/medir-bots/SKILL.md:7-16` manda "nunca somando linhas"** — regra certa para a
> borda e **errada para a origem**, sem distinguir as duas. **Corrigir essa skill é item da Fase 0.**

**A tabela correta é a da BORDA** — 13–19/08, `edge_bot_agents_daily.jsonl`, dedup por
`(date, agent_key)`, somando os dias:

| crawler | **borda** (contagem) | origem (piso) | cobertura do acervo |
|---|---|---|---|
| **googlebot** | **673** | 269 | 73,1 % |
| **claudebot** | **393** | 46 | 23,4 % |
| **gptbot** | **348** | 2 | 51,6 % |
| **bingbot** | **305** | 37 | 0,8 % |
| **oai-searchbot** | **268** | 101 | 4,2 % |
| chatgpt-user | 126 | 59 | — |
| **perplexitybot** | **0** | 4 | **0 %** |

> **Segunda correção de método nesta sessão, apanhada pela crítica adversarial Opus 5.** O plano
> declara em §10.1 que *"contagem → borda"*, e eu havia construído esta tabela **pela origem** —
> que só enxerga o que o cache **não** absorveu (`s-maxage=604800`). A origem é **amostrador
> enviesado, não contador**. O erro seria fatal para o diagnóstico: eu afirmava
> *"GPTBot: 2 requisições, veio e parou"* quando a borda registra **348** — uma diferença de
> **174×**. A origem permanece útil para **autenticidade** (verificação por IP/rDNS), nunca para
> volume.

**O que este dado diz, sem retórica:**

1. **Todos os bots relevantes estão vindo** — inclusive os de IA, em volume duas ordens de grandeza
   maior do que a origem sugeria. Não há bloqueio, não há invisibilidade de acesso.
2. **PerplexityBot é a única ausência real**: 0 na borda **e** 0 % de cobertura. Ele nunca engajou.
3. **Bingbot e OAI-SearchBot vêm mas quase não cobrem** (305 e 268 requisições para **0,8 %** e
   **4,2 %** do acervo) — pedem repetidamente as mesmas poucas URLs.
4. **Citação por IA: ZERO.** Nenhuma linha de `clique_de_volta` em 84 de
   `ai_citation_signal_daily.jsonl`; nenhum referer de assistente no `access.log`. **Continua sendo
   o fato mais duro, e nenhum achado o explica.**
5. **As "forjadas" da origem não são bots de IA mentindo** — são **um scanner de credenciais**
   vindo de dois IPs do Google Cloud (`35.204.225.70`, `34.53.233.72`) com 7 UAs diferentes,
   651 respostas **404**, pedindo `/.env`, `/.claude/settings.json`, `/.codex/config.toml` e SSRF a
   metadata GCP. Dano medido: **1,69 MB em 7 dias**; nada vazou.

   **Os três totais que estavam incompatíveis, agora reconciliados** (a crítica apanhou a
   inconsistência):

   | número | de onde vem | vale para |
   |---|---|---|
   | **572** forjadas | ledger de origem **somado**, 13–19/08 | é o número canônico do período |
   | **667** / 662 por IP | contagem no **log cru**, janela ligeiramente maior | atribuição ao scanner |
   | 511 | soma de uma coluna parcial | **descartado** — não reproduz |

6. **Um número que faltava e muda a leitura: 9.391 requisições NÃO-VERIFICÁVEIS** no mesmo período —
   contra 1.243 autênticas e 572 forjadas. **A maioria absoluta do tráfego de bot não é
   classificável** por faixa de IP nem rDNS. Isso reforça o item 0.9 (cobrir os 22 agentes sem
   verificação) e é mais uma razão para a contagem vir da **borda**, onde a Cloudflare faz a
   verificação que a origem não consegue.
6. **Risco de falso positivo na classificação:** 3 requisições reais de ChatGPT-User foram gravadas
   como autênticas, mas a OpenAI **retirou 40 prefixos** (244→204) — reprocessar hoje transformaria
   **tráfego real de citação em "fraude"**. Precisão medida: **99,25 %**; o problema é
   **reprodutibilidade**, não acurácia.

### 1.0 ★ O DEFEITO MAIOR, e ele não é frescor: o rastreio do Googlebot despencou 98,9 %

Achado pela crítica adversarial e **confirmado por mim** na borda:

| data | requisições do Googlebot |
|---|---|
| 06/08 | 25 |
| 07/08 | 102 |
| 08/08 | 2.190 |
| 09/08 | 1.047 |
| **10/08** | **4.297** ← pico |
| 11/08 | 1.038 |
| **12/08** | **49** ← **queda de 98,9 %** |
| 13–20/08 | 31–99/dia, **plano** |

**VEREDITO — decidido por medição, não por hipótese.** O discriminador não é a contagem de
requisições, é a **curva de cobertura** (`crawl_coverage_daily.jsonl`,
`cumulative_sitemap_coverage`):

| data | cobertura | **delta** | pedidos/dia |
|---|---|---|---|
| 08/08 | 2.004 | **+1.922** | 1.962 |
| 09/08 | 2.730 | +726 | 897 |
| **10/08** | 6.714 | **+3.984** | 4.178 |
| 11/08 | 7.148 | +434 | 977 |
| **12/08** | **7.148** | **+0** | 40 |
| 13–15/08 | 7.148 | **+0** | 29–51 |
| 19/08 | 7.256 | +1 | 57 |

**Não é H2 (regressão):** a descoberta **desacelerou antes de parar** (+3.984 → +434 → 0). Queda por
bloqueio ou defeito seria abrupta na cobertura, não em rampa descendente.

**Também não é H1 puro (varredura concluída):** ele estacionou em **7.148 de 9.926 = 72 %**,
deixando **2.778 URLs que nunca pediu**. E desde 12/08 faz 30–50 requisições/dia com delta de
descoberta **zero** — está **re-pedindo o que já conhece**.

**Veredito: o Googlebot desistiu no meio da varredura.** Não foi bloqueado e não terminou. Isso é
uma tese **mais dura** que a original do plano, e desdobra o problema em dois:

1. **Frescor** — sem conteúdo novo, ele não tem razão para retomar (é o que o plano entrega);
2. **2.778 URLs órfãs de descoberta** — um quarto do acervo nunca entrou em nenhum índice, e
   conteúdo novo **não resolve isso sozinho**. Entra como frente própria: malha de links internos
   apontando para o não-descoberto, e priorização dessas URLs no sitemap e no IndexNow.

**Consequência para a ordem de execução:** o item `0.0-P0` deixa de ser "investigar" (está
investigado) e vira **"priorizar as 2.778 URLs nunca visitadas na malha interna e nos canais de
descoberta"**, executado junto da Fase 0.

### 1.1-bis O que os bots de IA recebem — investigado até o log cru

Um alarme intermediário desta sessão dizia que **GPTBot levava 90 % de 404 e PerplexityBot 93 %**
(campo `status` do ledger de origem). **Falso alarme, e a causa foi mais uma armadilha de leitura:**
o campo `status` agrega a janela inteira **sem segregar por autenticidade**. Verificado no log cru
do nginx:

```
404 → 100% de exatamente 2 IPs:  35.204.225.70 (83) e 34.53.233.72 (69)   ← o scanner
200 → outros IPs: 74.7.227.34 (222), 216.73.216.x, 127.0.0.1
```

**Os bots de IA autênticos não recebem 404 nenhum.** E o que eles recebem prova a tese do plano:

```
74.7.227.34 — "…compatible; GPTBot/1.4; +https://openai.com/gptbot"
12/Aug/2026:21:03:20  GET /sitemaps/pages-0004.xml  200
12/Aug/2026:21:03:23  GET /sitemaps/pages-0025.xml  200
…  /transito/prescricao-multa-antiga/, /transito/multa-farol-apagado-rodovia-dia/ …  200
```

**O GPTBot real fez 224 requisições no log de origem em 12/08** (222 às 21h, mais uma às 16h e uma
às 22h), com **226 respostas 200 e uma 405** — a 405 é o `/mcp` em GET, comportamento correto.
Cobriu 51,6 % do acervo e **não voltou**. Não houve bloqueio, erro, robots restritivo nem lentidão.

> **Sempre declarar a camada do número — três medições desta sessão divergiram por isso.** O log de
> **origem** registra 1 requisição do ClaudeBot em 13/08; o `paths_requested_that_day` da **borda**
> registra 218 no mesmo dia. Nenhum está errado: a origem só vê o que o cache não absorveu.
> **Regra:** todo número neste plano diz de qual camada veio — borda (contagem, cobertura) ou origem
> (autenticidade, status servido). Comparar os dois sem dizer qual é qual foi a origem dos meus três
> erros.

**Diagnóstico consolidado:** o portal é acessível, o conteúdo é bom (§1.3), o Google já rastreia
73 % dele e está em rampa. O que falta é exatamente o que este plano entrega:
1. **motivo para voltar** — conteúdo novo diário, com sinal de frescor **verificável** (§1.2 e Fase 0);
2. **razão para os crawlers de IA revisitarem** — hoje eles amostram uma vez e congelam;
3. **qualquer sinal de citação** — hoje **zero**, e é o único fato que nenhum achado explica.

> **Terceira armadilha de leitura da sessão** (as outras duas em §1 e §1.2). Todas com a mesma
> assinatura: **ler um campo pela semântica que se supõe, não pela que ele tem.** Por isso §10
> exige verificação no dado cru antes de qualquer conclusão, e por isso a Fase 0 corrige a skill
> que induziu a primeira.

### 1.1-ter Padrão de desistência de cada bot — e o gatilho já montado

Reconstruído do log cru, excluindo os IPs do scanner. **Cada bot desiste de um jeito diferente, e a
contramedida é diferente para cada um:**

| bot | padrão medido | leitura | o que o traz de volta |
|---|---|---|---|
| **GPTBot** | **224 requisições concentradas em 12/08** (222 numa única hora), depois **nada** na origem | rajada de indexação: "li, terminei" — cobertura congelada em 51,6 % | URL nova no sitemap + IndexNow; ele volta para **acervo novo**, não para o mesmo |
| **ClaudeBot** | **evoluiu**: polling de `/sitemap.xml` a cada ~2 h (16/08, 28×) → **leitura de `/index.md`, ~1 página/hora, ativo hoje** | **não desistiu — está consumindo o acervo em markdown** | conteúdo novo **com gêmea markdown**; ele já vem buscar |
| **OAI-SearchBot** | declínio: 18 (12/08) → 26 (17/08) → 9 (18/08) → 0; e **32 pedidos da MESMA página** | busca **sob demanda**, não varredura | cobertura temática: existir a página que alguém perguntou |
| **PerplexityBot** | **2 requisições em 17/08 12h. Só.** | nunca engajou | precisa de descoberta externa (§3.4), não de frescor |
| Googlebot | 269 req, em rampa, 0 % de erro | saudável | frescor verificável (Fase 0) |

**Três consequências diretas para a arquitetura:**

1. **O sitemap é o canal de gatilho do ClaudeBot** — ele o consulta 12×/dia. Um `lastmod` verdadeiro
   e uma URL nova ali valem mais que qualquer outra sinalização para esse bot. Isso torna a Fase 0
   (`lastmod` verificável) **pré-condição de eficácia**, não burocracia.
2. **O markdown não é aposta — é o canal em uso AGORA.** Hoje, 20/08, o ClaudeBot pediu
   **exclusivamente `/index.md`**, uma página por hora, todas 200:

   ```
   03:48  /sucessoes/holding-imovel-rural-georreferenciamento/index.md
   04:00  /tributario/aduana-drawback-isencao-reposicao-estoque/index.md
   05:03  /sucessoes/inventario-extrajudicial-imovel-rural/index.md
   06:07  /sucessoes/inventarios-sucessivos-extrajudicial/index.md
   07:24  /sucessoes/inventario-extrajudicial-so-bens-financeiros/index.md
   ```

   A ~1 página/hora (≈24/dia), varrer 9.710 páginas levaria 404 dias — mais um argumento para que o
   **conteúdo novo entre no topo do canal**, e não no fim de uma fila de 400 dias. **Regra:
   toda página nova nasce com gêmea markdown, sem exceção.** Ele também tocou `/mcp` (405, correto —
   POST-only).
3. **OAI-SearchBot revela demanda real**: 32 pedidos de `/previdenciario/maternidade-homem/` são
   alguém perguntando isso a um assistente. **Esse padrão vira instrumento**: página pedida
   repetidamente por bot de busca de IA entra na fila de aprofundamento editorial — é demanda
   medida, não suposta.

**Portanto o problema é maior do que "falta frescor": o portal é hoje praticamente invisível para
crawler.** O plano ataca as duas metades — **descoberta** (o bot precisa ter motivo e caminho para
vir) e **frescor** (ter motivo para voltar).

### 1.1-quater O que foi descartado por medição (não é a causa)

| hipótese | teste | resultado |
|---|---|---|
| robots.txt afasta bots | leitura do robots servido | **permissivo** — `Allow: /` + `Content-Signal: ai-train=yes, search=yes, ai-input=yes` para Googlebot, Bingbot, OAI-SearchBot, Applebot |
| rate limit sufoca crawler | `content/crawl_policy.json` | bots valiosos em tier **`unlimited`** |
| Cloudflare bloqueia bot | simulação **marcada** (`X-Bot-Simulation`) com UA de Googlebot, GPTBot, ClaudeBot, OAI-SearchBot, PerplexityBot | **200 e 25.037 bytes para todos**, idêntico ao humano |
| `lastmod` inflado destruiu confiança | parse dos 32 shards servidos | **não inflado** — mas 9.582 de 9.926 URLs (**96,5 %**) declaram `lastmod` de **06/08**: 14 dias parado |
| chave IndexNow inválida | `public/<hash>.txt` | **válida** — 200, 40 bytes, conteúdo = chave; Yandex respondeu **202** `{"success":true}` e `api.indexnow.org` **200** |
| propriedade do Search Console não verificada | `dig TXT wikijuridica.com.br` | **já verificada**: `google-site-verification=Aguiea5gh9phvp62la7sSNdWnAtKtcIqUhr-HoDauRo` no DNS |
| Google Indexing API resolveria | doc oficial (2026-07-16) | **inutilizável**: só aceita `JobPosting` e `BroadcastEvent` em `VideoObject`. Conteúdo jurídico não se enquadra — independe de credencial |

> **Nota sobre IndexNow:** a doc oficial diz que *"o código 200 indica apenas que o buscador recebeu
> sua URL"*. O 200 dos ledgers do repo **não é prova de rastreio** — por isso a métrica de sucesso é
> cobertura, não confirmação de submissão.

### 1.2 A descoberta que reordena o plano: os sinais estão quebrados **antes** do conteúdo

A investigação de descoberta achou a causa provável da invisibilidade, e ela **não é falta de
conteúdo novo**. São quatro defeitos de sinal, todos medidos, todos de engenharia local:

**(a) O sitemap e o HTTP se contradizem — e a doc do Google diz o que acontece nesse caso.**

```
sitemap:  9.582 de 9.926 URLs com <lastmod>2026-08-06</lastmod>   → "nada mudou há 14 dias"
HTTP:     find public -name index.html -newermt '2026-08-20' → 9.711 de 9.929
          Last-Modified: Thu, 20 Aug 2026 10:09:44 GMT          → "tudo mudou hoje"
```

`developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap` (2026-07-08): o Google
usa `lastmod` *"if it's consistently and **verifiably** accurate (for example by comparing to the
last modification of the page)"*; e o blog de jun/2023: *"eventually Google won't believe you
anymore"*.

> **REFINAMENTO medido depois (2026-08-20), e ele corrige este item.** Comparando o registro
> canônico (`data/ops/page_content_revision.jsonl`, 9.720 rotas) com o sitemap servido:
> **1 divergência em 9.717** (`/fontes/`), e as 209 rotas sem registro são hubs de área e
> paginação, que nascem derivados. **O `lastmod` NÃO está mentindo** — os 96,5 % em 06/08 são a
> verdade de um acervo que de fato não mudou desde então, e `tools/generate-page-content-revision`
> já faz a coisa certa (hash do conteúdo ignorando datas, data só anda quando o conteúdo anda).
>
> A contradição, portanto, é de **um lado só**: o sitemap diz a verdade e o **HTTP mente**, porque o
> mtime rotaciona a cada republicação. A correção-mãe (§12.0) ataca exatamente esse lado. O gate
> 0.3 permanece como **preventivo** — impede que o registro e o sitemap se separem no futuro —,
> não como corretivo de um defeito presente.

**(b) O churn de bytes destrói o cache condicional.** O acervo inteiro é reescrito a cada
republicação (**3 republicações só hoje**, com `data/ops/publish-rollback-20260820-*` às 02:29,
09:00 e 10:09), embora `content_revised_at` continue 06/08 para 9.585 páginas — **o único delta é a
data**. Como o ETag do nginx deriva de mtime+size, ele rotaciona em massa e **o Googlebot nunca
recebe 304**: paga 25 KB de corpo em toda revisita. O mecanismo condicional está íntegro (medido:
`If-None-Match` → **304**), mas é invalidado pelo build. O post oficial de dez/2024 sobre caching
pede exatamente o contrário.

> **Ressalva importante, apurada depois:** o publicador **já é content-addressed** —
> `grava` (`cmd/publish-v2-direct/main.go:2007`) faz `if bytes.Equal(atual, novo) { return false }`
> e só toca o disco quando os bytes mudam. Os 9.711 arquivos foram reescritos porque os bytes
> **mudaram de verdade**: a data do relógio é injetada no HTML. Logo a correção não é implementar
> escrita content-addressed (ela existe) — é **parar de mudar os bytes sem mudança de conteúdo**.
> Ver §12.0.

**(c) Três superfícies da mesma URL discordam** (verificado por mim em
`/familia/divorcio-conjuge-mora-exterior/`):

| superfície | valor |
|---|---|
| texto visível | "Atualizado em 20 de agosto de 2026" |
| JSON-LD | `datePublished: 2026-08-20` **e** `dateModified: 2026-08-06` |
| sitemap | `<lastmod>2026-08-06</lastmod>` |

`dateModified` **14 dias antes** de `datePublished` é impossível. A doc de *Article dates*
(2025-12-10) exige que os valores visível e estruturado coincidam.

**(d) DEFEITO ANTI-FRAUDE — P0, verificado por mim.** O HTML publicado imprime ao visitante
**"Verificado em 20/08/2026 · Fonte oficial usada…"** e o manifesto carrega **23.759** campos
`checked_at: 2026-08-20`. Mas os ledgers que gravam verificação HTTP real param antes:

```
v2_official_source_verify_url_cache.jsonl   402 linhas · max checked_at = 2026-08-04T18:12:36Z
v2_official_source_stamp_ledger.jsonl       400 linhas · max ts         = 2026-08-04T18:49:27Z
v2_source_provenance.jsonl               20.482 linhas · max verified_at= 2026-08-12
```

**9.710 páginas jurídicas afirmam verificação que não ocorreu**, violando a regra do próprio
contrato ("nenhum campo de evidência é escrito como verdadeiro sem a ação correspondente ter sido
executada"). É defeito ético antes de ser defeito de SEO — e num portal assinado por advogado,
não pode ficar no ar.

**Causa-raiz isolada no código** (não é suposição — é a cadeia lida):

```
cmd/publish-v2-direct/main.go:2621   CheckedAt: opts.reviewedAt
cmd/publish-v2-direct/main.go:156    opts.reviewedAt ← flag "-reviewed-at", default defaultRevisionDate()
cmd/publish-v2-direct/main.go:131    defaultRevisionDate() → time.Now().UTC().Format("2006-01-02")
grep ledger de verificação em publish-v2-direct → ZERO ocorrências
```

**`checked_at` é `time.Now()` renomeado.** Ele nunca leu
`v2_official_source_verify_url_cache.jsonl`, nunca tocou uma URL oficial. E há uma ironia
instrutiva: o comentário de `main.go:124-130` explica que o default virou `time.Now()` para que
*"só o SILÊNCIO deixe de mentir"* sobre a data de **revisão** — e é esse mesmo valor que é copiado
para `checked_at`, onde passou a mentir sobre **verificação de fonte**. A correção de um campo
plantou o defeito no outro.

**Portanto a correção não é criar um gate — é cortar a cópia:**
1. `checked_at` passa a vir **exclusivamente** do ledger de verificação real, por URL de fonte;
2. onde não houver linha no ledger, o campo **não é emitido** e o HTML **não imprime "Verificado
   em"** — silêncio honesto em vez de afirmação falsa;
3. o gate `check-source-verification-evidence` entra como **defesa secundária** contra regressão,
   não como a correção;
4. um coletor de re-verificação (que é `internal/sourcecollect`, §4.1) passa a alimentar o ledger
   de verdade — aí o carimbo volta a ser legítimo.

**Verificação de segurança da correção — feita antes de propor, porque ela toca produção:**

| risco | verificação | resultado |
|---|---|---|
| campo vazio derruba o servidor no boot | `publishedmanifest.Validate` — lista dos 12 obrigatórios (`publishedmanifest.go:907-922`) | **`checked_at` NÃO está na lista** ✅ |
| render imprime "Verificado em " vazio | `internal/render/render.go:1705` | `if checked != ""` — **omite** ✅ |
| transação reprova campo vazio | `internal/publicrelease/publicrelease.go:6470` | `if source.CheckedAt != "" && !isISODate(...)` — **vazio passa** ✅ |

E o `provenanceMeta` já foi desenhado com a regra certa desde que nasceu — o comentário dele diz
literalmente: *"Campo ausente não vira frase vazia nem separador órfão."*

**Conclusão: a correção do defeito mais grave do plano é de uma linha, e todo o resto do sistema já
se comporta corretamente sem ela.** Risco de regressão: baixo, e verificável por teste antes do
commit.

**(e) Bug que bloqueia a métrica de sucesso.** `approved_at` é reescrito a cada republicação
(`internal/publicrelease/publicrelease.go:496`) e o acervo **nunca** tem mais de uma data distinta:
100 % `2026-08-06` em 06/08, 100 % `2026-08-13` em 19/08, 100 % `2026-08-20` hoje. **Não existe a
data de primeira publicação de cada página** — sem ela, `time-to-first-crawl` (§10.1) é incalculável.

### 1.3 O conteúdo NÃO é o problema (medido, e é uma boa notícia)

A auditoria adversarial do acervo procurou molde e não achou:

- **H2 por página: 5 a 14** (mediana 8) em 1.500 páginas; o H2 **de conteúdo** mais repetido aparece
  **5×/1.500**. Os únicos repetidos são estruturais (Proveniência, Relacionados, FAQ).
- **Corpo: mediana 697 palavras** (mín. 388). Frase de 8 palavras mais repetida: **6/1.200**.
- **Malha saudável**: outbound mediana 10, inbound mediana 6, **1 órfã** em 9.929, profundidade
  máxima **3** cliques a partir da home. Isso **não** é gargalo de rastreio.
- **Sem rastro de doorway v1** no ar (`authorial_mass_content_expansion.jsonl` = 0 linhas).
- Prosa real, específica e com análise jurídica — não enchimento.

**Conclusão que reordena o plano:** o acervo é bom e está mal sinalizado. Publicar conteúdo diário
sobre uma base que emite sinais contraditórios e não-verificáveis **amplifica o defeito em vez de
resolver**. Por isso nasce a **Fase 0** (§12): consertar os sinais antes de amplificá-los.

**Objetivo:** transformar o portal de acervo em **fonte viva** — conteúdo jurídico novo todo dia,
derivado de fonte pública oficial, com sinalização ativa de frescor. A métrica de sucesso é a
própria tabela acima, medida de novo em D+30.

### O que já foi medido neste servidor (2026-08-20)

| Fato | Evidência | Consequência |
|---|---|---|
| `/noticias` e `/jurisprudencia` → **404** | `curl` na origem `:8088` | rotas livres |
| `/sumulas/` → **200**, já tem **217 páginas** (`/sumulas/stf-117/`) | `curl` + `ls public/sumulas` | **não é seção nova** — é acervo a atualizar |
| `/feed.xml`: 1.000 entradas, 534 KB, **6 valores distintos de `<updated>`** (866 na mesma data) | parse do XML servido | **não é sinal falso** — o `updated` vem de `LastModified()` e é verídico; é o retrato honesto de um acervo parado. O defeito é o **cap de 1.000** já saturado e a granularidade por dia |
| Markdown por negociação **funciona** (`Accept: text/markdown` → 200) | `curl -H` | canal de IA pronto, falta conteúdo fresco |
| `public/` tem **0** `.md` | `find` | markdown é sintetizado em runtime (`internal/pagemarkdown`) |
| Borda cacheia **7 dias** (`s-maxage=604800`); purga é **total** | `curl -I` + `edge_cache_coverage.jsonl` (`{"miss":9994,"hit":11}` após purga) | publicar diário sob purga-tudo = **borda fria diária** |
| `try_files $uri $uri/ @fallback` → Go em `:8089` | `ops/nginx/standalone/nginx.conf:964` | **rota nova não exige uma linha de nginx** |
| `publicpath.Split` exige 2 segmentos **só para a página de massa autoral** | `publicpath.go:52` + medição: `/sumulas/pagina/2/` → **200**, e **180** `index.html` em 3 níveis | 3 segmentos **são possíveis**; slug plano é **escolha** (menos código, padrão vivo), não imposição |
| Purga de borda **seletiva existe** | `tools/purge-edge-cache --tag/--url`; servido `Cache-Tag: wj-acervo,area-sumulas` | publicar diário **não** exige esfriar a borda inteira |
| `LegalPageTypes` já declara `noticia-juridica`, `jurisprudencia`, `legislacao`, `precedente` | `internal/content/content.go:22` | vocabulário existe, **uso é zero** |
| `v2CanonicalPageTypes` mapeia só 4 tipos | `content.go:199` | **ponte a criar** |
| `internal/sourcefetch` é **metadata-only por contrato** (`ResponseBodyRead: false`) | `sourcefetch.go:329` | coletor de corpo **precisa nascer** |
| 13 timers `wikijuridica-*` ativos, **todos** de telemetria | `systemctl list-timers` | **nenhum produz conteúdo** |
| `--limit N` publica os N **primeiros alfabéticos** | `cmd/publish-v2-direct/main.go:265` | falta **modo incremental** |
| IndexNow (200), WebSub (204), purga de borda **funcionam** | ledgers `data/ops/*.jsonl` | cadeia de notificação existe |
| 347 checks registrados | `internal/checks/checks.go` | onde os gates novos entram |

---

## 2. Emenda de contrato — resolver ANTES de qualquer código

`CLAUDE.md:173` diz hoje: *"Fonte oficial é referência/proveniência, **nunca corpo**: proibido
scraping de conteúdo, cópia, espelho, paráfrase mecânica."* Executar este plano sem emendar faria
todo o trabalho reprovar no primeiro gate.

**DEC-032 (2026-08-20) — Conteúdo derivado de fonte oficial.**

- **Base legal:** Lei 9.610/98, **art. 8º, incisos I e IV** — não são objeto de proteção autoral os
  textos de lei, decisões judiciais e demais atos oficiais. Reproduzir uma súmula ou o dispositivo
  de um acórdão **não é violação**; é uso de domínio público.
- **Libera:** reproduzir texto oficial **identificado como citação**, com URL, data e hash.
- **NÃO afrouxa** (permanece integralmente proibido): inventar decisão/ementa/artigo/data;
  publicar texto oficial **sozinho**, sem valor autoral (espelho + thin content); copiar de portal
  **privado** (Jusbrasil, Conjur, Migalhas — esses têm direito autoral); ética OAB; anti-fraude de
  métrica; coerência de artefato.
- **Regra editorial substituta — "duas camadas":** toda página derivada tem, visualmente distintos,
  o **texto oficial citado** (bloco com fonte e data) e o **comentário autoral** (contexto, alcance,
  efeitos, limites). Piso medido de comentário próprio, verificado por gate novo (§6).

**Política de coleta (decisão do dono, 2026-08-20):** *"É só usar como humano, isso não é fraude, é
eu mesmo que to usando e me identificando."* Fica fixado:

1. **Identificação sempre** — o User-Agent carrega `+wikijuridica.com.br` (padrão já vigente em
   `tools/generate-legal-corpus:25`), de modo que o operador do site saiba quem acessou.
2. **Ritmo humano** — no máximo **1 requisição / 2 s por host** e teto diário por fonte (§4), com
   ledger de cada requisição.
3. **Preferência por canal aberto** — quando existir canal permitido por `robots.txt` ou API de
   dados abertos, ele é obrigatório; o acesso ao portal público é a **segunda** opção.
4. **Nunca espelho em massa** — a página publicada é comentário com citação, jamais réplica do
   documento oficial.
5. **Registro honesto de risco:** o termo de uso do `in.gov.br` veda scrapers e uso comercial, e o
   `robots.txt` é `Disallow: /`. Isso fica documentado em `docs/data-sources/` com o veredito do
   dono, não escondido.

**Crítica adversarial recebida e como o plano responde.** O crítico Fable sustentou que adotar UA
com prefixo `Mozilla/5.0` para vencer WAF é *racionalização*, porque contradiz
`cmd/enumerate-federal-norms/fetch.go:11` ("Nunca se passa por navegador"), e que institucionalizar
isso num pipeline **diário** multiplica a exposição. A crítica é procedente e o plano a incorpora
assim — sem descumprir a decisão do dono:

- **Regra dos três degraus, obrigatória e nessa ordem.** (1) canal aberto e permitido por robots
  (F2, F3, F4, F6, F7, F8) — cobre a **maioria** e as melhores fontes, e **não usa UA de navegador**;
  (2) canal público cujo operador exige cabeçalhos de navegador, com identificação embutida
  (`+wikijuridica.com.br`) e ritmo humano — hoje **apenas STF (F1, F5) e DOU (F9)**;
  (3) nunca, para host que negue o acesso por outro meio que não o WAF.
- **A contradição interna é resolvida por escrito**, não ignorada: `fetch.go:11` passa a
  referenciar a política única, e a exceção fica nominal (lista fechada de hosts), auditável por
  `check-collect-politeness`.
- **Mitigação que reduz a exposição real:** para o STF há **licença expressa de reprodução**
  publicada pelo próprio tribunal; e a página publicada é comentário com citação, jamais espelho.

**Execução:** DEC-032 em `docs/goal/DECISIONS.md` + edição cirúrgica de `CLAUDE.md:173` e
`docs/CONTENT_QUALITY.md:69`, ambas citando a base legal e o precedente.

---

## 3. Fontes — matriz de decisão medida

### 3.0 A base legal NÃO é uniforme — cada fonte tem a sua

A crítica adversarial derrubou a apresentação anterior, que invocava o art. 8º da Lei 9.610/98 para
tudo. Correto é **por fonte**:

| fonte | base legal correta | por quê |
|---|---|---|
| Decisão judicial, ementa, súmula | **Lei 9.610/98, art. 8º, IV** | são atos oficiais — sem proteção autoral |
| Texto de lei, decreto, IN | **art. 8º, I e IV** | idem |
| **Informativo do STF (F1)** | **a licença expressa do próprio STF**, com URL e data de consulta: *"Permite-se a reprodução desta publicação, no todo ou em parte, sem alteração do conteúdo, desde que citada a fonte"* (`portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF`, consultado 2026-08-20) | **"Tese" e "Resumo" são texto editorial** redigido pela Secretaria de Documentação — **não** é obviamente ato oficial. O art. 8º sozinho **não cobre F1** |
| Notícia institucional de tribunal | **não coberta** — só o **fato** é livre | a redação é protegida (art. 7º) |
| Portal privado (Jusbrasil, Migalhas, ConJur, JOTA) | **proibido reproduzir** | protegido; termos vedam expressamente |

**Regra:** a proveniência de cada página registra **qual** base legal a autoriza — nunca um art. 8º
genérico. Onde a base for licença, ela entra com URL e data.

### 3.0-bis Risco contratual do DOU — nomeado, não escondido

O `in.gov.br` tem `robots.txt` = `Disallow: /` **e** termo de uso que veda scraper e finalidade
comercial. A natureza do risco **não é direito autoral** (os atos são públicos) — é
**inadimplemento de termo de uso**, praticado por um advogado inscrito na OAB, num portal que tem
CTA de contratação. O art. 8º não toca essa categoria.

A decisão do dono (2026-08-20) autoriza o acesso como uso próprio identificado. A crítica levantou
um ponto legítimo: **um pipeline diário, automatizado e não supervisionado não é "uso humano"**.
Portanto, para F9 (DOU), o plano fixa:

- o DOU **não entra na Fase 2**; fica na Fase 3, depois de F1–F4 provarem o pipeline;
- quando entrar, é com **volume baixo, ritmo humano e seleção estrita** (só `artType` de alto valor
  jurídico), nunca varredura das 2.956 matérias diárias;
- o registro do risco fica em `docs/data-sources/`, com o veredito do dono, por escrito.

Legenda de robots medida por mim hoje. **Volume medido**, não estimado.

| # | Fonte | Canal medido | robots | Volume/dia medido | Veredito |
|---|---|---|---|---|---|
| F1 | **Informativo STF** — XLSX `Dados_InformativosSTF.xlsx` | 9,3 MB, **11.582 linhas × 24 col.** (Título, **Tese**, **Resumo**, Ramo do Direito, Matéria, Legislação); `Last-Modified` + `ETag` reais | UA de navegador exigido | **~9 itens/semana** (1,2/dia útil) | 🟢 **prioridade 1** — ver base legal em §3.0 |
| F2 | **STJ — dados abertos CKAN** | `temas.csv` 2.391 linhas (1.182 com `teseFirmada`); DJe `metadadosAAAAMMDD.json` + `textos*.zip` | `Crawl-Delay: 10`; `/api/` vedado | **4.680 documentos/dia** no DJe | 🟢 **prioridade 1** — **CC-BY** |
| F3 | ~~STJ — feeds Atom~~ | 346 KB / 88 KB / 18 KB | **`Disallow: /`** | — | 🔴 **FECHADO — ver §3.3** |
| F4 | **normas.leg.br** (LexML/Senado) | JSON-LD schema.org/`Legislation`, ~0,25 s; cliente **já existe** no repo | **`Allow: /`** | ~1,3–2,25 normas/dia | 🟢 **prioridade 1** — **CC-BY 4.0** |
| F5 | **Súmulas STF** `sumariosumulas.asp` | **736 súmulas + 63 vinculantes**, HTML por súmula | `Disallow: /processos` apenas | acervo + novas | 🟢 |
| F6 | **Diários estaduais — 5 UFs com API JSON** (AM, ES, GO, MT, PR) | `GET {host}/apifront/portal/edicoes/edicoes_from_data/AAAA-MM-DD` + PDF | **sem robots** (404) | **~7 edições / ~500 páginas** por dia útil | 🟢 |
| F7 | **Querido Diário** (`api.queridodiario.ok.org.br`) | API JSON + **texto já extraído**; código **MIT** | uso previsto | **295 diários/dia**, 228 municípios, 17 UFs | 🟢 |
| F8 | **Sigpub** (`diariomunicipal.com.br`) | 36 portais de associações estaduais | **`Disallow:` vazio = livre** | medir na Fase 3 desta sessão | 🟢 |
| F9 | **DOU** (`www.in.gov.br/leiturajornal`) | JSON embutido `<script id="params">`; íntegra em `/web/dou/-/{slug}` | **`Disallow: /`** + termo veda scraper | **2.956 matérias/dia** (DO1 346 · DO2 689 · DO3 1.921) | 🟡 ritmo humano, seleção estrita |
| F10 | **DataJud CNJ** | 91 aliases, **352.539.344 docs** | — | lag **6–41 dias**, carga em lote | 🔴 **ver §3.1** |
| F11 | TST (backend REST aberto) · TRFs · notícias oficiais | medido nos dossiês | — | TST via `jurisprudencia-backend2` sem auth | 🟢 Fase 3 desta sessão |

**Vetado por ordem do dono:** INLABS (exige cadastro) — *"não me mande fazer nada de autenticação"*.

### 3.1 DataJud — por que sai da rota principal (decisão com dado)

A API **funciona** e é ampla (91 tribunais, 352 milhões de documentos, chave pública do CNJ). Ela sai
da rota principal por três medições, não por dificuldade:

1. **Não tem texto.** O censo de campos (`_field_caps`) devolve número, classe, assuntos, órgão,
   movimentos e datas — **sem partes, sem advogados, sem ementa, sem íntegra**. É índice de
   movimentação processual, não acervo de jurisprudência: não dá para escrever conteúdo a partir dele.
2. **Termo de Uso V1.2 (27/11/2023), cláusulas 3.3 e 3.8** — uso "exclusivamente para fins **não
   comerciais**" e vedação a "explorar comercialmente a API ou qualquer informação derivada dela".
   O portal tem CTA de contratação. O fato judicial é domínio público, mas a cláusula restringe
   **este canal**, aceito tacitamente pelo uso (3.13 ainda limita a 120 req/min).
3. **Não é fresco.** Lag de 6 a 41 dias por tribunal; carga em lote (TJDFT: 148.480 docs em 10/08 e
   **zero** em 07, 08, 09).

**Substituição, não desistência:** o que o DataJud não entrega — jurisprudência **com texto e
recente** — vem de F1 (Informativo STF, com tese e resumo), F2 (STJ DJe, íntegras CC-BY) e F3
(feeds do STJ). O DataJud fica reservado para **estatística agregada** (ex.: volume de processos por
assunto e tribunal), que é uso informativo, sem exploração comercial da informação derivada — e
mesmo assim só depois de parecer próprio sobre 3.3/3.8.

### 3.2 Feeds RSS/Atom medidos — o motor do frescor diário

Todos **200, sem auth, sub-segundo**, medidos em 2026-08-20:

| feed | bytes | itens | volume/dia | natureza |
|---|---|---|---|---|
| `processo.stj.jus.br/jurisprudencia/externo/InformativoFeed` | 346.300 | **930** | — | **decisão judicial = domínio público** |
| `scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed` | 88.042 | 281 | — | idem (ISO-8859-1) |
| `scon.stj.jus.br/SCON/PesquisaProntaFeed` | 18.043 | 23 | — | idem (ISO-8859-1) |
| `res.stj.jus.br/hrestp-c-portalp/RSS.xml` | 583.766 | 118 | **4–12/dia útil** | notícia institucional |
| `www.tst.jus.br/rss` | 86.454 | 10 | **8–11/dia** | notícia institucional |
| `www.cjf.jus.br/cjf/noticias/ultimas-noticias/RSS` | 16.082 | 30 | 5–8/dia | notícia institucional |
| `portal.trf6.jus.br/feed/` | 88.845 | 10 | ~6/dia | notícia institucional |
| `agenciabrasil.ebc.com.br/rss/justica/feed.xml` | 53.009 | 10 | ~10/24 h | notícia — **ver licença** |

**Regra de licença para notícia (decisão fixada):** decisão judicial e ato oficial são domínio
público (art. 8º, IV). **Notícia institucional não é** — a redação é protegida, o **fato** não.
Portanto: notícia entra como **fato reescrito autoralmente com link para a fonte**, nunca cópia
nem paráfrase mecânica.

**Correção medida sobre a EBC:** a licença "CC BY 3.0 BR" **não se confirma** — zero ocorrências de
Creative Commons na home, `/sobre` e `/justica`; `/licenca-creative-commons` → **404**. O termo
vigente autoriza reprodução "para veículos de comunicação com fins jornalísticos, mediante indicação
da fonte" e exige contato de licenciamento para **fins comerciais**. Como o portal tem CTA,
**texto da EBC não é reproduzido** — apenas o fato.

**Hosts que negam este servidor** (medido): `jurisprudencia.stf.jus.br` e `redir.stf.jus.br` → 202
(WAF challenge); `www.tse.jus.br` → 403 até no `robots.txt` — política de crawl ilegível, **não
rastrear**; TRF1–TRF5 sem feed válido (200 com `text/html`). O STF **é** alcançável pela via de
arquivo (§F1/F5) desde que se corrija a cadeia TLS incompleta (baixar o intermediário AIA) — dois
agentes divergiram aqui e prevalece a medição mais profunda, que reproduziu o download.

**TST — achado:** `jurisprudencia.tst.jus.br/robots.txt` é `Disallow: /` e o site é SPA sem HTML
rastreável, **mas** o backend `jurisprudencia-backend2.tst.jus.br/rest/*` responde JSON **sem auth**
(`orgaos-judicantes`, `classes-processuais`, `indicadores`). Súmulas, OJs e PNs do TST saem por ali.

**Nada é descartado.** Fonte 🟡, 🔴 ou ⏳ permanece no plano com task própria de investigação.

---

## 3.9 ★ Catálogo de armadilhas por fonte — o achado mais caro da investigação

Cada linha abaixo custou tokens e foi medida por um agente. **São elas que quebram um coletor
ingênuo**, e nenhuma é dedutível da documentação. Este catálogo vai para
`docs/data-sources/FONTES_DIARIAS.md` e é leitura obrigatória de quem implementar cada coletor.

**Regra transversal que aparece em 4 fontes distintas: `status == 200` NÃO prova sucesso.**

### F1 — Informativo STF (XLSX)
- **Coluna G é serial Excel** (época 1899-12-30): `46239,125 → 2026-08-05`. Tratada como texto, vira
  `.125`/`3334` em qualquer histograma.
- `sheet1.xml` usa **`inlineStr`, sem `sharedStrings`** — parser que só lê `sharedStrings` devolve
  **vazio**, silenciosamente.
- **`.htm` da edição nova é 404**: `informativo1222.htm` = 200, `1223`/`1224` = 404. O HTML atrasa
  ~2 edições — para as recentes, citar o **PDF/DOCX**.
- Coluna N (Tese Julgado) vem **vazia** em parte das linhas — célula ausente ≠ coluna ausente.
- **Soft-404 no portal**: caminho inexistente devolve **200 com exatamente 54.429 bytes**
  (md5 `6272f469…`). Comparar tamanho/hash, nunca só o status.

### F2 — STJ dados abertos (CKAN)
- **Cada arquivo diário é um recurso NOVO com UUID novo** — a URL de amanhã é **imprevisível**. O
  coletor precisa reler o HTML do dataset todo dia, e o atalho `/api/` é **vedado por robots**.
- A página `integras-…` custa **11,4 s e 4,1 MB** — pior latência medida; quebra timeout ingênuo.
- `Crawl-Delay: 10` é piso, respeitado por limitador em processo (nunca `sleep`).
- `temas.csv` tem vírgulas e quebras **dentro** dos campos — exige parser CSV real, nunca `split(',')`.
- `situacao` tem 12 valores com **quase-homônimos distintos** (`Cancelada` 335 × `Cancelado` 197):
  agrupar por igualdade de string **inventa categoria**.
- **`textos*.zip` traz nome civil real de pessoa física** (medido) — enquanto `metadados*.json` vem
  anonimizado. É a maior exposição LGPD do conjunto.

### F4 — normas.leg.br
- **Fail-open com HTTP 200**: URN inexistente → **200** com 51 bytes; URN inválida → **200** com 25.
  Coletor ingênuo grava corpo vazio como sucesso. **Validar `legislationIdentifier` na resposta.**
- **`encoding` é dict OU array** — dict quando há uma redação, array quando há várias.
  `json.Unmarshal` em `[]` quebra em metade dos casos.
- O binário é **HTML gerado por Aspose.Words a partir de DOCX**: strip-tags ingênuo traz
  `<o:DocumentProperties>` com **nome da pessoa que editou o arquivo** — dado pessoal de terceiro,
  a descartar sempre.
- `contentUrl` vem como `/api/binario/…`; o caminho público é **`/api/public/binario/…`**.
- **Sitemap ≠ frescor**: ~1 semana de atraso medida (a Lei 15.490 de 17/08 não estava nele).
- Não existe endpoint público de **busca por data** — a URN vem por outro canal.

### F6 — Diários estaduais (AM, ES, GO, MT, PR)
- **O erro volta HTTP 200** com `{"erro":true}` — status 200 não é sucesso.
- Só aceita `YYYY-MM-DD`; `19-08-2026` e `19/08/2026` falham (com 200).
- `paginas` do JSON **não bate** com o PDF (MT declarou 24, o PDF tinha 5).
- **PR**: `www.documentos.dioe.pr.gov.br` serve certificado de outro CN → falha TLS. Host correto é
  `www.dioe.pr.gov.br`.
- **RJ**: `doweb.rj.gov.br` é **NXDOMAIN** (host de tutoriais antigos); vivo é `www.ioerj.com.br`.
- **CE e PI**: porta 443 fechada, só HTTP, charset **ISO-8859-1** → mojibake se assumir UTF-8.
- **PE**: `www.` dá handshake failure; o apex funciona.
- **AM**: recência irregular — zero edições em 18 e 19/08, mas edição em 14/08.
  **Ausência de item ≠ ausência de diário.**

### F7 — Querido Diário
- O host real da API é **`api.queridodiario.ok.org.br`**; `queridodiario.ok.org.br/api/*` devolve
  **200 com o HTML do SPA** para qualquer caminho. **Validar `content_type`, não status.**
- **A chave de frescor é `scraped_since`, não `published_since`** — o robô roda de madrugada sobre o
  dia anterior (ciclo D-1). Pedir "hoje" colhe **quase nada**.
- **`total_gazettes` satura em exatamente 10.000** (teto do Elasticsearch, não contagem).
- `aggregates.file_path` vem **sem barra**: `data.queridodiario.ok.braggregates/...`.
- `.txt` e `.pdf` vêm como `binary/octet-stream`.
- Cobertura em **queda de ~35 % em 14 meses**; **955 de 5.570 municípios** têm alguma coleta (17,1 %).

### F9 — DOU
- `robots.txt` = **`Disallow: /`** e termo veda scraper e uso comercial (§3.0-bis).
- O WAF **só aceita UA com prefixo `Mozilla/5.0`** — UA que se identifica como bot recebe conexão
  fechada (status 000), não 403.
- `content` do JSON embutido é **prévia truncada em 403 caracteres** (328 de 346 idênticas) — a
  íntegra só na página da matéria.
- Sábado, domingo e feriado: `jsonArray` **vazio** — normal, não erro.

### Concorrentes (fonte de pauta, nunca de texto)
- **Migalhas**: `…/{slug}.md` devolve **200 com `text/html`** de 221 KB — soft-200; um coletor
  ingênuo grava HTML achando que é markdown.
- **JOTA**: o corpo vive em `__NEXT_DATA__` com `<p>` escapados (`<p`) — quem extrai por `<p>`
  colhe **1 parágrafo** e conclui "página vazia".
- **news-sitemap é janela móvel** (~2 dias no JOTA, ~10 no Migalhas): perdeu o dia, perdeu a URL.
- **Jusbrasil**: `robots.txt` responde 200 e **todo o resto é 403** — falsa sensação de abertura.

## 3.10 ★ Bugs pré-existentes achados na investigação — todos entram no escopo

Ordem do dono: *"achado de subagente é trabalho pago, tem que ser resolvido; se tiver bug,
aproveitar e corrigir"*. Nenhum destes foi procurado — todos apareceram no caminho, e **todos são
corrigidos nesta sessão**:

| # | bug | arquivo:linha | gravidade |
|---|---|---|---|
| B1 | **`checked_at` é `time.Now()`** — 9.710 páginas afirmam verificação que não houve | `internal/v2publish/v2publish.go:251` | **P0 ético** |
| B2 | `approved_at`/`datePublished` reescritos a cada republicação — não existe data de primeira publicação | `internal/publicrelease/publicrelease.go:496` | **P0** |
| B3 | **Extrator de HTML quebrado**: `DefaultPythonBinary = "python3"`, e o `python3` do sistema **não tem trafilatura**; o venv só é alcançável por flag que nenhum código resolve | `internal/demandtextextractor` | **P0** (silencioso) |
| B4 | **Fetcher sem nenhuma guarda**: sem robots, sem rate limit, sem proteção SSRF, lendo 64 MB | `cmd/enumerate-federal-norms/fetch.go` | **P1 segurança** |
| B5 | **Contradição de política de UA**: um coletor usa UA de navegador para vencer WAF; outro declara *"Nunca se passa por navegador"* | `tools/generate-legal-corpus:25` × `cmd/enumerate-federal-norms/fetch.go:11` | **P1 contrato** |
| B6 | **Comentário que mente**: diz que `newAccessLoggerInDir` serve para "instância paralela", mas a função é **unexported** e ninguém de fora a alcança | `internal/httpserver/access_log.go:115-117` | P2 (R1 do contrato) |
| B7 | **Skill induz erro de leitura de 38×**: manda "nunca somar linhas" — certo para a borda, **errado para a origem** | `.claude/skills/medir-bots/SKILL.md:7-16` | **P1** (já mordeu) |
| B8 | **Nenhum leitor canônico soma a série de origem**, embora o produtor documente a regra | `tools/generate-bot-traffic-origin:70-85` sem consumidor | **P1** |
| B9 | **`feed.RenderRSS` existe, tem teste, e nada o publica** — canal morto | `internal/feed/feed.go:255` | P2 |
| B10 | **`internal/crawleridentity` é Googlebot-only** e **não é importado pelo `httpserver`** — verificação de identidade em runtime não existe | `internal/crawleridentity/identity.go:53,610` | P2 |
| B11 | **Unit "verde" com finalidade 100 % falha**: `edge-warm` fecha `exit 0`, ledger com `failures: 0`, e no mesmo registro `cache_status.miss: 10.004` | `ops/systemd/wikijuridica-edge-warm.*` | **P1** |
| B12 | **Nenhuma unit tem `OnFailure`** — falha com exit ≥2 ou crash não avisa ninguém | `ops/systemd/*.service` (zero ocorrências) | **P1** |
| B13 | **Evidência de IP não se propaga entre agentes**: 97 requisições `amzn-searchbot` dos **mesmos IPs já provados** como scanner caem em `unverifiable` em vez de `forged` | `tools/botagents.py` | P2 |
| B14 | **Faixas de IP upstream defasadas** — bingbot de **2024-01-03**; e 22 agentes sem faixa nem rDNS | `data/ops/bot_ip_ranges/*.json` | P2 |
| B15 | **Rollback sem retenção**: 67 snapshots × 98 MB = 6,2 GB, copiando `pages.json` inteiro para um delta de 15 páginas | `cmd/publish-v2-direct/main.go:2657` | P2 |
| B16 | **301 servidos a bot**: 15 de 68 requisições do Bingbot (22 %) viram redirect — orçamento de rastreio desperdiçado | rota | P2 |
| B17 | **Datas contraditórias na mesma URL**: `dateModified` (06/08) **anterior** a `datePublished` (20/08) no JSON-LD, e o sitemap discordando de ambos | `internal/structureddata` + `internal/sitemap` | **P1 SEO** |

**Regra que vale durante toda a implementação:** achado de subagente **não vira backlog**. Bug
encontrado no caminho é corrigido no mesmo ciclo, com o `arquivo:linha` e a medição registrados no
commit. Se a correção não couber no ciclo, ela vira task **com dono e prazo dentro desta sessão** —
nunca "documentado e seguimos".

## 4. Arquitetura — o que se constrói

### 4.1 `internal/sourcecollect` (NOVO — o coletor que falta)

`internal/sourcefetch` recusa corpo por contrato (`ResponseBodyRead: false`), e a capacidade está
espalhada em 5 fetchers com disciplina desigual — um deles (`cmd/enumerate-federal-norms/fetch.go`)
**sem robots, sem rate limit e sem guarda SSRF**. Nasce um coletor único:

- reusa as guardas SSRF de `sourcefetch` (`UnsafeIP`, `SafeDialContextWithOptions`, allowlist);
- **robots.txt** com cache por host (`temoto/robotstxt`, já usado em `cmd/collect-oracle`);
- **rate limit por host** (1 req/2 s) + teto diário por fonte + `Retry-After`;
- **cache HTTP condicional** (`If-None-Match` / `If-Modified-Since`) — hoje **não existe em nenhum
  coletor**, e sem ele o portal rebaixa a fonte oficial todo dia inteiro;
- decodificação de charset (ISO-8859-1 dos feeds do STJ) e cap de bytes;
- **ledger por requisição** em `data/ops/source_collect.jsonl` (URL, status, bytes, hash, UA);
- **remendo de cadeia TLS por host** (ver abaixo).

Corrige de passagem os dois bugs achados: o fetcher sem guardas e a divergência de política de UA.

**Cadeia TLS do STF — verificado por mim, não por relato.** `www.stf.jus.br` serve o certificado
**folha duas vezes** e **nenhum intermediário** (`Verify return code: 21`). Navegador não sofre
porque busca o intermediário pelo campo AIA; `curl` e clientes Go, sim. Reproduzido:

```
sem correção  → status 000 (falha de verificação)
AIA gsgccr6alphasslca2025.crt (1.425 B) + bundle do sistema
              → HTTP/2 200 · 9.311.518 bytes
                Last-Modified: Tue, 18 Aug 2026 21:51:26 GMT · ETag: "24fb6b75b2fdd1:0"
```

Sem esse remendo o coletor registraria "STF fora do ar" **todo dia** — um defeito falso. Com ele, o
GET condicional funciona de verdade: pergunta "mudou?" e recebe 304 sem baixar os 9 MB.

### 4.2 Pipeline diário — 5 estágios

```
coleta → seleção → síntese → gates → publicação+notificação
```

1. **Coleta** (`cmd/collect-daily-<fonte>`): busca o delta do dia, grava JSONL bruto datado em
   `data/research/daily/<fonte>/<AAAA-MM-DD>.jsonl` com proveniência (URL, data, hash, status).
2. **Seleção** (`cmd/select-daily-candidates`): filtra o que é juridicamente relevante. O DOU já
   entrega a classificação pronta — `artType` (Portaria 114, Decisão 62, Resolução 14, **Súmula 3**,
   Instrução Normativa, Acórdão) e `hierarchyList` (órgão). Descarta ruído (Pauta, Ata interna).
   **Janela temporal:** ver §5.
3. **Síntese** (`cmd/synthesize-daily-page`): mecanismo semântico (§5).
4. **Gates** (§6).
5. **Publicação**: reusa `cmd/publish-v2-direct` (transação com manifest ⊆ sitemap ⊆ public), em
   **modo incremental novo** (§7).

### 4.3 Rotas canônicas (decisão fixada, sem ambiguidade)

`publicpath.Split` exige **exatamente 2 segmentos** — o padrão do repo é slug plano
(`/sumulas/stf-117/`). Portanto:

| Seção | Rota | Observação |
|---|---|---|
| Notícias jurídicas | `/noticias/<slug-com-data>/` | 404 hoje, livre |
| Jurisprudência | `/jurisprudencia/<tribunal>-<id>/` | ex. `/jurisprudencia/stj-tema-1234/` |
| Súmulas | `/sumulas/<tribunal>-<n>/` | **já existe** — 217 páginas; entra atualização + novas |
| Legislação | `/leis/<slug>/` | `/leis/` já existe com 368 páginas |
| Diários oficiais | `/diarios/<uf>-<aaaammdd>/` | 404 hoje, livre |

Hubs de área **nascem sozinhos** (`internal/areahubroutes`), sem código novo. Custo em Go: apenas
`v2CanonicalPageTypes` (`content.go:199`) + o catálogo curado `homeAreaFamilies`
(`internal/render/home_areas.go:64`).

### 4.4 Estático ou dinâmico? — decisão fixada, com o critério

O nginx permitiria as duas vias (`try_files $uri $uri/ @fallback` → Go em `:8089`), então a escolha
é real. **Decisão: HTML ESTÁTICO, pelo mesmo caminho do acervo. Markdown continua dinâmico.**

| critério | estático (escolhido) | dinâmico (recusado) |
|---|---|---|
| **Coerência de artefato** | HTML em `public/` + linha no manifesto + entrada no sitemap, com SHA-256 batendo — a invariante que `publishedmanifest.Validate` **checa no boot do servidor** | página sem HTML em `public/` **quebraria a invariante** ou exigiria exceção. Exceção em coerência é como nascem 404 e 500 no índice do buscador |
| **Custo para o crawler** | sai do disco pelo nginx — **0,5 ms medido** | passa pelo Go. O contrato é explícito: *"deslocar CPU para o crawler é regressão P0"* |
| **ETag / 304** | nativo do nginx (mtime+size); com a Fase 0 corrigindo o churn, o **304 volta a funcionar** | exigiria implementar ETag no Go do zero |
| **Purga de borda** | `Cache-Tag` por área já funciona (`--tag`) | idem, mas sem ganho |

**O markdown permanece dinâmico** e não muda: `public/` tem **0 arquivos `.md`** e o
`internal/pagemarkdown` sintetiza em runtime — e é justamente esse canal que o **ClaudeBot está
consumindo agora** (§1.1-ter). Funciona, é leve, e não há motivo para materializar.

### 4.4-bis ★ NÃO-REGRESSÃO — o padrão que já vale 100/100 (ordem do dono)

O portal está hoje em **100 no Core Web Vitals** e **100 no agent-ready da Cloudflare**. Isso não é
sorte: é consequência de uma receita específica, medida por mim numa página real do acervo
(`/familia/divorcio-conjuge-mora-exterior/`):

| elemento | valor medido | por que importa |
|---|---|---|
| peso total | **23.877 B** (metade do teto de 50 KB) | margem real, não no limite |
| CSS externo (`<link rel=stylesheet>`) | **0** | um único CSS externo bloqueia render e derruba o LCP |
| `<style>` inline | 1, de **7.889 B** | todo o estilo chega no primeiro response |
| `<img>` | **0** | sem LCP de imagem, sem CLS de dimensão faltante |
| `<iframe>` | **0** | — |
| fontes externas (Google Fonts) | **0** | zero DNS/TLS de terceiro no caminho crítico |
| `<script>` | 3 (WebMCP, autorizado **por hash** na CSP) | única exceção, e ela é de integração de agente |
| JSON-LD | 2 blocos | estruturado sem custo de render |

**A regra, portanto:** *zero requisição de rede além do próprio HTML.* Uma única imagem, fonte
externa ou folha de estilo numa página nova **quebra o 100** — e o dono foi explícito sobre não
regredir.

**Invariantes que toda página diária deve cumprir, verificadas por gate antes de publicar:**

0. **As superfícies de agente que sustentam o agent-ready continuam servidas** — medidas por mim
   agora: `/.well-known/agent-card.json` (200, 3.281 B), `/.well-known/api-catalog` (200, 1.738 B),
   `/llms.txt` (200, 11.323 B), `/llms-full.txt` (200, **1.410.889 B**), `/openapi.json` (200,
   5.763 B), `/mcp` (405 em GET — correto, é POST-only), `/.well-known/security.txt` (200).
   **Conteúdo novo entra nesses catálogos**, não passa ao largo deles. O `llms.txt` já é escrito
   **na própria transação de publicação** (`main.go:1198`) e hoje declara os pontos de entrada
   (sitemap, feed Atom, home) e as superfícies de máquina (MCP, A2A, API, markdown gêmeo). As seções
   diárias entram ali como **pontos de entrada próprios** — `/noticias/`, `/jurisprudencia/`,
   `/sumulas/`, `/diarios/` com seus feeds — porque é esse o arquivo que um agente lê primeiro.
   A contagem "9710 páginas" do preâmbulo é derivada, então acompanha sozinha.
1. **Mesmo caminho de render** — `internal/render`, string builder, **sem template novo**. Página
   diária é um `page_type` novo no renderizador existente, não um renderizador paralelo.
2. **Zero recurso externo**: sem `<img>`, sem `<link rel=stylesheet>`, sem fonte remota, sem iframe.
   Ilustração de conteúdo jurídico não vale o custo — o valor está no texto.
3. **Teto de peso**: ≤ 50 KB é o contrato, mas a **meta é ficar na faixa do acervo (~25 KB)**.
   Gate reprova página diária acima de 30 KB — margem, não limite.
4. **Script**: nenhum script novo. O único autorizado continua sendo o WebMCP, por hash na CSP.
5. **CSP intocada** — `script-src 'sha256-…'`; mudar a política exige crítica adversarial (regra já
   vigente).
6. **JSON-LD acrescenta tipo, não troca base** — `NewsArticle`/decisão entram **ao lado** de
   `Article`, `FAQPage`, `BreadcrumbList`, `Legislation`, sem remover o que já pontua.
7. **`check-http-smoke` e o gate de peso rodam no ensaio da 8090 ANTES de produção**, comparando a
   página nova com a mediana do acervo — regressão medida é regressão barrada.

> **Régua de aceitação — e ela NÃO é dogma (emenda do dono, 2026-08-20):** *"não tem problema de
> quebrar os 100, se isso vai ajudar o projeto"*. Portanto:
>
> - o padrão acima é o **default**, porque é bom e custa zero — página que empata com o acervo passa
>   direto, sem discussão;
> - **quebrar o 100 é permitido quando houver ganho medido para o projeto** (ex.: uma tabela que
>   torna uma súmula compreensível, um dado estruturado que um agente de IA consome). O que **não** é
>   permitido é quebrar por descuido, por conforto visual ou por hábito de outro projeto;
> - toda exceção entra com **as duas medições no commit**: o custo (bytes, requisições novas, efeito
>   no LCP) e o ganho que a justifica. Regressão **medida e decidida** é engenharia; regressão
>   **acidental** é bug;
> - o teto de 50 KB e a proibição de framework/hidratação **permanecem** — esses são contrato de
>   indexação, não estética.

### 4.5 "O sitemap nasce junto" — por construção, não por convenção

`cmd/publish-v2-direct` já escreve **na mesma transação**: HTML em `public/`, `content/pages.json`,
`published_manifest.jsonl` e os shards de sitemap, com escrita atômica (temp + fsync + rename) e
snapshot de rollback. **Não existe caminho em que a página nasça sem o sitemap** — a transação falha
inteira ou grava tudo. O conteúdo diário usa esse mesmo caminho, sem atalho.

O que muda é **onde** a URL entra no sitemap: shard dedicado com ordinal reservado (§10.2 item 3),
para a coorte diária não rearranjar os ordinais do acervo.

### 4.6 URLs que não confundem bot — regras duras

1. **Uma URL por conteúdo.** Slug plano de 2 segmentos (`/jurisprudencia/stj-tema-1234/`), sempre
   com barra final, só `[a-z0-9-]` (`internal/router.IsCleanPublicPath`).
2. **Canonical HTTPS absoluto** em `wikijuridica.com.br`, apontando para a própria URL.
3. **Zero redirect na URL publicada.** Os **301 servidos ao Bingbot** (15 de 68 requisições, 22 %)
   são desperdício de orçamento de rastreio e viram item 0.10 da Fase 0.
4. **Nenhum parâmetro que altere o corpo.** Parâmetro de rastreamento (`utm_*`) serve o mesmo HTML
   com canonical para a URL limpa e **sem `noindex`** — regra já vigente no repo.
5. **Slug estável e imutável.** Publicada uma vez, a URL não muda: renomear obrigaria a redirect, e
   redirect confunde bot. Data no slug só quando ela **identifica** o conteúdo (diário oficial),
   nunca como desambiguador preguiçoso.
6. **Sem página de arquivo paginado por data no início** — hub cronológico só quando houver volume
   que o justifique, para não criar URLs magras que competem com o conteúdo real.

**Colisão de slug já tem gate — reusar, não reinventar:** `internal/v2publicpathcollision` e
`internal/v2crossshardcollision` existem e estão registrados em `internal/checks/checks.go`
(`v2-public-path-collision`, `v2-cross-shard-collision`). As seções novas são **áreas novas** — não
disputam slug com as 29 existentes (9.710 páginas, maior é `glossario` com 942) — mas a unicidade
**dentro** de cada seção diária passa pelos mesmos gates, sem exceção.

---

## 5. Mecanismo semântico — texto denso, nunca quebrado

O dono foi explícito: *"não basta puxar o conteúdo e ele sair quebrado"*, e *"não é só baixar a
súmula, tem que ter conteúdo explicando ela e os contornos e objetivos jurídicos"*.

**Janela de relevância (decisão minha, com critério de dado):** **180 dias** para jurisprudência.
Critério: `temas.csv` do STJ mostra **0,75 evento/dia corrido** nos últimos 120 dias — janela menor
esvazia a fila; janela maior traz precedente já assentado, que não é "em voga". Súmula e lei nova
não têm janela (entram sempre); lei **alterada** entra pela data da alteração.

**Pipeline de síntese, em 5 passos com gate próprio:**

1. **Extração — decidida por benchmark próprio, não por preferência.**

   | camada | escolha | evidência medida |
   |---|---|---|
   | **PDF** | **`pdftotext -enc UTF-8`** (poppler, GPL-2.0, **subprocesso** — não linka, não contamina o Go) | 0,09 s vs **4,27 s** do Tika (45×); e o **Tika duplicou o documento**: 32 `<div class="page">` num PDF de 16 páginas, `RESOLUÇÃO Nº 3.919` 2× |
   | DOCX/ODT/XLS | Tika 3.3.1 (Apache-2.0) fica **só** para isto | Tika continua útil fora de PDF |
   | **HTML** | **`go-trafilatura`** (Apache-2.0, Go puro, sem CGO) — **elimina o Python** | F1 **0,904** vs 0,908 do Python; **4,25 s vs 10,38 s** em 960 docs |

   **Go nativo para PDF não existe**: `pdfcpu` não extrai texto (issue aberta desde 2019),
   **`go-fitz` é AGPL-3.0 — proibido** (contaminaria o repo), `ledongthuc/pdf` quebra em
   CID/ToUnicode (típico de PDF de tribunal), `unipdf` é comercial.

   **Bug vivo a corrigir junto:** `internal/demandtextextractor.DefaultPythonBinary = "python3"`, e o
   `python3` do sistema **não tem trafilatura** — o venv `.cache/demand-extraction-venv` só é
   alcançável por flag que **nenhum código resolve**. O extrator de HTML está quebrado hoje; adotar
   `go-trafilatura` apaga venv, `exec`, timeout e o defeito de default de uma vez.

2. **Segmentação jurídica — o repo já resolve, falta ampliar.** `internal/ptbrtext.Sentences`
   (uax29/v2 + `shouldJoinNextSentence`) já tem 24 abreviações protegidas em
   `sentenceJoinAbbreviationSuffixes` (`text.go:842`), incluindo `art.`, `inc.`, `n.`, `p. ex.` —
   então **`art. 5º, inc. II` já não vira duas sentenças**. Faltam, como fato de código:
   `fls.`, `ss.`, `al.`, `cf.`, `j.`, `Rel.`, `Min.`, `Des.`, `Proc.`, `Súm.`, `Ac.`, `ed.`,
   `cap.`, `Ltda.`, `S.A.` — ampliar a lista e testar contra corpus real.

3. **Sumarização extrativa sem LLM externa — LexRank sobre embeddings estáticos.**
   `internal/model2vec` já tem `Embed`, `CosineSim` e `BuildHNSW`; falta o grafo + power-iteration
   (~120 linhas). **Duas pendências reais, medidas:**
   - **Nenhum modelo existe no disco** (`find` por `.m2v` → 0). É preciso baixar
     `potion-multilingual-128M` (512.361.560 B em f32; ~256 MB em f16, ~128 MB em i8) e converter
     pelo `SaveModel`.
   - **Armadilha que faria o resumo mentir em silêncio:** o vocabulário do potion é **subpalavra
     (BPE do bge-m3)** e `model2vec.Tokenize` é **palavra inteira (UAX#29)**. O lookup não falha —
     devolve **vetor degradado**. Ou o conversor agrega subtokens em entradas de palavra inteira,
     ou o chamador usa o tokenizer HF (18,6 MB). Sem resolver isso, o embedding "funciona" e mente.
   - Alternativas puro-Go se o modelo não fechar: `DavidBelicza/TextRank` (MIT) e `didasy/tldr`
     (LexRank, MIT) — TF-IDF em vez de embedding, qualidade menor mas sem pendência de modelo.

   > **Isto NÃO é bloqueador da sessão** — a crítica adversarial concluiu que era, e a conclusão não
   > se sustenta. Baixar `potion-multilingual-128M` (512 MB) e convertê-lo por `SaveModel` é
   > **trabalho desta sessão**, não impedimento externo: não exige credencial, cadastro nem
   > aprovação. E há **caminho de contingência imediato** — `TextRank`/`tldr`, MIT, puro Go, sem
   > modelo — que entrega sumarização extrativa funcional no mesmo dia. A ordem de ataque é:
   > (1) tentar o model2vec com o conversor que agrega subtokens; (2) medir a qualidade contra
   > amostra real; (3) se não fechar, TextRank entra e o model2vec vira melhoria posterior **da
   > mesma sessão**. Em nenhum cenário a Fase 2 fica sem sumarizador.
4. **Comentário autoral** — a camada que dá valor: contexto, alcance, efeito prático, limites.
   É o que separa a página de um espelho.
5. **Detector de texto truncado** (NOVO — o maior risco) — reprova conectivo pendurado, frase sem
   verbo principal, corte no meio de citação, mojibake. **Nasce com teste de falso positivo sobre
   amostra real**, como manda a política de detectores do repo.

### 5.1 Anatomia editorial por tipo de página

O dono fixou a régua: *"não é só baixar a súmula, tem que ter conteúdo explicando ela e os contornos
e objetivos jurídicos… nada raso, mas também nada muito denso, de forma que o leitor e as IAs leiam
sem desistir"*. Cada tipo nasce com estrutura própria, reusando o contrato v2 de 11 campos
(`opening`, `sections[]`, `faq[]`, `official_sources[]`).

**Súmula** — alvo 600–900 palavras
| bloco | conteúdo |
|---|---|
| `h1`/`opening` | o que a súmula resolve, em linguagem direta (não o texto dela) |
| bloco citado | **texto oficial integral**, identificado, com tribunal, número, data e URL |
| "O que ela decide" | tradução do enunciado para efeito prático |
| "De onde veio" | precedentes que a originaram, o conflito que ela pacificou |
| "Até onde alcança" | hipóteses que **não** cobre — o que mais gera erro |
| "O que mudou depois" | superação, revisão, cancelamento, ou lei posterior |
| `faq[]` | 2–3 perguntas reais de quem pesquisa o tema |

**Jurisprudência / tese** — 700–1.000 palavras. Tese firmada (citada) · caso concreto em 3 linhas ·
fundamento · **efeito para quem está na mesma situação** · o que ainda está em aberto.

**Notícia jurídica** — 350–600 palavras. Fato reescrito autoralmente (**nunca a redação da fonte**) ·
por que importa juridicamente · qual norma/decisão sustenta · link para a fonte oficial. Piso menor
exige `MIN_WORDS_HARD` por `page_type` (§6).

**Lei/norma nova** — 600–900 palavras. Ementa citada · o que muda na prática · quando entra em vigor ·
o que revoga ou altera · quem é afetado. Texto integral **linkado**, não espelhado.

**Diário oficial** — página **agregada por UF/dia**, nunca por ato individual (evita thin content e
reduz exposição LGPD): panorama do que saiu de juridicamente relevante, com os atos listados,
classificados por `artType`/órgão, cada um linkado à fonte.

**Regra transversal — o piso autoral.** Em todas: o comentário próprio tem de superar o piso medido
por `check-derived-authorial-floor`; página cujo valor esteja no texto oficial e não na explicação
**é reprovada**, porque seria espelho.

**LGPD — regra fixa:** nome de pessoa física natural não entra em página derivada. Diário e DJe
trazem nome civil (medido: íntegras do STJ com nome real de parte). O pipeline **anonimiza por
padrão**; nome de agente público em ato de nomeação só aparece quando for o próprio objeto do ato.

---

## 6. Gates novos (registrados em `internal/checks/checks.go`)

| gate | o que reprova |
|---|---|
| `check-derived-source-fidelity` | citação sem `official_sources[].verified_at`, `http_status` e hash do documento; afirmação sem `anchor_claim` |
| `check-derived-authorial-floor` | comentário autoral abaixo do piso — impede espelho disfarçado |
| `check-text-truncation` | texto quebrado, conectivo pendurado, mojibake, citação cortada |
| `check-daily-freshness-signals` | página do dia sem `lastmod` correto, fora do feed, ou sem IndexNow |
| `check-collect-politeness` | requisição sem robots verificado, sem UA identificável ou acima do teto diário |
| **`check-legal-citation-attribution`** | **★ o gate que faltava, e é o de maior risco.** O `CLAUDE.md` registra que citação legal mal atribuída aparece em **~8 % das páginas auditadas por humano** e que **nenhuma medição automática a detecta**. A 13–20 páginas/dia, isso seria **1 a 1,6 citações jurídicas erradas por dia, assinadas por OAB/RJ 227191**. O gate valida cada citação (artigo, súmula, tema, acórdão) **contra a fonte oficial coletada** — número, órgão, vigência e se não foi cancelada/superada. **Sem ele funcionando e medido, a publicação diária não começa** — ou entra revisão humana por página |
| **`check-pii-anonymization`** | **★ LGPD deixa de ser asserção.** §5.1 dizia *"o pipeline anonimiza por padrão"* sem implementação — era o mesmo defeito do `checked_at`. Diário oficial e DJe trazem **nome civil real** (medido: íntegras do STJ com nome de parte). O gate exige anonimizador **medido** (com teste de falso negativo sobre amostra real de diário), cobrindo iniciais, abreviaturas e sufixos (`Silva Jr.`) que regex ingênua não pega. **Enquanto não passar, F6/F7/F9 (diários) ficam fora da Fase 2** |
| `check-daily-cross-source-dedup` | **o mesmo fato chegando por duas fontes** — a mesma decisão do STJ vem por feed Atom **e** pelo CKAN; a mesma norma vem por `normas.leg.br` **e** pelo DOU. Sem isso, o portal publica a mesma coisa duas vezes com títulos diferentes, que é duplicação em escala |

**Reusar, não reinventar:** o repo já tem `internal/bloomdedupe`, `internal/legalminhash`,
`internal/v2bodyneardup` e `internal/v2bodysemanticdedup`. A dedup **entre fontes** é uma camada
nova (chave de identidade do ato: tribunal + classe + número, ou URN da norma), mas a dedup **de
corpo** aproveita o que existe.

**Mudança silenciosa de formato na fonte também já tem base:** `cmd/monitor-source-changes` compara
**hashes** do conteúdo textual das fontes oficiais citadas em `official_sources` e emite
`data/source-audit/sourcewatch_report.jsonl` marcando candidatas a revisão — sem nunca gravar o
texto bruto. Somam-se `internal/jsonfieldscan`, `internal/jsonfieldsdiff` e
`internal/jsonschemagate` para detectar mudança de **schema** de API (o caso do
`edicoes_from_data` que devolve `{"erro":true}` com **HTTP 200**). O que falta é ligar isso ao
pipeline diário como gate de coleta — não construir do zero.

**Ajustes necessários em gates existentes** (achados dos agentes):
- `MIN_WORDS_HARD = 250` é **global**; passa a ter **piso por `page_type`** (notícia ≠ artigo).
- `sem_linha_no_censo` pula qualquer página nova → o censo passa a ser regerado no pipeline.
- **Lane nova `derivada_de_fonte_oficial`** que **jamais** habilita CTA comercial.

---

## 7. Frescor — consertar o sinal falso

1. **Granularidade de `<updated>`/`lastmod`** — hoje 866 entradas compartilham a mesma data e o
   sitemap usa `YYYY-MM-DD`, então duas publicações no mesmo dia são indistinguíveis. Passa a
   timestamp completo, ordenável.
2. **Feed por seção** — `/noticias/feed.xml`, `/jurisprudencia/feed.xml`. O cap global de 1.000 em
   9.710 páginas hoje esconde 8.710 URLs.
3. **Sitemap de News** (`<news:news>`) — **não existe** (`/news-sitemap.xml` → 404). Regras oficiais
   medidas: **só URLs dos últimos 2 dias**, teto de **1.000** entradas, obrigatórios
   `news:publication` (name+language), `news:publication_date` (W3C) e `news:title`. Ressalva
   honesta: `news:name` precisa bater com o nome registrado no Google News — na prática exige ser
   publisher aprovado, e o doc **não afirma isso literalmente** (*sem fonte oficial* quanto à
   obrigatoriedade formal). Entra **depois** de haver cadência diária real, não antes.
4. **RSS** — `feed.RenderRSS` **já existe e nada o publica** (`internal/feed/feed.go:255`). Passa a
   ser servido.
5. **Purga seletiva por `Cache-Tag`** — **já existe** (`tools/purge-edge-cache --tag`, com
   `Cache-Tag: wj-acervo,area-sumulas` por área). O pipeline diário passa a usá-la em vez da purga
   total, que deixa a borda fria (medido: 9.994 miss em 10.020 URLs). Ressalvas medidas: `/`,
   `robots.txt` e `sitemap.xml` **não** carregam Cache-Tag (exigem `--url`), e a API tem teto de
   ~16 KB / ~1.000 tags por chamada — lote grande precisa de paginação, sob pena de falha silenciosa.
6. **★ Publicação incremental — NÃO é uma flag, é mudança de semântica do publicador.**
   `--limit N` hoje faz `selected = selected[:N]` (`main.go:265`) sobre lista ordenada por
   `intent_id` — publica os N primeiros **alfabéticos**, não os novos.

   **O risco, verificado no código, é derrubar o site:** `writeManifest` (`main.go:2483`) faz
   `os.Create(published_manifest.jsonl)` — **trunca e reescreve o manifesto inteiro** a partir do
   conjunto selecionado. O publicador é **reescritor de corpus**, não incremental. Um `--since`
   implementado como filtro ingênuo produziria:

   ```
   manifesto reescrito só com as páginas do dia
      → ~9.7 mil <loc> de sitemap sem linha de manifesto
      → sitemap_loc_without_manifest  (NÃO está em staticArtifactOnlyIssueCodes)
      → abort no boot (teto: 10 do mesmo código / 25 no total)
      → cmd/server/main.go:54 log.Fatal → o Go NÃO SOBE
      → o nginx segue servindo HTML estático, mas /index.md morre (public/ tem 0 arquivos .md)
      → o canal markdown que o ClaudeBot consome desaparece, e o site "parece no ar"
   ```

   **Portanto o incremental é implementado assim:** o conjunto publicado é sempre o **corpus
   completo** (acervo + novas do dia); `--since` seleciona apenas **o que é reescrito em disco** e
   **o que entra no delta de notificação** (IndexNow/feed/purga), nunca o que entra no manifesto.
   Com a correção-mãe (§12.0), reescrever o corpus inteiro passa a ser barato: `grava` compara bytes
   e devolve `e.iguais ≈ 9.710`. **Teste obrigatório antes de produção:** publicar com `--since` no
   ensaio da 8090 e verificar que o manifesto continua com **todas** as linhas e que o servidor sobe.
7. **JSON-LD** — acrescenta `NewsArticle` (com `datePublished`/`dateModified`) e o tipo adequado
   para decisão judicial, sobre a base que já emite `Article`, `FAQPage`, `Legislation`.
8. **IndexNow no publish** — hoje está em `tools/deploy-publico`, **não** em `cmd/publish-v2-direct`.
   Passa a disparar na transação, junto de WebSub e purga. **Com disciplina medida:** a FAQ oficial
   declara que *"toda URL submetida por IndexNow conta na cota de rastreio do site"* — submeter URL
   **sem mudança real queima cota**. Logo, só entra o que mudou de fato (o que a Fase 0 torna
   verificável). Teto por requisição: 10.000 URLs. Consumidores confirmados: Bing, Yandex, Seznam,
   Naver, Yep, Amazon — **o Google não participa** (sem fonte oficial de adesão).

### 7.1 A vantagem competitiva já existe e nenhum concorrente tem

Medido nos portais jurídicos de referência (sem copiar nada deles):

| portal | markdown para IA | postura com bot de IA | volume/dia | reprodução |
|---|---|---|---|---|
| Jusbrasil | não | **403 a tudo**; `llms.txt` manda o LLM **omitir tribunal e nº do processo** | não mensurável | conteúdo próprio protegido |
| Migalhas | **não** (`.md` devolve HTML em soft-200) | robots **libera** bots de IA | **70–86** | *"não está autorizada"* |
| JOTA | não (`.md` → 404) | libera | 30–35 | protegido |
| ConJur | não | **56 blocos `User-agent`** — fechado à IA | ~80 | protegido |
| **WikiJurídica** | **sim, e em uso real pelo ClaudeBot agora** | aberto e sinalizado (`Content-Signal`) | a construir | **domínio público + autoral** |

**Duas conclusões operacionais:** (i) nenhum concorrente serve markdown a agentes — o wiki serve, e
há prova de consumo; (ii) esses portais são **sinal de pauta**, nunca fonte de texto (os termos
proíbem reprodução) — o que se aproveita é *qual assunto entrou na agenda hoje*, escrevendo a partir
da fonte oficial primária.

> Achado que vale registrar: o `llms.txt` do Jusbrasil instrui o assistente a **não mencionar
> tribunal, órgão julgador nem número do processo** ao citar jurisprudência. Isso degrada
> verificabilidade — e é exatamente o oposto do que este plano faz, que é **citar a fonte com
> URL, data e hash**. É onde a wiki ganha confiança de assistente de IA.

---

## 8. Ensaio em porta isolada — antes de produção

O dono exigiu testar em outra porta. Há um **bloqueador achado**, e ele é de anti-fraude:

> `WIKI_ACCESS_LOG_DIR` **não existe**. `internal/httpserver/httpserver.go:784` hardcoda
> `root/data/ops/access/`. Uma instância de ensaio escreveria no **mesmo ledger** que decide SEO,
> como `warming:false, bot_simulation:false` — **indistinguível de tráfego real**.

**Correção obrigatória antes do ensaio:** criar `WIKI_ACCESS_LOG_DIR` + campo `instance` no
`accessEntry`. Sem isso, o ensaio polui a métrica — exatamente o que o contrato proíbe.

**Envelope do ensaio:** porta **8090** (já suportada por `tools/generate-nginx-standalone --porta
8090` e validada em `docs/ISOLAMENTO_NGINX.md`), com `WIKI_CACHE_DIR` isolado — a memória registra
que segunda instância no mesmo cache **destruiu o índice de busca em produção**. Smoke por socket
real (hoje `check-http-smoke` roda **em processo**, nunca abre socket — outra lacuna a preencher).

---

## 9. Agendamento diário

**Nenhum dos 13 timers produz conteúdo.** Nasce `wikijuridica-daily-content.timer` (systemd, padrão
já usado no projeto), com: janela de madrugada escalonada por fonte, `nice`, teto de duração,
`flock` contra concorrência, evidência em ledger e alerta em `data/ops/owner_alerts.jsonl` quando
falhar. Sem hardcode de data: tudo derivado do relógio e do estado.

**Limites diários por fonte** (para não sobrecarregar o servidor, como o dono pediu): teto de
requisições e de páginas geradas por fonte/dia, configurável em `content/`, medido e registrado.

---

## 10. Regras de verificação — ceticismo obrigatório

1. **Todo número deste plano tem medição própria reprodutível.** Hash determinístico (`blake2b`),
   nunca `hash()` do Python.
2. **Output de agente é alegação até leitura própria no disco.** Nenhum relatório vira decisão sem
   `Read`/`Grep` no arquivo citado.
3. **★ NÃO CONFIAR NOS GATES — ordem do dono, e esta sessão é a prova.**
   **Gate verde não é prova; gate vermelho não é veredito.** Evidência colhida hoje, no próprio repo:

   | o que os gates deveriam ter pego | o que aconteceu |
   |---|---|
   | 9.710 páginas afirmando *"Verificado em 20/08"* sem nenhuma verificação | **347 checks registrados, nenhum apanhou** |
   | `lastmod` do sitemap contradizendo o `Last-Modified` do HTTP em 96,5 % das URLs | nenhum check compara os dois |
   | `dateModified` **14 dias antes** de `datePublished` no JSON-LD | nenhum check testa a ordem |
   | `checked_at` sendo `time.Now()` copiado de `reviewedAt` | nenhum check lê a origem do campo |
   | `DefaultPythonBinary = "python3"` apontando para um Python **sem trafilatura** | extrator quebrado, nenhum check executa o caminho |

   **Regra operacional:** antes de decidir por um gate, **ler a implementação dele**; antes de
   confiar num verde, **medir o fato no dado cru**. Gate novo nasce com **teste de falso positivo
   sobre amostra real** e com a pergunta explícita *"o que este gate NÃO vê?"* documentada ao lado.
   Verde de gate nunca substitui leitura da amostra publicada.

### 10.0-bis Gate não pode virar armadilha de looping (ordem do dono)

Ferramenta de gate mal dimensionada trava agente em laço e queima tempo e dinheiro sem produzir
nada. **Todo gate novo deste plano nasce com estas cinco condições, medidas ANTES de entrar no
pipeline diário:**

1. **Custo medido antes de ligar.** Tempo de parede e memória sobre o corpus real de 9.710 páginas,
   registrados no commit. Gate sem número de custo não entra.
2. **Teto duro e condição de parada explícita** — limite de registros, de tempo e critério de fim.
   **É proibido "corrigir" lentidão aumentando timeout** (regra do repo: lentidão em 10k é bug P0,
   resolve-se com shard/índice/incremental).
3. **Reprovação é acionável, não circular.** A mensagem diz **qual registro**, **qual campo** e
   **qual correção** — gate que reprova sem apontar o quê leva o agente a tentar de novo às cegas.
4. **Detector de laço, com corte automático.** Mesmo gate reprovando o **mesmo item** pela 3ª vez =
   **para, não repete**: escala para revisão humana/adversarial e registra. Rodar o mesmo reparo
   três vezes é a assinatura de causa-raiz não atacada.
5. **Idempotência e incremental.** O gate roda só sobre o **delta do dia**, nunca sobre a árvore
   inteira a cada execução — e duas execuções seguidas sobre o mesmo delta produzem o mesmo
   veredito, sem efeito colateral.

**No pipeline diário isso vira envelope de execução:** cada onda tem teto de duração, `flock` contra
concorrência, `nice`, e **auditor independente do produtor** (§10.2 item 1). Onda que estoura o teto
**não é reexecutada em laço** — falha, alerta por `notify-owner`, e a causa é investigada.
4. **Detector novo nasce com teste de falso positivo** sobre amostra real.
5. **Crítica adversarial Fable antes de cada mudança cara** (gate, política, publicação, produção).
6. **Advisor** antes de fixar abordagem e antes de declarar pronto.
7. **Nada vai a produção sem ensaio na 8090** com medição comparativa.
8. **Baseline de bots re-medida em D+7 e D+30** — mas pela métrica certa (abaixo).

### 10.1 A métrica de sucesso (decisão fixada)

**Não é requisições/dia** — é dominada por cache e amostragem (gap medido de 38× borda×origem).
A métrica é **time-to-first-crawl**: o intervalo entre publicar uma URL e o crawler pedi-la pela
primeira vez, cruzando data de publicação × `paths_first_seen` (dict de 9.845 paths por crawler,
já existente em `data/ops/crawl_coverage_state.json`, **hoje sem nenhum consumidor que faça esse
cruzamento**).

**Instrumentos a criar ANTES da primeira publicação** — senão a linha de base do "antes" se perde:

| instrumento | por quê |
|---|---|
| `tools/measure-time-to-first-crawl` | a métrica do plano; hoje ninguém cruza publicação × `first_seen` |
| `cmd/check crawl-edge-origin-reconciliation` | o gap de 38× passou sem nenhum alarme |
| cobertura **por prefixo de rota** | a cobertura é global; `/noticias`, `/jurisprudencia` precisam de série própria |
| alarme de regressão de crawl | bot que some por N dias hoje não dispara nada |
| `tools/measure-bot-engagement-pattern` | classifica o **padrão** de cada bot (rajada única · polling · busca sob demanda · abandono) a partir do log cru, com o IP do scanner excluído. É o que permite dizer **por que** um bot parou, não só que parou |
| `tools/measure-bot-demand-signals` | extrai as URLs pedidas **repetidamente** por bot de busca de IA (hoje: 32× `/previdenciario/maternidade-homem/` pelo OAI-SearchBot). Vira **fila de aprofundamento editorial por demanda medida** — o sinal mais próximo de citação que existe |

**Fonte de verdade por pergunta** (misturar as três é o erro de ~100× já catalogado):
contagem → borda via `serie_saneada`; descoberta → `crawl_coverage_state`; autenticidade, forjado,
PerplexityBot e referer → **origem**.

**`clique_de_volta = 0` é aceito como KPI de partida.** Inventar proxy de citação seria a fraude de
métrica que o contrato proíbe. O sinal precursor legítimo é `chatgpt-user` (~21/dia).

---

## 10.2 Armadilhas medidas que quebrariam a implementação

Cada uma foi verificada no disco hoje. São as que matam um pipeline diário ingênuo:

1. **Unit `success` ≠ objetivo cumprido.** `wikijuridica-edge-warm` fecha `Result=success`,
   `ExecMainStatus=0`, ledger com `failures: 0` — e no mesmo registro `cache_status.miss: 10.004`.
   O auditor independente mediu **2,5 % de cobertura**. Toda unit de conteúdo nasce com
   **produtor + auditor independente + `notify-owner`**, nunca só com a contagem do que ela mesma fez.
2. **`OnFailure` não existe em nenhuma unit** (zero ocorrências). Falha ≥ exit 2 ou crash **não avisa
   ninguém**. Criar `wikijuridica-alerta@.service`. Preservar `SuccessExitStatus=0 1` (exit 1 é
   veredito medido, não defeito).
3. **★ Shard de sitemap: o churn diário é matemático, não hipotético.** A partição é por
   `(data de revisão, área)` com **`minCohortURLs = 50`** (`internal/sitemap/shard_partition.go:178`)
   e o ordinal é **posicional** (`pages-%04d.xml`). O volume diário fixado (§12.1) é de **13–20
   páginas — abaixo de 50**, então **toda coorte diária seria fundida**, rearranjando ordinais
   todo dia. O dano já é documentado no próprio repo, com log:

   ```
   13:50:43  /sitemaps/pages-0032.xml  200  28.876 bytes
   ~13:55    publicação encolhe o plano, arquivo removido
   13:58:07  /sitemaps/pages-0032.xml  410
   14:08:31  /sitemaps/pages-0032.xml  410  Googlebot
   ```

   `internal/sitemapgrace` remedia com carência, mas publicação diária transformaria o incidente em
   **rotina diária de 410 ao Googlebot**.

   **Decisão arquitetural — e ela é AÇÃO, não constatação** (a crítica apanhou que eu havia
   identificado sem agir): o conteúdo diário vai para **shard próprio, com ordinal reservado e
   monotônico** (nunca reciclado), fora da partição por `(data, área)` do acervo. Implementação
   concreta: reservar uma faixa de ordinal para a família diária (ex.: `pages-9xxx`), com a coorte
   diária **acumulando no mesmo shard até atingir `minCohortURLs`** em vez de criar um shard por
   dia — assim nenhuma coorte fica abaixo do piso e nada se funde/desfunde. O acervo para de sofrer
   churn e o shard diário cresce sem deslocar ninguém. A carência do `sitemapgrace` permanece como
   rede de segurança, não como mecanismo principal.

10. **★ Não existe via de RETIRADA de página publicada — e publicação diária exige uma.** O contrato
    proíbe deletar ou reverter página escrita (`[[pagina-escrita-nunca-descartada]]`), e a máquina
    correta é a de **supersessão** (`internal/v2semanticrecut`, `finalize-v2-semantic-recut`), que o
    plano não mencionava. Publicar diariamente sem via de retirada é publicar sem freio: uma página
    com citação errada ou com PII vazada precisa **sair do ar hoje**, preservando o texto.
    **Implementação nesta sessão:** ligar o pipeline diário à supersessão existente, com um caminho
    de "retirada de emergência" que (a) marca a página como superada, (b) preserva o texto no
    histórico, (c) remove do sitemap e do manifesto **na mesma transação**, e (d) purga a borda por
    tag. Testado no ensaio da 8090 antes de a primeira página diária ir ao ar.
4. **`build.Site` aborta se página de mão colidir com hub.** O índice `/noticias/` tem de ser o **hub
   derivado**, nunca uma `content.Page` em `pages.json`.
5. **`v2CanonicalPageTypes` falha em silêncio**: tipo desconhecido devolve `ok=false`, a página cai
   em `IsLegalContent()=false` e **some da contagem e do sitemap** sem erro nenhum.
6. **`cmd/build public` apaga `public/` inteiro.** No fluxo diário o escritor é
   `cmd/publish-v2-direct` (diff + rename atômico).
7. **Wrapper de cache de binário em timer falha quase toda janela** ("refusing stale or tampered
   binary") porque o fingerprint da árvore muda com escrita concorrente — usar `ExecStartPre` com
   build próprio, como documenta `ops/proposed/v2-official-source-verify.service:12-26`.
8. **Execução manual colide com a do timer** (medido: warms com `rps 12` fora do slot). A ferramenta
   precisa de lock de instância única, não só `Type=oneshot`.
9. **Escrita concorrente**: 50+ arquivos `M` agora. Unit que escreve em `data/editorial/` disputa com
   sessões vivas — só CAS/lease é seguro.
9-bis. **O rollback é ineficiente para cadência diária — medido.** `writeRollbackSnapshot`
   (`main.go:2657`) copia `content/pages.json` **inteiro** (70 MB) + manifest + rehearsal a cada
   publicação. Estado medido: **67 snapshots = 6,2 GB**, sem política de retenção. Cada snapshot
   custa **98 MB** para preservar um delta que, na cadência do plano, será de **13–20 páginas**.
   Projeção com uma publicação/dia: **~35 GB/ano** — e hoje houve **6 publicações num único dia**.

   > **Nota do dono (2026-08-20):** *"não se baseie muito pelo tamanho do disco, tem coisas que vou
   > limpar; é observação, não regra"*. Portanto **espaço em disco NÃO limita o volume nem a
   > cadência deste plano**. O item permanece por ser desperdício de engenharia (200× sobre o que
   > protege), e não por escassez.
   **Ações:** (a) política de retenção (manter os N últimos + o último de cada dia, purgar o resto);
   (b) snapshot **incremental** — guardar o delta, não a árvore; (c) compressão (`pages.json` é JSON
   e comprime muito). Sem isso, o pipeline diário enche o disco e derruba o portal por falta de
   espaço — falha silenciosa e evitável.

   **O contraste que dimensiona o absurdo** (medido): `public/` ocupa **296 MB** para 9.929 páginas
   = **30,5 KB/página**, e as 5.500 páginas novas projetadas para um ano custariam **0,16 GB**.
   O rollback, na mesma cadência, custa **~35 GB/ano** — **200× mais que o conteúdo que ele
   protege**. O conteúdo diário é barato; o que não escala é o mecanismo que o acompanha.
10. **`data/ops/access/*.jsonl` não é o log do site** (é do binário Go, ~1 % das URLs, sem IP), e os
    relógios diferem: ledger Go em UTC, cursor de origem em UTC−3.

**Acrescentadas pela crítica adversarial (Fable):**

11. **Publicar mais rápido que o regime de rastreio faz o acervo antigo decair.** O Googlebot opera
    em ~30–57 paths/dia; despejar centenas de URLs novas por dia compete com as 26,9 % do acervo que
    ele nunca visitou. **Consequência para o plano:** volume diário **calibrado**, não máximo — e
    prioridade de links internos para o que ainda não foi descoberto.
12. **O `/feed.xml` já está saturado** no cap de 1.000 (866 entradas de um único lote). Publicação
    diária expulsa as antigas do canal de descoberta por feed — outro motivo para feed **por seção**.
13. **A purga nunca foi validada contra a API real** (o próprio script admite "SEM medição"), e o
    `Cache-Tag` tem teto de ~16 KB/~1.000 tags: no dia de lote grande, falha **silenciosa**.
14. **STF e TSE têm WAF próprio** — o problema de coleta se repete, pior, na fonte que vira página.
    O plano trata isso na regra dos três degraus (§2) e rebaixando TSE a "não rastrear".

---

## 11. Meta-exigências do dono

1. **Versionar o plano no repo e commitar ANTES de começar.** Este arquivo vira
   `docs/goal/PLANO_FRESCOR_DIARIO.md` e é commitado como **passo 0**, antes de qualquer código.
   Junto dele vai `docs/data-sources/FONTES_DIARIAS.md` com a matriz medida (§3), para a evidência
   desta sessão não morrer no transcript.
2. **Tasklist.** Uma task por item deste plano em `.agents/runtime/p0_frontboard.jsonl`
   (`id`, `status`, `priority`, `evidencia`), criada **antes** da execução. Toda fonte 🟡/🔴/⏳
   entra como task de investigação — nada é descartado por parecer difícil.
3. **Notificação no terminal — mecanismo concreto, não promessa.** Uso `tools/notify-owner`, que já
   existe (239 linhas) e entrega em **3 canais**: `notify-send` no bus do usuário, `logger` com tag
   `wikijuridica-alerta` e `data/ops/owner_alerts.jsonl`, com cooldown por chave e `evidencia`
   obrigatória em severidade alta. Fica ligado a:
   - `wikijuridica-alerta@.service` (`OnFailure=` em **toda** unit nova — hoje **nenhuma** unit tem
     `OnFailure`, então falha de exit ≥2 não avisa ninguém);
   - um **fiscal de plano**: verificação que lê o frontboard e alerta task aberta sem progresso,
     para nenhum item ser esquecido;
   - o **auditor de resultado** de cada onda diária (produtor ≠ auditor, §10.2 item 1).

### 11.1 Cobertura do que foi pedido — conferência item a item

| pedido do dono | onde está |
|---|---|
| Súmulas STF, STJ e tribunais inferiores | §3 F1/F5 (STF: 736 + 63 vinculantes), F2/F3 (STJ), TST via backend REST; anatomia em §5.1 |
| Jurisprudência atual e relevante, sem focar no passado | §3 F1/F2/F3; janela de **180 dias** fixada em §5 com o critério de dado |
| Leis federais na íntegra | §3 F4 (`normas.leg.br`, JSON-LD, CC-BY 4.0) |
| Diário Oficial da União | §3 F9 (2.956 matérias/dia), com a ressalva de robots e a regra dos três degraus (§2) |
| Diários de todos os estados e do DF | §3 F6 (5 UFs com API JSON) + 22 UFs restantes na Fase 3 desta sessão |
| Diários dos principais municípios | §3 F7 (Querido Diário, 295/dia, 228 municípios) + F8 (Sigpub, 36 portais) |
| Seção de notícias | §3.2 (8 feeds medidos) + §4.3 rota + §5.1 anatomia + regra de licença |
| Notificar os bots de conteúdo fresco | §7 (IndexNow no publish, WebSub, feed por seção, news sitemap, purga por tag) |
| Sem hardcode | §9 (tudo derivado de relógio e estado; limites em `content/`) |
| Rotas nomeadas | §4.3 |
| APIs públicas investigadas | §3 — 11 famílias, todas com medição própria |
| Scraping inteligente com semântica | §5 (5 passos, com detector de truncamento) |
| Denso, não raso, sem thin content | §5.1 (pisos por tipo) + §6 (`check-derived-authorial-floor`) |
| SEO + markdown para bots de citação | §7 item 7 (JSON-LD) + markdown já servido por negociação |
| Testar em outra porta antes de produção | §8 (porta 8090, com o bloqueador `WIKI_ACCESS_LOG_DIR` resolvido antes) |
| Limites para não sobrecarregar | §2 item 2 e §9 (teto por fonte/dia, `flock`, `nice`, headroom) |
| DataJud expandido | §3.1 — investigado a fundo: 91 aliases, 352 M docs, e a razão medida de sair da rota principal |

### 11.2 Divergências conscientes do que foi pedido — declaradas, não escondidas

Três pontos em que decidi diferente do exemplo dado. Em cada um, a razão é medida, e a decisão é
minha por ordem expressa ("você decide e isso deve ir para o plano, sem margem"):

| pedido literal | decisão | razão |
|---|---|---|
| `wikijuridica.com.br/news` | **`/noticias/`** | o portal é PT-BR e as 38 áreas existentes são todas em português; `/news` destoaria do acervo inteiro |
| `wikijuridica.com.br/jurisprudencias` | **`/jurisprudencia/`** (singular) | "jurisprudência" é substantivo coletivo — o plural é incorreto em português jurídico, e o portal é assinado por advogado. `/sumulas/`, `/leis/` e `/diarios/` ficam no plural, acompanhando o padrão vivo |
| "expandir o DataJud, restrição demais é bug" | **rebaixado a uso estatístico** (§3.1) | a API **não é restrita** — 91 tribunais, 352 M documentos respondem. Mas **não tem texto de decisão** (censo de campos: sem ementa, sem íntegra, sem partes), tem lag de **6–41 dias**, e o Termo de Uso V1.2 (3.3/3.8) veda uso comercial e exploração de informação derivada. O que se queria dele — jurisprudência recente com texto — vem melhor de F1/F2/F3 |

**Nenhum item foi descartado.** DataJud, DOU, as 22 UFs sem API, TST, TSE e Sigpub permanecem no
plano com task própria (Fase 3), cada um com a razão medida do seu lugar na fila.

---

## 12. Ordem de execução

### 12.0 A correção-mãe — uma causa, quatro defeitos

Investigando a origem do `checked_at` (a lacuna que o advisor mandou fechar), a causa-raiz apareceu
e ela é **única** para os quatro defeitos de §1.2:

```
cmd/publish-v2-direct/main.go:155   publishedAt  default → defaultRevisionDate() = time.Now()
cmd/publish-v2-direct/main.go:156   reviewedAt   default → defaultRevisionDate() = time.Now()
cmd/publish-v2-direct/main.go:283   ambos → render → ENTRAM NO HTML PUBLICADO
cmd/publish-v2-direct/main.go:2507  ApprovedAt: opts.publishedAt
cmd/publish-v2-direct/main.go:2621  CheckedAt:  opts.reviewedAt
```

**A cadeia de dano, medida ponta a ponta:**

```
data do relógio entra no HTML
   → os bytes do arquivo mudam
   → `grava` (main.go:2007) reescreve — ele JÁ é content-addressed
     (`if bytes.Equal(atual, novo) { return false }`), mas os bytes mudaram DE VERDADE
   → 9.711 arquivos reescritos, mtime rotaciona
   → ETag do nginx (derivado de mtime+size) rotaciona
   → o Googlebot NUNCA recebe 304, paga 25 KB por revisita
   → e o `lastmod` do sitemap, que vem de outro campo (`content_revised_at`, CORRETO em 06/08),
     passa a contradizer o `Last-Modified` do HTTP
```

**Correção do item 0.2 do plano anterior, que estava errado:** *"implementar escrita
content-addressed"* era desnecessário — **ela já existe**. O que faltava era parar de mudar os bytes
sem mudança de conteúdo.

**A correção, portanto, é uma só:**

| campo | hoje | passa a ser |
|---|---|---|
| `datePublished` / `approved_at` | `time.Now()` a cada republicação | **data da primeira publicação**, imutável (`first_published_at`) |
| `dateModified` / `lastmod` | já vem de `content_revised_at` — **e já está correto** | mantido; vira a única fonte de "quando mudou" |
| `checked_at` | cópia de `reviewedAt` = `time.Now()` | **ledger de verificação real**, por URL; ausente ⇒ campo não emitido |
| `reviewedAt` | `time.Now()` no silêncio | data da revisão real; sem revisão nova, **não muda** |

**Efeito em cadeia, todos verificáveis por medição:** os bytes param de mudar → `grava` para de
reescrever → mtime preserva → ETag estabiliza → **304 volta a funcionar** → `lastmod` fica coerente
com o HTTP → `dateModified ≥ datePublished` fica correto → e o campo para de mentir sobre
verificação. **Uma correção, quatro defeitos.**

**Risco medido: baixo** (verificação em §1.2). O único cuidado é que `-published-at`/`-reviewed-at`
continuem aceitando valor explícito, para o operador manter uma onda coesa — muda-se o **default**,
não a capacidade.

### Fase 0 — Consertar os sinais (bloqueia tudo o mais)

Nada de conteúdo novo antes disto. Amplificar sinal quebrado é piorar o problema — e o item **0.1**
resolve um defeito ético que não pode continuar no ar.

| # | Passo | O que resolve |
|---|---|---|
| 0.0 | Commit do plano + `docs/data-sources/FONTES_DIARIAS.md` + tasklist + fiscal `notify-owner` | meta-exigências (§11) |
| **0.0-P0** | **As 2.778 URLs que o Googlebot nunca pediu** (72 % de cobertura, descoberta parada desde 12/08 — §1.0, já investigado e decidido). Priorizá-las na malha de links internos, no sitemap e no IndexNow. **Conteúdo novo não resolve isto sozinho** | **§1.0 — o segundo defeito** |
| **0.1** | **A CORREÇÃO-MÃE: datas derivam do conteúdo, não do relógio.** Alvo real: **`internal/v2publish/v2publish.go:251`** (`CheckedAt: reviewedAt`), que alimenta o manifesto público. *(`cmd/publish-v2-direct/main.go:2621` é `writeRehearsal` — grava só o ensaio transacional; corrigir lá não tocaria os 23.759 valores.)* Ver §12.0 | **§1.2 inteiro — anti-fraude P0** |
| **0.2** | Medir o efeito de 0.1: republicar sem mudança de conteúdo deve dar **`e.iguais` ≈ 9.710, `e.mudaram` ≈ 0**, mtime preservado e `If-None-Match` → **304**. *(O item anterior — "implementar escrita content-addressed" — foi **EXCLUÍDO**: `grava` (`main.go:2012`) já compara bytes e `gravaDatado` (`main.go:2168`) já carimba mtime pela data editorial. Era retrabalho.)* | prova de que o 304 voltou |
| **0.3** | Gate `check-sitemap-lastmod-veracity` — compara cada `lastmod` com o hash do conteúdo no `published_manifest` e reprova na divergência. **Defesa secundária**, não a correção | impede regressão de §1.2(a) |
| **0.4** | Gate `check-source-verification-evidence` + invariante testada `dateModified ≥ datePublished` | defesa secundária de §1.2(c) e (d) |
| **0.5** | Campo imutável `first_published_at` no manifesto | **§1.2(e) — destrava a métrica** |
| **0.6** | `tools/measure-time-to-first-crawl` + `check crawl-edge-origin-reconciliation` + cobertura por prefixo de rota | **§10.1 — mede o antes** |
| 0.7 | `WIKI_ACCESS_LOG_DIR` + campo `instance` no `accessEntry` | destrava o ensaio (§8) |
| **0.8** | **Corrigir `.claude/skills/medir-bots/SKILL.md:7-16`** — separar ledger cumulativo (borda → dedup) de incremental (origem → soma). A regra atual induziu erro de **38×** nesta sessão | §1 — armadilha de leitura |
| 0.9 | Cobrir os **22 agentes hoje não verificáveis** (sem faixa de IP nem rDNS), incluindo `duckassistbot` — que o próprio `botagents.py` chama de sinal de citação mais direto | §1 item 5 |
| 0.10 | Corrigir os **301 servidos a bot** (15 de 68 requisições do Bingbot, 22 %) — orçamento de rastreio desperdiçado em redirect | §1 — buraco do Bingbot |
| 0.11 | **Reader canônico da série de origem** — `tools/check-origin-bot-traffic-series` que **soma** por `(date, agent_key)`, com teste que **reprova** a leitura "última linha". O produtor já documenta a regra (`tools/generate-bot-traffic-origin:70-85`) e **nenhum leitor a implementa** — foi essa lacuna que produziu o erro de 38× | §1 — causa-raiz |
| 0.12 | **Neutralizar e classificar o scanner** — 2 IPs (`35.204.225.70`, `34.53.233.72`) responderam por **662 das 667** requisições forjadas, rodando **7 UAs de bot de IA diferentes**. Alvos incluem **credenciais de ferramentas de IA**: `/.claude/settings.json`, `/.claude.json`, `/.codex/config.toml`, `/.anthropic/config.json`, `/.cursor/mcp.json`, `/.continue/config.json`, além de SSRF a metadata GCP e injeção de comando. **Nada vazou** (651 de 667 → 404; as 17 respostas 200 são a home com query, 7.395 B, e `/openapi.json`, público legítimo). Ações: (a) classificar por IP e excluir da série de bot; (b) propagar a evidência de IP **entre agentes** — hoje 97 requisições `amzn-searchbot` dos **mesmos IPs provados** caem em `unverifiable` em vez de `forged`; (c) hardening: garantir 404 para todo caminho de credencial | §1 item 4 |
| 0.12-bis | **Retenção e enxugamento do rollback** — snapshot incremental + retenção + compressão (§10.2 item 9-bis). **Higiene recomendada, NÃO bloqueia a cadência diária** (o dono fará limpeza de disco à parte); entra por ser desperdício de 200× sobre o conteúdo protegido, não por falta de espaço | eficiência, não bloqueio |
| 0.13 | **Congelar faixa de IP por data** — 3 requisições reais de ChatGPT-User (que pediram `/sumulas/stf-810/`, `/bancario/simulacao-credito-…/`) foram gravadas como autênticas, mas a OpenAI **retirou 40 prefixos** (244→204) e uma re-execução hoje as marcaria **forjadas**. Precisão atual medida: **99,25 %** — o problema não é acurácia, é **reprodutibilidade** | §1 item 5 |

### ★ Regra que vale para toda a execução — **ZERO STUB** (ordem do dono, 2026-08-20)

**Proibido stub, placeholder, mock, `noop`, `TODO` ou "implementação parcial para depois".** Cada
item deste plano entrega **código real, arquivo real, dado real, rodando e medido**:

- coletor entregue = coletor que **buscou de verdade** e gravou JSONL com proveniência (URL, data,
  hash, status), com o comando reprodutível registrado;
- gate entregue = `case` em `internal/checks/checks.go` + implementação + `_test.go` que passa +
  **teste de falso positivo sobre amostra real**;
- rota entregue = URL que responde **200 com conteúdo real**, com HTML, entrada no sitemap e linha
  no `published_manifest`, SHA-256 batendo;
- página entregue = texto autoral real, com fonte oficial verificada **de fato** (nada de
  `checked_at` sem evidência — foi exatamente esse o defeito achado em §1.2(d)).

O que não puder ser implementado de verdade **não é declarado pronto**: é reportado como pendente,
com a razão medida. **Mas pendência não é adiamento** — bloqueador se resolve nesta sessão, e o
produto sai completo.

### ★ Falta de contexto NUNCA trava o plano — lança-se especialista (ordem do dono, 2026-08-20)

Quando faltar informação para decidir — formato de uma API, comportamento de um gate, causa de um
defeito, alternativa a uma dependência —, a resposta é **lançar agente engenheiro para investigar**,
nunca parar. Esta sessão já provou o método: **26 agentes em 3 ondas** produziram a matriz de fontes
medida, o mapa do repositório e o diagnóstico de descoberta; e **duas críticas adversariais**
(Fable e Opus 5) derrubaram **seis** conclusões minhas que teriam ido para a execução como verdade —
inclusive a tabela de bots inteira, medida com o instrumento errado.

Regra operacional durante a execução:

- **dúvida factual** → agente investigador com escopo fechado e exigência de evidência reproduzível;
- **decisão cara de reverter** (gate, política, publicação, produção) → **crítico adversarial antes
  de aplicar**, com pedido explícito de refutação;
- **resultado de agente é alegação** até verificação própria no disco — foi assim que apanhei o
  alvo errado do `checked_at` e o item 0.2 redundante;
- **nunca** usar "falta contexto", "é de outra frente" ou "precisa de decisão do dono" como razão
  para não avançar: se há rota segura de engenharia, ela é tomada.

### Fase 1 — Habilitar conteúdo derivado

| # | Passo | Depende de |
|---|---|---|
| 1.1 | DEC-032 + emenda `CLAUDE.md:173` / `CONTENT_QUALITY.md:69`, com a base legal **por fonte** (§3.0) | 0.0 |
| 1.2 | `internal/sourcecollect` (robots, rate, GET condicional, remendo TLS por host, ledger) + testes | 1.1 |
| 1.3 | Segmentador jurídico + sumarizador extrativo + detector de truncamento. **Inclui baixar e converter o modelo `.m2v`**; se o conversor de subtoken não fechar, TextRank/tldr entra no lugar — em nenhum cenário a Fase 2 fica sem sumarizador (§5) | 1.2 |
| **1.5** | **`check-legal-citation-attribution`** — valida cada citação contra a fonte coletada. **8 % × 15 páginas/dia = 1–1,6 citações erradas/dia assinadas por OAB.** Sem ele passando, a publicação diária não começa | 1.2 |
| **1.6** | **`check-pii-anonymization`** + anonimizador medido, com teste de falso negativo sobre amostra real de diário. Enquanto não passar, os diários (F6/F7/F9) não entram | 1.2 |
| **1.7** | **Via de retirada (supersessão)** ligada ao pipeline diário — §10.2 item 10. Publicar sem freio é publicar errado | 1.1 |
| **1.8** | **`--since` seguro** — corpus completo no manifesto, delta só na escrita e na notificação (§7, item 6), com teste de que o servidor sobe | 0.1 |
| 1.4 | Ponte de `page_type` + lane `derivada_de_fonte_oficial` + 5 gates (§6) | 1.1 |

### Fase 2 — Coletar e publicar

| # | Passo | Depende de |
|---|---|---|
| 2.1 | Coletores das fontes 🟢: F1 Informativo STF · F2 STJ CKAN · F3 feeds STJ · F4 normas.leg.br | 1.2 |
| 2.2 | Ensaio na porta **8090** com `WIKI_CACHE_DIR` e `WIKI_ACCESS_LOG_DIR` isolados; smoke por socket real | 0.7, 1.4, 2.1 |
| 2.3 | Frescor: feed por seção, news sitemap, RSS servido, purga por tag, IndexNow no publish, JSON-LD `NewsArticle` | 2.2 |
| 2.4 | Publicação incremental (`--since`) + primeira onda real, no volume fixado em §12.1 | 2.3 |
| 2.5 | Agendamento: `wikijuridica-daily-content.timer` + `OnFailure=` + auditor independente | 2.4 |

### Fase 3 — Ampliar (nada é descartado, e nada é "depois")

> **As fases são ordem de DEPENDÊNCIA, não cronograma.** Tudo aqui é desta sessão. "Fase 3" quer
> dizer *"roda depois que a Fase 2 provou o pipeline"*, não *"fica para outro dia"*.

| # | Passo |
|---|---|
| 3.1 | F5 súmulas STF · F6 diários estaduais (5 UFs com API) · F7 Querido Diário · F8 Sigpub |
| 3.2 | F9 DOU (regra dos três degraus) · TST via backend REST · notícias com regra de licença |
| 3.3 | 22 UFs sem API (scraper por UF) · parecer sobre DataJud 3.3/3.8 para uso estatístico |
| 3.4 | Frente de **descoberta e diagnóstico** — detalhada abaixo |
| **3.5** | **Fechar os bugs pré-existentes remanescentes** do catálogo §3.10: **B9** (publicar o RSS que já existe e ninguém serve) · **B10** (`crawleridentity` Googlebot-only e não importado pelo `httpserver`) · **B13** (evidência de IP não se propaga entre agentes) · **B14** (faixas upstream defasadas + 22 agentes sem verificação) · **B15** (retenção de rollback) · **B16** (301 servidos ao Bingbot). **Nenhum vira backlog** |
| **3.6** | **Publicar a evidência desta investigação no repo**: `docs/data-sources/FONTES_DIARIAS.md` com a matriz medida (§3), o catálogo de armadilhas (§3.9) e o de bugs (§3.10). Os dossiês dos 26 agentes são **dado pago** — morrem no transcript se não forem versionados |

### 3.4 Descoberta e diagnóstico — o que conteúdo diário sozinho não resolve

Três buracos medidos, com o que a engenharia pode fazer **sem depender de cadastro**:

| buraco medido | fato | ação de engenharia |
|---|---|---|
| **Não sabemos o status de INDEXAÇÃO** — só o de rastreio | propriedade do Search Console **já verificada por DNS desde 2026-08-06** (`google-site-verification=Aguiea5gh…` no TXT) | **`internal/gsc`**: cliente Go da Search Console API (`auth/webmasters.readonly`). Cotas oficiais: URL Inspection **2.000/dia, 600/min**; Search Analytics 1.200/min. Sem isso, "por que não indexa" é opinião |
| **Bingbot cobriu 83 de 9.926 (0,8 %)** e a propriedade Bing **não existe** (`dig TXT` sem `msvalidate`, sem `BingSiteAuth.xml`) | IndexNow **já funciona** (200/202 com posse comprovada), mas **não alcança o Google** — participantes são Amazon, Bing, Naver, Seznam, Yandex, Yep | verificar propriedade Bing por arquivo próprio no repo (é engenharia local, não cadastro em terceiro). Atenção: **SOAP/POX do Bing são aposentados em 31/08/2026** — se houver cliente, nasce REST |
| **PerplexityBot: 0 URLs do acervo** | nunca engajou; e a faixa de IP dele é a mais defasada (`creation_time_upstream: 2025-02-07`, 8 prefixos `/32`) | descoberta externa (links entrantes) — a doc oficial do Google diz que *"a vasta maioria das páginas novas é achada por links"*. Frente própria, não resolvida por frescor |

**O que NÃO adianta fazer** (medido, para não gastar esforço à toa):

- **Google Indexing API** — a doc oficial (2026-07-16) restringe a `JobPosting` e `BroadcastEvent`
  em `VideoObject`. Conteúdo jurídico **não se enquadra**; é inutilizável, independe de credencial.
- **Sitemap ping ao Google** — descontinuado em jun/2023, responde 404 por design.
- **Re-submeter a mesma URL** — a doc diz que *"pedir recrawl várias vezes para a mesma URL não a
  faz ser rastreada mais rápido"*.
- **Tratar 200 do IndexNow como prova de rastreio** — a doc é explícita: *"o código 200 indica
  apenas que o buscador recebeu sua URL"*.

### 12.1 Volume diário — número fixado, com o critério

**Dois tetos governam, e vale o menor:** (a) o que a fonte oficial realmente produz; (b) o que passa
nos gates com comentário autoral real e citação verificada.

> **Correção da versão anterior, apontada pela crítica adversarial.** Eu havia usado um terceiro
> teto — "absorção do crawler" (ClaudeBot ~24 páginas/dia). Era **erro de categoria**: esse número
> descreve a velocidade com que ele consome o **acervo existente**, não um orçamento que páginas
> novas gastem — o bot escolhe o que pede. Além disso vinha do instrumento errado (origem). O
> argumento foi **removido**, não maquiado.

| seção | fonte e volume medido | **dia útil** | **fim de semana / feriado** |
|---|---|---|---|
| Jurisprudência | Informativo STF **1,2/dia útil** + STJ teses **0,75/dia** + feeds STJ | 2–4 | 0–1 (feeds ainda publicam) |
| Súmulas | STF **736 + 63 vinculantes**; STJ acervo | 2 | 2 (acervo finito, independe de fonte nova) |
| Legislação | `normas.leg.br` **1,3–2,25 normas/dia** | 1–3 | 0 (não há sanção) |
| Notícias | 8 feeds somam **30–40 itens/dia** | 3–5 | 1–2 (volume cai, não zera) |
| Diários | 5 UFs com API (**7 edições/dia útil**) | 5 | **0 — não circulam** |
| **total** | | **13–19** | **3–5** |

**Piso de fim de semana explícito:** DOU e diários **não publicam** sábado, domingo nem feriado, e
legislação idem. Em ~30 % dos dias o teto real é **3–5 páginas**, sustentadas por súmulas (acervo
finito, sempre disponível) e notícias. **Projeção honesta:** ~**310–400** páginas em 30 dias
(não 450), ~**3.800–4.900** em um ano (não 5.500) — calculada com ~21 dias úteis/mês.

**O número é teto, não meta.** Dia em que a fonte não produzir, publica-se menos — e o dia de
súmulas existe justamente para o acervo não depender de fonte diária. **Inventar volume para bater
meta seria a fraude que o contrato proíbe.**

**Re-medição obrigatória:** baseline de cobertura (§1) refeita em D+7 e D+30, por
`cumulative_sitemap_coverage` e `time-to-first-crawl` — nunca por requisições/dia. Se a cobertura
do acervo antigo **cair**, o volume diário é reduzido: o teto (b) foi excedido.

---

*Seções ⏳ serão completadas com os dossiês em curso (STF, DataJud, TST/TSE, notícias, OSS de
sumarização, frescor para bots, concorrência) e com a crítica adversarial Fable, antes do
`ExitPlanMode`.*
