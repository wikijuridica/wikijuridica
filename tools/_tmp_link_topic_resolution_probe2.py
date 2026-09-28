#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe 2: regra de resolucao topico->rota, buckets de falha e malha final.

Read-only. Reusa a normalizacao de internal/v2internallinkgraph/tokens.go.
"""
import glob
import json
import math
import os
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tmp_link_topic_resolution_probe import (  # noqa: E402
    ROOT, slug_fold, content_tokens, seed_term, load_portfolio, load_pages,
)

RESERVED = {"buscar", "contato", "sobre", "aviso-legal", "fonte-oficial", "wiki"}


def public_path(area, intent_id):
    """Replica publicPathFor de internal/v2internallinkgraph/graph.go."""
    seed = seed_term(intent_id)
    if not area or area.strip() != area or not seed:
        return ""
    if slug_ascii(area) != area or slug_ascii(intent_id) != intent_id:
        return ""
    path = "/%s/%s/" % (slug_ascii(area), slug_ascii(seed))
    segments = [s for s in path.strip("/").split("/")]
    if len(segments) != 2 or not all(segments) or segments[0] in RESERVED:
        return ""
    return path


def slug_ascii(text):
    """Replica publicpath.Slug: NAO dobra acento (acento vira separador)."""
    out = []
    token = []
    for ch in text.lower():
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            token.append(ch)
        else:
            if token:
                out.append("".join(token))
                token = []
    if token:
        out.append("".join(token))
    return "-".join(out)


def main():
    portfolio, _ = load_portfolio()
    pages, tombstones, _ = load_pages(portfolio)
    ids = sorted(pages)
    idx = {iid: i for i, iid in enumerate(ids)}
    n = len(ids)
    areas = [pages[i]["area"] for i in ids]
    families = [pages[i]["family"] for i in ids]

    # ---- rota real de cada pagina ---------------------------------------
    routes = []
    no_route = []
    for iid in ids:
        path = public_path(pages[iid]["area"], iid)
        routes.append(path)
        if not path:
            no_route.append(iid)

    # ---- indices de identidade ------------------------------------------
    by_key = defaultdict(list)   # slugFold(intent|seed) -> nodes
    by_desc = defaultdict(list)  # slugFold(descritor) -> nodes
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

    gloss_nodes = {i for i in range(n) if areas[i] == "glossario"}

    # ---- TF-IDF ----------------------------------------------------------
    df = Counter()
    postings = defaultdict(list)
    for iid in ids:
        page = pages[iid]
        bag = set(content_tokens(seed_term(iid), page["title"], page["h1"],
                                 page["ltq"], page["family"], page["wt"], page["rp"]))
        for tok in bag:
            df[tok] += 1
            postings[tok].append(idx[iid])
    max_df = max(2, math.ceil(n * 0.20))
    idf = {t: math.log(1.0 + n / c) for t, c in df.items() if c <= max_df}

    def semantic(topic, from_area):
        query = sorted(set(content_tokens(topic)))
        weight = 0.0
        acc = defaultdict(float)
        matched = Counter()
        known = 0
        for tok in query:
            w = idf.get(tok)
            if w is None:
                continue
            known += 1
            weight += w
            for node in postings[tok]:
                if from_area and areas[node] != from_area:
                    continue
                acc[node] += w
                matched[node] += 1
        if weight <= 0 or not acc:
            return None, 0.0, 0.0, known
        ranked = sorted(((v / weight, k) for k, v in acc.items() if matched[k] >= 2), reverse=True)
        if not ranked:
            return None, 0.0, 0.0, known
        best_score, best = ranked[0]
        second = ranked[1][0] if len(ranked) > 1 else 0.0
        return best, best_score, second, known

    # ---- classificacao referencia a referencia ---------------------------
    buckets = Counter()
    dialect = Counter()
    tierA, tierB, tierC = [], [], []
    fail_samples = defaultdict(list)
    semantic_family = Counter()
    cache = {}

    for iid in ids:
        from_idx = idx[iid]
        area = areas[from_idx]
        for topic in pages[iid]["topics"]:
            is_free = (" " in topic) or (topic != slug_fold(topic))
            dialect["freetext" if is_free else "slug"] += 1
            key = slug_fold(topic)
            exact = list(dict.fromkeys(by_key.get(key, []) + by_desc.get(key, [])))
            same_area = [c for c in exact if areas[c] == area and c != from_idx]
            if same_area:
                buckets["A_identidade_mesma_area"] += 1
                tierA.append((from_idx, same_area[0]))
                continue
            gloss = [c for c in exact if c in gloss_nodes and c != from_idx]
            if gloss:
                buckets["B_glossario_global"] += 1
                dialect["freetext_to_gloss" if is_free else "slug_to_gloss"] += 1
                tierB.append((from_idx, gloss[0]))
                continue
            other = [c for c in exact if c != from_idx]
            if other:
                buckets["B2_identidade_outra_area_nao_glossario"] += 1
                fail_samples["outra_area"].append((iid, topic, ids[other[0]], areas[other[0]]))
                continue
            if exact:
                buckets["auto_referencia"] += 1
                continue
            ck = (topic, area)
            if ck not in cache:
                cache[ck] = semantic(topic, area)
            best, score, second, known = cache[ck]
            if best is not None and score >= 0.50 and score - second >= 0.05:
                buckets["C_semantico_mesma_area"] += 1
                same_fam = families[from_idx] and families[from_idx] == families[best]
                semantic_family["mesma_familia" if same_fam else "familia_diferente"] += 1
                tierC.append((from_idx, best, score, bool(same_fam)))
            elif best is not None and score >= 0.50:
                buckets["FALHA_ambiguo_margem"] += 1
                fail_samples["ambiguo"].append((iid, topic, round(score, 3)))
            elif known == 0:
                buckets["FALHA_sem_sinal"] += 1
                fail_samples["sem_sinal"].append((iid, topic))
            else:
                buckets["FALHA_abaixo_limiar"] += 1
                fail_samples["abaixo_limiar"].append((iid, topic, round(score, 3)))

    # ---- malha final: A + B + C(mesma familia), cap 3 por pagina ---------
    def build_mesh(cap, use_c, c_family_only):
        out = defaultdict(list)
        for a, b in tierA:
            out[a].append(b)
        for a, b in tierB:
            out[a].append(b)
        if use_c:
            for a, b, score, same_fam in sorted(tierC, key=lambda e: -e[2]):
                if c_family_only and not same_fam:
                    continue
                out[a].append(b)
        edges = set()
        for a, targets in out.items():
            for b in list(dict.fromkeys(targets))[:cap]:
                if routes[a] and routes[b] and a != b:
                    edges.add((a, b))
        return edges

    def metrics(edges):
        out_deg = Counter()
        in_deg = Counter()
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
        return {
            "edges": len(edges),
            "pages_with_out": len(out_deg),
            "pages_out_zero": n - len(out_deg),
            "avg_out_all": round(len(edges) / n, 2),
            "max_out": max(out_deg.values()) if out_deg else 0,
            "pages_zero_in": n - len(in_deg),
            "in_max": max(in_deg.values()) if in_deg else 0,
            "in_over_20": sum(1 for v in in_deg.values() if v > 20),
            "reciprocity": round(recip / max(len(edges), 1), 3),
            "components": len(sizes),
            "largest_component": sizes[0] if sizes else 0,
            "singletons": sum(1 for s in sizes if s == 1),
        }

    # ---- ancora: titulo do destino --------------------------------------
    title_len = [len(pages[i]["title"]) for i in ids]
    title_len.sort()
    anchors_ok = sum(1 for x in title_len if 20 <= x <= 65)

    report = {
        "universo": {
            "paginas_ativas": n, "tombstones": tombstones,
            "referencias_topico": sum(len(pages[i]["topics"]) for i in ids),
            "dialeto": dict(dialect),
            "paginas_sem_rota_valida": len(no_route),
            "amostra_sem_rota": no_route[:5],
        },
        "buckets": dict(buckets),
        "semantico_por_familia": dict(semantic_family),
        "malha_A_B": metrics(build_mesh(3, False, False)),
        "malha_A_B_C_familia": metrics(build_mesh(3, True, True)),
        "malha_A_B_C_tudo": metrics(build_mesh(3, True, False)),
        "malha_A_B_C_familia_cap4": metrics(build_mesh(4, True, True)),
        "ancora": {
            "title_min": title_len[0], "title_p50": title_len[n // 2],
            "title_max": title_len[-1], "title_entre_20_65": anchors_ok,
            "title_fora_faixa": n - anchors_ok,
        },
        "amostras": {k: v[:12] for k, v in fail_samples.items()},
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
