# Desenho de integração da política da rede social

> **SUPERADO em 2026-09-05.** Este documento propõe designar encarregado
> (`dpo_name`, `dpo_is_controller: true`), escrito **antes** da leitura do texto
> oficial das Resoluções CD/ANPD nº 2/2022 e nº 18/2024. Essa leitura, registrada
> em `docs/politica/ENQUADRAMENTO_PEQUENO_PORTE.md` (seção 5) e refletida na
> política pública `docs/politica/REDESOCIAL_POLITICA_DE_PRIVACIDADE_E_USO.md`
> (seção 1), concluiu que a **não designação** é o caminho adotado — um entre
> dois caminhos igualmente lícitos (designação com mitigação do conflito de
> interesse, art. 21, parágrafo único, II; ou a dispensa do art. 11 da Res.
> 2/2022, aqui escolhida por descrever a realidade de responsável único sem
> estrutura interna). O art. 19, § 2º não é um terceiro caminho: é o padrão de
> verificação em concreto que se aplicaria caso a designação ocorresse. As
> chaves `dpo_name` e
> `dpo_is_controller` propostas abaixo **não devem ser criadas** em
> `content/site.json`: a política pública já usa `editorial_identity` para o
> canal do art. 11, § 1º, sem precisar de um bloco `data_protection` distinto.
> Mantido aqui por preservação de trabalho, não como orientação vigente.

Documento de engenharia. O texto público está em
`docs/politica/REDESOCIAL_POLITICA_DE_PRIVACIDADE_E_USO.md` e é o único que sai
para o visitante. Aqui ficam as chaves de configuração, a forma exata que fecha
o gate `redesocial-completude`, e a lista de divergências entre o que a política
afirma e o que o código faz hoje.

Nada neste diretório foi aplicado: `content/site.json`, `internal/` e
`content/redesocial_entregas.json` não foram tocados.

---

## 1. Chaves novas em `content/site.json`

O arquivo tem hoje 594 bytes e duas chaves de topo úteis (`base_url` e
`editorial_identity`). A proposta acrescenta **um bloco novo de topo**,
`data_protection`, em vez de inchar `editorial_identity` — o autor editorial e o
encarregado pela LGPD são papéis distintos, ainda que hoje sejam a mesma pessoa,
e misturá-los faria uma mudança de encarregado reescrever a autoria das 10.141
páginas do acervo.

```json
"data_protection": {
  "controller_kind": "pessoa_natural",
  "controller_name": "Rafael Toledo",
  "controller_legal_name": "Rafael Toledo da Silva Duarte",
  "dpo_name": "Rafael Toledo",
  "dpo_is_controller": true,
  "dpo_email": "rafaeltoledoadvogado@outlook.com",
  "dpo_designation_source": "project_owner_declared_config",
  "dpo_designated_at": "2026-09-05",
  "support_channel_email": "rafaeltoledoadvogado@outlook.com",
  "support_channel_open_to_non_users": true,
  "brazil_representation": "direct_natural_person_domiciled_in_brazil",
  "policy_path": "/redesocial/politica/",
  "policy_effective_from": "2026-09-05"
}
```

Notas de desenho, uma por chave que não é óbvia:

- **`controller_kind` / `dpo_is_controller`** existem para que o renderizador
  possa emitir a frase certa sem que ninguém a escreva à mão. Com
  `dpo_is_controller: true`, o texto diz "o próprio controlador exerce a
  função"; com `false`, exigiria `dpo_name` distinto. Um booleano evita a classe
  de erro em que o nome do encarregado muda e a frase continua dizendo que ele é
  o controlador.
- **`support_channel_open_to_non_users`** não é decoração: o item 8 da tese do
  Tema 987 fala em canais "a usuários e a não usuários". A chave existe para que
  a página não possa afirmar isso sem que a configuração o declare.
- **`brazil_representation`** é um valor de conjunto fechado, não texto livre.
  Os dois valores que fazem sentido hoje são
  `direct_natural_person_domiciled_in_brazil` (o caso atual) e
  `legal_entity_representative` (se um dia houver pessoa jurídica). Texto livre
  aqui viraria a porta por onde entra a afirmação de uma estrutura que não
  existe.
- **`dpo_email` e `support_channel_email`** são chaves separadas mesmo tendo o
  mesmo valor hoje. Elas atendem a normas diferentes (LGPD art. 41, § 1º e tese
  do Tema 987, item 8) e podem divergir amanhã sem que uma quebre a outra.
- **`policy_path`** aponta a rota que servirá o texto público. **Ela ainda não
  existe** — ver a seção 4. Enquanto não existir, nenhuma página deve emitir
  link para ela: link publicado antes do destino é 404 entregue pela nossa mão.

**Não usar outro endereço do dono em lugar nenhum.** O e-mail profissional
declarado é `rafaeltoledoadvogado@outlook.com`, e é o único que pode aparecer em
configuração, página ou documento.

## 2. O que fecha o gate `redesocial-completude`

A entrega `F0-transparencia` em `content/redesocial_entregas.json` declara quatro
provas em `simbolos_go`, todas contra `internal/moderacao`:

| prova declarada | como `declaraSimbolo` a reconhece |
|---|---|
| `/redesocial/transparencia/` | literal em fonte Go, fora de comentário |
| `Encarregado` | **identificador** — `func`, `type` ou `const`/`var` |
| `canal de atendimento` | literal em fonte Go, fora de comentário |
| `representante legal no Brasil` | literal em fonte Go, fora de comentário |

`internal/redesocialcompletude/completude.go:1280` (`declaraSimbolo`) faz duas
passadas por arquivo `.go` que não seja `_test.go`: primeiro procura um
identificador declarado com aquele nome exato na AST; se não achar, cai no
`contemForaDeComentario`, que casa a string crua desde que ela não esteja em
comentário. Três das quatro provas têm espaço no nome e por isso só podem ser
satisfeitas pela segunda passada — ou seja, **por literal de string em código**,
não por comentário e não por teste.

A forma que satisfaz as quatro de uma vez, sem inventar dado, é um bloco de
rótulos públicos em `internal/moderacao` alimentado pelas chaves da seção 1 —
os rótulos são o texto que a página exibe, e o valor vem da configuração:

```go
// Rotulos da prestacao de contas publica exigida pela tese do Tema 987.
const (
	RotuloDoEncarregado = "encarregado pelo tratamento de dados pessoais"
	RotuloDoCanal       = "canal de atendimento"
	RotuloDaRepresentacao = "representante legal no Brasil"
	CaminhoDaTransparencia = "/redesocial/transparencia/"
)

// Encarregado e a designacao do art. 41 da Lei 13.709/2018, lida da
// configuracao -- nunca escrita aqui.
type Encarregado struct {
	Nome            string
	Email           string
	EhOControlador  bool
	DesignadoEm     string
}
```

`Encarregado` como `type` satisfaz a primeira passada; os três literais
satisfazem a segunda. O valor continua vindo de `content/site.json`, que é onde
a designação do controlador mora.

**Alternativa a considerar antes de escrever o código.** A prova
`"representante legal no Brasil"` codifica, no nome, uma figura que o item 10 da
tese descreve como "necessariamente pessoa jurídica com sede no país" — e que
não existe nesta operação. Declarar o rótulo é honesto **porque a página explica
que a representação é direta**; se preferires que o dado descreva o mundo em vez
do requisito, o caminho é corrigir a entrega em
`content/redesocial_entregas.json` para
`"identificacao de quem responde no Brasil"`. As duas rotas são defensáveis; a
que não é defensável é declarar o rótulo e deixar a página calada sobre a
diferença.

## 3. Aviso de dado sensível no formulário de publicação

O art. 11, I da LGPD exige consentimento **específico e destacado** para dado
sensível. Hoje não há, no caminho de publicação de dúvida, nenhum aviso a esse
respeito, e `internal/lgpd/finalidades.go` não declara `FundamentoSensivel` para
`conteudo_publico`. Enquanto isso não existir, a política não afirma
conformidade — ela orienta o usuário a escrever o mínimo.

Texto proposto para o formulário, ao lado do botão de publicar, curto o
bastante para ser lido:

> **O que você escrever aqui fica público.** Descreva o problema jurídico sem
> nome de outras pessoas, sem número de documento e sem detalhe de saúde que
> você não queira ver lido por qualquer pessoa. Você pode retirar o texto do ar
> depois, mas o que já foi lido não volta atrás.

Se o objetivo for materializar o art. 11, I, o aviso precisa virar caixa de
confirmação específica para a publicação — e aí `conteudo_publico` ganha
`FundamentoSensivel: art. 11, I`, com o registro do consentimento.

## 4. Divergências entre a política e o código, medidas em 2026-09-05

Cada linha é um achado com o arquivo onde vive. A política pública foi escrita
para **não** afirmar nada que dependa da correção destes pontos.

1. **As três rotas do art. 18 existem e não são servidas.**
   `cmd/social/titular.go:141` define `registraRotasDoTitular`, e nenhum arquivo
   de `cmd/social` a chama — `rotas.go` registra conta, feed, thread,
   transparência, indexação e consulta, mas não o titular. Consequência:
   `/redesocial/conta/meus-dados/`, `.../corrigir/` e `.../eliminar/` respondem
   404. Por isso a política indica o e-mail do encarregado como via de exercício
   e **não publica esses caminhos**.

2. **`lgpd.RegistraAcesso` não tem chamador no caminho servido.**
   `internal/lgpd/registrosacesso.go:167` está escrita e testada; o único
   chamador fora de teste é o próprio pacote. A tabela `registros_acesso` do
   `lgpd.db` não recebe linha, e `acessosDoTitular`
   (`cmd/social/titular.go:528`) leria uma tabela vazia. O registro de acesso
   real é o do nginx, transcrito por `tools/generate-origin-access-ledger` — foi
   ele que a seção 4 da política descreveu.

3. **A base legal de `seguranca` em `finalidades.go` não se sustenta para este
   controlador.** `internal/lgpd/finalidades.go:213` declara
   `art. 7º, II da Lei 13.709/2018 e art. 15 da Lei 12.965/2014`, e a
   `NotaDeEliminacao` fala em "guarda obrigatória". O art. 15, *caput*, alcança
   o "provedor de aplicações de internet **constituído na forma de pessoa
   jurídica** e que exerça essa atividade de forma organizada, profissionalmente
   e com fins econômicos" — conferido no Planalto, verbatim na seção 5. Uma
   pessoa natural não está no *caput*; ela pode ser alcançada pelo § 1º, por
   decisão judicial. Sugestão: base legal `art. 7º, IX` (legítimo interesse), com
   nota dizendo que o prazo de seis meses é adotado como padrão próprio, pelo
   parâmetro do art. 15 e para viabilizar resposta a requisição judicial. O
   mesmo reparo vale para o cabeçalho de `tools/generate-origin-access-ledger`,
   que escreve "o art. 15 OBRIGA o provedor".

4. **`Substrato.Nota` desatualizada em quatro finalidades.** `conta` diz
   "pendente: internal/contas nasce em F1" e `conteudo_publico` diz "pendente:
   internal/socialconteudo nasce em F2" — os dois pacotes existem e funcionam.
   `moderacao` diz "pendente: internal/moderacao nasce em F0, em outra frente", e
   ele está no ar servindo a página de transparência. Comentário que mente é bug.

5. **Finalidades sem substrato, que a política deliberadamente não descreve:**
   `intake_de_caso`, `processual`, `verificacao_oab` e `mensageria`. A política
   afirma, em vez disso, que a rede não recebe anexo, não pede documento e não
   tem mensagem privada — o que é verdade hoje e deixa de ser no dia em que o
   código nascer, quando o texto tem de ser reescrito **antes** do lançamento.

6. **`conteudo_publico` sem `FundamentoSensivel`.** Ver a seção 3.

7. **Divergência de data na página de transparência.** `cmd/social/pagina.go:262`
   afirma que o STF julgou os dois recursos "em 26 de junho de 2025". A série
   coletada (`data/research/daily/stf-informativo/2026-08-20.jsonl`) traz apenas
   o registro do **ajuste da tese**, julgado em 2026-06-17, Informativo nº 1.222.
   A tese fixa efeitos a partir da publicação da ata, "em 5/8/25". A política
   ancorou nas duas datas que estão conferidas; a página de transparência
   sustenta uma terceira que não foi encontrada na fonte coletada — conferir
   antes de a repetir em texto novo.

8. **Cloudflare não estava declarada em lugar nenhum como operadora.** O túnel vê
   o IP de todo visitante (`real_ip_header CF-Connecting-IP` no nginx desfaz o
   endereço da borda), o que a coloca no art. 5º, VII da LGPD. A política a
   nomeia; nenhuma configuração a declarava.

## 5. Conferência das fontes citadas

Coleta própria de 2026-09-05, com o agente do portal
(`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; conferencia-de-fonte-oficial)`).

| fonte | URL | HTTP | sha256 do corpo recebido |
|---|---|---|---|
| Lei 13.709/2018 (LGPD) | `https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm` | 200, 310.252 B | `b58abaa700b486306600a8534b043a5369933cbd3cf042dd7e6a159912b38f9c` |
| Lei 12.965/2014 (Marco Civil) | `https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm` | 200, 119.976 B | `9c3ea9503d764748a0fdd6b931a20856192292f51a9437e353d53c5ae23e9763` |
| CED — Resolução CFOAB 02/2015 | `https://www.oab.org.br/leisnormas/legislacao/resolucoes/02-2015` | 200, 107.253 B | `672887efbfaf9666784aefc22583f52d6b0b5832d0efe803e824f61aaaad02a6` |
| Provimento CFOAB 205/2021 | `https://www.oab.org.br/leisnormas/legislacao/provimentos/205-2021` | 200, 73.589 B | `c80f9ef427f33eefa6966a28c14807268d688e240560a6f53c57c8046db03d4c` |
| Tese do Tema 987 | Informativo do STF nº 1.222, RE 1.037.396/SP, Plenário, Rel. Min. Dias Toffoli, j. 2026-06-17 — série já coletada em `data/research/daily/stf-informativo/2026-08-20.jsonl` | — | `sha256_fonte` da linha: `9f41eea4aae46be9516f4d3a700c7d530313c082be8043cbdc33c553de27a987` |

O portal do STF (`portal.stf.jus.br`) não serve a cadeia intermediária do
certificado e, montada a cadeia à mão a partir do *Authority Information
Access*, respondeu **403** ao agente do portal. A tese usada é, portanto, a do
Informativo do STF já coletado, cuja licença permite reprodução citada a fonte.
Conferir de novo no portal do tribunal quando o acesso voltar.

### Dispositivos citados, e o que a conferência mostrou

- **LGPD art. 5º, VI** — controlador é "pessoa natural ou jurídica". Confere; é o
  dispositivo que sustenta pessoa física como controladora.
- **LGPD art. 5º, VIII** — encarregado como canal de comunicação entre
  controlador, titulares e ANPD. A redação em vigor é a da **Lei nº 15.352, de
  2026**, que passou a escrever "Agência Nacional de Proteção de Dados (ANPD)"
  onde antes se lia "Autoridade". A substância não mudou; o texto público usa a
  sigla.
- **LGPD art. 5º, II** — dado sensível inclui "dado referente à saúde". Confere.
- **LGPD art. 7º, II, V e IX** — conferidos, um a um.
- **LGPD art. 7º, § 4º** — dispensa de consentimento para dado tornado
  manifestamente público pelo titular. **Não foi usado no texto**: ele está no
  art. 7º e não alcança dado sensível, cujo regime é o do art. 11.
- **LGPD art. 11, I** — consentimento específico e destacado. Confere, e é o
  inciso que a plataforma **ainda não materializa** (seção 3).
- **LGPD art. 12** — dado anonimizado fora do escopo da lei. Confere.
- **LGPD art. 15, I e art. 16, I** — término do tratamento e conservação para
  obrigação legal. Conferem.
- **LGPD art. 18 e §§ 1º, 2º, 3º, 5º e 8º** — conferidos. O § 8º autoriza
  peticionar também perante os órgãos de defesa do consumidor.
- **LGPD art. 19, I e II** — imediato em formato simplificado, ou declaração
  completa em até 15 dias. Confere.
- **LGPD art. 41 e § 1º** — indicação do encarregado e divulgação pública da
  identidade e do contato, "preferencialmente no sítio eletrônico". Confere.
- **MCI art. 5º, VIII** — registro de acesso a aplicações é o conjunto de
  informações sobre data e hora de uso "a partir de um determinado endereço IP".
  Confere.
- **MCI art. 10, § 1º e art. 22** — disponibilização só por ordem judicial, com
  requisitos do pedido. Conferem.
- **MCI art. 11 e § 2º** — territorialidade. **Não há representante legal neste
  artigo**: o § 2º trata de pessoa jurídica sediada no exterior. A premissa de
  que o requisito de representante nasceria daqui está errada e não foi usada.
- **MCI art. 15, *caput* e §§ 1º a 3º** — a guarda de seis meses vincula o
  provedor "constituído na forma de pessoa jurídica" com fins econômicos.
  Conferido verbatim; ver a divergência 3.
- **MCI art. 19 e art. 21** — regime de responsabilidade e nudez não consentida.
  Conferem, e o art. 21 exige notificação com identificação específica do
  material, sob pena de nulidade.
- **Tema 987, itens 7, 8, 9 e 10** — autorregulação com notificações, devido
  processo e relatórios; canais a usuários **e a não usuários**; publicação e
  revisão periódica das regras; sede e representante no país. **Não são a
  "tese 3"**: o item 3 trata de responsabilidade solidária por conteúdo de
  terceiro. A numeração usada no texto público é a da tese.
- **CED art. 39** — publicidade de caráter meramente informativo, discrição e
  sobriedade. Confere.
- **CED art. 40, VI** — veda mala direta e panfleto com intuito de captação.
  Confere, e é o dispositivo certo para a promessa de não usar o e-mail
  cadastrado em prospecção.
- **CED art. 42, I** — veda responder com habitualidade a consulta jurídica nos
  meios de comunicação social. Confere.
- **CED art. 44 e § 1º** — nome e número de inscrição na publicidade; o § 1º
  admite expressamente e-mail, site e horário de atendimento.
- **Provimento 205/2021, art. 3º, *caput* e I** — caráter meramente informativo,
  discrição e sobriedade; vedada referência a honorários, gratuidade ou desconto
  como forma de captação. Confere.
- **Provimento 205/2021, art. 4º** — autoriza o marketing de conteúdo jurídico.
  Confere, e é o contraponto que impede ler o art. 42, I como proibição de
  produzir conteúdo.

Dispositivo que **não** foi citado por falta de conferência: a Resolução
CD/ANPD nº 2/2022, sobre agentes de tratamento de pequeno porte. A página do
gov.br devolveu 404 na coleta de hoje e o texto não foi lido em fonte oficial —
sem fonte oficial, não entra. Ela é irrelevante para o resultado, de todo modo:
o encarregado foi designado, e a eventual dispensa não seria usada.
