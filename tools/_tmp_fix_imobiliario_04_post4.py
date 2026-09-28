#!/usr/bin/env python3
"""Corrige casing de Pix e acentuação residual no imobiliário-04."""

import hashlib
import json
import os
import tempfile


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "8b27556e37c97ea6c33321ed8abe8f37dd2cebf59bcec747229d6306b1accf48"


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page.get("intent_id"): page for page in pages}
    by_intent["imob-recibo-aluguel-discriminado"]["meta_description"] = (
        "Pagou o aluguel em dinheiro ou Pix e não recebeu comprovante detalhado? Veja o que a Lei do "
        "Inquilinato exige sobre quitação discriminada."
    )
    damage = by_intent["imob-imovel-devolvido-danificado"]
    replacements = 0
    for item in damage["sections"]:
        old = item["text"]
        item["text"] = old.replace("alugueis vencidos", "aluguéis vencidos")
        replacements += old != item["text"]
    if replacements != 1:
        raise SystemExit(f"esperada uma correção de acento, encontradas {replacements}")

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04-post4.", dir=os.path.dirname(TARGET))
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

    print(f"PT-BR final promovido; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
