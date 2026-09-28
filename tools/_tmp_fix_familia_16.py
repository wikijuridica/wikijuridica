#!/usr/bin/env python3
"""Reescreve familia-16 e promove o candidato de forma atomica."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/editorial/v2_pages/familia-16.jsonl"
EXPECTED_SHA256 = "02a3c7acd365bfbf773e0c058e97d6258cc54a9a168132cca91d4615427cdb7f"


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def words(value: str) -> list[str]:
    folded = "".join(
        char
        for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    ).lower()
    return re.findall(r"[^\W_]+", folded, re.UNICODE)


def body_word_count(page: dict) -> int:
    parts = [page["opening"]]
    for section in page["sections"]:
        parts.extend((section["heading"], section["text"]))
    for item in page.get("faq", []):
        parts.extend((item["q"], item["a"]))
    return sum(len(words(part)) for part in parts)


def section(heading: str, text: str) -> dict:
    return {"heading": heading, "text": text}


def faq(question: str, answer: str) -> dict:
    return {"q": question, "a": answer}


def main() -> None:
    if file_sha256(TARGET) != EXPECTED_SHA256:
        raise SystemExit("familia-16 mudou desde a revisao; promocao recusada")

    originals = [json.loads(line) for line in TARGET.read_text(encoding="utf-8").splitlines()]
    original_by_id = {page["intent_id"]: page for page in originals}
    source_by_id = {
        page["intent_id"]: {item["url"]: item for item in page["official_sources"]}
        for page in originals
    }

    def source(intent_id: str, url: str, name: str, anchor_claim: str) -> dict:
        item = {"url": url, "name": name, "anchor_claim": anchor_claim}
        previous = source_by_id[intent_id].get(url)
        if previous:
            for field in ("verified_at", "http_status"):
                if field in previous:
                    item[field] = previous[field]
        return item

    def build(
        intent_id: str,
        title: str,
        meta_description: str,
        h1: str,
        opening: str,
        sections: list[dict],
        faqs: list[dict],
        sources: list[dict],
        internal_link_topics: list[str],
    ) -> dict:
        page = {
            "intent_id": intent_id,
            "title": title,
            "meta_description": meta_description,
            "h1": h1,
            "opening": opening,
            "sections": sections,
            "faq": faqs,
            "official_sources": sources,
            "internal_link_topics": internal_link_topics,
            "lane": "informativa",
            "word_count": 0,
        }
        page["word_count"] = body_word_count(page)
        return page

    pages = [
        build(
            "fam-juizado-violencia-domestica",
            "Juizado de Violência Doméstica: o que ele julga",
            "Saiba quais pedidos cabem no Juizado de Violência Doméstica, como funciona o divórcio e para onde vai o caso quando não há vara especializada.",
            "Competência do Juizado de Violência Doméstica, do crime às medidas familiares",
            "O Juizado de Violência Doméstica e Familiar contra a Mulher tem competência cível e criminal para causas decorrentes da violência doméstica. Isso permite concentrar proteção e responsabilização no mesmo órgão judicial, mas não transforma todo conflito de família em violência doméstica nem reúne automaticamente assuntos diferentes no mesmo processo.\n\nA pergunta prática é dupla: qual juiz pode decidir e em quais autos cada pedido será apresentado. Divórcio, alimentos provisórios, restrição de convivência e partilha seguem regras próprias, mesmo quando alguns deles ficam sob responsabilidade da vara especializada.",
            [
                section(
                    "Competência dupla não significa processo único",
                    "O art. 14 da Lei 11.340/2006 atribui ao juizado o processo, o julgamento e a execução das causas cíveis e criminais ligadas à violência doméstica. Assim, o órgão pode apreciar o crime, a medida protetiva e providências civis urgentes que nasçam do mesmo contexto. A conexão precisa aparecer nos fatos; uma disputa patrimonial antiga, sem relação atual com a violência, não migra para a vara especializada apenas porque as partes são ex-cônjuges.\n\nTambém é importante separar órgão competente de número do processo. Um pedido de família pode exigir petição e autuação próprias, conforme a organização do tribunal, ainda que seja distribuído ao mesmo juízo que acompanha a medida protetiva.",
                ),
                section(
                    "O divórcio pode ficar no órgão especializado, mas a partilha não",
                    "Em 2019, o art. 14-A passou a permitir que a ofendida escolha o órgão especializado também para encerrar o casamento ou reconhecer o fim da união estável. A faculdade evita deslocamento para outra vara, mas não funde automaticamente esse pedido ao processo criminal. Se a situação de violência começar depois que o divórcio já foi ajuizado, a ação tem preferência no juízo em que se encontra.\n\nA divisão do patrimônio ficou expressamente fora dessa competência. O divórcio pode ser decretado no juizado, enquanto a partilha segue perante o juízo cível ou de família competente. Certidão de casamento, pacto antenupcial, documentos da união estável e identificação do processo protetivo ajudam a definir a distribuição correta.",
                ),
                section(
                    "Alimentos e convivência podem exigir uma resposta urgente",
                    "A Lei Maria da Penha permite restringir ou suspender visitas aos dependentes e admite alimentos provisionais ou provisórios como medidas protetivas. O STJ também reconhece que o juizado pode executar alimentos fixados com essa natureza. Isso não equivale a decidir definitivamente toda guarda: a extensão da medida depende do risco, da urgência e do pedido apresentado.\n\nImagine que a mãe saia de casa com os filhos após uma ameaça e já tenha medida proibindo contato. Ela pode informar certidões de nascimento, despesas imediatas, decisão protetiva e eventual acordo anterior para que o juízo avalie alimentos e convivência sem esperar o desfecho criminal.",
                ),
                section(
                    "Onde o caso tramita quando a comarca não tem juizado",
                    "O art. 33 resolve a transição de forma específica: enquanto não estruturados os juizados especializados, as varas criminais acumulam competência cível e criminal decorrente da Lei Maria da Penha. Isso não produz fusão automática das ações de família com os autos criminais. Também não é correto dividir automaticamente a demanda entre uma vara criminal e outra cível comum.\n\nA distribuição concreta ainda segue a organização judiciária local. Antes de protocolar, vale confirmar no balcão judicial, na Defensoria Pública ou no Ministério Público qual unidade recebe medidas protetivas e ações relacionadas. Essa conferência evita remessa entre juízos sem prometer que todos os pedidos permanecerão nos mesmos autos.",
                ),
            ],
            [
                faq(
                    "É obrigatório já ter medida protetiva para pedir o divórcio no juizado?",
                    "O art. 14-A exige que a autora seja ofendida em situação de violência doméstica, mas não condiciona a opção a uma medida protetiva já deferida. Os fatos e a competência precisam ser demonstrados na ação.",
                ),
                faq(
                    "A vítima precisa de advogado no divórcio?",
                    "Sim. O pedido judicial de divórcio exige representação por advogado ou Defensoria Pública; a dispensa de advogado se refere ao requerimento inicial de medida protetiva, não à ação de família.",
                ),
            ],
            [
                source(
                    "fam-juizado-violencia-domestica",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art14",
                    "Lei Maria da Penha, art. 14",
                    "fundamenta a competência cível e criminal do Juizado de Violência Doméstica e Familiar contra a Mulher",
                ),
                source(
                    "fam-juizado-violencia-domestica",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art14a",
                    "Lei Maria da Penha, art. 14-A",
                    "fundamenta a opção pelo divórcio ou dissolução no juizado, a exclusão da partilha e a regra da ação já ajuizada",
                ),
                source(
                    "fam-juizado-violencia-domestica",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art33",
                    "Lei Maria da Penha, art. 33",
                    "define a acumulação cível e criminal pelas varas criminais enquanto não houver juizado estruturado",
                ),
                source(
                    "fam-juizado-violencia-domestica",
                    "https://processo.stj.jus.br/SCON/GetPDFINFJ?edicao=0550",
                    "STJ, Informativo 550",
                    "ancora a competência do juizado para executar alimentos fixados como medida protetiva",
                ),
            ],
            ["medidas protetivas de urgência", "divórcio litigioso", "guarda e convivência dos filhos"],
        ),
        build(
            "fam-indenizacao-vitima-violencia",
            "Indenização por violência doméstica: dois caminhos",
            "Entenda quando a sentença criminal pode fixar reparação mínima, o pedido expresso exigido pelo STJ e como avaliar uma ação civil complementar.",
            "Como a vítima pode buscar indenização pela violência doméstica",
            "A violência doméstica pode gerar reparação por danos morais, materiais e, conforme as sequelas, outros prejuízos demonstráveis. A vítima não precisa necessariamente começar uma ação civil do zero: a sentença penal condenatória pode fixar um valor mínimo. Para isso, porém, existe uma exigência processual que não deve ser esquecida.\n\nO valor criminal é um piso, não um teto. Se as perdas forem maiores, a via cível continua disponível, mas prazo, prova e possibilidade real de execução precisam ser examinados sem prometer recebimento.",
            [
                section(
                    "O pedido expresso exigido pelo Tema 983 do STJ",
                    "O art. 387, IV, do Código de Processo Penal autoriza a fixação de reparação mínima na condenação. No Tema 983, o STJ definiu a regra para violência doméstica: a acusação ou a própria ofendida deve formular pedido expresso de indenização por dano moral. Não é obrigatório indicar previamente uma quantia nem produzir instrução específica sobre o abalo moral, mas o pedido precisa existir.\n\nPor isso, a vítima deve conferir com o Ministério Público, com a assistência de acusação ou com seu representante se a denúncia ou outra manifestação processual contém esse requerimento. Sem ele, o juiz não deve criar a condenação civil mínima de ofício.",
                ),
                section(
                    "Quando uma ação civil complementar pode ser necessária",
                    "A reparação mínima não impede a cobrança de diferença na esfera cível. Tratamento psicológico, perda de renda, despesas médicas, mudança emergencial de residência e bens destruídos podem justificar valor superior, desde que relacionados ao ato ilícito. Os arts. 186 e 927 do Código Civil formam a base geral do dever de reparar.\n\nUm cenário comum é a sentença criminal reconhecer a agressão e fixar dano moral mínimo, enquanto a vítima possui recibos de terapia e comprovantes de afastamento profissional que não foram calculados naquele processo. Esses documentos, acompanhados da sentença, de laudos, notas fiscais, extratos e fotografias dos danos, permitem avaliar a complementação sem duplicar o que já foi pago.",
                ),
                section(
                    "O prazo de três anos não começa sempre no dia da agressão",
                    "O art. 206, § 3º, V, prevê três anos para a pretensão de reparação civil. Esse dado isolado não resolve o termo inicial. Quando a indenização depende de fato que também precisa ser apurado no juízo criminal, o art. 200 do Código Civil determina que a prescrição não corre antes da sentença penal definitiva; o STJ aplica essa regra quando há relação de prejudicialidade entre as esferas.\n\nSe não houve inquérito ou ação penal relevante para a prova civil, a conclusão pode ser diferente. A data do fato, o conhecimento da autoria, a existência da investigação e eventual vínculo conjugal precisam ser conferidos antes de afirmar quando o prazo termina.",
                ),
                section(
                    "Condenação não garante localização imediata de patrimônio",
                    "A indenização reconhece um crédito, mas seu recebimento depende da execução e de bens ou renda legalmente alcançáveis. A ausência atual de patrimônio não apaga o direito; pode apenas impedir ou retardar a satisfação naquele momento. Também é preciso distinguir absolvição por insuficiência de prova de uma decisão penal que reconheça categoricamente a inexistência do fato ou da autoria, pois os efeitos na ação civil não são iguais.\n\nAntes de escolher a rota, organize número do processo penal, decisões, pedido indenizatório, comprovantes do prejuízo e informações patrimoniais obtidas por meios lícitos. A Defensoria Pública pode orientar quem preencher os critérios de atendimento.",
                ),
            ],
            [
                faq(
                    "É necessário provar o sofrimento moral com laudo psicológico?",
                    "Para o valor mínimo do Tema 983, o STJ dispensa instrução específica do dano moral quando a violência doméstica está comprovada, desde que exista pedido expresso. Danos materiais e valores adicionais exigem prova compatível com o prejuízo alegado.",
                )
            ],
            [
                source(
                    "fam-indenizacao-vitima-violencia",
                    "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art387",
                    "Código de Processo Penal, art. 387, IV",
                    "autoriza a sentença condenatória a fixar valor mínimo para reparação dos danos da infração",
                ),
                source(
                    "fam-indenizacao-vitima-violencia",
                    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=983&cod_tema_inicial=983&novaConsulta=true&tipo_pesquisa=T",
                    "STJ, Tema Repetitivo 983",
                    "exige pedido expresso para o dano moral mínimo e dispensa indicação de quantia e instrução probatória específica",
                ),
                source(
                    "fam-indenizacao-vitima-violencia",
                    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art927",
                    "Código Civil, arts. 186 e 927",
                    "fundamenta o dever de reparar os prejuízos causados por ato ilícito",
                ),
                source(
                    "fam-indenizacao-vitima-violencia",
                    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art206",
                    "Código Civil, art. 206, § 3º, V",
                    "prevê o prazo geral de três anos para a pretensão de reparação civil",
                ),
                source(
                    "fam-indenizacao-vitima-violencia",
                    "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art200",
                    "Código Civil, art. 200",
                    "impede o curso da prescrição antes da sentença penal definitiva quando o fato deva ser apurado no juízo criminal",
                ),
            ],
            ["assistência de acusação", "danos materiais e morais", "medidas protetivas de urgência"],
        ),
        build(
            "fam-vitima-estrangeira-direitos",
            "Vítima migrante também tem proteção contra violência",
            "Mulher migrante pode denunciar violência doméstica mesmo sem documento migratório regular. Veja direitos, cautelas e canais públicos de atendimento.",
            "Mulher migrante sem documento pode pedir proteção no Brasil",
            "A proteção contra violência doméstica não depende de nacionalidade brasileira, visto válido ou autorização de residência. O agressor pode usar o medo de deportação, a retenção do passaporte ou a dependência econômica como instrumentos de controle, mas essas circunstâncias não retiram da mulher o direito de procurar a polícia e a Justiça.\n\nIsso não significa que uma irregularidade migratória deixe de existir. Significa que a denúncia de violência e um eventual procedimento de deportação têm fundamentos e garantias diferentes: pedir socorro não produz retirada automática do país.",
            [
                section(
                    "A situação migratória não afasta a Lei Maria da Penha",
                    "No art. 5º, o ponto decisivo não é o passaporte: a proteção alcança a agressão ligada ao gênero ocorrida no ambiente doméstico, familiar ou afetivo. Visto vencido ou residência irregular não afastam esse enquadramento. A Lei de Migração, em seu art. 4º, assegura ao migrante igualdade no acesso à vida, à segurança, à Justiça e à assistência jurídica gratuita para quem comprovar insuficiência de recursos.\n\nDelegacia, Ministério Público e Judiciário não podem recusar o registro ou o pedido protetivo apenas porque a vítima não apresentou CRNM. Se houver documento estrangeiro disponível, ele facilita a identificação, mas não deve ser recuperado mediante confronto com o agressor.",
                ),
                section(
                    "O que levar sem colocar a própria segurança em risco",
                    "Mensagens de ameaça, fotografias de lesões, prontuários, nomes de testemunhas e cópia segura do passaporte ou de outro documento ajudam no atendimento. Também é útil informar um telefone e um endereço em que a vítima possa receber contato sem exposição ao agressor. Se ela não domina o português, deve pedir atendimento com apoio linguístico; a disponibilidade de intérprete varia, por isso não convém prometer um serviço que o órgão local talvez não tenha de imediato.\n\nConsidere o caso de uma mulher cujo companheiro reteve o passaporte e ameaça chamar a imigração se ela sair de casa. Ela pode relatar tanto a agressão quanto a retenção do documento, sem voltar ao imóvel para buscá-lo antes de acionar a rede de proteção.",
                ),
                section(
                    "Por que a denúncia não causa deportação automática",
                    "O art. 50 da Lei 13.445/2017 define deportação como medida decorrente de procedimento administrativo por situação migratória irregular. Antes dela, deve haver notificação pessoal indicando a irregularidade e prazo de pelo menos sessenta dias para regularização, prorrogável por igual período mediante decisão fundamentada. A apuração da violência não substitui esse procedimento.\n\nAinda assim, não é correto prometer invisibilidade perante as autoridades migratórias. Se a vítima tiver dúvida sobre visto ou residência, pode tratar da regularização separadamente com a Defensoria Pública da União ou com a Polícia Federal, sem abandonar as providências urgentes de segurança.",
                ),
                section(
                    "Canais públicos e resposta em situação de perigo",
                    "A Central de Atendimento à Mulher, no número 180, informa direitos e localiza serviços próximos; em emergência ou risco imediato, o canal é o 190. Delegacias comuns também devem receber a ocorrência quando não houver unidade especializada. Defensoria Pública estadual, Ministério Público e centros de referência podem orientar sobre medida protetiva, abrigo e questões familiares.\n\nO atendimento migratório vem depois da segurança física quando há perigo atual. Guarde protocolos, número da ocorrência e cópias digitais dos documentos em conta a que o agressor não tenha acesso, sem divulgar localização em redes sociais.",
                ),
            ],
            [
                faq(
                    "O agressor pode cancelar sozinho o visto da vítima?",
                    "A ameaça não produz cancelamento automático. O efeito de separação ou fim do vínculo sobre a autorização de residência depende da modalidade migratória e deve ser conferido no procedimento próprio.",
                )
            ],
            [
                source(
                    "fam-vitima-estrangeira-direitos",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art5",
                    "Lei Maria da Penha, art. 5º",
                    "define o contexto doméstico, familiar ou afetivo protegido sem requisito de nacionalidade",
                ),
                source(
                    "fam-vitima-estrangeira-direitos",
                    "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13445.htm#art4",
                    "Lei de Migração, art. 4º",
                    "assegura ao migrante igualdade de direitos, acesso à Justiça e assistência jurídica nos termos legais",
                ),
                source(
                    "fam-vitima-estrangeira-direitos",
                    "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13445.htm#art50",
                    "Lei de Migração, art. 50",
                    "disciplina o procedimento, a notificação e o prazo de regularização anteriores à deportação",
                ),
                source(
                    "fam-vitima-estrangeira-direitos",
                    "https://www.gov.br/pt-br/servicos/denunciar-e-buscar-ajuda-a-vitimas-de-violencia-contra-mulheres",
                    "Governo Federal, serviço Ligue 180",
                    "informa a função nacional do canal de orientação e encaminhamento para mulheres em situação de violência",
                ),
            ],
            ["medidas protetivas de urgência", "assistência jurídica gratuita", "regularização migratória"],
        ),
        build(
            "fam-violencia-contra-mae-idosa",
            "Filho que agride a mãe idosa: proteção aplicável",
            "A violência de filho contra mãe idosa pode acionar a Lei Maria da Penha e o Estatuto da Pessoa Idosa. Entenda medidas, provas e notificações.",
            "Violência de filho contra mãe idosa: duas proteções que se somam",
            "Quando um filho ameaça, agride ou explora financeiramente a mãe idosa, a relação de parentesco não reduz a gravidade nem impede a aplicação da Lei Maria da Penha. A idade acrescenta a proteção do Estatuto da Pessoa Idosa, sem transformar o caso em simples desentendimento sobre cuidados.\n\nAs duas leis olham aspectos complementares: a primeira oferece medidas urgentes contra a violência doméstica; a segunda organiza direitos e deveres específicos de proteção à pessoa com sessenta anos ou mais.",
            [
                section(
                    "A idade da mãe não exclui a Lei Maria da Penha",
                    "O art. 5º da Lei 11.340/2006 abrange a violência ocorrida na unidade doméstica ou no âmbito da família. O Tema 1186 do STJ consolidou que a condição feminina é suficiente para atrair esse sistema protetivo no contexto doméstico, independentemente da idade, sem exigir prova de motivação exclusiva de gênero. A orientação vale para evitar que a proteção seja afastada apenas porque a vítima também pertence a outro grupo vulnerável.\n\nAgressão física, ameaça, humilhação, retenção de cartão bancário e apropriação de aposentadoria podem assumir naturezas diferentes. O enquadramento depende do ato provado, e não só do fato de agressor e vítima morarem juntos.",
                ),
                section(
                    "Quem deve notificar a violência contra a pessoa idosa",
                    "A denominação vigente é Estatuto da Pessoa Idosa. Seu art. 19 determina a notificação compulsória pelos serviços de saúde públicos e privados à autoridade sanitária quando houver suspeita ou confirmação de violência, além da comunicação aos órgãos competentes. Esses destinatários incluem autoridade policial, Ministério Público e conselhos da pessoa idosa indicados na lei.\n\nNão é correto atribuir indistintamente essa notificação técnica a qualquer instituição. Familiares, vizinhos e profissionais de outros setores podem denunciar, mas o dever específico do art. 19 recai sobre os serviços de saúde nos termos ali descritos.",
                ),
                section(
                    "Afastamento, proteção patrimonial e provas do risco",
                    "O juiz pode afastar o agressor do lar e proibir aproximação ou contato com base no art. 22 da Lei Maria da Penha. Se o filho administra dinheiro ou possui procuração, extratos bancários, contratos, comprovantes de saques, mensagens e relação de bens ajudam a revelar eventual violência patrimonial. Prontuários, fotografias, áudios obtidos licitamente e nomes de quem presenciou os fatos documentam agressões e ameaças.\n\nPor exemplo, se o filho retém o cartão da aposentadoria, impede a compra de remédios e ameaça a mãe quando ela pede contas, o pedido deve narrar cada ato, indicar datas aproximadas e explicar por que a permanência dele na residência mantém o risco.",
                ),
                section(
                    "Divergência sobre cuidados não basta para acusar violência",
                    "Discussões isoladas sobre médico, alimentação ou divisão de tarefas não configuram automaticamente violência doméstica. A resposta protetiva exige ato ou risco que atinja a integridade física, psicológica, sexual, moral ou patrimonial. Essa cautela evita usar a via penal para resolver mera discordância familiar sem deixar desprotegida a mãe que sofre coerção real.\n\nA medida protetiva independe de ação penal ou boletim de ocorrência prévio quando o risco está demonstrado. Em urgência, a informação pode ser levada à polícia ou ao Ministério Público; atendimento de saúde e segurança da vítima vêm antes da organização completa dos documentos.",
                ),
            ],
            [
                faq(
                    "A mãe precisa autorizar um familiar a fazer a denúncia?",
                    "Qualquer pessoa pode comunicar suspeita de violência às autoridades. A vontade e a palavra da mulher devem ser consideradas, mas risco grave ou incapacidade pode exigir atuação imediata da rede de proteção.",
                )
            ],
            [
                source(
                    "fam-violencia-contra-mae-idosa",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art5",
                    "Lei Maria da Penha, art. 5º",
                    "fundamenta a incidência da proteção no ambiente doméstico e familiar",
                ),
                source(
                    "fam-violencia-contra-mae-idosa",
                    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=1186&cod_tema_inicial=1186&novaConsulta=true&tipo_pesquisa=T",
                    "STJ, Tema Repetitivo 1186",
                    "afirma que a idade não afasta a Lei Maria da Penha quando a violência doméstica é praticada contra mulher",
                ),
                source(
                    "fam-violencia-contra-mae-idosa",
                    "https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741.htm#art19",
                    "Estatuto da Pessoa Idosa, art. 19",
                    "define a notificação pelos serviços de saúde e os órgãos destinatários da comunicação",
                ),
                source(
                    "fam-violencia-contra-mae-idosa",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art22",
                    "Lei Maria da Penha, art. 22",
                    "fundamenta afastamento do lar, proibição de contato e outras restrições impostas ao agressor",
                ),
                source(
                    "fam-violencia-contra-mae-idosa",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art19",
                    "Lei Maria da Penha, art. 19",
                    "prevê concessão e duração das medidas protetivas de acordo com a situação de risco",
                ),
            ],
            ["violência patrimonial contra pessoa idosa", "medidas protetivas de urgência", "curatela e tomada de decisão apoiada"],
        ),
        build(
            "fam-agressor-arma-medida",
            "Agressor com arma: providências na medida protetiva",
            "Veja como a Justiça pode apreender a arma, suspender a posse ou restringir o porte do agressor e por que CAC não se confunde com porte funcional.",
            "Arma do agressor: apreensão, posse e porte na proteção da vítima",
            "A existência ou o acesso fácil a uma arma aumenta a urgência da avaliação de risco. A Lei Maria da Penha prevê mais do que uma comunicação administrativa: o juiz pode ordenar apreensão imediata e impor restrições sobre posse ou porte, conforme os dados apresentados.\n\nA vítima não deve tentar localizar, manusear ou retirar a arma. Informar com precisão onde ela costuma ficar, quem é o titular e se pertence a uma instituição permite que polícia, Judiciário e órgão de controle atuem sem criar um confronto adicional.",
            [
                section(
                    "Apreensão imediata e restrição são providências diferentes",
                    "O art. 18, IV, autoriza o juiz a determinar a apreensão imediata da arma sob posse do agressor. Já o art. 22, I, permite suspender a posse ou restringir o porte, com comunicação ao órgão competente. A polícia também deve verificar se há registro de posse ou porte e juntar essa informação ao pedido protetivo.\n\nA decisão precisa dizer quais medidas foram adotadas. A simples notícia de que existe arma não prova que ela já foi recolhida; por isso, número do processo, cópia da ordem e confirmação do cumprimento são dados relevantes para o plano de segurança.",
                ),
                section(
                    "Arma funcional exige contato com a instituição responsável",
                    "Quando o agressor é policial, militar, agente penitenciário ou exerce outra função com armamento institucional, o porte funcional não deixa a ordem judicial sem efeito. A instituição ou corporação responsável deve ser comunicada para cumprir a restrição e controlar a arma de serviço. Esse regime não se confunde com o acervo particular.\n\nSe for seguro, a vítima pode informar cargo, unidade, matrícula conhecida, tipo de arma e mensagens em que houve exibição ou ameaça. Não é necessário obter fotografia do armamento se isso exigir aproximação ou acesso clandestino.",
                ),
                section(
                    "Registro de CAC não equivale a porte profissional",
                    "Colecionador, atirador desportivo ou caçador possui categoria regulatória própria; ser CAC não significa portar arma em razão de profissão. Desde julho de 2025, a Polícia Federal passou a responder pelas atualizações do cadastro de armas de CAC no Sinarm. O certificado, o número de série e o local habitual de guarda podem ajudar a individualizar o acervo, quando já forem conhecidos.\n\nA ordem judicial pode alcançar essas armas, mas o cumprimento deve passar pelas autoridades. Eventual guia de tráfego tampouco autoriza desrespeitar a proibição de contato ou outra restrição protetiva.",
                ),
                section(
                    "Arma escondida ou irregular deve ser comunicada, não enfrentada",
                    "Uma ordem de apreensão não elimina fisicamente o risco antes do cumprimento e não impede que o agressor tente obter acesso ilícito a outro armamento. Se a vítima souber de arma oculta, sem registro ou mantida na casa de terceiro, deve transmitir a informação à polícia com o máximo de detalhes que já possua, sem investigar por conta própria.\n\nConsidere um agressor que trabalha armado e também mantém rifles registrados como CAC. O pedido deve separar o armamento funcional do acervo particular, mencionar ameaças concretas e indicar os órgãos responsáveis. Essa descrição permite ordens dirigidas a cada registro e reduz lacunas na execução.",
                ),
            ],
            [
                faq(
                    "A medida protetiva sempre apreende a arma automaticamente?",
                    "Não. A apreensão e a suspensão ou restrição dependem da decisão e de seu cumprimento. A vítima deve relatar o acesso à arma para que o risco seja avaliado e a providência adequada seja expressamente determinada.",
                )
            ],
            [
                source(
                    "fam-agressor-arma-medida",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art18",
                    "Lei Maria da Penha, art. 18, IV",
                    "autoriza a determinação judicial de apreensão imediata da arma sob posse do agressor",
                ),
                source(
                    "fam-agressor-arma-medida",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art22",
                    "Lei Maria da Penha, art. 22, I e § 2º",
                    "fundamenta suspensão da posse, restrição do porte e comunicação à instituição responsável",
                ),
                source(
                    "fam-agressor-arma-medida",
                    "https://www.gov.br/pf/pt-br/assuntos/armas/dados-abertos/registros-de-armas-de-fogo-cac",
                    "Polícia Federal, registros de armas de fogo CAC",
                    "comprova que os registros de CAC estão no Sinarm-CAC e que a PF responde por suas atualizações desde julho de 2025",
                ),
            ],
            ["medidas protetivas de urgência", "descumprimento de medida protetiva", "avaliação de risco"],
        ),
        build(
            "fam-vitima-reatou-medida-cai",
            "Reconciliação revoga a medida protetiva?",
            "Reatar não encerra a medida protetiva por si só. Entenda o Tema 1249 do STJ, a revisão judicial e o efeito do consentimento no caso concreto.",
            "O que acontece com a medida protetiva quando há reaproximação",
            "A reconciliação não apaga automaticamente uma medida protetiva. A ordem continua formalmente vigente até que o juízo a reveja, e sua duração depende da persistência do risco, não do andamento de inquérito ou ação penal. A vítima também não é destinatária da proibição imposta ao agressor.\n\nIsso não torna recomendável resolver a situação apenas por mensagens ou encontros informais. Consentimento, coação, risco atual e alcance da decisão podem ser discutidos depois, inclusive no processo criminal por descumprimento.",
            [
                section(
                    "O Tema 1249 vincula a medida à situação de risco",
                    "O STJ definiu no Tema 1249 que as medidas têm natureza de tutela inibitória, devem ser fixadas sem prazo predeterminado e permanecem enquanto existir risco. Arquivamento, absolvição ou fim de outro processo não as extinguem necessariamente. A reavaliação pode ocorrer por provocação da vítima, do suposto agressor ou por iniciativa do juiz quando houver indícios concretos de que a proteção perdeu sua finalidade.\n\nAntes de revogar, o juízo deve assegurar contraditório, com prévia oitiva da vítima e do suposto agressor. A ofendida precisa ser comunicada se a medida for encerrada; uma conversa privada entre o casal não substitui essa decisão.",
                ),
                section(
                    "Consentimento pode influir no crime sem cancelar a ordem",
                    "A restrição judicial recai sobre o agressor, de modo que a mulher não pratica o art. 24-A por se aproximar. No Informativo 785, o STJ reconheceu que consentimento livre e inequívoco da vítima pode afastar a tipicidade do contato no caso concreto. Essa análise não vale quando a anuência resulta de ameaça, pressão, manipulação ou coação.\n\nA distinção é importante: uma possível absolvição penal por ausência de desobediência dolosa não significa que a medida tenha sido revogada. Até nova decisão, autoridades podem tratar a ordem como vigente, e novos contatos não consentidos continuam relevantes.",
                ),
                section(
                    "Como pedir uma revisão sem depender de acordo informal",
                    "A vítima pode procurar advogado, Defensoria Pública ou o próprio canal indicado pelo tribunal para informar a reaproximação e pedir revisão total ou parcial. Deve levar número do processo, cópia da decisão, relato do contexto atual e informação sobre episódios posteriores. O juízo pode manter proibição de contato, alterar distância, preservar proteção dos filhos ou revogar medidas que já não se justifiquem.\n\nSe o agressor fizer o pedido, a vítima deve ser ouvida antes do encerramento. Não precisa entregar intimação a ele nem encontrá-lo para produzir uma declaração conjunta.",
                ),
                section(
                    "Reconciliação aparente pode esconder pressão ou novo risco",
                    "Imagine que a vítima aceite uma conversa porque o agressor ameaça retirar ajuda financeira aos filhos. Esse assentimento não deve ser tratado como livre sem examinar a pressão. Mensagens, áudios lícitos, testemunhas e relatos à equipe de atendimento ajudam a mostrar como a reaproximação ocorreu.\n\nEm outro caso, o casal pode reconstruir voluntariamente o convívio e desejar retirar apenas a proibição de contato. Ainda assim, a via adequada é apresentar o novo quadro ao juízo. Se houver perigo imediato durante a tentativa de reconciliação, o foco volta a ser a segurança e o acionamento policial, não a formalização da revogação.",
                ),
            ],
            [
                faq(
                    "O agressor pode pedir sozinho o fim da medida?",
                    "Ele pode requerer a reavaliação, mas não revogar a ordem por conta própria. O juiz deve examinar a cessação do risco, ouvir as partes e comunicar eventual extinção à vítima.",
                )
            ],
            [
                source(
                    "fam-vitima-reatou-medida-cai",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art19",
                    "Lei Maria da Penha, art. 19",
                    "vincula concessão, revisão e duração das medidas protetivas à necessidade de proteção",
                ),
                source(
                    "fam-vitima-reatou-medida-cai",
                    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=1249&cod_tema_inicial=1249&novaConsulta=true&tipo_pesquisa=T",
                    "STJ, Tema Repetitivo 1249",
                    "define duração indeterminada conforme o risco e contraditório antes da revogação",
                ),
                source(
                    "fam-vitima-reatou-medida-cai",
                    "https://processo.stj.jus.br/docs_internet/informativos/PDF/Inf0785.pdf",
                    "STJ, Informativo de Jurisprudência 785",
                    "registra o efeito do consentimento livre da vítima na tipicidade do descumprimento no caso concreto",
                ),
                source(
                    "fam-vitima-reatou-medida-cai",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art22",
                    "Lei Maria da Penha, art. 22",
                    "identifica as obrigações protetivas impostas ao agressor",
                ),
            ],
            ["medidas protetivas de urgência", "descumprimento de medida protetiva", "assistência jurídica à vítima"],
        ),
        build(
            "fam-sigilo-endereco-vitima",
            "Como pedir proteção do endereço da vítima no processo",
            "A lei torna o nome sigiloso, mas não esconde automaticamente o endereço da contraparte. Saiba distinguir publicidade, acesso aos autos e pedido específico.",
            "Proteção do endereço da vítima exige uma medida específica",
            "O sigilo do nome, o segredo de justiça e a restrição de acesso ao endereço são mecanismos diferentes. Confundi-los pode criar uma falsa sensação de segurança: retirar o processo da consulta pública não significa necessariamente impedir que a contraparte e sua defesa vejam todos os documentos.\n\nA vítima que mudou de residência precisa avisar desde o primeiro atendimento que revelar o local pode aumentar o risco. O pedido deve indicar qual dado necessita de proteção e por quê, sem presumir que uma regra geral já resolveu o problema.",
            [
                section(
                    "O art. 17-A protege o nome, não todos os dados",
                    "Desde a Lei 14.857/2024, o nome da ofendida fica sob sigilo nos processos que apuram crimes de violência doméstica. O parágrafo único do art. 17-A é expresso ao dizer que essa proteção não alcança os demais dados do processo. Portanto, não há sigilo automático do endereço residencial com base nesse dispositivo.\n\nA identificação da mulher deixa de aparecer nas consultas públicas abrangidas pela regra, mas endereço, telefone e documentos sensíveis exigem análise própria. O título de uma petição ou a marca de segredo no processo não devem ser tratados como garantia de ocultação perante o agressor.",
                ),
                section(
                    "Segredo de justiça limita o público, mas as partes acessam os autos",
                    "O art. 189 do Código de Processo Civil permite segredo de justiça quando a intimidade precisa ser preservada. Esse regime impede a consulta pública, mas a contraparte e sua defesa podem acessar os autos. No processo penal, o art. 201, § 6º, autoriza o juiz a restringir dados, depoimentos e outras informações para preservar intimidade, vida privada, honra e imagem da vítima.\n\nOcultar o endereço do agressor depende, assim, de decisão específica e compatível com o direito de defesa. A prática varia entre tribunais: o dado pode ser juntado em documento restrito, cadastro apartado ou outro fluxo definido pelo juízo, sem promessa de bloqueio absoluto.",
                ),
                section(
                    "Dados escolares possuem proteção legal própria",
                    "A Lei Maria da Penha assegura prioridade para matricular ou transferir dependentes para escola próxima do novo domicílio mediante prova da ocorrência ou do processo em curso. O art. 9º, § 8º, determina sigilo dos dados da ofendida e dos dependentes usados nessa matrícula ou transferência, com acesso reservado ao juiz, ao Ministério Público e aos órgãos públicos competentes.\n\nEssa regra protege o cadastro escolar, mas não substitui o pedido de restrição no processo nem controla informações divulgadas por familiares, redes sociais ou aplicativos da escola.",
                ),
                section(
                    "Como formular o pedido e reduzir exposição desnecessária",
                    "No registro policial ou na primeira petição, a vítima pode pedir que o endereço seguro não apareça na narrativa acessível e seja entregue pelo canal restrito indicado pelo órgão. Convém informar decisão protetiva, ameaças de localização, perseguição anterior e presença de filhos, além de fornecer telefone seguro para contato. Depois, deve confirmar o que foi efetivamente deferido e como receberá intimações.\n\nPor exemplo, uma mulher acolhida temporariamente na casa de parentes não deve presumir que o segredo de justiça esconderá esse local. Ela pode apresentar pedido fundamentado para apartar o endereço e orientar escola e rede de apoio a não compartilhá-lo, enquanto evita publicar localização. Em risco imediato, a prioridade é acionar a polícia.",
                ),
            ],
            [
                faq(
                    "O advogado do agressor nunca verá o endereço protegido?",
                    "Não se pode garantir isso de forma geral. O alcance da restrição depende da decisão judicial e da compatibilização com a defesa; segredo de justiça, sozinho, não exclui o acesso dos procuradores das partes.",
                )
            ],
            [
                source(
                    "fam-sigilo-endereco-vitima",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art17a",
                    "Lei Maria da Penha, art. 17-A",
                    "estabelece o sigilo do nome e delimita que a regra não alcança os demais dados processuais",
                ),
                source(
                    "fam-sigilo-endereco-vitima",
                    "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art189",
                    "Código de Processo Civil, art. 189",
                    "disciplina o segredo de justiça e o acesso das partes e procuradores aos autos",
                ),
                source(
                    "fam-sigilo-endereco-vitima",
                    "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm#art201",
                    "Código de Processo Penal, art. 201, § 6º",
                    "autoriza providências judiciais específicas para preservar dados e intimidade da vítima",
                ),
                source(
                    "fam-sigilo-endereco-vitima",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art9",
                    "Lei Maria da Penha, art. 9º, §§ 7º e 8º",
                    "protege os dados usados na matrícula ou transferência escolar dos dependentes",
                ),
            ],
            ["medidas protetivas de urgência", "segredo de justiça", "transferência escolar protegida"],
        ),
        build(
            "fam-defensoria-vitima-atendimento",
            "Vítima de violência doméstica tem advogado gratuito?",
            "A Lei Maria da Penha garante acesso à Defensoria, mas o patrocínio gratuito segue critérios legais e institucionais. Entenda a proteção inicial.",
            "Defensoria e acompanhamento jurídico da vítima de violência doméstica",
            "A mulher pode pedir medida protetiva sem contratar advogado e tem direito a atendimento específico e humanizado. Quando o processo avança, a Lei Maria da Penha prevê acompanhamento jurídico, que pode ser prestado pela Defensoria Pública se estiverem presentes os critérios da instituição competente.\n\nAcesso ao serviço não é sinônimo de dispensa federal e universal de qualquer análise econômica ou jurídica. Ao mesmo tempo, a falta imediata de comprovante de renda não deve impedir que uma situação urgente seja levada à polícia e ao Judiciário.",
            [
                section(
                    "O pedido inicial de proteção não exige advogado",
                    "O art. 27 determina acompanhamento por advogado nos atos processuais cíveis e criminais, mas ressalva o pedido de medida protetiva previsto no art. 19. A própria ofendida pode formulá-lo e a autoridade policial encaminha o expediente ao juiz. Essa exceção permite resposta urgente antes de resolver quem fará a representação nos atos seguintes.\n\nSe houver audiência, recurso, divórcio, alimentos ou atuação como assistente de acusação, a necessidade de acompanhamento deve ser verificada. Número da ocorrência e do processo ajudam a Defensoria ou o advogado a localizar as decisões já proferidas.",
                ),
                section(
                    "O que significa acesso à Defensoria nos termos da lei",
                    "O art. 28 assegura a toda mulher em situação de violência doméstica acesso à Defensoria Pública ou à assistência judiciária gratuita, em sede policial e judicial. A própria norma usa a expressão nos termos da lei. A Lei Complementar 80 atribui à Defensoria orientação e defesa integral e gratuita dos necessitados, além da proteção de grupos vulneráveis.\n\nNa prática, a unidade competente aplica seus critérios institucionais, que podem considerar insuficiência de recursos e vulnerabilidade jurídica. Por isso, a página não deve prometer patrocínio gratuito irrestrito nem concluir que renda, patrimônio e possibilidade de contratar nunca serão avaliados.",
                ),
                section(
                    "Documentos úteis para o primeiro atendimento",
                    "Quando estiverem acessíveis sem risco, leve documento de identificação, comprovante de residência seguro, número do boletim, decisão protetiva, intimações e provas como mensagens, fotografias e prontuários. A Defensoria pode pedir comprovantes de renda, despesas familiares ou patrimônio para analisar a elegibilidade. A ausência de uma peça não autoriza ignorar emergência; explique o que ficou retido pelo agressor ou não pôde ser obtido.\n\nUma mãe que saiu de casa sem carteira de trabalho, por exemplo, pode apresentar os protocolos disponíveis e relatar a retenção dos documentos. A equipe orientará o complemento necessário e as providências que não podem esperar.",
                ),
                section(
                    "Se a Defensoria não assumir toda a demanda",
                    "A decisão institucional de não patrocinar um caso não elimina o direito de pedir proteção nem impede orientação sobre outros canais. Conforme o local, pode haver assistência judiciária conveniada, nomeação prevista em lei ou contratação particular. Essas rotas possuem regras próprias e não devem ser apresentadas como garantia de gratuidade.\n\nTambém é possível que a Defensoria atue em uma medida urgente e outro profissional cuide de questão patrimonial ou de família, segundo atribuições e critérios locais. O importante é identificar quem representa a vítima em cada processo e manter os contatos atualizados sem divulgar endereço inseguro.",
                ),
            ],
            [
                faq(
                    "A vítima precisa esperar a análise financeira para pedir proteção?",
                    "Não. O requerimento inicial de medida protetiva pode ser feito sem advogado. A análise de elegibilidade diz respeito ao patrocínio jurídico pela Defensoria e não autoriza adiar providência policial ou judicial urgente.",
                )
            ],
            [
                source(
                    "fam-defensoria-vitima-atendimento",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art27",
                    "Lei Maria da Penha, art. 27",
                    "prevê acompanhamento jurídico nos atos processuais e ressalva o pedido inicial de medida protetiva",
                ),
                source(
                    "fam-defensoria-vitima-atendimento",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art28",
                    "Lei Maria da Penha, art. 28",
                    "garante acesso humanizado à Defensoria ou assistência judiciária gratuita nos termos legais",
                ),
                source(
                    "fam-defensoria-vitima-atendimento",
                    "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp80.htm#art1",
                    "Lei Complementar 80/1994, arts. 1º e 4º",
                    "define a atuação gratuita da Defensoria em favor dos necessitados e de grupos vulneráveis",
                ),
            ],
            ["medidas protetivas de urgência", "Defensoria Pública", "assistência de acusação"],
        ),
        build(
            "fam-crime-perseguicao-stalking",
            "Crime de perseguição: conduta, prova e representação",
            "Stalking exige perseguição reiterada. Veja como documentar os episódios e o prazo atual de 12 meses no contexto de violência doméstica contra a mulher.",
            "Quando a perseguição reiterada configura crime e como representar",
            "Mensagens repetidas, vigilância da rotina, aparecimentos não combinados e monitoramento por terceiros podem configurar perseguição quando invadem a liberdade ou a privacidade da vítima. Desde 2021, o art. 147-A do Código Penal trata essa conduta como crime próprio, sem exigir agressão física anterior.\n\nUm episódio isolado pode ser grave e justificar outra resposta, mas o stalking exige reiteração. Organizar a sequência dos fatos e observar o prazo de representação evita reduzir o caso a uma coleção de capturas de tela sem contexto.",
            [
                section(
                    "Reiteração e invasão da liberdade são elementos centrais",
                    "O art. 147-A descreve a perseguição reiterada, por qualquer meio, que ameaça a integridade física ou psicológica, restringe locomoção ou invade e perturba liberdade ou privacidade. Telefonar uma vez após o término, sem ameaça ou invasão relevante, não basta por si só. Já seguir a vítima, criar perfis para contatá-la depois de bloqueios e aparecer repetidamente em seu trabalho pode revelar o padrão exigido.\n\nQuando o autor é ex-companheiro ou pessoa com quem houve relação íntima de afeto, os mesmos fatos podem integrar violência doméstica e fundamentar medida protetiva, sem que um enquadramento apague o outro.",
                ),
                section(
                    "O prazo doméstico passou a ser de doze meses em 2026",
                    "O crime de perseguição procede mediante representação. A Lei 15.438/2026 criou regra especial para crimes praticados em violência doméstica e familiar contra a mulher: a ofendida tem doze meses, contados do dia em que soube quem é o autor, para exercer o direito de queixa ou representação. A mudança entrou em vigor em 19 de junho de 2026.\n\nFora desse contexto especial, permanece a regra geral de seis meses, salvo outra norma aplicável. Não é prudente aguardar o fim do prazo: registrar e manifestar claramente o desejo de responsabilização reduz discussão futura sobre decadência.",
                ),
                section(
                    "Uma linha do tempo vale mais que imagens soltas",
                    "Preserve mensagens originais, links, cabeçalhos de e-mail, áudios recebidos, registros de chamadas e vídeos de câmeras, sem editar os arquivos. Anote data, local, meio usado, testemunhas e efeito sobre a rotina. Se um estabelecimento possui gravação, peça a preservação rapidamente, pois o sistema pode sobrescrever as imagens.\n\nImagine que o ex-parceiro envie mensagens por números diferentes, espere na saída do trabalho e peça a amigos informações sobre a vítima. A tabela cronológica permite mostrar reiteração e relacionar cada arquivo ao episódio correspondente, em vez de apresentar apenas uma captura sem origem.",
                ),
                section(
                    "Medida protetiva e denúncia atendem finalidades distintas",
                    "A representação viabiliza a persecução do crime; a medida protetiva busca interromper o risco. A vítima pode relatar perseguição na delegacia e pedir proibição de aproximação e contato, conforme o caso. Perigo atual, presença de arma ou tentativa de invasão exigem acionamento emergencial, sem esperar completar o dossiê.\n\nContato incômodo, mas não reiterado ou incapaz de atingir os elementos do art. 147-A, pode não configurar stalking. Isso não torna a conduta aceitável: ameaça, invasão de dispositivo, divulgação íntima e descumprimento de ordem possuem enquadramentos próprios que devem ser avaliados pelos fatos.",
                ),
            ],
            [
                faq(
                    "É preciso registrar uma ocorrência para cada episódio?",
                    "Não necessariamente. Um registro pode narrar a sequência e reunir as evidências, mas fatos posteriores relevantes devem ser comunicados com referência ao protocolo anterior para manter a cronologia atualizada.",
                )
            ],
            [
                source(
                    "fam-crime-perseguicao-stalking",
                    "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm#art147a",
                    "Código Penal, art. 147-A",
                    "define os elementos do crime de perseguição reiterada e a necessidade de representação",
                ),
                source(
                    "fam-crime-perseguicao-stalking",
                    "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14132.htm",
                    "Lei 14.132/2021",
                    "instituiu o crime de perseguição e revogou a antiga contravenção de perturbação da tranquilidade",
                ),
                source(
                    "fam-crime-perseguicao-stalking",
                    "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15438.htm",
                    "Lei 15.438/2026",
                    "ampliou para doze meses o prazo de representação ou queixa na violência doméstica contra a mulher",
                ),
                source(
                    "fam-crime-perseguicao-stalking",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art19",
                    "Lei Maria da Penha, art. 19",
                    "fundamenta a concessão de medidas protetivas de acordo com o risco relatado",
                ),
            ],
            ["medidas protetivas de urgência", "violência digital", "preservação de provas eletrônicas"],
        ),
        build(
            "fam-violencia-vicaria",
            "Violência vicária: definição legal e proteção da família",
            "Desde 2026, a Lei Maria da Penha define violência vicária. Entenda quem pode ser vítima direta, como diferenciar conflito familiar e quais provas importam.",
            "Violência vicária agora tem definição expressa na Lei Maria da Penha",
            "Desde abril de 2026, a violência vicária está expressamente definida no art. 7º, VI, da Lei Maria da Penha. Ela ocorre quando alguém pratica violência contra pessoa ligada à mulher com o objetivo de atingi-la. Filhos são vítimas frequentes, mas a lei também alcança outros familiares, dependentes e integrantes da rede de apoio.\n\nO conceito não deve ser usado como rótulo para qualquer desentendimento sobre guarda. É preciso identificar a violência dirigida à pessoa intermediária e a finalidade de causar sofrimento, punição ou controle à mulher.",
            [
                section(
                    "Quem a Lei 15.384/2026 inclui na proteção vicária",
                    "A Lei 15.384/2026 acrescentou o inciso VI ao art. 7º. A definição da violência vicária abrange conduta contra pessoa com vínculo familiar, de dependência, guarda ou apoio em relação à mulher, praticada para causar dano e atingi-la. O texto legal menciona descendente, ascendente, dependente, enteado, parente, pessoa sob responsabilidade direta e integrante da rede de apoio.\n\nUma ameaça contra a mãe idosa da ofendida para obrigá-la a retomar o relacionamento, por exemplo, pode integrar esse conceito. O ato contra a terceira pessoa precisa ser examinado por sua própria gravidade, além do dano pretendido contra a mulher.",
                ),
                section(
                    "A criança exposta também é vítima em nome próprio",
                    "Quando o ato recai sobre uma criança, a Lei 13.431/2017 oferece proteção adicional. Seu art. 4º trata como violência psicológica a exposição direta ou indireta a crime violento contra familiar, especialmente quando a criança o testemunha. Ela não é simples instrumento de prova do sofrimento materno: possui direitos próprios de acolhimento e proteção.\n\nPerguntas repetidas pela família podem causar revitimização e contaminar o relato. A escuta especializada, definida no art. 7º dessa lei, deve limitar a entrevista ao necessário e ser conduzida por profissional da rede de proteção.",
                ),
                section(
                    "Registros devem mostrar atos, contexto e destinatários",
                    "Mensagens que ameacem filhos ou parentes, comunicações da escola, prontuários, testemunhas, decisões de convivência e registros de entrega ajudam a reconstruir o padrão. Anote quem sofreu o ato, o que foi exigido da mulher e como os fatos se conectam. Não exponha a criança a gravações clandestinas dirigidas nem peça que repita a narrativa para várias pessoas.\n\nEm urgência, Conselho Tutelar, polícia, Ministério Público e juízo competente podem receber a informação conforme a vítima direta e a medida necessária. Pedido sobre convivência deve descrever risco concreto, e não apenas usar a expressão violência vicária.",
                ),
                section(
                    "Atraso de visita e divergência parental não bastam sozinhos",
                    "Um atraso ocasional, discordância escolar ou falha de comunicação após a separação não configura automaticamente violência vicária. A lei exige violência contra pessoa do círculo protegido e finalidade de atingir a mulher. Reiteração, ameaça, lesão e uso deliberado do sofrimento de terceiro ajudam a diferenciar o caso de conflito parental comum.\n\nConsidere o pai que ameaça ferir o filho caso a mãe não retire uma denúncia: há ato dirigido à criança e finalidade declarada de controlar a mulher. Isso é diferente de uma entrega tardia sem ameaça ou outro elemento. A distinção protege vítimas reais e evita transformar toda disputa de rotina em acusação de violência.",
                ),
            ],
            [
                faq(
                    "Violência vicária exige agressão física?",
                    "Não necessariamente. A lei fala em qualquer forma de violência contra a pessoa ligada à mulher. A natureza física, psicológica, sexual, moral ou patrimonial deve ser identificada nos fatos, sem presumir o enquadramento apenas pelo conflito familiar.",
                )
            ],
            [
                source(
                    "fam-violencia-vicaria",
                    "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15384.htm",
                    "Lei 15.384/2026",
                    "incluiu a violência vicária entre as formas de violência doméstica e definiu seu alcance pessoal e finalístico",
                ),
                source(
                    "fam-violencia-vicaria",
                    "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm#art7",
                    "Lei Maria da Penha, art. 7º, VI",
                    "traz a definição vigente de violência vicária contra familiares, dependentes e rede de apoio da mulher",
                ),
                source(
                    "fam-violencia-vicaria",
                    "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13431.htm#art4",
                    "Lei 13.431/2017, art. 4º",
                    "protege a criança exposta direta ou indiretamente a crime violento contra familiar",
                ),
                source(
                    "fam-violencia-vicaria",
                    "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13431.htm#art7",
                    "Lei 13.431/2017, art. 7º",
                    "define escuta especializada e limita o relato ao necessário para sua finalidade protetiva",
                ),
            ],
            ["guarda e convivência dos filhos", "escuta especializada", "medidas protetivas de urgência"],
        ),
    ]

    expected_ids = [page["intent_id"] for page in originals]
    actual_ids = [page["intent_id"] for page in pages]
    if actual_ids != expected_ids or len(set(actual_ids)) != 10:
        raise SystemExit(f"ordem ou cobertura de intents invalida: {actual_ids}")

    bands = {"verbete": (350, 700), "pergunta": (400, 800)}
    page_types = {
        "fam-juizado-violencia-domestica": "verbete",
        "fam-indenizacao-vitima-violencia": "pergunta",
        "fam-vitima-estrangeira-direitos": "pergunta",
        "fam-violencia-contra-mae-idosa": "pergunta",
        "fam-agressor-arma-medida": "pergunta",
        "fam-vitima-reatou-medida-cai": "pergunta",
        "fam-sigilo-endereco-vitima": "pergunta",
        "fam-defensoria-vitima-atendimento": "pergunta",
        "fam-crime-perseguicao-stalking": "verbete",
        "fam-violencia-vicaria": "verbete",
    }
    for page in pages:
        if not 20 <= len(page["title"]) <= 65:
            raise SystemExit(f"title fora da faixa: {page['intent_id']}")
        if not 70 <= len(page["meta_description"]) <= 160:
            raise SystemExit(f"meta fora da faixa: {page['intent_id']}")
        if not 2 <= len(page["official_sources"]) <= 5:
            raise SystemExit(f"fontes fora da faixa: {page['intent_id']}")
        if page["word_count"] != body_word_count(page):
            raise SystemExit(f"word_count incoerente: {page['intent_id']}")
        minimum, maximum = bands[page_types[page["intent_id"]]]
        if not minimum <= page["word_count"] <= maximum:
            raise SystemExit(
                f"word_count fora da banda: {page['intent_id']}={page['word_count']}"
            )
        for item in page["official_sources"]:
            was_present = item["url"] in source_by_id[page["intent_id"]]
            has_evidence = "verified_at" in item or "http_status" in item
            if not was_present and has_evidence:
                raise SystemExit(f"fonte nova recebeu metadata: {item['url']}")

    payload = "".join(json.dumps(page, ensure_ascii=False) + "\n" for page in pages)
    descriptor, candidate_name = tempfile.mkstemp(
        prefix=".familia-16.", suffix=".candidate", dir=TARGET.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        candidate = Path(candidate_name)
        parsed = [json.loads(line) for line in candidate.read_text(encoding="utf-8").splitlines()]
        if parsed != pages:
            raise SystemExit("readback do candidato divergiu")
        os.replace(candidate, TARGET)
    finally:
        candidate = Path(candidate_name)
        if candidate.exists():
            candidate.unlink()

    print(file_sha256(TARGET))
    for page in pages:
        print(f"{page['intent_id']} word_count={page['word_count']} sources={len(page['official_sources'])}")


if __name__ == "__main__":
    main()
