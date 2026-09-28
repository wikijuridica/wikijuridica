#!/usr/bin/env python3
"""Promove os ajustes pós-auditoria do imobiliário-04 com CAS próprio."""

import hashlib
import importlib.util
import json
import os
import tempfile


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "b77bbfe74fcbb4b1f646ec8225acd99f4ca27a93d79f43174f3bb6a681006edf"


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
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page.get("intent_id"): page for page in pages}
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
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04-post.", dir=directory)
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

    print(f"pós-auditoria promovida; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
