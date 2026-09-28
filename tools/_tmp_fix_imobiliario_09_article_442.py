#!/usr/bin/env python3
import hashlib
import json
import re
import unicodedata
from pathlib import Path


PATH = Path("data/editorial/v2_pages/imobiliario-09.jsonl")
EXPECTED_SHA256 = "72df19bf40c3312c1fc06b3ab669eb4fa544aad7f616d124e5a3c3c967c4a5e8"
OLD = (
    "Nos termos do artigo 441, provado o vício oculto, o adquirente pode rejeitar a coisa, "
    "desfazendo o contrato pela ação redibitória, ou conservá-la e pedir abatimento do preço "
    "pela ação estimatória."
)
NEW = (
    "O artigo 441 permite rejeitar a coisa quando o vício oculto torna o bem impróprio ao uso "
    "ou reduz seu valor. Como alternativa à redibição, o artigo 442 permite conservar o imóvel "
    "e pedir abatimento do preço pela ação estimatória."
)


def words(value):
    folded = "".join(
        char for char in unicodedata.normalize("NFD", value.lower())
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


payload = PATH.read_bytes()
actual = hashlib.sha256(payload).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual}")

pages = [json.loads(line) for line in payload.decode().splitlines()]
page = next(item for item in pages if item["intent_id"] == "imob-vicio-oculto-imovel-usado")
matches = sum(section["text"].count(OLD) for section in page["sections"])
if matches != 1:
    raise RuntimeError(f"expected one legal attribution to replace, got {matches}")
for section in page["sections"]:
    section["text"] = section["text"].replace(OLD, NEW)
page["word_count"] = body_word_count(page)

encoded = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in pages).encode()
PATH.write_bytes(encoded)
print(hashlib.sha256(encoded).hexdigest(), page["word_count"])
