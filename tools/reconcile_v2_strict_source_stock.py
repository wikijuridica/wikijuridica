#!/usr/bin/env python3
"""Autentica/reconcilia fontes exatas já materializadas no estoque v2.

O preflight do worker impede novos falsos-verdes, mas shards completos não
voltam à fila. Este gate aplica o mesmo catálogo ao estoque ativo. ``--write``
é deliberadamente conservador: só normaliza name/anchor de URLs que já existem
na página e preserva o par live ``verified_at``/``http_status``. URL ausente
exige pesquisa/proveniência própria e nunca é adicionada por este comando.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import sys
from typing import Any, Iterable, Mapping, NamedTuple

_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))
from tools import generate_v2_review_queue as queue


CATALOG_REL = "data/editorial/v2_source_hint_catalog.json"
PORTFOLIO_DIR_REL = "data/editorial/portfolio_v2"
PAGES_DIR_REL = "data/editorial/v2_pages"
MAX_CATALOG_BYTES = 8 * 1024 * 1024
MAX_PORTFOLIO_BYTES = 64 * 1024 * 1024
MAX_SHARD_BYTES = 64 * 1024 * 1024
_FILE_REL = re.compile(
    r"data/editorial/v2_pages/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl"
)


class Projection(NamedTuple):
    strict_intents: frozenset[str]
    sources_by_intent: Mapping[str, tuple[Mapping[str, str], ...]]


def _canonical_root(root: pathlib.Path | str) -> pathlib.Path:
    raw = os.fspath(root)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ValueError("root inválido")
    absolute = pathlib.Path(os.path.abspath(raw))
    if pathlib.Path(os.path.realpath(absolute)) != absolute or not absolute.is_dir():
        raise ValueError("root deve ser diretório real sem symlink")
    return absolute


def _decode_jsonl(payload: bytes, label: str) -> list[dict[str, Any]]:
    if not payload or not payload.endswith(b"\n"):
        raise ValueError(f"{label}: JSONL vazio ou sem newline terminal")
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(payload[:-1].split(b"\n"), 1):
        if not raw_line:
            raise ValueError(f"{label}:{line_number}: linha vazia")
        row = queue.decode_json_no_duplicate_keys(
            raw_line, f"{label}:{line_number}")
        if not isinstance(row, dict):
            raise ValueError(f"{label}:{line_number}: registro não é objeto")
        rows.append(row)
    return rows


def load_projection(root: pathlib.Path | str) -> Projection:
    canonical_root = _canonical_root(root)
    catalog_snapshot = queue.read_regular_file_snapshot(
        canonical_root / CATALOG_REL, max_bytes=MAX_CATALOG_BYTES)
    catalog = queue.decode_json_no_duplicate_keys(
        catalog_snapshot.payload, "catálogo exato")
    if (not isinstance(catalog, dict) or
            set(catalog) != {"_meta", "strict_intents", "source_hints"}):
        raise ValueError("catálogo exato perdeu schema fechado")
    queue._validate_source_catalog_meta(catalog["_meta"])
    strict_raw = catalog["strict_intents"]
    hints_raw = catalog["source_hints"]
    if (not isinstance(strict_raw, list) or not strict_raw or
            strict_raw != sorted(strict_raw) or
            len(strict_raw) != len(set(strict_raw)) or
            any(not isinstance(intent, str) or
                queue._INTENT_ID.fullmatch(intent) is None
                for intent in strict_raw) or
            not isinstance(hints_raw, dict)):
        raise ValueError("catálogo strict/source_hints inválido")
    exact_hints = {
        hint: queue._canonical_exact_source(source, f"source_hints.{hint}")
        for hint, source in hints_raw.items()
        if isinstance(hint, str) and queue._SOURCE_HINT_ID.fullmatch(hint)
    }
    if len(exact_hints) != len(hints_raw):
        raise ValueError("catálogo contém source_hint não canônico")

    strict = frozenset(strict_raw)
    records: dict[str, Mapping[str, Any]] = {}
    portfolio_dir = canonical_root / PORTFOLIO_DIR_REL
    for path in sorted(portfolio_dir.glob("*.jsonl")):
        snapshot = queue.read_regular_file_snapshot(
            path, max_bytes=MAX_PORTFOLIO_BYTES)
        for line_number, row in enumerate(
                _decode_jsonl(snapshot.payload, path.as_posix()), 1):
            intent_id = row.get("intent_id")
            if intent_id not in strict:
                continue
            if intent_id in records:
                raise ValueError(f"strict intent duplicado no portfolio: {intent_id}")
            source_hints = row.get("source_hints")
            if (not isinstance(source_hints, list) or not source_hints or
                    len(source_hints) != len(set(source_hints)) or
                    any(not isinstance(hint, str) or hint not in exact_hints
                        for hint in source_hints)):
                raise ValueError(
                    f"strict intent sem hints exatos: {intent_id}:{line_number}")
            records[intent_id] = row
    if set(records) != strict:
        missing = sorted(strict - set(records))
        raise ValueError(f"strict intents fora do portfolio: {missing[:8]}")

    by_intent: dict[str, tuple[Mapping[str, str], ...]] = {}
    for intent_id in sorted(strict):
        by_url: dict[str, dict[str, Mapping[str, str]]] = (
            collections.defaultdict(dict))
        for hint in sorted(records[intent_id]["source_hints"]):
            source = exact_hints[hint]
            by_url[source["url"]][hint] = source
        by_intent[intent_id] = tuple(
            queue._canonical_consolidated_source(by_url[url])
            for url in sorted(by_url)
        )
    return Projection(strict, by_intent)


def _stock_source_identity(source: Any, label: str) -> dict[str, str]:
    if not isinstance(source, dict):
        raise ValueError(f"{label}: fonte não é objeto")
    keys = set(source)
    if keys not in (
            {"name", "url", "anchor_claim"},
            {"name", "url", "anchor_claim", "verified_at", "http_status"}):
        raise ValueError(f"{label}: schema de fonte/proveniência inválido")
    return queue._canonical_staged_official_source(
        {field: source.get(field) for field in ("name", "url", "anchor_claim")},
        label,
    )


def check_stock(
    root: pathlib.Path | str,
    files: Iterable[str] | None = None,
) -> dict[str, Any]:
    canonical_root = _canonical_root(root)
    projection = load_projection(canonical_root)
    if files is None:
        paths = sorted((canonical_root / PAGES_DIR_REL).glob("*.jsonl"))
    else:
        rels = list(files)
        if (not rels or any(not isinstance(rel, str) or
                            _FILE_REL.fullmatch(rel) is None for rel in rels) or
                len(rels) != len(set(rels))):
            raise ValueError("files deve conter paths canônicos únicos")
        paths = [canonical_root / rel for rel in rels]

    defects: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    checked_pages = 0
    skipped_pages = 0
    for path in paths:
        snapshot = queue.read_regular_file_snapshot(
            path, max_bytes=MAX_SHARD_BYTES)
        for line_number, row in enumerate(
                _decode_jsonl(snapshot.payload, path.as_posix()), 1):
            intent_id = row.get("intent_id")
            if intent_id not in projection.strict_intents:
                continue
            location = f"{path.relative_to(canonical_root).as_posix()}:{line_number}"
            if intent_id in seen:
                defects.append({
                    "intent_id": intent_id,
                    "kind": "strict_intent_duplicate_stock",
                    "location": location,
                    "first_location": seen[intent_id],
                })
                continue
            seen[intent_id] = location
            if row.get("skipped") is True:
                skipped_pages += 1
                continue
            checked_pages += 1
            sources = row.get("official_sources")
            if not isinstance(sources, list) or not sources:
                defects.append({
                    "intent_id": intent_id,
                    "kind": "official_sources_missing",
                    "location": location,
                })
                continue
            actual: dict[str, Mapping[str, Any]] = {}
            for source_index, source in enumerate(sources, 1):
                try:
                    identity = _stock_source_identity(
                        source, f"{location}:official_sources[{source_index}]")
                except ValueError as error:
                    defects.append({
                        "intent_id": intent_id,
                        "kind": "official_source_invalid",
                        "location": location,
                        "detail": str(error),
                    })
                    continue
                if identity["url"] in actual:
                    defects.append({
                        "intent_id": intent_id,
                        "kind": "official_source_url_duplicate",
                        "location": location,
                        "url": identity["url"],
                    })
                    continue
                actual[identity["url"]] = identity
            for expected in projection.sources_by_intent[intent_id]:
                observed = actual.get(expected["url"])
                if observed is None:
                    defects.append({
                        "intent_id": intent_id,
                        "kind": "exact_source_url_missing",
                        "location": location,
                        "url": expected["url"],
                    })
                elif dict(observed) != dict(expected):
                    defects.append({
                        "intent_id": intent_id,
                        "kind": "exact_source_identity_mismatch",
                        "location": location,
                        "url": expected["url"],
                        "expected": dict(expected),
                        "actual": dict(observed),
                    })
    return {
        "ok": not defects,
        "strict_catalog_intents": len(projection.strict_intents),
        "strict_stock_pages_checked": checked_pages,
        "strict_stock_tombstones": skipped_pages,
        "defects": defects,
    }


def reconcile_file(root: pathlib.Path | str, rel_path: str) -> dict[str, Any]:
    canonical_root = _canonical_root(root)
    if not isinstance(rel_path, str) or _FILE_REL.fullmatch(rel_path) is None:
        raise ValueError("path do shard não é canônico")
    projection = load_projection(canonical_root)
    path = canonical_root / rel_path
    snapshot = queue.read_regular_file_snapshot(path, max_bytes=MAX_SHARD_BYTES)
    rows = _decode_jsonl(snapshot.payload, rel_path)
    changed: list[str] = []
    missing: list[dict[str, str]] = []
    for row in rows:
        intent_id = row.get("intent_id")
        if intent_id not in projection.strict_intents or row.get("skipped") is True:
            continue
        sources = row.get("official_sources")
        if not isinstance(sources, list) or not sources:
            missing.append({"intent_id": intent_id, "url": "(todas)"})
            continue
        by_url: dict[str, dict[str, Any]] = {}
        for index, source in enumerate(sources, 1):
            identity = _stock_source_identity(
                source, f"{rel_path}:{intent_id}:official_sources[{index}]")
            if identity["url"] in by_url:
                raise ValueError(f"{intent_id}: URL duplicada no estoque")
            by_url[identity["url"]] = source
        expected_by_url = {
            source["url"]: source
            for source in projection.sources_by_intent[intent_id]
        }
        absent = sorted(set(expected_by_url) - set(by_url))
        if absent:
            missing.extend({"intent_id": intent_id, "url": url} for url in absent)
            continue
        page_changed = False
        normalized_sources: list[dict[str, Any]] = []
        for source in sources:
            expected = expected_by_url.get(source["url"])
            if expected is None:
                normalized_sources.append(source)
                continue
            normalized: dict[str, Any] = dict(expected)
            if "verified_at" in source and "http_status" in source:
                normalized["verified_at"] = source["verified_at"]
                normalized["http_status"] = source["http_status"]
            normalized_sources.append(normalized)
            if normalized != source:
                page_changed = True
        if page_changed:
            row["official_sources"] = normalized_sources
            changed.append(intent_id)
    if missing:
        raise ValueError(
            "reconciliação recusa adicionar URL sem proveniência live: "
            f"{missing[:8]}")
    if changed:
        payload = ("\n".join(json.dumps(
            row, ensure_ascii=False, separators=(",", ":"),
        ) for row in rows) + "\n").encode("utf-8")
        queue.atomic_replace_cas(path, payload, snapshot.digest)
    result = check_stock(canonical_root, [rel_path])
    if not result["ok"]:
        raise RuntimeError(
            f"reconciliação não fechou gate: {result['defects'][:8]}")
    return {"file": rel_path, "changed_intents": changed, **result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--file", action="append", default=[])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        if args.write:
            if len(args.file) != 1:
                raise ValueError("--write exige exatamente um --file")
            result = reconcile_file(args.root, args.file[0])
        else:
            result = check_stock(args.root, args.file or None)
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
