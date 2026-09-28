# REFUTAÇÃO ADVERSARIAL — RUNBOOK P-1 / P0 / P1b

Medido 2026-09-16 01:00–01:20Z (2026-09-15 22:00–22:20 -03). HEAD `62d71de0`. Índice vazio. loadavg 7.46.
Todas as medições abaixo são minhas, executadas neste repositório, read-only.

## VEREDITO: OPERAVEL_COM_EMENDA — mas com uma falha que faz o bloco *declarar sucesso sem ter corrigido a superfície que o §12 chama de produto*.

---

## O QUE EU CONFIRMEI DO RUNBOOK (refutação tentada e falhada)

| afirmação do runbook | minha medição | veredito |
|---|---|---|
| 11.106 rotas no manifesto | 11.106 | ✓ |
| 944 com `approved_at == 2026-09-15` | 944 | ✓ |
| 942 com `dateModified < datePublished` no HTML servido, 0 sem JSON-LD | 942, 0 sem JSON-LD | ✓ |
| canais 875 /jurisprudencia/ · 38 /leis/ · 29 /sumulas/ | idêntico | ✓ |
| 0 de 944 presentes em `first_published_at.json` | 0 | ✓ |
| `first_published_at.json` 10.107 chaves, max 2026-08-27, mtime 2026-08-28 17:26 | idêntico | ✓ |
| 50 commits do manifesto, 2026-06-09..2026-09-10, último `315ac61b` | idêntico | ✓ |
| ledger 11.116 linhas; fórmula `29055289b861d603…` | idêntico | ✓ |
| `LOTE_MINIMO = 50` (`:115`); flags `--ressemear/--purge-targets/--dry-run` existem | idêntico | ✓ |
| `.gitignore:3:/public/` | idêntico | ✓ |
| CLAUDE.md linha **128**, regex de `check-contrato-vs-medicao:53`, `EXIT=0` com 11.106/11.039 | idêntico | ✓ |
| **regra C' produz `09-02:2 · 09-05:4 · 09-10:894 · 09-12:42 · 09-15:2`** | **idêntico, ao número** | ✓ |
| regra C' zera os impossíveis | 0 de 11.106 | ✓ |
| ensaio sem `-allow-public-write` não escreve byte (`main.go:853`, `:3036`, `:3692`) | confirmado por leitura | ✓ |
| `--limit` + `-allow-public-write` é recusado (`:351-358`) | confirmado | ✓ |
| NameError de `purge-edge-cache` no caminho de SUCESSO (`:191-196` × `:249`) | confirmado por leitura | ✓ |
| `purge-origin-cache --seco --rota`, `sweep --seco`, `reload-wiki-server --check`, `warm-edge-cache --de-arquivo/--rps/--concorrencia`, `generate-first-published-at --dry-run/--saida` | todas existem | ✓ |
| borda AGORA: `HIT`, `datePublished 2026-09-15`/`dateModified 2026-09-05`, `s-maxage=604800` | `HIT`, age **31303**, idêntico | ✓ |

**Refutei duas hipóteses minhas antes de reportá-las**: (a) que `--tag area-jurisprudencia` fosse no-op — o `ops/nginx/wikijuridica.conf` do repo NÃO tem `jurisprudencia` no `$wj_area_tag`, mas o nginx **vivo** é `-c ops/nginx/standalone/nginx.conf` (pid 2556682), que tem, e a origem emite `Cache-Tag: wj-acervo,area-jurisprudencia` (medido); (b) que a distribuição `09-10:894` estivesse errada — ela é a saída de C', não o `dateModified` cru, e bate exatamente.

---

## ATAQUE 1 — [QUEBRA A CORREÇÃO NO CANAL DE MÁQUINA] O gate I-1 é cego para 3 dos 4 canais e para a variante `Accept`. O bloco termina VERDE com o defeito vivo na superfície AI-first.

**Medido agora, três objetos de cache distintos na MESMA rota:**

| objeto | cf-cache-status | age | data que serve |
|---|---|---:|---|
| `https://…/jurisprudencia/stf-adi-4376/` (HTML) | HIT | 31303 | `datePublished 2026-09-15` |
| a MESMA URL com `Accept: text/markdown` (`vary: Accept-Encoding, Accept`) | **HIT** | **30363** | **`date_published: "2026-09-11"`** |
| `https://…/jurisprudencia/stf-adi-4376/index.md` | **MISS** | — | **`date_published: "2026-09-11"`** |

E na origem: `:8089` (Go) serve **`2026-09-15`**; `:8088` (nginx `wj_dyn`) serve **`2026-09-11`**.
Amostra por *stride* determinístico (passo 37 sobre as 944): **25 de 25** gêmeas `.md` na ORIGEM divergem do disco.

Ou seja: `09-11 > 09-05` — o canal de máquina tem a **sua própria** cronologia impossível, com uma data **diferente** da do HTML, e o runbook nunca a mediu. `check-cronologia-jsonld`, como especificado (lê `public/**/index.html` + amostra da BORDA em HTML), dará **EXIT=0** depois do passo 8 enquanto MCP/A2A/`/api/v1`/gêmea seguem servindo 2026-09-11 por até 7 dias.

**Emenda mínima:** a 2ª perna do I-1 mede as QUATRO serializações do mesmo objeto — `GET /rota/index.md`, `GET /rota/` com `Accept: text/markdown`, e `GET /api/v1/citar/rota/` — comparando `date_published` com o `datePublished` do disco; e o passo 13 acrescenta à lista de alvos a variante negociada (ou o passo 14 passa `--markdown` ao aquecedor, que existe exatamente porque é "outro objeto de cache por causa do vary.accept", `warm-edge-cache:593-595`).

---

## ATAQUE 2 — [ORDEM, e é a ordem que o próprio runbook diz não violar] O passo 8 purga a BORDA antes de recarregar o Go e antes de qualquer purga de ORIGEM.

`cmd/publish-v2-direct/main.go:2229` chama `purgarAcervoReescrito` (purga de borda) e só em `:2257` chama `recarregarServidor`. O runbook não menciona nem uma nem outra, e **nunca cita a flag `-skip-edge-purge` (`main.go:187`)**.

Com a origem comprovadamente suja (medição do ataque 1), purgar a borda antes de invalidar `wj_dyn` é literalmente o precedente de 2026-09-05 que o runbook cita como fundamento do seu passo 12: a primeira requisição repopula o Tiered Cache com o conteúdo VELHO. Os passos 12 e 13 chegam **depois**.

**Emenda mínima:** passo 8 roda com `-skip-edge-purge`; a ordem passa a 8 → 11 (reload) → 12 (origem, lista completa) → 13 (borda). Alternativa: purgar a origem ANTES do passo 8.

---

## ATAQUE 3 — [PURGA / SEO] O passo 8 esfria 627 páginas que ninguém reaquece.

`main.go:2290` `const limiarDeTag = 30`; `:2296` promove a área inteira a `--tag` quando ≥ 30 rotas mudaram.
Medido no manifesto: `/jurisprudencia/` **1.134** páginas (875 mudam), `/leis/` **406** (38 mudam), `/sumulas/` **329** (29 mudam → fica por URL).
⇒ o passo 8 purga `area-jurisprudencia` + `area-leis` = **1.540** objetos, mais hub e fatias de paginação, quando 913 bastavam. **1.134−875 + 406−38 = 627 páginas ficam frias e NÃO estão em `/tmp/p1b-alvos.txt`.** O timer de aquecimento só passa 04:20 e 16:20 UTC.

O runbook declara "custo colateral: **0 rotas rebaixadas** (MEDIDO)" — verdadeiro sobre o ledger (instante→dia), e silencioso sobre a borda.

**Emenda mínima:** `-skip-edge-purge` (ataque 2) resolve os dois de uma vez; se mantiver a purga interna, acrescentar as 627 ao arquivo de aquecimento.

---

## ATAQUE 4 — [NÚMERO ERRADO QUE ESCONDE A PRÓPRIA FALHA] "regra A deixa 900 de 944 impossíveis" — medido: **44**.

Reconstruí a estreia com o algoritmo de `generate-first-published-at:51-64,132-136` (50 commits, `setdefault`, data do commit):
`estreia_git das 944 = {2026-09-05: 6, 2026-09-10: 894}` → **900 têm estreia, 44 não têm**.
Impossíveis sob regra A (estreia pura, o que o gerador faz hoje, depois do passo 4): **44 de 944** — e **69 de 11.106** no acervo inteiro, com **67** caindo em dia 1. Sob C': **0** impossíveis.

O 900 do runbook é a contagem de rotas *que têm estreia*, rotulada como *ainda impossíveis*. Por que isso quebra: o passo 5 manda abortar comparando com 900. Se o `--piso-por-conteudo` for aplicado e falhar em silêncio (bug no patch), o operador vê **44**, não acha o 900, e conclui que o piso funcionou — **o número esperado esconde exatamente o modo de falha que ele deveria pegar**.

**Emenda mínima:** trocar a régua por invariante, não por magnitude: `rotas com estreia > dateModified == 0`. E corrigir os números: A = 44 de 944 / 69 de 11.106; "44 rotas sem histórico" é **67** no acervo (44 dentro das 944).

---

## ATAQUE 5 — [DANO IRREVERSÍVEL DE METADADO] C' carimba estreia 2026-09-15 em 3 páginas que estrearam em 2026-09-14, e `setdefault` torna isso permanente.

Medido: sob C', **5** rotas ficam com estreia 2026-09-15 —
`/noticias/stf-20260914/`, `/noticias/stj-20260914/`, `/noticias/tst-20260914/` (as três com `approved_at = 2026-09-14`), mais as 2 legítimas `stj-20260915` e `tst-20260915`.

O runbook mediu só dentro das 944 e escreve "`09-15:2` (as 2 legítimas)". As outras 3 estão **fora** das 944 e recebem data de estreia falsa. `generate-first-published-at` é `carrega_existente` + `primeira.setdefault(uid, data)` (`:139`) e o próprio docstring promete "uma entrada já registrada nunca é reescrita" — **a data errada nunca mais sai**.

**Emenda mínima:** piso = `min(estreia_git, approved_at_do_manifesto, dateModified_servido)`. Medido: põe as 3 em 2026-09-14 e deixa só as 2 genuínas em 09-15. O `approved_at` das 942 corrompidas é 09-15 (o maior dos três), então ele nunca baixa nada indevidamente.

---

## ATAQUE 6 — [PRÉ-CONDIÇÃO FALSA] PC-1: a publicação **NÃO** renova a carência. A janela de boot travado às 07:50Z continua aberta, e o runbook manda não fazer nada.

Medido `date -u` = 2026-09-16 01:13Z. `sweep --seco`: `pages-0094.xml`/`pages-0095.xml` **em carência, vencem 2026-09-16 07:50Z**; `6 shard(s) fora do indice | 0 vencido(s) | 2 vencendo em menos de 48h`.

Por código: `cmd/publish-v2-direct/main.go:1206-1235` remove shard órfão em três saídas — **carência VENCIDA**, marca corrompida, ou perdeu todas as URLs. Às 01:13Z nenhuma se aplica: o ramo é `orfaosEmCarencia++`, não `remover`. E `tools/sweep-sitemap-carencia-expirada:249,262` também só remove o que **já venceu**. `conciliaRegistryDeShard` só chama `ExpireRetired(agora, Period)`, que nada tomba antes do vencimento.
Às 07:50Z: `sitemapgrace.ValidRetirement` passa a falso → `publishedmanifest.go:510-513` cai em `is not listed in public/sitemap.xml` → **o boot do Go falha**. A varredura agendada é 08:19Z, **29 min depois**, e `OnFailure` é vazio com `StartLimitIntervalUSec=0`: o laço é mudo.

O passo 9 espera `0 vencendo em menos de 48h` — **inalcançável hoje**; e o "SE NÃO VIER: rodar sem `--seco`" não faz nada (nada venceu). O runbook diz "resolve PC-1 de graça". Não resolve.

**Emenda mínima:** PC-1 deixa de ser "de graça" e vira restrição escrita: **nenhum restart do Go entre 07:50Z e a varredura**; e o conserto é a varredura rodar antes do vencimento (mover o timer para ~07:45Z), não depois.

---

## ATAQUE 7 — [MEDIÇÃO IMPOSSÍVEL] O DEPOIS do passo 12 procura cabeçalho que o nginx vivo não emite.

Passo 12 manda `curl -D - … /index.md | grep -i 'x-cache\|age'` esperando `MISS`.
Dump completo dos cabeçalhos de `http://127.0.0.1:8088/jurisprudencia/stf-adi-4376/index.md` (medido): **não existe `X-Cache`, `X-Cache-Status` nem `Age`**. O grep volta vazio e o operador não distingue MISS de HIT.

**Emenda mínima:** provar por CORPO também na origem — comparar `date_published` de `:8088` com o de `:8089` —, a mesma regra que o runbook impõe, corretamente, para a borda.

---

## ATAQUE 8 — [A FERRAMENTA NÃO TEM O MODO QUE O PASSO EXIGE] 942 objetos de origem a invalidar; `purge-origin-cache` só aceita `--rota` uma a uma.

`tools/purge-origin-cache:102-104`: só `--rota` (repetível), `--gemeas-de-area`, `--seco`. **Não há `--de-arquivo`.** O passo 12 nomeia UMA rota de exemplo e diz "depois dirigido por rota", sem mecanismo. A necessidade medida é de ~942 (25/25 na amostra por stride).

**Emenda mínima:** acrescentar `--de-arquivo` ao `purge-origin-cache` no mesmo commit dos instrumentos (é o irmão exato do I-4), ou escrever no passo o laço real: `xargs -a /tmp/p1b-rotas.txt -n1 -I{} ./tools/purge-origin-cache --rota {}` — e conferir o exit de cada um.

---

## ATAQUE 9 — [O BUG DO PC-2 ESTÁ DENTRO DO CAMINHO CRÍTICO, a uma página de disparar]

O runbook classifica o NameError de `purge-edge-cache` como "fora do caminho critico daqui (usamos `--de-arquivo`)".
Medido: o passo 8 chama `purge-edge-cache` com `--tag area-jurisprudencia --tag area-leis --url ×29`. Existem 29 `--url` porque `/sumulas/` tem **29** rotas mudadas contra `limiarDeTag = 30`. Com 29 URLs, `caminhos` é não-vazio → `seletivo` verdadeiro → `alvos` atribuído → não estoura.
**Uma página a mais em /sumulas/ e os argumentos ficam só-tag**: `purga_total` falso, `len(alvos)` em `:249` sobre nome não atribuído → **NameError sobre uma purga que FOI ACEITA**; `publish-v2-direct:2231-2236` imprime "ATENÇÃO — purga do acervo falhou" e o operador, seguindo o passo 13, purga de novo e joga fora o aquecimento.

**Emenda mínima:** o I-4 (`alvos: list[str] = []` em `:191`) entra no passo 3, **antes** do passo 8, não como correção opcional de fim de sessão.

---

## ATAQUE 10 — [PURGA PARCIAL SEM RAMO DE TRATAMENTO] 1.884 URLs = 19 chamadas; uma falha deixa 18 purgadas e exit 1.

`tools/purge-edge-cache:94` `LOTE = 100`; o laço `:227-233` sobrescreve `status` a cada lote e marca `sucesso=False` em qualquer falha; `:236-246` grava **UMA** linha de ledger com o `http_status` do ÚLTIMO lote. O próprio docstring (`:28-33`) avisa "o ideal é um lote só por operação". O passo 13 não tem ramo para purga parcial, e a reação natural (repurgar) é o que o contrato diz jogar fora ~870 s de aquecimento.

**Emenda mínima:** fatiar a lista em arquivos de ≤100 linhas e purgar um por vez lendo o exit de cada, ou gravar uma linha de ledger por lote; e o "SE NÃO VIER" lê `data/ops/edge_cache_purge.jsonl` e repurga só o que faltou.

---

## ATAQUE 11 — [ROLLBACK IMPOSSÍVEL COMO ESCRITO] O passo 5 sobrescreve o arquivo antes do passo 6 preservá-lo.

Passo 5 = `generate-first-published-at --piso-por-conteudo` (grava) e commita. Passo 6 = copiar `data/editorial/first_published_at.json` para `$D/*.antes`. Na ordem do runbook, quando o passo 6 roda o arquivo **já é o novo** — o `.antes` é uma cópia do estado NOVO. O rollback declarado ("o anterior fica em `.agents/runtime/` (passo 6)") não existe. O `git show HEAD~1:` só funciona porque o passo 5 commitou; mas o próprio "SE NÃO VIER" do passo 5 manda **corrigir o gerador e re-rodar antes de commitar** — nesse ramo as 10.107 chaves originais desaparecem sem cópia, e `git reset/checkout/restore` é proibido.

**Emenda mínima:** mover a preservação do passo 6 para ANTES do passo 5 (é snapshot puro, cabe logo após o passo 3), ou rodar o ensaio com `--saida` num caminho de rascunho e só então gravar no lugar.

---

## ATAQUE 12 — [NÚMERO DERIVADO ERRADO, e é o motivo declarado de P0 vir antes de P6] A folga do gate sai do MEDIDO, não do DECLARADO.

`tools/check-contrato-vs-medicao:192`: `folga = max(200, int(publicadas * 0.05))` — `publicadas` é a **medição** do manifesto. Declarar 11.106 **não muda a folga**: ela já é 555 hoje (gate executado agora: 11.106 medidas / 11.039 declaradas / `EXIT=0`).
Tetos reais: com 11.039 declaradas o gate reprova quando `publicadas > 11.039/0,95` = **11.619**; com 11.106, **11.690**. O runbook afirma 11.594 → 11.661 e "devolve ~555 de margem ao publicador autônomo". O ganho real é **71 páginas**.
A ordem P0→P6 continua certa; a justificativa numérica, não.

---

## ATAQUE 13 — [SUPÕE SEM VERIFICAR] O gerador não tem `path`, e o piso precisa dele.

`tools/generate-first-published-at:76-89` (`intents_no_commit`) só rende `unique_intent_id`; o `path` do registro é descartado. O `--piso-por-conteudo` precisa ler `public/<rota>/index.html` — logo o patch tem de passar a render `(uid, path)`. Medido hoje: `intents no histórico git que não estão no worktree = 0`, então nenhuma rota supersedida sem HTML no disco — a falha é **latente**, não viva. Mas o runbook não escreve o fallback, e a regra segura é: HTML ausente ⇒ cai em `estreia_git`, **nunca** em hoje.

## ATAQUE 14 — [número esperado que muda depois do passo] Duas rotas servidas não têm linha no ledger.

Medido: `/noticias/stj-20260915/` e `/noticias/tst-20260915/` estão no manifesto (11.106) e **não** no `page_content_revision.jsonl` (11.116 linhas). O passo 6 espera `wc -l` = 11.116 (certo, ANTES). Depois do passo 14 (`--ressemear`) o ledger passa a 11.118 — correto, e o runbook não diz, então o operador pode ler como defeito.

---

## MEDIÇÕES PÓS-ADVISOR (fecham o que estava extrapolado)

**A) A gêmea e a variante `Accept` NÃO carregam `Cache-Tag`** (dump de cabeçalho na origem, ambas as formas). ⇒ a purga por tag do passo 8 evicta só HTML, cuja origem é o disco. **Ataque 2 rebaixado: ordem errada no código, inerte nesta passada.**

**B) O DESCRITOR E O DOCUMENTO DISCORDAM, medido agora, na mesma origem:**
| o que | sha256 do corpo `.md` |
|---|---|
| Go `:8089` | `b0ccb5c9ec443093951389823e44cd731ece764cb760265a73ef084162c5c1b8` |
| nginx `:8088` (gêmea servida) | `f4fe9c65040161dbb44562fd9743608447ae7a633b6d8e056bb34317192819f1` |
| `GET :8088/api/v1/citar/…` declara `markdown_sha256` | `b0ccb5c9…` (**fresco**) |

⇒ `/api/v1/*` está **fresco**; a gêmea está velha. Um agente que confira o `markdown_sha256` do descritor contra o documento que baixou recebe **mismatch**. O canal de máquina falha a própria verificação de integridade. **MCP e A2A: não medido.**

**C) `-skip-edge-purge` tem escopo MAIOR do que eu supus**: ela também desliga `:2154` (`artefatosDeDescobertaReescritos`) — sitemap/robots/llms/`security.txt`, cujo `Expires` muda a cada transação. E o help (`:188-190`) diz "usar só em ensaio local sem credencial; publicação real deve deixar a purga ligada". ⇒ **emenda do ataque 2/3 trocada**: manter a purga interna e (i) purgar a ORIGEM **antes** do passo 8, (ii) somar as 627 colaterais ao arquivo de aquecimento. Usar `-skip-edge-purge` em produção contraria o contrato da própria flag.

**D) `first_published_at.json` está LIMPO em HEAD** (`git status --porcelain` vazio; `git show HEAD:` devolve o documento). **Ataque 11 rebaixado**: o snapshot do passo 6 é inútil na ordem escrita (copia o estado NOVO como `.antes`), mas a recuperação existe por `git show HEAD:` — reordenar ainda assim.

**E) O piso correto NÃO é `min(git, approved_at, dateModified)`.** Controle medido sobre as 11.106: essa regra muda **55** rotas, e em `/diarios/` o `approved_at` é a data do DIÁRIO, não a da estreia (`/diarios/ba-20260827/`: estreia 08-29, approved 08-27) — ela **antecipa** estreia e reescreve entrada já gravada, violando a idempotência de `:139`.
**Regra medida que funciona — `approved_at` SÓ nas órfãs (sem entrada no arquivo e sem estreia no git), em vez da data do commit de hoje:**
`impossíveis 0` · `dia1 = 2`, e são exatamente `/noticias/stj-20260915/` e `/noticias/tst-20260915/` · difere de C' em **23** rotas (todas órfãs, nenhuma entrada existente tocada) · **distribuição nas 944 idêntica à que o runbook espera** (`09-02:2 · 09-05:4 · 09-10:894 · 09-12:42 · 09-15:2`). Custo zero no DEPOIS, e mata as 3 estreias falsas.

**F) `check-lastmod-causalidade --json` existe** (`:271`), junto de `--desde` e `--listar`. ✓

**G) `timeout 1800` do passo 8 é seguro** — refutei minha própria suspeita: `data/ops/daily_content_runs.jsonl` últimas 4 passadas = **1091, 576, 1044, 759 s** para a onda INTEIRA (coleta→publicação→aquecimento). 1800 s é ≥1,6× a onda completa.

**H) A hora do ataque 6 estava errada, e a janela é pior do que eu disse.** A varredura só remove o que **já venceu** (`:249,262`), então antecipá-la para 07:45Z é no-op: ela tem de correr **depois** de 07:50Z. E medido em `systemctl list-timers`:
- `wikijuridica-daily-content.timer` → próxima **2026-09-16 04:31:33 -03 = 07:31:33Z** — a onda diária começa **19 min antes** do vencimento e termina com `reload-wiki-server` (hoje o servidor entrou às 12:30:50 -03, 2 min depois de `pages.json` às 12:28:56);
- `wikijuridica-sitemap-shard-grace.timer` → **05:19:09 -03 = 08:19:09Z**;
- `wikijuridica-qualidade-diaria.timer` → **04:47:17 -03 = 07:47:17Z** (segura o flock heavy ~60 min).
⇒ Go **já rodando** sobrevive a 07:50Z; **restart** não. A onda das 07:31Z, com duração medida de 576–1091 s, tem probabilidade real de recarregar o servidor **depois** de 07:50Z, e a varredura só passa 08:19Z.

**I) `reload-wiki-server` amostra 6 rotas** (`data/ops/server_reload.jsonl`: `"amostradas": 6`). O runbook o vende como "auto-verificável por construção"; 6 de 11.106 não prova convergência — e hoje ele reportaria "sem divergência" (o `html_sha256` bate) enquanto 25 de 25 gêmeas amostradas na origem estão velhas.

## O QUE O ADVISOR MUDOU

Chamei uma vez, com o entregável já durável. **Nenhum fato que eu medi foi contrariado; ele corrigiu a LEITURA de dois números que eu medi bem e interpretei forte demais, e me mandou fechar três extrapolações.**

1. **Rebaixou o ataque 2** (ordem purga→reload). Mandou medir se a gêmea carrega `Cache-Tag`. Medi: **não carrega** (nem a variante `Accept`). Logo a purga interna toca só HTML, que sai do disco — a violação de ordem existe no código e **não tem vítima nesta passada**. Reclassifiquei, e passei a sustentar `-skip-edge-purge`... até ele me mandar ler o escopo da flag, e aí **troquei a emenda** (item C acima).
2. **Corrigiu a hora do ataque 6.** Eu propunha mover a varredura para ~07:45Z; ele apontou que ela só remove o **já vencido**, então 07:45Z é no-op. Fui medir os timers e achei algo pior do que eu tinha: a **onda diária começa 07:31Z**, 19 min antes do vencimento, e termina recarregando o servidor.
3. **Rebaixou o ataque 11** (rollback "impossível"). Mandou conferir o git: `first_published_at.json` está **limpo em HEAD**, então `git show HEAD:` recupera em qualquer ramo. Virou "snapshot inútil na ordem escrita", não "rollback impossível".
4. **Exigiu controle para a emenda do ataque 5.** Rodei `min(git, approved_at, dateModified)` sobre as 11.106: muda **55** rotas, e em `/diarios/` o `approved_at` é a data do diário — a emenda que eu ia propor **antecipava** estreia e reescrevia entrada já gravada. Substituí pela regra estreita (`approved_at` só nas órfãs), **medida**: 0 impossíveis, dia1 = as 2 legítimas, 23 rotas alteradas, DEPOIS do runbook intacto.
5. **Cobrou medição onde eu extrapolei no ataque 1.** Fui aos sha256: `/api/v1/citar` está **fresco** e a gêmea **velha** — mais forte do que eu havia escrito (descritor × documento discordam), e retirei `api/v1` da lista de canais velhos; MCP e A2A passaram a "não medido".
6. **Três verificações que eu não tinha feito:** `--json` de `check-lastmod-causalidade` (existe), o `timeout 1800` (refutei minha própria suspeita: onda inteira 576–1091 s), e o escopo de `-skip-edge-purge` (maior do que eu supunha — derrubou minha emenda original).

