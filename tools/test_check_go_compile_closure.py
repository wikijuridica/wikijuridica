#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "tools" / "check-go-compile-closure"


class CompileClosureTest(unittest.TestCase):
    def make_fixture(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="wiki-compile-closure-test-"))
        self.addCleanup(shutil.rmtree, root)
        (root / "lib").mkdir()
        (root / "cmd" / "app").mkdir(parents=True)
        (root / "cmd" / "devapp").mkdir(parents=True)

        (root / "go.mod").write_text(
            "module example.test/compileclosure\n\ngo 1.26\n",
            encoding="utf-8",
        )
        (root / "lib" / "lib.go").write_text(
            "package lib\n\nfunc Value() string { return \"ok\" }\n",
            encoding="utf-8",
        )
        (root / "cmd" / "app" / "main.go").write_text(
            "package main\n\n"
            'import "example.test/compileclosure/lib"\n\n'
            "func main() { _ = lib.Value() }\n",
            encoding="utf-8",
        )
        (root / "cmd" / "devapp" / "main.go").write_text(
            "//go:build devcmds\n\n"
            "package main\n\n"
            "func main() {}\n",
            encoding="utf-8",
        )
        (root / "cmd" / "devapp" / "main_test.go").write_text(
            "//go:build devcmds\n\n"
            "package main\n\n"
            "import \"testing\"\n\n"
            "func TestFixture(t *testing.T) {}\n",
            encoding="utf-8",
        )
        return root

    def run_checker(
        self, root: Path, *, parallelism: int | None = None,
        packages: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = {
            "HOME": os.environ.get("HOME", "/tmp"),
            "PATH": "/usr/bin:/bin",
            "TMPDIR": "/tmp",
        }
        arguments = [str(CHECKER), "--root", str(root)]
        if parallelism is not None:
            arguments.extend(["--parallelism", str(parallelism)])
        for package in packages or []:
            arguments.extend(["--package", package])
        return subprocess.run(
            arguments,
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )

    def test_compiles_main_package_without_linking_an_executable(self) -> None:
        root = self.make_fixture()
        result = self.run_checker(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("production+devcmds packages and test variants compiled", result.stdout)
        self.assertFalse((root / "app").exists())

    def test_devcmds_package_is_inside_compile_closure(self) -> None:
        root = self.make_fixture()
        (root / "cmd" / "devapp" / "main.go").write_text(
            "//go:build devcmds\n\npackage main\n\nfunc main() { missing() }\n",
            encoding="utf-8",
        )
        result = self.run_checker(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undefined: missing", result.stderr)

    def test_devcmds_test_variant_is_inside_compile_closure(self) -> None:
        root = self.make_fixture()
        (root / "cmd" / "devapp" / "main_test.go").write_text(
            "//go:build devcmds\n\npackage main\n\n"
            "import \"testing\"\n\n"
            "func TestFixture(t *testing.T) { missing() }\n",
            encoding="utf-8",
        )
        result = self.run_checker(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undefined: missing", result.stderr)

    def test_parallelism_is_auto_by_default_and_explicitly_overridable(self) -> None:
        root = self.make_fixture()
        explicit = self.run_checker(root, parallelism=1)
        self.assertEqual(explicit.returncode, 0, explicit.stderr)

        invalid = self.run_checker(root, parallelism=0)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("positive integer", invalid.stderr)

    def test_closed_environment_ignores_path_go_overrides_and_git_index(self) -> None:
        root = self.make_fixture()
        poison = root / "poison-bin"
        poison.mkdir()
        for name in ("go", "git", "bash"):
            executable = poison / name
            executable.write_text("#!/bin/sh\nexit 91\n", encoding="utf-8")
            executable.chmod(0o755)

        env = {
            "HOME": os.environ.get("HOME", "/tmp"),
            "PATH": str(poison),
            "TMPDIR": str(root / "attacker-tmp"),
            "GO_MODERN_BIN": str(poison / "go"),
            "GOFLAGS": "-tags=attacker",
            "GOENV": str(root / "attacker-goenv"),
            "GOTOOLCHAIN": "path",
            "GOWORK": str(root / "attacker.work"),
            "GIT_INDEX_FILE": str(root / "nonexistent-index"),
        }
        result = subprocess.run(
            [str(CHECKER), "--root", str(root)],
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("production+devcmds packages and test variants compiled", result.stdout)

    def test_fails_when_changed_library_breaks_reverse_dependent_main(self) -> None:
        root = self.make_fixture()
        first = self.run_checker(root)
        self.assertEqual(first.returncode, 0, first.stderr)

        (root / "lib" / "lib.go").write_text(
            "package lib\n\nfunc Value(required int) string { return \"broken\" }\n",
            encoding="utf-8",
        )
        result = self.run_checker(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not enough arguments in call to lib.Value", result.stderr)

    def test_selected_root_compiles_only_its_dependency_closure(self) -> None:
        root = self.make_fixture()
        (root / "cmd" / "devapp" / "main.go").write_text(
            "//go:build devcmds\n\npackage main\n\nfunc main() { missing() }\n",
            encoding="utf-8",
        )
        result = self.run_checker(
            root, packages=["example.test/compileclosure/cmd/app"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selected_root_argument_is_fail_closed(self) -> None:
        root = self.make_fixture()
        result = self.run_checker(root, packages=["./...;false-green"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("canonical Go import path", result.stderr)

    def test_readonly_module_mode_rejects_go_mod_drift(self) -> None:
        root = self.make_fixture()
        dependency = root / "dependency"
        dependency.mkdir()
        (dependency / "go.mod").write_text(
            "module example.test/dependency\n\ngo 1.26\n",
            encoding="utf-8",
        )
        (dependency / "dependency.go").write_text(
            "package dependency\n\nfunc Value() string { return \"dependency\" }\n",
            encoding="utf-8",
        )
        (root / "go.mod").write_text(
            "module example.test/compileclosure\n\ngo 1.26\n\n"
            "replace example.test/dependency => ./dependency\n",
            encoding="utf-8",
        )
        (root / "cmd" / "app" / "main.go").write_text(
            "package main\n\n"
            'import "example.test/dependency"\n\n'
            "func main() { _ = dependency.Value() }\n",
            encoding="utf-8",
        )

        result = self.run_checker(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("replaced but not required", result.stderr)

    def test_env_symlink_is_accepted_and_unusable_target_is_not(self) -> None:
        # uutils na torre (2026-09-24): /usr/bin/env é symlink de root para um
        # multicall. O checker roda como o wrapper o roda — `sh -c <texto>
        # <caminho do checker>` — com ENV_BIN trocado por um symlink.
        root = self.make_fixture()
        links = Path(tempfile.mkdtemp(prefix="wiki-compile-closure-env-"))
        self.addCleanup(shutil.rmtree, links)
        text = CHECKER.read_text(encoding="utf-8")
        declared = "ENV_BIN=/usr/bin/env\n"
        self.assertEqual(text.count(declared), 1)

        def run_with(env_bin: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["/bin/sh", "-c", text.replace(declared, f"ENV_BIN={env_bin}\n"),
                 str(CHECKER), "--root", str(root)],
                cwd=root,
                env={"HOME": os.environ.get("HOME", "/tmp"),
                     "PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"},
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30, check=False)

        env_link = links / "env"
        env_link.symlink_to(os.path.realpath("/usr/bin/env"))
        result = run_with(env_link)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("go-compile-closure: PASS", result.stdout)

        not_executable = links / "nao-executavel"
        not_executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        not_executable.chmod(0o644)
        to_not_executable = links / "env-para-nao-executavel"
        to_not_executable.symlink_to(not_executable)
        dangling = links / "env-quebrado"
        dangling.symlink_to(links / "ausente")
        for env_bin in (to_not_executable, dangling):
            with self.subTest(env_bin=env_bin.name):
                result = run_with(env_bin)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(
                    "go-compile-closure: trusted env binary is unavailable",
                    result.stderr)

    def test_checker_is_executable_and_never_invokes_linking_commands(self) -> None:
        mode = CHECKER.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR)
        text = CHECKER.read_text(encoding="utf-8")
        self.assertIn("list", text)
        self.assertIn("-tags=devcmds", text)
        self.assertIn("-test", text)
        self.assertIn("-export", text)
        self.assertIn("-mod=readonly", text)
        self.assertIn('"$ENV_BIN" -i', text)
        self.assertIn("GOWORK=off", text)
        self.assertIn("GIT_INDEX_FILE", text)
        self.assertIn("./...", text)
        self.assertNotIn('go-modern\" build', text)
        self.assertNotIn('go-modern\" test', text)
        self.assertNotIn("-p=2", text)

    def test_full_link_build_remains_in_engineering_release_profile_and_ci(self) -> None:
        engineering = (REPO_ROOT / "scripts" / "workflows" / "engenharia-gate.js").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "./tools/run-heavy-throttled nice -n 10 ./tools/go-modern build -p 4 ./...",
            engineering,
        )

        security = (REPO_ROOT / ".github" / "workflows" / "security.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("github/codeql-action/autobuild@", security)


if __name__ == "__main__":
    unittest.main()
