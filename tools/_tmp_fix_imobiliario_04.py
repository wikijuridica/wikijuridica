#!/usr/bin/env python3
"""Correção jurídico-editorial integral do shard imobiliário-04."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "82f3a4abc293d938a3aaeb06dcfa4b59e6d2b2c0d4a1ed7c1ddbf8c482233749"
TOMBSTONE_INTENT = "imob-aluguel-social-municipio"
TOMBSTONE_REASON = (
    "Aluguel social depende de lei, decreto, orçamento, calamidade e critérios de cada município. "
    "Como o tema editorial não identifica uma cidade, não existe fonte oficial local específica capaz de sustentar "
    "elegibilidade, valor ou procedimento sem criar uma página nacional enganosa. O tema permanece bloqueado até "
    "ser desdobrado por município com norma vigente e fonte oficial própria."
)
LEI = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm"
CC = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
CPC = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def section(heading, text):
    return {"heading": heading, "text": text}


UPDATES = {
    "imob-consignacao-aluguel-recusado": {
        "opening": (
            "A recusa do locador, o desaparecimento do boleto ou a devolução de uma transferência não "
            "autorizam o inquilino a simplesmente guardar o aluguel. A dívida continua vencendo enquanto o "
            "pagamento não for feito por meio capaz de produzir quitação. A Lei do Inquilinato oferece uma ação "
            "específica de consignação de aluguéis e acessórios, mas o resultado depende do depósito correto, "
            "da continuidade dos pagamentos e da prova do motivo que impediu o recebimento."
        ),
        "sections": [
            section(
                "O procedimento especial do artigo 67 começa com valores discriminados",
                "A petição deve identificar cada aluguel e acessório da locação e indicar os valores. Depois de "
                "determinada a citação, o autor é intimado para realizar, em vinte e quatro horas, o depósito "
                "judicial da importância indicada, sob pena de extinção do processo. O pedido também alcança as "
                "obrigações que vencerem durante a tramitação até a sentença de primeira instância; por isso, os "
                "depósitos seguintes precisam ser feitos nos vencimentos.\n\n"
                "A ação não se resume a transferir qualquer quantia para uma conta judicial. Ela busca obter a "
                "quitação das parcelas especificadas diante de recusa, mora do credor, dúvida sobre quem recebe "
                "ou outro fundamento juridicamente demonstrável. Contrato, boletos anteriores e memória de "
                "cálculo ajudam a separar aluguel, condomínio, tributos e demais encargos efetivamente devidos."
            ),
            section(
                "Depósito insuficiente pode ser complementado com acréscimo legal",
                "O locador pode contestar alegando que não houve recusa, que a recusa foi justa, que o depósito "
                "ocorreu fora do prazo ou do lugar ou que o valor não foi integral. Também pode formular pedido "
                "de despejo e cobrança da diferença na reconvenção. Isso mostra por que uma consignação "
                "insuficiente não deve ser tratada como vitória automática do inquilino.\n\n"
                "Ao mesmo tempo, a insuficiência não encerra necessariamente a discussão. O inciso VII do artigo "
                "67 permite complementar o depósito inicial no prazo de cinco dias contado da ciência da resposta, "
                "com acréscimo de dez por cento sobre a diferença. Cumprida essa regra, o juiz pode declarar a "
                "quitação e afastar a rescisão, sem excluir a responsabilidade do autor pelas custas e honorários "
                "previstos na lei. A janela é curta e exige cálculo conferido assim que a contestação chega."
            ),
            section(
                "Tentativas de pagamento formam a prova, mas não substituem a quitação",
                "Mensagens pedindo o boleto, transferência devolvida, carta recebida e resposta da administradora "
                "ajudam a demonstrar que o devedor procurou pagar no vencimento. Se havia conta indicada e ainda "
                "válida, convém registrar por que o pagamento não se completou. Um depósito unilateral em conta "
                "desconhecida ou sem identificação pode não permitir vincular a quantia à obrigação correta.\n\n"
                "A tentativa extrajudicial não é uma formalidade universal anterior à ação, mas a causa legal da "
                "consignação precisa existir e ser provada. Quando o credor é incerto, faleceu ou há disputa entre "
                "pessoas que se dizem autorizadas a receber, documentos sobre essa dúvida também devem integrar o "
                "pedido. O objetivo é impedir mora artificial sem criar um pagamento impossível de conferir."
            ),
            section(
                "Ajuizamento não suspende por si só cobrança ou negativação",
                "Protocolar a ação ou efetuar apenas o primeiro depósito não garante, sozinho, que nenhuma medida "
                "de cobrança será adotada. O efeito liberatório decorre do reconhecimento da consignação e da "
                "regularidade dos depósitos; medidas urgentes sobre protesto, cadastro de inadimplentes ou despejo "
                "dependem do quadro processual e de decisão específica quando necessária.\n\n"
                "Antes de ajuizar, devem ser conferidos o valor contratual, o reajuste, os encargos vencidos, a data "
                "da recusa e a competência territorial. Durante o processo, o calendário das parcelas vincendas "
                "não pode ser abandonado. Uma análise jurídica focada nesses documentos reduz o risco de usar a "
                "consignação para uma controvérsia de revisão de aluguel que exige outra estratégia."
            ),
            section(
                "Um roteiro documental para a recusa de recebimento",
                "Preserve o contrato e seus aditivos, os três últimos comprovantes, o boleto recusado ou ausente, "
                "as mensagens completas e o extrato que mostre a devolução. Monte uma tabela por vencimento, com "
                "aluguel e cada acessório em linha separada. Se houver dúvida sobre condomínio, imposto ou multa, "
                "não esconda a divergência em um total aproximado.\n\n"
                "Também registre ofertas posteriores de pagamento e qualquer mudança de dados bancários. Esse "
                "conjunto permite ao profissional responsável formular o pedido com o valor defendido, antecipar "
                "a possível alegação de diferença e acompanhar os depósitos seguintes sem prometer que a ação será "
                "acolhida antes da manifestação do locador e do exame judicial."
            ),
        ],
        "faq": [
            {
                "q": "Um depósito judicial impede automaticamente a negativação?",
                "a": (
                    "Não. A suficiência, a tempestividade e a causa da consignação precisam ser examinadas, e a "
                    "suspensão de uma anotação pode depender de decisão específica."
                ),
            },
            {
                "q": "É preciso depositar também os aluguéis que vencem durante a ação?",
                "a": (
                    "Sim. O artigo 67 inclui as obrigações vincendas até a sentença de primeira instância e exige "
                    "depósitos nos respectivos vencimentos."
                ),
            },
        ],
        "official_sources": [
            source(LEI + "#art67", "Lei 8.245/1991, art. 67", "rito, depósitos sucessivos, defesa e complemento da consignação locatícia"),
            source(CC + "#art334", "Código Civil, arts. 334 e 335", "efeito do depósito e hipóteses gerais de consignação em pagamento"),
        ],
    },
    "imob-recibo-aluguel-discriminado": {
        "meta_description": (
            "Pagou o aluguel em dinheiro ou Pix e não recebeu comprovante detalhado? Veja o que a Lei do "
            "Inquilinato exige sobre quitação discriminada."
        ),
        "opening": (
            "O artigo 22, inciso VI, da Lei do Inquilinato obriga o locador a entregar recibo discriminado das "
            "importâncias pagas e proíbe a quitação genérica. A regra vale para toda locação alcançada pela lei, "
            "seja o pagamento feito em dinheiro, Pix, transferência ou boleto. O comprovante bancário mostra que "
            "houve uma movimentação, mas não substitui a indicação de qual aluguel e quais encargos foram quitados."
        ),
        "sections": [
            section(
                "A quitação deve separar aluguel, período e encargos",
                "O recibo precisa permitir que as partes reconstruam a conta. Deve identificar o período pago, o "
                "aluguel, o condomínio ou outro encargo recebido e eventuais acréscimos. Uma declaração como "
                "'recebi o valor total' deixa em aberto a imputação e contraria a vedação legal de quitação "
                "genérica. A discriminação também evita aplicar reajuste do aluguel sobre parcelas que possuem "
                "natureza diferente.\n\n"
                "O dever existe mesmo quando uma imobiliária administra o contrato. A plataforma pode gerar o "
                "documento em nome do locador, desde que identifique credor, devedor, competência e rubricas. Não "
                "há exigência geral de papel timbrado, reconhecimento de firma ou suporte físico."
            ),
            section(
                "O crime do artigo 44 tem alcance bem mais estreito",
                "A recusa em fornecer recibo também aparece no artigo 44, inciso I, mas ali a lei descreve crime "
                "específico do locador ou sublocador em habitação coletiva multifamiliar. Essa hipótese penal não "
                "transforma toda falha de recibo em crime. Fora desse recorte, permanece o dever civil geral do "
                "artigo 22, inciso VI, e podem existir consequências contratuais ou probatórias.\n\n"
                "Não é o inciso IV do artigo 44 que trata de recibos: ele se refere à execução de despejo em desacordo "
                "com o artigo 65, parágrafo 2º. Usá-lo como fundamento geral da quitação discriminada mistura duas "
                "condutas diferentes e produz orientação penal incorreta."
            ),
            section(
                "Extrato e planilha própria não criam quitação pelo credor",
                "O locatário pode guardar uma planilha para conferir cobranças, mas esse registro unilateral não "
                "equivale ao recibo que a lei manda o locador fornecer. Da mesma forma, escrever uma descrição no "
                "campo do Pix ajuda a identificar a transferência, sem provar que o credor aceitou aquela "
                "imputação ou reconheceu todos os encargos como quitados.\n\n"
                "Diante da recusa, o pedido deve ser feito por escrito, reproduzindo as rubricas e o período. Se o "
                "locador recebe o dinheiro e discute depois o alcance do pagamento, a mensagem, o contrato, o "
                "boleto e o extrato serão examinados em conjunto. Se ele passa a recusar o próprio pagamento, a "
                "questão deixa de ser apenas documental e pode exigir consignação do valor correto."
            ),
            section(
                "Como organizar uma cobrança já paga sem recibo adequado",
                "Separe comprovante bancário, boleto, contrato e mensagem referente a cada mês. Solicite uma nova "
                "quitação que discrimine os itens e aponte por escrito qualquer cobrança repetida. Não retenha "
                "aluguéis futuros como forma de pressão, pois a falta do recibo não autoriza inadimplência "
                "unilateral.\n\n"
                "Se houver pagamento em espécie, peça o documento no ato e evite entregar novas quantias sem um "
                "meio verificável. Quando a divergência já envolve vários meses, uma conferência jurídica pode "
                "delimitar quais parcelas foram demonstradas, sem anunciar êxito ou devolução antes da análise da "
                "prova."
            ),
        ],
        "faq": [{
            "q": "Recibo enviado por correio eletrônico ou aplicativo pode ser válido?",
            "a": "Pode, desde que identifique as partes, o período e cada importância paga; o suporte digital não autoriza quitação genérica.",
        }],
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, VI", "dever geral de fornecer recibo discriminado e vedação da quitação genérica"),
            source(LEI + "#art44", "Lei 8.245/1991, art. 44, I e IV", "crime restrito à habitação coletiva e distinção do inciso sobre despejo"),
        ],
    },
    "imob-despesas-ordinarias-extraordinarias": {
        "opening": (
            "O boleto do condomínio não decide, pelo nome da rubrica, quem suporta a despesa na locação. Os "
            "artigos 22 e 23 da Lei 8.245/1991 separam custos extraordinários, atribuídos ao locador, de despesas "
            "ordinárias comprovadas, atribuídas ao locatário. A finalidade, o período e a documentação do gasto "
            "precisam ser conferidos antes de repassar ou recusar qualquer parcela."
        ),
        "sections": [
            section(
                "Despesas extraordinárias preservam ou ampliam o patrimônio",
                "O artigo 22, inciso X, coloca a cargo do locador as obras de reforma ou acréscimo que interessem à "
                "estrutura integral do imóvel, a pintura de fachadas e partes externas, as obras destinadas a "
                "repor a habitabilidade do edifício e as indenizações trabalhistas relativas a período anterior "
                "ao início da locação. Também lista a instalação de equipamentos de segurança, incêndio, telefonia, "
                "intercomunicação, esporte e lazer, a decoração ou paisagismo das áreas comuns e a constituição do "
                "fundo de reserva.\n\n"
                "A lista mostra que valor alto não é o único critério. Uma parcela pequena para constituir reserva "
                "continua extraordinária, enquanto uma manutenção cotidiana cara pode ser ordinária. A ata da "
                "assembleia e o contrato da obra revelam a destinação real."
            ),
            section(
                "Despesas ordinárias financiam administração e conservação corrente",
                "O artigo 23, inciso XII e parágrafo 1º, atribui ao locatário salários e encargos dos empregados do "
                "condomínio, consumo das áreas comuns, limpeza, conservação e pintura das instalações internas de "
                "uso comum, além da manutenção de sistemas hidráulicos, elétricos, mecânicos, de segurança, lazer, "
                "elevadores, porteiro eletrônico e antenas coletivas. Pequenos reparos nesses sistemas também "
                "aparecem na relação legal.\n\n"
                "O locatário só fica obrigado quando houver comprovação da previsão orçamentária e do rateio mensal, "
                "e pode exigir essa prova a qualquer tempo. Saldo negativo de gestão e reposição do fundo de reserva "
                "podem ser ordinários somente nos limites e períodos descritos pela própria lei."
            ),
            section(
                "Fundo de reserva exige identificar constituição ou reposição",
                "A constituição do fundo é despesa extraordinária do proprietário. Já a reposição de quantia que "
                "tenha sido usada, total ou parcialmente, para despesas ordinárias durante a locação integra a "
                "lista do artigo 23. Se o consumo do fundo ocorreu antes do início do contrato, a exceção legal "
                "impede transferir essa reposição ao novo inquilino.\n\n"
                "Por isso, o simples rótulo 'fundo de reserva' não basta. O demonstrativo deve mostrar se a cobrança "
                "está formando patrimônio, recompondo gasto corrente da ocupação atual ou cobrindo período anterior."
            ),
            section(
                "Ata, balancete e rateio resolvem a classificação concreta",
                "Peça a ata que aprovou a despesa, o orçamento, a data da execução e o balancete que demonstra como "
                "o valor foi usado. Uma troca integral de elevadores pode ser instalação extraordinária; reposições "
                "e manutenção periódica do equipamento existente podem ser ordinárias. Pintura externa da fachada "
                "é exemplo legal de custo do locador, enquanto pintura das dependências internas de uso comum está "
                "na lista ordinária.\n\n"
                "Cláusula que repassa genericamente todo o condomínio não altera a natureza de cada parcela. A "
                "contestação deve ser itemizada, sem descontar por conta própria valores de um aluguel vincendo. Uma "
                "revisão do contrato e dos documentos condominiais permite formular o pedido correto sem prometer "
                "reembolso automático."
            ),
        ],
        "faq": [{
            "q": "Uma obra aprovada como 'ordinária' pela assembleia obriga o inquilino?",
            "a": "Não necessariamente. A classificação locatícia depende da natureza e do período da despesa à luz dos artigos 22 e 23, além da prova do orçamento e do rateio.",
        }],
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, X", "despesas extraordinárias de responsabilidade do locador"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, XII e parágrafos", "despesas ordinárias, prova orçamentária e reposição do fundo"),
            source(LEI + "#art45", "Lei 8.245/1991, art. 45", "nulidade de cláusula que vise afastar objetivos da lei"),
        ],
    },
    "imob-fundo-reserva-inquilino": {
        "opening": (
            "A resposta depende da origem da parcela. A constituição do fundo de reserva é despesa extraordinária "
            "do locador. A reposição de valores do fundo usados para custear despesas ordinárias durante a locação "
            "pode caber ao locatário. A Lei do Inquilinato distingue expressamente essas situações, por isso um "
            "'não' absoluto induz a erro."
        ),
        "sections": [
            section(
                "Constituir a reserva patrimonial é obrigação do locador",
                "O artigo 22, inciso X, alínea g, inclui a constituição do fundo de reserva entre as despesas "
                "extraordinárias de condomínio. A cobrança destinada a formar ou ampliar essa reserva permanece "
                "vinculada ao patrimônio da unidade e não corresponde ao consumo mensal do ocupante. Mesmo que o "
                "condomínio emita um boleto único, o locador deve suportar essa parte.\n\n"
                "Uma chamada extra para recompor patrimônio sem relação com gasto ordinário atual também não muda "
                "de natureza apenas porque a administração a nomeou como reposição. É preciso olhar a saída de "
                "caixa que originou o rateio."
            ),
            section(
                "Reposição por despesa ordinária atual pode caber ao locatário",
                "O artigo 23, parágrafo 1º, alínea i, inclui nas despesas ordinárias a reposição do fundo total ou "
                "parcialmente utilizado para custear ou complementar os gastos correntes descritos nas alíneas "
                "anteriores. A exceção é explícita: se o uso se refere a período anterior ao início da locação, a "
                "reposição não deve ser transferida ao inquilino atual.\n\n"
                "A data do boleto de reposição, isoladamente, não resolve. Importa saber quando e para que o fundo "
                "foi consumido. Um balancete pode mostrar, por exemplo, que a reserva pagou salários e manutenção "
                "durante os meses em que o locatário ocupava o imóvel."
            ),
            section(
                "Como conferir e pedir restituição sem criar nova mora",
                "Solicite balancetes, ata, previsão orçamentária e planilha de rateio. Separe constituição, "
                "reposição ordinária do período atual e recomposição de período anterior. O artigo 23 permite ao "
                "locatário exigir a comprovação das despesas ordinárias a qualquer tempo.\n\n"
                "Se houve pagamento de parcela que competia ao locador, formalize o valor e proponha devolução ou "
                "compensação documentada. Não abata unilateralmente do aluguel seguinte: compensação exige dívidas "
                "recíprocas, líquidas e vencidas, e a divergência sobre a natureza da cota pode gerar cobrança de "
                "mora. Uma avaliação individual é necessária quando o histórico não discrimina o uso do fundo. "
                "Registre ainda quem recebeu cada pagamento e quais competências foram alcançadas, para não pedir ao "
                "locador a devolução de parcela que o condomínio já lançou como gasto corrente da ocupação."
            ),
        ],
        "faq": [{
            "q": "O nome 'fundo de reserva' no boleto basta para cobrar do proprietário?",
            "a": "Não. É necessário distinguir a constituição do fundo da reposição de valor usado em despesa ordinária e verificar a qual período o gasto pertence.",
        }],
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, X, g", "constituição do fundo como despesa extraordinária do locador"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, § 1º, i, e § 2º", "reposição ordinária durante a locação e direito à comprovação"),
            source(CC + "#art368", "Código Civil, art. 368", "requisitos gerais da compensação entre dívidas recíprocas"),
        ],
    },
    "imob-dono-cobrado-condominio-inquilino": {
        "opening": (
            "O contrato pode atribuir ao inquilino as despesas ordinárias, mas essa divisão interna não elimina "
            "a relação do proprietário com o condomínio nem transforma o locatário em condômino. A cobrança deve "
            "ser analisada conforme a natureza propter rem da cota, a titularidade e a relação material com a "
            "unidade. Depois, locador e locatário acertam entre si somente as parcelas que o contrato e a Lei do "
            "Inquilinato colocam a cargo de cada um."
        ),
        "sections": [
            section(
                "A contribuição condominial nasce da relação com a unidade",
                "O artigo 1336, inciso I, do Código Civil impõe ao condômino contribuir para as despesas na "
                "proporção de sua fração ideal, salvo regra válida diferente. Por sua natureza vinculada ao imóvel, "
                "o crédito condominial pode alcançar o proprietário e o próprio bem. O artigo 1.345, por sua vez, "
                "trata especificamente do adquirente que responde pelos débitos do alienante; ele não deve ser "
                "usado isoladamente como se descrevesse toda locação.\n\n"
                "A jurisprudência do STJ examina titularidade, posse e ciência do condomínio em situações concretas. "
                "Em 2020, a corte reconheceu que o dono poderia integrar a execução mesmo diante de acordo dos "
                "ocupantes para pagar a dívida. Isso explica o risco patrimonial do locador sem criar uma regra de "
                "que apenas uma pessoa sempre pode ser demandada em qualquer configuração."
            ),
            section(
                "O contrato de locação regula o reembolso entre as partes",
                "O artigo 23, inciso XII, atribui ao locatário as despesas ordinárias comprovadas. Salários do "
                "condomínio, consumo e manutenção corrente podem integrar esse grupo; obra extraordinária e "
                "constituição de fundo de reserva continuam, em regra, com o locador. O proprietário que paga cota "
                "ordinária correspondente ao período locado pode exigir o reembolso previsto no contrato e na lei, "
                "mas precisa discriminar a natureza e o mês.\n\n"
                "Multa, juros e custos adicionais também exigem nexo. Se o locador deixou a cobrança acumular mesmo "
                "tendo informação para evitar agravamento, a extensão do regresso pode ser discutida. Não é seguro "
                "somar todo o débito do condomínio e chamá-lo de obrigação do inquilino."
            ),
            section(
                "Locatário não recebe automaticamente todos os direitos de condômino",
                "No REsp 1.630.199, resumido no Informativo 704, o STJ decidiu que o locatário não podia demandar o "
                "condomínio para questionar administração e prestação de contas. A transferência contratual de "
                "certos encargos não o sub-roga em todos os direitos do proprietário. A própria lei permite que ele "
                "exija do locador a comprovação da previsão orçamentária e do rateio mensal.\n\n"
                "Isso muda a estratégia de prova: o inquilino pede documentos ao locador, e o locador exerce perante "
                "o condomínio os direitos ligados à unidade. Há exceções legais específicas, como participação em "
                "determinadas deliberações ordinárias, mas elas não tornam as posições idênticas."
            ),
            section(
                "Providências quando a dívida aparece",
                "O proprietário deve obter planilha atualizada, atas e boletos, separar períodos e verificar se já "
                "existe processo. Pagar para evitar crescimento da dívida não dispensa reservar prova do direito de "
                "regresso. O inquilino, por sua vez, deve apresentar comprovantes e apontar valores extraordinários "
                "ou anteriores que não lhe competem.\n\n"
                "A caução não deve ser apropriada sem prestação de contas. Se o contrato permite garantir encargos, "
                "o desconto exige dívida demonstrada e devolução do saldo com os rendimentos cabíveis. Uma cobrança "
                "jurídica responsável delimita devedor, período e natureza da cota antes de prometer recuperação "
                "integral. Se houver execução, matrícula, convenção e fase processual também precisam ser examinadas, "
                "porque acordo interno não suspende penhora nem altera sozinho o título já constituído."
            ),
            section(
                "Exemplo de acerto corretamente discriminado",
                "Imagine três cotas mensais ordinárias vencidas durante a ocupação e uma chamada extra para pintura "
                "da fachada. O condomínio cobra a unidade e o proprietário quita o total. No acerto com o locatário, "
                "os três meses correntes podem integrar o regresso se estiverem comprovados; a pintura externa, "
                "classificada pela lei como extraordinária, não deve ser repassada apenas por estar no mesmo acordo.\n\n"
                "Contrato, balancete e recibo do pagamento ao condomínio permitem chegar a essa divisão. Sem esses "
                "documentos, tanto a cobrança integral quanto a recusa integral correm o risco de tratar parcelas "
                "distintas como se fossem uma só."
            ),
        ],
        "faq": [{
            "q": "O contrato que manda o inquilino pagar condomínio libera o proprietário perante o condomínio?",
            "a": "Não. A cláusula disciplina a relação locatícia; a responsabilidade perante o condomínio decorre da relação jurídica com a unidade e das circunstâncias examinadas no caso.",
        }],
        "official_sources": [
            source(CC + "#art1336", "Código Civil, art. 1.336, I", "dever do condômino de contribuir para as despesas"),
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, XII e § 2º", "despesas ordinárias do locatário e comprovação do rateio"),
            source("https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D018492", "STJ, Informativo 704, REsp 1.630.199/RS", "limites dos direitos do locatário perante o condomínio"),
            source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/15102020-Dono-do-imovel-pode-ser-executado-mesmo-que-ocupante-tenha-feito-acordo-para-pagar-divida-condominial.aspx", "STJ, cobrança propter rem contra o proprietário", "risco do titular diante de dívida e acordo de ocupantes"),
        ],
    },
    "imob-contrato-verbal-aluguel": {
        "opening": (
            "A locação urbana pode nascer de acordo verbal porque, em regra, a lei não exige instrumento escrito "
            "para a validade do negócio. Isso não significa que todo contrato verbal seja necessariamente por prazo "
            "indeterminado. Valor, duração e demais condições podem ter sido combinados oralmente; o problema é "
            "provar com segurança o conteúdo e acessar efeitos que dependem de forma escrita."
        ),
        "sections": [
            section(
                "Validade e prova são perguntas diferentes",
                "O artigo 107 do Código Civil admite declaração de vontade sem forma especial quando a lei não a "
                "exige. Pagamentos, entrega das chaves e ocupação podem confirmar a existência da locação. Para "
                "reconstruir o acordo, servem mensagens, recibos, testemunhas e o histórico de cobranças.\n\n"
                "Esses elementos não provam automaticamente tudo o que uma parte afirma. Uma transferência mensal "
                "mostra valor e periodicidade, mas pode não demonstrar prazo fixo, índice de reajuste ou autorização "
                "para determinada obra. Quem invoca uma condição específica precisa relacioná-la às provas."
            ),
            section(
                "O artigo 47 alcança locação residencial verbal",
                "A Lei 8.245/1991 trata conjuntamente a locação residencial ajustada verbalmente e a escrita por "
                "prazo inferior a trinta meses. Findo o prazo estabelecido, ela se prorroga automaticamente por "
                "tempo indeterminado, e o imóvel somente pode ser retomado nas hipóteses do artigo 47. Portanto, é "
                "incorreto dizer que a oralidade apaga um prazo efetivamente combinado.\n\n"
                "Durante um prazo determinado provado, o locador não pode simplesmente retomar o imóvel fora das "
                "hipóteses legais. Depois da prorrogação, uso próprio, infração, extinção de trabalho vinculado ou "
                "vigência ininterrupta superior a cinco anos são exemplos de fundamentos previstos. O Informativo "
                "687 do STJ esclarece a contagem do período de cinco anos a partir da formação do vínculo."
            ),
            section(
                "Alguns efeitos exigem documento ou formalidade própria",
                "Fiança não se presume e deve ser escrita, conforme o artigo 819 do Código Civil. Averbação da "
                "locação para exercer pretensão real de preferência também depende de instrumento com os requisitos "
                "legais. Cláusula de vigência oponível ao adquirente requer contrato e registro adequados. A relação "
                "pode ser válida entre locador e locatário sem produzir todos esses efeitos perante terceiros.\n\n"
                "Formalizar depois o que já é praticado exige cuidado com a data e com obrigações passadas. Um aditivo "
                "não deve inventar retroativamente garantia, prazo ou dívida que nunca foram acordados."
            ),
            section(
                "Como documentar o acordo sem distorcer o histórico",
                "Reúna comprovantes, mensagens sobre entrada e saída, recibos, vistoria e contas vinculadas ao imóvel. "
                "Liste os pontos realmente convergentes e os controvertidos. Um instrumento escrito posterior pode "
                "fixar regras futuras, desde que ambas as partes concordem e compreendam o que mudou.\n\n"
                "Se já existe disputa sobre duração ou valor, assinar um texto preparado apenas pela outra parte pode "
                "funcionar como reconhecimento indesejado. A revisão jurídica deve explicar a prova disponível e os "
                "limites do artigo 47, sem anunciar que a falta de papel favorece necessariamente um dos lados."
            ),
        ],
        "faq": [{
            "q": "É possível combinar verbalmente um prazo de doze meses?",
            "a": "Sim, mas a existência e o termo do prazo podem precisar de prova; ao final, a locação residencial entra no regime do artigo 47 se a ocupação continuar.",
        }],
        "official_sources": [
            source(LEI + "#art47", "Lei 8.245/1991, art. 47", "regime da locação residencial verbal ou escrita por menos de trinta meses"),
            source(CC + "#art107", "Código Civil, art. 107", "liberdade de forma quando não houver exigência especial"),
            source(CC + "#art819", "Código Civil, art. 819", "forma escrita exigida para a fiança"),
            source("https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D018036", "STJ, Informativo 687, REsp 1.511.978/BA", "termo inicial da denúncia vazia do artigo 47, V"),
        ],
    },
    "imob-assinatura-eletronica-locacao": {
        "opening": (
            "A assinatura eletrônica pode formar contrato de locação válido. Para saber se o mesmo arquivo também "
            "serve como título executivo, porém, é preciso verificar autoria, integridade e o modo como a plataforma "
            "atestou o documento. Desde a Lei 14.620/2023, o artigo 784, parágrafo 4º, do CPC admite dispensar "
            "testemunhas em título eletrônico quando sua integridade é conferida por provedor de assinatura."
        ),
        "sections": [
            section(
                "Validade do contrato não depende apenas de ICP-Brasil",
                "A Medida Provisória 2.200-2/2001 preserva a validade de documentos emitidos com certificação da "
                "ICP-Brasil e também admite outros meios de comprovação de autoria e integridade aceitos pelas "
                "partes ou pela pessoa contra quem o documento é oposto. Assim, assinatura simples, avançada ou "
                "qualificada não deve ser avaliada só pelo nome comercial da plataforma.\n\n"
                "Identificação do signatário, autenticação, versão final, data e trilha de auditoria ajudam a demonstrar "
                "consentimento. Se o arquivo mudou depois do aceite ou a conta foi usada por terceiro, a controvérsia "
                "é probatória e não se resolve com um selo visual inserido no PDF."
            ),
            section(
                "A Lei 14.063 não é base geral isolada do contrato privado",
                "A Lei 14.063/2020 disciplina principalmente assinaturas em interações com entes públicos, atos de "
                "pessoas jurídicas e questões de saúde e licenciamento abrangidas por seu texto. Suas categorias "
                "podem ajudar a descrever tecnologia, mas a lei não é, sozinha, fundamento geral de toda locação "
                "privada eletrônica. A formação do negócio também passa pelo Código Civil e pela MP 2.200-2.\n\n"
                "A plataforma deve explicar qual modalidade usa e como preserva evidência. Dizer apenas que a "
                "assinatura é 'avançada' não demonstra, sem os registros correspondentes, quem assinou e qual era "
                "o conteúdo naquele instante."
            ),
            section(
                "O parágrafo 4º do artigo 784 mudou a análise das testemunhas",
                "A Lei 14.620/2023 acrescentou ao CPC uma regra específica: nos títulos executivos constituídos ou "
                "atestados eletronicamente, é admitida qualquer modalidade de assinatura eletrônica prevista em lei, "
                "e as testemunhas podem ser dispensadas quando a integridade for conferida por provedor de assinatura. "
                "Portanto, é incorreto afirmar que todo contrato eletrônico sem duas testemunhas perde executividade.\n\n"
                "A dispensa não torna executivo qualquer clique. A obrigação precisa ser certa, líquida e exigível, "
                "e a integridade efetivamente conferida pode ser questionada. Um contrato válido que não satisfaça o "
                "rito executivo ainda pode servir de prova em ação de conhecimento."
            ),
            section(
                "Pontos a conferir antes de guardar o arquivo final",
                "Baixe o contrato e o relatório de assinatura; confira hash ou código de verificação, endereços de correio eletrônico ou "
                "telefones autenticados, horários e eventuais certificados. Confirme que anexos, vistoria e inventário "
                "mencionados estão no pacote assinado. Não aceite link que apenas exibe uma versão mutável sem meio de "
                "validar o documento depois.\n\n"
                "Em cobrança concreta, compare a evidência tecnológica com o requisito jurídico invocado. Uma análise "
                "profissional pode distinguir validade, prova e executividade sem prometer que a plataforma será aceita "
                "antes do contraditório."
            ),
        ],
        "faq": [{
            "q": "Contrato eletrônico sem testemunhas é sempre inexequível?",
            "a": "Não. O artigo 784, § 4º, permite dispensá-las quando um provedor de assinatura confere a integridade, sem eliminar os demais requisitos da execução.",
        }],
        "official_sources": [
            source("https://www.planalto.gov.br/ccivil_03/mpv/antigas_2001/2200-2.htm", "MP 2.200-2/2001, art. 10", "autoria e integridade por ICP-Brasil ou outros meios admitidos"),
            source("https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l14063.htm", "Lei 14.063/2020", "âmbito e modalidades de assinatura eletrônica"),
            source(CPC + "#art784", "Código de Processo Civil, art. 784, § 4º", "título eletrônico e dispensa condicionada de testemunhas"),
            source("https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14620.htm", "Lei 14.620/2023", "inclusão do parágrafo 4º no artigo 784 do CPC"),
        ],
    },
    "imob-luvas-locacao-residencial": {
        "opening": (
            "Exigir do candidato uma quantia apenas para entregar o imóvel, além do aluguel e dos encargos "
            "permitidos, pode enquadrar-se no artigo 43, inciso I, da Lei do Inquilinato. O dispositivo qualifica a "
            "conduta como contravenção penal e não se limita, pelo texto, à moradia. É preciso separar essa cobrança "
            "de caução regular, aluguel antecipado nas exceções legais e serviço que realmente caiba ao locatário."
        ),
        "sections": [
            section(
                "O artigo 43 proíbe valor sem causa locatícia permitida",
                "A norma alcança quantia exigida por motivo de locação ou sublocação além do aluguel e encargos "
                "permitidos. O nome usado — taxa de reserva, sinal, luva ou cadastro — não define a legalidade. "
                "Importam a causa, o destinatário, o recibo e se a cobrança corresponde a obrigação admitida.\n\n"
                "A caução em dinheiro é garantia, não preço de acesso: não pode exceder três meses de aluguel e deve "
                "seguir o artigo 38. Cobrança antecipada de aluguel só é admitida nas hipóteses legais, como locação "
                "sem garantia nos termos do artigo 42 e temporada. Misturar garantia e valor por fora dificulta a "
                "prestação de contas e pode revelar a infração."
            ),
            section(
                "O artigo 44 não tipifica genericamente toda luva",
                "O artigo 44 reúne crimes de hipóteses específicas. Seu inciso I trata da recusa de recibo pelo "
                "locador ou sublocador em habitação coletiva multifamiliar; os demais incisos alcançam retomada "
                "insincera e execução irregular de despejo. Ele não é fonte penal genérica para toda cobrança de "
                "quantia de entrada.\n\n"
                "Para a exigência além do aluguel e encargos, o enquadramento textual está no artigo 43, inciso I. "
                "A distinção é relevante porque contravenção e crime possuem elementos e regimes diferentes; uma "
                "página informativa não deve atribuir tipo penal sem conferir os fatos."
            ),
            section(
                "Taxa de cadastro do candidato é despesa do locador",
                "O artigo 22, inciso VII, atribui ao locador as taxas de administração imobiliária e de intermediação, "
                "incluindo despesas necessárias à aferição da idoneidade do pretendente ou de seu fiador. Por isso, "
                "não é correto normalizar a cobrança do candidato apenas porque uma imobiliária diz ter prestado "
                "análise cadastral.\n\n"
                "Outros serviços pedidos livremente pelo interessado precisam ser identificados e não podem servir "
                "para disfarçar custo que a lei entrega ao locador. Recibo e descrição do serviço são essenciais para "
                "avaliar quem cobrou e por qual fundamento."
            ),
            section(
                "Restituição em dobro não é automática",
                "Quem pagou deve preservar comprovante, mensagens, anúncio e identificação do recebedor. A cobrança "
                "indevida pode fundamentar pedido de restituição e outras consequências, mas a Lei 8.245/1991 não "
                "cria, nesse ponto, uma devolução civil automática em dobro. A repetição precisa indicar sua base "
                "jurídica e os fatos do pagamento.\n\n"
                "Notificação pode pedir devolução simples e prestação de contas, sem ameaça penal genérica. Se houver "
                "indícios concretos da contravenção, o registro perante a autoridade competente segue avaliação "
                "própria. A orientação jurídica deve separar recuperação patrimonial e persecução penal, sem garantir "
                "resultado em nenhuma das vias."
            ),
        ],
        "faq": [{
            "q": "A imobiliária pode repassar ao candidato a pesquisa de idoneidade?",
            "a": "O artigo 22, VII, coloca no locador as despesas necessárias à aferição da idoneidade do pretendente ou do fiador.",
        }],
        "official_sources": [
            source(LEI + "#art43", "Lei 8.245/1991, art. 43, I", "contravenção por exigir quantia além de aluguel e encargos permitidos"),
            source(LEI + "#art44", "Lei 8.245/1991, art. 44", "crimes locatícios de hipóteses específicas"),
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, VII", "custos de administração, intermediação e aferição de idoneidade"),
            source(CC + "#art876", "Código Civil, art. 876", "dever geral de restituir pagamento indevido"),
        ],
    },
    "imob-locacao-temporada-regras": {
        "opening": (
            "Locação para temporada é a residência temporária motivada por lazer, curso, tratamento de saúde, obra "
            "na moradia do locatário ou outro fato ligado a tempo determinado, por no máximo noventa dias. O artigo "
            "48 não exige que o imóvel seja mobiliado; se for, o contrato deve descrever móveis, utensílios e estado."
        ),
        "sections": [
            section(
                "Finalidade temporária e limite de noventa dias",
                "A qualificação não depende do título dado ao documento ou do uso da palavra 'diária'. O contrato "
                "deve revelar o motivo transitório e respeitar o teto legal. Uma ocupação residencial contínua "
                "fracionada artificialmente em instrumentos sucessivos pode ser examinada conforme sua realidade, "
                "sem que a simples assinatura de um segundo contrato produza resultado automático.\n\n"
                "Se houver mobília, o inventário obrigatório deve permitir comparar quantidade e conservação na "
                "entrada e na saída. Fotos podem complementar, mas não substituem a descrição contratual exigida."
            ),
            section(
                "O artigo 49 admite antecipação e garantia ao mesmo tempo",
                "Na temporada, o locador pode receber de uma só vez e antecipadamente aluguéis e encargos. Também "
                "pode exigir qualquer modalidade de garantia prevista no artigo 37 para as demais obrigações. "
                "Portanto, pagamento antecipado não elimina necessariamente caução, fiança ou seguro; a proibição "
                "de cumular mais de uma modalidade de garantia continua aplicável.\n\n"
                "Contrato e recibo devem separar aluguel, encargos e garantia. Caução em dinheiro continua sujeita "
                "ao limite e ao depósito previstos no artigo 38, e não pode ser confundida com nova parcela de preço."
            ),
            section(
                "A prorrogação só se presume depois de mais de 30 dias sem oposição",
                "Pelo artigo 50, terminado o prazo, a permanência por mais de 30 dias sem oposição do locador "
                "faz presumir prorrogação por prazo indeterminado, mantidas as condições ajustadas. A mudança não "
                "ocorre no primeiro dia posterior ao vencimento. A oposição comprovável antes desse marco impede "
                "tratar o silêncio como concordância.\n\n"
                "Prorrogada a relação, o locador deixa de poder exigir pagamento antecipado de aluguel e encargos. "
                "A denúncia dessa locação exige espera de trinta meses de seu início ou observância das hipóteses do "
                "artigo 47; não se recuperam as facilidades de temporada chamando a ocupação prorrogada de nova estadia."
            ),
        ],
        "faq": [{
            "q": "Na temporada é possível cobrar antecipadamente e ainda exigir caução?",
            "a": "Sim. O artigo 49 permite antecipar aluguel e encargos e exigir uma modalidade de garantia para as demais obrigações, sem autorizar cumular garantias.",
        }],
        "official_sources": [
            source(LEI + "#art48", "Lei 8.245/1991, art. 48", "finalidade, prazo e inventário da locação para temporada"),
            source(LEI + "#art49", "Lei 8.245/1991, art. 49", "antecipação de aluguel e encargos com garantia"),
            source(LEI + "#art50", "Lei 8.245/1991, art. 50", "prorrogação após mais de 30 dias sem oposição"),
        ],
    },
    "imob-temporada-hospede-nao-sai": {
        "opening": (
            "O vencimento do contrato de temporada não autoriza trocar fechaduras, retirar bens ou cortar acesso. "
            "O ocupante deve restituir o imóvel, e o locador precisa documentar oposição e usar a ação de despejo se "
            "não houver saída voluntária. Os primeiros trinta dias importam porque a lei oferece uma hipótese de "
            "liminar e, se a permanência superar esse período sem oposição, presume prorrogação por prazo indeterminado."
        ),
        "sections": [
            section(
                "Oposição comprovada evita a presunção do artigo 50",
                "Terminado o prazo, o locador deve comunicar de forma clara que não aceita a continuidade e exigir a "
                "entrega das chaves. Pelo artigo 50, a prorrogação só se presume quando o locatário permanece por mais "
                "de trinta dias sem oposição. Não basta contar trinta dias exatos e afirmar que o contrato já mudou; "
                "importam o tempo superior ao limite e a ausência de reação demonstrável.\n\n"
                "Notificação por meio que preserve conteúdo, envio e recebimento ajuda a provar a oposição. Aceitar "
                "novo pagamento sem ressalva, negociar uma extensão ou continuar tratando o ajuste como vigente pode "
                "produzir prova em sentido contrário e deve ser avaliado no contexto."
            ),
            section(
                "A liminar exige ação proposta em até trinta dias do vencimento",
                "O artigo 59, parágrafo 1º, inciso III, permite liminar para desocupação em quinze dias quando a ação "
                "decorre do término do prazo da locação para temporada e é proposta até trinta dias depois do "
                "vencimento. Como nas hipóteses do parágrafo 1º, há caução equivalente a três meses de aluguel. A "
                "medida não nasce apenas da notificação: requer processo, documentos e decisão judicial.\n\n"
                "Perder essa janela não extingue o direito de pedir despejo. Significa apenas que essa liminar "
                "específica pode não estar disponível. Se também existe falta de pagamento, a petição precisa "
                "distinguir os fundamentos e os requisitos de cada medida."
            ),
            section(
                "Prorrogação muda cobrança antecipada e forma de denúncia",
                "Se a permanência passa de trinta dias sem oposição, a locação se presume prorrogada por tempo "
                "indeterminado nas condições ajustadas. O artigo 50 retira então a exigibilidade do pagamento "
                "antecipado de aluguel e encargos. Para denunciar essa relação, o locador deve observar o prazo de "
                "trinta meses do início ou as hipóteses do artigo 47, em vez de tratá-la como mera hospedagem.\n\n"
                "A existência de plataforma, intermediação ou pagamento por noite não decide sozinha o regime. Se a "
                "operação inclui serviços regulares típicos de hospedagem, pode haver enquadramento diferente, que "
                "exige examinar contrato e atividade efetivamente prestada."
            ),
            section(
                "Documentos para a retomada e para o acerto financeiro",
                "Preserve o contrato com datas, inventário, comprovante de pagamento, mensagens sobre saída, "
                "notificação de oposição e prova de entrega. Registre também valores relativos ao período excedente "
                "sem chamá-los automaticamente de diária ou multa; a base de cobrança depende da relação reconhecida.\n\n"
                "Se houver dano, faça vistoria comparativa e orçamento separado. Receber as chaves não equivale a "
                "dar quitação de avarias, e a alegação de dano não autoriza manter o ocupante no imóvel. Uma triagem "
                "jurídica rápida é útil por causa da janela do artigo 59, mas não garante a concessão da liminar.\n\n"
                "Calcule separadamente aluguel contratual até o termo, eventual valor posterior e encargos de consumo. "
                "Não imponha multa diária criada depois do vencimento nem use a caução como pagamento definitivo sem "
                "prestação de contas. Se o ocupante oferece saída em data próxima, um acordo escrito pode fixar chaves, "
                "vistoria e valor sem renunciar genericamente a dano ainda desconhecido."
            ),
            section(
                "Autotutela cria um problema novo para o proprietário",
                "Desligar serviços essenciais, bloquear a entrada ou remover pertences sem ordem judicial pode "
                "violar a posse e gerar responsabilidade civil. Mesmo depois do vencimento, a retomada coercitiva "
                "segue o devido processo. Situação emergencial de risco físico deve ser tratada pelos canais públicos "
                "adequados, não como atalho locatício.\n\n"
                "A estratégia segura combina oposição escrita, tentativa documentada de entrega e, se necessário, "
                "ação de despejo. Isso preserva a discussão principal e evita que o modo de retomada se torne o "
                "centro do litígio. Síndico, porteiro ou plataforma não devem receber ordem para apreender pertences; "
                "a cooperação deles limita-se ao que a convenção, o contrato e uma decisão válida permitem."
            ),
        ],
        "faq": [{
            "q": "Passados trinta dias, o locador perde o direito de despejar?",
            "a": "Não. Pode perder a liminar específica ou enfrentar prorrogação, conforme oposição e datas, mas o direito de buscar a retomada pelas regras aplicáveis permanece.",
        }],
        "official_sources": [
            source(LEI + "#art50", "Lei 8.245/1991, art. 50", "prorrogação da temporada e fim da antecipação"),
            source(LEI + "#art59", "Lei 8.245/1991, art. 59, § 1º, III", "liminar por término da temporada dentro da janela legal"),
            source(LEI + "#art47", "Lei 8.245/1991, art. 47", "retomada após prorrogação da locação residencial"),
        ],
    },
    "imob-vaga-garagem-fora-lei-inquilinato": {
        "opening": (
            "A Lei 8.245/1991 exclui de seu regime as vagas autônomas de garagem e os espaços para estacionamento "
            "de veículos. O contrato isolado segue as regras gerais de locação de coisas do Código Civil, e não o "
            "rito especial de despejo. Além disso, a locação para pessoa estranha ao condomínio depende da "
            "autorização expressa da convenção."
        ),
        "sections": [
            section(
                "A exclusão está no artigo 1º da Lei do Inquilinato",
                "O texto legal não baseia a exclusão em uma avaliação abstrata de função social: ele enumera vagas "
                "autônomas e espaços de estacionamento. Quando a garagem integra a mesma locação do apartamento ou "
                "da loja, é preciso ler o objeto e a matrícula para saber se existe obrigação acessória dentro do "
                "contrato principal ou uma contratação autônoma. A resposta não deve ser presumida apenas porque os "
                "boletos chegam juntos."
            ),
            section(
                "O Código Civil disciplina uso, remuneração e restituição",
                "A partir do artigo 565, o locador cede uso e gozo por tempo e retribuição determinados. Prazo, "
                "forma de denúncia, regras de acesso e inadimplemento devem ser descritos com precisão. Sem a Lei do "
                "Inquilinato, não se aplicam automaticamente suas garantias, seus prazos ou a ação de despejo.\n\n"
                "A via judicial depende do pedido concreto, da posse e do contrato; não é correto anunciar que toda "
                "retomada será necessariamente reintegração. Cobrança, obrigação de entregar e tutela possessória "
                "possuem requisitos distintos."
            ),
            section(
                "Terceiro de fora precisa de autorização expressa da convenção",
                "O artigo 1331, parágrafo 1º, do Código Civil impede contrato da garagem com terceiro estranho ao "
                "condomínio, a menos que a convenção dê autorização expressa. "
                "Não é apenas uma faculdade genérica de o condomínio restringir: a autorização convencional é a "
                "exceção necessária para contratar com quem não pertence ao edifício.\n\n"
                "Também devem ser observados cadastro, acesso e regras de segurança aprovadas validamente. A "
                "autorização não dispensa o locatário de cumprir a convenção e não permite criar direito sobre área "
                "que não corresponde à vaga identificada."
            ),
            section(
                "Um contrato útil identifica o bem e o regime",
                "Informe número da vaga, pavimento, prazo, preço, controle de acesso, veículo autorizado e condição "
                "de encerramento. Anexe a cláusula da convenção relevante quando o usuário for externo. Se a vaga "
                "estiver vinculada à unidade, confira se pode ser explorada separadamente e quem possui legitimidade "
                "para contratar.\n\n"
                "Essa verificação documental evita usar notificação ou garantia típica da Lei 8.245/1991 em negócio "
                "excluído dela, sem prometer uma retomada sumária que o regime civil não oferece."
            ),
        ],
        "faq": [{
            "q": "A convenção pode autorizar aluguel para pessoa que não mora no prédio?",
            "a": "Sim. O artigo 1331, § 1º, exige autorização expressa da convenção para alugar vaga a pessoa estranha ao condomínio.",
        }],
        "official_sources": [
            source(LEI + "#art1", "Lei 8.245/1991, art. 1º, parágrafo único", "exclusão de vagas autônomas e espaços de estacionamento"),
            source(CC + "#art565", "Código Civil, art. 565", "regime geral da locação de coisas"),
            source(CC + "#art1331", "Código Civil, art. 1.331, § 1º", "autorização convencional para locação de garagem a terceiro"),
        ],
    },
    "imob-imovel-sem-habite-se-alugado": {
        "opening": (
            "A falta de habite-se é uma irregularidade administrativa relevante, mas não torna toda locação nula "
            "nem prova, sozinha, que o imóvel é materialmente impróprio. O nome, o procedimento e os efeitos do "
            "documento dependem da legislação municipal. Na relação locatícia, a questão central é se o bem atende "
            "ao uso contratado e se havia defeito ou impedimento que o locador deveria informar ou corrigir."
        ),
        "sections": [
            section(
                "Regularidade municipal e aptidão concreta não são sinônimos",
                "O artigo 22, inciso I, obriga o locador a disponibilizar o bem apto à finalidade ajustada; os "
                "incisos seguintes exigem uso pacífico, manutenção da forma e do destino e responsabilidade por "
                "defeitos anteriores. A ausência do documento pode indicar risco de fiscalização, restrição de uso "
                "ou obra não aprovada, mas é necessário obter informação oficial da prefeitura sobre aquela edificação.\n\n"
                "Em alguns municípios há certificados equivalentes, regularização parcial ou regras diferentes para "
                "imóveis antigos. Uma consulta genérica na internet não substitui certidão, processo administrativo "
                "ou resposta do órgão urbanístico competente."
            ),
            section(
                "Vício físico e falta documental precisam ser separados",
                "O artigo 441 do Código Civil disciplina vício oculto que torna a coisa imprópria "
                "ao uso ou reduz seu valor. Instalação insegura, risco estrutural ou impossibilidade comprovada de "
                "obter licença para a atividade podem sustentar pretensão contratual. A mera inexistência do habite-se, "
                "sem efeito concreto demonstrado, não deve ser apresentada como vício oculto automático.\n\n"
                "Também importa o conhecimento prévio. Se o locador omitiu uma interdição ou condição essencial, o "
                "caso é diferente daquele em que a documentação e os limites de uso foram claramente informados e o "
                "imóvel continua seguro para a finalidade permitida."
            ),
            section(
                "Possíveis medidas dependem do impacto e da prova",
                "Regularização, cumprimento de obrigação, abatimento, resolução sem multa e perdas e danos não são "
                "consequências intercambiáveis. O remédio depende da gravidade, da possibilidade de correção, da "
                "notificação e do nexo entre a irregularidade e o prejuízo. Não é prudente reduzir ou suspender o "
                "aluguel unilateralmente apenas após descobrir a falta documental.\n\n"
                "Se uma autoridade proíbe a ocupação, preserve o auto e a data. Se há apenas pendência cadastral, "
                "peça certidão e cronograma. Laudo técnico é adequado quando a controvérsia envolve segurança ou "
                "habitabilidade, e não apenas cadastro municipal."
            ),
            section(
                "Documentos mínimos para decidir o próximo passo",
                "Reúna contrato, anúncio, certidão municipal, plantas ou processo de regularização, comunicações e "
                "eventuais autos de fiscalização. Para uso comercial, acrescente licença de atividade e exigências "
                "específicas. O fato de contas de água ou energia existirem não comprova aprovação urbanística.\n\n"
                "Uma avaliação jurídica deve confrontar a regra local e o uso prometido, em vez de repetir uma solução "
                "nacional inexistente. Isso permite formular pedido proporcional sem afirmar que o contrato acabou "
                "ou que haverá indenização antes de demonstrar o impedimento."
            ),
        ],
        "faq": [{
            "q": "Descobrir a falta de habite-se autoriza parar de pagar aluguel?",
            "a": "Não automaticamente. É preciso apurar a regra municipal, o impacto sobre o uso e a medida jurídica adequada, evitando criar mora unilateral.",
        }],
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, I a IV", "aptidão para o uso, manutenção e defeitos anteriores"),
            source(CC + "#art441", "Código Civil, art. 441", "requisitos do vício oculto em contrato comutativo"),
        ],
    },
    "imob-caucao-morar-ultimo-mes": {
        "opening": (
            "A caução em dinheiro garante obrigações do contrato; ela não se converte automaticamente no último "
            "aluguel. Deixar de pagar sem acordo pode gerar mora, pois ainda não se sabe se haverá consumo, dano ou "
            "outro débito no acerto final. A compensação é possível quando as partes a formalizam ou quando estão "
            "presentes os requisitos legais de dívidas recíprocas, líquidas e vencidas."
        ),
        "sections": [
            section(
                "A lei manda depositar a caução em poupança",
                "O artigo 38, parágrafo 2º, limita a caução em dinheiro a três meses de aluguel e determina seu "
                "depósito em caderneta de poupança autorizada e regulamentada pelo poder público. Todas as vantagens "
                "da aplicação revertem ao locatário quando a soma é levantada. Não se trata de mera recomendação.\n\n"
                "Se o valor ficou na conta corrente do locador, a prestação de contas deve considerar o rendimento "
                "que a forma legal teria produzido. A garantia não pode ser confundida com taxa de entrada nem com "
                "aluguel antecipado."
            ),
            section(
                "Compensação unilateral pode deixar duas dívidas controvertidas",
                "O artigo 368 do Código Civil prevê compensação quando duas pessoas são, ao mesmo tempo, credora e devedora uma da "
                "outra em obrigações líquidas, vencidas e fungíveis. Antes da devolução das chaves e da vistoria, a "
                "restituição da caução pode ainda não estar vencida ou liquidada. Por isso, o inquilino que simplesmente "
                "omite o último aluguel não deve presumir quitação.\n\n"
                "O locador também não pode chamar qualquer orçamento de dano líquido e reter o valor inteiro. Precisa "
                "demonstrar a obrigação, considerar desgaste normal e devolver o saldo com os rendimentos."
            ),
            section(
                "Acordo deve prever aluguel, vistoria e diferença",
                "Se as partes desejam usar parte da garantia no mês final, o documento deve identificar competência, "
                "valor, data de entrega e como serão tratados consumo e danos ainda não apurados. Uma solução possível "
                "é reservar parcela até o fechamento das contas e definir prazo de restituição, sem dar quitação ampla "
                "antes da vistoria.\n\n"
                "Na ausência de acordo, o caminho conservador é pagar o aluguel no vencimento, devolver as chaves de "
                "modo comprovável e exigir prestação de contas da caução. Divergência posterior pode ser discutida sem "
                "fabricar inadimplência no fim do contrato."
            ),
            section(
                "Provas para o acerto final",
                "Guarde comprovante do depósito inicial, extrato ou informação da poupança, laudos de entrada e saída, "
                "recibos e leituras finais de consumo. A planilha deve separar aluguel, encargos, reparos e rendimento. "
                "Orçamento estimado não prova que o serviço foi necessário nem que o dano foi causado pelo locatário.\n\n"
                "Se não houver consenso, uma revisão documental pode calcular a parcela incontroversa e formular a "
                "cobrança ou defesa adequada, sem prometer devolução integral antes de fechar as obrigações."
            ),
        ],
        "faq": [{
            "q": "A caução em dinheiro precisa render durante a locação?",
            "a": "Sim. A lei exige depósito em poupança e manda reverter ao locatário todas as vantagens da aplicação por ocasião do levantamento.",
        }],
        "official_sources": [
            source(LEI + "#art38", "Lei 8.245/1991, art. 38, § 2º", "limite, depósito em poupança e rendimentos da caução"),
            source(CC + "#art368", "Código Civil, arts. 368 e 369", "requisitos da compensação de obrigações recíprocas"),
        ],
    },
    "imob-locador-faleceu-para-quem-pagar": {
        "opening": (
            "A morte do locador não extingue a locação: o artigo 10 transmite o vínculo aos herdeiros. O inquilino, "
            "porém, não deve escolher informalmente um familiar e presumir que pagou a todos. Enquanto inventário, "
            "representação do espólio e administração do imóvel são esclarecidos, é preciso exigir documento que "
            "identifique quem pode receber e usar consignação se houver dúvida real."
        ),
        "sections": [
            section(
                "O contrato continua, mas muda o polo do locador",
                "Direitos e obrigações passam aos sucessores; prazo, aluguel e deveres não são apagados pelo óbito. "
                "Isso também não torna o contrato imune às formas de término previstas em lei. Os sucessores podem "
                "exercer direitos do locador conforme a duração, o uso e as demais regras aplicáveis, mas não apenas "
                "invocar a morte para impor saída imediata.\n\n"
                "Se havia imobiliária, peça confirmação de que sua autorização para continuar recebendo permanece "
                "válida perante o espólio. O comprovante antigo não demonstra, sozinho, poderes posteriores ao óbito."
            ),
            section(
                "Inventariante ou representante deve demonstrar poderes",
                "Com inventário aberto, o inventariante normalmente representa o espólio, e a decisão de nomeação "
                "permite conferir sua condição. Antes disso, herdeiros podem apresentar escritura, autorização conjunta "
                "ou outra documentação adequada à sucessão. Pagamento a um herdeiro isolado, contestado pelos demais, "
                "pode não liberar integralmente a obrigação.\n\n"
                "Solicite instrução por escrito, dados bancários vinculados ao recebedor autorizado e recibo "
                "discriminado. Não aceite aumento, taxa ou alteração de vencimento como condição improvisada para "
                "informar a nova conta."
            ),
            section(
                "Dúvida legítima permite consignar, não simplesmente guardar",
                "O artigo 335 do Código Civil admite consignação quando existe dúvida sobre quem deve legitimamente "
                "receber. A medida exige depósito e procedimento adequados; separar o dinheiro em conta própria não "
                "produz o mesmo efeito. Se há processo de inventário conhecido, essa informação precisa constar da "
                "análise para que os interessados sejam chamados corretamente.\n\n"
                "Mantenha o cálculo e os vencimentos em ordem. A quitação dependerá da regularidade da consignação, "
                "não de uma promessa genérica de que qualquer depósito judicial elimina a mora."
            ),
            section(
                "Documentos que reduzem o risco de pagamento duplicado",
                "Preserve certidão de óbito apresentada, contrato, últimos recibos, comunicações dos sucessores, "
                "nomeação do inventariante e dados da imobiliária. Responda de forma transparente a todos que reclamam "
                "o crédito, sem compartilhar dados pessoais desnecessários.\n\n"
                "Quando as instruções divergem, uma avaliação jurídica pode identificar representante e preparar a "
                "consignação antes do próximo vencimento. O objetivo é continuar pagando ao credor legítimo, não "
                "transformar a sucessão em período gratuito de ocupação."
            ),
        ],
        "faq": [{
            "q": "Posso pagar ao primeiro herdeiro que enviar uma chave Pix?",
            "a": "Não é prudente sem prova de poderes ou concordância válida dos demais; pagamento à pessoa errada pode não quitar a obrigação perante o espólio.",
        }],
        "official_sources": [
            source(LEI + "#art10", "Lei 8.245/1991, art. 10", "transmissão da locação aos herdeiros do locador"),
            source(CC + "#art335", "Código Civil, art. 335, IV", "consignação diante de dúvida sobre o credor legítimo"),
        ],
    },
    "imob-reajuste-sem-clausula": {
        "opening": (
            "Sem cláusula de reajuste, nenhum índice entra automaticamente no contrato. A Lei 10.192/2001 limita "
            "a periodicidade da correção, mas não cria autorização unilateral onde as partes nada pactuaram. A Lei "
            "do Inquilinato permite inserir ou modificar a cláusula por acordo e, depois de três anos, buscar revisão "
            "judicial para adequar o aluguel ao mercado."
        ),
        "sections": [
            section(
                "Periodicidade anual não substitui a falta de pacto",
                "O artigo 2º da Lei 10.192/2001 admite reajuste por índices em contratos com duração igual ou superior "
                "a um ano e invalida periodicidade inferior à anual. Essa regra responde quando a correção pode "
                "produzir efeitos, não qual índice se aplica a um contrato omisso. IGP-M, IPCA ou outro indicador "
                "não pode ser escolhido depois por apenas uma parte.\n\n"
                "Também é preciso distinguir reajuste monetário de novo aluguel de mercado. Uma proposta de aumento "
                "real não se torna simples correção por usar um índice como justificativa."
            ),
            section(
                "O artigo 18 exige comum acordo para criar ou mudar a cláusula",
                "Locador e locatário podem fixar novo valor e inserir ou alterar cláusula de reajuste. O aditivo deve "
                "indicar índice, periodicidade válida e marco inicial, sem cobrar retroativamente uma correção que não "
                "existia. A aceitação precisa ser clara; silêncio ou pagamento feito sob ressalva não devem ser "
                "tratados automaticamente como concordância.\n\n"
                "Se houver negociação, compare valor de mercado, duração restante e efeito futuro. Um índice anual "
                "pactuado agora só opera segundo o novo ajuste, não reescreve vencimentos anteriores."
            ),
            section(
                "A revisão judicial exige três anos do contrato ou do último acordo",
                "O artigo 19 permite ao locador ou ao locatário pedir revisão depois de três anos de vigência do "
                "contrato ou do acordo anteriormente realizado. O objetivo é ajustar o valor ao preço de mercado, "
                "com contraditório e prova; não há aumento imediato apenas porque uma parte anunciou que ajuizará.\n\n"
                "Antes desse marco, podem existir outros fundamentos contratuais excepcionais, mas não se deve "
                "apresentar a ação revisional comum como disponível a qualquer tempo."
            ),
            section(
                "Recusa do valor contratado pede prova e via de pagamento segura",
                "O inquilino deve responder ao aumento por escrito e continuar oferecendo o montante efetivamente "
                "devido, com identificação do mês. Se o locador recusa receber esse valor, não basta retê-lo ou fazer "
                "pagamento informal: o artigo 67 disciplina a consignação judicial de aluguel e acessórios.\n\n"
                "Contrato, comunicação do aumento, comprovantes e cálculo permitem definir o valor correto. Uma "
                "análise jurídica pode organizar negociação ou defesa sem prometer que todo aumento será afastado, "
                "pois a existência de acordo posterior e o histórico de pagamentos também serão examinados."
            ),
        ],
        "faq": [{
            "q": "O IPCA entra automaticamente se o contrato não indicar índice?",
            "a": "Não. A cláusula pode ser inserida por acordo; sem consenso, a revisão do valor segue os requisitos e o prazo do artigo 19.",
        }],
        "official_sources": [
            source("https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10192.htm#art2", "Lei 10.192/2001, art. 2º", "periodicidade mínima anual da correção pactuada"),
            source(LEI + "#art18", "Lei 8.245/1991, art. 18", "acordo para novo aluguel ou cláusula de reajuste"),
            source(LEI + "#art19", "Lei 8.245/1991, art. 19", "revisão judicial depois de três anos"),
            source(LEI + "#art67", "Lei 8.245/1991, art. 67", "consignação quando o aluguel devido é recusado"),
        ],
    },
    "imob-notificacao-extrajudicial-locacao": {
        "opening": (
            "Notificação extrajudicial documenta uma comunicação fora do processo, mas não é requisito universal "
            "para terminar toda locação. A necessidade, o prazo e o efeito mudam conforme uso residencial ou não "
            "residencial, duração escrita e eventual prorrogação. Confundir esses regimes pode criar uma exigência "
            "inexistente ou omitir aviso que a lei realmente pede."
        ),
        "sections": [
            section(
                "Contrato residencial escrito de trinta meses termina sem aviso",
                "O caput do art. 46 dispensa aviso no contrato residencial cujo prazo pactuado por escrito é de 30 "
                "meses ou mais; o vínculo resolve-se no vencimento. Não é correto dizer que o "
                "locador precisa sempre notificar antes do vencimento para ajuizar despejo pelo término.\n\n"
                "Se o locatário permanece por mais de trinta dias sem oposição, ocorre prorrogação por prazo "
                "indeterminado. Nessa fase, o art. 46, parágrafo 2º, permite ao locador denunciar o contrato e "
                "concede trinta dias para desocupação. Aqui a comunicação tem função distinta: encerra uma relação "
                "já prorrogada, não valida o vencimento original."
            ),
            section(
                "Contrato residencial curto ou verbal segue o artigo 47",
                "Na locação residencial verbal ou escrita por menos de trinta meses, o fim do prazo não autoriza "
                "denúncia vazia imediata. A relação se prorroga automaticamente e a retomada depende das hipóteses "
                "enumeradas no artigo 47, inclusive uso próprio, infração ou vigência ininterrupta superior a cinco "
                "anos. Uma notificação com prazo 'razoável' não cria fundamento ausente na lei.\n\n"
                "A comunicação continua útil para provar oposição, pedido de reparo, exercício de direito ou fato "
                "que sustente a retomada. Seu conteúdo, porém, precisa corresponder a uma hipótese jurídica real."
            ),
            section(
                "Locação não residencial distingue vencimento e prorrogação",
                "O artigo 56 determina que o contrato não residencial por prazo determinado cessa no vencimento sem "
                "notificação ou aviso. Se o locatário permanece por mais de trinta dias sem oposição, presume-se "
                "prorrogação por tempo indeterminado. Nesse cenário, o artigo 57 autoriza denúncia escrita e fixa "
                "trinta dias para a entrega do imóvel.\n\n"
                "Por isso, citar o artigo 57 como se regesse qualquer imóvel residencial ou qualquer contrato ainda "
                "dentro do prazo troca o âmbito da norma. Primeiro se classifica uso e fase; depois se redige o aviso."
            ),
            section(
                "Conteúdo, entrega e prova devem servir ao efeito pretendido",
                "A notificação deve identificar partes, imóvel, contrato, fato comunicado, fundamento e prazo legal "
                "aplicável. Carta com aviso, cartório ou meio eletrônico podem produzir prova conforme o caso, desde "
                "que seja possível demonstrar conteúdo e recebimento. O contrato pode indicar canal, mas cláusula "
                "não afasta forma que a lei imponha para ato específico.\n\n"
                "Silêncio não é confissão universal nem elimina defesa. Ele pode integrar a prova ao lado de resposta, "
                "conduta e documentos. Uma revisão jurídica da minuta evita ameaça genérica e registra exatamente a "
                "consequência que poderá ser pedida, sem garantir que futura ação será acolhida."
            ),
        ],
        "faq": [{
            "q": "É preciso notificar antes do fim de contrato residencial escrito de trinta meses?",
            "a": "O caput do art. 46 dispensa aviso no vencimento; se a locação se prorrogar, a denúncia posterior concede 30 dias para desocupação.",
        }],
        "official_sources": [
            source(LEI + "#art46", "Lei 8.245/1991, art. 46", "fim sem aviso e denúncia após prorrogação residencial longa"),
            source(LEI + "#art47", "Lei 8.245/1991, art. 47", "retomada da locação residencial verbal ou curta"),
            source(LEI + "#art56", "Lei 8.245/1991, art. 56", "fim e prorrogação da locação não residencial"),
            source(LEI + "#art57", "Lei 8.245/1991, art. 57", "denúncia escrita da locação não residencial prorrogada"),
        ],
    },
    "imob-lei-inquilinato-abrangencia": {
        "opening": (
            "A Lei 8.245/1991 rege, em geral, locações de imóveis urbanos residenciais, não residenciais e para "
            "temporada. O artigo 1º também exclui negócios que permanecem sob o Código Civil ou legislação especial. "
            "Classificar corretamente o objeto evita aplicar despejo, garantia ou preferência a relação que segue "
            "outro regime."
        ),
        "sections": [
            section(
                "Locações urbanas abrangidas possuem capítulos diferentes",
                "Moradia, temporada e imóvel não residencial estão dentro da mesma lei, mas não compartilham todos "
                "os prazos. Contrato residencial escrito de trinta meses, ajuste verbal curto e locação comercial "
                "prorrogada possuem formas diferentes de término. A incidência da lei é apenas a primeira pergunta; "
                "depois vêm finalidade, forma, prazo e fase do vínculo.\n\n"
                "A lei também disciplina garantias, preferência na venda, benfeitorias e ações locatícias. Nenhum "
                "desses institutos deve ser transportado isoladamente para um negócio expressamente excluído."
            ),
            section(
                "O artigo 1º enumera as exclusões",
                "Sob o regime geral do artigo 565 do Código Civil ou de leis especiais ficam imóveis de propriedade da União, estados, municípios, "
                "autarquias e fundações públicas; vagas autônomas de garagem e espaços de estacionamento; espaços "
                "destinados à publicidade; e arrendamento mercantil. A redação deve ser lida literalmente antes de "
                "ampliar a lista por semelhança.\n\n"
                "Apart-hotéis, hotéis-residência e equiparados também são excluídos quando prestam serviços regulares "
                "aos usuários e estão autorizados a funcionar como tais. Não basta o prédio chamar uma unidade de "
                "flat nem existir administração hoteleira em tese; atividade, serviços e autorização precisam ser "
                "verificados."
            ),
            section(
                "Empresa estatal não aparece automaticamente na exclusão",
                "O dispositivo menciona entes federativos, autarquias e fundações públicas, mas não lista toda "
                "empresa pública ou sociedade de economia mista. A natureza do bem, o regime da entidade, a licitação "
                "e o contrato precisam ser examinados antes de concluir se a Lei do Inquilinato incide. Dizer apenas "
                "que todo patrimônio estatal segue direito público é amplo demais.\n\n"
                "Da mesma forma, locação feita pela administração como inquilina não se confunde com imóvel público "
                "dado em locação. Sujeito, titularidade e objeto ocupam posições diferentes na análise."
            ),
            section(
                "O contrato e os registros revelam o regime concreto",
                "Consulte matrícula, convenção, autorização administrativa e descrição dos serviços. Em vaga, veja "
                "se é autônoma e se terceiro externo foi autorizado; em flat, confira licença e operação efetiva; em "
                "leasing, identifique a estrutura financeira.\n\n"
                "Só depois escolha procedimento de cobrança ou retomada. Uma avaliação jurídica pode mapear o regime "
                "sem prometer que o rótulo contratual prevalecerá sobre a realidade e a documentação oficial."
            ),
        ],
        "faq": [{
            "q": "Imóvel de empresa pública está sempre fora da Lei do Inquilinato?",
            "a": "Não é uma conclusão automática do artigo 1º; é necessário verificar a entidade, a natureza do bem e o regime específico do contrato.",
        }],
        "official_sources": [
            source(LEI + "#art1", "Lei 8.245/1991, art. 1º", "âmbito e exclusões expressas da lei locatícia"),
            source(CC + "#art565", "Código Civil, art. 565", "regra geral da locação de coisas nas hipóteses cabíveis"),
        ],
    },
    "imob-imovel-devolvido-danificado": {
        "opening": (
            "O locatário deve devolver o imóvel no estado em que o recebeu, descontadas as deteriorações do uso "
            "normal. Cobrar dano exige comparar entrada e saída, demonstrar causa imputável ao ocupante e calcular "
            "reparo proporcional. Pintura envelhecida ou componente já depreciado não pode ser transformado, sem "
            "análise, em reforma integral paga pelo inquilino."
        ),
        "sections": [
            section(
                "O artigo 23 separa avaria de envelhecimento",
                "Furo excessivo, piso quebrado por impacto e alteração sem autorização podem exigir recomposição. "
                "Desbotamento, folga de ferragem e marcas compatíveis com tempo e material podem representar uso "
                "normal. Não existe lista que resolva todos os casos: estado inicial, duração, manutenção e causa "
                "precisam ser relacionados.\n\n"
                "Defeito estrutural, infiltração de origem externa ou vício anterior não muda de responsável apenas "
                "porque apareceu durante a ocupação. A comunicação feita ao locador e os reparos anteriores ajudam a "
                "identificar a origem."
            ),
            section(
                "Laudos comparáveis são mais úteis que fotografias isoladas",
                "A vistoria inicial deve localizar ambiente e item, descrever conservação e registrar imagens. Na "
                "saída, repita ângulo e identificação. Assinatura de ambas as partes fortalece a prova, mas sua "
                "ausência não torna automaticamente inútil todo registro nem transfere sozinho o ônus.\n\n"
                "Foto sem data, orçamento e declaração unilateral possuem pesos diferentes. Um orçamento prova o "
                "preço oferecido por um serviço, não necessariamente quem causou o problema. Para origem técnica, "
                "parecer ou perícia pode ser necessário."
            ),
            section(
                "O valor deve refletir reparo necessário e depreciação",
                "Discrimine material, mão de obra, área e motivo. Se reparo localizado restitui o estado devido, a "
                "troca completa precisa de justificativa. Substituir item antigo por novo pode exigir considerar "
                "idade e conservação para evitar enriquecimento. Dois orçamentos ajudam a comparar preço, sem criar "
                "regra legal de quantidade mínima.\n\n"
                "Notifique o ex-locatário, permita resposta e preste contas da caução. Retenção não deve superar a "
                "dívida demonstrada, e o saldo da garantia continua devido com as vantagens aplicáveis."
            ),
            section(
                "Aluguel perdido durante obra não é automático",
                "Os artigos 402 e 403 do Código Civil alcançam o que razoavelmente se deixou de lucrar como efeito "
                "direto e imediato do inadimplemento. Para cobrar indisponibilidade, o locador precisa provar que o "
                "dano imputável exigia a obra, qual era sua duração necessária e que houve perda concreta de renda. "
                "Não basta multiplicar qualquer prazo de reforma pelo último aluguel.\n\n"
                "Melhoria planejada, demora do próprio proprietário ou obra sem relação com a avaria não deve ser "
                "incluída. Oferta de nova locação, cronograma e notas do reparo podem integrar a demonstração."
            ),
            section(
                "Cobrança organizada evita misturar dano, consumo e aluguel",
                "Monte uma tabela com item, estado inicial, estado final, causa, orçamento, valor atribuído e fonte da "
                "prova. Separe contas de consumo e aluguéis vencidos. Envie a memória ao locatário antes de ajuizar e "
                "registre eventual proposta de reparo direto.\n\n"
                "Uma revisão jurídica dos laudos pode excluir desgaste e identificar lacunas probatórias. Isso não "
                "garante recuperação, mas permite cobrar apenas o que possui fundamento e evita usar a caução como "
                "confissão antecipada de todos os itens. O envio deve conceder oportunidade real de conferir fotos e "
                "valores; recusa de assinatura na vistoria pode ser registrada, mas não converte o laudo unilateral em "
                "verdade incontestável."
            ),
            section(
                "A falta de vistoria inicial não autoriza presunções absolutas",
                "Sem laudo de entrada, a prova fica mais difícil, mas o processo não se resolve automaticamente a favor "
                "de qualquer lado. Fotografias do anúncio, notas de reparos anteriores, mensagens, testemunhas e perícia "
                "podem ajudar a reconstruir o estado. Quem cobra continua precisando demonstrar fato constitutivo do "
                "direito, e o locatário pode provar vício preexistente ou desgaste.\n\n"
                "Também convém preservar a cadeia temporal depois da entrega. Se terceiros entram ou uma obra começa "
                "antes da vistoria, fica mais difícil atribuir a avaria ao antigo ocupante. Data das chaves, acesso ao "
                "imóvel e armazenamento dos arquivos devem ser registrados sem alterar as imagens originais. Se houver "
                "seguro ou garantia administrada por terceiro, cumpra o prazo de aviso da apólice sem descrever como "
                "coberto um dano que ainda depende de regulação. A negativa da seguradora também não transfere, por si, "
                "a responsabilidade ao locatário."
            ),
        ],
        "faq": [{
            "q": "Qualquer avaria autoriza reter toda a caução?",
            "a": "Não. A retenção depende de obrigação demonstrada e deve preservar o saldo; desgaste normal, depreciação e valores sem nexo precisam ser excluídos e discriminados no acerto final documentado entre as partes.",
        }],
        "official_sources": [
            source(LEI + "#art23", "Lei 8.245/1991, art. 23, III e V", "devolução, uso normal e reparação de danos causados"),
            source(CC + "#art402", "Código Civil, art. 402", "danos emergentes e lucros cessantes razoáveis"),
            source(CC + "#art403", "Código Civil, art. 403", "prejuízo direto e imediato decorrente do inadimplemento"),
        ],
    },
    "imob-golpe-anuncio-falso-aluguel": {
        "opening": (
            "No falso aluguel, alguém usa anúncio, identidade ou imóvel sem autorização para obter pagamento. Os "
            "fatos podem configurar estelionato e, quando a fraude utiliza contato eletrônico ou meio semelhante, "
            "exigem examinar também a forma qualificada do artigo 171. A prioridade prática é acionar imediatamente "
            "a instituição financeira, preservar evidências e registrar o fato, sem prometer que o valor será recuperado."
        ),
        "sections": [
            section(
                "Pix deve ser contestado pelo MED o quanto antes",
                "O Banco Central orienta a vítima a acionar o Mecanismo Especial de Devolução pelo aplicativo da "
                "instituição. O pedido pode ser registrado em até oitenta dias da transação fraudulenta, mas rapidez "
                "aumenta a chance de localizar e bloquear recursos. O banco do pagador registra a notificação e as "
                "instituições analisam os indícios.\n\n"
                "O MED não é estorno garantido. A devolução pode ser integral, parcial ou inexistente conforme a "
                "conclusão e os valores encontrados. Ele não se destina a mero desacordo comercial nem a Pix enviado "
                "por erro para pessoa de boa-fé. Em paralelo, o boletim de ocorrência é recomendável e documenta o "
                "relato para investigação."
            ),
            section(
                "Preserve o anúncio antes que ele desapareça",
                "Guarde URL, capturas completas, perfil, telefone, endereço de correio eletrônico, horários, comprovante e chave de pagamento. "
                "Exporte a conversa sem editar e registre a resposta da plataforma. Se houve visita, identifique quem "
                "abriu o imóvel e quais documentos foram apresentados. Não publique dados pessoais ou tente confrontar "
                "o suspeito presencialmente.\n\n"
                "Informe o anúncio à plataforma para preservação e bloqueio conforme seus canais. A vítima pode "
                "entregar a prova às autoridades; obtenção de dados protegidos do usuário ou da conta segue requisição "
                "e procedimento próprios."
            ),
            section(
                "Enquadramento penal depende do ardil e do meio usado",
                "O artigo 171 descreve a obtenção de vantagem ilícita mediante indução ou manutenção da vítima em erro. "
                "O parágrafo 2º-A trata da fraude eletrônica cometida com informações fornecidas pela vítima ou por "
                "terceiro induzido a erro por redes sociais, contatos telefônicos, correio eletrônico fraudulento ou meio análogo. "
                "Nem todo contrato frustrado é crime; é necessário demonstrar o artifício e a intenção fraudulenta.\n\n"
                "Essa distinção evita transformar desistência ou inadimplemento civil em estelionato sem prova, e "
                "também impede ignorar a modalidade eletrônica quando o falso anunciante construiu a fraude por canais "
                "digitais. A autoridade define o enquadramento a partir da investigação."
            ),
            section(
                "Responsabilidade civil de terceiros não é presumida",
                "Identificado o autor, o artigo 927 fundamenta reparação do dano causado por ato ilícito. Banco, "
                "plataforma, corretor ou titular de conta não responde automaticamente só porque apareceu no caminho "
                "do pagamento. É preciso examinar conduta, dever de segurança, falha específica, ciência e nexo.\n\n"
                "Reclamação ao Banco Central, Procon ou Judiciário pode ser cabível conforme o fornecedor e o problema "
                "não resolvido, mas não substitui o MED nem prova responsabilidade. Danos morais também não devem ser "
                "prometidos apenas pela existência do golpe."
            ),
            section(
                "Conta de terceiro e recuperação judicial exigem investigação",
                "O nome que aparece no comprovante é uma pista, não prova definitiva de autoria. A conta pode pertencer "
                "a participante, interposta pessoa ou vítima de outra fraude. Bloqueio, quebra de sigilo e identificação "
                "de beneficiários seguem competência e procedimento próprios; a vítima não deve divulgar CPF, telefone "
                "ou endereço para mobilizar perseguição privada.\n\n"
                "Se o MED não recupera tudo, documentos bancários e policiais podem subsidiar medida civil ou criminal. "
                "Antes de ajuizar contra alguém, é necessário relacionar sua conduta ao ardil e ao destino dos recursos. "
                "Uma ação apressada contra o mero titular aparente pode falhar por ilegitimidade ou falta de nexo. "
                "A cronologia deve registrar transferências conhecidas sem afirmar que todos os destinatários "
                "participaram conscientemente do golpe."
            ),
            section(
                "Verificações antes de transferir reduzem o risco",
                "Visite o imóvel ou faça videoconferência verificável, confira documento e matrícula atualizada e "
                "valide o corretor no conselho regional por canal oficial. Compare nome do recebedor com proprietário "
                "ou intermediário autorizado e desconfie de pressão por reserva imediata em conta de terceiro.\n\n"
                "Fotos reais não provam legitimidade: podem ter sido copiadas. Um contrato recebido minutos antes do "
                "Pix também não substitui confirmação da titularidade e dos poderes. Essas medidas não eliminam todo "
                "risco, mas criam pontos objetivos de verificação."
            ),
        ],
        "faq": [{
            "q": "O MED garante a devolução de um Pix feito ao falso locador?",
            "a": "Não. Ele instaura análise e bloqueio quando cabíveis, mas a restituição depende da confirmação da fraude e dos recursos localizados.",
        }],
        "official_sources": [
            source("https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm#art171", "Código Penal, art. 171 e § 2º-A", "estelionato e fraude eletrônica conforme o meio empregado"),
            source("https://bcb.gov.br/meubc/faqs/p/o-que-e-e-como-funciona-o-mecanismo-especial-de-devolucao-med", "Banco Central, Mecanismo Especial de Devolução", "prazo, análise, bloqueio e limites do MED no Pix"),
            source(CC + "#art927", "Código Civil, art. 927", "reparação civil condicionada a ato ilícito e dano"),
        ],
    },
    "imob-despejo-defesa-inquilino": {
        "opening": (
            "A defesa começa pela petição inicial e por eventual decisão liminar, não por uma lista genérica de "
            "argumentos. Falta de pagamento, término, infração e retomada possuem fatos e provas diferentes. Na "
            "cobrança de aluguel, a lei permite purgar a mora em condições estritas, mas não autoriza reter aluguel "
            "unilateralmente por defeito no imóvel nem afastar esse direito por simples renúncia contratual."
        ),
        "sections": [
            section(
                "Leia fundamento, pedidos, cálculo e fase processual",
                "O mandado pode trazer ordem de citação, liminar de quinze dias ou audiência. Obtenha a inicial, os "
                "documentos e a decisão para identificar datas e fundamento. A falta de notificação anterior não é "
                "defesa universal: em várias hipóteses o vencimento ou a mora decorrem do contrato e da lei; em outras, "
                "a comunicação é elemento específico da retomada.\n\n"
                "Comprovantes, recibos, aditivos, mensagens e laudos devem responder às alegações concretas. Negar uma "
                "dívida sem conferir competências e encargos pode ocultar pagamento parcial ou cobrança duplicada."
            ),
            section(
                "Purgação exige depósito completo em quinze dias",
                "O artigo 62, inciso II, permite ao locatário e ao fiador evitar a rescisão mediante depósito judicial, "
                "no prazo de quinze dias contado da citação, de aluguéis e acessórios vencidos, multas, juros, custas "
                "e honorários fixados em dez por cento se o contrato não dispuser de outro modo. O benefício não é "
                "admitido quando já utilizado nos vinte e quatro meses anteriores à ação.\n\n"
                "A proteção legal da purgação não pode ser afastada por renúncia contratual antecipada. Ela também não "
                "se confunde com contestação: pagar pode preservar a locação, enquanto a defesa discute fatos e direito "
                "nos limites cabíveis."
            ),
            section(
                "Diferença do depósito possui regra de complemento",
                "Se o locador alega insuficiência e indica o valor, o artigo 62, inciso III, permite complementar em "
                "dez dias contados da intimação, incluindo a diferença. Não se deve prometer que qualquer depósito "
                "parcial afasta o despejo nem afirmar que a primeira divergência elimina sempre a possibilidade de "
                "correção. O cálculo e a manifestação do credor precisam ser lidos.\n\n"
                "Valores incontroversos devem ser identificados. A estratégia entre purgar, contestar ou praticar "
                "ambos os atos depende do objetivo e do histórico do benefício, sem omitir o risco de liminar já "
                "concedida. Comprovante de pagamento realizado fora dos autos precisa ser confrontado com a planilha, "
                "pois transferência ao credor não substitui silenciosamente o depósito exigido pelo procedimento. "
                "Depósitos novos também devem observar as parcelas que vencem durante o processo."
            ),
            section(
                "Vício no imóvel não autoriza retenção unilateral do aluguel",
                "Defeito anterior, reparo urgente ou descumprimento do locador pode sustentar obrigação de fazer, "
                "abatimento, resolução ou indenização conforme prova. Não autoriza simplesmente parar de pagar e "
                "presumir compensação na contestação. Se o credor recusa o valor correto, o artigo 67 oferece "
                "consignação judicial de aluguel e acessórios; disputa sobre redução exige fundamento próprio.\n\n"
                "A consignação também não deve ser improvisada depois da mora com um total escolhido pelo inquilino. "
                "Causa da recusa, vencimentos e parcelas precisam ser demonstrados."
            ),
            section(
                "Benfeitorias e uso próprio exigem requisitos específicos",
                "Benfeitoria necessária pode gerar indenização e retenção pelo artigo 35, salvo disposição contratual "
                "em contrário; a Súmula 335 do STJ admite cláusula de renúncia. Isso impede tratar qualquer obra "
                "documentada como barreira automática ao despejo. Autorização, natureza e redação contratual importam.\n\n"
                "Se a retomada se baseia em uso próprio, a defesa confronta os pressupostos do artigo 47 e a prova da "
                "situação alegada. Não basta afirmar, sem elementos, que a necessidade é falsa. Cada tese precisa de "
                "documento ou fato que possa ser submetido ao contraditório."
            ),
            section(
                "Prazo de contestação deve ser calculado no processo",
                "O artigo 335 do CPC prevê marcos diferentes conforme audiência, pedido de cancelamento e forma de "
                "citação. A data exibida no mandado não deve ser convertida mecanicamente em prazo sem conferir "
                "juntada, calendário forense e decisão. Purgação, complemento e recurso podem ter contagens próprias.\n\n"
                "Busque acesso ao processo assim que a comunicação chegar, organize cálculo e prova por tópico e "
                "registre medidas já cumpridas. Atendimento jurídico remoto pode ser usado para triagem documental, "
                "mas nenhuma orientação responsável promete manter a posse antes de examinar decisão e fundamento."
            ),
        ],
        "faq": [{
            "q": "O contrato pode retirar antecipadamente o direito de purgar a mora?",
            "a": "Não. A faculdade legal do artigo 62 não pode ser afastada por simples renúncia contratual, embora seu uso seja limitado pelo período de vinte e quatro meses.",
        }],
        "official_sources": [
            source(LEI + "#art62", "Lei 8.245/1991, art. 62", "purgação, prazo, conteúdo do depósito e complemento"),
            source(LEI + "#art67", "Lei 8.245/1991, art. 67", "consignação de aluguel recusado"),
            source(LEI + "#art35", "Lei 8.245/1991, art. 35", "benfeitorias, retenção e disposição contratual"),
            source(CPC + "#art335", "Código de Processo Civil, art. 335", "marcos para apresentação da contestação"),
        ],
    },
    "imob-locador-desistiu-antes-entrega": {
        "opening": (
            "Contrato definitivo assinado normalmente obriga o locador a entregar o imóvel na data e nas condições "
            "ajustadas. Se ele comunica recusa inequívoca antes das chaves, pode haver inadimplemento e medidas para "
            "cumprimento ou resolução. Restituição e indenização, contudo, dependem do conteúdo do contrato, de "
            "eventuais condições pendentes e da prova de prejuízos diretos; dano moral não é consequência automática."
        ),
        "sections": [
            section(
                "Primeiro confirme se o instrumento é definitivo",
                "Proposta, reserva e minuta sem aceite podem não equivaler ao contrato concluído. Verifique assinaturas, "
                "data de início, condição de aprovação, garantia e obrigação de entrega. Condição suspensiva deve ser "
                "clara e ter ocorrido conforme o procedimento pactuado; o locador não pode inventar depois uma "
                "'aprovação cadastral' para escapar de vínculo já perfeito.\n\n"
                "O artigo 22, inciso I, obriga entregar o imóvel apto ao uso. Mensagem de correio eletrônico que anuncia proposta melhor a "
                "terceiro, recusa expressa ou nova locação podem demonstrar que o cumprimento foi abandonado."
            ),
            section(
                "Cumprimento e resolução possuem consequências diferentes",
                "Se a entrega ainda é possível e interessa ao locatário, pode haver pedido de cumprimento, inclusive "
                "medida urgente quando seus requisitos estiverem presentes. Se a confiança acabou ou o bem já foi "
                "destinado a terceiro, a resolução com restituição dos valores pode ser a resposta mais adequada. "
                "Nenhuma delas nasce de autotutela ou entrada forçada no imóvel.\n\n"
                "Formalize a recusa, fixe posição e preserve a prova. Aceitar devolução de caução não deve ser tratado "
                "automaticamente como quitação ampla se a mensagem registra reserva de outros prejuízos."
            ),
            section(
                "Danos materiais exigem nexo e documentação",
                "O artigo 389 impõe perdas e danos pelo inadimplemento, e os artigos 402 e 403 limitam a reparação ao "
                "que se perdeu e deixou razoavelmente de lucrar como efeito direto e imediato. Caução e aluguel pagos "
                "devem ser restituídos quando perdem causa. Mudança não reembolsável, hospedagem necessária e diferença "
                "temporária de outro aluguel podem ser examinadas com recibos e datas.\n\n"
                "A diferença de preço não se multiplica indefinidamente, e o prejudicado deve adotar medidas razoáveis "
                "para reduzir o dano. Despesa anterior sem relação com a recusa ou escolha muito mais cara sem "
                "justificativa pode ser contestada."
            ),
            section(
                "Dano moral não se presume de toda desistência",
                "Frustração e necessidade de procurar outro imóvel, isoladamente, não garantem reparação extrapatrimonial. "
                "Gravidade, proximidade da mudança, situação de vulnerabilidade, exposição e consequências concretas "
                "serão avaliadas. A página não deve transformar moradia frustrada em valor certo de indenização.\n\n"
                "Preserve comunicações e prova do impacto sem produzir exposição pública desnecessária. Negociação pode "
                "resolver restituição e gastos materiais, mas eventual quitação deve listar exatamente o que abrange."
            ),
            section(
                "Taxas, garantia e intermediação precisam de acerto próprio",
                "Caução recebida pelo locador perde sua finalidade se o imóvel não é entregue e deve integrar a "
                "restituição, com os rendimentos pertinentes quando em dinheiro. Aluguel cobrado por período que não "
                "começou também exige devolução. Já comissão paga diretamente a corretor pode envolver contrato de "
                "intermediação distinto; é preciso identificar quem contratou o serviço, quando o resultado útil ocorreu "
                "e qual foi a causa da frustração.\n\n"
                "Conforme o inciso VII do artigo 22, despesas de administração e intermediação ficam com o locador, mas "
                "isso não permite somar ao pedido qualquer despesa paga a terceiro sem examinar a relação. Recibos e "
                "cláusulas mostram quem deve restituir cada quantia e evitam cobrar o mesmo valor de duas pessoas. "
                "Também devem ser conferidos estornos, multa contratual e eventual sinal, porque cada rubrica possui "
                "causa e destinatário próprios. Quando houver pagamento parcelado, datas, recibos e beneficiários ajudam a "
                "separar o que foi recebido pelo locador do que remunerou serviço autônomo efetivamente concluído e comprovado."
            ),
            section(
                "Um dossiê curto permite decidir sem promessa",
                "Separe contrato, comprovantes, vistoria, data de entrega, mensagem de recusa, reserva de mudança e "
                "documentos da alternativa encontrada. Faça cronologia com valores e tentativas de solução. Se havia "
                "condição, inclua prova de seu cumprimento ou da razão da reprovação.\n\n"
                "Uma análise jurídica pode redigir notificação, avaliar cumprimento ou resolução e quantificar o dano "
                "defensável. O serviço deve explicar riscos e prova, sem anunciar liminar, entrega forçada ou indenização "
                "antes da resposta do locador e do exame judicial."
            ),
        ],
        "faq": [{
            "q": "Contrato assinado garante indenização por dano moral se as chaves não forem entregues?",
            "a": "Não automaticamente. O inadimplemento pode gerar restituição e danos materiais provados; dano moral depende da gravidade e das consequências concretas.",
        }],
        "official_sources": [
            source(LEI + "#art22", "Lei 8.245/1991, art. 22, I", "obrigação de entregar o imóvel apto ao uso"),
            source(CC + "#art389", "Código Civil, art. 389", "responsabilidade pelo inadimplemento"),
            source(CC + "#art402", "Código Civil, art. 402", "danos emergentes e lucros cessantes razoáveis"),
            source(CC + "#art403", "Código Civil, art. 403", "limite dos efeitos diretos e imediatos"),
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
    for item in page.get("sections", []):
        total += count(item.get("heading", "")) + count(item.get("text", ""))
    for item in page.get("faq", []):
        total += count(item.get("q", "")) + count(item.get("a", ""))
    return total


def merge_sources(previous, replacements):
    old = {item.get("url"): item for item in previous if item.get("url")}
    merged = []
    for replacement in replacements:
        current = dict(replacement)
        prior = old.get(current["url"], {})
        for field in ("verified_at", "http_status"):
            if field in prior:
                current[field] = prior[field]
        merged.append(current)
    return merged


def validate_band(page):
    bands = {
        "verbete": (350, 700),
        "pergunta": (400, 800),
        "guia_problema": (700, 1400),
        "procedimento": (500, 1000),
    }
    low, high = bands[page["page_type"]]
    if not low <= page["word_count"] <= high:
        raise RuntimeError(
            f"word_count fora da faixa em {page['intent_id']}: {page['word_count']} ({low}-{high})"
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

    tombstone = by_intent.get(TOMBSTONE_INTENT)
    if not tombstone or tombstone.get("skipped") is not True:
        raise SystemExit("tombstone municipal ausente ou materializado indevidamente")
    tombstone["skip_reason"] = TOMBSTONE_REASON

    for intent_id, update in UPDATES.items():
        page = by_intent[intent_id]
        for field in ("title", "meta_description", "h1", "opening", "sections", "faq"):
            if field in update:
                page[field] = update[field]
        if "official_sources" in update:
            page["official_sources"] = merge_sources(
                page.get("official_sources", []), update["official_sources"]
            )
        page["word_count"] = body_word_count(page)
        validate_band(page)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")

    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04.", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        with open(TARGET, "rb") as handle:
            current_sha = hashlib.sha256(handle.read()).hexdigest()
        if current_sha != EXPECTED_SHA256:
            raise SystemExit(f"CAS falhou antes da promoção: {current_sha}")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(f"corrigidas {len(UPDATES)} páginas; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
