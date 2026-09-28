#!/usr/bin/env python3
import hashlib
import json
import sys

PATH = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
EXPECTED_SHA = '266702bb7ca4340446407c13942d7bf21c0e2c34c7fd106e5d351455cd7c26e9'

with open(PATH, 'rb') as f:
    raw = f.read()
actual_sha = hashlib.sha256(raw).hexdigest()
if actual_sha != EXPECTED_SHA:
    print('CAS ABORT', actual_sha)
    sys.exit(1)

lines = raw.decode('utf-8').splitlines()
pages = [json.loads(l) for l in lines if l.strip()]
by_id = {p['intent_id']: p for p in pages}

OLD_TAIL = (
    '\n\nEsse recorte por porte da prestadora — já explicado acima — '
    'vale também para o acesso digital ao documento: quem está fora '
    'do § 5º do art. 90 segue as partes incorporadas dos arts. 24, '
    '47, 54, 55, 60 e 99, sem o inciso III do art. 13, de modo que a '
    'consulta eletrônica não deve ser prometida a partir apenas '
    'desse dispositivo.'
)

page = by_id['tel-fatura-papel-cobrada']
found = False
for s in page['sections']:
    if OLD_TAIL in s['text']:
        if s['text'].count(OLD_TAIL) != 1:
            print('NOT UNIQUE')
            sys.exit(2)
        s['text'] = s['text'].replace(OLD_TAIL, '')
        found = True
        break
if not found:
    print('MISSING')
    sys.exit(2)


def words_of(s):
    import re
    import unicodedata

    def deaccent(x):
        return ''.join(
            c for c in unicodedata.normalize('NFD', x or '')
            if not unicodedata.combining(c))
    return re.findall(r'[^\W_]+', deaccent((s or '').lower()), re.UNICODE)


def body_word_count(p):
    total = len(words_of(p.get('opening', '')))
    for s in p.get('sections', []) or []:
        total += len(words_of(s.get('heading', '')))
        total += len(words_of(s.get('text', '')))
    for f in p.get('faq', []) or []:
        total += len(words_of(f.get('q', '')))
        total += len(words_of(f.get('a', '')))
    return total


page['word_count'] = body_word_count(page)
print('new word_count', page['word_count'])

with open(PATH, 'w', encoding='utf-8') as f:
    for p in pages:
        f.write(json.dumps(p, ensure_ascii=False))
        f.write('\n')
print('OK')
