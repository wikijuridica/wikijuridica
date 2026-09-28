#!/usr/bin/env python3
import hashlib
import json
import sys

PATH = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
EXPECTED_SHA = 'c8871b0157987b3dda7e82e39448227615c2cd3cbb77f737c645fe3c098dd3f2'

with open(PATH, 'rb') as f:
    raw = f.read()
actual_sha = hashlib.sha256(raw).hexdigest()
if actual_sha != EXPECTED_SHA:
    print('CAS ABORT', actual_sha)
    sys.exit(1)

lines = raw.decode('utf-8').splitlines()
pages = [json.loads(l) for l in lines if l.strip()]
by_id = {p['intent_id']: p for p in pages}

OPENING_FIXES = [
    ('tel-fatura-diferente-da-oferta',
     'Na faixa de até 5.000 acessos, permanecem somente os arts. 4º, '
     '5º e 7º, com CDC e LGT continuando decisivos.'
     if False else
     'Para até 5.000 acessos, permanecem apenas os arts. 4º, 5º e 7º, '
     'com CDC e LGT continuando decisivos.',
     'Na faixa de até 5.000, permanecem apenas os arts. 4º, 5º e 7º, '
     'com CDC e LGT continuando decisivos.'),
    ('tel-negativacao-conta-telefone-contestada',
     'Para quem tem até 5.000 acessos, permanecem apenas os arts. 4º, '
     '5º e 7º, mantidos CDC e LGT.',
     'Na faixa de até 5.000, valem apenas os arts. 4º, 5º e 7º, '
     'mantidos CDC e LGT.'),
    ('tel-mudanca-plano-nao-autorizada',
     'Na prestadora com até 5.000 acessos, permanecem somente os '
     'arts. 4º, 5º e 7º, sem prejuízo do CDC e da LGT.',
     'A faixa de até 5.000 recebe apenas os arts. 4º, 5º e 7º; CDC e '
     'LGT permanecem aplicáveis.'),
    ('tel-contestar-fatura-operadora',
     'Procure a ouvidoria apenas quando esse canal existir no regime '
     'da empresa.',
     'A ouvidoria só deve ser usada quando esse canal integrar o '
     'regime da prestadora.'),
    ('tel-fatura-papel-cobrada',
     'Na faixa de até 5.000 permanecem apenas os arts. 4º, 5º e 7º, '
     'com CDC e LGT continuam aplicáveis.',
     'Para a prestadora com até 5.000 acessos, o § 5º mantém somente '
     'os arts. 4º, 5º e 7º, com CDC e LGT continuam aplicáveis.'),
]

SECTION_FIXES = [
    ('tel-fatura-diferente-da-oferta',
     'Na prestadora com até 5.000 acessos ficam só os arts. 4º, 5º e '
     '7º, sem prejuízo do CDC e da LGT.',
     'Na prestadora com até 5.000 acessos ficam só os arts. 4º, 5º e '
     '7º, preservados CDC e LGT.'),
    ('tel-roaming-internacional-conta-alta',
     'No regime integral, o art. 21, § 3º, IX, manda registrar na '
     'oferta os valores de roaming; o art. 90 só o estende à PPP que '
     'opte pela ferramenta comparadora ou por determinação da Anatel; '
     'por isso o registro não é requisito universal.',
     'No regime integral, o art. 21, § 3º, IX, manda registrar na '
     'oferta os valores de roaming; a PPP só herda essa exigência se '
     'optar pela ferramenta comparadora, ou por decisão pontual da '
     'Anatel; fora dessas hipóteses, o registro não é requisito '
     'universal.'),
]

changed = []
for iid, old, new in OPENING_FIXES:
    page = by_id[iid]
    if old not in page['opening'] or page['opening'].count(old) != 1:
        print('OPENING MISMATCH', iid)
        print(repr(page['opening']))
        sys.exit(2)
    page['opening'] = page['opening'].replace(old, new)
    changed.append(iid)

for iid, old, new in SECTION_FIXES:
    page = by_id[iid]
    found = False
    for s in page['sections']:
        if old in s['text']:
            if s['text'].count(old) != 1:
                print('SECTION NOT UNIQUE', iid)
                sys.exit(2)
            s['text'] = s['text'].replace(old, new)
            found = True
            break
    if not found:
        print('SECTION MISSING', iid)
        sys.exit(2)
    changed.append(iid)


def words_of(s):
    import re
    import unicodedata

    def deaccent(x):
        return ''.join(
            c for c in unicodedata.normalize('NFD', x or '')
            if not unicodedata.combining(c))
    return re.findall(r'[^\W_]+', deaccent((s or '').lower()), re.UNICODE)


def body_word_count(page):
    total = len(words_of(page.get('opening', '')))
    for s in page.get('sections', []) or []:
        total += len(words_of(s.get('heading', '')))
        total += len(words_of(s.get('text', '')))
    for f in page.get('faq', []) or []:
        total += len(words_of(f.get('q', '')))
        total += len(words_of(f.get('a', '')))
    return total


for iid in set(changed):
    by_id[iid]['word_count'] = body_word_count(by_id[iid])

with open(PATH, 'w', encoding='utf-8') as f:
    for p in pages:
        f.write(json.dumps(p, ensure_ascii=False))
        f.write('\n')

print('OK', sorted(set(changed)))
