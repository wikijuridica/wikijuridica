# Publicidade e nome de pessoa em fonte oficial

**Ordem do dono (advogado responsável, OAB/RJ 227191), 2026-08-29, na
literalidade:** *"Nome de pessoas públicas, não pode ter PII, eles são
públicos"*; *"Todos os processos publicos, podem constar o nome toda da pessoa.
O jus brasil faz isso e o ordenamento juridico garante isso. É principio
consticional"*; *"Podem constar casos"*.

Este documento existe para que **nenhum agente trave** por dúvida sobre isso, e
para que **nenhum agente erre para o outro lado**. Ele é a fonte da política que
`internal/pii`, `internal/publicidadenome` e os coletores implementam.

**Como este documento foi produzido:** seis frentes de pesquisa jurídica
independentes levantaram **104 citações**, e cada uma passou por um verificador
adversarial instruído a *derrubá-la* — conferindo número, redação literal,
vigência e se a glosa correspondia ao que o dispositivo diz. Das 35 citações
submetidas ao ataque: **25 confirmadas, 10 corrigidas, nenhuma refutada**. As
correções foram todas de *glosa* (leitura ampliada demais), nunca de
identificação. Onde a verificação alcançou a fonte oficial primária, isso está
dito com a URL; o texto literal foi conferido contra o Planalto, o portal do STF
e `atos.cnj.jus.br`.

---

<!-- BLOCO-CANONICO-REGRAS-DO-DONO: inicio — replicado palavra por palavra; internal/contract/misc/regras_do_dono_test.go reprova cópia ausente ou divergente -->

## Regras do dono — bloco canônico (2026-09-15)

Sete vereditos adotados, um por linha, em vigor desde 2026-09-15. O argumento, o caso medido e
o prejuízo de cada um ficam em `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` §P0, nos blocos
*"Texto do item N"*, e em `docs/PRECEDENTES_DAS_ORDENS.md`; aqui fica só a ordem. Este bloco é
replicado palavra por palavra em `CLAUDE.md`, `AGENTS.md`, `GOAL.md`, `CHECKPOINT.md`,
`docs/CONTRATO_DADO_REAL.md`, `docs/MEDICAO_DE_AUDIENCIA.md`, `docs/CRAWLERS_E_BOTS.md`,
`docs/CONTENT_QUALITY.md`, `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` e
`docs/DATA_SOURCES.md` — cópia divergente ou ausente reprova
`./tools/go-modern test -count=1 ./internal/contract/misc/`. Nenhuma linha daqui carrega número
de estado: o contrato diz onde medir, e quanto é se mede na hora.

**Regra 8 — nenhuma decisão volta para o dono (2026-09-15).** Decida e execute a decisão técnica, inclusive a ambígua, pela rota mais conservadora que ainda entrega e com a suposição escrita no commit; é vedado devolver decisão ao dono, desenhar revisão humana como etapa de esteira de conteúdo ou travar frente à espera de aprovação.

**Regra 9 — dado público vai até o fim da cadeia, e o DataJud está destravado (2026-09-15).** DataJud, API Pública do CNJ, DJEN, LexML, `normas.leg.br`, Planalto, diários oficiais e portais da transparência entram em página publicada com número, classe, órgão, relator, andamento e nome das partes, retirado o identificador (CPF, RG); a linha que fica é `nivelSigilo > 0`, ECA, Maria da Penha, adoção e o art. 5º, II da LGPD, e quem propuser trava, gate, allowlist ou regime de "só sinal interno" cita a norma e o dispositivo — sem dispositivo citado, a rota segue aberta.

**Regra 13 — a ética da OAB tem três regimes, e o deste portal é o do conteúdo informativo (2026-09-15, precisada em 2026-09-16).** Regime A, publicidade profissional — anúncio, oferta, perfil, captação —, é o que CED arts. 39, 40, 44, 45 e 46 e Provimento 205/2021 arts. 3º, 5º e 6º disciplinam, e esses gates ficam como estão; regime B, conteúdo informativo, é permitido com deveres de forma — CED art. 41 (não induzir a litigar), art. 42, I (não responder consulta de caso concreto em canal público), art. 42, IV e art. 43 (sem sensacionalismo), Provimento art. 4º e Anexo Único — e é o regime de página, verbete, comentário de acórdão e dataset deste portal; regime C, a exatidão técnica da informação jurídica, está fora da disciplina, então erro de conteúdo se trata como defeito de qualidade: conserta-se o produtor, mede-se antes e depois, e a página publica e refina. O canal de contato tem autorização expressa no Provimento art. 4º, §3º, que equipara ao e-mail os aplicativos de mensagens instantâneas; jurisprudência pública de terceiro fica, e resultado obtido pelo próprio autor em causa que patrocina sai, mesmo anonimizado (Provimento art. 4º, §2º). Quem invocar risco disciplinar contra conteúdo informativo cita o dispositivo, e o texto literal conferido em fonte primária está em `docs/goal/JURIDICO_BASE.md` §1.1; sem dispositivo citado, a rota segue aberta.

**Regra 15 — tráfego, alcance e retorno de bot medem-se na borda (2026-09-15).** Com `s-maxage=604800` na Cloudflare o `HIT` não toca o Go, então `data/ops/access/*.jsonl` é piso e só tem autoridade sobre o que existe apenas na origem (rota dinâmica, gêmea Markdown, `/api/v1`, MCP, descritores); volume se lê por `tools/cloudflare_auth.py` — `cf.zona_id("wikijuridica.com.br")` e `cf.graphql(...)` sobre `httpRequestsAdaptiveGroups` com dimensão `userAgent`, fatiando a janela em um dia por chamada no plano Free (`JANELA_MAXIMA_DIAS_FREE = 1`) —, toda afirmação de volume declara a camada medida, e série cumulativa como `edge_bot_agents_daily` se lê por último-por-dia, sem somar linhas.

**Regra 16 — não estreitar o projeto com número curto (2026-09-15).** Antes de escrever que uma frente é pequena, marginal, não escala ou não vale a pena, meça na fonte com autoridade sobre aquela grandeza; instrumento que declara a própria limitação é ordem de trocar de instrumento, e volume baixo confirmado entra com a camada declarada e com a hipótese do que o aumentaria, não como veredito de encerramento.

**Regra 18 — é proibido limitar este projeto (2026-09-15).** A plataforma cresce, é indexada e é citada, e o papel da engenharia é acelerar: todo teto nomeia a causa física externa e medida — `Crawl-Delay` publicado pelo operador remoto, tok/s do modelo, cota de requisições da API —, toda recusa de frente vem com a medição que a sustenta e com a hipótese do que a reverteria, e margem de prudência própria não é teto, é atraso.

**Regra 20 — bug anterior não trava trabalho, e não se contorna (2026-09-15).** Defeito encontrado no caminho se conserta no caminho, com agentes, na mesma sessão: "já estava quebrado antes" não é licença para parar, contorno vira a próxima peça quebrada, e medição que não caiu na rodada é passo de runbook — item que chegue ao fim da execução sem medição é falha de execução.

<!-- BLOCO-CANONICO-REGRAS-DO-DONO: fim -->

## O alcance da ética da OAB, e o alcance do dado público (2026-09-16)

Duas ordens do dono se somam a este documento, sem retirar nada dele.

**Regra 13 — a disciplina da OAB tem três regimes, e este portal está no segundo.** A redação
literal, com URL, bytes e SHA-256 de cada dispositivo, está em `docs/goal/JURIDICO_BASE.md` §1.1.

- **Regime A — publicidade profissional:** anúncio, oferta de serviço, perfil, captação. CED
  arts. 39, 40, 44, 45 e 46; Provimento 205/2021 arts. 3º, 5º e 6º. Os gates que hoje reprovam
  promessa de resultado, preço, gratuidade como chamariz, comparação e autoengrandecimento
  ficam como estão, e a inscrição na OAB nas peças de rede social continua obrigatória (CED
  art. 44, §1º).
- **Regime B — conteúdo informativo, permitido com deveres de forma:** página, verbete,
  comentário de acórdão e dataset. CED art. 41 (não induzir a litigar), art. 42, I (não
  responder consulta sobre caso concreto em canal público), art. 42, IV e art. 43 (sobriedade,
  sem sensacionalismo); Provimento art. 4º e Anexo Único. **É o regime deste portal**, e o
  Provimento art. 2º, II nomeia o marketing de conteúdos jurídicos como estratégia lícita — o
  portal é figura nomeada pela norma, não tolerada por omissão. O art. 39 do CED, aliás, é o que
  **exige** que a publicidade tenha *"caráter meramente informativo"*: invocá-lo contra conteúdo
  informativo é invertê-lo.
- **Regime C — exatidão técnica da informação jurídica:** fora da disciplina. Nenhum dispositivo
  a alcança; EAOAB art. 34, XIV e CED art. 2º p.ú., II e art. 6º, que são os mais próximos, são
  processuais e dolosos. Erro de conteúdo é defeito de qualidade e se conserta como tal.

Ignorar o regime B erra para um lado — publica-se o que o CED art. 42, I veda; tratar o regime B
como se fosse o A erra para o outro — trava-se página informativa invocando norma de anúncio. Os
dois erros já aconteceram neste repositório. Quem alegar risco disciplinar cita o dispositivo;
sem dispositivo citado, a rota segue aberta.

**Dois pontos que ficam com o dispositivo na mão:** o canal de contato — site, rede social e
aplicativo de mensagens instantâneas — é autorizado expressamente pelo Provimento art. 4º, §3º,
que os equipara ao e-mail do CED art. 40, V, em caráter informativo; e a jurisprudência pública
de terceiro **fica**, enquanto o resultado obtido pelo próprio autor em causa que patrocina
**sai**, mesmo anonimizado (Provimento art. 4º, §2º, e Anexo Único, que veda *"resultados
concretos obtidos"* sem exigir identificação). É o que sustenta as páginas de `/jurisprudencia/`.

**Regra 9 — o dado público vai até o fim da cadeia.** A seção 1 deste documento já sustenta que
nome de parte e de agente público em ato oficial publicado pode constar. Fica explícito o que
faltava: isso alcança o **artefato público** — página, gêmea Markdown, dataset e API —, não para
em uso interno. DataJud, API Pública do CNJ, DJEN, LexML, `normas.leg.br`, Planalto, diários
oficiais e portais da transparência entram no caminho de publicação, com proveniência (URL, data
e hash). O que sai continua sendo o **identificador** (CPF, RG), e as exceções taxativas da
seção 2 — segredo de justiça (`nivelSigilo > 0`, marcado na própria API), ECA, Maria da Penha,
adoção e dado sensível do art. 5º, II da LGPD — permanecem integrais, com a checagem de cinco
passos da seção 4.

## 1. A regra: publicidade

No Brasil a publicidade é a **regra** e o sigilo é a **exceção**, e a exceção
depende de lei.

| Dispositivo | Texto literal | O que resolve |
|---|---|---|
| **CF/88, art. 5º, LX** | *"a lei só poderá restringir a publicidade dos atos processuais quando a defesa da intimidade ou o interesse social o exigirem"* | Restringir publicidade exige **lei** e uma de duas causas taxativas. Vontade do interessado não basta. |
| **CF/88, art. 5º, XXXIII** | *"todos têm direito a receber dos órgãos públicos informações de seu interesse particular, ou de interesse coletivo ou geral…"* | Direito subjetivo de acesso, com o sigilo como exceção que **quem nega** deve fundamentar. ⚠ A ressalva escrita no inciso (segurança da sociedade e do Estado) **não é o único limite**: o art. 37, §3º, II conjuga expressamente o acesso com o art. 5º, X; somam-se o art. 5º, LXXIX (EC 115/2022) e a LAI art. 31. |
| **CF/88, art. 37, caput** (EC 19/1998) | *"A administração pública direta e indireta… obedecerá aos princípios de legalidade, impessoalidade, moralidade, **publicidade** e eficiência"* | Erige a publicidade a princípio vinculante, e daí a publicação ser, em regra, condição de eficácia e instrumento de controle do ato. ⚠ **O caput NÃO disciplina quem deve ser nominalmente identificado** — quem sustenta a identificação do agente é o Tema 483, não este dispositivo. Não o cite para isso. |
| **CF/88, art. 93, IX** (EC 45/2004) | *"todos os julgamentos dos órgãos do Poder Judiciário serão públicos, e fundamentadas todas as decisões, sob pena de nulidade…"* | Julgamentos públicos e decisões fundamentadas. ⚠ A restrição que ele autoriza é à **PRESENÇA** em determinados atos — não ao conteúdo da decisão —, e depende de três condições cumulativas: previsão em lei, intimidade do interessado e ausência de prejuízo ao interesse público à informação. |

Fontes: `planalto.gov.br/ccivil_03/constituicao/constituicao.htm` (conferido
literalmente em 2026-08-29, HTTP 200, 1.839.482 bytes).

**As três ressalvas marcadas com ⚠ acima vieram do verificador adversarial, e
cada uma derrubou uma glosa ampliada da primeira redação deste documento.** Ficam
registradas porque são exatamente o erro que um agente com pressa repetiria:
citar o dispositivo certo para a conclusão errada. O dispositivo confere; a
leitura é que precisava ser estreitada.

### O fundamento positivo mais direto — e é infralegal

**Resolução CNJ 121/2010, art. 2º** (`atos.cnj.jus.br/atos/detalhar/92`):

> *"Art. 2.º Os dados básicos do processo de livre acesso são: I – número, classe
> e assuntos do processo; **II – nome das partes e de seus advogados**; III –
> movimentação processual; IV – inteiro teor das decisões, sentenças, votos e
> acórdãos."*

E o art. 1º assegura essa consulta *"a toda e qualquer pessoa, independentemente
de prévio cadastramento ou de demonstração de interesse"*.

**Nome das partes é dado de livre acesso, por norma expressa.** O CPF **não
figura em nenhum inciso** — ele aparece no art. 4º, III apenas como *critério de
localização* do processo, e essa distinção entre **chave de busca** e **conteúdo
divulgado** é o que separa o que fica do que sai.

### Republicar por terceiro é lícito no plano autoral

**Lei 9.610/1998, art. 8º, IV**: *"Não são objeto de proteção como direitos
autorais… os textos de tratados ou convenções, leis, decretos, regulamentos,
**decisões judiciais e demais atos oficiais**"*.

O limite da republicação é de **direitos da personalidade e proteção de dados**,
nunca de direito de autor.

### Jurisprudência vinculante

**STF, ARE 652.777/SP — Tema 483** (Pleno, rel. Min. Teori Zavascki, j.
23/04/2015, trânsito 14/08/2015):

> *"É legítima a publicação, inclusive em sítio eletrônico mantido pela
> Administração Pública, dos nomes dos seus servidores e do valor dos
> correspondentes vencimentos e vantagens pecuniárias."*

⚠ **Duas precisões que a verificação impôs, e que um agente reproduziria
errado:**
1. A classe é **ARE** (Recurso Extraordinário com Agravo), **não RE**. "RE
   652.777" é imprecisão corrente — não reproduza.
2. A tese legitima a publicação **pela Administração Pública**. Ela **não
   autoriza por si só** a republicação por terceiro privado, que precisa de base
   própria (LGPD art. 7º, IX — legítimo interesse) e do filtro do art. 7º, §3º.

**STF, RE 1.010.606/RJ — Tema 786** (Pleno, rel. Min. Dias Toffoli, j.
11/02/2021, trânsito 28/05/2021):

> *"É incompatível com a Constituição a ideia de um direito ao esquecimento,
> assim entendido como o poder de obstar, em razão da passagem do tempo, a
> divulgação de fatos ou dados verídicos e licitamente obtidos e publicados em
> meios de comunicação social analógicos ou digitais. Eventuais excessos ou
> abusos… devem ser analisados caso a caso…"*

Não existe direito ao esquecimento no Brasil. O titular **não pode exigir** a
retirada do nome só porque o ato é antigo — o controle migrou para o **abuso**,
aferido caso a caso.

### A LGPD não se opõe — e é onde mora a condição

| Dispositivo | O que estabelece |
|---|---|
| **art. 5º, I** | Nome é dado pessoal. Ser dado pessoal **não** o torna secreto. |
| **art. 5º, II** | Rol **fechado** de dado sensível. **Nome puro não está nele**; "estar em processo judicial" também não. |
| **art. 7º, §3º** | *"O tratamento de dados pessoais cujo acesso é público deve considerar a finalidade, a boa-fé e o interesse público que justificaram sua disponibilização."* — **autorização condicionada, não vedação.** |
| **art. 7º, IX** (c/c art. 10) | Legítimo interesse: é **esta** a base que efetivamente carrega a republicação por portal privado. |
| **art. 6º, I e III** | Finalidade e necessidade — é aqui que a restrição morde de verdade, não no art. 5º. |
| **art. 11, caput e I** | É **este** o dispositivo que restringe dado sensível; o art. 5º, II é apenas definitório. |

**CF/88, art. 5º, LXXIX** (EC 115/2022) elevou a proteção de dados a direito
fundamental autônomo. Não revoga a publicidade do dado público — obriga
ponderação.

---

## 2. A exceção: onde o nome NÃO pode sair

A exceção é **estreita e taxativa**. Fora dela, publicidade.

> ### ★ COMO O CÓDIGO APLICA ISTO (ordem do dono, 2026-08-29)
>
> A primeira implementação recusava o texto diante de **qualquer** marcador desta
> tabela e mandava o material para *"revisão humana"*. As duas coisas estavam
> erradas, e o dono corrigiu com estas palavras:
>
> > *"Você não pode deixar para revisão humana, é impossível. A revisão é feita
> > por Claude Code e agentes. E se é público, pode publicar. Para de travar o
> > projeto. Eu tô falando que os processos no Brasil são públicos e até o
> > JusBrasil faz isso, e JusBrasil não é governo."*
>
> **Não existe revisão humana neste projeto.** Mandar material para uma fila que
> ninguém processa não é cautela: é descartar trabalho pago e travar o canal com
> aparência de rigor. Quem revisa é o Claude Code e os agentes.
>
> **E a publicidade é a regra.** Só **quatro** hipóteses desta tabela impedem a
> publicação por si, porque nelas a lei veda a DIVULGAÇÃO, com dispositivo
> expresso: **segredo de justiça** (CPC art. 189), **ato infracional** (ECA art.
> 143 e 247), **vítima de crime sexual** (CP art. 234-B) e **adoção** (ECA art.
> 47 §4º e 48). Em `internal/publicidadenome` elas são as marcadas com
> `vedacaoLegal`, e `VedacaoLegalExpressa` é a régua única — um segundo detector
> com critério próprio seria a divergência silenciosa que este repositório já
> pagou para aprender.
>
> As demais linhas continuam sendo **detectadas**, porque informam o gerador e
> quem audita sobre o que aquele texto contém. Mas **não barram**: ato
> administrativo de pessoal publicado no diário oficial é público por força do
> art. 37 da Constituição, e está no diário exatamente por isso. Menção a saúde,
> a família ou a violência doméstica numa política pública municipal não
> transforma ato público em sigiloso.
>
> **Efeito medido no canal diário, no dia da mudança:** de **19 registros
> barrados para 2**, e de 14 para **16 páginas** com trecho citado. Os 2 que
> continuam fora são os de vedação expressa.
>
> O que sai do texto continua sendo o **identificador** — CPF, RG —, e disso
> cuida `internal/pii`. Esta régua decide sobre a hipótese legal de sigilo, não
> sobre o dado pessoal.

| Caso | Dispositivo | Regra prática de detecção |
|---|---|---|
| **Segredo de justiça** | **CPC art. 189**: *"Os atos processuais são públicos, todavia tramitam em segredo de justiça os processos: I – em que o exija o interesse público ou social; II – que versem sobre casamento, separação de corpos, divórcio, separação, união estável, filiação, alimentos e guarda de crianças e adolescentes; III – em que constem dados protegidos pelo direito constitucional à intimidade; IV – que versem sobre arbitragem…"* | Rol **taxativo**. Teste empírico decisivo: consultar o número do processo no portal do tribunal — se as partes **não** aparecem na consulta pública, o material está sob segredo e o nome não se reproduz, ainda que tenha vazado por outra via. |
| **Adolescente autor de ato infracional** | **ECA art. 143, parágrafo único**: *"Qualquer notícia a respeito do fato não poderá identificar a criança ou adolescente, vedando-se fotografia, referência a nome, apelido, filiação, parentesco, residência e, **inclusive, iniciais do nome e sobrenome**."* | ⚠ **Anonimizar por iniciais ("J.S., 16 anos") JÁ VIOLA.** A vedação alcança filiação, parentesco e residência — não basta tirar o nome. **ECA art. 247** tipifica como infração administrativa com multa. |
| **Criança/adolescente vítima ou testemunha** | **ECA art. 17** e **Lei 13.431/2017, art. 12, §§ 5º e 6º** | O art. 143 cobre o **autor**; a vítima é protegida por estes. Depoimento especial corre em segredo de justiça. |
| **Vítima de violência doméstica** | **Lei 11.340/2006, art. 17-A**: *"O nome da ofendida ficará sob sigilo… Parágrafo único. O sigilo… **não abrange o nome do autor do fato**, tampouco os demais dados do processo."* | Marcadores: "medida protetiva de urgência", "violência doméstica", "Lei Maria da Penha", "afastamento do lar". **Suprimir a vítima, podendo manter o autor.** **Art. 9º, §8º** estende aos dependentes matriculados em escola. |
| **Vítima de crime sexual** | **CP art. 234-B**: processos em segredo de justiça | ⚠ **Atribuição:** o art. 234-B foi inserido pela **Lei 12.015/2009**, não pela 13.718/2018. O dispositivo criado pela Lei 13.718/2018 nessa matéria é o **art. 218-C**. Não troque. |
| **Adoção** | **ECA art. 47, §4º** e **art. 48** | Registro original cancelado; só o próprio adotado, após os 18 anos, rompe o sigilo. |
| **Dado sensível** | **LGPD art. 11, caput e I** (não o art. 5º, II) | Saúde, origem racial, convicção, biometria, orientação sexual. |
| **Sigilo bancário e fiscal** | **LC 105/2001, art. 1º**; **CTN art. 198** | — |
| **Vítima em processo criminal** | **Res. CNJ 121/2010, art. 4º, §2º** | Nome de vítima **nunca** é dado básico em processo criminal. |

### Duas restrições que quase ninguém conhece, e que valem para este portal

**1. Res. CNJ 121/2010, art. 5º** — *"A disponibilização de consultas às bases de
decisões judiciais impedirá, quando possível, a busca pelo nome das partes."*

Publicidade **não autoriza indexação nominal de acervo decisório**. O nome é
público na consulta processual, mas **não como chave de pesquisa** em base de
jurisprudência. Isto alcança diretamente a busca interna do portal: publicar
jurisprudência é lícito; oferecer *busca por nome de parte* sobre ela, não.

**2. Res. CNJ 121/2010, art. 4º, §1º** — no **criminal**, após trânsito em
julgado absolutório, extinção da punibilidade ou cumprimento da pena, a consulta
pública fica restrita ao **número do processo**. Na **Justiça do Trabalho**,
restrita a número, nome do advogado e OAB — ali **não** se pesquisa por nome da
parte.

---

## 3. O que isto significa no código

| Decisão | Onde vive | Por quê |
|---|---|---|
| Nome de agente público e de parte em ato oficial **permanece** | `internal/pii.Mascarar` não suprime `atoDePessoal`; registra como achado `nome_agente_publico` | CF 37 caput, CF 93 IX, Res. CNJ 121/2010 art. 2º, II, Tema 483 |
| **CPF e RG saem** | `internal/pii` continua mascarando | Não são dado básico de livre acesso (Res. CNJ 121/2010 art. 2º); publicar CPF distribui credencial |
| **CNPJ permanece** | removido do `Mascarar` e do `Contem` | LGPD art. 1º protege pessoa **natural**; CNPJ identifica pessoa jurídica, com consulta pública na Receita; LAI art. 8º, §1º, IV manda publicar contrato |
| O predicado do gate **só reprova por identificador** | `internal/pii.Contem` | Reprovar por nome barrava o próprio ato oficial |
| Gate cobra os **dois lados** | `internal/publicidadenome` (`publicidade-nome-fonte-oficial`) | Suprimir demais destrói o ato; suprimir de menos vaza credencial |
| Metadado de editor **nunca** entra | `internal/planaltochannel.elementoSemTextoLegal` pula `<xml>` e `o:`/`w:`/`v:`/`m:`/`x:` | O nome do servidor que redigiu o DOCX não é o ato |

**Por que `internal/pii` NÃO é usado no coletor de normas federais:** ele
mascararia as **assinaturas** do ato — "LUIZ INÁCIO LULA DA SILVA" fecha a Medida
Provisória —, que são o documento oficial público. O recorte correto ali é por
**estrutura** (metadado do editor), não por detecção de nome.

---

## 4. Antes de publicar material com nome: a checagem

1. **O material cai numa exceção da §2?** Marcadores literais: "segredo de
   justiça", "ato infracional", "medida protetiva", "violência doméstica",
   "adoção", "acolhimento institucional", "guarda", "alimentos", "curatela", CID
   ou diagnóstico ao lado de nome. **Se cair, o nome não vai** — e no caso do
   ECA art. 143 nem as iniciais.
2. **É processo? Consulte o número no portal do tribunal.** Se a consulta pública
   não exibe as partes, está sob segredo (Res. CNJ 121/2010, art. 1º, parágrafo
   único).
3. **Há identificador?** CPF, RG, NIS/PIS/PASEP, CNS, título de eleitor, número
   de benefício, CNH, endereço residencial completo → **sai**, mesmo que o nome
   fique.
4. **Vai virar chave de busca?** Base de decisões judiciais não pode ser
   pesquisável por nome de parte (art. 5º).
5. **A finalidade se sustenta?** LGPD art. 7º, §3º e art. 6º, I e III: o
   tratamento de dado público exige finalidade, boa-fé e interesse público. Nome
   em página que não o usa para nada **não passa no teste da necessidade** — é
   ali que a restrição morde, não no art. 5º, II.

---

## 5. O que este documento NÃO decide

Não substitui leitura do caso concreto quando houver dúvida sobre exceção. E não
alcança **dado sensível** (LGPD art. 11) nem **processo sob segredo**: nesses,
ou a fonte não se coleta, ou o caso vai a revisão. Detector por expressão regular
não resolve exceção — quem resolve é a leitura.

**E não substitui conferir a citação na fonte.** Das 35 citações submetidas ao
verificador adversarial, **13 voltaram com correção** — nenhuma por dispositivo
inexistente, todas por *glosa* ou por *atribuição de redação*. Três exemplos do
que quase entrou aqui errado: atribuir ao art. 37, caput, a identificação
nominal que na verdade vem do Tema 483; apresentar a ressalva de segurança
nacional como único limite do art. 5º, XXXIII; e ler o art. 93, IX como
restrição de conteúdo quando ele restringe **presença**. Some-se a troca de
`RE` por `ARE` no Tema 483 e a atribuição do CP art. 234-B à Lei 13.718/2018
quando é da Lei 12.015/2009. **Citação legal mal atribuída é P1 permanente
neste repositório** — nenhuma medição automática a detecta.

**As 13 correções, e o que foi feito com cada uma** (para ninguém ter de
adivinhar):

| Correção do verificador | Tratamento aqui |
|---|---|
| CF art. 5º, XXXIII — a ressalva de segurança não é o único limite | **aplicada** na tabela §1 (⚠) |
| CF art. 37, caput — não disciplina identificação nominal | **aplicada** na tabela §1 (⚠); a identificação passou a ser atribuída ao Tema 483 |
| CF art. 93, IX — restringe PRESENÇA, não conteúdo | **aplicada** na tabela §1 (⚠) |
| Tema 483 é **ARE**, não RE | **aplicada** na §1 |
| Tema 483 legitima publicação *pela Administração*; terceiro precisa de base própria | **aplicada** na §1 |
| CP art. 234-B é da Lei 12.015/2009, não da 13.718/2018 | **aplicada** na §2 |
| CNJ 121/2010 art. 4º — atribuição de redação (Res. 143/2011) | **aplicada**: a §2 cita o §1º com a redação correta |
| CF art. 93, X — trata de decisão administrativa de tribunal | **N/A**: não é usado neste documento |
| CPC art. 189, II — leitura a estreitar | **aplicada**: a §2 transcreve o rol literal, sem glosa ampliada |
| LGPD art. 7º, I — defeito só na glosa | **N/A**: o documento usa o §3º e o IX, não o inciso I |
| LGPD art. 7º, §6º e §7º — "confere, não alterar" | **confirmada**, sem mudança |
| CNJ 121/2010 (identificação, URL, transcrição, vigência) — "conferem" | **confirmada**, sem mudança |
| STJ REsp 1.660.168 — desindexação, não apagamento | **N/A**: fora do escopo desta política; fica no registro da pesquisa |

---

## Precedente registrado

A política anterior era o inverso, e o custo estava medido no acervo: **88
ocorrências de `[nome removido]`** nos textos coletados, em trechos como
*"Exonerar a Sra. [nome removido] de Enfermeira, lotada na Secretaria de
Saúde"*. Não se entende uma exoneração sem saber quem foi exonerado. O canal
diário parecia morto porque o próprio anonimizador o matava — e `pii.Contem`
ainda **reprovava** o texto por conter nome, fazendo o coletor descartar o que
acabara de baixar e anonimizar. Ver `docs/goal/BUGLOG.md`, BUG-165 e BUG-172.
