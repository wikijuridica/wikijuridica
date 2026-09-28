#!/usr/bin/env python3
"""Restaura diacriticos inequivocos do primeiro bloco imobiliario-09."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-09.jsonl"
EXPECTED_SHA256 = "9328d80aa8fafaa6dafc7d2bf0373bed73f3e335f548079eb06766c0430d615d"
INTENTS = {
    "imob-vicio-construtivo-acao",
    "imob-vicio-oculto-imovel-usado",
    "imob-evicao-perdi-imovel",
    "imob-area-menor-escritura",
    "imob-metragem-planta-menor",
    "imob-itbi-base-calculo",
}
TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def deaccent(value):
    return "".join(
        char for char in unicodedata.normalize("NFD", value)
        if not unicodedata.combining(char)
    )


def selected_strings(page):
    yield page.get("opening", "")
    for item in page.get("sections", []):
        yield item.get("heading", "")
        yield item.get("text", "")
    for item in page.get("faq", []):
        yield item.get("q", "")
        yield item.get("a", "")
    for item in page.get("official_sources", []):
        yield item.get("name", "")
        yield item.get("anchor_claim", "")


def accent_map(pages):
    words = sorted({
        token
        for page in pages if page.get("intent_id") in INTENTS
        for value in selected_strings(page)
        for token in TOKEN.findall(value)
        if token.isascii() and token.isalpha() and len(token) > 1
    }, key=lambda value: (value.casefold(), value))
    result = subprocess.run(
        ["hunspell", "-d", "pt_BR", "-a"],
        input="\n".join(words) + "\n",
        text=True,
        check=True,
        capture_output=True,
    )
    responses = [line for line in result.stdout.splitlines()[1:] if line.strip()]
    if len(responses) != len(words):
        raise SystemExit(f"respostas hunspell inesperadas: {len(responses)} para {len(words)}")

    replacements = {}
    for word, response in zip(words, responses):
        if not response.startswith("&") or ":" not in response:
            continue
        suggestions = [item.strip() for item in response.split(":", 1)[1].split(",")]
        matches = [
            item for item in suggestions
            if " " not in item and deaccent(item).casefold() == word.casefold() and item != word
        ]
        if matches:
            replacements[word] = matches[0]

    replacements.update({
        "controverse": "controvérsia",
        "Controverse": "Controvérsia",
    })
    return replacements


def transform(value, replacements):
    return TOKEN.sub(lambda match: replacements.get(match.group(0), match.group(0)), value)


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    replacements = accent_map(pages)
    for page in pages:
        if page.get("intent_id") not in INTENTS:
            continue
        page["opening"] = transform(page.get("opening", ""), replacements)
        for item in page.get("sections", []):
            item["heading"] = transform(item.get("heading", ""), replacements)
            item["text"] = transform(item.get("text", ""), replacements)
        for item in page.get("faq", []):
            item["q"] = transform(item.get("q", ""), replacements)
            item["a"] = transform(item.get("a", ""), replacements)
        for item in page.get("official_sources", []):
            item["name"] = transform(item.get("name", ""), replacements)
            item["anchor_claim"] = transform(item.get("anchor_claim", ""), replacements)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-09-accent-a.", dir=os.path.dirname(TARGET))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        with open(TARGET, "rb") as handle:
            current = hashlib.sha256(handle.read()).hexdigest()
        if current != EXPECTED_SHA256:
            raise SystemExit(f"CAS falhou antes da promoção: {current}")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"acentos inequívocos={len(replacements)}; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
