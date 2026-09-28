#!/usr/bin/env python3
"""Remove duas colisoes editoriais de 12-gramas com CAS atomico."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-02.jsonl"
EXPECTED_SHA256 = "e97b8ea32fb25e3cc399ee5a3dcbb08f85027f26dc093ce8e233a4f5a5fd3477"


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

page = by_id["imob-contrato-curto-prorrogacao"]
page["opening"] = replace_once(
    page["opening"],
    "Na locação residencial verbal ou escrita por menos de 30 meses, o fim do prazo não abre "
    "denúncia vazia imediata.",
    "Quando a moradia foi alugada verbalmente ou por instrumento escrito com prazo inferior a "
    "30 meses, o vencimento não permite denúncia vazia imediata.",
    page["intent_id"],
)

page = by_id["imob-igpm-alto-renegociar"]
for section in page["sections"]:
    if "Sem acordo, o artigo 19 autoriza locador ou locatário" in section["text"]:
        section["text"] = replace_once(
            section["text"],
            "Sem acordo, o artigo 19 autoriza locador ou locatário a pedir revisão judicial depois "
            "de três anos de vigência do contrato ou do último acordo realizado.",
            "Sem acordo, o artigo 19 permite que qualquer parte busque a revisão judicial quando "
            "houver transcorrido o triênio desde o começo do contrato ou desde o acordo de valor "
            "mais recente.",
            page["intent_id"],
        )
        break
else:
    raise RuntimeError("imob-igpm-alto-renegociar: trecho trienal ausente")

for page in pages:
    page["word_count"] = body_word_count(page)

payload = "".join(
    json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
    for page in pages
).encode("utf-8")
directory = os.path.dirname(TARGET)
fd, temporary = tempfile.mkstemp(prefix=".imobiliario-02-dedupe.", dir=directory)
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
