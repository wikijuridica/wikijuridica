#!/usr/bin/env python3
"""Contratos focais do consumidor writing raw-recovery."""

from __future__ import annotations

import copy
import base64
import ast
import json
import pathlib
import re
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import generate_v2_review_queue as producer


ROOT = pathlib.Path(__file__).resolve().parent.parent
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def active_row(intent_id: str) -> bytes:
    return json.dumps({
        "intent_id": intent_id,
        "sections": [{"heading": "Questão específica", "text": "Texto."}],
        "official_sources": [{
            "name": "Código de Defesa do Consumidor",
            "url": (
                "https://www.planalto.gov.br/ccivil_03/leis/"
                "l8078compilado.htm"
            ),
            "anchor_claim": "Lei nº 8.078/1990 em texto compilado",
        }],
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def recovery_projection() -> dict:
    projection = producer.derive_writing_raw_recovery_projection(
        active_row("alpha"),
        "data/editorial/v2_pages/civil-a.jsonl",
        producer._sha256(active_row("alpha")),
        ["alpha"],
    )
    if projection is None:
        raise AssertionError("missing LF deveria produzir raw-recovery")
    return projection


def workflow_batch(projection: dict | None = None) -> dict:
    if projection is None:
        projection = recovery_projection()
    target_sha = projection["target_sha256"]
    return {
        "area": "civil",
        "families": ["familia"],
        "file": "data/editorial/portfolio_v2/civil.jsonl",
        "n": 1,
        "portfolio_sha256": SHA_A,
        "preserved_record_sha256": dict(
            projection["preserved_record_sha256"]),
        "skip": 0,
        "slug": "civil-a",
        "semantic_contract_sha256": SHA_B,
        "source_hint_catalog_sha256": SHA_C,
        "source_overrides": {},
        "sources": [],
        "strict_source_intents": [],
        "take": 0,
        "target_sha256": target_sha,
        "writer": "redator-juridico",
        "intent_ids": ["alpha"],
        "reuse": list(projection["reuse"]),
        "writing_recovery": projection,
    }


class WritingRawRecoveryConsumerTest(unittest.TestCase):
    def test_queue_pair_failure_resumes_forward_without_old_byte_restore(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            first = root / "writing-mass-todo.js"
            second = root / "writing-mass-todo-sem-telecom.js"
            first.write_bytes(b"first-old\n")
            second.write_bytes(b"second-old\n")
            first_old = producer.snapshot_sha256(first)
            second_old = producer.snapshot_sha256(second)
            original = producer.atomic_replace_cas

            def fail_second(path, payload, expected_sha256, **kwargs):
                if pathlib.Path(path) == second:
                    raise producer.CASMismatch("falha injetada na segunda perna")
                return original(path, payload, expected_sha256, **kwargs)

            with mock.patch.object(
                    producer, "atomic_replace_cas", side_effect=fail_second):
                with self.assertRaisesRegex(
                        producer.CASMismatch, "permanece no postimage"):
                    producer.atomic_replace_cas_pair_roll_forward(
                        first, b"first-new\n", first_old,
                        second, b"second-new\n", second_old)
            self.assertEqual(first.read_bytes(), b"first-new\n")
            self.assertEqual(second.read_bytes(), b"second-old\n")

            # Mesma autoridade/preimages: a perna já instalada é reutilizada
            # e somente a segunda avança. Nenhuma escrita repõe first-old.
            producer.atomic_replace_cas_pair_roll_forward(
                first, b"first-new\n", first_old,
                second, b"second-new\n", second_old)
            self.assertEqual(first.read_bytes(), b"first-new\n")
            self.assertEqual(second.read_bytes(), b"second-new\n")

    def test_relauncher_and_workflow_bind_the_executable_route(self):
        relaunch = (ROOT / "ops/relaunch-writing.sh").read_text(
            encoding="utf-8")
        workflow = (ROOT / "scripts/workflows/writing-mass.js").read_text(
            encoding="utf-8")
        for required in (
            "producer.derive_writing_raw_recovery_projection(",
            "producer.capture_writing_raw_recovery_projection(",
            "producer.persist_writing_raw_recovery_preimage(",
            "producer.verify_writing_raw_recovery_preimage_projection(",
            "writing_raw_recovery_evidence[target_rel_path] = evidence",
            "writing_raw_recovery_valid_extra_requires_migration",
            "item['writing_recovery'] = raw_recovery",
            "raw_recovery['preserved_record_sha256']",
            "exclusao run-scoped ocultaria raw-recovery",
            "supersession_projection_unavailable = True",
            "deferred_supersession_batches += 1",
            "Não use winners vazios como prova negativa",
            "lotes_raw_recovery=",
            "lotes_adiados_sem_epoch_dec020=",
            "producer.atomic_replace_cas_pair_roll_forward(",
        ):
            self.assertIn(required, relaunch)
        self.assertNotIn("output_snapshot.payload", relaunch)
        for required in (
            "'writing_recovery'",
            "function canonicalWritingRecovery(batch)",
            "v2_writing_raw_recovery_v1",
            "producer.verify_writing_raw_recovery_preimage_projection(",
            "producer.verify_staged_writing_recovery(",
            "raw_recovery_preimage_evidence=",
            "v2_raw_recovery_preimages/",
            "RAW-RECOVERY AUTENTICADO E NAO PUBLICAVEL",
            "publication_allowed=false",
            "index_policy=noindex",
            "function pythonStringList(values)",
            "${familiesPython}",
            "${rawRecoveryIntentIDsPython}",
        ):
            self.assertIn(required, workflow)

    def test_missing_lf_invalid_json_count_and_unaddressable_tombstone_route(self):
        path = "data/editorial/v2_pages/civil-a.jsonl"
        cases = (
            (
                "missing_lf",
                active_row("alpha"),
                ["alpha"],
                "missing_terminal_lf",
                ["alpha"],
            ),
            (
                "invalid_json",
                active_row("alpha") + b"\n{" + b"\n",
                ["alpha", "beta"],
                "invalid_json_row",
                ["alpha"],
            ),
            (
                "count",
                active_row("alpha") + b"\n",
                ["alpha", "beta"],
                "cardinality_mismatch",
                ["alpha"],
            ),
            (
                "unaddressable_tombstone",
                b'{"skipped":true}\n',
                ["alpha"],
                "unaddressable_row",
                [],
            ),
        )
        for label, payload, expected, reason, reuse in cases:
            with self.subTest(label=label):
                digest = producer._sha256(payload)
                projection = producer.derive_writing_raw_recovery_projection(
                    payload, path, digest, expected)
                self.assertIsNotNone(projection)
                assert projection is not None
                self.assertIn(reason, projection["reason_codes"])
                self.assertEqual(projection["target_sha256"], digest)
                self.assertEqual(projection["expected_intent_ids"], expected)
                self.assertEqual(projection["reuse"], reuse)
                self.assertFalse(projection["review_allowed"])
                self.assertFalse(projection["publication_allowed"])
                self.assertEqual(projection["index_policy"], "noindex")
                self.assertEqual(
                    projection["recovery_item_sha256"],
                    producer.writing_recovery_item_sha256(projection),
                )

        # Tombstone com identidade continua reparo row-level; somente o caso
        # sem intent_id amplia para raw-recovery.
        canonical_tombstone = b'{"intent_id":"alpha","skipped":true}\n'
        self.assertIsNone(producer.derive_writing_raw_recovery_projection(
            canonical_tombstone, path,
            producer._sha256(canonical_tombstone), ["alpha"]))

    def test_valid_extra_blocks_raw_recovery_instead_of_being_erased(self):
        payload = active_row("alpha") + b"\n" + active_row("extra") + b"\n"
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.derive_writing_raw_recovery_projection(
                payload,
                "data/editorial/v2_pages/civil-a.jsonl",
                producer._sha256(payload),
                ["alpha"],
            )
        self.assertEqual(
            caught.exception.rca["reason_codes"],
            ["writing_raw_recovery_valid_extra_requires_migration"],
        )

    def test_reused_live_source_metadata_survives_raw_verifier_byte_exact(self):
        path = "data/editorial/v2_pages/civil-a.jsonl"
        row = json.loads(active_row("alpha"))
        row["official_sources"][0]["verified_at"] = "2026-07-16"
        row["official_sources"][0]["http_status"] = 200
        target_payload = json.dumps(
            row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        target_digest = producer._sha256(target_payload)
        projection = producer.derive_writing_raw_recovery_projection(
            target_payload, path, target_digest, ["alpha"])
        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual(projection["reuse"], ["alpha"])
        encoded = base64.b64encode(json.dumps(
            projection, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).decode("ascii")
        semantic = producer.WritingSemanticContract(
            digest=SHA_A, unresolved_intents=frozenset(),
            requirement_fingerprints={}, portfolio_rel_paths={},
            target_rel_paths={}, superseded_target_rel_paths={},
            superseded_page_record_sha256={}, evidence_kinds={},
            evidence_rel_paths={}, evidence_sha256={}, dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        resolution = producer.WritingSourceResolution(
            selected_intents=("alpha",), source_overrides={},
            strict_source_intents=(),
        )
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            target = root / path
            target.parent.mkdir(parents=True)
            target.write_bytes(target_payload)
            evidence = producer.persist_writing_raw_recovery_preimage(
                root, target_payload, target_digest)
            staged = root / "staged.jsonl"
            staged.write_bytes(target_payload + b"\n")
            with (
                mock.patch.object(
                    producer, "verify_writing_source_resolution",
                    return_value=resolution,
                ),
                mock.patch.object(
                    producer, "load_writing_semantic_contract",
                    return_value=semantic,
                ),
                mock.patch.object(
                    producer,
                    "verify_writing_semantic_contract_dependencies",
                ),
            ):
                captured = producer.verify_staged_writing_recovery(
                    root, staged, path, target_digest,
                    "data/editorial/portfolio_v2/civil.jsonl", SHA_B,
                    "data/editorial/v2_source_hint_catalog.json", SHA_C,
                    ["familia"], 0, 1, 1, None, "ignored", encoded,
                    evidence,
                )
        self.assertEqual(captured.payload, target_payload + b"\n")

    def test_permanent_preimage_is_create_once_and_cas_bound(self):
        payload = active_row("alpha")
        digest = producer._sha256(payload)
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            (root / "data" / "editorial").mkdir(parents=True)
            expected = {
                "path": (
                    "data/editorial/v2_raw_recovery_preimages/" +
                    digest + ".raw"),
                "sha256": digest,
            }
            first = producer.persist_writing_raw_recovery_preimage(
                root, payload, digest)
            second = producer.persist_writing_raw_recovery_preimage(
                root, payload, digest)
            self.assertEqual(first, expected)
            self.assertEqual(second, expected)
            snapshot = producer.read_writing_raw_recovery_preimage(
                root, expected, digest)
            self.assertEqual(snapshot.payload, payload)
            semantic_payload = b"semantic-contract"
            portfolio_payload = b"portfolio"
            catalog_payload = b"catalog"
            semantic_path = (
                root / "data/editorial/v2_writing_semantic_contract.json")
            portfolio_path = (
                root / "data/editorial/portfolio_v2/civil.jsonl")
            catalog_path = (
                root / "data/editorial/v2_source_hint_catalog.json")
            portfolio_path.parent.mkdir(parents=True, exist_ok=True)
            semantic_path.write_bytes(semantic_payload)
            portfolio_path.write_bytes(portfolio_payload)
            catalog_path.write_bytes(catalog_payload)
            semantic = producer.WritingSemanticContract(
                digest=producer._sha256(semantic_payload),
                unresolved_intents=frozenset(),
                requirement_fingerprints={}, portfolio_rel_paths={},
                target_rel_paths={}, superseded_target_rel_paths={},
                superseded_page_record_sha256={}, evidence_kinds={},
                evidence_rel_paths={}, evidence_sha256={},
                dependency_sha256={}, absent_dependency_paths=frozenset(),
            )
            epoch = producer.writing_promotion_dependency_epoch(
                root, semantic,
                "data/editorial/portfolio_v2/civil.jsonl",
                producer._sha256(portfolio_payload),
                "data/editorial/v2_source_hint_catalog.json",
                producer._sha256(catalog_payload),
                raw_recovery_preimage_evidence=expected,
            )
            self.assertEqual(epoch[root / expected["path"]], digest)
            archive = root / expected["path"]
            archive.chmod(0o644)
            archive.write_bytes(payload + b"x")
            with self.assertRaises(producer.CASMismatch):
                producer.read_writing_raw_recovery_preimage(
                    root, expected, digest)

    def test_workflow_closed_schema_rejects_forged_recovery(self):
        workflow = (ROOT / "scripts/workflows/writing-mass.js").read_text(
            encoding="utf-8")
        start = workflow.index("const SNAPSHOT_SHA256")
        end = workflow.index("\nconst PERSONAS")
        validator = workflow[start:end]

        def accepted(batch: dict) -> bool:
            source = (
                "const batches = " +
                json.dumps([batch], ensure_ascii=False, separators=(",", ":")) +
                ";\n" + validator +
                "\nif (pythonStringList(['familia','alpha']) !== "
                '"[\'familia\',\'alpha\']") throw new Error("literal Python inseguro")\n' +
                "\nprocess.stdout.write('ok')\n"
            )
            result = subprocess.run(
                ["node", "-e", source], cwd=ROOT,
                text=True, capture_output=True, check=False,
            )
            return result.returncode == 0 and result.stdout == "ok"

        valid = workflow_batch()
        self.assertTrue(accepted(valid))
        mutations = []
        public = copy.deepcopy(valid)
        public["writing_recovery"]["publication_allowed"] = True
        mutations.append(public)
        wrong_target = copy.deepcopy(valid)
        wrong_target["writing_recovery"]["target_sha256"] = SHA_A
        mutations.append(wrong_target)
        extra_key = copy.deepcopy(valid)
        extra_key["writing_recovery"]["forged"] = True
        mutations.append(extra_key)
        missing_preservation = copy.deepcopy(valid)
        missing_preservation["preserved_record_sha256"] = {}
        mutations.append(missing_preservation)
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.assertFalse(accepted(mutation))

    def test_raw_prompt_emits_shell_safe_python_literals(self):
        workflow = (ROOT / "scripts/workflows/writing-mass.js").read_text(
            encoding="utf-8")
        # O slice precisa começar no trust-root do writer (o contrato e o
        # assert que writePrompt executa) — começar em SNAPSHOT_SHA256 deixava
        # assertV2StockWriterContractForEntry fora do eval (ReferenceError).
        start = workflow.index("const V2_STOCK_WRITER_CONTRACT")
        end = workflow.index("\nphase('Escrever')")
        source = (
            "const batches = " + json.dumps(
                [workflow_batch()], ensure_ascii=False,
                separators=(",", ":")) + ";\n" +
            workflow[start:end] +
            "\nprocess.stdout.write(writePrompt(batches[0]))\n"
        )
        result = subprocess.run(
            ["node", "-e", source], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        prompt = result.stdout
        self.assertIn("['familia']", prompt)
        self.assertIn("['alpha']", prompt)
        commands = re.findall(r'python3 -c "([^"]*)"', prompt)
        self.assertGreaterEqual(len(commands), 4)
        for index, command in enumerate(commands):
            with self.subTest(index=index):
                ast.parse(command)


def _load_reorder_cli():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader(
        "generate_v2_shard_slice_reorder",
        str(ROOT / "tools/generate-v2-shard-slice-reorder"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class MechanicalRecoveryFamilyTest(unittest.TestCase):
    """Família mecânica (ordem/LF) NUNCA consome redator; autoria SEMPRE."""

    PATH = "data/editorial/v2_pages/civil-a.jsonl"

    def order_mismatch_projection(self):
        payload = active_row("beta") + b"\n" + active_row("alpha") + b"\n"
        projection = producer.derive_writing_raw_recovery_projection(
            payload, self.PATH, producer._sha256(payload), ["alpha", "beta"])
        self.assertIsNotNone(projection)
        self.assertEqual(
            projection["reason_codes"], ["intent_order_mismatch"])
        return payload, projection

    def test_order_mismatch_only_is_mechanical_never_writer_work(self):
        _, projection = self.order_mismatch_projection()
        self.assertEqual(projection["invalid_rows"], 0)
        self.assertEqual(projection["unaddressable_rows"], 0)
        self.assertEqual(projection["reuse"], ["alpha", "beta"])
        self.assertTrue(
            producer.writing_recovery_mechanical_only(projection, 2))
        # A mera presença de writing_recovery NÃO pode mais emitir redator:
        # recovery 100% mecânica com reuse cobrindo o slice é no-op de AUTORIA.
        self.assertTrue(producer.writer_noop_batch(
            projection["reuse"], 2, writing_recovery=projection))

    def test_missing_terminal_lf_only_is_mechanical(self):
        payload = active_row("alpha")
        projection = producer.derive_writing_raw_recovery_projection(
            payload, self.PATH, producer._sha256(payload), ["alpha"])
        self.assertEqual(
            projection["reason_codes"], ["missing_terminal_lf"])
        self.assertTrue(
            producer.writing_recovery_mechanical_only(projection, 1))
        self.assertTrue(producer.writer_noop_batch(
            projection["reuse"], 1, writing_recovery=projection))

    def test_invalid_row_recovery_remains_authorship(self):
        payload = active_row("alpha") + b"\n{" + b"\n"
        projection = producer.derive_writing_raw_recovery_projection(
            payload, self.PATH, producer._sha256(payload), ["alpha", "beta"])
        self.assertGreater(projection["invalid_rows"], 0)
        self.assertFalse(
            producer.writing_recovery_mechanical_only(projection, 2))
        # Lote com QUALQUER linha a reconstruir segue para o redator.
        self.assertFalse(producer.writer_noop_batch(
            projection["reuse"], 2, writing_recovery=projection))

    def test_unaddressable_row_recovery_remains_authorship(self):
        payload = active_row("alpha") + b"\n" + json.dumps(
            {"sections": [{"heading": "Sem identidade", "text": "x"}]},
            ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        projection = producer.derive_writing_raw_recovery_projection(
            payload, self.PATH, producer._sha256(payload), ["alpha", "beta"])
        self.assertGreater(projection["unaddressable_rows"], 0)
        self.assertFalse(
            producer.writing_recovery_mechanical_only(projection, 2))
        self.assertFalse(producer.writer_noop_batch(
            projection["reuse"], 2, writing_recovery=projection))

    def test_missing_line_cardinality_remains_authorship(self):
        payload = active_row("alpha") + b"\n"
        projection = producer.derive_writing_raw_recovery_projection(
            payload, self.PATH, producer._sha256(payload), ["alpha", "beta"])
        self.assertIn("cardinality_mismatch", projection["reason_codes"])
        self.assertFalse(
            producer.writing_recovery_mechanical_only(projection, 2))
        self.assertFalse(producer.writer_noop_batch(
            projection["reuse"], 2, writing_recovery=projection))

    def test_forged_or_future_reason_codes_fail_closed(self):
        _, projection = self.order_mismatch_projection()
        forged_counter = dict(projection)
        forged_counter["invalid_rows"] = 1
        self.assertFalse(
            producer.writing_recovery_mechanical_only(forged_counter, 2))
        future_reason = dict(projection)
        future_reason["reason_codes"] = [
            "intent_order_mismatch", "novo_codigo_desconhecido"]
        self.assertFalse(
            producer.writing_recovery_mechanical_only(future_reason, 2))
        self.assertFalse(producer.writer_noop_batch(
            projection["reuse"], 2, writing_recovery=future_reason))
        # Divergência entre reuse do lote e reuse da recovery = autoria.
        self.assertFalse(producer.writer_noop_batch(
            ["alpha"], 2, writing_recovery=projection))
        self.assertFalse(producer.writer_noop_batch(
            ["alpha", "gamma"], 2, writing_recovery=projection))

    def test_reorder_cli_plan_is_byte_exact_permutation(self):
        cli = _load_reorder_cli()
        payload, projection = self.order_mismatch_projection()
        new_payload = cli.plan_reorder(
            payload, list(projection["expected_intent_ids"]),
            dict(projection["preserved_record_sha256"]))
        self.assertEqual(
            new_payload,
            active_row("alpha") + b"\n" + active_row("beta") + b"\n")
        self.assertEqual(
            sorted(payload.rstrip(b"\n").split(b"\n")),
            sorted(new_payload.rstrip(b"\n").split(b"\n")))
        # Payload reordenado tem de ser CANÔNICO (projeção residual None).
        self.assertIsNone(producer.derive_writing_raw_recovery_projection(
            new_payload, self.PATH, producer._sha256(new_payload),
            ["alpha", "beta"]))

    def test_reorder_cli_memoizes_semantic_contract_without_hiding_drift(self):
        """Memo do contrato: 1 load por lote, mas nunca reuso de estado vencido.

        Carregar o contrato semântico custa ~1,5 s (o epoch v3 autentica o
        estoque inteiro); process_record roda por linha do manifesto, então
        recarregar era O(lote × estoque). O reuso só é legítimo se: (a) o
        loader for preguiçoso — registro que morre no CAS da preimagem não
        paga contrato; (b) a guarda de epoch detectar qualquer mudança em
        dependência/estoque; (c) escrita própria invalidar na hora.
        """
        cli = _load_reorder_cli()
        contract = producer.WritingSemanticContract(
            digest="d" * 64,
            unresolved_intents=frozenset(),
            requirement_fingerprints={},
            portfolio_rel_paths={},
            target_rel_paths={},
            superseded_target_rel_paths={},
            superseded_page_record_sha256={},
            evidence_kinds={},
            evidence_rel_paths={},
            evidence_sha256={},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        loads = []

        def fake_load(root):
            loads.append(root)
            return contract

        epochs = ["epoch-1"]
        with mock.patch.object(
            cli.producer, "load_writing_semantic_contract", fake_load
        ), mock.patch.object(
            cli, "_semantic_contract_epoch", lambda root, c: epochs[-1]
        ):
            cli._invalidate_semantic_contract()
            self.assertIs(cli._semantic_contract(ROOT), contract)
            self.assertIs(cli._semantic_contract(ROOT), contract)
            self.assertEqual(len(loads), 1, "lote deve pagar 1 load")
            # (b) qualquer byte de dependência/estoque muda -> recarrega.
            epochs.append("epoch-2")
            cli._semantic_contract(ROOT)
            self.assertEqual(len(loads), 2, "epoch novo tem de recarregar")
            # (c) escrita própria (reorder aplicado) vence o memo.
            cli._invalidate_semantic_contract()
            cli._semantic_contract(ROOT)
            self.assertEqual(len(loads), 3, "escrita própria invalida o memo")
            cli._invalidate_semantic_contract()

        # (a) preguiça: preimagem fora do CAS recusa ANTES de carregar contrato.
        payload = active_row("alpha") + b"\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            target = root / self.PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            called = []
            with self.assertRaises(producer.CASMismatch):
                producer.capture_writing_raw_recovery_projection(
                    root, self.PATH, "0" * 64, ["alpha"],
                    semantic_contract_loader=lambda: called.append(1))
            self.assertEqual(called, [], "loader não pode ser ansioso")
            # Loader que devolve algo que não é contrato falha fechado.
            with self.assertRaises(TypeError):
                producer.capture_writing_raw_recovery_projection(
                    root, self.PATH, producer._sha256(payload), ["alpha"],
                    semantic_contract_loader=lambda: "nao-e-contrato")

    def test_reorder_cli_fixes_missing_terminal_lf(self):
        cli = _load_reorder_cli()
        payload = active_row("alpha")
        projection = producer.derive_writing_raw_recovery_projection(
            payload, self.PATH, producer._sha256(payload), ["alpha"])
        new_payload = cli.plan_reorder(
            payload, list(projection["expected_intent_ids"]),
            dict(projection["preserved_record_sha256"]))
        self.assertEqual(new_payload, active_row("alpha") + b"\n")

    def test_reorder_cli_refuses_anything_needing_authorship(self):
        cli = _load_reorder_cli()
        payload, projection = self.order_mismatch_projection()
        expected = list(projection["expected_intent_ids"])
        preserved = dict(projection["preserved_record_sha256"])
        with self.assertRaises(cli.ReorderRefused):
            cli.plan_reorder(
                active_row("beta") + b"\n", expected, preserved)
        with self.assertRaises(cli.ReorderRefused):
            cli.plan_reorder(
                active_row("beta") + b"\n{" + b"\n", expected, preserved)
        with self.assertRaises(cli.ReorderRefused):
            cli.plan_reorder(
                active_row("beta") + b"\n" + active_row("beta") + b"\n",
                expected, preserved)
        tampered = dict(preserved)
        tampered["alpha"] = "0" * 64
        with self.assertRaises(cli.ReorderRefused):
            cli.plan_reorder(payload, expected, tampered)
        with self.assertRaises(cli.ReorderRefused):
            cli.plan_reorder(
                payload.replace(b"\n", b"\r\n"), expected, preserved)

    def test_relauncher_binds_mechanical_route(self):
        relaunch = (ROOT / "ops/relaunch-writing.sh").read_text(
            encoding="utf-8")
        for required in (
            "producer.writing_recovery_mechanical_only(",
            "v2_writing_mechanical_reorder_v1",
            "data/ops/writing_mechanical_reorder_todo.jsonl",
            "lotes_reordenacao_mecanica=",
            "tools/generate-v2-shard-slice-reorder",
        ):
            self.assertIn(required, relaunch)


# ---------------------------------------------------------------------------
# Linhas REAIS dos shards vivos em 2026-09-05 — bytes copiados, não literal
# inventado. São os dois lotes que reprovavam o fechamento da fila com "reuse
# diverge da preimagem autenticada": a rota raw-recovery punha a tombstone
# fechada em ``reuse`` e o classificador (oráculo do verificador) não. Copiar em
# vez de ler do disco: o redator vai completar esses shards, e um teste que
# pulasse "se ausente" perderia a cobertura em silêncio. O SHA-256 de cada linha
# prova que o fixture É o registro vivo — bate com ``preserved_record_sha256`` da
# fila de 29/08 e com ``source_record_sha256`` em
# ``data/editorial/v2_rewrite_queue.jsonl``.
LIVE_AEREO_18_PATH = "data/editorial/v2_pages/aereo-18.jsonl"
LIVE_AEREO_18_SHA256 = "5f7d5d101cac7e73b77b5bab677acde008785f5b66d683f5a36661cde5f3460c"
# Slice do inventário (writing-mass-full.js: pagamento-e-reembolso, skip 0,
# take 3); a intenção do meio nunca foi escrita.
LIVE_AEREO_18_EXPECTED = (
    'aer-parcelas-cartao-voo-cancelado',
    'aer-reembolso-comprador-terceiro-titularidade',
    'aer-voucher-credito-expirou',
)
LIVE_AEREO_18_LINES = (
    b'{"intent_id": "aer-parcelas-cartao-voo-cancelado", "skipped": true, "skip_reason": "catalogo v2_source_hint_catalog.json sem resolucao exata para os source_hints (anac-res-400-2016, cdc-lei-8078-1990, bcb-estorno-cartao); intent strict exige source_overrides do catalogo, que estao vazios, bloqueando materializacao nesta execucao"}',
    b'{"intent_id": "aer-voucher-credito-expirou", "skipped": true, "skip_reason": "catalogo v2_source_hint_catalog.json sem resolucao exata para os source_hints (anac-res-400-2016, cdc-lei-8078-1990, jurisprudencia-stj); intent strict exige source_overrides do catalogo, que estao vazios, bloqueando materializacao nesta execucao"}',
)
LIVE_AEREO_18_LINE_SHA256 = (
    'ed3dbfc4beb70b4a8d36459da843c2d80d7210e958bbdc0a844a339bbdacbe3b',
    'ddbee99b66c5f1b1d1437e8599c7fda7ce52cae42a221af48cf996ee9ad7c5c6',
)
LIVE_SUCESSOES2_09_PATH = "data/editorial/v2_pages/sucessoes2-09.jsonl"
LIVE_SUCESSOES2_09_SHA256 = "05c41d45d7e0d8d910cb301cba20042fe0ac147aa7772009218e7626b222abd3"
# Lote pinado (take 0, intent_ids explícitos); a primeira intenção nunca foi
# escrita e a segunda é tombstone cujo motivo cita o catálogo pinado antigo.
LIVE_SUCESSOES2_09_EXPECTED = (
    'suc-itcmd-agregacao-doacoes-sucessivas',
    'suc-itcmd-base-calculo-quotas-holding',
)
LIVE_SUCESSOES2_09_LINES = (
    b'{"intent_id": "suc-itcmd-base-calculo-quotas-holding", "skipped": true, "skip_reason": "source_hints lc-227-2026 e cf-1988-art-155 sem entrada exata no catalogo pinado deste lote (584dd028...); apenas ec-132-2023 resolvido, o que forca a intencao para strict com override vazio no verificador staged e reprova qualquer pagina materializada sem reabrir a fila com catalogo atualizado"}',
)
LIVE_SUCESSOES2_09_LINE_SHA256 = (
    '79c67e87541dce409199447ceb26aebe11b8aa7104baca9bcc10614853b1d21e',
)


def closed_tombstone_row(
    intent_id: str,
    reason: str = "fonte oficial sem resolucao exata nesta execucao",
) -> bytes:
    return json.dumps(
        {"intent_id": intent_id, "skipped": True, "skip_reason": reason},
        ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def duplicate_url_page_row(intent_id: str) -> bytes:
    """Página publicada legítima cujas fontes repetem a URL.

    Padrão vivo (bancario-14 e outras 83 páginas em 2026-09-05): o predicado
    antigo da raw-recovery a excluía do reuse e mandava reescrever texto pago.
    """
    row = json.loads(active_row(intent_id))
    row["official_sources"].append(dict(row["official_sources"][0]))
    return json.dumps(
        row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def provenance_key_page_row(intent_id: str) -> bytes:
    """Página auditada com chave de proveniência fora do schema de escrita nova."""
    row = json.loads(active_row(intent_id))
    row["official_sources"][0]["source_kind"] = "legal_act"
    return json.dumps(
        row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class WritingReuseSemanticsTest(unittest.TestCase):
    """Uma só definição de ``reuse``: tombstone preenche o slot, nunca reusa.

    Família corrigida em 2026-09-05. ``derive_writing_raw_recovery_projection``
    tinha predicado próprio (tombstone fechada OU página com fontes canônicas)
    e ``classify_batch_completion`` outro (página ativa). Como
    ``ops/relaunch-writing.sh`` copia o ``reuse`` da raw-recovery para o lote e
    ``tools/verify_v2_writing_queue_closure.py`` usa o classificador como
    oráculo, qualquer diferença virava "reuse diverge da preimagem
    autenticada". Estes testes exigem IGUALDADE entre os dois produtores sobre
    os bytes vivos e sobre os dois membros da família (tombstone em reuse;
    página com fonte não canônica fora do reuse).
    """

    @staticmethod
    def both_producers(raw_lines, expected, rel_path):
        payload = b"\n".join(raw_lines) + b"\n"
        projection = producer.derive_writing_raw_recovery_projection(
            payload, rel_path, producer._sha256(payload), list(expected))
        rows = [json.loads(line) for line in raw_lines]
        completion = producer.classify_batch_completion(
            rows, expected, pathlib.PurePosixPath(rel_path).name, set(),
            semantically_blocked_intents=())
        return projection, completion

    def test_live_source_blocked_tombstones_fill_the_slot_but_never_reuse(self):
        cases = (
            ("aereo-18", LIVE_AEREO_18_PATH, LIVE_AEREO_18_EXPECTED,
             LIVE_AEREO_18_LINES, LIVE_AEREO_18_LINE_SHA256,
             LIVE_AEREO_18_SHA256),
            ("sucessoes2-09", LIVE_SUCESSOES2_09_PATH,
             LIVE_SUCESSOES2_09_EXPECTED, LIVE_SUCESSOES2_09_LINES,
             LIVE_SUCESSOES2_09_LINE_SHA256, LIVE_SUCESSOES2_09_SHA256),
        )
        for label, rel_path, expected, lines, line_shas, file_sha in cases:
            with self.subTest(lote=label):
                for line, digest in zip(lines, line_shas):
                    self.assertEqual(producer._sha256(line), digest)
                    row = json.loads(line)
                    self.assertIs(row["skipped"], True)
                    self.assertEqual(
                        set(row), {"intent_id", "skipped", "skip_reason"})
                    self.assertFalse(producer.writing_reusable_page(row))
                payload = b"\n".join(lines) + b"\n"
                self.assertEqual(producer._sha256(payload), file_sha)
                projection, completion = self.both_producers(
                    lines, expected, rel_path)
                self.assertIsNotNone(projection)
                assert projection is not None
                self.assertEqual(
                    projection["reason_codes"],
                    ["cardinality_mismatch", "intent_order_mismatch"])
                self.assertEqual(projection["reuse"], [])
                self.assertEqual(projection["preserved_record_sha256"], {})
                self.assertFalse(completion.complete)
                self.assertEqual(completion.reusable_expected, ())
                self.assertEqual(
                    list(completion.reusable_expected), projection["reuse"])
        # A tombstone PREENCHE: slice de uma intenção coberto só por ela é
        # lote completo (não reenfileira, não pressiona fabricação) e sem
        # reuse — o slot só volta ao redator quando o lote abrir por outro
        # motivo, e aí é re-decidido com o catálogo atual.
        row = json.loads(LIVE_SUCESSOES2_09_LINES[0])
        completion = producer.classify_batch_completion(
            [row], [row["intent_id"]], "sucessoes2-09.jsonl", set(),
            semantically_blocked_intents=())
        self.assertTrue(completion.complete)
        self.assertEqual(completion.reusable_expected, ())

    def test_reuse_predicate_is_the_same_for_classifier_and_raw_recovery(self):
        expected = ("alpha", "beta", "gamma", "delta", "omega")
        lines = [
            active_row("alpha"),
            closed_tombstone_row("beta"),
            duplicate_url_page_row("gamma"),
            provenance_key_page_row("delta"),
        ]
        projection, completion = self.both_producers(
            lines, expected, "data/editorial/v2_pages/civil-a.jsonl")
        assert projection is not None
        self.assertIn("cardinality_mismatch", projection["reason_codes"])
        self.assertEqual(projection["reuse"], ["alpha", "gamma", "delta"])
        self.assertEqual(
            list(completion.reusable_expected), ["alpha", "gamma", "delta"])
        self.assertEqual(
            set(projection["preserved_record_sha256"]),
            {"alpha", "gamma", "delta"})
        self.assertFalse(completion.complete)
        # Predicado direto: qualquer marca de pulo exclui, mesmo com corpo;
        # corpo vazio exclui; página ativa entra.
        self.assertTrue(
            producer.writing_reusable_page(json.loads(active_row("alpha"))))
        self.assertFalse(producer.writing_reusable_page(
            json.loads(closed_tombstone_row("beta"))))
        self.assertFalse(producer.writing_reusable_page(
            {"intent_id": "x", "skipped": True, "sections": [{"text": "t"}]}))
        self.assertFalse(
            producer.writing_reusable_page({"intent_id": "x", "sections": []}))

    def test_order_only_shard_with_tombstones_leaves_the_mechanical_family(self):
        # Consequência assumida em 2026-09-05: cidadania-04 tem 19 tombstones
        # strict + 3 páginas só fora de ordem. Antes era reordenação mecânica
        # porque ``reuse`` contava as tombstones; agora vai ao redator com as
        # páginas preservadas byte a byte, e cada slot strict só pode voltar
        # como tombstone fechada (o staged recusa página sem fonte exata). Um
        # follow-up que devolva esse caso à família mecânica precisa de um
        # predicado "preservável sob permutação" DISTINTO de ``reuse`` — nunca
        # de voltar a pôr tombstone em ``reuse``.
        expected = ("alpha", "beta", "gamma")
        lines = [
            closed_tombstone_row("beta"),
            closed_tombstone_row("gamma"),
            active_row("alpha"),
        ]
        projection, completion = self.both_producers(
            lines, expected, "data/editorial/v2_pages/civil-a.jsonl")
        assert projection is not None
        self.assertEqual(projection["reason_codes"], ["intent_order_mismatch"])
        self.assertEqual(projection["reuse"], ["alpha"])
        self.assertEqual(list(completion.reusable_expected), ["alpha"])
        self.assertFalse(completion.complete)
        self.assertFalse(
            producer.writing_recovery_mechanical_only(projection, 3))
        self.assertFalse(producer.writer_noop_batch(
            ["alpha"], 3, writing_recovery=projection))
        # UMA página reusável não distingue ordem nenhuma: qualquer permutação
        # de uma lista de um elemento é ela mesma. Este fixture, sozinho,
        # passava verde com os dois produtores ordenando ``reuse`` de formas
        # DIFERENTES — foi assim que a família chegou meio corrigida ao
        # fechamento da fila. A cobertura de ordem está no teste seguinte, com
        # cardinalidade ≥ 2.

    def test_reuse_order_is_the_authenticated_slice_never_the_shard(self):
        """``reuse`` sai na ordem do slice pinado, nos DOIS produtores.

        Segundo membro da família de 2026-09-05. O primeiro (predicado) unificou
        QUAIS intents entram em ``reuse``; este unifica em QUE ORDEM. A
        divergência é invisível com uma página reusável e reprova o fechamento
        com duas: ``derive_writing_raw_recovery_projection`` itera
        ``for intent in expected`` (ordem do slice) e
        ``classify_batch_completion`` varria os registros (ordem do shard).
        Como ``tools/verify_v2_writing_queue_closure.py`` compara o MESMO campo
        ``reuse`` com os dois — ``:385`` contra a raw-recovery e ``:833`` contra
        o classificador — nenhum valor satisfazia os dois ao mesmo tempo, e o
        lote vivo ``cidadania-04`` reprovava com "reuse diverge da preimagem
        autenticada" sem uma única página de diferença entre os produtores.

        O desempate é do slice: quando as ordens divergem, a do shard é o
        DEFEITO que o lote existe para reparar (``intent_order_mismatch``), e
        ``scripts/workflows/writing-mass.js:419`` — o consumidor que executa a
        ordem — recusa qualquer ``reuse`` diferente de
        ``expected_intent_ids.filter(...)``.
        """
        # Membro sintético: duas páginas ativas invertidas entre shard e slice,
        # uma tombstone no meio e uma intenção nunca escrita.
        expected = ("alpha", "beta", "gamma", "delta")
        lines = [
            active_row("gamma"),
            active_row("alpha"),
            closed_tombstone_row("beta"),
        ]
        projection, completion = self.both_producers(
            lines, expected, "data/editorial/v2_pages/civil-a.jsonl")
        assert projection is not None
        self.assertEqual(list(completion.reusable_expected),
                         projection["reuse"])
        # Literal, para que uma regressão de QUALQUER um dos dois produtores
        # falhe com diff legível em vez de "os dois erraram igual".
        self.assertEqual(projection["reuse"], ["alpha", "gamma"])
        self.assertEqual(list(completion.reusable_expected),
                         ["alpha", "gamma"])
        self.assertFalse(completion.complete)
        # A ordem observada NÃO é o contrato: é exatamente o que reprovava.
        observed_order = ["gamma", "alpha"]
        self.assertNotEqual(list(completion.reusable_expected), observed_order)

        # Topologia VIVA de cidadania-04 (2026-09-05), identidade a identidade:
        # o shard é o slice com ``cid-italiana-por-casamento`` deslocado da
        # posição 8 para o fim (22). As 19 tombstones são strict por fonte não
        # resolvida; as 3 páginas ativas ocupam 8/21/22 no slice e 20/21/22 no
        # shard. O CORPO das páginas é sintético de propósito — a invariante
        # aqui é de ORDEM, e o predicado que decide QUAIS linhas entram já é
        # coberto pelos fixtures de bytes vivos acima. A lista esperada é, byte
        # a byte, o ``reuse`` que ``scripts/workflows/writing-mass-todo.js``
        # carrega para esse lote.
        live_slice = (
            'cid-italiana-jus-sanguinis-visao',
            'cid-italiana-via-administrativa-consulado',
            'cid-italiana-via-judicial-italia',
            'cid-italiana-linha-materna-1948',
            'cid-italiana-documentos-certidoes',
            'cid-italiana-decreto-2025-limite-geracoes',
            'cid-italiana-naturalizacao-quebra',
            'cid-italiana-por-casamento',
            'cid-italiana-filhos-menores',
            'cid-passaporte-europeu-apos-cidadania',
            'cid-portuguesa-descendencia-filhos-netos',
            'cid-portuguesa-bisnetos',
            'cid-portuguesa-casamento-uniao',
            'cid-portuguesa-por-residencia',
            'cid-espanhola-lei-nietos-memoria',
            'cid-espanhola-residencia-ibero',
            'cid-espanhola-por-opcao-filhos',
            'cid-alema-descendencia-reparacao',
            'cid-polonesa-descendencia',
            'cid-cidadania-europeia-qual-buscar',
            'cid-naturalizacao-ordinaria-requisitos',
            'cid-naturalizacao-extraordinaria-15-anos',
        )
        live_active = {
            'cid-italiana-por-casamento',
            'cid-naturalizacao-ordinaria-requisitos',
            'cid-naturalizacao-extraordinaria-15-anos',
        }
        live_shard_order = [
            intent for intent in live_slice
            if intent != 'cid-italiana-por-casamento'
        ] + ['cid-italiana-por-casamento']
        live_lines = [
            active_row(intent) if intent in live_active
            else closed_tombstone_row(intent)
            for intent in live_shard_order
        ]
        live_projection, live_completion = self.both_producers(
            live_lines, live_slice,
            "data/editorial/v2_pages/cidadania-04.jsonl")
        assert live_projection is not None
        self.assertEqual(live_projection["reason_codes"],
                         ["intent_order_mismatch"])
        live_reuse = [
            'cid-italiana-por-casamento',
            'cid-naturalizacao-ordinaria-requisitos',
            'cid-naturalizacao-extraordinaria-15-anos',
        ]
        self.assertEqual(live_projection["reuse"], live_reuse)
        self.assertEqual(list(live_completion.reusable_expected), live_reuse)
        # Nenhuma página paga sai do reuse: as 3 ativas continuam preservadas
        # byte a byte, e as 19 tombstones continuam fora dele.
        self.assertEqual(set(live_projection["preserved_record_sha256"]),
                         live_active)
        self.assertFalse(live_completion.complete)

        # CONTROLE QUE CONTINUA REPROVANDO — sem ele isto seria falso-verde.
        # Canonizar a ordem NÃO afrouxa nada: o schema da projeção recusa
        # qualquer ``reuse`` fora da ordem do slice, inclusive uma permutação
        # do MESMO conjunto (é o que a antiga saída do classificador seria).
        permuted = dict(live_projection)
        permuted["reuse"] = [
            'cid-naturalizacao-ordinaria-requisitos',
            'cid-naturalizacao-extraordinaria-15-anos',
            'cid-italiana-por-casamento',
        ]
        self.assertEqual(set(permuted["reuse"]), set(live_reuse))
        permuted["recovery_item_sha256"] = (
            producer.writing_recovery_item_sha256(permuted))
        with self.assertRaisesRegex(
                ValueError, "projeção raw-recovery tem identidade inválida"):
            producer.validate_writing_raw_recovery_projection(
                permuted,
                target_rel_path="data/editorial/v2_pages/cidadania-04.jsonl",
                target_sha256=live_projection["target_sha256"],
                expected_intents=live_slice)
        # Segundo controle, com o mecanismo NOMEADO: o schema não conhece
        # tombstone — quem a exclui é ``writing_reusable_page``, no produtor
        # (coberto em ``test_live_source_blocked_tombstones_fill_the_slot_but_
        # never_reuse``). O que o schema garante é o ACOPLAMENTO
        # ``set(preserved) == set(reuse)``: contrabandear um intent a mais para
        # ``reuse`` — aqui uma das 19 tombstones, já na ordem do slice — é
        # recusado porque ele não tem bytes preservados. Sem esse par, uma
        # ordem canônica sozinha deixaria passar reuse inventado.
        self.assertNotIn(
            'cid-polonesa-descendencia', live_projection["reuse"])
        with_tombstone = dict(live_projection)
        with_tombstone["reuse"] = [
            intent for intent in live_slice
            if intent in live_active or intent == 'cid-polonesa-descendencia'
        ]
        self.assertEqual(
            with_tombstone["reuse"],
            [intent for intent in live_slice
             if intent in set(with_tombstone["reuse"])])
        with_tombstone["recovery_item_sha256"] = (
            producer.writing_recovery_item_sha256(with_tombstone))
        with self.assertRaisesRegex(
                ValueError, "projeção raw-recovery tem identidade inválida"):
            producer.validate_writing_raw_recovery_projection(
                with_tombstone,
                target_rel_path="data/editorial/v2_pages/cidadania-04.jsonl",
                target_sha256=live_projection["target_sha256"],
                expected_intents=live_slice)

    def test_raw_recovery_staged_preserves_noncanonical_page_and_keeps_controls(self):
        path = "data/editorial/v2_pages/civil-a.jsonl"
        preserved_line = duplicate_url_page_row("alpha")
        target_payload = preserved_line  # sem LF terminal: framing raw-recovery
        target_digest = producer._sha256(target_payload)
        expected = ["alpha", "beta"]
        projection = producer.derive_writing_raw_recovery_projection(
            target_payload, path, target_digest, expected)
        assert projection is not None
        self.assertEqual(projection["reuse"], ["alpha"])
        encoded = base64.b64encode(json.dumps(
            projection, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).decode("ascii")
        semantic = producer.WritingSemanticContract(
            digest=SHA_A, unresolved_intents=frozenset(),
            requirement_fingerprints={}, portfolio_rel_paths={},
            target_rel_paths={}, superseded_target_rel_paths={},
            superseded_page_record_sha256={}, evidence_kinds={},
            evidence_rel_paths={}, evidence_sha256={}, dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        resolution = producer.WritingSourceResolution(
            selected_intents=("alpha", "beta"), source_overrides={},
            strict_source_intents=(),
        )
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            target = root / path
            target.parent.mkdir(parents=True)
            target.write_bytes(target_payload)
            evidence = producer.persist_writing_raw_recovery_preimage(
                root, target_payload, target_digest)
            staged = root / "staged.jsonl"

            def verify(staged_payload: bytes):
                staged.write_bytes(staged_payload)
                with (
                    mock.patch.object(
                        producer, "verify_writing_source_resolution",
                        return_value=resolution),
                    mock.patch.object(
                        producer, "load_writing_semantic_contract",
                        return_value=semantic),
                    mock.patch.object(
                        producer,
                        "verify_writing_semantic_contract_dependencies"),
                ):
                    return producer.verify_staged_writing_recovery(
                        root, staged, path, target_digest,
                        "data/editorial/portfolio_v2/civil.jsonl", SHA_B,
                        "data/editorial/v2_source_hint_catalog.json", SHA_C,
                        ["familia"], 0, 2, 2, None, "ignored", encoded,
                        evidence)

            # Membro B ponta a ponta: a página preservada (URL repetida) passa
            # byte a byte; antes ela caía como escrita nova e reprovava em
            # "official_sources duplica URL", mandando reautorar texto pago.
            good = preserved_line + b"\n" + active_row("beta") + b"\n"
            self.assertEqual(verify(good).payload, good)
            # Re-decisão sem fabricação: o slot NÃO preservado aceita
            # tombstone fechada.
            with_tombstone = (
                preserved_line + b"\n" + closed_tombstone_row("beta") + b"\n")
            self.assertEqual(verify(with_tombstone).payload, with_tombstone)
            # CONTROLES que continuam reprovando (nomeados): linha NOVA com
            # URL repetida; tombstone com chave extra; linha preservada
            # alterada.
            with self.assertRaisesRegex(ValueError, "duplica URL"):
                verify(
                    preserved_line + b"\n" + duplicate_url_page_row("beta") +
                    b"\n")
            open_tombstone = json.dumps({
                "intent_id": "beta", "skipped": True,
                "skip_reason": "fonte indisponivel",
                "index_policy": "noindex",
            }, separators=(",", ":")).encode("utf-8")
            with self.assertRaisesRegex(ValueError, "não é fechada"):
                verify(preserved_line + b"\n" + open_tombstone + b"\n")
            tampered = json.loads(preserved_line)
            tampered["sections"][0]["text"] = "Texto alterado."
            tampered_line = json.dumps(
                tampered, ensure_ascii=False,
                separators=(",", ":")).encode("utf-8")
            with self.assertRaisesRegex(
                    ValueError, "alterou registro preservado"):
                verify(tampered_line + b"\n" + active_row("beta") + b"\n")


if __name__ == "__main__":
    unittest.main()
