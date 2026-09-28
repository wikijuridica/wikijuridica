#!/usr/bin/env python3
"""Consolida duplicatas v2 preservando os registros substituídos fora do estoque ativo."""

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease

PAGES = ROOT / "data/editorial/v2_pages"
ARCHIVE_REL = "data/editorial/v2_superseded/duplicate-intent-consolidation-2026-07-11.jsonl"
ARCHIVE = ROOT / ARCHIVE_REL
LOCK = ROOT / "data/editorial/.duplicate-intent-consolidation-20260711.lock"
CANONICAL = "imobiliario-05.jsonl"
EXPECTED_SHAS = {
    "imobiliario-05.jsonl": "cfba1f1fad1664866b4ae3d4781e272e0342e82c148217f1e1a39b9daa2f1b6f",
    "imobiliario-10.jsonl": "316aec3adb54230526a7eecad272f89602dda06d9927daeb60d446d037759c77",
    "imobiliario-12.jsonl": "270609bcbabf88fc9c5a6ed55848f42dc66c17105385c11213804e07ec2ff41a",
    "imobiliario-15.jsonl": "d0b6b9e00964ec4c8e88faec2f6420e2e900aed26d093c1008a9c9689cc6f7d5",
    "imobiliario-20.jsonl": "d8bccb04c9fddc16e43f1ae3876ed19551aba35d51abdb4a19c819540339b896",
    "imobiliario-22.jsonl": "92d4ff6af1c2d16d4188db386e5af7eedd3e947a2ccf7e79561c60c7cec3bb2d",
}
EXPECTED_INTENTS = {
    "imob-arrematacao-dividas-anteriores",
    "imob-arvore-vizinho-caiu-dano",
    "imob-cessao-direitos-hereditarios-imovel",
    "imob-condominio-cortar-agua-devedor",
    "imob-condominio-negativar-devedor",
    "imob-divida-condominio-omitida-venda",
    "imob-doacao-imovel-revogacao",
    "imob-dupla-venda-mesmo-imovel",
    "imob-ex-companheiro-nao-sai-imovel",
    "imob-exclusividade-corretor-vendi-sozinho",
    "imob-gaveta-comprador-nao-paga-banco",
    "imob-indisponibilidade-bens-vendedor",
    "imob-multa-inquilino-cobrada-dono",
    "imob-rateio-obra-luxo-minoria",
    "imob-sindico-nao-cobra-inadimplentes",
    "imob-vendedor-atrasa-documentacao",
    "imob-vizinho-construiu-dentro-terreno",
}


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def exclusive_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        os.fchmod(fd, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def assert_inputs_unchanged(payloads):
    for shard, expected_payload in payloads.items():
        actual_payload = (PAGES / shard).read_bytes()
        if actual_payload != expected_payload:
            raise SystemExit(
                f"pre-commit CAS mismatch {shard}: "
                f"expected={sha256(expected_payload)} actual={sha256(actual_payload)}"
            )


def load_existing_archive_rows():
    if not ARCHIVE.exists():
        return []
    rows = []
    for line_number, raw in enumerate(
            ARCHIVE.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            raise SystemExit(f"blank archive line {line_number}")
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise SystemExit(f"archive line {line_number} is not an object")
        rows.append(record)
    return rows


def recover_original_payload(shard, observed_payload, archive_rows):
    relevant = [
        record for record in archive_rows
        if record.get("source_shard") == shard
    ]
    if not relevant:
        return observed_payload
    lines = observed_payload.decode("utf-8").splitlines()
    seen_lines = set()
    for record in relevant:
        source_line = record.get("source_line")
        original_line = record.get("original_line")
        record_sha = record.get("source_record_sha256")
        if (not isinstance(source_line, int) or isinstance(source_line, bool) or
                source_line <= 0 or source_line > len(lines) or
                source_line in seen_lines or not isinstance(original_line, str) or
                sha256(original_line.encode("utf-8")) != record_sha):
            raise SystemExit(f"invalid recovery evidence for {shard}")
        seen_lines.add(source_line)
        current_line = lines[source_line - 1]
        if sha256(current_line.encode("utf-8")) == record_sha:
            continue
        try:
            tombstone = json.loads(current_line)
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"cannot recover {shard} line {source_line}: {exc}"
            ) from exc
        if (not isinstance(tombstone, dict) or not tombstone.get("skipped") or
                tombstone.get("skip_reason") != "duplicate_intent_consolidated" or
                tombstone.get("intent_id") != record.get("intent_id") or
                tombstone.get("superseded_record_sha256") != record_sha):
            raise SystemExit(
                f"current {shard} line {source_line} is neither original nor trusted tombstone"
            )
        lines[source_line - 1] = original_line
    return ("\n".join(lines) + "\n").encode("utf-8")


def run_locked():
    existing_archive_rows = load_existing_archive_rows()
    observed_payloads = {}
    payloads = {}
    parsed = {}
    for shard, expected_sha in EXPECTED_SHAS.items():
        path = PAGES / shard
        observed_payload = path.read_bytes()
        observed_payloads[shard] = observed_payload
        payload = recover_original_payload(
            shard, observed_payload, existing_archive_rows)
        actual_sha = sha256(payload)
        if actual_sha != expected_sha:
            raise SystemExit(f"CAS mismatch {shard}: expected={expected_sha} actual={actual_sha}")
        payloads[shard] = payload
        rows = []
        for line_number, raw in enumerate(payload.decode("utf-8").splitlines(), 1):
            rows.append((line_number, raw, json.loads(raw)))
        parsed[shard] = rows

    canonical = {}
    for line_number, _, record in parsed[CANONICAL]:
        intent = record.get("intent_id")
        if intent in EXPECTED_INTENTS and not record.get("skipped"):
            if intent in canonical:
                raise SystemExit(f"duplicate canonical intent {intent}")
            canonical[intent] = line_number
    if set(canonical) != EXPECTED_INTENTS:
        raise SystemExit(
            f"canonical set mismatch missing={sorted(EXPECTED_INTENTS - set(canonical))} "
            f"extra={sorted(set(canonical) - EXPECTED_INTENTS)}"
        )

    archive_rows = []
    rewritten = {}
    retired = set()
    for shard, rows in parsed.items():
        if shard == CANONICAL:
            continue
        output = []
        for line_number, raw, record in rows:
            intent = record.get("intent_id")
            if intent not in EXPECTED_INTENTS or record.get("skipped"):
                output.append(raw)
                continue
            if intent in retired:
                raise SystemExit(f"more than one losing active record for {intent}")
            retired.add(intent)
            record_sha = sha256(raw.encode("utf-8"))
            archive_rows.append({
                "schema_version": 1,
                "record_type": "v2_duplicate_intent_supersession",
                "intent_id": intent,
                "source_shard": shard,
                "source_line": line_number,
                "source_shard_sha256": EXPECTED_SHAS[shard],
                "source_record_sha256": record_sha,
                "canonical_shard": CANONICAL,
                "canonical_line": canonical[intent],
                "canonical_shard_sha256": EXPECTED_SHAS[CANONICAL],
                "original_line": raw,
                "index_policy": "noindex",
                "render_allowed": False,
                "sitemap_allowed": False,
                "publication_allowed": False,
                "checked_at": "2026-07-11",
            })
            output.append(json.dumps({
                "intent_id": intent,
                "skipped": True,
                "skip_reason": "duplicate_intent_consolidated",
                "superseded_by": CANONICAL,
                "supersession_archive": ARCHIVE_REL,
                "superseded_record_sha256": record_sha,
                "index_policy": "noindex",
                "render_allowed": False,
                "sitemap_allowed": False,
                "publication_allowed": False,
            }, ensure_ascii=False, separators=(",", ":")))
        rewritten[shard] = ("\n".join(output) + "\n").encode("utf-8")

    if retired != EXPECTED_INTENTS:
        raise SystemExit(
            f"losing set mismatch missing={sorted(EXPECTED_INTENTS - retired)} "
            f"extra={sorted(retired - EXPECTED_INTENTS)}"
        )
    archive_rows.sort(key=lambda row: (row["source_shard"], row["source_line"]))
    archive_payload = ("\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        for row in archive_rows
    ) + "\n").encode("utf-8")
    assert_inputs_unchanged(observed_payloads)
    if ARCHIVE.exists():
        existing_archive = ARCHIVE.read_bytes()
        if existing_archive != archive_payload:
            raise SystemExit(
                f"archive CAS mismatch {ARCHIVE_REL}: "
                f"expected={sha256(archive_payload)} actual={sha256(existing_archive)}"
            )
    else:
        atomic_write(ARCHIVE, archive_payload)

    for shard in sorted(rewritten):
        if observed_payloads[shard] != rewritten[shard]:
            atomic_write(PAGES / shard, rewritten[shard])

    print(f"archive={ARCHIVE_REL} rows={len(archive_rows)} sha256={sha256(archive_payload)}")
    for shard in sorted(rewritten):
        print(f"shard={shard} sha256={sha256(rewritten[shard])}")


def main():
    canonical_root = ROOT
    try:
        # Global-first evita inversão com ingest/finalização: archive, shards,
        # releituras CAS, temporários, renames e fsyncs compartilham um epoch.
        with canonical_stock_write_lease(canonical_root):
            with exclusive_lock(LOCK):
                run_locked()
    except StockEpochBusy as error:
        print(
            f"consolidate-v2-duplicate-intents: canonical stock busy: {error}",
            file=sys.stderr,
        )
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
