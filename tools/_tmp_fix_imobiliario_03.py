#!/usr/bin/env python3
"""Correcoes juridico-editoriais auditadas do shard imobiliario-03."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-03.jsonl"
EXPECTED_SHA256 = "45da2ae81e5b471beadc11220c5d6f3919b669cbf61a3c59e5683f109c50cff4"
LEI = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


UPDATES = {
    "imob-sublocacao-quando-pode": {
        "sections": {
            "O que exige o artigo 13 da Lei do Inquilinato para sublocar": (
                "Consentimento escrito e a regra dos trinta dias",
                "O artigo 13 da Lei 8.245/1991 parte de uma regra clara: cessao da locacao, sublocacao e emprestimo total ou parcial dependem de consentimento previo e escrito do locador. Uma conversa verbal ou a mera ciencia informal do proprietario nao oferecem a mesma seguranca. O pedido deve identificar a pessoa que ocupara o bem, a extensao da sublocacao e as condicoes pretendidas.\n\nOs paragrafos do mesmo artigo exigem uma leitura conjunta. A simples demora do locador, sem notificacao escrita especifica, nao autoriza presumir consentimento. Porem, o STJ decidiu no REsp 1.443.135 que, depois de o locatario notificar por escrito a pretensao ou a ocorrencia da cessao, a falta de oposicao formal no prazo legal de trinta dias pode legitimar a transferencia. Por isso, nao e correto tratar todo silencio como autorizacao nem afirmar que ele nunca produz efeito: importam o teor, a entrega e a data da notificacao."
            ),
            "Sublocar um quarto ou o imóvel inteiro: efeitos diferentes": (
                "Sublocacao parcial e total seguem a mesma exigencia de consentimento",
                "O consentimento escrito e exigido tanto para um quarto quanto para o imovel inteiro. A diferenca pratica esta no alcance da ocupacao, no valor e nas responsabilidades que precisam constar do ajuste. A Lei do Inquilinato aplica as regras da locacao a sublocacao no que couber; encerrada a locacao principal, as sublocacoes tambem se resolvem, preservado ao sublocatario eventual pedido de indenizacao contra o sublocador.\n\nA relacao nao e juridicamente invisivel para o locador. O artigo 16 preve responsabilidade subsidiaria do sublocatario pelos valores que deva ao sublocador quando este for demandado e pelos alugueis vencidos durante a lide. O locatario original, por sua vez, continua vinculado ao contrato principal enquanto nao houver cessao valida ou substituicao aceita."
            ),
            "Como formalizar o consentimento do locador por escrito": (
                "Como formalizar o pedido e preservar a prova",
                "O pedido deve ser enviado por meio que permita provar conteudo, recebimento e data. E-mail, notificacao extrajudicial ou plataforma da administradora podem cumprir essa funcao quando registram de modo inequivoco quem pretende sublocar, qual parte do imovel sera usada e por quanto tempo. Se houver concordancia expressa, um aditivo reduz a margem para disputa sobre aluguel, encargos, garantia e devolucao.\n\nSe o locador se opuser, ou se houver discussao sobre o efeito do silencio depois de notificacao regular, nao e prudente iniciar ou manter a sublocacao com base apenas em conversa informal. O contrato, a notificacao e a resposta devem ser analisados em conjunto antes de qualquer defesa em despejo ou pedido de reconhecimento da autorizacao."
            ),
        },
        "faq": [{
            "q": "O aluguel cobrado do sublocatario pode superar o aluguel principal?",
            "a": "Em regra, nao. O artigo 21 limita o aluguel da sublocacao ao da locacao; nas habitacoes coletivas multifamiliares, a soma pode chegar ao dobro, e o excesso pode ser reduzido ao limite legal.",
        }],
        "official_sources": [
            source(LEI + "#art13", "Lei 8.245/1991, arts. 13 a 16", "consentimento escrito, prazo de oposicao e efeitos da sublocacao"),
            source(LEI + "#art21", "Lei 8.245/1991, art. 21", "limites do aluguel da sublocacao"),
            source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi?ITA?dt=20180430&formato=PDF&nreg=201400616510&salvar=false&seq=1703168&tipo=0", "STJ, REsp 1.443.135/SP", "efeito do silencio apos notificacao escrita e prazo de trinta dias"),
        ],
    },
    "imob-direito-preferencia-inquilino": {
        "sections": {
            "O direito de preferência do artigo 27 da Lei do Inquilinato": (
                "Negocios que geram a preferencia do artigo 27",
                "O artigo 27 garante preferencia ao locatario na venda, promessa de venda, cessao ou promessa de cessao de direitos e dacao em pagamento. Antes de concluir um desses negocios com terceiro, o locador deve permitir que o inquilino aceite integralmente as mesmas condicoes. Nao e correto ampliar a regra para toda e qualquer alienacao onerosa: a propria lei enumera os negocios abrangidos e traz exclusoes expressas.\n\nA preferencia protege a oportunidade de contratar em igualdade, nao concede desconto nem obriga o proprietario a vender. Se a proposta do terceiro mudar em ponto relevante, como preco, entrada ou prazo, a comunicacao ao locatario tambem precisa refletir as condicoes efetivas."
            ),
            "Quando a preferência não se aplica": (
                "Exclusoes expressas do artigo 32",
                "O artigo 32 exclui perda da propriedade ou venda por decisao judicial, permuta, doacao, integralizacao de capital, cisao, fusao e incorporacao. Para contratos firmados a partir de 1º de outubro de 2001, o paragrafo unico tambem afasta, sob a condicao contratual destacada prevista na lei, a constituicao de propriedade fiduciaria e a perda ou venda decorrente da realizacao de garantia, inclusive leilao extrajudicial.\n\nHa ainda regras proprias para situacoes coletivas: se o imovel estiver totalmente sublocado, o artigo 30 coloca o sublocatario antes do locatario; se varias unidades forem alienadas em conjunto, o artigo 31 faz a preferencia incidir sobre a totalidade do negocio. Inadimplencia do aluguel, isoladamente, nao aparece nos artigos 27 a 32 como exclusao automatica da preferencia."
            ),
            "Documentos que confirmam a existência e a averbação do contrato": (
                "Contrato, notificacao e matricula cumprem funcoes diferentes",
                "O contrato vigente e a notificacao recebida provam a relacao e as condicoes oferecidas. A matricula atualizada permite conferir proprietario, onus e eventual registro da alienacao. A averbação da locacao nao e requisito para o locatario receber a oferta nem para, em tese, pedir perdas e danos, mas e indispensavel para o remedio real do artigo 33: haver o imovel para si depois de uma venda que desrespeitou a preferencia.\n\nPor isso, guardar apenas recibos de aluguel nao substitui o exame registral. Se houver interesse concreto na compra, a resposta deve aceitar integralmente a proposta dentro de trinta dias e conservar prova de que chegou ao locador."
            ),
        },
        "official_sources": [
            source(LEI + "#art27", "Lei 8.245/1991, arts. 27 a 31", "negocios abrangidos, notificacao, prazo e regras para sublocacao ou venda conjunta"),
            source(LEI + "#art32", "Lei 8.245/1991, art. 32", "hipoteses expressamente excluidas do direito de preferencia"),
        ],
    },
    "imob-preferencia-violada-adjudicacao": {
        "sections": {
            "O que o artigo 33 garante ao inquilino preterido": (
                "Perdas e danos ou aquisicao do imovel pelo artigo 33",
                "O artigo 33 oferece ao locatario preterido duas respostas diferentes. Ele pode reclamar do alienante as perdas e danos que consiga demonstrar ou, cumprindo os requisitos mais rigorosos da lei, depositar o preco e as despesas da transferencia para haver o imovel para si. A redacao usa a alternativa 'ou', mas a forma de formular pedidos principais ou subsidiarios no processo depende da estrategia e das regras processuais; nao se deve afirmar que uma escolha informal elimina automaticamente a outra.\n\nA indenizacao nao tem valor presumido. E preciso demonstrar a violacao da preferencia, o prejuizo efetivo e o nexo entre ambos. O simples fato de o preco de mercado ser maior que o valor da escritura nao transforma essa diferenca, por si so, em indenizacao certa."
            ),
            "Adjudicação em seis meses: os dois requisitos que travam o pedido": (
                "Prazo, averbacao previa e contrato com duas testemunhas",
                "Para haver o imovel, o pedido deve ser apresentado em ate seis meses contados do registro do ato de alienacao no cartorio de imoveis. Alem disso, a locacao precisa estar averbada na matricula pelo menos trinta dias antes da alienacao. O paragrafo unico exige, para a averbacao, uma via do contrato subscrita tambem por duas testemunhas.\n\nO prazo e registral: descobrir a venda tarde nao muda, por si so, o marco fixado na lei. Uma matricula atualizada e a certidao do registro sao, portanto, essenciais para calcular o tempo restante. Sem a averbacao previa, permanece em tese a pretensao obrigacional de perdas e danos, desde que haja prejuizo comprovado, mas nao o direito de tomar o imovel do adquirente."
            ),
            "Depósito do preço e das despesas de transferência": (
                "Deposito do preco e das despesas dentro da pretensao real",
                "O artigo 33 condiciona a aquisicao ao deposito do preco pago e das demais despesas do ato de transferencia. O STJ resume os requisitos de forma cumulativa: deposito, pedido no prazo de seis meses e averbacao previa da locacao assinada por duas testemunhas. O valor e o momento processual do deposito devem ser calculados a partir do registro e dos documentos do negocio, e nao de uma estimativa informal do valor de mercado.\n\nComo a falta de um requisito pode inviabilizar o remedio real, a primeira providencia e obter a matricula e os documentos da venda. A discussao sobre perdas e danos segue logica distinta e nao dispensa prova concreta do prejuizo."
            ),
        },
        "official_sources": [
            source(LEI + "#art33", "Lei 8.245/1991, art. 33", "perdas e danos, deposito, prazo registral e averbacao previa"),
            source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias-antigas/2016/2016-07-19_11-31_Locatario-e-indenizado-porque-imovel-foi-vendido-a-terceiro-no-prazo-de-preferencia.aspx", "STJ, direito de preferencia do locatario", "requisitos cumulativos para haver o imovel e distincao da reparacao obrigacional"),
        ],
    },
    "imob-locador-recusa-reparos": {
        "sections": {
            "Abatimento proporcional depois de dez dias de reparo pendente": (
                "O artigo 26 conta a duracao dos reparos, nao a espera anterior",
                "O artigo 26 trata de reparos urgentes que incumbem ao locador e que estao sendo realizados com a permanencia do locatario. Se a execucao durar mais de dez dias, nasce o direito ao abatimento proporcional do aluguel relativo ao periodo que exceder o decimo dia. A norma nao concede isencao total e nao diz que a contagem comeca no primeiro pedido ignorado antes do inicio da obra.\n\nA demora do locador em comecar um conserto que lhe incumbe pode configurar descumprimento dos deveres do artigo 22, mas esse problema exige prova e remedio proprio. Nao e seguro descontar unilateralmente qualquer valor do aluguel: a mora pode servir de fundamento para cobranca, consignacao adequada ou pedido judicial, conforme o caso."
            ),
            "Rescisão sem multa quando o reparo passa de trinta dias": (
                "Resilicao quando a execucao passa de trinta dias",
                "Se os reparos urgentes durarem mais de trinta dias, o paragrafo unico do artigo 26 permite ao locatario resilir o contrato. O marco tambem e a duracao da obra, nao qualquer periodo de silencio anterior do proprietario. A comunicacao de saida, a entrega das chaves e a prova das datas evitam que a discussao sobre o reparo se transforme em cobranca de alugueis posteriores.\n\nQuando nao ha obra em andamento, mas omissao grave do locador, pode haver pretensao de exigir cumprimento ou resolver o contrato por inadimplemento, com base no artigo 475 do Codigo Civil e nos deveres do artigo 22. Essa conclusao depende da importancia do defeito, da notificacao e da oportunidade efetiva de conserto."
            ),
            "Obrigação de fazer: pedir a execução judicial do conserto": (
                "Cumprimento, tutela urgente e pagamento sem mora artificial",
                "Se o objetivo e permanecer no imovel, e possivel pedir o cumprimento da obrigacao de reparar e, quando houver probabilidade do direito e perigo de dano, tutela de urgencia. Fotos, laudo, notificacao recebida e orcamentos ajudam a demonstrar a causa e a urgencia. A medida exata depende de quem responde pelo defeito: locador, condominio, vizinho ou o proprio locatario.\n\nEnquanto nao houver acordo seguro ou decisao, simplesmente parar de pagar ou reduzir o aluguel por conta propria cria risco de mora e despejo. A estrategia precisa separar o valor incontroverso do aluguel, o custo do reparo e o pedido de abatimento ou indenizacao."
            ),
        },
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22", "deveres do locador quanto ao estado, forma e defeitos anteriores do imovel"),
            source(LEI + "#art26", "Lei 8.245/1991, art. 26", "abatimento proporcional apos dez dias de reparos e resilicao apos trinta"),
            source(CC + "#art475", "Codigo Civil, art. 475", "cumprimento ou resolucao do contrato por inadimplemento"),
        ],
    },
    "imob-obras-imovel-abatimento": {
        "sections": {
            "Isenção total do aluguel até dez dias de obra": (
                "Ate dez dias nao ha abatimento automatico pelo artigo 26",
                "O artigo 26 nao cria isencao de aluguel. Se os reparos urgentes durarem ate dez dias, esse dispositivo nao concede abatimento automatico; se ultrapassarem esse periodo, o desconto e proporcional apenas ao tempo excedente. A extensao concreta do abatimento pode depender do impacto da obra e da prova produzida, mas o texto legal nao transforma o periodo excedente em gratuidade total."
            ),
            "Abatimento proporcional depois do décimo dia": (
                "Abatimento proporcional ao periodo excedente",
                "Superado o decimo dia de reparos urgentes a cargo do locador, o locatario tem direito ao abatimento proporcional previsto no paragrafo unico do artigo 26. A contagem considera a duracao efetiva da execucao. Inicio, interrupcoes, termino e areas afetadas devem ser documentados para permitir um calculo verificavel.\n\nA lei garante o direito, mas nao autoriza criar unilateralmente um percentual sem base e deixar de pagar o restante. Quando as partes nao concordam, e importante manter prova da proposta, pagar a parcela incontroversa pela via adequada e buscar a definicao do valor sem fabricar mora locaticia."
            ),
            "Rescisão quando a obra passa de trinta dias": (
                "Resilicao quando os reparos passam de trinta dias",
                "Se os reparos urgentes durarem mais de trinta dias, o locatario pode resilir o contrato. A regra nao exige que a obra atinja cozinha ou banheiro, nem limita o direito a um comodo especifico; exige a duracao legal e que se trate de reparo urgente cuja realizacao incumba ao locador. A entrega das chaves e a comunicacao do fundamento precisam ser documentadas."
            ),
        },
        "official_sources": [
            source(LEI + "#art26", "Lei 8.245/1991, art. 26", "abatimento proporcional e resilicao durante reparos urgentes"),
            source(LEI + "#art9", "Lei 8.245/1991, art. 9º, IV", "reparacoes urgentes determinadas pelo poder publico incompatíveis com a permanencia"),
        ],
    },
    "imob-benfeitorias-necessarias-clausula": {
        "sections": {
            "Cláusula de renúncia: quando o contrato afasta a indenização": (
                "A validade da renuncia segundo a Sumula 335 do STJ",
                "A Sumula 335 do STJ afirma que, nos contratos de locacao, e valida a clausula de renuncia a indenizacao das benfeitorias e ao direito de retencao. A jurisprudencia que originou o enunciado tambem afasta a aplicacao automatica do Codigo de Defesa do Consumidor a locacao urbana regida por lei especifica. Assim, nao e correto sugerir que a clausula cai apenas por estar em contrato padrao ou sem destaque.\n\nIsso nao permite ampliar a renuncia para qualquer obra. O STJ decidiu no REsp 1.931.087 que uma clausula sobre benfeitorias e adaptacoes nao se estende automaticamente a acessao, como uma nova construcao, porque renuncias sao interpretadas estritamente. E preciso classificar o que foi feito e ler a redacao exata do contrato."
            ),
            "Quando vale contestar a cláusula de renúncia": (
                "O que ainda pode ser discutido apesar da renuncia",
                "A discussao util nao parte de uma alegacao generica de abusividade. Ela verifica se a clausula existe e alcanca indenizacao, retencao ou ambas; se a obra e benfeitoria ou acessao; se houve autorizacao; e se a conduta do locador criou uma pretensao distinta, como descumprimento contratual ou enriquecimento sem causa em circunstancias comprovadas.\n\nMesmo sem direito de retencao, segurar as chaves como pressao pode prolongar aluguel e encargos. Notas, autorizacoes e fotos devem ser analisadas antes da devolucao, separando eventual credito pela obra do dever de restituir o imovel."
            ),
        },
        "official_sources": [
            source(LEI + "#art35", "Lei 8.245/1991, art. 35", "indenizacao e retencao, salvo disposicao contratual em contrario"),
            source("https://arquivocidadao.stj.jus.br/index.php/sumula-335-2?listLimit=100&sf_culture=pt&sort=referenceCode&sortDir=asc", "STJ, Sumula 335", "validade da clausula de renuncia a benfeitorias e retencao"),
            source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2024/27022024-Clausula-de-renuncia-as-benfeitorias-em-contrato-de-aluguel-nao-se-estende-as-acessoes.aspx", "STJ, REsp 1.931.087/SP", "renuncia a benfeitorias nao se estende automaticamente a acessoes"),
        ],
    },
    "imob-benfeitorias-retencao-verbete": {
        "sections": {
            "Indenização e direito de retenção conforme o Código Civil": (
                "Como a classificacao funciona na locacao",
                "O artigo 1.219 do Codigo Civil regula o possuidor de boa-fe em geral, mas a locacao urbana tem regra especifica. Pelo artigo 35 da Lei 8.245/1991, as benfeitorias necessarias feitas pelo locatario sao indenizaveis mesmo sem autorizacao e as uteis somente quando autorizadas, sempre ressalvada disposicao contratual em contrario. A clausula de renuncia a indenizacao e retencao e admitida pela Sumula 335 do STJ.\n\nAs voluptuarias recebem disciplina propria no artigo 36: nao sao indenizaveis, mas podem ser retiradas no fim da locacao se a retirada nao afetar a estrutura nem a substancia do imovel. Portanto, classificacao, autorizacao e contrato precisam ser lidos juntos; a regra geral do possuidor nao substitui a lei locaticia."
            ),
        },
        "official_sources": [
            source(CC + "#art96", "Codigo Civil, art. 96", "classificacao das benfeitorias necessarias, uteis e voluptuarias"),
            source(LEI + "#art35", "Lei 8.245/1991, arts. 35 e 36", "indenizacao, retencao e retirada de benfeitorias na locacao"),
            source("https://arquivocidadao.stj.jus.br/index.php/sumula-335-2?listLimit=100&sf_culture=pt&sort=referenceCode&sortDir=asc", "STJ, Sumula 335", "validade da renuncia contratual a indenizacao e retencao"),
        ],
    },
    "imob-reforma-sem-autorizacao": {
        "sections": {
            "Quando a reforma pequena não configura infração": (
                "Reversibilidade nao substitui o consentimento escrito",
                "A lei nao cria uma lista de pequenas mudancas dispensadas de autorizacao. Trocar um item removivel pode nao modificar a forma interna ou externa, mas pintura, furos, instalacoes e acabamentos dependem do contrato e do efeito concreto. Ser barato ou reversivel reduz o dano potencial, mas nao transforma automaticamente a intervencao em conduta autorizada.\n\nQuando houver duvida, a resposta segura e pedir consentimento escrito antes. O documento deve indicar o que sera alterado, quem pagara, se havera recomposicao na saida e se a obra sera indenizada. Silencio ou tolerancia informal podem gerar uma disputa probatoria que um aditivo simples evitaria."
            ),
            "Como reagir a uma notificação de infração por reforma": (
                "Regularizacao posterior nao apaga automaticamente a infracao",
                "Depois da notificacao, pode haver espaco para o locador autorizar a permanencia da obra ou ajustar sua reversao. Isso depende de concordancia efetiva; a utilidade da reforma nao obriga o proprietario a aceita-la e, pelo artigo 35, benfeitoria util so e indenizavel quando autorizada, salvo outro ajuste contratual.\n\nFotos, projetos, notas e mensagens ajudam a distinguir mudanca superficial, benfeitoria e dano estrutural. Se houver risco de despejo, a resposta precisa enfrentar a clausula e o artigo 23, VI, sem prometer que uma melhoria valorizada eliminara a infracao."
            ),
        },
        "official_sources": [
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, VI", "consentimento previo e escrito para modificar a forma do imovel"),
            source(LEI + "#art35", "Lei 8.245/1991, art. 35", "autorizacao exigida para indenizacao de benfeitoria util"),
            source(LEI + "#art9", "Lei 8.245/1991, art. 9º, II", "infracao legal ou contratual como causa de desfazimento"),
        ],
    },
    "imob-animal-imovel-alugado": {
        "title": "Contrato de aluguel proíbe animal: como analisar a cláusula",
        "meta_description": "Entenda a diferença entre proibição de animal no contrato de locação e na convenção de condomínio, e quais fatos precisam ser avaliados no caso concreto.",
        "h1": "A cláusula do aluguel pode proibir animal no imóvel?",
        "sections": {
            "A tensão entre liberdade contratual e função social da moradia": (
                "A clausula locaticia nao tem resposta automatica",
                "Em locacao privada, a analise parte do contrato, da boa-fe e dos limites legais ao exercicio de direitos. O artigo 421 do Codigo Civil nao elimina a liberdade contratual; ele a situa nos limites da funcao social, enquanto os artigos 421-A e 422 reforcam intervencao excepcional, revisao limitada e deveres de probidade e boa-fe. Por isso, nao se pode afirmar de antemao que toda proibicao e valida nem que a moradia torna toda restricao nula.\n\nPesam a redacao da clausula, o tipo de imovel, a justificativa apresentada, a existencia de dano, risco, barulho ou violacao da convencao condominial e a conduta das partes durante o contrato. A resposta e probatoria e contratual, nao depende apenas do porte do animal."
            ),
            "Como os tribunais têm tratado animais de pequeno porte e inofensivos": (
                "O precedente do STJ sobre condominio nao decide sozinho a locacao",
                "No REsp 1.783.076, o STJ afastou proibicao generica de animais em unidades autonomas contida em convencao de condominio quando ausentes risco a seguranca, higiene, saude e sossego. O caso trata da relacao condominial e do direito sobre a unidade autonoma; ele nao declarou, de forma geral, nulas as clausulas de contratos de aluguel entre locador e locatario.\n\nUsar esse precedente exige explicar a diferenca. Ele ajuda a avaliar uma regra do condominio, mas a clausula locaticia ainda precisa ser examinada a luz do contrato e dos fatos. Porte pequeno e ausencia de reclamacoes sao elementos relevantes, nao uma autorizacao judicial automatica."
            ),
            "Quando a proibição contratual ainda prevalece": (
                "Dano, sossego, higiene e regras do condominio",
                "Dano comprovado ao imovel, risco, perturbacao reiterada, falta de higiene ou descumprimento de regra condominial valida fortalecem a exigencia de cessar a conduta e podem caracterizar infracao. Especie ou tamanho, isoladamente, nao substituem essa prova, embora as caracteristicas do animal e do espaco sejam relevantes para medir risco e adequacao.\n\nAntes de responder a uma notificacao, devem ser reunidos contrato, convencao, regulamento, registros de reclamacoes e provas sobre a convivencia. A defesa nao deve prometer resultado com base apenas na frase 'animal de pequeno porte', nem ignorar uma clausula aceita sem analisar sua validade concreta."
            ),
        },
        "official_sources": [
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, II e X", "uso convencionado do imovel e cumprimento das regras condominiais"),
            source(CC + "#art421", "Codigo Civil, arts. 421, 421-A e 422", "funcao social, intervencao contratual excepcional e boa-fe"),
            source("https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&b=INFJ&operador=mesmo&p=true&processo=1783076&thesaurus=JURIDICO", "STJ, Informativo 649, REsp 1.783.076/DF", "proibicao generica de animais em convencao de condominio"),
        ],
    },
    "imob-sem-laudo-entrada": {
        "sections": {
            "Sem vistoria inicial, quem tem o ônus da prova": (
                "A falta do laudo nao inverte o onus automaticamente",
                "Sem laudo de entrada, cada parte continua sujeita a distribuicao do artigo 373 do CPC. Quem cobra indenizacao por dano deve provar o fato constitutivo de seu direito; quem alega pagamento, desgaste normal ou outro fato impeditivo, modificativo ou extintivo assume o onus correspondente. A posicao processual tambem importa: uma acao do locador por reparos nao tem a mesma estrutura de uma acao do locatario para recuperar caucao.\n\nO artigo 22, V, obriga o locador a fornecer descricao minuciosa do estado do imovel caso o locatario a solicite. Nao e um dever incondicional de produzir laudo em toda locacao. A ausencia do documento reduz a qualidade da comparacao para ambos, mas nao cria sozinha presuncao absoluta contra o proprietario."
            ),
            "O artigo 373 do Código de Processo Civil aplicado à disputa locatícia": (
                "Fato constitutivo, defesa e distribuicao dinamica",
                "Se o locador afirma que o locatario causou uma avaria e pede o custo do reparo, em regra precisa demonstrar o estado anterior, o dano posterior, a autoria ou nexo e o valor. O locatario pode provar que o defeito ja existia, decorreu de uso normal ou foi causado por terceiro. Em situacoes justificadas, o juiz pode distribuir o onus de modo diverso por decisao fundamentada, dando oportunidade de a parte cumprir o encargo.\n\nLogo, a resposta correta nao e dizer que a imobiliaria sempre perde por nao ter laudo. Fotos do anuncio, mensagens da entrada, ordens de servico e testemunhas podem suprir parte da lacuna, e a decisao dependera do conjunto probatorio."
            ),
            "Presunção que favorece o inquilino na ausência de registro": (
                "Nao existe presuncao geral de imovel sem danos",
                "A falta de registro inicial pode tornar insuficiente uma cobranca baseada apenas em vistoria final, mas nao prova que todo defeito surgiu antes da locacao. Da mesma forma, a assinatura de um laudo final nao substitui a comparacao com o estado de entrada nem elimina a ressalva legal do desgaste normal.\n\nA contestacao deve identificar item por item: qual era o estado conhecido, qual mudanca ocorreu, se ela e compativel com o tempo de uso e qual documento sustenta a conclusao. Essa analise e mais defensavel do que invocar uma suposta presuncao automatica que a lei nao estabelece."
            ),
        },
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, V", "descricao minuciosa do imovel quando solicitada pelo locatario"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, III e V", "devolucao com ressalva do uso normal e reparacao de danos causados"),
            source("https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art373", "Codigo de Processo Civil, art. 373", "distribuicao do onus da prova e possibilidade de decisao fundamentada diversa"),
        ],
    },
    "imob-locador-recusa-chaves": {
        "title": "Locador não aceita as chaves: como fixar o fim da locação",
        "meta_description": "Veja como documentar a recusa injustificada das chaves, quando cabe consignação judicial e por que avarias devem ser discutidas separadamente.",
        "h1": "O locador recusou as chaves: o que fazer?",
        "sections": {
            "Consignação das chaves como saída para travar o aluguel corrente": (
                "Consignacao judicial diante da recusa injustificada",
                "Quando a devolucao regular e recusada sem causa legitima, a consignacao judicial das chaves permite submeter a entrega ao Judiciario e documentar o marco pretendido para a retransmissao da posse. Antes disso, e importante provar que o imovel foi desocupado, que o aviso exigivel foi enviado e que houve oferta real das chaves em data e local definidos.\n\nA forma de terminar o contrato precisa ser observada. Na locacao por prazo indeterminado, o artigo 6º exige aviso escrito com antecedencia de trinta dias, salvo pagamento correspondente; em contrato por prazo determinado, a devolucao antecipada pode gerar a multa proporcional do artigo 4º. A recusa nao apaga essas obrigacoes, mas tambem nao autoriza o locador a prolongar artificialmente o aluguel."
            ),
            "O artigo 67 da Lei do Inquilinato e a ação de consignação": (
                "O artigo 67 trata de dinheiro, nao de chaves",
                "O artigo 67 disciplina a consignacao de alugueis e acessorios, com deposito de quantias e regras proprias. Ele nao e o fundamento textual especifico de uma 'acao de consignacao de chaves'. A possibilidade de consignar as chaves diante da recusa aparece na jurisprudencia do STJ sobre retransmissao da posse e encerramento da locacao.\n\nNo REsp 2.089.739, o tribunal registrou que, cumprido o aviso escrito na locacao por prazo indeterminado, cabe entregar as chaves e, se o locador recusar, promover a consignacao judicial. Em 2026, no REsp 2.220.656, o STJ reafirmou que supostas avarias devem ser discutidas em via propria e nao justificam condicionar o recebimento das chaves a concordancia com laudo."
            ),
            "Efeitos da consignação sobre o fim da responsabilidade do inquilino": (
                "A data relevante depende da oferta, da recusa e da prova",
                "A consignacao busca reconhecer a eficacia da devolucao apesar da resistencia do credor. Nao e correto prometer que qualquer deposito de chaves interrompe automaticamente todo encargo: o juiz examina desocupacao, aviso, oferta, motivo da recusa e regularidade do procedimento. Quando a recusa e ilegítima, a conduta do locador nao deve gerar alugueis artificiais, sem prejuizo da multa proporcional ou de valores anteriores efetivamente devidos.\n\nDanos de vistoria permanecem discutiveis em cobranca propria. O recebimento das chaves nao equivale a quitar avarias, e o locatario nao precisa assinar concordancia com um laudo como condicao para devolver a posse."
            ),
        },
        "official_sources": [
            source(LEI + "#art4", "Lei 8.245/1991, arts. 4º e 6º", "devolucao antecipada e aviso na locacao por prazo indeterminado"),
            source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/16012026-Fiador-fica-liberado-dos-alugueis-se-o-locador-se-recusa-a-receber-as-chaves.aspx", "STJ, REsp 2.220.656/RJ", "recusa condicionada a laudo e separacao entre entrega das chaves e avarias"),
            source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20231215&formato=PDF&nreg=202302759736&salvar=false&seq=2395831&tipo=0", "STJ, REsp 2.089.739/MG", "aviso escrito e consignacao judicial se houver recusa das chaves"),
        ],
    },
    "imob-entrega-chaves-fim-aluguel": {
        "sections": {
            "Quando o aluguel continua correndo mesmo após a saída": (
                "Saida fisica, devolucao e multa nao sao a mesma coisa",
                "Se o locatario apenas retira os moveis, mas conserva as chaves e nao oferece a devolucao regular, a posse nao foi retransmitida e os alugueis podem continuar. A situacao muda quando as chaves sao efetivamente entregues ou quando o locador as recusa injustificadamente e a devolucao e formalizada pela via adequada.\n\nEm contrato por prazo determinado, a saida antecipada pode gerar a multa proporcional do artigo 4º. Isso nao significa cobrar, ao mesmo tempo e pelo mesmo periodo, todos os alugueis futuros como se a posse permanecesse com o locatario. Aluguel corrente, multa de rescisao e reparacao de danos sao verbas distintas e precisam ser discriminadas."
            ),
            "Vistoria e reparos pendentes não prorrogam o aluguel automaticamente": (
                "Avarias nao autorizam condicionar o recebimento das chaves",
                "O STJ decidiu no REsp 2.220.656 que o fim da locacao por prazo indeterminado nao pode ser impedido pela exigencia de concordancia com laudo de vistoria. Eventuais danos devem ser discutidos em via propria. Assim, o locador pode receber as chaves com ressalva e cobrar o que provar, mas nao deve usar a entrega como instrumento para obter confissao de divida.\n\nA conclusao depende de devolucao regular. O locatario deve cumprir o aviso aplicavel, desocupar o bem e provar a oferta das chaves; abandonar o imovel ou apenas informar que saiu nao produz a mesma seguranca juridica."
            ),
        },
        "official_sources": [
            source(LEI + "#art4", "Lei 8.245/1991, arts. 4º, 6º e 23, III", "multa proporcional, aviso e dever de restituir o imovel"),
            source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/16012026-Fiador-fica-liberado-dos-alugueis-se-o-locador-se-recusa-a-receber-as-chaves.aspx", "STJ, REsp 2.220.656/RJ", "entrega das chaves nao pode ser condicionada a concordancia com avarias"),
        ],
    },
    "imob-contas-consumo-inquilino-anterior": {
        "title": "Dívida de água ou luz do morador anterior: quem responde",
        "meta_description": "Entenda por que débitos de consumo do antigo usuário não podem ser transferidos ao novo morador e como pedir a troca de titularidade com prova da posse.",
        "h1": "O novo inquilino responde pela conta antiga de água ou luz?",
        "sections": {
            "Dívida de consumo é obrigação pessoal, não do imóvel": (
                "Agua e energia: divida ligada ao usuario do periodo",
                "O STJ considera pessoais os debitos por agua, esgoto e energia consumidos por ocupante anterior: a obrigacao nasce da prestacao ao usuario, nao acompanha automaticamente a matricula do imovel. O novo locatario deve responder pelo consumo do seu periodo e manter a titularidade atualizada, mas nao pode ser obrigado a assumir conta de pessoa diversa apenas porque o medidor e o mesmo.\n\nEssa regra nao deve ser estendida sem exame a todo servico possivel. Para energia ha regulacao nacional da ANEEL; no saneamento, procedimentos administrativos podem variar conforme entidade reguladora e prestador local, embora a jurisprudencia do STJ afaste a transferencia do debito pretérito ao novo usuario."
            ),
            "Por que a concessionária não pode negar religação por débito de terceiro": (
                "Troca de titularidade da energia segundo a ANEEL",
                "A orientacao oficial da ANEEL sobre a Resolucao Normativa 1.000/2021 diz que a distribuidora nao pode cobrar divida do morador anterior nem exigir assuncao ou confissao desse debito como condicao para alterar a titularidade. O novo ocupante deve apresentar identificacao e documento datado que demonstre propriedade ou posse, como o contrato de locacao.\n\nIsso nao elimina outras pendencias legitimas do proprio solicitante nem requisitos tecnicos da instalacao. A negativa precisa ser obtida por escrito para distinguir divida de terceiro, falta de documento, debito do proprio consumidor ou problema de seguranca na unidade."
            ),
            "Quando vale reclamar na agência reguladora": (
                "Canais mudam conforme energia ou saneamento",
                "Para energia eletrica, depois do protocolo na distribuidora e da ouvidoria, a reclamacao pode seguir aos canais da ANEEL. Para agua e esgoto, a entidade competente pode ser municipal, estadual, intermunicipal ou distrital; e preciso identificar quem regula o prestador local. Protocolos, contrato e prova da data de entrada permitem demonstrar que o debito e anterior.\n\nIndenizacao nao e automatica. Ela depende de ilicitude, dano e nexo, especialmente quando houve privacao indevida e prolongada de servico essencial apesar da documentacao correta. A prioridade pratica e obter a titularidade e o restabelecimento, preservando prova para eventual reparacao."
            ),
        },
        "official_sources": [
            source("https://www.gov.br/aneel/pt-br/consumidores/como-resolver", "ANEEL, troca de titularidade", "divida de morador anterior nao pode condicionar a alteracao de titularidade de energia"),
            source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20191210&formato=PDF&nreg=201902280881&salvar=false&seq=1899333&tipo=0", "STJ, AREsp 1.557.116/MG", "debito de agua do antigo ocupante e obrigacao pessoal"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, VIII", "despesas de consumo devidas pelo locatario durante a ocupacao"),
        ],
    },
    "imob-taxa-contrato-cadastro": {
        "sections": {
            "Despesas de intermediação são do locador, não do candidato a inquilino": (
                "O artigo 22, VII inclui cadastro e idoneidade",
                "O artigo 22, VII, da Lei 8.245/1991 atribui ao locador as taxas de administracao imobiliaria e de intermediacao. O texto e expresso ao incluir entre elas as despesas necessarias para aferir a idoneidade do pretendente ou de seu fiador. Portanto, analise cadastral e consulta de credito usadas para selecionar o candidato nao se tornam cobranca legitima contra ele apenas porque foram executadas por empresa terceirizada.\n\nO nome dado a tarifa nao decide sua validade. E preciso verificar qual servico foi prestado, quem o contratou e se ele integra a atividade de administracao ou intermediacao feita em favor do proprietario."
            ),
            "Taxas que costumam ser cobradas indevidamente do candidato": (
                "Contrato, cadastro, credito e vistoria devem ser classificados",
                "Elaboracao do contrato pela administradora, cadastro, afericao de idoneidade do candidato ou fiador e outros atos necessarios a intermediacao entram na obrigacao legal do locador. Uma cobranca separada nao muda essa distribuicao. A vistoria de entrada tambem exige cautela: se integra a administracao e documenta o bem do proprietario, nao deve ser repassada ao candidato por rotulo genérico.\n\nJa despesas que a lei ou o contrato validamente atribuem ao locatario, como o premio do seguro de fianca previsto no artigo 23, XI, seguem disciplina diferente. A cobranca precisa ter fundamento identificavel, e nao apenas aparecer numa tabela da imobiliaria."
            ),
            "Quando alguma cobrança ao inquilino é legítima": (
                "O que pode caber ao locatario",
                "O locatario paga aluguel e encargos legal ou contratualmente exigiveis, despesas de consumo, despesas ordinarias de condominio quando comprovadas e o premio do seguro de fianca, entre outros itens previstos nos artigos 23 e seguintes. Isso nao autoriza transferir a ele o custo de selecionar o pretendente ou o fiador, que o artigo 22, VII colocou expressamente com o locador.\n\nUm servico verdadeiramente autonomo, solicitado pelo proprio candidato e sem ser condicao para participar da locacao, exige analise do contrato e da utilidade entregue. Chamar a consulta obrigatoria de 'servico opcional' nao basta para afastar a lei."
            ),
        },
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, VII", "administracao, intermediacao e afericao de idoneidade a cargo do locador"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, XI", "premio do seguro de fianca a cargo do locatario"),
            source(LEI + "#art45", "Lei 8.245/1991, art. 45", "nulidade de clausulas que elidam os objetivos da lei"),
        ],
    },
    "imob-imobiliaria-nao-repassa-alugueis": {
        "sections": {
            "A administração do aluguel como mandato do artigo 653 do Código Civil": (
                "Contrato de administracao e poderes de mandato",
                "O artigo 653 do Codigo Civil define mandato como o recebimento de poderes para, em nome de outra pessoa, praticar atos ou administrar interesses. Um contrato de administracao imobiliaria costuma reunir prestacao de servicos e poderes de mandato, mas a qualificacao e a extensao desses poderes dependem do instrumento. E preciso conferir se a imobiliaria recebe em nome do proprietario, quais descontos pode fazer e em que prazo deve repassar.\n\nQuando recebe aluguel por conta do dono, a administradora nao pode tratar o valor como receita propria. Contrato, extrato do locatario, demonstrativo mensal e conta de destino permitem reconstruir o fluxo e separar remuneracao autorizada de retencao sem fundamento."
            ),
            "Dever de prestar contas e o artigo 667": (
                "Diligencia no artigo 667 e contas no artigo 668",
                "O artigo 667 exige do mandatario diligencia habitual e reparacao do prejuizo causado por culpa. O dever de dar contas da gerencia e transferir ao mandante as vantagens recebidas esta no artigo 668, nao no 667. Se valores que deveriam ser entregues forem empregados em proveito proprio, o artigo 670 ainda preve juros desde o abuso.\n\nA prestacao de contas deve permitir conferir receitas, comissao, tributos, reparos autorizados e saldo. Um total sem documentos nao cumpre adequadamente a funcao de demonstrar como cada aluguel foi administrado."
            ),
            "Retenção de repasse: quando configura inadimplemento do mandato": (
                "Atraso, compensacao autorizada e uso indevido do valor",
                "O prazo de repasse vem primeiro do contrato. Um atraso pode decorrer de data bancaria, contestacao do pagamento ou desconto autorizado; retencao reiterada, sem demonstrativo ou fora dos poderes recebidos indica inadimplemento. O artigo 669 impede o mandatario de compensar prejuizos que causou com vantagens obtidas em outro ponto da gestao.\n\nAntes de concluir que houve apropriacao, devem ser exigidos extratos e documentos. Se a administradora recebeu e usou o dinheiro em proveito proprio, o artigo 670 disciplina juros, sem excluir cobranca do principal e perdas comprovadas. Eventual repercussao penal depende de fatos e elemento subjetivo e nao deve ser presumida pela simples mora contratual."
            ),
        },
        "official_sources": [
            source(CC + "#art653", "Codigo Civil, arts. 653 e 667", "conceito de mandato e dever de diligencia do mandatario"),
            source(CC + "#art668", "Codigo Civil, arts. 668 a 670", "prestacao de contas, vedacao de compensacao e juros pelo uso de valores"),
        ],
    },
    "imob-visitas-imovel-a-venda": {
        "sections": {
            "Horários e frequência razoáveis: onde termina a tolerância": (
                "A lei exige combinacao, mas nao fixa agenda padrao",
                "O artigo 23, IX, nao define numero de visitas, dias da semana ou antecedencia minima. Ele exige combinacao previa de dia e hora para a vistoria e vincula a visita de terceiros interessados a venda prevista no artigo 27. Por isso, nenhuma das partes pode impor sozinha uma agenda ilimitada nem bloquear, de forma sistematica, toda oportunidade de exame.\n\nA solucao pratica e registrar janelas compativeis com a rotina do morador, duracao estimada e identificacao de quem entrara. Trabalho, saude, criancas e seguranca podem justificar ajustes concretos, mas nao criam uma dispensa geral do dever legal. Da mesma forma, urgencia comercial do corretor nao autoriza acesso sem consentimento."
            ),
            "Combinação prévia: por que o aviso não pode ser dispensado": (
                "Aviso unilateral nao equivale sempre a combinacao",
                "Mandar uma mensagem poucos minutos antes nao prova que dia e hora foram combinados. O locatario pode recusar aquele ingresso e oferecer alternativa proxima, preservando por escrito que nao se opoe as visitas. O contexto importa: um horario ja pactuado pode exigir apenas confirmacao, enquanto uma visita nova precisa de concordancia real.\n\nO historico de propostas e respostas demonstra se houve cooperacao ou obstrucao. Essa prova e mais util do que adotar uma regra artificial de tantas horas de antecedencia que a Lei do Inquilinato nao estabeleceu."
            ),
            "Quando a insistência do locador vira abuso": (
                "A venda nao suspende o uso pacifico nem a inviolabilidade da casa",
                "A garantia de uso pacifico do artigo 22, II, continua durante a venda. Entrar com copia das chaves sem consentimento do morador nao se confunde com visita combinada e pode violar a posse e a inviolabilidade domiciliar. A qualificacao civil ou penal depende das circunstancias e dos elementos de cada conduta; nao se deve prometer que todo desencontro de agenda produz dano moral ou crime.\n\nRepeticao, ameaca, ingresso clandestino ou retirada de objetos aumentam a gravidade e devem ser documentados. Em emergencia real, como perigo imediato ou necessidade de socorro, a analise e diferente da simples conveniencia de mostrar o imovel."
            ),
        },
        "official_sources": [
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, IX", "vistoria com combinacao previa e visita de interessados na compra"),
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, II", "garantia de uso pacifico durante a locacao"),
            source("https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm#art5xi", "Constituicao Federal, art. 5º, XI", "inviolabilidade da casa e excecoes constitucionais"),
        ],
    },
    "imob-infiltracao-quem-paga-reparo": {
        "sections": {
            "Reparo estrutural e conservação simples: como separar as duas coisas": (
                "A causa do vazamento decide a responsabilidade",
                "A palavra 'infiltracao' nao identifica sozinha quem paga. Falha anterior a locacao ou defeito da estrutura que o locador deve manter aponta para os artigos 22, I, III e IV. Dano provocado pelo locatario, seus familiares, visitantes ou prepostos entra no artigo 23, V. Se a origem estiver em area comum ou em outra unidade, condominio ou vizinho podem ser os responsaveis diretos, sem eliminar a necessidade de o locador garantir ao inquilino um imovel apto ao uso.\n\nRejunte, silicone e ventilacao nao sao automaticamente 'manutencao do inquilino'. E preciso provar desgaste, causa, dever contratual e conduta. Umidade por falha de impermeabilizacao nao muda de natureza porque aparece no banheiro; mofo por falta de ventilacao tambem nao pode ser imputado sem examinar as condicoes do ambiente."
            ),
            "Como notificar o locador e registrar o problema": (
                "Comunicacao imediata e preservacao da causa",
                "O artigo 23, IV, obriga o locatario a comunicar imediatamente dano ou defeito cuja reparacao incumba ao locador. A notificacao deve mostrar data, local, evolucao e medidas urgentes tomadas para evitar agravamento. Fotos, videos e laudo ajudam, mas o locatario deve evitar quebrar paredes ou alterar a instalacao sem autorizacao, salvo providencia emergencial justificavel.\n\nO recebimento da mensagem prova ciencia; a constituicao em mora e seus efeitos dependem de a obrigacao estar vencida, do prazo concedido e da urgencia. Por isso, e melhor formular pedido objetivo de vistoria e reparo do que declarar, sem base, que qualquer mensagem ja autoriza descontar aluguel."
            ),
            "Quando o próprio inquilino responde pelo dano": (
                "Dano causado pelo ocupante e dever de reparacao",
                "O artigo 23, V, manda o locatario reparar imediatamente os danos provocados por si, dependentes, familiares, visitantes ou prepostos. Entupimento por descarte inadequado, perfuracao de tubulacao durante obra ou vazamento de equipamento instalado de modo incorreto sao exemplos possiveis, desde que o nexo seja demonstrado.\n\nQuando a origem e duvidosa, laudo tecnico e acesso coordenado aos pontos afetados evitam agravamento. A vistoria deve distinguir causa, dano secundario e responsabilidade: uma falha da unidade superior pode molhar a parede do locatario sem ter sido criada nem pelo inquilino nem pelo proprietario daquela unidade locada."
            ),
        },
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, I, III e IV", "estado de uso, manutencao da forma e defeitos anteriores"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, IV e V", "comunicacao do defeito e reparacao de danos causados pelo locatario"),
        ],
    },
    "imob-vicio-oculto-imovel-alugado": {
        "title": "Defeito anterior no imóvel alugado: quais são os direitos",
        "meta_description": "Saiba como provar que um defeito já existia antes da locação e quando discutir reparo, abatimento, resolução do contrato ou indenização.",
        "h1": "O imóvel alugado tinha um defeito anterior: como agir?",
        "sections": {
            "A responsabilidade do locador por defeitos anteriores à locação": (
                "Responsabilidade expressa no artigo 22, IV",
                "O artigo 22, IV, responsabiliza o locador pelos vicios ou defeitos anteriores a locacao. A regra nao depende de provar fraude: desconhecimento do proprietario nao transfere automaticamente ao locatario o custo de um problema que ja existia. O artigo 22, I, tambem exige a entrega do imovel em estado de servir ao uso contratado.\n\nA gravidade e a destinacao importam. Um defeito estetico informado e aceito tem efeito diferente de instalacao eletrica insegura escondida ou infiltracao que impede a moradia. Contrato, vistoria e mensagens precisam mostrar o que foi revelado e qual uso foi prometido."
            ),
            "Rescisão, abatimento ou indenização: as três saídas possíveis": (
                "Reparo, abatimento, resolucao e perdas comprovadas",
                "Nao existe um cardapio automatico de tres remedios com o mesmo requisito. O locatario pode exigir que o locador cumpra seus deveres e, se houver inadimplemento relevante, discutir resolucao do contrato com perdas e danos pelo artigo 475 do Codigo Civil. Durante reparos urgentes efetivamente realizados, o artigo 26 da Lei do Inquilinato preve abatimento proporcional depois do decimo dia e resilicao se durarem mais de trinta.\n\nIndenizacao por mudanca, bens danificados ou outro prejuizo exige prova do dano e do nexo. Abatimento fora da hipotese objetiva do artigo 26 tambem precisa ser fundamentado no comprometimento do uso e nao deve ser descontado unilateralmente sem acordo ou via juridica adequada."
            ),
            "Quando o inquilino perde o direito de reclamar": (
                "Defeito conhecido nao apaga todo dever do locador",
                "Se a condicao foi claramente informada, era visivel e foi aceita como parte do estado contratado, fica mais dificil chama-la depois de vicio oculto. Isso nao significa renuncia irrestrita a seguranca, habitabilidade ou reparos que a lei imponha ao locador, nem autoriza esconder defeito relevante.\n\nTambem pesa a comunicacao imediata: continuar usando o bem por longo periodo sem registrar o problema pode dificultar a prova da anterioridade e permitir agravamento. A analise deve separar defeito preexistente, desgaste normal, dano causado durante a ocupacao e risco conhecido na contratacao."
            ),
        },
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, I e IV", "entrega apta ao uso e responsabilidade por defeitos anteriores"),
            source(LEI + "#art26", "Lei 8.245/1991, art. 26", "efeitos da duracao de reparos urgentes a cargo do locador"),
            source(CC + "#art475", "Codigo Civil, art. 475", "cumprimento ou resolucao por inadimplemento e perdas comprovadas"),
        ],
    },
    "imob-imovel-interditado-defesa-civil": {
        "sections": {
            "Interdição por risco estrutural: por que a locação se desfaz sem multa": (
                "A interdicao exige formalizacao do fim da locacao",
                "Uma ordem que proibe a ocupacao pode tornar impossivel o uso residencial e sustentar o desfazimento sem a multa de uma saida voluntaria. Isso nao significa que o contrato desaparece sem comunicacao, devolucao das chaves ou acerto de contas. O auto precisa ser lido para saber alcance, prazo, autoridade competente e se a medida exige desocupacao total ou apenas reparo de parte do bem.\n\nO artigo 9º, IV, abrange reparacoes urgentes determinadas pelo poder publico que nao possam ser normalmente executadas com a permanencia do locatario, ou que este se recuse a permitir quando a permanencia for possivel. A causa concreta deve se encaixar nessa hipotese; uma recomendacao informal ou vistoria sem ordem de reparo nao produz automaticamente o mesmo efeito."
            ),
            "Devolução de valores pagos antecipadamente": (
                "Aluguel futuro, encargos e caucao exigem acerto separado",
                "Se houve pagamento por periodo posterior a efetiva devolucao do imovel, cabe apurar restituicao proporcional do que ficou sem causa, observadas as datas e o contrato. Encargos de consumo ou condominio devem ser rateados pelo periodo e por sua natureza, e nao devolvidos em bloco apenas porque ocorreu a interdicao.\n\nA caucao em dinheiro garante obrigacoes da locacao ate o acerto final. Ela deve ser restituida com as vantagens da poupanca depois de descontados apenas valores demonstrados; nao perde sua funcao no mesmo instante do auto se ainda existem aluguel anterior, consumo ou dano imputavel em discussao. A interdicao tambem nao autoriza o locador a reter a garantia sem prestacao de contas."
            ),
            "Quando cabe discutir responsabilidade do locador pelo risco": (
                "Interdicao sem culpa e defeito anterior nao sao iguais",
                "O fim do contrato e a indenizacao seguem perguntas distintas. Para cobrar mudanca, hospedagem ou danos a bens, e preciso demonstrar dever violado, prejuizo e nexo. O artigo 22, IV, responsabiliza o locador por defeitos anteriores; comunicacoes ignoradas e laudos anteriores podem provar ciencia e omissao.\n\nSe o risco surgiu por evento inevitavel sem culpa de qualquer parte, a distribuicao de perdas pode ser diferente. Por isso, nao basta anexar o auto: devem ser preservados laudos tecnicos, historico de manutencao, pedidos anteriores e comprovantes de despesas emergenciais."
            ),
        },
        "official_sources": [
            source(LEI + "#art9", "Lei 8.245/1991, art. 9º, IV", "desfazimento para reparacoes urgentes determinadas pelo poder publico"),
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, I a IV", "aptidao para uso, manutencao e defeitos anteriores"),
            source(LEI + "#art38", "Lei 8.245/1991, art. 38, § 2º", "limite e rendimento da caucao em dinheiro"),
        ],
    },
    "imob-locador-entra-sem-autorizacao": {
        "sections": {
            "Inviolabilidade do lar e o artigo 5º, inciso XI, da Constituição": (
                "A protecao constitucional pertence a quem mora no local",
                "O artigo 5º, XI, protege a casa como asilo inviolavel. O ingresso sem consentimento so e admitido, segundo o proprio texto constitucional, em caso de flagrante delito, desastre, para prestar socorro ou, durante o dia, por determinacao judicial. O proprietario que nao mora no imovel nao ganha uma excecao adicional por conservar o dominio ou uma copia da chave.\n\nA incidencia penal de uma entrada indevida depende dos elementos do artigo 150 do Codigo Penal e das circunstancias. No plano civil e locaticio, o uso pacifico e a posse direta ja bastam para impedir que o locador trate a chave reserva como permissao geral de acesso."
            ),
            "Medidas para fazer cessar a prática": (
                "Notificacao, seguranca e preservacao da prova",
                "A primeira resposta deve registrar data, modo de ingresso e objetos afetados, exigir que novos acessos sejam combinados e preservar imagens, mensagens e testemunhas. Boletim de ocorrencia documenta o relato, mas nao prova sozinho toda a dinamica nem garante indenizacao. Se houver perigo atual ou invasao em curso, os canais de emergencia adequados devem ser acionados.\n\nTrocar o segredo da fechadura pode proteger a posse, mas e prudente verificar contrato, regras do condominio e procedimentos de emergencia, alem de recompor ou entregar todas as chaves ao fim. Essa medida nao autoriza impedir vistoria regularmente combinada nem causar dano ao equipamento do imovel."
            ),
            "Indenização por dano moral em casos de reiteração": (
                "Dano moral depende da gravidade demonstrada",
                "Reiteracao apos notificacao, ingresso clandestino, exposicao da intimidade, ameaca ou retirada de bens tornam a conduta mais grave e fortalecem um pedido de obrigacao de nao fazer ou reparacao. Ainda assim, dano moral nao nasce automaticamente de qualquer entrada ou desencontro sobre vistoria; o juiz examina violacao concreta, prova e repercussao.\n\nUma tutela de urgencia pode ser pedida quando houver probabilidade do direito e risco de novas entradas, mas sua concessao nao e certa. A documentacao deve sustentar tanto o direito de uso pacifico quanto a urgencia alegada."
            ),
        },
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, II", "garantia de uso pacifico do imovel"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, IX", "vistoria mediante combinacao previa"),
            source("https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm#art5xi", "Constituicao Federal, art. 5º, XI", "inviolabilidade da casa e suas excecoes"),
            source("https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm#art150", "Codigo Penal, art. 150", "elementos legais da violacao de domicilio"),
        ],
    },
    "imob-vistoria-saida-cobranca-pintura": {
        "sections": {
            "Pintura e reparos de acabamento: quando integram o desgaste natural": (
                "A pintura deve ser comparada com o estado de entrada",
                "Desbotamento pelo tempo, marcas leves e envelhecimento compativel com duracao e uso podem entrar na ressalva do artigo 23, III. Furo, mancha ou mofo nao recebem classificacao automatica: tamanho, causa, quantidade, material e estado inicial mudam a conclusao. Uma infiltracao causada por defeito estrutural, por exemplo, nao se torna responsabilidade do locatario apenas porque manchou a tinta.\n\nPintura em cor diferente sem consentimento pode caracterizar modificacao vedada pelo artigo 23, VI e exigir recomposicao. Mesmo assim, a cobranca deve refletir o reparo necessario, o estado anterior e a depreciacao, sem financiar renovacao integral que deixe o imovel melhor do que foi entregue."
            ),
            "Quando a cobrança de pintura é legítima": (
                "Clausula de pintura nao apaga o desgaste normal",
                "A obrigacao de devolver no estado recebido convive com a excecao legal das deterioracoes do uso normal. Uma clausula que exige simplesmente 'pintura nova' em toda saida nao prova, por si, que o locatario causou dano nem elimina o artigo 23, III. Ela pode disciplinar cor e padrao de recomposicao quando existe alteracao ou avaria imputavel, mas a vistoria comparativa continua necessaria.\n\nA cobranca e mais defensavel quando identifica diferenca concreta entre entrada e saida, causa atribuivel ao ocupante, area a reparar e orcamento proporcional. Desconto generico da caucao deve vir acompanhado de contas e documentos, permitindo contestacao item a item."
            ),
        },
        "official_sources": [
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, III e VI", "uso normal e consentimento para modificar a forma do imovel"),
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, V e IX", "descricao quando solicitada e comprovantes das parcelas exigidas"),
            source(LEI + "#art45", "Lei 8.245/1991, art. 45", "nulidade de clausula que vise elidir objetivo da lei"),
        ],
    },
    "imob-desgaste-natural-vs-dano": {
        "sections": {
            "Exemplos de desgaste natural que não podem ser cobrados": (
                "Exemplos orientam, mas nao substituem a comparacao",
                "Perda gradual de brilho do piso, folga de ferragens e desbotamento podem ser compativeis com uso normal, sobretudo em locacao longa e materiais antigos. Pequenos furos, rejunte, silicone e pintura exigem contexto: quantidade, manutencao pactuada, qualidade inicial e possibilidade de reparo localizado. A lei nao traz uma lista de itens sempre gratuitos.\n\nA pergunta correta e se a alteracao excede o envelhecimento esperado para aquele material e periodo. Vida util, laudo de entrada e manutencoes feitas durante o contrato ajudam a evitar que o locatario pague um item novo no lugar de outro ja depreciado."
            ),
            "O que caracteriza avaria e dano indenizável": (
                "Causa, nexo e custo proporcional do reparo",
                "Vidro quebrado pelo ocupante, instalacao danificada em reforma e queimadura ou perfuracao fora do uso comum podem gerar dever de reparar pelo artigo 23, V. O locador precisa demonstrar que a avaria nao existia, que foi causada por pessoa sob responsabilidade do locatario e qual e o custo necessario para recompor o estado devido.\n\nA indenizacao nao deve criar enriquecimento. Se um componente antigo precisa ser substituido, sua idade e estado anterior podem influenciar o valor; se o reparo localizado resolve, a troca integral exige justificativa tecnica. Defeito estrutural, vicio anterior ou dano de terceiro segue outra atribuicao."
            ),
            "Como a perícia ou o laudo comparativo resolve a dúvida": (
                "Laudo comparativo e prova de causalidade",
                "A comparacao deve vincular cada fotografia de entrada ao mesmo ambiente e item na saida, com data e descricao. Uma vistoria unilateral e prova possivel, mas pode ser contestada; orcamento sem explicacao da causa prova preco, nao necessariamente responsabilidade. Quando a origem e tecnica, pericia ou parecer independente pode separar uso normal, falta de manutencao, vicio e dano.\n\nSem laudo inicial, outras provas continuam validas e o onus segue o artigo 373 do CPC. Nao ha presuncao automatica de que tudo foi causado pelo inquilino nem de que o imovel estava sem defeitos."
            ),
        },
        "official_sources": [
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, III e V", "ressalva do uso normal e reparacao de danos causados"),
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, IV e V", "defeitos anteriores e descricao do estado quando solicitada"),
            source("https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art373", "Codigo de Processo Civil, art. 373", "onus da prova dos fatos alegados"),
        ],
    },
}


def deaccent(value):
    return "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )


def body_word_count(page):
    def count(value):
        return len(re.findall(r"[^\W_]+", deaccent(value).lower(), re.UNICODE))

    total = count(page.get("opening", ""))
    for section in page.get("sections", []):
        total += count(section.get("heading", "")) + count(section.get("text", ""))
    for item in page.get("faq", []):
        total += count(item.get("q", "")) + count(item.get("a", ""))
    return total


def apply_page_update(page, update):
    for field in ("title", "meta_description", "h1", "opening", "faq", "official_sources"):
        if field in update:
            page[field] = update[field]

    pending = dict(update.get("sections", {}))
    for section in page.get("sections", []):
        old_heading = section.get("heading")
        if old_heading not in pending:
            continue
        new_heading, new_text = pending.pop(old_heading)
        section["heading"] = new_heading
        section["text"] = new_text
    if pending:
        raise RuntimeError(f"secoes ausentes em {page.get('intent_id')}: {sorted(pending)}")

    page["word_count"] = body_word_count(page)
    # O gate canonico aplica pisos distintos a artigo e verbete; esta guarda
    # local evita apenas truncamento acidental antes da auditoria completa.
    if not 300 <= page["word_count"] <= 1600:
        raise RuntimeError(
            f"word_count fora da faixa em {page.get('intent_id')}: {page['word_count']}"
        )


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page.get("intent_id"): page for page in pages}
    missing = sorted(set(UPDATES) - set(by_intent))
    if missing:
        raise SystemExit(f"intents ausentes: {missing}")

    for intent_id, update in UPDATES.items():
        apply_page_update(by_intent[intent_id], update)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")

    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-03.", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(open(TARGET, "rb").read()).hexdigest() != EXPECTED_SHA256:
            raise SystemExit("CAS falhou antes da promocao")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(f"corrigidas {len(UPDATES)} paginas; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
