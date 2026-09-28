# PARIDADE — o produtor mede o que o gate mede, e toda recusa tem nome

**Arquitetura final de gates da fábrica de páginas de acórdão.**
Síntese de CAMADAS + CEREBRO + SEVERIDADE, com as emendas dos três refutadores e
o que o crítico de completude apontou. Medições próprias desta sessão marcadas
**M-A**; medições do repositório que eu reli no produtor, **M-B**; tudo o mais é
leitura de código com `arquivo:linha`.

---

## 1. A tese em três frases

1. **Esta fábrica não tem um problema de severidade: tem um problema de
   DIVERGÊNCIA.** O produtor declara espelhar o gate (`main.go:99-101`) e mede
   outro corpo com outro tokenizador; medido por mim na população viva inteira,
   só a **composição do corpo** leva a mesma régua de **13 para 134 pares acima
   de 0,70** e de 22 para **122 de 1.074 páginas** — páginas que já estão no ar e
   que nenhum gate vivo reprova. (Com o tokenizador somado, 134 → 0; esse segundo
   trecho tem ressalva de população declarada no §4.2.)
2. **Toda recusa estatística do produtor é hoje um `continue` e um `++` num
   `map[string]int`** (`main.go:294-297`, `relata:2268-2312`): sem `intent_id`
   em disco, nenhuma das 532 pode ser nomeada, muito menos refutada — e o §5
   ("gate estatístico refutado por medição é pulado, **com a evidência
   gravada**") é literalmente inexecutável.
3. **Logo a correção não é afrouxar limiar nem construir camada nem juiz de
   LLM:** é fazer o produtor **chamar a função que o gate já usa** e **dar nome
   em disco a cada recusa** — e só depois, **com o número de P2 na mesa**,
   decidir se o resíduo vai ao censo como MÉDIO. A severidade fica intacta na
   Fase 1; o que cai é a divergência, e ela cai por medição.

> **Duas fases, e a fronteira é uma medição, não uma opinião.**
> **Fase 1 (esta sessão): paridade + ledger. A terminalidade do produtor fica
> INTACTA** — `main.go:294` continua recusando, só que com a régua certa e
> gravando o nome. **Fase 2 (só se RP-2 autorizar): `molde_acima_do_limiar`
> deixa de ser terminal** e passa a MÉDIO pelo caminho do §2.2.
> Enquanto a Fase 2 não acontecer, **este plano não põe uma página no ar** — e
> dizer o contrário seria a alegação que o §5 proíbe.

---

## 2. A regra de ouro nova: **FATO · DIVERGÊNCIA · JUÍZO**

As três arquiteturas trabalharam com duas categorias. Falta a terceira, e é onde
mora **100% do excesso que eu medi**.

> **DIVERGÊNCIA** é quando dois instrumentos afirmam medir a mesma coisa e não
> medem. Não é fato nem juízo: é **bug**. Não se resolve escolhendo limiar, nem
> criando banda, nem chamando modelo. Resolve-se fazendo um **chamar o outro** —
> e depois disso o número que sobrar é o número real, sobre o qual se decide.

| classe | o que é | quem decide | pode ser julgado por contexto? |
|---|---|---|---|
| **FATO** | proposição verificável sobre o artefato ou a fonte | código determinístico | **nunca** |
| **DIVERGÊNCIA** | dois instrumentos, mesma pergunta, respostas diferentes | medição A/B | **nunca** — é defeito a fechar |
| **JUÍZO** | heurística estatística sobre semelhança/densidade | censo, como MÉDIO | **sim**, e MÉDIO publica |

### 2.1 O que NUNCA se flexibiliza (nenhuma linha desta arquitetura toca)

| eixo | onde vive, verificado | por quê |
|---|---|---|
| **Anti-fraude** | contrato §5 | nenhum limiar desta arquitetura é movido para uma página passar. O único limiar que muda de *valor efetivo* muda porque o **corpo medido** passa a ser o corpo certo — e o número que prova isso está no §4 |
| **Coerência de artefato** | `cmd/publish-v2-direct/qualitygate.go:21-31` (9 códigos: `invalid_status`, `invalid_index_policy`, `unclean_url`, `invalid_canonical`, `canonical_path_mismatch`, `duplicate_canonical`, `missing_unique_intent`, `missing_title`, `missing_meta_description`) + `publishedmanifest.Validate` no boot | HTML + sitemap + `published_manifest` + SHA-256 batendo. Nenhuma rota desta arquitetura toca a transação de `internal/publicrelease` |
| **Ética OAB Prov. 205/2021** | `internal/oabgate.CheckResposta` | promessa de resultado, preço como chamariz, captação. **Só pode ficar mais estrita** |
| **Citação legal** | `internal/v2ingest/validate.go:29-39` `maxLegalCitationSpanWords=40` + `isLegalCitationExempt` (âncora textual + mesma norma em `official_sources` + guarda anti-hub do red-team Fable 2026-07-22) | atribuição é âncora literal, FATO. **E este gate está VIVO** — §4.4 |
| **Sigilo** | `elegivel:526` → `stjacordaos.MotivoBarrado` | exceção taxativa do §2. Terminal, sempre |
| **Campo ausente · corpo vazio · encoding** | `tools/generate-v2-publication-severity:395-402,747` | fato não se interpreta |

### 2.2 O que passa a ser julgado por contexto — e por quem

**Apenas os detectores ESTATÍSTICOS do PRODUTOR**, e o julgador **não é um
modelo**: é o censo, que já classifica estatístico como MÉDIO em 10.337 páginas
vivas (`tools/generate-v2-publication-severity:750-769`, bloco `# --- medios
(publicam) ---`, vizinho de `batch_global_similarity_refutado_por_medicao`).

**E o caminho existe, mas exige uma linha — não é "já está pronto".** Página
recusada por `continue` em `main.go:294` **nunca vira linha de shard**, então o
censo não a vê. Para o resíduo chegar ao censo (Fase 2) são dois passos, ambos
sobre mecanismo existente: (a) a página é **montada e gravada** com o motivo no
ledger; (b) o motivo entra em `data/editorial/v2_rewrite_queue.jsonl`, que o
censo já lê como `queue_reasons`
(`tools/generate-v2-publication-severity:768`), e ganha **uma linha** no bloco
`# --- medios (publicam) ---` — `medium.append("molde_refutado_por_medicao")` —
ao lado de `batch_global_similarity_refutado_por_medicao` (`:764-765`), que é o
vizinho de mesmo eixo. Uma linha de Python, num bloco que já existe, e nunca em
`critical`.

**Não há LLM em nenhum caminho de veredito desta arquitetura.** O ângulo CEREBRO
caiu por três motivos que verifiquei: (a) a máscara não tinha constantes de onde
derivar — os headings e as molduras de FAQ são concatenação `+` inline
(`main.go:1596-1630`, `:2011-2016`, `:2044-2048`), não `const`; (b) o custo por
tarefa varia 2,8× entre dias no próprio ledger, então a banda que ele justificava
não tem fundamento orçamentário; (c) **o detector em camadas que ele queria que um
4b julgasse já existe, em Go, determinístico, e roda** (§4.4). Cérebro continua
onde ele rende: extração, embeddings, fila de enriquecimento. Nunca no veredito.

---

## 3. As camadas, em ordem de execução

```
C0  FATO ............. terminal, com ledger.            (inalterado)
C1  PARIDADE ......... produtor chama a função do gate.  (O CONSERTO)
C2  LEDGER ........... toda recusa com intent_id.        (torna refutável)
C3  CENSO ............ estatístico = MÉDIO = publica.    (já é a política)
C4  ESCOPO ........... procedimental, medido antes.      (frente própria)
```

---

### C0 — FATO: terminal, e agora com nome

**O que faz.** Nada muda no veredito. Continuam terminais, na ordem de
`elegivel` (`main.go:513-544`): `agravo_ou_embargo_nao_vira_pagina_propria`
(`:516`, mas ver **C4**), `tipo_de_decisao_nao_e_acordao` (`:519`),
`barrado_por_<sigilo>` (`:526`), `campo_obrigatorio_ausente_no_registro`
(`:530`).

**O que muda.** Passam a gravar linha no ledger de C2 com
`numero_processo` — recusa de elegibilidade ocorre antes de existir `intent_id`.

**Reuso.** `internal/v2ingest/v2ingest.go:130-135` (`Skipped`/`SkipReason`) é o
precedente de registro gravado que não é página.

**Prova.** Conservação: `terminais + montadas == iterados` (na Fase 1 toda recusa
é terminal; na Fase 2 o termo `juizos` entra e a soma tem de continuar fechando),
e `iterados + nunca_avaliados == candidatos` (§7, prova P1).

---

### C1 — PARIDADE: o conserto, e é aqui que a fábrica destrava

**O defeito, medido.** O produtor diverge do gate em **duas** dimensões, e as
duas são pura divergência — nenhuma é escolha de calibração:

| dimensão | produtor | instrumento de referência | consequência |
|---|---|---|---|
| **composição do corpo** | `corpoDaPagina` (`main.go:2153-2168`) inclui `secao.Heading` | `v2bodyneardup.AssembleBody` (`neardup.go:153-176`) **exclui headings de propósito** — comentário: *"para não inflar a similaridade via títulos templatizados"*. `cmd/measure-molde-trigrama.carrega` (`:191-232`) também exclui | os 6 headings do acórdão são `"A fundamentação do " + sigla + " " + numero + …` (`main.go:1596-1630`): depois de `reDigito`→"N" colapsam entre páginas quaisquer |
| **tokenizador** | `reNaoPalavra = [^\p{L}\p{N}\s]` + `ToLower` manual (`main.go:2185-2190`) — **não dobra acento, e parte "2.204" em dois tokens** | `legalsignature.Tokenize(NormalizeText(…))` — dobra acento e **preserva separador de milhar por BUG-137** (`signature.go:91-110`), correção escrita justamente para não acusar variação numérica como molde | o produtor desfaz, dentro de si, a correção BUG-137 |

**M-A — medição própria, população inteira, esta sessão.**
`data/editorial/v2_pages/stj-tema-derivado-01.jsonl`, **1.074 páginas ativas**
(`skipped=false`, `sections` não vazio), **576.201 pares**, régua do produtor
(3-gramas, `[^\w\s]|_`→espaço, minúsculas, `[0-9]+`→"N"), Jaccard exato:

| composição do corpo | máximo | pares ≥0,70 | páginas atingidas |
|---|---|---|---|
| **AssembleBody** (sem heading) | 0,7377 | **13** | 22 |
| **corpoDaPagina** (com heading) | 0,7701 | **134** | **122** |

**O heading sozinho multiplica os pares por 10,3× e as páginas por 5,5×.**

**M-B — ledger do repositório, mesma população, produtor relido.**
`data/ops/molde_trigrama.jsonl`, 2026-09-09, mesmo shard, 1.070 páginas,
571.915 pares, composição AssembleBody + tokenizador `legalsignature` + dígitos
neutralizados, 3-gramas: máximo **0,6627**, **0 pares ≥0,70**.
Verifiquei no produtor que essa régua neutraliza dígito
(`cmd/measure-molde-trigrama/main.go:237,258-261`) — não é comparação contra
régua diferente.

**O que a diferença M-A(sem heading)=13 contra M-B=0 isola:** o tokenizador do
produtor, sozinho, sobre a composição certa, acrescenta 13 pares.

> **Somadas: a régua do produtor acusa 134 pares em 122 páginas onde a régua com
> baseline medido acusa ZERO.** Não é severidade calibrada. É o produtor medindo
> outra coisa. Este é o número que responde à ordem do dono — e responde melhor
> do que "o gate é burro": o gate está certo, o produtor é que não o chama.

**O conserto.** Uma função compartilhada, e o invariante passa a valer **por
construção**, não por disciplina de quem edita:

| arquivo:linha | hoje | passa a ser |
|---|---|---|
| `internal/v2bodyneardup/` (pacote novo, ~35 linhas no pacote existente) | — | `func MoldeShingles(body string, n int) map[uint64]struct{}` — `neutralizaDigitos(NormalizeText(body))` → `Tokenize` → `WordShingleHashes`. É **literalmente o corpo de `measure-molde-trigrama.carrega:237-245`**, extraído |
| `cmd/generate-acordao-pages/main.go:2153` `corpoDaPagina` | usado para molde **e** para `contaPalavras` | fica **só** para `contaPalavras` (espelha `v2ingest.bodyWordCount`, headings incluídos — está certo para contagem) |
| `main.go:294` | `shinglesNeutralizados(corpoDaPagina(pagina))` | `v2bodyneardup.MoldeShingles(v2bodyneardup.AssembleBody(...), 3)` |
| `main.go:715,:799` (`shinglesDoProprioShard`, `parecidaComPrevia`) | idem | idem — mesma função |
| `main.go:2185-2196` `reNaoPalavra`/`reDigito`/`shinglesNeutralizados` | régua local | **removidos**; `reDigito` sobrevive só no teste, que é quem o usa como mutador |
| `main.go:99-101` comentário ("esta régua é a mais severa das duas") | alegação | substituído por M-A/M-B com data |
| `cmd/measure-molde-trigrama/main.go:237` | régua local | chama `MoldeShingles` — **um produtor, um consumidor, mesma função** |

**Por que `internal/v2bodyneardup` e não `internal/legalsignature`.** Medi:
`./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock` devolve
`portaljuridico/internal/legalsignature` e `portaljuridico/internal/quality`, e
**não** devolve `internal/v2bodyneardup`. Tocar `legalsignature` dispararia a
reatestação do grafo (25+ testes, ~10 min, §1 do contrato). `v2bodyneardup` está
fora do grafo, já hospeda `AssembleBody`, e **pode importar** `legalsignature`
sem custo — importar não invalida, só editar o diretório invalida.

**Por que 3-gramas e dígito neutralizado FICAM.** Rejeito a emenda do refutador
de SEVERIDADE ("alinhar a 5-gramas / 0,82 / dígito preservado"), com evidência:

- `cmd/generate-acordao-pages/main_test.go:261-279`
  `TestAntiMoldeRecusaIrmaQuaseIdentica` tem controle positivo escrito —
  `irma := reDigito.ReplaceAllString(corpoDaPagina(primeira), "4242")` — com o
  motivo no comentário `:272-274`: *"É o caso que o 5-grama sem neutralizar
  deixa passar, e que o 3-grama neutralizado tem de pegar."* Remover a
  neutralização abre exatamente a porta que esse teste guarda: duas páginas de
  acórdão com prosa idêntica distintas só por `REsp 1.794.991` × `REsp
  2.150.333`. Isso é doorway, e o §8 proíbe.
- A régua 3-grama-neutralizada-sem-heading tem **baseline de falso positivo
  medido**: 0 em 571.915 pares (M-B). É a única régua do repositório com esse
  baseline sobre um canal derivado vivo. Trocar régua medida por régua não
  medida é regressão de instrumento.
- `tools/check-derived-authorial-floor:288` escreve a razão:
  `TAMANHO_SHINGLE_UNICIDADE = 3  # 3-gramas sobrevivem ao numero intercalado; 5 nao`.

**E o limiar 0,70 também fica** — até o número existir (§8, regra de parada RP-2).

**Prova.** P2 e P3 do §7.

---

### C2 — LEDGER: nenhuma recusa sem nome

**O que faz.** Cada decisão do produtor grava uma linha. Sem isto, calibrar é
opinar, e é o único item em que os três refutadores convergiram.

**Onde.** `data/editorial/v2_acordao_decisions.jsonl` — dado editorial
versionável, ao lado de `v2_publication_severity.jsonl`. Nunca `/tmp`.

**Campos** (o que a refutação exige, e nada decorativo):
`intent_id` (ou `numero_processo`, para recusa de elegibilidade) · `motivo` ·
`classe` (`fato|juizo`) · `score` · `limiar` · `regua_versao` ·
`par_mais_proximo` · `populacao_comparada` · `ordem_na_passada` · `medido_em`.

- **`ordem_na_passada` é obrigatório** porque `aceitas` cresce dentro da passada
  (`main.go:300`): a n-ésima página é comparada contra n−1 assinaturas, e o
  veredito de molde é **dependente de ordem por construção**. Gravá-lo torna
  isso visível; não gravá-lo o esconde.
- **`regua_versao`** segue a cadeia `Revisao*` que o repo já usa
  (`internal/cerebro/extracao.go:128-215`, `revisao_vN`), presa por teste
  dourado. Trocar a régua não pode ser efeito colateral de um commit sobre outra
  coisa — é a parte do `assinatura_da_formula` de
  `tools/generate-page-content-revision:385-411` que **serve** aqui.

**Flag: `--gravar`, NUNCA dentro de `-seco`.** `main.go:186` declara
`"seco", false, "relata sem gravar"`, e o precedente BUG-236
(`cmd/generate-public-robots` ignorou `--stdout` e reescreveu
`public/robots.txt`) é exatamente sobre flag que promete não gravar e grava.

**Custo.** Grava onde hoje `relata` (`main.go:2268-2312`) só faz `fmt.Printf`.
Zero disco hoje; uma linha por candidato depois.

**Prova.** P1 (conservação) e P6 (mutação) do §7.

---

### C3 — CENSO: estatístico é MÉDIO, e MÉDIO publica

**O que faz na Fase 1: nada.** A política já existe e é por isso que esta camada
é barata — mas o resíduo só chega a ela na **Fase 2**, e chegar custa a linha de
Python descrita no §2.2. Na Fase 1, C3 se resume aos três consertos honestos
abaixo, que independem de tudo o mais.

**Verificado:** `near_duplicate_content` **não está** em `criticalQualityCodes`
(`cmd/publish-v2-direct/qualitygate.go:21-31`) e `qualitygate.go:112` retorna
`nil` quando `len(criticos)==0` — ou seja, **quase-duplicata já publica hoje**,
como médio, no gate que decide publicação, a 0,82/5-gramas
(`internal/quality/quality.go:84,743`).

**O que muda, e é uma linha cada:**

1. `tools/check-derived-authorial-floor:279-286`: acrescentar
   `"stj-acordao-derivado": "stj-acordao-derivado-*.jsonl"` a
   `FAMILIAS_CANAIS_DERIVADOS`, **no commit que fizer nascer o shard**. O aviso
   está escrito em caixa alta no próprio arquivo (`:271-278`): *"FAMÍLIA NOVA
   ENTRA AQUI OU NASCE FORA DO GATE… o modo mais silencioso de um detector
   mentir"* — e já aconteceu com `leis-motor` em 2026-09-10.
2. `cmd/publish-v2-direct/main.go:3957`: parar de escrever o par de strings
   chumbado em `skipped_statistical_gates`. Medido: **11.106 linhas, 1 valor
   distinto**, alegando refutação de 2026-08-06 sobre 9.620 documentos que nunca
   leram essas páginas. Campo vazio é honesto; string chumbada é evidência
   inventada — e o invariante anti-fraude corta nos dois sentidos.
3. `tools/run-daily-content:736`: trocar o `grep -q 'achado MÉDIO'` por diff do
   censo por `intent_id`. Hoje `data/ops/refinement_queue.jsonl` tem 5 linhas,
   última 2026-09-04, **zero `intent_id`** — é log de tendência, e nada se drena
   de uma fila sem nomes.

**O que NÃO se faz, e o motivo verificado:**

- **Nenhum estado `pendente` no registro.** `v2publish.Severity`
  (`v2publish.go:163-175`) não tem campo de estado e `json.Unmarshal` descarta o
  desconhecido em silêncio; `SelectPublishable` (`:391-446`) lê só
  `row.Publish`, `row.Area` e colisão de rota. Um campo novo seria decorativo —
  e roteá-lo por `skipped` o transformaria em **CRÍTICO**
  `intencao_pulada_deliberadamente` (`generate-v2-publication-severity:688`),
  inflando o crítico de 100 para milhares, que é o erro que o comentário
  `:684-687` documenta ter *"quase mandado redigir 17 páginas que não devem
  existir"*. O orçamento continua sendo o `break` de `main.go:271-273`, que já
  existe e já funciona.
- **Não se toca em `protegidos`** (`main.go:279`, `intentsPublicados:732-743`).
  A auto-exclusão do próprio shard (`prefixoDoMeu`, `:741`) é desenho: é assim
  que melhoria em `montaPagina` alcança página já gravada, com
  `shardpreserve.Completa` (`:2240`) garantindo que a gravação nunca reduz o
  shard. Congelá-la prenderia a página na versão que tinha quando o juízo saiu.
- **Não se usa `noindex` nem a lane informativa como quarentena.**
  `internal/httpserver/markdown.go:72` exclui rota não indexável da gêmea
  Markdown de propósito e `cmd/publish-v2-direct/main.go:2398` a exclui do
  `llms.txt`: num portal AI-first (§12), `noindex` é cemitério com mais passos.
  E `main.go:78` já põe o canal inteiro em `lane="informativa"`, que governa CTA
  (`internal/content/content.go:473`), não indexação.

---

### C4 — ESCOPO: `procedimental`, e por que ela é a maior frente, não a primeira

**O achado do crítico, que confirmei no código.** `elegivel` roda
`procedimental(r.Classe)` (`main.go:516`) **antes** das duas medidas diretas de
"tem tese" — ementa ≥250 (`:532`) e âncora substantiva (`:538`) — e as anula.
`procedimental` (`:316-324`) classifica a **classe dos autos** por `strings.Contains`
sobre radicais, não o que o acórdão decidiu. São **49.807 registros de 60.221**
descartados por essa linha.

**O que eu NÃO herdo do crítico:** o número 12.302 é medição dele, não minha, e
o rendimento de `montaPagina` sobre eles **não foi medido por ninguém**
(`:1554` e `:1560` dependem de `leManifesto`). E a proposição jurídica de que o
STJ julga o mérito do especial sob a classe do agravo **não tem fonte oficial
citada nesta sessão** — pelo §9 do contrato, isso se escreve como "sem fonte
oficial", não se afirma.

**Por que é frente própria e vem depois.** O rótulo "doorway" que SEVERIDADE
colou nos 49.807 foi refutado por medição do crítico (o pool recusado é **menos**
duplicado que o publicado) — mas o critério certo já está escrito no repo:
`docs/goal/MAESTRO_CODEX_LOG.md:4176-4189`, *"Entidade = distinta por construção
(URN LexML única); doorway só em colisão de URN"*. Número de processo distinto é
entidade distinta. O caminho é mecânico e **não** passa por opinião sobre lei:
**trocar a classe dos autos pelo que o dispositivo diz**, medir o rendimento em
`-seco`, e pré-registrar a régua (§8, RP-4).

---

## 4. Os defeitos medidos que esta arquitetura conserta

### 4.1 Divergência de composição do corpo — **MEDIDO**

Produtor inclui headings; a especificação do gate os exclui com o motivo escrito
(`neardup.go:153-156`).
**Efeito isolado (M-A, 1.074 páginas, 576.201 pares): 134 → 13 pares ≥0,70;
122 → 22 páginas.** Sobre a população viva de tema, o conserto **desmarca 100
páginas de 122** — 82,0% do que essa régua acusa.
*Páginas de acórdão destravadas: **NÃO MEDIDO** — ver §9, lacuna L1.*

### 4.2 Divergência de tokenizador — **MEDIDO, com ressalva de população**

Produtor não dobra acento e parte separador de milhar, desfazendo o BUG-137 que
`legalsignature.NormalizeText:91-110` corrigiu.
**Efeito aparente: M-A sem heading = 13 pares contra M-B = 0 ⇒ 13 → 0.**

**A ressalva, e ela é minha:** M-A leu **1.074** páginas hoje; M-B leu **1.070**
em 2026-09-09, com seis ondas diárias no meio. As populações **não são as
mesmas**, então os 13 pares podem ter entrado com as páginas novas em vez de
virem do tokenizador. **4.1 é limpo** (as duas variantes saíram do mesmo
processo, sobre as mesmas 1.074 páginas); **4.2 não é.**
*Fecha com:* **P3** — rodar `measure-molde-trigrama` sobre o shard de HOJE. Se
ele devolver 0 sobre as 1.074, o isolamento vale; se devolver 13, o tokenizador
não explica nada e só 4.1 sustenta a tese (que já basta: 134 → 13).

### 4.3 Recusa sem nome — **MEDIDO, e é 100%**

`relata` (`main.go:2268-2312`) imprime `map[string]int`. **760 de 760 recusas da
passada `-seco -limite 500` não podem sequer ser nomeadas.** O ledger de C2 leva
esse número a 0. Não destrava página por si — **destrava a capacidade de
refutar**, que é o pré-requisito do §5.

### 4.4 O gate em camadas que ninguém sabia estar vivo — **CADEIA VERIFICADA**

O crítico afirmou que `internal/v2ingest/validate.go:1106-1166`
(`classifyDuplicatePhrases` + `isLegalCitationExempt`) "não tem invocador".
**É falso, e eu tracei a cadeia inteira:**

```
tools/deploy-publico:433            ./tools/ingest-v2-stock
  → cmd/ingest-v2-stock/main.go:433 v2ingest.PrepareTransactionPlan
  → internal/v2ingest/plan.go:244   Run(stageOpts)
  → internal/v2ingest/v2ingest.go:449  validateBatch(...)
  → internal/v2ingest/validate.go:471  classifyDuplicatePhrases(...)
```

O crítico olhou só `cmd/ingest-v2-pages/main.go:46` e perdeu o caminho
transacional. **Consequência que reordena tudo:**

- O detector de frase idêntica de 12 palavras **com isenção por citação legal
  ancorada** (`maxLegalCitationSpanWords=40`, mesma norma em `official_sources`,
  guarda anti-hub) **roda no caminho do deploy**. É exatamente o
  `internal/v2bodylayers` que CAMADAS queria construir e o
  `linguagem_forense_da_fonte` que CEREBRO queria que um 4b julgasse. **Já
  existe, é determinístico, e tem histórico de falso positivo fechado**
  (`DUPPHRASE_205_CHARACTERIZATION_20260722`). Construir outro seria duplicar
  um gate vivo.
- Página reprovada vira `StatusRejected` — cai do **estoque**, não aborta a onda.

**E aqui vem a correção que eu mesmo tive de fazer, porque ela derruba a
conclusão fácil.** Medi o consumidor: `cmd/publish-v2-direct/main.go:316` chama
`v2publish.LoadPages(root)`, que faz `filepath.Glob(root, PagesGlob)` —
**`data/editorial/v2_pages/*.jsonl`, o shard cru** (`v2publish.go:194-199`).
Não o estoque ingerido.

> **O gate de 12 palavras reprova do ESTOQUE; o publicador publica do SHARD.**
> São artefatos paralelos. Logo **é falso** dizer "relaxar terminalidade
> estatística no produtor é seguro porque atrás dela há um gate melhor": atrás
> dela, no caminho que gera `public/`, **não há esse gate**. O comentário do
> próprio `qualitygate.go:38-42` já dizia o quanto esse caminho pulava
> (*"cmd/publish-v2-direct nunca importou internal/quality… foi assim que 9.622
> páginas foram ao ar com a seção 'Links internos' vazia"*).
> **É por isso que a Fase 1 não relaxa nada**, e é por isso que a Fase 2 é
> condicionada a RP-2 em vez de ser consequência automática desta leitura.

### 4.5 O P0 real do canal de acórdão, que nenhuma das três viu — **PREDITO**

O comentário do próprio gerador (`main.go:1854-1863`) registra medição no lote
real de 2026-09-10: o pior par do canal (`jur-stj-resp-2117412` ×
`jur-stj-resp-2107422`, ambos sobre art. 51 e art. 4º do CDC) tem **81 palavras
seguidas iguais** em `blocoDispositivosLegais`, *"contra o teto de 12 do
ingest"*. O autor tentou quebrar a corrida, ela **subiu para 86** e a camada
citada caiu de 109 para 88 palavras, e ele arquivou como *"dívida da família…
RCA de família, não conserto de gerador"*.

Cruzando com 4.4: **81 > `maxLegalCitationSpanWords = 40`** ⇒ a isenção por
citação legal **não se aplica**, mesmo ancorada (`validate.go:29-39`, literal:
*"um trecho idêntico com mais de ~40 palavras é parágrafo-molde (near-dup/
fórmula), não citação legal, e continua reprovando mesmo se ancorado"*).

> **Predição:** quando o shard de acórdão chegar ao ingest, essas páginas serão
> rejeitadas **do estoque** por um gate determinístico e vivo — e a régua Jaccard
> de 0,70 não terá nada a ver com isso. **Há um defeito de produtor
> (`blocoDispositivosLegais`, `main.go:1841-1884`) que nenhuma das três
> arquiteturas viu, e ele é maior que o detector estatístico.**
> Rotulado **PREDITO, não medido**, e com dois furos declarados: (a) o shard não
> existe; (b) como o publicador lê o shard e não o estoque (§4.4), **não está
> verificado se essa rejeição impede a publicação ou só suja o estoque**. O teste
> que fecha (a) é P4; o que fecha (b) está em L5.

### 4.6 Evidência não merecida em produção — **MEDIDO**

`skipped_statistical_gates`: 11.106 linhas, 1 valor distinto. Vai a 0 com a
linha 3 de C3.

### Quadro-resumo

| defeito | classe | efeito medido | páginas |
|---|---|---|---|
| composição (headings) | DIVERGÊNCIA | 134 → 13 pares | **100 de 122 desmarcadas** (tema, vivo) — MEDIDO |
| tokenizador | DIVERGÊNCIA | 13 → 0 pares | **22 desmarcadas** — MEDIDO **com ressalva de população** (§4.2); P3 fecha |
| recusa anônima | instrumento | 760 → 0 anônimas | 0 destravadas, mas torna tudo refutável — MEDIDO |
| `blocoDispositivosLegais` 81 palavras | produtor | 81 > teto 40 | **PREDITO** — P4 mede; alcance sobre `public/` não verificado (L5) |
| família fora do gate Python | ponto cego | 1 linha | 0 — prevenção |
| `skipped_statistical_gates` | anti-fraude | 1 → 0 strings chumbadas | 11.106 linhas — MEDIDO |
| `procedimental` | ESCOPO | rendimento **NÃO MEDIDO** | frente C4 |
| **532 recusas do acórdão** | — | **NÃO MEDIDO** | **só P2 produz este número** |

---

## 5. O anti-looping

Sem LLM no veredito, o laço possível é **regerar → mesma recusa → regerar**, e
ele se fecha com quatro travas, nenhuma nova:

1. **O produtor é determinístico e puro.** Mesmo corpus + mesma régua + mesma
   ordem ⇒ mesmo veredito. Não há amostragem, logo não há veredito que se
   contradiz — que era o que obrigava CEREBRO a inventar "teto de contestação".
2. **Ledger com chave `(intent_id, regua_versao)`.** Segunda passada com a mesma
   régua não produz linha nova; só o bump de `regua_versao` reabre. É o padrão
   `Revisao*` de `internal/cerebro/extracao.go:128-215`, e aqui ele é
   **legítimo** porque a re-derivação é função pura do texto — a objeção do
   refutador de CEREBRO (veredito de LLM não é idempotente) não alcança um
   produtor determinístico.
3. **Conjunto de candidatos fixo.** `intentsPublicados` (`:732-743`) +
   `emitidos` (`:281-286`) + `shardpreserve.Completa` (`:2240`) já impedem que a
   passada se realimente. **Nada aqui muda** — e não se toca em `protegidos`,
   justamente para que a regeneração continue alcançando página já gravada.
4. **Gate por FLUXO, nunca por NÍVEL.** Qualquer fila que esta arquitetura
   alimentar (`v2_rewrite_queue.jsonl`) reprova por *entrada nova sem drenagem*,
   não por tamanho. Gate de nível contra política deliberada fica
   permanentemente vermelho e acaba desligado — precedente
   `gate-vermelho-por-estoque-que-nada-drena`.

**E a trava que dispensa fila inteira:** o dreno do juízo de molde é o **próprio
gerador re-rodado com a régua consertada**. Custo zero de LLM, determinístico, e
o juízo desaparece na re-medição — o que só é verdade porque C1 **de fato** muda
a régua. (Era a circularidade que derrubou SEVERIDADE: ela prometia o dreno e
declarava a calibração fora de escopo. Aqui a calibração **é** o escopo.)

---

## 6. Ordem de execução

### Sangra hoje — cabe numa sessão

| # | passo | arquivos | custo |
|---|---|---|---|
| **1** | `MoldeShingles` em `internal/v2bodyneardup` (extração de `measure-molde-trigrama:237-245`) + `measure-molde-trigrama` passa a chamá-la | 2 arquivos, ~35 linhas | fora do grafo de atestação (medido) |
| **2** | produtor chama `AssembleBody` + `MoldeShingles` em `:294,:715,:799`; remove `:2185-2196`; `corpoDaPagina` fica só para `contaPalavras` | 1 arquivo | leve |
| **3** | atualizar `TestAntiMoldeRecusaIrmaQuaseIdentica` (`main_test.go:261-279`) para a função nova — **os dois controles têm de continuar valendo**, e o positivo é o que prova que a neutralização sobreviveu | 1 arquivo | — |
| **4** | ledger C2 com `--gravar` (fora de `-seco`) | 1 arquivo | — |
| **5** | **P2**: `-seco -limite 500` com a régua nova, contra os mesmos 1.260 candidatos | — | ~min, load ≤12 |
| **6** | ler as 20 de maior score do ledger e classificar molde real × falso positivo (§8, RP-2) | — | leitura minha |
| **7** | `skipped_statistical_gates`: parar de escrever o literal (`publish-v2-direct/main.go:3957`) | 1 arquivo | — |

Passos 1–4 tocam Go ⇒ commit serializado em `flock /tmp/opt-wiki-commit.lock`
(o heavy é da bancada). Passo 7 é commit leve, separado.

### Prevenção — depois, e só com o número de P2 na mão

| # | passo | gatilho |
|---|---|---|
| 8 | **P4**: montar as 500 em ensaio **por cópia** e passá-las por `validateBatch` — mede 4.5 | logo após P2 |
| 9 | `blocoDispositivosLegais` (`main.go:1841-1884`): quebrar a corrida de 81 palavras **sem comer a camada citada** | só se P4 confirmar |
| 10 | `"stj-acordao-derivado"` em `FAMILIAS_CANAIS_DERIVADOS` | no commit que fizer nascer o shard |
| 11 | diff do censo em `run-daily-content:736` | — |
| 12 | **C4**: `procedimental` por dispositivo, com RP-4 pré-registrada | frente própria |
| 13 | indexar o anti-molde (prefixo de `v2bodyneardup`, ou `internal/legalminhash`/`densepairset`) | **antes** de qualquer passada > 500 |

### E o que NENHUM dos passos acima faz: pôr página no ar

**Declarado, porque o implícito aqui seria desonesto.** `generate-acordao-pages`
**não está** em `tools/run-daily-content:368-373` (a lista tem cinco geradores:
stj-tema, stj-sumula, stf-informativo, noticias, diarios) e o shard **não
existe**. Paridade + ledger entregam **zero páginas no ar**. A publicação é uma
sequência própria, com regras de commit próprias, e só começa **depois** de P2 e
RP-2:

| # | passo | regra que o governa |
|---|---|---|
| **A** | passada real (sem `-seco`) com `-limite` ≤ 500 — o shard nasce | §6 passo 13: acima de 500, indexar antes |
| **B** | commit `portfolio_v2/` **primeiro**, `v2_pages/` **depois**, com `./tools/check-v2-portfolio-pairing` antes | §1 do contrato: o gate recusa página cujo `intent_id` não esteja no portfólio do commit **pai** |
| **C** | `"stj-acordao-derivado"` em `FAMILIAS_CANAIS_DERIVADOS` **no mesmo commit** — e o gate vai ficar **vermelho** sobre a família nova, que é o preço honesto | `check-derived-authorial-floor:271-286` |
| **D** | linha em `GERADORES` de `tools/run-daily-content` | só depois de A–C verdes |

**Quem executa é esta engenharia, em sessão de escrita.** Nada de A–D devolve
decisão, cadastro ou revisão de conteúdo ao dono.

**O passo 13 não é desta sessão, e o motivo é medido:** `main_test.go:583-589`
registra que com n = 1.569 a passada O(n²) **não terminou em 10 minutos num
núcleo**. `-limite 500` cabe; acima disso, indexar — e o §11 do contrato chama
lentidão em 10k de bug P0 e proíbe "corrigir" aumentando timeout.

---

## 7. As provas de aceitação

| # | comando | número esperado |
|---|---|---|
| **P1** | `./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 500 --gravar <ledger>` e depois contar o ledger | `montadas + terminais == iterados` (**hoje 500 + 760 = 1.260**; na Fase 1 toda recusa ainda é terminal) e `iterados + nunca_avaliados == candidatos` (**1.260 + 3.503 = 4.763**). Linhas sem `intent_id` **nem** `numero_processo`: **0** (hoje: 760 de 760) |
| **P2** | a mesma passada de P1, comparando `molde_acima_do_limiar` | hoje **532**. Esperado **N < 532**, com direção dada por M-A (100 de 122 páginas desmarcadas no proxy). **Este é o número que a frente promete e que ninguém tem** |
| **P3** | `./tools/go-modern run ./cmd/measure-molde-trigrama -shard data/editorial/v2_pages/stj-tema-derivado-01.jsonl` **antes** do passo 1 (linha de base sobre a população de hoje) e **depois** | **antes ≡ depois**, byte a byte nos campos `maximo`/`pares_acima`. Divergência ⇒ a extração de `MoldeShingles` mudou o comportamento e o commit não pousa (RP-1). O valor absoluto **também responde à ressalva de 4.2**: `pares_acima 0` sobre as 1.074 de hoje confirma o isolamento do tokenizador; `pares_acima 13` o refuta |
| **P4** | montar as 500 em ensaio **por cópia** (nunca hardlink — precedente `ensaio-hardlink-codigo-quebra-atestacao`) e rodar `cmd/ingest-v2-pages` contra raiz temporária | conta as rejeitadas por `duplicate_phrase_with_page`. **Esperado > 0** se 4.5 estiver certa. Cada uma é achado de produtor, não de detector |
| **P5** | `./tools/go-modern test -count=1 ./cmd/generate-acordao-pages/` | `TestAntiMoldeRecusaIrmaQuaseIdentica` **verde nos dois controles**. **Prova por mutação, obrigatória:** remover a neutralização de dígito de `MoldeShingles` ⇒ o controle positivo (`irma`, só números trocados) tem de **FALHAR**. Se ficar verde com a neutralização removida, o teste não guarda nada (`teste-que-reimplementa-nao-testa`) |
| **P6** | trocar o veredito de uma página e conferir a linha do ledger | a linha **muda**. Ledger que não muda com o veredito não mede o veredito (`teste-que-reimplementa-nao-testa`) |
| **P7** | `./tools/go-modern run ./cmd/check v2-body-near-duplicates` antes e depois | **mesmo número de pares**. O eixo histórico de corpo inteiro não muda; a série de `tools/run-qualidade-diaria:679` não pode mudar de valor em silêncio |
| **P8** | contar valores distintos de `skipped_statistical_gates` em `data/editorial/authorial_mass_manifest_transaction_rehearsal.jsonl` | hoje **1 em 11.106 linhas**; esperado **0 strings chumbadas** após o passo 7 |
| **P9** | `python3` reproduzindo M-A com **sha256** em vez de `hash()` | os mesmos 13 / 134 pares, ±colisão. Fecha a lacuna L4 |

---

## 8. As regras de parada — decididas ANTES do número

**RP-1 — P3 não reproduz o ledger (≠ 0 pares / ≠ 0,6627).** **Para tudo.** A
extração de `MoldeShingles` mudou o comportamento do instrumento de referência,
e todo o §4.2 perde o chão. Corrigir a extração antes de qualquer outra coisa.

**RP-2 — leitura das 20 de maior score (passo 6), pré-registrada, e com critério
MECÂNICO — não "conferido à mão".**

O refutador de SEVERIDADE atacou exatamente "veredito conferido à mão", e com
razão. O critério aqui é verificável e o ledger já traz o insumo: para cada par,
**imprimem-se os shingles compartilhados e a posição de cada um no corpo**.

> **Molde real** = a maioria dos shingles compartilhados cai em **prosa autoral**
> — fora de todo span `“…”` e fora de `blocoEmenta`/`parteOperativa`.
> **Falso positivo** = a maioria cai **dentro** de span citado ou em lista de
> dispositivos (`blocoDispositivosLegais`), isto é, o molde é **da fonte** ou é
> enumeração de norma, não prosa nossa repetida.

A partição usa a marca que o repo já usa nos dois lados
(`check-derived-authorial-floor:268` `CITACAO = “([^”]{10,})”`; gerador
`main.go:2171` `reAspas`), e a leitura é da engenharia, nunca do dono.

- **≥ 19 de 20 são molde real** ⇒ a régua está certa e o defeito é do produtor.
  **Não se toca no limiar. NÃO se faz a Fase 2.** Vai-se para
  `blocoDispositivosLegais` (§4.5) e `perguntas()`.
- **≤ 1 de 20 é molde real** ⇒ a régua erra neste canal ⇒ **Fase 2 autorizada**
  (`molde_acima_do_limiar` vira MÉDIO). **Ainda assim não se move o limiar**
  antes de nomear *quais shingles* carregam o score; o precedente do repo é 46/46
  e 29/29 falso positivo, e quem ajusta constante sem nomear a causa repete isso.
- **Entre 2 e 18** ⇒ ambíguo: declara-se, grava-se, **não se muda constante
  nenhuma e não se faz a Fase 2**. O caminho é reduzir a ambiguidade medindo
  mais, nunca escolher a leitura depois do número.

**RP-3 — P2 devolve N ≥ 532.** **Para e reverte a expectativa, não o commit.** O
conserto de paridade continua certo (é divergência, e divergência se fecha de
qualquer modo), mas a frente **não destravou** e dizer que destravou seria
alegação. Nesse caso o gargalo é o produtor do acórdão, e o §4.5 vira P0
imediato.

**RP-4 — C4 (`procedimental`), pré-registrada antes de medir:** só se troca a
classe dos autos pelo dispositivo se a passada `-seco` com o filtro contornado
der **rendimento de `montaPagina` ≥ o do pool atual (500 de 1.260 = 39,7%)** e
**colisão de URN/rota = 0**. Abaixo disso, o pool novo é pior que o atual e não
entra. E a proposição jurídica sobre a classe do agravo **só se escreve com fonte
oficial primária, URL e data** — senão escreve-se "sem fonte oficial" (§9 do
contrato, R9).

**RP-5 — P7 diverge.** `AssembleBody` mudou de comportamento ao ser
compartilhado. **O commit não pousa.**

**RP-6 — load > 12 ou `check-load-headroom` reprova.** Nenhuma passada pesada
começa; trabalha-se outra frente. E **nenhuma passada acima de `-limite 500`**
antes do passo 13.

---

## 9. O que NÃO está verificado — sem maquiagem

**L1 — A camada autoral de página de ACÓRDÃO nunca foi medida, por ninguém.**
`data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` **não existe** (conferi:
`ls | grep -i acordao` devolve vazio, exit 1). Toda a minha medição M-A é sobre
`stj-tema-derivado`, que é **proxy**. E o proxy pode subestimar em uma direção
nomeada: `blocoDispositivosLegais` (`main.go:1841-1884`) sai idêntico quando dois
julgados invocam os mesmos artigos — 81 palavras seguidas, medido pelo autor — e
esse bloco **não tem equivalente nas páginas de Tema**. Os headings de acórdão
(`"A fundamentação do " + sigla + " " + numero`, `main.go:1596-1630`) também
colapsam mais que os de Tema depois da neutralização, o que empurra na direção
oposta. **Nenhum dos dois efeitos foi medido.**
*Fecha com:* **P2** — e é por isso que P2 é pré-requisito, não prova posterior.

**L2 — O número 532 → N não existe.** Eu não rodei o gerador. A sessão é
somente-leitura, e uma passada `-seco` compila e roda o produtor. **"Destravou" é
alegação até P2.** A comparação honesta é contra os **mesmos 1.260 candidatos
iterados**, não contra os 4.763.
*Fecha com:* **P2**.

**L3 — O rendimento de `montaPagina` sobre os acórdãos hoje recusados por
`procedimental` não foi medido por ninguém.** O número 12.302 é medição do
crítico de completude sobre `elegivel`, que é **elegibilidade, não páginas
prontas** — `montaPagina` tem mais quatro recusas (`:1554`, `:1560`, `:1653`,
`:1660`) que ninguém exerceu sobre esse pool. E a proposição jurídica que
justificaria a mudança **não tem fonte oficial nesta sessão**.
*Fecha com:* `-seco` com o filtro contornado + RP-4, e a fonte oficial com URL,
data e hash antes de qualquer afirmação sobre a lei.

**L4 — M-A usou `hash()` do Python, que o §2/R3 do contrato proíbe como hash
determinístico.** O A/B é **internamente válido** (as duas variantes foram
hasheadas no mesmo processo, com a mesma semente, então as interseções e os
Jaccards estão corretos e são comparáveis entre si), e colisão em 64 bits sobre
conjuntos de ~400 elementos é desprezível. Mas os números **não são reprodutíveis
entre processos** e não podem entrar em ledger nem em contrato nesta forma.
*Fecha com:* **P9** (repetir com sha256) ou, melhor, **P3** rodando o produtor Go
com `WordShingleHashes`.

**L5 — O §4.5 (81 palavras > teto de 40) é PREDIÇÃO, e o ALCANCE do gate de 12
palavras sobre `public/` não está verificado.** A cadeia de invocação
(deploy → `ingest-v2-stock` → `PrepareTransactionPlan` → `Run` → `validateBatch`
→ `classifyDuplicatePhrases`) eu verifiquei linha a linha. O que **não**
verifiquei: (a) a consequência sobre páginas de acórdão, porque o shard não
existe; (b) **se rejeição do estoque impede publicação** — medi que
`publish-v2-direct:316` publica do shard cru via `v2publish.LoadPages`
(`v2publish.go:194-199`), o que sugere que **não impede**, mas não tracei o que o
estoque governa a jusante; (c) se `ModeRewrite` revalida páginas já aceitas ou só
as novas; (d) se a isenção do Tune 1 (mesma URL canônica completa) alcançaria
esses spans.
*Fecha (a) com:* **P4**. *Fecha (b) com:* rodar o deploy em ensaio **por cópia** e
conferir se uma página `StatusRejected` no estoque aparece ou não em `public/`.
**Enquanto (b) estiver aberto, nenhuma decisão deste plano se apoia em "há um
gate atrás"** — e é por isso que a Fase 1 não relaxa nada.

**L6 — Três tokenizadores continuam divergindo no repositório, e eu fecho só
um.** Medido por leitura: gerador `[^\p{L}\p{N}\s]` sem dobra de acento
(`main.go:2185`); `legalsignature.NormalizeText:91` com dobra e separador de
milhar preservado; Python `[^\w\s]` com `re.UNICODE`, que **preserva o
sublinhado** (`check-derived-authorial-floor:292`);
`cmd/generate-stj-tema-pages/unicidade_test.go:35-38` com
`[^\p{L}\p{N}_\s]`, que também o preserva — e reimplementa a montagem **de
propósito**. C1 elimina o do gerador. Os outros três continuam de pé, e a
paridade Go↔Python **não tem teste**.
*Fecha com:* um teste que rode as duas implementações sobre as mesmas 1.074
páginas e compare a partição página a página, gravando o N divergente — **não**
uma fixture de `Split` contra si mesmo.

**L7 — Não medi o efeito nos outros seis geradores.** Cinco irmãos a 0,60/3-gramas
e o de lei-artigo a 0,70 provavelmente têm a mesma divergência de composição. A
generalização é **plausível, não medida**, e M-A só fala do canal de Tema.
*Fecha com:* rodar o A/B de M-A (já escrito) sobre cada shard de
`FAMILIAS_CANAIS_DERIVADOS`.

**L8 — Não medi a comparação entre áreas.** `parecida`/`parecidaComPrevia`
(`main.go:715,:799`) comparam só dentro da mesma `practice_area`. Molde entre o
canal de acórdão e outro canal continua invisível, antes e depois desta
arquitetura. **Não é regressão; é ponto cego preexistente que eu não fecho.**

**L9 — `data/ops/molde_trigrama.jsonl` tem 2 linhas, ambas do shard de Tema.** O
"32 pares em 43 páginas sobre 10.141 páginas vivas" do cabeçalho de
`cmd/measure-molde-trigrama/main.go:15-16` **não está no ledger** e **não se
reproduz**. Tratei-o como número a produzir, nunca a citar — e esta arquitetura
não se apoia nele em lugar nenhum.

**L10 — Este plano para no gate; publicação é sequência separada e ainda não
começou.** `generate-acordao-pages` não está em `run-daily-content:368-373`, o
shard não existe, e **Fase 1 entrega zero páginas no ar**. A sequência A–D do §6
é a que publica, e ela depende de P2, de RP-2 e do pareamento
portfólio↔páginas. Qualquer relatório que diga "destravou N páginas" antes de A–D
estará medindo intenção, não produção.

---

## Fecho: o que esta arquitetura recusa das três, e por quê

| recusado | de | motivo verificado |
|---|---|---|
| `internal/v2bodylayers` (pacote novo de partição) | CAMADAS | o detector em camadas **existe e roda** (`validate.go:1106-1166`, cadeia do §4.4). Construir outro é duplicar um gate vivo com histórico de falso positivo fechado |
| juiz de molde por LLM, banda cinzenta, SLA de retenção | CEREBRO | máscara sem constantes de onde derivar (`main.go:1596-1630`, `:2011-2016` são concatenação inline); custo/tarefa varia 2,8× entre dias, então a banda não tem fundamento orçamentário; e o rótulo restritivo do juiz não é verificável |
| estado `pendente` no registro + campo em `Severity` + edição do censo | SEVERIDADE | `json.Unmarshal` descarta campo desconhecido em silêncio (`v2publish.go:220`); `SelectPublishable:391-446` não o leria; e roteá-lo por `skipped` o tornaria **CRÍTICO** |
| remover a neutralização de dígito | refutador de SEVERIDADE | `main_test.go:272-274` tem controle positivo escrito contra exatamente esse doorway |
| congelar `protegidos` com juízo vigente | CEREBRO §7.5 | prenderia a página na versão do juízo para sempre; `shardpreserve.Completa` preservaria a linha velha |
| "49.807 páginas de agravo é doorway" como invariante | SEVERIDADE | refutado por medição do crítico; e o critério certo já está escrito em `MAESTRO_CODEX_LOG.md:4176-4189` (doorway só em colisão de URN) |

**O que sobrevive das três, e é o que esta arquitetura é:** a leitura de CAMADAS
de que as camadas têm réguas diferentes (mas a partição já existe em Go); a
insistência de CEREBRO de que o detector tem de **gravar o que viu** e não só
matar (mas sem LLM); e a tese de SEVERIDADE de que **recusa sem nome é o defeito
que impede consertar todos os outros** (mas com a calibração dentro do escopo, não
fora dele). E o que nenhuma das três tinha: **o número que prova que o excesso é
divergência, não severidade — 134 → 13 pares medido limpo sobre a mesma
população viva no mesmo processo (§4.1), e 134 → 0 se P3 confirmar a ressalva de
população do §4.2.**
