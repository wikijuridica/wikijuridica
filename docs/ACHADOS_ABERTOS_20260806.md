# Achados abertos — 2026-08-06

O que foi encontrado nesta sessão e **não** cabia nas tasks em curso. Cada item
traz a evidência já medida, para que o próximo turno comece de onde este parou e
não repita a medição.

Ordenado por retorno, não por facilidade.

---

## 0. A fila de escrita voltou a montar (2026-08-07)

`ops/relaunch-writing.sh` — que monta a fila de páginas novas — **abortava**.
Enquanto isso, nenhuma página nova podia ser escrita, e havia 324 intents de
portfólio sem página, 102 deles com brief pronto e fonte já resolvida.

Três causas, todas corrigidas:

1. **636 chaves de `source_hint` em texto livre.** A regra
   (`ops/relaunch-writing.sh:199`) exige kebab-slug ASCII; havia `"CC Lei
   10.406/2002 art. 1.147"`. Todas com URL oficial e campos corretos — só a
   chave. Normalizado nos DOIS lados sob o mesmo lease (catálogo + 896
   referências em 22 portfólios).
2. **20 URLs com fragmento de artigo** (`l10406.htm#art1240a`). Fragmento é
   navegação, não identidade — o servidor nem o recebe. As 20 URLs-base já
   apareciam sem fragmento em outros hints: a convenção era essa, elas é que
   destoavam.
3. **5 intents protegidos** viraram stale com a normalização (3 por requisito
   semântico, 2 por `active_source_changed_without_provenance`). Restaurados à
   linha exata do commit, com guarda que só aceita quando a única diferença é
   `source_hints`.

**Um falso positivo que quase virou mudança errada:** 15 entradas apareceram no
meu diagnóstico como "host não oficial" (`normattiva.it`, `diariodarepublica.pt`,
`boe.es`, `sistemas.cfm.org.br`). Estão certas — são as fontes oficiais das
páginas de cidadania italiana e portuguesa — e **já constavam da allowlist
`WRITING_SOURCE_EXACT_HOSTS`**. Meu script de teste é que não a consultava. Ia
mexer numa regra correta.

**Ganho imediato:** 5 lotes 100% mecânicos (ordem de linha divergente do slice
pinado) resolvidos **sem agente** por `tools/generate-v2-shard-slice-reorder`,
com permutação provada por multiset e CAS antes/depois — 49 páginas.

### O que foi resolvido depois (mesma sessão)

**549 fontes registradas no catálogo**, a partir de `data/legal-corpus/` — URL
oficial do Planalto, `document_sha256` e `fetched_at` já verificados. O
`anchor_claim` é o caput real do artigo citado; quando o hint não nomeia artigo,
a âncora só identifica o documento e a data de coleta, sem afirmar conteúdo não
conferido. Hint cujo diploma não está no corpus fica intacto: entrada ausente é
honesta, inventada é fraude.

| | antes | depois |
|---|---|---|
| hints ausentes | 1.857 | **1.312** |
| intents bloqueados | 2.008 | **1.496** |
| entradas no catálogo | 3.150 | **3.699** |
| lotes fora da fila | 394 | **364** |
| páginas escrevíveis na fila | 123 | **140** |

**Bug meu, corrigido no meio:** o comparador de apelido de diploma usava só
`.lower()`, então `"Código Civil art. 951"` não casava a entrada `"codigo
civil"`. Mil e sete referências apareciam como "fora do corpus" tendo a fonte
disponível. Com a normalização de acento, mais 146 hints resolveram.

**Nada de conteúdo foi tocado, e isso foi medido:** comparando o estoque entre a
publicação (`384f11cf`) e agora, mudaram `official_sources` (170), `title`/`h1`
(19) e `word_count` (3). **Prosa alterada em ZERO registros.** O peso ao vivo,
medido como Googlebot, ficou em 20 KB de média e 22,8 KB no pior caso — contra
teto de 50 KB do contrato; 5,7 a 7,8 KB com gzip.

### O que continua bloqueado, com o número medido

`prontos=42 faltantes=17 paginas_faltantes=140` e **364 lotes aguardando
catálogo**. A causa é uma só:

> **1.496 intents declaram `needs_source_research: false` — pesquisa concluída —
> e citam `source_hint` que não existe no catálogo.** São 1.312 hints distintos
> ausentes (`leis-estaduais-itcmd`, `resolucao-cmn`, `stf-tema-987`, `TNU`…).

O gate está certo: declarar pesquisa concluída sem a fonte resolvida é
inconsistência. Mas **1.927 desses 2.008 intents JÁ TÊM PÁGINA no ar** — o
defeito é do metadado do portfólio, não do conteúdo publicado. Só 81 estão sem
página.

Os 1.312 que sobraram estão em três classes que o corpus não cobre:

1. **norma de agência fora do Planalto** — RN 279/2011 (ANS), Res. CONTRAN
   918/2022, IN RFB 2110/2022, CVM, ANPD. Cada portal exige coleta própria;
2. **jurisprudência** — temas do STF/STJ e súmulas, sem canal mapeado (§4e-bis);
3. **categoria plural** — `leis-estaduais-itcmd`, `detrans-estaduais`. Essas
   **não têm URL única legítima**: são 27 leis estaduais. Aqui o correto não é
   inventar fonte, é o intent declarar `needs_source_research: true` ou trocar
   por um hint concreto.

**Sobra 1 hint quebrado de propósito:** `decreto-35851-1954`
(`normas.leg.br/?urn=…`, documento em query sobre path raiz).
`tools/generate-catalog-url-repair` tentou e não achou candidato respondendo 200.

## 1. Um gate que reprova por contagem própria pode estar barrando página boa

**Estado: causa corrigida, classe não varrida.**

O censo de severidade — que decide o que publica — contava palavras com uma
fórmula diferente da do gate de ingestão. Somava só `opening` + `sections[].text`;
a fórmula oficial (`bodyWordCount`, `internal/v2ingest/validate.go:984`) soma
também o *heading* de cada seção e o *q/a* de cada FAQ. Resultado: **37 páginas
marcadas como CRÍTICAS — proibidas de publicar — tinham entre 339 e 437
palavras**, e 2.018 apareciam como rasas sem serem.

Corrigido em `d2de4e02`, protegido por `tools/check-body-word-count-formula`, e
as 36 páginas resultantes foram ao ar em `384f11cf`.

**O que fica aberto:** essa mesma classe de defeito — *ferramenta de auditoria
que reimplementa uma regra do gate e diverge dela* — não foi varrida. O censo
tinha DOIS casos (a contagem e as chaves do FAQ) e ninguém os viu por meses. Vale
uma varredura dirigida: para cada regra que o Go aplica (`word_count`,
`title_length`, `meta_description`, `sections >= N` por `page_type`), conferir se
a ferramenta Python que a replica chega ao mesmo número sobre o estoque inteiro.

## 2. `visible_text` do censo ficou cega ao FAQ — e alimenta o detector de OAB

**Estado: corrigido, sem achado novo, mas o padrão merece atenção.**

A função pedia o FAQ pelas chaves `question`/`answer`; as reais são `q`/`a`.
Devolvia string vazia **em silêncio**. Todo detector apoiado nela — promessa de
resultado do Provimento OAB 205/2021, encoding, PT-BR — nunca leu o FAQ.

A rodada com o FAQ visível não produziu nenhum crítico novo, o que é coerente
com as duas rodadas anteriores em que as acusações de promessa eram falso
positivo. Mas o defeito era mudo: **acesso a chave inexistente em dict Python não
levanta erro**. Onde houver `record.get("nome_do_campo")` sobre um schema que
mudou, o mesmo silêncio pode existir.

## 3. Idade em anos entra como prazo na conferência de citação

**Estado: limite conhecido, não resolvido.**

`tools/measure-citation-conformance` já descarta "65 anos **de idade**" e "pena
máxima de dois anos". Não descarta idade escrita sem essas marcas — *"o filho que
complete 21 anos"*, *"o homem se aposenta aos 60"*. São 5 das 7 divergências que
sobraram na última medição, todas falso positivo.

Não é urgente (a ferramenta declara `DIVERGENTE` como fila de leitura, não como
veredito), mas quem for usar a saída precisa saber disso antes de tratar a lista
como defeito.

## 4. Diploma inferido por proximidade: 99,2% é um teto otimista

`tools/measure-citation-diploma-accuracy` mediu a regra contra o gabarito que a
própria língua dá ("art. 1.723 **do Código Civil**"). Acertou 7.728 de 7.787.

**O número não se estende ao resto.** Ele foi medido justamente onde a lei está
escrita logo após o artigo — o caso fácil. As **12.364 citações sem essa forma**
foram decididas por proximidade sem gabarito nenhum, e não há como conferi-las
com o que existe hoje. Cada linha de `data/ops/citation_conformance.jsonl` traz
`diploma_explicito_na_frase` para separar os dois casos; use esse campo.

Um caminho não explorado: resolver "do mesmo Código", "desta Lei" e "do referido
diploma" pelo diploma da citação anterior na mesma página. Foi visto em pelo
menos 3 casos reais.

## 5. Súmulas do STJ: 1.402 citações sem nenhuma forma de conferir

`arquivocidadao.stj.jus.br` responde 200, mas o padrão de URL é irregular e não
foi mapeado. Enquanto isso, toda citação de súmula do acervo é fé — a mesma
situação em que estava o texto de lei antes de `data/legal-corpus/`.

É a maior lacuna de verificação que sobrou. Task #26.

## 6. Canibalização: resolvida de 20 para 5, e o que resta é o slug

**Estado: 80% resolvido; o resíduo tem causa estrutural.**

Medido por `tools/measure-supersession-duplication`: não é plágio (Jaccard de
corpo máximo 0,27), é disputa da mesma consulta.

| | antes | depois da 1ª rodada | depois do restore |
|---|---|---|---|
| pares canibalizando, os dois no ar | 20 | **3** | 5 |
| Jaccard de intenção (máximo) | 0,78 | **0,38** | 0,46 |

**O restore teve custo, e ele precisa ficar registrado.** Com os 34 títulos
trocados, a medição deu 3 pares e máximo 0,38. Devolver os 17 títulos das
páginas protegidas — necessário para não quebrar a cadeia de supersessão —
devolveu 2 pares e subiu o máximo para 0,46. Foi uma troca deliberada:
integridade da cadeia autenticada em vez de dois pontos de similaridade. Quem
retomar precisa saber que esse resíduo é *preço pago*, não trabalho mal-feito.

A correção trocou `title` e `h1` para que cada página anunciasse o ângulo que já
entrega, sem tocar no corpo. Três coisas aprendidas no caminho, todas registradas
nos geradores:

1. **17 das 34 páginas estavam sob supersessão** — e eram justamente as
   "suprimidas" de cada par, o que é óbvio em retrospecto: é o arquivo de
   supersessão que o medidor lê para montar os pares. Editá-las aborta o
   pre-commit, e o gate está certo. Para desfazer a disputa **basta um lado
   mudar**.
2. Restaurar os **valores** não bastou: a linha continuava reprovando com o mesmo
   tamanho e nenhum campo diferente. A causa era **serialização** — `sort_keys`
   contra outra ordem de chaves. Idênticas para quem lê JSON, diferentes para um
   SHA-256.
3. Publicar as 36 páginas **criou dois pares novos**. Toda publicação em lote
   deve remedir canibalização depois.

**O resíduo é estrutural.** Os 5 que sobraram são dominados pelo SLUG, que entra
na medição de intenção e não pode mudar sem quebrar URL publicada:

| | |
|---|---|
| `/telecom-energia/reclamar-na-aneel/` | `/procedimentos/aneel-reclamar/` |
| `/sucessoes/previdencia-sem-beneficiario/` | `/bancario/previdencia-sem-beneficiario-indicado/` |
| `/inpi/registrar-software-inpi/` | `/procedimentos/inpi-registrar-software/` |

Um dos 5 é o falso positivo já documentado (RGPS × regime próprio de servidor).
Resolver os outros 4 exigiria decidir sobre rota — e "redirect como solução" é
proibido pelo `CLAUDE.md`. É decisão de arquitetura de URL, não de conteúdo.

## 6-bis. Diagnóstico original (histórico): canonical cruzado não é opção

Medido por `tools/measure-supersession-duplication`: não é plágio (Jaccard de
corpo máximo 0,27), é disputa da mesma consulta. O padrão dominante é **verbete
de glossário contra página de área com título quase idêntico** — em quatro casos
o slug é literalmente o mesmo:

| | |
|---|---|
| `/glossario/testamento-vital/` | `/sucessoes/testamento-vital/` |
| `/glossario/codicilo/` | `/sucessoes/codicilo/` |
| `/glossario/arrolamento-sumario/` | `/sucessoes/arrolamento-sumario/` |
| `/glossario/usucapiao-especial-urbana/` | `/imobiliario/usucapiao-especial-urbana/` |

**Canonical cruzado está fora:** `publishedmanifest.go:843` exige canonical
auto-referencial e o boot falha (`httpserver.go:247` → `log.Fatal`) se isso for
violado. Ou se muda o código, ou a solução é editorial.

Um par é **falso positivo do medidor** e não deve ser tocado:
`/previdenciario/acumular-pensao-aposentadoria/` × `/servidor/acumulacao-pensao-e-aposentadoria-redutor/`
— RGPS e regime próprio de servidor são regimes distintos, com regras distintas.

## 6-ter. Onde o litígio é alto e a cobertura é rasa (Datajud/CNJ, TJSP)

Medido por `tools/measure-judicial-demand`. Processo ajuizado é demanda
**comprovada** — quem litiga já passou do estágio da dúvida. Descartados os
rótulos que são categoria processual e não tema de consulta ("Objetos de cartas
precatórias", "Pena Privativa de Liberdade", "Leve"), o que sobra é isto:

| assunto | processos | páginas |
|---|---|---|
| Alienação Fiduciária | 1.119.536 | 31 |
| Contratos Bancários | 1.089.711 | **12** |
| Prestação de Serviços | 865.248 | 23 |
| Práticas Abusivas | 787.505 | **14** |
| Bancários | 704.279 | **12** |
| Perdas e Danos | 554.451 | 27 |
| Obrigações | 549.910 | 14 |
| Despesas Condominiais | 470.406 | 17 |
| Expurgos Inflacionários / Planos Econômicos | 462.897 | 13 |
| Cheque | 416.279 | 20 |
| Espécies de Contratos | 412.731 | **6** |

**Contratos bancários é a maior lacuna do acervo**: mais de um milhão de
processos no TJSP e doze páginas. É também faixa comercial pura — o leitor que
procura isso tem problema com contrato assinado, não curiosidade.

Atenção ao ler a coluna "páginas": ela conta por termo distintivo, e a primeira
versão da ferramenta reportou "IPTU: zero páginas" quando existem 39. O número é
indicativo de cobertura, não censo exato.

## 7. As 605 páginas rasas reais não se resolvem com o gerador de reparo

Aprofundar é **criar** conteúdo: adiciona afirmações, que exigem fonte oficial,
que exige proveniência registrada. O padrão de gerador datado com CAS que corrige
um trecho conhecido (`tools/generate-v2-cdc-art26-prazo-repair-20260806`) **não
serve** aqui — usá-lo geraria texto sem fonte em escala, que é exatamente o
`scaled content abuse` que o plano identificou como risco.

O caminho é o pipeline sancionado (fila de revisão → escrita → proveniência →
verificação → commit verificado).

E o alvo não é o número que estava na task: das 1.258 páginas entre 250 e 400
palavras, **653 são glossário (473), súmulas (91) e leis (89)** — formatos curtos
por natureza. Verbete de 399 palavras está certo; inflá-lo para 900 é o defeito,
não a correção. Alvo real: **605**, concentradas em imobiliário (55),
previdenciário (54), servidor (48), INPI (43) e família (38).

---

## Onde estão as evidências

| arquivo | o que contém |
|---|---|
| `data/ops/citation_conformance.jsonl` | uma linha por citação de prazo conferida, com os 4 estados |
| `data/ops/citation_diploma_accuracy.json` | hold-out da atribuição de lei, com os erros |
| `data/ops/supersession_duplication_measurement.json` | os 18 pares, com Jaccard de corpo e de intenção |
| `data/research/judicial_demand_by_subject.json` | volume de litígio por assunto (Datajud/CNJ) |
| `data/legal-corpus/*.json` | 26 diplomas, 8.562 artigos, com URL, data e SHA-256 |
| `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` | o que já mentiu neste repositório, e por quê |
