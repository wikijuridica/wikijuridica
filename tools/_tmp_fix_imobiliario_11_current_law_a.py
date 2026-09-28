#!/usr/bin/env python3
"""Atualiza a cadeia de mora, leilao e desocupacao da Lei 9.514/1997."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "fbc8c2fb3e0bd49bcf20c0f2543b2343828905569b1cc6f990da9051613133ed"
LAW_9514 = "https://www.planalto.gov.br/ccivil_03/leis/l9514.htm"
LAW_14711 = "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14711.htm"
THEME_1288 = (
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/"
    "19022026-Repetitivo-define-efeitos-da-quitacao-da-divida-em-imovel-com-"
    "alienacao-fiduciaria-apos-a-Lei-13-4652017.aspx"
)
REPOSSESSION = (
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2024/"
    "05072024-Acao-de-reintegracao-de-posse-de-imovel-com-alienacao-fiduciaria-"
    "nao-exige-previa-realizacao-de-leiloes.aspx"
)
OCCUPANCY = (
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2023/"
    "15022023-Terceira-Turma-afasta-aplicacao-do-CDC-e-nega-reducao-da-taxa-de-"
    "ocupacao-de-imovel-com-alienacao-fiduciaria.aspx/"
)


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
        if previous.get("url") != url:
            continue
        if "verified_at" in previous and "http_status" in previous:
            item["verified_at"] = previous["verified_at"]
            item["http_status"] = previous["http_status"]
        break
    return item


def update(page, *, title, meta, h1, opening, sections, faq, sources, links):
    page.update({
        "title": title,
        "meta_description": meta,
        "h1": h1,
        "opening": opening,
        "sections": sections,
        "faq": faq,
        "official_sources": [source(page, *item) for item in sources],
        "internal_link_topics": links,
        "lane": "comercial",
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
        by_id["imob-parei-pagar-financiamento"],
        title="Financiamento atrasado: da mora ao leilão do imóvel",
        meta="Entenda a intimação de 15 dias, a regra especial do imóvel residencial, a consolidação, os leilões e o risco de saldo após o atraso.",
        h1="O que acontece com o imóvel quando o financiamento atrasa",
        opening=(
            "O atraso não transfere o imóvel ao credor no dia seguinte, mas também não existe um número legal "
            "de parcelas que garanta espera. O contrato define a carência depois da qual o credor pode pedir a "
            "intimação pelo registro de imóveis. A partir daí, datas, espécie da operação e forma da comunicação "
            "determinam se ainda é possível manter o contrato ou se resta apenas adquirir o bem por preferência."
        ),
        sections=[
            {
                "heading": "O contrato define a carência antes da intimação",
                "text": (
                    "O art. 26 da Lei 9.514/1997 parte de dívida vencida e não paga, no todo ou em parte, e o "
                    "próprio contrato deve definir a carência para expedição da intimação. Uma única prestação "
                    "pode configurar mora se o instrumento permitir o início do rito; esperar duas, três ou mais "
                    "parcelas é uma política eventual do credor, não um direito do mutuário.\n\n"
                    "Antes do cartório, uma renegociação pode alterar vencimentos ou incorporar atrasos, mas só "
                    "produz esse efeito se for formalizada. Conversas telefônicas e propostas ainda não aceitas "
                    "não suspendem o procedimento nem substituem o pagamento previsto no contrato."
                ),
            },
            {
                "heading": "A intimação abre o prazo legal de 15 dias",
                "text": (
                    "A pedido do credor, o oficial intima o devedor e eventual terceiro fiduciante para pagar, em "
                    "15 dias, a prestação vencida, as que vencerem até o pagamento, juros, penalidades, encargos "
                    "legais, tributos, contribuições condominiais imputáveis ao imóvel e despesas de cobrança e "
                    "intimação. O valor não se resume às parcelas originalmente atrasadas.\n\n"
                    "A certidão indica quando e como a ciência ocorreu. Se a comunicação foi por edital, o prazo "
                    "parte da última publicação. A contagem concreta deve considerar a certidão e o calendário do "
                    "serviço registral; confiar apenas na data impressa por um banco pode fazer perder a janela."
                ),
            },
            {
                "heading": "Imóvel residencial do devedor tem regra especial até a consolidação",
                "text": (
                    "No financiamento destinado à aquisição ou construção do imóvel residencial do próprio "
                    "devedor, fora do sistema de consórcio, o art. 26-A permite pagar as parcelas vencidas e as "
                    "despesas até a averbação da consolidação. Essa extensão não deve ser aplicada automaticamente "
                    "a uma garantia residencial oferecida para outro empréstimo nem a qualquer imóvel de moradia.\n\n"
                    "O primeiro passo é conferir a finalidade declarada no contrato e a matrícula. Se a operação "
                    "não se enquadra na regra especial, ultrapassar os 15 dias sem purgação permite seguir para a "
                    "consolidação nos termos gerais."
                ),
            },
            {
                "heading": "Depois da consolidação não se reativa o contrato pelo atraso",
                "text": (
                    "A averbação da consolidação muda a posição jurídica. Para situações regidas pela Lei "
                    "13.465/2017, o Tema 1.288 do STJ afirma que não cabe purgar a mora depois desse marco: o antigo "
                    "devedor conserva o direito de preferência para adquirir o imóvel até a realização do segundo "
                    "leilão, pagando dívida, despesas e custos da nova aquisição.\n\n"
                    "Isso é diferente de depositar apenas prestações vencidas e continuar o financiamento. Casos "
                    "com consolidação e pagamento anteriores à mudança legislativa têm disciplina transitória e "
                    "precisam ser situados pela data dos atos, não somente pela data da assinatura do contrato."
                ),
            },
            {
                "heading": "Os leilões e o saldo dependem da finalidade do crédito",
                "text": (
                    "Consolidada a propriedade, o primeiro leilão deve ser promovido em até 60 dias; frustrado, o "
                    "segundo ocorre nos 15 dias seguintes. Nas operações residenciais especiais do art. 26-A, a "
                    "falta de lance que alcance dívida e encargos extingue o débito com quitação recíproca. Fora "
                    "dessa hipótese, a Lei 14.711/2023 admite cobrança do saldo remanescente.\n\n"
                    "Por isso, a frase de que entregar o imóvel sempre quita tudo está errada. Finalidade do "
                    "financiamento, valor da arrematação e despesas do rito precisam ser identificados antes de "
                    "calcular eventual sobra ou dívida restante."
                ),
            },
            {
                "heading": "Documentos para agir antes que a fase mude",
                "text": (
                    "Reúna contrato e aditivos, matrícula, extrato do saldo, comprovantes, requerimento do credor, "
                    "certidão de intimação e editais. Peça ao cartório cópia do procedimento e memória discriminada "
                    "do valor de purgação. Protocolos de acordo também importam, embora não suspendam o rito sem "
                    "aceitação ou decisão específica.\n\n"
                    "Um advogado pode verificar enquadramento no art. 26-A, regularidade da ciência e cálculo. A "
                    "análise deve ocorrer com a data exata em mãos; prometer anulação ou renegociação sem ler o "
                    "procedimento ignora o estágio que define a medida ainda disponível."
                ),
            },
        ],
        faq=[{
            "q": "Quantas parcelas atrasadas permitem iniciar a execução?",
            "a": (
                "A lei não fixa um número único. O contrato define a carência para a intimação e até uma parcela "
                "pode bastar, conforme o instrumento; a prática de o banco esperar mais não cria garantia legal."
            ),
        }],
        sources=[
            (LAW_9514 + "#art26", "Lei 9.514/1997, arts. 26 a 27", "mora, intimação, consolidação e leilões da garantia fiduciária"),
            (LAW_14711, "Lei 14.711/2023", "regra residencial especial, prazo de 60 dias e tratamento do saldo remanescente"),
            (THEME_1288, "STJ, Tema 1.288", "após a consolidação regida pela Lei 13.465/2017 resta direito de preferência, não purgação da mora"),
        ],
        links=["purgação da mora em 15 dias", "direito de preferência após consolidação", "primeiro e segundo leilão"],
    )

    update(
        by_id["imob-purgacao-mora-15-dias"],
        title="Purgação da mora: o que pagar nos 15 dias do cartório",
        meta="Saiba quando começa o prazo de purgação, quais parcelas e encargos entram na guia e quando a regra residencial permite pagar até a consolidação.",
        h1="Como conferir e pagar a purgação da mora no registro de imóveis",
        opening=(
            "A intimação do registro de imóveis não cobra apenas a primeira parcela em atraso. Ela abre uma etapa "
            "formal para restabelecer o contrato mediante pagamento do conjunto previsto em lei. Conferir a "
            "certidão, a finalidade do financiamento e a memória de cálculo é mais seguro do que contar quinze "
            "dias a partir da carta do banco ou pagar um boleto sem saber se o cartório registrou a quitação."
        ),
        sections=[
            {
                "heading": "O marco de contagem está na intimação certificada",
                "text": (
                    "O art. 26, § 1º, fixa prazo de 15 dias para satisfazer a mora. Na ciência pessoal ou postal, "
                    "a certidão do oficial documenta o recebimento; se a via excepcional for edital, a contagem "
                    "parte da última publicação. A data do primeiro atraso e a data de emissão de uma cobrança "
                    "bancária não substituem esse marco.\n\n"
                    "Peça cópia da certidão e identifique feriados ou indisponibilidades do serviço antes de "
                    "definir o último dia. A forma de contagem pode ser controvertida no caso concreto, de modo que "
                    "deixar o pagamento para o limite aumenta o risco de compensação ou protocolo tardio."
                ),
            },
            {
                "heading": "A guia inclui vencidas, vincendas no período e despesas",
                "text": (
                    "Devem entrar a prestação vencida e aquelas que vencerem até o pagamento, além dos juros "
                    "convencionais, penalidades, encargos contratuais e legais, tributos, cotas condominiais "
                    "imputáveis ao imóvel e despesas de cobrança e intimação. Pagar somente o principal indicado "
                    "num extrato antigo pode deixar diferença e impedir a purgação.\n\n"
                    "A planilha precisa discriminar cada rubrica e sua data. Encargo questionável não desaparece "
                    "porque foi incluído pelo credor, mas uma impugnação sem pagamento ou medida judicial não "
                    "interrompe automaticamente o procedimento. É preciso escolher uma estratégia que preserve o "
                    "prazo enquanto o cálculo é conferido."
                ),
            },
            {
                "heading": "O pagamento deve chegar ao procedimento registral",
                "text": (
                    "A lei prevê a purgação no registro de imóveis e o repasse ao credor. Siga a guia e o canal "
                    "formal indicados pelo oficial, exija protocolo e confirme que o valor foi vinculado à matrícula "
                    "correta. Um boleto fornecido pelo banco só resolve a etapa se o pagamento for reconhecido no "
                    "procedimento dentro do prazo.\n\n"
                    "Depois da purgação regular, o contrato convalesce e o oficial entrega as quantias ao credor, "
                    "deduzidas as despesas de cobrança e intimação. Guarde guia, comprovante, certidão e extrato "
                    "posterior que demonstre a continuidade do financiamento."
                ),
            },
            {
                "heading": "A regra residencial pode ampliar a janela antes da averbação",
                "text": (
                    "Para financiamento de aquisição ou construção do imóvel residencial do devedor, excetuado "
                    "consórcio, o art. 26-A assegura o pagamento das parcelas vencidas e despesas até a data da "
                    "averbação da consolidação. Não se trata de prorrogação universal para todo empréstimo que use "
                    "uma casa como garantia.\n\n"
                    "É necessário provar a finalidade da operação e verificar se a consolidação já entrou na "
                    "matrícula. A confirmação deve vir do registro atualizado, pois uma negociação paralela com o "
                    "credor não revela, sozinha, se o ato já foi averbado."
                ),
            },
            {
                "heading": "Consolidação posterior à Lei 13.465 muda o remédio",
                "text": (
                    "O Tema 1.288 do STJ separou as situações no tempo. Quando a propriedade foi consolidada sob o "
                    "regime posterior e a mora não havia sido purgada, não se retoma o contrato pagando apenas o "
                    "atraso; resta o direito de preferência para adquirir o imóvel nos termos do art. 27, § 2º-B.\n\n"
                    "Casos anteriores em que a purgação já havia ocorrido podem envolver ato jurídico perfeito. "
                    "Data da consolidação, data do pagamento e lei vigente em cada ato são documentos essenciais, "
                    "não detalhes que possam ser presumidos pelo ano do financiamento."
                ),
            },
            {
                "heading": "Checklist para revisar a cobrança sem perder o prazo",
                "text": (
                    "Compare contrato, extrato, planilha da intimação, comprovantes recentes e certidão da "
                    "matrícula. Verifique prestações que venceram durante a janela, multa, juros, tributos, condomínio "
                    "e custos cartorários. Solicite correção por escrito ao credor e ao oficial quando houver erro "
                    "identificável.\n\n"
                    "Se a divergência ameaçar a consolidação, um advogado pode avaliar pagamento com ressalva, "
                    "consignação ou tutela adequada aos fatos. Nenhuma dessas vias é automática; a prova do valor "
                    "disponível e da irregularidade alegada precisa acompanhar o pedido."
                ),
            },
        ],
        faq=[{
            "q": "Basta pagar as parcelas que estavam vencidas no dia da intimação?",
            "a": (
                "Não. A lei inclui também as prestações que vencerem até a data do pagamento e os encargos e "
                "despesas especificados no art. 26, § 1º."
            ),
        }],
        sources=[
            (LAW_9514 + "#art26", "Lei 9.514/1997, art. 26", "prazo, composição da purgação, forma da intimação e pagamento no registro"),
            (LAW_14711, "Lei 14.711/2023", "redação atual dos arts. 26 e 26-A e regime especial residencial"),
            (THEME_1288, "STJ, Tema 1.288", "efeitos temporais da consolidação sobre purgação e direito de preferência"),
        ],
        links=["intimação por edital", "direito de preferência após consolidação", "atraso no financiamento"],
    )

    update(
        by_id["imob-pagar-divida-ate-leilao"],
        title="Após a consolidação: preferência para adquirir o imóvel",
        meta="Entenda por que pagar só o atraso não reativa o financiamento após a consolidação e como funciona a preferência até o segundo leilão.",
        h1="Direito de preferência depois da consolidação da propriedade",
        opening=(
            "Depois que a consolidação é averbada, o devedor não conserva uma segunda purgação da mora sob as "
            "regras atuais. Ele pode exercer preferência para adquirir o imóvel antes do segundo leilão, mas o "
            "preço inclui a dívida e diversos custos de transferência. Tratar isso como simples quitação das "
            "parcelas atrasadas cria uma expectativa incompatível com a Lei 9.514/1997 e com o Tema 1.288 do STJ."
        ),
        sections=[
            {
                "heading": "Consolidação encerra a possibilidade de apenas curar o atraso",
                "text": (
                    "No regime posterior à Lei 13.465/2017, uma vez consolidada a propriedade sem purgação anterior, "
                    "o pagamento das prestações vencidas não restabelece o contrato. O Tema 1.288 do STJ fixou que "
                    "o devedor passa a ter somente a preferência prevista no art. 27, § 2º-B.\n\n"
                    "A matrícula atualizada mostra a data da averbação. Consultar apenas o aplicativo do banco ou "
                    "um boleto em aberto não esclarece se a posição registral já mudou, e a medida correta depende "
                    "precisamente desse marco."
                ),
            },
            {
                "heading": "A preferência pode ser exercida até o segundo leilão",
                "text": (
                    "Da consolidação até a data de realização do segundo leilão, o antigo fiduciante pode adquirir "
                    "o imóvel pelo preço legal. Não é necessário vencer uma disputa de lances, mas o exercício deve "
                    "ser formalizado antes do limite e seguir o procedimento indicado pelo credor e pelo registro.\n\n"
                    "Data, horário e local dos leilões devem ser comunicados aos endereços constantes do contrato, "
                    "inclusive o eletrônico. Obter edital e comprovantes de comunicação permite calcular a janela "
                    "sem depender de informação oral do atendimento bancário."
                ),
            },
            {
                "heading": "O preço é maior que o saldo mostrado no extrato",
                "text": (
                    "A conta reúne dívida, despesas, prêmios de seguro, encargos legais, condomínio e tributos, "
                    "inclusive ITBI e eventual laudêmio pagos na consolidação. Também cabem os custos da cobrança e "
                    "do leilão. Como se trata de nova aquisição, o fiduciante assume ainda tributos, custas e "
                    "emolumentos exigíveis para transferir o imóvel de volta.\n\n"
                    "Por isso, o valor de preferência não corresponde ao atraso nem necessariamente ao saldo "
                    "devedor isolado. A memória deve separar rubricas, datas e comprovantes para que cobranças sem "
                    "base possam ser contestadas de forma específica."
                ),
            },
            {
                "heading": "Casos antigos exigem linha do tempo própria",
                "text": (
                    "O Tema 1.288 preservou situações anteriores à Lei 13.465/2017 em que a propriedade já estava "
                    "consolidada e a mora havia sido purgada segundo o regime então aplicável. Para os atos "
                    "posteriores, a data de celebração do contrato não mantém, por si só, a disciplina antiga.\n\n"
                    "Contrato antigo, portanto, não significa automaticamente direito atual de reativação. É "
                    "necessário cruzar vigência da lei, consolidação e eventual pagamento já realizado."
                ),
            },
            {
                "heading": "Como formalizar a intenção e conferir o valor",
                "text": (
                    "Solicite por escrito ao credor a memória do preço de preferência, o canal de pagamento, os "
                    "documentos de consolidação e os editais. Protocole a manifestação de interesse sem aguardar o "
                    "último dia e peça confirmação sobre despesas que continuam sendo acrescidas.\n\n"
                    "Se houver recusa de informação, rubrica sem prova ou risco de realização do segundo leilão, um "
                    "advogado pode avaliar a medida adequada. O pedido precisa demonstrar capacidade de cumprir o "
                    "preço legal; alegar apenas intenção de pagar as parcelas vencidas não equivale ao exercício da "
                    "preferência."
                ),
            },
            {
                "heading": "Depois do segundo leilão a preferência deixa de existir",
                "text": (
                    "O limite legal é a realização do segundo leilão, e não uma fase indefinida até a revenda do "
                    "imóvel pelo credor. Depois disso, eventual discussão se volta à regularidade dos atos, à "
                    "destinação do produto da venda e ao saldo, conforme a espécie do financiamento.\n\n"
                    "Intimação inválida, preço abaixo do piso ou erro de cálculo podem justificar análise judicial, "
                    "mas não recriam automaticamente a oportunidade de compra. A proteção de terceiro e as regras "
                    "de perdas e danos também dependem do momento e da modalidade da operação."
                ),
            },
        ],
        faq=[{
            "q": "Após a consolidação, posso pagar apenas as parcelas atrasadas?",
            "a": (
                "No regime posterior à Lei 13.465/2017, não. Se não houve purgação antes da consolidação, resta a "
                "preferência para nova aquisição pelo preço completo do art. 27, § 2º-B."
            ),
        }],
        sources=[
            (LAW_9514 + "#art27", "Lei 9.514/1997, art. 27, § 2º-B", "prazo e componentes do preço no direito de preferência"),
            (LAW_14711, "Lei 14.711/2023", "redação atual da preferência e despesas incluídas na nova aquisição"),
            (THEME_1288, "STJ, Tema 1.288", "distinção entre purgação anterior e direito de preferência após a consolidação"),
        ],
        links=["purgação da mora", "primeiro e segundo leilão", "saldo após o leilão"],
    )

    update(
        by_id["imob-leilao-extrajudicial-como-funciona"],
        title="Leilão extrajudicial do imóvel: primeira e segunda etapas",
        meta="Veja o prazo de 60 dias, os pisos dos dois leilões, a comunicação ao devedor e a diferença entre financiamento residencial e outras dívidas.",
        h1="Como funcionam os dois leilões após a consolidação",
        opening=(
            "A Lei 14.711/2023 mudou pontos centrais do leilão da alienação fiduciária. O primeiro deve ocorrer em "
            "até 60 dias da consolidação, e não mais em 30. No segundo, o piso e o destino do saldo variam conforme "
            "a finalidade do financiamento. Ler apenas o valor da dívida ou repetir a regra anterior à reforma "
            "pode levar a uma conclusão errada sobre arrematação, quitação e cobrança posterior."
        ),
        sections=[
            {
                "heading": "O primeiro leilão deve ser promovido em até 60 dias",
                "text": (
                    "O prazo conta do registro da consolidação previsto no art. 26, § 7º. O edital deve indicar "
                    "matrícula, descrição, datas, horários, modalidade, condições de pagamento e valor mínimo. A "
                    "certidão da matrícula e o documento do leiloeiro permitem verificar se o marco foi observado.\n\n"
                    "A realização pode ser eletrônica, mas o devedor e eventual terceiro fiduciante devem receber "
                    "comunicação das datas, locais e horários nos endereços do contrato, inclusive o endereço "
                    "eletrônico. Publicidade ao mercado não substitui a comunicação legalmente prevista."
                ),
            },
            {
                "heading": "O piso inicial considera avaliação e base do ITBI",
                "text": (
                    "No primeiro leilão, o referencial parte do valor do imóvel indicado no contrato para excussão, "
                    "com os critérios de revisão pactuados. Se ele for inferior ao valor utilizado pelo órgão "
                    "competente como base do ITBI na consolidação, prevalece o maior como mínimo.\n\n"
                    "Isso exige comparar contrato, atualização e documento tributário. Usar uma avaliação antiga "
                    "sem aplicar o critério previsto ou omitir a base pública maior pode reduzir indevidamente o "
                    "piso e afetar a validade do ato."
                ),
            },
            {
                "heading": "Frustrado o primeiro, o segundo vem nos 15 dias seguintes",
                "text": (
                    "Se o maior lance não alcança o referencial do primeiro pregão, realiza-se o segundo nos 15 dias "
                    "seguintes. Para as operações gerais, busca-se lance igual ou superior à dívida, despesas e "
                    "encargos; se não houver, o credor pode aceitar, a seu exclusivo critério, valor de pelo menos "
                    "metade da avaliação do bem.\n\n"
                    "O limite de 50 por cento impede arrematação por preço inferior ao piso legal. O fato de a "
                    "dívida ser menor não autoriza vender abaixo da metade e depois transferir toda a perda ao "
                    "devedor."
                ),
            },
            {
                "heading": "Financiamento residencial do devedor segue regra especial",
                "text": (
                    "Na aquisição ou construção do imóvel residencial do próprio devedor, excetuado consórcio, o "
                    "art. 26-A exige, no segundo leilão, lance que alcance a dívida garantida mais antiga, despesas e "
                    "encargos. Se ninguém atingir esse referencial, a dívida é extinta com quitação recíproca e o "
                    "credor fica com livre disponibilidade do imóvel.\n\n"
                    "A exceção depende da finalidade contratual. Uma casa oferecida como garantia de crédito "
                    "empresarial ou de empréstimo sem destinação à sua aquisição não entra automaticamente nesse "
                    "tratamento."
                ),
            },
            {
                "heading": "Sobra e saldo negativo não têm a mesma solução",
                "text": (
                    "Quando há venda acima da dívida, despesas e encargos, o credor entrega o excedente ao "
                    "fiduciante nos cinco dias seguintes. Nas operações que não recebem a quitação especial do art. "
                    "26-A, produto insuficiente pode deixar saldo remanescente executável, com deduções definidas "
                    "pela lei.\n\n"
                    "Auto de arrematação, comprovante do preço, planilha do débito, comissão, tributos, seguro e "
                    "condomínio compõem a prestação de contas. Sem esses documentos não é possível afirmar que há "
                    "sobra nem aceitar uma cobrança residual."
                ),
            },
            {
                "heading": "O devedor ainda tem preferência antes do segundo pregão",
                "text": (
                    "Entre a consolidação e a data do segundo leilão, o fiduciante pode exercer preferência para "
                    "adquirir o imóvel pelo preço completo previsto no art. 27, § 2º-B. Isso não reativa o contrato "
                    "nem permite pagar apenas as parcelas em atraso.\n\n"
                    "Peça edital, comunicação, memória do preço de preferência e matrícula atual. Um advogado pode "
                    "conferir sequência, pisos e enquadramento residencial sem prometer cancelamento: irregularidade "
                    "precisa ser ligada ao ato e ao prejuízo demonstrado."
                ),
            },
        ],
        faq=[{
            "q": "O primeiro leilão ainda precisa ocorrer em 30 dias?",
            "a": "Não. A redação dada pela Lei 14.711/2023 fixa 60 dias contados do registro da consolidação.",
        }],
        sources=[
            (LAW_9514 + "#art27", "Lei 9.514/1997, arts. 26-A e 27", "prazos, pisos, comunicação, sobra e disciplina residencial dos leilões"),
            (LAW_14711, "Lei 14.711/2023", "alterações vigentes no primeiro e no segundo leilão"),
            (THEME_1288, "STJ, Tema 1.288", "direito de preferência após a consolidação sob o regime atual"),
        ],
        links=["direito de preferência", "preço vil no leilão", "saldo remanescente"],
    )

    update(
        by_id["imob-segundo-leilao-negativo-quitacao"],
        title="Leilão sem comprador: quando a dívida acaba ou continua",
        meta="A dívida não é sempre extinta após dois leilões vazios. Veja a regra do imóvel residencial do devedor e a cobrança residual nas demais operações.",
        h1="Segundo leilão negativo não produz a mesma quitação em todo contrato",
        opening=(
            "A reforma de 2023 eliminou a regra genérica de que dois leilões sem comprador encerram qualquer "
            "dívida garantida por alienação fiduciária. A quitação foi preservada para financiamento destinado à "
            "aquisição ou construção do imóvel residencial do próprio devedor, fora de consórcio. Nas demais "
            "operações, pode existir saldo remanescente mesmo que o credor fique com a livre disponibilidade do bem."
        ),
        sections=[
            {
                "heading": "A finalidade do financiamento vem antes do resultado do leilão",
                "text": (
                    "O art. 26-A cria normas especiais para aquisição ou construção do imóvel residencial do "
                    "devedor. Não basta a matrícula descrever uma casa nem a família morar no local: o crédito deve "
                    "ter a destinação prevista na norma. Operações de consórcio estão expressamente excluídas.\n\n"
                    "Contrato, proposta e comprovantes de liberação identificam a finalidade. Um imóvel residencial "
                    "dado depois em garantia de capital de giro, dívida empresarial ou crédito de livre uso tende a "
                    "seguir a regra geral, salvo outra disciplina específica."
                ),
            },
            {
                "heading": "Na operação residencial especial há quitação recíproca",
                "text": (
                    "No segundo leilão dessa modalidade, o referencial mínimo reúne a dívida garantida mais antiga, "
                    "despesas, emolumentos, seguro, tributos e condomínio. Se não houver lance que o alcance, a "
                    "dívida é considerada extinta e as partes dão quitação recíproca; o credor passa a dispor "
                    "livremente do imóvel.\n\n"
                    "A extinção não devolve a propriedade ao devedor e não gera sobra fictícia. Ela impede a "
                    "cobrança do excedente daquela obrigação após o desfecho legal, sem afastar a necessidade de "
                    "conferir outras dívidas autônomas que não estejam abrangidas."
                ),
            },
            {
                "heading": "Na regra geral o saldo pode ser cobrado",
                "text": (
                    "Fora do art. 26-A, se o segundo leilão não alcançar o referencial, o fiduciário fica com livre "
                    "disponibilidade do imóvel e deixa de dever eventual entrega de sobra. O § 5º-A do art. 27 "
                    "mantém o devedor obrigado pelo saldo que não for coberto e permite execução e uso de outras "
                    "garantias.\n\n"
                    "Quando os leilões não produzem venda, a lei manda deduzir, no cálculo residual, o referencial "
                    "mínimo da dívida atualizado, incluídos encargos e despesas. O credor não pode simplesmente "
                    "ignorar o valor atribuído ao imóvel e cobrar o débito original inteiro."
                ),
            },
            {
                "heading": "Arrematação abaixo da dívida também exige classificação",
                "text": (
                    "Na regra geral, o credor pode aceitar no segundo leilão, se não houver lance pelo montante da "
                    "dívida, proposta de pelo menos metade da avaliação. Se o produto não quitar tudo, o restante "
                    "pode subsistir. Já a operação residencial especial exige o referencial integral e resolve o "
                    "déficit pela quitação quando nenhum lance o alcança.\n\n"
                    "Por isso, leilão deserto e venda insuficiente são fatos diferentes. O auto, a modalidade do "
                    "crédito e a memória do saldo mostram qual regra incide."
                ),
            },
            {
                "heading": "Como responder a uma cobrança posterior",
                "text": (
                    "Solicite certidões dos dois leilões, editais, planilha da dívida na data dos pregões, contrato, "
                    "prova da finalidade do crédito e cálculo da dedução do imóvel. A cobrança deve explicar "
                    "capital, juros, despesas e valor utilizado para reduzir o débito.\n\n"
                    "Se o financiamento era para aquisição ou construção da moradia do devedor e o segundo leilão "
                    "não atingiu o mínimo, a documentação permite opor a quitação legal. Em outra modalidade, um "
                    "advogado pode revisar a dedução e as garantias sem afirmar que a ausência de arrematante, "
                    "sozinha, apagou a dívida."
                ),
            },
            {
                "heading": "A redação antiga não deve ser aplicada sem análise temporal",
                "text": (
                    "Contratos e procedimentos atravessam reformas legislativas, e o efeito temporal pode gerar "
                    "discussão. A resposta deve indicar datas de mora, consolidação e leilões e considerar atos já "
                    "concluídos. Repetir a antiga redação do § 5º como regra universal atual é incorreto.\n\n"
                    "A Lei 14.711/2023 é a fonte da distinção vigente. Casos consolidados sob disciplina anterior "
                    "podem exigir exame de direito intertemporal, sem transformar isso em promessa automática de "
                    "quitação ou de cobrança."
                ),
            },
        ],
        faq=[{
            "q": "Se ninguém comprar no segundo leilão, o banco pode cobrar o restante?",
            "a": (
                "Pode nas operações sujeitas à regra geral, após a dedução legal. No financiamento para aquisição "
                "ou construção da residência do devedor, fora de consórcio, aplica-se a quitação especial do art. 26-A."
            ),
        }],
        sources=[
            (LAW_9514 + "#art26a", "Lei 9.514/1997, arts. 26-A e 27", "quitação residencial especial e obrigação pelo saldo nas demais operações"),
            (LAW_14711, "Lei 14.711/2023", "substituição da extinção genérica pela distinção conforme a finalidade do financiamento"),
        ],
        links=["primeiro e segundo leilão", "sobra do leilão", "financiamento atrasado"],
    )

    update(
        by_id["imob-desocupacao-pos-consolidacao"],
        title="Desocupação após consolidação: liminar e taxa de ocupação",
        meta="Entenda quando o credor pode pedir reintegração, por que os 60 dias vêm da liminar e como é calculada a taxa de ocupação de 1%.",
        h1="Reintegração e custo de permanecer no imóvel consolidado",
        opening=(
            "Os 60 dias da Lei 9.514/1997 não são uma carência obrigatória entre a consolidação e o ajuizamento da "
            "reintegração. Eles correspondem ao prazo de desocupação fixado na liminar, quando o credor comprova a "
            "propriedade consolidada. Permanecer no imóvel também pode gerar taxa de ocupação desde a consolidação, "
            "de modo que negociar a saída exige conhecer o processo e o custo que continua correndo."
        ),
        sections=[
            {
                "heading": "A consolidação basta para pedir reintegração",
                "text": (
                    "O art. 30 assegura ao fiduciário, cessionário, sucessores e adquirente em leilão a reintegração "
                    "liminar quando comprovada a consolidação em seu nome. O STJ decidiu que o credor não precisa "
                    "realizar previamente os leilões para ajuizar a ação.\n\n"
                    "Isso não autoriza retirada pela força, troca clandestina de fechadura ou corte de serviços. A "
                    "desocupação coercitiva passa por ordem judicial e cumprimento do mandado, com identificação "
                    "das pessoas e do imóvel atingidos."
                ),
            },
            {
                "heading": "Os 60 dias são concedidos na decisão liminar",
                "text": (
                    "Com a prova registral, o juiz pode conceder a reintegração para desocupação em 60 dias. O prazo "
                    "é contado conforme a ordem e sua comunicação processual, não automaticamente a partir da "
                    "averbação. Antes da citação ou intimação, o ocupante não deve presumir que uma contagem informal "
                    "já lhe garante dois meses.\n\n"
                    "Leia decisão, mandado e certidão do oficial. A data exata e eventual acordo homologado definem "
                    "o cronograma; uma conversa com terceirizada de cobrança não modifica a ordem judicial."
                ),
            },
            {
                "heading": "A taxa legal é de 1 por cento ao mês ou fração",
                "text": (
                    "O art. 37-A impõe ao fiduciante taxa de ocupação de 1 por cento do valor do imóvel referido no "
                    "contrato, atualizado segundo o critério pactuado, por mês ou fração. Na redação vigente, ela é "
                    "computada desde a consolidação até a imissão do credor ou sucessor na posse.\n\n"
                    "O STJ afastou a redução judicial do percentual para 0,5 por cento com base genérica no CDC. "
                    "Ainda assim, datas, base de cálculo, atualização e sujeito cobrado podem ser conferidos; o "
                    "percentual legal não legitima uma planilha sem memória."
                ),
            },
            {
                "heading": "Locação e ocupação por terceiro pedem análise própria",
                "text": (
                    "Nem todo morador é o fiduciante responsável pela taxa. O contrato de locação, a anuência do "
                    "credor e a comunicação para denúncia influenciam a relação com o ocupante. Deve-se separar a "
                    "pretensão possessória contra quem está no bem da cobrança contratual dirigida às partes da "
                    "alienação fiduciária.\n\n"
                    "Identifique quem assinou o financiamento, quem ocupa, a origem da posse e os avisos recebidos. "
                    "Cobrar automaticamente do locatário a taxa do art. 37-A pode confundir relações distintas."
                ),
            },
            {
                "heading": "A defesa precisa atacar o fundamento registral ou processual",
                "text": (
                    "Intimação de mora irregular, consolidação sem pressuposto, pagamento reconhecido ou erro na "
                    "matrícula podem repercutir na posse. A defesa deve trazer certidões, recibos e cópia do "
                    "procedimento; alegar apenas que os leilões ainda não ocorreram não impede a reintegração segundo "
                    "o entendimento atual do STJ.\n\n"
                    "Tutela para suspender o mandado depende de probabilidade do direito e risco demonstrados. "
                    "Protocolar uma ação anulatória não paralisa automaticamente a ordem possessória."
                ),
            },
            {
                "heading": "Negociação de saída deve tratar prazo, chaves e valores",
                "text": (
                    "Um acordo útil registra data de entrega das chaves, vistoria, retirada de bens, responsabilidade "
                    "por condomínio e tributos, destino da taxa acumulada e comunicação ao processo. Sem quitação "
                    "expressa, desocupar não apaga necessariamente valores anteriores.\n\n"
                    "Leve matrícula, contrato, decisão, mandado, planilha da taxa e comprovantes a um advogado. A "
                    "orientação pode comparar defesa e acordo sem prometer permanência, porque a consolidação regular "
                    "dá ao credor uma via possessória célere."
                ),
            },
        ],
        faq=[{
            "q": "O banco precisa esperar 60 dias após a consolidação para entrar com a ação?",
            "a": (
                "Não. Segundo o STJ, a consolidação é suficiente para requerer reintegração; os 60 dias são o prazo "
                "de desocupação previsto para a liminar."
            ),
        }],
        sources=[
            (LAW_9514 + "#art30", "Lei 9.514/1997, arts. 30 e 37-A", "reintegração liminar, prazo de desocupação e taxa de ocupação"),
            (REPOSSESSION, "STJ, REsp 2.092.980", "reintegração não depende da realização prévia dos leilões"),
            (OCCUPANCY, "STJ, REsp 1.999.485", "percentual legal da taxa de ocupação e impossibilidade de redução genérica pelo CDC"),
        ],
        links=["consolidação da propriedade", "taxa de ocupação", "intimação e defesa no leilão"],
    )

    changed = {
        "imob-parei-pagar-financiamento",
        "imob-purgacao-mora-15-dias",
        "imob-pagar-divida-ate-leilao",
        "imob-leilao-extrajudicial-como-funciona",
        "imob-segundo-leilao-negativo-quitacao",
        "imob-desocupacao-pos-consolidacao",
    }
    if any(intent not in by_id for intent in changed):
        raise SystemExit("intent esperado ausente")

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-current-law-a.", dir=os.path.dirname(TARGET))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(open(TARGET, "rb").read()).hexdigest() != EXPECTED_SHA256:
            raise SystemExit("CAS falhou antes da promoção")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print("paginas corrigidas:")
    for intent in sorted(changed):
        print(f"  {intent}: {by_id[intent]['word_count']} palavras")
    print(f"sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
