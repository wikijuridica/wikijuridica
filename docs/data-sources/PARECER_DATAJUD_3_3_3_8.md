# Parecer — cláusulas 3.3 e 3.8 do Termo de Uso da API Pública do DataJud

**Consulente:** Wiki Jurídica (`wikijuridica.com.br`)
**Objeto:** uso da API Pública do DataJud (CNJ) pelo portal, à luz das cláusulas 3.3 e 3.8
**Fonte primária:** Termos de Uso da API Pública V1.2, 27/11/2023 — SHA-256 `2b974d5e580943981ad31bec8590200402ed29d79f58004d15d34a70aa307dd2`, obtido de `formularios.cnj.jus.br` em 2026-09-05, com confirmação cruzada em `datajud-wiki.cnj.jus.br`
**Dossiê de instrução:** `docs/goal/DOSSIE_DATAJUD_CLAUSULAS_3_3_E_3_8.md` (452 linhas, commit `bd2c9646`)
**Redigido por:** Claude Opus 5, em 2026-09-05
**ADOTADO** pelo subscritor em 2026-09-05
**Subscritor:** Rafael Toledo — OAB/RJ 227191

---

## Conclusões

Quem só precisa decidir lê estas oito linhas.

1. **O uso atual do portal é lícito e está dentro do Termo.** A consulta pontual por número de processo, servida a advogado verificado, e o agregado estatístico não configuram "fim comercial" da 3.3 nem "exploração comercial" da 3.8.
2. **O que a 3.3 e a 3.8 vedam por "uso comercial" é a mercantilização do CANAL e da BASE** — revender acesso, redistribuir o acervo, cobrar pelo dado. Não vedam o exercício profissional de quem consulta.
3. **A 3.8 não contém, e nunca conteve, exigência de autorização prévia por escrito.** Quem prevê autorização é a **3.13**, e exclusivamente para ultrapassar 120 requisições por minuto. Não há petição a protocolar.
4. **O limite vinculante é técnico, não conceitual:** 120 req/min (3.13). A cota repartida em 90 (consulta em primeiro plano) + 30 (worker) respeita esse teto por construção, com teste que exige a soma.
5. **A 3.9 gera obrigação real e ainda não cumprida:** publicar estudo ou página baseada no agregado exige dar ciência ao CNJ. Recomenda-se cumpri-la por escrito antes da primeira publicação desse tipo.
6. **O risco residual é contratual, não disciplinar nem penal.** A sanção que o próprio Termo prevê é a revogação de acesso (3.4 e 3.10). Não há tipo ético no CED ou no Provimento 205/2021 alcançado por esta conduta.
7. **`nivelSigilo > 0` é a única vedação absoluta**, e ela não vem do Termo: vem do CPC art. 189. Está implementada em três camadas independentes.
8. **Veredito: LIBERADO**, condicionado a (a) respeitar 120 req/min, (b) nunca exibir processo sigiloso, (c) cumprir a 3.9 antes de publicar estudo derivado, (d) registrar proveniência e data do dado em toda exibição.

---

## I. Premissa que precede as cláusulas: o dado é público, o canal é contratado

São duas coisas distintas, e confundi-las é a origem do erro que este parecer corrige.

**O dado processual é público por regra constitucional.** CF art. 5º, LX (a lei só restringe a publicidade quando a intimidade ou o interesse social o exigirem), art. 37 *caput* e art. 93, IX. O CPC art. 189 repete: *"os atos processuais são públicos"*, e o segredo é a lista taxativa dos incisos. A Lei 12.527/2011 fez da publicidade o preceito geral e do sigilo a exceção (art. 3º, I), e assegura o acesso **independentemente de motivação** (art. 10, § 3º). A Res. CNJ 121/2010, art. 2º, II, admite expressamente a consulta pública dos dados básicos do processo.

**O acesso por esta API específica é regido por contrato de adesão**, aceito tacitamente pelo uso (cláusula 1.2). O Termo não revoga a publicidade — não teria como, por hierarquia — mas rege as condições daquele canal.

A consequência prática é que o inadimplemento eventual do Termo **não torna ilícito o uso do dado**: torna descumprido um contrato cuja sanção própria é a perda do acesso (3.4, 3.10). É por isso que a qualificação do risco, no quesito 4 abaixo, é a que é.

---

## II. Respostas aos dez quesitos

### 1. CTA de contratação torna o uso "comercial" para a 3.3?

**Não.**

A 3.3, em transcrição literal: *"A API é fornecida exclusivamente para fins legais, não comerciais e autorizados, sendo seu uso indevido, abusivo, ilegal, malicioso ou imoral estritamente proibido."*

A expressão "não comerciais" qualifica **o fim do uso da API**, e não a natureza da atividade de quem a usa. Ler de outro modo produz absurdo verificável: nenhum escritório de advocacia, nenhuma empresa, nenhum jornal — todos entes que exercem atividade econômica — poderia consultar um dado que a LAI garante a qualquer pessoa sem exigir motivação. A interpretação que esvazia o direito de acesso da Lei 12.527/2011 não pode ser a correta.

O critério que separa uso comercial de uso profissional é **o objeto da comercialização**: comercializa-se a API quem revende o acesso, quem cobra pelo dado, quem redistribui o acervo como produto. Não comercializa quem consulta um processo público no exercício da própria profissão, ainda que a profissão seja remunerada.

O portal exibe CTA de contratação de advogado. Isso o torna uma atividade econômica — não torna a consulta processual uma venda da API.

### 2. Agregado de contagem é "informação derivada" para a 3.8? E o que a 3.8 proíbe?

**É informação derivada; e a 3.8 não proíbe usá-la.**

A 3.8, literal: *"O usuário concorda em não modificar, distribuir, vender ou explorar comercialmente a API ou qualquer informação derivada dela."*

Os quatro verbos são de **disposição sobre a coisa**: modificar, distribuir, vender, explorar comercialmente. Nenhum deles alcança o uso interno, a consulta, a leitura ou a análise. A cláusula veda transformar o dado em mercadoria ou em canal de redistribuição — não veda conhecê-lo.

Um agregado de contagem por assunto é informação derivada, sim. Publicá-lo como número informativo, com proveniência, não é vendê-lo nem distribuí-lo no sentido da cláusula, que pressupõe disponibilização do dado **como produto** a terceiros.

Ressalva honesta: "distribuir" é o verbo de maior superfície. Publicar em página pública uma **base consultável** derivada do DataJud — não um número, mas o acervo navegável — se aproximaria de distribuição. Este parecer não a autoriza; ela exigiria análise própria.

### 3. E a consulta por número de processo servida a advogado assinante?

**Lícita, e por fundamento mais forte que o agregado.**

Aqui não há sequer derivação: o que se serve é o próprio ato público, ao próprio interessado ou ao profissional que o representa, um processo por vez, mediante requisição individual. É a forma de uso mais próxima daquilo para que a API foi publicada.

O advogado que consulta processo pelo portal faz o que faria no balcão do fórum ou no PJe. A intermediação técnica não altera a natureza do ato.

Três salvaguardas já implementadas sustentam a conclusão, e sem elas ela seria mais frágil:

- **Sigilo:** `nivelSigilo > 0` não é exibido, guardado nem serializado, em três camadas independentes (`Consulta` não copia o corpo, `Guarda` não persiste, `DetalheDaResposta` recusa antes de qualquer parse).
- **Honestidade de cobertura:** toda resposta declara que o dado é histórico, traz a data em que o CNJ o atualizou e diz expressamente que não serve para contagem de prazo.
- **Teto:** 90 req/min para a consulta em primeiro plano e 30 para o worker, somando os 120 da 3.13.

### 4. Qual a natureza do risco, e há consequência disciplinar?

**Natureza: inadimplemento contratual. Consequência disciplinar: não há.**

A sanção que o próprio Termo prevê é a revogação de acesso — 3.4 (*"conceder ou revogar acesso sem aviso prévio"*) e 3.10 (*"monitorar o uso da API e tomar medidas para proteger seus direitos"*). Não há multa, não há cláusula penal, não há previsão de responsabilização pessoal.

Não se trata de direito autoral: os atos são públicos e, pela Lei 9.610/98 art. 8º, IV, textos oficiais não são obra protegida.

Quanto ao plano ético-disciplinar: o CED e o Provimento 205/2021 regem publicidade, captação, honorários e o dever de urbanidade. Descumprimento de termo de uso de API pública não encontra tipo em nenhum deles. Não se ignora o dever geral de probidade do art. 2º, parágrafo único, do CED — mas ele não converte inadimplemento contratual civil em infração disciplinar, e sustentar o contrário seria criar tipo por analogia, o que o direito sancionador não admite.

### 5. Veredito sobre a fonte

**LIBERADO, condicionado.** As condições estão nas conclusões 8(a) a 8(d) e devem constar da tabela de fontes.

A classificação anterior — "fechado" — apoiava-se em duas premissas hoje refutadas: a de que "não comercial" vedaria uso por portal com CTA (quesito 1) e a de que a 3.8 exigiria autorização prévia por escrito, texto que **a cláusula não contém**.

### 6. Que base legal registrar na proveniência de página que exiba número do DataJud?

**A Lei 12.527/2011 (arts. 3º, I; 7º; 8º) e a Res. CNJ 121/2010, art. 2º, II** — não a Lei 9.610/98 art. 8º.

O art. 8º da Lei de Direitos Autorais responde "isto é protegido por direito autoral?", e a resposta é não. Mas a pergunta da proveniência é outra: "o que autoriza publicar isto?". Quem autoriza é o regime de publicidade — a LAI e a resolução que abre a consulta pública.

Registre-se junto: a URL da API, a data da consulta e a data em que o CNJ atualizou o registro. Sem a última, o número aparenta atualidade que não tem.

### 7. A 3.9 dispara dever de dar ciência ao CNJ?

**Sim, e é a única obrigação positiva ainda não cumprida.**

A 3.9, literal: *"O usuário concorda em dar ciência ao CNJ de qualquer informação, notícia, estudo, relatório ou documento de qualquer natureza que seja disponibilizado ao público em geral."*

O alcance é amplo — "de qualquer natureza" — e a obrigação nasce da disponibilização ao público. Consulta individual servida a um advogado não é disponibilização ao público em geral; **página pública com estatística derivada é**.

Recomendação: antes da primeira publicação desse tipo, comunicação escrita ao CNJ, por protocolo eletrônico, com a identificação do usuário, a descrição do uso e o endereço da publicação. O Termo não indica canal específico; na ausência, o protocolo geral do CNJ é o caminho.

**Consequência operacional imediata:** enquanto a 3.9 não for cumprida, nenhum número derivado do DataJud deve aparecer em página pública. O uso hoje em produção — consulta individual ao advogado verificado — não é alcançado.

### 8. Quem é "o usuário"?

**O titular da chave de API**, que aqui é o portal — e, por trás dele, o subscritor deste parecer.

A 1.2 fixa aceitação tácita pelo uso; quem usa é quem detém a chave e dispara a requisição. O advogado assinante que consulta pelo portal **não** se torna usuário perante o CNJ: ele é destinatário de um serviço, sem relação contratual com a API.

Consequência prática, e ela é do subscritor: as obrigações do Termo — teto de requisições, 3.9, uso não comercial — recaem sobre o portal, não se repartem entre assinantes. O teto é do portal inteiro, e é por isso que a repartição 90/30 existe.

### 9. O cruzamento do `ranking_nacional.json` é alcançado pela 4.2?

**Não.**

A 4.2 veda cruzamento *para o fim de* coletar, armazenar ou processar dado pessoal. O cruzamento existente liga contagens agregadas por assunto e tribunal a títulos de páginas do próprio acervo. Não há dado pessoal em nenhum dos lados: nem no agregado (contagens), nem no acervo (títulos editoriais).

A cláusula é finalística. Sem a finalidade que ela descreve, não incide.

### 10. O foro de Brasília/DF muda o risco prático?

**Muda o custo, não a substância.**

A 5.1 elege Brasília/DF. Para inscrito na OAB/RJ, litigar lá é mais caro. Isso é relevante para a decisão de assumir risco, não para a licitude da conduta.

Registre-se, contudo, que a eleição de foro em contrato de adesão comporta discussão (CPC art. 63, § 3º), e que a hipótese de litígio é remota: a sanção natural do Termo é administrativa — revogar o acesso — e não demanda judicial.

---

## III. Recomendações operacionais

1. **Manter** a cota repartida 90/30 e o teste que exige a soma dos 120 da 3.13.
2. **Manter** as três camadas de recusa de `nivelSigilo > 0`. Esta é a única vedação absoluta, e ela é legal, não contratual.
3. **Cumprir a 3.9 por escrito** antes de publicar qualquer página com estatística derivada do DataJud. Até lá, nenhum número derivado em página pública.
4. **Registrar na proveniência** a URL da API, a data da consulta e a data de atualização do CNJ.
5. **Não construir** base consultável pública derivada do acervo do DataJud sem parecer específico — é o único uso que se aproxima do verbo "distribuir" da 3.8.
6. **Atualizar** `docs/data-sources/FONTES_DIARIAS.md` para "LIBERADO, condicionado", remetendo a este parecer.
7. **Não protocolar** petição de autorização sobre a 3.8: ela não prevê autorização, e o pedido pressuporia uma restrição que o texto não impõe.

---

## IV. Limites deste parecer

Ele responde ao que foi perguntado e não mais que isso. Fora do alcance:

- construção de base consultável pública derivada do DataJud (quesito 2, ressalva);
- uso de dado do DataJud para finalidade diversa da informativa e da consulta profissional;
- qualquer tratamento que envolva dado pessoal sensível do art. 5º, II da LGPD;
- processos em segredo de justiça, cuja vedação é legal e absoluta.

A análise parte do texto oficial V1.2 identificado no cabeçalho. Alteração do Termo pelo CNJ — que a 3.4 autoriza a qualquer tempo — exige revisão.

---

*Parecer ADOTADO pelo subscritor em 2026-09-05. A responsabilidade técnica é de Rafael Toledo, OAB/RJ 227191.*
