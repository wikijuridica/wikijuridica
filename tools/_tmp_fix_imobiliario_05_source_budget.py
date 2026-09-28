#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from pathlib import Path


PATH = Path("data/editorial/v2_pages/imobiliario-05.jsonl")
EXPECTED_SHA256 = "a32aac73acc22433c1dbd8864c9f49b78eb24364d15047dd261049ab939f522a"
TARGET = "imob-fiador-executado-defesas"

raw = PATH.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit(f"CAS mismatch: expected {EXPECTED_SHA256}, got {actual}")

pages = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
matches = [page for page in pages if page.get("intent_id") == TARGET]
if len(matches) != 1:
    raise SystemExit(f"expected one {TARGET}, got {len(matches)}")
page = matches[0]
sources = {item["url"]: item for item in page["official_sources"]}

cpc_url = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art914"
cc_url = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art819"
tenancy_url = "https://www.planalto.gov.br/ccivil_03/leis/l8245.htm#art40"

cpc = dict(sources[cpc_url])
cpc["name"] = "Código de Processo Civil, arts. 231, 914 e 915"
cpc["anchor_claim"] = "os arts. 914 e 915 tornam os embargos independentes de penhora e fixam 15 dias, contados pelos marcos do art. 231"

cc = dict(sources[cc_url])
cc["name"] = "Código Civil, arts. 819, 827 e 838"
cc["anchor_claim"] = "os arts. 819 e 827 delimitam interpretação e benefício de ordem, e o art. 838 qualifica a moratória sem consentimento"

tenancy = dict(sources[tenancy_url])
page["official_sources"] = [cpc, cc, tenancy]

payload = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in pages).encode("utf-8")
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
