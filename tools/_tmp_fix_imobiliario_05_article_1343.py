#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from pathlib import Path

from audit_v2_pages import body_word_count


PATH = Path("data/editorial/v2_pages/imobiliario-05.jsonl")
EXPECTED_SHA256 = "9bc039f0579e653d4d99cd70433d6602504d77c086518ac6b341bf17c02a3ba8"
TARGET = "imob-rateio-obra-luxo-minoria"

raw = PATH.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit(f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual}")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
matches = [page for page in pages if page.get("intent_id") == TARGET]
if len(matches) != 1:
    raise SystemExit(f"expected one {TARGET}, got {len(matches)}")
page = matches[0]

sections = [
    section for section in page["sections"]
    if section.get("heading") == "Nova construção pode exigir unanimidade"
]
if len(sections) != 1:
    raise SystemExit(f"expected one target section, got {len(sections)}")
sections[0]["heading"] = "Acréscimo comum e novas unidades têm quóruns diferentes"
sections[0]["text"] = (
    "O artigo 1.342 exige dois terços dos votos dos condôminos para obras em "
    "partes comuns, em acréscimo às já existentes, destinadas a facilitar ou "
    "aumentar a utilização, e proíbe construção que prejudique partes próprias "
    "ou comuns. Já o artigo 1.343 exige unanimidade para construir outro "
    "pavimento ou, no solo comum, outro edifício destinado a novas unidades. "
    "Essas hipóteses são mais específicas que simples embelezamento. Também se "
    "deve verificar se a intervenção altera a destinação ou avança sobre área "
    "exclusiva, questões que não se resolvem apenas contando votos."
)

cc_sources = [
    source for source in page["official_sources"]
    if "l10406compilada.htm" in source.get("url", "")
]
if len(cc_sources) != 1:
    raise SystemExit(f"expected one Civil Code source, got {len(cc_sources)}")
cc_sources[0]["url"] = (
    "https://www.planalto.gov.br/ccivil_03/leis/2002/"
    "l10406compilada.htm#art1341"
)
cc_sources[0]["name"] = (
    "Código Civil, arts. 1.336, 1.341, 1.342, 1.343 e 1.351"
)
cc_sources[0]["anchor_claim"] = (
    "os arts. 1.336, 1.341, 1.342, 1.343 e 1.351 disciplinam contribuição, "
    "espécies de obra, acréscimos, novas unidades e mudança de destinação"
)
page["word_count"] = body_word_count(page)

payload = "".join(
    json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
    for item in pages
).encode("utf-8")
fd, temporary = tempfile.mkstemp(prefix=PATH.name + ".", dir=PATH.parent)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if hashlib.sha256(PATH.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("CAS mismatch immediately before replace")
    os.replace(temporary, PATH)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)

print(hashlib.sha256(payload).hexdigest())
