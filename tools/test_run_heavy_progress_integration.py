#!/usr/bin/env python3
"""Fast integration tests for the run-heavy overrun watchdog."""

from __future__ import annotations

import json
import hashlib
import os
import signal
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
WRAPPER = TOOLS_DIR / "run-heavy-throttled"
FORBIDDEN_PROGRESS_ENV = (
    "WIKI_HEAVY_PROGRESS_FILE",
    "WIKI_HEAVY_PROGRESS_PROTOCOL",
    "WIKI_HEAVY_PROGRESS_OWNER",
    "WIKI_HEAVY_PROGRESS_RUN_ID",
    "WIKI_HEAVY_PROGRESS_LOCK_SCOPE",
    "WIKI_HEAVY_PROGRESS_CAPABLE",
)


def process_identity(pid: int) -> tuple[int, str] | None:
    try:
        payload = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError):
        return None
    fields = payload[payload.rfind(")") + 2 :].split()
    return int(fields[19]), fields[0]


def identity_is_running(pid: int, start_ticks: int) -> bool:
    identity = process_identity(pid)
    return identity is not None and identity[0] == start_ticks and identity[1] != "Z"


class RunHeavyOverrunIntegrationTest(unittest.TestCase):
    @staticmethod
    def descendant_processes(root_pid: int) -> dict[int, str]:
        processes: dict[int, tuple[int, str]] = {}
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                stat_payload = (entry / "stat").read_text()
                fields = stat_payload[stat_payload.rfind(")") + 2 :].split()
                parent_pid = int(fields[1])
                command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                    errors="replace"
                )
            except (FileNotFoundError, PermissionError, OSError, ValueError, IndexError):
                continue
            processes[int(entry.name)] = (parent_pid, command)
        descendants: dict[int, str] = {}
        frontier = {root_pid}
        while frontier:
            children = {
                pid: command
                for pid, (parent_pid, command) in processes.items()
                if parent_pid in frontier and pid not in descendants
            }
            descendants.update(children)
            frontier = set(children)
        return descendants

    def run_fake(
        self,
        *,
        sleep_seconds: float,
        exit_code: int,
        expected_ms: int = 1000,
        command_name: str = "run-check",
        monitor_program: str | None = None,
        environment_overrides: dict[str, str | None] | None = None,
        command_arguments: list[str] | None = None,
        signal_after_seconds: float | None = None,
        signal_number: int = signal.SIGTERM,
        command_program: str | None = None,
        precreated_lock_state: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path, float]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        command = root / command_name
        command.write_text(
            textwrap.dedent(
                command_program
                if command_program is not None
                else
                """\
                #!/usr/bin/env python3
                import os
                import pathlib
                import sys
                import time

                forbidden = (
                    "WIKI_HEAVY_PROGRESS_FILE",
                    "WIKI_HEAVY_PROGRESS_PROTOCOL",
                    "WIKI_HEAVY_PROGRESS_OWNER",
                    "WIKI_HEAVY_PROGRESS_RUN_ID",
                    "WIKI_HEAVY_PROGRESS_LOCK_SCOPE",
                    "WIKI_HEAVY_PROGRESS_CAPABLE",
                )
                leaked = [name for name in forbidden if name in os.environ]
                if leaked:
                    print("forbidden_progress_env=" + ",".join(leaked), file=sys.stderr)
                    raise SystemExit(91)
                pathlib.Path(os.environ["FAKE_HEAVY_PID_FILE"]).write_text(str(os.getpid()))
                time.sleep(float(os.environ["FAKE_HEAVY_SLEEP_SECONDS"]))
                print("records_per_second=1 records=1 duration_ms=1")
                raise SystemExit(int(os.environ["FAKE_HEAVY_EXIT_CODE"]))
                """
            )
        )
        command.chmod(0o755)
        lock_root = root / "locks"
        temporary_root = root / "tmp"
        temporary_root.mkdir()
        wrapper = WRAPPER
        if monitor_program is not None:
            harness_tools = root / "harness-tools"
            harness_tools.mkdir()
            wrapper = harness_tools / "run-heavy-throttled"
            wrapper.write_bytes(WRAPPER.read_bytes())
            wrapper.chmod(0o755)
            supervisor = harness_tools / "supervise-process-tree"
            supervisor.write_bytes((TOOLS_DIR / "supervise-process-tree").read_bytes())
            supervisor.chmod(0o755)
            watchdog = harness_tools / "run-heavy-progress-watchdog"
            watchdog.write_bytes(
                (TOOLS_DIR / "run-heavy-progress-watchdog").read_bytes()
            )
            watchdog.chmod(0o755)
            monitor = harness_tools / "check-command-progress"
            monitor.write_text(monitor_program)
            monitor.chmod(0o755)
        environment = os.environ.copy()
        for name in FORBIDDEN_PROGRESS_ENV:
            environment.pop(name, None)
        environment.update(
            {
                "FAKE_HEAVY_SLEEP_SECONDS": str(sleep_seconds),
                "FAKE_HEAVY_EXIT_CODE": str(exit_code),
                "FAKE_HEAVY_PID_FILE": str(root / "child.pid"),
                "WIKI_HEAVY_LOCK_DIR": str(lock_root),
                "TMPDIR": str(temporary_root),
                "WIKI_HEAVY_LOCK_WAIT_SECONDS": "2",
                "WIKI_HEAVY_LOCK_WAIT_NOTICE_SECONDS": "1",
                "WIKI_HEAVY_LOCK_HEARTBEAT_SECONDS": "1",
                "WIKI_HEAVY_LOCK_HEARTBEAT_STALE_SECONDS": "3",
                "WIKI_HEAVY_TIMEOUT_SECONDS": "8",
                "WIKI_HEAVY_TIMEOUT_KILL_AFTER_SECONDS": "1",
                "WIKI_HEAVY_BUDGET_MS": "8000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": str(expected_ms),
                "WIKI_HEAVY_STOP_CONDITION": "fake_command_exits_or_timeout",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1",
                "WIKI_HEAVY_PROGRESS_MONITOR": "auto",
                "WIKI_HEAVY_PROGRESS_WINDOW_SECONDS": "1",
                "WIKI_HEAVY_PROGRESS_ALERT_WINDOWS": "2",
                "WIKI_REPO_AWARENESS_TIMEOUT": "0.2s",
            }
        )
        for name, value in (environment_overrides or {}).items():
            if value is None:
                environment.pop(name, None)
            else:
                environment[name] = value
        if command_arguments is None:
            command_arguments = [
                "--timings",
                "--budget-ms=8000",
                "--max-duration=1s",
            ]
        started = time.monotonic()
        invocation = [str(wrapper), str(command), *command_arguments]
        if precreated_lock_state is not None:
            scope = environment["WIKI_HEAVY_LOCK_SCOPE"]
            lock_key = hashlib.sha256(f"scope:{scope}\n".encode()).hexdigest()
            stale_lock_dir = lock_root / f"{lock_key}.lock"
            stale_lock_dir.mkdir(parents=True, mode=0o700)
            current_identity = process_identity(os.getpid())
            if current_identity is None:
                raise AssertionError("cannot pin test process identity")
            if precreated_lock_state == "reused_owner":
                identity_fields = (
                    f"pid:{os.getpid()}",
                    f"pid_start_ticks:{current_identity[0] + 1}",
                )
            elif precreated_lock_state == "matching_owner":
                identity_fields = (
                    f"pid:{os.getpid()}",
                    f"pid_start_ticks:{current_identity[0]}",
                )
            elif precreated_lock_state == "reused_child":
                identity_fields = (
                    "pid:999999999",
                    f"child_pid:{os.getpid()}",
                    f"child_pid_start_ticks:{current_identity[0] + 1}",
                )
            else:
                raise AssertionError(
                    f"unsupported precreated lock state: {precreated_lock_state}"
                )
            stale_lock_dir.joinpath("meta").write_text(
                "\n".join(
                    (
                        *identity_fields,
                        "started_epoch:1",
                        "heartbeat_seconds:1",
                        "heartbeat_stale_seconds:1",
                        f"scope:scope:{scope}",
                        "command:reused-pid-holder",
                        "",
                    )
                )
            )
        if signal_after_seconds is None:
            completed = subprocess.run(
                invocation,
                cwd=TOOLS_DIR.parent,
                env=environment,
                text=True,
                capture_output=True,
                timeout=12,
                check=False,
            )
        else:
            process = subprocess.Popen(
                invocation,
                cwd=TOOLS_DIR.parent,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            child_pid_path = root / "child.pid"
            child_deadline = time.monotonic() + 2
            while not child_pid_path.exists() and time.monotonic() < child_deadline:
                time.sleep(0.01)
            if not child_pid_path.exists():
                process.terminate()
                process.communicate(timeout=3)
                raise AssertionError("supervised child never started")
            time.sleep(signal_after_seconds)
            descendants: dict[int, str] = {}
            observer_deadline = time.monotonic() + 1.5
            while time.monotonic() < observer_deadline:
                descendants = self.descendant_processes(process.pid)
                monitor_seen = any(
                    "check-command-progress" in command
                    for command in descendants.values()
                )
                if monitor_seen:
                    break
                time.sleep(0.01)
            (root / "owned-descendants.json").write_text(
                json.dumps(descendants, sort_keys=True)
            )
            process.send_signal(signal_number)
            stdout, stderr = process.communicate(timeout=5)
            completed = subprocess.CompletedProcess(
                invocation, process.returncode, stdout, stderr
            )
        return completed, root, time.monotonic() - started

    def build_lock_wait_fixture(
        self, root: Path
    ) -> tuple[Path, Path, list[str]]:
        command = root / "lock-worker"
        command.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import os
                import pathlib
                import time

                pathlib.Path(os.environ["LOCK_TEST_PID_FILE"]).write_text(str(os.getpid()))
                time.sleep(float(os.environ.get("LOCK_TEST_SLEEP_SECONDS", "10")))
                """
            )
        )
        command.chmod(0o755)
        pid_file = root / "lock-worker.pid"
        invocation = [
            str(WRAPPER),
            str(command),
            "--timings",
            "--budget-ms=8000",
            "--max-duration=1s",
        ]
        return command, pid_file, invocation

    def lock_wait_environment(
        self,
        *,
        root: Path,
        tmpdir: Path,
        pid_file: Path,
        scope: str,
        explicit_lock_root: Path | None,
    ) -> dict[str, str]:
        environment = os.environ.copy()
        for name in (*FORBIDDEN_PROGRESS_ENV, "WIKI_HEAVY_LOCK_DIR"):
            environment.pop(name, None)
        environment.update(
            {
                "TMPDIR": str(tmpdir),
                "LOCK_TEST_PID_FILE": str(pid_file),
                "LOCK_TEST_SLEEP_SECONDS": "10",
                "WIKI_HEAVY_LOCK_SCOPE": scope,
                "WIKI_HEAVY_LOCK_WAIT_SECONDS": "20",
                "WIKI_HEAVY_LOCK_WAIT_NOTICE_SECONDS": "0",
                "WIKI_HEAVY_LOCK_HEARTBEAT_SECONDS": "1",
                "WIKI_HEAVY_LOCK_HEARTBEAT_STALE_SECONDS": "3",
                "WIKI_HEAVY_TIMEOUT_SECONDS": "8",
                "WIKI_HEAVY_TIMEOUT_KILL_AFTER_SECONDS": "1",
                "WIKI_HEAVY_BUDGET_MS": "8000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": "8000",
                "WIKI_HEAVY_STOP_CONDITION": "fixture_lock_worker_exits_or_timeout",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1",
                "WIKI_HEAVY_PROGRESS_MONITOR": "off",
                "WIKI_REPO_AWARENESS_TIMEOUT": "0.2s",
            }
        )
        if explicit_lock_root is not None:
            environment["WIKI_HEAVY_LOCK_DIR"] = str(explicit_lock_root)
        return environment

    def wait_pid_file(self, path: Path, timeout: float = 5.0) -> int:
        deadline = time.monotonic() + timeout
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(path.exists(), f"worker did not write PID file {path}")
        return int(path.read_text())

    def terminate_wrapper(self, process: subprocess.Popen[str]) -> tuple[str, str]:
        if process.poll() is None:
            process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        return stdout, stderr

    def test_overrun_alerts_without_changing_child_exit_or_leaking_state(self) -> None:
        completed, root, elapsed = self.run_fake(
            # Two complete one-second observations must fit even when process
            # supervisor startup is briefly contended.
            sleep_seconds=4.0, exit_code=7
        )
        self.assertEqual(completed.returncode, 7, completed.stderr)
        self.assertIn("progress_monitor_alert", completed.stderr)
        self.assertIn("action=read_live_artifact_and_fix_root_cause_before_rerun", completed.stderr)
        self.assertNotIn("forbidden_progress_env=", completed.stderr)
        self.assertGreaterEqual(elapsed, 3.8)
        self.assertLess(elapsed, 7.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])
        self.assertEqual(list((root / "tmp").glob("wiki-heavy-supervision.*")), [])

    def test_command_finishing_inside_budget_has_no_alert(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=0.8, exit_code=0
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("progress_monitor_alert", completed.stderr)
        # Keep the bound below the former leaked eight-second timer while
        # allowing deterministic completion under full-CPU concurrent agents.
        self.assertLess(elapsed, 7.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])
        self.assertEqual(list((root / "tmp").glob("wiki-heavy-supervision.*")), [])

    def test_native_supervisor_timeout_returns_124_and_releases_lock(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=10,
            exit_code=0,
            expected_ms=1000,
            environment_overrides={
                "WIKI_HEAVY_TIMEOUT_SECONDS": "1",
                "WIKI_HEAVY_TIMEOUT_KILL_AFTER_SECONDS": "1",
                "WIKI_HEAVY_BUDGET_MS": "1000",
                "WIKI_HEAVY_PROGRESS_MONITOR": "off",
            },
            command_arguments=[
                "--timings",
                "--budget-ms=1000",
                "--max-duration=1s",
            ],
        )
        self.assertEqual(completed.returncode, 124, completed.stderr)
        self.assertGreaterEqual(elapsed, 0.8)
        self.assertLess(elapsed, 4.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])

    def test_gomaxprocs_absent_preserved_and_explicitly_overridden(self) -> None:
        command_program = """\
            #!/usr/bin/env python3
            import os
            print("observed_gomaxprocs=" + os.environ.get("GOMAXPROCS", "<missing>"))
        """
        cases = (
            (
                "absent",
                {"GOMAXPROCS": None, "WIKI_HEAVY_GOMAXPROCS": None},
                "<missing>",
            ),
            (
                "preserved",
                {"GOMAXPROCS": "23", "WIKI_HEAVY_GOMAXPROCS": None},
                "23",
            ),
            (
                "explicit_override",
                {"GOMAXPROCS": "23", "WIKI_HEAVY_GOMAXPROCS": "37"},
                "37",
            ),
        )
        for name, overrides, expected in cases:
            with self.subTest(name=name):
                completed, _root, elapsed = self.run_fake(
                    sleep_seconds=0,
                    exit_code=0,
                    command_program=command_program,
                    environment_overrides={
                        **overrides,
                        "WIKI_HEAVY_PROGRESS_MONITOR": "off",
                    },
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    completed.stdout,
                    f"observed_gomaxprocs={expected}\n",
                )
                self.assertLess(elapsed, 2.0)

    def test_nice_is_neutral_by_default_and_only_changes_by_opt_in(self) -> None:
        command_program = """\
            #!/usr/bin/env python3
            import os
            print("observed_nice=" + str(os.getpriority(os.PRIO_PROCESS, 0)))
        """
        inherited_nice = os.getpriority(os.PRIO_PROCESS, 0)
        observed: dict[str, int] = {}
        for name, configured in (("neutral", None), ("opt_in", "4")):
            with self.subTest(name=name):
                completed, _root, elapsed = self.run_fake(
                    sleep_seconds=0,
                    exit_code=0,
                    command_program=command_program,
                    environment_overrides={
                        "WIKI_HEAVY_NICE": configured,
                        "WIKI_HEAVY_IONICE_CLASS": None,
                        "WIKI_HEAVY_IONICE_LEVEL": None,
                        "WIKI_HEAVY_PROGRESS_MONITOR": "off",
                    },
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                observed[name] = int(completed.stdout.strip().split("=", 1)[1])
                self.assertLess(elapsed, 2.0)
        self.assertEqual(observed["neutral"], inherited_nice)
        self.assertEqual(observed["opt_in"], min(19, inherited_nice + 4))

    def test_stdout_and_stderr_stream_directly_without_fifo_or_tee(self) -> None:
        command_program = """\
            #!/usr/bin/env python3
            import sys
            print("direct-stdout", flush=True)
            print("direct-stderr", file=sys.stderr, flush=True)
        """
        completed, root, elapsed = self.run_fake(
            sleep_seconds=0,
            exit_code=0,
            command_program=command_program,
            environment_overrides={"WIKI_HEAVY_PROGRESS_MONITOR": "off"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "direct-stdout\n")
        self.assertIn("direct-stderr\n", completed.stderr)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(list((root / "tmp").glob("wiki-heavy-supervision.*")), [])
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertNotIn("mkfifo ", source)
        self.assertNotIn("tee -a ", source)

    def test_explicit_contract_enables_watchdog_for_non_go_command(self) -> None:
        completed, _root, _elapsed = self.run_fake(
            sleep_seconds=4.0,
            exit_code=5,
            command_name="python-oss-worker",
            environment_overrides={
                "WIKI_HEAVY_EXPECTED_DURATION_MS": None,
                "WIKI_HEAVY_STOP_CONDITION": (
                    "oss_evidence_written_or_failed_with_missing_dependency"
                ),
            },
        )
        self.assertEqual(completed.returncode, 5, completed.stderr)
        self.assertIn("progress_monitor_alert", completed.stderr)
        self.assertNotIn("reason=no_explicit_heavy_contract", completed.stderr)

    def test_reclaims_reused_owner_pid_without_waiting_on_unrelated_process(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=0,
            exit_code=0,
            environment_overrides={
                "WIKI_HEAVY_LOCK_SCOPE": "reused-owner-pid",
                "WIKI_HEAVY_PROGRESS_MONITOR": "off",
            },
            precreated_lock_state="reused_owner",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("owner_identity=pid_reused", completed.stderr)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])

    def test_reclaims_reused_child_pid_without_waiting_on_unrelated_process(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=0,
            exit_code=0,
            environment_overrides={
                "WIKI_HEAVY_LOCK_SCOPE": "reused-child-pid",
                "WIKI_HEAVY_PROGRESS_MONITOR": "off",
            },
            precreated_lock_state="reused_child",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("child_identity=pid_reused", completed.stderr)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])

    def test_matching_pinned_owner_pid_remains_fail_closed(self) -> None:
        completed, _root, elapsed = self.run_fake(
            sleep_seconds=0,
            exit_code=0,
            environment_overrides={
                "WIKI_HEAVY_LOCK_SCOPE": "matching-owner-pid",
                "WIKI_HEAVY_PROGRESS_MONITOR": "off",
            },
            precreated_lock_state="matching_owner",
        )
        self.assertEqual(completed.returncode, 75, completed.stderr)
        self.assertIn("analise_comando_ativo", completed.stderr)
        self.assertNotIn("reclaimed stale heavy lock", completed.stderr)
        self.assertLess(elapsed, 2.0)

    def test_empty_success_from_monitor_is_fail_closed_but_child_continues(self) -> None:
        completed, _root, elapsed = self.run_fake(
            sleep_seconds=1.2,
            exit_code=6,
            monitor_program="#!/bin/sh\nexit 0\n",
        )
        self.assertEqual(completed.returncode, 6, completed.stderr)
        self.assertIn("status=monitor_failure", completed.stderr)
        self.assertIn("reason=invalid_or_missing_schema", completed.stderr)
        self.assertGreaterEqual(elapsed, 1.1)
        self.assertLess(elapsed, 7.0)

    def test_malformed_contract_values_do_not_enable_or_pass_heavy_lane(self) -> None:
        cases = (
            (
                "budget_duration_instead_of_ms",
                {"WIKI_HEAVY_BUDGET_MS": None},
                ["--timings", "--budget-ms", "5s", "--max-duration=1s"],
                "budget_ms",
            ),
            (
                "missing_duration_number",
                {"WIKI_HEAVY_EXPECTED_DURATION_MS": None},
                ["--timings", "--budget-ms=8000", "--max-duration=ms"],
                "expected_duration_ms",
            ),
            (
                "zero_duration",
                {"WIKI_HEAVY_EXPECTED_DURATION_MS": None},
                ["--timings", "--budget-ms=8000", "--max-duration=00s"],
                "expected_duration_ms",
            ),
            (
                "garbage_throughput",
                {"WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=0garbage"},
                ["--timings", "--budget-ms=8000", "--max-duration=1s"],
                "throughput_expected",
            ),
            (
                "placeholder_stop",
                {"WIKI_HEAVY_STOP_CONDITION": "placeholder_later"},
                ["--timings", "--budget-ms=8000", "--max-duration=1s"],
                "stop_condition",
            ),
            (
                "progress_alert_window_above_watchdog_bound",
                {"WIKI_HEAVY_PROGRESS_ALERT_WINDOWS": "1000001"},
                ["--timings", "--budget-ms=8000", "--max-duration=1s"],
                "must not exceed 1000000",
            ),
        )
        for name, overrides, arguments, expected_error in cases:
            with self.subTest(name=name):
                completed, _root, elapsed = self.run_fake(
                    sleep_seconds=0,
                    exit_code=0,
                    environment_overrides=overrides,
                    command_arguments=arguments,
                )
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn(expected_error, completed.stderr)
                self.assertLess(elapsed, 1.5)

    def test_expected_duration_cannot_exceed_effective_timeout(self) -> None:
        completed, _root, elapsed = self.run_fake(
            sleep_seconds=0,
            exit_code=0,
            expected_ms=3000,
            environment_overrides={
                "WIKI_HEAVY_TIMEOUT_SECONDS": "2",
                "WIKI_HEAVY_BUDGET_MS": "2000",
            },
            command_arguments=[
                "--timings",
                "--budget-ms=2000",
                "--max-duration=3s",
            ],
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn(
            "expected duration must not exceed effective command timeout (2000ms)",
            completed.stderr,
        )
        self.assertLess(elapsed, 1.5)

    def test_maximum_timeout_keeps_helper_deadlines_within_native_bound(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=0.2,
            exit_code=0,
            environment_overrides={
                "WIKI_HEAVY_TIMEOUT_SECONDS": "86400",
                "WIKI_HEAVY_BUDGET_MS": "86400000",
            },
            command_arguments=[
                "--timings",
                "--budget-ms=86400000",
                "--max-duration=1s",
            ],
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("must be between 0 and 86400", completed.stderr)
        self.assertNotIn("must be between 0 and 300", completed.stderr)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])

    def test_term_cleans_only_owned_watchdog_and_child_without_tee_or_fifo(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=10,
            exit_code=0,
            signal_after_seconds=0.05,
        )
        self.assertEqual(completed.returncode, 143, completed.stderr)
        self.assertLess(elapsed, 3.0)
        self.assertEqual(list((root / "locks").glob("**/*")), [])
        self.assertEqual(list((root / "tmp").glob("wiki-heavy-supervision.*")), [])
        child_pid = int((root / "child.pid").read_text())
        descendants = {
            int(pid): command
            for pid, command in json.loads(
                (root / "owned-descendants.json").read_text()
            ).items()
        }
        self.assertIn(child_pid, descendants)
        self.assertFalse(any("tee" in command for command in descendants.values()))
        self.assertTrue(
            any("check-command-progress" in command for command in descendants.values()),
            descendants,
        )
        for owned_pid in descendants:
            with self.subTest(owned_pid=owned_pid):
                with self.assertRaises(ProcessLookupError):
                    os.kill(owned_pid, 0)

    def test_sigquit_is_forwarded_as_shell_status_131(self) -> None:
        completed, root, elapsed = self.run_fake(
            sleep_seconds=10,
            exit_code=0,
            signal_after_seconds=0.05,
            signal_number=signal.SIGQUIT,
        )
        self.assertEqual(completed.returncode, 131, completed.stderr)
        self.assertLess(elapsed, 3.5)
        self.assertEqual(list((root / "locks").glob("**/*")), [])
        child_pid = int((root / "child.pid").read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)

    def test_term_is_bounded_when_progress_monitor_ignores_term(self) -> None:
        monitor_program = textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import signal
            import time

            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            while True:
                time.sleep(1)
            """
        )
        completed, root, elapsed = self.run_fake(
            sleep_seconds=10,
            exit_code=0,
            monitor_program=monitor_program,
            signal_after_seconds=0.05,
        )
        self.assertEqual(completed.returncode, 143, completed.stderr)
        self.assertLess(elapsed, 4.5)
        self.assertEqual(list((root / "locks").glob("**/*")), [])
        self.assertEqual(list((root / "tmp").glob("wiki-heavy-supervision.*")), [])

    def test_default_lock_domain_is_shared_across_different_tmpdirs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tmp_a = root / "tmp-a"
            tmp_b = root / "tmp-b"
            tmp_a.mkdir()
            tmp_b.mkdir()
            _command, pid_file, invocation = self.build_lock_wait_fixture(root)
            scope = f"test-default-lock-{os.getpid()}-{time.monotonic_ns()}"
            first_environment = self.lock_wait_environment(
                root=root,
                tmpdir=tmp_a,
                pid_file=pid_file,
                scope=scope,
                explicit_lock_root=None,
            )
            first = subprocess.Popen(
                invocation,
                cwd=TOOLS_DIR.parent,
                env=first_environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                self.wait_pid_file(pid_file)
                second_environment = self.lock_wait_environment(
                    root=root,
                    tmpdir=tmp_b,
                    pid_file=pid_file,
                    scope=scope,
                    explicit_lock_root=None,
                )
                second_environment["WIKI_HEAVY_WAIT_CLASSIFICATION"] = (
                    "non_critical_wait"
                )
                started = time.monotonic()
                second = subprocess.run(
                    invocation,
                    cwd=TOOLS_DIR.parent,
                    env=second_environment,
                    text=True,
                    capture_output=True,
                    timeout=4,
                    check=False,
                )
                self.assertEqual(second.returncode, 75, second.stderr)
                self.assertIn("non_critical_wait forbids passive lock sleep", second.stderr)
                self.assertLess(time.monotonic() - started, 2.5)
            finally:
                stdout, stderr = self.terminate_wrapper(first)
            self.assertEqual(first.returncode, 143, stdout + stderr)

    def test_critical_dependency_wait_timeout_overrides_long_global_wait(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tmp_a = root / "tmp-a"
            tmp_b = root / "tmp-b"
            lock_root = root / "locks"
            tmp_a.mkdir()
            tmp_b.mkdir()
            _command, pid_file, invocation = self.build_lock_wait_fixture(root)
            scope = f"test-critical-wait-{os.getpid()}-{time.monotonic_ns()}"
            first_environment = self.lock_wait_environment(
                root=root,
                tmpdir=tmp_a,
                pid_file=pid_file,
                scope=scope,
                explicit_lock_root=lock_root,
            )
            first = subprocess.Popen(
                invocation,
                cwd=TOOLS_DIR.parent,
                env=first_environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                self.wait_pid_file(pid_file)
                second_environment = self.lock_wait_environment(
                    root=root,
                    tmpdir=tmp_b,
                    pid_file=pid_file,
                    scope=scope,
                    explicit_lock_root=lock_root,
                )
                second_environment.update(
                    {
                        "WIKI_HEAVY_WAIT_CLASSIFICATION": "critical_dependency",
                        "WIKI_HEAVY_DEPENDENCY_ID": "fixture-active-owner",
                        "WIKI_HEAVY_OWNER_PID": str(first.pid),
                        "WIKI_HEAVY_WAIT_TIMEOUT_MS": "250",
                        "WIKI_HEAVY_LAST_EVIDENCE": "fixture-owner-meta-read",
                        "WIKI_HEAVY_REORIENTATION_COMMAND": "true",
                    }
                )
                started = time.monotonic()
                second = subprocess.run(
                    invocation,
                    cwd=TOOLS_DIR.parent,
                    env=second_environment,
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                elapsed = time.monotonic() - started
                self.assertEqual(second.returncode, 75, second.stderr)
                self.assertIn("blocked after 1s", second.stderr)
                self.assertLess(elapsed, 4.5)
            finally:
                stdout, stderr = self.terminate_wrapper(first)
            self.assertEqual(first.returncode, 143, stdout + stderr)

    def test_sigkill_wrapper_releases_fd8_after_all_helpers_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            marker = root / "fd8-command.json"
            flock_path = root / "factory.lock"
            command = root / "fd8-worker"
            command.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import errno
                    import json
                    import os
                    import pathlib
                    import time

                    closed = False
                    try:
                        os.fstat(8)
                    except OSError as exc:
                        closed = exc.errno == errno.EBADF
                    raw = pathlib.Path("/proc/self/stat").read_text()
                    start_ticks = int(raw[raw.rfind(")") + 2:].split()[19])
                    pathlib.Path(os.environ["FD8_TEST_MARKER"]).write_text(json.dumps({
                        "pid": os.getpid(),
                        "start_ticks": start_ticks,
                        "fd8_closed": closed,
                    }))
                    time.sleep(10)
                    """
                )
            )
            command.chmod(0o755)
            environment = self.lock_wait_environment(
                root=root,
                tmpdir=temporary_root,
                pid_file=root / "unused.pid",
                scope=f"test-fd8-sigkill-{os.getpid()}-{time.monotonic_ns()}",
                explicit_lock_root=root / "run-heavy-locks",
            )
            environment.update(
                {
                    "FD8_TEST_MARKER": str(marker),
                    "WIKI_HEAVY_PROGRESS_MONITOR": "auto",
                    "WIKI_HEAVY_PROGRESS_WINDOW_SECONDS": "1",
                }
            )
            invocation = [
                "bash",
                "-c",
                'exec 8>"$1"; flock -n 8 || exit 90; shift; exec "$@"',
                "run-heavy-fd8-launcher",
                str(flock_path),
                str(WRAPPER),
                str(command),
                "--timings",
                "--budget-ms=8000",
                "--max-duration=1s",
            ]
            process = subprocess.Popen(
                invocation,
                cwd=TOOLS_DIR.parent,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                deadline = time.monotonic() + 2
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(), "fd8 command never started")
                command_identity = json.loads(marker.read_text())
                self.assertTrue(command_identity["fd8_closed"], command_identity)
                descendants = self.descendant_processes(process.pid)
                identities = {
                    pid: identity
                    for pid in descendants
                    if (identity := process_identity(pid)) is not None
                }
                contender = subprocess.run(
                    ["flock", "-n", str(flock_path), "-c", "true"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False,
                )
                self.assertNotEqual(contender.returncode, 0)

                process.kill()
                process.wait(timeout=1)
                self.assertEqual(process.returncode, -signal.SIGKILL)

                release_deadline = time.monotonic() + 4
                while time.monotonic() < release_deadline:
                    contender = subprocess.run(
                        ["flock", "-n", str(flock_path), "-c", "true"],
                        capture_output=True,
                        text=True,
                        timeout=1,
                        check=False,
                    )
                    live_helpers = {
                        pid: identity
                        for pid, identity in identities.items()
                        if identity_is_running(pid, identity[0])
                    }
                    command_running = identity_is_running(
                        int(command_identity["pid"]),
                        int(command_identity["start_ticks"]),
                    )
                    if (
                        contender.returncode == 0
                        and not live_helpers
                        and not command_running
                    ):
                        break
                    time.sleep(0.02)
                self.assertEqual(contender.returncode, 0, contender.stderr)
                for pid, (start_ticks, _state) in identities.items():
                    self.assertFalse(
                        identity_is_running(pid, start_ticks),
                        f"helper survived wrapper SIGKILL: pid={pid}",
                    )
                self.assertFalse(
                    identity_is_running(
                        int(command_identity["pid"]),
                        int(command_identity["start_ticks"]),
                    ),
                    command_identity,
                )
                try:
                    stdout, stderr = process.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    live_helpers = {
                        pid: identity
                        for pid, identity in identities.items()
                        if identity_is_running(pid, identity[0])
                    }
                    if process.stdout is not None:
                        process.stdout.close()
                    if process.stderr is not None:
                        process.stderr.close()
                    self.fail(
                        "wrapper SIGKILL left inherited output descriptors open; "
                        f"live_helpers={live_helpers} flock_rc={contender.returncode}"
                    )
                self.assertEqual(process.returncode, -signal.SIGKILL, stdout + stderr)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=1)
                if process.stdout is not None and not process.stdout.closed:
                    process.stdout.close()
                if process.stderr is not None and not process.stderr.closed:
                    process.stderr.close()

    def test_abandoned_detached_daemon_cannot_turn_leader_zero_green(self) -> None:
        command_program = """\
            #!/usr/bin/env python3
            import json
            import os
            import pathlib
            import signal
            import time

            marker = pathlib.Path(os.environ["FAKE_HEAVY_PID_FILE"])
            child = os.fork()
            if child == 0:
                os.setsid()
                daemon = os.fork()
                if daemon > 0:
                    os._exit(0)
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                raw = pathlib.Path("/proc/self/stat").read_text()
                start_ticks = int(raw[raw.rfind(")") + 2:].split()[19])
                marker.write_text(json.dumps({"pid": os.getpid(), "start_ticks": start_ticks}))
                while True:
                    time.sleep(1)
            os.waitpid(child, 0)
            deadline = time.monotonic() + 1
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            raise SystemExit(0)
        """
        completed, root, elapsed = self.run_fake(
            sleep_seconds=0,
            exit_code=0,
            command_program=command_program,
            environment_overrides={"WIKI_HEAVY_PROGRESS_MONITOR": "off"},
        )
        self.assertEqual(completed.returncode, 125, completed.stderr)
        self.assertIn("event=descendant_cleanup_after_leader_exit", completed.stderr)
        self.assertLess(elapsed, 8.0)
        identity = json.loads((root / "child.pid").read_text())
        proc_stat = Path(f"/proc/{identity['pid']}/stat")
        if proc_stat.exists():
            raw = proc_stat.read_text()
            current_start_ticks = int(raw[raw.rfind(")") + 2:].split()[19])
            self.assertNotEqual(current_start_ticks, identity["start_ticks"])


if __name__ == "__main__":
    unittest.main()
