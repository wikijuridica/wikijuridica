#!/usr/bin/env python3
import json
import os
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/editorial/v2_pages/previdenciario-16.jsonl"
TARGET = "prev-revisao-vida-toda-situacao"
STF_THEME_1102 = (
    "https://portal.stf.jus.br/jurisprudenciaRepercussao/verAndamentoProcesso.asp?"
    "classeProcesso=RE&incidente=5945131&numeroProcesso=1276977&numeroTema=1102"
)
STF_MODULATION = (
    "https://noticias.stf.jus.br/postsnoticias/segurados-nao-precisam-devolver-valores-recebidos-do-inss-"
    "com-base-na-tese-da-revisao-da-vida-toda-decide-stf/"
)
STF_2025 = (
    "https://portal.stf.jus.br/textos/verTexto.asp?pagina=casos_notorios_2025&"
    "servico=jurisprudenciaPesquisaGeral"
)


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def word_count(page):
    parts = [page["opening"]]
    for item in page["sections"]:
        parts.extend((item["heading"], item["text"]))
    for item in page.get("faq", []):
        parts.extend((item["q"], item["a"]))
    return sum(len(re.findall(r"[^\W_]+", part, re.UNICODE)) for part in parts)


def main():
    pages = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    matches = [page for page in pages if page.get("intent_id") == TARGET]
    if len(matches) != 1:
        raise AssertionError(f"{TARGET}: count={len(matches)}")
    page = matches[0]
    page["title"] = "Revisão da vida toda: decisão atual do STF e efeitos"
    page["meta_description"] = (
        "O STF tornou obrigatória a regra de transição e superou a revisão da vida toda. Entenda a modulação para "
        "valores recebidos e ações pendentes."
    )
    page["h1"] = "Como ficou a revisão da vida toda depois da decisão final do STF"
    page["opening"] = (
        "A revisão da vida toda não está aberta para novos pedidos como esteve depois do julgamento de 2022. Ao julgar "
        "as ADIs 2110 e 2111 em 2024, o STF declarou constitucional e obrigatória a regra de transição do art. 3º da "
        "Lei 9.876/1999, que considera as contribuições posteriores a julho de 1994. O segurado enquadrado nessa regra "
        "não pode escolher o cálculo definitivo do art. 29 da Lei 8.213/1991, ainda que pareça mais vantajoso.\n\n"
        "Em 2025, o Tribunal concluiu a adequação do Tema 1102 a esse resultado. A discussão atual é sobre os efeitos "
        "protegidos pela modulação e a situação processual de cada ação já proposta, não sobre protocolar uma nova "
        "revisão com a tese superada."
    )
    page["sections"] = [
        {
            "heading": "Como a tese surgiu e por que o resultado mudou",
            "text": (
                "A Lei 9.876/1999 criou regra de transição para quem já era filiado ao RGPS: o período básico de cálculo "
                "passou a começar em julho de 1994. Em 2022, no RE 1.276.977, o STF havia admitido usar a regra definitiva "
                "quando ela fosse melhor, entendimento conhecido como revisão da vida toda. O quadro mudou em março de "
                "2024, quando o Plenário julgou as ADIs 2110 e 2111 e concluiu que o art. 3º deve ser aplicado de modo "
                "cogente. Por isso, a decisão mais recente superou a opção que havia sido reconhecida no Tema 1102."
            ),
        },
        {
            "heading": "A regra vinculante que vale hoje",
            "text": (
                "O resultado atual impede o segurado abrangido pela transição de escolher a fórmula definitiva dos arts. "
                "29, I e II, da Lei 8.213/1991. Contribuições anteriores a julho de 1994 não entram por uma opção judicial "
                "de cálculo mais favorável. Essa conclusão vincula os demais órgãos do Judiciário e a Administração. Uma "
                "simulação que mostre renda maior com salários antigos pode explicar o interesse econômico que existia, "
                "mas não cria exceção à regra obrigatória fixada pelo STF."
            ),
        },
        {
            "heading": "O que a modulação protegeu",
            "text": (
                "O STF preservou a irrepetibilidade dos valores recebidos por segurados em razão de decisões judiciais, "
                "definitivas ou provisórias, proferidas até 5 de abril de 2024. Em outras palavras, essas quantias não "
                "devem ser devolvidas apenas porque a tese mudou. O Tribunal também afastou, excepcionalmente, a cobrança "
                "de honorários de sucumbência, custas e perícias contábeis dos autores que tinham ações ainda pendentes de "
                "conclusão naquele marco. A proteção não equivale a autorizar um novo pedido depois da superação da tese."
            ),
        },
        {
            "heading": "A situação das ações já ajuizadas",
            "text": (
                "Processos em curso precisam aplicar o resultado vinculante e a modulação conforme a fase em que se "
                "encontram. Decisão provisória, pagamento já realizado, coisa julgada, cumprimento de sentença e data dos "
                "atos processuais produzem problemas diferentes; não é correto prometer manutenção futura ou encerramento "
                "automático sem ler os autos. Quem recebeu valores deve separar decisões e comprovantes de pagamento. Quem "
                "teve a ação encerrada deve conferir o alcance do título antes de cogitar qualquer medida processual."
            ),
        },
        {
            "heading": "Quando ainda faz sentido revisar o benefício",
            "text": (
                "A derrota da vida toda não elimina revisões baseadas em erros independentes, como vínculo ausente, salário "
                "registrado incorretamente, tempo especial não analisado ou aplicação errada da própria regra válida. Esses "
                "fundamentos têm provas, prazos e riscos próprios e não devem ser apresentados como continuação da tese "
                "superada. Um advogado previdenciário particular pode examinar o processo de concessão e comparar o CNIS "
                "com a memória de cálculo por atendimento digital, sem prometer a inclusão de salários anteriores a 1994 "
                "quando o caso está submetido ao art. 3º da Lei 9.876/1999."
            ),
        },
    ]
    page["faq"] = [
        {
            "q": "Ainda cabe ajuizar uma nova ação de revisão da vida toda?",
            "a": (
                "Não com a expectativa de escolher a regra definitiva por ser mais vantajosa. O STF tornou obrigatória "
                "a transição do art. 3º e superou a tese anterior. Outro erro de cálculo precisa ter fundamento autônomo."
            ),
        },
        {
            "q": "Quem recebeu valores por decisão judicial precisa devolver?",
            "a": (
                "O STF protegeu da devolução os valores recebidos com base em decisões definitivas ou provisórias "
                "proferidas até 5 de abril de 2024. A aplicação ao caso exige conferir decisão e datas do processo."
            ),
        },
    ]
    page["official_sources"] = [
        source(
            STF_THEME_1102,
            "STF — Tema 1102 da repercussão geral",
            "registra a superação da opção pela regra definitiva e a modulação dos efeitos",
        ),
        source(
            STF_MODULATION,
            "STF — modulação da revisão da vida toda",
            "explica a regra obrigatória e a proteção de valores recebidos até o marco de abril de 2024",
        ),
        source(
            STF_2025,
            "STF — julgamentos relevantes de 2025",
            "confirma o encerramento da tese e a impossibilidade de escolher o cálculo mais favorável",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l9876.htm#art3",
            "Lei 9.876/1999, art. 3º",
            "contém a regra de transição declarada obrigatória pelo STF",
        ),
    ]
    page["word_count"] = word_count(page)

    payload = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in pages)
    fd, temp_name = tempfile.mkstemp(prefix=PATH.name + ".", dir=PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, PATH)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    print(json.dumps({"intent": TARGET, "word_count": page["word_count"], "publication": False}))


if __name__ == "__main__":
    main()
