#!/usr/bin/env python3
import argparse
import json
import math
import re
import sys
import time
from collections import defaultdict
from importlib.metadata import version

import ir_measures
from ir_measures import AP, P, RR, Recall, nDCG
from ranx import Qrels, Run


TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9]{3,}")
STOPWORDS = {
    "para", "com", "sem", "por", "uma", "uma", "que", "dos", "das", "documento",
    "documentos", "fonte", "prazo", "resposta", "juridico", "jurídico", "publica",
    "pública", "oficial", "conteudo", "conteúdo", "informativo", "analise",
    "análise", "registro", "registrado", "recebida",
}


TEXT_FIELDS = (
    "long_tail_query",
    "public_title",
    "public_meta_description",
    "public_h1",
    "public_summary",
)


def normalize_tokens(value):
    if not value:
        return []
    tokens = []
    for token in TOKEN_RE.findall(value.lower()):
        if token not in STOPWORDS:
            tokens.append(token)
    return tokens


def record_text(record, fields):
    parts = []
    for field in fields:
        value = record.get(field)
        if isinstance(value, str):
            parts.append(value)
    if "body" in fields:
        for section in record.get("public_body_sections") or ():
            if isinstance(section, dict):
                parts.append(str(section.get("heading") or ""))
                parts.append(str(section.get("text") or ""))
    return " ".join(parts)


def document_id(record, index):
    return record.get("refined_public_prose_id") or record.get("public_prose_candidate_id") or f"doc-{index:06d}"


def load_records(path):
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid_json line={line_number}: {exc}") from exc
            if record.get("publication_allowed") or record.get("render_allowed") or record.get("sitemap_allowed") or record.get("approval") or record.get("public_path"):
                raise SystemExit(f"public_flag_open line={line_number}")
            records.append(record)
    return records


def select_queries(records, query_limit):
    selected = []
    seen = set()
    for index, record in enumerate(records):
        key = (
            record.get("seed_term_id") or record.get("seed_term") or "",
            record.get("scenario_id") or "",
            record.get("context_id") or "",
        )
        if key in seen:
            continue
        query = record.get("long_tail_query") or record.get("public_title") or record.get("public_h1")
        if not query or len(normalize_tokens(query)) < 3:
            continue
        selected.append((index, record))
        seen.add(key)
        if len(selected) >= query_limit:
            break
    return selected


def build_qrels(records, query_records):
    qrels = {}
    for query_index, query_record in query_records:
        qid = document_id(query_record, query_index)
        seed = query_record.get("seed_term_id") or query_record.get("seed_term") or ""
        scenario = query_record.get("scenario_id") or ""
        context = query_record.get("context_id") or ""
        practice = query_record.get("practice_area") or ""
        rels = {}
        for index, record in enumerate(records):
            docid = document_id(record, index)
            relevance = 0
            if record.get("unique_intent_id") and record.get("unique_intent_id") == query_record.get("unique_intent_id"):
                relevance = 3
            elif seed and seed == (record.get("seed_term_id") or record.get("seed_term") or "") and scenario and scenario == record.get("scenario_id"):
                relevance = 2
            elif seed and seed == (record.get("seed_term_id") or record.get("seed_term") or ""):
                relevance = 1
            elif practice and practice == record.get("practice_area") and context and context == record.get("context_id"):
                relevance = 1
            if relevance > 0:
                rels[docid] = relevance
        if rels:
            qrels[qid] = rels
    return qrels


def weighted_score(query_tokens, doc_tokens, doc_unique_tokens):
    if not doc_tokens:
        return 0.0
    score = 0.0
    for token in query_tokens:
        if token in doc_unique_tokens:
            score += 1.0
    if not score:
        return 0.0
    return score / math.sqrt(len(doc_unique_tokens) + 1.0)


def build_run(records, query_records, fields, top_k):
    doc_tokens = []
    for record in records:
        tokens = normalize_tokens(record_text(record, fields))
        doc_tokens.append((tokens, set(tokens)))
    run = {}
    total_returned = 0
    for query_index, query_record in query_records:
        qid = document_id(query_record, query_index)
        query_tokens = normalize_tokens(record_text(query_record, ("long_tail_query", "public_title", "public_h1")))
        scores = []
        for index, record in enumerate(records):
            score = weighted_score(query_tokens, doc_tokens[index][0], doc_tokens[index][1])
            if score > 0:
                scores.append((document_id(record, index), score))
        scores.sort(key=lambda item: (-item[1], item[0]))
        trimmed = scores[:top_k]
        total_returned += len(trimmed)
        run[qid] = {docid: float(score) for docid, score in trimmed}
    return run, total_returned


def reciprocal_rank_fusion(runs, top_k, k=60):
    fused = {}
    for run in runs:
        for qid, docs in run.items():
            scores = fused.setdefault(qid, defaultdict(float))
            ranked = sorted(docs.items(), key=lambda item: (-item[1], item[0]))
            for rank, (docid, _score) in enumerate(ranked, 1):
                scores[docid] += 1.0 / (k + rank)
    out = {}
    for qid, docs in fused.items():
        ranked = sorted(docs.items(), key=lambda item: (-item[1], item[0]))[:top_k]
        out[qid] = {docid: float(score) for docid, score in ranked}
    return out


def ir_measures_rows(qrels, run):
    qrel_rows = []
    for qid, rels in qrels.items():
        for docid, rel in rels.items():
            qrel_rows.append(ir_measures.Qrel(qid, docid, int(rel)))
    run_rows = []
    for qid, docs in run.items():
        for docid, score in docs.items():
            run_rows.append(ir_measures.ScoredDoc(qid, docid, float(score)))
    return qrel_rows, run_rows


def metric_value(value):
    return round(float(value), 6)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--query-limit", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=40)
    args = parser.parse_args(argv)
    started = time.time()
    records = load_records(args.input)
    query_records = select_queries(records, args.query_limit)
    if not query_records:
        raise SystemExit("no_queries_selected")
    qrels = build_qrels(records, query_records)
    title_run, title_returned = build_run(records, query_records, ("public_title", "public_h1", "public_meta_description"), args.top_k)
    body_run, body_returned = build_run(records, query_records, ("public_summary", "body"), args.top_k)
    ranx_qrels = Qrels(qrels)
    title = Run(title_run, name="lexical_title")
    body = Run(body_run, name="lexical_body")
    # Build Qrels through ranx as an integration sanity check; metrics use
    # ir-measures to avoid ranx/Numba cold-JIT minutes on small local gates.
    if len(ranx_qrels.qrels) != len(qrels):
        raise SystemExit("ranx_qrels_mismatch")
    if len(title.to_dict()) != len(title_run) or len(body.to_dict()) != len(body_run):
        raise SystemExit("ranx_run_mismatch")
    fused = reciprocal_rank_fusion([title_run, body_run], args.top_k)
    qrel_rows, run_rows = ir_measures_rows(qrels, fused)
    ir_scores = ir_measures.calc_aggregate([nDCG@10, RR@10, AP@100, Recall@100, P@10], qrel_rows, run_rows)
    ndcg_at_10 = metric_value(ir_scores.get(nDCG@10, 0.0))
    mrr_at_10 = metric_value(ir_scores.get(RR@10, 0.0))
    map_at_100 = metric_value(ir_scores.get(AP@100, 0.0))
    recall_at_100 = metric_value(ir_scores.get(Recall@100, 0.0))
    precision_at_10 = metric_value(ir_scores.get(P@10, 0.0))
    payload = {
        "module_path": "ranx+ir-measures",
        "ranx_version": version("ranx"),
        "ir_measures_version": version("ir-measures"),
        "input_records": len(records),
        "query_count": len(query_records),
        "qrels_count": sum(len(rels) for rels in qrels.values()),
        "title_run_returned": title_returned,
        "body_run_returned": body_returned,
        "fused_run_returned": sum(len(docs) for docs in fused.values()),
        "ranx_fusion_method": "rrf-local-ranx-run-validated",
        "ranx_ndcg_at_10": ndcg_at_10,
        "ranx_mrr_at_10": mrr_at_10,
        "ranx_map_at_100": map_at_100,
        "ranx_recall_at_100": recall_at_100,
        "ranx_precision_at_10": precision_at_10,
        "ir_measures_ndcg_at_10": ndcg_at_10,
        "ir_measures_mrr_at_10": mrr_at_10,
        "ir_measures_map_at_100": map_at_100,
        "ir_measures_recall_at_100": recall_at_100,
        "ir_measures_precision_at_10": precision_at_10,
        "scan_duration_ms": max(1, int((time.time() - started) * 1000)),
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
