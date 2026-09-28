#!/usr/bin/env python3
"""Materializa os staging wave3 em shards canônicos, com CAS e epoch EX.

Deduplica contra o portfolio existente e entre os candidatos, valida o schema
e grava ``portfolio_v2/<area>-w3.jsonl``. O modo padrão é somente diagnóstico;
``--write`` publica apenas no estoque editorial interno (nunca no produto).
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import stat
import sys
import tempfile
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease


DEFAULT_STAGE_DIR = Path(
    "/tmp/claude-1000/-opt-wiki/79e60698-529c-45d5-b928-6a04e37a70ac/scratchpad"
)
REQ = [
    "intent_id", "page_type", "practice_area", "family", "long_tail_query",
    "working_title", "reader_problem", "lane", "source_hints",
    "needs_source_research", "distinct_because",
]
PAGE_TYPES = {"guia_problema", "pergunta", "verbete", "procedimento"}


def norm(value):
    value = unicodedata.normalize("NFKD", (value or "").lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9 ]", " ", value)


def toks(value):
    return set(norm(value).split())


def jacc(left, right):
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _read_jsonl_lenient(path):
    rows = []
    with path.open(encoding="utf-8") as source:
        for line in source:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                rows.append(record)
    return rows


def _atomic_replace_cas(path, before, payload):
    """Replace durável; ``before=None`` significa criação CAS."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if before is None:
        if os.path.lexists(path):
            raise RuntimeError(f"CAS de criação falhou; alvo surgiu: {path}")
        mode = 0o644
    else:
        info = os.lstat(path)
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or
                info.st_nlink != 1 or path.read_bytes() != before):
            raise RuntimeError(f"CAS de substituição falhou: {path}")
        mode = stat.S_IMODE(info.st_mode)
    fd, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as target:
            target.write(payload)
            target.flush()
            os.fsync(target.fileno())
        if before is None:
            if os.path.lexists(path):
                raise RuntimeError(f"CAS de criação falhou antes do rename: {path}")
        elif path.read_bytes() != before:
            raise RuntimeError(f"CAS mudou antes do rename: {path}")
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _materialize(canonical_root, stage_dir, write):
    portfolio_dir = canonical_root / "data/editorial/portfolio_v2"

    existing_ids = set()
    existing_queries = []
    for raw_path in sorted(glob.glob(os.fspath(portfolio_dir / "*.jsonl"))):
        for record in _read_jsonl_lenient(Path(raw_path)):
            intent = record.get("intent_id")
            if intent:
                existing_ids.add(intent)
            query = record.get("long_tail_query")
            if query:
                existing_queries.append(
                    (toks(query), record.get("practice_area", "")))

    staged = []
    for raw_path in sorted(glob.glob(os.fspath(stage_dir / "wave3_stage_*.jsonl"))):
        for record in _read_jsonl_lenient(Path(raw_path)):
            record["_src"] = os.path.basename(raw_path)
            staged.append(record)

    kept = []
    rejected = collections.Counter()
    seen_ids = set()
    kept_queries = []
    for record in staged:
        missing = [key for key in REQ if key not in record]
        if missing:
            rejected["schema_incompleto"] += 1
            continue
        intent = record["intent_id"]
        if record["page_type"] not in PAGE_TYPES:
            rejected["page_type_invalido"] += 1
            continue
        if not isinstance(record["source_hints"], list):
            rejected["source_hints_nao_lista"] += 1
            continue
        if not str(record.get("distinct_because", "")).strip():
            rejected["sem_distinct_because"] += 1
            continue
        if intent in existing_ids or intent in seen_ids:
            rejected["intent_id_duplicado"] += 1
            continue
        query_tokens = toks(record["long_tail_query"])
        area = record.get("practice_area", "")
        duplicate = any(
            existing_area == area and jacc(query_tokens, existing_tokens) >= 0.82
            for existing_tokens, existing_area in existing_queries
        ) or any(
            jacc(query_tokens, kept_tokens) >= 0.82
            for kept_tokens in kept_queries
        )
        if duplicate:
            rejected["long_tail_near_dup"] += 1
            continue
        seen_ids.add(intent)
        kept_queries.append(query_tokens)
        record.pop("_src", None)
        kept.append(record)

    by_area = collections.defaultdict(list)
    for record in kept:
        by_area[record.get("practice_area", "misc")].append(record)

    written = 0
    if write:
        portfolio_dir.mkdir(parents=True, exist_ok=True)
        for area in sorted(by_area):
            path = portfolio_dir / f"{area}-w3.jsonl"
            before = path.read_bytes() if path.exists() else None
            previous = {}
            if before is not None:
                for line in before.decode("utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        previous[json.loads(line)["intent_id"]] = line
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue
            for record in by_area[area]:
                previous[record["intent_id"]] = json.dumps(
                    record, ensure_ascii=False, separators=(",", ":"))
            payload = ("\n".join(previous.values()) + "\n").encode("utf-8")
            if payload != before:
                _atomic_replace_cas(path, before, payload)
            written += len(by_area[area])

    print(
        f"staged={len(staged)} kept={len(kept)} "
        f"written={'sim ' + str(written) if write else 'DRY-RUN'}"
    )
    print("rejeitados:", dict(rejected))
    print(
        "por area (kept):",
        {area: len(items) for area, items in sorted(
            by_area.items(), key=lambda item: -len(item[1]))},
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("stage_dir", nargs="?", type=Path, default=DEFAULT_STAGE_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    canonical_root = ROOT
    try:
        # Dedup lê o estoque inteiro; portanto a leitura e a eventual
        # materialização pertencem ao mesmo epoch EX, sem janela TOCTOU.
        with canonical_stock_write_lease(canonical_root):
            _materialize(canonical_root, args.stage_dir, args.write)
    except StockEpochBusy as error:
        print(f"wave3-materialize: canonical stock busy: {error}", file=sys.stderr)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
