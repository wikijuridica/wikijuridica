#!/usr/bin/env python3
"""Fail closed when a portfolio claims researched but unresolved sources."""

import argparse
import glob
import json
import os
import pathlib
import re
import stat
import sys
from urllib.parse import parse_qsl, unquote, urlsplit, urlunsplit


HINT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTENT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_KINDS = {
    "legal_act",
    "binding_precedent",
    "judicial_decision",
    "official_guidance",
    "official_service",
}
SOURCE_FIELDS = {"name", "url", "anchor_claim", "source_kind"}
MAX_SOURCE_RUNES = 8_192


def normalize_https_url(value: object) -> str:
    """Return a strict canonical comparison URL, or an empty string."""
    if (not isinstance(value, str) or not value or
            len(value) > MAX_SOURCE_RUNES or value != value.strip() or
            any(ord(char) < 32 for char in value) or "\\" in value or
            re.search(r"%(?![0-9a-fA-F]{2})", value)):
        return ""
    try:
        parsed = urlsplit(value)
        query_pairs = parse_qsl(
            parsed.query, keep_blank_values=True, strict_parsing=True)
        port = parsed.port
    except (UnicodeError, ValueError):
        return ""
    if (parsed.scheme.lower() != "https" or not parsed.hostname or
            parsed.username or parsed.password or port is not None or
            parsed.fragment):
        return ""
    if len({key for key, _ in query_pairs}) != len(query_pairs):
        return ""
    try:
        path = unquote(parsed.path or "/", errors="strict")
    except UnicodeError:
        return ""
    if any(part in {".", ".."} for part in path.split("/")):
        return ""
    path = re.sub(r"/{2,}", "/", path)
    if path != "/":
        path = path.rstrip("/")
    host = parsed.hostname.lower().rstrip(".")
    return urlunsplit(("https", host, path, parsed.query, ""))


class RegistryMatcher:
    """Match URLs only below an unambiguous exact official registry prefix."""

    def __init__(self, records: list[dict]):
        self.entries = []
        seen_ids = set()
        for record in records:
            source_id = record.get("source_id") if isinstance(record, dict) else None
            domains = record.get("official_domains") if isinstance(record, dict) else None
            bases = record.get("canonical_base_urls") if isinstance(record, dict) else None
            if (not isinstance(source_id, str) or HINT_ID.fullmatch(source_id) is None or
                    source_id in seen_ids or not isinstance(domains, list) or not domains or
                    not isinstance(bases, list) or not bases):
                raise ValueError("source registry record lacks exact URL identity")
            seen_ids.add(source_id)
            domain_set = {
                value.lower().rstrip(".") for value in domains
                if isinstance(value, str) and value
            }
            if len(domain_set) != len(domains):
                raise ValueError(f"source registry domains are invalid: {source_id}")
            accepted = 0
            for base in bases:
                normalized = normalize_https_url(base)
                if not normalized:
                    raise ValueError(f"source registry prefix is invalid: {source_id}")
                parsed = urlsplit(normalized)
                if parsed.hostname not in domain_set:
                    raise ValueError(f"source registry host mismatch: {source_id}")
                self.entries.append(
                    (source_id, parsed.hostname, parsed.path or "/", parsed.query))
                accepted += 1
            if not accepted:
                raise ValueError(f"source registry has no HTTPS prefix: {source_id}")

    def match(self, value: object) -> str:
        normalized = normalize_https_url(value)
        if not normalized:
            return ""
        parsed = urlsplit(normalized)
        candidates = []
        for source_id, host, base_path, base_query in self.entries:
            if parsed.hostname != host:
                continue
            if not (parsed.path == base_path or
                    parsed.path.startswith(base_path.rstrip("/") + "/")):
                continue
            if base_query and parsed.query != base_query:
                continue
            candidates.append((len(base_path), source_id))
        if not candidates:
            return ""
        longest = max(length for length, _ in candidates)
        matches = {source_id for length, source_id in candidates if length == longest}
        return next(iter(matches)) if len(matches) == 1 else ""


def decode_jsonl(raw: bytes, label: str) -> list[dict]:
    if not raw or not raw.endswith(b"\n") or b"\r" in raw:
        raise ValueError(f"{label}: JSONL is not canonical")
    rows = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line:
            raise ValueError(f"{label}:{line_number}: blank line")
        rows.append(decode_object(line, f"{label}:{line_number}"))
    return rows


def read_regular_snapshot(path: pathlib.Path, maximum: int) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                before.st_size < 0 or before.st_size > maximum):
            raise ValueError(f"{path}: unsafe or oversized regular file")
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after = os.fstat(descriptor)
        identity = lambda value: (
            value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_ctime_ns)
        if len(payload) > maximum or identity(before) != identity(after):
            raise ValueError(f"{path}: file changed during bounded read")
        return payload
    finally:
        os.close(descriptor)


def decode_object(raw: bytes, label: str) -> dict:
    def no_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"{label}: duplicate JSON key {key}")
            value[key] = item
        return value

    def reject_nonfinite(value):
        raise ValueError(f"{label}: non-finite JSON number {value}")

    value = json.loads(
        raw, object_pairs_hook=no_duplicates,
        parse_constant=reject_nonfinite)
    if not isinstance(value, dict):
        raise ValueError(f"{label}: JSON value is not an object")
    return value


def require_real_directory(path: pathlib.Path) -> None:
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError(f"{path}: directory is absent, symlinked, or unsafe")


def audit(root: pathlib.Path) -> dict:
    require_real_directory(root / "data/editorial/portfolio_v2")
    require_real_directory(root / "data/source-registry")
    catalog_path = root / "data/editorial/v2_source_hint_catalog.json"
    catalog = decode_object(
        read_regular_snapshot(catalog_path, 8 << 20), str(catalog_path))
    sources = catalog.get("source_hints")
    if not isinstance(sources, dict) or any(
            not isinstance(key, str) or HINT_ID.fullmatch(key) is None
            for key in sources):
        raise ValueError("source hint catalog is not canonical")

    registry_path = root / "data/source-registry/source_registry_v2.jsonl"
    registry = decode_jsonl(
        read_regular_snapshot(registry_path, 16 << 20), str(registry_path))
    matcher = RegistryMatcher(registry)
    for hint, source in sources.items():
        if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
            raise ValueError(f"source hint catalog entry has invalid shape: {hint}")
        name = source.get("name")
        claim = source.get("anchor_claim")
        kind = source.get("source_kind")
        if (not isinstance(name, str) or not name.strip() or name != name.strip() or
                len(name) > 512 or not isinstance(claim, str) or
                not claim.strip() or claim != claim.strip() or
                len(claim) > MAX_SOURCE_RUNES or kind not in SOURCE_KINDS or
                not matcher.match(source.get("url"))):
            raise ValueError(f"source hint catalog entry is not resolved: {hint}")

    findings = []
    records = researched = pending = 0
    pending_mixed = pending_fully_unresolved = pending_fully_resolved = 0
    seen = set()
    pattern = str(root / "data/editorial/portfolio_v2/*.jsonl")
    for filename in sorted(glob.glob(pattern)):
        payload = read_regular_snapshot(pathlib.Path(filename), 64 << 20)
        if not payload or not payload.endswith(b"\n") or b"\r" in payload:
            raise ValueError(f"{filename}: portfolio JSONL is not canonical")
        for line_number, raw in enumerate(payload.splitlines(), 1):
            row = decode_object(raw, f"{filename}:{line_number}")
            intent = row.get("intent_id")
            hints = row.get("source_hints")
            needs_research = row.get("needs_source_research")
            if (not isinstance(intent, str) or
                    INTENT_ID.fullmatch(intent) is None or intent in seen or
                    not isinstance(hints, list) or not hints or
                    len(hints) != len(set(hints)) or
                    any(not isinstance(hint, str) or not hint or
                        hint != hint.strip() for hint in hints) or
                    type(needs_research) is not bool):
                raise ValueError(
                    f"{filename}:{line_number}: invalid portfolio source identity")
            seen.add(intent)
            records += 1
            if needs_research:
                pending += 1
                # Censo da fila de pesquisa aberta (só informativo; a fila de
                # escrita já trata esses intents como tombstone-only via
                # derive_writing_source_resolution). "Misto" = ao menos um
                # hint resolve no catálogo e ao menos um não: a rota de
                # destrave é completar catálogo/alias pelo canal sancionado,
                # nunca afrouxar o resolvedor para override parcial.
                pending_unresolved = [
                    hint for hint in hints
                    if HINT_ID.fullmatch(hint) is None or hint not in sources]
                if pending_unresolved and len(pending_unresolved) < len(hints):
                    pending_mixed += 1
                elif pending_unresolved:
                    pending_fully_unresolved += 1
                else:
                    pending_fully_resolved += 1
                continue
            researched += 1
            unresolved = sorted(
                hint for hint in hints
                if HINT_ID.fullmatch(hint) is None or hint not in sources)
            if unresolved:
                findings.append({
                    "file": os.path.relpath(filename, root).replace(os.sep, "/"),
                    "line": line_number,
                    "intent_id": intent,
                    "unresolved_source_hints": unresolved,
                    "next_action": (
                        "resolve exact official sources or set "
                        "needs_source_research=true"),
                })
    return {
        "schema_version": 1,
        "portfolio_records": records,
        "researched_records": researched,
        "research_pending_records": pending,
        "research_pending_mixed_records": pending_mixed,
        "research_pending_fully_unresolved_records": pending_fully_unresolved,
        "research_pending_fully_resolved_records": pending_fully_resolved,
        "researched_with_unresolved_sources": len(findings),
        "passed": not findings,
        "publication_allowed": False,
        "index_policy": "noindex",
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-findings", type=int, default=100)
    args = parser.parse_args()
    if args.max_findings < 0:
        parser.error("--max-findings must be nonnegative")
    try:
        report = audit(pathlib.Path(args.root).resolve())
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"check-v2-portfolio-source-hints: {exc}", file=sys.stderr)
        return 2
    report["findings_total"] = len(report["findings"])
    report["findings"] = report["findings"][:args.max_findings]
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
