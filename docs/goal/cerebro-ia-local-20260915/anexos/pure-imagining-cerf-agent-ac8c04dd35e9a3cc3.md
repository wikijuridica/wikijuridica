# REFUTAÇÃO ADVERSARIAL — RUNBOOK P4/P5

Tudo abaixo é leitura/medição read-only feita nesta sessão em /opt/wiki, 2026-09-15.
Veredito: **OPERAVEL_COM_EMENDA**. Nenhum passo de P4/P5 publica, purga ou re-data
o acervo; o dano real está concentrado em UM passo (o 10), que manda reiniciar
produção com base num artefato de cache, e em DOIS passos que medem a coisa errada
(o 14 e o 12/16).

---

## A1 — PASSO 10 MANDA REINICIAR PRODUÇÃO POR CAUSA DO CACHE DA BORDA (o pior)

O passo 10 compara `html_sha256` de `https://wikijuridica.com.br/api/v1/citar<rota>`
com `sha256sum public/<rota>/index.html`, espera "hashes idênticos", e prescreve na
falha: *"Conserto: reiniciar pela cadeia"*.

MEDIDO agora, em rota que nenhum passo deste runbook toca:

| fonte | html_sha256 |
|---|---|
| `https://.../api/v1/citar/jurisprudencia/stf-aco-1560/` | `bdd5245baf2e…` |
| **origem** `http://127.0.0.1:8088/...` (Host: wikijuridica.com.br) | `4c575009031…` |
| `sha256sum public/jurisprudencia/stf-aco-1560/index.html` | `4c575009031…` |
| linha única do `published_manifest.jsonl` (`grep -c` = 1) | `4c575009031…` |
| bytes servidos `Accept-Encoding: identity` | `4c575009031…` |

Cabeçalhos da resposta divergente: `cache-control: public, max-age=60, s-maxage=3600`
· **`cf-cache-status: HIT`** · **`age: 148`**.

Ou seja: disco, manifesto e bytes servidos concordam; só a resposta **cacheada na
borda** discorda, e ela pode estar até **1 h** atrasada (`s-maxage=3600`). O
operador que seguir o passo 10 vê divergência e **reinicia `wikijuridica-server`
em produção** por um TTL — serviço cujo boot roda `publishedmanifest.Validate` e,
por contrato, pode recusar subir.

A própria API diz o procedimento certo no payload:
`verificacao.como = "o sha256 dos bytes de <url>, obtidos com Accept-Encoding: identity,
deve ser igual ao campo html_sha256"`.

Amostra: **6 de 6** outras rotas por stride batem API=disco=manifesto — ou seja o
falso positivo é intermitente, o que é pior: não há como distinguir "P6 falhou" de
"esta rota está cacheada" com o comando escrito.

MEDIDO ainda, para fechar a atribuição: **o processo Go NÃO está velho** —
`http://127.0.0.1:8089/api/v1/citar/...` devolve `4c575009…`, o valor certo, e
`ExecMainStartTimestamp=2026-09-15 12:30:27` é POSTERIOR ao mtime do manifesto
(12:28:57). A divergência é **só** o objeto cacheado na Cloudflare. Portanto a
remediação prescrita (reiniciar) não conserta nada: ela reinicia um processo que já
está correto e deixa o TTL da borda intacto.

**Emenda mínima (3 linhas):**
1. Consultar a autoridade sem cache, que é o **Go em `127.0.0.1:8089`** (o
   `WIKI_HTTP_ADDR` da unit) — `127.0.0.1:8088` é nginx **com `proxy_cache wj_dyn`
   em `/api/v1/*`** (CLAUDE.md §3) e só por sorte veio fresco na minha sonda:
   `curl -s http://127.0.0.1:8089/api/v1/citar<rota>` com o UA de sonda interna +
   `X-Warming-Request: true`.
2. Tirar a linha de base ANTES de o P6 publicar, na mesma rota que se vai conferir
   depois. Base divergente = defeito pré-existente, nunca sinal de P6.
3. Manter o "não republicar nem purgar" que o runbook já escreve — e acrescentar
   **"não reiniciar sem antes conferir a origem"**.

---

## A2 — "O LIMIAR NUNCA MORDE" É AMOSTRA APRESENTADA COMO POPULAÇÃO; A MARGEM É 5× MENOR

§0.3 e o passo 4 sustentam-se em "máximo real **0,5697** contra 0,70: o limiar nunca
morde", de um stride de **150 de 1.074 páginas = 11.175 de 576.201 pares (1,9%)**.

MEDIDO — rodei o gate real (`./tools/check-derived-authorial-floor`, exit 0, **106,3 s**):

```
stj-tema-derivado: 1074 paginas | mediana 0.2799 | max 0.6657 (limiar 0.70)
stf-informativo-derivado: 60 | mediana 0.3455 | max 0.6787
stj-sumula-derivada: 112 | mediana 0.4098 | max 0.6407
```

A **mediana confirma a régua** (0,2784 amostrado × 0,2799 população — é a mesma
régua). O **máximo, não**: a população dá **0,6657**, não 0,5697. A folga até 0,70 é
**0,0343**, não 0,1303 — cinco vezes menor. E `stf-informativo-derivado` chega a
**0,6787**, folga de 0,0213, numa família de só 60 páginas.

Consequência operacional: o DEPOIS do passo 4 ("0 pares ≥ 0,70") não é expectativa
segura para a família de acórdãos, que é população **outra** e **maior**; e a frase
"o limiar nunca morde" não se sustenta em população.

**Emenda:** trocar o número esperado do passo 4 por "≤ o máximo medido hoje na
população (0,6657 em tema, 0,6787 em informativo)", e declarar em toda linha do I1
"N de M pares" com o denominador da população, não da amostra.

---

## A3 — O SELFTEST QUE O RUNBOOK DIZ NÃO EXISTIR EXISTE, E TEM IGUALDADE EXATA

Passo 3: *"Não há teste do gate para rodar (MEDIDO)"*. O runbook só grepou
`tools/test_check_derived_authorial_floor*`.

MEDIDO: **`tools/check-derived-authorial-floor-selftest` existe, 313 linhas.** E em
`:231-238`:

```python
PARES_REPROVADOS_CONHECIDOS = 0
todos_pares, reprovados = mod.pares_quase_identicos(corpus, mod.LIMIAR_UNICIDADE)
placar.exige(len(reprovados) <= PARES_REPROVADOS_CONHECIDOS, ...)
placar.exige(len(reprovados) == PARES_REPROVADOS_CONHECIDOS, ...)   # IGUALDADE EXATA
```

`pares_quase_identicos` percorre **toda** família de `FAMILIAS_CANAIS_DERIVADOS`.
Registrar a família (passo 3) é inócuo hoje — o glob não casa arquivo, `corpus[familia]=[]`
(conferido em `:457-462`) —, mas no instante em que o P6 gravar o shard **um único par
de acórdãos ≥ 0,70 deixa o selftest vermelho**, e A2 mostra que a população real
chega a 0,6657. O runbook não põe o selftest na lista de gates do passo 9, então a
guarda que pegaria isso nunca roda na frente que a cria.

**Emenda:** acrescentar `./tools/check-derived-authorial-floor-selftest` à AÇÃO do
passo 9, e escrever no passo 3 que `PARES_REPROVADOS_CONHECIDOS` é teto **e** piso:
quem publicar a família responde por ele.

---

## A4 — O(n²) EM PYTHON: O GATE JÁ CUSTA 106 s E A FAMÍLIA NOVA O MULTIPLICA POR ~5,4

`tools/check-derived-authorial-floor:491-505` documenta: *"a maior família tem 205
páginas — 20.910 pares, milissegundos em Python puro"*. **O comentário mente hoje**:

- MEDIDO: maior família = `stj-tema-derivado`, **1.074 páginas = 576.201 pares**.
- MEDIDO: o gate inteiro leva **106,3 s** (`real 1m46.313s`), 1.394 páginas no eixo.
- `todos.append(...)` guarda **cada par** como tupla de 6 e depois `todos.sort()`.

Com os 2.488 acórdãos do P6 numa família só: **+3.093.828 pares (5,4×)**, ~3,7 M
tuplas antes do sort.

**Honestidade da medição (R3):** os 106,3 s são a passada INTEIRA, que também abre
os **11.357** arquivos de `public/` para os eixos 1 e 2 — **não separei** o custo de
`pares_quase_identicos`. Então 106,3 s é **teto superior** da parte O(n²), e não se
pode extrapolar "~650 s" a partir dele. O que se afirma sem extrapolar: a parte
quadrática cresce **5,4×** em pares e a lista `todos` passa a ~3,7 M tuplas antes de
um `sort`, num gate sem timeout. O número que falta se obtém em 10 linhas de Python
read-only importando o módulo como o selftest já faz (`mod`) e cronometrando só
`pares_quase_identicos` — isso é o que o passo deveria mandar fazer. E ele roda em
`tools/run-daily-content:844` **sem timeout nenhum** (loop de 7 gates, `"./tools/$gate"`
direto). A tabela §10 do runbook lista o tempo deste gate como "não medido" e nunca
dimensiona isto.

**Emenda:** medir o gate com a família populada ANTES de o P6 gravar (basta um
shard de ensaio fora de `v2_pages/`), e indexar/limitar a varredura de pares
(bucket por shingle) — o contrato nomeia "lentidão em 10k é bug P0" e proíbe
aumentar timeout. Sem isso, a etapa 8 da onda diária ganha ~11 min por dia.

---

## A5 — O PASSO 14 EDITA UM CAMINHO QUE 100% DO CORPUS EXISTENTE NÃO PERCORRE

O passo 14 carimba `Atestacao` em `internal/cerebro/extracao.go`, dentro de `extrai()`
(o `if !NormaAtestadaNoTexto(d.Norma, texto)` real está em **:548**, `continue` em
**:550** — o runbook diz :547/:549).

O passo 15 reprocessa o acervo por `cmd/generate-revisao-extracoes`, que chama
**`revisa()` em `:249`** — função OUTRA, com a **sua própria folga idêntica**:

```go
:259   if e.Executor == cerebro.ExecutorParser {
:260       return regeneraLinhaDoParser(e, texto, agora)   // 3º caminho
:261   }
...
:279   if !cerebro.NormaAtestadaNoTexto(d.Norma, texto) {   // a MESMA folga do texto inteiro
:280       nova.DescartadosNormaNaoAtestada++
```

MEDIDO na distribuição do próprio runbook: executores de parser
(`uniao_do_parser_v2` 33.763 + `parser_regenerado_v4` 1.272 + `uniao_do_parser_v1` 546)
= **35.581 de 44.176 linhas = 80,5%**, e essas saem em `:260` antes de qualquer
conferência nova. As demais passam por `:279`, que também não carimba.

Resultado: o campo nunca aparece no corpus reprocessado; o passo 16 mede **zero
mudança**; e a regra de parada pré-registrada lê "empate dentro do erro da amostra
⇒ segue sem creditar ganho". Falha segura, mas o operador conclui "a ideia é inerte"
quando o fato é "editei a função errada". É o precedente "Guarda pela metade" e
"Ausência de sinal não é evidência".

**Emenda:** uma função só — `cerebro.AtestacaoDaNorma(norma, textoCitado, texto) string`
— chamada nos **três** sítios (`extrai()`:548, `revisa()`:279, `regeneraLinhaDoParser`).
É literalmente o que o comentário de `extracao.go:552-556` exige: *"Mesma funcao do
parser — uma forma so no projeto, senao os dois produtores divergem no mesmo texto."*

---

## A6 — O GABARITO CONGELA UM STRIDE POSICIONAL SOBRE ARQUIVO QUE CRESCE ENQUANTO SE MEDE

I5/passo 12: *"Stride determinístico sobre os itens com `urn` não vazio"*, congelado,
e o passo 16 remede "contra o mesmo gabarito congelado".

MEDIDO: `grep -c "" data/ai/extracoes_dispositivos.jsonl` = **44.176** hoje, contra
os **44.153** do runbook: **+23 linhas**. O arquivo está `M` no git status, é
append-only, e `wikijuridica-cerebro.service` está `active running` escrevendo 24/7.
Pior: o próprio passo 15, com `--aplicar`, **acrescenta** linhas revisadas entre as
duas medições.

Stride por índice sobre arquivo que cresce seleciona **população diferente** na
segunda passada. O runbook mede antes e depois em duas populações e atribui a
diferença à correção — o precedente que ele mesmo cita ("antes/depois entre árvores
diferentes não atribui nada", "Amostra enriquecida mede o enriquecimento").

**Emenda:** o gabarito grava a **identidade** de cada um dos 100 itens
(`texto_sha256` + `norma` + `artigo`), e o I4 no passo 16 seleciona **por esse
conjunto de identidades**, nunca por índice. Se um item desapareceu, ele conta como
classe à parte, não é substituído.

Correlato: `data/corpus/jurisprudencia/stj-espelhos/` tem **54 arquivos** hoje, não
os 52 do passo 7 — o stride "6 de 52" que deriva o regex do fallback precisa ser
re-rodado sobre 54, ou é amostra de outra data. (`data/legal-corpus/*.json` = **29**,
esse confere.)

---

## A7 — `git add` FORA DO LOCK, E `-w 600` MENOR QUE QUEM SEGURA O LOCK

Passo 9: `git add <caminho exato>` e **depois**
`flock -w 600 /tmp/opt-wiki-agent-heavy.lock git commit -F <mensagem>`.

MEDIDO: `wikijuridica-qualidade-diaria.service` rodou hoje
`ExecMainStartTimestamp=04:48:12` → `ExecMainExitTimestamp=05:48:54` = **60 min 42 s**,
e a unit é `ExecStart=/usr/bin/flock /tmp/opt-wiki-agent-heavy.lock /opt/wiki/tools/run-qualidade-diaria`
— segura o lock a passada inteira. Próxima largada: **04:47:17 de 2026-09-16**.

Disparado nessa janela, `flock -w 600` **desiste em 10 min sem rodar o commit**, e o
índice fica com os arquivos Go **staged**. Essa é exatamente a condição que o
contrato precifica: closure de 77,6 s com o índice sujo contra 14,9 s limpo — o custo
cai em quem commitar depois. O passo 9 só prevê "índice sujo" como causa de vermelho,
nunca como **consequência** do seu próprio timeout.

(Conferido, e aqui o runbook está CERTO: o lock de commit deste repo é mesmo o
`agent-heavy` — `docs/OPERACAO_COMANDOS_E_CAMINHOS.md:415`, `tools/pre-voo:225`.
`grep` por `opt-wiki-commit.lock` em tools/ ops/ docs/ = **zero**.)

**Emenda:** pegar o lock primeiro e fazer add+commit dentro dele, com espera do
tamanho de quem o segura:
`flock -w 5400 /tmp/opt-wiki-agent-heavy.lock bash -c 'git add <caminho>; git commit -F <msg>'`
— ou `flock -n` e abortar **antes** de estagiar.

---

## A8 — TRÊS CORREÇÕES, UM CENSO SÓ: A ATRIBUIÇÃO SE PERDE NO PASSO 8

§0.3 decompõe eixo por eixo (B, C, D isolados) — disciplina exemplar. O passo 8
a abandona: um censo depois das **três** correções, diffado contra o censo do passo 2.

Mas a correção 2 (remover `pisoEmentaPalavras`, `main.go:532-533` — conferido) **aumenta
a população que chega ao anti-molde**, então `molde_acima_do_limiar` se move por
correção 1 (régua) **e** por correção 2 (mais candidatos) ao mesmo tempo. E
`aceitas` cresce dentro da passada (`main.go:296-299`), então o filtro é guloso e
dependente de ordem: mudar a população muda o contador mesmo com a régua parada.

**Emenda:** três censos `-seco -limite 99999` com `time` — um após o passo 4, um
após o 6, um após o 7 —, cada delta com uma causa só. E o mesmo `-limite` nos dois
lados de cada comparação.

---

## A9 — `internal/ptbrtext` ESTÁ NO GRAFO DO VALIDADOR E A PROIBIÇÃO NÃO O NOMEIA

MEDIDO: `./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock`
= 452 deps, 98 `portaljuridico/*`. **No grafo:** `internal/quality`,
`internal/legalsignature`, **`internal/ptbrtext`**. **Fora:** `v2bodyneardup`,
`cerebro`, `checks`, `stjacordaos`, `generate-acordao-pages` — a conclusão "P4/P5
não pagam reatestação" **confere**.

Mas a tabela §1 proíbe editar só `quality` e `legalsignature`, e a linha de PROVAS
nomeia os três e diz *"por isso EDITAR esses dois primeiros e proibido"* — deixando
`ptbrtext` de fora da proibição. E `cmd/generate-acordao-pages/main.go:859` é
`func contaPalavras(texto string) int { return len(ptbrtext.BodyWords(texto)) }`.
O passo 5, no SE NÃO VIER, manda resolver "divergência residual no separador ou no
`TrimSpace`" — que é precisamente onde se estica a mão para `ptbrtext`. Esse toque
custa `generate ./internal/v2ingest` + atestação no mesmo commit + 25 testes depois
de ~10 min.

**Emenda:** acrescentar `internal/ptbrtext` à linha de proibição, com a razão.

---

## A10 — I2 NÃO TEM ORÁCULO ÚNICO: OS DOIS GATES NÃO MONTAM O MESMO CORPO

§0.1 lista `AssembleBody` para um gate e `corpo_v2` para o outro, e o passo 4 manda
espelhar `AssembleBody` enquanto I2 compara com "`corpoCanonicoDoGate`".

MEDIDO — não são a mesma string:

- `tools/check-derived-authorial-floor:402-420` (`corpo_v2`): `.strip()` em **cada
  parte** e descarta vazias.
- `internal/v2bodyneardup/neardup.go:157-176` (`AssembleBody`): descarta vazias,
  **não faz strip**; junta com `"\n"` sob `if i > 0 && body != ""`.

Qualquer `sections[].text` com espaço nas pontas produz strings diferentes. E os
tokenizadores também divergem: o gate usa `_NAO_PALAVRA = [^\w\s]` (o `\w` do Python
**mantém** `_`), o gerador usa `[^\p{L}\p{N}\s]` (**troca** `_` por espaço).

**Emenda:** nomear UM oráculo — `corpo_v2`, já que `limiarMolde`/`shingleMold` do
gerador são copiados justamente desse gate (`main.go:96-103`) — e I2 asserta contra
um `corpo_v2` reescrito à mão com strip por parte. Manter as duas provas por mutação.

---

## A11 — DERIVA DE LINHA: onde o runbook manda ler não é onde a coisa está

Nenhuma bloqueia execução (grep recupera), mas num runbook o número é a instrução.
MEDIDO vs runbook:

| runbook | real |
|---|---|
| `corpoDaPagina` em `:715`, `:799` | **:711**, **:795** (`:294` e `:2318` conferem) |
| `DispositivoExtraido` `:50-56` | **:52-57** |
| `NormaAtestadaNoTexto`/`continue` `:547`/`:549` | **:548**/**:550** |
| `if len(posicoes) == 0` `:1113` | **:1114** (`reItemDeEmenta` em :1106 confere) |
| cortes de saída `:1679`/`:1682` (e `:1679`/`:1681`) | **:1678** `corpo_abaixo_da_banda_do_verbete`, **:1681** `comentario_proprio_abaixo_do_piso` |
| `check-v2-body-near-duplicates` threshold `:41` | **:42** |
| anchor-claim `:85-94`/`:96-106`/`:109-115` | `termos` **:83**, `carregar_corpus` **:95**, `texto_do_artigo` **:107** |

Confere: `pisoEmentaPalavras=250` em `:402` usado em `:532-533`; `-seco`/`-limite`
(default 30) em `:185-186`; `break` do limite em `:271-272`; `main_test.go:274` é o
controle do `4242`; `internal/quality/quality.go:84 = 0.82`; `measure-molde-trigrama`
lê o FAQ por `question`/`answer` (defeito real); `check-extracoes-dispositivos` é
read-only (só `json.dumps` para stdout); `/api/v1/citar` existe com campo
`html_sha256`; `httpserver.go:1071` é `buildAPIPublishedPages`; flags
`--aplicar`/`--preservar-em` de `generate-revisao-extracoes` existem (`:51-52`);
`tools/check-load-headroom --max` existe.

---

## A12 — O PASSO 11 ESPERA UM VALOR QUE O LOG NUNCA ESCREVE (`warm=false`)

Passo 11: *"DEPOIS: linhas com `warm=false`."*

MEDIDO no `access.log` de hoje (legível: `id -nG` tem **adm**, o arquivo é
`www-data adm`):

- `LC_ALL=C grep -icE 'GPTBot|PerplexityBot|ClaudeBot|OAI-SearchBot|Googlebot'` = **466**
- dessas, com `warm=false` literal: **0 de 466**
- o que realmente sai nas três primeiras linhas de bot: **`warm=-`**

Causa em `ops/nginx/wikijuridica.conf:61`: o formato é
`warm=$http_x_warming_request`, e nginx renderiza cabeçalho **ausente** como `-`,
nunca como `false`. O aquecedor manda o cabeçalho; o bot não manda nada.

Um operador que filtre ou exija `warm=false` lê **zero** e conclui que os bots de IA
não estão entrando — o inverso exato da verdade, e o precedente literal de
"Varredura com campo inexistente: `dict.get` com chave errada lê vazio e 'zero
ocorrências' vira medição falsa". O runbook acerta o `LC_ALL=C` e acerta o
`grep -c` contra `grep -oE`, e então inventa o valor do campo.

**Emenda:** o predicado de "tráfego real" é `warm=-` (cabeçalho ausente); ou, mais
robusto, `grep -v 'warm=true'`. E declarar o número como "466 de 466 linhas de bot
com `warm=-` hoje".

---

## A13 — O PASSO 17 NÃO TEM CAMINHO DE DADO: O CLASSIFICADOR NUNCA VÊ AS EXTRAÇÕES

Passo 17: *"`tools/generate-v2-publication-severity` passa a ler `atestacao` e a
classificar `texto_inteiro`/`nenhuma` como MÉDIO"* — escrito como ajuste de uma linha.

MEDIDO: `grep -nE "dispositivos|extracoes|atestacao" tools/generate-v2-publication-severity`
= **zero linhas**. O gerador de severidade **não lê** `data/ai/extracoes_dispositivos.jsonl`
hoje, nem nada derivado dele. A severidade é por PÁGINA; a atestação é por ITEM de
extração de ACÓRDÃO. Não existe junção página→acórdão→item nesse programa, e o
único elo candidato é `internal/stjacordaos/writeback.go`, que escreve URNs no
registro do corpus — o runbook nunca confere se ele carrega `texto_citado` ou a
atestação.

É o artefato que um passo supõe e nenhum passo gera (frente 6). Sem ele o passo 17 é
irrealizável como escrito, e o seu "DEPOIS: a fila cresce; a contagem de críticos não
muda" não pode ser observado.

**Emenda:** o passo 17 tem de declarar a junção antes de prometer a classificação —
qual chave liga item de extração a `intent_id` de página —, e se a junção não existir,
o passo certo é "a atestação vira sinal na fila de refino
(`data/editorial/v2_rewrite_queue.jsonl`), não campo de severidade".

---

## A14 — O PASSO 15 QUEBRA UM DATASET **PÚBLICO** COM TESTE DE IGUALDADE EXATA

O `--aplicar` do passo 15 acrescenta linhas revisadas a
`data/ai/extracoes_dispositivos.jsonl`. Esse arquivo **alimenta um dataset servido ao
público**:

- MEDIDO no disco: `public/datasets/extracoes-dispositivos-20260915.jsonl.gz`,
  **3.554.623 bytes**, escrito **06:54** de hoje (e as versões de 13 e 14).
- Produtor: `ops/systemd/wikijuridica-grafo-juridico.service:47`
  `ExecStartPost=-/opt/wiki/tools/generate-datasets-publicos` (com `-`: falha ignorada).
- `tools/test_datasets_publicos.py:146-160` (`test_extracoes_ultima_linha_por_chave`)
  compara o dataset com a **última linha por `chave`** do arquivo-fonte, e a
  comparação é do **registro inteiro**: `json.dumps(r, sort_keys=True)`.

Logo, no instante em que o passo 15 acrescenta linhas (com o campo `atestacao` novo),
a última-linha-por-chave do arquivo deixa de ser a do `.gz` já publicado, e esse teste
fica **vermelho** — e o `.gz` que está no ar passa a ser uma versão anterior do dado.
O runbook não regenera o dataset, não roda esse teste, e nem menciona que as extrações
são artefato público. Precedente: "Teste escrito antes do artefato regenerado —
regenere o artefato gerado ANTES de escrever a asserção que o consulta".

MEDIDO também: nem `run-qualidade-diaria` nem `run-daily-content` invocam
`test_datasets_publicos.py` (grep = zero) — o vermelho não aparece na bancada diária,
só quando alguém rodar à mão. Ou seja, a incoerência fica **silenciosa**.

**Emenda:** no mesmo commit do passo 15, rodar `tools/generate-datasets-publicos` e
`python3 tools/test_datasets_publicos.py`, e registrar que `public/datasets/*.jsonl.gz`
ganha campo novo (mudança de esquema de um artefato público, a anunciar). A extensão
`.jsonl.gz` já existe em `public/`, então **não** há questão de allowlist nova.

---

## O QUE O RUNBOOK ACERTA E NÃO DEVE SER MEXIDO

- **Nenhuma decisão volta ao dono**, nenhum cadastro, nenhuma revisão humana de
  esteira. O gabarito é explicitamente mecânico. Frente 7: limpa.
- **Nenhum dano de SEO**: P4/P5 não publicam, não re-datam, não purgam. O passo 10
  já proíbe republicar e purgar — a emenda A1 só acrescenta "nem reiniciar".
- **Rollbacks são para frente e funcionam**: `corpoParaMolde` volta a delegar numa
  linha; `Atestacao` é `omitempty`; a revisão é append-only com `--preservar-em`
  (flag conferida). Nenhum `git reset/checkout/stash/clean/revert`.
- `-seco` é read-only de fato (`main.go:214-218`, `executar` retorna antes de
  `gravaPortfolio`/`gravaShard`) — VERIFICADO por leitura, como o runbook diz.
- O censo exigir `-limite 99999` está certo: o `break` de `:271` corta a contagem.
- §0.6 tem razão: `measure-molde-trigrama` mede corpo SEM FAQ (`question`/`answer`
  contra `q`/`a`) e não serve de oráculo.
- A conclusão "P4/P5 não pagam reatestação do validador" está **medida e correta**.
- **Todos os comandos do passo 9 existem.** `tools/check-v2-body-near-duplicates`
  existe (wrapper de 272 B) e passa pelo `run-go-cmd-cached`, que injeta
  `-tags devcmds` (`:1660`) — sem o qual o `cmd/` com `//go:build devcmds` não
  compilaria. `cmd/generate-acordao-pages` e `cmd/generate-revisao-extracoes` **não**
  têm build tag, então `go-modern run` neles funciona. `tools/check-load-headroom --max`,
  `--aplicar`, `--preservar-em`, `-seco`, `-limite` — todos conferidos.
- O log do passo 11 **é legível** pelo operador (`id -nG` inclui `adm`).

---

## O QUE O ADVISOR MUDOU

Chamei o `advisor` com o relatório A1–A11 já durável em disco. Ele não derrubou
nenhuma das onze, e mudou quatro coisas:

1. **Corrigiu o alvo da emenda A1.** Eu apontava `127.0.0.1:8088` como "a origem";
   ele lembrou que o nginx tem `proxy_cache wj_dyn` em `/api/v1/*` e que a minha
   sonda só veio fresca por sorte. Medi então o **Go em `127.0.0.1:8089`**
   (`4c575009…`, correto) e reescrevi a emenda para a autoridade sem cache. O mesmo
   teste também **refutou** a hipótese de "processo Go velho" que eu estava
   perseguindo: o boot (12:30:27) é posterior ao manifesto (12:28:57) e o Go serve o
   hash certo — a culpa é só do `s-maxage=3600` da Cloudflare.
2. **Rebaixou meu "~650 s" de A4 a extrapolação indevida.** Os 106,3 s são a passada
   inteira, que também lê 11.357 arquivos de `public/`; eu não separei a parte
   O(n²). Reetiquetei como teto superior e mantive só o que medi (5,4× em pares,
   ~3,7 M tuplas, gate sem timeout).
3. **Mandou fechar quatro lacunas de frente 1 que eu não tinha coberto**, e três
   viraram achado novo: **A12** (`warm=false` não existe no log: 0 de 466 linhas de
   bot; o nginx escreve `warm=-`), **A13** (o `generate-v2-publication-severity` não
   lê as extrações — grep = zero — logo o passo 17 não tem caminho de dado) e **A14**
   (o passo 15 quebra o teste de igualdade exata de um dataset **público** em
   `public/datasets/`). A quarta checagem **absolveu** o runbook: o wrapper
   `tools/check-v2-body-near-duplicates` existe e o `-tags devcmds` é injetado.
4. **Disse onde pôr esta seção**, já que o schema de saída só tem `veredito` e
   `ataques[]`.

Um conselho dele eu **não** segui: rodar o censo `-seco -limite 99999` em background
para medir os 4.763. É leitura, o load está em 7,49 e caberia — mas é o número
central do **P6**, não do P4/P5, e o passo 2 deste runbook já manda medi-lo com
`time`; gastar ~10 min de CPU disputada para confirmar o diagnóstico de outro bloco
não muda nenhuma das quinze emendas. Fica registrado como **não medido, e por
escolha**, não por impedimento.
