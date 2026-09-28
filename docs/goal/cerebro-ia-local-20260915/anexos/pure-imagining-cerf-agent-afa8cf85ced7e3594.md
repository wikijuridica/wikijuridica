# REFUTAÇÃO ADVERSARIAL — frente REDE SOCIAL DE IA (ângulo dado e protocolo)

Data: 2026-09-15. Alvo: `/home/rafael/.claude/plans/pure-imagining-cerf-agent-a4f7eba0eab702b28.md`.
Modo: somente leitura. Toda evidência abaixo foi lida por mim no disco vivo ou medida por mim.

## VEREDITO: IMPLEMENTÁVEL COM EMENDA

A tabela M1–M13 do plano **sobreviveu à conferência**. Reproduzi M1 na origem
(200 / 1.786 B / 15 campos no acervo contra 404 / 30 B `page_not_published` na
rota social) e confirmei M5, M6, M8, M9, M10, M11, M12 e M13 no código. Cheguei a
acusar `idx_reacoes_alvo` de inexistente e **retrato**: ele está em
`internal/socialconteudo/esquema.go:132` e no banco vivo.

Os defeitos não são de medição — são de **ordenação, raio de explosão e três
guardas citadas ao contrário**. Duas quebram produção ou gate se executadas como
escritas (A9 e A5). Uma delas (A9) é justamente a única métrica com alvo binário.

---

## R1 — `socialisolation` aponta para o outro lado, e A9 colide com ele

**Alegação:** "Nunca FK em `data/ai/grafo.sqlite`: `socialisolation` reprova."

**Real:** `internal/socialisolation/socialisolation.go:1-17` prova que **o acervo
não arrasta o social**. `grep "grafo.sqlite\|data/ai" internal/socialisolation/` =
**0 ocorrências**. Ele não sabe nada sobre o grafo.

**A falha concreta é o inverso:** A9 põe a resolução de rota social em
`/api/v1/citar`, que vive em `internal/httpserver/api_citar.go:20,55` — e
`internal/httpserver` está no fecho de `cmd/server` (`socialisolation.go:69`
`pacoteDoServidor = "cmd/server"`). A regra (2), `socialisolation.go:118-196`,
acusa `social_isolation_acervo_toca_estado_social` para todo arquivo do fecho que
referencie marcador de estado social — **salvo** `classePermitida`, que exige
abrir o SQLite social com `mode=ro` **ou** `_pragma=query_only(1)` e falha aberta.

**Emenda:** A9 é viável, mas só pelo precedente que o plano não cita:
`internal/httpserver/mcp_social.go:15-28,193-195` usa **os dois** (`mode=ro` +
`_pragma=query_only(1)`) e :28 registra que o arquivo não pode nomear
`var/social/social.db` dentro dele, justamente por causa do gate. Escreva isso no
passo. E o limite do grafo precisa de guarda **de verdade** (um teste), porque a
citada não existe.

## R2 — A única métrica binária é inalcançável como especificada

**Alegação:** citabilidade = "200 com os **MESMOS 15 campos** do acervo".

**Medido por mim:** os 15 campos são `approved_at, area, author, html_sha256,
instrucao, markdown_sha256, markdown_url, oab, path, referencia_abnt,
reviewed_at, sources, title, url, verificacao`.

**Falha:** `html_sha256` e `markdown_sha256` são hash de **arquivo estático** com
linha no `published_manifest`; `approved_at`/`reviewed_at` vêm de lá. A página de
tema social é **dinâmica** e seu HTML muda a cada comentário ou refutação nova.
Um `html_sha256` sobre página mutável é citação que envelhece no instante
seguinte — exatamente o defeito que a §4 do próprio plano desenha o URN
(`:{corpo_sha256[0:16]}`) para impedir. As duas seções se contradizem.

**Emenda:** o `citar` social devolve URN + `corpo_sha256` **por objeto**, não
hash de página; e a métrica troca "MESMOS 15 campos" por um schema social
nomeado, com os campos que têm significado estável.

## R3 — A8 é o passo que enche a rede e roda sobre caminho com ZERO execuções

**Medido por mim no banco vivo** (`data/ai/fila.sqlite?mode=ro`):
`SELECT DISTINCT tipo FROM tarefa` = `embed_pagina`, `extrair_dispositivos`,
`medir_modelo`. **`gerar_comentario_autoridade` = 0 linhas, sempre.** O código
existe (`internal/cerebro/comentario.go:36,257`; `cmd/cerebro/main.go:252`;
`cmd/cerebro/comentarios.go:166`) e nunca foi exercido.

**E `data/ai/publicacoes_cerebro.jsonl` NÃO EXISTE no disco** — o ledger de
proveniência do DEC-059 jamais foi escrito. A cadeia inteira de publicação do
cérebro tem zero execuções.

**Vazão real do cérebro, medida por mim** (única tarefa que ele de fato roda),
`extrair_dispositivos` concluídas por hora (UTC): 80, 188, 120, 152, 120, 68,
116, 115, 140, 116, 91 nas **11 horas cheias**, mais 66 na hora corrente
parcial, que **descarto**. Logo **1.306 em 11 h = 118,7/h** (a hora parcial
incluída daria 114,3/h; uso a das 11 horas cheias). Pendentes: **34.085** ⇒
**287 h = 12,0 dias** só para drenar o que já está na fila, nos mesmos 4 núcleos
e sob `MemoryMax=12G`.

Extração é *prefill*-dominada com ~100 tokens de saída. Um comentário de
autoridade é geração longa; o contrato mede geração em **2,9 tok/s**
(`qwen3.5:9b`). A §6 do plano lista o que quebra primeiro — purga, SQLite,
observatório — e **omite a única restrição com número medido**.

**Emenda:** A8 exige sonda antes da promessa: enfileirar N=20
`gerar_comentario_autoridade`, medir s/peça e tok/s reais, derivar o teto. E
"11.039 salas passam a ter o que anunciar" só se escreve depois desse número.

## R4 — A ordem de A5 abre exatamente a janela de laço de boot que o contrato proíbe

**Plano A5:** "binário no disco → JSON → swap → restart".
**Contrato (CLAUDE.md §1):** o campo que o binário recusa "só entra no disco
**junto com** o swap do binário e o restart".

**Verificado:** `internal/socialpolicy/policy.go:295` `DisallowUnknownFields`;
`cmd/social/main.go:112` `log.Fatalf("boot: %v", err)`;
`systemctl show wikijuridica-social` ⇒ `Restart=always`, `ActiveState=active`
desde 2026-09-11.

**Falha:** entre "JSON" e "swap" o binário **velho** está no ar com um JSON que
ele rejeita. Qualquer restart nessa janela — crash, ou o earlyoom que em
2026-09-08 já matou `llama-server` e os servidores MCP — vira `log.Fatalf` +
`Restart=always` = **laço de boot da rede social inteira**.

**Emenda:** swap do binário **primeiro**, JSON depois, restart por último; e um
Load de ensaio contra o binário novo antes de o JSON tocar o disco.

**A emenda tem janela simétrica, e ela precisa ser fechada junto.** "Swap
primeiro" só é seguro se o binário **novo** tolerar o JSON **velho** — um crash
entre o swap e a escrita do JSON põe o binário novo sobre a política antiga, com
o mesmo `log.Fatalf` e o mesmo `Restart=always`. Logo a seção `refutacao` tem de
nascer **opcional, com defaults no código**, e só então a ordem swap→JSON→restart
fecha as duas pontas. Sem isso o conserto é metade de conserto.

## R5 — A purga síncrona está DENTRO do mutex global de publicação (M5 e §5 não foram compostas)

**Verificado:** `cmd/social/interno.go:389-390` `sv.publicarMu.Lock(); defer
Unlock()`; a purga é chamada em `:550` (comentário) e `:609` (resposta), **dentro
do mesmo mutex**; `cmd/social/escrita.go:350-379` chama
`socialpurga.Invalidar(r.Context(), ...)` sem goroutine;
`internal/socialpurga/borda.go:66` `http.Client{Timeout: 30 * time.Second}`.

**Falha 1:** toda publicação do cérebro segura um mutex global através de uma
chamada HTTP externa de 30 s. Uma resposta lenta da Cloudflare trava **toda** a
publicação por 30 s.

**Falha 2, mais fina:** o contexto é `r.Context()`. Se o cliente do cérebro
desconecta, a purga é cancelada no meio. `invalidar.go:51-76` faz
`origem.Descarta` **antes** de `borda.Purga`, e `borda.go:82-100` devolve
`purgadas` parcial no primeiro lote que falha — logo o cancelamento deixa origem
descartada, borda velha e lote pela metade.

**Emenda:** **A14 precede A8**, não o contrário. E a purga sai de `r.Context()`
para um contexto próprio com deadline próprio.

## R6 — O alvo do §7 mora em pacote COMPARTILHADO: raio de 11.106 páginas não nomeado

**Alegação:** "o gate de conteúdo social tem ponto cego documentado
(`gate.go:10-21`): `hasNearbyNegation`".

**Real:** `internal/socialconteudo/gate.go:10-21` é o bloco de imports e o `type
Fonte`. `hasNearbyNegation` está em **`internal/oabgate/oabgate.go:805-830`**,
alcançado por `oabgate.CheckCampos` (`socialconteudo/gate.go:110`) e
`CheckResposta`. `internal/cerebro/gate.go:11` apenas **documenta**.

**Falha — e aqui eu corrijo a mim mesmo.** Minha primeira versão disse que o raio
era de **11.106 páginas** porque `oabgate.CheckPage` guardaria o acervo. **Medi
sem truncar e é falso:**
`grep -rn "oabgate.CheckPage\|CheckPageWithIdentity(" internal/ cmd/ tools/
--include=*.go | grep -v "_test\|^internal/oabgate/"` devolve **zero linhas**.
`CheckPage` não tem chamador de produção — ele é, ele próprio, um caso do defeito
que `socialisolation.go` rule (4) nomeia: "foi assim que internal/oabgate passou
a existir sem chamador". **O acervo não chama oabgate. Não medido que chame.**

O raio real continua existindo, e é outro: `hasNearbyNegation` é alcançado por
`CheckCampos`/`CheckResposta`, consumidos por `internal/cerebro/gate.go:207`,
`internal/socialconteudo/gate.go:110`, `socialconteudo/posts.go`,
`socialconteudo/habitualidade.go`, `internal/socialpolicy/policy.go` e por
`cmd/social/{interno,escrita,superficie,consulta,thread,cursos}.go`. Mexer no
predicado muda **todos** os caminhos de escrita social de uma vez — comentário de
autoridade, resposta, post e dúvida — e não apenas a refutação que o §7 mede.

**Emenda:** citar `oabgate.go:805`; parametrizar a janela/lista de negação por
chamador em vez de editar o predicado comum; e rodar o controle de falso
positivo sobre **os quatro tipos de escrita social**, não só sobre as 200
refutações. Não invocar o acervo como raio sem antes achar o chamador.

## R7 — O pré-requisito que A10 se auto-impôs olha o teste, a asserção e a superfície errados

**Plano:** "CONFERIR ANTES se `author_credential_test.go` conta JSON-LD na regra
das duas ocorrências de OAB."

**Resposta medida:** **não conta.** `internal/render/author_credential_test.go:39`
usa `semDadoEstruturado(html)` antes de contar, exatamente para excluir dado
estruturado.

**Mas há uma segunda asserção que o plano não menciona:** `:43-44` exige
`strings.Count(html, "identifier":"OAB/RJ 227191") == 1` — **exatamente uma** no
grafo. Um bloco `ClaimReview` que carregue o identificador da OAB quebra essa,
numa página do acervo.

**E a superfície:** o teste é `package render`, e `socialrender` **não importa**
`internal/render` (`internal/socialrender/socialrender.go:47` registra a decisão).
Ele nunca roda contra `/redesocial/tema/`. A10 mexe em
`socialrender/socialrender.go:435` (`DadosEstruturados`), que esse teste não guarda.

**A favor do plano:** JSON-LD sob `script-src 'none'`
(`internal/socialheaders/socialheaders.go:123`) **já é precedente** —
`socialrender.go:435` emite `<script type="application/ld+json">` e
`cmd/social/thread_jsonld_test.go` existe. A10 **não** quebra CSP. Conferi antes
de levantar a objeção, e ela não se sustenta.

**Emenda:** trocar o pré-requisito pelos dois reais — (a) a contagem de
`identifier` == 1 se `ClaimReview` algum dia pousar em página do acervo; (b)
`socialrender` **não tem** teste equivalente: escrever um.

## R8 — O orçamento de 30 KB já está todo alocado; os dois pilares do plano disputam o mesmo espaço

**Verificado:** `internal/socialrender/telasdotema.go:243-262`. O comentário do
código é explícito: "No tamanho real observado (325 palavras, ~3,2 KB) cabem
**nove** comentários; no teto de palavras, cabe **um**."

**Falha:** a §3 reusa o **mesmo** pool via `ComentariosNaPagina()`. Então A8
(encher 11.039 salas de comentários) e a refutação — os dois pilares do plano —
disputam ~9 vagas por tema. O plano trata isso como "a próxima decisão difícil";
ela está no caminho crítico de **A7**.

**Emenda:** declarar a banda HTML como **amostra** com link para a gêmea (que
serve a lista inteira), e dar à refutação sub-orçamento próprio, medido. O corte
não pode ser por mérito (Prov. CFOAB 205/2021 art. 5º veda ranking e nota, como o
próprio plano diz) — então a regra de corte tem de ser declarada e
não-meritocrática (cronológica), e isso precisa estar escrito **antes** de A7.

## R9 — B5/B8 reusam o `oauthserver` anulando a premissa que o próprio pacote diz torná-lo seguro

**Verificado:** `internal/oauthserver/oauthserver.go:210`
`Escopos: []string{EscopoRelatos}` — **fixo na hora do registro**; `:157`
`CotaDiariaDeRegistro = 20`; `:353-360` `escopoConcedido` só interseca o que o
cliente **já tem**. Logo B5 não se resolve em `:357`: sem tocar **`:210`** —
linha que o plano nunca nomeia — nenhum cliente jamais terá
`redesocial:escrever`.

**O mais grave é a premissa.** `oauthserver.go:159-176` justifica o registro
**anônimo** assim: "o que protege a escrita não é saber QUEM escreve... entra em
QUARENTENA (**nada é publicado por esta via**)". E `agentreports.go:13-22`:
"ela não publica... grava uma linha numa QUARENTENA que nenhum caminho de
publicação lê... Se relatar pudesse mudar estado de serviço, relatar viraria arma
de censura."

B8 dá a clientes registrados anonimamente um caminho para refutação
**publicada**. Isso inverte a premissa, e M9 cita `agentreports` como precedente
de "escrita de agente com proveniência" quando ele é precedente de
**não-publicação**.

**Emenda:** B5 inclui `oauthserver.go:210`. E a escrita de agente nasce
`em_moderacao`, promovida só pelo `decisao_de_moderacao` do cérebro (que A8 já
cria) — o plano tem a peça, mas precisa **escrever a premissa substituta** no
doc do `oauthserver`, ou o próximo leitor restaura o raciocínio antigo.

## R10 — O vocabulário de `reacoes` não admite os objetos novos, e alargá-lo é a reconstrução de doze passos

**Verificado:** `internal/socialdb/esquema.go:281-285`
`CHECK (alvo_tipo IN ('duvida','resposta','post'))`; e `:880-974`
`reconstroiReacoesParaAceitarPost` — "os doze passos", dirigidos pelo CHECK
gravado no disco.

**Falha:** o plano modela `alegacoes.alvo_tipo` na forma de `reacoes` e inclui
`comentario_de_autoridade` e `refutacao`. Para a tabela nova, ótimo. Mas
**refutação e comentário não podem receber reação** sem alargar o CHECK de
`reacoes` — e `internal/socialautoridade/esquema.go:14-27` diz por que isso é
caro: subir `socialdb.VersaoEsquema` "dispara a reconstrução dos doze passos
sobre o banco vivo, **e a v3 já está reservada** para a entrada da
`REFERENCES contas(id)`".

**E B4 colide com essa reserva:** o plano pede "socialautoridade/esquema.go
**v3**". A v3 já tem dono declarado no código.

**Emenda:** ou declarar que refutação não recebe reação (e escrever isso), ou
agendar o alargamento de `reacoes` como passo próprio citando o precedente dos
doze passos. B4 passa a **v4**, ou se funde à mudança já reservada para a v3.

## R11 — A6 transforma o portal em lavanderia de citação: `legalfacts` EXTRAI, não VERIFICA

**Alegação (§5 e A6):** `AvaliarRefutacao` reprova refutação sem "≥1 citação
**resolvida** por `internal/legalfacts`, o extrator que **NUNCA inventa URN**".
É a peça vendida como "inverter o prêmio à vagueza".

**Real, lido no pacote:** `legalfacts` é **extrator sintático**.
`norma.go:extractNormas` detecta sinais no texto e monta a URN por
`internal/lexml/urn.go:26 BuildURN` — **construção de forma canônica, sem
nenhuma checagem de existência**. `norma.go:84` diz o contrário do que o plano
supõe: quando a norma não casa o padrão, "a URN LexML **não se monta** e ela some
do JSON-LD e do link de fonte oficial **sem deixar rastro**". E `:346`: sem norma
identificável por perto, ele "ainda assim gera um fato artigo com **chave local
(não-URN)**".

**Falha concreta, e é o ataque 6 do roteiro pelo nome:** uma refutação que cite
**"Lei 99.999/2020, art. 5º"** — norma inexistente, forma perfeitamente canônica
— produz URN bem-formada e **passa** o gate de A6. O plano teria então publicado,
sob a assinatura do advogado (Rafael Toledo, OAB/RJ 227191), com `ClaimReview` e
bloco "Como citar", uma citação fabricada com aparato de verificabilidade
completo — que é exatamente o produto que a §12 do contrato vende a LLMs. O gate
desenhado para premiar a citação verificável premia a citação **bem-formatada**.
Pior que o defeito que ele veio corrigir: antes a vagueza vencia, agora vence a
fabricação competente.

**Isto não é risco inventado:** o CLAUDE.md §8 já diz "**Proibido inventar**
decisão, ementa, artigo, citação, data ou resultado", e §5 classifica "citação
legal mal atribuída" como **P1 permanente**, "a única classe com risco real sob a
OAB", porque "nenhuma medição automática a detecta".

**Emenda, e ela é barata porque a superfície já existe:** resolução tem de ser
conferida contra **existência**, não contra forma — medi
`GET /api/v1/citacoes` = **200** na origem, e o grafo tem 79.706 nós. A condição
de A6 passa a ser "URN que **resolve** em `/api/v1/citacoes` ou no grafo". E o
experimento do §7 ganha um **segundo braço de controle**: 20 peças com citação
**fabricada mas bem-formada** têm de reprovar **20/20**, ao lado das 20 com
promessa explícita. Sem esse braço, o experimento não mede a falha que importa.

---

## O que NÃO derrubei (conferido e de pé)

- **M1** reproduzido por medição própria: acervo 200 / 1.786 B / 15 campos;
  social 404 / 30 B `page_not_published`.
- **M5, M6, M8, M9, M10, M11, M12, M13** conferidos no código e no banco vivo.
  `idx_reacoes_alvo` existe (`socialconteudo/esquema.go:132` + banco vivo) — eu
  o acusei de inexistente e retrato.
- **Baseline de conteúdo confirmado por mim:** `duvidas`, `respostas`,
  `comentarios_de_autoridade`, `reacoes` = **0, 0, 0, 0** no banco vivo.
- **A escolha de `/api/v1/redesocial/` em vez de `/redesocial/` para POST está
  certa** e pelo motivo certo: `socialrender/exportacao.go:57-63` documenta a
  Dynamic Redirect que acrescenta barra final sob `/redesocial/`.
- **`DocumentoDaDuvida`** tem a forma que o plano descreve
  (`socialrender/duvida.go:134-143`), e os 1.756 B × 1.230 B de
  `exportacao.go:30-36` estão lá.
- **B7 procede:** não há `amazonbot.json` em `data/ops/bot_ip_ranges/` (14
  arquivos, nenhum dele) e o rDNS é Google-only —
  `crawleridentity/identity.go:43,53` (`DNSOutcomePTRDomainNotGoogle`,
  `AllowedGoogleCrawlerPTRSuffixes`), não `:525`, que é o `LookupPTR` genérico.
- **A10 não quebra CSP** — precedente já no ar.
- **Não achei O(n²) nem consulta sem índice** no modelo proposto: os UNIQUE de
  `alegacoes(alvo_tipo,alvo_id,trecho_sha256)` e
  `refutacoes(alegacao_id,autor_conta_id)` já servem de prefixo às leituras.
  A amplificação "3 triggers de FTS5" da §6 **superconta**: o DDL proposto não
  cria FTS para refutação (`socialconteudo/esquema.go` tem 5 triggers, nenhum
  para a tabela nova). Erro na direção conservadora.

## Ataques que NÃO se sustentam (e por que eu os abandonei)

- **"A10 quebra `script-src 'none'`"** — falso, precedente medido acima.
- **"`idx_reacoes_alvo` é inventado"** — falso, existe no DDL e no banco vivo.
- **"Falta índice para ler refutações por tema"** — falso, os UNIQUE cobrem.
- **Risco jurídico inventado** — não levantei nenhum. O `CHECK (nivel_sigilo = 0)`
  da §1 é mais restritivo que o `if` de hoje e se apoia em CPC art. 189, que é
  onde a lista de segredo é taxativa; a publicidade do ato continua sendo regra.

## O que o advisor mudou

Chamei-o com o arquivo já durável. Ele mudou quatro coisas, e uma delas era um
erro meu que teria custado a credibilidade da peça inteira:

1. **R6 estava errado e foi reescrito.** Eu afirmei raio de **11.106 páginas**
   apoiado em `oabgate.CheckPage`, sobre um `grep` que eu havia truncado com
   `head -20`. Ele mandou re-rodar sem truncar: **zero chamadores de produção**
   de `CheckPage`/`CheckPageWithIdentity`. Refiz a medição, confirmei, retirei o
   número e reformulei o raio para o conjunto real — os quatro caminhos de
   escrita social que consomem `CheckCampos`/`CheckResposta`. Sem essa correção
   eu teria levantado contra o plano exatamente o tipo de número não medido que
   a REGRA ZERO-C proíbe.
2. **R11 foi acrescentado.** Eu havia lido `norma.go:84,346` e concluído que
   `legalfacts` é extrator, não verificador — e deixei isso no raciocínio sem
   virar ataque. Ele apontou que essa é a lavanderia de citação do ataque 6, no
   passo (A6) que o plano vende como sua melhor peça. Medi `/api/v1/citacoes` =
   200 para dar emenda barata, e desenhei o segundo braço de controle do §7.
3. **R4 ganhou a janela simétrica.** Minha emenda ("swap primeiro") só fecha uma
   ponta: o binário novo sobre o JSON velho falha igual. A seção tem de nascer
   opcional com defaults.
4. **Rigor de "N de M" na vazão:** eu misturava a hora parcial corrente na média.
   Passei a declarar as 11 horas cheias (118,7/h) e a dizer qual usei.

Ele não contradisse nenhuma medição minha, então não houve reconciliação a fazer.
O veredito `IMPLEMENTAVEL_COM_EMENDA` ele confirmou.

## Sobre os ataques 4 e 8 do roteiro

- **Devolve decisão ao dono? Não.** O `decisao_de_moderacao` no socket do cérebro
  (`interno.go:399-406`) é o desenho certo e evita a esteira humana. **Mas** o
  plano importa `agentreports` como precedente, e o precedente dele tem
  "triagem (**ato humano**, por ferramenta separada)" escrito em
  `agentreports.go:16-17`. Herdar o precedente sem herdar a triagem precisa ser
  **dito**, senão o próximo leitor reintroduz a etapa humana proibida.
- **Custo proporcional?** A Trilha A sim: ela liga peças que já existem. A Trilha
  B pede a **primeira migração real** de `internal/contas`, cuja função hoje "só
  sabe confirmar" (`contas/esquema.go:66-77`, lido: a única `SchemaVersion` que
  existiu é a 1), para uma demanda com **zero consumidores medidos** — o próprio
  plano admite "nenhum dos 81 UAs que tocam `/mcp` jamais tentou escrever". O
  portão B1 está corretamente posicionado. Mantenha-o como portão e não o
  antecipe.
