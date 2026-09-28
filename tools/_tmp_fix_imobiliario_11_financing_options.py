#!/usr/bin/env python3
"""Atualiza SAC/Price, FGTS e portabilidade com regras vigentes."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "17da635491914c5f3a003516003f63b6a01dc5e5f06a47754f9f6f3c3fdcbde4"
LAW_FGTS = "https://www.planalto.gov.br/ccivil_03/leis/l8036consol.htm#art20"
FGTS_AMORT = "https://www.fgts.gov.br/Paginas/subpaginas/amortizacao_liquidacao.aspx"
FGTS_BUY = "https://www.fgts.gov.br/Paginas/subpaginas/aquisicao_imovel_novo_usado.aspx"
FGTS_MANUAL = "https://www.caixa.gov.br/Downloads/fgts-moradia/MANUAL_DA_MORADIA_PROPRIA_02_12_2025_V_035.pdf"
CMN_4676 = "https://normativos.bcb.gov.br/Lists/Normativos/Attachments/50628/Res_4676_v16_L.pdf"
CMN_5057 = "https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=5057&tipo=Resolu%C3%A7%C3%A3o+CMN"
BCB_PORTABILITY = "https://www.bcb.gov.br/meubc/faqs/p/passo-a-passo-da-portabilidade-de-credito"
BCB_DDC = "https://www.bcb.gov.br/meubc/faqs/p/informacoes-e-documentos-exigidos-do-banco-para-quitar-ou-transferir-divida"
THEME_572 = "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=572&cod_tema_inicial=572&novaConsulta=true&tipo_pesquisa=T"
LAW_4380 = "https://www.planalto.gov.br/ccivil_03/leis/l4380.htm#art15a"


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
        by_id["imob-tabela-sac-vs-price"],
        title="SAC ou Price: como comparar o financiamento imobiliário",
        meta="Compare amortização, juros, evolução das parcelas e saldo no SAC e na Price sem tratar um sistema como ilegal ou sempre mais barato.",
        h1="Diferenças práticas entre SAC e Tabela Price",
        opening=(
            "SAC e Price distribuem amortização e juros de formas diferentes, mas o nome do sistema não informa "
            "sozinho quanto o contrato custará. Taxa, prazo, indexador, seguros e tarifas alteram o fluxo. A parcela "
            "da Price também não permanece necessariamente igual quando existem atualização monetária e encargos "
            "variáveis. A comparação útil usa duas planilhas com as mesmas premissas e lê o saldo em cada data."
        ),
        sections=[
            {
                "heading": "No SAC a amortização do principal é constante",
                "text": (
                    "O Sistema de Amortização Constante divide o principal em quotas de amortização iguais. Como os "
                    "juros incidem sobre um saldo que cai mais rapidamente, o componente financeiro tende a diminuir "
                    "e as prestações começam maiores e decrescem, mantidas as demais condições.\n\n"
                    "Indexador, seguro MIP/DFI, taxa de administração ou diferença entre data-base e vencimento podem "
                    "impedir uma queda linear no boleto total. É preciso separar prestação de principal e juros dos "
                    "itens acessórios."
                ),
            },
            {
                "heading": "Na Price a prestação financeira é nivelada pela fórmula",
                "text": (
                    "No Sistema Francês, a prestação de amortização e juros é calculada para um fluxo nivelado nas "
                    "premissas contratadas. No início, os juros representam parcela maior e a amortização é menor; "
                    "essa proporção se inverte com o tempo. O saldo, por isso, costuma cair mais devagar no começo.\n\n"
                    "Dizer que o boleto será nominalmente idêntico por décadas ignora correção e seguros. Dizer que "
                    "todo uso da Price contém juros ilegais também é incorreto."
                ),
            },
            {
                "heading": "Custo total depende de taxa, prazo e pagamentos",
                "text": (
                    "Com taxa e prazo iguais e sem eventos extraordinários, a amortização mais rápida do SAC tende a "
                    "reduzir juros acumulados, ao custo de prestações iniciais maiores. Uma proposta Price com taxa "
                    "menor pode, porém, custar menos que um SAC mais caro. Só o Custo Efetivo Total e o fluxo completo "
                    "permitem comparar ofertas reais.\n\n"
                    "Antecipações mudam o resultado. Pergunte se o pagamento extra reduz prazo ou prestação e peça a "
                    "nova memória do saldo antes de escolher apenas pela primeira parcela."
                ),
            },
            {
                "heading": "Price não prova capitalização em abstrato",
                "text": (
                    "No Tema 572, o STJ decidiu que verificar capitalização na Tabela Price é questão de fato e pode "
                    "exigir interpretação do contrato e prova técnica. Para operações do SFH, a data também importa: "
                    "o art. 15-A da Lei 4.380/1964 passou a permitir pactuação de capitalização mensal.\n\n"
                    "Uma perícia séria identifica período, cláusula, taxa e lançamentos. Substituir a Price pelo SAC "
                    "em uma calculadora, sem apontar a regra violada, não demonstra valor indevido."
                ),
            },
            {
                "heading": "Compare cenários na mesma data-base",
                "text": (
                    "Solicite taxa nominal e efetiva, CET, prazo, indexador, saldo inicial, seguros e planilha de "
                    "evolução. Simule renda disponível no início, saldo após cinco ou dez anos e custo de amortizações "
                    "planejadas. Use a mesma data e o mesmo índice para não atribuir ao sistema uma diferença criada "
                    "pelas premissas.\n\n"
                    "A capacidade de suportar a parcela inicial é tão relevante quanto o total projetado. Uma "
                    "prestação menor que depende de prazo mais longo pode aumentar a exposição a juros e seguro."
                ),
            },
            {
                "heading": "Contrato assinado deve bater com a execução",
                "text": (
                    "Depois da contratação, confira se taxa, sistema e indexador lançados correspondem ao instrumento. "
                    "Divergência documental pode justificar pedido de explicação e cálculo revisional; mera preferência "
                    "posterior pelo outro sistema não cria direito de troca retroativa.\n\n"
                    "Um advogado e, quando necessário, contador podem revisar uma inconsistência concreta. A análise "
                    "não deve prometer economia antes de comparar contrato, extrato e memória matemática. Guarde "
                    "também as simulações entregues antes da assinatura: elas ajudam a identificar se a divergência "
                    "veio de premissa informada, alteração contratual ou execução diferente do que foi pactuado."
                ),
            },
        ],
        faq=[{
            "q": "A Tabela Price é ilegal no financiamento imobiliário?",
            "a": (
                "Não por si só. O STJ exige análise fática para verificar eventual capitalização, considerando "
                "contrato, prova técnica, data e regime jurídico."
            ),
        }],
        sources=[
            (THEME_572, "STJ, Tema 572", "análise da capitalização na Tabela Price depende de fatos e pode exigir perícia"),
            (LAW_4380, "Lei 4.380/1964, art. 15-A", "possibilidade de pactuação de capitalização mensal nas operações do SFH"),
        ],
        links=["revisão de financiamento", "amortização extraordinária", "portabilidade de crédito imobiliário"],
    )

    update(
        by_id["imob-fgts-amortizar-financiamento"],
        title="FGTS no financiamento: amortizar, quitar ou pagar parcelas",
        meta="Veja a diferença entre amortização, liquidação e pagamento de 12 prestações, o intervalo de dois anos e os requisitos atuais para usar o FGTS.",
        h1="Como usar o FGTS durante o financiamento imobiliário",
        opening=(
            "O FGTS pode reduzir o saldo, liquidar a dívida ou pagar parte de prestações, mas cada modalidade tem "
            "limites próprios. O intervalo de dois anos vale para nova amortização ou liquidação pelo mesmo "
            "trabalhador; o pagamento parcial segue um ciclo de até doze prestações e limite de 80 por cento. "
            "Misturar essas regras costuma gerar indeferimento ou uma expectativa errada sobre parcelas atrasadas."
        ),
        sections=[
            {
                "heading": "Amortização reduz saldo, prazo ou encargo futuro",
                "text": (
                    "Na amortização, o valor sai da conta vinculada e abate o principal. Conforme contrato e opção "
                    "disponível, o recálculo pode encurtar o prazo ou diminuir o encargo. As prestações precisam estar "
                    "em dia na data do uso, segundo a orientação operacional do FGTS.\n\n"
                    "O trabalhador deve ser titular ou coobrigado do financiamento. Depois de uma amortização ou "
                    "liquidação com seus recursos, ele aguarda no mínimo dois anos para nova movimentação dessas "
                    "modalidades no mesmo vínculo aplicável."
                ),
            },
            {
                "heading": "Liquidação pode encerrar contrato com prestações em atraso",
                "text": (
                    "A liquidação usa o saldo disponível para quitar integralmente a operação. Diferentemente da "
                    "amortização parcial, a página oficial do FGTS admite prestações atrasadas quando o uso efetivamente "
                    "encerra a dívida. Se o saldo da conta não cobre tudo, é necessário complementar conforme cálculo "
                    "do agente financeiro.\n\n"
                    "Peça valor para uma data certa, porque juros e encargos podem mudar até a compensação. Após o "
                    "pagamento, ainda será preciso obter termo e cancelar a alienação na matrícula."
                ),
            },
            {
                "heading": "Pagamento parcial alcança até 80 por cento por doze prestações",
                "text": (
                    "Nessa modalidade, o saque é distribuído pelas próximas doze prestações, ou pelo período restante "
                    "se menor, e pode cobrir no máximo 80 por cento do total considerado. O trabalhador continua "
                    "responsável pela parte não coberta a cada vencimento.\n\n"
                    "A orientação vigente admite até seis prestações em atraso no pedido. Isso não suspende eventual "
                    "execução já iniciada nem garante enquadramento; o protocolo deve ser feito antes que a situação "
                    "registral mude."
                ),
            },
            {
                "heading": "SFH, SFI recente e consórcio podem entrar conforme a regra",
                "text": (
                    "O serviço oficial inclui contratos no SFH, operações fora do SFH celebradas a partir de 12 de "
                    "junho de 2021, autofinanciamento em consórcio e programas públicos de moradia, observados os "
                    "requisitos de cada modalidade. Não é correto dizer que todo contrato SFI está excluído nem que "
                    "qualquer empréstimo com imóvel em garantia aceita FGTS.\n\n"
                    "Data, finalidade habitacional, valor de avaliação e registro precisam ser validados pelo agente."
                ),
            },
            {
                "heading": "Trabalhador e imóvel passam por novo enquadramento",
                "text": (
                    "Em geral, exigem-se três anos de trabalho sob o regime do FGTS, períodos somados, destinação à "
                    "moradia e ausência de outro imóvel ou financiamento impeditivo nas condições do manual. O teto "
                    "do SFH está em R$ 2,25 milhões desde a Resolução CMN 5.255/2025, embora páginas antigas ainda "
                    "mostrem R$ 1,5 milhão.\n\n"
                    "Regime de bens, fração de propriedade, município de residência ou trabalho e financiamento já "
                    "existente exigem leitura individual. A declaração é renovada a cada movimentação."
                ),
            },
            {
                "heading": "Documentos e protocolo para escolher a modalidade",
                "text": (
                    "Separe identidade, extrato do FGTS, contrato, saldo devedor, matrícula, declaração de imposto de "
                    "renda e comprovantes de residência e ocupação. Solicite ao agente simulações de redução de prazo, "
                    "redução de encargo, liquidação e pagamento parcial.\n\n"
                    "Um advogado pode examinar indeferimento ou urgência da execução, mas não substitui a habilitação "
                    "do agente operador. O pedido deve usar a regra vigente na data, sem prometer liberação apenas "
                    "porque existe saldo na conta. Exija decisão escrita com o requisito não atendido; isso permite "
                    "corrigir documento, distinguir erro operacional de impedimento real e formular contestação "
                    "objetiva, sem reiniciar o pedido às cegas."
                ),
            },
        ],
        faq=[{
            "q": "Posso usar FGTS para pagar toda a prestação por doze meses?",
            "a": (
                "Não nessa modalidade. O limite é de até 80 por cento do valor considerado, e o mutuário paga o "
                "restante em cada vencimento."
            ),
        }],
        sources=[
            (LAW_FGTS, "Lei 8.036/1990, art. 20", "hipóteses legais de movimentação da conta para moradia própria"),
            (FGTS_AMORT, "FGTS, amortização, liquidação e prestações", "modalidades, intervalos, atrasos admitidos e requisitos operacionais"),
            (FGTS_MANUAL, "Manual da Moradia Própria, versão 035", "documentos e critérios vigentes desde dezembro de 2025"),
            (CMN_4676, "Resolução CMN 4.676 consolidada", "limite atual de R$ 2,25 milhões no SFH"),
        ],
        links=["quitação e baixa da alienação", "financiamento atrasado", "FGTS na compra do imóvel"],
    )

    update(
        by_id["imob-fgts-comprar-imovel-procedimento"],
        title="FGTS para comprar imóvel: requisitos e documentos",
        meta="Confira os três anos de trabalho, restrições de imóvel e SFH, teto de R$ 2,25 milhões, intervalo do imóvel e etapas para usar o FGTS.",
        h1="Como preparar o uso do FGTS na compra da moradia",
        opening=(
            "Ter saldo disponível não basta para usar o FGTS na compra. Trabalhador, imóvel e operação precisam se "
            "enquadrar na data da movimentação. A análise considera vínculos de três anos, financiamento ativo, "
            "propriedade em municípios relevantes, finalidade de moradia, valor de avaliação e histórico do próprio "
            "imóvel. Fazer essa triagem antes do sinal evita assumir obrigação contando com recurso que pode ser negado."
        ),
        sections=[
            {
                "heading": "Três anos de FGTS podem ser somados",
                "text": (
                    "O trabalhador precisa totalizar pelo menos três anos sob o regime do FGTS, consecutivos ou não e "
                    "em um ou mais empregadores. Não é necessário que todo o período venha do vínculo atual. Extrato "
                    "e carteira de trabalho ajudam a demonstrar lacunas ou contas vinculadas diferentes.\n\n"
                    "Cada comprador que usar seu saldo deve manifestar a intenção e cumprir os requisitos. O direito "
                    "de um integrante não regulariza automaticamente a situação do outro."
                ),
            },
            {
                "heading": "Outro financiamento SFH ou imóvel local pode impedir",
                "text": (
                    "Na data da aquisição, o trabalhador não pode ser titular de financiamento ativo no SFH em "
                    "qualquer parte do país. Também não pode ser proprietário, possuidor, promitente comprador, "
                    "cessionário ou usufrutuário de imóvel residencial no município de residência ou ocupação "
                    "principal, incluídos limítrofes e a mesma região metropolitana.\n\n"
                    "Há situações específicas de fração, usufruto, doação, herança e regime de bens. Elas devem ser "
                    "comprovadas pelo manual, e não resolvidas com uma declaração genérica de que o imóvel não é usado."
                ),
            },
            {
                "heading": "O imóvel deve servir à moradia e estar comercializável",
                "text": (
                    "A unidade deve ser residencial urbana, destinada à moradia do trabalhador e sem impedimento de "
                    "comercialização na matrícula. Em imóvel misto, somente a área residencial discriminada no laudo "
                    "pode receber o recurso. Construção exige modalidade e documentação próprias.\n\n"
                    "O local deve estar no município de trabalho ou residência, ou nas extensões admitidas. Para a "
                    "residência, o manual pode exigir prova temporal, por isso contas e declarações devem refletir a "
                    "situação verdadeira."
                ),
            },
            {
                "heading": "O teto atual do SFH é R$ 2,25 milhões",
                "text": (
                    "A Resolução CMN 5.255/2025 elevou o valor máximo de avaliação do SFH para R$ 2,25 milhões. O "
                    "Manual da Moradia remete ao limite vigente do CMN, embora algumas páginas do FGTS ainda exibam "
                    "o antigo R$ 1,5 milhão. A fonte normativa atual deve prevalecer na conferência.\n\n"
                    "O FGTS somado ao financiamento não pode ultrapassar o menor valor entre compra e venda e "
                    "avaliação. Preço declarado acima do laudo não cria saldo extra utilizável."
                ),
            },
            {
                "heading": "O histórico do imóvel também pode bloquear a operação",
                "text": (
                    "Se a aquisição ou construção anterior do mesmo imóvel usou FGTS, deve haver intervalo de três "
                    "anos entre as transações, contado do registro do contrato ou escritura. A restrição acompanha "
                    "o bem negociado e não se confunde com os três anos de trabalho exigidos do comprador.\n\n"
                    "A matrícula histórica e os títulos anteriores permitem verificar o marco. Perguntar apenas ao "
                    "vendedor pode não revelar uma utilização registrada recentemente."
                ),
            },
            {
                "heading": "Agente financeiro confere documentos antes da liberação",
                "text": (
                    "Apresente identificação, extrato, declarações, imposto de renda, estado civil e regime de bens, "
                    "comprovantes de trabalho e residência, matrícula e laudo. O agente avalia o enquadramento e "
                    "transfere o recurso dentro da operação; o dinheiro não é entregue livremente ao comprador.\n\n"
                    "A promessa de compra deve prever o que ocorre se o FGTS não for aprovado, sem transformar toda "
                    "negativa em culpa do vendedor. Orientação jurídica pode revisar cláusula e documentos, mas não "
                    "garante liberação antes da decisão do operador. Prazo de análise, restituição do sinal e dever "
                    "de cooperação documental devem estar escritos antes de qualquer pagamento relevante."
                ),
            },
        ],
        faq=[{
            "q": "O imóvel pode ter sido comprado com FGTS pelo vendedor?",
            "a": (
                "Pode, desde que se cumpra o intervalo de três anos entre aquela transação registrada e a nova "
                "aquisição que também usará FGTS."
            ),
        }],
        sources=[
            (LAW_FGTS, "Lei 8.036/1990, art. 20", "uso da conta vinculada para aquisição de moradia própria"),
            (FGTS_BUY, "FGTS, aquisição de imóvel novo ou usado", "requisitos do trabalhador, localização, destinação e intervalo do imóvel"),
            (FGTS_MANUAL, "Manual da Moradia Própria, versão 035", "documentos e critérios de aquisição vigentes"),
            (CMN_4676, "Resolução CMN 4.676 consolidada", "valor máximo atual de avaliação no SFH"),
        ],
        links=["FGTS para amortizar", "cláusula suspensiva na compra", "documentos da matrícula"],
    )

    update(
        by_id["imob-portabilidade-financiamento"],
        title="Portabilidade do financiamento imobiliário: etapas e custos",
        meta="Veja como pedir proposta ao novo banco, quais dados entram na requisição, os prazos entre instituições e a averbação da garantia em ato único.",
        h1="Como transferir o financiamento imobiliário para outro banco",
        opening=(
            "A portabilidade transfere a operação à instituição que aprovar uma nova proposta; não é um pedido de "
            "desconto ao banco atual nem entrega de dinheiro ao cliente. A instituição de destino analisa crédito e "
            "envia a requisição pelo sistema regulado. Se concluída, quita o saldo no banco de origem e recebe, em "
            "ato registral único, a sub-rogação da dívida e da garantia fiduciária ou hipotecária."
        ),
        sections=[
            {
                "heading": "Comece pelo Documento Descritivo do Crédito",
                "text": (
                    "O banco credor deve fornecer o DDC com número do contrato, saldo atualizado, evolução, modalidade, "
                    "taxas nominal e efetiva, prazo, sistema de pagamento, composição das prestações e último "
                    "vencimento. Esses dados permitem comparar propostas na mesma data.\n\n"
                    "Peça também CET, seguros, tarifas, indexador e matrícula. Parcela menor obtida apenas por prazo "
                    "mais longo pode aumentar o custo, e diferença de seguro pode consumir a redução de juros."
                ),
            },
            {
                "heading": "A solicitação formal é feita à instituição proponente",
                "text": (
                    "O devedor escolhe o possível banco de destino e apresenta pedido físico ou eletrônico. A "
                    "proponente, depois de aprovar a análise, envia à credora original taxa anual nominal e efetiva, "
                    "CET, prazo, amortização e prestações. Entregar documentos ao banco atual sem proposta aprovada "
                    "não inicia a mesma sequência regulatória.\n\n"
                    "A origem pode oferecer contraproposta, mas a decisão de permanecer é do cliente. Desistência "
                    "deve ser formal e registrada, não presumida por uma conversa de retenção."
                ),
            },
            {
                "heading": "Os bancos trocam recursos e confirmações em prazo regulado",
                "text": (
                    "Pelo fluxo comum, a instituição original tem até cinco dias úteis do recebimento da requisição "
                    "para solicitar o envio dos recursos; via Open Finance, o prazo informado pelo BC é de até três "
                    "dias úteis. Recebimento ou impedimento da transferência deve ser confirmado à proponente em até "
                    "dois dias úteis.\n\n"
                    "O processo completo pode levar até sete dias úteis quando os dados permitem a transferência, "
                    "sem contar análise prévia, avaliação e etapa registral. Guarde o código e a data da requisição."
                ),
            },
            {
                "heading": "Crédito imobiliário exige documento para averbação única",
                "text": (
                    "A Resolução CMN 5.057 determina que o documento contenha informações, declarações e assinaturas "
                    "necessárias para averbar, em um ato, a sub-rogação da dívida e da garantia. Não é preciso cancelar "
                    "o gravame e constituir outro em operações separadas como se fosse compra nova.\n\n"
                    "Financiamento no SFH deve continuar enquadrado no SFH. No SFI, as condições são negociadas, mas "
                    "a portabilidade ainda segue o fluxo regulado entre instituições."
                ),
            },
            {
                "heading": "Portabilidade não tem tarifa de transferência, mas compare despesas",
                "text": (
                    "Custos das comunicações entre os bancos não podem ser repassados, e a nova instituição é "
                    "responsável por quitar a dívida. Se o solicitante ainda não for cliente, pode existir tarifa de "
                    "cadastro. Avaliação do imóvel, averbação e seguros devem aparecer de forma clara na proposta ou "
                    "na política de isenção.\n\n"
                    "Calcule o ponto de equilíbrio entre essas despesas e a economia mensal. Não aceite procuração "
                    "irrestrita, contrato em branco ou operação com crédito adicional disfarçado de portabilidade."
                ),
            },
            {
                "heading": "Recusa ou atraso precisa ser documentado",
                "text": (
                    "A proponente pode negar novo crédito por sua análise; isso é diferente de a credora original "
                    "bloquear requisição regular. Peça motivo, protocolo e DDC, e registre reclamação nos canais da "
                    "instituição antes do Banco Central ou defesa do consumidor.\n\n"
                    "Um advogado pode analisar entrave registral, tarifa ou descumprimento de prazo. Não cabe prometer "
                    "aprovação pela nova instituição nem economia sem proposta final e CET comparável. Se a origem "
                    "alegar impedimento, preserve a resposta e confira saldo, contrato e código no sistema; erro de "
                    "identificação pode ser corrigido sem transformar a falha em nova contratação fora da "
                    "portabilidade."
                ),
            },
        ],
        faq=[{
            "q": "O banco atual pode impedir a portabilidade porque não quer perder o contrato?",
            "a": (
                "Não pode bloquear uma requisição regular por esse motivo, embora possa fazer contraproposta. A "
                "instituição de destino ainda precisa aprovar o novo crédito."
            ),
        }],
        sources=[
            (CMN_5057, "Resolução CMN 5.057 consolidada", "regras da portabilidade e averbação imobiliária em ato único"),
            (BCB_PORTABILITY, "Banco Central, passo a passo da portabilidade", "requisição, prazos e confirmações entre instituições"),
            (BCB_DDC, "Banco Central, Documento Descritivo do Crédito", "informações que o credor deve fornecer para comparar e transferir a dívida"),
        ],
        links=["SAC ou Price", "revisão do financiamento", "baixa da alienação fiduciária"],
    )

    changed = {
        "imob-tabela-sac-vs-price",
        "imob-fgts-amortizar-financiamento",
        "imob-fgts-comprar-imovel-procedimento",
        "imob-portabilidade-financiamento",
    }
    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-options.", dir=os.path.dirname(TARGET))
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
    for intent in sorted(changed):
        print(f"{intent}: {by_id[intent]['word_count']} palavras")
    print(f"sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
