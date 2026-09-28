"""Autentica substituições integrais de shards após migração de portfólio.

Uma mudança de intenção editorial pode retirar todos os ``intent_id`` de um
slice e colocar outros no mesmo shard.  A fila de escrita deve continuar
recusando extras por padrão: substituir o arquivo somente é permitido quando
um registro imutável preserva cada linha anterior e vincula, de forma
bijetiva, as intenções retiradas às novas intenções do portfólio.

Este módulo não escreve ``v2_pages`` nem publica conteúdo.  Ele apenas lê o
registro/arquivo de preservação e devolve uma autorização fechada que ainda é
submetida ao CAS normal do shard pelo workflow de escrita.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
from typing import Any, Mapping, Sequence

from tools import generate_v2_review_queue as queue


REGISTRY_REL_PATH = "data/editorial/v2_portfolio_intent_migrations.jsonl"
SCHEMA_V1 = "v2_portfolio_intent_migration_v1"
SCHEMA_V2 = "v2_portfolio_intent_migration_v2"
# Compatibilidade nominal para produtores v1 existentes. Novos registros
# pinados são emitidos explicitamente como SCHEMA_V2.
SCHEMA_VERSION = SCHEMA_V1
ARCHIVE_RECORD_TYPE = "v2_portfolio_intent_migration_archive"
MAX_REGISTRY_BYTES = 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_TARGET_BYTES = 64 * 1024 * 1024
MAX_PORTFOLIO_BYTES = 64 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_MIGRATION_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SHARD = re.compile(r"[a-z0-9_]+(?:-[a-z0-9_]+)+\.jsonl")
_INTENT = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_FAMILY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_PORTFOLIO = re.compile(
    r"data/editorial/portfolio_v2/[a-z0-9_]+(?:-[a-z0-9_]+)*\.jsonl"
)
_ARCHIVE = re.compile(
    r"data/editorial/v2_superseded/"
    r"portfolio-intent-migration-[a-z0-9_]+(?:-[a-z0-9_]+)*-"
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}\.jsonl"
)

_PUBLIC_CLOSED = {
    "index_policy": "noindex",
    "render_allowed": False,
    "sitemap_allowed": False,
    "publication_allowed": False,
    "approval": False,
    "publicly_indexable": False,
}

_REGISTRY_V1_KEYS = {
    "schema_version",
    "migration_id",
    "target_shard",
    "source_shard_sha256",
    "source_intent_ids",
    "replacement_intent_ids",
    "portfolio_families",
    "portfolio_skip",
    "portfolio_take",
    "portfolio_n",
    "portfolio_path",
    "portfolio_sha256",
    "archive_path",
    "archive_sha256",
    "checked_at",
    *_PUBLIC_CLOSED,
}
_REGISTRY_V2_KEYS = _REGISTRY_V1_KEYS | {"portfolio_intent_ids"}

_ARCHIVE_KEYS = {
    "schema_version",
    "record_type",
    "migration_id",
    "source_shard",
    "source_line",
    "source_shard_sha256",
    "source_record_sha256",
    "source_intent_id",
    "replacement_intent_id",
    "original_line",
    "portfolio_path",
    "portfolio_sha256",
    "checked_at",
    *_PUBLIC_CLOSED,
}

_QUEUE_V1_KEYS = {
    "schema_version",
    "migration_id",
    "target_shard",
    "source_shard_sha256",
    "source_intent_ids",
    "replacement_intent_ids",
    "portfolio_families",
    "portfolio_skip",
    "portfolio_take",
    "portfolio_n",
    "archive_path",
    "archive_sha256",
    "registry_sha256",
}
_QUEUE_V2_KEYS = _QUEUE_V1_KEYS | {
    "portfolio_intent_ids",
    "portfolio_path",
    "portfolio_sha256",
}


@dataclasses.dataclass(frozen=True)
class MigrationCatalog:
    registry_sha256: str
    migrations: Mapping[str, Mapping[str, Any]]
    dependency_sha256: Mapping[str, str]


def _verify_catalog_dependencies(
    canonical_root: pathlib.Path,
    catalog: MigrationCatalog,
) -> None:
    """Reautentica registry+archives no fim de cada preflight consumidor."""
    for rel_path, expected_digest in catalog.dependency_sha256.items():
        limit = (MAX_REGISTRY_BYTES if rel_path == REGISTRY_REL_PATH
                 else MAX_ARCHIVE_BYTES)
        snapshot = queue.read_regular_file_snapshot(
            canonical_root / rel_path, max_bytes=limit)
        if snapshot.digest != expected_digest:
            raise queue.CASMismatch(
                f"dependência de migração mudou durante preflight: {rel_path}")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_root(root: pathlib.Path | str) -> pathlib.Path:
    raw = os.fspath(root)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ValueError("raiz de migração inválida")
    absolute = pathlib.Path(os.path.abspath(raw))
    resolved = pathlib.Path(os.path.realpath(absolute))
    if resolved != absolute:
        raise ValueError("raiz de migração não pode conter symlink")
    if not absolute.is_dir():
        raise ValueError("raiz de migração deve ser diretório")
    return absolute


def _parse_date(value: Any, label: str) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise ValueError(f"{label} deve ser data canônica")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{label} deve ser YYYY-MM-DD") from error
    if parsed.isoformat() != value:
        raise ValueError(f"{label} deve ser YYYY-MM-DD")
    return value


def _canonical_list(value: Any, pattern: re.Pattern[str], label: str) -> list[str]:
    if (not isinstance(value, list) or not value or
            any(not isinstance(item, str) or pattern.fullmatch(item) is None
                for item in value) or
            len(set(value)) != len(value)):
        raise ValueError(f"{label} deve ser lista canônica, não vazia e única")
    return list(value)


def _closed_public_flags(record: Mapping[str, Any], label: str) -> None:
    for key, expected in _PUBLIC_CLOSED.items():
        if record.get(key) != expected:
            raise ValueError(f"{label} abre flag pública {key}")


def _decode_jsonl(payload: bytes, label: str) -> list[dict[str, Any]]:
    if not payload or not payload.endswith(b"\n"):
        raise ValueError(f"{label} deve terminar com newline")
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(payload[:-1].split(b"\n"), 1):
        if not raw:
            raise ValueError(f"{label}:{line_number}: linha vazia")
        try:
            record = queue.decode_json_no_duplicate_keys(
                raw, f"{label}:{line_number}")
        except ValueError as error:
            raise ValueError(f"{label}:{line_number}: JSON inválido") from error
        if not isinstance(record, dict):
            raise ValueError(f"{label}:{line_number}: registro não é objeto")
        records.append(record)
    return records


def _validate_registry_record(record: Mapping[str, Any], line: int) -> dict[str, Any]:
    label = f"{REGISTRY_REL_PATH}:{line}"
    schema = record.get("schema_version")
    expected_keys = (
        _REGISTRY_V1_KEYS if schema == SCHEMA_V1 else
        _REGISTRY_V2_KEYS if schema == SCHEMA_V2 else None
    )
    if expected_keys is None:
        raise ValueError(f"{label}: schema_version inválido")
    if set(record) != expected_keys:
        raise ValueError(f"{label}: schema aberto ou incompleto")
    migration_id = record.get("migration_id")
    target = record.get("target_shard")
    if not isinstance(migration_id, str) or _MIGRATION_ID.fullmatch(migration_id) is None:
        raise ValueError(f"{label}: migration_id inválido")
    if not isinstance(target, str) or _SHARD.fullmatch(target) is None:
        raise ValueError(f"{label}: target_shard inválido")
    for field in ("source_shard_sha256", "portfolio_sha256", "archive_sha256"):
        if not isinstance(record.get(field), str) or _SHA256.fullmatch(record[field]) is None:
            raise ValueError(f"{label}: {field} inválido")
    source_ids = _canonical_list(record.get("source_intent_ids"), _INTENT, label + ":source_intent_ids")
    replacement_ids = _canonical_list(record.get("replacement_intent_ids"), _INTENT, label + ":replacement_intent_ids")
    if len(source_ids) != len(replacement_ids) or set(source_ids) & set(replacement_ids):
        raise ValueError(f"{label}: migração deve ser bijetiva e disjunta")
    families = _canonical_list(
        record.get("portfolio_families"), _FAMILY,
        label + ":portfolio_families")
    skip = record.get("portfolio_skip")
    take = record.get("portfolio_take")
    count = record.get("portfolio_n")
    if (type(skip) is not int or skip < 0 or type(take) is not int or take < 0 or
            type(count) is not int or count != len(replacement_ids) or
            (take > 0 and (len(families) != 1 or take != count)) or
            (take == 0 and skip != 0)):
        raise ValueError(f"{label}: seletor de portfolio inválido")
    if schema == SCHEMA_V1:
        if take == 0:
            raise ValueError(
                f"{label}: schema v1 não autentica seletor pinado")
    else:
        portfolio_intent_ids = _canonical_list(
            record.get("portfolio_intent_ids"), _INTENT,
            label + ":portfolio_intent_ids")
        if (take != 0 or portfolio_intent_ids != replacement_ids or
                len(portfolio_intent_ids) != count):
            raise ValueError(
                f"{label}: schema v2 não vincula intent_ids pinados exatos")
    portfolio_path = record.get("portfolio_path")
    archive_path = record.get("archive_path")
    if not isinstance(portfolio_path, str) or _PORTFOLIO.fullmatch(portfolio_path) is None:
        raise ValueError(f"{label}: portfolio_path inválido")
    if not isinstance(archive_path, str) or _ARCHIVE.fullmatch(archive_path) is None:
        raise ValueError(f"{label}: archive_path inválido")
    _parse_date(record.get("checked_at"), label + ":checked_at")
    _closed_public_flags(record, label)
    return dict(record)


def _validate_archive(
    record: Mapping[str, Any],
    archive_payload: bytes,
) -> None:
    label = str(record["archive_path"])
    if len(archive_payload) > MAX_ARCHIVE_BYTES:
        raise ValueError(f"{label}: arquivo excede limite")
    rows = _decode_jsonl(archive_payload, label)
    source_ids = record["source_intent_ids"]
    replacements = record["replacement_intent_ids"]
    if len(rows) != len(source_ids):
        raise ValueError(f"{label}: quantidade de registros diverge da migração")
    original_lines: list[str] = []
    for index, row in enumerate(rows):
        row_label = f"{label}:{index + 1}"
        if set(row) != _ARCHIVE_KEYS:
            raise ValueError(f"{row_label}: schema aberto ou incompleto")
        if (row.get("schema_version") != 1 or
                row.get("record_type") != ARCHIVE_RECORD_TYPE or
                row.get("migration_id") != record["migration_id"] or
                row.get("source_shard") != record["target_shard"] or
                type(row.get("source_line")) is not int or
                row.get("source_line") != index + 1 or
                row.get("source_shard_sha256") != record["source_shard_sha256"] or
                row.get("source_intent_id") != source_ids[index] or
                row.get("replacement_intent_id") != replacements[index] or
                row.get("portfolio_path") != record["portfolio_path"] or
                row.get("portfolio_sha256") != record["portfolio_sha256"] or
                row.get("checked_at") != record["checked_at"]):
            raise ValueError(f"{row_label}: metadados divergem do registro")
        original = row.get("original_line")
        record_sha = row.get("source_record_sha256")
        if (not isinstance(original, str) or "\n" in original or "\r" in original or
                not isinstance(record_sha, str) or _SHA256.fullmatch(record_sha) is None or
                _digest(original.encode("utf-8")) != record_sha):
            raise ValueError(f"{row_label}: linha original/hash inválido")
        try:
            original_record = queue.decode_json_no_duplicate_keys(
                original, row_label + ":original_line")
        except ValueError as error:
            raise ValueError(f"{row_label}: linha original não é JSON") from error
        if (not isinstance(original_record, dict) or
                original_record.get("intent_id") != source_ids[index]):
            raise ValueError(f"{row_label}: intent_id original diverge")
        _parse_date(row.get("checked_at"), row_label + ":checked_at")
        _closed_public_flags(row, row_label)
        original_lines.append(original)
    reconstructed = ("\n".join(original_lines) + "\n").encode("utf-8")
    if _digest(reconstructed) != record["source_shard_sha256"]:
        raise ValueError(f"{label}: arquivo original não reconstrói source_shard_sha256")


def load_catalog(root: pathlib.Path | str) -> MigrationCatalog:
    """Carrega e autentica registro e archives, recusando paths indiretos."""
    canonical_root = _canonical_root(root)
    registry_path = canonical_root / REGISTRY_REL_PATH
    if not os.path.lexists(registry_path):
        return MigrationCatalog("", {}, {})
    registry = queue.read_regular_file_snapshot(
        registry_path, max_bytes=MAX_REGISTRY_BYTES)
    rows = _decode_jsonl(registry.payload, REGISTRY_REL_PATH)
    migrations: dict[str, Mapping[str, Any]] = {}
    dependencies: dict[str, str] = {REGISTRY_REL_PATH: registry.digest}
    seen_ids: set[str] = set()
    for line, raw in enumerate(rows, 1):
        record = _validate_registry_record(raw, line)
        target = record["target_shard"]
        migration_id = record["migration_id"]
        if target in migrations or migration_id in seen_ids:
            raise ValueError("registro de migrações repete alvo ou migration_id")
        archive = queue.read_regular_file_snapshot(
            canonical_root / record["archive_path"],
            max_bytes=MAX_ARCHIVE_BYTES,
        )
        if archive.digest != record["archive_sha256"]:
            raise ValueError(f"archive digest diverge: {record['archive_path']}")
        _validate_archive(record, archive.payload)
        dependencies[record["archive_path"]] = archive.digest
        migrations[target] = record
        seen_ids.add(migration_id)
    catalog = MigrationCatalog(registry.digest, migrations, dependencies)
    _verify_catalog_dependencies(canonical_root, catalog)
    return catalog


def _select_portfolio_intents(
    portfolio_payload: bytes,
    portfolio_path: str,
    families: Sequence[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: Sequence[str] | None,
) -> list[str]:
    """Autentica o owner de cada intent e deriva o seletor sem fallback."""
    family_order = _canonical_list(
        list(families), _FAMILY, "families da migração")
    if (type(skip) is not int or skip < 0 or
            type(take) is not int or take < 0 or
            type(expected_n) is not int or expected_n < 1 or
            (take > 0 and (
                len(family_order) != 1 or take != expected_n or
                intent_ids is not None)) or
            (take == 0 and (
                skip != 0 or
                not isinstance(intent_ids, list) or
                len(intent_ids) != expected_n or
                any(not isinstance(intent_id, str) or
                    _INTENT.fullmatch(intent_id) is None
                    for intent_id in intent_ids) or
                len(set(intent_ids)) != len(intent_ids)))):
        raise ValueError("seletor de portfolio da migração é inválido")
    by_family: dict[str, list[str]] = {}
    family_by_intent: dict[str, str] = {}
    for line_number, row in enumerate(
            _decode_jsonl(portfolio_payload, portfolio_path), 1):
        family = row.get("family")
        intent_id = row.get("intent_id")
        if (not isinstance(family, str) or
                _FAMILY.fullmatch(family) is None or
                not isinstance(intent_id, str) or
                _INTENT.fullmatch(intent_id) is None or
                intent_id in family_by_intent):
            raise ValueError(
                f"portfolio não canônico em {portfolio_path}:{line_number}")
        by_family.setdefault(family, []).append(intent_id)
        family_by_intent[intent_id] = family
    if take > 0:
        selected = by_family.get(family_order[0], [])[skip:skip + take]
    else:
        assert isinstance(intent_ids, list)
        allowed_families = set(family_order)
        selected = []
        for intent_id in intent_ids:
            owner_family = family_by_intent.get(intent_id)
            if owner_family is None:
                raise ValueError(
                    f"intent_id pinado não existe no portfolio: {intent_id}")
            if owner_family not in allowed_families:
                raise ValueError(
                    "intent_id pinado não pertence às families da migração: "
                    f"{intent_id}: {owner_family}")
            selected.append(intent_id)
        observed_family_runs: list[str] = []
        for intent_id in selected:
            owner_family = family_by_intent[intent_id]
            if (not observed_family_runs or
                    observed_family_runs[-1] != owner_family):
                observed_family_runs.append(owner_family)
        if observed_family_runs != family_order:
            raise ValueError(
                "ordem integral dos intent_ids não coincide com as families "
                "da migração")
    if len(selected) != expected_n:
        raise ValueError(
            f"seletor da migração selecionou {len(selected)}; "
            f"esperava {expected_n}")
    return selected


def queue_authorization(
    catalog: MigrationCatalog,
    target_shard: str,
    target_payload: bytes,
    target_sha256: str,
    portfolio_path: str,
    portfolio_payload: bytes,
    portfolio_sha256: str,
    expected_intents: Sequence[str],
    families: Sequence[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: Sequence[str] | None = None,
) -> dict[str, Any] | None:
    """Autoriza um replacement integral apenas para a preimagem registrada."""
    record = catalog.migrations.get(target_shard)
    if record is None:
        return None
    schema = record.get("schema_version")
    if schema == SCHEMA_V1:
        if intent_ids is not None:
            raise ValueError(
                f"migração {record['migration_id']} v1 não autentica pin")
    elif schema == SCHEMA_V2:
        if (not isinstance(intent_ids, list) or
                list(intent_ids) != record.get("portfolio_intent_ids") or
                list(intent_ids) != list(expected_intents)):
            raise ValueError(
                f"migração {record['migration_id']} não autentica pin exato")
    else:
        raise ValueError(f"migração {record['migration_id']} tem schema inválido")
    selected = _select_portfolio_intents(
        portfolio_payload, portfolio_path, families, skip, take,
        expected_n, intent_ids)
    if (_digest(target_payload) != target_sha256 or
            target_sha256 != record["source_shard_sha256"] or
            portfolio_path != record["portfolio_path"] or
            _digest(portfolio_payload) != portfolio_sha256 or
            portfolio_sha256 != record["portfolio_sha256"] or
            selected != list(expected_intents) or
            list(expected_intents) != record["replacement_intent_ids"] or
            list(families) != record["portfolio_families"] or
            skip != record["portfolio_skip"] or
            take != record["portfolio_take"] or
            expected_n != record["portfolio_n"]):
        raise ValueError(f"migração {record['migration_id']} diverge do snapshot vivo")
    current = _decode_jsonl(target_payload, target_shard)
    current_ids = [row.get("intent_id") for row in current]
    if current_ids != record["source_intent_ids"]:
        raise ValueError(f"migração {record['migration_id']} não cobre a preimagem exata")
    authorization = {
        "schema_version": schema,
        "migration_id": record["migration_id"],
        "target_shard": target_shard,
        "source_shard_sha256": record["source_shard_sha256"],
        "source_intent_ids": list(record["source_intent_ids"]),
        "replacement_intent_ids": list(record["replacement_intent_ids"]),
        "portfolio_families": list(record["portfolio_families"]),
        "portfolio_skip": record["portfolio_skip"],
        "portfolio_take": record["portfolio_take"],
        "portfolio_n": record["portfolio_n"],
        "archive_path": record["archive_path"],
        "archive_sha256": record["archive_sha256"],
        "registry_sha256": catalog.registry_sha256,
    }
    if schema == SCHEMA_V2:
        authorization["portfolio_intent_ids"] = list(
            record["portfolio_intent_ids"])
        authorization["portfolio_path"] = record["portfolio_path"]
        authorization["portfolio_sha256"] = record["portfolio_sha256"]
    return authorization


def verify_queue_authorization(
    root: pathlib.Path | str,
    authorization: Mapping[str, Any],
    target_rel_path: str,
    portfolio_rel_path: str,
    expected_intents: Sequence[str],
    families: Sequence[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: Sequence[str] | None = None,
) -> None:
    """Revalida no worker a autorização embutida pelo produtor da fila."""
    if not isinstance(authorization, Mapping):
        raise ValueError("autorização de migração da fila tem schema inválido")
    schema = authorization.get("schema_version")
    expected_keys = (
        _QUEUE_V1_KEYS if schema == SCHEMA_V1 else
        _QUEUE_V2_KEYS if schema == SCHEMA_V2 else None
    )
    if expected_keys is None or set(authorization) != expected_keys:
        raise ValueError("autorização de migração da fila tem schema inválido")
    canonical_root = _canonical_root(root)
    catalog = load_catalog(canonical_root)
    if authorization.get("registry_sha256") != catalog.registry_sha256:
        raise ValueError("registro de migrações mudou depois da fila")
    target_path = pathlib.PurePosixPath(target_rel_path)
    record = catalog.migrations.get(target_path.name)
    if (target_path.parent != pathlib.PurePosixPath("data/editorial/v2_pages") or
            target_path.name != authorization.get("target_shard") or
            record is None or
            not isinstance(portfolio_rel_path, str) or
            _PORTFOLIO.fullmatch(portfolio_rel_path) is None or
            portfolio_rel_path != record.get("portfolio_path")):
        raise ValueError("alvo de migração não coincide com o shard da fila")
    target = queue.read_regular_file_snapshot(
        canonical_root / target_rel_path, max_bytes=MAX_TARGET_BYTES)
    portfolio = queue.read_regular_file_snapshot(
        canonical_root / portfolio_rel_path, max_bytes=MAX_PORTFOLIO_BYTES)
    expected = queue_authorization(
        catalog,
        target_path.name,
        target.payload,
        target.digest,
        portfolio_rel_path,
        portfolio.payload,
        portfolio.digest,
        expected_intents,
        families,
        skip,
        take,
        expected_n,
        intent_ids,
    )
    if expected is None or dict(authorization) != expected:
        raise ValueError("autorização de migração não autentica o snapshot vivo")
    _verify_catalog_dependencies(canonical_root, catalog)
    if (queue.snapshot_sha256(
            canonical_root / target_rel_path,
            max_bytes=MAX_TARGET_BYTES) != target.digest or
            queue.snapshot_sha256(
                canonical_root / portfolio_rel_path,
                max_bytes=MAX_PORTFOLIO_BYTES) !=
            portfolio.digest):
        raise queue.CASMismatch(
            "preimagem ou portfolio mudou durante preflight de migração")


def verify_post_replacement_queue_authorization(
    root: pathlib.Path | str,
    authorization: Mapping[str, Any],
    target_rel_path: str,
    portfolio_rel_path: str,
    expected_intents: Sequence[str],
    families: Sequence[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: Sequence[str] | None = None,
) -> Mapping[str, str]:
    """Autentica uma autorização depois que o CAS já substituiu o shard.

    O verificador de resultado não pode exigir a antiga preimagem no alvo: o
    CAS legítimo já a removeu. O archive autenticado, porém, reconstrói esses
    bytes e o registro ainda fixa source hash, portfolio, seletor e replacement.
    Esta variante reusa essas provas sem transformar o novo shard na preimagem.
    Retorna os fingerprints que o consumidor deve reler antes de agir.
    """
    if not isinstance(authorization, Mapping):
        raise ValueError("autorização de migração da fila tem schema inválido")
    schema = authorization.get("schema_version")
    expected_keys = (
        _QUEUE_V1_KEYS if schema == SCHEMA_V1 else
        _QUEUE_V2_KEYS if schema == SCHEMA_V2 else None
    )
    if expected_keys is None or set(authorization) != expected_keys:
        raise ValueError("autorização de migração da fila tem schema inválido")
    canonical_root = _canonical_root(root)
    target_path = pathlib.PurePosixPath(target_rel_path)
    if (target_path.parent != pathlib.PurePosixPath("data/editorial/v2_pages") or
            not isinstance(portfolio_rel_path, str) or
            _PORTFOLIO.fullmatch(portfolio_rel_path) is None):
        raise ValueError("alvo de migração não coincide com o shard da fila")
    catalog = load_catalog(canonical_root)
    record = catalog.migrations.get(target_path.name)
    if (record is None or
            target_path.name != authorization.get("target_shard") or
            portfolio_rel_path != record.get("portfolio_path") or
            authorization.get("registry_sha256") != catalog.registry_sha256):
        raise ValueError("registro de migração não coincide com a fila")
    portfolio = queue.read_regular_file_snapshot(
        canonical_root / portfolio_rel_path, max_bytes=MAX_PORTFOLIO_BYTES)
    if portfolio.digest != record.get("portfolio_sha256"):
        raise ValueError("portfolio mudou depois da fila")
    selected = _select_portfolio_intents(
        portfolio.payload, portfolio_rel_path, families, skip, take,
        expected_n, intent_ids)
    if selected != list(expected_intents):
        raise ValueError("slice vivo do portfolio não coincide com a migração")
    expected_authorization = {
        "schema_version": record["schema_version"],
        "migration_id": record["migration_id"],
        "target_shard": record["target_shard"],
        "source_shard_sha256": record["source_shard_sha256"],
        "source_intent_ids": list(record["source_intent_ids"]),
        "replacement_intent_ids": list(record["replacement_intent_ids"]),
        "portfolio_families": list(record["portfolio_families"]),
        "portfolio_skip": record["portfolio_skip"],
        "portfolio_take": record["portfolio_take"],
        "portfolio_n": record["portfolio_n"],
        "archive_path": record["archive_path"],
        "archive_sha256": record["archive_sha256"],
        "registry_sha256": catalog.registry_sha256,
    }
    if schema == SCHEMA_V2:
        expected_authorization.update({
            "portfolio_intent_ids": list(record["portfolio_intent_ids"]),
            "portfolio_path": record["portfolio_path"],
            "portfolio_sha256": record["portfolio_sha256"],
        })
    if (dict(authorization) != expected_authorization or
            record["replacement_intent_ids"] != list(expected_intents) or
            record["portfolio_families"] != list(families) or
            record["portfolio_skip"] != skip or
            record["portfolio_take"] != take or
            record["portfolio_n"] != expected_n):
        raise ValueError("autorização de migração não autentica o snapshot pós-CAS")
    _verify_catalog_dependencies(canonical_root, catalog)
    if queue.snapshot_sha256(
            canonical_root / portfolio_rel_path,
            max_bytes=MAX_PORTFOLIO_BYTES) != portfolio.digest:
        raise queue.CASMismatch("portfolio mudou durante verificação pós-CAS")
    dependencies = dict(catalog.dependency_sha256)
    dependencies[portfolio_rel_path] = portfolio.digest
    return dependencies


def verify_queue_identity(
    root: pathlib.Path | str,
    migration_id: str,
    target_rel_path: str,
    target_sha256: str,
    portfolio_rel_path: str,
    portfolio_sha256: str,
    registry_sha256: str,
    archive_sha256: str,
    families: Sequence[str],
    skip: int,
    take: int,
    expected_n: int,
    intent_ids: Sequence[str] | None = None,
) -> None:
    """Preflight compacto para o comando textual do workflow.

    Os campos simples evitam serializar um objeto JSON dentro de várias
    camadas de quoting do shell. A autorização completa é reconstruída do
    registro autenticado e comparada aos hashes imutáveis embutidos na fila.
    """
    canonical_root = _canonical_root(root)
    catalog = load_catalog(canonical_root)
    target_path = pathlib.PurePosixPath(target_rel_path)
    if (target_path.parent != pathlib.PurePosixPath("data/editorial/v2_pages") or
            not isinstance(migration_id, str) or
            _MIGRATION_ID.fullmatch(migration_id) is None or
            not isinstance(portfolio_rel_path, str) or
            _PORTFOLIO.fullmatch(portfolio_rel_path) is None or
            any(not isinstance(digest, str) or
                _SHA256.fullmatch(digest) is None for digest in (
                    target_sha256, portfolio_sha256,
                    registry_sha256, archive_sha256))):
        raise ValueError("identidade compacta de migração inválida")
    record = catalog.migrations.get(target_path.name)
    if record is not None:
        schema = record.get("schema_version")
        if schema == SCHEMA_V1:
            if intent_ids is not None:
                raise ValueError(
                    "migração v1 não autentica intent_ids pinados")
        elif schema == SCHEMA_V2:
            if (not isinstance(intent_ids, list) or
                    list(intent_ids) != record.get("portfolio_intent_ids")):
                raise ValueError(
                    "migração v2 não coincide com intent_ids pinados")
        else:
            raise ValueError("registro de migração tem schema inválido")
    if (record is None or record.get("migration_id") != migration_id or
            record.get("portfolio_path") != portfolio_rel_path or
            catalog.registry_sha256 != registry_sha256 or
            record.get("archive_sha256") != archive_sha256 or
            record.get("portfolio_families") != list(families) or
            record.get("portfolio_skip") != skip or
            record.get("portfolio_take") != take or
            record.get("portfolio_n") != expected_n):
        raise ValueError("registro de migração não coincide com a fila")
    target = queue.read_regular_file_snapshot(
        canonical_root / target_rel_path, max_bytes=MAX_TARGET_BYTES)
    portfolio = queue.read_regular_file_snapshot(
        canonical_root / portfolio_rel_path, max_bytes=MAX_PORTFOLIO_BYTES)
    if target.digest != target_sha256 or portfolio.digest != portfolio_sha256:
        raise ValueError("preimagem ou portfolio mudou depois da fila")
    family_order = _canonical_list(list(families), _FAMILY, "families da fila")
    if (type(skip) is not int or skip < 0 or type(take) is not int or take < 0 or
            type(expected_n) is not int or expected_n < 1 or
            (take > 0 and (len(family_order) != 1 or
                           intent_ids is not None)) or
            (take == 0 and (
                skip != 0 or
                not isinstance(intent_ids, list) or
                len(intent_ids) != expected_n or
                any(not isinstance(intent_id, str) or
                    _INTENT.fullmatch(intent_id) is None
                    for intent_id in intent_ids) or
                len(set(intent_ids)) != len(intent_ids)))):
        raise ValueError("seletor de portfolio da fila é inválido")
    by_family: dict[str, list[str]] = {}
    family_by_intent: dict[str, str] = {}
    for line_number, row in enumerate(
            _decode_jsonl(portfolio.payload, portfolio_rel_path), 1):
        family = row.get("family")
        intent_id = row.get("intent_id")
        if (not isinstance(family, str) or _FAMILY.fullmatch(family) is None or
                not isinstance(intent_id, str) or
                _INTENT.fullmatch(intent_id) is None or
                intent_id in family_by_intent):
            raise ValueError(
                f"portfolio não canônico em {portfolio_rel_path}:{line_number}")
        by_family.setdefault(family, []).append(intent_id)
        family_by_intent[intent_id] = family
    if take > 0:
        selected = by_family.get(family_order[0], [])[skip:skip + take]
    else:
        if not isinstance(intent_ids, list):
            raise ValueError("seletor pinado exige intent_ids exatos")
        allowed_families = set(family_order)
        selected = []
        for intent_id in intent_ids:
            owner_family = family_by_intent.get(intent_id)
            if owner_family is None:
                raise ValueError(
                    f"intent_id pinado não existe no portfolio: {intent_id}")
            if owner_family not in allowed_families:
                raise ValueError(
                    "intent_id pinado não pertence às families da migração: "
                    f"{intent_id}: {owner_family}")
            selected.append(intent_id)
        observed_family_runs: list[str] = []
        for intent_id in selected:
            owner_family = family_by_intent[intent_id]
            if (not observed_family_runs or
                    observed_family_runs[-1] != owner_family):
                observed_family_runs.append(owner_family)
        if observed_family_runs != family_order:
            raise ValueError(
                "ordem integral dos intent_ids não coincide com as families "
                "da migração")
    if (len(selected) != expected_n or
            selected != record["replacement_intent_ids"]):
        raise ValueError(
            "slice vivo do portfolio não coincide com a migração da fila")
    authorization = queue_authorization(
        catalog,
        target_path.name,
        target.payload,
        target.digest,
        portfolio_rel_path,
        portfolio.payload,
        portfolio.digest,
        record["replacement_intent_ids"],
        families,
        skip,
        take,
        expected_n,
        intent_ids,
    )
    if (authorization is None or
            authorization["source_shard_sha256"] != target_sha256 or
            authorization["registry_sha256"] != registry_sha256 or
            authorization["archive_sha256"] != archive_sha256):
        raise ValueError("migração não autoriza a preimagem da fila")
    _verify_catalog_dependencies(canonical_root, catalog)
    if (queue.snapshot_sha256(
            canonical_root / target_rel_path,
            max_bytes=MAX_TARGET_BYTES) != target.digest or
            queue.snapshot_sha256(
                canonical_root / portfolio_rel_path,
                max_bytes=MAX_PORTFOLIO_BYTES) !=
            portfolio.digest):
        raise queue.CASMismatch(
            "preimagem ou portfolio mudou durante preflight de migração")


def build_archive_payload(
    migration_id: str,
    target_shard: str,
    source_payload: bytes,
    source_intent_ids: Sequence[str],
    replacement_intent_ids: Sequence[str],
    portfolio_path: str,
    portfolio_sha256: str,
    checked_at: str,
) -> bytes:
    """Monta o archive determinístico usado por produtores one-shot testáveis."""
    source_sha = _digest(source_payload)
    source_rows = _decode_jsonl(source_payload, target_shard)
    if [row.get("intent_id") for row in source_rows] != list(source_intent_ids):
        raise ValueError("source_intent_ids não coincide com a preimagem")
    if len(source_intent_ids) != len(replacement_intent_ids):
        raise ValueError("listas de migração não são bijetivas")
    original_lines = source_payload[:-1].decode("utf-8").split("\n")
    rows: list[dict[str, Any]] = []
    for index, (source_id, replacement_id, original) in enumerate(zip(
            source_intent_ids, replacement_intent_ids, original_lines), 1):
        rows.append({
            "schema_version": 1,
            "record_type": ARCHIVE_RECORD_TYPE,
            "migration_id": migration_id,
            "source_shard": target_shard,
            "source_line": index,
            "source_shard_sha256": source_sha,
            "source_record_sha256": _digest(original.encode("utf-8")),
            "source_intent_id": source_id,
            "replacement_intent_id": replacement_id,
            "original_line": original,
            "portfolio_path": portfolio_path,
            "portfolio_sha256": portfolio_sha256,
            "checked_at": checked_at,
            **_PUBLIC_CLOSED,
        })
    return ("\n".join(json.dumps(
        row, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ) for row in rows) + "\n").encode("utf-8")


def build_registry_record(
    migration_id: str,
    target_shard: str,
    source_payload: bytes,
    source_intent_ids: Sequence[str],
    replacement_intent_ids: Sequence[str],
    portfolio_path: str,
    portfolio_sha256: str,
    archive_path: str,
    archive_payload: bytes,
    checked_at: str,
    portfolio_families: Sequence[str],
    portfolio_skip: int,
    portfolio_take: int,
    portfolio_n: int,
    portfolio_intent_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    if portfolio_intent_ids is None:
        if portfolio_take == 0:
            raise ValueError(
                "migração v1 não pode representar seletor take==0 pinado")
        schema = SCHEMA_V1
    else:
        if (not isinstance(portfolio_intent_ids, list) or
                portfolio_take != 0 or portfolio_skip != 0 or
                list(portfolio_intent_ids) != list(replacement_intent_ids) or
                len(portfolio_intent_ids) != portfolio_n or
                any(not isinstance(intent_id, str) or
                    _INTENT.fullmatch(intent_id) is None
                    for intent_id in portfolio_intent_ids) or
                len(set(portfolio_intent_ids)) != len(portfolio_intent_ids)):
            raise ValueError(
                "migração v2 exige portfolio_intent_ids pinados exatos")
        schema = SCHEMA_V2
    record = {
        "schema_version": schema,
        "migration_id": migration_id,
        "target_shard": target_shard,
        "source_shard_sha256": _digest(source_payload),
        "source_intent_ids": list(source_intent_ids),
        "replacement_intent_ids": list(replacement_intent_ids),
        "portfolio_families": list(portfolio_families),
        "portfolio_skip": portfolio_skip,
        "portfolio_take": portfolio_take,
        "portfolio_n": portfolio_n,
        "portfolio_path": portfolio_path,
        "portfolio_sha256": portfolio_sha256,
        "archive_path": archive_path,
        "archive_sha256": _digest(archive_payload),
        "checked_at": checked_at,
        **_PUBLIC_CLOSED,
    }
    if schema == SCHEMA_V2:
        record["portfolio_intent_ids"] = list(portfolio_intent_ids)
    return record
