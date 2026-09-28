#!/usr/bin/env python3
"""Focused argv/environment tests for tools/go-modern."""

from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import unittest


GO_MODERN = pathlib.Path(__file__).with_name("go-modern")


class GoModernTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="go-modern-test-")
        self.root = pathlib.Path(self.temporary.name)
        self.args_path = self.root / "args"
        self.cgo_path = self.root / "cgo"
        self.fake_go = self.root / "fake-go"
        self.fake_go.write_text(
            "#!/usr/bin/env bash\n"
            "printf '%s\\0' \"$@\" >\"$GO_MODERN_CAPTURE_ARGS\"\n"
            "printf '%s\\n' \"${CGO_ENABLED:-unset}\" >\"$GO_MODERN_CAPTURE_CGO\"\n",
            encoding="utf-8",
        )
        self.fake_go.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, *args: str, cgo: str | None = None, goflags: str = "") -> tuple[list[str], str]:
        environment = os.environ.copy()
        environment.update(
            {
                "GO_MODERN_BIN": os.fspath(self.fake_go),
                "GO_MODERN_CAPTURE_ARGS": os.fspath(self.args_path),
                "GO_MODERN_CAPTURE_CGO": os.fspath(self.cgo_path),
                "GOFLAGS": goflags,
            }
        )
        environment.pop("CGO_ENABLED", None)
        if cgo is not None:
            environment["CGO_ENABLED"] = cgo
        result = subprocess.run(
            [os.fspath(GO_MODERN), *args],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self.args_path.read_bytes().split(b"\0")
        self.assertEqual(captured[-1], b"")
        return [value.decode("utf-8") for value in captured[:-1]], self.cgo_path.read_text(encoding="ascii").strip()

    def test_run_injects_devcmds_without_reading_program_arguments_as_go_flags(self) -> None:
        argv, cgo = self.invoke("run", "./cmd/example", "--tags=program-value", "-race")
        self.assertEqual(argv, ["run", "-tags", "devcmds", "./cmd/example", "--tags=program-value", "-race"])
        self.assertEqual(cgo, "unset")

        argv, _ = self.invoke("run", "-buildvcs", "./cmd/example", "--tags=program-value")
        self.assertEqual(argv, ["run", "-tags", "devcmds", "-buildvcs", "./cmd/example", "--tags=program-value"])

    def test_run_merges_existing_separate_and_equals_tags(self) -> None:
        argv, _ = self.invoke("run", "-ldflags", "-X main.value=x", "-tags", "integration", "./cmd/example")
        self.assertEqual(argv, ["run", "-ldflags", "-X main.value=x", "-tags", "integration,devcmds", "./cmd/example"])

        argv, _ = self.invoke("run", "-tags=integration,devcmds", "./cmd/example")
        self.assertEqual(argv, ["run", "-tags=integration,devcmds", "./cmd/example"])

        argv, _ = self.invoke("run", "./cmd/example", goflags="-trimpath -tags=integration")
        self.assertEqual(argv, ["run", "-tags", "integration,devcmds", "./cmd/example"])

    def test_global_chdir_prefix_is_preserved(self) -> None:
        argv, _ = self.invoke("-C", "/tmp", "run", "./cmd/example")
        self.assertEqual(argv, ["-C", "/tmp", "run", "-tags", "devcmds", "./cmd/example"])

    def test_race_enables_cgo_only_when_operator_did_not_set_it(self) -> None:
        argv, cgo = self.invoke("run", "-race", "./cmd/example")
        self.assertEqual(argv, ["run", "-tags", "devcmds", "-race", "./cmd/example"])
        self.assertEqual(cgo, "1")

        _, cgo = self.invoke("test", "-race", "./internal/example")
        self.assertEqual(cgo, "1")

        _, cgo = self.invoke("test", "-race", "./internal/example", cgo="0")
        self.assertEqual(cgo, "0")

        _, cgo = self.invoke("test", "./internal/example", goflags="-race")
        self.assertEqual(cgo, "1")


if __name__ == "__main__":
    unittest.main()
