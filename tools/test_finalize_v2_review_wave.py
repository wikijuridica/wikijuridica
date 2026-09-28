from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import tempfile
import unittest

from tools import generate_v2_review_queue as producer
from tools.test_generate_v2_review_queue_distinctness_v3 import (
    endpoint,
    symmetric_report,
)


SCRIPT = pathlib.Path(__file__).with_name("finalize-v2-review-wave")


def load_wave_finalizer():
    loader = importlib.machinery.SourceFileLoader(
        "finalize_v2_review_wave_under_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("não foi possível carregar finalizador de wave")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


WAVE = load_wave_finalizer()


def load_verifier():
    path = pathlib.Path(__file__).with_name("verify-v2-workflow-results")
    loader = importlib.machinery.SourceFileLoader(
        "verify_v2_workflow_results_for_wave_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("não foi possível carregar verificador")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


VERIFY = load_verifier()


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def bound_tasks(target_count: int = 2):
    owner = (
        "data/editorial/v2_pages/civil-owner.jsonl", "owner-intent")
    targets = tuple(
        (f"data/editorial/v2_pages/civil-target-{index:02d}.jsonl",
         f"target-intent-{index:02d}")
        for index in range(target_count))
    nodes = (owner,) + targets
    report = symmetric_report(nodes, [
        ("title_dup_global", owner, target) for target in targets
    ])
    todo = producer.build_todo(
        report, set(), {}, {node: 1 for node in nodes}, set(report["files"]))
    selected, cohorts, deferred = producer.select_review_wave_epoch(todo, 24)
    if deferred:
        raise AssertionError("fixture não deveria deferir")
    stock = {node[0]: digest(node[0]) for node in nodes}
    epoch = {
        "mode": producer.GLOBAL_DISTINCTNESS_MODE,
        "schema_version": 1,
        "algorithm_fingerprint":
            WAVE.single.EXPECTED_INCREMENTAL_ALGORITHM_FINGERPRINT,
        "batch_fingerprint": WAVE.single.EXPECTED_GLOBAL_BATCH_FINGERPRINT,
        "generation_root": digest("generation"),
        "stock_root": digest("stock"),
        "authenticated_shards": len(nodes),
        "publication_allowed": False,
        "index_policy": "noindex",
    }
    target_intent_by_path = {path: intent for path, intent in targets}
    for item in selected:
        path = f"data/editorial/v2_pages/{item['slug']}.jsonl"
        item["target_sha256"] = stock[path]
        item["distinctness_dependency_sha256"] = {
            dependency: stock[dependency]
            for dependency in item.pop("distinctness_dependency_paths")
        }
        item["distinctness_epoch"] = epoch
        for components in item["componentes_distinctness"].values():
            for component in components:
                component.pop("dependency_paths", None)
        intent = target_intent_by_path[path]
        item["target_intent_ids"] = [intent]
        item["review_target_intent_ids"] = [intent]
        item["file_wide_review"] = False
        item["preserved_record_sha256"] = {}
    selected = producer.bind_exact_component_waves(
        selected, cohorts, stock, epoch)
    for item in selected:
        item["queue_item_sha256"] = producer.review_queue_item_sha256(item)
    return owner, targets, selected, cohorts, stock, epoch


def valid_receipt(tasks, queue_sha: str):
    paths = sorted(
        f"data/editorial/v2_pages/{task['slug']}.jsonl" for task in tasks)
    contract = tasks[0]["exact_component_wave"]
    post = {path: digest("post:" + path) for path in paths}
    receipt = {
        "schema_version": WAVE.RECEIPT_SCHEMA,
        "wave_id": contract["wave_id"],
        "group_id": contract["group_id"],
        "cohort_index": contract["cohort_index"],
        "cohort_count": contract["cohort_count"],
        "member_paths": paths,
        "component_ids": contract["component_ids"],
        "preserved_owners": contract["preserved_owners"],
        "queue_artifact_sha256": queue_sha,
        "queue_item_sha256_by_path": {
            path: next(task["queue_item_sha256"] for task in tasks
                       if path.endswith(f"/{task['slug']}.jsonl"))
            for path in paths
        },
        "corrigidos_por_classe_by_path": {
            path: {"title_dup_global": 1} for path in paths
        },
        "pre_sha256_by_path": {
            path: contract["member_pre_sha256"][path] for path in paths
        },
        "staged_sha256_by_path": {
            path: digest("staged:" + path) for path in paths
        },
        "post_sha256_by_path": post,
        "source_provenance_evidence_by_path": {
            path: {
                "path": (
                    "data/source-registry/"
                    "v2_source_provenance_live_evidence_sets/exact-" +
                    digest("evidence-path:" + path) + ".jsonl"),
                "sha256": digest("evidence:" + path),
            }
            for path in paths
        },
        "audit_report_sha256_by_path": {
            path: digest("audit:" + path) for path in paths
        },
        "distinctness_generation_root_by_path": {
            path: digest("generation:" + path) for path in paths
        },
        "journal_path": "/tmp/wiki-v2-wave/exact-component-wave-journal.jsonl",
        "journal_sha256": digest("journal"),
        "commands_by_path": {path: [] for path in paths},
        "pre_provenance_defects_by_path": {path: {} for path in paths},
        "audit_ok": True,
        "mutation_applied": True,
        "publication_allowed": False,
        "index_policy": "noindex",
    }
    return receipt, post


class ExactComponentWaveFinalizerTest(unittest.TestCase):
    def test_bound_queue_covers_every_member_and_single_finalizer_refuses_it(self):
        _, targets, tasks, _, stock, _ = bound_tasks(3)
        self.assertEqual(len(tasks), 3)
        wave_ids = {
            task["exact_component_wave"]["wave_id"] for task in tasks
        }
        self.assertEqual(len(wave_ids), 1)
        member_paths = {target[0] for target in targets}
        for task in tasks:
            path = f"data/editorial/v2_pages/{task['slug']}.jsonl"
            self.assertEqual(
                set(task["exact_component_wave"]["member_paths"]),
                member_paths)
            self.assertEqual(
                task["exact_component_wave"]["member_pre_sha256"],
                {member: stock[member] for member in member_paths})
            self.assertTrue(
                (member_paths - {path}).issubset(
                    task["distinctness_dependency_sha256"]))
            with self.assertRaisesRegex(
                    WAVE.single.FinalizationError,
                    "finalize-v2-review-wave"):
                WAVE.single._validate_task(task)
        validated, contract = WAVE.validate_wave_tasks(
            tasks, next(iter(wave_ids)))
        self.assertEqual(
            [task["slug"] for task in validated],
            [pathlib.PurePosixPath(path).stem for path in sorted(member_paths)])
        self.assertEqual(set(contract["member_paths"]), member_paths)

    def test_planned_a_postimage_does_not_make_b_stale(self):
        pre = {"a": digest("pre-a"), "b": digest("pre-b")}
        staged = {"a": digest("staged-a"), "b": digest("staged-b")}
        observed = {"a": staged["a"], "b": pre["b"]}
        self.assertEqual(
            WAVE.classify_wave_states(pre, staged, observed),
            {"a": "installed", "b": "pending"})

    def test_external_drift_fails_closed(self):
        pre = {"a": digest("pre-a"), "b": digest("pre-b")}
        staged = {"a": digest("staged-a"), "b": digest("staged-b")}
        with self.assertRaisesRegex(WAVE.WaveError, "drift externo"):
            WAVE.classify_wave_states(
                pre, staged, {"a": staged["a"], "b": digest("foreign")})

    def test_missing_draft_member_fails_before_mutation(self):
        _, _, tasks, _, _, _ = bound_tasks(2)
        complete = [{
            "slug": task["slug"],
            "workspace": f"/tmp/{task['slug']}",
            "staged_sha256": digest("staged:" + task["slug"]),
            "corrigidos_por_classe": {"title_dup_global": 1},
        } for task in tasks]
        self.assertEqual(
            len(WAVE.validate_draft_manifest(complete, tasks)), 2)
        with self.assertRaisesRegex(WAVE.WaveError, "wave inteira"):
            WAVE.validate_draft_manifest(complete[:-1], tasks)

    def test_forged_or_incomplete_wave_receipt_fails(self):
        _, _, tasks, _, _, _ = bound_tasks(2)
        queue_sha = digest("queue")
        wave_id = tasks[0]["exact_component_wave"]["wave_id"]
        receipt, current = valid_receipt(tasks, queue_sha)
        self.assertEqual(
            WAVE.validate_wave_receipt(
                receipt, wave_id=wave_id,
                queue_artifact_sha256=queue_sha,
                current_sha256_by_path=current),
            receipt)

        forged = copy.deepcopy(receipt)
        first = forged["member_paths"][0]
        forged["post_sha256_by_path"][first] = digest("forged")
        with self.assertRaisesRegex(WAVE.WaveError, "forjado/stale"):
            WAVE.validate_wave_receipt(
                forged, wave_id=wave_id,
                queue_artifact_sha256=queue_sha,
                current_sha256_by_path=current)

        incomplete = copy.deepcopy(receipt)
        incomplete["source_provenance_evidence_by_path"].pop(first)
        with self.assertRaisesRegex(WAVE.WaveError, "identidade inválida"):
            WAVE.validate_wave_receipt(
                incomplete, wave_id=wave_id,
                queue_artifact_sha256=queue_sha)

    def test_wave_id_is_recomputed_not_trusted(self):
        _, _, tasks, _, _, _ = bound_tasks(2)
        forged = copy.deepcopy(tasks)
        forged_id = digest("forged-wave")
        for task in forged:
            task["exact_component_wave"]["wave_id"] = forged_id
            task["queue_item_sha256"] = producer.review_queue_item_sha256(task)
        with self.assertRaisesRegex(WAVE.WaveError, "não autentica"):
            WAVE.validate_wave_tasks(forged, forged_id)

    def test_collective_receipt_is_consumable_by_external_verifier(self):
        _, _, tasks, _, _, _ = bound_tasks(2)
        queue_sha = digest("queue-artifact")
        receipt, _ = valid_receipt(tasks, queue_sha)
        paths = receipt["member_paths"]
        coordinator = next(
            task for task in tasks
            if paths[0].endswith(f"/{task['slug']}.jsonl"))
        prefix = (
            f"wiki-v2-{coordinator['slug']}-"
            f"{coordinator['target_sha256'][:12]}-")
        # Namespace do produtor (.agents/runtime/wworkspaces), o mesmo que
        # verify-v2-workflow-results exige; /tmp deixou de ser aceito quando o
        # produtor migrou (92c6a7f8, 2026-08-04). O prefixo continua sendo o
        # contrato entre produtor e verificador.
        workspace = producer.create_workflow_workspace(
            coordinator["slug"], coordinator["target_sha256"])
        self.assertTrue(workspace.name.startswith(prefix), workspace)
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                root = pathlib.Path(raw_root)
                commands = []
                for label in (
                        "wave-staged-local-audit",
                        "source-provenance-plan",
                        "source-provenance-live-all",
                        "source-provenance-check",
                        "wave-final-against-stock-audit"):
                    commands.append({
                        "label": label, "returncode": 0, "duration_ms": 1,
                        "stdout_sha256": digest("stdout:" + label),
                        "stderr_sha256": digest("stderr:" + label),
                    })
                for path in paths:
                    payload = ("post-wave:" + path + "\n").encode("utf-8")
                    live = root / path
                    live.parent.mkdir(parents=True, exist_ok=True)
                    live.write_bytes(payload)
                    receipt["post_sha256_by_path"][path] = hashlib.sha256(
                        payload).hexdigest()
                    receipt["distinctness_generation_root_by_path"][path] = (
                        tasks[0]["distinctness_epoch"]["generation_root"])
                    evidence_rel = (
                        "data/source-registry/"
                        "v2_source_provenance_live_evidence_sets/exact-" +
                        digest("evidence-path:" + path) + ".jsonl")
                    evidence_payload = (
                        "evidence:" + path + "\n").encode("utf-8")
                    evidence_path = root / evidence_rel
                    evidence_path.parent.mkdir(parents=True, exist_ok=True)
                    evidence_path.write_bytes(evidence_payload)
                    receipt["source_provenance_evidence_by_path"][path] = {
                        "path": evidence_rel,
                        "sha256": hashlib.sha256(evidence_payload).hexdigest(),
                    }
                    receipt["commands_by_path"][path] = copy.deepcopy(commands)
                    receipt["pre_provenance_defects_by_path"][path] = {}
                journal = workspace / WAVE.JOURNAL_NAME
                journal.write_bytes(b'{"authenticated":"fixture"}\n')
                receipt["journal_path"] = str(journal)
                receipt["journal_sha256"] = producer.snapshot_sha256(journal)
                receipt_path = workspace / WAVE.RECEIPT_NAME
                receipt_payload = VERIFY._canonical_review_receipt_payload(
                    receipt)
                receipt_path.write_bytes(receipt_payload)
                receipt_sha = hashlib.sha256(receipt_payload).hexdigest()
                queue_by_slug = {task["slug"]: task for task in tasks}
                claims = {}
                for task in tasks:
                    path = f"data/editorial/v2_pages/{task['slug']}.jsonl"
                    claim = {
                        "slug": task["slug"], "file": path,
                        "paginas": task["n"],
                        "target_sha256": task["target_sha256"],
                        "staged_sha256":
                            receipt["staged_sha256_by_path"][path],
                        "corrigidos_por_classe":
                            receipt["corrigidos_por_classe_by_path"][path],
                        "receipt_path": str(receipt_path),
                        "receipt_sha256": receipt_sha,
                        "queue_item_sha256": task["queue_item_sha256"],
                        "audited_sha256":
                            receipt["post_sha256_by_path"][path],
                        "audit_ok": True, "mutation_applied": True,
                        "wave_id": task["exact_component_wave"]["wave_id"],
                        "queue_artifact_sha256": queue_sha,
                    }
                    VERIFY._validate_claim_shape("review", claim, task)
                    claims[task["slug"]] = claim
                VERIFY._validate_exact_wave_claim_coverage(
                    claims, queue_by_slug)
                dependencies, selected_provenance = VERIFY._verify_exact_wave_receipt(
                    claims[tasks[0]["slug"]], tasks[0], queue_sha,
                    root, queue_by_slug)
                self.assertIn(receipt_path, dependencies)
                selected_path = (
                    f"data/editorial/v2_pages/{tasks[0]['slug']}.jsonl"
                )
                selected_evidence = (
                    receipt["source_provenance_evidence_by_path"][selected_path]
                )
                self.assertEqual(
                    selected_provenance,
                    {
                        "file": selected_evidence["path"],
                        "sha256": selected_evidence["sha256"],
                    },
                )
                missing = dict(claims)
                missing.pop(tasks[-1]["slug"])
                with self.assertRaisesRegex(
                        VERIFY.VerificationError, "wave inteira"):
                    VERIFY._validate_exact_wave_claim_coverage(
                        missing, queue_by_slug)
        finally:
            shutil.rmtree(workspace)


if __name__ == "__main__":
    unittest.main()
