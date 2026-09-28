#!/usr/bin/env python3
"""Correção jurídica final de retrovenda e fonte tributária da permuta."""

import hashlib
import json
import os
import tempfile

from _tmp_fix_imobiliario_09_lib import body_word_count


TARGET = "data/editorial/v2_pages/imobiliario-09.jsonl"
EXPECTED_SHA256 = "8c0ac939942c33b09f6bf5f36f1d0644856dfc45db4164d095a7aa8dca937f57"


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page["intent_id"]: page for page in pages}

    retro = by_intent["imob-retrovenda-verbete"]["sections"][3]
    retro["text"] = retro["text"].replace(
        "O artigo 507 permite cessão e transmissão do direito a herdeiros e legatários. Havendo vários titulares, o exercício "
        "segue as regras do dispositivo, sem fracionar o imóvel unilateralmente. Pelo artigo 508, o direito pode ser exercido "
        "contra terceiro adquirente.",
        "O artigo 507 permite cessão e transmissão do direito a herdeiros e legatários e autoriza exercê-lo contra terceiro "
        "adquirente. O artigo 508 cuida da concorrência quando duas ou mais pessoas podem retratar o mesmo imóvel e exige solução "
        "que preserve o depósito integral, sem fracionamento unilateral.",
    )

    permuta = by_intent["imob-permuta-imoveis"]
    permuta["official_sources"].append({
        "url": "https://normas.receita.fazenda.gov.br/sijut2consulta/anexoOutros.action?idArquivoBinario=73829",
        "name": "Receita Federal, Solução de Consulta Cosit 128/2024",
        "anchor_claim": "ganho de capital da pessoa física restrito à torna na permuta imobiliária com dinheiro",
    })

    for page in pages:
        page["word_count"] = body_word_count(page)
        if not 600 <= page["word_count"] <= 1400:
            raise SystemExit(f"faixa inválida: {page['intent_id']}={page['word_count']}")
        if not 2 <= len(page.get("official_sources", [])) <= 5:
            raise SystemExit(f"fontes inválidas: {page['intent_id']}")

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-09-post-legal.", dir=os.path.dirname(TARGET))
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
    print(f"correção jurídica promovida; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()

