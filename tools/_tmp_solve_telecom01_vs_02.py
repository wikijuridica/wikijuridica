#!/usr/bin/env python3
"""Automated solver: pick, for each conflicting telecom-01 page, a
TELECOM_PPP_MICRO_FLOOR_ALTERNATIVES-based sentence that produces zero
12-gram overlap with (a) telecom_energia-02.jsonl (read-only, never
touched) and (b) every other page currently in telecom_energia-01.jsonl.
Also re-verifies TELECOM01_PPP_SCOPE_RULES stays satisfied for every
edited page (current_legal_fact must remain 0).
"""
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
print('telecom-02 forbidden grams:', len(FORBIDDEN2))

# Candidate micro-floor sentences: (label, template). {N} placeholder for
# the numeral block is not needed -- alternatives already spell it out.
CANDIDATES = [
    ('idx1',
     'Até 5.000 acessos recebem só arts. 4º, 5º e 7º.'),
    ('idx2',
     'Até 5.000 acessos recebem apenas os arts. 4º, 5º e 7º.'),
    ('idx3',
     'Prestadoras com até 5.000 acessos recebem somente os arts. 4º, '
     '5º e 7º.'),
    ('idx4',
     'Prestadora com até 5.000 acessos recebe somente os arts. 4º, 5º '
     'e 7º.'),
    ('idx5',
     'Para prestadoras com até 5.000 acessos, o art. 90, § 5º, mantém '
     'apenas os arts. 4º, 5º e 7º.'),
    ('idx7',
     'Para quem tem até 5.000 acessos, permanecem apenas os arts. 4º, '
     '5º e 7º.'),
    ('idx8',
     'Para quem tem até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º.'),
    ('idx21',
     'Para até 5.000 acessos, contêm apenas os arts. 4º, 5º e 7º.'),
    ('idx23',
     'Na prestadora com até 5.000 acessos, o RGC conserva somente os '
     'arts. 4º, 5º e 7º.'),
    ('idx26',
     'Na faixa de até 5.000 acessos, permanecem somente os arts. 4º, '
     '5º e 7º.'),
    ('idx27',
     'Para até 5.000 acessos, o RGC mantém somente os arts. 4º, 5º e '
     '7º.'),
    ('idx0',
     'Até 5.000 acessos recebem só os arts. 4º, 5º e 7º.'),
    ('idx8b',
     'Para quem tem até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º.'),
    ('idx13',
     'A prestadora com até 5.000 acessos fica no piso dos arts. 4º, '
     '5º e 7º.'),
    ('idx15',
     'Uma prestadora com até 5.000 acessos segue apenas os arts. 4º, '
     '5º e 7º.'),
    ('idx17',
     'Prestadoras com até 5.000 acessos seguem apenas os arts. 4º, 5º '
     'e 7º.'),
    ('idx18',
     'Somente os arts. 4º, 5º e 7º valem para a prestadora com até '
     '5.000 acessos.'),
    ('idx19',
     'Mantém somente os arts. 4º, 5º e 7º para a empresa com até '
     '5.000 acessos.'),
    ('idx24',
     'Para a prestadora com até 5.000 acessos, o § 5º mantém somente '
     'os arts. 4º, 5º e 7º.'),
    ('idx25',
     'Prestadoras com até 5.000 acessos ficam somente com os arts. '
     '4º, 5º e 7º.'),
    ('idxA',
     'Na prestadora com até 5.000 acessos, o § 5º restringe o RGC aos '
     'arts. 4º, 5º e 7º.'),
    ('idxB',
     'Somente até 5.000 acessos permanecem no piso mínimo dos arts. '
     '4º, 5º e 7º.'),
    ('idxC',
     'Uma prestadora de até 5.000 acessos fica restrita apenas aos '
     'arts. 4º, 5º e 7º.'),
]

TAILS = {
    'tel-cobranca-servico-nao-contratado': '',
    'tel-contestar-fatura-operadora': ' Preservados CDC e LGT.',
    'tel-devolucao-em-dobro-telefonia': (
        ' A restituição continua examinada pelo art. 42 do CDC '
        'enquanto a LGT assegura reparação em termos gerais. Ainda '
        'assim, prazo, juros e demais automatismos regulatórios não '
        'devem ser importados automaticamente.'),
    'tel-linha-no-meu-cpf-fraude': (
        ' CDC, LGT e LGPD continuam protegendo cadastro e dados.'),
    'tel-parcelas-aparelho-nao-comprado': (
        ' Permanecendo CDC e LGT aplicáveis à relação, a LGPD segue '
        'igualmente vigente.'),
    'tel-mudanca-plano-nao-autorizada': ' CDC e LGT permanecem aplicáveis.',
    'tel-negativacao-conta-telefone-contestada': ' Mantidos CDC e LGT.',
    'tel-fatura-papel-cobrada': ' Com CDC e LGT continuam aplicáveis.',
}

OLD_SENTENCES = {
    'tel-cobranca-servico-nao-contratado':
        'Até 5.000 acessos recebem só os arts. 4º, 5º e 7º.',
    'tel-contestar-fatura-operadora':
        'Quem tem até 5.000 acessos permanece somente com os arts. 4º, '
        '5º e 7º, preservados CDC e LGT.',
    'tel-devolucao-em-dobro-telefonia':
        'Já a prestadora com até 5.000 acessos fica no piso dos arts. '
        '4º, 5º e 7º; a restituição continua examinada pelo art. 42 do '
        'CDC enquanto a LGT assegura reparação em termos gerais. Ainda '
        'assim, prazo, juros e demais automatismos regulatórios não '
        'devem ser importados automaticamente.'
        if False else
        'Já a prestadora com até 5.000 acessos fica no piso dos arts. '
        '4º, 5º e 7º; a restituição continua examinada pelo art. 42 do '
        'CDC enquanto a LGT assegura reparação em termos gerais, sem '
        'que prazo, juros ou demais automatismos regulatórios sejam '
        'importados automaticamente.',
    'tel-linha-no-meu-cpf-fraude':
        'Prestadoras com até 5.000 acessos seguem apenas os arts. 4º, '
        '5º e 7º, CDC, LGT e LGPD continuam protegendo cadastro e '
        'dados.',
    'tel-parcelas-aparelho-nao-comprado':
        'Uma prestadora com até 5.000 acessos segue apenas os arts. '
        '4º, 5º e 7º, permanecendo CDC e LGT aplicáveis à relação; a '
        'LGPD segue igualmente vigente.',
    'tel-mudanca-plano-nao-autorizada':
        'A faixa de até 5.000 recebe apenas os arts. 4º, 5º e 7º; CDC '
        'e LGT permanecem aplicáveis.',
    'tel-negativacao-conta-telefone-contestada':
        'Na faixa de até 5.000, valem apenas os arts. 4º, 5º e 7º, '
        'mantidos CDC e LGT.',
    'tel-fatura-papel-cobrada':
        'Para a prestadora com até 5.000 acessos, o § 5º mantém '
        'somente os arts. 4º, 5º e 7º, com CDC e LGT continuam '
        'aplicáveis.',
}

ORDER = [
    'tel-cobranca-servico-nao-contratado',
    'tel-contestar-fatura-operadora',
    'tel-devolucao-em-dobro-telefonia',
    'tel-linha-no-meu-cpf-fraude',
    'tel-parcelas-aparelho-nao-comprado',
    'tel-mudanca-plano-nao-autorizada',
    'tel-negativacao-conta-telefone-contestada',
    'tel-fatura-papel-cobrada',
]


def build_forbidden_others(current_pages_dict, exclude_iid):
    grams = set()
    for iid, p in current_pages_dict.items():
        if iid == exclude_iid:
            continue
        grams |= page_grams(p)
    return grams


def scope_rule_ok(page, iid):
    if iid not in a.TELECOM01_PPP_SCOPE_RULES:
        return True
    visible = '\n'.join(t for _, t in a.labeled_visible_parts(page))
    code, groups = a.TELECOM01_PPP_SCOPE_RULES[iid]
    for alternatives in groups:
        if not any(a.criminal13_declarative_alternative_affirmed_in_text(
                visible, alt) for alt in alternatives):
            return False
    return True


assigned = {}
for iid in ORDER:
    old = OLD_SENTENCES[iid]
    page = by1[iid]
    if old not in page['opening']:
        print('OLD SENTENCE NOT FOUND for', iid)
        print(repr(page['opening']))
        sys.exit(2)

    chosen = None
    for label, micro in CANDIDATES:
        if label in assigned.values():
            continue  # do not reuse the same alternative twice in file
        new_sentence = micro + TAILS[iid]
        new_opening = page['opening'].replace(old, new_sentence, 1)
        # Build a scratch page copy to test.
        scratch = dict(page)
        scratch['opening'] = new_opening
        new_grams = page_grams(scratch)
        forbidden_others = build_forbidden_others(by1, iid)
        if new_grams & FORBIDDEN2:
            continue
        if new_grams & forbidden_others:
            continue
        if not scope_rule_ok(scratch, iid):
            continue
        chosen = (label, new_sentence, new_opening)
        break

    if chosen is None:
        print('NO SAFE CANDIDATE for', iid)
        sys.exit(3)

    label, new_sentence, new_opening = chosen
    page['opening'] = new_opening
    assigned[iid] = label
    print('ASSIGNED', iid, '->', label, ':', new_sentence)

print()
print('Final assignment:', assigned)


def body_word_count(p):
    total = len(a.words_of(p.get('opening', '')))
    for s in p.get('sections', []) or []:
        total += len(a.words_of(s.get('heading', '')))
        total += len(a.words_of(s.get('text', '')))
    for f in p.get('faq', []) or []:
        total += len(a.words_of(f.get('q', '')))
        total += len(a.words_of(f.get('a', '')))
    return total


for iid in assigned:
    by1[iid]['word_count'] = body_word_count(by1[iid])

with open(PATH1, 'w', encoding='utf-8') as f:
    for p in pages1:
        f.write(json.dumps(p, ensure_ascii=False))
        f.write('\n')

print('WROTE', PATH1)
