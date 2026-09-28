#!/usr/bin/env python3
"""Consolida a duplicata Aéreo preservando a preimagem autenticada (DEC-020)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

if __package__:
    from .v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease
else:
    from v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease


ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data/editorial/v2_pages"
SOURCE_SHARD = "codex-educacao-portfolio-aereo-r03.jsonl"
CANONICAL_SHARD = "codex-educacao-recovered-portfolio-aereo-r03.jsonl"
ARCHIVE_REL = (
    "data/editorial/v2_superseded/"
    "duplicate-intent-consolidation-aereo-2026-07-21.jsonl"
)
ARCHIVE = ROOT / ARCHIVE_REL
SOURCE_SHA256 = "3fe09b94204781973af365aae08401388a719d977184631d7f009ac1316ebdfd"
# Preimagem do vencedor tal como revisado em 2026-07-21 (pousado em fccac729).
# Fica gravada no archive como proveniência da adjudicação; NÃO é pino do
# shard vivo — ver authenticate_canonical.
CANONICAL_SHA256 = "32e35f362f706a4a4ed751fbd589d1876997eb084b4eaf5a3a8d5d064998b84c"
EXPECTED_INTENTS = (
    "aer-atraso-restricao-trafego-aereo-controle-solo",
    "aer-cancelamento-fechamento-aeroporto-obras-determinacao-autoridade",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_lines(payload: bytes, label: str) -> list[tuple[str, dict]]:
    if not payload or not payload.endswith(b"\n") or b"\r" in payload:
        raise ValueError(f"{label}: JSONL sem framing canônico")
    rows = []
    for line_number, raw in enumerate(payload[:-1].split(b"\n"), 1):
        pairs = json.loads(
            raw, object_pairs_hook=lambda values: ("object", values))
        if (not isinstance(pairs, tuple) or pairs[0] != "object" or
                len({key for key, _ in pairs[1]}) != len(pairs[1])):
            raise ValueError(f"{label}:{line_number}: objeto/chaves inválidos")
        record = dict(pairs[1])
        rows.append((raw.decode("utf-8"), record))
    return rows


def authenticate_canonical(canonical: bytes) -> None:
    """Autentica o shard vencedor VIVO pelo invariante, não pelo byte.

    Espelha o gate irmão em Go (internal/v2supersessionintegrity/integrity.go,
    issues "canonical_same_intent_missing" e "canonical_line_mismatch"): para
    cada intenção adjudicada, o vencedor tem de conter exatamente UM registro
    com a mesma intent_id, ativo, na mesma canonical_line que o archive
    registra. O byte do vencedor não é pinado: ele é estoque vivo e evolui
    legitimamente — o reparo de citação 8e49a419 (2026-08-12) reescreveu
    official_sources das duas linhas e CANONICAL_SHA256 (a preimagem revisada
    em 2026-07-21, preservada no archive como proveniência) deixou de casar;
    pinar o vencedor congelaria a página publicada contra qualquer reparo.
    Todo desvio, inclusive framing quebrado, sai como
    "shard vencedor revisado divergiu: <motivo>".
    """
    try:
        rows = canonical_lines(canonical, CANONICAL_SHARD)
    except ValueError as error:
        raise ValueError(f"shard vencedor revisado divergiu: {error}") from error
    for canonical_line, intent_id in enumerate(EXPECTED_INTENTS, 1):
        matches = [number for number, (_raw, record) in enumerate(rows, 1)
                   if record.get("intent_id") == intent_id]
        if len(matches) != 1 or rows[matches[0] - 1][1].get("skipped"):
            raise ValueError(
                "shard vencedor revisado divergiu: "
                f"{intent_id} deveria ter exatamente um registro ativo, "
                f"encontrados {len(matches)}")
        if matches[0] != canonical_line:
            raise ValueError(
                "shard vencedor revisado divergiu: "
                f"{intent_id} está na linha {matches[0]}, o archive registra "
                f"canonical_line={canonical_line}")


def build_artifacts(source: bytes, canonical: bytes) -> tuple[bytes, bytes]:
    # O perdedor é preimagem congelada: tombstonado e preservado no archive,
    # nada o evolui legitimamente — o pino de byte continua.
    if sha256(source) != SOURCE_SHA256:
        raise ValueError("preimagem do shard perdedor divergiu")
    authenticate_canonical(canonical)
    source_rows = canonical_lines(source, SOURCE_SHARD)
    if len(source_rows) != 2:
        raise ValueError(
            "a adjudicação Aéreo exige exatamente duas linhas no shard perdedor")
    source_intents = tuple(row[1].get("intent_id") for row in source_rows)
    if source_intents != EXPECTED_INTENTS:
        raise ValueError("intents Aéreo não coincidem com a autoridade revisada")
    if any(row[1].get("skipped") for row in source_rows):
        raise ValueError(
            "adjudicação esperava dois registros ativos no shard perdedor")

    archive_rows = []
    tombstones = []
    for index, (original_line, _record) in enumerate(source_rows, 1):
        record_sha = sha256(original_line.encode("utf-8"))
        intent_id = EXPECTED_INTENTS[index - 1]
        archive_rows.append({
            "schema_version": 1,
            "record_type": "v2_duplicate_intent_supersession",
            "intent_id": intent_id,
            "source_shard": SOURCE_SHARD,
            "source_line": index,
            "source_shard_sha256": SOURCE_SHA256,
            "source_record_sha256": record_sha,
            "canonical_shard": CANONICAL_SHARD,
            "canonical_line": index,
            "canonical_shard_sha256": CANONICAL_SHA256,
            "original_line": original_line,
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
            "approval": False,
            "publicly_indexable": False,
            "public_path": "",
            "checked_at": "2026-07-21",
        })
        tombstones.append({
            "intent_id": intent_id,
            "skipped": True,
            "skip_reason": "duplicate_intent_consolidated",
            "superseded_by": CANONICAL_SHARD,
            "supersession_archive": ARCHIVE_REL,
            "superseded_record_sha256": record_sha,
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
        })
    encode = lambda rows: ("\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        for row in rows) + "\n").encode("utf-8")
    return encode(tombstones), encode(archive_rows)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run() -> tuple[str, str]:
    source_path = PAGES / SOURCE_SHARD
    canonical_path = PAGES / CANONICAL_SHARD
    source = source_path.read_bytes()
    canonical = canonical_path.read_bytes()
    if ARCHIVE.exists():
        archive = ARCHIVE.read_bytes()
        # Idempotência depois da primeira execução: autentique o archive e os
        # tombstones reconstruindo-os a partir das preimagens preservadas.
        archive_records = canonical_lines(archive, ARCHIVE_REL)
        if len(archive_records) != 2:
            raise ValueError("archive Aéreo existente tem cardinalidade inválida")
        recovered_source = ("\n".join(
            record[1]["original_line"] for record in archive_records) + "\n"
        ).encode("utf-8")
        expected_source, expected_archive = build_artifacts(
            recovered_source, canonical)
        if archive != expected_archive or source != expected_source:
            raise ValueError("estado Aéreo existente não coincide com a adjudicação")
        return sha256(source), sha256(archive)

    tombstones, archive = build_artifacts(source, canonical)
    # O archive nasce antes dos tombstones: uma interrupção nunca deixa uma
    # referência no estoque sem a preimagem correspondente já durável.
    atomic_write(ARCHIVE, archive)
    if source_path.read_bytes() != source or canonical_path.read_bytes() != canonical:
        raise ValueError("CAS Aéreo mudou antes da promoção dos tombstones")
    atomic_write(source_path, tombstones)
    return sha256(tombstones), sha256(archive)


def main() -> int:
    try:
        with canonical_stock_write_lease(ROOT):
            source_hash, archive_hash = run()
    except StockEpochBusy as error:
        print(f"consolidate-v2-duplicate-aereo: estoque ocupado: {error}")
        return 75
    print(
        f"source={SOURCE_SHARD} sha256={source_hash} archive={ARCHIVE_REL} "
        f"archive_sha256={archive_hash} canonical={CANONICAL_SHARD} "
        f"canonical_sha256={CANONICAL_SHA256} publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
