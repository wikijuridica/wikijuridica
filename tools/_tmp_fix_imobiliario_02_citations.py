#!/usr/bin/env python3
"""Alinha quatro citacoes de artigo ao auditor canonico, com CAS atomico."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-02.jsonl"
EXPECTED_SHA256 = "c23662d8975d76eb3cfd56cdf3a856859dcea1d332f6f6eb0f6182355732de74"


def replace_once(value, old, new, label):
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperava uma ocorrencia, encontrou {count}")
    return value.replace(old, new)


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


with open(TARGET, "rb") as handle:
    raw = handle.read()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"CAS recusado: esperado {EXPECTED_SHA256}, atual {actual}")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
by_id = {page["intent_id"]: page for page in pages}

page = by_id["imob-dividas-locatario-falecido"]
page["sections"][1]["text"] = replace_once(
    page["sections"][1]["text"],
    "O art. 1.792 do Código Civil limita",
    "O artigo 1792 do Código Civil limita",
    page["intent_id"],
)

page = by_id["imob-duas-garantias-vedacao"]
page["sections"][2]["text"] = replace_once(
    page["sections"][2]["text"],
    "O Código Civil, artigo 1.467, II, reconhece",
    "O Código Civil, artigo 1467, II, reconhece",
    page["intent_id"],
)

page = by_id["imob-fianca-sem-outorga-conjugal"]
page["sections"][0]["text"] = replace_once(
    page["sections"][0]["text"],
    "O Código Civil impede que pessoa casada",
    "O artigo 1647 do Código Civil impede que pessoa casada",
    page["intent_id"],
)

page = by_id["imob-igpm-alto-renegociar"]
for section in page["sections"]:
    if "A regra geral do Código Civil permite corrigir prestação" in section["text"]:
        section["text"] = replace_once(
            section["text"],
            "A regra geral do Código Civil permite corrigir prestação",
            "O artigo 317 do Código Civil permite corrigir prestação",
            page["intent_id"],
        )
        break
else:
    raise RuntimeError("imob-igpm-alto-renegociar: trecho do artigo 317 ausente")

for page in pages:
    page["word_count"] = body_word_count(page)

payload = "".join(
    json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
    for page in pages
).encode("utf-8")
directory = os.path.dirname(TARGET)
fd, temporary = tempfile.mkstemp(prefix=".imobiliario-02-citations.", dir=directory)
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
