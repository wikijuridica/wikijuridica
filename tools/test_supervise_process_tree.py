#!/usr/bin/env python3
"""Focused adversarial tests for supervise-process-tree."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
TOOL = TOOLS_DIR / "supervise-process-tree"


def process_identity(pid: int) -> tuple[int, str] | None:
    try:
        payload = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError):
        return None
    close_paren = payload.rfind(")")
    fields = payload[close_paren + 2 :].split()
    return int(fields[19]), fields[0]


def identity_is_running(pid: int, start_ticks: int) -> bool:
    identity = process_identity(pid)
    return identity is not None and identity[0] == start_ticks and identity[1] != "Z"


def wait_identity_stopped(pid: int, start_ticks: int, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not identity_is_running(pid, start_ticks):
            return True
        time.sleep(0.01)
    return not identity_is_running(pid, start_ticks)


def signal_identity(pid: int, start_ticks: int, signal_number: int) -> None:
    pidfd = os.pidfd_open(pid, 0)
    try:
        current = process_identity(pid)
        if current is None or current[0] != start_ticks:
            raise RuntimeError(f"process identity changed before signal: {pid}")
        signal.pidfd_send_signal(pidfd, signal_number, None, 0)
    finally:
        os.close(pidfd)


class ProcessTreeSupervisorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.processes: list[subprocess.Popen[str]] = []
        self.identities: list[tuple[int, int]] = []

    def tearDown(self) -> None:
        for process in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=0.5)
        for pid, start_ticks in self.identities:
            if identity_is_running(pid, start_ticks):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def run_tool(self, *arguments: str, timeout: float = 3.0) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )

    def wait_json_file(self, path: Path, timeout: float = 2.0) -> dict[str, int]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                payload = json.loads(path.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(0.01)
                continue
            return {key: int(value) for key, value in payload.items()}
        self.fail(f"timed out waiting for {path}")

    def wait_direct_child(self, parent_pid: int, timeout: float = 2.0) -> dict[str, int]:
        children_path = Path(f"/proc/{parent_pid}/task/{parent_pid}/children")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                children = [int(raw) for raw in children_path.read_text().split()]
            except (FileNotFoundError, ProcessLookupError):
                children = []
            if len(children) == 1:
                identity = process_identity(children[0])
                if identity is not None:
                    return {"pid": children[0], "start_ticks": identity[0]}
            time.sleep(0.01)
        self.fail(f"timed out waiting for sole child of {parent_pid}")

    def test_direct_exec_ignores_python3_injected_by_path(self) -> None:
        # 2026-09-24, torre: o drop-in 20-python.conf pos um CPython sem pidfd na
        # frente do PATH, e com `#!/usr/bin/env python3` o guardiao morria com
        # exit 125. run-heavy-throttled o executa DIRETO (pelo shebang), entao
        # este teste tambem: um python3 falso no PATH que sai 99 nao pode ser o
        # interpretador do guardiao.
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "python3"
            fake.write_text("#!/bin/sh\nexit 99\n")
            fake.chmod(0o755)
            completed = subprocess.run(
                [str(TOOL), "--", "/bin/sh", "-c", "exit 7"],
                text=True,
                capture_output=True,
                check=False,
                timeout=3.0,
                env={**os.environ, "PATH": f"{temp}:/usr/bin:/bin"},
            )
        self.assertEqual(completed.returncode, 7, completed.stderr)

    def test_preserves_output_and_normal_exit_status(self) -> None:
        completed = self.run_tool(
            "--",
            sys.executable,
            "-c",
            "import sys; print('out'); print('err', file=sys.stderr); sys.exit(7)",
        )
        self.assertEqual(completed.returncode, 7, completed.stderr)
        self.assertEqual(completed.stdout, "out\n")
        self.assertEqual(completed.stderr, "err\n")

    def test_reports_shell_status_when_leader_dies_by_signal(self) -> None:
        completed = self.run_tool(
            "--",
            sys.executable,
            "-c",
            "import os,signal; os.kill(os.getpid(), signal.SIGTERM)",
        )
        self.assertEqual(completed.returncode, 128 + signal.SIGTERM, completed.stderr)

    def test_inherited_ignored_sigchld_does_not_discard_leader_status(self) -> None:
        launcher = (
            "import os,signal,sys\n"
            "signal.signal(signal.SIGCHLD, signal.SIG_IGN)\n"
            "os.execv(sys.argv[1], sys.argv[1:])\n"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                launcher,
                sys.executable,
                str(TOOL),
                "--",
                sys.executable,
                "-c",
                "raise SystemExit(7)",
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=3,
        )
        self.assertEqual(completed.returncode, 7, completed.stderr)

    def test_close_fd8_only_in_producer_branch(self) -> None:
        probe = (
            "import errno,os,sys\n"
            "try:\n os.fstat(8)\nexcept OSError as exc:\n"
            " sys.exit(0 if exc.errno == errno.EBADF else 4)\n"
            "sys.exit(9)\n"
        )
        command = [
            "bash",
            "-c",
            'exec 8</dev/null; exec "$@"',
            "bash",
            sys.executable,
            str(TOOL),
            "--close-fd8",
            "--",
            sys.executable,
            "-c",
            probe,
        ]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=3)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        command.remove("--close-fd8")
        completed = subprocess.run(command, text=True, capture_output=True, timeout=3)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        separator_index = command.index("--")
        command[separator_index:separator_index] = ["--pass-fd", "8"]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=3)
        self.assertEqual(completed.returncode, 9, completed.stderr)

    def test_normal_exit_reaps_double_fork_setsid_daemon_ignoring_term(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "daemon.json"
            program = r'''
import json,os,pathlib,signal,sys,time
marker=pathlib.Path(sys.argv[1])
child=os.fork()
if child == 0:
    os.setsid()
    daemon=os.fork()
    if daemon > 0:
        os._exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raw=pathlib.Path('/proc/self/stat').read_text()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
    while True:
        time.sleep(1)
os.waitpid(child, 0)
deadline=time.monotonic()+1
while not marker.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
sys.exit(17)
'''
            completed = self.run_tool(
                "--term-grace-seconds",
                "0.05",
                "--kill-grace-seconds",
                "0.5",
                "--",
                sys.executable,
                "-c",
                program,
                str(marker),
            )
            daemon = self.wait_json_file(marker)
            self.identities.append((daemon["pid"], daemon["start_ticks"]))
            self.assertEqual(completed.returncode, 17, completed.stderr)
            self.assertTrue(
                wait_identity_stopped(daemon["pid"], daemon["start_ticks"]),
                "detached daemon survived normal leader exit",
            )

    def test_strict_cleanup_rejects_green_leader_that_abandons_daemon(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "daemon.json"
            program = r'''
import json,os,pathlib,signal,sys,time
marker=pathlib.Path(sys.argv[1])
child=os.fork()
if child == 0:
    os.setsid()
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raw=pathlib.Path('/proc/self/stat').read_text()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
    while True:
        time.sleep(1)
deadline=time.monotonic()+1
while not marker.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
sys.exit(0)
'''
            completed = self.run_tool(
                "--fail-on-descendant-cleanup",
                "--term-grace-seconds",
                "0.02",
                "--kill-grace-seconds",
                "0.5",
                "--",
                sys.executable,
                "-c",
                program,
                str(marker),
            )
            daemon = self.wait_json_file(marker)
            self.identities.append((daemon["pid"], daemon["start_ticks"]))
            self.assertEqual(completed.returncode, 125, completed.stderr)
            self.assertIn("event=descendant_cleanup_after_leader_exit", completed.stderr)
            self.assertTrue(
                wait_identity_stopped(daemon["pid"], daemon["start_ticks"]),
                "strict cleanup reported failure but left daemon alive",
            )

    def test_teardown_race_orphan_dying_alone_keeps_leader_green(self) -> None:
        # Wrapper aninhado: o líder sai verde enquanto um utilitário seu (o
        # sleep do heartbeat de um wrapper interno) ainda vive por instantes e
        # é adotado pelo subreaper. Morte ESPONTÂNEA dentro do grace de
        # teardown não é abandono — o exit verde do líder deve prevalecer.
        program = r'''
import os,sys,time
child=os.fork()
if child == 0:
    time.sleep(0.4)
    os._exit(0)
sys.exit(0)
'''
        completed = self.run_tool(
            "--fail-on-descendant-cleanup",
            "--",
            sys.executable,
            "-c",
            program,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("event=descendant_teardown_race_resolved", completed.stderr)
        self.assertNotIn(
            "event=descendant_cleanup_after_leader_exit", completed.stderr
        )

    def test_teardown_race_grace_zero_restores_strict_failure(self) -> None:
        program = r'''
import os,sys,time
child=os.fork()
if child == 0:
    time.sleep(0.4)
    os._exit(0)
sys.exit(0)
'''
        completed = self.run_tool(
            "--fail-on-descendant-cleanup",
            "--teardown-race-grace-seconds",
            "0",
            "--",
            sys.executable,
            "-c",
            program,
        )
        self.assertEqual(completed.returncode, 125, completed.stderr)
        self.assertIn("event=descendant_cleanup_after_leader_exit", completed.stderr)

    def test_term_supervisor_boundedly_reaps_ignoring_leader_and_daemon(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            leader_marker = Path(directory) / "leader.json"
            daemon_marker = Path(directory) / "daemon.json"
            program = r'''
import json,os,pathlib,signal,sys,time
leader_marker=pathlib.Path(sys.argv[1]); daemon_marker=pathlib.Path(sys.argv[2])
signal.signal(signal.SIGTERM, signal.SIG_IGN)
raw=pathlib.Path('/proc/self/stat').read_text()
start=int(raw[raw.rfind(')')+2:].split()[19])
leader_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
child=os.fork()
if child == 0:
    os.setsid()
    daemon=os.fork()
    if daemon > 0:
        os._exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raw=pathlib.Path('/proc/self/stat').read_text()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    daemon_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
    while True:
        time.sleep(1)
os.waitpid(child, 0)
while True:
    time.sleep(1)
'''
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(TOOL),
                    "--term-grace-seconds",
                    "0.05",
                    "--kill-grace-seconds",
                    "0.5",
                    "--",
                    sys.executable,
                    "-c",
                    program,
                    str(leader_marker),
                    str(daemon_marker),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.processes.append(process)
            leader = self.wait_json_file(leader_marker)
            daemon = self.wait_json_file(daemon_marker)
            self.identities.extend(
                [
                    (leader["pid"], leader["start_ticks"]),
                    (daemon["pid"], daemon["start_ticks"]),
                ]
            )
            started = time.monotonic()
            process.terminate()
            stdout, stderr = process.communicate(timeout=2)
            elapsed = time.monotonic() - started
            self.assertEqual(stdout, "")
            self.assertEqual(process.returncode, 128 + signal.SIGTERM, stderr)
            self.assertLess(elapsed, 1.5)
            for identity in (leader, daemon):
                self.assertTrue(
                    wait_identity_stopped(identity["pid"], identity["start_ticks"]),
                    f"process survived cleanup: {identity}",
                )

    def test_sigkill_guardian_leaves_supervisor_to_reap_detached_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            leader_marker = Path(directory) / "leader.json"
            daemon_marker = Path(directory) / "daemon.json"
            program = r'''
import json,os,pathlib,signal,sys,time
leader_marker=pathlib.Path(sys.argv[1]); daemon_marker=pathlib.Path(sys.argv[2])
signal.signal(signal.SIGTERM, signal.SIG_IGN)
raw=pathlib.Path('/proc/self/stat').read_text()
start=int(raw[raw.rfind(')')+2:].split()[19])
leader_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
child=os.fork()
if child == 0:
    os.setsid()
    daemon=os.fork()
    if daemon > 0:
        os._exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raw=pathlib.Path('/proc/self/stat').read_text()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    daemon_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
    while True:
        time.sleep(1)
os.waitpid(child, 0)
while True:
    time.sleep(1)
'''
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(TOOL),
                    "--term-grace-seconds",
                    "0.05",
                    "--kill-grace-seconds",
                    "0.5",
                    "--",
                    sys.executable,
                    "-c",
                    program,
                    str(leader_marker),
                    str(daemon_marker),
                ],
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.processes.append(process)
            leader = self.wait_json_file(leader_marker)
            daemon = self.wait_json_file(daemon_marker)
            self.identities.extend(
                [
                    (leader["pid"], leader["start_ticks"]),
                    (daemon["pid"], daemon["start_ticks"]),
                ]
            )
            process.kill()
            process.wait(timeout=1)
            for identity in (leader, daemon):
                self.assertTrue(
                    wait_identity_stopped(
                        identity["pid"], identity["start_ticks"], timeout=2
                    ),
                    f"tree member survived guardian SIGKILL: {identity}",
                )

    def test_native_timeout_returns_124_and_reaps_ignoring_leader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "leader.json"
            program = r'''
import json,os,pathlib,signal,sys,time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
raw=pathlib.Path('/proc/self/stat').read_text()
start=int(raw[raw.rfind(')')+2:].split()[19])
pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
while True:
    time.sleep(1)
'''
            started = time.monotonic()
            # --timeout-seconds must outlast a real leader boot, not just the
            # guardian/supervisor fork chain in front of it. The leader here is
            # exec'd (a fresh CPython, not a cheap fork of an already-imported
            # one): measured on this host, plain `sys.executable -c <this
            # program>` takes 40-55ms fork-to-marker-write before the
            # supervisor's own guardian+supervisor forks, setsid, prctl and
            # procfs verification even run. 0.05s left no margin, so the
            # deadline fired and killed the leader mid-boot, before it reached
            # the write_text call -- wait_json_file then timed out on a file
            # that was never going to appear. 0.35s leaves ~6x that measured
            # ceiling; total wall time still lands around 0.5s, comfortably
            # under the 1.5s bound asserted below.
            completed = self.run_tool(
                "--timeout-seconds",
                "0.35",
                "--kill-after-seconds",
                "0.2",
                "--term-grace-seconds",
                "0.02",
                "--kill-grace-seconds",
                "0.5",
                "--",
                sys.executable,
                "-c",
                program,
                str(marker),
            )
            leader = self.wait_json_file(marker)
            self.identities.append((leader["pid"], leader["start_ticks"]))
            self.assertEqual(completed.returncode, 124, completed.stderr)
            self.assertLess(time.monotonic() - started, 1.5)
            self.assertTrue(
                wait_identity_stopped(leader["pid"], leader["start_ticks"]),
                "leader survived native timeout cleanup",
            )

    def test_sigkill_inner_supervisor_is_recovered_by_guardian(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            leader_marker = Path(directory) / "leader.json"
            daemon_marker = Path(directory) / "daemon.json"
            program = r'''
import json,os,pathlib,signal,sys,time
leader_marker=pathlib.Path(sys.argv[1]); daemon_marker=pathlib.Path(sys.argv[2])
signal.signal(signal.SIGTERM, signal.SIG_IGN)
raw=pathlib.Path('/proc/self/stat').read_text()
start=int(raw[raw.rfind(')')+2:].split()[19])
leader_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
child=os.fork()
if child == 0:
    os.setsid()
    daemon=os.fork()
    if daemon > 0:
        os._exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raw=pathlib.Path('/proc/self/stat').read_text()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    daemon_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
    while True:
        time.sleep(1)
os.waitpid(child, 0)
while True:
    time.sleep(1)
'''
            guardian = subprocess.Popen(
                [
                    sys.executable,
                    str(TOOL),
                    "--term-grace-seconds",
                    "0.05",
                    "--kill-grace-seconds",
                    "0.5",
                    "--",
                    sys.executable,
                    "-c",
                    program,
                    str(leader_marker),
                    str(daemon_marker),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.processes.append(guardian)
            supervisor = self.wait_direct_child(guardian.pid)
            leader = self.wait_json_file(leader_marker)
            daemon = self.wait_json_file(daemon_marker)
            self.identities.extend(
                [
                    (supervisor["pid"], supervisor["start_ticks"]),
                    (leader["pid"], leader["start_ticks"]),
                    (daemon["pid"], daemon["start_ticks"]),
                ]
            )
            signal_identity(
                supervisor["pid"], supervisor["start_ticks"], signal.SIGKILL
            )
            stdout, stderr = guardian.communicate(timeout=2)
            self.assertEqual(stdout, "")
            self.assertEqual(guardian.returncode, 128 + signal.SIGKILL, stderr)
            for identity in (leader, daemon):
                self.assertTrue(
                    wait_identity_stopped(identity["pid"], identity["start_ticks"]),
                    f"guardian did not recover descendant: {identity}",
                )

    def test_sigkill_invoker_triggers_guardian_pdeath_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            guardian_marker = root / "guardian.json"
            leader_marker = root / "leader.json"
            daemon_marker = root / "daemon.json"
            target = r'''
import json,os,pathlib,signal,sys,time
leader_marker=pathlib.Path(sys.argv[1]); daemon_marker=pathlib.Path(sys.argv[2])
signal.signal(signal.SIGTERM, signal.SIG_IGN)
raw=pathlib.Path('/proc/self/stat').read_text()
start=int(raw[raw.rfind(')')+2:].split()[19])
leader_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
child=os.fork()
if child == 0:
    os.setsid()
    daemon=os.fork()
    if daemon > 0:
        os._exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raw=pathlib.Path('/proc/self/stat').read_text()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    daemon_marker.write_text(json.dumps({'pid':os.getpid(),'start_ticks':start}))
    while True:
        time.sleep(1)
os.waitpid(child, 0)
while True:
    time.sleep(1)
'''
            launcher = r'''
import json,os,pathlib,subprocess,sys,time
process=subprocess.Popen(sys.argv[2:], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
raw=pathlib.Path(f'/proc/{process.pid}/stat').read_text()
start=int(raw[raw.rfind(')')+2:].split()[19])
pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid':process.pid,'start_ticks':start}))
while True:
    time.sleep(1)
'''
            invoker = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    launcher,
                    str(guardian_marker),
                    sys.executable,
                    str(TOOL),
                    "--term-grace-seconds",
                    "0.05",
                    "--kill-grace-seconds",
                    "0.5",
                    "--",
                    sys.executable,
                    "-c",
                    target,
                    str(leader_marker),
                    str(daemon_marker),
                ],
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.processes.append(invoker)
            guardian = self.wait_json_file(guardian_marker)
            leader = self.wait_json_file(leader_marker)
            daemon = self.wait_json_file(daemon_marker)
            self.identities.extend(
                [
                    (guardian["pid"], guardian["start_ticks"]),
                    (leader["pid"], leader["start_ticks"]),
                    (daemon["pid"], daemon["start_ticks"]),
                ]
            )
            invoker.kill()
            invoker.wait(timeout=1)
            for identity in (guardian, leader, daemon):
                self.assertTrue(
                    wait_identity_stopped(
                        identity["pid"], identity["start_ticks"], timeout=2
                    ),
                    f"process survived invoker SIGKILL: {identity}",
                )

    def test_missing_command_and_version_are_versioned(self) -> None:
        completed = self.run_tool("--", "/definitely/missing/wiki-command")
        self.assertEqual(completed.returncode, 127)
        self.assertIn("command not found", completed.stderr)

        completed = self.run_tool("--version")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout.strip(), "process-tree-supervisor/v2")

    def test_rejects_effectively_unbounded_cleanup_deadline(self) -> None:
        started = time.monotonic()
        completed = self.run_tool(
            "--term-grace-seconds",
            "1e300",
            "--",
            sys.executable,
            "-c",
            "pass",
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("between 0 and 300 seconds", completed.stderr)
        self.assertLess(time.monotonic() - started, 1)


if __name__ == "__main__":
    unittest.main()
