#!/usr/bin/env python3
"""Focused regression tests for run-check build-lock initialization."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path


RUN_CHECK = Path(__file__).resolve().with_name("run-check")


class RunCheckBuildLockTest(unittest.TestCase):
    def test_symlink_cache_is_rejected_before_any_build_or_wait(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            tools = root / "tools"
            tools.mkdir(parents=True)
            wrapper = tools / "run-check"
            shutil.copy2(RUN_CHECK, wrapper)
            real_cache = Path(directory) / "real-cache"
            real_cache.mkdir()
            cache = Path(directory) / "cache-link"
            cache.symlink_to(real_cache, target_is_directory=True)
            environment = os.environ.copy()
            environment.update(
                {
                    "WIKI_CHECK_BIN_CACHE": str(cache),
                    "WIKI_CHECK_RUN_TIMEOUT_SECONDS": "2",
                }
            )
            result = subprocess.run(
                [str(wrapper), "fixture-check"],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertIn("writable non-symlink", result.stderr)

    def test_non_lock_mkdir_failure_fails_fast_instead_of_looping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            tools = root / "tools"
            tools.mkdir(parents=True)
            wrapper = tools / "run-check"
            shutil.copy2(RUN_CHECK, wrapper)
            cache = Path(directory) / "cache"
            cache.mkdir()
            (cache / "build.lock").write_text("regular-file-collision\n")
            environment = os.environ.copy()
            environment.update(
                {
                    "WIKI_CHECK_BIN_CACHE": str(cache),
                    "WIKI_CHECK_RUN_TIMEOUT_SECONDS": "2",
                }
            )
            started = time.monotonic()
            result = subprocess.run(
                [str(wrapper), "fixture-check"],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertIn("mkdir failed without a valid same-user lock directory", result.stderr)
            self.assertLess(elapsed, 1.0)

    def test_waiter_reads_complete_owner_metadata_after_bounded_handshake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            tools = root / "tools"
            tools.mkdir(parents=True)
            wrapper = tools / "run-check"
            shutil.copy2(RUN_CHECK, wrapper)

            cache = Path(directory) / "cache"
            lock = cache / "build.lock"
            lock.mkdir(parents=True)
            owner = subprocess.Popen(["sleep", "5"])
            try:
                metadata = lock / "meta"

                def publish_metadata() -> None:
                    time.sleep(0.05)
                    temporary = lock / ".meta.fixture"
                    temporary.write_text(
                        "\n".join(
                            [
                                f"pid:{owner.pid}",
                                f"started_epoch:{int(time.time())}",
                                "command:fixture-owner-build",
                                "timeout_seconds:5",
                                "budget_ms:5000",
                                "stop_condition:fixture_owner_exits",
                                "lock_scope:build:./cmd/check",
                                "",
                            ]
                        )
                    )
                    os.replace(temporary, metadata)

                publisher = threading.Thread(target=publish_metadata)
                publisher.start()
                environment = os.environ.copy()
                environment.update(
                    {
                        "WIKI_CHECK_BIN_CACHE": str(cache),
                        "WIKI_CHECK_BUILD_LOCK_META_INIT_GRACE_MS": "500",
                        "WIKI_CHECK_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait",
                        "WIKI_CHECK_RUN_TIMEOUT_SECONDS": "2",
                    }
                )
                started = time.monotonic()
                result = subprocess.run(
                    [str(wrapper), "fixture-check"],
                    cwd=root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    timeout=3,
                    check=False,
                )
                elapsed = time.monotonic() - started
                publisher.join(timeout=1)
                self.assertEqual(result.returncode, 75, result.stderr)
                self.assertIn(f"pid={owner.pid}", result.stderr)
                self.assertIn("command=fixture-owner-build", result.stderr)
                self.assertNotIn("hypothesis=lock_metadata_missing", result.stderr)
                self.assertGreaterEqual(elapsed, 0.04)
                self.assertLess(elapsed, 1.5)
            finally:
                owner.terminate()
                owner.wait(timeout=2)

    def test_missing_metadata_grace_has_a_hard_upper_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            tools = root / "tools"
            tools.mkdir(parents=True)
            wrapper = tools / "run-check"
            shutil.copy2(RUN_CHECK, wrapper)
            cache = Path(directory) / "cache"
            (cache / "build.lock").mkdir(parents=True)
            environment = os.environ.copy()
            environment.update(
                {
                    "WIKI_CHECK_BIN_CACHE": str(cache),
                    "WIKI_CHECK_BUILD_LOCK_META_INIT_GRACE_MS": "30",
                    "WIKI_CHECK_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait",
                    "WIKI_CHECK_RUN_TIMEOUT_SECONDS": "2",
                }
            )
            started = time.monotonic()
            result = subprocess.run(
                [str(wrapper), "fixture-check"],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertIn("hypothesis=lock_metadata_missing", result.stderr)
            self.assertLess(elapsed, 1.0)

    def test_malformed_metadata_is_not_reclaimed_before_stale_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            tools = root / "tools"
            tools.mkdir(parents=True)
            wrapper = tools / "run-check"
            shutil.copy2(RUN_CHECK, wrapper)
            cache = Path(directory) / "cache"
            lock = cache / "build.lock"
            lock.mkdir(parents=True)
            metadata = lock / "meta"
            metadata.write_text("started_epoch:1\ncommand:partial-owner\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "WIKI_CHECK_BIN_CACHE": str(cache),
                    "WIKI_CHECK_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait",
                    "WIKI_CHECK_BUILD_LOCK_STALE_SECONDS": "900",
                    "WIKI_CHECK_RUN_TIMEOUT_SECONDS": "2",
                }
            )
            result = subprocess.run(
                [str(wrapper), "fixture-check"],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertIn("pid=unknown", result.stderr)
            self.assertTrue(metadata.is_file())

    def test_critical_wait_rejects_owner_pid_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            tools = root / "tools"
            tools.mkdir(parents=True)
            wrapper = tools / "run-check"
            shutil.copy2(RUN_CHECK, wrapper)
            cache = Path(directory) / "cache"
            lock = cache / "build.lock"
            lock.mkdir(parents=True)
            owner = subprocess.Popen(["sleep", "5"])
            try:
                (lock / "meta").write_text(
                    "\n".join(
                        [
                            f"pid:{owner.pid}",
                            f"started_epoch:{int(time.time())}",
                            "command:fixture-owner-build",
                            "timeout_seconds:5",
                            "budget_ms:5000",
                            "stop_condition:fixture_owner_exits",
                            "lock_scope:build:./cmd/check",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )
                environment = os.environ.copy()
                environment.update(
                    {
                        "WIKI_CHECK_BIN_CACHE": str(cache),
                        "WIKI_CHECK_BUILD_LOCK_WAIT_CLASSIFICATION": "critical_dependency",
                        "WIKI_CHECK_BUILD_LOCK_DEPENDENCY_ID": "fixture-dependency",
                        "WIKI_CHECK_BUILD_LOCK_OWNER_PID": str(owner.pid + 100000),
                        "WIKI_CHECK_BUILD_LOCK_WAIT_TIMEOUT_MS": "1000",
                        "WIKI_CHECK_BUILD_LOCK_LAST_EVIDENCE": "fixture-evidence",
                        "WIKI_CHECK_BUILD_LOCK_REORIENTATION_COMMAND": "fixture-command",
                        "WIKI_CHECK_RUN_TIMEOUT_SECONDS": "2",
                    }
                )
                result = subprocess.run(
                    [str(wrapper), "fixture-check"],
                    cwd=root,
                    env=environment,
                    text=True,
                    capture_output=True,
                    timeout=3,
                    check=False,
                )
                self.assertEqual(result.returncode, 75, result.stderr)
                self.assertIn(f"owner_pid_mismatch(observed={owner.pid})", result.stderr)
                self.assertTrue(lock.is_dir())
            finally:
                owner.terminate()
                owner.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
