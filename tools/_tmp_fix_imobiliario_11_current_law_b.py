#!/usr/bin/env python3
"""Atualiza conceitos, intimacao, preco, sobra e hipoteca no shard imobiliario-11."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "d48821a6a599f4febcd35387797bfe50dfdf26d2e55a913bc9872326f788fa8f"
LAW_9514 = "https://www.planalto.gov.br/ccivil_03/leis/l9514.htm"
LAW_14711 = "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14711.htm"
LAW_8009 = "https://www.planalto.gov.br/ccivil_03/leis/l8009.htm"
INTIMATION_EXHAUSTION = (
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/"
    "02082021-Intimacao-do-devedor-fiduciante-por-edital-e-nula-se-nao-forem-"
    "esgotados-todos-os-outros-meios-previamente.aspx"
)
INFO_794 = "https://processo.stj.jus.br/docs_internet/informativos/PDF/Inf0794.pdf"
INFO_812 = "https://processo.stj.jus.br/docs_internet/informativos/PDF/Inf0812.pdf"
INFO_664 = (
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar"
    "&aplicacao=informativo&livre=%40cnot%3D017464"
)
INFO_635 = (
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre="
    "%40CNOT%3D016810"
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
        if previous.get("url") == url:
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
        by_id["imob-alienacao-fiduciaria-verbete"],
        title="Alienação fiduciária de imóvel: propriedade e garantia",
        meta="Entenda o registro da propriedade fiduciária, a posse do devedor, a baixa após quitação e o que muda quando ocorre a consolidação.",
        h1="Como funciona a propriedade fiduciária do imóvel",
        opening=(
            "Na alienação fiduciária, o registro transfere ao credor uma propriedade resolúvel destinada a garantir "
            "a dívida, enquanto o devedor permanece com a posse direta e usa o imóvel. Isso não torna o banco dono "
            "pleno desde o início nem autoriza venda livre durante o contrato. Quitado o crédito, a garantia se "
            "resolve; havendo mora, a propriedade só se consolida depois do procedimento previsto em lei."
        ),
        sections=[
            {
                "heading": "O registro constitui a propriedade fiduciária",
                "text": (
                    "O art. 22 da Lei 9.514/1997 define o negócio pelo qual o fiduciante transfere ao fiduciário a "
                    "propriedade resolúvel de imóvel para garantia. O art. 23 determina que essa propriedade se "
                    "constitui com o registro do contrato na matrícula. Assinatura sem ingresso registral não deve "
                    "ser tratada como se já produzisse todos os efeitos reais contra terceiros.\n\n"
                    "A certidão atualizada mostra credor, devedor, título, valor e eventuais garantias sucessivas. "
                    "Ela é o documento inicial para venda, inventário, execução ou discussão sobre prioridade."
                ),
            },
            {
                "heading": "Credor tem posse indireta e devedor conserva o uso",
                "text": (
                    "Constituída a garantia, o fiduciante torna-se possuidor direto e o fiduciário, possuidor "
                    "indireto. Enquanto adimplente, o devedor utiliza o imóvel por sua conta e risco e responde por "
                    "obrigações contratuais, tributos e conservação conforme o caso. O credor não pode ocupar ou "
                    "explorar economicamente a casa como se a garantia fosse aquisição definitiva.\n\n"
                    "Também é impreciso dizer que a propriedade já está consolidada no banco durante todo o "
                    "financiamento. Consolidação é ato posterior à mora não purgada e possui averbação própria."
                ),
            },
            {
                "heading": "O devedor não transfere livremente sem anuência",
                "text": (
                    "Os direitos do fiduciante podem ser transmitidos com anuência expressa do fiduciário, nos "
                    "termos do art. 29. Uma venda informal não altera o sujeito que continua obrigado perante o "
                    "credor nem substitui o registro. O comprador de gaveta assume risco de inadimplemento, morte, "
                    "divórcio e recusa futura de formalização.\n\n"
                    "A saída regular pode envolver assunção aprovada, quitação com recursos da venda ou operação "
                    "simultânea. Contrato, saldo e matrícula precisam conversar entre si."
                ),
            },
            {
                "heading": "Quitação resolve a garantia, mas exige baixa registral",
                "text": (
                    "Com o pagamento integral, a propriedade fiduciária se resolve em favor do fiduciante. O credor "
                    "deve fornecer termo de quitação em 30 dias, e o oficial cancela o registro da garantia à vista "
                    "desse documento. A dívida pode estar paga sem que uma certidão antiga já mostre o imóvel livre.\n\n"
                    "Guarde termo, protocolo e nova matrícula. A baixa é importante para provar a disponibilidade do "
                    "bem perante comprador, inventário, novo financiador ou autoridade tributária."
                ),
            },
            {
                "heading": "Mora não permite apropriação imediata do imóvel",
                "text": (
                    "O credor precisa requerer intimação pelo registro de imóveis, permitir a purgação prevista nos "
                    "arts. 26 e 26-A e só então averbar a consolidação se os pressupostos forem atendidos. Depois, "
                    "aplicam-se os leilões e o direito de preferência. Pular ciência, prazo ou registro pode gerar "
                    "controvérsia; o simples atraso não substitui esses atos.\n\n"
                    "A Lei 14.711/2023 alterou prazo, piso e tratamento do saldo. Modelos anteriores à reforma não "
                    "devem ser usados para explicar um procedimento atual sem conferir as datas."
                ),
            },
            {
                "heading": "Documentos para identificar a posição jurídica",
                "text": (
                    "Leia contrato e aditivos, certidão da matrícula, extrato da dívida, termo de quitação quando "
                    "existir e documentos de intimação ou consolidação. A descrição coloquial de que o imóvel está "
                    "no nome do banco não informa se há propriedade fiduciária ativa, consolidação ou aquisição por "
                    "terceiro.\n\n"
                    "Um advogado pode classificar o ato e conferir o caminho disponível sem prometer baixa, "
                    "anulação ou recuperação antes de ler a matrícula. Cada etapa tem pressupostos diferentes."
                ),
            },
        ],
        faq=[{
            "q": "O banco é proprietário pleno enquanto o contrato está em dia?",
            "a": (
                "Não. Ele detém propriedade fiduciária resolúvel para garantia e posse indireta; o devedor conserva "
                "a posse direta. Propriedade consolidada é etapa posterior à mora não purgada."
            ),
        }],
        sources=[
            (LAW_9514 + "#art22", "Lei 9.514/1997, arts. 22 a 30", "constituição, posições das partes, quitação, transmissão e execução da propriedade fiduciária"),
            (LAW_14711, "Lei 14.711/2023", "alterações vigentes na excussão da garantia imobiliária"),
        ],
        links=["baixa da alienação após quitação", "venda de imóvel financiado", "consolidação e leilão"],
    )

    update(
        by_id["imob-intimacao-edital-nulidade"],
        title="Intimação por edital na alienação fiduciária: requisitos",
        meta="Veja quando o edital pode substituir a intimação pessoal, como funciona a hora certa, quais provas pedir e o efeito de uma comunicação irregular.",
        h1="Quando a intimação por edital pode ser questionada",
        opening=(
            "O edital é uma forma excepcional de constituir a mora na alienação fiduciária de imóvel. Ele não se "
            "torna válido apenas porque uma carta voltou, mas também não é sempre nulo quando o devedor não assinou "
            "pessoalmente. Tentativas no endereço, suspeita de ocultação, certidão do oficial e publicações precisam "
            "ser reconstruídas antes de concluir se o prazo de purgação começou."
        ),
        sections=[
            {
                "heading": "A intimação pessoal é o ponto de partida",
                "text": (
                    "O art. 26 prevê intimação do devedor e, quando houver, do terceiro fiduciante pelo oficial do "
                    "registro de imóveis, com formas legalmente admitidas de diligência e correspondência. O "
                    "endereço contratual é relevante, mas prova de atualização recebida pelo credor também deve ser "
                    "preservada.\n\n"
                    "Peça a certidão completa, avisos de recebimento e datas das diligências. Uma etiqueta de "
                    "devolução isolada não revela quem foi procurado, em qual local nem por que a entrega falhou."
                ),
            },
            {
                "heading": "Suspeita de ocultação conduz à hora certa",
                "text": (
                    "Quando o intimando é procurado por duas vezes no domicílio ou residência e há suspeita motivada "
                    "de que se oculta, a lei remete ao procedimento de hora certa, com aviso a familiar ou vizinho "
                    "sobre o retorno no dia útil seguinte. O edital não deve servir como atalho para ignorar esses "
                    "indícios.\n\n"
                    "A certidão precisa narrar as tentativas e a razão da suspeita. Menções padronizadas sem datas, "
                    "horários ou pessoas encontradas podem justificar apuração, mas a validade será decidida a partir "
                    "do conjunto documental."
                ),
            },
            {
                "heading": "Local ignorado, incerto ou inacessível autoriza edital certificado",
                "text": (
                    "Se o devedor, cessionário ou representante estiver em local ignorado, incerto ou inacessível, "
                    "o serventuário certifica o fato e o oficial promove publicação durante pelo menos três dias em "
                    "jornal de grande circulação local ou de comarca acessível quando não houver imprensa diária. O "
                    "prazo começa na última publicação.\n\n"
                    "O STJ já anulou edital precipitado quando o credor conhecia meio para localizar a devedora e "
                    "não esgotou as alternativas. Em outro caso, aceitou o edital após reiterada esquiva no endereço "
                    "indicado. Os precedentes mostram por que a prova das diligências é decisiva."
                ),
            },
            {
                "heading": "Recusa ou mudança aparente não geram uma resposta automática",
                "text": (
                    "A recusa documentada e repetida pode demonstrar ocultação ou justificar a passagem à forma "
                    "substitutiva. Já a simples anotação de mudança, quando existem outros endereços conhecidos ou "
                    "comunicação cadastral recente, pode ser insuficiente. Não é correto afirmar que toda recusa "
                    "equivale a intimação nem que ela sempre invalida o procedimento.\n\n"
                    "Protocolos de atualização, contas recebidas pelo próprio banco, rastreamento e imagens do local "
                    "ajudam a confrontar a narrativa da certidão sem depender de lembrança oral."
                ),
            },
            {
                "heading": "A comunicação dos leilões é uma etapa separada",
                "text": (
                    "Depois da consolidação, datas, horários e locais dos dois leilões devem ser comunicados aos "
                    "endereços do contrato, inclusive ao eletrônico. Uma intimação regular para purgar a mora não "
                    "supre automaticamente a falta de comunicação posterior, e a discussão deve indicar qual ato "
                    "está ausente.\n\n"
                    "Editais, mensagens, cartas e comprovantes de envio compõem linhas do tempo diferentes. Misturar "
                    "essas fases pode produzir pedido errado ou deixar de apontar o vício relevante."
                ),
            },
            {
                "heading": "O efeito do vício depende do estágio e das pessoas atingidas",
                "text": (
                    "A falta da intimação exigida para constituir a mora pode comprometer a consolidação, mas o "
                    "resultado judicial não deve ser prometido como anulação automática de tudo. Data da ação, "
                    "registro, leilão, aquisição por terceiro e demonstração do prejuízo influenciam o remédio; em "
                    "certas controvérsias a lei direciona a solução para perdas e danos.\n\n"
                    "Reúna contrato, matrícula histórica, procedimento registral e editais. Um advogado pode pedir "
                    "a providência proporcional com base no documento faltante, sem inventar diligências nem "
                    "garantir retorno do imóvel antes da análise judicial."
                ),
            },
        ],
        faq=[{
            "q": "Uma carta devolvida já permite intimar por edital?",
            "a": (
                "Não necessariamente. É preciso examinar o motivo, as diligências, eventual hora certa e a certidão "
                "de local ignorado, incerto ou inacessível."
            ),
        }],
        sources=[
            (LAW_9514 + "#art26", "Lei 9.514/1997, arts. 26 e 27", "formas de intimação, hora certa, edital e comunicação das datas dos leilões"),
            (INTIMATION_EXHAUSTION, "STJ, REsp 1.906.475", "edital é nulo quando havia meios não esgotados para localizar a devedora"),
            (INFO_794, "STJ, Informativo 794", "edital admitido diante de reiterada esquiva de recebimento no endereço contratual"),
        ],
        links=["purgação da mora", "comunicação do leilão", "consolidação da propriedade"],
    )

    update(
        by_id["imob-leilao-preco-vil"],
        title="Preço vil no leilão extrajudicial: piso e avaliação",
        meta="Entenda o limite de 50% da avaliação, a regra especial da dívida residencial e quais documentos podem demonstrar arrematação por preço vil.",
        h1="Quando o preço do leilão fiduciário fica abaixo do mínimo legal",
        opening=(
            "Desde a Lei 14.711/2023, o segundo leilão da regra geral não pode aceitar lance inferior à metade da "
            "avaliação, mesmo quando a dívida é menor. Para o financiamento de aquisição ou construção da "
            "residência do devedor, o art. 26-A usa como referencial a dívida e os encargos. Avaliação, finalidade do "
            "crédito e data do ato precisam ser identificadas antes de chamar o preço de vil."
        ),
        sections=[
            {
                "heading": "Primeiro leilão usa o maior referencial aplicável",
                "text": (
                    "O contrato deve indicar o valor do imóvel para venda e o critério de revisão. Se esse valor for "
                    "inferior ao adotado pelo órgão competente como base do ITBI na consolidação, a base pública mais "
                    "alta funciona como mínimo no primeiro leilão. A atualização não pode ser substituída por um "
                    "número histórico escolhido sem memória.\n\n"
                    "Compare contrato, índice, certidão tributária, edital e laudo. Divergência de área, benfeitorias "
                    "ou identificação também pode distorcer o parâmetro e afastar interessados."
                ),
            },
            {
                "heading": "Segundo leilão geral não pode ficar abaixo de 50 por cento",
                "text": (
                    "Pela redação atual do art. 27, busca-se primeiro lance que cubra dívida, despesas e encargos. "
                    "Sem ele, o credor pode aceitar, por escolha própria, proposta de ao menos metade da avaliação. "
                    "O limite não autoriza o arrematante a pagar menos nem obriga o credor a aceitar exatamente 50 "
                    "por cento.\n\n"
                    "O Informativo 812 do STJ afirma que, após a reforma, não há dúvida sobre a vedação abaixo da "
                    "metade. O tribunal também aplicou a proteção a caso anterior, com base em abuso, boa-fé e "
                    "proibição de enriquecimento sem causa."
                ),
            },
            {
                "heading": "A operação residencial especial usa outro piso",
                "text": (
                    "Quando o crédito financiou a aquisição ou construção do imóvel residencial do próprio devedor, "
                    "fora de consórcio, o segundo leilão só aceita lance igual ou superior à dívida garantida mais "
                    "antiga, despesas e encargos. Se ninguém alcançar esse referencial, ocorre a quitação especial e "
                    "o credor fica com o imóvel.\n\n"
                    "Essa regra pode exigir piso maior que metade da avaliação. Não se escolhe a fórmula mais baixa; "
                    "a finalidade comprovada do contrato determina o regime."
                ),
            },
            {
                "heading": "Preço baixo não é medido apenas pelo saldo devedor",
                "text": (
                    "Um saldo pequeno não transforma o próprio saldo no valor de mercado do bem. A jurisprudência do "
                    "STJ toma a avaliação como referência para vedar alienação inferior à metade na regra geral. Da "
                    "mesma forma, alegar que a casa vale mais sem laudo ou dado objetivo não demonstra erro.\n\n"
                    "Avaliações próximas ao pregão, negócios comparáveis, características corretas e critérios do "
                    "contrato ajudam a testar se o valor oficial ficou defasado ou se o edital descreveu bem diverso "
                    "do que foi vendido."
                ),
            },
            {
                "heading": "Publicidade e descrição podem explicar a formação do preço",
                "text": (
                    "Falha na comunicação ao devedor, publicação inadequada ou descrição materialmente errada são "
                    "vícios próprios. Eles não precisam ser inventados para completar a tese de preço vil, mas podem "
                    "mostrar por que não houve competição. Cada alegação deve apontar documento, regra e prejuízo.\n\n"
                    "Preserve página do leiloeiro, edital integral, registros de publicação, fotos e auto de "
                    "arrematação. Capturas sem data ou anúncio incompleto dificultam provar o que estava disponível "
                    "aos licitantes."
                ),
            },
            {
                "heading": "A medida judicial depende do momento do registro",
                "text": (
                    "Antes da transferência, uma tutela pode buscar impedir ato abaixo do piso quando os requisitos "
                    "estão documentados. Depois da arrematação, entram segurança do adquirente, registro e eventual "
                    "conversão em perdas e danos. A nulidade não decorre de um anúncio que apenas compara preço pago "
                    "com estimativa informal.\n\n"
                    "Um advogado pode reconstruir avaliação, regime, lances e registros e definir pedido adequado. "
                    "Não é responsável garantir devolução do imóvel sem examinar a posição do terceiro e a data em "
                    "que cada ato foi concluído."
                ),
            },
        ],
        faq=[{
            "q": "Todo leilão abaixo do valor de mercado é nulo?",
            "a": (
                "Não. A regra geral veda lance inferior à metade da avaliação, e a modalidade residencial pode "
                "exigir o total da dívida e encargos. O valor de mercado alegado precisa de prova."
            ),
        }],
        sources=[
            (LAW_9514 + "#art27", "Lei 9.514/1997, arts. 26-A e 27", "valores mínimos do primeiro e do segundo leilão"),
            (LAW_14711, "Lei 14.711/2023", "introdução expressa do piso de metade da avaliação na regra geral"),
            (INFO_812, "STJ, Informativo 812", "vedação de preço vil em execução extrajudicial e parâmetro de 50 por cento"),
        ],
        links=["primeiro e segundo leilão", "avaliação do imóvel", "ação contra leilão irregular"],
    )

    update(
        by_id["imob-saldo-leilao-devolucao"],
        title="Sobra do leilão: cálculo e devolução ao devedor",
        meta="Veja o que é abatido do preço do leilão, o prazo de cinco dias para a sobra, como pedir contas e quando pode existir saldo devedor residual.",
        h1="Como conferir o valor que sobra depois do leilão do imóvel",
        opening=(
            "O credor não fica livremente com todo o preço obtido no leilão. Depois de descontar dívida, despesas e "
            "encargos definidos na Lei 9.514/1997, deve entregar ao fiduciante o excedente em cinco dias. A mesma "
            "conta pode revelar situação oposta nas operações gerais: produto insuficiente e saldo ainda exigível. "
            "Auto de venda e memória discriminada são indispensáveis para distinguir os dois resultados."
        ),
        sections=[
            {
                "heading": "A sobra nasce do preço efetivamente recebido",
                "text": (
                    "O ponto de partida é o valor da venda no primeiro ou no segundo leilão. Dele são deduzidos o "
                    "saldo da operação na data do pregão, juros convencionais, penalidades e demais encargos "
                    "contratuais, além dos itens que a lei classifica como despesas e encargos do imóvel.\n\n"
                    "Avaliação contratual não é dinheiro recebido e, sozinha, não gera crédito ao devedor. Se o "
                    "leilão ficou deserto, aplica-se a disciplina própria da falta de lance, não uma sobra calculada "
                    "como se tivesse ocorrido venda."
                ),
            },
            {
                "heading": "Despesas dedutíveis precisam ser demonstradas",
                "text": (
                    "A lei inclui custos de intimação, anúncios, comissão do leiloeiro e emolumentos necessários ao "
                    "procedimento. Prêmios de seguro, tributos e contribuições condominiais também entram como "
                    "encargos do imóvel. Cada rubrica deve corresponder ao período e ao documento que a sustenta.\n\n"
                    "Taxa genérica, honorário sem base ou valor duplicado pode ser questionado. Pedir nota, guia, "
                    "edital, contrato do leiloeiro e extrato evita discutir a conta apenas por estimativa."
                ),
            },
            {
                "heading": "O excedente deve ser entregue em cinco dias",
                "text": (
                    "O art. 27, § 4º, fixa os cinco dias seguintes à venda para o credor entregar a importância que "
                    "sobejar, nela compreendida a indenização de benfeitorias, após as deduções legais. A entrega "
                    "produz quitação recíproca quanto ao resultado dessa conta.\n\n"
                    "Mantenha dados bancários e endereço atualizados e protocole pedido de demonstrativo. O dever "
                    "não depende de o ex-proprietário adivinhar que houve excedente, embora a cobrança documentada "
                    "seja necessária quando o repasse não ocorre."
                ),
            },
            {
                "heading": "Credor deve explicar a destinação do produto",
                "text": (
                    "Auto de arrematação, comprovante de pagamento, extrato na data do leilão e relação de despesas "
                    "permitem refazer a operação. Se houver credores com garantias ou constrições registradas, a "
                    "distribuição também pode observar prioridades, o que exige consultar a matrícula histórica e "
                    "eventual quadro de credores.\n\n"
                    "Uma planilha final sem documentos de origem não basta para verificar a sobra. O pedido deve "
                    "abranger os elementos do procedimento, e não somente uma declaração de saldo zero."
                ),
            },
            {
                "heading": "Falta de sobra não significa sempre quitação",
                "text": (
                    "Na aquisição ou construção da residência do devedor, a regra especial impede saldo residual "
                    "quando o segundo leilão não atinge o mínimo. Em outras operações, a Lei 14.711/2023 mantém a "
                    "obrigação pelo montante não satisfeito e permite execução, observada a dedução do valor legal "
                    "do bem quando não há venda.\n\n"
                    "Portanto, resultado negativo não autoriza o credor a cobrar sem memória nem permite ao devedor "
                    "invocar quitação universal. Finalidade do crédito e produto do leilão resolvem a classificação."
                ),
            },
            {
                "heading": "Documentos para cobrar diferença não repassada",
                "text": (
                    "Reúna contrato, matrícula, editais, auto, comprovante do preço, planilha do saldo, condomínio, "
                    "tributos, seguro e despesas. Notifique o credor para prestar contas e pagar o valor identificado, "
                    "com indicação da conta e do cálculo divergente.\n\n"
                    "Se não houver resposta, um advogado pode avaliar exibição, prestação de contas ou cobrança, "
                    "inclusive prazos aplicáveis ao caso. Não é adequado prometer uma sobra só porque o imóvel tinha "
                    "valor sentimental ou avaliação de mercado superior à dívida. Registre também quando tomou "
                    "ciência da venda e de eventual recusa, pois esses marcos ajudam a examinar atualização, juros "
                    "sobre o valor não repassado e prazo da pretensão sem adotar uma data abstrata."
                ),
            },
        ],
        faq=[{
            "q": "A sobra é a diferença entre avaliação do imóvel e dívida?",
            "a": (
                "Não. Ela é calculada sobre o preço efetivo da venda, depois de dívida, despesas e encargos legais."
            ),
        }],
        sources=[
            (LAW_9514 + "#art27", "Lei 9.514/1997, art. 27", "composição da dívida, despesas, encargos e devolução do excedente em cinco dias"),
            (LAW_14711, "Lei 14.711/2023", "redação atual da sobra e do saldo remanescente"),
        ],
        links=["leilão sem comprador", "saldo remanescente", "prestação de contas do credor"],
    )

    update(
        by_id["imob-bem-familia-nao-protege-fiduciaria"],
        title="Bem de família e alienação fiduciária: quais proteções restam",
        meta="Dar a moradia em alienação fiduciária permite executar a garantia, mas não elimina toda proteção contra terceiros, vícios ou falta de consentimento.",
        h1="Bem de família não invalida automaticamente a garantia fiduciária",
        opening=(
            "A impenhorabilidade da Lei 8.009/1990 não transforma a moradia em bem inalienável. Quem constitui "
            "validamente alienação fiduciária não pode, em regra, desfazer a garantia alegando depois apenas que "
            "reside no imóvel. Isso é diferente de permitir que qualquer outro credor penhore o bem ou de ignorar "
            "consentimento, propriedade de terceiro e vício na formação do contrato."
        ),
        sections=[
            {
                "heading": "Impenhorabilidade não é proibição de alienar",
                "text": (
                    "O bem de família legal protege a residência contra dívidas em geral, mas não impede o titular "
                    "capaz de dispor do imóvel. No Informativo 664, o STJ reconheceu a validade de alienação "
                    "fiduciária voluntariamente constituída em contrato de mútuo e rejeitou comportamento "
                    "contraditório de oferecer a garantia e depois negar sua eficácia somente pela moradia.\n\n"
                    "A execução deve seguir a Lei 9.514/1997. A proteção familiar não apaga intimação, consolidação "
                    "e leilão regulares da própria obrigação garantida."
                ),
            },
            {
                "heading": "Financiamento da própria aquisição é a hipótese mais direta",
                "text": (
                    "Quando o crédito permitiu comprar ou construir o próprio imóvel, a garantia e a dívida estão "
                    "ligadas ao acesso à moradia. O atraso pode levar à excussão, embora o art. 26-A atualmente dê "
                    "tratamento especial à purgação e à quitação residual da residência financiada.\n\n"
                    "Dizer que o bem de família impede o leilão contraria a estrutura do financiamento. A defesa "
                    "deve verificar o procedimento e o cálculo, sem usar a impenhorabilidade como resposta única."
                ),
            },
            {
                "heading": "Credor estranho não ocupa a mesma posição do fiduciário",
                "text": (
                    "O imóvel registrado em propriedade fiduciária integra a esfera do fiduciário para fins de "
                    "garantia; terceiro que executa outra dívida do fiduciante não pode simplesmente penhorar como se "
                    "o devedor fosse proprietário pleno. No Informativo 635, o STJ também protegeu os direitos do "
                    "fiduciante relacionados à moradia contra execução por cheques.\n\n"
                    "É essencial identificar quem cobra, qual obrigação está garantida e qual direito foi atingido. "
                    "Execução da garantia e penhora por terceiro são fenômenos distintos."
                ),
            },
            {
                "heading": "Consentimento e titularidade continuam relevantes",
                "text": (
                    "A garantia não alcança validamente a parte de quem não participou do negócio quando a lei exige "
                    "anuência, ressalvadas discussões sobre boa-fé do terceiro e regime patrimonial. Cônjuge, "
                    "companheiro conhecido, coproprietário e representante precisam ser examinados pelos documentos "
                    "do título e da matrícula.\n\n"
                    "Assinatura falsa, incapacidade, procuração insuficiente ou vício de vontade são alegações "
                    "diferentes da impenhorabilidade e exigem prova específica. A residência não convalida fraude, "
                    "mas também não a demonstra por si só."
                ),
            },
            {
                "heading": "Dívida empresarial ou de terceiro pede análise do benefício",
                "text": (
                    "Quando a família oferece o imóvel para obrigação de empresa ou de outra pessoa, titularidade, "
                    "proveito econômico, consentimentos e espécie da garantia ganham peso. Precedentes sobre hipoteca "
                    "não devem ser transportados sem cuidado para alienação fiduciária, e a regra de uma operação "
                    "residencial não se aplica automaticamente ao capital de giro.\n\n"
                    "Contrato social, destino dos recursos, composição familiar e assinaturas ajudam a afastar a "
                    "frase simplista de que toda garantia é nula ou toda moradia pode ser tomada."
                ),
            },
            {
                "heading": "Como organizar uma defesa tecnicamente útil",
                "text": (
                    "Reúna matrícula antes e depois do gravame, instrumento completo, comprovantes da destinação do "
                    "crédito, certidões de casamento ou união, assinaturas, procurações e procedimento cartorário. "
                    "Separe três perguntas: a garantia nasceu validamente, a dívida é a garantida e a execução "
                    "respeitou o rito?\n\n"
                    "Um advogado pode classificar essas questões e buscar medida proporcional. Nenhum atendimento "
                    "responsável deve prometer proteção da casa somente pelo endereço de residência, nem ignorar "
                    "direito de coproprietário que não consentiu. Se já houver intimação, acrescente certidão das "
                    "diligências, cálculo da mora e edital: uma garantia válida ainda pode ter sido executada por "
                    "procedimento defeituoso, e as duas análises não se excluem."
                ),
            },
        ],
        faq=[{
            "q": "Morar no único imóvel anula a alienação fiduciária?",
            "a": (
                "Não. A moradia, sozinha, não invalida garantia voluntária e regular. Ainda podem existir defesas "
                "sobre consentimento, titularidade, dívida e procedimento."
            ),
        }],
        sources=[
            (LAW_8009, "Lei 8.009/1990", "regra de impenhorabilidade do imóvel residencial e exceções legais"),
            (LAW_9514 + "#art22", "Lei 9.514/1997", "constituição e execução da alienação fiduciária imobiliária"),
            (INFO_664, "STJ, Informativo 664", "bem de família legal não impede alienação fiduciária voluntariamente constituída"),
            (INFO_635, "STJ, Informativo 635", "proteção dos direitos do fiduciante sobre moradia contra execução de terceiro"),
        ],
        links=["validade da alienação fiduciária", "intimação e leilão", "garantia de dívida empresarial"],
    )

    update(
        by_id["imob-execucao-hipoteca-diferenca"],
        title="Hipoteca e alienação fiduciária: execução após 2023",
        meta="Compare propriedade, registro, mora e leilão nas duas garantias e entenda quando a hipoteca também pode seguir execução extrajudicial.",
        h1="Diferenças atuais entre hipoteca e alienação fiduciária",
        opening=(
            "A hipoteca mantém a propriedade com o devedor; a alienação fiduciária transfere propriedade resolúvel "
            "ao credor após o registro. Desde a Lei 14.711/2023, porém, não é correto distinguir as duas dizendo que "
            "a hipoteca sempre exige processo judicial: créditos hipotecários podem usar procedimento extrajudicial "
            "se o título contiver a previsão legal expressa e a operação não estiver excluída."
        ),
        sections=[
            {
                "heading": "Na hipoteca o proprietário continua sendo o devedor",
                "text": (
                    "A hipoteca grava o imóvel e dá preferência ao credor conforme registro e prioridade, mas não "
                    "transfere domínio nem posse apenas por sua constituição. O proprietário pode usar o bem dentro "
                    "dos limites do gravame, e a satisfação da dívida ocorre pela excussão da garantia.\n\n"
                    "Certidão da matrícula identifica grau, credor, valor e obrigações garantidas. Havendo vários "
                    "ônus, a ordem registral interfere na distribuição do produto."
                ),
            },
            {
                "heading": "Na fiduciária existe propriedade resolúvel registrada",
                "text": (
                    "Com o registro do contrato fiduciário, o credor recebe propriedade resolúvel e posse indireta, "
                    "enquanto o fiduciante conserva posse direta. O pagamento resolve a garantia; a mora não purgada "
                    "permite averbar consolidação e seguir aos leilões da Lei 9.514/1997.\n\n"
                    "Consolidação não é necessária na hipoteca porque o domínio nunca havia sido transferido ao "
                    "credor. Na execução hipotecária extrajudicial, a alienação se formaliza depois do leilão por "
                    "ata notarial e registro."
                ),
            },
            {
                "heading": "Lei 14.711 criou via extrajudicial para a hipoteca",
                "text": (
                    "O art. 9º da reforma permite executar extrajudicialmente o crédito hipotecário. O devedor e "
                    "eventual terceiro hipotecante são intimados pessoalmente pelo registro de imóveis para purgar "
                    "a mora em 15 dias. Sem pagamento, averba-se o início da excussão e o primeiro leilão deve ser "
                    "promovido em 60 dias.\n\n"
                    "A opção depende de o título constitutivo prever expressamente o procedimento e mencionar seus "
                    "termos legais. A via não se aplica ao financiamento da atividade agropecuária, e a execução "
                    "judicial continua disponível conforme o título e a escolha cabível."
                ),
            },
            {
                "heading": "Os leilões têm semelhanças, mas os títulos não se confundem",
                "text": (
                    "A hipoteca extrajudicial também usa dois leilões, comunicação, pisos e direito de remir antes da "
                    "alienação. Se não houver lance suficiente, o credor pode apropriar-se do bem pelo referencial "
                    "ou realizar venda direta dentro das condições e do prazo legais. A ata notarial documenta "
                    "intimação e pregões para a transmissão.\n\n"
                    "Na fiduciária, o credor já consolidou a propriedade antes dos leilões e o antigo devedor tem "
                    "preferência para nova aquisição. Aplicar o nome de uma etapa à outra pode levar a pedidos e "
                    "custos errados."
                ),
            },
            {
                "heading": "Residência financiada recebe proteção contra saldo nas duas vias",
                "text": (
                    "A reforma prevê tratamento especial quando a operação financiou aquisição ou construção do "
                    "imóvel residencial do devedor, fora de consórcio. Na alienação fiduciária, o art. 26-A extingue "
                    "a dívida se o segundo leilão não alcança o referencial. Na hipoteca, o art. 9º, § 10, exonera o "
                    "devedor do saldo que a excussão não cobrir.\n\n"
                    "Uma residência dada para outra finalidade não recebe automaticamente esse resultado. O destino "
                    "do crédito precisa constar da análise."
                ),
            },
            {
                "heading": "Qual garantia e qual via constam do seu contrato",
                "text": (
                    "Leia título, matrícula, cláusula de execução, data, finalidade do financiamento e intimação. "
                    "Confirme se há hipoteca, propriedade fiduciária, extensão da garantia ou concurso de credores. "
                    "A publicidade registral vale mais que a expressão genérica usada num boleto.\n\n"
                    "Um advogado pode mapear rito, prazos e defesas sem afirmar que hipoteca é sempre lenta ou que "
                    "alienação fiduciária é imune a controle judicial. Ambas exigem pressupostos e permitem discutir "
                    "vícios concretos, inclusive intimação, cálculo, prioridade registral e formação do preço."
                ),
            },
        ],
        faq=[{
            "q": "Hipoteca ainda precisa sempre de execução judicial?",
            "a": (
                "Não. A Lei 14.711/2023 permite execução extrajudicial quando o título contém a previsão exigida; "
                "há exclusões e a via judicial não foi eliminada."
            ),
        }],
        sources=[
            ("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1473", "Código Civil, arts. 1.473 e seguintes", "constituição e objeto da garantia hipotecária"),
            (LAW_9514, "Lei 9.514/1997", "propriedade fiduciária, consolidação e leilões da alienação fiduciária"),
            (LAW_14711, "Lei 14.711/2023, art. 9º", "procedimento extrajudicial da hipoteca, requisitos, prazos e exceção residencial"),
        ],
        links=["alienação fiduciária", "execução extrajudicial de hipoteca", "leilão e saldo remanescente"],
    )

    changed = {
        "imob-alienacao-fiduciaria-verbete",
        "imob-intimacao-edital-nulidade",
        "imob-leilao-preco-vil",
        "imob-saldo-leilao-devolucao",
        "imob-bem-familia-nao-protege-fiduciaria",
        "imob-execucao-hipoteca-diferenca",
    }
    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-current-law-b.", dir=os.path.dirname(TARGET))
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
