#!/usr/bin/env python3
"""Segunda passada atomica de PT-BR e lei vigente em imobiliario-02."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-02.jsonl"
EXPECTED_SHA256 = "df0541930ae0f931254cfa9655eaa4af68feea2dd6bdff33051a640b89c398c0"

STJ_RESP_1745916 = (
    "https://processo.stj.jus.br/processo/revista/documento/mediado/"
    "?num_registro=201801289623&tipo=ITA&formato=PDF"
)
STJ_RESP_77457 = (
    "https://processo.stj.jus.br/processo/revista/documento/mediado/"
    "?num_registro=199500547090&tipo=ITA&formato=PDF"
)
STJ_INFO_660 = (
    "https://processo.stj.jus.br/jurisprudencia/externo/informativo/"
    "?acao=pesquisar&livre=%40CNOT%3D%27017357%27#informativo-660"
)


WORD_ACCENTS = {
    "alugueis": "aluguéis",
    "analise": "análise",
    "aniversario": "aniversário",
    "anuncio": "anúncio",
    "apos": "após",
    "ate": "até",
    "beneficio": "benefício",
    "calculo": "cálculo",
    "calculos": "cálculos",
    "cambio": "câmbio",
    "circunstancia": "circunstância",
    "clausula": "cláusula",
    "clausulas": "cláusulas",
    "conferencia": "conferência",
    "copia": "cópia",
    "credito": "crédito",
    "creditos": "créditos",
    "cumulo": "cúmulo",
    "dai": "daí",
    "debito": "débito",
    "debitos": "débitos",
    "deposito": "depósito",
    "depositos": "depósitos",
    "distancia": "distância",
    "divida": "dívida",
    "dividas": "dívidas",
    "divorcio": "divórcio",
    "domicilio": "domicílio",
    "eficacia": "eficácia",
    "especifica": "específica",
    "especifico": "específico",
    "espolio": "espólio",
    "estrategia": "estratégia",
    "explicito": "explícito",
    "forcada": "forçada",
    "forcas": "forças",
    "formula": "fórmula",
    "ha": "há",
    "imoveis": "imóveis",
    "indice": "índice",
    "indices": "índices",
    "inicio": "início",
    "inventario": "inventário",
    "legitima": "legítima",
    "legitimo": "legítimo",
    "matricula": "matrícula",
    "matriculas": "matrículas",
    "memoria": "memória",
    "moveis": "móveis",
    "negocio": "negócio",
    "noticia": "notícia",
    "numero": "número",
    "numeros": "números",
    "paragrafo": "parágrafo",
    "patrimonio": "patrimônio",
    "pendencia": "pendência",
    "pendencias": "pendências",
    "pericia": "perícia",
    "periodica": "periódica",
    "politicas": "políticas",
    "porem": "porém",
    "pratica": "prática",
    "praticas": "práticas",
    "preferencia": "preferência",
    "premio": "prêmio",
    "providencia": "providência",
    "publico": "público",
    "referencia": "referência",
    "renuncia": "renúncia",
    "residencia": "residência",
    "revertera": "reverterá",
    "rotulo": "rótulo",
    "salario": "salário",
    "sera": "será",
    "serie": "série",
    "silencio": "silêncio",
    "socio": "sócio",
    "sumula": "súmula",
    "termino": "término",
    "titulo": "título",
    "titulos": "títulos",
    "transito": "trânsito",
    "ultima": "última",
    "ultimo": "último",
    "valida": "válida",
    "valido": "válido",
    "vicio": "vício",
    "vinculo": "vínculo",
    "vitoria": "vitória",
    "voluntaria": "voluntária",
    "voluntario": "voluntário",
    "aplicara": "aplicará",
    "definira": "definirá",
    "impedira": "impedirá",
    "prosseguira": "prosseguirá",
}


EXACT_LANGUAGE_REPLACEMENTS = {
    "denuncia-la": "denunciá-la",
    "aplica-lo": "aplicá-lo",
    "não e": "não é",
    "Não e": "Não é",
    "também e": "também é",
    "Também e": "Também é",
    "E preciso": "É preciso",
    "E necessário": "É necessário",
    "E indispensável": "É indispensável",
    "e necessário": "é necessário",
    "e indispensável": "é indispensável",
    "e possível": "é possível",
    "qual e": "qual é",
    "Qual e": "Qual é",
    "o ponto e": "o ponto é",
    "O ponto e": "O ponto é",
    "O prazo legal para a nova garantia e de": "O prazo legal para a nova garantia é de",
    "o limite e de três meses": "o limite é de três meses",
    "A quarta modalidade legal e a": "A quarta modalidade legal é a",
    "para negociação e diferente": "para negociação é diferente",
    "O prêmio e custo": "O prêmio é custo",
    "nada mais e devido": "nada mais é devido",
    "modalidade e essencial": "modalidade é essencial",
    "A poupança e destino legal": "A poupança é destino legal",
    "objetivo imediato e impedir": "objetivo imediato é impedir",
    "qual garantia e válida": "qual garantia é válida",
    "A cumulação e vedada": "A cumulação é vedada",
    "o segurado e o locador e o garantido e o locatário": "o segurado é o locador e o garantido é o locatário",
    "Falta de pagamento de aluguéis e cobertura básica": "Falta de pagamento de aluguéis é cobertura básica",
    "O seguro e acessório": "O seguro é acessório",
    "A apólice e cancelada": "A apólice é cancelada",
    "Quando a cobrança e feita": "Quando a cobrança é feita",
    "O artigo 786 do Código Civil ainda e a regra vigente": "O artigo 786 do Código Civil ainda é a regra vigente",
    "A quarta modalidade listada na Lei 8.245/1991 e a": "A quarta modalidade listada na Lei 8.245/1991 é a",
    "garantia e e residencial comum": "garantia e é residencial comum",
    "quando a garantia e ineficaz": "quando a garantia é ineficaz",
    "fiador e impreciso": "fiador é impreciso",
    "intervalo inferior a um ano e defeito": "intervalo inferior a um ano é defeito",
    "O objeto e ajustar": "O objeto é ajustar",
    "o IGP-M e sempre indevido": "o IGP-M é sempre indevido",
    "o triênio e requisito": "o triênio é requisito",
    "O triênio e requisito": "O triênio é requisito",
    "percentual anual e insuficiente": "percentual anual é insuficiente",
    "Durante períodos de alta, e comum": "Durante períodos de alta, é comum",
    "A referência e o mercado": "A referência é o mercado",
    "em geral, e aplicação automática": "em geral, é aplicação automática",
    "o aluguel provisório e sempre": "o aluguel provisório é sempre",
    "O aluguel provisório e sempre": "O aluguel provisório é sempre",
    "A diferença da sentença e cobrada": "A diferença da sentença é cobrada",
    "Se parte e incontroversa e outra": "Se parte é incontroversa e outra",
    "enquanto a divergência e julgada": "enquanto a divergência é julgada",
    "todo acréscimo e abusivo": "todo acréscimo é abusivo",
    "A multa de aluguel e sempre": "A multa de aluguel é sempre",
    "o resultado global e manifestamente": "o resultado global é manifestamente",
    "toda acumulação e proibida": "toda acumulação é proibida",
    "ainda e necessário examinar": "ainda é necessário examinar",
    "Duração do atraso e relevante": "Duração do atraso é relevante",
    "Transferência pelo empregador e exceção": "Transferência pelo empregador é exceção",
    "O artigo 57 e próprio": "O artigo 57 é próprio",
    "inferior a 30 meses e automática": "inferior a 30 meses é automática",
    "prazo de substituição e diferente": "prazo de substituição é diferente",
    "esta na": "está na",
    "esta no": "está no",
    "esta registrada": "está registrada",
    "esta registrado": "está registrado",
    "esta garantida": "está garantida",
    "esta preenchido": "está preenchido",
    "equivalem automaticamente a insolvência": "equivalem automaticamente à insolvência",
    "pertencem a relação": "pertencem à relação",
    "pertence a relação": "pertence à relação",
    "vincula as indenizações": "vincula às indenizações",
    "pertencem as condições": "pertencem às condições",
    "comunicação a sociedade": "comunicação à sociedade",
    "remete as exceções": "remete às exceções",
    "benefício a família": "benefício à família",
    "corresponde a Selic": "corresponde à Selic",
    "retroagir a citação": "retroagir à citação",
    "limitada as hipóteses": "limitada às hipóteses",
    "submetida ao artigo 47 e as hipóteses": "submetida ao artigo 47 e às hipóteses",
    "a fiança original as obrigações": "a fiança original às obrigações",
    "obrigações anteriores a morte": "obrigações anteriores à morte",
    "produto e as normas da capitalização": "produto e às normas da capitalização",
    "somada mecanicamente a atualização": "somada mecanicamente à atualização",
    "responder a notificação": "responder à notificação",
    "pertence a locação por prazo indeterminado": "pertence à locação por prazo indeterminado",
    "em conjunto a luz dos precedentes": "em conjunto à luz dos precedentes",
    "ligado a ocupação": "ligado à ocupação",
    "abre denuncia vazia": "abre denúncia vazia",
    "permite denuncia por escrito": "permite denúncia por escrito",
    "criar denuncia vazia": "criar denúncia vazia",
    "regras especificas do produto": "regras específicas do produto",
    "denuncia da locação": "denúncia da locação",
    "Por isso, a perda do abono e a multa não são sempre dupla punição.": "Por isso, combinar a perda do abono com a multa não configura sempre dupla punição.",
}


def preserve_case(source, replacement):
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def accent_words(value):
    if not isinstance(value, str):
        return value
    for old, new in WORD_ACCENTS.items():
        value = re.sub(
            rf"(?<!\w){re.escape(old)}(?!\w)",
            lambda match, replacement=new: preserve_case(match.group(0), replacement),
            value,
            flags=re.IGNORECASE,
        )
    for old, new in EXACT_LANGUAGE_REPLACEMENTS.items():
        value = re.sub(
            rf"(?<!\w){re.escape(old)}(?!\w)",
            new,
            value,
        )
    return value


def visible_fields(page):
    yield "title", page
    yield "meta_description", page
    yield "h1", page
    yield "opening", page
    for section in page.get("sections", []):
        yield "heading", section
        yield "text", section
    for item in page.get("faq", []):
        yield "q", item
        yield "a", item
    for source in page.get("official_sources", []):
        yield "name", source
        yield "anchor_claim", source


def replace_once(value, old, new, label):
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperava uma ocorrência, encontrou {count}")
    return value.replace(old, new)


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def apply_legal_fixes(pages):
    by_id = {page["intent_id"]: page for page in pages}

    page = by_id["imob-substituicao-garantia-exigida"]
    section = page["sections"][0]
    section["text"] = replace_once(
        section["text"],
        "Também não basta dizer que um imóvel usado na análise inicial foi vendido: o inciso III "
        "fala em alienação ou gravação de todos os imóveis do fiador, ou em mudança para outro "
        "município sem comunicação ao locador.",
        "Não basta vender um imóvel que serviu de referência na análise inicial: o inciso III "
        "se refere à alienação ou gravação de todos os imóveis do fiador, ou à mudança para outro "
        "município sem comunicação ao locador.",
        page["intent_id"],
    )
    page["sections"][3]["text"] += (
        " A responsabilidade residual depende da causa legal específica e não acompanha toda "
        "substituição prevista no artigo 40."
    )
    page["sections"][1]["text"] += " A contagem objetiva é de 30 dias."
    page["sections"][2]["text"] = replace_once(
        page["sections"][2]["text"],
        "caução equivalente a três meses de aluguel",
        "caução equivalente a três aluguéis",
        page["intent_id"],
    )

    page = by_id["imob-duas-garantias-vedacao"]
    page["sections"][1]["text"] += (
        " O locatário não escolhe automaticamente qual garantia subsiste."
    )
    page["sections"][2]["text"] = replace_once(
        page["sections"][2]["text"],
        "No REsp 2.233.511, julgado em 2026, o STJ distinguiu esse mecanismo das garantias "
        "contratuais: a fiança ajustada não exclui, por si, o penhor que decorre diretamente da lei.",
        "No REsp 2.233.511, julgado em 2026, o STJ distinguiu esse mecanismo das garantias "
        "contratuais: a fiança ajustada não exclui, por si, o penhor que decorre diretamente da lei. "
        "O penhor é garantia legal, não é garantia contratual.",
        page["intent_id"],
    )

    page = by_id["imob-seguro-fianca-regresso"]
    page["opening"] = replace_once(
        page["opening"],
        "O seguro-fiança protege o locador",
        "O seguro-fiança locatícia protege o locador",
        page["intent_id"],
    )
    page["sections"][1]["text"] = replace_once(
        page["sections"][1]["text"],
        "A Lei 15.040/2024 entrou em vigor em 11 de dezembro de 2025 e revogou os artigos 757 a "
        "802 do Código Civil. Seu artigo 94 estabelece",
        "A Lei 15.040/2024 entrou em vigor em 11 de dezembro de 2025. Seu artigo 133 revogou os "
        "artigos 757 a 802 do Código Civil, e o artigo 94 estabelece",
        page["intent_id"],
    )

    page = by_id["imob-titulo-capitalizacao-resgate"]
    page["sections"][1]["text"] = (
        "A Resolução CNSP 384/2020, arts. 32 e 33, reproduzida no manual técnico da SUSEP, "
        "define instrumento de garantia como título cuja provisão matemática assegura obrigação "
        "assumida pelo titular perante terceiro. O contrato principal deve prever o título como "
        "instrumento ou outra caução admitida. A cessão se aperfeiçoa no inadimplemento previsto, "
        "limitada à obrigação garantida.\n\n"
        "O resgate durante o contrato exige anuência do terceiro garantido. Isso explica por que "
        "a sociedade de capitalização pede prova de liberação; a exigência precisa corresponder "
        "ao documento assinado, e não a uma recusa sem motivo após o encerramento."
    )

    page = by_id["imob-desconto-pontualidade"]
    old_source = page["official_sources"][0]
    if "num_registro=201801289623" not in old_source["url"]:
        raise RuntimeError("fonte esperada do REsp 1.745.916 não encontrada")
    page["official_sources"][0] = source(
        STJ_RESP_1745916,
        old_source["name"],
        old_source["anchor_claim"],
    )

    page = by_id["imob-transferencia-trabalho-sem-multa"]
    if not any("num_registro=199500547090" in item["url"] for item in page["official_sources"]):
        page["official_sources"].append(source(
            STJ_RESP_77457,
            "STJ, REsp 77.457/SP",
            "exceção taxativa para transferência por empregador público ou privado e aviso de trinta dias",
        ))

    page = by_id["imob-morte-locatario-quem-fica"]
    page["sections"][1]["text"] = replace_once(
        page["sections"][1]["text"],
        "O artigo 11 não cria a janela de 30 dias e o residual de 120 dias do artigo 12, que trata "
        "de separação e divórcio.",
        "A disciplina da separação e do divórcio é distinta e não deve ser transportada para a "
        "sub-rogação por morte.",
        page["intent_id"],
    )
    page["sections"][2]["text"] = replace_once(
        page["sections"][2]["text"],
        "No REsp 439.945/RS, o STJ decidiu que a morte do locatário afiançado extingue a fiança "
        "para obrigações posteriores, apesar da sub-rogação prevista no artigo 11.",
        "No REsp 439.945/RS, o STJ decidiu que a fiança se extingue para obrigações posteriores, "
        "apesar da sub-rogação prevista no artigo 11, quando morre o locatário afiançado.",
        page["intent_id"],
    )
    page["sections"][3]["text"] += (
        " A comunicação documentada também evita cobranças dirigidas à pessoa errada."
    )

    page = by_id["imob-dividas-locatario-falecido"]
    page["sections"][0]["heading"] = "O espólio concentra as dívidas até a morte"
    page["sections"][1]["text"] = replace_once(
        page["sections"][1]["text"],
        "O artigo 1.792 do Código Civil",
        "O art. 1.792 do Código Civil",
        page["intent_id"],
    )
    page["sections"][3]["text"] = replace_once(
        page["sections"][3]["text"],
        "O REsp 439.945/RS reconhece que o fiador responde pelas dívidas anteriores cobertas pelo "
        "contrato, mas a fiança se extingue para obrigações posteriores ao óbito do locatário, "
        "apesar da sub-rogação.",
        "O REsp 439.945/RS reconhece que o fiador responde pelas dívidas anteriores cobertas pelo "
        "contrato, mas não responde por obrigações posteriores ao óbito do locatário: a fiança se "
        "extingue para o período novo, apesar da sub-rogação.",
        page["intent_id"],
    )

    page = by_id["imob-divorcio-inquilinos-locacao"]
    info = page["official_sources"][2]
    if "017357" not in info["url"]:
        raise RuntimeError("fonte esperada do Informativo 660 não encontrada")
    page["official_sources"][2] = source(
        STJ_INFO_660,
        info["name"],
        info["anchor_claim"],
    )


def words_of(value):
    folded = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", folded.lower(), re.UNICODE)


def body_word_count(page):
    total = len(words_of(page.get("opening", "")))
    for section in page.get("sections", []):
        total += len(words_of(section.get("heading", "")))
        total += len(words_of(section.get("text", "")))
    for item in page.get("faq", []):
        total += len(words_of(item.get("q", "")))
        total += len(words_of(item.get("a", "")))
    return total


def transform(raw):
    pages = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(pages) != 22 or len({page["intent_id"] for page in pages}) != 22:
        raise RuntimeError("o shard precisa conter 22 intent_ids únicos")

    for page in pages:
        for key, container in visible_fields(page):
            container[key] = accent_words(container.get(key, ""))

    apply_legal_fixes(pages)
    for page in pages:
        page["word_count"] = body_word_count(page)
    return pages


def preview_text(pages):
    for page in pages:
        print(page["title"])
        print(page["meta_description"])
        print(page["h1"])
        print(page["opening"])
        for section in page.get("sections", []):
            print(section["heading"])
            print(section["text"])
        for item in page.get("faq", []):
            print(item["q"])
            print(item["a"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-text", action="store_true")
    args = parser.parse_args()

    with open(TARGET, "rb") as handle:
        raw_bytes = handle.read()
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"CAS recusado: esperado {EXPECTED_SHA256}, atual {actual}")

    pages = transform(raw_bytes.decode("utf-8"))
    if args.preview_text:
        preview_text(pages)
        return

    payload = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-02-peer.", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, TARGET)
        directory_fd = os.open(directory, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == "__main__":
    main()
