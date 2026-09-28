#!/usr/bin/env python3
"""Reescreve o shard imobiliario-07 após revisão jurídica de fonte primária."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path


TARGET = Path("data/editorial/v2_pages/imobiliario-07.jsonl")
EXPECTED_SHA256 = {
    "a61911e62b34a4eb85b47f0069a305ef555493ab2586c0ee4582d789afafc4c2",
    "9da76bf04ca741bdca6cc32dd31998c57a20de5b17e4e5311c59b2495796115b",
}


def words(value):
    folded = "".join(
        char for char in unicodedata.normalize("NFD", (value or "").lower())
        if unicodedata.category(char) != "Mn"
    )
    return re.findall(r"[^\W_]+", folded, re.UNICODE)


def body_word_count(page):
    values = [page.get("opening", "")]
    for section in page.get("sections", []):
        values.extend((section.get("heading", ""), section.get("text", "")))
    for item in page.get("faq", []):
        values.extend((item.get("q", ""), item.get("a", "")))
    return sum(len(words(value)) for value in values)


def section(heading, text):
    return {"heading": heading, "text": text}


def faq(question, answer):
    return {"q": question, "a": answer}


def apply_text(page, *, title, meta, h1, opening, sections, faqs):
    page["title"] = title
    page["meta_description"] = meta
    page["h1"] = h1
    page["opening"] = opening
    page["sections"] = sections
    page["faq"] = faqs


def set_sources(page, specs):
    previous = {item["url"]: item for item in page.get("official_sources", [])}
    sources = []
    for url, name, claim in specs:
        source = {"url": url, "name": name, "anchor_claim": claim}
        old = previous.get(url)
        if old is not None:
            for field in ("verified_at", "http_status"):
                if field in old:
                    source[field] = old[field]
        sources.append(source)
    page["official_sources"] = sources


def rewrite_morte(page):
    apply_text(
        page,
        title="Morte do locatário empresário: quem continua no ponto",
        meta=(
            "Saiba como a morte do locatário afeta a loja, quem se sub-roga no contrato "
            "e quais comunicações protegem locador, espólio, sucessor e fiador."
        ),
        h1="O empresário morreu: quem assume a locação da loja?",
        opening=(
            "A morte de quem assinou a locação comercial não encerra, por si só, o contrato. "
            "A Lei do Inquilinato identifica quem ocupa a posição do locatário e exige cuidado "
            "com uma distinção decisiva: ser herdeiro não equivale automaticamente a suceder no "
            "negócio. Também é incorreto presumir que a garantia permanece inalterada. A resposta "
            "depende de quem era o locatário, de quem continuará a atividade e das comunicações "
            "feitas ao locador e ao fiador."
        ),
        sections=[
            section(
                "Espólio e sucessor no negócio ocupam posições diferentes",
                (
                    "O art. 11, II, da Lei 8.245/1991 determina que, na locação não residencial, "
                    "a morte do locatário sub-roga o espólio e, se for o caso, o sucessor no negócio. "
                    "Durante a administração da herança, o inventariante representa o espólio. A "
                    "passagem posterior exige identificar quem efetivamente recebeu e continuará a "
                    "empresa ou atividade explorada no imóvel. A partilha de um bem a determinado "
                    "herdeiro, isoladamente, não transforma qualquer familiar em sucessor empresarial."
                ),
            ),
            section(
                "A morte de sócio não é sempre a morte do locatário",
                (
                    "Antes de invocar a sub-rogação, é necessário conferir o nome que consta como "
                    "locatário. Se uma sociedade empresária assinou o contrato e apenas um de seus "
                    "sócios morreu, a pessoa jurídica continua existindo e permanece como locatária, "
                    "salvo efeito específico do contrato ou da reorganização societária. Se o contrato "
                    "foi assinado pelo empresário individual falecido, entram em cena o espólio e o "
                    "eventual sucessor no negócio, nos termos do art. 11, II."
                ),
            ),
            section(
                "Comunicação escrita e exoneração do fiador",
                (
                    "O art. 12, § 1º, estende às hipóteses do art. 11 o dever de comunicar a "
                    "sub-rogação por escrito ao locador e ao fiador, quando houver fiança. Recebida a "
                    "comunicação, o fiador pode notificar o locador de sua exoneração em até trinta "
                    "dias. Nessa situação, o § 2º mantém sua responsabilidade por cento e vinte dias "
                    "depois da notificação. Por isso, não se deve afirmar que a fiança segue para sempre "
                    "nem que desaparece no dia do óbito."
                ),
            ),
            section(
                "Documentos que esclarecem a continuidade",
                (
                    "Contrato de locação, certidão de óbito, termo de inventariança, atos societários e "
                    "documentos de transferência do estabelecimento ajudam a demonstrar quem responde "
                    "pelo vínculo. A comunicação deve registrar a data de recebimento pelo locador e pelo "
                    "fiador, pois dela podem decorrer prazos relevantes. Um aditamento pode organizar a "
                    "relação, mas não deve substituir a análise da sub-rogação que já decorre da lei."
                ),
            ),
            section(
                "Como organizar o caso sem presumir o resultado",
                (
                    "Em uma papelaria mantida por empresário individual, por exemplo, o espólio pode "
                    "prosseguir no contrato enquanto se apura quem continuará o negócio. Se uma filha "
                    "receber e assumir a atividade, a documentação empresarial e sucessória deve mostrar "
                    "essa continuidade. O contrato e a fiança precisam ser revistos separadamente. Em "
                    "casos com inventário litigioso, aluguel em atraso ou dúvida sobre a empresa, a "
                    "orientação jurídica serve para definir comunicações e responsabilidades, sem prometer "
                    "que o locador aceitará toda solução proposta."
                ),
            ),
        ],
        faqs=[
            faq(
                "Qualquer herdeiro pode assumir a loja alugada?",
                (
                    "Não automaticamente. A lei menciona o espólio e, se houver, o sucessor no negócio; "
                    "é preciso demonstrar quem continuará a atividade e como ocorreu a sucessão."
                ),
            ),
            faq(
                "A fiança termina com a morte do locatário?",
                (
                    "Não de forma automática. A sub-rogação deve ser comunicada, e o fiador dispõe de "
                    "trinta dias para notificar sua exoneração, mantendo responsabilidade por cento e "
                    "vinte dias após essa notificação."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art11",
            "Lei 8.245/1991, art. 11, II",
            "sub-rogação do espólio e, se for o caso, do sucessor no negócio na locação não residencial",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art12",
            "Lei 8.245/1991, art. 12, §§ 1º e 2º",
            "comunicação escrita da sub-rogação e exoneração do fiador em trinta dias, com responsabilidade residual de cento e vinte dias",
        ),
    ])


def rewrite_desapropriacao(page):
    apply_text(
        page,
        title="Desapropriação de imóvel alugado: direito do lojista",
        meta=(
            "Entenda o direito próprio do locatário comercial diante da desapropriação, a "
            "indenização do fundo de comércio e a necessidade de provar cada prejuízo."
        ),
        h1="O imóvel da loja foi desapropriado: o locatário pode ser indenizado?",
        opening=(
            "A desapropriação atinge o proprietário do imóvel e também pode causar dano direto ao "
            "comerciante que operava ali como locatário. Esses interesses não se confundem. O valor "
            "pago pelo terreno e pela construção não resolve necessariamente a perda suportada pelo "
            "negócio, mas o reconhecimento do direito do lojista também não produz um valor automático. "
            "É necessário demonstrar o fundo de comércio afetado, os demais danos ligados à retirada "
            "compulsória e o nexo com o procedimento expropriatório."
        ),
        sections=[
            section(
                "O direito do locatário não depende da relação com o proprietário",
                (
                    "No REsp 406.502/SP, divulgado no Informativo 131, o STJ reconheceu ao locatário "
                    "comercial despojado do fundo de comércio o direito ao ressarcimento por perdas e "
                    "danos. O tribunal registrou que essa proteção existe independentemente das relações "
                    "jurídicas entre proprietário e inquilino e esteja o locatário protegido, ou não, pela "
                    "antiga Lei de Luvas. Portanto, preencher os requisitos da ação renovatória não é "
                    "condição universal para existir a pretensão indenizatória."
                ),
            ),
            section(
                "A indenização do proprietário tem objeto diferente",
                (
                    "O Decreto-Lei 3.365/1941 organiza a desapropriação do bem. O proprietário discute a "
                    "justa indenização pela perda do imóvel, enquanto o locatário pode alegar dano próprio "
                    "decorrente da desarticulação da atividade. A mesma rubrica não pode ser paga duas "
                    "vezes. Por isso, laudos e documentos devem separar o que pertence ao imóvel, o que "
                    "integra o estabelecimento do locatário e o que representa perda efetivamente causada "
                    "pela retirada."
                ),
            ),
            section(
                "Fundo de comércio exige demonstração concreta",
                (
                    "Tempo de funcionamento, desempenho contábil, clientela vinculada ao ponto, contratos, "
                    "investimentos, registros financeiros contemporâneos e possibilidade real de transferência são elementos que podem ser "
                    "examinados. Nenhum deles, sozinho, fixa a indenização. Um empreendimento sem resultado "
                    "econômico comprovável ou capaz de mudar sem perda relevante pode receber avaliação "
                    "diferente de um negócio consolidado cuja localização seja essencial. O precedente "
                    "assegura a possibilidade jurídica do ressarcimento, não uma tabela de valores nem êxito "
                    "em todo caso."
                ),
            ),
            section(
                "Habilitação e ação própria não são escolhas automáticas",
                (
                    "A forma de apresentar a pretensão depende da fase do processo, das partes já presentes, "
                    "do objeto discutido e das regras processuais aplicáveis ao ente expropriante. Pode ser "
                    "pertinente pedir ingresso no procedimento existente ou discutir perdas e danos em ação "
                    "própria, mas a habilitação não é uma via única prometida pela decisão do STJ. A análise "
                    "precoce evita escolher um pedido incompatível com o estágio do processo."
                ),
            ),
            section(
                "Provas que devem ser preservadas desde a ciência da desapropriação",
                (
                    "Contrato de locação, atos expropriatórios, balanços, notas fiscais, inventário de bens, "
                    "licenças e registros de mudança ajudam a reconstruir o cenário anterior e posterior. "
                    "Também é importante documentar datas, comunicações e despesas sem produzir estimativas "
                    "artificiais. A prescrição, a competência e o rito variam conforme o ente público e a "
                    "pretensão formulada; não é seguro aguardar o encerramento do processo do proprietário "
                    "sem avaliar esses marcos."
                ),
            ),
            section(
                "Exemplo de apuração sem valor prefixado",
                (
                    "Uma padaria que funciona há anos em imóvel locado recebe ordem de desocupação em razão "
                    "de obra viária. O proprietário apresenta laudo do terreno e da construção. A empresa, "
                    "por sua vez, reúne contabilidade, prova da clientela ligada ao endereço, custos de "
                    "transferência e dados sobre eventual perda operacional. A perícia deve evitar misturar "
                    "benfeitorias já consideradas na indenização imobiliária com danos próprios do negócio. "
                    "A assistência jurídica e técnica serve para definir a via e organizar a prova, não para "
                    "garantir um montante antecipadamente."
                ),
            ),
        ],
        faqs=[
            faq(
                "Só tem direito quem poderia propor ação renovatória?",
                (
                    "Não. No REsp 406.502/SP, o STJ afirmou que o ressarcimento do locatário comercial "
                    "despojado do fundo de comércio independe de proteção pela Lei de Luvas."
                ),
            ),
            faq(
                "O locatário deve obrigatoriamente se habilitar no processo do dono?",
                (
                    "Não há resposta única. O meio processual depende da fase, do objeto e das partes do "
                    "caso; ingresso no processo e ação própria precisam ser comparados tecnicamente."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3365.htm",
            "Decreto-Lei 3.365/1941",
            "regime geral da desapropriação por utilidade pública e da indenização pelo bem expropriado",
        ),
        (
            "https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40CNOT%3D%27002932%27",
            "STJ, Informativo 131, REsp 406.502/SP",
            "direito do locatário comercial ao ressarcimento, inclusive do fundo de comércio, independentemente da relação com o proprietário",
        ),
        (
            "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/IMGD?dt=20020527&formato=PDF&nreg=200200079510&salvar=false&seq=51763&tipo=0",
            "STJ, inteiro teor do REsp 406.502/SP",
            "cabimento de perdas e danos ao locatário despojado do fundo de comércio, protegido ou não pela Lei de Luvas",
        ),
    ])


def rewrite_preferencia(page):
    apply_text(
        page,
        title="Preferência do lojista na venda do imóvel alugado",
        meta=(
            "Veja em quais negócios o locatário comercial tem preferência, como funciona o "
            "prazo de trinta dias e quais são as exceções do art. 32."
        ),
        h1="Quando o lojista tem preferência para comprar o imóvel?",
        opening=(
            "O locatário não recebe preferência em toda mudança de propriedade. A Lei 8.245/1991 "
            "define uma lista de negócios sujeitos à oferta e outra lista de situações excluídas. "
            "Também distingue a aceitação da proposta, o pedido de perdas e danos e a pretensão de "
            "adquirir o imóvel do terceiro. Conferir a operação, a comunicação e a averbação do "
            "contrato evita aplicar o prazo certo ao negócio errado."
        ),
        sections=[
            section(
                "Operações alcançadas pelo art. 27",
                (
                    "O art. 27 assegura preferência em igualdade de condições na venda, promessa de "
                    "venda, cessão ou promessa de cessão de direitos e dação em pagamento. A comunicação "
                    "deve informar as condições do negócio, especialmente preço, forma de pagamento, "
                    "existência de ônus reais e local e horário em que a documentação pode ser examinada. "
                    "Permuta, doação e usufruto não devem ser acrescentados a essa lista como se estivessem "
                    "no caput do dispositivo."
                ),
            ),
            section(
                "Aceitação inequívoca em trinta dias",
                (
                    "Pelo art. 28, o direito caduca se o locatário não aceitar a proposta de forma "
                    "inequívoca no prazo de trinta dias. A contagem pressupõe ciência de uma comunicação "
                    "com condições suficientes para a decisão. Uma resposta que muda preço, prazo ou forma "
                    "de pagamento pode representar contraproposta, e não exercício da preferência em "
                    "igualdade com o terceiro. A prova do recebimento e do conteúdo de ambas as mensagens "
                    "é central."
                ),
            ),
            section(
                "Exclusões expressas do art. 32",
                (
                    "A preferência não alcança perda da propriedade ou venda por decisão judicial, permuta, "
                    "doação, integralização de capital, cisão, fusão e incorporação. Para contratos firmados "
                    "a partir de 1º de outubro de 2001, o parágrafo único também trata da constituição de "
                    "propriedade fiduciária e da perda da propriedade ou venda por formas de realização de "
                    "garantia. Nessa hipótese adicional, a condição deve constar destacadamente em cláusula "
                    "contratual específica."
                ),
            ),
            section(
                "Venda sem respeito à preferência",
                (
                    "O art. 33 permite ao locatário preterido reclamar perdas e danos. Para haver o imóvel "
                    "para si, porém, existem requisitos adicionais: depósito do preço e das despesas do ato "
                    "de transferência, pedido em até seis meses do registro da alienação e contrato de "
                    "locação averbado na matrícula pelo menos trinta dias antes dessa alienação. A simples "
                    "existência de contrato escrito não substitui a averbação para essa tutela contra o "
                    "adquirente."
                ),
            ),
            section(
                "A averbação muda o remédio disponível",
                (
                    "Sem averbação tempestiva, pode subsistir a pretensão de perdas e danos contra quem "
                    "descumpriu a preferência, mas não se deve prometer a transferência do imóvel do terceiro. "
                    "Com a averbação, ainda será necessário provar a preterição e cumprir depósito e prazo. "
                    "Matrícula atualizada, contrato, comprovante da averbação, notificação, proposta do "
                    "terceiro e escritura ou registro formam o núcleo documental da análise."
                ),
            ),
            section(
                "Condições diferentes exigem nova comparação",
                (
                    "A preferência deve refletir o negócio efetivamente celebrado. Se o preço, a entrada, "
                    "o parcelamento ou outra condição relevante muda depois da primeira comunicação, não é "
                    "seguro tratar a recusa anterior como renúncia permanente. Deve-se comparar a oferta "
                    "recebida pelo locatário com o instrumento levado a registro e verificar se surgiu uma "
                    "oportunidade distinta. A lei protege igualdade de condições, não prioridade abstrata "
                    "sobre qualquer negociação futura."
                ),
            ),
            section(
                "Como conferir uma proposta na prática",
                (
                    "Se o locador informa que venderá a sala por determinado preço parcelado, o lojista deve "
                    "verificar se recebeu todos os termos e se consegue aceitá-los sem reservas dentro de "
                    "trinta dias. Se depois descobrir registro por preço ou forma diferentes, será preciso "
                    "comparar os negócios e a situação registral da locação. A revisão jurídica rápida ajuda "
                    "a preservar prova e prazo, mas não transforma permuta, doação ou execução judicial em "
                    "venda voluntária sujeita ao art. 27."
                ),
            ),
        ],
        faqs=[
            faq(
                "A preferência existe se o imóvel for dado em permuta?",
                "Não. A permuta aparece entre as exclusões expressas do art. 32 da Lei 8.245/1991.",
            ),
            faq(
                "Sem averbação o lojista perde toda proteção?",
                (
                    "Não necessariamente. O art. 33 prevê perdas e danos, mas a pretensão de haver o imóvel "
                    "do adquirente exige averbação anterior, depósito e observância do prazo de seis meses."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art27",
            "Lei 8.245/1991, art. 27",
            "negócios sujeitos ao direito de preferência e conteúdo da comunicação ao locatário",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art28",
            "Lei 8.245/1991, art. 28",
            "caducidade da preferência se a proposta não for aceita inequivocamente em trinta dias",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art32",
            "Lei 8.245/1991, art. 32",
            "exclusões da preferência e condição destacada para propriedade fiduciária e realização de garantia",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art33",
            "Lei 8.245/1991, art. 33",
            "perdas e danos e requisitos para o locatário preterido haver o imóvel do adquirente",
        ),
    ])


def rewrite_garantias(page):
    apply_text(
        page,
        title="Garantias na locação comercial: modalidades e troca",
        meta=(
            "Conheça as garantias permitidas no aluguel comercial, o limite da caução em dinheiro "
            "e as hipóteses legais de substituição durante o contrato."
        ),
        h1="Quais garantias podem ser exigidas na locação comercial?",
        opening=(
            "A locação de loja, sala ou galpão não autoriza criar qualquer garantia nem acumulá-las. "
            "A Lei do Inquilinato traz modalidades determinadas, disciplina a caução em dinheiro e "
            "prevê situações em que o locador pode exigir substituição. A leitura conjunta dos arts. "
            "37 a 40 evita dois erros opostos: empilhar garantias no início e afirmar que a garantia "
            "jamais pode mudar depois da assinatura."
        ),
        sections=[
            section(
                "Quatro modalidades e apenas uma por contrato",
                (
                    "O art. 37 enumera caução, fiança, seguro de fiança locatícia e cessão fiduciária "
                    "de quotas de fundo de investimento. Seu parágrafo único proíbe mais de uma modalidade "
                    "no mesmo contrato. Assim, não se pode exigir simultaneamente caução e fiador para "
                    "garantir a mesma locação. Produtos oferecidos pelo mercado precisam ser juridicamente "
                    "classificados; o nome comercial não cria uma quinta modalidade legal."
                ),
            ),
            section(
                "Caução em dinheiro tem teto e destino definidos",
                (
                    "Segundo o art. 38, § 2º, a caução em dinheiro não pode exceder três meses de aluguel e "
                    "deve ser depositada em caderneta de poupança. As vantagens da aplicação revertem ao "
                    "locatário no levantamento, descontadas as obrigações legitimamente apuradas. Caução em "
                    "bens móveis ou imóveis segue formalidades próprias e não deve ser confundida com esse "
                    "limite específico da caução em dinheiro."
                ),
            ),
            section(
                "Alcance da garantia até a devolução do imóvel",
                (
                    "O art. 39 estabelece que, salvo disposição contratual em contrário, a garantia se "
                    "estende até a efetiva devolução do imóvel, ainda que a locação tenha sido prorrogada por "
                    "prazo indeterminado. Essa regra geral convive com exoneração, comunicação e outras "
                    "hipóteses previstas na própria lei. Portanto, não autoriza dizer que toda garantia "
                    "sobrevive invariavelmente a qualquer mudança pessoal ou contratual."
                ),
            ),
            section(
                "Quando o art. 40 permite exigir nova garantia",
                (
                    "O art. 40 reúne situações como morte, ausência, interdição, recuperação, falência ou "
                    "insolvência do fiador, alienação de seus imóveis, exoneração, desaparecimento ou perda "
                    "do bem caucionado e término de determinadas garantias institucionais. Também disciplina "
                    "casos de prorrogação e manifestação de quem não pretende manter a garantia. Verificada "
                    "uma hipótese legal, o locador pode notificar o locatário para apresentar nova garantia "
                    "em trinta dias, sob pena de desfazimento da locação."
                ),
            ),
            section(
                "Substituição negociada e substituição exigida",
                (
                    "As partes podem acordar a troca de modalidade por aditamento, desde que eliminem a "
                    "garantia anterior e não produzam cumulação proibida. Em separado, o art. 40 autoriza o "
                    "locador a exigir nova garantia nas hipóteses que enumera. Antes de recusar ou exigir a "
                    "troca, é necessário verificar o evento, a redação do contrato, a notificação e o prazo. "
                    "A revisão jurídica da minuta ou da cobrança deve esclarecer esses pontos sem prometer "
                    "aceitação de uma modalidade específica."
                ),
            ),
        ],
        faqs=[
            faq(
                "O locador pode exigir fiador e caução ao mesmo tempo?",
                "Não. O art. 37, parágrafo único, veda mais de uma modalidade de garantia no mesmo contrato.",
            ),
            faq(
                "A garantia pode mudar durante a locação?",
                (
                    "Sim, por acordo que evite cumulação ou quando ocorrer hipótese do art. 40. Neste último "
                    "caso, a lei prevê notificação para nova garantia em trinta dias."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art37",
            "Lei 8.245/1991, art. 37",
            "modalidades de garantia locatícia e proibição de exigir mais de uma no mesmo contrato",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art38",
            "Lei 8.245/1991, art. 38",
            "formas de caução e limite de três meses com depósito em poupança para a caução em dinheiro",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art39",
            "Lei 8.245/1991, art. 39",
            "alcance temporal da garantia, salvo disposição contratual em contrário",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art40",
            "Lei 8.245/1991, art. 40",
            "hipóteses de exigência de nova garantia e prazo de trinta dias após notificação",
        ),
    ])


def rewrite_quiosque(page):
    apply_text(
        page,
        title="Quiosque e estande: quando existe locação comercial",
        meta=(
            "Entenda como o conteúdo do contrato define se quiosque ou estande é locação, ajuste "
            "atípico ou relação de shopping, e quando cabe renovatória."
        ),
        h1="Quiosque ou estande tem direito à renovação do espaço?",
        opening=(
            "O nome impresso no contrato não resolve a natureza jurídica de um quiosque, box ou "
            "estande. É preciso examinar a área cedida, a exclusividade, a duração, os serviços, "
            "a ligação com um evento e a organização do empreendimento. Um espaço pequeno pode "
            "integrar uma locação; outro, visualmente parecido, pode ser objeto de participação "
            "temporária ou contrato misto. A consequência para a ação renovatória vem dessa "
            "classificação e dos requisitos legais, não da palavra usada pelas partes."
        ),
        sections=[
            section(
                "A realidade do uso vem antes do rótulo",
                (
                    "O art. 1º da Lei 8.245/1991 delimita as locações de imóveis urbanos submetidas ao seu "
                    "regime. Para saber se o espaço integra esse campo, deve-se verificar se há cessão de "
                    "área identificável por determinado período e mediante remuneração, além do peso dos "
                    "serviços e regras coletivas. Chamar a cobrança de taxa de participação ou aluguel é "
                    "um indício, mas não substitui a leitura das obrigações efetivas."
                ),
            ),
            section(
                "Renovatória exige requisitos cumulativos",
                (
                    "Mesmo quando houver locação não residencial, o art. 51 não concede renovação a todo "
                    "ocupante. O instrumento deve ser escrito e ter prazo certo; contratos sucessivos precisam "
                    "alcançar cinco anos sem interrupção, e a exploração do mesmo ramo deve durar ao menos três "
                    "anos. A ação ainda deve observar a janela legal anterior ao fim do contrato. Um quiosque "
                    "fixo com apenas três anos de vínculo, por exemplo, não satisfaz sozinho o requisito "
                    "temporal."
                ),
            ),
            section(
                "Quiosque em shopping tem disciplina própria",
                (
                    "Quando o quiosque integra shopping center, o art. 54 reconhece as condições livremente "
                    "pactuadas entre lojista e empreendedor, sem afastar as disposições procedimentais da Lei "
                    "do Inquilinato e os limites do próprio artigo. Isso não significa que todo quiosque de "
                    "corredor seja automaticamente uma locação renovável. Contrato, localização, prazo e "
                    "atividade precisam preencher o regime e os requisitos correspondentes."
                ),
            ),
            section(
                "Evento temporário pode formar contrato misto ou atípico",
                (
                    "Um estande vinculado a uma feira de poucos dias costuma envolver credenciamento, "
                    "montagem, segurança, divulgação e acesso ao público, além do uso físico. O art. 425 do "
                    "Código Civil permite contratos atípicos, observadas as normas gerais. A predominância "
                    "desses elementos e a ausência de estabilidade podem afastar a caracterização de uma "
                    "locação comercial típica, mas a duração curta, isoladamente, não autoriza ignorar todo "
                    "o conteúdo do ajuste."
                ),
            ),
            section(
                "Comparação prática sem conclusão automática",
                (
                    "Um quiosque delimitado em shopping, ocupado de modo contínuo por contratos escritos "
                    "sucessivos, pode reunir elementos de locação e ainda precisará cumprir o art. 51. Já o "
                    "estande montado apenas para uma feira anual, com pacote de serviços e término ligado ao "
                    "evento, aponta para estrutura diferente. A revisão jurídica deve comparar documentos e "
                    "execução real antes de afirmar que há despejo, renovatória ou simples encerramento do "
                    "contrato."
                ),
            ),
        ],
        faqs=[
            faq(
                "Todo quiosque fixo dá direito à ação renovatória?",
                (
                    "Não. Primeiro é preciso caracterizar a locação e, depois, comprovar cumulativamente os "
                    "requisitos de contrato escrito, prazos e continuidade do ramo previstos no art. 51."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art1",
            "Lei 8.245/1991, art. 1º",
            "campo de aplicação da Lei do Inquilinato e exclusões legais",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art51",
            "Lei 8.245/1991, art. 51",
            "requisitos cumulativos e prazo de ajuizamento da ação renovatória",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art54",
            "Lei 8.245/1991, art. 54",
            "regime das relações entre lojistas e empreendedores de shopping center",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art425",
            "Código Civil, art. 425",
            "possibilidade de contratos atípicos observadas as normas gerais do Código Civil",
        ),
    ])


def rewrite_coworking(page):
    apply_text(
        page,
        title="Coworking: contrato atípico, misto ou locação",
        meta=(
            "Coworking não recebe classificação automática: cessão exclusiva, serviços e execução "
            "real indicam se há contrato atípico, misto ou locação."
        ),
        h1="Coworking é locação? A resposta depende do contrato real",
        opening=(
            "Coworking descreve modelos bastante diferentes. Alguns oferecem posições rotativas, "
            "recepção, internet e salas sob reserva; outros cedem uma sala fechada e exclusiva por "
            "longo período, com poucos serviços relevantes. A classificação jurídica não decorre "
            "do nome coworking nem de uma regra segundo a qual esse contrato nunca seria locação. "
            "Ela depende do objeto predominante e da forma como a relação é executada."
        ),
        sections=[
            section(
                "Serviços e compartilhamento apontam para ajuste misto",
                (
                    "Quando o usuário contrata acesso flexível a áreas comuns, estações não exclusivas, "
                    "recepção, internet, limpeza, correspondência e salas mediante reserva, o conjunto pode "
                    "formar contrato misto ou atípico. O art. 425 do Código Civil permite que as partes "
                    "estruturem contratos atípicos, desde que respeitem as normas gerais. Nenhum serviço "
                    "isolado, porém, elimina automaticamente um componente locatício."
                ),
            ),
            section(
                "Cessão exclusiva pode aproximar a relação da locação",
                (
                    "Uma sala determinada, entregue com exclusividade, por prazo e remuneração definidos, "
                    "pode revelar predominância da cessão de uso do imóvel. Nessa situação, os serviços "
                    "acessórios não bastam para afastar a possível incidência da Lei 8.245/1991. O art. 1º "
                    "delimita seu campo, mas a aplicação ao caso exige examinar espaço, controle de acesso, "
                    "prazo, preço, autonomia do ocupante e finalidade."
                ),
            ),
            section(
                "Ritos e direitos acompanham a classificação comprovada",
                (
                    "Não é seguro prometer que o operador jamais precisará de ação de despejo ou que o "
                    "usuário nunca poderá discutir renovatória. Se predominar um contrato de serviços ou "
                    "atípico, tendem a valer as cláusulas de resolução e as regras gerais do Código Civil. "
                    "Se a relação for reconhecida como locação, entram em análise os instrumentos da Lei do "
                    "Inquilinato e seus requisitos específicos."
                ),
            ),
            section(
                "Documentos úteis para uma classificação responsável",
                (
                    "Contrato, planta ou identificação da sala, regras de uso, notas fiscais, pacote de "
                    "serviços, controle de chaves e prática cotidiana mostram o que foi realmente cedido. "
                    "A avaliação deve evitar conclusões universais e indicar quais fatos mudariam o regime. "
                    "Em controvérsia concreta, uma análise jurídica individualizada pode organizar esses "
                    "elementos sem antecipar o resultado judicial."
                ),
            ),
        ],
        faqs=[
            faq(
                "Ter internet e recepção impede que exista locação?",
                (
                    "Não. Esses serviços são relevantes, mas devem ser comparados com a exclusividade, a "
                    "duração e a predominância da cessão do espaço no caso concreto."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art425",
            "Código Civil, art. 425",
            "liberdade para estipular contratos atípicos dentro das normas gerais",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art1",
            "Lei 8.245/1991, art. 1º",
            "campo de aplicação da locação de imóvel urbano e exclusões legais",
        ),
    ])


def rewrite_rural(page):
    apply_text(
        page,
        title="Imóvel rural para empresa: arrendamento ou locação",
        meta=(
            "Veja como a destinação agrária, a retribuição e a partilha de riscos diferenciam "
            "arrendamento rural, parceria e uso comercial não agrário."
        ),
        h1="O contrato da empresa no imóvel rural é arrendamento?",
        opening=(
            "A matrícula rural e o nome dado ao contrato não bastam para classificá-lo. O Estatuto "
            "da Terra e o Decreto 59.566/1966 olham para o uso temporário da terra com atividade "
            "agrícola, pecuária, agroindustrial, extrativa ou mista. Dentro desse campo, ainda é "
            "necessário distinguir arrendamento de parceria. Fora dele, o uso empresarial pode "
            "seguir outro regime, mas a Lei do Inquilinato também não se aplica automaticamente "
            "apenas porque existe uma empresa no local."
        ),
        sections=[
            section(
                "Destinação agrária define o primeiro enquadramento",
                (
                    "Os arts. 92 e seguintes do Estatuto da Terra disciplinam a posse ou o uso temporário "
                    "da terra para exploração agrária. O art. 3º do Decreto 59.566/1966 define o arrendamento "
                    "rural como cessão do uso e gozo de imóvel rural para exploração agrícola, pecuária, "
                    "agroindustrial, extrativa ou mista, mediante certa retribuição ou aluguel. A atividade "
                    "real pesa mais do que expressões genéricas do instrumento."
                ),
            ),
            section(
                "Retribuição certa não se confunde com partilha",
                (
                    "No arrendamento, o preço é fixado em quantia certa e pode ser pago em dinheiro ou em "
                    "equivalente de frutos ou produtos, observadas as regras e limites do art. 95 e do "
                    "decreto. Na parceria do art. 96, há partilha de riscos do empreendimento e de frutos, "
                    "produtos ou lucros nas proporções ajustadas. A presença de produto rural como meio de "
                    "pagamento não transforma, sozinha, o arrendamento em parceria."
                ),
            ),
            section(
                "Percentual isolado não resolve a natureza do contrato",
                (
                    "É incorreto afirmar que qualquer percentual é proibido e produz parceria automática. "
                    "É preciso saber se a cláusula apenas converte uma retribuição certa, se respeita os "
                    "limites legais ou se distribui produção e riscos entre as partes. Gestão, despesas, "
                    "caso fortuito, resultado negativo e forma efetiva de acerto ajudam a distinguir os "
                    "modelos. Cláusulas contrárias às normas agrárias obrigatórias não se tornam válidas pelo "
                    "rótulo escolhido."
                ),
            ),
            section(
                "Uso não agrário exige uma segunda análise",
                (
                    "Um galpão empregado apenas para logística, uma antena ou um pátio industrial podem não "
                    "formar contrato agrário, pois não há exploração da terra nas atividades descritas pelo "
                    "Estatuto. Ainda assim, a incidência da Lei 8.245/1991 depende das características do "
                    "imóvel, da destinação urbana ou comercial e das exclusões de seu art. 1º. A conclusão "
                    "não deve ser extraída somente do endereço rural nem do objeto social da empresa."
                ),
            ),
            section(
                "Elementos para revisar o instrumento",
                (
                    "Matrícula e cadastro rural, descrição da área, atividade licenciada, notas de produção, "
                    "forma de remuneração, divisão de riscos, benfeitorias e prática de pagamento permitem "
                    "confrontar o papel com a realidade. Em uma armazenagem sem cultivo, por exemplo, pode "
                    "haver uso comercial não agrário; em uma agroindústria integrada à exploração da terra, "
                    "o regime agrário pode ser relevante. A orientação jurídica deve identificar esses fatos "
                    "antes de sugerir prazo, retomada ou reajuste."
                ),
            ),
        ],
        faqs=[
            faq(
                "Pagamento em parte da colheita sempre cria parceria rural?",
                (
                    "Não automaticamente. É necessário distinguir equivalência de retribuição certa da "
                    "partilha de riscos, frutos, produtos ou lucros que caracteriza a parceria."
                ),
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l4504compilada.htm#art92",
            "Lei 4.504/1964, art. 92",
            "posse ou uso temporário da terra mediante arrendamento ou parceria em atividade agrária",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l4504compilada.htm#art95",
            "Lei 4.504/1964, art. 95",
            "regras obrigatórias do arrendamento rural, inclusive preço e limites legais",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l4504compilada.htm#art96",
            "Lei 4.504/1964, art. 96",
            "partilha de riscos e de frutos, produtos ou lucros na parceria rural",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/decreto/antigos/d59566.htm#art3",
            "Decreto 59.566/1966, art. 3º",
            "conceito de arrendamento rural e retribuição certa pela exploração agrária",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art1",
            "Lei 8.245/1991, art. 1º",
            "campo de aplicação da locação de imóvel urbano e exclusões",
        ),
    ])


def rewrite_pj_moradia(page):
    apply_text(
        page,
        title="Empresa aluga moradia: quem é o locatário",
        meta=(
            "Quando a empresa aluga imóvel para diretor ou empregado, a locação é não residencial, "
            "a pessoa jurídica permanece locatária e o ocupante não a substitui."
        ),
        h1="A empresa alugou a casa do diretor: qual regime se aplica?",
        opening=(
            "A finalidade física de moradia não torna residencial todo contrato. O art. 55 da Lei "
            "8.245/1991 considera não residencial a locação em que a pessoa jurídica é locatária e "
            "o imóvel se destina a seus titulares, diretores, sócios, gerentes, executivos ou "
            "empregados. Essa classificação não muda quem assinou: a empresa continua sendo parte, "
            "enquanto o morador é ocupante indicado segundo o contrato."
        ),
        sections=[
            section(
                "O art. 55 mantém a pessoa jurídica no contrato",
                (
                    "A empresa responde por aluguel, encargos e demais obrigações assumidas, mesmo que o "
                    "beneficiário direto da moradia seja um executivo. A saída desse ocupante da empresa ou "
                    "sua transferência para outra cidade não extingue automaticamente a locação e não "
                    "converte o novo morador em locatário. O contrato deve ser consultado para decidir entre "
                    "manter, substituir o ocupante ou encerrar o vínculo."
                ),
            ),
            section(
                "Troca de ocupante depende do que foi pactuado",
                (
                    "Se o instrumento autoriza a moradia de empregados ou administradores sem identificar "
                    "uma pessoa exclusiva, uma comunicação documentada pode bastar para atualizar cadastro "
                    "e acesso. Se o imóvel foi entregue para pessoa determinada ou a mudança altera risco, "
                    "uso ou número de moradores, pode ser necessário consentimento ou aditamento. Não existe "
                    "regra geral no art. 4º que substitua automaticamente um executivo por outro."
                ),
            ),
            section(
                "Cessão, sublocação e empréstimo exigem consentimento",
                (
                    "O art. 13 exige consentimento prévio e escrito do locador para cessão da locação, "
                    "sublocação ou empréstimo total ou parcial do imóvel. Nem toda troca interna de empregado "
                    "é sublocação, porque a empresa pode continuar como única locatária e pagadora. Porém, se "
                    "ela transfere a posição contratual, cobra do ocupante ou entrega o imóvel fora da "
                    "finalidade autorizada, o enquadramento precisa ser revisto à luz desse dispositivo."
                ),
            ),
            section(
                "Responsabilidade do morador e garantias",
                (
                    "O diretor não responde pessoalmente só porque reside no local. Sua responsabilidade pode "
                    "decorrer de assinatura como parte, fiador, garantidor ou de dano que ele próprio cause, "
                    "mas não deve ser presumida contra o texto do contrato. Vistoria, identificação dos "
                    "ocupantes, regras condominiais e comunicações devem permanecer organizadas para separar "
                    "obrigações da empresa, do morador e de eventual garantidor."
                ),
            ),
            section(
                "Exemplo de substituição documentada",
                (
                    "Uma companhia aluga apartamento para seus diretores e assina como locatária. Quando o "
                    "primeiro diretor é transferido, ela confere a cláusula de destinação e comunica o locador "
                    "antes de instalar a sucessora. Se o contrato limitava a ocupação à pessoa indicada, as "
                    "partes avaliam aditamento. Uma revisão jurídica pode prevenir infração sem afirmar que "
                    "toda troca exige novo contrato ou que nenhuma depende de anuência."
                ),
            ),
        ],
        faqs=[
            faq(
                "O diretor vira locatário por morar no imóvel?",
                "Não. Se a pessoa jurídica assinou como locatária, ela permanece parte do contrato.",
            ),
            faq(
                "A empresa pode sublocar o imóvel sem avisar?",
                "Não. Cessão, sublocação e empréstimo dependem de consentimento prévio e escrito do locador.",
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art55",
            "Lei 8.245/1991, art. 55",
            "classificação não residencial da locação contratada por pessoa jurídica para moradia de seus integrantes",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art13",
            "Lei 8.245/1991, art. 13",
            "consentimento prévio e escrito para cessão da locação, sublocação ou empréstimo do imóvel",
        ),
    ])


def rewrite_uso_diverso(page):
    apply_text(
        page,
        title="Uso diverso no imóvel comercial: infração e prova",
        meta=(
            "Saiba quando a mudança de atividade viola a destinação da locação comercial, como "
            "documentar o fato e por que a notificação não é requisito universal."
        ),
        h1="Mudar o ramo da loja permite rescindir a locação?",
        opening=(
            "A mudança de atividade pode ser irrelevante, regularizável ou uma infração capaz de "
            "fundamentar o desfazimento da locação. O resultado depende da destinação convencionada "
            "ou presumida, do impacto concreto do novo uso e das demais obrigações legais e "
            "contratuais. A Lei do Inquilinato não fixa uma notificação prévia universal nem um "
            "prazo padrão de quinze dias para todo caso. Notificar costuma ter valor estratégico e "
            "probatório, mas não deve ser apresentada como condição que os arts. 9º e 23 sempre exigem."
        ),
        sections=[
            section(
                "Destinação convencionada ou presumida",
                (
                    "O art. 23, II, obriga o locatário a servir-se do imóvel para o uso convencionado ou "
                    "presumido, compatível com sua natureza e finalidade. Uma cláusula que limita o espaço "
                    "a consultório produz análise diferente de outra que autoriza uso comercial amplo. "
                    "Mesmo cláusula genérica convive com zoneamento, regras condominiais, segurança, licença "
                    "e proibição de uso lesivo ao imóvel ou à vizinhança."
                ),
            ),
            section(
                "Infração pode desfazer o contrato",
                (
                    "O art. 9º, II, permite desfazer a locação em decorrência de infração legal ou contratual. "
                    "Para aplicar essa regra, é necessário demonstrar a obrigação violada e a conduta real, "
                    "não apenas discordar do novo ramo. Gravidade, possibilidade de correção, tolerância "
                    "anterior e redação contratual podem influenciar a controvérsia. O dispositivo não cria "
                    "rescisão automática sem prova nem torna toda mudança comercial ilícita."
                ),
            ),
            section(
                "Notificação é ferramenta de prova, não ritual universal",
                (
                    "Uma notificação pode descrever o uso encontrado, apontar a cláusula, pedir acesso a "
                    "documentos e oferecer prazo razoável para cessação ou regularização. Ela também registra "
                    "ciência e eventual persistência da conduta. Contudo, os arts. 9º, II, e 23, II, não "
                    "estabelecem que toda ação por uso diverso dependa dessa etapa nem escolhem quinze dias "
                    "como prazo legal. Contrato, urgência, risco e natureza da obrigação devem orientar a "
                    "estratégia."
                ),
            ),
            section(
                "Prova precisa mostrar o uso efetivo",
                (
                    "Fotografias lícitas, anúncios públicos, vistorias previstas no contrato, documentos de "
                    "licenciamento e comunicações ajudam a demonstrar a atividade. A coleta deve respeitar "
                    "acesso, privacidade e cadeia documental. Um alvará desatualizado pode indicar problema "
                    "administrativo, mas não prova sozinho tudo o que ocorre no imóvel. Da mesma forma, uma "
                    "alteração cadastral não elimina eventual limite contratual."
                ),
            ),
            section(
                "Mudança compatível pode não ser infração",
                (
                    "Se o contrato autoriza uso comercial sem limitar ramo e a nova atividade é compatível "
                    "com imóvel, condomínio e legislação local, pode faltar a infração necessária ao "
                    "desfazimento. Também pode haver consentimento posterior ou prática reiterada conhecida "
                    "pelo locador, fatos que exigem exame próprio. Isso não significa que qualquer atividade "
                    "seja permitida; significa que a conclusão precisa partir da obrigação realmente "
                    "assumida."
                ),
            ),
            section(
                "O pedido deve corresponder à infração demonstrada",
                (
                    "Se o conflito chega ao Judiciário, a narrativa deve ligar fatos, cláusula ou regra legal "
                    "e consequência pretendida. Pedir despejo com base apenas em suspeita, sem identificar o "
                    "uso incompatível, abre espaço para controvérsia probatória. Também é preciso separar "
                    "infração continuada de dano já consumado e de obrigação que pode ser corrigida. Essa "
                    "delimitação orienta documentos, testemunhas e eventual pedido de indenização, sem "
                    "converter toda irregularidade administrativa em causa automática de rescisão."
                ),
            ),
            section(
                "Exemplo de resposta proporcional",
                (
                    "Um contrato destina uma sala a escritório silencioso, mas o ocupante instala atividade "
                    "com máquinas, circulação intensa e risco não previsto. O locador registra os fatos, "
                    "confere a cláusula e envia notificação com prazo escolhido conforme a possibilidade de "
                    "regularização, sem apresentá-lo como prazo legal fixo. Se a conduta persiste, avalia o "
                    "despejo por infração e eventual dano. Apoio jurídico pode organizar prova e pedido, mas "
                    "não garante a rescisão antes da análise do caso."
                ),
            ),
        ],
        faqs=[
            faq(
                "É obrigatório notificar antes de pedir despejo por uso diverso?",
                (
                    "Os arts. 9º, II, e 23, II, não criam requisito universal de notificação prévia. Ela "
                    "pode ser importante por contrato, para permitir correção ou para produzir prova."
                ),
            ),
            faq(
                "A lei concede sempre quinze dias para regularizar?",
                "Não. Esse prazo não aparece como regra geral nesses dispositivos e não deve ser inventado.",
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art23",
            "Lei 8.245/1991, art. 23, II",
            "dever de usar o imóvel conforme o convencionado ou presumido e de modo compatível com sua natureza",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art9",
            "Lei 8.245/1991, art. 9º, II",
            "desfazimento da locação em decorrência de infração legal ou contratual",
        ),
    ])


def rewrite_verbal(page):
    apply_text(
        page,
        title="Locação comercial verbal e ação renovatória",
        meta=(
            "Entenda por que o art. 51 exige contrato escrito e determinado, como funciona a "
            "denúncia por prazo indeterminado e por que contrato novo não retroage."
        ),
        h1="Contrato verbal permite renovar compulsoriamente o ponto?",
        opening=(
            "Recibos, mensagens e pagamentos podem provar que existe uma locação, mas não transformam "
            "um ajuste verbal em contrato escrito por prazo determinado para a ação renovatória. O "
            "fundamento dessa exigência está no próprio art. 51 da Lei 8.245/1991, e não no art. 108 "
            "do Código Civil. Também é preciso separar a falta de renovatória das regras sobre término "
            "ou denúncia da locação não residencial."
        ),
        sections=[
            section(
                "O art. 51 reúne requisitos cumulativos",
                (
                    "A renovatória exige contrato escrito e com prazo determinado, soma de prazos "
                    "ininterruptos de pelo menos cinco anos e exploração do mesmo ramo por no mínimo três "
                    "anos. A ação deve ser proposta no intervalo legal anterior ao término. A longa ocupação "
                    "verbal pode demonstrar atividade e pagamentos, mas não supre a forma e o prazo "
                    "determinado exigidos pelo inciso I."
                ),
            ),
            section(
                "Recibos provam fatos, não fabricam o requisito",
                (
                    "Comprovantes bancários, conversas e notas podem mostrar valor do aluguel, posse e "
                    "obrigações combinadas. Ainda assim, não criam retroativamente um instrumento escrito "
                    "com termo inicial e final. A controvérsia sobre existência da locação é diferente da "
                    "aptidão documental para a renovação compulsória. Por isso, não se deve atribuir ao "
                    "art. 108 do Código Civil uma regra especial que o art. 51 já contém expressamente."
                ),
            ),
            section(
                "Contrato novo conta para a frente",
                (
                    "As partes podem formalizar um contrato escrito e determinado, mas não devem declarar "
                    "ficticiamente que ele existia no período verbal. O novo instrumento produz seus efeitos "
                    "conforme a data e o prazo reais. Para futura renovatória, será necessário verificar se "
                    "os contratos escritos e ininterruptos atingem o período legal e se os demais requisitos "
                    "continuam presentes."
                ),
            ),
            section(
                "Prazo determinado e indeterminado têm saídas diferentes",
                (
                    "Pelo art. 56, a locação não residencial por prazo determinado termina com o prazo, "
                    "independentemente de aviso. Se o locatário permanece por mais de trinta dias sem oposição, "
                    "presume-se a prorrogação por prazo indeterminado nas condições ajustadas. Já o art. 57 "
                    "permite denunciar a locação não residencial por prazo indeterminado mediante aviso "
                    "escrito, concedendo trinta dias para desocupação."
                ),
            ),
            section(
                "Decisões possíveis antes do conflito",
                (
                    "O comerciante pode negociar prazo escrito suficiente, organizar prova das benfeitorias e "
                    "planejar eventual mudança sem presumir indenização automática pelo ponto. O locador, por "
                    "sua vez, deve identificar se há prazo determinado ou vínculo já indeterminado antes de "
                    "notificar. Uma revisão jurídica pode esclarecer a posição documental e negociar condições, "
                    "mas não pode retroagir o contrato nem garantir renovação compulsória."
                ),
            ),
        ],
        faqs=[
            faq(
                "Recibos substituem contrato escrito na renovatória?",
                (
                    "Não. Eles podem provar pagamentos e ocupação, mas não suprem o contrato escrito e com "
                    "prazo determinado exigido pelo art. 51."
                ),
            ),
            faq(
                "Um contrato assinado agora aproveita todo o período verbal?",
                "Não retroativamente. O novo contrato deve refletir datas reais e contará conforme seu prazo.",
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art51",
            "Lei 8.245/1991, art. 51",
            "requisitos cumulativos do contrato escrito, prazo e ramo para a ação renovatória",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art56",
            "Lei 8.245/1991, art. 56",
            "término da locação não residencial determinada e prorrogação pela permanência sem oposição",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art57",
            "Lei 8.245/1991, art. 57",
            "denúncia escrita da locação não residencial por prazo indeterminado com trinta dias para desocupação",
        ),
    ])


def rewrite_encargos(page):
    apply_text(
        page,
        title="IPCA e encargos no aluguel comercial: limites",
        meta=(
            "Veja como repartir condomínio, tributos e reajuste no aluguel comercial, quais despesas "
            "a lei atribui a cada parte e por que shopping é hipótese específica."
        ),
        h1="O contrato comercial pode repassar todos os encargos ao inquilino?",
        opening=(
            "A liberdade contratual não apaga a distribuição prevista na Lei do Inquilinato. Despesas "
            "ordinárias e extraordinárias de condomínio recebem tratamento diferente; tributos e outros "
            "encargos só podem ser cobrados do locatário quando sua responsabilidade estiver atribuída. "
            "Também não existe obrigação legal de usar IPCA: o índice deve ser pactuado e o reajuste "
            "monetário precisa respeitar a periodicidade mínima anual."
        ),
        sections=[
            section(
                "Despesas extraordinárias cabem ao locador",
                (
                    "O art. 22, X, atribui ao locador as despesas extraordinárias de condomínio, como obras "
                    "estruturais e constituição de fundo de reserva nas situações descritas pela lei. O mesmo "
                    "artigo trata de impostos, taxas e seguro complementar contra fogo, salvo disposição "
                    "expressa em contrário. A leitura da cláusula deve identificar cada rubrica, em vez de "
                    "usar a fórmula vaga de que tudo será pago pelo inquilino."
                ),
            ),
            section(
                "Despesas ordinárias cabem ao locatário",
                (
                    "O art. 23, XII, põe a cargo do locatário as despesas ordinárias de condomínio, ligadas à "
                    "administração e manutenção cotidiana conforme a lista legal. Classificar a cobrança exige "
                    "examinar sua causa, não apenas o nome dado pelo condomínio. Uma obra extraordinária não "
                    "vira despesa ordinária porque foi parcelada no boleto mensal."
                ),
            ),
            section(
                "O art. 25 não cria repasse livre",
                (
                    "O art. 25 permite ao locador cobrar juntamente com o aluguel os tributos, encargos e "
                    "despesas ordinárias de condomínio cuja responsabilidade tenha sido atribuída ao locatário. "
                    "A expressão cuja responsabilidade tenha sido atribuída é o limite da cobrança. Uma cláusula "
                    "expressa pode repartir determinados tributos entre as partes, mas não altera por si só o "
                    "sujeito passivo definido na legislação tributária."
                ),
            ),
            section(
                "Liberdade do art. 54 vale para shopping center",
                (
                    "O art. 54 prestigia as condições livremente pactuadas nas relações entre lojistas e "
                    "empreendedores de shopping center. Essa regra não é uma autorização geral para toda "
                    "locação comercial. Além disso, o § 1º proíbe cobrar do locatário de shopping determinadas "
                    "despesas extraordinárias e obras que alterem projeto ou memorial, ressalvadas as hipóteses "
                    "legais. Fundo de promoção e rateios também precisam estar descritos e demonstráveis."
                ),
            ),
            section(
                "IPCA é opção contratual, não índice obrigatório",
                (
                    "O art. 2º da Lei 10.192/2001 admite correção monetária ou reajuste por índices de preços "
                    "em contratos com duração igual ou superior a um ano e considera nula a periodicidade "
                    "inferior à anual. As partes podem escolher IPCA ou outro indexador juridicamente admitido, "
                    "definindo data-base e fórmula. Reajuste periódico não se confunde com revisão do valor de "
                    "mercado nem autoriza duplicar índices no mesmo período."
                ),
            ),
            section(
                "Conferência prática da cobrança",
                (
                    "Contrato, convenção e boletos do condomínio, atas de obra, carnês tributários e memória de "
                    "reajuste permitem separar obrigação legal, atribuição contratual e cálculo. Antes de deixar "
                    "de pagar, o locatário deve identificar a rubrica controvertida e preservar a parcela "
                    "incontroversa conforme orientação do caso. A assistência jurídica pode revisar a cobrança "
                    "ou negociar cláusulas, sem prometer que toda transferência será nula."
                ),
            ),
        ],
        faqs=[
            faq(
                "Toda despesa extraordinária pode ser transferida em contrato comercial?",
                (
                    "Não se deve presumir isso. O art. 22, X, atribui essas despesas ao locador, e o art. 54, "
                    "§ 1º, ainda impõe limites específicos nas locações de shopping."
                ),
            ),
            faq(
                "O reajuste comercial precisa usar IPCA?",
                "Não. O índice é pactuado; a correção monetária deve respeitar periodicidade mínima anual.",
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art22",
            "Lei 8.245/1991, art. 22",
            "obrigações do locador, inclusive despesas extraordinárias de condomínio",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art23",
            "Lei 8.245/1991, art. 23",
            "obrigações do locatário, inclusive despesas ordinárias de condomínio",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art25",
            "Lei 8.245/1991, art. 25",
            "cobrança de tributos, encargos e despesas ordinárias quando atribuídos ao locatário",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art54",
            "Lei 8.245/1991, art. 54 e § 1º",
            "pactuação e limites específicos nas relações entre lojistas e empreendedores de shopping center",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10192.htm#art2",
            "Lei 10.192/2001, art. 2º",
            "admissibilidade de indexador pactuado e periodicidade mínima anual da correção monetária",
        ),
    ])


def rewrite_hotel(page):
    apply_text(
        page,
        title="Locação de imóvel para hotel: retomada e fundo",
        meta=(
            "Diferencie hospedagem excluída da Lei do Inquilinato e locação a operador de hotel, "
            "e entenda a regra geral do mesmo ramo no art. 52, § 1º."
        ),
        h1="Imóvel operado como hotel tem proteção especial contra retomada?",
        opening=(
            "A Lei do Inquilinato não cria uma blindagem exclusiva para hotéis, pousadas ou hostels. "
            "Primeiro é preciso identificar qual contrato existe. A hospedagem prestada ao usuário em "
            "apart-hotel, hotel-residência ou equiparado pode estar excluída da lei; já a cessão de um "
            "imóvel a uma empresa que nele opera hospedagem pode formar locação não residencial. Depois "
            "dessa classificação, aplicam-se os requisitos da renovatória e as regras gerais de retomada."
        ),
        sections=[
            section(
                "Hospedagem do usuário e locação ao operador não são iguais",
                (
                    "O art. 1º, parágrafo único, item 4, exclui as locações em apart-hotéis, hotéis-residência "
                    "ou equiparados que prestem serviços regulares a seus usuários e sejam autorizados a "
                    "funcionar como tais. Essa relação de hospedagem não deve ser confundida automaticamente "
                    "com o contrato pelo qual o proprietário entrega o imóvel inteiro a uma empresa para "
                    "explorar hotel ou pousada. Neste segundo caso, o conteúdo pode revelar locação comercial."
                ),
            ),
            section(
                "Renovatória continua sujeita ao art. 51",
                (
                    "Se houver locação não residencial, o operador só pode buscar renovação compulsória ao "
                    "comprovar contrato escrito e determinado, soma mínima de cinco anos, mesmo ramo por pelo "
                    "menos três anos e ajuizamento no período legal. Investimentos, reputação e tempo de "
                    "funcionamento não dispensam esses requisitos. Também é necessário distinguir bens do "
                    "imóvel daqueles pertencentes ao estabelecimento empresarial."
                ),
            ),
            section(
                "A regra do mesmo ramo é geral",
                (
                    "O art. 52, II, admite oposição à renovação para uso próprio ou transferência de fundo de "
                    "comércio nas condições legais. O § 1º estabelece que, nessa hipótese, o imóvel não pode "
                    "ser destinado ao uso do mesmo ramo do locatário. Essa proteção vale para atividades em "
                    "geral, não apenas hotelaria. A exceção ocorre quando a própria locação também envolvia o "
                    "fundo de comércio, com instalações e pertences."
                ),
            ),
            section(
                "Não existe imunidade a toda retomada",
                (
                    "O locador pode apresentar outros fundamentos previstos no art. 52, e a renovatória pode "
                    "falhar por ausência de requisitos ou prova. Também será necessário verificar se a alegação "
                    "de uso próprio corresponde ao uso efetivo e ao ramo informado. A mera intenção de abrir "
                    "hotel não decide o caso sem examinar quem detinha o fundo, quais instalações integravam o "
                    "contrato e qual hipótese legal foi invocada."
                ),
            ),
            section(
                "Exemplo com dois contratos distintos",
                (
                    "Uma empresa aluga por dez anos um prédio vazio, instala seus móveis e opera uma pousada. "
                    "Esse vínculo com o proprietário pode ser locação não residencial. Os contratos diários "
                    "com hóspedes, porém, são relações de hospedagem e não se confundem com a locação principal. "
                    "Se o proprietário se opõe à renovação para explorar o mesmo ramo, o art. 52, § 1º, exige "
                    "análise do fundo e das instalações. Orientação jurídica pode organizar essa prova sem "
                    "prometer renovação ou impedir toda retomada."
                ),
            ),
        ],
        faqs=[
            faq(
                "O art. 52, § 1º, protege somente hotéis e pousadas?",
                "Não. A restrição ao mesmo ramo é regra geral, com a exceção legal ligada ao fundo de comércio.",
            ),
            faq(
                "Hospedagem em apart-hotel é igual à locação do prédio ao operador?",
                "Não necessariamente. São relações distintas e devem ser classificadas pelo conteúdo real.",
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art1",
            "Lei 8.245/1991, art. 1º, parágrafo único, item 4",
            "exclusão das relações em apart-hotéis, hotéis-residência ou equiparados que prestem serviços regulares",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art51",
            "Lei 8.245/1991, art. 51",
            "requisitos gerais da ação renovatória de locação não residencial",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art52",
            "Lei 8.245/1991, art. 52 e § 1º",
            "oposição à renovação, vedação geral de destinação ao mesmo ramo e exceção relativa ao fundo de comércio",
        ),
    ])


def rewrite_faturamento(page):
    apply_text(
        page,
        title="Queda de faturamento e revisão do aluguel comercial",
        meta=(
            "Saiba como negociar o aluguel, quando cabe revisional após três anos e por que os arts. "
            "317 e 478 não transformam toda queda de receita em redução judicial."
        ),
        h1="Faturamento caiu: há direito a reduzir o aluguel da loja?",
        opening=(
            "A queda de receita é um sinal para reorganizar o contrato, mas não cria desconto judicial "
            "automático. A Lei 8.245/1991 permite que as partes alterem o aluguel por acordo e prevê ação "
            "revisional depois de três anos. O Código Civil contém mecanismos excepcionais para fatos "
            "imprevisíveis ou extraordinários. Cada caminho exige pressupostos e provas diferentes. "
            "Misturá-los pode levar o empresário a interromper pagamentos sem base e agravar o risco de "
            "despejo."
        ),
        sections=[
            section(
                "Acordo pode ser feito a qualquer tempo",
                (
                    "O art. 18 da Lei do Inquilinato permite que locador e locatário fixem novo valor por "
                    "acordo, bem como insiram ou modifiquem cláusula de reajuste. Desconto temporário, "
                    "diferimento e mudança de índice devem indicar período, valor, vencimento, tratamento das "
                    "diferenças e retorno às condições anteriores. Fluxo de caixa, histórico de pagamento e "
                    "vacância comparável ajudam a construir uma proposta, mas o locador não é obrigado a "
                    "aceitá-la."
                ),
            ),
            section(
                "Revisional legal exige intervalo de três anos",
                (
                    "Pelo art. 19, após três anos de vigência do contrato ou do acordo anteriormente realizado, "
                    "locador ou locatário pode pedir revisão judicial para ajustar o aluguel ao preço de mercado. "
                    "Essa ação compara valor locativo, imóvel, localização, época e condições negociais; a mera "
                    "queda do faturamento da empresa não prova que o aluguel está fora do mercado. O marco de "
                    "três anos deve ser contado a partir do contrato ou do último acordo relevante."
                ),
            ),
            section(
                "O art. 68 organiza o procedimento",
                (
                    "A ação revisional segue o procedimento do art. 68, que trata da petição, do valor pretendido, "
                    "do aluguel provisório e da audiência. Não se deve prometer liminar com o percentual pedido "
                    "pelo locatário. Laudo ou parecer de mercado, contratos comparáveis e características do "
                    "imóvel precisam sustentar o valor, e a parte contrária pode impugnar metodologia e amostra."
                ),
            ),
            section(
                "Art. 317 depende de fato imprevisível e desproporção",
                (
                    "O art. 317 do Código Civil permite correção judicial da prestação quando motivos "
                    "imprevisíveis produzirem desproporção manifesta entre o valor devido e o momento de sua "
                    "execução. Oscilação comum do negócio, concorrência, erro de gestão ou redução isolada das "
                    "vendas não satisfazem automaticamente essa regra. É preciso ligar o evento à prestação e "
                    "demonstrar a desproporção, preservando, quando possível, o valor real da prestação."
                ),
            ),
            section(
                "Art. 478 é remédio excepcional de resolução",
                (
                    "Nos contratos de execução continuada ou diferida, o art. 478 exige acontecimento "
                    "extraordinário e imprevisível que torne a prestação excessivamente onerosa, com extrema "
                    "vantagem para a outra parte. O dispositivo trata de resolução, não de desconto obrigatório "
                    "em qualquer crise. A distribuição contratual de riscos e a natureza do evento precisam ser "
                    "analisadas; dificuldade financeira empresarial, por si só, não basta."
                ),
            ),
            section(
                "Não interrompa o pagamento sem estratégia formal",
                (
                    "Enquanto não houver acordo ou decisão, o aluguel contratado continua exigível. O empresário "
                    "deve separar valores incontroversos, encargos, garantias e risco de despejo, além de registrar "
                    "as propostas trocadas. Se o negócio não puder permanecer, rescisão e entrega do imóvel também "
                    "devem ser negociadas com vistoria e cálculo da multa, em vez de simplesmente abandonar o "
                    "ponto."
                ),
            ),
            section(
                "Exemplo que separa mercado e evento excepcional",
                (
                    "Uma loja paga valor muito superior ao de imóveis equivalentes três anos após o último acordo. "
                    "Ela pode reunir comparáveis para a revisional dos arts. 19 e 68, mesmo sem evento extraordinário. "
                    "Se, além disso, uma intervenção pública imprevisível bloqueia o acesso por longo período, os "
                    "arts. 317 ou 478 podem ser avaliados com prova específica, sem resultado presumido. Apoio jurídico "
                    "pode comparar as vias e negociar, mas não garante redução baseada apenas no percentual de queda "
                    "do caixa."
                ),
            ),
        ],
        faqs=[
            faq(
                "Qualquer queda de faturamento permite revisar o aluguel?",
                (
                    "Não. A revisional legal exige o intervalo de três anos e prova do valor de mercado; os "
                    "remédios do Código Civil dependem de pressupostos excepcionais próprios."
                ),
            ),
            faq(
                "É possível negociar antes dos três anos?",
                "Sim. O art. 18 permite acordo sobre novo aluguel e cláusula de reajuste a qualquer tempo.",
            ),
        ],
    )
    set_sources(page, [
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art18",
            "Lei 8.245/1991, art. 18",
            "acordo para novo valor de aluguel e inserção ou modificação da cláusula de reajuste",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art19",
            "Lei 8.245/1991, art. 19",
            "revisão judicial do aluguel após três anos de contrato ou do acordo anterior",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art68",
            "Lei 8.245/1991, art. 68",
            "procedimento da ação revisional de aluguel",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art317",
            "Código Civil, art. 317",
            "correção judicial por motivos imprevisíveis e desproporção manifesta da prestação",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art478",
            "Código Civil, art. 478",
            "resolução por onerosidade excessiva em contrato continuado ou diferido diante de acontecimento extraordinário e imprevisível",
        ),
    ])


REWRITERS = {
    "imob-morte-empresario-ponto": rewrite_morte,
    "imob-desapropriacao-imovel-alugado": rewrite_desapropriacao,
    "imob-preferencia-lojista-venda": rewrite_preferencia,
    "imob-garantias-locacao-comercial": rewrite_garantias,
    "imob-locacao-quiosque-feira": rewrite_quiosque,
    "imob-coworking-natureza-juridica": rewrite_coworking,
    "imob-arrendamento-rural-vs-locacao": rewrite_rural,
    "imob-locacao-pj-moradia-socio": rewrite_pj_moradia,
    "imob-uso-diverso-ponto": rewrite_uso_diverso,
    "imob-renovatoria-contrato-verbal": rewrite_verbal,
    "imob-ipca-encargos-livres-comercial": rewrite_encargos,
    "imob-hotel-pousada-retomada": rewrite_hotel,
    "imob-queda-faturamento-renegociar": rewrite_faturamento,
}


WORD_BANDS = {
    "imob-desapropriacao-imovel-alugado": (630, 1540),
    "imob-preferencia-lojista-venda": (630, 1540),
    "imob-uso-diverso-ponto": (630, 1540),
    "imob-queda-faturamento-renegociar": (630, 1540),
    "imob-coworking-natureza-juridica": (315, 770),
}


def validate(pages):
    ids = [page.get("intent_id") for page in pages]
    if ids != list(REWRITERS):
        raise RuntimeError(f"ordem ou intents inesperados: {ids}")
    if len(ids) != len(set(ids)):
        raise RuntimeError("intent duplicado")
    for page in pages:
        intent = page["intent_id"]
        if page.get("lane") not in {"comercial", "informativa"}:
            raise RuntimeError(f"lane inválida: {intent}")
        if not 20 <= len(page["title"]) <= 65:
            raise RuntimeError(f"title fora da faixa: {intent}")
        if not 70 <= len(page["meta_description"]) <= 160:
            raise RuntimeError(f"meta fora da faixa: {intent}")
        if len(page.get("sections", [])) < 4:
            raise RuntimeError(f"seções insuficientes: {intent}")
        sources = page.get("official_sources", [])
        if not 2 <= len(sources) <= 5:
            raise RuntimeError(f"fontes fora da faixa: {intent}={len(sources)}")
        if len({source["url"] for source in sources}) != len(sources):
            raise RuntimeError(f"fonte duplicada: {intent}")
        for source in sources:
            if not source["url"].startswith("https://"):
                raise RuntimeError(f"fonte sem HTTPS: {intent}")
        count = body_word_count(page)
        lo, hi = WORD_BANDS.get(intent, (360, 880))
        if not lo <= count <= hi:
            raise RuntimeError(f"word_count fora da faixa: {intent}={count} ({lo}-{hi})")
        page["word_count"] = count

    visible = " ".join(
        [page["opening"] for page in pages] +
        [part["text"] for page in pages for part in page["sections"]] +
        [item["a"] for page in pages for item in page["faq"]]
    ).lower()
    forbidden = (
        "garantias seguem valendo",
        "constituí-lo em usufruto",
        "renúncia expressa a esse direito",
        "ele não pode trocá-la unilateralmente",
        "o coworking não é, tecnicamente, um contrato de locação",
        "vedado o pagamento em percentual da colheita",
        "sem necessidade de novo contrato",
        "exige regularização em quinze dias",
        "art. 108 do código civil (lei 10.406/2002)",
        "essa liberdade de repasse existe",
        "proteção específica contra determinadas formas de retomada",
    )
    stale = [phrase for phrase in forbidden if phrase in visible]
    if stale:
        raise RuntimeError(f"afirmações obsoletas persistem: {stale}")


def main():
    original = TARGET.read_bytes()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha not in EXPECTED_SHA256:
        raise SystemExit(
            f"CAS falhou: esperado um de {sorted(EXPECTED_SHA256)}, encontrado {actual_sha}"
        )
    pages = [
        json.loads(line)
        for line in original.decode("utf-8").splitlines()
        if line.strip()
    ]
    for page in pages:
        REWRITERS[page["intent_id"]](page)
    validate(pages)
    encoded = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")

    fd, temporary = tempfile.mkstemp(
        prefix=".imobiliario-07-current-law.", suffix=".tmp", dir=TARGET.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(TARGET.read_bytes()).hexdigest() != actual_sha:
            raise RuntimeError("CAS mudou antes da troca atômica")
        os.replace(temporary, TARGET)
        directory_fd = os.open(TARGET.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(hashlib.sha256(encoded).hexdigest())
    for page in pages:
        metadata = sum(
            1 for source in page["official_sources"]
            if "verified_at" in source and "http_status" in source
        )
        print(
            page["intent_id"], page["word_count"],
            len(page["official_sources"]), metadata,
        )


if __name__ == "__main__":
    main()
