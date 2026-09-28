#!/usr/bin/env python3
"""Remove anglicismos residuais da prosa do imobiliário-04."""

import hashlib
import importlib.util
import json
import os
import tempfile


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "92c377d89d43a39cd4bff99f3dcfd8bbce8bc55c38a88f49e10f9a13fe0acb4d"


def load_model():
    spec = importlib.util.spec_from_file_location(
        "imobiliario_04_fix_model", "tools/_tmp_fix_imobiliario_04.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(page, old, new):
    hits = 0
    for field in ("opening",):
        value = page.get(field, "")
        if old in value:
            page[field] = value.replace(old, new)
            hits += 1
    for item in page.get("sections", []):
        for field in ("heading", "text"):
            value = item.get(field, "")
            if old in value:
                item[field] = value.replace(old, new)
                hits += 1
    for item in page.get("faq", []):
        for field in ("q", "a"):
            value = item.get(field, "")
            if old in value:
                item[field] = value.replace(old, new)
                hits += 1
    if hits != 1:
        raise SystemExit(f"esperada uma ocorrência de {old!r}, encontradas {hits}")


def main():
    model = load_model()
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page.get("intent_id"): page for page in pages}
    by_intent[model.TOMBSTONE_INTENT]["skip_reason"] = model.TOMBSTONE_REASON
    replacements = {
        "imob-recibo-aluguel-discriminado": [
            ("Recibo enviado por e-mail", "Recibo enviado por correio eletrônico"),
        ],
        "imob-assinatura-eletronica-locacao": [
            ("e-mails ou telefones", "endereços de correio eletrônico ou telefones"),
        ],
        "imob-golpe-anuncio-falso-aluguel": [
            ("telefone, e-mail, horários", "telefone, endereço de correio eletrônico, horários"),
            ("contatos telefônicos, e-mail fraudulento", "contatos telefônicos, correio eletrônico fraudulento"),
        ],
    }
    for intent_id, pairs in replacements.items():
        page = by_intent[intent_id]
        for old, new in pairs:
            replace_once(page, old, new)
        page["word_count"] = model.body_word_count(page)
        model.validate_band(page)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04-post5.", dir=os.path.dirname(TARGET))
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

    print(f"PT-BR residual promovido; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
