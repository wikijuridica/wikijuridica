#!/usr/bin/env python3
"""Fecha duplicidade local e a fonte especifica da Sumula 380."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "dabf2642339a710009aa0fe7dc17c8c3b0475c8f51d38f8a3f1d531b9345442a"


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
    by_id = {page["intent_id"]: page for page in pages}

    negative = by_id["imob-segundo-leilao-negativo-quitacao"]
    old = "financiamento destinado à aquisição ou construção do imóvel residencial do próprio devedor"
    new = "crédito usado para comprar ou construir a residência pertencente ao próprio devedor"
    if negative["opening"].count(old) != 1:
        raise SystemExit("trecho de duplicidade não encontrado uma vez")
    negative["opening"] = negative["opening"].replace(old, new)
    negative["word_count"] = body_word_count(negative)

    revision = by_id["imob-revisao-financiamento-imobiliario"]
    url = "https://processo.stj.jus.br/SCON/sumstj/toc.jsp?sumula=380.num."
    if any(source.get("url") == url for source in revision["official_sources"]):
        raise SystemExit("Súmula 380 já presente")
    revision["official_sources"].append({
        "url": url,
        "name": "STJ, Súmula 380",
        "anchor_claim": "ajuizamento da ação revisional não impede, sozinho, a caracterização da mora",
    })

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-peer-followup.", dir=os.path.dirname(TARGET))
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
    print(f"negative_words={negative['word_count']}; revision_sources={len(revision['official_sources'])}")
    print(f"sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
