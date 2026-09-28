#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador do artefato Cowork W2 — família EMPRESARIAL / Contratos B2B & PJ.
Tmp (tools/_tmp_*, ignorado pelo .gitignore). Emite o .md com FACT-BRIEF + bloco jsonl
ingest-ready, com word_count calculado pela fórmula do gate (opening + headings +
textos das seções + FAQ q/a) e validação de title/meta/seções."""
import json, sys

CC   = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CPC  = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
LRF  = "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11101.htm"
LC123= "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp123.htm"
L9609= "https://www.planalto.gov.br/ccivil_03/leis/l9609.htm"
L13966="https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13966.htm"
DATA = "2026-07-22"

PAGES = []

# ------------------------------------------------------------------ 1
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22): A cláusula penal tem teto e pode ser revista. "
"CC art. 412 — o valor da cominação imposta na cláusula penal nao pode exceder o da obrigacao principal "
"(fonte: "+CC+"#art412, verificado 2026-07-22). CC art. 413 — a penalidade deve ser reduzida equitativamente "
"pelo juiz se a obrigacao principal tiver sido cumprida em parte, ou se o montante for manifestamente excessivo, "
"tendo-se em vista a natureza e a finalidade do negocio ("+CC+"#art413). CC art. 416 — para exigir a pena nao e "
"necessario que o credor alegue prejuizo ("+CC+"#art416). Enunciado 356 da IV Jornada de Direito Civil (CJF/STJ) e "
"jurisprudencia do STJ tratam o art. 413 como norma de ordem publica, com reducao ate de oficio. Franquia regida "
"pela Lei 13.966/2019, que revogou a Lei 8.955/94 e exige a Circular de Oferta de Franquia (COF) entregue ao menos "
"10 dias antes da assinatura ("+L13966+"#art2). Nao ha invencao de valor, prazo ou resultado."),
"intent_id":"emp-multa-rescisoria-franquia-desproporcional-reducao-judicial",
"page_type":"guia_problema","lane":"comercial",
"title":"Multa de rescisão da franquia é abusiva? Como reduzir",
"h1":"Reduzir na Justiça a multa rescisória do contrato de franquia",
"meta_description":"O franqueado pode pedir ao juiz a redução da multa de rescisão desproporcional. Veja o que dizem os arts. 412 e 413 do Código Civil e como reunir provas.",
"opening":(
"Sair de uma franquia antes do fim do contrato, ou ser desligado pela franqueadora, quase sempre esbarra numa multa "
"rescisória. Quando essa multa vem calculada sobre todas as mensalidades ou royalties que faltavam, o valor costuma "
"assustar e parecer uma punição por encerrar o negócio. A boa notícia é que a cláusula penal não é intocável: o "
"Código Civil fixa um teto e autoriza o juiz a reduzir o que for excessivo.\n\n"
"Isso não significa que toda multa cai por terra. Entender em que situações a redução é cabível, e o que precisa "
"ser demonstrado, é o que separa uma cobrança aceita de uma cobrança revista."),
"sections":[
{"heading":"O teto do art. 412 e a válvula de escape do art. 413",
"text":(
"A multa de rescisão é uma cláusula penal: um valor previamente combinado para o caso de descumprimento ou saída "
"antecipada. O art. 412 do Código Civil impõe um limite claro — a penalidade não pode ultrapassar o valor da própria "
"obrigação principal. Uma multa que, somada, supere aquilo que seria devido pelo contrato já nasce reduzível.\n\n"
"O art. 413 vai além e funciona como válvula de escape: o juiz deve reduzir a penalidade de forma equitativa em duas "
"hipóteses — quando a obrigação já foi cumprida em parte e quando o montante se mostra manifestamente excessivo, "
"considerando a natureza e a finalidade do negócio. O Superior Tribunal de Justiça trata essa regra como norma de "
"ordem pública, de modo que a redução pode ocorrer até de ofício, sem depender de um pedido perfeito do devedor.")},
{"heading":"Tempo cumprido e desproporção: os dois gatilhos da redução",
"text":(
"O primeiro gatilho é o cumprimento parcial. Um franqueado que operou três dos cinco anos contratados já pagou "
"royalties, investiu na marca e gerou receita para a rede; cobrar dele a multa cheia, como se nada tivesse cumprido, "
"ignora o art. 413 e o adimplemento havido.\n\n"
"O segundo gatilho é o excesso manifesto. Aqui pesa a comparação entre o valor da multa e o prejuízo real que a saída "
"causou à franqueadora. Uma cláusula que projeta lucros futuros por anos inteiros, sem relação com o dano efetivo, "
"tende a ser tida como desproporcional. Quanto mais próxima do fim estava a franquia, mais frágil fica a cobrança "
"integral.")},
{"heading":"O que joga a favor da franqueadora",
"text":(
"Um artigo honesto precisa mostrar o outro lado. A cláusula penal é válida e cumpre função legítima: pré-fixa as "
"perdas e danos e dispensa a franqueadora de provar prejuízo, por força do art. 416. O juiz reduz o excesso, não "
"anula a cláusula — logo, alguma multa em regra permanece.\n\n"
"Além disso, a franqueadora costuma alegar investimento em treinamento, cessão de know-how, exclusividade de "
"território e estrutura montada para o franqueado. Se a saída decorreu de descumprimento grave de padrão pelo próprio "
"franqueado, a multa ganha respaldo. Redução não é sinônimo de isenção, e cada contrato é lido junto com a Circular "
"de Oferta de Franquia entregue antes da assinatura, na forma da Lei 13.966/2019.")},
{"heading":"Como contestar o valor na prática",
"text":(
"O caminho começa antes do processo. Vale notificar a franqueadora apresentando os números — tempo de operação, "
"faturamento gerado, valor da multa frente ao que restava — e propor uma composição. Se a cobrança for judicializada, "
"a redução é pedida em contestação e, quando cabível, em reconvenção; o franqueado que quer antecipar a discussão pode "
"ajuizar ação revisional ou declaratória.\n\n"
"Reúna o contrato de franquia e seus aditivos, a COF, os comprovantes de faturamento e de tempo de operação e a "
"memória de cálculo da multa. Como o tema envolve leitura contratual fina e prova de desproporção, é comum conduzir a "
"causa com apoio de advogado, com triagem e envio dos documentos de forma digital e atuação a distância, o que "
"facilita quando franqueado e franqueadora estão em estados diferentes.\n\n"
"Exemplo: uma rede cobra de um ex-franqueado que operou três dos cinco anos uma multa equivalente a 100% dos royalties "
"dos dois anos restantes. Demonstrado o adimplemento parcial e a ausência de prejuízo proporcional, o valor é candidato "
"natural à redução equitativa do art. 413.")},
],
"faq":[
{"q":"A multa da franquia pode ser zerada pelo juiz?","a":"Em regra, não. O art. 413 autoriza a redução equitativa do excesso, e o art. 412 limita a multa ao valor da obrigação principal, mas a cláusula penal em si permanece válida — o juiz ajusta o montante, não elimina a penalidade."},
{"q":"Preciso provar que a franqueadora não teve prejuízo?","a":"A cláusula penal dispensa a prova de prejuízo para ser exigida (art. 416). Para reduzir, o que se demonstra é a desproporção: o tempo de contrato já cumprido e o tamanho da multa frente à obrigação principal e ao dano real."},
],
"official_sources":[
{"url":CC+"#art412","name":"Código Civil, art. 412","anchor_claim":"A multa (cláusula penal) não pode exceder o valor da obrigação principal."},
{"url":CC+"#art413","name":"Código Civil, art. 413","anchor_claim":"O juiz reduz a penalidade equitativamente no cumprimento parcial ou quando o valor é manifestamente excessivo."},
{"url":L13966+"#art2","name":"Lei 13.966/2019, art. 2º","anchor_claim":"Regime da franquia e entrega da Circular de Oferta de Franquia antes da assinatura."},
],
"internal_link_topics":["rescisao-contrato-franquia-o-que-franqueado-recebe","clausula-penal-limite-contrato-empresarial","encerrar-franquia-antes-do-prazo-multa","cof-circular-oferta-franquia-o-que-contem"],
})

# ------------------------------------------------------------------ 2
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22): Compensação de dívidas recíprocas. CC art. 368 — se duas pessoas "
"forem ao mesmo tempo credor e devedor uma da outra, as duas obrigacoes extinguem-se, ate onde se compensarem "
"("+CC+"#art368). CC art. 369 — a compensacao efetua-se entre dividas liquidas, vencidas e de coisas fungiveis "
"("+CC+"#art369). CC art. 373 — a diferenca de causa nao impede a compensacao, salvo excecoes (esbulho/furto/roubo; "
"comodato, deposito ou alimentos; coisa nao suscetivel de penhora) ("+CC+"#art373). CC art. 375 — nao havera "
"compensacao quando as partes, por mutuo acordo, a excluirem, ou no caso de renuncia previa de uma delas "
"("+CC+"#art375). Todos confirmados via busca em fonte oficial/planalto em 2026-07-22."),
"intent_id":"emp-compensacao-divida-entre-empresas-como-fazer",
"page_type":"pergunta","lane":"comercial",
"title":"Compensação de dívidas entre empresas: como funciona",
"h1":"Quando uma empresa abate o que deve com o que tem a receber",
"meta_description":"Se duas empresas devem uma à outra, o Código Civil permite compensar os valores e extinguir a dívida até onde coincidirem. Veja requisitos, limites e como formalizar.",
"opening":(
"É uma situação corriqueira entre empresas que mantêm relação continuada: a sua deve a um fornecedor e, ao mesmo "
"tempo, tem valores a receber dele por outra operação. Em vez de pagar de um lado e cobrar do outro, o Código Civil "
"permite encontrar as contas. Chama-se compensação, e ela extingue as obrigações até onde os créditos coincidirem."),
"sections":[
{"heading":"A regra do art. 368: crédito que encontra crédito",
"text":(
"O art. 368 do Código Civil é direto: se duas pessoas são, ao mesmo tempo, credora e devedora uma da outra, as duas "
"obrigações se extinguem até onde se compensarem. Se a empresa A deve R$ 20 mil à B e a B deve R$ 30 mil à A, "
"compensa-se o valor comum e resta apenas o saldo de R$ 10 mil.\n\n"
"Para a compensação chamada legal operar por si, o art. 369 exige três requisitos somados: as dívidas devem ser "
"líquidas (valor certo), vencidas (exigíveis) e de coisas fungíveis e da mesma espécie — tipicamente dinheiro. "
"Presentes esses pressupostos, a extinção recíproca decorre da própria lei, independentemente de acordo.")},
{"heading":"Quando a compensação não se aplica",
"text":(
"Nem todo débito entra na conta. O art. 373 ressalva hipóteses em que a compensação não é admitida — por exemplo, "
"quando uma das dívidas provém de esbulho, furto ou roubo, decorre de comodato, depósito ou alimentos, ou recai "
"sobre coisa não suscetível de penhora. E o art. 375 permite que as próprias partes afastem a compensação, seja por "
"acordo mútuo, seja por renúncia prévia de uma delas — cláusula comum em contratos empresariais.\n\n"
"Há ainda um limite prático decisivo: se o valor que a outra empresa deve a você está em discussão ou não é líquido, "
"não há compensação automática. Nesse cenário, ela é pleiteada em juízo, e o encontro de contas depende do "
"reconhecimento do crédito controvertido.")},
{"heading":"Como formalizar sem virar novo litígio",
"text":(
"Havendo os requisitos, o caminho mais limpo é documentar. Envie uma notificação ou firme um termo de compensação com "
"a memória dos débitos recíprocos, notas fiscais e contratos que os originam, deixando claro o saldo remanescente e "
"quem paga a quem. Isso evita que a operação seja lida depois como pagamento parcial ou reconhecimento indevido de "
"dívida.\n\n"
"Se a outra parte resiste ou já cobrou judicialmente, a compensação é alegada em contestação e, quando você tem saldo "
"a receber maior, em reconvenção. Por envolver conferência de valores e redação de termos, é frequente conduzir o "
"encontro de contas com apoio jurídico, com envio digital dos documentos e atendimento a distância, útil quando as "
"empresas ficam em cidades diferentes.")},
],
"faq":[
{"q":"Posso compensar sozinho, sem o aceite da outra empresa?","a":"Se as dívidas forem líquidas, vencidas e em dinheiro (art. 369), a compensação legal opera independentemente de acordo. Mas, se o outro discorda ou o valor está em discussão, quem decide o encontro de contas é o juiz."},
{"q":"Um contrato pode proibir a compensação?","a":"Sim. O art. 375 admite que as partes excluam a compensação por acordo mútuo ou por renúncia prévia de uma delas — por isso vale checar se o contrato tem cláusula nesse sentido antes de simplesmente abater os valores."},
],
"official_sources":[
{"url":CC+"#art368","name":"Código Civil, arts. 368 e 369","anchor_claim":"Extinção recíproca de obrigações entre credores mútuos e requisitos (dívidas líquidas, vencidas e fungíveis)."},
{"url":CC+"#art373","name":"Código Civil, arts. 373 e 375","anchor_claim":"Hipóteses em que a compensação não é admitida e possibilidade de exclusão por acordo ou renúncia."},
],
"internal_link_topics":["notificacao-extrajudicial-cobranca-empresa","acordo-parcelamento-divida-empresarial-garantia","cessao-credito-notificacao-devedor","perdas-e-danos-inadimplemento-contratual-b2b"],
})

# ------------------------------------------------------------------ 3
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22): Cobrança com nota fiscal e comprovante de entrega. CPC art. 784 "
"enumera os titulos executivos extrajudiciais (letra de cambio, nota promissoria, duplicata, debenture, cheque, "
"escritura publica, documento particular assinado pelo devedor e por 2 testemunhas, entre outros); a nota fiscal "
"NAO consta do rol, logo nao autoriza execucao direta ("+CPC+"#art784). CPC art. 700 — a acao monitoria cabe a "
"quem tem prova escrita sem eficacia de titulo executivo; NF + comprovante de entrega assinado servem de prova "
"escrita ("+CPC+"#art700). CPC art. 701 — deferida a inicial, o juiz manda pagar em 15 dias; sem embargos, o "
"mandado vira titulo executivo. Verificado em fonte oficial/planalto e jurisprudencia em 2026-07-22."),
"intent_id":"emp-cobranca-nota-fiscal-comprovante-entrega-sem-contrato",
"page_type":"guia_problema","lane":"comercial",
"title":"Cobrar empresa só com nota fiscal e comprovante de entrega",
"h1":"Como cobrar quem não pagou tendo apenas a nota e o canhoto",
"meta_description":"Sem contrato assinado nem duplicata, a nota fiscal e o comprovante de entrega ainda permitem cobrar. Veja por que cabe ação monitória e quais outros caminhos existem.",
"opening":(
"Você vendeu a mercadoria ou prestou o serviço, emitiu a nota fiscal e tem o comprovante de que a entrega foi "
"recebida — mas não há contrato assinado nem duplicata emitida, e o cliente não paga. A dúvida é natural: dá para "
"cobrar só com esses papéis? Dá. Eles não permitem tudo, mas abrem caminhos concretos."),
"sections":[
{"heading":"Nota fiscal não é título executivo — e o que isso muda",
"text":(
"O art. 784 do Código de Processo Civil lista o que é título executivo extrajudicial: letra de câmbio, nota "
"promissória, duplicata, cheque, debênture, escritura pública, documento particular assinado pelo devedor e por duas "
"testemunhas, entre outros. A nota fiscal não está nessa lista.\n\n"
"Na prática, isso significa que você não pode ir direto à execução, que é o rito mais rápido, reservado a quem já tem "
"um título pronto. Mas ficar de fora do rol não impede a cobrança — apenas define por qual porta você entra.")},
{"heading":"A ação monitória, feita sob medida para esse caso",
"text":(
"O art. 700 do CPC criou a ação monitória justamente para quem tem prova escrita da dívida, porém sem a força de um "
"título executivo. A nota fiscal acompanhada do canhoto de entrega assinado (ou do comprovante logístico com "
"recebimento identificável) é o exemplo clássico dessa prova escrita.\n\n"
"O procedimento é ágil: aceita a inicial, o juiz expede mandado para o devedor pagar em quinze dias (art. 701). Se ele "
"não paga nem apresenta embargos, o mandado se converte em título executivo, e a cobrança segue para a fase de "
"expropriação. É o caminho que melhor aproveita a nota e o comprovante que você já tem em mãos.")},
{"heading":"Protesto e ação de cobrança: quando usar cada um",
"text":(
"Antes ou em paralelo, o documento comprobatório da dívida pode ser levado a protesto. O protesto pressiona o devedor "
"e permite a negativação em cadastros, funcionando como cobrança extrajudicial — mas não substitui a ação, apenas a "
"reforça.\n\n"
"Se a prova escrita for frágil (por exemplo, sem assinatura de recebimento), a via mais segura passa a ser a ação de "
"cobrança pelo procedimento comum, na qual se pode produzir outras provas, como testemunhas e trocas de mensagens. A "
"escolha entre monitória, protesto e cobrança depende diretamente da qualidade do que você conseguiu documentar.")},
{"heading":"O que fortalece a cobrança e o prazo que corre",
"text":(
"O ponto sensível é a entrega. Um canhoto assinado por quem recebeu, um aviso de recebimento dos Correios ou o "
"registro eletrônico da nota fiscal eletrônica dão robustez à prova. Sem isso, a monitória fica vulnerável a embargos "
"que neguem o recebimento.\n\n"
"Some ao conjunto o pedido de compra, e-mails de confirmação e o histórico de pagamentos anteriores do cliente. Fique "
"atento à prescrição: a pretensão de cobrança tem prazo, contado do vencimento, e deixar o débito envelhecer "
"enfraquece a via judicial. Como a definição do rito e a montagem da prova exigem análise caso a caso, é comum "
"estruturar a cobrança com apoio de advogado, com triagem e envio dos documentos de forma digital e atuação em "
"qualquer estado.\n\n"
"Exemplo: uma transportadora entregou a carga com canhoto assinado pelo destinatário, emitiu a nota e não recebeu os "
"R$ 8 mil combinados. Com a nota e o canhoto, ajuíza monitória; não havendo embargos, obtém o título e parte para a "
"execução.")},
],
"faq":[
{"q":"Preciso de contrato assinado para cobrar?","a":"Não. A nota fiscal com comprovante de entrega recebido serve de prova escrita e autoriza a ação monitória (art. 700 do CPC), mesmo sem contrato assinado ou duplicata."},
{"q":"Posso levar a nota fiscal a protesto?","a":"É possível protestar o documento que comprova a dívida. O protesto pressiona o devedor e permite negativá-lo, mas é medida de cobrança extrajudicial — não equivale à ação nem dispensa, sozinho, a via judicial."},
],
"official_sources":[
{"url":CPC+"#art784","name":"CPC, art. 784","anchor_claim":"Rol dos títulos executivos extrajudiciais, no qual a nota fiscal não figura."},
{"url":CPC+"#art700","name":"CPC, arts. 700 e 701","anchor_claim":"Ação monitória com base em prova escrita sem eficácia de título executivo e mandado de pagamento em 15 dias."},
],
"internal_link_topics":["acao-monitoria-cobrar-divida-empresa","executar-duplicata-requisitos-comprovante-entrega","protesto-como-cobrar-divida-empresa","empresa-nao-pagou-servico-como-cobrar"],
})

# ------------------------------------------------------------------ 4
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22): Depósito elisivo na falência. Lei 11.101/2005 art. 94, I — a "
"falencia pode ser decretada por impontualidade injustificada no pagamento de obrigacao liquida materializada em "
"titulo(s) protestado(s) cuja soma ultrapasse 40 salarios minimos ("+LRF+"#art94); tambem por execucao frustrada "
"(inc. II) e atos de falencia (inc. III). Art. 98, caput — citado, o devedor tem 10 dias para contestar; paragrafo "
"unico — nos pedidos com base nos incisos I e II do art. 94, o devedor pode, no prazo da contestacao, depositar o "
"valor correspondente ao total do credito, acrescido de correcao monetaria, juros e honorarios advocaticios, "
"hipotese em que a falencia nao sera decretada ("+LRF+"#art98). Art. 96 — materias de defesa do devedor. O deposito "
"elide a falencia e converte o feito em cobranca. Verificado em fonte oficial/planalto e doutrina em 2026-07-22."),
"intent_id":"emp-deposito-elisivo-contestar-pedido-de-falencia",
"page_type":"guia_problema","lane":"comercial",
"title":"Pedido de falência: o depósito elisivo que evita a quebra",
"h1":"Citada em pedido de falência? O depósito que afasta a decretação",
"meta_description":"Empresa citada em pedido de falência por dívida pode depositar o valor no prazo de defesa e impedir a quebra. Entenda o depósito elisivo do art. 98 da Lei 11.101.",
"opening":(
"Receber a citação de um pedido de falência assusta com razão: não é uma cobrança comum, e sim um processo que pode "
"levar ao encerramento da empresa. Só que a lei reserva ao devedor uma saída objetiva, disponível dentro do prazo de "
"defesa. Ela se chama depósito elisivo, e afasta a decretação da quebra sem obrigar você a abrir mão de discutir a "
"dívida."),
"sections":[
{"heading":"Como um credor consegue pedir a sua falência",
"text":(
"A Lei 11.101/2005 não transforma qualquer inadimplência em falência. O art. 94, inciso I, permite o pedido quando há "
"impontualidade injustificada no pagamento de obrigação líquida representada por título ou títulos protestados cuja "
"soma ultrapasse quarenta salários mínimos na data do pedido. Há ainda o inciso II (execução frustrada, quando o "
"devedor não paga, não deposita nem nomeia bens) e o inciso III (a prática de atos de falência).\n\n"
"O caminho mais comum é o do inciso I: um credor reúne duplicatas ou outros títulos protestados que somem acima do "
"piso legal e ajuíza o pedido. Por isso a falência funciona, na prática, como uma pressão severa de cobrança — e "
"exige reação rápida.")},
{"heading":"O relógio começa a correr: dez dias para reagir",
"text":(
"Citada a empresa, abre-se o prazo do art. 98: dez dias para contestar. Esse é o momento decisivo. Perder o prazo "
"significa abrir mão tanto da defesa quanto da principal ferramenta financeira à disposição do devedor.\n\n"
"Dentro desses dez dias, três respostas são possíveis e não se excluem: contestar a dívida, depositar o valor para "
"elidir a falência, ou fazer as duas coisas. A escolha depende de a dívida ser realmente devida e de a empresa ter "
"caixa para o depósito.")},
{"heading":"O depósito elisivo e o que ele cobre",
"text":(
"O parágrafo único do art. 98 é a válvula de segurança. Nos pedidos fundados nos incisos I e II do art. 94, o devedor "
"pode, no prazo da contestação, depositar o valor correspondente ao total do crédito, acrescido de correção "
"monetária, juros e honorários advocatícios — e, feito isso, a falência não será decretada.\n\n"
"O efeito é duplo. De um lado, elide-se o estado de insolvência presumida: a quebra fica afastada. De outro, o "
"processo não termina ali; converte-se em verdadeiro rito de cobrança, no qual ainda se discute a existência e a "
"exigibilidade da dívida. Se o devedor vencer essa discussão, levanta o depósito, no todo ou em parte; se perder, o "
"valor vai ao credor. Por isso depositar não é admitir a dívida.")},
{"heading":"Defesas além do depósito e o risco de não agir",
"text":(
"O depósito não é a única resposta. O art. 96 lista matérias de defesa que, se acolhidas, derrubam o próprio pedido — "
"como falsidade do título, prescrição, pagamento já feito, nulidade da obrigação ou vício do protesto. Quando a "
"empresa tem uma dessas defesas sólidas, pode contestar sem depositar, assumindo, porém, o risco de a quebra ser "
"decretada se a tese não vingar.\n\n"
"É aí que mora a decisão estratégica. Se a dívida é real mas a empresa é viável, o depósito preserva a atividade e "
"ganha tempo. Se a cobrança é indevida, a defesa técnica pode ser suficiente. Separe desde já a citação, os títulos "
"protestados, os comprovantes de pagamento e o balanço recente. Como o prazo é curto e a decisão pesa, é prudente "
"acionar advogado logo na citação, com triagem e envio dos documentos de forma digital e atuação a distância.\n\n"
"Exemplo: uma indústria é alvo de pedido de falência lastreado em duplicatas protestadas de R$ 120 mil. No prazo, "
"deposita o total com os acréscimos, afasta a quebra e segue discutindo; ao comprovar que R$ 30 mil já haviam sido "
"pagos, levanta essa diferença ao final.")},
],
"faq":[
{"q":"Depositar significa admitir que devo?","a":"Não. O depósito elisivo do art. 98, parágrafo único, afasta a decretação da falência, mas o processo passa a discutir a existência e a exigibilidade da dívida. Vencendo essa discussão, o devedor pode levantar o valor depositado."},
{"q":"Posso depositar só uma parte da dívida?","a":"O texto legal fala em depositar o valor total do crédito com correção, juros e honorários. Depósito parcial ou fora do prazo é objeto de controvérsia na jurisprudência; o seguro é depositar o total dentro dos dez dias de defesa."},
],
"official_sources":[
{"url":LRF+"#art94","name":"Lei 11.101/2005, art. 94","anchor_claim":"Hipóteses de pedido de falência, incluindo impontualidade de títulos protestados acima de 40 salários mínimos."},
{"url":LRF+"#art98","name":"Lei 11.101/2005, art. 98","anchor_claim":"Prazo de dez dias para contestação e depósito elisivo que impede a decretação da falência."},
{"url":LRF+"#art96","name":"Lei 11.101/2005, art. 96","anchor_claim":"Matérias de defesa do devedor no pedido de falência."},
],
"internal_link_topics":["pedido-falencia-empresa-devedora-requisitos","como-pedir-falencia-cliente-que-nao-paga","recuperacao-judicial-o-que-e-requisitos","habilitacao-credito-falencia-como-fazer"],
})

# ------------------------------------------------------------------ 5
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22): Responsabilidade do MEI/empresario individual. LC 123/2006 art. 18-A "
"define o MEI como o empresario individual optante pelo recolhimento em valores fixos mensais, com receita bruta "
"anual de ate R$ 81.000,00; desenquadramento obrigatorio ao exceder o limite ("+LC123+"#art18a). CC art. 966 define "
"empresario ("+CC+"#art966). O empresario individual (inclusive o MEI) e pessoa fisica que exerce empresa: o CNPJ "
"nao cria pessoa juridica distinta, e o patrimonio pessoal responde diretamente pelas dividas, com responsabilidade "
"ilimitada, dispensando o incidente de desconsideracao (entendimento consolidado do STJ: a firma individual e ficcao "
"que nao separa patrimonio). CPC art. 833 protege bens/verbas impenhoraveis, e a Lei 8.009/90 resguarda o bem de "
"familia, mesmo para o MEI. Verificado em fonte oficial/planalto, gov.br e jurisprudencia em 2026-07-22."),
"intent_id":"emp-mei-devedor-patrimonio-pessoal-responde-direto",
"page_type":"pergunta","lane":"comercial",
"title":"Cliente é MEI e não pagou: bens pessoais respondem?",
"h1":"Por que o patrimônio pessoal do MEI responde sem desconsideração",
"meta_description":"O MEI é empresário individual e não separa pessoa de empresa: os bens pessoais respondem direto pela dívida, sem precisar de desconsideração da personalidade jurídica.",
"opening":(
"Quando o devedor é um Microempreendedor Individual, muita gente supõe que o CNPJ o blinda como uma empresa comum. "
"Não é o caso. O MEI é um empresário individual, e essa diferença muda tudo na hora de cobrar: o patrimônio pessoal "
"do titular pode responder diretamente pela dívida, sem os obstáculos que existem nas sociedades."),
"sections":[
{"heading":"MEI é uma pessoa só: titular e negócio se confundem",
"text":(
"O MEI está definido no art. 18-A da Lei Complementar 123/2006 como o empresário individual que opta por recolher os "
"tributos em valores fixos mensais, com receita bruta anual de até R$ 81 mil. A palavra-chave é empresário "
"individual: por trás do CNPJ não há uma pessoa jurídica autônoma, e sim uma pessoa física que exerce atividade "
"empresarial, na forma do art. 966 do Código Civil.\n\n"
"Como o titular e o negócio são a mesma pessoa, os patrimônios se confundem. O Superior Tribunal de Justiça já "
"assentou que a firma individual é uma ficção que permite à pessoa natural atuar no mercado, sem que isso implique "
"separação entre o patrimônio do empresário e o da pessoa física titular. Não existe, ali, a barreira patrimonial "
"típica das sociedades.")},
{"heading":"Por que a cobrança dispensa a desconsideração",
"text":(
"Numa sociedade limitada, os bens dos sócios só são alcançados depois de instaurado o incidente de desconsideração da "
"personalidade jurídica, provando-se abuso — desvio de finalidade ou confusão patrimonial. É uma etapa a mais, com "
"contraditório próprio.\n\n"
"No MEI não há esse degrau. Como inexiste separação entre a pessoa física e a atividade, o titular responde de forma "
"direta e ilimitada pelas obrigações do negócio. O credor pode buscar o título ou a ação diretamente contra o CPF do "
"empreendedor, e a jurisprudência dispensa o incidente de desconsideração para atingir esse patrimônio.")},
{"heading":"Os limites da penhora e o que conferir antes",
"text":(
"Responder de forma ilimitada não é o mesmo que perder tudo. Continuam protegidos o bem de família, por força da Lei "
"8.009/90, e as verbas e bens impenhoráveis do art. 833 do CPC, como salários e instrumentos de trabalho dentro de "
"certos limites. A cobrança recai sobre o patrimônio penhorável do titular, não sobre o que a lei resguarda.\n\n"
"Antes de agir, vale confirmar a natureza jurídica no cadastro do CNPJ: em geral o MEI aparece como empresário "
"individual, mas existem casos em que o negócio se estruturou como sociedade, o que muda o regime. Reúna o contrato "
"ou a nota fiscal, o comprovante da dívida e essa consulta cadastral. Por envolver execução e delimitação de bens, "
"esse tipo de cobrança costuma ser conduzido com apoio de advogado, com envio digital dos documentos e atuação em "
"todo o país.\n\n"
"Exemplo: um prestador cobra R$ 15 mil de um cliente MEI que não pagou. Pode ajuizar a cobrança e, obtido o título, "
"executar diretamente os bens penhoráveis do titular, respeitados o bem de família e as verbas impenhoráveis.")},
],
"faq":[
{"q":"O MEI tem CNPJ, então não é pessoa jurídica?","a":"O MEI tem CNPJ para fins fiscais e de formalização, mas juridicamente é um empresário individual — pessoa física que exerce empresa. Não há personalidade jurídica separada do titular, e por isso o patrimônio pessoal responde pelas dívidas."},
{"q":"Todos os bens do MEI podem ser penhorados?","a":"Não. Mesmo respondendo de forma ilimitada, ficam protegidos o bem de família (Lei 8.009/90) e as verbas e bens impenhoráveis do art. 833 do CPC. A penhora atinge apenas o patrimônio que a lei admite constrangir."},
],
"official_sources":[
{"url":LC123+"#art18a","name":"Lei Complementar 123/2006, art. 18-A","anchor_claim":"Define o MEI como empresário individual optante pelo recolhimento fixo, com receita bruta anual de até R$ 81 mil."},
{"url":CC+"#art966","name":"Código Civil, art. 966","anchor_claim":"Conceito de empresário — pessoa que exerce profissionalmente atividade econômica organizada."},
{"url":CPC+"#art833","name":"CPC, art. 833","anchor_claim":"Bens e verbas impenhoráveis que limitam a constrição, inclusive do empresário individual."},
],
"internal_link_topics":["desconsideracao-personalidade-juridica-quando","empresario-individual-vs-sociedade-responsabilidade","negativar-empresa-devedora-serasa-pj","execucao-titulo-extrajudicial-contra-empresa"],
})

# ------------------------------------------------------------------ 6
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22): Incidente de desconsideracao (rito) + base material. CPC arts. "
"133 a 137 (verbatim, obtidos por fetch do planalto): art. 133 (instauracao a pedido da parte ou do MP; aplica-se a "
"desconsideracao inversa); art. 134 (cabivel em todas as fases do conhecimento, no cumprimento de sentenca e na "
"execucao de titulo extrajudicial; suspende o processo salvo se requerida na inicial; §4 exige demonstrar os "
"pressupostos legais); art. 135 (citado o socio/PJ, 15 dias para manifestar-se e requerer provas); art. 136 (decisao "
"interlocutoria; agravo interno se do relator); art. 137 (acolhido o pedido, alienacao/oneracao em fraude a execucao "
"e ineficaz frente ao requerente) ("+CPC+"#art133). Base material: CC art. 50, redacao da Lei 13.874/2019 — abuso "
"caracterizado por desvio de finalidade (proposito de lesar credores/atos ilicitos, §1) ou confusao patrimonial "
"(§2, I a III); §4 (grupo economico por si so nao basta); §5 (mera expansao da atividade nao e desvio) "
"("+CC+"#art50). Verificado em fonte oficial/planalto em 2026-07-22."),
"intent_id":"emp-incidente-desconsideracao-personalidade-como-pedir",
"page_type":"procedimento","lane":"comercial",
"title":"Incidente de desconsideração: como atingir os sócios",
"h1":"Como instaurar o incidente para alcançar os bens dos sócios",
"meta_description":"Execução travada contra empresa sem bens? O incidente de desconsideração dos arts. 133 a 137 do CPC permite pedir que os sócios respondam. Veja o passo a passo e os requisitos.",
"opening":(
"A execução avança, mas a empresa devedora não tem bens penhoráveis. É a situação que trava a recuperação de muitos "
"créditos empresariais. O caminho para alcançar o patrimônio dos sócios existe e tem nome: incidente de "
"desconsideração da personalidade jurídica. Mas ele não é automático — depende de requisitos de direito material e "
"de um rito próprio, que vale conhecer antes de peticionar."),
"sections":[
{"heading":"Antes do pedido: o abuso que a lei exige",
"text":(
"O incidente é o instrumento processual; o direito de fundo está no art. 50 do Código Civil, com a redação da Lei "
"13.874/2019. Ele só autoriza estender as obrigações aos sócios ou administradores quando há abuso da personalidade "
"jurídica, caracterizado por desvio de finalidade ou confusão patrimonial.\n\n"
"A própria lei define os termos. Desvio de finalidade é usar a empresa para lesar credores ou praticar atos ilícitos. "
"Confusão patrimonial é a ausência de separação de fato entre os patrimônios — por exemplo, a sociedade pagando "
"repetidamente contas pessoais do sócio, ou transferências de ativos sem contraprestação. O art. 50 ainda esclarece "
"que a mera existência de grupo econômico não basta e que a simples expansão da atividade não é desvio. Ou seja: a "
"empresa não ter bens, por si só, não abre o incidente.")},
{"heading":"Como e quando instaurar o incidente",
"text":(
"O art. 134 do CPC define a oportunidade: o incidente é cabível em todas as fases do processo de conhecimento, no "
"cumprimento de sentença e na execução fundada em título extrajudicial. Ele é instaurado a pedido da parte ou do "
"Ministério Público (art. 133) e aplica-se também à desconsideração inversa, quando se busca atingir a empresa por "
"dívida do sócio.\n\n"
"A instauração suspende o processo, salvo quando a desconsideração já é pedida na petição inicial — hipótese em que o "
"sócio é citado desde logo, sem incidente autônomo. O requerimento precisa demonstrar o preenchimento dos "
"pressupostos legais (art. 134, §4º): não basta afirmar que a empresa não paga; é preciso apontar o abuso e indicar "
"as provas que o sustentam.")},
{"heading":"O contraditório do sócio e a decisão",
"text":(
"Instaurado o incidente, o sócio ou a pessoa jurídica é citado para se manifestar e requerer as provas cabíveis no "
"prazo de quinze dias (art. 135). Garante-se, assim, o contraditório antes de qualquer constrição sobre o patrimônio "
"pessoal — diferentemente de uma penhora surpresa.\n\n"
"Concluída a instrução, se necessária, o incidente é resolvido por decisão interlocutória (art. 136). Dessa decisão "
"cabe agravo de instrumento; quando proferida por relator em tribunal, cabe agravo interno. É uma etapa que se "
"encerra dentro do próprio processo, sem exigir uma ação nova.")},
{"heading":"O efeito prático e o que reunir para o pedido",
"text":(
"Acolhido o pedido, o art. 137 traz a consequência mais valiosa para o credor: a alienação ou a oneração de bens "
"praticada em fraude à execução torna-se ineficaz em relação a quem requereu a desconsideração. Bens que o sócio "
"tentou pôr a salvo voltam a responder pela dívida.\n\n"
"Do outro lado, o pedido sem lastro é rejeitado, e a jurisprudência é firme em não confundir insolvência com abuso. "
"Por isso, o sucesso depende da prova: contratos e extratos que revelem confusão de contas, transferências de "
"ativos, esvaziamento da empresa em favor de outra do mesmo grupo, além de certidões de bens dos sócios e do contrato "
"social. Como a tese exige demonstrar o abuso com documentos, é comum estruturar o incidente com apoio de advogado, "
"com triagem e envio dos documentos de forma digital e atuação em qualquer comarca.\n\n"
"Exemplo: um sócio esvazia a empresa devedora e passa o faturamento para outra sociedade que ele controla. Com "
"extratos, notas e o contrato social das duas, o credor instaura o incidente e pede que os bens do sócio e da nova "
"empresa respondam pela dívida.")},
],
"faq":[
{"q":"A empresa não ter bens já basta para atingir o sócio?","a":"Não. É preciso demonstrar abuso da personalidade jurídica — desvio de finalidade ou confusão patrimonial (art. 50 do Código Civil). A simples insolvência, ou a existência de grupo econômico, não autoriza a desconsideração."},
{"q":"O incidente paralisa a execução?","a":"Sim. A instauração do incidente suspende o processo, salvo quando a desconsideração é requerida já na petição inicial — caso em que o sócio é citado de imediato, sem suspensão."},
],
"official_sources":[
{"url":CPC+"#art133","name":"CPC, arts. 133 a 137","anchor_claim":"Rito do incidente de desconsideração: instauração, suspensão do processo, contraditório em 15 dias, decisão e fraude à execução."},
{"url":CC+"#art50","name":"Código Civil, art. 50","anchor_claim":"Requisitos materiais da desconsideração: desvio de finalidade e confusão patrimonial, com os limites dos §§ 4º e 5º."},
],
"internal_link_topics":["desconsideracao-personalidade-juridica-quando","responsabilidade-administrador-dividas-empresa","execucao-titulo-extrajudicial-contra-empresa","socio-que-saiu-responde-dividas"],
})

# ------------------------------------------------------------------ 7
PAGES.append({
"fact_brief": (
"FACT-BRIEF (verificado ao vivo em 2026-07-22, fetch integral do planalto): Titularidade de software sob encomenda. "
"Lei 9.609/1998 art. 4 (verbatim) — salvo estipulacao em contrario, pertencerao exclusivamente ao empregador, "
"contratante de servicos ou orgao publico os direitos relativos ao programa de computador desenvolvido durante a "
"vigencia de contrato expressamente destinado a P&D, ou em que a atividade do contratado seja prevista, ou decorra da "
"natureza dos encargos; §1 (compensacao do trabalho limita-se a remuneracao convencionada); §2 (programa gerado sem "
"relacao com o contrato e sem uso de recursos do contratante pertence ao desenvolvedor) ("+L9609+"#art4). Art. 2 — o "
"programa e protegido pelo regime de direitos autorais; §3: a protecao independe de registro ("+L9609+"#art2). Art. "
"11 — a transferencia de tecnologia e registrada no INPI para efeitos perante terceiros, com entrega obrigatoria do "
"codigo-fonte comentado e documentacao ("+L9609+"#art11). O direito moral de paternidade do autor persiste (art. 2, "
"§1), mas nao impede a exploracao economica pelo titular. Sem invencao."),
"intent_id":"emp-desenvolvimento-software-encomenda-propriedade",
"page_type":"pergunta","lane":"comercial",
"title":"Software sob encomenda: de quem é o código-fonte?",
"h1":"Contratei o desenvolvimento de um sistema: a titularidade é minha?",
"meta_description":"Quem paga pelo desenvolvimento de um software nem sempre vira dono do código. Veja o que diz a Lei 9.609/98 e por que a cláusula de titularidade é decisiva no contrato.",
"opening":(
"Sua empresa contratou o desenvolvimento de um sistema, pagou pelo trabalho e agora quer ter certeza de que é dona do "
"código. A intuição diz que quem paga leva — mas, no software, a resposta depende de dois fatores combinados: o que a "
"Lei do Software estabelece e, principalmente, o que o contrato prevê sobre titularidade."),
"sections":[
{"heading":"A regra do art. 4º da Lei do Software",
"text":(
"A Lei 9.609/1998 trata do ponto no art. 4º. A regra é que, salvo estipulação em contrário, pertencem exclusivamente "
"ao empregador ou ao contratante de serviços os direitos sobre o programa desenvolvido durante a vigência de um "
"contrato expressamente destinado a isso, ou quando a criação decorre da natureza do que foi contratado.\n\n"
"Traduzindo para o dia a dia: se a empresa contratou justamente para que aquele sistema fosse desenvolvido, os "
"direitos tendem a ser dela, e a remuneração do desenvolvedor se limita ao valor combinado (art. 4º, §1º). O ponto "
"cego está no 'salvo estipulação em contrário' — o contrato pode dispor diferente, e a lei respeita essa escolha.")},
{"heading":"Quando o código pode não ser seu",
"text":(
"O mesmo art. 4º, no §2º, aponta a exceção: pertence ao desenvolvedor o programa gerado sem relação com o contrato e "
"sem o uso de recursos, dados ou equipamentos do contratante. Se o contrato foi vago — não deixou claro que o objeto "
"era desenvolver aquele software para a sua empresa — e o profissional usou ambiente e ferramentas próprias, a "
"titularidade fica disputável.\n\n"
"Some-se a isso que o software é protegido pelo regime dos direitos autorais (art. 2º). A transferência definitiva "
"desses direitos patrimoniais não se presume: precisa estar expressa e por escrito. Sem uma cláusula nesse sentido, "
"você pode ter pago pelo sistema e, ainda assim, não deter com segurança a titularidade do código.")},
{"heading":"A cláusula que resolve: cessão e entrega do código-fonte",
"text":(
"O contrato de desenvolvimento bem-feito não deixa a titularidade ao acaso. Ele prevê a cessão total e definitiva dos "
"direitos patrimoniais de autor ao contratante, a entrega do código-fonte comentado e da documentação técnica, e a "
"vedação de reuso do mesmo código em outros projetos. Um mecanismo de escrow de código pode garantir o acesso mesmo "
"em caso de conflito.\n\n"
"Quando há transferência de tecnologia, o art. 11 prevê o registro do contrato no INPI para produzir efeitos perante "
"terceiros, com entrega obrigatória do código-fonte comentado e do memorial descritivo. Vale lembrar que o direito "
"moral de paternidade do programador permanece com ele (art. 2º, §1º), mas isso não impede que a empresa explore "
"economicamente o software de que é titular.")},
{"heading":"Como se proteger antes e depois de contratar",
"text":(
"O outro lado é duro: sem cláusula de titularidade, o contratante corre risco mesmo tendo pago em dia, e a nota "
"fiscal, sozinha, não transfere direito autoral. A proteção do software independe de registro (art. 2º, §3º), mas o "
"registro e a cessão escrita ajudam a provar quem é o titular.\n\n"
"Antes de contratar, o ideal é um contrato de desenvolvimento com cessão expressa, definição de escopo e previsão de "
"entrega do código. Se o conflito já existe — o desenvolvedor se recusa a entregar o código-fonte ou alega ser o "
"autor —, o caminho passa por notificação e, se preciso, medida judicial. Reúna o contrato, a especificação do "
"escopo, o repositório com o histórico de commits e os comprovantes de pagamento. Por envolver leitura de contrato e "
"prova de autoria, é comum tratar o tema com apoio de advogado, com envio digital dos documentos e atuação a "
"distância.\n\n"
"Exemplo: uma startup pagou R$ 60 mil a um desenvolvedor autônomo que agora se recusa a entregar o código-fonte, "
"dizendo ser o autor. A definição depende de o contrato ter destinado o trabalho ao desenvolvimento do sistema e de "
"conter cláusula de cessão de direitos.")},
],
"faq":[
{"q":"Pagar pelo desenvolvimento já me torna dono do código?","a":"Nem sempre. Pelo art. 4º da Lei 9.609/98, os direitos tendem a ser do contratante quando o contrato se destina expressamente ao desenvolvimento, mas o próprio artigo admite estipulação em contrário. Sem cláusula de cessão, a titularidade pode ficar em disputa."},
{"q":"Preciso registrar o software no INPI para ser titular?","a":"Não. A proteção do programa independe de registro (art. 2º, §3º). Ainda assim, o registro e a cessão de direitos por escrito ajudam a comprovar a titularidade e a entrega do código-fonte, sobretudo em caso de conflito."},
],
"official_sources":[
{"url":L9609+"#art4","name":"Lei 9.609/1998, art. 4º","anchor_claim":"Titularidade do programa desenvolvido sob contrato pertence ao contratante, salvo estipulação em contrário."},
{"url":L9609+"#art2","name":"Lei 9.609/1998, art. 2º","anchor_claim":"Software protegido pelo regime de direitos autorais; proteção independe de registro."},
{"url":L9609+"#art11","name":"Lei 9.609/1998, art. 11","anchor_claim":"Registro de transferência de tecnologia no INPI e entrega obrigatória do código-fonte comentado."},
],
"internal_link_topics":["contrato-prestacao-servicos-clausulas-criticas","nda-clausulas-essenciais","desenvolvedor-reteve-codigo-fonte-escrow","vazamento-informacao-confidencial-o-que-fazer"],
})

# ------------------------------------------------------------------ compute + validate + emit
MIN_SECTIONS={"verbete":2,"pergunta":2,"procedimento":3,"guia_problema":4}
def wc(p):
    parts=[p["opening"]]
    for s in p["sections"]:
        parts.append(s["heading"]); parts.append(s["text"])
    for f in p["faq"]:
        parts.append(f["q"]); parts.append(f["a"])
    return len(" ".join(parts).split())

errs=[]
for p in PAGES:
    tl=len(p["title"]); ml=len(p["meta_description"]); ns=len(p["sections"])
    if not(20<=tl<=65): errs.append(f'{p["intent_id"]}: title len {tl}')
    if not(70<=ml<=160): errs.append(f'{p["intent_id"]}: meta len {ml}')
    mn=MIN_SECTIONS[p["page_type"]]
    if ns<mn: errs.append(f'{p["intent_id"]}: sections {ns}<{mn} ({p["page_type"]})')
    if p["h1"].strip()==p["title"].strip(): errs.append(f'{p["intent_id"]}: h1==title')
    for s in p["official_sources"]:
        if s["url"].rstrip("/").endswith((".gov.br","planalto.gov.br")) and "#" not in s["url"]:
            errs.append(f'{p["intent_id"]}: source homepage/no-anchor {s["url"]}')
    p["_wc"]=wc(p)

# heading uniqueness across all pages
allh={}
for p in PAGES:
    for s in p["sections"]:
        h=s["heading"].lower().strip(); allh[h]=allh.get(h,0)+1
dups=[h for h,c in allh.items() if c>1]
if dups: errs.append("dup headings: "+"; ".join(dups))

def emit_line(p):
    o={"intent_id":p["intent_id"],"title":p["title"],"meta_description":p["meta_description"],
       "h1":p["h1"],"opening":p["opening"],"sections":p["sections"],
       "faq":[{"q":f["q"],"a":f["a"]} for f in p["faq"]],
       "official_sources":p["official_sources"],
       "internal_link_topics":p["internal_link_topics"],"lane":p["lane"],
       "index_policy":"index","publication_allowed":False,"render_allowed":False,
       "sitemap_allowed":False,"approval":False,"public_path":"",
       "needs_source_research":False,"word_count":p["_wc"]}
    return json.dumps(o,ensure_ascii=False)

RANGE={"verbete":(350,700),"pergunta":(400,800),"procedimento":(500,1000),"guia_problema":(700,1400)}
out=[]
out.append("# OPUS_FLEET_W2 — Geração EMPRESARIAL / Contratos B2B & PJ (Cowork Opus, 2026-07-22)\n")
out.append("Família: **empresarial** (contratos B2B & PJ, lane comercial). Autor Opus 4.8, onda W2 do fleet.")
out.append("Método: intents net-new do gap portfólio×estoque (`data/editorial/portfolio_v2/empresarial*.jsonl` "
           "menos `data/editorial/v2_pages/*.jsonl`), 167 intents no gap; selecionados 7 de ângulos distintos, "
           "cada um com base legal específica **verificada AO VIVO** (planalto/gov.br) em 2026-07-22.\n")
out.append("Dedup: nenhum dos 7 intent_id existe no estoque (checado contra 245 intents empresariais atuais). "
           "Ângulos cobertos: cláusula penal/distrato (franquia), cobrança PJ (compensação; NF sem título), "
           "insolvência (depósito elisivo), responsabilidade de sócio (incidente de desconsideração; MEI), "
           "prestação de serviços/tech B2B (software sob encomenda).\n")
out.append("Todos os drafts nascem **bloqueados**: `index_policy=index`, `publication_allowed=render_allowed="
           "sitemap_allowed=false`, `approval=false`, `public_path=\"\"`, `needs_source_research=false`. "
           "`official_sources` sem `verified_at`/`http_status` (a evidência HTTP é preenchida pela ingestão, "
           "conforme WRITING_SPEC §7). `faq` no schema real `{q,a}`.\n")
out.append("Candidato adicional já verificado ao vivo e pronto para próxima onda (não incluído para respeitar o "
           "teto de 7): `emp-meios-de-recuperacao-judicial-opcoes-do-plano` (Lei 11.101 arts. 47, 50 e 60, §ú — "
           "rol exemplificativo de meios; UPI sem sucessão, STF ADI 3.934).\n")
out.append("---\n")
for i,p in enumerate(PAGES,1):
    lo,hi=RANGE[p["page_type"]]
    flag="" if lo*0.9<=p["_wc"]<=hi*1.1 else "  ⚠fora-da-faixa"
    out.append(f"## {i}. `{p['intent_id']}`  ·  {p['page_type']}  ·  {p['lane']}  ·  {p['_wc']} palavras{flag}\n")
    out.append(p["fact_brief"]+"\n")
    out.append("```jsonl")
    out.append(emit_line(p))
    out.append("```\n")

path="docs/goal/cowork/OPUS_FLEET_W2_gen_empresarial_20260722.md"
with open(path,"w",encoding="utf-8") as fh:
    fh.write("\n".join(out)+"\n")

print("WROTE",path)
print("PAGES",len(PAGES))
for p in PAGES:
    print(f'  {p["intent_id"]:60s} type={p["page_type"]:13s} wc={p["_wc"]:4d} title={len(p["title"])} meta={len(p["meta_description"])} sec={len(p["sections"])}')
print("ERRORS:", errs if errs else "none")
