from __future__ import annotations

import os
import pathlib
import tempfile
import threading
import unittest

from tools import v2_stock_epoch as epoch


class CanonicalStockEpochThreadingTest(unittest.TestCase):
    def test_nested_go_mod_cannot_shadow_canonical_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "go.mod").write_text("module fixture\n", encoding="utf-8")
            target = root / "data" / "editorial" / "v2_pages" / "civil.jsonl"
            target.parent.mkdir(parents=True)
            (target.parent / "go.mod").write_text(
                "module nested-shadow\n", encoding="utf-8"
            )
            target.write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                epoch.canonical_stock_root_for_target(target), root.resolve()
            )

            unrelated = root / "data" / "other" / "record.jsonl"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("{}\n", encoding="utf-8")
            self.assertIsNone(epoch.canonical_stock_root_for_target(unrelated))

    def test_same_thread_is_reentrant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with epoch.canonical_stock_write_lease(directory):
                with epoch.canonical_stock_write_lease(directory):
                    self.assertEqual(epoch._LEASE_DEPTH, 2)
            self.assertEqual(epoch._LEASE_DEPTH, 0)

    def test_other_thread_fails_fast_and_can_acquire_after_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first_result: list[BaseException | str] = []

            def contender() -> None:
                try:
                    with epoch.canonical_stock_write_lease(directory):
                        first_result.append("acquired")
                except BaseException as error:  # surfaced to the test thread
                    first_result.append(error)

            with epoch.canonical_stock_write_lease(directory):
                blocked = threading.Thread(target=contender)
                blocked.start()
                blocked.join(timeout=0.5)
                self.assertFalse(blocked.is_alive(), "contender blocked instead of failing fast")
                self.assertEqual(len(first_result), 1)
                self.assertIsInstance(first_result[0], epoch.StockEpochBusy)

            second_result: list[BaseException | str] = []

            def released_contender() -> None:
                try:
                    with epoch.canonical_stock_write_lease(directory):
                        second_result.append("acquired")
                except BaseException as error:
                    second_result.append(error)

            released = threading.Thread(target=released_contender)
            released.start()
            released.join(timeout=0.5)
            self.assertFalse(released.is_alive())
            self.assertEqual(second_result, ["acquired"])

    @unittest.skipUnless(hasattr(os, "fork"), "requires fork")
    def test_forked_child_does_not_trust_parent_thread_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            read_fd, write_fd = os.pipe()
            try:
                with epoch.canonical_stock_write_lease(directory):
                    child = os.fork()
                    if child == 0:
                        os.close(read_fd)
                        result = b"unexpected"
                        try:
                            with epoch.canonical_stock_write_lease(directory):
                                result = b"acquired"
                        except epoch.StockEpochBusy:
                            result = b"busy"
                        except BaseException:
                            result = b"error"
                        os.write(write_fd, result)
                        os._exit(0)
                    os.close(write_fd)
                    write_fd = -1
                    result = os.read(read_fd, 32)
                    waited, status = os.waitpid(child, 0)
                    self.assertEqual(waited, child)
                    self.assertTrue(os.WIFEXITED(status))
                    self.assertEqual(os.WEXITSTATUS(status), 0)
                    self.assertEqual(result, b"busy")
            finally:
                os.close(read_fd)
                if write_fd >= 0:
                    os.close(write_fd)


if __name__ == "__main__":
    unittest.main()
