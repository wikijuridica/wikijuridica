#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mede a resolucao de internal_link_topics -> pagina no estoque v2.

Read-only. Replica a normalizacao de internal/v2internallinkgraph/tokens.go
(slugFold + contentTokens) para medir, estrategia por estrategia, quantos
topicos casam com uma pagina real do acervo.
"""
import glob
import json
import math
import os
import sys
import unicodedata
from collections import Counter, defaultdict

ROOT = "/opt/wiki"

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos",
    "nas", "para", "por", "com", "que", "um", "uma", "uns", "umas", "as",
    "os", "ao", "aos", "se", "ou", "como", "sobre",
}


def _fold(text):
    out = []
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.combining(ch):
            continue
        ch = ch.lower()
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
        else:
            out.append("\x00")
    return "".join(out)


def slug_fold(*parts):
    pieces = []
    for part in parts:
        if not part:
            continue
        pieces.append(_fold(part))
    raw = "\x00".join(pieces)
    tokens = [t for t in raw.split("\x00") if t]
    return "-".join(tokens)


def content_tokens(*parts):
    tokens = []
    for part in parts:
        if not part:
            continue
        for tok in _fold(part).split("\x00"):
            if len(tok) < 2 or tok in STOPWORDS:
                continue
            tokens.append(tok)
    return tokens


def seed_term(intent_id):
    sep = intent_id.find("-")
    if sep <= 0 or sep == len(intent_id) - 1:
        return ""
    return intent_id[sep + 1:]


def load_portfolio():
    portfolio = {}
    dupes = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "data/editorial/portfolio_v2/*.jsonl"))):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                iid = rec.get("intent_id", "")
                if not iid:
                    continue
                if iid in portfolio:
                    dupes += 1
                    continue
                portfolio[iid] = rec
    return portfolio, dupes


def load_pages(portfolio):
    pages = {}
    tombstones = 0
    orphan_join = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "data/editorial/v2_pages/*.jsonl"))):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                iid = rec.get("intent_id", "")
                if not iid:
                    continue
                if rec.get("skipped"):
                    tombstones += 1
                    continue
                if iid in pages:
                    continue
                meta = portfolio.get(iid)
                if meta is None:
                    orphan_join += 1
                    continue
                pages[iid] = {
                    "intent_id": iid,
                    "title": rec.get("title", ""),
                    "h1": rec.get("h1", ""),
                    "topics": rec.get("internal_link_topics") or [],
                    "area": meta.get("practice_area", ""),
                    "family": meta.get("family", ""),
                    "ltq": meta.get("long_tail_query", ""),
                    "wt": meta.get("working_title", ""),
                    "rp": meta.get("reader_problem", ""),
                    "shard": os.path.basename(path),
                }
    return pages, tombstones, orphan_join


def main():
    portfolio, port_dupes = load_portfolio()
    pages, tombstones, orphan_join = load_pages(portfolio)
    ids = sorted(pages)
    idx = {iid: i for i, iid in enumerate(ids)}
    n = len(ids)

    # --- indices de identidade exata -------------------------------------
    by_intent = defaultdict(list)      # slugFold(intent_id)
    by_seed = defaultdict(list)        # slugFold(seedTerm(intent_id))
    by_descriptor = defaultdict(list)  # slugFold(title|h1|ltq|wt|rp)
    for iid in ids:
        page = pages[iid]
        i = idx[iid]
        s = slug_fold(iid)
        if s:
            by_intent[s].append(i)
        s = slug_fold(seed_term(iid))
        if s:
            by_seed[s].append(i)
        for descriptor in (page["title"], page["h1"], page["ltq"], page["wt"], page["rp"]):
            s = slug_fold(descriptor)
            if s:
                by_descriptor[s].append(i)

    # --- universo de topicos ---------------------------------------------
    topic_refs = []       # (from_idx, topic)
    for iid in ids:
        for topic in pages[iid]["topics"]:
            topic_refs.append((idx[iid], topic))
    distinct_topics = sorted({t for _, t in topic_refs})
    topic_usage = Counter(t for _, t in topic_refs)

    # --- TF-IDF (replica do tier 2 do resolver Go) ------------------------
    node_tokens = []
    df = Counter()
    postings = defaultdict(list)
    for iid in ids:
        page = pages[iid]
        bag = set(content_tokens(seed_term(iid), page["title"], page["h1"],
                                 page["ltq"], page["family"], page["wt"], page["rp"]))
        node_tokens.append(bag)
        for tok in bag:
            df[tok] += 1
            postings[tok].append(idx[iid])
    max_df = max(2, math.ceil(n * 0.20))
    idf = {}
    for tok, count in df.items():
        if count > max_df:
            continue
        idf[tok] = math.log(1.0 + n / count)
    areas = [pages[iid]["area"] for iid in ids]

    def semantic(topic, from_area):
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
                if from_area and areas[node] != from_area:
                    continue
                acc[node] += w
                matched[node] += 1
        if weight <= 0 or not acc:
            return None, 0.0
        best, best_score, second = -1, 0.0, 0.0
        for node, value in acc.items():
            if matched[node] < 2:
                continue
            coverage = value / weight
            if coverage > best_score or (coverage == best_score and (best == -1 and True)):
                second = best_score
                best_score = coverage
                best = node
            elif coverage > second:
                second = coverage
        if best == -1 or best_score < 0.50:
            return None, best_score
        if best_score - second < 0.05:
            return None, best_score
        return best, best_score

    # --- estrategias por REFERENCIA (from, topic) -------------------------
    stats = Counter()
    edges_exact_area = set()
    edges_exact_global = set()
    unresolved_exact = []
    cross_area_only = []
    semantic_only = []
    ambiguous = []
    self_ref = 0
    semantic_cache = {}

    for from_idx, topic in topic_refs:
        area = areas[from_idx]
        key = slug_fold(topic)
        cand_intent = by_intent.get(key, [])
        cand_seed = by_seed.get(key, [])
        cand_desc = by_descriptor.get(key, [])
        cand_all = list(dict.fromkeys(cand_intent + cand_seed + cand_desc))
        if cand_intent:
            stats["hit_intent_id"] += 1
        if cand_seed:
            stats["hit_seed_term"] += 1
        if cand_desc:
            stats["hit_descriptor"] += 1
        if cand_all:
            stats["hit_exact_any_global"] += 1
        same_area = [c for c in cand_all if areas[c] == area]
        if same_area:
            stats["hit_exact_any_same_area"] += 1
            if len(same_area) > 1:
                stats["exact_ambiguous_same_area"] += 1
                ambiguous.append((topic, len(same_area)))
            target = same_area[0]
            if target == from_idx:
                self_ref += 1
            else:
                edges_exact_area.add((from_idx, target))
                edges_exact_global.add((from_idx, target))
        elif cand_all:
            stats["hit_exact_cross_area_only"] += 1
            cross_area_only.append((ids[from_idx], topic, ids[cand_all[0]]))
            if cand_all[0] != from_idx:
                edges_exact_global.add((from_idx, cand_all[0]))
        else:
            cache_key = (topic, area)
            if cache_key not in semantic_cache:
                semantic_cache[cache_key] = semantic(topic, area)
            node, score = semantic_cache[cache_key]
            if node is not None:
                stats["hit_semantic_same_area_only"] += 1
                semantic_only.append((ids[from_idx], topic, ids[node], round(score, 3)))
            else:
                stats["unresolved_any"] += 1
                unresolved_exact.append((ids[from_idx], topic, round(score, 3)))

    # --- metricas de grafo sobre a malha EXATA (mesma area) --------------
    def graph_metrics(edge_set):
        out_deg = Counter()
        in_deg = Counter()
        for a, b in edge_set:
            out_deg[a] += 1
            in_deg[b] += 1
        reciprocal = sum(1 for a, b in edge_set if (b, a) in edge_set)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edge_set:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        comps = Counter(find(i) for i in range(n))
        sizes = sorted(comps.values(), reverse=True)
        return {
            "edges": len(edge_set),
            "avg_out": round(len(edge_set) / n, 3),
            "pages_with_out": len(out_deg),
            "pages_zero_in": n - len(in_deg),
            "reciprocal_edges": reciprocal,
            "reciprocity": round(reciprocal / max(len(edge_set), 1), 3),
            "components": len(sizes),
            "largest_component": sizes[0] if sizes else 0,
            "singletons": sum(1 for s in sizes if s == 1),
            "in_deg_p50": sorted(in_deg.values())[len(in_deg) // 2] if in_deg else 0,
            "in_deg_max": max(in_deg.values()) if in_deg else 0,
        }

    report = {
        "stock": {
            "portfolio_records": len(portfolio),
            "portfolio_dupes_ignored": port_dupes,
            "active_pages": n,
            "tombstones": tombstones,
            "pages_without_portfolio_join": orphan_join,
            "topic_refs": len(topic_refs),
            "distinct_topics": len(distinct_topics),
            "topic_reuse_p50": sorted(topic_usage.values())[len(topic_usage) // 2],
            "topic_reuse_max": topic_usage.most_common(1)[0] if topic_usage else None,
            "topics_used_once": sum(1 for v in topic_usage.values() if v == 1),
        },
        "strategies_by_reference": dict(stats),
        "self_reference_topics": self_ref,
        "graph_exact_same_area": graph_metrics(edges_exact_area),
        "graph_exact_global": graph_metrics(edges_exact_global),
        "samples": {
            "unresolved": unresolved_exact[:40],
            "cross_area_only": cross_area_only[:15],
            "semantic_only": semantic_only[:15],
            "ambiguous_exact": ambiguous[:10],
            "top_reused_topics": topic_usage.most_common(10),
        },
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
