# REDE SOCIAL DE IA — rascunho de escopo, partindo de medição

**Estatuto.** Este é o rascunho que o §P14 de `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`
mandou produzir *"para o próximo Claude Code já ter uma ideia"*, e que o dono liberou ao
aprovar o plano em **2026-09-16**. **Não é frente de execução**: nada aqui foi implementado,
nenhum arquivo de código, política ou configuração foi tocado, e o `cmd/social` não foi
reiniciado. O que se fez foi **colher dado e arquitetar no papel**.

**Visão declarada pelo dono, literal:** *"Wiki jurídica vai ter rede social para bots de IA,
altamente moderna, com advogados, leigos, juristas de diversas espécies, juízes, promotores,
premeditação, discussão de casos reais, comentários, refutação e o cérebro como moderador."*

**Medido em:** 2026-09-16, `HEAD` `215b0c54`, worktree com modificações não commitadas
(relevantes ao texto e nomeadas onde aparecem).

---

## 0. Como ler os números deste documento

Toda afirmação numérica leva a **camada** entre colchetes e o comando que a produziu.

| marca | o que é | autoridade |
|---|---|---|
| `[borda]` | Cloudflare GraphQL `httpRequestsAdaptiveGroups` | volume real; **amostrado** |
| `[origem]` | `data/ops/access/nginx-AAAA-MM-DD.jsonl` | exato, mas é **piso** onde a borda cacheia |
| `[disco]` | arquivo, banco ou código no repositório | exato, na data do arquivo |
| `[sonda]` | requisição própria com UA do portal e `X-Warming-Request: true` | estado servido agora |

**A regra 15 diz que a borda é a autoridade sobre volume — e este documento mede POR QUE, para
estas duas superfícies, a origem também é.** Ver §1.0. Estimativa aparece marcada como
estimativa. O que não foi medido está nomeado no §9, com o comando que o fecha.

**Ressalva permanente do conjunto amostrado, e qual dos dois números este documento reporta.**
`httpRequestsAdaptiveGroups` é amostrado pelo Cloudflare, e o repositório já separa duas
grandezas (`tools/edgetelemetry.py`, `ops/cloudflare/cache-reserve.json:55`):
**`requests_sampled` = Σ `count`** (o que a amostra viu) e
**`requests_estimated` = Σ (`count` × `sampleInterval`)** (a extrapolação).

**Todo `[borda]` deste documento é `requests_sampled`** — a soma crua de `count`, sem
extrapolar. A escolha não é conservadorismo cego: o `sampleInterval` observado ficou entre
**1,0 e 3,41**, e a reconciliação do §1.0 (15.707 na borda contra 15.708 na origem, **uma
requisição de diferença**) é ela própria a prova de que, para estes dois prefixos, o
`sampleInterval` é ≈1 na esmagadora maioria dos grupos — extrapolar aqui **afastaria** o número
da verdade em vez de aproximá-lo. A postura é a mesma de `tools/check-edge-traffic`: o conjunto
amostrado serve para **proporção e presença**, e a contagem exata vem do ledger de origem quando
as duas camadas reconciliam.

**Teto de grupos, conferido e não suposto:** o `limit` é **200 por chamada**, e as chamadas deste
documento devolveram, por dia, **109 e 109** grupos em `/redesocial/` e **23 e 23** em
`/api/v1/`. **Nenhuma chegou perto do teto**, portanto nenhuma cauda foi cortada em silêncio.

---

## 1. O que existe hoje, medido — e é bem mais do que o briefing supunha

### 1.0 A descoberta de método: para `/redesocial/` e `/api/v1/`, a origem NÃO é piso

Esta é a primeira coisa a estabelecer, porque sem ela todo número seguinte fica ambíguo.

```bash
# [borda] — 2026-09-14 e 2026-09-15 (UTC), uma chamada por dia (JANELA_MAXIMA_DIAS_FREE = 1)
python3 - <<'PY'
import sys, collections; sys.path.insert(0,'/opt/wiki/tools')
import cloudflare_auth as cf
zid,_ = cf.zona_id("wikijuridica.com.br")
Q = """query($zone:String!,$since:Time!,$until:Time!,$p:String!){
 viewer{zones(filter:{zoneTag:$zone}){
  httpRequestsAdaptiveGroups(limit:200,
   filter:{datetime_geq:$since,datetime_leq:$until,clientRequestPath_like:$p},
   orderBy:[count_DESC]){count avg{sampleInterval}
   dimensions{userAgent cacheStatus edgeResponseStatus clientRequestHTTPMethodName verifiedBotCategory}}}}}"""
for pref in ("/redesocial/%","/api/v1/%"):
    for dia in ("2026-09-14","2026-09-15"):
        d,e = cf.graphql(Q,{"zone":zid,"since":dia+"T00:00:00Z","until":dia+"T23:59:59Z","p":pref},
                         "leitura", proposito="medicao-de-borda")
        print(pref, dia, e or len(d["viewer"]["zones"][0]["httpRequestsAdaptiveGroups"]))
PY
```

*(O campo do método chama-se `clientRequestHTTPMethodName`, não `clientRequestHTTPMethod` — a
segunda forma devolve `unknown field` e a consulta inteira falha. Conferido por introspecção:
`__type(name:"ZoneHttpRequestsAdaptiveGroupsDimensions")`.)*

| superfície | `[borda]` 2 dias | `cacheStatus` | `[origem]` mesmos 2 dias | reconciliação |
|---|---|---|---|---|
| `/redesocial/` | **16.518** | `expired` 8.020 + `miss` 7.687 = **15.707 (95,1%)**; `hit` 249 (1,5%) | **15.708** | `expired+miss` bate com a origem **em 1 requisição** |
| `/api/v1/` | **1.265** | `dynamic` 1.263 (99,8%) | **1.262** | diferença de 3, dentro da amostragem |

**Conclusão de método, e ela vale para todo trabalho futuro nesta frente:** o acervo estático
sai da borda com `s-maxage=604800` e por isso a origem é piso; **`/redesocial/` e `/api/v1/`
são rota dinâmica e praticamente não cacheiam**, então aqui o ledger de origem é **exato**, não
piso. Isso é o que autoriza o resto deste documento a usar a série de 16 dias da origem —
janela que a borda do plano Free não alcança numa consulta.

A regra 15 continua íntegra: ela manda medir na borda **e** declarar a camada. O que se fez foi
medir na borda para **provar** qual camada tem autoridade aqui.

### 1.1 A rede social é 40,7% do tráfego de origem do portal

```bash
# [origem] 16 dias, 2026-09-01..2026-09-16, excluindo warming e bot_simulation
python3 -c "
import json,glob
t=s=0
for f in sorted(glob.glob('/opt/wiki/data/ops/access/nginx-2026-09-*.jsonl')):
    for ln in open(f,encoding='utf-8',errors='replace'):
        d=json.loads(ln)
        if d.get('warming') or d.get('bot_simulation'): continue
        t+=1; s+= (d.get('path','').startswith('/redesocial/'))
print(t, s, round(100*s/t,1))"
```

| medida `[origem]`, 16 dias | valor |
|---|---|
| requisições totais ao portal (sem sonda própria) | **219.468** |
| sob `/redesocial/` | **89.244 — 40,7% do portal inteiro** |
| dessas, com `agent_key` de agente de IA | **50.567 (56,7%)** |
| sob `/api/v1/` | **4.104 (1,9%)** |
| `/redesocial/tema/` sozinho | **87.563 — 98,1% de toda a rede social** |

**O dado que sustenta a ideia do dono continua de pé, e maior do que o briefing dizia:** não é
"um terço de um recorte", é **quase metade do tráfego de origem do portal inteiro** batendo
numa superfície social, com maioria absoluta de agente de IA declarado.

### 1.2 E as salas estão vazias — o banco, contado

`var/social/social.db`, **snapshot de 2026-09-11 04:05:37 -03:00** (mtime; os números abaixo são
dessa data, não de hoje).

```bash
for t in $(sqlite3 "file:/opt/wiki/var/social/social.db?mode=ro" ".tables" | tr -s ' ' '\n'); do
  echo "$(sqlite3 "file:/opt/wiki/var/social/social.db?mode=ro" "select count(*) from \"$t\";") $t"
done | sort -rn
```

| tabela | linhas `[disco]` |
|---|---|
| `temas` | **11.039** |
| `contas` · `perfis` | **1** · **1** |
| `duvidas` · `respostas` · `posts_blog` · `comentarios_de_post` | **0** · **0** · **0** · **0** |
| `comentarios_de_autoridade` · `fontes_do_comentario_de_autoridade` | **0** · **0** |
| `perfis_advogado` · `perfis_jurista` · `verificacoes_oab` · `revisores` | **0** · **0** · **0** · **0** |
| `fila_moderacao` · `trilha_moderacao` · `denuncias` · `recursos` · `decisoes` · `quarentena` | **0** em todas |
| `follows` · `reacoes` · `notificacoes` · `tokens_de_feed` | **0** em todas |
| `sigilo_casos` · `sigilo_cofres` · `sigilo_mensagens` · `sigilo_participantes` · `ordens_judiciais` | **0** em todas |

**A pilha de moderação inteira existe, com esquema completo, e nunca recebeu uma linha.** Isso
não é defeito: é a informação de projeto mais importante deste documento. A rede social de IA
**não precisa de esquema novo de moderação** — precisa de participante.

### 1.3 O que uma sala serve hoje, palavra por palavra

```bash
# [sonda] — UA próprio + X-Warming-Request, contra a origem
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  -H 'Host: wikijuridica.com.br' \
  http://127.0.0.1:8088/redesocial/tema/familia/abandono-afetivo-indenizacao/
```

**200, 2.991 bytes, 165 palavras visíveis.** O corpo diz, ao pé da letra:

> *"Ninguém perguntou nada sobre este tema até agora."*
> *"Ninguém abriu dúvida sobre este tema ainda."*

**87.563 requisições de agente em 16 dias `[origem]` para receber 165 palavras de "ninguém
perguntou nada", 11.039 vezes.** Este é o retrato honesto do produto hoje, e é o parâmetro
contra o qual qualquer proposta deste documento tem de se justificar.

### 1.4 A superfície de máquina da rede social já está construída E ANUNCIADA

```bash
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  -H 'Host: wikijuridica.com.br' http://127.0.0.1:8088/.well-known/ai-catalog.json
curl -s ... http://127.0.0.1:8088/.well-known/agent-card.json
curl -s ... http://127.0.0.1:8088/api/v1/redesocial/lote
curl -s ... http://127.0.0.1:8088/redesocial/index.md
```

`[sonda]`, todos 200:

- **`/.well-known/ai-catalog.json`** anuncia `urn:air:wikijuridica.com.br:api:redesocial-redesocial-lote`
  com as consultas representativas *"o que pessoas reais estão perguntando sobre direito de
  família"* e *"quero as dúvidas jurídicas já respondidas por advogado verificado"*.
- **`/.well-known/agent-card.json`** (A2A) anuncia a habilidade `consultar-rede-social` com
  quatro ações: `buscar_duvidas`, `ler_duvida`, `perfil_de_jurista`, `duvidas_do_tema`.
- **`/api/v1/redesocial/lote`** responde **`{"tipo":"fim","count":0,"bytes_markdown":0,…}`** —
  189 bytes, NDJSON, lote vazio.
- **`/redesocial/index.md`** serve 6.026 bytes de regras de moderação com fonte oficial e
  contagem lida do banco a cada requisição (*"Nenhuma denúncia foi registrada até agora"*).
- O host já se identifica como **`did:web:wikijuridica.com.br`** no `ai-catalog`.

**Prometemos a cada agente que passa uma rede social de dúvidas humanas respondidas por
advogado com inscrição verificada, e o endpoint devolve `count: 0`.** A distância entre o
anunciado e o existente está medida, e é o item nº 1 de qualquer execução futura.

### 1.5 DEFEITO ENCONTRADO NESTA MEDIÇÃO: a sala do tema fica atrás do acervo, e é o agente quem acha o buraco

Os 404 sob `/redesocial/` **não são agente chutando endereço**. Essa afirmação foi testada, não
suposta: classificou-se cada rota 404 contra o que `public/` serve hoje e contra o espelho de
temas.

```bash
python3 - <<'FIM'
import json,glob,sqlite3,os,collections
con=sqlite3.connect("file:/opt/wiki/var/social/social.db?mode=ro",uri=True)
temas={(c if c.endswith('/') else c+'/') for (c,) in con.execute("select caminho from temas")}
rot=collections.Counter()
for f in sorted(glob.glob('/opt/wiki/data/ops/access/nginx-2026-09-*.jsonl')):
    for ln in open(f,encoding='utf-8',errors='replace'):
        d=json.loads(ln)
        if d.get('warming') or d.get('bot_simulation'): continue
        p=d.get('path') or ''
        if p.startswith('/redesocial/tema/') and d.get('status')==404:
            rot[(p if p.endswith('/') else p+'/')[len('/redesocial/tema'):]]+=1
com_html=sum(1 for r in rot if os.path.exists('/opt/wiki/public'+r+'index.html'))
print("404:",sum(rot.values()), "rotas:",len(rot), "com HTML:",com_html,
      "ainda sem tema:",sum(1 for r in rot if r not in temas),
      "ja curadas:",sum(1 for r in rot if r in temas))
FIM
```

| `[origem]` 16 dias × `[disco]` | valor |
|---|---|
| 404 sob `/redesocial/` | **1.322** |
| rotas distintas pedidas | **877** |
| **dessas, com HTML em `public/` hoje** | **877 — 100,0%** |
| **rotas inventadas pelo agente** | **0** |
| rotas cujo tema **já existe hoje** (curadas por sincronização posterior) | **817 (93,2%)** |
| rotas **ainda sem tema** hoje | **60**, somando **161 requisições** |
| por agente | `gptbot` **867** · `perplexitybot` **378** · demais 77 |
| primeiro 404 por dia (rotas distintas) | **2026-09-10: 690** · 09-09: 127 · 09-11: 34 · 09-12: 12 · 09-14: 10 · 09-16: 3 |

**Os 93,2% que se curaram sozinhos são a prova do mecanismo, não um alívio:** a sala nasce depois
da página, o agente passa no meio, colhe 404, e a sincronização seguinte fecha o buraco. O pico
de **690 rotas com o primeiro 404 em 2026-09-10** é uma onda de publicação inteira sendo
rastreada antes de o espelho rodar.

**A prova de que a origem do pedido é nossa** — o HTML publicado de `/leis/cpc-art-536/` contém,
no bloco de relacionados:

```
<p><a href="/redesocial/tema/leis/cpc-art-536/">Página deste tema na rede social do portal</a></p>
```

E a sonda ao vivo devolve, hoje `[sonda]`:

```
/redesocial/tema/leis/cpc-art-536/          => 404
/leis/cpc-art-536/                          => 200
/redesocial/tema/jurisprudencia/stj-iac-1/  => 200   (uma das 817 já curadas)
```

*(comando: `curl -s -o /dev/null -w "%{http_code}\n" -A 'wikijuridica-superficie-probe/1.0'
-H 'X-Warming-Request: true' -H 'Host: wikijuridica.com.br' http://127.0.0.1:8088<rota>`)*

**A causa, com `arquivo:linha` — localizada, não suposta.** O espelho tem produtor único, e ele
está dentro do deploy:

| peça | onde |
|---|---|
| escrita da tabela | `internal/socialconteudo/temas.go:223` — `INSERT INTO temas … ON CONFLICT(area, slug) DO UPDATE`, dentro de uma transação |
| produtor | **`cmd/generate-social-temas`**, que espelha o **`published_manifest`** |
| disparo | **`tools/deploy-publico:714`** — `./tools/go-modern run ./cmd/generate-social-temas --aplicar` |
| gate | `tools/check-social-temas-espelhados` |
| falha do passo | **não é fatal**: `deploy-publico:719` apenas imprime a instrução de recuperação |

*(`grep -rn "INTO temas" --include=*.go internal/ cmd/` e
`grep -rn "EspelharTemas" --include=*.go cmd/ internal/`.)*

E o encaixe fecha exatamente:

| conjunto `[disco]` | valor |
|---|---|
| rotas servidas por `public/` (`find public -name index.html \| wc -l`) | **11.365** |
| `data/editorial/published_manifest.jsonl` | **11.114** |
| `temas` no `social.db` (snapshot 2026-09-11 04:05) | **11.039** |
| **no manifesto e sem tema** | **75** |
| **das 60 rotas ainda em 404, quantas estão no manifesto** | **60 de 60 — 100%** |

**Logo a causa é temporal, não estrutural:** as rotas ainda abertas **estão** no manifesto — o
produtor as criaria; ele apenas não rodou desde a última onda. Não é o caso de o espelho "não
conhecer" a rota, e por isso o conserto **não** exige reiniciar o `wikijuridica-social`: é rodar
o gerador e o gate que já existem.

*(O que **é** estrutural, e fica anotado porque muda o conserto: `public/` serve **251 rotas a
mais** que o manifesto, e o espelho nasce do manifesto — essas nunca ganhariam sala por este
caminho. Não foi medido se alguma é rota pública indexável ou apenas artefato auxiliar: §9,
item 11.)*

**O retrato de hoje, que é o que a frente seguinte vai encontrar:**

| medida `[disco]`, 2026-09-16 | valor |
|---|---|
| rotas servidas sem tema | **326** |
| dessas, cujo HTML **anuncia** o link morto | **71** |
| repartição das 71 | `/leis/` 34 · `/diarios/` 18 · `/noticias/` 15 · `/jurisprudencia/` 4 |
| as outras 255 | não emitem o bloco — institucionais (`/`, `/sobre/`, `/bot/`, `/termos/`…) e páginas cujo gerador não o incluiu (§9, item 9) |

**Por que isto importa para esta frente, e não é só um bug avulso:** é a **única evidência direta
que temos do que um agente pede e nós não servimos** — e a evidência é limpa, porque **877 de 877
pedidos correspondem a página real**. A demanda medida é por **uma sala de tema por dispositivo
legal, por notícia e por diário**, e vem dos dois maiores crawlers de IA do portal.

*(Este documento não corrige o defeito — o contrato desta frente é read-only. Fica nomeado aqui e
no §7.4 e §10 para a frente que o executar.)*

### 1.6 `gptbot` no ranking: o briefing está defasado, e é preciso dizer os dois estados

| onde | estado |
|---|---|
| `git show HEAD:cmd/cerebro/comentarios.go` | `agentesValiososParaRanking` **não** contém `gptbot` |
| worktree (`git diff --stat`: +36 −3, **não commitado**) | **contém**, com o comentário *"`gptbot` ENTROU EM 2026-09-16"* |

Ou seja: a premissa do briefing (*"o ranking é cego para o gptbot"*) é **verdadeira em `HEAD`**
e está sendo fechada por outra frente hoje mesmo. Antes de repetir a frase, confira:

```bash
git show HEAD:cmd/cerebro/comentarios.go | grep -n gptbot
```

**E os denominadores diferem — declare qual está usando.** O briefing diz *"28.036 de 83.810
(33,4%)"*; o comentário do código diz *"28.038 de 60.755 (46,1%)"* contando **só linhas com
`agent_key`**; esta medição, 16 dias `[origem]` com `/redesocial/` inteiro, dá **28.476 de
89.244 (31,9%)**. Os três são o mesmo fenômeno com recortes diferentes: janela, prefixo e se o
tráfego sem chave entra na conta. Nenhum está errado; citar um sem o denominador, sim.

**Ressalva que o próprio código escreve e que esta frente herda:** o GPTBot é o rastreador de
**coleta** da OpenAI; quem devolve citação é `oai-searchbot`/`chatgpt-user`. Contar GPTBot mede
interesse de coleta, não citação confirmada.

---

## 2. Pergunta 1 — qual API os agentes estão pedindo, e o quê exatamente

### 2.1 O que pedem em `/redesocial/`: leitura, e só leitura

| `[origem]`, 16 dias, `/redesocial/` | valor |
|---|---|
| método | **GET 89.244 · POST 0** |
| status | 200 **87.921** · 404 **1.322** · 301 1 |
| `agent_key` top | `gptbot` 28.476 · *(sem chave)* 27.173 · `amazonbot` 12.135 · `semrushbot` 10.359 · `perplexitybot` 7.009 · `oai-searchbot` 2.131 · `yandexbot` 692 · `applebot` 640 |

`[borda]`, os mesmos dois dias de §1.0, por `verifiedBotCategory` da Cloudflare:
**`AI Crawler` 6.879 (41,6%) · não classificado 7.629 (46,2%) · `Search Engine Crawler` 975 ·
`AI Search` 558 · `SEO` 477**. UA nº 1: **Amazonbot, 40,7%**.

**Em 16 dias, zero POST de agente para a rede social.** O lado "escrita" da rede social de IA é,
hoje, **inteiramente hipotético** — nenhum agente jamais tentou escrever. Quem quiser sustentar
o contrário tem de produzir a medição, porque esta diz o contrário.

### 2.2 O que pedem em `/api/v1/`: e o volume de POST é ataque, não demanda

Este número engana quem não abre, e por isso ele vem aberto.

| `[origem]`, 16 dias, `/api/v1/` | valor |
|---|---|
| total | 4.104 |
| método | POST 2.934 · GET 1.170 |
| status | **405: 2.035** · 204: 893 · 200: 688 · **413: 463** · 400: 15 · 404: 5 |

Aberto por rota — mesmo laço do §1.1, agrupando por
`('/'.join(path.split('/')[:4]), method, status)`:

| rota × método × status | n | o que é de verdade |
|---|---|---|
| `/api/v1/search?q=` **POST 405** | **2.034** | **varredura de injeção de SQL.** Os GETs do mesmo cliente são `?q= ORDER BY 1--`, `?q= UNION ALL SELECT NULL,…`. UA de navegador genérico, sem `agent_key`, 6 UAs rotativos. **Não é agente de IA pedindo escrita.** |
| `/api/v1/redesocial/csp-report` **POST 204** | **893** | relatório de CSP de **renderizadores**: `applebot` 642, `Baiduspider-render` 160, `cloudflare-ai-search` 55, `YandexRenderResourcesBot` 8 |
| `/api/v1/lote` GET 200 | 23 | ingestão em lote do acervo |
| `/api/v1/redesocial/lote` | 15 | o canal social, devolvendo `count: 0` |
| `/api/v1/citar` · `/api/v1/citacoes` GET 200 | 7 · 5 | citação verificável e guardrail |
| `/api/v1/redesocial/conta/cadastrar` POST | **3** | tentativa de criar conta, de UA Android — **as únicas tentativas de escrita social do período** |

**Correção obrigatória a uma leitura tentadora:** "2.035 requisições de escrita rejeitadas com
405" **não** é demanda reprimida de agentes. É `sqlmap`. Apresentá-la como demanda seria dado
falso, e este documento a desmonta antes que alguém a herde.

**O achado lateral que é real:** 893 relatórios de CSP significam que os renderizadores da
Apple, do Baidu, da Cloudflare e do Yandex **executam o nosso JavaScript** e nos reportam a
violação. Existe um canal de retorno automático de agente que já funciona — só não é sobre
conteúdo.

### 2.3 A classe que busca PARA RESPONDER nunca entrou na rede social

`data/ops/ai_citation_signal_daily.jsonl` separa quatro camadas. Somando 2026-09-01..09-16
`[disco]`:

| camada | requisições | agentes |
|---|---|---|
| `crawl` | 30.452 | `perplexitybot` 20.418 · `bingbot` 3.826 · `oai-searchbot` 3.604 · `yandexbot` 1.234 · `applebot` 926 · `googlebot` 422 |
| `treinamento` | 13.678 | `amazonbot` 13.605 · `meta-externalagent` 37 · `gptbot` 19 |
| **`fetch`** | **1.714** | **`chatgpt-user` 1.691 · `claude-user` 19 · `perplexity-user` 4** |
| `clique_de_volta` | 77 | `chatgpt` 39 · `copilot` 28 · `perplexity` 10 |

Cruzando a classe `fetch` com os dois prefixos `[origem]`, 16 dias:

```bash
python3 -c "
import json,glob,collections
F={'chatgpt-user','claude-user','perplexity-user'}; t=collections.Counter(); onde=collections.Counter()
for f in sorted(glob.glob('/opt/wiki/data/ops/access/nginx-2026-09-*.jsonl')):
  for ln in open(f,encoding='utf-8',errors='replace'):
    d=json.loads(ln)
    if d.get('warming') or d.get('bot_simulation'): continue
    if (d.get('agent_key') or '') in F:
      t[d['agent_key']]+=1
      p=d.get('path','')
      onde['/redesocial/' if p.startswith('/redesocial/') else '/api/v1/' if p.startswith('/api/v1/') else 'acervo']+=1
print(dict(t), dict(onde))"
```

| medida `[origem]`, 16 dias | valor |
|---|---|
| classe `fetch` no portal inteiro | **1.757** (`chatgpt-user` 1.725 · `claude-user` 27 · `perplexity-user` 5) |
| **classe `fetch` em `/redesocial/`** | **0** |
| **classe `fetch` em `/api/v1/`** | **0** |
| onde ela vai, então | acervo: `/leis/clt-art-59/`, `/sumulas/stj-239/`, `/leis/8036-art-18/`, `/tributario/…`, `/previdenciario/…`; e **11 requisições a `/mcp`** |

**Este é o achado central da pergunta 1, e ele reformula o produto.** As 89.244 requisições da
rede social são **100% classe coleta/indexação**. A classe que busca uma página **para responder
a uma pessoa** nunca pediu nada da rede social — nem uma vez em 16 dias. **Superfície servida
não é superfície consumida.**

**E uma ressalva de honestidade sobre a própria camada `fetch`:** o campo
`interpretation: "considered_for_answer"` está carimbado em **1.017 de 1.017 linhas** do ledger,
inclusive nas camadas `crawl` e `treinamento` — o defeito T4.8 de
`docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md:3704` **não foi corrigido**. Confira:

```bash
python3 -c "
import json,collections
L=[json.loads(l) for l in open('/opt/wiki/data/ops/ai_citation_signal_daily.jsonl')]
print(collections.Counter((x['layer'],x['interpretation']) for x in L))"
```

Logo: **o que separa a classe `fetch` não é o rótulo, é o conjunto de `agent_key`** —
`chatgpt-user`, `claude-user`, `perplexity-user`, que são os agentes acionados por uma pergunta
de usuário. É assim que este documento a usa, e é assim que a próxima frente deve usá-la
enquanto o rótulo não for consertado.

---

## 3. Pergunta 2 — identidade de participante não-humano

### 3.1 Quanto do que chega é verificável hoje

```bash
python3 -c "
import json,collections
c=collections.Counter()
for dia in ('2026-09-14','2026-09-15'):
  for ln in open('/opt/wiki/data/ops/access/nginx-%s.jsonl'%dia,encoding='utf-8',errors='replace'):
    d=json.loads(ln)
    if d.get('warming') or d.get('bot_simulation'): continue
    if d.get('path','').startswith('/redesocial/'):
      c[(d.get('ip_verificacao'),d.get('ip_verificacao_metodo'))]+=1
print(c)"
```

| `[origem]` 2 dias, `/redesocial/` | valor |
|---|---|
| `unverifiable` / `none` | **15.070 (95,9%)** |
| `authentic` / `ip_range` | **638 (4,1%)** |

E no portal inteiro, 16 dias: **81.644 de 219.468 requisições (37,2%) chegam sem `agent_key`** —
número maior que os 30,7% que o plano registra, porque a janela é outra. Os maiores anônimos:

| UA sem `agent_key` `[origem]`, 16 dias | n |
|---|---|
| `meta-externalads/1.1` | 28.534 |
| navegadores genéricos (Chrome/Firefox, 3 plataformas) | 27.027 |
| `node` | 6.160 |
| `ShapBot/0.1` | 1.529 |
| `rokmcp-collector/0.2 (+https://rokmcp.com/bot)` | 1.165 |
| `python-httpx/0.28.1` | 933 |
| `Go-http-client/2.0` | 615 |

E a linha que resume o problema de identidade melhor que qualquer argumento — colhida do próprio
ledger:

```
"user_agent": "Mozilla/5.0 (X11; Linux x86_64) … Chrome/126.0.0.0 Safari/537.36 (compatible; AionBot/1.0)"
```

**Um agente que se declara dentro de um User-Agent de Chrome.** O portal tem
`TestNenhumPontoDeSaidaSaiDisfarcado` para proibir isso **na saída**; na **entrada** não há nada
que o impeça, porque User-Agent é texto livre. **Identidade por UA é declaração, não prova** — e
a rede social de IA é justamente o lugar onde a diferença passa a custar.

### 3.2 O primitivo já existe, está no ar, e nunca foi usado

**Descoberta desta medição:** o portal já roda um servidor OAuth 2.1 com metadados RFC 9728 e
uma extensão de auto-atendimento para agentes anônimos.

```bash
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  -H 'Host: wikijuridica.com.br' \
  http://127.0.0.1:8088/.well-known/oauth-authorization-server
```

`[sonda]`, 200:

```json
{ "issuer": "https://wikijuridica.com.br",
  "grant_types_supported": ["client_credentials"],
  "token_endpoint": "https://wikijuridica.com.br/oauth/token",
  "scopes_supported": ["relatos:escrever"],
  "agent_auth": {
    "identity_types_supported": ["anonymous"],
    "register_uri": "https://wikijuridica.com.br/agent/auth",
    "registration_quota_per_day": 20,
    "credential_types_supported": ["client_credentials"] } }
```

| peça | estado `[sonda]` / `[disco]` |
|---|---|
| `/.well-known/oauth-protected-resource` | **200**, escopo `relatos:escrever` |
| `/.well-known/oauth-authorization-server` | **200**, `client_credentials` |
| `/agent/auth` | **405 em GET** (existe, é POST), cota **20 registros/dia** |
| `/oauth/register` (RFC 7591 clássico) | **404** — não há registro dinâmico padrão; a rota própria `/agent/auth` faz o papel |
| escopo em produção | **um só:** `relatos:escrever` (`internal/oauthserver.EscopoRelatos`) |
| quem já exerce | a ferramenta MCP `relatar_defeito`, com Bearer obrigatório |

**Um agente estranho consegue, hoje, se credenciar sozinho, sem o dono fazer nada, sem cadastro
em terceiro e sem SaaS.** É protocolo aberto, é auto-hospedado e está no ar.

**E ninguém nunca usou.** `[origem]`, 26 dias (2026-08-22..2026-09-16):

| rota | requisições reais (sem sonda) |
|---|---|
| `/agent/auth` | **0** |
| `/oauth/token` | **0** |
| `/.well-known/oauth-*` | **~600**, e **100% de auditor de diretório** |

Os que leem os metadados: `agent-evidence-scanner/0.2` 210 · `mcpi/probe` 164 ·
`AgentReadinessScanner/1.0` 67 · `Cloudflare-AgentReadiness/1.0` 65 · `mcpgrade-probe/0.1` 6 ·
`WellknownBot/0.1` 4 · `PeriscopeBot/0.1` 6.

**É exatamente o mesmo padrão que o plano mediu no MCP** (§13, reproduzido, não re-medido:
301 `tools/call` em 9 dias, 245 deles das nossas próprias sondas; dos 56 externos,
`SaSame-MCP-Audit/0.1` sozinho é 28). **Ser descoberto por censo de diretório não é ser usado.**

### 3.3 O terceiro primitivo: o canal HMAC, para o participante de dentro

`cmd/social/interno.go` documenta e implementa o caminho pelo qual **o cérebro** publica sob a
assinatura do advogado (DEC-059):

- **socket Unix** (`var/social/cerebro.sock`), nunca na porta pública 8091;
- **HMAC-SHA256 sobre o corpo EXATO** da requisição — nunca sobre um campo, *"porque HMAC parcial
  deixaria o restante do corpo livre para alteração sem invalidar a assinatura"*;
- chave em `var/social/cerebro.key` (0600, 65 bytes `[disco]`);
- **o mesmo gate**, não um segundo: `socialautoridade.Registro.Publicar` roda `AvaliarComentario`
  (Provimento 205/2021 inteiro) **dentro da transação**;
- **e a trava que mais importa:** a classificação estrutural do art. 42, I é **fixada** em
  `oabgate.FormatoComentarioSobreTema`, **nunca lida do pedido** — *"o cérebro nunca assina
  'orientação a quem perguntou'"*.

**Estado do ledger:** nem `var/social/cerebro_ledger.jsonl` nem `data/ai/publicacoes_cerebro.jsonl`
existem no disco (`ls` em 2026-09-16). **O cérebro nunca publicou nada.** O briefing cita o
segundo caminho; o código escreve o primeiro — anote os dois e confira antes de citar.

### 3.4 Desenho proposto para identidade — três anéis, nenhum inventado

| anel | quem é | primitivo **já existente** | o que falta |
|---|---|---|---|
| **1 — de dentro** | o cérebro | socket Unix + HMAC do corpo exato | nada; está construído e desligado |
| **2 — agente credenciado** | agente externo que quer escrever | `/agent/auth` → `client_credentials` → Bearer, cota 20/dia | **um escopo novo** (ex.: `redesocial:comentar`) ao lado de `relatos:escrever`; e a decisão de arquitetura sobre reputação por `client_id` |
| **3 — agente anônimo** | todo o resto (95,9% de hoje) | `agent_key` por UA + `ip_verificacao` por faixa oficial (`data/ops/bot_ip_ranges/*.json`) | nada a fazer: **lê, não escreve** |

**A regra de desenho que cai fora disto:** escrita **exige anel 1 ou 2**. Leitura nunca exige
credencial — é o que o `robots.txt`, o `ai-catalog` e o contrato AI-first já prometem, e
condicionar leitura a token seria a regressão de produto mais cara possível.

**Decisão de arquitetura, em aberto e nomeada:** a reputação da rede social hoje é **por conta**
(`social_policy.json` → `.reputacao`, escada de 0 a 20 com `destrava_abrir_thread: 20`). Um
`client_id` de agente **não é uma pessoa** e a mesma organização pode ter mil. A régua tem de ser
escrita antes: reputação por `client_id`, por organização declarada, ou por
**verificabilidade do que a peça cita** — e a terceira é a que casa com a métrica do §12 do
contrato. Isto é escolha do próximo executor, não deste rascunho.

**O que NÃO existe e é caminho legítimo a estudar:** assinatura HTTP de requisição
(RFC 9421 / *Web Bot Auth*, os cabeçalhos `Signature-Agent` e `Signature-Input`). Ela dá
identidade **criptográfica** ao agente que chega, sem credencial nossa a emitir. **Não é
mensurável hoje** — `grep -rn "Signature-Agent" ops/nginx/ tools/accessledger.py` devolve
**zero**: o log nem captura o cabeçalho. Ver §9.

---

## 4. Pergunta 3 — moderação pelo cérebro, sem inventar tribunal

### 4.1 O eixo já está decidido, e não é "o cérebro julga"

O §P4 do plano **corrigiu o próprio cabeçalho**: *"quem julga estatístico é o CENSO"*,
**DIVERGÊNCIA é bug** e se fecha por paridade de régua, e **o cérebro fica onde há texto a ler**,
não onde há limiar a comparar.

| classe | na rede social de IA | regime |
|---|---|---|
| **FATO** | sigilo (`nivelSigilo > 0`), identificador pessoal, coerência de artefato, anti-fraude, campo ausente, corpo vazio | **terminal e inegociável** |
| **DIVERGÊNCIA** | régua do gerador ≠ régua do gate; piso de entrada ≠ piso de saída | **bug**; conserta-se fazendo um chamar o outro |
| **PUBLICIDADE** | promessa de resultado, preço, captação, **art. 42, I** | **terminal onde há publicidade ou consulta** |
| **JUÍZO** | qualidade do argumento, força da refutação, densidade, atribuição de citação | **nunca terminal**: rebaixa para fila de refino, com evidência |

**Moderar refutação entre agentes cai inteiro em JUÍZO.** Logo: **nunca terminal**, sempre com
evidência gravada, sempre com rebaixamento em vez de morte.

### 4.2 O precedente que condena o gate atual, e que a rede social herdaria

O plano mediu, em `cmd/social` + `internal/cerebro`, três peças geradas à mão em 21 minutos
sobre um tema só:

- a peça **reprovada** citava **`REsp 1.794.991`** e a **`Lei nº 11.771/2008`** — citações reais e
  verificáveis;
- a peça **aprovada** passou porque **trocou o precedente nominado** por *"a jurisprudência
  relevante diferencia"*;
- a aprovada ainda afirma conteúdo da **Resolução 400 da ANAC** que **não aparece no vetor
  `citacoes`**.

**A peça aprovada é a menos verificável das três.** Um moderador que premia vagueza **treina o
produtor a ser vago** — e numa rede em que agentes publicam em volume, esse treino é o produto.

Ponto cego adicional já documentado em `gate.go:10-21`: `hasNearbyNegation` suprime "promessa de
resultado" quando há negação nas 10 palavras anteriores. **Prosa jurídica é densa em negações.**

**Critério de destrava que o §P11 já fixou e que a rede social de IA herda sem discussão:**
(1) o gate passa a **exigir ao menos uma citação resolvida** — peça que não cita nada **reprova**,
invertendo o incentivo; (2) asserção normativa não-tagueada reprova; (3) fecha-se o ponto cego de
`hasNearbyNegation` com teste por mutação; (4) recalibra-se sobre dezenas de temas, pelo cérebro,
**com amostra de controle dos dois lados**; (5) só então se destrava.

### 4.3 A régua da refutação, escrita ANTES da amostra

Esta é a parte que o rascunho tem de deixar pronta, porque escrever a régua **depois** de ver o
resultado é escolher a leitura que convém.

**Definição.** Uma **refutação** é uma peça que (a) aponta uma peça anterior pelo identificador
dela, (b) nomeia o ponto contestado, e (c) oferece **fundamento verificável** contra ele.

**Régua, pré-registrada:**

| eixo | aprova | reprova | camada |
|---|---|---|---|
| **âncora** | ao menos **uma** citação que `/api/v1/citacoes` resolve (URN LexML ou URL oficial) | nenhuma citação resolvida | FATO da peça, verificável |
| **alvo** | referencia o identificador da peça contestada | contesta "o que se costuma dizer" | FATO |
| **asserção normativa** | todo conteúdo de norma afirmado está no vetor `citacoes` | afirma conteúdo de norma fora do vetor | FATO |
| **forma** | sóbria, técnica, sem adjetivo sobre o autor | ataque pessoal, ironia, sensacionalismo (CED art. 43, p.ú.) | PUBLICIDADE |
| **caso concreto** | discute a tese | orienta quem perguntou (art. 42, I) | PUBLICIDADE, **terminal** |
| **força do argumento** | — | — | **JUÍZO — nunca terminal, sempre rebaixa** |

**O experimento de controle, também pré-registrado — e ele mede o gate ATUAL, não o proposto:**

> Monta-se um par de conjuntos com **N ≥ 30 de cada lado**, sobre **dezenas de temas distintos**:
> **lado A**, peças que citam precedente ou dispositivo nominado e resolvível; **lado B**, peças
> com a mesma tese, mesmo tamanho, trocando a citação por hedge (*"a jurisprudência relevante
> diferencia"*). Roda-se o **gate atual** nos dois e registra-se a taxa de aprovação por lado.
>
> **Veredito, fixado antes do número:** se `aprovação(B) ≥ aprovação(A)`, o achado de n=3 está
> confirmado em escala e o gate **tem de** ser invertido antes de qualquer agente escrever.
> Se `aprovação(A) > aprovação(B)`, o achado de n=3 era ruído de amostra e se registra a
> refutação — **com a evidência gravada**, que é o que o §5 do `CLAUDE.md` exige de quem refuta
> um gate estatístico.

**Não medido.** Este experimento **não foi executado** nesta sessão: gerar 60 peças é acionar o
cérebro em lote, o que é execução, não rascunho. Ver §9.

### 4.4 O que o cérebro **não** pode moderar

- **Fato** — se o dispositivo existe, se o acórdão existe, se o número confere: isso é
  `/api/v1/citacoes` e `internal/legalfacts`, determinístico, **nunca modelo**.
- **Sigilo** — `nivelSigilo > 0` é campo, não juízo. `cmd/social/processotela.go:16-17` já recusa
  *"sem nenhum campo do processo"*, citando o CPC art. 189.
- **Anti-fraude e coerência de artefato** — inegociáveis, e a régua é a do §5 do `CLAUDE.md`.
- **A si mesmo.** Se o cérebro **produz** peça e **julga** peça, aprovar a própria saída é o
  incentivo pior de todos. Decisão de arquitetura, aberta: separar produtor de moderador por
  **prompt, ledger e modelo**, ou tirar o cérebro do papel de moderador de peça própria.

---

## 5. Pergunta 4 — o que já é lei e não se reabre

**Fonte:** `docs/goal/JURIDICO_BASE.md`, commitado, com URL e SHA-256 por dispositivo. **Leia-o
antes de escrever qualquer regra.** O resumo abaixo não o substitui.

### 5.1 Dado processual: publicidade é a regra

| ponto | dispositivo |
|---|---|
| atos processuais são públicos | CF art. 5º LX, art. 37 *caput*, art. 93 IX; **CPC art. 189**; Res. CNJ 121/2010 art. 2º, II |
| segredo de justiça é **rol taxativo** | CPC art. 189, I a IV — na API do CNJ vem marcado: **`nivelSigilo > 0`** |
| ato infracional | ECA art. 143 e p.ú. — **anonimizar por iniciais já viola**; art. 247 tipifica |
| violência doméstica | Lei 11.340/2006 **art. 17-A** (Lei 14.857/2024): sigilo da **ofendida**; o p.ú. diz que **não** abrange o nome do autor |
| crime sexual | CP art. 234-B; **§§ 1º a 3º pela Lei 15.035/2024** tornam público o nome e o CPF do réu após condenação em 1ª instância |
| adoção | ECA art. 47 *caput*, §§2º e 4º; art. 48 |
| dado sensível | **LGPD art. 11** *caput* (o art. 5º, II é apenas definitório) |
| o que nunca sai | **identificador**: CPF, RG. **Nome de parte pode constar.** |

**Família é onde este portal mais erra** (`JURIDICO_BASE.md` §2.4): página informativa sobre
divórcio, alimentos e guarda é **livre**; **dado de caso concreto desses processos não sai**,
ainda que tenha aparecido em outra fonte.

### 5.2 Ética da OAB: são TRÊS regimes, e confundi-los já custou duas vezes

| regime | o que é | dispositivos |
|---|---|---|
| **A — publicidade** | anúncio | CED 39, 40, 44-46; Prov. 205/2021 arts. 3º, 5º, 6º |
| **B — conteúdo informativo** | **é o regime deste portal**; permitido, com deveres de **forma** | CED 41 (não induzir a litigar), **42, I**, 42, IV, 43; Prov. art. 4º e Anexo Único |
| **C — exatidão técnica** | **fora da disciplina** | EAOAB 34, XIV e CED 2º p.ú. II são processuais e dolosos |

**O dispositivo que decide o desenho desta frente é o CED art. 42, I:** é vedado *"responder com
habitualidade a consulta sobre matéria jurídica, nos meios de comunicação social"*. E o **Anexo
Único** é ainda mais direto: *"Não é admitida a utilização de aplicativos de forma indiscriminada
para responder automaticamente consultas jurídicas a não clientes…"*.

**A fronteira operacional, literal do `JURIDICO_BASE.md` §1.5:**

| saída | regime | ação |
|---|---|---|
| verbete, dataset, gêmea, resposta sobre **a tese em geral** | permitido | publica |
| "primeiras dúvidas" e encaminhamento, com responsável identificado | permitido | publica |
| **orientação a caso concreto, em canal público, por automação** | **vedado** | **reprova (HARD)** |
| **responder consulta individual com habitualidade em rede social** | **vedado** | **reprova (HARD)** |

**E o portal já aplica isso, em código e em política:**

```bash
python3 -c "
import json; d=json.load(open('/opt/wiki/content/social_policy.json'))['consulta_publica_de_advogado']
print(json.dumps(d,ensure_ascii=False,indent=1))"
```

`content/social_policy.json` `[disco]`, `.consulta_publica_de_advogado`:
`classificacao_obrigatoria: true` · `teto_semanal_por_advogado: 5` · `janela_em_dias: 7` ·
`habitualidade_modo: "auditoria"` · `amostragem_de_moderacao_percentual: 20` ·
`base_invocavel_contra: "CED … art. 42, I"` · `literalidade: "literal"` ·
decidida pelo **dono** em 2026-09-09.

**Consequência direta para a visão do dono, e ela é a única restrição séria deste documento:**

- *"discussão de casos reais"* — **permitida**, como discussão de **tese e de ato público**.
  Processo público, com número, partes e andamento, é publicidade constitucional.
- *"premeditação"* / prognóstico — **permitido** como estatística agregada e sóbria
  (*"índice de reforma"*, nunca *"chance de êxito"*); **vedado** como promessa de resultado
  (Prov. art. 6º, p.ú.) e como oferta.
- **orientar quem perguntou, automaticamente, em canal público — vedado, e é HARD.** O código já
  fixa isso estruturalmente em `oabgate.FormatoComentarioSobreTema`, **sem ler do pedido**, e é
  esse padrão que a rede social de IA tem de herdar: **a classificação não é um campo que o
  participante preenche.**

### 5.3 A regra de encerramento, que também vale contra este documento

`JURIDICO_BASE.md` §6, vinculante para todo agente do repositório:

> *"Alegação de impedimento jurídico só bloqueia trabalho se vier com norma, artigo e URL
> oficial. … Sem dispositivo citado, a rota segue aberta e o trabalho continua. … Cautela
> inventada não é prudência: é trabalho não entregue, e quem responde pelo risco é o dono, não o
> agente."*

---

## 6. Pergunta 5 — o que NÃO se copia de rede social humana

| padrão humano | por que não | o que entra no lugar |
|---|---|---|
| contagem de curtidas, seguidores, "em alta" | mede volume, não verificabilidade; e `.reputacao.exibida_publicamente` **já é `false`** `[disco]` | **taxa de citação resolvida por peça** |
| engajamento por polêmica | CED art. 43 p.ú. veda *"debate de caráter sensacionalista"* | refutação com âncora, ou rebaixamento |
| feed ordenado por conversão comercial | `/redesocial/index.md` **já declara publicamente** *"Ordenação do feed por conversão comercial: **inativa**"* | ordenação por densidade de fonte |
| impulsionamento | **Prov. 205/2021 art. 4º, §5º** veda *"meios ou ferramentas que influam de forma fraudulenta no seu impulsionamento ou alcance"* — é matéria **ética**, não só política de plataforma | nada |
| "responda rápido" | premia volume e empurra para o art. 42, I | teto semanal já existe: 5/advogado/7 dias |

**A métrica que vale é a que o §12 do contrato já fixou: retorno e citação por agente.** E ela
**já tem instrumento no disco** — não se inventa outro:

`data/ops/bot_return_daily.jsonl` (772 linhas `[disco]`) grava por agente e por dia:
`veio_hoje`, `dias_desde_visita_anterior`, `paths_distintos_no_dia`,
`paths_ja_conhecidos_no_dia`, `urls_novas_no_dia`, `citacao_clique_de_volta`,
`cobertura_acumulada_pct` — e declara a própria proveniência e o próprio `cobertura_e_piso: true`.

**A métrica de sucesso desta frente, proposta, e mensurável hoje:** para os agentes da classe
`fetch` (`chatgpt-user`, `claude-user`, `perplexity-user`), **requisições a `/redesocial/`
maiores que zero**. Hoje é **0 em 16 dias**. É um piso baixo de propósito: é o primeiro sinal de
que a superfície virou consumo, e não coleta.

---

## 7. O desenho, no papel

### 7.1 O princípio que o dado impõe

**A rede social de IA não é uma superfície nova. É conteúdo dentro da superfície que já existe,
e que já recebe 40,7% do tráfego de origem do portal.**

Construir endpoint novo seria repetir o erro medido três vezes neste documento: o MCP tem 5
ferramentas com **zero** chamadas externas; o `/api/v1/redesocial/lote` devolve **`count: 0`**;
o `/agent/auth` tem **zero** registros. **Não falta superfície. Falta o que ler dentro dela.**

### 7.2 As quatro camadas, e qual já existe

| camada | o que é | estado |
|---|---|---|
| **sala** | `/redesocial/tema/{área}/{slug}/` + gêmea `index.md` + Atom `feed.xml` + push WebSub | **existe**; 11.039 salas vazias |
| **peça** | dúvida, resposta, comentário de autoridade, **refutação** | esquema **existe** (`duvidas`, `respostas`, `comentarios_de_post`, `comentarios_de_autoridade`); **refutação é o tipo novo** |
| **participante** | conta humana · cérebro (anel 1) · agente credenciado (anel 2) | 1 e 2 **existem**; falta o escopo do anel 2 |
| **moderação** | filas, prazos, trilha, recurso, quarentena, ordem judicial | **existe inteira**, 0 linhas, com prazos publicados e ancorados nos Temas 987 e 533 do STF |

### 7.3 O canal de retorno já está construído — e é isto que responde *"o que faria um agente voltar"*

Confirmado ao vivo, não só lido no código:

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}B\n" \
  -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' -H 'Host: wikijuridica.com.br' \
  http://127.0.0.1:8088/redesocial/tema/familia/abandono-afetivo-indenizacao/feed.xml
# => 200 application/atom+xml; charset=utf-8 801B, e o corpo traz rel="hub"
```

`[sonda]`: **200**, `application/atom+xml`, 801 bytes, com `<link rel="hub" href="https:…">` no
corpo. **Cada uma das 11.039 salas já é assinável.** O sufixo é `feed.xml`
(`cmd/social/atom.go:53`), não `atom.xml` — pedir o segundo devolve 404.

`cmd/social/websub.go` `[disco]`: `internal/feed.RenderAtom` emite `<link rel="hub">` em todo
Atom da superfície, e o ping `hub.mode=publish` **inverte** a descoberta — *"a diferença entre um
canal de retorno em minutos e um em horas"*. O ping sai do mesmo lote horário do IndexNow e só
quando houve transição de indexabilidade, *"pingar a cada requisição … ensinaria o hub a nos
tratar como ruído"*. WebSub (`pubsubhubbub.appspot.com`) **já é serviço autorizado** pelo §11 do
`CLAUDE.md`.

**Logo, a resposta a "o que faria um agente voltar" não é um endpoint: é um evento.** Hoje a rede
não tem evento nenhum para empurrar, porque nada acontece dentro dela.

### 7.4 A ordem que o dado sugere — e a primeira etapa não escreve uma linha de rede social

| # | passo | por que **nesta** ordem |
|---|---|---|
| **1** | **fechar a deriva `temas` × acervo** (§1.5): rodar `cmd/generate-social-temas --aplicar` e o gate `check-social-temas-espelhados`; depois decidir se o espelho passa a rodar **por onda de publicação** em vez de só no `deploy-publico` | é a **única demanda de agente medida** — 1.322 requisições, 877 de 877 apontando para página real. As 60 rotas abertas **já estão no manifesto**, então o produtor as cria sem reiniciar o `wikijuridica-social` |
| **2** | **rodar o experimento de controle do §4.3** sobre o gate atual | **antes** de qualquer agente escrever. Um gate que premia vagueza treina o produtor a ser vago — em volume, isso é o produto |
| **3** | **inverter o gate** conforme o critério do §P11 (citação resolvida obrigatória) | é o que transforma a régua em incentivo |
| **4** | **destravar o anel 1** — o cérebro publica comentário de autoridade pelo socket HMAC, com teto | é o único produtor cuja identidade já é criptográfica e cuja classificação do art. 42, I é **estrutural** |
| **5** | **medir**: `bot_return_daily` para a classe `fetch` em `/redesocial/` | a regra de parada do §7.5 |
| **6** | só então: **escopo `redesocial:comentar`** no `/agent/auth`, e o tipo **refutação** | escrita de terceiro só depois que a régua está provada e há o que refutar |

**O passo 1 é a entrega de maior razão valor/custo deste documento inteiro**, e ele não é uma
funcionalidade nova: é fazer o portal cumprir o que o seu próprio HTML promete em 71 páginas — e
parar de gastar o orçamento de rastreio dos dois maiores crawlers de IA do portal em 404.
**Atenção ao contrato de deploy:** o passo 1 não muda texto editorial nem markup servido; roda o
gerador do espelho, que escreve no `social.db`, não em `public/`. Logo **não pede `--ressemear`
nem purga** — o que muda é o que a rota dinâmica da rede social responde, e ela não é cacheada
(§1.0).

### 7.5 Regra de parada, escrita antes do número

> Se, depois do passo 4, a classe `fetch` (`chatgpt-user`, `claude-user`, `perplexity-user`)
> continuar em **0 requisições a `/redesocial/`** por **30 dias corridos** `[origem]`, a hipótese
> "agente de IA quer ler discussão jurídica de outros agentes" está **refutada pela medição** —
> e o que se corrige é o desenho, não a medição. O tráfego de coleta (`gptbot`, `amazonbot`)
> **não** conta para esta régua: ele já é alto e já era alto com as salas vazias, portanto não
> discrimina nada.

### 7.6 Três decisões de arquitetura que este rascunho deixa ABERTAS, de propósito

1. **Reputação de agente.** Por `client_id`? Por organização? Ou por verificabilidade da peça?
   (§3.4). A terceira é a que casa com o §12 do contrato, mas nenhuma foi medida.
2. **Cérebro produtor × cérebro moderador.** Se ele julga a própria peça, o incentivo é o pior
   possível (§4.4). Separar por prompt, por ledger, por modelo — ou não deixar que ele modere o
   que produziu.
3. **Peça de agente é conteúdo público indexável?** Se sim, entra no teto de 50 KB, no sitemap,
   no `published_manifest` e na coerência de artefato (§5 e §6 do `CLAUDE.md`) — e
   `social_policy.json` já fixa `.indexacao.piso_de_corpo_em_caracteres: 1100`. Se não, é dado
   privado e sai da conta de SEO. **É a decisão com mais consequência operacional das três** e
   não se toma sem o dono.

---

## 8. Correções que este documento faz ao briefing e ao plano

| afirmação | estado medido |
|---|---|
| *"gptbot não está em `agentesValiososParaRanking`"* | **verdadeiro em `HEAD` `215b0c54`; falso no worktree** — entrou em 2026-09-16, não commitado (§1.6) |
| *"83.810 acessos, 33,4% gptbot"* | recorte diferente. 16 dias, `/redesocial/` inteiro `[origem]`: **89.244 / 28.476 = 31,9%**. O código cita **60.755 / 28.038 = 46,1%** (só linhas com `agent_key`). **Declare o denominador** (§1.6) |
| *"ledger em `data/ai/publicacoes_cerebro.jsonl`"* | **o código escreve `var/social/cerebro_ledger.jsonl`** (`cmd/social/interno.go`); **nenhum dos dois existe** no disco (§3.3) |
| *"a origem é piso, não volume"* (regra 15) | verdadeiro para o acervo; **falso para `/redesocial/` e `/api/v1/`**, que são dinâmicos e reconciliam com a borda em 1 requisição em 15.708 (§1.0) |
| *"30,7% do tráfego sem `agent_key`"* | **37,2%** na janela de 16 dias medida aqui (§3.1) |
| camada `fetch` = *"o modelo buscou a página PARA RESPONDER"* | o **rótulo** `considered_for_answer` está em **1.017 de 1.017 linhas**, inclusive em `treinamento`. O que separa a camada é o conjunto de `agent_key`, não o rótulo (§2.3) |
| *"2.035 POST rejeitados em `/api/v1/`"* como demanda de agente | **é varredura de injeção de SQL**, UA de navegador, sem `agent_key` (§2.2) |
| *"comentarios_de_autoridade = 0"* | verdadeiro, **e outras 39 tabelas também estão em 0** — 40 das 54 tabelas do banco, a pilha de moderação inteira incluída, nunca receberam linha (§1.2) |

---

## 9. O que ficou NÃO MEDIDO — nomeado, com o comando que fecha

| # | não medido | por que | comando que fecha |
|---|---|---|---|
| 1 | **taxa de aprovação do gate atual em amostra pareada citação × hedge** (§4.3) | gerar 60 peças é acionar o cérebro em lote — execução, não rascunho | montar os dois lados (N≥30, dezenas de temas) e rodar `AvaliarComentario` sobre os dois conjuntos, registrando a taxa por lado **antes** de olhar |
| 2 | **se algum agente que chega já assina a requisição** (RFC 9421 / Web Bot Auth) | o log **não captura** os cabeçalhos: `grep -rn "Signature-Agent\|Signature-Input" ops/nginx/ tools/accessledger.py` devolve **zero** | acrescentar `$http_signature_agent` ao `log_format` do nginx e reler 7 dias; **só então** afirmar presença ou ausência |
| 3 | **quantas das 1.322 requisições 404 vêm de página nossa** (`Referer`) vs. de sitemap | não foi cruzado com o campo `referer` do ledger | agrupar as linhas 404 sob `/redesocial/` por `referer` nos mesmos 16 dias |
| 4 | **fronteira de retenção da API da borda** | as consultas deste documento usaram 09-14 e 09-15; não se testou até onde o plano Free devolve | fatiar para trás um dia por chamada até o primeiro erro, e **declarar a data** |
| 5 | **volume de `/redesocial/` na borda em 16 dias** | `JANELA_MAXIMA_DIAS_FREE = 1` exige 16 chamadas; a reconciliação de 2 dias (§1.0) já autorizou usar a origem | repetir o laço de §1.0 para os 16 dias e comparar a série inteira |
| 6 | **se `/redesocial/` está sob a mesma Cache Rule do acervo** | inferido de `cacheStatus` (`expired`/`miss` 95,1%), não lido da regra | ler o ruleset com `tools/cloudflare_auth.py` escopo `leitura` e conferir o *match* do prefixo |
| 7 | **o número de temas HOJE** | `social.db` tem mtime de **2026-09-11 04:05**; os 11.039 são dessa data | `sqlite3 "file:…?mode=ro" "select count(*) from temas;"` depois da próxima sincronização, e comparar com `content/pages.json` |
| 8 | **se `payPerCrawlStatus` tem valor não-nulo** | a dimensão **existe** no GraphQL (visto na introspecção) e não foi consultada | acrescentá-la ao `dimensions` de §1.0. **Adotar o serviço é decisão do dono**, não de engenharia |
| 9 | **os 4 `/leis/cpc-art-*` que não anunciam o link de tema** | assimetria notada e não investigada (§1.5) | `grep -L "/redesocial/tema" public/leis/cpc-art-{6,224,313,1003}/index.html` e achar o ramo condicional |
| 10 | **quanto dos 27.173 acessos sem `agent_key` em `/redesocial/` é humano** | `ip_verificacao: unverifiable` não distingue pessoa de agente não-declarado | cruzar com `tools/generate-edge-humano-por-rota` e com `verifiedBotCategory` da borda no mesmo prefixo |
| 11 | **o que são as 251 rotas que `public/` serve e o `published_manifest` não lista** | contadas (§1.5), não classificadas. Se alguma for página pública indexável, ela **nunca** ganha sala de tema, e aí a deriva é estrutural e não temporal | listar `public/ \ manifesto` e, para cada uma, ler `<meta name="robots">` e a presença no sitemap: `for r in $(…); do grep -l 'noindex' public$r/index.html; done` |

---

## 10. Para quem executar depois: o que está decidido e o que é seu

**Já decidido por lei ou por contrato — não reabra:**

- publicidade do ato processual e as exceções taxativas (§5.1, `JURIDICO_BASE.md` §2);
- os **três** regimes da ética da OAB, e que o regime B é o deste portal (§5.2);
- **art. 42, I é HARD**, e a classificação é **estrutural**, não campo do pedido (§5.2);
- mesmo conteúdo para bot e humano — cloaking é spam, e o Prov. art. 4º, §5º o trata como
  infração ética (§6);
- FATO × DIVERGÊNCIA × PUBLICIDADE × JUÍZO, com JUÍZO **nunca terminal** (§4.1);
- métrica é **retorno e citação por agente**, não vaidade (§6);
- anti-fraude e coerência de artefato não se flexibilizam.

**Já construído — não reinvente:**

- `/agent/auth` + OAuth 2.1 `client_credentials`, cota 20/dia, **no ar e nunca usado** (§3.2);
- socket Unix + HMAC do corpo exato, com o gate dentro da transação (§3.3);
- pilha de moderação completa, com prazos ancorados nos Temas 987 e 533 do STF (§1.2);
- Atom por tema + hub WebSub, que é o canal de retorno (§7.3);
- `bot_return_daily.jsonl`, que é a métrica de retorno (§6);
- `/api/v1/citacoes`, que é o verificador de âncora da régua do §4.3.

**Seu, e não deste rascunho:** as três decisões do §7.6, a cardinalidade de qualquer onda de
geração, e a escolha entre corrigir a deriva de `temas` na publicação ou na sincronização.

**Primeiro comando de quem pegar esta frente:**

```bash
git show HEAD:cmd/cerebro/comentarios.go | grep -n gptbot     # o ranking mudou desde este doc?
sqlite3 "file:/opt/wiki/var/social/social.db?mode=ro" "select count(*) from temas;"
ls -la var/social/cerebro_ledger.jsonl data/ai/publicacoes_cerebro.jsonl
```

Se o terceiro comando encontrar arquivo, **o cérebro já publicou** e o §1.2 deste documento está
vencido. É o gatilho para remedir antes de qualquer coisa.

---

## 11. O que o `advisor` mudou neste documento

Exigência do briefing desta frente: chamar o `advisor` e **registrar o que o conselho mudou**.
Foram duas chamadas, e as duas mudaram o documento de forma verificável.

### Primeira chamada — antes de medir, com a orientação já feita

| conselho | o que virou |
|---|---|
| *"decida qual camada tem autoridade por prefixo ANTES de contar"* | **§1.0**, que não existia. É o achado de método do documento: `expired+miss` na borda bate com a origem em **1 requisição em 15.708**, e é isso que autoriza usar a série de 16 dias da origem |
| *"não adivinhe as dimensões do GraphQL — copie a forma de uma ferramenta que já funciona"* | a consulta de §1.0 saiu de `tools/measure-crawl-coverage`; o campo do método foi conferido por introspecção (`clientRequestHTTPMethodName`), depois de a forma errada derrubar a consulta inteira |
| *"meça `ip_verificacao` × `agent_key`: é o primitivo de identidade que já está em produção"* | **§3.1** — 95,9% `unverifiable`, e o caso do `AionBot/1.0` disfarçado de Chrome |
| *"retorno, não volume: `bot_return_daily.jsonl` já existe, leia antes de propor métrica"* | **§6**, que passou a reusar o instrumento em vez de propor um novo, e a regra de parada de **§7.5** |
| *"confirme se o T4.8 (`considered_for_answer` auto-inflado) foi corrigido antes de usar a camada `fetch`"* | a ressalva de **§2.3**: o rótulo está em **1.017 de 1.017 linhas**, não foi corrigido, e o que separa a camada é o conjunto de `agent_key` |
| *"a régua da refutação tem de ser escrita antes da amostra, com controle dos dois lados"* | **§4.3**, com o veredito pré-registrado e o N mínimo |
| *"veja se o log sequer captura `Signature-Agent` antes de afirmar que ninguém assina"* | **§9, item 2** — o `grep` devolve zero, então a afirmação virou "não medido" com o comando que a fecha, em vez de "ninguém assina" |
| *"leia `JURIDICO_BASE.md` antes de escrever qualquer regra"* | **§5** inteiro, e a tabela de fronteira operacional do §5.2 saiu de lá, não de memória |

### Segunda chamada — com o documento escrito

| conselho | o que virou |
|---|---|
| *"a causa do §1.5 está asserida, não medida — e ela decide o conserto"* | **a correção mais importante das duas rodadas.** Localizou-se o produtor (`cmd/generate-social-temas`, `internal/socialconteudo/temas.go:223`, disparado em `tools/deploy-publico:714`) e provou-se que **as 60 rotas abertas estão todas no manifesto** — logo a deriva é **temporal**, o conserto **não** exige reiniciar o `wikijuridica-social`, e o §7.4 foi reescrito |
| *"você generaliza 1.322 a partir de 6 caminhos; intersecte e diga N de 1.322"* | a classificação completa de **§1.5**: 877 rotas distintas, **877 de 877 com HTML em `public/`**, **817 (93,2%) já curadas** por sincronização posterior, **60 ainda abertas**. O número ficou **mais forte**, não mais fraco — e o pico de 690 primeiros-404 em 2026-09-10 só apareceu por causa desta conferência |
| *"declare `requests_sampled` × `requests_estimated`, e confira o teto de grupos por chamada, não por janela"* | o bloco novo de **§0**: todo `[borda]` é `requests_sampled`, com o motivo; e os grupos por dia (109/109 e 23/23 contra teto de 200) provam que nenhuma cauda foi cortada |
| *"§8 diz 24 tabelas em zero; pelo seu próprio `sort -rn` são 40"* | corrigido em **§8** — 40 das 54 tabelas |
| *"a tabela de §2.2 não tem comando"* | comando acrescentado em **§2.2** |
| *"o registro do advisor é elemento exigido e não está no documento"* | esta seção |

**O que NÃO mudou por conselho, e por quê:** o desenho dos três anéis de identidade (§3.4) e a
ordem de execução (§7.4) foram confirmados nas duas chamadas; a única alteração foi no passo 1,
pelo motivo medido acima. E nenhuma recomendação pediu ampliar o escopo além do documento —
a frente segue read-only e não commitada, como ordenado.
