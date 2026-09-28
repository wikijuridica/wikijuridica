#!/usr/bin/env python3
"""Corrige o numero do precedente da taxa de ocupacao com CAS."""

import hashlib
import json
import os
import tempfile


TARGET = "data/editorial/v2_pages/imobiliario-11.jsonl"
EXPECTED_SHA256 = "cf593d85d23179c4b4d307c3ab52a139ff37481329a95932b62c2fb69ac4de40"
INTENT = "imob-desocupacao-pos-consolidacao"
SOURCE_URL = (
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2023/"
    "15022023-Terceira-Turma-afasta-aplicacao-do-CDC-e-nega-reducao-da-taxa-de-"
    "ocupacao-de-imovel-com-alienacao-fiduciaria.aspx/"
)


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    page = next((item for item in pages if item.get("intent_id") == INTENT), None)
    if page is None:
        raise SystemExit("intent ausente")
    sources = [item for item in page.get("official_sources", []) if item.get("url") == SOURCE_URL]
    if len(sources) != 1 or sources[0].get("name") != "STJ, REsp 2.011.150":
        raise SystemExit("fonte anterior não encontrada exatamente")
    sources[0]["name"] = "STJ, REsp 1.999.485"

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-11-source-label.", dir=os.path.dirname(TARGET))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(open(TARGET, "rb").read()).hexdigest() != EXPECTED_SHA256:
            raise SystemExit("CAS falhou antes da promoção")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"source=REsp 1.999.485; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
