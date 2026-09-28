#!/usr/bin/env python3
"""Remove uma colisão externa do shard 17 sem alterar sua tese jurídica."""

import hashlib
import json
import os
import tempfile

from tools.audit_v2_pages import body_word_count


PATH = "data/editorial/v2_pages/previdenciario-17.jsonl"
EXPECTED_SHA256 = "f78316d1d2c9742fda74cf418b090c45e70ad351902ede2cbe39da4dcf05d4fe"
OLD = (
    "O art. 29-A da Lei 8.213/1991 determina que o INSS use essas informações para calcular "
    "o salário de benefício e permite ao segurado pedir correção mediante documentos."
)
NEW = (
    "Pelo art. 29-A da Lei 8.213/1991, essas informações entram no cálculo do salário de "
    "benefício; o segurado, porém, pode requerer a correção documental do cadastro."
)


with open(PATH, "rb") as handle:
    raw = handle.read()
if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
    raise SystemExit("previdenciario-17 mudou; releia antes de aplicar")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
page = next(item for item in pages if item["intent_id"] == "prev-verbete-cnis")
text = page["sections"][0]["text"]
if text.count(OLD) != 1:
    raise SystemExit("frase esperada ausente ou duplicada")
page["sections"][0]["text"] = text.replace(OLD, NEW)
page["word_count"] = body_word_count(page)

directory = os.path.dirname(PATH)
fd, temporary = tempfile.mkstemp(prefix=".previdenciario-17.", suffix=".tmp", dir=directory)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        for item in pages:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, PATH)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
