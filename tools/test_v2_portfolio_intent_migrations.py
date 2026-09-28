#!/usr/bin/env python3
"""Testes adversariais do autorizador de migração integral de shard."""

from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools import v2_portfolio_intent_migrations as migrations


class PortfolioIntentMigrationTest(unittest.TestCase):
    def fixture(self, *, pinned: bool = False) -> tuple[pathlib.Path, dict, list[str]]:
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-v2-migration-test-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        source_rel = "data/editorial/v2_pages/seguros-01.jsonl"
        portfolio_rel = "data/editorial/portfolio_v2/seguros.jsonl"
        archive_rel = (
            "data/editorial/v2_superseded/"
            "portfolio-intent-migration-seguros-01-2026-07-14.jsonl"
        )
        source_ids = ["seg-antiga-a", "seg-antiga-b"]
        replacements = ["seg-nova-a", "seg-nova-b"]
        source = (
            b'{"intent_id":"seg-antiga-a","title":"A"}\n'
            b'{"intent_id":"seg-antiga-b","skipped":true,"skip_reason":"fonte ausente"}\n'
        )
        portfolio = (
            b'{"intent_id":"seg-nova-a","family":"dpvat-spvat"}\n'
            b'{"intent_id":"seg-nova-b","family":"dpvat-spvat"}\n'
        )
        portfolio_sha = migrations._digest(portfolio)
        archive = migrations.build_archive_payload(
            "seguros-01-dpvat-20260714",
            "seguros-01.jsonl",
            source,
            source_ids,
            replacements,
            portfolio_rel,
            portfolio_sha,
            "2026-07-14",
        )
        record = migrations.build_registry_record(
            "seguros-01-dpvat-20260714",
            "seguros-01.jsonl",
            source,
            source_ids,
            replacements,
            portfolio_rel,
            portfolio_sha,
            archive_rel,
            archive,
            "2026-07-14",
            ["dpvat-spvat"],
            0,
            0 if pinned else 2,
            2,
            replacements if pinned else None,
        )
        for rel, payload in (
            (source_rel, source),
            (portfolio_rel, portfolio),
            (archive_rel, archive),
            (migrations.REGISTRY_REL_PATH, (
                json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
            ).encode("utf-8")),
        ):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        return root, record, replacements

    def test_catalog_and_worker_recheck_authenticate_exact_preimage(self) -> None:
        root, _, replacements = self.fixture()
        catalog = migrations.load_catalog(root)
        source = (root / "data/editorial/v2_pages/seguros-01.jsonl").read_bytes()
        portfolio = (root / "data/editorial/portfolio_v2/seguros.jsonl").read_bytes()
        authorization = migrations.queue_authorization(
            catalog,
            "seguros-01.jsonl",
            source,
            migrations._digest(source),
            "data/editorial/portfolio_v2/seguros.jsonl",
            portfolio,
            migrations._digest(portfolio),
            replacements,
            ["dpvat-spvat"],
            0,
            2,
            2,
        )
        self.assertIsNotNone(authorization)
        migrations.verify_queue_authorization(
            root,
            authorization,
            "data/editorial/v2_pages/seguros-01.jsonl",
            "data/editorial/portfolio_v2/seguros.jsonl",
            replacements,
            ["dpvat-spvat"],
            0,
            2,
            2,
        )
        migrations.verify_queue_identity(
            root,
            authorization["migration_id"],
            "data/editorial/v2_pages/seguros-01.jsonl",
            authorization["source_shard_sha256"],
            "data/editorial/portfolio_v2/seguros.jsonl",
            catalog.migrations["seguros-01.jsonl"]["portfolio_sha256"],
            authorization["registry_sha256"],
            authorization["archive_sha256"],
            ["dpvat-spvat"],
            0,
            2,
            2,
        )

        for families, skip, take, expected_n in (
            (["familia-inexistente"], 0, 2, 2),
            (["dpvat-spvat"], 1, 1, 1),
            (["dpvat-spvat"], 0, 2, 1),
        ):
            with self.assertRaisesRegex(ValueError, "registro de migração"):
                migrations.verify_queue_identity(
                    root,
                    authorization["migration_id"],
                    "data/editorial/v2_pages/seguros-01.jsonl",
                    authorization["source_shard_sha256"],
                    "data/editorial/portfolio_v2/seguros.jsonl",
                    catalog.migrations["seguros-01.jsonl"]["portfolio_sha256"],
                    authorization["registry_sha256"],
                    authorization["archive_sha256"],
                    families,
                    skip,
                    take,
                    expected_n,
                )

        (root / "data/editorial/v2_pages/seguros-01.jsonl").write_bytes(
            b'{"intent_id":"seg-antiga-a","title":"evoluiu"}\n'
            b'{"intent_id":"seg-antiga-b","skipped":true}\n'
        )
        with self.assertRaisesRegex(ValueError, "snapshot vivo"):
            migrations.verify_queue_authorization(
                root,
                authorization,
                "data/editorial/v2_pages/seguros-01.jsonl",
                "data/editorial/portfolio_v2/seguros.jsonl",
                replacements,
                ["dpvat-spvat"],
                0,
                2,
                2,
            )
        dependencies = migrations.verify_post_replacement_queue_authorization(
            root,
            authorization,
            "data/editorial/v2_pages/seguros-01.jsonl",
            "data/editorial/portfolio_v2/seguros.jsonl",
            replacements,
            ["dpvat-spvat"],
            0,
            2,
            2,
        )
        self.assertEqual(
            dependencies[migrations.REGISTRY_REL_PATH],
            authorization["registry_sha256"],
        )
        self.assertEqual(
            dependencies[authorization["archive_path"]],
            authorization["archive_sha256"],
        )
        forged = dict(authorization)
        forged["archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "snapshot pós-CAS"):
            migrations.verify_post_replacement_queue_authorization(
                root,
                forged,
                "data/editorial/v2_pages/seguros-01.jsonl",
                "data/editorial/portfolio_v2/seguros.jsonl",
                replacements,
                ["dpvat-spvat"],
                0,
                2,
                2,
            )

    def test_v2_binds_pinned_intents_and_v1_cannot_authenticate_pin(self) -> None:
        root, record, replacements = self.fixture(pinned=True)
        self.assertEqual(record["schema_version"], migrations.SCHEMA_V2)
        self.assertEqual(record["portfolio_intent_ids"], replacements)
        catalog = migrations.load_catalog(root)
        source = (root / "data/editorial/v2_pages/seguros-01.jsonl").read_bytes()
        portfolio = (
            root / "data/editorial/portfolio_v2/seguros.jsonl"
        ).read_bytes()
        authorization = migrations.queue_authorization(
            catalog,
            "seguros-01.jsonl",
            source,
            migrations._digest(source),
            "data/editorial/portfolio_v2/seguros.jsonl",
            portfolio,
            migrations._digest(portfolio),
            replacements,
            ["dpvat-spvat"],
            0,
            0,
            2,
            replacements,
        )
        self.assertIsNotNone(authorization)
        self.assertEqual(authorization["schema_version"], migrations.SCHEMA_V2)
        self.assertEqual(authorization["portfolio_intent_ids"], replacements)
        self.assertEqual(
            authorization["portfolio_path"],
            "data/editorial/portfolio_v2/seguros.jsonl",
        )
        self.assertEqual(
            authorization["portfolio_sha256"], record["portfolio_sha256"])
        migrations.verify_queue_authorization(
            root,
            authorization,
            "data/editorial/v2_pages/seguros-01.jsonl",
            "data/editorial/portfolio_v2/seguros.jsonl",
            replacements,
            ["dpvat-spvat"],
            0,
            0,
            2,
            replacements,
        )
        migrations.verify_queue_identity(
            root,
            authorization["migration_id"],
            "data/editorial/v2_pages/seguros-01.jsonl",
            authorization["source_shard_sha256"],
            "data/editorial/portfolio_v2/seguros.jsonl",
            record["portfolio_sha256"],
            authorization["registry_sha256"],
            authorization["archive_sha256"],
            ["dpvat-spvat"],
            0,
            0,
            2,
            replacements,
        )
        for pins in (None, [], list(reversed(replacements))):
            with self.subTest(pins=pins):
                with self.assertRaisesRegex(ValueError, "pin|intent_ids"):
                    migrations.queue_authorization(
                        catalog,
                        "seguros-01.jsonl",
                        source,
                        migrations._digest(source),
                        "data/editorial/portfolio_v2/seguros.jsonl",
                        portfolio,
                        migrations._digest(portfolio),
                        replacements,
                        ["dpvat-spvat"],
                        0,
                        0,
                        2,
                        pins,
                    )

        v1_root, _, v1_replacements = self.fixture()
        v1_catalog = migrations.load_catalog(v1_root)
        v1_source = (
            v1_root / "data/editorial/v2_pages/seguros-01.jsonl"
        ).read_bytes()
        v1_portfolio = (
            v1_root / "data/editorial/portfolio_v2/seguros.jsonl"
        ).read_bytes()
        with self.assertRaisesRegex(ValueError, "v1 não autentica pin"):
            migrations.queue_authorization(
                v1_catalog,
                "seguros-01.jsonl",
                v1_source,
                migrations._digest(v1_source),
                "data/editorial/portfolio_v2/seguros.jsonl",
                v1_portfolio,
                migrations._digest(v1_portfolio),
                v1_replacements,
                ["dpvat-spvat"],
                0,
                2,
                2,
                v1_replacements,
            )

    def test_v2_registry_rejects_pin_tampering_and_unpinned_take_zero(self):
        root, record, _ = self.fixture(pinned=True)
        registry_path = root / migrations.REGISTRY_REL_PATH
        tampered = dict(record)
        tampered["portfolio_intent_ids"] = list(
            reversed(tampered["portfolio_intent_ids"]))
        registry_path.write_text(
            json.dumps(
                tampered, ensure_ascii=False, separators=(",", ":"),
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "pinados exatos"):
            migrations.load_catalog(root)

        with self.assertRaisesRegex(ValueError, "take==0 pinado"):
            migrations.build_registry_record(
                "seguros-01-dpvat-20260714",
                "seguros-01.jsonl",
                b'{"intent_id":"antigo"}\n',
                ["antigo"],
                ["novo"],
                "data/editorial/portfolio_v2/seguros.jsonl",
                "0" * 64,
                "data/editorial/v2_superseded/"
                "portfolio-intent-migration-seguros-01-2026-07-14.jsonl",
                b'{"archive":true}\n',
                "2026-07-14",
                ["dpvat-spvat"],
                0,
                0,
                1,
            )

    def test_worker_rechecks_registry_after_catalog_load(self) -> None:
        root, _, replacements = self.fixture()
        catalog = migrations.load_catalog(root)
        record = catalog.migrations["seguros-01.jsonl"]
        registry_path = root / migrations.REGISTRY_REL_PATH
        real_load = migrations.load_catalog

        def load_then_mutate(value):
            loaded = real_load(value)
            registry_path.write_bytes(registry_path.read_bytes() + b"\n")
            return loaded

        with mock.patch.object(
                migrations, "load_catalog", side_effect=load_then_mutate):
            with self.assertRaisesRegex(
                    migrations.queue.CASMismatch,
                    "dependência de migração mudou"):
                migrations.verify_queue_identity(
                    root,
                    record["migration_id"],
                    "data/editorial/v2_pages/seguros-01.jsonl",
                    record["source_shard_sha256"],
                    "data/editorial/portfolio_v2/seguros.jsonl",
                    record["portfolio_sha256"],
                    catalog.registry_sha256,
                    record["archive_sha256"],
                    ["dpvat-spvat"],
                    0,
                    2,
                    len(replacements),
                )

    def test_archive_reconstruction_and_public_flags_fail_closed(self) -> None:
        root, record, _ = self.fixture()
        archive_path = root / record["archive_path"]
        rows = [json.loads(line) for line in archive_path.read_text().splitlines()]
        rows[0]["original_line"] = '{"intent_id":"seg-antiga-a","title":"forjada"}'
        rows[0]["source_record_sha256"] = migrations._digest(
            rows[0]["original_line"].encode("utf-8")
        )
        archive_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) for row in rows) + "\n",
            encoding="utf-8",
        )
        registry_path = root / migrations.REGISTRY_REL_PATH
        registry = json.loads(registry_path.read_text())
        registry["archive_sha256"] = migrations._digest(archive_path.read_bytes())
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "não reconstrói"):
            migrations.load_catalog(root)

        root, record, _ = self.fixture()
        registry_path = root / migrations.REGISTRY_REL_PATH
        registry = json.loads(registry_path.read_text())
        registry["publication_allowed"] = True
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "flag pública"):
            migrations.load_catalog(root)

    def test_registry_and_archive_duplicate_keys_fail_closed(self) -> None:
        root, _, _ = self.fixture()
        registry_path = root / migrations.REGISTRY_REL_PATH
        registry_path.write_bytes(registry_path.read_bytes().replace(
            b'"migration_id":',
            b'"migration_id":"forjada","migration_id":',
            1,
        ))
        with self.assertRaisesRegex(ValueError, "JSON inválido"):
            migrations.load_catalog(root)

        root, record, _ = self.fixture()
        archive_path = root / record["archive_path"]
        archive_path.write_bytes(archive_path.read_bytes().replace(
            b'"original_line":',
            b'"original_line":"forjada","original_line":',
            1,
        ))
        registry_path = root / migrations.REGISTRY_REL_PATH
        registry = json.loads(registry_path.read_text())
        registry["archive_sha256"] = migrations._digest(archive_path.read_bytes())
        registry_path.write_text(
            json.dumps(
                registry, ensure_ascii=False, separators=(",", ":"),
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "JSON inválido"):
            migrations.load_catalog(root)

    def test_symlinked_archive_and_wrong_replacement_order_are_rejected(self) -> None:
        root, record, replacements = self.fixture()
        archive_path = root / record["archive_path"]
        outside = root / "outside.jsonl"
        outside.write_bytes(archive_path.read_bytes())
        archive_path.unlink()
        archive_path.symlink_to(outside)
        with self.assertRaises((OSError, RuntimeError)):
            migrations.load_catalog(root)

        root, _, _ = self.fixture()
        catalog = migrations.load_catalog(root)
        source = (root / "data/editorial/v2_pages/seguros-01.jsonl").read_bytes()
        portfolio = (root / "data/editorial/portfolio_v2/seguros.jsonl").read_bytes()
        with self.assertRaisesRegex(ValueError, "snapshot vivo"):
            migrations.queue_authorization(
                catalog,
                "seguros-01.jsonl",
                source,
                migrations._digest(source),
                "data/editorial/portfolio_v2/seguros.jsonl",
                portfolio,
                migrations._digest(portfolio),
                list(reversed(replacements)),
                ["dpvat-spvat"],
                0,
                2,
                2,
            )

    def test_worker_rejects_portfolio_path_escape_and_symlink_before_use(self):
        root, _, replacements = self.fixture()
        catalog = migrations.load_catalog(root)
        authorization = migrations.queue_authorization(
            catalog,
            "seguros-01.jsonl",
            (root / "data/editorial/v2_pages/seguros-01.jsonl").read_bytes(),
            catalog.migrations["seguros-01.jsonl"]["source_shard_sha256"],
            "data/editorial/portfolio_v2/seguros.jsonl",
            (root / "data/editorial/portfolio_v2/seguros.jsonl").read_bytes(),
            catalog.migrations["seguros-01.jsonl"]["portfolio_sha256"],
            replacements,
            ["dpvat-spvat"],
            0,
            2,
            2,
        )
        self.assertIsNotNone(authorization)
        with self.assertRaisesRegex(ValueError, "alvo de migração"):
            migrations.verify_queue_authorization(
                root,
                authorization,
                "data/editorial/v2_pages/seguros-01.jsonl",
                "data/editorial/portfolio_v2/../segredos.jsonl",
                replacements,
                ["dpvat-spvat"],
                0,
                2,
                2,
            )
        with self.assertRaisesRegex(ValueError, "identidade compacta"):
            migrations.verify_queue_identity(
                root,
                authorization["migration_id"],
                "data/editorial/v2_pages/seguros-01.jsonl",
                authorization["source_shard_sha256"],
                "../../fora.jsonl",
                catalog.migrations["seguros-01.jsonl"]["portfolio_sha256"],
                authorization["registry_sha256"],
                authorization["archive_sha256"],
                ["dpvat-spvat"],
                0,
                2,
                2,
            )

        portfolio_path = root / "data/editorial/portfolio_v2/seguros.jsonl"
        outside = root / "portfolio-real.jsonl"
        outside.write_bytes(portfolio_path.read_bytes())
        portfolio_path.unlink()
        portfolio_path.symlink_to(outside)
        with self.assertRaises((OSError, RuntimeError)):
            migrations.verify_queue_authorization(
                root,
                authorization,
                "data/editorial/v2_pages/seguros-01.jsonl",
                "data/editorial/portfolio_v2/seguros.jsonl",
                replacements,
                ["dpvat-spvat"],
                0,
                2,
                2,
            )

    def test_batch_classifier_requires_exact_authenticated_preimage(self) -> None:
        records = [
            {"intent_id": "seg-antiga-a", "sections": [{"text": "A"}]},
            {"intent_id": "seg-antiga-b", "skipped": True, "skip_reason": "antiga"},
        ]
        completion = migrations.queue.classify_batch_completion(
            records,
            ["seg-nova-a", "seg-nova-b"],
            "seguros-01.jsonl",
            (),
            ["seg-antiga-a", "seg-antiga-b"],
            semantically_blocked_intents=(),
        )
        self.assertFalse(completion.complete)
        self.assertEqual(completion.reusable_expected, ())
        self.assertEqual(completion.authenticated_extras, ())
        with self.assertRaisesRegex(ValueError, "preimagem"):
            migrations.queue.classify_batch_completion(
                list(reversed(records)),
                ["seg-nova-a", "seg-nova-b"],
                "seguros-01.jsonl",
                (),
                ["seg-antiga-a", "seg-antiga-b"],
                semantically_blocked_intents=(),
            )
        with self.assertRaisesRegex(ValueError, "extra ativo"):
            migrations.queue.classify_batch_completion(
                records,
                ["seg-nova-a", "seg-nova-b"],
                "seguros-01.jsonl",
                (),
                semantically_blocked_intents=(),
            )


if __name__ == "__main__":
    unittest.main()
