#!/usr/bin/env python3
"""Fail-close only the 60 Wave 3 portfolio records added by 1bba0ec6."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
COMMIT = "1bba0ec6"
TARGETS = {
    Path("data/editorial/portfolio_v2/consumidor.jsonl"): {
        "expected_count": 39,
        "expected_sha256": "fa5cfc7605eb86b5f9ded248bd3dfb9f97a977a5507dac869d1abd464b3d8475",
    },
    Path("data/editorial/portfolio_v2/bancario.jsonl"): {
        "expected_count": 21,
        "expected_sha256": "29e2cbfa9d3d34dcf098ca8c21e7318756b76b41f08a87655b0abeef4fb47796",
    },
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def commit_added_ids(path: Path, expected_count: int) -> set[str]:
    output = subprocess.check_output(
        [
            "git",
            "diff",
            "--unified=0",
            f"{COMMIT}^",
            COMMIT,
            "--",
            str(path),
        ],
        cwd=ROOT,
        text=True,
    )
    ids: set[str] = set()
    for line in output.splitlines():
        if not line.startswith("+{"):
            continue
        record = json.loads(line[1:])
        intent_id = record["intent_id"]
        if not record.get("family", "").startswith("w3-"):
            raise SystemExit(f"non-Wave-3 record in {COMMIT}: {intent_id}")
        if record.get("needs_source_research") is not False:
            raise SystemExit(f"unexpected historical flag in {COMMIT}: {intent_id}")
        ids.add(intent_id)
    if len(ids) != expected_count:
        raise SystemExit(
            f"{path}: expected {expected_count} added Wave-3 ids in {COMMIT}, got {len(ids)}"
        )
    return ids


def corrected_payload(path: Path, config: dict[str, object]) -> tuple[bytes, bytes, int]:
    absolute = ROOT / path
    before = absolute.read_bytes()
    actual_sha = sha256(before)
    expected_sha = str(config["expected_sha256"])
    if actual_sha != expected_sha:
        raise SystemExit(f"{path}: CAS mismatch: expected {expected_sha}, got {actual_sha}")

    ids = commit_added_ids(path, int(config["expected_count"]))
    seen: set[str] = set()
    changed = 0
    output: list[bytes] = []
    marker = b'"needs_source_research": false'
    replacement = b'"needs_source_research": true'

    for raw_line in before.splitlines(keepends=True):
        record = json.loads(raw_line)
        intent_id = record.get("intent_id")
        if intent_id not in ids:
            output.append(raw_line)
            continue
        if intent_id in seen:
            raise SystemExit(f"{path}: duplicate target intent_id {intent_id}")
        seen.add(intent_id)
        if record.get("needs_source_research") is not False:
            raise SystemExit(f"{path}: target is not false before migration: {intent_id}")
        if raw_line.count(marker) != 1:
            raise SystemExit(f"{path}: target flag marker is not unique: {intent_id}")

        updated_line = raw_line.replace(marker, replacement, 1)
        updated = json.loads(updated_line)
        expected = dict(record)
        expected["needs_source_research"] = True
        if updated != expected:
            raise SystemExit(f"{path}: non-flag mutation detected: {intent_id}")
        output.append(updated_line)
        changed += 1

    missing = ids - seen
    if missing:
        raise SystemExit(f"{path}: commit targets absent from current portfolio: {sorted(missing)}")
    if changed != int(config["expected_count"]):
        raise SystemExit(f"{path}: expected {config['expected_count']} changes, got {changed}")
    return before, b"".join(output), changed


def main() -> None:
    prepared: dict[Path, tuple[bytes, bytes, int]] = {
        path: corrected_payload(path, config) for path, config in TARGETS.items()
    }

    staged: list[tuple[Path, Path]] = []
    try:
        for path, (before, after, _) in prepared.items():
            absolute = ROOT / path
            if sha256(absolute.read_bytes()) != sha256(before):
                raise SystemExit(f"{path}: CAS changed immediately before write")
            descriptor, temp_name = tempfile.mkstemp(prefix=f".{absolute.name}.", dir=absolute.parent)
            temp_path = Path(temp_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(after)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_path, absolute.stat().st_mode)
            staged.append((temp_path, absolute))

        for temp_path, absolute in staged:
            os.replace(temp_path, absolute)

        total = 0
        for path, (_, after, changed) in prepared.items():
            total += changed
            print(f"{path}: changed={changed} sha256={sha256(after)}")
        print(f"total_changed={total}")
    finally:
        for temp_path, _ in staged:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
