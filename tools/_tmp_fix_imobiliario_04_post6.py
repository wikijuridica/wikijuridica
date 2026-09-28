#!/usr/bin/env python3
"""Remove o último estrangeirismo substituível do imobiliário-04."""

import hashlib
import importlib.util
import json
import os
import tempfile


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "d34098a44c3e94bbf0ef8324c8227c67ecb09aefdf8a9beda0016e401ea12ad2"


def main():
    spec = importlib.util.spec_from_file_location(
        "imobiliario_04_fix_model", "tools/_tmp_fix_imobiliario_04.py"
    )
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    page = next(item for item in pages if item.get("intent_id") == "imob-locador-desistiu-antes-entrega")
    old = "E-mail que anuncia proposta melhor"
    new = "Mensagem de correio eletrônico que anuncia proposta melhor"
    hits = 0
    for item in page["sections"]:
        if old in item["text"]:
            item["text"] = item["text"].replace(old, new)
            hits += 1
    if hits != 1:
        raise SystemExit(f"esperada uma substituição, encontradas {hits}")
    page["word_count"] = model.body_word_count(page)
    model.validate_band(page)

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04-post6.", dir=os.path.dirname(TARGET))
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

    print(f"PT-BR encerrado; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
