# Deploy pendente — 2026-09-10

Preparado por esta sessão a pedido do dono; **a execução final é da sessão par**
(`ai-legal-platform-cache-optimization`), pela ordem dele desta data: *"quando ele
terminar, fala que mandei ele corrigir tudo, inclusive os pre existentes e quando
tiver tudo verde e confirmado com contexto e leitura e medição ele faz o build e
deploy final"*.

Este documento existe para que quem executa não precise redescobrir nenhuma das
decisões abaixo. Cada uma é medida, com o comando que a mediu.

---

## 1. O que está no repositório e ainda não está no ar

| medida | valor |
|---|---|
| páginas no `published_manifest` | **11.039** (`unique_intent_id`) |
| páginas de `leis-motor` commitadas e **não publicadas** | **38** |
| páginas de `stj-tema-derivado` remontadas (texto mudou) | **1.070** |

As 38 são **rota nova**. As 1.070 são rota existente com **texto diferente** — a
camada oficial passou a sair em excertos comentados (commit `c59a570f`).

## 2. `--ressemear`: NÃO, e o motivo é a matriz do §6

| o que mudou | `--ressemear`? | por quê |
|---|---|---|
| texto editorial das 1.070 de tema | **não** | a re-datação é VERDADEIRA: o corpo mudou de fato |
| 38 rotas novas de `leis-motor` | **não** | sob `--ressemear` o IndexNow fica calado (`tools/deploy-publico:997`), e para rota NOVA esse comportamento não está medido em lugar nenhum — apostar nele custaria o anúncio das 38 |
| corpus, gates, seletor, inventário | irrelevante | são dado e ferramenta; não tocam markup, CSS nem script inline |

**Nenhuma mudança de markup, CSS ou script inline entrou nesta leva.** Logo a
folha `/assets/wj-<hash>.css` não muda de bytes e `check-csp-style-hashes` não
fica vermelho.

## 3. Purga de borda: NÃO purgue à mão

```
tail -1 data/ops/edge_cache_purge.jsonl
{"purged_at": "2026-09-09T17:09:12+00:00", "scope": "tudo"}
```

A última purga já foi **`scope: "tudo"`**. Pelo §6, purgar de novo joga fora
~870 s de aquecimento e deixa a borda em `MISS`. A purga que o próprio deploy faz
basta. **E leia o motivo que ele imprime**: se ele disser `purgando tudo`, não
purgue de novo.

## 4. Pré-condição que trava o deploy hoje

`tools/deploy-publico` compila `./cmd/...` **do worktree**. Com Go sujo de outra
frente, o deploy quebra por código de terceiro em edição — é o precedente
`worktree-compartilhado-agente-quebra-deploy`. Confira antes:

```bash
git status --porcelain internal/ cmd/ | wc -l      # tem de estar em zero, ou perto
```

O par pediu explicitamente: **não deployar com `cmd/social` sujo**, porque o
agente da rede social entregou pacote novo (`internal/socialmedia`) e rotas em
`cmd/social`.

## 5. O que fica verde SÓ depois da republicação

- **`tools/check-derived-authorial-floor`, eixo do teto.** Ele lê
  `public/**/index.html`, e `public/` ainda tem as páginas velhas. Depois da
  republicação as 6 páginas acima de `TETO_CITADO = 0.55` desaparecem — medido no
  JSONL com o denominador do gate calibrado: **zero acima de 0,55, zero acima de
  0,50, máximo 0,4981**. O eixo de unicidade, que lê o JSONL, já está verde.
- **`binario-vs-fonte`** e **`crawl-reachability`**, que o par nomeou como os dois
  que só fecham com o deploy.

## 6. Prova depois de publicar

```bash
./tools/check-http-smoke
./tools/check-v2-portfolio-pairing          # tem de continuar exit 0
./tools/check-derived-authorial-floor       # o eixo do teto passa a fechar
./tools/check-caracteres-de-controle        # 18.323 arquivos, exit 0
./tools/check-legal-corpus-contamination    # 8.854 artigos, 0 achados
```

E ler amostra à mão: check verde não substitui ler a página. As rotas novas são
`/{área}/{slug}/` derivadas de `leis-motor-01.jsonl`.

## 7. Commits desta frente que entram nesta publicação

| commit | o que fecha |
|---|---|
| `84cb5d96` | os oito bloqueantes da auditoria adversarial do motor de artigo de norma |
| `e6bdf1e3` | 43 intenções de portfólio que a onda de hoje não conseguiu commitar |
| `95377e39` | as 38 páginas de artigo de norma |
| `7c894fb1` | corpus: art. 359-M do Código Penal de volta, endereço do artigo, 3 gates novos |
| `22583e50` | feed do STF na matriz de fontes |
| `c59a570f` | DEC-032: a camada oficial deixa de sair em bloco único |
| `8511f48a` | clones de terceiro fora da árvore, com inventário e reversão |
| `740c7e4d` | restauração das 290 linhas do inventário de clones que `8511f48a` apagou |
| `773e2574` | este dossiê |

## 8. Os números da seção 1 mudaram em 2026-09-10, depois de dois defeitos achados

O parágrafo original fica; o que ele contava foi superado por medição, e o
motivo está aqui.

**1.070 → 1.074 páginas de `stj-tema-derivado`, mais 70 `h1` de páginas já
publicadas.** A sessão par achou que `cmd/generate-stj-tema-pages` **não era
determinístico**: os mapas de predecessor e de irmão de bloco eram indexados
pelo número puro, e o cadastro numera Tema, IAC, PUIL e Controvérsia em séries
separadas — o vencedor dependia da ordem de iteração do mapa. Corrigido em
`842070dc`/`737f8754`/`6b28ef8e`, com prova de idempotência (duas rodadas, mesmo
sha256 do shard). Enquanto durou, qualquer rodada produzia "texto mudou" falso.

**A trava do DEC-032 continua respeitada depois disso**, e eu re-medi em vez de
supor: sobre as 1.074 páginas do shard commitado, com o mesmo método calibrado
contra os cinco números que o gate imprime e usando a **menor** folga de CHROME
(+106 palavras, isto é, o pior caso para a razão), a razão citada máxima é
**0,5039** (`jur-stj-tema-938`), **zero** páginas acima de 0,55 e **zero**
abaixo do piso autoral de 250 palavras. Duas ficam acima de 0,50, que é o teto
*interno* do gerador — aviso, não reprovação.

**A decisão de `--ressemear` não muda**, e agora por dois motivos em vez de um:
as 1.074 mudaram o corpo, e os 70 `h1` mudaram título e as 24 seções de
predecessor — texto servido de verdade nos dois casos, então a re-datação é
verdadeira e suprimi-la esconderia do buscador conteúdo que mudou.

## 9. Frente do corpus-oráculo, depois deste dossiê

`3151d21a`, `b8f797ee` e `88f2927e` mexeram em `internal/sourcesnapshotaudit`,
`internal/planaltochannel`, `cmd/collect-oracle` e no dado de
`data/source-snapshots`. **Nada disso republica página**, mas muda o que o
gate `source-snapshot-corpus` e o `verify-grounding` respondem no build final.

O que é dívida nomeada com teto escrito, o que é limite externo, e o que muda
em página publicada está em **`docs/goal/CORPUS_ORACULO_ENTREGA_20260910.md`**.
Leia antes de tratar qualquer vermelho de corpus como regressão da publicação.

`0f129470` entra aqui pelo mesmo motivo: ele não republica página, mas é o que
devolveu à cadeia a capacidade de se autenticar. Desde 2026-08-27 um symlink de
`node_modules/.bin/playwright-core` fazia o contrato de código de
`tools/bootstrap-chain` abortar antes do passo 1 (`source contract crosses
symlink`), então nenhum vermelho de corpus podia sequer ser medido pela cadeia.

## 10. Vermelhos que NÃO são desta publicação, e não a seguram

Medido em 2026-09-10: a cadeia de derivados de `data/editorial/` está parada
desde **2026-08-05**, com **38 dos 40 passos** de `tools/bootstrap-chain` mais
velhos que a própria fonte. Os gates que a leem —`public-prose-candidate`,
`scaledcontentreleaseverdict`, `prose-mechanical-quality`,
`ptbr-confusables-quality`, `ptbr-unicode-quality`, `ptbr-pair-rescoring`,
`ptbr-spellcheck` — reprovam por isso, e por nada que esta leva tenha feito.

**Nenhum dos 38 artefatos entra em `public/`**: todos são
`publication_allowed: false`, `render_allowed: false`, `index_policy: noindex`.
Publicar com eles stale serve exatamente o mesmo byte.

A medição completa, a prova de que o commit `6d3623c2` não é a causa, e a razão
de `bootstrap-chain` (teto duro de 600 s) não ser o instrumento do conserto estão
em **`docs/goal/CADEIA_EDITORIAL_PARADA_20260910.md`**. Leia antes de tratar
qualquer um desses sete vermelhos como regressão da publicação.

---

## 11. Segunda leva desta sessão: ortografia e citação legal no que JÁ está no ar

Tudo abaixo foi achado **depois** da republicação de 09:33 desta data, pela
passada exata de `tools/measure-ortografia-publicada --stride 1` contra os
11.287 HTML servidos. São correções de **texto**, então a matriz do §6 manda
deploy **sem `--ressemear`**: a re-datação é verdadeira.

| commit | o que corrige | páginas no ar afetadas |
|---|---|---|
| `c8ff9460` | `Resolucao do Senado Federal nº 9, de 1992` sem acento, no texto do link de Proveniência e no `name` do CreativeWork do JSON-LD | **12** |
| (fronteira de palavra em `internal/legalfacts/norma.go`) | o autolinkador casava `constituição` **dentro** de "desconstituição" e "reconstituição", partindo a palavra e ligando-a à Constituição Federal | **39** |

### Por que as 39 são o mais grave desta leva

O HTML servido traz, literalmente:

```html
o pedido de des<a href="https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"
   rel="external">constituição</a> do aditivo
```

São dois defeitos numa ocorrência só. O leitor vê **palavra partida**
("pedido de des constituição do aditivo"), que o §8 classifica como fragmento
truncado — falha P0. E a citação fica **mal atribuída**: desconstituição de um
aditivo bancário e reconstituição de fatos não têm relação com a Constituição
Federal, e o §5 chama citação mal atribuída de **P1 permanente**, a única classe
com risco real sob a OAB. O JSON-LD publica a mesma âncora, então o erro alcança
a camada de máquina junto.

Medido na árvore servida: `des«constituição»` 18 ocorrências, `re«constituição»`
26 — **44 ocorrências em 39 páginas**.

Causa raiz: `reNomesCompletos` não tinha `\b`. As duas irmãs do mesmo arquivo
tinham (`reNormaComNumero` abre com `\b`; `reAcronimosCurtos` põe `\b` em cada
alternativa). É o mesmo dano que o comentário de `reDispositivoCluster` já
registrava para `art. 452-A` (BUG-115): quem segue o link chega ao dispositivo
errado.

### O que fica verde só depois desta publicação

`tools/measure-ortografia-publicada` continuará listando `des` (16 páginas) e
`Resolucao` (12) enquanto o `public/` for o de 09:33. **Não é defeito a
perseguir** — é a mesma janela declarada que `check-csp-style-hashes` tem contra
o `public/` antigo. Depois de publicar, os dois somem sem tocar em mais nada.

### O que NÃO entra nesta publicação, e por quê

- **`pólo`** (10 páginas): grafia pré-1990, mas dentro de **tese do STJ
  transcrita entre aspas**. Transcrição fica literal — mesma regra do `reconher`
  do `temas.csv`.
- **`br`, `gov`, `ans`, `jurisprudencia`**: texto de URL renderizada como link
  (`gov.br/ans`, `/jurisprudencia/…`). Legitimar `jurisprudencia` sem acento
  cegaria o gate para o erro real em prosa; o conserto certo é o instrumento não
  tokenizar URL, e isso é trabalho de outro dia, nomeado aqui para não sumir.
- **A cauda de 1.216 tokens** de 1 a 9 páginas do censo: **não lida**. Entra em
  allowlist só o que foi lido em contexto; escolher por ordem alfabética é
  exatamente o defeito do `top_misspellings` truncado.

### O número desta seção veio de um par medido sobre a MESMA árvore

A primeira passada exata começou às 09:33, dentro da janela do `deploy-publico`
(12:20:48Z→13:01Z = 09:20→10:01 local): ela leu a árvore **enquanto** os 11.287
arquivos eram reescritos. A aritmética a denuncia sozinha — 47.206 candidatos
com allowlist de 145 termos contra 47.342 com 301 termos, quando acrescentar
termo só pode **diminuir** o conjunto de candidatos. Descartada como base.

O par válido, medido duas vezes sobre a árvore já assentada e variando só a
allowlist por `--raiz`:

| allowlist | candidatos | grafias distintas | faixa ≥ 10 páginas |
|---|---|---|---|
| 145 termos (antes) | 47.570 | 1.406 | 190 tokens |
| 301 termos (depois) | 47.342 | 1.182 | **8 tokens** |

Os oito que restam são `br`, `gov`, `Gov`, `ans`, `des`, `Resolucao`,
`jurisprudencia` e `pólo` — todos nomeados acima como fora de escopo ou já
corrigidos no código e à espera desta republicação.

---

## 12. Ambiente: três venvs estavam ausentes, e o `sca-staticcheck` não tinha onde rodar

Achado em 2026-09-10, e a causa está **fora** do repositório.
`~/.config/pip/pip.conf` desta máquina declara `user = true` no `[global]` — a
instalação padrão do dono, documentada no próprio arquivo. Dentro de um venv o
pip recusa:

```
ERROR: Can not perform a '--user' install. User site-packages are not
visible in this virtualenv.
```

**Nenhum** dos quinze wrappers de `tools/` que criam venv declarava `PIP_USER`,
então todos falhavam ao provisionar ambiente novo. Três venvs estavam ausentes
em silêncio: `.cache/oss-python-venv`, `.cache/python-quality-sca-venv` e
`.cache/zizmor-workflow-security-venv`. O do SCA é o ambiente de `ruff`, `mypy`,
`pip-audit` e `pip-licenses` — o `sca-staticcheck`, primeiro P0 da bancada
diária, **não tinha onde rodar, e ninguém sabia**.

O defeito é invisível até alguém tentar: venv criado ANTES da mudança do
pip.conf continua funcionando, e o wrapper só falha ao criar um NOVO — deixando
um `bin/python` válido e um site-packages vazio, que é o estado mais enganoso
possível.

`666974bd` põe `PIP_USER=0` nos quinze pontos de instalação, com guarda de
regressão em `tools/test_pip_user_em_venv.py`. Os três venvs foram materializados
e conferidos **de dentro de cada interpretador**:

| venv | pins verificados |
|---|---|
| `.cache/oss-python-venv` | `torch 2.12.1+cpu`, `fastembed 0.8.0`, `spacy 3.8.14`, `stanza 1.13.0`, `rapidfuzz 3.14.5`, `warcio 1.8.1` |
| `.cache/python-quality-sca-venv` | `ruff 0.15.20`, `mypy 2.1.0`, `pip 26.1.2`, `setuptools 81.0.0` |
| `.cache/zizmor-workflow-security-venv` | `zizmor 1.26.1` |

`./tools/check-requirements-fixados` passa a sair **exit 0**.

### Dois vermelhos que ficam nomeados, e nenhum é desta publicação

1. **`oss-install-matrix-env` termina exit 101**, DEPOIS de a árvore Python
   inteira ser instalada. É o passo de binários de busca: `tantivy-cli v0.24.0`
   não compila porque a dependência `traitobject` usa
   `unsafe impl Trait for ::std::marker::Sync + Send + Sync`, que o rustc atual
   recusa com **E0119**. `traitobject` está sem manutenção; trocar o backend de
   busca é decisão de arquitetura, não conserto de ambiente. Pré-existente e
   independente do `PIP_USER`.

2. **`check-ptbr-morphsyntax-evidence`** reprova com
   `checked_at stale: expected='2026-09-10' actual='2026-07-15'`. É evidência
   velha, **não** modelo ausente — o plano registrava "8 arquivos do Bosque
   faltando", e com o venv provisionado a causa medida é outra. Regenerável.

## 13. A prova de que as duas correções chegaram ao `public/` (medida 10:55)

A republicação do par escreveu **1.511 páginas entre 10:42 e 10:44** (histograma
de `mtime` sobre os 11.287 `index.html` de `public/`). Sobre essa árvore, os três
números que decidem:

| Padrão no HTML servido | Antes | Depois |
|---|---|---|
| `des<a href` (palavra partida pelo autolinkador) | 16 páginas | **0** |
| `re<a href` | presente | **0** |
| `Resolucao do Senado` (sem acento) | 12 páginas | **0** |

**Zero não basta como prova** — página apagada também dá zero. O controle
positivo, no mesmo passe:

- **48 páginas** trazem `desconstituição`/`reconstituição` INTEIRAS no texto
  visível, e nenhuma delas com a palavra partida. Medido tirando as tags **sem
  inserir espaço**, justamente para que uma palavra partida por `<a>`
  reaparecesse colada e fosse contada.
- **13 páginas** trazem `Resolução do Senado` acentuado.

É a evidência de que `e740f219` (fronteira de palavra em
`internal/legalfacts/norma.go:83`) e `c8ff9460` (ortografia do rótulo do Senado)
chegaram à árvore servida, e não só ao shard.

**Nota de honestidade sobre o 12 × 13:** o gerador do Senado trocou o rótulo em
12 páginas; a árvore servida tem 13 com a forma acentuada. A décima terceira já
estava correta antes e nunca passou pelo gerador — o número da troca continua
12, o da cobertura é 13, e são grandezas diferentes.

**E `public/index.html` NÃO serve de sinal de republicação:** o `mtime` dele
ficou em 09:33:28 durante uma passada que reescreveu 1.511 páginas. Página cujos
bytes não mudam não é reescrita. O sinal certo é o histograma de `mtime` ou o
ledger do deploy.

## 14. Achado novo, na mesma família da fronteira de palavra: 28 colagens no texto do STJ

Enquanto o deploy do par rodava, varri o HTML servido por um padrão que o censo
de ortografia **não enxerga** — o tokenizador dele quebra em `.`, então
`presumida.Assim` entra como `presumida` + `Assim`, duas palavras corretas.

**No ar:** 26 formas, **28 ocorrências, 17 páginas**, todas em
`/jurisprudencia/stj-tema-*`, dentro do trecho que a própria página anuncia como
"A transcrição é literal". Exemplos: `presumida.Assim` (Tema 875, ×2),
`públicas.II` (1402, ×2), `mínimo.Tese` e `legal.Proposta` (1080),
`conversão.Tese` e `moratórios.Proposta` (66), `julgada.Não`, `decisão.A`,
`geral.As`, `indiretas.No`, `monetária.No`, `previdenciária.As`, `públicos.As`,
`tributária.A` (905), `medida.IV` e `criminal.II` (1249), `gravoso.II` (1325),
`ambientais.D` (IAC 13), `valoradas.V` (710).

**A causa não é nossa.** Na fonte coletada de hoje
(`data/research/daily/stj-precedentes/2026-09-10.jsonl`, 1.197 registros) o mesmo
padrão aparece **51 vezes em 18 temas**, repartido por campo: `tese_firmada` 43,
`questao_submetida` 7, `delimitacao_julgado` 1. O coletor lê a célula do CSV
oficial com `strings.TrimSpace` e nada mais (`cmd/collect-stj-precedentes/main.go:247`).

**A medição que decide o que é isso**, na mesma fonte e nos mesmos campos:

| Fronteira de frase | ocorrências |
|---|---|
| com espaço | 125 |
| com quebra de linha | 5 |
| **colada, sem nada** | **16** |

O par decisivo é o Tema 118 com `segurança.\n\nTese` contra o Tema 1080 com
`salário-mínimo.Tese` — **a mesma expressão** ("Tese após revisão"), uma com
quebra e outra sem nada. É quebra de linha perdida no export do STJ, não grafia.

**Por que isto NÃO é o precedente do `pólo` nem do `reconher`.** Aqueles são
GRAFIA dentro de aspas, e o §8 manda transcrever com o erro do original — o
próprio gerador escreve essa doutrina em `main.go:2419-2437`. Aqui não muda
palavra nenhuma: é espaço em branco. E o gerador **já normaliza espaço na
transcrição** — `limpa()` faz `strings.Join(strings.Fields(v), " ")`
(`main.go:2360`), que é exatamente o que transforma as 5 quebras de linha em
espaço antes de a citação chegar ao leitor. Restaurar o espaço onde a quebra se
perdeu aplica a MESMA regra que já está no código, de forma consistente.

**Onde a correção entra, e onde ela NÃO entra.** Não em `limpa()`: ela é a
normalização genérica do gerador e alimenta identidade — chave de
`blocosDeJulgamento` (comentário em `main.go:1603` exige texto BYTE-IDÊNTICO),
piso de 15 palavras (`:1618`), `chaveDoPrecedente`, `teseAindaNaoPublicada` e o
título. O lugar é `citador.transcreve`
(`cmd/generate-stj-tema-pages/excertos_comentados.go:976`), que é o funil ÚNICO
dos cinco campos oficiais e onde já existe uma transformação declarada da
citação (`semAspasCurvas`).

**O efeito colateral medido, e é um só:** `transcreve` decide repartir em
excertos por `len(strings.Fields(limpo)) >= minPalavrasParaReparte` (60,
`excertos_comentados.go:134`). Simulando a restauração campo a campo nos 18
temas, **exatamente uma** contagem cruza o limiar: Tema 1402,
`questao_submetida`, **59 → 60**. Todas as outras 27 sobem dentro da mesma faixa.

**Controles negativos obrigatórios do teste** (os dois últimos vieram da sessão
par): `consumidor.gov.br` · `Fala.BR` · `J.Silva` · `S.A.` · `D.O.U.` ·
`art.5º` · `inc.II` · `Lei n.11.101` — abreviação jurídica colada casa o mesmo
padrão e **não** pode ganhar espaço, senão o autolinkador perde o dispositivo.

**A guarda de regressão tem casa:** o eixo entra em `internal/publichtmlshape`
(`cmd/check public-html-shape`), que já varre os 11.288 HTML por forma de prosa —
gerador datado sem eixo deixa a classe voltar em silêncio.

### 14.1 Emenda aos números da §14, e o motivo: a guarda escondia o que ela filtrava

Os números da §14 vieram de um padrão **estreito** — `letra{2,} + ponto +
Maiúscula`, com uma lista de domínio de topo filtrando o rótulo seguinte. Os dois
recortes cobravam preço:

1. **O padrão exigia duas letras antes do ponto e não aceitava `)`.** Ficaram de
   fora `(...do CDC).Tese B)` (Tema 10, 2 casos), `(nota do risco de
   crédito).II` e `(lei do cadastro positivo).III` (Tema 710) e
   `.../2011.IV - Apesar` (dígito antes do ponto, Tema 710).
2. **A guarda de domínio de topo trazia `com`, e isso era pior.** `Com` abre
   frase em português jurídico o tempo todo — "Com efeito,", "Com base nisso" —
   e `entendimento anterior.Com efeito` é exatamente a colagem que a regra
   existe para restaurar. Com `com` na lista ela passaria **em silêncio**; e,
   como TODAS as varreduras carregavam `if rótulo_seguinte in TLD: continue`, a
   própria medição não poderia tê-la visto. O filtro escondia o que filtrava.

**Remedido com a guarda desligada**, imprimindo os rótulos seguintes reais:

| Onde | Total sem guarda | `.BR` (nome de serviço) | Colagem de verdade |
|---|---|---|---|
| Fonte coletada de hoje | **55** | 0 | **55** |
| HTML servido | **55** | 25 (`Fala.BR`) | **30, em 17 páginas** |

Nenhum `.Com`, `.Org` ou `.Net` existe em nenhum dos dois lados. A lista ficou
com **um elemento, `br`**, e é a única medida.

**Os números corretos, que substituem os da §14:** 30 ocorrências publicadas em
17 páginas (não 28), e 55 na fonte (não 51, e a linha "colada" da tabela é 55,
não 16). A §14 fica como está, com esta emenda ao lado — o padrão estreito
produziu os primeiros, e dizer qual padrão produziu qual número é o que permite
ao próximo leitor não ter de adivinhar.

**Correção da mesma classe no censo de ortografia, e ela custou três iterações.**
Os cinco tokens de maior alcance do censo exato — `br` (1.658 páginas), `gov`
(1.604), `Gov` (69), `ans` (16) e `jurisprudencia` (10) — não eram erro nenhum:
saíam de o tokenizador quebrar `Consumidor.gov.br`, `(Inep/gov.br)`, `".bet.br"`
e `/jurisprudencia/stj-tema-1261/`. Cada rodada matou uma forma e deixou um
sobrevivente que só a rodada seguinte viu:

| Rodada | O que faltava | Sobreviventes |
|---|---|---|
| 1 | regra de endereço inexistente | `br` 1.658 · `gov` 1.604 · `Gov` 69 · `ans` 16 |
| 2 | `/` na guarda de contexto barrava `(Inep/gov.br)` | `br` 7 · `gov` 1 |
| 3 | ponto inicial de `".bet.br"` não era aceito | `br` 6 |
| 4 | nome de arquivo em prosa (`robots.txt`, `datasets.json`, `index.md`) | — |

**Censo exato sobre a árvore de 11.051 páginas publicadas, depois das quatro:**
47.302 candidatos, **1.158 fora do dicionário**, 2.588 domínios + 43 caminhos +
2 URLs ignorados, e o token de maior alcance passou a ser **`pólo` (10 páginas)**
— a grafia literal da tese do Tema 193, que fica no ar de propósito.

### 14.2 Duas correções ao que ficou escrito nos commits `9c90547f` e `da5f3922`

**A primeira: o cruzamento de limiar do Tema 1402 NÃO aconteceu.** As três
mensagens (o commit do código, o do shard e o aviso à sessão par) dizem que o
efeito colateral previsto "se confirmou". O diff semântico não sustenta isso: em
`jur-stj-tema-1402` mudaram duas inserções de espaço e mais nada — `word_count`
459 antes e depois, 3 blocos entre aspas antes e depois, 5 seções antes e depois.

**A causa, lida no código:** a primeira montagem chama
`novoCitador(intentID, false, 1, …)` (`main.go:1924`) — `reparte = false`. A
repartição em excertos só existe na passada de escalonamento (`:1979`), que só
acontece quando a razão citada estoura o teto. O Tema 1402 está em 0,336, muito
abaixo, então `minPalavrasParaReparte` **nunca é consultado nessa página**. A
contagem cruzou de 59 para 60 palavras, e o limiar não governava nada ali.

A previsão estava certa sobre a aritmética e errada sobre a consequência. O que
de fato aconteceu é mais contido do que eu previ: **as únicas duas páginas cuja
diagramação mudou são as duas que já estavam em modo de repartição** — 905 e 996.

**A segunda, e esta é para quem publica: a razão citada do Tema 905 SUBIU.**
Medida sobre os dois shards (`da5f3922` contra `da5f3922^`), contando palavras
dentro de `“…”` sobre o corpo:

| Página | antes | depois | delta |
|---|---|---|---|
| `jur-stj-tema-905` | 0,5489 | **0,5793** | **+0,0304** |
| `jur-stj-tema-996` | 0,5178 | 0,5109 | −0,0069 |
| `jur-stj-tema-1402` | 0,3361 | 0,3361 | 0 |

A causa é direta: com as fronteiras de frase restauradas, `reparteOficial`
produziu 18 blocos citados em vez de 13, e as elisões `[…]` — que antes
**deixavam texto oficial de fora do corpo** — deixaram de ser necessárias. Mais
texto citado entrou.

**Esta medida é um proxy, e o número que o gate usa é outro.** A régua de
`check-derived-authorial-floor` monta o corpo como h1 + títulos + abertura +
seções + FAQ, e o próprio gerador, com essa régua, reporta **0,529 contra o teto
de 0,55** — passa, e é o valor a citar. O proxy acima serve para a **direção**,
que é o que faltava: eu tinha medido só o estado final e declarado "passa", sem
dizer que a margem encolheu.

**Consequência prática:** `jur-stj-tema-905` é a página a vigiar na publicação.
`citacao_acima_do_teto_do_corpo` está na lista que a §2.4 do plano chama de
inegociável, e o gate só mede `public/` — ele **não** enxerga o shard, então o
número só aparece depois de publicado. Quem publicar confere essa página primeiro.

## 15. O vermelho de morfossintaxe: não era carga, era o corpus 13,5× maior

`check-ptbr-morphsyntax-evidence` reprova com
`checked_at stale: expected='2026-09-10' actual='2026-07-15'`. A §12 registrava
"evidência velha, regenerável". **Regenerável ela não era**, e a causa está
medida.

**O que o gerador faz.** Além das 4 amostras de diagnóstico que o `--limit`
governa, ele roda um **passe de release sobre o corpus inteiro** —
`load_corpus_samples(source_path, 0, ...)` em
`scripts/ptbr_morphsyntax_oracle.py:229`, onde `0` significa *todos* os
registros. Cada registro e cada segmento passa por spaCy (POS + NER, parser
desligado), e as frases que o spaCy marca como sem verbo passam por Stanza.

**Por que estourou.** O commit `944a40fa` (2026-07-09) mediu **116 s** para esse
passe e escreveu, no próprio corpo, *"escala a 10k"*. Não escala — e o número
que prova isso é o tamanho do corpus naquele commit:

| | registros | bytes de `refined_public_prose.jsonl` |
|---|---|---|
| `944a40fa` (2026-07-09) | 590 | 5.295.507 |
| hoje | 7.959 | 86.519.453 |

**13,5× mais registros.** Medido em execução direta pelo venv, **fora do
envelope**, com a máquina em load 6–7: **1.347 s de parede a 94% de CPU e
1.323.904 kB de RSS — e ainda não tinha terminado quando eu o encerrei**, então
1.347 s é piso, não total. O custo POR registro caiu (0,197 s no N=590 contra
menos de 0,17 s hoje); o que cresceu foi o corpus.

**Contra o que isso bate:** `WIKI_HEAVY_BUDGET_MS=180000` no wrapper, teto duro
de **540 s** do `run-heavy-throttled`
(`expected duration must not exceed effective command timeout (540000ms)`) e teto
de **600 s da `tools/bootstrap-chain` inteira**, que roda este gerador como passo
(`bootstrap-chain:69`). Nenhum dos três cabe. A evidência parou em 15/07 porque
não havia como regenerá-la.

**Duas leituras minhas que caíram no caminho, e ficam registradas:**

1. **"É carga."** Falso: a segunda tentativa deu `PIPESTATUS=124` com load 6–7,
   e a execução direta mostra 94% de CPU contínuos. É trabalho, não espera.
2. **"A declaração do envelope está errada, é só corrigi-la."** Também falso, e
   pior: era a resposta que o §4 do contrato proíbe. O `944a40fa` escreveu a
   regra certa para si mesmo — *"Proibido corrigir com timeout maior; corrige-se
   com menos trabalho"* — e foi ela que apontou a saída.

**A correção é menos trabalho, e ela existe porque o corpus é inerte.** A análise
de release já é **por registro** (`analyze_record_spacy_only_from_docs` devolve um
dicionário por registro; os agregados são somas), e o plano já mediu
`refinement_changed: false` em 7.959 de 7.959. Registro que não mudou não precisa
ser reanalisado.

- **Cache endereçado pelo conteúdo** em `.cache/ptbr-morphsyntax-release-cache.jsonl`,
  com a chave incluindo o texto, cada segmento, o teto de caracteres e a
  **identidade dos motores** (spaCy, modelo, Stanza, torch). Cache que ignorasse a
  versão do motor devolveria o veredito do motor velho depois de um upgrade — que
  é o falso verde que este oráculo existe para impedir.
- **Falha ABERTA para recomputar**: qualquer erro de leitura descarta o cache
  inteiro. `--sem-cache` força a passada completa, para auditoria.
- **`--release-lote N`** limita quantos registros NOVOS uma execução analisa. O
  resto vem do cache. Quando o lote acaba antes do corpus, o cache é gravado, o
  **artefato não é escrito** e o processo sai com **exit 3** — não é sucesso e não
  é defeito, é progresso. É assim que uma passada de ~1.300 s volta a caber no
  envelope de 540 s e no teto de 600 s da cadeia, **sem que nenhum registro deixe
  de ser analisado**.
- O cache guarda a análise **já fechada**, depois do dual-engine, porque o
  veredito do Stanza sobre um texto é determinístico. Guardar o candidato em vez
  do veredito faria o Stanza rodar sobre o corpus inteiro a cada execução.

**E as quatro dicas de bootstrap mandavam para um comando que não funciona.**
`tools/check-oracle-liveness` (2×), `tools/check-ptbr-morphsyntax-evidence` e
`tools/requirements_interpretadores.json` diziam
`generate-ptbr-morphsyntax-evidence --limit 0`. Medido no código: `--limit 0`
significa **todos os 7.959 registros como amostra de diagnóstico**
(`oracle.py:580`), e `validate_record` (`:1047`) recusa o artefato porque
`requested_corpus_sample_limit` não bate com o padrão 4 do verificador. As quatro
passam a apontar `--release-lote 1`, que aquece o venv sem produzir registro
inválido.

**Sizing medido do lote, para o próximo agente não ter de descobrir.** Rodando o
oráculo direto pelo venv com `--release-lote 1`: **39,77 s de parede, exit 3** —
é o custo fixo de carga (spaCy + Stanza + torch) mais o passe de diagnóstico das
4 amostras. O passe de release custa pouco mais de 0,17 s por registro. Logo,
dentro do orçamento declarado de 180 s cabem ~800 registros novos por execução, e
o corpus inteiro aquece em cerca de catorze fatias. **`--release-lote 600` é a
fatia usada aqui**, com folga.

**E o exit 3 não vira vermelho em lugar nenhum, o que foi conferido e não
presumido:** `tools/run-qualidade-diaria` classifica 75 como `infra` e 124 como
relógio, e **não chama este gerador**; quem o chama é `tools/bootstrap-chain`
(passo 20), onde uma fatia parcial deve mesmo interromper o passo. O aquecimento
é fora de banda, que é o que a memória `cadeia-aquecimento-standalone` já manda:
aquecer o produtor fora e usar a cadeia só para autenticar.


## 16. O fecho da frente de morfossintaxe, e as três coisas que a medição achou no caminho

### 16.1 O gate fechou, e fechou com o corpus inteiro

`./tools/check-ptbr-morphsyntax-evidence: pass`, `duration_ms=16594`. Era o
vermelho mais antigo da bancada — `checked_at` de 2026-07-15, 57 dias.

| campo | antes | agora |
|---|---|---|
| `checked_at` | 2026-07-15 | **2026-09-10** |
| `input_records` | 590 | **7.959** |
| `release_covered_records` | 590 | **7.959** |
| `release_from_cache` | — | 7.801 |
| `release_computed_now` | — | 158 |

Treze fatias de `--release-lote 600`. **A passada que não cabia em 180 s agora
custa 16,6 s**, e caiu porque o trabalho caiu: nenhum registro deixou de ser
analisado. É o que o §4 do contrato manda — perf se corrige por menos trabalho,
nunca por timeout maior.

**A cobertura completa achou o que a amostra de 590 não via:**
`release_blocked_record_count: 2` — um `sentence_without_verb` e um
`terminal_preposition`, em
`refined-public-prose-authorial-mass-draft-v2-cons-pagamento-pix-loja-nao-entregou`
e `...sum-stj-221`. São registros da camada `refined_public_prose`, que nasce
`StatusBlocked` por desenho: **não há página publicada com esses dois defeitos**.
É o eixo fazendo o que existe para fazer, com nome de registro e código.

### 16.2 O laço de aquecimento lia o exit do `tail`, e quase me fez declarar vitória falsa

O primeiro laço trazia `rc=$(cmd 2>&1 | tail -2); rc=${PIPESTATUS[0]}`. Dentro de
`$( … | tail )` o `PIPESTATUS` do subshell **não sai dele**: o `rc` medido era o
do `tail`, sempre 0. O laço imprimiu **"ARTEFATO ESCRITO na fatia 1"** com o
cache em 601 linhas e o artefato ainda em 15/07.

É a memória `shell-exit-code-pipelines` uma camada mais fundo do que ela costuma
morder: eu **usei** `PIPESTATUS[0]`, mas dentro de uma substituição de comando,
onde ele mede o processo errado. **O mesmo erro derrubou o commit** que eu tinha
lançado com `flock -w 1800 … | tail -5`: o `flock` desistiu em 1.800 s sem pegar
o lock, saiu 1, e a tarefa reportou exit 0. O commit não existia e eu achava que
sim.

Reescrito sem pipe, com `$?` direto, **e com uma segunda condição de parada**:
cache que não cresce entre fatias interrompe o laço — para não repetir vinte
vezes um erro real.

### 16.3 O acoplamento que a próxima sessão precisa saber

`refined_public_prose.jsonl` (7.959 linhas) **é a entrada do oráculo**, e
`check-public-prose-candidate` está vermelho com `records=7959 expected=7984`: a
cadeia editorial está 25 registros atrás de `authorial_mass_drafts.jsonl`.

**Regenerar a cadeia reabre a morfossintaxe**, porque `input_records` e
`input_fingerprint` mudam. O conserto é barato — o cache é endereçado por
conteúdo, então as 7.959 chaves seguem válidas e só os 25 novos custam análise —
mas só se a ordem for respeitada:

```
1. regenerar public_prose_candidate / refined_public_prose
2. ./tools/generate-ptbr-morphsyntax-evidence     (~16 s + os 25 novos)
3. ./tools/check-ptbr-morphsyntax-evidence        (tem de dar pass)
4. commit do artefato
5. deploy
```

## 17. A frase colada saiu do canal de tema e apareceu no de súmula

O eixo `glued_sentence` de `internal/publichtmlshape` foi de **17 para 1** contra
a árvore servida estável (`records=11288 issues=63 indexable=11284 noindex=4`).

As dezesseis que fecharam são do canal de tema, por `52b29cd9`. Conferido por
leitura e não pelo número: das 8 amostras que o eixo gravava, **8 de 8** têm o
espaço restaurado no HTML servido.

**A que sobrou é de outro gerador, e esse é o achado.**
`public/sumulas/stj-573/index.html` — "não pode ser presumida.Assim, a data de
emissão". `cmd/generate-stj-sumula-pages` tem o **seu próprio `limpa()`** e nunca
passou pelo `citador.transcreve`. Mesma causa raiz na fonte (a exportação CSV do
STJ perde a quebra de linha do acórdão), família de código diferente.

Corrigido com o **mesmo** `internal/fronteiradefrase`, nos cinco pontos que
interpolam texto oficial entre aspas — tese, questão, delimitação, referência
legislativa e referência sumular. **Fora do `limpa`**, que alimenta
`corta(limpa(tema.Questao), 160)` (a meta description) e
`primeiraFrase(limpa(...))` (a abertura); **fora do `AnchorClaim`**, que é
proveniência e tem de espelhar os bytes da fonte. Cinco mutantes, um por ponto,
todos mortos.

**O eixo continua CONTADO, não bloqueante, e é decisão e não omissão:** o `1` não
é defeito em aberto — é defeito corrigido esperando publicação. Virar o eixo agora
reprovaria o acervo por algo que o próximo deploy resolve. O compromisso datado em
`internal/publichtmlshape/shape.go:543` vale: quando der 0 na árvore servida, ele
vira, e o teste que hoje prova a CONTAGEM passa a provar a REPROVAÇÃO.

### 17.1 Medir o primeiro defeito expôs um segundo, maior

O shard de súmula **trocava de ordem a cada execução**. `numeros` nasce de
`range porSumula` — iteração de mapa — e `sort.Slice` não é estável, com dois
critérios que empatam muito (`riqueza` tem cinco valores possíveis para 138
súmulas).

Medido: duas execuções do mesmo binário com a mesma entrada deram **zero
registros diferentes e 92 das 112 linhas trocadas de lugar**.

O custo de review é chato. O de produção é sério: `tetodelote` corta a lista no
`-limite`, e cortar dentro de um empate faz **qual página inédita entra no lote
virar sorteio** — o mesmo comando publicando páginas diferentes.

**Varredura da família inteira, sem esperar a terceira ocorrência:**

| gerador | veredito |
|---|---|
| `generate-stj-sumula-pages:366` | **corrigido** — terceiro critério: o número da súmula |
| `generate-diario-pages:417` | **corrigido** — quarto critério: a chave `UF\|data` |
| `generate-noticia-pages:300` e `:922` | já totais (desempatam pela própria chave, única) |
| `generate-diario-pages:1001` | já total |
| `generate-stf-informativo-pages:382` | `SliceStable` sobre lista lida de arquivo, não de mapa |
| `generate-stj-tema-pages:317,826,1637` | idem, e as duas últimas desempatam por data + número |

**Separar o que é meu do que é da fonte, antes de commitar:** rodando o código de
HEAD contra a entrada de hoje, o meu código altera **1 registro** (`sum-stj-573`,
delta de 1 byte). Os títulos de `sum-stj-547` e `sum-stj-558` também mudaram e
**não são meus** — vêm do dump de 2026-09-10.

## 18. O art. 151 do CTN tem dez incisos, e duas páginas diziam seis

Fatia acordada com a sessão par, que mediu 40 páginas citando o art. 151 e
recortou as que **enumeram** — citar o artigo não ficou errado; enumerar seis de
dez e afirmar taxatividade produz afirmação **falsa**.

Conferido na fonte primária antes de qualquer edição: `data/legal-corpus/ctn.json`,
buscado de `https://www.planalto.gov.br/ccivil_03/leis/l5172.htm` em
`2026-09-10T08:56:35Z`, `document_sha256 4bf75ac9…`. Dez incisos — **VII a X
incluídos pela LC 236/2026**, e **III e V com redação nova** da mesma lei. O
recorte da sessão par listava VII, VIII e IX; **o X também é dela**.

Sem marca de `(Vigência)` nem de `(Produção de efeito)` em nenhuma das 173
menções à LC 236 no consolidado. O que o próprio Código condiciona foi para a
página **como o Código diz**: VII a IX "nos termos da legislação específica", X
"nos termos da regulamentação estabelecida pelos órgãos de cobrança judicial".

**A taxatividade não se tocou** — rol taxativo alterado por lei complementar
continua taxativo, só que maior.

Por gerador datado (`tools/generate-v2-ctn-art151-lc236-20260910`), escrita
atômica, idempotente, com guarda por marca: a frase que a correção **remove** tem
de estar lá, senão ele aborta. `word_count` recomputado por
`tools/generate-v2-word-count-refresh`, que usa a fórmula canônica do gate —
duplicar a tokenização seria a segunda implementação que diverge.

`guia_problema` tem banda 700–1400 com tolerância de ±10%, isto é **630–1540**: a
página estava em 644 e ficou em 695, dentro antes e dentro depois.

### 18.1 A citação da LC 236 não resolve, e a lacuna é de corpus

`POST /api/v1/citacoes` com o corpo das duas páginas devolve
`lei-ref:lei.complementar:236` com `resolvida: false`, e
`grep -ac 'lei.complementar:2026;236' data/source-snapshots/manifest.jsonl` = **0**.

`resolvida: false` significa "este pacote não consegue verificar contra fonte
oficial" (`api_citacoes.go:90-96`), não "citação inventada" — súmula, tema e
precedente nascem `false` por desenho, e `artigo:art151` já era `false` antes.

**O texto não muda por causa disso.** A afirmação está provada pelo consolidado do
CTN que é a `official_sources` das duas páginas. Tirar o nome da LC para agradar o
parser esconderia proveniência; inventar URN seria fraude. **O conserto é pôr a
LC 236/2026 no corpus** — e aí as duas páginas resolvem sem tocar numa vírgula.

## 19. Um detector acusava 100% do acervo, e a causa era um link

`check-text-truncation` reprovava com **22.236 ocorrências em 11.287 de 11.287
páginas**, a home junto. O cabeçalho do próprio gate registrava que, depois da
calibração de 2026-08-26, R1 media ~zero.

A causa: desde `52631d4c` (2026-09-05) o render emite em toda rota
`<p><a href="/redesocial/">Rede social jurídica do portal…</a></p>` e, nas de
tema, `<p><a>Página deste tema na rede social do portal</a></p>`. Agrupando os
trechos acusados, **esses dois textos respondiam por tudo**. O commit que os
introduziu já se chamava "e a família de detectores que ele cegava".

A isenção de rótulo já cobria `<li>` link-only pela **mesma** causa medida em
2026-08-26 (80 acusações, 80 falsos positivos). Estendida a `<p>` com a condição
inalterada — o bloco inteiro é uma âncora e nada mais (`so_ancoras == txt`).
Prosa com link no meio continua exigindo pontuação final.

**De 22.236 para 1. E a isenção não escondeu nada: ela revelou.** O sobrevivente é
real e está numa página que o §11 do contrato nomeia — `/bot/` renderiza
`<p>User-agent: WikijuridicaBot Disallow: /</p>`, **duas diretivas de robots.txt
na mesma linha**, porque o corpo em `content/pages.json:1008` as separa com `\n`
simples e o render colapsa isso em espaço. A página que existe para dizer ao
operador como nos bloquear estava dando a instrução errada.

Não corrigido por mim, e o motivo é escopo de arquivo: `content/pages.json` tinha
trabalho não-commitado de outra frente no disco, e commitá-lo por pathspec levaria
junto o que não é meu. Passado à sessão par, que já abriu
`tools/generate-pagina-bot-robots-em-lista-20260910`.

Sete casos de autoteste novos chamam `e_rotulo` **diretamente**, com o HTML
interno real — separados de `CASOS_AUTOTESTE` porque aquele conjunto chama
`analisa_blocos`, que recebe blocos **já filtrados** por `e_rotulo`; testar a
isenção por lá seria testar o filtro pelo lado em que ele não age. Três são
controles negativos.

**E o cabeçalho ficou mentindo por um commit.** `54603753` mudou o código e não o
texto que dizia "em `<p>` exige-se pontuação final SEMPRE" e "roda 12 casos". R1
diz que comentário que mente é bug; corrigido em `77c28870`, com a remedição
datada e sem apagar a linha de 2026-08-26.

## 20. O que ficou vigiado, e o que saiu da vigilância

**Saiu:** `jur-stj-tema-905`. Eu havia pedido vigilância porque um proxy meu media
a razão de citação em 0,5793 contra o teto de 0,55. O gate próprio diz outra
coisa: `check-derived-authorial-floor: OK`, `texto citado: min 3.3% | mediana
19.0% | max 52.3% (teto 55%)`. **O máximo do acervo inteiro é 52,3%** — a página
não cruza, e o número que vale é o do gate, não o do proxy. Comentário autoral:
min 298, mediana 360, máx 1190 (piso 250). Nenhum molde se repete: máximo por
canal 0,6787 contra limiar de 0,70.

**Fica:** o eixo `glued_sentence` até a próxima publicação, e a ordem da §16.3 se
alguém regenerar a cadeia editorial.

## 21. A guarda de falha upstream do OSS invalidava pelo relógio, e a causa era o DNS

`f4087db4` fez a matriz OSS voltar a rodar guardando as falhas conhecidas por
24 h, com invalidação por troca de rustc. Para o `tantivy-cli` a chave é exata:
o `rustc` é a única variável do E0119 numa cadeia abandonada em 2018. Para o
`quickwit` é a chave errada — a causa registrada é `install.quickwit.io` ter
saído do DNS, e trocar de compilador não muda nada nisso. O host podia voltar às
9h e a guarda continuaria pulando até as 16h27 do dia seguinte.

`b83b0ceb` amarra a invalidação à **causa**: a guarda só se levanta quando o
motivo do registro mais novo casa um marcador **e** a precondição daquela causa
diz que ela se desfez. Para o quickwit é `getent hosts` no host derivado da
própria URL — 0,01–0,05 s medidos em três amostras.

**O par marcador+precondição não é cerimônia.** Sem ele, um quickwit que
voltasse ao DNS e falhasse por outro motivo passaria a pagar um `curl` a cada
invocação para sempre — inclusive dentro da sonda de identidade do Go do
`run-go-cmd-cached`, que é exatamente o custo que a guarda existe para não
pagar.

**E o motivo registrado tinha de acompanhar.** Medido com a URL apontada para um
host que resolve: o texto era fixo, dizia "saiu do DNS" depois de a instalação
ter falhado por rejeição do override, e o marcador voltava a casar — o retry
virava laço. A linha nova passa a dizer qual das duas causas ocorreu.

O autoteste (`WIKI_OSS_AUTOTESTE=1`, 12 casos) subiu para **antes** do
provisionamento: teste que paga o provisionamento inteiro para conferir uma
decisão de milissegundos não entra em suíte nenhuma.
`tools/test_oss_install_matrix_env_cache_negativo.sh` entra pela descoberta por
glob do passo 2c-bis e mata cinco mutantes — marcador ignorado, rustc ignorado,
TTL ignorado, registro mais antigo em vez do mais novo, e motivo fixo. Custo do
wrapper inalterado: **0,18–0,27 s** contra os 0,310 s de `f4087db4`.

**E o `missing_count: 0` de 2026-07-05 não estava errado: estava não medido.**
Conferi o registro anterior de `data/ops/oss_installation_matrix_evidence.jsonl`
— `missing_dependency_ids: []`. O `lighthouse` não foi reportado antes e
ignorado; ele nunca chegou a ser procurado, porque a sonda estourava o teto
antes. É a mesma frase do `check-normative-fingerprint-selftest`.

## 22. `check-public-prose-candidate` diz "faltam 25" quando o desencontro é de 445

A sessão par mediu por conjunto e eu reproduzi no disco, com
`unique_intent_id`:

```
authorial_mass_drafts      7.984 linhas / 7.984 ids
public_prose_candidate     7.959 linhas / 7.959 ids
refined_public_prose       7.959 — conjunto IDÊNTICO ao candidate

só em drafts     235      só em candidate     210
```

O gate reprova com `records=7959 expected=7984`. **O degrau de 25 é o líquido de
uma troca de 445 registros**, e quem lê o número planeja o trabalho errado:
"gerar 25" deixaria 235 intenções sem prosa e 210 candidatas órfãs.

**As 445 já estão publicadas — todas.** Conferi contra o `published_manifest`
(11.039 `unique_intent_id`): 235/235 e 210/210 têm página no ar. Então isto não é
fila de publicação nem página faltando; é **cobertura de derivação**.

**A causa é única, e o arquivo prova:** os 7.959 registros do disco carregam
**um único** `input_fingerprint_sha256` (`0943498303…`), e o gate já acusa
`public_prose_candidate_input_fingerprint_mismatch`. O derivado é um instantâneo
coerente de um `authorial_mass_drafts` anterior. Os dois lados da diferença têm
a mesma explicação: o que entrou no estoque depois (235) e o que saiu dele (210).

**E o derivado não ficou para trás hoje — ficou há um mês.** A sessão par cobrou
a ressalva e eu medi: `drafts_expected` está em **7.984 desde `ea559b13`
(2026-09-10T12:00Z)**, vinha de 7.985 em 2026-09-09 e de **7.972 em 2026-08-30**;
a transação de hoje (`accepted=7984 rejected=3201`) *reafirmou* o número, não o
moveu. Do outro lado, `public_prose_candidate.jsonl` foi gerado por último em
torno de **2026-08-12** (`501109ea`) — o `f44aaf65` de hoje é edição cirúrgica de
mojibake, não regeração, e o `input_fingerprint_sha256` do HEAD é o mesmo
`0943498303…` do disco. Então as 445 são a soma de um mês de movimento da cadeia,
e não o efeito de uma passada. Isso muda o **prazo** do conserto, não o conserto:
regenerar continua sendo o que fecha, com a ordem da §16.3.

**O relator de conjunto JÁ EXISTE e está morto atrás de um early-return.**
`internal/publicprosecandidate/public_prose_candidate.go:2970` (`freshnessIssues`)
emite `public_prose_candidate_unexpected_record` e
`public_prose_candidate_missing_record` **por id** — que é exatamente a medição
que faltava. Só que `:427` o condiciona a `len(inputIssues) == 0`, e hoje
`inputFingerprintIssues` dispara para os 7.959. O detector que eu esperava ver
nunca executa: é o padrão `ausencia-de-sinal-nao-e-evidencia` outra vez, e o que
sobra na saída é a cardinalidade, que subestima 445 como 25.

**Duas frentes separadas, e nenhuma some:**

1. **Instrumento.** Quando o fingerprint de entrada diverge, o gate ainda tem de
   dizer o tamanho verdadeiro — `so_na_fonte` e `so_no_derivado` com contagem e
   amostra, derivados dos ids do estoque (leitura barata), sem reconstruir a
   prosa. É Go em `internal/publicprosecandidate`, **fora da janela do deploy
   #4** porque `deploy-publico` compila do worktree.
2. **Dado.** Regenerar a cadeia é o que fecha o desencontro — e reabre o portão
   de morfossintaxe: a ordem da §16.3 vale integralmente (regenerar →
   `generate-ptbr-morphsyntax-evidence` → `check-ptbr-morphsyntax-evidence` →
   commit → deploy).

## 23. O eixo `glued_sentence` virou — o compromisso datado foi cumprido no mesmo dia

`internal/publichtmlshape/shape.go:543` escreveu de manhã que o eixo nasceria
**contado e não bloqueante**, e fixou a condição de virada: `glued_sentence_files
== 0` na árvore servida. Medido contra os 11.288 HTML que o deploy #4
republicou:

```
antes  glued_sentence_files=1  public/sumulas/stj-573/index.html
                               ", não pode ser presumida.Assim, a data de emissã"
agora  glued_sentence_files=0  glued_sentence_samples=null
```

O único sobrevivente era a página que `transcricao()` corrigiu no gerador de
súmulas; a publicação levou a correção ao disco. Com 0 arquivos, ligar o bloqueio
**não reprova o acervo** — passa a reprovar a CLASSE na próxima vez que ela
tentar nascer. `public-html-shape: pass`, `blocking_issue_files: 0`, e os 62
`issue_files` restantes são todos `heading_preposition_chain`, que segue contado
pela nota datada em `validateRecord`.

O parágrafo antigo não foi apagado: ficou com data e motivo, porque é ele que
explica por que o eixo passou por dois estados. E o teste trocou de sentido junto
— `TestFraseColadaEhContadaENaoBloqueia` virou `TestFraseColadaReprova`, com a
asserção anterior registrada no corpo. Dois mutantes mortos, e o segundo importa
porque a virada de um eixo não pode arrastar o vizinho: a cadeia de preposição
continua contada. `f98eaf17`.

**Um controle negativo que eu escrevi e retirei.** Criei um teste novo para a
cadeia e, ao rodar a mutação, vi que `TestCadeiaDePreposicaoContaMasNaoBloqueia`
já cobria exatamente o mesmo — inclusive o `FileAudit` com os quatro contadores
em 1. Segunda implementação da mesma verificação diverge no dia em que uma ganha
um caso que a outra não tem. Retirado.

## 24. O eixo de cobertura, e os dois erros que ele cometeu antes de acertar

`cf0a7722` faz o gate dizer o tamanho verdadeiro do desencontro: 235 só no
estoque, 210 só no derivado, contra o degrau de 25 que a cardinalidade anunciava.
A previsão foi **declarada antes de rodar** (§22) e o gate imprimiu exatamente
`only_in_stock=235 only_in_records=210`, com amostras que batem com a medição
independente em Python.

**Só que a primeira execução imprimiu `only_in_stock=0 only_in_records=7959`**, e
eu parei em vez de ajustar o esperado. As duas causas valem mais que o conserto:

1. **`LoadRecords` é a leitura errada para pertinência.** Ele aplica refinamento
   de paid-intent e valida o lote, e volta com 7.984 registros **e**
   `report.Passed() == false`, por um
   `authorial_mass_stock_paid_refinement_orphan_draft_id`. Refinamento muda
   CAMPO, não pertinência. `LoadBaseRecords` é a leitura certa — drafts +
   expansão, sem refinamento e sem validação — e é a barata (1,79 s a frio).
2. **Eu tinha engolido o relatório.** A primeira versão devolvia `nil` quando o
   report reprovava, e o resultado foi um eixo que se dizia medido e lia estoque
   vazio como "o derivado inteiro sobra". É o mesmo early-return que este eixo
   existe para consertar, cometido dentro do conserto. A falha virou
   `public_prose_candidate_stock_coverage_unavailable`, com nome.

**E a advertência que veio antes do código evitou o terceiro:** o eixo tem de ser
cego à quarentena da promessa (DEC-024). `expectedCount` já a desconta duas
linhas acima; contá-la como `only_in_stock` reintroduziria o elo insatisfazível
que o comentário de `:226` registra ter encerrado. Com o ledger em **0 linhas**,
esse falso positivo nasceria **dormente** e acordaria na primeira página
quarentenada, quando ninguém lembrasse do patch. Entrou com teste próprio e
controle negativo.

**Parede, medida antes e depois:** 9,62 s → 12,6–13,6 s. As 47,8 s da primeira
execução eram o *rebuild* do pacote, não o gate — separar as duas coisas foi o
que impediu de tratar um custo de compilação como regressão de escala. Os ~3,5 s
são pagos **só no ramo em que o gate já está vermelho**: com o derivado fresco,
`inputIssues` é vazio e o eixo não roda.

Quatro mutantes mortos: isenção da quarentena, lado único da troca, amostra sem
corte, e entrada de ledger sem intent isentando.

## 25. A ordem da regeneração não é folclore: está declarada em `tools/bootstrap-chain`

A memória desta máquina diz que a cadeia editorial tem "~9 artefatos com ordem
obrigatória que o repo não declara", e que a parada de 2026-08-05 custou 31 dias
por causa disso. **Metade dessa frase está superada, e o conserto do §22/§24
depende de saber qual metade.**

Medido: `internal/` declara **59 artefatos** de `data/editorial/` com
`OutputRelPath`, e o acoplamento é cobrado por `..._artifact_stale` com a
mensagem `OutputRelPath older_than <input>` — a aresta existe no código, uma a
uma. E a **ordem topológica está declarada**, posicionalmente, em
`tools/bootstrap-chain`: `STEP_ARTIFACTS` e `STEP_BINARIES`, **42 passos**, com o
comentário dizendo que *"a posição é o contrato: um passo sem output explícito
não pode ser pulado por `--from`"*.

Os três passos que interessam ao desencontro de 445 (índice 1-based do `--from`):

```
passo 12  generate-public-prose-candidate   data/editorial/public_prose_candidate.jsonl
passo 13  generate-refined-public-prose     data/editorial/refined_public_prose.jsonl
                                            + data/ops/refined_public_prose_generation_witness.json
passo 26  (ptbr)                            data/ops/ptbr_morphsyntax_evidence.jsonl
```

**É por isso que regenerar reabre o portão de morfossintaxe, e agora com o
número do passo em vez da lembrança:** a evidência de morfossintaxe é o passo
**26**, catorze passos DEPOIS do candidato. Regenerar o 12 invalida tudo o que
vem abaixo dele na lista, e o `check-ptbr-morphsyntax-evidence` é um dos que
recomeçam. A sequência da §16.3 está confirmada pela própria ferramenta, não só
pela memória.

**O que continua verdadeiro da memória:** o teto duro de tempo por passo
(`refined_public_prose.jsonl` é o único artefato no
`BOOTSTRAP_REUSE_POOL_ARTIFACTS`, preservado por CÓPIA entre tentativas porque
"sem o pool, cada retomada do refined recomeçava do zero e nenhuma rodada cabia
no teto de 540 s/passo"). Então a regeneração se aquece por produtor, fora da
cadeia, e a cadeia autentica — que é exatamente o que a memória
`cadeia-aquecimento-standalone` registra.

**Não roda hoje, e o motivo é de ordem, não de coragem:** o ciclo #5 da sessão
par está para disparar e a cadeia reescreve derivados de `data/editorial/` que o
publicador lê da worktree. Fica como o próximo item desta frente, com o
procedimento já derivado em vez de um ponteiro vago.

## 26. O gate de escala OSS revela um stale por vez, e por isso ninguém viu o tamanho

Três evidências foram remedidas hoje porque o gate as nomeou, uma depois da
outra, a cada execução: `source_fetch_resilience` (2026-07-05),
`bigcache_byte_cache` (2026-08-29) e `official_pdf_probe` (2026-07-05) —
`50607636` e `0cda63cc`. Nenhuma sai para a rede: cenários roteirizados em
memória, cache local e atestação de capacidade do `pdfcpu`, somando menos de
2 s. A de resiliência **declara o próprio modo**
(`evidence_mode: synthetic_resilience_proof_not_live_recheck`), que é o que a
separa de número inventado.

**Cada uma revelava a seguinte, e foi isso que me fez medir a lista inteira em
vez de continuar puxando o fio.** `internal/ossscaleintegration/coverage.go`
declara **41** artefatos de evidência. Censo do último registro de cada um:

| estado do último registro | quantos |
|---|---|
| `checked_at: 2026-09-10` | **3** |
| `checked_at` de 2026-06 | 25 |
| `checked_at` de 2026-07 | 6 |
| `checked_at` de 2026-08 | 5 |
| sem o campo `checked_at` | 1 (`sca_license_overrides.jsonl`) |
| carimbo RFC3339 em vez de data | 1 (`x_net_html_blocked_sample_parser_evidence.jsonl`, `2026-06-19T12:17:07-03:00`) |

**A frase honesta é "38 de 41 cujo último registro não carrega
`checked_at: 2026-09-10`"**, e não "38 desatualizadas": dois dos 41 usam esquema
diferente, e tratá-los como se fossem o mesmo campo repetiria o erro de instrumento
que este dossiê já nomeou quatro vezes hoje.

**Um dos três atuais é `ptbr_morphsyntax_evidence.jsonl`** — o eixo fechado nesta
sessão. É o único membro da família que está em dia, e é por isso que o censo
mede o acervo em vez de acusá-lo.

**E regenerar as 38 NÃO deixaria o gate verde.** Três das cinco áreas que ele
reprova falham por pino de versão, não por frescor:

```
roaring-shard-bitmaps      github.com/RoaringBitmap/roaring/v2  got=v2.25.0  want=v2.14.5
roaring-postings-dedupe    idem
dense-pairset-roaring64    idem
gosec-sca-static-analysis  github.com/securego/gosec/v2         got=v2.29.0  want=v2.27.1
staticcheck-sca-bugfinding honnef.co/go/tools                   got=v0.8.1   want=v0.7.0
gofeed-demand-feed-parser  github.com/mmcdole/gofeed            got=v1.4.2   want=v1.3.0
```

O registro pina versões que o `go.mod` já ultrapassou. Mexer em qualquer um dos
dois lados é **ADR** — dependência que afeta runtime, com licença, versão fixada
e benchmark —, não varredura. Fica nomeado com o número, não consertado às
pressas com um ciclo de deploy na fila.

**O que isto acrescenta ao §21:** lá o instrumento estava cego e dizia
`missing_count: 0`. Aqui ele enxerga, mas mostra **um por área**, então o
tamanho do acervo parado só aparece para quem for medir a lista — e ninguém
tinha ido. É a mesma família, na forma "vê certo e mostra pouco".

## 27. O registro afirmava a versão de adoção, e a asserção que devia guardar isso não era testada

`oss-scale-integration-coverage` reprovava quatro integrações por
`module_version_mismatch` e eu classifiquei isso como **ADR**. Errado, e a
sessão par refutou com a citação certa — que eu conferi por leitura própria:

```
policy.go:1753 (roaring)  "upgraded to v2.25.0 on 2026-08-26 with no API change
                           at the two call sites (import and roaring.New)"
policy.go:2498 (gofeed)   "upgraded to v1.4.2 on 2026-08-26 ... with build and
                           package tests green"
c30979b8 (2026-08-26)     mede o risco do gofeed: o `Parse` do v1.4.x detecta o
                          tipo nos primeiros 4 KiB, o único uso é
                          demandobservations.go:4586, e os fixtures trazem o
                          marcador `jsonfeed.org` no byte 25 — folga de 4.071
```

A decisão existia, com data e risco medido. O que ficou para trás foram
constantes afirmando a versão de **adoção** contra um `go.mod` que dizia outra
havia duas semanas — a mesma classe do comentário que mente (R1), numa
constante. `314735ee`.

**E a par errou por simetria, o que vale registrar:** ela concluiu que o gofeed
não tinha ADR **depois de procurar só no histórico do `go.mod`**. O registro
estava no arquivo de política, que é onde ele devia estar. Concluir da ausência
sem cobrir onde a coisa mora é o `ausencia-de-sinal-nao-e-evidencia` outra vez —
e desta vez o catálogo pegou o erro de quem o escreveu.

**A causa da recorrência era a CÓPIA, e ela só existe onde o registro copia em
vez de ler.** `coverage.go:1232,1250` já liam
`roaringpostings.ModulePath`/`ModuleVersionPinned` — por isso as três
integrações de roaring caem juntas ao consertar **uma** constante. Mas
`scaleindex` repetia a string em dois pontos, o que dava dois lugares para
lembrar a cada subida; agora referencia a fonte única. O **gofeed não tem
constante para ler**, então a versão dele continua escrita à mão em
`coverage.go:3085` — dito aqui em vez de redescoberto em outubro.

**O achado que justifica o commit sozinho: a asserção não era testada.** Medi o
mutante ANTES de escrever o teste — retirar a metade `BitmapVersionPinned` de
`ValidateRecord` (`index.go:574`) **não reprovava um único teste da bancada**. A
metade `BitmapModule` era coberta de graça, porque o módulo nunca muda; a
versão, que é a que muda, não tinha guarda. Foi por isso que pôde ficar duas
semanas errada sem ninguém notar.
`TestValidateRecordRejeitaVersaoDeBitmapDivergente` mata o mutante, com controle
negativo.

**Os testes ficam com literal, de propósito.** Assertar
`record.X != pkg.Constante` contra produção que faz `record.X = pkg.Constante` é
tautologia: não pode falhar. O literal é o que obriga a confirmação deliberada a
cada subida.

**Armadilha que uma varredura teria criado, registrada porque o número é o
mesmo:** `"v1.3.0"` aparece em três lugares e **dois não são o gofeed** —
`internal/rapidpropertyfuzz/evidence.go:25` e `policy.go:2015` são
`pgregory.net/rapid` (MPL-2.0, test-only). Um `sed` casaria os três e mudaria a
versão declarada de uma dependência que ninguém decidiu mexer.

**O que este commit deixa VERMELHO, e por quê.**
`data/ops/scale_index_benchmark_evidence.jsonl` continua em 2026-07-07 dizendo
v2.14.5, então `scale-index-benchmark` passa a acusar
`scale_index_sidecar_contract_invalid`. Não dá para regerar, e a tentativa
revelou a cadeia inteira atrás:

```
generate-scale-index-benchmark          -> scale_index_ensure_failed:
                                           scaled_content_release_verdict.jsonl: no such file
generate-scaled-content-release-verdict -> scaled_content_release_verdict_
                                           public_prose_language_patterns_stale  records=7959
```

O verdict depende do `public_prose_language_patterns` — **passo 16 da
`bootstrap-chain`, abaixo do candidato do passo 12 que está um mês atrás** (§22 e
§25). É o desencontro de 445 aparecendo por outra porta. O check já estava
vermelho por `scale_index_live_layer_evidence_failed`, mesma causa raiz; o que
muda é que **antes a evidência e a constante concordavam numa versão falsa**, e
agora a divergência está à vista. Mesmo padrão do eixo de forma: coerente
consigo mesmo e errado.

**Medido depois:** os quatro `module_version_mismatch` de roaring e gofeed saíram
do gate. Sobram `osv-scanner` (v2.5.1/v2.4.0) e `cyclonedx-gomod`
(v1.12.0/v1.10.0), de outra frente, e ali **não basta trocar o `want`**: os dois
trazem `evidence_module_missing` junto, isto é, a evidência aponta o módulo na
versão antiga e tem de ser regravada com a versão que rodou.

## 28. A árvore do #5, medida com os dois números juntos

O compromisso do §23 era medir `glued_sentence_files` **e**
`blocking_issue_files` depois da publicação seguinte, porque o modo `trecho:`
grava prosa literal que **não passa pelo funil `internal/fronteiradefrase`** — ao
contrário dos geradores de súmula e tema, onde `transcricao()` é o funil — e o
eixo virou bloqueante no meio do caminho.

```
input_html_files            11.288
glued_sentence_files             0     glued_sentence_samples   null
blocking_issue_files             0     blocking_issue_samples   []
issue_files                     62     todos heading_preposition_chain
```

E a correção chegou ao **ar**, não só ao shard:
`public/tributario/iptu-imunidade-entidade-templo/index.html` traz "impugnações,
os recursos e a manifestação de inconformidade… previstos no inciso III na
redação da Lei Complementar 236, de 2026", com **zero** ocorrências da redação
revogada.

## 29. O verdict não sumiu numa regeneração: foi apagado em 2026-07-09

A §27 afirmou, no corpo e na mensagem de `314735ee`, que
`scale-index-benchmark` **já estava vermelho** por
`scale_index_live_layer_evidence_failed` antes da minha mudança. Era inferência
a partir do arquivo ausente — e afirmação numérica por inferência é o que R3
proíbe. Medi:

```
git ls-files --error-unmatch data/editorial/scaled_content_release_verdict.jsonl
  error: pathspec ... did not match any file(s) known to git
git cat-file -e 314735ee~1:data/editorial/scaled_content_release_verdict.jsonl
  fatal: path ... does not exist in '314735ee~1'
git log --diff-filter=D --oneline -- data/editorial/scaled_content_release_verdict.jsonl
  3f36df9c fix(escala+prosa): cadeia N=590 — global_similarity aceita corpus limpo ...
git show --stat 3f36df9c -- data/editorial/scaled_content_release_verdict.jsonl
  1 file changed, 209 deletions(-)
```

`3f36df9c` é de **2026-07-09 13:14:02 -0300** e é ancestral de HEAD. O insumo do
check saiu do repositório **dois meses antes** do meu commit, num commit que
regenerou a cadeia a N=590 e cuja própria mensagem registra que o passo 12
(refined) ficou surfando uma família de detectores de prosa. É a mesma cadeia
parada que a §22 e a §25 nomeiam, vista de um terceiro ângulo.

**O que isso corrige na §27:** a frase "já estava vermelho" passa de inferência a
fato datado, com o commit que o produziu. E o que ela NÃO passa a dizer: que o
vermelho seja irrelevante. Ele é o mesmo bloqueio da cadeia editorial, e só a
regeneração a partir do passo 12 o resolve — trocar o pino do bitmap nunca ia
resolvê-lo, e o commit não afirmou que resolveria.

## 30. A evidência não estava velha: o registro copiou a versão em sete lugares

A §27 fechou os quatro `module_version_mismatch` de roaring e gofeed e deixou
`osv-scanner` e `cyclonedx-gomod` para a outra frente, com uma frase minha que
**medi agora e é falsa**: *"os dois trazem `evidence_module_missing` junto, isto é,
a evidência aponta o módulo na versão antiga e tem de ser regravada com a versão
que rodou."*

`data/ops/sca_toolchain_evidence.jsonl` já traz a versão certa nas três linhas:

```
sca-osv-2026-08-30       module_path .../osv-scanner/v2/cmd/osv-scanner  module_version v2.5.1
sca-licenses-2026-08-30  module_path .../cyclonedx-gomod/cmd/...         module_version v1.12.0
sca-sbom-2026-08-30      idem                                            v1.12.0
```

**Por que os dois códigos aparecem juntos, lido no detector:**

```go
// coverage.go, evidenceRecordMatchesIntegration
if pair.version != integration.ModuleVersion { continue }
// coverage.go, evidenceIdentityPathMatches
for _, candidate := range []string{integration.ModulePath, integration.UseNeedle, integration.ToolPath} {
```

O caminho da evidência **já casa** — é exatamente o `ToolPath` do registro. Só a
versão barra, e o teste de versão vem **antes** do de caminho. Logo
`oss_scale_integration_module_version_mismatch` (`:3382`) e
`oss_scale_integration_evidence_module_missing` (`:3454`) são **o mesmo defeito
visto duas vezes**, e subir o `ModuleVersion` mata os dois. Regravar a evidência
apagaria medição boa para consertar o lado errado.

**A família da §27 se repete, multiplicada por sete:**

| módulo | de | para | onde a cópia mora |
|---|---|---|---|
| osv-scanner | v2.4.0 | v2.5.1 | `ossscaleintegration/coverage.go:2488` · `toolartifactprovenance/provenance.go:97` (o `ExpectedVersion` **e** a string `Source` com `@v2.4.0`) · `checkperformance/ledger.go:647` |
| cyclonedx-gomod | v1.10.0 | v1.12.0 | `ossscaleintegration/coverage.go:2513` · `toolartifactprovenance/provenance.go:98` (idem, dois pontos na mesma linha) · `checkperformance/ledger.go:649` **e** `:651` |

A deriva tem data: `tools/sca/go.mod` subiu para v2.5.1/v1.12.0 em `b36aaf5b`,
**2026-08-30** — onze dias com sete registros Go parados atrás de um `go.mod` que
andou.

**E uma armadilha que separa os sete de um oitavo.**
`internal/scaignorepolicy/policy.go:442` diz *"Medido em 2026-08-26 contra o
binário real (osv-scanner v2.4.0, resolvido…)"*. Esse **não** se edita: é medição
datada, e trocar o número nela seria fabricar uma medição que ninguém fez. Ele se
**supera** com data e motivo, que é o que o contrato manda para parágrafo vencido.

A frente é da outra sessão e continua sendo — o que muda é que ela recebe o
diagnóstico medido em vez do meu palpite errado.

## 31. Os sete passaram a ler, e o gate caiu de cinco áreas para três

A §30 mapeou as sete cópias. Fechadas em `6d6c7ea7` (a fonte única e o guarda),
`945ec250` (o triângulo) e `0d737536` (o rewiring).

**A dúvida que precisava ser medida antes de escrever qualquer número** era qual
versão vale: a linha `require` do `tools/sca/go.mod` ou a que o binário reporta.
São fatos distintos, e supor um pelo outro trocaria um vermelho por outro de
forma diferente:

```
go-modern list -modfile=tools/sca/go.mod -m github.com/google/osv-scanner/v2 \
    github.com/CycloneDX/cyclonedx-gomod
  github.com/google/osv-scanner/v2      v2.5.1
  github.com/CycloneDX/cyclonedx-gomod  v1.12.0

data/ops/tool_artifact_provenance.jsonl (2026-08-29, em HEAD)
  osv-scanner-sca      exp=v2.5.1   det=osv-scanner version: 2.5.1
  cyclonedx-gomod-sca  exp=v1.12.0  det=Version: v1.12.0
  source=...osv-scanner@v2.5.1   source=...cyclonedx-gomod@v1.12.0
```

Batem. E o ledger da proveniência **já gravava** `expected` e `source` nessas
versões desde 29/08, enquanto `provenance.go:97,98` dizia v2.4.0 e v1.10.0 desde
`10640462` (2026-06-30) — logo `validateRecordsWithTools:260` reprovava por
`ExpectedVersion` **e** por `Source`, e `:263` por `versionMatches`. Não era um
gate afetado: eram dois.

**O que o guarda passou a provar, em três pontas.** `versions_test.go` casa
constante × `tools/sca/go.mod` × `module_version` da evidência. A terceira ponta
é a que importa: `evidenceRecordMatchesIntegration` compara a **versão antes do
caminho**, então evidência certa com pino errado é descartada **como se estivesse
ausente** — é essa mecânica que faz `module_version_mismatch` e
`evidence_module_missing` aparecerem juntos.

Quatro mutantes mortos: constante do osv, constante do cyclonedx, parser
preguiçoso (aceita a primeira linha com versão) e casamento pelo `ModulePath` em
vez do `ToolPath`. O terceiro e o quarto são os que separam guarda de decoração.

**`ledger_test.go:906-908` reprovou na hora**, como tinha de reprovar:

```
ledger_test.go:918: sca-osv module evidence=...osv-scanner@v2.5.1, want ...@v2.4.0
```

Os literais subiram. **Ficam literais de propósito** — teste que afirma a
constante contra produção que atribui a mesma constante é tautologia, e foi assim
que `BitmapVersionPinned` ficou errado por duas semanas (§27).

**E um vermelho meu, que eu criei em `314735ee` e fechei em `f65e4bc8`.** Subir a
constante do gofeed sem regravar a evidência trocou `module_version_mismatch` por
`evidence_module_mismatch` + `evidence_module_missing`. A correção não foi editar
o número: foi medir de novo (`list -m -json` deu `v1.4.2` e tag time
`2026-08-20T11:51:21Z`), reler o LICENSE no cache do módulo, e **reconferir no
código** as afirmações de política do registro em vez de herdá-las —
`demandobservations.go:4589` parseia de `bytes.NewReader` e não há `ParseURL` em
`internal/`; `:4626` descarta o item sem corpo de pesquisa, e `combineResearchText`
nem inclui o título.

**O que sobra, medido, e por que cada um sobra:**

| área | motivo | de quem |
|---|---|---|
| `performance:scale-index-benchmark` | `bitmap_version_pinned v2.14.5` numa evidência de **2026-07-07** que é MEDIÇÃO de benchmark. Trocar o número sem rodar o benchmark seria fabricar medição, e o benchmark está bloqueado pelo verdict apagado em 2026-07-09 (§29) | cadeia editorial |
| `oss_installation_matrix` | `lighthouse`, `tantivy` e `quickwit` ausentes, mais `oss_useful_agent_adapters_evidence.jsonl` com `checked_at=2026-07-05 want=2026-09-10` — o segundo é gate que reprova por relógio, a família da §21 | aberta |
| `content_quality` | três `external_dedupe_oracle_*_fingerprint_stale` no minhash e no zoekt | aberta |

E `tool-artifact-provenance` **continua vermelho**, por outra família inteira:
sete ferramentas em `live_artifact_path_mismatch` / `live_artifact_hash_mismatch` /
`live_discovery_failed`, porque o ledger guarda o caminho do GOCACHE
(`/home/rafael/.cache/go-build/<hash>-d/<tool>`) e esse caminho anda a cada
rebuild. Atinge govulncheck, gosec, staticcheck, gitleaks e scorecard junto — não
é deriva de versão, e o que eu fechei aqui não a toca.

## 32. Duas das três áreas que sobraram são a mesma cadeia, e uma delas guarda o hash do vazio

A §31 listou três áreas restantes como se fossem três problemas. Medi as fontes
e são dois.

`internal/dedupeexternaloracle/oracle.go:550-563` compara o fingerprint gravado
com o do arquivo **de hoje**, em três camadas:

```go
RefinedPublicProseRelPath = "data/editorial/refined_public_prose.jsonl"
InternalPairRelPath       = "data/editorial/authorial_mass_signature_candidate_pairs.jsonl"
authorialmassqualityvectors.OutputRelPath =
                            "data/editorial/authorial_mass_editorial_quality_vectors.jsonl"
```

As três são artefatos de `data/editorial/` — a **mesma cadeia** parada que a §22,
a §25 e a §29 nomeiam, e `refined_public_prose.jsonl` é justamente o único membro
do `BOOTSTRAP_REUSE_POOL_ARTIFACTS`. Logo `content_quality` não é uma frente à
parte: é a cadeia vista por uma quarta porta, ao lado de
`performance:scale-index-benchmark`.

**E o valor gravado numa das três diz mais do que "velho":**

```
external_dedupe_oracle_internal_pair_fingerprint_stale:
  sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
printf '' | sha256sum
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

É o SHA-256 da **string vazia**. A mensagem carrega
`record.InternalDedupeFingerprintSHA256`, isto é, o que o oráculo GRAVOU: na
execução que produziu esse registro, a camada de pares internos estava vazia.
Regenerar o fingerprint agora produziria um número novo sobre uma entrada que
ninguém conferiu — a mesma armadilha que fez o
`scale_index_benchmark_evidence.jsonl` ficar de fora (§31). Fica nomeado, não
regenerado.

**Sobra, de fato, uma área com causa própria:** `oss_installation_matrix`, com
`lighthouse`, `tantivy` e `quickwit` ausentes — e os dois últimos são exatamente
os que o cache negativo da §21 registra como falha a montante — mais
`oss_useful_agent_adapters_evidence.jsonl` em `checked_at=2026-07-05
want=2026-09-10`, que é gate reprovando por relógio, a família da §21.

## 33. Depois do #6, os quatro números ficaram iguais

A §28 mediu depois do #5. O compromisso era repetir depois do #6, e o eixo
discriminante não são os dois zeros — é o par que ninguém pensa em olhar: se o
render tivesse mudado, `input_html_files` ou `issue_files` teriam mudado junto.

```
input_html_files            11.288
issue_files                     62   todos heading_preposition_chain_files
glued_sentence_files             0   glued_sentence_samples   null
blocking_issue_files             0   blocking_issue_samples   null
indexable 11.284 · noindex 4
```

Campo a campo contra a evidência anterior, **só três campos mudaram, e nenhum é
contador**:

```
input_fingerprint_sha256   626741bb...  ->  5e583891...
record_fingerprint_sha256  f6757c48...  ->  f6f0aafe...
scan_duration_ms           8130         ->  8697
```

Os bytes dos 11.288 HTML andaram — o binário novo muda o `vcs.revision` — e a
forma não. Bate com o que o próprio deploy imprimiu no passo 6/7: *"0 pagina(s)
mudaram de conteudo"*. A previsão foi dita ao par **antes** da medição, e é isso
que a torna prova em vez de constatação.

Medido com o #6 ainda reaquecendo a borda, e isso não contamina a leitura: o gate
lê `public/**/index.html` do disco, que o passo 2 já reescreveu e o 5b já serviu.
O reaquecimento só faz requisição.

## 34. Proposta (não implementada) — `v2-source-provenance-strict` e o relógio

A outra sessão pediu o desenho por escrito **antes** de existir em código, e a
condição é do contrato, não dela: proveniência de fonte oficial é a única área que
o §5 marca como P1 permanente, porque gate frouxo aqui não produz vermelho depois
— produz página com fonte errada e ninguém vê. Isto é proposta. Nada foi editado.

**O censo, medido hoje** (`./tools/go-modern run ./cmd/check v2-source-provenance-strict`):

```
158  v2_source_provenance_selection_sidecar_invalid   (invólucro)
136  v2_source_provenance_checked_at_stale
 42  v2_source_provenance_audit_policy_invalid
 12  v2_source_provenance_input_selection_invalid
  3  v2_source_provenance_partial_content_contract_invalid
  3  v2_source_provenance_apply_eligibility_invalid
```

O invólucro carrega a causa dentro, e a distribuição dela desfaz a dúvida que eu
tinha: **124 dos 158 são `checked_at_stale`** e 30 são `audit_policy_invalid`. Somando
com os diretos, o relógio responde por ~260 de ~290 ocorrências classificadas.

O estado do dado: `data/source-registry/v2_source_provenance_live_evidence.jsonl`
tem **12 registros, todos com `checked_at 2026-07-14`** — 58 dias —, e o diretório
de conjuntos tem **186** arquivos.

**A regra que reprova é uma linha** (`audit.go:988-994`):

```go
if checkedDate.Before(nowDate) {
    return time.Time{}, Report{Issues: []Issue{{Code: "v2_source_provenance_checked_at_stale", ...}}}
}
```

Isto é `checked_at == hoje, em UTC`. Evidência escrita ontem reprova hoje, mesmo
que nada tenha mudado.

**Por que essa guarda invalida a chave errada — o argumento é o da §21, e ele é
verificável na MESMA função.** A auditoria já tem invalidação **por causa**, três
delas, todas em `audit.go:652-663`: `audit_policy_invalid` (a política mudou),
`input_fingerprint_invalid` (o conjunto de entrada mudou) e
`input_selection_invalid` (a seleção mudou). O que o relógio acrescenta é só uma
hipótese: *a fonte remota pode ter mudado*. E essa é justamente a única coisa que
uma auditoria offline **não consegue observar** — ela não faz requisição. Logo a
regra do calendário não mede o risco que diz medir; ela mede o tempo passar.

**Desenho proposto, em quatro pontos:**

1. **Toda checagem de integridade continua bloqueante, sem exceção** — ordem dos
   `evidence_id`, `schema_version`, fingerprint da política, fingerprint da
   entrada, seleção, escopo, política de host exato, ordem das requisições,
   contrato metadata-only, flags públicas fechadas e `record_fingerprint`. É aí
   que mora o risco de citação mal atribuída, e nada disso cede.
2. **Frescor sai de "hoje" e passa a ter horizonte nomeado**, com código próprio
   (`..._checked_at_beyond_horizon`), e o horizonte é propriedade da FONTE, não do
   arquivo — fonte que publica versionamento tem horizonte maior que a que não
   publica.
3. **Quem zera o frescor é uma reverificação real** — requisição de metadado à
   fonte oficial, pelo `wikijuridicabot`, que reescreve `checked_at` e o
   `record_fingerprint`. Sem esse produtor, mudar o limiar seria só empurrar a
   data, e isso é o que o §5 chama de afrouxar gate.
4. **O caso que prova que não afrouxei**: registro cujo `input_fingerprint` ou
   `input_selection` divergiu continua **bloqueante mesmo dentro do horizonte** —
   entrada nova sem reverificação é exatamente a situação em que a evidência
   antiga descreve outra coisa.

**E os 30 + 42 `audit_policy_invalid` não são relógio.** Eles dizem que a evidência
foi escrita sob uma versão de política anterior à do código de hoje. Isso não se
resolve por horizonte nenhum: exige rodar a auditoria de novo sob a política
vigente. Fica registrado para não ser varrido junto com o resto.

**Estado: proposta aberta, aguardando revisão da outra sessão.** Nenhuma linha de
`internal/v2sourceprovenance` foi tocada.

### 34.1 Emenda, depois da revisão: a função que eu ia tocar tem três chamadores, e um deles carimba página

A outra sessão revisou a §34 e aprovou os pontos 1, 3 e 4. **O ponto 2 fica
emendado por uma objeção que eu confirmei por leitura própria**, e ela é
bloqueante. O parágrafo original não se apaga: ele dizia onde ir, e o lugar era
o errado.

```
grep -rn "validateCurrentCheckedAt" internal/v2sourceprovenance/*.go | grep -v _test
  audit.go:324    checkedDate, checkedAtReport := validateCurrentCheckedAt(checkedAt, now)
  audit.go:795    _, checkedAtReport := validateCurrentCheckedAt(record.CheckedAt, time.Now().UTC())
  audit.go:988    func validateCurrentCheckedAt(...)
  apply.go:2837   if _, report := validateCurrentCheckedAt(record.CheckedAt, time.Now().UTC()); !report.Passed()
```

**`apply.go:2836` é `evidenceEligibleForApply`** — o portão que decide se uma
evidência pode ser carimbada numa página. Li a função inteira:

```go
func evidenceEligibleForApply(record EvidenceRecord) bool {
	if _, report := validateCurrentCheckedAt(record.CheckedAt, time.Now().UTC()); !report.Passed() {
		return false
	}
	return record.LiveAttempted && record.ApplyEligible &&
		record.RecordStatus == RecordStatusVerified &&
		...
		record.VerifiedAtCandidate == record.CheckedAt
}
```

Ali `checked_at` de hoje **não é regra de calendário**: é a afirmação *"esta
evidência foi colhida nesta execução, então posso carimbá-la numa página
publicada"* — e ela vem pareada com `VerifiedAtCandidate == CheckedAt`. Afrouxar
isso é exatamente a citação mal atribuída que o §5 chama de P1 permanente: página
no ar dizendo fonte verificada com evidência de 58 dias que ninguém rebuscou.

**E `audit.go:324` é a auditoria escolhendo o PRÓPRIO `checked_at`**, com default
`now.Format("2006-01-02")`. Horizonte ali deixaria uma auditoria nova nascer
carimbada com data velha.

**Emenda ao ponto 2, explícita para quem for implementar:** a mudança vive **só no
caminho de conferência**, `audit.go:795`, por uma função nova
(`validateCheckedAtDentroDoHorizonte`). `validateCurrentCheckedAt` **fica intacta**
e continua servindo `audit.go:324` e `apply.go:2837` como está hoje. Quem ler
"afrouxar o `checked_at`" e for à função compartilhada vai ao lugar errado — é por
isso que esta emenda existe.

**Emenda de ordem:** os pontos 2 e 3 não são paralelos. **(3) produtor de
reverificação primeiro; (2) horizonte depois**, e só depois de o reverificador ter
rodado ao menos uma vez. Invertido, o observável é um gate que ficou verde sem
nenhuma fonte rebuscada — e verde sem trabalho é o que o §5 chama de fraude
operacional.

**Dimensionamento do reverificador, para ninguém estimar "é rápido":** ele tem
**186 conjuntos** em `v2_source_provenance_live_evidence_sets/` como alvo e **12
registros de referência** em `v2_source_provenance_live_evidence.jsonl`, todos em
`2026-07-14`. O custo é de requisição a fonte oficial, com o teto que cada
operador publica e o recuo por 429/403 **e por erro de transporte** — o WAF F5 do
Planalto derruba a conexão em vez de devolver 429.

## 35. O #6 no ar, conferido por leitura minha do log, não pelo aviso do par

```
aquecidas: 22361 em 1863s (12.00 r/s)
  status: {200: 22361}
NO AR — 11051 paginas, cache limpo, https://wikijuridica.com.br
EXIT=0
```

Contei no log em vez de aceitar o relato: **zero ocorrência de `AVISO` ou `WARN`**
e **nenhum status 410** — a única linha com "410" é a que ANUNCIA que os 28 shards
retirados ficam fora da lista, não uma resposta. No #5 esse mesmo aquecimento
fechou com 28 `410` e um aviso que dizia o contrário do que tinha acontecido; o
conserto de `2ead0ce2` fechou os dois no primeiro caso real.

**A medição de forma da §33 continua valendo depois disto, e o motivo é
verificável:** `deploy-binario-go` troca o binário Go que serve rota dinâmica e
**não reescreve `public/`**. O `input_fingerprint_sha256` mudou no #6 porque o
passo 2 republicou os 11.288 arquivos; a troca de binário sozinha não os toca.

**E `check-binario-vs-fonte` em 1 é o gate funcionando, não regressão.** Li o
critério dele antes de concluir:

> reprova <=> existe commit que tocou `internal/`, `cmd/`, `go.mod` ou `go.sum`
> DEPOIS do commit que o binário declara em `vcs.revision`

O binário do #6 foi buildado com `e7d1a694`; `6d6c7ea7` e `0d737536` entraram
durante o reaquecimento — deliberadamente, depois de eu medir que o passo 7/7 não
compila `./cmd/...`. **Consequência operacional que passa a valer para mim:**
commit de doc ou de dado **não** reprova esse gate (o cabeçalho diz por extenso
que arquivo de dado sujo não reprova), mas commit em `internal/`, `cmd/`, `go.mod`
ou `go.sum` reprova — então commit de código meu se coordena com a troca de
binário do par, e não o contrário.

## 36. Um rascunho de página PUBLICADA sumiu na republicação de hoje

O passo 1 da cadeia editorial reprova por dado, e o dado aponta para uma perda:

```
authorial-mass-scale-shards: [authorial_mass_scale_stock_authorial_mass_stock_paid_refinement_orphan_draft_id:
    authorial-mass-draft-v2-proc-exec-cumprimento-obrigacao-fazer-astreintes]
```

**O órfão existe porque o rascunho foi removido, e a página dele continua no ar.**
Medido com `git show`, sem tocar na worktree:

```
ea559b13^  authorial_mass_drafts.jsonl   7.985 registros, o intent presente
ea559b13   authorial_mass_drafts.jsonl   7.984 registros, o intent AUSENTE
diferença de conjunto: 1 removido, 0 acrescentados
```

`ea559b13` é *"a republicacao de 2026-09-10 esta no ar"*, de hoje 10:18. A mensagem
descreve 2.914 páginas com texto novo e 1.457 re-datadas; **não menciona retirar
rascunho nenhum**.

E a página não foi retirada com ele:

```
published_manifest                      1 ocorrência
v2_publication_severity                 severity=medio  publish=True
public/procedimentos/…astreintes/       existe
data/editorial/v2_pages/procedimentos-w3-02.jsonl   presente
data/editorial/portfolio_v2/procedimentos-w3.jsonl  presente
```

O registro perdido tem **7.987 bytes e 38 campos** de texto autoral — `opening`,
`body_sections`, `h1_draft`, `official_source_urls`, `checked_at 2026-09-09`. É
exatamente o que o §8 chama de texto que **nunca se descarta**.

**O que já está descartado como causa**, lido em `internal/v2ingest/convert.go`:

| recusa de `ConvertPage` | por que não se aplica |
|---|---|
| `high_intent_keywords_underivable:<3` | as chaves são `{long_tail_query, title, h1, seed_term}` distintas; título, H1 e seed já são três |
| `record_too_large` | `maxDraftRecordBytes = 250000`; o registro tem 7.987 bytes, e 729 dos 7.984 vivos passam de 7.900, com máximo em 11.855 |
| ausência no portfólio | está em `portfolio_v2/procedimentos-w3.jsonl` |
| FAQ vazia | 9 das 20 páginas do mesmo shard têm `faq: []` |

**Por que não se conserta à mão:** `source_selection_rank` é **posicional e contíguo**
— medi `1..7984` sem buracos. Reinserir o registro exigiria renumerar 2.363 outros,
que é edição em massa cega sobre um artefato de 49 MB. O caminho certo é o produtor:
`cmd/ingest-v2-stock` converte `v2_pages` + `portfolio_v2` em rascunhos por
`v2ingest.ConvertPage`, e é ele que tem de voltar a emitir o intent.

**O que faltou medir, e por quê:** `./tools/ingest-v2-stock --prepare-only` (valida sem
escrever) não chegou a rodar — `run-go-cmd-cached` abortou com
`build source changed after authenticated read: /opt/wiki/internal/legalfacts/norma.go`,
porque a outra sessão está editando esse pacote agora. A guarda está certa; a medição
espera a janela.

## 37. O rascunho não sumiu: o ingest REJEITOU a página, e ele rejeita 3.055 páginas que estão no ar

A §36 registrou a perda e listou o que **não** era a causa. A causa está gravada,
com motivo, em `data/ops/v2_ingest_report.jsonl`:

```
run v2-ingest-20260910T170000Z
  intent_id   proc-exec-cumprimento-obrigacao-fazer-astreintes
  status      rejected
  reasons     ['duplicate_phrase_with_page:line=3528:intent=gloss-astreintes']
  word_count  818   public_path /procedimentos/exec-cumprimento-obrigacao-fazer-astreintes/
```

**Quem roda é o passo 0 do deploy**, `tools/deploy-publico:395`, e ele **terminou por
conta própria** — não foi truncamento por tempo, que era o primeiro discriminante:

```
.agents/runtime/deploy-ingest-20260910-092104.log
  accepted=7984  rejected=3200
  TIMING command=ingest-v2-stock status=pass duration_ms=572649
.agents/runtime/deploy-ingest-20260910-103108.log
  accepted=7984  rejected=3200
  TIMING command=ingest-v2-stock status=pass duration_ms=611152
```

A colisão é consequência da própria republicação: 2.914 páginas ganharam texto novo
hoje, o par passou a compartilhar frase, e a regra mantém a de linha menor (3528) e
rejeita a de linha maior (6984).

**E o censo mostra que não é um caso — é o regime.** Do relatório inteiro:

```
accepted 7.984    rejected 3.201    (de 11.185 páginas)
  3.957  heading_reuse_above_global_limit
  2.461  official_sources_insufficient
  1.335  portfolio_lane_invalid  ·  portfolio_page_type_invalid  ·  lane_invalid
  1.259  duplicate_phrase_with_page
  1.027  h1_equals_title
    500  missing_required_field
    384  official_source_host_not_allowed
```

Cruzando os 3.201 rejeitados com o `published_manifest`:

```
rejeitados                            3.201
publicados                           11.039
REJEITADOS QUE ESTÃO PUBLICADOS       3.055
```

**O corpus autoral cobre 7.984 das 11.039 páginas publicadas. As outras 3.055 não têm
rascunho nenhum** — e é por isso que a cadeia mede 7.959 enquanto o estoque tem 11.204
intents. Hoje mudou **um** registro de lado (7.985 → 7.984); o buraco de 3.055 é
permanente e ninguém o estava contando.

**Isto reenquadra as 445 da §22.** Elas não são "duas gerações que divergiram": são a
**borda móvel** de um conjunto que exclui por regra de qualidade, no ingest, páginas que
já estão no ar. `only_in_stock=235` e `only_in_records=210` medem quem entrou e quem
saiu dessa borda entre duas execuções — não um erro de sincronização.

**A régua que me parece violada, e que eu não vou consertar sozinho às cegas:** o
repositório já tem o precedente de que **página publicada não sai por similaridade,
piso ou assinatura**. Aqui ela sai — em silêncio, e levando junto o refinamento pago
que a referenciava, que é como o defeito virou vermelho no passo 1 da cadeia. O que
falta decidir é onde a correção mora: no ingest (que não deveria rejeitar o que já está
publicado, e sim classificar), ou no validador do refinamento (que não deveria tratar
como órfão fatal o que o ingest classificou). Proposta antes de código, como na §34.

## 38. O que a página perde não é a publicação: é o rascunho, e o modo que o descarta não tem alternativa no CLI

A §37 fechou com uma régua que eu disse violada — *"página publicada não sai por
similaridade, piso ou assinatura"* — e com a frase "aqui ela sai". **Medi, e essa
parte está errada: a página não sai de lugar nenhum do que é público.** O caso que
abriu a §36/§37, `proc-exec-cumprimento-obrigacao-fazer-astreintes`, continua
inteiro depois da reprovação:

```
published_manifest.jsonl                              1 linha
data/editorial/v2_pages/                              1 shard
public/procedimentos/exec-.../index.html         31.803 bytes
public/sitemaps/pages-0022.xml                     presente
```

O precedente de publicação está intacto. O que a reprovação tira é **o rascunho
autoral**, e a regra que isso toca é outra: *"Página escrita nunca é descartada:
texto redigido foi pago pelo dono"* (§8 do contrato). Deixo a frase da §37 no lugar,
datada e superada por esta.

### O `drafts_expected` não declara nada — ele conta o que o próprio ingest acabou de escrever

Foi o primeiro discriminante, e ele derruba a leitura de "manifesto declara um
subconjunto de 7.984":

```
internal/v2ingest/v2ingest.go:654   drafts_expected = total real do arquivo canônico
internal/v2ingest/v2ingest.go:666   DraftsExpected: draftsTotal
wc -l data/editorial/authorial_mass_drafts.jsonl   7984
```

`drafts_expected` é a contagem do arquivo de rascunhos **depois do lote**, escrita
pela mesma execução que produziu o arquivo. Comparar um com o outro é o padrão que
`internal/refinedcorpusfloor` já nomeia no próprio cabeçalho (BUG-225): artefato que
valida a si mesmo nunca reprova. A série histórica confirma que ele acompanha o
arquivo e não o acervo — 7.972 em 2026-08-30, 7.985 e depois 7.984 hoje, enquanto o
estoque v2 ia a 11.204 e o publicado a 11.039.

### Os 3.055 são cobertura, não expulsão — e a expulsão real são 231

União dos `unique_intent_id` das **50 revisões** do arquivo de rascunhos
(2026-08-07 até hoje), cruzada com os reprovados que estão publicados:

```
intents que já tiveram rascunho, alguma vez        8.591
rejeitados que estão publicados                    3.055
  nunca tiveram rascunho                           2.824   (92,4%)
  tiveram e não têm mais                             231   ( 7,6%)
```

**A §37 contou os dois grupos como um.** Os 2.824 nunca entraram na camada autoral —
é lacuna de cobertura, e o ingest não os expulsou de nada. Os 231 são a classe real:
página publicada cujo rascunho existiu e não existe mais. O número reencontra a mesma
família que a §22 mede (`only_in_stock=235`, `only_in_records=210`) e que o cabeçalho
de `refinedcorpusfloor` registra (234 e 221) — não é coincidência, é o mesmo conjunto
visto de três lados.

### A causa é uma linha, e o código já tem a garantia que ela desliga

```go
// cmd/ingest-v2-stock/main.go:436
Mode: v2ingest.ModeRewrite, Now: now, OriginsByLine: origins,

// internal/v2ingest/v2ingest.go:415-418
if opts.Mode == ModeRewrite {
    // No rewrite o arquivo é substituído; nada do conteúdo velho entra na
    // checagem de duplicidade nem na base de ranks.
    existing = nil
}

// internal/v2ingest/v2ingest.go:565-567  (ModeUpsert)
// O merge é por intent e só substitui versões cuja nova página foi
// aceita. Reprovação preserva integralmente o draft anterior, mesmo
// quando outro item do mesmo lote é aceito e força a escrita.
```

`ModeUpsert` **existe e escreve exatamente a garantia que falta** — reprovação
preserva o rascunho anterior. Ele não tem flag: `grep -n '"mode"' cmd/ingest-v2-stock/main.go`
devolve vazio, o modo é literal na linha 436, e o `note` do manifesto de hoje confirma
o que rodou (`transaction=v2-rewrite-v5-f4534f9f…`). O deploy chama
`tools/ingest-v2-stock` sem argumento de modo (`tools/deploy-publico:395`), logo
**todo deploy que reingere roda em rewrite, e todo rascunho de página reprovada é
descartado nesse instante**.

O caminho de reparo que o comentário do `ModeUpsert` descreve — *"detector aponta →
agente corrige a página na fonte → upsert atualiza o estoque"* — nunca esteve
disponível para quem opera o deploy.

### O que isto NÃO autoriza

Trocar o literal da linha 436 por `ModeUpsert` seria a correção de uma linha e a
regressão de outra coisa: em upsert o arquivo deixa de ser função pura do estoque, e
rascunho de intenção que saiu do acervo passa a viver para sempre — que é o
`expansion_expected` permanentemente stale que a DEC-012 já corrigiu uma vez
(`v2ingest.go:655-658`). A proposta vai à §39, depois do `advisor`, e antes dela roda
`./tools/ingest-v2-stock --prepare-only` para confirmar o veredito contra o binário
de HEAD — o que hoje ainda não é possível, porque `internal/legalfacts/norma.go` está
em edição pelo par (é a correção do CTN, e a guarda do ingest está certa em recusar).

## 39. Proposta (não implementada) — o rascunho sobrevive enquanto a página está no ar

A §38 achou a causa e disse que a proposta viria depois do `advisor` e do
`--prepare-only`. O `advisor` foi consultado; o `--prepare-only` **não pôde rodar**, e
o motivo é medição nova que vale por si (§39.1). A proposta sai mesmo assim, porque o
que ela precisa provar já está provado sem o binário.

### Primeiro: o raio de explosão de hoje é exatamente 1, e isso não enfraquece o achado

O `advisor` levantou a objeção certa: se 231 páginas publicadas perderam rascunho, por
que a cadeia só ficou vermelha agora? Medi antes de escrever.

```
./tools/generate-authorial-mass-scale-shards --profile-only
authorial-mass-scale-shards: [authorial_mass_stock_paid_refinement_orphan_draft_id:
  authorial-mass-draft-v2-proc-exec-cumprimento-obrigacao-fazer-astreintes]
rc=1
```

O passo 1 nomeia o caso exato. E o detector (`internal/authorialmassstock/stock.go:1044-1051`)
itera a camada de refinamento pago procurando `draft_id` sem rascunho aplicado:

```
draft_id nos rascunhos de hoje                     7.984
draft_id na camada de refinamento pago             2.446
ORFAOS (refinamento sem rascunho)                      1
refinamentos que ainda tem rascunho                2.445
```

**Um órfão, e é o de hoje.** Os outros 606 rascunhos perdidos ao longo das 50 revisões
nunca tiveram refinamento pago, então nunca acenderam o passo 1. Não é sorte: é a
interseção de dois conjuntos que quase não se cruzam — até cruzar.

**O que isso muda na leitura:** o dano não é grande hoje; é **não limitado**. O gatilho
é exógeno — a página de astreintes foi reprovada por `duplicate_phrase_with_page` contra
uma página que *outra* republicação alterou. Qualquer uma das 2.445 restantes vira órfã
no dia em que uma edição alheia empurrar seu par para cima do limiar. E a §37 registrou
que 2.914 páginas ganharam texto novo só hoje.

### A proposta

Hoje, em `ModeRewrite`:

```go
// internal/v2ingest/v2ingest.go:413-418
stockBeforeUpsert := existing
if opts.Mode == ModeRewrite {
    existing = nil        // o conteudo anterior inteiro e descartado
}
```

Proposta — **em rewrite, o conjunto gravado passa a ser**:

```
total = accepted  ∪  (stockBeforeUpsert  ∩  published_manifest)
```

Um rascunho sobrevive **enquanto a página dele está publicada**, e só enquanto.

- **§8 fica satisfeito** — "página escrita nunca é descartada": nenhum texto pago sai
  do corpus enquanto a rota estiver no ar.
- **A DEC-012 fica satisfeita** — o motivo pelo qual `ModeUpsert` inteiro é a resposta
  errada é que ele torna rascunho imortal e devolve o `expansion_expected`
  permanentemente stale (`v2ingest.go:655-658`). Aqui o rascunho **morre** quando a
  página sai da publicação, que é o momento certo.
- **Nenhuma régua afrouxa.** A reprovação continua reprovando, com o mesmo motivo, no
  mesmo relatório. Muda o que se carrega adiante, não o que se aceita.

### Custo, medido antes de propor

| Pergunta | Medição |
|---|---|
| O dado já está na mão? | `stockBeforeUpsert` é capturado em `v2ingest.go:413`, **antes** do `existing = nil`. Em rewrite ele existe e não é usado |
| A chave de junção existe dos dois lados? | `unique_intent_id` — está no schema dos rascunhos e em `publishedmanifest.Record:73` |
| Custa pacote novo na atestação? | **Não.** `portaljuridico/internal/publishedmanifest` já está nos 98 do fecho, via `internal/authorialmassplan:75`, que já chama `publishedmanifest.LoadRecords(root)` |

### A semântica de um ciclo de atraso, declarada de propósito

O ingest roda no **passo 0** do `deploy-publico`; a publicação vem depois. Logo o
manifesto que ele lê é o do **release anterior**. Consequências, ambas desejadas:

- Página publicada ontem e reprovada hoje **mantém** o rascunho — é exatamente o caso
  que se quer proteger.
- Página que nasce e é reprovada no mesmo ciclo não ganha rascunho — correto, porque
  ela nunca teve um.

Isso é decisão, não acidente, e por isso está escrito aqui antes do código.

### O que a proposta NÃO resolve, e por que não entra nela

O par pediu, com razão, que antes de afrouxar a régua do ingest eu medisse quantas das
3.201 reprovações são acusação concreta. **A proposta não afrouxa régua nenhuma**, então
a distribuição não a condiciona: sob ela os 231 se preservam independentemente do motivo.
A medição foi feita mesmo assim, porque aponta duas frentes próprias — §39.2.

### Ainda não implementado

Como na §34, a proposta fica escrita antes do código. O que falta para implementar:
`--prepare-only` verde contra um binário cuja atestação bata (§39.1), teste de regressão
que prove a preservação com um caso reprovado-e-publicado, e teste por mutação que prove
que a interseção com o manifesto é o que mata o rascunho de página despublicada — sem ele,
a implementação passaria igual com `ModeUpsert` puro, que é a regressão da DEC-012.

## 39.1. Por que o `--prepare-only` não pôde rodar, e por que isso é achado e não obstáculo

```
TIMING command=ingest-v2-stock status=fail duration_ms=32263
ingest-v2-stock: generated validator attestation does not match authenticated source graph:
  generated=sha256:8db793be5fa740f79c64c8b65b40d5d4ee3a60a6047e775858e84c0a0212c498
  source=sha256:25c0a28055072bb8b03952caeafc01a12e5863d22430a15052838247582e20a5;
  run go generate ./internal/v2ingest
```

A causa é o `internal/legalfacts/norma.go` em edição pelo par (a correção do CTN). E o
motivo pelo qual isso alcança o ingest está medido:

```
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock | grep legalfacts
  portaljuridico/internal/legalfacts          (98 pacotes no fecho)
```

**A tabela do §1 do contrato nomeia `internal/v2ingest`, `cmd/ingest-v2-stock`, `go.mod`
e `go.sum` — não nomeia `legalfacts`.** O grafo hasheia o **fecho**, não a lista da
tabela, e por isso a armadilha é maior do que o contrato deixa ver: qualquer um dos 98
invalida a atestação.

**Consequência operacional que ninguém tinha visto, e que vale mais que o meu bloqueio:**
`tools/deploy-publico:395` reingere o estoque quando o validador mudou desde o
contentstore. Um commit que toque qualquer pacote do fecho **sem** levar
`./tools/go-modern generate ./internal/v2ingest` junto faz o passo **0/7 do deploy**
morrer com este mesmo erro, depois de já ter pago a compilação. Avisado ao par, que
reordenou a execução por causa disso.

## 39.2. As 3.201 reprovações, classificadas — e dois defeitos que a contagem crua escondia

Pedido do par. Sobre o relatório do run `v2-ingest-20260910T170000Z`, contando **páginas**
(não ocorrências de motivo) e separando o que reprova sozinho:

| motivo | páginas | publicadas | motivo único |
|---|---:|---:|---:|
| `official_sources_insufficient` | 2.461 | 2.319 | 602 |
| `portfolio_page_type_invalid` | 1.335 | 1.327 | 0 |
| `lane_invalid` | 1.335 | 1.327 | 0 |
| `portfolio_lane_invalid` | 1.335 | 1.327 | 0 |
| `duplicate_phrase_with_page` | 1.259 | 1.219 | 446 |
| `h1_equals_title` | 1.027 | 985 | 0 |
| `heading_reuse_above_global_limit` | 990 | 986 | 0 |
| `body_sections_below_stock_minimum` | 100 | **0** | 0 |
| `declared_word_count_missing_or_invalid` | 100 | **0** | 0 |
| `intent_skipped_by_writer` | 100 | **0** | 0 |
| `missing_required_field` | 100 | **0** | 0 |

Mediana de motivos por página: **2**.

**Defeito 1 — a §37 contou strings de motivo, não páginas.** Ela publicou "3.957
`heading_reuse_above_global_limit`". São **990 páginas**: o motivo carrega `:detalhe`, e
cada heading distinto virava uma linha. Mesmo erro de unidade que a §38 corrigiu no
`drafts_expected`. A contagem crua da §37 fica superada por esta tabela.

**Defeito 2 — três nomes para uma condição só.** `portfolio_page_type_invalid`,
`lane_invalid` e `portfolio_lane_invalid` dão **exatamente 1.335 cada, sempre juntos, e
zero como motivo único**. Quem soma a coluna vê 4.005 e planeja três frentes onde há uma.
O conserto provável é no relatório, não na regra — e a verificação é olhar se os três
saem do mesmo `if`. Fica nomeado, não consertado nesta seção.

**A coorte que reprova certo:** os quatro motivos de exatamente 100 páginas têm **zero
publicadas**. É a mesma coorte `intencao_pulada_deliberadamente` que
`tools/generate-v2-publication-severity:649-670` documenta como decisão editorial — 121
registros `skipped: true` que não devem virar página. Assinatura de coorte, não de régua.

**E uma discordância de contrato, levantada pelo par e que eu confirmo:**
`official_sources_insufficient` acusa **2.319 páginas publicadas** e reprova 602 sozinho.
O §5 do contrato classifica *"fonte insuficiente"* como motivo **médio** — publica e
refina depois. A régua do ingest o trata como reprovação. **São duas réguas discordando
sobre a mesma página**, e a pergunta não é qual afrouxar: o §5 está escrito no contrato e
a do ingest não. Frente própria, fora da §39.

## 40. A produção inteira dos cinco geradores é invisível à cadeia autoral, e a causa é uma terceira lista de vocabulário

A §39.2 nomeou "três nomes para uma condição só" e disse que a verificação era olhar se
os três saem do mesmo `if`. **Não saem** — são três condições distintas
(`internal/v2ingest/validate.go:617-625`) que disparam juntas nas mesmas 1.335 páginas.
Abri o `:detalhe` de cada motivo, e o que estava por trás é maior que o defeito de
relatório:

```
lane_invalid              'derivada_de_fonte_oficial'   1335
portfolio_lane_invalid    'derivada_de_fonte_oficial'   1335
portfolio_page_type_invalid
    tema_repetitivo   1074
    sumula             112
    julgado             60
    noticia             48
    diario-oficial      41      (= 1.335)
```

Uma lane só, e cinco `page_type` que são exatamente **as cinco famílias determinísticas
da onda diária**. `1.327 das 1.335 estão publicadas`.

### O vocabulário do ingest é a lista velha, e as outras três subsistemas conhecem a lane

```go
// internal/v2ingest/validate.go:63
var validLanes = map[string]bool{"comercial": true, "informativa": true}

// internal/v2ingest/validate.go — wordCountBands
"verbete" · "pergunta" · "guia_problema" · "procedimento"
```

Contra o que o resto do repositório faz com o mesmo valor:

```
cmd/generate-noticia-pages/main.go:787,1418        Lane: "derivada_de_fonte_oficial"
cmd/generate-diario-pages/main.go:963,1366         Lane: "derivada_de_fonte_oficial"
cmd/generate-stj-tema-pages/main.go:1210           Lane: "derivada_de_fonte_oficial"
cmd/generate-stj-sumula-pages/main.go:707,1026     Lane: "derivada_de_fonte_oficial"
cmd/generate-stf-informativo-pages/main.go:777     Lane: "derivada_de_fonte_oficial"
internal/checks/text_truncation.go:132             if p.Lane == "derivada_de_fonte_oficial" { … }
```

Os cinco geradores sancionados **emitem** a lane, e um gate de qualidade **já a trata
como caso próprio**. Só o validador da ingestão não a conhece — e reprova por isso.

**E são três vocabulários, não dois.** O serving tem o seu
(`internal/content/content.go:40-50`: `wiki`, `legislacao`, `dispositivo-legal`,
`jurisprudencia`, `precedente`, `noticia-juridica`, `artigo`, `pergunta`,
`hub-tematico`), que **também** não contém nenhum dos cinco `page_type` do portfólio:
`noticia` × `noticia-juridica`, `sumula` × `precedente`, `julgado` × `jurisprudencia`.
Três listas para um conceito, disjuntas duas a duas exceto por `pergunta`, e nenhum gate
compara as três.

### O que isso explica, com número

```
publicados que NUNCA tiveram rascunho              2.824
  reprovados por lane derivada_de_fonte_oficial    1.327   (47,0%)
```

**Quase metade da lacuna de cobertura da §38 tem uma causa só, e ela não é qualidade
editorial.** As 1.335 nunca tiveram rascunho — zero delas aparece em qualquer das 50
revisões do arquivo. Não é conteúdo que se perdeu: é uma linha de produção inteira que
a cadeia autoral nunca enxergou, porque a porta de entrada recusa o crachá dela.

### É a mesma família do achado do par de hoje

O par acabou de achar, em `internal/legalfacts`, que o pré-filtro `detectNormaSignals`
era **uma segunda lista das mesmas siglas** e ficou para trás quando a primeira foi
corrigida — a metade do conserto que pousou em 2026-09-08 e a outra metade que não. Aqui
é a mesma forma em outro subsistema: **duas listas da mesma coisa divergem sempre, e a
divergência é silenciosa porque cada lado passa nos próprios testes.** A diferença é o
tamanho do silêncio: lá eram 443 ocorrências de citação, aqui são 1.327 páginas
publicadas fora da cadeia.

### O que NÃO se conclui daqui

Não se conclui que essas páginas *devessem* ter rascunho autoral. Elas nascem de fonte
oficial, por gerador determinístico, e é plausível que a camada de massa autoral não seja
o lugar delas. O que não se sustenta é o **veredito atual**: `portfolio_lane_invalid`
acusa de inválido um valor que quatro outros lugares do repositório tratam como legítimo.
Página fora de escopo tem de sair **classificada**, não **reprovada** — a diferença é
exatamente a que a §39 já usa: reprovar é acusação de defeito, e acusação errada em
volume é o que faz um relatório de 3.201 linhas não significar nada.

Isto é achado, não conserto. `internal/v2ingest/validate.go` está no fecho de atestação
(§39.1) e o par vai atestar e deployar nos próximos minutos; tocar o arquivo agora
invalidaria o trabalho dele. Fica nomeado, medido, e com o conserto desenhado para depois
do deploy dele.

### 40.1. A ponte que resolveria isso já existe, no pacote que o ingest já importa

O conserto não é "acrescentar cinco chaves a `wordCountBands`". O repositório **já
construiu** a tradução, pela DEC-032, e ela está completa:

```go
// internal/content/content.go — v2CanonicalPageTypes
"pergunta":        "pergunta"
"guia_problema":   "artigo"
"procedimento":    "artigo"
"verbete":         "wiki"
"sumula":          "wiki"
"noticia":         "noticia-juridica"
"diario-oficial":  "noticia-juridica"
"julgado":         "jurisprudencia"
"tema_repetitivo": "precedente"
"norma":           "legislacao"
```

**Dez chaves — e as cinco que o ingest reprova estão todas lá**, com comentário datado
explicando por que cada uma cai onde cai. As quatro bandas do `wordCountBands` também
estão. Ou seja: `wordCountBands` é um **subconjunto de 4 de um vocabulário de 10** que
vive em `internal/content`, e `portaljuridico/internal/content` **já está nos 98 pacotes
do fecho de atestação** do `v2ingest` — conferido, não suposto.

E há função pública pronta: `content.CanonicalPageType(v2PageType) (string, bool)`, com
teste próprio (`internal/content/derived_page_types_test.go`) que prova a ponte para
quatro dos tipos e que nenhum deles habilita CTA.

**A medição que fecha o argumento:** `grep -rln wordCountBands internal/` devolve **um
arquivo só** — `internal/v2ingest/validate.go`. Nenhum teste cruza essa lista com
`LegalPageTypes` nem com `v2CanonicalPageTypes`. E o repositório **sabe** fazer esse
cruzamento: `internal/legalmarketingpolicy/cta_page_type_vocabulary_test.go` e
`internal/content/derived_page_types_test.go` são exatamente isso, para outras duas
listas. A prática existe; ela só nunca alcançou a lista da ingestão.

**Desenho do conserto, para depois do deploy do par:** o validador consulta
`content.CanonicalPageType` antes de decidir. Tipo que a ponte conhece e cujo canônico
está em `LegalPageTypes` **não é `invalid`** — é derivado de fonte oficial, e sai
classificado como fora do escopo da massa autoral, com o motivo dizendo isso. Tipo que a
ponte não conhece continua reprovando, com o mesmo código de hoje. A banda de contagem de
palavras passa a ser resolvida pelo canônico, e `derivada_de_fonte_oficial` entra em
`validLanes` — porque quatro lugares do repositório já a tratam como legítima e um gate
de qualidade já a nomeia.

**O teste que a mudança tem de trazer, e sem ele ela é remendo:** um caso que compara as
**três** listas e falha quando qualquer uma ganhar chave que as outras não têm. É a única
forma de o próximo `page_type` novo não repetir isto — e é a mesma lição que o par tirou
hoje do `detectNormaSignals`.

## 41. As duas réguas de fonte oficial não só discordam: a de publicação LÊ o veredito da outra e o rebaixa

O par insistiu duas vezes que `official_sources_insufficient` é o nó, e que o §5 o
classifica como **médio** — publica e refina depois. Fui ler antes de concordar, porque
nome igual não é semântica igual. **É igual, e é pior do que "duas réguas discordando".**

**A régua da ingestão** (`internal/v2ingest/validate.go:783-785`):

```go
if validSources < 2 {
    reject("official_sources_insufficient:%d", validSources)
}
```

**A régua da publicação** (`tools/generate-v2-publication-severity:750-757`):

```python
# --- medios (publicam) ---
sources = [s for s in (record.get("official_sources") or []) if (s.get("url") or "").strip()]
if not sources:
    medium.append("sem_fonte_oficial")
elif len(sources) < 2 or "official_sources_insufficient" in queue_reasons:
    medium.append("fonte_insuficiente")
```

Mesmo limiar (`< 2`) — e a segunda **cita o código de motivo da primeira pelo nome**,
`official_sources_insufficient`, para chegar à conclusão **oposta**: médio, publica,
refina depois. Não são duas medições que por acaso batem: uma consome o veredito da
outra e o rebaixa de propósito.

**A distribuição diz o que está em jogo:**

```
official_sources_insufficient   2.461 paginas   (2.319 publicadas)
    validSources = 0     141
    validSources = 1   2.320
```

**2.320 páginas têm fonte oficial válida — uma.** Não é ausência de proveniência; é
falta da segunda fonte. E o §5 já decidiu o que fazer com isso: publica e refina.

**Por que isso não é "afrouxar régua", que era a minha objeção inicial e cai:** as duas
réguas guardam coisas diferentes por desenho — a da ingestão guarda a entrada no corpus
autoral, a da severidade guarda a publicação. Poderiam divergir legitimamente. O que
torna a divergência um defeito é a §38: **com `ModeRewrite`, a régua mais estrita não
apenas recusa a entrada — ela destrói o rascunho que já existia.** A régua que ninguém
escreveu no contrato vence a que está escrita, por efeito colateral de um modo de
escrita, não por decisão.

**Ordem de conserto, e ela importa:** a §39 (rascunho sobrevive enquanto a página está
publicada) resolve a **perda** para os três casos — §39, §40 e §41 — sem tocar em régua
nenhuma. Só depois dela vale discutir o veredito de cada uma, porque aí a discussão é
sobre o que o relatório *diz*, e não sobre o que ele *apaga*. Se a ordem se inverter, a
gente vai debater classificação enquanto rascunho continua sumindo.

## 42. Os 231 rascunhos não estão perdidos: estão no git, inteiros, e são 115.199 palavras

A §38 provou o vazamento e a §39 desenhou a válvula. Nenhuma das duas perguntou o que
interessa ao §8 — *"texto redigido foi pago pelo dono"*: **o texto derramado dá para
buscar de volta?** Dá, e a medição é limpa.

Para cada um dos 231 intents que perderam rascunho **e continuam publicados**, procurei a
revisão mais recente de `data/editorial/authorial_mass_drafts.jsonl` que ainda o continha,
li o registro e conferi que ele parseia e tem corpo:

```
perdidos e publicados (o alvo do §8)      231
recuperados de alguma revisao             231
nao encontrados                             0

com body_sections e texto                 231
sem corpo                                   0
palavras por rascunho    min=244  mediana=482  max=1145
TOTAL                                 115.199 palavras
```

**231 de 231, sem uma perda.** Nenhum registro corrompido, nenhum vazio, nenhum truncado.
Cento e quinze mil palavras de texto autoral pago, íntegras, fora do corpus vivo.

E a origem mostra que a sangria foi em ondas, não contínua:

```
501109ea  2026-08-12   204 rascunhos
72009d93  2026-07-09    17
2e04fe27  2026-08-30     5
064058f8  2026-08-04     3
c4e5cffd  2026-08-07     1
6d3623c2  2026-09-10     1   (o de hoje)
```

### O horizonte está fechado, e isso importa para o número

O `advisor` cobrou: "231" só vale se a união cobrir a vida inteira do arquivo.

```
git log --diff-filter=A -- data/editorial/authorial_mass_drafts.jsonl
  e1028afc  2026-06-14  p0 generate blocked mass authorial drafts
revisoes totais: 50
```

A revisão mais antiga **é a criação**. A união de 50 cobre de 2026-06-14 até hoje, então
231 é o número, não "231 dentro do histórico registrado".

### A §41 fica mais forte, não mais fraca

O `advisor` também cobrou a frase central da §41 — que a régua da publicação "consome o
veredito da ingestão" —, apontando que `queue_reasons` poderia vir de outro produtor que
apenas reusa a string. Conferi quem escreve a fila:

```
internal/v2ingest/v2ingest.go:33    RewriteQueueRelPath = "data/editorial/v2_rewrite_queue.jsonl"
internal/v2ingest/v2ingest.go:974   temp, err := os.CreateTemp(filepath.Dir(path), ".v2_rewrite_queue_*.tmp")
```

**É o próprio ingest que escreve a fila.** Então `queue_reasons` são literalmente os
motivos de reprovação dele, e `generate-v2-publication-severity:756` os lê para
classificar como **médio**. A frase da §41 se confirma: uma régua lê o veredito da outra e
o rebaixa de propósito.

### A ordem da remediação, e o efeito colateral que ela tem de declarar

**Restaurar antes de fechar a válvula não adianta:** o `ModeRewrite` reescreve o arquivo a
cada deploy que reingere, então 231 registros repostos hoje somem no próximo passo 0/7.
A ordem é **§39 primeiro, restauração depois**.

E a restauração tem uma consequência que precisa estar escrita antes de alguém a executar:
`drafts_expected` passaria de **7.984 para 8.215**, e ele alimenta
`authorialmassstock.EffectiveReleaseMinimum`, que ainda é consumido por quatro pacotes de
produção — `internal/jsonlstream`, `internal/scaledcontentreleaseverdict`,
`internal/authorialmassstock` e `internal/publicproselanguagepatterns`. É exatamente o
mecanismo que o cabeçalho de `internal/refinedcorpusfloor` descreve: *"o piso CRESCE a
cada rascunho novo, e o corpus refinado está congelado desde 2026-08-05"*. Os oito oráculos
de prosa já foram desacoplados por aquele pacote; **estes quatro não**.

Logo a restauração é de três peças, não de uma: gerador datado que repõe os 231 do git ·
medição do que acontece com os quatro pisos · e a decisão, escrita, de qual deles ainda
deve seguir o tamanho do arquivo de rascunhos. Nenhuma delas é o conserto da §39, e
nenhuma delas se faz antes dele.

**O que já está garantido, independentemente de tudo isso:** o texto não se perdeu. Está
em `git show <rev>:data/editorial/authorial_mass_drafts.jsonl`, endereçável por intent, e
esta seção é o índice de onde cada um está.

### 42.1. O índice existe no disco, é reprodutível, e a bancada mata quatro mutantes

Não adianta a §42 dizer "o texto está no git" e deixar a localização numa medição de
sessão. O índice nasce com produtor próprio:

```
tools/generate-rascunhos-perdidos-recuperaveis        (Python, fora do fecho Go)
data/editorial/rascunhos_perdidos_recuperaveis.jsonl  231 linhas
tools/test_generate_rascunhos_perdidos_recuperaveis.py  7 casos
```

Cada linha traz `unique_intent_id`, `draft_id`, a **rota publicada real**, `page_type`,
`practice_area`, `revisao_git` (a revisão mais recente que ainda continha o rascunho),
`palavras_do_corpo` e `secoes`. Recuperar um é
`git show <revisao_git>:data/editorial/authorial_mass_drafts.jsonl`.

**Duas armadilhas que a ferramenta evita por construção, e cada uma tem caso de teste:**

- **A rota vem do MANIFESTO, não do rascunho.** O `public_path` do próprio rascunho é
  `""` — ele nasce `authorial_mass_draft_blocked` e o campo é zerado sem condicional.
  Copiar dali faria as 231 páginas que **estão no ar** saírem apontando para lugar
  nenhum, e campo vazio não levanta erro: o defeito seria silencioso. Medido depois do
  conserto: **0 rotas vazias em 231**.
- **Comparação por CONJUNTO, nunca por linha.** `v2ingest.go:592` ordena por
  `SourceSelectionRank` antes de gravar, então o arquivo é reordenado a cada execução e
  um diff de linhas mede a ordem. É a mesma armadilha que o par encontrou hoje na
  evidência do LexML (37 removidas / 207 acrescentadas que eram reordenação).
- **Ausência de histórico aborta.** Arquivo que existe no disco e nunca foi commitado
  faria a união sair vazia, `perdidos` sair vazio e o índice dizer "nada se perdeu".
  O caso de teste monta exatamente isso: repositório **com** histórico, caminho **sem**.

Prova por mutação, quatro mutantes, todos mortos:

| mutante | caso que reprova |
|---|---|
| tirar `& rotas_publicadas` (indexar despublicado também) | `test_rascunho_que_saiu_sem_pagina_publicada_fica_de_fora` |
| guarda de histórico devolve lista vazia em vez de abortar | `test_arquivo_sem_historico_aborta_em_vez_de_devolver_vazio` |
| `--resumo` passa a gravar | `test_resumo_nao_grava` |
| rota volta a vir do rascunho | `test_a_rota_vem_do_manifesto_e_nao_do_rascunho` |

## 43. Os outros 376 rascunhos perdidos são o cartesiano v1, e a saída deles estava certa

A §42 tratou dos 231 que estão publicados. Faltavam **376** dos 607 perdidos, e eu quase
os somei ao prejuízo: a contagem crua dá **1.176.065 palavras**, mediana de **3.117** por
rascunho — seis vezes o tamanho dos 231. Antes de escrever isso, abri um registro.

```
chave        busca-apreensao-veiculo::negativa-formal::prazo-sete-dias
             seed_term_id :: scenario_id :: context_id
long_tail    "busca e apreensão de veículo negativa formal com documento prazo curto de sete dias"
abertura     "A busca «busca e apreensão de veículo negativa formal com documento
              prazo curto de sete dias» descreve esta situação: …"
secoes       24
```

**É o cartesiano v1.** A assinatura fecha nos três lados:

```
376 de 376 dos perdidos-nao-publicados tem scenario_id E context_id
  0 de 7.984 do arquivo VIVO tem qualquer um dos dois   (DEC-008)
  0 de 376 ainda existe em data/editorial/v2_pages/
```

`docs/PRECEDENTES_DAS_ORDENS.md:93` registra o veredito: o v2 **substituiu** o v1 em
2026-07-09 — *"300 rascunhos + 9.700 expansão — doorway/duplicado, DEC-004; hoje
`authorial_mass_content_expansion=0`, só recuperável no git"*. A saída deles do corpus
não foi vazamento: foi a decisão editorial sendo aplicada.

**Quase escrevi que 1,17 milhão de palavras tinham se perdido.** Teria sido a terceira
contagem inflada do dia — depois dos "3.055 que saem do ar" (§38) e dos "3.957
`heading_reuse`" (§39.2) — e a pior das três. Nas três, o que desfez foi ler **uma linha**
do dado em vez de confiar na contagem.

**E isto valida o escopo da §39 por um segundo caminho.** A interseção com o
`published_manifest` exclui o cartesiano **sozinha**, sem precisar saber o que é v1 nem
carregar uma lista de famílias mortas. Filtro certo pelo motivo certo: se amanhã outra
geração for aposentada, ela fica de fora sem ninguém acrescentar regra.

**A conta dos 607 fecha assim:**

```
607 rascunhos perdidos
  231  publicados        -> perda real, recuperavel, indexada (§42)
  376  cartesiano v1     -> saida correta, DEC-004
```

## 44. O `source_selection_rank` não é identidade — e o validador que o guarda foi escrito para um lote de 300

O par perguntou se recuperar os 231 obriga a renumerar o arquivo, e a pergunta é boa:
`internal/authorialmassdrafts/drafts.go:360` exige **`rank == número da linha`**.

**Primeiro, uma correção minha, e ela é de proveniência de medição.** Eu escrevi ao par
que *"medi `1..7984`, sem buracos"* — **não tinha medido**. Medi depois, provocado pela
resposta dele, e o número está certo:

```
source_selection_rank   n=7984  min=1  max=7984  distintos=7984
contiguo 1..N? True     buracos: 0
```

O fato sobrevive; a proveniência dele não. Fica escrito porque a R3 do contrato separa
amostra de população, e a mesma regra vale para **quem** mediu: "medi" só depois de rodar.

**O rank é posicional e é reatribuído a cada passada.** Comparando o rank do MESMO intent
entre revisões do arquivo:

```
revisao       n      comuns com hoje   rank igual
6d3623c2   7.985           7.984          5.621   (70,4%)
9ac7ff75   7.972           7.971          1.493   (18,7%)
71bfaaac   7.971           7.970            108   ( 1,4%)
```

Não é identidade: é a posição do registro naquela geração. Logo a renumeração que o par
temia **já acontece toda passada** — não é preço que a recuperação introduz.

### E aqui aparece o terceiro caso da mesma família do dia

`authorialmassdrafts.Validate` (`drafts.go:235-259`), chamado pelo gate
`authorial-mass-drafts` (`internal/checks/checks.go:2172`), faz:

```go
if len(candidates) < InitialBlockedBatchSize { … }          // InitialBlockedBatchSize = 300
report.Issues = append(report.Issues,
    ValidateRecords(records, sorted[:InitialBlockedBatchSize]).Issues...)   // so os 300 primeiros
```

e `ValidateRecords` abre com:

```go
if len(records) != InitialBlockedBatchSize {
    issues = append(… "authorial_mass_drafts_count_mismatch" …)   // 7.984 != 300
}
…
candidate, ok := candidatesByRank[record.SourceSelectionRank]      // so ranks 1..300 existem
```

**O validador foi escrito para o lote inicial de 300 do v1** — o mesmo "300 rascunhos +
9.700 expansão" que a DEC-004 condenou — e o corpus que ele valida hoje tem 7.984 do v2.
Medido contra o dado vivo, o join por rank **não fecha para nenhum registro**:

```
data/editorial/authorial_mass_candidate_selection.jsonl   10.000 candidatos, ranks 1..10000
join rascunho -> candidato por rank:  ok=0   rank_ausente=0   divergente=7.984
```

**Não afirmo o veredito do gate, porque não o rodei.** `cmd/check` compila do worktree e o
deploy do par está no ar — a regra que combinamos é não compilar de lá enquanto ele roda.
O que está medido é o **dado**: o join não fecha para nenhum dos 7.984. Por leitura de
código isso obriga `count_mismatch` e milhares de `candidate_mismatch`; se o gate estiver
verde, então ele retorna antes de `ValidateRecords`, e aí o achado é outro e pior — um
validador que nunca alcança a validação. **Rodar `./tools/go-modern run ./cmd/check
authorial-mass-drafts` depois do deploy resolve qual dos dois, e é o próximo passo.**

### A família, nomeada porque é o terceiro caso hoje

| # | Artefato que ficou para trás | Produção que seguiu | Tamanho do silêncio |
|---|---|---|---|
| 1 | `detectNormaSignals`, segunda lista das mesmas siglas (achado do par) | `internal/lexml` resolvia CTN/CPP/CP desde 2026-09-08 | 443 ocorrências de `art. N do CTN` |
| 2 | `validLanes` e `wordCountBands` (§40) | cinco geradores emitem `derivada_de_fonte_oficial` | 1.327 páginas publicadas fora da cadeia |
| 3 | `InitialBlockedBatchSize = 300` (esta seção) | corpus v2 com 7.984 rascunhos | join por rank não fecha para nenhum |

A memória `anti-looping-e-concorrencia` diz que a terceira correção do mesmo subsistema
manda parar e atacar a família inteira. **A família não é "listas de siglas": é artefato
de verificação que ficou preso à geração anterior da produção que ele verifica** — e o
sintoma comum é que cada lado continua passando nos próprios testes, porque nenhum teste
cruza os dois. É por isso que o teste da correção tem de falhar **na lista**, e não no
efeito.

### 44.1. Não é só o tamanho do lote: o arquivo de candidatos inteiro é o cartesiano v1, congelado uma semana antes do v2

A §44 disse que o validador foi escrito para um lote de 300. Fui ver **por que** o join
não fecha, campo a campo, em vez de aceitar a contagem — e a resposta é maior:

```
rascunho linha 1   rank=1
   candidate_id    authorial-mass-candidate-v2-serv-acao-regressiva-estado-cobra-servidor
   intent          serv-acao-regressiva-estado-cobra-servidor

candidato rank 1
   candidate_id    authorial-mass-candidate-busca-apreensao-veiculo-negativa-formal-prazo-sete-dias
   intent          busca-apreensao-veiculo::negativa-formal::prazo-sete-dias
```

O candidato de rank 1 é **chave tripla** — o cartesiano do §43. Censo do arquivo inteiro:

```
data/editorial/authorial_mass_candidate_selection.jsonl
  candidatos                          10.000
  com chave tripla (cartesiano v1)    10.000   (100%)
  sem chave tripla                         0
  mtime                               2026-06-30
  ultimo commit                       34d6df3d  2026-07-02
```

**O v2 substituiu o v1 em 2026-07-09** (`PRECEDENTES_DAS_ORDENS.md:93`). Este arquivo
parou **uma semana antes**. E o join também não fecha por `candidate_id` — testei, para
não culpar a chave errada: **0 de 7.984**. Não é rank desalinhado: são duas gerações
diferentes de ponta a ponta.

**Consequência para a recuperação, e ela inverte a conclusão do par.** O par apontou, com
razão, que `rank` é chave de junção com o candidato (`drafts.go:356`), que entra no hash de
qualidade do refinamento (`refinement_quality.go:1136`) e na comparação de compatibilidade
(`compatibility.go:369`) — e concluiu que a recuperação "paga renumeração ou reconstrução
coordenada". **Esses invariantes já estão quebrados hoje, para 100% do corpus vivo.**
Reinserir 231 registros não pode quebrar um join que não fecha para nenhum dos 7.984.

Isso não torna a recuperação livre: torna o problema **anterior** a ela. Antes de devolver
os 231 é preciso saber o que o gate `authorial-mass-drafts` está de fato afirmando hoje,
porque uma das duas é verdade e as duas são achado:

- ele reprova com milhares de `candidate_mismatch` e ninguém está lendo, ou
- ele passa, e então retorna antes de `ValidateRecords` — um validador que nunca alcança a
  validação.

**Só medi o dado; não rodei o gate** (`cmd/check` compila do worktree e o deploy do par
está no ar). `./tools/go-modern run ./cmd/check authorial-mass-drafts` depois do deploy
decide, e é o primeiro passo depois dele.

## 45. 49 gates nunca rodaram, e a causa é o desempate alfabético do rotativo — corrigido

Enquanto o deploy do par ocupava o worktree, medi a cobertura do runner que existe
justamente para acabar com gate cego. **O runner tem o defeito que ele veio consertar,
na metade que sobrou.**

```
data/ops/gates_rotativos.jsonl — 8 rodadas, 2026-09-05 a 2026-09-10
  gates registrados                    358
  rodaram ao menos uma vez             309
  NUNCA rodaram                         49
  toda rodada terminou exit=1 por orcamento estourado
  executados por rodada: 199, 102, 62, 61, 28, 36, 51 …
```

E os 49 não são aleatórios: são um **sufixo alfabético contínuo**, de
`redesocial-entrega-final` a `zizmor-workflow-security`. Entre eles, `seo`,
`seo-oracles`, `technical-seo-google-contract`, `v2-cross-shard-collision`,
`v2-public-path-collision`, `text-truncation`, `sem-dado-pessoal-em-git`,
`sigilo-sem-texto-claro`, `tool-artifact-provenance`, `sqlite-fts5-corpus-evidence`,
`structured-data-evidence`, `storage-contract` e os onze `social-*`. Rota duplicada, SEO,
sigilo e dado pessoal — o que o §5 chama de inegociável.

### A causa é uma linha, e o comentário ao lado dela já descrevia o defeito

```python
def ordem(n: str) -> tuple[int, str]:
    """O mais antigo primeiro; empate desfeito pelo nome, para ser determinístico."""
    return (-idade(n, ultimo, hoje), n)
```

Gate nunca executado tem idade `10_000` — **todos empatados**. Com o empate desfeito pelo
nome e o orçamento estourando em toda rodada, o fim do alfabeto perde todo dia, e "perder
todo dia" é "nunca rodar".

O mais notável é que o comentário logo abaixo **já dizia isso**, sobre a outra metade:

> *"Em 2026-09-07 sobraram 9, e eram os nove últimos em ordem alfabética entre os
> empatados na idade."*

O conserto de então foi ordenar **os fixos** por idade — correto, e insuficiente: ele
resolve gates de idades **diferentes** e não toca no empate. O sintoma foi visto, nomeado
e medido; a causa sobreviveu duas linhas abaixo. É a mesma forma dos três casos da §44:
metade do conserto pousa.

### O conserto

`desempate(nome, dia)` = `sha256(nome + "|" + data)`. Determinístico **dentro da rodada**
(dois replays do mesmo dia dão a mesma ordem, então o ledger continua auditável) e
**diferente a cada dia** (o sufixo de ontem é o prefixo de algum amanhã). Idade continua
dominando: o sorteio só decide **empate**.

A decisão saiu de dentro de `main()` para `ordem_da_fila(nome, ultimo, hoje)`, no escopo do
módulo — e essa mudança não é cosmética, ver abaixo.

**Efeito medido sobre os 49 reais, com o ledger de verdade:**

```
ANTES (alfabetico)     atrasada · p0-cycle-close · redesocial-entrega-final ·
                       sca-sbom · sca-scorecard · sca-staticcheck · sca-toolchain-* …
DEPOIS (sorteio)       storage-contract · v2-writing-semantic-closure · term-seeds ·
                       social-http-smoke · social-policy · scaled-content-release-verdict ·
                       zizmor-workflow-security · social-cache · text-truncation …
sobreposicao antes x depois        2 de 12
sobreposicao hoje x amanha         2 de 12
```

### A prova por mutação achou um teste meu que não testava

Escrevi primeiro três casos que exercitavam `desempate()` direto. **O mutante que devolvia
`ordem` ao alfabeto SOBREVIVEU**: a função certa continuava certa, e quem voltava a errar
era o chamador. É literalmente `teste-que-reimplementa-nao-testa` aplicado a mim, no mesmo
dia em que eu e o par trocamos essa lição três vezes.

Duas correções: as asserções passaram a ser sobre **`ordem_da_fila`** (por isso a extração
do escopo), e nasceu um caso que assere sobre **`chamados` — quem de fato rodou** — através
de `main()` com os dublês. Cinco mutantes, cinco mortos:

| mutante | reprova |
|---|---|
| desempate volta ao alfabeto | 3 casos |
| semente sem a data (não rotaciona) | 1 |
| idade ignorada na ordenação | 3 |
| `main()` deixa de usar `ordem_da_fila` | 1 |
| `fixos.sort(key=ordem)` removido | 2 |

**O que isto NÃO conserta:** o orçamento continua estourando em toda rodada, e 49 gates
cegos viram "49 gates que agora entram na roda" — não "49 gates que rodaram". A cobertura
real só sobe quando o orçamento ou o custo mudarem, e a coluna de idade do
`--cobertura` é onde isso se lê. O que muda hoje é que a cegueira deixou de ser
**permanente e determinada pela inicial do nome**.

### 45.1. Correção de três pontos da §45, achados por revisão logo depois do commit

**Os 49 não são 47 por acaso: dois são excluídos por desenho, e um deles eu usei como
manchete.** `FECHAMENTO` filtra gates de fechamento de ciclo de **ambas** as listas
(`fixos` e `fila`), mas eles continuam em `todos` e, portanto, em `gates_registrados: 358`.
Nunca podem aparecer no conjunto executado — corretamente.

```
nunca no ledger                                    49
  excluidos por FECHAMENTO (por desenho)            2   redesocial-entrega-final
                                                        p0-cycle-close-indexable-10k
  VITIMAS REAIS                                    47   de sca-sbom a zizmor-workflow-security
```

A §45 e o commit `10aeba8c` nomeiam `redesocial-entrega-final` como o extremo esquerdo do
sufixo faminto. **Ele não é faminto, é excluído.** O intervalo correto começa em
`sca-sbom`. O conserto continua certo; a contagem e o enquadramento não estavam.
O meu próprio `test_1` da bancada já afirmava essa exclusão — eu tinha a evidência do
lado e não a apliquei à população que estava medindo.

**A estimativa de custo decide se o conserto entrega alguma coisa, e ela joga a favor.**
Um gate que nunca rodou não tem duração medida no ledger. Se o desconhecido fosse caro por
padrão, ele subiria à cabeça da fila e seria pulado por não caber, todo dia, para sempre —
e o desempate novo mudaria a lista sem mudar nada. Medido:

```python
CUSTO_DESCONHECIDO = 10.0            # run-gates-rotativos:131
custo = estimado.get(proximo, CUSTO_DESCONHECIDO)    # :513
```

**Dez segundos.** Os 47 entram, começam, e saem da rodada com custo medido — ou com o
piso de corte, que `cortados_por_orcamento` grava por `max` justamente para não rebaixar
medição completa. Ou seja: "entram na roda" **e** rodam, na primeira rodada em que a idade
os põe na frente.

**E `--cobertura` estava ordenando ao contrário da execução.** A linha era
`sorted(((idade, nome) for n in todos), reverse=True)` — que desempata por nome
**descendente**, a ordem oposta à da fila. Quem lesse `--cobertura` para saber quem entra
amanhã via uma lista que a rodada não seguia. As duas passam a ler
`ordem_da_fila`, que é a mesma chave. Sem isso, a §45 mandaria o leitor conferir a
cobertura num painel que discorda do executor.

### 45.2. "Nunca rodou pelo rotativo" não é "nunca foi medido": os cegos de verdade são 13

O par mediu por outro eixo e o número da manchete cai. Reproduzi por leitura própria antes
de aceitar:

```
vitimas reais do desempate                        47
  com wrapper tools/check-<nome>                  34
  SEM wrapper — so rodam por `cmd/check <nome>`   13
```

Wrapper existir **não é alguém rodar** — é alcançabilidade, não cobertura. Mas a distinção
é material, e a prova está na minha própria lista: `text-truncation` **rodou hoje com
exit=0**, pelo wrapper, enquanto o rotativo nunca o alcançou. `sca-sbom`, `seo`,
`sca-staticcheck`, `structured-data-evidence` e `tool-artifact-provenance` também têm
wrapper.

**Os 13 sem nenhum caminho de execução:**

```
sem-dado-pessoal-em-git          sigilo-sem-texto-claro
technical-seo-google-contract    template-skeleton-duplication
term-seed-promotions             utility-marginal-score
v2-acervo-similaridade           v2-internal-link-graph-topology
v2-portfolio-intent-distinctness v2-writing-semantic-closure
social-piso-comparativo          social-policy
social-sem-chave-no-ambiente
```

**`sem-dado-pessoal-em-git` e `sigilo-sem-texto-claro` são LGPD e segredo de justiça** — a
lista taxativa do §2 —, sem nenhum caminho de execução, nenhum dia. São os dois primeiros
da fila, à frente dos `social-*` e do `tool-artifact-provenance`.

**A régua que sai daqui, e vale para as duas sessões:** número que discorda do que o outro
mediu se reconcilia **antes** de virar mensagem. Funcionou nas duas direções hoje — a
correção dos 3.055 veio de mim depois de eu ter dado o número errado ao par; a da atestação
do deploy veio de mim para ele; e uma medição dele que dava "293 cegos" morreu antes de ser
enviada porque discordava dos meus 47. A causa dela era ler `gates` (a lista de executados)
como se fosse a de registrados e procurar lista em `gates_executados`, que é `int` — o
instrumento medindo a coisa ao lado, terceira vez no dia entre nós dois.

## 46. O `authorial-mass-drafts` respondeu: reprova com ~27.831 achados, trunca em 200, e ninguém lê

A §44.1 deixou duas hipóteses e disse que rodar o gate decidiria qual. Rodado contra
HEAD limpo, depois do deploy do par:

```
./tools/go-modern run ./cmd/check authorial-mass-drafts
  exit status 1
  check output truncated: omitted_failures=27631 max_errors=200
```

**~27.831 achados.** É o primeiro ramo: o gate reprova, e o vermelho não chega a ninguém.
E as famílias são mais do que a §44 previa:

```
authorial_mass_drafts_candidate_mismatch          line=58 rank=58   (em todas as linhas)
authorial_mass_drafts_stale_checked_at            checked_at=2026-09-10 expected=2026-06-21
authorial_mass_drafts_thin_section                <draft>:Perguntas frequentes
authorial_mass_drafts_missing_contractual_intent  <draft>
```

**`expected=2026-06-21` fecha o círculo da §44.1.** A data esperada sai do **mesmo arquivo
de candidatos v1** — `authorial_mass_candidate_selection.jsonl`, mtime 2026-06-30, último
commit `34d6df3d` de 2026-07-02, uma semana antes de o v2 substituir o v1. Não é um defeito
com quatro sintomas: é **um artefato congelado antes do v2 servindo de referência a quatro
detectores ao mesmo tempo**.

**E o gate trunca em 200.** Mesmo quem o rodasse veria 200 de 27.831 — a cegueira não era
só de agendamento (§45), era também de saída. Duas camadas independentes escondendo o
mesmo vermelho.

**Não conserto nesta seção**, e o motivo é o mesmo de sempre: consertar o arquivo de
candidatos sem consertar o recorte de 300 (`sorted[:InitialBlockedBatchSize]`, §44) deixa
7.684 reprovando; consertar o recorte sem o arquivo deixa 7.984. São duas coisas presas e
independentes, e a régua do §5 pede saber o que cada uma afirma antes de mexer. Fica com
dono, número e caminho.

## 47. §39 no código: o rascunho sobrevive enquanto a página está publicada

Implementada a proposta da §39, sem desvio do desenho.

```go
// internal/v2ingest/v2ingest.go — ramo de rewrite
total = append(total, accepted...)
if opts.Mode == ModeRewrite {
    preservados, err := rascunhosDePaginaPublicada(projectRoot, stockBeforeUpsert, total)
    ...
    proximo := len(total) + 1
    for indice := range preservados {
        preservados[indice].SourceSelectionRank = proximo
        proximo++
    }
    total = append(total, preservados...)
}
```

`rascunhosDePaginaPublicada` cruza o estoque ANTERIOR (capturado em `:413`, antes do
`existing = nil`) com o `published_manifest` e devolve o que continua no ar e não foi
regravado por este lote. **Zero pacote novo no fecho de atestação**:
`portaljuridico/internal/publishedmanifest` já estava nos 98, via
`internal/authorialmassplan:75`, e não importa `v2ingest` — conferido, sem ciclo.

**O rank não custa nada, e é o ponto que a objeção do par obrigou a provar.**
`nextSelectionRank:1067` devolve **1** em rewrite: os aceitos já recebem 1..N na ordem de
aceitação, toda passada. Os preservados entram **depois**, com N+1..N+K. Nenhum rank de
aceito muda, e `prepared_validation.go:57` — que trata `rank != linha` como **erro fatal**,
não como issue, e roda no caminho transacional do deploy (`plan.go:280`) — continua
satisfeito. Renumerar não é preço da recuperação: é o que o rewrite já faz.

**Manifesto ausente ≠ manifesto ilegível.** Raiz nova (bancada, ensaio) não tem manifesto e
também não tem página publicada: preservar nada é a resposta certa, e o ingest não pode
abortar por isso. Já um arquivo que **existe** e não devolve registro nenhum aborta — nesse
caso não há como provar publicação de ninguém, e "preservar nada" seria o mesmo descarte
silencioso que a §39 existe para impedir. Linha torta isolada não justifica descartar texto
pago: usa-se o que parseou.

**Prova por mutação, quatro mutantes, quatro mortos:**

| mutante | caso que reprova |
|---|---|
| preservação desligada (`if false`) | preserva **e** aborta |
| preserva também despublicado (tira `!publicado[id]`) | descarta despublicada |
| preservados sem renumerar | `rank == linha` |
| manifesto ilegível passa em silêncio | aborta |

O código foi restaurado entre cada mutante por **troca exata de string** — nunca
`git checkout` —, com `gofmt` conferido depois de cada volta.

**O caso que o comentário do `ModeUpsert` descreve e nunca teve como rodar** é o corpo do
teste principal, e foi observação do par: *"reprovação preserva o draft anterior MESMO
QUANDO outro item do mesmo lote é aceito e força a escrita"*. Um teste que só verificasse
"o rascunho continua no arquivo" passaria por acaso num lote sem aceites — não haveria
escrita nenhuma. Por isso o segundo lote sempre aceita uma página, e a asserção cobra
`AcceptedCount == 1` antes de olhar o estoque.

**O que a §39 NÃO faz:** ela **estanca**, não devolve. Os 231 já perdidos continuam só no
git, indexados pela §42. A recuperação é passada própria, depois desta, e tem de decidir o
que fazer com `drafts_expected` (7.984 → 8.215) nos quatro pacotes que ainda derivam piso
dele.

## 48. Quase publiquei que o classificador era órfão. Ele está ligado — e o erro foi meu, de procurar no diretório errado

Ao provar que a §39 não regride nada, fui atrás do instrumento que separa
**regressão** de **dívida** e conclui que ninguém o executava:

```
grep -rn "check-baseline-testes-vermelhos" tools/ ops/ .claude/hooks/
  4 ocorrencias — todas em COMENTARIO
```

Escrevi uma seção inteira chamando-o de "o 312º órfão", com as 223 falhas não
classificadas do log de 2026-09-07 como prova. **O commit falhou por `index.lock` do
par, e nessa janela eu fui conferir mais fundo. Ele está ligado desde sempre:**

```
.githooks/pre-commit:735-736
  if [ -x "$ROOT/tools/check-baseline-testes-vermelhos" ] &&
    baseline_saida="$("$PYTHON_BIN" -I "$ROOT/tools/check-baseline-testes-vermelhos" "$LOG_TESTE_FOCADO" 2>&1)"; then

git config core.hooksPath  ->  .githooks
```

**O repositório usa `core.hooksPath=.githooks`, e eu procurei em `.claude/hooks/`.**
Ausência num diretório que eu escolhi não é ausência — é a memória
`ausencia-de-sinal-nao-e-evidencia`, aplicada a mim, no mesmo dia em que o par e eu
caímos cada um na própria memória escrita.

### E o passo que eu ia commitar teria sido uma máquina de falso positivo

O `2b-bis` que eu escrevi apontava o classificador para `suite-completa.log`. **O
baseline foi medido com o pacote SOZINHO** — o registro de `internal/v2ingest` traz
`duracao_s: 561.331`, que é o pacote isolado — e a `suite-completa` roda tudo em
paralelo. Medido nos dois logs que existem:

```
                         2026-09-05   2026-09-07
internal/v2ingest            83           80     (na suite, em paralelo)
                              80 em comum, 0 novo em 09-07
baseline (isolado, 09-05)      3
```

Comparar as duas populações produziria **~77 regressões falsas por dia**, para
sempre, num gate cuja saída inteira seria falso positivo — exatamente o dano que o
par acabou de consertar no `sem-dado-pessoal-em-git` (dois de dois falsos positivos)
e que o próprio comentário do pre-commit chama de *"o falso positivo caro que este
repositório já pagou várias vezes"*. **O passo foi retirado antes de entrar**, e
`tools/run-qualidade-diaria` volta byte a byte ao que era.

### O que sobra, medido, e é achado de verdade

**A `suite-completa` produz ~77 falhas em `internal/v2ingest` que o pacote isolado
não tem, e isso é estável, não flaky:** 80 dos 83 de 2026-09-05 reaparecem idênticos
em 2026-09-07, zero novos. As famílias são `TestValidateInstalledCanonicalStockSnapshot*`
(37), `TestPrepareTransactionPlan*` (15), `TestReusableSemanticsMemo*`,
`TestPreparedTransactionReuse*`, `TestStockFreshnessSourceCache*` — lease, epoch, ABA
e relógio, o que quebra sob concorrência consigo mesmo.

Isso responde a pergunta que o par levantou (*"baseline apodreceu ou nunca cobriu a
família?"*) **sem esperar a medição isolada**: na mesma data em que o baseline
registrou 3, a suíte já acusava 83. Não apodreceu e não errou — **são condições de
medição diferentes**, e o baseline está certo para a condição em que é usado.

O defeito, então, não é do baseline nem do classificador: é da **`suite-completa`**,
que declara 80 vermelhos num pacote que tem 3. Quem lê o log diário não tem como
saber isso, e é a mesma forma do `max_errors=200` da §46 e do `--cobertura` da §45.1
— o instrumento afirma sobre uma condição que ele não nomeia.

**Conserto proposto, não implementado:** a `suite-completa` serializar os pacotes
sensíveis a lease (`-p 1` para eles), ou o log declarar a condição de execução na
primeira linha, para que ninguém compare com um baseline isolado. Antes disso é
preciso o número isolado de hoje, que está rodando em `wiki-bench-v2ingest`.

Bancada nova, no lugar da que eu ia escrever: `tools/test_baseline_vermelhos_esta_ligado.py`,
6 casos. Ela protege a ligação **real** — que o pre-commit continue chamando o
classificador, que ele receba `$LOG_TESTE_FOCADO` e **não** `suite-completa.log`, e que
`core.hooksPath` continue sendo `.githooks` (se mudar, a ligação deixa de valer em
silêncio) — mais os dois casos do gate em si: regressão reprova, dívida tolera.

## 49. 48 arquivos de produto sumiram da worktree por horas, e nada barrava o `git add` que os apagaria de HEAD

Enquanto esperava a bancada, `git status` mostrou o que ninguém estava olhando:

```
git status --short | grep '^ D' | wc -l   ->  48

data/editorial/refined_public_prose.jsonl        (86 MB)
data/editorial/public_prose_candidate.jsonl      (77 MB)
data/editorial/authorial_mass_scale_shards.jsonl
data/editorial/authorial_mass_legal_signatures.jsonl
data/editorial/semantic_cluster_index.jsonl
data/ops/content_inventory.parquet · external_dedupe_oracle.jsonl · …
```

**A pegada é minha:** a passada `--from 1` do `tools/bootstrap-chain`, hoje de manhã,
preserva-antes-de-mutar — move o canônico para `<nome>.stale-resume-<epoch>-<hash>` e só
o repõe quando o passo fecha. O passo 1 parou no órfão de refinamento pago (§42), e os
canônicos ficaram fora do disco das 11:29 até as 21:03.

### Existir cópia não é existir A cópia

Medi que os 48 tinham cópia preservada e escrevi isso ao par. **Ele mediu melhor:**

```
copia MAIS NOVA de hoje                 11
copia MAIS NOVA de agosto ou 05/09      37
ALGUMA copia que REPRODUZ HEAD          48   <- o criterio certo
```

Restaurar pela cópia mais nova teria posto conteúdo de agosto por cima de 37 arquivos, e
o `git status` ficaria **limpo mentindo**. O critério que vale é sha256 contra
`git show HEAD:<arquivo>`. Reproduzi por conta própria antes de tocar em nada:

```
apagados                                 48
com copia que REPRODUZ HEAD byte a byte  48
restaurados e conferidos DEPOIS de escrever  48
divergentes                               0
```

Restauro por `shutil.copy2` — cópia, nunca `move`: a preservação fica onde está. Nenhum
`git checkout`, nenhum `restore`.

**É a mesma família do `public_path` vazio da §42.1 e do diff-por-linha da §38: a pergunta
não é "existe", é "existe o quê".**

### O custo já tinha sido cobrado, no relógio do par

O par perdeu **435 s** num pre-commit que reprovou sem relação com o trabalho dele:

```
--- FAIL: TestAuthorialMassAntiTemplatePassLinesExposeGlobalBlockerScale
FAIL  portaljuridico/internal/checks  435,5 s

internal/checks/run_context_test.go:1798
  qualityLine := PassLine("authorial-mass-editorial-quality-vectors", ".")
```

`PassLine` executa o gate **contra o worktree real**, o arquivo era um dos 48, e o veredito
do pre-commit é do pacote inteiro. **`internal/checks` ficou travado para as duas sessões**
enquanto a cadeia estivesse no meio — e o sinal (`authorial_mass_quality_vectors_missing`)
é preciso sobre o arquivo e mudo sobre a causa. Fica nomeado: teste de contrato que lê o
worktree transforma "cadeia em regeneração" em "pacote vermelho", sem dizer isso.

### O gate que faltava

`tools/check-produto-nao-some-do-worktree` (`49bb6a03`), ligado ao `.githooks/pre-commit`:

- **reprova** produto rastreado ausente **sem** cópia ao lado;
- **não acusa** deleção preservada — preservar-antes-de-mutar é o comportamento correto da
  cadeia, e acusá-lo faria a saída inteira ser falso positivo, que é o que faz gate deixar
  de ser lido (o par acabou de consertar exatamente isso no `sem-dado-pessoal-em-git`, com
  dois de dois falsos positivos);
- **ignora** deleção já estagiada: ali a decisão foi tomada e o lugar de discuti-la é a
  revisão do commit;
- **imprime a cardinalidade na primeira linha**, antes de qualquer caminho.

Ligado ao pre-commit, e não solto em `tools/`: gate sem runner é o 312º órfão — medido
hoje, `run-qualidade-diaria` não faz glob de `tools/check-*`, e
`generate-varredura-bateria-gates`, que faz, não está sob timer nenhum. A mensagem de
reprova diz **como sair do caminho** (estagiar a remoção deliberada), porque gate que barra
sem dizer a saída vira contorno com `--no-verify`.

8 casos, 4 mutantes mortos: qualquer vizinho contando como preservação · deleção já
estagiada entrando na conta · filtro de árvore de produto removido · cardinalidade saindo
da primeira linha.

**E a medição da bancada foi refeita por causa disto.** O restauro dos 48 aconteceu **com a
`wiki-bench-v2ingest` rodando**, e há testes desse pacote que leem o worktree vivo
(`TestCurrentLegalFacts*LiveShard`). Metade da execução viu os arquivos ausentes e a outra
metade presentes: medição contaminada não é medição pequena, é medição inválida. Parada e
relançada às 19:12 com a worktree em HEAD.

### 47.1. A régua do veredito da bancada, escrita ANTES do número

A §0.5.1 deste dossiê registra por que isto existe: naquele dia a primeira leitura que eu ia
reportar era "+30%", vinda de uma fatia escolhida **depois** de ver o resultado. A régua
pré-registrada foi o que impediu. Esta medição ainda não tinha uma, e o número chega em
minutos.

**O problema concreto:** o baseline dos 3 vermelhos de `internal/v2ingest` foi medido em
`e21021ae` (2026-09-05) e HEAD andou muito desde então — o `f1781505` do par, a atestação
regenerada, os 48 canônicos restaurados. Se o isolado der 5, sem régua eu escolheria a
interpretação depois de ver o número.

**A régua, com os três desfechos e a ação de cada um:**

| resultado da bancada isolada | veredito | ação |
|---|---|---|
| falhas ⊆ {`TestCurrentImobiliario09LegalFactsLiveShard`, `TestCurrentLegalFactsLiveFamilia13AndImobiliario11`, `TestCurrentLegalFactsLiveImobiliario05`} | sem regressão | **commita** |
| qualquer falha em `rascunho_de_pagina_publicada_test.go`, `TestUpsertMode*`, `TestAppendMode*`, `TestRoundTripDraft*`, `TestDuplicatePhrase*`, `TestNextSelectionRank` | **é minha** | **não commita**, conserta |
| falha fora do baseline e fora dessa lista | deriva desde 2026-09-05 | `git log --oneline e21021ae..HEAD -- internal/v2ingest/` **antes** de atribuir a mim |

E o veredito final não sai do meu olho sobre a lista: passa por
`./tools/check-baseline-testes-vermelhos <log>`, que nomeia cada falha e é **o mesmo juiz
que o pre-commit vai usar** — se ele reprovar, o commit não entra de qualquer forma.

**Depois do commit, a verificação que o fixture de 3 registros não dá.** Com a atestação
batendo, `./tools/ingest-v2-stock --prepare-only` fica destravado, e `plan.go:280` chama
`validatePreparedDraftSet` sobre o conjunto **preparado real** — 7.984 aceitos mais os
preservados —, cobrando `rank == linha` e unicidade em escala. É a prova do desenho de rank
que a §39 prometeu e que a atestação do par bloqueou na primeira tentativa. Depois da
bancada, nunca concorrente com ela.

**E uma conferência barata antes de retomar a cadeia:** os canônicos que eu restaurei
tinham sido movidos para `.stale-resume-*` como parte de uma transação **retomável**. Falta
confirmar se o `--from N` seguinte aceita o canônico presente onde o recibo o esperava
movido, ou se ele re-preserva por cima. Não bloqueia nada agora — mas é o tipo de coisa que
não se descobre no meio de uma passada de 600 s.

### 47.2. O número da bancada, medido contra a régua que já estava escrita

```
ok  	portaljuridico/internal/v2ingest	834.434s
EXIT=0
```

`./tools/go-modern test -count=1 -timeout 30m ./internal/v2ingest/`, sob
`systemd-run --user --unit=wiki-bench-v2ingest --property=MemoryMax=5G
--property=Nice=10`, worktree limpa dos 48 canônicos restaurados, sem passada da
cadeia concorrente. **Zero falhas.**

Pela régua da §47.1: `∅ ⊆ {os 3 do baseline}` ⇒ **sem regressão, commita.** E
nenhum dos seis nomes da linha do meio (`rascunho_de_pagina_publicada_test.go`,
`TestUpsertMode*`, `TestAppendMode*`, `TestRoundTripDraft*`,
`TestDuplicatePhrase*`, `TestNextSelectionRank`) apareceu.

**Um número a mais do que a régua previa — e eu errei a atribuição dele, pela
segunda vez hoje.** Os três vermelhos do baseline —
`TestCurrentImobiliario09LegalFactsLiveShard`,
`TestCurrentLegalFactsLiveFamilia13AndImobiliario11`,
`TestCurrentLegalFactsLiveImobiliario05` — **passaram**. Eu escrevi ao par que a
causa era o trabalho dele em `legalfacts`. **O par recusou o crédito e foi ler o
critério, que me desmente:** `internal/v2ingest/current_legal_facts.go:2299`
julga o texto visível e as fontes oficiais lidas de
`data/editorial/v2_pages/<shard>.jsonl` e **não passa por `internal/legalfacts` em
lugar nenhum**; e `directLegalValidatorSnapshotAsOf` é data **literal**
(2026-07-11), então também não é gate que virou de veredito pelo relógio.

O discriminante que a §47.1 mandava rodar aponta para **um único commit** na
janela: `70091b32` (2026-09-05), *"artigo." com ponto em 8 páginas publicadas — o
gate apontava erro de português achando que apontava lacuna de direito*, na
família `currentLegalFact`. Provável, não medido: provar exigiria rodar os testes
contra o shard em `e21021ae`, e worktree não se reverte para isso.

Registro certo: **verde hoje, medido; causa provável em `70091b32`, e não no
trabalho de nenhum de nós dois hoje.** O que quase aconteceu tem nome — número que
CONCORDA com o que se quer ouvir é o que passa sem conferência —, e foi o par
quem o pegou, verificando um crédito que eu estava lhe dando de graça.
`data/ops/testes_vermelhos_conhecidos.json` sai da mão de quem os mediu, com esse
motivo escrito, e não de carona num commit desta frente.

Duração: **834 s**, contra os 561 s conhecidos do pacote. A diferença é
compilação, e ela explica por que a primeira tentativa morreu no `-timeout 10m`
padrão: o teto era o problema, não o patch.

**Ordem do que sai agora:** a §39 (código, três testes, atestação e este dossiê)
por pathspec, com o índice compartilhado respeitado — o par estava commitando
`internal/checks/sem_dado_pessoal_em_git_test.go` na mesma janela, e commit por
pathspec não varre o que é dele.

### 47.3. O que a passada de 834 s cobre, e o que ela não cobre

Correção de escopo, escrita porque a §47.2 lê melhor do que a verdade permite.

**A bancada de 834 s mediu a árvore da atestação `fe883ea…`.** Depois dela eu
achei, conferindo o diff antes de commitar, que a função nova tinha sido inserida
logo abaixo do comentário de `nextSelectionRank`: o comentário ficou colado na
função errada e `nextSelectionRank` ficou sem documentação nenhuma — `godoc`
atribuiria as quatro linhas à função nova. Comentário na função errada é pior que
comentário ausente: o ausente manda ler o código, o errado manda acreditar. Mover
as quatro linhas de volta mudou bytes do diretório, e a atestação hasheia o
diretório, então **o commit leva `9789d69dcc42d9cc1d65ec051c8617311d24d74e03ce669563b211bb2f3106b8`,
que nunca passou por bancada de pacote inteiro.**

O que cobre a árvore commitada:

| verificação | escopo | resultado |
|---|---|---|
| `go-modern test -run 'TestRewritePreserva\|TestRewriteSemManifesto\|TestRewriteAborta\|Attestation\|Fingerprint'` | **26 testes** casados, entre eles `TestCompiledValidatorFingerprintAttestationMatchesCurrentSource` | `ok 42,101s` |
| `gofmt -l internal/v2ingest/v2ingest.go` | formatação | vazio |
| `./tools/go-modern generate ./internal/v2ingest` | atestação contra o grafo real | exit 0 |
| bancada de 834 s | árvore **anterior** (`fe883ea…`) | `ok`, zero falhas |

**E a contagem dos 26 foi medida, não presumida.** `go test -run X` imprime `ok`
mesmo quando `X` casa **zero** testes — um `ok` de padrão vazio é indistinguível de
um `ok` de suíte verde, e eu não passei `-v`. O discriminante custou zero
compilação: `grep -n "^func Test" internal/v2ingest/validator_fingerprint_graph_test.go`
devolve 28 funções, 26 delas casando `Attestation|Fingerprint`. Sem essa conferência
a linha acima seria exatamente o tipo de verde que não prova nada.

**O que ainda falta para a §39 estar VERIFICADA, e não só verde:** `--prepare-only`.
Ele valida a atestação contra o grafo real **e** cobra `rank == linha` e unicidade
em `validatePreparedDraftSet` (`plan.go:280`) sobre o conjunto preparado real —
7.984 aceitos mais os preservados —, que é a escala que o fixture de três registros
não alcança. Enquanto ele não rodar, o desenho de rank está provado em três
registros e argumentado em 8.215.

E o efeito colateral esperado fica declarado **antes** de aparecer, para não ser
lido como regressão: se `drafts_expected` subir de 7.984 para 8.215, os quatro
pacotes que derivam piso dele — `jsonlstream`, `scaledcontentreleaseverdict`,
`authorialmassstock`, `publicproselanguagepatterns` — vão acusar. Isso é o
instrumento funcionando.

### 50. A régua do veredito do prompt novo, escrita ANTES de ler a primeira linha

Terceira vez hoje que a régua sai antes do número, e desta vez o número já está
sendo produzido em **produção**: `bin/cerebro` foi reconstruído e
`wikijuridica-cerebro` reiniciado às 20:00:23. Armar o vigia sem critério seria
escolher a leitura depois.

O que o commit `8b1e7584` afirma, e como cada afirmação se refuta:

| afirmação | como se lê na linha nova | refuta se |
|---|---|---|
| o modelo para de gastar decode com súmula | `eval_tokens` mediano contra as linhas do balde `modelo` sem `versao_do_prompt` | não cair; mediana anterior conhecida: 597 linhas do balde `modelo` |
| a súmula não se perde | `sumulas_pelo_parser > 0` em toda ementa que cita súmula | qualquer ementa com súmula e `sumulas_pelo_parser == 0` |
| o prompt pega | `sumulas_devolvidas_pelo_modelo` perto de zero | se ficar alto: o modelo ignorou a instrução, e aí **a instrução é que está errada**, não o desenho — o parser continua entregando, mas o ganho de decode não vem e o commit vira meia-verdade |
| nada regride | `dispositivos` continua trazendo a norma/artigo do modelo | linha com `sumulas_pelo_parser > 0` e zero URN `urn:lex` onde a anterior tinha |

E o desfecho "o modelo insiste" tem ação escrita: não se aceita a súmula dele
(duplicaria), não se conta como alucinação (ela está no texto) — reescreve-se a
instrução e mede-se de novo, com `versao_do_prompt` nova. É para isso que o campo
existe.

### 50.1. O que a medição das súmulas ainda não respondeu, e a ordem em que se responde

**Os 121 são defeito reparável, não só evidência.** `parser acha MAIS: 121`
significa que 121 acórdãos estão **agora** em `dispositivos_promovidos.jsonl` com
vínculo de súmula faltando — e é esse arquivo que `generate-lei-artigo-pages:461`
e `generate-acordao-pages:413` leem. O prompt novo só alcança extração futura:
`UltimaExtracaoPorChaveEModelo` chaveia por `chave+modelo`, **não** por versão de
prompt, então as 1.204 já concluídas nunca voltam à fila. O reparo é uma passada
do parser sobre os textos do payload — zero chamada ao modelo —, e
`cmd/medir-sumula-parser-vs-modelo` já nomeia cada acórdão e cada URN que falta.

**E a pergunta que decide se vale ordenar a fila por valor vem ANTES do
ordenador.** O modelo contribui hoje com 285 URNs LexML em 598 chamadas. A mesma
maquinaria determinística que valida cada uma delas já existe e já filtra todo
item do modelo — `NormaAtestadaNoTexto` exige a norma literal no texto,
`reArtigoNaNorma` separa "art. 1.022 do CPC/2015", `urnDaCitacao` produz a URN, e
`reSinalDeNorma` já detecta presença de norma. Se a detecção for mecanicamente
derivável como a da súmula foi, a contribuição real do modelo encolhe para o
pareamento artigo↔norma — ou para nada.

Isso decide se ordenar importa: 29.143 chamadas × 59,3 s são 20 dias, e um
ordenador que otimize a ordem de trabalho que não deveria acontecer é o pior
retorno possível. **A ordem é: medir o lado lex primeiro, com zero chamada, sobre
os mesmos 599 acórdãos rotulados.** E qualquer ordenador que nasça depois se
valida contra esse mesmo conjunto — uma pontuação que não separa os casos de
rendimento 285 dos de rendimento zero em dado que já temos não vai separar em
dado que não temos.

**Fora do meu escopo desde a ordem do dono desta noite:** o `--prepare-only` da
§39 e a recuperação dos 231 rascunhos ficam com a frente de ingestão/publicação.
Registrado aqui para não sumir, não para ser cobrado desta frente.

### 50.2. A régua da §50 cobrou, e o commit `8b1e7584` errou o título

Dez linhas com `versao_do_prompt=sem_sumula_v2` já em produção, contra as 604 do
mesmo balde sem ela:

| arm | n | `eval_tokens` mediana | `prompt_tokens` mediana | dispositivos/linha | URNs LexML/linha |
|---|---|---|---|---|---|
| prompt antigo | 604 | **81** | 688 | 1,99 | 0,48 |
| prompt novo | 10 | **80** | 713 | **2,90** | **1,00** |

**A saída NÃO caiu.** A mensagem de `8b1e7584` diz "75% menos saída", e isso está
errado como afirmação: os 75,2% eram a FATIA das URNs do modelo que eram súmula,
não uma redução medida de `eval_tokens`. A régua da §50 nomeava exatamente esta
coluna, e ela diz 80 contra 81 — dentro do ruído, não uma queda.

**O que subiu, e muito:** dispositivos por linha de 1,99 para 2,90 (+46%) e URNs
LexML por linha de 0,48 para 1,00 (**+108%**). O par mais forte é o mesmo acórdão
nos dois braços: `1460091` deu `eval=38, 1 dispositivo` no prompt antigo e
`eval=297, 4 dispositivos (2 LexML)` no novo. Mesma entrada, mesmo modelo,
temperatura 0.

**E a régua já apontou por que a saída não caiu:** `sumulas_devolvidas_pelo_modelo`
é maior que zero em **4 das 10** linhas (2, 1, 3, 3). O modelo continua escrevendo
súmula apesar de o prompt mandar ignorá-la. Pela ação escrita na §50, isso não é
defeito do desenho — o parser entrega do mesmo jeito e nada se perde —, é
**instrução que pegou só em parte**, e o conserto é redação nova com
`versao_do_prompt` nova, medida contra este mesmo braço. Não se conserta hoje: com
n=10 eu estaria escolhendo a redação pelo ruído.

O título correto do que `8b1e7584` + `ca014088` entregam é **mais recall pelo
mesmo custo de saída**, não "menos saída". Fica registrado aqui porque a sessão
par já estava citando o número de volta, e número errado que circula entre dois
dossiês vira fato medido sem ninguém ter medido — que é a assimetria que a gente
nomeou hoje de manhã.
