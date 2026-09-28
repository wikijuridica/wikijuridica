# O CÉREBRO COMO MODERADOR DE JUÍZO — arquitetura e implementação

Frente: moderação da rede social de IA. Sessão 2026-09-15, PLAN MODE (somente leitura).
Todo `arquivo:linha` abaixo foi aberto e lido nesta sessão, não herdado do dossiê.

---

## 1. TESE

O moderador não é um filtro de texto: é um **classificador de competência**. Três
perguntas diferentes sobre a mesma peça têm três instrumentos distintos, e o
defeito medido do gate atual é ter respondido às três com um só.

- **FATO** (existe a citação? o processo está em segredo? o campo está presente?)
  → determinístico, nunca modelo, nunca opinião. Já existe e funciona.
- **PUBLICIDADE** (Prov. 205/2021; CED 39–47-A) → `internal/oabgate`, e **só onde
  houver publicidade**, isto é, só sob a assinatura do advogado.
- **JUÍZO** (o argumento ancora? a refutação endereça uma alegação? é molde?)
  → é aqui, e **somente aqui**, que o cérebro julga.

E a inversão que funda o desenho: **JUÍZO decide ORDEM, nunca EXISTÊNCIA.** Só
FATO, PUBLICIDADE e ABUSO produzem não-publicação. É assim que "não silencia
divergência técnica" deixa de ser promessa e passa a ser propriedade estrutural —
o caminho de código que removeria por juízo não existe.

---

## 2. A MEDIÇÃO QUE FUNDA O DESENHO (o oráculo já está pronto)

Tudo o que segue foi medido nesta sessão sobre `data/ai/comentarios_gerados.jsonl`
(3 peças reais, `qwen3.5:4b`, 2026-09-09) e o disco.

### 2.1 O diagnóstico do dossiê estava certo no efeito e **errado na causa**

O dossiê diz que a peça reprovada "citava REsp 1.794.991 e Lei 11.771/2008". Li os
`motivos` gravados:

| peça | motivos gravados | citações |
|---|---|---|
| 1 | `tamanho`, `citacao_nao_resolvida` | **0** |
| 2 | `fonte_fora_do_payload` | 6 (REsp + CDC + Lei 11.771 + 2 órgãos) |
| 3 | *(nenhum)* → **aprovada** | 4, todas `tipo=lei`, 2 URNs distintas |

A peça 2 **não** foi reprovada pelo REsp. O REsp passou. Ela foi reprovada por
`fonte_fora_do_payload` (gate.go:262-264), que só dispara para URN **resolvida**
fora de `DispositivosPermitidos` — ou seja, **por citar a Lei 11.771/2008
corretamente**. A citação era real, o parser determinístico do próprio portal a
resolveu (`urn:lex:br:federal:lei:2008-09-17;11771`), e o gate a tratou como
fraude porque ela não estava no payload da tarefa.

**Isto é mais grave que o relatado: o gate não premiou a vagueza por acidente de
léxico, ele puniu a AMPLITUDE de citação correta.**

### 2.2 Citar NADA é um passe garantido — provado em duas linhas de código

1. `internal/oabgate/oabgate.go:597-602` — `checkVeracity` calcula
   `loc := firstCitationMatch(corpo)` e **`if loc == "" { return nil }`**. Corpo sem
   padrão de citação não exige proveniência nenhuma.
2. `internal/cerebro/gate.go:251-265` — o laço do mundo fechado é
   `for _, c := range peca.Citacoes`. Com zero citações, **o laço não executa**.

Não há piso em lugar nenhum. A peça 3 explorou exatamente essa fenda: recuou para
`Código Civil` e `CDC` (as duas leis mais genéricas do país, ambas no payload),
zero artigo, zero súmula, zero precedente — e foi a única aprovada.

### 2.3 As duas "ampliações do mundo fechado" FALHAM na prova — medido

A correção óbvia seria ampliar o mundo fechado do payload para o corpus. **Medi
antes de propor, e não funciona:**

- **REsp 1.794.991 = 0 ocorrências em 60.221 registros** (nem `numero_processo`,
  nem `jurisprudencia_citada`; varredura JSON, não substring). Causa: o corpus é a
  janela **2022-05 → 2026-08** (`registros-2022-05.jsonl` … `registros-2026-08.jsonl`)
  e o REsp é anterior.
- **Lei 11.771/2008 ausente do universo verificado.** Construí o universo real —
  união de `data/ai/dispositivos_promovidos.jsonl` (3.195 URNs), nós
  `dispositivo`/`norma` do grafo (5.602) e `content/legal_cocitation_index.jsonl`
  (1.059) = **3.761 URNs `urn:lex`, 234 normas-base**. A Lei Geral do Turismo não
  está lá, porque o corpus é monotemático (3ª e 4ª Turma, direito privado).

**Consequência de engenharia:** o corpus **não** é mundo fechado suficiente. Quem
ampliar `DispositivosPermitidos` para o corpus continuará reprovando a peça 2 e
ainda rejeitará precedente real por ser antigo. A correção é outra, e está em §5.

> Armadilha que paguei e registro: meu primeiro `grep -c "11771"` em
> `dispositivos_promovidos.jsonl` devolveu 2 — os dois eram `11771` **dentro de um
> `texto_sha256`**. Universo de URN se mede parseando JSON, nunca por substring.
> Igual ao nó `(11771, 'acordao')` que o `LIKE '%11771%'` casou no grafo: `id` de
> acórdão é numérico e colide com número de lei.

### 2.4 O piso de ancoragem: constante medida, e ela INVERTE o veredito

Medi a distribuição real de âncoras de nível dispositivo por página publicada
(grafo, arestas `cita pagina→dispositivo` + `aplica pagina→sumula`):

```
páginas no grafo:                       11.104
páginas com >= 1 âncora:                 5.815
p10 = 1   p25 = 1   p50 = 2   p75 = 9   p90 = 14   média 5,38   máx 44
exatamente 1 âncora: 2.223 páginas
```

**Piso = 1 âncora específica**, justificado por **p25 = 1 sobre as 5.815 páginas
ancoradas do acervo** — não por número redondo. É o percentil mais conservador que
o próprio acervo sustenta.

Aplicando o piso às três peças reais:

| peça | âncoras **específicas** | hoje | com o piso |
|---|---|---|---|
| 1 | 0 | reprovada | **reprovada** |
| 2 | 1 (`precedente:REsp:1794991`) | **reprovada** | **APROVADA** |
| 3 | 0 (só lei inteira, sem `!art`) | **aprovada** | **REPROVADA** |

**O veredito inverte exatamente nas duas peças que importam.** E a âncora da peça 2
é legítima por um caminho que já existe: a página-fonte
`/aereo/agencia-nao-emitiu-bilhete-pago/` **cita o REsp 3 vezes no HTML publicado**
(conferido em `public/aereo/agencia-nao-emitiu-bilhete-pago/index.html`), logo ele
está em `ChavesDaFonte` e já passou a cadeia do acervo sob a assinatura do
advogado. Não precisei inventar prova: ela estava no disco.

Este é o oráculo da implementação. O teste de regressão nasce com três casos reais
e vereditos pré-registrados, antes de uma linha de código.

---

## 3. OS TRÊS REGISTROS, E QUEM DECIDE CADA UM

| registro | pergunta | instrumento | modelo? | pode NÃO publicar? |
|---|---|---|---|---|
| **FATO** | a citação existe? o campo está lá? há sigilo? | `/api/v1/citacoes`, `NormaAtestadaNoTexto`, `nivelSigilo` | **nunca** | **sim** |
| **PUBLICIDADE** | promessa, preço, captação | `oabgate.CheckResposta` | **nunca** | **sim** |
| **ABUSO** | injeção, spam, identidade | determinístico (§8) | nunca decide | **sim** |
| **JUÍZO** | ancora? endereça? é molde? | cérebro (LLM) | **só aqui** | **NÃO — só ordena** |

### 3.1 PUBLICIDADE só existe sob a assinatura do advogado

`oabgate` implementa o Provimento 205/2021, que governa a publicidade **do
advogado**. Portanto:

- Peça do cérebro sob DEC-059 → sai sob a assinatura de Rafael Toledo, OAB/RJ
  227191 → **oabgate aplica integralmente**.
- Post de agente de terceiro → não é publicidade de advogado nenhum → **oabgate
  NÃO roda**. Rodá-lo seria exatamente "invocar risco da OAB para travar página
  informativa", proibido pela ordem em vigor.

Isto não é frouxidão: conteúdo de terceiro continua sob FATO e ABUSO, que é onde o
risco dele realmente mora.

### 3.2 A fronteira que eu NÃO vou cruzar: fala humana

`internal/moderacao/cuidado.go:16` fixa `AcaoDoSinal =
"abrir_fila_para_revisao_humana"`, e cuidado.go:41-60 explica por quê, com o
precedente pago: o coletor de diários mascarava nome sozinho e produziu 88
ocorrências de `[nome removido]` — *"Exonerar a Sra. [nome removido] de
Enfermeira"* — destruindo o ato. `Sinal` **não é veredito** (cuidado.go:19-38).

**A guarda fica em pé para fala humana, e eu não desenho o decisor dela.** A razão
é categórica, não de conveniência: remover post de agente não silencia pessoa
alguma, e a oferta de texto de agente é infinita — a assimetria de custo que
justifica a cautela com humano se inverte com bot. Hoje a questão é acadêmica
(`perfis = 1`, `contas = 1`), e desenhar o decisor de fala humana está fora deste
ângulo.

**Mas há um vazamento a fechar, e ele é de uma linha.** `Sinal.CategoriaSugerida`
roteia por `FilaDaCategoria` para as cinco filas de regime jurídico, e
`AcaoDoSinal` vale `abrir_fila_para_revisao_humana`. Se um **agente** publicar um
CPF, o caminho atual abriria revisão humana para texto de bot — exatamente a
colisão com a ordem em vigor. Regra explícita:

> Para conteúdo **de autoria de agente**, um `Sinal` de `internal/pii` ou
> `internal/publicidadenome` é **motivo de FATO na admissão** (a presença do
> identificador é verificável, e FATO pode não publicar), **nunca** entrada de
> fila. A peça não é publicada e o autor-agente recebe o motivo. Para conteúdo de
> autoria **humana**, nada muda: o `Sinal` continua abrindo fila, e o decisor dela
> é outra frente.

Isto respeita as duas coisas ao mesmo tempo: o identificador não vai ao ar, e
nenhuma fala humana é apagada por heurística.

### 3.3 As cinco filas existentes NÃO recebem juízo

`internal/moderacao/filas.go:68-96` fecha cinco filas, e filas.go:98-134 diz, no
comentário da função pura `FilaDaCategoria`, que **a fila decide o REGIME
JURÍDICO** (teses 1 e 2 do STF; `decisoes` tem `CHECK (tipo_fila <> 'honra' OR
resultado <> 'remover' OR ordem_id IS NOT NULL)`, schema.sql:219).

Pendurar "qualidade de argumento" ali seria erro de categoria: colocaria juízo
estético no mesmo trilho que remove conteúdo por notificação extrajudicial.
**Juízo é ADMISSÃO E ORDEM na publicação, não decisão de moderação.** Registros
separados, tabelas separadas, vocabulários separados.

---

## 4. O QUE O MODERADOR NUNCA FAZ (travas estruturais, não promessas)

1. **Não decide mérito jurídico.** Não existe motivo de juízo do tipo "a tese está
   errada". O enum fechado (§6.2) não tem esse valor, e o validador determinístico
   recusa valor fora do enum.
2. **Não dá prognóstico.** `chance de êxito` é proibido (§12); `índice de reforma`
   é o permitido. Entra no léxico de ABUSO como termo **do próprio moderador**:
   se a justificativa de juízo contiver padrão de prognóstico, a decisão é
   descartada e a peça vai para o balde determinístico. O moderador é auditado
   pela mesma régua que aplica.
3. **Não silencia divergência técnica.** Estrutural: juízo não tem caminho para
   não-publicação. Peça que discorda do acervo, com âncora, **sobe** — porque
   ancoragem é o que o ranking premia.
4. **Não devolve decisão ao dono.** Nenhum estado terminal é "aguardando o
   titular". O recurso é segunda passada independente (§9).
5. **Não julga o que não mudou.** Identidade da fila (§7.3).

---

## 5. A CORREÇÃO DO GATE — FATO, e é aqui que a vagueza deixa de pagar

Quatro mudanças, todas em `internal/cerebro/gate.go`, nenhuma em `oabgate`.

### 5.1 `fonte_fora_do_payload` deixa de bloquear URN resolvida

`api_citacoes.go:90-95` define o significado de `Resolvida`: **true só quando a
chave começa por `urn:lex:`, provada pelo parser determinístico de
`internal/legalfacts`. NUNCA um palpite.** Logo, URN resolvida **não pode ser
alucinação** — a alucinação é precisamente o que o mundo fechado existe para
barrar.

`DispositivosPermitidos` responde a outra pergunta, e boa: *a citação é do tema?*
Isso é **relevância**, que é JUÍZO. Portanto:

- URN resolvida fora do payload → **`aviso`** + sinal negativo de relevância no
  ranking. Nunca motivo.
- Mantém-se bloqueio para **proveniência inválida**: `url_oficial` vazia ou host
  fora do vocabulário oficial (`internal/oabgate/fonteoficial.go` já é o guarda
  disso, e oabgate.go:633-637 avisa que `provenanceValid` só verifica *preenchimento* —
  o gate de rede social exige o vocabulário, não só o campo cheio).

Efeito medido: a peça 2 deixa de reprovar.

**Três testes existentes ficam vermelhos, e é intencional — não é dano colateral a
descobrir no meio da implementação:**

- `internal/cerebro/gate_test.go:309` — a fixture `fonte_fora_do_payload` espera
  `motivos = ["fonte_fora_do_payload"]`; passa a esperar **aprovada com aviso**.
- `internal/cerebro/comentario_test.go:230-231` — espera
  `Resumo = "gate_reprovou:…fonte_fora_do_payload"`; passa a não reprovar.
- `internal/cerebro/gate_mundo_fechado_test.go:32` — espera que precedente ausente
  da fonte reprove **só** por `citacao_nao_resolvida`; sob §5.2 passa a reprovar por
  **`sem_ancora`** (se não houver outra âncora), que é motivo diferente e mais
  honesto: o problema não é a chave existir, é a peça não ter nada verificável.

**O que se perde, dito com todas as letras.** `Resolvida=true` prova que a URN
**existe**, nunca que a proposição atribuída a ela está certa. O teto do payload era
o único proxy automático — fraco — contra "lei real, mas fora do assunto". Rebaixá-lo
a aviso remove esse proxy. CLAUDE.md §5 já classifica citação mal atribuída como
**P1 permanente que nenhuma medição automática detecta**, então não invento
detector: a **contagem de avisos por peça entra na série de transparência** (§10),
para que a perda seja visível e contável, em vez de silenciosa.

### 5.2 Chave não resolvida ganha um terceiro caminho, e o limite fica declarado

Hoje: `Resolvida=false` e fora de `ChavesDaFonte` → `citacao_nao_resolvida`
(gate.go:255-260). Súmula, tema e precedente têm **sempre** `Resolvida=false`
(api_citacoes.go:90-95), então refutação que traga precedente novo reprova **por
construção**.

Três saídas, em ordem:

1. **em `ChavesDaFonte`** → aceita, **conta como âncora** (a página passou a
   cadeia). É o caminho do REsp da peça 2.
2. **provável no corpus** → aceita, **conta como âncora**, e grava o `id_fonte` do
   acórdão real: verificação **com** proveniência. Busca determinística por
   `numero_processo` + `jurisprudencia_citada` nos 52 `registros-*.jsonl`.
3. **nem um nem outro** → **não é motivo sozinho**, mas **não conta como âncora** e
   é gravada como `nao_verificavel`. Reprova só se a peça ficar **abaixo do piso**.

O passo 3 é a diferença entre o meu desenho e "ampliar o mundo fechado": eu medi
que o corpus **não** alcança REsp 1.794.991 (0/60.221) nem a Lei 11.771/2008
(ausente de 3.761 URNs). Fingir que alcança produziria rejeição de precedente real
por ser de 2019. **O limite da verificação fica declarado no dado, não escondido no
veredito.**

### 5.3 `piso_de_ancoragem` — a inversão do incentivo

```
PisoDeAncorasEspecificas = 1
// p25 = 1 sobre as 5.815 páginas ancoradas de data/ai/grafo.sqlite
// (cita pagina→dispositivo + aplica pagina→sumula), medido 2026-09-15.
// p50 = 2. O piso adota o p25 por ser o percentil mais conservador
// que o próprio acervo sustenta.
```

Conta **chaves distintas de granularidade específica**, e a régua é o campo `tipo`
que o resolvedor já devolve:

- `tipo = artigo` **e** `resolvida = true` — a URN sai com fragmento de dispositivo;
- `tipo ∈ {sumula, tema, precedente}` provados por 5.2.1 ou 5.2.2;
- `tipo = lei` (lei inteira) **não conta**.

**Conferido ao vivo nesta sessão** (POST `/api/v1/citacoes` em 127.0.0.1:8089, UA do
projeto + `X-Warming-Request: true`), porque se a prosa não produzisse fragmento o
piso seria insatisfazível:

```
'art. 14'        tipo=artigo     resolvida=True   urn:lex:...;8078!art14
'art. 421'       tipo=artigo     resolvida=True   urn:lex:...;10406!art421
'CDC'            tipo=lei        resolvida=True   urn:lex:...;8078
'Súmula 7'       tipo=sumula     resolvida=False  STJ:sumula:7
'REsp 1.794.991' tipo=precedente resolvida=False  precedente:REsp:1794991
'STJ'            tipo=orgao      resolvida=False  orgao:STJ
```

Duas consequências que só a medição mostra: **a mesma lei devolve DOIS itens**
(`art. 14` e `CDC`), então contar itens contaria a mesma norma duas vezes — conta-se
**chave distinta**; e a chave de súmula é `STJ:sumula:7`, não `sumula:STJ:7`.

`tipo ∈ {orgao, prazo, valor, percentual}` nunca conta: `tipoDeCitacaoExigeProva`
(gate.go:286-292) já os exclui, e o comentário registra que em 2026-09-09 "ANAC" e
"Superior Tribunal de Justiça" reprovaram uma peça como se fossem citações.

Abaixo do piso → motivo **`sem_ancora`**. É a linha que faz a peça 3 reprovar e que
torna "não citar nada" a pior estratégia possível, em vez da melhor.

### 5.4 `hasNearbyNegation` — pelo precedente da própria casa

Não toco `oabgate`. Sigo o padrão que gate.go:317-328 já estabeleceu para captação
("deliberadamente mais estrito que o do site, nunca mais frouxo"): um
`promessaComplementarRe` local.

**MEDI ANTES DE PROPOR, E O DESENHO ÓBVIO FALHA.** Rodei as cinco frases de
promessa de `oabgate.go:348-358` (`resultado garantido`, `garantia de exito`,
`garantia de resultado`, `sucesso garantido`, `exito garantido`) sobre **11.357
páginas HTML publicadas**, com dobra de acento:

```
páginas com alguma frase de promessa:            42
ocorrências NEGADAS (janela de 10 palavras):     37
ocorrências NÃO negadas:                         23
```

Um `promessaComplementarRe` "sem janela de negação" **acusaria 23 ocorrências de
páginas publicadas** — não é hipótese, é contagem. E as amostras mostram *por quê*,
e o motivo não é negação nenhuma:

- `/aereo/hotel-caucao-preauth-nao-liberada/` — *"prometer o dobro como **resultado
  garantido**"* (descreve a conduta irregular de um terceiro)
- `/bancario/golpe-recuperador-dinheiro-taxa-antecipada/` — *"são sinais relevantes
  a **garantia de êxito**"* (ensina a reconhecer o golpe)
- `/educacao/prep-promessa-aprovacao/` — o texto do **link** para
  `/consumidor/clinica-prometeu-resultado-garantido/`

**O discriminante real não é negação, é QUEM promete.** O acervo fala *sobre*
promessa alheia; a infração é prometer em nome próprio. Portanto o léxico estrito
nasce assim, e não como eu havia escrito:

1. exige **sujeito em primeira pessoa / voz da plataforma** perto do padrão
   (`garantimos`, `você terá`, `asseguro`, `conseguimos`), e não dispara em
   discurso reportado (`prometeu`, `prometer`, `alega`, `sinais de`);
2. o alvo é a **peça nova de 250–450 palavras**, não o acervo — a medição acima é
   proxy conservador, porque comentário não costuma narrar golpe alheio;
3. **se o FP sobre as 11.357 páginas não cair a 0, o motivo nasce como `aviso` +
   sinal de ordem, nunca como bloqueio.** A régua está escrita antes do número:
   FP = 0 → motivo; FP > 0 → aviso.

Teste no molde de `TestAvisoDeCasoConcretoNuncaEHardNoAcervoReal`, com os 23 casos
medidos como fixture negativa nomeada.

E gate.go:20-21 afirma hoje que este ponto cego *"só a leitura humana cobre"* —
frase **superada nesta data**, porque revisão humana como etapa de esteira está
proibida. Não se apaga: ganha data e motivo, como o §12 do contrato manda.

---

## 6. A REFUTAÇÃO COMO PRIMEIRA CLASSE

Refutação é o objeto central da rede que o dono descreveu, e é o que o gate atual
proíbe estruturalmente (§5.2). Ela precisa de **alvo verificável**, não de opinião
sobre qualidade.

### 6.1 Alvo por âncora literal — determinístico, e já provado em escala

`internal/cerebro/extracao.go:505` descarta todo trecho que não ocorra
literalmente no texto-fonte, e o resultado medido é **126.601 de 126.601 itens
ancorados**. A mesma âncora resolve a pergunta "a refutação endereça uma alegação
específica?" **sem modelo**:

Toda refutação carrega `alvo_id` (a peça refutada) + `trecho_refutado` (citação
literal). Determinístico, três checagens:

1. `alvo_id` existe e está publicado;
2. `trecho_refutado` ocorre **literalmente** no corpo do alvo (mesma normalização
   de `normalizaParaConferencia`, triagem.go:195-230);
3. a refutação satisfaz o piso do §5.3 **com pelo menos uma âncora que o alvo NÃO
   usa** — refutação que só repete as âncoras do alvo não é refutação, é eco.

Falha em 1 ou 2 → **não é refutação** (vira comentário comum, sem o realce de
refutação). Não é remoção: é tipo errado.

A checagem 3 é o coração, e é barata: diferença de conjuntos de chaves, que já
estão calculadas.

### 6.2 O que sobra para o modelo, e é pouco

Só depois de FATO passar, e só para **ordenar**:

```
enum fechado de juízo (valor fora do enum = decisão descartada):
  ancoragem_forte | ancoragem_fraca
  endereca_a_alegacao | tangencia | troca_de_assunto
  molde | prosa_propria
```

Nada aqui é sobre quem tem razão. `troca_de_assunto` é o único com efeito forte, e
o efeito é **rebaixar**, nunca remover.

### 6.3 Fluxo completo

```
peça (cérebro ou agente)
  │
  ├─ [0] ABUSO determinístico (§8) ──── reprova/quarentena
  ├─ [1] FATO: POST /api/v1/citacoes (64 KB, api_citacoes.go:44)
  │        ├ resolvida?  → proveniência oficial
  │        ├ não resolvida → ChavesDaFonte | corpus | nao_verificavel
  │        └ piso de âncoras (§5.3) ──── reprova: sem_ancora
  ├─ [2] refutação? → alvo + trecho literal + âncora nova (§6.1) ── tipo
  ├─ [3] PUBLICIDADE: oabgate, SÓ se assinada (§3.1) ──── reprova
  │
  └─ [4] JUÍZO (LLM) — só se [0..3] passaram, e só ordena
           └ monotônico: só ACRESCENTA motivo de ordem, nunca remove motivo de FATO
```

**Monotonicidade é a trava, e vale nos dois sentidos:** o modelo não pode absolver
o que FATO reprovou (é o que impede injeção de prompt de virar aprovação, §8.2) e
não pode reprovar por conta própria (é o que impede censura de divergência).

---

## 7. TRIAGEM DETERMINÍSTICA E CUSTO

### 7.1 O orçamento real, medido hoje

`data/ai/fila.sqlite` agora: **34.118 `extrair_dispositivos` pendentes**, 3
executando. A 79,3 s/tarefa (triagem.go:12) = **31,3 dias de máquina cheia**.
Moderar cada publicação com LLM disputa exatamente essa fila.

Custo de uma peça gerada, dos três registros reais: `prompt_tokens` 1.734/1.746/1.864
(média **1.781**), `eval_tokens` 360/461/418 (média **413**), `eval_tok_s`
4,866/5,281/4,804 (média **4,98**). Com prefill de 15–19 tok/s (§12): geração ≈
**177–202 s/peça**.

Um **julgamento** é muito mais barato, porque a saída é enum + justificativa curta:
prompt ≈ 700–900 tokens (a peça de 250–450 palavras + esquema) → prefill 37–60 s;
saída ≈ 80 tokens → 16 s. **≈ 53–76 s por julgamento** — *estimativa*, com a parte
de saída não medida (nunca se gerou um julgamento). O primeiro passo da
implementação é medi-la, não presumi-la.

### 7.2 O padrão de triagem já existe e tem perda validada em zero

`internal/cerebro/triagem.go:8-36` é o precedente exato: três baldes
(`BaldeSemSinal`, `BaldeSoSumula`, `BaldeModelo`), **32,7% das tarefas sem modelo
nenhum**, com perda validada — *"ZERO item legítimo se perde"*.

A tradução para moderação:

| balde | condição | modelo? |
|---|---|---|
| `reprovada_por_fato` | qualquer motivo de FATO/PUBLICIDADE/ABUSO | **não** |
| `sem_ancora` | abaixo do piso (§5.3) | **não** |
| `eco` | refutação sem âncora nova (§6.1.3) | **não** |
| `aprovada_trivial` | âncoras ≥ p50 (=2) **e** similaridade < 0,35 | **não** |
| `zona_cinzenta` | o que resta | **sim** |

A **zona cinzenta é definida por medição, não por intuição**: as fronteiras (p50=2;
0,35 como metade de `LimiarDeSimilaridade = 0.70`, gate.go:139) se calibram na
primeira leva contra veredito pré-registrado, e o número que entra no código é o
medido. Enquanto não houver leva, a zona é **tudo o que passou FATO** — errar para
o lado de julgar mais, nunca de aprovar sem olhar.

### 7.3 Anti-looping: identidade da fila, e não `revisao_vN`

**Correção de fato:** procurei `revisao_v` em `internal/ cmd/ tools/` e **o símbolo
não existe** neste repositório (só `previsao_v1`, que é outra coisa). Não vou citar
como existente algo que não medi.

O que existe é melhor: `internal/cerebro/fila.go` fixa
**`UNIQUE(tipo, chave, impressao, modelo)`**, e o comentário acima dele explica a
semântica — *"a MESMA página com texto novo vira tarefa nova e com texto igual vira
INSERT ignorado: é assim que a fila é idempotente sem consultar o resultado"*, e
`modelo` entra na identidade desde a v2 porque sem ele o segundo modelo nunca
executava.

Tarefa nova:

```
tipo      = "julgar_peca"
chave     = id da peça
modelo    = o modelo julgador
impressao = sha256(corpo ‖ chaves de citação ordenadas ‖ VersaoDoGate)
```

`VersaoDoGate` dentro da impressão é o que faz a mudança de régua rejulgar tudo, e
só ela. Peça que não mudou, sob régua que não mudou, **não volta à fila** — por
construção do índice único, sem consultar resultado. `INSERT OR IGNORE` é o
anti-looping.

E a guarda de saúde já existe: `internal/cerebro/saude.go:85-98` fixa
`TetoBytesResidentesPadrao` em 9 GiB e saude.go:162-164 **pesa bytes residentes**,
não conta modelos — o par do incidente de 2026-09-08 12:04:53 (14b+9b = 16 GB)
continua barrado. O julgador usa modelo pequeno e entra sob a mesma guarda, sem
knob novo.

---

## 8. ABUSO

### 8.1 Identidade antes do primeiro post (lição comprada por terceiro)

A Moltbook mediu o preço: **2.895.874 agentes registrados, 206.839 verificados
(92,9% sem verificação)**, 1,5 M tokens vazados, injeção em 2,6% dos posts. O
caminho certo é identidade criptográfica **antes** do primeiro post, não depois do
primeiro incidente.

Hoje **não existe caminho de escrita para agente**: `cmd/social/agentes.go:26-34`
registra que `/api/v1/redesocial/*` é a superfície de escrita e **só responde a
POST com CSRF**, e `perfis`/`contas` valem 1. Portanto não desenho o caminho de
escrita (é outra frente) — **declaro o contrato que a moderação exige** dele:

- identidade verificável por assinatura (Web Bot Auth,
  `draft-ietf-webbotauth-httpsig-protocol-00`), não por User-Agent — o dossiê mediu
  que UA é forjável e que a identidade só se verifica na borda;
- `alvo_id` + `trecho_refutado` quando for refutação;
- citações passando por `/api/v1/citacoes`;
- **sem campo livre que chegue a um prompt** (§8.2).

### 8.2 Injeção de prompt — o vetor é agente→agente

Procurei defesa existente (`grep` por `injecao|injection|ignore previous|desconsidere`
em `internal/ cmd/`): **nada relevante. A defesa não existe e precisa nascer.**

Um agente publica texto que instrui o agente **leitor** — ou o **moderador**. Três
camadas, e a mais importante é a primeira:

1. **Estrutural (a que realmente protege).** O conteúdo julgado **nunca** entra no
   prompt como instrução: entra como dado delimitado, e a saída do modelo é
   **enum fechado** validado determinísticamente. A monotonicidade do §6.3 fecha o
   ganho: mesmo que a injeção convença o julgador a dizer "aprovado", **isso não
   remove motivo de FATO** — o texto injetado não tem caminho para virar aprovação.
   Injeção que não pode alterar o resultado não é vulnerabilidade, é ruído.
2. **Léxico** (`injecao_de_prompt`): imperativo dirigido a modelo
   ("ignore as instruções anteriores", "desconsidere", "you are now",
   "system:", "</instruction>"). **Sinal para ordem + quarentena, nunca remoção
   silenciosa** — e nasce com FP test sobre as 11.106 páginas: um texto jurídico
   legítimo pode dizer "desconsidere-se a prova", e se o léxico acusar página
   publicada ele encolhe antes de entrar.
3. **Publicação**: a gêmea Markdown de conteúdo de agente sai com delimitador
   explícito de conteúdo não confiável, para que o próximo agente leitor saiba o
   que é dado de terceiro e o que é documento do portal.

### 8.3 Spam e rede coordenada

`CategoriaContaInautentica` (filas.go:26, 117-122) já existe e já nomeia a tese 3
do STF (presunção relativa para rede artificial de bots). Sinais determinísticos,
sem modelo: taxa por identidade; `similaridadeJaccard5Gramas` (gate.go:429-446) já
disponível para quase-duplicata entre peças do **mesmo** autor; `alvo_id` repetido.

**Teto por identidade, nunca por conteúdo:** rebaixa e enfileira; nunca apaga por
volume. Volume alto de peças ancoradas é o produto funcionando, não abuso.

---

## 9. RECURSO SEM DONO — e a fraqueza declarada

`internal/moderacao/schema.sql:231-247` já tem `recursos`, com
**`CHECK (revisor_id IS NULL OR revisor_id <> revisor_original_id)`**: quem julga o
recurso não pode ser quem decidiu. O mecanismo existe; reuso.

**Mas não vou finjir independência que não tenho.** Duas instâncias de
`qwen3.5:4b` não são dois julgadores independentes, e o L-MAD mede o preço de
debate com modelo fraco: **−7,35 pontos** com Llama3.1-8B, contra +7,6/+7,8 com
modelo médio. Então:

- **recurso de FATO** → re-execução determinística com a evidência nova (evidência
  nova = `impressao` nova = tarefa nova, §7.3). **Disponível de imediato**, e é a
  maior parte dos recursos, porque FATO é o único registro que reprova.
- **recurso de JUÍZO** → exige **segundo modelo genuinamente distinto**. Enquanto
  houver um só modelo útil na CPU, o recurso de juízo fica **declarado como não
  disponível**, em vez de simulado por uma segunda passada do mesmo peso. Com a
  RTX 5060 Ti (prefill 74–130×, k medido 0,648/0,660 na própria placa) o segundo
  julgador passa a caber, e o portão é **essa medição**, não calendário.

Nenhum estado é "aguardando o dono". Prazo de recurso sai de
`moderacao.PrazoDeRecurso` (filas.go:201-216), que já falha fechado quando a
política não declara.

---

## 10. TRANSPARÊNCIA

O produtor é `internal/moderacaotransparencia`, e li o ledger real
(`data/ops/moderacao_transparencia_diaria.jsonl`, 12 linhas, schema
`moderacao_transparencia_diaria_v1`). Ele já resolve o que é difícil:

- `piso_de_agregacao: 5` — contagem de 1 a 4 sai como **faixa**, e quando suprimir
  uma célula seria desfeito por subtração, **uma segunda célula ou o total também
  é suprimido**;
- `taxa_falso_positivo` com `indefinida: true` quando não há substrato;
- a ressalva honesta já gravada: *"Zero aqui é ausência de substrato, nunca
  ausência de denúncia"*;
- `PorCodigo []CodigoDoFiltro` com `NoLexico bool`
  (transparencia.go:104-117), agregado por `contaPorCodigo` (montagem.go:39-66).

**Integração:** os códigos de juízo e de abuso se **registram** em `PorCodigo` com
`NoLexico` distinguindo léxico de derivado — se não se registrarem lá, não aparecem
na prestação de contas, que é o defeito clássico de instrumento pela metade. Toda
decisão grava motivo + evidência; a evidência de FATO é a chave da citação (não o
texto do autor), pelo mesmo desenho de `itemDaFilaEmJSON`
(cmd/social/moderacao.go:136-153), que carrega `conteudo_ref` e **não** o texto
denunciado, para não republicar o que já saiu do ar.

**Duas ressalvas de desenho, para não copiar régua sem pensar.** (a) O
`piso_de_agregacao: 5` e a supressão por faixa existem para impedir
reidentificação de **quem denunciou** — contagem de decisões sobre peça **de
agente** não tem titular a proteger, então herdar a supressão ali só esconderia o
próprio desempenho. A série de juízo publica número exato; a de denúncia mantém a
faixa. (b) A **contagem de avisos por peça** (as URNs resolvidas fora do payload,
§5.1) entra como célula própria: é ela que torna visível a única perda conhecida
desta arquitetura.

A trilha é à prova de reescrita: `trilha_moderacao`
(schema.sql:295-306) tem `encadeamento TEXT NOT NULL UNIQUE CHECK (length = 64)` —
cadeia de hash. E `tamanhoMinimoDoFundamento = 20` (cmd/social/moderacao.go:100-110)
já recusa decisão sem motivação escrita: *"decisão de moderação sem fundamento é o
que o recurso não tem como atacar"*. Vale igual para o cérebro: **decisão do
moderador sem fundamento não grava.**

---

## 11. PASSOS DE IMPLEMENTAÇÃO (na ordem, com o artefato de cada um)

Ordem obrigatória: **oráculo → régua determinística → medição → modelo**. Nada de
LLM antes do passo 6.

| # | passo | artefato |
|---|---|---|
| 1 | Teste de regressão com as **3 peças reais** e vereditos pré-registrados (1 reprova, 2 **aprova**, 3 **reprova**) | `internal/pecagate/oraculo_real_test.go` + fixtures de `comentarios_gerados.jsonl` — **vermelho ao nascer** |
| 2 | Extrair o gate puro de `internal/cerebro/gate.go` para `internal/pecagate` (só `content` + `oabgate`; hoje o pacote arrasta `ollama`, `sqlitepool`, `semantica`, `lexml` — medido) para que `cmd/social` e `cmd/cerebro` usem a MESMA régua | `internal/pecagate/` + `cerebro` reexportando; zero mudança de comportamento |
| 3 | `PisoDeAncorasEspecificas = 1` + `AncorasEspecificas()` + motivo `sem_ancora`; peça 3 reprova | passo 1 fica verde na peça 3 |
| 4 | `fonte_fora_do_payload`: resolvida → **aviso**; acrescentar exigência de vocabulário oficial de fonte; peça 2 aprova | passo 1 verde nas três |
| 5 | Verificador determinístico de precedente/súmula no corpus (`numero_processo` + `jurisprudencia_citada`, 52 `registros-*.jsonl`), gravando `id_fonte`; **teste registra 0/60.221 para REsp 1.794.991** como limite conhecido | `internal/pecagate/precedente_no_corpus.go` + índice em `data/ai/precedentes_do_corpus.jsonl` |
| 6 | **Medir** o custo real de um julgamento (o número de §7.1 é estimativa): 20 julgamentos, `prompt_tokens`/`eval_tokens` gravados | `data/ai/medicao_julgamento.jsonl` + a constante de zona cinzenta derivada dali |
| 7 | `tipo=julgar_peca` na fila, `impressao = sha256(corpo ‖ chaves ‖ VersaoDoGate)`, enum fechado + validador; **monotônico** | migração de fila (identidade já suporta) + `internal/pecagate/juizo.go` |
| 8 | Refutação: `alvo_id`, `trecho_refutado` com âncora literal, âncora nova obrigatória | `internal/pecagate/refutacao.go` + teste com alvo real do acervo |
| 9 | `promessaComplementarRe` **por sujeito (1ª pessoa), não por ausência de negação** — medido: o naive acusa 23 ocorrências em 11.357 páginas; FP=0 → motivo, FP>0 → aviso; supersede gate.go:20-21 com data | teste de acervo real com os 23 casos como fixture negativa |
| 10 | Léxico `injecao_de_prompt` + FP test sobre o acervo; delimitador de conteúdo não confiável na gêmea | `internal/pecagate/abuso.go` |
| 11 | Registrar códigos de juízo/abuso em `PorCodigo`; série diária passa a medi-los | `moderacao_transparencia_diaria_v1` com os códigos novos |
| 12 | Gate de fluxo: reprova se peça publicada sem âncora, se decisão sem fundamento, se enum fora do vocabulário | `tools/check-moderacao-de-juizo` (read-only) |

**Travas de execução a respeitar, medidas:** campo novo em
`content/social_policy.json` exige **binário primeiro** —
`internal/socialpolicy/policy.go` usa `DisallowUnknownFields`, `cmd/social` faz
`log.Fatalf` e a unit tem `Restart=always`: JSON antes do binário = laço de boot.
Ordem: binário no disco → JSON → swap → restart.

---

## 12. MÉTRICAS (como se mede que funcionou)

1. **Oráculo invertido**: 3 de 3 peças reais com o veredito pré-registrado (hoje: 1 de 3). Camada: teste.
2. **FP do léxico de promessa**: 0 de 11.106 páginas publicadas acusadas. Camada: acervo.
3. **FP/FN do gate**, o número que nunca existiu: amostra de N peças com veredito pré-registrado **antes** de rodar. Camada: disco.
4. **Fração sem modelo**: alvo ≥ 32,7% (o que a triagem de extração já entrega). Camada: fila.
5. **Custo por julgamento**: medido em `medicao_julgamento.jsonl`, comparado aos 79,3 s de `extrair_dispositivos`. Camada: Ollama.
6. **Rejulgamento**: 0 tarefas `julgar_peca` com `impressao` repetida. Camada: `fila.sqlite`.
7. **Ancoragem do que se publica**: 100% das peças publicadas com ≥ 1 âncora específica; mediana ≥ p50 (=2) do acervo. Camada: disco.
8. **Refutação real**: % com `trecho_refutado` literal e âncora nova. Camada: disco.
9. **Zero decisão sem fundamento** e trilha encadeada sem furo. Camada: `social.db`.
10. **csp-report = 0** e **404 de AI Crawler verificado = 0** nas rotas novas (o dossiê mediu 243/dia e 870). Camada: borda.

---

## 13. RISCOS — onde este desenho pode falhar

1. **O piso pode ser gamed por âncora decorativa.** Citar `art. 5º da CF` em
   qualquer texto satisfaz o piso sem melhorar nada. Mitigação parcial:
   `NormaAtestadaNoTexto` e relevância como sinal de ordem. **Mas o piso mede
   presença, não pertinência, e pertinência é juízo — que por desenho não reprova.**
   É a fraqueza mais séria, e é consciente: prefiro exigir âncora gameável a premiar
   a ausência de âncora, porque a primeira é detectável na leitura da amostra e a
   segunda não deixa rastro.
2. **p25 = 1 é piso frouxo, e a escolha dele NÃO foi pré-registrada.** 2.223 páginas
   do acervo têm exatamente 1 âncora, e o p50 é 2. Escolhi o percentil conservador
   para não reprovar o que o próprio acervo publica — **mas escolhi depois de ter
   lido as três peças, sabendo que p25=1 separa a peça 2 da 3 e que p50=2
   reprovaria as duas.** Isso é seleção de régua depois do número, que é
   exatamente o que "régua do veredito antes do número" existe para impedir.
   Registro a limitação em vez de apresentar a inversão como validação: **o
   oráculo das três peças é demonstração de mecanismo, não evidência de
   calibração.** O teste genuinamente pré-registrado é o do passo 6 — veredito
   escrito antes de rodar, sobre leva que eu não vi. Se lá o piso 1 deixar passar
   vagueza, o número certo é 2, e a troca vem com a medição junto.
3. **A verificação de precedente tem cobertura parcial e eu medi o buraco**: janela
   2022-05→2026-08, 3ª e 4ª Turma, 97,4% do corpus. Precedente criminal, tributário
   ou anterior a 2022 cai em `nao_verificavel` — aceito, não contado. Se o piso
   passar a exigir 2, áreas mal cobertas (previdenciário 12,7%, criminal 22,1%)
   ficam estruturalmente reprovadas. **O piso interage com a lacuna do corpus, e
   subir o piso sem ampliar o corpus censura por área.**
4. **Recurso de juízo não existe até haver segundo modelo.** Declarado, não
   simulado. Enquanto durar, juízo errado se corrige por mudança de régua
   (`VersaoDoGate` rejulga tudo), que é grosso.
5. **O julgador é auditado por léxico, e léxico tem ponto cego** — é a mesma classe
   de defeito que `hasNearbyNegation`. Não tenho mitigação forte; tenho o registro
   da decisão e a série, que permitem descobrir depois.
6. **Extrair o gate (passo 2) toca código que funciona em produção.** É refatoração
   sem mudança de comportamento, protegida pelo passo 1, mas o contrato proíbe
   mexer no que funciona: se a extração não for necessária (se `cmd/social` puder
   importar `internal/cerebro` sem arrastar Ollama), **não se faz**. A medição dos
   imports diz que arrasta; conferir no `go list -deps` antes de mover.
7. **Custo de julgamento é estimativa** (53–76 s), com a parte de saída não medida.
   Se o julgamento custar como uma extração (79,3 s), moderar 11.039 temas é 10
   dias de máquina cheia contra 31,3 dias de fila já pendente. O passo 6 existe
   para essa medição vir antes da decisão, e o balde `aprovada_trivial` existe para
   que o número não precise ser bom.
8. **Não medi** a taxa real de injeção no nosso tráfego (a Moltbook mediu 2,6% no
   dela). O léxico nasce sem base própria, e o primeiro número honesto vem da
   primeira leva.
9. **Fala humana fica sem decisor.** É deliberado e está fora do ângulo, mas é uma
   lacuna real do desenho: se humanos começarem a postar antes de o decisor existir,
   a fila de cuidado ativo volta a pedir revisão humana — que está proibida.
   Precisa de frente própria, e precisa antes do primeiro perfil humano.

---

## 14. O QUE O ADVISOR MUDOU

Chamei o advisor após a orientação e antes de escrever. Ele mudou o desenho em
pontos concretos:

- **JUÍZO decide ordem, nunca existência** — explicitar isso como propriedade
  estrutural (e não como promessa) veio dele, e é o que dá lastro ao §4.3.
- **Monotonicidade como defesa de injeção**, não só como higiene: o argumento de
  que injeção incapaz de alterar o resultado deixa de ser vulnerabilidade é dele.
- **Piso por granularidade, não por contagem de itens**: eu ia contar citações, o
  que faria a peça 3 passar com 4. Contar chaves específicas é o que inverte o
  veredito.
- **PUBLICIDADE só sob a assinatura do advogado** (§3.1) — eu ia rodar `oabgate`
  em post de terceiro, que seria justamente travar informação por risco de OAB.
- **Âncora literal de `extracao.go` como alvo de refutação** (§6.1): reuso em vez
  de inventar medida de "endereça a alegação".
- **Seguir o precedente de `captacaoComplementarRe`** em vez de tocar `oabgate`; e
  tratar gate.go:20-21 como linha a superar com data.
- **Não presumir FP = 0 no léxico estrito de promessa** — foi o empurrão que me fez
  medir, e a medição **derrubou a minha própria versão do §5.4**: o léxico sem
  janela de negação acusaria **23 ocorrências em 11.357 páginas publicadas**, e as
  amostras mostraram que o discriminante real é *quem promete* (discurso reportado
  vs. voz própria), não a negação. A régua FP=0→motivo / FP>0→aviso ficou escrita
  **antes** do número da implementação.
- **Conferir a granularidade do resolvedor antes de depender dela** (§5.3): uma
  chamada a `/api/v1/citacoes` provou que `art. 14 do CDC` devolve
  `…8078!art14` com `tipo=artigo`, e revelou que a mesma lei gera **dois** itens —
  o piso conta chave distinta, não item, e a chave de súmula é `STJ:sumula:7`.
- **Fechar o vazamento do `Sinal` para texto de agente** (§3.2) e **nomear os três
  testes que ficam vermelhos** no passo 4 (§5.1), em vez de descobri-los no meio da
  implementação.
- **Assumir que o piso não foi pré-registrado** (risco 2): escolhi p25=1 depois de
  ver as três peças, e isso está dito, não maquiado.
- **Não construir o caminho de escrita**, só declarar seu contrato (§8.1).
- **Declarar a fraqueza da independência do recurso** com o número do L-MAD (§9).

**Onde a medição primária contrariou o advisor, e eu segui a medição:** ele propôs
ampliar o mundo fechado para o corpus, aceitando precedente cujo número exista nos
espelhos do STJ, e ampliar `DispositivosPermitidos` para as URNs do grafo. Medi as
duas e **as duas falham no caso real**: REsp 1.794.991 = **0 de 60.221** (corpus
começa em 2022-05) e Lei 11.771/2008 **ausente** do universo de 3.761 URNs. Se eu
tivesse seguido, o gate continuaria reprovando a peça 2 e passaria a rejeitar
precedente real por ser antigo. Adotei a **terceira via** do §5.2: chave não
provável não reprova sozinha, não conta como âncora, e é gravada como
`nao_verificavel` — o limite da verificação fica declarado no dado em vez de
escondido no veredito. Também não usei `revisao_vN`, citado no enunciado da frente:
**grep em `internal/ cmd/ tools/` mostra que o símbolo não existe** neste
repositório; a versão vive na `impressao` da fila, que existe.
