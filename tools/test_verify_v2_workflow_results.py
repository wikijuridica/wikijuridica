#!/usr/bin/env python3
"""Focused contracts for verifier-owned raw recovery authentication."""

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
LOADER = importlib.machinery.SourceFileLoader(
    "verify_v2_workflow_results_contract",
    str(ROOT / "tools" / "verify-v2-workflow-results"),
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
VERIFY = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(VERIFY)
PRODUCER = VERIFY.producer


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class WorkflowResultInputBoundaryTests(unittest.TestCase):

    def test_result_path_requires_regular_nonsymlink_snapshot(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            target = root / "result.json"
            target.write_text("{}\n", encoding="utf-8")
            alias = root / "alias.json"
            alias.symlink_to(target)
            with self.assertRaisesRegex(
                    VERIFY.VerificationError, "arquivo regular seguro"):
                VERIFY._read_json(str(alias))
            self.assertEqual(VERIFY._read_json(str(target)), {})


class ReviewSourceProvenanceAttestationTests(unittest.TestCase):

    def test_review_receipt_generation_must_equal_live_global_epoch(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            stock = root / "data" / "editorial" / "v2_pages"
            stock.mkdir(parents=True)
            shard = stock / "civil-review-01.jsonl"
            shard.write_bytes(b"{}\n")
            relative = "data/editorial/v2_pages/civil-review-01.jsonl"
            generation = "a" * 64
            index = {
                "status": "ready",
                "mode": "global-distinctness-v3-read-only",
                "schema_version":
                    VERIFY.auditor_contract.GLOBAL_BATCH_SCHEMA_VERSION,
                "algorithm_fingerprint":
                    VERIFY.auditor_contract.INCREMENTAL_ALGORITHM_FINGERPRINT,
                "batch_fingerprint":
                    VERIFY.auditor_contract.GLOBAL_BATCH_ALGORITHM_FINGERPRINT,
                "target_digest": sha(shard.read_bytes()),
                "target_snapshot_bound": True,
                "inventory_complete": True,
                "inventory_stable": True,
                "candidate_routing_complete": True,
                "local_routing_complete": True,
                "visible_surface_scope_complete": True,
                "visible_surfaces": list(
                    VERIFY.auditor_contract.INCREMENTAL_VISIBLE_SURFACES),
                "publication_allowed": False,
                "index_policy": "noindex",
                "stock_shards": 1,
                "stock_pages": 1,
                "generation_root": generation,
                "stock_root": "c" * 64,
            }
            report = {
                "files": {relative: {
                    "file": relative, "active_pages": 1,
                    "defects": {}, "ok": True,
                    "distinctness_index": index,
                }},
                "total_pages": 1,
                "max_heading_reuse": 1,
            }
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps({
                "distinctness_generation_root": "b" * 64,
            }), encoding="utf-8")
            claims = {"civil-review-01": {"receipt_path": str(receipt)}}
            with self.assertRaisesRegex(
                    VERIFY.VerificationError, "generation root global vivo"):
                VERIFY._validate_global_review_merit(root, report, claims)
            receipt.write_text(json.dumps({
                "distinctness_generation_root": generation,
            }), encoding="utf-8")
            attestation, _ = VERIFY._validate_global_review_merit(
                root, report, claims)
            self.assertEqual(attestation["generation_root"], generation)

    def test_canonical_queue_and_stock_membership_reject_symbolic_or_new_entry(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            workflows = root / "scripts" / "workflows"
            stock = root / "data" / "editorial" / "v2_pages"
            workflows.mkdir(parents=True)
            stock.mkdir(parents=True)
            outside = root / "outside.js"
            outside.write_text(
                "const REVIEW_QUEUE_OPERATIONAL_RCA = null\n"
                "const files = []\n", encoding="utf-8")
            canonical = workflows / "writing-review-todo.js"
            canonical.symlink_to(outside)
            with self.assertRaisesRegex(
                    VERIFY.VerificationError, "arquivo regular seguro"):
                VERIFY._load_queue(root, "review", None)

            watch = VERIFY._open_review_stock_membership_watch(root)
            self.addCleanup(lambda: __import__("os").close(watch[0]))
            (stock / "civil-review-01.jsonl").write_text(
                '{"intent_id":"civil-exemplo"}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                    VERIFY.VerificationError, "membership"):
                VERIFY._assert_review_stock_membership_unchanged(root, watch)

    def test_stdout_is_bound_to_current_selection_and_exact_sidecar(self):
        relative = (
            "data/source-registry/v2_source_provenance_live_evidence_sets/" +
            "exact-" + "a" * 64 + ".jsonl")
        payload = (
            "v2-source-provenance: check=current-selection-pass "
            "release_eligible=false scope=all records=2 verified=2 blocked=0 "
            f"path={relative} publication=false\n"
        ).encode("utf-8")
        VERIFY._validate_source_provenance_check_stdout(
            payload, relative, "civil-review-01")
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "divergiu"):
            VERIFY._validate_source_provenance_check_stdout(
                payload, relative.replace("a" * 64, "b" * 64),
                "civil-review-01")
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "divergiu"):
            VERIFY._validate_source_provenance_check_stdout(
                payload.replace(b"current-selection-pass", b"structural-pass"),
                relative, "civil-review-01")


class RawRecoveryVerifierTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        portfolio_rel = "data/editorial/portfolio_v2/civil.jsonl"
        target_rel = "data/editorial/v2_pages/civil-recovery-01.jsonl"
        portfolio = (
            b'{"family":"familia","intent_id":"intent-a"}\n'
            b'{"family":"familia","intent_id":"intent-b"}\n'
        )
        line_a = (
            b'{"intent_id":"intent-a","sections":[{"heading":"Contexto",'
            b'"text":"Preservar"}],"official_sources":[{"name":"Planalto",'
            b'"url":"https://www.planalto.gov.br/ccivil_03/leis/'
            b'l8078compilado.htm","anchor_claim":"Lei"}]}'
        )
        line_b = b'{"intent_id":"intent-b","body":"reescrito"}'
        target = line_a + b"\n" + line_b + b"\n"
        raw_preimage = line_a + b"\n" + line_b
        raw_digest = sha(raw_preimage)
        for relative, payload in ((portfolio_rel, portfolio),
                                  (target_rel, target)):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        evidence_rel = (
            "data/editorial/v2_raw_recovery_preimages/" +
            raw_digest + ".raw")
        evidence_path = self.root / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(raw_preimage)
        expected = ["intent-a", "intent-b"]
        recovery = {
            "schema_version": "v2_writing_raw_recovery_v1",
            "route": "writing_full_shard_recovery",
            "target_rel_path": target_rel,
            "target_sha256": raw_digest,
            "expected_n": 2,
            "expected_intent_ids": expected,
            "expected_intent_ids_sha256": sha(json.dumps(
                expected, ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8")),
            "reason_codes": ["missing_terminal_lf"],
            "raw_lines_seen": 2,
            "parsed_object_rows": 2,
            "invalid_rows": 0,
            "unaddressable_rows": 0,
            "reuse": ["intent-a"],
            "preserved_record_sha256": {"intent-a": sha(line_a)},
            "review_allowed": False,
            "publication_allowed": False,
            "index_policy": "noindex",
        }
        recovery["recovery_item_sha256"] = (
            PRODUCER.writing_recovery_item_sha256(recovery))
        self.entry = {
            "area": "civil", "families": ["familia"],
            "file": portfolio_rel, "n": 2,
            "portfolio_sha256": sha(portfolio),
            "preserved_record_sha256": {"intent-a": sha(line_a)},
            "skip": 0, "slug": "civil-recovery-01",
            "semantic_contract_sha256": "2" * 64,
            "source_hint_catalog_sha256": "3" * 64,
            "source_overrides": {}, "sources": [],
            "strict_source_intents": [], "take": 2,
            "target_sha256": raw_digest, "writer": "redator-juridico",
            "reuse": ["intent-a"], "writing_recovery": recovery,
        }
        self.target = target
        self.evidence_rel = evidence_rel
        self.evidence_path = evidence_path

    def queue(self, entry=None):
        value = self.entry if entry is None else entry
        return VERIFY._queue_by_slug(
            "mass", [value], "2" * 64, None)[value["slug"]]

    def test_closed_projection_binds_live_slice_and_preserved_bytes(self):
        entry = self.queue()
        claim = {
            "slug": entry["slug"], "file": entry["writing_recovery"]["target_rel_path"],
            "target_sha256": entry["target_sha256"],
            "intent_ids": ["intent-a", "intent-b"],
            "audited_sha256": sha(self.target),
            "audit_ok": True, "written": 2, "expected": 2,
            "raw_recovery_preimage_evidence": {
                "path": self.evidence_rel,
                "sha256": self.entry["target_sha256"],
            },
        }
        VERIFY._validate_claim_shape("mass", claim, entry)
        missing_evidence = dict(claim)
        missing_evidence.pop("raw_recovery_preimage_evidence")
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "preimagem permanente"):
            VERIFY._validate_claim_shape(
                "mass", missing_evidence, entry)
        digest, lines, dependencies = VERIFY._verify_live_file(
            self.root, "mass", claim, entry, None)
        self.assertEqual(digest, sha(self.target))
        self.assertEqual(lines, 2)
        self.assertEqual(len(dependencies), 1)
        self.assertEqual(
            VERIFY._verify_raw_recovery_preimage_evidence(
                self.root, claim, entry),
            {self.evidence_path: self.entry["target_sha256"]},
        )

    def test_fingerprint_target_and_extra_migration_are_rejected(self):
        fingerprint = copy.deepcopy(self.entry)
        fingerprint["writing_recovery"]["recovery_item_sha256"] = "f" * 64
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "writing_recovery inválido"):
            self.queue(fingerprint)

        target = copy.deepcopy(self.entry)
        target["writing_recovery"]["target_sha256"] = "f" * 64
        target["writing_recovery"]["recovery_item_sha256"] = (
            PRODUCER.writing_recovery_item_sha256(
                target["writing_recovery"]))
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "target SHA raw-recovery"):
            self.queue(target)

        migration = copy.deepcopy(self.entry)
        migration["portfolio_intent_migration"] = None
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "coexistiu com rota divergente"):
            self.queue(migration)

    def test_recomputed_but_reordered_expected_ids_fail_live_slice_binding(self):
        entry = copy.deepcopy(self.entry)
        recovery = entry["writing_recovery"]
        recovery["expected_intent_ids"] = ["intent-b", "intent-a"]
        recovery["expected_intent_ids_sha256"] = sha(json.dumps(
            recovery["expected_intent_ids"], ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8"))
        recovery["reuse"] = []
        recovery["preserved_record_sha256"] = {}
        entry["reuse"] = []
        entry["preserved_record_sha256"] = {}
        recovery["recovery_item_sha256"] = (
            PRODUCER.writing_recovery_item_sha256(recovery))
        entry = self.queue(entry)
        claim = {
            "intent_ids": ["intent-a", "intent-b"],
            "audited_sha256": sha(self.target),
        }
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "diverge do slice vivo"):
            VERIFY._verify_live_file(
                self.root, "mass", claim, entry, None)

    def test_recovery_rejects_noop_without_cas(self):
        entry = copy.deepcopy(self.entry)
        live_digest = sha(self.target)
        entry["target_sha256"] = live_digest
        entry["writing_recovery"]["target_sha256"] = live_digest
        entry["writing_recovery"]["recovery_item_sha256"] = (
            PRODUCER.writing_recovery_item_sha256(
                entry["writing_recovery"]))
        entry = self.queue(entry)
        claim = {
            "intent_ids": ["intent-a", "intent-b"],
            "audited_sha256": live_digest,
        }
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "não prova CAS"):
            VERIFY._verify_live_file(
                self.root, "mass", claim, entry, None)

    def test_preimage_evidence_is_exact_and_content_addressed(self):
        entry = self.queue()
        claim = {
            "raw_recovery_preimage_evidence": {
                "path": self.evidence_rel,
                "sha256": entry["target_sha256"],
            },
        }
        VERIFY._verify_raw_recovery_preimage_evidence(
            self.root, claim, entry)

        forged = copy.deepcopy(claim)
        forged["raw_recovery_preimage_evidence"]["path"] = (
            "data/editorial/v2_raw_recovery_preimages/" + "f" * 64 + ".raw")
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "bind inválido"):
            VERIFY._verify_raw_recovery_preimage_evidence(
                self.root, forged, entry)

        self.evidence_path.write_bytes(b"drift")
        with self.assertRaisesRegex(VERIFY.VerificationError,
                                    "diverge do target SHA"):
            VERIFY._verify_raw_recovery_preimage_evidence(
                self.root, claim, entry)


if __name__ == "__main__":
    unittest.main()
