#!/usr/bin/env python3
"""Compara official_sources de cada p<NN>.json contra o override exato do
contrato (decodificado do base64 do proprio prompt, nao retypado a mao).
"""
import base64
import json
import re
import sys
from pathlib import Path

PROMPT = Path('/sessions/focused-kind-bohr/mnt/wiki/.agents/runtime/staging/cowork_prompts_20260730/sucessoes-w3-03.prompt.txt')
WORKDIR = Path(sys.argv[1])

content = PROMPT.read_text(encoding='utf-8')
blobs = re.findall(r'[A-Za-z0-9+/]{200,}={0,2}', content)
proj = json.loads(base64.b64decode(blobs[0]))
overrides = proj['source_overrides']

order = [
    ("p01.json", "suc-substituicao-vulgar-testamento"),
    ("p02.json", "suc-legado-imovel-com-divida"),
    ("p03.json", "suc-legado-alimentos-pensao"),
    ("p04.json", "suc-testamento-testemunhas-requisitos"),
    ("p05.json", "suc-testamento-guarda-custodia-vias"),
    ("p06.json", "suc-testamento-fundacao-caridade"),
    ("p07.json", "suc-testamento-parte-disponivel-companheiro"),
    ("p08.json", "suc-testamento-ordem-preferencia-legados"),
    ("p09.json", "suc-testamento-encargo-modal"),
    ("p10.json", "suc-testamento-bens-digitais-senha-cripto"),
    ("p11.json", "suc-testamento-testamenteiro-dativo"),
    ("p12.json", "suc-testamento-curatelado-interdito"),
    ("p13.json", "suc-testamento-assinatura-a-rogo"),
    ("p14.json", "suc-testamento-cerrado-extraviado"),
    ("p15.json", "suc-testamento-indicar-curador-filho-deficiente"),
]


def consolidated(by_hint):
    hints = sorted(by_hint)
    first = by_hint[hints[0]]
    url = first['url']
    return {
        'name': first['name'],
        'url': url,
        'anchor_claim': " | ".join(by_hint[h]['anchor_claim'] for h in hints),
    }


overall_ok = True
for fname, intent in order:
    path = WORKDIR / fname
    if not path.exists():
        print(f"{fname}: (ainda nao escrito, pulando)")
        continue
    page = json.loads(path.read_text(encoding='utf-8'))
    if page.get('intent_id') != intent:
        print(f"{fname}: INTENT_ID MISMATCH {page.get('intent_id')!r} != {intent!r}")
        overall_ok = False
        continue
    expected_by_hint = overrides.get(intent, {})
    if not expected_by_hint:
        print(f"{fname} ({intent}): sem override (ok, nada a checar)")
        continue
    by_url = {}
    for hint, src in expected_by_hint.items():
        by_url.setdefault(src['url'], {})[hint] = src
    actual_sources = {s['url']: s for s in page.get('official_sources', [])}
    ok = True
    for url, hints in by_url.items():
        expected = consolidated(hints)
        actual = actual_sources.get(url)
        if actual is None:
            print(f"{fname} ({intent}): FALTA fonte para URL {url}")
            ok = False
            continue
        actual_identity = {k: actual.get(k) for k in ('name', 'url', 'anchor_claim')}
        if actual_identity != expected:
            print(f"{fname} ({intent}): DIVERGE para {url}")
            print(f"  esperado: {expected}")
            print(f"  atual:    {actual_identity}")
            ok = False
    if ok:
        print(f"{fname} ({intent}): OK ({len(by_url)} fonte(s) de override conferida(s))")
    else:
        overall_ok = False

print()
print("RESULTADO GERAL:", "OK" if overall_ok else "DIVERGENCIAS ENCONTRADAS")
sys.exit(0 if overall_ok else 1)
