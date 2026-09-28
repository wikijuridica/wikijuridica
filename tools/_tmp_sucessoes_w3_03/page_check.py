#!/usr/bin/env python3
"""Pre-check leve (nao oficial) para uma pagina p<NN>.json antes do recount/CAS.

Uso: python3 page_check.py <arquivo.json> <intent_id-esperado>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, '/sessions/focused-kind-bohr/mnt/wiki')
from tools.audit_v2_pages import (
    is_generic_heading, source_host_allowed, body_word_count, norm_key,
)

BANDS = {'verbete': (350, 700), 'pergunta': (400, 800),
         'guia_problema': (700, 1400), 'procedimento': (500, 1000)}


def main():
    path = Path(sys.argv[1])
    expected_intent = sys.argv[2]
    page_type = sys.argv[3] if len(sys.argv) > 3 else None
    problems = []
    data = json.loads(path.read_text(encoding='utf-8'))

    if data.get('intent_id') != expected_intent:
        problems.append(f"intent_id mismatch: {data.get('intent_id')!r}")

    title = data.get('title', '')
    if not (20 <= len(title) <= 65):
        problems.append(f"title len={len(title)} (precisa 20-65): {title!r}")

    meta = data.get('meta_description', '')
    if not (70 <= len(meta) <= 160):
        problems.append(f"meta_description len={len(meta)} (precisa 70-160): {meta!r}")

    h1 = data.get('h1', '')
    if not h1:
        problems.append("h1 vazio")
    if h1 == title:
        problems.append("h1 igual ao title")

    lane = data.get('lane')
    if lane not in ('comercial', 'informativa'):
        problems.append(f"lane invalida: {lane!r}")

    sections = data.get('sections') or []
    if not sections:
        problems.append("sem sections")
    headings_seen = set()
    for s in sections:
        h = s.get('heading', '')
        k = norm_key(h)
        if is_generic_heading(h):
            problems.append(f"heading generico banido: {h!r}")
        if k in headings_seen:
            problems.append(f"heading duplicado no arquivo: {h!r}")
        headings_seen.add(k)
        if not (s.get('text') or '').strip():
            problems.append(f"section sem texto: {h!r}")

    faq = data.get('faq') or []
    if len(faq) > 4:
        problems.append(f"faq com {len(faq)} itens (max 4)")

    topics = [t for t in (data.get('internal_link_topics') or []) if str(t).strip()]
    if not (2 <= len(topics) <= 4):
        problems.append(f"internal_link_topics len={len(topics)} (precisa 2-4)")

    sources = data.get('official_sources') or []
    if not (2 <= len(sources) <= 5):
        problems.append(f"official_sources len={len(sources)} (precisa 2-5)")
    seen_urls = set()
    for src in sources:
        for field in ('name', 'url', 'anchor_claim'):
            if not (src.get(field) or '').strip():
                problems.append(f"source sem {field}: {src}")
        extra = set(src) - {'name', 'url', 'anchor_claim'}
        if extra:
            problems.append(f"source com campos extras (staged deve ter so name/url/anchor_claim): {extra}")
        url = src.get('url', '')
        if not source_host_allowed(url):
            problems.append(f"source host nao permitido: {url}")
        if url in seen_urls:
            problems.append(f"source URL duplicada: {url}")
        seen_urls.add(url)

    if page_type:
        band = BANDS.get(page_type)
        if band:
            real = body_word_count(data)
            lo, hi = band
            thin = lo * 9 // 10
            thick = hi * 11 // 10
            status = "OK"
            if real < thin:
                status = "THIN"
            elif real > thick:
                status = "ESTICADA"
            print(f"body_word_count={real} band={band} thin<{thin} thick>{thick} status={status}")

    min_sections = {'verbete': 2, 'pergunta': 2, 'procedimento': 3, 'guia_problema': 4}
    if page_type:
        need = min_sections.get(page_type, 4)
        total_sections = len(sections) + (1 if faq else 0)
        if total_sections < need:
            problems.append(f"secoes insuficientes: {total_sections} < {need} (page_type={page_type})")

    if problems:
        print("PROBLEMAS:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("PRE-CHECK OK")


if __name__ == '__main__':
    main()
