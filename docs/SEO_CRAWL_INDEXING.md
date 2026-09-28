# SEO_CRAWL_INDEXING.md

## Indexacao

Toda pagina com `status != published` ou `index_policy != index` recebe `noindex,follow` e fica fora de sitemap.

Para página jurídica, `status=published` e `index_policy=index` nunca bastam isoladamente. A entrada em sitemap e indexação exige registro correspondente em `published_manifest`, fonte oficial específica auditada, revisão jurídico-editorial/OAB, paid-intent/CTA classificado por intenção/ética ou classificação informativa explícita, qualidade/anti-template em lote, canonical/robots/sitemap coerentes, HTTP smoke/Googlebot, HTML leve e release gate completo. Sem essa cadeia, a página reprovada aciona correção executável mesmo que algum campo local pareça publicável. O objetivo deste `/goal` inclui construir essa cadeia até páginas públicas reais; reprovação correta protege qualidade, mas não autoriza parar em diagnóstico quando houver próxima camada executável.

Pedido explícito, contrato vivo, checkpoint, roadmap, pergunta de engenharia e achado integrado de agente exigem execução verificável do `/goal` ativo, não comentário, recomendação ou fase posterior. Todo requisito executável pertence a este `/goal`. Em SEO/crawl, cada diagnóstico deve virar correção, check, smoke, manifesto/transação preparada, prova de HTML leve, sitemap/canonical/robots coerentes, publicação aprovada com gate completo e correção executável das páginas reprovadas. Verde técnico sem leitura de conteúdo e sem próxima camada executada é passividade.

Toda pagina indexavel precisa de:
- HTML textual completo;
- HTML leve, sem runtime cliente, sem hidratacao, sem bundle e sem CSS inline excessivo (JavaScript: ver a emenda de 2026-08-19 mais abaixo — um unico script inline de integracao de agente, autorizado por hash);
- `<title>` unico;
- meta description unica;
- canonical absoluto;
- meta robots `index,follow`;
- links internos rastreaveis;
- conteudo util e nao duplicado.

Googlebot e bots de IA devem encontrar no primeiro response o mesmo conteúdo útil que o humano recebe: texto principal, canonical, robots, links internos e sinais editoriais não podem depender de execução cliente desnecessária. A otimização para rastreadores deve ser consequência de boa engenharia de página, não substituto para conteúdo jurídico útil. Página pesada, dependente de renderização cliente ou com custo alto de CPU para crawler é regressão P0, mesmo que o conteúdo pareça correto.

## URL base oficial

O dominio oficial do projeto e `wikijuridica.com.br`. `content/site.json` deve declarar `base_url="https://wikijuridica.com.br"`, `base_url_mode="official_configured"`, `official_url_status="locked"` e `official_url_locked=true`.

Os testes devem validar base HTTPS, canonical absoluto, path limpo e correspondencia entre canonical e rota usando a base configurada. Eles nao devem voltar a `portal-juridico.example` nem hardcodar dominio de laboratorio no algoritmo. URL oficial travada nao libera publicacao: candidatos e pre-publicacao continuam `noindex` e bloqueados ate fonte, revisao, qualidade, CTA, sitemap e manifesto publico finito passarem.

## Orcamento de HTML

Pagina publica indexavel deve ser facil de rastrear. O contrato atual reprova HTML publico acima de 50 KB, referencias `.js/.mjs/.wasm`, `modulepreload`, import maps, payloads de framework e marcadores de hidratacao.

**Emenda de 2026-08-19 sobre `<script>`.** Ate esta data o contrato reprovava QUALQUER `<script>`
executavel. Por ordem do dono, JavaScript leve passou a ser permitido quando serve integracao de
agente de IA. Hoje existe exatamente UM script no HTML publico: o registro de ferramentas WebMCP
(`internal/webmcp`), 1.095 bytes, inline, que expoe ao agente dentro do navegador as duas
capacidades que o portal ja oferece por MCP e por REST. A permissao e estreita e verificada em
quatro camadas — `internal/htmlcontract`, `internal/htmlpolicy`, `internal/checks` e a CSP —, e em
todas o criterio e IGUALDADE BYTE A BYTE com `webmcp.Script`: qualquer outro script, ou uma
variacao de uma virgula deste, continua reprovando. A CSP autoriza por hash sha256 derivado do
proprio corpo, nunca `unsafe-inline`. O que NAO mudou: o conteudo continua completo no primeiro
response, sem hidratacao — nenhum leitor sem JavaScript perde nada. O objetivo e manter o primeiro response barato, textual e previsivel para Googlebot, OAI-SearchBot e bots valiosos. É regressão deslocar custo pesado de CPU, renderização, parsing ou hidratação para rastreadores; o runtime público deve servir HTML simples e completo.

## Orcamento de Search appearance

Pesquisa oficial feita em 2026-06-09 na Central da Pesquisa Google:
- Conteudo util para pessoas: `https://developers.google.com/search/docs/fundamentals/creating-helpful-content`
- Crawling e indexing: `https://developers.google.com/search/docs/crawling-indexing`
- Canonicalizacao: `https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls`
- Robots meta: `https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag`
- Links de titulo: `https://developers.google.com/search/docs/appearance/title-link?hl=pt-BR`
- Metadescricoes/snippets: `https://developers.google.com/search/docs/appearance/snippet?hl=pt-br`
- Requisitos tecnicos minimos: `https://developers.google.com/search/docs/essentials/technical`

Pesquisa oficial complementar feita em 2026-06-12 na Central da Pesquisa Google:
- Conteúdo útil e confiável para pessoas: `https://developers.google.com/search/docs/fundamentals/creating-helpful-content`
- Orientação sobre conteúdo gerado com IA: `https://developers.google.com/search/docs/fundamentals/using-gen-ai-content`
- Políticas de spam, incluindo abuso de escala e keyword stuffing: `https://developers.google.com/search/docs/essentials/spam-policies`
- JavaScript SEO e fila de renderização do Googlebot: `https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics`
- Googlebot, mobile-first e limite de fetch HTML: `https://developers.google.com/search/docs/crawling-indexing/googlebot`
- Sitemaps para sites grandes/complexos: `https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview`

Pontos contratuais:
- o Google informa que nao ha limite fixo oficial para tamanho de `<title>`;
- o Google informa que nao ha limite fixo oficial para metadescricoes;
- ambos podem ser truncados conforme a largura do dispositivo;
- Googlebot precisa conseguir acessar a pagina, receber HTTP 200 e encontrar conteudo indexavel que nao viole politicas de spam.
- conteudo criado principalmente para manipular ranking, raso, mecanico, massificado ou sem valor adicional deve ser tratado como falha editorial antes de virar URL.
- automação editorial só é aceitável quando melhora acurácia, qualidade, relevância e valor para usuários; gerar muitas páginas sem valor adicional é falha de contrato.
- sitemap ajuda descoberta em site grande, mas não garante indexação e não substitui links internos, canonical coerente, conteúdo útil e gates de publicação.
- canonical em HTML, sitemap e links internos devem apontar de forma consistente para a URL preferida; divergência entre sinais é regressão.
- Googlebot pode renderizar JavaScript, mas o projeto deve continuar servindo HTML textual completo e leve no primeiro response para reduzir custo, fila de renderização e risco de conteúdo invisível.
- orçamento formal de title/meta não basta para publicação: duplicidade exata, final truncado por corte mecânico, prefixo genérico em massa e meta/título sem intenção única continuam causas editoriais acionáveis, mesmo quando canonical e robots estão corretos.

Decisao do projeto: usar orcamento conservador interno, contado por caracteres Unicode, para reduzir truncagem e texto ruim:
- `title`: 20 a 65 caracteres Unicode;
- metadescricao: 70 a 160 caracteres Unicode;
- `max-snippet:-1` (sem limite) em paginas indexaveis. **Atencao: o orcamento de 160 vale para title e metadescricao, NAO para o snippet.** O valor unico mora em `internal/editorial/editorial.go` (`MaxSnippetCharacters`), e `internal/seo` so o referencia. O racional: o Google lista `max-snippet` entre os controles que LIMITAM o que pode aparecer em AI Overviews e AI Mode, entao qualquer teto ali reduz a superficie de citacao por assistente de IA — o oposto do objetivo do portal. Verificado no ar em 2026-08-12: as paginas emitem `content="index,follow,max-snippet:-1"`.

Quando nao houver dados atuais suficientes sobre Googlebot, snippets, links de titulo, metadados ou superficie de busca, o agente deve pesquisar a Central da Pesquisa Google no dia da sessao e registrar a fonte consultada.

## Diagnóstico SEO bloqueado por lote

`./tools/check-release-rehearsal-review-seo-readiness` calcula o próximo lote indicado pelo plano editorial e cruza `batch_public_manifest_gates` com `batch_prepublication_gates`. O check é read-only e precisa reportar `approval=false`, `publication=false`, `publication_allowed=0` e `release_ready=0`.

Esse diagnóstico separa coerência mecânica de aprovação pública:
- title/meta dentro do orçamento, canonical HTTPS oficial e robots `noindex,follow` podem estar corretos;
- ainda assim, duplicidade de title/meta, final truncado, texto genérico e ausência de revisão autoral mantêm o lote reprovado para publicação;
- `mechanical_ready_blocked` significa que a camada básica está coerente para continuar o laboratório, não que a URL está pronta para `published_manifest`, sitemap, render ou indexação.

Autocrítica de engenharia: a correção executável é transformar duplicidade e truncamento em correção automática de title/meta por intenção única, validada em lote. É seguro porque o diagnóstico não escreve em `public/`, `content/pages.json` ou JSONL editorial. A otimização é real quando reduz falso conforto de budget verde; ainda há risco de falso negativo em H1 e naturalidade do corpo enquanto esses campos não forem validados por render/final draft.

## Crawl

`content/crawl_policy.json` configura bots. Googlebot, OAI-SearchBot, GPTBot e regra geral sao separados. Busca interna e parametros ficam bloqueados em robots.txt e tambem usam `noindex` quando renderizados.

Robots.txt sozinho nao e usado como substituto de `noindex`.

As regras de bots devem ser inequívocas: `registry_version`, `rate_tiers`, `bot_registry`, `rules` e `access_rules` precisam concordar. Cada `user_agent` aparece uma única vez em `rules`, `access_rules` e `bot_registry`; bots de busca/discovery e fetch iniciado por usuário ficam em `valuable_search_or_user_bot` com `unlimited_no_rate_limit`; bots de treinamento ficam em tier explícito com limite de requisições; e `*` permanece em `unknown_guard_rate_limit`, nunca ilimitado. Regras `robots.txt` para bots valiosos e de treinamento precisam manter `Allow: /` e não podem bloquear a raiz com `Disallow: /`, `/*` ou `/*$`; rate limit de treinamento é política de tráfego, não bloqueio de crawl. A prévia HTTP de release valida essa política antes de aceitar `robots.txt`/sitemap, para evitar que um smoke técnico aprove rate limit errado ou regra ambígua.

## Shard de sitemap retirado do índice tem CARÊNCIA, não remoção imediata

O nome do shard é posicional (`/sitemaps/pages-%04d.xml`) e a partição por (data de revisão, área) faz o **conjunto** de shards mudar sempre que uma coorte nasce, esvazia ou cruza `minCohortURLs`. Isso é aceito de propósito — o ganho de `lastmod` acionável foi medido em 468× —, mas tem uma consequência que custou rastreamento: quando o plano encolhe, o ordinal do fim some.

Medido no access log de 2026-08-13, minuto a minuto:

| hora | evento |
|---|---|
| 13:50:43 | `/sitemaps/pages-0032.xml` responde **200**, 28.876 bytes |
| ~13:55 | a publicação encolhe o plano e o arquivo é removido |
| 13:58:07 | `/sitemaps/pages-0032.xml` responde **410** |
| 14:08:31 | **Googlebot** (66.249.73.97) recebe **410** |

O Googlebot não estava com cache velho: ele leu o índice **verdadeiro**, publicado pelo portal, e caiu num buraco que o portal abriu oito minutos depois. Em 2026-08-12 a mesma mecânica entregou 14 respostas 404 ao Bingbot — `pages-0032..0045`, todas as tentativas dele naquele dia.

A regra, portanto: **shard que sai do índice continua servível por oito dias** (`internal/sitemapgrace`). Ele sai do índice na hora — o índice sempre descreve o plano atual —, mas o arquivo permanece em disco, servido com 200 pelo nginx a quem tenha lido um índice anterior. O prazo é derivado, não escolhido: a borda serve `/sitemap.xml` com `edge_ttl override_origin` de 604.800 s, então um crawler pode legitimamente estar lendo um índice de seis dias atrás; sete dias mais um de margem.

Três propriedades que não se afrouxam:

- **A marca vive dentro do XML**, num comentário entre a declaração e o `<urlset>` — nunca num ledger externo. `publishedmanifest` recusa shard fora do índice e `<loc>` duplicada, e essa validação roda no boot: registro externo que se perdesse transformaria cada carência num portal fora do ar.
- **O reconhecimento é estrito.** Só é carência o arquivo com instante RFC3339 legível, não futuro, e XML que parseia com raiz `urlset`. O que não passar volta a ser arquivo comum, e arquivo comum fora do índice reprova — senão o único guarda de `.xml` estranho em `public/sitemaps/` viraria peneira permanente.
- **O órfão é podado a cada publicação**: `<loc>` que saiu do acervo sai dele também; se esvaziar, é removido na hora (`urlset` vazio é schema-inválido). É o que impede a carência de recriar o cenário "sitemap lista URL 410" que o gate de supersessão combate.

Alongar o prazo seria pior, não melhor: o 410 é justamente o sinal que faz o crawler **parar** de pedir o arquivo, e um 200 perpétuo fora do índice ensina o contrário. Algum 410 tardio continua acontecendo — a memória do crawler dura mais que qualquer prazo razoável. O que a carência elimina é o 4xx de quem leu um índice que o portal publicou.

Verificação: `tools/check-sitemap-shard-grace` (coerência do diretório, roda no deploy) e `tools/check-sitemap-shard-churn` (quantas revisões faltam para a próxima coorte cruzar o piso).

## Continuidade SEO do /goal

SEO/crawl é contrato de publicação, não relatório consultivo. Quando um check de SEO, sitemap, canonical, robots, HTML leve, title/meta ou Googlebot apontar próxima ação, o Codex deve transformá-la em ajuste de gerador, dado, teste, gate ou release evidence no próprio `/goal`. Sitemap só acelera descoberta de URLs já aprovadas; não compensa conteúdo duplicado, artificial, sem fonte, sem revisão, sem utilidade ou pesado para rastreamento.

Search readiness pertence ao caminho de publicação deste `/goal`. Quando title/meta/H1/canonical/robots ou smoke Googlebot ficarem bloqueados, a resposta obrigatória é ler amostras, entender a causa e corrigir gerador, texto autoral, classificador ou teste nos dados reais. Não usar orçamento verde, sitemap de ensaio ou smoke técnico para mascarar conteúdo fraco; também não tratar falha de search appearance como motivo para pausa. A correção deve manter HTML público leve e barato para rastreadores.

## Evidência Prioritária Bloqueada

`./tools/check-priority-release-evidence` valida `data/editorial/priority_release_evidence.jsonl` como ensaio bloqueado de SEO/crawl. O check exige canonical em `https://wikijuridica.com.br`, robots `noindex,follow`, HTML textual leve, ausência de runtime cliente, hash recalculável e smoke Googlebot sem escrever no sitemap real, `public/`, `content/pages.json` ou `published_manifest`.

Esse check reduz risco técnico de HTML pesado e head incoerente, mas não aprova indexação. A próxima decisão precisa ler amostras e contadores vivos: no estado atual, `html_lightweight=198`, `http_smoke=198`, `source_blocked=9`, `paid_blocked=8`, `selected_blocked=181`, `final_sample_reviews=181`, `published_manifest=0` e `publication_allowed=0` significam que a técnica de render/HTTP avançou em ensaio bloqueado, mas fonte específica, paid-intent/assistência pública, aprovação jurídico-editorial algorítmica/Codex auditável e escala ainda impedem promoção real. Não há página jurídica pública aprovada para a meta de 10 mil. O passo seguinte deve virar execução: calcular o déficit público jurídico, operar nova cobertura externa/conector textual ou ampliar conteúdo autoral bloqueado com cadeia completa, e só preparar release público quando todos os gates permitirem, sem confundir smoke técnico ou seleção com aceite público.

## Telemetria de bot é obrigação contínua, e separa TREINO de BUSCA

**A distinção que faltava.** Medir bot por "família" (OpenAI, Anthropic) colapsa dois papéis que decidem coisas opostas. Pela documentação oficial dos dois fornecedores: **GPTBot** e **ClaudeBot** rastreiam para **treinar modelo**; **OAI-SearchBot** e **Claude-SearchBot** são os que governam se o portal aparece **citado numa resposta**. Medido em 2026-08-07: os dois de treino varreram o acervo inteiro no mesmo dia (43.087 e 16.460 requisições estimadas) enquanto os dois de busca somaram **2**. Sob o rótulo de família essa diferença é invisível — e ela é a única que importa para o objetivo do portal.

Por isso: **toda medição de bot grava o User-Agent EXATO**, nunca a família, e classifica por função (`search`, `user`, `training`, `ads`, `diagnostic`, `seo`, `infra`). A tabela é fonte única em `tools/botagents.py`; duas tabelas divergiriam no primeiro agente novo e a série passaria a comparar coisas diferentes sem ninguém perceber.

**Separar agente do mesmo operador também é obrigatório.** Googlebot, GoogleOther, Google-InspectionTool e Chrome-Lighthouse chegam todos do bloco `66.249.*`. Classificar por faixa de IP fez, numa análise desta sessão, o PageSpeed Insights ser contado como Googlebot: 61 hits que eram 13.

**O dado é perecível, e essa é uma restrição de engenharia, não um detalhe.**
- Borda (`httpRequestsAdaptiveGroups`): retenção de **8 dias**, janela máxima de 1 dia por consulta. Dia não capturado é dia perdido para sempre.
- Origem (`/var/log/nginx/wikijuridica/access.log`, movido em 2026-08-11 — ver FASE 2 de `docs/plans/2026-08-11-recuperacao-crawl.md`): antes desta data o arquivo vivia solto em `/var/log/nginx/wikijuridica.access.log` e caía no glob `*.log` de `/etc/logrotate.d/nginx` (do projeto vizinho `/opt/divorcio`, `hourly` + `rotate 14` = **13 h 33 min** de janela, medidos — o prejuízo era observável: a borda registrou 9.662 requisições do GPTBot num dia em que a origem guardava 2). Com subdiretório próprio e `/etc/logrotate.d/wikijuridica` (`daily`, `rotate 30`), a retenção real passa a ser de semanas.

A coleta roda por timer (`wikijuridica-bot-telemetry.timer`, 30 min) e acumula em ledger que não rotaciona. Coletor que lê janela que ENCOLHE grava **incremento com cursor**, nunca total do dia: regravar o total faria a série subcontar conforme o log rotacionasse — mentindo para baixo, justamente no sentido que faria concluir que o bot parou de vir.

**Autenticidade.** Volume sem verificação é alegação: User-Agent é texto livre.

> **Correção de 2026-08-12.** Este parágrafo afirmava que "o plano Free da Cloudflare nega `botScore`/`verifiedBotCategory`". **A premissa era falsa e foi refutada por medição.** `verifiedBotCategory` — a verificação da própria Cloudflare, por rDNS e faixa de IP publicada pelo operador — **funciona no plano Free**, e é o que o esquema `edge_bot_agents_daily_v3` passou a exigir (`tools/generate-bot-agents-daily`, comentário do bump de esquema) — **hoje o esquema é o `edge_bot_agents_daily_v4`**, e a correção seguinte está descrita logo abaixo. A afirmação errada ficou aqui por semanas, num documento de leitura obrigatória, ensinando justamente o hábito que ela deveria impedir: contar crawler por string de User-Agent. É o caso exemplar de por que `docs/ARQUITETURA_FIEL.md` existe e por que comentário e documento **não são fonte** — só o código que executa é.

Na **borda**, portanto, a verificação é `verifiedBotCategory`: linha com categoria vazia significa que a Cloudflare não autenticou aquele cliente (UA forjado ou sonda nossa), e não entra na contagem. Na **origem**, a verificação sai do log, que tem o IP real (`real_ip_header CF-Connecting-IP`), conferido contra as faixas que os operadores publicam (`data/ops/bot_ip_ranges/`, 11 operadores) com rDNS confirmado nos dois sentidos como reserva. Operador sem faixa e sem PTR sai como `unverified`, **nunca** como `spoofed` — não saber não é o mesmo que saber que é falso.

Uma consequência que se perde de vista: bot que a Cloudflare **não verifica** (a Perplexity saiu da lista de bots verificados) aparece como zero na contagem de borda. Zero ali significa **não-mensurável por este método**, não ausência de rastreio — e comparar, no mesmo ranking, bot verificado com bot não-verificável mistura duas coisas diferentes.

> **Correção de 2026-09-02 (esquema `edge_bot_agents_daily_v4`).** O parágrafo acima descrevia um limite que deixou de existir para quem publica faixa de IP. Medido naquela data: o PerplexityBot fazia ~1.200 requisições/dia à borda, **100%** dos `clientIP` dentro dos 8 prefixos oficiais de `data/ops/bot_ip_ranges/perplexitybot.json`, e `verifiedBotCategory` **vazia em 100%** delas. Sob o v3 isso gravava `requests_sampled=0`, e toda a série derivada (`bot_return_daily`, `crawl_coverage`, `check-crawler-error-budget`) lia "nunca veio" e "abandonou" — falso negativo sistêmico para um bot que rastreava todo dia, de dentro da própria faixa que ele publica. O **v4** acrescenta uma segunda consulta, só para o agente que sobrou sem verificação da Cloudflare **e** tem faixa oficial conhecida: pede `clientIP` na mesma janela e reclassifica como *verificado por faixa de IP* o grupo cujo endereço cai dentro do prefixo publicado pelo operador. O que não verificou por nenhuma das duas formas continua nomeado em `requests_sampled_unverified_ua` — **nunca some**, porque não saber continua não sendo o mesmo que saber que é falso. A verificação da Cloudflare e a por faixa de IP são critérios **independentes**, e o registro guarda os dois.

**Anti-inflação.** Requisição com `bot_sim=1` (a simulação que este repositório dispara para conferir o que o bot vê) e warming interno ficam **fora da métrica** e contados à parte, nomeados. Sem isso o Googlebot marcava 61 quando o real era 13, e Applebot, bingbot e PerplexityBot "existiam" sendo que cada hit era um curl deste repositório.

## Superfícies de descoberta e integridade de link

**Link interno tem de ter artefato em disco.** Em 2026-08-07, 28.913 ocorrências de link (27,5% do total) apontavam para destinos que só existiam enquanto o processo Go estivesse de pé — os 29 hubs, as 177 páginas de paginação, os 2 favicons e as 7 páginas institucionais. Com o processo fora, mais de um quarto dos links do portal viraria 404 ao mesmo tempo. `tools/check-internal-link-integrity` mede isso, e a pergunta que ele responde é *o que quebra se o processo estiver fora* — o modo `--estrito` a transforma em veredito: sem sonda, todo destino fora de `public/` reprova.

**Mas "não está em `public/`" nunca foi sinônimo de "não existe"** (corrigido em 2026-09-05). O portal tem rotas que existem e nunca terão arquivo em disco: `/redesocial/` (servida por `cmd/social` na 8091), as gêmeas `.md`, `/api/v1/*`, `/openapi.json` e o `.well-known/`. No modo padrão o gate classifica em três: destino com arquivo em `public/`; destino sem arquivo cuja rota a origem **prova** com 2xx (passa, com a ressalva impressa); e destino sem arquivo nem rota (reprova). A sonda é no **nginx em `127.0.0.1:8088`**, a única superfície que enxerga as duas origens — o modo antigo sondava o Go em `:8089`, que responde **404** a `/redesocial/`, e portanto errava justamente na rota dinâmica que a sonda existia para salvar. Quando a sonda não alcança a origem, ou a origem responde 5xx/429, o gate sai **2 (indeterminado)**: processo parado não é link morto, e o que não se mediu não vira lastro.

**Parâmetro de rastreamento não desindexa.** Ver a emenda em `CLAUDE.md`: `utm_*`/`gclid` servem o mesmo corpo e são consolidados por canonical; `noindex` ali destrói o valor do link em vez de consolidá-lo.
