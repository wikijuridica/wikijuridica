# O que confiar, o que não confiar, e por quê

Documento de continuidade para quem for trabalhar neste repositório. Cada item
custou tempo real de diagnóstico — a lista existe para que ninguém pague duas
vezes pelo mesmo erro.

**A regra que resume tudo:** número de comando não é fato. Antes de agir sobre
um dado do repositório, leia o conteúdo real que ele descreve. Vários checks
daqui já afirmaram, com confiança, coisas falsas.

---

## Por qual ATO se lê este documento (acrescentado em 2026-09-16)

Documento que se procura por **tema** não é procurado: quem vai afirmar um volume não pensa
"vou ler sobre medição". Por isso a entrada aqui é pelo **ato que você está prestes a
praticar**. Se você reconhecer o seu na coluna da esquerda, a seção da direita é leitura
obrigatória antes do comando.

| antes de… | leia |
|---|---|
| afirmar volume, alcance, rastreio, retorno ou citação de bot | §13.1 (`ai_citation_signal_daily.jsonl`), §13.2 (`edge_bot_agents_daily`), §13.3 (`bing_webmaster_daily.jsonl`) |
| publicar número derivado de contagem de linhas de um JSONL vivo | §13.4 (`extracoes_dispositivos.jsonl`), §13.5 (`v2_rewrite_queue.jsonl`) |
| ordenar, priorizar ou cortar por um score | §9 e §13.6 (`risco_superacao.jsonl`) — score que satura não ordena |
| afirmar quando uma página estreou, ou datar qualquer coisa por commit | §13.7 (`first_published_at.json`), §13.9 (`published_manifest.jsonl`) |
| consultar a fila do cérebro por SQL | §13.8 (`data/ai/fila.sqlite`) |
| recusar conteúdo por similaridade, molde, fonte insuficiente ou piso de palavras | §14 — três hipóteses dessa família já foram medidas e **descartadas** |
| propor um LLM como juiz de limiar, ou um canal novo como "alavanca" | §14 — o que já foi tentado e o que a medição devolveu |

O caso concreto de cada armadilha — a data, o número e o prejuízo — fica em
`docs/PRECEDENTES_DAS_ORDENS.md`. Aqui mora o **arquivo**; lá mora a **ordem**.

---

## 1. Comandos e dados que JÁ MENTIRAM

### `v2_publication_severity.jsonl` → campo `public_path`
**Não use.** Ele contém o `intent_id` cru (`/autonomos/acon-b2b-escopo-alterado/`)
em vez do slug publicado (`/autonomos/b2b-escopo-alterado/`). **Zero** dos 9.741
resolvem no disco. Junte sempre por **`intent_id`**.

### Detector de `promessa_oab`
Acusou **46 páginas** num episódio e **29** noutro. **Todas inocentes** nos dois.
O padrão do falso positivo é sempre um destes quatro:
- negação — "sem confundir chance processual com garantia de resultado";
- promessa de terceiro descrita como objeto da análise — página sobre o golpe do
  falso recuperador, onde "garantia de êxito" é listada como sinal de fraude;
- vocabulário técnico — "créditos com garantia real", "garantia irredutível de
  cinco anos" (art. 618 do CC);
- enunciado legal — "a empreitada é voltada a um resultado certo".

Corrigido em 2026-08-06 e **protegido por `tools/check-promise-detector`**, que
roda 13 frases que devem reprovar e 16 que não podem. Se mexer no detector, rode
esse check: ele já pegou um afrouxamento meu durante a própria correção.

### `cmd/check internal-link-mesh-integrity`
Ficou **inexecutável** por meses: `content/pages.json` cresceu para 62 MB e o
loader tinha teto de 16 MB. Falhava antes de auditar qualquer coisa. Não era
falso verde — era um gate que ninguém percebeu que parou de rodar. Teto elevado
para 128 MiB; acima de ~19 mil páginas a leitura precisa virar streaming.

### `publicrelease` → `staging_unsafe_path`
Quando `.release-staging` **não existe**, o erro dizia "caminho inseguro" —
mandando quem lê caçar adulteração onde só falta um pré-requisito. Corrigido
para `public_release_committed_artifacts_promotion_absent`.

### `snapshot-public-release`
Travava **a si mesmo**: tomava `flock` exclusivo no inode de `/opt/wiki` e em
seguida pedia o lease do estoque, que usa `flock` compartilhado no MESMO inode.
Reportava "v2 ingest transaction is already active" sem transação alguma. Por
isso `releases/` nunca existiu. Corrigido com arquivo de lock próprio.

### `measure-supersession-duplication` (esta ferramenta, primeira versão)
Mediu **Jaccard do corpo**, achou 0,27 contra limiar 0,70 e concluiu
"consolidação REFUTADA". **A conclusão estava errada** e quase derrubou um gate
correto. Vocabulário do corpo mede plágio; não mede canibalização. As páginas
tinham redação diferente e **a mesma intenção de busca**. Hoje mede os dois
eixos separados.

> Esta é a armadilha mais cara do repositório: **usar a métrica errada e
> confiar no resultado.** Antes de refutar um gate, confira se sua medição
> responde à mesma pergunta que ele faz.

---

## 2. Onde os dados são confiáveis

| Fonte | Confiança | Observação |
|---|---|---|
| `data/editorial/v2_pages/*.jsonl` | alta | O estoque canônico. É a fonte do conteúdo. |
| `data/editorial/published_manifest.jsonl` | alta | O que está publicado, com `html_sha256` real. |
| `content/pages.json` | alta, mas é ESPELHO | Derivado da publicação; não edite à mão. |
| `data/editorial/v2_superseded/*.jsonl` | alta | Ver a nota abaixo antes de usar: `canonical_shard` **não** aponta para a intenção vencedora. |
| Arquivos de veredito humano | alta no rótulo, **fraca na causa** | O veredito é `REPROVADA:N`, um código sem legenda central. Ver seção 4. |

---

## 3. Verifique SEMPRE o que é servido, não só o que está em disco

Toda a cadeia de integridade histórica comparava **disco com disco**. Em
2026-08-06 medimos: **76% das páginas eram servidas com HTML diferente do
auditado** e nenhum gate via.

Três caches, e cada um mordeu uma vez:

1. `var/on-demand-cache` — respostas do Go. Limpo pelo `deploy-publico`.
2. `open_file_cache` do nginx — **declarado no `nginx.conf` global do projeto
   vizinho `/opt/divorcio`, sem `open_file_cache_valid`**. Servia arquivo velho
   indefinidamente em página com tráfego. Reload gracioso NÃO resolve; só
   restart.
3. Cache de borda do Cloudflare — `tools/purge-edge-cache`, passo 6 do deploy.

**Use:** `tools/check-served-vs-manifest`, `tools/check-static-freshness`,
`tools/check-sitemap-fidelity`, `tools/check-what-bots-see`.

---

## 4. Pendências reais, com o dado já medido

### 18 pares canibalizando, os dois no ar
`tools/measure-supersession-duplication` mede e grava a evidência. Os piores:

| intenção | par |
|---|---|
| 0,78 | `proc-inpi-registrar-software` ↔ `pi-registrar-software-inpi` |
| 0,50 | `gloss-rmi` ↔ `prev-verbete-rmi` |
| 0,50 | `banc-alienacao-fiduciaria-imovel-o-que-e` ↔ `imob-alienacao-fiduciaria-verbete` |
| 0,50 | `gloss-dados-de-criancas` ↔ `lgpd-protecao-criancas-adolescentes-regime` |

A consolidação de 2026-07-15 **acertou o diagnóstico e nunca foi aplicada**: os
registros dizem `publication_allowed: false`, e as 53 páginas estão no ar. Não é
plágio (corpo distinto, Jaccard máximo 0,27) — é o buscador sem saber qual das
duas ranquear.

Decidir entre canonical, fusão ou diferenciação de intenção é escolha de SEO com
impacto real; não faça no meio de outra mudança.

### `canonical_shard` NÃO aponta para a intenção vencedora

Erro meu, registrado para ninguém repetir: li o campo como "a intenção que
sobrevive à canibalização" e abri uma tarefa para consertar "19 registros que
apontam para si mesmos". **Os 19 estavam certos.**

`internal/v2supersessionintegrity/integrity.go:524` exige que o shard canônico
contenha **exatamente um registro ativo com o MESMO `intent_id`**. O registro é
uma lápide na origem, e o ponteiro diz para onde aquela mesma intenção migrou de
shard. Apontar para o próprio `intent_id` é o comportamento exigido — são
exatamente os `trusted_tombstones=19` que o gate reporta como válidos.

Dos 150 registros, o gate considera 137: **118 são `active`** — a consolidação
diagnosticada em 2026-07-15 nunca foi aplicada, e as páginas seguem no ar —, 19
são lápides válidas e 13 são ignorados. Os que "não resolvem" apontam para
shards de nome antigo (`imobiliario.jsonl`, sem número) e estão entre os
ignorados; não são dívida ativa.

**Antes de propor conserto num campo de dado deste repositório, leia o gate que
o valida.** Levei uma tarefa inteira baseada em ler o nome do campo.

### Vereditos humanos sem legenda
133 páginas fora do ar por `REPROVADA:N`. A legenda **não existe em lugar
nenhum**; foi reconstruída lendo justificativas soltas em
`.agents/runtime/tmp_rescue/20260806/tmp/final37.py`:

- `REPROVADA:2` — abreviação corrompida (`"O artigo. 1.606"`, ponto espúrio)
- `REPROVADA:4` — auto-referência editorial no corpo ("A página é informativa…")
- `REPROVADA:5` — erro de citação legal, inclusive numeração sem separador

Só **12 das 133** têm padrão mecânico; as outras 121 precisam de leitura
jurídica. **Escrever essa legenda num lugar central é pré-requisito** para
qualquer tentativa de recuperar as 133 em escala.

### Correção não passa por página sob supersessão
`fam-heranca-entra-na-partilha` está preservada em arquivo de supersessão, e
qualquer edição vira `active_source_changed_without_provenance`, **abortando o
commit**. Corrigi-la exige o canal com proveniência durável (revisão
independente, forward committed ou recut semântico). O gerador de separador de
milhar a mantém numa lista de exclusão documentada.

---

## 4b. Acesso a texto de lei — o que responde e o que bloqueia

Mapeado em 2026-08-06, com User-Agent próprio e identificação do projeto:

| fonte | resultado | serve para |
|---|---|---|
| `planalto.gov.br` | **bloqueia** (conexão recusada / WAF) | — |
| `lexml.gov.br/busca/SRU` | 200, mas devolve **página de verificação de segurança** do Senado | — |
| `normas.leg.br/api/...` | 404 nas rotas testadas | — |
| `legis.senado.leg.br/dadosabertos` | **200, JSON** | matérias e tramitação |
| `dadosabertos.camara.leg.br/api/v2` | **200, JSON** | proposições |
| `in.gov.br` (Imprensa Nacional) | **200** | texto **publicado** no DOU |

O que falta e é o que realmente importa para conferir citação: **texto
CONSOLIDADO** (com as alterações posteriores incorporadas). O DOU dá a
publicação original; os dados abertos dão tramitação. Sem consolidado, conferir
"o art. 27 do CDC fixa cinco anos" exige leitura manual da fonte.

Consequência prática: a conferência de citação em escala **ainda não tem canal
automatizável**. Conferência pontual continua possível — foi assim que o prazo
prescricional do CDC art. 27 foi confirmado nesta sessão.

## 4c. Inferir diploma pelo contexto: medido e reprovado

Tentação óbvia para as 9.256 citações sem diploma: usar o diploma que a própria
página nomeia em outro ponto. **A regra foi validada e erra 38,7%.**

O teste: para cada citação que JÁ tem diploma, esconder o próprio e tentar
inferir pelas demais citações da mesma página. Em 5.079 casos aplicáveis,
acertou 3.113 (61,3%). Os erros mais comuns confundem `lei_especifica` com
`codigo_civil`, `cpc` com `codigo_civil` e `cdc` com `codigo_civil`.

Aplicar isso ao acervo injetaria cerca de 3.900 atribuições de lei erradas.
**Numa página jurídica, atribuir um artigo à lei errada é pior que não nomear a
lei.** Não faça.

## 4d. Fontes que FUNCIONAM (corrigindo o que eu mesmo escrevi acima)

A seção 4b dizia que `planalto.gov.br` "bloqueia". **Estava errado.** Ele recusa
requisição sem os cabeçalhos de um navegador; com `Accept`, `Accept-Language` e
compressão, devolve o texto compilado inteiro. Foi assim que `data/legal-corpus/`
foi montado: **26 diplomas, 8.182 artigos**, e 9.084 citações passaram a ser
conferíveis contra o texto oficial (99,56% dos artigos citados existem).

| fonte | estado | serve para |
|---|---|---|
| `planalto.gov.br` **com headers de navegador** | **200** | texto consolidado de lei |
| `api-publica.datajud.cnj.jus.br` **com a chave pública do CNJ** | **200** | metadados de processo, volume por assunto |
| `arquivocidadao.stj.jus.br` | 200, **mas não serve** | ver 4e-bis |
| `atos.cnj.jus.br/atos/detalhar/` | **200** | atos normativos do CNJ |
| `www2.camara.leg.br/legin` | **200** | segunda fonte de lei |
| `lexml.gov.br/SRU` | challenge de segurança | — |
| `scon.stj.jus.br` | 403 | — |
| `jurisprudencia.stf.jus.br` | recusa conexão | — |

**O 401 do Datajud não era o gate do projeto** — era falta da chave pública que o
CNJ divulga em `datajud-wiki.cnj.jus.br/api-publica/acesso`. E o rótulo
`metadata_only` do registro **está correto, não é rigidez**: a API só entrega
assuntos, classe, órgão julgador, movimentos e `nivelSigilo` — sem partes, sem
peças, sem conteúdo de decisão.

Antes de declarar uma fonte bloqueada, teste com cabeçalhos completos e procure a
credencial pública documentada.

## 4e. Conferir citação legal: o que o corpus e o conferidor sabem e não sabem

Montado em 2026-08-06 e corrigido cinco vezes no mesmo dia, sempre porque
**acusou página correta**. Os bugs valem mais que o resultado, porque quem
reescrever a ferramenta os cometerá de novo.

**Cinco defeitos do extrator do corpus** (`tools/generate-legal-corpus`),
protegidos hoje por `tools/check-legal-corpus-extractor`:

| defeito | efeito |
|---|---|
| artigo com sufixo não indexado | 625 dispositivos (`43-A`, `103-A`, `61-A`…) comparados contra o artigo-base errado |
| `[ºo°]` com `IGNORECASE` | "Art. 103. **O** prazo de decadência" perdia a 1ª palavra |
| referência cruzada lida como cabeçalho | "no art. 110 deste Código" partia o art. 109 ao meio |
| `A rt. 107` (palavra partida por `<b>`) | o art. 107 do CP não existia no corpus |
| artigo transcrito de OUTRA lei | a Lei 14.790/2023 tem **dois** "Art. 32"; o corpus guardava o alheio |

**O `<strike>` do Planalto abre e fecha fora da fronteira semântica** e engole
cabeçalho vigente junto (o art. 18-C da LC 123/2006 perde o dele assim). Por
isso **artigo ausente do corpus NUNCA é acusação** — é falta de cobertura.

**Seis vieses do conferidor** (`tools/measure-citation-conformance`), todos
pegos pelo autoteste de 22 frases reais, todos produzindo acusação falsa:
numeral composto somado errado ("cento e oitenta" → 80); "mensal" lido como
prazo de um mês; imagem retórica ("cada mês que passa"); idade e pena com forma
de prazo; acento (`três` ≠ `tres`); e prazo pertencente a outro artigo da mesma
frase.

**Cobertura real:** de 20.473 citações, só **719** têm prazo conferível. Os
outros 96% caem em `AMBIGUO` — a frase não afirma prazo, ou o diploma não está
no corpus. **Conferência de citação não é medição de qualidade do acervo**; ela
cobre uma fatia estreita e é honesta sobre isso.

**Resultado de 2026-08-06:** 7 divergências, das quais **2 reais** (prazo de 90
dias do CDC atribuído ao art. 18, sendo do art. 26, II — corrigidas por
`tools/generate-v2-cdc-art26-prazo-repair-20260806`) e 5 falso-positivo por
idade em anos. **Limite conhecido e não resolvido:** idade escrita sem a
expressão "de idade" ("o filho que complete 21 anos") continua entrando como
prazo.

**A regra que saiu daqui:** quando a ferramenta e a página divergem, leia o
dispositivo antes de decidir quem errou. Nas 23 divergências da primeira
medição, **21 eram da ferramenta**. E uma busca na web chegou a afirmar o
contrário do corpus sobre o art. 32 da Lei 14.790 — quem decidiu foi o HTML do
Planalto, que tinha os dois artigos.

## 4e-bis. Súmula: 1.214 citações e NENHUM canal para conferir

**Corrigindo a seção 4d, que eu mesmo escrevi errado.** A tabela dizia
`arquivocidadao.stj.jus.br` → 200 → "texto de súmula do STJ". O código HTTP é
200 mesmo — e a página **não tem o enunciado**. É um sistema de descrição
arquivística (AtoM); `/index.php/sumula-479` devolve apenas os campos "Termos
hierárquicos / equivalentes / associados", todos com o valor "Súmula 479".

Foi o erro exato contra o qual este documento existe: **anotei o código de
resposta em vez de ler o conteúdo.**

O acervo cita **1.214 súmulas em 613 páginas**, 468 distintas — STJ 325, TST
158, STF 49, e **668 (55%) sem nomear o tribunal na frase**. Testado em
2026-08-06, com User-Agent próprio e cabeçalhos de navegador:

| fonte | resultado |
|---|---|
| `arquivocidadao.stj.jus.br/index.php/sumula-N` | 200, só taxonomia — sem enunciado |
| `dadosabertos.web.stj.jus.br` | 200; **21 datasets e nenhum de súmula** (precedentes qualificados e espelhos de acórdão, sim) |
| `scon.stj.jus.br/SCON/sumanot/` | 403 |
| `www.stj.jus.br/.../Sumulas` | sem resposta |
| `portal.stf.jus.br` e `jurisprudencia.stf.jus.br` | sem resposta |
| `www.tst.jus.br/sumulas` | 302 sem destino útil |
| `lexml.gov.br/urn/...:sumula:...` | 200 com 1 KB, sem enunciado |

**Conclusão: a citação de súmula continua sendo fé.** É a maior lacuna de
verificação do acervo — a mesma situação em que estava o texto de lei antes de
`data/legal-corpus/`, e ali a saída foi descobrir que o Planalto só exigia
cabeçalhos de navegador. Aqui não há equivalente conhecido.

Quem retomar: `arquivocidadao` tem a súmula como *termo de indexação* de
documentos digitalizados; talvez os documentos vinculados ao termo tragam o
enunciado. Não foi explorado.

## 4f. A fila de escrita carrega um CAS — a ordem das operações importa

**Custou 1,57 milhão de tokens e zero página.** Em 2026-08-07 disparei o
workflow de escrita com 17 lotes; os 17 agentes abortaram no preflight com:

    CASMismatch: "portfolio ou catálogo de fontes mudou depois da fila"
    tools/generate_v2_review_queue.py:2033, em derive_writing_source_resolution

`scripts/workflows/writing-mass-todo.js` embute um snapshot CAS do portfólio e
do catálogo de fontes. Eu gerei a fila, **depois** rodei um resolvedor que
adicionou 38 entradas ao catálogo e reescreveu 45 referências de portfólio, e só
então disparei o workflow.

O gate está certo e não se afrouxa: sem ele o redator escreveria a página contra
uma fonte que já não é a da intenção.

**A ordem é:** catálogo e portfólio primeiro → `ops/relaunch-writing.sh` →
workflow. **Enquanto o workflow roda, não se toca em catálogo nem em portfólio.**

## 4g. API pública do normas.leg.br: existe, e como achá-la

Eu havia registrado que não havia canal para norma federal além do Planalto.
Errado. `normas.leg.br` tem API pública **sem credencial**, e ela se documenta:

    GET /v3/api-docs                                → OpenAPI completa
    GET /api/public/metadados/gerais?urn=<urn lexml> → JSON-LD Legislation
    GET /api/public/binario/<uuid>/texto             → o TEXTO (CC-BY 4.0)
    GET /api/public/legislation-types                → as 77 espécies cobertas

**Como foi achada, porque o método vale mais que o endereço:** a SPA declara
`publicApiUrl: "/api/public/"` no bundle. Os caminhos adivinhados davam 404 —
mas o 404 vinha em JSON no formato do Spring Boot, o que provava haver API
atrás. Daí `/v3/api-docs`.

Dois defeitos dela, contornados sem adivinhação:
- o `contentUrl` que ela devolve **omite o segmento `/public/`** e dá 404; o
  caminho que serve é o do OpenAPI;
- o binário responde **406** a `Accept: application/json` — ele serve HTML.

A URL do binário passa no gate (https, `.leg.br`, path específico, sem query nem
fragmento). A de navegação (`normas.leg.br/?urn=…`) não passa, e com razão.

**Cobertura:** lei, lei complementar, decreto, decreto-lei, emenda
constitucional, medida provisória e decreto legislativo federais, mais acórdãos
do STF em controle concentrado. **Não cobre súmula nem resolução de agência.**

**Critério de aceitação:** ela responde 200 mesmo para URN inexistente, com
`name: null`. O critério é o campo, nunca o código HTTP.

## 4h. Intenção e página NÃO entram no mesmo commit — a autoridade é o pai

**Custo medido: quatro tentativas de commit, cada uma com o pre-commit completo,
e o índice estava íntegro o tempo todo.**

`tools/check-v2-finalized-commit` recusa shard de `data/editorial/v2_pages/`
cujo `intent_id` não tenha exatamente uma linha em `data/editorial/portfolio_v2/`.
Isso está claro na mensagem. O que **não** estava é qual portfólio conta:

```python
# tools/check-v2-finalized-commit:1341
members = portfolio_membership(old)     # <- o commit PAI, nunca o candidato
```

e o comentário três funções acima diz por quê:

> *"The parent portfolio is deliberately the membership authority. A candidate
> cannot add its own portfolio row and consume it in the same transaction."*

**A regra é boa e não deve ser afrouxada:** ninguém fabrica a demanda e o
conteúdo no mesmo movimento atômico. Declara-se por que a página deve existir;
só depois se escreve. O campo `distinct_because` de cada intenção é a defesa
anti-template na camada da demanda — recusa a permutação antes de alguém pagar
tokens para escrevê-la.

**A ordem correta são DOIS commits:**

```bash
./tools/check-v2-portfolio-pairing              # confere em <1s, sem build
git commit -F <msg> -- data/editorial/portfolio_v2   # 1) a intenção
git commit -F <msg> -- data/editorial/v2_pages       # 2) a página
```

**Por que isso enganou:** conferir o pareamento no disco — ou até sobre o
próprio `git write-tree` do índice — dá **1:1 perfeito**, e a recusa passa a
parecer defeito do gate. Não é: o conteúdo está certo, o que falta é um commit
antes. Nenhuma checagem local reproduz a recusa, porque a diferença não está no
que você tem, está em **onde já está**.

Mudanças aplicadas em 2026-08-20 para o erro não se repetir:

- a mensagem do gate passou a dizer o caso (ausente × duplicado), a regra e os
  **dois comandos na ordem** — `membership_hint`, usada nos três pontos que
  emitiam a recusa. Nenhuma verificação foi afrouxada; ela só passou a explicar;
- nasceu `tools/check-v2-portfolio-pairing`, read-only, que responde em menos de
  um segundo e **espelha a regra do gate** — inclusive tolerando tombstone
  (`skipped: true`) sem linha de portfólio. Espelhar importa: na primeira
  execução ela acusou 6 páginas de `/aereo/` "sem intenção" que o gate aceita,
  porque são órfãs tombstonadas com
  `skip_reason: orphan_no_portfolio_join_semantic_duplicate_of_active_canonical`.
  **Verificador mais severo que o gate manda consertar o que não está quebrado.**

## 4i. `\b` do Go é ASCII — e ele corta palavra em português

**Medido em 2026-08-20**, num título que foi publicado. A regex

```go
regexp.MustCompile(`(?i)\b(é|são|deve|...)\b`)
```

foi escrita para achar o verbo que abre o predicado numa tese do STJ. Ela casou
**dentro** de `"empréstimo"`.

**Por quê.** O `\b` do RE2 (e do PCRE sem `(*UCP)`) é definido sobre a classe
ASCII `[0-9A-Za-z_]`. O `é` é U+00E9, dois bytes em UTF-8, e **não** pertence a
essa classe. Logo existe uma fronteira de palavra entre o `r` e o `é` de
"emp**r**-**é**stimo", e `\bé\b` casa ali com folga.

**O dano.** O corte saiu como `Questão referente ao empr` — cortado no meio da
palavra, pela própria função que existia para não cortar. Um `\b` numa lista de
verbos em português é uma bomba-relógio: quanto mais acentuada a palavra
procurada, mais provável o falso casamento.

**A regra:** em português, **não use `\b` para casar palavra inteira**. Compare
por token — `strings.Fields` e lookup em `map[string]struct{}` —, que não tem
fronteira para errar. Se a regex for inevitável, delimite explicitamente com
`(^|[^\p{L}])` … `($|[^\p{L}])`, nunca com `\b`. O mesmo vale para `\w`, `\W`,
`\s` em contexto de letra acentuada.

Onde isto está resolvido no repo: `internal/titulojuridico.verbosDeCorte` é um
conjunto de tokens, e o comentário dele carrega este precedente.

**Parente próximo, também medido:** `internal/textotruncado` teve de separar
*prova de corte* de *suspeita* porque a regra de delimitador desbalanceado
acusou 103 blocos do acervo — todos com aspas ímpares vindas do **texto oficial
citado** (o STJ abre aspa reta dentro de aspa curva e não fecha). Ali o detector
estava certo sobre o fato e errado sobre a conclusão: "consertar" a pontuação de
um acórdão é adulterar citação, e a licença do STF condiciona a reprodução a ser
*sem alteração do conteúdo*.

**E o corte que nenhum detector de forma vê:** o campo `materia` do Informativo
do STF é truncado pela fonte em 79–80 caracteres, no meio da palavra —
`"Autonomia Financeira e Adminis"`, `"Tempo de Serv"`. Não termina em conectivo
nem em hífen: **parece uma palavra**. A guarda é de domínio, não de forma —
`materiaSaneada` descarta o último segmento quando o campo bate no limite.

## 4j. "A rota responde 200" NÃO prova que o conteúdo está atual

**Medido em 2026-08-20, em produção.** Depois de reescrever 419 títulos, o
publicador imprimiu:

```
sem divergencia: o processo ja serve o manifesto do disco.
```

Era falso. O `tools/reload-wiki-server` sondava cada rota com
`markdown_responde` e perguntava **só** `status == 200`. Isso detecta rota
**nova** e é cego para conteúdo **alterado**: título corrigido numa rota que já
existia responde 200 com o texto velho.

**Por que importa mais do que parece.** O nginx serve o HTML estático de
`public/` e estava correto. Mas o **markdown gêmeo, a busca, o MCP e o A2A**
saem do processo Go, que seguia com o `pages.json` antigo em memória. O único
público que recebia o título desatualizado era o dos **agentes de IA** — o
público que este portal quer alcançar. Medido antes da correção:

```
MCP buscar_paginas "Súmula 560"
   → "Súmula 560 do STJ: Cinge-se o debate trazido nos autos em sa…"   (velho)
disco / nginx
   → "Súmula 560 do STJ: Indisponibilidade de bens e direitos"          (novo)
```

E o restart nunca acontecia, porque a própria sonda dizia que não precisava.

**A regra:** sonda de frescor compara **conteúdo**, nunca existência. Hoje
`reload-wiki-server` compara o título servido com o do disco.

**O campo certo é `heading`, não `title`.** Os dois existem em
`content/pages.json` e são diferentes **por desenho** — `title` respeita o teto
de 65 caracteres do `<title>`, `heading` vai até 70 e é o que vira `<h1>` e a
primeira linha do markdown. A primeira versão da correção comparou com `title` e
acusou divergência em página correta: `/jurisprudencia/stj-tema-898/` tem title
terminando em "atualização monetária" e heading seguindo "…nas indenizações".
Mesma família do erro catalogado em §4 e em `[[medicao-chaves-que-enganam]]`.

## 4k. `data/corpus/jurisprudencia/stj-espelhos/` — ementas de acórdão do STJ

**Fonte:** os dez datasets `espelhos-de-acordaos-*` do CKAN de dados abertos do
STJ (`https://dadosabertos.web.stj.jus.br/dataset`), um por órgão julgador —
Corte Especial, três Seções e seis Turmas. Cada dataset publica **um arquivo
JSON por mês**, nomeado pelo último dia do mês (`20250731.json`). A Primeira
Turma tinha 50 arquivos mensais em 2026-09-08, cobrindo de 2022-05 a 2026-06.

**Base legal.** Decisão judicial não é obra protegida (Lei 9.610/98, art. 8º,
IV), e o ato processual é público (CPC art. 189; CF art. 5º LX, art. 37 *caput*
e art. 93 IX). Sobre isso, o próprio STJ declara licença aberta na página do
dataset — a âncora `rel="dc:rights"` traz "Creative Commons Atribuição". O
coletor confere essa declaração a cada execução e **aborta se ela sumir**:
colher texto oficial sem a licença que o tribunal publica é colher sem
proveniência.

**O que o espelho traz:** `ementa` integral (média de 1.412 caracteres, máxima
de 3.932 na amostra de julho de 2025), o dispositivo do acórdão (campo
`decisao`), relator, órgão julgador, sigla e descrição da classe, número do
processo e do registro, data de julgamento, data de publicação no diário,
`referenciasLegislativas` no formato REPLEG, jurisprudência citada e tema.

**O que ele NÃO traz, e por que os campos saem vazios:**

- **Inteiro teor.** O espelho vai até o dispositivo, nunca ao voto. Por isso
  `inteiro_teor` e `inteiro_teor_url` saem vazios: inventar uma URL de inteiro
  teor que a fonte não publica seria proveniência falsa. O canal de inteiro teor
  do STJ existe — é o dataset
  `integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica`, diário,
  com `metadados<AAAAMMDD>.json` e `textos<AAAAMMDD>.zip` — e foi medido em
  2026-09-08: 4.537 registros de metadado **sem ementa** contra 31 inteiros
  teores no zip do mesmo dia. Rendimento útil de ~31/dia, contra ~1.200
  ementas/mês deste canal.
- **Nível de sigilo.** O espelho não tem o campo, e a razão é estrutural:
  processo em segredo de justiça não é publicado no Diário, logo não chega ao
  espelho. `nivel_sigilo` sai **nulo**, não zero. Zero afirmaria "público por
  declaração da fonte", e a fonte não declara nada.

**O que o filtro consegue e não consegue detectar.** `stjacordaos.MotivoBarrado`
barra por marcador textual de segredo de justiça e por identificador pessoal
(CPF, CNPJ, título de eleitor) que escape para a ementa. Ele **não** barra por
assunto: acórdão que cite o ECA é precedente público sobre direito da criança, e
suprimi-lo seria a super-supressão que o contrato proíbe. Nos 40 acórdãos reais
do `testdata`, zero foram barrados — o teste de falso positivo veio antes do
teste de acerto.

**Cursor e ritmo.** `cursor.json` guarda, por dataset e competência, o ETag, o
Last-Modified, o sha256 da fonte e a contagem gravada. Ele é escrito **a cada
lote**, não ao final: com Crawl-Delay 10, uma varredura dos dez datasets leva
mais de uma hora, e cursor salvo só no fim faria a execução seguinte rebaixar a
fonte de novo pelo que já tinha. A execução é limitada por `--max-recursos`
porque `run-go-cmd-cached` recusa comando pesado acima de 1.800 s; aumentar
timeout no lugar disso seria mascarar performance.

### Duas armadilhas que já custaram dado nesta camada

**O teto de registros truncava o mês e o cursor mentia.** Medido na primeira
coleta de produção, em 2026-09-08: `--max-registros 200` contra o
`20220531.json` da Primeira Turma, que tem 408 acórdãos, gravou 200, marcou a
competência como coletada e perdeu 208 em silêncio. O teto agora decide apenas
se o **próximo** arquivo começa; arquivo começado vai inteiro. A correção veio
com o teste `TestColetaNaoTruncaArquivoMensalPeloTetoDeRegistros`.

**Mês sem registro gravável derrubava a coleta.** Recesso, mês sem acórdão
publicado ou mês inteiramente barrado produzem lote vazio, e o hash de arquivo
inexistente virava erro fatal no primeiro mês vazio da série. O manifesto agora
registra o lote vazio com o hash da **fonte**, que é o que prova que o mês foi
lido.

## 5. Como corrigir conteúdo, sem exceção

Sempre por **gerador datado** com: lease de época (`tools/v2_stock_epoch`), lock
exclusivo, CAS pelo sha256 da linha viva, CAS por trecho (exatamente uma
ocorrência), escrita atômica com fsync, `word_count` recalculado pela fórmula do
ingest, demais linhas byte a byte, e idempotência comprovada rodando duas vezes.

Molde: `tools/generate-v2-prescricao-cdc27-repair-20260806`.

**E todo detector novo nasce com teste de falso positivo sobre amostra real.**
Nesta sessão o teste pegou erro em três detectores diferentes — inclusive nos
meus, depois de eu ter certeza de que estavam certos.

## 6. `data/ops/eventos/` — o evento unificado humano + bot

Gerado por `tools/generate-evento-unificado` (mandato AI-first, §7). Uma linha
por `(dia, página)` em `eventos-AAAA-MM-DD.jsonl`, mais uma linha agregada
`path:"_dia"`, e um `cursor.json` que marca até onde cada dia já fechou.

**O que É**: cruza `data/ops/access/access-AAAA-MM-DD.jsonl` (ledger do
PROCESSO GO, não o do nginx) com a série de borda saneada
(`edgetelemetry.serie_saneada`) e com `clarity_insights_daily.jsonl`, usando
`tools/botagents.agente_de` como identidade única de agente (a mesma chave que
`edge_bot_agents_daily.agent_key`).

**O que NÃO é**:

- **Não tem GA4.** Não existe coletor da GA4 Data API neste repositório nem
  credencial em `.env.local` (só `CLOUDFLARE_*` e `WIKI_CLARITY_API_TOKEN`).
  Toda linha `_dia` traz `ga4: {"disponivel": false, "motivo": "..."}` —
  verdade declarada, nunca zero fingindo medição. Os eventos que a página
  emite (`whatsapp_click`, `fonte_oficial`, `indice_click`,
  `relacionado_click`, `busca_interna`) só são observáveis no painel do GA4
  até um coletor existir.
- **A borda não tem `path`.** `edge_bot_agents_daily.jsonl` é por
  `(dia, agent_key)`, sem URL — por isso `borda_por_agente` só entra na linha
  `_dia`, nunca na linha por página.
- **Aquecimento e sonda ficam fora da conta.** Linha com `warming:true` ou
  `bot_simulation:true` nunca soma em `requisicoes` (mesma regra de
  `accessledger.linhas_saneadas`) — e por isso a contagem por página deste
  arquivo é ESPARSA para tráfego real: a maior parte do acervo é servida pelo
  nginx direto do disco e nunca chega ao processo Go que este ledger mede.
  Medido em 2026-09-07: das 25.184 linhas do dia, 20.169 eram sonda interna de
  paridade (`bot_simulation:true`), e só 2 eram bot valioso externo real.
- **`pct_markdown_da_pagina` não adivinha o path da gêmea.** A gêmea Markdown
  às vezes tem URL própria (`/familia/x/index.md`) e às vezes é servida por
  negociação de `Accept` na MESMA URL — medido em 2026-09-07,
  `/jurisprudencia/stf-adi-7666/` teve linhas `route_class:"page"` e
  `route_class:"markdown"` com o path idêntico. Por isso o cálculo conta,
  DENTRO do mesmo `path`, a fração de hits que vieram como `"markdown"` contra
  `"page"`, em vez de tentar montar o path da gêmea por convenção de string.
- **`agentes_de_ia` é um conjunto curado, não a categoria "search" inteira de
  `tools/botagents`.** Reusa a separação já revisada em
  `tools/measure-ai-citation` (tabela `CAMADA`): os crawlers específicos de IA
  (citação, fetch ao vivo, treinamento). Buscador clássico (Googlebot,
  Bingbot, Applebot, DuckDuckBot, YandexBot) fica de fora de propósito.

## 7. `data/ai/grafo.sqlite` — o grafo de conhecimento jurídico v1

Gerado por `tools/generate-grafo-juridico` (mandato AI-first, §3 camada 1 e
§12 P1). É um **índice derivado**: nunca é a fonte de verdade de nada, sempre
regenerável a partir de quatro arquivos que já existem no acervo, e o
gerador só lê — nunca escreve em `content/`, `data/editorial/` nem
`data/source-snapshots/`. `tools/consultar-grafo` é a ferramenta de leitura
(por chave exata ou termo via FTS5); é a base da futura ferramenta MCP
`grafo(entidade)`, hoje só em Go.

**De onde vem cada nó e cada aresta** (medido sobre o acervo inteiro em
2026-09-08, v1.1 com a fonte 5 de acórdãos: 14.473 nós, 149.820 arestas,
39,6 MiB de `grafo.sqlite`, 17,7 s de geração — 3,0 s para montar o grafo em
memória, 11,4 s para gravar o sqlite, 2,4 s para o segundo artefato
`grafo_vizinhanca.jsonl`. Estado anterior, v1, registrado para referência:
13.575 nós, 148.571 arestas, 36,8 MiB, 9,7 s):

| Nó/aresta | Fonte | Contagem medida |
|---|---|---|
| `pagina` (chave=path) + `area` + `da_area` | `data/editorial/published_manifest.jsonl` | 10.141 páginas, 32 áreas, 10.141 arestas |
| `dispositivo` (chave=URN com `!art…`) + `cita` (página→dispositivo) + `pertence_a` (dispositivo→norma) | `content/legal_cocitation_index.jsonl`, campo `percursos[].urn`/`rotulo` | 860 dispositivos, 7.234 `cita`, 860 `pertence_a` |
| `cocitada_com` (página↔página, peso = nº de dispositivos citados em comum, uma direção só) | derivado do mesmo arquivo, agregando os citantes de cada `urn` | 127.921 arestas |
| `norma` (chave=URN sem `!`) | `data/source-snapshots/manifest.jsonl` (as que o oráculo já coletou) **união** com as URNs-base citadas por alguma página mas nunca coletadas **união** com as URNs citadas por algum acórdão do STJ mas nunca coletadas | 162 normas (126 de página/oráculo + 36 órfãs só citadas por acórdão; rótulo vem do texto real com que uma página a citou — "Código Civil, art. 421" vira rótulo "Código Civil" — ou, faltando isso, é formatado a partir da própria URN: "Lei nº 15.040/2024") |
| `sumula` (chave=`sumula:<tribunal>:<numero>`) + `julgado_por` (sumula→tribunal) | idem, linhas com `tipo:"sumula"` (só STF nesta base) | 67 súmulas |
| `tema` (chave=`tema:<tribunal>:<tipo>:<numero>`) + `julgado_por` (tema→tribunal) | `data/source-registry/stj_precedentes_qualificados.jsonl` (CSV oficial CC-BY do STJ) | 2.347 temas (2.384 linhas — 37 colapsam por par `(tipo,numero)` duplicado no CSV) |
| `revoga` (norma→norma, origem = quem revoga) | `revogado_por` de `manifest.jsonl`, texto livre resolvido por gramática fechada (tipo de norma + número) **contra URN já presente no grafo** | 1 aresta (só a Lei 14.382/2022 revogando parte do Código Civil resolve — as demais leis revogadoras citadas em texto livre nunca foram coletadas pelo oráculo, e o gerador não inventa nó para uma delas caber) |
| `acordao` (chave=`acordao:STJ:<id_fonte>`) + `julgado_por` (acordao→tribunal) + `cita` (acordao→norma, hoje sempre norma — ver abaixo) | `data/corpus/jurisprudencia/stj-espelhos/registros-*.jsonl` (v1.1, 2026-09-08; espelhos oficiais da Primeira Turma do STJ, dados abertos, Creative Commons Atribuição) | 862 acórdãos, 862 `julgado_por`, 387 `cita` (295 dos 862 acórdãos — 34,2% — têm ao menos uma URN em `dispositivos_citados_urn`; das 70 URNs distintas citadas, 36 nunca tinham sido coletadas antes e viraram nó `norma` órfão) |

**Armadilha real do `manifest.jsonl` que o gerador teve que absorver**: a
maioria das 11.317 linhas é **por artigo** (`dispositivo:"art_5"`, não
`""`), e **2.309 das 6.675 chaves `(urn_lex, dispositivo)` têm linha
duplicada de verdade** — a mesma URN+dispositivo aparece duas vezes, uma
com `revogado_por` vazio e outra preenchida, ou com `content_sha256`
diferente por recoleta em data posterior. A "representante" de cada norma
(usada para `vigencia_status` e `tipo_norma` do nó) é a linha de
`dispositivo` vazio **mais recente por `fetched_at`** — pegar a primeira
linha do arquivo, sem esse critério, faria o nó da norma carregar um
`vigencia_status` de uma coleta velha mesmo quando uma coleta mais nova já
está no mesmo arquivo.

**O que o grafo v1 NÃO tem, com todas as letras** (não é lacuna escondida —
é ausência de coletor, e popular essas arestas por adivinhação seria
inventar dado):

- **`supera` e `impactada_por` ficam vazias.** O STJ traz
  `numero_repercussao_geral_stf` em 354 dos seus 2.384 registros — um
  número de Repercussão Geral do STF que o tema está vinculado —, mas não
  há coletor do LADO do STF para esse número (nenhum metadado, nenhuma URN,
  nenhum acórdão). Criar um nó `tema:STF:...` só com um número solto, sem
  nenhum outro dado, seria inventar entidade a partir de metade da
  evidência; a aresta fica de fora até existir um coletor de Repercussão
  Geral do STF.
- **`altera` e `aplica` também ficam vazias.** Nenhuma das quatro fontes
  carrega uma relação explícita de "norma A altera norma B" (fora da
  revogação) nem "página aplica norma X" além da citação já coberta por
  `cita`; popular qualquer uma delas exigiria inferir por proximidade de
  texto, o que o contrato deste gerador proíbe.
- **Súmula/tema → dispositivo (`cita`) fica vazia.** Nem os 67 enunciados
  de súmula do STF (lidos do próprio blob do oráculo) nem as 2.384 linhas
  de temas do STJ trazem uma URN LexML embutida no texto — só prosa
  ("Súmula 44/STJ", "Lei 9.494/1997, art. 1º-F..."). Extrair a URN dali
  seria reconhecimento de entidade em texto livre, e o contrato deste
  gerador só cria aresta quando a URN já está literalmente no dado.
- **Não há inteiro teor de acórdão, mesmo depois da fonte 5 (atualizado
  2026-09-08).** O espelho do STJ traz `ementa` (citação identificada,
  DEC-032, com `base_legal` registrado no nó `acordao`), mas `inteiro_teor`
  e `inteiro_teor_url` vêm sempre vazios nos 862 registros medidos — o
  coletor não tem acesso ao texto integral do voto. Isso continua
  impedindo `supera` e `impactada_por` de verdade: sem o voto completo não
  há como saber se um acórdão supera outro, só que ambos existem.
- **`dispositivos_citados_urn` do STJ é granularidade de NORMA, nunca de
  artigo — medido, não suposto.** Das 70 URNs distintas citadas pelos 862
  acórdãos, **nenhuma** carrega o sufixo `!art…`; o coletor de hoje
  normaliza a referência legislativa bruta ("LEG:FED LEI:008987 ANO:1995
  ART:00011") até o nível de norma e descarta o `ART:`. Por isso `acordao
  -cita->` aponta sempre para um nó `norma`, nunca `dispositivo`, nesta
  versão do dado — o gerador já trata corretamente o dia em que a URN vier
  com artigo (cria `dispositivo` + `pertence_a` pela mesma função
  `norma_base_de_urn` que separa dispositivo de norma na fonte 1), mas essa
  rota só é exercitada por um registro hipotético no teste, nunca pelo
  corpus real ainda.

**`data/ai/grafo_vizinhanca.jsonl` — o segundo artefato, para o servidor Go
(2026-09-08).** Uma linha por nó (mesma chave natural do sqlite), com
`{"chave","tipo","rotulo","atributos","vizinhos":[...]}` — cada vizinho traz
só `aresta`, `direcao`, `chave`, `tipo`, `rotulo` e `peso`, nunca os
`atributos` do vizinho (isso é o que mantém o arquivo em 12,1 MiB para
14.473 linhas, bem abaixo do teto de 15 MB). Serve para o `internal/`
carregar a vizinhança inteira em memória sem round-trip de sqlite por
requisição de agente. **Duas exclusões deliberadas, não omissão**:
`cocitada_com` fica sempre fora (o Go já mantém a co-citação em memória por
outro artefato — incluir aqui triplicaria o arquivo, já que são 127.921 das
149.820 arestas) e `da_area` de **saída** de página fica fora (é redundante
com `atributos.area`, que a própria linha da página já carrega); a mesma
aresta `da_area`, vista do lado da área, continua aparecendo como vizinho
de entrada. `grafo_manifest.json` registra caminho, sha256, tamanho e
número de linhas desse artefato ao lado dos `fontes` do sqlite.

`tools/test_grafo_juridico.py` cobre isso com fixture real pequena (30
linhas de cada fonte principal, incluindo os dois casos de `revogado_por` —
um que resolve, outro que não — e a colisão de `(tipo,numero)` duplicada do
STJ) e prova por mutação que quebrar a separação `urn.split("!")[0]`
(dispositivo→norma) derruba a suíte inteira, não só o teste que a nomeia. A
fixture de acórdãos (`stj_espelhos_sample.jsonl`, 6 registros REAIS do
mesmo corpus) prova nó `acordao`, aresta `cita`/`julgado_por`, a norma
órfã criada por citação e o formato de `grafo_vizinhanca.jsonl`; o ramo
dispositivo+`pertence_a` a partir de acórdão é provado à parte, com um
registro construído à mão, porque o corpus real ainda não produz URN de
artigo (ver acima).

**Fonte 6 (2026-09-08): `data/ai/extracoes_dispositivos.jsonl`**, o que o cérebro
extraiu por LLM (`internal/cerebro/extracao.go`) dos acórdãos sem referência
estruturada. Entra só o item com `urn` — LexML provada pelo parser ou
`sumula:<TRIB>:<n>` — e só para acórdão que a fonte 5 já trouxe (acórdão fora do
grafo é descartado e contado, nunca inventado); a última linha por `chave`
vence porque o cérebro reprocessa e apende. A aresta guarda `fonte` =
`data/ai/extracoes_dispositivos.jsonl` e, na evidência, o `texto_citado`
literal, o modelo e os hashes do prompt e do texto, então dá para separar o que
veio do parser do que veio do modelo. Medido na primeira ingestão: 31 registros,
16 acórdãos, 23 itens com URN, 2 sem, 0 fora do grafo; `grafo_manifest.json`
traz essas contagens em `extracoes_llm`. A fixture
`extracoes_dispositivos_sample.jsonl` (3 linhas) prova a última-linha-vence, o
descarte do acórdão desconhecido e a proveniência.

## 8. `data/ai/propostas_reescrita.jsonl` — a fila de propostas de reescrita (P2)

Gerado por `tools/generate-propostas-reescrita` (mandato AI-first §12, P2:
"primeira fila de reescrita com 100 propostas justificadas"). Cruza três
fontes já descritas neste documento — o evento unificado (seção 6), a
severidade de publicação (`data/editorial/v2_publication_severity.jsonl`) e
o grafo jurídico (seção 7) — com `content/pages.json` e o
`published_manifest`, para apontar página+motivo com pelo menos um número
medido em `evidencia`. Medido em 2026-09-08: 8,25 s para as 10.141 páginas
publicadas, 7.057 candidatas antes do teto, 100 escritas.

**O que ISTO NÃO É.** Não é fila aprovada nem ordem de execução: é proposta
com evidência, para o pipeline editorial (CLAUDE.md §5) decidir. Nenhuma
linha vira `content/pages.json`, `public/` ou `published_manifest` por conta
própria — quem aplica é sempre o gerador datado com CAS da cadeia editorial,
nunca edição manual de JSONL (campo `aplicar_por`, literal em toda linha).
`publicacao` também é literal por linha: passa pela cadeia do §5, e só leva
`--ressemear` se a correção mudar markup, nunca só o texto (matriz do §6 do
`CLAUDE.md`).

**A janela de 3 dias de eventos é pouca, e isso está medido, não
escondido.** `data/ops/eventos/` só tinha `eventos-2026-09-06.jsonl` a
`eventos-2026-09-08.jsonl` no dia desta geração — `--dias 7` pede sete, o
gerador lê os que existem e registra `janela_dias_lidos` na evidência de
cada proposta de demanda. Nessa janela, **nenhuma página real ultrapassou o
limiar de `agentes_leem_humanos_nao`** (≥3 requisições de agente de IA E
≥60% do tráfego da página) — só 10 páginas tinham tráfego registrado no
período inteiro. Isso é o portal ainda cedo no mandato B2A, não um bug do
gerador: a fila vai ficar mais rica em `agentes_leem_humanos_nao` conforme
`data/ops/eventos/` acumular dias e conforme MCP/`/api/v1`/gêmea Markdown
ganharem tráfego de agente real.

**GA4 continua ausente** (mesma armadilha da seção 6): a evidência de
demanda vem só do log de borda/origem via `evento_unificado_v1`, nunca de
evento de negócio (`whatsapp_click`, `busca_interna`) — esses só existem no
painel GA4, sem credencial configurada neste repositório.

**Por que a fila de 100 saiu dominada por um único motivo.** A fórmula de
prioridade (documentada no código, `PESO_MOTIVO` +
`demanda_agentes_normalizada`) dá peso 0,85 a
`precedente_disponivel_nao_citado` — citação legal mal atribuída é P1
permanente (CLAUDE.md §5) — contra 0,65/0,60/0,55 dos motivos de debito
editorial genérico. Como a esmagadora maioria das 10.141 páginas não tem
nenhum dado de tráfego na janela (demanda normalizada = 0 para quase todo
mundo), a prioridade de quem dispara `precedente_disponivel_nao_citado`
(4.317 candidatas) fica empatada em 0,51 e vence o corte de 100 por ordem
alfabética de path — não é uma falha do critério, é o resultado correto de
priorizar risco jurídico sobre polimento editorial quando a demanda ainda
não diferencia as páginas. Isso muda sozinho assim que a coleta de tráfego
de agente amadurecer.

**`precedente_disponivel_nao_citado` só dispara com dupla checagem
negativa**, e as duas são obrigatórias: o acórdão do grafo precisa ter
`ementa` não vazia (860 nós `dispositivo` do grafo se ligam a normas com
acórdão do STJ associado, mas nem todo acórdão tem número de processo
extraível do `rotulo` — quem não tem, é descartado da evidência, nunca
tratado como "já citado"), e a página não pode conter nem os dígitos do
número do processo nem a string "classe + número" (ex. "REsp 1953626"), em
título, resumo, heading, corpo ou FAQ — verificado sobre o texto completo de
`content/pages.json`, nunca sobre um resumo.

`tools/test_propostas_reescrita.py` cobre os cinco motivos (positivo e
negativo cada), a recusa por falta de número medido, idempotência byte a
byte fora de `gerado_em`, teto+ordenação por prioridade, e prova por
mutação (inverter a condição de `agentes_leem_humanos_nao` derruba a
suíte; desfazer a inversão volta ao verde). Fixtures em
`tools/testdata/propostas_reescrita/` são linhas reais de
`published_manifest`, `v2_publication_severity` e do evento unificado real
de 2026-09-06 para `/jurisprudencia/stf-adi-4376/`; o grafo de teste é
construído do zero pelo próprio teste (sqlite3, schema idêntico ao real) e
uma linha de evento sintética documenta o limiar de
`agentes_leem_humanos_nao` porque a janela real ainda não tem exemplo
positivo (ver acima).

**Similaridade TF-IDF nos precedentes (2026-09-08, segunda geração).** A primeira
fila de 100 nasceu inteira de `precedente_disponivel_nao_citado`, e todas as 100
eram par (página, acórdão) que citava a **mesma norma inteira** — CDC 39, Código
Civil 35, CF/88 6 — com o gerador escolhendo o primeiro acórdão por chave entre
até 43 "disponíveis". Medido com cosseno TF-IDF (stdlib, acentos dobrados,
boilerplate processual na lista vazia) entre a ementa e o corpo da página: a
**melhor** similaridade de cada página deu mediana 0,020 e máximo 0,084 — a fila
inteira era ruído, e precedente errado é a citação mal atribuída do §5 do
CLAUDE.md. Agora o gerador ordena os candidatos pela similaridade, grava
`similaridade_tfidf`, `candidatos_avaliados` e `segunda_similaridade` na
evidência (um acórdão por chave, com `normas_em_comum` e `dispositivos_em_comum`)
e só propõe acima do piso **por laço**: 0,15 quando há dispositivo (artigo) em
comum, 0,20 quando só a norma inteira liga os dois — escolhido sobre a amostra
por faixa de `data/ops/precedentes_amostra_por_faixa_daily.jsonl` (2026-09-08):
entre 0,15 e 0,20, todo par com dispositivo em comum era do tema e todo par sem
era classe processual. O pool de candidatos inclui as duas rotas do grafo,
`acordao → norma` e `acordao → dispositivo → norma` (só a primeira deixava 296
de 9.199 acórdãos elegíveis), e o tokenizador guarda o número do artigo
(`n1694`). Distribuição com o pool completo: mediana 0,113, máx 0,487
(4.895 páginas com par). Primeira versão dizia:
sobram 10 precedentes (0,150–0,186), todos em páginas tributárias — o que a
Primeira Turma julga. O resto da fila é `corpo_curto` (1.348 candidatas) e
`fonte_insuficiente` (1.386). O que a medição diz de verdade: o corpus coletado
(Primeira Turma, direito público) **não casa com o acervo** (família, consumidor,
trabalho); a correção é coletar Terceira e Quarta Turmas e a Segunda Seção, não
afrouxar o piso. Teste: `SimilaridadeDePrecedenteTest` em
`tools/test_propostas_reescrita.py`.

## 9. `data/ai/risco_superacao.jsonl` — o risco de superação por página (P3)

Escrito por `tools/generate-risco-superacao` logo depois do grafo (`ExecStartPost`
de `wikijuridica-grafo-juridico.service`, 06:50), lido pelo servidor no boot
(`internal/httpserver/mcp_risco.go`) e devolvido por `contexto_juridico` em dois
níveis: por bloco e agregado. Uma linha por página que cita dispositivo presente
no grafo **e** que algum acórdão coletado também cite (1.360 em 2026-09-08);
página fora desse cruzamento não tem linha, e o servidor responde `medido: false`
com o motivo. Última linha por `path` vence. O arquivo está no `.gitignore`
(1,7 MB, derivado); a medição do dia vai em `data/ops/risco_superacao_daily.jsonl`.

- **A fórmula é explícita e o número nunca é opinião**: `risco = min(1, peso/5) ×
  recência`, com `peso` = soma dos acórdãos julgados **depois da âncora** da
  página: 1,0 se citam o mesmo dispositivo (artigo), 0,2 se citam só a norma
  inteira (laço fraco — sem o peso, 5 acórdãos citando "o CDC" levariam 1.173
  páginas a 1,0 idênticas); recência 1,0 até 365 dias do mais recente, 0,5 até
  730, 0,25 depois. Acórdão sem data conta no total e nunca nos posteriores.
- **A âncora NÃO é `reviewed_at`**: 9.715 de 10.141 páginas trazem
  `reviewed_at=2026-08-26` porque um gerador carimbou o dia da execução (commit
  546f4aef). A âncora é o `checked_at` mais antigo de `source_provenance`
  (a conferência da fonte), senão `approved_at`, senão `reviewed_at`; a linha
  grava `ancora_origem`. Acórdão com a data da âncora fica fora (estrito).
- **"Não medido" é contado**: `acordaos_sem_extracao` (3.801 em 2026-09-08) são
  acórdãos do corpus ainda sem dispositivo extraído — eles não entram e a
  explicação diz quantos são. Página não cita súmula no grafo (0 arestas), logo
  tese mudada por súmula é invisível para este número.
- **Zero não é "seguro"**: em 2026-09-08 todo o acervo mede 0 porque o corpus do
  STJ coletado vai de 2018 a 2022 e as revisões são de 2026-08. O campo
  `explicacao` diz isso com as datas. Quando o coletor trouxer acórdãos de 2026,
  o número sobe sozinho na manhã seguinte, sem mudar código.
- **Súmula 7 do STJ é ruído conhecido**: acórdão que só invoca o reexame de fatos
  raramente altera tese; a explicação avisa quando todos os posteriores são desse
  tipo, mas o número não é descontado — quem lê decide.
- **Não é etiqueta de HTML**: o dado sai só pelo canal de máquina. Levar ao HTML
  passa pela cadeia de publicação (§5 do CLAUDE.md) e pela matriz `--ressemear`.
- Teste: `python3 tools/test_risco_superacao.py` (grafo sintético de 7 nós, contagem
  independente) e `go test ./internal/httpserver/ -run 'Risco'`.

> **Acrescentado em 2026-09-16 — o campo `risco` não ordena.** A fórmula tem teto em 1,0 e
> o teto está povoado: **1.213 das 4.986 linhas valem exatamente 1,0**. Para priorizar,
> cortar ou ranquear, use `peso_apos_revisao`, que não satura. Medição, comando e a
> distribuição do dia em **§13.6**.

## 10. `data/ops/edge_frescor_daily.jsonl` — a borda serve velho o que mudou hoje? (2026-09-09)

Escrito por `tools/check-edge-frescor --gravar` (a unit
`wikijuridica-edge-frescor.timer`, 09:40 UTC, roda `--desde-horas 24 --purgar
--gravar`), uma linha por execução, `schema_version: edge_frescor_v1`. Linha
idêntica — fora `duracao_s` e `gerado_em` — não se regrava; o consumidor lê a
**última** linha de cada `date`. Sem `--gravar` o check é read-only e imprime a
mesma linha, para diagnóstico sem ponto novo na série (BUG-236). Teste:
`python3 tools/test_check_edge_frescor.py` (28 casos, offline, com a prova por
mutação abaixo).

**O que motivou, medido em 2026-09-09 às 14:23 UTC.** A única rota carimbada no
dia (`/radar-ia/`, `revised_on: 2026-09-09T00:36:02Z`) tinha o HTML fresco na
borda (`HIT`, `age: 49785`, sha igual ao disco) e a gêmea `/radar-ia/index.md`
**velha**: `HIT`, `age: 39932`, `date_modified: "2026-09-08"` e `issued`
`[[2026, 9, 8]]`, enquanto a origem (`127.0.0.1:8088`, `Host` do portal, duas
leituras idênticas) já servia `2026-09-09T00:36:02Z`. Onze horas de canal de
máquina — o que 86,5% dos bots de IA leem — desatualizado, sem nenhum
instrumento apontando. É o §4j em outra camada: lá o processo Go servia velho
com a rota respondendo 200; aqui é a borda.

- **A verdade do HTML é o arquivo cru `public/<path>/index.html`, atestado pelo
  `html_sha256` do `published_manifest`** (é o sha256 do arquivo, conferido em
  22/22 por stride de 500). **Nunca o `served_sha256` de
  `page_content_revision.jsonl`**: é a fórmula neutralizada (scripts sem
  atributo e a seção de relacionados removidos) e acusaria as 10 mil rotas como
  velhas. Também não o `content_sha256`, que só cobre o que o autor escreve.
- **Disco ≠ manifesto é outra classe, e não purga.** `disco_diverge_do_manifesto`
  (e `disco_ausente`) é defeito de publicação: purgar levaria à borda um arquivo
  que ninguém atestou. A prova por mutação em `test_check_edge_frescor.py`
  troca `sha_disco` por `sha_manifesto` no fonte real de `classifica_html` e
  mostra a classe mudar nos dois sentidos — `borda == disco ≠ manifesto` vira
  **`velha`** (purgaria o defeito) e `borda == manifesto ≠ disco` vira
  **`fresca`** (esconderia o defeito).
- **Rota fora do manifesto compara com o disco.** `/`, `/sobre/`, `/bot/`,
  `/radar-ia/`, `/fontes/`… (12 em 2026-09-09) não têm linha no manifesto; o
  disco é o que o nginx serve e não há outra verdade. A linha grava quais foram
  (`sem_manifesto`).
- **A verdade da gêmea é o processo Go (`127.0.0.1:8089`), nunca o nginx
  (`:8088`).** O Go responde a gêmea com `Vary: Accept-Encoding` e o nginx
  (`proxy_cache wj_dyn`, `s-maxage=604800`) guarda **um objeto por valor do
  cabeçalho**, por sete dias. A primeira versão deste check leu `:8088` com
  `Accept-Encoding: identity` — variante que nenhum cliente externo pede — e por
  isso recebeu o Go fresco e concluiu que a borda "acabara de buscar velho na
  origem" (`cf-cache-status: MISS` com corpo antigo). Medido em 2026-09-09 às
  15:0x UTC em `/jurisprudencia/stj-tema-1/index.md`, 14 min depois do restart do
  Go (14:21:29 UTC): `identity` e o Go davam `Repr-Digest me+fOMAS…`; as
  variantes `gzip, br` e vazia davam `7LUjhlZI…` (`verified_at: 2026-09-08`, sem a
  seção nova). No access log de gêmeas, o que a borda pede é `"gzip, br"`
  (51.217) e `""` (40.728); `identity` são 970, as sondas. É a mesma medição que
  `tools/warm-origin-cache` fez em 2026-09-05 (`VARIANTES_ACCEPT_ENCODING`), e o
  teste do check exige que as duas tuplas continuem iguais.
- **Daí a terceira classe, `origem_cache_velha`**: a borda pode estar fresca
  AGORA e o próximo MISS dela buscar no nginx a variante velha — e purgar só a
  borda repopula o Tiered Cache com o conteúdo antigo (§1 do CLAUDE.md, medido
  em 2026-09-05). O check lê as duas variantes em `:8088` só pelo `Repr-Digest`
  (a `gzip, br` vem em brotli, que a stdlib não abre; o digest é da
  representação e a compressão não o altera) e, com `--purgar`, segue a ordem do
  `deploy-binario-go`: `tools/purge-origin-cache --rota` → `purge-edge-cache` →
  releitura. O `purge-origin-cache --seco` acha **um** objeto por gêmea (o nó
  primário `fb:…:0`); as variantes de `Vary` são arquivos secundários que o
  nginx só alcança por esse nó. Que removê-lo as invalida é o que
  `pos_purga_velhas` mede na primeira execução com `--purgar` — se não
  invalidar, o exit é 2 e o dono fica sabendo, em vez de o check declarar
  purga feita.
- **Compressão e ETag não servem para comparar.** O corpo pela borda é lido com
  `Accept-Encoding: identity` e hasheado; resposta que ainda vier comprimida é
  `erro_de_sonda`. O `Repr-Digest` (RFC 9530, `sha-256=:base64:`) é conferido
  contra o corpo lido e discordância é `erro_de_sonda`, nunca "velha". O ETag da
  borda vem fraco (`W/`) porque houve compressão no caminho.
- **A lista é o carimbo.** `--dia` casa `revised_on[:10]`; `--desde-horas N`
  inclui carimbo que **toca** a janela, e dia puro (287 das 288 rotas recentes)
  conta o dia inteiro — por isso a unit usa horas e não dia: às 09:40 UTC o dia
  corrente tem uma rota e a onda carimbou ontem. Mudança de markup sem
  `--ressemear` não avança o carimbo e fica fora da lista.
- **Não amostra.** Acima de `--max` (2.000) é exit 2 com a contagem, nunca uma
  fatia silenciosa. Cada rota custa 2 leituras pela borda (8 rps, concorrência
  4, UA `wikijuridica-superficie-probe/1.0` + `X-Warming-Request: true`) e uma
  local; a variante `Accept: text/markdown` de `<path>` é um terceiro objeto de
  cache que **não** é sondado.
- **Purga por URL, com teto igual à lista.** `tools/purge-edge-cache` acima do
  `--teto-por-url` dele (3.000) degrada para purga total em silêncio e joga fora
  ~870 s de aquecimento; o check passa `--de-arquivo - --teto-por-url <n>` só
  com os canais medidos velhos, e relê o que purgou (`pos_purga_velhas`).
- **Exit:** 0 tudo fresco, na borda e na origem; 1 há velha na borda (purgada
  se `--purgar`), cache de origem velho (invalidado se `--purgar`) ou disco ≠
  manifesto; 2 não mediu — ledger ou manifesto ausentes, nginx ou Go fora
  (`/readyz` nos dois), sonda que não completou em alguma rota, purga ou
  invalidação que falhou ou não surtiu efeito, lista acima do teto. A unit
  mascara só o 1 (`SuccessExitStatus=0 1`); o 2 alerta o dono. Canal medido
  velho é purgado mesmo com o outro canal em erro, e o erro ainda derruba o exit
  para 2 — "nenhuma rota velha" não se afirma com sonda incompleta.
- **Somatório fechado:** `frescas + velhas_total + disco_diverge_total +
  origem_cache_velha_classe + erros_de_sonda == rotas_mudadas` (precedência
  velha > disco ≠ manifesto > origem velha > erro; `origem_cache_velha_total`
  conta a condição em qualquer classe, `_classe` só onde ela é a mais grave);
  `conferidas` são as sem erro. Listas cortam em 50 com o `*_total` ao lado; a
  saída de terminal lista todas.

## 11. `data/ops/baseline_bot_nao_confirmado.json` — a linha de base do não-confirmado (2026-09-10)

Escrito por `tools/generate-baseline-bot-nao-confirmado`, lido (nunca escrito)
por `tools/check-perfil-por-bot`. Existe porque o gate reprovava 15 agentes de
15 com a mesma frase, aplicando `--max-spoof 0` à **soma** de
`requests_estimated_unverified_ua` numa janela de oito dias.

**As TRÊS pernas da borda, e a que engana.** `requests_estimated` do v4 já é a
soma de duas confirmações independentes — `requests_estimated_cloudflare_verified`
(`verifiedBotCategory`) e `requests_estimated_ip_range` (`clientIP` dentro do
prefixo que o operador publica). O que sobra em
`requests_estimated_unverified_ua` é **ausência de prova de identidade**, e não
prova de fraude: o PerplexityBot legítimo mede `cloudflare_verified = 0` todo
santo dia, e só a faixa de IP o salva. Somar as pernas de novo, ou chamar a
terceira de "spoofing", desfaz a correção v4 com o sinal trocado.

**O que decide identidade, medido em 2026-09-10** por
`./tools/measure-borda-nao-confirmado-por-ip <agente>@<dia> --rdns`, que IMPORTA
a FASE 2 de `tools/generate-bot-agents-daily` em vez de reimplementá-la. Vale só
dentro da retenção de 8 dias do `httpRequestsAdaptiveGroups`: a medição de
2026-09-06 é reproduzível até ~2026-09-14, e depois disso a prova é o que está
escrito aqui.

- bingbot, 2026-09-06: as 842 não confirmadas vieram de **um IP**,
  `132.196.1.195` (US), fora dos 28 prefixos publicados pela Microsoft e **sem
  PTR** — enquanto 401 amostradas do mesmo User-Agent, no mesmo dia, foram
  confirmadas pela Cloudflare. A verificação que a própria Microsoft documenta
  é rDNS para `*.search.msn.com`. Os 401 confirmados do mesmo agente naquele
  dia vieram de `40.77.167.*` e `52.167.144.*`, todos com PTR
  `msnbot-*.search.msn.com` fechando FCrDNS.
- **Não é BingPreview colapsado dentro de bingbot** — hipótese testada e
  refutada no User-Agent exato. As 842 vieram com a string canônica
  `Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)`; a
  Microsoft real daquele dia chegou com as variantes `Chrome/116.0.1938.76` e
  `Chrome/136.0.0.0`; e o `BingPreview/1.0b` que aparece em
  `user_agent_samples` está na perna **verificada** (~6 das 407), zero das 842.
  `botagents.AGENTES` casa mesmo "bingpreview" dentro da chave "bingbot" — a
  suspeita era legítima, e o que a desfaz é medir a string, não ler a tabela.
- 2026-09-08: o bloco "SG" de quase todos os agentes é **um host**,
  `34.158.60.234` (`bc.googleusercontent.com`), vestindo perplexitybot,
  claudebot, gptbot, applebot… — a mesma rotação de identidade que o detector
  de burst do check apanha na origem, nos minutos `00:33Z` e `00:34Z`.
- perplexitybot, 2026-09-08, **mesma execução do mesmo código**: 169 amostradas
  movidas para `ip_range` (18.97.9.96–103, os 8 prefixos oficiais). É a prova
  de que a segunda consulta funciona — o zero do bingbot é resposta, não
  silêncio. **O coletor não tem defeito; o veredito é que tinha.**

**O país não decide nada.** `countries_unverified_ua` diz `US` para o bingbot, e
os Estados Unidos são compatíveis com a Microsoft: país compatível não confirma
identidade, e país incompatível também não a refuta (qualquer operador usa CDN e
região). Quem decide é o `clientIP` contra a faixa publicada, e o PTR.

**Armadilhas do arquivo:**

- **`max_diario`, nunca `total_janela`.** O critério é o máximo diário. Teto
  sobre soma muda de valor com `--dias` — foi a aritmética do defeito original
  (842 + 158 = 1.000 contra teto 0).
- **Ele ABSORVE os episódios da janela de referência, de propósito.** O v4 da
  série começa em 2026-09-02: não existe janela v4 anterior "limpa" de onde
  tirar base. Por isso cada agente guarda `dia_do_maximo` e
  `paises_no_dia_do_maximo`, e o gerador imprime o que absorveu. O teto de 842
  do bingbot **é um dia de ataque**, não a rotina dele — quem lê o arquivo tem
  de saber disso.
- **Não entra no `run-qualidade-diaria`.** Linha de base regenerada todo dia se
  abençoa sozinha: o pico de ontem viraria o normal de hoje. Regenera-se por
  decisão, com a saída lida por quem decidiu.
- **Envelhecer é reprovar.** Uma série ruidosa não admite o teste de "baseline
  inflado" de `check-baseline-testes-vermelhos`; o único sinal de apodrecimento
  aqui é o tempo, e o gate reprova acima de `--baseline-max-idade-dias` (30).
- **Agente ausente do arquivo conta como base 0** — mesmo precedente do baseline
  de vermelhos: o que não está listado é regressão. Sem isso, bastaria um
  `agent_key` novo para entrar por baixo do gate.
- **Linha anterior ao `edge_bot_agents_daily_v4`, para agente COM faixa oficial,
  é INDETERMINADA** e fica fora do veredito (impressa, nunca somada): naquele
  dia o produtor nem tentou a verificação por `clientIP`.
- **Quatro agentes não têm faixa oficial em `data/ops/bot_ip_ranges/`** —
  `amazonbot`, `amzn-searchbot`, `bytespider`, `meta-externalagent`. Para eles a
  segunda verificação é impossível e o não-confirmado mistura impostor com bot
  honesto que ninguém consegue autenticar. É lacuna **nossa** de instrumento,
  relatada e não reprovada (R4).

**Limite conhecido do coletor, medido e conservador.** O filtro `userAgent_like`
da FASE 2 nasce das amostras reais de UA **não verificado**, e essa amostra é
limitada a 4 strings por (dia, agente) — as de maior volume, porque a consulta
vem ordenada por `count_DESC`. Um agente com mais de 4 grafias distintas de UA
não confirmado pode ficar sem o token da 5ª em diante, e a cauda dela não é
reclassificada por IP. O erro é sempre para o lado seguro (nunca credita
identidade que não confirmou) e, desde que o veredito é por regressão, ele não
produz mais vermelho falso — mas está aqui nomeado, não escondido.

Prova por mutação em `tools/test_check_perfil_por_bot.py` (16 casos; nove
sabotagens distintas do detector foram medidas e todas ficam vermelhas).

## 12. `data/editorial/authorial_mass_drafts.jsonl` — e as duas armadilhas de leitura que ele ensinou (2026-09-10)

O arquivo canônico de rascunhos autorais: 7.984 registros, 47 MB, reescrito pelo
`cmd/ingest-v2-stock` a cada deploy que reingere (`tools/deploy-publico:395`).

**Ele NÃO cobre o acervo, e a diferença é grande.** Medido em 2026-09-10: 7.984
rascunhos contra 11.039 páginas publicadas. **2.824 páginas publicadas nunca tiveram
rascunho** — 1.327 delas porque `internal/v2ingest/validate.go:63` não conhece a lane
`derivada_de_fonte_oficial` que os cinco geradores da onda diária emitem. Quem ler a
contagem de rascunhos como "tamanho do acervo" erra por 28%.

**`drafts_expected` do `stock_manifest.json` não declara nada** — `v2ingest.go:654,666`
gravam nele a contagem do próprio arquivo **depois** do lote. Compará-lo com o arquivo é
o artefato validando a si mesmo (BUG-225, e o cabeçalho de `internal/refinedcorpusfloor`
já nomeia o padrão).

### Armadilha 1 — diff de linha sobre arquivo reordenado mede a ORDEM, não o conteúdo

`v2ingest.go:592` faz `sort.SliceStable` por `SourceSelectionRank` antes de gravar, e o
rewrite **renumera do 1 a cada passada** (`nextSelectionRank:1067`). Então o mesmo
registro muda de linha e de rank entre execuções sem nada ter acontecido com ele:

```
rank do MESMO intent, comparado com hoje
  revisao de 2026-09-10 (anterior)   70,4% igual
  revisao de 2026-08-30              18,7%
  a anterior a ela                    1,4%
```

Um `git diff` de linhas sobre este arquivo — ou sobre
`data/source-audit/lexml_norm_registry_20260826.jsonl`, que é regravado como
`anteriores + resolvidos` — parece perda e não é. **Compare CONJUNTOS de
`unique_intent_id`.** Em 2026-09-10 o mesmo engano apareceu nos dois arquivos, em duas
sessões diferentes, no mesmo dia.

### Armadilha 2 — campo vazio POR CONSTRUÇÃO não é dado ausente: é dado que veio de outro lugar

`public_path` é `""` em **todos** os 7.984 registros. Não é falha de preenchimento: o
rascunho nasce `authorial_mass_draft_blocked` e
`internal/publicprosecandidate/public_prose_candidate.go:728,752,756` zera
`PublicPath`, `Approval` e `Status` **sem condicional**. A rota real da página vive no
`published_manifest.jsonl`.

O perigo é que o campo vazio **não levanta erro nenhum**: o schema aceita, o JSON parseia,
o gate passa, e uma ferramenta que copiasse `public_path` dali produziria 231 linhas
apontando para lugar nenhum — em produto cujo propósito era localizar páginas que estão no
ar. Foi pego lendo o **primeiro registro** em vez de confiar no schema (R1), e hoje é caso
de teste em `tools/test_generate_rascunhos_perdidos_recuperaveis.py`.

**Regra geral:** antes de usar um campo deste arquivo, conte quantos registros o têm
preenchido. Se forem zero, ele é derivado de outro artefato — e o artefato certo é quem
deve responder.

### O que já se perdeu, e onde está

`data/editorial/rascunhos_perdidos_recuperaveis.jsonl` (produtor:
`tools/generate-rascunhos-perdidos-recuperaveis`) indexa os **231** intents que têm página
publicada e perderam o rascunho — 115.199 palavras, todas recuperáveis por
`git show <revisao_git>:data/editorial/authorial_mass_drafts.jsonl`. Os outros 376 que
saíram são o cartesiano v1 da DEC-004 e **não** devem voltar.

---

## 13. Armadilhas medidas na auditoria do cérebro de IA local (2026-09-15/16)

Nove arquivos, uma armadilha cada. Todas custaram um número errado publicado dentro da
própria sessão que os mediu. A ordem segue a tabela de gatilhos do topo.

### 13.1 `data/ops/ai_citation_signal_daily.jsonl` — mede a ORIGEM, e diz isso de si mesmo

O arquivo conta requisição que **chegou à origem**. Ele declara a própria limitação em três
campos, que existem para ser lidos antes do número:

- `is_lower_bound: true` — o valor é piso, nunca volume;
- `edge_reconciliation: "origem <= borda SEMPRE, mesmo racional de cache."`;
- `lower_bound_reason`, que enumera o que a origem **não vê**: `HIT` na borda, citação sem
  clique, resposta dada pela memória do modelo, `fetch` descartado pelo modelo e clique com
  `Referer` suprimido.

**A armadilha não é o arquivo: é ler a ressalva e usar o número assim mesmo.** Em 2026-09-15
a sessão transcreveu a frase `origem <= borda SEMPRE` e, no parágrafo seguinte, apresentou
**943 requisições de origem** como volume de bot. A borda, nas mesmas 24 h, tinha **17.325
bots em 88.033 requisições**.

Volume, alcance e retorno medem-se por `./tools/check-edge-traffic`. Este arquivo serve para
outra pergunta — *quais rotas um agente específico buscou na origem* — e é ótimo nela.

```bash
tail -1 data/ops/ai_citation_signal_daily.jsonl | python3 -m json.tool | grep -E 'is_lower_bound|edge_reconciliation'
```

### 13.2 `data/ops/edge_bot_agents_daily.jsonl` — série CUMULATIVA: somar linhas infla

Cada linha é um **retrato acumulado do dia até aquele instante**, não um incremento. Medido
em 2026-09-16 sobre o arquivo inteiro: **473 das 772 chaves `(date, agent_key)` têm mais de
uma linha**, e a mesma chave repete até **96 vezes** no dia. Os valores de
`requests_estimated` para `('2026-09-02', 'applebot')` saem em ordem crescente —
5, 9, 13, 19, 27, 29, 30, 33 — porque cada linha reescreve o total, não soma a ele.

Quem somar as linhas de um dia multiplica o tráfego por dezenas. **O leitor canônico é
`tools/edgetelemetry.py:270` (`serie_saneada`)**, que toma a última linha por chave; há
teste que reprova a leitura que deixar de passar por ele
(`tools/test_generate_previsao_audiencia.py:308`).

```bash
python3 -c "
import json,collections
c=collections.Counter()
for l in open('data/ops/edge_bot_agents_daily.jsonl'):
    d=json.loads(l); c[(d['date'],d['agent_key'])]+=1
print('chaves', len(c), 'repetidas', sum(1 for v in c.values() if v>1))
"
```

### 13.3 `data/ops/bing_webmaster_daily.jsonl` — é busca clássica; citação de IA não está ali

O arquivo carrega o que a API do Bing Webmaster devolve, e os tipos gravados em 2026-09-16
são `url_info` (1.090), `pagina_consulta` (437), `consulta_diaria` (231), `pagina_diaria`
(219), `busca_diaria` (35), `rastreio_diario` (33) e `consulta_pagina` (3). Todos vêm de
`GetQueryStats` / `GetPageStats` e da família de rastreio — **busca clássica**: impressão,
clique, posição, data de rastreio.

**Citação em resposta gerada não está neste arquivo**, e procurá-la aqui devolve zero — que
é indistinguível de "não há citação". As citações que o painel da Microsoft exibe (~23.000
em 2026-09-15) vêm de outra superfície. O fato de a API que as expõe estar em *preview* diz
respeito à maturidade da API, **não** à confiabilidade da contagem.

### 13.4 `data/ai/extracoes_dispositivos.jsonl` — append-only e VIVO, e o denominador não é a linha

Duas armadilhas empilhadas, e a segunda é a cara.

**Primeira: o arquivo cresce enquanto você o lê.** Medido nesta sessão, nas leituras de
2026-09-16: 45.067 linhas às 07:36, **45.069** às 07:59, **45.072** minutos depois — três
números diferentes para a mesma pergunta, no mesmo dia, sem que nada tenha mudado além do
relógio. Em 2026-09-15 ele **cresceu 3×** no meio de uma auditoria. Qualquer afirmação sobre
ele exige **snapshot datado** (é o que `.agents/runtime/revisao-extracoes/<data>/` existe
para guardar), e comparar contagem entre datas sem snapshot compara dois objetos diferentes.

**Segunda: o denominador certo é o item pela chave de cache, não a linha e não o item bruto.**
A chave de cache é `(chave, modelo)` — `internal/cerebro/extracao.go` — e uma reexecução
**apende** uma linha nova em vez de substituir a antiga. Medido em 2026-09-16:

| denominador | valor (2026-09-16) | valor da auditoria (2026-09-15) |
|---|---|---|
| itens somando **todas** as linhas | 138.526 | 135.181 |
| itens da **última linha por `(chave, modelo)`** ← o certo | **129.837** | **126.601** |
| itens da última linha por `chave` | 105.766 | 105.263 |
| linhas do arquivo | 45.072 | — |
| chaves `(chave, modelo)` distintas | 42.988 | — |

> **Correção do enunciado, 2026-09-16.** O §1.4 do plano
> `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` descreve 135.181 como *"a soma de todas as
> linhas de um arquivo append-only"*. Não é: é a soma dos **itens de `dispositivos`** de
> todas as linhas. O arquivo nunca teve 135 mil linhas — no histórico do git ele vai de 660
> a 37.176 (HEAD), e o pico medido no disco é 45.072. A conclusão do plano (denominador
> inflado por linhas superadas, real 126.601) **continua correta**; o rótulo da grandeza é
> que estava trocado, e trocar a grandeza é como um denominador errado começa.

```bash
python3 -c "
import json
tot=0; last={}
for l in open('data/ai/extracoes_dispositivos.jsonl'):
    d=json.loads(l); n=len(d.get('dispositivos') or [])
    tot+=n; last[(d.get('chave'),d.get('modelo'))]=n
print('itens brutos',tot,'| itens por chave de cache',sum(last.values()))
"
```

**Terceira, e é a que engana quem confia em taxa:** medir a âncora literal sobre este arquivo
**mede o filtro sobre si mesmo**. `internal/cerebro/extracao.go:503-508` descarta o item não
ancorado *antes* de gravar; contar 100% de âncora no disco prova que o filtro rodou, não que
a atribuição está certa. O que essa taxa esconde está em §14 e no precedente correspondente.

### 13.5 `data/editorial/v2_rewrite_queue.jsonl` — é RETRATO, não acúmulo

O arquivo é **regenerado inteiro a cada ingest**. Medido em 2026-09-16: **3.201 linhas com um
único `run_id`** — `v2-ingest-20260911T050000Z-v2-stock-merged-jsonl` — e `mtime` de
2026-09-11 02:58. Consequências:

- `queued_at` é a data da **regeneração**, não a data em que aquela página entrou na fila.
  Ordenar por ele não dá antiguidade de nenhuma página.
- Crescimento entre duas leituras **não** é entrada nova: é outro retrato. Para medir fluxo
  (entrou/saiu), comparam-se os conjuntos de `intent_id` entre dois retratos datados, nunca
  as contagens.
- Um único `run_id` no arquivo inteiro é o sinal de que ele é retrato. Se um dia houver dois,
  o produtor mudou de regime e esta seção precisa ser remedida.

```bash
python3 -c "
import json,collections
c=collections.Counter(json.loads(l)['run_id'] for l in open('data/editorial/v2_rewrite_queue.jsonl'))
print(len(c),'run_id distintos:',c.most_common(3))
"
```

### 13.6 `data/ai/risco_superacao.jsonl` — o score SATURA; quem ordena é `peso_apos_revisao`

Complementa a §9, que descreve o produtor e a fórmula. A armadilha aqui é de **uso**.

`risco = min(1, peso/5) × recência` tem teto em 1,0 por construção, e o teto é povoado:
medido em 2026-09-16, **1.213 das 4.986 linhas (24,3%) valem exatamente 1,0** — em 2026-09-15
eram 1.190. Um quarto do arquivo empatado no topo **não ordena nada**: quem cortar "as 200
mais arriscadas" por esse campo está sorteando dentro de um empate de 1.213.

O sinal que ordena é `peso_apos_revisao`, que não satura. Medido em 2026-09-16 sobre as mesmas
4.986 linhas: mínimo 0, máximo **162,0**, mediana **0,4** (em 2026-09-15: 0,20 a 142,00,
mediana 1,20 — o arquivo é regenerado toda manhã às 06:51, então a distribuição anda; use a
do dia, com o comando abaixo).

```bash
python3 -c "
import json,statistics
p=[json.loads(l)['peso_apos_revisao'] for l in open('data/ai/risco_superacao.jsonl')]
r=[json.loads(l)['risco'] for l in open('data/ai/risco_superacao.jsonl')]
print('linhas',len(p),'| risco==1.0:',sum(1 for v in r if v==1.0))
print('peso: min',min(p),'max',max(p),'mediana',statistics.median(p))
"
```

### 13.7 `data/editorial/first_published_at.json` — congelado, e a diferença re-data páginas

O registro de estreia de cada página. Medido em 2026-09-16:

| medida | valor |
|---|---|
| `mtime` | **2026-08-28 17:26** — congelado há 19 dias |
| `total` (e entradas em `first_published_at`) | **10.107** |
| `unique_intent_id` no `published_manifest.jsonl` | **11.114** |
| no manifesto e **sem** registro de estreia | **1.007** |
| no registro e fora do manifesto | 0 |

As 1.007 páginas sem registro **não têm data de estreia estável**: cada onda que republica
carimba nelas a data corrente, e o JSON-LD servido passa a dizer que a página nasceu hoje.

**Por que ele está congelado — duas causas medidas em 2026-09-16, e as duas precisam cair:**

1. **O produtor é órfão.** `tools/generate-first-published-at` não é chamado por nada:
   `grep -rln "generate-first-published-at" ops/ tools/ cmd/ internal/` devolve só o próprio
   script, e não há `.service`, `.timer` nem passo de `tools/deploy-publico` que o execute.
   Quem **lê** o arquivo é `cmd/publish-v2-direct/main.go:91` (e o comentário de `:3580` diz
   corretamente quem deveria produzi-lo). É o defeito de classe da ordem 3 em
   `docs/PRECEDENTES_DAS_ORDENS.md`: consumidor vivo, produtor que ninguém aciona.
2. **A entrada dele também parou.** O campo `fonte` do próprio arquivo diz de onde a data sai
   — *"histórico git do `published_manifest` (data do commit, não `approved_at`)"*. O último
   commit que toca o manifesto é de **2026-09-10** (§13.9), então mesmo executado hoje o
   gerador só alcançaria as páginas que entraram em commit até aquela data.

Rodar o gerador sem commitar o manifesto **não** fecha a lacuna, e commitar o manifesto sem
rodar o gerador também não. A diferença é conferível em um comando:

```bash
python3 -c "
import json
reg=set(json.load(open('data/editorial/first_published_at.json'))['first_published_at'])
man={json.loads(l)['unique_intent_id'] for l in open('data/editorial/published_manifest.jsonl')}
print('manifesto',len(man),'registro',len(reg),'sem estreia',len(man-reg))
"
```

### 13.8 `data/ai/fila.sqlite` — a tabela é `tarefa`, o caminho é `data/ai/`, e o WAL está vivo

Três enganos que fazem a consulta falhar ou mentir, todos conferidos em 2026-09-16:

- **A tabela chama-se `tarefa`, no singular.** `sqlite3 data/ai/fila.sqlite ".tables"` devolve
  exatamente `esquema_versao  tarefa`. `SELECT ... FROM tarefas` erra com
  `no such table`, e quem tratar o erro como "fila vazia" conclui o oposto do real.
- **O caminho é `data/ai/fila.sqlite`.** `var/cerebro/` **não existe** neste repositório
  (`ls -d var/cerebro` → *Arquivo ou diretório inexistente*); documento ou prompt que mande
  procurar lá está desatualizado.
- **Há WAL vivo ao lado** — `fila.sqlite-wal` (564.472 bytes) e `fila.sqlite-shm` em
  2026-09-16 07:59. Copiar só o `.sqlite` para medir em outro lugar **deixa para trás as
  escritas mais recentes**, e o retrato sai velho sem avisar. Para snapshot consistente, use
  `sqlite3 data/ai/fila.sqlite ".backup <destino>"`, nunca `cp`.

O banco tinha 139.546.624 bytes em 2026-09-16 07:36 — é o maior artefato de estado do
cérebro, e cresce.

### 13.9 `data/editorial/published_manifest.jsonl` — a onda diária o reescreve e não o commita

O manifesto é a fonte da verdade do que está no ar, e a §2 deste documento o classifica com
confiança **alta** — corretamente, para o conteúdo. A armadilha é de **ciclo de vida**: a
onda diária reescreve o arquivo e **não o inclui no commit dela**. Medido em 2026-09-16, o
último commit que toca o manifesto é **`315ac61b`, de 2026-09-10** — ele está `M` no
`git status` há **6 dias**, enquanto as ondas de 2026-09-15 commitaram estoque e portfólio
(`62d71de0`, `7ac3dff5`) sem levar o manifesto junto. Portanto
`git show HEAD:data/editorial/published_manifest.jsonl` devolve um estado mais velho que o
disco.

> Não é que ele **nunca** seja commitado: os commits de deploy de 2026-09-10 o levaram. O que
> não acontece é a onda **diária** commitá-lo, e é a diária que roda todo dia.

Duas consequências, as duas ativas em 2026-09-16:

1. **Quem mede pelo HEAD mede o passado.** Contar `unique_intent_id` no HEAD e no disco dá
   números diferentes; só o disco descreve o que está servido.
2. **O histórico que alimenta o registro de estreia para junto.**
   `tools/generate-first-published-at` deriva a data do **histórico git** do manifesto (campo
   `fonte`, §13.7), de modo que nenhuma página publicada depois de 2026-09-10 tem de onde
   ganhar data de estreia. Isto é **uma** das duas causas do congelamento; a outra é que o
   gerador é órfão e não roda. As duas estão medidas no §13.7, e consertar só uma não
   destrava a outra.

```bash
git status --short data/editorial/published_manifest.jsonl
git show HEAD:data/editorial/published_manifest.jsonl | wc -l   # compare com o disco
```

---

## 14. Hipóteses testadas e DESCARTADAS com evidência (2026-09-15)

Descartado com medição vale tanto quanto confirmado: é o que impede a próxima sessão de
gastar turno reabrindo o que já foi respondido. Cada linha traz o que derrubou a hipótese.
**Reabrir qualquer uma destas exige medição nova que contradiga o número da direita** — não
basta achar que o resultado é contraintuitivo.

| hipótese levantada | o que a mediu, e o que ela devolveu |
|---|---|
| a comparação **cross-família** infla a detecção de molde | **64.440 pares** comparados: mediana 0,0079, **máximo 0,0313**, e **zero** pares ≥ 0,70. O limiar nunca é alcançado nessa população — cross-família não é a causa de molde nenhum |
| o motivo `sem_duas_fontes_oficiais_verificaveis` está barrando páginas | **zero disparos** em passadas de 30, 120 e 500 candidatos. O motivo existe — `cmd/generate-acordao-pages/main.go:1560` — e não morde |
| o campo `dispositivo` do acórdão serve como camada citada | **é a fórmula de votação** — *"Vistos, relatados e discutidos…"*. Lidos 3 de 3 registros amostrados; não há dispositivo legal ali |
| as linhas legadas do cérebro (anteriores ao filtro de 2026-09-10) inventaram súmulas | **0 URNs LexML não atestadas**. Das 987 súmulas nessas linhas, 910 batem por regex; as 77 restantes são enumerações ("Súmulas 7 e 83 do STJ") que a regex de conferência não parseia — e os exemplos amostrados aparecem no próprio trecho. Sem evidência de invenção |
| as 36 tarefas truncadas do cérebro são laço degenerado do modelo | **é ementa densa**: dose-resposta monótona por tamanho de entrada — 0% abaixo de 1.000 caracteres, 5,56% acima de 5.000 — e **nenhuma** das 5.930 tarefas concluídas exibe a assinatura de laço |
| a gêmea Markdown é a alavanca de citação por IA | a classe de agente que responde lê **HTML 128× mais**: **26 requisições à gêmea contra 3.352** ao HTML. A gêmea é contrato de canal de máquina (§7 do `CLAUDE.md`), não alavanca de citação |
| o MCP já é canal de produto | **245 de 301** `tools/call` em 9 dias são sonda **nossa**; as 5 ferramentas de ativo receberam **zero** chamadas externas. É superfície servida, ainda não consumida |
| o IndexNow tem teto de 1.000 URLs por dia | `MAX_URLS=1000` é **por requisição**, não por dia. Medido: **19.669 URLs num único dia**, 20 de 20 lotes aceitos. Teto de dia não existe nessa constante |

## 15. O git converte fim de linha e destrói evidência — três casos medidos em 2026-09-16

**Gatilho por ATO:** *antes de commitar qualquer arquivo cujo `sha256` seja prova* — fixture de
teste baixada da fonte, censo, amostra de auditoria, arquivo com hash publicado num relatório.

`core.autocrlf=input` nesta máquina converte CRLF em LF ao adicionar. Para código isso é correto
e desejado. Para arquivo cujo byte é evidência, é **destruição silenciosa**: o `git add` sai com
exit 0, o arquivo continua certo na worktree, e o blob guardado é outro. **Só um checkout novo
revela**, e aí o teste fica vermelho por um motivo que nada no código explica.

| # | arquivo | disco | blob | como apareceu |
|---|---|---|---|---|
| 1 | `.../censo-20260915/colisao/-quinta-turma__20260131.json` | `591363b3…` | `3a955bd3…` | conferência manual antes do commit `22f36e15` |
| 2 | `internal/stjacordaos/testdata/espelhos-…-malformado.json` | 599 B, `ea2537c3…` | 576 B, `be44ede8…` | o agente da frente P1 conferiu antes de commitar |
| 3 | `internal/stjacordaos/testdata/dataset-espelhos-primeira-turma.html` | **115.986 B** | **115.162 B** | **já estava corrompido em HEAD** — achado pela guarda nova |

**O caso 3 é o que justifica a guarda.** Ninguém percebeu porque a worktree sempre esteve certa, e
dois testes leem essa fixture. Pior: `internal/stjacordaos/coleta.go:24` e `dataset_test.go:10`
**afirmam** *"a página real da Primeira Turma tem 115.986 bytes"* — o comentário e a fixture
commitada já discordavam, e nenhum instrumento enxergava.

### O conserto, e a ordem importa

1. `<diretório>/.gitattributes` com `* -text` (ou o arquivo nomeado), **escopado ao diretório**.
2. `git add --renormalize <caminhos exatos>` — **`git add` sozinho NÃO basta**: ele reusa o cache
   de stat e não reconverte. Foi assim que a primeira tentativa no censo pareceu não funcionar.

**Nunca ponha `-text` no `.gitattributes` da raiz.** Ele o proíbe por escrito, e a proibição está
certa lá: protege os JSONL da fábrica, que são gerados por ferramenta e não têm sha256 publicado
como evidência. As duas regras convivem porque são sobre classes de arquivo diferentes.

### A guarda

`tools/check-evidencia-byte-a-byte` (read-only) confere que o blob bate com o disco em
`*/testdata/*`, `*censo-*/*`, `data/source-audit/*`, `*/fixtures/*` e `*/golden/*`. Bancada em
`tools/test_evidencia_byte_a_byte.py`, 8 asserções, 3 mutantes mortos.

**Ela pula arquivo em edição na worktree, e isso é deliberado.** A primeira versão acusou
`data/source-audit/v2_source_provenance.jsonl`, que tinha **zero CRLF dos dois lados** e estava
` M` com 20.970 linhas legitimamente reescritas por outra frente. Comparar índice com disco acusa
qualquer arquivo em edição — que é trabalho em curso, não corrupção. **Guarda que acusa trabalho
em curso é guarda que se aprende a ignorar.**

---

## 16. O alarme que não podia tocar — seis armadilhas medidas em 2026-09-16

Família inteira de defeitos com a MESMA assinatura: **o instrumento cai, e a queda
chega ao dono com o número de quem mediu** — ou não chega. Todas foram medidas neste
dia, e cada uma derruba uma leitura "óbvia" que uma sessão anterior já tinha escrito.

### 16.1 A convenção 0/1/2 é deliberada — e a máscara do 1 é o que PRESERVA o alarme do 2

Está escrita em `tools/run-daily-content:264-278` e em
`ops/systemd/wikijuridica-daily-content.service:52-55`:

| código | significado | a unit |
|---|---|---|
| 0 | mediu, está são | sucesso |
| 1 | mediu, está degradado — **VEREDITO** | **mascara** (`SuccessExitStatus=0 1`) |
| ≥ 2 | não mediu / processo quebrou — **DEFEITO** | falha, e o `OnFailure` avisa |

**Um plano anterior mandava REMOVER `SuccessExitStatus` de 19 units. Isso era regressão**,
e três medições a derrubaram: (a) a convenção é deliberada e documentada; (b) o alarme
CHEGOU — `04:50:14 wikijuridica-alerta[2300886]: ⚠️ Onda diaria de conteudo parou`, pelo
canal próprio do script, com `ExecMainStatus=1` e `Result=success`; (c) duas units da
lista já estavam certas (`moderacao-transparencia` com `SuccessExitStatus=75`,
`bot-telemetry` com a diretiva removida e o motivo em `:68-70`).

**O gate conta 22 diretivas `SuccessExitStatus`, não 19** — o número de 19 é o de units
citadas no plano, e os dois não são a mesma população. Quem for auditar, conte pelo gate.

### 16.2 O defeito real: TODA exceção não tratada vira exit 1 — e a máscara a engole

`sys.exit(main())` faz o interpretador sair com **1** quando uma exceção sobe ao topo.
Logo: `traceback ⇒ exit 1 ⇒ a unit mascara ⇒ Result=success ⇒ OnFailure MUDO`. O
instrumento quebrado fica **indistinguível** do instrumento que mediu e disse "está tudo
bem". Vale **inclusive** para as ferramentas que já distinguem 1 de 2, porque o `return 2`
delas só cobre o erro **antecipado**.

Conserto: `tools/lib/saida_de_medidor.py` (`main_protegido`) e o irmão `.sh`. O traceback
continua inteiro no stderr — **isto não é mascarar erro, é o oposto**: só o número passa a
dizer a verdade.

### 16.3 Quatro ferramentas não tinham caminho de saída ≥ 2 NENHUM

`check-tunnel-health`, `check-fontes-alcancaveis`, `check-network-health` e
`check-portal-health` só sabiam 0 e 1. Para elas a máscara apagava o **único** sinal
existente. E o estado que faltava não era teórico:

- `check-fontes-alcancaveis` com o registry vazio sondava **zero hosts**, não achava
  nenhum morto e imprimia **`pass`**. Zero fonte sondada não é "todas vivas".
- `check-tunnel-health` com a frota vazia pulava a guarda inteira (`if frota_total and …`)
  e saía **0**, tendo sondado zero réplicas.
- `check-portal-health` engolia toda exceção de `systemctl show` num `return ""`; daí
  `int("" or 0) = 0`, `NRestarts` virava 0, o delta virava 0 e **o detector de laço de
  restart — o único instrumento da classe (A) de `wikijuridica-social.service:85-95`, o
  que pegou os 87 restarts — ficava cego dizendo OK**.

### 16.4 Exit 1 mascarado **NÃO** aborta o `ExecStart` seguinte — exit 2 aborta

Um achado lateral dizia que o exit 1 de `generate-alertas-reconciliados` abortava o
`check-owner-alerts-abertos` em `wikijuridica-alertas-abertos.service:50-51`, e que
faltava o prefixo `ExecStart=-`. **Medido com unit volátil no gerenciador de usuário
(systemd 252), e é falso:**

```
ExecStart=/bin/sh -c 'echo PRIMEIRO; exit 1'   SuccessExitStatus=0 1
ExecStart=/bin/sh -c 'echo SEGUNDO-RODOU'
  -> PRIMEIRO / SEGUNDO-RODOU / Result=success / ExecMainStatus=0

o mesmo com `exit 2` no primeiro
  -> PRIMEIRO apenas / Result=exit-code / ActiveState=failed
```

Com a máscara, o exit 1 é **limpo** e a cadeia continua. Quem aborta é o **≥ 2**.
Portanto **acrescentar `ExecStart=-` ali seria REGRESSÃO**: esconderia do `OnFailure`
justamente o exit 2 que o helper agora produz quando o reconciliador QUEBRA. A unit está
certa como está.

### 16.5 `StartLimitIntervalSec` em `[Service]` é ignorada — e o alarme fica aritmeticamente impossível

`systemd-analyze verify` sobre uma fixture devolve, literalmente:

```
Unknown key 'StartLimitIntervalSec' in section [Service], ignoring.
```

E há um caso onde o defeito **não tem literal para procurar**:
`wikijuridica-cerebro.service` tem `Restart=always`, `RestartUSec=15s` e **não declara
`StartLimit*` nenhum**. Valem os defaults do manager (medidos:
`DefaultStartLimitIntervalUSec=10s`, `DefaultStartLimitBurst=5`). Cinco partidas a 15 s
levam **≥ 60 s** contra uma janela de **10 s**: o burst **nunca** é atingido, a unit
**nunca** entra em `failed`, e o `OnFailure=` da linha 42 **nunca** dispara.

**A resposta não é `StartLimitIntervalSec=0`** — `wikijuridica-social.service:84-96` já
analisou essa troca e escolheu o `0` de propósito, porque daemon que SERVE não pode ficar
parado até alguém mandar `reset-failed`. Para daemon que **processa**, a resposta é
**detector nomeado**: `tools/check-cerebro-vivo`, que reprova por **crescimento na
janela**, nunca por nível (nível cumulativo cria gate vermelho que nada drena).

**Piso de ruído medido**: `NRestarts=1` acumulado, mesmo PID (926445) desde
2026-09-14 04:40:57, **0 reinícios** na janela retida do journal. Limiar = 2, e a folga
entre 0 e 2 é operação normal (troca de binário, `daemon-reload`).

### 16.6 Em bash, `trap ERR` **não** pega a violação de `set -u`; `trap EXIT` pega

O conserto prescrito para bash era `set -e` + `trap ERR`. Medido nesta máquina:

| script | crash de `set -u` | resultado |
|---|---|---|
| `set -uo pipefail` + `trap ERR` | referência a variável não definida | **trap NÃO dispara**, sai **1** |
| `set -uo pipefail` + `trap EXIT` | idem | trap dispara, dá para corrigir para **2** |
| `set -euo pipefail` + `set -E` + `trap ERR` | `false` dentro de função | dispara (o `-E` é obrigatório) |

E isso decide o desenho, porque **dos seis scripts bash chamados pelas units que mascaram
exit 1, CINCO não têm `set -e`**. Acrescentar `set -e` a eles mudaria a semântica de falha
de cada comando — regressão proibida. Por isso `tools/lib/saida_de_medidor.sh` tem **duas**
funções, e a escolha entre elas não é estilo: é qual `set` o script já usa.

Cuidado adicional: **bash guarda UMA trap EXIT**. `tools/run-daily-content` já tem a sua
(`gravaEvidencia`, que preserva ≥ 2 desde a auditoria de 2026-08-28); instalar outra ali a
**destruiria**. O gate reconhece a que já existe em vez de exigir o helper.

### 16.7 O `.path` reinicia o servidor sem guarda — e `ConditionPathExists` seria pior

`ops/systemd/wikijuridica-server-reload.path` observa três artefatos do cérebro e dispara
`systemctl restart wikijuridica-server.service` **como root, sem condição**. Em 24 h:
**2 disparos**, e o de **04:52:02** caiu **108 segundos** depois do fim da onda diária
(04:50:14). O desastre está descrito em `wikijuridica-daily-content.service:36-43`:
restart entre a escrita do sitemap e a do manifesto ⇒ *sitemap sem manifesto* ⇒ o boot
aborta (`publishedmanifest.Validate`) ⇒ com `Restart=always`/`RestartSec=5`/
`StartLimitIntervalSec=0`, **laço infinito**.

**A guarda tem de ESPERAR, não pular.** `PathChanged` é *edge-triggered*: condição falsa ⇒
unit **pulada** ⇒ o restart se perde **para sempre**, o servidor fica com índice velho e
`buscar_semantico` some de `tools/list`. Daí `tools/aguardar-fim-de-deploy`.

E **`flock` não serve**: o lock de transação é **arquivo-batida com mtime**, re-tocado a
cada 30 s por `com_batida_no_lock()` (`tools/deploy-publico:196-203`). Ninguém segura fd
nele, então `flock -w` retornaria na hora.

**O lock tem CINCO leitores, não quatro** — o quinto é Go:
`internal/checks/http_smoke_redesocial.go:60,66`, e ele escreve a janela em **minutos**
(`30 * time.Minute`), não em segundos. Um teste que exigisse o literal `1800` dele estaria
mandando o código piorar para satisfazer a asserção; `tools/test_aguardar_fim_de_deploy.sh`
verifica a **equivalência** (1800 s ÷ 60 = 30 min).

> **Armadilha de teste que custou uma execução:** a primeira versão do wrapper esperava com
> `exec {fd}< <(exec cat)`. Funciona no terminal e **trava** sob `saida=$(wrapper 2>&1)`: o
> `cat` da substituição de processo herda o stderr capturado e nunca o fecha. O conserto é
> um **FIFO aberto em `<>` e desligado do filesystem** — espera real no kernel, sem `sleep`,
> sem busy-wait e sem processo auxiliar.

### 16.8 `generate-edge-cache-coverage` é um wrapper de `exec` — o exit code é de outro arquivo

Ele tem 24 linhas e termina em `exec "$ROOT/tools/check-edge-cache-coverage" --gravar "$@"`.
O `set -euo pipefail` dele quase não alcança nada: **o código de saída da unit é o da
ferramenta execada**. Exigir o helper no wrapper seria exigir uma linha que não muda
comportamento nenhum — por isso `check-units-alarme` **segue um salto de `exec`** ao
verificar a proteção.

### O que guarda tudo isso

`tools/check-units-alarme` ganhou **R-F** (alarme inalcançável, com allowlist de detector
nomeado que exige arquivo existente, executável e que **nomeie a unit** — detector que não
nomeia o alvo não é detector) e **R-G** (só 1 e 75 são mascaráveis; **mascarar 2 reprova
sempre**, porque 2 é "não medi"; e unit que mascara 1 exige que todo `ExecStart` sem
prefixo `-` aponte para script com tradução crash→≥2).

Provado por mutação em `tools/test_units_alarme.sh`: gate cego à seção, gate que aceita
mascarar o 2 e gate que não exige a proteção — **os três morrem**, cada um no caso que o
mira.

## 17. `data/ai/extracoes_dispositivos.jsonl` — dois recortes, e eles dão números diferentes

**O arquivo é append-only e VIVO** (o cérebro escreve nele agora), então **toda medição exige
snapshot datado, com sha256 e hora de corte**. A referência desta seção é
`.agents/runtime/p5-atribuicao/20260916/extracoes_snapshot_20260916.jsonl`, sha256
`f689279ca3ff57f4e7982bfbaa1dc5c858f5fffc6746ba6c433072608c886892`, 45.089 linhas,
corte 2026-09-16T08:39:02-03:00.

**A armadilha: existem DOIS recortes legítimos, e eles não coincidem.**

| recorte | quem usa | contagem no snapshot |
|---|---|---|
| última linha por **`(chave, modelo)`** — `cerebro.ChaveExtracaoCache` | o cache de enfileiramento (`UltimaExtracaoPorChaveEModelo`), e por isso é o recorte da **medição de qualidade** | **43.005** chaves · 129.913 itens |
| última linha por **`chave`** | `generate-revisao-extracoes` e `generate-writeback-extracoes` — é o que **vira promoção, grafo e página** | **36.224** chaves · 39.271 itens de súmula do STJ |

A diferença são **6.781 chaves com duas linhas**, e o par é sempre o mesmo, conferido item a item
em 2026-09-16: `{parser, qwen3.5:4b}`. Nenhuma chave tem duas linhas de modelos de geração
diferentes.

**Consequência prática, medida na passada do P5:** depois da revisão de atribuição, o recorte por
`(chave, modelo)` ainda mostrava **4 itens** de súmula fora do catálogo, e o recorte por `chave`
mostrava **0**. Não era defeito: os 4 estavam em linhas antigas que outra linha mais nova já
superou, e que o writeback **não lê**. Quem medir por um recorte num dia e pelo outro no dia
seguinte vai chamar isso de regressão — e vai estar medindo dois universos.

**Regra:** diga qual recorte usou, no mesmo lugar em que disser o número.
`cmd/medir-atribuicao-no-trecho` imprime o dele (caminho, sha256, linhas e chaves de cache) em
toda execução, de propósito.

## 18. INSTRUMENTO QUEBRADO INDUZ A CONSERTAR A COISA CERTA NO LUGAR ERRADO (2026-09-16)

Ordem do dono, 2026-09-16: *"Cuidado com bugs de gerador ou de gate, eles podem te induzir a
erro. Você deve registrar essas armadilhas."*

Esta seção não é sobre um arquivo de dado: é sobre o **erro de atribuição** que um gate ou um
gerador defeituoso provoca em quem o lê. As três formas abaixo foram medidas no mesmo dia, e em
todas o instinto certo — *"o gate reprovou, então o conteúdo está errado"* — levava a destruir
trabalho bom.

### 18.1 O gate reprovou 1.425 vezes, e 100,0% era ele

`check derived-body-repetition` acusou **1.425 ocorrências** de frase repetida nas páginas de
acórdão do STJ e **parou a onda diária na etapa 4/9**. A leitura natural: a moldura de
`cmd/generate-acordao-pages` repete texto, então corrija o gerador.

**A medição disse o contrário.** Assinatura das ocorrências, sobre o lote inteiro:

```
ocorrencias intra-pagina: 1413
  comeca_com_digito   1413  (100,0%)
     ex: "371 do Código de Processo Civil de 2015"
```

Aquilo não é frase: é o rabo de `art. 371 do Código de Processo Civil de 2015`, partido no ponto
de **`art.`**. `internal/blocosunicos/blocosunicos.go` cortava sentença em `[.!?]\s+` **sem lista
de abreviações**, o fragmento ficava com 10 palavras e passava o piso de 8 — então **toda página
que cita o mesmo artigo em duas seções "repete uma frase"**.

Custo se a leitura natural tivesse prevalecido: reescrever **7.569 páginas corretas** para
agradar um detector quebrado, e o gerador passaria a evitar citar o mesmo dispositivo duas
vezes, o que é exatamente o contrário do que uma página de acórdão deve fazer.

**A régua que separou, e ela foi escrita ANTES do número:** *se ≥80% das ocorrências começarem
com dígito ou `§` (assinatura de corte em abreviatura), a causa é o segmentador; se <50%, há
repetição real.* Deu 100,0%.

### 18.2 O rótulo do driver dizia "completou" quando a cadeia havia parado

Na mesma investigação, `tools/publicar-estoque` imprimia `cadeia completou: sim` numa passada que
**morreu na etapa 4/9**. O campo lido era `escopo` do `daily_content_runs.jsonl`, e o trap `EXIT`
gravava `completa` sempre que a variável de escopo estivesse vazia — que é o estado de um
`exit 1` direto de gate. **Campo-proxy lido como campo-fato.**

Efeito no chefe: eu concluí que o `OnFailure` era alarme falso e mandei um agente "consertar o
exit 1". Ele mediu primeiro e me corrigiu: o exit 1 estava certo, o alarme estava certo, e o que
mentia era a linha de relatório. **Mandei consertar a guarda em vez do defeito** — e só não
aconteceu porque o agente não obedeceu antes de medir.

### 18.3 O teste ficou vermelho por causa do disco, não do código

`TestOLoteDeSessentaContraOOraculo` reprovou com *"a passada devolveu 0 página(s): sem duas irmãs
não há colisão de lote a medir"*. Não era regressão: as 7.569 intenções da família acabavam de
ser commitadas, então `roda` corretamente devolveu zero — as já emitidas saem do caminho antes de
gastar cota, e é isso que faz o drenador avançar em vez de remontar as mesmas páginas.

**Duas causas se parecem e só uma é defeito:** poço drenado (nada a medir) e passada vazia com o
poço cheio (regressão). Um teste que olhe só `len(Paginas) == 0` acusa o código pelo estado do
disco; pular sempre que der zero esconde a regressão. O conserto foi expor `Passada.JaEmitidas` e
**decidir por dado, nunca por leitura da linha de log**.

### O que fazer, na ordem

1. **Antes de corrigir o produtor porque um gate reclamou, meça a ASSINATURA das ocorrências.**
   Concentração de 100% num padrão sintático (começa com dígito, começa com `§`, sempre a mesma
   seção) é assinatura de **instrumento**, não de conteúdo. Conteúdo ruim é disperso.
2. **Leia a ocorrência inteira, não a contagem.** As 1.425 viraram diagnóstico na hora em que uma
   delas foi impressa por extenso: `"371 do Código de Processo Civil de 2015"` se explica sozinho.
3. **Régua antes do número** (§ `regua-do-veredito-antes-do-numero`): escreva qual resultado
   implica qual culpado, e só então rode.
4. **Divergência entre dois instrumentos é BUG, e se fecha por paridade** — nunca escolhendo o
   veredito que dá menos trabalho. Aqui, `check derived-body-repetition` reprovava e
   `generate-v2-publication-severity` classificava as MESMAS páginas como `limpo`: os dois não
   podiam estar certos.
5. **Corrija no instrumento compartilhado, e conte os consumidores.** `blocosunicos.Frases` é
   usado pelo gate e por três geradores (`stj-tema`, `stj-sumula`, `stf-informativo`): consertar
   ali destrava quatro caminhos, e consertar no gerador de acórdão deixaria os outros três
   quebrados do mesmo jeito.
6. **Correção de detector nasce com CONTROLE nas duas direções.** O teste tem de provar que o
   falso positivo morreu **e** que a repetição real continua sendo pega — senão a correção é
   indistinguível de desligar o gate.

### 18.4 O gate disse "EM LACO" sobre um laço que havia terminado 3,8 horas antes

A quarta desta família, e a mais fácil de acreditar, porque o gate **não estava
errado sobre o passado** — só sobre o tempo verbal.

`tools/check-cerebro-vivo` reprovou com `wikijuridica-cerebro.service: EM LACO |
restarts na janela de 24h: 23`. A leitura natural é "o cérebro está reiniciando
agora". A própria linha desmentia isso, no fim: `ativo=active desde=Wed
2026-09-16 17:02:36`, três horas e quarenta e oito minutos antes.

**O que a medição mostrou**, contando os intervalos entre partidas:

```
21 intervalos DENTRO do laço ... 17 a 273 s (mediana 21 s), 12:09 → 12:18
depois do laço ................. 15:36 e 17:02, partidas isoladas
desde 17:02 .................... nenhuma
```

Um laço com `RestartSec=15` se apresenta como partida a cada ~20 s. O que havia
era um laço **real** de nove minutos, já corrigido: a causa era `SQLITE_BUSY`
(`database is locked (5)`) tratada como fatal, e às 12:18:50 a versão nova subiu
e passou a **pausar com a classe nomeada** em vez de morrer — está no journal,
na linha `pausa [infra/]: fila ocupada por outro processo`.

**A armadilha é de classe conhecida, e o próprio gate já a descrevia.** O
docstring dele diz, correto, que reprovar por NÍVEL acumulado *"cria um gate que,
uma vez vermelho, fica vermelho"*. Ele então passou a contar ocorrências **dentro
de uma janela** — o que é melhor, e ainda é nível: a janela de 24 h carrega o
passado já consertado, então **qualquer conserto de laço deixa o gate vermelho
pelas 24 h seguintes**. É o "vermelho permanente que se aprende a ignorar" que o
§P9 do plano do cérebro condena, com outra roupa.

**A correção é o segundo eixo, não um limiar maior.** Nível responde *quantas
vezes reiniciou*; fluxo responde *ainda está reiniciando*. O veredito é a
conjunção:

```python
em_laco       = na_janela > limiar and estavel_ha < ESTABILIDADE_SEGUNDOS
laco_historico = na_janela > limiar and not em_laco   # passa, e AVISA
```

`ESTABILIDADE_SEGUNDOS = 1800` é **calibrado por medição, não por prudência**:
6,6× o maior intervalo observado dentro do laço (273 s) e 120× o `RestartSec`.
Um laço ativo nunca fica 30 minutos sem reiniciar; um sistema consertado sempre
fica.

**Duas notas de método que valem mais que o conserto:**

1. **O tempo desde a partida não se lê por `strptime`.** O
   `ExecMainStartTimestamp` sai como `Wed 2026-09-16 17:02:36 -03`, que **não
   casa** com `%a %Y-%m-%d %H:%M:%S %z`. Um parse que falhasse em silêncio
   devolveria "0 s desde a partida" — que neste gate significa **EM LAÇO**. O
   caminho sem locale é `ExecMainStartTimestampMonotonic` contra
   `/proc/uptime`.
2. **O teste existente pegou a regressão, e foi por ter controle positivo.**
   Ao entrar o eixo de fluxo, a fixture de laço passou a ser julgada contra a
   estabilidade **real da máquina** (3,8 h) e o controle positivo virou verde por
   acidente — isto é, reprovou. Daí a flag `--estavel-ha`: **um teste de
   predicado com dois eixos tem de controlar os dois**, senão o eixo não
   controlado vem do ambiente e o resultado muda de hora em hora.

*E uma armadilha de leitura, de brinde:* ao medir o exit do gate por
`./tools/check-cerebro-vivo … | tail -4` eu li `EXIT=0` e quase registrei "o
predicado não morde". Era o exit do `tail` — `PIPESTATUS[0]` é o do gate, e a
armadilha já estava escrita em `.claude/rules/`.
