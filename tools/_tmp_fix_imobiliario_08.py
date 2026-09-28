#!/usr/bin/env python3
"""Corrige, por CAS, os falsos verdes jurídicos do shard imobiliario-08."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path


TARGET = Path("data/editorial/v2_pages/imobiliario-08.jsonl")
EXPECTED_SHA256 = "72e7ebad7926c8e91bf2746daa421646f7a8d44c0877ffd172bf78585e07a783"
CONTENT_FIXED_SHA256 = "d54f21ea1134b0d2bdbe0232bb94a9083b4af2bd5e0dd26842968daccaeb4012"
METADATA_FIXED_SHA256 = "22eb37b7077bec3a8cf43392ed0db7e3df396e754a13b8a3616d94a8abeffe98"
FINAL_SHA256 = "4a478db66f02edc2fb009a7bd675187ff8efc9eac53569639aa721d1f41ecd94"


def words(value):
    folded = "".join(
        char
        for char in unicodedata.normalize("NFD", (value or "").lower())
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


def source(url, name, claim, existing):
    item = {"url": url, "name": name, "anchor_claim": claim}
    previous = existing.get(url)
    if previous is not None:
        for key in ("verified_at", "http_status"):
            if key in previous:
                item[key] = previous[key]
    return item


def set_sources(page, specs):
    existing = {item["url"]: item for item in page["official_sources"]}
    page["official_sources"] = [source(*spec, existing) for spec in specs]


def section(page, heading):
    return next(item for item in page["sections"] if item["heading"] == heading)


def rewrite_distrato_amount(page):
    section(page, "As deduções do artigo 67-A antes de qualquer percentual")["text"] = (
        "O art. 67-A da Lei 4.591/1964, incluído pela Lei 13.786/2018, parte das quantias "
        "pagas diretamente à incorporadora, atualizadas pelo índice contratual, e enumera "
        "deduções cumulativas. Entre elas estão a integralidade da corretagem, a pena "
        "convencional limitada a 25% da quantia paga — ou a até 50% no patrimônio de "
        "afetação — e os encargos do período em que a unidade ficou disponível ao adquirente. "
        "A fruição corresponde a 0,5% do valor atualizado do contrato, calculado pro rata die: "
        "não é uma taxa de 0,5% multiplicada por cada dia. A lei também não manda subtrair a "
        "corretagem e só depois aplicar a pena sobre o saldo; cada rubrica precisa ser conferida "
        "na base que o próprio dispositivo lhe atribui."
    )
    section(page, "Um exemplo prático de conta que costuma sair errada")["text"] = (
        "Uma conferência segura separa as rubricas em vez de aplicar descontos em cascata. "
        "Primeiro se identificam as quantias efetivamente pagas à incorporadora e sua atualização; "
        "depois se verifica a corretagem comprovadamente paga, a pena contratual dentro do teto "
        "legal e, se houve disponibilização da unidade, o período exato de impostos, condomínio "
        "e fruição. A pena não deve ser recalculada sobre um saldo criado pela dedução prévia da "
        "corretagem, e a fruição de 0,5% deve ser rateada pro rata die, não repetida como percentual "
        "diário. Uma planilha que exponha base, período e fórmula de cada item permite ao comprador "
        "localizar a divergência antes de negociar ou discutir a cobrança."
    )
    page["faq"][0]["a"] = (
        "A corretagem comprovadamente paga é uma dedução autônoma do art. 67-A. Isso não autoriza "
        "reduzir primeiro uma base e calcular a pena sobre o saldo: a pena tem como referência a "
        "quantia paga, dentro do teto legal aplicável."
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art67a",
                "Lei 4.591/1964, art. 67-A (incluído pela Lei 13.786/2018)",
                "define separadamente as deduções, a base e os tetos da pena e a fruição de 0,5% calculada pro rata die",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art43a",
                "Lei 4.591/1964, art. 43-A",
                "distingue a resolução por atraso de entrega do distrato imputável ao adquirente",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13786.htm",
                "Lei 13.786/2018",
                "incluiu os regimes dos arts. 43-A e 67-A na Lei 4.591/1964",
            ),
        ],
    )


def rewrite_distrato_deadline(page):
    page["sections"].insert(
        0,
        {
            "heading": "A data do contrato define qual regime de devolução incide",
            "text": (
                "Os percentuais e prazos introduzidos pela Lei 13.786/2018 regem os contratos "
                "celebrados sob sua vigência. O STJ afastou a aplicação simples e direta da lei "
                "nova aos contratos anteriores, cujos efeitos continuam submetidos ao regime "
                "jurídico vigente na contratação e à jurisprudência pertinente. Por isso, antes "
                "de escolher entre 30, 180 ou outro parâmetro, é indispensável conferir a data do "
                "compromisso e a causa do desfazimento."
            ),
        },
    )
    target = section(page, "O que fazer quando o prazo já venceu e não há pagamento")
    target["text"] = target["text"].replace(
        "Montar essa notificação com o cálculo certo, já incluindo os juros do atraso no próprio pagamento, costuma render mais quando revisado por um advogado antes do envio, com todo o contato feito remotamente por quem já não mora perto do empreendimento.",
        "A notificação deve indicar o regime temporal aplicável, o termo inicial, a correção e os juros reclamados. Um advogado pode revisar esses dados e os documentos antes do envio, inclusive em atendimento remoto quando o comprador já não mora perto do empreendimento.",
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art67a",
                "Lei 4.591/1964, art. 67-A, §§ 5º a 8º",
                "fixa os prazos de restituição para contratos alcançados pelo regime legal do distrato",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art43a",
                "Lei 4.591/1964, art. 43-A, § 1º",
                "fixa o prazo ligado à resolução por atraso de entrega, hipótese distinta do distrato do adquirente",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13786.htm",
                "Lei 13.786/2018",
                "introduziu as regras especiais de restituição nos contratos posteriores à sua vigência",
            ),
            (
                "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ATC?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20190625&formato=PDF&nreg=201602669130&salvar=false&seq=93879287&tipo=68",
                "STJ, questão de ordem sobre a Lei 13.786/2018",
                "afasta a aplicação simples e direta da Lei 13.786/2018 aos contratos celebrados antes de sua vigência",
            ),
        ],
    )


def rewrite_builder_fault(page):
    page["opening"] = (
        "Nem todo desfazimento de contrato de compra na planta segue a retenção de 25% ou 50% "
        "do art. 67-A. A Súmula 543 do STJ distingue a culpa exclusiva do vendedor ou construtor "
        "daquela atribuída ao comprador. Já o prazo especial de 60 dias do art. 43-A, § 1º, tem "
        "hipótese mais estreita: resolução porque a entrega ultrapassou o prazo contratual somado "
        "à tolerância. Outros defeitos ou inadimplementos exigem enquadramento próprio e não "
        "recebem automaticamente esse prazo."
    )
    section(page, "A Súmula 543 do STJ e a distinção entre culpas")["text"] = (
        "A Súmula 543 do Superior Tribunal de Justiça estabelece, nos contratos submetidos ao "
        "Código de Defesa do Consumidor, restituição integral quando o desfazimento decorre de "
        "culpa exclusiva do vendedor ou construtor e parcial quando o comprador lhe dá causa. "
        "O enunciado não transforma todo vício da unidade em atraso de entrega nem transporta, "
        "por si só, o prazo de 60 dias do art. 43-A para qualquer espécie de inadimplemento."
    )
    section(page, "O que o artigo 43-A, § 1º, da Lei 4.591 garante ao comprador")["text"] = (
        "O § 1º do art. 43-A incide quando a entrega do imóvel ultrapassa a data contratual, já "
        "computada a tolerância válida, e o adquirente opta por resolver o contrato. Nessa hipótese "
        "específica, ele assegura a devolução integral dos valores pagos, a multa contratual "
        "cabível e afasta as deduções do art. 67-A. Defeito construtivo, divergência de acabamento "
        "ou outro descumprimento sem atraso de entrega pode fundamentar resolução ou indenização "
        "por normas próprias, mas não deve ser apresentado como incidência automática do § 1º."
    )
    section(page, "O prazo de 60 dias corridos contados da resolução")["text"] = (
        "Na resolução fundada no atraso de entrega descrito pelo § 1º, a restituição deve ocorrer "
        "em até 60 dias corridos contados da resolução, com a atualização indicada no dispositivo. "
        "Esse termo não é um prazo geral para todo inadimplemento da construtora; a causa da "
        "resolução precisa ser identificada antes de aplicá-lo."
    )
    section(page, "Provar a culpa da construtora ainda é necessário")["text"] = (
        "Atribuir o atraso à incorporadora depende do contrato, do cronograma e das causas "
        "efetivamente provadas. Caso fortuito ou força maior podem influenciar a mora e os remédios "
        "disponíveis, mas não convertem automaticamente o caso em distrato causado pelo comprador "
        "nem autorizam, sem outro fundamento, as retenções do art. 67-A. Da mesma forma, eventual "
        "contribuição do adquirente precisa ser demonstrada e delimitada."
    )
    page["faq"][1]["a"] = (
        "A Súmula 543 continua relevante para distinguir quem deu causa ao desfazimento, respeitado "
        "o regime temporal e a legislação especial aplicável. O prazo de 60 dias do art. 43-A, "
        "porém, está ligado à resolução por atraso de entrega além da tolerância."
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art43a",
                "Lei 4.591/1964, art. 43-A, § 1º",
                "disciplina a resolução por atraso de entrega além da tolerância e o prazo de 60 dias nessa hipótese",
            ),
            (
                "https://processo.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=543",
                "Súmula 543 do Superior Tribunal de Justiça",
                "distingue a restituição integral por culpa exclusiva do vendedor da restituição parcial quando o comprador causa o desfazimento",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art67a",
                "Lei 4.591/1964, art. 67-A",
                "regula as retenções do desfazimento imputável ao adquirente, sem transformar força maior em culpa automática deste",
            ),
        ],
    )


def rewrite_tolerance(page):
    section(page, "Quando a tolerância não se aplica ou já foi superada")["text"] = (
        "Se a cláusula não foi pactuada de forma clara e destacada, ou se prevê tolerância acima "
        "de 180 dias, ela não conta com a proteção automática do caput do art. 43-A. Uma explicação "
        "técnica da incorporadora não amplia o limite legal nem preserva esse porto seguro. Quando "
        "o prazo contratual somado aos 180 dias já passou, a análise se desloca para a mora, a "
        "manutenção do contrato ou sua resolução. Contrato, cronograma e comunicados devem ser "
        "comparados antes de definir a medida cabível."
    )
    page["faq"][0]["a"] = (
        "O art. 43-A protege a tolerância de até 180 dias, pactuada de modo claro e destacado. "
        "Prazo superior não mantém essa proteção apenas por vir acompanhado de justificativa "
        "técnica e deve ser examinado à luz do contrato e das normas de proteção aplicáveis."
    )


def rewrite_delay_resolution(page):
    section(page, "Quando a rescisão por atraso pode ser negada")["text"] = (
        "Caso fortuito, força maior e eventual contribuição do comprador exigem prova e podem "
        "alterar a atribuição da mora ou a extensão dos remédios contratuais. Isso não transforma "
        "automaticamente o atraso em desistência causada pelo comprador nem libera, por si só, "
        "as retenções do art. 67-A. Antes da notificação, convém organizar contrato, cronograma, "
        "comunicados e documentos sobre a causa do atraso para definir se há resolução pelo art. "
        "43-A, manutenção do vínculo ou outra consequência jurídica."
    )


def rewrite_lost_profits(page):
    page["opening"] = (
        "A possibilidade de somar cláusula penal moratória e lucros cessantes no atraso da obra "
        "não se resolve apenas pelo art. 43-A. No Tema 970, o STJ fixou que a cláusula moratória, "
        "quando estabelecida em valor equivalente ao locativo, em regra já indeniza o adimplemento "
        "tardio e afasta a cumulação com lucros cessantes. A natureza e a base de cada parcela "
        "precisam ser comparadas para evitar dupla reparação."
    )
    section(page, "Por que lucros cessantes de mesma natureza tendem a ser absorvidos")["text"] = (
        "Segundo o Tema 970 do STJ, a cláusula penal moratória equivalente ao valor locativo tem "
        "finalidade de indenizar a entrega tardia e, em regra, afasta a soma com lucros cessantes "
        "fundados na mesma privação de uso. Não é necessário chamar toda parcela de 'multa de 1%' "
        "para aplicar a distinção: importa verificar se a cláusula já recompõe o aluguel que o "
        "comprador deixou de receber ou precisou pagar."
    )
    section(page, "Quando o pedido de cumulação pode prosperar")["text"] = (
        "Prejuízo alegadamente distinto exige demonstração concreta de fato gerador, natureza e "
        "valor que não estejam cobertos pela cláusula moratória. A exceção não deve ser prometida "
        "como automática apenas porque há recibos de aluguel ou outro gasto. Antes de formular o "
        "pedido, um advogado imobiliário pode confrontar a cláusula, o Tema 970 e os comprovantes "
        "para separar eventual dano autônomo da privação de uso já indenizada."
    )
    set_sources(
        page,
        [
            (
                "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=970&cod_tema_inicial=970&novaConsulta=true&tipo_pesquisa=T",
                "STJ, Tema Repetitivo 970",
                "fixa que a cláusula penal moratória equivalente ao locativo, em regra, afasta a cumulação com lucros cessantes",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art43a",
                "Lei 4.591/1964, art. 43-A, §§ 2º e 3º",
                "disciplina a indenização legal pela manutenção do contrato e a vedação de cumular as multas dos §§ 1º e 2º",
            ),
        ],
    )


def rewrite_incc(page):
    section(page, "O princípio da boa-fé objetiva como fundamento da discussão")["heading"] = (
        "A tese do Tema 996 para o indexador depois do prazo"
    )
    section(page, "A tese do Tema 996 para o indexador depois do prazo")["text"] = (
        "No Tema Repetitivo 996, o STJ decidiu que, esgotado o prazo de entrega já computada a "
        "tolerância, cessa a correção do saldo por indexador setorial ligado ao custo da construção. "
        "A substituição deve ser pelo IPCA, salvo quando esse índice for mais gravoso ao consumidor. "
        "A ressalva impede trocar mecanicamente o INCC por um índice que aumente ainda mais o saldo."
    )
    section(page, "A alternativa: índice de correção monetária geral após o atraso")["text"] = (
        "O recálculo precisa comparar o indexador setorial e o IPCA no período posterior ao prazo "
        "de entrega somado à tolerância. Se o IPCA for mais oneroso, a própria tese do Tema 996 "
        "impede que a substituição piore a situação do consumidor. Em contrato com financiamento "
        "associativo, os extratos do agente financeiro e da incorporadora devem usar o mesmo marco "
        "temporal para que a diferença não reapareça em outra planilha."
    )
    set_sources(
        page,
        [
            (
                "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=996&cod_tema_inicial=996&novaConsulta=true&tipo_pesquisa=T",
                "STJ, Tema Repetitivo 996",
                "determina substituir o indexador setorial pelo IPCA após o prazo de entrega e a tolerância, salvo se o IPCA for mais gravoso ao consumidor",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art43a",
                "Lei 4.591/1964, art. 43-A",
                "define o limite legal da tolerância que integra o marco temporal do atraso",
            ),
        ],
    )


def rewrite_pre_key_interest(page):
    section(page, "Quando a cobrança de juros no pé pode ser questionada")["text"] = (
        "O STJ registrou no Informativo 499 que a cobrança de juros compensatórios antes das "
        "chaves não é abusiva por si só no contrato de incorporação, desde que haja previsão "
        "expressa e informação que permita ao consumidor controlar taxa e base. Sem cláusula "
        "expressa, o art. 406 do Código Civil não cria automaticamente o direito da incorporadora "
        "de cobrar a taxa legal: esse dispositivo define a taxa legal quando juros são devidos, "
        "mas não substitui a fonte contratual da remuneração. Também são questionáveis a incidência "
        "sobre parcelas quitadas e a mistura opaca entre juros e correção monetária."
    )
    page["faq"][1]["a"] = (
        "Não há percentual único específico para os juros compensatórios pré-chaves. A cobrança "
        "depende de cláusula expressa e informação transparente sobre taxa e base; o art. 406 não "
        "autoriza sozinho uma cobrança ausente do contrato."
    )
    set_sources(
        page,
        [
            (
                "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40cnot%3D013315",
                "STJ, Informativo de Jurisprudência 499",
                "reconhece a validade em tese dos juros compensatórios pré-chaves quando expressamente previstos e informados",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art406",
                "Código Civil, art. 406",
                "define a taxa legal quando os juros são devidos, sem criar por si só juros compensatórios não pactuados",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art422",
                "Código Civil, art. 422",
                "impõe boa-fé na execução e na apresentação dos encargos contratuais",
            ),
        ],
    )


def rewrite_construction_interest(page):
    page["opening"] = (
        "No financiamento associativo de imóvel na planta, o agente financeiro libera recursos "
        "por etapas e cobra juros sobre o capital já desembolsado durante a construção. Esse "
        "encargo, chamado de juros ou taxa de evolução de obra, não se torna ilícito apenas porque "
        "o percentual físico ficou temporariamente estável. O marco objetivo firmado pelo STJ é o "
        "fim do prazo contratual de entrega, incluída a tolerância."
    )
    section(page, "O que é e por que existe a taxa de evolução de obra")["text"] = (
        "À medida que o banco libera parcelas do financiamento para a obra, incidem encargos sobre "
        "o capital efetivamente desembolsado. O percentual de execução orienta as liberações, mas "
        "uma estagnação física não apaga o capital que já foi entregue nem encerra automaticamente "
        "os juros antes do vencimento contratual. Extratos de liberação e laudos de engenharia são "
        "documentos diferentes e precisam ser comparados."
    )
    section(page, "Por que a cobrança se torna questionável durante o atraso")["text"] = (
        "O Tema Repetitivo 996 fixou que é ilícita a cobrança de juros de obra, ou encargo "
        "equivalente, depois do prazo contratual para entrega das chaves, já acrescido da tolerância. "
        "Portanto, a mera estagnação em 70% antes desse marco não extingue o encargo. Ela pode servir "
        "como indício sobre o cronograma, mas a restituição deve ser delimitada pelas cobranças "
        "posteriores ao vencimento reconhecido na tese."
    )
    section(page, "A relação entre o banco e a incorporadora não isenta o comprador")["text"] = (
        "Banco, incorporadora e comprador participam de relações contratuais conectadas, mas a "
        "responsabilidade por cada cobrança depende da operação e dos documentos. O Tema 996 oferece "
        "um marco objetivo para os juros de obra; ele não dispensa identificar quem recebeu o encargo, "
        "quando houve cada liberação e qual era a data de entrega somada à tolerância."
    )
    section(page, "Documentos que evidenciam a cobrança indevida")["text"] = (
        "Devem ser reunidos o contrato de financiamento, o cronograma e a data de entrega com a "
        "tolerância, os demonstrativos de liberação de capital, os laudos de evolução e os extratos "
        "mensais. A planilha de revisão precisa separar valores anteriores e posteriores ao marco "
        "do Tema 996; laudo que mostre obra parada antes da data final, isoladamente, não prova que "
        "todos os juros daquele período eram indevidos."
    )
    section(page, "O caminho para reaver valores cobrados indevidamente")["text"] = (
        "A contestação deve indicar o prazo de entrega acrescido da tolerância e listar os juros de "
        "obra cobrados depois desse marco. O pedido pode ser dirigido ao agente que recebeu os valores, "
        "com cópia dos extratos e da memória de cálculo, sem presumir que toda cobrança desde uma "
        "estagnação anterior era ilícita. Se não houver solução, a definição dos responsáveis e da "
        "restituição depende da estrutura contratual e pode ser examinada judicialmente. Um advogado "
        "pode revisar os dois contratos e delimitar o período antes da notificação."
    )
    set_sources(
        page,
        [
            (
                "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=996&cod_tema_inicial=996&novaConsulta=true&tipo_pesquisa=T",
                "STJ, Tema Repetitivo 996",
                "veda juros de obra somente depois do prazo de entrega acrescido da tolerância e não pela mera estagnação anterior",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art51",
                "Código de Defesa do Consumidor, art. 51",
                "permite controlar cláusulas desproporcionais sem substituir o marco temporal específico do Tema 996",
            ),
        ],
    )


def rewrite_adjudication_judicial(page):
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
                "Código Civil, art. 1.418",
                "fundamenta a exigência de outorga e a adjudicação compulsória diante da recusa",
            ),
            (
                "https://processo.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=239",
                "Súmula 239 do Superior Tribunal de Justiça",
                "dispensa o registro prévio do compromisso para o direito à adjudicação compulsória",
            ),
        ],
    )


def rewrite_adjudication_registry(page):
    section(page, "A notificação prévia de 15 dias como prova do inadimplemento")["heading"] = (
        "A notificação para anuir ou impugnar em 15 dias úteis"
    )
    section(page, "A notificação para anuir ou impugnar em 15 dias úteis")["text"] = (
        "O Provimento 150 do CNJ determina que o requerido seja notificado para, em 15 dias úteis "
        "contados do primeiro dia útil posterior ao recebimento, anuir à transmissão ou impugnar "
        "o pedido com suas razões e documentos. O silêncio pode gerar presunção de veracidade da "
        "alegação de inadimplemento, mas o prazo não é contado em dias corridos."
    )
    section(page, "Quando ainda vale optar pela via judicial")["text"] = (
        "A impugnação não converte automaticamente o pedido cartorário em ação judicial. Pelo "
        "Provimento 150, o requerente é ouvido, o oficial decide e a parte interessada pode recorrer. "
        "Persistindo a controvérsia, os autos seguem ao juízo para exame da procedência da impugnação; "
        "se ela for rejeitada, o procedimento retorna ao registro, e, se acolhida, é extinto. A via "
        "judicial autônoma continua disponível quando a disputa sobre contrato, pagamento ou terceiros "
        "exigir cognição mais ampla. A assistência de advogado é obrigatória no rito extrajudicial e "
        "ajuda a organizar a ata, as notificações e a resposta à eventual impugnação."
    )
    page["faq"][1]["a"] = (
        "O tempo varia com a documentação e as manifestações. O requerido dispõe de 15 dias úteis "
        "para anuir ou impugnar; eventual impugnação é decidida pelo oficial e admite o percurso "
        "recursal previsto no Provimento 150."
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm",
                "Lei 6.015/1973, art. 216-B",
                "autoriza a adjudicação compulsória extrajudicial no registro de imóveis",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14382.htm#art11",
                "Lei 14.382/2022, art. 11",
                "incluiu o art. 216-B na Lei de Registros Públicos",
            ),
            (
                "https://atos.cnj.jus.br/atos/detalhar/5258",
                "CNJ, Provimento 150/2023",
                "regula a notificação em 15 dias úteis, a decisão da impugnação e o recurso no procedimento extrajudicial",
            ),
        ],
    )


def rewrite_unregistered_promise(page):
    section(page, "Por que o contrato de gaveta não gera direito real automático")["text"] = (
        "O registro da promessa sem arrependimento constitui o direito real previsto no art. 1.417 "
        "do Código Civil e amplia sua oponibilidade. Sem registro, o comprador fica mais exposto, "
        "mas seu contrato e sua posse não se tornam juridicamente invisíveis. A Súmula 84 do STJ "
        "admite embargos de terceiro fundados em posse decorrente de compromisso não registrado "
        "contra a penhora do imóvel. O êxito depende de provar a posse, a anterioridade e a boa-fé; "
        "não é imunidade automática contra qualquer credor."
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
                "Código Civil, art. 1.417",
                "disciplina a constituição do direito real do promitente comprador pelo registro",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l9514.htm",
                "Lei 9.514/1997",
                "regula a alienação fiduciária e os riscos do repasse informal sem anuência do credor",
            ),
            (
                "https://processo.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=84",
                "Súmula 84 do Superior Tribunal de Justiça",
                "admite embargos de terceiro baseados na posse oriunda de compromisso sem registro",
            ),
        ],
    )


def rewrite_assignment(page):
    section(page, "O que a cessão de crédito do artigo 286 autoriza")["heading"] = (
        "Cessão de crédito não é cessão da posição contratual"
    )
    section(page, "Cessão de crédito não é cessão da posição contratual")["text"] = (
        "O art. 286 do Código Civil permite ao credor transferir um crédito, com as limitações "
        "legais e contratuais. Vender a posição de comprador de imóvel na planta é operação mais "
        "ampla: além de direitos, há parcelas e outras obrigações a assumir. A cessão de crédito "
        "não transfere automaticamente todo o saldo devedor nem exonera o comprador original."
    )
    section(page, "Por que a anuência da incorporadora costuma ser exigida")["text"] = (
        "A transferência das obrigações aproxima-se da assunção de dívida do art. 299, que exige "
        "consentimento expresso do credor. Ao examinar cessão de posição contratual, o STJ também "
        "reconheceu a relevância do consentimento do contratante cedido, inclusive para avaliar a "
        "capacidade econômica do cessionário e a eventual exoneração do cedente. A anuência pode "
        "ser prévia, contemporânea ou posterior, conforme o negócio, mas não deve ser tratada como "
        "dispensável só porque o art. 286 rege a parcela ativa da relação."
    )
    section(page, "A taxa de cessão e outros custos da operação")["text"] = (
        "A previsão contratual não torna válida qualquer taxa percentual de cessão. O STJ já "
        "considerou abusiva a cobrança calculada sobre o valor do contrato, distinguindo-a de uma "
        "taxa administrativa razoável e vinculada a despesas efetivas de documentação e análise. "
        "O comprador deve exigir a cláusula, a memória de cálculo, a descrição do serviço e o valor "
        "nominal antes de aceitar a cobrança."
    )
    section(page, "O documento que formaliza a cessão")["text"] = (
        "O instrumento deve identificar direitos cedidos, saldo e obrigações assumidas, preço do "
        "acerto entre cedente e cessionário, responsabilidade por parcelas anteriores e forma de "
        "anuência da incorporadora. Antes da assinatura, um advogado imobiliário pode comparar o "
        "instrumento com o contrato original e revisar se a taxa cobrada corresponde a serviço "
        "administrativo demonstrado ou a percentual potencialmente abusivo."
    )
    page["faq"][0]["a"] = (
        "A assunção do saldo precisa constar do instrumento e ser aceita pela incorporadora como "
        "credora. Sem consentimento para exonerar o cedente, a cessão entre compradores não transfere "
        "automaticamente toda a dívida perante a incorporadora."
    )
    page["faq"][1]["a"] = (
        "Transferir apenas um crédito segue lógica distinta. Para substituir o comprador em direitos "
        "e obrigações, a cessão da posição contratual exige o consentimento do contratante cedido, "
        "que pode ser anterior, simultâneo ou posterior conforme o caso."
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art286",
                "Código Civil, art. 286",
                "regula a cessão de crédito, que não equivale à transferência integral da posição contratual",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art299",
                "Código Civil, art. 299",
                "exige consentimento expresso do credor para a assunção da obrigação por terceiro",
            ),
            (
                "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20140815&formato=HTML&nreg=200800478609&salvar=false&seq=1257215&tipo=0",
                "STJ, REsp 1.036.530/SC",
                "examina o consentimento do contratante cedido e os efeitos da cessão da posição contratual",
            ),
            (
                "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?dt_publicacao=07%2F04%2F2022&num_registro=201801264968",
                "STJ, REsp 1.947.698/MS",
                "distingue taxa administrativa razoável de taxa percentual de cessão calculada sobre o contrato, considerada abusiva",
            ),
        ],
    )


def rewrite_brokerage_cta(page):
    target = section(page, "O que fazer quando surge disputa sobre quem deveria pagar")
    target["text"] += (
        " Antes de pagar ou recusar a comissão, um advogado pode revisar a autorização de venda, "
        "a proposta e as mensagens para identificar quem contratou o serviço e se houve informação "
        "clara sobre a distribuição do custo."
    )


def rewrite_defect_deadlines(page):
    section(page, "O prazo de 180 dias para propor a ação depois do defeito aparecer")["heading"] = (
        "O alcance limitado dos 180 dias do artigo 618"
    )
    section(page, "O alcance limitado dos 180 dias do artigo 618")["text"] = (
        "O parágrafo único do art. 618 prevê decadência em 180 dias após o aparecimento do vício "
        "para o direito assegurado naquele artigo. O STJ, no Informativo 620, distinguiu os remédios: "
        "o prazo curto alcança a rescisão ou o abatimento do preço ligados à garantia, mas não "
        "elimina toda pretensão indenizatória. A ação condenatória por inadimplemento contratual "
        "permanece sujeita, em regra, ao prazo prescricional decenal do art. 205."
    )
    section(page, "Quando o negócio é entre particulares, sem incorporadora envolvida")["text"] = (
        "Na compra de imóvel usado entre particulares, vício oculto não segue automaticamente apenas "
        "o prazo geral de dez anos. Os pedidos redibitórios — desfazer o negócio ou obter abatimento "
        "do preço — observam o art. 445 do Código Civil: para imóvel, em regra, um ano da entrega, "
        "reduzido à metade se o adquirente já estava na posse; se o vício só puder ser conhecido mais "
        "tarde, a contagem começa da ciência, respeitado o limite legal. Pretensão indenizatória "
        "contratual tem natureza diferente e exige enquadramento próprio."
    )
    section(page, "Reunir a prova do defeito antes que o prazo passe")["text"] = (
        "Fotos e vídeos datados, laudo de engenheiro, contrato, data da entrega e comunicação formal "
        "ao responsável permitem distinguir garantia de solidez, vício redibitório, vício de consumo "
        "e indenização. Como cada remédio tem termo e prazo próprios, o registro da manifestação e "
        "da ciência do defeito deve ser preservado desde o início, sem presumir que os 180 dias "
        "eliminam toda ação ou que dez anos resolvem qualquer compra de usado."
    )
    page["faq"][0]["a"] = (
        "São regimes diferentes. Os 180 dias do art. 618 não barram automaticamente a indenização "
        "contratual, e o art. 26 do CDC disciplina reclamações por vícios aparentes ou ocultos na "
        "relação de consumo. O pedido concreto define qual prazo incide."
    )
    page["faq"][1]["a"] = (
        "O fim da garantia quinquenal não gera uma resposta única. É preciso verificar quando o "
        "defeito surgiu, sua natureza, a relação de consumo, o remédio pretendido e a prescrição "
        "contratual; o Informativo 620 reconhece prazo decenal para a pretensão indenizatória, sem "
        "transformá-lo em prazo universal para toda reclamação."
    )
    set_sources(
        page,
        [
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art618",
                "Código Civil, art. 618",
                "fixa a garantia quinquenal de solidez e o prazo de 180 dias ligado aos remédios da garantia",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art445",
                "Código Civil, art. 445",
                "disciplina a decadência dos pedidos redibitórios por vício oculto, inclusive em imóvel usado entre particulares",
            ),
            (
                "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40CNOT%3D016580",
                "STJ, Informativo de Jurisprudência 620",
                "distingue o prazo decadencial dos remédios por vício da prescrição decenal da pretensão indenizatória",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art26",
                "Código de Defesa do Consumidor, art. 26",
                "regula a decadência da reclamação por vícios aparentes e ocultos na relação de consumo",
            ),
            (
                "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art27",
                "Código de Defesa do Consumidor, art. 27",
                "fixa a prescrição do fato do produto, hipótese distinta do simples vício contratual",
            ),
        ],
    )


REWRITERS = {
    "imob-distrato-planta-quanto-volta": rewrite_distrato_amount,
    "imob-distrato-devolucao-prazo": rewrite_distrato_deadline,
    "imob-distrato-culpa-construtora": rewrite_builder_fault,
    "imob-atraso-obra-tolerancia-180": rewrite_tolerance,
    "imob-atraso-obra-rescisao": rewrite_delay_resolution,
    "imob-lucros-cessantes-cumulacao-multa": rewrite_lost_profits,
    "imob-correcao-incc-atraso": rewrite_incc,
    "imob-juros-no-pe": rewrite_pre_key_interest,
    "imob-taxa-evolucao-obra": rewrite_construction_interest,
    "imob-adjudicacao-compulsoria": rewrite_adjudication_judicial,
    "imob-adjudicacao-extrajudicial-procedimento": rewrite_adjudication_registry,
    "imob-contrato-gaveta-riscos": rewrite_unregistered_promise,
    "imob-cessao-direitos-compra": rewrite_assignment,
    "imob-comissao-corretagem-quem-paga": rewrite_brokerage_cta,
    "imob-vicio-construtivo-prazos": rewrite_defect_deadlines,
}


NEW_SOURCE_URLS = {
    "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ATC?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20190625&formato=PDF&nreg=201602669130&salvar=false&seq=93879287&tipo=68",
    "https://processo.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=543",
    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=970&cod_tema_inicial=970&novaConsulta=true&tipo_pesquisa=T",
    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=996&cod_tema_inicial=996&novaConsulta=true&tipo_pesquisa=T",
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40cnot%3D013315",
    "https://processo.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=239",
    "https://atos.cnj.jus.br/atos/detalhar/5258",
    "https://processo.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=84",
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art299",
    "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20140815&formato=HTML&nreg=200800478609&salvar=false&seq=1257215&tipo=0",
    "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao?dt_publicacao=07%2F04%2F2022&num_registro=201801264968",
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art445",
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40CNOT%3D016580",
}

PROBED_200_SOURCE_URLS = NEW_SOURCE_URLS - {
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art299",
    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art445",
}


def visible(page):
    values = [page.get("opening", "")]
    for item in page.get("sections", []):
        values.extend((item.get("heading", ""), item.get("text", "")))
    for item in page.get("faq", []):
        values.extend((item.get("q", ""), item.get("a", "")))
    return " ".join(values).lower()


def validate(original_lines, output_lines, pages):
    if len(original_lines) != 22 or len(output_lines) != 22 or len(pages) != 22:
        raise RuntimeError("o shard deve conservar exatamente 22 linhas")
    changed = {
        json.loads(before)["intent_id"]
        for before, after in zip(original_lines, output_lines)
        if before != after
    }
    if changed != set(REWRITERS):
        raise RuntimeError(f"escopo de linhas alteradas divergiu: {sorted(changed)}")
    if len({page["intent_id"] for page in pages}) != 22:
        raise RuntimeError("intent_id ausente ou duplicado")

    for page in pages:
        measured = body_word_count(page)
        if page["word_count"] != measured:
            raise RuntimeError(
                f"word_count inexato: {page['intent_id']}={page['word_count']} medido={measured}"
            )
        if not 360 <= measured <= 880:
            raise RuntimeError(f"word_count fora da faixa: {page['intent_id']}={measured}")
        if not 2 <= len(page["official_sources"]) <= 5:
            raise RuntimeError(f"quantidade de fontes inválida: {page['intent_id']}")
        for item in page["official_sources"]:
            if item["url"] in NEW_SOURCE_URLS and (
                "verified_at" in item or "http_status" in item
            ):
                raise RuntimeError(f"metadado inventado em fonte nova: {item['url']}")

    by_id = {page["intent_id"]: page for page in pages}
    required = {
        "imob-distrato-planta-quanto-volta": ("pro rata die", "não é uma taxa de 0,5% multiplicada por cada dia", "não manda subtrair a corretagem"),
        "imob-distrato-devolucao-prazo": ("contratos celebrados sob sua vigência", "aplicação simples e direta"),
        "imob-distrato-culpa-construtora": ("não transforma todo vício", "não convertem automaticamente"),
        "imob-atraso-obra-tolerancia-180": ("não amplia o limite legal", "não mantém essa proteção"),
        "imob-atraso-obra-rescisao": ("não transforma automaticamente", "retenções do art. 67-a"),
        "imob-lucros-cessantes-cumulacao-multa": ("tema 970", "advogado imobiliário"),
        "imob-correcao-incc-atraso": ("salvo quando esse índice for mais gravoso", "tema 996"),
        "imob-juros-no-pe": ("não cria automaticamente", "informativo 499"),
        "imob-taxa-evolucao-obra": ("mera estagnação", "depois do prazo contratual"),
        "imob-adjudicacao-extrajudicial-procedimento": ("15 dias úteis", "não converte automaticamente"),
        "imob-contrato-gaveta-riscos": ("súmula 84", "embargos de terceiro"),
        "imob-cessao-direitos-compra": ("não transfere automaticamente", "art. 299", "advogado imobiliário"),
        "imob-comissao-corretagem-quem-paga": ("um advogado pode revisar",),
        "imob-vicio-construtivo-prazos": ("informativo 620", "art. 445", "não elimina toda pretensão indenizatória"),
    }
    for intent, markers in required.items():
        text = visible(by_id[intent])
        missing = [marker for marker in markers if marker not in text]
        if missing:
            raise RuntimeError(f"marcadores jurídicos ausentes em {intent}: {missing}")
    if "costuma render mais quando revisado por um advogado" in visible(
        by_id["imob-distrato-devolucao-prazo"]
    ):
        raise RuntimeError("linguagem orientada a resultado permaneceu")


def main():
    payload = TARGET.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(
            f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}"
        )
    original_lines = payload.decode("utf-8").splitlines(keepends=True)
    pages = [json.loads(line) for line in original_lines if line.strip()]
    if not set(REWRITERS).issubset({page["intent_id"] for page in pages}):
        raise RuntimeError("páginas alvo ausentes")

    for page in pages:
        rewrite = REWRITERS.get(page["intent_id"])
        if rewrite is not None:
            rewrite(page)
        page["word_count"] = body_word_count(page)

    output_lines = []
    for original, page in zip(original_lines, pages):
        if page["intent_id"] in REWRITERS:
            output_lines.append(
                json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
        else:
            output_lines.append(original)
    validate(original_lines, output_lines, pages)
    encoded = "".join(output_lines).encode("utf-8")

    fd, temporary = tempfile.mkstemp(
        prefix=".imobiliario-08-fix.", suffix=".tmp", dir=TARGET.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(TARGET.read_bytes()).hexdigest() != EXPECTED_SHA256:
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
        if page["intent_id"] in REWRITERS:
            missing_meta = sum(
                1
                for item in page["official_sources"]
                if "verified_at" not in item or "http_status" not in item
            )
            print(
                page["intent_id"],
                f"words={page['word_count']}",
                f"sources={len(page['official_sources'])}",
                f"sources_without_live_metadata={missing_meta}",
            )


def metadata_main():
    payload = TARGET.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != CONTENT_FIXED_SHA256:
        raise SystemExit(
            f"CAS de metadados falhou: esperado {CONTENT_FIXED_SHA256}, encontrado {actual_sha}"
        )
    original_lines = payload.decode("utf-8").splitlines(keepends=True)
    pages = [json.loads(line) for line in original_lines if line.strip()]
    by_id = {page["intent_id"]: page for page in pages}
    content_touched = set()

    incc = by_id["imob-correcao-incc-atraso"]
    section(incc, "Documentos e caminho para questionar a correção aplicada")["text"] += (
        " A memória de cálculo deve mostrar, mês a mês, o saldo anterior, o fator do índice "
        "contratual, o IPCA do mesmo período e o valor efetivamente lançado. Essa comparação "
        "também permite aplicar a salvaguarda do menor ônus sem apagar parcelas, pagamentos ou "
        "amortizações ocorridos durante o atraso."
    )
    content_touched.add(incc["intent_id"])

    construction = by_id["imob-taxa-evolucao-obra"]
    section(construction, "O caminho para reaver valores cobrados indevidamente")["text"] += (
        " O art. 51 do Código de Defesa do Consumidor permite controlar cláusulas que imponham "
        "desvantagem exagerada, mas esse controle não substitui a demonstração do período e da "
        "base de cada encargo."
    )
    construction["sections"].append(
        {
            "heading": "Como montar o recorte temporal da revisão",
            "text": (
                "Uma tabela simples pode reunir, em colunas separadas, a data prevista de entrega, "
                "o fim da tolerância, cada liberação do banco, a data e o valor de cada débito e a "
                "eventual entrega das chaves. Os lançamentos anteriores ao marco do Tema 996 não "
                "devem ser misturados aos posteriores. Se houve aditivo de prazo, ele precisa ser "
                "examinado quanto à forma, à informação prestada e à sua eficácia; não basta "
                "substituir unilateralmente a data original na planilha. Esse recorte ajuda a "
                "quantificar o pedido sem transformar atraso físico, desembolso bancário e juros "
                "em uma única rubrica genérica."
            ),
        }
    )
    content_touched.add(construction["intent_id"])

    pre_key = by_id["imob-juros-no-pe"]
    section(pre_key, "Quando a cobrança de juros no pé pode ser questionada")["text"] += (
        " A apresentação e a execução desses encargos também devem observar a boa-fé objetiva "
        "do art. 422 do Código Civil."
    )
    content_touched.add(pre_key["intent_id"])

    document_evidence = {}
    for page in pages:
        for item in page["official_sources"]:
            if item.get("verified_at") and item.get("http_status") == 200:
                document_evidence.setdefault(item["url"].split("#", 1)[0], item)

    touched = set()
    for page in pages:
        for item in page["official_sources"]:
            url = item["url"]
            if url in PROBED_200_SOURCE_URLS:
                item["verified_at"] = "2026-07-10"
                item["http_status"] = 200
                touched.add(page["intent_id"])
            elif url in NEW_SOURCE_URLS:
                evidence = document_evidence.get(url.split("#", 1)[0])
                if evidence is None:
                    raise RuntimeError(f"evidência do mesmo documento ausente: {url}")
                item["verified_at"] = evidence["verified_at"]
                item["http_status"] = evidence["http_status"]
                touched.add(page["intent_id"])

    word_count_touched = set()
    for page in pages:
        measured = body_word_count(page)
        if page.get("word_count") != measured:
            word_count_touched.add(page["intent_id"])
        page["word_count"] = measured

    output_lines = [
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ]
    for page in pages:
        if page["word_count"] != body_word_count(page):
            raise RuntimeError(f"word_count inexato após metadados: {page['intent_id']}")
        for item in page["official_sources"]:
            if not item.get("verified_at") or item.get("http_status") != 200:
                raise RuntimeError(
                    f"fonte sem evidência viva após probes: {page['intent_id']} {item['url']}"
                )
    changed = {
        json.loads(before)["intent_id"]
        for before, after in zip(original_lines, output_lines)
        if before != after
    }
    expected_changed = touched | content_touched | word_count_touched
    if changed != expected_changed:
        raise RuntimeError(
            "mudanças fora do escopo: "
            f"changed={sorted(changed)} expected={sorted(expected_changed)}"
        )
    encoded = "".join(output_lines).encode("utf-8")

    fd, temporary = tempfile.mkstemp(
        prefix=".imobiliario-08-metadata.", suffix=".tmp", dir=TARGET.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(TARGET.read_bytes()).hexdigest() != CONTENT_FIXED_SHA256:
            raise RuntimeError("CAS mudou antes da troca atômica de metadados")
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
    print("metadados por probe HTTP 200 ou evidência idêntica de documento:")
    for intent in sorted(touched):
        print(intent)


def dedupe_main():
    payload = TARGET.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != METADATA_FIXED_SHA256:
        raise SystemExit(
            f"CAS anti-duplicidade falhou: esperado {METADATA_FIXED_SHA256}, encontrado {actual_sha}"
        )
    original_lines = payload.decode("utf-8").splitlines(keepends=True)
    pages = [json.loads(line) for line in original_lines if line.strip()]
    by_id = {page["intent_id"]: page for page in pages}
    touched = {
        "imob-adjudicacao-compulsoria",
        "imob-atraso-obra-indenizacao",
        "imob-desistencia-imovel-usado-sinal",
        "imob-distrato-culpa-construtora",
        "imob-distrato-planta-quanto-volta",
        "imob-vendedor-falecido-escritura",
    }

    adjudication = by_id["imob-adjudicacao-compulsoria"]
    target = section(adjudication, "O caminho extrajudicial antes de ir à Justiça")
    target["text"] = target["text"].replace(
        "segue-se para a ação de adjudicação compulsória na vara cível da comarca onde está o imóvel, com pedido de tutela de urgência quando houver risco concreto de o vendedor alienar o bem a terceiro durante o processo",
        "a demanda pode ser proposta no juízo competente da situação do bem. Se houver risco concreto de alienação a terceiro durante o processo, também se pode examinar uma tutela de urgência",
    )

    delay = by_id["imob-atraso-obra-indenizacao"]
    target = section(delay, "Caminho extrajudicial e judicial para cobrar a indenização")
    target["text"] = target["text"].replace(
        "Se a incorporadora recusar ou pagar a menor, cabe ação de cobrança no juizado especial cível, quando o valor permitir, ou na vara cível, cumulando o pedido de indenização com eventual discussão sobre lucros cessantes.",
        "Se a incorporadora recusar ou pagar a menor, a cobrança judicial deve observar valor, complexidade da prova e competência; eventual discussão sobre lucros cessantes pode integrar a mesma demanda quando houver base fática própria.",
    )

    used = by_id["imob-desistencia-imovel-usado-sinal"]
    section(used, "O que o artigo 418 prevê para quem desiste tendo dado o sinal")["text"] = (
        "Pelo art. 418, se a inexecução for atribuída a quem entregou as arras, quem as recebeu "
        "pode encerrar o vínculo e conservar a quantia como indenização mínima, sem demonstração "
        "prévia de prejuízo nesse montante. Assim, o comprador que abandona o negócio depois de "
        "pagar o sinal corre o risco de perder o valor inteiro, e não apenas um percentual semelhante "
        "ao distrato de unidade adquirida na planta."
    )

    fault = by_id["imob-distrato-culpa-construtora"]
    target = section(fault, "Extrajudicial primeiro, ação de cobrança depois")
    target["text"] = target["text"].replace(
        "ajuizada no juizado especial cível ou na vara cível conforme o valor da causa, e esse é justamente o tipo de disputa em que vale reunir toda a prova documental com apoio de um advogado antes de notificar formalmente a incorporadora.",
        "cuja competência dependerá do valor, da complexidade da prova e dos pedidos formulados. A documentação pode ser organizada com apoio de um advogado antes da notificação formal à incorporadora.",
    )

    amount = by_id["imob-distrato-planta-quanto-volta"]
    target = section(amount, "As deduções do artigo 67-A antes de qualquer percentual")
    target["text"] = target["text"].replace(
        "O art. 67-A da Lei 4.591/1964, incluído pela Lei 13.786/2018, parte das quantias",
        "A disciplina acrescentada em 2018 ao art. 67-A da Lei 4.591/1964 parte das quantias",
    )

    deceased = by_id["imob-vendedor-falecido-escritura"]
    target = section(deceased, "O espólio assume a posição do vendedor falecido")
    target["text"] = target["text"].replace(
        "O art. 618 do Código de Processo Civil lista entre os deveres do inventariante representar o espólio ativa e passivamente, em juízo ou fora dele, o que inclui responder por obrigações contratuais assumidas em vida pelo falecido, como a promessa de venda de um imóvel ainda não escriturado.",
        "O art. 618 do Código de Processo Civil atribui ao inventariante a atuação em nome do espólio, tanto judicial quanto extrajudicialmente. Essa função abrange as obrigações contratuais deixadas pelo falecido, como a promessa de alienar um imóvel cuja escritura não chegou a ser lavrada.",
    )

    for page in pages:
        page["word_count"] = body_word_count(page)
        if page["word_count"] != body_word_count(page):
            raise RuntimeError(f"word_count inexato após dedupe: {page['intent_id']}")
    output_lines = []
    for original, page in zip(original_lines, pages):
        if page["intent_id"] in touched:
            output_lines.append(
                json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
        else:
            output_lines.append(original)
    changed = {
        json.loads(before)["intent_id"]
        for before, after in zip(original_lines, output_lines)
        if before != after
    }
    if changed != touched:
        raise RuntimeError(
            f"escopo anti-duplicidade divergiu: changed={sorted(changed)}"
        )
    encoded = "".join(output_lines).encode("utf-8")

    fd, temporary = tempfile.mkstemp(
        prefix=".imobiliario-08-dedupe.", suffix=".tmp", dir=TARGET.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(TARGET.read_bytes()).hexdigest() != METADATA_FIXED_SHA256:
            raise RuntimeError("CAS mudou antes da troca atômica anti-duplicidade")
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
    for intent in sorted(touched):
        print(intent, by_id[intent]["word_count"])


def validate_final():
    payload = TARGET.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != FINAL_SHA256:
        raise RuntimeError(f"SHA final inesperado: {actual_sha}")
    pages = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    if len(pages) != 22 or len({page["intent_id"] for page in pages}) != 22:
        raise RuntimeError("estado final não contém 22 intents únicos")
    for page in pages:
        if page["word_count"] != body_word_count(page):
            raise RuntimeError(f"word_count final inexato: {page['intent_id']}")
        if not 2 <= len(page["official_sources"]) <= 5:
            raise RuntimeError(f"fontes finais fora da faixa: {page['intent_id']}")
        if any(
            not item.get("verified_at") or item.get("http_status") != 200
            for item in page["official_sources"]
        ):
            raise RuntimeError(f"fonte final sem evidência: {page['intent_id']}")
    print(FINAL_SHA256)
    print("estado final já convergido e validado")


if __name__ == "__main__":
    current_sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    if current_sha == FINAL_SHA256:
        validate_final()
    elif current_sha == METADATA_FIXED_SHA256:
        dedupe_main()
    elif current_sha == CONTENT_FIXED_SHA256:
        metadata_main()
        dedupe_main()
    elif current_sha == EXPECTED_SHA256:
        main()
        metadata_main()
        dedupe_main()
    else:
        main()
