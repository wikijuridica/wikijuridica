#!/usr/bin/env python3
"""Promove a limpeza PT-BR e o tombstone municipal do imobiliário-04."""

import hashlib
import importlib.util
import json
import os
import tempfile


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "d611695087ad88f875a42396350ff157e76660074a1c6411070f94c3cf73c696"


def load_model():
    spec = importlib.util.spec_from_file_location(
        "imobiliario_04_fix_model", "tools/_tmp_fix_imobiliario_04.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    model = load_model()
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page.get("intent_id"): page for page in pages}
    tombstone = by_intent.get(model.TOMBSTONE_INTENT)
    if not tombstone or tombstone.get("skipped") is not True:
        raise SystemExit("tombstone municipal ausente ou materializado indevidamente")
    tombstone["skip_reason"] = model.TOMBSTONE_REASON

    for intent_id, update in model.UPDATES.items():
        page = by_intent[intent_id]
        for field in ("title", "meta_description", "h1", "opening", "sections", "faq"):
            if field in update:
                page[field] = update[field]
        if "official_sources" in update:
            page["official_sources"] = model.merge_sources(
                page.get("official_sources", []), update["official_sources"]
            )
        page["word_count"] = model.body_word_count(page)
        model.validate_band(page)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04-post3.", dir=os.path.dirname(TARGET))
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

    print(f"limpeza final promovida; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
