#!/usr/bin/env python3
import hashlib
import json
import sys

PATH = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
EXPECTED_SHA = '0c33e83be7ec91f01f22f99b0f5cfbac2dc7b3da1c4cab7193bf7905028cf34d'

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
     '5º e 7º, com CDC e LGT continuando decisivos.',
     'Para até 5.000 acessos, permanecem apenas os arts. 4º, 5º e 7º, '
     'com CDC e LGT continuando decisivos.'),
    ('tel-negativacao-conta-telefone-contestada',
     'Para quem tem até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º, mantidos CDC e LGT.',
     'Para quem tem até 5.000 acessos, permanecem apenas os arts. 4º, '
     '5º e 7º, mantidos CDC e LGT.'),
    ('tel-cobranca-servico-nao-contratado',
     'os arts. 47 e 60 a 65 integram o regime ordinário, mas o art. '
     '48 permanece excluído.',
     'os arts. 47 e 60 a 65 alcançam o regime ordinário, mas o art. '
     '48 permanece excluído.'),
    ('tel-contestar-fatura-operadora',
     'Use a ouvidoria apenas se esse canal integrar o regime da '
     'prestadora.',
     'Procure a ouvidoria apenas quando esse canal existir no regime '
     'da empresa.'),
]

SECTION_FIXES = [
    ('tel-devolucao-em-dobro-telefonia',
     'a ouvidoria pode anteceder a Anatel; para PPP, o art. 90 não '
     'incorpora os arts. 87 a 89 e esse degrau não deve ser inventado.',
     'a ouvidoria pode anteceder a Anatel; na PPP, os arts. 87 a 89 '
     'seguem fora do art. 90, de modo que esse degrau não deve ser '
     'inventado.'),
    ('tel-fatura-papel-cobrada',
     'Para PPP, os arts. 87 a 89 ficam fora do art. 90, e a '
     'reclamação pode seguir do atendimento disponível à plataforma '
     'Anatel Consumidor.',
     'Na PPP, o art. 90 não recebe os arts. 87 a 89, de modo que a '
     'reclamação pode seguir do atendimento disponível direto à '
     'plataforma Anatel Consumidor.'),
]

changed = []
for iid, old, new in OPENING_FIXES:
    page = by_id[iid]
    if old not in page['opening'] or page['opening'].count(old) != 1:
        print('OPENING MISMATCH', iid)
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
