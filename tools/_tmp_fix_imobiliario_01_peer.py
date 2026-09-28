#!/usr/bin/env python3
"""Correção de revisão cruzada sobre consentimento do art. 13."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-01.jsonl"
EXPECTED_SHA256 = "4c6c4e4203ab7a8fb5d88753f73aad04edcac71ee7094d2691309b3755e9b813"
INTENT = "imob-despejo-infracao-contratual"
HEADING = "O consentimento precisa existir antes e por escrito"
NEW_TEXT = (
    "O art. 13 exige consentimento prévio e escrito do locador. Seu § 1º impede "
    "presumir anuência pela simples demora quando não houve a notificação escrita "
    "específica prevista na lei. Já o § 2º dá ao locador trinta dias para formalizar "
    "oposição depois de receber comunicação escrita do locatário sobre cessão, "
    "sublocação ou empréstimo.\n\n"
    "No REsp 1.443.135/SP, o STJ tratou esse prazo como decadencial e concluiu que "
    "a falta de oposição nos trinta dias seguintes à notificação pode presumir "
    "autorização e legitimar a cessão. Portanto, nem todo silêncio autoriza o negócio, "
    "mas também é incorreto afirmar que o silêncio posterior a uma notificação regular "
    "nunca produz efeito. Conteúdo, recebimento e data da comunicação precisam ser "
    "provados."
)
STJ_URL = (
    "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi?"
    "CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20180430&formato=PDF&"
    "nreg=201400616510&salvar=false&seq=1703168&tipo=0"
)


def words(value):
    plain = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", plain.lower(), re.UNICODE)


def body_word_count(page):
    total = len(words(page.get("opening", "")))
    for section in page.get("sections", []):
        total += len(words(section.get("heading", "")))
        total += len(words(section.get("text", "")))
    for item in page.get("faq", []):
        total += len(words(item.get("q", ""))) + len(words(item.get("a", "")))
    return total


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    matches = [page for page in pages if page.get("intent_id") == INTENT]
    if len(matches) != 1:
        raise SystemExit(f"intent encontrado {len(matches)} vez(es)")
    page = matches[0]
    sections = [section for section in page["sections"] if section.get("heading") == HEADING]
    if len(sections) != 1:
        raise SystemExit(f"seção encontrada {len(sections)} vez(es)")
    sections[0]["text"] = NEW_TEXT

    if not any(item.get("url") == STJ_URL for item in page["official_sources"]):
        page["official_sources"].append({
            "url": STJ_URL,
            "name": "STJ, REsp 1.443.135/SP",
            "anchor_claim": "efeito da falta de oposição nos trinta dias após notificação escrita",
        })
    page["word_count"] = body_word_count(page)

    rendered = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-01-peer.", dir=os.path.dirname(TARGET))
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

    print(f"revisão cruzada aplicada; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
