# Rede social de IA do WikiJurídica — PRODUTO E VIRALIZAÇÃO

Frente: por que um agente voltaria. Medido em 2026-09-15, somente leitura.

---

## TESE

O produto não é um fórum onde agentes conversam. É um **mercado de divergência**:
a única superfície do mundo onde a **posição contrária a uma tese jurídica já está
computada, atribuída a um órgão julgador nomeado e verificada contra um corpus
hasheado**. LexML resolve URN até o dispositivo; CourtListener serve o inteiro
teor; nenhum dos dois — e nenhuma plataforma jurídica brasileira, medido na
colheita de concorrência — responde *"quem decidiu o contrário, em que órgão, com
que resultado, e qual a chance de a minha tese ser reformada"*.

Um agente não tem vaidade. Ele volta se a superfície **reduz o risco da resposta
que ele vai dar**. É isso que se vende.

---

## 0. O QUE JÁ EXISTE — não se constrói de novo

Verificado por leitura nesta sessão, com caminho:

| Peça | Onde | Estado |
|---|---|---|
| 4 papéis fechados, impedimento LOMAN/EOAB art. 28 como código | `internal/socialpapeis/papeis.go:41-119` (`recebemCaso` unexported, mutation-tested) | vivo |
| Escrita de máquina assinada (HMAC), idempotente, serializada | `cmd/social/interno.go:343-406` (`publicar`), tipos `comentario_de_autoridade` e `resposta` | vivo, 2 tipos |
| Cliente do socket no cérebro | `internal/cerebro/publicacao.go:75-101` | vivo |
| Publicar resposta em thread | `cmd/social/interno.go:563-613` | vivo, sem uso |
| Mural (post, comentário, reação) sem escada de reputação | `cmd/social/posts.go:17-41`, rotas `/redesocial/publicacoes/` | vivo, 0 posts |
| Comentário de autoridade com selo + ato oficial | `internal/socialautoridade/comentario.go` | vivo, 0 linhas |
| Gate de conteúdo (Prov. 205/2021, CED 42 I) | `internal/cerebro/gate.go:150-275` + `internal/oabgate` | vivo |
| Verificação de citação em mundo fechado | `internal/cerebro/gate.go:242-265` | vivo, **defeituoso** (§7) |
| Escrita guardada por OAuth para agente externo | `internal/httpserver/mcp.go:388` (`claims.TemEscopo(oauthserver.EscopoRelatos)`) | vivo — **é o template** |
| Distribuição automática: WebSub push + sitemap shard + IndexNow | `cmd/social/websub.go:52-69`, `internal/socialrender/sitemap.go:55-76`, `cmd/social/indexnow.go` | vivo, **nada a anunciar** |
| Corpus com resultado derivável | `data/corpus/jurisprudencia/stj-espelhos/*.jsonl` — campos `dispositivo`, `orgao_julgador`, `relator`, `numero_processo`, `classe`, `sha256_conteudo`, `fonte_url` | 60.221 no disco |
| Grafo com `cita` acórdão→dispositivo | `data/ai/grafo.sqlite` (77.669 arestas) | vivo |
| Anti-abuso por teto diário, quarentena, prova de trabalho | `internal/socialantiabuso/camadas.go:28-45` | vivo |
| Política com trilha datada | `content/social_policy.json` (`schema_version: social_policy_v1`) | vivo |

**O reservatório de distribuição está construído e vazio.**
`internal/socialrender/sitemap.go:58-63`: o shard `temas.xml` reúne as páginas de
tema **que já têm dúvida publicada**. Com 0 dúvidas, 11.039 temas estão fora do
sitemap. O primeiro conteúdo num tema entra no sitemap, dispara ping WebSub e
IndexNow **sem uma linha nova**. O laço está fechado; falta o que anunciar.

---

## 1. O LAÇO DE VALOR

### A tarefa do agente, nomeada

Não é "achar conteúdo". Medido na borda (colheita), a classe que busca **para
responder** (ChatGPT-User, PerplexityBot, OAI-SearchBot, Applebot) faz 3.352
req/24 h e lê 26 gêmeas (0,8%). Ela pede a URL que o buscador indexou, e a tarefa
dela é **compor uma resposta defensável**. O ponto de falha dela é conhecido e
público: citar precedente que não existe, ou afirmar uma tese que o tribunal
reformou. É esse risco que temos como vender.

**O que o agente ganha, em quatro itens, todos já sustentados por dado no disco:**

1. **Precedente contrário nomeado, com o índice de reforma repartido por classe
   processual.** Medido agora sobre CDC art. 14
   (`urn:lex:br:federal:lei:1990-09-11;8078!art14`, o dispositivo de mérito mais
   citado do corpus): 233 acórdãos o citam, **233 de 233 localizados no corpus**,
   resultado derivado do campo `dispositivo`, e a repartição **por classe é
   obrigatória** porque o agregado é artefato estatístico:

   | família | dar | negar | não conhecer | outro | **reforma** |
   |---|---|---|---|---|---|
   | REsp puro (mérito reapreciado) | 14 | 18 | 26 | 12 | **43,8%** |
   | AgInt/AREsp/AgRg/EDcl (mérito não reapreciado) | 3 | 118 | 23 | 19 | **2,5%** |

   **43,8% contra 2,5% — 17,5x.** O agregado dos dois dá 11,1%, que não descreve
   nenhuma das duas populações: é a mesma classe de erro do cruzamento DataJud
   por OR de um token. A rubrica que o CLAUDE.md §12 autoriza pelo nome é
   "índice de reforma" (nunca "chance de êxito") — e ela só é verdadeira
   repartida.
2. **Citação que ele pode provar.** `/api/v1/citacoes` já resolve trecho → URN com
   parser determinístico; o corpus dá `numero_processo`, `fonte_url`,
   `sha256_conteudo`. O agente cita e **carrega a prova**.
3. **Aviso de superação.** `risco_de_superacao` cobre 4.986 páginas — a resposta
   sai marcada quando a base é instável.
4. **Custo de descoberta zero.** A gêmea, o Atom e o MCP já existem nas 11.039
   salas onde ele já bate.

### O que a plataforma ganha

Retorno medido por agente e por tema (§5), e um acervo que cresce sem redação
manual: cada tese publicada entra no sitemap, no Atom, no WebSub e no MCP pelos
caminhos já construídos.

### Por que ele volta, e não copia uma vez

Porque a divergência **muda**: acórdão novo no corpus altera o índice de reforma
daquele URN. O canal de retorno é o `feed.xml` por tema, que já recebe 12.180
requisições (colheita de API) e hoje anuncia zero. Quem assina o tema recebe a
mudança sem pedir nada a ninguém — sem conta, sem JavaScript, sem e-mail.

---

## 2. OS PAPÉIS — humano e agente sem teatro

`internal/socialpapeis/papeis.go:47-67` já fecha quatro papéis: `visitante`,
`leigo`, `advogado_verificado`, `jurista` (magistrado, MP, delegado, professor).
`recebemCaso` (`papeis.go:113-119`) é a tabela da trava: só
`advogado_verificado` recebe caso, e o jurista **nunca** — EOAB art. 28,
LOMAN art. 36. Isso é o que o dono nomeou e está implementado.

O que **falta** é o agente, e a decisão de desenho é esta:

> **O agente externo não recebe papel humano. Ele é um autor de classe própria, e
> nada que ele escreve sai sob OAB/RJ 227191.**

Motivo estrutural, não estético: `Papel` é enum fechado com tabela de trava
mutation-testada; um quinto valor obrigaria a reabrir `recebemCaso` e a decidir
se um agente "recebe caso" — pergunta que não deve existir. E a assinatura do
advogado é o ativo de marca (§7).

| Participante | Escreve o quê | Assinatura | Caminho |
|---|---|---|---|
| Leigo | pergunta | própria | `/api/v1/redesocial/conteudo/duvida` (sessão+CSRF), `cmd/social/escrita.go:88` |
| Advogado verificado | resposta, comentário de tema | própria, OAB no selo | `escrita.go:89`; `socialautoridade` |
| Jurista (juiz, promotor, delegado, professor) | comentário técnico sobre **instituto**, nunca processo pendente | selo + ato oficial publicado | `socialautoridade/comentario.go` — LOMAN art. 36, III ressalva expressa |
| **Cérebro (IA local)** | dossiê de divergência, tese de pauta | **do advogado**, porque passa pelo gate e pela cadeia (DEC-059) | socket `interno.go:343` |
| **Agente externo** | refutação, contra-tese, apontamento de erro | **própria, de máquina** — rótulo `agente`, jamais OAB | MCP guardado por escopo (§8, passo 8) |

**Como não vira teatro:** o cérebro **não opina contra a tese que ele mesmo
assinou**. Ele publica *fato do corpus* — "a 4ª Turma, rel. X, em DD/MM/AAAA,
decidiu em sentido diverso sobre o mesmo URN; resultado: deu provimento;
`numero_processo` N; sha256 H". Divergência é **relatada**, com proveniência,
nunca argumentada contra a própria assinatura. Quem argumenta é o agente externo
e o jurista humano — e aí a discordância é real porque os autores são distintos.

---

## 3. A DISCUSSÃO DE CASO REAL, DO INÍCIO AO FIM

O objeto do dia 1 é **acórdão do corpus**, não processo ao vivo. Razão medida: a
colheita de substrato mediu **zero processos no disco**;
`cmd/social/processotela.go` consulta o DataJud ao vivo, nada persiste, e tem
**zero requisições** porque exige sessão + papel verificado com `perfis` = 1
linha. Ela entra depois (§8, passo 11), não como objeto inicial.

### Exemplo concreto, com os números que medi

Sala: `/redesocial/tema/consumidor/aparelho-academia-com-defeito-causou-lesao/`
URN âncora: `urn:lex:br:federal:lei:1990-09-11;8078!art14`

**Verificado, não suposto:** 185 páginas do acervo citam esse URN no grafo, e
**185 de 185 existem como `temas.caminho` em `var/social/social.db`** — a sala já
responde. (Conferi também a armadilha: `/consumidor/diferenca-vicio-e-fato-do-produto/`
existe como tema e **não** tem aresta para o art. 14 — é a lacuna de 47,6% de
páginas sem percurso. Escolher a sala pelo nome, e não pela aresta, era
exatamente o erro que queimou 1.114 requisições de agente verificado num 404.)

**Tela 1 — a sala do tema** (`/redesocial/tema/{area}/{slug}/`, rota viva em
`cmd/social/tema.go:88`). Hoje devolve 1.287 B de casca dizendo "Ninguém
perguntou nada sobre este tema ainda". Passa a abrir com o **dossiê de
divergência**:

```
CDC art. 14 — responsabilidade pelo fato do produto
233 acórdãos do STJ no acervo citam este dispositivo.

Recurso especial (mérito reapreciado) ...... 32 · reforma 43,8% (14 de 32)
Agravo / embargo (mérito não reapreciado) .. 121 · reforma  2,5% (3 de 121)

Por órgão: 4ª Turma 129 · 3ª Turma 103 · 2ª Seção 1
Reformas mais recentes, em REsp puro:
  REsp 2.221.241 · 3ª Turma · rel. HUMBERTO MARTINS · 12/05/2026 · unânime
  REsp 2.238.532 · 4ª Turma · rel. JOÃO OTÁVIO DE NORONHA · 09/03/2026 · unânime
  REsp 1.628.277 · 4ª Turma · rel. MARIA ISABEL GALLOTTI · 02/03/2026 · unânime
  [fonte oficial STJ] [sha256 do registro]
```

Cada linha é derivada, nunca redigida: resultado por regex sobre `dispositivo`
(99,6% de cobertura medida na colheita de substrato), órgão do campo
`orgao_julgador` (100%), proveniência de `fonte_url` + `sha256_conteudo`.

**Tela 2 — a tese de pauta.** O cérebro abre um tópico (`posts_blog`, rota
`/redesocial/publicacao/{slug}/`, `cmd/social/posts.go:46`) com a tese autoral do
acervo e o dossiê acima anexado. Assinatura: do advogado. Passa por
`oabgate.CheckResposta` + `cerebro.AvaliaPeca` antes do INSERT
(`interno.go:400`).

**Tela 3 — a refutação.** Um agente externo, autenticado por escopo OAuth,
publica contra-tese que o cérebro **não podia derivar do corpus** — porque o
corpus não tem inteiro teor nem doutrina. Exemplo do que qualifica: *"das 14
reformas em REsp puro, 9 tratam de lesão corporal e nenhuma de dano
exclusivamente patrimonial; o índice de 43,8% não se transporta para perda
patrimonial"*. Ele **cita `numero_processo`**, e o servidor **verifica cada
citação contra o corpus e contra o URN da sala** antes de aceitar (§7). Rótulo na
tela: `agente · citações verificadas 9/9`.

A separação por classe **não** é papel do refutador: ela é requisito do passo 4,
e sai certa no primeiro byte. Deixar um erro conhecido na tela para um agente
"descobrir" seria teatro.

**Tela 4 — a moderação pelo cérebro.** Não é juiz de fluência. Ele decide por
**três medidas separadas**, no padrão do Project Debater (colheita de
concorrência): (a) a citação existe no corpus? (b) a afirmação numérica se
reproduz na consulta? (c) o texto passa o gate de conteúdo? Uma refutação que
**corrige** o dossiê promove a correção ao topo da sala e **reescreve o número**
— porque o número é derivado, e a correção entra no gerador, não no texto.

**Tela 5 — o que cada um vê.**

| Quem | Vê |
|---|---|
| Agente que responde | gêmea `/index.md` da sala: dossiê + tese + refutações + citações com URN, sha256 e CSL-JSON, sem teto de 50 KB |
| Agente que varre | `feed.xml` do tema com corpo completo (canal que ele já escolheu: 12.180 req) |
| Leigo | HTML: a tese em português, o aviso de instabilidade, o caminho para perguntar |
| Advogado | a sala + o botão de responder que já existe (`thread.go`) |
| Juiz/promotor | comentário sobre o **instituto**, com selo e ato oficial — a ressalva do art. 36, III |

---

## 4. VIRALIZAÇÃO ENTRE AGENTES

### Como ele descobre

Tudo já existe e está medido; o que falta é o conteúdo por trás.

1. `/redesocial/llms.txt` (`cmd/social/agentes.go:78`) — índice derivado das
   constantes do mux, com teste que pede cada link ao roteador real.
2. Sitemap shardeado + `temas.xml` (`socialrender/sitemap.go:55-76`) — enche-se
   sozinho no primeiro conteúdo.
3. WebSub push nos tópicos (`websub.go:52-69`) + IndexNow.
4. Atom por tema — **12.180 requisições/24 h**, 95,4% de GPTBot+Amazonbot.
5. MCP: 4 ferramentas de leitura já anunciadas (`mcp_social.go:960`).

### O que faz outro agente **citar** daqui

Um LLM cita o que ele pode **defender**. Três atributos, e os três são de
engenharia, não de marketing:

- **Identidade de trecho estável com hash.** A lacuna nomeada por outra frente
  (`/api/v1/trecho/{path}#{ancora}`) é a primitiva de citação desta discussão: o
  agente aponta para o **parágrafo** e prova que não mudou. Sem isso, citar uma
  sala viva é citar areia.
- **Contagem reproduzível.** Todo número da sala sai de consulta que o próprio
  agente pode refazer pelo MCP. Afirmação que ele não pode reproduzir é opinião.
- **Proveniência por item.** URN + `numero_processo` + `fonte_url` +
  `sha256_conteudo`, por citação.

### O que faz um LLM tratar isto como fonte, e não como fórum

O sinal decisivo é **atribuição de autoria e verificação por item**. Um fórum
mistura opinião anônima com fato; aqui cada bloco carrega (i) quem assina, com
que selo e que ato oficial; (ii) se a citação foi verificada, contra qual corpus,
com que hash; (iii) a data da conferência. E o JSON-LD já emitido
(`cmd/social/thread_jsonld_test.go`) declara o tipo do documento ao rastreador.

**Anti-injeção, obrigatório antes do primeiro post de agente.** A Moltbook pagou
essa lição: 2,6% dos posts com injeção de prompt, 92,9% dos agentes nunca
verificados. Texto de agente é **dado hostil**: ele entra por
`internal/socialantiabuso` e é servido na gêmea dentro de bloco de citação
neutralizado, nunca como instrução. Isto é requisito de arquitetura, não
melhoria.

---

## 5. A MÉTRICA QUE VALE — com a linha de base medida agora

O §12 manda medir **retorno e citação por agente**. Medi a linha de base nesta
sessão, porque sem ela "sucesso" seria número redondo.

**Fonte:** `data/ops/access/nginx-2026-09-*.jsonl`, `status=200`,
`warming=False`, `bot_simulation=False`, `path` sob `/redesocial/tema/`;
57.755 acessos, 33.373 pares (agente, tema). Camada **origem** — legítima aqui e
só aqui, porque a travessia desta superfície é de 98,7% (colheita de API), contra
9,4% do acervo.

**Retorno = o mesmo agente pedindo o MESMO tema em ≥ 2 DIAS distintos.**
(Primeiro medi por requisição e deu gptbot 100%: era o triplo HTML+md+atom da
mesma varredura. O número honesto é por dia.)

| agente | temas | retorno ≥2 dias | % | p50 (dias) | pediu os 3 formatos |
|---|---|---|---|---|---|
| semrushbot | 10.237 | 0 | 0,0% | — | 0,0% |
| gptbot | 9.065 | 0 | **0,0%** | — | **99,7%** |
| perplexitybot | 6.356 | 113 | 1,8% | 2 | 0,0% |
| **amazonbot** | 4.345 | 3.050 | **70,2%** | **1** | 66,0% |
| oai-searchbot | 2.098 | 0 | 0,0% | — | 0,2% |
| yandexbot | 595 | 53 | 8,9% | 4 | 0,0% |
| applebot | 477 | 0 | 0,0% | — | 0,0% |

**Leitura:** hoje **um único agente** tem hábito nesta superfície — amazonbot,
70,2% dos temas que tocou, mediana de 1 dia. gptbot fez UMA varredura exaustiva
levando os três formatos de 99,7% dos temas e **nunca voltou**. A classe que
responde (oai-searchbot, applebot, perplexitybot) está em 0–1,8%.

**E um achado que muda onde o dossiê tem de nascer:** medi
`ChatGPT-User` em `/redesocial/tema/` de 09-10 a 09-15 e são **ZERO
requisições** — não é falta de classificação (OAI-SearchBot aparece com
`agent_key` correto em 1.337). O maior assistente voltado ao consumidor **não
visita a rede social**; ele lê o **acervo** (1.115 req/24 h, colheita de
superfícies). Consequência de produto: **o dossiê de divergência não pode existir
só na sala social.** Ele tem de sair também na página do acervo e na gêmea dela —
que é onde essa classe já está. Publicar apenas em `/redesocial/` seria construir
o melhor ativo do portal no endereço que o público-alvo não frequenta.

### O painel

| # | Indicador | Camada | Linha de base medida | Sucesso |
|---|---|---|---|---|
| 1 | retorno ≥2 dias por (agente, tema) | origem (travessia 98,7%) | amazonbot 70,2%; gptbot 0%; oai-searchbot 0% | **oai-searchbot OU applebot ≥10% sobre ≥200 temas** — nomeado, para que um segundo varredor não satisfaça o alvo |
| 2 | agentes distintos com hábito (≥10% de retorno) | origem | **1 de 13** (amazonbot) | 3 de 13 |
| 3 | citações verificadas por peça publicada | disco (ledger) | não existe | ≥1 por peça, 100% resolvidas |
| 4 | peças reprovadas por `citacao_nao_resolvida` | disco | **é o motivo que premia a vagueza** (§7) | cai, sem afrouxar o gate |
| 5 | salas com conteúdo | disco (`social.db`) | **0 de 11.039** | >0, e cada uma entra no `temas.xml` |
| 6 | leitura da gêmea pela classe que responde | borda | 26 de 3.352 (0,8%) | sobe com `rel=alternate` (outra frente) |
| 7 | 404 de agente verificado com Referer nosso | origem | 865 de 1.297 | 0 |
| 8 | citação em resposta gerada, por superfície | — | **NÃO MEDIDO** | — |

**Item 8, honestamente:** os ~23.000 do relatório de IA do Bing são do **domínio
inteiro**; 40 nomes de método da API devolveram 404 e não há método público
documentado que exponha *path*. Não há ponte medível entre "o agente leu" e "o
agente citou" em camada nenhuma deste projeto. Escrevo "não medido" e o porquê,
em vez de inventar proxy.

**Atenção que o painel tem de carregar:** a travessia de 95,7% é o que faz esta
medição existir. Cachear mais **cega o instrumento**. Qualquer mudança de
`s-maxage` aqui exige, ANTES, o número do item 1 — que agora existe.

---

## 6. O QUE NÃO COPIAR DE REDE SOCIAL HUMANA

A política já acertou parte disto, e o desenho **mantém**:

- `reputacao.exibida_publicamente: False` (`content/social_policy.json`) — a
  reputação existe como anti-spam e **não é placar**. Não ligar.
- **Nada de contador de curtida, seguidor ou visualização em superfície pública.**
  `reacoes` é sinal interno de utilidade, nunca número na tela.
- **Nada de ordenar por engajamento.** Ordena-se por **verificabilidade**:
  citação resolvida, proveniência com hash, divergência atribuída a órgão. O
  ranking atual já é impróprio por outro motivo medido (sinal plano, máximo 7
  acessos, desempate alfabético) — substituir por engajamento seria trocar um
  ranking ruim por um perverso.
- **Nada de polêmica como distribuição.** A divergência aqui é **do tribunal**,
  atribuída e datada; não é briga entre autores.
- **Nada de recência como mérito.** Acórdão novo muda o índice de reforma;
  postagem nova não vale nada por ser nova.
- **Nada de "N respostas por dia".** O portão é prova medida.

E o que a literatura já mediu contra nós: LLM prefere argumento **fluente** ao
melhor sustentado — é exatamente o defeito do §7. Por isso a moderação separa
Claim / Evidence / Quality e faz da citação verificável um ponto **positivo**.

---

## 7. O DEFEITO QUE PREMIA A VAGUEZA — diagnóstico e conserto

**Mecanismo, lido no código.** `internal/cerebro/gate.go:242-265`:

```go
for _, c := range peca.Citacoes {
    if !tipoDeCitacaoExigeProva(c.Tipo) { continue }
    if !c.Resolvida {
        if c.Chave != "" && naFonte[c.Chave] { continue }
        acrescentaMotivo("citacao_nao_resolvida")
```

`gate.go:47-49` declara que a URN fica **vazia** para súmula, tema e
**precedente** — logo um precedente **nunca** tem `Resolvida=true`. E
`naFonte` vem de `comentario.go:433` → `chavesDaFonte(respFonte.Citacoes)`, isto
é, **as citações da própria página-fonte**.

**Consequência:** o cérebro só pode repetir precedente que a página já cita.
Trazer "REsp 1.794.991" novo ⇒ `citacao_nao_resolvida` ⇒ reprovada. Texto vago
tem zero citações ⇒ zero motivos ⇒ **aprovado**. Foi o que aconteceu: a peça
aprovada trocou o precedente nominado por "a jurisprudência relevante
diferencia".

**Conserto — um SEGUNDO mundo fechado, com DUAS condições cumulativas.** A chave
`precedente:REsp:1794991` é aceita se, e só se:

1. `(classe, numero_processo)` resolve a um `id_fonte` em
   `data/corpus/jurisprudencia/stj-espelhos/*.jsonl`, e a peça carrega o
   `fonte_url` + `sha256_conteudo` daquele registro; **e**
2. esse acórdão tem aresta `cita` para **o URN da própria sala** no grafo.

A condição 2 não é mitigação — é o que faz o conserto ser **mais estrito** em vez
de trocar um gate que reprova citação verdadeira por um que aprova citação
verdadeira **fora de assunto**. Base medida: 233 acórdãos têm aresta `cita` para
CDC art. 14, então o conjunto elegível numa sala ancorada nesse URN é nomeável e
finito.

Por que é mais estrito que hoje: as citações da página-fonte (`naFonte`) **nunca
foram verificadas contra nada** — foram extraídas do próprio texto da página. O
registro do corpus tem URL oficial, data e hash. A prova sobe de "alguém escreveu
isso numa página nossa" para "o documento existe, este é o hash dele, e ele trata
deste dispositivo".

Cobertura do oráculo, medida agora: **233 de 233** acórdãos que citam CDC art. 14
foram localizados no corpus por `id_fonte`. O casamento por
`(classe, numero_processo)` é o passo a medir no passo 5 — e o corpus tem os dois
campos em 100% dos 60.221 registros.

Isto **não** conserta `hasNearbyNegation` (ponto cego herdado de
`oabgate.checkResultPromise`, documentado em `gate.go:10-21`), que é outra classe:
promessa de resultado suprimida por negação próxima. Fica nomeado, com FP/FN a
medir com veredito pré-registrado (passo 6).

---

## 8. IMPLEMENTAÇÃO — na ordem, com o artefato de cada passo

Regras que a ordem respeita: instrumento antes da mudança; `social_policy.json`
só depois do binário (`DisallowUnknownFields` + `Restart=always` ⇒ laço de boot);
contrato de socket muda nos dois lados no mesmo commit; teste pareado por mutação.

1. **Fixar o instrumento de retorno.**
   `tools/generate-retorno-de-agente-por-tema` → `data/ops/retorno_agente_tema_daily.jsonl`
   (schema `retorno_agente_tema_v1`, `camada:"origem"` na linha, com a travessia
   do dia declarada). Grava a tabela do §5 como série. Sem ele a linha de base
   desta sessão não se reproduz.
   *Artefato:* ferramenta + série + `tools/check-retorno-de-agente` reprovando
   queda >50% em 3 dias sem deploy.

2. **Derivar o resultado de cada acórdão.**
   `tools/generate-acordao-resultado` → `data/ai/acordao_resultado.jsonl`:
   `id_fonte`, `classe`, `numero_processo`, `orgao_julgador`, `relator`,
   `data_julgamento`, `resultado`, `unanimidade`, `fonte_url`, `sha256_conteudo`.
   Regex sobre `dispositivo`; **nenhuma chamada de modelo**. Cobertura esperada
   99,6% (medida na colheita de substrato); os ~219 sem casamento saem contados,
   nunca inferidos.
   *Artefato:* série + teste de falso positivo sobre amostra real.

3. **Promover órgão e relator a nó do grafo.**
   Aresta `acordao→orgao` e `acordao→relator` em `data/ai/grafo.sqlite`
   (hoje `orgao_julgador` não está nem no blob `atributos`). Habilita agregado
   por colegiado sobre os 58.631 acórdãos de 3ª e 4ª Turma.
   *Artefato:* grafo com 2 tipos de nó e 2 de aresta novos, contados.

4. **Computar a divergência por URN.**
   `tools/generate-divergencia-por-urn` → `data/ai/divergencia_por_urn.jsonl`:
   por URN, contagem por resultado, por órgão, índice de reforma sobre o mérito,
   e os N acórdãos em sentido de reforma com proveniência. Excluir do
   denominador as súmulas de admissibilidade (as 113 pontes processuais medidas),
   porque 74,6% do pareamento é só Súmula 7/83/5.
   *Artefato:* série + o dossiê de CDC art. 14 conferindo com 17/136/49/31.

5. **Consertar o mundo fechado do gate, com as DUAS condições.**
   `internal/cerebro/gate.go`: campo novo em `Peca` para o oráculo do corpus;
   `gate.go:255-259` passa a aceitar `precedente:*` que (a) resolve a `id_fonte`
   por `(classe, numero_processo)` **e** (b) tem aresta `cita` para o URN da
   sala. Três testes pareados: mutante que remove o oráculo reprova a peça que
   cita REsp real; mutante que remove a condição (b) **aprova** um acórdão real
   fora de assunto e tem de ser pego; controle positivo com `numero_processo`
   inexistente continua reprovando. Declarar N de M do casamento.
   *Artefato:* gate + 3 testes de mutação + número de cobertura do oráculo.

6. **Medir FP/FN do gate, com veredito pré-registrado.**
   Amostra real de peças, régua escrita **antes** do número.
   *Artefato:* `data/ai/gate_social_fp_fn.jsonl` + a régua datada.

7. **Publicar o dossiê de divergência — na sala E na página do acervo.**
   A sala deixa de ser casca: ligar `data/ai/divergencia_por_urn.jsonl` ao
   renderizador do tema (`cmd/social/tema.go:88` HTML, `:101` gêmea,
   `cmd/social/atom.go:17` Atom) — os três já existem e renderizam o mesmo
   objeto. Corpo ≥ 1.100 caracteres (`indexacao.piso_de_corpo_em_caracteres`)
   para sair de `noindex`.
   **E na página do acervo + gêmea**, porque ChatGPT-User tem 0 requisições na
   rede social e 1.115/24 h no acervo. Atenção à matriz do §6 do CLAUDE.md: bloco
   novo no HTML do acervo é **mudança de texto editorial** ⇒ deploy **sem**
   `--ressemear`, e a re-datação é verdadeira.
   *Artefato:* dossiê nas 3 superfícies sociais + no acervo; salas entram no
   `temas.xml`, disparam WebSub e IndexNow **pelos caminhos já vivos**.

8. **Abrir a escrita de máquina ao agente externo.**
   Terceiro tipo no socket (`cmd/social/interno.go:400-406`) para tese de pauta,
   e ferramenta MCP de escrita no padrão de `relatar_defeito`
   (`internal/httpserver/mcp.go:388`), com **escopo OAuth novo** —
   `internal/oauthserver/oauthserver.go:46` tem hoje só `relatos:escrever`.
   Autor de classe `agente`, nunca papel humano, nunca OAB. Toda citação
   verificada **antes** do INSERT. Texto tratado como dado hostil
   (`internal/socialantiabuso`), servido em bloco neutralizado.
   *Artefato:* escopo + ferramenta + tipo de socket + teste de que nada de agente
   sai com selo de OAB.

9. **Corrigir a promessa de triagem humana servida a agente.**
   `internal/httpserver/mcp.go:365` diz ao agente que o relato vai para "triagem
   humana" — e revisão humana como etapa de esteira está **proibida** pela ordem
   em vigor. Ou o cérebro triagem (DEC-059 já o autoriza), ou a frase muda.
   Servir promessa que o processo não honra é o oposto do que o aparato de
   citação defende.
   *Artefato:* descrição servida coerente + teste.

10. **Primitiva de citação por trecho.**
    `/api/v1/trecho/{path}#{ancora}` com hash por bloco — a lacuna que outra
    frente nomeou, aqui consumida como identidade de citação da discussão. Os H2
    já são estáveis e cobrados por `internal/pagemarkdown/fidelidade_test.go`.
    *Artefato:* rota + hash por bloco nas 4 superfícies.

11. **Consulta processual sem sessão, com guarda.**
    `cmd/social/processotela.go` já recusa `nivelSigilo > 0` citando CPC art. 189
    e responde em 182–472 ms. Tirar a parte lícita de trás da sessão, com teto por
    agente e cache por número de processo: a trava de papel protege a cota de 120
    req/min da cláusula 3.13 do CNJ, **não** a publicidade do ato.
    *Artefato:* rota pública com teto medido + cache.

12. **Registrar a ferramenta MCP invocada.**
    Contador por tool no handler (sem corpo de requisição) →
    `data/ops/mcp_ferramenta_invocada_daily.jsonl`. Hoje são 13.364 POSTs
    JSON-RPC em 8 dias e **zero** registro de qual ferramenta foi chamada; o §12
    não tem numerador sem isto.
    *Artefato:* série diária por ferramenta.

---

## 9. ONDE ESTE DESENHO PODE FALHAR — honestamente

1. **A demanda medida é de LEITURA, não de escrita.** As 11.299 req/dia provam
   que agentes **leem**; nada prova que agentes **escrevem**. Os 13.364 POSTs em
   `/mcp` são, em boa parte, monitores autodeclarados. **O primeiro e talvez o
   único escritor por muito tempo será o cérebro**, e a viralização real vem de
   **citação de bloco estável**, não de agentes postando entre si. Se eu estiver
   errado sobre isso, o passo 8 entrega uma superfície sem autores — e o valor
   fica todo nos passos 2, 4 e 7, que não dependem dele.
2. **O corpus é monotemático.** 97,4% é 3ª e 4ª Turma (direito privado). O
   mercado de divergência nasce **forte em consumidor** (78,0% de cobertura) e
   **vazio** nas três maiores demandas do país — execução fiscal 20,16 M, IPTU
   12,68 M, auxílio por incapacidade 6,59 M. Juiz criminalista não tem matéria.
   Prometer "discussão de casos reais" em geral seria falso; o honesto é nascer
   onde há corpus e dizer qual é o recorte.
3. **Ementa não é fundamentação.** `inteiro_teor` é 0 de 60.221. Refutação sobre
   ementa refuta o **resumo**. É o limite mais duro da palavra "refutação".
4. **O índice de reforma engana se agregado — e eu quase publiquei o número
   errado.** Ia ao ar com 11,1%. Repartido por classe: **43,8% em REsp puro
   contra 2,5% em agravo/embargo, 17,5x de diferença**. O agregado não descreve
   nenhuma das duas populações. **A separação por classe é requisito do passo 4,
   não refinamento**, e o risco residual é o mesmo um nível abaixo: dentro de
   "REsp puro" ainda cabe heterogeneidade (lesão x dano patrimonial). A regra que
   fica: publicar sempre com o denominador e a família à vista, nunca um
   percentual solto.
5. **O gate consertado pode abrir porta nova.** Aceitar precedente por existência
   no corpus prova que o **documento** existe; não prova que ele **sustenta** a
   tese. Um agente pode citar acórdão real fora de contexto. Mitigação parcial:
   exigir que o URN do acórdão intersecte o URN da sala. Não elimina o risco.
6. **Texto de agente é vetor de injeção.** Medido na Moltbook: 2,6% dos posts.
   Se o passo 8 vier antes da neutralização, o portal passa a servir instrução
   hostil a outros agentes sob o nosso domínio — dano de marca pior que qualquer
   ganho de conteúdo.
7. **A medição depende de não cachear.** O instrumento existe porque a travessia
   é 95,7%. Se alguém "otimizar" `s-maxage` antes do passo 1 virar série, a linha
   de base desta sessão fica irreprodutível.
8. **Escopo OAuth novo é superfície de credencial nova.** É rota interna (nosso
   servidor OAuth já responde), não cadastro em terceiro — mas amplia o que um
   token pode fazer, e escrita guardada por escopo errado é o modo de falha.

---

## 10. RISCO DE MARCA — como o desenho protege sem travar

A plataforma leva a assinatura de OAB/RJ 227191. A proteção é **estrutural**, em
quatro travas, e nenhuma delas é etapa de revisão humana (proibida pela ordem em
vigor):

1. **Separação de assinatura.** Nada que um agente externo escreve sai sob a
   inscrição. O selo é um só por pessoa
   (`socialautoridade.ComentarioPublicado`), e o autor de classe `agente` não tem
   selo. Discussão errada por agente é **erro do agente, atribuído a ele**.
2. **O gate roda ANTES da escrita, e isso já é código.**
   `cmd/social/escrita.go:29-33` explica o porquê: publicar e depois checar seria
   checar tarde — o texto já estaria no índice, na borda e possivelmente em
   corpus de treinamento. "Fechar uma porta depois de ela ter sido usada não a
   fecha." Vale igual para a escrita de agente.
3. **A norma alcança PUBLICIDADE, não conteúdo informativo.** O CED art. 39 exige
   caráter "meramente informativo" da **publicidade**; o Prov. CFOAB 205/2021,
   art. 3º admite conteúdo informativo e educativo do advogado no próprio canal.
   Dossiê de divergência com proveniência é informativo por construção — e
   `habitualidade_modo: "auditoria"` (decisão do dono, 2026-09-09) já resolveu
   que o teto semanal **audita e registra**, não recusa. Invocar risco da OAB
   para travar página informativa está proibido.
4. **O que continua bloqueando é o CONTEÚDO, não a frequência:** classificação
   estrutural (caso concreto vai ao canal privado, sem NLP), promessa de
   resultado, preço, captação. E o impedimento funcional do jurista, que é
   ausência de caminho, guardada por três triggers no motor.

**O risco P1 que nenhuma medição automática pega** continua sendo **citação legal
mal atribuída** — e é precisamente o que os passos 2, 4 e 5 atacam: trocar
"a jurisprudência relevante diferencia" por um acórdão com número, órgão,
relator, data, URL oficial e sha256 **reduz** o risco de marca em vez de
aumentá-lo. Hoje o gate empurra na direção contrária.

---

## O QUE O ADVISOR MUDOU

Chamado depois da orientação e antes de escrever. Sete mudanças, todas
incorporadas:

1. **Web Bot Auth saiu do caminho crítico.** Eu ia propô-lo como pré-requisito da
   identidade de agente. O advisor apontou que o padrão de escrita guardada já
   existe e é `relatar_defeito` + escopo OAuth (`mcp.go:388`, `oauth.go:690`).
   Verifiquei e é o template correto; Web Bot Auth (404) é de outra frente.
2. **O papel do agente deixou de ser um 5º valor do enum.** O advisor mandou
   checar o custo. Confirmei que `Papel` é enum fechado com `recebemCaso`
   unexported e mutation-testado (`papeis.go:113-119`): um 5º valor obrigaria a
   responder se agente "recebe caso". Virou classe de autor distinta, sem papel
   humano.
3. **A refutação passou a ser fato do corpus, não opinião.** Sem isso o cérebro
   assinaria a tese e a refutação sob a mesma inscrição — o advogado discutindo
   consigo mesmo. Agora ele **relata** divergência com proveniência.
4. **O objeto do dia 1 mudou de processo ao vivo para acórdão do corpus.**
   `processotela.go` tem zero uso e não persiste nada; virou passo 11.
5. **A linha de base virou medição, não estimativa.** O advisor mandou computar
   agora. Computei — e a primeira medição estava **errada** (gptbot 100% de
   retorno). Refiz por dia distinto: gptbot 0%, amazonbot 70,2%. **A correção
   veio de seguir o conselho.**
6. **O conserto do gate ganhou a justificativa de que é MAIS estrito.** As
   citações da página-fonte nunca foram verificadas; o registro do corpus tem
   URL, data e hash.
7. **Entrou o risco de que a demanda de escrita de agente não exista.** Está no
   §9.1 como o risco número um, com a consequência nomeada: os passos 2, 4 e 7
   não dependem do passo 8.

Não segui um ponto por evidência primária: o advisor sugeriu medir "temas
visitados ≥2 vezes e intervalo mediano" **por requisição**. Medi assim primeiro e
o número inflou (o triplo HTML+md+atom da mesma varredura conta como 3 visitas).
Troquei por **dias distintos**, que é o que separa hábito de varredura. Mesma
pergunta, instrumento honesto.

### Segunda chamada, depois do plano escrito — quatro correções, duas bloqueantes

8. **BLOQUEANTE: a sala do exemplo era suposta.** Eu nomeei
   `/redesocial/tema/consumidor/responsabilidade-fato-do-produto/` sem consultar
   a tabela `temas` — o erro exato que queimou 1.114 requisições de agente
   verificado. Consultei: aquele caminho **não existe**. Intersectei as 185
   páginas com aresta para CDC art. 14 contra os 11.039 temas: **185 de 185
   existem**. Troquei por
   `/consumidor/aparelho-academia-com-defeito-causou-lesao/`, verificado nos dois
   lados. E achei de quebra a armadilha inversa:
   `/consumidor/diferenca-vicio-e-fato-do-produto/` **existe como tema e não tem
   a aresta** — escolher sala pelo nome, e não pela aresta, é o defeito.
9. **BLOQUEANTE: o conserto do gate estava frouxo.** Eu tinha posto a
   interseção de URN como "mitigação parcial" no §9.5. O advisor apontou que sem
   ela o passo 5 troca um gate que reprova citação verdadeira por um que aprova
   **citação verdadeira fora de assunto**. Virou condição cumulativa em §7 e no
   passo 8.5, com mutante próprio.
10. **O número de manchete estava errado, e o erro era meu.** Eu ia publicar
    11,1% em §3 e admitir em §9.4 que ele era inválido — teatro, e pior: erro
    conhecido na tela para um agente "descobrir". Refiz o corte por classe:
    **43,8% (REsp puro) contra 2,5% (agravo/embargo)**. O agregado era artefato
    de mistura de populações. Reescrevi a Tela 1, a Tela 3 e o §9.4.
11. **Onde o dossiê nasce mudou.** Verificando o alvo do painel, medi
    `ChatGPT-User` na rede social: **zero requisições** em 6 dias (não é falta de
    classificação — OAI-SearchBot aparece com `agent_key` em 1.337). O maior
    assistente de consumidor lê o **acervo**, não a rede social. O passo 7 passou
    a exigir o dossiê **também** na página do acervo e na gêmea, com a matriz de
    deploy do §6 do CLAUDE.md nomeada.

O advisor também se corrigiu: ele havia me dado `/api/v1/trecho/{path}#{ancora}`
como lacuna e mandou verificar a âncora de H2 antes de manter o passo 10.
Verifiquei — `internal/pagemarkdown/fidelidade_test.go:60-75` cobra que **toda
seção com título vira H2** sobre o acervo real. O passo 10 fica.
