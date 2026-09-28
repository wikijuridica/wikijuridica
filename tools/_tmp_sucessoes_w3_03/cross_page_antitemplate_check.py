#!/usr/bin/env python3
"""Varredura anti-molde CROSS-PAGE dentro do proprio lote (nao substitui o
auditor canonico global, que compara contra TODO o estoque -- isso aqui e
so uma rede de seguranca local antes da autoauditoria oficial)."""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, '/sessions/focused-kind-bohr/mnt/wiki')
from tools.audit_v2_pages import norm_key, VOCAB_RE, GENERIC_HEADINGS, is_generic_heading

WORKDIR = Path(sys.argv[1])
files = sorted(WORKDIR.glob("p*.json"))

all_headings = {}
all_sentences = {}
problems = []

SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def sentences_of(text):
    return [s.strip() for s in SENT_SPLIT_RE.split(text or '') if len(s.strip()) > 25]


for path in files:
    data = json.loads(path.read_text(encoding='utf-8'))
    intent = data.get('intent_id')

    # vocabulario interno banido em qualquer campo visivel
    visible = [data.get('title', ''), data.get('meta_description', ''), data.get('h1', ''), data.get('opening', '')]
    for s in data.get('sections', []) or []:
        visible += [s.get('heading', ''), s.get('text', '')]
    for f in data.get('faq', []) or []:
        visible += [f.get('q', ''), f.get('a', '')]
    for v in visible:
        m = VOCAB_RE.search(v or '')
        if m:
            problems.append(f"{path.name} ({intent}): vocabulario interno banido {m.group()!r} em {v[:60]!r}")

    # headings duplicados entre paginas do lote + genericos banidos globalmente
    for s in data.get('sections', []) or []:
        h = s.get('heading', '')
        k = norm_key(h)
        if is_generic_heading(h):
            problems.append(f"{path.name} ({intent}): heading generico banido: {h!r}")
        if k in all_headings:
            problems.append(
                f"{path.name} ({intent}): heading repetido do lote (tambem em "
                f"{all_headings[k]}): {h!r}")
        else:
            all_headings[k] = f"{path.name} ({intent})"

    # frases (>25 chars) repetidas verbatim entre paginas do lote
    for v in visible:
        for sent in sentences_of(v):
            key = norm_key(sent)
            if not key:
                continue
            if key in all_sentences and all_sentences[key][0] != path.name:
                problems.append(
                    f"{path.name} ({intent}): frase repetida do lote (tambem em "
                    f"{all_sentences[key][1]}): {sent[:90]!r}")
            else:
                all_sentences[key] = (path.name, f"{path.name} ({intent})")

if problems:
    print(f"{len(problems)} PROBLEMA(S):")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print(f"OK: {len(files)} paginas, {len(all_headings)} headings unicos, sem vocabulario interno, sem frase repetida >25 chars")
