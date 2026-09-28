#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe 4: gate de contencao de termos (destino evidencia o topico) + malha final."""
import json
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tmp_link_topic_resolution_probe import (  # noqa: E402
    slug_fold, content_tokens, seed_term, load_portfolio, load_pages,
)
from _tmp_link_topic_resolution_probe2 import public_path  # noqa: E402


def main():
    portfolio, _ = load_portfolio()
    pages, _, _ = load_pages(portfolio)
    ids = sorted(pages)
    idx = {iid: i for i, iid in enumerate(ids)}
    n = len(ids)
    areas = [pages[i]["area"] for i in ids]
    families = [pages[i]["family"] for i in ids]
    titles = [pages[i]["title"] for i in ids]
    routes = [public_path(pages[i]["area"], i) for i in ids]
    # Vitrine do destino: o que o LEITOR ve no link (titulo) + h1 + seed da rota.
    showcase = [set(content_tokens(pages[i]["title"], pages[i]["h1"], seed_term(i))) for i in ids]

    by_key = defaultdict(list)
    by_desc = defaultdict(list)
    for iid in ids:
        i = idx[iid]
        for key in (slug_fold(iid), slug_fold(seed_term(iid))):
            if key:
                by_key[key].append(i)
        page = pages[iid]
        for descriptor in (page["title"], page["h1"], page["ltq"], page["wt"], page["rp"]):
            key = slug_fold(descriptor)
            if key:
                by_desc[key].append(i)
    gloss = {i for i in range(n) if areas[i] == "glossario"}

    df = Counter()
    postings = defaultdict(list)
    tokcount = [0] * n
    for iid in ids:
        page = pages[iid]
        bag = set(content_tokens(seed_term(iid), page["title"], page["h1"],
                                 page["ltq"], page["family"], page["wt"], page["rp"]))
        tokcount[idx[iid]] = len(bag)
        for tok in bag:
            df[tok] += 1
            postings[tok].append(idx[iid])
    max_df = max(2, math.ceil(n * 0.20))
    idf = {t: math.log(1.0 + n / c) for t, c in df.items() if c <= max_df}

    def ranked(topic, area):
        query = sorted(set(content_tokens(topic)))
        weight = 0.0
        acc = defaultdict(float)
        matched = Counter()
        for tok in query:
            w = idf.get(tok)
            if w is None:
                continue
            weight += w
            for node in postings[tok]:
                if areas[node] != area:
                    continue
                acc[node] += w
                matched[node] += 1
        if weight <= 0:
            return []
        out = [(v / weight, k) for k, v in acc.items() if matched[k] >= 2]
        out.sort(key=lambda p: (-p[0], tokcount[p[1]], p[1]))
        return out

    def contains(topic, node):
        """Gate: a vitrine do destino evidencia TODOS os termos do topico."""
        q = set(content_tokens(topic))
        return bool(q) and q <= showcase[node]

    stats = Counter()
    mesh = defaultdict(list)
    sem_destino = Counter()
    cache = {}
    for iid in ids:
        src = idx[iid]
        area = areas[src]
        for topic in pages[iid]["topics"]:
            key = slug_fold(topic)
            exact = [c for c in dict.fromkeys(by_key.get(key, []) + by_desc.get(key, [])) if c != src]
            same = [c for c in exact if areas[c] == area]
            if same:
                stats["A"] += 1
                mesh[src].append((same[0], "A"))
                continue
            g = [c for c in exact if c in gloss]
            if g:
                stats["B"] += 1
                mesh[src].append((g[0], "B"))
                continue
            if exact:
                stats["descartado_outra_area"] += 1
                continue
            ck = (topic, area)
            if ck not in cache:
                cache[ck] = ranked(topic, area)
            cands = cache[ck]
            if not cands or cands[0][0] < 0.50:
                stats["descartado_sem_destino"] += 1
                sem_destino[topic] += 1
                continue
            best_score = cands[0][0]
            tied = [node for score, node in cands if best_score - score < 0.05]
            gated = [node for node in tied if contains(topic, node)]
            if len(tied) == 1:
                node = tied[0]
                if contains(topic, node):
                    stats["C_unico_com_gate"] += 1
                    mesh[src].append((node, "C"))
                else:
                    stats["descartado_C_sem_gate"] += 1
                continue
            if len(gated) == 1:
                stats["D_empate_resolvido_por_gate"] += 1
                mesh[src].append((gated[0], "D"))
            elif len(gated) > 1:
                fam = [x for x in gated if families[src] and families[x] == families[src]]
                stats["D_empate_gate_multiplo_familia" if fam else "D_empate_gate_multiplo_especifico"] += 1
                mesh[src].append(((fam or gated)[0], "D"))
            else:
                stats["descartado_empate_sem_gate"] += 1

    # Corte do cap por PRIORIDADE DE TIER (A > B > C > D), estavel na ordem dos
    # topicos dentro do tier: sem isso um link de identidade exata na 4a posicao
    # seria descartado em favor de um semantico na 1a.
    priority = {"A": 0, "B": 1, "C": 2, "D": 3}
    for src in mesh:
        mesh[src] = sorted(mesh[src], key=lambda pair: priority[pair[1]])

    edges = set()
    kinds = Counter()
    for src, targets in mesh.items():
        seen = set()
        for node, kind in targets:
            if node in seen or node == src or not routes[node]:
                continue
            seen.add(node)
            if len(seen) > 3:
                break
            edges.add((src, node))
            kinds[kind] += 1

    out_deg, in_deg = Counter(), Counter()
    for a, b in edges:
        out_deg[a] += 1
        in_deg[b] += 1
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = Counter(find(i) for i in range(n))
    sizes = sorted(comps.values(), reverse=True)
    recip = sum(1 for a, b in edges if (b, a) in edges)
    bytes_by_page = []
    for src, targets in mesh.items():
        total = 132
        seen = set()
        for node, _ in targets:
            if node in seen or node == src or not routes[node]:
                continue
            seen.add(node)
            if len(seen) > 3:
                break
            total += len(routes[node]) + len(titles[node]) + 24
        bytes_by_page.append(total)
    bytes_by_page.sort()

    report = {
        "classificacao_das_30628_referencias": dict(stats),
        "arestas_por_tier": dict(kinds),
        "malha_final": {
            "arestas": len(edges),
            "paginas_com_saida": len(out_deg),
            "paginas_sem_saida": n - len(out_deg),
            "saida_media": round(len(edges) / n, 2),
            "saida_max": max(out_deg.values()) if out_deg else 0,
            "paginas_sem_entrada": n - len(in_deg),
            "entrada_max": max(in_deg.values()) if in_deg else 0,
            "entrada_acima_de_20": sum(1 for v in in_deg.values() if v > 20),
            "reciprocidade": round(recip / max(len(edges), 1), 3),
            "componentes": len(sizes),
            "maior_componente": sizes[0] if sizes else 0,
            "isolados": sum(1 for s in sizes if s == 1),
        },
        "gap_de_portfolio": {
            "topicos_distintos_sem_destino": len(sem_destino),
            "top_30": sem_destino.most_common(30),
        },
        "bytes_secao_relacionados": {
            "p50": bytes_by_page[len(bytes_by_page) // 2] if bytes_by_page else 0,
            "p95": bytes_by_page[int(len(bytes_by_page) * 0.95)] if bytes_by_page else 0,
            "max": bytes_by_page[-1] if bytes_by_page else 0,
        },
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
