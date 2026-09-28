from __future__ import annotations

import os
import pathlib
import tempfile
import unittest

from tools import generate_v2_review_queue as producer


class TerminalVaultHandoffTests(unittest.TestCase):
    def test_successful_canonical_cas_moves_displaced_inode_to_cold_incoming(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            (root / "go.mod").write_text("module fixture\n", encoding="utf-8")
            pages = root / "data/editorial/v2_pages"
            pages.mkdir(parents=True)
            target = pages / "area-01.jsonl"
            target.write_bytes(b"preimage\n")
            descriptor = os.open(target, os.O_RDWR)
            try:
                expected = producer.snapshot_sha256(target)
                producer.atomic_replace_cas(target, b"postimage\n", expected)
                self.assertEqual(target.read_bytes(), b"postimage\n")
                self.assertEqual(
                    list(pages.glob(
                        ".area-01.jsonl.stale-cas-"
                        "displaced-committed-retained-*")),
                    [],
                )
                incoming = list((
                    root / "data/editorial/v2_artifact_vault/incoming/"
                    "review_queue_stale_cas"
                ).glob(
                    ".area-01.jsonl.stale-cas-"
                    "displaced-committed-retained-*"))
                self.assertEqual(len(incoming), 1)
                self.assertEqual(incoming[0].read_bytes(), b"preimage\n")

                os.lseek(descriptor, 0, os.SEEK_SET)
                os.ftruncate(descriptor, 0)
                os.write(descriptor, b"late-fd-write\n")
                os.fsync(descriptor)
                self.assertEqual(incoming[0].read_bytes(), b"late-fd-write\n")
                self.assertEqual(target.read_bytes(), b"postimage\n")
            finally:
                os.close(descriptor)


if __name__ == "__main__":
    unittest.main()
