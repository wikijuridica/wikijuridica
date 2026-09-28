# REFUTACAO ADVERSARIAL — REDE SOCIAL DE IA (angulo produto/viralizacao)

VEREDITO: **IMPLEMENTAVEL_COM_EMENDA**

O enquadramento (divergencia computada, atribuida, com proveniencia) e solido e as
superficies existem. Mas (a) a manchete e 71,2% derivada de modelo enquanto o texto
a chama de verificada contra corpus, (b) o caminho de publicacao que ele nomeia nao
publica, e (c) o unico caminho que funciona esta fechado por zero linhas numa tabela.

---

## A1 — O CONSERTO DO GATE (passo 5) ESTA FORA DO CAMINHO DE ESCRITA

`AvaliaPeca` tem **um** chamador fora de teste: `internal/cerebro/comentario.go:442`.
O caminho de producao nao passa por ele. Os tres caminhos de escrita que existem:

| caminho | gate real | mundo fechado de citacao |
|---|---|---|
| `cmd/social/interno.go:530` comentario -> `socialautoridade.Publicar` -> `socialconteudo/gate.go:101` | PII + `motivosDeVedacaoLegal` + `oabgate.CheckCampos` | **nao** |
| `cmd/social/interno.go:584` resposta -> `recusaPeloArt42Interno` (`:626-650`) | `oabgate.CheckResposta` | **nao** |
| `cmd/social/posts.go:222` mural -> `socialconteudo/posts.go:153` | `AvaliarComentario` (mesmo do 1º) | **nao** |

Consequencias: consertar `gate.go:255-259` muda o que o cerebro **propoe**, nunca o
que o servidor **aceita**; e o passo 8 ("Toda citacao verificada ANTES do INSERT",
citando `interno.go:400-406`) descreve codigo que nao existe ali.

**Emenda:** instalar o oraculo de precedente em
`socialconteudo.GateDeConteudo.AvaliarComentario` — unico ponto que 2 dos 3
caminhos ja atravessam — e em `recusaPeloArt42Interno` para o terceiro.

## A1b — A TELA 2 NAO TEM COMO ACONTECER: O SOCKET NAO CONHECE `posts_blog`

"Tela 2 — cerebro abre topico em `posts_blog` ... gate ANTES do INSERT
(`interno.go:400`)". O socket aceita **dois** tipos, `interno.go:99-100` e o switch
de `:400-406`: `comentario_de_autoridade` e `resposta`. Nao ha ramo de post; tipo
desconhecido devolve `tipo_invalido`. O unico caminho vivo ate `posts_blog` e o
formulario HTTP (`cmd/social/posts.go:222`), que exige **sessao com cookie** — e o
cerebro se autentica por HMAC em unix socket, sem sessao. A Tela 2, como escrita,
nao executa.

Ressalva de honestidade: o caminho do mural **nao** e um buraco de gate — ele roda
`AvaliarComentario` (`posts.go:153`). Mas e o variante `CheckCampos`, sem a
classificacao estrutural e a habitualidade do art. 42, I que `CheckResposta` roda
nos outros dois caminhos. Tres portas, duas reguas diferentes, nenhuma com citacao.

**Emenda:** terceiro tipo no socket com o gate do caminho 2, ou a tese de pauta
nasce como `comentario_de_autoridade` (ver A2).

## A2 — O DOSSIE RENDERIZADO NAO ENTRA NO SITEMAP, NAO SAI DO noindex, NAO DISPARA NADA

O plano vende "o primeiro conteudo entra no sitemap, dispara WebSub e IndexNow
**sem uma linha nova**". Medido nos cinco predicados:

| mecanismo | arquivo:linha | predicado real |
|---|---|---|
| sair de `noindex` | `cmd/social/tema.go:221` | so se `total > 0 \|\| len(comentarios) > 0` |
| entrar em `temas.xml` | `cmd/social/indexacao.go:498,530` | `TemasComDuvidaPublicada` U `TemasComComentarioPublicado` |
| dado do primeiro | `internal/socialconteudo/navegacao.go:395` | `JOIN duvidas d ON d.tema_id=t.id AND d.estado='publicada'` |
| Atom do tema | `internal/socialconteudo/atom.go:175` | `SELECT ... FROM duvidas d` — so duvidas |
| WebSub | `cmd/social/websub.go:52-58` | topicos = `/redesocial/feed.xml` e `/redesocial/perguntas/feed.xml`. **O feed por tema nao e topico.** |
| IndexNow | `cmd/social/indexnow.go:34` | a lista espelha o sitemap |

Um bloco renderizado a partir de `data/ai/divergencia_por_urn.jsonl` nao e duvida
nem comentario: a sala fica `noindex, follow`, fora do `temas.xml`, fora do Atom e
fora do IndexNow. O melhor ativo do portal nasceria invisivel para a exata
maquinaria de descoberta que o plano usa como argumento.

**Emenda:** publicar o dossie **como `comentario_de_autoridade`** pelo tipo de socket
que ja existe. Ele conta em `len(comentarios)` (tema.go:221), entra no `temas.xml`
por `TemasComComentarioPublicado` (indexacao.go:530) e roda gate dentro da
transacao. Zero predicado novo de render.
**Restricao que a emenda carrega (e A6 torna mordente):** `socialautoridade` e
append-only — o `Registro` expoe `Publicar`, `ComentariosDoTema`,
`ContagemDeComentariosDoTema`, `TemasComComentarioPublicado` e **nenhum metodo de
edicao**, e `esquema.go:209-214` tem trigger `BEFORE UPDATE` que da `RAISE(ABORT)`.
Cada refresh do indice empilha um dossie novo na sala em vez de corrigir o anterior.
Ou o dossie ganha estado de supersedido, ou a sala acumula N versoes contraditorias.

## A3 — BLOQUEANTE: O UNICO CAMINHO QUE FUNCIONA ESTA FECHADO POR ZERO LINHAS

`sqlite3 "file:var/social/social.db?mode=ro"`, medido agora:

```
temas 11039 | duvidas 0 | respostas 0 | comentarios_de_autoridade 0
posts_blog 0 | perfis 1 | perfis_advogado 0 | perfis_jurista 0 | contas 1
```

`internal/socialautoridade/socialautoridade.go:250` exige
`EXISTS(SELECT 1 FROM perfis_advogado WHERE perfil_id = ?)`, senao
`ErrInscricaoNaoVigente`. E `papelEfetivoInterno` (`interno.go:470-478`) deriva o
papel de `SeloDeOABVigente`: sem inscricao deferida o autor do cerebro resolve para
`leigo` e `Valida` recusa com `ErrAutorSemAutoridade`.

Existe provisionamento — `cmd/social-verificar-oab` (Pedir + Deferir,
`main.go:681`) — e o plano **nao o nomeia**. Ate ele rodar, todo passo 7 e 8 e
inalcancavel. E ato de identidade, nao revisao de conteudo: permitido, mas tem de
ser passo 0 declarado.

## A4 — A MANCHETE E 71,2% DERIVADA DE MODELO, E O PLANO A CHAMA DE VERIFICADA CONTRA CORPUS

O 233 confere, e "233 de 233 localizados no corpus" **tambem confere** (verificado
pelo join da `chave` do no, 233 de 233 casados). A proveniencia, nao:

```
select a.fonte, count(*) from arestas a join nos o on o.id=a.origem
 where a.destino=75737 and o.tipo='acordao' group by 1;
  data/ai/extracoes_dispositivos.jsonl .......... 166   (71,2%)
  data/corpus/.../stj-espelhos/registros-*.jsonl .. 67   (28,8%)
```

Confirmacao independente: varrendo `dispositivos_citados_urn` nas 60.359 linhas do
corpus, exatamente **67** registros citam `!art14` (132 dobrando `art14_par*`). E so
**19,9% (12.002 de 60.359)** do corpus tem qualquer URN — 48.357 tem lista vazia.

"resultado derivado do campo `dispositivo`" e verdade para o *resultado*; a
*vinculacao* ao art. 14 vem, para 166 de 233, de inferencia de modelo — sobre uma
extracao cuja folga ja esta medida (15,51% dos itens sem o numero do artigo no
proprio `texto_citado`; 19,0% apoiados em `NormaAtestadaNoTexto`, que testa a norma
no texto INTEIRO). O `sha256_conteudo` atesta o **texto** do acordao; nunca que ele
cita o art. 14. Vender "verificada contra um corpus hasheado" e a afirmacao que nao
se sustenta.

**Emenda:** carregar `arestas.fonte` para dentro do dossie por item (a coluna ja
existe) e publicar o indice em duas linhas — subconjunto atestado como manchete,
subconjunto de extracao rotulado. Nunca um percentual fundido.

## A5 — A COLUNA "OUTRO" FUNDE 6 REFORMAS COM 6 FALHAS DE MEDICAO

A tabela do §1 **reproduz** (retrato: a primeira versao desta refutacao acusou
"nao reproduz" comparando populacoes diferentes — erro meu, corrigido). Sobre os
233, por classe:

```
REsp puro   n= 70 | negar 18 · dar 14 · dar_PARCIAL 6 · nao_conhecer 26 · SEM_CASAMENTO 6
agravo      n=163 | negar 118 · dar 2 · dar_PARCIAL 4 · nao_conhecer 23 · SEM_CASAMENTO 16
```

14/18/26 batem exatamente. O "outro 12" do plano = **6 dar_PARCIAL + 6
SEM_CASAMENTO**; o "outro 19" = 4 + 16 (o plano diz dar 3, eu meço 2 — 1 registro de
diferenca de regex).

Duas coisas incompativeis moram na mesma celula: **6 acordaos em que o merito FOI
reformado em parte** e **6 em que a medicao falhou**. Consequencias medidas:

- contando provimento parcial como reforma, REsp puro vai de 43,8% (14/32) para
  **52,6% (20/38)**, e agravo de 2,5% para **4,8% (6/124)**;
- `SEM_CASAMENTO` e **22 de 233 = 9,4%** nesta amostra — contra o orcamento de
  "~219 em 60.221 = 0,4%" do passo 2 (ver A7).

E o documento traz DOIS denominadores: a tabela soma 70 (14/70 = **20,0%**) e a Tela
1 imprime "32 · reforma 43,8% (14 de 32)", descartando em silencio "nao conhecer"
(26) e "outro" (12). Um produto cuja tese e "publicar sempre com denominador a
vista" embarca dois no mesmo arquivo.

**Emenda:** quatro classes, nao tres — `dar`, `dar_parcial`, `negar`,
`nao_conhecer` — mais `sem_casamento` como celula **separada e contada**; um
denominador escrito no byte ("reforma entre os julgados em que o merito foi
apreciado"); e a decisao explicita sobre parcial, que vale 8,8 pontos.

## A6 — O NUMERO VAI MUDAR POR CULPA DA NOSSA FILA, E A PAGINA VAI ATRIBUIR AO TRIBUNAL

`data/ai/fila.sqlite`, medido agora: `extrair_dispositivos` concluida **8.397**,
pendente **34.091** (19,7% feito). Os 166 de 233 edges de art14 ja vem desses 19,7%.
Quando os 80,3% restantes entrarem, a populacao cresce e o indice se move — sem
nenhum acordao novo julgado. O laco de retorno do plano diz "a divergencia MUDA —
acordao novo altera o indice"; a fonte dominante de mudanca, por muito tempo, sera
o dreno do proprio backlog. Combinado com A2 (append-only), a sala acumula dossies
divergentes cuja causa a pagina atribui ao STJ.

**Emenda:** carimbar o dossie com `extracoes_concluidas/total` e congelar a manchete
no subconjunto atestado (67), que nao se move com a fila.

## A7 — A COBERTURA DO PASSO 2 ERRA POR ~25x

Regex direta sobre `dispositivo`, 60.359 registros:

```
negar 39.235 (65,0%) · dar 6.925 (11,5%) · nao conhecer 6.721 (11,1%)
NENHUM CASAMENTO 7.026 (11,6%) · dispositivo VAZIO 348 (0,58%) · ambiguos 104
```

O plano orca "~219 sem casamento" (99,6%). So o campo literalmente vazio ja da
**348**. Na amostra atestada de art14 a perda e 22 de 233 (9,4%). Ressalva honesta:
a regex e minha, e uma melhor sobe a cobertura — mas o plano afirma 99,6% sem
medicao nenhuma, e 0,58% de dispositivo vazio e um piso que regex nao vence.

**Emenda:** medir antes de prometer; declarar N de M; teste de falso positivo sobre
os 104 ambiguos, que e onde "dar parcial" se esconde.

## A8 — O PASSO 8 ATRAVESSA UMA FRONTEIRA DE BINARIO QUE UM GATE DEFENDE, E COLAPSA A TRAVA 1

`cmd/social/mcp_social.go` **nao existe** (cite do §5); `grep AddTool cmd/social/`
devolve zero. As quatro ferramentas estao em `internal/httpserver/mcp_social.go`
(1.338 linhas), servidas pelo **cmd/server:8089**, enquanto o banco social e o
socket pertencem ao **cmd/social:8091**.
`internal/checks/ingress_rota_anunciada_test.go:41-43`: "a rota de agentsurface e'
servida SEMPRE pelo cmd/server: o cmd/social nao importa internal/httpserver
(socialisolation reprova)".

E o socket aceita **uma** origem: `interno.go:377` recusa tudo que nao for
`"cerebro"` com `origem_invalida`, sob uma chave HMAC unica
(`interno.go:364`, conferida antes do parse). Logo uma ferramenta MCP de escrita na
8089 teria de se autenticar no socket social **como o cerebro** — exatamente o
colapso de assinatura que a trava 1 do §7 existe para impedir.

**Emenda:** segunda origem + segunda chave + coluna `autor_classe` propria; ou a
escrita do agente externo mora em store proprio e nunca toca a credencial do cerebro.

## A9 — O PASSO 7 NO ACERVO REPUBLICA 11.106 PAGINAS E O PLANO NAO PRECIFICA

Uma `<section>` nova nao esta entre os blocos que
`tools/generate-page-content-revision` neutraliza (script + `<section
aria-labelledby="conteudos-relacionados">`), entao o hash de revisao de toda pagina
muda. O plano acerta que e texto e acerta o "sem --ressemear". O que ele omite e a
consequencia ja medida no CLAUDE.md §6: a publicacao zera mtime e ETag do acervo
inteiro e "os bots que revalidam rebaixam o acervo junto (medido duas vezes com o
meta-externalagent)". Com amazonbot em 3.446 req/24h e 70,2% de retorno, este e o
unico passo capaz de empurrar a metrica de sucesso do proprio plano para baixo.

**Emenda:** agrupar numa publicacao so e medir a taxa de 304 depois
(`tools/check-efeito-nos-bots`), com veredito pre-registrado.

## A10 — O PASSO 3 ESTA ERRADO NOS DOIS SENTIDOS

`arestas.tipo` e CHECK fechado de 10 valores, e **`julgado_por` ja existe com 62.966
arestas**: acordao->tribunal 60.221, sumula->tribunal 398, tema->tribunal 2.347;
`tribunal` tem 2 nos. E os atributos do no acordao ja trazem
`['base_legal','classe','data_julgamento','data_publicacao','ementa','fonte_url','numero_registro','relator','sha256_conteudo']`
— **`relator` esta la**; quem falta e `orgao_julgador` (so no `rotulo`, como texto).
O plano diz "orgao_julgador nao esta nem no blob atributos" (certo) e trata relator
como igualmente ausente (errado), e propoe um tipo de aresta que ja esta ocupado.

**Emenda:** migracao do CHECK antes de qualquer `INSERT` de tipo novo; reusar
`julgado_por` para acordao->orgao; relator sai do blob sem chamada de modelo.

## A11 — ESCALA: O QUE QUEBRA PRIMEIRO E O POOL DE 12 CONEXOES

A rede social e rota dinamica no `cmd/social` (8091), com `s-maxage=3600` (1 h — nao
os 604800 do acervo estatico) e pool de **`MaxAbertas = 12` / `MaxOciosas = 4`**
(`internal/sqlitepool/sqlitepool.go:127,139`) para o processo inteiro.
`indexacao.go:590` ja documenta o modo de falha: "cursor que nao fecha segura
conexao do pool; com o pool pequeno deste processo, alguns deles travam o servidor
inteiro". E `TemasComDuvidaPublicada` e **deliberadamente sem teto**
(`navegacao.go:388`: "ela e o predicado do sitemap, e por isso nao tem teto"), hoje
barata porque retorna 0 linhas. Se o passo 7 tiver exito, ela cresce de 0 para ate
11.039 linhas com `GROUP BY` por tema, no mesmo processo de 12 conexoes.

**Nao medido, e por que:** nao rodei carga contra 8091 (sessao e somente leitura, e
sondar escrita exigiria criar conta). Tambem **nao medido**: se o dossie e lido por
requisicao de `divergencia_por_urn.jsonl` ou carregado no boot — o plano nao diz, e
como `cmd/social` nao pode importar `internal/httpserver` (socialisolation), ele nao
reusa nenhum carregador do acervo e tera de nascer um pacote proprio.

**Emenda:** o carregador do dossie nasce em memoria no boot, com teto declarado; e
`temasNoSitemap` ganha paginacao antes de a primeira sala encher, nao depois.

---

## O QUE SOBREVIVE AO ATAQUE (para o plano nao ser sobrecorrigido)

- **O teto de 50 KB NAO e risco.** `htmlcontract.go:28` `HTMLBudgetBytes = 50000`;
  medido sobre 11.358 arquivos de `public/`: max **38.466** B, p99 30.040, media
  23.414, **0 arquivos >= 45.000**. Sobram 11,5 KB na pior pagina. O dossie cabe.
- **A tabela de divergencia do §1 reproduz** (14/18/26 exatos). O produto tem
  materia; o defeito esta na apresentacao (A5) e na proveniencia (A4), nao no fato.
- **Verificados e corretos:** `papeis.go` (4 papeis; `recebemCaso` unexported
  :110-119), `interno.go` (HMAC antes do parse :364, serializado :390, 2 tipos
  :99-100), `escrita.go:38-41` ("o gate do art. 42 roda ANTES da escrita"),
  `mcp.go:388` (`claims.TemEscopo(oauthserver.EscopoRelatos)`), `mcp.go:363`
  ("fila de triagem humana" — **o passo 9 esta certo**), `oauthserver.go:44`
  (`EscopoRelatos` unico escopo; o plano disse :46), `agentes.go:78`
  (`/redesocial/llms.txt`), `fidelidade_test.go:63-73` (toda secao com titulo vira
  H2 — **a ancora do passo 10 se sustenta**), `internal/socialantiabuso` (4 modulos),
  `publicacao.go:76-87`, `comentario.go:433`.
- **§3 esta certo no fundo, errado na cite.** Precedente nunca resolve — mas a prova
  nao e `gate.go:47-49` (comentario), e sim `api_citacoes.go:90-95,316-317`:
  `Resolvida = true` so quando `CanonicalKey` comeca por `urn:lex:`.
- **Passos 2, 4 e 12 sao deterministicos** e nao enfileiram atras das 34.091 tarefas.
- **O corpus tem os campos prometidos**: `id_fonte`, `classe`, `numero_processo`,
  `orgao_julgador`, `relator`, `data_julgamento`, `fonte_url`, `sha256_conteudo`,
  `nivel_sigilo`. `inteiro_teor` vazio em 60.221 de 60.221 — o plano ja admite.
- `comentario_de_autoridade` **aceita** `PapelAdvogadoVerificado` (`interno.go:521`,
  `socialautoridade/comentario.go:140-141`, DEC-059): o desenho da assinatura do
  advogado e legitimo; falta so a linha de A3.
- Gap nao explicado: **60.359 linhas no disco contra 60.221 nos `acordao`** no grafo
  (138 de diferenca). Nao medido se sao duplicatas ou descartes.

## NORMA: NENHUMA OBJECAO LEVANTADA

Nao encontrei violacao, e nao invento risco que a lei nao impoe.
`processotela.go:16-17` ja recusa `nivelSigilo > 0` citando CPC art. 189. Processo
judicial e ato publico (CPC 189; CF 5º LX, 37 caput, 93 IX), entao o passo 11 nao
viola norma: o limite e **tecnico** (teto de requisicoes que o operador publica,
clausula 3.13 do DataJud), nao juridico. Prov. 205/2021 e CED 39-47-A alcancam
publicidade, nao o dossie informativo.

## REVISAO HUMANA / DECISAO DEVOLVIDA AO DONO

Um ponto vivo: `internal/cerebro/gate.go:10-21` termina dizendo que o ponto cego de
`hasNearbyNegation` "**so a leitura humana cobre**". O passo 6 mede FP/FN mas nao
substitui esse controle compensatorio — e leitura humana como etapa de esteira esta
proibida. **Emenda:** o passo 6 entrega detector, nao so medicao.

---

## O QUE O ADVISOR MUDOU

Quatro correcoes, uma delas num erro meu de metodo:

1. **A5 estava errada, e do jeito que eu acusava o plano de errar.** Meu script
   recuperava so 67 `id_fonte` de 233 arestas, porque as 166 vindas de
   `extracoes_dispositivos.jsonl` tem `evidencia` de outra forma, sem a chave
   `id_fonte` — o `.get("id_fonte","")` as descartava em silencio. Eu comparei meu
   subconjunto de 67 com a populacao de 233 do plano e conclui "nao reproduz".
   Refiz pelo join da `chave` do no (`acordao:STJ:000816609`): **233 de 233 casam**,
   e a tabela do plano reproduz exatamente (14/18/26). Retratei a acusacao e A5
   virou o ataque certo e mais duro: a coluna "outro" funde 6 reformas parciais com
   6 falhas de medicao, e isso vale 8,8 pontos na manchete.
2. **Faltava o buraco do `posts_blog`**, que eu tinha achado e deixado de fora. Ele
   entrou como A1b — e aqui **contrariei o advisor com evidencia primaria**: ele
   disse que `CriarPost` roda "quarentena + orcamento only, zero oabgate";
   `internal/socialconteudo/posts.go:153` chama `a.gate.AvaliarComentario`. O ataque
   correto nao e ausencia de gate, e sim que o socket nao tem ramo de post e o
   cerebro nao tem sessao: a Tela 2 nao executa.
3. **Faltava o angulo 3 (escala).** Entrou como A11, com numero medido (pool de 12,
   `s-maxage=3600`, `TemasComDuvidaPublicada` sem teto por desenho) e com "nao
   medido, e por que" nos dois pontos que nao apurei.
4. **A emenda de A2 estava meio-especificada.** `socialautoridade` e append-only
   (`Registro` sem metodo de edicao; trigger `BEFORE UPDATE` com `RAISE(ABORT)` em
   `esquema.go:209-214`), entao publicar o dossie como comentario empilha versoes a
   cada refresh de A6. A restricao passou a constar dentro da propria emenda.

Menores, tambem aplicados: o gap 60.359 vs 60.221 ficou escrito como nao medido, e
A4 passou a afirmar "233 de 233 no corpus" como **verificado**, nao assumido.
