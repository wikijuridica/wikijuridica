#!/usr/bin/env python3
"""Testes do produtor one-shot de migração do seguros-01."""

from __future__ import annotations

import os
import pathlib
import shutil
import stat
import tempfile
import unittest

from tools import migrate_v2_portfolio_intents_seguros01_20260714 as producer
from tools import v2_portfolio_intent_migrations as migrations


class Seguros01MigrationProducerTest(unittest.TestCase):
    def test_exclusive_lock_rejects_hardlink_without_chmod(self):
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-seguros-lock-"))
        self.addCleanup(lambda: shutil.rmtree(root))
        lock = root / "migration.lock"
        alias = root / "migration-alias.lock"
        lock.write_bytes(b"")
        lock.chmod(0o640)
        os.link(lock, alias)
        original = producer.LOCK_PATH
        producer.LOCK_PATH = lock
        try:
            with self.assertRaisesRegex(RuntimeError, "arquivo regular único"):
                with producer.exclusive_lock():
                    self.fail("hardlinked lock acquired")
        finally:
            producer.LOCK_PATH = original
        self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o640)

    def setUp(self) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-seguros-migration-"))
        self.addCleanup(lambda: shutil.rmtree(self.root))
        self.source_ids = ["seg-antiga-a", "seg-antiga-b"]
        self.replacements = ["seg-nova-a", "seg-nova-b"]
        self.source = (
            b'{"intent_id":"seg-antiga-a","title":"A"}\n'
            b'{"intent_id":"seg-antiga-b","skipped":true,"skip_reason":"antiga"}\n'
        )
        self.portfolio = (
            b'{"intent_id":"seg-nova-a","family":"dpvat-spvat"}\n'
            b'{"intent_id":"seg-nova-b","family":"dpvat-spvat"}\n'
        )
        for rel, payload in (
            (producer.SOURCE_REL, self.source),
            (producer.PORTFOLIO_REL, self.portfolio),
            ("public/marker.txt", b"public-byte-identical\n"),
        ):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        (self.root / producer.ARCHIVE_REL).parent.mkdir(
            parents=True, exist_ok=True)
        self.originals = {
            "ROOT": producer.ROOT,
            "SOURCE_INTENT_IDS": producer.SOURCE_INTENT_IDS,
            "REPLACEMENT_INTENT_IDS": producer.REPLACEMENT_INTENT_IDS,
            "EXPECTED_SOURCE_SHA256": producer.EXPECTED_SOURCE_SHA256,
            "EXPECTED_PORTFOLIO_SHA256": producer.EXPECTED_PORTFOLIO_SHA256,
            "EXPECTED_ARCHIVE_SHA256": producer.EXPECTED_ARCHIVE_SHA256,
            "PORTFOLIO_FAMILIES": producer.PORTFOLIO_FAMILIES,
            "PORTFOLIO_SKIP": producer.PORTFOLIO_SKIP,
            "PORTFOLIO_TAKE": producer.PORTFOLIO_TAKE,
            "PORTFOLIO_N": producer.PORTFOLIO_N,
        }
        producer.ROOT = self.root
        producer.SOURCE_INTENT_IDS = self.source_ids
        producer.REPLACEMENT_INTENT_IDS = self.replacements
        producer.EXPECTED_SOURCE_SHA256 = migrations._digest(self.source)
        producer.EXPECTED_PORTFOLIO_SHA256 = migrations._digest(self.portfolio)
        producer.PORTFOLIO_FAMILIES = ["dpvat-spvat"]
        producer.PORTFOLIO_SKIP = 0
        producer.PORTFOLIO_TAKE = 2
        producer.PORTFOLIO_N = 2
        producer.EXPECTED_ARCHIVE_SHA256 = migrations._digest(
            migrations.build_archive_payload(
                producer.MIGRATION_ID,
                "seguros-01.jsonl",
                self.source,
                self.source_ids,
                self.replacements,
                producer.PORTFOLIO_REL,
                producer.EXPECTED_PORTFOLIO_SHA256,
                producer.CHECKED_AT,
            )
        )
        self.addCleanup(self.restore_globals)

    def restore_globals(self) -> None:
        for name, value in self.originals.items():
            setattr(producer, name, value)

    def test_idempotent_recovery_preserves_source_and_public(self) -> None:
        first = producer.run()
        source_after = (self.root / producer.SOURCE_REL).read_bytes()
        public_after = (self.root / "public/marker.txt").read_bytes()
        archive_after = (self.root / producer.ARCHIVE_REL).read_bytes()
        second = producer.run()
        self.assertEqual(first, second)
        self.assertEqual(source_after, self.source)
        self.assertEqual(public_after, b"public-byte-identical\n")
        self.assertEqual((self.root / producer.ARCHIVE_REL).read_bytes(), archive_after)

        # Falha simulada entre as duas pernas: archive já persistiu, registro
        # ainda não. O rerun fecha sem rotacionar a evidência.
        (self.root / migrations.REGISTRY_REL_PATH).unlink()
        recovered = producer.run()
        self.assertEqual(recovered, first)
        self.assertEqual((self.root / producer.ARCHIVE_REL).read_bytes(), archive_after)
        self.assertEqual((self.root / producer.SOURCE_REL).read_bytes(), self.source)

    def test_source_drift_fails_before_registry(self) -> None:
        (self.root / producer.SOURCE_REL).write_bytes(
            b'{"intent_id":"seg-antiga-a","title":"mudou"}\n'
            b'{"intent_id":"seg-antiga-b","skipped":true}\n'
        )
        with self.assertRaisesRegex(RuntimeError, "preimagem mudou"):
            producer.run()
        self.assertFalse((self.root / migrations.REGISTRY_REL_PATH).exists())
        self.assertFalse((self.root / producer.ARCHIVE_REL).exists())


if __name__ == "__main__":
    unittest.main()
