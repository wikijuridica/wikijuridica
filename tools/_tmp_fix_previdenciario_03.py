#!/usr/bin/env python3
import json
import os
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/editorial/v2_pages/previdenciario-03.jsonl"
BASE_PATH = Path("/tmp/previdenciario-03.before-root-fix.jsonl")
GENERIC_INSS = "https://www.gov.br/inss/pt-br"
INSS_SPECIAL = "https://www.gov.br/inss/pt-br/direitos-e-deveres/aposentadorias/aposentadoria-especial"
STF_VIGILANTE = (
    "https://portal.stf.jus.br/jurisprudenciarepercussao/"
    "verandamentoprocesso.asp?classeprocesso=re&incidente=6344761&"
    "numeroprocesso=1368225&numerotema=1209"
)
STJ_EPI = (
    "https://www.stj.jus.br/sites/portalp/Paginas/comunicacao/Noticias/2025/"
    "29042025-Anotacao-positiva-sobre-uso-de-EPI-afasta-risco-laboral-para-fins-de-aposentadoria-especial.aspx"
)
STJ_RUIDO = (
    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?"
    "cod_tema_final=694&cod_tema_inicial=694&novaConsulta=true&tipo_pesquisa=T"
)
STJ_RUIDO_NEN = (
    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?"
    "cod_tema_final=1083&cod_tema_inicial=1083&novaConsulta=true&tipo_pesquisa=T"
)
STJ_ELECTRICITY = (
    "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?"
    "cod_tema_final=534&cod_tema_inicial=534&novaConsulta=true&tipo_pesquisa=T"
)
STF_EPI = "https://portal.stf.jus.br/jurisprudenciarepercussao/tema.asp?num=555"
ADI_6309_STF = "https://portal.stf.jus.br/processos/detalhe.asp?incidente=5848987"
ADI_6309_MPS = (
    "https://www.gov.br/previdencia/pt-br/assuntos/rpps/julgamentos/"
    "adi-6309-idade-minima-para-aposentadoria-especial-no-rgps-conversao-de-tempo-e-calculo-dos-proventos"
)
INSS_IN_128 = "https://portalin.inss.gov.br/in/530"
RPS_ANNEX = "https://www.planalto.gov.br/ccivil_03/decreto/d3048anexoii-iii-iv.htm"
RPS_ART66 = "https://www.planalto.gov.br/ccivil_03/decreto/d3048compilado.htm#art66"
DECREE_53831 = "https://www.planalto.gov.br/ccivil_03/decreto/1950-1969/d53831.htm"


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def section(page, heading):
    matches = [item for item in page["sections"] if item["heading"] == heading]
    if len(matches) != 1:
        raise AssertionError(f"{page['intent_id']}: heading {heading!r} count={len(matches)}")
    return matches[0]


def body_word_count(page):
    parts = [page["opening"]]
    for item in page["sections"]:
        parts.extend((item["heading"], item["text"]))
    for item in page.get("faq", []):
        parts.extend((item["q"], item["a"]))
    return sum(len(re.findall(r"[^\W_]+", part, re.UNICODE)) for part in parts)


def replace_source(page, old_url, replacement):
    matches = [idx for idx, item in enumerate(page["official_sources"]) if item["url"] == old_url]
    if len(matches) != 1:
        raise AssertionError(f"{page['intent_id']}: source {old_url!r} count={len(matches)}")
    page["official_sources"][matches[0]] = replacement


def fix_overview(page):
    page["opening"] = (
        "A aposentadoria especial reduz o tempo contributivo exigido de quem comprova exposição efetiva, habitual "
        "e permanente a agentes prejudiciais à saúde. Conforme o enquadramento regulamentar, o período mínimo é de "
        "15, 20 ou 25 anos. Depois de 28 de abril de 1995, o nome do cargo não basta e a exposição precisa ser provada; "
        "cada fundamento segue o precedente aplicável. O Tema 1209 exclui a periculosidade da vigilância, enquanto o "
        "Tema 534 preserva o enquadramento da eletricidade comprovada. Até aquele marco, ainda pode haver enquadramento "
        "por categoria profissional conforme a norma vigente na época do trabalho.\n\n"
        "Em junho de 2026, o STF atualizou um ponto central desse regime. Na ADI 6309, declarou inconstitucionais "
        "as idades mínimas que a EC 103/2019 havia criado para a regra permanente, mas manteve a vedação de converter "
        "tempo especial posterior à reforma em comum e a nova fórmula de cálculo."
    )
    section(page, "A base legal do benefício")["text"] = (
        "Os arts. 57 e 58 da Lei 8.213/1991 tratam do tempo reduzido e da prova da exposição. A EC 103/2019 criou "
        "idades de 55, 58 e 60 anos no art. 19, § 1º, I, mas o STF afastou essas alíneas na ADI 6309, concluída em "
        "3 de junho de 2026. Como o julgamento é recente, requerimentos devem conferir a publicação do acórdão, "
        "eventual modulação e a atualização dos procedimentos administrativos, sem usar simuladores antigos como "
        "única resposta."
    )
    section(page, "Quais agentes contam como nocivos")["text"] = (
        "O regulamento lista agentes físicos, químicos e biológicos, como ruído acima do limite, calor, poeiras minerais, "
        "produtos cancerígenos, radiação ionizante e agentes biológicos em atividades específicas. A lista não transforma "
        "cargo em prova automática. Para fundamentos de periculosidade, o precedente também importa: o Tema 534 admite "
        "eletricidade comprovada, enquanto o Tema 1209 afastou a vigilância baseada somente no perigo."
    )
    section(page, "Como a exposição é provada")["text"] = (
        "Nos períodos sujeitos à prova técnica, o Perfil Profissiográfico Previdenciário é preenchido com base em "
        "laudo das condições ambientais. Para trabalho antigo, formulários e enquadramento por categoria devem ser "
        "avaliados segundo a legislação da época, inclusive o marco de 28 de abril de 1995. Exigir o PPP moderno "
        "como única prova de toda a carreira apagaria esse regime histórico."
    )
    page["faq"][0]["a"] = (
        "Não. No Tema 555, o STF decidiu que, demonstrada por medição a exposição acima do patamar normativo, a "
        "empresa não elimina a especialidade apenas ao assinalar proteção auricular eficaz no PPP."
    )
    page["official_sources"] = [
        item for item in page["official_sources"]
        if item["url"] not in {
            "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art19",
            "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm#art58",
        }
    ]
    page["official_sources"][0]["name"] = "Lei 8.213/1991, arts. 57 e 58"
    page["official_sources"][0]["anchor_claim"] = (
        "define o benefício e disciplina a comprovação da exposição efetiva"
    )
    page["official_sources"].extend([
        source(
            ADI_6309_STF,
            "STF — ADI 6309",
            "registra o julgamento que afastou as idades mínimas da regra permanente da aposentadoria especial",
        ),
        source(
            ADI_6309_MPS,
            "Ministério da Previdência — síntese oficial da ADI 6309",
            "delimita a queda da idade mínima e a manutenção da vedação de conversão e do novo cálculo",
        ),
        source(
            STF_EPI,
            "STF — Tema 555 da repercussão geral",
            "sustenta a exceção do ruído quanto à alegação de EPI eficaz",
        ),
        source(
            STJ_ELECTRICITY,
            "STJ — Tema repetitivo 534",
            "preserva o reconhecimento da eletricidade perigosa quando a exposição permanente é comprovada",
        ),
    ])


def fix_requirements(page):
    page["title"] = "Aposentadoria especial após a ADI 6309: requisitos atuais"
    page["meta_description"] = (
        "Entenda o que o STF mudou na aposentadoria especial em 2026, quais tempos de exposição permanecem e por "
        "que os procedimentos do INSS precisam ser conferidos."
    )
    page["h1"] = "Requisitos atuais da aposentadoria especial depois da ADI 6309"
    page["opening"] = (
        "A EC 103/2019 criou idades mínimas de 55, 58 e 60 anos para a aposentadoria especial de quem se filiou ao "
        "RGPS depois da reforma. Em 3 de junho de 2026, porém, o STF concluiu a ADI 6309 e declarou inconstitucionais "
        "essas exigências do art. 19, § 1º, I.\n\n"
        "Continuam relevantes os tempos mínimos de 15, 20 ou 25 anos de efetiva exposição, a carência e a prova "
        "técnica. A decisão manteve a vedação de converter em tempo comum o período especial posterior à reforma e "
        "preservou o novo cálculo do benefício. Quem já havia completado todos os requisitos até 13 de novembro de "
        "2019 conserva o direito adquirido à regra anterior."
    )
    age = section(page, "As três idades da regra permanente")
    age["heading"] = "O que a ADI 6309 retirou da regra permanente"
    age["text"] = (
        "O julgamento afastou as alíneas que combinavam 55 anos com o grupo de 15 anos, 58 com o de 20 e 60 com o "
        "de 25. A síntese oficial do Ministério da Previdência informa que o STF considerou a idade incompatível com "
        "a finalidade de retirar o trabalhador da exposição nociva depois de cumprido o período especial."
    )
    page["sections"].insert(1, {
        "heading": "Efeitos da reforma preservados no julgamento",
        "text": (
            "O STF não restaurou todo o regime anterior a 2019. A síntese oficial registra que continuaram válidos "
            "a proibição de converter em tempo comum a exposição posterior à EC 103 e o coeficiente novo de cálculo. "
            "Também permanecem a carência, o tempo mínimo do grupo e a demonstração por PPP e laudo. A mudança é "
            "delimitada: retira a barreira etária da regra permanente, sem transformar tempo nocivo em benefício "
            "automático nem assegurar renda de 100% da média."
        ),
    })
    regimes = section(page, "Quem cai na regra permanente e quem cai na transição")
    regimes["heading"] = "Direito adquirido, transição e regra permanente"
    regimes["text"] = (
        "Há três situações distintas. Quem completou os requisitos até 13/11/2019 conserva o direito adquirido do art. "
        "3º da EC 103. O segurado já filiado naquela data, mas ainda sem requisitos completos, usa a transição do art. "
        "21, com 66, 76 ou 86 pontos e o mínimo especial correspondente. Quem se filiou a partir de 14/11/2019 estava "
        "no art. 19, cujas idades mínimas foram afastadas pela ADI 6309. A decisão não invalidou a pontuação da transição."
    )
    docs = section(page, "Documentos que sustentam o pedido pela regra combinada")
    docs["heading"] = "Documentos que continuam indispensáveis"
    docs["text"] = (
        "Para períodos recentes, o PPP deve identificar agente, intensidade quando exigida e tempo de exposição com "
        "suporte técnico. Até 28 de abril de 1995, porém, o enquadramento por categoria profissional e os formulários "
        "da época também precisam ser considerados. CNIS e contribuições demonstram carência e tempo total, sem "
        "presumir que todo período de exposição corresponde a contribuição válida. Um "
        "advogado previdenciário particular pode revisar esses marcos por atendimento digital, sem prometer implantação "
        "antes da análise administrativa."
    )
    implementation = section(page, "Situações em que o pedido esbarra na idade mínima")
    implementation["heading"] = "Como tratar uma negativa baseada apenas na idade"
    implementation["text"] = (
        "Uma decisão administrativa que repita apenas as idades do art. 19 precisa ser confrontada com a ADI 6309. "
        "Como o julgamento é recente, também se deve conferir acórdão, trânsito, eventual modulação e atos de "
        "adaptação do INSS na data do requerimento. Isso evita tanto aceitar uma regra já afastada quanto prometer "
        "efeito retroativo ou concessão automática sem examinar o processo."
    )
    section(page, "Um exemplo prático do cálculo combinado")["text"] = (
        "Uma pessoa filiada em 2020 que trabalha no grupo de 25 anos continuará projetando a data em que completará "
        "25 anos de exposição e a carência. Depois da ADI 6309, a projeção não deve acrescentar automaticamente uma "
        "idade de 60 anos. Já o filiado em 2018 pertence à transição e precisa cumprir os 86 pontos, além dos 25 anos "
        "especiais, pois os dois públicos não são alternativas livremente escolhidas."
    )
    page["faq"][0]["q"] = "O PPP é obrigatório para todo período especial antigo?"
    page["faq"][0]["a"] = (
        "Não como regra única e retroativa. Até 28 de abril de 1995 pode existir enquadramento por categoria "
        "profissional, e a prova segue os formulários e requisitos vigentes quando o trabalho foi prestado. Para "
        "períodos posteriores, PPP e suporte técnico assumem papel central."
    )
    page["faq"][1]["q"] = "O simulador do INSS já reflete a ADI 6309?"
    page["faq"][1]["a"] = (
        "Não se deve presumir. O resultado precisa ser comparado com o julgamento e com os atos administrativos "
        "vigentes na data da consulta, porque sistemas e instruções podem levar tempo para ser atualizados."
    )
    replace_source(
        page,
        "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm",
        source(
            "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art21",
            "EC 103/2019, art. 21",
            "limita a transição à filiação ao RGPS até a reforma, sem exigir exposição especial anterior",
        ),
    )
    page["official_sources"] = [
        source(
            "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art3",
            "EC 103/2019, art. 3º",
            "preserva o direito adquirido de quem completou os requisitos antes da reforma",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art21",
            "EC 103/2019, art. 21",
            "define a transição por pontos para quem já era filiado ao RGPS",
        ),
        source(
            INSS_IN_128,
            "IN INSS 128/2022, arts. 260 a 262",
            "separa os públicos dos arts. 19 e 21 e preserva o regime probatório histórico",
        ),
        source(ADI_6309_STF, "STF — ADI 6309", "registra a procedência parcial que afastou as idades do art. 19"),
        source(
            ADI_6309_MPS,
            "Ministério da Previdência — síntese oficial da ADI 6309",
            "delimita o que foi afastado e o que permaneceu válido na reforma",
        ),
    ]


def fix_transition(page):
    page["meta_description"] = (
        "Entenda a transição da aposentadoria especial, que soma idade e tempo total de contribuição e exige "
        "15, 20 ou 25 anos de efetiva exposição."
    )
    page["opening"] = (
        "Quem já era filiado ao RGPS em 13 de novembro de 2019 pode usar a transição da aposentadoria especial, "
        "mesmo que a exposição nociva tenha começado depois. A conta soma idade e tempo total de contribuição para "
        "alcançar 66, 76 ou 86 pontos, mas mantém, separadamente, o mínimo de 15, 20 ou 25 anos de efetiva exposição.\n\n"
        "Tempo comum ajuda na pontuação; não substitui o período especial mínimo. Separar essas duas contas evita "
        "indeferimentos causados pela leitura equivocada de que apenas idade e anos no agente nocivo entram na soma."
    )
    section(page, "Como a pontuação é calculada")["text"] = (
        "O art. 21 da Emenda Constitucional 103/2019 soma idade e tempo de contribuição, inclusive períodos comuns, "
        "e exige 66 pontos com 15 anos de exposição, 76 pontos com 20 anos ou 86 pontos com 25 anos. Não há idade "
        "mínima isolada nessa transição, mas a pontuação não dispensa o tempo especial mínimo do grupo."
    )
    section(page, "Quem tem acesso a essa transição")["text"] = (
        "Pode usar a transição quem já era filiado ao RGPS em 13/11/2019. O texto constitucional não condiciona "
        "esse acesso ao exercício de atividade especial antes da reforma. Quem se filiou somente depois daquela data "
        "não entra no art. 21; para esse público, a ADI 6309 afastou as idades do art. 19, mas não dispensou o tempo "
        "especial, a carência nem a prova técnica."
    )
    proof = section(page, "Provas necessárias para reconhecer o período anterior a 2019")
    proof["heading"] = "Provas do tempo especial e do tempo total"
    proof["text"] = (
        "Para períodos posteriores a 28 de abril de 1995, PPP e suporte técnico demonstram a efetiva exposição que "
        "cumpre o mínimo especial. Até esse marco, o enquadramento por categoria profissional e os formulários da "
        "época devem ser avaliados conforme a legislação vigente durante o trabalho. CNIS, carteiras de trabalho e "
        "comprovantes de recolhimento documentam também os períodos comuns que entram na pontuação, mas não completam "
        "os 15, 20 ou 25 anos de exposição."
    )
    section(page, "Um exemplo de como a soma funciona na prática")["text"] = (
        "Uma segurada pré-filiada com 60 anos de idade, 26 anos de contribuição total e 25 anos reconhecidos como "
        "especiais soma 86 pontos e cumpre também o mínimo do grupo de 25 anos. Outra pessoa com 58 anos, 30 anos "
        "de contribuição e apenas 23 anos de exposição soma 88 pontos, mas ainda não pode obter a especial porque "
        "faltam dois anos do requisito nocivo mínimo."
    )
    comparison = section(page, "Quando a transição por pontos não é a melhor escolha")
    comparison["heading"] = "O que a ADI 6309 não afastou expressamente"
    comparison["text"] = (
        "A síntese oficial da ADI 6309 identifica como inconstitucionais as idades do art. 19, § 1º, I, e informa que "
        "a vedação de conversão pós-reforma e o novo cálculo foram mantidos. Ela não declara inválidos os 66, 76 e "
        "86 pontos do art. 21. Para o segurado pré-filiado, portanto, a projeção deve continuar separando pontos e "
        "tempo especial até que o acórdão ou decisão posterior determine alcance diferente."
    )
    page["sections"].insert(3, {
        "heading": "Como o tempo comum entra sem virar tempo especial",
        "text": (
            "Vínculos administrativos, comerciais ou de outra atividade sem agente nocivo podem aumentar o tempo "
            "total usado nos pontos, desde que estejam reconhecidos no CNIS ou sejam comprovados. Eles continuam "
            "comuns e não reduzem os 15, 20 ou 25 anos de exposição exigidos. Períodos simultâneos também não devem "
            "ser contados duas vezes como se cada emprego acrescentasse um ano ao calendário. A memória de cálculo "
            "precisa mostrar, em colunas separadas, tempo total, tempo especial e idade na data projetada."
        ),
    })
    section(page, "Como reunir a documentação sem se perder no tempo")["text"] = (
        "A documentação deve ser organizada vínculo por vínculo e conforme a regra probatória de cada período. CNIS, "
        "carteiras e recolhimentos mostram o tempo total; formulários antigos, enquadramento profissional, PPP e laudos "
        "demonstram o tempo especial conforme a época. Um advogado previdenciário particular pode revisar essas peças "
        "por atendimento digital, sem prometer reconhecimento antes da análise administrativa ou judicial."
    )
    page["faq"][0]["a"] = (
        "Sim. O tempo comum entra na soma de idade e tempo total de contribuição, mas não substitui o mínimo de "
        "15, 20 ou 25 anos de efetiva exposição exigido para o grupo."
    )
    page["faq"][1]["a"] = (
        "Não. A regra exige a pontuação e o tempo especial mínimo do grupo, sem pedágio sobre o que faltava em 2019."
    )
    page["official_sources"][0]["anchor_claim"] = (
        "soma idade e tempo total de contribuição, com mínimo separado de 15, 20 ou 25 anos de exposição"
    )
    page["official_sources"][1]["anchor_claim"] = (
        "disciplina a prova técnica da exposição nos períodos em que esse regime probatório é aplicável"
    )
    page["official_sources"] = [
        item for item in page["official_sources"]
        if item["url"] not in {
            "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm",
            INSS_SPECIAL,
        }
    ]
    page["official_sources"].extend([
        source(
            INSS_IN_128,
            "IN INSS 128/2022, arts. 261 e 262",
            "preserva o enquadramento por categoria até 28 de abril de 1995 e a prova conforme a lei do período",
        ),
        source(ADI_6309_STF, "STF — ADI 6309", "permite conferir o alcance atual do julgamento sobre o art. 19"),
        source(
            ADI_6309_MPS,
            "Ministério da Previdência — síntese oficial da ADI 6309",
            "informa que a decisão afastou a idade permanente, sem declarar inválidos os pontos do art. 21",
        ),
    ])


def fix_noise(page):
    section(page, "Os limites de ruído por período")["text"] = (
        "A sucessão regulamentar considera exposição superior a 80 dB até 5 de março de 1997, superior a 90 dB de "
        "6 de março de 1997 a 18 de novembro de 2003 e superior a 85 dB desde 19 de novembro de 2003. No Tema 694, "
        "o STJ examinou especificamente o intervalo intermediário: confirmou o patamar superior a 90 dB e vedou "
        "retroagir o limite de 85 dB. Cada período deve ser comparado com a norma então vigente."
    )
    section(page, "Um exemplo de cálculo por período misto")["text"] = (
        "Se um operador trabalhou de 1995 a 2010 sob medição constante de 88 dB, o trecho até 5 de março de 1997 "
        "supera o limite de 80 dB e pode ser especial; de 6 de março de 1997 a 18 de novembro de 2003, 88 dB não "
        "supera os 90 dB então exigidos; desde 19 de novembro de 2003, volta a superar o limite de 85 dB. O PPP "
        "precisa permitir essa divisão temporal."
    )
    methodology = section(page, "A metodologia de medição que o INSS exige")
    methodology["text"] = (
        "De 19 de novembro a 31 de dezembro de 2003, a IN INSS 128 aceita o valor medido acima de 85 dB e torna o Nível "
        "de Exposição Normalizado facultativo. A partir de 1 de janeiro de 2004, a orientação administrativa exige NEN "
        "segundo a NHO-01 da Fundacentro. Para períodos anteriores, o STJ não exige NEN. Se o campo faltar e a especialidade "
        "for discutida em juízo, o Tema 1083 admite o nível máximo medido somente quando perícia judicial comprova "
        "habitualidade e permanência; média aritmética simples não substitui esses critérios."
    )
    epi = section(page, "O uso de protetor auricular não afasta o direito")
    epi["heading"] = "EPI e ruído acima do limite legal"
    epi["text"] = (
        "O Tema 555 do STF estabelece que, quando a medição comprova ruído acima do limite legal aplicável ao período, "
        "a declaração empresarial de EPI eficaz no PPP não descaracteriza o tempo especial. A tese não dispensa a "
        "medição nem transforma exposição abaixo do patamar em atividade especial."
    )
    page["faq"][2]["q"] = "A indicação de protetor auricular eficaz elimina o tempo especial por ruído?"
    page["faq"][2]["a"] = (
        "Não quando o ruído medido supera o limite legal do período. Nessa hipótese, o Tema 555 do STF impede que a "
        "declaração de EPI eficaz no PPP, sozinha, descaracterize a especialidade."
    )
    page["official_sources"] = [
        source(
            DECREE_53831,
            "Decreto 53.831/1964 — quadro anexo",
            "fundamenta o limite histórico superior a 80 dB até 5 de março de 1997",
        ),
        source(
            STJ_RUIDO,
            "STJ — Tema repetitivo 694",
            "confirma o limite superior a 90 dB no intervalo intermediário e veda retroagir 85 dB",
        ),
        source(
            STJ_RUIDO_NEN,
            "STJ — Tema repetitivo 1083",
            "define NEN e, na falta dele, o uso judicial do pico com perícia sobre habitualidade e permanência",
        ),
        source(
            STF_EPI,
            "STF — Tema 555 da repercussão geral",
            "qualifica a irrelevância da declaração de EPI eficaz quando o ruído supera o limite legal",
        ),
        source(
            INSS_IN_128,
            "IN INSS 128/2022 — medição de ruído",
            "distingue a janela final de 2003 e torna obrigatório o NEN a partir de 1 de janeiro de 2004",
        ),
    ]


def fix_vigilante(page):
    page["title"] = "Vigilante e aposentadoria especial após o Tema 1209 do STF"
    page["meta_description"] = (
        "O STF decidiu que vigilante, armado ou desarmado, não tem tempo especial só pela periculosidade. Veja o "
        "que ainda deve ser conferido no PPP."
    )
    page["h1"] = "Tema 1209: vigilância e tempo especial no RGPS"
    page["opening"] = (
        "O Supremo Tribunal Federal encerrou a controvérsia nacional sobre a periculosidade da vigilância. No "
        "Tema 1209, a Corte fixou que a atividade de vigilante, com ou sem arma de fogo, não se caracteriza como "
        "especial para a aposentadoria do art. 201, § 1º, da Constituição.\n\n"
        "A tese supera a orientação anterior que admitia o enquadramento pelo risco de violência. Porte de arma, "
        "transporte de valores ou trabalho em local sujeito a assalto não bastam, por si sós, para reconhecer o período."
    )
    page["sections"] = [
        {
            "heading": "A tese vinculante fixada pelo STF",
            "text": (
                "O Tema 1209 afirma expressamente que vigilante armado e vigilante desarmado não têm atividade "
                "especial apenas em razão da profissão ou do perigo. Como decisão de repercussão geral, a tese "
                "orienta os processos que discutem esse mesmo fundamento no RGPS."
            ),
        },
        {
            "heading": "Arma de fogo não muda o resultado pela periculosidade",
            "text": (
                "O porte de arma pode demonstrar risco ocupacional, mas o STF afastou justamente a periculosidade "
                "como fundamento autônomo para essa aposentadoria especial. Assim, documentos de porte, contrato de "
                "vigilância e registro de transporte de valores não substituem a prova de agente nocivo admitido."
            ),
        },
        {
            "heading": "Quando outro agente nocivo ainda precisa ser analisado",
            "text": (
                "A tese não impede o exame de exposição efetiva a agente físico, químico ou biológico prejudicial à "
                "saúde. Um vigilante que também trabalhou sob ruído acima do limite, por exemplo, precisa comprovar "
                "esse agente no PPP e no laudo técnico. Nesse caso, o fundamento é o ruído, não o cargo nem o risco de assalto."
            ),
        },
        {
            "heading": "Efeito sobre pedidos e processos em andamento",
            "text": (
                "Pedidos administrativos e ações ainda sem decisão definitiva devem ser avaliados à luz da tese do "
                "STF. Benefícios já concedidos e decisões transitadas em julgado exigem análise individual do ato e "
                "de sua estabilidade; a tese não autoriza concluir, sem examinar o processo, que haverá corte ou cobrança."
            ),
        },
        {
            "heading": "O que conferir no PPP antes de insistir no pedido",
            "text": (
                "É preciso separar referências a arma, violência e periculosidade de medições ou descrições de "
                "agentes nocivos à saúde. Se o PPP registra apenas a função de vigilante e o porte de arma, falta o "
                "fundamento aceito pelo Tema 1209. Se registra outro agente, a intensidade, a habitualidade e o período "
                "devem ser conferidos pelas regras próprias desse agente."
            ),
        },
        {
            "heading": "Como refazer a projeção previdenciária",
            "text": (
                "Períodos antes tratados como especiais somente pela vigilância devem ser retirados dessa coluna "
                "até que exista prova de outro agente nocivo. Eles ainda podem contar como tempo comum e participar "
                "de uma aposentadoria por idade ou de transição comum, conforme a filiação e os demais requisitos. "
                "Refazer a projeção evita protocolar uma aposentadoria especial sustentada por tese já rejeitada e "
                "permite identificar períodos independentes que continuam juridicamente aproveitáveis."
            ),
        },
        {
            "heading": "Por que o precedente anterior não resolve o caso atual",
            "text": (
                "Antes do julgamento do STF, o STJ admitia reconhecer a vigilância perigosa mediante prova da "
                "atividade, inclusive depois de 1995. O Tema 1209 examinou essa controvérsia em repercussão geral e "
                "fixou a tese contrária. Citar apenas decisões antigas, sem enfrentar o precedente constitucional "
                "posterior, cria uma expectativa que já não corresponde ao parâmetro vinculante."
            ),
        },
        {
            "heading": "Periculosidade trabalhista não equivale a tempo especial",
            "text": (
                "O eventual direito a adicional de periculosidade na relação de emprego tem finalidade e requisitos "
                "próprios. Ele não transforma automaticamente o período em especial no RGPS. Depois do Tema 1209, "
                "receber adicional, portar arma ou atuar em transporte de valores não substitui a demonstração de um "
                "agente prejudicial à saúde aceito pela legislação previdenciária."
            ),
        },
        {
            "heading": "Como revisar um caso baseado na jurisprudência anterior",
            "text": (
                "Quem recebeu negativa ou tem ação pendente baseada apenas na periculosidade precisa recalcular a "
                "estratégia, verificar outros períodos contributivos e procurar eventual agente nocivo independente. "
                "Um advogado previdenciário particular pode revisar o PPP e as decisões já proferidas por atendimento "
                "digital, sem prometer que o antigo fundamento continuará válido depois da tese vinculante."
            ),
        },
    ]
    page["faq"] = [
        {
            "q": "Vigilante armado ainda consegue tempo especial apenas pelo porte de arma?",
            "a": "Não. O Tema 1209 inclui expressamente a vigilância com arma e afasta a periculosidade como fundamento autônomo.",
        },
        {
            "q": "Um vigilante exposto a ruído pode ter o período reconhecido?",
            "a": (
                "Pode, se o ruído superar o limite da época e estiver tecnicamente comprovado. O reconhecimento será "
                "pelo agente físico, não pela atividade de vigilância."
            ),
        },
    ]
    page["official_sources"] = [
        source(
            STF_VIGILANTE,
            "STF — Tema 1209 da repercussão geral",
            "fixa que a atividade de vigilante, com ou sem arma de fogo, não caracteriza atividade especial",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm#art201",
            "Constituição Federal, art. 201, § 1º",
            "limita requisitos diferenciados à efetiva exposição a agentes prejudiciais à saúde previstos em lei complementar",
        ),
    ]


def fix_epi(page):
    page["opening"] = (
        "A anotação de EPI eficaz no PPP não é um detalhe neutro. O STJ, no Tema 1090, decidiu que essa informação "
        "afasta, em princípio, o tempo especial, ressalvadas situações excepcionais como a exposição a ruído. Para "
        "outros agentes, cabe ao segurado que contesta o formulário apresentar elementos concretos de inadequação ou "
        "ineficácia.\n\n"
        "Isso não torna a marcação incontestável. Falta de certificado, manutenção, substituição, higienização, "
        "treinamento ou adequação ao risco pode afastar a presunção; se a prova deixar dúvida real, a conclusão deve "
        "favorecer o segurado."
    )
    section(page, "Para outros agentes, a eficácia real importa")["text"] = (
        "Segundo o Tema 1090 do STJ, a informação positiva de EPI no PPP descaracteriza o tempo especial em princípio. "
        "Quem ajuíza a ação deve demonstrar inadequação ao risco, certificado irregular, falha de manutenção, troca ou "
        "higienização, treinamento insuficiente ou outro dado capaz de pôr a eficácia em dúvida. Não basta afirmar, de "
        "forma genérica, que toda marcação empresarial é inválida."
    )
    section(page, "Como contestar a marcação de EPI eficaz")["text"] = (
        "A contestação deve apontar o defeito verificável do equipamento ou de sua gestão. Na via judicial, o ônus "
        "inicial é do segurado; perícia, fichas de entrega, certificado e registros de treinamento ajudam a cumprir "
        "essa carga. Se a avaliação das provas revelar divergência ou dúvida sobre a eficácia real, o próprio Tema "
        "1090 determina solução favorável ao autor. A análise deve identificar o agente, o modelo fornecido e a "
        "rotina de uso, porque falhas distintas exigem provas diferentes."
    )
    noise = section(page, "A exceção do ruído: EPI nunca afasta o direito")
    noise["heading"] = "A exceção do ruído acima do limite legal"
    noise["text"] = (
        "Se o nível aferido excede o patamar normativo vigente naquele intervalo, o Tema 555 do STF estabelece que a "
        "declaração de EPI eficaz no PPP não descaracteriza o tempo especial. A exceção depende dessa exposição "
        "objetivamente acima do patamar; não dispensa medição nem abrange, de forma automática, qualquer ambiente ruidoso."
    )
    page["official_sources"].append(source(
        STJ_EPI,
        "STJ — Tema repetitivo 1090",
        "define a presunção da anotação positiva, o ônus probatório do segurado e a solução favorável em caso de dúvida",
    ))
    page["official_sources"].append(source(
        STF_EPI,
        "STF — Tema 555 da repercussão geral",
        "fixa que a declaração de EPI eficaz não descaracteriza o tempo especial por ruído acima dos limites",
    ))


def fix_radiation(page):
    page["opening"] = (
        "Técnicos de radiologia, dentistas e outros profissionais que operam equipamentos de raio-X podem ficar "
        "expostos a radiação ionizante, agente expressamente previsto no Anexo IV do Decreto 3.048/1999. O enquadramento "
        "atual é no grupo de 25 anos, e não no grupo de 15 anos.\n\n"
        "A profissão, sozinha, não basta. Nos períodos sujeitos à prova técnica, PPP e laudo devem demonstrar exposição "
        "efetiva, habitual e permanente; registros de dosimetria reforçam essa análise quando existem, mas sua ausência "
        "não impede automaticamente o reconhecimento."
    )
    first = section(page, "Por que a radiação ionizante garante tempo reduzido")
    first["heading"] = "Por que a radiação ionizante está no grupo de 25 anos"
    first["text"] = (
        "O código 2.0.3 do Anexo IV do Decreto 3.048/1999 lista os trabalhos com radiações ionizantes e fixa tempo "
        "de 25 anos. A gravidade do agente exige controle técnico rigoroso, mas não autoriza reduzir o requisito para "
        "15 anos, faixa reservada pelo regulamento à mineração subterrânea em frentes de produção."
    )
    section(page, "O monitoramento dosimétrico como prova central")["text"] = (
        "Profissionais expostos a radiação ionizante costumam usar dosímetro individual, que registra a dose recebida "
        "ao longo do tempo. Os relatórios fortalecem a prova, mas devem ser lidos com o PPP e o laudo técnico: é esse "
        "conjunto que identifica a fonte de radiação, a rotina de trabalho, as medidas de controle e a habitualidade "
        "da exposição durante cada vínculo."
    )
    example = section(page, "Um exemplo de reconhecimento pelo grupo de 15 anos")
    example["heading"] = "Um exemplo de reconhecimento pelo grupo de 25 anos"
    example["text"] = (
        "Um técnico de radiologia hospitalar com 25 anos operando aparelhos de raio-X e tomografia, PPP coerente e "
        "dosimetria que confirma exposição habitual pode cumprir o requisito temporal do grupo. Dezesseis anos de "
        "radiação ionizante, isoladamente, não completam o mínimo regulamentar de 25 anos."
    )
    replace_source(
        page,
        "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm",
        source(
            RPS_ANNEX,
            "Decreto 3.048/1999 — Anexo IV, código 2.0.3",
            "classifica trabalhos com radiações ionizantes no grupo de 25 anos",
        ),
    )
    page["faq"][1]["q"] = "Médico radiologista tem o mesmo tratamento que técnico de radiologia?"


def fix_miner(page):
    page["meta_description"] = (
        "Entenda o grupo de 15 anos para mineração subterrânea em frente de produção e o que a ADI 6309 mudou sobre "
        "a antiga idade mínima."
    )
    page["opening"] = (
        "O trabalho permanente no subsolo de mineração, em frente de produção, integra o grupo especial de 15 anos "
        "do Anexo IV. O enquadramento não alcança toda função de uma mineradora: local, tarefa e permanência precisam "
        "estar descritos no PPP e no laudo.\n\n"
        "A EC 103/2019 havia acrescentado idade mínima de 55 anos ao grupo na regra permanente. Em junho de 2026, "
        "o STF declarou essa exigência inconstitucional na ADI 6309, mantendo outros pontos da reforma, como o novo "
        "cálculo e a vedação de converter tempo especial posterior à reforma em comum."
    )
    section(page, "Por que o subsolo está no grupo de 15 anos")["text"] = (
        "O código 4.0.2 do Anexo IV reserva 15 anos aos trabalhos permanentes no subsolo de minerações subterrâneas "
        "em frente de produção. Atividade subterrânea afastada da frente pertence ao grupo de 20 anos, e trabalho "
        "na superfície depende de outro agente nocivo devidamente comprovado."
    )
    age = section(page, "A idade mínima de 55 anos na regra permanente")
    age["heading"] = "A queda da idade mínima de 55 anos"
    age["text"] = (
        "A alínea do art. 19 que combinava 55 anos de idade com 15 anos de exposição foi uma das declaradas "
        "inconstitucionais pelo STF. O tempo mínimo especial e a carência permanecem; como o julgamento é recente, "
        "é prudente conferir acórdão, eventual modulação e atualização administrativa antes de projetar a concessão."
    )
    example = section(page, "Um exemplo de transição por tempo anterior a 2019")
    example["heading"] = "Como ficam direito adquirido, transição e regra pós-reforma"
    example["text"] = (
        "Quem completou 15 anos na frente de produção e os demais requisitos até 13/11/2019 preserva o direito adquirido "
        "à regra anterior. O filiado até essa data que ainda não havia completado os requisitos usa a transição do art. "
        "21: precisa de 66 pontos, calculados pela idade mais o tempo total de contribuição, e de 15 anos na atividade. "
        "O pós-filiado não usa a transição e, após a ADI 6309, não deve receber automaticamente a idade de 55 anos; ainda "
        "precisa comprovar exposição, carência e o enquadramento especial."
    )
    page["faq"][1]["a"] = (
        "A transição usa a soma da idade com o tempo total de contribuição e exige, separadamente, 15 anos de efetiva "
        "exposição na frente de produção. Tempo comum pode aumentar os pontos, mas não completa o mínimo especial."
    )
    page["faq"][2]["a"] = (
        "A tabela regulamentar transforma cada período especial na equivalência do grupo predominante. Por isso, "
        "anos sujeitos aos patamares de 15, 20 e 25 não entram na conta pelo mesmo peso antes dessa conversão."
    )
    page["official_sources"] = [
        source(RPS_ANNEX, "Decreto 3.048/1999 — Anexo IV", "classifica a frente de produção subterrânea no grupo de 15 anos"),
        source(
            "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art3",
            "EC 103/2019, arts. 3º e 21",
            "preserva o direito adquirido e disciplina a transição por 66 pontos para o pré-filiado sem requisitos completos",
        ),
        source(RPS_ART66, "Decreto 3.048/1999, art. 66", "regula conversão entre grupos especiais distintos"),
        source(ADI_6309_STF, "STF — ADI 6309", "afasta a idade mínima de 55 anos do grupo permanente de 15 anos"),
        source(
            ADI_6309_MPS,
            "Ministério da Previdência — síntese oficial da ADI 6309",
            "confirma a queda da idade e a manutenção do novo cálculo e da vedação de conversão pós-reforma",
        ),
    ]


def fix_groups(page):
    section(page, "O grupo de 15 anos: os agentes mais graves")["text"] = (
        "O Anexo IV reserva o grupo de 15 anos aos trabalhos permanentes no subsolo de minerações subterrâneas em "
        "frentes de produção. Não é uma categoria aberta para qualquer agente considerado muito perigoso, e radiação "
        "ionizante não pertence a essa faixa."
    )
    section(page, "O grupo de 20 anos: uma faixa intermediária")["text"] = (
        "O grupo de 20 anos inclui, entre as hipóteses regulamentares, trabalhos com exposição a amianto (asbesto) e mineração "
        "subterrânea cujas atividades estejam afastadas das frentes de produção. Agentes biológicos não entram "
        "genericamente nessa faixa; o código 3.0.1 do Anexo IV prevê 25 anos."
    )
    section(page, "O grupo de 25 anos: a faixa mais comum")["text"] = (
        "A faixa de 25 anos abrange grande parte das exposições reconhecidas, como ruído acima do limite, radiações "
        "ionizantes e os agentes biológicos do código 3.0.1, além de outras hipóteses específicas do Anexo IV. O "
        "grupo deve ser identificado pelo código regulamentar e pela prova técnica do caso."
    )
    section(page, "Por que a mesma profissão pode cair em grupos diferentes")["text"] = (
        "Na mineração subterrânea, quem trabalha de modo permanente em frente de produção se enquadra no grupo de "
        "15 anos; atividades subterrâneas afastadas da frente pertencem ao grupo de 20 anos. O cargo genérico no "
        "registro não resolve a classificação: localização, tarefa e exposição descritas no PPP é que permitem "
        "aplicar o código correto."
    )
    page["faq"][0]["a"] = (
        "Sim, com técnica própria. O art. 66 do Decreto 3.048/1999 prevê tabela de conversão entre tempos especiais "
        "de 15, 20 e 25 anos quando a pessoa exerceu duas ou mais atividades especiais sem completar o mínimo em uma "
        "delas. Cada período precisa ser reconhecido e convertido para a atividade preponderante; não é soma livre "
        "sem os fatores regulamentares."
    )
    page["faq"][1]["a"] = (
        "Não depois do julgamento de junho de 2026. Na ADI 6309, o STF declarou inconstitucionais as idades de 55, "
        "58 e 60 anos que o art. 19 associava aos três grupos. O tempo especial do grupo, a carência e a prova da "
        "exposição continuam exigidos; a implementação administrativa deve ser conferida no caso concreto."
    )
    for item in page["official_sources"]:
        if item["url"] == "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc103.htm#art19":
            item["anchor_claim"] = "contém as idades do art. 19 posteriormente afastadas na ADI 6309"
    replace_source(
        page,
        "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm",
        source(
            RPS_ANNEX,
            "Decreto 3.048/1999 — Anexo IV",
            "distingue as atividades e os agentes dos grupos de 15, 20 e 25 anos",
        ),
    )
    page["official_sources"].append(source(
        RPS_ART66,
        "Decreto 3.048/1999, art. 66",
        "prevê a tabela de conversão entre períodos especiais de 15, 20 e 25 anos",
    ))
    page["official_sources"].extend([
        source(ADI_6309_STF, "STF — ADI 6309", "afasta as idades mínimas associadas aos grupos especiais"),
        source(
            ADI_6309_MPS,
            "Ministério da Previdência — síntese oficial da ADI 6309",
            "confirma a queda das idades e a preservação dos demais pontos indicados da reforma",
        ),
    ])


FIXES = {
    "prev-verbete-aposentadoria-especial": fix_overview,
    "prev-especial-requisitos-pos-reforma": fix_requirements,
    "prev-especial-transicao-pontos": fix_transition,
    "prev-especial-ruido": fix_noise,
    "prev-especial-vigilante": fix_vigilante,
    "prev-epi-eficaz-negativa": fix_epi,
    "prev-especial-raio-x-radiacao": fix_radiation,
    "prev-especial-mineiro-subsolo": fix_miner,
    "prev-especial-grupos-15-20-25": fix_groups,
}


def main():
    if not BASE_PATH.is_file():
        raise AssertionError(f"deterministic source snapshot missing: {BASE_PATH}")
    pages = [json.loads(line) for line in BASE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(pages) != 22:
        raise AssertionError(f"unexpected page count: {len(pages)}")
    ids = [page["intent_id"] for page in pages]
    missing = sorted(set(FIXES) - set(ids))
    if missing:
        raise AssertionError(f"missing targets: {missing}")
    generic_before = sum(
        item["url"] == GENERIC_INSS
        for page in pages
        for item in page["official_sources"]
    )
    if generic_before != 22:
        raise AssertionError(f"unexpected generic INSS count: {generic_before}")

    for page in pages:
        page["official_sources"] = [item for item in page["official_sources"] if item["url"] != GENERIC_INSS]
        if page["intent_id"] in FIXES:
            FIXES[page["intent_id"]](page)
            page["word_count"] = body_word_count(page)
        if page["intent_id"] == "prev-ppp-eletronico-esocial":
            page["official_sources"].append(source(
                INSS_SPECIAL,
                "INSS — Aposentadoria especial",
                "explica o uso do PPP para comprovar a exposição e requerer a aposentadoria especial",
            ))

    for page in pages:
        urls = [item["url"] for item in page["official_sources"]]
        if len(urls) < 2 or len(urls) != len(set(urls)):
            raise AssertionError(f"{page['intent_id']}: invalid source cardinality or duplicate: {urls}")
        if any(url == GENERIC_INSS for url in urls):
            raise AssertionError(f"{page['intent_id']}: generic INSS survived")

    data = "".join(json.dumps(page, ensure_ascii=False) + "\n" for page in pages)
    fd, temp_name = tempfile.mkstemp(prefix=PATH.name + ".", dir=PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, PATH)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

    print(
        json.dumps(
            {
                "file": str(PATH.relative_to(ROOT)),
                "pages": len(pages),
                "generic_sources_removed": generic_before,
                "legal_records_corrected": len(FIXES),
                "publication": False,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
