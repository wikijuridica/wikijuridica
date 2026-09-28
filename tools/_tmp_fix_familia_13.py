#!/usr/bin/env python3
"""Revisão jurídico-editorial integral de familia-13 com promoção CAS atômica."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/editorial/v2_pages/familia-13.jsonl"
INITIAL_SHA256 = "04d2c1e8ac069060c36cdd1c9e23552ff65d2607c5f72c956ce9049477c20ff7"
EXPECTED_SHA256 = "97985aa2600311315e69cdaa66c8cfd974d7cf9c01e5551b15cb280cf55ee87a"

BANDS = {
    "guia_problema": (700, 1400),
    "pergunta": (400, 800),
    "procedimento": (500, 1000),
    "verbete": (350, 700),
}

PAGE_TYPES = {
    "fam-investigacao-paternidade": "guia_problema",
    "fam-recusa-dna-presuncao": "pergunta",
    "fam-dna-pai-falecido": "guia_problema",
    "fam-paternidade-post-mortem-heranca": "guia_problema",
    "fam-reconhecer-filho-cartorio": "procedimento",
    "fam-reconhecimento-filho-maior-consentimento": "pergunta",
    "fam-paternidade-socioafetiva": "verbete",
    "fam-registrar-socioafetivo-cartorio": "procedimento",
    "fam-multiparentalidade": "verbete",
    "fam-incluir-pai-biologico-multiparentalidade": "guia_problema",
    "fam-anular-registro-paternidade": "guia_problema",
    "fam-adocao-a-brasileira": "verbete",
    "fam-pai-se-recusa-registrar": "guia_problema",
    "fam-direito-origem-genetica": "pergunta",
    "fam-abandono-afetivo-indenizacao": "guia_problema",
    "fam-dna-gratuito": "pergunta",
    "fam-retificar-certidao-nascimento": "procedimento",
    "fam-inseminacao-caseira-paternidade": "pergunta",
    "fam-registro-reproducao-assistida": "pergunta",
    "fam-barriga-solidaria-registro": "pergunta",
    "fam-adocao-unilateral-enteado": "guia_problema",
    "fam-alimentos-com-investigacao": "pergunta",
}


def sha256(path: Path) -> str:
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
    for item in page["sections"]:
        parts.extend((item["heading"], item["text"]))
    for item in page["faq"]:
        parts.extend((item["q"], item["a"]))
    return sum(len(words(part)) for part in parts)


def section(heading: str, text: str) -> dict:
    return {"heading": heading, "text": text}


def faq(question: str, answer: str) -> dict:
    return {"q": question, "a": answer}


def main() -> None:
    if sha256(TARGET) != EXPECTED_SHA256:
        raise SystemExit("familia-13 mudou desde a delegação; promoção recusada")

    originals = [json.loads(line) for line in TARGET.read_text(encoding="utf-8").splitlines()]
    original_by_id = {page["intent_id"]: page for page in originals}
    source_by_id = {
        page["intent_id"]: {item["url"]: item for item in page["official_sources"]}
        for page in originals
    }

    def source(intent_id: str, url: str, name: str, anchor_claim: str) -> dict:
        item = {"url": url, "name": name, "anchor_claim": anchor_claim}
        previous = source_by_id[intent_id].get(url)
        if previous is not None:
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
            "lane": original_by_id[intent_id]["lane"],
            "word_count": 0,
        }
        page["word_count"] = body_word_count(page)
        return page

    pages = [
        build(
            "fam-investigacao-paternidade",
            "Investigação de paternidade: provas e efeitos",
            "Entenda quem pode pedir o reconhecimento de paternidade, como o DNA é avaliado e quais decisões podem tratar de registro, alimentos e herança.",
            "Como funciona a investigação judicial de paternidade",
            "A ausência do nome do pai no registro não impede que o filho busque o reconhecimento em qualquer fase da vida. A investigação de paternidade é uma ação de estado: procura definir juridicamente a filiação por exame genético e por outros elementos lícitos, sem transformar a narrativa de nenhuma das partes em resultado antecipado. A estratégia muda quando o investigado morreu, quando já existe outro vínculo paterno ou quando também se pedem alimentos.",
            [
                section(
                    "Quem é titular da ação e por que ela não prescreve",
                    "O artigo 1606 do Código Civil atribui ao filho, enquanto viver, a ação de prova da filiação. Se ele morrer menor ou incapaz, a pretensão passa aos herdeiros; se a ação já tiver sido iniciada pelo filho, os herdeiros podem continuá-la, ressalvada a hipótese legal de processo extinto. O estado de filiação é imprescritível, mas pretensões patrimoniais associadas podem ter prazos próprios. Petição de herança, por exemplo, não se torna imprescritível apenas porque depende do reconhecimento de paternidade.\n\nQuando o filho é criança ou adolescente, ele atua representado ou assistido conforme a idade. Ministério Público e Defensoria Pública têm funções institucionais próprias, mas a forma concreta de representação deve ser conferida no caso, sem pressupor que todo procedimento começará do mesmo modo.",
                ),
                section(
                    "DNA é central, mas integra um conjunto de provas",
                    "O exame de DNA costuma oferecer a evidência técnica mais direta. O laudo deve identificar as amostras, a cadeia de coleta e a conclusão estatística, e será apreciado com os demais elementos do processo. Mensagens, fotografias, testemunhas do relacionamento no período provável da concepção e registros de convivência podem contextualizar o pedido. Nenhum percentual deve ser anunciado antes da perícia nem substituído por teste doméstico sem controle de identidade.\n\nA recusa injustificada ao exame não equivale a confissão absoluta. Ela induz presunção relativa, que o juiz avalia com o restante da prova. Se o suposto pai faleceu, o polo passivo e a perícia indireta seguem regras diferentes, com participação dos herdeiros e possível exame de parentes consanguíneos.",
                ),
                section(
                    "Competência territorial depende da configuração do pedido",
                    "Não existe uma promessa universal de que a demanda tramitará no foro do pai ou no foro do filho. Domicílios, idade do investigante, cumulação com alimentos, regras do Código de Processo Civil e organização judiciária local podem alterar a competência. Antes do protocolo, é necessário identificar quem serão as partes, quais pedidos serão cumulados e se há processo sucessório ou registro anterior relacionado.\n\nO procedimento normalmente inclui petição inicial, citação válida, defesa, saneamento, produção de prova e sentença. Citação por edital é excepcional e exige tentativas adequadas de localização; sua simples conveniência não autoriza pular as buscas determinadas pelo juízo.",
                ),
                section(
                    "Alimentos podem ser discutidos na mesma demanda",
                    "O reconhecimento pode ser cumulado com alimentos. Uma tutela alimentar antes do resultado do DNA depende de decisão judicial e de indícios suficientes; não nasce automaticamente do ajuizamento. Ao reconhecer a paternidade na sentença de primeiro grau, o art. 7º da Lei 8.560/1992 determina a fixação de alimentos provisionais ou definitivos ao reconhecido que deles necessite. Julgada procedente a investigação, a Súmula 277 do STJ situa os alimentos desde a citação, matéria que exige cálculo conforme o título judicial.\n\nNecessidade de quem pede e possibilidade de quem paga continuam relevantes. Valores, forma de cobrança e eventual revisão não podem ser definidos em texto geral sem renda, despesas e decisão do processo.",
                ),
                section(
                    "A sentença modifica o estado de filiação e orienta o registro",
                    "A procedência declara a filiação e fornece ordem para a averbação no registro civil, com os dados que a decisão determinar. Direitos sucessórios decorrem da igualdade entre os filhos, mas a recuperação de herança já partilhada pode exigir petição de herança e análise de prescrição. Alimentos precisam ser fixados e quantificados; sobrenome e demais ajustes registrais devem observar o pedido, a decisão e as regras do registro civil.\n\nA improcedência pode decorrer de DNA excludente confiável ou de insuficiência do conjunto probatório. Falta de convivência, isoladamente, não prova ausência de vínculo biológico, assim como ajuda financeira isolada não prova filiação.",
                ),
                section(
                    "Organização documental sem promessa de resultado",
                    "Certidão de nascimento atualizada, dados disponíveis para localização, mensagens preservadas no formato original, fotografias contextualizadas e nomes de testemunhas formam um ponto de partida. Se já houve teste, devem ser guardados laudo completo e informações sobre coleta. Documentos não devem ser alterados nem obtidos por invasão de conta ou exposição da intimidade de terceiros.\n\nEm atendimento jurídico particular, a utilidade está em definir partes, competência, pedidos e prova antes do protocolo. A consulta pode começar por meios digitais, mas citação, perícia e comparecimentos seguem o que o juízo determinar, sem garantia de tramitação integral a distância.",
                ),
            ],
            [
                faq(
                    "A investigação pode ser proposta quando o filho já é adulto?",
                    "Sim. O estado de filiação pode ser investigado durante a vida do filho. Isso não elimina os prazos próprios de pedidos patrimoniais que venham a ser cumulados ou formulados depois.",
                )
            ],
            [
                source("fam-investigacao-paternidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1606", "Código Civil, art. 1.606", "define a titularidade da ação de prova da filiação e as hipóteses de sucessão processual"),
                source("fam-investigacao-paternidade", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm", "Lei 8.560/1992", "disciplina a investigação de paternidade e a fixação de alimentos quando a filiação é reconhecida"),
                source("fam-investigacao-paternidade", "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm", "Código de Processo Civil", "rege competência, citação, prova pericial e procedimento comum aplicáveis ao caso concreto"),
            ],
            ["recusa ao exame de DNA", "alimentos na investigação", "paternidade após a morte"],
        ),
        build(
            "fam-recusa-dna-presuncao",
            "Recusa ao DNA: alcance da presunção de paternidade",
            "Saiba por que a recusa injustificada ao exame de DNA gera presunção relativa, quais outras provas importam e como a Súmula 301 do STJ é aplicada.",
            "O que a recusa ao exame de DNA significa no processo",
            "O investigado não controla o desfecho da ação apenas deixando de comparecer ao exame. A recusa injustificada tem consequência probatória, mas não transforma a paternidade em verdade automática: a Súmula 301 do STJ estabelece presunção relativa, aberta à avaliação do conjunto de provas e à demonstração em sentido contrário.",
            [
                section(
                    "Presunção relativa não é resultado automático",
                    "Os arts. 231 e 232 do Código Civil permitem que a recusa a exame médico não favoreça quem a apresenta e seja suprida por outros meios de prova. Na investigação de paternidade, a Súmula 301 do STJ diz que a recusa do suposto pai ao DNA induz presunção juris tantum de paternidade. Isso significa que a recusa pesa contra ele, sem dispensar o juiz de examinar a coerência das alegações, testemunhos, documentos e demais circunstâncias.\n\nNão é tecnicamente correto dizer que o ônus simplesmente muda inteiro de lado. O autor continua responsável por apresentar os elementos constitutivos que estiverem ao seu alcance; o réu, por sua vez, deve enfrentar de modo concreto a prova e a presunção produzidas, em vez de se limitar a negar.",
                ),
                section(
                    "Ausência justificada e recusa são situações diferentes",
                    "Uma falta pontual por doença, erro de intimação ou impossibilidade comprovada pode levar à remarcação. A caracterização da recusa depende do histórico processual: ciência adequada, oportunidade real de coleta e ausência de justificativa aceita. O juízo registra essas ocorrências nos autos e pode determinar novas providências antes de valorar a conduta.\n\nTambém não cabe à parte declarar sozinha que houve recusa. Intimações, certidões do laboratório e decisões devem ser preservadas. Comparecimento tardio ou oferta de outro teste serão avaliados quanto à confiabilidade, à identificação das amostras e ao momento processual.",
                ),
                section(
                    "Quais provas acompanham a presunção",
                    "Mensagens do período da concepção, fotografias contextualizadas, depoimentos de quem conhecia o relacionamento e registros de apoio à gestante ou à criança podem compor o quadro. A inexistência de um desses itens não decide o processo isoladamente. Do mesmo modo, rumores, suposições sobre terceiros ou documentos sem origem verificável não substituem prova.\n\nQuando o suposto pai faleceu, a lei permite exame em parentes consanguíneos e estende à recusa injustificada deles uma presunção relativa a ser apreciada com as demais provas. Essa hipótese exige identificar corretamente todos os herdeiros e não deve ser confundida com a recusa pessoal do investigado vivo.",
                ),
                section(
                    "Como preparar a análise do caso",
                    "É útil reunir o cronograma das marcações, comprovantes de intimação disponíveis, justificativas apresentadas e toda a prova independente do relacionamento. Na advocacia particular, um profissional pode avaliar se o comportamento já foi formalmente caracterizado como recusa e quais medidas probatórias ainda são proporcionais. A orientação não deve prometer reconhecimento: a consequência da Súmula 301 continua relativa e depende dos autos.",
                ),
            ],
            [],
            [
                source("fam-recusa-dna-presuncao", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art232", "Código Civil, arts. 231 e 232", "rege os efeitos probatórios da recusa a exame médico necessário"),
                source("fam-recusa-dna-presuncao", "https://www.stj.jus.br/docs_internet/revista/eletronica/stj-revista-sumulas-2011_23_capSumula301.pdf", "STJ, Súmula 301", "fixa a presunção relativa de paternidade decorrente da recusa do suposto pai ao DNA"),
                source("fam-recusa-dna-presuncao", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm", "Lei 8.560/1992", "admite todos os meios legais e moralmente legítimos para provar a paternidade"),
            ],
            ["investigação de paternidade", "DNA com pai falecido", "prova pericial de filiação"],
        ),
        build(
            "fam-dna-pai-falecido",
            "DNA após a morte: parentes, herdeiros e exumação",
            "Entenda contra quem propor a investigação de paternidade após a morte, como funciona o DNA com parentes e quando a exumação pode ser avaliada.",
            "Como provar a paternidade quando o suposto pai morreu",
            "A morte do suposto pai não extingue o direito ao reconhecimento da filiação, mas altera partes, prova e estratégia. A ação de estado não deve ser proposta simplesmente contra o espólio: a jurisprudência do STJ exige a presença de todos os herdeiros. O exame pode usar material de parentes consanguíneos e a exumação fica para situações em que sua necessidade e proporcionalidade sejam demonstradas ao juiz.",
            [
                section(
                    "Todos os herdeiros integram o polo passivo",
                    "O artigo 1606 do Código Civil preserva a pretensão de filiação nos limites ali definidos. Quando o suposto genitor já morreu, o STJ distingue a ação de estado de uma cobrança contra o patrimônio: a investigação deve ser ajuizada contra todos os herdeiros do falecido, e não contra o espólio. O Informativo 656, ao examinar o REsp 1.667.576, reafirma essa legitimidade para a ação rescisória relativa à investigação e registra a orientação consolidada para a própria investigatória.\n\nAntes de protocolar, é preciso obter certidão de óbito, identificar descendentes, ascendentes ou cônjuge conforme a sucessão concreta e conferir o inventário. A omissão de herdeiro necessário pode comprometer contraditório e validade da decisão.",
                ),
                section(
                    "A viúva pode participar mesmo quando não herda",
                    "O Informativo 578 do STJ reconhece que a viúva pode impugnar a investigação post mortem e receber o processo no estado em que estiver, ainda que, na configuração examinada, não fosse herdeira nem litisconsorte necessária. Isso não muda a regra de que os herdeiros são réus. Apenas mostra que meação, memória familiar e possível repercussão sobre a situação jurídica da viúva exigem tratamento processual cuidadoso.\n\nA lista de participantes não deve ser deduzida somente de uma certidão antiga. Renúncia, representação sucessória, falecimento de herdeiro e partilha anterior podem mudar quem precisa ser citado.",
                ),
                section(
                    "Lei 14.138/2021 permite DNA em parentes consanguíneos",
                    "A Lei 14.138/2021 inseriu o § 2º no art. 2º-A da Lei 8.560/1992. Se o suposto pai morreu ou não há notícia de seu paradeiro, o juiz pode determinar exame de DNA em parentes consanguíneos, com preferência pelos de grau mais próximo. Pais, filhos e irmãos do falecido podem fornecer material conforme a disponibilidade e a adequação técnica. A proximidade jurídica não dispensa o laboratório de explicar a probabilidade e as limitações do parentesco testado.\n\nA recusa de um parente gera presunção relativa, apreciada em conjunto com a prova existente. Não significa que qualquer recusa de qualquer familiar, sozinha, declare a paternidade.",
                ),
                section(
                    "Ônus bipartido exige prova e contraposição concretas",
                    "Em notícia de 20 de março de 2026, a Terceira Turma do STJ descreveu o ônus probatório como bipartido. O pretenso filho pode usar meios legítimos, inclusive DNA indireto e testemunhas; os réus não afastam esse material apenas sugerindo, sem prova, que outro parente poderia ser o pai. No caso divulgado, um laudo com irmãos do falecido foi lido junto a depoimentos, e a defesa precisava apresentar contraposição concreta.\n\nEsse entendimento não cria porcentagem universal nem dispensa a análise do método. Número de parentes, grau de parentesco, marcadores usados e hipóteses alternativas precisam constar do laudo.",
                ),
                section(
                    "Exumação é medida judicial, não etapa automática",
                    "A exumação pode ser considerada quando o material indireto é indisponível ou inconclusivo e a coleta dos restos mortais é necessária para esclarecer a filiação. O juiz pondera utilidade, possibilidade técnica, dignidade dos restos, custos e existência de meios menos invasivos. Não há uma regra geral que a condicione à anuência de toda a família, nem uma autorização automática baseada no desejo de uma das partes.\n\nCemitério, perito e cadeia de custódia cumprem a ordem judicial. Estado de conservação e tempo de sepultamento podem afetar a viabilidade, razão pela qual resultado positivo não pode ser prometido.",
                ),
                section(
                    "Prova documental e sucessão devem ser separadas",
                    "Cartas, mensagens, fotografias e testemunhas do relacionamento continuam úteis, sobretudo para contextualizar DNA indireto. A sentença de filiação pode abrir efeitos registrais e sucessórios, mas não substitui automaticamente inventário, habilitação ou petição de herança. Se bens já foram partilhados, o prazo patrimonial precisa ser examinado desde a abertura da sucessão.\n\nUma consulta particular pode organizar a árvore de herdeiros, os documentos do inventário e as alternativas periciais. O atendimento remoto facilita a triagem, mas coleta genética, citações e atos presenciais obedecem às determinações do processo.",
                ),
            ],
            [
                faq(
                    "O exame com um único irmão do falecido sempre resolve?",
                    "Não. A força estatística depende do parentesco, dos marcadores e das hipóteses consideradas. O laboratório deve explicar as limitações, e o juiz aprecia o laudo com as demais provas.",
                )
            ],
            [
                source("fam-dna-pai-falecido", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1606", "Código Civil, art. 1.606", "preserva a ação de prova da filiação e disciplina sua continuidade por herdeiros do filho"),
                source("fam-dna-pai-falecido", "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14138.htm", "Lei 14.138/2021", "incluiu o exame em parentes consanguíneos e a presunção relativa decorrente da recusa"),
                source("fam-dna-pai-falecido", "https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisarumaedicao&livre=%270578%27.cod.", "STJ, Informativo 578", "trata da legitimidade dos herdeiros e da participação da viúva na investigação post mortem"),
                source("fam-dna-pai-falecido", "https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisarumaedicao&livre=%270656%27.cod.", "STJ, Informativo 656 e REsp 1.667.576", "reafirma que a ação de estado deve ser dirigida aos herdeiros, não ao espólio"),
                source("fam-dna-pai-falecido", "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/20032026-Em-investigacao-de-paternidade--o-onus-da-prova-e-bipartido.aspx", "STJ, notícia de 20 de março de 2026", "explica o ônus bipartido em investigação post mortem com DNA indireto e testemunhas"),
            ],
            ["petição de herança", "recusa de parentes ao DNA", "investigação de paternidade"],
        ),
        build(
            "fam-paternidade-post-mortem-heranca",
            "Paternidade após a morte: prazo para pedir herança",
            "Entenda a diferença entre reconhecer a filiação e pedir herança, o prazo decenal e a tese do Tema 1200 do STJ sobre a abertura da sucessão.",
            "Reconhecimento tardio e petição de herança já partilhada",
            "O reconhecimento de filiação e a recuperação de patrimônio são pretensões distintas. A primeira é uma ação de estado e não prescreve; a petição de herança tem natureza patrimonial e se submete a prazo. No Tema 1200, o STJ fixou que a contagem começa na abertura da sucessão e não espera o encerramento da investigação de paternidade.",
            [
                section(
                    "Filiação imprescritível não torna a herança imprescritível",
                    "O artigo 1606 do Código Civil permite ao filho buscar a prova da filiação durante a vida. Já o artigo 1824 assegura ao herdeiro o reconhecimento de seu direito sucessório e a restituição da herança, ou de parte dela, contra quem a possua como herdeiro ou sem título. Essa segunda pretensão lida com bens e estabilidade patrimonial, motivo pelo qual recebe tratamento prescricional próprio.\n\nÉ possível obter a declaração de paternidade e, ainda assim, encontrar prescrição quanto à herança. Por isso, a análise patrimonial não deve ser deixada apenas para depois do trânsito em julgado da ação de filiação.",
                ),
                section(
                    "Tema 1200 conta o prazo desde a morte",
                    "A tese repetitiva do STJ é objetiva: o prazo para a petição de herança conta-se da abertura da sucessão, isto é, da morte, e sua fluência não é impedida, suspensa ou interrompida pelo ajuizamento da ação de reconhecimento de filiação, independentemente do trânsito em julgado. A referência utilizada deve ser a página específica do Tema 1200, e não o índice geral de repetitivos.\n\nEm regra, aplica-se o prazo geral de dez anos do Código Civil. Causas legais de impedimento, suspensão ou interrupção, inclusive situações de incapacidade, precisam ser examinadas com datas e documentos; o texto geral não resolve essas exceções.",
                ),
                section(
                    "Cumulação pode evitar perda de tempo processual",
                    "Conforme a situação, reconhecimento de filiação e petição de herança podem ser formulados no mesmo processo, com decisão primeiro sobre o estado de filho e depois sobre os efeitos patrimoniais. Isso não garante uma única sentença nem elimina questões de competência, inventário e citação de todos os interessados. A providência adequada depende de quando ocorreu o óbito, de quem recebeu os bens e de onde tramita a sucessão.\n\nQuando a partilha ainda não terminou, pode ser necessário pedir reserva de quinhão ou habilitação, sem presumir que a simples notícia da investigação paralisa todos os atos do inventário.",
                ),
                section(
                    "O que a petição de herança pode alcançar",
                    "O pedido pode buscar o quinhão que caberia ao filho em bens ainda existentes ou o valor correspondente, conforme posse, alienações e boa-fé de terceiros. A inclusão de novo descendente também altera o cálculo das quotas dos demais sucessores. Não é correto prometer a devolução física de todo bem vendido nem afirmar que a partilha será anulada integralmente.\n\nMatrículas atualizadas, extratos juntados ao inventário, formal de partilha e documentos de alienação ajudam a identificar o que ainda está com herdeiros e o que foi transferido a terceiros.",
                ),
                section(
                    "Partes e documentos precisam refletir a sucessão real",
                    "Certidões de óbito e nascimento, decisão ou pedido de filiação, cópia integral do inventário, formal de partilha, relação de herdeiros e provas dos bens são essenciais. Também importam renúncias, cessões de direitos hereditários e falecimentos posteriores. A ação de filiação post mortem deve envolver todos os herdeiros do suposto pai; o espólio, sozinho, não substitui essas pessoas na ação de estado.\n\nO cálculo do prazo deve ser feito pela data exata do óbito e pelas causas legais demonstráveis, não pela data em que o filho soube da possível paternidade como regra genérica.",
                ),
                section(
                    "Orientação jurídica deve começar pelo calendário",
                    "Em atendimento particular, o primeiro passo útil é montar uma linha do tempo com morte, abertura e encerramento do inventário, reconhecimento de filiação e transferências patrimoniais. Essa triagem permite avaliar cumulação, tutela de reserva e documentos faltantes sem garantir recuperação. Grande parte dos autos pode ser analisada digitalmente, mas atos e competência seguem o processo concreto.\n\nTambém convém separar meação de herança e registrar o valor atribuído a cada bem na partilha. O cônjuge pode receber patrimônio por fundamentos diferentes, e tratar tudo como quinhão hereditário distorce o cálculo. Dívidas, impostos e despesas do inventário reduzem o acervo antes da divisão; a cota teórica do novo filho não corresponde necessariamente ao valor bruto dos bens listados.",
                ),
            ],
            [
                faq(
                    "A investigação de paternidade interrompe o prazo da petição de herança?",
                    "Não por si só. O Tema 1200 afirma que o ajuizamento da ação de filiação não impede, suspende nem interrompe a fluência iniciada na abertura da sucessão, sem afastar outras causas legais que sejam comprovadas.",
                )
            ],
            [
                source("fam-paternidade-post-mortem-heranca", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1824", "Código Civil, art. 1.824", "fundamenta a petição de herança e a restituição do quinhão hereditário"),
                source("fam-paternidade-post-mortem-heranca", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1606", "Código Civil, art. 1.606", "distingue a ação de prova da filiação, de natureza imprescritível"),
                source("fam-paternidade-post-mortem-heranca", "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=1200&cod_tema_inicial=1200&novaConsulta=true&tipo_pesquisa=T", "STJ, Tema Repetitivo 1200", "fixa a abertura da sucessão como termo inicial e afasta suspensão pela ação de filiação"),
            ],
            ["DNA com pai falecido", "inventário e reserva de quinhão", "prescrição sucessória"],
        ),
        build(
            "fam-reconhecer-filho-cartorio",
            "Reconhecimento voluntário de filho no cartório",
            "Veja as formas de reconhecimento voluntário, as anuências exigidas, os documentos básicos e quando a divergência precisa ser levada ao Judiciário.",
            "Como formalizar o reconhecimento voluntário de filiação",
            "Quando não existe disputa sobre a paternidade, a filiação pode ser reconhecida sem ação investigatória. A Lei 8.560/1992 admite declaração no registro de nascimento, escritura pública, escrito particular arquivado, testamento e manifestação expressa perante juiz. Para o procedimento registral posterior ao nascimento, o Código Nacional de Normas do CNJ define identidade, anuências e remessa entre cartórios.",
            [
                section(
                    "Escolha da forma e conferência da identidade",
                    "O reconhecimento é pessoal e irrevogável, embora o documento possa assumir uma das formas legais. No cartório, o oficial confere documento oficial de identificação, qualificação e assinatura do reconhecedor e mantém a documentação exigida. O pedido pode ser apresentado a registro civil diverso daquele que lavrou o nascimento; a serventia receptora encaminha o termo e as cópias ao cartório do assento.\n\nIsso não autoriza reconhecimento por mensagem informal nem permite que terceiro assine no lugar do pai sem título juridicamente adequado. A certidão de nascimento atualizada ajuda a localizar o assento e conferir a filiação já registrada.",
                ),
                section(
                    "Anuência muda conforme a idade do filho",
                    "Para a averbação posterior, o Código Nacional de Normas exige anuência escrita do filho maior. Se o reconhecido é menor, depende da anuência da mãe; na falta dela ou na impossibilidade de manifestação válida, o caso é apresentado ao juiz competente. O artigo 1614 do Código Civil confirma que o filho maior não pode ser reconhecido sem consentimento.\n\nO filho reconhecido quando menor pode impugnar o reconhecimento nos quatro anos seguintes à maioridade ou emancipação, conforme o mesmo artigo. Essa regra não deve ser confundida com o direito imprescritível do próprio filho de investigar a filiação.",
                ),
                section(
                    "Documentos básicos e envio ao cartório do assento",
                    "Em geral, são necessários documento oficial do reconhecedor, certidão de nascimento do filho e o termo ou instrumento adequado. O oficial pode solicitar complementação para individualizar as pessoas e afastar homonímia. Se o pedido for feito fora do cartório de origem, haverá comunicação entre serventias; não se cria um novo registro de nascimento.\n\nDados falsos ou dúvida fundada sobre fraude levam o oficial a não praticar o ato e a submeter a questão ao magistrado. Divergência sobre a verdade biológica não deve ser resolvida pela inserção unilateral de informação controvertida.",
                ),
                section(
                    "Gratuidade do reconhecimento e limites da certidão",
                    "O reconhecimento de paternidade e sua averbação observam a gratuidade assegurada pelas normas nacionais. Emissão de vias adicionais e outros atos não abrangidos podem seguir a legislação de emolumentos local, por isso eventual cobrança deve ser discriminada pelo cartório. A nova certidão passa a refletir a filiação averbada sem narrar, no traslado comum, a origem do reconhecimento além do permitido pelas regras registrais.",
                ),
                section(
                    "Recusa ou dúvida desloca a questão para outra via",
                    "Se o suposto pai nega o vínculo, não é localizado ou se recusa a reconhecer, o cartório não realiza investigação nem impõe DNA. A averiguação oficiosa prevista na Lei 8.560/1992 ou a ação de investigação podem ser adequadas. Disputas sobre alimentos, convivência e herança também exigem providência própria; o oficial registra a filiação, mas não calcula prestações nem partilha bens.",
                ),
            ],
            [
                faq(
                    "O reconhecimento pode ser apresentado em cartório diferente do nascimento?",
                    "Sim. O Código Nacional de Normas prevê a colheita perante outra serventia e o envio ao cartório que mantém o assento, desde que identidade, documentos e anuências estejam regulares.",
                )
            ],
            [
                source("fam-reconhecer-filho-cartorio", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm", "Lei 8.560/1992", "enumera as formas legais de reconhecimento voluntário de filho"),
                source("fam-reconhecer-filho-cartorio", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1614", "Código Civil, art. 1.614", "exige consentimento do filho maior e prevê a impugnação pelo reconhecido menor"),
                source("fam-reconhecer-filho-cartorio", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "Código Nacional de Normas rege identidade, anuência, remessa e averbação do reconhecimento"),
            ],
            ["averiguação oficiosa de paternidade", "consentimento do filho maior", "retificação do registro civil"],
        ),
        build(
            "fam-reconhecimento-filho-maior-consentimento",
            "Reconhecimento de filho adulto exige consentimento",
            "Entenda por que o filho maior precisa consentir com o reconhecimento voluntário, como formalizar a anuência e o que ocorre diante de recusa.",
            "O consentimento do filho maior no reconhecimento voluntário",
            "O reconhecimento voluntário não é uma decisão unilateral do pai quando o filho já atingiu a maioridade. O artigo 1614 do Código Civil protege a identidade e o estado familiar construídos pela pessoa adulta: sem sua concordância, a averbação voluntária não se completa. Isso é diferente da investigação promovida pelo próprio filho contra quem nega a paternidade.",
            [
                section(
                    "O alcance exato do artigo 1614",
                    "A norma diz que o filho maior não pode ser reconhecido sem consentimento. A concordância se refere ao ato voluntário apresentado pelo reconhecedor e não pode ser presumida apenas por contatos familiares, ajuda financeira ou teste genético particular. Para o reconhecido menor, o artigo prevê a possibilidade de impugnar nos quatro anos seguintes à maioridade ou emancipação.\n\nO consentimento não é avaliação moral sobre a ausência passada. É requisito jurídico para alterar o registro de pessoa adulta pela via voluntária.",
                ),
                section(
                    "Como a anuência chega ao registro civil",
                    "No procedimento registral, a anuência deve ser escrita e colhida com conferência de identidade, conforme o Código Nacional de Normas do CNJ. O cartório que recebe a manifestação pode ser diferente daquele que lavrou o nascimento e encaminhará a documentação à serventia de origem. Antes de assinar, o filho pode pedir leitura do termo e conferir quais dados serão averbados.\n\nInstrumentos públicos, particulares ou manifestação perante juiz seguem as formas previstas na Lei 8.560/1992, mas nenhuma delas elimina o consentimento exigido do maior.",
                ),
                section(
                    "Recusa impede o ato voluntário, não encerra toda controvérsia",
                    "Se o filho maior não concorda, o reconhecimento voluntário e sua averbação não avançam. Não é adequado afirmar, porém, que qualquer discussão judicial possível fica automaticamente proibida: ações de estado têm legitimidades, pedidos e interesses próprios, e a pessoa afetada deve ser ouvida. O resultado depende da pretensão concreta, da prova e da proteção da identidade familiar.\n\nQuando é o filho quem busca a filiação, ele pode ajuizar investigação mesmo contra a vontade do suposto pai. Nesse cenário, o consentimento exigido pelo artigo 1614 não funciona como veto do investigado.",
                ),
                section(
                    "Efeitos devem ser explicados antes da assinatura",
                    "O reconhecimento produz estado de filiação e repercute em parentesco, alimentos e sucessão. Alteração de sobrenome deve observar o pedido e as regras registrais, sem presumir que toda averbação imporá automaticamente uma forma específica de nome. Uma orientação jurídica particular pode esclarecer os efeitos e conferir o instrumento, sem pressionar o filho a consentir nem prometer solução para conflitos familiares.",
                ),
            ],
            [
                faq(
                    "Ajuda financeira anterior vale como consentimento?",
                    "Não. Pagamentos ou presentes podem integrar a história familiar, mas não substituem a manifestação formal do filho maior para o reconhecimento voluntário.",
                )
            ],
            [
                source("fam-reconhecimento-filho-maior-consentimento", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1614", "Código Civil, art. 1.614", "condiciona o reconhecimento do filho maior ao consentimento e trata da impugnação do reconhecido menor"),
                source("fam-reconhecimento-filho-maior-consentimento", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm", "Lei 8.560/1992", "define as formas pelas quais o reconhecimento voluntário pode ser manifestado"),
            ],
            ["reconhecimento voluntário no cartório", "investigação de paternidade", "alteração de sobrenome"],
        ),
        build(
            "fam-paternidade-socioafetiva",
            "Paternidade socioafetiva: vínculo, prova e efeitos",
            "Entenda como cuidado estável e reconhecimento social podem formar filiação socioafetiva, o Tema 622 do STF e as vias cartorial e judicial.",
            "O que caracteriza a paternidade socioafetiva",
            "Paternidade socioafetiva é filiação fundada numa relação estável de pai e filho exteriorizada na vida familiar e social. Não nasce de um gesto isolado, de namoro com o genitor biológico nem do simples apoio financeiro. O artigo 1593 do Código Civil admite parentesco de outra origem, e o direito brasileiro protege a realidade familiar demonstrada por fatos consistentes.",
            [
                section(
                    "Estado de filho exige estabilidade e expressão social",
                    "Cuidado cotidiano, responsabilidade por saúde e educação, apresentação pública como família, residência, inclusão como dependente e documentos escolares podem revelar o vínculo. Nome, trato e fama são referências tradicionais, mas a prova não se reduz a checklist rígido. O contexto deve mostrar que as pessoas se reconheceram de modo duradouro em posições de pai ou mãe e filho, sem fraude ou uso instrumental do registro.\n\nO Código Nacional de Normas exige apuração objetiva do vínculo no procedimento extrajudicial. Fotografias isoladas ou uma declaração genérica não bastam quando o conjunto aponta outra realidade.",
                ),
                section(
                    "Tema 622 permite coexistência com a origem biológica",
                    "No Tema 622, o STF fixou que a paternidade socioafetiva, declarada ou não em registro público, não impede o reconhecimento concomitante do vínculo baseado na origem biológica, com os efeitos jurídicos próprios. A tese evita uma escolha automática entre sangue e cuidado. Ela também não determina multiparentalidade em todo caso: cada vínculo alegado precisa ser provado e a solução deve respeitar a situação familiar concreta.\n\nO motivo patrimonial, sozinho, não autoriza negar uma filiação biológica comprovada. Da mesma forma, afeto alegado apenas para obter vantagem não substitui estado de filho real.",
                ),
                section(
                    "Cartório atende somente aos requisitos nacionais",
                    "O reconhecimento socioafetivo extrajudicial é possível para pessoa acima de 12 anos. O requerente deve ser maior de 18 anos e ter pelo menos 16 anos a mais que o reconhecido; ascendentes e irmãos não podem usar essa via entre si. Exigem-se prova objetiva, consentimentos pessoais previstos na norma e parecer favorável do Ministério Público. O cartório pode incluir um ascendente socioafetivo mesmo coexistindo filiação biológica; mais de um ascendente socioafetivo exige processo judicial.",
                ),
                section(
                    "Reconhecimento produz filiação, não favor revogável",
                    "Formalizado o vínculo, surgem direitos e deveres de filiação, inclusive alimentos e sucessão conforme as regras aplicáveis. O reconhecimento voluntário é irrevogável e só pode ser desconstituído judicialmente por vício de vontade, fraude ou simulação. Conflito, pessoa com 12 anos ou menos, falta de consentimento ou prova controvertida deslocam a discussão para o Judiciário, sem promessa de deferimento.",
                ),
            ],
            [],
            [
                source("fam-paternidade-socioafetiva", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1593", "Código Civil, art. 1.593", "admite parentesco natural ou civil resultante de consanguinidade ou outra origem"),
                source("fam-paternidade-socioafetiva", "https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=622", "STF, Tema 622", "permite o reconhecimento concomitante dos vínculos socioafetivo e biológico"),
                source("fam-paternidade-socioafetiva", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "estabelece requisitos, provas, consentimentos e limites do reconhecimento extrajudicial"),
            ],
            ["reconhecimento socioafetivo em cartório", "multiparentalidade", "inclusão do pai biológico"],
        ),
        build(
            "fam-registrar-socioafetivo-cartorio",
            "Reconhecimento socioafetivo no cartório: requisitos",
            "Veja idade mínima, diferença de 16 anos, prova objetiva, consentimentos, parecer do Ministério Público e limites do reconhecimento socioafetivo.",
            "Como pedir o reconhecimento socioafetivo extrajudicial",
            "O cartório pode formalizar uma relação socioafetiva sem processo quando o caso se enquadra no Código Nacional de Normas do CNJ. A via não serve para criar parentesco apenas por conveniência: a pessoa reconhecida deve ter mais de 12 anos, o vínculo precisa ser estável e socialmente exteriorizado, e o procedimento exige prova concreta, consentimentos pessoais e parecer favorável do Ministério Público.",
            [
                section(
                    "Idades, impedimentos e diferença mínima",
                    "O requerente precisa ter mais de 18 anos, independentemente do estado civil, e ser pelo menos 16 anos mais velho que o filho socioafetivo. Irmãos não podem reconhecer um ao outro, nem ascendentes podem reconhecer descendentes pela sistemática socioafetiva. A norma autoriza o procedimento apenas para reconhecido acima de 12 anos; abaixo dessa faixa, eventual pretensão depende da via judicial.\n\nEsses requisitos são cumulativos. Maioridade do requerente não compensa diferença etária insuficiente, e convivência longa não permite ao cartório afastar um impedimento expresso.",
                ),
                section(
                    "Prova objetiva do vínculo estável",
                    "O registrador deve atestar como verificou a socioafetividade. Podem ser apresentados apontamento escolar como responsável, plano de saúde ou previdência, registro de residência comum, vínculo conjugal com o ascendente biológico, inscrição como dependente, fotografias de momentos relevantes e declarações de testemunhas com firma reconhecida. A lista é exemplificativa, mas a apuração objetiva é obrigatória.\n\nSe um documento típico não existir, o requerente explica a impossibilidade e oferece outros elementos. O oficial precisa registrar sua forma de apuração e arquivar as provas; não basta colher uma frase de afeto.",
                ),
                section(
                    "Consentimentos são pessoais e incluem o Ministério Público",
                    "Sendo o reconhecido menor de 18 anos, pai e mãe constantes do registro e o próprio filho maior de 12 anos devem consentir pessoalmente perante oficial ou escrevente autorizado. Para o maior, permanece necessária sua concordância. Falta ou impossibilidade de manifestação válida de quem deve consentir leva o caso ao juiz competente.\n\nDepois de atendidos os requisitos, o expediente segue ao Ministério Público. Somente parecer favorável permite ao registrador praticar o ato; parecer desfavorável impede o registro administrativo, e eventual dúvida vai ao Judiciário.",
                ),
                section(
                    "Um ascendente socioafetivo pode coexistir com o biológico",
                    "O reconhecimento é unilateral e pode incluir um ascendente socioafetivo, do lado paterno ou materno, sem apagar automaticamente a filiação biológica já existente. A norma admite até dois pais e duas mães no campo filiação, mas limita a via extrajudicial à inclusão de um ascendente socioafetivo. Se a pretensão é incluir mais de um ascendente socioafetivo, será necessária ação judicial. Portanto, não é correto afirmar que toda coexistência entre vínculo biológico e socioafetivo exige processo.",
                ),
                section(
                    "Documentos, cartório competente e situações de recusa",
                    "O pedido pode ser processado por registro civil diverso daquele do nascimento, com documento oficial do requerente e certidão do filho em original e cópia, além das provas e anuências. Processo judicial em curso sobre filiação ou adoção impede o uso simultâneo desta sistemática. Suspeita de fraude, falsidade, simulação, vício de vontade ou dúvida sobre o estado de filho obriga o oficial a fundamentar a recusa e encaminhar o caso ao juiz.\n\nUma consulta jurídica pode organizar a prova e conferir os consentimentos, mas não substitui a apuração do registrador nem o parecer do Ministério Público.",
                ),
            ],
            [
                faq(
                    "É possível desfazer o reconhecimento no próprio cartório?",
                    "Não por simples arrependimento. O ato é irrevogável e só pode ser desconstituído judicialmente nas hipóteses de vício de vontade, fraude ou simulação.",
                )
            ],
            [
                source("fam-registrar-socioafetivo-cartorio", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "arts. 505 a 511 regem idade, diferença etária, prova, consentimentos, parecer e limites"),
                source("fam-registrar-socioafetivo-cartorio", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1593", "Código Civil, art. 1.593", "fornece a base civil do parentesco resultante de outra origem"),
                source("fam-registrar-socioafetivo-cartorio", "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm", "Lei 6.015/1973", "rege os assentos e averbações do registro civil das pessoas naturais"),
            ],
            ["paternidade socioafetiva", "multiparentalidade", "consentimento do filho maior"],
        ),
        build(
            "fam-multiparentalidade",
            "Multiparentalidade: coexistência de vínculos de filiação",
            "Entenda quando vínculos biológico e socioafetivo podem coexistir, os efeitos próprios de cada filiação e o limite da via extrajudicial.",
            "O que significa ter mais de um pai ou mãe no registro",
            "Multiparentalidade é a coexistência jurídica de vínculos de filiação, como o pai biológico e o pai socioafetivo que efetivamente exerceu essa função. Ela não apaga uma história para validar outra nem surge só porque há padrasto, madrasta ou exame genético. Cada vínculo precisa de fundamento e prova, e a solução deve refletir a identidade familiar da pessoa reconhecida.",
            [
                section(
                    "Tema 622 rejeita a escolha automática entre vínculos",
                    "O STF decidiu no Tema 622 que a paternidade socioafetiva, esteja ou não registrada, não impede o reconhecimento concomitante da filiação baseada na origem biológica, com os efeitos jurídicos próprios. A tese protege a paternidade responsável e impede que o genitor biológico use a existência de pai de criação para afastar, por si só, responsabilidades.\n\nIsso não cria presunção de que toda família recomposta é multiparental. Socioafetividade exige estado de filho, e origem biológica controvertida exige prova adequada.",
                ),
                section(
                    "Alimentos e sucessão seguem os vínculos reconhecidos",
                    "A filiação reconhecida produz direitos e deveres. Necessidade do alimentando e possibilidade de cada responsável continuam orientando alimentos, sem fórmula automática de divisão igual. Na sucessão, o filho integra a classe correspondente de cada pai ou mãe reconhecido segundo as regras aplicáveis. A existência de outro vínculo não reduz por si só o estado de filho nem autoriza negar a origem biológica por receio patrimonial.",
                ),
                section(
                    "Nem toda multiparentalidade depende de ação",
                    "O Código Nacional de Normas permite ao cartório incluir um ascendente socioafetivo, inclusive sem apagar a filiação biológica já registrada, desde que o reconhecido tenha mais de 12 anos e todos os requisitos sejam satisfeitos. O ato é unilateral e não pode resultar em mais de dois pais e duas mães. A inclusão de mais de um ascendente socioafetivo deve tramitar judicialmente.\n\nConflito, falta de consentimento, prova controvertida ou processo de filiação em curso também afastam a solução administrativa.",
                ),
                section(
                    "Registro deve refletir a decisão ou o ato válido",
                    "Na via judicial, o pedido precisa deixar claro quais vínculos se pretende reconhecer e quais devem permanecer. DNA, registro atual e provas do estado de filho orientam a instrução. Na via cartorial, o registrador faz apuração objetiva e depende de parecer favorável do Ministério Público. Em ambos os casos, sobrenome e ascendentes serão lançados conforme o título e as normas registrais, sem promessa de formato antes da qualificação.",
                ),
            ],
            [],
            [
                source("fam-multiparentalidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1593", "Código Civil, art. 1.593", "admite parentesco resultante de outra origem além da consanguinidade"),
                source("fam-multiparentalidade", "https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=622", "STF, Tema 622", "reconhece a possibilidade de filiação biológica concomitante à socioafetiva"),
                source("fam-multiparentalidade", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "define quando um ascendente socioafetivo pode ser incluído extrajudicialmente e quando a via judicial é obrigatória"),
            ],
            ["reconhecimento socioafetivo no cartório", "inclusão do pai biológico", "alimentos entre múltiplos pais"],
        ),
        build(
            "fam-incluir-pai-biologico-multiparentalidade",
            "Incluir pai biológico sem excluir o pai socioafetivo",
            "Veja como provar a origem biológica, preservar a filiação socioafetiva e pedir a coexistência dos vínculos sem prometer foro ou resultado.",
            "Como somar a filiação biológica ao vínculo de criação",
            "Quem já possui pai socioafetivo não precisa escolher automaticamente entre a história de cuidado e a origem genética. O Tema 622 do STF admite o reconhecimento concomitante dos vínculos. O caminho concreto pode envolver reconhecimento voluntário ou ação judicial, conforme consenso, registro existente e prova; não há regra de que toda coexistência precise começar em processo.",
            [
                section(
                    "O Tema 622 protege os dois fundamentos da filiação",
                    "A tese do STF afirma que a paternidade socioafetiva, declarada ou não em registro, não impede o vínculo concomitante baseado na origem biológica, com efeitos jurídicos próprios. O pai biológico não se libera porque outra pessoa criou o filho, e o pai socioafetivo não é apagado apenas porque surgiu um exame genético.\n\nA análise começa por identificar se o vínculo de criação já está registrado ou ainda precisa ser provado. Convivência estável, cuidado e reconhecimento social sustentam a socioafetividade; o DNA e os demais meios legítimos tratam da origem biológica.",
                ),
                section(
                    "Consenso pode simplificar, mas o registro deve ser qualificável",
                    "Se o pai biológico reconhece voluntariamente e todos os requisitos registrais são atendidos, o cartório avaliará o título e o assento existente. Quando há recusa, dúvida sobre a origem, conflito entre interessados ou exigência não superada, a investigação judicial permite produzir DNA e pedir expressamente a manutenção do vínculo socioafetivo. O reconhecimento socioafetivo extrajudicial de um ascendente também pode coexistir com filiação biológica, nas condições do Código Nacional de Normas.\n\nMais de um ascendente socioafetivo, porém, depende da via judicial.",
                ),
                section(
                    "Partes e competência não admitem fórmula única",
                    "O pai biológico controvertido deve participar da investigação. O pai socioafetivo registrado e outros interessados podem precisar integrar o contraditório porque a decisão repercute no assento e nas relações familiares, mas a formação das partes será definida pela pretensão e pelo juízo. Também não se pode prometer foro do filho ou do pai: idade, domicílios, cumulação com alimentos e regras locais influenciam a competência.\n\nA petição deve descrever o registro atual, a filiação que se pretende acrescentar e a preservação pedida, evitando um pedido ambíguo de simples substituição.",
                ),
                section(
                    "Provas dos vínculos respondem a perguntas diferentes",
                    "Certidão atualizada mostra a situação registral. DNA com cadeia de coleta e identificação responde à origem genética. Documentos escolares, plano de saúde, fotografias contextualizadas, residência e testemunhos podem revelar estado de filho socioafetivo. Um tipo de prova não substitui o outro: genética não demonstra cuidado, e cuidado não demonstra ascendência.\n\nDocumentos devem ser obtidos licitamente e preservados no formato original. Conversas recortadas ou declarações preparadas apenas para o processo podem exigir confirmação.",
                ),
                section(
                    "Efeitos patrimoniais não tornam a filiação ilegítima",
                    "Alimentos e sucessão acompanham os vínculos reconhecidos conforme suas regras. Necessidade e capacidade econômica continuam relevantes, e a herança é apurada em cada sucessão. A intenção de obter um efeito patrimonial pode ser examinada no contexto da boa-fé e da prova, mas não autoriza negar uma filiação biológica comprovada apenas porque ela produz herança ou alimentos. O estado de filho não depende de demonstrar convivência afetiva com o genitor biológico.",
                ),
                section(
                    "Resultado registral e orientação responsável",
                    "A sentença ou o título válido orienta a averbação de pais, avós e eventual sobrenome conforme o pedido e a qualificação registral. Não se deve prometer tempo, inclusão automática de nome ou concordância de todos. Em atendimento particular, a contribuição técnica é escolher a via, formar corretamente o contraditório e separar as provas dos dois vínculos com cautela; etapas digitais não eliminam perícia e atos determinados pelo juízo.\n\nA vontade da pessoa reconhecida merece atenção especial. Se for adulta, sua narrativa sobre identidade, nome e relações familiares integra o caso; se for criança ou adolescente, representação, escuta e melhor interesse orientam a condução. A existência de conflito entre os adultos não autoriza usar o registro como punição nem esconder a origem. Eventuais alimentos vencidos, herança já aberta ou registro feito em outro país acrescentam questões próprias e não devem ser resolvidos apenas no pedido de averbação.",
                ),
            ],
            [
                faq(
                    "O pai socioafetivo precisa concordar com o DNA?",
                    "A prova genética diz respeito ao vínculo biológico e pode ser determinada no processo. A participação do pai socioafetivo e o alcance de sua manifestação dependem do registro, dos pedidos e da formação do contraditório, sem poder de veto automático sobre a origem do filho.",
                )
            ],
            [
                source("fam-incluir-pai-biologico-multiparentalidade", "https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=622", "STF, Tema 622", "autoriza o reconhecimento concomitante das filiações socioafetiva e biológica"),
                source("fam-incluir-pai-biologico-multiparentalidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1593", "Código Civil, art. 1.593", "reconhece parentesco natural ou civil conforme consanguinidade ou outra origem"),
                source("fam-incluir-pai-biologico-multiparentalidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1606", "Código Civil, art. 1.606", "fundamenta a ação de prova da filiação proposta pelo filho"),
                source("fam-incluir-pai-biologico-multiparentalidade", "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm", "Código de Processo Civil", "rege contraditório, prova e procedimento da pretensão judicial"),
            ],
            ["multiparentalidade", "paternidade socioafetiva", "investigação de paternidade"],
        ),
        build(
            "fam-anular-registro-paternidade",
            "DNA negativo e anulação do registro de paternidade",
            "Entenda por que o DNA negativo não basta, a diferença entre negatória e anulação do reconhecimento e os requisitos cumulativos usados pelo STJ.",
            "Quando a paternidade registral pode ser desconstituída",
            "Um DNA negativo prova ausência de vínculo genético, mas não apaga sozinho o estado de filiação. A resposta depende de como o registro foi formado e de existir ou não paternidade socioafetiva. Para reconhecimento voluntário, o STJ exige prova robusta de erro ou coação e inexistência de relação socioafetiva, requisitos cumulativos que protegem a estabilidade do filho.",
            [
                section(
                    "Negatória do marido e anulação registral não são idênticas",
                    "O artigo 1601 do Código Civil prevê que cabe ao marido contestar a paternidade dos filhos nascidos de sua mulher e declara imprescritível essa ação. Já o artigo 1604 impede reivindicar estado contrário ao registro de nascimento, salvo prova de erro ou falsidade. Quando alguém reconheceu voluntariamente um filho, a discussão costuma envolver validade da declaração registral e vínculo socioafetivo, não mera aplicação automática da regra dirigida ao marido.\n\nA petição precisa identificar a origem do registro: presunção conjugal, declaração no nascimento, escritura, reconhecimento posterior ou decisão judicial. Misturar essas hipóteses pode levar ao fundamento jurídico errado.",
                ),
                section(
                    "Dois requisitos cumulativos segundo o STJ",
                    "Em decisão divulgada em 10 de junho de 2025, o STJ reafirmou que a anulação do registro exige prova clara de que o pai foi induzido a erro ou coagido e, ao mesmo tempo, inexistência de relação socioafetiva entre pai e filho. No caso, mesmo reconhecido vício de consentimento, a convivência familiar comprovada impediu a retificação.\n\nQuem registrou sabendo que não era o pai biológico não demonstra erro apenas apresentando DNA. E quem foi enganado também não obtém automaticamente a exclusão se exerceu por anos uma paternidade socioafetiva que o ordenamento protege.",
                ),
                section(
                    "DNA responde à genética, não à validade da vontade",
                    "O laudo excludente é importante, mas não informa o que o registrante sabia no dia do ato nem como a relação se desenvolveu. Mensagens da época, testemunhas, contexto da declaração e documentos que revelem quando a dúvida surgiu podem tratar do vício. Escola, plano de saúde, dependência, convivência, fotografias contextualizadas e testemunhos ajudam a demonstrar ou afastar estado de filho.\n\nTeste particular sem cadeia de identificação pode precisar ser repetido judicialmente. O juiz aprecia sua confiabilidade e assegura contraditório ao filho e aos demais interessados.",
                ),
                section(
                    "Afastamento posterior não apaga toda a história",
                    "Rompimento conjugal, conflito depois do DNA ou afastamento recente não eliminam retroativamente vínculo socioafetivo antes consolidado. A decisão de 2025 considerou a história de viagens, despesas e convivência anterior, mesmo após anos de distanciamento. Por outro lado, o simples nome no registro também não prova, em todos os casos, que houve socioafetividade: é preciso examinar fatos concretos e a voluntariedade.\n\nNão existe prazo de conveniência pelo qual a demora, sozinha, decida a ação. Imprescritibilidade, boa-fé, proteção do filho e modalidade do registro devem ser analisadas sem criar decadência que a lei não previu.",
                ),
                section(
                    "Efeitos dependem da sentença e não retroagem livremente",
                    "Se a desconstituição for acolhida, a sentença define a alteração do assento e os efeitos sobre nome, parentesco, alimentos e sucessão. Valores alimentares consumidos têm proteção própria, e eventual repetição não deve ser prometida. Também não se pode excluir avós registrais, extinguir dívida ou inserir outro pai apenas com pedido administrativo baseado no DNA.\n\nO filho precisa participar do contraditório, representado ou assistido conforme a idade. Seu melhor interesse não substitui a prova, mas impede que a controvérsia seja tratada só como disputa entre adultos.",
                ),
                section(
                    "Documentos para uma triagem jurídica responsável",
                    "Certidão atualizada, instrumento que originou o reconhecimento, laudo completo, mensagens contemporâneas ao registro e provas da convivência devem ser organizados por data. Uma consulta particular pode distinguir negatória, anulação e eventual reconhecimento de outro vínculo, sem prometer retirada do nome. O atendimento inicial pode ocorrer digitalmente, mas perícia e atos processuais seguem a decisão judicial.\n\nÉ necessário conferir também quem pretende ajuizar. A ação do marido prevista no artigo 1601 protege situação personalíssima, enquanto pedido do próprio filho, de terceiro ou de sucessor pode ter fundamento e legitimidade diferentes. Falecimento do pai registral, incapacidade do filho e sentença anterior sobre a mesma filiação exigem análise específica de sucessão processual e coisa julgada. Nenhuma dessas questões é resolvida apenas apresentando novo exame particular.",
                ),
            ],
            [
                faq(
                    "A mãe admitir que houve engano substitui todas as provas?",
                    "Não. A declaração pode ser relevante, mas o juiz examina sua consistência, o DNA, as circunstâncias do registro e a eventual socioafetividade, com contraditório do filho e dos interessados.",
                )
            ],
            [
                source("fam-anular-registro-paternidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1601", "Código Civil, art. 1.601", "disciplina a ação do marido para contestar a paternidade e sua imprescritibilidade"),
                source("fam-anular-registro-paternidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1604", "Código Civil, art. 1.604", "condiciona a alteração do estado constante do registro à prova de erro ou falsidade"),
                source("fam-anular-registro-paternidade", "https://www.stj.jus.br/sites/portalp/paginas/comunicacao/noticias/2025/10062025-retificacao-de-registro-de-filho-apos-exame-negativo-de-dna-depende-da-inexistencia-de-vinculo-socioafetivo.aspx", "STJ, decisão divulgada em 10 de junho de 2025", "reafirma erro ou coação e ausência de socioafetividade como requisitos cumulativos"),
            ],
            ["paternidade socioafetiva", "exame de DNA judicial", "retificação do registro civil"],
        ),
        build(
            "fam-adocao-a-brasileira",
            "Adoção à brasileira: ilicitude e proteção da criança",
            "Entenda o crime de registrar filho alheio como próprio, por que a prática não deve ser incentivada e como o melhor interesse é analisado caso a caso.",
            "O que é adoção à brasileira e por que ela é irregular",
            "A expressão descreve o registro consciente do filho de outra pessoa como se fosse biológico, fora do procedimento de adoção. O ato não é atalho legítimo para formar família: burla controles destinados a proteger a criança, a família de origem e pretendentes habilitados. Quando a situação já existe, porém, a resposta civil não pode ignorar vínculos reais nem retirar a criança de um lar sem avaliação concreta.",
            [
                section(
                    "Art. 242 do Código Penal tipifica o registro falso",
                    "Registrar como próprio o filho de outrem é crime previsto no art. 242 do Código Penal. A lei prevê tratamento diferente quando houver motivo de reconhecida nobreza e admite que o juiz deixe de aplicar a pena nessa hipótese, mas isso depende do caso e não transforma a conduta em regular. Pagamento, ocultação, intermediação ou falsificação podem agravar o quadro e envolver outros ilícitos.\n\nQuem ainda pretende receber diretamente uma criança deve procurar a Vara da Infância e Juventude e seguir o Estatuto, sem combinar entrega e registro paralelos.",
                ),
                section(
                    "Vínculo formado não é automaticamente válido ou nulo",
                    "O STJ ressalta que a adoção direta contraria o sistema legal e não deve ser incentivada, ao mesmo tempo em que exige exame do melhor interesse da criança. Tempo de convivência, segurança do ambiente, risco físico ou psíquico, origem da entrega e estudo psicossocial influenciam medidas de guarda, acolhimento e registro. Não existe regra de que o crime sempre consolida filiação nem de que a descoberta sempre rompe imediatamente a família vivida.",
                ),
                section(
                    "Quem registrou não pode tratar o filho como contrato revogável",
                    "Quando o registrante sabia não ser o pai biológico e construiu relação socioafetiva, o STJ afasta a simples desconstituição por arrependimento ou término da relação com a mãe. O estado de filho e sua proteção não ficam sujeitos a uma condição privada. Situação diversa pode existir diante de fraude, ausência de vínculo e iniciativa do próprio filho, mas depende de ação, prova e contraditório.",
                ),
                section(
                    "Regularização exige rede de proteção e análise individual",
                    "Certidão, história da entrega, documentos de cuidado e informações verdadeiras devem ser apresentados a advogado, Defensoria, Ministério Público ou Vara da Infância. Não se deve produzir novo documento falso nem combinar versões. A solução pode envolver guarda, adoção, filiação socioafetiva ou retificação, conforme idade, vínculos e segurança. O objetivo é regularizar sem ocultar a origem e sem prometer preservação automática do registro irregular.",
                ),
            ],
            [
                faq(
                    "A pessoa registrada pode conhecer ou buscar a origem biológica?",
                    "Sim. O direito à origem e eventual pretensão de filiação pertencem à pessoa registrada. Os efeitos sobre o vínculo existente exigem análise própria e não autorizam substituição automática no cartório.",
                )
            ],
            [
                source("fam-adocao-a-brasileira", "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm#art242", "Código Penal, art. 242", "tipifica o registro de filho alheio como próprio e prevê o tratamento do motivo de reconhecida nobreza"),
                source("fam-adocao-a-brasileira", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art50", "Estatuto da Criança e do Adolescente, art. 50", "estrutura o cadastro e as salvaguardas do procedimento legal de adoção"),
                source("fam-adocao-a-brasileira", "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias-antigas/2018/2018-02-04_08-01_Julgados-sobre-adocao-a-brasileira-buscam-preservar-o-melhor-interesse-da-crianca.aspx", "STJ, especial sobre adoção à brasileira", "expõe a análise caso a caso da irregularidade e do melhor interesse da criança"),
            ],
            ["adoção unilateral", "direito à origem genética", "anulação do registro de paternidade"],
        ),
        build(
            "fam-pai-se-recusa-registrar",
            "Pai não registra o filho: averiguação e investigação",
            "Veja como funciona a averiguação oficiosa, o que ocorre se o suposto pai negar ou silenciar e quando a investigação judicial se torna necessária.",
            "Caminhos quando o suposto pai não reconhece o filho",
            "A mãe pode registrar a criança apenas com sua filiação e indicar o suposto pai para a averiguação prevista na Lei 8.560/1992. O procedimento busca um reconhecimento espontâneo, mas não decide a paternidade nem força exame de DNA. Se houver negativa, silêncio ou controvérsia, a solução pode exigir investigação judicial com contraditório e prova.",
            [
                section(
                    "O cartório envia a indicação para averiguação",
                    "No registro de nascimento de menor apenas com a maternidade estabelecida, o oficial remete ao juiz certidão integral e os dados disponíveis do suposto pai indicados pela mãe. O juízo pode ouvi-la sobre a alegação e notifica o indicado para se manifestar. É importante fornecer nome completo, endereço conhecido e outros dados verdadeiros, sem acessar ilicitamente cadastros ou inventar identificadores.\n\nA indicação não insere o nome na certidão. Até haver reconhecimento válido ou decisão judicial, o assento permanece com a filiação juridicamente estabelecida.",
                ),
                section(
                    "Reconhecimento espontâneo encerra a dúvida registral",
                    "Se o notificado confirma expressamente a paternidade, lavra-se termo de reconhecimento e a averbação é enviada ao cartório do nascimento. Identidade e manifestação são conferidas conforme o Código Nacional de Normas. Anuências exigidas para o reconhecido maior ou para determinadas situações de menor também devem ser observadas.\n\nO procedimento não fixa sozinho convivência, guarda ou valor de alimentos. Esses assuntos podem exigir acordo homologado ou decisão própria, embora decorram da nova relação de filiação.",
                ),
                section(
                    "Negativa ou silêncio podem levar ao Ministério Público",
                    "Se o suposto pai não responde em 30 dias ou nega a alegação, o juiz remete os autos ao Ministério Público para eventual investigação de paternidade, desde que existam elementos suficientes. Não é correto prometer que o órgão ajuizará toda indicação sem análise. A mãe ou o próprio filho, representado ou assistido quando necessário, também podem buscar Defensoria Pública ou advocacia particular para avaliar a ação.\n\nA averiguação não é requisito obrigatório para o filho exercer o direito de investigação, nem sua frustração prova por si só a paternidade.",
                ),
                section(
                    "A ação judicial permite DNA e outras provas",
                    "Na investigação, o suposto pai é citado e pode se defender. O juiz pode determinar DNA, ouvir testemunhas e examinar mensagens, fotografias e documentos do período da concepção. Recusa injustificada ao exame gera presunção relativa, não certeza automática. Citação por edital é excepcional e depende de buscas adequadas; não basta afirmar que o endereço mudou.\n\nCompetência e partes variam conforme domicílios, idade, cumulação com alimentos e eventual falecimento do investigado. Não há foro único que possa ser prometido em todos os casos.",
                ),
                section(
                    "Alimentos antes do DNA dependem de indícios e decisão",
                    "É possível cumular alimentos com a investigação e pedir tutela provisória quando houver suporte probatório, mas o pagamento não nasce automaticamente da indicação no cartório. Ao reconhecer a paternidade em sentença, a Lei 8.560/1992 manda fixar alimentos provisionais ou definitivos ao reconhecido que deles necessite. Valor e termo inicial devem seguir a decisão e a jurisprudência aplicável.\n\nO silêncio na averiguação também não autoriza prisão. Prisão civil pressupõe obrigação alimentar judicialmente exigível e inadimplemento submetido ao procedimento próprio.",
                ),
                section(
                    "Documentos úteis e atendimento sem promessa",
                    "Certidão atualizada, comprovante da indicação, dados lícitos para localização, mensagens preservadas e nomes de testemunhas ajudam a decidir a etapa seguinte. Um atendimento particular pode organizar prova, pedidos e competência; a Defensoria atende quem preencher seus critérios. Nenhum canal sério deve garantir reconhecimento, prazo curto ou exame gratuito antes de verificar o caso e a estrutura local.\n\nSe o filho já atingiu a maioridade, a iniciativa e o consentimento passam a ser tratados segundo sua própria posição jurídica, e a mãe não substitui automaticamente sua vontade. Se o suposto pai morreu, a averiguação administrativa deixa de oferecer o mesmo caminho de reconhecimento pessoal: a investigação post mortem precisa ser dirigida a todos os herdeiros e pode utilizar DNA de parentes consanguíneos. Esses cenários devem ser identificados antes de insistir em notificações inadequadas.\n\nO registro sem o nome paterno não reduz direitos civis da criança nem autoriza constrangimento no atendimento público. A busca pela filiação deve preservar intimidade e evitar divulgação do nome do indicado fora dos canais necessários.",
                ),
            ],
            [
                faq(
                    "O suposto pai pode ser preso por ignorar a notificação do cartório?",
                    "Não. O silêncio pode encerrar a averiguação sem reconhecimento e levar à análise de uma investigação, mas não constitui dívida alimentar nem autoriza prisão por si só.",
                )
            ],
            [
                source("fam-pai-se-recusa-registrar", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm#art2", "Lei 8.560/1992, art. 2º", "disciplina indicação, notificação, reconhecimento e remessa ao Ministério Público na averiguação"),
                source("fam-pai-se-recusa-registrar", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1606", "Código Civil, art. 1.606", "fundamenta a ação de prova da filiação proposta pelo filho"),
                source("fam-pai-se-recusa-registrar", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "consolida o procedimento registral de indicação e reconhecimento voluntário"),
            ],
            ["investigação de paternidade", "recusa ao DNA", "alimentos na investigação"],
        ),
        build(
            "fam-direito-origem-genetica",
            "Pessoa adotada pode conhecer a origem biológica?",
            "Saiba como o art. 48 do ECA garante acesso à origem e ao processo de adoção e por que conhecer os dados não altera sozinho a filiação adotiva.",
            "Direito da pessoa adotada de conhecer a origem biológica",
            "Conhecer a própria origem é direito da pessoa adotada, não favor dos pais nem autorização para exposição pública. O art. 48 do Estatuto da Criança e do Adolescente assegura acesso ao processo após os 18 anos e admite acesso anterior com orientação e assistência jurídica e psicológica. A busca por informação não desfaz a adoção nem cria automaticamente uma segunda filiação.",
            [
                section(
                    "Acesso após os 18 anos pertence ao adotado",
                    "A pessoa maior pode requerer ao juízo competente acesso irrestrito ao processo de adoção e conhecimento da origem biológica. Não depende de anuência dos pais adotivos. Identificação do processo, certidão atualizada e documentos pessoais ajudam a localizar autos antigos, físicos ou digitais. Se o feito tramitou sob sigilo, o pedido é apresentado nos próprios canais judiciais, não em redes sociais ou cadastros informais.\n\nAntes dos 18 anos, o parágrafo único do art. 48 exige assistência jurídica e psicológica para que o acesso ocorra de modo compatível com a idade e a proteção da pessoa adotada.",
                ),
                section(
                    "Sigilo da entrega não apaga o direito da criança",
                    "O Informativo 835 do STJ, ao tratar da entrega voluntária e do sigilo da gestante, ressalta que a proteção do nascimento não exclui o direito fundamental da criança à origem genética; o exercício é postergado nos termos do art. 48. Isso evita transformar o sigilo devido durante a entrega em apagamento definitivo da história pessoal.\n\nO acesso deve respeitar dados de terceiros e as determinações do juízo. Conhecer identidade não significa autorização para divulgar documentos protegidos.",
                ),
                section(
                    "Informação e estado de filiação são planos distintos",
                    "O art. 41 do ECA estabelece que a adoção atribui condição de filho e desliga o adotado dos pais e parentes anteriores, salvo impedimentos matrimoniais. Por isso, obter nomes, histórico médico e circunstâncias do nascimento não restabelece sozinho alimentos ou sucessão com a família biológica. Eventual pretensão de filiação ou multiparentalidade exige ação própria, legitimidade, prova e análise do caso; não é consequência automática da abertura dos autos.",
                ),
                section(
                    "Busca responsável preserva autonomia e segurança",
                    "É útil definir se o objetivo é informação médica, cópia do processo, contato ou discussão de estado. Equipe técnica pode ajudar a preparar impactos emocionais e limites de aproximação. Advocacia particular ou Defensoria podem localizar o processo e formular o pedido, sem prometer encontro, reciprocidade ou efeito patrimonial. Contato com familiares deve respeitar vontade, privacidade e segurança de todos, especialmente quando houver pessoa menor.",
                ),
            ],
            [
                faq(
                    "Os pais adotivos precisam autorizar o acesso do adulto?",
                    "Não. Depois dos 18 anos, o direito de acessar o processo e conhecer a origem pertence ao adotado; o juízo apenas organiza o acesso aos autos sigilosos.",
                )
            ],
            [
                source("fam-direito-origem-genetica", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art48", "Estatuto da Criança e do Adolescente, art. 48", "garante conhecimento da origem biológica e acesso ao processo de adoção"),
                source("fam-direito-origem-genetica", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art41", "Estatuto da Criança e do Adolescente, art. 41", "define os efeitos da adoção sobre o estado de filiação e os vínculos anteriores"),
                source("fam-direito-origem-genetica", "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D021160", "STJ, Informativo 835", "distingue o sigilo da entrega do direito posterior da criança de conhecer a origem"),
            ],
            ["processo de adoção", "multiparentalidade", "adoção à brasileira"],
        ),
        build(
            "fam-abandono-afetivo-indenizacao",
            "Abandono afetivo: requisitos para indenização",
            "Entenda por que a responsabilidade é excepcional e exige omissão ilícita no dever de cuidado, dano e nexo causal, além de prova adequada.",
            "Quando a omissão parental pode gerar reparação civil",
            "Indenização por abandono afetivo não cobra amor nem pune toda relação distante. A responsabilidade aparece em situações graves nas quais o genitor descumpre dever jurídico de cuidado e causa dano demonstrável ao filho. O STJ admite a reparação, mas os elementos da responsabilidade civil precisam ser provados; separação dos pais, conflito familiar ou contato imperfeito não bastam.",
            [
                section(
                    "Cuidado é dever jurídico, afeto espontâneo não é",
                    "O art. 22 do Estatuto da Criança e do Adolescente atribui aos pais deveres de sustento, guarda, convivência, assistência material e afetiva e educação. Os arts. 186 e 927 do Código Civil tratam do ato ilícito e da obrigação de reparar. A análise não exige que alguém sinta determinada emoção, mas verifica se houve omissão voluntária e injustificada em deveres concretos de proteção e formação do filho.\n\nPagar pensão não esgota automaticamente todos os deveres parentais; por outro lado, atraso alimentar isolado também não prova dano moral por abandono. Cada obrigação e cada consequência precisam ser separadas.",
                ),
                section(
                    "REsp 1.159.242 reconheceu a possibilidade, não uma regra automática",
                    "O precedente destacado pelo STJ no Informativo Extraordinário 17 afirma que a omissão do genitor no dever de cuidar pode caracterizar dano moral compensável. O caso é referência para a possibilidade jurídica, não tabela para toda ausência. Conduta ilícita, dano e relação causal permanecem necessários, e outros julgados podem afastar indenização quando a prova não revela abandono qualificado.\n\nExpressões como falta de amor ou ausência em comemorações ajudam a narrar a história, mas não substituem fatos objetivos sobre cuidado, capacidade de presença e consequências sofridas.",
                ),
                section(
                    "Conduta deve ser examinada no contexto familiar",
                    "É preciso reconstruir oportunidades reais de convivência, tentativas de contato, impedimentos criados por terceiros, distância, doença, violência, decisões de guarda e conhecimento da filiação. Um genitor que desconhecia justificadamente a paternidade não está na mesma situação de quem sabia, tinha condições e recusou toda responsabilidade. Alienação parental alegada sem prova não apaga a omissão, assim como conflito com o outro genitor não autoriza abandonar o filho.\n\nA análise deve evitar culpar a criança ou exigir que ela tenha insistido em receber cuidado.",
                ),
                section(
                    "Dano e nexo causal exigem prova compatível",
                    "Prontuários, relatórios de acompanhamento psicológico, documentos escolares e testemunhas podem demonstrar consequências e contexto. Laudo psicológico não é requisito mecânico em toda ação, mas pedidos baseados em sofrimento psíquico precisam de prova capaz de relacionar o dano à conduta apontada. A ausência de mensagens, sozinha, é difícil de provar e deve ser combinada com fontes positivas, como decisões, comunicações preservadas e depoimentos.\n\nDocumentos de saúde devem ser usados com consentimento e proteção da intimidade. Exposição pública do conflito pode ampliar o dano e não substitui prova judicial.",
                ),
                section(
                    "Valor, competência e prazo não admitem promessa genérica",
                    "Não há valor tabelado. Gravidade, duração, consequências e funções compensatória e pedagógica são avaliadas no caso, sem transformar indenização em preço da relação familiar. A unidade judicial competente pode depender da organização local e da forma do pedido, por isso não é correto prometer uma vara específica em todo o país.\n\nPretensões indenizatórias também se submetem a prescrição. O termo inicial pode envolver maioridade e circunstâncias do dano, e deve ser calculado com datas e jurisprudência aplicável, sem concluir apenas pela idade atual do filho.",
                ),
                section(
                    "Triagem jurídica deve testar os três elementos",
                    "Uma linha do tempo com reconhecimento da filiação, guarda, alimentos, contatos, decisões e acompanhamento de saúde permite avaliar conduta, dano e nexo separadamente. A advocacia particular pode organizar essa prova e estimar riscos, mas não deve garantir condenação nem usar a dor como captação. Quem preencher os critérios pode procurar a Defensoria Pública. O atendimento inicial digital não elimina perícia ou audiência eventualmente determinadas.\n\nTambém é preciso distinguir reparação civil de outras respostas. Execução de alimentos cobra parcelas fixadas; regulamentação de convivência organiza contato; perda ou suspensão do poder familiar protege a criança em hipóteses legais. A indenização não substitui essas medidas nem restaura por si mesma a relação. Se a pessoa ainda é menor e enfrenta risco atual, a prioridade pode estar na proteção imediata, e não em calcular dano moral futuro. Escolher a pretensão errada pode expor a família sem enfrentar o problema presente.",
                ),
            ],
            [
                faq(
                    "Filho adulto pode buscar reparação por fatos da infância?",
                    "A maioridade não exclui automaticamente a pretensão, mas prescrição, prova do dano e nexo causal precisam ser avaliados pelas datas e circunstâncias concretas.",
                )
            ],
            [
                source("fam-abandono-afetivo-indenizacao", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art927", "Código Civil, arts. 186 e 927", "fundamenta ato ilícito, dano, nexo causal e dever de reparar"),
                source("fam-abandono-afetivo-indenizacao", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art22", "Estatuto da Criança e do Adolescente, art. 22", "define deveres parentais de sustento, guarda, convivência, assistência e educação"),
                source("fam-abandono-afetivo-indenizacao", "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&b=INFJ&livre=RESP+1.159.242-SP&operador=mesmo&p=true&thesaurus=JURIDICO", "STJ, Informativo Extraordinário 17 e REsp 1.159.242", "reconhece a possibilidade de dano moral pela omissão no dever jurídico de cuidado"),
            ],
            ["responsabilidade civil familiar", "pensão alimentícia", "convivência entre pais e filhos"],
        ),
        build(
            "fam-dna-gratuito",
            "Exame de DNA e gratuidade da justiça",
            "Veja como pedir gratuidade para a perícia genética, o alcance da declaração de insuficiência e por que o laboratório é definido no processo.",
            "Como pedir custeio do DNA pela gratuidade judicial",
            "Quem não consegue pagar as despesas do processo sem comprometer o próprio sustento pode pedir gratuidade da justiça. O benefício abrange honorários de perito e custo do exame de DNA judicial, mas depende de decisão e não dá liberdade para escolher qualquer laboratório particular ou exigir reembolso de teste feito antes da ação.",
            [
                section(
                    "CPC inclui a perícia entre as despesas abrangidas",
                    "O art. 98 do Código de Processo Civil assegura gratuidade à pessoa com insuficiência de recursos e inclui os honorários do perito. O pedido pode constar da petição inicial, da defesa ou de manifestação posterior quando a necessidade surgir. Para pessoa natural, a alegação de insuficiência tem presunção relativa; se os autos trouxerem elementos contrários, o juiz deve oportunizar comprovação antes de indeferir.\n\nExtratos, renda, despesas familiares e situação de trabalho podem ser solicitados. Não existe um valor nacional único de renda que resolva todos os pedidos.",
                ),
                section(
                    "O juízo organiza laboratório, data e pagamento",
                    "Deferido o benefício e determinada a prova, o exame segue a estrutura disponível ao tribunal: laboratório credenciado, órgão público, universidade conveniada ou perito nomeado. As partes recebem instruções de coleta e identificação. Fazer teste particular sem autorização não obriga o Estado a pagar nem garante que o laudo seja aceito como perícia judicial.\n\nA gratuidade afasta adiantamento nos limites da decisão, mas não muda o dever de comparecer nem a consequência probatória de recusa injustificada.",
                ),
                section(
                    "Defensoria, Ministério Público e advocacia têm papéis distintos",
                    "A Defensoria Pública presta assistência a quem satisfaz seus critérios e pode formular investigação e gratuidade. Na averiguação oficiosa de menor, a Lei 8.560/1992 prevê remessa ao Ministério Público para avaliar ação quando houver elementos suficientes. Também é possível contratar advocacia particular e ainda pedir gratuidade, pois benefício processual e modalidade de representação não são a mesma coisa.\n\nNa falta de unidade local da Defensoria, a alternativa institucional varia; cartório judicial pode informar canais, mas não presta consulta jurídica.",
                ),
                section(
                    "Benefício pode ser parcial ou revisto",
                    "O juiz pode conceder gratuidade integral, parcial ou parcelamento, conforme a capacidade demonstrada. Se surgirem provas de que os requisitos não existiam ou deixaram de existir, a decisão pode ser revista com contraditório. Isso não autoriza cobrança informal pelo laboratório nem cancelamento unilateral da coleta. Antes de agir, guarde a decisão, a nomeação do perito e as intimações sobre o exame.",
                ),
            ],
            [
                faq(
                    "Contratar advogado particular impede a gratuidade?",
                    "Não por si só. A lei manda analisar a insuficiência para as despesas do processo; o contrato particular pode ser considerado entre os dados econômicos, sem criar impedimento automático.",
                )
            ],
            [
                source("fam-dna-gratuito", "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art98", "Código de Processo Civil, arts. 98 e 99", "abrange perícia na gratuidade e rege pedido, presunção e possibilidade de comprovação"),
                source("fam-dna-gratuito", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm", "Lei 8.560/1992", "disciplina a investigação na qual a prova genética pode ser determinada"),
            ],
            ["investigação de paternidade", "recusa ao exame de DNA", "Defensoria Pública"],
        ),
        build(
            "fam-retificar-certidao-nascimento",
            "Retificação de certidão: cartório ou Justiça?",
            "Entenda quando erro evidente pode ser corrigido pelo oficial, quais documentos apresentar e quando a alteração exige procedimento judicial.",
            "Como corrigir dados no registro de nascimento",
            "A via correta depende da natureza do dado, não apenas de ele parecer simples ao interessado. O art. 110 da Lei de Registros Públicos permite ao oficial corrigir erro que possa ser constatado imediatamente e não exija indagação. Alterações que dependam de prova, disputa ou decisão sobre estado da pessoa seguem o art. 109 e passam pelo Judiciário.",
            [
                section(
                    "Erro evidente pode ser corrigido administrativamente",
                    "Erros de grafia, transposição de número, inexatidão de data demonstrada pelo próprio arquivo do cartório e falha de transposição do livro para a certidão podem caber no art. 110. O ponto decisivo é a certeza objetiva obtida dos documentos e assentamentos, sem investigar fatos controvertidos. O oficial pode agir de ofício ou a requerimento e deve indicar os elementos que justificam a correção.\n\nNem toda diferença entre documentos é erro evidente. A grafia usada por anos, a omissão de sobrenome ou divergência de local de nascimento pode exigir reconstrução da origem e não deve ser prometida como ato imediato.",
                ),
                section(
                    "Pedido começa pelo assento e pela prova do dado correto",
                    "Certidão atualizada, documento de identidade e registros anteriores coerentes ajudam a demonstrar a inexatidão. O interessado deve explicar qual campo está errado, qual informação pretende inserir e de onde vem a prova. O cartório que mantém o assento decide a qualificação; outra serventia pode orientar sobre envio eletrônico quando houver serviço disponível, sem garantia de que todo pedido seja resolvido no balcão mais próximo.\n\nSe faltar documento, o oficial pode formular exigência fundamentada em vez de simplesmente alterar o livro.",
                ),
                section(
                    "Filiação e mudanças complexas seguem outras regras",
                    "Incluir ou excluir pai, mudar estado de filiação, rever adoção ou resolver dúvida sobre identidade não é correção material. Reconhecimento voluntário válido, sentença de investigação ou decisão de desconstituição fornecem títulos próprios para averbação. Alteração de prenome, sobrenome e gênero também possui disciplina específica na Lei de Registros Públicos e nas normas nacionais, que não deve ser confundida com o art. 110.\n\nO fato de a nova informação ser verdadeira não torna dispensável o procedimento exigido para prová-la.",
                ),
                section(
                    "Art. 109 cobre retificação que exige decisão",
                    "Quando o pedido requer indagação, prova testemunhal, perícia ou afeta interesse de terceiro, a retificação judicial é apresentada com documentos e indicação precisa do assento. O Ministério Público participa nos termos da lei, e interessados podem ser ouvidos. A sentença determina ao registro a alteração autorizada; ela não permite mudanças além do que foi decidido.\n\nCompetência e representação dependem do pedido e da organização judiciária, sem promessa de vara ou prazo nacional.",
                ),
                section(
                    "Custos e nova certidão devem ser discriminados",
                    "Gratuidade e emolumentos variam conforme natureza do ato e legislação aplicável. O interessado pode pedir ao cartório indicação escrita do fundamento de eventual cobrança e da exigência. Depois da averbação, é prudente emitir certidão atualizada e conferir o resultado antes de corrigir outros documentos. Uma orientação jurídica é útil quando a nota devolutiva revela controvérsia, não para garantir deferimento administrativo.",
                ),
            ],
            [
                faq(
                    "Erro na certidão de pessoa falecida pode ser corrigido?",
                    "Pode haver legitimidade de interessado para pedir a correção, mas o cartório ou o juízo examinará interesse, prova e via adequada; o falecimento não transforma alteração complexa em erro evidente.",
                )
            ],
            [
                source("fam-retificar-certidao-nascimento", "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art110", "Lei de Registros Públicos, art. 110", "autoriza correção administrativa de erro constatável sem indagação"),
                source("fam-retificar-certidao-nascimento", "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art109", "Lei de Registros Públicos, art. 109", "disciplina a retificação judicial quando a alteração exige prova e decisão"),
            ],
            ["reconhecimento de paternidade", "alteração de nome", "anulação do registro"],
        ),
        build(
            "fam-inseminacao-caseira-paternidade",
            "Inseminação caseira: filiação não tem resposta automática",
            "Entenda por que DNA, acordo de doação e projeto parental são avaliados em conjunto e por que a filiação do doador conhecido pode ser controvertida.",
            "Como a inseminação caseira afeta a discussão de filiação",
            "A inseminação realizada fora de serviço de reprodução assistida não possui, hoje, uma regra nacional única que transforme o doador conhecido automaticamente em pai ou que o exclua automaticamente da filiação. O método biológico, o projeto parental, os consentimentos, a configuração familiar e os direitos da criança podem entrar em disputa. Por isso, não é seguro anunciar o resultado antes de examinar documentos e jurisprudência do caso.",
            [
                section(
                    "Regime documental da clínica não se transfere por analogia simples",
                    "O Código Nacional de Normas do CNJ permite registrar filhos de reprodução assistida com documentação do serviço: declaração de nascido vivo, declaração do diretor técnico na técnica heteróloga e prova da relação dos beneficiários, quando aplicável. A Resolução CFM 2.320/2022 disciplina práticas médicas e consentimento em clínicas. Na inseminação doméstica, esses documentos técnicos normalmente não existem, e o cartório pode não ter o título previsto para lançar diretamente o projeto parental.\n\nEssa ausência cria necessidade de qualificação ou decisão; não prova, sozinha, que o doador é pai.",
                ),
                section(
                    "DNA demonstra origem genética, não resolve sozinho o estado",
                    "Um exame pode confirmar a contribuição genética do doador, mas filiação jurídica em reprodução planejada envolve também vontade procriacional, consentimento do casal ou da pessoa beneficiária e interesse da criança. O artigo 1597 do Código Civil trata de presunções na reprodução assistida dentro de hipóteses conjugais, sem oferecer resposta completa para todo arranjo doméstico. Tribunais podem valorar de modo diferente doações informais, relações afetivas e pedidos formulados depois do nascimento.\n\nAssim, nem a criança nem o doador devem ser tratados como se a sentença já estivesse definida.",
                ),
                section(
                    "Acordo privado é prova, mas não controla direito de terceiro",
                    "Mensagens e instrumento assinado podem demonstrar intenção de doar material sem assumir parentalidade, consentimento do parceiro e planejamento da concepção. Eles não podem renunciar em nome da criança a direitos indisponíveis nem obrigar o juiz a ignorar o contexto. Também devem ser examinados autenticidade, data, clareza e conduta posterior.\n\nA recomendação responsável é preservar registros honestos do projeto parental e informações médicas relevantes. Não se deve orientar o afastamento entre doador e criança como técnica para fabricar ausência de vínculo; contato e cuidado são decisões humanas e podem ter efeitos que exigem análise própria.",
                ),
                section(
                    "Registro e controvérsia exigem solução individualizada",
                    "Antes do nascimento, orientação pode mapear documentação, reconhecimento pelo integrante do projeto parental e alternativas clínicas regulares. Depois do nascimento, certidão, consentimentos, histórico da concepção e convivência ajudam a definir se há via cartorial ou necessidade judicial. Advocacia particular pode conduzir essa análise com discrição, sem prometer exclusão do doador, reconhecimento de outro genitor ou resultado patrimonial. O direito da criança à identidade e à origem deve permanecer no centro.",
                ),
            ],
            [
                faq(
                    "Um contrato assinado impede investigação futura?",
                    "Não oferece impedimento absoluto. Ele pode provar a intenção dos adultos, mas o juiz examina o conjunto, a natureza indisponível da filiação e os direitos da criança.",
                )
            ],
            [
                source("fam-inseminacao-caseira-paternidade", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1597", "Código Civil, art. 1.597", "trata das presunções de filiação em hipóteses de reprodução assistida"),
                source("fam-inseminacao-caseira-paternidade", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "define a documentação registral da reprodução assistida realizada por clínica ou serviço"),
                source("fam-inseminacao-caseira-paternidade", "https://sistemas.cfm.org.br/normas/visualizar/resolucoes/BR/2022/2320", "CFM, Resolução 2.320/2022", "disciplina consentimentos e práticas médicas de reprodução assistida no ambiente clínico"),
            ],
            ["registro por reprodução assistida", "direito à origem genética", "multiparentalidade"],
        ),
        build(
            "fam-registro-reproducao-assistida",
            "Registro de filho por reprodução assistida heteróloga",
            "Veja quais documentos o CNJ exige, quem comparece ao cartório e por que o doador de material genético não integra a filiação registral.",
            "Como registrar a criança concebida com material doado",
            "Na reprodução assistida heteróloga realizada em clínica, a filiação registral acompanha o projeto parental documentado, e não exige que o doador compareça ou seja identificado na certidão. O Código Nacional de Normas do CNJ permite o registro sem autorização judicial prévia quando os beneficiários apresentam os documentos exigidos e a situação se enquadra na disciplina nacional.",
            [
                section(
                    "Comparecimento dos pais e situação do casal",
                    "Em regra, ambos os pais comparecem ao registro civil. Se forem casados ou viverem em união estável, um deles pode praticar o ato apresentando a documentação exigida. Para casal homoafetivo, o assento deve trazer os ascendentes sem distinção inadequada entre linha paterna e materna. A qualificação depende da certidão ou escritura que demonstre casamento ou união estável, quando essa for a configuração do projeto parental.\n\nA norma deve ser aplicada à situação real; não se deve inventar vínculo conjugal apenas para completar documentos.",
                ),
                section(
                    "DNV e declaração do diretor técnico são centrais",
                    "O art. 513 do Código Nacional de Normas exige declaração de nascido vivo e, na técnica heteróloga, declaração com firma reconhecida do diretor técnico da clínica, centro ou serviço. O documento informa que houve reprodução assistida heteróloga e identifica os beneficiários. Também se apresenta prova de casamento ou união estável nos casos previstos. O cartório arquiva a documentação que fundamentou o registro.\n\nRecibo do tratamento, contrato isolado ou mensagem do médico não substituem automaticamente a declaração técnica no formato exigido.",
                ),
                section(
                    "Doador não precisa ser identificado pelo registrador",
                    "O art. 479 impede o oficial de exigir a identificação do doador como condição para registrar a criança. O conhecimento posterior da ascendência biológica não cria, por si só, vínculo de parentesco nem efeitos jurídicos entre doador e filho gerado pela técnica, conforme o art. 513, § 3º. Isso não elimina regras médicas de guarda de dados nem questões de saúde e origem que possam ser tratadas pelos canais adequados.\n\nA Resolução CFM 2.320/2022 disciplina sigilo, consentimento e responsabilidade dos serviços médicos, sem transformar o doador em declarante do nascimento.",
                ),
                section(
                    "Falta de documento deve gerar exigência clara",
                    "Atendidos os requisitos nacionais, o registrador não pode recusar o registro. Se faltar declaração, houver divergência de nomes ou a concepção ocorreu fora de serviço formal, o oficial pode formular exigência ou submeter dúvida ao juízo competente; isso é diferente de exigir adoção automática. Antes do parto, vale conferir com a clínica se os termos identificam corretamente os beneficiários. Orientação jurídica particular pode tratar uma recusa concreta, sem garantir solução administrativa para arranjo não documentado.",
                ),
            ],
            [
                faq(
                    "O doador assina a certidão ou o termo de registro?",
                    "Não. No procedimento formal, a declaração vem do diretor técnico e identifica os beneficiários; o registrador não pode condicionar o ato à identificação do doador.",
                )
            ],
            [
                source("fam-registro-reproducao-assistida", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "arts. 479 e 512 a 515 regem documentos, comparecimento e ausência de vínculo com o doador"),
                source("fam-registro-reproducao-assistida", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1597", "Código Civil, art. 1.597", "trata das presunções de filiação relacionadas à reprodução assistida"),
                source("fam-registro-reproducao-assistida", "https://sistemas.cfm.org.br/normas/visualizar/resolucoes/BR/2022/2320", "CFM, Resolução 2.320/2022", "disciplina consentimento, doação e responsabilidade médica em reprodução assistida"),
            ],
            ["inseminação caseira", "gestação por substituição", "direito à origem genética"],
        ),
        build(
            "fam-barriga-solidaria-registro",
            "Gestação por substituição: requisitos e registro",
            "Entenda as regras da Resolução CFM 2.320/2022 para a cedente temporária, a autorização excepcional e os documentos do registro civil.",
            "Quais regras valem para a gestação por substituição",
            "A gestação por substituição é procedimento de reprodução assistida sujeito a requisitos médicos e registrais. Não basta um acordo privado entre interessados. A Resolução CFM 2.320/2022 exige que a cedente temporária tenha ao menos um filho vivo, pertença à família de um dos parceiros até o quarto grau consanguíneo ou obtenha autorização excepcional do Conselho Regional de Medicina, e proíbe caráter lucrativo ou comercial.",
            [
                section(
                    "Cedente precisa cumprir filiação e parentesco definidos pelo CFM",
                    "A cedente temporária do útero deve ter pelo menos um filho vivo. Também deve ser parente consanguínea de até quarto grau de um dos parceiros do projeto parental. A resolução alcança, dentro do limite, mãe ou filha, avó ou irmã, tia ou sobrinha e prima, observada a classificação civil do parentesco. Quando não houver esse vínculo, a clínica não pode tratar a exceção como liberada por simples declaração: o caso depende de autorização do Conselho Regional de Medicina.\n\nA avaliação médica continua necessária mesmo quando o parentesco existe; ele não substitui segurança clínica e consentimento informado.",
                ),
                section(
                    "Pagamento pela gestação é vedado",
                    "A cessão temporária não pode ter caráter lucrativo ou comercial. Custos médicos e despesas documentadas precisam ser tratados de modo transparente, sem transformar compensação de gasto em preço pela entrega da criança. Contratos de remuneração não ganham validade apenas porque foram assinados. A clínica deve manter prontuário e termos de consentimento compatíveis com a resolução e orientar os participantes sobre riscos médicos e psicológicos.\n\nQuando a cedente é casada ou vive em união estável, a documentação exigida pelo CFM inclui aprovação do cônjuge ou companheiro.",
                ),
                section(
                    "Termos devem definir riscos e filiação antes do procedimento",
                    "A resolução exige documentação sobre aspectos biopsicossociais, riscos da gestação e puerpério, garantia de tratamento e acompanhamento médico e termo de compromisso entre pacientes e cedente sobre a filiação. Também há providências para o registro civil. Esses instrumentos não eliminam controle judicial em litígio, mas reduzem ambiguidades e demonstram o projeto parental formado antes da concepção.\n\nÉ imprudente iniciar o tratamento e tentar reconstruir consentimentos apenas depois da gravidez.",
                ),
                section(
                    "CNJ define documentos para o assento de nascimento",
                    "O Código Nacional de Normas exige declaração de nascido vivo, documentos da reprodução assistida e, na gestação por substituição, termo de compromisso firmado pela cedente esclarecendo a filiação. O nome da parturiente informado na DNV não constará como mãe no registro feito conforme o procedimento. O assento indicará os beneficiários do projeto parental, e os documentos permanecerão arquivados no cartório.\n\nDivergência documental ou situação fora das regras pode exigir qualificação adicional ou decisão judicial; não se deve prometer registro imediato.",
                ),
                section(
                    "Planejamento prévio protege todas as pessoas envolvidas",
                    "Clínica, cedente e beneficiários devem conferir parentesco, filho vivo, autorização excepcional, gratuidade, consentimentos e documentos registrais antes da transferência embrionária. Advocacia particular pode revisar os termos sem substituir a avaliação médica ou o CRM. Eventual conflito será decidido à luz da filiação, do projeto parental e do melhor interesse da criança, razão pela qual nenhum contrato autoriza prometer que uma futura disputa é impossível.",
                ),
            ],
            [
                faq(
                    "Uma amiga sem parentesco pode ser cedente?",
                    "Somente se o caso receber autorização do Conselho Regional de Medicina e cumprir os demais requisitos. A ausência de parentesco não pode ser suprida apenas por contrato entre as partes.",
                )
            ],
            [
                source("fam-barriga-solidaria-registro", "https://sistemas.cfm.org.br/normas/visualizar/resolucoes/BR/2022/2320", "CFM, Resolução 2.320/2022", "exige filho vivo, parentesco consanguíneo até quarto grau ou autorização do CRM e veda lucro"),
                source("fam-barriga-solidaria-registro", "https://atos.cnj.jus.br/atos/detalhar/5243", "CNJ, Provimento 149/2023 compilado", "arts. 512 e 513 definem o registro e o termo da cedente na gestação por substituição"),
            ],
            ["registro por reprodução assistida", "consentimento informado", "filiação por projeto parental"],
        ),
        build(
            "fam-adocao-unilateral-enteado",
            "Adoção unilateral de enteado: requisitos e efeitos",
            "Entenda consentimentos, avaliação judicial, dispensa de cadastro, possível estágio de convivência e substituição de apenas uma linha parental.",
            "Como funciona a adoção do enteado pelo padrasto ou madrasta",
            "A adoção unilateral permite ao cônjuge ou companheiro adotar o filho do outro e manter a filiação com esse genitor. A outra linha parental é substituída pela do adotante após decisão judicial. O vínculo de convivência é relevante, mas não elimina consentimentos, escuta da criança, avaliação técnica nem necessidade de resolver o poder familiar do genitor que será substituído.",
            [
                section(
                    "Art. 41 preserva o vínculo com o genitor parceiro",
                    "O art. 41, § 1º, do Estatuto da Criança e do Adolescente prevê que, quando um cônjuge ou companheiro adota o filho do outro, mantêm-se os vínculos de filiação entre o adotado e o genitor parceiro, bem como seus parentes. A decisão cria filiação plena com o adotante e rompe a linha anterior que ele substitui, ressalvados impedimentos matrimoniais. O artigo 1626 do Código Civil segue a mesma estrutura.\n\nNão é uma simples inclusão de padrasto ou madrasta ao registro. Quem deseja somar, e não substituir, deve avaliar filiação socioafetiva e multiparentalidade, institutos com pressupostos diferentes.",
                ),
                section(
                    "Consentimento dos pais e do adolescente",
                    "O art. 45 do ECA exige consentimento dos pais ou representantes legais e, se o adotando tiver mais de 12 anos, também seu consentimento colhido em audiência. O consentimento dos pais é dispensado quando eles são desconhecidos ou foram destituídos do poder familiar. Uma recusa do genitor não é ignorada apenas porque ele convive pouco: eventual destituição exige fundamento legal, prova, contraditório e decisão.\n\nA criança menor de 12 anos também deve ser ouvida de forma compatível com seu desenvolvimento sempre que possível, ainda que a lei reserve consentimento formal à faixa superior.",
                ),
                section(
                    "Cadastro de adoção é dispensado nessa hipótese",
                    "O art. 50, § 13, do ECA permite adoção em favor de candidato domiciliado no Brasil não cadastrado previamente quando se tratar de pedido unilateral. A dispensa evita fila incompatível com um vínculo familiar já existente, mas não dispensa habilitação moral, idoneidade, documentos ou estudo do melhor interesse. O juízo ainda verifica a relação entre adotante e enteado e a aptidão para assumir deveres permanentes.\n\nA adoção é irrevogável e não pode servir apenas para alterar sobrenome ou facilitar benefício.",
                ),
                section(
                    "Estágio de convivência pode ser dispensado pelo juiz",
                    "O ECA admite dispensar estágio de convivência quando o adotando já está sob tutela ou guarda legal do adotante por tempo suficiente para avaliar a relação. Convivência doméstica, por si só, não obriga a dispensa, e guarda de fato isolada não a garante. Equipe interprofissional pode realizar entrevistas, visitas e estudo psicossocial.\n\nNão há prazo nacional fixo: localização do outro genitor, prova sobre poder familiar e agenda técnica influenciam a duração, sem autorizar promessa de procedimento mais rápido que outras adoções.",
                ),
                section(
                    "Documentos devem contar a história familiar completa",
                    "Certidão do enteado, casamento ou união estável, documentos pessoais, comprovantes de convivência e cuidado, decisões de guarda e dados para localizar o outro genitor ajudam a instruir o pedido. Escola, saúde e testemunhas podem demonstrar responsabilidades reais. Se houver abandono alegado, devem ser apresentados fatos objetivos, não apenas ausência de fotografia ou conflito entre adultos.\n\nA competência para adoção de criança ou adolescente é exercida pelo órgão judicial da infância e juventude conforme a organização local. Adulto adotando segue disciplina própria.",
                ),
                section(
                    "Sentença orienta averbação e novos efeitos",
                    "Deferida a adoção, o mandado substitui no assento a linha biológica atingida pela linha adotiva e seus ascendentes, preservando o registro original conforme as normas nacionais. O adotado passa a ter direitos e deveres de filho perante o adotante, inclusive alimentos e sucessão. Esses efeitos não dependem de promessa privada nem podem ser desfeitos pelo fim do casamento com o genitor parceiro.\n\nOrientação particular pode organizar consentimentos e provas, mas deve deixar claro que equipe técnica e juiz decidem pelo interesse do adotando. A relação com irmãos e avós da linha substituída também sofre efeitos jurídicos, ressalvados impedimentos matrimoniais; por isso, a família precisa compreender mais do que a troca de nome na certidão. Se o enteado já é adulto, seu consentimento e a disciplina da adoção de maiores são indispensáveis, e a análise não reproduz automaticamente todas as etapas voltadas a criança ou adolescente.",
                ),
            ],
            [
                faq(
                    "A oposição do outro genitor prova abandono?",
                    "Não. A oposição é manifestação processual. Abandono ou outra causa de perda do poder familiar exige fatos, prova e decisão; sem consentimento ou destituição, a adoção não pode ser prometida.",
                )
            ],
            [
                source("fam-adocao-unilateral-enteado", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art41", "Estatuto da Criança e do Adolescente, art. 41", "preserva a filiação com o genitor parceiro e cria vínculo pleno com o adotante"),
                source("fam-adocao-unilateral-enteado", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1626", "Código Civil, art. 1.626", "define os efeitos da adoção unilateral sobre as linhas de filiação"),
                source("fam-adocao-unilateral-enteado", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art45", "Estatuto da Criança e do Adolescente, art. 45", "rege consentimento dos pais e do adotando maior de 12 anos"),
                source("fam-adocao-unilateral-enteado", "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art50", "Estatuto da Criança e do Adolescente, art. 50", "prevê a exceção cadastral para adoção unilateral"),
            ],
            ["paternidade socioafetiva", "multiparentalidade", "destituição do poder familiar"],
        ),
        build(
            "fam-alimentos-com-investigacao",
            "Alimentos na investigação: termo inicial e tutela",
            "Entenda a Súmula 277 do STJ, a diferença entre alimentos provisórios e os fixados na sentença e como a cobrança retroativa é apurada.",
            "Desde quando há alimentos na investigação de paternidade",
            "A investigação pode ser cumulada com pedido alimentar, mas é preciso distinguir duas decisões. Antes do DNA, o juiz pode avaliar alimentos provisórios diante de indícios e urgência. Se a investigação for julgada procedente, a Súmula 277 do STJ determina que os alimentos sejam devidos desde a citação, e a sentença define valor e alcance do título.",
            [
                section(
                    "Súmula 277 fixa a citação após a procedência",
                    "O enunciado do STJ afirma: julgada procedente a investigação de paternidade, os alimentos são devidos a partir da citação. O marco evita limitar o dever apenas à data da sentença, mas pressupõe citação válida e reconhecimento da filiação. Não se deve calcular dívida desde o nascimento ou desde o primeiro contato sem título que autorize esse período.\n\nA data de citação precisa ser extraída dos autos. Comparecimento espontâneo, nulidade e pluralidade de pedidos podem exigir análise processual específica.",
                ),
                section(
                    "Art. 7º trata da sentença que reconhece a filiação",
                    "A Lei 8.560/1992 manda o juiz, sempre que reconhecer a paternidade na sentença de primeiro grau, fixar alimentos provisionais ou definitivos ao reconhecido que deles necessite. Esse dispositivo não diz que alimentos provisórios surgem automaticamente no início. A decisão deve examinar necessidade do filho e possibilidade do reconhecido pai, com dados de renda e despesas.\n\nSe o filho é maior, a necessidade não é presumida em todas as situações e deve ser demonstrada conforme estudo, saúde e capacidade de sustento.",
                ),
                section(
                    "Tutela anterior ao DNA exige suporte mínimo",
                    "A Lei de Alimentos permite ao juiz fixar alimentos provisórios ao despachar pedido adequadamente instruído. Em investigação, a incerteza sobre filiação exige indícios compatíveis, como relacionamento no período da concepção, reconhecimento informal ou outros documentos. A força necessária varia com o caso; a mera indicação do nome no cartório não garante pagamento. A decisão pode ser revista quando surgirem DNA, renda e novas provas.",
                ),
                section(
                    "Cobrança retroativa depende do título e da idade das parcelas",
                    "Depois da procedência, o débito entre citação e sentença é calculado pelo valor e pelos critérios definidos judicialmente, considerando eventuais quantias já pagas. O modo de execução não é único: prisão civil se limita às prestações recentes abrangidas pelo rito legal, enquanto parcelas antigas seguem cobrança patrimonial. Não é correto prometer prisão por todo o retroativo.\n\nPlanilha deve indicar competência mensal, índice, pagamentos e data da citação. Uma orientação particular pode revisar o cálculo e os documentos sem prometer valor ou medida coercitiva.",
                ),
            ],
            [
                faq(
                    "É possível receber alimentos antes do resultado do DNA?",
                    "É possível pedir tutela provisória, mas o juiz exige indícios e analisa necessidade e possibilidade. O ajuizamento, sozinho, não cria automaticamente a obrigação.",
                )
            ],
            [
                source("fam-alimentos-com-investigacao", "https://www.stj.jus.br/docs_internet/revista/eletronica/stj-revista-sumulas-2011_21_capSumula277.pdf", "STJ, Súmula 277", "fixa a citação como termo inicial dos alimentos quando a investigação é julgada procedente"),
                source("fam-alimentos-com-investigacao", "https://www.planalto.gov.br/ccivil_03/leis/l8560.htm#art7", "Lei 8.560/1992, art. 7º", "manda fixar alimentos na sentença de primeiro grau que reconhece a paternidade"),
                source("fam-alimentos-com-investigacao", "https://www.planalto.gov.br/ccivil_03/leis/l5478.htm#art4", "Lei de Alimentos, art. 4º", "fundamenta a avaliação de alimentos provisórios no início da demanda adequadamente instruída"),
            ],
            ["investigação de paternidade", "recusa ao exame de DNA", "execução de alimentos"],
        ),
    ]

    if [page["intent_id"] for page in pages] != [page["intent_id"] for page in originals]:
        raise SystemExit("ordem ou conjunto de intent_ids divergiu do shard original")

    generic_indexes = {
        "https://www.cnj.jus.br/atos_normativos/",
        "https://processo.stj.jus.br/repetitivos/temas_repetitivos/",
    }
    new_source_count = 0
    preserved_metadata_count = 0
    band_errors = []
    for page in pages:
        intent_id = page["intent_id"]
        page_type = PAGE_TYPES[intent_id]
        low, high = BANDS[page_type]
        count = body_word_count(page)
        if page["word_count"] != count or not low <= count <= high:
            band_errors.append(
                f"{intent_id}:tipo={page_type}:palavras={count}:faixa={low}-{high}"
            )
        if not 20 <= len(page["title"]) <= 65:
            raise SystemExit(f"título fora da faixa: {intent_id}")
        if not 70 <= len(page["meta_description"]) <= 160:
            raise SystemExit(f"meta fora da faixa: {intent_id} ({len(page['meta_description'])})")
        if page["title"].casefold() == page["h1"].casefold():
            raise SystemExit(f"title e h1 iguais: {intent_id}")
        if not 2 <= len(page["official_sources"]) <= 5:
            raise SystemExit(f"fontes fora da faixa: {intent_id}")
        if len(page["internal_link_topics"]) < 2:
            raise SystemExit(f"links internos insuficientes: {intent_id}")
        for item in page["official_sources"]:
            if item["url"] in generic_indexes:
                raise SystemExit(f"índice genérico residual: {intent_id}")
            previous = source_by_id[intent_id].get(item["url"])
            if previous is None:
                new_source_count += 1
                if "verified_at" in item or "http_status" in item:
                    raise SystemExit(f"metadata inventada em fonte nova: {intent_id} {item['url']}")
            else:
                if "verified_at" in item or "http_status" in item:
                    preserved_metadata_count += 1
                for field in ("verified_at", "http_status"):
                    if field in item and item[field] != previous.get(field):
                        raise SystemExit(f"metadata alterada: {intent_id} {item['url']} {field}")

    if band_errors:
        raise SystemExit("faixas inválidas: " + ", ".join(band_errors))

    corpus = "\n".join(
        part
        for page in pages
        for part in [page["opening"], *(item["text"] for item in page["sections"])]
    ).casefold()
    banned_claims = (
        "ação contra o espólio",
        "foro do domicílio do filho",
        "foro do domicílio do pai",
        "evitar qualquer contato contínuo entre o doador e a criança",
        "apenas obter benefício patrimonial",
        "até o segundo grau",
    )
    for phrase in banned_claims:
        if phrase in corpus:
            raise SystemExit(f"afirmação jurídica vedada residual: {phrase}")

    required_facts = (
        "todos os herdeiros",
        "lei 14.138/2021",
        "tema 1200",
        "tema 622",
        "acima de 12 anos",
        "pelo menos 16 anos",
        "parecer favorável do ministério público",
        "mais de um ascendente socioafetivo",
        "ao menos um filho vivo",
        "quarto grau consanguíneo",
        "conselho regional de medicina",
        "caráter lucrativo ou comercial",
        "súmula 301",
        "súmula 277",
        "ônus probatório como bipartido",
    )
    for phrase in required_facts:
        if phrase not in corpus:
            raise SystemExit(f"fato obrigatório ausente: {phrase}")

    payload = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    fd, temp_name = tempfile.mkstemp(
        dir=TARGET.parent, prefix=".familia-13.", suffix=".tmp"
    )
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())

    # CAS imediatamente antes da promoção; os.replace mantém o shard indivisível.
    observed = sha256(TARGET)
    if observed != EXPECTED_SHA256:
        raise SystemExit(
            f"familia-13 mudou durante a montagem: esperado={EXPECTED_SHA256} observado={observed}"
        )
    os.replace(temp_name, TARGET)
    directory_fd = os.open(TARGET.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)

    print(
        json.dumps(
            {
                "pages": len(pages),
                "initial_sha256": INITIAL_SHA256,
                "final_sha256": sha256(TARGET),
                "new_sources_without_live_metadata": new_source_count,
                "source_entries_with_preserved_exact_url_metadata": preserved_metadata_count,
                "word_count_min": min(page["word_count"] for page in pages),
                "word_count_max": max(page["word_count"] for page in pages),
                "word_count_total": sum(page["word_count"] for page in pages),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
