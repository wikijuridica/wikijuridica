#!/usr/bin/env python3
"""Testes adversariais da projeção exata de fontes da fila v2."""

from __future__ import annotations

import base64
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools import generate_v2_review_queue as producer


def canonical_json(value: object) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ) + "\n").encode("utf-8")


def encode_projection(value: object) -> str:
    return base64.b64encode(json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")).decode("ascii")


class WritingSourceResolutionTest(unittest.TestCase):
    def test_atomic_cas_aborts_on_dependency_drift_and_preserves_both_sides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            dependency = root / "portfolio.jsonl"

            def exercise(target: pathlib.Path, initial: bytes | None,
                         staged: bytes) -> None:
                dependency.write_bytes(b"epoch-one\n")
                if initial is not None:
                    target.write_bytes(initial)
                expected = producer.snapshot_sha256(target)
                epoch = {dependency: producer.snapshot_sha256(dependency)}
                original_assert = producer._assert_dependency_epoch
                calls = 0

                def drift_on_postcheck(dependencies):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        dependency.write_bytes(b"epoch-two\n")
                    return original_assert(dependencies)

                with mock.patch.object(
                        producer, "_assert_dependency_epoch",
                        drift_on_postcheck):
                    with self.assertRaises(producer.CASMismatch):
                        producer.atomic_replace_cas(
                            target, staged, expected,
                            dependency_sha256=epoch)
                if initial is None:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), initial)
                recoveries = list(root.glob(
                    f".{target.name}.stale-cas-dependency-drift-*"))
                self.assertTrue(any(
                    path.read_bytes() == staged for path in recoveries))

            exercise(root / "existing.jsonl", b"original\n", b"staged\n")
            exercise(root / "missing.jsonl", None, b"staged-new\n")

            dependency.write_bytes(b"stable\n")
            stable = root / "stable.jsonl"
            stable.write_bytes(b"before\n")
            producer.atomic_replace_cas(
                stable, b"after\n", producer.snapshot_sha256(stable),
                dependency_sha256={
                    dependency: producer.snapshot_sha256(dependency)},
            )
            self.assertEqual(stable.read_bytes(), b"after\n")

    def test_fifo_is_rejected_without_blocking_on_open(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = pathlib.Path(directory) / "staged.fifo"
            os.mkfifo(fifo)
            code = (
                "from tools import generate_v2_review_queue as p; "
                "import pathlib,sys; "
                "p.read_regular_file_snapshot(pathlib.Path(sys.argv[1]))"
            )
            completed = subprocess.run(
                [sys.executable, "-c", code, str(fifo)],
                cwd=pathlib.Path(__file__).resolve().parent.parent,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("arquivo regular", completed.stderr)

    def test_snapshot_limit_is_enforced_before_returning_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "oversized.json"
            path.write_bytes(b"1234")
            with self.assertRaisesRegex(ValueError, "excede limite de 3 bytes"):
                producer.read_regular_file_snapshot(path, max_bytes=3)
            with self.assertRaisesRegex(ValueError, "excede limite de 3 bytes"):
                producer.snapshot_sha256(path, max_bytes=3)

    def setUp(self) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-source-resolution-"))
        self.addCleanup(lambda: shutil.rmtree(self.root))
        self.portfolio_rel = "data/editorial/portfolio_v2/seguros.jsonl"
        self.catalog_rel = "data/editorial/v2_source_hint_catalog.json"
        self.target_rel = "data/editorial/v2_pages/seguros-01.jsonl"
        self.source_a = {
            "name": "Lei específica A",
            "url": "https://www.planalto.gov.br/lei-a",
            "anchor_claim": "regra material específica A",
        }
        self.source_b = {
            "name": "Lei específica B",
            "url": "https://www.planalto.gov.br/lei-b",
            "anchor_claim": "regra material específica B",
        }
        records = [
            {
                "intent_id": "seg-dpvat-a",
                "family": "dpvat-spvat",
                "source_hints": ["fonte-especifica-a"],
                "needs_source_research": False,
            },
            {
                "intent_id": "seg-dpvat-b",
                "family": "dpvat-spvat",
                "source_hints": ["fonte-especifica-b"],
                "needs_source_research": False,
            },
            {
                "intent_id": "seg-outra",
                "family": "outra-familia",
                "source_hints": [],
                "needs_source_research": True,
            },
        ]
        self.portfolio = b"".join(canonical_json(record) for record in records)
        self.catalog = canonical_json({
            "_meta": {
                "schema_version": 1,
                "purpose": "resolve fontes exatas antes da escrita",
                "source_policy": "somente fonte oficial específica",
            },
            "strict_intents": ["seg-dpvat-a", "seg-dpvat-b"],
            "source_hints": {
                "fonte-especifica-a": self.source_a,
                "fonte-especifica-b": self.source_b,
            },
        })
        for rel, payload in (
            (self.portfolio_rel, self.portfolio),
            (self.catalog_rel, self.catalog),
        ):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        (self.root / self.target_rel).parent.mkdir(parents=True, exist_ok=True)
        self.expected = {
            "source_overrides": {
                "seg-dpvat-a": {"fonte-especifica-a": self.source_a},
                "seg-dpvat-b": {"fonte-especifica-b": self.source_b},
            },
            "strict_source_intents": ["seg-dpvat-a", "seg-dpvat-b"],
        }
        self.intent_ids = ["seg-dpvat-a", "seg-dpvat-b"]
        semantic_contract = producer.WritingSemanticContract(
            digest="0" * 64,
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
        semantic_loader = mock.patch.object(
            producer, "load_writing_semantic_contract",
            return_value=semantic_contract)
        semantic_dependencies = mock.patch.object(
            producer, "verify_writing_semantic_contract_dependencies")
        semantic_loader.start()
        semantic_dependencies.start()
        self.addCleanup(semantic_loader.stop)
        self.addCleanup(semantic_dependencies.stop)

    def verify(self, projection: object, *, families=None, expected_n=2) -> None:
        producer.verify_writing_source_resolution(
            self.root,
            self.portfolio_rel,
            producer._sha256(self.portfolio),
            self.catalog_rel,
            producer._sha256(self.catalog),
            ["dpvat-spvat"] if families is None else families,
            0,
            0,
            expected_n,
            self.intent_ids,
            encode_projection(projection),
        )

    def staged_payload(self, source_a=None, source_b=None) -> bytes:
        return b"".join(canonical_json(record) for record in (
            {
                "intent_id": "seg-dpvat-a",
                "official_sources": [self.source_a if source_a is None else source_a],
            },
            {
                "intent_id": "seg-dpvat-b",
                "official_sources": [self.source_b if source_b is None else source_b],
            },
        ))

    def verify_staged(
        self,
        staged: pathlib.Path,
        projection: object | None = None,
        preservation: object | None = None,
    ) -> producer.RegularFileSnapshot:
        return producer.verify_staged_writing_source_resolution(
            self.root,
            staged,
            self.target_rel,
            producer.snapshot_sha256(self.root / self.target_rel),
            self.portfolio_rel,
            producer._sha256(self.portfolio),
            self.catalog_rel,
            producer._sha256(self.catalog),
            ["dpvat-spvat"],
            0,
            0,
            2,
            self.intent_ids,
            encode_projection(self.expected if projection is None else projection),
            None if preservation is None else encode_projection(preservation),
        )

    def test_exact_projection_passes(self) -> None:
        self.verify(self.expected)

    def derive_from_records(self, records):
        payload = b"".join(canonical_json(record) for record in records)
        (self.root / self.portfolio_rel).write_bytes(payload)
        return producer.derive_writing_source_resolution(
            self.root, self.portfolio_rel, producer._sha256(payload),
            self.catalog_rel, producer._sha256(self.catalog),
            ["dpvat-spvat"], 0, 0, 1, [records[0]["intent_id"]])

    def test_completed_research_with_unresolved_hint_fails_closed(self) -> None:
        record = {
            "intent_id": "seg-nao-strict", "family": "dpvat-spvat",
            "source_hints": ["fonte-ausente"],
            "needs_source_research": False,
        }
        with self.assertRaisesRegex(
                ValueError, "pesquisa concluída sem resolução exata"):
            self.derive_from_records([record])

    def test_pending_research_is_tombstone_only_strict_without_override(self) -> None:
        record = {
            "intent_id": "seg-nao-strict", "family": "dpvat-spvat",
            "source_hints": ["fonte-ausente"],
            "needs_source_research": True,
        }
        resolution = self.derive_from_records([record])
        self.assertEqual(resolution.strict_source_intents,
                         ("seg-nao-strict",))
        self.assertEqual(resolution.source_overrides, {})

    def test_mixed_pending_research_blocks_page_even_citing_resolved_source(
            self) -> None:
        # Controle negativo da família "zeramento do resolvedor": intent com
        # pesquisa aberta e hints MISTOS (um resolvido no catálogo, um não)
        # nunca pode materializar página — nem citando só a fonte resolvida.
        # O mecanismo é o par {strict sem override} disparando
        # "intent strict sem source_hints materializados" no verificador
        # staged. Preservar override parcial desarmaria exatamente esse
        # gatilho; este teste pina a barreira e prova, no mesmo cenário, que
        # o intent saudável do lote segue materializando sua fonte exata.
        records = [
            {
                "intent_id": "seg-misto",
                "family": "dpvat-spvat",
                "source_hints": ["fonte-especifica-a", "fonte-pendente"],
                "needs_source_research": True,
            },
            {
                "intent_id": "seg-dpvat-b",
                "family": "dpvat-spvat",
                "source_hints": ["fonte-especifica-b"],
                "needs_source_research": False,
            },
        ]
        portfolio = b"".join(canonical_json(record) for record in records)
        (self.root / self.portfolio_rel).write_bytes(portfolio)
        pins = ["seg-misto", "seg-dpvat-b"]
        resolution = producer.derive_writing_source_resolution(
            self.root, self.portfolio_rel, producer._sha256(portfolio),
            self.catalog_rel, producer._sha256(self.catalog),
            ["dpvat-spvat"], 0, 0, 2, pins)
        # O zeramento é por intenção: o hint resolvido do intent misto não
        # vira override, e o intent saudável não perde nada.
        self.assertEqual(resolution.strict_source_intents,
                         ("seg-dpvat-b", "seg-misto"))
        self.assertEqual(resolution.source_overrides, {
            "seg-dpvat-b": {"fonte-especifica-b": self.source_b},
        })
        projection = encode_projection({
            "source_overrides": {
                "seg-dpvat-b": {"fonte-especifica-b": self.source_b},
            },
            "strict_source_intents": ["seg-dpvat-b", "seg-misto"],
        })

        def verify_staged_mixed(payload: bytes) -> producer.RegularFileSnapshot:
            staged = self.root / "final-misto.jsonl"
            staged.write_bytes(payload)
            return producer.verify_staged_writing_source_resolution(
                self.root, staged, self.target_rel,
                producer.snapshot_sha256(self.root / self.target_rel),
                self.portfolio_rel, producer._sha256(portfolio),
                self.catalog_rel, producer._sha256(self.catalog),
                ["dpvat-spvat"], 0, 0, 2, pins, projection, None)

        materialized_page = canonical_json({
            "intent_id": "seg-misto",
            "official_sources": [self.source_a],
        })
        healthy_page = canonical_json({
            "intent_id": "seg-dpvat-b",
            "official_sources": [self.source_b],
        })
        with self.assertRaisesRegex(
                ValueError,
                "intent strict sem source_hints materializados: seg-misto"):
            verify_staged_mixed(materialized_page + healthy_page)

        tombstone = canonical_json({
            "intent_id": "seg-misto",
            "skipped": True,
            "skip_reason": "fonte-pendente sem resolução exata no catálogo",
        })
        accepted = tombstone + healthy_page
        snapshot = verify_staged_mixed(accepted)
        self.assertEqual(snapshot.payload, accepted)

    def test_source_urls_over_workflow_limit_fail_closed(self) -> None:
        def at_utf8_limit(prefix: str) -> str:
            remaining = (
                producer._MAX_OFFICIAL_SOURCE_URL_BYTES -
                len(prefix.encode("utf-8"))
            )
            self.assertGreater(remaining, 2)
            return (prefix + "á" * (remaining // 2) +
                    "a" * (remaining % 2))

        oversized = (
            "https://www.planalto.gov.br/" +
            "a" * producer._MAX_OFFICIAL_SOURCE_URL_BYTES
        )
        oversized_query = (
            "https://www.planalto.gov.br/ato?id=" +
            "a" * producer._MAX_OFFICIAL_SOURCE_URL_BYTES
        )
        for label, url in (
            ("path", oversized),
            ("query", oversized_query),
        ):
            with self.subTest(label=label):
                self.assertGreater(
                    len(url), producer._MAX_OFFICIAL_SOURCE_URL_BYTES)
                with self.assertRaisesRegex(
                        ValueError, "URL candidata oficial HTTPS inválida"):
                    producer._canonical_candidate_source({
                        "name": "Portal oficial",
                        "url": url,
                    }, f"fonte:{label}")
                with self.assertRaisesRegex(
                        ValueError, "URL oficial HTTPS inválida"):
                    producer._canonical_exact_source({
                        "name": "Ato oficial",
                        "url": url,
                        "anchor_claim": "regra jurídica específica",
                    }, f"fonte-exata:{label}")

        for label, prefix in (
            ("path", "https://www.planalto.gov.br/ato/"),
            ("query", "https://www.planalto.gov.br/ato?id="),
        ):
            exact_limit = at_utf8_limit(prefix)
            self.assertEqual(
                len(exact_limit.encode("utf-8")),
                producer._MAX_OFFICIAL_SOURCE_URL_BYTES,
            )
            self.assertLess(len(exact_limit),
                            producer._MAX_OFFICIAL_SOURCE_URL_BYTES)
            producer._canonical_candidate_source({
                "name": "Portal oficial",
                "url": exact_limit,
            }, f"fonte-limite:{label}")
            producer._canonical_exact_source({
                "name": "Ato oficial",
                "url": exact_limit,
                "anchor_claim": "regra jurídica específica",
            }, f"fonte-exata-limite:{label}")

            utf8_oversized = exact_limit + "á"
            self.assertLess(len(utf8_oversized),
                            producer._MAX_OFFICIAL_SOURCE_URL_BYTES)
            self.assertGreater(
                len(utf8_oversized.encode("utf-8")),
                producer._MAX_OFFICIAL_SOURCE_URL_BYTES,
            )
            with self.assertRaisesRegex(
                    ValueError, "URL candidata oficial HTTPS inválida"):
                producer._canonical_candidate_source({
                    "name": "Portal oficial",
                    "url": utf8_oversized,
                }, f"fonte-utf8:{label}")
            with self.assertRaisesRegex(
                    ValueError, "URL oficial HTTPS inválida"):
                producer._canonical_exact_source({
                    "name": "Ato oficial",
                    "url": utf8_oversized,
                    "anchor_claim": "regra jurídica específica",
                }, f"fonte-exata-utf8:{label}")

        invalid_unicode = "https://www.planalto.gov.br/ato/\ud800"
        with self.assertRaisesRegex(
                ValueError, "URL candidata oficial HTTPS inválida"):
            producer._canonical_candidate_source({
                "name": "Portal oficial",
                "url": invalid_unicode,
            }, "fonte-surrogate")
        with self.assertRaisesRegex(
                ValueError,
                "(?:URL oficial HTTPS inválida|url não é texto canônico)"):
            producer._canonical_exact_source({
                "name": "Ato oficial",
                "url": invalid_unicode,
                "anchor_claim": "regra jurídica específica",
            }, "fonte-exata-surrogate")

    def test_pinned_selector_derives_exact_order_independent_of_portfolio_order(self):
        reordered = b"".join(reversed(self.portfolio.splitlines(keepends=True)))
        (self.root / self.portfolio_rel).write_bytes(reordered)
        resolution = producer.derive_writing_source_resolution(
            self.root,
            self.portfolio_rel,
            producer._sha256(reordered),
            self.catalog_rel,
            producer._sha256(self.catalog),
            ["dpvat-spvat"],
            0,
            0,
            2,
            ["seg-dpvat-a", "seg-dpvat-b"],
        )
        self.assertEqual(
            resolution.selected_intents,
            ("seg-dpvat-a", "seg-dpvat-b"),
        )
        self.assertEqual(dict(resolution.source_overrides),
                         self.expected["source_overrides"])

    def test_pinned_selector_rejects_missing_duplicate_unknown_and_wrong_family(self):
        common = (
            self.root,
            self.portfolio_rel,
            producer._sha256(self.portfolio),
            self.catalog_rel,
            producer._sha256(self.catalog),
        )
        invalid = (
            (None, 2, ["dpvat-spvat"], "seletor"),
            ([], 2, ["dpvat-spvat"], "seletor"),
            (["seg-dpvat-a", "seg-dpvat-a"], 2,
             ["dpvat-spvat"], "seletor"),
            (["seg-inexistente"], 1,
             ["dpvat-spvat"], "não existe"),
            (["seg-outra"], 1,
             ["dpvat-spvat"], "families declaradas"),
        )
        for pins, count, families, message in invalid:
            with self.subTest(pins=pins):
                with self.assertRaisesRegex(ValueError, message):
                    producer.derive_writing_source_resolution(
                        *common, families, 0, 0, count, pins)

    def test_pinned_selector_requires_complete_ordered_family_runs(self):
        common = (
            self.root,
            self.portfolio_rel,
            producer._sha256(self.portfolio),
            self.catalog_rel,
            producer._sha256(self.catalog),
            ["dpvat-spvat", "outra-familia"],
            0,
            0,
        )
        valid = producer.derive_writing_source_resolution(
            *common, 3, ["seg-dpvat-a", "seg-dpvat-b", "seg-outra"])
        self.assertEqual(
            valid.selected_intents,
            ("seg-dpvat-a", "seg-dpvat-b", "seg-outra"),
        )
        for pins in (
            ["seg-dpvat-a", "seg-dpvat-b"],
            ["seg-outra", "seg-dpvat-a", "seg-dpvat-b"],
            ["seg-dpvat-a", "seg-outra", "seg-dpvat-b"],
        ):
            with self.subTest(pins=pins):
                with self.assertRaisesRegex(ValueError, "families declaradas"):
                    producer.derive_writing_source_resolution(
                        *common, len(pins), pins)

    def test_positional_selector_requires_pin_field_absent(self):
        common = (
            self.root,
            self.portfolio_rel,
            producer._sha256(self.portfolio),
            self.catalog_rel,
            producer._sha256(self.catalog),
            ["dpvat-spvat"],
            0,
            2,
            2,
        )
        resolution = producer.derive_writing_source_resolution(*common, None)
        self.assertEqual(resolution.selected_intents, tuple(self.intent_ids))
        with self.assertRaisesRegex(ValueError, "seletor"):
            producer.derive_writing_source_resolution(*common, [])

    def test_pending_legacy_hints_are_tombstone_only_until_resolved(self):
        records = [
            {
                "intent_id": "seg-legado",
                "family": "legado",
                "source_hints": ["CLT art. 477", "Lei 8.036/1990 art. 18"],
                "needs_source_research": True,
            },
        ]
        portfolio = b"".join(canonical_json(record) for record in records)
        portfolio_path = self.root / self.portfolio_rel
        portfolio_path.write_bytes(portfolio)
        producer.verify_writing_source_resolution(
            self.root, self.portfolio_rel, producer._sha256(portfolio),
            self.catalog_rel, producer._sha256(self.catalog),
            ["legado"], 0, 0, 1, ["seg-legado"],
            encode_projection({
                "source_overrides": {},
                "strict_source_intents": ["seg-legado"],
            }),
        )

        catalog_value = json.loads(self.catalog)
        catalog_value["strict_intents"] = ["seg-legado"]
        catalog = canonical_json(catalog_value)
        (self.root / self.catalog_rel).write_bytes(catalog)
        with self.assertRaisesRegex(ValueError, "strict sem resolução exata"):
            producer.verify_writing_source_resolution(
                self.root, self.portfolio_rel, producer._sha256(portfolio),
                self.catalog_rel, producer._sha256(catalog),
                ["legado"], 0, 0, 1, ["seg-legado"],
                encode_projection({
                    "source_overrides": {},
                    "strict_source_intents": ["seg-legado"],
                }),
            )

    def test_irrelevant_but_official_source_cannot_replace_exact_hint(self) -> None:
        tampered = json.loads(json.dumps(self.expected))
        tampered["source_overrides"]["seg-dpvat-a"]["fonte-especifica-a"] = (
            self.source_b
        )
        with self.assertRaisesRegex(ValueError, "divergem da projeção exata"):
            self.verify(tampered)

    def test_strict_intent_and_selector_tampering_fail_closed(self) -> None:
        tampered = json.loads(json.dumps(self.expected))
        tampered["strict_source_intents"] = ["seg-dpvat-a"]
        with self.assertRaisesRegex(ValueError, "divergem da projeção exata"):
            self.verify(tampered)
        with self.assertRaisesRegex(ValueError, "families declaradas"):
            self.verify(self.expected, families=["outra-familia"])
        with self.assertRaisesRegex(ValueError, "seletor"):
            self.verify(self.expected, expected_n=1)

    def test_catalog_and_portfolio_hashes_are_rechecked(self) -> None:
        (self.root / self.catalog_rel).write_bytes(self.catalog + b"\n")
        with self.assertRaisesRegex(producer.CASMismatch, "mudou depois da fila"):
            self.verify(self.expected)

    def test_catalog_schema_and_duplicate_keys_fail_closed(self) -> None:
        catalog_path = self.root / self.catalog_rel
        value = json.loads(self.catalog)
        value["_meta"].pop("source_policy")
        invalid_meta = canonical_json(value)
        catalog_path.write_bytes(invalid_meta)
        with self.assertRaisesRegex(ValueError, "_meta"):
            producer.verify_writing_source_resolution(
                self.root,
                self.portfolio_rel,
                producer._sha256(self.portfolio),
                self.catalog_rel,
                producer._sha256(invalid_meta),
                ["dpvat-spvat"], 0, 0, 2, self.intent_ids,
                encode_projection(self.expected),
            )

        duplicate = self.catalog.replace(
            b'"strict_intents":', b'"_meta":{},"strict_intents":', 1)
        catalog_path.write_bytes(duplicate)
        with self.assertRaisesRegex(ValueError, "chave JSON duplicada"):
            producer.verify_writing_source_resolution(
                self.root,
                self.portfolio_rel,
                producer._sha256(self.portfolio),
                self.catalog_rel,
                producer._sha256(duplicate),
                ["dpvat-spvat"], 0, 0, 2, self.intent_ids,
                encode_projection(self.expected),
            )

    def test_staged_materialization_is_exact_and_same_snapshot_reaches_cas(self):
        staged = self.root / "workspace" / "final.jsonl"
        staged.parent.mkdir()
        verified_payload = self.staged_payload()
        staged.write_bytes(verified_payload)
        snapshot = self.verify_staged(staged)

        # Uma troca posterior do path não pode trocar os bytes já autenticados.
        staged.write_bytes(self.staged_payload(source_a=self.source_b))
        target = self.root / "target.jsonl"
        target.write_bytes(b"preimage\n")
        producer.atomic_replace_cas(
            target, snapshot.payload, producer.snapshot_sha256(target))
        self.assertEqual(target.read_bytes(), verified_payload)

    def test_staged_shape_and_preserved_bytes_are_authenticated(self):
        staged = self.root / "final-preserved.jsonl"
        rows = [json.loads(line) for line in self.staged_payload().splitlines()]
        rows[0]["sections"] = [
            {"heading": "Página existente", "text": "Preservada."},
        ]
        extra = {
            "intent_id": "seg-extra-autenticado",
            "sections": [{"heading": "Evolução", "text": "Preservada."}],
        }
        extra_raw = canonical_json(extra)[:-1]
        payload = b"".join(canonical_json(row) for row in rows) + extra_raw + b"\n"
        staged.write_bytes(payload)
        # A fila só pode declarar hashes derivados desta preimagem CAS, nunca
        # dos próprios bytes que pretende promover.
        (self.root / self.target_rel).write_bytes(
            canonical_json(rows[0]) + extra_raw + b"\n")
        preservation = {
            "reuse": ["seg-dpvat-a"],
            "preserve_extras": ["seg-extra-autenticado"],
            "preserved_record_sha256": {
                "seg-dpvat-a": producer._sha256(canonical_json(rows[0])[:-1]),
                "seg-extra-autenticado": producer._sha256(extra_raw),
            },
            "authenticated_replacement": False,
            "semantic_contract_sha256": "0" * 64,
            "semantic_relocation_removals": [],
        }
        with self.assertRaisesRegex(ValueError, "sem vencedor DEC-020"):
            self.verify_staged(staged, preservation=preservation)
        self.enterContext(mock.patch(
            "tools.audit_v2_pages.validated_duplicate_supersession_winners",
            return_value=({
                ("seguros-01.jsonl", "seg-extra-autenticado"),
            }, []),
        ))
        snapshot = self.verify_staged(staged, preservation=preservation)
        self.assertEqual(snapshot.payload, payload)

        changed_extra = dict(extra)
        changed_extra["sections"] = [
            {"heading": "Evolução", "text": "Alterada silenciosamente."},
        ]
        staged.write_bytes(
            b"".join(canonical_json(row) for row in rows) +
            canonical_json(changed_extra))
        with self.assertRaisesRegex(ValueError, "mudou byte a byte"):
            self.verify_staged(staged, preservation=preservation)

        staged.write_bytes(payload + canonical_json({
            "intent_id": "seg-extra-nao-autorizado",
        }))
        with self.assertRaisesRegex(ValueError, "fila exige"):
            self.verify_staged(staged, preservation=preservation)

        forged = json.loads(json.dumps(preservation))
        forged_row = dict(rows[0])
        forged_row["official_sources"] = [self.source_b]
        forged["preserved_record_sha256"]["seg-dpvat-a"] = (
            producer._sha256(canonical_json(forged_row)[:-1])
        )
        staged.write_bytes(
            canonical_json(forged_row) + canonical_json(rows[1]) +
            extra_raw + b"\n")
        with self.assertRaisesRegex(ValueError, "diverge da preimagem"):
            self.verify_staged(staged, preservation=forged)

    def test_staged_relocation_requires_exact_resolution_before_removal(self):
        staged = self.root / "final-relocation.jsonl"
        row_a = {
            "intent_id": "seg-dpvat-a",
            "official_sources": [self.source_a],
            "sections": [{"heading": "Existente", "text": "Preservada."}],
        }
        row_b = {
            "intent_id": "seg-dpvat-b",
            "official_sources": [self.source_b],
            "sections": [{"heading": "Nova", "text": "Materializada."}],
        }
        relocated = {
            "intent_id": "seg-relocado-antigo",
            "sections": [{"heading": "Antigo", "text": "Owner superado."}],
        }
        row_a_raw = canonical_json(row_a)[:-1]
        relocated_raw = canonical_json(relocated)[:-1]
        (self.root / self.target_rel).write_bytes(
            row_a_raw + b"\n" + relocated_raw + b"\n")
        staged.write_bytes(canonical_json(row_a) + canonical_json(row_b))
        contract = producer.WritingSemanticContract(
            digest="9" * 64,
            unresolved_intents=frozenset({"seg-relocado-antigo"}),
            requirement_fingerprints={"seg-relocado-antigo": "8" * 64},
            portfolio_rel_paths={
                "seg-relocado-antigo": self.portfolio_rel},
            target_rel_paths={
                "seg-relocado-antigo":
                "data/editorial/v2_pages/seguros-02.jsonl"},
            superseded_target_rel_paths={
                "seg-relocado-antigo": self.target_rel},
            superseded_page_record_sha256={
                "seg-relocado-antigo": producer._sha256(relocated_raw)},
            evidence_kinds={
                "seg-relocado-antigo": "duplicate_supersession_record"},
            evidence_rel_paths={"seg-relocado-antigo": "evidence"},
            evidence_sha256={"seg-relocado-antigo": "7" * 64},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        removals = list(producer.semantic_relocation_removals_for_target(
            self.target_rel,
            ((row_a_raw, row_a), (relocated_raw, relocated)),
            contract,
        ))
        preservation = {
            "reuse": ["seg-dpvat-a"],
            "preserve_extras": [],
            "preserved_record_sha256": {
                "seg-dpvat-a": producer._sha256(row_a_raw)},
            "authenticated_replacement": False,
            "semantic_contract_sha256": contract.digest,
            "semantic_relocation_removals": removals,
        }
        with mock.patch.object(
                producer, "load_writing_semantic_contract",
                return_value=contract):
            with self.assertRaisesRegex(ValueError, "antes da resolução"):
                self.verify_staged(staged, preservation=preservation)

        resolved = contract._replace(unresolved_intents=frozenset())
        with mock.patch.object(
                producer, "load_writing_semantic_contract",
                return_value=resolved):
            snapshot = self.verify_staged(staged, preservation=preservation)
        self.assertEqual(snapshot.payload, staged.read_bytes())

    def test_closed_tombstone_does_not_force_source_fabrication(self):
        staged = self.root / "final-tombstone.jsonl"
        rows = [
            {
                "intent_id": "seg-dpvat-a",
                "skipped": True,
                "skip_reason": "fonte oficial indisponível no probe live",
            },
            json.loads(self.staged_payload().splitlines()[1]),
        ]
        staged.write_bytes(b"".join(canonical_json(row) for row in rows))
        self.verify_staged(staged)

        rows[0]["official_sources"] = [self.source_a]
        staged.write_bytes(b"".join(canonical_json(row) for row in rows))
        with self.assertRaisesRegex(ValueError, "tombstone de escrita não é fechada"):
            self.verify_staged(staged)

    def test_staged_rejects_fabricated_live_metadata_and_nonofficial_extra(self):
        staged = self.root / "final-untrusted-source.jsonl"
        fabricated = dict(self.source_a)
        fabricated.update({"verified_at": "2099-01-01", "http_status": 200})
        staged.write_bytes(self.staged_payload(source_a=fabricated))
        with self.assertRaisesRegex(ValueError, "schema inválido"):
            self.verify_staged(staged)

        rows = [json.loads(line) for line in self.staged_payload().splitlines()]
        rows[0]["official_sources"].append({
            "name": "Metadata local",
            "url": "http://169.254.169.254/latest/meta-data",
            "anchor_claim": "não é fonte oficial",
        })
        staged.write_bytes(b"".join(canonical_json(row) for row in rows))
        with self.assertRaisesRegex(ValueError, "não é fonte oficial permitida"):
            self.verify_staged(staged)

        # A mesma barreira vale para intenções sem source_hint exato; caso
        # contrário a maioria do portfólio ainda poderia alimentar SSRF/live.
        staged.write_bytes(canonical_json({
            "intent_id": "seg-outra",
            "official_sources": [{
                "name": "Metadata local",
                "url": "http://169.254.169.254/latest/meta-data",
                "anchor_claim": "não é fonte oficial",
                "verified_at": "2099-01-01",
                "http_status": 200,
            }],
        }))
        empty_projection = {
            "source_overrides": {},
            "strict_source_intents": [],
        }
        with self.assertRaisesRegex(ValueError, "schema inválido"):
            producer.verify_staged_writing_source_resolution(
                self.root,
                staged,
                self.target_rel,
                producer.snapshot_sha256(self.root / self.target_rel),
                self.portfolio_rel,
                producer._sha256(self.portfolio),
                self.catalog_rel,
                producer._sha256(self.catalog),
                ["outra-familia"],
                0,
                0,
                1,
                ["seg-outra"],
                encode_projection(empty_projection),
            )

    def test_staged_rejects_irrelevant_source_anchor_order_and_indirect_path(self):
        staged = self.root / "final.jsonl"
        staged.write_bytes(self.staged_payload(source_a=self.source_b))
        with self.assertRaisesRegex(ValueError, "perdeu fonte exata"):
            self.verify_staged(staged)

        wrong_anchor = dict(self.source_a)
        wrong_anchor["anchor_claim"] = "claim oficial, mas materialmente diferente"
        staged.write_bytes(self.staged_payload(source_a=wrong_anchor))
        with self.assertRaisesRegex(ValueError, "fonte material diverge"):
            self.verify_staged(staged)

        rows = [json.loads(line) for line in self.staged_payload().splitlines()]
        staged.write_bytes(b"".join(canonical_json(row) for row in reversed(rows)))
        with self.assertRaisesRegex(ValueError, "ordem integral dos intent_ids"):
            self.verify_staged(staged)

        real = self.root / "real-final.jsonl"
        real.write_bytes(self.staged_payload())
        staged.unlink()
        staged.symlink_to(real)
        with self.assertRaises((OSError, RuntimeError)):
            self.verify_staged(staged)

    def test_duplicate_url_requires_deterministic_lossless_consolidation(self):
        alias = {
            "name": "Lei específica A, segundo dispositivo",
            "url": self.source_a["url"],
            "anchor_claim": "regra material específica A2",
        }
        portfolio_records = [json.loads(line) for line in self.portfolio.splitlines()]
        portfolio_records[0]["source_hints"] = [
            "fonte-especifica-a", "fonte-especifica-z",
        ]
        portfolio = b"".join(canonical_json(row) for row in portfolio_records)
        catalog_value = json.loads(self.catalog)
        catalog_value["source_hints"]["fonte-especifica-z"] = alias
        catalog = canonical_json(catalog_value)
        (self.root / self.portfolio_rel).write_bytes(portfolio)
        (self.root / self.catalog_rel).write_bytes(catalog)
        projection = json.loads(json.dumps(self.expected))
        projection["source_overrides"]["seg-dpvat-a"][
            "fonte-especifica-z"
        ] = alias
        consolidated = {
            "name": self.source_a["name"],
            "url": self.source_a["url"],
            "anchor_claim": (
                self.source_a["anchor_claim"] + " | " + alias["anchor_claim"]
            ),
        }
        staged = self.root / "consolidated.jsonl"
        staged.write_bytes(self.staged_payload(source_a=consolidated))
        producer.verify_staged_writing_source_resolution(
            self.root,
            staged,
            self.target_rel,
            producer.snapshot_sha256(self.root / self.target_rel),
            self.portfolio_rel,
            producer._sha256(portfolio),
            self.catalog_rel,
            producer._sha256(catalog),
            ["dpvat-spvat"],
            0,
            0,
            2,
            self.intent_ids,
            encode_projection(projection),
        )
        divergent = dict(consolidated)
        divergent["anchor_claim"] = "regra material específica A2"
        staged.write_bytes(self.staged_payload(source_a=divergent))
        with self.assertRaisesRegex(ValueError, "fonte material diverge"):
            producer.verify_staged_writing_source_resolution(
                self.root,
                staged,
                self.target_rel,
                producer.snapshot_sha256(self.root / self.target_rel),
                self.portfolio_rel,
                producer._sha256(portfolio),
                self.catalog_rel,
                producer._sha256(catalog),
                ["dpvat-spvat"],
                0,
                0,
                2,
                self.intent_ids,
                encode_projection(projection),
            )


if __name__ == "__main__":
    unittest.main()
