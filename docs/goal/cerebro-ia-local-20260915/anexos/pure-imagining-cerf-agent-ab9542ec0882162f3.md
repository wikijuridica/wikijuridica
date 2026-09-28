# O cérebro julga o que é juízo — gate estatístico vira testemunha

Arquitetura pelo ângulo: **o detector estatístico deixa de ser JUIZ e vira TESTEMUNHA;
quem decide é a IA local, com evidência gravada.**

Tudo abaixo foi lido no disco nesta sessão. Números meus estão marcados MEDIDO;
o que não medi está marcado NÃO MEDIDO com o motivo.

---

## 0. Medições próprias desta sessão (sessão somente-leitura)

| o quê | número | fonte |
|---|---|---|
| fila do cérebro | `extrair_dispositivos` 34.781 pendentes + 3 executando + 7.707 concluídas + 39 erro; `embed_pagina` 11.248 concluídas | `sqlite3 -readonly data/ai/fila.sqlite` |
| custo por tarefa, 2026-09-15 | 462 lotes, 1.386 tarefas, **48,5 s/tarefa**, 647,9 prompt tok/tarefa, 108,3 eval tok/tarefa | `data/ops/ia_local_daily.jsonl` |
| mediana s/tarefa por dia | 09-10 48,9 · 09-11 44,8 · 09-12 60,8 · 09-13 62,2 · 09-14 62,7 · 09-15 38,8 (p90 84,9–106,2) | idem |
| drenagem | 1.218,75 tarefas/dia (média dos 4 últimos dias) ⇒ **28,5 dias** para as 34.784 | idem |

---

## 1. A tese em uma frase

**Enquadramento honesto, antes de tudo:** este canal **não está na onda diária** —
`tools/run-daily-content:368-373` lista cinco geradores e nenhum deles é
`generate-acordao-pages`; o shard `stj-acordao-derivado-01.jsonl` não existe e o
gerador tem um commit só. **Impacto em produção hoje: zero.** Nada aqui é
emergência de produção; é a arquitetura com que o canal nasce ligado, e o primeiro
entregável não custa um token de LLM.


Hoje `cmd/generate-acordao-pages/main.go:293-297` mata a página e o motivo vira
um `map[string]int` impresso em stdout (`relata`, :2268-2312). O detector é juiz,
carrasco e escrivão — e não deixa rastro. A arquitetura troca isso por três
camadas, **nesta ordem, e a ordem é o desenho**:

```
T0  FATO          determinístico, nunca julgado, só pode ficar mais estrito
T1  TESTEMUNHA    mede, grava score + os TRECHOS SOBREPOSTOS, nunca mata
T1,5 MÁSCARA      classifica o trecho sobreposto SEM LLM (fonte / andaime / residual)
T2  JUÍZO         só o residual, só na banda cinzenta, assíncrono, pela fila
```

T1,5 é o passo que o ângulo exige e que quase se esquece: **parser antes de LLM**
(`internal/cerebro/triagem.go:8-36` — a triagem determinística já poupou 32,7%
da fila de extração). Se a máscara sozinha separar os controles, **o LLM não é
adotado**. Isso está em `provas`, não em `riscos`.

---

## 2. Por que a máscara vem antes, com o código que a sustenta

Uma página de acórdão tem três camadas e o detector atual soma as três:

| camada | onde está no código | unicidade importa? |
|---|---|---|
| 1 · texto oficial citado | isolada por `reAspas` em `corpoAutoral`, main.go:2176-2178 | **não** — DEC-032 manda citar |
| 3 · andaime do template | seis headings main.go:1595,1604,1611,1617,1623,1629 + molduras de FAQ main.go:1990-2046 | **não** — o gerador as emite iguais |
| 2 · prosa autoral | o resíduo | **sim** — é a única que importa |

`corpoDaPagina` (main.go:2153-2168) concatena **Opening + Heading + Text + FAQ** —
camadas 1+2+3 — e é ele que entra em `shinglesNeutralizados` (:2187-2196) e no
corte de :294. Li as molduras do FAQ em :1990-2046: são literais fixos com
encaixe variável (`sigla`, `numero`, `orgao`, `julgamento`, `materia`, `IDFonte`).
Depois de `reDigito.ReplaceAllString(limpo, "N")` (:2189) os encaixes numéricos
colapsam e a moldura fica byte-idêntica entre quaisquer duas páginas do canal.
A última resposta do FAQ (:2043-2048) são ~60 palavras quase constantes.

Precedente vivo para mascarar antes de hashear: `cmd/generate-diario-pages/main.go:1400`
já mede sobre `semTrechoCitado(...)`, e `tools/generate-page-content-revision`
neutraliza blocos estruturais antes de hashear. A máscara não é invenção minha.

**Como a máscara não mente sobre o que filtra** (precedente próprio: "guarda
esconde o que filtra"): a lista de literais do andaime é **derivada das mesmas
constantes** que `perguntas()` e `montaPagina()` emitem, com um teste que falha
se uma moldura nova aparecer em `perguntas()` e não na máscara. Lista copiada
envelhece sozinha; lista derivada, não.

---

## 3. T1 — a passada-testemunha (zero LLM, e é o primeiro entregável)

**Onde ela mora: dentro do gerador**, `cmd/generate-acordao-pages`, flag
`-seco -testemunha <arquivo>`. Só ele tem `montaPagina` e o corpo do candidato;
candidato recusado nunca vira linha de shard, então nenhum instrumento que leia
`data/editorial/v2_pages/` o alcança. `cmd/measure-molde-trigrama` **não** é o
instrumento desta passada: ele lê shards e é o medidor contínuo do acervo (§9).

Ele já tem o conceito de banda — `bandaInicial = *limiar - 0.10`
(cmd/measure-molde-trigrama/main.go:117), contada em `naBanda` (:170) — mas o
**0,10 é número redondo escolhido à mão** e por isso **não o adoto**; as bordas
saem da curva da §5.

Uma linha JSONL por candidato iterado, com quatro scores contra o vizinho mais próximo:

| score | régua | por que existe |
|---|---|---|
| `s_hoje` | 3-grama neutralizado sobre `corpoDaPagina` | a régua que hoje mata (main.go:294) |
| `s_gate` | 5-grama, dígito preservado. Corpo montado por `v2bodyneardup.AssembleBody` (neardup.go:153-175 — `opening + sections[].text + faq`, headings **excluídos de propósito**, comentário :154-156) e shingles por `shingleHashes` (:177-190), que tokeniza com `legalsignature.Tokenize(legalsignature.NormalizeText(body))` — dígito preservado | a régua do único gate desta família que roda (`tools/run-qualidade-diaria:679`) |
| `s_autoral` | 3-grama neutralizado sobre `corpoAutoral` (main.go:2176) | camada 1 fora |
| `s_residual` | 3-grama neutralizado sobre `corpoAutoral` menos o andaime | camadas 1 e 3 fora — **o número que decide** |

E, o que hoje não existe em lugar nenhum: **os trechos sobrepostos**, reconstruídos
como corridas contíguas de shingles compartilhados, cada um já classificado pela
máscara:

- `linguagem_forense_da_fonte` — a corrida ocorre **literalmente nas duas ementas
  de origem**. Verificável em Go, é a mesma âncora do pós-filtro de extração
  (`Extracao.Descartados`, `internal/cerebro/extracao.go:68-71`).
- `andaime_do_template` — a corrida é substring de um literal conhecido.
- `residual` — nem uma coisa nem outra. **Só isto vai ao juízo.**

Custo: zero LLM, uma passada `-seco`. Hoje o gerador não grava nada disso: os
21 pontos terminais produzem zero linha em disco.

---

## 4. Onde o cérebro entra no trajeto

**Assíncrono, pela fila, nunca dentro do gerador.** O gerador roda na onda diária;
uma chamada síncrona de ~50 s por página faria uma passada de 500 durar ~7 h e
acoplaria a fábrica ao Ollama — que `internal/cerebro/saude.go:98` pausa sozinho
quando o host aperta.

```
generate-acordao-pages -seco -testemunha  →  testemunho.jsonl  (zero LLM)
                                                    │
                        cmd/cerebro enfileirar --juizo-de-molde   (lê o testemunho)
                                                    │
                          fila.sqlite  tipo=julgar_molde  prioridade acima do backlog
                                                    │
                        Worker (worker.go:60) → Executor (worker.go:24)
                                                    │
                            data/ai/juizos_de_molde.jsonl  (append-only)
                                                    │
      ┌─────────────────────────────────────────────┼──────────────────────────┐
 generate-v2-publication-severity            publish-v2-direct         check-juizo-de-molde
 (rótulo MÉDIO + v2_rewrite_queue)        (skipped_statistical_gates    (gate de sinal, §7)
                                            real, por página)
```

Quem enfileira: o **mesmo enfileirador que já existe**, `cmd/cerebro/main.go:778`,
que hoje enfileira extração lendo o corpus e pulando por cache (:758-763). O
gerador **nunca toca `fila.sqlite`** — um caminho de escrita, um escritor, que é
a regra escrita em cmd/cerebro/main.go:749-754.

Onde grava: `data/ai/juizos_de_molde.jsonl`, ao lado de
`ArquivoExtracoes = data/ai/extracoes_dispositivos.jsonl` (extracao.go:30).
Isto não é gosto: a unit do cérebro tem `ReadWritePaths=/opt/wiki/data/ai
/opt/wiki/data/ops` (cabeçalho de `internal/cerebro/publicacao.go`), então
`data/ai/` é o único lugar onde o daemon escreve sem mexer na unit.

---

## 5. As três bandas, e de que medição saem os limites

```
s_residual        0 ─────────── borda_inferior ══════ borda_superior ─────────── 1
                    publica, sem      BANDA CINZENTA        acima: retido até o
                    tarefa            publica MÉDIO +       juízo, com prioridade
                    (custo zero)      juízo assíncrono      (SLA na §6)
```

**Duas perguntas diferentes, duas fontes diferentes — e confundi-las é o erro que
quase cometi.** Onde ficam as bordas (roteamento) e se o juiz tem sinal
(adoção) não se respondem com a mesma amostra.

### 5a. Adoção — os controles, particionados pela MÁSCARA e nunca pelo incumbente

Rotular como "molde" o par que a régua incumbente acusou seria **assumir que o
detector sob teste é a verdade** — e a tese aqui é justamente que ele dispara sobre
as camadas 1+3. Os controles saem, portanto, do passo **determinístico e
verificável**, nunca do score:

Toma-se o conjunto de pares com `s_hoje` alto (os que a régua de hoje mataria) e
**particiona-se pela máscara da §3**:

| controle | partição | rótulo exigido | por que o rótulo é defensável |
|---|---|---|---|
| **negativo** (juiz não pode reprovar) | `s_hoje` alto **e** corridas `residual` vazias ou ínfimas | `distinta` | toda a sobreposição está atestada nas duas ementas ou é substring de literal do template. É **falso positivo do incumbente por construção** — o caso exato da queixa do dono |
| **positivo** (juiz tem de reprovar) | `s_hoje` alto **e** corridas `residual` presentes | `molde_autoral` | a corrida não ocorre em nenhuma das duas ementas e não é substring de nenhum literal do template. Só sobra prosa nossa repetida |
| **positivo por construção** | fixture | `molde_autoral` | página A com a camada autoral de B e a camada citada de A. Fica em `testdata/`, como `internal/cerebro/testdata/` — **nunca escrita em shard** |

A circularidade que resta é só em relação à **máscara** — substring e âncora
literal, as duas conferíveis em Go — nunca em relação ao LLM. É a mesma disciplina
do pós-filtro de extração, que aceita item só quando o trecho ocorre no texto.

**Dois rótulos que eu tinha escrito e retiro:**
- Os "32 pares ≥0,70 em 43 páginas" do cabeçalho de `cmd/measure-molde-trigrama/main.go:15-16`
  **não são dívida medida citável**: aquela passada não está no ledger
  (`data/ops/molde_trigrama.jsonl` só tem as duas linhas do shard de Tema) e o
  número não se reproduz. Vira **prova a regenerar** (§ provas), não insumo.
- "Já publicada sob a assinatura do dono" **não prova unicidade**: o censo publica
  tudo que é MÉDIO, e 5.600 páginas vivas carregam `batch_global_similarity`. Par
  com `s_gate` baixo é teste trivial; o que discrimina é `s_hoje` alto com
  `s_residual` baixo.

### 5b. Roteamento — as bordas saem da curva do próprio juiz, sem oráculo

Não há pessoa nesta etapa. Rodam-se 10 decis de `s_residual` × 20 pares = 200
julgamentos e levanta-se **veredito-vs-score do próprio 4b**; +100 dentro do decil
onde ele deixa de ser constante (n=20 por decil só localiza a borda a ±1 decil).

`borda_inferior` = maior score em que ≥95% dos vereditos são `distinta`.
`borda_superior` = menor score em que ≥95% são `molde_autoral`.
**A banda é onde o juiz deixa de concordar consigo mesmo** — que é a definição
operacional de zona cinzenta, e é medição, não chute.

200/300 é **derivado do orçamento** (cabe numa janela noturna a ~48,5 s cada), não
constante do desenho. Isso mede *onde julgar*; se o juiz presta é a §5a que diz.

Se ainda se quiser rótulo externo sobre a banda, o oráculo é um **modelo mais
forte com justificativa escrita por par** (DEC-019, fiscalização cruzada entre
pares) — e não se chama isso de humano. O contrato proíbe devolver ao dono tarefa
que é da engenharia, e a memória registra que ele não revisa páginas.

**Resultado falsificável, pré-registrado (régua do veredito antes do número):** se
as duas bordas se cruzarem — isto é, se não houver separação monotônica — o score
**não tem poder preditivo** e a ação certa é **abandonar o score**, não julgar.

**Tamanho da banda: NÃO MEDIDO.** Sai da passada-testemunha. Se a máscara derrubar
`s_residual` abaixo da borda inferior para a maioria dos 532, a banda é quase vazia
e o custo de LLM é quase zero — que é o desfecho desejado e a razão de medir antes
de construir.

---

## 6. O juízo: prompt, formato, verificação e o veredito

Reuso direto do que a extração já provou:

- `SistemaDoJuizoDeMolde` — constante curta, espelhando `SistemaDaExtracao`
  (extracao.go:~215). Curta porque **prefill domina**: medido hoje 647,9 prompt tok
  contra 108,3 eval tok por tarefa, e o §12 manda cortar em tokens, não em inteligência.
- `EsquemaDoJuizo` `json.RawMessage` — impõe a FORMA na decodificação, como
  `EsquemaDaExtracao`. O repo já mediu que 444 dos 811 caracteres do prompt antigo
  eram descrição de formato.
- `VersaoDoPromptJuizo` — o pareado não existe sem ela (extracao.go:~205).

**A entrada NÃO são dois corpos.** São só as corridas `residual`, numeradas. Isso
(a) corta o prefill de ~2.000 tokens para ~200-400 palavras e (b) faz a pergunta certa.

**Saída por corrida**: rótulo do conjunto fechado de 3 + o excerto literal. E aqui
está a resposta à objeção do juiz permissivo, em código:

> **O rótulo mais permissivo é o único deterministicamente verificável.**
> `linguagem_forense_da_fonte` é conferido em Go contra as duas ementas de origem;
> não ocorrendo lá, o rótulo é **descartado e contado** —
> `descartados_fonte_nao_atestada`, a mesma disciplina de contador de
> `Extracao.DescartadosNormaNaoAtestada` (extracao.go:76-79) e de
> `DescartadosGeracaoAmbigua` (:106-110), que existem exatamente porque "guarda que
> remove zero não pode ser indistinguível de guarda que não roda".

Um juiz que diz "isso é da fonte" sobre a nossa prosa é pego **de graça**. Um juiz
que exagera para `prosa_autoral_repetida` só custa trabalho de reescrita — a página
publica de todo jeito. A assimetria é o desenho, não um efeito colateral.

Registro (`data/ai/juizos_de_molde.jsonl`), campo por campo:

```
schema_version · chave (intent_id) · par · rubrica · modelo · versao_do_prompt
corpo_sha256 · par_sha256 · s_hoje · s_gate · s_autoral · s_residual
trechos[{excerto, rotulo, atestado_nas_duas_ementas}]
descartados_fonte_nao_atestada · descartados_sem_ancora
veredito: distinta | molde_autoral | indeterminado
motivos[] · avisos[]        ← disciplina de gate.go:111-116: Motivos SEMPRE bloqueiam, Avisos NUNCA
prompt_tokens · eval_tokens · eval_tok_s · done_reason · gerado_em
```

### O retido tem dente, e o dente tem prazo

Acima da borda superior a página é **retida até o juízo**, com prioridade acima do
backlog (`Reivindicar` ordena por `prioridade DESC`, fila.go:~355; o esquema de
prioridade já existe — `cmd/cerebro/main.go` põe a amostra em 5 e o resto em −5).

Mas **a retenção é limitada em TEMPO, nunca em desfecho**: se o juízo não chegar
até a onda diária seguinte (`tools/run-daily-content`, cadência que já existe), a
página **publica como MÉDIO**. Nenhum score estatístico pode manter página fora do
ar — é o que preserva "nada trava" e é o que impede o gate estatístico de voltar
a ser veredito por uma porta lateral.

E a expiração **nunca é silenciosa**: `check-juizo-de-molde` reporta quantas
publicaram sem juízo na janela. O alarme é do daemon (`SaudeDoPortal`, saude.go:76,
`Verifica` :98, `restartsDoServico` :268), não um fallback mudo.

---

## 7. Anti-looping — cinco travas, e uma delas fecha um buraco que eu li no código

1. **Identidade da fila.** `UNIQUE(tipo, chave, impressao, modelo)` (fila.go:73-93);
   `Enfileirar` é `INSERT OR IGNORE` (:~312). `impressao =
   sha256(corpo_autoral_residual ‖ corpo do par ‖ rubrica)`. Mesma pergunta = tarefa ignorada.

2. **Skip por (chave, rubrica) no enfileiramento** — a trava que importa. Antes de
   enfileirar, ler o último registro de `juizos_de_molde.jsonl`, na forma exata de
   `UltimaExtracaoPorChaveEModelo` (extracao.go:884-903) e do skip de
   cmd/cerebro/main.go:758-763. **Deriva de texto não reabre o juízo; só o bump de
   rubrica reabre.** Sem isto, o gerador reescreve a página todo dia com pequena
   variação e a fila cresce para sempre.

3. **Cadeia `RubricaVigente`** — o padrão `revisao_vN` de extracao.go:128-215, que o
   próprio repo documenta em :175-181: *"o skip da revisão compara com a VIGENTE,
   então cada conjunto novo de regras precisa de um nome novo para reabrir o que as
   anteriores fecharam"*. Bump exige **re-passar a fixture congelada** (§8).

4. **Teto de contestação = 2.** Dois vereditos sob rubricas distintas que discordam
   ⇒ `juizo_contestado`, nunca mais enfileirado sozinho. **2 é estrutural, não
   orçamentário**: um veredito é um veredito, dois que se contradizem são uma
   contenda. A página segue publicada como MÉDIO enquanto isso.
   **`indeterminado` é veredito**, não ausência: a tarefa concluiu, a trava 2 não a
   reabre sob a mesma rubrica, e ela **conta para o teto**. Sem dizer isto, uma
   página acima da borda superior ficaria `juizo_pendente` com um veredito que não
   diz nada — e sairia pelo SLA sem ninguém perceber. Acima da borda superior,
   `indeterminado` publica MÉDIO com o rótulo `juizo_indeterminado:<rubrica>`.

6. **Sem troca de modelo, por construção.** O juízo usa o **mesmo `qwen3.5:4b`** da
   extração, e `Reivindicar` agrupa o lote por `(tipo, modelo)` (fila.go:~355/:~375).
   Logo o juízo não paga os 21-48 s de `load_duration` por alternância — o custo que
   `OLLAMA_MAX_LOADED_MODELS` e a guarda de bytes residentes (`saude.go:90`, teto de
   9 GiB) existem para conter.

5. **O buraco que li e que fecharia o loop pelo outro lado.**
   `intentsPublicados` (main.go:732-743) **pula deliberadamente o próprio shard**
   (`prefixoDoMeu`, :73/:741) — e com razão: lê-lo de volta faria o gerador esvaziar
   a si mesmo. Consequência: uma página retida no shard **não entra em `protegidos`
   (:279) e é remontada a cada passada**. A trava 2 impede a tarefa duplicada, mas
   não a remontagem. Correção de uma linha, com motivo nomeado:
   `protegidos = intentsPublicados(raiz) ∪ intentsComJuizoVigente(juizos_de_molde.jsonl)`.
   `shardpreserve.Completa` (:2240) já garante que a gravação nunca reduz o shard.

---

## 8. A tabela que não se cruza

| eixo | classe | quem decide | o cérebro pode |
|---|---|---|---|
| coerência de artefato (HTML+sitemap+manifesto+SHA-256) | FATO | `publishedmanifest.Validate`; os 9 de `cmd/publish-v2-direct/qualitygate.go:21-31` | **nada** |
| campo obrigatório ausente · corpo vazio · encoding | FATO | `tools/generate-v2-publication-severity:395-402`, `:747` | **nada** |
| rota duplicada · área não derivável · intent duplicado | FATO | `internal/v2publish/v2publish.go:401,415,427` | **nada** |
| promessa de resultado · preço · captação (Prov. 205/2021) | ÉTICA | `internal/oabgate.CheckResposta` | **só endurecer** |
| **atribuição** de citação legal (trecho ancorado, URN atestada) | FATO | pós-filtro de extracao.go; `NormaAtestadaNoTexto`; mundo fechado de gate.go | **só endurecer** |
| anti-fraude · métrica · habitualidade | FATO | contrato | **nada** |
| — linha — | | | |
| **molde/similaridade entre páginas** | JUÍZO | **cérebro**, na banda, sobre o resíduo | **afrouxar e endurecer** |
| **comprimento** da citação (`minimoCitacaoOficial=25`, `tetoCitado=0,42`, main.go:89-96) | JUÍZO | cérebro | mesmo mecanismo, não detalhado aqui |
| thin content na faixa 250–400 | JUÍZO | cérebro | idem |
| `terminaEmConectivo` (main.go:1420-1428, 42 palavras num conjunto plano, contra a regra contextual de v2ingest) | JUÍZO | cérebro | idem |
| `integralmenteEmCaixaAlta` / item transcritível (main.go:1145, :1216) | JUÍZO | cérebro | idem |

**A linha fina que importa:** a *atribuição* de uma citação nunca é julgada por
contexto — ela é âncora literal, FATO. Os *limiares de comprimento* da citação são
heurística e caem do lado do juízo. Confundir os dois é o que transforma
"citação legal mal atribuída é P1 permanente" em detector estatístico, que é a
troca que este desenho recusa.

**Regra de ouro:** o juízo **nunca cria recusa nova**. Ele só pode desfazer recusa
heurística ou mandar para `v2_rewrite_queue.jsonl`. Detector novo que reprove
nasce em T0, determinístico, com teste de falso positivo sobre amostra real.

---

## 9. Consumo — e o defeito que isto conserta de passagem

- `tools/generate-v2-publication-severity` ganha o mapeamento no bloco
  `# --- medios (publicam) ---`, que li em :750-769, ao lado de
  `batch_global_similarity_refutado_por_medicao` (:764-765) — o vizinho certo,
  porque é o precedente do mesmo eixo. E lê o JSONL **por campo desserializado,
  nunca `x in lista`**: os quatro `in queue_reasons`/`==` que li ali
  (`"missing_required_field"` :747, `"official_sources_insufficient"` :758,
  `page_antitemplate_status == "review_required"` :762, `"duplicate_phrase_with_page"`
  :768) são membership exata contra elementos **prefixados**, e é por isso que
  disparam zero. Mapeamento: `molde_autoral` → MÉDIO `molde_confirmado_por_juizo:<rubrica>`
  + linha em `v2_rewrite_queue.jsonl` (formato já existente: `intent_id`, `reasons[]`,
  `source_shard_sha256`); `distinta` → MÉDIO `molde_refutado_por_juizo:<rubrica>`;
  ausente acima da borda superior → `juizo_pendente`. **Nunca CRÍTICO.**

- `cmd/publish-v2-direct/main.go:3957` para de escrever duas strings chumbadas.
  O campo `SkippedStatisticalGates` (:3899) passa a levar, **por página**, o que o
  JSONL diz daquele intent. Isso conserta um defeito de anti-fraude que está no ar:
  hoje as **11.106 linhas do ensaio carregam o MESMO par de strings**, alegando uma
  refutação medida em 9.620 documentos em 2026-08-06 — que nunca leu 1.244 dessas
  páginas, entre elas as 1.134 `jur-` desta mesma família. Evidência escrita sem a
  medição correspondente é exatamente o que o contrato proíbe.

- `cmd/measure-molde-trigrama` entra em `tools/run-qualidade-diaria`, ao lado de
  `v2-body-near-duplicates` (:679), como **medidor contínuo e gratuito de falso
  negativo**: par ≥ limiar cujos dois intents carregam veredito `distinta` é um
  **erro nomeado do juiz**, gravado. Hoje o instrumento tem 1 commit e nenhum invocador.

---

## 10. Custo, com a conta aberta

| linha | número | classe |
|---|---|---|
| custo de uma extração hoje | 48,5 s/tarefa, 647,9 prompt tok (2026-09-15, 1.386 tarefas) | **MEDIDO** |
| backlog | 34.784 pendentes ÷ 1.218,75/dia = **28,5 dias** | **MEDIDO** |
| custo de um juízo | **≤ 48,5 s** — o prompt é MENOR que uma ementa de 3.000 chars (só as corridas residuais, ~200-400 palavras) | **ESTIMADO por paridade de prefill — NÃO MEDIDO** |
| como confirmar sem gastar o backlog | `TipoMedirModelo` com `modo: "gerar"` (tarefas.go:26,43-48) sobre 20 conjuntos reais — o tipo já existe e há 3 tarefas `medir_modelo` pendentes na fila | — |
| **julgar TODOS os 4.763 candidatos** | 4.763 × 48,5 s = 231.006 s = **64,2 h = 2,67 dias de Ollama exclusivo = 9,4% do backlog** | derivado — **é o número que obriga a banda** |
| 532 julgamentos de uma vez | 26.600 s = **7,4 h = 1,08% do backlog de 28,5 dias** | derivado dos dois acima |
| regime permanente | `-limite` default é 30/passada (main.go:185) × fração da banda | derivado |
| fração da banda | **NÃO MEDIDO** — sai da passada-testemunha | — |

O juízo entra por prioridade acima do backlog (fila.go `prioridade DESC`), então
paga-se 1% de atraso na extração, uma vez.

---

## 11. Onde este desenho pode deixar passar conteúdo ruim

1. **A máscara pode mascarar demais.** Se a lista de literais do andaime divergir do
   que `perguntas()` (main.go:1990-2046) emite, a máscara remove prosa real e esconde
   molde verdadeiro — o precedente "guarda esconde o que filtra". Mitigado por
   derivação + teste, não eliminado.
2. **O rótulo restritivo não é verificável.** `prosa_autoral_repetida` é palavra do
   modelo. Custa reescrita, nunca despublicação — mas um juiz sistematicamente
   restritivo enche a fila de reescrita com página boa, e só a fixture pega isso.
3. **Fixture congelada envelhece.** As bordas saem de 300 pares rotulados uma vez; o
   acervo anda. Mitigado pelo medidor contínuo da §9, não resolvido.
4. **Citação mal atribuída continua P1 permanente** e **nada aqui a detecta.** Este
   desenho não toca nisso e não deve dar impressão de tocar.
5. **A comparação é intra-área.** O gerador compara só contra `/jurisprudencia/`
   (main.go:715/799). Molde entre o canal de acórdão e outro canal fica invisível
   para T1 e, portanto, para T2.
6. **Troca de modelo troca veredito.** Mitigado porque `modelo` está na identidade da
   fila (fila.go:93) e no registro; a troca obriga a re-rodar a fixture.
7. **A expiração do SLA publica sem juízo.** É deliberado (nada trava), mas se o
   daemon ficar dias fora, a banda superior publica inteira sem julgamento. Fica
   contado, nunca silencioso.
8. **O maior risco honesto:** se a banda cinzenta sair grande, o custo de LLM explode
   e a tentação será alargar as bordas para caber no orçamento — que é escolher a
   leitura depois do número. A régua pré-registrada da §5b existe para barrar isso.
9. **Os controles da §5a dependem da máscara estar certa.** Se a máscara classificar
   como `andaime_do_template` uma corrida que não é, o par migra do controle positivo
   para o negativo e o teste fica mais fácil do que deveria. A verificação é substring
   contra literal conhecido e âncora literal contra as duas ementas — as duas
   conferíveis —, mas é o ponto do desenho onde um erro se propaga para a régua de
   adoção inteira.

---

## 12. Provas — comando e número esperado

1. **Passada-testemunha existe.**
   `./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 500 -testemunha <arq>`
   ⇒ **1.260 linhas**, uma por candidato iterado, com os quatro scores e as corridas
   sobrepostas classificadas. Hoje: **0 linhas** — `relata` (main.go:2268-2312) só
   imprime contagem, e os 21 pontos terminais não gravam nada.
2. **A máscara sozinha pode encerrar o caso.** Sobre as mesmas 1.260, contar os
   candidatos com **alguma** corrida `residual`. Pré-registrado: se for **0**, o
   conserto é determinístico (trocar `corpoDaPagina` por `corpoAutoral` menos andaime
   em main.go:294) e **o LLM não é adotado**.
3. **Custo do juízo.** `cmd/cerebro` `medir_modelo` `modo:"gerar"` (tarefas.go:43-48)
   sobre 20 conjuntos reais de corridas ⇒ s/julgamento. Esperado **≤ 48,5 s** (a
   mediana de extração de hoje; teto por paridade de prefill).
4. **Discriminação, contra o incumbente.** Juiz e régua incumbente pontuados sobre a
   MESMA partição da §5a. Adoção só se **estritamente melhor nos dois eixos**: menos
   falso positivo no controle negativo E não mais falso negativo no positivo. É
   comparação, não limiar inventado.
5. **Dívida do acervo, regenerada.** `cmd/measure-molde-trigrama -shard <todos>`
   ⇒ linha nova em `data/ops/molde_trigrama.jsonl` com `pares_acima`. As "32 em 43
   páginas" do cabeçalho :15-16 **não estão no ledger** (só há as duas linhas do shard
   de Tema, máximo 0,6627, `pares_acima` 0) — este é o número a produzir, não a citar.
6. **Falso negativo contínuo, de graça.** `measure-molde-trigrama` em
   `tools/run-qualidade-diaria` ao lado de :679 ⇒ par ≥ limiar cujos dois intents
   carreguem veredito `distinta` = **erro nomeado do juiz**. Esperado hoje: 0 de 0.
7. **Anti-loop.** Rodar o enfileirador duas vezes seguidas ⇒ segunda passada
   `novas=0`, como a extração já registra hoje em `data/ops/cerebro_enfileirar.jsonl`
   (`candidatos=25238 novas=0 ja_na_fila=25238`).
8. **A evidência não-merecida some.** Valores distintos de `skipped_statistical_gates`
   em `authorial_mass_manifest_transaction_rehearsal.jsonl` ⇒ **> 1**. Hoje: **1 valor
   em 11.106 linhas**.
