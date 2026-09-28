#!/usr/bin/env python3
import hashlib
import json
import sys

PATH = 'data/editorial/v2_pages/telecom_energia-01.jsonl'
EXPECTED_SHA = '2c7535a67fe4523520c824dd14ef1a2bb6f5ea78680edb6ae279e75ea25fa4ab'

with open(PATH, 'rb') as f:
    raw = f.read()
actual_sha = hashlib.sha256(raw).hexdigest()
if actual_sha != EXPECTED_SHA:
    print('CAS ABORT', actual_sha)
    sys.exit(1)

lines = raw.decode('utf-8').splitlines()
pages = [json.loads(l) for l in lines if l.strip()]
by_id = {p['intent_id']: p for p in pages}


def sub(page, field_getter, field_setter, old, new, label):
    text = field_getter(page)
    if old not in text:
        print('MISSING', label, page['intent_id'])
        sys.exit(2)
    if text.count(old) != 1:
        print('NOT UNIQUE', label, page['intent_id'])
        sys.exit(2)
    field_setter(page, text.replace(old, new))


def opening_get(p):
    return p['opening']


def opening_set(p, v):
    p['opening'] = v


FIXES = [
    ('tel-cobranca-servico-nao-contratado',
     'contratação, cobrança e restituição seguem sujeitas à oferta, ao '
     'CDC e à LGT',
     'contratação, cobrança e restituição continuam sujeitas à oferta, '
     'ao CDC e à LGT'),
    ('tel-contestar-fatura-operadora',
     'preservados CDC e LGT. A ouvidoria só cabe quando esse canal '
     'integrar o regime da prestadora.',
     'preservados CDC e LGT. Use a ouvidoria apenas se esse canal '
     'integrar o regime da prestadora.'),
    ('tel-devolucao-em-dobro-telefonia',
     'a restituição segue examinada pelo art. 42 do CDC, e a LGT '
     'assegura reparação em termos gerais',
     'a restituição continua examinada pelo art. 42 do CDC enquanto a '
     'LGT assegura reparação em termos gerais'),
    ('tel-fatura-diferente-da-oferta',
     'com os arts. 34 e 55, X, e também os arts. 87 a 89 permanecendo '
     'excluídos; já o art. 21 é condicional, dependendo da opção pela '
     'ferramenta comparadora ou de determinação específica da Anatel.',
     'os arts. 34 e 55, X, permanecem excluídos, assim como os arts. '
     '87 a 89; já o art. 21 é condicional, dependendo da opção pela '
     'ferramenta comparadora ou de determinação específica da Anatel.'),
    ('tel-fatura-papel-cobrada',
     'com o inciso III do art. 13 e o inciso X do art. 55 permanecendo '
     'excluídos. Na faixa de até 5.000 permanecem apenas os arts. 4º, '
     '5º e 7º, com CDC e LGT continuando aplicáveis, sem que '
     'antecedência, meio eletrônico ou gratuidade de artigos excluídos '
     'sejam importados automaticamente.',
     'O inciso III do art. 13 permanece excluído. O inciso X do art. '
     '55 permanece excluído. Na faixa de até 5.000 permanecem apenas '
     'os arts. 4º, 5º e 7º, com CDC e LGT continuam aplicáveis, sem '
     'que antecedência, meio eletrônico ou gratuidade de artigos '
     'excluídos sejam importados automaticamente.'),
    ('tel-ligacoes-nao-reconhecidas',
     'Na faixa de até 5.000 acessos, o RGC conserva somente os arts. '
     '4º, 5º e 7º; CDC, LGT e RGST permanecem aplicáveis. A ouvidoria '
     'só entra na sequência quando esse canal existir no regime da '
     'empresa.',
     'Na faixa de até 5.000 acessos, conserva somente os arts. 4º, 5º '
     'e 7º; CDC, LGT e RGST permanecem aplicáveis. A ouvidoria só '
     'participa quando esse canal existir no regime da empresa.'),
    ('tel-roaming-internacional-conta-alta',
     'para a PPP, o art. 21 passa a ser condicional conforme a opção '
     'pela ferramenta comparadora ou a determinação da Anatel, '
     'permanecendo excluído o art. 59. Para até 5.000 acessos, restam '
     'apenas os arts. 4º, 5º e 7º, com RGST, CDC e LGT ainda '
     'aplicáveis. Recorra à ouvidoria só se esse canal integrar o '
     'regime da prestadora.',
     'para a PPP, o art. 21 é condicional conforme a opção pela '
     'ferramenta comparadora ou a determinação da Anatel, e o art. 59 '
     'permanece excluído. Para até 5.000 acessos, restam apenas os '
     'arts. 4º, 5º e 7º, com RGST, CDC e LGT ainda aplicáveis. Use a '
     'ouvidoria apenas se esse canal integrar o regime da prestadora.'),
    ('tel-linha-no-meu-cpf-fraude',
     'com CDC, LGT e LGPD continuando a proteger cadastro e dados.',
     'CDC, LGT e LGPD continuam protegendo cadastro e dados.'),
    ('tel-mudanca-plano-nao-autorizada',
     'Na prestadora com até 5.000 acessos, o RGC se limita aos arts. '
     '4º, 5º e 7º, sem prejuízo do CDC e da LGT.',
     'Na prestadora com até 5.000 acessos, permanecem somente os arts. '
     '4º, 5º e 7º, sem prejuízo do CDC e da LGT.'),
    ('tel-negativacao-conta-telefone-contestada',
     'Na empresa com até 5.000 acessos, o RGC conserva somente os '
     'arts. 4º, 5º e 7º, mantidos CDC e LGT. A escalada à ouvidoria só '
     'se aplica quando esse canal existir no regime da prestadora.',
     'Para quem tem até 5.000 acessos, permanecem somente os arts. 4º, '
     '5º e 7º, mantidos CDC e LGT. A ouvidoria só integra a escalada '
     'quando existir no regime da prestadora.'),
    ('tel-parcelas-aparelho-nao-comprado',
     'Para prestadora com até 5.000 acessos, o RGC se restringe aos '
     'arts. 4º, 5º e 7º, sem afastar CDC, LGT e LGPD. Recorra à '
     'ouvidoria apenas se a prestadora mantiver esse canal.',
     'Uma prestadora com até 5.000 acessos segue apenas os arts. 4º, '
     '5º e 7º, sem afastar CDC e LGT; a LGPD permanece igualmente '
     'aplicável. A ouvidoria só deve ser usada se a prestadora '
     'mantiver esse canal.'),
]

changed = []
for iid, old, new in FIXES:
    page = by_id[iid]
    found_in_opening = old in page['opening']
    if found_in_opening:
        sub(page, opening_get, opening_set, old, new, 'opening')
        changed.append(iid)
        continue
    found_in_section = False
    for s in page['sections']:
        if old in s['text']:
            if s['text'].count(old) != 1:
                print('NOT UNIQUE section', iid)
                sys.exit(2)
            s['text'] = s['text'].replace(old, new)
            found_in_section = True
            break
    if not found_in_section:
        print('MISSING (neither opening nor section)', iid)
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

print('OK changed:', sorted(set(changed)))
