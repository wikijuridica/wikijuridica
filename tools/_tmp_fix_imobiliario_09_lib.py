#!/usr/bin/env python3
"""Apoio para correcoes CAS do shard imobiliario-09."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-09.jsonl"


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def section(heading, text):
    return {"heading": heading, "text": text}


def _deaccent(value):
    return "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )


def body_word_count(page):
    def count(value):
        return len(re.findall(r"[^\W_]+", _deaccent(value).lower(), re.UNICODE))

    total = count(page.get("opening", ""))
    for item in page.get("sections", []):
        total += count(item.get("heading", "")) + count(item.get("text", ""))
    for item in page.get("faq", []):
        total += count(item.get("q", "")) + count(item.get("a", ""))
    return total


def merge_sources(previous, replacements):
    """Mantem evidencia live somente quando a URL continua literalmente identica."""
    old = {item.get("url"): item for item in previous if item.get("url")}
    merged = []
    for replacement in replacements:
        current = dict(replacement)
        prior = old.get(current["url"], {})
        for field in ("verified_at", "http_status"):
            if field in prior:
                current[field] = prior[field]
        merged.append(current)
    return merged


def apply_updates(expected_sha256, updates, producer):
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != expected_sha256:
        raise SystemExit(f"CAS falhou: esperado {expected_sha256}, encontrado {actual_sha}")

    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page.get("intent_id"): page for page in pages}
    missing = sorted(set(updates) - set(by_intent))
    if missing:
        raise SystemExit(f"intents ausentes: {missing}")

    for intent_id, update in updates.items():
        page = by_intent[intent_id]
        for field in ("title", "meta_description", "h1", "opening", "sections", "faq"):
            if field in update:
                page[field] = update[field]
        if "official_sources" in update:
            page["official_sources"] = merge_sources(
                page.get("official_sources", []), update["official_sources"]
            )
        page["word_count"] = body_word_count(page)
        if not 600 <= page["word_count"] <= 1400:
            raise RuntimeError(
                f"word_count fora da faixa em {intent_id}: {page['word_count']} (600-1400)"
            )

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
        for page in pages
    ).encode("utf-8")

    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=f".{producer}.", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        with open(TARGET, "rb") as handle:
            current_sha = hashlib.sha256(handle.read()).hexdigest()
        if current_sha != expected_sha256:
            raise SystemExit(f"CAS falhou antes da promocao: {current_sha}")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    final_sha = hashlib.sha256(rendered).hexdigest()
    print(f"corrigidas {len(updates)} paginas; sha256={final_sha}")

