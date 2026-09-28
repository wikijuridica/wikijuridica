#!/usr/bin/env python3
import hashlib
import json
import sys

PATH = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
EXPECTED_SHA = '851a935ee400c734a618e672a83ecda0d773bd8871ccd77f8f42465cd3320fa3'

with open(PATH, 'rb') as f:
    raw = f.read()
actual_sha = hashlib.sha256(raw).hexdigest()
if actual_sha != EXPECTED_SHA:
    print('CAS ABORT', actual_sha)
    sys.exit(1)

lines = raw.decode('utf-8').splitlines()
pages = [json.loads(l) for l in lines if l.strip()]
by_id = {p['intent_id']: p for p in pages}

FIXES = [
    ('tel-cobranca-servico-nao-contratado',
     'Nesse recorte, contratação, cobrança e restituição continuam '
     'sujeitas à oferta, ao CDC e à LGT, sem que o art. 48 vire '
     'obrigação setorial universal.',
     'Nesse recorte, contratação, cobrança e restituição continuam '
     'sujeitas à oferta, ao CDC e à LGT. Ainda assim, o art. 48 não '
     'deve ser apresentado como obrigação setorial universal.'),
    ('tel-fatura-papel-cobrada',
     'Na faixa de até 5.000 permanecem apenas os arts. 4º, 5º e 7º, '
     'com CDC e LGT continuam aplicáveis, sem que antecedência, meio '
     'eletrônico ou gratuidade de artigos excluídos sejam importados '
     'automaticamente.',
     'Na faixa de até 5.000 permanecem apenas os arts. 4º, 5º e 7º, '
     'com CDC e LGT continuam aplicáveis. Ainda assim, antecedência, '
     'meio eletrônico e gratuidade de artigos excluídos não devem ser '
     'presumidos automaticamente desse recorte.'),
    ('tel-parcelas-aparelho-nao-comprado',
     'Uma prestadora com até 5.000 acessos segue apenas os arts. 4º, '
     '5º e 7º, sem afastar CDC e LGT; a LGPD permanece igualmente '
     'aplicável.',
     'Uma prestadora com até 5.000 acessos segue apenas os arts. 4º, '
     '5º e 7º, permanecendo CDC e LGT aplicáveis à relação; a LGPD '
     'segue igualmente vigente.'),
    ('tel-roaming-internacional-conta-alta',
     'Para até 5.000 acessos, restam apenas os arts. 4º, 5º e 7º, com '
     'RGST, CDC e LGT ainda aplicáveis.',
     'Para até 5.000 acessos, restam apenas os arts. 4º, 5º e 7º, com '
     'RGST, CDC e LGT continuam aplicáveis.'),
]

changed = []
for iid, old, new in FIXES:
    page = by_id[iid]
    if old not in page['opening']:
        print('MISSING', iid)
        sys.exit(2)
    if page['opening'].count(old) != 1:
        print('NOT UNIQUE', iid)
        sys.exit(2)
    page['opening'] = page['opening'].replace(old, new)
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
