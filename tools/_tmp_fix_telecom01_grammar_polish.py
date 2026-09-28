#!/usr/bin/env python3
import hashlib
import json
import sys

PATH = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
EXPECTED_SHA = '8f43016ec30f1104b2d43b875e442537069598cbf8b1c17b4386087b9504f907'

with open(PATH, 'rb') as f:
    raw = f.read()
if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
    print('CAS ABORT', hashlib.sha256(raw).hexdigest())
    sys.exit(1)

lines = raw.decode('utf-8').splitlines()
pages = [json.loads(l) for l in lines if l.strip()]
by_id = {p['intent_id']: p for p in pages}

page = by_id['tel-fatura-papel-cobrada']
fixes = [
    ('nas partes incorporadas, O inciso III do art. 13 permanece '
     'excluído.',
     'nas partes incorporadas. O inciso III do art. 13 permanece '
     'excluído.'),
    ('Para quem tem até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º. Com CDC e LGT continuam aplicáveis.',
     'Para quem tem até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º. CDC e LGT continuam aplicáveis.'),
]
for old, new in fixes:
    if old not in page['opening'] or page['opening'].count(old) != 1:
        print('MISMATCH', repr(old))
        sys.exit(2)
    page['opening'] = page['opening'].replace(old, new)

with open(PATH, 'w', encoding='utf-8') as f:
    for p in pages:
        f.write(json.dumps(p, ensure_ascii=False))
        f.write('\n')
print('OK')
