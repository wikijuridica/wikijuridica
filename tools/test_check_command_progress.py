#!/usr/bin/env python3
"""Focused deterministic tests for check-command-progress."""

from __future__ import annotations

import errno
import importlib.machinery
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


TOOLS_DIR = Path(__file__).resolve().parent
TOOL_PATH = TOOLS_DIR / "check-command-progress"
LOADER = importlib.machinery.SourceFileLoader("check_command_progress", str(TOOL_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
MONITOR = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = MONITOR
LOADER.exec_module(MONITOR)


class CommandProgressTest(unittest.TestCase):
    def setUp(self) -> None:
        self.processes: list[subprocess.Popen[str]] = []

    def tearDown(self) -> None:
        for process in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

    def spawn_ready(self, program: str, *arguments: str) -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [sys.executable, "-c", program, *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.processes.append(process)
        assert process.stdout is not None
        ready = process.stdout.readline().strip()
        self.assertEqual(ready, "ready")
        return process

    def run_monitor(
        self,
        process: subprocess.Popen[str] | int,
        *arguments: str,
        window: str = "0.2",
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        pid = process if isinstance(process, int) else process.pid
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                str(pid),
                "--window-seconds",
                window,
                "--json",
                *arguments,
            ],
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )
        self.assertTrue(completed.stdout, completed.stderr)
        return completed, json.loads(completed.stdout)

    def current_identity(self) -> tuple[int, int]:
        process = MONITOR.ProcSampler()._read_process(os.getpid(), strict=True)
        assert process is not None
        return process.pid, process.start_ticks

    @staticmethod
    def progress_payload(
        pid: int,
        start_ticks: int,
        completed: int,
        **extra: object,
    ) -> str:
        payload: dict[str, object] = {
            "schema": MONITOR.PROGRESS_SCHEMA,
            "pid": pid,
            "start_ticks": start_ticks,
            "completed": completed,
        }
        payload.update(extra)
        return json.dumps(payload, sort_keys=True)

    def test_artifact_change_is_unattributed_not_productive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact.json"
            artifact.write_text('{"generation":0}')
            process = self.spawn_ready(
                "import pathlib,sys,time\n"
                "path=pathlib.Path(sys.argv[1])\n"
                "print('ready', flush=True)\n"
                "time.sleep(0.3)\n"
                "path.write_text('{\"generation\":1}')\n"
                "time.sleep(1)\n",
                str(artifact),
            )
            completed, result = self.run_monitor(
                process, "--artifact", str(artifact), window="0.65"
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(result["status"], "unattributed_progress_risk")
            self.assertEqual(
                result["reason"], "artifact_change_without_attributed_progress"
            )
            self.assertTrue(result["artifact_changed"])
            self.assertEqual(result["reported_progress_count"], 0)
            self.assertEqual(result["unattributed_artifact_change_count"], 1)
            self.assertTrue(result["identity_stable"])
            self.assertIsNone(process.poll(), "the observer must never terminate the command")

    def test_artifact_change_is_not_hidden_by_unchanged_progress_file(self) -> None:
        process = MONITOR.ProcessCounters(42, 1, 100, "S", 20)
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (process,))
        config = MONITOR.MonitorConfig(
            42,
            0.2,
            25.0,
            1,
            artifacts=("artifact",),
            progress_files=("progress",),
        )
        progress = ("progress", 42, 100, 7, None, None, None)
        observer_before = {
            ("artifact", "artifact"): ("artifact", 1, "before"),
            ("progress", "progress"): progress,
        }
        observer_after = {
            ("artifact", "artifact"): ("artifact", 1, "after"),
            ("progress", "progress"): progress,
        }
        result = MONITOR.evaluate_snapshots(
            before, after, observer_before, observer_after, config, 100
        )
        self.assertEqual(result["status"], "unattributed_progress_risk")
        self.assertEqual(
            result["reason"], "artifact_change_without_attributed_progress"
        )
        self.assertEqual(result["unattributed_artifact_change_count"], 1)
        self.assertEqual(result["reported_progress_count"], 0)

    def test_semantic_progress_file_is_self_reported_not_productive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            process = self.spawn_ready(
                "import json,os,pathlib,sys,time\n"
                "path=pathlib.Path(sys.argv[1])\n"
                "raw=pathlib.Path('/proc/self/stat').read_text()\n"
                "start=int(raw[raw.rfind(')')+2:].split()[19])\n"
                "def write(completed):\n"
                " path.write_text(json.dumps({'schema':'command-progress-counter/v1',"
                "'pid':os.getpid(),'start_ticks':start,'completed':completed}))\n"
                "write(0)\n"
                "print('ready', flush=True)\n"
                "time.sleep(0.3)\n"
                "write(1)\n"
                "time.sleep(1)\n",
                str(progress),
            )
            completed, result = self.run_monitor(
                process, "--progress-file", str(progress), window="0.65"
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(result["status"], "reported_progress_unverified_risk")
            self.assertEqual(
                result["reason"],
                "self_reported_progress_does_not_prove_writer_or_durable_output",
            )
            self.assertTrue(result["progress_changed"])
            self.assertEqual(result["reported_progress_count"], 1)

    def test_external_writer_cannot_turn_sleeping_target_green(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            target = self.spawn_ready(
                "import time\nprint('ready', flush=True)\ntime.sleep(2)\n"
            )
            observed = MONITOR.ProcSampler()._read_process(target.pid, strict=True)
            assert observed is not None
            common = {
                "producer": "copied-producer",
                "run_id": "copied-run",
                "lock_scope": "copied-scope",
            }
            progress.write_text(
                self.progress_payload(target.pid, observed.start_ticks, 0, **common)
            )
            attacker = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import pathlib,sys,time\n"
                    "time.sleep(0.3)\n"
                    "pathlib.Path(sys.argv[1]).write_text(sys.argv[2])\n",
                    str(progress),
                    self.progress_payload(
                        target.pid, observed.start_ticks, 1, **common
                    ),
                ],
                text=True,
            )
            self.processes.append(attacker)
            completed, result = self.run_monitor(
                target,
                "--progress-file",
                str(progress),
                "--progress-owner",
                common["producer"],
                "--progress-run-id",
                common["run_id"],
                "--progress-lock-scope",
                common["lock_scope"],
                window="0.65",
            )
            attacker.wait(timeout=1)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(result["status"], "reported_progress_unverified_risk")
            self.assertEqual(result["reported_progress_count"], 1)
            self.assertIsNone(target.poll(), "external reports must not affect the target")

    def test_heartbeat_touch_is_alive_but_not_output_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / "heartbeat"
            heartbeat.write_text("alive")
            process = self.spawn_ready(
                "import os,pathlib,sys,time\n"
                "path=pathlib.Path(sys.argv[1])\n"
                "print('ready', flush=True)\n"
                "time.sleep(0.3)\n"
                "current=path.stat()\n"
                "os.utime(path, ns=(current.st_atime_ns,current.st_mtime_ns+1000000))\n"
                "time.sleep(1)\n",
                str(heartbeat),
            )
            completed, result = self.run_monitor(
                process, "--heartbeat", str(heartbeat), window="0.65"
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(result["status"], "reported_progress_unverified_risk")
            self.assertEqual(
                result["reason"],
                "heartbeat_does_not_prove_writer_or_durable_output",
            )
            self.assertTrue(result["heartbeat_changed"])

    def test_touch_is_not_semantic_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            pid, start_ticks = self.current_identity()
            progress.write_text(self.progress_payload(pid, start_ticks, 1))
            config = MONITOR.MonitorConfig(
                pid, 0.1, 25.0, 1, progress_files=(str(progress),)
            )
            identities = frozenset({(pid, start_ticks)})
            before = MONITOR._observer_token(
                "progress", str(progress), config, identities
            )
            current = progress.stat()
            os.utime(
                progress,
                ns=(current.st_atime_ns, current.st_mtime_ns + 1_000_000),
            )
            after = MONITOR._observer_token(
                "progress", str(progress), config, identities
            )
            self.assertEqual(before, after)

    def test_touch_is_not_artifact_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact.json"
            artifact.write_text('{"completed":1}\n')
            before = MONITOR._observer_token("artifact", str(artifact))
            current = artifact.stat()
            os.utime(
                artifact,
                ns=(current.st_atime_ns, current.st_mtime_ns + 1_000_000),
            )
            after = MONITOR._observer_token("artifact", str(artifact))
            self.assertEqual(before, after)

    def test_deleted_artifact_is_regression_not_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact"
            artifact.write_text("required")
            process = self.spawn_ready(
                "import pathlib,sys,time\n"
                "path=pathlib.Path(sys.argv[1])\n"
                "print('ready', flush=True)\n"
                "time.sleep(0.3)\n"
                "path.unlink()\n"
                "time.sleep(1)\n",
                str(artifact),
            )
            completed, result = self.run_monitor(
                process, "--artifact", str(artifact), window="0.65"
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(result["status"], "observer_regression_risk")
            self.assertEqual(result["regressed_observer_count"], 1)
            self.assertFalse(result["artifact_changed"])

    def test_oversized_progress_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            progress.write_bytes(b"x" * (MONITOR.MAX_OBSERVER_BYTES + 1))
            token = MONITOR._observer_token("progress", str(progress))
            self.assertEqual(token[0], "invalid")
            self.assertEqual(token[1], "progress_file_too_large")

    def test_deep_json_fails_closed_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "deep.json"
            progress.write_text("[" * 2_000 + "0" + "]" * 2_000)
            token = MONITOR._observer_token("progress", str(progress))
            self.assertEqual(token[0], "invalid")
            self.assertEqual(token[1], "progress_json_invalid")

    def test_symlink_observer_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.write_text("value")
            link = Path(directory) / "link"
            link.symlink_to(target)
            token = MONITOR._observer_token("artifact", str(link))
            self.assertEqual(token[:2], ("invalid", "symlink_observer_not_followed"))

    def test_symlink_in_parent_component_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            (real / "artifact").write_text("value")
            link = root / "linked-parent"
            link.symlink_to(real, target_is_directory=True)
            token = MONITOR._observer_token("artifact", str(link / "artifact"))
            self.assertEqual(token[0], "invalid")
            self.assertEqual(token[1], "unsafe_path_component")

    def test_non_regular_observers_fail_closed_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fifo = root / "fifo"
            os.mkfifo(fifo)
            child_directory = root / "directory"
            child_directory.mkdir()
            for observer in (fifo, child_directory, Path("/dev/null")):
                started = __import__("time").monotonic()
                token = MONITOR._observer_token("artifact", str(observer))
                elapsed = __import__("time").monotonic() - started
                self.assertEqual(token[0], "invalid")
                self.assertEqual(token[1], "observer_requires_regular_file")
                self.assertLess(elapsed, 0.5)

    def test_device_final_component_is_only_opened_with_o_path(self) -> None:
        real_open = os.open
        final_flags: list[int] = []

        def recording_open(
            path: str,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            if path == "null" and dir_fd is not None:
                final_flags.append(flags)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(MONITOR.os, "open", side_effect=recording_open):
            token = MONITOR._observer_token("artifact", "/dev/null")
        self.assertEqual(token[:2], ("invalid", "observer_requires_regular_file"))
        self.assertEqual(len(final_flags), 1)
        self.assertTrue(final_flags[0] & os.O_PATH)
        self.assertTrue(final_flags[0] & os.O_NOFOLLOW)
        self.assertFalse(final_flags[0] & os.O_NONBLOCK)

    def test_heartbeat_reads_metadata_without_pread(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / "heartbeat"
            heartbeat.write_text("metadata only")
            with mock.patch.object(
                MONITOR.os,
                "pread",
                side_effect=AssertionError("heartbeat must not read content"),
            ):
                token = MONITOR._observer_token("heartbeat", str(heartbeat))
            self.assertEqual(token[0], "heartbeat")

    def test_noatime_denial_never_falls_back_to_metadata_mutating_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            observer = Path(directory) / "observer"
            observer.write_text("stable")
            real_open = os.open
            reader_attempts = 0

            def deny_noatime(
                path: str,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                nonlocal reader_attempts
                if path == "observer" and dir_fd is not None and flags & os.O_NONBLOCK:
                    reader_attempts += 1
                    raise PermissionError(errno.EPERM, "O_NOATIME denied")
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(MONITOR.os, "open", side_effect=deny_noatime):
                token = MONITOR._observer_token("artifact", str(observer))
            self.assertEqual(token[:2], ("invalid", "observer_reader_open_failed"))
            self.assertEqual(token[2], errno.EPERM)
            self.assertEqual(reader_attempts, 1)

    def test_final_component_swap_to_symlink_is_never_followed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observer = root / "observer"
            target = root / "target"
            observer.write_text("safe")
            target.write_text("must-not-be-read")
            real_open = os.open
            swapped = False

            def racing_open(
                path: str,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                nonlocal swapped
                if (
                    path == "observer"
                    and dir_fd is not None
                    and not flags & os.O_DIRECTORY
                    and not swapped
                ):
                    swapped = True
                    observer.unlink()
                    observer.symlink_to(target)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(MONITOR.os, "open", side_effect=racing_open):
                token = MONITOR._observer_token("artifact", str(observer))
            self.assertTrue(swapped)
            self.assertEqual(token[0], "invalid")
            self.assertEqual(token[1], "symlink_observer_not_followed")

    def test_final_component_replace_before_reader_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            observer = Path(directory) / "observer"
            replacement = Path(directory) / "replacement"
            observer.write_text("first inode")
            replacement.write_text("second inode")
            real_open = os.open
            final_open_count = 0

            def racing_open(
                path: str,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                nonlocal final_open_count
                if path == "observer" and dir_fd is not None:
                    final_open_count += 1
                    if final_open_count == 2:
                        os.replace(replacement, observer)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(MONITOR.os, "open", side_effect=racing_open):
                token = MONITOR._observer_token("artifact", str(observer))
            self.assertEqual(token[:2], ("invalid", "observer_replaced_before_read"))

    def test_mutation_during_pread_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact"
            artifact.write_text("stable-before-read")
            real_pread = os.pread
            mutated = False

            def mutating_pread(fd: int, size: int, offset: int) -> bytes:
                nonlocal mutated
                payload = real_pread(fd, size, offset)
                if not mutated:
                    mutated = True
                    current = artifact.stat()
                    os.utime(
                        artifact,
                        ns=(current.st_atime_ns, current.st_mtime_ns + 1_000_000),
                    )
                return payload

            with mock.patch.object(MONITOR.os, "pread", side_effect=mutating_pread):
                token = MONITOR._observer_token("artifact", str(artifact))
            self.assertEqual(token[:2], ("invalid", "observer_changed_during_read"))

    def test_large_artifact_pread_budget_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "large"
            artifact.write_bytes(b"x" * (MONITOR.MAX_OBSERVER_BYTES * 2 + 17))
            real_pread = os.pread
            requested = 0

            def bounded_pread(fd: int, size: int, offset: int) -> bytes:
                nonlocal requested
                requested += size
                return real_pread(fd, size, offset)

            with mock.patch.object(MONITOR.os, "pread", side_effect=bounded_pread):
                token = MONITOR._observer_token("artifact", str(artifact))
            self.assertEqual(token[0], "artifact")
            self.assertLessEqual(requested, MONITOR.MAX_OBSERVER_BYTES)

    def test_duplicate_progress_json_fails_closed_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid, start_ticks = self.current_identity()
            progress = Path(directory) / "progress.json"
            progress.write_text(
                "{"
                f'"schema":"{MONITOR.PROGRESS_SCHEMA}",'
                f'"pid":{pid},"start_ticks":{start_ticks},'
                '"completed":1,"completed":2}'
            )
            token = MONITOR._observer_token(
                "progress",
                str(progress),
                allowed_identities=frozenset({(pid, start_ticks)}),
            )
            self.assertEqual(token[:2], ("invalid", "progress_json_invalid"))

    def test_progress_identity_must_belong_to_observed_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid, start_ticks = self.current_identity()
            progress = Path(directory) / "progress.json"
            progress.write_text(self.progress_payload(pid, start_ticks, 1))
            token = MONITOR._observer_token(
                "progress",
                str(progress),
                allowed_identities=frozenset({(pid, start_ticks + 1)}),
            )
            self.assertEqual(token[0:2], ("invalid", "progress_process_not_in_tree"))

    def test_zero_start_ticks_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid, _ = self.current_identity()
            progress = Path(directory) / "progress.json"
            progress.write_text(self.progress_payload(pid, 0, 1))
            token = MONITOR._observer_token(
                "progress",
                str(progress),
                allowed_identities=frozenset({(pid, 0)}),
            )
            self.assertEqual(token[:2], ("invalid", "progress_process_identity_invalid"))

    def test_progress_auth_expectations_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid, start_ticks = self.current_identity()
            progress = Path(directory) / "progress.json"
            progress.write_text(
                self.progress_payload(
                    pid,
                    start_ticks,
                    1,
                    producer="producer-a",
                    run_id="run-a",
                    lock_scope="scope-a",
                )
            )
            config = MONITOR.MonitorConfig(
                pid,
                0.1,
                25.0,
                1,
                progress_files=(str(progress),),
                progress_owner="producer-b",
                progress_run_id="run-a",
                progress_lock_scope="scope-a",
            )
            token = MONITOR._observer_token(
                "progress",
                str(progress),
                config,
                frozenset({(pid, start_ticks)}),
            )
            self.assertEqual(token[:2], ("invalid", "progress_producer_mismatch"))

    def test_transition_machine_tracks_monotonic_self_reported_progress(self) -> None:
        baseline = ("progress", 42, 100, 7, "producer", "run", "scope")
        advanced = ("progress", 42, 100, 8, "producer", "run", "scope")
        regressed = ("progress", 42, 100, 6, "producer", "run", "scope")
        changed_owner = ("progress", 42, 100, 8, "other", "run", "scope")
        self.assertIs(
            MONITOR.classify_observer_transition("progress", baseline, advanced),
            MONITOR.ObserverTransition.PROGRESS_ADVANCED,
        )
        self.assertIs(
            MONITOR.classify_observer_transition("progress", baseline, regressed),
            MONITOR.ObserverTransition.PROGRESS_REGRESSED,
        )
        self.assertIs(
            MONITOR.classify_observer_transition(
                "progress", baseline, changed_owner
            ),
            MONITOR.ObserverTransition.PROGRESS_IDENTITY_CHANGED,
        )

    def test_fully_asserted_progress_start_remains_unverified(self) -> None:
        process = MONITOR.ProcessCounters(42, 1, 100, "S", 20)
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (process,))
        config = MONITOR.MonitorConfig(
            42,
            0.2,
            25.0,
            1,
            progress_files=("progress",),
            progress_owner="producer",
            progress_run_id="run",
            progress_lock_scope="scope",
        )
        old = {("progress", "progress"): ("missing",)}
        new = {
            ("progress", "progress"): (
                "progress",
                42,
                100,
                1,
                "producer",
                "run",
                "scope",
            )
        }
        result = MONITOR.evaluate_snapshots(before, after, old, new, config, 100)
        self.assertEqual(result["status"], "reported_progress_unverified_risk")
        self.assertEqual(result["reported_progress_count"], 1)

        unauthenticated = MONITOR.classify_observer_transition(
            "progress", ("missing",), new[("progress", "progress")]
        )
        self.assertIs(
            unauthenticated,
            MONITOR.ObserverTransition.APPEARED_UNVERIFIED,
        )
        zero = tuple(
            0 if index == 3 else value
            for index, value in enumerate(new[("progress", "progress")])
        )
        not_started = MONITOR.classify_observer_transition(
            "progress",
            ("missing",),
            zero,
            fully_asserted_progress_metadata=True,
        )
        self.assertIs(not_started, MONITOR.ObserverTransition.APPEARED_UNVERIFIED)

    def test_final_snapshot_accepts_identity_seen_in_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            progress.write_text(self.progress_payload(43, 200, 1))
            config = MONITOR.MonitorConfig(
                42,
                0.2,
                25.0,
                1,
                progress_files=(str(progress),),
            )
            root = MONITOR.ProcessCounters(42, 1, 100, "S", 20)
            child = MONITOR.ProcessCounters(43, 42, 200, "S", 10)
            after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (root,))
            observations = MONITOR.snapshot_observers(
                config,
                after,
                frozenset({(child.pid, child.start_ticks)}),
            )
            self.assertEqual(observations[("progress", str(progress))][0], "progress")

    def test_invalid_baseline_cannot_become_productive(self) -> None:
        process = MONITOR.ProcessCounters(42, 1, 100, "S", 20)
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (process,))
        config = MONITOR.MonitorConfig(
            42, 0.2, 25.0, 1, progress_files=("progress",)
        )
        old = {("progress", "progress"): ("invalid", "bad_schema")}
        new = {
            ("progress", "progress"): (
                "progress",
                42,
                100,
                9,
                None,
                None,
                None,
            )
        }
        result = MONITOR.evaluate_snapshots(before, after, old, new, config, 100)
        self.assertEqual(result["status"], "observer_invalid_risk")
        self.assertEqual(result["reason"], "observer_baseline_invalid")
        self.assertEqual(result["baseline_invalid_observer_count"], 1)

    def test_busy_loop_with_unchanged_observer_is_risk_not_activity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "unchanged"
            artifact.write_text("unchanged")
            process = self.spawn_ready(
                "import time\n"
                "print('ready', flush=True)\n"
                "deadline=time.monotonic()+2\n"
                "value=0\n"
                "while time.monotonic()<deadline:\n"
                " value=(value+1)%1000003\n"
            )
            completed, result = self.run_monitor(
                process,
                "--artifact",
                str(artifact),
                "--busy-cpu-percent",
                "0.1",
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(result["status"], "busy_loop_risk")
            self.assertGreater(result["cpu_ticks_delta"], 0)
            self.assertFalse(result["artifact_changed"])
            self.assertIsNone(process.poll(), "risk detection must not kill the process")

    def test_busy_compute_without_observer_is_unverified(self) -> None:
        process = self.spawn_ready(
            "import time\n"
            "print('ready', flush=True)\n"
            "deadline=time.monotonic()+2\n"
            "value=0\n"
            "while time.monotonic()<deadline:\n"
            " value=(value+1)%1000003\n"
        )
        completed, result = self.run_monitor(
            process, "--busy-cpu-percent", "0.1"
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "compute_unverified")
        self.assertEqual(result["reason"], "cpu_activity_without_progress_observer")

    def test_idle_process_is_stall_risk(self) -> None:
        process = self.spawn_ready(
            "import time\nprint('ready', flush=True)\ntime.sleep(2)\n"
        )
        completed, result = self.run_monitor(
            process,
            "--busy-cpu-percent",
            "50",
            "--min-io-activity-bytes",
            "1000000000",
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "idle_stall_risk")

    def test_descendant_cpu_is_included_in_process_tree(self) -> None:
        process = self.spawn_ready(
            "import signal,subprocess,sys,time\n"
            "child=subprocess.Popen([sys.executable,'-c',"
            "'import time; deadline=time.monotonic()+2; value=0; '"
            "'\\nwhile time.monotonic()<deadline: value=(value+1)%1000003'])\n"
            "def stop(*_):\n"
            " child.terminate()\n"
            " child.wait(timeout=1)\n"
            " raise SystemExit(0)\n"
            "signal.signal(signal.SIGTERM, stop)\n"
            "print('ready', flush=True)\n"
            "child.wait()\n"
        )
        completed, result = self.run_monitor(
            process, "--busy-cpu-percent", "0.1", window="0.25"
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "compute_unverified")
        self.assertGreaterEqual(result["tree_processes_before"], 2)
        self.assertGreater(result["cpu_ticks_delta"], 0)

    def test_missing_pid_is_exited_without_waiting_window(self) -> None:
        completed, result = self.run_monitor(99999999, window="0.5")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(result["status"], "exited")
        self.assertEqual(result["reason"], "missing_before_window")
        self.assertEqual(result["window_seconds"], 0.0)

        class MissingSampler:
            clock_ticks = 100

            @staticmethod
            def sample(_pid: int) -> None:
                return None

        sleeps: list[float] = []
        config = MONITOR.MonitorConfig(99999999, 60.0, 25.0, 1)
        MONITOR.monitor(config, sampler=MissingSampler(), sleep_fn=sleeps.append)
        self.assertEqual(sleeps, [], "a missing PID must not consume the window budget")

    def test_observer_inside_target_tree_fails_closed_without_window(self) -> None:
        started = __import__("time").monotonic()
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                str(os.getpid()),
                "--window-seconds",
                "1",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=1,
            check=False,
        )
        elapsed = __import__("time").monotonic() - started
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("observer_process_inside_target_tree", completed.stderr)
        self.assertLess(elapsed, 0.5)

    def test_existing_malformed_root_proc_stat_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc_root = Path(directory)
            process_root = proc_root / "42"
            process_root.mkdir()
            (process_root / "stat").write_text("42 malformed-without-fields\n")
            (proc_root / "uptime").write_text("100.0 50.0\n")
            self_root = proc_root / "self"
            self_root.mkdir()
            (self_root / "stat").write_text(
                "1 (python) S " + " ".join(["0"] * 18 + ["123"]) + "\n"
            )
            sampler = MONITOR.ProcSampler(proc_root)
            with self.assertRaisesRegex(
                MONITOR.InspectionError, "proc_stat_malformed"
            ):
                MONITOR.monitor(
                    MONITOR.MonitorConfig(42, 0.1, 25.0, 1),
                    sampler=sampler,
                    sleep_fn=lambda _seconds: None,
                )

    def test_missing_procfs_is_not_misreported_as_exited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            absent = Path(directory) / "not-mounted"
            sampler = MONITOR.ProcSampler(absent)
            with self.assertRaisesRegex(MONITOR.InspectionError, "procfs_unavailable"):
                MONITOR.monitor(
                    MONITOR.MonitorConfig(99999999, 0.1, 25.0, 1),
                    sampler=sampler,
                    sleep_fn=lambda _seconds: None,
                )

    def test_empty_procfs_mount_is_not_misreported_as_exited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sampler = MONITOR.ProcSampler(Path(directory))
            with self.assertRaisesRegex(MONITOR.InspectionError, "procfs_unavailable"):
                MONITOR.monitor(
                    MONITOR.MonitorConfig(99999999, 0.1, 25.0, 1),
                    sampler=sampler,
                    sleep_fn=lambda _seconds: None,
                )

    def test_nonfinite_procfs_uptime_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc_root = Path(directory)
            (proc_root / "uptime").write_text("nan 0\n")
            self_root = proc_root / "self"
            self_root.mkdir()
            (self_root / "stat").write_text(
                "1 (python) S " + " ".join(["0"] * 18 + ["123"]) + "\n"
            )
            sampler = MONITOR.ProcSampler(proc_root)
            with self.assertRaisesRegex(MONITOR.InspectionError, "procfs_unavailable"):
                MONITOR.monitor(
                    MONITOR.MonitorConfig(99999999, 0.1, 25.0, 1),
                    sampler=sampler,
                    sleep_fn=lambda _seconds: None,
                )

    def test_pid_starttime_change_is_identity_change(self) -> None:
        before_process = MONITOR.ProcessCounters(42, 1, 100, "R", 20)
        after_process = MONITOR.ProcessCounters(42, 1, 200, "R", 30)
        before = MONITOR.TreeSnapshot(42, 100, "R", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 200, "R", 1.1, 100.1, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.1, 1.0, 1)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["status"], "exited")
        self.assertEqual(result["reason"], "pid_identity_changed")
        self.assertFalse(result["identity_stable"])

    def test_io_delta_is_unverified_not_productive(self) -> None:
        before_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, wchar=100, io_available=True
        )
        after_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, wchar=250, io_available=True
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["status"], "compute_unverified")
        self.assertEqual(result["reason"], "io_activity_without_explicit_progress")
        self.assertEqual(result["io_chars_delta"], 150)

    def test_logical_and_storage_io_are_not_double_counted(self) -> None:
        before_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, io_available=True
        )
        after_process = MONITOR.ProcessCounters(
            42,
            1,
            100,
            "S",
            20,
            rchar=100,
            read_bytes=100,
            io_available=True,
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 150)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["io_chars_delta"], 100)
        self.assertEqual(result["io_read_bytes_delta"], 100)
        self.assertEqual(result["status"], "idle_stall_risk")
        self.assertEqual(result["reason"], "no_progress_cpu_or_io_activity")

    def test_io_availability_transition_does_not_import_lifetime_counters(self) -> None:
        before_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, io_available=False
        )
        after_process = MONITOR.ProcessCounters(
            42,
            1,
            100,
            "S",
            20,
            rchar=10_000,
            wchar=20_000,
            read_bytes=30_000,
            write_bytes=40_000,
            io_available=True,
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["io_chars_delta"], 0)
        self.assertEqual(result["io_read_bytes_delta"], 0)
        self.assertEqual(result["io_write_bytes_delta"], 0)
        self.assertEqual(result["status"], "idle_stall_risk")

    def test_prebaseline_new_identity_counters_are_not_attributed_to_window(self) -> None:
        root = MONITOR.ProcessCounters(42, 1, 100, "S", 20, io_available=True)
        child = MONITOR.ProcessCounters(
            43,
            42,
            10_000,
            "S",
            500,
            wchar=50_000,
            io_available=True,
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (root,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (root, child))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["tree_spawned"], 1)
        self.assertEqual(result["cpu_ticks_delta"], 0)
        self.assertEqual(result["io_chars_delta"], 0)
        self.assertEqual(result["status"], "idle_stall_risk")

    def test_postbaseline_new_identity_counters_are_bounded_to_window(self) -> None:
        root = MONITOR.ProcessCounters(42, 1, 100, "S", 20, io_available=True)
        child = MONITOR.ProcessCounters(
            43,
            42,
            10_001,
            "S",
            1,
            wchar=1,
            io_available=True,
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (root,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (root, child))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["tree_spawned"], 1)
        self.assertEqual(result["cpu_ticks_delta"], 1)
        self.assertEqual(result["io_chars_delta"], 1)
        self.assertEqual(result["status"], "compute_unverified")

    def test_overrun_mode_classifies_unverified_io_as_risk(self) -> None:
        before_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, wchar=100, io_available=True
        )
        after_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, wchar=250, io_available=True
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1, overrun_risk=True)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["status"], "io_without_progress_risk")
        self.assertEqual(
            result["reason"], "declared_duration_exceeded_with_unverified_io"
        )

    def test_overrun_mode_classifies_unverified_compute_as_risk(self) -> None:
        before_process = MONITOR.ProcessCounters(42, 1, 100, "R", 20)
        after_process = MONITOR.ProcessCounters(42, 1, 100, "R", 30)
        before = MONITOR.TreeSnapshot(42, 100, "R", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 100, "R", 1.2, 100.2, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.2, 1.0, 1, overrun_risk=True)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["status"], "busy_loop_risk")
        self.assertEqual(
            result["reason"], "declared_duration_exceeded_with_unverified_compute"
        )

    def test_overrun_mode_classifies_idle_target_as_risk(self) -> None:
        process = MONITOR.ProcessCounters(42, 1, 100, "S", 20)
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (process,))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1, overrun_risk=True)
        result = MONITOR.evaluate_snapshots(before, after, {}, {}, config, 100)
        self.assertEqual(result["status"], "idle_stall_risk")
        self.assertEqual(
            result["reason"], "declared_duration_exceeded_without_material_progress"
        )

    def test_io_with_unchanged_expected_artifact_is_risk(self) -> None:
        before_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, wchar=100, io_available=True
        )
        after_process = MONITOR.ProcessCounters(
            42, 1, 100, "S", 20, wchar=250, io_available=True
        )
        before = MONITOR.TreeSnapshot(42, 100, "S", 1.0, 100.0, (before_process,))
        after = MONITOR.TreeSnapshot(42, 100, "S", 1.2, 100.2, (after_process,))
        config = MONITOR.MonitorConfig(42, 0.2, 25.0, 1, artifacts=("artifact",))
        observers = {("artifact", "artifact"): ("artifact", 1, "same")}
        result = MONITOR.evaluate_snapshots(
            before, after, observers, observers, config, 100
        )
        self.assertEqual(result["status"], "io_without_progress_risk")
        self.assertEqual(
            result["reason"], "io_activity_without_expected_output_progress"
        )

    def test_zombie_root_does_not_consume_window(self) -> None:
        zombie_process = MONITOR.ProcessCounters(42, 1, 100, "Z", 20)
        zombie = MONITOR.TreeSnapshot(42, 100, "Z", 1.0, 100.0, (zombie_process,))

        class ZombieSampler:
            clock_ticks = 100

            @staticmethod
            def sample(_pid: int) -> MONITOR.TreeSnapshot:
                return zombie

        sleeps: list[float] = []
        config = MONITOR.MonitorConfig(42, 60.0, 25.0, 1)
        result = MONITOR.monitor(config, sampler=ZombieSampler(), sleep_fn=sleeps.append)
        self.assertEqual(result["status"], "exited")
        self.assertEqual(result["reason"], "root_zombie_before_window")
        self.assertEqual(result["window_seconds"], 0.0)
        self.assertEqual(sleeps, [])

    def test_key_value_schema_has_fixed_order(self) -> None:
        result = MONITOR._empty_result(42, "missing_before_window")
        output = io.StringIO()
        with redirect_stdout(output):
            MONITOR.emit(result, False)
        keys = [field.partition("=")[0] for field in output.getvalue().split()]
        self.assertEqual(keys, list(MONITOR.KV_FIELDS))

    def test_window_has_hard_upper_bound(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOL_PATH),
                str(os.getpid()),
                "--window-seconds",
                "60.01",
            ],
            text=True,
            capture_output=True,
            timeout=1,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("window-seconds must be between", completed.stderr)

    def test_observer_count_is_bounded_before_process_sampling(self) -> None:
        class ForbiddenSampler:
            clock_ticks = 100

            @staticmethod
            def sample(_pid: int) -> None:
                raise AssertionError("sampler must not run beyond observer limit")

        config = MONITOR.MonitorConfig(
            os.getpid(),
            0.1,
            25.0,
            1,
            artifacts=tuple(f"artifact-{index}" for index in range(MONITOR.MAX_OBSERVERS + 1)),
        )
        with self.assertRaisesRegex(MONITOR.InspectionError, "observer_limit_exceeded"):
            MONITOR.monitor(config, sampler=ForbiddenSampler())

    def test_help_does_not_claim_artifacts_are_productive(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(TOOL_PATH), "--help"],
            text=True,
            capture_output=True,
            timeout=1,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("never proves productive work", completed.stdout)


if __name__ == "__main__":
    unittest.main()
