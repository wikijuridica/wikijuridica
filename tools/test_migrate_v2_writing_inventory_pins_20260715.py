#!/usr/bin/env python3
"""Testes focais do produtor one-shot de pins do inventário v2."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from tools import generate_v2_review_queue as queue
from tools import migrate_v2_writing_inventory_pins_20260715 as producer
from tools import v2_portfolio_intent_migrations as migrations


def jsonl(records: list[dict]) -> bytes:
    return b"".join(
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        .encode("utf-8")
        for record in records
    )


class WritingInventoryPinMigrationTest(unittest.TestCase):
    def semantic_contract(
        self,
        *,
        unresolved: tuple[str, ...] = (),
        targets: dict[str, str] | None = None,
        dependencies: dict[str, str] | None = None,
        absent: tuple[str, ...] = (),
        digest: str = "a" * 64,
    ) -> queue.WritingSemanticContract:
        targets = targets or {}
        return queue.WritingSemanticContract(
            digest=digest,
            unresolved_intents=frozenset(unresolved),
            requirement_fingerprints={
                intent_id: "b" * 64 for intent_id in targets
            },
            portfolio_rel_paths={
                intent_id: "data/editorial/portfolio_v2/consumidor.jsonl"
                for intent_id in targets
            },
            target_rel_paths=targets,
            superseded_target_rel_paths=targets,
            superseded_page_record_sha256={
                intent_id: None for intent_id in targets
            },
            evidence_kinds={
                intent_id: "archived_shard_snapshot" for intent_id in targets
            },
            evidence_rel_paths={
                intent_id: "data/editorial/portfolio_v2/consumidor.jsonl"
                for intent_id in targets
            },
            evidence_sha256={intent_id: "c" * 64 for intent_id in targets},
            dependency_sha256=dependencies or {},
            absent_dependency_paths=frozenset(absent),
        )

    def portfolio(self, records: list[dict]) -> producer.PortfolioSnapshot:
        payload = jsonl(records)
        snapshot = queue.RegularFileSnapshot(
            payload, hashlib.sha256(payload).hexdigest()
        )
        return producer.load_portfolio(
            "data/editorial/portfolio_v2/consumidor.jsonl", snapshot
        )

    def test_pin_retires_adjusts_aggregates_and_covers_only_trailing_orphans(self):
        portfolio = self.portfolio([
            {"intent_id": "cons-a-um", "family": "familia-a"},
            {"intent_id": "cons-a-dois", "family": "familia-a"},
            {"intent_id": "cons-b-um", "family": "familia-b"},
            {"intent_id": "cons-c-um", "family": "familia-c"},
            {"intent_id": "cons-c-dois", "family": "familia-c"},
            {"intent_id": "cons-d-um", "family": "familia-d"},
            {"intent_id": "cons-d-dois", "family": "familia-d"},
        ])
        batches = [
            {
                "families": ["familia-a", "familia-b"],
                "skip": 0,
                "take": 0,
                "n": 3,
                "area": "consumidor",
                "file": portfolio.rel_path,
                "slug": "consumidor-01",
                "metadata": {"preservar": True},
            },
            {
                "families": ["familia-c"],
                "skip": 0,
                "take": 1,
                "n": 1,
                "area": "consumidor",
                "file": portfolio.rel_path,
                "slug": "consumidor-02",
            },
            {
                "families": ["familia-c"],
                "skip": 0,
                "take": 2,
                "n": 2,
                "area": "consumidor",
                "file": portfolio.rel_path,
                "slug": "consumidor-03",
            },
        ]
        with (
            mock.patch.object(
                producer, "AGGREGATE_SHARDS", ("consumidor-d01",)
            ),
            mock.patch.object(
                producer, "RETIRED_BATCHES", frozenset({"consumidor-02"})
            ),
            mock.patch.object(
                producer, "SLICE_ADJUSTMENTS", {"consumidor-03": (1, 1)}
            ),
            mock.patch.object(
                producer,
                "TAKE_ZERO_EXCLUSIONS",
                {"consumidor-01": frozenset({"cons-a-dois"})},
            ),
        ):
            result, counts = producer.pin_and_expand_inventory(
                batches,
                {portfolio.rel_path: portfolio},
                overflow_pins={},
                aggregate_intents={
                    "consumidor-d01": ("cons-a-dois", "cons-c-um")
                },
            )
        by_slug = {batch["slug"]: batch for batch in result}
        self.assertNotIn("consumidor-02", by_slug)
        self.assertEqual(
            by_slug["consumidor-01"]["intent_ids"],
            ["cons-a-um", "cons-b-um"],
        )
        self.assertEqual(
            by_slug["consumidor-01"]["metadata"], {"preservar": True}
        )
        self.assertEqual(
            (by_slug["consumidor-03"]["skip"],
             by_slug["consumidor-03"]["take"]),
            (1, 1),
        )
        self.assertEqual(
            by_slug["consumidor-d01"]["intent_ids"],
            ["cons-a-dois", "cons-c-um"],
        )
        self.assertEqual(
            (by_slug["consumidor-04"]["skip"],
             by_slug["consumidor-04"]["take"]),
            (0, 2),
        )
        self.assertEqual(counts["portfolio_intents"], 7)
        self.assertEqual(counts["new_batches"], 1)
        self.assertEqual(counts["new_intents"], 2)

    def test_non_trailing_orphan_is_rejected_instead_of_overlapping_owner(self):
        portfolio = self.portfolio([
            {"intent_id": "cons-a-um", "family": "familia-a"},
            {"intent_id": "cons-a-dois", "family": "familia-a"},
            {"intent_id": "cons-a-tres", "family": "familia-a"},
        ])
        batches = [{
            "families": ["familia-a"],
            "skip": 1,
            "take": 2,
            "n": 2,
            "area": "consumidor",
            "file": portfolio.rel_path,
            "slug": "consumidor-01",
        }]
        with (
            mock.patch.object(producer, "AGGREGATE_SHARDS", ()),
            mock.patch.object(producer, "RETIRED_BATCHES", frozenset()),
            mock.patch.object(producer, "SLICE_ADJUSTMENTS", {}),
            mock.patch.object(producer, "TAKE_ZERO_EXCLUSIONS", {}),
            self.assertRaisesRegex(ValueError, "cauda contígua"),
        ):
            producer.pin_and_expand_inventory(
                batches,
                {portfolio.rel_path: portfolio},
                overflow_pins={},
                aggregate_intents={},
            )

    def test_workflow_parser_rejects_duplicate_batch_keys(self):
        payload = (
            b"const batches = "
            b'[{"slug":"consumidor-01","slug":"consumidor-02"}]\n'
        )
        with self.assertRaisesRegex(ValueError, "chave JSON duplicada"):
            producer.parse_workflow_document(payload, "fixture")

    def test_queue_item_carries_exact_pin_and_authenticated_empty_target(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-queue-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        # ``needs_source_research`` é campo obrigatório e booleano do portfólio
        # (``generate_v2_review_queue.py:2111``). Sem ele o caso morria em
        # "identidade/source_hints não canônicos na linha 1" dentro de
        # ``derive_writing_source_resolution``, ANTES de chegar ao
        # ``classify_batch_completion`` cujo ``reuse`` este teste existe para
        # fixar (``migrate_v2_writing_inventory_pins_20260715.py:1485``).
        portfolio_records = [{
            "intent_id": "cons-pin-um",
            "family": "familia-pin",
            "source_hints": [],
            "needs_source_research": False,
        }]
        portfolio_payload = jsonl(portfolio_records)
        portfolio_rel = "data/editorial/portfolio_v2/consumidor.jsonl"
        catalog_rel = producer.SOURCE_CATALOG_REL
        catalog_payload = json.dumps({
            "_meta": {
                "schema_version": 1,
                "purpose": "fixture de resolução exata",
                "source_policy": "fonte oficial específica",
            },
            "strict_intents": [],
            "source_hints": {},
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        area_payload = json.dumps({
            "_meta": {},
            "consumidor": [{
                "name": "Lei oficial",
                "url": "https://www.planalto.gov.br/ccivil_03/leis/fixture.htm",
            }],
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        for rel_path, payload in (
            (portfolio_rel, portfolio_payload),
            (catalog_rel, catalog_payload),
        ):
            path = root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        portfolio = producer.load_portfolio(
            portfolio_rel,
            queue.RegularFileSnapshot(
                portfolio_payload, hashlib.sha256(portfolio_payload).hexdigest()
            ),
        )
        batch = {
            "families": ["familia-pin"],
            "skip": 0,
            "take": 0,
            "n": 1,
            "area": "consumidor",
            "file": portfolio_rel,
            "slug": "consumidor-01",
            "intent_ids": ["cons-pin-um"],
        }
        items = producer.build_queue_items(
            root,
            [batch],
            {portfolio_rel: portfolio},
            queue.RegularFileSnapshot(
                catalog_payload, hashlib.sha256(catalog_payload).hexdigest()
            ),
            queue.RegularFileSnapshot(
                area_payload, hashlib.sha256(area_payload).hexdigest()
            ),
            {},
            set(),
            migrations.MigrationCatalog("", {}, {}),
            self.semantic_contract(),
            [{
                "slug": "consumidor-01",
                "review_note": {"preservar": True},
                "reuse": ["stale-intent"],
                "preserve_extras": ["stale-extra"],
                "portfolio_intent_migration": {"stale": True},
                "target_sha256": "f" * 64,
            }],
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["intent_ids"], ["cons-pin-um"])
        self.assertEqual(items[0]["target_sha256"], producer.EMPTY_SHA256)
        self.assertEqual(items[0]["semantic_contract_sha256"], "a" * 64)
        self.assertEqual(items[0]["preserved_record_sha256"], {})
        self.assertEqual(items[0]["review_note"], {"preservar": True})
        self.assertNotIn("reuse", items[0])
        self.assertNotIn("preserve_extras", items[0])
        self.assertNotIn("portfolio_intent_migration", items[0])

        target_rel = "data/editorial/v2_pages/consumidor-01.jsonl"
        target_payload = jsonl([{
            "intent_id": "cons-pin-um",
            "sections": [{"text": "Página do recorte anterior."}],
        }])
        blocked_items = producer.build_queue_items(
            root,
            [batch],
            {portfolio_rel: portfolio},
            queue.RegularFileSnapshot(
                catalog_payload, hashlib.sha256(catalog_payload).hexdigest()
            ),
            queue.RegularFileSnapshot(
                area_payload, hashlib.sha256(area_payload).hexdigest()
            ),
            {target_rel: queue.RegularFileSnapshot(
                target_payload, hashlib.sha256(target_payload).hexdigest()
            )},
            set(),
            migrations.MigrationCatalog("", {}, {}),
            self.semantic_contract(
                unresolved=("cons-pin-um",),
                targets={"cons-pin-um": target_rel},
                digest="c" * 64,
            ),
            [],
        )
        self.assertEqual(len(blocked_items), 1)
        self.assertNotIn("reuse", blocked_items[0])
        self.assertEqual(
            blocked_items[0]["semantic_contract_sha256"], "c" * 64
        )

        expected_raw = json.dumps({
            "intent_id": "cons-pin-um",
            "sections": [{"text": "Página atual preservável."}],
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        relocated_raw = json.dumps({
            "intent_id": "cons-recorte-antigo",
            "sections": [{"text": "Página do owner anterior."}],
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        relocated_payload = expected_raw + b"\n" + relocated_raw + b"\n"
        relocated_contract = queue.WritingSemanticContract(
            digest="d" * 64,
            unresolved_intents=frozenset({"cons-recorte-antigo"}),
            requirement_fingerprints={"cons-recorte-antigo": "e" * 64},
            portfolio_rel_paths={"cons-recorte-antigo": portfolio_rel},
            target_rel_paths={
                "cons-recorte-antigo":
                "data/editorial/v2_pages/consumidor-02.jsonl"},
            superseded_target_rel_paths={
                "cons-recorte-antigo": target_rel},
            superseded_page_record_sha256={
                "cons-recorte-antigo": hashlib.sha256(
                    relocated_raw).hexdigest()},
            evidence_kinds={
                "cons-recorte-antigo": "duplicate_supersession_record"},
            evidence_rel_paths={"cons-recorte-antigo": "evidence"},
            evidence_sha256={"cons-recorte-antigo": "f" * 64},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        relocation_items = producer.build_queue_items(
            root,
            [batch],
            {portfolio_rel: portfolio},
            queue.RegularFileSnapshot(
                catalog_payload, hashlib.sha256(catalog_payload).hexdigest()),
            queue.RegularFileSnapshot(
                area_payload, hashlib.sha256(area_payload).hexdigest()),
            {target_rel: queue.RegularFileSnapshot(
                relocated_payload, hashlib.sha256(relocated_payload).hexdigest())},
            set(),
            migrations.MigrationCatalog("", {}, {}),
            relocated_contract,
            [],
        )
        self.assertEqual(len(relocation_items), 1)
        self.assertEqual(
            relocation_items[0]["semantic_relocation_removals"],
            [{
                "intent_id": "cons-recorte-antigo",
                "record_sha256": hashlib.sha256(relocated_raw).hexdigest(),
                "owner_target_rel_path":
                    "data/editorial/v2_pages/consumidor-02.jsonl",
                "requirement_sha256": "e" * 64,
            }],
        )
        self.assertEqual(relocation_items[0]["reuse"], ["cons-pin-um"])
        self.assertEqual(
            relocation_items[0]["preserved_record_sha256"],
            {"cons-pin-um": hashlib.sha256(expected_raw).hexdigest()},
        )

        with self.assertRaisesRegex(ValueError, "campos públicos"):
            producer.build_queue_items(
                root,
                [batch],
                {portfolio_rel: portfolio},
                queue.RegularFileSnapshot(
                    catalog_payload,
                    hashlib.sha256(catalog_payload).hexdigest(),
                ),
                queue.RegularFileSnapshot(
                    area_payload,
                    hashlib.sha256(area_payload).hexdigest(),
                ),
                {},
                set(),
                migrations.MigrationCatalog("", {}, {}),
                self.semantic_contract(),
                [{
                    "slug": "consumidor-01",
                    "publication_allowed": True,
                }],
            )

    def test_without_telecom_must_be_exact_projection_of_canonical_todo(self):
        todo = [
            {"slug": "consumidor-01", "area": "consumidor",
             "metadata": {"preservar": True}},
            {"slug": "telecom_energia-01", "area": "telecom_energia"},
        ]
        producer._validate_existing_without_telecom_projection(
            todo, [todo[0]]
        )
        with self.assertRaisesRegex(ValueError, "perder metadata"):
            producer._validate_existing_without_telecom_projection(
                todo,
                [{"slug": "consumidor-01", "area": "consumidor"}],
            )

    def test_portfolio_membership_rejects_unowned_file_and_post_plan_drift(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-portfolios-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        directory = root / "data/editorial/portfolio_v2"
        directory.mkdir(parents=True)
        consumer_payload = jsonl([{
            "intent_id": "cons-a-um", "family": "familia-a",
        }])
        (directory / "consumidor.jsonl").write_bytes(consumer_payload)
        (directory / "nova-area.jsonl").write_bytes(jsonl([{
            "intent_id": "nova-a-um", "family": "familia-nova",
        }]))
        batches = [{
            "families": ["familia-a"], "skip": 0, "take": 1, "n": 1,
            "area": "consumidor",
            "file": "data/editorial/portfolio_v2/consumidor.jsonl",
            "slug": "consumidor-01",
        }]
        with self.assertRaisesRegex(
                queue.CASMismatch, "sem_owner=.*nova-area"):
            producer._snapshot_portfolios(root, batches)

        empty_preimages = producer.PreimageBundle(
            manifest=queue.RegularFileSnapshot(
                b"", hashlib.sha256(b"").hexdigest()
            ),
            archives={},
        )
        plan = producer.MigrationPlan(
            inputs={},
            dependency_sha256={},
            stock_sha256={},
            portfolio_paths=(
                "data/editorial/portfolio_v2/consumidor.jsonl",
            ),
            semantic_contract=self.semantic_contract(),
            outputs={},
            preimage_bundle=empty_preimages,
            receipt_payload=b"",
            counts={},
        )
        with self.assertRaisesRegex(
                queue.CASMismatch, "conjunto de portfólios mudou"):
            producer._revalidate_plan(root, plan)

        stable_paths = producer._portfolio_paths(root)
        sandwich_plan = producer.MigrationPlan(
            inputs={},
            dependency_sha256={},
            stock_sha256={},
            portfolio_paths=stable_paths,
            semantic_contract=self.semantic_contract(),
            outputs={},
            preimage_bundle=empty_preimages,
            receipt_payload=b"",
            counts={},
        )
        with (
            mock.patch.object(
                producer, "_portfolio_paths",
                side_effect=[stable_paths, (*stable_paths, "late.jsonl")],
            ),
            mock.patch.object(producer, "_stock_paths", return_value=[]),
            self.assertRaisesRegex(
                queue.CASMismatch, "durante a revalidação CAS"
            ),
        ):
            producer._revalidate_plan(root, sandwich_plan)

    def test_semantic_contract_epoch_requires_exact_inventory_owner(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-semantic-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        portfolio = self.portfolio([{
            "intent_id": "cons-recorte-atual",
            "family": "familia-a",
        }])
        batch = {
            "families": ["familia-a"],
            "skip": 0,
            "take": 1,
            "n": 1,
            "area": "consumidor",
            "file": portfolio.rel_path,
            "slug": "consumidor-01",
        }
        target_rel = "data/editorial/v2_pages/consumidor-01.jsonl"
        target = queue.RegularFileSnapshot(b"", producer.EMPTY_SHA256)
        correct = self.semantic_contract(
            unresolved=("cons-recorte-atual",),
            targets={"cons-recorte-atual": target_rel},
            dependencies={
                portfolio.rel_path: portfolio.digest,
                target_rel: target.digest,
            },
        )
        with mock.patch.object(
            queue, "verify_writing_semantic_contract_dependencies"
        ) as verify:
            producer._validate_semantic_contract_epoch(
                root,
                [batch],
                {portfolio.rel_path: portfolio},
                {target_rel: target},
                correct,
            )
        verify.assert_called_once_with(root, correct)

        absent_owner = self.semantic_contract(
            unresolved=("cons-recorte-atual",),
            targets={"cons-recorte-atual": target_rel},
            dependencies={portfolio.rel_path: portfolio.digest},
            absent=(target_rel,),
        )
        with mock.patch.object(
            queue, "verify_writing_semantic_contract_dependencies"
        ) as verify_absent:
            producer._validate_semantic_contract_epoch(
                root,
                [batch],
                {portfolio.rel_path: portfolio},
                {},
                absent_owner,
            )
        verify_absent.assert_called_once_with(root, absent_owner)

        wrong_target = self.semantic_contract(
            unresolved=("cons-recorte-atual",),
            targets={
                "cons-recorte-atual":
                "data/editorial/v2_pages/consumidor-02.jsonl"
            },
        )
        with self.assertRaisesRegex(ValueError, "target_divergente"):
            producer._validate_semantic_contract_epoch(
                root,
                [batch],
                {portfolio.rel_path: portfolio},
                {target_rel: target},
                wrong_target,
            )

    def test_retired_slug_remains_reserved_for_new_tail(self):
        portfolio = self.portfolio([
            {"intent_id": "cons-a-um", "family": "familia-a"},
            {"intent_id": "cons-a-dois", "family": "familia-a"},
            {"intent_id": "cons-a-tres", "family": "familia-a"},
        ])
        batches = [
            {
                "families": ["familia-a"], "skip": 0, "take": 1, "n": 1,
                "area": "consumidor", "file": portfolio.rel_path,
                "slug": "consumidor-01",
            },
            {
                "families": ["familia-a"], "skip": 1, "take": 1, "n": 1,
                "area": "consumidor", "file": portfolio.rel_path,
                "slug": "consumidor-02",
            },
        ]
        with (
            mock.patch.object(
                producer, "AGGREGATE_SHARDS", ("consumidor-d01",)
            ),
            mock.patch.object(
                producer, "RETIRED_BATCHES", frozenset({"consumidor-02"})
            ),
            mock.patch.object(producer, "SLICE_ADJUSTMENTS", {}),
            mock.patch.object(producer, "TAKE_ZERO_EXCLUSIONS", {}),
        ):
            result, _ = producer.pin_and_expand_inventory(
                batches,
                {portfolio.rel_path: portfolio},
                overflow_pins={},
                aggregate_intents={"consumidor-d01": ("cons-a-dois",)},
            )
        self.assertIn("consumidor-03", {batch["slug"] for batch in result})
        self.assertNotIn(
            "consumidor-02", {batch["slug"] for batch in result}
        )

    def test_multifile_failure_rolls_back_only_owned_output_hash(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-txn-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        first = root / "first.txt"
        second = root / "second.txt"
        first.write_bytes(b"first-before\n")
        second.write_bytes(b"second-before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            if path == second and payload == b"second-after\n":
                raise queue.CASMismatch("falha injetada")
            queue.atomic_replace_cas(path, payload, expected)

        with self.assertRaisesRegex(RuntimeError, "voltaram às preimagens"):
            producer.atomic_replace_many(
                root,
                [
                    ("first.txt", b"first-before\n", b"first-after\n"),
                    ("second.txt", b"second-before\n", b"second-after\n"),
                ],
                replace=replace,
            )
        self.assertEqual(first.read_bytes(), b"first-before\n")
        self.assertEqual(second.read_bytes(), b"second-before\n")

    def test_post_effect_error_on_intermediate_is_authenticated_and_rolled_back(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-effect-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        first = root / "first.txt"
        second = root / "second.txt"
        first.write_bytes(b"first-before\n")
        second.write_bytes(b"second-before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            queue.atomic_replace_cas(path, payload, expected)
            if path == first and payload == b"first-after\n":
                raise OSError("falha pós-efeito injetada")

        with self.assertRaisesRegex(RuntimeError, "voltaram às preimagens"):
            producer.atomic_replace_many(
                root,
                [
                    ("first.txt", b"first-before\n", b"first-after\n"),
                    ("second.txt", b"second-before\n", b"second-after\n"),
                ],
                replace=replace,
            )
        self.assertEqual(first.read_bytes(), b"first-before\n")
        self.assertEqual(second.read_bytes(), b"second-before\n")

    def test_post_effect_error_on_commit_marker_preserves_coherent_outputs(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-marker-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        output = root / "output.txt"
        marker = root / "receipt.json"
        output.write_bytes(b"before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            queue.atomic_replace_cas(path, payload, expected)
            if path == marker and payload == b'{"complete":true}\n':
                raise OSError("fsync pós-rename injetado")

        with self.assertRaisesRegex(RuntimeError, "commit marker apareceu"):
            producer.atomic_replace_many(
                root,
                [
                    ("output.txt", b"before\n", b"after\n"),
                    ("receipt.json", b"", b'{"complete":true}\n'),
                ],
                replace=replace,
                commit_marker_rel="receipt.json",
            )
        self.assertEqual(output.read_bytes(), b"after\n")
        self.assertEqual(marker.read_bytes(), b'{"complete":true}\n')

    def test_marker_appearing_during_before_last_prevents_output_rollback(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-marker-race-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        output = root / "output.txt"
        marker = root / "receipt.json"
        output.write_bytes(b"before\n")

        def marker_then_fail() -> None:
            marker.write_bytes(b'{"complete":true}\n')
            raise queue.CASMismatch("falha depois da criação concorrente")

        with self.assertRaisesRegex(RuntimeError, "commit marker apareceu"):
            producer.atomic_replace_many(
                root,
                [
                    ("output.txt", b"before\n", b"after\n"),
                    ("receipt.json", b"", b'{"complete":true}\n'),
                ],
                before_last=marker_then_fail,
                commit_marker_rel="receipt.json",
            )
        self.assertEqual(output.read_bytes(), b"after\n")
        self.assertEqual(marker.read_bytes(), b'{"complete":true}\n')

    def test_unsafe_existing_marker_is_rejected_before_any_output_write(self):
        for kind in ("symlink", "hardlink", "fifo"):
            with self.subTest(kind=kind):
                root = pathlib.Path(tempfile.mkdtemp(
                    prefix=f"wiki-pin-marker-{kind}-"
                ))
                self.addCleanup(
                    lambda root=root: __import__("shutil").rmtree(root)
                )
                output = root / "output.txt"
                marker = root / "receipt.json"
                output.write_bytes(b"before\n")
                if kind == "symlink":
                    marker.symlink_to("missing-receipt")
                elif kind == "hardlink":
                    source = root / "shared-receipt.json"
                    source.write_bytes(b"{}\n")
                    os.link(source, marker)
                else:
                    os.mkfifo(marker)
                calls: list[pathlib.Path] = []

                def replace(
                    path: pathlib.Path, payload: bytes, expected: str,
                ) -> None:
                    calls.append(path)
                    queue.atomic_replace_cas(path, payload, expected)

                with self.assertRaisesRegex(
                    ValueError, "commit marker precisa estar ausente"
                ):
                    producer.atomic_replace_many(
                        root,
                        [
                            ("output.txt", b"before\n", b"after\n"),
                            ("receipt.json", b"", b"{}\n"),
                        ],
                        replace=replace,
                        commit_marker_rel="receipt.json",
                    )
                self.assertEqual(calls, [])
                self.assertEqual(output.read_bytes(), b"before\n")

    def test_unsafe_marker_appearing_after_preflight_is_fail_stop(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-marker-unsafe-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        output = root / "output.txt"
        marker = root / "receipt.json"
        output.write_bytes(b"before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            if path == marker:
                marker.symlink_to("missing-receipt")
                raise OSError("falha com marker inseguro já nomeado")
            queue.atomic_replace_cas(path, payload, expected)

        with self.assertRaisesRegex(
            RuntimeError, "commit marker apareceu.*não autenticada"
        ):
            producer.atomic_replace_many(
                root,
                [
                    ("output.txt", b"before\n", b"after\n"),
                    ("receipt.json", b"", b"{}\n"),
                ],
                replace=replace,
                commit_marker_rel="receipt.json",
            )
        self.assertEqual(output.read_bytes(), b"after\n")
        self.assertTrue(marker.is_symlink())

    def test_marker_appearing_during_rollback_reapplies_owned_effect(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-marker-rollback-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        first = root / "first.txt"
        second = root / "second.txt"
        marker = root / "receipt.json"
        first.write_bytes(b"first-before\n")
        second.write_bytes(b"second-before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            if path == marker:
                raise queue.CASMismatch("falha antes do marker")
            queue.atomic_replace_cas(path, payload, expected)
            if path == second and payload == b"second-before\n":
                marker.write_bytes(b'{"complete":true}\n')
                raise OSError("marker apareceu depois do efeito de rollback")

        with self.assertRaisesRegex(
            RuntimeError, "commit marker apareceu durante rollback"
        ):
            producer.atomic_replace_many(
                root,
                [
                    ("first.txt", b"first-before\n", b"first-after\n"),
                    ("second.txt", b"second-before\n", b"second-after\n"),
                    ("receipt.json", b"", b'{"complete":true}\n'),
                ],
                replace=replace,
                commit_marker_rel="receipt.json",
            )
        self.assertEqual(first.read_bytes(), b"first-after\n")
        self.assertEqual(second.read_bytes(), b"second-after\n")
        self.assertEqual(marker.read_bytes(), b'{"complete":true}\n')

    def test_post_effect_error_during_rollback_counts_as_restored(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-rollback-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        first = root / "first.txt"
        second = root / "second.txt"
        first.write_bytes(b"first-before\n")
        second.write_bytes(b"second-before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            if path == second and payload == b"second-after\n":
                raise queue.CASMismatch("falha antes do segundo efeito")
            queue.atomic_replace_cas(path, payload, expected)
            if path == first and payload == b"first-before\n":
                raise OSError("falha pós-rollback injetada")

        with self.assertRaisesRegex(RuntimeError, "voltaram às preimagens"):
            producer.atomic_replace_many(
                root,
                [
                    ("first.txt", b"first-before\n", b"first-after\n"),
                    ("second.txt", b"second-before\n", b"second-after\n"),
                ],
                replace=replace,
            )
        self.assertEqual(first.read_bytes(), b"first-before\n")
        self.assertEqual(second.read_bytes(), b"second-before\n")

    def test_concurrent_output_evolution_is_preserved_during_rollback(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-concurrent-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        first = root / "first.txt"
        second = root / "second.txt"
        concurrent = "evolução concorrente\n".encode("utf-8")
        first.write_bytes(b"first-before\n")
        second.write_bytes(b"second-before\n")

        def replace(path: pathlib.Path, payload: bytes, expected: str) -> None:
            if path == second and payload == b"second-after\n":
                first.write_bytes(concurrent)
                raise queue.CASMismatch("falha depois da evolução concorrente")
            queue.atomic_replace_cas(path, payload, expected)

        with self.assertRaisesRegex(RuntimeError, "evolução concorrente"):
            producer.atomic_replace_many(
                root,
                [
                    ("first.txt", b"first-before\n", b"first-after\n"),
                    ("second.txt", b"second-before\n", b"second-after\n"),
                ],
                replace=replace,
            )
        self.assertEqual(first.read_bytes(), concurrent)
        self.assertEqual(second.read_bytes(), b"second-before\n")

    def test_precommit_failure_rolls_back_outputs_before_receipt_creation(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-precommit-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        output = root / "output.txt"
        receipt = root / "receipt.json"
        output.write_bytes(b"before\n")

        def reject_precommit() -> None:
            raise queue.CASMismatch("dependência mudou")

        with self.assertRaisesRegex(RuntimeError, "voltaram às preimagens"):
            producer.atomic_replace_many(
                root,
                [
                    ("output.txt", b"before\n", b"after\n"),
                    ("receipt.json", b"", b"{}\n"),
                ],
                before_last=reject_precommit,
                commit_marker_rel="receipt.json",
            )
        self.assertEqual(output.read_bytes(), b"before\n")
        self.assertFalse(receipt.exists())

    def test_prepare_preimages_is_append_only_exact_and_idempotent(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-preimages-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        expected = {}
        payloads = {}
        for rel_path in producer._OUTPUT_PATHS:
            payload = ("active-preimage:" + rel_path + "\n").encode("utf-8")
            path = root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            payloads[rel_path] = payload
            expected[rel_path] = hashlib.sha256(payload).hexdigest()

        with mock.patch.object(producer, "EXPECTED_INPUT_SHA256", expected):
            first = producer.prepare_preimages(root)
            for active_path, archive_rel in (
                    producer.PREIMAGE_ARCHIVE_BY_OUTPUT.items()):
                archive_path = root / archive_rel
                self.assertEqual(archive_path.read_bytes(), payloads[active_path])
                self.assertEqual(archive_path.stat().st_mode & 0o777, 0o644)
                self.assertEqual(archive_path.stat().st_nlink, 1)
            manifest_before = (
                root / producer.PREIMAGE_MANIFEST_REL
            ).read_bytes()
            second = producer.prepare_preimages(root)
            self.assertEqual(second.manifest.digest, first.manifest.digest)
            self.assertEqual(
                (root / producer.PREIMAGE_MANIFEST_REL).read_bytes(),
                manifest_before,
            )

            manifest_path = root / producer.PREIMAGE_MANIFEST_REL
            manifest_value = json.loads(manifest_before)
            manifest_value["preimage_set_sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(
                    manifest_value,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "preimage_set"):
                producer._verify_preimage_manifest(root)
            manifest_path.write_bytes(manifest_before)

            archive_rel = sorted(producer._PREIMAGE_ARCHIVE_PATHS)[0]
            archive_path = root / archive_rel
            archive_payload = archive_path.read_bytes()
            original_reader = producer._read_immutable_preimage
            archive_mutated = False

            def mutate_archive_after_first_read(
                read_root, rel_path, *, missing_ok
            ):
                nonlocal archive_mutated
                snapshot = original_reader(
                    read_root, rel_path, missing_ok=missing_ok
                )
                if rel_path == archive_rel and not archive_mutated:
                    archive_mutated = True
                    archive_path.write_bytes(archive_payload + b"raced\n")
                return snapshot

            with (
                mock.patch.object(
                    producer,
                    "_read_immutable_preimage",
                    side_effect=mutate_archive_after_first_read,
                ),
                self.assertRaises(queue.CASMismatch),
            ):
                producer._verify_preimage_manifest(root)
            self.assertTrue(archive_mutated)
            archive_path.write_bytes(archive_payload)

            active_rel = next(
                active for active, archive in
                producer.PREIMAGE_ARCHIVE_BY_OUTPUT.items()
                if archive == archive_rel
            )
            active_path = root / active_rel
            active_payload = active_path.read_bytes()
            active_path.write_bytes(active_payload + b"postimage\n")
            with self.assertRaisesRegex(
                    queue.CASMismatch, "não coincide byte a byte"):
                producer._read_required_inputs(root, first)
            active_path.write_bytes(active_payload)
            active_path.chmod(0o600)
            with self.assertRaisesRegex(RuntimeError, "mode=0644"):
                producer._read_required_inputs(root, first)
            active_path.chmod(0o644)

            archive_path.write_bytes(archive_path.read_bytes() + b"evolved\n")
            with self.assertRaises(queue.CASMismatch):
                producer.prepare_preimages(root)

    def test_completed_receipt_has_closed_paths_counts_and_public_flags(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-pin-receipt-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        expected_inputs = {}
        for rel_path in producer.EXPECTED_INPUT_SHA256:
            payload = ("preimage:" + rel_path + "\n").encode("utf-8")
            expected_inputs[rel_path] = hashlib.sha256(payload).hexdigest()
            if rel_path not in producer._OUTPUT_PATHS:
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
        output_sha256 = {}
        for rel_path in producer._OUTPUT_PATHS:
            payload = (rel_path + "\n").encode("utf-8")
            path = root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            output_sha256[rel_path] = hashlib.sha256(payload).hexdigest()
        preimage_archives = {}
        preimage_entries = {}
        for active_path, archive_rel in (
                producer.PREIMAGE_ARCHIVE_BY_OUTPUT.items()):
            payload = ("preimage:" + active_path + "\n").encode("utf-8")
            archive_path = root / archive_rel
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            archive_path.write_bytes(payload)
            archive_path.chmod(0o644)
            digest = hashlib.sha256(payload).hexdigest()
            preimage_archives[archive_rel] = digest
            preimage_entries[active_path] = {
                "archive_path": archive_rel,
                "sha256": digest,
                "bytes": len(payload),
                "mode": "0644",
                "nlink": 1,
            }
        preimage_manifest = {
            "schema_version": "v2_writing_inventory_preimages_v1",
            "migration_id": "writing-inventory-pins-20260715",
            "checked_at": "2026-07-15",
            "preimages": preimage_entries,
            "preimage_set_sha256": producer._preimage_set_digest(
                preimage_entries
            ),
            "publication_touches": [],
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
            "approval": False,
            "publicly_indexable": False,
        }
        preimage_manifest_payload = (
            json.dumps(
                preimage_manifest,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ) + "\n"
        ).encode("utf-8")
        preimage_manifest_path = root / producer.PREIMAGE_MANIFEST_REL
        preimage_manifest_path.write_bytes(preimage_manifest_payload)
        preimage_manifest_path.chmod(0o644)
        preimage_manifest_sha256 = hashlib.sha256(
            preimage_manifest_payload
        ).hexdigest()
        portfolio_rel = "data/editorial/portfolio_v2/consumidor.jsonl"
        portfolio_payload = b'{"intent_id":"cons-receipt-fixture"}\n'
        portfolio_path = root / portfolio_rel
        portfolio_path.parent.mkdir(parents=True, exist_ok=True)
        portfolio_path.write_bytes(portfolio_payload)
        portfolio_sha256 = {
            portfolio_rel: hashlib.sha256(portfolio_payload).hexdigest(),
        }
        catalog_rel = producer.portfolio_migrations.REGISTRY_REL_PATH
        catalog_payload = b"catalog fixture\n"
        catalog_path = root / catalog_rel
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_bytes(catalog_payload)
        catalog_sha256 = hashlib.sha256(catalog_payload).hexdigest()
        catalog = producer.portfolio_migrations.MigrationCatalog(
            registry_sha256=catalog_sha256,
            migrations={},
            dependency_sha256={catalog_rel: catalog_sha256},
        )
        trusted_rel = (
            "data/editorial/v2_superseded/receipt-fixture.jsonl"
        )
        trusted_payload = b"trusted supersession fixture\n"
        trusted_path = root / trusted_rel
        trusted_path.parent.mkdir(parents=True, exist_ok=True)
        trusted_path.write_bytes(trusted_payload)
        trusted_sha256 = hashlib.sha256(trusted_payload).hexdigest()
        trusted_dependencies = {trusted_rel: trusted_sha256}
        aggregate_sha256 = {}
        for slug in producer.AGGREGATE_SHARDS:
            rel_path = f"data/editorial/v2_pages/{slug}.jsonl"
            payload = (slug + "\n").encode("ascii")
            path = root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            aggregate_sha256[rel_path] = hashlib.sha256(payload).hexdigest()
        extra_stock_rel = "data/editorial/v2_pages/consumidor-01.jsonl"
        extra_stock_payload = b"stock-extra\n"
        extra_stock_path = root / extra_stock_rel
        extra_stock_path.write_bytes(extra_stock_payload)
        semantic_target_rel = (
            "data/editorial/v2_pages/semantic-receipt-fixture.jsonl"
        )
        semantic_target_payload = b"semantic target fixture\n"
        semantic_target_path = root / semantic_target_rel
        semantic_target_path.write_bytes(semantic_target_payload)
        semantic_target_sha256 = hashlib.sha256(
            semantic_target_payload
        ).hexdigest()
        semantic_absent_rel = (
            "data/editorial/v2_pages/semantic-absent-fixture.jsonl"
        )
        semantic_contract_payload = b"semantic contract fixture\n"
        semantic_contract_path = root / producer.SEMANTIC_CONTRACT_REL
        semantic_contract_path.write_bytes(semantic_contract_payload)
        semantic_contract_sha256 = hashlib.sha256(
            semantic_contract_payload
        ).hexdigest()
        semantic_contract = queue.WritingSemanticContract(
            digest=semantic_contract_sha256,
            unresolved_intents=frozenset({"semantic-receipt-fixture"}),
            requirement_fingerprints={
                "semantic-receipt-fixture": "d" * 64
            },
            portfolio_rel_paths={
                "semantic-receipt-fixture": portfolio_rel
            },
            target_rel_paths={
                "semantic-receipt-fixture": semantic_target_rel
            },
            superseded_target_rel_paths={
                "semantic-receipt-fixture": semantic_target_rel
            },
            superseded_page_record_sha256={
                "semantic-receipt-fixture": None
            },
            evidence_kinds={
                "semantic-receipt-fixture": "archived_shard_snapshot"
            },
            evidence_rel_paths={
                "semantic-receipt-fixture": semantic_target_rel
            },
            evidence_sha256={
                "semantic-receipt-fixture": semantic_target_sha256
            },
            dependency_sha256={
                portfolio_rel: portfolio_sha256[portfolio_rel],
                semantic_target_rel: semantic_target_sha256,
            },
            absent_dependency_paths=frozenset({semantic_absent_rel}),
        )
        stock_sha256 = {
            **aggregate_sha256,
            extra_stock_rel: hashlib.sha256(extra_stock_payload).hexdigest(),
            semantic_target_rel: semantic_target_sha256,
        }
        portfolio_set = producer._snapshot_set_digest(portfolio_sha256)
        aggregate_set = producer._snapshot_set_digest(aggregate_sha256)
        counts = {
            "batches_before": producer.EXPECTED_BATCHES_BEFORE,
            "batches_after": producer.EXPECTED_BATCHES_AFTER,
            "portfolio_intents": producer.EXPECTED_PORTFOLIO_INTENTS,
            "take_zero_batches": producer.EXPECTED_TAKE_ZERO_BATCHES,
            "aggregate_batches": producer.EXPECTED_AGGREGATE_BATCHES,
            "retired_batches": producer.EXPECTED_RETIRED_BATCHES,
            "adjusted_batches": producer.EXPECTED_ADJUSTED_BATCHES,
            "new_batches": producer.EXPECTED_NEW_BATCHES,
            "new_intents": producer.EXPECTED_NEW_INTENTS,
            "complete_batches": producer.EXPECTED_COMPLETE_BATCHES,
            "todo_batches": producer.EXPECTED_TODO_BATCHES,
            "todo_without_telecom_batches":
                producer.EXPECTED_TODO_WITHOUT_TELECOM_BATCHES,
            "semantic_requirements":
                producer.EXPECTED_SEMANTIC_REQUIREMENTS,
            "unresolved_semantic_requirements":
                producer.EXPECTED_UNRESOLVED_SEMANTIC_REQUIREMENTS,
        }
        pin_digest = producer._digest(json.dumps(
            {
                slug: list(producer.OVERFLOW_PINS[slug])
                for slug in sorted(producer.OVERFLOW_PINS)
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        receipt = {
            "schema_version": "v2_writing_inventory_pin_migration_v3",
            "migration_id": "writing-inventory-pins-20260715",
            "checked_at": "2026-07-15",
            "input_sha256": {
                **expected_inputs,
                **portfolio_sha256,
                **aggregate_sha256,
                catalog_rel: catalog_sha256,
                **trusted_dependencies,
                producer.SEMANTIC_CONTRACT_REL: semantic_contract_sha256,
                **semantic_contract.dependency_sha256,
                producer.PREIMAGE_MANIFEST_REL: preimage_manifest_sha256,
                **preimage_archives,
                "portfolio_set": portfolio_set,
                "aggregate_set": aggregate_set,
            },
            "absent_input_paths": [semantic_absent_rel],
            "stock_sha256": stock_sha256,
            "stock_set_sha256": producer._snapshot_set_digest(stock_sha256),
            "output_sha256": output_sha256,
            "preimage_manifest_sha256": preimage_manifest_sha256,
            "preimage_archive_sha256": preimage_archives,
            "preimage_set_sha256": producer._preimage_set_digest(
                preimage_entries
            ),
            "counts": counts,
            "overflow_pin_sha256": pin_digest,
            "publication_touches": [],
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
            "approval": False,
            "publicly_indexable": False,
        }
        receipt_path = root / producer.RECEIPT_REL
        receipt_path.parent.mkdir(parents=True, exist_ok=True)

        def write_receipt() -> None:
            receipt_path.write_text(
                json.dumps(
                    receipt,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )

        write_receipt()
        with (
            mock.patch.object(
                producer, "EXPECTED_INPUT_SHA256", expected_inputs
            ),
            mock.patch.object(
                producer, "EXPECTED_PORTFOLIO_SET_SHA256", portfolio_set
            ),
            mock.patch.object(
                producer, "EXPECTED_AGGREGATE_SET_SHA256", aggregate_set
            ),
            mock.patch.object(
                producer.portfolio_migrations,
                "load_catalog",
                return_value=catalog,
            ),
            mock.patch.object(
                producer,
                "_trusted_supersession_dependency_sha256",
                return_value=trusted_dependencies,
            ),
            mock.patch.object(
                producer.queue,
                "load_writing_semantic_contract",
                return_value=semantic_contract,
            ),
        ):
            self.assertEqual(
                producer._verify_completed_receipt(root)["counts"], counts
            )

            absent_paths = receipt.pop("absent_input_paths")
            write_receipt()
            with self.assertRaisesRegex(ValueError, "recibo existente"):
                producer._verify_completed_receipt(root)
            receipt["absent_input_paths"] = absent_paths
            write_receipt()

            receipt["absent_input_paths"] = [
                "data/editorial/v2_pages/semantic-outra-ausencia.jsonl"
            ]
            write_receipt()
            with self.assertRaisesRegex(ValueError, "ausências semânticas"):
                producer._verify_completed_receipt(root)
            receipt["absent_input_paths"] = absent_paths
            write_receipt()

            receipt_payload = receipt_path.read_bytes()
            receipt_path.chmod(0o600)
            with self.assertRaisesRegex(RuntimeError, "mode=0644"):
                producer._verify_completed_receipt(root)
            receipt_path.chmod(0o644)

            receipt_path.write_bytes(receipt_payload[:-1] + b" \n")
            with self.assertRaisesRegex(ValueError, "não é canônico"):
                producer._verify_completed_receipt(root)
            receipt_path.write_bytes(receipt_payload)

            template_path = root / producer.TEMPLATE_REL
            template_payload = template_path.read_bytes()
            template_path.write_bytes(template_payload + b"evolved\n")
            with self.assertRaises(queue.CASMismatch):
                producer._verify_completed_receipt(root)
            template_path.write_bytes(template_payload)

            semantic_contract_path.write_bytes(
                semantic_contract_payload + b"evolved\n"
            )
            with self.assertRaises(queue.CASMismatch):
                producer._verify_completed_receipt(root)
            semantic_contract_path.write_bytes(semantic_contract_payload)

            portfolio_path.write_bytes(portfolio_payload + b"evolved\n")
            with self.assertRaises(queue.CASMismatch):
                producer._verify_completed_receipt(root)
            portfolio_path.write_bytes(portfolio_payload)

            extra_stock_path.write_bytes(extra_stock_payload + b"evolved\n")
            with self.assertRaises(queue.CASMismatch):
                producer._verify_completed_receipt(root)
            extra_stock_path.write_bytes(extra_stock_payload)

            original_semantic_stock = receipt["stock_sha256"][
                semantic_target_rel
            ]
            receipt["stock_sha256"][semantic_target_rel] = "e" * 64
            receipt["stock_set_sha256"] = producer._snapshot_set_digest(
                receipt["stock_sha256"]
            )
            write_receipt()
            with self.assertRaisesRegex(
                    ValueError, "dependências semânticas e estoque"):
                producer._verify_completed_receipt(root)
            receipt["stock_sha256"][semantic_target_rel] = (
                original_semantic_stock
            )
            receipt["stock_set_sha256"] = producer._snapshot_set_digest(
                receipt["stock_sha256"]
            )
            write_receipt()

            output_rel = sorted(producer._OUTPUT_PATHS)[0]
            output_path = root / output_rel
            output_payload = output_path.read_bytes()
            output_path.chmod(0o600)
            with self.assertRaisesRegex(RuntimeError, "mode=0644"):
                producer._verify_completed_receipt(root)
            output_path.chmod(0o644)
            original_artifact_reader = (
                producer._read_canonical_0644_artifact
            )
            output_mutated = False

            def mutate_output_after_first_hash(
                read_root, rel_path, *, max_bytes,
            ):
                nonlocal output_mutated
                snapshot = original_artifact_reader(
                    read_root, rel_path, max_bytes=max_bytes
                )
                if rel_path == output_rel and not output_mutated:
                    output_mutated = True
                    output_path.write_bytes(output_payload + b"evolved\n")
                return snapshot

            with (
                mock.patch.object(
                    producer,
                    "_read_canonical_0644_artifact",
                    side_effect=mutate_output_after_first_hash,
                ),
                self.assertRaises(queue.CASMismatch),
            ):
                producer._verify_completed_receipt(root)
            self.assertTrue(output_mutated)
            output_path.write_bytes(output_payload)

            archive_rel = sorted(preimage_archives)[0]
            archive_path = root / archive_rel
            archive_payload = archive_path.read_bytes()
            archive_path.write_bytes(archive_payload + b"evolved\n")
            with self.assertRaises(queue.CASMismatch):
                producer._verify_completed_receipt(root)
            archive_path.write_bytes(archive_payload)
            archive_path.chmod(0o600)
            with self.assertRaisesRegex(RuntimeError, "mode=0644"):
                producer._verify_completed_receipt(root)
            archive_path.chmod(0o644)

            preimage_manifest_path.write_bytes(
                preimage_manifest_payload + b" "
            )
            with self.assertRaises((ValueError, queue.CASMismatch)):
                producer._verify_completed_receipt(root)
            preimage_manifest_path.write_bytes(preimage_manifest_payload)

            removed_preimage = receipt[
                "preimage_archive_sha256"
            ].pop(archive_rel)
            write_receipt()
            with self.assertRaises((ValueError, queue.CASMismatch)):
                producer._verify_completed_receipt(root)
            receipt["preimage_archive_sha256"][archive_rel] = (
                removed_preimage
            )
            write_receipt()

            receipt_preimage_set = receipt["preimage_set_sha256"]
            receipt["preimage_set_sha256"] = "0" * 64
            write_receipt()
            with self.assertRaises(queue.CASMismatch):
                producer._verify_completed_receipt(root)
            receipt["preimage_set_sha256"] = receipt_preimage_set
            write_receipt()

            removed_catalog = receipt["input_sha256"].pop(catalog_rel)
            write_receipt()
            with self.assertRaisesRegex(ValueError, "dependências"):
                producer._verify_completed_receipt(root)
            receipt["input_sha256"][catalog_rel] = removed_catalog

            removed_semantic = receipt["input_sha256"].pop(
                producer.SEMANTIC_CONTRACT_REL
            )
            write_receipt()
            with self.assertRaisesRegex(ValueError, "preimagens"):
                producer._verify_completed_receipt(root)
            receipt["input_sha256"][producer.SEMANTIC_CONTRACT_REL] = (
                removed_semantic
            )

            removed_semantic_target = receipt["input_sha256"].pop(
                semantic_target_rel
            )
            write_receipt()
            with self.assertRaisesRegex(ValueError, "preimagens"):
                producer._verify_completed_receipt(root)
            receipt["input_sha256"][semantic_target_rel] = (
                removed_semantic_target
            )

            removed_portfolio = receipt["input_sha256"].pop(
                portfolio_rel
            )
            write_receipt()
            with self.assertRaisesRegex(ValueError, "preimagens"):
                producer._verify_completed_receipt(root)
            receipt["input_sha256"][portfolio_rel] = removed_portfolio

            aggregate_path = sorted(aggregate_sha256)[0]
            removed_aggregate = receipt["input_sha256"].pop(aggregate_path)
            write_receipt()
            with self.assertRaisesRegex(ValueError, "aggregate_set"):
                producer._verify_completed_receipt(root)
            receipt["input_sha256"][aggregate_path] = removed_aggregate

            receipt["output_sha256"]["../escape"] = "b" * 64
            write_receipt()
            with self.assertRaisesRegex(ValueError, "saídas aberto"):
                producer._verify_completed_receipt(root)


if __name__ == "__main__":
    unittest.main()
