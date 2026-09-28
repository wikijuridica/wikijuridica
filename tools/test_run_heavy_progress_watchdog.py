#!/usr/bin/env python3
"""Focused lifecycle and protocol tests for run-heavy-progress-watchdog."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
WATCHDOG = TOOLS_DIR / "run-heavy-progress-watchdog"
SUPERVISOR = TOOLS_DIR / "supervise-process-tree"


class ProgressWatchdogTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.lock_dir = self.root / "lock"
        self.lock_dir.mkdir(mode=0o700)
        self.target = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.addCleanup(self._stop_target)

    def _stop_target(self) -> None:
        if self.target.poll() is None:
            self.target.terminate()
            try:
                self.target.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.target.kill()
                self.target.wait(timeout=1)

    def _checker(self, program: str) -> Path:
        checker = self.root / "check-command-progress"
        checker.write_text(textwrap.dedent(program))
        checker.chmod(0o755)
        return checker

    def _risk_then_exited_checker(
        self, status: str, *, risk_samples: int
    ) -> tuple[Path, Path]:
        """Return a deterministic protocol double that ends without a deadline.

        The real checker owns one observation window per invocation.  Repeating
        a risk forever would make a short watchdog deadline double as the test's
        termination mechanism and race the startup of consecutive supervised
        probes.  This double instead emits exactly the requested risk samples,
        then the real protocol's terminal ``exited`` result.
        """

        counter = self.root / f"{status}.samples"
        checker = self._checker(
            f"""\
            #!/usr/bin/env python3
            from pathlib import Path

            counter = Path({str(counter)!r})
            try:
                samples = int(counter.read_text())
            except FileNotFoundError:
                samples = 0
            if samples >= {risk_samples}:
                print("status=exited reason=fixture_complete schema=command-progress/v4")
                raise SystemExit(0)
            counter.write_text(str(samples + 1))
            print("status={status} reason=test schema=command-progress/v4 cpu_percent=0")
            raise SystemExit(2)
            """
        )
        return checker, counter

    def _arguments(
        self,
        checker: Path,
        *,
        deadline: float = 0.25,
        initial_delay: float = 0,
        alert_windows: int = 1,
        lock_scope: str = "test:watchdog",
    ) -> list[str]:
        return [
            str(WATCHDOG),
            "--target-pid",
            str(self.target.pid),
            "--check-command-progress",
            str(checker),
            "--supervise-process-tree",
            str(SUPERVISOR),
            "--lock-dir",
            str(self.lock_dir),
            "--lock-scope",
            lock_scope,
            "--initial-delay-seconds",
            str(initial_delay),
            "--window-seconds",
            "1",
            "--alert-windows",
            str(alert_windows),
            "--deadline-seconds",
            str(deadline),
        ]

    def _supervised_invocation(self, arguments: list[str], timeout: float) -> list[str]:
        return [
            str(SUPERVISOR),
            "--timeout-seconds",
            str(timeout),
            "--kill-after-seconds",
            "1",
            "--term-grace-seconds",
            "1",
            "--kill-grace-seconds",
            "1",
            "--fail-on-descendant-cleanup",
            "--close-fd8",
            "--",
            *arguments,
        ]

    def _run(
        self,
        checker: Path,
        *,
        deadline: float = 0.25,
        initial_delay: float = 0,
        alert_windows: int = 1,
        lock_scope: str = "test:watchdog",
    ) -> tuple[subprocess.CompletedProcess[str], float]:
        arguments = self._arguments(
            checker,
            deadline=deadline,
            initial_delay=initial_delay,
            alert_windows=alert_windows,
            lock_scope=lock_scope,
        )
        started = time.monotonic()
        completed = subprocess.run(
            self._supervised_invocation(arguments, deadline + 2),
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            timeout=deadline + 4,
            check=False,
        )
        return completed, time.monotonic() - started

    @staticmethod
    def _identity(pid: int) -> tuple[int, int] | None:
        try:
            payload = Path(f"/proc/{pid}/stat").read_text()
        except (FileNotFoundError, ProcessLookupError):
            return None
        close_paren = payload.rfind(")")
        fields = payload[close_paren + 2 :].split()
        return pid, int(fields[19])

    @classmethod
    def _descendant_identities(cls, root_pid: int) -> set[tuple[int, int]]:
        processes: dict[int, tuple[int, int]] = {}
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                payload = (entry / "stat").read_text()
                fields = payload[payload.rfind(")") + 2 :].split()
                processes[int(entry.name)] = (int(fields[1]), int(fields[19]))
            except (FileNotFoundError, OSError, ValueError, IndexError):
                continue
        descendants: set[tuple[int, int]] = set()
        frontier = {root_pid}
        while frontier:
            children = {
                pid
                for pid, (parent_pid, _start_ticks) in processes.items()
                if parent_pid in frontier
                and all(existing_pid != pid for existing_pid, _ in descendants)
            }
            for pid in children:
                descendants.add((pid, processes[pid][1]))
            frontier = children
        return descendants

    @classmethod
    def _assert_identity_gone(
        cls, testcase: unittest.TestCase, identity: tuple[int, int], timeout: float = 3
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cls._identity(identity[0]) != identity:
                return
            time.sleep(0.02)
        testcase.fail(f"process identity survived watchdog cleanup: {identity}")

    def test_preserves_all_v4_risk_statuses_and_alert_threshold(self) -> None:
        statuses = (
            "idle_stall_risk",
            "busy_loop_risk",
            "io_without_progress_risk",
            "observer_invalid_risk",
            "observer_regression_risk",
            "reported_progress_unverified_risk",
            "unattributed_progress_risk",
        )
        for status in statuses:
            with self.subTest(status=status):
                expected_windows = (
                    1
                    if status
                    in {"observer_invalid_risk", "observer_regression_risk"}
                    else 2
                )
                checker, counter = self._risk_then_exited_checker(
                    status, risk_samples=expected_windows
                )
                completed, _elapsed = self._run(
                    # The fixture exits through the protocol.  The deadline is
                    # now only a bounded failure guard, not a race-prone timer
                    # that must fit two independent supervisor startups.
                    checker,
                    alert_windows=2,
                    deadline=4,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("schema=command-progress/v4", completed.stderr)
                self.assertIn(f"status={status}", completed.stderr)
                self.assertIn(
                    f"consecutive_windows={expected_windows}", completed.stderr
                )
                self.assertIn(
                    "action=read_live_artifact_and_fix_root_cause_before_rerun",
                    completed.stderr,
                )
                self.assertEqual(counter.read_text(), str(expected_windows))
                self.assertIsNone(self.target.poll())

    def test_exited_invalid_schema_and_unexpected_exit_match_inline_protocol(self) -> None:
        cases = (
            (
                "exited",
                "echo 'status=exited reason=gone schema=command-progress/v4'; exit 0",
                None,
            ),
            (
                "invalid_schema",
                "exit 0",
                "status=monitor_failure reason=invalid_or_missing_schema rc=0",
            ),
            (
                "unexpected_exit",
                "echo 'status=idle_stall_risk reason=x schema=command-progress/v4'; exit 0",
                "status=monitor_failure reason=unexpected_status_or_exit rc=0",
            ),
        )
        for name, body, expected in cases:
            with self.subTest(name=name):
                checker = self._checker(f"#!/bin/sh\n{body}\n")
                # Every fixture terminates through the protocol; this is a
                # startup guard, not a scheduler race.
                completed, elapsed = self._run(checker, deadline=2)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                if expected is None:
                    self.assertNotIn("progress_monitor_alert", completed.stderr)
                else:
                    self.assertIn(expected, completed.stderr)
                    self.assertIn(
                        "action=inspect_monitor_without_signalling_command",
                        completed.stderr,
                    )
                self.assertLess(elapsed, 1.5)
                self.assertIsNone(self.target.poll())

    def test_tokens_are_single_line_bounded_and_terminal_safe(self) -> None:
        counter = self.root / "terminal-safe.samples"
        checker = self._checker(
            f"""\
            #!/usr/bin/env python3
            import sys
            from pathlib import Path

            counter = Path({str(counter)!r})
            if counter.exists():
                print("status=exited reason=fixture_complete schema=command-progress/v4")
                raise SystemExit(0)
            counter.write_text("1")
            sys.stdout.write("status=observer_invalid_risk reason=bad\\x1b[31m schema=command-progress/v4\\nsecond=forbidden\\n")
            raise SystemExit(2)
            """
        )
        completed, _elapsed = self._run(
            checker,
            # The terminal protocol result ends the fixture.  The deadline is
            # only a guard and no longer races process-supervisor startup.
            deadline=2,
            lock_scope="scope with spaces\nnext\x1b[2J",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("\x1b", completed.stderr)
        self.assertNotIn("second=forbidden", completed.stderr)
        alert_lines = [
            line
            for line in completed.stderr.splitlines()
            if "progress_monitor_alert" in line
        ]
        self.assertGreaterEqual(len(alert_lines), 1, completed.stderr)
        self.assertTrue(
            all("lock_scope=scope_with_spaces_next_[2J" in line for line in alert_lines),
            alert_lines,
        )
        self.assertEqual(counter.read_text(), "1")
        self.assertIsNone(self.target.poll())

    def test_closes_inherited_descriptors_before_initial_delay(self) -> None:
        checker = self._checker(
            "#!/bin/sh\necho 'status=exited reason=gone schema=command-progress/v4'\n"
        )
        read_fd, write_fd = os.pipe()
        os.set_inheritable(read_fd, True)
        try:
            process = subprocess.Popen(
                self._arguments(
                    checker, deadline=1.2, initial_delay=0.5
                ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                pass_fds=(read_fd,),
            )
            inherited_path = Path(f"/proc/{process.pid}/fd/{read_fd}")
            deadline = time.monotonic() + 0.4
            while inherited_path.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertFalse(inherited_path.exists())
            _stdout, stderr = process.communicate(timeout=2)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIsNone(self.target.poll())
        finally:
            os.close(read_fd)
            os.close(write_fd)

    def test_term_is_bounded_probe_is_reaped_and_target_is_never_signalled(self) -> None:
        probe_pid_file = self.root / "probe.pid"
        checker = self._checker(
            f"""\
            #!/usr/bin/env python3
            import os
            import pathlib
            import signal
            import time
            pathlib.Path({str(probe_pid_file)!r}).write_text(str(os.getpid()))
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            while True:
                time.sleep(1)
            """
        )
        arguments = self._arguments(checker, deadline=8)
        started = time.monotonic()
        process = subprocess.Popen(
            self._supervised_invocation(arguments, 10),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 2
        while not probe_pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(probe_pid_file.exists(), "probe never started")
        probe_identity = self._identity(int(probe_pid_file.read_text()))
        self.assertIsNotNone(probe_identity)
        owned_identities = self._descendant_identities(process.pid)
        process.send_signal(signal.SIGTERM)
        _stdout, stderr = process.communicate(timeout=6)
        self.assertEqual(process.returncode, 143, stderr)
        self.assertLess(time.monotonic() - started, 5.5)
        self.assertIsNone(self.target.poll(), "watchdog signalled the producer")
        assert probe_identity is not None
        self._assert_identity_gone(self, probe_identity)
        for identity in owned_identities:
            with self.subTest(owned_identity=identity):
                self._assert_identity_gone(self, identity)

    def test_supervisor_parent_sigkill_still_leaves_no_probe_orphan(self) -> None:
        probe_pid_file = self.root / "probe-parent-death.pid"
        checker = self._checker(
            f"""\
            #!/usr/bin/env python3
            import os
            import pathlib
            import signal
            import time
            pathlib.Path({str(probe_pid_file)!r}).write_text(str(os.getpid()))
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            while True:
                time.sleep(1)
            """
        )
        process = subprocess.Popen(
            self._supervised_invocation(self._arguments(checker, deadline=8), 10),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 2
        while not probe_pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(probe_pid_file.exists(), "probe never started")
        probe_identity = self._identity(int(probe_pid_file.read_text()))
        self.assertIsNotNone(probe_identity)
        owned_identities = self._descendant_identities(process.pid)
        process.kill()
        process.communicate(timeout=2)
        self.assertEqual(process.returncode, -signal.SIGKILL)
        self.assertIsNone(self.target.poll(), "watchdog signalled the producer")
        assert probe_identity is not None
        self._assert_identity_gone(self, probe_identity)
        for identity in owned_identities:
            with self.subTest(owned_identity=identity):
                self._assert_identity_gone(self, identity)


if __name__ == "__main__":
    unittest.main()
