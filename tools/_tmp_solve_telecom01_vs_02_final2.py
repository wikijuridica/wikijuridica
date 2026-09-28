#!/usr/bin/env python3
import hashlib
import json
import sys

sys.path.insert(0, 'tools')
import audit_v2_pages as a  # noqa: E402

PATH1 = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
PATH2 = 'data/editorial/v2_pages/telecom_energia-02.jsonl'
EXPECTED_SHA1 = 'e48111682f6734e46f67ce2b27ecb8f7e109eb4cbf2ea68689fe31c7792e9e4d'

with open(PATH1, 'rb') as f:
    raw1 = f.read()
if hashlib.sha256(raw1).hexdigest() != EXPECTED_SHA1:
    print('CAS ABORT', hashlib.sha256(raw1).hexdigest())
    sys.exit(1)

pages1 = [json.loads(l) for l in raw1.decode('utf-8').splitlines() if l.strip()]
by1 = {p['intent_id']: p for p in pages1}

with open(PATH2, 'rb') as f:
    raw2 = f.read()
pages2 = [json.loads(l) for l in raw2.decode('utf-8').splitlines() if l.strip()]


def page_grams(p):
    grams = set()
    for _, part in a.labeled_visible_parts(p):
        toks = a.words_of(part)
        for i in range(len(toks) - 12 + 1):
            grams.add(tuple(toks[i:i + 12]))
    return grams


FORBIDDEN2 = set()
for p in pages2:
    FORBIDDEN2 |= page_grams(p)

FIXES = [
    ('tel-fatura-paga-duas-vezes',
     'Na prestadora com até 5.000 acessos, permanecem somente os '
     'arts. 4º, 5º e 7º; o CDC disciplina a repetição do indébito e '
     'a LGT preserva a reparação cabível, sem importar automaticamente '
     'o crédito no ciclo seguinte ou o depósito em 30 dias.',
     'Até 5.000 acessos recebem só arts. 4º, 5º e 7º. O CDC disciplina '
     'a repetição do indébito e a LGT preserva a reparação cabível, '
     'sem importar automaticamente o crédito no ciclo seguinte ou o '
     'depósito em 30 dias.'),
    ('tel-fatura-papel-cobrada',
     'Até 5.000 acessos recebem apenas os arts. 4º, 5º e 7º. Com CDC '
     'e LGT continuam aplicáveis.',
     'Para quem tem até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º. Com CDC e LGT continuam aplicáveis.'),
]

for iid, old, new in FIXES:
    page = by1[iid]
    if old not in page['opening'] or page['opening'].count(old) != 1:
        print('MISMATCH', iid)
        sys.exit(2)
    page['opening'] = page['opening'].replace(old, new)


def body_word_count(p):
    total = len(a.words_of(p.get('opening', '')))
    for s in p.get('sections', []) or []:
        total += len(a.words_of(s.get('heading', '')))
        total += len(a.words_of(s.get('text', '')))
    for f in p.get('faq', []) or []:
        total += len(a.words_of(f.get('q', '')))
        total += len(a.words_of(f.get('a', '')))
    return total


for iid, _, _ in FIXES:
    by1[iid]['word_count'] = body_word_count(by1[iid])

union1 = set()
for p in pages1:
    union1 |= page_grams(p)
overlap = union1 & FORBIDDEN2
print('overlap vs telecom-02 after fix:', len(overlap))
if overlap:
    for g in overlap:
        print('  ', ' '.join(g))
    sys.exit(4)

# intra-file dedup check
seen_ngrams = {}
intra_dup = False
for p in pages1:
    grams = page_grams(p)
    for g in grams:
        owner = seen_ngrams.get(g)
        if owner and owner != p['intent_id']:
            print('INTRA DUP', owner, p['intent_id'], ' '.join(g))
            intra_dup = True
        else:
            seen_ngrams[g] = p['intent_id']
if intra_dup:
    sys.exit(5)

for iid, _, _ in FIXES:
    page = by1[iid]
    visible = '\n'.join(t for _, t in a.labeled_visible_parts(page))
    code, groups = a.TELECOM01_PPP_SCOPE_RULES[iid]
    for gi, alts in enumerate(groups):
        ok = any(a.criminal13_declarative_alternative_affirmed_in_text(
            visible, alt) for alt in alts)
        if not ok:
            print('SCOPE FAIL', iid, gi)
            sys.exit(6)

with open(PATH1, 'w', encoding='utf-8') as f:
    for p in pages1:
        f.write(json.dumps(p, ensure_ascii=False))
        f.write('\n')

print('OK wrote', PATH1)
