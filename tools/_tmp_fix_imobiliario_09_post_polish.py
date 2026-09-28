#!/usr/bin/env python3
"""Polimento final de concordância e fonte jurisprudencial do imobiliário-09."""

import hashlib
import json
import os
import tempfile

from _tmp_fix_imobiliario_09_lib import body_word_count


TARGET = "data/editorial/v2_pages/imobiliario-09.jsonl"
EXPECTED_SHA256 = "8fad8a60029e6b606581b4c7109b6fe7ec29b570f00e36030edd71a9367ac18c"


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page["intent_id"]: page for page in pages}

    construction = by_intent["imob-vicio-construtivo-acao"]
    construction["faq"][1]["a"] = (
        "O condomínio, representado pelo síndico, pode defender interesses comuns, sem substituir automaticamente "
        "pretensões individuais sobre danos exclusivos de cada unidade."
    )
    construction["official_sources"].append({
        "url": "https://stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20190905&formato=PDF&nreg=201703173540&salvar=false&seq=1859561&tipo=0",
        "name": "STJ, REsp 1.721.694/SP",
        "anchor_claim": "prazo prescricional da pretensão indenizatória decorrente de vício construtivo",
    })

    retro = by_intent["imob-retrovenda-verbete"]["sections"][4]
    retro["text"] = retro["text"].replace(
        "Se o suposto comprador apenas entrega dinheiro como mútuo, o vendedor continua usando o imóvel e o valor de resgate "
        "funciona como dívida com encargos, pode haver discussão",
        "Se o suposto comprador entrega dinheiro como mútuo enquanto o vendedor continua usando o imóvel e o valor de resgate "
        "funciona como dívida com encargos, pode haver discussão",
    )

    for page in pages:
        page["word_count"] = body_word_count(page)
        if not 600 <= page["word_count"] <= 1400:
            raise SystemExit(f"faixa inválida: {page['intent_id']}={page['word_count']}")
        if not 2 <= len(page.get("official_sources", [])) <= 5:
            raise SystemExit(f"fontes inválidas: {page['intent_id']}")

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-09-post-polish.", dir=os.path.dirname(TARGET))
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
    print(f"polimento promovido; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()

