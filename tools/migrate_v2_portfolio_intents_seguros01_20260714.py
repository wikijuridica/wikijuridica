#!/usr/bin/env python3
"""Preserva a preimagem SPVAT antiga e autoriza o novo slice DPVAT.

Produtor one-shot, idempotente e ancorado nos hashes observados. Ele nunca
altera ``v2_pages`` nem ``public``: grava primeiro o archive não renderizável e
depois acrescenta o registro de autorização. A fila continua responsável pela
substituição posterior sob CAS e pelos gates jurídico-editoriais das páginas
novas.
"""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
import pathlib
import stat
import sys

_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))
from tools import generate_v2_review_queue as queue
from tools import v2_portfolio_intent_migrations as migrations


ROOT = _IMPORT_ROOT
SOURCE_REL = "data/editorial/v2_pages/seguros-01.jsonl"
PORTFOLIO_REL = "data/editorial/portfolio_v2/seguros.jsonl"
ARCHIVE_REL = (
    "data/editorial/v2_superseded/"
    "portfolio-intent-migration-seguros-01-2026-07-14.jsonl"
)
MIGRATION_ID = "seguros-01-dpvat-spvat-20260714"
CHECKED_AT = "2026-07-14"
EXPECTED_SOURCE_SHA256 = (
    "ef2ee97f83c50ebe78e47315675321a202c0da6d1d5e1bfe9d0e5b482002dce6"
)
EXPECTED_PORTFOLIO_SHA256 = (
    "59bc1845d4c4dfaf80cdb8df414ab94b4795d3e8cbc782efc0612b3c11148d1f"
)
EXPECTED_ARCHIVE_SHA256 = (
    "d5002dcf016abad14fefcbdd761d0ed0b204c7f36120cc805130722ba0926988"
)
SOURCE_INTENT_IDS = [
    "seg-spvat-o-que-e",
    "seg-spvat-quem-tem-direito",
    "seg-spvat-como-pedir-morte",
    "seg-spvat-invalidez-permanente",
    "seg-spvat-despesas-medicas",
    "seg-spvat-valores",
    "seg-spvat-prazo-prescricao",
    "seg-spvat-sem-boletim",
    "seg-spvat-pedestre-atropelado",
    "seg-spvat-veiculo-nao-identificado",
    "seg-spvat-desconta-acao-judicial",
    "seg-spvat-premio-atrasado",
    "seg-spvat-beneficiarios-morte",
]
REPLACEMENT_INTENT_IDS = [
    "seg-spvat-status-2026",
    "seg-dpvat-canal-data-sinistro",
    "seg-dpvat-morte-caixa-2021-2023",
    "seg-dpvat-invalidez-caixa-2021-2023",
    "seg-dpvat-dams-caixa-2021-2023",
    "seg-dpvat-valores-historicos",
    "seg-dpvat-pendencia-documental-caixa",
    "seg-dpvat-boletim-documentos-caixa",
    "seg-dpvat-pedestre-janela-caixa",
    "seg-dpvat-veiculo-nao-identificado-caixa",
    "seg-dpvat-acidente-fim-2023",
    "seg-dpvat-menor-incapaz-caixa",
    "seg-dpvat-beneficiarios-morte-historico",
]
PORTFOLIO_FAMILIES = ["dpvat-spvat"]
PORTFOLIO_SKIP = 0
PORTFOLIO_TAKE = 13
PORTFOLIO_N = 13
# O worker de promoção segura o mesmo lock durante preflight final + CAS. Isso
# liga registry/archive ao epoch da substituição, em vez de apenas comparar
# hashes em duas janelas independentes.
LOCK_PATH = pathlib.Path("/tmp/opt-wiki-v2-portfolio-migrations.lock")
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_PORTFOLIO_BYTES = 64 * 1024 * 1024


@contextmanager
def exclusive_lock():
    fd = os.open(LOCK_PATH, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    locked = False
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                before.st_uid != os.geteuid()):
            raise RuntimeError(
                "lock da migração deve ser arquivo regular único do usuário atual")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        opened = os.fstat(fd)
        named = os.lstat(LOCK_PATH)
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or
                opened.st_uid != os.geteuid() or
                not stat.S_ISREG(named.st_mode) or named.st_nlink != 1 or
                (opened.st_dev, opened.st_ino) !=
                (named.st_dev, named.st_ino)):
            raise RuntimeError("lock da migração mudou durante a aquisição")
        os.fchmod(fd, 0o600)
        yield
    finally:
        if locked:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _snapshot_or_empty(
    path: pathlib.Path,
    *,
    max_bytes: int,
) -> queue.RegularFileSnapshot:
    if not os.path.lexists(path):
        return queue.RegularFileSnapshot(b"", migrations._digest(b""))
    return queue.read_regular_file_snapshot(path, max_bytes=max_bytes)


def _portfolio_family_intents(payload: bytes) -> list[str]:
    records = migrations._decode_jsonl(payload, PORTFOLIO_REL)
    return [record.get("intent_id") for record in records
            if record.get("family") == "dpvat-spvat"]


def _registry_payload(existing: bytes, record: dict) -> bytes:
    records = [] if not existing else migrations._decode_jsonl(
        existing, migrations.REGISTRY_REL_PATH)
    matching = [item for item in records if
                item.get("migration_id") == MIGRATION_ID or
                item.get("target_shard") == "seguros-01.jsonl"]
    if matching:
        if len(matching) != 1:
            raise RuntimeError("registro existente diverge da migração ancorada")
        if matching[0] == record:
            return existing
        # Evolução pré-commit do schema v1: a primeira versão ainda não
        # carregava o seletor que vincula o target ao slice vivo do portfólio.
        # Só substitua exatamente essa preimagem, sem aceitar qualquer outra
        # diferença silenciosa.
        selector_fields = {
            "portfolio_families", "portfolio_skip", "portfolio_take",
            "portfolio_n",
        }
        selectorless = {
            key: value for key, value in record.items()
            if key not in selector_fields
        }
        current_selectorless = {
            key: value for key, value in matching[0].items()
            if key not in selector_fields
        }
        current_selector = {
            key: matching[0][key] for key in selector_fields
            if key in matching[0]
        }
        legacy_selectors = [
            {},
            {
                "portfolio_families": ["dpvat-spvat"],
                "portfolio_skip": 0,
                "portfolio_take": 0,
                "portfolio_n": 13,
            },
        ]
        if (current_selectorless != selectorless or
                current_selector not in legacy_selectors):
            raise RuntimeError("registro existente diverge da migração ancorada")
        records = [item for item in records if item is not matching[0]]
    records.append(record)
    records.sort(key=lambda item: (item.get("target_shard", ""), item.get("migration_id", "")))
    return ("\n".join(json.dumps(
        item, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ) for item in records) + "\n").encode("utf-8")


def run() -> tuple[str, str]:
    source_path = ROOT / SOURCE_REL
    portfolio_path = ROOT / PORTFOLIO_REL
    archive_path = ROOT / ARCHIVE_REL
    registry_path = ROOT / migrations.REGISTRY_REL_PATH

    source = queue.read_regular_file_snapshot(
        source_path, max_bytes=MAX_SOURCE_BYTES)
    portfolio = queue.read_regular_file_snapshot(
        portfolio_path, max_bytes=MAX_PORTFOLIO_BYTES)
    if source.digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"preimagem mudou: expected={EXPECTED_SOURCE_SHA256} actual={source.digest}")
    if portfolio.digest != EXPECTED_PORTFOLIO_SHA256:
        raise RuntimeError(
            "portfolio mudou: atualize a migração por revisão para frente, "
            f"expected={EXPECTED_PORTFOLIO_SHA256} actual={portfolio.digest}")
    source_records = migrations._decode_jsonl(source.payload, SOURCE_REL)
    if [record.get("intent_id") for record in source_records] != SOURCE_INTENT_IDS:
        raise RuntimeError("preimagem não contém os 13 intent_ids ancorados")
    if _portfolio_family_intents(portfolio.payload) != REPLACEMENT_INTENT_IDS:
        raise RuntimeError("família dpvat-spvat diverge dos 13 replacements ancorados")

    archive_payload = migrations.build_archive_payload(
        MIGRATION_ID,
        "seguros-01.jsonl",
        source.payload,
        SOURCE_INTENT_IDS,
        REPLACEMENT_INTENT_IDS,
        PORTFOLIO_REL,
        portfolio.digest,
        CHECKED_AT,
    )
    archive_digest = migrations._digest(archive_payload)
    if archive_digest != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(
            "archive reconstruído diverge da evidência revisada: "
            f"expected={EXPECTED_ARCHIVE_SHA256} actual={archive_digest}")
    record = migrations.build_registry_record(
        MIGRATION_ID,
        "seguros-01.jsonl",
        source.payload,
        SOURCE_INTENT_IDS,
        REPLACEMENT_INTENT_IDS,
        PORTFOLIO_REL,
        portfolio.digest,
        ARCHIVE_REL,
        archive_payload,
        CHECKED_AT,
        PORTFOLIO_FAMILIES,
        PORTFOLIO_SKIP,
        PORTFOLIO_TAKE,
        PORTFOLIO_N,
    )

    archive_before = _snapshot_or_empty(
        archive_path, max_bytes=migrations.MAX_ARCHIVE_BYTES)
    if archive_before.payload and archive_before.payload != archive_payload:
        raise RuntimeError("archive existente diverge da preimagem ancorada")
    if not archive_before.payload:
        queue.atomic_replace_cas(archive_path, archive_payload, archive_before.digest)

    # A fonte e o portfólio precisam continuar no mesmo epoch depois da
    # primeira perna. Crash aqui é recuperável: o archive é append-only e o
    # rerun apenas conclui o registro.
    if (queue.snapshot_sha256(source_path) != source.digest or
            queue.snapshot_sha256(portfolio_path) != portfolio.digest):
        raise queue.CASMismatch("fonte ou portfolio mudou durante a migração")

    registry_before = _snapshot_or_empty(
        registry_path, max_bytes=migrations.MAX_REGISTRY_BYTES)
    registry_payload = _registry_payload(registry_before.payload, record)
    if registry_payload != registry_before.payload:
        queue.atomic_replace_cas(
            registry_path, registry_payload, registry_before.digest)

    catalog = migrations.load_catalog(ROOT)
    authorization = migrations.queue_authorization(
        catalog,
        "seguros-01.jsonl",
        source.payload,
        source.digest,
        PORTFOLIO_REL,
        portfolio.payload,
        portfolio.digest,
        REPLACEMENT_INTENT_IDS,
        PORTFOLIO_FAMILIES,
        PORTFOLIO_SKIP,
        PORTFOLIO_TAKE,
        PORTFOLIO_N,
    )
    if authorization is None:
        raise RuntimeError("migração persistida não autenticou a preimagem")
    if (queue.snapshot_sha256(source_path) != source.digest or
            queue.snapshot_sha256(portfolio_path) != portfolio.digest):
        raise queue.CASMismatch("fonte ou portfolio mudou antes do fechamento")
    return authorization["archive_sha256"], authorization["registry_sha256"]


def main() -> None:
    with exclusive_lock():
        archive_sha, registry_sha = run()
    print(
        f"migration={MIGRATION_ID} source_sha256={EXPECTED_SOURCE_SHA256} "
        f"archive_sha256={archive_sha} registry_sha256={registry_sha} "
        "source_unchanged=true public_unchanged=true publication=false"
    )


if __name__ == "__main__":
    main()
