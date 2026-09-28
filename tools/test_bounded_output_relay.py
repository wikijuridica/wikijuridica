#!/usr/bin/env python3
"""Focused tests for the bounded binary output relay."""

from __future__ import annotations

import os
from pathlib import Path
import select
import subprocess
import tempfile
import time
import unittest


TOOLS_DIR = Path(__file__).resolve().parent
RELAY = TOOLS_DIR / "bounded-output-relay"


class BoundedOutputRelayTest(unittest.TestCase):
    def run_relay(
        self,
        tail_path: Path,
        payload: bytes,
        *,
        tail_bytes: int = 4096,
        target_fd: int = 1,
        timeout: float = 5,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [
                str(RELAY),
                "--tail-file",
                str(tail_path),
                "--tail-bytes",
                str(tail_bytes),
                "--target-fd",
                str(target_fd),
            ],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )

    def test_streams_all_stdout_and_persists_only_chronological_tail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tail_path = Path(directory) / "stdout.tail"
            payload = bytes(range(256)) * 97
            completed = self.run_relay(tail_path, payload, tail_bytes=1003)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, payload)
            self.assertEqual(completed.stderr, b"")
            self.assertEqual(tail_path.read_bytes(), payload[-1003:])
            self.assertEqual(tail_path.stat().st_mode & 0o777, 0o600)

    def test_can_stream_to_stderr_without_text_decoding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tail_path = Path(directory) / "stderr.tail"
            payload = b"\x00\xffbinary\n" * 700
            completed = self.run_relay(
                tail_path,
                payload,
                tail_bytes=2048,
                target_fd=2,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(completed.stdout, b"")
            self.assertEqual(completed.stderr, payload)
            self.assertEqual(tail_path.read_bytes(), payload[-2048:])

    def test_closed_consumer_still_drains_stdin_and_persists_tail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tail_path = Path(directory) / "closed.tail"
            payload = b"closed-consumer-" * (1024 * 128)
            with tempfile.TemporaryFile() as source:
                source.write(payload)
                source.seek(0)
                process = subprocess.Popen(
                    [
                        str(RELAY),
                        "--tail-file",
                        str(tail_path),
                        "--tail-bytes",
                        "8192",
                    ],
                    stdin=source,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                assert process.stdout is not None
                process.stdout.close()
                status = process.wait(timeout=5)
                assert process.stderr is not None
                diagnostic = process.stderr.read()
                process.stderr.close()
            self.assertEqual(status, 74, diagnostic)
            self.assertIn(b"stdin was drained", diagnostic)
            self.assertEqual(tail_path.read_bytes(), payload[-8192:])

    def test_rejects_symlink_fifo_public_file_and_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            referent = base / "referent"
            referent.write_bytes(b"do-not-touch")
            referent.chmod(0o600)
            symlink = base / "tail-symlink"
            symlink.symlink_to(referent)

            fifo = base / "tail-fifo"
            os.mkfifo(fifo, 0o600)

            public_file = base / "public-tail"
            public_file.write_bytes(b"public-do-not-touch")
            public_file.chmod(0o644)

            real_parent = base / "real-parent"
            real_parent.mkdir()
            linked_parent = base / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)

            for hostile in (
                symlink,
                fifo,
                public_file,
                linked_parent / "tail",
            ):
                with self.subTest(path=hostile):
                    completed = self.run_relay(hostile, b"payload", timeout=2)
                    self.assertEqual(completed.returncode, 73, completed.stderr)

            self.assertEqual(referent.read_bytes(), b"do-not-touch")
            self.assertEqual(public_file.read_bytes(), b"public-do-not-touch")
            self.assertFalse((real_parent / "tail").exists())

    def test_closes_inherited_descriptors_before_draining(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tail_path = Path(directory) / "fd.tail"
            read_fd, write_fd = os.pipe()
            os.set_blocking(read_fd, False)
            try:
                process = subprocess.Popen(
                    [str(RELAY), "--tail-file", str(tail_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    pass_fds=(write_fd,),
                )
                os.close(write_fd)
                write_fd = -1
                deadline = time.monotonic() + 2
                inherited_writer_closed = False
                while time.monotonic() < deadline:
                    readable, _, _ = select.select([read_fd], [], [], 0.05)
                    if readable and os.read(read_fd, 1) == b"":
                        inherited_writer_closed = True
                        break
                self.assertTrue(inherited_writer_closed)
                assert process.stdin is not None
                process.stdin.close()
                self.assertEqual(process.wait(timeout=2), 0)
                assert process.stderr is not None
                process.stderr.close()
            finally:
                os.close(read_fd)
                if write_fd >= 0:
                    os.close(write_fd)

    @unittest.skipUnless(Path("/proc/self/status").exists(), "requires Linux procfs")
    def test_memory_does_not_scale_with_total_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tail_path = Path(directory) / "memory.tail"
            process = subprocess.Popen(
                [
                    str(RELAY),
                    "--tail-file",
                    str(tail_path),
                    "--tail-bytes",
                    str(1024 * 1024),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            assert process.stdin is not None
            block = b"M" * (64 * 1024)
            peak_rss_kib = 0
            for _ in range(768):  # 48 MiB, while retained state stays at 1 MiB.
                process.stdin.write(block)
                if _ % 8 == 0:
                    try:
                        status = Path(f"/proc/{process.pid}/status").read_text()
                    except FileNotFoundError:
                        break
                    for line in status.splitlines():
                        if line.startswith("VmRSS:"):
                            peak_rss_kib = max(peak_rss_kib, int(line.split()[1]))
                            break
            process.stdin.close()
            status = process.wait(timeout=8)
            assert process.stderr is not None
            diagnostic = process.stderr.read()
            process.stderr.close()
            self.assertEqual(status, 0, diagnostic)
            self.assertGreater(peak_rss_kib, 0)
            self.assertLess(peak_rss_kib, 32 * 1024)
            self.assertEqual(tail_path.stat().st_size, 1024 * 1024)
            self.assertEqual(tail_path.read_bytes(), b"M" * (1024 * 1024))

    def test_invalid_or_excessive_tail_size_fails_before_file_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for value in ("0", "-1", "not-a-number", str(64 * 1024 * 1024 + 1)):
                tail_path = Path(directory) / f"tail-{value}"
                completed = subprocess.run(
                    [
                        str(RELAY),
                        "--tail-file",
                        str(tail_path),
                        "--tail-bytes",
                        value,
                    ],
                    input=b"payload",
                    capture_output=True,
                    timeout=2,
                    check=False,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertFalse(tail_path.exists())


if __name__ == "__main__":
    unittest.main()
