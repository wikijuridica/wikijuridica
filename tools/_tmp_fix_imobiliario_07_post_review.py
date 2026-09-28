#!/usr/bin/env python3
"""Aplica duas correções pós-revisão no imobiliario-07, preservando 11 linhas."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path


TARGET = Path("data/editorial/v2_pages/imobiliario-07.jsonl")
EXPECTED_SHA256 = "5b4c1c17921732a0ebe3777cd749f28610837af7c0ec98ccc5e4fcc969259ac4"
TARGET_IDS = {
    "imob-arrendamento-rural-vs-locacao",
    "imob-renovatoria-contrato-verbal",
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


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def rewrite_rural(page):
    section_by_heading = {item["heading"]: item for item in page["sections"]}
    section_by_heading["Retribuição certa não se confunde com partilha"]["text"] = (
        "O art. 18 do Decreto 59.566/1966 determina que o preço do arrendamento seja "
        "ajustado em quantia fixa de dinheiro. O pagamento pode ocorrer em dinheiro ou em "
        "quantidade de frutos ou produtos cujo preço corrente no mercado local, nunca inferior "
        "ao preço mínimo oficial, equivalha ao aluguel na época da liquidação. Portanto, produto "
        "rural pode funcionar como meio de pagamento do valor monetário, sem se tornar o próprio "
        "preço ajustado."
    )
    section_by_heading["Percentual isolado não resolve a natureza do contrato"]["text"] = (
        "O parágrafo único do art. 18 proíbe ajustar como preço do arrendamento uma quantidade "
        "fixa de frutos ou produtos, ou seu equivalente em dinheiro. Essa vedação não autoriza "
        "concluir que qualquer referência percentual produz automaticamente parceria. Na parceria "
        "do art. 96 do Estatuto da Terra, importam a partilha de riscos e a divisão de frutos, "
        "produtos ou lucros. Forma de cálculo, gestão, despesas, caso fortuito, resultado negativo "
        "e prática de liquidação devem ser examinados junto às normas agrárias obrigatórias."
    )
    existing = {item["url"]: item for item in page["official_sources"]}
    specs = [
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
            "https://www.planalto.gov.br/ccivil_03/decreto/antigos/d59566.htm#art18",
            "Decreto 59.566/1966, art. 18",
            "preço em quantia fixa de dinheiro, pagamento pelo equivalente corrente em frutos ou produtos e vedação de quantidade fixa como preço",
        ),
        (
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art1",
            "Lei 8.245/1991, art. 1º",
            "campo de aplicação da locação de imóvel urbano e exclusões",
        ),
    ]
    rebuilt = []
    for url, name, claim in specs:
        item = source(url, name, claim)
        previous = existing.get(url)
        if previous is not None:
            for key in ("verified_at", "http_status"):
                if key in previous:
                    item[key] = previous[key]
        rebuilt.append(item)
    page["official_sources"] = rebuilt
    page["word_count"] = body_word_count(page)


def rewrite_verbal(page):
    section_by_heading = {item["heading"]: item for item in page["sections"]}
    section_by_heading["Prazo determinado e indeterminado têm saídas diferentes"]["text"] = (
        "Pelo art. 56, a locação não residencial por prazo determinado termina com o prazo, "
        "independentemente de aviso. Se o locatário permanece por mais de trinta dias sem oposição, "
        "presume-se a prorrogação por prazo indeterminado nas condições ajustadas. O art. 57 permite "
        "a denúncia escrita da locação não residencial por prazo indeterminado, com trinta dias para "
        "desocupação, mas essa regra não deve ser apresentada como autorização vazia e universal: "
        "destinação, contrato e proteções especiais também precisam ser verificados."
    )
    page["sections"].insert(
        4,
        {
            "heading": "Destinações do art. 53 recebem proteção especial",
            "text": (
                "Nas locações de imóveis utilizados por hospitais, unidades sanitárias oficiais, "
                "asilos, estabelecimentos de saúde e de ensino autorizados e fiscalizados pelo Poder "
                "Público, bem como por entidades religiosas devidamente registradas, o art. 53 restringe "
                "a rescisão às hipóteses que enumera. Por isso, não se pode usar o art. 57 isoladamente "
                "para prometer denúncia vazia em toda locação não residencial por prazo indeterminado. "
                "A atividade efetiva e os requisitos da proteção especial devem ser conferidos."
            ),
        },
    )
    page["official_sources"].append(
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art53",
            "Lei 8.245/1991, art. 53",
            "destinações protegidas e hipóteses restritas de rescisão da locação",
        )
    )
    page["word_count"] = body_word_count(page)


def validate(original_lines, output_lines, pages):
    if len(original_lines) != 13 or len(output_lines) != 13 or len(pages) != 13:
        raise RuntimeError("o shard deve conservar exatamente 13 linhas")
    changed = []
    for before, after in zip(original_lines, output_lines):
        intent = json.loads(before)["intent_id"]
        if before != after:
            changed.append(intent)
        elif intent in TARGET_IDS:
            raise RuntimeError(f"linha alvo permaneceu idêntica: {intent}")
    if set(changed) != TARGET_IDS or len(changed) != 2:
        raise RuntimeError(f"linhas alteradas fora do escopo: {changed}")

    by_id = {page["intent_id"]: page for page in pages}
    rural = by_id["imob-arrendamento-rural-vs-locacao"]
    verbal = by_id["imob-renovatoria-contrato-verbal"]
    if len(rural["official_sources"]) != 5:
        raise RuntimeError("a página rural deve conservar cinco fontes")
    if len(verbal["official_sources"]) != 4:
        raise RuntimeError("a página verbal deve ter quatro fontes")
    for page in (rural, verbal):
        if page["word_count"] != body_word_count(page):
            raise RuntimeError(f"word_count inexato: {page['intent_id']}")
        if not 360 <= page["word_count"] <= 880:
            raise RuntimeError(f"word_count fora da faixa: {page['intent_id']}")

    rural_text = " ".join(item["text"] for item in rural["sections"]).lower()
    required_rural = (
        "quantia fixa de dinheiro",
        "preço corrente no mercado local",
        "na época da liquidação",
        "proíbe ajustar como preço",
        "quantidade fixa de frutos ou produtos",
        "não autoriza concluir que qualquer referência percentual produz automaticamente parceria",
    )
    if missing := [value for value in required_rural if value not in rural_text]:
        raise RuntimeError(f"limites do art. 18 ausentes: {missing}")
    art18 = next(
        item for item in rural["official_sources"] if item["url"].endswith("#art18")
    )
    if "verified_at" in art18 or "http_status" in art18:
        raise RuntimeError("fonte nova art. 18 recebeu metadado inventado")

    verbal_text = " ".join(item["text"] for item in verbal["sections"]).lower()
    for marker in ("art. 53", "hospitais", "entidades religiosas devidamente registradas"):
        if marker not in verbal_text:
            raise RuntimeError(f"ressalva do art. 53 ausente: {marker}")
    art53 = next(
        item for item in verbal["official_sources"] if item["url"].endswith("#art53")
    )
    if "verified_at" in art53 or "http_status" in art53:
        raise RuntimeError("fonte nova art. 53 recebeu metadado inventado")


def main():
    payload = TARGET.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(
            f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}"
        )
    original_lines = payload.decode("utf-8").splitlines(keepends=True)
    pages = [json.loads(line) for line in original_lines if line.strip()]
    if {page["intent_id"] for page in pages} & TARGET_IDS != TARGET_IDS:
        raise RuntimeError("páginas alvo ausentes")

    for page in pages:
        if page["intent_id"] == "imob-arrendamento-rural-vs-locacao":
            rewrite_rural(page)
        elif page["intent_id"] == "imob-renovatoria-contrato-verbal":
            rewrite_verbal(page)

    output_lines = []
    for original, page in zip(original_lines, pages):
        if page["intent_id"] in TARGET_IDS:
            output_lines.append(
                json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
        else:
            output_lines.append(original)
    validate(original_lines, output_lines, pages)
    encoded = "".join(output_lines).encode("utf-8")

    fd, temporary = tempfile.mkstemp(
        prefix=".imobiliario-07-post-review.", suffix=".tmp", dir=TARGET.parent
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
    for intent in sorted(TARGET_IDS):
        page = next(item for item in pages if item["intent_id"] == intent)
        print(intent, page["word_count"], len(page["official_sources"]))


if __name__ == "__main__":
    main()
