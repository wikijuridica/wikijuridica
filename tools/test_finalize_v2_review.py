from __future__ import annotations

import base64
import contextlib
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).with_name("finalize-v2-review")


def load_finalizer():
    loader = importlib.machinery.SourceFileLoader(
        "finalize_v2_review_under_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("não foi possível carregar finalizer")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


FINALIZER = load_finalizer()


def encode_json(value) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


def queue_item() -> dict:
    return {
        "slug": "civil-01",
        "area": "civil",
        "n": 1,
        "target_sha256": "1" * 64,
        "defeitos": {"meta_len": 1},
        "alvos": {"meta_len": ["intent-a"]},
        "target_intent_ids": ["intent-a"],
        "review_target_intent_ids": ["intent-a"],
        "file_wide_review": False,
        "preserved_record_sha256": {},
        "distinctness_dependency_sha256": {
            "data/editorial/v2_pages/civil-02.jsonl": "2" * 64,
        },
    }


def command_summary(label: str, returncode: int = 0) -> dict:
    return {
        "label": label,
        "returncode": returncode,
        "duration_ms": 1,
        "stdout_sha256": "a" * 64,
        "stderr_sha256": "b" * 64,
    }


def local_audit_report() -> dict:
    return {
        "file": "../../proc/self/fd/9",
        "pages": 1,
        "active_pages": 1,
        "defects": {},
        "ok": True,
    }


def provenance_resolvable_local_audit_report() -> dict:
    report = local_audit_report()
    report["defects"] = {
        "official_source_verified_at_invalid": ["intent-a"],
        "official_source_http_status_invalid": ["intent-a"],
    }
    report["ok"] = False
    return report


def final_audit_report(target_digest: str = "4" * 64) -> dict:
    return {
        "file": "data/editorial/v2_pages/civil-01.jsonl",
        "pages": 1,
        "active_pages": 1,
        "defects": {},
        "ok": True,
        "distinctness_neighbors": [],
        "distinctness_index": {
            "status": "ready",
            "schema_version": 3,
            "target_digest": target_digest,
            "generation_root": "5" * 64,
            "stock_root": "6" * 64,
            "algorithm_fingerprint": (
                FINALIZER.EXPECTED_INCREMENTAL_ALGORITHM_FINGERPRINT),
            "stock_shards_verified": 1,
            "overlay_shards_parsed": 0,
            "overlay_pages": 0,
            "stock_pages_indexed": 1,
            "stock_bytes_hashed": 0,
            "stock_metadata_scanned": 2,
            "profiles_loaded": 0,
            "candidates_compared": 0,
            "stock_candidates_compared": 0,
            "local_pairs_compared": 0,
            "local_ngram_adjudications": [],
            "candidate_terms_read": 0,
            "postings_scanned": 0,
            "inventory_complete": True,
            "candidate_routing_complete": True,
            "local_routing_complete": True,
            "target_snapshot_bound": True,
            "visible_surface_scope_complete": True,
            "visible_surfaces": list(
                FINALIZER.auditor_contract.INCREMENTAL_VISIBLE_SURFACES),
            "candidate_generation": (
                FINALIZER.auditor_contract.INCREMENTAL_CANDIDATE_GENERATION),
            "exact_adjudication": (
                FINALIZER.auditor_contract.INCREMENTAL_EXACT_ADJUDICATION),
            "publication_allowed": False,
            "index_policy": "noindex",
        },
    }


def canonical_workspace(task: dict) -> pathlib.Path:
    return FINALIZER.producer.create_workflow_workspace(
        task["slug"], task["target_sha256"])


def v3_queue_item() -> dict:
    target = {"shard": "data/editorial/v2_pages/civil-01.jsonl",
              "intent_id": "intent-a"}
    peer = {"shard": "data/editorial/v2_pages/civil-02.jsonl",
            "intent_id": "intent-b"}
    item = queue_item()
    item["defeitos"] = {"title_dup_global": 1}
    item["alvos"] = {"title_dup_global": ["intent-a~intent-b"]}
    item["distinctness_dependency_sha256"] = {
        peer["shard"]: "2" * 64,
    }
    item["evidencias_distinctness"] = {
        "title_dup_global": [{
            "type": "issue",
            "code": "title_dup_global",
            "left": target,
            "right": peer,
            "field": "title",
            "candidate_reasons": ["title"],
            "publication_allowed": False,
            "index_policy": "noindex",
            "projection_target": target,
            "projection_peer": peer,
        }],
    }
    item["componentes_distinctness"] = {
        "title_dup_global": [{
            "projection_target": target,
            "preserved_owner": peer,
            "component_id": "3" * 64,
            "member_count": 2,
        }],
    }
    item["distinctness_epoch"] = {
        "mode": FINALIZER.producer.GLOBAL_DISTINCTNESS_MODE,
        "schema_version": 1,
        "algorithm_fingerprint": (
            FINALIZER.EXPECTED_INCREMENTAL_ALGORITHM_FINGERPRINT),
        "batch_fingerprint": FINALIZER.EXPECTED_GLOBAL_BATCH_FINGERPRINT,
        "generation_root": "4" * 64,
        "stock_root": "5" * 64,
        "authenticated_shards": 2,
        "publication_allowed": False,
        "index_policy": "noindex",
    }
    return item


class FinalizerContractTest(unittest.TestCase):
    def test_base64_json_rejects_duplicate_keys(self):
        payload = base64.b64encode(b'{"slug":1,"slug":2}').decode("ascii")
        with self.assertRaises(FINALIZER.FinalizationError):
            FINALIZER._decode_base64_json(payload, "queue-item")

    def test_task_and_corrections_are_bound_to_queue(self):
        task = FINALIZER._validate_task(queue_item())
        self.assertEqual(
            FINALIZER._bounded_corrections({"meta_len": 1}, task),
            {"meta_len": 1},
        )
        for unsafe in ({}, {"title_len": 1}, {"meta_len": 0},
                       {"meta_len": 2}, {"meta_len": True}):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(FINALIZER.FinalizationError):
                    FINALIZER._bounded_corrections(unsafe, task)

    def test_task_rejects_forged_editable_scope_and_open_defect_projection(self):
        forged = queue_item()
        forged["target_intent_ids"] = ["intent-a", "intent-b"]
        forged["n"] = 2
        forged["review_target_intent_ids"] = ["intent-a", "intent-b"]
        forged["preserved_record_sha256"] = {}
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "escopo editável"):
            FINALIZER._validate_task(forged)

        divergent = queue_item()
        divergent["defeitos"]["meta_len"] = 2
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "projeções exatas"):
            FINALIZER._validate_task(divergent)

    def test_file_wide_requires_closed_producer_allowlist(self):
        unknown = queue_item()
        unknown["defeitos"] = {"mystery_file_problem": 1}
        unknown["alvos"] = {"mystery_file_problem": ["arquivo_inteiro"]}
        unknown["file_wide_review"] = True
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "record-level"):
            FINALIZER._validate_task(unknown)

        allowed = queue_item()
        allowed["defeitos"] = {"json_invalido": 1}
        allowed["alvos"] = {"json_invalido": ["linha_1"]}
        allowed["file_wide_review"] = True
        self.assertEqual(
            FINALIZER._validate_task(allowed)["file_wide_review"], True)

        malformed = json.loads(json.dumps(allowed))
        malformed["alvos"]["json_invalido"] = ["qualquer-coisa"]
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "allowlist"):
            FINALIZER._validate_task(malformed)

    def test_v3_evidence_component_epoch_and_peer_are_closed(self):
        valid = v3_queue_item()
        self.assertEqual(
            FINALIZER._validate_task(valid)["distinctness_epoch"]
            ["authenticated_shards"], 2)

        mutations = []
        evidence_null = json.loads(json.dumps(valid))
        evidence_null["evidencias_distinctness"]["title_dup_global"] = [None]
        mutations.append(evidence_null)
        component_null = json.loads(json.dumps(valid))
        component_null["componentes_distinctness"]["title_dup_global"] = [None]
        mutations.append(component_null)
        epoch_zero = json.loads(json.dumps(valid))
        epoch_zero["distinctness_epoch"]["authenticated_shards"] = 0
        mutations.append(epoch_zero)
        wrong_projection = json.loads(json.dumps(valid))
        wrong_projection["evidencias_distinctness"]["title_dup_global"][0][
            "projection_target"]["shard"] = (
                "data/editorial/v2_pages/civil-03.jsonl")
        mutations.append(wrong_projection)
        missing_peer = json.loads(json.dumps(valid))
        missing_peer["distinctness_dependency_sha256"] = {}
        mutations.append(missing_peer)
        for unsafe in mutations:
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(FINALIZER.FinalizationError):
                    FINALIZER._validate_task(unsafe)

    def test_workspace_is_bound_to_slug_snapshot_tmp_and_inode(self):
        task = queue_item()
        with tempfile.TemporaryDirectory() as arbitrary:
            os.chmod(arbitrary, 0o700)
            with self.assertRaisesRegex(
                    FINALIZER.FinalizationError, "namespace privado"):
                FINALIZER._open_workspace(task, arbitrary)

        workspace = canonical_workspace(task)
        moved = workspace.with_name(workspace.name + "_moved")
        replacement = None
        binding = None
        try:
            binding = FINALIZER._open_workspace(task, str(workspace))
            workspace.rename(moved)
            workspace.mkdir(mode=0o700)
            replacement = workspace
            with self.assertRaisesRegex(
                    FINALIZER.FinalizationError, "trocado"):
                FINALIZER._assert_workspace_binding(binding)
        finally:
            if binding is not None:
                os.close(binding.descriptor)
            if replacement is not None:
                shutil.rmtree(replacement, ignore_errors=True)
            shutil.rmtree(moved, ignore_errors=True)

    def test_memfd_payload_is_sealed_against_toctou(self):
        payload = b'{"intent_id":"intent-a"}\n'
        descriptor = FINALIZER._immutable_payload_fd(payload)
        try:
            self.assertEqual(os.pread(descriptor, len(payload), 0), payload)
            with self.assertRaises(OSError):
                os.write(descriptor, b"x")
        finally:
            os.close(descriptor)

    def test_dependency_identity_detects_same_digest_aba(self):
        with tempfile.TemporaryDirectory() as temporary:
            dependency = pathlib.Path(temporary) / "peer.jsonl"
            dependency.write_bytes(b"peer\n")
            expected = FINALIZER.hashlib.sha256(b"peer\n").hexdigest()
            epoch = {dependency: expected}
            identities = FINALIZER._capture_dependency_identities(epoch)
            current = dependency.stat().st_mtime_ns
            os.utime(dependency, ns=(current + 1_000_000, current + 1_000_000))
            with self.assertRaisesRegex(
                    FINALIZER.FinalizationError, "ABA"):
                FINALIZER._assert_dependency_identities(epoch, identities)

    def test_target_and_peer_locks_precede_global_locks_in_sorted_order(self):
        observed = []
        next_fd = iter(range(100, 110))

        def fake_open(path):
            observed.append(str(path))
            return next(next_fd)

        with (
            mock.patch.object(FINALIZER, "_open_lock", side_effect=fake_open),
            mock.patch.object(FINALIZER.os, "close"),
        ):
            stack = FINALIZER._lock_set("civil-02", {
                "data/editorial/v2_pages/civil-03.jsonl": "3" * 64,
                "data/editorial/v2_pages/civil-01.jsonl": "1" * 64,
            })
            stack.close()
        self.assertEqual(observed, [
            "/tmp/opt-wiki-v2-civil-01.transaction.lock",
            "/tmp/opt-wiki-v2-civil-02.transaction.lock",
            "/tmp/opt-wiki-v2-civil-03.transaction.lock",
        ])

    def test_final_audit_must_bind_exact_target_and_complete_epoch(self):
        task = queue_item()
        report = final_audit_report("9" * 64)
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "target_digest"):
            FINALIZER._validate_final_audit(report, task, "4" * 64)
        report = final_audit_report()
        report["distinctness_index"]["inventory_complete"] = False
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError,
                "snapshot_or_inventory_incomplete"):
            FINALIZER._validate_final_audit(report, task, "4" * 64)

    def test_final_audit_projection_rejects_schema_algorithm_scope_and_budget(self):
        task = queue_item()
        mutations = {
            "schema": ("schema_version", 2, "schema_version"),
            "algorithm": ("algorithm_fingerprint", "7" * 64,
                          "algorithm_fingerprint"),
            "scope": ("visible_surfaces", ["title"],
                      "visible_surface_scope"),
            "counter": ("stock_metadata_scanned", -1,
                        "counter:stock_metadata_scanned"),
            "status": ("status", "stale", "projection_status"),
        }
        for name, (field, value, expected) in mutations.items():
            with self.subTest(name=name):
                report = final_audit_report()
                report["distinctness_index"][field] = value
                with self.assertRaisesRegex(
                        FINALIZER.FinalizationError, expected):
                    FINALIZER._validate_final_audit(
                        report, task, "4" * 64)

    def test_pre_provenance_audit_rejects_nonresolvable_blocker(self):
        task = queue_item()
        payload = (
            b'{"intent_id":"intent-a","official_sources":'
            b'[{"url":"https://www.planalto.gov.br/x"}]}\n')
        report = provenance_resolvable_local_audit_report()
        report["defects"]["fontes_min"] = ["intent-a"]
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "não resolvível"):
            FINALIZER._validate_pre_provenance_audit(report, task, payload)

    def test_pre_provenance_audit_cannot_edit_preserved_intent(self):
        task = queue_item()
        task["review_target_intent_ids"] = ["intent-b"]
        payload = (
            b'{"intent_id":"intent-a","official_sources":'
            b'[{"url":"https://www.planalto.gov.br/x"}]}\n')
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "ampliar escopo"):
            FINALIZER._validate_pre_provenance_audit(
                provenance_resolvable_local_audit_report(), task, payload)

    def test_source_provenance_binding_requires_exact_checked_sidecar(self):
        relative = (
            "data/source-registry/"
            "v2_source_provenance_live_evidence_sets/"
            f"exact-{'e' * 64}.jsonl")
        stdout = (
            "v2-source-provenance: check=current-selection-pass "
            "release_eligible=false scope=all records=2 verified=2 "
            f"blocked=0 path={relative} publication=false\n").encode()
        snapshot = FINALIZER.producer.RegularFileSnapshot(
            b'{"evidence":true}\n', "f" * 64)
        with mock.patch.object(
                FINALIZER.producer, "read_regular_file_snapshot",
                return_value=snapshot) as capture:
            binding = FINALIZER._source_provenance_evidence_binding(stdout)
        self.assertEqual(binding, {"path": relative, "sha256": "f" * 64})
        capture.assert_called_once_with(
            FINALIZER.INSTALL_ROOT / relative, max_bytes=16 * 1024 * 1024)
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "binding"):
            FINALIZER._source_provenance_evidence_binding(
                stdout.replace(b"exact-", b"foreign-"))

    def test_queue_envelope_binds_item_fingerprint_and_rca(self):
        item = queue_item()
        item["queue_item_sha256"] = FINALIZER._queue_item_fingerprint(item)
        payload = (
            "const REVIEW_QUEUE_OPERATIONAL_RCA = null\n" +
            "const files = " + json.dumps(
                [item], ensure_ascii=False, sort_keys=True,
                separators=(",", ":")) + "\n"
        ).encode("utf-8")
        parsed = FINALIZER._parse_queue_payload(payload, "civil-01")
        self.assertEqual(parsed["queue_item_sha256"],
                         item["queue_item_sha256"])

        changed = json.loads(json.dumps(item))
        changed["area"] = "consumidor"
        unsafe_payload = (
            "const REVIEW_QUEUE_OPERATIONAL_RCA = null\n" +
            "const files = " + json.dumps([changed]) + "\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "fingerprint"):
            FINALIZER._parse_queue_payload(unsafe_payload, "civil-01")

        rca_payload = payload.replace(
            b"REVIEW_QUEUE_OPERATIONAL_RCA = null",
            b'REVIEW_QUEUE_OPERATIONAL_RCA = {"code":"stale"}')
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "RCA operacional"):
            FINALIZER._parse_queue_payload(rca_payload, "civil-01")

    def test_cli_invalid_input_is_fail_closed_json(self):
        process = subprocess.run(
            [str(SCRIPT), "--queue-item-base64", "!!!",
             "--workspace", "/tmp/no-workspace",
             "--staged-sha256", "0" * 64,
             "--corrections-base64", encode_json({"meta_len": 1})],
            cwd=SCRIPT.parent.parent, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=10,
        )
        self.assertEqual(process.returncode, 2)
        result = json.loads(process.stdout)
        self.assertIs(result["audit_ok"], False)
        self.assertIs(result["mutation_applied"], False)
        self.assertIs(result["publication_allowed"], False)
        self.assertEqual(result["index_policy"], "noindex")

    def test_cli_valid_base64_item_still_cannot_authorize_mutation(self):
        process = subprocess.run(
            [str(SCRIPT), "--queue-item-base64", encode_json(queue_item()),
             "--workspace", "/tmp/wiki-v2-civil-01-111111111111-forged1",
             "--staged-sha256", "3" * 64,
             "--corrections-base64", encode_json({"meta_len": 1})],
            cwd=SCRIPT.parent.parent, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=10,
        )
        self.assertEqual(process.returncode, 2)
        result = json.loads(process.stdout)
        self.assertIs(result["audit_ok"], False)
        self.assertIs(result["mutation_applied"], False)
        self.assertIn("artefato canônico", result["error"])

    def test_receipt_is_create_only(self):
        task = queue_item()
        workspace = canonical_workspace(task)
        binding = None
        reservation = None
        try:
            binding = FINALIZER._open_workspace(task, str(workspace))
            reservation = FINALIZER._reserve_receipt(binding)
            receipt = {"schema_version": 1, "audit_ok": False}
            path, digest = FINALIZER._write_receipt(
                binding, reservation, receipt)
            self.assertEqual(
                FINALIZER.producer.snapshot_sha256(path), digest)
            with self.assertRaisesRegex(
                    FINALIZER.FinalizationError, "evoluiu"):
                FINALIZER._write_receipt(binding, reservation, receipt)
            with self.assertRaises(FileExistsError):
                FINALIZER._reserve_receipt(binding)
        finally:
            if reservation is not None:
                os.close(reservation.descriptor)
            if binding is not None:
                os.close(binding.descriptor)
            shutil.rmtree(workspace, ignore_errors=True)

    def test_live_scope_rejects_provenance_change_outside_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = pathlib.Path(temporary) / "civil-01.jsonl"
            first = b'{"intent_id":"intent-a","value":1}'
            second = b'{"intent_id":"intent-b","value":2}'
            target.write_bytes(first + b"\n" + second + b"\n")
            task = {
                "target_intent_ids": ["intent-a", "intent-b"],
                "preserved_record_sha256": {
                    "intent-b": FINALIZER.hashlib.sha256(second).hexdigest(),
                },
            }
            digest = FINALIZER.producer.snapshot_sha256(target)
            FINALIZER._verify_live_review_scope(task, target, digest)
            changed = b'{"intent_id":"intent-b","value":3}'
            target.write_bytes(first + b"\n" + changed + b"\n")
            changed_digest = FINALIZER.producer.snapshot_sha256(target)
            with self.assertRaisesRegex(
                    FINALIZER.FinalizationError, "registro preservado"):
                FINALIZER._verify_live_review_scope(
                    task, target, changed_digest)

    def test_timeout_kills_descendant_process_group(self):
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = pathlib.Path(temporary) / "orphan-wrote"
            child = (
                "import pathlib,time; time.sleep(2); "
                f"pathlib.Path({str(sentinel)!r}).write_text('orphan')"
            )
            parent = (
                "import subprocess,time; "
                f"subprocess.Popen(['python3','-c',{child!r}]); "
                "time.sleep(20)"
            )
            with self.assertRaisesRegex(
                    FINALIZER.FinalizationError, "process group encerrado"):
                FINALIZER._run(
                    ["python3", "-c", parent], timeout_seconds=1,
                    label="timeout-test")
            time.sleep(2.25)
            self.assertFalse(
                sentinel.exists(), "descendente sobreviveu ao timeout")

    def test_kill_process_group_reaps_descendants_after_leader_exited(self):
        process = mock.Mock()
        process.pid = 54321
        process.poll.return_value = 0
        process.wait.return_value = 0
        with mock.patch.object(FINALIZER.os, "killpg") as killpg:
            FINALIZER._kill_process_group(process)
        self.assertEqual(killpg.call_args_list, [
            mock.call(54321, FINALIZER.signal.SIGTERM),
            mock.call(54321, 0),
            mock.call(54321, FINALIZER.signal.SIGKILL),
        ])
        process.wait.assert_called_once_with(timeout=5)

    def test_run_accepts_only_explicit_nonzero_returncode(self):
        stdout, summary = FINALIZER._run(
            ["python3", "-c", "import sys; sys.exit(1)"],
            timeout_seconds=5, label="accepted-one",
            accepted_returncodes=(0, 1))
        self.assertEqual(stdout, b"")
        self.assertEqual(summary["returncode"], 1)
        with self.assertRaisesRegex(FINALIZER.FinalizationError, "exit=1"):
            FINALIZER._run(
                ["python3", "-c", "import sys; sys.exit(1)"],
                timeout_seconds=5, label="rejected-one")

    def test_run_kills_unbounded_output_at_memory_cap(self):
        command = (
            "import os\n"
            "chunk=b'x'*65536\n"
            "while True: os.write(1,chunk)\n"
        )
        with self.assertRaisesRegex(
                FINALIZER.FinalizationError, "output excedeu limite"):
            FINALIZER._run(
                ["python3", "-c", command], timeout_seconds=10,
                label="unbounded-output")

    def test_preexisting_receipt_fails_before_audit_or_cas(self):
        task = queue_item()
        task["queue_item_sha256"] = FINALIZER._queue_item_fingerprint(task)
        workspace = canonical_workspace(task)
        (workspace / "finalizer-receipt.json").write_text("occupied")
        args = mock.Mock(
            queue_file="/opt/wiki/scripts/workflows/writing-review-todo.js",
            queue_item_base64=None,
            slug="civil-01",
            workspace=str(workspace),
            staged_sha256="3" * 64,
            corrections_base64=encode_json({"meta_len": 1}),
        )
        staged = FINALIZER.producer.RegularFileSnapshot(
            b'{"intent_id":"intent-a","official_sources":'
            b'[{"url":"https://www.planalto.gov.br/ccivil_03/leis/'
            b'l8078compilado.htm"}]}\n', "3" * 64)
        try:
            with (
                mock.patch.object(
                    FINALIZER, "_load_queue_item",
                    return_value=(task, "8" * 64)),
                mock.patch.object(FINALIZER, "_verify_staged",
                                  return_value=staged),
                mock.patch.object(FINALIZER, "_run") as run,
                mock.patch.object(
                    FINALIZER.producer, "atomic_replace_cas") as cas,
            ):
                result, exit_code = FINALIZER.finalize(args)
            self.assertEqual(exit_code, 2)
            self.assertIs(result["audit_ok"], False)
            self.assertIs(result["mutation_applied"], False)
            run.assert_not_called()
            cas.assert_not_called()
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_cas_exception_after_exchange_is_reported_as_mutation(self):
        task = queue_item()
        task["queue_item_sha256"] = FINALIZER._queue_item_fingerprint(task)
        workspace = canonical_workspace(task)
        args = mock.Mock(
            queue_file="/opt/wiki/scripts/workflows/writing-review-todo.js",
            queue_item_base64=None,
            slug="civil-01",
            workspace=str(workspace),
            staged_sha256="3" * 64,
            corrections_base64=encode_json({"meta_len": 1}),
        )
        staged = FINALIZER.producer.RegularFileSnapshot(
            b'{"intent_id":"intent-a","official_sources":'
            b'[{"url":"https://www.planalto.gov.br/ccivil_03/leis/'
            b'l8078compilado.htm"}]}\n', "3" * 64)
        try:
            with (
                mock.patch.object(
                    FINALIZER, "_load_queue_item",
                    return_value=(task, "8" * 64)),
                mock.patch.object(FINALIZER, "_verify_staged",
                                  return_value=staged),
                mock.patch.object(
                    FINALIZER, "_run",
                    return_value=(
                        json.dumps(local_audit_report()).encode(),
                        command_summary("staged-local-audit"))),
                mock.patch.object(FINALIZER, "_lock_set",
                                  return_value=contextlib.ExitStack()),
                mock.patch.object(FINALIZER, "_resource_lock",
                                  return_value=contextlib.ExitStack()),
                mock.patch.object(
                    FINALIZER, "_capture_dependency_identities",
                    return_value={}),
                mock.patch.object(
                    FINALIZER, "_assert_relational_dependency_bindings"),
                mock.patch.object(
                    FINALIZER.producer, "atomic_replace_cas",
                    side_effect=RuntimeError("exchange installed then failed")),
                mock.patch.object(
                    FINALIZER.producer, "snapshot_sha256",
                    return_value="3" * 64),
            ):
                result, exit_code = FINALIZER.finalize(args)
            self.assertEqual(exit_code, 2)
            self.assertIs(result["audit_ok"], False)
            self.assertIs(result["mutation_applied"], True, result)
            self.assertEqual(
                result["observed_after_failure_sha256"], "3" * 64)
            self.assertTrue(pathlib.Path(result["receipt_path"]).is_file())
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_success_path_promotes_once_then_audits_serially(self):
        task = queue_item()
        task["queue_item_sha256"] = FINALIZER._queue_item_fingerprint(task)
        workspace = canonical_workspace(task)
        args = mock.Mock(
            queue_file="/opt/wiki/scripts/workflows/writing-review-todo.js",
            queue_item_base64=None,
            slug="civil-01",
            workspace=str(workspace),
            staged_sha256="3" * 64,
            corrections_base64=encode_json({"meta_len": 1}),
        )
        staged = FINALIZER.producer.RegularFileSnapshot(
            b'{"intent_id":"intent-a","official_sources":'
            b'[{"url":"https://www.planalto.gov.br/ccivil_03/leis/'
            b'l8078compilado.htm"}]}\n', "3" * 64)
        local_summary = command_summary("staged-local-audit", returncode=1)
        final_summary = command_summary("final-against-stock-audit")
        run_results = [
            (json.dumps(provenance_resolvable_local_audit_report()).encode(),
             local_summary),
            (json.dumps(final_audit_report()).encode(), final_summary),
        ]
        try:
            with (
                mock.patch.object(
                    FINALIZER, "_load_queue_item",
                    return_value=(task, "8" * 64)),
                mock.patch.object(FINALIZER, "_verify_staged",
                                  return_value=staged) as verify,
                mock.patch.object(FINALIZER, "_run",
                                  side_effect=run_results) as run,
                mock.patch.object(FINALIZER, "_lock_set",
                                  return_value=contextlib.ExitStack()),
                mock.patch.object(FINALIZER, "_resource_lock",
                                  return_value=contextlib.ExitStack()),
                mock.patch.object(
                    FINALIZER, "_source_provenance",
                    return_value=(
                        [
                            command_summary("source-provenance-plan"),
                            command_summary("source-provenance-live-all"),
                            command_summary("source-provenance-check"),
                        ],
                        {
                            "path": (
                                "data/source-registry/"
                                "v2_source_provenance_live_evidence_sets/"
                                f"exact-{'e' * 64}.jsonl"),
                            "sha256": "f" * 64,
                        },
                    )),
                mock.patch.object(FINALIZER, "_verify_live_review_scope"),
                mock.patch.object(
                    FINALIZER, "_capture_dependency_identities",
                    return_value={}),
                mock.patch.object(FINALIZER, "_assert_dependency_identities"),
                mock.patch.object(
                    FINALIZER.producer, "atomic_replace_cas") as cas,
                mock.patch.object(
                    FINALIZER.producer, "snapshot_sha256",
                    side_effect=["3" * 64, "4" * 64, "4" * 64]),
            ):
                result, exit_code = FINALIZER.finalize(args)
            self.assertEqual(exit_code, 0, result)
            self.assertIs(result["audit_ok"], True)
            self.assertIs(result["mutation_applied"], True)
            self.assertEqual(result["audited_sha256"], "4" * 64)
            self.assertRegex(result["receipt_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(verify.call_count, 3)
            self.assertEqual(run.call_count, 2)
            first_command = run.call_args_list[0].args[0]
            self.assertRegex(first_command[5], r"^/proc/self/fd/[0-9]+$")
            self.assertEqual(len(run.call_args_list[0].kwargs["pass_fds"]), 1)
            cas.assert_called_once()
            receipt_payload = json.loads(
                pathlib.Path(result["receipt_path"]).read_text())
            self.assertNotIn("error", receipt_payload)
            self.assertEqual(receipt_payload["promoted_sha256"], "3" * 64)
            self.assertEqual(
                set(receipt_payload["pre_provenance_defects"]), {
                    "official_source_verified_at_invalid",
                    "official_source_http_status_invalid",
                })
        finally:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
