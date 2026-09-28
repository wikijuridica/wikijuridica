#!/usr/bin/env python3
"""Mantém cinco fontes revisionais e registra o estado atual do Tema 1.378."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "df96f38ed38008f2e00cdde37cc2de609c69b229dfac7943c8d7535c3e8c9040"
THEME_1378 = "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true&num_processo_classe=2227280&sg_classe=REsp&tipo_pesquisa=T"
SUSEP = "https://www.gov.br/susep/pt-br/assuntos/meu-futuro-seguro/seguros-previdencia-e-capitalizacao/seguros/seguro-habitacional"


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


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    page = next(item for item in pages if item["intent_id"] == "imob-revisao-financiamento-imobiliario")

    page["sections"][1]["text"] = (
        "O julgamento repetitivo dos Temas 27, 28 e 29 afastou a ideia de um teto bancário geral de 12 por cento ao "
        "ano e admitiu revisão dos juros apenas em situação excepcional, numa relação de consumo, quando as "
        "particularidades demonstrarem cabalmente a desvantagem exagerada. Não existe, portanto, percentual universal "
        "que transforme qualquer contrato em abusivo.\n\n"
        "A taxa média de operações equivalentes pode integrar a comparação, mas não deve virar multiplicador mecânico. "
        "O Tema 1.378 continua afetado no portal do STJ e discute justamente se médias de mercado ou critérios "
        "predefinidos bastam como fundamento exclusivo. Enquanto não houver tese definitiva, modalidade, data, prazo, "
        "risco e garantias precisam ser examinados no caso, e a situação do repetitivo deve ser conferida novamente."
    )
    page["sections"][4]["text"] = (
        "O seguro habitacional cobre riscos próprios do financiamento, mas o Tema 972 do STJ impede compelir o "
        "consumidor a contratar com o banco ou com a seguradora indicada por ele. A alternativa apresentada ainda "
        "precisa atender às coberturas e condições aplicáveis à operação. O ponto revisável é a restrição comprovada "
        "da escolha ou uma cobrança incompatível com o contrato, e não a simples variação do prêmio ou a existência "
        "do seguro.\n\n"
        "Um exemplo documentável seria a proposta limitar o seguro a uma empresa do grupo econômico e o banco recusar, "
        "sem fundamento técnico, alternativa equivalente apresentada pelo mutuário. Proposta, negativa escrita, "
        "certificado e composição do custo permitem confrontar o caso com o precedente, sem prometer restituição antes "
        "dessa verificação."
    )

    page["official_sources"] = [item for item in page["official_sources"] if item["url"] != SUSEP]
    page["official_sources"].append({
        "url": THEME_1378,
        "name": "STJ, Tema 1.378",
        "anchor_claim": "controvérsia afetada sobre uso exclusivo da taxa média ou de critérios predefinidos para reconhecer juros abusivos",
    })
    if len(page["official_sources"]) != 5:
        raise SystemExit(f"fontes revisionais inesperadas: {len(page['official_sources'])}")
    page["word_count"] = body_word_count(page)

    encoded = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in pages).encode("utf-8")
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(hashlib.sha256(encoded).hexdigest())
    print(page["intent_id"], page["word_count"], len(page["official_sources"]))


if __name__ == "__main__":
    main()
