#!/usr/bin/env python3
"""Conclui a revisão de quitação, atraso, renegociação e venda financiada."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "22c009a1367ba5d63c4ec98422049a63467f9268ef8585e58d59d6a382d8fe50"
LAW_9514 = "https://legis.senado.leg.br/norma/551390/publicacao/34619692"
LAW_14711 = "https://www2.camara.leg.br/legin/fed/lei/2023/lei-14711-30-outubro-2023-794873-normaatualizada-pl.html"
LAW_6015 = "https://legis.senado.leg.br/norma/547891/publicacao/34619429"
BCB_DDC = "https://www.bcb.gov.br/meubc/faqs/p/informacoes-e-documentos-exigidos-do-banco-para-quitar-ou-transferir-divida"


def words(value):
    plain = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", plain.lower(), re.UNICODE)


def body_word_count(page):
    values = [page.get("opening", "")]
    for section in page.get("sections", []):
        values.extend((section.get("heading", ""), section.get("text", "")))
    for item in page.get("faq", []):
        values.extend((item.get("q", ""), item.get("a", "")))
    return sum(len(words(value)) for value in values)


def source(page, url, name, anchor_claim):
    item = {"url": url, "name": name, "anchor_claim": anchor_claim}
    for previous in page.get("official_sources", []):
        if previous.get("url") == url:
            if "verified_at" in previous and "http_status" in previous:
                item["verified_at"] = previous["verified_at"]
                item["http_status"] = previous["http_status"]
            break
    return item


def update(page, *, title, meta, h1, opening, sections, faq, sources, links, lane):
    page.update({
        "title": title,
        "meta_description": meta,
        "h1": h1,
        "opening": opening,
        "sections": sections,
        "faq": faq,
        "official_sources": [source(page, *item) for item in sources],
        "internal_link_topics": links,
        "lane": lane,
    })
    page["word_count"] = body_word_count(page)
    if not 600 <= page["word_count"] <= 1400:
        raise SystemExit(f"{page['intent_id']}: faixa inesperada {page['word_count']}")


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_id = {page["intent_id"]: page for page in pages}

    update(
        by_id["imob-quitei-baixa-alienacao"],
        title="Quitação do financiamento e baixa da alienação fiduciária",
        meta="Entenda o termo de quitação em 30 dias, a multa legal pelo atraso e o cancelamento da propriedade fiduciária no registro de imóveis.",
        h1="Como cancelar a alienação fiduciária depois de quitar o imóvel",
        opening=(
            "A liquidação integral resolve a propriedade fiduciária, mas o registro não desaparece apenas porque a "
            "última parcela foi paga. O credor deve fornecer um termo de quitação e esse título permite ao registro "
            "de imóveis cancelar o gravame. A Lei 9.514/1997 fixa prazo e multa específicos para o primeiro passo; "
            "por isso, protocolo, documento correto e conferência da matrícula são mais úteis do que uma declaração "
            "genérica de que o contrato está encerrado."
        ),
        sections=[
            {
                "heading": "A quitação resolve a garantia, mas ainda falta refletir isso na matrícula",
                "text": (
                    "O art. 25 da Lei 9.514/1997 estabelece que o pagamento da dívida e dos encargos resolve a "
                    "propriedade fiduciária. Isso encerra a função da garantia, mas o registro anterior continua "
                    "produzindo efeitos enquanto não for cancelado. A Lei de Registros Públicos prevê que o "
                    "cancelamento é lançado por averbação e pode ser requerido pelo interessado com documento hábil.\n\n"
                    "Na alienação fiduciária, o documento indicado pela lei especial é o termo de quitação. Um "
                    "comprovante da última prestação ajuda a demonstrar o pagamento, porém não substitui, por si só, "
                    "o título que o art. 25 manda o credor emitir."
                ),
            },
            {
                "heading": "O credor tem 30 dias contados da liquidação",
                "text": (
                    "O prazo começa na data em que a dívida foi efetivamente liquidada, não na data em que o cliente "
                    "decidiu pedir a baixa. O § 1º do art. 25 inclui o devedor e, quando houver, o terceiro fiduciante "
                    "entre os destinatários do termo. Antes de contar o prazo, confirme se restaram encargo, diferença "
                    "de atualização, seguro ou lançamento pendente no demonstrativo final.\n\n"
                    "Guarde o comprovante da liquidação e o número do pedido. Se o documento não chegar, a cobrança "
                    "escrita deve identificar contrato, imóvel, data do pagamento e canal para entrega. Essa trilha "
                    "evita discussão posterior sobre quando a obrigação venceu."
                ),
            },
            {
                "heading": "O atraso gera multa legal de 0,5% ao mês ou fração",
                "text": (
                    "Desde a Lei 14.711/2023, o § 1º-A do art. 25 prevê multa de 0,5% ao mês, ou fração, sobre o valor "
                    "do contrato quando o termo não é disponibilizado dentro dos 30 dias. A quantia se reverte a quem "
                    "deveria receber o documento. Não se trata de percentual sobre o saldo já zerado.\n\n"
                    "A multa legal não autoriza presumir que todo atraso também produz dano moral ou qualquer outra "
                    "indenização. Uma pretensão adicional depende dos fatos e do prejuízo demonstrável. O primeiro "
                    "pedido deve buscar a entrega do termo e registrar precisamente o período de descumprimento."
                ),
            },
            {
                "heading": "Apresente o termo ao registro de imóveis competente",
                "text": (
                    "Com o termo, o interessado apresenta o pedido ao registro em que está a matrícula. O § 2º do "
                    "art. 25 determina que o oficial cancele o registro da propriedade fiduciária à vista da quitação. "
                    "A forma de apresentação, os emolumentos e eventuais exigências operacionais seguem a legislação "
                    "registral e as normas locais; não é seguro afirmar que sempre cabem ao banco ou sempre ao devedor.\n\n"
                    "Se houver exigência, peça nota escrita e verifique se ela trata de assinatura, representação, "
                    "identificação da matrícula ou outro elemento do título. Corrigir uma exigência individualizada é "
                    "mais eficaz do que reapresentar o mesmo arquivo sem saber por que foi recusado."
                ),
            },
            {
                "heading": "Confira a certidão depois do cancelamento",
                "text": (
                    "A etapa termina com a leitura de certidão atualizada, não apenas com recibo de protocolo. Confira "
                    "número da matrícula, descrição do imóvel, titularidade e ato de cancelamento. A certidão da situação "
                    "jurídica atualizada informa direitos, ônus e restrições vigentes e permite detectar erro antes de "
                    "uma venda, doação, inventário ou nova garantia.\n\n"
                    "Se o credor já entregou o termo e o problema está no registro, a providência muda: cumpra ou "
                    "conteste a exigência registral adequada. Se o termo continua retido depois do prazo, preserve a "
                    "prova e avalie cobrança administrativa ou judicial dirigida ao credor."
                ),
            },
        ],
        faq=[{
            "q": "A última parcela paga já basta para vender o imóvel como livre de gravame?",
            "a": (
                "Não é prudente concluir isso sem o cancelamento. A dívida pode estar liquidada, mas a matrícula "
                "continua exibindo a propriedade fiduciária até o ato registral baseado no termo de quitação."
            ),
        }],
        sources=[
            (LAW_9514, "Lei 9.514/1997, art. 25", "resolução da propriedade fiduciária, termo em 30 dias, multa de 0,5% e cancelamento registral"),
            (LAW_6015, "Lei 6.015/1973, arts. 19 e 248 a 252", "certidão imobiliária, averbação do cancelamento e efeitos do registro enquanto não cancelado"),
        ],
        links=["alienação fiduciária de imóvel", "venda de imóvel financiado", "portabilidade do financiamento imobiliário"],
        lane="informativa",
    )

    update(
        by_id["imob-atraso-quantas-parcelas-execucao"],
        title="Atraso no financiamento: quando pode começar a execução",
        meta="A lei não exige duas ou três parcelas: veja a carência contratual, o padrão de 15 dias e a intimação para purgar a mora.",
        h1="Quantas parcelas atrasadas permitem executar o imóvel financiado",
        opening=(
            "Não existe na Lei 9.514/1997 uma tolerância geral de duas, três ou quatro parcelas. Uma dívida vencida e "
            "não paga pode levar ao procedimento depois da carência aplicável. O contrato pode fixar esse intervalo; "
            "se for omisso, a lei hoje estabelece 15 dias. Só depois vem a intimação do registro de imóveis, que abre "
            "outro prazo de 15 dias para pagar o conjunto indicado no art. 26."
        ),
        sections=[
            {
                "heading": "O número de boletos não é o critério legal",
                "text": (
                    "O caput do art. 26 fala em dívida vencida e não paga, no todo ou em parte. Ele não condiciona a "
                    "cobrança extrajudicial ao acúmulo de um número mínimo de prestações. Assim, a pergunta correta é "
                    "quando termina a carência que impede a expedição da intimação, e não quantos boletos o mercado "
                    "costuma tolerar.\n\n"
                    "Uma política comercial mais paciente pode existir, mas não cria proteção permanente nem altera "
                    "o contrato. Sem documento oficial do credor para o caso concreto, não conte com a alegação de "
                    "que bancos sempre aguardam vários meses."
                ),
            },
            {
                "heading": "Leia a cláusula de carência; na omissão, o padrão é 15 dias",
                "text": (
                    "O § 2º do art. 26 permite que o contrato estabeleça o prazo de carência após o qual a intimação "
                    "será expedida. A Lei 14.711/2023 acrescentou regra objetiva para o silêncio contratual: sem prazo "
                    "convencionado, a carência é de 15 dias. Isso corrige a ideia de que a instituição pode protocolar "
                    "a intimação no dia seguinte em qualquer contrato.\n\n"
                    "Localize a cláusula de mora nas condições particulares e gerais. Registre o vencimento, pagamentos "
                    "parciais e eventual acordo. Um prazo contratual diferente precisa ser lido junto com a norma "
                    "vigente e com a data da operação."
                ),
            },
            {
                "heading": "A intimação abre 15 dias para purgar a mora",
                "text": (
                    "A requerimento do credor, o oficial do registro de imóveis intima o devedor e, se houver, o terceiro "
                    "fiduciante. A partir dessa intimação, o § 1º concede 15 dias para satisfazer a prestação vencida, "
                    "as que vencerem até o pagamento, juros, penalidades, encargos contratuais e legais, tributos, "
                    "condomínio imputável ao imóvel e despesas de cobrança e intimação.\n\n"
                    "Portanto, pagar apenas o boleto mais antigo pode não purgar a mora. Peça memória discriminada e "
                    "recibo do valor efetivamente recebido no procedimento. Se o montante tiver erro, a contestação "
                    "precisa apontar o lançamento e preservar o prazo, em vez de supor que a discussão o suspende."
                ),
            },
            {
                "heading": "Financiamento residencial tem uma etapa especial antes da consolidação",
                "text": (
                    "Nos financiamentos para aquisição ou construção do imóvel residencial do devedor, fora do sistema "
                    "de consórcio, o art. 26-A determina que a consolidação seja averbada 30 dias depois de expirar o "
                    "prazo para purgação. Até a averbação da consolidação, a lei assegura o pagamento das parcelas "
                    "vencidas e das despesas legalmente indicadas, fazendo o contrato convalescer.\n\n"
                    "Essa regra especial não transforma o atraso em período sem encargos e não deve ser transportada "
                    "automaticamente a imóvel comercial, crédito sem finalidade residencial ou consórcio. A finalidade "
                    "e a estrutura da operação precisam ser conferidas no instrumento."
                ),
            },
            {
                "heading": "Atue antes de depender da última data possível",
                "text": (
                    "No primeiro atraso, peça saldo atualizado, confirme endereço físico e eletrônico cadastrado e "
                    "protocole proposta realista. Negociação informal não impede o credor de prosseguir. Se já houver "
                    "intimação, anote data, forma de entrega, cartório, matrícula e composição do débito; são esses dados "
                    "que permitem avaliar pagamento, acordo ou vício concreto.\n\n"
                    "Não ignore correspondência nem edital esperando outra cobrança. O procedimento registral tem "
                    "efeitos próprios, e a ausência de uma ligação telefônica anterior não cria, sozinha, nulidade."
                ),
            },
        ],
        faq=[{
            "q": "Uma única parcela atrasada pode iniciar o caminho da consolidação?",
            "a": (
                "Pode haver requerimento após a carência aplicável, pois a lei não exige várias parcelas. Ainda assim, "
                "a consolidação depende da intimação e do decurso dos prazos e etapas previstos nos arts. 26 e 26-A."
            ),
        }],
        sources=[
            (LAW_9514, "Lei 9.514/1997, arts. 26 e 26-A", "dívida vencida, carência, intimação, purgação e regra especial do financiamento residencial"),
            (LAW_14711, "Lei 14.711/2023", "alterações atuais da carência padrão e do procedimento de alienação fiduciária imobiliária"),
        ],
        links=["intimação do cartório e purgação da mora", "renegociação do financiamento em atraso", "consolidação da propriedade e leilão"],
        lane="comercial",
    )

    update(
        by_id["imob-renegociar-financiamento-atraso"],
        title="Renegociar financiamento imobiliário atrasado com segurança",
        meta="Organize saldo, proposta e documentos sem confundir negociação com suspensão da mora ou direito automático a alongamento.",
        h1="Como negociar o financiamento atrasado antes da consolidação",
        opening=(
            "Negociar cedo pode reduzir encargos e ampliar as opções, mas a Lei 9.514/1997 não obriga o credor a "
            "conceder pausa, incorporar parcelas ou alongar o prazo. Essas mudanças dependem de aprovação e acordo "
            "formal. Enquanto a proposta está em análise, a mora e os prazos do procedimento continuam, salvo se o "
            "credor documentar suspensão, pagamento ou nova condição."
        ),
        sections=[
            {
                "heading": "Comece pelo saldo e pela fase exata do procedimento",
                "text": (
                    "Peça demonstrativo com principal, juros, multa, seguros, tributos, condomínio e despesas já "
                    "lançadas. Confirme se existe apenas cobrança administrativa, requerimento ao registro, intimação "
                    "cumprida ou consolidação averbada. A alternativa juridicamente disponível muda em cada etapa.\n\n"
                    "O Banco Central informa que o cliente pode solicitar os dados necessários para quitar ou transferir "
                    "a dívida, inclusive número do contrato, saldo atualizado, taxa, prazo e sistema de pagamento. Use "
                    "esses elementos para construir a proposta e conferir o valor, não como promessa de aprovação."
                ),
            },
            {
                "heading": "Pausa, incorporação e alongamento são possibilidades contratuais",
                "text": (
                    "Algumas instituições oferecem produtos que adiam prestações, incorporam vencidos ao saldo ou "
                    "aumentam o prazo. A existência de uma modalidade no site de um banco não cria regra para todos os "
                    "contratos. Elegibilidade, nova análise de renda, limite de prazo, origem dos recursos e garantia "
                    "podem excluir o pedido.\n\n"
                    "Compare a parcela proposta e o custo total. Incorporar atraso ao principal pode aliviar o caixa "
                    "agora, mas faz o valor renegociado integrar o fluxo futuro. Peça CET, planilha, novo vencimento e "
                    "efeito sobre seguros antes de aceitar."
                ),
            },
            {
                "heading": "Envie uma proposta que possa ser executada",
                "text": (
                    "Apresente renda atual, despesas essenciais, motivo da redução de capacidade e valor que pode ser "
                    "pago de entrada e por mês. Defina se pretende reduzir prestação, ganhar prazo ou vender o imóvel "
                    "com liquidação simultânea. Uma proposta numérica permite ao credor avaliar sustentabilidade e "
                    "evita acordo que volta a inadimplir no primeiro vencimento.\n\n"
                    "Toda concessão precisa aparecer no instrumento: parcelas abrangidas, encargos, vencimentos, "
                    "saldo, condição para interromper atos de cobrança e consequência do novo atraso. Promessa de "
                    "atendente ou protocolo de análise não equivale a novação nem a quitação."
                ),
            },
            {
                "heading": "Proposta pendente não suspende intimação nem consolidação",
                "text": (
                    "O art. 26 permite a intimação depois da carência aplicável e abre 15 dias para purgar a mora. "
                    "Se o financiamento se enquadrar na regra residencial do art. 26-A, ainda existe a janela especial "
                    "até a averbação da consolidação, mas o valor devido e as despesas precisam ser observados.\n\n"
                    "Não deixe um prazo vencer porque o aplicativo mostra solicitação em análise. Peça resposta escrita "
                    "e, se houver acordo, confirme com o registro ou com o credor quais atos foram efetivamente sustados. "
                    "Discussão sobre cálculo também não paralisa o procedimento por presunção."
                ),
            },
            {
                "heading": "Portabilidade ou venda podem ser comparadas, sem garantia de aceitação",
                "text": (
                    "Com os dados da dívida, outra instituição pode analisar uma portabilidade, e uma venda pode ser "
                    "estruturada para liquidar o saldo. Nenhuma dessas rotas obriga terceiro a conceder crédito nem "
                    "elimina o atraso enquanto não se concluir. Dívida já inadimplida, renda insuficiente ou fase "
                    "avançada do procedimento podem inviabilizar a operação na prática.\n\n"
                    "Compare prazos reais com a carência e com a intimação. Se a conta não fecha, uma orientação jurídica "
                    "individual deve examinar o contrato, a regularidade do procedimento e uma saída patrimonial possível, "
                    "sem prometer revisão ou liminar apenas para ganhar tempo."
                ),
            },
            {
                "heading": "Registre aceitação, pagamento e saldo remanescente",
                "text": (
                    "Depois do acordo, guarde o instrumento assinado, boletos, comprovantes e novo demonstrativo. "
                    "Verifique se os vencidos foram quitados, parcelados ou incorporados e se despesas cartorárias "
                    "continuam pendentes. Um acordo que só trata das prestações pode não eliminar custo já lançado no "
                    "procedimento.\n\n"
                    "Se o credor rejeitar a proposta, exija o saldo atualizado e decida a próxima medida antes do prazo "
                    "legal. A negativa, por si só, não prova abusividade; erro de cálculo, descumprimento de acordo ou "
                    "vício de intimação precisam ser demonstrados separadamente."
                ),
            },
        ],
        faq=[{
            "q": "O banco é obrigado a incorporar as parcelas atrasadas ao saldo?",
            "a": (
                "Não há esse direito geral na Lei 9.514/1997. A incorporação depende de política de crédito e acordo "
                "formal, e deve ser comparada pelo novo saldo, CET, prazo e parcela."
            ),
        }],
        sources=[
            (LAW_9514, "Lei 9.514/1997, arts. 26 e 26-A", "carência, intimação, purgação e limites temporais enquanto se negocia"),
            (BCB_DDC, "Banco Central, dados para quitar ou transferir dívida", "informações contratuais que o cliente pode pedir para avaliar quitação ou transferência"),
        ],
        links=["intimação do cartório e purgação da mora", "portabilidade do financiamento imobiliário", "venda de imóvel financiado"],
        lane="comercial",
    )

    update(
        by_id["imob-venda-imovel-financiado"],
        title="Venda de imóvel financiado: anuência, quitação e registro",
        meta="Veja como vender direitos sobre imóvel alienado, obter anuência expressa do credor e evitar riscos do contrato de gaveta.",
        h1="Como vender um imóvel ainda sujeito à alienação fiduciária",
        opening=(
            "É possível vender antes da quitação, mas o vendedor não pode tratar o imóvel como se estivesse livre. "
            "O art. 29 da Lei 9.514/1997 permite transmitir os direitos do fiduciante com anuência expressa do credor, "
            "e o adquirente assume as obrigações correspondentes. Outra estrutura possível usa o preço ou novo crédito "
            "para liquidar o saldo e cancelar a garantia. Ambas exigem participação documental do credor e coerência "
            "com a matrícula."
        ),
        sections=[
            {
                "heading": "O vendedor transmite direitos aquisitivos, não um imóvel livre",
                "text": (
                    "Na alienação fiduciária registrada, o credor detém a propriedade resolúvel em garantia e o devedor "
                    "mantém posse direta e direitos aquisitivos. Por isso, o objeto disponível antes da quitação não é "
                    "idêntico à propriedade plena sem ônus. A matrícula e o contrato mostram exatamente a garantia, "
                    "o titular e eventuais outras restrições.\n\n"
                    "Obtenha certidão atualizada e demonstrativo do saldo antes de fixar preço. Condomínio, tributos, "
                    "parcelas vencidas e despesas do financiamento influenciam quanto sobra para o vendedor e o que o "
                    "comprador precisará pagar."
                ),
            },
            {
                "heading": "A transmissão do art. 29 exige anuência expressa do credor",
                "text": (
                    "O art. 29 não autoriza simples comunicação posterior. A anuência deve ser expressa, e o adquirente "
                    "assume as obrigações ligadas aos direitos transmitidos. Na prática, o credor pode exigir cadastro, "
                    "análise de renda, documentos do negócio e instrumento próprio. A lei não garante que qualquer "
                    "candidato será aprovado.\n\n"
                    "O documento final deve identificar comprador, vendedor, contrato, saldo, data de corte e efeitos "
                    "sobre a responsabilidade do devedor anterior. Não presuma liberação apenas porque o comprador "
                    "começou a pagar; confirme o que o credor consentiu e o que foi levado ao registro."
                ),
            },
            {
                "heading": "A venda também pode liquidar o financiamento no fechamento",
                "text": (
                    "Em vez de assumir o contrato existente, o comprador pode usar recursos próprios ou crédito novo "
                    "para pagar o saldo do credor no fechamento. A coordenação deve prever valor atualizado, conta e "
                    "forma de pagamento, termo de quitação, cancelamento da propriedade fiduciária e registro da "
                    "transmissão. A Lei 9.514/1997 dá ao credor 30 dias após a liquidação para fornecer o termo.\n\n"
                    "Não entregue todo o preço ao vendedor esperando que ele quite depois. A estrutura documental pode "
                    "direcionar a parcela necessária ao credor e condicionar a liberação do restante aos títulos e "
                    "protocolos combinados."
                ),
            },
            {
                "heading": "Contrato de gaveta não altera sozinho o devedor perante o banco",
                "text": (
                    "Um instrumento particular sem anuência pode produzir obrigações entre vendedor e comprador, mas "
                    "não satisfaz o requisito do art. 29 perante o fiduciário. O financiamento e a matrícula permanecem "
                    "como estavam. Se o ocupante deixa de pagar, o credor cobra conforme o contrato registrado; se o "
                    "devedor formal falece, se divorcia ou sofre execução, o comprador informal enfrenta riscos que o "
                    "pagamento das parcelas não remove automaticamente.\n\n"
                    "Também há risco para o vendedor, cujo nome pode continuar vinculado ao débito. Recibos são prova "
                    "da relação privada, não substituto da anuência e do ato registral."
                ),
            },
            {
                "heading": "Prepare a operação em três trilhas coordenadas",
                "text": (
                    "Na trilha financeira, peça saldo, taxa, prazo e condições para liquidação ou transferência. Na "
                    "contratual, distribua entrada, despesas, posse, inadimplemento e devolução se o credor negar a "
                    "operação. Na registral, confira os títulos necessários, prenotação e matrícula final. Nenhuma "
                    "trilha deve pressupor que as outras se resolverão sozinhas.\n\n"
                    "Se houver sinal antes da análise do credor, discipline prazo, condição suspensiva e restituição. "
                    "Isso reduz a disputa quando o comprador não é aprovado ou o saldo real difere da estimativa."
                ),
            },
            {
                "heading": "Regularização tardia depende de consentimento atual",
                "text": (
                    "Quem já assinou contrato informal deve reunir instrumento, comprovantes, saldo e matrícula e "
                    "procurar o credor para uma solução formal. O tempo de pagamentos feitos pelo comprador não obriga "
                    "o banco a aceitar automaticamente a substituição. Pode ser necessário novo crédito, liquidação "
                    "ou ajuste entre as partes.\n\n"
                    "Uma revisão jurídica deve separar posse, pagamentos, dívida perante o credor e titularidade "
                    "registral. Prometer regularização simples sem examinar essas quatro posições pode aumentar o risco "
                    "de ambos os contratantes."
                ),
            },
        ],
        faq=[{
            "q": "O comprador pode assumir as parcelas sem falar com o banco?",
            "a": (
                "Ele pode pagar materialmente um boleto, mas isso não substitui a anuência expressa exigida pelo art. 29 "
                "nem o torna, por si só, devedor reconhecido pelo credor e titular na matrícula."
            ),
        }],
        sources=[
            (LAW_9514, "Lei 9.514/1997, arts. 25 e 29", "quitação da garantia e transmissão dos direitos do fiduciante com anuência expressa"),
            (LAW_6015, "Lei 6.015/1973", "efeitos do registro, matrícula, certidões e cancelamento por documento hábil"),
            (BCB_DDC, "Banco Central, dados para quitar ou transferir dívida", "informações para calcular saldo e comparar quitação ou transferência de crédito"),
        ],
        links=["alienação fiduciária de imóvel", "quitação e baixa da alienação fiduciária", "portabilidade do financiamento imobiliário"],
        lane="comercial",
    )

    encoded = "".join(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages).encode("utf-8")
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(hashlib.sha256(encoded).hexdigest())
    for intent_id in (
        "imob-quitei-baixa-alienacao",
        "imob-atraso-quantas-parcelas-execucao",
        "imob-renegociar-financiamento-atraso",
        "imob-venda-imovel-financiado",
    ):
        print(intent_id, by_id[intent_id]["word_count"])


if __name__ == "__main__":
    main()
