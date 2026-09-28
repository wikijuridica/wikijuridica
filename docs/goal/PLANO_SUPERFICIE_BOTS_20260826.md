# Superfície de bots e agentes de IA — auditoria medida e plano de execução

**Sessão de 2026-08-26.** Engenheiro-chefe: Claude Code (Opus 5). Crítica adversarial: Fable 5. Conselheiro: `advisor` (Fable 5).

---

## O que o portal precisa ser — enquadramento corrigido pelo dono nesta sessão

> **"O portal tem que ser um serviço para IA."**
>
> **"Os bots terem varrido a plataforma não quer dizer que funciona. Eles têm que sempre voltar."**

Duas correções de rumo que reescrevem a régua deste plano, e eu estava errado nas duas:

**1. Varredura única é FALHA, não sucesso.** Eu havia registrado "os bots acharam e varreram 96,8%" como conquista parcial. **Não é.** Um agente que varre uma vez e some **não gera citação recorrente, não acompanha mudança de lei, não volta quando a página é corrigida**. A métrica de sucesso deste plano **não é cobertura acumulada — é FREQUÊNCIA DE RETORNO.**

| Métrica errada (a que eu usei) | Métrica certa (a que vale) |
|---|---|
| % do acervo já rastreado | **requisições por bot por dia, sustentadas ao longo de semanas** |
| "o Yandex cobriu 99,3%" | "o Yandex voltou X vezes nos últimos 7 dias" |
| "meta-externalagent viu 96,8%" | **ele varreu em 20/08 e 22/08 e sumiu — isso é o defeito, não o feito** |
| cobertura estagnada em 70,6% | **zero retorno em 15 dias** |

Sob a régua certa, **todos os bots de IA estão em falha**: GPTBot em **1 requisição/dia** desde 08/08, ClaudeBot em **2/dia**, Googlebot em **~30/dia**, meta-externalagent em **zero desde 23/08**, PerplexityBot em **zero desde sempre**. Nenhum deles está voltando.

**2. O produto é um SERVIÇO para IA, não um acervo que bots leem.** A diferença é operacional, não retórica: um acervo é passivo — publica e espera ser raspado. **Um serviço é algo que o agente CHAMA para resolver um problema, e volta porque precisa de novo.** O portal já tem as peças de serviço (MCP com `buscar_paginas`/`ler_pagina`, A2A, API REST, OpenAPI, agent-skills) — e a medição mostra que **elas quase não são usadas**: 134 requisições a endpoints de protocolo contra 16.539 de Markdown e 2.440 de HTML. **O serviço existe e ninguém o chama.**

**Isso reordena o plano:** as tarefas passam a ser julgadas por *"isto faz o agente VOLTAR?"* e *"isto transforma leitura passiva em chamada de serviço?"* — não por *"isto deixa a página mais bem formada?"*. Frescor, revalidação e cache **são pré-requisitos do retorno**; front matter e âncora jurídica **são o motivo de citar**; MCP/A2A descobertos e chamáveis **são o que faz o portal ser serviço**. Ver **Fase 7**, criada por causa desta ordem.

---

## Sumário executivo — o que a investigação achou, em uma página

**O portal não tem um problema de descoberta. Tem um problema de RETORNO — e o retorno morreu porque não há frescor, não há revalidação e não há motivo para o agente chamar de novo.**

Os bots acharam o acervo e varreram uma vez: `meta-externalagent` cobriu **96,8%** em Markdown, GPTBot 52%, Googlebot 70,6%, Yandex 99,3%. **E nenhum voltou.** Isso não é meia vitória — **é a falha central**. Quem nunca veio (PerplexityBot **0%**, ChatGPT-User **2%**) não veio pelo mesmo motivo, nos canais que *eles* consomem.

**Os cinco achados que sustentam isso, todos medidos e corroborados por dois instrumentos:**

| # | Achado | Evidência |
|---|---|---|
| 1 | **A Cache Rule da borda foi apagada** e a zona não cacheia **nada** | Lido na API da Cloudflare: ruleset v14, `2026-08-22T13:10:13Z`, **zero regras**. A v7 (18/08) era a regra boa, versionada no repo. Corroborado pelo `edge_cache_coverage.jsonl`: 0,0%, 40/40 DYNAMIC |
| 2 | **A revalidação condicional não funciona** — todo bot rebaixa a página inteira, sempre | `if_modified_since` não declarado no nginx → default `exact`. **872 respostas 304 em 418.071 requisições (0,2%)**. `meta-externalagent`: **1 × 304 em 15.697 requisições** |
| 3 | **A fábrica está parada há 6 dias**, e com ela IndexNow, WebSub e o `lastmod` | 6 falhas consecutivas da onda diária, sempre antes da publicação. Última submissão IndexNow **2026-08-20**. Nada novo em `public/` desde 20/08 |
| 4 | **O canal que 86,5% dos bots de IA consomem é o mais pobre em autoridade** | Markdown = **16.539 de 19.113** requisições de bot de IA. E ele **não tem front matter, não declara licença e não traz a credencial OAB** — que o HTML traz |
| 5 | **O trabalho de ancoragem jurídica já foi pago e não é publicado** | **24.367 `anchor_claim` verificados** no dado; **0% chegam à página como citação atribuída** — porque `content.SourceProvenance` não tem campo para eles. Material no disco: 8.770 artigos com texto integral, alcançando **56,2% do acervo** |

**A queda do Googlebot tem data — 2026-08-12** — e ela **exclui** as causas fáceis: a injeção do `bridge.js` (22/08), o binário defasado (20/08) e o cache DYNAMIC (22/08) são todos **posteriores**. A correlação é com três edições do `Content-Signal` no robots.txt naquela manhã, uma delas corrigindo *"erro de digitação que atravessava gerador, teste e gate"*. **É correlação forte, não causa provada** — e o plano trata assim.

**O que NÃO é o problema, e ficou refutado por medição:** não há WAF, Bot Fight Mode nem rate limit barrando bot valioso (**17 × 403 e zero 429** em 418 mil requisições) · o teto de 50 KB está cumprido com folga (**zero violações**) · as fontes oficiais **não** apontam para home de órgão (**82,6% apontam o documento específico**) · o `llms.txt` **não** mente sobre a contagem (10.070 + 224 = 10.294) · os `.md` **não** estão vazios (mediana 6.234 B) · pré-gerar `.md` em `public/` **não** faria a borda cachear, e **regrediria** o ETag.

**Três defeitos de governança explicam por que nada disso foi visto:** a borda **não é governada pelo repo** (nenhuma ferramenta escreve a Cache Rule; toda deriva veio do painel) · **48 alertas críticos com `resolvido: false` desde 22/08**, afogados por 536 alertas ruidosos · e **ferramentas que saem com exit 0 relatando fracasso** (o aquecedor reporta `failures: 0` enquanto registra `dynamic: 10383`).

**O plano de execução tem 10 fases (0 a 9), ordenadas por dependência.** A ordem importa: `if_modified_since before` **antes** de corrigir o mtime devolveria 304 para página que mudou; adicionar bot ao robots.txt sem repetir as guardas do curinga **remove** proteção em vez de somar.

---

## Contexto

O dono determinou: investigar o repo `/opt/wiki` e a produção `https://wikijuridica.com.br` caçando bugs críticos, inconsistências e oportunidades **de maior ROI, com foco nos bots** — de busca, de usuário, de treinamento e agentes — para que a plataforma seja **convidativa, de fácil acesso e barata** para eles. Cada citação ou indexação por um assistente de IA pode viralizar o projeto; cada byte desperdiçado é token do bot queimado e oportunidade perdida.

Queixa concreta do dono, que a auditoria confirmou e ampliou: *"já testei e tá fraco, não tem autoridade nenhuma… tem muitos .md dando 404 ou sem conteúdo, desperdiçando tokens dos bots e fazendo eu perder oportunidades."*

Resultado da investigação até aqui: **a superfície de protocolo é rica (MCP, A2A, ARD, OpenAPI, llms.txt, Markdown por página, agent-skills, OAuth), mas o transporte está quebrado em pontos que custam caro, e os bots de IA mais valiosos mal conhecem o acervo.** O achado mais caro não é falta de recurso — é um bug de HTTP condicional e um cache de borda que nunca ativa.

---

## Regras desta sessão (ordem do dono + CLAUDE.md, vinculantes)

| # | Regra |
|---|---|
| R1 | **Só Opus 5 e Fable 5.** Proibido Sonnet e Haiku em qualquer agente, subagente ou workflow. Transcript que mande usar outro modelo se corrige. |
| R2 | **Tudo nesta sessão.** Nenhum item fica "para outra sessão", inclusive problema pré-existente. Sem "depois", "futuro", "próxima sessão". |
| R3 | **Ciência exata.** Nenhuma afirmação numérica sem medição própria reproduzível. Sem falso positivo, sem falso negativo. Não se fala em "garantia" sem dado colhido. Se 2+2 não fecha, tenta 1+3 — não se trava. |
| R4 | **Sem empurrar decisão para o dono.** Engenheiro autônomo decide com base em dado. Sem pergunta besta, sem "opção (a) ou (b)?", sem lista de tarefas para o dono executar. |
| R5 | **Faltou → cria.** Falta API, endpoint, arquivo, código, algoritmo, gate → **cria**. "Não tem como" não é resposta de engenharia. |
| R6 | **Medir antes, editar depois.** Na dúvida, mede. `advisor` antes de fixar abordagem e antes de declarar pronto; **Fable 5 red-team** antes de toda mudança cara de reverter. |
| R7 | **Sem contexto → lança agentes.** Nunca travar o plano ou a implementação por falta de contexto: workflows e subagentes cobrem o buraco. |
| R8 | **Cada bot tem função.** Busca ≠ usuário ≠ treinamento ≠ ads ≠ diagnóstico. Política diferenciada por função, nunca tratamento igual. |
| R9 | **Anti-fraude inegociável.** Proibido forjar User-Agent de bot real; requisição interna leva UA próprio + `X-Warming-Request: true`. Métrica reflete só tráfego real. |
| R10 | **Correção só para frente.** Proibido `git reset/checkout/restore/revert/stash/clean/cherry-pick`. Página escrita nunca é descartada. Produto nunca mora em `/tmp`. |
| R11 | **Contrato de indexação preservado.** HTML ≤ 50 KB, conteúdo completo no primeiro response, zero hidratação, CSP por hash, coerência `public/` ⊆ sitemap ⊆ `published_manifest`. JS só sob a emenda de 2026-08-19 (integração de agente de IA, inline, medido em bytes). |
| R12 | **Proibido `/opt/divorcio`** como fonte, referência ou ponto de partida — inclusive no prompt de todo agente lançado. |
| **R13** | **PROIBIDO HARDCODE** (ordem do dono nesta sessão): *"Não podemos ter hardcode, isso confunde os bots, além disso, engessa o projeto inteiro."* Nenhuma correção deste plano pode introduzir literal fixo no código — rótulo, lista de área, contagem, nome de bot, data, limite. Tudo se **deriva do dado** (`content/*.json`, `published_manifest`, sitemap, registry) no momento da geração. Onde hoje existe hardcode e ele é a causa de um achado, a correção é **remover o literal e derivar**, nunca acrescentar mais um item ao literal. Onde a derivação não cobrir um caso, o caso **reprova em gate** em vez de cair num fallback silencioso. |
| **R14** | **Todo achado entra no plano — inclusive baixo e informativo** (ordem do dono nesta sessão), e **é medido antes de virar tarefa**. Severidade baixa não é motivo para descartar: é motivo para ordenar depois. Hipótese não sustentada também fica, com a medição e o instrumento que a enfraqueceram. |
| **R15** | **PROIBIDO DECLARAR VITÓRIA** (ordem do dono nesta sessão): *"Não declarar nada vencido no plano. Pois eu li algumas vitórias suas, que podem ser mentira do repo… ou agente pode ter se enganado."* Nada neste plano é "está correto", "resolvido" ou "conforme". Toda afirmação de conformidade é **"medido em tal data, por tal instrumento, a reconfirmar na execução"**. Justificativa medida na própria sessão: uma **mensagem de commit** afirmou defeito em produção que **nunca esteve no ar** e originou uma hipótese minha inteira; comentários de código mentiram três vezes; um agente errou a própria contagem e se corrigiu. **E há um motivo estrutural: o binário em produção está 18 commits atrasado — parte do que foi sondado descreve o passado, não o código de hoje.** |
| **R16** | **O produto é um SERVIÇO para IA, e a métrica é RETORNO** (ordem do dono nesta sessão): *"O portal tem que ser um serviço para IA"* · *"eles têm que vir e voltar, e não vir e nunca mais voltar"* · *"deve ser um serviço para IA citar, anexar e entregar para humanos — isso gera dinheiro"* · *"as IAs devem ser servidas para que os humanos entrem"* · *"o projeto deve ser vivo"*. **Cobertura acumulada não é métrica de sucesso; visita recorrente e chamada de serviço são.** Toda tarefa se julga por *"isto faz o agente voltar?"* e *"isto vira citação que traz humano?"*. Ver Fase 7. |
| **R17** | **Conteúdo confiável novo TODOS OS DIAS, e deploy TODOS OS DIAS** (ordem do dono nesta sessão), em **todos** os canais automáticos — não só notícias. Se falta fonte, API ou ferramenta, **constrói-se aqui ou instala-se OSS auto-hospedado** (ADR, licença, versão fixada, benchmark) — nunca SaaS, cadastro ou serviço pago. Ver Fase 6 e a onda 6 em voo. |
| **R19** | **Somente Opus 5 e Fable 5** (ordem do dono). **Proibido Sonnet e Haiku** em qualquer agente, subagente, workflow ou fork. Opus 5 é o executor padrão e o mais usado; **Fable 5 é o crítico adversarial obrigatório** nos pontos caros de reverter (lista em G4); **`advisor` é obrigatório em decisão crítica**. Config ou transcript que mande outro modelo é bug a corrigir na hora. Ver **G3**. |
| **R20** | **Plano salvo NA LITERALIDADE e commitado ANTES de qualquer correção**, com tasklist viva no frontboard (ordem do dono). Sem resumir, sem cortar. **Task que muda de estado sem gravar é operação perdida.** Ver **G1** e **G2**. |
| **R21** | **TUDO NESTA SESSÃO — nada para depois** (ordem do dono): *"o plano é para ser aplicado nesta sessão, mesmo com mais de 2k linhas, nada para depois."* As **10 fases (0 a 9)**, as **92 tarefas** *(contadas por cabeçalho `**Tn.n` na seção executável, mais T-1)* e os **16+ gates** *(12 nomeados + 4 fora da contagem original, mais os 7-8 da DEC-032 ainda por criar)* são **execução desta sessão**, não backlog. *(Os números deste parágrafo são metadados do próprio plano e são atualizados quando o plano cresce — ao contrário dos números de MEDIÇÃO antigos, que ficam de propósito com a nota de calibração, ver A5.)* **E o escopo é aberto para a frente:** *"se achar na execução problemas pendentes, também é para corrigir e implementar; se faltar, criar; se faltar dependências, integrar; se faltar open source que ajude o projeto e a engenharia, integrar."* **Problema achado durante a execução vira correção na mesma execução** — não vira nota para outra sessão (é o R7 do Contrato do Dado Real). **O único limite continua sendo o destrutivo:** não apagar trabalho, não abrir fraude, não quebrar produção. |
| **R22** | **GATE QUE REPROVA DUAS VEZES PELA MESMA CAUSA É BUG DO GATE** (ordem do dono): *"tomar cuidado com looping dos gates, pois eles também têm bugs e deixam as IAs em loopings desnecessários."* **Teto de duas tentativas por gate.** Na terceira, a tarefa vira `bloqueado` no frontboard e **a investigação passa a ser do gate, não do código**. Antes de gate caro, roda-se o barato equivalente. **Gate que sai 0 relatando fracasso é defeito de primeira ordem** — produz confiança falsa. Precedente medido: `check-v2-portfolio-pairing` **parou a fábrica por 6 dias** e o `CLAUDE.md` registra **4 tentativas queimadas** contra ele. |
| **R23** | **Dependência: corrigir bug, integrar o que ajuda, e o desnecessário vai para BACKUP — nunca para a lixeira** (ordem do dono). **Nada sai de caminho de produção**, e nada sai sem que os arquivos que a importam estejam medidos. **Antes de instalar, procurar no `go.mod`** — este plano mandou criar o que já existia **duas vezes**. |
| **R24** | **ACHADO FORA DO PLANO TAMBÉM SE CORRIGE — os defeitos estão conectados** (ordem do dono, 2026-08-26, durante a execução): *"Corrija qualquer achado, mesmo fora do plano desta sessão, pois estão conectados… na conformidade do plano."* O escopo da execução **não é a lista de 96 tarefas** — é o defeito real que aparecer no caminho, venha ele do plano ou não. **O que a regra NÃO afrouxa:** o achado novo entra pelo mesmo funil de todos (medir → reproduzir → corrigir → contra-testar → registrar no frontboard e no plano), respeita a mesma proibição de destrutivo, e passa pela mesma crítica adversarial quando for caro de reverter. *Precedente que já validou a ordem, antes de ela ser dada:* os dois leitores do frontboard estavam cegos — `p0-next` escondendo 58 tarefas livres e `wiki-brief` imprimindo `BOARD ?` — e **nenhum dos dois estava no plano**; sem corrigi-los, a tasklist de 95 tarefas nasceria ilegível para quem fosse operá-la. |
| **R18** | **Canal certo para cada consumidor** (ordem do dono nesta sessão): *"O Bing não pode ficar recebendo pelo WebSub ou IndexNow as URLs de `.md`, pois ele não vai indexar."* Notificação a buscador leva **só URL canônica de HTML**; Markdown se anuncia nos canais de agente (`Link: rel=alternate`, `llms.txt`, MCP), **nunca** nos de indexação. **A separação tem de ser estrutural — derivada do canal —, não disciplina de quem escreve o código.** Ver onda 7 em voo. |

---

## Medições próprias já realizadas (reprodutíveis)

Todas colhidas nesta sessão, em 2026-08-26, contra produção e contra o disco.

### M1 — Inventário público

| Métrica | Valor medido | Como reproduzir |
|---|---|---|
| URLs no sitemap servido | **10.294** (34 shards) | baixar `sitemap.xml`, seguir os 34 shards, contar `<loc>` |
| HTMLs em `public/` | **10.299** | `find public -name '*.html' \| wc -l` |
| Arquivos `.md` em `public/` | **0** — todo Markdown é gerado em runtime pelo Go | `find public -name '*.md' \| wc -l` |
| `llms.txt` | 12.013 bytes | `curl -sSI https://wikijuridica.com.br/llms.txt` |
| `llms-full.txt` | **1.455.210 bytes** (~1,4 MB, ≈ 360 mil tokens) | idem |
| Página 404 | **7.521 bytes**, quase toda CSS inline, e carrega `.webmcp/bridge.js` | `curl -sS https://wikijuridica.com.br/nao-existe/` |

### M2 — Cobertura de Markdown (amostra determinística de 303 URLs, 1 a cada 34)

| Resultado | Contagem |
|---|---|
| `index.md` → 200 `text/markdown` | 297 (98,0%) |
| `index.md` → **404** | 6 (2,0%) — **todas rotas de paginação `/area/pagina/N/`** |
| `Accept: text/markdown` → 200 `text/markdown` | 297 |
| `Accept: text/markdown` → **200 `text/html`** | **6 — o agente pede Markdown, recebe HTML e não é avisado** |

Tamanhos do Markdown de acervo: min 3.860 · p50 6.076 · max 11.043 bytes. **A queixa "sem conteúdo" não se confirmou nas páginas de acervo** — o Markdown delas é bom (autor, OAB, data de revisão, fontes oficiais datadas, relacionados, canônico).

**Confirmado por segunda medição independente (onda 2), com amostra maior:** 120 artigos amostrados sistematicamente (1 a cada 84 do sitemap) — mínimo **4.250 B**, p10 4.709, mediana 6.234, média 6.343, máximo 10.216, e **zero documentos abaixo de 2.000 B**. Nenhum vazio, nenhum esqueleto. Cobertura conferida: 38/38 rotas de um segmento e 40/40 artigos, **172 artigos no total entre três experimentos — nenhuma falha fora da classe `/pagina/`**.

**Conclusão sobre a queixa do dono, com os dois lados ditos:** *"muitos .md dando 404"* está **certo e localizado** — são as 185 fatias de paginação, mais a cauda de rotas institucionais e formas alternativas de URL (M12, M19). *"ou sem conteúdo"* está **medido e refutado** — nenhum Markdown de acervo é vazio ou fraco em bytes. O que resta da percepção de fraqueza é qualitativo e tem endereço próprio: o Markdown **não carrega front matter, não declara licença e não traz a credencial OAB estruturada**, enquanto o HTML declara tudo isso em JSON-LD (M16, O2b abaixo). **O agente que pede Markdown recebe menos autoridade que o que lê HTML** — essa é a fraqueza real.

**Rotas de paginação no sitemap: 185** (1,8% do total). Nenhuma tem Markdown.

Formas alternativas que um bot tenta por convenção, todas medidas:

| Forma | Resultado |
|---|---|
| `/area/slug/index.md` | 200 `text/markdown` ✅ |
| `/area/slug.md` | **404** (7.521 bytes de HTML de erro) |
| `/area/slug/index.md/` | **404** |
| `/area/slug/md` | **404** |
| `/area/slug/?format=md` | **200 `text/html`** (silencioso) |

### M3 — Tráfego de bot na borda: o número REAL, pelo leitor canônico

> **⚠ Registro de erro próprio, mantido de propósito.** Minha primeira leitura deste arquivo somou as linhas cruas do JSONL e produziu *"2.078.098 requisições em 7 dias"*. **Estava inflada em ~68×.** `data/ops/edge_bot_agents_daily.jsonl` é append-only **cumulativo**: cada agente tem ~68 linhas no mesmo dia, cada uma um snapshot acumulado. Somá-las conta o mesmo tráfego 68 vezes. O leitor canônico do projeto é `tools/edgetelemetry.py → serie_saneada(root)`, que deduplica por `(date, agent_key)` mantendo a **última** linha e descarta a linha fisicamente impossível. Fica no plano como precedente: **é exatamente a classe de erro que o dono mandou evitar — número inflado que parece autoridade.**

Números reais, pela `serie_saneada`, média dos últimos 7 dias com dado:

| Agente | Função | Req. 7d | **Req./dia** | No registry? |
|---|---|---|---|---|
| meta-externalagent | training | 17.021 | **2.432** | sim |
| **semrushbot** | seo | 8.144 | **1.163** | **NÃO** |
| cloudflare-agentreadiness | infra | 2.519 | 360 | **NÃO** |
| bingbot | search | 2.517 | 360 | sim |
| facebookexternalhit | social | 2.083 | 298 | sim |
| claudebot | training | 1.223 | 175 | sim |
| gptbot | training | 1.088 | 155 | sim |
| **yandexbot** | search | 1.074 | 153 | **NÃO** |
| oai-searchbot | search | 908 | 130 | sim |
| amazonbot | training | 774 | 111 | sim |
| **googlebot** | search | **228** | **33** | sim |
| chrome-lighthouse | diagnostic | 212 | 30 | **NÃO** |
| chatgpt-user | user | 205 | 29 | sim |
| google-inspectiontool | diagnostic | 87 | 12 | **NÃO** |
| applebot | search | 38 | 5 | sim |
| duckduckbot | search | 11 | 2 | sim |
| **ahrefsbot** | seo | 2 | 0 | **NÃO** |
| **perplexitybot** | search | **0** | **0** | sim |
| bytespider · amzn-searchbot · google-extended | — | 0 | 0 | sim |

**TOTAL de bot verificado: 38.134 requisições em 7 dias ≈ 5.448/dia.**

**Corroboração por instrumento independente** (a regra que passei a aplicar depois do erro acima):

| Instrumento | O que diz | Concorda? |
|---|---|---|
| `serie_saneada` (borda Cloudflare) | 5.448 req de bot/dia | — |
| `edge_traffic_daily.jsonl` (25/08) | 74.029 req totais na zona, das quais **62.340 são aquecimento próprio** e **11.689 orgânicas** | ✅ 5.448 cabe dentro de 11.689 |
| Log do nginx (M18) | Googlebot 154 req em ~6 dias ≈ 26/dia | ✅ contra 33/dia da borda |

A discrepância borda×origem que eu havia anotado como "a reconciliar" **não existe** — era artefato do meu erro de leitura. Fica registrada a resolução.

**O que esses números realmente significam — e é o achado central da sessão:**

1. **Googlebot faz 33 requisições por dia** para um acervo de 10.294 páginas. Nesse ritmo, uma varredura completa levaria **312 dias**.
2. **PerplexityBot: zero.** GPTBot: 155/dia. ChatGPT-User: 29/dia. OAI-SearchBot: 130/dia. Os bots que geram citação praticamente não vêm.
3. **SemrushBot faz 35× mais requisições que o Googlebot** (1.163 contra 33) — e não indexa, não cita, não gera nada. É o segundo maior consumidor do portal.
4. **meta-externalagent sozinho é 45% de todo o tráfego de bot** (2.432/dia), classificado como treinamento.
5. **O aquecimento interno faz 62.340 requisições/dia — 11,5× mais que todos os bots do mundo somados** (5.448), e enche um cache de borda que mede 0% de cobertura.

O portal está, na prática, **invisível para os bots de IA** — e gasta 91% da própria banda conversando consigo mesmo.

### M3.b — Disciplina anti-armadilha adotada a partir daqui (ordem do dono)

> *"Por isso tem que tomar cuidado com dados falsos positivos ou negativos, podem ser inflados ou podem ser silenciosos. Use engenharia inteligente."*

Três armadilhas já morderam **nesta sessão**. Todas viram regra e todas vão para o prompt de cada agente lançado:

| # | Armadilha | Como se manifesta | Antídoto |
|---|---|---|---|
| **A1** | **Número inflado** | `edge_bot_agents_daily.jsonl` cumulativo: somar linhas multiplica por ~68 | usar `tools/edgetelemetry.py → serie_saneada()`; nunca somar JSONL append-only sem checar se é cumulativo |
| **A2** | **Falso negativo silencioso** | `data/ops/access/*.jsonl` é o ledger do **processo Go**; o HTML estático servido pelo nginx não aparece nele → "o Googlebot sumiu" | log real em `/var/log/nginx/wikijuridica/access.log`; **ausência de linha ≠ ausência do fato** |
| **A3** | **Falso positivo silencioso** | `Accept: text/markdown` devolve **200 `text/html`** onde não há Markdown; quem olha só o status conclui que funcionou | verificar sempre **Content-Type e corpo**, nunca só o código de status |
| **A4** | **Binário defasado** | `bin/wikijuridica-server` está **18 commits atrás** do fonte — sondar `:8089` mostra o **passado**, não o código de hoje | para o código atual, **ler o fonte**; para o que está no ar, **sondar** — e nunca confundir os dois |
| **A5** | **Contagem de alerta sem dedupe** | `owner_alerts.jsonl` **também é cumulativo**: linha crua dá "48" ou "839"; **deduplicado por chave dá 25 chaves não resolvidas, 7 delas críticas** | ledger de alerta se lê **por chave**, nunca por linha |

> **⚠ Nota de calibração sobre os números de alerta neste plano.** Onde o texto diz **"48 alertas críticos"**, **"48 repetições"** ou **"839 não resolvidos / 118 críticos"**, são **leituras de linha crua** feitas antes de a armadilha A5 ser descoberta. **O número correto, deduplicado por chave (medição do Fable da onda 5): 841 linhas = 25 chaves não resolvidas, das quais 7 são críticas** — `borda-cache-regra`, `borda-origem`, `portal-fora`, `rede-externo`, `rede-uplink`, `tunel-conexoes`, `tunel-uplink` — **6 delas abertas desde 22/08**. **Deixo as leituras antigas no texto de propósito**, porque elas mostram a evolução da medição e porque a gravidade **não muda**: sete famílias de defeito crítico abertas há dias é tão grave quanto 118 linhas. **O que muda é o direito de citar o número.**

**Regra fixada:** todo número deste plano declara (a) como foi medido, (b) qual instrumento, (c) qual **segundo instrumento independente** concorda. Sem o segundo, o número entra marcado como *instrumento único — não corroborado* e **não sustenta decisão**. Nenhum agente lançado a partir daqui recebe prompt sem essa seção.

### M4 — Cobertura de crawl por bot (`data/ops/crawl_coverage_never_requested.json`, as_of 2026-08-26, base 10.294 URLs)

| Crawler | URLs que **nunca** pediu | Cobertura |
|---|---|---|
| **perplexitybot** | **10.294** | **0,00%** |
| **chatgpt-user** | 10.090 | **1,98%** |
| **oai-searchbot** | 9.345 | **9,22%** |
| bingbot | 8.199 | 20,35% |
| claudebot | 7.785 | 24,37% |
| googleother | 6.992 | 32,08% |
| gptbot | 4.901 | 52,39% |
| googlebot | 3.023 | 70,63% |
| **yandexbot** | 74 | **99,28%** |
| **amazonbot** | 48 | **99,53%** |

Leitura correta deste dado, contra a hipótese fácil:

- **A anomalia não é "Googlebot bloqueado".** Googlebot cobriu 70,63% do acervo, e o log do nginx registra **zero 403 e zero 429** para ele (M18). Quem é ineficiente é o **Bingbot**: 360 req/dia e apenas 20,35% de cobertura acumulada — bate repetidamente nas mesmas poucas URLs.
- **O achado caro é outro: os bots de IA que citam mal conhecem o acervo.** PerplexityBot nunca pediu **uma única URL**. ChatGPT-User viu 2%. OAI-SearchBot viu 9%. Um modelo não cita o que nunca leu — é exatamente o "não tem autoridade nenhuma" que o dono percebeu.
- Os dois bots com melhor cobertura (Yandex 99,28% e Amazon 99,53%) são justamente os que **não recebem tratamento diferenciado** — um deles nem está no registry.

### M5 — Google Search Console (MCP `Advanced_GSC`, propriedade `sc-domain:wikijuridica.com.br`, siteOwner, 30 dias)

Impressões por dia: 0 (até 07/08) → 248 → 467 → 368 → 854 → 1.021 → 1.350 → 771 → 742 → 1.649 → **2.551 (pico em 17/08)** → 1.351 → 474 → 562 → 341 → 249 → 271 → 261 → **241 (25/08)**.

**Total de cliques em 30 dias: 7. Posição média ~65-70.** Ou seja: o Google descobriu, indexou parcialmente, e as **impressões caíram 90% desde o pico** — o portal está sendo rebaixado, não promovido.

### M6 — Transporte e cache (o achado de maior ROI)

**M6.a — `cf-cache-status: DYNAMIC` em tudo.** Medido três vezes seguidas em página de acervo, e uma vez em Markdown, `llms.txt` e `sitemap.xml`: **nenhum** artefato é cacheado na borda, apesar de o HTML declarar `cache-control: public, max-age=86400, s-maxage=604800`.

**Corroborado pelo instrumento do próprio projeto**, `data/ops/edge_cache_coverage.jsonl`, medido em 2026-08-26T10:08 — `cobertura_pct: 0.0` · `estados: {"DYNAMIC": 40}` em 40/40 amostras · `nao_cacheaveis: 40` · `quentes: 0` · `paginas_protegidas_estimadas: 0` · `universo_urls: 10255`. Dois instrumentos independentes, mesmo veredito: **zero por cento de cobertura de cache de borda.**

Consequência: **toda** requisição — de bot, de humano e do próprio aquecimento — atravessa o túnel Cloudflare até a origem em `127.0.0.1:8089`.

**M6.a.1 — Causa-raiz isolada por experimento controlado (feito nesta sessão).** Sondei recursos que variam em extensão e em `Vary`, para separar as hipóteses:

| Recurso | Extensão | `Vary` | `Cache-Control` | `cf-cache-status` |
|---|---|---|---|---|
| `/favicon.ico` | `.ico` | Accept-Encoding | max-age=31536000 | **HIT** ✅ |
| `/favicon.svg` | `.svg` | Accept-Encoding | max-age=31536000 | **HIT** ✅ |
| `/robots.txt` | `.txt` | accept-encoding | max-age=31536000 | **HIT** ✅ |
| `/llms.txt` | `.txt` | Accept-Encoding | max-age=86400, s-maxage=604800 | **DYNAMIC** ❌ |
| `/sitemap.xml` | `.xml` | — | max-age=300 | DYNAMIC |
| `/feed.xml` | `.xml` | Accept-Encoding | max-age=86400 | DYNAMIC |
| `/openapi.json` | `.json` | Accept-Encoding | max-age=300 | DYNAMIC |
| página de acervo | (sem extensão) | Accept-Encoding, **Accept** | max-age=86400, s-maxage=604800 | DYNAMIC |

**O experimento derruba a hipótese do `Vary: Accept`**: `/llms.txt` tem apenas `Accept-Encoding` e mesmo assim é DYNAMIC, enquanto `/robots.txt` — mesma extensão, mesmo `Vary` — é HIT. E derruba a hipótese de `Cache-Control` mal declarado: o HTML declara `s-maxage=604800` corretamente e é ignorado.

**O que resta e explica 100% das observações: a zona Cloudflare está no comportamento PADRÃO, sem nenhuma Cache Rule.** Por padrão a Cloudflare cacheia apenas as extensões da sua lista estática (`.ico`, `.svg`, `.css`, `.js`, imagens, fontes, arquivos…) e **ignora `Cache-Control` de origem para tudo que está fora dela** — HTML sem extensão, `.md`, `.xml`, `.json` e `.txt` ficam todos de fora. (`/robots.txt` é caso à parte, tratado especialmente pela Cloudflare.)

**Consequência direta:** todo o acervo, todos os Markdown, todos os sitemaps, todos os feeds e todo o `llms.txt` são não-cacheáveis por configuração ausente — não por defeito de código. **A correção é uma Cache Rule**, não uma refatoração. É o achado de maior relação retorno/esforço da sessão.

**M6.b — `If-Modified-Since` quebrado no HTML (viola RFC 9110 §13.1.3).** O handler HTML exige **igualdade exata** de data:

| `If-Modified-Since` enviado | Resposta HTML | Resposta Markdown | Correto seria |
|---|---|---|---|
| Tue, 05 Aug 2026 (anterior) | 200 · 22.648 B | 200 · 4.699 B | 200 ✅ |
| Thu, 06 Aug 2026 (igual) | **304 · 0 B** | — | 304 ✅ |
| Fri, 07 Aug 2026 (posterior) | **200 · 22.648 B** ❌ | — | **304** |
| Mon, 25 Aug 2026 (posterior) | **200 · 22.648 B** ❌ | **304 · 0 B** ✅ | **304** |

O caminho do **Markdown está correto**; o do **HTML está errado**. Como todo bot revalida com a data da sua última visita — sempre posterior ao `last-modified` fixo de 06/08 — **todo bot baixa a página inteira toda vez, sempre**.

**Corroboração em campo (M18):** de 418.071 requisições registradas no log do nginx, apenas **872 foram 304 — 0,2%**. O Googlebot fez 154 requisições e recebeu 31 × 304 e 119 × 200.

**O custo real não é banda do servidor** — o tráfego externo do portal é modesto (~45 MB/dia fora o aquecimento). **O custo é orçamento de rastreamento e token do agente.** Com o Googlebot fazendo 33 requisições/dia, cada uma que devolve 22,6 KB em vez de um 304 vazio é uma página nova que ele deixa de buscar. Para um agente de IA, é o mesmo em tokens: reler íntegra o que não mudou consome o orçamento que ele daria a conteúdo novo. Numa superfície que precisa ser **barata para o bot**, é o defeito mais direto.

**M6.b.1 — Causa-raiz localizada, e não é código Go: é o default do nginx.** Duas verificações fecham o caso:

1. `grep -n "if_modified_since" ops/nginx/standalone/nginx.conf` → **nenhuma ocorrência.** O nginx usa o default **`if_modified_since exact`**, que responde 304 **apenas** quando a data bate exatamente. A semântica da RFC é `if_modified_since before;`.
2. O bug se reproduz **direto na origem**, sem borda nenhuma: `curl -H 'Host: wikijuridica.com.br' -H 'If-Modified-Since: Mon, 25 Aug 2026 …' http://127.0.0.1:8088/…` → **200 com 22.488 B**. Com a data exata de 06/08 → 304.

Isso explica **por que o Markdown acerta e o HTML erra**: o HTML do acervo é arquivo estático servido pelo nginx (governado pelo `if_modified_since exact`), e o Markdown é gerado pelo Go, que implementa a comparação correta.

**Consequências para o plano:** a correção é **uma diretiva**, não uma refatoração de handler como eu havia escrito, e é **imune ao binário Go defasado** (O6) — entra por `nginx -t` + reload, sem rebuild.

**⚠ Duas correções à minha própria formulação, ambas vindas da crítica Fable e confirmadas por mim:**

1. **A diretiva vai no vhost vivo `ops/nginx/wikijuridica.conf`, NÃO no `standalone/nginx.conf`.** O standalone é **gerado** por `tools/generate-nginx-standalone` e traz no cabeçalho *"NÃO EDITE À MÃO"*. Editar o standalone seria revertido na próxima regeneração (ver O24/D-1). E **antes de qualquer regeneração é preciso resolver a paridade pendente** — `check-nginx-standalone-parity` está em FAIL hoje (O24/D-2).
2. **`if_modified_since before` NÃO pode ser o primeiro passo.** O `Last-Modified` servido é o **mtime**, que carrega a **data editorial** (05/08), enquanto a escrita real foi 20/08 (`ctime`) — medido em **10.256 de 10.258 arquivos**. Com `before`, o servidor passaria a devolver **304 para páginas que de fato mudaram**. **A ordem segura é: (1) fazer o publicador gravar mtime = instante da publicação real, mantendo a data editorial no conteúdo e no manifesto, onde ela pertence; (2) só então trocar a diretiva.** Inverter a ordem transforma uma correção em regressão silenciosa de conteúdo.

Corrige-se também a leitura de M6.d: o `Last-Modified` "congelado" é o mtime, e o mtime carrega data editorial **de propósito** (`[[gerador-datado-cas-correcao-v2]]`). **Se ele deve continuar sendo o sinal de frescor é justamente o que o dono mandou apurar com fonte oficial — está na onda 5.**

**M6.c — O HTML *tem* ETag na origem; quem o remove é a borda.** Medição nas duas camadas, mesma URL:

| Camada | `ETag` | `Last-Modified` |
|---|---|---|
| Origem `127.0.0.1:8088` | **`"6a73ce80-57d8"`** ✅ | Thu, 06 Aug 2026 |
| Borda `wikijuridica.com.br` | **ausente** ❌ | Thu, 06 Aug 2026 |

O nginx serve estático com ETag por default, como esperado. **A Cloudflare o remove — comportamento coerente com reescrever o corpo**, que é exatamente o que O7 provou que ela faz para injetar `bridge.js`.

**M6.c.1 — A cadeia causal completa, com todos os elos medidos:**

```
Cloudflare injeta bridge.js no corpo (O7)
        ↓
remove o ETag da resposta (M6.c)
        ↓
resta só Last-Modified como validador
        ↓
nginx com if_modified_since exact rejeita toda data posterior (M6.b.1)
        ↓
nenhuma revalidação funciona: 872 de 418.071 respostas são 304 (0,2%) (M18)
        ↓
todo bot rebaixa a página inteira toda vez — e a borda não cacheia nada (M6.a)
```

**Isto reordena a decisão sobre a injeção da borda (O7): ela não é só uma violação do contrato de HTML leve — é um elo da cadeia que mata a revalidação.** O item vai ao red-team Fable com essa cadeia declarada.

**M6.d — `Last-Modified` congelado.** Todas as páginas de acervo: `Thu, 06 Aug 2026 00:00:00 GMT`. Todos os hubs de área testados (`/consumidor/`, `/trabalhista/`, `/familia/`, `/leis/`, `/sumulas/`): `Thu, 20 Aug 2026 00:00:00 GMT`. Data por lote, não por página: o bot não consegue saber o que mudou.

**M6.e — Compressão funciona.** Brotli ativo: 26.163 B → **7.052 B** (−73%). `Vary: Accept-Encoding, Accept` presente e correto. `Link: rel="alternate" type="text/markdown"` presente no header — bem feito.

### M7 — Rotas que respondem erro em produção

| Rota | Status medido |
|---|---|
| `/.well-known/mcp.json` | **404** |
| `/.well-known/agent-catalog` | **404** |
| `/api/search` | **404** (HTML de erro de 7.521 B) |
| `/areas/` | **404** |
| `/mcp` (GET) | 405 (POST é o correto — a verificar se responde) |

### M8 — ~~Divergência de números em artefato público~~ → **REFUTADO pela onda 2**

Eu havia registrado como defeito o fato de o `llms.txt` dizer **"10070 páginas"** enquanto o sitemap expõe **10.294** URLs. **Não é divergência — os dois estão certos e contam populações diferentes.** Decomposição das 10.294 `<loc>` únicas, conferida por duas frentes independentes:

```
10.070 artigos (rotas de duas seções)
+  185 fatias de paginação (/area/pagina/N/)
+   38 rotas de um segmento (hubs de área + institucionais)
+    1 raiz
= 10.294
```

E o próprio portal **já declara a diferença**: `GET /api/v1/pages` devolve, no mesmo objeto, `count: 10070`, `enumeration_superset: 224` e um `enumeration_scope` em texto explicando que a enumeração cobre *"todas as URLs indexáveis, incluindo hubs de área e paginação, que não são itens desta coleção"*. **10.070 + 224 = 10.294, exato.**

**Ação corrigida:** não alterar contagem nenhuma. O único ganho é publicar a frase que remove a ambiguidade recorrente — no `llms.txt`, gerada em `cmd/publish-v2-direct` a partir do sitemap que a transação acabou de escrever, nunca de literal. Fica também um número **realmente** órfão a explicar: o `total_indexado: 10.077` que o MCP devolve, que não bate com nenhum dos dois.

### M10 — Log de acesso da origem (`data/ops/access/`, 20 a 26/08, 137.335 linhas)

O ledger de acesso do wiki grava `bot_class`, `bot_rule`, `route_class`, `status`, `bytes`, `warming`. Agregação própria:

| `bot_rule` | Req. | MB | 404 | 304 | 200 |
|---|---|---|---|---|---|
| `*` (curinga) | 72.173 | **1.037,6** | 1.422 | 335 | 62.263 |
| Googlebot | 48.101 | **1.169,0** | 0 | **0** | 48.101 |
| meta-externalagent | 15.722 | 99,9 | 1 | 4 | 15.713 |
| Amazonbot | 439 | 2,7 | 101 | 0 | 336 |
| ClaudeBot | 381 | 2,2 | 44 | 1 | 336 |
| OAI-SearchBot | 202 | 1,3 | 42 | 0 | 159 |
| ChatGPT-User | 133 | 1,0 | 132 | 0 | **0** |
| Amzn-SearchBot | 91 | 0,7 | 89 | 0 | **0** |
| PerplexityBot | 50 | 0,4 | 49 | 0 | 1 |
| GPTBot | 43 | 0,3 | 42 | 0 | 1 |

**Total no período: 126.910 respostas 200 · 1.922 respostas 404 · apenas 340 respostas 304.**

**Confirmação em campo do bug P0 de revalidação (M6.b):** o Googlebot fez 48.101 requisições e recebeu **zero 304**, baixando **1,17 GB** em 7 dias. Nenhuma revalidação funcionou — exatamente o que a medição sintética previu.

**⚠ Ressalva metodológica que descobri depois e que corrige a leitura acima — `data/ops/access/` é o ledger do processo Go, não do portal inteiro.** Distribuição diária das linhas: 06-11/08 ~1,5-2,7 mil/dia · 12/08 33.036 · 13/08 61.681 · 14-18/08 ~3 mil/dia · 19/08 14.070 · **20/08 107.377** · 21-26/08 ~3-5 mil/dia. E o `route_class` dos dias normais é quase todo `mcp`, `health`, `search_jump`, `markdown` — não `page`. **O Googlebot aparece nesse ledger em exatamente três dias (12, 13 e 20/08) e em nenhum outro**, porque o nginx serve o HTML estático de `public/` direto do disco e esse caminho não passa pelo Go. Logo: **as colunas de banda e de 404 da tabela acima valem só para as rotas dinâmicas** (MCP, Markdown gerado, busca, erro). É a armadilha catalogada em `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` — *ausência de linha ≠ ausência do fato*. O instrumento certo é o M18.

### M11 — Falsificação de identidade de bot valioso (achado de segurança e de política)

Os 404 atribuídos a `ChatGPT-User`, `PerplexityBot`, `GPTBot`, `Amzn-SearchBot` e `Amazonbot` **não são dos bots reais**: os caminhos pedidos são varredura de credencial —
`/.env`, `/.aws/credentials`, `/@fs/proc/self/environ`, `/.git-credentials`, `/secrets.json`, `/gcp-service-account.json`, `/login/..;/actuator/env`, `/.claude/settings.json`, `/rclone.conf`, `/dump.sql`.

**Dos 7.117 respostas 404 do período, 1.738 (24,4%) são varredura de credencial**, distribuída entre User-Agents que se declaram bots de IA valiosos.

Consequência de política, medida: o `bot_rule` é aplicado **por User-Agent cru**, sem verificação de identidade na origem (`requests_local_verification: 0` na telemetria). Um scanner que escreve `ChatGPT-User` no cabeçalho recebe hoje o tier `unlimited_no_rate_limit`. **O portal concede acesso ilimitado a quem alega ser um bot valioso.** A verificação por reverse DNS e por faixas de IP publicadas (`data/ops/bot_ip_ranges/` já existe para o Google) e/ou Web Bot Auth resolve isso.

### M12 — Caminhos de descoberta de agente que os clientes pedem e o portal não serve

Dos 5.379 respostas 404 legítimos (não-varredura) do período, a maioria esmagadora é **cliente de agente procurando artefato de descoberta**. Separando por data, distingo o que já foi resolvido do que **continua quebrado hoje**:

**Já resolvido** (404 até 19-20/08, 200 desde então): `/.well-known/agent-card.json`, `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`, `/.well-known/mcp/server-card.json`, `/auth.md`, `/openapi.json`, `/.well-known/api-catalog`, `/.well-known/agent-skills/index.json`. Nenhuma ação necessária.

**Ainda 404 em 26/08** — com o cliente real que pede:

| Caminho | Freq. recente | Quem pede | O que é |
|---|---|---|---|
| `/.well-known/agent.json` | ~11-14/dia | `PREA-DiscoveryEngine`, `agent-trust-index` | convenção de agent card |
| `/.well-known/mcp` | ~11-14/dia | `PREA-DiscoveryEngine` | descoberta MCP |
| `/mcp/.well-known/oauth-protected-resource` | 3/dia constante | `aisec-registry` | **RFC 9728 §3 — metadata relativo ao path do resource server. Gap de conformidade, não moda.** |
| `/.well-known/http-message-signatures-directory` | recorrente | `Cloudflare-AgentReadiness`, `AgentReadinessScanner` | **Web Bot Auth / RFC 9421 — diretório de chaves públicas** |
| `/.well-known/mcp.json`, `/.well-known/mcp/server-cards.json` | recorrente | scanners de prontidão | variantes de descoberta MCP |
| `/.well-known/x402`, `/.well-known/x402.json` | ~23+20 | `node`, `agent-tools.cloud-crawler`, `AgenstryBot` | pagamento de agente (x402) |
| `/.well-known/openid-configuration` | recorrente | scanners, `Station70-Gatekeeper-Catalog` | OIDC discovery |
| `/.well-known/acp.json`, `/.well-known/ucp`, `/.well-known/mpp`, `/.well-known/payment-manifest`, `/.well-known/owners.json`, `/.well-known/glama.json`, `/.well-known/did.json`, `/.well-known/a2a.json`, `/.well-known/ai-plugin.json`, `/.well-known/traffic-advice` | 1-20 cada | `VerifyMCP-OwnersBot`, `undici`, `Agenstry`, `Vouch-Census`, Chrome Prefetch Proxy | protocolos de agente emergentes e registries |

**Leitura honesta, sem inflar:** quem bate nesses caminhos hoje são **registries e escaneadores de descoberta de agentes**, não os bots que citam. Isso tem valor de descoberta (entrar em catálogo de servidores MCP), que é diferente de valor de citação. A onda 1 decide, por documentação oficial, quais desses têm consumidor real — **é proibido criar arquivo-fantasma só para converter 404 em 200** (seria stub, vedado pelo contrato). Os dois que já se sustentam por spec publicada são o **RFC 9728** e o **Web Bot Auth**.

Achado colateral: **`/direito/familia/` foi pedido por GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot e Claude-SearchBot** — cinco bots de IA distintos tentando um padrão de URL `/direito/<area>/` que o portal não serve. Modelos "acreditam" que essa rota existe. Alias 301 resolve e recupera a visita.

Também 404 hoje: `/fontes/planalto/index.md` (16x), `/contato/advogado/index.md` (8x), `/consumidor/index.md` (6x), `/buscar/index.md` (5x), `/agent.md` (6x), `/politica-de-uso.md` (3x), `/glossario/pagina/3/index.md` (3x) — a cauda de Markdown ausente de M2.

### M13 — Tráfego sob o curinga `*`: 2,3 GB para User-Agent vazio

| User-Agent sob `*` | Req. | MB |
|---|---|---|
| **(vazio)** | **99.402** | **2.334,9** |
| `wikijuridica-watchdog/1.0` (interno) | 27.024 | 72,1 |
| `SentinelOracle/0.1` | 6.504 | 5,8 |
| `curl/7.88.1` | 5.880 | 62,5 |
| `wikijuridica-edge-audit/1.0` (interno) | 4.662 | 0,0 |
| `mcpbeat/0.1` (liveness de MCP) | 3.637 | 3,6 |
| `Cloudflare-AgentReadiness`, `AgentReadinessScanner`, `zevruna-monitor`, `agent-tools.cloud-crawler` | 500-1.300 cada | — |

**Requisição sem User-Agent consome 2,33 GB** e é a maior fatia isolada de banda do portal. O registry tem a classe `no_http_user_agent` (tier `product_use_control`), mas na prática esse tráfego cai em `*`. Ou a classe não está sendo aplicada, ou o `bot_rule` do log não a reflete — a onda 2 rastreia; de qualquer forma, 2,33 GB para cliente anônimo é dinheiro.

Nota metodológica: parte do tráfego sob `*` é **interno e identificado corretamente** (`wikijuridica-watchdog`, `wikijuridica-cache-warm`, `wikijuridica-edge-audit`, `wikijuridica-check-static-freshness`) — com UA próprio, como o contrato anti-fraude exige. Não é fraude; é ruído a excluir das contas de tráfego externo.

### M14 — Protocolos de agente: estado medido, funcionando

| Superfície | Estado medido |
|---|---|
| **MCP** `/mcp` | **Funciona.** `initialize` responde SSE com `protocolVersion: 2025-06-18`, `serverInfo: wikijuridica v1`. `tools/list` devolve `buscar_paginas`, `ler_pagina`, `relatar_defeito` com `inputSchema` e `outputSchema` completos e anotações (`readOnlyHint`, `idempotentHint`). Qualidade alta. |
| **A2A** `/a2a/v1` | **Funciona, mas com portão.** Exige header `A2A-Version: 1.0`; sem ele devolve erro `-32009`. Com o header, `SendMessage` respondeu a *"prazo para reclamar vício de produto durável"* com 5 páginas pertinentes e trechos reais. **Risco:** cliente A2A que não envia o header é rejeitado em vez de atendido — verificar contra a spec se a exigência é legítima ou se deve haver default tolerante. |
| **Artefatos que respondem 200** | `/openapi.json` (5.763 B) · `/api.md` (9.586 B) · `/auth.md` (10.055 B) · `/api/politica-de-uso.json` (4.255 B) · `/.well-known/api-catalog` (1.738 B, `application/linkset+json` com profile RFC 9727 — correto) · `/.well-known/ai-catalog.json` · `/.well-known/agent-card.json` · `/.well-known/mcp/server-card.json` · `/.well-known/agent-skills/index.json` (12.746 B) · `/.well-known/oauth-authorization-server` · `/.well-known/oauth-protected-resource` · `/.well-known/security.txt` |

### M15 — Peso e composição do HTML (página de acervo típica, 22.648 B)

| Componente | Bytes | % do HTML |
|---|---|---|
| **CSS inline** | **7.911** | **34,9%** |
| JSON-LD (3 blocos) | 2.781 | 12,3% |
| Texto visível ao leitor | 5.999 | **26,5%** |
| `<head>` inteiro | 13.065 | 57,7% |
| `<body>` inteiro | 9.511 | 42,3% |

Comparação de representações da **mesma página**:

| Representação | Sem compressão | Com Brotli |
|---|---|---|
| HTML | 22.648 B | 7.052 B |
| Markdown | 4.699 B | **1.972 B** |
| **Razão** | **4,8× menor** | **3,6× menor** |

**O CSS inline é idêntico nas 10.294 páginas.** Um agente que percorre o acervo inteiro em HTML paga 7.911 × 10.294 ≈ **81,4 MB só de CSS que não usa**. O Markdown já resolve isso — o problema é que o agente precisa *saber* que ele existe, e nem toda porta de entrada informa.

### M15.a — O custo em TOKENS para um agente consumir este acervo

O dono formulou o problema em tokens do bot: *"não gostam de gastar muitos tokens para poder navegarem ou citarem"*. Traduzi as medições de bytes para tokens. **A conversão usa ~4 bytes/token para PT-BR e é declarada como aproximação** — os bytes são medidos, a razão é estimada.

**Por página de acervo:**

| Representação | Bytes | ~Tokens | |
|---|---|---|---|
| HTML bruto | 22.648 | **5.662** | |
| Markdown bruto | 4.699 | **1.175** | **79% menos** |
| texto útil (o que o modelo aproveita) | 5.999 | 1.500 | |
| **CSS inline** | **7.911** | **1.978** | **boilerplate que o bot paga e não usa** |

**Acervo inteiro (10.294 páginas):**

| | Volume | ~Tokens |
|---|---|---|
| em HTML | 233,1 MB | **58,28 M** |
| em Markdown | 48,4 MB | **12,09 M** |
| **economia do Markdown** | 184,8 MB | **46,19 M** |
| **só o CSS inline repetido** | 81,4 MB | **20,36 M** |

**O que já aconteceu de fato**, aplicando as medições ao volume real do `meta-externalagent`:

- Ele pediu **15.697 páginas em Markdown** ≈ 74 MB ≈ **18,44 M tokens**.
- Se tivesse pedido HTML: 356 MB ≈ **88,88 M tokens**.
- **O canal Markdown poupou ao agente ~70 M tokens.** É a prova de que o investimento em Markdown **funciona** — e o argumento mais forte para corrigir os buracos dele (185 rotas sem gêmea, negociação silenciosa, TTL 168× menor, front matter ausente) em vez de construir artefato novo.

**E o que a revalidação quebrada custa:** a segunda varredura do mesmo agente (5.922 requisições, 22/08) **devolveu corpo inteiro** — 27,8 MB ≈ **6,96 M tokens** que, com o 304 correto, seriam **zero bytes e zero tokens**. *Foi o portal quem gastou os tokens do agente, por defeito próprio.*

### M16 — JSON-LD: forte, com lacunas nomeadas

Emitido hoje em página de acervo: `Article` + `FAQPage` + `BreadcrumbList`. O `Article` traz `@id`, `mainEntityOfPage`, `headline`, `description`, `abstract`, `inLanguage: pt-BR`, `url`, `datePublished`, `dateModified`, `author` (Person com `@id`), `reviewedBy`, `publisher` (Organization com `@id`), **`citation[]` apontando para as URLs oficiais**, `isAccessibleForFree`, `license: CC-BY-4.0` e `usageInfo`. É bem acima da média.

Lacunas medidas, todas com efeito direto em confiança de máquina:

1. **A credencial OAB não está estruturada.** O `author` é `{"@type":"Person","name":"Rafael Toledo"}` — sem `identifier` (OAB/RJ 227191), sem `jobTitle`, sem `honorificSuffix`, sem `sameAs`, sem `knowsAbout`. O texto humano diz a credencial; o grafo de máquina não. Para E-E-A-T e para um modelo decidir se confia, é o campo que falta.
2. `datePublished` = `dateModified` = `2026-08-06` — data de lote, igual ao `Last-Modified` congelado (M6.d).
3. Ausentes: `isBasedOn`, `about`, `mentions`, `speakable`, `Person.knowsAbout`.
4. Não há `WebSite` com `SearchAction`, nem `Organization` com `sameAs`, na página de acervo.
5. `<head>` tem Open Graph e Twitter Card completos, `<link rel="alternate" type="text/markdown">`, `<link rel="api-catalog">`, `max-snippet:-1` — tudo correto.

### M17 — Descoberta em massa: artefatos grandes demais

| Artefato | Tamanho | Observação |
|---|---|---|
| `/llms-full.txt` | 1.455.210 B | ≈ 360 mil tokens — nenhum modelo carrega de uma vez |
| `/glossario/llms.txt` | 260.917 B | ≈ 65 mil tokens |
| `/consumidor/llms.txt` | 192.851 B | |
| `/previdenciario/llms.txt` | 187.450 B | |
| `/tributario/llms.txt` | 143.343 B | |
| `/feed.xml` | 511.521 B | **1.000 entradas**, sem `<content>`, só `<summary>`; média 507 B/entrada |
| `/rss.xml` | 512.491 B | idem |
| `/consumidor/feed.xml` | **404** | não há feed por área |

O `llms.txt` de área existe e responde 200 em todas as áreas testadas — bom. O problema é o **tamanho**: um agente que quer o índice de uma área paga 65 mil tokens. Feed de 1.000 entradas não serve a frescor (que pede as últimas dezenas, com paginação RFC 5005) e não expõe `rel="alternate" type="text/markdown"` por entrada.

### M18 — Log real do nginx do wiki (`/var/log/nginx/wikijuridica/access.log` + 6 rotações, 418.071 linhas, ~6 dias)

Este é o log do que **realmente atravessa o portal**, incluindo o acervo estático. Formato próprio, com `host=`, `allow=`, `bot_sim=`, `rt=`, `cf_ray=`, `warm=`.

| Bot | Req. | MB | 200 | 304 | 404 | 403 | 429 | 5xx |
|---|---|---|---|---|---|---|---|---|
| **`wikijuridica-*` (interno)** | **361.612** | **2.699,1** | 356.889 | 378 | 0 | 10 | 0 | 2 |
| outro / não classificado | 25.153 | 126,8 | 20.547 | 177 | 758 | 7 | 0 | 17 |
| meta-externalagent | 15.973 | 46,2 | 15.958 | 5 | 1 | 0 | 0 | 0 |
| semrushbot | 7.778 | 54,2 | 7.698 | 79 | 0 | 0 | 0 | 0 |
| bingbot | 1.674 | 11,8 | 1.637 | 22 | 0 | 0 | 0 | 0 |
| facebookexternalhit | 1.323 | 10,6 | 1.305 | 13 | 0 | 0 | 0 | 0 |
| amazonbot | 953 | 4,6 | 759 | 0 | **190** | 0 | 0 | 0 |
| **agentreadiness** | 888 | 1,1 | 416 | 61 | **366 (41%)** | 0 | 0 | 0 |
| oai-searchbot | 842 | 5,7 | 782 | 17 | 42 | 0 | 0 | 0 |
| claudebot | 828 | 3,4 | 740 | 44 | 44 | 0 | 0 | 0 |
| chatgpt-user | 323 | 1,9 | 184 | 0 | **132** | 0 | 0 | 0 |
| yandexbot | 224 | 1,3 | 188 | 36 | 0 | 0 | 0 | 0 |
| **googlebot** | **154** | 1,1 | 119 | 31 | 0 | 0 | 0 | 0 |
| perplexitybot | 70 | 0,5 | 19 | 2 | **49** | 0 | 0 | 0 |
| gptbot | 49 | 0,1 | 7 | 0 | **42** | 0 | 0 | 0 |
| **google-extended** | 42 | 0,1 | 0 | 0 | **42** | 0 | 0 | 0 |
| applebot · duckduckbot · claude-user · ahrefsbot · bytespider · lighthouse · inspectiontool | 1-58 cada | — | — | — | — | — | — | — |

**Totais: 407.426 × 200 · 872 × 304 (0,2%) · 1.666 × 404 · 17 × 403 · 0 × 429 · banda 2,97 GB.**

Cinco conclusões, todas medidas:

1. **O portal serve a si mesmo.** O tráfego interno (`wikijuridica-watchdog`, `-cache-warm`, `-edge-audit`, `-check-static-freshness`) é **86,5% das requisições e 91% da banda** — 2,7 GB por semana. Não é fraude (UA próprio identificado, como o contrato exige), mas é **aquecimento que não aquece nada**: o instrumento do próprio projeto mede 0% de cobertura de cache de borda. Gasta-se 2,7 GB/semana para encher um cache que não existe.
2. **Não há bloqueio de bot.** 17 respostas 403 e **zero 429** em 418 mil requisições. Isso **derruba** a hipótese fácil de que WAF, Bot Fight Mode ou rate limit estariam barrando o Googlebot. A causa é outra.
3. **304 = 0,2% do total.** Confirmação de campo, em escala, do bug P0 de revalidação (M6.b).
4. **`google-extended` fez 42 requisições e recebeu 42 × 404.** Google-Extended **não é crawler** — é controle de produto e não busca URL. Tráfego com esse UA é, por definição, falsificação. Somado a `gptbot` (42 de 49 em 404), `chatgpt-user` (132), `perplexitybot` (49) e `amazonbot` (190) pedindo caminhos de credencial, confirma M11 pelo outro lado.
5. **`agentreadiness` reprova o portal em 41% das sondas** (366 de 888 em 404) — é a medida externa e independente do gap de M12.

**✅ Discrepância borda × origem: RESOLVIDA, e a causa era erro meu.** Eu havia anotado aqui um fator de ~95× entre borda e origem para o Googlebot. Não existe: a leitura da borda estava inflada 68× por soma de ledger cumulativo (ver M3). Com a `serie_saneada`, os dois instrumentos **concordam**: Googlebot 33/dia na borda contra ~26/dia no nginx. Fica registrado como precedente da armadilha **A1**.

### M19 — URLs deformadas por extração de Markdown (achado novo, corrigível barato)

Amostras reais do log do nginx e do ledger do Go:

- `GET /educacao/index.md):` → 404 — **Amazonbot**. O modelo copiou a URL de dentro de um Markdown `[texto](url)` e trouxe `):` junto.
- `/.well-known/oauth-protected-resource\`` e `/.well-known/oauth-authorization-server\`` — 39 e 39 ocorrências, crase residual de bloco de código.
- `/.well-known/oauth-authorization-server):` — 2 ocorrências.
- `/.well-known/oauth-protected-resource/mcp\``, `/.well-known/oauth-protected-resource/api/v1/relatos\``.

Padrão: **agentes de IA extraem URLs de texto Markdown e carregam pontuação terminal** — `)`, `:`, `` ` ``, `,`, `.`. Cada um vira 404. Normalizar a cauda de pontuação e responder **301 para a URL limpa** recupera a visita a custo quase zero, e é engenharia defensiva legítima (não é criar rota fantasma: a rota de destino existe).

### M20 — Duas páginas de erro 404 diferentes

O nginx serve um 404 de **2.412 bytes**; o servidor Go serve um 404 de **7.521 bytes**. Mesmo portal, mesma condição, dois artefatos distintos — inconsistência de superfície, e o caminho caro é o que atende as rotas dinâmicas onde justamente os agentes erram mais.

### M9 — Registry de bots (`content/crawl_policy.json`)

32 entradas: 11 `search_discovery`, 9 `user_triggered_fetch`, 8 `training`, 2 `ads_validation`, 1 `product_use_control`, 1 curinga `*`. `Content-Signal: ai-train=yes, search=yes, ai-input=yes` declarado.

Pontos a resolver, já identificados na leitura do `robots.txt` servido:

- `Disallow: /*?` aplicado aos 8 bots de treinamento e ao Applebot-Extended — colide com a emenda de 2026-08-07 do projeto, que manda servir `utm_*` com canonical **sem** `noindex`. Um link de campanha vira conteúdo invisível para GPTBot/ClaudeBot/CCBot.
- `Google-Extended` está agrupado com bots de treinamento no `robots.txt`, mas é **controle de produto**, não crawler — classificado certo no registry, agrupado de forma discutível no arquivo.
- Nenhuma diretiva `Crawl-delay` nem `Clean-param` — esta última é suportada pelo Yandex, que é justamente o bot com melhor cobertura do acervo.
- 5 agentes com tráfego real fora do registry caem no grupo `*`.

---

## Onde este plano vai morar (ordem do dono)

Este arquivo vive hoje em `/home/rafael/.claude/plans/` — fora do repositório, portanto **fora do versionamento e perdível entre sessões**. Na execução, o primeiro ato é copiá-lo para dentro do projeto, em caminho versionável, e **commitá-lo na mesma sessão**:

```
/opt/wiki/docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md
```

Com ponteiro em `docs/goal/CHECKPOINT_DIGEST.md` e entrada em `docs/goal/MAESTRO_CODEX_LOG.md` registrando o quê e o porquê. Vale a regra do dono de 2026-07-29: **o que custou trabalho e dinheiro nasce dentro do repo e é commitado na mesma sessão** — nada de produto vivendo só em diretório volátil.

O arquivo é atualizado **a cada leva de agentes**: todo achado de workflow é materializado nele com medição, instrumento e corroboração, e investigado — nenhum achado morre em transcript.

---

## Ondas de investigação em voo

Lançadas nesta sessão, 23 agentes Opus 5 + 2 críticos Fable 5. Nenhuma decisão do plano espera por elas: o que voltar **entra neste arquivo** e vira task.

**Funil obrigatório de integração — aprendido nas ondas 1-3, vale para todas:** resultado de onda entra por *crítica Fable da onda → cruzamento com medição própria → só então vira tarefa*. **Item que contradiga medição já fechada exige reconciliação explícita, nunca substituição silenciosa.** O briefing de cada onda carrega números que podem envelhecer (18 commits, 3.023 URLs nunca pedidas, ~5.448 req/dia): se o retorno divergir, remede antes de aceitar. Três ondas já voltaram derrubando premissas do próprio briefing — é o comportamento esperado, não anomalia.

**Onde cada onda pendente aterrissa neste plano:** onda 4 → causa da queda do Googlebot (M22, com veredito **ou** "não fecha"), inventário de hardcode (R13/T5.9/T4.2), identidade de bot (T4.3), `anchor_claim` (T5.4), achados baixos (Fase 3-4). Onda 5 → destino do `lastmod` (T2.3), canal de notícias (Fase 6), desenho de frescor (T2.5/T1.3), conformidade DEC-032 (T6.2).

| Onda | Run ID | O que apura |
|---|---|---|
| **1 — Documentação oficial de bots** | `wf_e754299b-817` | 12 agentes, um por família (Google · Microsoft/Bing · OpenAI · Anthropic · Apple+Amazon · Perplexity+DDG · Meta · outros provedores de IA · buscadores regionais · SEO/analytics · sociais/preview · protocolos e padrões). Cada um devolve: token exato de UA, propósito, se respeita robots e qual grupo obedece, método oficial de verificação de identidade, URL da lista de IPs, se executa JS, diretivas honradas, o que a doc diz sobre **elegibilidade de citação**, e política recomendada. Fonte oficial com URL e data, ou literalmente "sem fonte oficial". Fecha com refutação adversarial Fable 5. |
| **2 — Auditoria do repo e da produção** | `wf_d4a46368-01b` | 10 agentes: política de bots e ponto de enforcement · Markdown e negociação de conteúdo · MCP/A2A/OAuth · roteamento e buracos · llms.txt e descoberta · dados estruturados JSON-LD · peso e custo por bot · telemetria e cegueira · borda Cloudflare e nginx · autoridade do conteúdo para máquina. Fecha com refutação adversarial Fable 5. |

---

## Onda 1 — documentação oficial: o que voltou (12 famílias, `wf_e754299b-817`)

**Contagem:** 35 bots do registry confirmados contra doc oficial · **144 tokens ausentes levantados** (nem todos devem entrar — parte é folclore, parte é padrão e não bot, e a crítica Fable ainda está rodando para derrubar o que não se sustenta).

### O1 — Google: 22 dos ~25 tokens ausentes, e três subfamílias que **não herdam nada**

O registry tem 3 tokens Google (`Googlebot`, `AdsBot-Google`, `Google-Extended`). A lacuna não é cosmética:

| Grupo | Tokens ausentes | Por que importa |
|---|---|---|
| **Agêntico** | **`Google-Agent`** | Fetcher agêntico (2026-03-20), lista de IP exclusiva (`user-triggered-agents.json`, 20 prefixos) e **único bot Google com identidade criptográfica** — Web Bot Auth/RFC 9421, identidade `https://agent.bot.goog`. É o encaixe direto entre a superfície de agente já construída e um agente Google real. |
| **Ignoram o `*`** | `APIs-Google`, `AdsBot-Google-Mobile`, `Mediapartners-Google` (+ `AdsBot-Google`, já presente) | A doc declara *"The global user agent (\*) is ignored"*. Qualquer política escrita supondo que `*` cobre a família Google **está errada para eles**. |
| **Ignora robots.txt inteiro** | `Google-Safety` | *"ignores robots.txt rules"*. O único controle possível é faixa de IP na borda. |
| **Não herdam `Googlebot`** | `GoogleOther`, `GoogleOther-Image`, `GoogleOther-Video`, `Storebot-Google` | Obedecem só ao próprio token e caem no `*`. |
| **Disparados por usuário** | `Google-GeminiNotebook`, `Google-Read-Aloud`, `FeedFetcher-Google`, `GoogleProducer`, `Google-Site-Verification`, `Google-CWS`, `GoogleMessages`, `Google-Pinpoint` | **`FeedFetcher-Google` é o consumidor Google do WebSub** — e o portal já opera WebSub. `Google-Site-Verification` sustenta o Search Console, onde vive o controle de elegibilidade em IA generativa. |
| **Renomeação com prazo vencendo** | `Google-NotebookLM` → **`Google-GeminiNotebook`** (2026-07-22) | O nome antigo é suportado *"until August 2026"* — **expira este mês**, e o novo não está em lugar nenhum do registry. |

**O1.a — Dado obsoleto no repo, medido.** As listas de IP do Google **mudaram de endereço em 2026-02-11**: o caminho canônico agora é `/static/crawling/ipranges/`, não `/static/search/apis/ipranges/`. Medição por `curl`: o caminho antigo de `googlebot.json` responde **301 para `common-crawlers.json`** — o arquivo `googlebot.json` **não existe mais como recurso próprio**. O repo mantém `data/ops/bot_ip_ranges/googlebot.json`, `google-special-crawlers.json` e `google-user-triggered.json`: **3 arquivos para 5 listas oficiais**, e um deles aponta para recurso que foi absorvido.

**O1.b — Declaração oficial do Google que contraria parte do investimento atual do portal.** Da doc de otimização para IA (`developers.google.com/search/docs/fundamentals/ai-optimization-guide`), literal:

> *"You don't need to create new machine readable files, AI text files, markup, or Markdown to appear in Google Search (including its generative AI capabilities), as Google Search itself doesn't use them."*

E sobre `llms.txt`, literal:

> *"It's completely fine if you decide to create and maintain LLMS.txt files … Doing so will neither harm nor help your site's visibility or rankings in Google Search, as Google Search ignores them."*

**Leitura correta, sem exagerar para nenhum lado:** isso **não** torna `llms.txt` e Markdown inúteis — outros consumidores existem, e o Markdown é 4,8× mais barato para qualquer agente que o leia. Mas **proíbe** contabilizá-los como causa de citação no Google. O que o Google declara governar a elegibilidade em IA generativa é: (a) a página estar **indexada e elegível a snippet**; (b) a propriedade **não estar em opt-out** de *Search generative AI* no Search Console (default é incluído); (c) `robots.txt` para `Googlebot` — e **não** `Google-Extended`, que governa Gemini Apps e grounding no Vertex, não AI Overviews. O mecanismo declarado é RAG sobre o índice de Busca com *query fan-out*.

### O2 — OpenAI: o registry está completo; as lacunas são de **verificação e de métrica**

Os quatro tokens que a OpenAI opera (`OAI-SearchBot`, `GPTBot`, `ChatGPT-User`, `OAI-AdsBot`) **já estão no registry**. Não falta token. Faltam três coisas:

1. **O agente de navegação da OpenAI não tem User-Agent.** Operator → ChatGPT agent → ChatGPT Cloud browser identifica-se por **assinatura RFC 9421**: headers `Signature`/`Signature-Input`/`Signature-Agent` com valor literal `"https://chatgpt.com"`, chaves em `https://chatgpt.com/.well-known/http-message-signatures-directory` (verificado vivo: 1 chave Ed25519, `purpose=ai`). **Um registry baseado em User-Agent é cego para ele.** Como Anthropic, Google (`agent.bot.goog`) e You.com usam o **mesmo padrão**, a implementação é de família, não de fornecedor.
2. **Faixas de IP não espelhadas.** Os quatro JSON existem e têm cadências muito diferentes (medido 2026-08-26): `chatgpt-user.json` 204 prefixos (dinâmico, exige refresh diário) · `searchbot.json` 35 · `gptbot.json` 21 · `adsbot.json` 2. **Todos 100% IPv4, zero IPv6** — uma allowlist que assuma IPv6 ou exija rDNS derruba bot legítimo.
3. **A métrica de citação existe e não está instrumentada.** A OpenAI acrescenta **`utm_source=chatgpt.com`** a toda URL de referência (declaração oficial no Publishers FAQ). **É o único sinal de citação consumada que a OpenAI dá ao publisher**, e o portal não o conta em `data/ops/`. Depende de a rota com query string servir 200 com canonical limpo e sem `noindex` — coberto pela emenda de 2026-08-07, mas **a cobertura precisa ser verificada nos hubs e na paginação, não suposta**.

**O2.a — WebMCP: o portal usa a API errada.** A doc oficial da OpenAI (`learn.chatgpt.com/docs/webmcp.md`) define o registro por **`document.modelContext.registerTool({name, description, inputSchema, annotations:{readOnlyHint:true}, execute})`**, e o browser embutido do ChatGPT **descobre essas ferramentas ao visitar a página** — sem cadastro, sem aprovação, sem contrato. A frente de protocolos apurou que o portal registra via **`navigator.modelContext`, que está fora da spec vigente de 2026-08-26**. Corrigir isso em `internal/webmcp` (e recalcular o hash da CSP) é a única alavanca da família OpenAI ativável hoje sem depender de ninguém. A própria OpenAI usa o padrão no site dela — há modelo de referência público.

### O3 — Anthropic: registry completo; falta a lista de IP e fica uma armadilha documental

`ClaudeBot`, `Claude-User` e `Claude-SearchBot` são os três únicos bots que a Anthropic documenta, e os três já estão corretamente classificados. Lacunas:

1. **Falta `data/ops/bot_ip_ranges/anthropic.json`.** A Anthropic publica `https://claude.com/crawling/bots.json` (26 prefixos, `creationTime` 2026-08-18). Sem ele, as requisições atribuídas a `claudebot` são contadas **sem prova de origem**. Detalhe que quebra heurística: **sem IPv6**, e 3 dos 26 prefixos são blocos Azure — "Anthropic = Google Cloud" é falso.
2. **`anthropic-ai`, `Claude-Web`, `claude-code` não têm fonte oficial.** A Anthropic nunca os reivindicou. **Ausência do registry não é defeito** — cair no `*` é o tratamento correto. Adicioná-los só teria valor de auditoria (impedir que uma sessão futura os promova por engano).
3. **Armadilha documental a registrar:** a versão de 2024-05-01 dizia que ClaudeBot honrava também os *disallows* de `CCBot`; a versão de 2026-04-07 **removeu a frase sem anunciar revogação**. Hoje CCBot está com `Allow: /`, então não há dano — mas a regra *"nunca fechar CCBot com `Disallow: /` sem reverificar o artigo"* precisa ficar escrita.

### O4 — Outros provedores de IA: separar o real do folclore

Dos 23 tokens investigados: **12 têm doc oficial, 8 não têm nenhuma fonte primária, e 1 tem doc oficial que declara que o token não existe.**

**Adicionar, com doc verificada** (ordem de retorno para citação): `YouBot` (melhor higiene de identidade da família — Web Bot Auth Ed25519 + rDNS + faixa; honra `Crawl-delay`) · `Kagibot` (grafia com b minúsculo) · `LinerBot` (público acadêmico/profissional, o mais alinhado ao acervo jurídico) · `Diffbot` e `Diffbot-User` (declara não treinar modelo de fundação; propaga entidade/autoria para terceiros) · **`FirecrawlAgent`** (o portal já serve exatamente o que o Firecrawl produz: Markdown) · `AI2Bot` e `Ai2Bot-Dolma` · `ImagesiftBot` · `Webzio`/`Webzio-Extended` · `Coherebot`.

**Adicionar só como cobertura barata, nunca documentar como confirmados** (sem fonte oficial): `kagi-fetcher`, `Timpibot`, `TikTokSpider`, `PanguBot`, `PetalBot`, `Devin`, `omgili`/`omgilibot`, `Trae`.

**NÃO adicionar:** `Kangaroo Bot` (folclore) · `cohere-ai` e `cohere-training-data-crawler` — **o fornecedor desmente**: *"We do not use Cohere bots or user agents for the purpose of crawling or scraping web content to train generative AI foundation models at this time"* · `Brave-Search` — a doc oficial declara que o crawler **não anuncia UA diferenciado**; a entrada casaria com zero requisições, e a ação correta é submeter URLs em `search.brave.com/submit-url`.

**O4.a — Duas armadilhas de configuração que valem para o registry inteiro:**

- **Cascata Googlebot.** `Kagibot` e `ImagesiftBot` herdam, **por documentação oficial**, o grupo `Googlebot` quando não há grupo próprio. Hoje é vantagem (Googlebot liberado); vira **regressão silenciosa** se o grupo `Googlebot` for restringido um dia. A dependência precisa ficar registrada junto das entradas.
- **Diretiva contra UA não é controle.** Diffbot e Firecrawl permitem que o **cliente** troque o UA avaliado ou desligue a adesão a robots.txt (Firecrawl: *"Ignore the website's robots.txt rules. Enterprise only"*). Brave não se identifica. Bytespider não tem doc. Para esses, o instrumento real é **rate limit e verificação de identidade**, nunca a linha no robots.

### O5 — Protocolos: onde há consumidor real, e onde não há

| Canal | Estado apurado | Ação |
|---|---|---|
| **MCP Registry** (`registry.modelcontextprotocol.io`) | **Único registro público que aceita inscrição hoje.** Self-serve pelo CLI `mcp-publisher`; namespace de domínio próprio verificado por **DNS TXT ou HTTP challenge** — ambos executáveis com a infraestrutura local, sem credencial de terceiro. Status: PREVIEW, API freeze v0.1. | **Registrar o `/mcp`.** É a resposta concreta a *"como um servidor MCP público é descoberto hoje"*: por este registro ou por configuração direta — **não por varredura da web**. |
| **Consumo MCP direto por URL (Claude)** | Qualquer usuário Claude, **inclusive no plano gratuito**, pode plugar `https://wikijuridica.com.br/mcp` sem aprovação, sem contrato e sem OAuth (autenticação é opcional). Transportes aceitos: streamable HTTP ou SSE. | Já funciona. Cumprir o requisito de anotação: todo tool com `title` e `readOnlyHint`/`destructiveHint` — **o portal já anota**. |
| **Connectors Directory (Anthropic)** | **Exige organização Team ou Enterprise.** Falha o critério de auto-serviço sem contrato. | Registrado como fato. Decisão de custear é do dono; **não é tarefa desta sessão**. |
| **IndexNow** | O blog oficial do Bing (07/2025) recomenda combinar sitemap com IndexNow para submissão em tempo real, em texto que trata explicitamente de *"AI generated answers"*. Protocolo aberto, sem cadastro, **já na lista autorizada do repo**. | **Canal de frescor com maior alcance real** — o Bing alimenta Copilot e ChatGPT Search, e faz 360 req/dia contra 33 do Googlebot. Verificar se está ativo e medindo. |
| **Web Bot Auth (RFC 9421)** | Não é canal de inscrição: é camada de **verificação**. Em produção hoje: OpenAI (`chatgpt.com`), Google (`agent.bot.goog`), You.com. Mistral, Kagi, Brave, Cohere, Ai2, CCBot, Diffbot, Liner, Webz.io, ImageSift e ByteDance **não** documentam suporte. Biblioteca `cloudflare/web-bot-auth` permite verificação própria na origem. | Implementar verificação — é o que fecha o buraco do agente sem UA (O2.1) e o de M11. |
| **A2A e ARD/ai-catalog** | **Não há onde se inscrever.** A spec A2A declara não prescrever API padrão para registros curados; o repositório do `ai-catalog` é *"temporary working repo"* da Linux Foundation, com adoção pendente de voto. | Manter servindo; **não gastar engenharia esperando registro que não existe**. |
| **NLWeb** | Não é bot, é protocolo, e **exige exatamente as três peças que o portal já expõe**: MCP, JSON-LD schema.org e endpoint de pergunta em linguagem natural. Toda instância NLWeb *"acts as an MCP server"* com o método `ask`. | Sem token a registrar. O passo de retorno é garantir que o MCP aceite pergunta em linguagem natural e responda em JSON-LD schema.org. |

**O5.a — Correção de um item que eu mesmo tinha errado.** Eu havia listado o 404 em **`/.well-known/http-message-signatures-directory`** (M12) como gap a fechar. **Não é defeito e não deve ser "corrigido":** aquele diretório pertence a quem **assina requisições de saída**, não a quem as recebe. Um site que só recebe bots não publica esse diretório — ele **lê** o dos outros. Achado derrubado pela própria onda, antes de virar trabalho errado.

**O5.b — Veredito duro e honesto da frente de protocolos, que vale registrar inteiro:** o portal **já publica praticamente tudo o que existe para publicar** (7 artefatos servindo 200), e a medição própria mostra que isso rendeu **um único consumidor medido — um scanner de diagnóstico** (`cloudflare-agentreadiness`). O retorno de citação por IA hoje **não vem de artefato de agente**; vem de (a) estar indexado e elegível a snippet, (b) `max-snippet:-1` — já correto, (c) `Content-Signal` com `ai-input=yes` — já declarado, e (d) frescor de sitemap/IndexNow no Bing. Isso reordena as prioridades do plano: **antes de publicar mais artefato, consertar o que impede o acervo de ser rastreado e revalidado barato.**

---

## Onda 2 — auditoria do repo e da produção: o que voltou (6 de 10 frentes, `wf_d4a46368-01b`)

**69 achados nas 6 primeiras frentes.** Quatro frentes e a crítica Fable ainda rodam. Os que seguem já vêm com `arquivo:linha` e medição própria.

### O6 — **[CRÍTICO] O binário Go em produção está 6 dias defasado do fonte**

**Isto reordena tudo o que vem depois: auditar o código não descreve o que está no ar.**

- `/opt/wiki/bin/wikijuridica-server` — mtime **2026-08-20 13:08**. Processo PID 3789447 iniciado 2026-08-20 15:55:20 (5d15h de uptime).
- `git log --since='2026-08-20 13:08' -- internal/ cmd/` = **18 commits** não embarcados.
- Prova por conteúdo: `strings -a bin/wikijuridica-server | grep -c 'application/rss+xml'` = **0**, e a string existe em `internal/httpserver/artefatosestaticos.go:41` — o commit `4a3217eb` (*"o RSS que existia há meses e ninguém servia"*) **não está no binário**.
- Prova funcional independente: `GET /rss.xml` no Go (8089) = **404**, enquanto `public/rss.xml` existe (512.491 B) e o nginx o serve com 200.

**Consequências em cadeia, já medidas:** os `/{area}/llms.txt` respondem 404 no Go e 200 pelo nginx (por isso minha sonda pela borda deu 200 — **camada, de novo**); e três hubs servem título genérico porque o processo carregou `content/area_hub_editorial.json` **antes** de ele existir (boot 15:55:20, arquivo 16:02:05, commit `cc1d796f` 16:03:28).

**Correção:** rebuild + restart na mesma sessão de qualquer correção Go. **Correção de raiz:** `tools/check-binario-vs-fonte` — compara hash/mtime do binário em execução com o último commit que tocou `internal/` ou `cmd/` e reprova se houver commit posterior. Mesma classe de gate que `check-arquitetura-fiel`.

### O7 — **[CRÍTICO] A Cloudflare injeta script externo de 47.616 B em toda página e reescreve a CSP por nonce**

Medido nas duas camadas, na mesma requisição:

| | Origem (127.0.0.1:8088) | Borda (wikijuridica.com.br) |
|---|---|---|
| Página 404 | 7.361 B, **zero** tags `<script>` | 7.521 B, com `<script type="module" src=".../.webmcp/bridge.js" nonce="…" data-packs="c2pa,mcp-server-client">` |
| `/familia/` | 29.020 B | 29.180 B (+160) |
| CSP `script-src` | `'sha256-LWtUrcm…'` e nada mais | a mesma **+ `'nonce-<32 hex>'`** |
| `/.webmcp/bridge.js` | **404** no nginx **e** no Go | **200, 47.616 B, `server: cloudflare`, `cf-cache-status: HIT`** |

O nonce do header e o do corpo **batem na mesma resposta** (`ae64aa2a…`), o que prova reescrita **da borda**, não do Go. **O arquivo não existe no portal** — é servido pela própria Cloudflare.

**Viola três dos cinco limites que a emenda de 2026-08-19 do `CLAUDE.md` manteve:** item 2 (tamanho medido declarado no commit — 47.616 B nunca foram declarados), item 3 (nada de bundle nem host externo — é módulo externo de 47 KB) e item 5 (**CSP autoriza por hash, nunca por token largo** — `nonce` autoriza qualquer script que a borda escolher injetar).

**Nenhum gate vê:** `tools/check-ingress-security-headers:88` sobe réplica do nginx em `127.0.0.1` e **nunca fala com a borda**; `tools/check-agent-surface-live:33` fala com a borda e **passou 100% (exit 0)** sem olhar CSP nem `<script>`. **Gate verde não é prova — é ausência de cobertura.**

**Correção, nesta ordem:** (1) `tools/check-edge-html-injection` — read-only, baixa ~10 rotas da origem e da borda e reprova se a CSP servida diferir byte a byte de `httpserver.ContentSecurityPolicy` ou se o HTML da borda contiver `<script>` ausente na origem; (2) decidir a injeção **com medição**: desligá-la por janela curta e remedir `cf-cache-status` e presença de ETag — se o cache voltar a HIT, a injeção é também causa do problema de cache; se não, a causa é a Cache Rule ausente (M6.a.1). Versionar em `ops/cloudflare/`, como já se faz com `waf-custom-rules.json` e `cache-rules.json`. **Este item passa por red-team Fable antes de qualquer toque em produção.**

### O8 — **[GRAVE] A fábrica está parada há 6 dias, e com ela todo o frescor**

`journalctl -u wikijuridica-daily-content.service --since 2026-08-15`: **seis falhas consecutivas**, todas **antes** da etapa 8/9 (publicação) — 21/08 pareamento · 22/08 coleta + pareamento · 23/08 pareamento · 24/08 coleta + pareamento · 25/08 coleta + preservação · 26/08 preservação. O script para na primeira falha (*"A ONDA PAROU"*), então a **etapa 9/9 — IndexNow — nunca roda**.

Consequências medidas: última submissão IndexNow **2026-08-20T16:46:14Z** · último ping WebSub aceito **2026-08-20T18:59:59Z** · `find public -newermt 2026-08-21 -type f` **vazio** · `systemctl list-timers | grep -ci indexnow` = **0** (a única automação é a etapa 9/9). O WebSub **não** está quebrado: roda a cada 30 min e corretamente não pinga porque o feed não muda há 6 dias.

**E dentro do erro de 26/08 há um alerta que vale por si:** *"TRABALHO APAGADO: 50 página(s) ativa(s) sumiram de 1 shard(s) — `stf-informativo-derivado-01.jsonl`: 50 → 4"*. É exatamente a classe de perda que o contrato de 2026-08-07 proíbe (*página escrita nunca é descartada*). A guarda de preservação **funcionou** — travou a onda em vez de deixar passar. Recuperação apontada pelo próprio script: `git show HEAD:data/editorial/v2_pages/stf-informativo-derivado-01.jsonl`.

**Correção em duas camadas:** (a) recuperar o shard e corrigir o gerador que apagou; (b) **desacoplar o frescor da onda** — hoje um único shard corrompido silencia IndexNow e WebSub do portal inteiro, inclusive para as 10.070 páginas sadias e no ar. Criar `wikijuridica-indexnow.timer`/`.service` chamando `tools/generate-indexnow-incremental-submit`, no mesmo padrão do `wikijuridica-websub-ping.timer` que já existe e é idempotente por hash.

**Peso desse achado no contexto do plano:** a onda 1 apurou que **IndexNow é o canal de frescor com maior alcance real** para este portal (o Bing faz 360 req/dia contra 33 do Googlebot, e alimenta Copilot e ChatGPT Search). Ele está **desligado há 6 dias** — e ninguém foi avisado.

### O9 — Roteamento: buracos com endereço

- **[ALTA] `/sitemaps/` responde 410 Gone** sobre o diretório-pai dos 34 shards vivos. Cadeia: `/sitemaps` → 301 → `/sitemaps/` → **410** (dois saltos até um "foi embora"). Causa exata: `ops/nginx/standalone/nginx.conf:810` usa `try_files $uri @sitemap_extinto` e diretório não é arquivo, caindo em `return 410`. **O Go tem handler correto** (`httpserver.go:1414-1428`, responde 200 com o índice de 4.406 B) **e a requisição nunca chega lá**. Correção sem regex: um `location = /sitemaps/` com `proxy_pass` — `location =` vence o prefixo por precedência, e **nenhum shard muda de comportamento** (o 410 legítimo para shard ordinal extinto é preservado).
- **[ALTA] Rotas de máquina devolvem HTML institucional em erro.** `/a2a/v1` e `/api/v1/relatos` entregam **6.389 bytes de HTML** a um cliente JSON.
- **[MÉDIA] A borda remove o ETag** das páginas de acervo — o bot perde o validador forte e fica só com o `Last-Modified` que está quebrado (M6.b).
- **[MÉDIA] 10,2% dos 404 de origem são URLs mutiladas** copiadas de documentos do próprio portal: crase de Markdown (`%60`) e o fecho `)` seguido de `:`. Confirma M19 com número.
- **[MÉDIA] 45,2% dos 404 de origem são agentes procurando descritores sob `/.well-known/`**, e **cinco famílias podem ser servidas com conteúdo que o portal já tem**.
- **[BAIXA] `/api/search` era o caminho errado da minha sonda** — a busca por API **existe e é descoberta**. O defeito real é o **404 dela responder HTML**. Corrige M7 e M12.
- **[BAIXA] Comentário que mente:** o `nginx.conf` afirma que os 28 caminhos `/{area}/pagina/` respondem `301→404`; medido, **respondem 200** com a página inteira.
- **[BAIXA] Content-Type do sitemap difere por camada:** `text/xml` no nginx, `application/xml` no Go.

### O10 — Markdown e negociação

- **[CRÍTICO] Negociação falha em silêncio** — confirma M2/A3 com leitura de código.
- **[ALTO] Requisição de Markdown que dá 404 recebe 7.521 B de HTML**, com CSS e script, em vez de erro em `text/markdown`.
- **[ALTO] O Markdown não tem front matter e não declara licença nenhuma** — enquanto o HTML declara CC BY 4.0. **É a assimetria de autoridade que responde à queixa do dono.**
- **[ALTO] Três hubs entregam título genérico e sem acento no Markdown** — consequência de O6 (config carregada antes de existir). `/diarios/index.md` serve *"Conteúdos jurídicos de Diarios"*; o HTML da mesma rota serve *"Que municípios publicaram diário oficial, dia a dia"*.
- **[ALTO] Rótulo de área sem acento em 285 URLs estáticas** — `Diarios`, `Noticias`, `Jurisprudencia` no **breadcrumb visível** e no **JSON-LD**. Causa: o mapa `breadcrumbAreaLabels` (`internal/structureddata/structured_data.go:1110`) não tem essas três chaves e o fallback capitaliza o slug ASCII. **É falha P0 de PT-BR pelo contrato do projeto**, e nenhum gate pega: a família de gates PT-BR opera sobre `PublicBodySections`, e rótulo de navegação gerado em runtime nunca entra nesse escopo. Correção em três partes: as entradas no mapa, republicar as 285 páginas (o breadcrumb está assado no HTML), e **transformar o fallback ASCII em erro** com um check `area-label-cobertura`.
- **[MÉDIO] A gêmea `.md` não carrega Cache-Tag** e tem `s-maxage` 168× menor que o HTML, e **a purga da publicação nunca nomeia a URL `.md`**.

### O11 — Dados estruturados

- **[ALTA] `dateModified` do JSON-LD contradiz a data visível em 9.710 de 10.071 páginas (96,4%).** Par dominante: JSON-LD `2026-08-06` contra visível `2026-08-20`, em 9.576 páginas. A diretriz do Google exige que a marcação corresponda ao conteúdo visível — **contradizer-se no campo de frescor é motivo declarado para o buscador tratar a marcação como não confiável**. O defeito não é a precedência (`content.go:371-383` documenta de propósito a separação *revisão de conteúdo* × *revisão jurídica humana*), é que **dois canais rotulam coisas diferentes com o mesmo rótulo**.
- **[ALTA] O único gate de dados estruturados valida 360 registros de uma camada de ENSAIO e nunca abre `public/`** — 10.071 nós `Article` ao vivo não passam por gate nenhum. Gate verde, cobertura zero.
- **[ALTA] O mesmo `@id` de `Person` carrega dois `name` diferentes no grafo, e a credencial OAB existe só em prosa** — confirma e agrava M16.
- **[ALTA] O Markdown carrega 4 dos 18 campos do JSON-LD, todos como prosa** — sem front matter, sem licença, sem datas estruturadas.
- **[MÉDIA] `isBasedOn` e `speakable` são zero em 10.299 páginas** — e nas 1.000+ páginas derivadas de texto oficial, `isBasedOn` é **a** propriedade semanticamente correta (DEC-032).
- **[MÉDIA] 217 páginas de hub e paginação** — as que concentram os links internos — **emitem `CollectionPage` sem `BreadcrumbList` e sem `isPartOf`**.
- **[MÉDIA] Cinco páginas sem nenhum JSON-LD, e duas delas são `/fontes/` e `/fontes/planalto/`** — justamente as páginas de proveniência.
- **[MÉDIA] `sameAs` é zero em todo o corpus** — nenhuma entidade se liga a identificador externo.
- **[MÉDIA] Zero Dublin Core, zero `<meta name="author">`, zero `<link rel="license">`, zero `<meta name="citation_*">`** em 10.299 páginas.
- **[MÉDIA] `about` existe em 5,3% das páginas** — 9.533 artigos não declaram assunto.

### O12 — Política de bots

- **[ALTA] Os rate limits por bot do registry não são aplicados em lugar nenhum — o registry é decorativo quanto a taxa.** Confirma a suspeita do plano com leitura de código.
- **[ALTA] `check-robots-parser-real` julga o robots.txt com um parser cego a `Disallow: /*?`, e os dois parsers do repo discordam sobre o mesmo arquivo.**
- **[ALTA] Canal de citação de IA (`Cloudflare-AI-Search`) e os dois maiores crawlers da origem estão fora do registry**, caindo no `*`.
- **[MÉDIA] Nenhum gate compara o robots.txt SERVIDO com o do disco** — buraco que já custou dias de robots errado no ar.
- **[MÉDIA] `Applebot-Extended` tem `access_rule` de 20 r/m** sendo que o próprio repo declara que ele não envia User-Agent — **configuração morta**.
- **[MÉDIA] Sem `Clean-param` nem `Crawl-delay`** — o único mecanismo de consolidação de parâmetro que o Yandex entende não está declarado, e o Yandex é o crawler com melhor cobertura do acervo.
- **[MÉDIA] Comentário que mente em `internal/crawl`** sobre o canal Content-Signal estar fechado por gate.
- **[MÉDIA] `internal/robotsaudit` não audita a política do portal** — é conformidade de saída; a política de entrada fica sem auditor.

### O13 — llms.txt e descoberta

- **[MÉDIO] `llms-full.txt`: 1,4 MB que não são "full" nem cabem em contexto** — **52,9% do arquivo são caracteres de URL** e ~26% é o mesmo prefixo repetido.
- **[MÉDIO] Submissão IndexNow não é comprovável para 9.601 das 10.292 URLs**, e o próprio estado admite que a reconstrução é impossível.
- **[MÉDIO] Metade do feed é um empate:** 506 das 1.000 entradas têm o mesmo timestamp, e o corte cai dentro dele, resolvido **por ordem alfabética**.
- **[MÉDIO] As páginas que provam autoria e proveniência (`/sobre/`, `/metodologia/`, `/fontes/`) servem Markdown 200 e não aparecem em nenhum `llms.txt`.**
- **[MÉDIO] `check-edge-discovery-freshness` cobre 9 rotas de raiz e deixa de fora os 34 shards de sitemap e os 32 `llms.txt` de área** — exatamente o que mais importa.

### O14 — MCP, A2A e OAuth

- **[CRÍTICO] `relatar_defeito` sem token responde 200 sem `WWW-Authenticate`**, enquanto a gêmea REST `/api/v1/relatos` responde 401 com o desafio completo. Mesma capacidade, mesmo binário, dois comportamentos — **descuido de cobertura, não decisão**. Causa em `oauth.go:658-660`: requisição sem `Authorization` pula todo o caminho de desafio, e a guarda em `httpserver.go:1130-1134` é **cega a qual ferramenta** está sendo chamada. A correção precisa ser **antes** de entregar ao SDK (no streamable HTTP os headers do 200/SSE saem antes de o handler rodar) e é barata: o header `Mcp-Name` já nomeia a ferramenta.
- **[ALTA] `aisec-registry` toma 404 na descoberta de autorização do MCP** — sonda `/mcp/.well-known/…` e o portal só serve `/.well-known/…/mcp`. **Gap de conformidade com RFC 9728**, confirma M12.
- **[ALTA] Um crawler de descoberta real sonda `/.well-known/agent.json` e `/.well-known/mcp` 16× cada em 32 h e toma 404 nas duas.**
- **[ALTA] O Agent Skill empacotado ensina uma receita incompleta do MCP** — enquanto `api.md` e `auth.md` ensinam a certa.
- **[MÉDIO] Os tarballs de skill não têm diretório raiz** — extrair dois no mesmo lugar sobrescreve o `SKILL.md`.
- **[MÉDIO] O bridge da borda registra duas ferramentas de C2PA num acervo sem imagem** e duplica as que o portal já registra.
- **[MÉDIO] Sem `authorization_code`, sem PKCE e sem registro dinâmico, nenhum cliente MCP padrão consegue token** — limitação declarada com honestidade, mas é limitação.
- **[BAIXO] `total_indexado` do MCP (10.077) não bate com o `count` da API REST (10.070)** — o único número realmente órfão.

### O15 — Borda Cloudflare: a causa-raiz com data e hora

- **[CRÍTICO] A zona não tem NENHUMA regra de cache desde `2026-08-22T13:10:13Z`.** O ruleset de cache está na **versão 14 com zero regras**, e as **quatro fases de ruleset da zona estão vazias**. Isso **confirma e data** a dedução de M6.a.1: não é defeito de código, é configuração que foi removida. 100% do tráfego atravessa o túnel.
- **[ALTO] Os três arquivos versionados em `ops/cloudflare/` afirmam um estado de borda que não existe.** O repo declara regras que a zona não tem. **É a armadilha do comentário que mente, aplicada à infraestrutura** — e explica por que ninguém percebeu.
- **[ALTO] Always Online foi DESLIGADO em 2026-08-24** — era a única defesa que restava contra o 530 do túnel, num dia em que a borda já não cacheava nada.
- **[MÉDIO] Cache Reserve (produto pago, lastreado em R2) está LIGADO numa zona que não cacheia nada.** Custo sem contrapartida.
- **[MÉDIO] A borda entrega o `robots.txt` com `Cache-Control` de UM ANO** enquanto a origem declara 300 s — **o crawler pode não reler a política de bots por 12 meses**. Isso torna qualquer correção de robots invisível por um ano.
- **[BAIXO] `Amazonbot` cai na pista genérica de rate limit:** o allowlist `$wj_bot_allow` tem `amzn-searchbot` e `amzn-user`, mas **não** `amazonbot` — que é o que realmente vem (111 req/dia).
- **[INFORMATIVO] ⚠ A hipótese que eu havia marcado como de maior ROI foi REFUTADA por medição:** **não há Bot Fight Mode, WAF, challenge nem rate limit atingindo bot valioso.** O Googlebot não está sendo barrado. Coerente com M18 (17 respostas 403 e **zero** 429 em 418 mil requisições). **Registro como refutação minha, não como confirmação.**
- **[INFORMATIVO] Túnel:** `protocol http2` confirmado no ar, 25 instâncias no teto de 100 conexões da Cloudflare, **sem impacto de latência atribuível ao protocolo**.
- **[MÉDIO] A causa exata do 404 no Markdown de paginação: exclusão deliberada na linha 328 do `nginx.conf`.** Tem endereço, e a mesma linha explica por que a URL canônica devolve HTML a quem pede Markdown.

### O16 — Peso e custo para o bot

- **[CRÍTICA] O aquecimento gasta 436.380 requisições por semana na origem para aquecer 0,07%** — **29,6× mais carga que o Googlebot, produzindo nada**, porque a zona não cacheia. Confirma M18 com número de eficácia.
- **[ALTA] O CSS inline custa 2.148 bytes comprimidos por página — 30,1% do payload que o bot baixa — e a compressão NÃO o neutraliza.** Agregado: **20,4 milhões de bytes** no acervo.
- **[MÉDIA] `brotli_static` está ligado e não existe UM arquivo `.br` em disco:** o nginx **recomprime os 10.299 HTMLs a cada requisição**, ~10 min/dia de CPU jogada fora. Correção trivial e de ganho imediato: pré-comprimir no build.
- **[MÉDIA] `llms-full.txt` entrega 316 KB comprimidos e não é cacheado** — cada leitura de agente atravessa o túnel inteiro.
- **[MÉDIA] O alerta crítico do próprio portal está aberto há 48 repetições e 4 dias sem que nada aconteça.** *A observabilidade funciona; a resposta a ela, não.*
- **[BAIXA] ✅ O teto de 50 KB está cumprido com folga:** **zero violações em 10.299 arquivos**, maior página 36.937 B (73,9% do teto). Contrato preservado.

### O17 — Telemetria: onde o portal é cego

- **[CRÍTICA] 2.401 URLs — 23,3% do acervo — nunca foram pedidas por NENHUM dos quatro crawlers que decidem busca ou citação** (Googlebot ∩ Bingbot ∩ OAI-SearchBot ∩ ChatGPT-User). Individualmente (as_of 2026-08-26): Googlebot nunca pediu 3.023 · Bingbot 8.199 · OAI-SearchBot 9.345 · ChatGPT-User 10.090 · **PerplexityBot 10.294 (100%)** · ClaudeBot 7.785 · GoogleOther 6.992 · GPTBot 4.901. **Só Amazonbot e YandexBot varreram o acervo — e nenhum dos dois traz tráfego nem citação para um portal jurídico brasileiro.**
- **[CRÍTICA] O Googlebot não está limitado — ele PAROU de descobrir**, e **nunca pediu 19 dos 38 hubs de área**, embora tenha pedido páginas `/pagina/N/` dentro deles. Combina com O8 (fábrica parada, `lastmod` sem novidade há 6 dias).
- **[CRÍTICA] `claude-searchbot` — o bot que decide se o portal é citado pelo Claude — não tem rastreamento de cobertura nenhum**, e teve **1 requisição verificada**.
- **[CRÍTICA] O gate de honestidade da telemetria está VERMELHO há 12 dias** por um buraco de **2.007 bytes NUL** no ledger, e **por desenho não consegue se curar**.
- **[ALTA] O gate de liveness reprova ~18 h de cada 24 h por construção**, e a instrução de conserto que ele imprime **aponta para a unit errada**.
- **[ALTA] As rotas que cada bot pediu são lidas do log, agrupadas na memória e JOGADAS FORA — sobra só a contagem.** É por isso que ninguém sabia qual URL deu 404 para qual bot. **É a cegueira que esta sessão teve de contornar à mão.**
- **[ALTA] Bots de IA verificados estão pedindo Markdown e endpoints de protocolo de agente desde 2026-08-20, e o dado está enterrado num arquivo de estado** que ninguém lê. **Isso é evidência positiva de que a superfície de agente TEM consumidor — e ela estava invisível.**
- **[ALTA] A medição de citação carimba `considered_for_answer` em toda linha, inclusive nas 84% que ela própria classifica como sem relação com citação.** Métrica que se auto-infla — vai contra o contrato anti-fraude e precisa de correção.
- **[ALTA] PerplexityBot e Amzn-SearchBot são 100% não autenticados na borda; ChatGPT-User tem fração relevante de UA não verificada.** Confirma M11 pelo instrumento do projeto.
- **[MÉDIA] Os dois maiores consumidores — meta-externalagent e semrushbot, 32.526 requisições na origem — não têm método de verificação nenhum.**
- **[MÉDIA] 16 agentes que a telemetria conta não são governados pela política de rastreio, e 2 que a política governa a telemetria não sabe contar.**
- **[MÉDIA] O ledger da borda tem 22.557 linhas para 326 fatos — 69× de redundância, 16,8 MB crescendo ~730 KB/dia**, e todo consumidor varre o arquivo inteiro. **É a causa material da armadilha A1** — e some com um compactador.
- **[ALTO] Confirmação independente do meu erro:** *"Os volumes de bot do briefing do chefe estão inflados ~55×: o `edge_bot_agents_daily.jsonl` é um ledger CUMULATIVO e foi somado linha a linha."* Duas frentes independentes apanharam. Ordem de grandeza confere com os 68× que medi.

### O18 — Conteúdo: a resposta medida à queixa *"não tem autoridade nenhuma"*

Esta frente responde diretamente ao dono, com número em vez de impressão. **É o achado mais valioso da sessão em potencial de citação.**

- **[CRÍTICO] 64% das afirmações normativas do corpo não têm âncora verificável** — a página afirma o que a lei manda **sem dizer qual dispositivo**.
- **[CRÍTICO] Todo link inline de artigo aponta para a lei inteira: 0 de 106 links externos do corpo têm o fragmento do dispositivo**, embora a URL profunda já exista e seja construível.
- **[CRÍTICO] 24.367 afirmações normativas ancoradas e verificadas EXISTEM no dado (`anchor_claim`) e 95% nunca chegam à página.** **O trabalho já foi feito e pago — está no repositório e não é publicado.** É a maior alavanca de autoridade disponível, e não exige redigir uma linha nova.
- **[ALTO] O canal Markdown é estritamente mais pobre que o HTML:** perde **URN LexML**, licença, lista de citações e política de uso. Confirma M16/O11 e nomeia o que falta.
- **[ALTO] Zero páginas informam vigência da norma citada** — o acervo diz quando a **URL** foi conferida, nunca se a **norma** está em vigor. Para conteúdo jurídico, é o que um modelo precisa saber para citar com segurança.
- **[ALTO] Não existe identificador estável nem seção "como citar"** — o modelo não tem como referenciar a página com precisão nem detectar que ela mudou.
- **[ALTO] O gate answer-first existe, é bom, e não fiscaliza nada:** `pagefactory` só roda num binário de prova; `entityrender` e `resumoextrativo` têm zero chamadas em produção.
- **[ALTO] A família de súmulas derivadas publica molde:** **80 páginas com quatro frases idênticas**, sigla interna de órgão julgador e data em formato ISO no texto visível. Viola anti-template e PT-BR.
- **[MÉDIO] 30% dos rótulos de fonte prometem um dispositivo específico e a URL entrega o documento inteiro** — o rodapé afirma precisão que não tem.

### O19 — Correções que a onda 1 aplicou aos próprios achados (crítica Fable)

O crítico Fable da onda 1 derrubou pontos das pesquisas, e as derrubadas entram **antes** dos achados:

1. **URL de `policy_source` errada.** O verbatim do Google sobre IA na Busca **não** está em `google-common-crawlers`; vive em `developers.google.com/search/docs/appearance/ai-features`. Num registry que grava `policy_source` por entrada, URL que não sustenta a citação é defeito.
2. **`max-snippet:-1` não é o único controle de input para AI Overviews.** São quatro: `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`. É o único que **limita sem remover** — a formulação anterior era falsa.
3. **⚠ ARMADILHA GRAVE — precedência de grupo no robots.txt.** Grupo nomeado **descarta o `*` inteiro**, e `internal/crawl/crawl.go:1139` (`RenderRobotsTXT`) serializa cada regra em grupo `User-agent:` próprio. **Criar um grupo "GoogleOther / Allow: /" removeria de GoogleOther a única guarda que ele tem hoje** — o `Disallow: /buscar/` herdado do `*`. **Isto significa que adicionar bots ao registry, feito ingenuamente, é uma REGRESSÃO, não uma melhoria.** Toda entrada nova precisa repetir as guardas do `*`, e isso vira requisito de gate.
4. **Fetchers disparados por usuário ignoram robots.txt.** Verbatim do Google: *"Because the fetch was requested by a user, these fetchers generally ignore robots.txt rules."* Logo, as ~8 recomendações de `Allow` para `Google-Site-Verification`, `Read-Aloud`, `GeminiNotebook`, `FeedFetcher`, `GoogleMessages`, `Pinpoint`, `CWS` e `GoogleProducer` **só têm efeito na borda** (faixa de IP), nunca via robots.
5. **`exp` da chave do `chatgpt.com` é ROLANTE** (medido mudando entre duas leituras). Qualquer implementação de Web Bot Auth precisa **cachear por `kid` e reler `nbf`/`exp` a cada fetch**, nunca congelar o valor.
6. **Números inventados pelos agentes**, removidos: "creationTime já mudou três vezes", "a mesma implementação verifica Claude e Perplexity", "Crawl Control do BWT com 24 faixas horárias em 5 quadrantes".
7. **Content-Signal: nenhuma doc oficial de Google, Microsoft ou OpenAI o menciona.** O portal **emite** `ai-train=yes, search=yes, ai-input=yes` em cada grupo, e nenhum dos três grandes declara honrá-lo. **Fato a registrar, não motivo para remover** — mas proíbe contá-lo como causa de citação.
8. **Reordenação "Bing tem mais alavancagem que Google" — DERRUBADA**, e eu confirmei em campo: o Fable levantou a hipótese de que parte das requisições do Bingbot fosse lixo de busca interna, porque o grupo `Bingbot` tem `Disallow:` vazio e descarta o `Disallow: /buscar/` do `*`. **Medi no log do nginx: Bingbot 0% de requisições a `/buscar/` ou com query string** (idem Googlebot, YandexBot e SemrushBot). **A hipótese não se confirma — mas a armadilha estrutural do item 3 continua de pé**, e é o mesmo mecanismo.

---

## Onda 3 — arquitetura de servir (4 de 6 frentes, `wf_367e8cb2-ac5`)

### O20 — **Resposta direta ao dono: "por que não tem nada no `public`? Isso é bom?"**

> **VEREDITO MEDIDO: sim, é bom. Zero `.md` em `public/` foi decisão deliberada, com motivo escrito e teste que a defende. NÃO pré-gerar.**

A pergunta é legítima e a resposta não é opinião — a frente testou a hipótese e ela **caiu**:

| Hipótese testada | Resultado medido |
|---|---|
| *"Com `.md` em disco, a borda cachearia"* | **REFUTADA.** O HTML **já está em disco desde 06/08** e devolve `cf-cache-status: DYNAMIC` igualzinho ao `.md` de runtime. Disco não tem relação causal com cacheabilidade neste portal — o gargalo é a borda (O15). |
| *"Pré-gerar melhoraria os validadores"* | **INVERSO — regrediria dois.** O runtime emite **ETag de CONTEÚDO** (`markdown.go:242`, ex.: `"1c8f1664d1e1afdf367de439f1ae71d2"`); o nginx estático emitiria `hex(mtime)-hex(size)` (`"6a73ce80-62dd"`), que **colide e não muda quando o conteúdo muda mantendo o tamanho**. E o `Last-Modified` do runtime já serve a **data editorial correta** (`httpserver.go:925`), enquanto a pré-geração ingênua reintroduziria um defeito que o repo **já corrigiu em 2026-08-12**. |
| *"O runtime é caro"* | **NÃO É.** Custo medido: **0,63 ms de CPU por requisição**, ~1.100 req/dia = **0,7 segundo de CPU por dia**. Não há economia a perseguir. |
| *"Pré-gerar daria `.md` às 185 rotas de paginação"* | **NÃO DARIA.** A exclusão é deliberada, documentada, e corrige um defeito de duplicação já medido. |

**Único ganho real da pré-geração, dito sem exagero:** com o Go parado, `.md` devolve 502 — e o repo **já aceitou esse custo por escrito**.

**Achados colaterais desta frente, que importam mais que a pergunta original:**

- **O canal Markdown é 81% `meta-externalagent`** — ou seja, **é o canal de bot de IA de maior volume do portal**, e cada requisição dele bate na origem porque a borda não cacheia.
- **NÃO EXISTE cache de Markdown.** Existe cache de HTML em disco, com invalidação por assinatura e sem TTL.
- **[DEFEITO REAL] A gêmea `.md` declara TTL de borda 168× menor que o HTML da mesma página**, com o mesmo conteúdo e a mesma data editorial. Sem justificativa.

### O21 — Cache de borda: causa-raiz confirmada por três frentes independentes, com as armadilhas da correção

**A causa é uma só, com carimbo de tempo:** a zona **não tem nenhuma Cache Rule desde `2026-08-22T13:10:13Z`** (ruleset v14, zero regras, quatro fases vazias). **Não é `Vary`, não é `Set-Cookie`, não é extensão** — as três hipóteses foram testadas e caíram. Isso confirma o experimento controlado de M6.a.1 e dá a data.

**Falsos verdes que deixaram passar — todos a corrigir:**

- **`tools/check-edge-vary-contract` lê a verdade e sai VERDE**: `exit 0` com zero regras vivas na zona.
- **O aquecedor sai com `exit 0` e `failures:0` enquanto registra `dynamic:10383`.** **Mede o próprio fracasso e reporta sucesso.**
- **48 alertas críticos sobre exatamente este defeito, emitidos desde `2026-08-21T17:53`, todos com `resolvido: false`.** *A detecção funcionou. Ninguém consumiu.* **É o achado de processo mais importante da sessão: o portal sabia, e o saber não virou ação.**

**Achado arquitetural de fundo:** **a configuração de borda deste portal não é governada pelo repo.** `grep -rl http_request_cache_settings tools/ cmd/ internal/` devolve **apenas** `check-edge-vary-contract` (que **lê**) e um **comentário** em `deploy-publico`. **Nenhuma ferramenta escreve a Cache Rule** — toda a deriva de 21-24/08 veio de edição de painel, e ficou **4 dias e 21 horas no ar com o alarme tocando a cada 2 h**.

**⚠ Duas armadilhas na correção, apanhadas antes de o trabalho começar** — e é exatamente por isso que a onda existiu:

1. **Restaurar o corpo versionado LITERALMENTE pregaria por 7 dias 6 rotas de descritor** que nasceram depois de 2026-08-12 e pedem `max-age=300`. O JSON versionado está **desatualizado em relação às rotas de agente que o portal criou desde então**.
2. **Com a allowlist de `vary` restaurada, a variante Markdown de todas as 10.294 URLs fica fria por construção** — porque **o aquecedor nunca pede `Accept: text/markdown`**. Ou seja: restaurar a regra sem tocar no aquecedor deixaria justamente o canal de agente (81% meta-externalagent) sem cache.

**Correção arquitetural proposta, em três peças, todas locais e sem SaaS** (respeita R5 e a proibição de terceiros):

1. `tools/apply-cache-rules` — **PUT idempotente** do corpo versionado no entrypoint da fase, com leitura-antes-de-escrever e ledger em `data/ops/edge_rule_apply.jsonl`.
2. `tools/check-edge-rule-drift` — read-only, `exit != 0`, GET do entrypoint e **diff canônico** contra `ops/cloudflare/cache-rules.json`, **reprovando explicitamente quando `rules` está ausente ou vazio** (o caso de hoje, que o gate atual atravessa em verde). Registra a `version` viva — foi o histórico de versões da API o único instrumento que datou a deriva.
3. Fechar o laço de alerta: alerta crítico com `resolvido: false` por N repetições **precisa escalar**, não repetir 48 vezes em silêncio.

### O22 — Aquecimento interno: inventário completo e veredito

Inventário medido no log do nginx, dia cheio 2026-08-25 (77.533 linhas, 550,2 MB):

| Produtor | req/dia | MB/dia | Entra por | Disparo | Objetivo declarado |
|---|---|---|---|---|---|
| `wikijuridica-cache-warm/1.0` | **62.319** | **435,4** | borda | `edge-warm.timer`, 6×/dia, `warm-edge-cache --rps 6 --concorrencia 4` | manter 10.390 URLs quentes para queda de túnel não virar 530 ao crawler |
| `wikijuridica-watchdog/1.0` | 3.405 | 53,5 | origem | `watchdog.timer`, 2 min, `check-portal-health --repair` | acervo no ar, busca viva, restart em loop |
| `wikijuridica-edge-audit/1.0` | 1.840 | 4,8 | borda | `edge-live.timer` 2 min + `edge-cache-coverage.timer` 2 h | a borda alcança a origem? quanto segue quente? |
| `wikijuridica-websub/1.0` | 47 | 3,2 | borda | `websub-ping.timer`, 30 min | avisa o hub quando `/feed.xml` muda |
| **INTERNO** | **67.611 (87,2%)** | **496,9 (90,3%)** | | | |
| externo | 9.922 (12,8%) | 53,4 | | | |

**Confirmação cruzada:** 6 dias × ~497 MB/dia ≈ **2,98 GB** — bate com os 2,97 GB que medi em M18 por caminho independente.

- **[CRÍTICO] O escudo anti-530 está caído há 3,92 dias** e o aquecimento virou **trabalho nulo**: 62.319 GET/dia contra páginas que a origem já serve em menos de 1 ms, enchendo um cache que não existe. **436.380 requisições por semana para aquecer 0,07% — 29,6× mais carga que o Googlebot.**
- **[ALTO] O aquecimento não enche cache de borda, nem cache do Go, nem nada aproveitável.**
- **[ALTO] O vigia declara medir "BUSCA VIVA" e na verdade valida um 200 de página estática em disco** — **a busca do Go pode estar morta e ele não perceberia**. (Ecoa o precedente `[[instancia-auditoria-cachedir]]`, em que a busca ficou morta respondendo 200.)
- **[MÉDIO] `organic_requests` conta sonda interna como audiência:** o desconto lê só o ledger do aquecedor e **ignora 1.887 req/dia das sondas**. É inflação de métrica — corrigir por dever de anti-fraude, mesmo sendo interna e não intencional.
- **[INFORMATIVO] ✅ Anti-fraude dos produtores internos: LIMPO**, verificado em **todo o histórico do log, não por amostragem**. Nenhum forja UA de bot real. O contrato está sendo cumprido.

**Nota de decisão:** o aquecimento **não deve ser simplesmente desligado** — ele existe para um motivo real (evitar 530 ao crawler em queda de túnel). O que deve mudar é: (a) restaurar a Cache Rule para que ele passe a ter efeito; (b) fazê-lo aquecer **também** a variante `Accept: text/markdown`; (c) reduzir a cadência ao que a cobertura medida exigir, em vez de 6 varreduras completas por dia.

### O23 — Mapa real nginx × Go, e o achado estrutural

**O roteamento inteiro é mais simples do que as 1.277 linhas de config sugerem, e a simplicidade é o achado:** **não existe uma única `location` regex.** Dez `location =`, quatro prefixos e quatro locations nomeadas. A decisão de fundo cabe numa frase:

> `location /` (linha 897) serve do disco `/opt/wiki/public` via `try_files $uri $uri/ @fallback`, e **tudo que o disco não tem cai em `@fallback` e vira proxy para o Go em 127.0.0.1:8089**.

Como `public/` tem 10.299 `.html` e zero `.md`, a divisão é exata: **HTML = nginx lendo disco; Markdown, busca, API, MCP, A2A e contato = Go.**

**Verificação de cloaking, importante e positiva:** **nada de User-Agent influencia conteúdo** — o único uso de UA na config é a chave de rate limit. **Humano e crawler recebem o mesmo byte da origem.** Contrato cumprido.

Achados desta frente:

- **[ALTA] ✅ Confirmação independente: o bug do `If-Modified-Since` é do NGINX, não do Go** — a diretiva `if_modified_since` nunca foi declarada e o default é `exact`. Bate com a minha verificação em M6.b.1.
- **[ALTA] ✅ Confirmação independente: o nginx NÃO apaga o ETag — ele emite; quem apaga é a Cloudflare**, e o `Last-Modified` vem do mtime do arquivo. Bate com M6.c.
- **[MÉDIA] `/area/pagina/N/index.md` dá 404 no GO, não no nginx** — corrige a atribuição de camada, e as 185 rotas **não anunciam nenhum** alternate.
- **[MÉDIA] Três arquivos de configuração nginx no repo NÃO são carregados por nada** — **editar qualquer um deles não muda produção, em silêncio.** É a mesma família do "repo mente sobre a borda" (O15).
- **[MÉDIA] O gêmeo Markdown tem três políticas de cache diferentes da página HTML, e o caminho negociado não emite `Last-Modified`.**
- **[BAIXA] `brotli_static` ligado sobre ZERO arquivos pré-comprimidos** — nginx recomprime na origem e a Cloudflare comprime de novo na borda. Confirma O16.
- **[BAIXA] `CLOUDFLARE_API_TOKEN` em `.env.local` está inválido** — toda a telemetria de borda depende de o fallback para o token escopado nunca falhar. **Fragilidade silenciosa de instrumento.**

---

## M21 — Incidente da borda reconstruído na API da Cloudflare (medição própria, fonte autoritativa)

O dono autorizou usar a API da Cloudflare nesta sessão. **Bastou o token de zona — não precisei da API global.** Achado de instrumento, primeiro: **`CLOUDFLARE_API_TOKEN` está inválido** (`Invalid API Token`); quem funciona é **`CLOUDFLARE_ZONE_TOKEN`**. Toda a telemetria de borda depende de o fallback nunca falhar — fragilidade silenciosa a corrigir.

**Zona:** `wikijuridica.com.br` · `b2e1366a94c5dcac97f2fc264f18928f` · status `active` · plano **Free Website**.

**Estado atual, lido do entrypoint:**
```
phase=http_request_cache_settings  ruleset "wikijuridica — cache de HTML na borda"
version 14  |  last_updated 2026-08-22T13:10:13.447383Z  |  rules: 0
```

**Linha do tempo completa do incidente, por versão do ruleset:**

| Versão | Timestamp (UTC) | Estado das regras |
|---|---|---|
| v1 | 2026-08-12T00:51:27 | a Cache Rule nasce |
| v2-v6 | 12/08 a 16/08 | evolução |
| **v7** | **2026-08-18T18:29:31** | **1 regra — A REGRA BOA**, idêntica ao corpo versionado em `ops/cloudflare/cache-rules.json`: exclui `/buscar/`, `/contato/` e rotas de corpo variável · `edge_ttl` 604800 com `status_code_ttl` (4xx=60s, 5xx=0) · `browser_ttl: respect_origin` · `origin_error_page_passthru: false` · **e `vary: { accept: { action: normalize, media_types: ["text/markdown", …] } }`** — ou seja, **tratava a negociação de Markdown corretamente** |
| **v8** | **2026-08-21T14:14:17** | **0 regras** — primeiro apagamento; a regra boa some |
| v9 | 2026-08-21T20:22:03 | 1 regra: `Cache default file extensions [Template]` |
| v10 | 2026-08-21T20:23:07 | 2 regras: + `Cache everything [Template]` (`expr: true`) |
| v11 | 2026-08-21T20:36:18 | 3 regras: + `Set browser cache time [Template]` |
| v12 | 2026-08-22T13:10:04 | 2 regras — perde `Cache default file extensions` |
| v13 | 2026-08-22T13:10:10 | 1 regra — perde `Cache everything` ← **o elo que cacheava HTML** |
| **v14** | **2026-08-22T13:10:13** | **0 regras — estado de hoje** |

**Três leituras que só a linha do tempo permite:**

1. **A regra de engenharia do repo esteve no ar e foi substituída por templates de painel.** A v7 é o corpo versionado; a v8 a apagou; v9-v11 são **templates genéricos do painel Cloudflare**, não a configuração do projeto. Isso confirma o achado da onda 3 — *"a configuração de borda não é governada pelo repo"* — e mostra o mecanismo: **edição manual de painel sobrescreveu a engenharia versionada.**
2. **v12→v13→v14 aconteceram em NOVE SEGUNDOS**, removendo uma regra por vez até zerar. É assinatura de exclusão sucessiva no painel (ou de script apagando em laço), não de uma mudança pensada.
3. **A medição independente do projeto bate exatamente:** `edge_cache_coverage.jsonl` registra 100% HIT em **2026-08-21T21:57** (v11, templates ainda ativos) e 40/40 DYNAMIC em **2026-08-22T14:20** (v14, zero regras). **Dois instrumentos, mesma história, mesmos carimbos.**

**Consequência para a correção:** o alvo não é "criar uma Cache Rule" — é **restaurar a v7**, que já existe versionada e já é boa. Com **um ajuste obrigatório** apanhado pela onda 3: o `edge_ttl` de 604800 em `override_origin` prenderia por 7 dias as ~6 rotas de descritor de agente que nasceram depois de 12/08 e pedem `max-age=300`. Essas rotas precisam entrar na lista de exclusão, ou o `edge_ttl` precisa passar a `respect_origin` para elas. **E o aquecedor precisa passar a pedir também `Accept: text/markdown`**, senão a variante que 81% do tráfego de bot de IA consome fica fria por construção.

**Outros rulesets da zona, para o registro:** `http_request_firewall_custom` v12 (*"wikijuridica — higiene de superfície"*) · `http_request_dynamic_redirect` v11 · `http_request_transform` v4 · `http_response_headers_transform` v2 · `http_response_compression` v2 · `http_config_settings` v2 · mais os gerenciados (Normalization v6, Managed Free Ruleset v74, DDoS L7 v3402).

### M21.a — A credencial disponível não alcança as fases onde mora o problema

Mapeei o que cada credencial de `.env.local` consegue fazer:

| Variável | Estado | Alcance medido |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | **inválido** (`Invalid API Token`) | nenhum |
| `CLOUDFLARE_ZONE_TOKEN` | **ativo** (`b470ac76…`) | lista rulesets · lê `http_request_cache_settings` e seu histórico de versões |
| `CLOUDFLARE_EMAIL` | preenchido | sem chave global correspondente no arquivo |
| `CLOUDFLARE_API_KEY` / `GLOBAL_API_KEY` / `ACCOUNT_ID` | **vazios** | — |

**Medido:** ler `http_request_firewall_custom` (por fase **e** por id do ruleset) devolve **`request is not authorized`**. O mesmo vale para `http_request_transform`, `http_response_headers_transform` e `http_response_compression`.

**Por que isso importa, e não é detalhe de credencial:** são exatamente essas as fases onde vive **a injeção do `bridge.js` e a reescrita da CSP** (O7), e é o **audit log da conta** que guarda **quem** apagou a Cache Rule (O24/N-3). Ou seja: **o portal hoje não consegue auditar nem governar por API justamente as camadas em que a deriva aconteceu** — o que explica por que a deriva de 21-24/08 ficou quase 5 dias no ar sem ninguém saber a origem.

**Consequência para a execução:** T1.1 e T1.2 (Cache Rule) são executáveis com o token atual. **T3.1 (identificar o ator e decidir a injeção) exige credencial de escopo de conta** — o dono mencionou ter a API geral com e-mail; se ela estiver disponível na execução, a tarefa fecha; se não, T3.1 entrega a **decisão medida** (desligar por janela curta e remedir) sem a atribuição de autoria, e isso fica dito, não escondido.

---

## M23 — A superfície Markdown TEM consumidor, e é massivo: 86,5% do que bot de IA pede

Medi, no log real do nginx (6 dias), o que cada bot de IA efetivamente pediu, separando **Markdown** × **endpoints de protocolo** × **HTML**:

| Bot de IA | Markdown | Protocolo | HTML | Preferência |
|---|---|---|---|---|
| **meta-externalagent** | **15.697** | 77 | 199 | **98% Markdown** |
| amazonbot | 348 | 29 | 579 | 36% Markdown |
| claudebot | 335 | 7 | 470 | 41% Markdown |
| oai-searchbot | 158 | 6 | 678 | 19% Markdown |
| chatgpt-user | 0 | 8 | 316 | HTML |
| perplexitybot | 0 | 7 | 63 | HTML |
| applebot · gptbot · claude-searchbot · claude-user · bytespider | 0-1 | 0 | 16-52 | HTML |
| **TOTAL** | **16.539** | **134** | **2.440** | **86,5% Markdown** |

**Isto reordena o plano e corrige um veredito da onda 1.** A frente de protocolos concluiu que *"a superfície de agente rendeu um único consumidor medido, e é um scanner de diagnóstico"* — **verdadeiro para os artefatos `.well-known`, falso para o Markdown**. O canal Markdown é, disparado, **o mais consumido por bot de IA neste portal**.

**Cinco tarefas mudam de peso por causa desta medição:**

1. **T5.3 (front matter no Markdown) sobe para alavanca principal de autoridade.** 86,5% do consumo de IA passa por um documento que **não declara licença, não traz a credencial OAB estruturada e carrega 4 dos 18 campos** que o HTML tem. **O canal mais lido é o mais pobre — e é exatamente isso que o dono percebeu como "não tem autoridade nenhuma".**
2. **Os 185 `/pagina/N/` sem Markdown** deixam de ser 1,8% de rotas e passam a ser buracos no canal principal.
3. **A negociação que devolve HTML calado** (armadilha A3) atinge o canal que 86,5% do tráfego de IA usa.
4. **O TTL de borda 168× menor no `.md`** (O20) penaliza justamente o canal mais requisitado — e a purga da publicação **nunca nomeia a URL `.md`**.
5. **Aquecer a variante `Accept: text/markdown`** (T1.5) deixa de ser luxo: sem ela, o canal principal fica frio por construção quando a Cache Rule voltar.

**Ressalva honesta:** 95% desse volume é **um único agente** (`meta-externalagent`, classificado como treinamento). Se ele parar, o número desaba. Mas **ClaudeBot (41%), Amazonbot (36%) e OAI-SearchBot (19%) também preferem ou usam Markdown de forma relevante** — não é um consumidor único. E `ChatGPT-User` e `PerplexityBot` pedem **zero** Markdown: ou não sabem que existe, ou não o preferem — **o que é medição a fazer, não conclusão a tirar.**

### M23.a — E ele já varreu quase tudo, uma vez, e foi embora

Detalhamento do que o `meta-externalagent` fez no canal Markdown:

| Métrica | Valor |
|---|---|
| URLs **distintas** em Markdown | **9.965** |
| Cobertura do acervo (10.294) | **96,8%** |
| Respostas | 15.695 × 200 · **1 × 304** · 1 × 404 |
| Distribuição por dia | **20/08: 9.769** · **22/08: 5.922** · 23/08: **6** · depois, nada |

URLs distintas em Markdown pelos demais: ClaudeBot **335** · Amazonbot **348** · OAI-SearchBot **137**.

**Duas leituras, e a segunda é a síntese causal da sessão:**

1. **Uma resposta 304 em 15.697 requisições.** É o bug de revalidação (M6.b.1) medido no canal principal, em escala: o agente rebaixou o acervo **duas vezes inteiro** porque nada lhe disse que nada tinha mudado.

2. **O padrão "varre tudo e vai embora" é o mesmo em todos os bots de treinamento** — GPTBot (4.432 req em 07/08, depois 1/dia), ClaudeBot (2.149 em 07/08, depois 2/dia), meta-externalagent (9.769 em 20/08, 5.922 em 22/08, depois nada). **Eles não voltam porque nada sinaliza que voltaria a valer a pena.** E é exatamente o que está desligado: o `lastmod` não muda desde 20/08, o feed não muda, o IndexNow está parado há 6 dias, e a revalidação condicional não funciona.

> **A síntese que o plano precisava:** o portal **não tem um problema de descoberta — tem um problema de FRESCOR**. Os bots acharam o acervo, varreram (uns 96,8%, outros 20-50%), e foram embora. Quem não voltou não voltou por falta de sinal; quem nunca veio (Perplexity 0%, ChatGPT-User 2%) não veio por falta do mesmo sinal chegando pelos canais que **eles** consomem. Isso põe a **Fase 1 (destravar a fábrica e o IndexNow)** e a **Fase 2 (revalidação e frescor)** acima de qualquer artefato novo — e explica por que publicar mais `.well-known` não moveria a agulha.

---

## M24 — Os hubs de área estão descobríveis e mesmo assim não são pedidos

Medi a decomposição do que cada bot **nunca** pediu, separando hubs de área, fatias de paginação e artigos:

| Bot | Nunca pediu | dos quais **hubs** | paginação | artigos |
|---|---|---|---|---|
| googlebot | 3.023 | **19 de 38** | 81 | 2.923 |
| oai-searchbot | 9.345 | **12 de 38** | 185 | 9.148 |
| chatgpt-user | 10.090 | **34 de 38** | 179 | 9.877 |

**E os hubs não estão escondidos:** são **38 no sitemap** e **39 links diretos da home**. Ou seja — **descoberta não é o gargalo de linkagem**; é o mesmo problema de parada (M22/M23.a). O Googlebot ignorou `/familia/`, `/bancario/`, `/imobiliario/`, `/empresarial/`, `/administrativo/` — áreas grandes, linkadas da home, no sitemap.

**Achado que sai daqui e é acionável hoje — confirmei por medição direta:**

```
/sobre/          ocorrências no llms.txt: 0
/metodologia/    ocorrências no llms.txt: 0
/fontes/         ocorrências no llms.txt: 0
/aviso-legal/    ocorrências no llms.txt: 0
/privacidade/    ocorrências no llms.txt: 0
```

**Nenhuma das cinco páginas institucionais é anunciada no `llms.txt`** — e são exatamente as que provam **autoria, método, proveniência e limites de uso**, isto é, as que um modelo leria para decidir se confia na fonte. Elas **existem, servem Markdown 200, estão no sitemap**, e nenhum canal de descoberta as aponta. Entre os hubs que o Googlebot nunca pediu estão justamente `/metodologia/` e `/privacidade/`.

**Incluí-las no `llms.txt` (raiz e por área) é correção de minutos, sem redigir uma linha, com efeito direto sobre a percepção de autoridade que o dono relatou.** Derivando a lista do dado (as rotas institucionais já estão em `content/pages.json`), **nunca por literal** — R13.

### M24.a — Um item que está CERTO e vale registrar

`GET /previdenciario/135-ou-agencia/?utm_source=chatgpt.com` responde:

```
status 200 · 22.648 bytes
<link rel="canonical" href="https://wikijuridica.com.br/previdenciario/135-ou-agencia/">
<meta name="robots" content="index,follow,max-snippet:-1">
```

**Canonical limpo, sem `noindex`, com `max-snippet:-1`.** A emenda de 2026-08-07 está **cumprida na prática**, e o caminho pelo qual a OpenAI sinaliza citação (`utm_source=chatgpt.com`) **não é destruído pelo portal**. Falta só **contar** esse sinal (T4.7) — a porta está aberta, ninguém está do lado de dentro anotando quem entrou.

---

## M22 — A queda do Googlebot: série medida e o que ela exclui

Este é o achado que **quatro frentes de auditoria não viram** e que a crítica Fable da onda 2 apanhou. Verifiquei pessoalmente na série canônica (`data/ops/crawl_coverage_daily.jsonl`, verificação por `cloudflare_verified_bot_category`).

| Data | Googlebot req/dia | Cobertura cumulativa |
|---|---|---|
| 06/08 | 5 | 0,01% |
| 07/08 | 87 | 0,83% |
| 08/08 | **1.962** | 20,19% |
| 09/08 | 897 | 27,50% |
| **10/08** | **4.178** | **67,64%** |
| 11/08 | 977 | 72,01% |
| **12/08** | **40** ← queda de 96% | 72,01% |
| 13/08 a 26/08 | 4 a 157/dia | **estagnada em ~70,6%** |

**O colapso tem data: 2026-08-12.** E a cobertura **não voltou a crescer em 14 dias** — 3.023 URLs jamais pedidas.

**O mesmo padrão em outros bots, com data própria:**

| Bot | Pico | Depois |
|---|---|---|
| **GPTBot** | **4.432 req em 07/08** (cobertura 50,75%) | **1 req/dia** desde 08/08, com dois picos isolados (13/08: 151 · 21/08: 520) |
| **ClaudeBot** | **2.149 req em 07/08** (cobertura 21,77%) | **2 req/dia** desde 08/08, picos em 13/08 e 20/08 |
| **Bingbot** | quase nada até 19/08 | **cresce desde 20/08**: 484 · 237 · 248 · 217 · 307 · 648 — cobertura 0,35% → 20,35% |
| **OAI-SearchBot** | crescimento contínuo | 187-227/dia recentemente, cobertura 9,22% |

**Confirmação independente pelo Google Search Console** (MCP, propriedade `sc-domain:wikijuridica.com.br`, `siteOwner`):

| URL | Veredito do Google |
|---|---|
| `/previdenciario/maternidade-homem/` (a mais rastreada) | **Indexed and healthy** · `Last Crawled: 2026-08-10 10:53` · `Robots.txt: ALLOWED` · `Page Fetch: SUCCESSFUL` · Rich Results **PASS** |
| `/leis/lindb/` (uma das 3.023 nunca pedidas) | **"URL is unknown to Google"** · `Robots.txt: STATE_UNSPECIFIED` |

**A última varredura que o Google admite é 2026-08-10** — exatamente o pico da série. E a URL não visitada não está **bloqueada**: está **desconhecida**. **Isso descarta bloqueio e confirma parada de descoberta.**

**O que a data exclui, e é muita coisa:** a injeção do `bridge.js` (22/08), o binário defasado (20/08), o cache DYNAMIC (22/08 — e a Cache Rule só nasceu em 12/08T00:51) e a fábrica parada (21/08) **são todos POSTERIORES a 12/08**. Nenhum deles pode ser a causa. Igualmente descartado: `Disallow: /*?` — o grupo do Googlebot tem `Allow: /` limpo.

> ## ⚠ M22 FOI SUPERADA PELA ONDA 4 — leia O28 antes de agir
>
> **A hipótese que formulei abaixo (Content-Signal em 12/08) está REFUTADA por medição própria da frente dedicada**, e a própria data está errada: **o colapso foi em 2026-08-11T02Z, não em 12/08**. O Content-Signal só entrou no config em **12/08 09:03 — depois do evento**. Mantenho o texto abaixo para rastreabilidade do raciocínio; **o veredito válido é o de O28.**

**O que aconteceu em 12/08, medido no git (não em comentário — o dono avisou para não confiar neles):**

```
6d075fc7  2026-08-12 09:03  feat(crawl): o sinal que autoriza CITACAO por IA chama-se ai-input, e faltava
eeb7c6cf  2026-08-12 09:25  fix(crawl): Content-Signal so no curinga nao chegava a nenhum bot de citacao
c0a10058  2026-08-12 09:44  feat(crawl): erro de digitacao no sinal atravessava gerador, teste e gate
f71a0f3e  2026-08-13 11:10  fix(robots): tres defeitos que liberavam ou bloqueavam o bot errado
5cc0e8ea  2026-08-13 13:14  fix(robots): o gerador desfaria em silencio as tres correcoes de hoje de manha
```

**Três edições do `Content-Signal` no robots.txt na manhã de 12/08, uma delas corrigindo um erro de digitação que "atravessava gerador, teste e gate", e mais três defeitos de robots no dia seguinte "que liberavam ou bloqueavam o bot errado".** O Googlebot despencou naquele mesmo dia. Há ainda o precedente documentado de o **Bing Webmaster ter acusado erro de sintaxe** no robots e *"Discovered but not crawled"*.

**⚠ Postura obrigatória: isto é CORRELAÇÃO FORTE, não causa provada.** A contra-hipótese legítima é que 08-11/08 foi o **surto de descoberta inicial** de um site novo (0% → 72% em quatro dias) e o que veio depois é o ritmo de manutenção. O que enfraquece essa contra-hipótese é a **estagnação por 14 dias com 3.023 URLs nunca pedidas** e um `lastmod` que parou de mudar — não é perfil de manutenção, é perfil de descoberta interrompida. **A frente dedicada (onda 4) tem de fechar isso com evidência do Search Console** — relatório de estatísticas de rastreamento e histórico do robots.txt como o Google o leu —, e nenhuma correção deve ser aplicada com base só na correlação.

---

## O24 — Críticas Fable das ondas 2 e 3: o que foi derrubado antes de virar trabalho errado

**Esta seção existe porque cada item aqui teria custado uma correção errada aplicada em produção.**

### Derrubado — e eu confirmei pessoalmente

**D-1. `ops/nginx/wikijuridica.conf` NÃO é config morta — é a fonte única de verdade.** Um agente da onda 3 concluiu o oposto. O cabeçalho do arquivo que a unit carrega diz, literalmente: *"GERADO por `tools/generate-nginx-standalone` … NÃO EDITE À MÃO … DERIVADO de `ops/nginx/wikijuridica.conf` — o vhost vivo, que é a fonte única de verdade"*. **Consequência grave:** toda correção de nginx apontada para o `standalone/` — inclusive o `if_modified_since before` que eu havia escrito em M6.b.1 — **seria revertida na próxima regeneração**. O achado sobrevive (`grep if_modified_since` nos dois arquivos → ausente nos dois, default `exact` vale); **o caminho de correção estava errado e está corrigido aqui: edita-se o vhost vivo e regenera-se o dedicado.**

**D-2. Deriva VIVA entre vhost e nginx rodando, agora — e eu rodei o check:**
```
$ ./tools/check-nginx-standalone-parity
  diretivas que decidem resposta — vivo: 67 | dedicado: 76
check-nginx-standalone-parity: FAIL
  - 1 diretiva(s) do vhost VIVO ausentes no nginx dedicado:
      - more_set_headers 'Vary: Accept-Encoding'
  Migrar assim regride o site. Derive o dedicado do vhost vivo, nao do arquivo de 06/08.
EXIT=1
```
**Aviso operacional que muda a ordem de execução:** a **primeira** edição sancionada de nginx regenera o dedicado e **embarca esse diff pendente junto**, como efeito colateral não intencional. **Resolver a paridade é pré-requisito de qualquer mexida em nginx**, não uma tarefa paralela.

**D-3. "Nenhum detector escalou o problema de cache" — falso, e é a armadilha A2 de novo.** Um agente olhou só o *tail* de `owner_alerts.jsonl` (inundado por 536 alertas `rede-banda` a ~1/min) e concluiu ausência. A contagem real: **48 alertas com `chave: "borda-cache-regra"`, severidade crítica, primeiro em 2026-08-21T17:53, último em 2026-08-26T10:08, todos `resolvido: false`, canais `enviado`.** *A emissão funcionou. O que falhou foi o exit code das ferramentas e o consumo do canal.*

**D-4. Propor `301` de `/area/pagina/N/index.md` viola regra escrita do projeto** — *"PROIBIDO: redirect como solução. URL existe = conteúdo existe"*. A outra frente propôs a correção compatível (mapear o `Link: rel=alternate` da fatia para o índice do hub + corrigir o `llms.txt`), e as duas frentes não se citaram. **Vale a que não cria redirect.**

**D-5. "Negociação falha em silêncio" — severidade rebaixada.** Servir a representação default quando a pedida não existe é **permitido pela RFC 9110 §12.5.1**; 406 é opção, não obrigação. E o cliente **tem** como perceber: o `Content-Type` anuncia HTML. O dano real (o agente não descobre a gêmea) já está inteiro em outros dois achados. Continua defeito — mas de conformidade, não crítico.

### Não corroborado — a apurar antes de agir

**N-1. Três corpos diferentes propostos para restaurar a Cache Rule.** `cache-rules.json` (19/08) **já tem** o bloco `vary` com `text/markdown` **e já exclui** `/mcp`, `/a2a` e `/.well-known/agent-card.json`; o `cache-rule-rollback.json` (12/08) **não tem** nada disso; e um terceiro agente propôs reconstruir à mão o que já existe. **Se qualquer um for executado sem consolidar, a deriva recomeça no ato da restauração.** **Pré-condição do PUT: um corpo canônico único.**

**N-2. Exclusões faltantes, que valem para todos os corpos propostos.** Conferido no JSON: **não há `/oauth`**, e de `.well-known` só o literal `agent-card.json`. Com `edge_ttl: override_origin 604800`, ficariam pregados por 7 dias: `/oauth/jwks`, `/oauth/token` e ~5 descritores `.well-known` que pedem `max-age=300`. **E `/sitemap.xml`, que declara `max-age=300` e não é excluído por nenhuma expressão** — pregar o sitemap por 7 dias é o oposto do que o portal precisa. A correção depende de a purga transacional alcançar as superfícies de descoberta, **e há precedente no repo de purga com alcance menor que o suposto** (`[[purga-borda-alcance-real]]`).

**N-3. O mecanismo da deleção é especulação; o ATOR não foi identificado.** Os carimbos (v12→v13→v14 em 9 s) são fato; "script de read-modify-write" é hipótese — três cliques de *delete* no painel produzem a mesma assinatura, e a janela 21-24/08 aparece como `interface: "UI"`. **Idem a injeção do `bridge.js`: pode ser beta da Cloudflare habilitado pelo próprio dono, não intrusão** — ninguém checou o ator antes de tratar como problema de segurança. **Tentei ler o ator: a API de versões do ruleset não expõe esse campo com token de zona** (`campos: description, id, kind, last_updated, name, phase, version`); exige o audit log da conta, que precisa da credencial de conta. **Fica como medição pendente, e é ela que impede a recorrência** — restaurar a regra sem saber quem edita o painel deixa o mesmo dedo no mesmo botão.

### Subestimado

**S-1. A injeção do `bridge.js` tinha duas severidades incompatíveis em duas frentes (crítico × média) e ambas subestimavam** — nenhuma a ligou à data da perda de cache. **Severidade única e máxima, um defeito, um nome.**

**S-2. Aquecer a variante Markdown dobraria o tráfego próprio** (+~62 mil req/dia) para manter quente um canal com **~1.100 requisições externas/dia**. Custo × benefício a pesar antes, não depois.

**S-3. ⚠ ACHADO NOVO E FORA DO ESCOPO PREVISTO: o uplink é WiFi 2.4 GHz a 72 Mbit/s.** É disso que falam os 536 alertas `rede-banda` (*"associado em 2.4 GHz, mas a banda esperada é 5 GHz"*). **Ninguém conectou o aquecimento de 474 MB/dia ao uplink degradado.** Um portal que serve bots por um rádio de 72 Mbit/s tem um teto físico que nenhuma otimização de bytes contorna.

**S-4. "Bot real = 3.008 req/dia" é medição de origem numa janela em que a borda ainda cacheava** — subconta a demanda real. Serve como ordem de grandeza, **não como baseline de dimensionamento**.

**S-5. `Last-Modified` uniforme é DELIBERADO, não acidente.** O publicador grava datado por **data editorial** de propósito (`[[gerador-datado-cas-correcao-v2]]`: *"gravaDatado usa data editorial; mtime não denuncia"*). **Trocar para mtime físico faria todo redeploy renovar `Last-Modified` de 10 mil páginas sem mudança de conteúdo — pior para revalidação, não melhor.** A correção proposta precisa de outra base. *(Esta é a frente que a onda 5 está apurando com fonte oficial, a pedido do dono.)*

### Faltando — falsos negativos que a auditoria não viu

**F-1. O canal de alerta está inundado.** 536 alertas `rede-banda` (~1/min, com `silenciado_por_cooldown` inconsistente — o último diz `true` e seguem sendo gravados) **afogando os 48 críticos**. As propostas tratam a reincidência do crítico; **ninguém trata o flood que o esconde**.

**F-2. Gate novo sobre canal morto é papel.** Três achados propõem criar checks novos (`check-edge-html-injection`, `check-served-robots-drift`, `check-binario-vs-fonte`) **sem notar que o mecanismo de detecção desta exata classe já disparou 48 vezes sem efeito**. **O defeito de processo — alerta sem consumidor que corrija — é anterior a qualquer gate novo e precisa ser resolvido primeiro.**

**F-3. Comentário que mente no próprio `CLAUDE.md`.** Ele descreve `./tools/check-http-smoke` como *"smoke HTTP: robots, sitemap, HTML sem runtime cliente"*; `grep -n robots tools/check-http-smoke` = **zero ocorrências**. O contrato do repo documenta uma cobertura que o script não tem. *(Reforça a ordem do dono: não confiar em comentário.)*

**F-4. `reload-wiki-server` não basta — é uma ação só, não duas.** Reload sem rebuild relança o binário de 20/08 13:08: os hubs corrigem, **mas o RSS continua 404 e as 18 mudanças de Go continuam fora do ar**.

### Confirmações que sobreviveram à crítica

- **Causa do `DYNAMIC`:** o Fable tentou refutar e falhou. Sonda dele: `favicon.ico` = HIT · `robots.txt` = MISS (elegível) · `sitemap.xml` = DYNAMIC · HTML = DYNAMIC — *"assinatura exata de zona só com extensões default, zero Cache Rule, incompatível com causa em Vary, proxy ou plano"*. Leu a API e confirmou `version 14, n_rules: 0`. **Três instrumentos, mesma conclusão.**
- **Armadilha A1 limpa nas seis frentes da onda 3** — todas usaram log do nginx ou série saneada; nenhuma somou o ledger cumulativo.
- **`.br` pré-comprimidos na transação não violam contrato** (hash do par entra na evidência de release).
- **Ninguém propôs desligar o aquecimento** — as propostas são restaurar a regra e usar a flag `--so-frios`, que **já existe** (`tools/warm-edge-cache:28,162-186`).
- **Nenhum dos seis propôs extrair o CSS** para arquivo externo — o contrato de "conteúdo completo no primeiro response" foi respeitado.

---

## M25 — O risco que o dono levantou: `.md` chegando ao Bing por IndexNow/WebSub

**A pergunta:** *"O Bing não pode ficar recebendo pelo WebSub ou IndexNow as URLs de `.md`, pois ele não vai indexar."*

**O que medi hoje, e o que a medição NÃO prova** (aplicando R15 — nada aqui é vitória):

| Verificação | Resultado | Instrumento |
|---|---|---|
| O gerador IndexNow deriva as URLs de onde? | **do sitemap** — `sitemap_urls(base)` lê os `<loc>` | leitura do código, `tools/generate-indexnow-incremental-submit:140-149,252` |
| O sitemap contém `.md`? | **zero ocorrências de `index.md` em 10.294 `<loc>`** | contagem própria sobre os 34 shards baixados |
| O ledger registra `.md` enviado? | **zero** — mas ver a ressalva abaixo | `grep` em `indexnow_direct_submissions.jsonl` (58 linhas) |
| O WebSub envia lista de páginas? | **não** — publica `hub.mode=publish&hub.url=<feedURL>`, **um único URL de feed** | `internal/websub/websub.go:88-119` |
| O feed contém `.md`? | **zero ocorrências** | sonda própria em `/feed.xml` |

**⚠ E aqui está por que isto NÃO fecha, exatamente como o dono avisou:** **o ledger do IndexNow não prova o que foi enviado.** Ele grava apenas `first_url`, `last_url` e `url_count` — **e o próprio código admite a limitação por escrito**: *"um intervalo alfabético não prova quais URLs estavam no lote"*. **Não existe forma de auditar retroativamente o que já foi submetido.** O que posso afirmar é sobre o **caminho do código de hoje**, não sobre o histórico.

**O risco é real e é FUTURO, e a preocupação do dono antecipa exatamente o buraco:** o IndexNow **deriva do sitemap**. Este plano contém propostas de **anunciar Markdown mais amplamente** (front matter, `rel=alternate` por entrada de feed, `llms.txt` mais rico). **Se em algum momento uma URL `.md` entrar no sitemap ou no feed, o IndexNow passa a submetê-la sozinho — sem ninguém decidir isso.** A separação não pode depender de quem escreve o código lembrar: **tem de ser estrutural** (R18), com o notificador de buscador **filtrando por canal**, e um gate que reprove URL não-HTML na fila de indexação.

**A frente dedicada está em voo (onda 7)** e tem duas tarefas aqui: trazer **fonte oficial** sobre o que Google e Bing declaram indexar quanto a `text/markdown` — hoje eu **não tenho** essa fonte, e portanto **não afirmo** que o Bing não indexaria —, e projetar o **ledger que prova** o que foi enviado, sem repetir o defeito de ledger cumulativo que já mordeu duas vezes nesta sessão.

---

## Onda 4 — causa, hardcode e identidade (3 de 5 frentes, `wf_1fbcd076-219`)

### O25 — Identidade de bot: forjar tier ilimitado custa uma string

**Veredito da frente:** *"A verificação de identidade de bot NÃO existe no caminho da requisição."* O único diferenciador em produção é o map `$wj_bot_allow` do nginx, que **casa User-Agent cru por substring não-ancorada** e entrega a pista ilimitada (chave de rate limit **vazia**) a quem se declarar.

**Medido no log real da origem (105.827 linhas, 25-26/08):** **6 requisições receberam `allow=1` vindas de IPs que não estão em NENHUMA faixa publicada e não têm PTR** — 4 declarando `ChatGPT-User` e 2 declarando `Googlebot` de um IPv6 brasileiro (`2804:d41:…`).

**E a verificação que existe offline produz falso negativo medido:** **34 de 34 requisições de `Google-InspectionTool`, todas com rDNS bidirecional confirmado** em `crawl-66-249-73-97.googlebot.com`, **são contadas como não-verificáveis** — porque o mapeamento `authenticates_agents` está **hardcoded** em `tools/generate-bot-ip-ranges` e prende o InspectionTool a `special-crawlers.json`, enquanto os IPs reais vivem em `googlebot.json`.

**As duas falhas têm a mesma causa-raiz, e é a que o dono nomeou:** a identidade do operador é **declarada em literal** dentro do script e do map do nginx, em vez de **derivada de `content/crawl_policy.json`**.

Demais achados da frente:

- **[ALTA] Grupo nomeado novo no robots.txt entra SEM GATE.** `crawl.ValidatePolicy` só percorre as listas `Required*` (`crawl.go:742-800`) e `LoadDefaultPolicy` lê o JSON verbatim. **A armadilha do Fable (T4.1) é real e o gate que a impediria não existe.**
- **[ALTA] 11 URLs de faixa de IP, 11 mapeamentos de agente e 2 métodos de rDNS vivem em literal Python**, fora do registry.
- **[MÉDIA] Drift unidirecional:** o nginx concede pista ilimitada a **4 agentes que o registry Go nunca classificou**, e nenhum gate reprova.
- **[MÉDIA] Web Bot Auth: cobertura zero — e o `log_format wj_main` nem captura `Signature-Agent`**, então o portal **não consegue medir quem já assina**. Instrumentar o log é pré-requisito de qualquer decisão sobre RFC 9421.
- **[MÉDIA] Três listas oficiais de faixa não espelhadas**, uma delas de bot que **está** no registry com rate tier próprio.
- **[BAIXA] As três URLs do Google apontam para o endereço antigo e só funcionam por 301.** Confirma O1.a.
- **[BAIXA] `meta-webindexer` e `Slackbot-LinkExpanding` estão no registry e no nginx, mas são invisíveis para toda a telemetria de identidade.**
- **[BAIXA] `requests_local_verification` é praticamente zero na série de borda — e o zero é ESTRUTURAL, não ausência de bot.**

### O26 — Hardcode: o inventário, e duas correções às minhas próprias medições

**Correção 1 à minha medição:** eu registrei em T4.2 que "a duplicação Go↔JSON não está divergindo hoje, mas vai envelhecer". **A frente foi além e conferiu as 32 entradas campo a campo: batem, e existe teste que compara o `BotRegistry` inteiro.** O JSON é **artefato gerado com guarda**. **A cópia sem guarda nenhuma é a do Python** — e é por isso que o problema apareceu lá.

**Correção 2, e é grave:** **`Meta-WebIndexer` — o crawler de citação do Meta AI, cadastrado em 13/08 justamente para ser rastreado — veio 4 vezes em 3 rotações distintas do log e não existe em série nenhuma da telemetria.** *O portal está cego para o sinal que essa frente existe para medir.*

**A fonte de verdade dos rótulos de área JÁ EXISTE e já cobre 100% do acervo:** `content/area_hub_editorial.json` tem **exatamente as mesmas 32 chaves** que o `published_manifest` tem de áreas — conferido nos dois sentidos, ambas as diferenças vazias. **O mapa de 32 rótulos no Go parece cobrir o mesmo espaço e não cobre: erra 5 para menos e 5 para mais.** Por isso **286 páginas** estão no ar dizendo *"Jurisprudencia"*, *"Noticias"* e *"Diarios"* sem acento, **no texto visível E no JSON-LD**. **A correção não inventa literal nenhum: acrescenta um campo ao JSON que já é a autoridade, deleta o mapa e deleta o fallback title-case.**

Demais achados:

- **[MÉDIO] 82 literais do domínio em Go de produção**, com `site.json` travado ao lado — **e um comentário que mente sobre isso**.
- **[BAIXO] `informationalAreaChannels`: canais públicos, telefones e URLs literais no Go**, cobrindo 11 das 32 áreas.
- **[BAIXO] 47 datas de conferência congeladas em código Go de produção.** *(O próprio agente corrigiu a medição: contou 57 com grep frouxo, o número com dois instrumentos concordando é 47. Registro a autocorreção — é o padrão que a sessão inteira exige.)*
- **[INFORMATIVO] `institutionalLinkLabels`: sem defeito medido**, mas a derivação óbvia mudaria o texto visível — cuidado ao derivar.

**✅ REFUTAÇÃO DE UMA PREOCUPAÇÃO MINHA — item 5 do briefing (número fixo em artefato público, que o dono chamou de "o pior tipo"):** varredura própria em `llms.txt`, `openapi.json`, `agent-card.json`, `api-catalog`, `agent-skills/index.json`, `feed.xml` e `security.txt` → **NÃO EXISTE nenhum**. O `llms.txt` afirma 10.070 e o manifesto tem **exatamente 10.070 linhas**, com as contagens por área conferindo; o `Expires` do `security.txt` é recomputado com `time.Now().AddDate(1,0,0)`. **Esses dois são o modelo de derivação a copiar nas correções de hardcode** — e vale dizê-lo, não só listar defeito.

### O27 — Os 24.367 `anchor_claim`: confirmado, com correção de magnitude e uma segunda parede

**Confirmado, e a verdade estrutural é mais forte que a minha estimativa.** Eu escrevi "95% não chegam à página". A medição dá **87,99% ausentes no HTML servido** e **90,97% ausentes no corpo autoral** — mas o número que importa é outro: **0% são publicados como citação atribuída à fonte.** Os 9-12% que "aparecem" são **prosa do redator que coincide, não citação**.

**Por que não chegam — não é gate, é ausência de destino:** `internal/v2publish/v2publish.go:249-266` projeta `official_sources` em `content.SourceProvenance` (`internal/content/content.go:34-40`), **estrutura que não tem campo para o claim**. Logo `renderProvenance` (`render.go:1681`) e `citationsFromProvenance` (`institutional.go:312`) **jamais podem emiti-lo**. **Nenhum gate barra porque o destino não existe.**

**Segunda parede, a montante:** o schema de página tem **lista fechada de 5 chaves** (`adjudicate_shard.go:80/711`) e **recusa** `urn_lex`, `vigencia_*`, `content_sha256` e o trecho oficial que o brief **já produz** (`generate_v2_writing_briefs.py:764`).

**O material para corrigir está pago e no disco:** **28 diplomas / 8.770 artigos com texto integral e sha** em `data/legal-corpus/`; **9.125 fontes (37,4%) resolvem hoje a artigo exato**, alcançando **5.642 páginas — 56,2% do acervo ativo**.

**⚠ Armadilha na publicação, apanhada antes:** **607 strings de claim se repetem em ≥2 páginas e não podem virar corpo visível** — seria molde/anti-template. A publicação exige as **duas camadas da DEC-032** e partição por repetição.

Demais achados desta frente:

- **[MÉDIA] Rótulo de fonte promete dispositivo específico e a URL entrega o documento inteiro em 6.091 casos.**
- **[MÉDIA] Nenhuma página publica vigência da norma**, em texto ou em dado estruturado — **embora o dado exista no pipeline**.
- **[MÉDIA] Nota de licença da fonte é constante única aplicada às 24.367 fontes**, contra a exigência da DEC-032 de **base legal POR FONTE**.
- **[MÉDIA] O gate `check-derived-authorial-floor`, que a DEC-032 declara como guardião contra página-espelho, NÃO EXISTE.**
- **[MÉDIA] Molde de quatro frases em 80 páginas de súmula derivada do STJ** — confirma.
- **[BAIXA] O `published_manifest` também perde `anchor_claim` e `license_note`** — o registro canônico de publicação não guarda o que a página afirma da fonte.
- **[BAIXA] O campo `uso` do legal-corpus declara `nunca_corpo_de_pagina`, não é lido por código nenhum, e CONTRADIZ a DEC-032 desde 2026-08-20** — comentário que mente, em dado.
- **[BAIXA] Não há `isBasedOn` no `Article`, e o nó `citation` não carrega texto** — o JSON-LD cita a fonte sem dizer o que ela sustenta.
- **[INFORMATIVO] O identificador estável para "como citar esta página" JÁ EXISTE INTEIRO no dado** e não é exposto em lugar nenhum. Confirma T5.7.

### O28 — A queda do Googlebot: SÃO DOIS EVENTOS, e a minha hipótese caiu

**Este é o achado que a frente dedicada entregou, e ele reescreve M22.** *"A evidência NÃO sustenta uma causa única. Sustenta DOIS eventos independentes que o repositório vinha tratando como um só — e é essa fusão que impediu o fechamento até hoje."*

#### Fase 1 — colapso abrupto em **2026-08-11T02Z** (não 12/08), de 977 → 40 paths/dia

**Hipótese sustentada, com CONFIANÇA MÉDIA e explicitamente NÃO PROVADA:** redução de taxa de rastreio disparada por **agrupamento de 5xx servido pela borda** ao Googlebot verificado.

**Sustentam:** 45 respostas 5xx (34× 530 + 9× 502) concentradas em 08-10T18Z (7), 08-10T23Z (12) e 08-11T00Z (27), **com o colapso 2 h depois** · o mecanismo é **literal na doc oficial** (*"reduces your site's crawling rate when it encounters a significant number of URLs with 500, 503, or 429"*) · 26 s de ausência medida de conexão do túnel dentro da hora 08-11T00Z.

**Enfraquecem, e a frente disse isso sozinha:** os 45 erros vêm de **um único snapshot de 48 h sobre dataset amostrado**, e a retenção de 8 dias da Cloudflare **já venceu — é irreproduzível** · a "dose-resposta em dois crawlers" que o repo alegava é **mais fraca do que constava**: o Googlebot **tolerou 13 erros em 08/08 sem reagir e ainda atingiu o pico de 4.297 em 10/08** · **a aritmética não fecha**: 26 s de origem inalcançável não produzem 27 erros no ritmo medido do crawler.

#### Fase 2 — não recuperação (12/08 até hoje), com um segundo evento que ninguém tinha registrado

**CONFIANÇA MÉDIA-ALTA:** supressão de **demanda** de rastreio — o Google **conhece** as URLs e **escolhe não gastá-las** —, agravada a partir de 18/08 por **o August 2026 spam update do Google, confirmado, com rollout de 18/08 a 21/08**, que **nenhum artefato do repositório menciona**.

**Sustentam:** o orçamento de erro está **limpo há 14 dias** (680 snapshots de 6 h; único erro: 1× 502 ao bingbot em 25/08) — **se fosse backoff por 5xx, a taxa teria voltado** · três inspeções no GSC mostram que **a descoberta funciona e o rastreio é que é recusado**: URLs nunca pedidas, **uma em shard fresco e outra em shard congelado**, ambas voltam **`Discovered – currently not indexed`** · a queda de impressões de **2.551 (17/08) para 256 (25/08), −90%, começa no primeiro dia do rollout do update**.

**⚠ Correção importante à leitura que eu tinha:** *"a queda de impressões começa em 18/08, não em 11/08. Entre 11/08 e 17/08 — todo o período do colapso de rastreio — as impressões SOBEM de 854 para 2.551."* **São dois fenômenos com datas, mecanismos e curvas distintas**, e tudo o que veio depois de 18/08 vinha sendo lido como *"a queda de 11/08 que não recuperou"*.

#### O que a frente REFUTOU por medição própria — inclusive a minha hipótese central

| Hipótese | Como caiu |
|---|---|
| **Content-Signal malformado quebrou o parsing** *(era a minha)* | **Só entrou no config em 12/08 09:03 — DEPOIS do colapso de 11/08T02Z.** E `git log -S 'serach'` devolve **vazio**: o erro de digitação **nunca esteve no ar**. |
| **A mensagem de commit `c0a10058`** | **MENTE.** Afirma que o erro "atravessou gerador, teste e gate"; o que existia era a **possibilidade** (o teste só conferia o prefixo). **Minha hipótese nasceu dessa mensagem, e a mensagem era a única fonte dela.** *(Exatamente o que o dono avisou: não confiar em comentário — e vale para mensagem de commit.)* |
| **robots.txt bloqueando** | **Reconstruído byte a byte nas três versões.** O único bloqueio era `Disallow: /*?*`, que atinge só URL com query string — **e nenhuma URL do acervo tem query string**. A correção de 11/08 21:58 veio **depois** do evento das 02Z. |
| **Sitemap** | A repartição por (data, área) entrou em **12/08 07:25 — depois**. |
| **Qualidade / thin content** | **As impressões SUBIRAM** durante todo o colapso do rastreio (854 → 2.551). O Google estava servindo **mais** do portal, não menos. |
| **Links internos explicam quais URLs ele escolheu** *(hipótese do próprio agente, derrubada por ele)* | Média de links de entrada: **9,16** nas já pedidas × **8,62** nas nunca pedidas; **mediana 6 e 6**. E o grafo é saudável: **1 órfã em 10.294**. |

#### Achados colaterais desta frente, todos acionáveis

- **[MÉDIA] `crawl_coverage_daily.jsonl` é TAMBÉM cumulativo e NÃO tem leitor canônico.** `googlebot/2026-08-12` tem **21 linhas**, e `paths_requested_that_day` assume `{0, 7, 8, 13, 40, 103}` em linhas diferentes — **103 é 2,6× o valor correto porque conta por string de User-Agent, somando as sondas do próprio repositório**. **Eu li esse arquivo, e o meu "40" está certo por sorte** (é o valor estável final). **É a armadilha A1 numa segunda fonte** — e pede o mesmo leitor canônico que o ledger de borda já tem.
- **[ALTA] `lastmod` congelado em 93,1% do acervo:** 9.582 de 10.294 URLs e 28 dos 34 filhos do índice ainda dizem **2026-08-06, vinte dias depois**. *"O `<lastmod>` é o único sinal do protocolo que diz ao crawler 'volte aqui'."* **É o motivo estrutural de não haver força puxando o rastreio de volta** — e conecta direto com a ordem do dono sobre retorno (Fase 7).
- **[MÉDIA] Ordinal de shard de sitemap foi RESSUSCITADO:** `pages-0032/0033/0034` responderam **410 Gone** e hoje servem **200** — **a identidade da URL foi reutilizada depois de um sinal de remoção permanente**, e é exatamente onde estão as 580 URLs com lastmod fresco. **Correção: alocar ordinal por marca d'água monotônica, nunca por posição no plano; ordinal aposentado responde 410 para sempre.**
- **[ALTA] Não existe instrumento que distinga "não achou" de "achou e recusou".** `measure-crawl-coverage` e `check-crawl-coverage-stall` só dizem *"a cobertura parou"* — **compatível com dois problemas opostos, de correções opostas**. É a ambiguidade que manteve a frente aberta desde 13/08. → **T7.1.**
- **[MÉDIA] O orçamento de erro não tem denominador nem causa na linha.** *"Sem denominador, 45 erros tanto podem ser 0,8% quanto 80%."*

**Postura que o plano adota a partir daqui:** a Fase 1 fica registrada como **hipótese de confiança média, não provada e hoje irreproduzível** (a retenção da Cloudflare venceu). A Fase 2 tem confiança média-alta e **dois componentes**, um deles externo e fora do controle do portal (o spam update). **Nenhuma correção deste plano depende de cravar a causa da Fase 1** — e é assim que deve ser.

---

## O29 — **Resposta ao dono: o `lastmod` deve continuar? SIM — e o defeito está na outra ponta**

> **Pergunta do dono:** *"Investigue se o lastmod deve continuar, se isso é necessário… pois isso pode engessar e enganar ou desmotivar bots. Ou se tem outra alternativa e sempre manter fresh."*

**VEREDITO DA FRENTE: MANTER os dois sinais — mas SEPARAR as fontes.** E a investigação **corrige três medições minhas**.

#### O `<lastmod>` do sitemap não mente — e essa parte do sistema é a única que já está certa

| Medição | Resultado | Instrumento |
|---|---|---|
| ~~lastmod × artefato em disco: 10.288 de 10.294 batem~~ | **⚠ DERRUBADO PELO FABLE — corroboração CIRCULAR.** `gravaDatado` carimba o mtime **a partir da** data editorial, então `lastmod == mtime` é **o mesmo dado contado duas vezes** (viola R3/R8 do Contrato do Dado Real). **Não vale como segundo instrumento.** | — |
| páginas cujo corpo editorial mudou desde 06/08 | **28** | diff de `body_sections` entre `4a0c2aac` e hoje |
| páginas cujo lastmod se moveu | **as mesmas 28 — 1:1, zero date-bumping** | **este é o instrumento que sustenta o veredito**, e o Fable o amostrou: 3 páginas com lastmod movido têm corpo diferente; 3 paradas em 06/08 têm corpo idêntico |
| `reviewed_at` movido para 20/08 em 9.467 páginas (revisão jurídica) | **lastmod NÃO se moveu** — quem manda é `content_revised_at` | `internal/content/last_modified_test.go:75-131`, que chama isso de *"peça anti-fraude"* |

> **⚠ Correção de método, e ela importa:** eu havia registrado "dois checks independentes". **Era um só.** A conclusão sobrevive — mas por **um** instrumento, e assim fica escrito.

**Fonte oficial, verbatim:**
- **Google** — *"Google uses the `<lastmod>` value if it's consistently and verifiably (for example by comparing to the last modification of the page) accurate."* (`developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap`, verificado 2026-08-26). **É exatamente a condição que este acervo cumpre de forma medível.**
- **Bing** — sem lastmod, *"search engines may delay crawling updated content or may over-crawl your website"*.
- **sitemaps.org** resolve a tensão com todas as letras: *"this tag is separate from the If-Modified-Since (304) header the server can return, and search engines may use the information from both sources differently."*

**Remover o `lastmod` destruiria o único sinal do sistema que está funcionando.** A resposta à preocupação do dono é: **ele não engessa nem engana — porque não está mentindo.**

#### O defeito real: o `Last-Modified` HTTP RETROCEDE NO TEMPO em 9.439 páginas

`gravaDatado` (`cmd/publish-v2-direct/main.go:2459-2465`) carimba o mtime de volta para a data editorial sempre que a reescrita seguinte encontra bytes idênticos. **Em 20/08 houve quatro publicações:** a primeira mudou os bytes (mtime = 20/08); **as seguintes acharam esses mesmos bytes e os carimbaram DE VOLTA para 2026-08-06T00:00:00Z**.

- **Viola RFC 9110 §8.8.2:** *"The 'Last-Modified' header field … provides a timestamp indicating the date and time at which the origin server believes the selected representation was last modified"* — **é da REPRESENTAÇÃO (os bytes), não da data editorial.**
- **E degrada o ETag:** o do acervo é `hex(mtime)-hex(size)`, derivado do mtime rebobinado — **abaixo da propriedade de validador FORTE** da §8.8.1 (*"unique across all versions of all representations … over time"*). **Duas versões diferentes podem receber o mesmo ETag.**
- **O repo JÁ TEM a implementação correta e não a usa no caminho estático:** `internal/httpserver/conditional.go:44-47` define `strongETag` como SHA-256 do corpo — **é o que o caminho Markdown já faz**. E o Google *"strongly recommends using ETag because it's less prone to errors"* (`Crawling December: HTTP caching`, dez/2024).

#### A ordem de correção — agora com a norma nomeando o caso

**NUNCA trocar `if_modified_since` para `before` enquanto o mtime puder retroceder.** A RFC 9110 §13.1.3 **descreve literalmente esta situação** ao justificar o comportamento de igualdade exata: *"…when the server has chosen to only honor exact timestamp matches (due to a problem with Last-Modified dates that appear to go 'back in time' when the origin server's clock is corrected or a representation is replaced)."*

> **⚠ Correção do Fable da onda 5, e ela é importante:** dizer que *"o `exact` é a única coisa que impede o dano"* **superestima o `exact`**. Ele **não protege** o cliente cujo `If-Modified-Since` é **igual** à data rebobinada — **o 304-para-página-que-mudou JÁ ACONTECE HOJE**. Medido nos dois lados: `IMS: 06 Aug 2026` → **304**, para página cujos bytes mudaram em 20/08; e o Fable confirmou na borda viva. **O `exact` só evita ALARGAR a janela; não a fecha.** Ligar `before` agora a **alargaria** — daí a ordem —, mas o vazamento existe desde já, e é o passo T2.2 que o estanca.

**Escala do problema, medida por dois instrumentos independentes:** `git show 4a0c2aac:…published_manifest.jsonl` (último commit de 06/08, 9.467 rotas) contra o manifesto de hoje → **9.467 de 9.467 `html_sha256` DIFERENTES: 100% do acervo teve os bytes alterados desde 06/08.** E `stat` no disco → **9.439 desses ainda declaram `mtime = 2026-08-06T00:00:00Z`**.

> **O risco em uma frase:** *qualquer intermediário — borda, proxy ou crawler — que revalide por `If-Modified-Since` recebe 304 e serve os bytes velhos por tempo indeterminado. Não há erro visível, não há 5xx, não há alerta: o cache simplesmente nunca aprende que a página mudou.*

**Ordem segura, com teste de aceitação por passo:**

| Passo | Ação | Teste |
|---|---|---|
| **0** | **Não tocar** em `if_modified_since` | `curl -H 'If-Modified-Since: <LM+1dia>'` tem de devolver **200**; se devolver 304, alguém ligou o `before` sem o passo 1 |
| **1** | **ETag forte de conteúdo no caminho estático**, gerado do `html_sha256` que o `published_manifest` já carrega (dado, não hardcode) — `map $uri $wj_etag` + `more_set_headers` | o ETag servido é idêntico ao `html_sha256` da rota, e muda **se e somente se** os bytes mudarem |
| **2** | **Parar a rebobinada do mtime** em `gravaDatado`, ou aceitá-la só quando `content_sha256` **e** `html_sha256` forem os mesmos da publicação daquela data | `Last-Modified` nunca anterior à última escrita real |
| **3** | **Só então** `if_modified_since before` no **vhost vivo** | as quatro datas de M6.b, com posterior → 304 |

**Servir os dois consumidores não exige escolher:** `lastmod` editorial correto (o que o **Bing** usa para escalonar rastreio) **+** ETag forte e 304 barato (o que o **Google** prefere no plano HTTP).

#### Três medições MINHAS que esta frente corrigiu

1. **"mtime dos HTML = 2026-08-05" era artefato de FUSO HORÁRIO.** O valor bruto é `2026-08-06T00:00:00Z` e **bate exatamente com o lastmod**. O shell roda com `TZ=-03` e meia-noite UTC aparece como 21h do dia anterior. **Toda medição de tempo daqui em diante se faz em epoch ou com `TZ=UTC` explícito.**
2. **"ctime = data de escrita real" é impreciso.** `os.Chtimes` **também move o ctime** — e `gravaDatado` o chama em toda publicação idempotente. **O oráculo de "mudou de verdade" é o hash**, que já existe em duas granularidades (`html_sha256` e `content_sha256`). **`ctime` não entra em nenhuma decisão.**
3. **A taxa de 304 do Googlebot é 1,9%, não 15,8%** — janela e instrumento diferentes; **os dois números podem ser verdadeiros**, e a medição válida é pela borda (`serie_saneada`), não pelo log de origem, que responde *"quanto a borda revalidou"*.

**E um erro do meu briefing:** mandei citar a **RFC 8674**, que **não trata de cache nem de `Last-Modified`**. A norma aplicável é a **RFC 9110** (§8.8.1, §8.8.2, §13.1.3, §13.2.2), complementada pela **RFC 9111** para frescor por `max-age`/`s-maxage`.

#### Achados colaterais desta frente

- **[MÉDIO] Sub-declaração de lastmod em 9.467 páginas pelo critério literal do Google.** O texto oficial diz: *"an update to the main content, **the structured data, or links on the page** is generally considered significant"*. O oráculo do portal (`content_sha256`) **ignora links e proveniência de propósito** — decisão razoável contra reenvio em massa ao IndexNow —, **mas o critério do Google é mais largo**. **Correção sem misturar os dois usos:** gravar **dois** hashes — o `content_sha256` atual continua governando o IndexNow, e um `significant_sha256` (corpo + links renderizados + proveniência) passa a governar o `<lastmod>`.
- **[MÉDIO] Comentário que mente, e o gate se apoia nele.** `check-lastmod-por-evento` declara que o caso "HTML novo com data antiga" não é reprovado porque *"o sinal honesto para ele é o Last-Modified HTTP, que o publicador já emite"*. **É falso no ar** — esse Last-Modified foi rebobinado pelo próprio publicador. **O gate passa verde apoiado numa garantia inexistente.**
- **[MÉDIO] Home e cinco institucionais: as únicas 6 URLs onde os dois sinais discordam.** A home é reescrita a cada publicação porque carrega a **contagem viva** de conteúdos por área, mas seu registro editorial não muda. **Para rotas derivadas (home, hubs, paginação), o lastmod deve vir do hash do HTML servido** — e o repo **já adotou essa regra** no `generate-indexnow-incremental-submit` para as 206 rotas derivadas.
- **[BAIXO] Formato do `<lastmod>`: 10.241 URLs só com data, 53 com data e hora.** Válido pela spec (a hora é omissível), mas **aquém do que o Bing pede** (*"use standard ISO 8601 … including both the date and time"*). **Correção honesta: registrar o instante UTC a partir de agora, e NÃO retroagir hora para as 9.585 linhas históricas** — inventar `00:00:00Z` onde não houve medição seria precisão fabricada.
- **[INFORMATIVO] IndexNow COMPLEMENTA o lastmod, não o substitui.** Nem a spec do protocolo nem o Bing afirmam que dispensa sitemap ou lastmod — **o próprio Bing recomenda os dois juntos, no mesmo post**. *"Temos IndexNow"* não é argumento para remover lastmod.
- **[BAIXO] ⚠ DIVERGÊNCIA ENTRE AGENTES — e eu a RECONCILIEI por medição própria.** Esta frente reportou `llms_txt_contagem_divergente: declara=10070 real=9792`; a onda 4 mediu `10.070 = 10.070`. **Medi eu mesmo, em 2026-08-26:**

| Verificação | Resultado |
|---|---|
| `llms.txt` declara | **10.070 páginas** |
| `published_manifest.jsonl` | **10.070 linhas** ✓ |
| **soma das 32 contagens por área declaradas dentro do próprio `llms.txt`** | **10.070** ✓ |
| sitemap | 10.294 (= 10.070 + 224 de hubs, paginação e raiz) ✓ |

  **O artefato é internamente coerente e bate com o manifesto por três caminhos.** O `9.792` do check vem de **outro critério de contagem** — e, portanto, **o suspeito é o CHECK, não o `llms.txt`**. Fica como item a investigar (qual população o check mede e por que difere), **não como defeito do artefato**. *Registro a reconciliação porque foi exatamente o tipo de conflito que o dono mandou não deixar passar — e porque o resultado inverte quem estava errado.*

---

## O30 — Frescor: o portal tem um CARIMBO, não um SINAL

**Diagnóstico da frente, em duas linhas:** *(1)* **todos** os canais de frescor derivam da **mesma data editorial de lote**, não do instante em que a página mudou — 93,1% das URLs do sitemap declaram `2026-08-06`, **50,6% das entradas do feed** declaram `2026-08-06T00:00:00Z`, e o `Last-Modified` HTTP é o mtime editorial. *(2)* O único canal de **push** que funciona (IndexNow) **só existe dentro da etapa 9/9**, depois da publicação na 8/9 — e como a fábrica falha antes da 8/9, **está parado há 6 dias; não há timer próprio para ele entre os 13 timers do portal**.

**Consumo real medido, e ele reordena a prioridade:**

| Canal | Consumo externo em 8 dias | Quem consome |
|---|---|---|
| **sitemap** (índice + 34 shards) | **693 leituras** | **Cloudflare-AI-Search 645** · Googlebot 48 |
| `/feed.xml` | **4 buscas externas** contra **396 internas** | praticamente ninguém — **o portal lê o próprio feed** |
| `/llms.txt` | 115 (maioria interna) | — |
| IndexNow | — | **última submissão 2026-08-20T16:46Z** |
| WebSub | — | **9 pings aceitos com 204 em 20/08, e o hub não buscou o tópico nenhuma vez** |

**→ Consertar o `lastmod` do sitemap vale mais que qualquer melhoria no feed.** O feed só vira consumível por agente depois de ganhar conteúdo integral e `alternate` para Markdown.

**Nota de método que merece registro — o agente derrubou o próprio achado:** ele ia publicar *"o hub nunca buscou o feed"* com base no log de origem (zero `FeedFetcher-Google` em 13 dias). **A Cloudflare mostrou 2 buscas em 19/08, invisíveis na origem porque naquele dia a Cache Rule ainda existia e foram servidas como `hit`.** O achado corrigido é **mais estreito e mais grave**: em **20/08, o dia dos nove pings aceitos**, as 97 requisições ao feed na borda foram **todas internas**. *É a armadilha A2 apanhada em tempo real, por segundo instrumento.*

**Achados da frente:**

- **[CRÍTICO] IndexNow só existe na etapa 9/9** — qualquer falha anterior silencia o push do portal inteiro.
- **[ALTO] O estado do IndexNow se contradiz:** **9.601 URLs marcadas "nunca submetidas" contra 52.838 submissões no ledger.** O ledger não prova o que foi enviado (só `first_url`/`last_url`), e o próprio código admite.
- **[ALTO] WebSub: `204` não prova entrega.** O hub aceitou e não buscou.
- **[ALTO] A borda remove o ETag do HTML** — o acervo fica sem validador forte e só pode revalidar pelo `Last-Modified` que retrocede. Confirma M6.c e O29.
- **[MÉDIO] O feed cobre 1.000 de 10.070 páginas (9,9%) e não implementa a paginação da RFC 5005**, criada exatamente para esse caso.
- **[MÉDIO] Nenhuma entrada do feed tem conteúdo integral nem `link rel=alternate`** para a gêmea Markdown que o portal já serve.
- **[MÉDIO] ⚠ O feed declara-se 16 horas mais velho do que é — e o `SKILL.md` publicado pelo portal manda o agente PARAR DE LER quando isso acontece.** **É autossabotagem publicada.**
- **[MÉDIO] O feed não emite o cabeçalho HTTP `Link rel=hub`** que a spec do WebSub pede ao publicador.
- **[MÉDIO] Não há canal incremental legível por máquina:** `/api/v1/pages` **não aceita parâmetro nenhum**, muito menos filtro por data. **É o que faria o agente perguntar "o que mudou desde X" em vez de revarrer 10 mil páginas** — ataca diretamente a ordem do dono sobre retorno.
- **[MÉDIO] Destinos, cadência e orçamento do IndexNow são constantes Go de política, não configuração.** Hardcode (R13).
- **[BAIXO] O mesmo shard de sitemap declara duas datas:** `2026-08-06` no índice e `13/Aug` no cabeçalho HTTP.
- **[BAIXO] 96% das requisições ao `/sitemap.xml` são do watchdog interno** — telemetria lida sem separar UA **superestima o consumo em ~24×**.
- **[BAIXO] Um crawler A2A real procurou o agent card em 5 caminhos convencionais e recebeu 404 nos 5.**
- **[BAIXO] RSS 2.0 sem `cloud`, sem `language`, sem `ttl`, e itens sem `content:encoded`.**
- **[INFORMATIVO] Um bot engoliu a pontuação do `llms.txt` e pediu `/educacao/index.md):`** — confirma M19 pela terceira vez.

**Desenho alvo que a frente propôs — e o princípio é o certo:** *"o sinal de frescor deriva do FATO DE MUDANÇA, não da etapa da fábrica."*
1. **Fato-fonte único:** a transação de promoção grava `{url, content_sha256, changed_at, change_kind}` num ledger append-only, com `changed_at` sendo **o instante da promoção (relógio)**, nunca a data editorial do lote.
2. **Reconciliador desacoplado**, em unit systemd própria, que compara o ledger de mudança × o ledger de emissão por canal e **emite só o delta**. **Se a fábrica morreu na etapa 4, o reconciliador ainda emite o que já foi promovido.**
3. **Ledger de prova por canal** (url, sinal, resposta, instante) — o que hoje não existe.
4. **Tudo parametrizado em `content/freshness_policy.json`** (destinos, lote, intervalo, janela do feed, tamanho de página RFC 5005, hub) — **derivado, não hardcoded**.

*O relatório completo da frente ficou em `/home/rafael/.claude/plans/…-agent-aff68af9d78dd4008.md` (4.776 B) e **deve ser copiado para o repo** junto com este plano (T-1).*

---

## O31 — Canais derivados: conformes no ponto de maior risco, frágeis em quatro outros

**No ponto que a DEC-032 marca como o mais perigoso, a medição ABSOLVE o portal** — e isso precisa ser dito com a mesma clareza dos defeitos: **nenhuma das 20 páginas de `/noticias/` reproduz a redação de matéria de tribunal.** O coletor **nem sequer armazena o campo `description`** do feed; o que a página cita é **o título, com link**. *O risco jurídico que eu havia levantado não se materializou* — medido em 2026-08-26, **a reconfirmar na execução** (R15).

**Mas a conformidade é frágil, e em quatro pontos está quebrada:**

- **[CRÍTICO] `check-derived-authorial-floor` — o gate que a própria DEC-032 nomeia como guardião da regra das duas camadas — NÃO EXISTE.** A regra vive só na prosa dos contratos.
- **[ALTO] O piso que existe mede a coisa errada:** `pisoDePalavras = 270`, repetido em **cinco geradores** (hardcode, R13), **conta o texto citado junto com o autoral**. Um espelho com comentário curto passa.
- **[ALTO] 50 páginas publicadas de `/jurisprudencia/` perderam o registro editorial** — **é o mesmo erro que trava a fábrica desde 21/08** (T6.2), e **o texto está inteiro em HEAD, recuperável**.
- **[ALTO] Página pública ÓRFÃ e INDEXÁVEL — confirmei pessoalmente.** `/diarios/ms-20260819/` responde **200 com 24.232 bytes** e traz `<meta name="robots" content="index,follow,max-snippet:-1">`, **sem existir no sitemap nem no `published_manifest`**.
  **Medi o universo inteiro para saber se havia mais:** das **10.298 rotas com `index.html`** em `public/`, **4 estão fora do sitemap e do manifesto** — e **3 delas são legítimas** (`/buscar/`, `/contato/advogado/`, `/fontes/planalto/`, todas `noindex,follow`). **Exatamente uma é o defeito.**
  **Isto viola a coerência de artefato que o `CLAUDE.md` declara INEGOCIÁVEL**, e mostra que `publishedmanifest.Validate` **não cobre o sentido `public/` → manifesto** — só o inverso. **Correção: dar registro à página ou tirá-la do ar, e fechar o gate nos dois sentidos.**
- **[ALTO] Nenhuma página derivada grava a base legal que a autoriza** — embora o registro coletado **já a traga pronta** (`base_legal`, `licenca`, `licenca_url`, `sha256_fonte`). O que sobrou dela na página é **prosa dentro de `official_sources[].name`**. A DEC-032 exige base **POR FONTE**.
- **[ALTO] A página de súmula apresenta a tese de Tema repetitivo sob o título "O que diz a Súmula N"** — **a equivalência é inverificável por construção**. É erro jurídico de atribuição, a classe que o `CLAUDE.md` marca como **P1 permanente**.
- **[MÉDIO] O molde alcança os CINCO canais**, não só as súmulas: **frases idênticas em 100% das páginas de cada canal**.
- **[MÉDIO] Sigla interna de órgão julgador (`S1`/`S2`/`S3`/`CE`) no texto visível de 280 de 323 páginas derivadas.**
- **[MÉDIO] Data em formato ISO no texto visível de 265 páginas derivadas.** *(Ambas violam PT-BR e anti-template.)*
- **[MÉDIO] O coletor de notícias não usa `internal/sourcecollect`:** sem consulta a robots, sem GET condicional, sem teto diário.
- **[MÉDIO] O ledger por requisição que a DEC-032 exige "Sempre" — e que o cabeçalho de `internal/sourcecollect` promete — NÃO EXISTE.**
- **[MÉDIO] As páginas de diário citam o espelho de uma ONG como "o link para o documento oficial".** Proveniência incorreta.
- **[MÉDIO] A licença do Informativo do STF — a ÚNICA base legal do canal — não é verificável a partir desta máquina e não tem cópia local.** **Sem ela, o canal inteiro fica sem fundamento declarado.**
- **[MÉDIO] Comentário que mente no coletor:** *"o `description` do STJ é IDÊNTICO ao `title`"* não é verdade.
- **[BAIXO] PT-BR quebrado nas páginas do Informativo do STF:** nome de ministro em caixa alta, taxonomia crua, **parêntese que nunca fecha**.
- **[BAIXO] Nove páginas derivadas redigidas e nunca publicadas** — trabalho pago parado no shard.

**Contagem por canal, medida no `published_manifest` pela chave `path` e corroborada por `public/` e pelos sitemaps:** `/noticias/` 20 · `/jurisprudencia/` 250 · `/sumulas/` 297 · `/diarios/` 8.

**Condições para retomar o frescor diário sem violar contrato:** (a) restaurar os 50 registros por gerador datado a partir de HEAD; (b) dar registro à órfã de MS ou tirá-la do ar; (c) o piso passar a medir **a camada autoral**; (d) o **ledger por requisição** passar a existir.

---

## O32 — Achados baixos fechados por medição: 9 confirmados, 1 refutado, 1 não reproduzido

O dono mandou que **todo achado entre e seja medido antes de virar tarefa** (R14). Esta frente fechou os 12 itens pendentes. **Três saíram MAIORES que a premissa.**

### ⚠ O32.a — Contradição entre agentes sobre qual config nginx é viva — e a reconciliação

**Dois agentes disseram coisas opostas, e a reconciliação importa para T0.4:**

- **Fable da onda 3:** *"`ops/nginx/wikijuridica.conf` é a fonte única de verdade; o standalone é GERADO e não deve ser editado."*
- **Onda 4:** *"`ops/nginx/wikijuridica.conf`, que produção NÃO CARREGA, foi editado e commitado em 2026-08-20 (`f8a25fd9`, +29 linhas) e a correção NUNCA chegou ao ar."*

**Os dois estão certos, e juntos formam o achado real:** o arquivo **é** a fonte de onde o dedicado é gerado, **mas o gerador não foi rodado depois daquela edição** — por isso as 29 linhas do commit `f8a25fd9` (*"o A2A ganha a capacidade de relato, e três referências deixam de ser falsas"*) **estão em produção zero**. É exatamente o que `check-nginx-standalone-parity` acusa hoje (FAIL, T0.4).

**E o agravante:** `tools/check-ingress-security-headers:216` **valida esse arquivo** e o comentário da linha 206 **o chama de "o arquivo vivo"** — **o gate testa o que não está no ar e passa verde**. *Comentário que mente, dentro de um gate, sobre o próprio objeto que ele mede.*

**Correção proposta — gate `nginx-config-alcancavel`:** lê o `ExecStart` da unit para descobrir o `-c` real, roda `nginx -T -c <esse arquivo>` para coletar o conjunto **alcançado**, enumera `find ops/nginx -name '*.conf'` e **reprova todo arquivo que não seja alcançado**. Fecha de uma vez os três órfãos (O32.b) e a deriva.

### O32.b — Três configs nginx órfãs, confirmadas

Confirma e amplia a minha medição de T0.3.b: `standalone/bot-policy.conf` e `standalone/server.conf` não são incluídos por nada, e o `wikijuridica.conf` — embora seja a fonte — **não estava refletido no que roda**.

### ⚠ O32.c — Contaminação de métrica DECLARADA pelo próprio agente

> *"CONTAMINAÇÃO DECLARADA: minhas ~110 sondas à borda nesta sessão saíram com UA próprio (`wiki-onda4/1.0`) mas **SEM `X-Warming-Request`** — violação da regra global do `CLAUDE.md` — e por isso **entraram em `organic_requests` de 26/08**."*

**Registro isto em destaque por três motivos:** é honestidade exemplar, do tipo que a sessão inteira exigiu; **vale para mim também** — parte das minhas sondas levou `X-Warming-Request: true` e parte não; e **significa que a métrica `organic_requests` de 2026-08-26 está contaminada por esta auditoria e não deve ser usada como linha de base**. A correção do item de credencial cobre também a ferramenta de sonda.

### O32.d — `organic_requests` está inflado de 16,1% a 31,9% por instrumentação própria

O campo sai com `basis: exact_raw_minus_warming_ledger` e o comentário do check afirma *"nenhum campo afirma exatidão que a evidência não sustenta"* — **enquanto 16% a 32% do número é a própria casa**. O log **já tem a solução**: o campo `warm=$http_x_warming_request` classifica categoricamente, e foi criado justamente porque a exclusão por prefixo de User-Agent **já falhou uma vez**.
**Correção:** promover `edge_cache_warm.jsonl` a **ledger de tráfego próprio** — toda ferramenta interna que sai para a borda grava ali, inclusive as sondas de auditoria. **É dever de anti-fraude**, mesmo sendo erro interno.

### O32.e — Sete páginas institucionais indexáveis e no sitemap sem linha no manifesto

`/`, `/aviso-legal/`, `/fontes/`, `/metodologia/`, `/privacidade/`, `/sobre/`, `/termos/` — todas com `index_policy=index`, todas no sitemap, todas com HTML em `public/`, **e a API responde 404 nelas**. No sentido inverso a diferença é zero.
**Isto reconcilia o 10.070 × 10.294** (M8) e conecta com M24: **as páginas que provam autoria e método não estão no manifesto, não estão no `llms.txt` e a API não as conhece.**

### O32.f — 28 URLs `/{area}/pagina/` servem conteúdo de hub quase duplicado, declarando `index`

`GET /familia/pagina/` devolve **200, 28.904 bytes**, com `<meta name="robots" content="index,follow,max-snippet:-1">` e `canonical` para `/familia/` — **mas o corpo NÃO é idêntico** ao de `/familia/` (sha `6e394f6a…` × `70ac0fd7…`). **28 URLs quase-duplicadas e indexáveis.**
**E o comentário do `nginx.conf` afirma que elas respondem `301→404`** — uma das **seis famílias de comentário do nginx que a medição contradiz**.
**Correção imediata:** essas 28 rotas saem com `noindex` enquanto não tiverem índice próprio.

### O32.g — O registry declara 60 r/m para treinamento e o nginx não tem zona de treinamento nenhuma

Confirma O12/T4.4 por outro caminho. **E o histórico de 429 é revelador: 9.501 `wikijuridica-audit/1.0` · 1.294 `cache-warm` · 996 `ratelimit-probe` · 886 `InfraAudit` · 298 `Audit/1.0` · 87 `curl-teste/1.0` — 100% ferramentas nossas, nenhum bot externo.**
**Correção:** ou o nginx materializa os tiers a partir de `crawl.DefaultRateTiers()` (uma zona por tier não-ilimitado), **ou o registry para de declarar tier que ninguém aplica**. A primeira é a correta.

### O32.h — Demais itens fechados

- **[MÉDIA] `robots.txt` com `Cache-Control` de um ano na borda contra 300 s na origem.** Fonte oficial: *"Google generally caches the contents of robots.txt file for up to 24 hours, but may cache it longer… may increase or decrease the cache lifetime based on max-age Cache-Control HTTP headers."* **O teto de 24 h não é garantido.** Correção: `browser_cache_ttl` da zona = *Respect Existing Headers*; **a origem já declara o TTL certo por rota**.
- **[MÉDIA] Tarballs de agent-skill sem diretório raiz** — extrair dois no mesmo lugar produz *"uma habilidade quimera"*: manifesto de A2A com scripts de MCP. **Não é erro do consumidor: é o formato do artefato que convida ao erro**, e o portal publica os três no mesmo diretório.
- **[BAIXA] `http://www.` custa dois saltos** — **único caso evitável em toda a matriz testada**. E o tratamento da pontuação residual **é o correto**: 404 imediato, sem soft-404 nem cadeia.
- **[BAIXA] `Content-Type` do sitemap difere por camada**, e `/sitemaps/sitemap-1.xml` responde **410 no nginx e 404 no Go** — mesma URL, dois status. **Nenhum dos dois é errado pela spec; a divergência é que é o achado.**
- **[BAIXA] `brotli_static` sobre zero arquivos `.br`** — a compressão funciona (verificado: `Content-Encoding: br` e `gzip`), **o que não existe é o "static"**.
- **[INFORMATIVO] A cauda de 9,37 s NÃO reproduziu em 60 amostras.** Mediana **261 ms**; as cinco mais lentas são hubs (0,7-1,1 s); `time_connect` entre 33 e 69 ms. **Mas a mediana de 261 ms já denuncia que a borda não cacheia.**
- **[INFORMATIVO] O fallback de credencial exige que a variável INVÁLIDA esteja presente.** Se o `ZONE_TOKEN` sumir, **seis ferramentas caem para a Global API Key com o token inválido e recebem 403** — `measure-crawl-coverage`, `generate-bot-agents-daily`, `check-crawler-error-budget`, `check-edge-traffic` e `check-edge-vary-contract` **param de medir em silêncio**, que é o modo de falha que este repositório mais teme.
- **⚠ [CONTRADIÇÃO RESOLVIDA POR MIM — a onda 3 estava certa e esta onda errada]** A onda 4 afirmou *"Amazonbot ESTÁ cadastrado e o nginx obedece o registry"*, refutando a onda 3. **Fiz o grep nos dois arquivos:**
  ```
  ops/nginx/wikijuridica.conf:112   ~*amzn-searchbot  1;
  ops/nginx/wikijuridica.conf:113   ~*amzn-user       1;
  ops/nginx/standalone/nginx.conf:206  ~*amzn-searchbot  1;
  ops/nginx/standalone/nginx.conf:207  ~*amzn-user       1;
  ```
  **`amazonbot` não aparece em nenhum dos dois.** As duas afirmações são compatíveis se separadas: **ele está no `crawl_policy.json`** (registry) **e NÃO está no allowlist do nginx** (`$wj_bot_allow`) — que é o único ponto onde o tratamento diferenciado acontece de fato. **Logo, o Amazonbot cai na pista genérica**, exatamente como a onda 3 disse, **e faz 111 requisições/dia**. **T4.5 confirmada.**

---

## O33 — Crítica Fable da onda 4: o triângulo que ninguém montou, e a Fase 1 rebaixada

### 🔺 F1 — O TRIÂNGULO, e ele muda a prioridade do plano inteiro

**Três achados estavam em silos e ninguém os conectou. O Fable conectou, e eu re-medi:**

| Peça | Medição |
|---|---|
| **Publicação em massa** | **9.467 das 10.070 linhas** do `published_manifest` aprovadas em **2026-08-06**, no ar em massa **~13/08** |
| **Spam update do Google** | rollout **18 a 21/08**, confirmado por chamada própria ao dashboard oficial |
| **Estoque com molde e thin** | **80/80** páginas de súmula com frase-molde idêntica, **publicadas** · `anchor_claim` **88-91% ausentes do HTML** · a política *"médio publica"* pôs no ar `word_count` **250-400** e **fonte insuficiente** |

> **A leitura que faltava:** *"Se um spam update derrubou 90% das impressões de um domínio que publicou ~9,7 mil páginas derivadas dias antes, o estoque com molde/thin é o principal CANDIDATO a alvo do update."*

**Consequência direta para este plano:** a **fila de refinamento** (molde, duas camadas da DEC-032, `anchor_claim` no corpo, súmulas com frase repetida) **deixa de ser cosmética e vira a resposta de engenharia à Fase 2 da queda**. Ela sobe da Fase 5 para prioridade de topo, ao lado de destravar a fábrica.

**Ressalva obrigatória (R15):** isto é **hipótese com correlação temporal forte e mecanismo plausível**, não causa provada. **Mas é a única hipótese que explica as duas coisas ao mesmo tempo** — a queda de impressões e o fato de o Google conhecer as URLs e recusar rastreá-las (`Discovered – currently not indexed`).

### D — Rebaixamentos que o Fable impôs, e eu aceito

- **A Fase 1 da queda do Googlebot é INDETERMINADA, não "confiança média".** A contra-hipótese do surto de descoberta **nunca foi confrontada de verdade**: a cobertura foi de 7.147 (12/08) para **7.271 (26/08)** — **~100-124 URLs novas em 14 dias, com ZERO 5xx desde 11/08**. E o mecanismo que o próprio Google documenta **prevê recuperação gradual quando os erros cessam** — **que não veio**. Isso é **incompatível** com "redução de taxa por 5xx" como causa única, e **compatível** com saciação (70% do acervo já rastreado) + autoridade baixa de domínio novo. **O que fica de pé é correlação temporal, e o plano não crava causa.**
- **Duas das seis evidências de "tier ilimitado forjado" eram autoprovocadas** — vinham da **mesma /64 do host de auditoria do portal**. **A evidência cai de 6 para 4**, e as 4 que sobram são reais (ChatGPT-User de IPs externos sem faixa publicada, todos com `allow=1`). *O agente usou o artefato da própria onda como prova de ataque de terceiro — erro da família A3.*
- **[NÃO CORROBORADO] "Comentário que mente" em `entitycandidate.go:216`** — a função devolve caminho **sem host**, e o comentário é verdadeiro para ela. **Os 81 literais de domínio em 46 arquivos são reais** (recontados), mas **este rótulo específico não foi provado**.
- **[NÃO CORROBORADO] Markdown sem front matter e o recorte de `informationalAreaChannels`** — instrumento único, por confissão dos próprios agentes.

### S — Subestimados, e um deles é sobre o meu próprio plano

- **🔴 S1 — O canal morto de alertas, e o número certo (dois Fables discordaram, e o segundo tem razão).**
  **⚠ Os dois números que registrei estão errados, pelo mesmo motivo:** *"48 alertas críticos"* (meu, e do briefing) e *"839 não resolvidos, ~118 críticos"* (Fable da onda 4) são **leituras de LINHA CRUA de um ledger cumulativo** — **a armadilha A1 numa TERCEIRA fonte**.
  **Medição deduplicada por chave (Fable da onda 5):** **841 linhas não resolvidas = 25 chaves distintas**; **críticas = 7 chaves distintas** (`borda-cache-regra`, `borda-origem`, `portal-fora`, `rede-externo`, `rede-uplink`, `tunel-conexoes`, `tunel-uplink`), **6 delas abertas desde 22/08**.
  **Regra que fica:** *qualquer número desse ledger sem dedupe por chave é leitura errada.* **O problema não encolhe** — **7 famílias de defeito crítico abertas há dias** é tão grave quanto 118 linhas —, mas o número tem de ser honesto.
  **E o diagnóstico do canal também estava errado:** não é que "o alerta funciona e ninguém age". `tools/notify-owner:159-223` **silencia repetição por cooldown**, e as últimas linhas do ledger saem com desktop e journal `silenciado`. **O alerta nem chega mais.**
  **E as cinco frentes da onda propuseram SEIS instrumentos novos sobre esse canal**, sem que nenhuma propusesse consertar o laço de resposta.
  > **É exatamente o padrão que eu mesmo escrevi em T1.4 e que o plano repetiu.** Fica reforçado: **T1.4 é pré-requisito de todo gate novo deste plano**, sem exceção.
- **S2 — A Inspection API não sustenta a régua proposta.** Teto de **10 chamadas/dia** no instrumento disponível: classificar as 3.023 URLs nunca pedidas levaria **~302 dias**. **A "série de fila de recusa" de T7.1 não nasce desse instrumento** sem outra credencial — e a proposta original não dizia isso.
- **S3 — O fix do `lastmod` produz date bumping se aplicado como escrito.** Derivar o lastmod como *"o maior instante de mudança entre as URLs que o shard anuncia"* está **certo para o shard no índice** e **errado se carimbado por URL** — marcaria centenas de URLs inalteradas com data nova. **O repo já tem gate contra isso** (`lastmod_sem_date_bumping: pass, urls_conferidas: 9873`). **Sem especificar a derivação por URL, ou mente para o Google ou o gate existente reprova a correção.**

### F3 — Tensão interna entre duas correções deste plano

**O gate proposto em T4.2** (*"as regras do robots têm de ser iguais à derivação das classes do `bot_registry`"*) **somado à reforma que registra `semrushbot`, `ahrefsbot`, `chrome-lighthouse` e `cloudflare-agentreadiness`** **força grupo nomeado no robots.txt** para bots que hoje caem no curinga — **e grupo nomeado descarta o curinga**. **É a armadilha T4.1 sendo reintroduzida pela própria correção.**
**Resolução:** a classe nova de observação **precisa vir com template que reproduza as guardas do curinga**, e o gate tem de verificar isso. **Sem as duas coisas, a reforma remove proteção existente.**

### O que o Fable re-mediu e bateu exato

286 HTMLs sem acento · mapa de breadcrumb com 5 chaves mortas e sem `jurisprudencia`/`noticias`/`diarios` · `area_hub_editorial.json` 32=32 nos dois sentidos · `66.249.73.97` em `googlebot.json` e fora de `google-special-crawlers.json` · `ValidatePolicy` só itera `Required*` · 25 tokens no map do nginx, 4 sem registry · `content.SourceProvenance` sem `AnchorClaim` · lastmod 9.582/580/63/50/19 · `crawl_coverage_daily` com 1.225 linhas e 21 duplicatas em googlebot/12-08 · **48 críticos `borda-cache-regra` não resolvidos** · **`check-derived-authorial-floor` inexistente (só citado em `DECISIONS.md:521`)** · spam update 18-21/08.

**E sobre hardcode:** *"conferi as seções 'sem-hardcode' de todos os achados — **nenhuma correção proposta acrescenta literal**; a única derivação furada é a do `lastmod` (S3)."*

---

## O34 — Crítica Fable da onda 5: uma contradição que eu colei, e dois falsos negativos

### ⚠ CONTRADIÇÃO FRONTAL entre dois vereditos que eu registrei lado a lado

- **A frente do `lastmod` diz:** *"o `<lastmod>` do sitemap NÃO mente… manter e proteger, não mexer."*
- **A frente do frescor diz:** *"o portal tem um CARIMBO, não um SINAL… deve virar `changed_at` de relógio."*

**Os FIXES convergem** (`significant_sha256` ≈ `changed_at` por URL). **As proses são incompatíveis, e eu as colei sem reconciliar.** A reconciliação, com a letra da fonte:

> Pelo critério **literal** do Google — *"an update to the main content, **the structured data, or links on the page** is generally considered significant"* —, a **sub-declaração em 9.467 páginas pesa MAIS que o [médio] que lhe foi atribuído**. É **exatamente o caso** em que o Google declara que **para de usar o `lastmod` do site inteiro** (*"if it's consistently and verifiably accurate"*).

**Veredito reconciliado, que é o que vale:** o `lastmod` **não mente sobre o que ele mede** (mudança de corpo editorial) — e por isso não se remove. **Mas ele mede MENOS do que o Google considera significativo**, e é essa lacuna que ameaça o sinal. **O sinal que o veredito quer proteger está em risco pelo próprio critério da fonte citada.** → **T2.3.b já incorpora a correção (`significant_sha256`), e sobe de prioridade.**

### Falsos negativos que a onda inteira não viu

**F-a — Ninguém perguntou COMO os gates deixaram `"6 As decisões que o STJ divulgou…"` chegar a 20 páginas em produção.** O censo de severidade (etapa 7/9) e os checks de PT-BR e de meta **aprovaram uma `meta_description` que começa com dígito colado em maiúscula**. **Corrigir o chamador (`main.go:467`) sem um teste de gate que reprove o padrão garante reincidência na próxima família derivada.** → entra em T6.5.

**F-b — O fix do ETag via `more_set_headers` entrou no plano como SUPOSIÇÃO.** Nenhum agente verificou se o módulo existe. **O Fable verificou: `libnginx-mod-http-headers-more` está instalado E já carregado** (`ops/nginx/standalone/nginx.conf:16`). **Desta vez passou** — mas *"é o padrão de fix não-verificado que a `ARQUITETURA_FIEL` proíbe"*. **Fica a regra: toda correção deste plano que dependa de uma capacidade tem de declarar onde ela foi verificada.**

### Não corroborado — número que eu não devo integrar

**A taxa de 304 do Googlebot de 15,8%** apareceu **sem instrumento apresentado** e é **contradita pelo único instrumento reproduzível da onda** (1,9% no mesmo log de origem; `bingbot` 1,6% bate nos dois). **Não integrar 15,8% sem a medição que o sustente.** *(Já corrigido em O29.)*

### O que o Fable conferiu na fonte primária e bateu verbatim

**Todas as citações decisivas conferem**, abertas por ele em 2026-08-26: Google `build-sitemap` (as duas frases) · Bing fev/2023 (*"may delay crawling updated content or may over-crawl"*) · **RFC 9110 — linha 5.984 do txt tem literalmente `Last-Modified dates that appear to go "back in time"`** · §8.8.1 *"unique across all versions"* · §13.1.3 *"earlier or equal to the date provided"* · RFC 4287 §4.2.15 · **RFC 8674 (a correção do meu briefing pelo agente está certa)** · sitemaps.org (*"separate from the If-Modified-Since (304) header"*) · **WebSub, "W3C Recommendation 02 June 2026"**, inclusive o *"at least one Link Header"* · **Lei 9.610 art. 46, III e VIII no LEGIN — a miscitação no coletor é real.** **Nenhuma citação derrubada.**

### E a lista do que ele re-verificou pessoalmente, para não se re-verificar de novo

`gravaDatado` rebobina o mtime (código lido; epoch `1785974400` medido) · deadlock 5/9-antes-de-6/9 real (`run-daily-content:303-311` sai com exit 1 **antes** do commit) · STF lê só o último glob e sobrescreve (HEAD=50 × disco=4) · **o gerador de notícias é acumulativo (`main.go:148-160`) — o padrão a copiar existe** · bug do `plural` confirmado · `v2publish.Page` sem `publication_date` confirmado · **`check-derived-authorial-floor` nomeado em `DECISIONS.md:521` e inexistente em Go e em `tools/` (grep zero)** · CC BY 4.0 global confirmado (`structured_data.go:64`) · docstring do `check-lastmod-por-evento` promete controle que não existe · **borda remove o ETag: origem devolve `ETag: "6a73ce80-5ee7"`, borda não devolve** · home com lastmod 06/08 e mtime 20/08 17:31:41 · 9 pings WebSub 204 em 20/08 e nenhum depois.

---

## 🔴 M26 — VIOLAÇÃO ANTI-FRAUDE VIVA, E ELA É DESTA SESSÃO

**A crítica Fable da onda 4 apanhou, eu confirmei, e a origem é a minha própria operação. Registro com atribuição porque esconder seria a falha maior.**

**Medição própria no log do nginx (15 arquivos, 20 a 26/08):**

```
140 requisições com User-Agent de bot REAL vindas da própria rede
 26 delas SEM o header X-Bot-Simulation
```

**A ocorrência mais grave, e é de hoje:**

| Quando | Origem | User-Agent | Caminho | `bot_sim` | Passou pela borda |
|---|---|---|---|---|---|
| **26/08 08:13:51** | IPv6 `2804:d41:c05c:2e00:…` (rede do dono) | `Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)` — **forma nua** | `/familia/abandono-afetivo-indenizacao/` | **NÃO** | **sim (`cf_ray`)** |
| **26/08 08:13:51** | idem | idem (2ª requisição) | idem | **NÃO** | sim |
| **26/08 08:13:51** | idem | **`GPTBot/1.2`** | idem | **NÃO** | sim |
| **26/08 08:13:51** | idem | **`GPTBot/1.2`** (2ª) | idem | **NÃO** | sim |

**Isto viola a proibição literal do `CLAUDE.md` global:** *"PROIBIDO: self-warming/requests com User-Agent de bots reais (GPTBot, ClaudeBot, etc.) — FRAUDE"*.

**Três agravantes, todos medidos:**

1. **Não é caminho sancionado.** `tools/check-what-bots-see-externo` **proíbe explicitamente esse UA** e exige `X-Bot-Simulation: true` (linha 77); os UAs de `check-what-bots-see:67-68` **têm sufixo `Chrome/125`** — o que apareceu no log é a **forma nua**, que nenhuma ferramenta do repo emite.
2. **Atravessou a Cloudflare.** Têm `cf_ray` — **não ficaram em `localhost`**. Foram contadas como tráfego real de Googlebot e GPTBot pela borda.
3. **Poluem toda série contada por string de UA** — é a **mesma família de contaminação** que fez 12/08 render "103" em vez de 40 no `crawl_coverage_daily`. **Ou seja: esta auditoria contaminou o dado que estava auditando.**

**Atribuição honesta:** o horário (08:13:51 de hoje) cai dentro da janela em que as ondas 3 e 4 estavam ativas. **A origem é um agente que eu lancei.** Não vou empurrar para "não atribuído": **a responsabilidade é da orquestração, e é minha.**

### 🔴 M26.a — E a mesma classe de falha é MINHA, e é ANTERIOR

**O advisor apontou que a minha autoacusação estava incompleta, e ele tem razão — uma autoacusação pela metade é a mesma doença que o dono nomeou.** Registro por inteiro:

| O que eu fiz | Quando | Defeito |
|---|---|---|
| Sonda de M2 — **303 URLs × 2 requisições** (`index.md` + `Accept: text/markdown`) | ~07:40 | **sem `X-Warming-Request`, sem UA identificado** (curl default) |
| Coleta do sitemap — **34 shards** | ~07:42 | idem |
| Probes de M6, M7, M12, M14 (headers, MCP, A2A, `.well-known`, feeds, `llms.txt` de área) | 07:45-08:50 | idem |
| Sonda de M24.a com **`?utm_source=chatgpt.com`** | ~08:52 | **com** UA e header — **mas gerou o único registro de "citação por ChatGPT" do log inteiro**, que é meu |

**Só passei a usar `-A 'wiki-auditor/1.0 (auditoria interna)' -H 'X-Warming-Request: true'` depois que o hook `protect-bot-ratelimit.sh` me bloqueou, por volta de 08:50.** **Antes disso, ~700 requisições minhas entraram na telemetria como tráfego externo.**

**Não usei UA de bot real** — isso é a diferença entre a minha falha e a do agente, e é uma diferença que importa. **Mas o efeito na métrica é o mesmo**, e o `utm_source` que eu gerei é **exatamente** o falso positivo que a onda 7 identificou como *"a fraude de métrica já armada no dado"*.

**T-2 ganha, portanto, um segundo item:** **excluir da telemetria de 2026-08-26 também as minhas ~700 sondas**, não só as 26 do agente — e **a linha de base de 26/08 fica marcada como contaminada por esta auditoria inteira**, minha parte incluída.

**A lição estrutural é a mesma dos dois lados:** o hook protege o shell do orquestrador e **não alcança nem o subagente nem o começo da minha própria sessão**. **Regra que só existe em prosa não é controle.** O gate que reprova no log é o que fecha isso — para agente e para mim.

**Contexto que não é desculpa, mas é fato:** há também **20/08 15:59:11 com `bot_sim=SIM`** — várias sondas corretas, marcadas, de `127.0.0.1`, do `check-what-bots-see`. **A ferramenta sancionada funciona.** O problema é agente escrevendo `curl -A` à mão.

### Correção — e ela é estrutural, não disciplina

**T-2 (entra ANTES da Fase 0, junto com T-1):**

1. **Purgar a contaminação da telemetria:** marcar as 26 requisições identificadas como tráfego próprio nos ledgers de 20-26/08, e **declarar no plano que as séries desses dias estão contaminadas** — já feito em O32.c e aqui.
2. **Fechar o buraco no ponto certo.** O hook `protect-bot-ratelimit.sh` **existe e funciona** — ele me bloqueou nesta sessão quando a palavra "Googlebot" apareceu num `echo`. **Mas ele não alcança o que roda dentro de um subagente de workflow.** A correção é fazer a guarda valer **na borda de saída**, não só no shell: o gate `check-bot-telemetry-honesty` passa a **reprovar** quando o log registrar UA de bot real sem `bot_sim=true` vindo de IP próprio.
3. **Prompt de agente deixa de ser o único controle.** Toda onda desta sessão levou a proibição no prompt — **e ainda assim aconteceu**. *Regra que só existe em prosa não é controle; é esperança.* O log já tem o campo (`bot_sim`) e a classificação: **falta o gate que reprova.**

> **Registro isto como o achado mais desconfortável da sessão, e o deixo em destaque de propósito.** O dono mandou: *"não declarar nada vencido… pode ser mentira do repo, ou agente pode ter se enganado"*. **Aqui o agente não se enganou sobre o repo — ele violou o contrato.** E foi a **crítica adversarial que apanhou**, não nenhum gate. É exatamente por isso que o Fable existe.

---

## O35 — Ondas 6 e 7 (parciais): o inventário, o deploy, o serviço e o canal certo

### O35.a — **Você estava certo sobre o `.md`: a ausência dele nos canais de buscador é ACASO, não regra**

**A frente dedicada mediu e o veredito é mais grave do que a pergunta:**

> *"NENHUMA URL `.md` sai hoje por IndexNow nem por WebSub, e a razão NÃO é uma trava desses notificadores: é o acaso de o sitemap não ter `.md`. **Não existe, em lugar nenhum do repo, um invariante que PROÍBA uma URL não-canônica de entrar num canal de buscador** — a ausência de `.md` é propriedade emergente do sitemap, não regra verificada."*

**E as três mudanças que este próprio plano previa atacam exatamente esse ponto cego:**
1. expor Markdown no sitemap → **leva `.md` ao IndexNow por construção**;
2. feed com `rel=alternate` para Markdown → **leva `.md` ao Bing, porque Google e Bing aceitam Atom/RSS COMO sitemap**;
3. `llms.txt` mais rico → **já está no ar**.

**Correção central proposta, e é elegante porque não usa lista de extensões:**
> **Um invariante único, derivado do dado: todo canal de buscador emite somente URL cujo `canonical` é ela mesma.** Isso **exclui a gêmea `.md` para sempre** — ela carrega `Link rel=canonical` apontando para o HTML **por construção**.

**Achados desta frente:**
- **[ALTA] ⚠ CORREÇÃO DE FATO, e o agente derrubou o próprio achado:** a linha *"Googlebot buscou `index.md` em 13/08"* que ele mesmo havia levantado **é ENSAIO INTERNO** (`bot_sim=true`, header `X-Bot-Simulation`, IP fora das três faixas Google do repo). **Medido: ZERO fetch de `.md` por Googlebot verificado e ZERO por bingbot em 14 dias.**
- **[ALTA] Markdown está ausente da lista oficial de tipos indexáveis do Google.** Para o Bing **não há lista oficial** — o que existe é recusa pública e primária. *(Fonte a conferir no Fable.)*
- **[ALTA] Uma única `<loc>` `.md` no sitemap REPROVA a submissão IndexNow INTEIRA** — **mata o canal do Bing em vez de excluir a URL**. O modo de falha é catastrófico, não gracioso.
- **[MÉDIA] `/llms-full.txt` anuncia 10.071 URLs `.md` em `text/plain`, sem `X-Robots-Tag`, com `robots.txt` liberado para Bingbot e Googlebot** — **é a única rota que já expõe `.md` em massa a buscador**.
- **[MÉDIA] O `Link rel=alternate` para Markdown é idêntico para agente e para buscador** — não há diferenciação de canal.
- **[BAIXA] Não existe arquivo de faixas para os *user-triggered fetchers* do Google, e o arquivo com esse nome no repo é outra coisa.**
- **[ALTA] A matriz canal × consumidor:** o registry **já tem `policy_source` por bot** — **faltam a coluna de FORMATO e a de SINAL DE MUDANÇA**.

### O35.b — Inventário dos canais: **7 declarados, UM produz**

| Medição | Valor |
|---|---|
| Canais de conteúdo automático declarados | **7** |
| Canais que produzem página nova **por natureza** hoje | **1** — `noticias-oficiais`, ~6/dia |
| Última publicação de **qualquer** página | **2026-08-20** (360 páginas). **21 a 26/08: ZERO** |
| Registros do manifesto vindos de canal automático | **358 de 10.070 — 3,6%** |
| Registros ancorados em data do dia | **28 — 0,3%** |
| Units do portal | **18 das 19 MEDEM; uma só PRODUZ** |

**🔴 E o achado que libera semanas de frescor com uma linha:** os tetos **`-limite 200`** e **`-limite 80`**, **hardcoded** em `tools/run-daily-content`, **valem exatamente o número já publicado (200 e 80)** — então os dois maiores canais têm **cadência real ZERO**, enquanto **989 temas e 58 súmulas já redigíveis ficam de fora todo dia**. **1.047 páginas prontas, barradas por dois literais.** *(R13 em estado puro: o hardcode não só engessa — ele parou a produção.)*

**Demais achados:**
- **[ALTA] `collect-normas-federais` roda todo dia e NÃO TEM CONSUMIDOR:** 610 KB coletados, **60 normas/dia**, **zero páginas** — o canal `/leis` não tem produtor. **É a única fonte diária-por-natureza com licença de domínio público**, e está sendo coletada para o nada.
- **[ALTA] O mesmo padrão de sobrescrita do STF está em `generate-stj-tema-pages` e `generate-stj-sumula-pages`** — *"hoje é inofensivo por acidente"*. **Três geradores com a mesma bomba.**
- **[MÉDIA] O ledger da onda declara 323 páginas geradas num dia em que produziu 11** — **conta regeneração como produção e engana em 29×**.
- ~~**[MÉDIA] 280 páginas são reverificadas na fonte todo dia e `verified_at` não alimenta o `lastmod`**~~ — **⚠ DERRUBADO PELO FABLE DA MESMA ONDA (O40), e o achado ficou aqui sem a marca até a auditoria de completude apanhar.** `internal/content/content.go:129-137`: *"NASCE FORA DA CADEIA DE `LastModified()` DE PROPÓSITO… seria carimbo por decurso de varredura, exatamente o que a doc do Google exclui"*, com **teste-guarda `TestLastModifiedIgnoraSourcesVerifiedAt`**. **Não é defeito — é contrato testado.** *(O fato de 280 páginas serem reverificadas todo dia continua verdadeiro e é positivo; o que cai é chamá-lo de defeito.)*
- **[MÉDIA] `diarios-municipais` seco há 4 dias e a onda não registra falha:** janela fixa de "ontem" **sem cursor**, e **coleta zero sai com exit 0**.
- **[MÉDIA] A malha de links internos das notícias vê 401 de 10.070 rotas e liga zero páginas.**
- **[BAIXA] `generate-entity-pages` é um sexto gerador desconectado:** 799 candidatos, 54 rascunhos no disco, **zero no ar**.
- **[BAIXA] `collect-stj-precedentes-qualificados` existe, tem teste próprio e não está na onda.**

**Ordem de ataque proposta por (páginas novas/dia) ÷ esforço:** 1º **STF read-all** (esforço mínimo, o padrão correto já existe no gerador irmão; devolve 50 páginas e **destrava as 11 líquidas/dia de todos os canais** — *é o único item que muda o estado do portal hoje*); 2º **inverter as etapas 5/9 e 6/9** (uma troca de ordem no shell); 3º **derivar os tetos do estoque** (libera 1.047 páginas); 4º malha de links e cursor de diários; 5º construir o gerador de normas federais.

### O35.c — Deploy diário: **não há, e nunca houve** — e ligar o automático hoje seria perigoso

**Etapas 6/9 (commit), 7/9 (censo), 8/9 (publicação) e 9/9 (prova + IndexNow) têm contagem ZERO em 6 execuções** — corroborado por **zero diretórios `publish-rollback-*` depois de `20260820-190544`** (o publicador cria um **antes** de qualquer escrita, então ausência de snapshot = ausência de publicação).

**Custo NÃO é o obstáculo:** a onda gasta **143-200 s de parede e 15-33 s de CPU**, e o commit é leve.

**🔴 O caminho perigoso, medido — e é por isto que o automático não pode ser ligado hoje:**
> Uma interrupção **entre a escrita do sitemap e a do manifesto** deixa **sitemap escrito sem manifesto correspondente**, o que **aborta o boot do servidor Go sem teto nenhum**; com `Restart=always`, `RestartSec=5` e `StartLimitIntervalSec=0`, **o põe em laço infinito de reinício — e a própria etapa 9/9 reinicia o servidor nesse estado.**
> **E a janela do systemd (5.400 s) é MENOR que a soma dos tetos declarados das próprias etapas (12.900 s)** — ou seja, **o SIGTERM do systemd é um gatilho plausível, não hipótese**.

**Pré-requisitos obrigatórios antes de ligar o deploy automático:**
1. **Quarentena por shard** — hoje *"4 páginas defeituosas do STF retiveram 319 páginas limpas"* das outras quatro famílias.
2. **Barreira transacional entre sitemap e manifesto.**
3. **Lock que sobrevive a sinal** — o atual é `O_EXCL` **sem tratador**, e um SIGTERM **deixa lock órfão que trava toda publicação seguinte**.
4. **Commit do resultado da publicação** — hoje **nada commita**: manifesto, `pages.json` e censo ficam sujos.
5. **Limpeza do `var/on-demand-cache`** (**120 MB, intocado desde 20/08**) — a onda não faz, e **isso reproduz exatamente o bug de 2026-08-06** que `tools/deploy-publico` existe para evitar.
6. **Corrigir o `RESTORE.md`, que ensina a ESVAZIAR o manifesto** — destruindo a coerência que o contrato chama de inegociável.
7. **Tetos de tolerância do boot são constantes fixas (10 e 25)** calibradas para 9.710 páginas, num projeto que mira centenas de milhares. **Hardcode (R13).**

**Comentários que mentem, achados aqui:** a unit diz que o binário Go é construído no `ExecStartPre` — **e não há `ExecStartPre` nenhum** (*a onda diária nunca faz deploy de binário*); e a ferramenta de pareamento afirma custo de *"build Go de minutos"* por tentativa — **medido, são 12,5 s**.

**Risco histórico medido:** *"em 30 dias houve UM dia de publicação, e ele introduziu ao menos três classes de defeito no ar."* E o **censo de severidade está congelado em 20/08**, com **92% do acervo classificado como MÉDIO** e a fila de refinamento com **uma única linha**.

### O35.d — O portal como serviço: **construiu o certo e entrega no canal errado**

> **Veredito:** *"O portal JÁ CONSTRUIU, com qualidade alta, quase tudo que um agente precisa para CITAR — e entrega esse material ao canal errado."*

`/api/politica-de-uso.json` traz **SPDX `CC-BY-4.0`**, **`attribution_string` pronta** (*"Rafael Toledo, OAB/RJ 227191 — wikijuridica.com.br"*), escopo separando texto autoral de texto oficial, e fundamento na Lei 9.610/98. O JSON-LD traz `license`, `usageInfo`, `author`, `reviewedBy`, `citation`, `@id`.

**E nada disso chega onde os agentes leem.** Medido em 2026-08-26 por `grep -oi licen`: **ZERO ocorrências no `.md` servido (4.699 B) e ZERO na resposta do MCP `ler_pagina` (10.138 B)**.

> **O portal licenciou o acervo para o canal que os agentes menos usam:** o HTML responde por **12,8%** do tráfego de bot de IA; Markdown e MCP, por **86,5%**.

**🔴 O funil mede ZERO — e a fraude de métrica já está armada no dado:**
- Em **882.137 linhas de log (14 dias)** há **3 valores reais de `utm_source`**: dois `ig` e **um `chatgpt.com`**.
- **Esse único é o próprio auditor interno** (UA `wiki-auditor/1.0`, `warm=true`) — **é meu, desta sessão**.
- **Referers de produto de IA (chatgpt, openai, perplexity, copilot, gemini, claude, you.com, phind, deepseek, grok, mistral): ZERO.**
- **Citações reais que trouxeram humano: zero medido.**
- > *"O único contador que alguém construiria ingenuamente (`grep utm_source=chatgpt.com`) marcaria **100% de tráfego próprio como citação** — a fraude de métrica que o contrato proíbe **já está armada no dado**."* **T4.7 tem de nascer com essa exclusão.**

**Onde o portal perde, dito sem indulgência:**
- **(a) Licença** — perde por não entregar *in-band* no formato que o agente lê. *"Um LLM atribui pelo que está na janela de contexto, não por um arquivo de política que ele teria de buscar à parte."*
- **(b) Frescor** — perde feio: **9.582 de 10.294 declaram `lastmod 2026-08-06`**, e o `Last-Modified` diz `06/Aug` **enquanto o corpo do próprio Markdown diz "revisado em 2026-08-20"**. **Duas datas contraditórias na mesma página.**
- **(c) Âncora normativa** — **ganha em prosa** (*"Lei nº 13.105/2015, art. 373 — verificado em 2026-07-31"*), **perde em máquina**: nenhum campo estruturado, e `source_id` é slug, **não URN LexML** — apesar de `cmd/collect-oracle` **já manipular `urn:lex`**.
- **(d) Formato barato** — **GANHA, e é o ativo real.**

**Demais achados:**
- **[ALTO] O único ativo que muda todo dia é invisível ao agente:** o corpus de normas federais coletado hoje **não está em `llms.txt`, sitemap, feed nem em lugar nenhum**.
- **[MÉDIO] As três ferramentas de agente são as mesmas em MCP e A2A, e nenhuma devolve data ou fonte** — *"o agente não consegue ranquear por frescor nem julgar"*.
- **[MÉDIO] O Markdown obriga o agente a fazer NLP em português** para extrair o que deveria ser campo.
- **[BAIXO] `Cache-Tag` ausente na resposta Markdown** — a purga por tag **não alcança o formato que 86,5% dos bots consomem**.
- **[BAIXO] Toda página Markdown afirma ao agente que o `llms.txt` é "o mapa completo das páginas públicas" — e o `llms.txt` lista 85 URLs, não 10.070 páginas.** *(Afirmação falsa servida a agente.)*
- **[BAIXO] `Content-Signal` viaja só na resposta Markdown e não no HTML.**

---

## M27 — O `/mcp` É procurado todo dia, sem queda — e eu tinha medido isso errado

A onda 7 reportou que `/mcp` recebe *"20.591 requisições de 635 IPs distintos, todo dia, sem tendência de queda"*. **Isso contradiz frontalmente a minha M23, que contou apenas 134 requisições a endpoints de protocolo. Refiz a medição.**

**Medição própria, log do nginx, 10 dias, `/mcp` + `/a2a`:**

| Métrica | Valor |
|---|---|
| Requisições | **15.161** |
| IPs distintos | **488** |
| Métodos | POST 13.882 · GET 1.031 · HEAD 216 · OPTIONS 21 · DELETE 11 |
| Por dia | 1.671 · 1.576 · 1.835 · 1.815 · 1.186 · 1.032 · 1.131 · 1.886 · **2.107** · 922 (dia em curso) |
| Status | **200: 9.819** · 202: 3.692 · **405: 1.115** · 400: 228 · **404: 163** · 499: 85 · 403: 29 · 401: 4 |

**Meu erro em M23 está identificado:** eu filtrei por **User-Agent de bot de IA conhecido por nome** (`gptbot`, `claudebot`, `oai-searchbot`…). **Os consumidores do `/mcp` usam UAs próprios**, e por isso **ficaram todos de fora da minha conta**. **M23 continua válida para o que ela mede — a preferência de formato entre bots de IA nomeados —, mas não mede a superfície de protocolo.** Corrigido aqui.

### ⚠ E aqui a ressalva que impede inflar o achado — quem chama NÃO é quem eu esperava

| User-Agent | Req. | O que é |
|---|---|---|
| `SentinelOracle/0.1` | 3.863 | monitor |
| **`mcpbeat/0.1 (+…/bot/; liveness check)`** | 2.545 | **liveness check — declara isso no próprio UA** |
| `node` | 1.729 | genérico |
| `zevruna-monitor/1.0` | 1.296 | monitor |
| `python-httpx/0.28.1` | 1.240 | genérico |
| `Go-http-client/2.0` | 901 | genérico |
| `agent-tools.cloud-crawler/0.1` | 309 | crawler de descoberta |
| `AgentReadinessScanner/1.0` | 187 | scanner |
| **`wikijuridica-agent-surface-probe/1.0`** | 173 | **nosso** |

**O veredito honesto tem duas metades, e as duas importam:**

1. **✅ É verdade que existe tráfego recorrente e sustentado ao `/mcp`** — ~1.500/dia, **488 IPs**, **sem tendência de queda em 10 dias**. **Isto é literalmente o "vir e voltar" que o dono cobra, e está acontecendo.** É a única superfície do portal com esse comportamento.

2. **⚠ Mas o consumo é majoritariamente de MONITORAMENTO E SCANNER, não de agente resolvendo problema jurídico.** `mcpbeat` se declara *liveness check*; `SentinelOracle`, `zevruna-monitor` e `AgentReadinessScanner` são monitores. **Chamar esses 15 mil de "agentes usando o portal" seria inflar exatamente como o dono proibiu.**

### O que É acionável, e é bastante

- **O portal rejeita ~8% das requisições ao próprio serviço: 1.115 × 405 e 163 × 404.** Há **1.031 GETs** a `/mcp` — e o MCP sobre HTTP responde a POST, então **cada GET vira 405**. **Um cliente que sonda com GET conclui "não existe" e vai embora.** Um `GET /mcp` que devolva o *server card* em vez de 405 converte 1.031 rejeições em 1.031 descobertas.
- **Os 163 × 404 são pedidos de metadados** — casa com O14/T3.5 (`/mcp/.well-known/oauth-protected-resource`, RFC 9728).
- **Há um ecossistema de diretórios e monitores de MCP que já conhece este servidor.** É o público que leva ao registro (T3.7) — **e que hoje recebe 405 e 404**.
- **O outro achado da mesma frente, que confirmei antes:** o **maior leitor do sitemap é o `Cloudflare-AI-Search` (951) contra o Googlebot (114)** — **e ele honra GET condicional (70 vezes)**. **O consumidor mais assíduo do portal é um agente de IA que já revalida direito — e o `lastmod` que ele lê está parado há 20 dias.**

---

> ## ⚠ O36 a O39 são PRÉ-FABLE — não fechar nada com base neles ainda
>
> As frentes das ondas 6 e 7 concluíram, **mas os dois críticos Fable ainda estão rodando**. Pelo funil que esta sessão fixou — *crítica Fable → cruzamento com medição própria → só então vira tarefa* —, **tudo em O36-O39 é ALEGAÇÃO até a refutação passar**. Os Fables anteriores derrubaram, em média, de 2 a 4 achados por onda, incluindo **uma corroboração circular minha** e **dois números que eu havia integrado**. **Estas quatro seções entram no plano por ordem do dono (nenhum dado se perde), com o selo de que ainda não passaram pelo crivo.**
>
> **Já há sinal de que serão derrubadas em parte:** a onda 7 mediu **62 commits** de defasagem do binário onde a onda 2 mediu 18, e **1,51 GB/dia** de aquecimento onde a onda 3 mediu 474 MB/dia. **Duas frentes, dois números, e eu não sei qual está certo até alguém reconciliar.**

## O36 — Fontes: o que temos, o que está quebrado e o que fecha o gap de frescor

### O36.a — O teto real de frescor: **~10 a 15 itens/dia, e ZERO em legislação**

O portal coleta **5 fontes em 8 hosts, e todas respondem**. Entrada real de conteúdo **novo**: **~10,7 itens/dia** (STJ 1,7 + notícias 8,2 + STF 0,8 + **normas 0,0**) — enquanto a onda registra *"323 páginas geradas"*, número que **é remontagem do mesmo acervo**.

> **Nenhuma fonte mudou de layout, nenhuma passou a exigir credencial, nenhuma bloqueou o projeto — o defeito é todo de engenharia própria.**

**Defeitos por fonte, medidos:**
- **[ALTA] Querido Diário (o canal de maior volume, 485 edições/lote) está sistematicamente fora de fase:** a janela de coleta (`scraped_since` = ontem 00:00, às 04:2x) **é mais curta que o lag de indexação da própria fonte, medido em ~24 h**. **É a causa real das 4 ondas sem diários** — não é a fonte que caiu.
- **[ALTA] Coleta que devolve ZERO linhas com exit 0 é registrada como sucesso** — a onda é cega para a falha mais provável.
- **[MÉDIA] `normas-federais` baixa 12,9 MB por dia para produzir ZERO registro novo**, e o sitemap da fonte **não suporta GET condicional**. **Pior custo/benefício do repositório.**
- **[ALTA] `normas.leg.br` não está "atrasado 8 dias" como diz o comentário do coletor: está CONGELADO em 2026-08-12** e não avançou um único dia em seis execuções. *(Mais um comentário que mente.)*
- **[MÉDIA] `collect-stj-precedentes` regrava o dump completo todo dia:** 14 MB em 6 dias para **10 registros novos**.
- **[BAIXA] O feed do CJF está congelado desde 20/08** e o coletor recolhe as mesmas 30 notícias todo dia sem notar.
- **[MÉDIA] Dos seis TRFs, só o TRF6 serve o feed que o coletor assume** — o padrão de host é **hardcoded** e **falha em silêncio nos outros cinco**.
- **[MÉDIA] O log de cada coletor vai para `/tmp` e é sobrescrito a cada onda** — **a causa das falhas de 22, 24 e 25/08 foi destruída**. *(Viola a regra do dono de que produto não mora em `/tmp`.)*
- **[MÉDIA] 21 arquivos e 16 MB de matéria-prima em untracked há até 124 h** — e **o gate que os apanha existe e não está na onda**.
- **[MÉDIA] O certificado folha do STF expira em 2026-10-05 — 40 dias** — e o canal depende de um intermediário fixado no repo.
- **[INFORMATIVO] Armadilha registrada: o canal alternativo do LexML (SRU) está atrás do WAF do Senado e devolve HTTP 200 com página de verificação.** *Armadilha para qualquer coletor que confie no status.*

**Conformidade de coleta (DEC-032), e aqui há falha real:**
- **[ALTA] `internal/sourcecollect` promete "ledger de cada requisição" no próprio cabeçalho e não escreve nenhum** — **a DEC-032 não tem trilha de auditoria**.
- **[ALTA] `collect-noticias-oficiais` não consulta o `robots.txt` de nenhum dos quatro hosts** — **viola o primeiro degrau da DEC-032**.
- **[BAIXA] `TetoDiario` é por PROCESSO, não por dia** — *"o comentário e o nome mentem sobre a garantia"*.
- **[BAIXA] `robotsPermite` testa o grupo pelo UA padrão, não pelo UA que a requisição vai enviar.**
- **[MÉDIA] `content/source_registry.json` descreve outro portal:** **54 das 58 fontes estão desligadas, e 3 dos 8 hosts coletados todo dia nem constam**.
- **[INFORMATIVO] ✅ O que está CERTO e deve ser preservado:** exceção de UA do STF, **GET condicional do STJ e do STF**, e o parser de data PT-BR do feed do STJ.

### O36.b — **Dois canais abertos, sem credencial, verificados hoje, que fecham o gap**

> **A resposta à sua pergunta sobre criar API ou instalar OSS: não precisa de nenhum dos dois para o gap principal.**

| Canal | O que entrega | Licença | Verificado |
|---|---|---|---|
| **Diário da Justiça do STJ, no CKAN** | **3.968 decisões em 24/08**, 3.334 em 21/08 · **íntegras em `.txt` UTF-8** · D+1 | **CC-BY** | por sonda própria, 2026-08-26 |
| **Lista de legislação do Senado (dados abertos)** | legislação federal até **D-2**, **~12,5 normas/dia útil** — contra as **0** de hoje | aberta | idem |

**⚠ E o agente declarou uma falha do próprio método, que vira requisito:** *"O robots do `dadosabertos.web.stj.jus.br` **PROÍBE `/api/`** — e foi por `/api/` que eu medi. **O coletor de produção não pode repetir isso.**"* **A fonte é boa; o caminho de acesso tem de respeitar o robots** (primeiro degrau da DEC-032).

**Sobre OSS — e a resposta é "construir aqui", com razão medida:**
- **[INFORMATIVO] A categoria "extrator OSS de PDF de diário oficial" NÃO SE APLICA:** as íntegras do STJ **são `.txt` UTF-8**. *Instalar um extrator de PDF resolveria um problema que este portal não tem.*
- **[INFORMATIVO] A taxonomia que permite classificar decisão por área do direito SEM hardcode existe e é pública: o SGT do CNJ.** **É a peça que substitui literal por dado** (R13).
- **[INFORMATIVO] ✅ Três canais brasileiros relevantes exigem credencial ou estão inalcançáveis — e nenhum deles virou tarefa do dono.** *(Regra respeitada.)*

**[ALTA] E o hardcode que impede tudo isso de ser barato:** **nenhum dos cinco coletores diários lê `content/source_registry.json`** — **as 12 URLs de fonte são literais dentro do Go**, e **fonte nova exige build**. **É por isso que "adicionar uma fonte" parece caro quando deveria ser uma linha de config.**

**O que falta, em uma frase da própria frente:** *"O gap não se fecha com SaaS nem com OSS novo… o que falta é engenharia própria e barata: tirar as 12 URLs literais de dentro do Go e pô-las no registry, escrever ~200 linhas sobre o `internal/sourcecollect` que já existe, e publicar uma superfície de delta diário derivada do `published_manifest`."*

---

## O37 — Notificação: sete canais implementados, **nenhum entregando**

> **Causa comum dos três achados críticos, e é de arquitetura:** *"o SINAL está acoplado ao DESFECHO de um pipeline de produção, e o RECIBO de protocolo (204 do hub, 200 do buscador) vem sendo tratado como prova de ENTREGA, num ledger que fica verde sem que ninguém tenha vindo ler."*

- **[CRÍTICO] WebSub é push para ninguém:** **16 pings aceitos, ZERO buscas do hub ao feed em 14 dias.**
- **[CRÍTICO] IndexNow operava por DESPEJO:** **43.438 submissões de URL para ~10 mil URLs em 6 dias — o acervo inteiro duas vezes num único dia**. *"Exatamente o padrão que a FAQ desaconselha"*, **e já rendeu 403 a este domínio**.
- **[CRÍTICO] O sinal é a etapa 9/9 de um script que morre na 3/9 ou 5/9** — há 6 dias, com **2.094 páginas geradas e nenhuma publicada nem anunciada**.
- **[ALTO] Dois escritores, um estado:** a submissão completa de 19/08 **não atualizou o estado incremental**, que segue afirmando que 9.601 URLs jamais foram enviadas.
- **[ALTO] `feed.xml` e `llms.txt` saem com `s-maxage=604800`** — **sete dias de congelamento na borda para os dois artefatos cuja única função é anunciar mudança**.
- **[MÉDIO] Os ledgers medem o POST, nunca a entrega** — nenhum canal tem campo de verificação posterior.
- **[BAIXO] O ping WebSub baixa 511 KB do feed a cada 30 min só para calcular um hash** — enquanto **o feed já serve ETag e Last-Modified**.
- **[BAIXO] Custo do frescor diário: ~349 URLs/dia** — **uma ordem de grandeza abaixo de qualquer limite declarado**. **O gargalo não é cota; é a onda travada.**

### ⚠ Duas refutações que o próprio agente fez, e que evitariam dano

1. *"Eu ia afirmar que 9.601 URLs jamais foram anunciadas — o ledger de lotes mostrou o acervo completo submetido em 19/08, **e a correção que eu proporia (drenar 10 lotes) seria o reenvio em massa que já rendeu 403 a este domínio**."*
2. *"Eu ia atribuir ao IndexNow um retorno de bot de 50% contra 0% — **o teste do confundidor mostrou que a coorte anunciada é 83,2% rota de hub e 68,3% presente no feed, contra 5,5% no controle**, ou seja **correlação de seleção**."*

**Ambas são exatamente o tipo de erro que o dono mandou não deixar passar — e foram apanhadas pelo próprio autor, antes de virarem tarefa.**

### Arquitetura proposta para "a cada instante"

**Barramento de eventos local em JSONL append-only**, emitido **dentro da transação de publicação**, disparado por **`systemd.path` sobre o delta de estado — não pelo exit code da onda** · **cursor por destino que só avança contra recibo** · **idempotência por `content_sha256`** · **verificação de entrega cruzada contra o log do nginx**. **Sem fila externa** (o volume medido de 349 eventos/dia não justifica) e **sem SaaS**.

---

## M28 — Separar o self-warming do bot legítimo: a verificação que o dono exigiu

> **Ordem do dono:** *"Tem que tomar cuidado, pois o servidor faz self-warming, e você pode achar que são milhares de requisições de bots legítimos… pois na Cloudflare eu vejo o meu próprio servidor."*

**Ele está certo, e esta sessão já tropeçou nisso três vezes** (96% das requisições ao sitemap eram watchdog; `organic_requests` inflado 16-32%; duas "evidências de forjamento" que eram sondas da casa). **Fui verificar as duas medições deste plano que poderiam estar contaminadas.**

### Verificação 1 — a série de bots (`serie_saneada`) está LIMPA

Listei as **31 chaves** que a série carrega no histórico inteiro e conferi as amostras de User-Agent:

```
adsbot-google · ahrefsbot · amazonbot · amzn-searchbot · applebot · bingbot · bytespider · ccbot ·
chatgpt-user · chrome-lighthouse · claude-searchbot · claude-user · claudebot ·
cloudflare-agentreadiness · dataforseo · duckassistbot · duckduckbot · facebookexternalhit ·
google-extended · google-inspectiontool · googlebot · googlebot-image · googleother · gptbot ·
meta-externalagent · mj12bot · oai-searchbot · perplexity-user · perplexitybot · semrushbot · yandexbot
```

**Chaves que seriam nossas: NENHUMA.** O aquecimento (`wikijuridica-cache-warm`), o watchdog e as sondas **não entram na série de bots** — são contados à parte, em `edge_traffic_daily`, onde aparecem como `self_warming_requests`. **Os ~5.448 req/dia de bot verificado não incluem tráfego próprio.**

**⚠ Mas há uma ressalva que muda como esses números devem ser lidos:** vários agentes estão marcados **`unverified_at_edge`** — `chatgpt-user`, `claude-searchbot`, `duckduckbot`, `googleother`, `bytespider`, `amzn-searchbot`, `google-extended`, `duckassistbot`, `perplexity-user`. **Esses são declarados por User-Agent e NÃO verificados pela Cloudflare** — ou seja, **podem ser falsificação**, exatamente como M11 mediu. **Ao ler a série, `cloudflare_verified_bot_category` é dado; `unverified_at_edge` é alegação.**

### Verificação 2 — o achado do `/mcp` sobrevive à separação

Refiz a contagem de M27 **excluindo tudo que é nosso** (UA `wikijuridica-*`, `wiki-onda*`, `wiki-audit*`, `curl-teste`, `ratelimit-probe`; IP `127.*` e a `/64` da casa; e `warm=true`):

| | Requisições | IPs distintos |
|---|---|---|
| **EXTERNO** | **14.063** | **483** |
| INTERNO (nosso) | 1.099 | 5 |
| **externo real** | **92,8%** | |

**O achado do `/mcp` sobrevive:** ~1.400 requisições externas por dia, de 483 IPs distintos. **A ressalva de M27 continua valendo — a maioria é monitor e scanner, não agente que cita — mas não é tráfego próprio disfarçado.**

### A disciplina que fica, e vale para toda leitura futura

| Instrumento | Inclui tráfego próprio? | Como separar |
|---|---|---|
| `serie_saneada` (bots) | **não** | já separado por `agent_key` |
| `edge_traffic_daily` | **sim** | campo `self_warming_requests` — **mas subconta**: ignora 1.887 req/dia de sondas (O32.d) |
| log do nginx | **sim, e é 86,5% dele** | campo `warm=$http_x_warming_request` + UA `wikijuridica-*` + `/64` da casa |
| `organic_requests` | **sim, inflado 16-32%** | **não use como linha de base até T0.8** |
| Painel da Cloudflare | **sim** | é onde o dono vê o próprio servidor — **`verifiedBotCategory` é o filtro certo** |

**Regra fixada:** *nenhum número de tráfego neste plano vale sem dizer se o self-warming foi excluído e como.* Onde a exclusão não foi feita, está escrito.

---

## O38 — Qualidade do conteúdo automático: **a camada AUTORAL é que é molde**

> **Todas as 308 páginas foram medidas — não amostradas.** E o veredito inverte o que a DEC-032 temia:
> *"O problema NÃO é excesso de citação (a proporção citada é sadia, 20-25%): é que a **camada AUTORAL é molde**. A página derivada é hoje **um espelho com decoração** — o único texto único é a citação oficial, **exatamente a forma que a DEC-032 declarou proibida**."*

**Medição no HTML servido:** **65,6% a 75,6% dos 8-gramas de cada canal se repetem entre páginas do mesmo canal**, com **bloco literal de 104 a 208 palavras presente em mais da metade das páginas**.

### 🔴 Três defeitos de risco jurídico real

1. **80 páginas intituladas "O que diz a Súmula N do STJ" citam a `tese_firmada` de uma linha `tipo=Tema` — não o enunciado da súmula.** E a frente **confirmou na fonte primária**: **o portal de dados abertos do STJ não tem dataset de súmulas**, então **nenhum canal do pipeline jamais coletou o enunciado**. **O portal afirma publicar o texto de uma súmula que nunca teve.**
2. **100 das 284 páginas STJ/STF têm o `anchor_claim` — o campo que existe para PROVAR a citação — cortado em ~297 caracteres terminando em reticências.** **O instrumento de verificabilidade está truncado.**
3. **29 páginas apresentam uma SÚMULA sob o cabeçalho "O dispositivo legal em discussão" / "A base legal invocada".** **Súmula não é dispositivo legal** — é **misatribuição de citação**, *a única classe de defeito que o `CLAUDE.md` nomeia como risco OAB real e P1 permanente*.

### Demais achados

- **[CRÍTICO] 50 páginas `/jurisprudencia/stf-*/` estão NO AR sem linha em NENHUM shard v2** — órfãs, produto do `os.WriteFile`. **O HTML público é hoje a ÚNICA cópia.** *(Amplia T0.6: não é uma órfã, são 51.)*
- **[CRÍTICO] Base legal por fonte não é registrada em nenhuma página:** o coletor grava `base_legal` e `licenca`, **e o gerador descarta os dois**.
- **[CRÍTICO] Canal de notícias: 20,5% das palavras visíveis são o título literal do tribunal** — e **0 de 20** registram a base legal. *(Ressalva: o título é o que a DEC-032 permite; o volume é que pesa.)*
- **[CRÍTICO] ZERO de OITO gates declarados pela DEC-032 e pelo PLANO existem em `internal/checks`.**
- **[CRÍTICO] O projeto do gate `check-derived-authorial-floor` tem o critério certo, e é contraintuitivo:** **PALAVRA AUTORAL ÚNICA, não palavra** — *"porque um piso de palavras aprova 100% das páginas-molde"*.
- **[MÉDIO] 63 pares tema↔súmula publicados citam o texto oficial IDÊNTICO**, com o mesmo `anchor_claim` e a mesma URL — **duas URLs indexáveis da mesma coisa**.
- **[MÉDIO] 284 das 323 páginas derivadas não têm `publication_date`** — num canal cuja razão de existir é frescor diário.
- **[MÉDIO] Canal de diários: 3,66 MB de texto já ANONIMIZADO estão coletados e a página não usa um caractere** — lista número de edição.
- **[MÉDIO] `word_count` declarado omite o FAQ em 280 de 280 páginas STJ** — `conta()` diverge da fórmula canônica.
- **[MÉDIO] O piso é 270 palavras hardcoded, igual nos cinco geradores**, contra os pisos de 350 a 1.000 que o PLANO declara por tipo.
- **[MÉDIO] ISO date e sigla interna no texto visível:** 261 HTMLs com `"2009-12-02"` em prosa e 80 com `"órgão CE/S1/S2/S3 do STJ"`.
- **[BAIXO] Matéria-prima paga e não convertida:** 59 julgados do STF viraram 4 páginas · 51 de 217 notícias nunca usadas · 604 edições de diário.

### ✅ Dois achados negativos, medidos e reportados com honestidade

- **ZERO violação de ética OAB e ZERO CTA comercial nos 5 canais derivados** — as 12 ocorrências que a varredura acusou eram **12 falsos positivos**; lane correta em **323/323**.
- **A divulgação de situação não-corrente do precedente FUNCIONA** — 0 páginas omitem "Revisado"/"Afetado". *"Minha primeira medição acusou 13 e era falso positivo meu, corrigido."*

> **E o alerta que decide a ordem:** *"Publicar diariamente sobre esta base multiplicaria o molde e a misatribuição em ~13-20 páginas/dia."* **Isto amarra a Fase 6 à Fase 5: destravar a fábrica ANTES de corrigir o molde seria industrializar o defeito.**

---

## O39 — Observabilidade: **o canal de alerta é write-only**, e cinco números do meu briefing estavam errados

### 🔴 A cadeia causal que explica por que nada disso foi visto

> **183 alertas críticos/altos com `resolvido: false` e ZERO leitores no repositório inteiro — nenhum check lê `owner_alerts.jsonl`.**

E daí decorre tudo: ninguém viu que a onda falha **há 7 dias**, que a última aprovação do manifesto é de **20/08**, que **99,9% do aquecimento volta `dynamic`**, e que **757 requisições a `GET`/`HEAD` `/mcp` levaram 405 em 7 dias, de 111 clientes distintos — vários deles diretórios de MCP que voltaram TODOS os 7 dias e nunca receberam nada.**

**🔴 E a métrica que responde diretamente à sua ordem sobre retorno:** **54,8% dos 301 clientes distintos não-warm vieram UM ÚNICO DIA e não voltaram.**

### ⚠ Cinco divergências contra o meu briefing — o agente as nomeou, e elas valem

| Eu escrevi | Medição corrigida |
|---|---|
| binário **18 commits** atrás | ver reconciliação abaixo — **e o achado novo é pior que os dois números** |
| onda falhando há **6 dias** | **7 dias** |
| `considered_for_answer` em **84%** sem relação | **97,5%** |
| `requests_local_verification` é **zero estrutural** | **NÃO é zero estrutural** |
| aquecimento move **474 MB/dia** | **1,51 GB/dia** |

*O briefing mandava desconfiar quando divergisse. Divergiu, e a correção é do agente, não minha.*

### ⚠ Reconciliação do "18 × 62 commits" — feita por mim, e o achado real é outro

```
git log --since='2026-08-20 13:08' -- internal/ cmd/   →  18 commits
git log --since='2026-08-20 13:08'                     →  61 commits
```

**Os dois estão certos, medindo escopos diferentes:** **18** é o que tocou o **código do servidor** (o que importa para "o binário está velho"); **~61-62** é o total de commits no repositório. **Nenhuma das duas medições estava errada — faltava dizer o escopo.**

**E o achado NOVO, que é pior que qualquer um dos dois números:**

```
mod   portaljuridico  v0.0.0-20260820155603-39f13d3602d1+dirty
build vcs.revision=39f13d3602d13721911f0c7263d85b71b89695c4
build vcs.time=2026-08-20T15:56:03Z
build vcs.modified=true
```

> **`vcs.modified=true` e o sufixo `+dirty`: o binário em produção NÃO CORRESPONDE A NENHUM COMMIT.** Foi construído com a worktree suja, sobre `39f13d3602d1` **mais alterações não commitadas que ninguém sabe quais são**. **Não é só que ele está desatualizado — é que não há como saber exatamente o que ele contém.**
>
> **Isso eleva T0.1 e T0.3:** o rebuild não é "atualizar"; é **restabelecer correspondência entre o que roda e o que está versionado**. E o gate `check-binario-vs-fonte` precisa reprovar **`vcs.modified=true`**, não só commit posterior.

### Demais achados

- **[ALTA] 🔴 O próprio `/auth.md` envenena a cadeia de descoberta OAuth:** **quatro URLs escritas dentro de crase** geram **138 respostas 404 com `%60` em 7 dias**. **O portal publica um documento que ensina o agente a pedir a URL errada.** *(Confirma M19 pela origem: a pontuação residual não vem só do parser do bot — vem do nosso texto.)*
- **[ALTA] Demanda real de descoberta chegando e recebendo 404:** `agent.json`, `mcp`, `mcp.json`, `server-cards.json`, `glama.json`, `owners.json`.
- **[ALTA] Há forjador ATIVO usando os UAs de GPTBot, PerplexityBot, ClaudeBot, OAI-SearchBot e ChatGPT-User** — e **a identidade não é verificada na leitura do log**. *(Confirma M11 e M26 por terceiro instrumento.)*
- **[ALTA] Cinco `check-*` não têm nenhum caminho de saída diferente de zero — e dois deles, que guardam COLISÃO DE ROTA PÚBLICA, não têm NENHUM `exit` ou `return`.** **Gates que não podem reprovar.**
- **[ALTA] A telemetria vê 128 UAs de agente, governa 32, e descarta método e rota** — *"por isso nenhum dos achados 4, 6 e 7 apareceu em série nenhuma"*.
- **[MÉDIA] O ruído afoga o sinal por construção:** 61% do ledger é uma condição crônica, **`repeticoes` é escrito e nunca lido**, e o cooldown silencia.
- **[MÉDIA] Os ledgers de ops não têm verificação de integridade** — **linha corrompida com bytes NUL**, e arquivo com duas linhas para a mesma data.
- **[MÉDIA] O aquecimento é 78,4% do tráfego de origem e move ~3 GB/dia por um rádio 2.4 GHz half-duplex** — **desperdício medido, mas NÃO é a causa de degradação**. *(Rebaixa minha leitura de O24/S-3.)*
- **[MÉDIA] Endpoint público de saúde do PROJETO** — derivado só de ledger que já existe. **É o que hoje nem agente nem humano têm como perguntar.**
- **[ALTA] Painel mínimo de "vivo": nove métricas, de que dado cada uma sai, quanto vale hoje e qual o alvo derivado de baseline medido.** → alimenta T7.1.

---

## 🔧 O QUE FALTA E SE CONSTRÓI OU INSTALA — nesta sessão

> **Ordem do dono:** *"Se tiver que colocar para instalar tokenizador no projeto, deve instalar se for open source e se for para ajudar o projeto com visitas de bots… Se achar na execução problemas pendentes, também é para corrigir e implementar; se faltar, criar; se faltar dependências, integrar; se faltar open source para ajudar com mais coisas no projeto e engenharia e que facilita trabalho, deve integrar."*

### O que o projeto JÁ tem — medido, para não instalar o que existe

**202 dependências no `go.mod`**, e o arsenal de texto já é grande:

| Já instalado | Para quê serve aqui |
|---|---|
| `clipperhouse/uax29/v2` · `rivo/uniseg` | **segmentação Unicode de palavra e sentença** — a base correta de qualquer contagem em PT-BR |
| `mfonda/simhash` · `hbollon/go-edlib` · `adrg/strutil` | similaridade e distância — **a base do gate `derived-authorial-floor`** |
| `blevesearch/bleve/v2` · `blugelabs/bluge` · `snowballstem` | índice e stemming |
| `coregx/ahocorasick` | varredura multi-padrão (molde, frases repetidas) |
| `pemistahl/lingua-go` | detecção de idioma |
| `temoto/robotstxt` · `jimsmart/grobotstxt` | **dois parsers de robots** — o que permite o teste diferencial de T4.1 |
| `mmcdole/gofeed` · `aafeher/go-sitemap-parser` | feed e sitemap |
| `cespare/xxhash` · `bits-and-blooms/bloom` | hash rápido e dedup |

**Regra que sai daí:** **antes de instalar qualquer coisa, procurar no `go.mod`.** Metade do que este plano precisa **já está pago**. `internal/legalminhash` e `internal/v2bodyneardup`, que o gate de molde deve reusar, são construídos sobre esses pacotes.

### 🔢 Tokenizador — instalar, e por quê

**Medido agora: nenhum tokenizador está disponível.** `tiktoken`, `transformers` e `tokenizers` → **os três dão `ModuleNotFoundError`**.

**Consequência que atravessa o plano inteiro:** **todo número de token deste documento — inclusive M15.a, que sustenta o argumento do custo para o bot — é estimativa por bytes ÷ 4.** Os bytes são medidos; **a razão é chutada**. Para PT-BR acentuado, essa razão é notoriamente pior que para inglês, e o plano **não sabe por quanto**.

**Por que isso ajuda "com visitas de bots", que é o critério do dono:** o argumento central do plano — *o Markdown é 4,8× mais barato e por isso 86,5% dos bots de IA o preferem* — **hoje é medido em bytes**. Com tokenizador real, o portal passa a **medir o que o agente de fato paga**, pode **declarar o custo em tokens nos próprios artefatos de agente** (`llms.txt`, front matter, resposta do MCP), e pode **dimensionar o `llms-full.txt` de 1,4 MB pelo que ele realmente ocupa numa janela de contexto** — hoje estimado em ~360 mil tokens **sem instrumento**.

**Candidatos open source, a decidir por ADR na execução:**

| Candidato | Licença | Nota |
|---|---|---|
| `github.com/pkoukk/tiktoken-go` | MIT | BPE compatível com os encodings da OpenAI, **em Go** — casa com o resto do projeto, sem Python no caminho de runtime |
| `github.com/tiktoken-go/tokenizer` | MIT | mesma família, sem download de vocabulário em runtime |
| `tiktoken` (Python) | MIT | só se a contagem ficar restrita a ferramenta de medição, **nunca no caminho de resposta** |

**Como entra, pelo contrato do projeto:** **ADR + licença revisada + versão fixada + benchmark**, porque toca contagem que vira número publicado. **E o benchmark é específico:** medir a razão bytes/token **no corpus real em PT-BR**, não em amostra sintética — **é justamente essa razão que o plano hoje chuta.**

**E o critério de parada, para não virar obra:** se o tokenizador entrar no caminho de **resposta HTTP**, sai. Ele serve para **medir e declarar**, não para gerar.

### Outras faltas que a execução cria ou instala — todas com o mesmo crivo

| Falta medida | Resposta |
|---|---|
| **Validador de dados estruturados** — nenhum foi executado; o plano não sabe se o JSON-LD passaria no Rich Results | **construir aqui** sobre `santhosh-tekuri/jsonschema` (já instalado) + o vocabulário schema.org; **não é SaaS**, e o Rich Results Test é de terceiro |
| **Gate `derived-authorial-floor`** | **construir**, reusando `legalminhash` + `v2bodyneardup`, com **cálculo exato confirmando antes de reprovar** |
| **Ledger de coleta da DEC-032** | **construir** — o schema já está desenhado (O42) |
| **`/changes.json` e `/api/v1/novidades`** | **construir** — desenhos completos em O42, derivados de dado que já existe |
| **Fila durável para notificação** | **não instalar.** O volume medido é **349 eventos/dia** — JSONL append-only + `systemd.path` basta. *"Sem fila externa, que o volume não justifica."* |
| **Extrator de PDF de diário oficial** | **não instalar.** As íntegras do STJ **são `.txt` UTF-8** — resolveria um problema que o portal não tem |
| **Taxonomia de área do direito** | **integrar o SGT do CNJ** (34.603 + 7.601 entradas, público) — **é o que substitui o hardcode de área por dado** |
| **Verificador Web Bot Auth (RFC 9421)** | **avaliar `cloudflare/web-bot-auth`** (open source) contra construir; **decide o benchmark**, porque entra no caminho de requisição |
| **Faixas de IP** | **já existem 11 arquivos** — falta `openai-adsbot.json` e corrigir as três URLs do Google |

### 📦 As 202 dependências: o que já medi, e a onda 8 que está apurando

> **Ordem do dono:** *"Se no repo tem 202 dependências, elas podem estar com bugs, e deve corrigir ou integrar."* E depois: *"Se tiver redundâncias ou bugs, corrigir os bugs das dependências e pode colocar em backup os que não são necessários, e instalar os necessários. E integrar algum código Go que possa ajudar."*

**O que medi por conta própria, antes de lançar a onda:**

| Medição | Valor |
|---|---|
| Dependências **diretas** | **66** |
| Dependências **indiretas** | **128** |
| **Diretas órfãs** (sem nenhum import no código) | **ZERO** — todas as 66 são usadas |

**Redundância medida, por número de arquivos `.go` de produção que importam cada uma:**

| Família | Membros | Arquivos de produção |
|---|---|---|
| **Motores/clientes de busca** | `bleve` · `bluge` · `meilisearch` · `opensearch` · `typesense` | 8 · 4 · 4 · 4 · 4 |
| **Bancos KV / cache** | `pebble` · `badger` · `ristretto` · `golang-lru` | 24 · 5 · 3 · 2 |
| **Codecs JSON** | `json-iterator` · `simdjson-go` · `segmentio/encoding` · `goccy/go-json` | 4 · 2 · 4 · 4 |

**⚠ E aqui um falso positivo grave que eu quase registrei — medi e ele caiu:**

`meilisearch`, `opensearch` e `typesense` são **clientes de serviço externo**, o que pareceria violar o contrato self-hosted first. **Fui verificar:**

```
ss -ltnp | grep -E '7700|9200|8108|9300'  → nada
systemctl list-units --state=running | grep -iE 'meili|opensearch|typesense'  → nada
importados em: internal/ossinstallmatrix · ossscaleintegration ·
               searchbackendbench · searchsidecarclients
```

**Nenhum serviço roda, e os três só aparecem em pacotes de BENCHMARK e de matriz de instalação de OSS.** **Não é dependência de produção nem violação de contrato** — é comparação deliberada. *(A onda 8 confirma lendo o código; registro aqui para que ninguém "corrija" o que não é defeito.)*

**O que a onda 8 (`wf_26127f48-c67`) está apurando, em 5 frentes + Fable:** versão fixada × versão atual × **repositório arquivado** · **licença lida no arquivo LICENSE, não presumida pelo nome** · **CVE consultada em `vuln.go.dev` para a versão EXATA** · issues de crash nas deps que tocam **entrada externa** (parsers de robots, feed, sitemap, HTML, JSON, DNS — as que um bot ou fonte hostil alcança) · **workarounds de bug de dependência já pagos e escritos no código** · a divergência real entre os **4 codecs JSON** (que serializam o JSON-LD, o `openapi.json` e o `agent-card` — **divergência ali é defeito público**) · `go.sum`, `replace`, `vendor/`, `GOFLAGS` · deps de mantenedor único · **o que a stdlib já faz bem** · e as integrações a instalar.

**A regra do dono para o que sobrar:** **o desnecessário vai para BACKUP, não para a lixeira** — mesma disciplina de "nunca descartar trabalho". **Remover dependência é mudança cara e irreversível na prática**, então: nada sai sem que os arquivos que a importam estejam medidos, e nada sai de caminho de produção.

### 💰 Dependência documentada e não usada é dinheiro parado — a medição que faltava

> **Ordem do dono:** *"As dependências não podem ficar somente documentadas, elas precisam ser usadas, senão é dinheiro jogado fora. Mas usadas para ajudar o projeto com base em engenharia de qualidade."*

**Ele apontou uma distinção que eu não tinha feito, e ela muda a leitura de "zero órfãs".** Ter `import` **não** é estar em uso: os três clientes de busca **têm import e não servem uma requisição sequer**. Refiz a medição separando **caminho de produção** de **pacote de benchmark/evidência**:

| Categoria | Quantas | Quais |
|---|---|---|
| **Em caminho de produção** | **61 de 66** | servem requisição, build, publicação ou coleta |
| **Só em benchmark/evidência** | **5** | `meilisearch-go` · `opensearch-go/v4` · `typesense-go/v3` · `fgprof` · `pprof` |

**A leitura honesta dos cinco, sem tratar todos igual:**

- **Os três clientes de busca** (`meilisearch`, `opensearch`, `typesense`) vivem em `searchbackendbench`, `searchsidecarclients`, `ossinstallmatrix` e `ossscaleintegration`. **São comparação deliberada de backend, e a busca real do portal não depende deles.** **Pergunta que a onda 8 tem de responder: o benchmark já respondeu o que ia responder?** Se sim, **o resultado vira ADR e os três vão para backup** — porque manter cliente de serviço externo no `go.mod` é superfície de CVE e de atualização por um benchmark encerrado. Se o benchmark ainda vai correr, **ele corre nesta sessão** e então decide.
- **`fgprof` e `pprof` são instrumentos de diagnóstico**, e o projeto tem um problema **medido** que eles resolvem: **TTFB de borda 111-123 ms**, hubs a 0,7-1,1 s, e uma cauda de 9,37 s que **não reproduziu**. **Eles não estão sobrando — estão ociosos.** **Usá-los é a correção**: perfilar a geração de Markdown em runtime e os hubs, que são as rotas mais lentas medidas.

**E o critério que fica, porque "usar" não pode virar desculpa para inventar uso:** **dependência se justifica por PROBLEMA MEDIDO que ela resolve, não por estar instalada.** Três exemplos concretos desta própria sessão, onde há dependência parada e problema medido esperando por ela:

| Dependência já paga | Problema medido que ela resolve |
|---|---|
| `mfonda/simhash` · `hbollon/go-edlib` · `adrg/strutil` | **65,6-75,6% dos 8-gramas repetidos** entre páginas do mesmo canal — é o gate `derived-authorial-floor` que não existe |
| `coregx/ahocorasick` | **bloco literal de 104-208 palavras** em mais da metade das páginas derivadas |
| `clipperhouse/uax29` · `rivo/uniseg` | **`word_count` diverge da fórmula canônica em 280 de 280 páginas** por contar errado |
| `temoto/robotstxt` **e** `jimsmart/grobotstxt` | **os dois parsers discordam sobre o mesmo robots.txt** — ter os dois é o que permite o teste diferencial de T4.1, e hoje ninguém o faz |
| `santhosh-tekuri/jsonschema` | **nenhum validador de dados estruturados foi executado** sobre os 10.071 nós `Article` |
| `fgprof` · `pprof` | **a cauda de latência de 9,37 s não reproduziu** e ninguém perfilou |

> **Isto é o inverso de instalar coisa nova: é COBRAR o que já foi pago.** Seis dependências ociosas resolvem seis defeitos medidos deste plano — e **nenhuma delas exige ADR, licença nova ou benchmark, porque já estão no `go.mod`.**

**A ordem de trabalho que sai daí:** **primeiro usar o que está parado** (custo zero de adoção, defeito medido esperando), **depois instalar o que falta** (tokenizador, verificação de assinatura), **por último decidir o que vai para backup** (os três clientes de busca, se o benchmark já respondeu).

### ⚠️ LOOPING DE GATE — a armadilha que já custou 6 dias, e a regra que sai dela

> **Ordem do dono:** *"Tomar cuidado com looping dos gates, pois eles também têm bugs e deixam as IAs em loopings desnecessários."*

**Ele está certo, e esta sessão tem o caso mais caro documentado:**

| Evidência medida | O que aconteceu |
|---|---|
| `check-v2-portfolio-pairing` exige o intent no commit **PAI**, e a onda o chama **antes** do commit que o satisfaz | **a fábrica parou 6 dias**, 6 de 6 execuções "parcial" |
| O `CLAUDE.md` registra **4 tentativas queimadas** contra esse mesmo gate | *"cada tentativa cega custa um pre-commit inteiro"* |
| **5 `check-*` não têm nenhum caminho de saída ≠ 0** — e **dois deles guardam colisão de rota pública** | gates que **não podem reprovar** |
| `check-edge-vary-contract` sai **verde** com zero regras vivas na zona | gate verde sobre mundo errado |
| O aquecedor sai com `failures: 0` **registrando `dynamic: 10383`** | ferramenta que mede o próprio fracasso e reporta sucesso |
| Gate de dados estruturados valida **360 registros de camada de ENSAIO** e nunca abre `public/` | cobertura zero, verde permanente |

**As cinco regras que passam a valer para todo gate nesta execução:**

1. **Gate que reprova DUAS vezes seguidas pela mesma causa é BUG DO GATE até prova em contrário.** Não se tenta uma terceira. Lê-se a implementação — o `CONTRATO_DADO_REAL` R2 já diz isso: *"gate vermelho não é veredito"*.
2. **Antes de rodar gate caro, rodar o barato que responde a mesma pergunta.** `./tools/check-v2-portfolio-pairing` é read-only e leva **menos de 1 s**; o pre-commit com build leva minutos. **O plano já registra isso e a execução tem de obedecer.**
3. **Gate que sai 0 relatando fracasso é defeito de primeira ordem** — pior que gate ausente, porque **produz confiança falsa**. Os 5 sem caminho de saída ≠ 0 entram na lista de correção.
4. **Nenhum gate novo antes de T1.4** (o canal de alerta consertado) — **são 12 gates propostos**, e gate sobre canal morto é papel.
5. **Teto de tentativas por gate: duas.** Na terceira, a tarefa muda de estado para `bloqueado`, o motivo vai para o frontboard, e **a investigação passa a ser do gate, não do código**. *É o que impede o loop que o dono descreveu.*

**E a razão pela qual isso é ainda mais sério com agentes:** um agente que recebe "gate vermelho" tende a **tentar de novo variando o input** — e cada tentativa custa tokens do dono sem produzir nada. **A regra do teto de duas tentativas é o que transforma um loop caro numa investigação barata.**

### E a regra que governa tudo isto

> **Falta ≠ bloqueio.** Se falta ferramenta, **constrói-se ou instala-se open source auto-hospedado**, com ADR, licença, versão fixada e benchmark quando afeta runtime. **Nunca SaaS, nunca cadastro, nunca serviço pago** (R-b do `CLAUDE.md`). E **nunca instalar antes de procurar no `go.mod`** — o projeto já tem 202 dependências, e este plano descobriu **duas vezes** que mandava criar o que já existia (as faixas de IP, e o arquivo de user-triggered fetchers do Google).

---

## ⚙️ GOVERNANÇA DA EXECUÇÃO — como esta operação se conduz

> **Ordem do dono, ao aprovar:** *"Antes do plano, você precisa salvar o plano na literalidade quando eu aprovar e commitar ele e criar tasklist para poder acompanhar e não perder a operação de engenharia por você e pelos agentes. E sempre consultar o advisor quando tomar decisões críticas. Sem Sonnet, sem Haiku. E usar Fable 5 para criticidade, adversarial, apontar erros, apontar falhas, melhorar a engenharia, nas questões mais críticas… Mas o Opus 5, que é o seu modelo, será o mais usado. Mas você precisa ver na execução o que usar, se vai precisar de workflow, de agentes especializados etc. Tudo com base em dados e para não perder contexto."*

### G1 — Os dois primeiros atos, antes de qualquer correção

1. **Salvar o plano NA LITERALIDADE** em `/opt/wiki/docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md` — **cópia fiel, sem resumir, sem cortar, sem "melhorar"**. Ele carrega as medições, as refutações, as autoacusações e os erros corrigidos; **cortar qualquer parte é perder o que custou tokens**.
2. **Commitar imediatamente**, com ponteiro em `docs/goal/CHECKPOINT_DIGEST.md` e registro em `docs/goal/MAESTRO_CODEX_LOG.md`. Junto, copiar para `data/ops/agent_reports/onda_bots_20260826/` os **`journal.jsonl` das OITO ondas** *(alinhado com T-1: eram "7" aqui e "8" lá — quem executasse este parágrafo ao pé da letra perderia uma onda inteira)* e o relatório avulso do agente de frescor. **Commit de conteúdo é leve — não builda Go.**

**Só depois disso começa a Fase 0.**

### G2 — Tasklist viva, para nada se perder

**Uma task por item do plano**, com estado rastreável — não uma lista de intenções, mas o instrumento de continuidade da operação:

| Campo | Para quê |
|---|---|
| `id` (T0.1, T1.1, …) | casa com o plano, sem tradução |
| `fase` e `depende_de` | a ordem é por dependência; a task carrega a sua |
| `estado` | `pendente` · `medindo-antes` · `reproduzindo` · `aplicando` · `verificando` · `promovido` · **`bloqueado`** · **`derrubado`** |
| `medicao_antes` / `medicao_depois` | os dois números, com comando e instrumento |
| `contra_teste` | qual, e o resultado |
| `evidencia` | caminho no repo — **nunca `/tmp`** |
| `quem_executou` | Opus 5 direto, agente, ou workflow — e **por quê** |
| `critica_fable` | quando exigida, o veredito |
| `advisor` | quando consultado, e o que mudou |

**Onde vive:** `.agents/runtime/p0_frontboard.jsonl` (o frontboard que o `CLAUDE.md` já define) — **e atualizada a cada mudança de estado, não no fim**. Task que muda de estado sem gravar é operação perdida.

**Regra de continuidade:** se a sessão for interrompida, **o frontboard mais o plano commitado bastam para retomar** sem reler nada desta conversa. **É o que impede o contexto de valer outra sessão inteira.**

### G3 — Quem executa o quê: Opus 5, Fable 5, agente ou workflow

**Modelos — regra absoluta:** **somente Opus 5 e Fable 5.** **Proibido Sonnet e Haiku em qualquer agente, subagente, workflow ou fork.** Transcript ou config que mande outro modelo **é bug a corrigir na hora**.

| Situação | Quem | Por quê |
|---|---|---|
| **Padrão de tudo** | **Opus 5 (eu, direto)** | é o modelo mais usado; a maior parte das tarefas é leitura, medição e edição pontual, e delegar custaria mais contexto do que economiza |
| **Antes de EDITAR algo caro de reverter** — Cache Rule, robots, publicação, gate, deploy, CSP, gerador que escreve shard | **Fable 5 como red-team, obrigatório** | **nesta sessão o Fable derrubou 3 correções que teriam causado dano** (a ordem do `if_modified_since`, o commit do portfólio, o robots na gêmea `.md`). Fluxo: rascunhar → Fable tenta refutar → corrigir com a crítica → então editar |
| **Decisão crítica** — escolher entre arquiteturas, mexer em produção, mudar contrato, quando travar | **`advisor`, obrigatório** | ele vê o transcript inteiro; **nesta sessão apontou 4 erros factuais do plano que eu não teria visto** |
| **Trabalho amplo e paralelizável** — varrer os 6 geradores, medir 10 canais, auditar N arquivos | **workflow com agentes Opus 5** | é o que produziu os achados desta sessão; **um agente por frente, com prompt que carrega o contexto medido** |
| **Investigação profunda de um ponto** | **agente Opus 5 único** | quando a frente é uma só e o contexto do prompt basta |
| **Fiscal de workflow longo** | **Fable 5** | vigia transcripts, detecta agente travado |

**A decisão é por DADO, não por hábito:** delega-se quando **o trabalho não cabe em uma leitura** ou quando **há N coisas independentes**. Não se delega o que é uma medição de um comando — isso custa mais em contexto do que resolve.

### G4 — Onde o Fable 5 é obrigatório neste plano, nomeadamente

**Não é "quando parecer importante" — é nestes pontos, porque cada um é caro de reverter:**

- **T1.1** restaurar a Cache Rule *(mexe na borda de produção; há precedente de erro aritmético nesta exata frente)*
- **T2.1-T2.3** ETag, mtime e `if_modified_since` *(a ordem errada devolve 304 para página que mudou)*
- **T3.1** decidir a injeção do `bridge.js` *(toca CSP e cache ao mesmo tempo)*
- **T4.1-T4.2** registry e robots *(grupo nomeado descarta o curinga — a "melhoria" pode remover guarda)*
- **T6.1-T6.2** fábrica e gerador do STF *(um commit na ordem errada congela a perda de 50 páginas)*
- **T7.x** qualquer canal de notificação *(uma URL não-canônica no canal errado mata o IndexNow inteiro)*
- **T5.4** publicar os `anchor_claim` *(toca texto publicado; 607 claims repetidos não podem virar corpo)*
- **T8.2** `og:image` em 10.299 páginas *(toca o `<head>` do acervo inteiro e acrescenta bytes ao HTML sob teto de 50 KB)*
- **T9.1** bump de `x/mod` + toolchain `go1.26.6` *(o próprio plano declara que o contra-teste é o BOOT — toca a verificação de módulo e obriga rebuild do binário de produção)*
- **T9.4** migrar `json-iterator` para `goccy` *(19 call sites em caminho de produção, dentro do binário público)*
- **Qualquer tarefa que edite gerador que escreve shard** *(a classe que já apagou 50 páginas)*

*(G4 nasceu antes das Fases 8 e 9 existirem. As três entradas acima entram pelo MESMO critério das demais — caro de reverter —, não por serem novas.)*

### G5 — Não perder contexto

- **Todo achado da execução vai para o plano commitado**, não para a conversa. **A conversa é volátil; o repo não.**
- **Todo número da execução entra com data, comando e instrumento** — quem retomar não precisa refazer.
- **Divergência entre o plano e a medição da execução:** **vale a medição**, e o plano é **corrigido no repo**, com o motivo. **Nunca defendido.**
- **Prompt de agente carrega o contexto medido**, não manda o agente descobrir de novo — foi o que fez as 7 ondas renderem.
- **As armadilhas A1-A5 vão no prompt de todo agente lançado.** Elas morderam 5 vezes nesta sessão, inclusive a mim.

---

## 🧪 PROTOCOLO DE VERIFICAÇÃO AO VIVO — nada neste plano se aplica sem ser testado antes

> **Ordem do dono, literal:** *"Não devemos confiar de primeira, sempre medir, testar, colher dados, poder abrir o projeto em outra porta para testar ao vivo, podendo reload o sistema e tudo que precisa, mas tudo com teste, ao vivo, em outra porta, **sem duplicar nada**. Tudo deve ser testado na execução, medido em tempo real, com evidência de engenharia."*

**Esta seção governa TODAS as fases abaixo.** Nenhuma tarefa é considerada feita por ter sido escrita, nem por o gate ficar verde — **só por medição ao vivo, antes e depois, com a evidência gravada no repo**.

### Por que isto não é formalidade: o placar desta própria sessão

| O que aconteceu | Quantas vezes |
|---|---|
| Premissa minha derrubada por medição | **9** |
| Número que eu integrei e estava errado | **5** (68×, 48 alertas, 15,8% de 304, mtime 05/08, 18×62 commits) |
| Comentário de código ou de commit que mentia | **8** |
| Gate verde sobre mundo errado | **5** |
| Agente que se corrigiu sozinho antes de eu integrar | **6** |
| Correção que teria causado dano se aplicada na ordem escrita | **3** |

> **Nenhum desses foi apanhado por gate. Todos foram apanhados por medição própria ou por crítica adversarial.** É por isso que o protocolo abaixo é obrigatório e não opcional.

### 🔴 A armadilha da "outra porta" — já destruiu produção neste projeto

**O dono pediu instância paralela para testar. Isso é o certo — e é exatamente onde o projeto já se feriu.**

**Precedente registrado (`[[instancia-auditoria-cachedir]]`):** uma segunda instância foi subida em porta diferente e **destruiu o índice de busca da produção** — a busca ficou **morta respondendo 200**, que é o pior modo de falha possível. **A causa: porta diferente NÃO isola disco.**

**Verifiquei o estado hoje, e a armadilha continua armada:**

```
cmd/server/main.go:47   cacheDir := "var/on-demand-cache"          ← default COMPARTILHADO
cmd/server/main.go:48   if env := os.Getenv("WIKI_CACHE_DIR")…     ← o isolamento existe
cmd/server/main.go:24   if env := os.Getenv("WIKI_HTTP_ADDR")…     ← a porta

var/on-demand-cache → 120 MB, intocado desde 2026-08-20 15:58
```

> **`WIKI_CACHE_DIR` é OBRIGATÓRIO em toda instância de teste.** Sem ele, a segunda instância escreve no mesmo cache da produção e corrompe o índice — **independentemente da porta**.
>
> **E "sem duplicar nada" está correto e não conflita com isso:** o isolamento de cache **não é duplicação — é o oposto**. Duplicar seria copiar `public/` ou o acervo; **isolar o cache é justamente o que impede a instância de teste de escrever por cima da de produção**. **A instância de teste lê os MESMOS `public/`, `content/` e `data/` — só o cache de escrita é dela.**

### O ambiente de verificação, definido

```bash
WIKI_HTTP_ADDR=127.0.0.1:8099 \
WIKI_CACHE_DIR=/opt/wiki/var/verify-cache \
  ./bin/wikijuridica-server.verify
```

| Regra | Por quê |
|---|---|
| **Porta 8099** (produção: Go 8089, nginx 8088) | não colide, e **8080/8081 são do projeto vizinho** — proibido tocar |
| **`WIKI_CACHE_DIR` próprio** | **obrigatório** — sem ele, corrompe a produção |
| **Binário próprio** (`.verify`), nunca sobrescrever `bin/wikijuridica-server` | trocar o binário de produção é deploy, não teste |
| **Lê `public/`, `content/`, `data/` de produção — sem copiar** | é o "sem duplicar nada": mesma fonte, escrita isolada |
| **Nunca escrever em `public/`, `data/editorial/`, `content/`** a partir da instância de teste | verificação é read-only sobre o produto |
| **Derrubar ao fim, e conferir que `var/on-demand-cache` não foi tocado** | `stat` antes e depois; mtime igual = isolamento funcionou |

**Para o nginx**, a mesma disciplina: `nginx -t -c <conf>` valida sem aplicar; a instância de teste sobe com `-p` próprio e porta própria; **e a paridade (`check-nginx-standalone-parity`) é conferida antes e depois de qualquer regeneração** (T0.4).

### O ciclo obrigatório por tarefa

Toda tarefa deste plano passa por **seis passos, nesta ordem**, e **nenhum é pulável**:

| # | Passo | Evidência que fica |
|---|---|---|
| **1** | **MEDIR ANTES** — o estado atual do que a tarefa promete mudar | número + comando que o produz, no ledger da tarefa |
| **2** | **REPRODUZIR O DEFEITO** na instância de teste — se não reproduz, **o defeito pode não existir mais** (o binário é `+dirty` e 18 commits atrás: parte do que sondei descreve o passado) | log da reprodução |
| **3** | **APLICAR** a correção | diff commitado |
| **4** | **MEDIR DEPOIS**, na instância de teste, **com o mesmo comando do passo 1** | comparação antes/depois |
| **5** | **VERIFICAR O QUE NÃO PODE QUEBRAR** — o contra-teste, específico por tarefa (tabela abaixo) | resultado do contra-teste |
| **6** | **PROMOVER** e **remedir em produção**, com `reload` quando bastar e `restart` quando o binário mudar | medição em produção, gravada em `data/ops/` |

**Se o passo 2 não reproduzir o defeito, a tarefa PARA e o achado volta para investigação.** Não se corrige o que não se viu quebrar.

### Contra-testes obrigatórios — o que cada correção pode quebrar

| Tarefa | O que medir DEPOIS que **não pode** ter mudado |
|---|---|
| **T1.1** Cache Rule | `/sitemap.xml` e os descritores **continuam com `max-age=300`** · a variante `Accept: text/markdown` **entra em HIT junto** · nenhuma rota de corpo variável (`/buscar/`, `/contato/`) passa a ser cacheada |
| **T2.1** ETag forte | o ETag muda **se e somente se** os bytes mudam · **`If-None-Match` continua respondendo 304** · a compressão não o enfraquece para `W/` |
| **T2.2** mtime | `<lastmod>` do sitemap **NÃO se move** (é outra semântica, O29) · `check-lastmod-por-evento` continua verde |
| **T2.3** `if_modified_since before` | **página que MUDOU responde 200** — este é o contra-teste que impede o desastre da ordem invertida |
| **T4.2** registry | **as guardas do curinga estão repetidas em cada grupo novo** (T4.1) · `check-robots-parser-real` e o parser real concordam · `/buscar/` continua bloqueado para quem já bloqueava |
| **T5.9** rótulos derivados | **nenhum rótulo visível mudou além dos 3 sem acento** · o fallback ASCII virou erro de gate |
| **T6.1/T6.2** fábrica | `check-shard-preservation` verde · **contagem de registros por shard só CRESCE** · nenhuma página publicada sai do manifesto |
| **T0.6** órfãs | **as 51 continuam servindo 200** (não se apaga página publicada) e passam a ter registro · as 3 `noindex` legítimas seguem fora |
| **T3.6** WebMCP | **hash da CSP recalculado e propagado às duas cópias do nginx** · a página **sem JS continua completa** (contrato de indexação) |
| **T7.x** notificação | **nenhuma URL não-canônica entra em canal de buscador** (R18) · o ledger prova o que foi enviado |
| **Qualquer** tarefa | **HTML ≤ 50 KB** · conteúdo completo no primeiro response · coerência `public/` ⊆ sitemap ⊆ `published_manifest` · `nginx -t` verde · métrica não conta tráfego próprio (M28) |

### Evidência de engenharia — o que fica gravado

Cada tarefa entrega, **no repo** (nunca em `/tmp`, R10):

1. **Comando reproduzível** que mede antes e depois — no ledger da tarefa.
2. **Os dois números**, com data, instrumento e **se o self-warming foi excluído** (M28).
3. **O contra-teste** da tabela acima, com resultado.
4. **Um segundo instrumento** quando o número sustentar decisão — ou a marca explícita *"instrumento único, não corroborado"* (R3).
5. **O que NÃO foi possível medir**, dito por extenso — como os agentes desta sessão fizeram.

### Medição em tempo real, durante a execução

- **Antes de cada fase:** rodar o painel de "vivo" (T7.1) e gravar a linha de base.
- **Durante:** acompanhar `/var/log/nginx/wikijuridica/access.log` **separando o warming** (campo `warm=`) — nunca a contagem crua.
- **Depois de cada promoção:** remedir na produção e comparar com o previsto. **Divergência entre previsto e medido para a tarefa, não vira nota de rodapé.**
- **Os ledgers cumulativos** (`edge_bot_agents_daily`, `crawl_coverage_daily`, `owner_alerts`) **só se leem por leitor canônico ou dedupe por chave** (A1, A5).

### E a regra que fecha tudo

> **Nada neste plano é verdade porque está escrito aqui.** Cada número traz data, instrumento e ressalva; **cada tarefa só existe depois de reproduzir o defeito ao vivo**; e **cada correção só está feita depois de medida na produção, com o contra-teste passando**. Onde a medição da execução contrariar o que este plano afirma, **vale a medição** — e o plano é corrigido, não defendido.

---

## O40 — Crítica Fable da onda 6: cinco derrubados, e o achado que salvou o plano

### 🔴 O que ninguém tinha visto — e que invalidava uma tarefa minha

**Já registrado em destaque no topo da Fase 6.** Em resumo: **o gerador do STF truncou também `portfolio_v2` (50→4)**, **`check-shard-preservation` não cobre esse diretório**, e **a correção que eu havia escrito (commitar o portfólio primeiro) congelaria a perda**. **Ordem segura obrigatória: gerador → preservação estendida → recuperação → só então reordenar.**

### Derrubados — e três deles são números que eu integrei

1. **"`verified_at` não alimenta o `lastmod`" — DERRUBADO: é desenho DELIBERADO, com teste-guarda.** `internal/content/content.go:129-137` diz literalmente: *"NASCE FORA DA CADEIA DE `LastModified()` DE PROPÓSITO. Escrever reconferência em `ReviewedAt` moveria `<lastmod>`… seria carimbo por decurso de varredura, exatamente o que a doc do Google exclui… O teste irmão `TestLastModifiedIgnoraSourcesVerifiedAt` existe para que essa separação não seja desfeita por engano."* **O agente citou `content.go:384-392` e não leu o comentário do próprio campo 40 linhas acima — violação R1 clássica.** *O fix dele por acaso converge com o desenho e pode ser aproveitado; o achado, como formulado, mandaria alguém "consertar" um contrato testado.*
2. **"46 páginas apagadas por noite" — o número é 50.** Os 4 do disco são `intent_id` **diferentes** (`adi-7236`, `adi-7774`, `are-1477280`, `mi-7516`); **perdidos = 50, todos no `published_manifest` com HTML em `public/`**. *"46 é aritmética 50−4 indevida sobre conjuntos disjuntos."* **O achado sobrevive; o número não.**
3. **"7 execuções, todas parciais" — são 6.** *"Número sem corroboração — o padrão exato que esta sessão já pagou quatro vezes."*
4. **"Diários secos há 4 dias e a onda não registra falha" — a onda REGISTROU 3 das 4** (22, 24 e 25/08, exit≠0). **Só o caso de hoje (0 edições com exit 0) passou calado.** O defeito real é um só: **vazio-com-sucesso não distinguido de falha**.
5. **"A etapa 5/9 commita" — é a 6/9.** **Rótulo errado exatamente na etapa cujo reordenamento é a correção mais delicada da onda.**

### Subestimados

- **🔴 O boot-loop está a UMA noite, não a duas.** O `else` da etapa 8/9 **não dá `exit`** — registra "publicacao" e **segue para a 9/9, que chama `reload-wiki-server` NA MESMA NOITE**. Se o `timeout 1800` matar o publish entre o sitemap (`:822`) e o manifesto (`:1733-1747`), **o próprio script reinicia o servidor contra `sitemap_loc_without_manifest`** — condição **deliberadamente fatal** (`publishedmanifest.go:1417-1420`) — com `Restart=always`, `RestartSec=5`, `StartLimitIntervalSec=0`. **Os quatro elos foram verificados no fonte.**
- **O canal de alertas é pior que o enunciado, e há um defeito novo:** **862 alertas `resolvido:false`, 127 críticas** (56 só em 21/08); *"Onda diaria de conteudo parou"* disparou **7 dias seguidos** sem nenhum resolvido. **E `SuccessExitStatus=0 1` na unit faz o `OnFailure` NUNCA disparar para onda "parcial"** — **o alerta de unit é cego para o modo de falha que ocorreu 6 de 6 vezes.** *(É a terceira contagem diferente do mesmo ledger nesta sessão — ver nota de calibração A5. O que não muda: o canal não é consumido.)*
- **O robots do STJ dados abertos: `Disallow: /api/` + `Crawl-Delay: 10`.** **A confissão do agente procede e delimita o fix:** a medição por `/api/` violou o degrau 1 da DEC-032; **o caminho por página de dataset (`/dataset/…`) é permitido e sobrevive** — **mas o coletor só é legal se implementado exatamente assim, nunca pela API CKAN.**

### Faltando

- **`https://legis.senado.leg.br/robots.txt` responde 403 Forbidden** (medido pelo Fable). **O canal de legislação proposto para substituir o `normas.leg.br` não teve robots verificado**, e a política do próprio `sourcecollect` **trata robots inalcançável como erro**. **O fix não entra sem resolver esse caso explicitamente.**
- **Ninguém propôs CONSUMO do canal de alertas** — só emissores novos. **Pela terceira onda seguida.**

### ✅ Mandatos verificados com resultado vazio

- **SaaS, cadastro ou tarefa do dono: nenhum** nas três frentes lidas. QD, STJ e Senado são dados abertos sem conta.
- **DEC-032: sem violação.** `generate-noticia-pages:23` — *"AFIRMA o fato com palavras próprias"*; art. 8º, IV é base correta para decisões do Diário da Justiça do STJ; **ninguém tratou redação de tribunal como reproduzível**.
- **Hardcode nos fixes: nenhum acrescenta literal cego.**

### Confirmado por refutação tentada e falhada

STF lê só o último JSONL e trunca · **o Fable EXECUTOU `check-v2-portfolio-pairing` → EXIT=1, 15 pendentes** · `-limite 200`/`-limite 80` hardcoded · mesma expressão *last-file* em `stj-tema:230` e `stj-sumula:167` · **`generate-noticia` lê todos, com comentário explicando o porquê (`:149-155`)** · `normas-federais` sem consumidor · registry 58 fontes / **4 habilitadas** · lock `O_EXCL` sem `signal.Notify` · **o `RESTORE.md` gerado ensina `: > manifesto`** · tetos 10/25 literais · `TimeoutStartSec=5400` contra soma de 12.900 · comentário da unit mente sobre `ExecStartPre` · `public/` no `.gitignore` e `git ls-files public/` = 0 · **nenhum commit pós-publicação** · `var/on-demand-cache` 120 MB, mtime 20/08, **zero referências no publicador e no reload** · `sourcecollect.go:33` promete ledger e não escreve · `collect-noticias-oficiais` com **zero menções a robots** · censo mtime 20/08 · fila de refinamento com 1 linha · **82 rollbacks, 0 restores** · manifesto com última aprovação em 20/08 (360 páginas) e **zero em 21-26**.

---

## O41 — Crítica Fable da onda 7: o fix do `.md` estava errado, e o erro era grave

### 🔴 S1 — O fix que eu ia adotar **CRIARIA** o caminho da `.md` até o índice do buscador

**A proposta era:** bloquear a gêmea `.md` por `robots.txt` para buscadores clássicos, mantendo o `Link rel=alternate`.

**A doc oficial do Google, aberta pelo crítico hoje, diz o contrário:**
> *"A page that's disallowed in robots.txt **can still be indexed if linked to from other sites**"* · *"This is **not** a mechanism for keeping a web page out of Google."*

**A cadeia do dano, e ela é pior que o estado atual:**
1. Bloqueada por robots, a `.md` fica **infetchável**.
2. O Googlebot **deixa de ver o `Link rel=canonical`** que hoje é **a única consolidação** (confirmado por curl: a gêmea serve `Link: <…>; rel="canonical"` e **nenhum `X-Robots-Tag`**).
3. **Links para `.md` existem e multiplicam:** 16.539 fetches por bots de IA, agentes citam URLs `.md` em transcripts públicos, **e o `llms-full.txt` lista 10.071 delas**.
4. **Resultado: `.md` como "Indexed, though blocked" — sem canonical e sem conteúdo.**

**O mesmo erro em dupla:** propor `X-Robots-Tag: noindex` **junto com** bloqueio no robots — **bloqueado, o `noindex` nunca é visto**. **O par correto por rota é UM ou OUTRO, nunca os dois.**

> **✅ O invariante de canonicidade (O35.a) SOBREVIVE e é a correção certa** — *todo canal de buscador emite somente URL cujo canonical é ela mesma*. **O que cai é o robots.txt como instrumento.**

### 🔴 S2 — E a gêmea `.md` declara `search=yes` — nenhuma frente viu

Curl de hoje na `.md`: `Content-Signal: ai-train=yes, search=yes, ai-input=yes`.

> **A única representação que carrega `Content-Signal` é exatamente a que o plano quer fora de todo canal de buscador — e ela afirma `search=yes`.** Qualquer consumidor de Content-Signal lê **o oposto** do invariante. **E o fix da outra frente ("emitir também no HTML, valor idêntico") propagaria o `search=yes` sem discutir se a gêmea deveria dizê-lo.**

**Confirmei as três pontas pessoalmente, em 2026-08-26:**

```
GET /previdenciario/135-ou-agencia/index.md
  content-signal: ai-train=yes, search=yes, ai-input=yes      ← a gêmea DIZ search=yes
  link: <…/135-ou-agencia/>; rel="canonical"                  ← e carrega o canonical
  (nenhum X-Robots-Tag)

GET /previdenciario/135-ou-agencia/
  link: <…/index.md>; rel="alternate"; type="text/markdown"
  (nenhum Content-Signal, nenhum X-Robots-Tag)

GET /llms-full.txt
  content-type: text/plain; charset=utf-8
  (nenhum X-Robots-Tag — e o arquivo lista 10.071 URLs .md)
```

**O quadro fecha e confirma o perigo do fix errado:**
1. **O `canonical` da gêmea é a consolidação que existe hoje** — bloquear por robots o torna invisível.
2. **A gêmea declara `search=yes`** — contradiz o próprio invariante que se quer impor.
3. **Nenhuma das rotas tem `X-Robots-Tag`**, e o `llms-full.txt` **expõe 10.071 URLs `.md` em texto plano, sem nenhuma diretiva.**

**A correção certa, portanto, tem três partes e nenhuma delas é robots.txt:** (a) o **invariante de canonicidade** nos canais de buscador; (b) **`X-Robots-Tag: noindex` na gêmea `.md`** — **fetchável**, para que a diretiva seja lida; (c) **rever o `search=yes`** do Content-Signal da gêmea, que hoje diz ao consumidor o contrário da intenção.

### D5 — E a premissa sobre o Google estava lida ao contrário

A página oficial diz *"Google can index the content of **most text-based files**"*, e a categoria texto é **aberta** — *"Text (.txt, .text, **other file extensions**)"* —, **com detecção por `Content-Type`**. **A ausência de `.md` da lista NÃO estabelece que o Google não indexa `text/markdown`; a própria página sugere o oposto.**
**Consequência: a conclusão sobrevive e fica MAIS urgente** — a gêmea é **plausivelmente indexável**. *"Usar 'markdown ausente da lista' como premissa de segurança é ler a fonte de trás para frente."*
**Sobre o Bing:** as fontes primárias são **posts pessoais no Bluesky de funcionários** (Canel, Mueller). **Post social de funcionário não é norma** — se entrar no `source_registry`, entra rotulado *"declaração pública de funcionário, sem documentação oficial"*.

### Demais derrubados

- **D1 — "Não existe arquivo de faixas para os user-triggered fetchers do Google" é FALSO.** `data/ops/bot_ip_ranges/google-user-triggered.json` existe, aponta para a fonte oficial certa e tem **1.056 prefixos** — **mesmo total do arquivo vivo, conferido hoje**. **O fix criaria um duplicado.** **O defeito real é outro e menor: o campo `authenticates_agents` está rotulado `['google-site-verification']` — metadado mentiroso (R1).** *(A conclusão operacional sobrevive por outro caminho: os 3 IPs do `Google-Read-Aloud` não casam com nenhuma faixa viva — "somente UA" está correto.)*
- **D2 — 🔴 O plano REPETE um comentário que mente, em vez de acusá-lo.** O cabeçalho de `generate-indexnow-incremental-submit` afirma *"não tem caller de produção… fica dormente de propósito"* — **e `run-daily-content:407` o chama** (etapa 9/9). **E o mesmo cabeçalho documenta que ligar `incremental` e `direct` ao mesmo evento produz SUBMISSÃO DUPLA — o gatilho do 403 que já mordeu o domínio — e hoje os dois caminhos coexistem.** *"Comentário que mente é bug a corrigir (R1) — o plano o promoveu a evidência."*
- **D3 — `notifications/resources/list_changed` no MCP NÃO TEM TRANSPORTE.** `internal/httpserver/mcp.go:420`: o servidor roda o SDK oficial em **modo stateless** — sem sessão, sem stream servidor→cliente. **Implementá-la exige abandonar o stateless**, mudança de arquitetura que o plano não menciona.
  **E os consumidores do `/mcp`, medidos por UA no log de hoje:** `SentinelOracle` **declara literalmente "liveness-only, never invokes tools"** (255) · `mcpbeat` "liveness check" (108) · `Go-http-client` (164) · `zevruna-monitor` (45) · `MCPWatch` "security research" (10) · `mcp2-research` (12). **Cliente-agente real na amostra: ~10 requisições de `claude-code/2.1.241`.**
  **E ninguém mediu `tools/call` × `initialize`** — o access log não mostra o método JSON-RPC. ***Isto rebaixa M27: o "vir e voltar" do `/mcp` é real em volume, mas o uso de FERRAMENTA não foi medido por ninguém.***
- **D4 — RFC 5005 é padrão sem consumidor, pelo critério do próprio plano.** Hub buscou o feed **zero vezes em 14 dias**; leitores externos ≈ 0 (**49 requisições totais, quase todas internas**). *"Consertar o truncamento de um documento não-lido é exatamente o 'trabalho perdido' que o mandato proíbe."* **→ T2.5 rebaixada: o feed só ganha investimento depois que houver leitor.**

### Não corroborados — e a classe que o dono proibiu

- **N1 — Âncora errada, erro de classe `ARQUITETURA_FIEL`:** o "onde" cita `internal/webmcp/webmcp.go` para as tools MCP. **Medido: `webmcp.go` tem 82 linhas e é o script in-page; as tools estão em `internal/httpserver/mcp.go:59-61`**, e `grep -rn structuredContent internal/` devolve **zero**. **A medição viva está certa; a âncora mandaria editar o arquivo errado.**
- **N2 — Quatro declarações de conformidade SEM instrumento**, incluindo *"O portal JÁ CONSTRUIU, **com qualidade alta**"* — **linguagem de vitória pura, que R15 proíbe**. **Todas viram "conforme em <data> pelo instrumento <X>, a reconfirmar", ou saem.** *(Aplica-se ao meu O35.d, que copiou a frase.)*
- **N3 — Duas frentes entregam fixes CONTRADITÓRIOS para `GET /mcp`**: uma manda responder com o *server-card*, outra com SSE. **No Streamable HTTP, GET abre stream SSE ou recebe 405** — devolver JSON a um cliente que fez GET esperando SSE **viola a convenção que esses clientes falam**. **Nenhuma abriu a spec. Quem implementar escolhe no escuro.** → **T3 ganha requisito: ler o texto literal da spec antes de tocar em `GET /mcp`.**

### Subestimados

- **S4 — ~13 artefatos novos despejados no mesmo canal morto.** E o crítico fechou a evidência que faltava: **os consumidores de `owner_alerts.jsonl` são `tools/notify-owner` e a unit de alerta — os DOIS PRODUTORES.** *"`check-owner-alerts-abertos` ligado ao runner é circular: o runner falha exatamente quando os alertas nascem."* **Números de hoje: 947 linhas, 184 críticas/altas abertas** (`borda-origem` 58 + `borda-cache-regra` 49). **Quarta contagem do mesmo ledger — ver A5.**
- **S5 — Hardcodes que os próprios fixes perpetuam:** `MaxEntries = 1000` literal · timer WebSub `OnUnitActiveSec=30min` · `OnCalendar` diário literal · **"bloquear nos grupos dos buscadores clássicos" implica lista literal de nomes de bot, quando o `bot_registry` já tem `purpose=search_discovery` por linha e ninguém manda DERIVAR dali** · "média móvel" sem janela definida.
- **S3 — A auto-assinatura WebSub fabricaria tráfego próprio:** com zero assinantes externos, assinar a si mesmo faz o hub buscar o feed **porque você pediu**. *"Entrega ponta a ponta vira entrega-a-si-próprio"* — **e os fetches induzidos entrariam no access log sem marcação**. **Mesma classe do falso positivo do `utm_source=chatgpt.com` que era meu.** **Se implementada, o fetch por auto-assinatura nasce marcado e fora de toda contagem, por escrito no schema.**

### F1 — A acusação mais séria, e ela me obriga a responder

> *"Ninguém restaura a Cache Rule — só se constrói detector. Quatro frentes documentaram o cache morto e nenhuma o religou nem tentou. **R7: achado vira correção na mesma sessão.**"*

**A acusação é justa contra as frentes, e não contra o plano: `T1.1` É restaurar a Cache Rule**, com corpo canônico, exclusões corrigidas e teste de aceitação. **Mas o crítico acrescenta um dado que eu não tinha e que muda o T1.1:** *"`tools/purge-edge-cache` fala com `api.cloudflare.com`, logo existe token local; **se ele tem escopo de ruleset é coisa a MEDIR, não a assumir impossível**."*

**Medi durante a sessão (M21.a): o `CLOUDFLARE_ZONE_TOKEN` LÊ o ruleset de cache e o histórico de versões.** **Se ele também ESCREVE é a medição que falta** — e ela decide se T1.1 é executável hoje ou se depende de credencial de conta. **Item de primeira ordem na execução.**

---

## O42 — Auditoria de completude: as lacunas que faltavam, e duas que invalidam tarefas minhas

> **O dono mandou:** *"lançar explorador para ler os achados de todos os agentes e ver se não esquecer de colocar no update plan… nenhum dado é descartado."* **O auditor varreu os 7 `journal.jsonl` e o relatório avulso contra este plano.** O que segue é o que ficou de fora — e **duas coisas mudam tarefas que eu já tinha escrito**.

### 🔴 O42.a — O ATOR do esvaziamento da Cache Rule **FOI identificado**, e o plano diz o contrário

**Duas frentes leram o audit log da conta Cloudflare. Eu adotei a leitura da frente que NÃO leu.**

```
GET /accounts/$ACC/audit_logs?since=2026-08-16&until=2026-08-23
  v9-v14 → rulesets_update / rulesets_create
           interface: "UI"   actor = user   cf-ray SEA/SJC
  PUTs de API do repo → separados, 13:11:02 e 13:12:13, interface: API
  v8 (2026-08-21T14:14:17Z) → sem autoria na página trazida (termina em 14:48)
```

> **O esvaziamento veio do PAINEL, pela conta do dono.** Não foi script, não foi ferramenta do repo — e os PUTs do repo aparecem **separados e identificados como API**.

**E a correção que a frente propôs começava por um passo que eu suprimi:**
> *"(1) UMA pergunta de uma linha ao dono — 'as regras de cache da zona foram esvaziadas por você no painel em 21-22/08; posso restaurar?' — porque o audit log prova autoria dele via UI, e o precedente registrado em `ops/cloudflare/README-waf.md` (**'religar sem saber por que foi desligada pode reabrir o mesmo problema'**) se aplica literalmente."*

**T1.1 está corrigida:** **não é PUT direto.** É **perguntar primeiro** — não por burocracia, mas porque **religar uma proteção que o dono desligou de propósito pode reabrir o problema que ele estava evitando**. O `README-waf.md` **não é citado uma única vez no plano**, e passa a ser leitura obrigatória antes de T1.1.

### 🔴 O42.b — Restaurar a v7 pode NÃO tirar a zona do DYNAMIC

**Medição que o plano não carregava:** **na era em que a regra do projeto estava viva (v5/v7, até 21/08), a cobertura oscilou entre 0,0% e 17,5% em 28 medições**, e a auditoria de 2026-08-19 mediu **90/90 MISS três horas depois do aquecedor**. **Os 100% HIT vieram do template de painel *"Cache everything"*, que NÃO tem `override_origin`.**

> **O teste de aceitação de T1.1 pode reprovar com o PUT correto.** **Retenção é defeito separado e ainda aberto** — e nenhuma frente conseguiu separar se a diferença é a regra, o `edge_ttl` ou os **10 `purge_everything` que o painel disparou entre 21 e 24/08**.

**O experimento prescrito, que entra em T1.1:** restaurar a v7 → **medir a cobertura por 12 h** → remover **só** o bloco `vary` → medir de novo.
**Mais a sonda diferencial que isola o `Vary`:** `/familia/` (emite `Vary: Accept-Encoding, Accept`) contra `/familia/pagina/2/` (emite só `Vary: Accept-Encoding`) — *"se a primeira ficar DYNAMIC e a segunda virar HIT/MISS, a causa é o `Vary: Accept`"*.

### 🔴 O42.c — As faixas de IP JÁ EXISTEM. O plano mandava criar o que está no disco.

**Arbitrei lendo o disco:**

```
data/ops/bot_ip_ranges/  — 11 arquivos, todos com mtime 2026-08-25 11:24 (ANTERIOR a esta sessão)
  anthropic.json · bingbot.json · duckduckbot.json
  openai-chatgpt-user.json · openai-gptbot.json · openai-searchbot.json
  perplexitybot.json · perplexity-user.json
  googlebot.json · google-special-crawlers.json · google-user-triggered.json
```

**O plano afirmava, em O2 e O3, que faltavam as listas da OpenAI e da Anthropic. Estava errado.** Três frentes da onda 1 disseram *"tem hoje apenas `google-*.json`"* e **a frente Meta disse que havia 11** — **nenhuma das quatro registrou a divergência, e eu adotei a leitura errada**.

**T4.3 corrigida:** **falta apenas `openai-adsbot.json`.** O trabalho real é outro, e é maior: **atualizar as três URLs do Google que apontam para o endereço antigo** (respondem por 301), **corrigir o metadado mentiroso `authenticates_agents`** (rotulado `['google-site-verification']`), e **adicionar Perplexity ao conjunto verificado — porque `Perplexity-User` ignora robots.txt por design, e IP é a ÚNICA superfície de controle que sobra**.

**E há uma armadilha de coleta que faria o gate ficar verde por ausência de dado:** a Amazon publica **três esquemas incompatíveis** — `amazonbot/ip-addresses` (chave `ipv4Prefix`, IPv4 solto **sem máscara**, 592 entradas) · `searchbot-ip-addresses` (chave `ip_prefix`, CIDR /32, 694) · `live-ip-addresses` (`ipv4Prefix` solto, 1.040). *"Um coletor escrito contra o formato do Google grava lista vazia para o `Amzn-SearchBot` e o gate fica verde por ausência de dado."*

### 🔴 O42.d — A armadilha do Yandex é mais forte que a regra geral, e T4.6 a dispara

**Doc oficial, literal:** *"If the `User-agent: Yandex` string is detected, the `User-agent: *` string is ignored."* **O casamento é por SUBSTRING `Yandex`, case-insensitive.**

> **No instante em que o robots.txt ganhar QUALQUER grupo contendo "Yandex", todo o grupo `*` deixa de valer para a família inteira** — e **é exatamente o que T4.6 (Clean-param para o Yandex) faria**. **T4.6 fica bloqueada até que a entrada nova traga, ela mesma, todas as guardas do curinga.**

**E o achado que a frente marcou como o mais importante da família, ausente do plano:** **`YandexAdditionalBot` e `YandexAdditional` são o canal de CITAÇÃO em IA do Yandex** — a doc confirma que **toda resposta da IA do Yandex leva referência à fonte**. **Devem ser PERMITIDOS, não bloqueados.** É o crawler com **99,28% de cobertura do acervo**.

**Correção adicional:** o plano lista `Crawl-delay` junto de `Clean-param` como *"o que o Yandex entende"* — **o Yandex NÃO considera `Crawl-delay` desde 2018-02-22** (doc oficial).

### ⚠ O42.e — E o `Disallow: /*?` NÃO está no grupo Applebot: arbitrei

Duas frentes se contradisseram e o auditor não arbitrou. **Fui ao robots servido:**

```
User-agent: Applebot / DuckDuckBot / OAI-SearchBot
Disallow:              ← vazio
Allow: /

User-agent: Applebot-Extended
Disallow: /buscar/
Disallow: /*?          ← só aqui
```

**A frente "sociais" estava certa; a frente "Apple e Amazon", errada.** **M9 e O12 do plano estão corretos** — a diretiva atinge os 8 bots de treinamento e o `Applebot-Extended`, **não** o Applebot de busca.

### Lacunas ALTAS que entram como tarefa

- **🔴 `og:image` ausente em 100% do acervo** — `grep -rl 'og:image' public/` retorna **zero**, e `internal/seo/seo.go:186-188` documenta a decisão. **Degrada de uma vez LinkedIn (exige og:image), WhatsApp (absoluta, <600 KB, ≥300 px) e facebookexternalhit — que faz 298 req/dia.** *(A onda 7 levantou o mesmo e eu o cortei de O35.d. Volta.)* Junto: **`twitter:card=summary`, não `summary_large_image`.**
- **🔴 O forjador sonda `169.254.169.254`** — **endereço de metadados de nuvem: é tentativa de SSRF/credencial**, não só rate-limit forjado. Eleva M11/M26 de "abuso de tier" para **incidente de segurança**.
- **🔴 O Fable da onda 1 só recebeu 3 das 12 famílias** (Google, Microsoft, OpenAI), truncado no meio de uma frase. **Nove famílias nunca passaram por refutação adversarial** — e o plano tratava O19 como se a crítica tivesse coberto tudo. **Item de execução: submeter as nove restantes ao Fable antes de mexer no registry.**
- **🔴 Auditar o acervo contra `noarchive` e `nocache`** — *"qualquer um dos dois corta o portal das respostas do Copilot sem afetar o ranking orgânico, e é o tipo de defeito que não aparece em nenhum gate atual"*. **Zero ocorrências no plano até agora.**
- **🔴 O DOU é INALCANÇÁVEL deste servidor:** `in.gov.br/leiturajornal` devolve `PROTOCOL_ERROR` em HTTP/2 (curl 92) e *"Empty reply from server"* em HTTP/1.1 (curl 52), com DNS resolvendo. `inlabs.in.gov.br` idem. **O plano não menciona o DOU uma vez** — num plano cuja R17 exige legislação nova todo dia.
- **🔴 Os OITO gates da DEC-032 têm NOME** e o plano só dizia "zero de oito": `legal-citation-attribution`, `derived-authorial-floor`, `source-fidelity`, `text-truncation`, `daily-cross-source-dedup`, `freshness-signals`, `pii-anonymization`. **Sem os nomes, T5 e T6 não têm o que implementar.**
- **🔴 PRESERVAR antes de corrigir as 50 páginas órfãs do STF:** *"copiar os 50 `index.html` para `.agents/runtime/` com data, porque são a única cópia"* — e só então **gerador datado de RE-INGESTÃO**, que reconstrói as linhas do shard a partir do HTML público + o registro bruto em `data/research/`. **T0.6 nomeia as órfãs e não carregava nem a preservação nem o desenho.**
- **`meta-externalads` está documentado pela Meta e não existe no registry** — o portal não governa o crawler de publicidade da Meta. **E a Meta não publica lista de IP nenhuma**: `meta-externalagent` é 45% do tráfego de bot e **fica fora do método de verificação por faixa**.
- **Smart Tiered Cache está LIGADO e INERTE** (`argo/tiered_caching: on` desde 24/08) — o plano cita Cache Reserve e nunca o Tiered.
- **Histórico de painel não versionado:** `cache_level` mudado 4× · `browser_cache_exp` 3× · **`dev_mode` ligado e desligado em 24/08** · `tiered_caching` desligado e religado · **10 `purge_everything`** — e `edge_cache_purge.jsonl` tem última linha em 20/08, **provando que nenhuma passou por ferramenta do repo**.
- **Custo medido da travessia:** borda TTFB **111-123 ms** contra origem **0,42-0,49 ms**; descontado o TLS local (~89 ms), **sobram ~30 ms de Cloudflare→túnel→nginx pagos em TODA requisição**.
- **7.710 requisições EXTERNAS/dia (48,8 MB) atravessam o túnel sem precisar**, por 12+ colos (IAD 6.777, PDX 666, EWR 372…). **É a fatia eliminável medida** — o plano só carregava o número do aquecedor.
- **89 eventos `Lost connection with the edge` nas 25 units em 24 h** — o número que sustenta o achado do Always Online desligado.

### Desenhos completos que existem nos journals e não estavam no plano

- **`/changes.json` com cursor**, derivado de `page_content_revision.jsonl` ∩ `published_manifest.jsonl`, servindo `url, content_sha256, revised_on` + link Markdown irmão. **T7.2.b só dizia "um endpoint com cursor"** — o ledger de origem não aparecia.
- **`/api/v1/novidades`** — `{gerado_em, janela, total, itens:[{url, titulo, area, tipo, publicado_em, fonte_oficial, sha256}]}`, com ETag e Last-Modified reais.
- **IndexNow — particionar ANTES de verificar:** aplicar o invariante de canonicidade, separar emissíveis de não-emissíveis, **reprovar POR URL com relatório nominal, jamais abortando o lote**. *(O plano registrava o modo de falha catastrófico e não a correção.)*
- **Ledger IndexNow endereçado por conteúdo (CAS):** lote como lista **ordenada** em `data/ops/indexnow_batches/<sha256>.txt` — **reenvio do mesmo conjunto não duplica disco**. É a resposta a M25.
- **Separar os dois conceitos que colidem num campo só:** `content_sha256` ("mudou desde o último anúncio?") × `anunciada_em`/`anunciada_por` ("houve recibo, de qual lote?").
- **Coorte de CONTROLE gravada no momento do anúncio** — mesmo estrato, deliberadamente não anunciada. **Sem ela o efeito de anunciar é inseparável de recência e rota de hub** — o confundidor que o próprio agente derrubou.
- **Ledger de coleta da DEC-032, com schema:** host, URL, método, status, bytes, sha256, etag, last_modified, duração, se veio de 304, **UA efetivamente enviado**, veredito do robots e a regra que autorizou.
- **Oráculo de coleta vazia:** `total_gazettes` já vem na resposta do Querido Diário — `total>0` com `len(gazettes)==0` é **defeito**; `total==0` é *"janela vazia confirmada pela fonte"*.
- **Marca-d'água em vez de janela fixa:** maior `coletado_na_fonte` já gravado como `scraped_since`, dedup por `url_original` — **torna a coleta idempotente e recupera sozinha os dias perdidos**.
- **Separar descobridor de detalhe na legislação:** `legis.senado.leg.br/dadosabertos/legislacao/lista?ano=` como **descoberta** (D-2) e `normas.leg.br` como **detalhe por URN** (JSON-LD `schema.org/Legislation`, CC-BY). **O plano os tratava como alternativas.**
- **O gate `check-derived-authorial-floor` reusa `internal/legalminhash` e `internal/v2bodyneardup`**, com **cálculo exato confirmando antes de reprovar**. **Nenhum dos dois pacotes era citado.**
- **`anchor_claim` truncado: guardar hash do documento + offset, nunca cortar.**
- **Teto do protocolo IndexNow = 10.000 URLs por lote** — entra em `content/freshness_policy.json`.

### Números e limitações que faltavam

**Números:** 93,3% das URLs marcadas "nunca submetidas" · o feed é **0,9%** do consumo de descoberta · **10.225 de 10.299** arquivos de `public/` com mtime às 21:00 (prova de que mtime não serve de instrumento) · **92,1%** do acervo em MÉDIO sobre 10.170 registros · **75,4%** dos itens do feed do STJ com `title` idêntico ao `description` · **423 verbetes sem `DefinedTerm`** · SGT do CNJ com **34.603 e 7.601 entradas** · **61,5%** do ledger de alertas é condição crônica · corroboração I1×I2 de 25/08 (`/feed.xml` 53=53 → **0 externo**; `/sitemap.xml` 711 origem × 25 borda → **externo ≈ 25**) · feed na borda: **79 hit / 18 miss em 20/08 contra 53 dynamic em 25/08**.

**Limitações declaradas que o plano precisa carregar** — as mais decisivas:
- **Não há tokenizador instalado.** **Todo número de token deste plano, inclusive M15.a, é estimativa por bytes/4** — bytes medidos, razão estimada.
- **O volume do bug de negociação silenciosa é IMENSURÁVEL por construção:** com `$wj_gemea` vazio, a requisição é servida do disco pelo nginx e **nunca chega ao Go**.
- **Nenhum validador externo de dados estruturados foi executado** — nem Rich Results Test nem `validator.schema.org`.
- **Os 35,3% de refetch são TETO do que a correção do 304 pode recuperar, não ganho medido** — o `log_format` não registra headers de request.
- **Todas as sondas de borda partiram do próprio host** — os TTFB absolutos **subestimam** o que um bot externo paga.
- **O enunciado oficial das súmulas do STJ é inobtenível:** `scon.stj.jus.br` 403, `stj.jus.br/publicacaoinstitucional` 404, CKAN sem dataset. **É o que torna o defeito das 80 páginas estrutural, não editorial.**
- **A licença do Informativo do STF — única base legal do canal — responde 403.**
- **O log de origem de 06 a 10/08 foi DESTRUÍDO** pelo `logrotate` do projeto vizinho, que capturava `/var/log/nginx/*.log`. Corrigido em 11/08, **tarde demais para o incidente**.
- **A taxa real de citação continua não mensurável pela origem** — **busca zero-clique na casa de ~68% é provavelmente o maior componente**.
- **Nenhum evento de "humano agiu" (clique no CTA) é gravado** — a terceira etapa do funil **não tem linha de base**.
- **O plano Free da Cloudflare não expõe status HTTP por bot no GraphQL**, e a janela máxima é **1 dia por query**.
- **Não foi medido se o Googlebot VERIFICADO recebe a injeção do `bridge.js`** — a Cloudflare pode isentar bot verificado; **a injeção está provada para requisição NÃO verificada**.

### Contradições entre frentes que ninguém registrou — e como ficam

| Tema | Posições | Arbitragem |
|---|---|---|
| **Faixas de IP no disco** | 3 frentes: *"só `google-*.json`"* · frente Meta: *"11 arquivos"* | **Li o disco: 11 arquivos. A frente Meta está certa.** ✅ corrigido |
| **Quem apagou a Cache Rule** | 1 frente: *"não tentei o audit log"* · 2 frentes: *"lido, `interface: UI`, conta do dono"* · 1 frente: *"não há registro em lugar nenhum"* | **As duas que leram estão certas.** O plano adotara a cega. ✅ corrigido |
| **`Disallow: /*?` no Applebot** | frente sociais: *"só em treinamento e Extended"* · frente Apple: *"também no Applebot de busca"* | **Li o robots servido: a frente sociais está certa.** ✅ arbitrado |
| **Submissões IndexNow** | 52.838 · 43.438 · "~39,4 mil" | **Três números, três frentes, nenhuma reconciliação. Fica aberto e é medição da execução.** |
| **Buscas externas ao feed** | 4 (achado) × 3 (relatório avulso da **mesma frente**) | contradição **interna a uma frente** |
| **Rejeições em `/mcp`** | 757/7 dias · 1.115+163/10 dias (minha) · 1.315+187/20.591 req | **três janelas, nenhuma nota de escopo** |
| **`verified_at` × `lastmod`** | frente: *"defeito"* · Fable: *"desenho deliberado com teste-guarda"* | **O Fable está certo — e O35.b ainda carrega o achado derrubado.** ⚠ marcar |
| **Cadência de notícias** | ~6/dia × 8,2/dia, **nas mesmas 24 h** | sem reconciliação |

### 🔢 Os 78 tokens de user-agent que estavam só agregados

**A onda 1 nomeou 176 entradas em 12 famílias; 78 tokens não aparecem no plano** — e **vários JÁ ESTÃO no registry e mesmo assim não eram nomeados** (`adidxbot`, `facebookexternalhit`, `meta-externalfetcher`, `Slackbot-LinkExpanding`, `MistralAI-User`, `MistralAI-Index`, `MistralAI-Training`, `FacebookBot`).

- **Google (8):** `Googlebot-Video` · `Googlebot-News` · **`Google-CloudVertexBot`** (ingestão para agente de IA **sob pedido do dono do site**) · `DuplexWeb-Google`, `AdsBot-Google-Mobile-Apps`, `googleweblight` *(aposentados)* · `Google-Firebase`, `GoogleAgent-Mariner` *(não confirmados)*
- **Microsoft (7):** `adidxbot` *(no registry)* · `MicrosoftPreview` · `BingVideoPreview` · `msnbot` *(armadilha de precedência)* · `msnbot-media`, `AzureAI-SearchBot`, `Copilot` *(não confirmados)*
- **Regionais (22):** **`YandexAdditionalBot`, `YandexAdditional`** *(canal de citação em IA)* · `YandexComBot` · `YandexRenderResourcesBot` · `YandexImages` · `YandexPagechecker` · `YandexMetrika` · `YandexDirect` · `Baiduspider` (+`-render`, `-image`, `-video`, `-news`, `-mobile`, `-smartapp`) · `Sogou web spider` · `Yeti` · `SeznamBot` · `Qwantbot` · `MojeekBot` · `search.marginalia.nu` · **`IAcrawler`** *(buscador brasileiro com índice e crawler próprios)*
- **Sociais (15):** `Twitterbot` · `facebookexternalhit/1.1` · `WhatsApp/2.x` · `meta-externalfetcher/1.1` · `meta-externalads/1.1` · `LinkedInBot` · `TelegramBot` · `Discordbot/2.0` · `Slackbot 1.0` · `Slack-ImgProxy` · `Pinterestbot` · `redditbot` · `Bluesky Cardyb/1.1` · `Mastodon/<versão>`
- **SEO (14):** `SiteAuditBot` · `SemrushBot-BA/-SI/-SWA/-OCOB/-FT/-ESI` · `SplitSignalBot` · `RyteBot` · `AhrefsSiteAudit` · `rogerbot` · `DataForSeoBot` · `barkrowler` · `serpstatbot` — **todos com doc oficial, todos com volume zero hoje, todos acionáveis por um terceiro sem aviso**
- **Outros IA (4):** `MistralAI-User/-Index/-Training` *(os três no registry)* · `omgilibot`/`omgili`
- **Meta (3):** `meta-externalads` · `meta-externalfetcher` · `FacebookBot` *(saiu da doc oficial — resta confirmação de terceiro)*
- **Apple e Amazon (3):** `iTMS` *(não segue robots por design, mesmos hosts da Apple)* · **`AmazonAdBot`** *(único bot Amazon que honra `Crawl-Delay`)* · **`AmazonProductDiscoverybot`** *(assina com RFC 9421)*
- **OpenAI (1):** `ChatGPT Atlas` · **Perplexity (1):** `Comet` · **Anthropic (0):** família integralmente coberta

**E a inversão de prioridade, dita com número:** os bots de SEO caem em `unknown_guard_rate_limit` — **120 rpm, o DOBRO do que o portal concede a bots de treinamento (60) e SEIS VEZES o tier estrito (20)**. ***"Quem paga em citação é limitado; quem não paga nada é liberado."***

### As ~60 fontes oficiais com URL e data

**Estão nos journals e não no plano.** Entre as decisivas: as três listas canônicas do Google (`common-crawlers.json`, `special-crawlers.json`, `user-triggered-fetchers.json`) · `developers.openai.com/api/docs/bots` e os quatro `*.json` da OpenAI · **`help.openai.com/…/publishers-and-developers-faq`** (a declaração do `utm_source=chatgpt.com` que sustenta T4.7) · `platform.claude.com/docs/en/api/ip-addresses` · `bing.com/toolbox/bingbot.json` · **`bing.com/webmasters/help/robots-meta-tags-…`** (sustenta o achado `noarchive`/`nocache` × Copilot) · **`indexnow.org/faq`** (a FAQ que desaconselha o despejo em massa) · `yandex.com/support/webmaster/en/yandex-ai` · `docs.cohere.com/docs/cohere-web-crawlers.md` (o desmentido da Cohere, que o plano afirma sem citar) · `w3.org/TR/websub` · `rfc-editor.org/rfc/rfc9309.html` · **as quatro fontes RSS que o canal de notícias consome** · `dadosabertos.web.stj.jus.br/robots.txt` · **`portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF`** (a licença do Informativo, que responde 403) · `github.com/modelcontextprotocol/registry`.

**Todas entram no `source_registry` com URL, data de verificação e — quando for o caso — o rótulo *"declaração pública de funcionário, sem documentação oficial"*** (o caso dos posts de Bluesky sobre o Bing).

---

## 🔴 O43 — RED-TEAM SOBRE ESTE PLANO: o que ele derrubou, e a quarta correção perigosa

**O crítico adversarial leu o plano consolidado e o atacou. Achou uma bomba, dois números errados meus, sete contradições residuais e — o mais grave — uma lista de achados que eu declarei "entram como tarefa" e que NÃO viraram tarefa nenhuma.**

### 🔴🔴 A QUARTA CORREÇÃO PERIGOSA: T1.3 congelaria a mutilação do portfólio

**Eu havia isolado o perigo em T6.1 e colocado um banner lá. O crítico mostrou que a bomba está em T1.3, na Fase 1, ANTES de T6.1 existir.**

**A cadeia, verificada por ele no disco e por mim:**
1. T1.3 manda **destravar a fábrica** na Fase 1.
2. Destravar exige o reordenamento 5/9↔6/9 — **que é de T6.1, na Fase 6**.
3. **T1.3 recupera só o shard de `v2_pages` e NUNCA menciona `portfolio_v2`** (medido: `portfolio_v2/jurisprudencia-stf-derivada-01.jsonl` = **4 linhas contra 50 no HEAD**).
4. **T1.3 não estende `check-shard-preservation`** (medido: `DIRETORIO = "data/editorial/v2_pages"`, linha 45 — **o portfólio segue sem guarda**).
5. **Com a onda destravada, `run-daily-content:313-316` faz `git add data/editorial/portfolio_v2` + commit INCONDICIONAL do diff.**
6. **Resultado: a mutilação 50→4 vira a nova verdade — exatamente o dano que o banner de T6.1 proíbe.**

**Agravante que ele verificou executando:** o próprio `check-v2-portfolio-pairing` **imprime hoje** *"PRÓXIMO COMANDO: `git commit -- data/editorial/portfolio_v2`"*, com **15 pendentes**. **O gate está literalmente instruindo o passo que causa o dano.** E `stj-tema`/`stj-sumula` carregam **a mesma bomba last-file**, também sem guarda de portfólio.

> **✅ CORREÇÃO: T1.3 NÃO destrava a fábrica.** A ordem segura de T6.1 (**gerador read-all → estender a preservação a `portfolio_v2` → recuperar os 50 → só então reordenar**) **passa a ser pré-requisito de T1.3**, e nenhum commit de portfólio acontece antes do passo 3. **T1.3 fica reduzida, na Fase 1, ao timer próprio do IndexNow** — que não depende da onda.

**E o segundo problema de T1.3, também dele:** o critério *"`find public -newermt <hoje>` não vazio"* **exige publicação na Fase 1**, contra O38 (*"destravar a fábrica antes de corrigir o molde seria industrializar o defeito"*, **13-20 páginas/dia**) e contra os **7 pré-requisitos de O35.c**, nenhum listado como dependência. **O critério muda: a Fase 1 entrega a fábrica DESTRAVÁVEL, não fábrica publicando.**

### Números meus que ele derrubou — e eu remedi

**1. O número dos alertas estava errado, e o antídoto A5 também.** Ele mostrou que *"25 chaves não resolvidas, 7 críticas"* é **tautologia**: **todo alerta nasce `resolvido:false`**, então "alguma linha aberta na história" dá 25/25 por construção. **Refiz pela última linha por chave, que é a semântica de estado de um ledger append-only:**

```
998 linhas · 25 chaves distintas
ÚLTIMA linha por chave → 18 não resolvidas
   3 CRÍTICAS: borda-cache-regra · borda-origem · tunel-uplink
   9 ALTAS:    onda-diaria-{20,21,22,23,24,25,26}/08 · tunel-frota
               unit-falhou-wikijuridica-daily-content
```

**Três leituras diferentes do mesmo arquivo nesta sessão** — 48, 839/118, 25/7, e agora 18/3+9. **E o crítico está certo sobre a causa: o antídoto A5, como eu o escrevi, diz "ler por chave" e NÃO diz QUAL linha nem QUAL severidade.** **A5 corrigido: última linha por chave, e a severidade declarada.**
**E note o que a lista revela:** **7 das 9 altas são `onda-diaria-<data>` — uma por dia.** É a chave com data dentro, que faz cada dia parecer alerta novo (T6.10). **A gravidade sobrevive: 3 famílias críticas abertas há dias sustentam T1.4.**

**2. "Os OITO gates da DEC-032 têm nome" — a lista tem SETE.** `legal-citation-attribution`, `derived-authorial-floor`, `source-fidelity`, `text-truncation`, `daily-cross-source-dedup`, `freshness-signals`, `pii-anonymization`. **O oitavo continua sem nome — e sem nome, T5/T6 não têm o que implementar.** Achar o oitavo é tarefa da execução.

### Contradições residuais que ficaram — todas corrigidas aqui

| Onde | O conflito | Resolução |
|---|---|---|
| **T2.5 / T7.2 × O41/D4 × O35.a** | O41 rebaixou T2.5 (*"o feed só ganha investimento depois que houver leitor"*) e as tasks seguiram sem a marca — **mandando expor `rel=alternate` para Markdown por entrada, que é o caminho da `.md` até o Bing** | **T2.5 e T7.2 ficam BLOQUEADAS.** O `rel=alternate` no feed **só entra depois do invariante de canonicidade (R18)**, e o invariante **cobre o feed explicitamente** |
| **T1.3 × O40** | O40 derrubou "46" (é 50, conjuntos disjuntos) e T1.3 ainda dizia 46 | **corrigido: 50** |
| **T5.4 × O27 e O18** | T5.4 abria com "95%" (O27 corrigiu para 87,99%/90,97%, **e o que importa é 0% como citação atribuída**) e dizia "61,1%" onde O18 diz 64% | **corrigido** |
| **M12 × O24/D-4 × T3.9** | D-4 diz que 301 viola *"redirect como solução"*; M12 propõe 301 **sem argumentar**; T3.9 propõe 301 **argumentando que a rota de destino existe** | **T3.9 sobrevive** (não cria rota fantasma); **M12 não vira task** sem o mesmo argumento |
| **M3 × M28** | M3 rotula "TOTAL de bot **verificado**: 38.134" incluindo chaves que M28 mede como `unverified_at_edge` | **M3 corrigido**: o total mistura verificado e alegado |
| **G1 × T-1** | G1 diz "7 `journal.jsonl`"; T-1 dizia "cinco ondas" | **corrigido: são 8 ondas** |
| **T1.1 banner × corpo** | o banner declara o experimento de 12 h e o corpo mantinha o teste binário | **corrigido** |

### 🔴 O achado mais grave de todos: eu declarei "entra como tarefa" e não criei a tarefa

**O crítico fez o grep e a lista é constrangedora.** *"Zero das 'Lacunas ALTAS que entram como tarefa' viraram task nas Fases."*

**E entre elas está a QUEIXA-MANCHETE DO DONO:**

> **As 185 rotas `/pagina/N/` sem Markdown NÃO TÊM TASK NENHUMA.** M23 as elevou a *"buraco no canal principal"*; D-4 prescreveu a correção compatível (`Link rel=alternate` da fatia → índice do hub + corrigir o `llms.txt`); O23 mediu que *"as 185 rotas não anunciam nenhum alternate"*. **E a única aparição em formato de tarefa está no ANEXO SUPERADO, com a correção ERRADA** (*"gerar Markdown para paginação"*), **refutada por O20**.

**As tarefas que faltavam, criadas agora — Fase 8:**

**T8.1 — As 185 fatias de paginação anunciam o Markdown do hub, não um `.md` próprio.** Correção de D-4, compatível com o contrato: `map $wj_link_alt` aponta a fatia para o **índice Markdown do hub**, e o `llms.txt` deixa de prometer o que não existe. **PROIBIDO 301** (*"URL existe = conteúdo existe"*) e **PROIBIDO gerar `.md` de paginação** (refutado por O20). **Verificar:** `Accept: text/markdown` numa fatia **nunca devolve HTML calado**; o `llms.txt` não promete `.md` para as 185.
**T8.2 — `og:image` em todo o acervo.** Ausente em **100%** (`grep -rl og:image public/` = 0); degrada LinkedIn, WhatsApp e `facebookexternalhit` (**298 req/dia**). Junto: `twitter:card` de `summary` para `summary_large_image`. **Sem hardcode:** imagem derivada do dado da página. **Contra-teste:** HTML continua **≤ 50 KB** e o peso adicional é declarado em bytes.
**T8.3 — Incidente de segurança: o forjador sonda `169.254.169.254`.** Não é abuso de tier — é **tentativa de SSRF/credencial de metadados de nuvem**. Bloquear o padrão na borda e **verificar que o portal não tem caminho que alcance esse endereço**.
**T8.4 — Submeter as NOVE famílias da onda 1 nunca refutadas ao Fable.** O crítico da onda 1 **só recebeu 3 de 12**, truncado. **Pré-requisito de T4.2** — mexer no registry com nove famílias sem crítica é o que este plano passou a sessão inteira evitando.
**T8.5 — Auditar o acervo contra `noarchive` e `nocache`.** *"Qualquer um dos dois corta o portal das respostas do Copilot sem afetar o ranking orgânico, e não aparece em nenhum gate atual."*
**T8.6 — As 5 institucionais entram no `llms.txt`.** `/sobre/`, `/metodologia/`, `/fontes/`, `/aviso-legal/`, `/privacidade/` — **zero ocorrências hoje**, e são as que provam autoria. M24 chamou de *"correção de minutos"* e não virou task.
**T8.7 — Os 5 `check-*` sem caminho de saída ≠ 0** — **dois guardam colisão de rota pública**. Gate que não pode reprovar.
**T8.8 — Leitor canônico de `crawl_coverage_daily.jsonl`** (21 linhas para a mesma chave) e **origem do `total_indexado: 10.077`** do MCP, o único número órfão.
**T8.9 — `meta-externalads` no registry** e o **DOU inalcançável** (`PROTOCOL_ERROR` em HTTP/2, *"Empty reply"* em HTTP/1.1, DNS resolvendo) — investigar o caminho de rede antes de desistir da fonte.

### Tarefas sem "como verificar" — o preâmbulo prometia e não entregava

**O crítico listou ~19:** T0.8, T3.3, T3.4, T3.5, T3.7, T4.4, T4.5, T4.7, T4.8, T4.9, T4.10, T5.1-T5.3, T5.5-T5.8, T5.11, T6.3, T6.9. **E a tabela de contra-testes cobre ~11 famílias de ~40 tasks — com T4.5 e T4.6, que tocam robots e allowlist, FORA dela.**

> **Regra corrigida, e ela é executável:** **o ciclo de 6 passos do PROTOCOLO vale para TODA tarefa, sem exceção.** Onde a tarefa não traz "como verificar" explícito, **o passo 1 (medir antes) define o critério** — e a tarefa **não sai de `medindo-antes` no frontboard enquanto o critério não estiver escrito**. **A ausência vira bloqueio de estado, não licença para pular.**

### Gates: eu escrevi "nenhum antes de T1.4" e violei por ordenação

**T0.3 e T0.5 são dois dos doze e vivem na Fase 0 — antes de T1.4 existir. T1.2 precede T1.4 dentro da própria Fase 1.** E **há pelo menos 4 gates fora da minha contagem de doze**: o das guardas do curinga (T4.1), o de token registry×consumidores (T4.2), o piso de 82,6% (T5.12) e a auditoria `noarchive`/`nocache` — **mais os 7-8 da DEC-032, nomeados e sem task que os crie**.

> **Regra corrigida:** **T1.4 sobe para a FASE 0**, como **T0.9**, e passa a ser pré-requisito real de todos. **Exceção declarada e única:** `check-binario-vs-fonte` (T0.3) e `nginx-config-alcancavel` (T0.5) **podem nascer antes**, porque **são gates de pré-condição da própria execução** — reprovam antes de qualquer trabalho começar e não dependem de canal de alerta para serem lidos. **A exceção fica escrita; o resto espera.**

### Correções perigosas adicionais que ele apanhou

**T2.1 (ETag por `map $uri $wj_etag`) tem dois buracos:**
- **O manifesto não cobre as 7 institucionais indexáveis** (O32.e — verificado: `grep '/sobre/' published_manifest.jsonl` = 0 e `public/sobre/index.html` existe). **T2.1 não diz o que a rota descoberta serve** — ETag vazio? removido? o default? **Viola a regra do próprio plano: "caso não coberto reprova em gate, nunca fallback silencioso".**
- **Ninguém verificou se ETag injetado por `more_set_headers` participa da avaliação de `If-None-Match` do nginx** — o filtro de 304 compara contra o ETag **interno**. **Se não participa, T2.1 entrega validador anunciado que nunca valida.** **Medição obrigatória na execução, antes de aplicar.**
- **E mesmo aplicado, o ETag não chega a bot nenhum enquanto a borda o remover (T3.1, Fase 3)** — dependência que só T2.4 menciona.

**T0.6 (Validate cobrindo `public/` → manifesto) colide com as mesmas 7 institucionais:** a extensão ingênua **ou exige allowlist literal (R13) ou reprova no boot** — e **falha de `Validate` aborta o servidor**. **Falta a regra derivada de isenção antes de fechar o gate nos dois sentidos.**

### Violações de regra minhas

- **R15 em T6.12:** *"A tubulação JÁ EXISTE e está correta… o frescor chega sozinho na madrugada seguinte"* — **declaração de vitória sobre comportamento futuro**, sem data, sem instrumento, sem "a reconfirmar". **Corrigido.** *(Menor: O5.b, "já correto" ×2.)*
- **R13 em T1.1, calibrada:** acrescentar exclusões **literais** de rota ao `cache-rules.json` **não é violação** (JSON de ops é dado, não código) — **mas perpetua a armadilha 1 de O21** (*"o JSON versionado está desatualizado em relação às rotas criadas desde então"*), **quando a alternativa derivada — `respect_origin` para a classe de descritores — está escrita em M21 e não foi a escolhida**. **T1.1 passa a preferir a derivada.**

### E o que ele tentou derrubar e não conseguiu

**T2.2 (parar a rebobinada do mtime) NÃO causaria date-bumping** — ele leu `gravaDatado:2433-2467` e confirmou que `grava()` devolve `mudou=false` e **pula a escrita** quando os bytes são idênticos; sem o `Chtimes`, o mtime fica na última escrita real. **A formulação é segura.** · **O42.c** (11 arquivos de IP) confere · **O42.e** (`/*?` fora do Applebot de busca) confere · **T6.2** (last-file no gerador STF, **inclusive a extensão ao portfólio**) confere · **O41/D2** (o comentário do IndexNow mente) confere · **T0.3.c** (`grep -c robots tools/check-http-smoke` = 0) confere · **`strongETag` em `conditional.go:44-47`** confere · **a aritmética de M8 e M15.a** e **a soma de M3** fecham.

---

## O44 — Onda 8: as dependências. Você estava certo, e o número era exato.

> **Sua ordem:** *"Se no repo tem 202 dependências, elas podem estar com bugs, e deve corrigir ou integrar."*
> **O número 202 está EXATO** — 74 diretas + 128 indiretas. **E a minha medição de "66 diretas" estava errada:** contei um bloco `require` e não o arquivo inteiro. **São 74.**

### 🔴 O44.a — Quatro vulnerabilidades VIVAS, e o gate que as veria está vermelho há 28 dias

| Vulnerabilidade | Onde |
|---|---|
| **GO-2026-6179** e **GO-2026-6180** | `golang.org/x/mod v0.37.0` — **dependência DIRETA** — *bypass de verificação do sumdb*, corrigidas em v0.40.0 |
| **GO-2026-6222** | `golang.org/x/image v0.43.0` — alocação excessiva ao decodificar WebP VP8L (CVE-2026-46603), corrigida em v0.45.0 |
| **GO-2026-5932** | — |

**Confirmadas por DOIS instrumentos independentes que concordam integralmente.**

**E o achado que importa mais que as quatro:**

> **O projeto JÁ TEM instrumento de vulnerabilidade — `govulncheck` v1.5.0 e `osv-scanner` v2.4.0 — e ele JÁ ESTÁ VERMELHO HÁ 28 DIAS.** O memo grava `verdict=fail` do `check-sca-osv` **desde 2026-07-29**, apontando exatamente **GO-2026-5932**. **Ninguém corrigiu.**

**Somam-se:**
- **As 5 exceções de vulnerabilidade em `tools/sca/osv-scanner.toml` EXPIRARAM em 2026-07-30** — 27 dias atrás — **e o próprio código tem o detector para isso** (`sca_ignore_policy_ignore_until_expired`).
- **O último `govulncheck` vivo rodou em 2026-08-12 e passou VERDE — um dia ANTES de as vulnerabilidades de `x/mod` serem publicadas.** **O verde é obsoleto, não é prova.**
- **31 módulos afetados nos 5 módulos de FERRAMENTA**, que o gate de produto **explicitamente não cobre por contrato**.
- **`govulncheck` está pinado em v1.5.0 e a versão atual é v1.7.0** — o detector está duas minor atrás da base que consulta.
- **Três checks da família SCA nunca produziram memo** — não há evidência de que `sca-licenses`, `sca-scorecard` e `sca-gitleaks-secrets` tenham rodado.

### 🔴 O44.b — O remoto GitHub está 2.332 commits e 77 dias atrás do HEAD

> **Dependabot e CodeQL NUNCA viram o código que roda hoje.**

E daí decorre: **o SBOM CycloneDX commitado como evidência está 55 dias defasado** — **não contém 13 das 74 diretas e erra a versão de outras 5**; **21,6% dos pares `module@version` do `go.mod` não têm cobertura nele**. **O gate `sca-govulncheck` está registrado e NÃO PERSISTE NENHUMA EVIDÊNCIA — a única prova de que rodou é uma mensagem de commit.** *(E esta sessão já mediu que mensagem de commit mente.)*
**Dois módulos Go do repo estão FORA do Dependabot** (`/tools/perf` e `/tools/duckdbolap`) — **e são justamente onde estão as vulnerabilidades** —, **e o gate que deveria pegar isso tem a lista fixa**: gate verde não é prova.

### 🔴 O44.c — `json-iterator/go` está ARQUIVADO, dentro do binário público

**`archived: true`** confirmado por dois instrumentos (API do GitHub e a página HTML com o rótulo *"Public archive"*), `pushed_at` **2024-05-27**, **272 issues abertas**. Versão fixada **v1.1.12, de 2021-09-11 — 1.809 dias**. **Está no binário que serve o portal, com 19 pontos de chamada em produção.**

**Rota de saída, e ela é segura:** migrar os 19 call sites de `jsoncodec.UnmarshalIterator` para `jsoncodec.Unmarshal` (`goccy/go-json`), **que já é o `PrimaryJSONModule` declarado no próprio wrapper**. **A migração é semanticamente segura porque o jsoniter está configurado como `ConfigCompatibleWithStandardLibrary`** — mesmo contrato que o goccy honra. Manter `UnmarshalIterator` como alias durante a transição.

### 🔴 O44.d — Os codecs JSON: o risco é maior do que redundância

- **O caminho de publicação escreve com `encoding/json` da stdlib e o servidor lê com `json-iterator`** — **dois codecs sobre o artefato mais importante do portal**.
- **O SHA-256 de integridade do `contentstore` é função dos bytes exatos do `goccy/go-json`, e NENHUM teste fixa esses bytes.** **Uma atualização do codec muda o hash de integridade sem ninguém perceber.**
- **`goccy/go-json` — o decodificador PRIMÁRIO — tem issue ABERTA de panic por entrada malformada em sequência**, aberta há 3 dias.
- **`json-iterator` acumula 41 issues abertas de crash.**
- **`segmentio/encoding` está linkado no binário de produção com ZERO chamadores** — e **há um ADR que afirma o contrário**.
- **A família JSON tem SEIS membros, não quatro** — minha medição subcontou.

### ✅ O44.e — E a redundância se INVERTE quando se mede o binário servido

**Dois instrumentos independentes concordam item a item** — grafo de imports estático (58 pacotes internos alcançáveis de `cmd/server`) e **`strings -a` sobre o binário de 35.708.022 bytes**:

```
meilisearch=0 · typesense=0 · opensearch=0 · blugelabs=0
pebble=0 · badger=0 · ristretto=0 · golang-lru=0
simdjson=0 · gjson=0 · sjson=0 · sqlite=0 · bigcache=0
blevesearch=13714   ← o único motor de busca no binário servido
```

> **O processo em produção NÃO carrega nenhum dos quatro bancos KV, nenhum cliente de serviço externo e nenhum motor de busca além do Bleve.** **A redundância é real no `go.mod` e quase inexistente no que serve o site.**

**E o alcance real corrige a leitura inteira:** **apenas 27 das 74 diretas chegam aos binários públicos** (`cmd/server` + `cmd/build`); **46 vivem só no `cmd/check`** e 1 é só de teste. **64% das dependências diretas não tocam a página servida.** **E 52 das 74 têm UM ÚNICO arquivo de produção que as importa.**

**O contrato self-hosted first NÃO está violado — medido por três instrumentos:** `ss -ltnp` (nada em 7700/9200/8108), `docker ps -a`, `ps aux`. Os três clientes vivem em `internal/searchsidecarclients/clients.go`, que declara **`PublicServing: false`** e **`LoopbackOnly: true`**, e **não é alcançável a partir de `cmd/server`**.

**⚠ E uma advertência de método que me atinge:** *"o diretório `.cache/` contém árvores completas de source que inflam qualquer auditoria por grep — a medição do próprio chefe pode estar afetada."* **As minhas contagens de import por `grep -rl` não excluíram `.cache/`.**

### O44.f — Estado das 74, e o que fazer com cada grupo

| Estado | Quantas | Ação |
|---|---|---|
| Em dia | **16** | — |
| Atrasadas minor/patch | **37** | atualizar as do binário público primeiro (**RoaringBitmap está 14 releases atrás**) |
| Atrasadas **major** | **2** | **`ristretto` v0.2.0 direta + `ristretto/v2` v2.2.0 indireta — DUAS linhas major da mesma biblioteca no mesmo build** |
| **Abandonadas** (sem release **e** sem commit há >18 meses) | **8-9** | **duas são de 2015 e 2019, e ambas no binário público** |
| Sem release >18 meses, repositório ativo | **10** | monitorar |
| **ARQUIVADA** | **1** | `json-iterator` — O44.c |

**Licenças:** **zero GPL/AGPL/LGPL reais** · 70 permissivas · **4 fora da lista** (2× MPL-2.0, 1× **CC0-1.0 no binário público**, 1× em transição MIT→Apache-2.0).
**⚠ E o agente reportou um bug do próprio detector, antes de publicar:** *"acusou GPL/LGPL/AGPL em 2 módulos MPL-2.0"* — **corrigido antes de reportar**.

**Violação de contrato medida: 18 das 74 diretas não têm ADR — e a mais grave é o codec JSON PRIMÁRIO do binário público.**

**Outros achados:**
- **`minio/sha256-simd` está no binário como pass-through literal para a stdlib** — **a CPU desta máquina não tem `sha_ni` nem AVX-512**.
- **OpenTelemetry cria um span por requisição no caminho quente, sem `TracerProvider` e sem exportador** — **custo por requisição com zero observabilidade em troca**.
- **`content/pages.json` (72,9 MB) é lido inteiro para a memória e decodificado SEM modo estrito**, embora o próprio facade já ofereça a variante estrita.
- **Não existe `vendor/`:** o build só é reprodutível offline por um **cache de 18 GB fora do repo, fora do git e sujeito a GC**.
- **`GOTOOLCHAIN=auto` no caminho interativo permite download silencioso de toolchain**; o pre-commit já é fail-closed e ninguém notou a assimetria.
- **`CLAUDE.md` declara toolchain go1.26.4; o `go.mod` e o wrapper dizem go1.26.5** — comentário que mente.
- **Ponto único de falha:** 15 dos 67 módulos do binário público vivem em **namespace pessoal**, o mais antigo com **7 anos**.
- **Os dois parsers de robots estão congelados há 4 e 5 anos** — e são **o único código que lê arquivo de terceiro para decidir política**.
- **`gofeed` pulou de v1.3.0 para v1.4.x** sem CVE envolvida.

### ✅ O44.g — O que está sadio, medido e não presumido

- **Integridade criptográfica:** `go.sum` cobre **564/564**, **`go mod verify` responde "all modules verified"**, **zero `replace`/`exclude`/`retract`**, e **nenhuma variável que desligue verificação** (`GOFLAGS`, `GOPRIVATE`, `GONOSUMDB`, `GOINSECURE` vazias; `GOSUMDB=sum.golang.org`).
- **Zero chamadas de rede em `init()`** — **188 arquivos com `func init()` varridos**. Os 14 hosts literais em 1.930 arquivos `.go` são todos de documentação/spec. **O SDK MCP é servidor (inbound), não cliente.** **Não há exporter OTLP.**
- **Zero workaround de bug de dependência no código** — a varredura não achou nenhum.

### O44.h — Integrações: o que instalar, e o que já existe

| Item | Veredito medido |
|---|---|
| **Tokenizador** | **`github.com/tiktoken-go/tokenizer` v0.8.1 (MIT)**, restrito a **gerador OFFLINE** — **`pkoukk/tiktoken-go` DESQUALIFICADO** por baixar vocabulário em runtime |
| **Web Bot Auth** | **`cloudflare/web-bot-auth` é RUST — não importável em Go.** E o verificador RFC 9421 **alcançaria só 3,95% do tráfego**. **A decisão é de COLOCAÇÃO, não de biblioteca** — adiada com razão medida |
| **Validador de JSON-LD** | **JÁ EXISTE e nunca foi apontado para o site** — a evidência cobre **360 registros de ensaio de 2026-07-01** contra **10.294 páginas reais** |
| **Verificação de bot por IP** | **JÁ EXISTE**, com DNS reverso + direto (`gaissmai/bart` + `miekg/dns`) — **nada a instalar** |
| **robots contra RFC 9309 · coerência de sitemap · cliente de teste MCP** | **as três já têm ferramenta no repo — nada a instalar** |
| **Gerador de carga** | **Vegeta já está integrado** — mas a única evidência mede **rota de ENSAIO de 01/07, anterior à publicação do site** |

**🔴 E um achado de conteúdo que veio junto:** **293 páginas publicam JSON-LD do tipo `HowTo`, cujo rich result o Google REMOVEU em 14/09/2023** — **1.149.327 bytes de marcação sem retorno possível**.

**E outro divisor hardcoded, irmão do meu:** **`estimateInputTokens` usa `len(json)/4`** — **e esse número entra num ledger de CUSTO**. **Nenhum instrumento do repo confirma o divisor.** É exatamente o problema que o tokenizador resolve.

**Validação de vocabulário schema.org: o agente construiu e rodou agora, sem dep nova** — **13/13 tipos e 45/46 propriedades válidos**. **11 propriedades e 1 tipo estão em `pending.schema.org`** — mas o agente ressalvou que *"`isPartOf` sozinho NÃO é sinal confiável de termo provisório"*.

---

## O45 — Crítica Fable da onda 8: dois falsos negativos dela, e três fixes que não podiam ser aplicados

### 🔴 O toolchain `go1.26.5` está DENTRO da faixa afetada — e cinco agentes tinham o JSON na mão

**Os registros OSV de GO-2026-6179 e GO-2026-6180 trazem DUAS entradas `affected`:**
```
golang.org/x/mod   → fixed 0.40.0
toolchain          → fixed 1.25.13 / 1.26.6 / 1.27.0-rc.3
```
**O `go.mod` pina `toolchain go1.26.5`, e o binário de produção foi construído com go1.26.5.** **Ambos < 1.26.6.**

> **Nenhum dos cinco agentes reportou — e a frente de conformidade chegou a auditar `GOTOOLCHAIN=auto` sem notar que o toolchain PRESENTE já está na faixa.**

**Escopo correto, e o crítico o delimitou:** **a exposição é no caminho de verificação do sumdb do próprio `go` (download de módulo), não no runtime do servidor** — **zero import de `sumdb` em código de produção**. **Correção: baixar `go1.26.6` para `.toolchains/` junto com o bump de `x/mod`.**

### 🔴 `.git/codex-private-go-cache/` — ~100 módulos espelhados DENTRO do `.git`

**Legado do Codex desativado.** **Morde qualquer `grep -r` feito na raiz — inclusive os meus.** A advertência de método da onda listava `.cache/gate-build` e `.cache/dead-tmp-quarantine`; **este terceiro espelho não aparece em nenhuma das cinco frentes.**

### Derrubados — e três deles são fixes que teriam quebrado algo

1. **🔴 "18 das 74 diretas sem ADR" — a formulação CAI, e agir sobre ela criaria ADRs duplicados.** O `goccy/go-json` **tem registro completo** em `internal/codex2policyenforcement/policy.go:2495-2522`: `DecisionReason`, licença, versão pinada, `AllowedWriteScopes` e **`BenchmarkEvidencePath = "data/ops/jsoncodec_goccy_evidence.jsonl"` — arquivo que EXISTE** (1.597 B, 2026-06-30). **O agente cruzou os 74 paths só contra `docs/adr/` e `DECISIONS.md`, ignorando o registry de policy** que a própria frente vizinha cita como ADR. **Resíduo comprovado: só `otel` está genuinamente sem registro.** Os outros 16 têm hits em `policy.go` que **ninguém leu um a um** — podem ser *needle-string*, como o hit de `ristretto` em `:2985`.
2. **🔴 "O memo replaya a reprovação a custo zero" — mecanismo errado.** `scaMemoTTL = 24h`; `scaMemoFresh` devolve `false` para `age > TTL` (`sca_memo.go:190-192`). **O memo de 29/07 está EXPIRADO há 27 dias e não replaya nada.** **A leitura precisa é pior, não melhor:** *"nenhuma execução de `sca-osv` produziu veredito memoizável desde 29/07 — **a cor ATUAL do gate é DESCONHECIDA**"* (os irmãos `sca-sbom` e `sca-actionlint` têm memos **de hoje**; o `sca-osv` parou em 29/07). **A substância sobrevive: o último veredito gravado é `fail` por GO-2026-5932, e o advisory não tem evento `fixed`.**
3. **🔴 TRÊS fixes que violam contrato ou não compilam:**
   - **"Remover `MarshalCompatibility`/`UnmarshalCompatibility` e tirar `segmentio` do `go.mod`"** — o `CLAUDE.md` **proíbe** *"deletar código/variável/import para resolver"*.
   - **"Trocar `sha256-simd` por `crypto/sha256`"** — viola **ZERO REGRESSÃO** (*"simplificar código que já funciona em produção"*). **O fato é verdadeiro** (`hashdigest.go:26` é pass-through e a CPU não tem `sha_ni` nem `avx512f`, só `avx2`) — **o fix é que não pode ser aplicado assim.**
   - **"Mover `searchsidecarclients` para outro módulo"** — **NÃO COMPILA**: é importado **de verdade** por **três** pacotes (`ossinstallmatrix/matrix.go:28`, `ossscaleintegration/coverage.go:82`, `searchbackendbench/bench.go:23`).
   > **Três agentes deram três disposições contraditórias para o MESMO fato — integrar, manter, remover.** **Adjudicação única: vale a de "manter"**, que é a contratualmente válida. *(E o `UnmarshalCompatibility` **tem** teste que pina o contrato: `jsoncodec_test.go:33-45`.)*
4. **"Instalar Meilisearch e fazer valer"** — **contradiz o ADR deliberado de probe-bank** e **duplicaria o Bleve, que está SERVINDO busca viva**: o crítico mediu **`curl 127.0.0.1:8089/buscar/?q=pensao` = 200**. *"Instalar um segundo motor para justificar um cliente é resolver a dependência criando infraestrutura redundante."*

### Não corroborados

- **"Dois codecs sobre `pages.json`" como severidade ALTA — não se sustenta.** Os fatos batem, **mas a medição do próprio agente deu 0 chaves duplicadas, 0 bytes residuais, 0 arquivos mistos, UTF-8 limpo** — **ele mediu a AUSÊNCIA do defeito que alega**, e "alto" sem cenário de falha demonstrado. **✅ Mas o achado irmão FICA DE PÉ e é o risco real da família: o SHA-256 do `contentstore` é tomado sobre bytes do `goccy` (`:623`) e decodificado por `json-iterator` (`:627`), sem golden test.**
- **A partição 27/46/1 por alcance de binário é instrumento único** (`go list -deps`, não reproduzido). **Corroboração parcial:** `go version -m` confirma o subconjunto conferido — `goccy`, `json-iterator`, `segmentio`, `sha256-simd` **dentro**; `meilisearch`, `typesense`, `opensearch`, `bluge`, `pebble`, `badger`, `ristretto` **fora**.
- **Call sites de `UnmarshalIterator`: 19, não 21** — arbitrado por grep próprio (19 linhas em 11 arquivos).

### ✅ O que resistiu à refutação, com fonte aberta pelo crítico

**74 + 128 = 202** (parser próprio, incluindo as 8 `require` de linha única) · **`json-iterator` arquivado** (`archived: true`, pushed 2024-05-27) · **as versões dígito a dígito** (x/mod v0.40.0 de 13/08, ristretto/v2 v2.4.2, gofeed v1.4.2) · **as duas linhas major de ristretto** e seus 2 importadores reais · **GO-2026-5932/6179/6180/6222 existem com as datas e faixas afirmadas**, e **GO-2026-4923 está `withdrawn`** — *a autocorreção do avaliador de faixa era verdadeira* · **licenças lidas no cache** (golang-lru/v2 e rapid = MPL-2.0, hnsw = CC0-1.0, mcp go-sdk em transição) · **os 5 `ignoreUntil = "2026-07-30"` expirados** · **Dependabot com 5 blocos para 7 módulos reais** · **`git rev-list --count origin/main..HEAD` = 2332**, origin em 2026-06-10 · **binário `+dirty`** · **SBOM com `timestamp 2026-07-02`, 171 componentes, e o set-diff dá exatamente as 13 ausentes** · **`goccy` issue #604 aberta em 2026-08-23**.

### E dois mandatos sem caso vivo

- **"Instalar o que já existe": nenhum caso nesta onda** — **a frente de vulnerabilidades inclusive se autocorrigiu**, registrando que o `govulncheck` já existe em `tools/sca`.
- **SaaS ou cadastro disfarçado: nenhum.** Todos os fixes são locais e auto-hospedados.

> **Síntese do crítico:** *"A onda é factualmente forte — toda afirmação de versão, CVE, licença e git que ataquei resistiu com fonte aberta por mim. O que cai é (a) dois instrumentos cegos, (b) um mecanismo mal descrito, (c) três fixes que violam contrato ou não compilam, e (d) dois falsos negativos meus por cima da onda."*

---

## 📋 REGISTRO DA EXECUÇÃO — o que a medição ao vivo confirmou, derrubou e achou de novo

> **Esta seção é escrita DURANTE a execução, pela regra G5:** *"divergência entre o plano
> e a medição da execução: vale a medição, e o plano é corrigido no repo, com o motivo —
> nunca defendido."* Cada entrada traz data, comando e camada.

### 2026-08-26 · T-1, G1, G2 — o plano entrou no repo e virou tasklist

- Plano em `docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md`, commit `2364681e`.
- Evidência das 8 ondas em `data/ops/agent_reports/onda_bots_20260826/`.
  **Achado da própria execução:** o plano mandava copiar **um** relatório avulso de agente;
  havia **24** em `~/.claude/plans/`, todos fora do repositório. Os 24 foram commitados.
- **95 tarefas** no frontboard, **derivadas do plano** por `tools/generate-frontboard-plano-bots`
  (commit `485779d9`). Grafo verificado: **zero ciclos, zero dependências órfãs**.

### 2026-08-26 · Antes de G2 — os dois leitores do frontboard estavam cegos

Achado ao ler quem consome o board antes de escrever nele (commit `cec68a2f`):

| Instrumento | Defeito medido | Efeito |
|---|---|---|
| `tools/p0-next` | filtrava `available`/`running`/`blocked`; o board usa `queued`/`in_progress`/… — **144 linhas, ZERO casadas** | o "dispatcher de autonomia" imprimia *"Nada AVAILABLE"* com **58 tarefas livres** e mandava o agente entrante PARAR |
| `tools/wiki-brief` | `TypeError` ao ordenar: `priority` mistura `int` e `str` (24 × 11 nas livres) | `2>/dev/null` engolia o traceback e imprimia `BOARD ?` — as linhas `ATIVA` e `LIVRE` **nunca apareciam** |

**O `wiki-brief` já documentava o defeito do `p0-next` em 5 linhas de comentário e pedia o
conserto por escrito, desde 2026-07-28.** Corrigido com leitor canônico
(`tools/frontboard.py`, no padrão de `edgetelemetry.py`), com teste sobre o board **real**.
As 144 linhas históricas **não** foram reescritas: o defeito era de leitura.

### 2026-08-26 11:41 · T0.1 — CONCLUÍDA, verificada em porta isolada antes de produção

| | Antes | Depois |
|---|---|---|
| `vcs.revision` do binário | `39f13d3602d1` **+dirty**, 18 commits atrás | **`485779d989c1` = HEAD** |
| `/rss.xml` no Go | **404** (`strings 'application/rss+xml'` = **0**) | **200** (strings = 2) |
| Título de `/diarios/index.md` | *"Conteúdos jurídicos de **Diarios**"* (sem acento) | *"Que municípios publicaram diário oficial, dia a dia"* |

**A ordem do advisor não era formalidade, e a medição a justificou:** `systemctl cat` confirma
`Restart=always`, `RestartSec=5`, `StartLimitIntervalSec=0`, e `publishedmanifest.Validate`
aborta fatal no boot — **restart contra estado incoerente seria loop infinito em produção**, e
o disco de hoje nunca havia passado por um boot. O boot em `127.0.0.1:8099` passou limpo antes
de qualquer toque na unit.

**O contra-teste de isolamento não é teatro:** a instância de verificação gerou **117 MB** no
próprio `WIKI_CACHE_DIR`. Sem ele, teria escrito por cima do cache de produção — o precedente
que já matou a busca do portal. `mtime` de `var/on-demand-cache` **idêntico** (1787252328).

**⚠ CORREÇÃO AO PLANO — T0.1 não deve usar `tools/deploy-publico`.** O plano o citava
(`:227`). Lido na execução: são **8 etapas**, e duas estão fora do escopo — a **0/7 faz
reingest do estoque** e a **6/7 PURGA A BORDA DA CLOUDFLARE**, zona que T1.1 ainda vai mexer
com corpo canônico. Foram extraídos build → swap → cache → restart.

**⚠ CORREÇÃO AO PLANO — o critério de T0.3 estava errado e o gate nasceria vermelho para
sempre.** `vcs.modified=true` é **permanente nesta máquina**: marca `true` com qualquer arquivo
rastreado modificado, e os timers reescrevem JSONL de `data/ops/` continuamente (91 arquivos
sujos no momento da medição, **1** deles Go). Um gate que reprove `vcs.modified` **nunca pode
passar** — é o R22. **Critério correto:** `vcs.revision` contém o último commit que tocou
`internal/`, `cmd/` ou `go.mod`.

**Achado colateral, medido e liberado:** `go.sum` tinha **+247 linhas não commitadas** (resíduo
da onda de dependências, mtime de hoje 10:16). **Todas** são hash de `go.mod`, **zero** de
conteúdo — nada novo entra no binário; `go mod verify` responde *all modules verified*.

### 2026-08-26 11:44 · T0.2 — remedição nas três camadas, e o que ela muda

Instrumento novo e reusável: **`tools/check-superficie-bots-live`** — 36 sondas × 3 camadas
(Go 8089 · nginx 8088 · borda), com `Content-Type` e tamanho (nunca só o status, armadilha A3),
e **`X-Warming-Request: true` embutido sem opção de desligar** por causa de M26. Resultado
gravado em `data/ops/superficie_bots_live.jsonl`.

**Confirmados AO VIVO (medição própria, não de agente):**

| Achado | Evidência desta execução |
|---|---|
| **O7 — injeção da borda** | `<script … .webmcp/bridge.js … data-packs="c2pa,mcp-server-client">` inserido **antes do `<link rel=canonical>`**, **exatamente +160 bytes** em `/`, `/consumidor/`, `/previdenciario/135-ou-agencia/` e `/sobre/` — e **zero** em rss/feed/sitemap/json. A injeção é **só em HTML** |
| **O9/T3.8 — `/sitemaps/`** | **200 no Go, 410 no nginx e na borda** — o handler correto existe e a requisição nunca chega nele |
| **A3 — negociação silenciosa** | `/familia/pagina/2/` com `Accept: text/markdown` → **200 `text/html`**, enquanto `/previdenciario/135-ou-agencia/` com o mesmo header → **200 `text/markdown`**. O defeito é **só na paginação** |
| **T8.1 — as 185 fatias** | `/familia/pagina/2/index.md` → **404 com 7.361 bytes de HTML** |
| **T3.5 — RFC 9728** | `/mcp/.well-known/oauth-protected-resource` → **404** |
| **M20 — 404 caro** | 7.361 B na origem, 7.521 B na borda |

**⚠ CORREÇÃO AO PLANO — O6 errou sobre o `llms.txt` de área.** O plano listava
*"os `/{area}/llms.txt` respondem 404 no Go e 200 pelo nginx"* como **consequência em cadeia do
binário defasado**. Medido depois do rebuild: **continua 404 no Go e 200 no nginx**, porque
`public/consumidor/llms.txt` **existe em disco**. É o desenho normal descrito em O23 (*"HTML =
nginx lendo disco; Markdown, busca, API = Go"*), **não um defeito**. Sai da lista de tarefas.

**Achado positivo que refina T3.3:** `/.well-known/agent.json` e `/.well-known/mcp` já devolvem
**160 bytes de JSON** em vez de HTML — o erro negociado **já existe** para essa família. O que
falta é estendê-lo às rotas que ainda servem 7.361 B de HTML a cliente-máquina.

### 2026-08-26 11:52 · 🔴 T0.4 ESTAVA INVERTIDA — regenerar o nginx quebraria 278 páginas

**É a quinta correção perigosa apanhada antes de aplicar, e a primeira achada pela execução
e não pela crítica.** O plano manda, em T0.4 e em O24/D-1: *"editar sempre `ops/nginx/wikijuridica.conf`
(fonte única) e regenerar com `tools/generate-nginx-standalone`. Nunca editar o `standalone/`."*
**Medido, gerando o dedicado para um arquivo temporário e comparando:**

| Verificação | Resultado |
|---|---|
| Áreas nos maps de roteamento do que **RODA** | **32** |
| Áreas no que o gerador **produziria** | **29** |
| **Perdidas ao regenerar** | **`diarios`, `jurisprudencia`, `noticias`** — **278 páginas publicadas** (8 + 250 + 20) |
| Bloco de feeds `application/atom+xml` | **6 ocorrências no que roda, 1 no vhost** — o `location` exato que corrige o tipo de `/feed.xml` e `/rss.xml` sumiria |
| Diretivas que decidem resposta | **vivo 67 · dedicado 76** — *o dedicado está À FRENTE, não atrás* |
| O defeito que T0.4 alega (`Vary` ausente com brotli) | **NÃO está vivo**: `/api.md`, `/…/index.md` e `/.well-known/agent-skills/index.json` servem `Content-Encoding: br` **com** `Vary: Accept-Encoding` |

**A causa do mal-entendido:** `check-nginx-standalone-parity` compara **uma direção só**
(vhost → dedicado). Quando o dedicado ganha algo que o vhost não tem, ele não acusa — e o
relatório *"1 diretiva do vhost ausente no dedicado"* faz parecer que o dedicado é que está
atrasado. **O sentido inverso, que é o perigoso, é invisível para o gate.**

**✅ ORDEM CORRIGIDA para T0.4 — a inversa da que estava escrita:**
1. **NÃO regenerar.** O `standalone/nginx.conf` é hoje o artefato mais correto dos dois.
2. **Portar do dedicado para o vhost** o que só existe no dedicado (as 3 áreas nos dois maps e
   o bloco de feeds), para que a *fonte* volte a merecer o nome.
3. **Estender o gate** a comparar **os dois sentidos**, senão a próxima sessão repete isto.
4. **Só então** o gerador volta a ser seguro, e a diretiva `more_set_headers 'Vary: Accept-Encoding'`
   entra pelo caminho normal.

**Precedente que isto reforça:** o plano inteiro foi construído sobre a premissa de que o
`standalone/` é derivado e descartável. **Ele não é** — alguém o editou à mão contra o aviso do
cabeçalho, e o resultado é que hoje ele é o mais completo. Tratar o rótulo *"GERADO … NÃO EDITE
À MÃO"* como verdade, sem conferir, é a mesma classe do comentário que mente.

### 2026-08-26 12:20 · Crítica Fable sobre T0.4 — a forma forte cai, a causa-raiz é outra

**DERRUBADO da minha conclusão:** *"regenerar destruiria o roteamento de 278 páginas"* **é
forte demais.** Regenerar **não produz nenhum 404**: o acervo sai de `location /` + `try_files`
do disco, e os artigos das 3 áreas são de **dois segmentos**, casando a regra genérica
`wj_rota` (`nginx.conf:330`) — mantêm gêmea Markdown e `Link` independentemente da lista de
áreas. **Nenhuma página sairia do ar.**

**O dano real de regenerar, que continua grave e é maior em alcance:**

| # | Regressão | Alcance |
|---|---|---|
| a | `Cache-Tag` por área some nas 3 áreas → **a purga seletiva da borda não as alcança** | correção de texto não chega ao leitor — a classe de bug que `59bc7add` pagou |
| b | Os **3 hubs** perdem negociação Markdown e `Link: rel=alternate` | canal de agente |
| c | `/feed.xml` e `/rss.xml` **regridem para `text/xml`** (hoje servem `application/atom+xml`) | agregadores |
| d | `@fallback` perde `gzip_vary off` + `-s '200 304'` | **TODAS as rotas do Go**, não só 278 |

**E a minha lista de porte estava incompleta:** o diff fecha em **TRÊS deltas** (74 linhas =
carimbo + 2 maps + 49 de feeds + **19 do hunk do `Vary` em `@fallback`**). Portar só os dois
que eu listei e regenerar **ainda reverteria o fix do `Vary`** — e o gate reprovaria na mesma
diretiva de hoje.

**CAUSA-RAIZ REAL, e não é a que eu escrevi:** a hipótese *"o gerador deriva de dado
desatualizado"* está **refutada** — `tools/generate-nginx-standalone:82` embute o vhost
**verbatim**, só trocando `listen`. A causa é **colisão de fonte-de-verdade**:

- `internal/contract/public/nginx_agent_surface_test.go:21-25` e `nginx_bot_policy_drift_test.go:33`
  declaram o **STANDALONE** canônico — literalmente *"um guarda que continue lendo o arquivo
  velho protege um fantasma"*;
- o gerador, o `check-nginx-standalone-parity` e os cabeçalhos declaram o **VHOST**.

Os 3 commits de 2026-08-20 (`59bc7add`, `3bd86cb7`, `4a3217eb`) editaram **só o standalone** —
coerentes com o lado dos testes, violando o *"NÃO EDITE À MÃO"* do próprio arquivo. **O gate
unidirecional explica por que ninguém viu, não por que aconteceu.**

**Furos na ordem que eu propus, todos aceitos:**
1. *Não regenerar* — correto, **e mais afiado**: `--saida` **default É produção**, `nginx -t`
   **aprova o gerado** (medido, exit 0), e depois da regressão o `check-nginx-standalone-parity`
   ficaria **VERDE certificando o estrago**.
2. *Portar* — falta o 3º delta, **e decidir qual arquivo é canônico é pré-requisito**, porque
   todos os testes de contrato Go leem o standalone.
3. *Gate bidirecional* — **quebraria duas vezes**: extras legítimos do wrapper (`load_module`,
   `events`, temp paths) dariam vermelho permanente; e o parser só compara linhas cujo primeiro
   token está em `DECIDEM_RESPOSTA` (`parity:62`), então **corpo de `map` é invisível nos DOIS
   sentidos** — nem bidirecional pegaria o drift 32×29. **O gate certo é outro:**
   regenerar-para-temporário + **diff módulo carimbo == vazio**.
4. *Regenerar por fim* — sem critério de aceite. O correto: **gerado ≡ produção exceto a linha
   do carimbo (diff == 1 linha)**.

**Residual apanhado:** o symlink `/etc/nginx/sites-enabled/wikijuridica → wikijuridica.conf`
ainda existe. Dormente (`nginx.service` inactive+disabled), **mas editar o vhost muda o que um
nginx do sistema ressuscitado serviria — na mesma porta 8088.**

**Duas correções ao meu método, que valem por si:** (a) a frase *"o vhost vivo, fonte única de
verdade"* **não é autodeclaração do vhost** — mora no cabeçalho do standalone e no gerador; o
cabeçalho do próprio vhost ainda descreve o modelo aposentado (*"instalar via symlink em
sites-enabled"*); (b) meu grep `"path": "/` (com espaço) **devolve 0** no manifesto real — os
números 8/250/20 estão certos, o método citado é **irreprodutível** (R3).

**O que ele tentou derrubar e não conseguiu:** a direção (o dedicado está à frente — 3 commits
só nele, ambos limpos no git, produção == committed); *"feeds sob outra forma no vhost"* (o
único `atom+xml` do vhost é `gzip_types`); *"o `Vary` vem de `gzip_vary`"* (`gzip_vary off` nas
locations envolvidas — vem de `more_set_headers`, e o 304 o carrega); e *"editado à mão com
algo ERRADO"* — **nada errado no conteúdo: os 3 deltas são commitados, comentados, funcionais
e medidos no ar. O erro é de processo, não de conteúdo.**

### 2026-08-26 12:35 · T6.2 + T0.6 — os três geradores corrigidos e as 50 páginas com lastro

**A perda era o DOBRO do que o plano media, porque a guarda cobria metade.**
`check-shard-preservation` protegia só `v2_pages`; o mesmo `os.WriteFile` do mesmo gerador
truncou também o **portfólio**, e isso era invisível:

| Shard | disco | HEAD |
|---|---|---|
| `v2_pages/stf-informativo-derivado-01.jsonl` | 4 | **50** |
| `portfolio_v2/jurisprudencia-stf-derivada-01.jsonl` | 4 | **50** |

**Medido:** **50 páginas `/jurisprudencia/stf-*/` publicadas e no ar sem linha em shard nenhum.**
A prova estava impressa e ninguém leu — o próprio `check-v2-portfolio-pairing` imprimia
*"10402 já COMMITADOS, 10367 no estado atual"*, e a diferença de 35 é **−50 do STF +15 novas**.

**Ordem segura cumprida:** preservar (50 HTMLs em `.agents/runtime/preservado-20260826-stf-orfas/`,
1,3 MB) → corrigir os **três** geradores (`stf-informativo`, `stj-tema`, `stj-sumula`) com o
padrão *read-all* do gerador irmão que nunca perdeu página → estender a guarda ao portfólio
(passou a acusar **100** em vez de 50) → recuperar **por escrita para frente do gerador
corrigido**, nunca por `git checkout`.

**Resultado:** 4 → **54** nos dois shards · `check-shard-preservation` **OK em 944 shards** ·
**páginas publicadas sem shard: 50 → 0**.

**Bug separado, achado por `go vet` e corrigido junto:** `generate-stj-tema-pages:628` passava
`referencia` **duas vezes** para uma string com **um** `%s`, e o Go anexa o excedente — a
resposta do FAQ terminava em `"...se o Tema 4 se aplica.%!(EXTRA string=Tema 4)"`. **200 de 200
registros** de `stj-tema-derivado-01.jsonl` carregam a marca, e **os 200 estão publicados**.
**NÃO chegou ao leitor** — zero ocorrências no HTML e no Markdown servidos, porque esse FAQ não
é o que o publicador emite hoje. **Era bomba armada**, e `go vet` acusava sem que ninguém
rodasse vet sobre `cmd/`.

### 2026-08-26 12:55 · ❌ T0.7 DERRUBADA — o `noindex` contrariaria política escrita do repo

**A premissa não reproduziu, e a correção prescrita seria pior que o estado atual.**

O plano manda pôr `noindex` nas 28 rotas `/{area}/pagina/`, com base em O32.f, que afirmava
*"o corpo NÃO é idêntico (sha `6e394f6a…` × `70ac0fd7…`)"*. **Medido depois do rebuild de T0.1:**

| Verificação | Resultado |
|---|---|
| Corpos idênticos ao hub | **28 de 28** (md5 conferido rota a rota) |
| Canonical apontando para o próprio hub | **28 de 28** |
| No sitemap | **zero** — `grep '/pagina/</loc>'` em todos os shards = 0 |
| Requisições de bot no período | **~25** contra **649** das `/pagina/N/` que estão no sitemap |
| `index.html` em disco sob `*/pagina/` | **zero** |

**Atribuição da divergência com O32.f, fechada:** não existe `public/{area}/pagina/index.html`
— **as 28 caem no `@fallback`/Go**. O `sha` diferente que O32.f mediu veio do **binário velho**,
e o rebuild de T0.1 igualou os corpos. É a armadilha **A4**, e a própria varredura de órfãs de
T0.6 prova por outro caminho: se esses arquivos existissem em disco, ela teria achado **28
órfãs a mais** — achou 4.

**Por que NÃO aplicar o `noindex`, e o fundamento é do próprio repositório:** a emenda de
2026-08-07 do `CLAUDE.md` decide exatamente esta classe — variante que serve **o mesmo corpo**
recebe **canonical para a URL limpa e fica SEM `noindex`**, porque *"o canonical é o mecanismo
correto para variante, e o `noindex` ali destrói o valor do link em vez de consolidá-lo"*.

**E a assimetria de risco é grande:** `noindex` numa página que canonicaliza para o hub é
**sinal conflitante** — a documentação de canonicalização trata `noindex` como remoção, não
consolidação, e o risco conhecido é o sinal ser atribuído ao **cluster canônico**, isto é, aos
**hubs**, por onde 85% dos artigos são alcançados, num momento em que as impressões já caíram
90%. De um lado, arriscar as páginas mais valiosas do portal; do outro, um custo medido de
~25 requisições no período. **O status quo está correto e a tarefa não se executa.**

*(Registrado pelo mesmo padrão de T0.3.c, e pela regra G5 do plano aprovado: divergência entre
plano e medição vale a medição, e o plano é corrigido — nunca defendido.)*

---

### 2026-08-26 14:18 · 🔴 T2.6 armou uma bomba que eu mesmo não vi, e o red-team viu

A pré-compressão brotli de hoje cedo (10.370 arquivos) ligou o gerador **somente** em
`tools/deploy-publico`. A onda diária roda 04:23 e reescreve `index.html`, `feed.xml`,
`rss.xml` e os sitemaps **sem tocar nas gêmeas `.br`** — e `brotli_static on` serve
`$uri.br` sem comparar frescor com o fonte.

**E não era só de amanhã: dois arquivos já estavam stale**, `/llms.txt.br` e
`/noticias/llms.txt.br` — o `llms.txt` é o mapa que os agentes de IA leem. Medido no
access log, **a Cloudflare puxa a origem já comprimida** (os fetches batem byte a byte
com o `stat` dos `.br`), então o corpo velho não pararia num cliente: entraria no cache
de borda e seria distribuído a todos, enquanto o IndexNow anunciava as mesmas URLs como
recém-atualizadas.

**Corrigido em `f261f1d2`:** poda **antes** de comprimir (interrupção deixa ausência, que
o nginx resolve em q5, nunca conteúdo velho), etapa 8.5/9 entre publicação e IndexNow, e
o gate `check-brotli-static-fresco` com contra-teste nos dois sentidos. A poda também
apanha `.br` **órfão**, que com `brotli_static` **ressuscita página retirada do ar** —
furo na coerência de artefato por um caminho que nenhuma auditoria de `public/*.html` vê.

### 2026-08-26 14:25 · T3.3 corrigiu o erro negociado e abriu envenenamento de cache

A negociação de erro por `Accept`, feita hoje, deu à mesma URL três respostas possíveis —
**e a função não declarava `Vary`**. Medido pelo red-team, determinístico: pedir uma rota
inexistente com `Accept: text/markdown` fazia o navegador seguinte receber `text/markdown`
em HIT na borda. Corrigido em `be4a6cf4`, com o header **nos dois ramos**: o balde
envenenado costuma ser o do HTML, que é o default e chega primeiro.

### 2026-08-26 14:47 · T6.6 reaberta — corrigir o produtor não conserta o estoque

A base legal foi corrigida no coletor às 13:53. Às 14:30 medi o estoque: **1.174 de 1.174
registros já coletados** seguiam com `art. 46, VIII`, e o gerador lê a licença **do dado**.
Zero havia chegado a página publicada — a correção pegou antes do dano.

Corrigido por `tools/generate-noticias-licenca-corrigida` (`bb185ba8`), que **lê a tabela
do próprio coletor** em vez de duplicá-la, e falha alto se o literal Go mudar de forma.
Contra-testes: 1.174→0 ocorrências, contagem preservada, e **o único campo que difere no
diff é `licenca`**.

**Achado colateral da mesma família:** o campo `natureza` estava em 100% dos registros e o
struct do gerador **não o declarava** — descartado no `Unmarshal`, exatamente como o
publicador perdia `publication_date` (T6.4). Ganhou campo **e guarda**: registro sem
licença ou sem natureza não vira página (`52d7364c`).

### 2026-08-26 14:55 · T6.8 — o molde cai 34%, e o oráculo NÃO foi atingido

Medido no shard commitado, por 8-gramas sobre corpo+FAQ: maior bloco literal **161
palavras, mediana 149**. Depois: **107 e 100** (−34% e −33%). O oráculo que fixei antes de
escrever — nenhum bloco ≥ 40 palavras — **não foi alcançado**, e isso fica dito.

**Quatro tentativas, e as três primeiras ensinaram a quarta:** variar por presença de sinal
**piorou** (245 palavras — cinco sinais dão 15 perfis para 54 páginas, e eu tinha medido
esses 15 perfis antes de escrever a solução que os ignorava); contagem deu 202; colegiados
nomeados, 119; **limitar a dois cuidados por página, 107** — porque a causa não era só
variedade, era **comprimento**: eu havia escrito 200 palavras onde o original tinha 93.

**A prescrição do plano não se aplicava:** ela mandava derivar de `categorias`,
`temas_citados` e `sumulas_citadas`, que aparecem em **6,0%, 1,2% e 0%** dos 1.174
registros. A derivação teve de vir do título.

**Onde o molde resiste, dito por extenso:** nas páginas de TST e CJF, cujos títulos não
carregam sinal nenhum — fechar exige material que o título não dá, o que é trabalho de
coleta, não de redação.

### 2026-08-26 15:05 · 🔴 T6.7 DERRUBADA pelo red-team — a tese vestiu clareza de risco jurídico

O plano afirmava risco jurídico real em declarar CC BY 4.0 nas 20 páginas com manchetes de
tribunais. **Três camadas independentes derrubam, e conferi as três:** a CC BY §1(h) limita
os direitos licenciados aos que o licenciante **tem autoridade para licenciar**, e a §5
nega garantia de não-infração; o art. 8º, VI diz que **título isolado não é objeto de
proteção**; e o JSON-LD **já separa** — `license` no `NewsArticle` (sem `articleBody`,
campos 100% autorais) e as matérias em `citation[]` **sem** license.

**A premissa fática errou a ordem de grandeza.** Medi: **350 páginas** têm citação literal
de terceiro, não 20 — jurisprudência 250, súmulas 80, notícias 20, diários 0. Severidade
invertida: as 330 primeiras citam ato oficial (inciso IV, já coberto).

**E a correção proposta desfaria a DEC-031**, deixando as páginas de notícias como as únicas
sem licença legível por máquina — justamente as mais orientadas a citação por IA —, ao custo
de republicar **10.071 páginas**.

Aplicado apenas o que sobreviveu: o `scope_excludes` passa a nomear o inciso VI, e o teste
passa a **exigir** `"art. 8º, VI"` e `"título"` na string — sem isso a extensão regrediria
em silêncio, porque o `Contains` anterior passava sem eles.

### 2026-08-26 15:10 · Reconciliação do frontboard — ele estava mentindo sobre 32 tarefas

As Fases 5, 7 e 9 apareciam como **0 resolvidas** enquanto os agentes já haviam concluído e
commitado. Conferi os oito hashes que eles alegaram (todos existem) e registrei estado,
medição e evidência tarefa a tarefa. **37 → 51 de 95 resolvidas.** Frontboard que não
reflete o disco é a mesma classe do comentário que mente.

### 2026-08-26 · Defeito de concorrência achado no gate, registrado e NÃO corrigido às pressas

`tools/check-go-index-compile-closure` adquire o lock exclusivo do workspace (`:2552`)
**antes** de avaliar se há impacto de build (`:2589`, `no_staged_build_impact`). Consequência
medida três vezes hoje: commit de conteúdo puro — que o `CLAUDE.md` declara **leve e
concorrente** — é reprovado por build Go de outro agente, com *"lock concorrente; fail-fast,
sem espera"*.

**Não corrigido nesta sessão, e o motivo é dito:** mover a avaliação para antes do lock
mexe no código que valida owner/mode/nlink do próprio lock, com cinco frentes commitando ao
mesmo tempo. Contornado com `flock` e retry curto. Fica como task.


### 2026-08-26 16:21 · 🚀 DEPLOY — o binário no ar passou a corresponder ao HEAD

**Doze commits de servidor estavam só no fonte.** Build isolado para
`bin/wikijuridica-server.next`, verificado em `127.0.0.1:8099` com `WIKI_CACHE_DIR`
próprio — o cache de produção ficou **intocado** (mtime idêntico antes e depois,
que é o contra-teste do precedente `[[instancia-auditoria-cachedir]]`, onde porta
diferente não isolou disco e a busca morreu respondendo 200). Só então a troca
atômica e o restart.

`check-binario-vs-fonte` ficou **verde pela primeira vez no dia**.

Medido nas três camadas depois: `/changes.json` e `/api/v1/novidades` de **404 para
200**, `Vary: Accept` no erro negociado, RFC 9728 respondendo. Perguntar "mudou
algo?" custava 1.385.860 B em 35 requisições; passa a custar 1 requisição e 0 B de
corpo.

**`vcs.modified=true` é ruído nesta máquina, não código sujo:** os timers reescrevem
JSONL em `data/ops` continuamente, e por isso o gate não reprova por esse campo —
ele reprova por commit de código posterior ao `vcs.revision`.

### 2026-08-26 16:45 · 🔴 O `if_modified_since before` NÃO ALCANÇA QUEM PASSA PELA BORDA

Correção de uma alegação minha de hoje cedo. Ligar `before` no nginx foi registrado
como ganho de revalidação. Medido agora com `If-Modified-Since` **posterior** ao
`Last-Modified`, nas três camadas:

    Go     127.0.0.1:8089   304, 0 B
    nginx  127.0.0.1:8088   304, 0 B
    borda  wikijuridica     200, 22.488 B   (cf-cache-status: HIT, age 12912)

A borda serve do cache dela e aplica a própria comparação, **sem consultar a
origem**. O ganho real é menor do que registrei.

Pelo mesmo mecanismo, **o risco que o red-team levantou contra essa mudança também
não se materializa**: "304 para página que mudou depois do carimbo" exigiria que a
requisição condicional chegasse à origem, e ela não chega.

**O caminho barato que DE FATO funciona é o ETag:** `If-None-Match` pela borda
devolve **304 com 0 B**, medido em 2 de 2 rotas. E é o que o Google recomenda. O
ETag volta a atravessar a borda — enfraquecido para `W/` pela recompressão, o que
não impede a revalidação.

### 2026-08-26 16:45 · T3.1 superada por mudança de estado que ninguém registrou

A injeção de 47.616 B de `bridge.js` que existia às 13:07 **não existe mais**: zero
scripts na origem e na borda, em 3 rotas. Provavelmente um beta da Cloudflare
desligado. **Não declaro resolvido** — se for intermitente, volta. Quem vigia é o
gate `check-edge-html-injection`.

### 2026-08-26 · O GARGALO AGORA É A REPUBLICAÇÃO, e ele é comum a cinco tarefas

Um padrão ficou visível ao medir a superfície ao vivo: **várias correções de hoje
estão no código e não no ar**, todas presas à mesma publicação —

    T8.1  185 fatias sem `rel=alternate` para o Markdown do hub (gate: 185 mudas)
    T8.2  og:image ausente nos 10.298 HTMLs do acervo
    T6.5  meta description com contagem colada em 20 de 20 páginas de notícia
    T5.x  front matter, `anchor_claim` e JSON-LD enriquecidos

O gate de cada uma fica **vermelho por desenho** até a republicação, e isso é o
comportamento certo: gate que ignora o defeito conhecido para ficar verde é o gate
verde sobre mundo errado que este plano já catalogou cinco vezes.

**Por que não republicar já:** o ensaio completo mostra `HTML escrito: 10070
REESCRITAS` e `hubs: 217 REESCRITAS`, e três frentes ainda editavam
`internal/structureddata`, `internal/render` e `internal/pagemarkdown` — publicar
no meio congelaria um estado intermediário. A ordem é: frentes fecham → ensaio →
leitura de amostra real do conteúdo → crítica adversarial → publicação.

### 2026-08-26 16:45 · Monitor pós-deploy instalado, e ele tem o direito de não concluir

`tools/generate-deploy-marco` gravou o eixo da comparação (31 agentes congelados,
21 valiosos) com o commit lido do BINÁRIO em execução, não do `git HEAD` — confundir
os dois é a armadilha A4.

`tools/check-efeito-deploy-bots` compara as janelas pela régua de RETORNO, não de
cobertura: cobertura acumulada só cresce e por isso **nunca acusa abandono**, que foi
como o GPTBot caiu para 1 requisição/dia sem ninguém ver. Timer diário às 09:15,
instalado e ativo.

**Hoje ele diz "CEDO DEMAIS", e isso é o desenho:** com menos de 3 dias não emite
tendência. Passados 7 dias sem nenhum bot valioso voltando, avisa pelo canal do
dono com severidade alta e nomeia o próximo eixo (frescor); aparecendo o efeito,
**resolve a chave** — alerta que nunca é resolvido vira as 25 chaves abertas que
este repositório acumulou.

### 2026-08-26 · Uma armadilha de máquina que custou 12 minutos de CPU

`./tools/go-modern run ./cmd/check` **sem argumento não lista os checks: ele executa
todos**, inclusive `gosec` sobre o módulo inteiro. Usei isso para descobrir o nome de
um check e abri **45 processos, load 52 em 8 núcleos**. O dono viu a máquina travando
e perguntou o que estava pendurado — era meu, não dos agentes. Para descobrir um
nome, lê-se a fonte.


## PLANO DE EXECUÇÃO — ordenado por dependência, não por severidade

**Por que a ordem é esta:** a auditoria mostrou que vários "defeitos" são o **mesmo evento** visto de ângulos diferentes, e que corrigir na ordem errada transforma correção em regressão (o caso do `if_modified_since`). A ordem abaixo respeita as dependências medidas. **Cada tarefa traz: o que fazer · onde · como verificar · o que NÃO fazer.**

**Regra que atravessa todas:** nenhuma correção acrescenta literal ao código (R13). Onde a derivação não cobrir um caso, **o caso reprova em gate**, nunca cai em fallback silencioso.

---

### FASE 0 — Reconciliar o que está no ar com o que está no fonte

> **Sem isto, toda medição de produção deste plano descreve um binário de 20/08, e várias tarefas seguintes seriam trabalho em cima de um estado que não existe mais.**

### T-1 — Antes de tudo: gravar este plano dentro do repositório

Copiar este arquivo para **`/opt/wiki/docs/goal/PLANO_SUPERFICIE_BOTS_20260826.md`**, com ponteiro em `docs/goal/CHECKPOINT_DIGEST.md` e registro em `docs/goal/MAESTRO_CODEX_LOG.md`, e **commitar na mesma sessão**. Hoje ele vive em `/home/rafael/.claude/plans/`, fora do versionamento. Ordem do dono de 2026-07-29: o que custou trabalho e dinheiro nasce no repo.

**Junto:** copiar para `data/ops/agent_reports/onda_bots_20260826/` os **`journal.jsonl` das OITO ondas** *(corrigido: eu havia escrito "cinco", e quem executasse ao pé da letra perderia três)*, mais o **relatório avulso do agente de frescor** e os **resultados persistidos** — **nenhum dado de agente fica só em diretório volátil de sessão.**

---

**T0.1 — Rebuild + restart + reload de config editorial.** Uma ação só, não três (O24/F-4).
- **Onde — usar o caminho sancionado que já existe**, `tools/deploy-publico:227`, que builda para `bin/wikijuridica-server.next` e só então troca:
  `nice -n 10 ./tools/go-modern build -o bin/wikijuridica-server.next ./cmd/server` → troca atômica → `systemctl restart wikijuridica-server` → `./tools/reload-wiki-server`.
  *(Corrigido: eu havia escrito `go-modern build ./cmd/...`, que compila mas **não instala** o binário. E `nice -n 10` é exigência do CLAUDE.md em janela com agentes ativos.)*
- **Verificar:** `GET /rss.xml` no `127.0.0.1:8089` passa de 404 para 200 · `/diarios/index.md` passa a servir *"Que municípios publicaram diário oficial, dia a dia"* em vez de *"Conteúdos jurídicos de Diarios"* · `strings bin/wikijuridica-server | grep -c 'application/rss+xml'` ≥ 1.
- **Não fazer:** não aplicar nenhuma outra correção Go antes disto — elas não estariam no ar de qualquer forma.

**T0.2 — REMEDIR os defeitos de produção depois do restart.** Vários podem evaporar.
- **Onde:** repetir as sondas de M2 (Markdown por família de rota), M7 (rotas que erram), O9 (`/sitemaps/`, `/a2a/v1`, `/api/v1/relatos`), O14 (`relatar_defeito` sem token).
- **Entregável:** uma tabela "antes × depois" no arquivo do plano dentro do repo. **O que sumiu, sai da lista de tarefas.**

**T0.3 — Gate `check-binario-vs-fonte`.** Read-only; compara o hash/mtime do binário em execução com o último commit que tocou `internal/` ou `cmd/` e reprova se houver commit posterior. Mesma classe de `check-arquitetura-fiel`.
- **Ressalva de O24/F-2:** este gate só vale se o canal de alerta for consumido. Ver T1.4.

**T0.3.b — Dois arquivos de config nginx são órfãos, e um deles governa bots.** Medido por mim:

| Arquivo | Bytes | Carregado? |
|---|---|---|
| `ops/nginx/wikijuridica.conf` | 64.656 | **fonte única de verdade** (vhost vivo, gera o dedicado) |
| `ops/nginx/standalone/nginx.conf` | 72.840 | **é o que roda** (gerado) |
| `ops/nginx/security-headers.conf` | 4.791 | ✅ carregado por `include` |
| **`ops/nginx/standalone/bot-policy.conf`** | 5.017 | ❌ **nenhum `include` o carrega** |
| **`ops/nginx/standalone/server.conf`** | 11.629 | ❌ **nenhum `include` o carrega** |

**Editar `bot-policy.conf` não muda nada em produção, e nada avisa.** Um arquivo com esse nome é exatamente onde uma sessão futura iria mexer para ajustar política de bot — e o ajuste sumiria em silêncio. **Correção:** ou os arquivos são incluídos, ou saem do caminho, ou ganham um cabeçalho gerado dizendo que são inertes — mais um gate que reprove `.conf` sob `ops/nginx/` sem `include` correspondente.

**T0.3.c — Comentário que mente no próprio `CLAUDE.md`.** Ele descreve `./tools/check-http-smoke` como *"smoke HTTP: robots, sitemap, HTML sem runtime cliente"*. Medido: `grep -c robots tools/check-http-smoke` = **0**, e o script não referencia nenhuma rota literal. **O contrato do repo documenta uma cobertura que o script não tem** — corrigir o texto **e** dar ao smoke a cobertura que ele diz ter. *(Reforça a ordem do dono: não confiar em comentário; comentário que mente é bug.)*

**T0.4 — Resolver a paridade do nginx ANTES de qualquer edição de nginx.**
- **Estado atual medido:** `check-nginx-standalone-parity` = **FAIL** — `more_set_headers 'Vary: Accept-Encoding'` existe no vhost vivo e falta no dedicado.
- **E há mais atrás disso (O32.a):** o commit `f8a25fd9` de 2026-08-20 (*"o A2A ganha a capacidade de relato, e três referências deixam de ser falsas"*, **+29 linhas**) editou o vhost e **nunca chegou ao ar**, porque o gerador não rodou. **Ao regenerar, essas 29 linhas embarcam junto** — o diff precisa ser lido e aprovado, não sofrido como efeito colateral.
- **Onde:** editar sempre `ops/nginx/wikijuridica.conf` (fonte única) e regenerar com `tools/generate-nginx-standalone`. **Nunca editar o `standalone/`.**
- **Verificar:** `check-nginx-standalone-parity` exit 0 · `nginx -t` verde · o diff embarcado é conhecido e intencional.

**T0.5 — Gate `nginx-config-alcancavel`.** Lê o `ExecStart` da unit para achar o `-c` real, roda `nginx -T` sobre ele, coleta o conjunto **alcançado**, enumera `find ops/nginx -name '*.conf'` e **reprova todo arquivo não alcançado**. Fecha os órfãos de T0.3.b **e** impede que uma correção commitada fique fora do ar de novo. **Corrige também o comentário de `check-ingress-security-headers:206`, que chama de "arquivo vivo" o que produção não carrega.**

**T0.6 — Página órfã indexável: `/diarios/ms-20260819/`.** Serve **200 com 24.232 bytes** e `index,follow,max-snippet:-1`, **sem entrada no sitemap nem no `published_manifest`**. Medi o universo: das 10.298 rotas com `index.html`, **4 estão fora dos dois, e 3 são `noindex` legítimo** — **exatamente uma é o defeito**.
- **⚠ E não é uma órfã: são 51.** As 50 páginas `/jurisprudencia/stf-*/` (O38) estão no ar **sem linha em nenhum shard** — **o HTML público é hoje a ÚNICA cópia delas**.
- **🔴 PASSO ZERO, obrigatório (O42):** **copiar os 50 `index.html` para `.agents/runtime/` com data, ANTES de qualquer correção** — *"porque são a única cópia"*. **É a regra de que página escrita nunca é descartada, aplicada ao único lugar onde o texto ainda existe.**
- **Depois:** **gerador datado de RE-INGESTÃO**, que reconstrói as linhas do shard **a partir do HTML público + o registro bruto em `data/research/`**. **Não é reescrever: é recuperar.**
- **Correção da órfã de MS:** dar registro à página **ou** tirá-la do ar (a decisão vem do conteúdo dela: se é página de diário válida, entra no manifesto por gerador datado).
- **Correção de raiz:** `publishedmanifest.Validate` hoje cobre manifesto → `public/`; **passa a cobrir também `public/` → manifesto**, senão o próximo órfão indexável entra pelo mesmo buraco. **A coerência de artefato é declarada inegociável no `CLAUDE.md` e está furada num sentido.**

**T0.7 — As 28 rotas `/{area}/pagina/` saem com `noindex` hoje.** Servem **200** com conteúdo de hub **quase duplicado** (sha diferente do hub) e declaram `index` com canonical para o hub — **28 quase-duplicatas indexáveis**. Enquanto não tiverem índice próprio (raiz em `cmd/publish-v2-direct`), `noindex` é a resposta correta e imediata.

**T0.8 — Parar de contaminar a própria métrica.** Confirmado nesta sessão: **as sondas de auditoria (minhas e as dos agentes) entraram em `organic_requests`** porque saíram com UA próprio **sem** `X-Warming-Request`. E o campo declara `basis: exact_raw_minus_warming_ledger` estando **inflado de 16,1% a 31,9%**.
- **Correção:** promover `edge_cache_warm.jsonl` a **ledger de tráfego próprio**, onde toda ferramenta interna que sai para a borda grava — incluindo sondas de auditoria. **O log já tem o campo `warm=$http_x_warming_request` que classifica categoricamente.**
- **Consequência para este plano:** **a métrica `organic_requests` de 2026-08-26 está contaminada por esta auditoria e não serve de linha de base.**

**T0.9 — [PRÉ-REQUISITO DE TODOS OS GATES] Consertar o canal de alerta. É a antiga T1.4, promovida para cá — e a promoção é POSICIONAL, não só lógica.**
*(O43 declarou a promoção e ela não tinha sido materializada: a Fase 0 terminava em T0.8 e a tarefa seguia listada na Fase 1. Quem gerasse o frontboard a partir da sequência do plano ordenaria os gates ANTES do canal que os torna legíveis — exatamente a inversão que a regra proíbe. **O conteúdo executável integral continua escrito no bloco T1.4 da Fase 1, que passa a ser o DETALHE desta tarefa; a EXECUÇÃO acontece aqui, na Fase 0.** Nada foi movido de lugar no texto para não perder o banner com a contagem dos gates.)*
- **O que fazer, em resumo:** corrigir o cooldown do alerta ruidoso que afoga os críticos · **escalar** alerta crítico não resolvido após N repetições · corrigir as ferramentas que **saem com exit 0 relatando fracasso**.
- **Critério verificável de "feita":** existe um **consumidor** de `owner_alerts.jsonl` que lê, age e marca `resolvido` — hoje os únicos que tocam o arquivo são `tools/notify-owner` e a unit de alerta, **os dois PRODUTORES**. **Enquanto o grep de consumidores devolver só produtores, T0.9 não está feita.**
- **Única exceção declarada:** `check-binario-vs-fonte` (T0.3) e `nginx-config-alcancavel` (T0.5) **podem nascer antes**, porque são gates de **pré-condição da própria execução** — reprovam antes de qualquer trabalho começar e não dependem de canal de alerta para serem lidos. **Os outros 14+ esperam.**

---

### FASE 1 — Devolver o portal ao estado operável

> ### 🔴 T1.1 FOI CORRIGIDA — não é um PUT direto (ver O42.a e O42.b)
>
> **O audit log da conta prova que o esvaziamento veio do PAINEL, pela conta do dono** (v9-v14 com `interface: "UI"`, `actor=user`). **E o `ops/cloudflare/README-waf.md` — que este plano não citava — registra o precedente:** *"religar sem saber por que foi desligada pode reabrir o mesmo problema"*.
>
> **✅ Passo 0 RESOLVIDO — o dono autorizou nesta sessão:** *"Pode colocar no plano, que pode consertar o lado da Cloudflare, tem as credenciais."* **A pergunta que a frente exigia está respondida e a autorização é explícita.** Não há mais pergunta pendente ao dono em todo o plano.
>
> **O que a autorização NÃO dispensa**, e continua valendo como cuidado técnico: **ler `ops/cloudflare/README-waf.md` antes** — ele registra que *"religar sem saber por que foi desligada pode reabrir o mesmo problema"*, e o audit log mostra que **a mudança veio do painel, junto de `dev_mode` ligado/desligado, `cache_level` mudado 4×, `tiered_caching` desligado e religado, e 10 `purge_everything`**. **Restaurar sem entender esse conjunto é religar uma peça de um quadro que mudou inteiro.**
>
> **E a autorização cobre mais que a Cache Rule:** com credencial de escrita, entram no escopo desta fase o **Always Online** (desligado em 24/08, era a única defesa contra o 530), o **`browser_cache_ttl`** (hoje 1 ano na borda contra 300 s da origem — congela o `robots.txt` por 12 meses), o **Smart Tiered Cache** (ligado e inerte) e a **decisão sobre a injeção do `bridge.js`** (T3.1). **Tudo versionado em `ops/cloudflare/` e aplicado por `tools/apply-cache-rules` (T1.2), nunca por painel** — porque **foi exatamente a edição por painel que produziu a deriva que este plano está consertando**.
>
> **E o teste de aceitação mudou:** **restaurar a v7 pode NÃO tirar a zona do DYNAMIC.** Na era em que a regra do projeto estava viva, **a cobertura oscilou entre 0,0% e 17,5% em 28 medições**, com **90/90 MISS** três horas depois do aquecedor; **os 100% HIT vieram do template de painel "Cache everything", que não tem `override_origin`**. **Retenção é defeito separado e ainda aberto.**
>
> **Experimento que substitui o teste binário:** restaurar a v7 → **medir cobertura por 12 h** → remover **só** o bloco `vary` → medir de novo. **Mais a sonda diferencial:** `/familia/` (`Vary: Accept-Encoding, Accept`) contra `/familia/pagina/2/` (só `Accept-Encoding`) — **se a primeira ficar DYNAMIC e a segunda virar HIT/MISS, a causa é o `Vary: Accept`.**
>
> **Ler antes:** `ops/cloudflare/README-waf.md`. **Medir antes:** se o `CLOUDFLARE_ZONE_TOKEN` tem escopo de **escrita** em ruleset (hoje só está provado que lê).

**T1.1 — Restaurar a Cache Rule da borda, com corpo canônico único.**
- **Onde:** `PUT` no **entrypoint da fase** `http_request_cache_settings` (rota por fase, nunca por id de ruleset — o id não está versionado), com `CLOUDFLARE_ZONE_TOKEN`.
- **Corpo:** partir de `ops/cloudflare/cache-rules.json` (que **já** tem `vary/accept normalize` para `text/markdown` e já exclui `/mcp`, `/a2a`, `agent-card.json`), **acrescentando as exclusões que faltam** (O24/N-2): `/oauth/*`, os descritores `.well-known` que pedem `max-age=300` e **`/sitemap.xml`**. **É proibido usar `cache-rule-rollback.json` ou reconstruir à mão** — três corpos divergentes foi exatamente o que produziu a deriva.
- **Verificar (teste de aceitação, e é ele que separa "restaurado" de "reintroduzi a armadilha"):** `cf-cache-status` vira HIT em página de acervo **e** em `/…/index.md` pedido com `Accept: text/markdown` · `/sitemap.xml` e os descritores continuam respeitando `max-age=300` · `edge_cache_coverage.jsonl` sai de 0,0%.
- **Antes de aplicar:** **red-team Fable obrigatório** (mudança cara de reverter, em produção, com precedente de erro aritmético nesta exata frente).
- **Não fazer:** não aplicar `edge_ttl override_origin` sobre rotas de descoberta.

**T1.2 — `tools/apply-cache-rules` e `tools/check-edge-rule-drift`.** Fechar o laço de governança: hoje **nenhuma ferramenta escreve a Cache Rule** e toda deriva veio do painel.
- `apply-cache-rules`: PUT idempotente, leitura-antes-de-escrever, ledger em `data/ops/edge_rule_apply.jsonl`.
- `check-edge-rule-drift`: read-only, exit ≠ 0, diff canônico contra o versionado, **reprovando explicitamente quando `rules` está ausente ou vazio** — o caso de hoje, que `check-edge-vary-contract` atravessa em verde.

> ### 🔴🔴 T1.3 FOI REDUZIDA — ela destravaria a fábrica e CONGELARIA a mutilação (O43)
>
> **O red-team mostrou que a bomba está aqui, não em T6.1.** Destravar a fábrica na Fase 1 exige o reordenamento 5/9↔6/9; com a onda destravada, **`run-daily-content:313-316` faz `git add data/editorial/portfolio_v2` + commit INCONDICIONAL** — e o portfólio do STF está em **4 linhas contra 50 no HEAD**, **sem guarda** (`check-shard-preservation` cobre só `v2_pages`).
>
> **Agravante verificado executando o gate: ele próprio imprime *"PRÓXIMO COMANDO: `git commit -- data/editorial/portfolio_v2`"*, com 15 pendentes. O gate instrui o passo que causa o dano.**
>
> **✅ T1.3 na Fase 1 fica reduzida a UMA coisa: o timer próprio do IndexNow**, que **não depende da onda**. **Destravar a fábrica move-se para a Fase 6**, atrás da ordem segura de T6.1, e o critério *"`find public -newermt <hoje>` não vazio"* **sai** — porque publicar antes de corrigir o molde **industrializaria o defeito** (O38: 13-20 páginas/dia).

**T1.3 — Timer próprio do IndexNow (e SÓ isso nesta fase).**
- **A recuperação do shard e o destravamento da onda migraram para a Fase 6**, atrás da ordem segura: **gerador read-all → estender `check-shard-preservation` a `portfolio_v2` → recuperar os 50 → só então reordenar.**
- Quando lá chegar: recuperar `stf-informativo-derivado-01.jsonl` **lendo** com `git show HEAD:…` e escrevendo **para frente por gerador datado**. **PROIBIDO** `git reset/checkout/restore/revert/stash/clean`.
- Corrigir o gerador que apagou **50** registros ativos *(não 46 — O40 derrubou a aritmética sobre conjuntos disjuntos)*, **e os dois irmãos com a mesma bomba** (`stj-tema`, `stj-sumula`).
- **Desacoplar o frescor da onda:** criar `ops/systemd/wikijuridica-indexnow.timer`/`.service` no padrão dos ~20 timers que já existem lá, chamando **`tools/generate-indexnow-incremental-submit`** — **verificado: a ferramenta existe** (ao lado de `generate-indexnow-direct-submit` e `generate-indexnow-key-public-file`), e é idempotente por hash, então rodar sozinha é seguro. **Escopo confirmado: criar o timer, não a ferramenta.** Hoje **um shard corrompido silencia IndexNow e WebSub do portal inteiro**, inclusive para as 10.070 páginas sadias.
- **Verificar:** submissão IndexNow com data de hoje no ledger · `find public -newermt <hoje>` não vazio.

> ### 🔴 T1.4 É PRÉ-REQUISITO DE TODOS OS GATES NOVOS — e eu contei quantos são
>
> **Três críticos Fable seguidos acusaram o mesmo padrão:** *"gate novo sobre canal morto é papel"*, *"as cinco frentes propuseram SEIS instrumentos novos sem que nenhuma consertasse o laço de resposta"*, *"~13 artefatos novos no mesmo canal morto"*. **Fui contar no plano:**
>
> **Gates que este plano cria: 7 nomeados** — `check-answerfirst-publicado` · `check-binario-vs-fonte` · `check-derived-authorial-floor` · `check-edge-html-injection` · `check-edge-rule-drift` · `check-owner-alerts-abertos` · `check-served-robots-drift` — **mais 5 sem prefixo padronizado**: `nginx-config-alcancavel` (T0.5) · `area-label-cobertura` (T5.9) · `check-bot-attribution-grade` · `check-indexnow-state-reconciliation` · `check-lastmod-fidelidade`. **Doze ao todo.**
>
> **REGRA, e ela vale sem exceção: nenhum dos doze é implementado antes de T1.4 estar feita e verificada.** Um gate que reprova num canal que ninguém lê **não é controle — é mais uma linha num ledger de 25 chaves não resolvidas**.
>
> **E um deles é circular por construção:** `check-owner-alerts-abertos` **ligado ao runner falha exatamente quando os alertas nascem** — o runner morre na etapa 3/9 ou 5/9, que é quando o alerta é emitido. **Ele precisa de gatilho independente do runner (`systemd.path` ou timer próprio), ou não nasce.**
>
> **O que "T1.4 feita" significa, em critério verificável:** existe um **consumidor** que lê `owner_alerts.jsonl`, **age** e **marca `resolvido`** — hoje os únicos que tocam o arquivo são `tools/notify-owner` e a unit de alerta, **os dois PRODUTORES**. Enquanto o grep de consumidores devolver só produtores, **T1.4 não está feita**.

**T1.4 — Consertar o canal de alerta ANTES de criar gate novo.** (O24/F-1 e F-2)
> **⚠ ESTA TAREFA EXECUTA NA FASE 0, COMO T0.9.** O texto abaixo é o **detalhe integral** dela e fica aqui para não perder o banner com a contagem dos gates; **no frontboard, o id é `T0.9` e a fase é 0.** Não executar duas vezes.
- **Problema medido:** 48 alertas críticos `borda-cache-regra` com `resolvido: false` desde 22/08, **afogados por 536 alertas `rede-banda` a ~1/min** cujo `silenciado_por_cooldown` está inconsistente.
- **Fazer:** corrigir o cooldown do alerta ruidoso; **escalar** alerta crítico não resolvido após N repetições; corrigir as ferramentas que **saem com exit 0 relatando fracasso** (`check-edge-vary-contract` verde com zero regras; aquecedor com `failures:0` e `dynamic:10383`).
- **Racional:** *"gate novo sobre canal morto é papel."* Todo gate proposto neste plano depende desta tarefa.

**T1.5 — Aquecimento: fazer valer, não desligar.** Ele existe por um motivo real (evitar 530 ao crawler em queda de túnel).
- Usar a flag `--so-frios`, **que já existe** (`tools/warm-edge-cache:28,162-186`).
- Aquecer **também** a variante `Accept: text/markdown` — **mas pesando o custo**: dobraria o tráfego próprio (+62 mil req/dia) para um canal com ~1.100 requisições externas/dia (O24/S-2).
- Reduzir a cadência ao que a cobertura medida exigir, em vez de 6 varreduras completas por dia.
- **Contexto físico a considerar (O24/S-3):** o uplink é **WiFi 2.4 GHz a 72 Mbit/s**. 474 MB/dia de aquecimento num rádio desses tem custo real.

---

### FASE 2 — Revalidação e frescor (ordem interna obrigatória)

> **Ordem definida por norma citada (O29). Ela tem quatro passos e inverter qualquer um transforma correção em regressão de conteúdo.**

**T2.0 — NÃO TOCAR em `if_modified_since` ainda.** O default `exact` é hoje **a única coisa que impede dano maior**, porque o `Last-Modified` servido **retrocede no tempo**. A RFC 9110 §13.1.3 descreve literalmente este caso.
- **Teste de guarda:** `curl -H 'If-Modified-Since: <LastModified+1dia>'` numa página do acervo tem de devolver **200**. Se devolver 304, alguém ligou o `before` fora de ordem.

**T2.1 — PRIMEIRO: ETag forte de conteúdo no caminho estático.**
- **Hoje o ETag do acervo é `hex(mtime)-hex(size)`** e o mtime rebobina — **duas versões diferentes podem receber o mesmo ETag**, o que fica **abaixo do validador forte da RFC 9110 §8.8.1**. O Google *"strongly recommends using ETag"*.
- **O repo já tem a implementação certa e não a usa aqui:** `internal/httpserver/conditional.go:44-47` (`strongETag` = SHA-256 do corpo), que é o que o caminho Markdown já faz.
- **Como, sem hardcode:** o publicador gera um `map $uri $wj_etag { … }` **a partir do `html_sha256` que o `published_manifest` já carrega**, e a `location /` passa a emitir `ETag: "$wj_etag"`.
- **Verificar:** o ETag servido é idêntico ao `html_sha256` da rota **e muda se e somente se os bytes mudarem**.

**T2.2 — SEGUNDO: parar a rebobinada do mtime.** `gravaDatado` (`cmd/publish-v2-direct/main.go:2459-2465`) carimba o mtime de volta para a data editorial quando encontra bytes idênticos — em 20/08 houve **quatro publicações**, e as três últimas devolveram o mtime para 06/08. **Medido: 9.439 páginas servem bytes de 20/08 declarando 06/08.**
- A data editorial **continua no conteúdo e no manifesto**, onde pertence, e **para de governar cache HTTP** (RFC 9110 §8.8.2: `Last-Modified` é da **representação**).
- Alternativa aceitável: manter a rebobinada **só** quando `content_sha256` **e** `html_sha256` forem os mesmos da publicação daquela data.

**T2.3 — TERCEIRO, e só agora: `if_modified_since before;`** no **vhost vivo** (`ops/nginx/wikijuridica.conf`), regenerando o dedicado — nunca editando o `standalone/`.
- **Verificar:** as quatro datas de M6.b — anterior → 200; igual → 304; **posterior → 304** (hoje 200).

**T2.3.b — `<lastmod>`: MANTER. Pergunta do dono respondida com fonte (O29).** Ele **não mente** — 10.288 de 10.294 URLs batem com o artefato em disco, e as 28 páginas cujo corpo mudou são **exatamente** as 28 cujo lastmod se moveu. O Google o usa *"if it's consistently and verifiably accurate"* — condição cumprida; o Bing avisa que **sem ele** os buscadores *"may delay crawling updated content or may over-crawl your website"*. **Remover destruiria o único sinal que já funciona.**
- **O que muda:** ampliar o oráculo para o critério **literal** do Google, que inclui *"the structured data, or links on the page"* — **9.467 páginas tiveram links e JSON-LD alterados e o lastmod não se moveu**. Correção **sem misturar os dois usos**: manter `content_sha256` governando o IndexNow (onde reenvio em massa é nocivo) e criar um `significant_sha256` (corpo + links + proveniência) para governar o `<lastmod>`.
- **Rotas derivadas** (home, hubs, paginação, institucionais com contagem viva): lastmod pelo **hash do HTML servido** — regra que o repo **já adotou** no `generate-indexnow-incremental-submit` para as 206 rotas derivadas.
- **Granularidade:** o Bing pede ISO 8601 **com hora**; 10.241 URLs têm só data. **Registrar o instante UTC a partir de agora e NÃO retroagir** — inventar `00:00:00Z` onde não houve medição seria precisão fabricada.

**T2.4 — ETag no HTML servido.** A origem **emite** (`"6a73ce80-57d8"`); **a borda remove**, porque reescreve o corpo para injetar o `bridge.js`. Amarrado a T3.1.

**T2.5 — Feed como canal de frescor.** Hoje: 1.000 entradas, 511 KB, só `<summary>`, 506 empatadas no mesmo timestamp, sem feed por área. Avaliar contra RFC 4287 e RFC 5005 (paginação), e expor `rel="alternate" type="text/markdown"` por entrada.

**T2.6 — Pré-comprimir `.br` na transação de publicação.** `brotli_static` está ligado sobre **zero** arquivos.
- **Ganho medido:** br q11 pré-comprimido = 6.373 B/pág contra 7.011 B/pág do q5 on-the-fly (**−9,1% na rede**), CPU por requisição cai a zero (~1,5 ms/req hoje), **e o ETag volta a ser forte** (o filtro de compressão o enfraquece para `W/"…"`).
- Hash do par entra na evidência de release, preservando a coerência `public/` ⊆ sitemap ⊆ `published_manifest`.

---

### FASE 3 — Autoridade da borda e conformidade de protocolo

**T3.1 — Decidir a injeção do `bridge.js` com medição, e identificar o ator.**
- **Fatos:** 47.616 B de JS externo por página · `nonce` acrescentado à CSP · o arquivo **não existe na origem** · viola três dos cinco limites da emenda de HTML leve.
- **Primeiro:** ler o **audit log da conta** para saber **quem** ligou (o token de zona não expõe o ator; precisa da credencial de conta). Pode ser beta habilitado pelo próprio dono — tratar como intrusão sem verificar seria erro.
- **Depois:** desligar por janela curta e **remedir** `cf-cache-status` e presença de ETag. Se o cache voltar, a injeção é elo da cadeia de M6.c.1; se não, a causa é só a Cache Rule.
- Versionar a decisão em `ops/cloudflare/`.

**T3.2 — `check-edge-html-injection`.** Baixa ~10 rotas da origem e da borda e reprova se a CSP diferir byte a byte de `httpserver.ContentSecurityPolicy` ou se o HTML da borda contiver `<script>` ausente na origem. **Depende de T1.4.**

**T3.3 — Erro em HTML para cliente-máquina: um ponto de correção, não três.** `/a2a/v1`, `/api/v1/relatos`, `.md` inexistente e o 404 do Go entregam HTML a quem pediu JSON ou Markdown. **Uma família, um lugar** (`error_response.go` seguindo a intenção da requisição).

**T3.4 — `relatar_defeito` sem token deve responder 401 com `WWW-Authenticate`.** A correção precisa ser **antes** de entregar ao SDK (no streamable HTTP os headers do 200/SSE saem antes de o handler rodar) e é barata: o header `Mcp-Name` já nomeia a ferramenta.

**T3.5 — Alias RFC 9728: `/mcp/.well-known/oauth-protected-resource`.** Cliente real (`aisec-registry`) sonda 3×/dia e toma 404. É conformidade de spec publicada, não moda.

**T3.6 — WebMCP: migrar de `navigator.modelContext` para `document.modelContext`.** A spec vigente (2026-08-26) e a doc da OpenAI definem `document.modelContext.registerTool(...)`, e **o browser embutido do ChatGPT descobre as ferramentas ao visitar a página** — sem cadastro nem contrato. Recalcular o hash da CSP e propagar por `cmd/generate-csp-nginx`.

**T3.7 — Registrar o `/mcp` no MCP Registry.** Único registro público que aceita inscrição hoje; self-serve por `mcp-publisher`, namespace verificado por **DNS TXT** — sem credencial de terceiro, sem SaaS.

**T3.8 — `/sitemaps/` deve responder 200, não 410.** `location = /sitemaps/` com `proxy_pass` vence o prefixo por precedência; o 410 legítimo do shard ordinal extinto é preservado.

**T3.9 — Normalizar URL com pontuação residual.** Agentes extraem URLs de Markdown e trazem `)`, `:`, `` ` ``, `,`. **10,2% dos 404 de origem são isso.** 301 para a URL limpa é engenharia defensiva legítima — **a rota de destino existe**, não é criar rota fantasma.

---

### FASE 4 — Política de bots, identidade e registry

**T4.1 — ⚠ A armadilha que torna a "melhoria" uma regressão.** No robots.txt, **grupo nomeado descarta o curinga inteiro**, e `RenderRobotsTXT` (`internal/crawl/crawl.go:1139`) serializa cada regra em grupo próprio. **Criar um grupo `GoogleOther / Allow: /` REMOVE dele o `Disallow: /buscar/` que ele herda hoje do `*`.** → **Toda entrada nova precisa repetir as guardas do curinga, e isso vira GATE, não disciplina.**

**T4.2 — Reformar o registry por FUNÇÃO, derivando do dado.** A lista de bots existe em **três cópias**. **Medi a divergência entre elas:**

| Cópia | Tokens | Divergência |
|---|---|---|
| `content/crawl_policy.json` (canônica) | **32** | — |
| `internal/crawl/crawl.go:257-406` (`DefaultBotRegistry`) | **32** | **zero** — sincronizada hoje |
| `tools/botagents.py:31` (`AGENTES`) + `:123` (`FUNCAO`) | **50** entradas / 45 chaves | **+18 tokens** |

**Leitura:** a duplicação Go↔JSON **não está divergindo hoje** — mas é duplicação, e uma delas vai envelhecer sozinha algum dia (é a natureza do hardcode que o dono proibiu). **A divergência real está no Python: a TELEMETRIA já conhece 50 bots enquanto a POLÍTICA governa 32.** Entre os 18 que a telemetria conta e o robots.txt não governa: `ahrefsbot`, `chrome-lighthouse`, `cloudflare-agentreadiness`, `bingpreview`, `blexbot`, `dataforseo`, `dotbot`, `duckassistbot`. **É a confirmação numérica do achado O17** (*"16 agentes que a telemetria conta não são governados pela política"*) — e mostra qual das três cópias está mais perto da realidade.

**Correção sem hardcode:** **fonte única** em `content/crawl_policy.json`; `DefaultBotRegistry` passa a **carregar**, não a reproduzir; `botagents.py` **importa** do mesmo JSON. Gate que reprova quando qualquer consumidor conhecer token que a fonte não tem — **hoje esse gate não existe, e por isso os 18 passaram despercebidos**.
- **Entram, com doc oficial verificada:** os 6 com tráfego real fora do registry (`semrushbot` 1.163 req/dia, `cloudflare-agentreadiness` 360, `yandexbot` 153, `chrome-lighthouse` 30, `google-inspectiontool` 12, `ahrefsbot`) · a família Google que não herda nada (`Google-Agent`, `GoogleOther*`, `Storebot-Google`, `Google-Safety`, `APIs-Google`, `AdsBot-Google-Mobile`, `Mediapartners-Google`) · **`Google-GeminiNotebook`** (o nome antigo `Google-NotebookLM` **expira este mês**) · `YouBot`, `Kagibot`, `LinerBot`, `Diffbot`, `FirecrawlAgent`, `AI2Bot`, `ImagesiftBot`.
- **NÃO entram:** `cohere-ai` e `cohere-training-data-crawler` (**o fornecedor desmente operá-los**) · `Brave-Search` (a doc declara que **não há UA diferenciado**) · `Kangaroo Bot` (folclore).
- **Registrar a cascata:** `Kagibot` e `ImagesiftBot` herdam o grupo `Googlebot` por documentação oficial — hoje é vantagem, vira regressão se `Googlebot` for restringido.
- **Fetcher disparado por usuário IGNORA robots.txt** (verbatim do Google). Para esses, o instrumento é **faixa de IP na borda**, nunca linha no robots.

**T4.3 — Verificar identidade antes de conceder tier.** Hoje declarar-se `ChatGPT-User` basta para receber acesso ilimitado (`requests_local_verification: 0`), e **24,4% dos 404 são varredura de credencial vinda de UA de bot valioso**.
- **⚠ CORRIGIDO (O42.c): as listas JÁ EXISTEM.** `data/ops/bot_ip_ranges/` tem **11 arquivos** com mtime **2026-08-25 11:24**, anterior a esta sessão — inclusive **`anthropic.json`, `openai-chatgpt-user.json`, `openai-gptbot.json`, `openai-searchbot.json`, `perplexitybot.json`, `perplexity-user.json`, `duckduckbot.json` e `bingbot.json`**. **O plano afirmava que faltavam e mandava criá-las. Falta apenas `openai-adsbot.json`.**
  **O trabalho real é outro:** (a) **atualizar as três URLs do Google**, que apontam para o endereço antigo e só funcionam por 301; (b) **corrigir o metadado mentiroso `authenticates_agents`**, rotulado `['google-site-verification']`; (c) **ligar Perplexity ao caminho verificado — porque `Perplexity-User` ignora robots.txt por design, e IP é a única superfície de controle que resta**; (d) **`meta-*` fica fora do método: a Meta não publica lista de IP nenhuma**, e é 45% do tráfego de bot.
  **Armadilha de coleta que faria o gate ficar verde por ausência de dado:** a Amazon publica **três esquemas incompatíveis** — `ipv4Prefix` solto **sem máscara** (592) · `ip_prefix` em CIDR /32 (694) · `ipv4Prefix` solto (1.040). *"Um coletor escrito contra o formato do Google grava lista vazia para o `Amzn-SearchBot` e o gate fica verde por ausência de dado."*
- **Corrigir o endereço obsoleto do Google:** as listas mudaram para `/static/crawling/ipranges/` em 2026-02-11 e o `googlebot.json` antigo responde **301**; o repo espelha 3 arquivos para 5 listas oficiais.
- **Sem hardcode:** a URL de cada lista vem do registry, declarada por bot, nunca de literal no script.
- **Web Bot Auth (RFC 9421):** OpenAI, Google (`agent.bot.goog`) e You.com já assinam. **O `exp` da chave é rolante** — cachear por `kid` e reler `nbf`/`exp` a cada fetch, nunca congelar.

**T4.4 — Aplicar de fato o rate limit, ou parar de declará-lo.** O nginx tem **uma única zona genérica de 3.000 r/m por IP** — 25× o guard declarado de 120, 50× a faixa de treinamento de 60, 150× a estrita de 20. E `ValidatePolicy` **reprova** bot de treinamento sem `requests_per_minute`, número que nunca é aplicado. **Registry decorativo é pior que registry ausente: mente para quem o lê.**

**T4.5 — Corrigir o allowlist:** `$wj_bot_allow` tem `amzn-searchbot` e `amzn-user` mas **não `amazonbot`**, que é o que realmente vem (111 req/dia).

**T4.6 — 🔴 BLOQUEADA até que a armadilha seja resolvida (O42.d).** A proposta era `Clean-param` para o Yandex — o crawler com **99,28% de cobertura** do acervo, hoje no curinga.
**Por que está bloqueada:** a doc oficial diz, literal, *"If the `User-agent: Yandex` string is detected, the `User-agent: *` string is ignored"* — **o casamento é por SUBSTRING, case-insensitive**. **Criar QUALQUER grupo contendo "Yandex" faz o `*` deixar de valer para a família inteira** — a armadilha T4.1, disparada pela própria correção.
**Condição para desbloquear:** a entrada nova **traz, ela mesma, todas as guardas do curinga**, e o gate verifica isso.
**Correção de fato ao plano:** o `Yandex` **NÃO considera `Crawl-delay` desde 2018-02-22** (doc oficial) — O12 os listava juntos como *"o que o Yandex entende"*.
**E o achado que faltava, mais importante que a tarefa original:** **`YandexAdditionalBot` e `YandexAdditional` são o canal de CITAÇÃO em IA do Yandex** — a doc confirma que **toda resposta da IA do Yandex leva referência à fonte**. **Devem ser PERMITIDOS**, e hoje nem estão no registry.

**T4.7 — Instrumentar a métrica de citação que existe e não é contada:** a OpenAI acrescenta **`utm_source=chatgpt.com`** a toda URL de referência — **é o único sinal de citação consumada que ela dá ao publisher**, e não há contagem em `data/ops/`.

**T4.8 — Corrigir a telemetria que se auto-infla:** `considered_for_answer` é carimbado em toda linha, inclusive nas 84% que a própria ferramenta classifica como sem relação com citação; e `organic_requests` conta 1.887 req/dia de sonda interna como audiência. **Dever de anti-fraude, mesmo sendo erro interno e não intencional.**

**T4.9 — Compactar o ledger de borda:** 22.557 linhas para 326 fatos (69× de redundância, 16,8 MB crescendo 730 KB/dia). **É a causa material da armadilha A1** — some com um compactador.

**T4.10 — Gravar as rotas por bot, que hoje são jogadas fora.** O agrupamento acontece em memória e só a contagem sobrevive; por isso ninguém sabia qual URL deu 404 para qual bot, e esta sessão teve de reconstruir isso à mão.

---

### FASE 5 — Autoridade do conteúdo (o que responde *"não tem autoridade nenhuma"*)

**T5.1 — Alinhar a data visível ao `LastModified()`.** **96,7% das páginas se contradizem sobre a data de atualização dentro do próprio HTML**: o byline usa `ReviewedAt` cru (`render.go:1016-1022`) e o JSON-LD usa o helper sancionado (`structured_data.go:688`). **Uma linha, corrige 9.710 páginas.** Alternativa igualmente válida: manter `ReviewedAt` no visível e rotulá-lo *"Revisado em"*, não *"Atualizado em"* — são semânticas distintas.

**T5.2 — Emitir a credencial OAB no grafo.** **0 de 10.042 páginas** emitem `author` com `jobTitle`, `identifier` ou `hasCredential`; o nó completo existe em **uma** rota (`/sobre/`). E o **mesmo `@id`** carrega dois nomes diferentes no grafo. Popular a partir de `content.EditorialIdentity` — **nunca hardcoded**, exatamente como `LegalService` e `Organization` já fazem.

**T5.3 — Front matter YAML no Markdown.** O canal que os agentes consomem carrega **4 dos 18 campos** do JSON-LD, todos como prosa, **e não declara licença nenhuma** enquanto o HTML declara CC BY 4.0. É reprojeção do mesmo objeto — **nenhum dado novo**. Corrigir junto a divergência de rótulo (*"Proveniência"* no HTML × *"Fontes oficiais"* no Markdown).

**T5.4 — Publicar os 24.367 `anchor_claim` que já existem e não chegam à página.** **95% deles nunca são publicados.** É a maior alavanca de autoridade disponível **e não exige redigir uma linha nova**.
- **Estado medido:** 61,1% das afirmações normativas sem âncora verificável; **2.080 páginas (20,6%) sem nenhuma**; 533 páginas com zero âncora em qualquer elemento.
- **Como:** gerador datado com lease + CAS + escrita atômica. **PROIBIDO** editar JSONL à mão, **PROIBIDO** reescrever do zero, **PROIBIDO** descartar texto redigido.
- **Ordem:** priorizar as 2.080 páginas sem nenhuma âncora, ordenadas por rastreio real de bot. **Critério positivo primeiro** (`[[oraculo-antes-de-refinar]]`): calibrar nas 10 páginas já amostradas, conferir por leitura humana, só então liberar o lote.

**T5.5 — Fragmento do dispositivo nos links inline.** **0 de 106 links externos do corpo** têm o fragmento — todos apontam a lei inteira, embora a URL profunda já exista e seja construível.

**T5.6 — `Legislation` com URN LexML nas 2.293 páginas que citam lei federal e não emitem o nó.** O extrator existe e falha em silêncio: instrumentar `internal/legalfacts` para **registrar** as citações que reconheceu como lei e não conseguiu normalizar, e ampliar o normalizador pelas formas **realmente observadas**, nunca por adivinhação.

**T5.7 — Identificador de versão e "como citar".** **0 páginas** emitem `version`; **2 páginas** contêm *"Como citar"*; **97,5%** têm `datePublished` igual a `dateModified`. Reaproveitar o **SHA-256 do conteúdo que o `published_manifest` já armazena** — zero cálculo novo, determinístico e conferível, no mesmo espírito do digest das agent-skills.

**T5.8 — Vigência da norma.** **Zero páginas** informam se a norma citada está em vigor — dizem apenas quando a **URL** foi conferida. Para conteúdo jurídico, é o que um modelo precisa para citar com segurança.

**T5.9 — Rótulos de área acentuados, DERIVADOS.** `Diarios`, `Noticias`, `Jurisprudencia` aparecem sem acento no **breadcrumb visível** e no **JSON-LD** de **285 URLs**. **A correção NÃO é acrescentar três entradas ao mapa hardcoded** (isso violaria R13 e deixaria a próxima área nova repetir o defeito): **derivar o rótulo do dado** (`content/pages.json`, `content/area_hub_editorial.json`) e **transformar o fallback ASCII em erro de gate**. Republicar as 285 páginas — o breadcrumb está assado no HTML.

**T5.10 — answer-first: medir antes de decidir.** O gate existe, é bom e **não fiscaliza o acervo publicado**: só 29,2% passariam; 67,8% estouram `MaxAnswerWords=60`; `resumoextrativo` é código morto. **A mediana real é 70 e o gate diz 60** — ou o acervo está errado, ou o número herdado está. **Criar `tools/check-answerfirst-publicado` (read-only) antes de mexer em texto.**

**T5.11 — Molde nas súmulas derivadas.** 80 páginas com quatro frases idênticas, **sigla interna de órgão julgador e data em formato ISO no texto visível** — viola anti-template e PT-BR.

**T5.12 — Proteger o que já está bom.** **PREMISSA REFUTADA:** as fontes **não** apontam para home de órgão — **82,6% apontam o documento específico**, só 0,6% (139 links) apontam raiz, e 69,7% das páginas têm **todas** as fontes específicas. **Não corrigir; criar check que reprove regressão abaixo do piso medido de 82,6%**, e usar o `citation[]` existente como insumo de T5.4.

---

### FASE 6 — Canal de notícias: duas causas-raiz achadas, correção conhecida

> **O timer está SAUDÁVEL e pontual.** Rodou nos 6 dias. O defeito é *dispara e o serviço falha, sempre* — `daily_content_runs.jsonl` registra **6 de 6 execuções "parcial": a onda NUNCA completou uma vez desde que nasceu**, e as etapas 8/9 (publicação) e 9/9 (IndexNow) **jamais rodaram**. O canal **coleta e redige com sucesso toda madrugada** — 26 páginas hoje às 04:25 — **e nunca publica**. Atraso: **6 dias** (última notícia no ar é de 20/08).

> ## 🔴🔴 PARE — T6.1 COMO EU ESCREVI CAUSARIA DANO IRREVERSÍVEL
>
> **A crítica Fable da onda 6 achou o que CINCO frentes não viram, e é contra esta tarefa.**
>
> **O gerador do STF truncou TAMBÉM o shard de PORTFÓLIO, e ninguém percebeu:**
> ```
> data/editorial/portfolio_v2/jurisprudencia-stf-derivada-01.jsonl
>    HEAD = 50   ·   disco = 4
> ```
> Escrito pelo **mesmo `os.WriteFile` do mesmo último-arquivo** (`generate-stf-informativo-pages/main.go:265` e `:400`). **E `check-shard-preservation` guarda SÓ `data/editorial/v2_pages` (linha 45) — `portfolio_v2` não tem preservação NENHUMA.**
>
> **A prova estava impressa e ninguém leu:** o próprio `check-v2-portfolio-pairing` imprime *"10402 já COMMITADOS, 10367 no estado atual"* — **−35 = −50 do STF +15 novas**. *"Ninguém leu o segundo número."*
>
> **A consequência de aplicar T6.1 como eu a escrevi:** ela manda **commitar o portfólio primeiro**. **Aplicado sobre o disco de hoje, esse commit CONGELA a mutilação 50→4 como nova verdade e destrói o registro de demanda de 50 páginas que estão NO AR** — violando a proibição de descartar trabalho redigido e quebrando o primeiro elo da cadeia `shard → manifesto → public → sitemap`.
>
> ### ✅ ORDEM SEGURA, e ela é obrigatória
> **1º** corrigir o gerador (**read-all**, o padrão do gerador irmão) · **2º** **estender `check-shard-preservation` a `portfolio_v2`** · **3º** recuperar os 50 registros por gerador datado a partir de HEAD · **4º** **só então** reordenar as etapas 5/9 e 6/9.
>
> **Nenhum commit de portfólio antes do passo 3.**

**T6.1 — [CRÍTICA] Deadlock de ordem: a onda chama o check ANTES do commit que o satisfaz.**
`tools/run-daily-content` executa `check-v2-portfolio-pairing` na **etapa 5/9**, mas o check lê o portfólio do **commit PAI** (`arvore="HEAD"`) e o commit que colocaria os intents lá é a **etapa 6/9, depois**. Como a etapa 2/9 gera intents novos toda madrugada, `so_no_candidato` **nunca é vazio** e a etapa 5/9 **sempre reprova** — 21, 22, 23 e 24/08, mensagem idêntica. **A própria saída do check imprime a ordem certa:** *"PRÓXIMO COMANDO: git commit -- data/editorial/portfolio_v2 / e SÓ DEPOIS: git commit -- data/editorial/v2_pages"*. É exatamente a armadilha que o `CLAUDE.md` documenta.
- **Correção:** mover a chamada para **depois** do commit do portfólio e **antes** do commit das páginas.

**T6.2 — [CRÍTICA] `generate-stf-informativo-pages` lê só o último JSONL e sobrescreve o shard inteiro.**
Linhas 153-158: `arquivos[len(arquivos)-1]` — lê **apenas o arquivo mais recente**; linha 261 grava com `os.WriteFile`, **substituindo o shard**. Em 25/08 o coletor trouxe delta de **5 registros** contra 54 do arquivo de 20/08 → o gerador montou 4 páginas e **reescreveu 50 → 4**. A guarda `intentsJaPublicados` não protege porque só reordena o que foi lido.
- **Correção — copiar o padrão que já funciona no gerador irmão** (`cmd/generate-noticia-pages/main.go:152`, que **lê todos os arquivos e por isso nunca perdeu página**): laço sobre todos os JSONL, deduplicando pela chave de julgado que já compõe o `intent_id`.
- **✅ Nada foi perdido:** os 50 estão **íntegros no git**, com lastro integral em `2026-08-20.jsonl` (50/50). Recuperação por **escrita para frente** pelo gerador corrigido — a saída passa a ser a **união 54 = 50 + 4**, com `check-shard-preservation` verde.

**T6.3 — 15 páginas redigidas paradas no disco, não commitadas — ATIVO a recuperar.**
6 de notícia (`not-cjf-20260820`, `not-tst-20260821`, `not-stj-20260824`, `not-tst-20260824`, `not-stj-20260825`, `not-tst-20260825`), 5 de diário, 4 de STF. Mais **597 KB de matéria-prima coletada e nunca usada** (6 arquivos diários de 21 a 26/08). **Nunca descartar — é trabalho pago.**

**T6.4 — [ALTA] O publicador DESCARTA a data que a notícia declara — e é isto que empata o feed.**
O gerador **grava** `PublicationDate: dia` (`main.go:476`) e o JSONL confirma (`"publication_date": "2026-07-24"`). Mas o struct que o publicador usa (`internal/v2publish/v2publish.go:30-44`) **não declara esse campo** — o `json.Unmarshal` o **descarta em silêncio** — e a linha 290 grava `PublicationDate: publishedAt`, valor único para o acervo inteiro.
- **Consequência medida:** as 20 notícias **empatam em 2026-08-20 no sitemap, no feed e no `pages.json`** — contribui para os 506 empates de timestamp no feed (O13).
- **⚠ Delimitação do alcance, medida por mim — e ela refuta uma hipótese minha:** cheguei a supor que este descarte explicaria os **93,1% de `lastmod` congelado**. **Não explica.** Li o struct (14 campos, nenhum `publication_date` — confirmado) e medi o dado: **apenas 2 de 876 shards declaram `publication_date`, somando 39 registros**. O resto do acervo **não declara data própria**, então não há o que descartar. **O bug é real e vale corrigir — mas seu alcance são 39 registros, e justamente os do canal de frescor diário, o único que precisa de data própria.** O `lastmod` congelado tem outra causa e continua em aberto (T2.3/O28).
- **Correção — duas linhas:** acrescentar `PublicationDate string` ao struct e trocar por `primeiroNaoVazio(page.PublicationDate, publishedAt)`.

**T6.5 — [ALTA] `meta_description` corrompida em 100% do canal.**
`plural()` **sempre** prefixa a contagem. Na abertura está certo (`"5 comunicados"`); na meta o chamador passa uma frase iniciada em maiúscula → **`"5 As decisões que o STJ divulgou em 20 de agosto de 2026…"`**, servido em `<meta name="description">`. **26/26 do estoque e 20/20 do HTML no ar.**
- **Correção no CHAMADOR, não no helper** (o helper está certo e é usado corretamente em outros pontos).

**T6.6 — [MÉDIA] Base legal por fonte apurada e não publicada — e MISCITADA no código.**
O coletor **faz o trabalho certo**: cada fonte carrega a base declarada, e o cabeçalho distingue corretamente o **fato** (livre) da **redação** da notícia institucional (protegida), registrando que a EBC foi excluída por licença não confirmada. **Nada disso atravessa** — o registro de página tem 14 chaves e nenhuma de licença.
- **E há erro jurídico no comentário do código:** invoca *"art. 46, VIII, que autoriza citação 'na medida justificada para o fim a atingir'"* — **essa expressão é do inciso III, não do VIII**. E o **art. 8º, VI** (*"nomes e títulos isolados"*), que é a base **mais limpa** para reproduzir manchete, **não é invocado**.
- **Fonte oficial verificada pela frente:** Lei 9.610/1998, arts. 8º e 46, via Câmara/LEGIN (HTTP 200, 108.814 B, 2026-08-26). **Declarado como instrumento único — não corroborado**: o `planalto.gov.br` recusou 4 tentativas e o LexML não respondeu.
- **Correção:** propagar `Licenca` e `Natureza` por fonte (a estrutura `Source` já é por fonte e o coletor já grava os dois campos) e corrigir a base declarada para o fundamento que o texto oficial sustenta.

**T6.7 — [MÉDIA] As 20 páginas declaram CC BY 4.0 sobre manchetes de tribunais que o portal não detém.**
O JSON-LD servido traz `"license":"…/by/4.0/"`, e a **CC BY autoriza redistribuir e ADAPTAR, inclusive comercialmente**. A página de notícia é **a única família cujo corpo contém texto de terceiro reproduzido literalmente**. **Risco jurídico real, não formalidade.**
- **Correção:** escopar a licença **a partir do dado**, não enfraquecer a política: CC BY 4.0 sobre **o comentário autoral**, e no bloco de fontes a base declarada de **cada trecho citado** — a distinção que a DEC-032 chama de duas camadas.

**T6.8 — [MÉDIA] Molde: bloco de 93 palavras idêntico em 18 de 26 páginas** (28% do corpo), porque `comoLer(sigla)` varia **por órgão, não por página**. 25 das 26 carregam um bloco literalmente repetido, **e o limiar de similaridade não apanha**.
- **Correção:** fazer o bloco derivar **do conteúdo do dia** — tema repetitivo → alcance vinculante; decisão monocrática → colegialidade; ato administrativo → não é mérito. **O material já está coletado.**

**T6.9 — [BAIXA] Coleta de diários municipais falhou em 3 de 6 ondas, sem causa investigada** — o log vai para `/tmp`, volátil, e o journal só imprime *"falhou"*. **Correção:** gravar exit code e última linha no ledger que já existe.

**T6.10 — [BAIXA] Seis alertas, seis dias, a mesma falha — e nada percebe que é a mesma.** A chave inclui a data (`onda-diaria-$HOJE`), então cada dia é "novo". **É a assinatura de laço sem progresso que o contrato manda tratar como bug.** **Correção:** severidade em função da **reincidência**, lida do ledger. *(Mesma família de T1.4.)*

**T6.11 — ✅ O CONTEÚDO ESTÁ CONFORME — linha de base a proteger.** Verificação contrato a contrato nas 20 rotas no ar: coerência manifesto ⊆ sitemap ⊆ `public` **limpa** · **duas camadas cumpridas com 79,1% de comentário autoral** · texto oficial só como **manchete entre aspas curvas, em bloco próprio** · **Jaccard exato máximo 0,638 em 325 pares** · **PT-BR sem mojibake** · identidade OAB presente · `official_sources` com `verified_at` e `http_status: 200` por matéria. **Registrar como linha de base** para que regressão futura seja detectável por comparação.

**T6.12 — A tubulação de frescor existe, e o que falta é o sinal — medido em 2026-08-26, a reconfirmar.** *(Reescrito: a redação anterior dizia "JÁ EXISTE e está correta… o frescor chega sozinho na madrugada seguinte" — declaração de vitória sobre comportamento futuro, que R15 proíbe. O red-team apanhou.)* O feed ordena por `Updated` desc e corta em 1.000 (`internal/feed/feed.go:119-126`); o IndexNow incremental decide por **hash de conteúdo por URL**; o WebSub tem timer próprio e **vivo**; o `llms.txt` por área é gerado no build. **Nada disso precisa ser criado.** O que está quebrado é **o sinal que a alimenta — a data — e o fato de a onda nunca chegar às etapas 8/9 e 9/9.** Corrigidos T6.1, T6.2 e T6.4, **o frescor chega sozinho a sitemap, feed e IndexNow na madrugada seguinte.**

---

### FASE 7 — Fazer o bot VOLTAR, e virar serviço que ele chama

> **Esta fase existe por ordem direta do dono nesta sessão:** *"O portal tem que ser um serviço para IA"* e *"eles têm que vir e voltar, e não vir e nunca mais voltar"*. As Fases 0-2 removem os impedimentos; **esta cria o motivo de retorno.**

**T7.1 — Instrumentar RETORNO como métrica de primeira classe.** Hoje a telemetria mede **cobertura acumulada**, que só cresce e por isso **nunca acusa abandono**. É por isso que ninguém viu o GPTBot cair para 1 requisição/dia em 08/08 e o meta-externalagent sumir em 23/08.
- **Criar a série de retorno por bot:** requisições/dia · dias desde a última visita · intervalo mediano entre visitas · URLs revisitadas × URLs novas.
- **Alarme por ABANDONO**, não por cobertura parada: bot valioso sem visita há N dias dispara. Hoje `check-crawl-coverage-stall` só sabe dizer que a cobertura parou — e **cobertura parada é compatível tanto com "não achou" quanto com "achou e recusou"**, que são problemas opostos com correções opostas.
- **Classificar cada URL pelo estado que o próprio Google reporta:** `unknown` / `discovered-not-indexed` / `crawled-not-indexed` / `indexed`. **A série que passa a valer é a "fila de recusa"**, e o alarme dispara quando ela cresce.
  **⚠ Limitação medida, e ela vem DENTRO da tarefa, não numa nota adiante:** a Inspection API tem **teto de 10 chamadas/dia** no instrumento disponível. **Classificar as 3.023 URLs nunca pedidas nesse ritmo levaria ~302 dias** — e mesmo a amostra estratificada gira em ~10/dia. **A "fila de recusa" NÃO nasce desse instrumento.** O que ele sustenta é **amostragem estratificada como termômetro** (10/dia, priorizando shards e áreas distintas), e a série de retorno tem de vir da **borda** (`serie_saneada` + `crawl_coverage`), não do GSC. **Registrar isso como limite do desenho, não como promessa a cumprir depois.**

**T7.2 — Dar ao agente um motivo para voltar.** Sem sinal de mudança, um agente que já leu tudo **não tem por que retornar**. Os canais que produzem esse sinal estão todos parados ou quebrados (Fases 1-2). Além de consertá-los:
- **`lastmod` que se move quando a página muda** — hoje **93,1% do acervo (9.582 URLs) declara 2026-08-06 há vinte dias**, e 28 dos 34 shards idem. O contrato do protocolo para `<lastmod>` é *"a página mudou"*, e o portal **não está pedindo recrawl de quase nada**.
- **Feed que serve frescor de verdade** (T2.5), com paginação e `rel="alternate"` para Markdown por entrada.
- **IndexNow vivo e desacoplado** (T1.3) — é o canal de maior alcance real medido.
- **Canal de notícias diário** (Fase 6) — é a única fonte de frescor natural do portal.

**T7.2.b — [MEDIDO POR MIM] Não existe canal incremental: a API ignora todos os parâmetros.**
Sondei `/api/v1/pages` com `limite`, `since`, `cursor`, `area` e `modified_since` — **os cinco devolvem exatamente a mesma resposta de 243 bytes**:

```json
{"version":"v1","count":10070,"item":"/api/v1/pages/{path}",
 "enumeration":"/api/v1/sitemap",
 "enumeration_scope":"todas as URLs indexáveis, incluindo hubs de área e paginação…",
 "enumeration_superset":224}
```

**Não é uma coleção paginável — é um descritor.** Um agente que queira saber *"o que mudou desde X"* **não tem como perguntar**: só lhe resta revarrer o sitemap inteiro, 10.294 URLs.

> **É a peça central do problema de retorno.** O `meta-externalagent` varreu 96,8% do acervo duas vezes e sumiu; o GPTBot ficou em 1 requisição/dia. **Nenhum deles tem um jeito barato de perguntar "vale a pena voltar?".** Criar esse canal — um endpoint com cursor, ou um feed incremental por `changed_at` — é o que transforma revarredura cara em consulta barata, e é o que faz o agente voltar sem custo.

**T7.3 — Transformar leitura passiva em chamada de serviço.** Medição que expõe o problema: **134 requisições a endpoints de protocolo contra 16.539 de Markdown e 2.440 de HTML.** O serviço existe e quase ninguém o chama.
- **Tornar o MCP descobrível de fato:** registrar no MCP Registry (T3.7) — é o único registro público que aceita inscrição e a descoberta hoje **não acontece por varredura da web**.
- **WebMCP na API certa** (T3.6): `document.modelContext.registerTool(...)` faz o browser embutido do ChatGPT **descobrir as ferramentas ao visitar a página** — sem cadastro, sem contrato. É a ponte mais direta entre "bot lê a página" e "agente usa o portal".
- **Anunciar as ferramentas onde o agente já está olhando:** o Markdown é lido 86,5% das vezes e **não menciona que existe MCP, A2A ou busca por API**. Um bloco de front matter com os endpoints (T5.3) converte leitor em cliente.
- **Fechar a conformidade que faz cliente real desistir:** `relatar_defeito` devolvendo 200 em vez de 401 (T3.4), o alias RFC 9728 (T3.5), e erro em HTML para cliente JSON (T3.3).

**T7.4 — Medir citação, não só rastreio.** Rastreio é meio; **citação é o produto**. O único sinal de citação consumada disponível hoje é o **`utm_source=chatgpt.com`** da OpenAI, que **funciona no portal e não é contado** (M24.a, T4.7). Contá-lo é a primeira métrica honesta de retorno com valor.

**Critério de aceitação desta fase — e da sessão inteira:** o sucesso **não** é "cobertura subiu". É **bot valioso com visitas recorrentes ao longo de semanas**, e **chamadas de serviço crescendo**. Se depois das correções o Googlebot continuar em ~30 requisições/dia e o PerplexityBot em zero, **o plano não funcionou**, por mais bem formada que cada página esteja.

---

### FASE 8 — As lacunas que eu declarei como tarefa e não virei tarefa *(criada pelo red-team O43)*

> ### 🔴 Por que esta fase existe, e por que ela quase não existiu duas vezes
>
> **Primeira falha:** eu escrevi *"Lacunas ALTAS que entram como tarefa"* em O42 e **criei ZERO tarefas** — o red-team fez o grep e a lista era constrangedora. **Entre as esquecidas estava a QUEIXA-MANCHETE DO DONO:** as **185 rotas `/pagina/N/` sem Markdown**. A única aparição em formato de tarefa estava no **anexo superado**, com a correção **errada** (*"gerar Markdown para paginação"*), já refutada por O20.
>
> **Segunda falha, um nível acima:** as tarefas T8.1–T8.9 nasceram **dentro da narrativa do O43** e **não como fase da seção executável** — o plano saltava de FASE 7 para FASE 9. **Quem executasse a sequência (ou gerasse o frontboard a partir dela) pularia a queixa-manchete de novo.** É a mesma classe de falha, reintroduzida na camada de cima: a tarefa foi criada, mas fora de onde o executor lê.
>
> **Fica registrado como precedente:** *achado que vira tarefa tem de virar tarefa NA SEQUÊNCIA DE EXECUÇÃO, não em parágrafo de diagnóstico.* É o R7 do Contrato do Dado Real aplicado ao próprio plano.

**T8.1 — [A QUEIXA-MANCHETE] As 185 fatias de paginação anunciam o Markdown do HUB, não um `.md` próprio.**
- **O defeito, medido:** `Accept: text/markdown` numa fatia `/area/pagina/N/` devolve **200 `text/html` calado** (M2, armadilha A3); `/area/pagina/N/index.md` devolve **404 no Go** (O23), e **as 185 rotas não anunciam nenhum `alternate`**. **M23 as elevou de "1,8% de rotas" a "buracos no canal principal"** — o canal que 86,5% dos bots de IA consomem.
- **A correção é a de D-4, e é a ÚNICA compatível com o contrato:** `map $wj_link_alt` faz a fatia apontar o `Link: rel=alternate` para o **índice Markdown do hub**, e o `llms.txt` **deixa de prometer o que não existe**.
- **PROIBIDO `301`** — *"redirect como solução; URL existe = conteúdo existe"* (D-4). **PROIBIDO gerar `.md` de paginação** — refutado por O20 (a exclusão é deliberada e corrige uma duplicação já medida).
- **Verificar:** `Accept: text/markdown` numa fatia **nunca devolve HTML calado** · o `llms.txt` não promete `.md` para as 185 · as **28 rotas `/{area}/pagina/`** continuam **com canonical ao hub, fora do sitemap, e com o corpo idêntico ao do hub**. *(Este contra-teste dizia "continuam `noindex`" enquanto T0.7 existia; T0.7 foi **derrubada por medição** — ver o REGISTRO DA EXECUÇÃO —, e exigir `noindex` aqui contradiria a emenda de 2026-08-07 do `CLAUDE.md`.)*

**T8.2 — `og:image` ausente em 100% do acervo.** `grep -rl 'og:image' public/` retorna **zero** em 10.299 arquivos, e `internal/seo/seo.go:186-188` documenta a decisão. **Degrada de uma vez LinkedIn (exige og:image), WhatsApp (absoluta, <600 KB, ≥300 px) e `facebookexternalhit` — que faz 298 req/dia.** Junto: `twitter:card` sai de `summary` para `summary_large_image`.
- **Sem hardcode (R13):** imagem **derivada do dado da página** (área, título, identidade editorial), nunca literal por rota.
- **Verificar (contra-teste):** HTML continua **≤ 50 KB** · o peso adicional é **declarado em bytes no commit** · conteúdo completo no primeiro response · **red-team Fable obrigatório** (G4) — toca o `<head>` do acervo inteiro.

**T8.3 — [SEGURANÇA] O forjador sonda `169.254.169.254`.** **Não é abuso de tier: é endereço de metadados de nuvem — tentativa de SSRF/credencial.** Eleva M11/M26 de "forjar UA para ganhar rate limit" para **incidente de segurança**.
- **Fazer:** bloquear o padrão na borda (`ops/cloudflare/waf-custom-rules.json`, versionado) **e verificar por leitura de código que o portal não tem nenhum caminho que alcance esse endereço**.
- **Verificar:** o bloqueio não atinge bot legítimo (contra-teste sobre a allowlist de T4.5).

**T8.4 — [PRÉ-REQUISITO DE T4.2] Submeter ao Fable as NOVE famílias da onda 1 que nunca passaram por refutação.** O crítico da onda 1 **só recebeu 3 de 12** (Google, Microsoft, OpenAI) e foi **truncado no meio de uma frase** — e o plano tratava O19 como se a crítica tivesse coberto tudo. **Mexer no registry com nove famílias sem crítica é exatamente o que esta sessão passou inteira evitando** (a armadilha do grupo nomeado que descarta o curinga, T4.1, saiu de uma dessas críticas).

**T8.5 — Auditar o acervo contra `noarchive` e `nocache`.** *"Qualquer um dos dois corta o portal das respostas do Copilot sem afetar o ranking orgânico"* — e **não aparece em nenhum gate atual**. **Zero ocorrências no plano até o O42.** Fonte: `bing.com/webmasters/help/robots-meta-tags-…`.

**T8.6 — As 5 institucionais entram no `llms.txt`.** `/sobre/`, `/metodologia/`, `/fontes/`, `/aviso-legal/`, `/privacidade/` — **medido: zero ocorrências hoje**, e são **as páginas que provam autoria, método, proveniência e limites de uso**, isto é, as que um modelo leria para decidir se confia na fonte. **M24 chamou de "correção de minutos" e não virou task.**
- **Sem hardcode:** a lista sai de `content/pages.json`, nunca de literal.
- **Cruza com T0.6/O32.e:** **sete institucionais indexáveis não têm linha no `published_manifest`** e a API responde 404 nelas — **a mesma família de defeito, dois sintomas.**

**T8.7 — Os 5 `check-*` sem nenhum caminho de saída ≠ 0 — e dois deles guardam COLISÃO DE ROTA PÚBLICA.** **Gate que não pode reprovar é pior que gate ausente: produz confiança falsa** (é a regra 3 da seção de looping de gate). **Depende de T0.9.**

**T8.8 — Leitor canônico de `crawl_coverage_daily.jsonl`, e a origem do número órfão.**
- O arquivo **é cumulativo e não tem leitor canônico**: `googlebot/2026-08-12` tem **21 linhas**, e `paths_requested_that_day` assume `{0, 7, 8, 13, 40, 103}` — **103 é 2,6× o correto porque conta por string de UA, somando as sondas do próprio repositório**. **É a armadilha A1 numa segunda fonte**, e pede o mesmo `serie_saneada` que o ledger de borda já tem.
- Junto: achar a origem do **`total_indexado: 10.077`** que o MCP devolve — **o único número realmente órfão** (não bate com 10.070 nem com 10.294).

**T8.9 — `meta-externalads` no registry, e o DOU inalcançável.**
- **`meta-externalads` está documentado pela Meta e não existe no registry** — o portal não governa o crawler de publicidade de quem faz **45% do seu tráfego de bot**. *(E a Meta **não publica lista de IP nenhuma**: `meta-externalagent` fica fora do método de verificação por faixa — limitação a declarar, não a esconder.)*
- **O DOU responde `PROTOCOL_ERROR` em HTTP/2 (curl 92) e "Empty reply from server" em HTTP/1.1 (curl 52), com DNS resolvendo** — `in.gov.br/leiturajornal` e `inlabs.in.gov.br`. **Investigar o caminho de rede antes de desistir da fonte**, num plano cuja R17 exige legislação nova todo dia.

**Regra que vale para as nove:** onde a tarefa não traz "como verificar" explícito, **o passo 1 do PROTOCOLO (medir antes) define o critério**, e a tarefa **não sai de `medindo-antes` no frontboard enquanto o critério não estiver escrito**.

---

### FASE 9 — Dependências e cadeia de suprimento *(da onda 8 e da crítica O45)*

> **Ordem sua:** *"Se no repo tem 202 dependências, elas podem estar com bugs, e deve corrigir ou integrar… corrigir os bugs das dependências e pode colocar em backup os que não são necessários… integrar algum código Go que possa ajudar."*

**T9.1 — 🔴 As quatro vulnerabilidades vivas, e o toolchain junto.**
`x/mod` v0.37.0 → **v0.40.0** (GO-2026-6179, GO-2026-6180) · `x/image` v0.43.0 → **v0.45.0** (GO-2026-6222, CVE-2026-46603) · **GO-2026-5932**.
**E o que os cinco agentes perderam (O45): o toolchain `go1.26.5` está DENTRO da faixa — `fixed 1.26.6`.** Baixar `go1.26.6` para `.toolchains/` **junto** com o bump.
**Verificar:** `govulncheck` limpo **nas quatro**; **e o contra-teste é o boot** — bump de `x/mod` toca verificação de módulo, então o build tem de fechar antes de promover.

**T9.2 — 🔴 O gate de vulnerabilidade não tem cor conhecida há 28 dias.** A leitura precisa (O45): **não é que ele "replaya" — é que nenhuma execução produziu veredito memoizável desde 29/07**, enquanto os irmãos têm memo de hoje. **Fazer o `sca-osv` rodar e persistir evidência**, e **renovar as 5 exceções expiradas em 2026-07-30** — **o detector de expiração já existe** (`sca_ignore_policy_ignore_until_expired`). **E `govulncheck` está pinado em v1.5.0 contra v1.7.0 atual.**

**T9.3 — 🔴 O remoto está 2.332 commits e 77 dias atrás — Dependabot e CodeQL nunca viram o código atual.** *(Confirmado pelo crítico: `git rev-list --count origin/main..HEAD` = 2332.)* **Sem isto, todo gate de supply chain audita um repositório fantasma.** Junto: **`/tools/perf` e `/tools/duckdbolap` estão fora do Dependabot — e são onde estão as vulnerabilidades** — e **o gate que deveria pegar isso tem lista fixa**.

**T9.4 — 🔴 `json-iterator` está arquivado, no binário público, com 19 call sites.** *(19, não 21 — arbitrado.)* Migrar para `jsoncodec.Unmarshal` (`goccy`), **que já é o `PrimaryJSONModule` do próprio wrapper**, mantendo `UnmarshalIterator` como **alias durante a transição**. **Semanticamente segura** porque o jsoniter roda em `ConfigCompatibleWithStandardLibrary`. **Só remover do `go.mod` depois de os testes dos pacotes tocados passarem.**

**T9.5 — 🔴 Golden test para o SHA-256 do `contentstore`.** É o achado que **sobreviveu** à crítica: o hash de integridade é função dos **bytes exatos do `goccy`** (`:623`) e o dado é decodificado por **`json-iterator`** (`:627`), **sem nenhum teste que fixe esses bytes**. **Uma atualização do codec muda o hash de integridade sem ninguém perceber.** *(O achado irmão — "dois codecs sobre `pages.json`" — foi rebaixado: a própria medição deu 0 duplicadas e UTF-8 limpo.)*

**T9.6 — SBOM e evidência.** O SBOM commitado tem `timestamp 2026-07-02`, **171 componentes**, e **faltam 13 das 74 diretas, com 5 versões erradas** — **21,6% dos pares `module@version` sem cobertura**. **E o `sca-govulncheck` não persiste evidência nenhuma: a única prova de que rodou é uma mensagem de commit** — que esta sessão já mediu mentir.

**T9.7 — Atualizações sem CVE, priorizando o binário público.** 37 diretas atrasadas em minor/patch — **`RoaringBitmap` está 14 releases atrás, dentro do binário**. **`gofeed` v1.3.0 → v1.4.2.** **E as duas linhas major de `ristretto` no mesmo build** (v0.2.0 direta + v2.2.0 indireta).

**T9.8 — O que fica, o que vai para backup, e o que NÃO se toca.**
- **NÃO REMOVER `segmentio/encoding` nem trocar `sha256-simd`** — os fatos são verdadeiros (zero chamadores; pass-through numa CPU sem `sha_ni`), **mas os fixes violam "deletar para resolver" e ZERO REGRESSÃO**. **Adjudicação única (O45): manter, com o teste que pina o contrato.**
- **NÃO MOVER `searchsidecarclients`** — **não compila**: três pacotes o importam de verdade.
- **NÃO INSTALAR Meilisearch** — contradiz o ADR de probe-bank e **duplicaria o Bleve, que serve busca viva** (`/buscar/?q=pensao` = **200**, medido).
- **Backup dos três clientes de busca** só **se** o benchmark já respondeu — e essa é a pergunta a fechar, não a assumir.

**T9.9 — ADRs: 1, não 18.** A varredura cruzou só `docs/adr/` e **ignorou `internal/codex2policyenforcement/policy.go`**, onde o `goccy` tem registro completo **com `BenchmarkEvidencePath` que existe no disco**. **Resíduo comprovado: só `otel` está sem registro.** **Os outros 16 precisam ser lidos um a um antes de qualquer ADR novo — escrever 18 retroativos criaria duplicados.**

**T9.10 — Higiene que distorce toda medição por grep.** **`.git/codex-private-go-cache/` espelha ~100 módulos de terceiros dentro do `.git`** (legado do Codex), além de `.cache/gate-build` e `.cache/dead-tmp-quarantine`. **Morde qualquer `grep -r` na raiz — inclusive os meus desta sessão.** Excluir por padrão em toda ferramenta de auditoria.

**T9.11 — Apontar os instrumentos que já existem para o alvo certo.** *(A onda 8 mostrou que o trabalho aqui não é instalar — é usar.)*
- **Validador de JSON-LD: existe e nunca foi apontado para o site** — a evidência cobre **360 registros de ensaio de 01/07** contra **10.294 páginas reais**.
- **Vegeta está integrado** e a única evidência mede **rota de ensaio anterior à publicação**.
- **Verificação de bot por IP já existe** com DNS reverso + direto (`gaissmai/bart` + `miekg/dns`) — **nada a instalar**.
- **`fgprof`/`pprof` estão ociosos** e há cauda de latência não reproduzida.

**T9.12 — Tokenizador: `tiktoken-go/tokenizer` v0.8.1 (MIT), restrito a gerador OFFLINE.** **`pkoukk/tiktoken-go` desqualificado** por baixar vocabulário em runtime. **Nunca no caminho de resposta.** Corrige **dois** divisores chutados: o meu (`bytes/4` em M15.a) e o do repo (**`estimateInputTokens` usa `len(json)/4` e alimenta um ledger de CUSTO**).

**T9.13 — Web Bot Auth: adiado com razão medida, não por preguiça.** **`cloudflare/web-bot-auth` é RUST — não importável em Go**, e o verificador **alcançaria só 3,95% do tráfego**. **A decisão é de colocação, não de biblioteca.** **E o log ainda não captura `Signature-Agent`** — instrumentar primeiro.

**T9.14 — 293 páginas publicam JSON-LD `HowTo`, cujo rich result o Google removeu em 14/09/2023** — **1.149.327 bytes de marcação sem retorno possível**. Remover ou substituir pelo tipo que ainda tem elegibilidade.

**T9.15 — Itens menores, medidos:** **OpenTelemetry cria um span por requisição no caminho quente, sem `TracerProvider` e sem exportador** — custo com zero observabilidade · **`pages.json` (72,9 MB) é lido inteiro sem modo estrito**, embora o facade ofereça a variante · **não existe `vendor/`**: o build offline depende de um cache de **18 GB fora do git e sujeito a GC** · **`GOTOOLCHAIN=auto`** permite download silencioso no caminho interativo · **`CLAUDE.md` diz go1.26.4 e o `go.mod` diz go1.26.5**.

**✅ E o que a medição encontrou SADIO, para não ser "consertado":** `go.sum` cobre **564/564** · **`go mod verify` passa** · **zero `replace`/`exclude`/`retract`** · **nenhuma variável desliga verificação** · **zero chamadas de rede em `init()`** (188 arquivos varridos) · **zero workaround de bug de dependência no código** · **self-hosted first não violado** (três instrumentos).

---

### Hipóteses que a medição NÃO sustentou — e por que nenhuma delas é "vitória"

> **Ordem do dono nesta sessão:** *"Não declarar nada vencido no plano. Pois eu li algumas vitórias suas, que podem ser mentira do repo… ou agente pode ter se enganado."*
>
> **Ele está certo, e a própria sessão prova o ponto.** Uma mensagem de commit afirmou defeito em produção que **nunca esteve no ar**, e eu construí uma hipótese inteira em cima dela. Comentários de código mentiram três vezes. Um agente errou a própria contagem (57 → 47) e se corrigiu. **Portanto:**
>
> - Cada linha abaixo é **"não sustentado pela medição de 2026-08-26, por tal instrumento"** — **não** é "está correto".
> - **Toda uma delas volta a ser verificada na execução**, depois do rebuild (o binário está 18 commits atrasado, então parte do que sondei descreve o passado).
> - Onde houver **um só instrumento**, está escrito. Instrumento único não fecha nada.
> - **Nenhum item desta tabela autoriza pular uma verificação.** Ela existe para não gastar trabalho na direção errada, não para declarar terreno conquistado.

| Hipótese | O que a medição de 2026-08-26 mostrou | Instrumentos |
|---|---|---|
| `llms.txt` diz 10.070 e o sitemap 10.294 → divergência | **Refutado.** 10.070 + 185 + 38 + 1 = 10.294. O portal já declara em `/api/v1/pages`. |
| "Muitos `.md` sem conteúdo" | **Refutado.** n=120, mínimo 4.250 B, mediana 6.234 B, zero abaixo de 2.000 B. |
| `lastmod` do sitemap é mentiroso/uniforme | **Refutado.** 28× 06/08, 3× 20/08, 1× 07, 1× 12, 1× 13 — fiel ao dado. |
| Bot Fight Mode / WAF / rate limit barrando bot valioso | **Refutado — mas atenção à evidência que sustenta.** O log do nginx (17× 403, zero 429) **não basta**: challenge da Cloudflare nunca chega ao nginx, e usá-lo como prova seria a armadilha A2 aplicada a mim mesmo. **O que sustenta de verdade:** a série `crawl_coverage_daily` é medida **na borda** por `cloudflare_verified_bot_category` e mostra o Googlebot chegando ~30×/dia; e o GSC responde `Page Fetch: SUCCESSFUL` e `Robots.txt: ALLOWED`. **Dois instrumentos que enxergam a borda, não a origem.** |
| Fontes oficiais apontam home de órgão | **Refutado.** 82,6% apontam documento específico; 0,6% apontam raiz. |
| `/.well-known/http-message-signatures-directory` faltando é defeito | **Refutado.** Esse diretório é de quem **assina** requisições de saída, não de quem as recebe. |
| `/api/search` faltando | **Refutado.** A busca por API existe e é descoberta; o defeito é o 404 dela responder HTML. |
| Pré-gerar `.md` em `public/` faria a borda cachear | **Refutado.** O HTML **já** está em disco e também é DYNAMIC. E pré-gerar **regrediria** o ETag (conteúdo → mtime-tamanho). |
| Bingbot desperdiça rastreio em busca interna | **Refutado por mim.** 0% de requisições a `/buscar/` ou com query string. |
| `UA "Googlebot"` no código de release é fraude | **Refutado por mim.** É `httptest` em memória, sem rede. |
| "Bing tem mais alavancagem que Google" | **Derrubado.** Volume de crawl não é valor, e o elo com o ChatGPT era "sem fonte oficial". |
| Teto de 50 KB por página violado | **Refutado.** Zero violações em 10.299 arquivos; maior página 36.937 B. |
| Aquecimento interno forja UA de bot real | **Refutado.** Anti-fraude LIMPO, verificado em todo o histórico do log. |
| `Vary: Accept` causa o `DYNAMIC` | **Refutado por experimento.** `/llms.txt` tem só `Accept-Encoding` e é DYNAMIC; `/robots.txt`, igual, é HIT. |

---

## Anexo — Achados por ROI (redação anterior, mantida para rastreabilidade)

### P0 — `If-Modified-Since` do HTML viola a RFC e anula toda revalidação

**Evidência:** M6.b. Data posterior ao `Last-Modified` devolve 200 com corpo inteiro; só igualdade exata devolve 304. O caminho do Markdown, no mesmo servidor, está correto.
**Custo medido:** 0,2% de 304 em 418.071 requisições (M18). Não é banda — é **orçamento de rastreamento e token do agente**: com o Googlebot a 33 requisições/dia, cada corpo inteiro devolvido desnecessariamente é uma página nova que ele deixa de buscar.
**Correção:** comparação `last-modified <= if-modified-since` (RFC 9110 §13.1.3) no handler HTML, mais teste de regressão com as quatro datas de M6.b. Reaproveitar a lógica já correta do caminho Markdown.

### P0 — Borda nunca cacheia: `cf-cache-status: DYNAMIC` em todo artefato

**Evidência:** M6.a, medido três vezes em HTML e uma em Markdown, `llms.txt` e `sitemap.xml`.
**Custo:** 100% do tráfego de bot atravessa o túnel até a origem. É a causa material de o portal ser "caro" para bot, e amplifica o P0 anterior.
**Correção:** Cache Rule de borda cobrindo conteúdo (não só descoberta — ver `[[purga-borda-alcance-real]]`), com verificação medida de `cf-cache-status` virando HIT, e purga por tag na transação de publicação. Antes de aplicar, red-team Fable: mexer em cache de produção é caro de reverter, e há precedente de erro aritmético apanhado nessa exata frente.

### P0 — Os bots que citam não conhecem o acervo

**Evidência:** M4. PerplexityBot 0,00%, ChatGPT-User 1,98%, OAI-SearchBot 9,22% de cobertura.
**Leitura:** é a tradução técnica de "não tem autoridade nenhuma". Não se cita o que não se leu.
**Correção (engenharia, não marketing):** canal de descoberta que esses agentes efetivamente consomem — `llms.txt` navegável e paginado em vez do monólito de 1,4 MB, feeds por área com frescor real, `lastmod` verdadeiro por página, IndexNow/WebSub verificados por medição, e superfície de leitura barata (Markdown) descoberta a partir de cada porta de entrada. A onda 1 traz o que cada fornecedor declara oficialmente consumir; sem doc oficial, não se inventa mecanismo.

### P1 — 185 rotas de paginação sem Markdown, e negociação que mente

**Evidência:** M2. `Accept: text/markdown` devolve 200 `text/html` nessas rotas — falha silenciosa, o pior tipo para um agente.
**Correção:** gerar Markdown para as rotas de paginação (são índices, o Markdown é trivial e barato), **e** corrigir a negociação para nunca devolver HTML calado quando Markdown foi pedido. Somar as formas alternativas de M2 (`/slug.md`, `?format=md`) como aliases resolvidos, não como 404.

### P1 — 6 agentes com tráfego real fora do registry, e verificação de identidade ausente

**Evidência:** M3 (fora do registry: `semrushbot`, `yandexbot`, `ahrefsbot`, `cloudflare-agentreadiness`, `chrome-lighthouse`, `google-inspectiontool`) e M11 (a política é aplicada por User-Agent cru, sem verificação — `requests_local_verification: 0`).
**O que os números dizem:** SemrushBot faz **1.163 req/dia, 35× o Googlebot**, e não indexa nem cita. YandexBot faz 153/dia com **99,28% de cobertura do acervo** — o crawler que melhor conhece o portal está no grupo curinga. `google-extended` recebeu 42 requisições e 42 × 404 — como não é crawler, é falsificação por definição.
**Correção:** (a) classificar os 6 por **função** com política própria; (b) **verificar identidade antes de conceder tier** — reverse DNS e faixas de IP publicadas (`data/ops/bot_ip_ranges/` já existe para o Google) e/ou Web Bot Auth, para que declarar-se "ChatGPT-User" deixe de bastar para receber acesso ilimitado; (c) fechar o buraco de enforcement que a onda 2 está localizando no código.

### P1 — 404 caro e rotas de agente quebradas

**Evidência:** M7 e M1. Todo erro custa 7.521 bytes ao bot, com CSS inline e um `<script>` que ele não usa.
**Correção:** resposta de erro leve por negociação de conteúdo (Markdown/JSON curto para quem não pediu HTML), e criar o que falta: `/api/search` (hoje um agente não consegue buscar sem MCP), e os artefatos de `.well-known` que clientes reais procuram — conforme o que a onda 1 confirmar em spec oficial, sem criar arquivo-fantasma só para ter 200.

### P2 — Números divergentes em artefato público e `Last-Modified` por lote

**Evidência:** M8 e M6.d. `llms.txt` publica 10.070 contra 10.294 do sitemap e 10.299 do disco; datas por lote, não por página.
**Correção:** número derivado de uma fonte única no momento da geração, e `Last-Modified`/`lastmod` reais por página, vindos do manifesto editorial.

---

## O que ainda falta apurar antes de fechar o plano

1. Retorno das duas ondas e das duas refutações Fable — em especial: onde vive o enforcement de rate limit, por que a paginação não tem Markdown (`arquivo:linha`), estado real de MCP/A2A sob chamada verdadeira, o que o JSON-LD já emite, e se há Bot Fight Mode / WAF / Cache Rule na borda.
2. Quais bots relevantes faltam no registry segundo **documentação oficial** — a onda 1 responde com URL e data; nada entra por blog.
3. Quais padrões de superfície de agente têm **consumidor comprovado** e quais estão mortos — para não gastar engenharia em artefato que ninguém lê.
4. Causa da queda de 90% nas impressões do GSC (M5) cruzada com a cobertura de M4.

Cada item acima já tem agente em voo ou sonda definida. Nenhum deles bloqueia a execução dos P0, que estão medidos e prontos para correção.
