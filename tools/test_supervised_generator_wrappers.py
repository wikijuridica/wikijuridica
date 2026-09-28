#!/usr/bin/env python3
"""Focused behavior tests for generator supervision and temp cleanup."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


TOOLS = pathlib.Path(__file__).parent


class RunGenerateSupervisedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="run-generate-supervised-test-")
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "tools").mkdir()
        (self.root / "data" / "research").mkdir(parents=True)
        (self.root / "data" / "research" / "example.jsonl").write_text("{}\n", encoding="utf-8")
        shutil.copy2(TOOLS / "run-generate-supervised", self.root / "tools" / "run-generate-supervised")
        (self.root / "tools" / "generate-example").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (self.root / "tools" / "generate-example").chmod(0o755)
        self.capture = self.root / "capture"
        fake_heavy = self.root / "tools" / "run-heavy-throttled"
        fake_heavy.write_text(
            "#!/usr/bin/env bash\n"
            "printf 'timing_mode=%s\\n' \"${WIKI_HEAVY_TIMING_MODE:-}\" >\"$CAPTURE\"\n"
            "printf 'arg=%s\\n' \"$@\" >>\"$CAPTURE\"\n",
            encoding="utf-8",
        )
        fake_heavy.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *args: str, capability: str | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update({"CAPTURE": os.fspath(self.capture), "HOME": os.fspath(self.root)})
        environment.pop("WIKI_GENERATE_TIMINGS_CAPABILITY", None)
        environment.pop("WIKI_HEAVY_TIMING_MODE", None)
        if capability is not None:
            environment["WIKI_GENERATE_TIMINGS_CAPABILITY"] = capability
        return subprocess.run(
            [os.fspath(self.root / "tools" / "run-generate-supervised"), *args],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )

    def captured(self) -> tuple[str, list[str]]:
        lines = self.capture.read_text(encoding="utf-8").splitlines()
        return lines[0].removeprefix("timing_mode="), [line.removeprefix("arg=") for line in lines[1:]]

    def latest_claim(self) -> dict[str, object]:
        claim = self.root / ".agents" / "runtime" / "generate-wrapper-claims" / "generate-example.jsonl"
        return json.loads(claim.read_text(encoding="utf-8").splitlines()[0])

    def test_default_supervisor_timing_preserves_standalone_argv(self) -> None:
        result = self.invoke("./cmd/generate-example", "--root", "/tmp/example", "--tags=program")
        self.assertEqual(result.returncode, 0, result.stderr)
        mode, args = self.captured()
        self.assertEqual(mode, "supervisor_wall_clock_v1")
        self.assertEqual(
            args,
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/generate-example", "--root", "/tmp/example", "--tags=program"],
        )
        claim = self.latest_claim()
        self.assertEqual(claim["timing_mode"], "supervisor_wall_clock_v1")
        self.assertEqual(claim["command"], "./cmd/generate-example")

    def test_child_timing_flag_requires_explicit_capability(self) -> None:
        result = self.invoke("./cmd/generate-example", "--root", "/tmp/example", capability="child_flag_v1")
        self.assertEqual(result.returncode, 0, result.stderr)
        mode, args = self.captured()
        self.assertEqual(mode, "child_flag_v1")
        self.assertEqual(args[1:], ["./cmd/generate-example", "--timings", "--root", "/tmp/example"])
        self.assertEqual(self.latest_claim()["command"], "./cmd/generate-example --timings")

    def test_multiplex_preserves_subcommand_before_child_arguments(self) -> None:
        result = self.invoke("./cmd/generate", "example", "--root", "/tmp/example")
        self.assertEqual(result.returncode, 0, result.stderr)
        mode, args = self.captured()
        self.assertEqual(mode, "supervisor_wall_clock_v1")
        self.assertEqual(args[1:], ["./cmd/generate", "example", "--root", "/tmp/example"])

    def test_unknown_timing_capability_fails_closed(self) -> None:
        result = self.invoke("./cmd/generate-example", capability="source-code-guess")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("WIKI_GENERATE_TIMINGS_CAPABILITY", result.stderr)
        self.assertFalse(self.capture.exists())


class SupervisionAndCleanupIntegrationTest(unittest.TestCase):
    def test_run_heavy_emits_external_timing_without_mutating_child_argv(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-heavy-external-timing-test-") as temporary:
            root = pathlib.Path(temporary)
            (root / "data" / "research").mkdir(parents=True)
            (root / "data" / "research" / "example.jsonl").write_text("{}\n", encoding="utf-8")
            capture = root / "child-capture"
            fake_runner = root / "run-go-cmd-cached"
            fake_runner.write_text(
                "#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" >\"$CAPTURE\"\n",
                encoding="utf-8",
            )
            fake_runner.chmod(0o755)
            environment = os.environ.copy()
            environment.update(
                {
                    "CAPTURE": os.fspath(capture),
                    "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                    "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                    "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                    "WIKI_HEAVY_BUDGET_MS": "5000",
                    "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                    "WIKI_HEAVY_STOP_CONDITION": "fake child exits",
                    "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1",
                    "WIKI_HEAVY_TIMING_MODE": "supervisor_wall_clock_v1",
                    "WIKI_HEAVY_LOCK_DIR": os.fspath(root / "locks"),
                    "WIKI_HEAVY_PROGRESS_MONITOR": "off",
                    "WIKI_HEAVY_TIMEOUT_SECONDS": "5",
                    "WIKI_HEAVY_TIMEOUT_KILL_AFTER_SECONDS": "1",
                }
            )
            result = subprocess.run(
                [os.fspath(TOOLS / "run-heavy-throttled"), os.fspath(fake_runner), "./cmd/generate-example", "--root", "/tmp/example"],
                cwd=root,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(capture.read_text(encoding="utf-8").splitlines(), ["./cmd/generate-example", "--root", "/tmp/example"])
            self.assertRegex(result.stderr, r"timing mode=supervisor_wall_clock_v1 duration_ms=\d+ exit_code=0")

    def test_content_lab_temp_files_are_removed_after_cached_runner_returns(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lab-content-quality-test-") as temporary:
            root = pathlib.Path(temporary)
            (root / "tools").mkdir()
            shutil.copy2(TOOLS / "lab-content-quality", root / "tools" / "lab-content-quality")
            capture = root / "args"
            fake_runner = root / "tools" / "run-go-cmd-cached"
            fake_runner.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" >\"$CAPTURE\"\n", encoding="utf-8")
            fake_runner.chmod(0o755)
            environment = os.environ.copy()
            environment.update({"CAPTURE": os.fspath(capture), "HOME": os.fspath(root)})
            result = subprocess.run(
                [os.fspath(root / "tools" / "lab-content-quality")],
                cwd=root,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            args = capture.read_text(encoding="utf-8").splitlines()
            self.assertEqual(args[0], "./cmd/content-lab")
            for value in args[1:]:
                _, path = value.split(":", 1)
                self.assertFalse(pathlib.Path(path).exists(), path)


if __name__ == "__main__":
    unittest.main()
