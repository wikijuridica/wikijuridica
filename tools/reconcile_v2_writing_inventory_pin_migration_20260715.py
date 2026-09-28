#!/usr/bin/env python3
"""Reconcilia, sem retrofabricar, a migração de pins da fila de escrita v2.

O recibo one-shot de ``migrate_v2_writing_inventory_pins_20260715`` nunca foi
gravado.  As preimagens foram preservadas, mas os runtimes ativos evoluíram
antes da transação.  Portanto, copiar hashes atuais para um recibo antigo
seria um falso histórico.

Este sucessor separa quatro provas:

* o bundle de preimagens imutáveis e seu commit de introdução;
* a transformação pura do inventário 667 -> 737, recomposta dos bytes
  arquivados e dos portfólios pinados;
* a fila atual, recomposta no epoch vivo (estoque, semântica, fontes e
  migrações) com o runtime atual;
* a linhagem Git exata de todo input e output vivo.

``--check`` é sempre read-only. ``--apply-workflows`` instala somente as três
filas sob CAS; elas precisam ser commitadas antes de ``--apply-receipt`` criar
o recibo 0644/NOREPLACE. Nenhum modo altera preimagens, estoque ou publicação.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import datetime
import errno
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from tools import generate_v2_review_queue as queue
from tools import migrate_v2_writing_inventory_pins_20260715 as migration
from tools import v2_portfolio_intent_migrations as portfolio_migrations


ROOT = _IMPORT_ROOT
TOOL_REL = "tools/reconcile_v2_writing_inventory_pin_migration_20260715.py"
TEST_REL = (
    "tools/test_reconcile_v2_writing_inventory_pin_migration_20260715.py"
)
RECEIPT_REL = (
    "data/editorial/"
    "v2_writing_inventory_pin_migration_reconciliation_20260715.json"
)
SCHEMA_VERSION = "v2_writing_inventory_pin_migration_reconciliation_v2"
RECONCILIATION_ID = "writing-inventory-pins-20260715-forward-reconciliation"
HISTORICAL_CHECKED_AT = "2026-07-15"
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
MAX_GIT_OUTPUT_BYTES = 256 * 1024 * 1024
MAX_GIT_HISTORY_COMMITS = 256
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID_RE = re.compile(r"[0-9a-f]{40,64}\Z")
_RECEIPT_KEYS = {
    "schema_version",
    "reconciliation_id",
    "migration_epoch_date",
    "observed_at_utc",
    "validation_date",
    "original_receipt_rel_path",
    "successor_receipt_rel_path",
    "original_receipt_exists",
    "preimages",
    "original_transform",
    "live_outputs",
    "cross_shard_owner_evidence",
    "successor_epoch",
    "git_lineage",
    "anchor_commit",
    "graph_sha256",
    "graph_set_sha256",
    "warnings",
    "blockers",
    "passed",
    "publication_touches",
    "index_policy",
    "render_allowed",
    "sitemap_allowed",
    "publication_allowed",
    "approval",
    "publicly_indexable",
    "proof_sha256",
}

_GRAPH_TOOL_PATHS = (
    TOOL_REL,
    TEST_REL,
    "tools/migrate_v2_writing_inventory_pins_20260715.py",
    "tools/test_migrate_v2_writing_inventory_pins_20260715.py",
    "tools/generate_v2_review_queue.py",
    "tools/v2_portfolio_intent_migrations.py",
    "tools/audit_v2_pages.py",
)


class ReconciliationBlocked(RuntimeError):
    """A prova está incompleta; nenhum efeito deve ser aplicado."""


@dataclass(frozen=True)
class ReconstructedInventory:
    batches: tuple[Mapping[str, Any], ...]
    portfolios: Mapping[str, migration.PortfolioSnapshot]
    aggregate_snapshots: Mapping[str, queue.RegularFileSnapshot]
    counts: Mapping[str, int]
    archived_full_sha256: str
    transformed_archived_full_sha256: str
    transformed_batches_sha256: str


@dataclass(frozen=True)
class SuccessorEpoch:
    outputs: Mapping[str, bytes]
    input_sha256: Mapping[str, str]
    absent_input_paths: tuple[str, ...]
    stock_sha256: Mapping[str, str]
    counts: Mapping[str, int]


@dataclass(frozen=True)
class WorkflowApplyPlan:
    outputs: Mapping[str, bytes]
    expected_outputs: Mapping[str, bytes]
    input_sha256: Mapping[str, str]
    absent_input_paths: tuple[str, ...]
    stock_sha256: Mapping[str, str]
    all_stock_evidence: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ReceiptCreateEffect:
    created: bool
    installed: Any | None
    inode_fd: int | None


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: Any, *, indent: int | None = None) -> bytes:
    if indent is None:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    else:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=indent,
        )
    return (text + "\n").encode("utf-8")


def _mapping_digest(values: Mapping[str, Any]) -> str:
    return _digest(_canonical_json_bytes(dict(sorted(values.items()))))


def _observation_clock(
    observed_at_utc: str | None,
) -> tuple[str, str]:
    if observed_at_utc is None:
        observed_at_utc = datetime.datetime.now(
            datetime.timezone.utc
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.datetime.fromisoformat(
            observed_at_utc.replace("Z", "+00:00")
        )
    except ValueError as error:
        raise ValueError("observed_at_utc não é RFC3339") from error
    if (parsed.tzinfo is None or parsed.utcoffset() != datetime.timedelta(0) or
            parsed.microsecond != 0 or
            observed_at_utc != parsed.isoformat().replace("+00:00", "Z")):
        raise ValueError("observed_at_utc exige UTC canônico em segundos")
    return observed_at_utc, parsed.date().isoformat()


def _block(
    blockers: list[dict[str, Any]],
    code: str,
    detail: str,
    *,
    required_artifact: str | None = None,
) -> None:
    item: dict[str, Any] = {"code": code, "detail": detail}
    if required_artifact is not None:
        item["required_artifact"] = required_artifact
    blockers.append(item)


def _document_components(
    payload: bytes,
    label: str,
) -> tuple[migration.WorkflowDocument, dict[str, Any]]:
    document = migration.parse_workflow_document(payload, label)
    batches_payload = _canonical_json_bytes(list(document.batches))
    return document, {
        "sha256": _digest(payload),
        "bytes": len(payload),
        "prefix_sha256": _digest(document.prefix),
        "batches_sha256": _digest(batches_payload),
        "batch_count": len(document.batches),
        "suffix_sha256": _digest(document.suffix),
    }


def reconstruct_original_inventory(
    root: pathlib.Path,
    bundle: migration.PreimageBundle | None = None,
) -> ReconstructedInventory:
    """Recompõe somente o núcleo determinístico e historicamente provado.

    A saída todo original dependia de um template intermediário cujo SHA-256
    foi pinado pelo one-shot, mas cujos bytes não foram arquivados nem
    commitados.  O inventário, por outro lado, é integralmente reconstruível
    da preimagem full e dos portfólios/aggregates pinados.
    """
    if bundle is None:
        bundle = migration._verify_preimage_manifest(root)
    archive_path = migration.PREIMAGE_ARCHIVE_BY_OUTPUT[migration.FULL_REL]
    archive = bundle.archives[archive_path]
    full_document = migration.parse_workflow_document(
        archive.payload, archive_path
    )
    portfolios = migration._snapshot_portfolios(
        root, full_document.batches
    )
    aggregate_intents, aggregate_snapshots = (
        migration._snapshot_aggregate_intents(root, portfolios)
    )
    batches, counts = migration.pin_and_expand_inventory(
        full_document.batches,
        portfolios,
        aggregate_intents=aggregate_intents,
    )
    expected_core_counts = {
        "batches_before": migration.EXPECTED_BATCHES_BEFORE,
        "batches_after": migration.EXPECTED_BATCHES_AFTER,
        "portfolio_intents": migration.EXPECTED_PORTFOLIO_INTENTS,
        "take_zero_batches": migration.EXPECTED_TAKE_ZERO_BATCHES,
        "aggregate_batches": migration.EXPECTED_AGGREGATE_BATCHES,
        "retired_batches": migration.EXPECTED_RETIRED_BATCHES,
        "adjusted_batches": migration.EXPECTED_ADJUSTED_BATCHES,
        "new_batches": migration.EXPECTED_NEW_BATCHES,
        "new_intents": migration.EXPECTED_NEW_INTENTS,
    }
    if dict(counts) != expected_core_counts:
        raise ValueError(
            "transformação pura do inventário mudou: "
            f"actual={dict(counts)!r} expected={expected_core_counts!r}"
        )
    transformed = full_document.encode(batches)
    return ReconstructedInventory(
        batches=tuple(batches),
        portfolios=portfolios,
        aggregate_snapshots=aggregate_snapshots,
        counts=dict(counts),
        archived_full_sha256=archive.digest,
        transformed_archived_full_sha256=_digest(transformed),
        transformed_batches_sha256=_digest(
            _canonical_json_bytes(list(batches))
        ),
    )


def reconstruct_current_inventory(
    root: pathlib.Path,
    bundle: migration.PreimageBundle | None = None,
) -> ReconstructedInventory:
    """Constrói o sucessor do estado vivo, sem reescrever a prova histórica.

    O fingerprint agregado do one-shot autentica apenas aquele instante. Seus
    bytes não foram arquivados e, portanto, uma divergência nunca pode ser
    promovida a nova verdade histórica. Para o sucessor, lemos os aggregates
    vivos separadamente, aplicando as mesmas validações fechadas de schema,
    cardinalidade e pertencimento ao owner, mas deliberadamente sem comparar
    com ``EXPECTED_AGGREGATE_SET_SHA256``.
    """
    if bundle is None:
        bundle = migration._verify_preimage_manifest(root)
    archive_path = migration.PREIMAGE_ARCHIVE_BY_OUTPUT[migration.FULL_REL]
    archive = bundle.archives[archive_path]
    full_document = migration.parse_workflow_document(
        archive.payload, archive_path
    )
    portfolios = migration._snapshot_portfolios(root, full_document.batches)
    aggregate_intents, aggregate_snapshots = (
        _snapshot_current_aggregate_intents(root, portfolios)
    )
    batches, counts = migration.pin_and_expand_inventory(
        full_document.batches, portfolios,
        aggregate_intents=aggregate_intents,
    )
    transformed = full_document.encode(batches)
    return ReconstructedInventory(
        batches=tuple(batches), portfolios=portfolios,
        aggregate_snapshots=aggregate_snapshots, counts=dict(counts),
        archived_full_sha256=archive.digest,
        transformed_archived_full_sha256=_digest(transformed),
        transformed_batches_sha256=_digest(
            _canonical_json_bytes(list(batches))
        ),
    )


def _snapshot_current_aggregate_intents(
    root: pathlib.Path,
    portfolios: Mapping[str, migration.PortfolioSnapshot],
) -> tuple[dict[str, tuple[str, ...]],
           dict[str, queue.RegularFileSnapshot]]:
    expected_counts = {
        "consumidor-d01": 13, "glossario2-d01": 13,
        "glossario2-d02": 13, "glossario2-d03": 13,
        "glossario2-d04": 13, "glossario2-d05": 8,
        "seguros-d01": 13, "tributario-d02": 13,
    }
    snapshots: dict[str, queue.RegularFileSnapshot] = {}
    result: dict[str, tuple[str, ...]] = {}
    for slug in migration.AGGREGATE_SHARDS:
        rel_path = f"data/editorial/v2_pages/{slug}.jsonl"
        snapshot = queue.read_regular_file_snapshot(
            root / rel_path, max_bytes=migration.MAX_STOCK_BYTES
        )
        records, _ = migration._decode_target(rel_path, snapshot)
        intent_ids = tuple(record.get("intent_id") for record in records)
        portfolio = portfolios[
            f"data/editorial/portfolio_v2/{slug.split('-d', 1)[0]}.jsonl"
        ]
        if (len(intent_ids) != expected_counts[slug] or
                len(intent_ids) != len(set(intent_ids)) or
                any("skipped" in record for record in records) or
                any(not isinstance(intent_id, str) or
                    migration._INTENT.fullmatch(intent_id) is None or
                    intent_id not in portfolio.family_by_intent
                    for intent_id in intent_ids)):
            raise ValueError(f"{rel_path}: aggregate vivo não é canônico")
        result[slug] = intent_ids
        snapshots[rel_path] = snapshot
    return result, snapshots


def _read_live_outputs(
    root: pathlib.Path,
) -> tuple[
    dict[str, queue.RegularFileSnapshot],
    dict[str, migration.WorkflowDocument],
    dict[str, dict[str, Any]],
]:
    snapshots: dict[str, queue.RegularFileSnapshot] = {}
    documents: dict[str, migration.WorkflowDocument] = {}
    components: dict[str, dict[str, Any]] = {}
    for rel_path in sorted(migration._OUTPUT_PATHS):
        snapshot = migration._read_canonical_0644_artifact(
            root,
            rel_path,
            max_bytes=migration.MAX_WORKFLOW_BYTES,
        )
        document, evidence = _document_components(
            snapshot.payload, rel_path
        )
        snapshots[rel_path] = snapshot
        documents[rel_path] = document
        components[rel_path] = evidence
    return snapshots, documents, components


def _snapshot_current_input(
    root: pathlib.Path,
    rel_path: str,
    *,
    max_bytes: int,
) -> queue.RegularFileSnapshot:
    return migration._read_canonical_0644_artifact(
        root, rel_path, max_bytes=max_bytes
    )


def build_successor_epoch(
    root: pathlib.Path,
    reconstructed: ReconstructedInventory,
    live_documents: Mapping[str, migration.WorkflowDocument],
) -> SuccessorEpoch:
    """Recalcula as três saídas contra o epoch vivo sem aceitar seus hashes.

    O ``full`` preserva prefixo/sufixo runtime vivos, mas troca a lista pelo
    resultado puro reconstruído.  ``todo`` e ``todo-sem-telecom`` são
    renderizados novamente a partir do template vivo e da classificação dos
    snapshots atuais.  Assim, nenhum output é aceito porque declarou o próprio
    hash.
    """
    template = _snapshot_current_input(
        root,
        migration.TEMPLATE_REL,
        max_bytes=migration.MAX_WORKFLOW_BYTES,
    )
    area_sources = _snapshot_current_input(
        root,
        migration.AREA_SOURCES_REL,
        max_bytes=migration.MAX_WORKFLOW_BYTES,
    )
    source_catalog = _snapshot_current_input(
        root,
        migration.SOURCE_CATALOG_REL,
        max_bytes=migration.MAX_WORKFLOW_BYTES,
    )
    stock, winners, supersession_evidence = migration._snapshot_stock(root)
    semantic_contract = queue.load_writing_semantic_contract(root)
    migration._validate_semantic_contract_epoch(
        root,
        reconstructed.batches,
        reconstructed.portfolios,
        stock,
        semantic_contract,
    )
    migration_catalog = portfolio_migrations.load_catalog(root)
    # A reconciliação durável precisa ser uma função apenas dos inputs que o
    # successor epoch sela. O produtor normal preserva campos não próprios do
    # TODO anterior por conveniência operacional; aqui isso criaria um
    # self-input impossível de reproduzir depois que o próprio TODO fosse
    # substituído. Reconstruímos deliberadamente sem predecessor: todo campo
    # emitido passa a vir do inventário e dos catálogos autenticados abaixo.
    durable_predecessor_todo: tuple[Mapping[str, Any], ...] = ()
    todo = migration.build_queue_items(
        root,
        reconstructed.batches,
        reconstructed.portfolios,
        source_catalog,
        area_sources,
        stock,
        winners,
        migration_catalog,
        semantic_contract,
        durable_predecessor_todo,
    )
    todo_without_telecom = [
        item for item in todo if item["area"] != "telecom_energia"
    ]
    live_full = live_documents[migration.FULL_REL]
    outputs = {
        migration.FULL_REL: live_full.encode(reconstructed.batches),
        migration.TODO_REL: migration._embed_queue(
            template.payload, todo, "writing-mass-todo"
        ),
        migration.TODO_WITHOUT_TELECOM_REL: migration._embed_queue(
            template.payload,
            todo_without_telecom,
            "writing-mass-todo-sem-telecom",
        ),
    }
    portfolio_sha256 = {
        path: snapshot.digest
        for path, snapshot in reconstructed.portfolios.items()
    }
    aggregate_sha256 = {
        path: snapshot.digest
        for path, snapshot in reconstructed.aggregate_snapshots.items()
    }
    stock_sha256 = {
        path: snapshot.digest for path, snapshot in stock.items()
    }
    input_sha256 = migration._merge_dependency_sha256(
        {
            migration.TEMPLATE_REL: template.digest,
            migration.AREA_SOURCES_REL: area_sources.digest,
            migration.SOURCE_CATALOG_REL: source_catalog.digest,
        },
        portfolio_sha256,
        aggregate_sha256,
        dict(migration_catalog.dependency_sha256),
        {
            path: snapshot.digest
            for path, snapshot in supersession_evidence.items()
        },
        {
            migration.SEMANTIC_CONTRACT_REL: semantic_contract.digest,
        },
        semantic_contract.dependency_sha256,
        stock_sha256,
    )
    counts = {
        **dict(reconstructed.counts),
        "complete_batches": len(reconstructed.batches) - len(todo),
        "todo_batches": len(todo),
        "todo_without_telecom_batches": len(todo_without_telecom),
        "semantic_requirements": len(
            semantic_contract.requirement_fingerprints
        ),
        "unresolved_semantic_requirements": len(
            semantic_contract.unresolved_intents
        ),
    }
    return SuccessorEpoch(
        outputs=outputs,
        input_sha256=dict(sorted(input_sha256.items())),
        absent_input_paths=tuple(
            sorted(semantic_contract.absent_dependency_paths)
        ),
        stock_sha256=dict(sorted(stock_sha256.items())),
        counts=counts,
    )


def _cross_shard_owner_evidence(
    root: pathlib.Path,
    reconstructed: ReconstructedInventory,
    *,
    sample_limit: int = 32,
) -> dict[str, Any]:
    expected_owner: dict[str, str] = {}
    for batch in reconstructed.batches:
        portfolio = reconstructed.portfolios[batch["file"]]
        target = f"data/editorial/v2_pages/{batch['slug']}.jsonl"
        for intent_id in migration._select_ids(batch, portfolio):
            previous = expected_owner.get(intent_id)
            if previous is not None:
                raise ValueError(
                    f"inventário reconstruído duplicou {intent_id}: "
                    f"{previous} e {target}"
                )
            expected_owner[intent_id] = target

    semantic_contract = queue.load_writing_semantic_contract(root)
    semantic_baselines = {
        intent_id: semantic_contract.superseded_target_rel_paths[intent_id]
        for intent_id in semantic_contract.unresolved_intents
    }
    actual_paths: dict[str, set[str]] = {}
    classifications: list[dict[str, Any]] = []
    active_rows = 0
    tombstone_rows = 0
    unknown_active: list[dict[str, str]] = []
    for path in migration._stock_paths(root):
        rel_path = path.relative_to(root).as_posix()
        snapshot = queue.read_regular_file_snapshot(
            path, max_bytes=migration.MAX_STOCK_BYTES
        )
        records, _ = migration._decode_target(rel_path, snapshot)
        for row_number, record in enumerate(records, 1):
            intent_id = record.get("intent_id")
            if record.get("skipped"):
                # Tombstones DEC-020 são prova da retirada, não owners vivos.
                tombstone_rows += 1
                classifications.append({
                    "path": rel_path,
                    "row": row_number,
                    "intent_id": intent_id,
                    "class": "tombstone",
                })
                continue
            active_rows += 1
            if not isinstance(intent_id, str) or intent_id not in expected_owner:
                unknown_active.append({
                    "path": rel_path,
                    "row": str(row_number),
                    "intent_id": intent_id if isinstance(intent_id, str) else "",
                })
                classification = "unknown_or_orphan_active"
            else:
                actual_paths.setdefault(intent_id, set()).add(rel_path)
                classification = (
                    "canonical_owner" if rel_path == expected_owner[intent_id]
                    else "known_off_owner"
                )
            classifications.append({
                "path": rel_path,
                "row": row_number,
                "intent_id": intent_id,
                "class": classification,
            })

    semantic_pending = {
        intent_id: {
            "expected_owner": expected_owner[intent_id],
            "superseded_target": semantic_baselines[intent_id],
            "actual_paths": sorted(paths),
        }
        for intent_id, paths in sorted(actual_paths.items())
        if (intent_id in semantic_baselines and
            paths == {semantic_baselines[intent_id]} and
            semantic_baselines[intent_id] != expected_owner[intent_id])
    }
    divergent = {
        intent_id: {
            "expected_owner": expected_owner[intent_id],
            "actual_paths": sorted(paths),
        }
        for intent_id, paths in sorted(actual_paths.items())
        if (any(path != expected_owner[intent_id] for path in paths) and
            intent_id not in semantic_pending)
    }
    for item in classifications:
        if (item["class"] == "known_off_owner" and
                item["intent_id"] in semantic_pending):
            item["class"] = "semantic_pending_owner"
    return {
        "expected_intents": len(expected_owner),
        "expected_owner": dict(sorted(expected_owner.items())),
        "expected_owner_set_sha256": _mapping_digest(expected_owner),
        "observed_intents": len(actual_paths),
        "semantic_pending_intents": len(semantic_pending),
        "semantic_pending": semantic_pending,
        "semantic_pending_set_sha256": _mapping_digest(semantic_pending),
        "cross_shard_intents": len(divergent),
        "cross_shard": divergent,
        "cross_shard_set_sha256": _mapping_digest(divergent),
        "all_stock_rows": len(classifications),
        "active_rows": active_rows,
        "tombstone_rows": tombstone_rows,
        "classified_rows": len(classifications),
        "classification_sha256": _digest(
            _canonical_json_bytes(classifications)
        ),
        "classification": classifications,
        "unknown_or_orphan_active_rows": len(unknown_active),
        "unknown_or_orphan_sample": unknown_active[:sample_limit],
        "sample": [
            {"intent_id": intent_id, **value}
            for intent_id, value in list(divergent.items())[:sample_limit]
        ],
    }


def _trusted_git_binary() -> str:
    candidates = ("/usr/bin/git", "/bin/git")
    for candidate in candidates:
        try:
            info = os.stat(candidate, follow_symlinks=False)
        except FileNotFoundError:
            continue
        if (stat.S_ISREG(info.st_mode) and info.st_uid == 0 and
                not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)):
            return candidate
    raise RuntimeError("binário Git root-owned e não gravável não encontrado")


def _git_env() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "HOME": "/nonexistent",
    }


def _git(
    root: pathlib.Path,
    args: Sequence[str],
    *,
    check: bool = True,
    max_bytes: int = MAX_GIT_OUTPUT_BYTES,
) -> subprocess.CompletedProcess[bytes]:
    command = [
        _trusted_git_binary(),
        "--literal-pathspecs",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.fsmonitor=false",
        "-C", os.path.abspath(os.fspath(root)),
        *args,
    ]
    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_git_env(),
        check=False,
    )
    if len(result.stdout) > max_bytes or len(result.stderr) > 1024 * 1024:
        raise RuntimeError("saída Git excedeu orçamento")
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()[:1000]
        raise RuntimeError(
            f"Git {' '.join(args[:3])} falhou ({result.returncode}): {detail}"
        )
    return result


def _git_with_input(
    root: pathlib.Path,
    args: Sequence[str],
    payload: bytes,
    *,
    max_bytes: int = MAX_GIT_OUTPUT_BYTES,
) -> bytes:
    command = [
        _trusted_git_binary(), "--literal-pathspecs",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.fsmonitor=false",
        "-C", os.path.abspath(os.fspath(root)), *args,
    ]
    result = subprocess.run(
        command, input=payload, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=_git_env(), check=False,
    )
    if (result.returncode != 0 or len(result.stdout) > max_bytes or
            len(result.stderr) > 1024 * 1024):
        detail = result.stderr.decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Git batch falhou ({result.returncode}): {detail}")
    return result.stdout


def _git_anchor_graph(
    root: pathlib.Path,
    anchor_commit: str,
    graph: Mapping[str, str | None],
) -> dict[str, dict[str, Any]]:
    """Autentica todo o grafo com um ls-tree e um cat-file batch."""
    present = sorted(path for path, digest in graph.items() if digest is not None)
    absent = sorted(path for path, digest in graph.items() if digest is None)
    tree = _git(
        root,
        ["ls-tree", "-rz", anchor_commit, "--", *sorted(graph)],
        max_bytes=MAX_GIT_OUTPUT_BYTES,
    ).stdout
    entries: dict[str, tuple[str, str]] = {}
    for row in (row for row in tree.split(b"\0") if row):
        metadata, separator, encoded_path = row.partition(b"\t")
        fields = metadata.split(b" ")
        path = encoded_path.decode("utf-8")
        if (not separator or len(fields) != 3 or
                fields[0] not in {b"100644", b"100755"} or
                fields[1] != b"blob" or path not in graph):
            raise ValueError(f"entrada Git insegura no grafo: {path!r}")
        entries[path] = (fields[2].decode("ascii"), path)
    unexpected_absent = sorted(path for path in absent if path in entries)
    missing_present = sorted(path for path in present if path not in entries)
    if unexpected_absent:
        raise ValueError(
            "grafo Git diverge em presenças/ausências: "
            f"presentes_indevidos={unexpected_absent[:8]} "
            f"ausentes_indevidos={missing_present[:8]}"
        )
    oid_paths = sorted((oid, path) for path, (oid, _) in entries.items())
    request = b"".join(oid.encode("ascii") + b"\n" for oid, _ in oid_paths)
    response = _git_with_input(root, ["cat-file", "--batch"], request)
    offset = 0
    evidence: dict[str, dict[str, Any]] = {}
    for path in missing_present:
        evidence[path] = {
            "git_blob_oid": None,
            "sha256": None,
            "matches_graph": False,
            "reason": "path_absent_from_anchor",
        }
    for expected_oid, path in oid_paths:
        end = response.find(b"\n", offset)
        if end < 0:
            raise RuntimeError("resposta cat-file batch truncada")
        header = response[offset:end].decode("ascii").split(" ")
        if (len(header) != 3 or header[0] != expected_oid or
                header[1] != "blob" or not header[2].isdigit()):
            raise ValueError(f"header cat-file inválido para {path}")
        size = int(header[2])
        start = end + 1
        payload = response[start:start + size]
        if len(payload) != size or response[start + size:start + size + 1] != b"\n":
            raise RuntimeError(f"blob batch truncado: {path}")
        offset = start + size + 1
        actual = _digest(payload)
        evidence[path] = {
            "git_blob_oid": expected_oid,
            "sha256": actual,
            "matches_graph": actual == graph[path],
        }
    if offset != len(response):
        raise RuntimeError("resposta cat-file batch contém cauda")
    return evidence


def _git_head(root: pathlib.Path) -> str:
    raw = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"],
               max_bytes=4096).stdout.strip().decode("ascii")
    if GIT_OID_RE.fullmatch(raw) is None:
        raise ValueError("HEAD Git não é OID canônico")
    return raw


def _git_tree_blob(
    root: pathlib.Path,
    commit: str,
    rel_path: str,
) -> tuple[str, bytes] | None:
    pure = pathlib.PurePosixPath(rel_path)
    if (pure.is_absolute() or pure.as_posix() != rel_path or
            ".." in pure.parts):
        raise ValueError(f"path Git inseguro: {rel_path!r}")
    result = _git(
        root,
        ["ls-tree", "-z", commit, "--", rel_path],
        check=False,
        max_bytes=64 * 1024,
    )
    if result.returncode != 0 or not result.stdout:
        return None
    rows = result.stdout.split(b"\0")
    rows = [row for row in rows if row]
    if len(rows) != 1:
        raise ValueError(f"Git tree ambígua para {rel_path}")
    metadata, separator, encoded_path = rows[0].partition(b"\t")
    fields = metadata.split(b" ")
    if (not separator or encoded_path.decode("utf-8") != rel_path or
            len(fields) != 3 or fields[0] != b"100644" or
            fields[1] != b"blob"):
        raise ValueError(f"Git tree mode/tipo inseguro para {rel_path}")
    oid = fields[2].decode("ascii")
    if GIT_OID_RE.fullmatch(oid) is None:
        raise ValueError(f"Git blob OID inválido para {rel_path}")
    raw_size = _git(
        root, ["cat-file", "-s", oid], max_bytes=4096
    ).stdout.strip().decode("ascii")
    if not raw_size.isdigit() or int(raw_size) > MAX_GIT_OUTPUT_BYTES:
        raise RuntimeError(f"Git blob excede orçamento: {rel_path}")
    payload = _git(
        root,
        ["cat-file", "blob", oid],
        max_bytes=int(raw_size) + 1,
    ).stdout
    if len(payload) != int(raw_size):
        raise RuntimeError(f"Git blob truncado: {rel_path}")
    return oid, payload


def _git_head_path_evidence(
    root: pathlib.Path,
    head: str,
    rel_path: str,
    live_payload: bytes,
) -> dict[str, Any]:
    blob = _git_tree_blob(root, head, rel_path)
    if blob is None:
        return {
            "path": rel_path,
            "anchored": False,
            "reason": "path_absent_from_head",
            "live_sha256": _digest(live_payload),
        }
    oid, payload = blob
    return {
        "path": rel_path,
        "anchored": payload == live_payload,
        "reason": "exact_head_blob" if payload == live_payload else
                  "worktree_differs_from_head_blob",
        "git_blob_oid": oid,
        "git_blob_sha256": _digest(payload),
        "live_sha256": _digest(live_payload),
    }


def _introduction_commit(
    root: pathlib.Path,
    rel_paths: Iterable[str],
) -> str:
    commits: set[str] = set()
    for rel_path in sorted(set(rel_paths)):
        result = _git(
            root,
            [
                "log", "-n", "2", "--diff-filter=A", "--format=%H",
                "--", rel_path,
            ],
            max_bytes=64 * 1024,
        )
        rows = [row for row in result.stdout.decode("ascii").splitlines()
                if row]
        if len(rows) != 1 or GIT_OID_RE.fullmatch(rows[0]) is None:
            raise ValueError(
                f"preimage sem commit único de introdução: {rel_path}"
            )
        commits.add(rows[0])
    if len(commits) != 1:
        raise ValueError(
            f"bundle de preimages foi introduzido em commits distintos: "
            f"{sorted(commits)}"
        )
    return next(iter(commits))


def _history_contains_sha256(
    root: pathlib.Path,
    rel_path: str,
    expected_sha256: str,
) -> tuple[str, ...]:
    if SHA256_RE.fullmatch(expected_sha256) is None:
        raise ValueError("SHA-256 histórico inválido")
    result = _git(
        root,
        [
            "log", "--all", "-n", str(MAX_GIT_HISTORY_COMMITS + 1),
            "--format=%H", "--", rel_path,
        ],
        max_bytes=256 * 1024,
    )
    commits = [row for row in result.stdout.decode("ascii").splitlines()
               if row]
    if len(commits) > MAX_GIT_HISTORY_COMMITS:
        raise RuntimeError("histórico Git excede teto de 256 commits")
    found: list[str] = []
    seen_blobs: set[str] = set()
    for commit in commits:
        blob = _git_tree_blob(root, commit, rel_path)
        if blob is None:
            continue
        oid, payload = blob
        if oid in seen_blobs:
            continue
        seen_blobs.add(oid)
        if _digest(payload) == expected_sha256:
            found.append(commit)
    return tuple(found)


def _read_epoch_path(root: pathlib.Path, rel_path: str) -> bytes:
    max_bytes = migration._dependency_max_bytes(rel_path)
    snapshot = queue.read_regular_file_snapshot(
        root / rel_path, max_bytes=max_bytes
    )
    return snapshot.payload


def _receipt_snapshot(
    root: pathlib.Path,
    *,
    missing_ok: bool,
) -> queue.RegularFileSnapshot | None:
    try:
        directory_fd, name, absolute = queue._open_parent_directory(
            root / RECEIPT_REL
        )
    except FileNotFoundError:
        if missing_ok:
            return None
        raise
    try:
        snapshot = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=missing_ok,
            max_bytes=MAX_RECEIPT_BYTES,
        )
        if snapshot is None:
            return None
        if snapshot.mode != 0o644 or snapshot.nlink != 1:
            raise RuntimeError(
                f"recibo sucessor exige 0644/nlink1: {absolute}"
            )
        return queue.RegularFileSnapshot(snapshot.payload, snapshot.digest)
    finally:
        os.close(directory_fd)


def _validate_receipt_anchor(
    root: pathlib.Path,
    value: Mapping[str, Any],
    *,
    receipt_payload: bytes | None = None,
) -> None:
    anchor = value["anchor_commit"]
    head = _git_head(root)
    if _git(
        root, ["merge-base", "--is-ancestor", anchor, head],
        check=False, max_bytes=4096,
    ).returncode != 0:
        raise ValueError("anchor_commit do receipt não é ancestral do HEAD")
    evidence = _git_anchor_graph(root, anchor, value["graph_sha256"])
    mismatches = sorted(
        path for path, item in evidence.items() if not item["matches_graph"]
    )
    if mismatches:
        raise ValueError(f"blobs do grafo divergiram no anchor: {mismatches[:8]}")
    try:
        current_evidence = _git_anchor_graph(
            root, head, value["graph_sha256"]
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError(
            f"HEAD descendente alterou blobs/ausências do grafo: {error}"
        ) from error
    current_mismatches = sorted(
        path for path, item in current_evidence.items()
        if not item["matches_graph"]
    )
    if current_mismatches:
        raise ValueError(
            "HEAD descendente alterou blobs/ausências do grafo: "
            f"{current_mismatches[:8]}"
        )
    if receipt_payload is not None:
        committed = _git_tree_blob(root, head, RECEIPT_REL)
        if committed is None or committed[1] != receipt_payload:
            raise ValueError(
                "receipt sucessor não é blob exato do HEAD descendente"
            )


_ROOT_STABLE_RECEIPT_KEYS = frozenset({
    "schema_version", "reconciliation_id", "migration_epoch_date",
    "original_receipt_rel_path", "successor_receipt_rel_path",
    "original_receipt_exists", "preimages", "original_transform",
    "live_outputs", "cross_shard_owner_evidence", "successor_epoch",
    "graph_sha256", "graph_set_sha256", "warnings", "publication_touches",
    "index_policy", "render_allowed", "sitemap_allowed",
    "publication_allowed", "approval", "publicly_indexable",
})


def _validate_receipt_against_live_report(
    receipt: Mapping[str, Any],
    live_report: Mapping[str, Any],
) -> None:
    """Liga identidades auto-consistentes aos bytes recomputados do root."""
    if any(key not in receipt or key not in live_report
           for key in _ROOT_STABLE_RECEIPT_KEYS):
        raise ValueError("receipt/live report perdeu seção root-aware estável")
    divergent = sorted(
        key for key in _ROOT_STABLE_RECEIPT_KEYS
        if receipt[key] != live_report[key]
    )
    if divergent:
        raise ValueError(
            "receipt diverge da recomputação root-aware nas seções estáveis: "
            f"{divergent}"
        )


def inspect(
    root: pathlib.Path = ROOT,
    *,
    observed_at_utc: str | None = None,
    require_terminal_receipt: bool = True,
) -> dict[str, Any]:
    root = pathlib.Path(os.path.abspath(os.fspath(root)))
    observed_at_utc, validation_date = _observation_clock(observed_at_utc)
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "reconciliation_id": RECONCILIATION_ID,
        "migration_epoch_date": HISTORICAL_CHECKED_AT,
        "observed_at_utc": observed_at_utc,
        "validation_date": validation_date,
        "original_receipt_rel_path": migration.RECEIPT_REL,
        "successor_receipt_rel_path": RECEIPT_REL,
    }

    original_receipt_exists = os.path.lexists(root / migration.RECEIPT_REL)
    report["original_receipt_exists"] = original_receipt_exists
    if original_receipt_exists:
        _block(
            blockers,
            "original_receipt_unexpectedly_present",
            "o sucessor recusa coexistir com recibo one-shot não autenticado",
            required_artifact=(
                "verificação explícita do receipt original antes da "
                "reconciliação"
            ),
        )

    existing_successor: queue.RegularFileSnapshot | None = None
    try:
        existing_successor = _receipt_snapshot(root, missing_ok=True)
    except Exception as error:
        _block(
            blockers,
            "successor_receipt_unsafe",
            str(error),
            required_artifact="receipt sucessor regular 0644/nlink1",
        )

    try:
        bundle = migration._verify_preimage_manifest(root)
        preimage_sha256 = {
            path: snapshot.digest
            for path, snapshot in sorted(bundle.archives.items())
        }
        preimage_entries = migration._preimage_entries(bundle.archives)
        report["preimages"] = {
            "manifest_rel_path": migration.PREIMAGE_MANIFEST_REL,
            "manifest_sha256": bundle.manifest.digest,
            "archive_sha256": preimage_sha256,
            "entries": preimage_entries,
            "preimage_set_sha256": migration._preimage_set_digest(
                preimage_entries
            ),
        }
    except Exception as error:
        bundle = None
        _block(
            blockers,
            "immutable_preimage_bundle_invalid",
            str(error),
            required_artifact=migration.PREIMAGE_MANIFEST_REL,
        )

    reconstructed: ReconstructedInventory | None = None
    current_inventory: ReconstructedInventory | None = None
    if bundle is not None:
        try:
            reconstructed = reconstruct_original_inventory(root, bundle)
            report["original_transform"] = {
                "inventory_reconstructable": True,
                "expected_aggregate_set_sha256": (
                    migration.EXPECTED_AGGREGATE_SET_SHA256
                ),
                "historical_reconstruction_error": None,
                "archived_full_sha256": (
                    reconstructed.archived_full_sha256
                ),
                "transformed_archived_full_sha256": (
                    reconstructed.transformed_archived_full_sha256
                ),
                "transformed_batches_sha256": (
                    reconstructed.transformed_batches_sha256
                ),
                "counts": dict(reconstructed.counts),
            }
        except Exception as error:
            archive = bundle.archives[
                migration.PREIMAGE_ARCHIVE_BY_OUTPUT[migration.FULL_REL]
            ]
            report["original_transform"] = {
                "inventory_reconstructable": False,
                "expected_aggregate_set_sha256": (
                    migration.EXPECTED_AGGREGATE_SET_SHA256
                ),
                "historical_reconstruction_error": str(error),
                "archived_full_sha256": archive.digest,
                "transformed_archived_full_sha256": None,
                "transformed_batches_sha256": None,
                "counts": {},
            }
            warnings.append({
                "code": "historical_aggregate_bytes_not_durable",
                "detail": (
                    "o aggregate one-shot "
                    f"{migration.EXPECTED_AGGREGATE_SET_SHA256} não foi "
                    "arquivado; o sucessor não alega que o inventário "
                    "histórico seja reconstruível nem substitui esse hash"
                ),
                "required_artifact": (
                    "elo histórico é irrecuperável; usar somente snapshot "
                    "vivo completo, grafo e anchor do successor"
                ),
            })
        try:
            current_inventory = reconstruct_current_inventory(root, bundle)
        except Exception as error:
            _block(
                blockers, "current_inventory_not_reconstructable", str(error),
                required_artifact="snapshot vivo completo e canônico",
            )

    live_snapshots: dict[str, queue.RegularFileSnapshot] = {}
    live_documents: dict[str, migration.WorkflowDocument] = {}
    try:
        live_snapshots, live_documents, components = _read_live_outputs(root)
        report["live_outputs"] = components
        if current_inventory is not None:
            active_batches = live_documents[migration.FULL_REL].batches
            if list(current_inventory.batches) != active_batches:
                _block(
                    blockers,
                    "live_full_inventory_is_still_preimage",
                    "full ativo não contém o inventário reconstruído 737; "
                    f"active={len(active_batches)} "
                    f"expected={len(current_inventory.batches)}",
                    required_artifact=(
                        "transação sucessora CAS dos três workflows"
                    ),
                )
    except Exception as error:
        _block(
            blockers,
            "live_workflow_snapshot_invalid",
            str(error),
            required_artifact="três workflows regulares 0644 autenticados",
        )

    cross_shard: dict[str, Any] | None = None
    if current_inventory is not None:
        try:
            cross_shard = _cross_shard_owner_evidence(root, current_inventory)
            report["cross_shard_owner_evidence"] = cross_shard
            if cross_shard["cross_shard_intents"]:
                _block(
                    blockers,
                    "cross_shard_owner_lineage_unreconciled",
                    f"{cross_shard['cross_shard_intents']} intents vivem "
                    "fora do owner canônico que o one-shot classificaria",
                    required_artifact=(
                        "plano sucessor que autentique owners rNN e impeça "
                        "reenfileiramento"
                    ),
                )
            if cross_shard["unknown_or_orphan_active_rows"]:
                _block(
                    blockers,
                    "all_stock_contains_unknown_or_orphan_active_rows",
                    f"{cross_shard['unknown_or_orphan_active_rows']} linhas "
                    "ativas do estoque não pertencem ao inventário fechado",
                    required_artifact=(
                        "migração explícita ou owner canônico para 100% das "
                        "linhas ativas"
                    ),
                )
        except Exception as error:
            _block(
                blockers,
                "cross_shard_owner_scan_failed",
                str(error),
                required_artifact="snapshot fechado do estoque v2",
            )

    successor: SuccessorEpoch | None = None
    if current_inventory is not None and live_documents:
        try:
            successor = build_successor_epoch(
                root, current_inventory, live_documents
            )
            expected_output_sha256 = {
                path: _digest(payload)
                for path, payload in sorted(successor.outputs.items())
            }
            report["successor_epoch"] = {
                "input_sha256": dict(successor.input_sha256),
                "input_set_sha256": _mapping_digest(
                    successor.input_sha256
                ),
                "absent_input_paths": list(
                    successor.absent_input_paths
                ),
                "stock_sha256": dict(successor.stock_sha256),
                "stock_set_sha256": _mapping_digest(
                    successor.stock_sha256
                ),
                "expected_output_sha256": expected_output_sha256,
                "counts": dict(successor.counts),
            }
            actual_output_sha256 = {
                path: snapshot.digest
                for path, snapshot in sorted(live_snapshots.items())
            }
            if expected_output_sha256 != actual_output_sha256:
                divergent = sorted(
                    path for path in expected_output_sha256
                    if expected_output_sha256[path] !=
                    actual_output_sha256.get(path)
                )
                _block(
                    blockers,
                    "live_outputs_do_not_match_successor_epoch",
                    f"saídas divergentes do plano recomputado: {divergent}",
                    required_artifact=(
                        "instalação atômica CAS das saídas recomputadas"
                    ),
                )
        except Exception as error:
            _block(
                blockers,
                "successor_epoch_not_reconstructable",
                str(error),
                required_artifact=(
                    "produtor atual que classifique todo o estoque/owners "
                    "semânticos sem falso reenfileiramento"
                ),
            )

    try:
        head = _git_head(root)
        git_evidence: dict[str, Any] = {"head": head}
        preimage_paths = {
            migration.PREIMAGE_MANIFEST_REL,
            *migration._PREIMAGE_ARCHIVE_PATHS,
        }
        introduction = _introduction_commit(root, preimage_paths)
        ancestor = _git(
            root,
            ["merge-base", "--is-ancestor", introduction, head],
            check=False,
            max_bytes=4096,
        ).returncode == 0
        git_evidence["preimage_introduction_commit"] = introduction
        git_evidence["preimage_commit_is_head_ancestor"] = ancestor
        if not ancestor:
            _block(
                blockers,
                "preimage_commit_not_in_head_lineage",
                f"{introduction} não é ancestral de {head}",
            )

        live_payload_by_path: dict[str, bytes] = {}
        if bundle is not None:
            live_payload_by_path[migration.PREIMAGE_MANIFEST_REL] = (
                bundle.manifest.payload
            )
            live_payload_by_path.update({
                path: snapshot.payload
                for path, snapshot in bundle.archives.items()
            })
        live_payload_by_path.update({
            path: snapshot.payload
            for path, snapshot in live_snapshots.items()
        })
        graph_static_paths = {
            migration.TEMPLATE_REL,
            *_GRAPH_TOOL_PATHS,
        }
        for rel_path in sorted(graph_static_paths):
            try:
                snapshot = queue.read_regular_file_snapshot(
                    root / rel_path,
                    max_bytes=migration._dependency_max_bytes(rel_path),
                )
                live_payload_by_path[rel_path] = snapshot.payload
            except Exception as error:
                _block(
                    blockers,
                    "git_lineage_input_unreadable",
                    f"{rel_path}: {error}",
                )
        if successor is not None:
            for rel_path in successor.input_sha256:
                if rel_path in live_payload_by_path:
                    continue
                try:
                    live_payload_by_path[rel_path] = _read_epoch_path(
                        root, rel_path
                    )
                except Exception as error:
                    _block(
                        blockers,
                        "git_lineage_epoch_input_unreadable",
                        f"{rel_path}: {error}",
                    )
        # O grafo continua fechado mesmo quando a recomposição histórica
        # bloqueia: todo estoque, portfólio e input nominal ainda é selado.
        closure_candidates = {
            *migration.EXPECTED_INPUT_SHA256,
            *(
                path.relative_to(root).as_posix()
                for path in migration._stock_paths(root)
            ),
            *migration._portfolio_paths(root),
            portfolio_migrations.REGISTRY_REL_PATH,
            migration.SEMANTIC_CONTRACT_REL,
        }
        closure_absences: set[str] = set()
        try:
            closure_semantic = queue.load_writing_semantic_contract(root)
            closure_candidates.update(closure_semantic.dependency_sha256)
            closure_absences.update(closure_semantic.absent_dependency_paths)
        except Exception as error:
            _block(blockers, "graph_closure_semantic_failed", str(error))
        try:
            closure_migrations = portfolio_migrations.load_catalog(root)
            closure_candidates.update(closure_migrations.dependency_sha256)
        except Exception as error:
            _block(blockers, "graph_closure_migrations_failed", str(error))
        for rel_path in sorted(closure_candidates):
            if rel_path in live_payload_by_path:
                continue
            try:
                live_payload_by_path[rel_path] = _read_epoch_path(
                    root, rel_path
                )
            except Exception as error:
                _block(
                    blockers,
                    "graph_closure_input_unreadable",
                    f"{rel_path}: {error}",
                )
        graph_paths: dict[str, str | None] = {
            path: _digest(payload)
            for path, payload in sorted(live_payload_by_path.items())
        }
        for path in sorted(closure_absences):
            if os.path.lexists(root / path):
                _block(
                    blockers, "declared_absence_is_present",
                    f"dependência semanticamente ausente apareceu: {path}",
                )
            graph_paths[path] = None
        if successor is not None:
            for path, digest in successor.input_sha256.items():
                if graph_paths.get(path) != digest:
                    raise queue.CASMismatch(
                        f"closure perdeu digest do input vivo: {path}"
                    )
            for path, payload in successor.outputs.items():
                if graph_paths.get(path) != _digest(payload):
                    # Antes de --apply-workflows a divergência é blocker, mas
                    # o grafo ainda deve descrever os bytes vivos observados.
                    continue
            for path in successor.absent_input_paths:
                if os.path.lexists(root / path):
                    _block(
                        blockers,
                        "declared_absence_is_present",
                        f"dependência semanticamente ausente apareceu: {path}",
                    )
                graph_paths[path] = None
        graph_paths[migration.RECEIPT_REL] = None
        graph_sha256 = _digest(_canonical_json_bytes(graph_paths))
        report["anchor_commit"] = head
        report["graph_sha256"] = dict(sorted(graph_paths.items()))
        report["graph_set_sha256"] = graph_sha256
        path_evidence = _git_anchor_graph(root, head, graph_paths)
        git_evidence["paths"] = path_evidence
        unanchored = sorted(
            path for path, evidence in path_evidence.items()
            if not evidence["matches_graph"]
        )
        git_evidence["unanchored_paths"] = unanchored
        if unanchored:
            _block(
                blockers,
                "live_epoch_not_anchored_in_head",
                f"{len(unanchored)} paths vivos não são blobs exatos do "
                f"HEAD: {unanchored[:16]}",
                required_artifact=(
                    "commit atômico dos inputs, produtor e três outputs"
                ),
            )
        if bundle is not None:
            for rel_path in sorted(preimage_paths):
                committed = _git_tree_blob(root, introduction, rel_path)
                payload = live_payload_by_path.get(rel_path)
                if committed is None or payload is None or committed[1] != payload:
                    _block(
                        blockers,
                        "preimage_commit_blob_mismatch",
                        f"commit de introdução não autentica {rel_path}",
                    )
        final_head = _git_head(root)
        git_evidence["final_head"] = final_head
        if final_head != head:
            _block(
                blockers,
                "head_changed_during_lineage_check",
                f"HEAD mudou durante inspeção: before={head} after={final_head}",
            )
        drifted_paths: list[str] = []
        for rel_path, payload in sorted(live_payload_by_path.items()):
            try:
                current = queue.read_regular_file_snapshot(
                    root / rel_path,
                    max_bytes=migration._dependency_max_bytes(rel_path),
                )
            except Exception as error:
                _block(
                    blockers,
                    "lineage_final_snapshot_unreadable",
                    f"{rel_path}: {error}",
                )
                continue
            if current.payload != payload or current.digest != _digest(payload):
                drifted_paths.append(rel_path)
        git_evidence["drifted_paths_during_check"] = drifted_paths
        if drifted_paths:
            _block(
                blockers,
                "live_epoch_changed_during_lineage_check",
                f"paths mudaram durante inspeção: {drifted_paths[:16]}",
            )
        appeared_absences = sorted(
            path for path, digest in graph_paths.items()
            if digest is None and os.path.lexists(root / path)
        )
        git_evidence["appeared_absences_during_check"] = appeared_absences
        if appeared_absences:
            _block(
                blockers,
                "graph_absence_changed_during_check",
                f"paths ausentes apareceram: {appeared_absences[:16]}",
            )
        report["git_lineage"] = git_evidence

        expected_template = migration.EXPECTED_INPUT_SHA256[
            migration.TEMPLATE_REL
        ]
        historical_template_commits = _history_contains_sha256(
            root, migration.TEMPLATE_REL, expected_template
        )
        original_transform = report.setdefault("original_transform", {})
        original_transform["original_template_sha256"] = expected_template
        original_transform["original_template_git_commits"] = list(
            historical_template_commits
        )
        original_transform["exact_original_queue_reconstructable"] = bool(
            historical_template_commits
        )
        if not historical_template_commits:
            warnings.append({
                "code": "original_queue_template_not_durable",
                "detail": (
                    f"template {expected_template} não existe no histórico "
                    "Git nem no bundle de preimages; o receipt sucessor não "
                    "alega que o output one-shot original chegou a existir"
                ),
                "required_artifact": (
                    "nenhum artefato retroativo pode corrigir esse elo; a "
                    "prova válida é o plano sucessor recomputado"
                ),
            })
    except Exception as error:
        _block(
            blockers,
            "git_lineage_check_failed",
            str(error),
            required_artifact="repositório Git íntegro com blobs vivos no HEAD",
        )

    report["warnings"] = warnings
    report["blockers"] = blockers
    report["passed"] = not blockers
    report["publication_touches"] = []
    report["index_policy"] = "noindex"
    report["render_allowed"] = False
    report["sitemap_allowed"] = False
    report["publication_allowed"] = False
    report["approval"] = False
    report["publicly_indexable"] = False

    proof_value = {
        key: value for key, value in report.items()
        if key not in {"proof_sha256"}
    }
    report["proof_sha256"] = _digest(_canonical_json_bytes(proof_value))
    if existing_successor is not None:
        try:
            existing_value = queue.decode_json_no_duplicate_keys(
                existing_successor.payload, RECEIPT_REL
            )
            _validate_receipt_value(existing_value)
            _validate_receipt_anchor(
                root, existing_value,
                receipt_payload=(
                    existing_successor.payload
                    if require_terminal_receipt else None
                ),
            )
            _validate_receipt_against_live_report(
                existing_value, report
            )
        except Exception as error:
            _block(
                blockers,
                "successor_receipt_stale_or_divergent",
                str(error),
                required_artifact=(
                    "nova migração datada; receipt create-only não pode ser "
                    "sobrescrito"
                ),
            )
        if blockers:
            report["blockers"] = blockers
            report["passed"] = False
            proof_value = {
                key: value for key, value in report.items()
                if key != "proof_sha256"
            }
            report["proof_sha256"] = _digest(
                _canonical_json_bytes(proof_value)
            )
    return report


def _closed_sha_map(value: Any, label: str) -> Mapping[str, str]:
    if (not isinstance(value, Mapping) or any(
            not isinstance(path, str) or not path or
            not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None
            for path, digest in value.items())):
        raise ValueError(f"schema profundo exige mapa SHA-256 em {label}")
    return value


def _closed_int_map(value: Any, label: str) -> Mapping[str, int]:
    if (not isinstance(value, Mapping) or any(
            not isinstance(key, str) or type(count) is not int or count < 0
            for key, count in value.items())):
        raise ValueError(f"schema profundo exige mapa de contagens em {label}")
    return value


def _validate_receipt_value(value: Mapping[str, Any]) -> None:
    if (set(value) != _RECEIPT_KEYS or
            value.get("schema_version") != SCHEMA_VERSION or
            value.get("reconciliation_id") != RECONCILIATION_ID or
            value.get("migration_epoch_date") != HISTORICAL_CHECKED_AT or
            value.get("original_receipt_rel_path") !=
            migration.RECEIPT_REL or
            value.get("successor_receipt_rel_path") != RECEIPT_REL or
            value.get("original_receipt_exists") is not False or
            value.get("passed") is not True or
            value.get("blockers") != [] or
            value.get("publication_touches") != [] or
            value.get("index_policy") != "noindex" or
            any(value.get(flag) is not False for flag in (
                "render_allowed", "sitemap_allowed", "publication_allowed",
                "approval", "publicly_indexable",
            )) or not isinstance(value.get("proof_sha256"), str) or
            SHA256_RE.fullmatch(value["proof_sha256"]) is None):
        raise ValueError("valor não é receipt sucessor publicamente fechado")
    observed, validation_date = _observation_clock(
        value.get("observed_at_utc")
        if isinstance(value.get("observed_at_utc"), str) else ""
    )
    if (observed != value["observed_at_utc"] or
            validation_date != value.get("validation_date")):
        raise ValueError("datas histórica/viva do receipt divergem")
    anchor = value.get("anchor_commit")
    graph = value.get("graph_sha256")
    lineage = value.get("git_lineage")
    if (not isinstance(anchor, str) or GIT_OID_RE.fullmatch(anchor) is None or
            not isinstance(graph, Mapping) or
            not isinstance(lineage, Mapping)):
        raise ValueError("schema profundo do grafo/lineage é inválido")
    paths = graph
    if (not paths or any(
            not isinstance(path, str) or
            not path or pathlib.PurePosixPath(path).is_absolute() or
            pathlib.PurePosixPath(path).as_posix() != path or
            ".." in pathlib.PurePosixPath(path).parts or
            (digest is not None and
             (not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None))
            for path, digest in paths.items()
        ) or value.get("graph_set_sha256") !=
            _digest(_canonical_json_bytes(dict(sorted(paths.items()))))):
        raise ValueError("schema profundo/digest do grafo é inválido")
    required_graph_paths = {
        migration.RECEIPT_REL,
        migration.PREIMAGE_MANIFEST_REL,
        *migration._PREIMAGE_ARCHIVE_PATHS,
        *migration._OUTPUT_PATHS,
        *_GRAPH_TOOL_PATHS,
    }
    if not required_graph_paths.issubset(paths):
        raise ValueError("grafo não fecha ferramentas, workflows e preimages")
    if paths[migration.RECEIPT_REL] is not None:
        raise ValueError("ausência do receipt original não foi selada")
    preimages = value.get("preimages")
    if (not isinstance(preimages, Mapping) or set(preimages) != {
            "manifest_rel_path", "manifest_sha256", "archive_sha256",
            "entries", "preimage_set_sha256"} or
            preimages.get("manifest_rel_path") !=
            migration.PREIMAGE_MANIFEST_REL):
        raise ValueError("schema profundo de preimages é inválido")
    archives = _closed_sha_map(preimages["archive_sha256"], "preimages")
    entries = preimages.get("entries")
    if (set(archives) != migration._PREIMAGE_ARCHIVE_PATHS or
            not isinstance(entries, Mapping) or
            set(entries) != set(migration.PREIMAGE_ARCHIVE_BY_OUTPUT) or any(
                not isinstance(entry, Mapping) or set(entry) != {
                    "archive_path", "sha256", "bytes", "mode", "nlink"} or
                entry.get("archive_path") !=
                migration.PREIMAGE_ARCHIVE_BY_OUTPUT[active] or
                entry.get("sha256") != archives.get(entry.get("archive_path")) or
                type(entry.get("bytes")) is not int or entry["bytes"] < 0 or
                entry.get("mode") != "0644" or entry.get("nlink") != 1
                for active, entry in entries.items()) or
            any(paths.get(path) != digest for path, digest in archives.items()) or
            paths.get(migration.PREIMAGE_MANIFEST_REL) !=
            preimages.get("manifest_sha256") or
            any(SHA256_RE.fullmatch(str(preimages.get(key))) is None for key in
                ("manifest_sha256", "preimage_set_sha256")) or
            preimages.get("preimage_set_sha256") !=
            migration._preimage_set_digest(entries)):
        raise ValueError("relações digest/graph de preimages divergem")

    outputs = value.get("live_outputs")
    if (not isinstance(outputs, Mapping) or
            set(outputs) != migration._OUTPUT_PATHS):
        raise ValueError("schema profundo de live_outputs é inválido")
    for path, component in outputs.items():
        if (not isinstance(component, Mapping) or set(component) != {
                "sha256", "bytes", "prefix_sha256", "batches_sha256",
                "batch_count", "suffix_sha256"} or
                component.get("sha256") != paths.get(path) or
                type(component.get("bytes")) is not int or
                component["bytes"] < 0 or
                type(component.get("batch_count")) is not int or
                component["batch_count"] < 0 or any(
                    not isinstance(component.get(key), str) or
                    SHA256_RE.fullmatch(component[key]) is None
                    for key in ("sha256", "prefix_sha256", "batches_sha256",
                                "suffix_sha256"))):
            raise ValueError(f"schema/digest do live output diverge: {path}")

    successor = value.get("successor_epoch")
    if (not isinstance(successor, Mapping) or set(successor) != {
            "input_sha256", "input_set_sha256", "absent_input_paths",
            "stock_sha256", "stock_set_sha256", "expected_output_sha256",
            "counts"}):
        raise ValueError("schema profundo de successor_epoch é inválido")
    input_sha = _closed_sha_map(successor["input_sha256"], "successor inputs")
    stock_sha = _closed_sha_map(successor["stock_sha256"], "successor stock")
    expected_outputs = _closed_sha_map(
        successor["expected_output_sha256"], "successor outputs"
    )
    absences = successor["absent_input_paths"]
    if (not input_sha or not stock_sha or
            not isinstance(absences, list) or absences != sorted(set(absences)) or
            any(not isinstance(path, str) or paths.get(path, "present") is not None
                for path in absences) or
            successor.get("input_set_sha256") != _mapping_digest(input_sha) or
            successor.get("stock_set_sha256") != _mapping_digest(stock_sha) or
            set(expected_outputs) != migration._OUTPUT_PATHS or
            any(outputs[path]["sha256"] != digest
                for path, digest in expected_outputs.items()) or
            any(paths.get(path) != digest
                for path, digest in {**input_sha, **stock_sha}.items())):
        raise ValueError("relações digest/count/graph do successor divergem")
    _closed_int_map(successor["counts"], "successor counts")
    successor_counts = successor["counts"]
    expected_successor_count_keys = {
        "batches_before", "batches_after", "portfolio_intents",
        "take_zero_batches", "aggregate_batches", "retired_batches",
        "adjusted_batches", "new_batches", "new_intents",
        "complete_batches", "todo_batches",
        "todo_without_telecom_batches", "semantic_requirements",
        "unresolved_semantic_requirements",
    }
    count_relations = {
        "batches_after": outputs[migration.FULL_REL]["batch_count"],
        "todo_batches": outputs[migration.TODO_REL]["batch_count"],
        "todo_without_telecom_batches": outputs[
            migration.TODO_WITHOUT_TELECOM_REL]["batch_count"],
    }
    if (set(successor_counts) != expected_successor_count_keys or
            any(successor_counts.get(key) != expected
                for key, expected in count_relations.items()) or
            successor_counts["complete_batches"] +
            successor_counts["todo_batches"] !=
            successor_counts["batches_after"] or
            successor_counts["semantic_requirements"] !=
            migration.EXPECTED_SEMANTIC_REQUIREMENTS or
            successor_counts["unresolved_semantic_requirements"] !=
            migration.EXPECTED_UNRESOLVED_SEMANTIC_REQUIREMENTS):
        raise ValueError("contagens successor/live_outputs divergem")

    cross = value.get("cross_shard_owner_evidence")
    cross_keys = {
        "expected_intents", "expected_owner", "expected_owner_set_sha256",
        "observed_intents", "semantic_pending_intents",
        "semantic_pending",
        "semantic_pending_set_sha256", "cross_shard_intents",
        "cross_shard",
        "cross_shard_set_sha256", "all_stock_rows", "active_rows",
        "tombstone_rows", "classified_rows", "classification_sha256",
        "classification",
        "unknown_or_orphan_active_rows", "unknown_or_orphan_sample", "sample",
    }
    if not isinstance(cross, Mapping):
        raise ValueError("receipt não classificou 100% do estoque ativo")
    classification_material = (
        cross.get("classification")
        if isinstance(cross.get("classification"), list) else []
    )
    classes = [
        item.get("class") for item in classification_material
        if isinstance(item, Mapping)
    ]
    known_active_classes = {
        "canonical_owner", "known_off_owner", "semantic_pending_owner"
    }
    known_active_intents = {
        item.get("intent_id") for item in classification_material
        if isinstance(item, Mapping) and item.get("class") in known_active_classes
        and isinstance(item.get("intent_id"), str)
    }
    off_owner_intents = {
        item.get("intent_id") for item in classification_material
        if isinstance(item, Mapping) and item.get("class") == "known_off_owner"
    }
    semantic_pending_intents = {
        item.get("intent_id") for item in classification_material
        if isinstance(item, Mapping) and
        item.get("class") == "semantic_pending_owner"
    }
    expected_owner_material = (
        cross.get("expected_owner")
        if isinstance(cross.get("expected_owner"), Mapping) else {}
    )
    classification_coordinates = [
        (item.get("path"), item.get("row"))
        for item in classification_material if isinstance(item, Mapping)
    ]
    off_owner_paths: dict[str, set[str]] = {}
    pending_paths: dict[str, set[str]] = {}
    for item in classification_material:
        if not isinstance(item, Mapping) or not isinstance(
                item.get("intent_id"), str):
            continue
        if item.get("class") == "known_off_owner":
            off_owner_paths.setdefault(item["intent_id"], set()).add(
                item.get("path"))
        elif item.get("class") == "semantic_pending_owner":
            pending_paths.setdefault(item["intent_id"], set()).add(
                item.get("path"))
    for intent in tuple(off_owner_paths):
        off_owner_paths[intent] = {
            item.get("path") for item in classification_material
            if isinstance(item, Mapping) and
            item.get("intent_id") == intent and
            item.get("class") in known_active_classes
        }
    for intent in tuple(pending_paths):
        pending_paths[intent] = {
            item.get("path") for item in classification_material
            if isinstance(item, Mapping) and
            item.get("intent_id") == intent and
            item.get("class") in known_active_classes
        }
    if (not isinstance(cross, Mapping) or set(cross) != cross_keys or any(
            type(cross.get(key)) is not int or cross[key] < 0 for key in {
                "expected_intents", "observed_intents",
                "semantic_pending_intents", "cross_shard_intents",
                "all_stock_rows", "active_rows", "tombstone_rows",
                "classified_rows", "unknown_or_orphan_active_rows"}) or any(
            not isinstance(cross.get(key), str) or
            SHA256_RE.fullmatch(cross[key]) is None for key in {
                "semantic_pending_set_sha256", "cross_shard_set_sha256",
                "classification_sha256"}) or
            cross.get("sample") != [] or
            cross.get("unknown_or_orphan_sample") != [] or
            not isinstance(cross.get("semantic_pending"), Mapping) or
            not isinstance(cross.get("cross_shard"), Mapping) or
            not isinstance(cross.get("classification"), list) or
            cross["semantic_pending_intents"] !=
            len(cross["semantic_pending"]) or
            cross["semantic_pending_set_sha256"] !=
            _mapping_digest(cross["semantic_pending"]) or
            cross["cross_shard_intents"] != len(cross["cross_shard"]) or
            cross["cross_shard_set_sha256"] !=
            _mapping_digest(cross["cross_shard"]) or
            cross["classified_rows"] != len(cross["classification"]) or
            cross["classification_sha256"] != _digest(
                _canonical_json_bytes(cross["classification"])) or
            not isinstance(cross.get("expected_owner"), Mapping) or
            any(not isinstance(intent, str) or not isinstance(owner, str) or
                pathlib.PurePosixPath(owner).is_absolute() or
                pathlib.PurePosixPath(owner).as_posix() != owner or
                ".." in pathlib.PurePosixPath(owner).parts
                for intent, owner in expected_owner_material.items()) or
            cross.get("expected_owner_set_sha256") !=
            _mapping_digest(expected_owner_material) or
            len(classification_coordinates) !=
            len(set(classification_coordinates)) or
            any(not isinstance(item, Mapping) or set(item) != {
                    "path", "row", "intent_id", "class"} or
                not isinstance(item.get("path"), str) or
                pathlib.PurePosixPath(item["path"]).is_absolute() or
                pathlib.PurePosixPath(item["path"]).as_posix() != item["path"] or
                ".." in pathlib.PurePosixPath(item["path"]).parts or
                type(item.get("row")) is not int or item["row"] < 1 or
                (item.get("intent_id") is not None and
                 not isinstance(item.get("intent_id"), str)) or
                item.get("class") not in {
                    "tombstone", "canonical_owner", "known_off_owner",
                    "semantic_pending_owner", "unknown_or_orphan_active"}
                for item in cross["classification"]) or
            any(not isinstance(intent, str) or
                not isinstance(item, Mapping) or set(item) != {
                    "expected_owner", "superseded_target", "actual_paths"} or
                not isinstance(item.get("expected_owner"), str) or
                not isinstance(item.get("superseded_target"), str) or
                not isinstance(item.get("actual_paths"), list) or
                any(not isinstance(path, str) for path in item["actual_paths"])
                for intent, item in cross["semantic_pending"].items()) or
            any(not isinstance(intent, str) or
                not isinstance(item, Mapping) or set(item) != {
                    "expected_owner", "actual_paths"} or
                not isinstance(item.get("expected_owner"), str) or
                not isinstance(item.get("actual_paths"), list) or
                any(not isinstance(path, str) for path in item["actual_paths"])
                for intent, item in cross["cross_shard"].items()) or
            cross["classified_rows"] != cross["all_stock_rows"] or
            cross["tombstone_rows"] != classes.count("tombstone") or
            cross["active_rows"] !=
            len(classes) - classes.count("tombstone") or
            cross["unknown_or_orphan_active_rows"] !=
            classes.count("unknown_or_orphan_active") or
            cross["observed_intents"] != len(known_active_intents) or
            cross["expected_intents"] !=
            successor_counts["portfolio_intents"] or
            cross["expected_intents"] != len(expected_owner_material) or
            not known_active_intents.issubset(expected_owner_material) or
            any(item.get("class") == "canonical_owner" and
                item.get("path") != expected_owner_material.get(
                    item.get("intent_id"))
                for item in classification_material
                if isinstance(item, Mapping)) or
            any(item.get("class") in {
                    "known_off_owner", "semantic_pending_owner"} and
                item.get("path") == expected_owner_material.get(
                    item.get("intent_id"))
                for item in classification_material
                if isinstance(item, Mapping)) or
            not set(item.get("path") for item in classification_material
                    if isinstance(item, Mapping)).issubset(stock_sha) or
            set(cross["cross_shard"]) != off_owner_intents or
            any(set(item["actual_paths"]) != off_owner_paths.get(intent, set()) or
                item["expected_owner"] != expected_owner_material.get(intent)
                for intent, item in cross["cross_shard"].items()) or
            set(cross["semantic_pending"]) != semantic_pending_intents or
            any(set(item["actual_paths"]) != pending_paths.get(intent, set()) or
                item["expected_owner"] != expected_owner_material.get(intent) or
                item["superseded_target"] not in pending_paths.get(intent, set())
                for intent, item in cross["semantic_pending"].items()) or
            cross["unknown_or_orphan_active_rows"] != 0 or
            cross["cross_shard_intents"] != 0):
        raise ValueError("receipt não classificou 100% do estoque ativo")

    lineage_keys = {
        "head", "preimage_introduction_commit",
        "preimage_commit_is_head_ancestor", "paths", "unanchored_paths",
        "final_head", "drifted_paths_during_check",
        "appeared_absences_during_check",
    }
    if (not isinstance(lineage, Mapping) or set(lineage) != lineage_keys or
            lineage.get("head") != anchor or lineage.get("final_head") != anchor or
            lineage.get("preimage_commit_is_head_ancestor") is not True or
            any(lineage.get(key) != [] for key in (
                "unanchored_paths", "drifted_paths_during_check",
                "appeared_absences_during_check")) or
            not isinstance(lineage.get("preimage_introduction_commit"), str) or
            GIT_OID_RE.fullmatch(lineage["preimage_introduction_commit"]) is None or
            not isinstance(lineage.get("paths"), Mapping)):
        raise ValueError("schema profundo/closure do git_lineage é inválido")
    present_graph = {path: digest for path, digest in paths.items()
                     if digest is not None}
    if set(lineage["paths"]) != set(present_graph):
        raise ValueError("git_lineage não fecha os paths presentes do grafo")
    for path, evidence in lineage["paths"].items():
        if (not isinstance(evidence, Mapping) or set(evidence) != {
                "git_blob_oid", "sha256", "matches_graph"} or
                not isinstance(evidence.get("git_blob_oid"), str) or
                GIT_OID_RE.fullmatch(evidence["git_blob_oid"]) is None or
                evidence.get("sha256") != present_graph[path] or
                evidence.get("matches_graph") is not True):
            raise ValueError(f"git_lineage path inválido: {path}")

    original = value.get("original_transform")
    original_keys = {
        "inventory_reconstructable", "archived_full_sha256",
        "transformed_archived_full_sha256", "transformed_batches_sha256",
        "counts", "original_template_sha256",
        "original_template_git_commits", "exact_original_queue_reconstructable",
        "expected_aggregate_set_sha256", "historical_reconstruction_error",
    }
    if (not isinstance(original, Mapping) or set(original) != original_keys or
            original.get("inventory_reconstructable") is not True and
            original.get("inventory_reconstructable") is not False or
            original.get("expected_aggregate_set_sha256") !=
            migration.EXPECTED_AGGREGATE_SET_SHA256 or
            not isinstance(original.get("archived_full_sha256"), str) or
            SHA256_RE.fullmatch(original["archived_full_sha256"]) is None or
            not isinstance(original.get("original_template_sha256"), str) or
            SHA256_RE.fullmatch(original["original_template_sha256"]) is None or
            not isinstance(original.get("original_template_git_commits"), list) or
            any(not isinstance(commit, str) or
                GIT_OID_RE.fullmatch(commit) is None
                for commit in original["original_template_git_commits"]) or
            original.get("exact_original_queue_reconstructable") is not
            bool(original["original_template_git_commits"])):
        raise ValueError("schema profundo de original_transform é inválido")
    _closed_int_map(original["counts"], "original counts")
    expected_original_counts = {
        "batches_before": migration.EXPECTED_BATCHES_BEFORE,
        "batches_after": migration.EXPECTED_BATCHES_AFTER,
        "portfolio_intents": migration.EXPECTED_PORTFOLIO_INTENTS,
        "take_zero_batches": migration.EXPECTED_TAKE_ZERO_BATCHES,
        "aggregate_batches": migration.EXPECTED_AGGREGATE_BATCHES,
        "retired_batches": migration.EXPECTED_RETIRED_BATCHES,
        "adjusted_batches": migration.EXPECTED_ADJUSTED_BATCHES,
        "new_batches": migration.EXPECTED_NEW_BATCHES,
        "new_intents": migration.EXPECTED_NEW_INTENTS,
    }
    if original["inventory_reconstructable"]:
        if (original.get("historical_reconstruction_error") is not None or
                any(not isinstance(original.get(key), str) or
                    SHA256_RE.fullmatch(original[key]) is None for key in {
                        "transformed_archived_full_sha256",
                        "transformed_batches_sha256"}) or
                dict(original["counts"]) != expected_original_counts):
            raise ValueError("claim histórico reconstruível diverge")
    elif (not isinstance(original.get("historical_reconstruction_error"), str) or
          not original["historical_reconstruction_error"] or
          original.get("transformed_archived_full_sha256") is not None or
          original.get("transformed_batches_sha256") is not None or
          original["counts"]):
        raise ValueError("non-claim histórico irrecuperável é inválido")
    full_archive = migration.PREIMAGE_ARCHIVE_BY_OUTPUT[migration.FULL_REL]
    if original["archived_full_sha256"] != archives[full_archive]:
        raise ValueError("archived_full_sha256 não liga ao archive full")

    warnings = value.get("warnings")
    if (not isinstance(warnings, list) or any(
            not isinstance(item, Mapping) or set(item) != {
                "code", "detail", "required_artifact"} or
            any(not isinstance(item[key], str) or not item[key]
                for key in item)
            for item in warnings)):
        raise ValueError("schema profundo de warnings é inválido")
    if not original["inventory_reconstructable"]:
        historical_warnings = [
            item for item in warnings
            if item["code"] == "historical_aggregate_bytes_not_durable"
        ]
        if (len(historical_warnings) != 1 or
                migration.EXPECTED_AGGREGATE_SET_SHA256 not in
                historical_warnings[0]["detail"]):
            raise ValueError(
                "non-claim histórico exige warning ligado ao hash one-shot"
            )
    proof = dict(value)
    claimed = proof.pop("proof_sha256")
    if _digest(_canonical_json_bytes(proof)) != claimed:
        raise ValueError("proof_sha256 do receipt sucessor diverge")


def receipt_payload(report: Mapping[str, Any]) -> bytes:
    if report.get("passed") is not True or report.get("blockers") != []:
        raise ReconciliationBlocked(
            "receipt sucessor recusado enquanto houver blocker"
        )
    value = dict(report)
    _validate_receipt_value(value)
    payload = _canonical_json_bytes(value, indent=2)
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ValueError("receipt sucessor excede 4 MiB")
    return payload


def _atomic_create_receipt_effect(
    root: pathlib.Path,
    payload: bytes,
) -> ReceiptCreateEffect:
    if not isinstance(payload, bytes) or not payload.endswith(b"\n"):
        raise TypeError("receipt precisa ser bytes canônicos com newline")
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ValueError("receipt sucessor excede 4 MiB")
    existing = _receipt_snapshot(root, missing_ok=True)
    if existing is not None:
        if existing.payload != payload:
            raise queue.CASMismatch("receipt sucessor existente diverge")

    directory_fd, name, absolute = queue._open_parent_directory(
        root / RECEIPT_REL
    )
    temp_name: str | None = None
    try:
        raced = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=True,
            max_bytes=MAX_RECEIPT_BYTES,
        )
        if raced is not None:
            if (raced.mode == 0o644 and raced.nlink == 1 and
                    raced.payload == payload):
                os.fsync(directory_fd)
                final_existing = queue._read_snapshot_at(
                    directory_fd,
                    name,
                    missing_ok=False,
                    max_bytes=MAX_RECEIPT_BYTES,
                )
                if (final_existing is None or
                        not queue._same_snapshot(final_existing, raced)):
                    raise queue.CASMismatch(
                        "receipt existente mudou durante fsync"
                    )
                return ReceiptCreateEffect(False, None, None)
            raise queue.CASMismatch(
                "receipt sucessor apareceu com bytes/modo divergentes"
            )
        temp_name, staged = queue._create_temp_at(
            directory_fd, name, payload, 0o644
        )
        try:
            queue._renameat2(
                directory_fd,
                temp_name,
                directory_fd,
                name,
                queue._RENAME_NOREPLACE,
            )
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
            raced = queue._read_snapshot_at(
                directory_fd,
                name,
                missing_ok=False,
                max_bytes=MAX_RECEIPT_BYTES,
            )
            if (raced is None or raced.mode != 0o644 or
                    raced.nlink != 1 or raced.payload != payload):
                raise queue.CASMismatch(
                    "criação concorrente do receipt divergiu"
                ) from error
            os.fsync(directory_fd)
            final_raced = queue._read_snapshot_at(
                directory_fd,
                name,
                missing_ok=False,
                max_bytes=MAX_RECEIPT_BYTES,
            )
            if (final_raced is None or
                    not queue._same_snapshot(final_raced, raced)):
                raise queue.CASMismatch(
                    "receipt concorrente mudou durante fsync"
                )
            return ReceiptCreateEffect(False, None, None)
        temp_name = None
        os.fsync(directory_fd)
        installed = queue._read_snapshot_at(
            directory_fd,
            name,
            missing_ok=False,
            max_bytes=MAX_RECEIPT_BYTES,
        )
        if (installed is None or installed.mode != 0o644 or
                installed.nlink != 1 or
                not queue._same_snapshot(installed, staged)):
            raise queue.CASMismatch(
                f"receipt sucessor mudou durante instalação: {absolute}"
            )
        inode_fd = os.open(
            name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
        inode_info = os.fstat(inode_fd)
        if ((inode_info.st_dev, inode_info.st_ino) !=
                (installed.device, installed.inode)):
            os.close(inode_fd)
            raise queue.CASMismatch(
                "receipt mudou antes da captura do token de efeito"
            )
        return ReceiptCreateEffect(True, installed, inode_fd)
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)


def _atomic_create_receipt(root: pathlib.Path, payload: bytes) -> bool:
    """Compatibilidade: cria/reusa sem expor o token interno de effect-CAS."""
    effect = _atomic_create_receipt_effect(root, payload)
    if effect.inode_fd is not None:
        os.close(effect.inode_fd)
    return effect.created


def _remove_created_receipt(
    root: pathlib.Path,
    payload: bytes,
    installed: Any,
    inode_fd: int,
) -> bool:
    """Remove somente o inode exato criado por esta tentativa.

    ``False`` significa que a entrada já sumiu ou foi substituída; nesse caso
    nada é removido, inclusive quando o substituto tem os mesmos bytes.
    """
    directory_fd, name, _ = queue._open_parent_directory(root / RECEIPT_REL)
    try:
        held = os.fstat(inode_fd)
        if ((held.st_dev, held.st_ino) !=
                (installed.device, installed.inode)):
            raise queue.CASMismatch("token do inode criado divergiu")
        current = queue._read_snapshot_at(
            directory_fd, name, missing_ok=True,
            max_bytes=MAX_RECEIPT_BYTES,
        )
        if (current is None or current.payload != payload or
                current.mode != 0o644 or current.nlink != 1 or
                not queue._same_snapshot(current, installed)):
            return False
        os.unlink(name, dir_fd=directory_fd)
        os.fsync(directory_fd)
        if queue._read_snapshot_at(
                directory_fd, name, missing_ok=True,
                max_bytes=MAX_RECEIPT_BYTES) is not None:
            raise queue.CASMismatch("receipt reapareceu após rollback autenticado")
        return True
    finally:
        os.close(directory_fd)


def _workflow_apply_plan(root: pathlib.Path) -> WorkflowApplyPlan:
    bundle = migration._verify_preimage_manifest(root)
    reconstructed = reconstruct_current_inventory(root, bundle)
    live_snapshots, live_documents, _ = _read_live_outputs(root)
    successor = build_successor_epoch(root, reconstructed, live_documents)
    all_stock = _cross_shard_owner_evidence(root, reconstructed)
    _validate_all_stock_preflight(all_stock)
    return WorkflowApplyPlan(
        outputs=dict(successor.outputs),
        expected_outputs={
            path: snapshot.payload for path, snapshot in live_snapshots.items()
        },
        input_sha256=dict(successor.input_sha256),
        absent_input_paths=successor.absent_input_paths,
        stock_sha256=dict(successor.stock_sha256),
        all_stock_evidence=all_stock,
    )


def _validate_all_stock_preflight(evidence: Mapping[str, Any]) -> None:
    if (not isinstance(evidence, Mapping) or
            evidence.get("classified_rows") != evidence.get("all_stock_rows") or
            evidence.get("active_rows", -1) + evidence.get(
                "tombstone_rows", -1) != evidence.get("all_stock_rows") or
            evidence.get("unknown_or_orphan_active_rows") != 0 or
            evidence.get("cross_shard_intents") != 0):
        raise ReconciliationBlocked(
            "apply-workflows exige 100% all-stock classificado, sem orphan "
            "nem owner cross-shard"
        )


def _revalidate_workflow_apply_plan(
    root: pathlib.Path,
    plan: WorkflowApplyPlan,
    *,
    outputs_installed: bool = False,
) -> None:
    for path, expected in plan.input_sha256.items():
        if outputs_installed and path in plan.outputs:
            expected = _digest(plan.outputs[path])
        actual = queue.snapshot_sha256(
            root / path, max_bytes=migration._dependency_max_bytes(path)
        )
        if actual != expected:
            raise queue.CASMismatch(f"input mudou antes do CAS: {path}")
    appeared = sorted(
        path for path in plan.absent_input_paths if os.path.lexists(root / path)
    )
    if appeared:
        raise queue.CASMismatch(f"dependências ausentes apareceram: {appeared[:8]}")
    current_stock_paths = {
        path.relative_to(root).as_posix() for path in migration._stock_paths(root)
    }
    if current_stock_paths != set(plan.stock_sha256):
        raise queue.CASMismatch("universo all-stock mudou antes do CAS")
    current_stock = {
        path: queue.snapshot_sha256(root / path, max_bytes=migration.MAX_STOCK_BYTES)
        for path in sorted(current_stock_paths)
    }
    queue.authenticate_snapshot_set(
        plan.stock_sha256, current_stock, current_stock_paths
    )


def _apply_workflows_locked(root: pathlib.Path) -> Mapping[str, str]:
    """Instala somente os três workflows; nunca cria qualquer receipt."""
    root = pathlib.Path(os.path.abspath(os.fspath(root)))
    if (os.path.lexists(root / RECEIPT_REL) or
            os.path.lexists(root / migration.RECEIPT_REL)):
        raise queue.CASMismatch("algum receipt já existe; workflows fechados")
    plan = _workflow_apply_plan(root)
    _revalidate_workflow_apply_plan(root, plan)
    replacements = [
        (path, plan.expected_outputs[path], plan.outputs[path])
        for path in sorted(migration._OUTPUT_PATHS)
    ]
    def terminal_preflight() -> None:
        if (os.path.lexists(root / RECEIPT_REL) or
                os.path.lexists(root / migration.RECEIPT_REL)):
            raise queue.CASMismatch(
                "receipt apareceu antes do CAS terminal dos workflows"
            )
        _revalidate_workflow_apply_plan(root, plan)

    # Não há operação falível após o CAS terminal. Qualquer falha no
    # preflight ocorre dentro de atomic_replace_many e aciona seu rollback
    # effect-CAS autenticado das saídas intermediárias.
    migration.atomic_replace_many(
        root, replacements, before_last=terminal_preflight
    )
    return {path: _digest(payload) for path, payload in sorted(plan.outputs.items())}


def apply_workflows(root: pathlib.Path = ROOT) -> Mapping[str, str]:
    root = pathlib.Path(os.path.abspath(os.fspath(root)))
    with migration.exclusive_lock():
        return _apply_workflows_locked(root)


def _apply_receipt_locked(
    root: pathlib.Path,
) -> tuple[Mapping[str, Any], bool]:
    """Cria somente o receipt após workflows commitados e grafo fechado."""
    root = pathlib.Path(os.path.abspath(os.fspath(root)))
    observed_at_utc, _ = _observation_clock(None)
    first = inspect(root, observed_at_utc=observed_at_utc)
    payload = receipt_payload(first)
    second = inspect(root, observed_at_utc=observed_at_utc)
    second_payload = receipt_payload(second)
    if payload != second_payload:
        raise queue.CASMismatch(
            "epoch mudou entre plano e precommit do receipt sucessor"
        )
    if os.path.lexists(root / migration.RECEIPT_REL):
        raise queue.CASMismatch("receipt original apareceu antes do commit")
    effect = _atomic_create_receipt_effect(root, payload)
    try:
        final = _receipt_snapshot(root, missing_ok=False)
        if final is None or final.payload != payload:
            raise queue.CASMismatch("receipt sucessor final divergiu")
        _validate_receipt_value(
            queue.decode_json_no_duplicate_keys(final.payload, RECEIPT_REL)
        )
        final_report = inspect(
            root,
            observed_at_utc=observed_at_utc,
            require_terminal_receipt=False,
        )
        if receipt_payload(final_report) != payload:
            raise queue.CASMismatch(
                "epoch mudou durante a criação do receipt sucessor"
            )
        if os.path.lexists(root / migration.RECEIPT_REL):
            raise queue.CASMismatch("receipt original apareceu durante o commit")
        # O check terminal ocorre somente depois que o receipt for commitado;
        # exigir isso aqui criaria um ciclo impossível no próprio apply.
        if effect.inode_fd is not None:
            os.close(effect.inode_fd)
        return first, effect.created
    except BaseException as error:
        if effect.created:
            try:
                removed = _remove_created_receipt(
                    root, payload, effect.installed, effect.inode_fd
                )
            finally:
                os.close(effect.inode_fd)
            if not removed:
                raise queue.CASMismatch(
                    "falha pós-create; receipt criado mudou e foi preservado"
                ) from error
        raise


def apply_receipt(root: pathlib.Path = ROOT) -> tuple[Mapping[str, Any], bool]:
    root = pathlib.Path(os.path.abspath(os.fspath(root)))
    with migration.exclusive_lock():
        return _apply_receipt_locked(root)


# Compatibilidade de import apenas; a CLI exige a ação explícita.
apply = apply_receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--apply-workflows", action="store_true")
    action.add_argument("--apply-receipt", action="store_true")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.check:
            report = inspect(args.root)
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            return 0 if report["passed"] else 1
        if args.apply_workflows:
            outputs = apply_workflows(args.root)
            print(json.dumps({
                "workflow_output_sha256": outputs,
                "receipt_created": False,
                "publication": False,
            }, ensure_ascii=False, sort_keys=True))
            return 0
        report, created = apply_receipt(args.root)
        print(json.dumps({
            "created": created,
            "receipt_rel_path": RECEIPT_REL,
            "proof_sha256": report["proof_sha256"],
            "publication": False,
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"reconciliation blocked: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
