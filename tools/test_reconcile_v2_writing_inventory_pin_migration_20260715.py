#!/usr/bin/env python3
"""Regressões do reconciliador durável da migração writing inventory."""

from __future__ import annotations

import hashlib
import errno
import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest
from unittest import mock


from tools import generate_v2_review_queue as queue
from tools import reconcile_v2_writing_inventory_pin_migration_20260715 as sut


def _closed_report(**updates: object) -> dict[str, object]:
    graph_paths: dict[str, str | None] = {
        path: "a" * 64 for path in {
            sut.migration.PREIMAGE_MANIFEST_REL,
            *sut.migration._PREIMAGE_ARCHIVE_PATHS,
            *sut.migration._OUTPUT_PATHS,
            *sut._GRAPH_TOOL_PATHS,
        }
    }
    graph_paths[sut.migration.RECEIPT_REL] = None
    input_path = "data/editorial/fixture-input.json"
    stock_path = "data/editorial/v2_pages/fixture-stock.jsonl"
    graph_paths[input_path] = "e" * 64
    graph_paths[stock_path] = "f" * 64
    expected_owner = {
        "fixture-intent": stock_path,
        **{
            f"fixture-unobserved-{index:04d}": stock_path
            for index in range(1, sut.migration.EXPECTED_PORTFOLIO_INTENTS)
        },
    }
    empty_sha = hashlib.sha256(b"").hexdigest()
    output_evidence = {
        path: {
            "sha256": graph_paths[path], "bytes": 0,
            "prefix_sha256": empty_sha, "batches_sha256": empty_sha,
            "batch_count": (
                sut.migration.EXPECTED_BATCHES_AFTER
                if path == sut.migration.FULL_REL else
                sut.migration.EXPECTED_TODO_BATCHES
                if path == sut.migration.TODO_REL else
                sut.migration.EXPECTED_TODO_WITHOUT_TELECOM_BATCHES
            ),
            "suffix_sha256": empty_sha,
        }
        for path in sut.migration._OUTPUT_PATHS
    }
    git_paths = {
        path: {
            "git_blob_oid": "c" * 40,
            "sha256": digest,
            "matches_graph": True,
        }
        for path, digest in graph_paths.items() if digest is not None
    }
    value: dict[str, object] = {
        "schema_version": sut.SCHEMA_VERSION,
        "reconciliation_id": sut.RECONCILIATION_ID,
        "migration_epoch_date": sut.HISTORICAL_CHECKED_AT,
        "observed_at_utc": "2026-07-16T10:00:00Z",
        "validation_date": "2026-07-16",
        "original_receipt_rel_path": sut.migration.RECEIPT_REL,
        "successor_receipt_rel_path": sut.RECEIPT_REL,
        "original_receipt_exists": False,
        "preimages": {
            "manifest_rel_path": sut.migration.PREIMAGE_MANIFEST_REL,
            "manifest_sha256": graph_paths[
                sut.migration.PREIMAGE_MANIFEST_REL],
            "archive_sha256": {
                path: graph_paths[path]
                for path in sut.migration._PREIMAGE_ARCHIVE_PATHS
            },
            "entries": {
                active: {
                    "archive_path": archive,
                    "sha256": graph_paths[archive],
                    "bytes": 0,
                    "mode": "0644",
                    "nlink": 1,
                }
                for active, archive in
                sut.migration.PREIMAGE_ARCHIVE_BY_OUTPUT.items()
            },
            "preimage_set_sha256": sut.migration._preimage_set_digest({
                active: {
                    "archive_path": archive,
                    "sha256": graph_paths[archive],
                    "bytes": 0,
                    "mode": "0644",
                    "nlink": 1,
                }
                for active, archive in
                sut.migration.PREIMAGE_ARCHIVE_BY_OUTPUT.items()
            }),
        },
        "original_transform": {
            "inventory_reconstructable": True,
            "expected_aggregate_set_sha256": (
                sut.migration.EXPECTED_AGGREGATE_SET_SHA256
            ),
            "historical_reconstruction_error": None,
            "archived_full_sha256": "a" * 64,
            "transformed_archived_full_sha256": "b" * 64,
            "transformed_batches_sha256": "c" * 64,
            "counts": {
                "batches_before": sut.migration.EXPECTED_BATCHES_BEFORE,
                "batches_after": sut.migration.EXPECTED_BATCHES_AFTER,
                "portfolio_intents": sut.migration.EXPECTED_PORTFOLIO_INTENTS,
                "take_zero_batches": sut.migration.EXPECTED_TAKE_ZERO_BATCHES,
                "aggregate_batches": sut.migration.EXPECTED_AGGREGATE_BATCHES,
                "retired_batches": sut.migration.EXPECTED_RETIRED_BATCHES,
                "adjusted_batches": sut.migration.EXPECTED_ADJUSTED_BATCHES,
                "new_batches": sut.migration.EXPECTED_NEW_BATCHES,
                "new_intents": sut.migration.EXPECTED_NEW_INTENTS,
            },
            "original_template_sha256": "d" * 64,
            "original_template_git_commits": [],
            "exact_original_queue_reconstructable": False,
        },
        "live_outputs": output_evidence,
        "cross_shard_owner_evidence": {
            "expected_intents": sut.migration.EXPECTED_PORTFOLIO_INTENTS,
            "expected_owner": expected_owner,
            "expected_owner_set_sha256": sut._mapping_digest(expected_owner),
            "observed_intents": 1,
            "semantic_pending_intents": 0,
            "semantic_pending": {},
            "semantic_pending_set_sha256": sut._mapping_digest({}),
            "cross_shard_intents": 0,
            "cross_shard": {},
            "cross_shard_set_sha256": sut._mapping_digest({}),
            "all_stock_rows": 1,
            "active_rows": 1,
            "tombstone_rows": 0,
            "classified_rows": 1,
            "classification": [{
                "path": stock_path, "row": 1,
                "intent_id": "fixture-intent", "class": "canonical_owner",
            }],
            "classification_sha256": sut._digest(
                sut._canonical_json_bytes([{
                    "path": stock_path, "row": 1,
                    "intent_id": "fixture-intent",
                    "class": "canonical_owner",
                }])),
            "unknown_or_orphan_active_rows": 0,
            "unknown_or_orphan_sample": [],
            "sample": [],
        },
        "successor_epoch": {
            "input_sha256": {input_path: graph_paths[input_path]},
            "input_set_sha256": sut._mapping_digest({
                input_path: graph_paths[input_path]}),
            "absent_input_paths": [],
            "stock_sha256": {stock_path: graph_paths[stock_path]},
            "stock_set_sha256": sut._mapping_digest({
                stock_path: graph_paths[stock_path]}),
            "expected_output_sha256": {
                path: graph_paths[path]
                for path in sut.migration._OUTPUT_PATHS
            },
            "counts": {
                "batches_before": sut.migration.EXPECTED_BATCHES_BEFORE,
                "batches_after": sut.migration.EXPECTED_BATCHES_AFTER,
                "portfolio_intents": sut.migration.EXPECTED_PORTFOLIO_INTENTS,
                "take_zero_batches": sut.migration.EXPECTED_TAKE_ZERO_BATCHES,
                "aggregate_batches": sut.migration.EXPECTED_AGGREGATE_BATCHES,
                "retired_batches": sut.migration.EXPECTED_RETIRED_BATCHES,
                "adjusted_batches": sut.migration.EXPECTED_ADJUSTED_BATCHES,
                "new_batches": sut.migration.EXPECTED_NEW_BATCHES,
                "new_intents": sut.migration.EXPECTED_NEW_INTENTS,
                "complete_batches": (
                    sut.migration.EXPECTED_BATCHES_AFTER -
                    sut.migration.EXPECTED_TODO_BATCHES),
                "todo_batches": sut.migration.EXPECTED_TODO_BATCHES,
                "todo_without_telecom_batches": (
                    sut.migration.EXPECTED_TODO_WITHOUT_TELECOM_BATCHES),
                "semantic_requirements": (
                    sut.migration.EXPECTED_SEMANTIC_REQUIREMENTS),
                "unresolved_semantic_requirements": (
                    sut.migration.EXPECTED_UNRESOLVED_SEMANTIC_REQUIREMENTS),
            },
        },
        "git_lineage": {
            "head": "b" * 40,
            "preimage_introduction_commit": "a" * 40,
            "preimage_commit_is_head_ancestor": True,
            "paths": git_paths,
            "unanchored_paths": [],
            "final_head": "b" * 40,
            "drifted_paths_during_check": [],
            "appeared_absences_during_check": [],
        },
        "anchor_commit": "b" * 40,
        "graph_sha256": graph_paths,
        "graph_set_sha256": sut._digest(
            sut._canonical_json_bytes(dict(sorted(graph_paths.items())))
        ),
        "passed": True,
        "blockers": [],
        "warnings": [],
        "publication_touches": [],
        "index_policy": "noindex",
        "render_allowed": False,
        "sitemap_allowed": False,
        "publication_allowed": False,
        "approval": False,
        "publicly_indexable": False,
    }
    value.update(updates)
    proof = dict(value)
    value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
    return value


class ReceiptContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-migrecon-"))
        (self.root / "data/editorial").mkdir(parents=True)

    def tearDown(self) -> None:
        for directory, children, files in os.walk(
                self.root, topdown=False, followlinks=False):
            for name in files:
                pathlib.Path(directory, name).unlink(missing_ok=True)
            for name in children:
                child = pathlib.Path(directory, name)
                if child.is_symlink():
                    child.unlink()
                else:
                    child.rmdir()
        self.root.rmdir()

    def test_receipt_payload_is_closed_canonical_and_self_authenticating(
        self,
    ) -> None:
        report = _closed_report()
        payload = sut.receipt_payload(report)
        self.assertTrue(payload.endswith(b"\n"))
        value = queue.decode_json_no_duplicate_keys(payload, "receipt")
        sut._validate_receipt_value(value)
        self.assertEqual(value["publication_touches"], [])
        self.assertEqual(value["index_policy"], "noindex")
        for flag in (
            "render_allowed", "sitemap_allowed", "publication_allowed",
            "approval", "publicly_indexable",
        ):
            self.assertIs(value[flag], False)

        tampered = dict(value)
        tampered["approval"] = True
        with self.assertRaisesRegex(ValueError, "publicamente fechado"):
            sut._validate_receipt_value(tampered)
        tampered = dict(value)
        tampered["warnings"] = [{
            "code": "historical_note",
            "detail": "valid nested mutation",
            "required_artifact": "none",
        }]
        with self.assertRaisesRegex(ValueError, "proof_sha256"):
            sut._validate_receipt_value(tampered)
        tampered = dict(value)
        tampered["publication_allowed_shadow"] = True
        with self.assertRaisesRegex(ValueError, "publicamente fechado"):
            sut._validate_receipt_value(tampered)

    def test_blocked_report_cannot_become_receipt(self) -> None:
        report = _closed_report(
            passed=False,
            blockers=[{"code": "missing", "detail": "evidence"}],
        )
        with self.assertRaisesRegex(
                sut.ReconciliationBlocked, "houver blocker"):
            sut.receipt_payload(report)

    def test_create_is_0644_noreplace_and_idempotent_only_for_exact_bytes(
        self,
    ) -> None:
        payload = sut.receipt_payload(
            _closed_report(observed_at_utc="2026-07-16T10:00:00Z")
        )
        self.assertTrue(sut._atomic_create_receipt(self.root, payload))
        target = self.root / sut.RECEIPT_REL
        info = target.stat(follow_symlinks=False)
        self.assertTrue(stat.S_ISREG(info.st_mode))
        self.assertEqual(stat.S_IMODE(info.st_mode), 0o644)
        self.assertEqual(info.st_nlink, 1)
        self.assertEqual(target.read_bytes(), payload)
        self.assertFalse(sut._atomic_create_receipt(self.root, payload))

        other = sut.receipt_payload(
            _closed_report(
                observed_at_utc="2026-07-16T10:00:01Z")
        )
        with self.assertRaisesRegex(queue.CASMismatch, "existente diverge"):
            sut._atomic_create_receipt(self.root, other)

    def test_existing_unsafe_mode_or_hardlink_fails_closed(self) -> None:
        payload = sut.receipt_payload(
            _closed_report()
        )
        target = self.root / sut.RECEIPT_REL
        target.write_bytes(payload)
        target.chmod(0o600)
        with self.assertRaisesRegex(RuntimeError, "0644/nlink1"):
            sut._atomic_create_receipt(self.root, payload)

    def test_create_mode_ignores_restrictive_umask_and_exact_race_reuses(
        self,
    ) -> None:
        payload = sut.receipt_payload(
            _closed_report()
        )
        previous_umask = os.umask(0o077)
        try:
            self.assertTrue(sut._atomic_create_receipt(self.root, payload))
        finally:
            os.umask(previous_umask)
        target = self.root / sut.RECEIPT_REL
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o644)

        target.unlink()
        def install_same_then_report_exists(
            source_fd: int,
            source_name: str,
            target_fd: int,
            target_name: str,
            flags: int,
        ) -> None:
            del source_fd, source_name, flags
            descriptor = os.open(
                target_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
                0o644,
                dir_fd=target_fd,
            )
            try:
                os.write(descriptor, payload)
                os.fchmod(descriptor, 0o644)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            raise OSError(errno.EEXIST, "fixture race")

        with mock.patch.object(
                queue, "_renameat2", install_same_then_report_exists):
            self.assertFalse(sut._atomic_create_receipt(self.root, payload))
        self.assertEqual(target.read_bytes(), payload)

        target.unlink()

        def install_other_then_report_exists(
            source_fd: int,
            source_name: str,
            target_fd: int,
            target_name: str,
            flags: int,
        ) -> None:
            del source_fd, source_name, flags
            descriptor = os.open(
                target_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
                0o644,
                dir_fd=target_fd,
            )
            try:
                os.write(descriptor, b"{}\n")
                os.fchmod(descriptor, 0o644)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            raise OSError(errno.EEXIST, "fixture divergent race")

        with mock.patch.object(
                queue, "_renameat2", install_other_then_report_exists):
            with self.assertRaisesRegex(
                    queue.CASMismatch, "criação concorrente"):
                sut._atomic_create_receipt(self.root, payload)
        self.assertEqual(target.read_bytes(), b"{}\n")

        target.chmod(0o644)
        alias = target.with_name("receipt-hardlink.json")
        os.link(target, alias)
        with self.assertRaisesRegex(RuntimeError, "0644/nlink1"):
            sut._atomic_create_receipt(self.root, payload)

    def test_apply_never_writes_when_inspection_is_blocked(self) -> None:
        blocked = _closed_report(
            passed=False,
            blockers=[{"code": "missing", "detail": "evidence"}],
        )
        with mock.patch.object(sut, "inspect", return_value=blocked), \
                mock.patch.object(sut, "_atomic_create_receipt") as create:
            with self.assertRaises(sut.ReconciliationBlocked):
                sut.apply(self.root)
            create.assert_not_called()

    def test_apply_workflows_never_creates_receipt(self) -> None:
        before = {path: (path + "\n").encode() for path in sut.migration._OUTPUT_PATHS}
        after = {path: payload + b"after\n" for path, payload in before.items()}
        plan = sut.WorkflowApplyPlan(
            outputs=after,
            expected_outputs=before,
            input_sha256={},
            absent_input_paths=(),
            stock_sha256={},
        )
        with mock.patch.object(sut, "_workflow_apply_plan", return_value=plan), \
                mock.patch.object(sut, "_revalidate_workflow_apply_plan"), \
                mock.patch.object(
                    sut.migration, "atomic_replace_many") as replace, \
                mock.patch.object(
                    queue, "snapshot_sha256",
                    side_effect=lambda path, **_: hashlib.sha256(
                        after[path.relative_to(self.root).as_posix()]
                    ).hexdigest(),
                ), mock.patch.object(sut, "_atomic_create_receipt") as receipt:
            result = sut.apply_workflows(self.root)
        self.assertEqual(set(result), set(after))
        replace.assert_called_once()
        receipt.assert_not_called()
        self.assertFalse(os.path.lexists(self.root / sut.RECEIPT_REL))

    def test_apply_receipt_never_runs_workflow_transaction(self) -> None:
        blocked = _closed_report(
            passed=False,
            blockers=[{"code": "missing", "detail": "evidence"}],
        )
        with mock.patch.object(sut, "inspect", return_value=blocked), \
                mock.patch.object(
                    sut.migration, "atomic_replace_many") as replace:
            with self.assertRaises(sut.ReconciliationBlocked):
                sut.apply_receipt(self.root)
        replace.assert_not_called()

    def test_post_create_failure_removes_only_created_receipt(self) -> None:
        report = _closed_report()
        calls = 0
        def fail_third(_: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("post-create")
        with mock.patch.object(sut, "inspect", return_value=report), \
                mock.patch.object(
                    sut, "_validate_receipt_value",
                    side_effect=fail_third,
                ):
            with self.assertRaisesRegex(RuntimeError, "post-create"):
                sut._apply_receipt_locked(self.root)
        self.assertFalse(os.path.lexists(self.root / sut.RECEIPT_REL))

    def test_post_create_failure_preserves_reused_receipt(self) -> None:
        report = _closed_report()
        payload = sut.receipt_payload(report)
        self.assertTrue(sut._atomic_create_receipt(self.root, payload))
        calls = 0
        def fail_third(_: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("post-reuse")
        with mock.patch.object(sut, "inspect", return_value=report), \
                mock.patch.object(
                    sut, "_validate_receipt_value",
                    side_effect=fail_third,
                ):
            with self.assertRaisesRegex(RuntimeError, "post-reuse"):
                sut._apply_receipt_locked(self.root)
        self.assertEqual((self.root / sut.RECEIPT_REL).read_bytes(), payload)

    def test_post_create_failure_preserves_concurrent_same_bytes_inode(self) -> None:
        report = _closed_report()
        payload = sut.receipt_payload(report)

        calls = 0
        def replace_inode_then_fail(_: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 3:
                target = self.root / sut.RECEIPT_REL
                target.unlink()
                target.write_bytes(payload)
                target.chmod(0o644)
                raise RuntimeError("concurrent replacement")

        with mock.patch.object(sut, "inspect", return_value=report), \
                mock.patch.object(
                    sut, "_validate_receipt_value",
                    side_effect=replace_inode_then_fail,
                ):
            with self.assertRaisesRegex(
                    queue.CASMismatch, "mudou e foi preservado"):
                sut._apply_receipt_locked(self.root)
        self.assertEqual((self.root / sut.RECEIPT_REL).read_bytes(), payload)

    def test_third_epoch_inspect_drift_removes_created_receipt(self) -> None:
        good = _closed_report()
        blocked = _closed_report(
            passed=False,
            blockers=[{"code": "epoch_drift", "detail": "changed"}],
        )
        with mock.patch.object(
                sut, "inspect", side_effect=[good, good, blocked]):
            with self.assertRaises(sut.ReconciliationBlocked):
                sut._apply_receipt_locked(self.root)
        self.assertFalse(os.path.lexists(self.root / sut.RECEIPT_REL))

    def test_third_epoch_drift_preserves_concurrent_replacement_inode(self) -> None:
        good = _closed_report()
        payload = sut.receipt_payload(good)
        blocked = _closed_report(
            passed=False,
            blockers=[{"code": "epoch_drift", "detail": "changed"}],
        )
        calls = 0
        def inspect_with_replacement(*_: object, **__: object) -> object:
            nonlocal calls
            calls += 1
            if calls == 3:
                target = self.root / sut.RECEIPT_REL
                target.unlink()
                target.write_bytes(payload)
                target.chmod(0o644)
                return blocked
            return good
        with mock.patch.object(sut, "inspect", side_effect=inspect_with_replacement):
            with self.assertRaisesRegex(
                    queue.CASMismatch, "mudou e foi preservado"):
                sut._apply_receipt_locked(self.root)
        self.assertEqual((self.root / sut.RECEIPT_REL).read_bytes(), payload)

    def test_apply_workflows_rolls_back_when_terminal_preflight_fails(self) -> None:
        before = {
            path: ("before:" + path + "\n").encode()
            for path in sut.migration._OUTPUT_PATHS
        }
        after = {
            path: ("after:" + path + "\n").encode()
            for path in sut.migration._OUTPUT_PATHS
        }
        for path, payload in before.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            target.chmod(0o644)
        plan = sut.WorkflowApplyPlan(
            outputs=after, expected_outputs=before,
            input_sha256={}, absent_input_paths=(), stock_sha256={},
            all_stock_evidence={
                "all_stock_rows": 0, "classified_rows": 0,
                "active_rows": 0, "tombstone_rows": 0,
                "unknown_or_orphan_active_rows": 0,
                "cross_shard_intents": 0,
            },
        )
        with mock.patch.object(sut, "_workflow_apply_plan", return_value=plan), \
                mock.patch.object(
                    sut, "_revalidate_workflow_apply_plan",
                    side_effect=[None, RuntimeError("terminal preflight")],
                ):
            with self.assertRaisesRegex(RuntimeError, "voltaram às preimagens"):
                sut._apply_workflows_locked(self.root)
        for path, payload in before.items():
            self.assertEqual((self.root / path).read_bytes(), payload)

    def test_all_stock_preflight_rejects_orphan(self) -> None:
        with self.assertRaisesRegex(
                sut.ReconciliationBlocked, "all-stock"):
            sut._validate_all_stock_preflight({
                "all_stock_rows": 2, "classified_rows": 2,
                "active_rows": 2, "tombstone_rows": 0,
                "unknown_or_orphan_active_rows": 1,
                "cross_shard_intents": 0,
            })

    def test_deep_schema_rejects_partial_graph_and_unclassified_stock(self) -> None:
        value = _closed_report()
        value["graph_sha256"] = {}
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "grafo"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        value["cross_shard_owner_evidence"][
            "unknown_or_orphan_active_rows"
        ] = 1
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

    def test_historical_epoch_and_live_utc_dates_are_distinct(self) -> None:
        value = _closed_report()
        value["validation_date"] = sut.HISTORICAL_CHECKED_AT
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "datas histórica/viva"):
            sut._validate_receipt_value(value)
        with self.assertRaisesRegex(ValueError, "UTC canônico"):
            sut._observation_clock("2026-07-16T07:00:00-03:00")

    def test_deep_schema_closes_digest_count_graph_and_lineage_relations(self) -> None:
        value = _closed_report()
        output_path = next(iter(sut.migration._OUTPUT_PATHS))
        value["live_outputs"] = {
            path: dict(component)
            for path, component in value["live_outputs"].items()
        }
        value["live_outputs"][output_path]["sha256"] = "f" * 64
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "live output"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        value["cross_shard_owner_evidence"] = dict(
            value["cross_shard_owner_evidence"]
        )
        value["cross_shard_owner_evidence"]["active_rows"] = 0
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        value["git_lineage"] = dict(value["git_lineage"])
        value["git_lineage"]["paths"] = dict(
            value["git_lineage"]["paths"]
        )
        value["git_lineage"]["paths"].pop(output_path)
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "não fecha"):
            sut._validate_receipt_value(value)

        for section, field, message in (
            ("preimages", "preimage_set_sha256", "preimages"),
            ("original_transform", "archived_full_sha256", "archive full"),
            ("cross_shard_owner_evidence", "semantic_pending_set_sha256", "100%"),
            ("cross_shard_owner_evidence", "classification_sha256", "100%"),
        ):
            value = _closed_report()
            value[section] = dict(value[section])
            value[section][field] = "0" * 64
            proof = dict(value)
            proof.pop("proof_sha256")
            value["proof_sha256"] = sut._digest(
                sut._canonical_json_bytes(proof))
            with self.assertRaisesRegex(ValueError, message):
                sut._validate_receipt_value(value)

        value = _closed_report()
        value["graph_sha256"] = dict(value["graph_sha256"])
        value["graph_sha256"][""] = "0" * 64
        value["graph_set_sha256"] = sut._digest(
            sut._canonical_json_bytes(
                dict(sorted(value["graph_sha256"].items())))
        )
        proof = dict(value)
        proof.pop("proof_sha256")
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))
        with self.assertRaisesRegex(ValueError, "grafo"):
            sut._validate_receipt_value(value)

    def test_classification_material_derives_all_counters_and_owner_maps(self) -> None:
        def resign(value: dict[str, object]) -> None:
            proof = dict(value)
            proof.pop("proof_sha256")
            value["proof_sha256"] = sut._digest(
                sut._canonical_json_bytes(proof))

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["classification"] = [dict(cross["classification"][0])]
        cross["classification"][0]["class"] = "tombstone"
        cross["classification_sha256"] = sut._digest(
            sut._canonical_json_bytes(cross["classification"]))
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

    def test_root_aware_recomputation_rejects_consistent_intent_rename(self) -> None:
        def resign(value: dict[str, object]) -> None:
            proof = dict(value)
            proof.pop("proof_sha256")
            value["proof_sha256"] = sut._digest(
                sut._canonical_json_bytes(proof))

        live = _closed_report()
        receipt = _closed_report()
        cross = dict(receipt["cross_shard_owner_evidence"])
        cross["expected_owner"] = dict(cross["expected_owner"])
        owner = cross["expected_owner"].pop("fixture-intent")
        cross["expected_owner"]["invented-consistent-intent"] = owner
        cross["expected_owner_set_sha256"] = sut._mapping_digest(
            cross["expected_owner"])
        cross["classification"] = [dict(cross["classification"][0])]
        cross["classification"][0]["intent_id"] = (
            "invented-consistent-intent")
        cross["classification_sha256"] = sut._digest(
            sut._canonical_json_bytes(cross["classification"]))
        receipt["cross_shard_owner_evidence"] = cross
        proof = dict(receipt)
        proof.pop("proof_sha256")
        receipt["proof_sha256"] = sut._digest(
            sut._canonical_json_bytes(proof))

        # O objeto isolado é propositalmente autoconsistente; somente a
        # recomputação contra o root conhece a identidade verdadeira.
        sut._validate_receipt_value(receipt)
        with self.assertRaisesRegex(ValueError, "root-aware"):
            sut._validate_receipt_against_live_report(receipt, live)

    def test_root_aware_recomputation_rejects_warning_tamper(self) -> None:
        def resign(value: dict[str, object]) -> None:
            proof = dict(value)
            proof.pop("proof_sha256")
            value["proof_sha256"] = sut._digest(
                sut._canonical_json_bytes(proof))

        live = _closed_report()
        receipt = _closed_report()
        receipt["warnings"] = [{
            "code": "adulterated_but_schema_valid",
            "detail": "warning não recomputado do root",
            "required_artifact": "artefato inventado",
        }]
        proof = dict(receipt)
        proof.pop("proof_sha256")
        receipt["proof_sha256"] = sut._digest(
            sut._canonical_json_bytes(proof))

        sut._validate_receipt_value(receipt)
        with self.assertRaisesRegex(ValueError, "root-aware"):
            sut._validate_receipt_against_live_report(receipt, live)

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["classification"] = [
            dict(cross["classification"][0]),
            dict(cross["classification"][0]),
        ]
        cross["classification_sha256"] = sut._digest(
            sut._canonical_json_bytes(cross["classification"]))
        cross["classified_rows"] = 2
        cross["all_stock_rows"] = 2
        cross["active_rows"] = 2
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["classification"] = [dict(cross["classification"][0])]
        cross["classification"][0]["path"] = (
            "data/editorial/v2_pages/not-in-stock.jsonl")
        cross["classification"][0]["class"] = "tombstone"
        cross["classification_sha256"] = sut._digest(
            sut._canonical_json_bytes(cross["classification"]))
        cross["active_rows"] = 0
        cross["tombstone_rows"] = 1
        cross["observed_intents"] = 0
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["classification"] = [dict(cross["classification"][0])]
        cross["classification"][0]["intent_id"] = "invented-intent"
        cross["classification_sha256"] = sut._digest(
            sut._canonical_json_bytes(cross["classification"]))
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["observed_intents"] = 0
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["expected_intents"] -= 1
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)

        value = _closed_report()
        cross = dict(value["cross_shard_owner_evidence"])
        cross["cross_shard"] = {
            "fixture-intent": {
                "expected_owner": "data/editorial/v2_pages/expected.jsonl",
                "actual_paths": ["data/editorial/v2_pages/actual.jsonl"],
            }
        }
        cross["cross_shard_intents"] = 1
        cross["cross_shard_set_sha256"] = sut._mapping_digest(
            cross["cross_shard"])
        value["cross_shard_owner_evidence"] = cross
        resign(value)
        with self.assertRaisesRegex(ValueError, "100%"):
            sut._validate_receipt_value(value)


class WorkflowLineageTest(unittest.TestCase):
    def test_irrecoverable_historical_aggregate_stays_a_non_claim(self) -> None:
        value = _closed_report()
        original = dict(value["original_transform"])
        historical = sut.migration.EXPECTED_AGGREGATE_SET_SHA256
        original.update({
            "inventory_reconstructable": False,
            "historical_reconstruction_error": (
                f"expected={historical} actual={'f' * 64}"
            ),
            "transformed_archived_full_sha256": None,
            "transformed_batches_sha256": None,
            "counts": {},
        })
        value["original_transform"] = original
        value["warnings"] = [{
            "code": "historical_aggregate_bytes_not_durable",
            "detail": f"hash histórico {historical} irrecuperável",
            "required_artifact": "successor vivo fechado",
        }]
        value["publication_touches"] = []
        value["index_policy"] = "noindex"
        value["render_allowed"] = False
        value["sitemap_allowed"] = False
        value["publication_allowed"] = False
        value["approval"] = False
        value["publicly_indexable"] = False
        proof = dict(value)
        proof.pop("proof_sha256", None)
        value["proof_sha256"] = sut._digest(sut._canonical_json_bytes(proof))

        sut._validate_receipt_value(value)
        self.assertEqual(
            value["original_transform"]["expected_aggregate_set_sha256"],
            historical,
        )
        self.assertFalse(value["original_transform"]["inventory_reconstructable"])
        self.assertFalse(value["publication_allowed"])

    def test_current_aggregate_reader_does_not_accept_unknown_owner(self) -> None:
        source = pathlib.Path(sut.__file__).read_text(encoding="utf-8")
        function = source.split(
            "def _snapshot_current_aggregate_intents(", 1
        )[1].split("\ndef _read_live_outputs(", 1)[0]
        self.assertNotIn("EXPECTED_AGGREGATE_SET_SHA256", function)
        self.assertIn("intent_id not in portfolio.family_by_intent", function)

    def test_current_aggregate_reader_rejects_any_skipped_field(self) -> None:
        portfolios = {}
        for area in {slug.split("-d", 1)[0]
                     for slug in sut.migration.AGGREGATE_SHARDS}:
            path = f"data/editorial/portfolio_v2/{area}.jsonl"
            intents = {
                f"{area}-intent-{index}"
                for index in range(20)
            }
            portfolios[path] = sut.migration.PortfolioSnapshot(
                rel_path=path, payload=b"", digest="0" * 64,
                records=(), by_family={},
                family_by_intent={intent: "family" for intent in intents},
            )

        snapshot = queue.RegularFileSnapshot(b"{}\n", "1" * 64)
        for malformed in (True, 1, "false", None):
            with self.subTest(skipped=malformed):
                def decode(rel_path, snapshot):
                    slug = pathlib.PurePosixPath(rel_path).stem
                    area = slug.split("-d", 1)[0]
                    count = 8 if slug == "glossario2-d05" else 13
                    records = [
                        {"intent_id": f"{area}-intent-{index}"}
                        for index in range(count)
                    ]
                    if slug == "consumidor-d01":
                        records[0]["skipped"] = malformed
                    return records, None

                with mock.patch.object(
                        queue, "read_regular_file_snapshot",
                        return_value=snapshot), mock.patch.object(
                            sut.migration, "_decode_target",
                            side_effect=decode):
                    with self.assertRaisesRegex(ValueError, "não é canônico"):
                        sut._snapshot_current_aggregate_intents(
                            pathlib.Path("/unused"), portfolios
                        )

    def test_durable_successor_does_not_consume_predecessor_todo(self) -> None:
        source = pathlib.Path(sut.__file__).read_text(encoding="utf-8")
        function = source.split("def build_successor_epoch(", 1)[1].split(
            "\ndef _cross_shard_owner_evidence(", 1
        )[0]
        self.assertIn("durable_predecessor_todo", function)
        self.assertNotIn("live_documents[migration.TODO_REL].batches", function)
        self.assertIn(
            "semantic_contract,\n        durable_predecessor_todo,",
            function,
        )

    def test_document_components_bind_prefix_batches_and_suffix(self) -> None:
        batches = [{
            "families": ["familia"],
            "skip": 0,
            "take": 1,
            "n": 1,
            "area": "area",
            "file": "data/editorial/portfolio_v2/area.jsonl",
            "slug": "area-01",
        }]
        payload = (
            b"export const meta = {}\nconst batches = " +
            json.dumps(batches, separators=(", ", ": ")).encode("ascii") +
            b"\nexport default batches\n"
        )
        document, evidence = sut._document_components(payload, "fixture")
        self.assertEqual(document.batches, batches)
        self.assertEqual(evidence["batch_count"], 1)
        self.assertEqual(evidence["sha256"], hashlib.sha256(payload).hexdigest())

        changed = payload.replace(b"export default", b"// later\nexport default")
        _, changed_evidence = sut._document_components(changed, "changed")
        self.assertEqual(
            evidence["batches_sha256"], changed_evidence["batches_sha256"]
        )
        self.assertNotEqual(
            evidence["suffix_sha256"], changed_evidence["suffix_sha256"]
        )

    def test_all_stock_classifies_every_row_and_exposes_orphan(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wiki-all-stock-") as directory:
            root = pathlib.Path(directory)
            target = root / "data/editorial/v2_pages/area-01.jsonl"
            target.parent.mkdir(parents=True)
            target.write_text(
                '{"intent_id":"known"}\n'
                '{"intent_id":"orphan"}\n'
                '{"intent_id":"old","skipped":true}\n'
            )
            target.chmod(0o644)
            portfolio = sut.migration.PortfolioSnapshot(
                rel_path="data/editorial/portfolio_v2/area.jsonl",
                payload=b"",
                digest=hashlib.sha256(b"").hexdigest(),
                records=(),
                by_family={"family": ("known",)},
                family_by_intent={"known": "family"},
            )
            reconstructed = sut.ReconstructedInventory(
                batches=({
                    "families": ["family"], "skip": 0, "take": 1,
                    "n": 1, "area": "area",
                    "file": portfolio.rel_path, "slug": "area-01",
                },),
                portfolios={portfolio.rel_path: portfolio},
                aggregate_snapshots={}, counts={},
                archived_full_sha256="a" * 64,
                transformed_archived_full_sha256="b" * 64,
                transformed_batches_sha256="c" * 64,
            )
            semantic = mock.Mock(
                unresolved_intents=(), superseded_target_rel_paths={}
            )
            with mock.patch.object(
                    sut.migration, "_stock_paths", return_value=[target]), \
                    mock.patch.object(
                        queue, "load_writing_semantic_contract",
                        return_value=semantic,
                    ):
                evidence = sut._cross_shard_owner_evidence(
                    root, reconstructed
                )
            self.assertEqual(evidence["all_stock_rows"], 3)
            self.assertEqual(evidence["classified_rows"], 3)
            self.assertEqual(evidence["active_rows"], 2)
            self.assertEqual(evidence["tombstone_rows"], 1)
            self.assertEqual(evidence["unknown_or_orphan_active_rows"], 1)


class GitLineageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-migrecon-git-"))
        subprocess.run(
            ["/usr/bin/git", "init", "-q", str(self.root)], check=True
        )
        (self.root / "evidence").mkdir()
        (self.root / "evidence/a.txt").write_text("alpha\n")
        (self.root / "evidence/b.txt").write_text("beta\n")
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root),
                "add", "evidence/a.txt", "evidence/b.txt",
            ],
            check=True,
        )
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root),
                "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-q", "-m", "anchor evidence",
            ],
            check=True,
        )

    def tearDown(self) -> None:
        subprocess.run(
            ["/bin/chmod", "-R", "u+rwX", str(self.root)], check=True
        )
        for directory, children, files in os.walk(
                self.root, topdown=False, followlinks=False):
            for name in files:
                pathlib.Path(directory, name).unlink(missing_ok=True)
            for name in children:
                child = pathlib.Path(directory, name)
                if child.is_symlink():
                    child.unlink()
                else:
                    child.rmdir()
        self.root.rmdir()

    def test_head_blob_and_common_introduction_commit_are_exact(self) -> None:
        head = sut._git_head(self.root)
        payload = (self.root / "evidence/a.txt").read_bytes()
        evidence = sut._git_head_path_evidence(
            self.root, head, "evidence/a.txt", payload
        )
        self.assertTrue(evidence["anchored"])
        introduction = sut._introduction_commit(
            self.root, {"evidence/a.txt", "evidence/b.txt"}
        )
        self.assertEqual(introduction, head)
        self.assertEqual(
            sut._history_contains_sha256(
                self.root,
                "evidence/a.txt",
                hashlib.sha256(payload).hexdigest(),
            ),
            (head,),
        )

    def test_dirty_or_untracked_bytes_are_not_git_lineage(self) -> None:
        head = sut._git_head(self.root)
        path = self.root / "evidence/a.txt"
        path.write_text("changed\n")
        evidence = sut._git_head_path_evidence(
            self.root, head, "evidence/a.txt", path.read_bytes()
        )
        self.assertFalse(evidence["anchored"])
        self.assertEqual(
            evidence["reason"], "worktree_differs_from_head_blob"
        )
        untracked = b"not committed\n"
        evidence = sut._git_head_path_evidence(
            self.root, head, "evidence/untracked.txt", untracked
        )
        self.assertFalse(evidence["anchored"])
        self.assertEqual(evidence["reason"], "path_absent_from_head")

    def test_receipt_anchor_remains_valid_under_descendant_head(self) -> None:
        anchor = sut._git_head(self.root)
        graph = {
            "evidence/a.txt": hashlib.sha256(
                (self.root / "evidence/a.txt").read_bytes()
            ).hexdigest(),
            "evidence/never.txt": None,
        }
        (self.root / "later.txt").write_text("later\n")
        subprocess.run(
            ["/usr/bin/git", "-C", str(self.root), "add", "later.txt"],
            check=True,
        )
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root),
                "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-q", "-m", "descendant",
            ],
            check=True,
        )
        value = {"anchor_commit": anchor, "graph_sha256": graph}
        sut._validate_receipt_anchor(self.root, value)

        (self.root / "evidence/never.txt").write_text("later only\n")
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root), "add",
                "evidence/never.txt",
            ],
            check=True,
        )
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root),
                "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-q", "-m", "path appears after anchor",
            ],
            check=True,
        )
        with self.assertRaisesRegex(ValueError, "HEAD descendente"):
            sut._validate_receipt_anchor(self.root, value)

    def test_terminal_receipt_requires_exact_blob_in_descendant_head(self) -> None:
        anchor = sut._git_head(self.root)
        graph = {
            "evidence/a.txt": hashlib.sha256(
                (self.root / "evidence/a.txt").read_bytes()
            ).hexdigest(),
            "evidence/never.txt": None,
        }
        receipt_payload = b'{"terminal":true}\n'
        receipt = self.root / sut.RECEIPT_REL
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(receipt_payload)
        value = {"anchor_commit": anchor, "graph_sha256": graph}
        with self.assertRaisesRegex(ValueError, "blob exato"):
            sut._validate_receipt_anchor(
                self.root, value, receipt_payload=receipt_payload
            )
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root), "add",
                sut.RECEIPT_REL,
            ],
            check=True,
        )
        subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root),
                "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-q", "-m", "commit successor receipt",
            ],
            check=True,
        )
        sut._validate_receipt_anchor(
            self.root, value, receipt_payload=receipt_payload
        )

        receipt.write_bytes(b'{"terminal":false}\n')
        with self.assertRaisesRegex(ValueError, "blob exato"):
            sut._validate_receipt_anchor(
                self.root, value, receipt_payload=receipt.read_bytes()
            )

        unrelated_tree = subprocess.run(
            ["/usr/bin/git", "-C", str(self.root), "mktree"],
            input=b"", stdout=subprocess.PIPE, check=True,
        ).stdout.strip().decode("ascii")
        unrelated = subprocess.run(
            [
                "/usr/bin/git", "-C", str(self.root),
                "-c", "user.name=fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit-tree", unrelated_tree, "-m", "unrelated root",
            ],
            stdout=subprocess.PIPE, check=True,
        ).stdout.strip().decode("ascii")
        with mock.patch.object(sut, "_git_head", return_value=unrelated):
            with self.assertRaisesRegex(ValueError, "ancestral"):
                sut._validate_receipt_anchor(
                    self.root, value, receipt_payload=receipt_payload
                )


if __name__ == "__main__":
    unittest.main()
