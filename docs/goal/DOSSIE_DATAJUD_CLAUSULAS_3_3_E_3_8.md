# Dossiê das cláusulas 3.3 e 3.8 do Termo de Uso da API Pública do DataJud

> **O que este documento é, e o que ele não é.** Este é o **insumo** da entrega
> `F4-parecer-da-fase-3-3` (`content/redesocial_entregas.json`), montado até a fronteira que o
> próprio campo `motivo` daquela entrega fixou: *"o parecer sobre as cláusulas 3.3 e 3.8 do termo do
> DataJud é ato de advogado sobre relação contratual com o CNJ: sai sob a OAB/RJ 227191 e é
> assinatura do dono, não produto de modelo"*.
>
> **Este documento não é o parecer e não satisfaz a entrega.** A prova da entrega é
> `docs/data-sources/PARECER_DATAJUD_3_3_3_8.md`, que **não foi criado aqui de propósito**: criá-lo,
> ainda que como esqueleto, faria o gate enxergar um parecer que o advogado inscrito não escreveu —
> a mesma classe de defeito que um agente emitindo `reprovada_em_auditoria_humana`.
>
> Aqui há texto oficial transcrito, medição conferida no disco, estado do código e **perguntas**.
> Nenhuma conclusão jurídica sobre a licitude do uso é oferecida, porque essa conclusão é do dono.

- **Montado em:** 2026-09-05 (acessos à rede às 18:57–19:00 BRT, `-03:00`).
- **Identidade de saída usada em toda requisição:**
  `Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; dossie-datajud)`.
- **Cópia preservada das fontes baixadas:** `/opt/wiki/.agents/runtime/dossie-datajud/2026-09-05/`
  (PDF, extração em texto, três páginas da wiki, a página institucional e `SHA256SUMS.txt`).

**Colisão de nomes que confunde quem chega agora:** o identificador da entrega é
`F4-parecer-da-fase-3-3` — o "3.3" ali é a **Fase 3.3 do roadmap**, e não a cláusula 3.3. No
`FONTES_DIARIAS.md`, por sua vez, "§3.3" é a **seção** que trata dos feeds do STJ fechados
(linha 50), enquanto a análise do DataJud está na **§3.1** (linhas 62–81). As três numerações "3.3"
são coisas diferentes e coexistem nos documentos vivos do repositório.

---

## 1. As duas cláusulas, no texto oficial e literal

### 1.1 Proveniência da fonte primária

| item | valor medido |
|---|---|
| documento | **Termo de Uso da API Pública do DataJud, Versão 1.2 — Brasília-DF, 27 de novembro de 2023** |
| URL | `https://formularios.cnj.jus.br/wp-content/uploads/2023/11/Termos-de-uso-api-publica-V1.2.pdf` |
| status HTTP | **200**, direto (`num_redirects=0`, conferido) |
| tipo e tamanho | `application/pdf`, **108.214 bytes**, PDF 1.7, **3 páginas** |
| SHA-256 do PDF | `2b974d5e580943981ad31bec8590200402ed29d79f58004d15d34a70aa307dd2` |
| SHA-256 da extração `pdftotext -layout` | `928106bf4ffec66b9c72b9121d588af77feffabf51676cc23d95473cf8581cea` |
| data e hora de acesso | 2026-09-05, 18:57 BRT |
| caminho para o PDF | link "Baixar o Termo de Uso" em `https://datajud-wiki.cnj.jus.br/api-publica/termo-uso/` (HTTP **200**, 15.893 bytes, SHA-256 `e7c686c9bfd23fddc93e3de3069c66e42981fc863717705a2b565457b65f77ae`) |

Fontes secundárias baixadas na mesma passada, todas **HTTP 200**:

| URL | bytes | SHA-256 |
|---|---|---|
| `https://datajud-wiki.cnj.jus.br/api-publica/acesso/` | 14.683 | `8855e0d92ca79618dbdee5c20dac9541859168622d85d4bb09be221e424bb492` |
| `https://datajud-wiki.cnj.jus.br/api-publica/` | 13.715 | `391b616a0af1e4b6862f4eeb9c29534ee9ed902694a5777fea82371e67e70e74` |
| `https://www.cnj.jus.br/sistemas/datajud/api-publica/` | 275.322 | `3a2a5ba381f24f6a55cc8c3a46ca825713841d8280a7176fdeb24f78e43849eb` |

Esta última é o endereço que a **cláusula 1.1 incorpora por referência** ao Termo ("bem como os
demais termos e condições presentes no endereço eletrônico
`https://www.cnj.jus.br/sistemas/datajud/api-publica/`, no momento da utilização do serviço"). O
que ela diz, no ponto: os dados "são rigorosamente aderentes aos critérios estipulados pela
**Portaria n. 160 de 09/09/2020**" e podem ser explorados "em variados contextos, incluindo
pesquisa acadêmica, desenvolvimento de aplicativos que facilitem o acesso à informação jurídica e
até mesmo análise de tendências e padrões do sistema de Justiça, **desde que respeitem os critérios
especificados no Termo de Uso**".

### 1.2 Cláusula 3.3 — transcrição literal

> **3.3.** A API é fornecida exclusivamente para fins legais, não comerciais e autorizados, sendo
> seu uso indevido, abusivo, ilegal, malicioso ou imoral estritamente proibido.

*(Termo de Uso da API Pública do DataJud, v1.2, seção "3. 3 RESPONSABILIDADES", página 1 do PDF. Citação
identificada da fonte oficial primária acima.)*

### 1.3 Cláusula 3.8 — transcrição literal

> **3.8.** O usuário concorda em não modificar, distribuir, vender ou explorar comercialmente a API
> ou qualquer informação derivada dela.

*(Mesma fonte, mesma seção, também na página 1 do PDF.)*

A página `api-publica/termo-uso/` da wiki do CNJ reproduz as duas cláusulas com **texto idêntico**
ao do PDF, num quadro "Atenção!" que também destaca 1.2, 3.2, 3.6 e 3.9. As duas fontes conferem
entre si.

### 1.4 As cláusulas vizinhas que o parecer não pode ignorar — transcrição literal

> **1.2** O usuário manifestará tacitamente sua aceitação às condições deste termo ao utilizar a
> interface.

> **3.9.** O usuário concorda em dar ciência ao CNJ de qualquer informação, notícia, estudo,
> relatório ou documento de qualquer natureza que seja disponibilizado ao público em geral.

> **3.13.** O usuário concorda em não realizar mais de 120 requisições por minuto, a menos que
> tenha autorização expressa por escrito do CNJ.

> **3.22.** O CNJ se reserva o direito de alterar estes termos e condições a qualquer momento, sem
> aviso prévio.

> **4.2.** O usuário concorda em não coletar, armazenar ou processar dados pessoais originários da
> API ou realizar cruzamentos de informação para esse fim, exceto conforme permitido pela LGPD e
> outras leis e regulamentos aplicáveis.

> **5.1** As Partes elegem o foro da Comarca de Brasília/DF para a resolução de quaisquer
> controvérsias oriundas deste termo, renunciando a todo e qualquer outro, por mais privilegiado
> que seja.

### 1.5 Achados sobre o texto vigente — o que não bate com o que o repositório supõe

**Achado 1 — a numeração confere; a redação de 3.8 citada no plano, não.**
`docs/goal/PLANO_REDE_SOCIAL.md` (§2, "DataJud — o que o termo de uso realmente permite") cita:

> "**3.8** — 'não modificar, distribuir, vender ou explorar comercialmente a API ou qualquer
> informação derivada dela **sem autorização prévia por escrito do CNJ**'."

O trecho em negrito **não existe na cláusula 3.8** do documento vigente. A 3.8 termina em "derivada
dela." A expressão "autorização expressa por escrito do CNJ" aparece **uma única vez** no Termo, e
é da **cláusula 3.13** — a das 120 requisições por minuto. Conferência feita por busca literal:
`autorização`/`escrito` no PDF ocorrem só nas linhas de 3.3 ("autorizados") e 3.13 ("autorização
expressa por escrito"); nas três páginas da wiki e na página institucional do CNJ, nenhuma
ocorrência da expressão junto de 3.8 (as duas ocorrências de "escrito" em
`cnj.jus.br/sistemas/datajud/api-publica/` são do item de menu "Escritório Digital").

Consequência direta para a entrega irmã: **`F4-peticao-ao-cnj` está formulada como "pedido de
autorização escrita ao CNJ para a cláusula 3.8"**, mas a 3.8, como redigida, **não prevê válvula de
autorização escrita**. Quem prevê autorização escrita é a 3.13, e só quanto ao teto de requisições.
Isso não torna o pedido impossível — o CNJ pode autorizar o que quiser, e a 3.22 mostra que ele se
reserva alterar o termo — mas muda a natureza do que se pede: não é o exercício de uma exceção
prevista no contrato, é **pedido de autorização não prevista**. O parecer precisa fechar isso antes
de a petição ser redigida.

**Achado 2 — a paráfrase de 3.3 no repositório é mais estreita que o texto.**
`docs/data-sources/FONTES_DIARIAS.md:70-71` resume 3.3 como uso "exclusivamente para fins **não
comerciais**". O literal é "exclusivamente para fins **legais, não comerciais e autorizados**". São
três qualificadores cumulativos, e "autorizados" é o mais indeterminado dos três — não há no Termo
definição do que seja "fim autorizado", nem procedimento de autorização, salvo a menção da 3.13.

**Achado 3 — o plano cita "Termo de Uso v1.1" como fonte primária lida.**
`PLANO_REDE_SOCIAL.md` §2 abre com "Fonte primária lida: Termo de Uso da API Pública do DataJud,
**v1.1** (CNJ)". A única versão que o CNJ publica hoje na página de termo de uso é a **V1.2, de
27/11/2023**. As URLs análogas para V1.1 e V1.3 no mesmo diretório
(`.../2023/11/Termos-de-uso-api-publica-V1.1.pdf` e `...-V1.3.pdf`) devolveram **404** em
2026-09-05. Isso prova que **essas URLs não existem** — **não** prova que a v1.1 nunca existiu.
**Não apurei** onde o texto da v1.1 estaria arquivado, e o repositório não guarda cópia dela.
Enquanto isso não for apurado, a citação de 3.8 com o acréscimo do Achado 1 fica **sem fonte
oficial**.

**Achado 4 — defeitos de forma no próprio documento oficial, registrados como observação.**
O título da seção 3 sai do PDF como "**3. 3 RESPONSABILIDADES**" (numeração duplicada por erro de
formatação); as cláusulas **3.10 e 3.16 têm texto idêntico** ("O CNJ se reserva o direito de
monitorar o uso da API e tomar medidas para proteger seus direitos e interesses legais"). Nenhum
dos dois altera 3.3 ou 3.8 — ficam registrados porque quem citar o documento vai encontrá-los.

**Achado 5 — vigência é datada.** Pela cláusula 3.22 o CNJ altera o Termo "a qualquer momento, sem
aviso prévio". Tudo acima vale para o documento servido em **2026-09-05**, com os hashes desta
seção. Qualquer parecer assinado depois disso deve reconferir o hash do PDF antes.

---

## 2. O que `docs/data-sources/FONTES_DIARIAS.md` exige que o parecer responda

O arquivo é `docs/data-sources/FONTES_DIARIAS.md` (297 linhas). A exigência do parecer está em
**uma única frase**, ao fim da §3.1 (linhas 77–81):

> "O DataJud fica reservado para **estatística agregada** (ex.: volume de processos por assunto e
> tribunal), que é uso informativo, sem exploração comercial da informação derivada — e mesmo assim
> só depois de parecer próprio sobre 3.3/3.8."

**Achado 6 — o documento cobra o parecer, mas não enumera as perguntas dele.** Não há em
`FONTES_DIARIAS.md` uma lista de quesitos. O que existe são as premissas que a §3.1 e a §3.0-bis
afirmam, e cada premissa afirmada é uma pergunta que o parecer tem de confirmar ou derrubar. Listo-as
uma a uma, como perguntas, sem respondê-las:

1. **A premissa central da §3.1, item 2:** o texto diz que a cláusula "restringe **este canal**,
   aceito tacitamente pelo uso", e que "o portal tem CTA de contratação". *O parecer precisa
   responder: um portal que exibe CTA de contratação de advogado incorre em "fim comercial" da 3.3
   quando o que consome da API é agregado estatístico que não aparece em página pública?*
2. **A premissa da §3.1, parágrafo final:** "estatística agregada … é uso informativo, sem
   exploração comercial da informação derivada". *É afirmação, não demonstração. O parecer precisa
   responder: agregado de contagem por assunto é "informação derivada" da API para efeito da 3.8?
   E se for, a 3.8 proíbe usá-la internamente, ou só "modificar, distribuir, vender ou explorar
   comercialmente"?*
3. **A distinção que a §3.1 não faz:** ela foi escrita sobre a coleta **agregada**. *O parecer
   precisa responder separadamente pelo segundo uso, que nasceu depois dela: a consulta por número
   de processo servida a advogado assinante (seção 4 deste dossiê).*
4. **A qualificação do risco fixada na §3.0-bis para o DOU, por analogia expressa:** "a natureza do
   risco **não é direito autoral** (os atos são públicos) — é **inadimplemento de termo de uso**,
   praticado por um advogado inscrito na OAB, num portal que tem CTA de contratação". *O parecer
   precisa responder: no DataJud, a natureza do risco é a mesma? E qual é a consequência disciplinar
   possível, se houver, sob o Código de Ética, para inadimplemento contratual do inscrito?*
5. **A tabela de fontes (linha 57) classifica o DataJud como fechado, remetendo à §3.1**, sem
   veredito próprio. *O parecer precisa responder qual é o veredito — fechado, condicionado ou
   liberado — e,
   se condicionado, condicionado a quê exatamente.*
6. **A §3.0 fixa que "a proveniência de cada página registra qual base legal a autoriza — nunca um
   art. 8º genérico".** *O parecer precisa responder: se algum dia um número vindo do DataJud
   aparecer em página pública, qual é a base legal a registrar na proveniência daquela página —
   Lei 9.610/98 art. 8º, a Portaria CNJ 160/2020, o próprio Termo, ou nenhuma delas?*
7. **A obrigação da 3.9 não é mencionada em lugar nenhum do repositório.** *O parecer precisa
   responder: publicar estudo, relatório ou página baseada no agregado dispara o dever de "dar
   ciência ao CNJ"? Em que forma e para qual endereço?*
8. **A questão do sujeito.** As cláusulas falam em "o usuário", e a 1.2 diz que a aceitação é tácita
   pelo uso. *O parecer precisa responder quem é o usuário aqui: Rafael Toledo pessoa física, a
   pessoa jurídica do escritório, o portal wikijuridica.com.br, ou cada advogado assinante do
   produto da rede social que dispara a consulta.*
9. **A cláusula 4.2 e o cruzamento.** O `ranking_nacional.json` cruza contagens do CNJ com títulos
   do acervo (`content/pages.json`). *O parecer precisa responder: cruzamento sem dado pessoal é
   alcançado pela 4.2, cuja vedação é a cruzamentos "para esse fim" — o fim de coletar, armazenar
   ou processar dado pessoal?*
10. **O foro da 5.1 é Brasília/DF.** *O parecer precisa dizer se isso muda a avaliação prática do
    risco para um inscrito na OAB/RJ.*

---

## 3. A medição que antecipou a questão — 283.415.422 processos

### 3.1 Onde o número está, e ele confere

- **Arquivo:** `data/research/datajud/ranking_nacional.json`, campo `processos_totais`, linha 7035
  do JSON formatado.
- **Valor:** `283415422`.
- **Data da coleta declarada no próprio artefato:** `collected_at =
  2026-08-07T13:46:38.776131+00:00`; os 22 arquivos por tribunal trazem o mesmo carimbo.
- **Conferência exata feita agora:** a soma do campo `processos` dos **22** arquivos irmãos
  (`data/research/datajud/<alias>.json`) dá **283.415.422** — igualdade exata, não aproximação.

| tribunal | processos | tribunal | processos |
|---|---:|---|---:|
| tjsp | 74.492.169 | trf1 | 12.354.076 |
| tjmg | 36.595.940 | tjsc | 10.718.137 |
| tjrj | 23.117.604 | tjgo | 7.082.339 |
| trf3 | 17.385.970 | trf5 | 7.044.288 |
| tjba | 15.453.689 | tjpe | 6.721.324 |
| trf4 | 14.494.881 | trt2 | 5.235.660 |
| tjrs | 13.995.914 | tst | 4.891.946 |
| tjpr | 12.751.818 | tjce | 4.691.760 |
| trf2 | 4.526.294 | trf6 | 4.490.532 |
| trt15 | 3.665.445 | stj | 3.592.561 |
| tse | 85.898 | stm | 27.177 |

### 3.2 De onde ele saiu

Da ferramenta `tools/generate-datajud-corpus` (Python), que consulta
`https://api-publica.datajud.cnj.jus.br/api_publica_<alias>/_search` com `Authorization: APIKey`
(chave **pública**, divulgada pelo próprio CNJ em `datajud-wiki.cnj.jus.br/api-publica/acesso`). Por
tribunal ela faz **quatro** requisições: uma de total (`size: 0`, `track_total_hits: true`,
`query: {match_all: {}}`, lendo `hits.total.value`) e três de agregação por termos
(`assuntos.nome.keyword`, `classe.nome.keyword`, `grau.keyword`), com pausa entre elas. O total
nacional é `sum(r["processos"] for r in coletados)` — soma de contagens, sem deduplicação entre
tribunais.

**Volume real daquela rodada, contado nos artefatos:** 22 tribunais × (1 total + 3 agregações) =
**88 requisições**, das quais **87 gravaram resultado** e **1 falhou com HTTP 429 (Too Many
Requests)** — a agregação de assuntos do `tjpe`, cujo arquivo registra a falha em `falhas`.

**Medição colateral que interessa ao quesito da 3.13:** pelos horários de gravação dos arquivos
(`data/research/datajud/`, o primeiro às 10:47 e o `tjpe` às 10:51 de 2026-08-07), o 429 chegou
depois de cerca de 36 requisições em torno de quatro minutos — algo próximo de **9 requisições por
minuto**, uma ordem de grandeza abaixo do teto de 120/min da cláusula 3.13. Como a APIKey é
**pública e compartilhada por todos os usuários**, o dado sugere limite aferido por chave, e não por
usuário. Registro como medição; a leitura contratual disso é do parecer (quesito VI).

**Correção que isto impõe ao `PLANO_REDE_SOCIAL.md` §2**, que afirma "**1 única chamada HTTP real**
foi bem-sucedida (TJSP, 2026-07-21, HTTP 200, contagem agregada)": essa contagem vale para o ledger
`data/research/codex2_datajud_observations.jsonl`, e **não** para o repositório inteiro. Só a rodada
de 2026-08-07 fez 88 chamadas, e deixou o 429 gravado como prova.

### 3.3 O que a medição demonstra — e o que ela não demonstra

Demonstra, sem interpretação:

- que a API foi **consumida em escala** (88 requisições, 22 tribunais) em 2026-08-07, ou seja,
  **antes** do parecer que `FONTES_DIARIAS.md:81` condiciona ao uso agregado;
- que, pela literalidade da cláusula 1.2, esse consumo já é **aceitação tácita** do Termo — a
  cláusula afirma isso de si mesma, e transcrevê-la não é opinar;
- que o dado coletado é **agregado e sem dado pessoal**: contagens por assunto, classe e grau, sem
  número de processo, sem parte, sem advogado, sem texto;
- que houve **cruzamento com o acervo editorial**: cada assunto do ranking carrega
  `paginas_no_acervo` (ex.: "Dívida Ativa (Execução Fiscal)" 20.163.683 processos e 468 páginas;
  "Indenização por Dano Moral" 12.895.909 e 182), derivado dos títulos de `content/pages.json`;
- que o artefato **não alcança o caminho de publicação**: busca por `ranking_nacional` e
  `judicial_demand` em todo o código Go, Python e JavaScript do repositório devolve **zero
  leitores** — nenhum programa lê esses arquivos hoje; eles são artefato de pesquisa em disco.

Não demonstra — e o parecer é que decide — se essa coleta e esse cruzamento cabem em "fins legais,
não comerciais e autorizados" (3.3) e se o ranking é "informação derivada" cuja "exploração
comercial" a 3.8 veda.

### 3.4 Achado 7 — a identidade de saída daquelas duas ferramentas não é a canônica

`tools/generate-datajud-corpus:95` e `tools/measure-judicial-demand:78` enviam
`User-Agent: wikijuridica-demanda/1.0 (+wikijuridica.com.br)`, escrito à mão. O contrato manda sair
por `internal/wikijuridicabot`. Como são scripts Python, `TestNenhumPontoDeSaidaSaiDisfarcado` (que
varre Go) não os enxerga. **Não é disfarce de navegador nem de bot de terceiro** — é identidade
própria, porém fora do caminho canônico e sem a URL `/bot/`. **A medição dos 283.415.422 foi feita
sob esse UA.** Registro como achado para o chefe; não corrigi, porque isso alargaria o commit em
curso e está fora do escopo deste dossiê.

---

## 4. O estado do código

### 4.1 `internal/datajudfila` existe

Sim: `internal/datajudfila/` com `cliente.go`, `fila.go`, `limitador.go`, `latencia.go`,
`atraso.go` e três arquivos de teste. O comando é `cmd/datajud-fila` (invólucro
`tools/datajud-fila`).

### 4.2 A consulta que o projeto faz hoje pelo Go

Uma só, em `internal/datajudfila/cliente.go`, método `Consulta`:

- endpoint `POST https://api-publica.datajud.cnj.jus.br/api_publica_{alias}/_search`;
- corpo `{"size": 1, "query": {"match": {"numeroProcesso": <número CNJ normalizado>}}}` — **um
  processo por vez**, com o alias do tribunal derivado do próprio número CNJ;
- cabeçalho `Authorization: APIKey <chave pública>`; sem chave, falha explícita
  (`ErroSemChave`), nunca requisição sem autorização;
- identidade de saída por `wikijuridicabot.Aplica(requisicao, wikijuridicabot.PropositoColetaOficial)`
  — aqui o caminho canônico **é** respeitado;
- ordem limitador → disjuntor → rede, com `LimiteDeRequisicoesPorMinuto = 120` **nomeando a cláusula
  3.13** no comentário do código, e sem bandeira de linha de comando para afrouxá-lo;
- filtro estrutural por `nivelSigilo` (`Resposta.Sigiloso()` quando > 0);
- `ServeParaPrazo` sempre responde **não**, com o lag junto (42 dias medidos em 2026-09-04).

**Quem semeia a fila:** `cmd/datajud-fila --semear-do-djen` enfileira apenas processos em que
advogados da plataforma **já foram intimados** pelo DJEN — "não há varredura especulativa do CNJ: o
que se consulta é o que já tem dono aqui dentro" (comentário do comando). **Quem consome:**
`cmd/social` (`cobertura.go`), que lê a série de atraso e a exibe na tela do produto.

### 4.3 Sob qual cláusula essa consulta cai

Duas cláusulas são citadas **no próprio código** e estão respeitadas por construção: a **3.13**
(limitador de 120 req/min) e, pelo desenho metadata-only mais o filtro de `nivelSigilo`, a família
**4.x** da LGPD. A trava `datajudImportAllowed`
(`internal/codex2policyenforcement/policy.go:4429`) garante estruturalmente que **nenhum pacote do
caminho de publicação compila contra `internal/datajud*`** — `render`, `seo`, `sitemap`,
`publicrelease`, `pagefactory`, `feed`, `cmd/build` e `cmd/publish-v2-direct` ficam de fora, e
`TestCaminhoDePublicacaoNaoImportaDatajud` prova que continua assim. Os consumidores autorizados são
`internal/datajud*`, `internal/codex2datajud*`, `cmd/social/` e `cmd/*datajud*`.

**O que está aberto, e é do parecer:** a trava impede a **publicação**; ela não responde pela
**3.3** e pela **3.8** quanto ao produto. O comentário do próprio código diz que "o termo de uso do
CNJ restringe uso comercial e redistribuição" — e o dado do DataJud, hoje, chega a `cmd/social`, que
serve advogados que a tabela de monetização do `PLANO_REDE_SOCIAL.md` prevê como **assinantes de
SaaS** ("Assinatura SaaS do advogado — Permitido"). *Entregar a um assinante pagante informação
derivada da API é "explorar comercialmente" para efeito da 3.8?* É a pergunta mais afiada do
dossiê, e não é a pergunta sobre a qual a §3.1 do `FONTES_DIARIAS.md` foi escrita — aquela era
sobre o agregado estatístico.

### 4.4 O que exatamente a 3.8 restringe — leitura literal, sem conclusão

A 3.8 nomeia **quatro verbos** aplicados a dois objetos. Objetos: (i) **a API** e (ii) **qualquer
informação derivada dela**. Verbos: **modificar**, **distribuir**, **vender**, **explorar
comercialmente**. Não há na cláusula ressalva, exceção, prazo, nem menção a autorização. O que o
parecer tem de fixar, para cada verbo:

- **modificar** — recai sobre a API (a interface) ou também sobre a informação? Agregar contagens é
  "modificar" a informação derivada?
- **distribuir** — exibir a um assinante autenticado é distribuir? E publicar em página aberta?
- **vender** — há venda quando o preço é da assinatura da ferramenta, e não do dado?
- **explorar comercialmente** — é o verbo mais amplo e o único que o repositório vem citando; é ele
  que precisa de fronteira escrita.

---

## 5. Esqueleto do parecer — títulos e as perguntas que cada um tem de fechar

> Somente perguntas. Nenhuma resposta é sugerida aqui, e a ordem não insinua conclusão.
> O parecer, quando existir, mora em `docs/data-sources/PARECER_DATAJUD_3_3_3_8.md`.

### I. Objeto, fonte e vigência
- Qual documento é a fonte, em que versão, com qual hash e em que data ele foi conferido?
- O que se faz do fato de que a 3.22 permite alteração sem aviso prévio — o parecer se dá por
  datado, ou fixa um procedimento de reconferência?
- A v1.1 citada no `PLANO_REDE_SOCIAL.md` existiu? Se sim, onde está arquivada, e o texto de 3.8
  mudou entre as versões?

### II. Quem é "o usuário" e quando a aceitação se deu
- Pessoa física inscrita, escritório, portal ou assinante: quem aderiu tacitamente pela 1.2?
- A adesão se deu na primeira requisição de 2026-07-21, na rodada de 88 requisições de 2026-08-07, ou
  a cada consulta?
- Se o usuário for o assinante do produto, quem responde pelas obrigações — ele ou o portal que
  intermedeia?

### III. Cláusula 3.3 — "fins legais, não comerciais e autorizados"
- Os três qualificadores são cumulativos? Qual o efeito de cada um isoladamente?
- O que é "fim autorizado" num termo que não define autorização fora da 3.13?
- Um portal com CTA de contratação torna comercial **todo** uso que faça da API, ou o teste é sobre
  o uso concreto?
- Uso interno, que decide prioridade editorial e nunca aparece ao público, é "fim comercial"?

### IV. Cláusula 3.8 — os quatro verbos e os dois objetos
- Fronteira de cada verbo (item 4.4 acima), um a um.
- "Informação derivada" alcança contagem agregada que não permite reidentificar processo algum?
- A vedação é absoluta ou comporta autorização? Se comporta, com que fundamento, já que o texto não
  a prevê?

### V. Os dois usos concretos, avaliados em separado
- **Uso A — agregado estatístico** (`generate-datajud-corpus`, 283.415.422 processos, cruzado com
  `paginas_no_acervo`): cabe em 3.3 e 3.8? A resposta muda se o número for citado numa página
  pública? Muda se for só prioridade editorial interna?
- **Uso B — consulta por processo** (`internal/datajudfila.Consulta`, semeada pelo DJEN, servida por
  `cmd/social` a advogado assinante): cabe em 3.3 e 3.8? A resposta muda conforme o produto seja
  gratuito ou pago? Muda se o consulente for o próprio advogado do processo?
- Há um terceiro uso previsto no roadmap que o parecer deva alcançar desde já?

### VI. As obrigações vizinhas
- **3.9** — o que dispara o dever de ciência ao CNJ, e por qual canal ele se cumpre?
- **3.13** — o limitador por construção basta como cumprimento, ou há registro a manter?
- **4.2 / 4.6 / 3.11** — o desenho metadata-only e o filtro por `nivelSigilo` bastam? O cruzamento
  com o acervo é alcançado pela 4.2?
- **1.1** — o que a página incorporada por referência acrescenta, e como se prova o que ela dizia na
  data do uso?

### VII. Natureza e medida do risco
- O risco é contratual, disciplinar, ambos ou nenhum?
- Que consequência a 3.4 e a 3.14 autorizam (revogação de acesso sem aviso), e qual o impacto disso
  num produto que dependa da API?
- Com foro em Brasília/DF (5.1), qual o custo prático de uma controvérsia?
- Há precedente conhecido de o CNJ acionar usuário da API pública? *(Se não houver pesquisa feita,
  o parecer deve dizer "não pesquisado" — nunca supor.)*

### VIII. A petição ao CNJ — se cabe, e como
- Dado que a 3.8 não prevê autorização escrita (Achado 1), o que exatamente se pede: autorização
  não prevista, consulta interpretativa, ou alteração do termo?
- A quem se endereça, por qual canal, e o pedido precisa descrever os usos A e B em separado?
- O pedido, enquanto pendente, autoriza continuar, obriga a suspender, ou é indiferente?

### IX. Decisão e efeitos no repositório
- Veredito para a linha F10 da tabela de `FONTES_DIARIAS.md` (fechado, condicionado ou liberado) e redação exata a
  substituir a §3.1.
- O que fazer com `data/research/datajud/` — mantém, mantém com aviso de proveniência, ou fica
  restrito?
- A trava `datajudImportAllowed` permanece como está, aperta ou afrouxa?
- Que correções o parecer manda fazer nos textos internos: a citação de 3.8 no
  `PLANO_REDE_SOCIAL.md` (Achado 1), a paráfrase de 3.3 em `FONTES_DIARIAS.md` (Achado 2), a
  referência à v1.1 (Achado 3), a contagem de "1 única chamada HTTP" (§3.2 deste dossiê) e o
  User-Agent das duas ferramentas Python (Achado 7)?

---

## 6. O que ficou sem apurar

- **Texto da versão 1.1 do Termo.** Não localizei nenhuma cópia publicada no domínio do CNJ; as
  URLs prováveis devolveram 404 e o repositório não guarda cópia. Sem isso, a citação de 3.8 feita
  no `PLANO_REDE_SOCIAL.md` fica **sem fonte oficial**.
- **Procedimento de autorização do CNJ.** Nem o Termo, nem a wiki, nem
  `cnj.jus.br/sistemas/datajud/api-publica/` descrevem canal, formulário ou endereço para pedir
  autorização de uso — a única menção a autorização escrita é a da 3.13. **Sem fonte oficial** sobre
  como se pede.
- **Precedente de fiscalização.** Não pesquisei se o CNJ já revogou acesso ou acionou usuário da API
  pública por 3.3/3.8. Fica como quesito VII do esqueleto.
- **Portaria CNJ 160/2020.** Citada pela página institucional como o critério dos dados; não a
  baixei nem a conferi neste dossiê.
- **Enquadramento das cláusulas.** Deliberadamente não apurado: é o ato de advogado que esta entrega
  reserva ao titular da OAB/RJ 227191.
