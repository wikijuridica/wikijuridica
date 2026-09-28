#!/usr/bin/env python3
"""
Extracao para red-team pre-promote (seed 20260722B).
Read-only: le v2_ingest_report.jsonl (status=accepted) + shards data/editorial/v2_pages/*.jsonl.
Nao gera, nao edita, nao publica conteudo -- apenas amostra e imprime para revisao adversarial externa.
"""
import json
import random
import re
import sys

REPO = "/sessions/zen-adoring-cerf/mnt/wiki"
INGEST_REPORT = f"{REPO}/data/ops/v2_ingest_report.jsonl"
SEED = "20260722B"
N_TOTAL = 14
N_COMERCIAL = 10
N_INFORMATIVA = 4

PAID_SIGNAL_RE = re.compile(r"advogad|contrata|particular|honorári", re.IGNORECASE)


def load_accepted():
    rows = []
    with open(INGEST_REPORT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("status") == "accepted":
                rows.append(d)
    return rows


def build_pools(rows):
    pools = {}
    for r in rows:
        area = r["practice_area"]
        lane = r["lane"]
        pools.setdefault(area, {}).setdefault(lane, []).append(r)
    return pools


def sample_selection(pools):
    rng_log = []
    random.seed(SEED)

    comercial_areas_pool = sorted(a for a, lanes in pools.items() if lanes.get("comercial"))
    random.shuffle(comercial_areas_pool)
    chosen_comercial_areas = comercial_areas_pool[:N_COMERCIAL]
    rng_log.append(f"comercial_areas_pool(sorted)={comercial_areas_pool}")
    rng_log.append(f"chosen_comercial_areas={chosen_comercial_areas}")

    informativa_areas_pool = sorted(
        a for a, lanes in pools.items()
        if lanes.get("informativa") and a not in chosen_comercial_areas
    )
    random.shuffle(informativa_areas_pool)
    chosen_informativa_areas = informativa_areas_pool[:N_INFORMATIVA]
    rng_log.append(f"informativa_areas_pool(sorted, excl. comerciais)={informativa_areas_pool}")
    rng_log.append(f"chosen_informativa_areas={chosen_informativa_areas}")

    chosen = [(a, "comercial") for a in chosen_comercial_areas] + [(a, "informativa") for a in chosen_informativa_areas]
    if len(chosen) < N_TOTAL:
        remaining_pool = sorted(a for a in pools if a not in [c[0] for c in chosen])
        random.shuffle(remaining_pool)
        need = N_TOTAL - len(chosen)
        for a in remaining_pool[:need]:
            lane = "comercial" if pools[a].get("comercial") else "informativa"
            chosen.append((a, lane))
        rng_log.append(f"fallback_fill(faltou completar 14 distintas)={remaining_pool[:need]}")

    selected_rows = []
    for area, lane in chosen:
        candidates = sorted(pools[area][lane], key=lambda r: r["intent_id"])
        row = random.choice(candidates)
        selected_rows.append(row)
        rng_log.append(f"area={area} lane={lane} n_candidates={len(candidates)} -> intent_id={row['intent_id']}")

    return selected_rows, rng_log


def read_shard_record(source_shard, source_line, expected_intent_id):
    path = f"{REPO}/{source_shard}" if not source_shard.startswith(REPO) else source_shard
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            if i == source_line:
                rec = json.loads(line)
                if rec.get("intent_id") != expected_intent_id:
                    raise RuntimeError(
                        f"MISMATCH shard={source_shard} line={source_line} "
                        f"esperado={expected_intent_id} encontrado={rec.get('intent_id')}"
                    )
                return rec
    raise RuntimeError(f"linha {source_line} nao encontrada em {source_shard}")


def corpo_text(rec):
    parts = [rec.get("opening", "") or ""]
    for s in rec.get("sections", []) or []:
        parts.append(s.get("text", "") or "")
    return "\n\n".join(parts)


def mechanical_checks(rec, lane):
    title = rec.get("title", "") or ""
    meta = rec.get("meta_description", "") or ""
    title_len = len(title)
    meta_len = len(meta)
    title_ok = 20 <= title_len <= 65
    meta_ok = 70 <= meta_len <= 160
    if lane == "comercial":
        paid_ok = bool(PAID_SIGNAL_RE.search(corpo_text(rec)))
    else:
        paid_ok = None
    return title_len, title_ok, meta_len, meta_ok, paid_ok


def format_page(ingest_row, rec, idx):
    lane = rec.get("lane", ingest_row.get("lane"))
    page_type = rec.get("page_type") or ingest_row.get("page_type")
    practice_area = rec.get("practice_area") or ingest_row.get("practice_area")
    intent_id = rec["intent_id"]
    word_count = rec.get("word_count", ingest_row.get("word_count"))

    lines = []
    lines.append("=" * 90)
    lines.append(f"[{idx}/14] INTENT: {intent_id}")
    lines.append(
        f"LANE: {lane} | PAGE_TYPE: {page_type} | PRACTICE_AREA: {practice_area} | WORD_COUNT: {word_count}"
    )
    lines.append(
        f"source_shard: {ingest_row.get('source_shard')}  source_line: {ingest_row.get('source_line')}  "
        f"draft_id: {ingest_row.get('draft_id')}"
    )
    lines.append(f"public_path (pretendido, publication_allowed={rec.get('publication_allowed')}): {rec.get('public_path') or ingest_row.get('public_path')}")
    lines.append("-" * 90)
    lines.append(f"TITLE ({len(rec.get('title') or '')} chars): {rec.get('title')}")
    lines.append(f"META  ({len(rec.get('meta_description') or '')} chars): {rec.get('meta_description')}")
    lines.append(f"H1: {rec.get('h1')}")
    lines.append("-" * 90)
    lines.append("FONTES OFICIAIS:")
    sources = rec.get("official_sources") or []
    if not sources:
        lines.append("  (nenhuma fonte oficial registrada no shard)")
    for s in sources:
        lines.append(f"  - {s.get('name')} - {s.get('url')}")
        lines.append(f"    anchor_claim: {s.get('anchor_claim')}")
        lines.append(f"    verified_at: {s.get('verified_at')}  http_status: {s.get('http_status')}")
    lines.append("-" * 90)
    lines.append("OPENING:")
    lines.append(rec.get("opening") or "(vazio)")
    lines.append("")
    for s in rec.get("sections") or []:
        lines.append(f"## {s.get('heading')}")
        lines.append(s.get("text") or "(vazio)")
        lines.append("")
    faq = rec.get("faq") or []
    lines.append("FAQ:")
    if not faq:
        lines.append("  (vazio - sem FAQ nesta pagina)")
    else:
        for qa in faq:
            if isinstance(qa, dict):
                lines.append(f"  Q: {qa.get('question') or qa.get('q')}")
                lines.append(f"  A: {qa.get('answer') or qa.get('a')}")
            else:
                lines.append(f"  - {qa}")
    lines.append("-" * 90)
    cta_val = rec.get("cta")
    lines.append(f"CTA: {cta_val if cta_val is not None else 'ausente - schema v2_pages nao tem campo cta (CTA e renderizado via content/cta_policy.json na publicacao, nao armazenado no JSONL editorial)'}")
    lines.append("=" * 90)
    lines.append("")
    return "\n".join(lines)


def main():
    rows = load_accepted()
    pools = build_pools(rows)
    selected_rows, rng_log = sample_selection(pools)

    dump_parts = []
    dump_parts.append("EXTRACAO RED-TEAM PRE-PROMOTE - seed 20260722B")
    dump_parts.append(f"Fonte: data/ops/v2_ingest_report.jsonl (status=accepted, {len(rows)} linhas elegiveis, {len(pools)} practice_areas distintas)")
    dump_parts.append("Metodologia de amostragem (deterministica, reproduzivel):")
    dump_parts.append("  1. random.seed('20260722B')")
    dump_parts.append("  2. pool de areas com >=1 pagina comercial aceita -> sorted() -> random.shuffle() -> primeiras 10")
    dump_parts.append("  3. pool de areas com >=1 pagina informativa aceita, excluindo as 10 ja escolhidas -> sorted() -> random.shuffle() -> primeiras 4")
    dump_parts.append("  4. em cada area escolhida, candidatos da lane alvo ordenados por intent_id -> random.choice() define a pagina")
    dump_parts.append("Log do sorteio:")
    for l in rng_log:
        dump_parts.append(f"  - {l}")
    dump_parts.append("")

    table_rows = []
    for idx, ingest_row in enumerate(selected_rows, start=1):
        rec = read_shard_record(ingest_row["source_shard"], ingest_row["source_line"], ingest_row["intent_id"])
        dump_parts.append(format_page(ingest_row, rec, idx))

        lane = rec.get("lane", ingest_row.get("lane"))
        title_len, title_ok, meta_len, meta_ok, paid_ok = mechanical_checks(rec, lane)
        table_rows.append({
            "intent_id": rec["intent_id"],
            "lane": lane,
            "practice_area": rec.get("practice_area") or ingest_row.get("practice_area"),
            "title_len": title_len,
            "title_ok": title_ok,
            "meta_len": meta_len,
            "meta_ok": meta_ok,
            "paid_ok": paid_ok,
        })

    full_dump = "\n".join(dump_parts)

    table_lines = []
    table_lines.append("| # | intent_id | practice_area | lane | title_ok (len) | meta_ok (len) | paid_signal_ok |")
    table_lines.append("|---|-----------|----------------|------|-----------------|-----------------|----------------|")
    for i, r in enumerate(table_rows, start=1):
        paid_str = "n/a (lane informativa)" if r["paid_ok"] is None else ("TRUE" if r["paid_ok"] else "FALSE")
        table_lines.append(
            f"| {i} | {r['intent_id']} | {r['practice_area']} | {r['lane']} | "
            f"{'TRUE' if r['title_ok'] else 'FALSE'} ({r['title_len']}) | "
            f"{'TRUE' if r['meta_ok'] else 'FALSE'} ({r['meta_len']}) | {paid_str} |"
        )
    table_str = "\n".join(table_lines)

    with open(f"{REPO}/data/ops/cowork_redteam_sample_20260722B.txt", "w", encoding="utf-8") as fh:
        fh.write(full_dump)
        fh.write("\n\nTABELA DE CHECAGEM MECANICA\n")
        fh.write(table_str)
        fh.write("\n")

    print("DUMP_SIZE_BYTES", len(full_dump.encode("utf-8")))
    print("N_SELECTED", len(selected_rows))
    print("=== TABELA ===")
    print(table_str)


if __name__ == "__main__":
    main()
