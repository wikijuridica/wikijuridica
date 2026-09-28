#!/usr/bin/env python3
"""Applies the verified conflict-free replacements (checked in scratch
runs against telecom_energia-02.jsonl union-grams, intra-file grams, and
TELECOM01_PPP_SCOPE_RULES) to telecom_energia-01.jsonl."""
import hashlib
import json
import sys

sys.path.insert(0, 'tools')
import audit_v2_pages as a  # noqa: E402

PATH1 = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
PATH2 = 'data/editorial/v2_pages/telecom_energia-02.jsonl'
EXPECTED_SHA1 = 'bf714b9e58b6d94ce2479e5df7015580ee76b280a7fa7ef1287112fdcc28a485'

with open(PATH1, 'rb') as f:
    raw1 = f.read()
if hashlib.sha256(raw1).hexdigest() != EXPECTED_SHA1:
    print('CAS ABORT telecom-01', hashlib.sha256(raw1).hexdigest())
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
    ('tel-cobranca-servico-nao-contratado',
     'Até 5.000 acessos recebem só os arts. 4º, 5º e 7º.',
     'Até 5.000 acessos recebem só arts. 4º, 5º e 7º.'),
    ('tel-contestar-fatura-operadora',
     'Quem tem até 5.000 acessos permanece somente com os arts. 4º, '
     '5º e 7º, preservados CDC e LGT.',
     'Até 5.000 acessos recebem apenas os arts. 4º, 5º e 7º. '
     'Preservados CDC e LGT.'),
    ('tel-devolucao-em-dobro-telefonia',
     'Já a prestadora com até 5.000 acessos fica no piso dos arts. '
     '4º, 5º e 7º; a restituição continua examinada pelo art. 42 do '
     'CDC enquanto a LGT assegura reparação em termos gerais, sem '
     'que prazo, juros ou demais automatismos regulatórios sejam '
     'importados automaticamente.',
     'Prestadoras com até 5.000 acessos recebem somente os arts. 4º, '
     '5º e 7º. A restituição continua examinada pelo art. 42 do CDC '
     'enquanto a LGT assegura reparação em termos gerais. Ainda '
     'assim, prazo, juros e demais automatismos regulatórios não '
     'devem ser importados automaticamente.'),
    ('tel-linha-no-meu-cpf-fraude',
     'Prestadoras com até 5.000 acessos seguem apenas os arts. 4º, '
     '5º e 7º, CDC, LGT e LGPD continuam protegendo cadastro e '
     'dados.',
     'Para até 5.000 acessos, contêm apenas os arts. 4º, 5º e 7º. '
     'CDC, LGT e LGPD continuam protegendo cadastro e dados.'),
    ('tel-parcelas-aparelho-nao-comprado',
     'Uma prestadora com até 5.000 acessos segue apenas os arts. 4º, '
     '5º e 7º, permanecendo CDC e LGT aplicáveis à relação; a LGPD '
     'segue igualmente vigente.',
     'Na prestadora com até 5.000 acessos, o RGC conserva somente os '
     'arts. 4º, 5º e 7º. Permanecendo CDC e LGT aplicáveis à relação, '
     'a LGPD segue igualmente vigente.'),
    ('tel-mudanca-plano-nao-autorizada',
     'A faixa de até 5.000 recebe apenas os arts. 4º, 5º e 7º; CDC e '
     'LGT permanecem aplicáveis.',
     'Para prestadoras com até 5.000 acessos, o art. 90, parágrafo '
     '5º, mantém apenas os arts. 4º, 5º e 7º. CDC e LGT permanecem '
     'aplicáveis.'),
    ('tel-negativacao-conta-telefone-contestada',
     'Na faixa de até 5.000, valem apenas os arts. 4º, 5º e 7º, '
     'mantidos CDC e LGT.',
     'Até 5.000 acessos recebem só arts. 4º, 5º e 7º. Mantidos CDC e '
     'LGT.'),
    ('tel-fatura-papel-cobrada',
     'Para a prestadora com até 5.000 acessos, o § 5º mantém somente '
     'os arts. 4º, 5º e 7º, com CDC e LGT continuam aplicáveis.',
     'Até 5.000 acessos recebem apenas os arts. 4º, 5º e 7º. Com CDC '
     'e LGT continuam aplicáveis.'),
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

# Final in-process verification before writing.
union1 = set()
for p in pages1:
    union1 |= page_grams(p)
overlap_02 = union1 & FORBIDDEN2
print('remaining overlap vs telecom-02:', len(overlap_02))
if overlap_02:
    for g in overlap_02:
        print('  ', ' '.join(g))
    print('ABORT: not writing, overlap remains')
    sys.exit(4)

for iid, _, _ in FIXES:
    if iid in a.TELECOM01_PPP_SCOPE_RULES:
        page = by1[iid]
        visible = '\n'.join(t for _, t in a.labeled_visible_parts(page))
        code, groups = a.TELECOM01_PPP_SCOPE_RULES[iid]
        for gi, alts in enumerate(groups):
            ok = any(a.criminal13_declarative_alternative_affirmed_in_text(
                visible, alt) for alt in alts)
            if not ok:
                print('SCOPE FAIL', iid, gi)
                sys.exit(5)

with open(PATH1, 'w', encoding='utf-8') as f:
    for p in pages1:
        f.write(json.dumps(p, ensure_ascii=False))
        f.write('\n')

print('OK wrote', PATH1)
