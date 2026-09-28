#!/usr/bin/env python3
"""I/O adversarial do projetor DEC-020 usado antes do CAS de escrita."""

from __future__ import annotations

import os
import pathlib
import shutil
import tempfile
import time
import unittest

from tools import audit_v2_pages as auditor


class SupersessionProjectionSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-dec020-safe-"))
        self.addCleanup(lambda: shutil.rmtree(self.root))
        self.pages = self.root / "data/editorial/v2_pages"
        self.pages.mkdir(parents=True)

    def test_regular_unique_snapshot_is_accepted(self) -> None:
        (self.pages / "civil-01.jsonl").write_text(
            '{"intent_id":"civil-unico","sections":[{"text":"A"}]}\n',
            encoding="utf-8",
        )
        winners, issues = auditor.validated_duplicate_supersession_winners(
            self.root, trusted_archives={})
        self.assertEqual(winners, set())
        self.assertEqual(issues, [])

    def test_fifo_symlink_hardlink_and_duplicate_keys_fail_closed(self) -> None:
        fifo = self.pages / "fifo-01.jsonl"
        os.mkfifo(fifo)
        started = time.monotonic()
        with self.assertRaises(RuntimeError):
            auditor.validated_duplicate_supersession_winners(
                self.root, trusted_archives={})
        self.assertLess(time.monotonic() - started, 1.0)
        fifo.unlink()

        outside = self.root / "outside.jsonl"
        outside.write_text('{"intent_id":"fora"}\n', encoding="utf-8")
        linked = self.pages / "linked-01.jsonl"
        linked.symlink_to(outside)
        with self.assertRaises(OSError):
            auditor.validated_duplicate_supersession_winners(
                self.root, trusted_archives={})
        linked.unlink()

        original = self.pages / "hard-01.jsonl"
        original.write_text('{"intent_id":"hard"}\n', encoding="utf-8")
        os.link(original, self.pages / "hard-02.jsonl")
        with self.assertRaises(RuntimeError):
            auditor.validated_duplicate_supersession_winners(
                self.root, trusted_archives={})
        original.unlink()
        (self.pages / "hard-02.jsonl").unlink()

        duplicate = self.pages / "duplicate-01.jsonl"
        duplicate.write_text(
            '{"intent_id":"primeiro","intent_id":"segundo"}\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "chave JSON duplicada"):
            auditor.validated_duplicate_supersession_winners(
                self.root, trusted_archives={})


if __name__ == "__main__":
    unittest.main()
