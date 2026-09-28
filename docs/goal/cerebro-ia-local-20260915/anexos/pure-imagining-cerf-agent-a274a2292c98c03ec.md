# Refutação adversarial — arquitetura de MODERAÇÃO da rede social de IA

Sessão 2026-09-15, PLAN MODE (somente leitura). Alvo: o plano de 779 linhas em
`/home/rafael/.claude/plans/pure-imagining-cerf-agent-ad11af5e88b35de6c.md`.

VEREDITO: **IMPLEMENTÁVEL_COM_EMENDA**. O mecanismo (registro de competência; juízo
que ordena e não remove) sobrevive ao ataque. **O ponto de cobrança e a calibração
do piso não sobrevivem.**

---

## 0. O que NÃO consegui derrubar (ataque 1: os arquivo:linha)

Conferi um a um. Todos existem e fazem o que o plano diz:

| citação do plano | conferido |
|---|---|
| `gate.go:10-21` ponto cego `hasNearbyNegation` | sim, comentário literal no cabeçalho do pacote |
| `gate.go:262-264` `fonte_fora_do_payload` só para URN resolvida | sim (`if !permitidas[c.URN]`, linha 262-263) |
| `gate.go:256` chave na fonte é passe livre | sim |
| `oabgate.go:599-602` `if loc == "" { return nil }` | sim, linha 600 |
| `api_citacoes.go:90-95` `Resolvida` só por parser determinístico | sim — e diz mais (ver A4) |
| `extracao.go:505` âncora literal descarta trecho ausente | sim |
| `triagem.go:195-230` `NormaAtestadaNoTexto` no texto inteiro | sim |
| `fila.go` `UNIQUE(tipo, chave, impressao, modelo)` | sim (EsquemaSQL) |
| `cuidado.go:16` `AcaoDoSinal = "abrir_fila_para_revisao_humana"` | sim, constante |
| `filas.go:98-134` `FilaDaCategoria` é função pura, teses 1/2 | sim |
| `schema.sql:231-247` `CHECK (revisor_id <> revisor_original_id)` | sim, linha 244 |
| `transparencia.go:104-117` `PorCodigo`/`NoLexico` | sim |
| `cmd/social/moderacao.go:100-110` fundamento ≥ 20 caracteres | sim, linha 107 |
| `cmd/cerebro/comentarios.go:42-50` gptbot ausente do ranking | sim, mapa fechado de 7 agentes |
| peça 2 punida por citar a Lei 11.771/2008 **corretamente** | **sim** — `resolvida:true, na_fonte:false` no JSONL |
| `VerificarTrilha` detecta bifurcação da cadeia | sim — caminha por `seq` e compara `anterior`; **não** levantei essa objeção |

O diagnóstico do oráculo (a peça 2 foi punida pela amplitude de citação correta,
não pelo REsp) está **certo**, e conferi no dado real.

---

## A1 — FATAL. O gate redesenhado não é o gate que admite conteúdo

`cmd/social/interno.go:627-661` (`recusaPeloArt42Interno`) é a régua do **servidor**
do socket. Ela monta `oabgate.RespostaDeAdvogado` com `Campos{Titulo, Corpo}` +
`Fontes` e chama **só** `oabgate.CheckResposta` (linha 650). Não há `Citacoes`, não
há `DispositivosPermitidos`, não há `ChavesDaFonte`, não há similaridade, não há
mundo fechado.

E `cmd/social` **não importa** `internal/cerebro`: `grep -rn "internal/cerebro"
cmd/social/*.go` devolve zero linhas (os 13 importadores são `cmd/cerebro`,
`cmd/generate-*` e `cmd/medir-*`).

E o plano de 779 linhas **nunca nomeia esse ponto**: `grep -n -iE
"interno\.go|recusaPeloArt42"` no arquivo devolve **zero linhas**. Nenhum dos 12
passos liga `pecagate` ao caminho de admissão.

Consequências:

1. `AvaliaPeca` é gate de **cliente**. A tese "o caminho de código que removeria por
   juízo não existe" é verdadeira e **irrelevante**: o caminho que **publica sem
   passar pelo piso** já existe, é o de produção, e o plano não o toca.
2. A justificativa do passo 2 ("importá-lo em `cmd/social` levaria o cliente Ollama
   para o binário social") **pressupõe** o import pelo servidor — que é a coisa
   certa. Mas nenhum passo o especifica: o passo 2 entrega "`internal/pecagate/` +
   cerebro reexportando, **zero mudança de comportamento**". Zero mudança de
   comportamento é exatamente o que não pode ser, porque o comportamento que falta
   é o servidor cobrar o que o cliente alega.

**Emenda mínima:** acrescentar o passo que falta — o piso e o mundo fechado passam a
ser cobrados em `cmd/social/interno.go:650`, com `internal/pecagate` importado por
`cmd/social`. Isso torna o passo 2 **pré-requisito**, não condicional, e muda o seu
artefato de "zero mudança de comportamento" para "a admissão do socket passa a
reprovar o que hoje ela aceita" — com as três peças reais como oráculo do
comportamento novo **no servidor**, não só no cliente.

---

## A2 — FATAL. O piso quebra 34 asserções, não 3 — e reprova os 15 modelos de comentário BOM deste repo

O plano não erra por omissão: ele **afirma** ter enumerado o raio de explosão. Linha
238: *"**Três testes existentes ficam vermelhos, e é intencional — não é dano
colateral a descobrir no meio da implementação**"*; linha 761 repete que o plano
"nomeia os testes que ficam vermelhos". É essa afirmação que a medição falsifica.

`pecaAprovadaBase()` (`internal/cerebro/gate_test.go:84`) devolve uma `Peca` **sem
`Citacoes`, sem `ChavesDaFonte`, sem `DispositivosPermitidos`**. As 15 fixtures
aprovadas (`grep -c '^\tadd(' internal/cerebro/gate_test.go` = **15**) têm portanto
**zero** citações. `fixturesReprovadas()` faz `tema := fixturesAprovadas()
["consumidor_garantia"]` (linha 256) e clona — as **19** fixtures com lista EXATA de
motivos (`grep -c 'out\["'` = **19**) herdam zero citações.

Com `PisoDeAncorasEspecificas = 1`, cada uma dessas 34 fixtures ganha `sem_ancora`:
as 15 aprovadas deixam de aprovar; as 19 reprovadas passam a devolver
`[motivo_esperado, sem_ancora]` e quebram a igualdade exata. Medição adicional:
das 10 literais `CitacaoVerificada{}` nos testes do pacote, **0** setam `Tipo` — logo
nem p8 nem p9 produzem âncora qualificada.

O plano declara "**três** testes ficam vermelhos: `gate_test.go:309`,
`comentario_test.go:230-231`, `gate_mundo_fechado_test.go:32`". A conta medida é
**34 asserções em `gate_test.go`**, mais `gate_mundo_fechado_test.go` (que fica
vermelho pelo passo **3**, não pelo 4: o `strings.Join(v.Motivos,",") !=
"citacao_nao_resolvida"` da mutação passa a ver dois motivos), mais
`comentario_test.go`.

Pior que o número: os 15 corpos foram **escritos à mão pela engenharia deste repo
como modelo de comentário aprovado** e citam "O Código de Defesa do Consumidor",
"A Constituição Federal", "O Código Civil" — **sem um único artigo numerado**. Isto é,
a definição interna de comentário bom é exatamente a peça que o piso reprova. Quem
executar o passo 3 vai encontrar 34 vermelhos e a saída barata será afrouxar o piso —
fraude de gate por cansaço.

**Emenda mínima:** antes de escolher a constante, reescrever as 15 fixtures
aprovadas com âncora real (é trabalho de conteúdo, não de gate) **ou** declarar o
piso aplicável só a peça de agente, com as fixtures do acervo isentas por campo
explícito na `Peca` (`Origem`), nunca por exceção silenciosa dentro do detector.

---

## A3 — FATAL. O instrumento que derivou o piso não mede o que o plano diz que ele mede

Medido em `data/ai/grafo.sqlite` (ro):

```
nós tipo='pagina'                                        11.104
páginas com ≥1 aresta (cita→dispositivo ∪ aplica→sumula)  5.815
páginas com ZERO                                          5.289
percentis sobre TODAS as 11.104:  p25=0   p50=1   p75=3
```

**Retrato honesto de um erro meu primeiro:** eu ia declarar que "47,6% do acervo não
cumpre o piso". Rodei o controle positivo antes de afirmar o zero, e ele me refutou.

Amostra por *stride* determinístico (passo 88) sobre as 5.289 páginas "sem âncora",
lendo o HTML publicado em `public/**/index.html` e procurando `urn:lex:…!artN`:
**29 de 60 têm URN de dispositivo resolvida no HTML servido** (31 de 60 não têm; 0
sem arquivo). Exemplos: `/administrativo/acidente-em-servico-nao-reconhecido/`
(`…;8112!art212`), `/bancario/consignado-clt-como-funciona/` (`…;10820!art2`),
`/cidadania/cpf-primeira-via-adulto/` (`…decreto:2018-11-22;9580!art32`).

A causa está na proveniência das arestas. `SELECT fonte,tipo … WHERE origem é
página`: as âncoras de página vêm de **dois artefatos derivados** —
`derivado:frente-d` (`aplica`, 22.789) e `content/legal_cocitation_index.jsonl`
(`cita`, 8.516). A extração do cérebro (`data/ai/extracoes_dispositivos.jsonl`,
102.771 arestas `cita`) tem por chave `acordao:STJ:…`, **não página** — conferido na
fila: as 34.091 pendentes são todas acórdão. Então a fila pendente **não** explica as
5.289, e o número tampouco é conteúdo: é **cobertura de artefato**.

Logo, o que cai é a derivação, e cai duas vezes:

1. **Tautologia.** "p25 sobre as 5.815 ancoradas" é percentil de um conjunto cujo
   mínimo é 1 **por construção** — qualquer percentil dele é ≥ 1. Precedente do
   repo: `amostra-enriquecida-mede-o-enriquecimento`.
2. **Instrumento incompleto.** A população de 5.815 subconta em ~48% da população
   que ela exclui (29/60 medido). O plano trata `5.815` como "as páginas ancoradas
   do acervo"; é "as páginas presentes em dois derivados". E a métrica declarada
   ("mediana ≥ p50 (=2) **do acervo**") herda o mesmo defeito: p50 do acervo pelo
   mesmo instrumento é **1**, não 2.

Quanto do acervo realmente ficaria sem âncora é **não medido pelo plano**. Minha
estimativa, marcada como estimativa a partir de 60 páginas: ~24,6% (≈2.733 de 11.104)
sem nenhuma URN de dispositivo resolvida no HTML.

**Emenda mínima:** derivar o piso do **HTML publicado** (parse de `urn:lex:…!art`
sobre `public/**/index.html`, população = 11.104, N de M declarado), não do grafo; e
só então escolher a constante — com a régua do veredito escrita antes do número, que
é o que o passo 6 já promete e o passo 3 não cumpre.

---

## A4 — A única âncora que aprova a peça 2 é ECO da fonte, e o plano proíbe eco

`internal/httpserver/api_citacoes.go:90-95` é explícito: *"súmula, tema e precedente
têm chave própria e ficam **sempre** com `Resolvida=false`, porque este pacote **não
tem como verificar** essas chaves contra uma fonte oficial"*. O passo 5 mede
REsp 1.794.991 = **0 de 60.221**. Logo "precedente **provado**" só pode significar
uma coisa: estar em `ChavesDaFonte` — que `gate.go:256` **já** trata como passe livre.

Então a peça 2 aprova por **repetir uma citação que a página-fonte já publica**. E o
passo 8 define exatamente esse ato como eco: *"refutação que repete as âncoras do
alvo é eco"*. O piso, na prática executável hoje, é "copie ao menos uma citação não-lei
da fonte" — e a fonte é o que o próprio prompt entrega ao modelo.

Some-se o passo 4: rebaixado `fonte_fora_do_payload` a aviso, `art. 5º da CF`
(`tipo=artigo`, `Resolvida=true`) passa a **contar como âncora** e a produzir só um
aviso. O risco admitido ("citar art. 5º da CF satisfaz o piso") não é teórico: o
passo 4 é o que o torna gratuito.

**Emenda mínima:** a âncora que conta não pode ser a que está em `ChavesDaFonte` —
tem de ser chave **distinta das da fonte**, ou provada pelo verificador do passo 5.
Com isso a peça 2 volta a reprovar, o oráculo de 3/3 cai, e é assim que tem de ser:
o passo 6 (pré-registrado) é o teste honesto, não as 3 peças.

---

## A5 — O passo 9 nomeia símbolo inexistente e mira o detector errado

`promessaComplementarRe`: **zero ocorrências** em `internal/` e `cmd/`. O que existe
é `captacaoComplementarRe` (`internal/cerebro/gate.go:324`), que é **captação**
(`chame`, `fale`, `whatsapp`), não promessa.

O ponto cego que o passo 9 quer fechar é `hasNearbyNegation`
(`internal/oabgate/oabgate.go:810`, usado em `oabgate.go:333`, dentro de
`checkResultPromise`). Esse pacote é o que `cmd/social/interno.go:650` roda em
produção **e** o que governa a publicidade do acervo inteiro. Mexer lá é mudar a
régua de 11 mil páginas publicadas — a regressão que o contrato proíbe. Mexer só em
`cerebro` não fecha o ponto cego no caminho que **admite** o conteúdo (A1).

**Emenda mínima:** o passo 9 não "muda `promessaComplementarRe`"; ele **cria** um
detector novo em `internal/pecagate`, por sujeito, que roda **ao lado** de
`oabgate.CheckResposta` e nunca dentro dele. A régua de FP=0 → motivo / FP>0 → aviso
fica, mas medida contra o acervo com o detector novo, não contra `hasNearbyNegation`.

---

## A6 — A remoção não chega à borda: até 3.600 s servindo o que a moderação removeu

Medido agora contra produção (UA do projeto + `X-Warming-Request: true`), em
`/redesocial/tema/administrativo/acao-improbidade-servidor-exigencia-dolo/`:

```
cache-control: public, max-age=600, s-maxage=3600
cf-cache-status: HIT      age: 11      200, 3.099 bytes, 0,134 s
```

Os 12 passos não têm **nenhum** que purgue a borda depois de uma decisão de remoção.
E o próprio repo escreve em `internal/moderacao/filas.go` (comentário de `Urgente`)
que em nudez não consentida e conteúdo infantil *"o dano cresce por hora de
exposição"* — a fila extrajudicial nasce com prazo curto contra uma borda que serve
por até **uma hora** depois de removido. A matriz do CLAUDE.md §6 já manda purgar o
que o deploy não cobre; decisão de moderação não é deploy.

**Emenda mínima:** decisão com resultado `remover` ou `restringir_alcance` dispara
purga por URL (rota do conteúdo **e** rota do tema, que embute o trecho) via
`tools/purge-edge-cache`, e a métrica passa a ser o tempo entre `decidida_em` e o
primeiro `MISS` medido na borda — não "zero decisão sem fundamento".

---

## A7 — A métrica `csp-report = 0` nasce vermelha, sem causa atribuída

`var/social/csp_violacoes_agregadas.jsonl`, superfície **pública**:

```
2026-09-15  script-src-elem 243   script-src 65
2026-09-14  script-src-elem 132   script-src 109
```

Com `duvidas = 0`, `respostas = 0`, `comentarios_de_autoridade = 0` — ou seja, **308
violações/dia com zero conteúdo social publicado**. O plano fixa "csp-report = 0 nas
rotas novas" sem nomear a causa da linha de base. Isso é vermelho permanente a ser
explicado depois: o padrão `vermelho-conhecido-é-atribuição`.

**Emenda mínima:** a métrica separa `blocked-uri` sob nosso controle de injeção do
cliente (extensão de navegador é a causa canônica de `script-src-elem` com
`script-src 'none'`) e fixa o alvo em zero **só** para a primeira classe, declarando
a segunda como linha de base medida de 308/dia.

---

## A8 — O teto de escrita já existe e é 60 r/m por IP — vem antes de qualquer custo de moderação

O nginx **vivo** é `/usr/sbin/nginx -c /opt/wiki/ops/nginx/standalone/nginx.conf -p
/opt/wiki/var/nginx/` (lido em `/proc/2556682/cmdline`) — **não** o
`ops/nginx/wikijuridica.conf` que está em `sites-enabled` e que **não tem nenhuma
location `/redesocial/`**. No config vivo:

```
:842   limit_req_zone $binary_remote_addr zone=wj_social_escrita:10m rate=60r/m;
:2064  location ^~ /api/v1/redesocial/ { limit_req zone=wj_social_escrita burst=10 nodelay; }
```

A chave é **o IP**. Agentes atrás do mesmo egress (OpenAI, Amazon, Anthropic)
dividem **1 escrita/s**. O plano discute 53–76 s por julgamento e 34 mil tarefas de
fila; numa viralização entre agentes o que quebra primeiro é a **porta de escrita**,
e a causa é configuração nossa — não física externa, então pela REGRA ZERO-C ela não
é teto, é atraso.

**Emenda mínima:** chavear a zona pela **conta autenticada** (não por
`$binary_remote_addr`), declarar o teto medido por conta, e registrar no plano que o
arquivo a editar é `ops/nginx/standalone/nginx.conf` — editar `wikijuridica.conf`
não serve tráfego nenhum.

---

## A9 — `julgar_peca` com prioridade default mata a extração (a direção do risco está invertida)

Medido em `data/ai/fila.sqlite` (ro): **todas** as 34.091 pendentes têm prioridade
**negativa** (−23 a −6); `medir_modelo` em −10. `Reivindicar` (`fila.go:380`) ordena
`prioridade DESC, id ASC`, e o schema declara `prioridade INTEGER NOT NULL DEFAULT 0`
(`fila.go:74`).

Logo `julgar_peca` nascendo com o default fica **acima de tudo que está pendente**.
Numa viralização a moderação **preempta permanentemente** `extrair_dispositivos` —
que é a fonte de 26,5% das arestas do grafo (104.002 de 393.081). O plano compara
"~10 dias de moderação contra 31,3 dias de fila já pendente" como se fossem filas
concorrentes em FIFO. Não são: é preempção total, e o lote de `Reivindicar` agrupa
por `tipo` + `modelo`, então o lote inteiro vira julgamento.

**Emenda mínima:** `julgar_peca` nasce com prioridade **explícita** e com teto de
fatia (alternância por tipo no lote), e a métrica inclui a vazão de
`extrair_dispositivos` antes/depois — senão a moderação paga o próprio custo com o
grafo que a sustenta.

---

## A10 — O oráculo do passo 1 não é reconstruível a partir do arquivo que ele cita

`data/ai/comentarios_gerados.jsonl` (3 linhas, `comentario_gerado_v1`) **não grava**
`DispositivosPermitidos`, `ChavesDaFonte` nem `TextoFonte` — só `citacoes[].na_fonte`.
Sem `TextoFonte` o caminho de `similaridade` (`gate.go:268`) fica descoberto na
fixture; `DispositivosPermitidos` só é inferível para as URNs que a peça citou.

E a peça 1 **não tem a chave `citacoes`**. O plano afirma "citações: 0" — inferência,
não leitura: o motivo `citacao_nao_resolvida` também é emitido por
`motivoDoCodigoOAB` (`gate.go:305-308`) a partir de três códigos do oabgate. Medi o
corpo da peça 1: 234 palavras, sem nenhum padrão de `citationPatterns` (cita
"Resolução 400/2016 da ANAC", "Código de Defesa do Consumidor", "Lei Geral do
Turismo" — nenhum casa `\blei\s*n?[o.]?\s*\d`). Portanto a peça 1 reprova por
**`tamanho`** (234 < 250) antes de o piso ser exercido: ela não testa o piso.

**Emenda mínima:** o passo 1 grava as entradas completas da `Peca` como fixture
versionada (`internal/pecagate/testdata/`), derivadas uma vez do acervo e
congeladas — e declara que a peça 1 exercita `tamanho`, não o piso.

---

## A11 — Assimetria de publicidade abre lavanderia, e a página já carrega a inscrição

A regra "post de agente de terceiro → `oabgate` não roda" cria o caminho: qualquer
texto que o oabgate reprovaria sob a assinatura do advogado é publicado ao se
declarar agente. Medido no HTML servido em produção: a página de tema
(`3.099 bytes`) carrega **`OAB/RJ 227191`**, 1 ocorrência.

**Não estou levantando risco de norma** — a ordem do dono é explícita que a OAB
alcança publicidade, não conteúdo informativo, e o Prov. 205/2021 governa a
publicidade *do advogado*. O ataque é o vetor 6: a superfície serve conteúdo de
terceiro **sob a inscrição do titular**, sem gate de publicidade nenhum, e um agente
adversário que queira anunciar tem o caminho aberto e barato.

**Emenda mínima (nenhuma bloqueia conteúdo informativo):** rodar `oabgate` em todo
conteúdo como **sinal de aviso contável** na série de transparência; e não emitir a
inscrição do titular na página cujo conteúdo principal é de agente de terceiro.

---

## A12 — Proporcionalidade: 12 passos para um fluxo de zero peças, e o recurso de FATO não tem quem assine

`var/social/social.db` medido agora: `duvidas 0`, `respostas 0`,
`comentarios_de_autoridade 0`, `denuncias 0`, `fila_moderacao 0`, `decisoes 0`,
`recursos 0`, **`revisores 0`**, `perfis 1`, `temas 11.039`.

O plano admite o fluxo zero no último risco, mas não tira a consequência: 12 passos,
um pacote novo, 34 asserções reescritas e uma mudança na régua do acervo — para um
subsistema que ainda não recebeu uma peça.

E o recurso: a §9 do plano diz *"o mecanismo existe; reuso"* apontando para
`schema.sql:231-247`, e em seguida define o recurso de FATO como *"re-execução
determinística … `impressao` nova = tarefa nova"* — que é `fila.sqlite`, e **não
escreve linha nenhuma em `recursos`**. As duas frases não fecham: o recurso
"disponível de imediato" não passa pela tabela que o plano diz reusar. E a tabela,
se passasse, não julga: `revisores` tem **0** linhas medidas, e `schema.sql:244`
exige `revisor_id <> revisor_original_id`. **Emenda:** ou o recurso de FATO grava
`recursos` com um revisor determinístico registrado (a versão do gate como
`revisor_id`, o que satisfaz o CHECK sem inventar pessoa), ou a §9 declara que o
recurso de FATO vive só na fila e que `recursos` continua vazia — uma das duas, não
as duas.

**Emenda mínima:** executar **agora** só o que mede sem tocar produção — passo 1
(oráculo, com A10 corrigido), passo 6 (custo real do julgamento) e passo 12 (gate
read-only de fluxo) — e mover para a frente de execução o que de fato falta e não
está no plano: **a régua em `cmd/social/interno.go:650`** (A1) e a **purga na
remoção** (A6). O piso (passos 3 e 4) espera o número do passo 6 e a correção de A3.

---

## Precisões menores (não derrubam, mas o plano afirma errado)

- A tese diz que o piso "reprova a peça que não cita nada — hoje a única aprovada".
  A peça 3 cita **4** itens (2 URNs distintas, `tipo=lei`). Ela não cita "nada": cita
  leis sem artigo. A frase certa é "reprova a peça sem âncora específica".
- `gate_mundo_fechado_test.go:32` fica vermelho pelo **passo 3**, não pelo passo 4
  (o plano o lista sob o 4). Importa para a ordem: o passo 3 já quebra antes de o 4
  rodar.
- O plano propõe quarentena em `internal/pecagate/abuso.go`; já existe a tabela
  `quarentena` em `var/social/social.db` (`conta_id`, `inicio_em`,
  `publicacoes_sobreviventes`). Duas quarentenas é deriva.
- A fila pendente medida hoje é **34.091**, não 34.118/34.217 (deriva normal, mas a
  camada tem de ser declarada: `data/ai/fila.sqlite`, `estado='pendente'`).

---

## Conferência contra o plano REAL (779 linhas), não contra o resumo

O advisor apontou que eu estava atacando o resumo do prompt. Abri o arquivo e
grepei cada acusação de omissão. Resultado:

| termo | ocorrências em 779 linhas | efeito |
|---|---|---|
| `interno.go`, `recusaPeloArt42` | **0** | A1 confirmado como lacuna real |
| `purga`/`purge`, `s-maxage`, `borda` após remoção | **0** (só `borda` na métrica de csp) | A6 confirmado |
| `wj_social_escrita`, `limit_req` | **0** | A8 confirmado |
| `prioridade` | **0** | A9 confirmado |
| `revisores` | **0** | A12 confirmado |
| "Três testes … ficam vermelhos" | linhas 238 e 761 | A2 vira falsificação de afirmação explícita |
| baseline de csp 243/dia | linha 676, **na mesma linha do alvo zero** | A7 vira contradição explícita |

---

## O que o advisor mudou

Três correções, e uma delas derrubou minha própria manchete:

1. **Eu estava atacando o resumo, não o plano.** Grepei as 779 linhas e converti
   cada "o plano não diz X" em evidência (tabela acima). Quatro ataques (A1, A6, A8,
   A9) sobreviveram com prova; dois (A2, A7) ficaram mais fortes, porque o plano
   **afirma** o contrário do medido em vez de apenas omitir.
2. **A1 tinha um sub-ataque errado.** Eu havia escrito que o passo 2 "se autocancela"
   porque `go list -deps` de `cmd/social` não mostraria Ollama. O `-deps` do plano é
   sobre `internal/cerebro`, não sobre `cmd/social`. **Apaguei o parágrafo.** O
   núcleo — `interno.go:627-661` cobra só `oabgate.CheckResposta` e nenhum passo liga
   `pecagate` ali — sobrevive sozinho e ficou mais preciso.
3. **A3 estava errado no número, e o controle positivo me pegou.** Eu ia declarar
   "47,6% do acervo não cumpre o piso". O advisor levantou que zero-âncora podia ser
   fila pendente. Não era (as 34.091 pendentes têm chave `acordao:STJ:…`) — era pior
   e diferente: **o instrumento é incompleto**. Amostra por stride, 29 de 60 páginas
   "sem âncora" **têm** `urn:lex:…!artN` no HTML publicado. Retirei o 47,6%, troquei
   a manchete de "o acervo não cumpre" para "o instrumento não mede o que o plano diz",
   e marquei minha estimativa (~24,6%) como estimativa de 60 páginas.
4. **A12 supunha que o recurso de FATO passava por `recursos`.** Li a §9 do plano:
   ele diz "reuso" a tabela e define o recurso como tarefa nova na fila. Reescrevi
   para a contradição real entre as duas frases, sem inventar a premissa.
