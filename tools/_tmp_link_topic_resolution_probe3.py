#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe 3: desempate do bucket ambiguo, custo em bytes e dimensionamento."""
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
    gloss_nodes = {i for i in range(n) if areas[i] == "glossario"}

    df = Counter()
    postings = defaultdict(list)
    node_tok_count = [0] * n
    for iid in ids:
        page = pages[iid]
        bag = set(content_tokens(seed_term(iid), page["title"], page["h1"],
                                 page["ltq"], page["family"], page["wt"], page["rp"]))
        node_tok_count[idx[iid]] = len(bag)
        for tok in bag:
            df[tok] += 1
            postings[tok].append(idx[iid])
    max_df = max(2, math.ceil(n * 0.20))
    idf = {t: math.log(1.0 + n / c) for t, c in df.items() if c <= max_df}

    def ranked_candidates(topic, from_area):
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
                if areas[node] != from_area:
                    continue
                acc[node] += w
                matched[node] += 1
        if weight <= 0:
            return []
        out = [(v / weight, k) for k, v in acc.items() if matched[k] >= 2]
        out.sort(key=lambda p: (-p[0], node_tok_count[p[1]], p[1]))
        return out

    amb_tie_sizes = Counter()
    amb_family_unique = 0
    amb_family_none = 0
    amb_family_multi = 0
    tierD = []
    samples = []
    cache = {}
    bucket = Counter()

    for iid in ids:
        src = idx[iid]
        area = areas[src]
        for topic in pages[iid]["topics"]:
            key = slug_fold(topic)
            exact = [c for c in dict.fromkeys(by_key.get(key, []) + by_desc.get(key, [])) if c != src]
            if [c for c in exact if areas[c] == area] or [c for c in exact if c in gloss_nodes] or exact:
                continue
            ck = (topic, area)
            if ck not in cache:
                cache[ck] = ranked_candidates(topic, area)
            ranked = cache[ck]
            if not ranked:
                continue
            best_score = ranked[0][0]
            if best_score < 0.50:
                continue
            tied = [node for score, node in ranked if best_score - score < 0.05]
            if len(tied) <= 1:
                continue  # ja resolvido no tier C
            bucket["ambiguo_total"] += 1
            amb_tie_sizes[min(len(tied), 6)] += 1
            same_fam = [node for node in tied if families[src] and families[node] == families[src]]
            if len(same_fam) == 1:
                amb_family_unique += 1
                tierD.append((src, same_fam[0]))
            elif not same_fam:
                amb_family_none += 1
                tierD.append((src, tied[0]))  # desempate: mais especifico, deterministico
            else:
                amb_family_multi += 1
                tierD.append((src, same_fam[0]))
            if len(samples) < 8:
                samples.append({
                    "de": iid, "topico": topic, "empatados": len(tied),
                    "candidatos": [titles[node] for node in tied[:4]],
                    "escolhido": titles[(same_fam or tied)[0]],
                })

    # ---- custo em bytes de uma secao de 3 links --------------------------
    per_link = []
    for src in range(n):
        for dst in (src,):
            pass
    sample_links = []
    for src, dst in tierD[:5000]:
        sample_links.append(len(routes[dst]) + len(titles[dst]) + len('<li><a href=""></a></li>'))
    avg_link = sum(sample_links) / max(len(sample_links), 1)
    wrapper = len('<section aria-labelledby="conteudos-relacionados">\n'
                  '<h2 id="conteudos-relacionados">Conteúdos relacionados</h2>\n<ul></ul>\n</section>\n')
    report = {
        "ambiguidade": {
            "referencias_ambiguas": bucket["ambiguo_total"],
            "tamanho_do_empate": dict(sorted(amb_tie_sizes.items())),
            "familia_resolve_unico": amb_family_unique,
            "familia_nao_ajuda": amb_family_none,
            "familia_ainda_multipla": amb_family_multi,
        },
        "custo_bytes": {
            "bytes_por_link_medio": round(avg_link, 1),
            "bytes_secao_3_links": round(wrapper + 3 * avg_link, 1),
            "wrapper_bytes": wrapper,
            "rota_media": round(sum(len(r) for r in routes) / n, 1),
            "titulo_medio": round(sum(len(t) for t in titles) / n, 1),
        },
        "indice_materializado": {
            "linhas": n,
            "bytes_por_linha_estimado": round(
                sum(len(json.dumps({"intent_id": ids[i], "links": [
                    {"path": routes[i], "anchor": titles[i]}] * 3}, ensure_ascii=False))
                    for i in range(0, n, 50)) / len(range(0, n, 50)), 1),
        },
        "amostras_ambiguidade": samples,
    }
    report["indice_materializado"]["megabytes_9620"] = round(
        report["indice_materializado"]["bytes_por_linha_estimado"] * n / 1048576, 2)
    report["indice_materializado"]["megabytes_500k"] = round(
        report["indice_materializado"]["bytes_por_linha_estimado"] * 500000 / 1048576, 1)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
