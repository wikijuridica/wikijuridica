# JURIDICO_BASE.md — fontes primárias para quem produz conteúdo

**Anexo obrigatório de todo briefing de agente que escreve, audita, classifica,
publica ou bloqueia conteúdo do `wikijuridica.com.br`.**

Este documento existe para impedir dois defeitos medidos, que custaram meses:

1. **Regra inexistente.** Sessões inventaram restrições que a norma brasileira
   não impõe — "risco sob a OAB" para travar página informativa, "o termo de uso
   do CNJ proíbe uso comercial" apoiado numa cláusula que não diz isso — e
   usaram a invenção como pré-requisito de escala.
2. **Letra fria fora de contexto.** Ler um dispositivo isolado e ignorar o que a
   própria norma autoriza no artigo seguinte. Ordem do dono, 2026-09-15, na
   literalidade: *"estou a meses tentando destravar e o Claude Code leva a Lei na
   literalidade, sendo que não é bem assim"*.

**Como foi produzido:** cada dispositivo citado aqui foi baixado da fonte oficial
em **2026-09-16**, convertido a texto e conferido na redação literal. URL, tamanho
em bytes e SHA-256 do que foi baixado estão na **§7 — tabela de prova**. Onde a
fonte oficial recusou a requisição, está escrito qual e com que código HTTP —
nenhuma afirmação normativa deste documento vem de memória ou de portal privado.

**Autor responsável pelo conteúdo publicado:** Rafael Toledo, OAB/RJ 227191. É
ele quem assina, dirige e responde. A ferramenta executa.

**Como ler.** O mínimo vinculante são três blocos curtos: **DECIDA ASSIM**, **§5 —
o que NÃO é vedação** e **§6 — quem alegar restrição cita o dispositivo**. As demais
seções são consultadas **por gatilho**: §1 ao escrever ou auditar texto público e
CTA; §2 ao tocar dado de processo; §3 ao trazer texto oficial para o corpo; §4 ao
tratar dado pessoal; §7 quando alguém pedir a prova de uma citação.

---

## DECIDA ASSIM

1. **Página informativa publica.** Conteúdo jurídico informativo é expressamente permitido (Prov. CFOAB 205/2021, arts. 1º, 2º-II e 4º). Não peça permissão.
2. **Nunca bloqueie por "risco sob a OAB" sem citar dispositivo.** Sem provimento, artigo do CED ou julgado nomeado, a rota segue aberta (§6).
3. **Erro de conteúdo é defeito de QUALIDADE, não infração disciplinar.** Conserta no produtor, mede antes e depois, publica e refina (§5 do CLAUDE.md; fundamento em §1.4).
4. **CTA neutro fica.** "Tire suas dúvidas pelo WhatsApp" é canal informativo, autorizado pelo art. 4º, §3º do Prov. 205/2021. Não remova.
5. **Imperativo de contratar ou litigar sai.** "Contrate agora", "entre com a ação já" cruza o art. 3º, §1º do Provimento e o art. 41 do CED. Reescreva (§1.2).
6. **Promessa de resultado sai sempre, em qualquer publicidade** (Prov. art. 6º, parágrafo único). Inclui "garantimos", "êxito certo", "você vai receber".
7. **Preço, desconto e gratuidade como chamariz saem** (Prov. art. 3º, I). Explicar *gratuidade de justiça* ou *BPC/LOAS* como instituto jurídico **não** é isso.
8. **Jurisprudência pública de terceiro e caso hipotético FICAM; caso do próprio advogado com resultado, ainda que anonimizado, SAI** (Prov. art. 4º, §2º; art. 6º e p.ú.; Anexo Único).
9. **Não responda consulta de caso concreto em canal público, nem por automação indiscriminada** (CED art. 42, I; Anexo Único, "Aplicativos"). Informação geral e primeiras dúvidas: permitido (Anexo Único, "Chatbot").
10. **Texto informativo não induz a litigar** (CED art. 41). Descreva o direito; não empurre para a ação.
11. **Especialidade só com título certificado ou notória especialização** (Prov. art. 3º, III c/c EAOAB art. 3º-A, p.ú.).
12. **Duas menções à inscrição OAB por página** — byline e rodapé (CED art. 44; régua em `internal/render/author_credential_test.go`).
13. **Nome de parte em processo público PODE constar** (Res. CNJ 121/2010, art. 2º, II). O que sai é IDENTIFICADOR: CPF, RG.
14. **Segredo de justiça, ECA, Maria da Penha, adoção e dado sensível não saem** — lista taxativa em §2.3, cada uma com dispositivo.
15. **Família é tema-núcleo e é livre como INFORMAÇÃO; o DADO DE CASO desses processos está sob segredo** (CPC art. 189, II). Não confunda tema com autos.
16. **Lei, decisão judicial e ato oficial não têm proteção autoral** (Lei 9.610/98, art. 8º, IV); citação identificada é lícita (art. 46, III e VIII).
17. **Dado público em ato processual trata-se por legítimo interesse** (LGPD art. 7º, IX c/c §3º), nunca por consentimento. Sensível: art. 11.
18. **Não fraude alcance nem impulsionamento** (Prov. art. 4º, §5º) — cloaking e métrica inflada são também questão ética, não só política do buscador.
19. **Regra interna do repositório não é lei.** §5.2 lista quais são: o dono pode mudá-las; a norma, não.
20. **Na dúvida entre travar e publicar, publique e refine.** Travar sem dispositivo é o defeito que este documento existe para impedir.

---

## 1. Publicidade da advocacia × conteúdo informativo

### 1.1 A tese correta, com a precisão que faltava

A formulação curta que circula neste repositório — *"a ética da OAB alcança
publicidade, não conteúdo informativo"* — **está certa na conclusão e curta demais
na premissa**. A redação literal mostra três regimes, não dois:

| Regime | Alcance | Dispositivos conferidos |
|---|---|---|
| **A. Publicidade profissional** | anúncio, oferta, perfil profissional, captação | CED arts. 39, 40, 44, 45, 46; Prov. 205/2021 arts. 3º, 5º, 6º |
| **B. Conteúdo informativo — permitido, com deveres de FORMA** | artigo, verbete, comentário, dataset, resposta pública | CED arts. 41, 42, 43; Prov. art. 4º; Anexo Único ("Criação de conteúdo…") |
| **C. Fora da disciplina** | exatidão técnica da informação jurídica em conteúdo informativo | nenhum dispositivo a alcança; os três que mais se aproximam são processuais e dolosos (§1.4) |

**O regime B é o deste portal, e ele é de permissão com forma, não de proibição.**
Quem ignora o regime B erra para um lado (publica o que o CED art. 42, I veda);
quem trata o regime B como se fosse A erra para o outro (trava página informativa
invocando norma de anúncio). Os dois erros já aconteceram aqui.

**Texto literal que sustenta cada linha** (fonte e hash na §7):

- **Prov. 205/2021, art. 1º**: *"É permitido o marketing jurídico, desde que
  exercido de forma compatível com os preceitos éticos e respeitadas as limitações
  impostas pelo Estatuto da Advocacia, Regulamento Geral, Código de Ética e
  Disciplina e por este Provimento."*
- **Prov., art. 2º, II** define *marketing de conteúdos jurídicos* como a estratégia
  *"que se utiliza da criação e da divulgação de conteúdos jurídicos… voltada para
  informar o público e para a consolidação profissional do(a) advogado(a)"*. Ou
  seja: **o portal é figura nomeada pela norma, não tolerada por omissão.**
- **Prov., art. 4º, caput**: *"No marketing de conteúdos jurídicos poderá ser
  utilizada a publicidade ativa ou passiva, desde que não esteja incutida a
  mercantilização, a captação de clientela ou o emprego excessivo de recursos
  financeiros…"*
- **CED art. 39**: *"A publicidade profissional do advogado tem caráter meramente
  informativo e deve primar pela discrição e sobriedade, não podendo configurar
  captação de clientela ou mercantilização da profissão."* — **o art. 39 EXIGE o
  caráter informativo.** Invocá-lo contra conteúdo informativo é invertê-lo.
- **Anexo Único, "Criação de conteúdo, palestras, artigos"**: *"Deve ser orientada
  pelo caráter técnico informativo, sem divulgação de resultados concretos obtidos,
  clientes, valores ou gratuidade."* — é a regra editorial do portal, escrita pela
  própria OAB.

**Sobre "publicidade passiva":** o portal encontrado por busca orgânica se enquadra
no art. 2º, VII (*"divulgação capaz de atingir somente público certo que tenha
buscado informações acerca do anunciante ou dos temas anunciados"*), e o Anexo
Único confirma a lógica ao permitir palavra-chave *"quando responsivo a uma busca
iniciada pelo potencial cliente"*. **Mas isso é reforço, não a viga:** o art. 4º
permite conteúdo jurídico em publicidade **ativa ou passiva**. Não construa
permissão sobre a classificação — ela não é o que decide.

**Onde a distinção ativa/passiva importa de fato:** o art. 6º, *caput* veda **na
publicidade ativa** informação sobre dimensões, qualidades ou estrutura física do
escritório; o **parágrafo único** estende a **qualquer publicidade** a ostentação
de bens, a promessa de resultados e o uso de casos concretos para oferta.

### 1.1-A O dispositivo que protege as páginas de jurisprudência

As ~875 páginas de `/jurisprudencia/` comentam acórdãos públicos de terceiros.
O que a norma veda é outra coisa, e o texto é explícito — **Prov. 205/2021, art. 4º,
§2º**:

> *"Na divulgação de imagem, vídeo ou áudio contendo atuação profissional, inclusive
> em audiências e sustentações orais, em processos judiciais ou administrativos, não
> alcançados por segredo de justiça, serão respeitados o sigilo e a dignidade
> profissional e vedada a referência ou menção a decisões judiciais e resultados de
> qualquer natureza obtidos **em procedimentos que patrocina ou participa de alguma
> forma**, ressalvada a hipótese de manifestação espontânea em caso coberto pela
> mídia."*

**A vedação é sobre o resultado obtido pelo próprio advogado no processo que
patrocina.** Comentar decisão pública de terceiro — STF, STJ, TST, tribunal
estadual — **não é caso concreto para oferta** e não está vedado. O art. 5º, §3º
repete a régua para vídeos e lives; o Anexo Único ("Criação de conteúdo") a repete
para artigos: *"sem divulgação de resultados concretos obtidos, clientes, valores ou
gratuidade"*.

| Situação | Regime |
|---|---|
| comentar acórdão público de terceiro, com fonte | **fica** |
| exemplo hipotético, construído para ilustrar a tese | **fica** |
| resultado obtido pelo próprio autor em causa que patrocina | **sai** — art. 4º, §2º |
| o mesmo resultado próprio, anonimizado | **sai** — Anexo Único veda *"resultados concretos obtidos"*, sem exigir identificação |

### 1.2 Frase que cruza a linha → reescrita que a traz de volta

| Cruza | Dispositivo | Reescrita que fica |
|---|---|---|
| "Contrate agora e garanta seu benefício" | Prov. art. 3º, §1º (incitar diretamente à contratação) + art. 6º, p.ú. (promessa) | "Este texto explica os requisitos do benefício. Tire suas dúvidas pelo WhatsApp." |
| "Entre com a ação hoje e receba o que é seu" | CED art. 41 (induzir o leitor a litigar) | "A via judicial é cabível quando o pedido administrativo é negado; veja os prazos abaixo." |
| "Consulta gratuita para novos clientes" | Prov. art. 3º, I (gratuidade como captação) | *(remover; explicar gratuidade de justiça como instituto é outra coisa — permanece)* |
| "Honorários a partir de R$ 500, parcelados" | Prov. art. 3º, I (valor e forma de pagamento) | *(remover integralmente do conteúdo público)* |
| "O melhor escritório de direito previdenciário do Rio" | Prov. art. 3º, IV (autoengrandecimento e comparação) | "Conteúdo de direito previdenciário escrito por Rafael Toledo, OAB/RJ 227191." |
| "Conseguimos R$ 180 mil para o cliente J.S. em 2025" | Prov. art. 6º, p.ú. (caso concreto como oferta e resultado) | "O valor da indenização varia conforme os critérios do art. 944 do Código Civil." |
| "Não perca o prazo! Ligue já antes que prescreva" | CED arts. 39 e 43 (urgência/medo; sobriedade) | "O prazo prescricional é de X anos, contados de Y. Verifique sua situação." |
| "Especialista em direito digital" (sem título) | Prov. art. 3º, III c/c EAOAB art. 3º-A, p.ú. | "Atuação em direito digital." *(ou instruir o título certificado, se houver)* |
| "Respondo sua dúvida: no seu caso, entre com ação de X" | CED art. 42, I (consulta com habitualidade) + orientação a caso concreto em canal público | "Em casos com esse contorno, a jurisprudência do STJ costuma exigir A e B. Cada situação depende dos documentos." |

**A régua do que permanece é dupla e literal:** art. 2º, VIII define captação como
o mecanismo que *"de forma ativa… se destinam a angariar clientes pela indução à
contratação dos serviços ou estímulo do litígio"*; art. 3º, §1º exige publicidade
*"sem incitar **diretamente** ao litígio judicial, administrativo ou à contratação
de serviços"*. **Indução ativa e direta** é o que a norma nomeia. Um canal de
contato neutro, ao lado de texto que explica o direito, não é indução: é o que o
art. 4º, §3º autoriza expressamente.

### 1.3 O CTA de WhatsApp tem autorização expressa — e é recente

O **CED art. 40, V** veda *"o fornecimento de dados de contato, como endereço e
telefone, em colunas ou artigos literários, culturais, acadêmicos ou jurídicos…
bem assim… em veiculação de matérias pela internet, **sendo permitida a referência
a e-mail**"*.

Lido sozinho, esse inciso é a "letra fria" que travaria o botão de WhatsApp do
portal inteiro. **Ele não está sozinho.** O **Prov. 205/2021, art. 4º, §3º** diz:

> *"Para os fins do previsto no inciso V do art. 40 do Código de Ética e
> Disciplina, **equiparam-se ao e-mail, todos os dados de contato e meios de
> comunicação do escritório ou advogado(a), inclusive os endereços dos sites, das
> redes sociais e os aplicativos de mensagens instantâneas**, podendo também
> constar o logotipo, desde que em caráter informativo, respeitados os critérios de
> sobriedade e discrição."*

**Conclusão operacional:** site, redes sociais, WhatsApp e logotipo em conteúdo
jurídico são **permitidos por dispositivo expresso**, com duas condições —
**caráter informativo** e **sobriedade**. O CTA neutro do portal fica. Quem quiser
removê-lo tem de derrubar o art. 4º, §3º, não apenas citar o art. 40, V.

Reforço no mesmo sentido: **CED art. 44, §1º** admite na publicidade profissional
*"o endereço, e-mail, site, página eletrônica, QR code, logotipo"*, horário de
atendimento e idiomas; **CED art. 46, parágrafo único** admite internet como
veículo *"desde que estas não impliquem o oferecimento de serviços ou representem
forma de captação de clientela"*.

### 1.4 Precisão de citação legal: a resposta exata, não a resposta chapada

Pergunta que já travou escala aqui: *"citação legal mal atribuída é risco
disciplinar?"*

**Os únicos dispositivos de veracidade localizados são estes, e são de publicidade:**

- **Prov. 205/2021, art. 1º, §1º**: *"As informações veiculadas deverão ser
  objetivas e verdadeiras e são de exclusiva responsabilidade das pessoas físicas
  identificadas…"*
- **Prov., art. 1º, §2º**: quem veicula deve **comprovar a veracidade** quando
  solicitado pelos órgãos de fiscalização, *"sob pena de incidir na infração
  disciplinar prevista no art. 34, inciso XVI, do Estatuto"*.
- **Prov., art. 3º, II**: vedada *"divulgação de informações que possam induzir a
  erro ou causar dano a clientes, a outros(as) advogados(as) ou à sociedade"*.

E o **Estatuto (Lei 8.906/94), art. 34, XVI**, para o qual o §2º remete, é
literalmente: *"deixar de cumprir, no prazo estabelecido, determinação emanada do
órgão ou de autoridade da Ordem, em matéria da competência desta, depois de
regularmente notificado"*. **É dever procedimental de atender à fiscalização — não
é norma sobre exatidão de citação jurídica.**

**Portanto:** não há, no Provimento 205/2021 nem no CED, dispositivo que discipline
a **precisão técnica de citação legal em conteúdo informativo**. Atribuição
imprecisa é **defeito de qualidade** — conserta-se no produtor, mede-se antes e
depois, e a página **publica e refina** (§5 do CLAUDE.md).

*O que isso NÃO autoriza:* inventar decisão, ementa, artigo ou resultado. Isso é
proibido pelo §8 do CLAUDE.md e cai, sim, no art. 3º, II (induzir a erro) quando
publicado. A diferença entre **errar a atribuição de um artigo real** e **inventar
um dispositivo** é a diferença entre defeito e falsidade.

#### Dispositivos próximos que NÃO alcançam conteúdo informativo — e por quê

Um leitor adversarial encontra estes três. Estão aqui, com o texto literal e com a
razão de não servirem de trava, para que ninguém precise "descobri-los" depois:

- **Estatuto (Lei 8.906/94), art. 34, XIV** — *"deturpar o teor de dispositivo de
  lei, de citação doutrinária ou de julgado, bem como de depoimentos, documentos e
  alegações da parte contrária, **para confundir o adversário ou iludir o juiz da
  causa**"*. É **a** norma disciplinar sobre citação distorcida — e é de **atuação
  processual**: exige verbo doloso (*deturpar*), uma parte adversária e um juiz da
  causa. Erro de atribuição em verbete público não tem adversário, não tem juízo e
  não tem dolo de iludir. **Não se aplica**; e a existência dela reforça o ponto:
  quando o legislador quis punir citação distorcida, escreveu, e escreveu para o
  processo.
- **CED art. 2º, parágrafo único, II** — dever de *"atuar com destemor,
  independência, honestidade, decoro, **veracidade**, lealdade, dignidade e boa-fé"*.
  Cláusula geral de conduta. Sustenta corrigir o erro conhecido; não converte
  imprecisão técnica em infração nem autoriza bloqueio prévio de publicação.
- **CED art. 6º** — *"É defeso ao advogado expor os fatos em Juízo ou na via
  administrativa **falseando deliberadamente a verdade** e utilizando de má-fé."*
  Também processual, também doloso.

**Régua para o gate:** citação distorcida **de propósito** para enganar é matéria
disciplinar quando usada em processo; citação **imprecisa** em conteúdo informativo
é defeito de qualidade. Se um agente não consegue mostrar dolo e destinatário
processual, não há enquadramento — há correção a fazer.

*Registro de superação:* a linha do `CLAUDE.md` §5 que chama citação mal atribuída
de *"a única classe com risco real sob a OAB"* fica **superada nesta data** quanto
ao enquadramento disciplinar, pela ordem do dono de 2026-09-15 e por este
levantamento. O **defeito continua real e continua P1 de qualidade**; o rótulo
disciplinar cai. Não se apaga a linha: anota-se o motivo.

### 1.5 Automação, resposta pública e habitualidade — aqui existe limite real

Este portal serve IA e humanos e expõe `responder_pergunta` por MCP. A norma tem
três entradas diretas, e elas **não** se resumem a "pode tudo":

- **CED art. 42, I** — é vedado *"responder com habitualidade a consulta sobre
  matéria jurídica, nos meios de comunicação social"*. É o dispositivo que
  `internal/oabgate/consulta.go` já aplica, e ele fala de **consulta** (pergunta de
  caso concreto dirigida a quem responde), não de conteúdo geral.
- **Anexo Único, "Aplicativos para responder consultas jurídicas"** — *"Não é
  admitida a utilização de aplicativos de forma indiscriminada para responder
  automaticamente consultas jurídicas a não clientes por suprimir a imagem, o poder
  decisório e as responsabilidades do profissional, representando mercantilização
  dos serviços jurídicos."*
- **Anexo Único, "Chatbot"** — permitido *"para responder as primeiras dúvidas de um
  potencial cliente ou para encaminhar as primeiras informações"*, sem afastar a
  pessoalidade nem suprimir a responsabilidade do profissional.

**Fronteira operacional, para gerador e para gate:**

| Saída | Regime | Ação |
|---|---|---|
| verbete, página, dataset, gêmea Markdown, resposta sobre **a tese em geral** | permitido | publica |
| "primeiras dúvidas" e encaminhamento, com identificação do responsável | permitido | publica |
| **orientação a caso concreto**, em canal **público**, por automação | vedado | reprova (HARD) |
| responder consulta individual com **habitualidade** em rede social | vedado | reprova (HARD) |

Também literal e aplicável: **CED art. 42, IV** veda divulgar *"listas de clientes
e demandas"*; **CED art. 43** exige que manifestação pública vise *"objetivos
exclusivamente ilustrativos, educacionais e instrutivos"*, e seu parágrafo único
veda *"o debate de caráter sensacionalista"*.

### 1.6 Fraude de alcance é matéria ética, não só política de plataforma

**Prov. 205/2021, art. 4º, §5º**: *"É vedada a publicidade a que se refere o caput
mediante uso de meios ou ferramentas que influam de forma fraudulenta no seu
impulsionamento ou alcance."*

Cloaking, conteúdo diferente para bot e humano, inflar métrica com tráfego próprio
e comprar alcance artificial **violam esse parágrafo**, além das regras do
buscador. É mais um fundamento — agora normativo — para o anti-fraude do §6 do
CLAUDE.md e para o `X-Warming-Request` das sondas.

---

## 2. Dado processual público

O tratamento completo, com as 104 citações verificadas por refutação adversarial,
está em **`docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md`**. Esta seção é o resumo
vinculante mais o que aquele documento não traz.

### 2.1 A regra: publicidade

| Dispositivo | Redação conferida |
|---|---|
| **CF art. 5º, LX** | *"a lei só poderá restringir a publicidade dos atos processuais quando a defesa da intimidade ou o interesse social o exigirem"* |
| **CF art. 37, caput** | a administração pública *"obedecerá aos princípios de legalidade, impessoalidade, moralidade, publicidade e eficiência"* |
| **CF art. 93, IX** | *"todos os julgamentos dos órgãos do Poder Judiciário serão públicos…"* — a restrição que autoriza é à **presença** em determinados atos, não ao conteúdo da decisão |
| **CPC art. 189** | *"Os atos processuais são públicos, todavia tramitam em segredo de justiça os processos: I – …interesse público ou social; II – casamento, separação de corpos, divórcio, separação, união estável, filiação, alimentos e guarda…; III – dados protegidos pelo direito constitucional à intimidade; IV – arbitragem…"* |
| **Lei 12.527/2011, art. 3º, I** | *"observância da publicidade como preceito geral e do sigilo como exceção"* |
| **Res. CNJ 121/2010, art. 2º** | dados básicos de livre acesso: *"I – número, classe e assuntos; **II – nome das partes e de seus advogados**; III – movimentação processual; IV – inteiro teor das decisões, sentenças, votos e acórdãos"* |

**O fundamento direto do nome da parte é a Res. CNJ 121/2010, art. 2º, II** — norma
expressa, e o art. 1º assegura a consulta *"a toda e qualquer pessoa,
independentemente de prévio cadastramento ou de demonstração de interesse"*.

⚠ **Não use o Tema 483 do STF para isso.** A tese — *"É legítima a publicação,
inclusive em sítio eletrônico mantido pela Administração Pública, dos nomes dos
seus servidores e do valor dos correspondentes vencimentos e vantagens
pecuniárias"* (ARE 652.777, rel. Min. Teori Zavascki) — legitima a publicação **pela
Administração** e trata de **servidor e remuneração**. É âncora fraca para portal
privado e não fala de nome de parte. A âncora certa é a Res. CNJ 121/2010.

### 2.2 O que pode sair publicado e o que nunca sai

| Publica | Não publica |
|---|---|
| número, classe, assunto, órgão, relator | **CPF, RG** e demais identificadores |
| **nome das partes e dos advogados** | dado sensível do art. 5º, II da LGPD (§4) |
| movimentação processual | qualquer dado de processo em segredo (§2.3) |
| inteiro teor de decisão, sentença, voto e acórdão | nome de vítima em processo criminal (Res. CNJ 121/2010, art. 4º, §2º) |

**A distinção que separa o que fica do que sai:** o CPF aparece na Res. CNJ 121/2010
apenas no art. 4º, III, como **critério de localização** do processo — chave de
busca, não conteúdo divulgado.

**Duas restrições pouco conhecidas, e elas valem aqui:**

- **Res. CNJ 121/2010, art. 4º, §1º** — no criminal, após trânsito em julgado
  absolutório, extinção da punibilidade ou cumprimento da pena, a consulta pública
  fica restrita ao **número do processo**; na **Justiça do Trabalho**, restrita a
  número, nome do advogado e registro na OAB — ali **não** se pesquisa por nome da
  parte.
- **Res. CNJ 121/2010, art. 5º** — a disponibilização de consultas a bases de
  decisões *"impedirá, quando possível, a busca pelo nome das partes"*. Publicar
  jurisprudência é lícito; oferecer **busca por nome de parte** sobre ela, não.

### 2.3 As exceções taxativas

| Hipótese | Dispositivo conferido |
|---|---|
| **Segredo de justiça** | CPC art. 189, I a IV (rol taxativo). Na API do CNJ vem marcado: `nivelSigilo > 0` — o campo existe para ser respeitado |
| **Ato infracional** | ECA art. 143 e parágrafo único: vedada notícia que identifique, *"vedando-se fotografia, referência a nome, apelido, filiação, parentesco, residência e, inclusive, iniciais do nome e sobrenome"* — anonimizar por iniciais **já viola**; ECA art. 247 tipifica |
| **Violência doméstica** | Lei 11.340/2006, **art. 17-A** (incluído pela **Lei 14.857/2024**): *"O nome da ofendida ficará sob sigilo…"*; parágrafo único: *"O sigilo… não abrange o nome do autor do fato, tampouco os demais dados do processo"* — suprime-se a vítima, mantendo o autor |
| **Crime sexual** | CP art. 234-B (incluído pela Lei 12.015/2009): processos em segredo de justiça |
| **Adoção** | ECA art. 47, *caput* (mandado *"do qual não se fornecerá certidão"*), §2º (cancela o registro original) e §4º, red. Lei 12.010/2009 (*"Nenhuma observação sobre a origem do ato poderá constar nas certidões do registro"*); art. 48: só o próprio adotado, após os 18 anos, tem acesso irrestrito |
| **Dado sensível** | LGPD art. 11, *caput* (o art. 5º, II é apenas definitório) |

**Atualização que o documento-irmão ainda não registra:** o **CP art. 234-B ganhou
§§ 1º a 3º pela Lei 15.035/2024** — a partir da condenação em primeira instância
pelos crimes ali listados, o sistema de consulta processual torna **público o nome
completo do réu e o seu CPF**, restabelecendo-se o sigilo em caso de absolvição
recursal (§2º). Ou seja: a lei **abriu** onde a intuição diria fechar. Isso não
muda a regra interna deste repositório de remover CPF (§5.2) — mas desmente a ideia
de que sigilo de vítima implica sigilo do réu.

### 2.4 Família: onde este portal mais erra

Divórcio, alimentos e guarda são o núcleo editorial do portal **e** estão no rol do
segredo de justiça (CPC art. 189, II). As duas coisas convivem:

- **Página informativa sobre divórcio, alimentos, guarda, união estável:** livre.
  O tema não é sigiloso; os **autos** é que são.
- **Dado de caso concreto desses processos** — partes, andamento, inteiro teor:
  **não sai**, ainda que tenha aparecido em outra fonte.
- **Teste empírico decisivo:** consulte o número no portal do tribunal. Se as partes
  não aparecem na consulta pública, o material está sob segredo.

---

## 3. Direito autoral sobre texto oficial

**Lei 9.610/1998, art. 8º, IV** — *"Não são objeto de proteção como direitos autorais
de que trata esta Lei: … IV - os textos de tratados ou convenções, leis, decretos,
regulamentos, **decisões judiciais e demais atos oficiais**"*.

**Consequência:** lei, decreto, súmula, decisão judicial e ato oficial **podem virar
corpo de página**, sem licença e sem autorização. O limite da republicação é de
direitos da personalidade e proteção de dados (§2 e §4) — **nunca** de direito de
autor.

**Lei 9.610/1998, art. 46, III** — não ofende direito autoral *"a citação em livros,
jornais, revistas ou qualquer outro meio de comunicação, de passagens de qualquer
obra, para fins de estudo, crítica ou polêmica, **na medida justificada para o fim a
atingir, indicando-se o nome do autor e a origem da obra**"*.

**Lei 9.610/1998, art. 46, VIII** — livre *"a reprodução, em quaisquer obras, de
pequenos trechos de obras preexistentes… sempre que a reprodução em si não seja o
objetivo principal da obra nova e que não prejudique a exploração normal da obra
reproduzida"*. **É o fundamento legal da "regra das duas camadas"** do §8 do
CLAUDE.md: texto citado e comentário autoral em blocos distintos, com o citado
subordinado ao autoral.

**Lei 9.610/1998, art. 47** — *"São livres as paráfrases e paródias que não forem
verdadeiras reproduções da obra originária nem lhe implicarem descrédito."*

**Em forma prática:**

| Fonte | Pode virar corpo? | Como |
|---|---|---|
| lei, decreto, súmula, decisão, acórdão, ato oficial | **sim, integral** | art. 8º, IV — sem autorização; com URL e data por dever de proveniência (R9), não por dever legal |
| obra doutrinária, artigo assinado, livro | **só trecho** | art. 46, III — citação identificada, na medida justificada, com autor e origem |
| **notícia institucional de tribunal** | **não** como redação | o fato é livre; a redação do texto jornalístico não está no art. 8º, IV |
| portal jurídico privado | **não** como corpo | sinal interno com metadado e trecho hasheado (§12 do CLAUDE.md) |

---

## 4. LGPD sobre dado já público em ato processual

| Dispositivo | O que estabelece |
|---|---|
| **art. 5º, I** | nome é dado pessoal — ser dado pessoal **não** o torna secreto |
| **art. 5º, II** | rol **fechado** de dado sensível: origem racial ou étnica, convicção religiosa, opinião política, filiação sindical ou a organização religiosa/filosófica/política, saúde, vida sexual, dado genético ou biométrico. **Nome puro não está nele; "estar em processo" também não** |
| **art. 7º, IX** | **base legal deste portal**: *"quando necessário para atender aos interesses legítimos do controlador ou de terceiro, exceto no caso de prevalecerem direitos e liberdades fundamentais do titular"* |
| **art. 7º, §3º** | *"O tratamento de dados pessoais cujo acesso é público deve considerar a finalidade, a boa-fé e o interesse público que justificaram sua disponibilização."* — **autorização condicionada, não vedação** |
| **art. 6º, I e III** | finalidade e necessidade — é aqui que a restrição morde de verdade |
| **art. 11** | é **este** que restringe dado sensível; o art. 5º, II apenas define |

**Precisão que evita erro comum:** não invoque o **art. 7º, §4º** ("dados tornados
manifestamente públicos **pelo titular**") para dado processual. A parte não tornou
seu nome público por vontade própria — **a lei** o tornou público. O par correto é
**art. 7º, IX + §3º**, filtrado pelo art. 6º, I e III.

**Dado sensível em ato público:** menção a saúde, religião ou orientação sexual
dentro de um ato oficial publicado não transforma o ato em sigiloso, mas o
tratamento do **dado sensível em si** passa a exigir o art. 11 — que não tem
hipótese de "legítimo interesse". Na prática, para este portal: **não se extrai nem
se destaca o dado sensível**; publica-se o ato, sem construir índice ou perfil sobre
o atributo sensível.

**Lei 12.527/2011, art. 31** obriga tratamento transparente de informação pessoal,
com respeito à intimidade, vida privada, honra e imagem. **CF art. 5º, LXXIX** (EC
115/2022) elevou a proteção de dados a direito fundamental: não revoga a publicidade
do dado público, obriga ponderação.

---

## 5. O que NÃO é vedação

Três camadas. Confundi-las é o defeito que este documento existe para impedir.

### 5.1 Restrições inventadas neste repositório — não existem na norma

| Restrição invocada | Por que é invenção |
|---|---|
| *"Citação legal mal atribuída é risco disciplinar sob a OAB"* | Não há dispositivo sobre exatidão técnica de citação em conteúdo informativo. Os únicos textos de veracidade (Prov. art. 1º, §§1º-2º; art. 3º, II) são de **publicidade**, e o art. 34, XVI do Estatuto é dever de atender à fiscalização (§1.4) |
| *"Página informativa exige revisão humana antes de publicar"* | Nenhuma norma exige revisão humana prévia. Ordem do dono, 2026-08-29 e 2026-09-15: quem revisa é o Claude Code e os agentes |
| *"CTA de WhatsApp em artigo viola o CED art. 40, V"* | O art. 4º, §3º do Prov. 205/2021 **equipara** ao e-mail todos os meios de contato, inclusive mensageria e redes (§1.3) |
| *"O termo de uso do DataJud/CNJ exige autorização prévia por escrito"* | A cláusula 3.8 não contém essa ressalva (conferido no texto oficial V1.2 — `docs/goal/DOSSIE_DATAJUD_CLAUSULAS_3_3_E_3_8.md`); quem prevê autorização é a 3.13, e só para o teto de 120 req/min |
| *"API pública não pode ser usada com finalidade comercial"* | Nenhum dispositivo. O ato processual é público por CF art. 5º, LX, art. 37, art. 93, IX, CPC art. 189 e Lei 12.527/2011; o limite é técnico (teto de requisições) e de proveniência |
| *"Nome de parte não pode aparecer"* | Res. CNJ 121/2010, art. 2º, II diz o contrário, expressamente |
| *"Mencionar tema de família implica segredo de justiça"* | O segredo alcança **os autos**, não o tema (§2.4) |
| *"Falar de gratuidade de justiça ou BPC/LOAS é oferta de gratuidade"* | O art. 3º, I veda **honorários, forma de pagamento, gratuidade ou desconto do próprio serviço** como captação — não o instituto jurídico da assistência gratuita |
| *"Atendimento 100% digital / online é promessa de resultado"* | Descreve modo real de atendimento; promessa é de **resultado**, não de meio (Prov. art. 6º, p.ú.) |

### 5.2 Regras internas de engenharia — obrigatórias aqui, mas não são lei

O dono pode alterá-las por ordem; a norma, não. Nunca as apresente como exigência
legal, e nunca as derrube sozinho invocando "a lei não exige".

- **Remover CPF e RG de todo texto publicado.** Escolha mais estrita que a lei —
  o CP art. 234-B, §1º (Lei 15.035/2024) chega a tornar público o CPF do réu
  condenado. Fundamento interno: publicar CPF distribui credencial.
- **URL, data e hash da fonte oficial.** Dever de proveniência (R9 do contrato). A
  Lei 9.610/98, art. 8º, IV **não** exige atribuição para ato oficial.
- **Proibição de "paráfrase mecânica".** Regra de qualidade editorial e anti-thin
  content. A Lei 9.610/98, art. 47 declara **livres** as paráfrases.
- **Similaridade de corpo < 0,70 e anti-template.** Engenharia editorial e SEO.
- **Duas menções à inscrição OAB por página, exatamente.** O CED art. 44 **exige**
  constar nome e número de inscrição; o teto de duas é sobriedade calibrada aqui.
- **Não mencionar ferramenta, IA ou assistência em artefato público.** Ordem do
  dono de 2026-09-09 sobre autoria. **Conferido:** existe a **Recomendação CFOAB
  n. 001/2024** (Proposição n. 49.0000.2024.007325-9/COP, relator Cons. Federal
  Francisco Queiroz Caputo Neto, 11.11.2024), cujo item 4 trata de *"Comunicação
  sobre o uso de IA Generativa"* — e ela é **recomendação** (*"Recomenda-se
  transparência **com o cliente**…"*, item 4.1), dirigida à **relação com o cliente
  na prestação do serviço**: formalização prévia por documento escrito, consentimento
  informado e direito do cliente de interagir com um ser humano (itens 4.1.1, 4.2.1
  e 4.3). **Ela não impõe divulgação de uso de IA em conteúdo informativo público**,
  e não é provimento. Se um dia este portal prestar serviço a cliente por dentro da
  plataforma, o item 4 passa a valer **nessa relação** — não nas páginas.
  Divulgação oficial: `oab.org.br/noticia/62711`; texto conferido no PDF do próprio
  Conselho Federal (hash na §7).

### 5.3 Vedações reais que continuam valendo — não as afrouxe

Promessa de resultado (Prov. art. 6º, p.ú.) · preço, forma de pagamento, gratuidade
ou desconto como captação (art. 3º, I) · informação que induza a erro (art. 3º, II)
· especialidade sem título ou notória especialização (art. 3º, III c/c EAOAB art.
3º-A, p.ú.) · expressão persuasiva, autoengrandecimento e comparação (art. 3º, IV) ·
incitar diretamente ao litígio ou à contratação (art. 3º, §1º) · caso concreto como
oferta e ostentação (art. 6º e p.ú.) · induzir o leitor a litigar (CED art. 41) ·
responder consulta com habitualidade em meio de comunicação social (CED art. 42, I)
· listas de clientes e demandas (CED art. 42, IV) · sensacionalismo (CED art. 43,
p.ú.) · resposta automática indiscriminada a consulta de não cliente (Anexo Único) ·
impulsionamento fraudulento (art. 4º, §5º) · mala direta e panfletagem (CED art. 40,
VI; Anexo Único) · rádio, cinema, televisão, outdoor (CED art. 40, I e II).

---

## 6. Quem alegar restrição cita o dispositivo

**Regra de encerramento, vinculante para todo agente deste repositório:**

> Alegação de impedimento jurídico só bloqueia trabalho se vier com **norma,
> artigo e URL oficial**. "Risco sob a OAB", "exposição disciplinar",
> "responsabilidade profissional", "pode dar problema" e "por precaução" **não são
> fundamento** e não param nada.
>
> Sem dispositivo citado, **a rota segue aberta** e o trabalho continua.
>
> Com dispositivo citado, a discussão é sobre o **texto**: leia o artigo inteiro,
> leia o artigo seguinte e verifique se outra norma o excepciona — foi assim que o
> art. 40, V do CED (que pareceria proibir o WhatsApp) encontrou o art. 4º, §3º do
> Provimento (que o autoriza).
>
> **Cautela inventada não é prudência: é trabalho não entregue, e quem responde
> pelo risco é o dono, não o agente.**

---

## 7. Tabela de prova

Todas as requisições em **2026-09-16**, com o agente do portal
`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; pesquisa-juridica-fonte-oficial)`.
SHA-256 = 16 primeiros hexadígitos do corpo baixado.

| Afirmação | Norma | Artigo | URL oficial | Bytes / SHA-256 | Conferido no texto oficial |
|---|---|---|---|---|---|
| Marketing jurídico é permitido | Prov. CFOAB 205/2021 | art. 1º | `oab.org.br/leisnormas/legislacao/provimentos/205-2021` | 73.589 / `c80f9ef427f33eef` | **sim** |
| Marketing de conteúdo é figura nomeada | Prov. 205/2021 | art. 2º, II | idem | idem | **sim** |
| Publicidade passiva definida | Prov. 205/2021 | art. 2º, VII | idem | idem | **sim** |
| Captação = indução ativa a contratar/litigar | Prov. 205/2021 | art. 2º, VIII | idem | idem | **sim** |
| Vedado preço/gratuidade/desconto como captação | Prov. 205/2021 | art. 3º, I | idem | idem | **sim** |
| Vedada informação que induza a erro | Prov. 205/2021 | art. 3º, II | idem | idem | **sim** |
| Vedada especialidade sem título | Prov. 205/2021 | art. 3º, III | idem | idem | **sim** |
| Vedado persuasivo/autoengrandecimento/comparação | Prov. 205/2021 | art. 3º, IV | idem | idem | **sim** |
| Sóbrio = sem incitar diretamente a litigar/contratar | Prov. 205/2021 | art. 3º, §1º | idem | idem | **sim** |
| Conteúdo jurídico admite publicidade ativa ou passiva | Prov. 205/2021 | art. 4º, caput | idem | idem | **sim** |
| Contato, site, redes e mensageria equiparam-se a e-mail | Prov. 205/2021 | art. 4º, §3º | idem | idem | **sim** |
| Vedado impulsionamento fraudulento | Prov. 205/2021 | art. 4º, §5º | idem | idem | **sim** |
| Vedada menção a decisões e resultados **obtidos em procedimento que patrocina ou participa** | Prov. 205/2021 | art. 4º, §2º | idem | idem | **sim** |
| Vedado caso concreto/resultado em vídeo e live | Prov. 205/2021 | art. 5º, §3º | idem | idem | **sim** |
| Promessa de resultado e caso concreto vedados em qualquer publicidade | Prov. 205/2021 | art. 6º e p.ú. | idem | idem | **sim** |
| Criação de conteúdo: técnico-informativa, sem resultados/clientes/valores | Prov. 205/2021 | Anexo Único | idem | idem | **sim** |
| Chatbot permitido para primeiras dúvidas | Prov. 205/2021 | Anexo Único | idem | idem | **sim** |
| Vedada resposta automática indiscriminada a não clientes | Prov. 205/2021 | Anexo Único | idem | idem | **sim** |
| Palavra-chave permitida se responsiva a busca do cliente | Prov. 205/2021 | Anexo Único | idem | idem | **sim** |
| Publicidade tem caráter **meramente informativo** | CED (Res. 02/2015) | art. 39 | `oab.org.br/leisnormas/legislacao/resolucoes/02-2015` | 107.253 / `672887efbfaf9666` | **sim** |
| Meios vedados; contato em artigo, com ressalva de e-mail | CED | art. 40, I-VI e p.ú. | idem | idem | **sim** |
| Texto divulgado não deve induzir o leitor a litigar | CED | art. 41 | idem | idem | **sim** |
| Vedado responder consulta com habitualidade | CED | art. 42, I | idem | idem | **sim** |
| Vedada lista de clientes e demandas | CED | art. 42, IV | idem | idem | **sim** |
| Manifestação pública só ilustrativa/educacional; sem sensacionalismo | CED | art. 43 e p.ú. | idem | idem | **sim** |
| Nome e inscrição OAB na publicidade; site, e-mail, QR code admitidos | CED | art. 44 e §1º | idem | idem | **sim** |
| Internet como veículo, sem oferecimento de serviços | CED | art. 46 e p.ú. | idem | idem | **sim** |
| Existe art. 47-A (TAC, Res. 04/2020) | CED | art. 47-A | idem | idem | **sim** |
| Captação de causas é infração disciplinar | Lei 8.906/94 | art. 34, IV | `planalto.gov.br/ccivil_03/leis/l8906.htm` | 194.129 / `fcb308690f7de12a` | **sim** |
| Art. 34, XVI é descumprir determinação da Ordem | Lei 8.906/94 | art. 34, XVI | idem | idem | **sim** |
| Deturpar citação de lei/julgado **para confundir adversário ou iludir o juiz da causa** é infração — norma processual e dolosa | Lei 8.906/94 | art. 34, XIV | idem | idem | **sim** |
| Dever geral de veracidade e boa-fé | CED | art. 2º, p.ú., II | `oab.org.br/leisnormas/legislacao/resolucoes/02-2015` | 107.253 / `672887efbfaf9666` | **sim** |
| Vedado falsear deliberadamente a verdade em Juízo ou via administrativa | CED | art. 6º | idem | idem | **sim** |
| Notória especialização | Lei 8.906/94 | art. 3º-A e p.ú. | idem | idem | **sim** |
| Restrição à publicidade processual exige lei | CF/88 | art. 5º, LX | `planalto.gov.br/ccivil_03/constituicao/constituicao.htm` | 1.839.482 / `aac8f3f0c8d6a1e8` | **sim** |
| Publicidade é princípio da administração | CF/88 | art. 37, caput | idem | idem | **sim** |
| Julgamentos são públicos | CF/88 | art. 93, IX | idem | idem | **sim** |
| Proteção de dados é direito fundamental | CF/88 | art. 5º, LXXIX | idem | idem | **sim** |
| Atos processuais são públicos; segredo é rol taxativo | CPC | art. 189 | `planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm` | 1.691.158 / `47d76df7a0e89ba0` | **sim** |
| Publicidade como preceito geral, sigilo como exceção | Lei 12.527/2011 | art. 3º, I | `planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm` | 109.489 / `a3196c876bfb9c4a` | **sim** |
| Tratamento transparente de informação pessoal | Lei 12.527/2011 | art. 31 | idem | idem | **sim** |
| Ato oficial e decisão judicial sem proteção autoral | Lei 9.610/98 | art. 8º, IV | `planalto.gov.br/ccivil_03/leis/l9610.htm` | 148.434 / `955cc29776efb2eb` | **sim** |
| Citação lícita com autor e origem | Lei 9.610/98 | art. 46, III | idem | idem | **sim** |
| Pequenos trechos subordinados à obra nova | Lei 9.610/98 | art. 46, VIII | idem | idem | **sim** |
| Paráfrase é livre | Lei 9.610/98 | art. 47 | idem | idem | **sim** |
| Nome é dado pessoal; rol fechado de sensível | LGPD | art. 5º, I e II | `planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm` | 310.252 / `9dfb3b3a946f84f7` | **sim** |
| Legítimo interesse como base | LGPD | art. 7º, IX | idem | idem | **sim** |
| Dado de acesso público: finalidade, boa-fé, interesse público | LGPD | art. 7º, §3º | idem | idem | **sim** |
| Dado sensível restringido pelo art. 11 | LGPD | art. 11 | idem | idem | **sim** |
| Consulta processual livre a qualquer pessoa | Res. CNJ 121/2010 | art. 1º | `atos.cnj.jus.br/atos/detalhar/92` | 18.141 / `c95a6aaf23458331` | **sim** |
| **Nome das partes é dado básico de livre acesso** | Res. CNJ 121/2010 | art. 2º, II | idem | idem | **sim** |
| CPF é critério de localização, não conteúdo divulgado | Res. CNJ 121/2010 | art. 4º, III | idem | idem | **sim** |
| Criminal pós-trânsito e trabalhista com consulta restrita | Res. CNJ 121/2010 | art. 4º, §1º | idem | idem | **sim** |
| Nome de vítima não é dado básico no criminal | Res. CNJ 121/2010 | art. 4º, §2º | idem | idem | **sim** |
| Base de decisões impede busca pelo nome das partes | Res. CNJ 121/2010 | art. 5º | idem | idem | **sim** |
| Vedada identificação de adolescente autor, inclusive iniciais | ECA | art. 143 e p.ú. | `planalto.gov.br/ccivil_03/leis/l8069.htm` | 696.305 / `6a9015e59c8dcb7b` | **sim** |
| Divulgar nome/ato/documento de procedimento sobre ato infracional é infração administrativa com multa | ECA | art. 247 e §1º | idem | idem | **sim** |
| Direito ao respeito abrange preservação da imagem e da identidade | ECA | art. 17 | idem | idem | **sim** |
| Sigilo do registro de adoção; acesso só ao adotado após os 18 | ECA | art. 47, *caput*, §§2º e 4º; art. 48 | idem | idem | **sim** |
| Nome da ofendida sob sigilo; autor do fato não | Lei 11.340/2006 | art. 17-A e p.ú. (Lei 14.857/2024) | `planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm` | 264.515 / `488268242fbb9247` | **sim** |
| Crimes sexuais em segredo de justiça | CP | art. 234-B (Lei 12.015/2009) | `planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm` | 673.409 / `10f92e9479c7d764` | **sim** |
| Nome e CPF do réu condenado tornam-se públicos | CP | art. 234-B, §§1º-3º (Lei 15.035/2024) | idem | idem | **sim** |
| Transparência sobre IA generativa é **com o cliente**, por recomendação | CFOAB, Recomendação n. 001/2024 | itens 4.1, 4.1.1, 4.2.1, 4.3 | `s.oab.org.br/arquivos/2024/11/7160d4fe-9449-4aed-80bc-a2d7ac1f5d2f.pdf` | 1.302.782 / `95235c9364bb6a7e` | **sim** |
| Tese do Tema 483 (nomes e vencimentos de servidores) | STF, ARE 652.777 | Tema 483 | `portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=483` | — | **não — ver §7.1** |

### 7.1 O que NÃO foi confirmado em fonte primária nesta passada

1. **STF, Tema 483 (ARE 652.777).** O portal do STF devolveu **HTTP 403** às
   requisições do `WikijuridicaBot` (inclusive depois de corrigida a cadeia TLS —
   o servidor não envia o intermediário GlobalSign GCC R6 AlphaSSL CA 2025). **Não
   se disfarçou o agente como navegador**, por proibição expressa do §11 do
   CLAUDE.md. A tese está confirmada por busca restrita ao domínio `stf.jus.br` e
   pela verificação registrada em `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md`
   (2026-08-29). **Por isso este documento não apoia nenhuma conclusão apenas no
   Tema 483** — a âncora do nome da parte é a Res. CNJ 121/2010, art. 2º, II.
2. **Lei 13.431/2017, art. 12, §§5º e 6º** (depoimento especial de criança e
   adolescente vítima ou testemunha) — **não baixada** nesta passada. O documento
   irmão a cita; quem depender dela confira o texto no Planalto antes de usar.
3. **Ementas de Tribunais de Ética e Disciplina** sobre publicidade — não há base
   consolidada de acesso aberto conferida nesta passada. Onde um agente precisar de
   precedente do TED, **escreva "sem fonte oficial localizada"** em vez de supor.
4. **Resoluções 18/2022-DIR, 23/2022-DIR e 24/2022-DIR** (composição do Comitê
   Regulador do Marketing Jurídico), citadas no art. 9º do Provimento — não
   baixadas; não afetam nenhuma regra de conteúdo deste documento.

---

## 8. Como este anexo entra no briefing

Cole no prompt de todo agente de conteúdo:

> Leia `docs/goal/JURIDICO_BASE.md` antes de decidir qualquer bloqueio por motivo
> jurídico. O bloco "DECIDA ASSIM" é vinculante. Se você for travar, adiar ou
> reduzir publicação por razão jurídica, **cite norma, artigo e URL** — sem isso, a
> rota segue aberta e o trabalho continua.

Documentos irmãos, quando o caso for de dado pessoal em fonte oficial ou de termo
de uso de API pública:

- `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` — nome, PII e as exceções, em
  detalhe, com o histórico de refutação.
- `docs/goal/DOSSIE_DATAJUD_CLAUSULAS_3_3_E_3_8.md` — o caso concreto de cláusula
  contratual lida como se fosse vedação legal.
- `docs/CONTRATO_DADO_REAL.md` — R1 a R10, incluindo R9 (fonte oficial com URL e
  data, ou "sem fonte oficial").
