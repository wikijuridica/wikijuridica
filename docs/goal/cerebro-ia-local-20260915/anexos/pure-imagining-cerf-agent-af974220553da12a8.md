# Colheita: QUAL API OS AGENTES MAIS REQUISITAM — /opt/wiki, 2026-09-15

Todas as medições abaixo foram feitas NESTA sessão, em modo somente-leitura.
Camada declarada em cada linha. "N de M" em toda amostra.

---

## 0. RESPOSTA EM UMA LINHA

A API que os agentes mais requisitam é a **superfície de tema da rede social**:
`/redesocial/tema/{área}/{slug}/` mais suas duas gêmeas de máquina
(`/index.md` e `/feed.xml`). Ela é **12,8% de todo o tráfego da zona**
(11.274 de 88.259 requisições na BORDA, 24 h) e **97,3% de tudo que a rede
social recebe** (85.056 de 87.440 na ORIGEM, 11 dias).

E o que ela devolve hoje é **1.287 bytes de casca**: o corpo do documento diz
"Ninguém perguntou nada sobre este tema ainda".

---

## 1. AS ROTAS, UMA A UMA (leitura de código)

Fonte: `cmd/social/rotas.go` (o único multiplexador do processo — "rota que não
está neste arquivo não existe"), mais as constantes de caminho de
`cmd/social/*.go`. Processo: `wikijuridica-social` em `127.0.0.1:8091`
(socket systemd), proxiado pela `location ^~ /redesocial/` do nginx.

### 1.1 Leitura pública (GET/HEAD; `soLeitura` devolve 405 ao resto)

| rota | o que devolve | origem 11 d |
|---|---|---|
| `/redesocial/tema/{área}/{slug}/` | HTML do tema espelhado do acervo: título, link para a página do acervo, link para a porta da área, lista de dúvidas (hoje vazia), formulário de acompanhar, `<link rel=alternate>` do Atom | **60.247** |
| `/redesocial/tema/{área}/{slug}/index.md` | gêmea Markdown do MESMO objeto — 1.287 bytes medidos | **12.629** |
| `/redesocial/tema/{área}/{slug}/feed.xml` | Atom das dúvidas do tema (`socialconteudo.Atom`, EscopoTema) | **12.180** |
| `/redesocial/tema/{área}/{slug}/pagina-N/` (+ gêmea) | paginação da lista de dúvidas | 7 |
| `/redesocial/area/{área}/` (+ `pagina-N`, + gêmeas) | porta da área: todos os temas da área | 1.178 |
| `/redesocial/` e `/redesocial/index.md` | página inicial da rede | 78 |
| `/redesocial/sitemap.xml`, `/redesocial/sitemap/*.xml` | sitemap próprio da rede, FORA do índice do acervo | 106 |
| `/redesocial/perguntas/`, `/index.md`, `/feed.xml` | feed global de dúvidas (HTML, gêmea, Atom) | 27 |
| `/redesocial/duvida/{slug}/` (+ gêmea, + `feed.xml`) | thread de uma dúvida | 0 |
| `/redesocial/consulta/` + `/index.md` | consulta ao corpus jurídico | 26 |
| `/redesocial/confere/` + `/index.md` | conferidor de citação legal (aceita `?citacao=`) | 33 |
| `/redesocial/tese/` + `/index.md` | painel de tese | 0 |
| `/redesocial/transparencia/` + `/index.md` | relatório da moderação, lido da série JSONL auditada | 15 |
| `/redesocial/cobertura/` + `/index.md` | o que as fontes processuais cobrem (DataJud é histórico) | 20 |
| `/redesocial/antes-de-perguntar/` + `/index.md` | busca no acervo por LOOPBACK HTTP (nunca por import — `internal/socialisolation`) | 19 |
| `/redesocial/publicacoes/`, `/publicacao/{id}/` | mural da comunidade | 17 |
| `/redesocial/perfil/{handle}/` (+ gêmea) | perfil público; contagem de seguidores aparece, LISTA nunca (CED art. 42, IV) | 0 |
| `/redesocial/perguntar/` | tela de abrir dúvida | 23 |
| `/redesocial/conta/*` | cadastrar, entrar, sair, recuperação, **prazo/**, **processo/** | 43 |
| `/redesocial/notificacoes/` | caixa de entrada (privada: `no-store`, `noindex`) | 0 |
| `/redesocial/cursos/` + `/index.md` | vitrine de cursos (só se `content/cursos.json` declarar) | 0 |
| `/redesocial/feed.xml` | Atom do movimento | 4 |
| `/redesocial/llms.txt` | índice de máquina da rede, derivado das constantes de caminho | 0 |
| `/redesocial/midia/{id}` | imagem de post | 0 |
| `/redesocial/assets/css/wj-social-<hash>.css` | folha única, `immutable` 1 ano; a URL exata está na CSP do nginx | 10 |
| `/healthz`, `/readyz` | sonda (`no-store`, `noindex`) | — |

### 1.2 Escrita (POST) — toda sob `/api/v1/redesocial/`

**Por exigência da BORDA, não por gosto**: o WAF bloqueia POST fora de `/api`,
`/mcp` e `/a2a`. Uma rota de escrita em `/redesocial/` tomaria 403 na Cloudflare
antes de chegar ao processo.

| rota | o que faz | origem 11 d |
|---|---|---|
| `/api/v1/redesocial/csp-report` | receptor do `report-uri` das duas CSPs | **743** |
| `/api/v1/redesocial/conteudo/duvida` · `/resposta` · `/seguir-tema` · `/deixar-de-seguir-tema` | escrita do domínio | 0 |
| `/api/v1/redesocial/conta/*` (`cadastrar`, `entrar`, `sair`, `processo/consultar`, `prazo/*`) | conta e ferramentas | 5 |
| `/api/v1/redesocial/moderacao/*` | decidir fila (passa por `moderacao.Decidir`, nunca SQL direto) | 0 |
| `/api/v1/redesocial/denuncia` | denúncia pela web | 0 |
| `/api/v1/redesocial/notificacoes/marcar-lidas` | — | 0 |
| `/api/v1/redesocial/confirmar` | confirmação de e-mail | 0 |
| `/api/v1/redesocial/lote` | **lote de documentos da rede** | **14** (13 de `Neuronto/1.0`) |

---

## 2. MEDIÇÃO — BORDA E ORIGEM

### 2.1 BORDA (Cloudflare GraphQL `httpRequestsAdaptiveGroups`, janela
`2026-09-15T00:47:44Z → 2026-09-16T00:47:44Z`, `sampleInterval ≈ 1,003`)

| superfície | requisições 24 h | % da zona |
|---|---|---|
| **zona inteira** | **88.259** | 100% |
| `/redesocial/%` | **11.274** | **12,8%** |
| `%/index.md` (gêmeas do acervo) | 2.931 | 3,3% |
| `/mcp%` | 1.964 | 2,2% |
| `/api/v1/%` | 555 | 0,6% |
| `/a2a%` | 20 | 0,02% |
| resto (acervo HTML, assets) | ≈ 71.515 | 81,0% |

### 2.2 A DESCOBERTA METODOLÓGICA: a rede social é a única superfície com
telemetria QUASE COMPLETA

`cacheStatus` de `/redesocial/%` na borda, 24 h:

```
expired  5.673   (50,3%)  -> revalida contra a origem
miss     5.116   (45,4%)  -> vai à origem
none       278   ( 2,5%)
hit        194   ( 1,7%)  <-- SÓ ISTO fica na borda
bypass      13
```

**95,7% das requisições à rede social chegam ao processo Go.** Contra-prova pela
origem: `data/ops/access/nginx-2026-09-15.jsonl` registra **11.148** linhas com
`superficie=redesocial` — contra 11.274 na borda. **Travessia = 98,9%.**

No MESMO dia, o acervo registrou **7.234** linhas na origem contra ≈ 74.446 na
borda: **travessia de 9,7%**.

> Consequência de engenharia, e ela inverte a regra da casa: para o ACERVO a
> série de origem é piso (o `HIT` esconde quase tudo); para a REDE SOCIAL a série
> de origem é **quase a população**. É o único lugar do projeto onde se vê,
> requisição por requisição, o que cada agente de IA faz. **Isso é o
> instrumento, não um efeito colateral.**

Causa medida do não-cacheamento: `cacheControlPublico = "public, max-age=600,
s-maxage=3600"` (`cmd/social/rotas.go:27`) contra **11.039 temas** e ~11.000
requisições/dia. Cada tema é pedido ~1×/dia; o TTL de 1 h sempre venceu antes da
próxima visita. Confirmado ao vivo: `cf-cache-status: EXPIRED` no HTML e `MISS`
na gêmea.

### 2.3 ORIGEM — `superficie=redesocial`, 2026-09-05 a 2026-09-16 (11 dias úteis
de série; a superfície nasceu em 05/09)

**87.440 requisições**, 11,45 MB servidos só em 2026-09-15.

Por família de rota:

```
60.247  /redesocial/tema/{a}/{s}/           (68,9%)
12.629  /redesocial/tema/{a}/{s}/index.md   (14,4%)
12.180  /redesocial/tema/{a}/{s}/feed.xml   (13,9%)
 1.178  /redesocial/area/
   763  /api/v1/redesocial/*
   443  todo o resto somado
```

Por agente (`agent_key` do nginx):

```
28.474  gptbot            (32,6%)
26.834  nao_identificado  (30,7%)
10.589  amazonbot
10.225  semrushbot
 6.997  perplexitybot
 2.127  oai-searchbot
 1.002  applebot
   699  yandexbot
   190  cloudflare-ai-search
   113  petalbot · 104 mj12bot · 39 ahrefsbot · 24 meta-externalagent
    11  bingbot · 8 dotbot · 2 facebookexternalhit · 1 googlebot
```

Status: 85.395 × 200 · **1.297 × 404** · 743 × 204 · 4 × 303 · 1 × 301.

### 2.4 OS 30,7% "NÃO IDENTIFICADOS" — o registro de bots tem buraco

Top user-agents sem `agent_key`, dos 26.834:

```
8.485  meta-externalads/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)
7.008  ...Chrome/126.0.0.0 Safari/537.36 (compatible; AionBot/1.0)
  951  Baiduspider/2.0  (+154 Baiduspider-render)
~9.900  Chrome de 14 versões distintas, 636–720 req cada, perfeitamente distribuídas
```

- `meta-externalads/1.1` e `AionBot/1.0` são **agentes declarados** que o
  registro não conhece — 15.493 requisições (17,7%) invisíveis a toda métrica
  por agente.
- A cauda de Chrome em 14 versões com contagens quase iguais (636–720) é assinatura
  de **rotação de UA**, não de 14 pessoas. Não medido: a qual operador pertence.

### 2.5 SÉRIE TEMPORAL — e o que ela desmente

```
dia          total   gptbot  amazon  perplex  semrush  nao_id
2026-09-05      11        0       0        0        0      11
2026-09-06   3.021        0       0    1.612        0     210
2026-09-07   4.118        0       0    1.008    2.938       4
2026-09-08   1.253        0       2       24    1.067      44
2026-09-09  33.738   27.603       7    1.716    3.594     691
2026-09-10   4.150      817      62    1.559      458   1.023
2026-09-11  15.062        0     378      310    1.115  13.069
2026-09-12   4.773       36   1.198      499      322   1.852
2026-09-13   5.040        2   2.248      117      301   1.950
2026-09-14   5.112       16   3.472       33      154   1.075
2026-09-15  11.148        0   3.222      119      271   6.902
```

**Fato incômodo, e ele precisa entrar no plano:** os 28.474 do gptbot são **uma
varredura única em 2026-09-09** (27.603 num dia, 97,0% do total dele). Depois
disso: 817, 0, 36, 2, 16, **0**. O gptbot varreu a rede inteira uma vez e **não
voltou**. Quem é recorrente e CRESCENTE hoje é o **amazonbot**
(62 → 378 → 1.198 → 2.248 → 3.472 → 3.222).

Isso não rebaixa o número — 11.274/dia na borda é o fato de hoje. Rebaixa a
LEITURA: o que existe hoje é varredura de descoberta, e a página vazia é
exatamente o motivo pelo qual o gptbot não teve o que voltar a buscar.

---

## 3. O QUE OS AGENTES BUSCAM — E OS 404 SÃO A MELHOR PARTE

### 3.1 Padrão de formato: só dois agentes querem a gêmea de máquina

| agente | HTML | index.md | feed.xml | % MD |
|---|---|---|---|---|
| **gptbot** | 9.906 | **9.065** | 9.065 | **31,8%** |
| **amazonbot** | 4.282 | **3.064** | 3.066 | **28,9%** |
| não identificado | 25.631 | 496 | 0 | 1,8% |
| semrushbot | 10.217 | 0 | 0 | 0% |
| perplexitybot | 6.847 | 0 | 0 | 0% |
| oai-searchbot | 2.098 | 4 | 4 | 0,2% |
| applebot | 467 | 0 | 0 | 0% |

**gptbot e amazonbot pedem HTML + Markdown + Atom do MESMO tema, em proporção
1 : 0,92 : 0,92.** Eles estão consumindo a superfície de máquina inteira, por
tema. Perplexity, Semrush e Applebot só leem HTML.

### 3.2 Cobertura: a varredura foi EXAUSTIVA, não seletiva

11.037 dos 11.039 temas receberam ao menos um acesso. Distribuição (todos os
agentes): mediana ≈ 7 acessos, **máximo 26**, e o top 1% (110 temas) concentra
apenas **1,8%** dos acessos. Não há concentração: é sweep de catálogo.

### 3.3 OS 404 — 1.297 em 7 dias, e 865 deles vieram de LINK NOSSO

```
por área pedida:   1.128 jurisprudencia · 90 leis · 34 sumulas · 34 noticias · 11 diarios
por agente:          865 gptbot · 378 perplexitybot · 38 nao_id · 8 yandex · 5 amazon · 3 semrush
por dia:  09-09:128 · 09-10:1.033 · 09-11:48 · 09-12:54 · 09-13:11 · 09-14:16 · 09-15:7
```

**865 dos 1.297 404 trazem `Referer`, e são 865 referers DISTINTOS**, todos do
nosso próprio domínio — exemplo: `https://wikijuridica.com.br/jurisprudencia/stj-tema-967/`
apontando para `/redesocial/tema/jurisprudencia/stj-tema-967/`, que devolveu 404.

Cruzando os 874 alvos de 404 distintos com a tabela `temas` de hoje
(`var/social/social.db`, leitura `mode=ro`):

- **817 alvos (1.161 acessos) JÁ EXISTEM hoje** — eram lag de sincronização;
- **57 alvos (136 acessos) CONTINUAM AUSENTES**: 33 em `leis`, 10 `noticias`,
  10 `diarios`, 4 `jurisprudencia`.

**Causa raiz medida:** `generate-social-temas` é chamado por `tools/deploy-publico`
e **não tem timer próprio** (`systemctl list-timers` não lista nenhuma unit
social). Entre publicar no acervo e rodar o deploy, TODA página nova tem sua
gêmea social respondendo 404 — e o agente que segue o link nosso recebe o 404.
O pico de 1.033 num único dia (2026-09-10) é essa janela.

Ainda ausentes hoje: `temas` tem `leis` 368 contra 406 páginas em
`content/pages.json` (38 de diferença) e `jurisprudencia` 1.130 contra 1.134.

### 3.4 Demanda inventada pelo agente (sem referer): a taxonomia que ele ESPERA

Dos 432 sem referer, o padrão é consistente e é uma pista de produto:

```
/redesocial/tema/leis/cpc-art-536/ · cpc-art-513 · cpc-art-1017 · cc-art-167 ...
/redesocial/tema/noticias/stj-20260910/ · tst-20260910 · stf-20260908 ...
/redesocial/tema/jurisprudencia/stj-tema-1119/
```

O agente presume **uma página por artigo de código** e **uma página por dia por
tribunal**. Temos 406 páginas em `leis` e 59 em `noticias` — ele pede as que
faltam. O corpus para atender isso já está no disco (60.221 acórdãos do STJ,
`data/research/datajud/` com 1.022 assuntos).

---

## 4. `processotela.go` — A FUNDAÇÃO TÉCNICA, MEDIDA EM ZERO

Leitura de `cmd/social/processotela.go` + `cmd/social/processo.go`:

- Rotas: tela `/redesocial/conta/processo/` (GET) e escrita
  `/api/v1/redesocial/conta/processo/consultar` (POST).
- **Três desfechos, e nenhum é "não existe"**: (1) registro encontrado, com
  metadados e andamentos e **sempre a data em que o CNJ atualizou o registro**;
  (2) `nivelSigilo > 0` → recusa, **sem nenhum campo do processo**, citando
  CPC art. 189; (3) zero resultado → "não localizado na base pública", nunca
  "processo inexistente".
- **É SÍNCRONA por medição, não por fé**: o plano registrava 28.289 ms do lado do
  CNJ; remedido em 2026-09-05 por `numeroProcesso` nos índices tjrj, tjsp, trt1 e
  trf2, a resposta veio entre **182 ms e 472 ms em 19 de 19 amostras**. A fila
  (`internal/datajudfila`) virou rede de segurança, não pré-requisito.
- A trava de papel (advogado verificado) **não é ética, é cota**: processo é ato
  público; o que a sessão protege é o teto de **120 req/min da cláusula 3.13** do
  termo do CNJ.

**USO MEDIDO: ZERO.** Em 11 dias de origem, `/redesocial/conta/` recebeu 43
requisições, distribuídas em `cadastrar/` (21), `entrar/` (19+2) e afins.
**Nenhuma** em `processo/` ou `prazo/`. Causa: a rota exige sessão + papel
verificado, e `perfis` tem **1 linha** no banco. Ela é invisível para os
11.274 agentes/dia porque está atrás de um login que ninguém fez.

> A prova de que dado processual público já circula com guarda **existe e
> funciona** — e está trancada atrás da única porta que o tráfego medido não
> atravessa.

---

## 5. A POLÍTICA — O QUE UM CAMPO NOVO CUSTA

`content/social_policy.json` (`schema_version: social_policy_v1`, vigente desde
2026-09-04, `modo: intermediacao`) + `internal/socialpolicy/policy.go`.

**A restrição de engenharia, exata:** `policy.go:284 Load()` → `policy.go:295
decoder.DisallowUnknownFields()`. `cmd/social` faz `log.Fatalf` se a política
reprova, e a unit tem **`Restart=always`** (confirmado por `systemctl show`).
Logo: **campo novo no JSON sem campo correspondente na struct = laço de boot da
rede social.** A ordem obrigatória é: binário novo no disco → `.env`/JSON → swap
→ restart. Nunca o JSON primeiro.

Limiares vivos hoje:

- **`chaves` (7 interruptores, cada um com `base_invocavel_contra` e
  `literalidade`)**: ligadas — `push_caso_para_advogado`, `intermediacao_ativa`,
  `consulta_processual_publica`. Desligadas — `destaque_pago`,
  `percentual_sobre_honorario`, `ordenacao_por_conversao`, `honorario_no_perfil`
  (esta é a única que a norma nomeia literalmente: Prov. 205/2021 art. 3º).
- **`prazos_moderacao_horas`**: extrajudicial urgente 24 · comum 72 · honra 72 ·
  triagem 24 · OAB 168 · recurso abrir 360 · julgar 360.
- **`quarentena_conta_nova`**: 7 dias, 3 posts sobrevividos para sair, 5 posts/dia,
  20 comentários/dia, sem link externo, sem mensagem a quem não segue, 2 menções.
- **`orcamentos_diarios_por_conta`**: 20 posts · 100 comentários · 200 mensagens ·
  200 follows · 20 denúncias · 10 edições de perfil.
- **`reputacao`**: inicial 0 · post sobrevive 30 d +1 · resposta útil +3 ·
  denúncia procedente −20 · remoção judicial −100 · destrava link externo 5 ·
  DM a desconhecido 10 · **abrir thread de pauta 20** · não exibida publicamente.
- **`consulta_publica_de_advogado`**: teto 5/7 dias, **`habitualidade_modo:
  "auditoria"`** (DEC-059 — acima do teto sai aviso datado
  `oab_habitualidade_acima_do_parametro_de_auditoria`, SeveritySoft, e entra na
  transparência; não recusa), léxico só aviso, **amostragem de moderação 20%
  determinística por sha256**, fonte oficial não conta como link externo.
- **`abertura_de_duvida`**: reputação 0, limitada só pela quarentena. Abrir
  DÚVIDA ≠ abrir THREAD DE PAUTA (esta custa 20).
- **`indexacao`**: tudo público é indexável; **piso de corpo 1.100 caracteres**
  (derivado: a página indexável mais magra do acervo tem 1.111). Thread sem
  resposta nasce `noindex, follow`.

> **O piso de 1.100 caracteres é a trava silenciosa da rede social de IA.** A
> gêmea Markdown de um tema tem **1.287 bytes** hoje — e quase todos são navegação.
> Qualquer conteúdo gerado precisa passar 1.100 caracteres de corpo para ser
> indexável. Não é obstáculo: é a especificação do tamanho mínimo da peça.

---

## 6. O RANKING — DUAS FALHAS, E A SEGUNDA É PIOR QUE A PRIMEIRA

`cmd/cerebro/comentarios.go` — subcomando `enfileirar-comentarios`. Lê
`data/ops/access/nginx-*.jsonl` (nunca o banco social: `internal/socialisolation`),
conta `(area, slug)` por acesso em `/redesocial/tema/`, descarta
`bot_simulation` e `warming`, filtra por `agentesValiososParaRanking`, ordena
`hits DESC, area ASC, slug ASC`, resolve contra `content/pages.json`, e enfileira
`gerar_comentario_autoridade` com `--top 300 --dias 14 --modelo qwen3.5:4b
--prioridade -3`. Identidade `UNIQUE(tipo, chave, impressao, modelo)` com
`impressao = sha256(area+"/"+slug)`, então re-rodar nunca duplica.

### Falha 1 — o vocabulário fechado (`comentarios.go:42-50`)

Dentro: `perplexitybot`, `oai-searchbot`, `chatgpt-user`, `bingbot`,
`amazonbot`, `googlebot`, `claudebot`.

Medido contra o tráfego real de `/redesocial/tema/` (85.063 acessos):

```
dentro do vocabulário   19.369   (22,8%)
gptbot (fora)           28.036   (33,0%)
todo o resto (fora)     37.658   (44,2%)
```

**O ranking enxerga 22,8% do sinal.** Três dos sete nomes que ele lista são
quase-zero no dado real: `chatgpt-user` 0, `claudebot` 0, `googlebot` 1,
`bingbot` 11. Fora ficam gptbot (28.036), applebot (1.002), cloudflare-ai-search
(190), meta-externalagent (24), mais `meta-externalads` (8.485) e `AionBot`
(7.008) que sequer têm `agent_key`.

### Falha 2 — O SINAL É PLANO. O ranking não está rankeando nada.

Distribuição de acessos por tema, só dos 7 agentes "valiosos", 11 dias:

```
8.621 temas · soma 19.369 · MÁXIMO 7 acessos
  1 acesso: 3.942 temas     4 acessos: 1.877 temas
  2 acessos: 1.463 temas    5 acessos:   459 temas
  3 acessos:   862 temas    6 acessos:    14 temas · 7 acessos: 4 temas
top 1% (86 temas) concentra 2,3% dos acessos
```

Com 8.621 temas disputando e **máximo 7**, o `--top 300` é decidido por um
punhado de empates e, no empate, **pela ordem alfabética de `area`**. O ranking
mede **exaustividade de varredura**, não interesse: crawler varre tudo uma vez.

Efeito de incluir o gptbot, calculado:

- temas com sinal: 8.621 → **10.905**
- máximo: 7 → 10 (continua plano)
- **sobreposição do TOP-50: 11 de 50.** 78% da seleção muda.

> Incluir o gptbot corrige a Falha 1 e **troca 39 dos 300 primeiros lugares sem
> melhorar a Falha 2**. Um ranking plano com mais dados continua plano. O
> conserto real é trocar a MÉTRICA, não a lista de agentes — ver §8.

---

## 7. A REDE SOCIAL ESTÁ VAZIA (leitura de `var/social/social.db`, `mode=ro`)

```
temas                      11.039
duvidas                         0
respostas                       0
perfis                          1
comentarios_de_autoridade       0
follows                         0
reacoes                         0
notificacoes                    0
denuncias                       0
```

**11.274 requisições por dia de agentes de IA contra uma rede social com zero
conteúdo.** O corpo da gêmea que eles baixam, medido ao vivo (1.287 bytes), diz:

> "Ninguém perguntou nada sobre este tema até agora."
> "Ninguém abriu dúvida sobre este tema ainda."

O HTML equivalente tem 3.012 bytes. Nenhum dos dois traz um único dispositivo
legal, ementa, citação ou parágrafo de conteúdo jurídico.

---

## 8. O QUE ISSO DIZ SOBRE A REDE SOCIAL DE IA

1. **A demanda já existe e é a maior do portal.** 12,8% da zona, 11.274/dia,
   sobre a superfície mais pobre que servimos. Não há hipótese a validar sobre
   "os agentes vão vir": eles já vieram, já varreram os 11.037 temas, e dois
   deles (gptbot, amazonbot) pedem HTML + Markdown + Atom do mesmo tema.
2. **A rede social é o único observatório completo de agentes que temos**
   (travessia 98,9% contra 9,7% do acervo). Toda instrumentação de comportamento
   de agente deve nascer aqui, não no acervo.
3. **O gptbot varreu e não voltou.** Ele encontrou casca. Retorno se compra com
   conteúdo que muda — que é exatamente o que uma rede social de IA produz.
4. **Os 404 são o caderno de pedidos**: página por artigo de código, página por
   tribunal por dia, página por tema repetitivo do STJ. E 865 deles saíram de
   link NOSSO — isso é defeito com causa raiz medida (§3.3), não preferência de
   bot.
5. **A fundação de dado processual público com guarda existe e funciona**
   (`processotela.go`, 182–472 ms em 19 de 19), e tem uso zero porque está atrás
   de sessão.
6. **O ranking que escolheria o que a IA comenta está cego (22,8%) e plano
   (máx. 7).** Publicar comentário guiado por ele hoje seria escolher 300 temas
   praticamente ao acaso alfabético.

---

## 9. LACUNAS — O QUE FALTA MEDIR PARA DIMENSIONAR A REDE SOCIAL DE IA

Cada item diz o que falta, por que o número de hoje não responde, e onde se mede.

**L1 — Retorno por agente (o número que substitui o ranking plano).** Hoje
contamos acessos; não contamos **quantas vezes o MESMO agente volta ao MESMO
tema**. É a única métrica que separa varredura de interesse, e o dado bruto já
está na origem (`agent_key`, `path`, `ts`) com travessia de 98,9%. Não existe
série. Sem ela o `--top 300` continua alfabético.

**L2 — Identidade dos 30,7% não identificados.** 26.834 requisições sem
`agent_key`, das quais 15.493 são agentes que se DECLARAM
(`meta-externalads/1.1`, `AionBot/1.0`) e ~9.900 são rotação de UA em 14 versões
de Chrome. Falta: registrá-los em `data/ops/bot_ip_ranges/` ou no registro de
agentes, e confirmar por ASN/IP quem é a cauda de Chrome. Enquanto durar, um
terço de toda métrica por agente é ficção.

**L3 — Citação: não medimos se a rede social é citada.** Os ~23.000 do Bing são
do domínio inteiro; não há corte por `/redesocial/`. Falta: descobrir se o
relatório de IA do Bing expõe path (os 40 nomes de método candidatos devolveram
404) e, enquanto não, medir o proxy disponível — `clique_de_volta` com
`Referer` de assistente, hoje 81 no acervo inteiro e **não segmentado** por
superfície.

**L4 — Conversão de leitura em retorno.** `fetch` ("considered_for_answer") vale
2.638 na série de origem do acervo; não há campo equivalente marcado nas 87.440
da rede social. Falta classificar cada linha de `superficie=redesocial` nas
mesmas camadas (treinamento / crawl / fetch / clique) para que as duas séries
sejam comparáveis. Sem isso não se sabe se as 11.274/dia são treino ou resposta.

**L5 — Custo unitário de servir um agente.** 11,45 MB e 11.148 requisições à
origem num dia, com 95,7% de não-cache. Falta: CPU e ms por requisição por rota
(`duration_ms` está no ledger, nunca agregado) e o custo marginal de responder
com conteúdo real em vez de casca. É o que dimensiona quantos agentes a
superfície aguenta antes da RTX 5060 Ti.

**L6 — Teto de escrita.** A rede social de IA vai gerar comentário, refutação e
discussão. Falta medir: throughput real de `gerar_comentario_autoridade` de ponta
a ponta (a fila tem 53.786 linhas e **3 `medir_modelo` pendentes** — a medição do
modelo está parada), e quantos caracteres uma peça precisa para passar o piso de
1.100 do `indexacao`.

**L7 — O que o gate de conteúdo social deixa passar E o que ele barra errado.**
Já documentado: `hasNearbyNegation` (gate.go:10-21) suprime "promessa de
resultado" com negação nas 10 palavras anteriores, e das 3 peças geradas a
APROVADA foi a que trocou "REsp 1.794.991" por "a jurisprudência relevante
diferencia". Falta a medição que falta: taxa de falso positivo e falso negativo
do gate sobre uma amostra real de N peças, com o veredito pré-registrado.

**L8 — Cobertura da taxonomia que o agente pede.** 57 alvos de 404 ainda
ausentes hoje, e o padrão pede `leis/{código}-art-{N}` e
`noticias/{tribunal}-{AAAAMMDD}`. Falta contar quantas páginas por artigo de
código o acervo cobre hoje (406 em `leis`) contra quantos artigos os 60.221
acórdãos do STJ efetivamente citam — o corpus está no disco e a extração do
cérebro já ancorou 126.601 de 126.601 dispositivos.

**L9 — Sincronismo `temas` × acervo, como série e não como incidente.** Não há
timer para `generate-social-temas`; ele só roda dentro de `tools/deploy-publico`.
Falta uma medição contínua da diferença entre `content/pages.json` e a tabela
`temas` (hoje: `leis` 406 vs 368, `jurisprudencia` 1.134 vs 1.130) e do tempo
que cada página nova passa respondendo 404 na gêmea social.

**L10 — Eficácia de cache contra a cauda longa.** `s-maxage=3600` sobre 11.039
temas pedidos ~1×/dia produz 1,7% de HIT por construção. Falta medir o intervalo
real entre duas visitas ao MESMO tema (por agente) — é ele, e não um palpite, que
diz qual `s-maxage` transformaria 95,7% de travessia em cache útil. **Atenção:
travessia alta é hoje o nosso instrumento (§2.2); cachear mais CEGA a medição.**
A decisão precisa do número antes, não depois.

---

## 10. O QUE O ADVISOR MUDOU

Cinco verificações. **Duas mudaram claims; três confirmaram.**

**MUDOU — §6 inteira se reescreve. A premissa da tarefa é um erro de categoria
que o código já antecipava.**
`comentarios.go:38-41` exclui o gptbot DE PROPÓSITO: o comentário diz "o ranking
mede leitura por IA que CITA, nao rastreamento de indexacao generica". E
`tools/botagents.py:201` classifica `gptbot` como **`funcao: "training"`**. A
série temporal que eu mesmo medi confirma a classificação: varredura exaustiva
única em 09-09, depois zero. Então "incluir o gptbot porque é 33%" adicionaria
sinal da camada de TREINAMENTO a um ranking que a rejeita por desenho.

Mas a verificação achou o defeito REAL, que é pior: **`tools/botagents.py:201-202`
classifica `amazonbot` e `claudebot` como `training` — a MESMA lane do gptbot — e
os dois estão DENTRO de `agentesValiososParaRanking`.** A lista mistura 4 `search`
+ 1 `user` + **2 `training`**, e exclui um terceiro `training`. Não é vocabulário
incompleto: é vocabulário **incoerente com a taxonomia do próprio projeto**.

E há duas definições contraditórias de "valioso" no mesmo repositório:
`tools/generate-bot-return-series:104` define
`FUNCOES_VALIOSAS = ("search", "user", "training")` e por isso
`data/ops/bot_return_state.json` grava **`gptbot: valioso=True`** — enquanto
`cmd/cerebro/comentarios.go:42-50` o exclui. Mesmo conceito, dois artefatos,
vereditos opostos.

**MUDOU — L1 estava errada ao dizer "não existe série".**
`data/ops/bot_return_daily.jsonl` + `bot_return_state.json`
(`tools/generate-bot-return-series`) medem retorno para **42 agentes**, com
`intervalo_mediano_entre_visitas_dias`, `dias_desde_ultima_visita`,
`queda_desde_o_pico_pct` e `limite_de_abandono_dias`. Da borda, por agente, **no
domínio inteiro**. Medido nela: `gptbot` pico **106.685** req/dia e queda de
**99,9%**; `claudebot` pico 43.065 e **19 dias sem visita**; `chatgpt-user` queda
de só 0,9%. A lacuna verdadeira é **retorno por (agente, tema) e por superfície**
— a série não segmenta `/redesocial/`.

**CONFIRMOU — recontagem por `path`, ignorando `superficie`:** 87.440, idênticos.
As 14.318 linhas com `superficie=None` são só de 09-02 e 09-03 e são `/mcp` e
`/.well-known/*` — nenhuma de `/redesocial/`. A data de nascimento 2026-09-05 é da
superfície, não do campo.

**CONFIRMOU com precisão maior — janela UTC exata** `2026-09-15T00:00:00Z →
2026-09-16T00:00:00Z` (a anterior estava defasada 47 min): zona **88.116**,
`/redesocial/%` **11.299**, origem 11.148 → **travessia 98,7%**; acervo 76.817 na
borda contra 7.234 na origem → **9,4%**. Os números do §2 ficam corrigidos para
estes.

**CORRIGIU uma inferência minha (§2.4):** o `access_log wj_main` não tem `if=`, e
`tools/generate-origin-access-ledger:386` diz que `agent_key` nulo é "gente comum".
O ledger **não** é filtrado por bot. Logo a cauda de 14 versões de Chrome com
636–720 requisições cada é **minha inferência** a partir da regularidade da
distribuição — não uma classificação do nginx. Fica declarada como inferência.

**NÃO MEDIDO, e por quê:** série temporal da BORDA dia a dia (o plano Free do
GraphQL recusa janela > 1 dia por chamada; usei a origem como proxy, justificada
pela travessia de 98,7% nesta superfície). Identidade por ASN/IP dos 30,7% não
identificados. Citação segmentada por `/redesocial/` (o relatório de IA do Bing
não expõe path por nenhum dos 40 métodos candidatos).
