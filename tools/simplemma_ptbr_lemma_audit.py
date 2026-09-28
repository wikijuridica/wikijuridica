#!/usr/bin/env python3
import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import simplemma


TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+")


def main() -> int:
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--checked-at", default="2026-06-26")
    parser.add_argument("--output", default="data/ops/simplemma_ptbr_lemma_audit.jsonl")
    parser.add_argument("--timings", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    source_path = root / "data/editorial/refined_public_prose.jsonl"
    output_path = root / args.output

    records = []
    source_hash = hashlib.sha256()
    with source_path.open("rb") as handle:
        for line in handle:
            source_hash.update(line)
            if not line.strip():
                continue
            records.append(json.loads(line))

    selected = records[: args.limit if args.limit > 0 else len(records)]
    lemma_counts: Counter[str] = Counter()
    token_count = 0
    records_with_flags = 0
    for record in selected:
        if (
            record.get("approval")
            or record.get("publication_allowed")
            or record.get("render_allowed")
            or record.get("sitemap_allowed")
            or record.get("public_path")
        ):
            records_with_flags += 1
        for token in TOKEN_RE.findall(visible_text(record).lower()):
            if len(token) < 3:
                continue
            lemma = simplemma.lemmatize(token, lang="pt")
            if not lemma:
                continue
            token_count += 1
            lemma_counts[lemma] += 1

    top_lemmas = [
        {"lemma": lemma, "count": count}
        for lemma, count in sorted(lemma_counts.items(), key=lambda item: (-item[1], item[0]))[:30]
    ]
    record = {
        "audit_id": "simplemma-ptbr-lemma-audit-2026-06-26",
        "record_status": "simplemma_ptbr_lemma_audit_blocked_no_publication",
        "checked_at": args.checked_at,
        "tool_name": "simplemma",
        "package_name": "simplemma",
        "package_version": importlib.metadata.version("simplemma"),
        "package_license": "MIT",
        "package_source_url": "https://github.com/adbar/simplemma",
        "package_registry_url": "https://pypi.org/project/simplemma/1.2.0/",
        "integration_mode": "python_offline_ptbr_lemma_oracle_blocked",
        "input_layer": "data/editorial/refined_public_prose.jsonl",
        "input_records": len(records),
        "sampled_records": len(selected),
        "input_fingerprint_sha256": source_hash.hexdigest(),
        "token_count": token_count,
        "unique_lemma_count": len(lemma_counts),
        "top_lemmas": top_lemmas,
        "public_flags_open_records": records_with_flags,
        "use_policy": "blocked_ptbr_lemma_quality_oracle_no_publication_no_public_write",
        "publication_allowed": False,
        "render_allowed": False,
        "sitemap_allowed": False,
        "public_path": "",
        "approval": False,
        "index_policy": "noindex",
    }
    fingerprint_payload = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    record["record_fingerprint_sha256"] = hashlib.sha256(fingerprint_payload).hexdigest()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
    temp_path.replace(output_path)
    print(
        f"simplemma-ptbr-lemma-audit: records={len(records)} sampled={len(selected)} "
        f"tokens={token_count} unique_lemmas={len(lemma_counts)} publication=false"
    )
    if args.timings:
        duration_ms = int((time.monotonic() - started) * 1000)
        print(
            f"TIMING check=simplemma-ptbr-lemma-audit status=pass duration_ms={duration_ms} "
            f"records={len(records)} sampled={len(selected)} tokens={token_count} publication=false",
            file=sys.stderr,
        )
    return 0


def visible_text(record: dict) -> str:
    values = [
        record.get("public_title", ""),
        record.get("public_meta_description", ""),
        record.get("public_h1", ""),
        record.get("public_summary", ""),
        record.get("public_legal_notice", ""),
    ]
    for section in record.get("public_body_sections") or []:
        values.append(section.get("heading", ""))
        values.append(section.get("text", ""))
    return "\n".join(value for value in values if value)


if __name__ == "__main__":
    raise SystemExit(main())
