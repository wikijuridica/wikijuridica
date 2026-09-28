#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile
import time
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "check-go-index-compile-closure"
CHECKER = REPO_ROOT / "tools" / "check-go-compile-closure"
TOOL_NAMESPACE = runpy.run_path(
    str(TOOL), run_name="go_index_compile_closure_test")
API_SURFACE_HELPER = TOOL_NAMESPACE["API_SURFACE_HELPER"]
PINNED_GO_VERSION = TOOL_NAMESPACE["PINNED_GO_VERSION"]
PINNED_GO_VERSION_PAYLOAD = TOOL_NAMESPACE["PINNED_GO_VERSION_PAYLOAD"]
PINNED_TOOLCHAIN_REL = TOOL_NAMESPACE["PINNED_TOOLCHAIN_REL"]
PINNED_TOOL_DIGESTS = TOOL_NAMESPACE["PINNED_TOOL_DIGESTS"]
SnapshotError = TOOL_NAMESPACE["SnapshotError"]
authenticate_pinned_toolchain = TOOL_NAMESPACE[
    "_authenticate_pinned_toolchain"]
revalidate_file = TOOL_NAMESPACE["_revalidate_file"]
revalidate_runtime_directory = TOOL_NAMESPACE[
    "_revalidate_runtime_directory"]
safe_payload = TOOL_NAMESPACE["_safe_payload"]
resolve_system_binary = TOOL_NAMESPACE["_resolve_system_binary"]
bind_system_binary = TOOL_NAMESPACE["_bind_system_binary"]
MAX_SYSTEM_BINARY_SYMLINK_HOPS = TOOL_NAMESPACE[
    "MAX_SYSTEM_BINARY_SYMLINK_HOPS"]
# runpy.run_path devolve uma CÓPIA dos globais do módulo; trocar uma constante
# para as funções enxergarem exige o dicionário que elas de fato consultam.
TOOL_GLOBALS = bind_system_binary.__globals__


class IndexCompileClosureTest(unittest.TestCase):
    def make_minimal_toolchain_runtime(self) -> Path:
        runtime_root = Path(tempfile.mkdtemp(
            prefix="go-index-toolchain-runtime-")).resolve()
        self.addCleanup(shutil.rmtree, runtime_root)
        source = REPO_ROOT.joinpath(*PINNED_TOOLCHAIN_REL.parts)
        target = runtime_root.joinpath(*PINNED_TOOLCHAIN_REL.parts)
        for relative in ("VERSION", *PINNED_TOOL_DIGESTS):
            destination = target.joinpath(
                *Path(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source.joinpath(*Path(relative).parts), destination)
        return runtime_root

    def workspace_paths(self, root: Path) -> tuple[Path, Path]:
        digest = hashlib.sha256()
        digest.update(b"wiki-go-index-closure-workspace-v1\0")
        digest.update(str(os.getuid()).encode("ascii"))
        digest.update(b"\0")
        digest.update(os.fsencode(root.resolve()))
        key = digest.hexdigest()[:32]
        parent = Path("/tmp") / f"wiki-go-index-closure-u{os.getuid()}"
        return parent / f"{key}.workspace", parent / f"{key}.lock"

    def cleanup_workspace_paths(self, root: Path) -> None:
        workspace, lock = self.workspace_paths(root)
        if workspace.is_symlink():
            workspace.unlink()
        elif workspace.exists():
            shutil.rmtree(workspace)
        if lock.exists() or lock.is_symlink():
            lock.unlink()
        try:
            workspace.parent.rmdir()
        except OSError:
            pass

    def result_workspace(self, result: subprocess.CompletedProcess[str]) -> Path:
        match = re.search(r"(?:^| )workspace=(/\S+)", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        assert match is not None
        return Path(match.group(1))

    def make_fixture(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="wiki-go-index-closure-test-")).resolve()
        self.addCleanup(shutil.rmtree, root)
        self.addCleanup(self.cleanup_workspace_paths, root)
        (root / "lib").mkdir()
        (root / "cmd" / "app").mkdir(parents=True)
        (root / "cmd" / "devapp").mkdir(parents=True)
        (root / "tools").mkdir()
        (root / "go.mod").write_text(
            "module example.test/indexclosure\n\ngo 1.26\n", encoding="utf-8")
        (root / "go.sum").write_bytes(b"")
        (root / "lib" / "lib.go").write_text(
            "package lib\n\nfunc Value() string { return \"ok\" }\n",
            encoding="utf-8")
        (root / "cmd" / "app" / "main.go").write_text(
            "package main\n\n"
            'import "example.test/indexclosure/lib"\n\n'
            "func main() { _ = lib.Value() }\n", encoding="utf-8")
        (root / "cmd" / "devapp" / "main.go").write_text(
            "//go:build devcmds\n\npackage main\n\nfunc main() {}\n",
            encoding="utf-8")
        (root / "cmd" / "devapp" / "main_test.go").write_text(
            "//go:build devcmds\n\npackage main\n\nimport \"testing\"\n\n"
            "func TestFixture(t *testing.T) {}\n", encoding="utf-8")
        shutil.copyfile(TOOL, root / "tools" / TOOL.name)
        shutil.copyfile(CHECKER, root / "tools" / CHECKER.name)
        (root / "tools" / TOOL.name).chmod(0o755)
        (root / "tools" / CHECKER.name).chmod(0o755)
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Fixture")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "add", "--", ".")
        self.git(root, "commit", "-q", "-m", "fixture baseline")
        return root

    def stage_trivial_go_change(self, root: Path) -> None:
        """Stage a harmless, still-valid change to a real Go build input.

        Some fixtures only stage a change to the Python router or the shell
        checker itself.  Since neither file is a compiler input, that alone
        is routed through the proportional authority-only fast path (see
        test_checker_only_delta_is_authenticated_without_full_go_compile),
        which never actually executes the checker -- it only authenticates
        the staged blob and validates shell syntax.  Tests that need to
        observe real checker *execution* (exit code, stderr side effects,
        timing) must also stage a genuine Go delta so the gate takes the
        full compile route.

        A go.mod comment (rather than a package .go file) is used
        deliberately: a module-manifest change forces the full/reverse
        route for the whole module without invoking the direct-route AST
        surface classifier (a separate `go run` subprocess with its own,
        less predictable, timing).  That keeps callers that assert a tight
        elapsed-time bound (e.g. the global budget test) robust regardless
        of Go build-cache warmth.
        """
        manifest = root / "go.mod"
        manifest.write_text(
            manifest.read_text(encoding="utf-8") + "\n// trivial comment\n",
            encoding="utf-8")
        self.git(root, "add", "--", "go.mod")

    def git(
        self, root: Path, *arguments: str, input_payload: bytes | None = None,
    ) -> bytes:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(root), *arguments], input=input_payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(
            completed.returncode, 0,
            completed.stderr.decode("utf-8", errors="replace"))
        return completed.stdout

    def run_tool(
        self, root: Path, *, index: Path | None = None,
        environment: dict[str, str] | None = None,
        index_from_environment: bool = False,
        discover_index: bool = False,
        parallelism: int | None = None,
        budget_seconds: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        selected_index = index or root / ".git" / "index"
        env = {
            "HOME": os.environ.get("HOME", "/tmp"),
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
        }
        if environment:
            env.update(environment)
        arguments = [str(TOOL), "--root", str(root)]
        if discover_index:
            pass
        elif index_from_environment:
            env["GIT_INDEX_FILE"] = str(selected_index)
        else:
            arguments.extend(["--index-file", str(selected_index)])
        if parallelism is not None:
            arguments.extend(["--parallelism", str(parallelism)])
        if budget_seconds is not None:
            arguments.extend(["--budget-seconds", str(budget_seconds)])
        return subprocess.run(
            arguments,
            cwd=root, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=30, check=False)

    def test_staged_snapshot_ignores_broken_worktree(self) -> None:
        root = self.make_fixture()
        (root / "lib" / "lib.go").write_text(
            "package lib\n\nfunc Value(required int) string { return \"bad\" }\n",
            encoding="utf-8")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("go-index-compile-closure: PASS", result.stdout)

    def test_workspace_path_is_deterministic_rebuilt_and_cleaned(self) -> None:
        root = self.make_fixture()
        first = self.run_tool(root)
        self.assertEqual(first.returncode, 0, first.stderr)
        first_workspace = self.result_workspace(first)
        expected_workspace, _ = self.workspace_paths(root)
        self.assertEqual(first_workspace, expected_workspace)
        self.assertTrue(first_workspace.is_absolute())
        self.assertFalse(first_workspace.is_relative_to(root))
        self.assertFalse(first_workspace.exists())

        # A secure residue from a crashed producer is discarded; staged OIDs,
        # not previous workspace bytes, remain the only materialization source.
        first_workspace.mkdir(mode=0o700)
        (first_workspace / "root" / "lib").mkdir(parents=True, mode=0o700)
        poison = first_workspace / "root" / "lib" / "lib.go"
        poison.write_text("package lib\nfunc broken(\n", encoding="utf-8")
        poison.chmod(0o600)
        second = self.run_tool(root)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.result_workspace(second), first_workspace)
        self.assertFalse(first_workspace.exists())

    def test_workspace_is_cleaned_when_staged_checker_fails(self) -> None:
        root = self.make_fixture()
        staged_runtime = root / "tools" / CHECKER.name
        staged_runtime.write_bytes(
            staged_runtime.read_bytes() +
            b"\nprintf 'intentional fixture failure\\n' >&2\nexit 41\n")
        staged_runtime.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        # A checker-only delta with no staged Go input is legitimately fast-
        # pathed (proportional authority-delta auth, no execution -- see
        # test_checker_only_delta_is_authenticated_without_full_go_compile).
        # Staging a real (harmless) Go change alongside forces the full
        # compile route so the injected failure is actually exercised.
        self.stage_trivial_go_change(root)
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("intentional fixture failure", result.stderr)
        workspace, _ = self.workspace_paths(root)
        self.assertFalse(workspace.exists())

    def test_concurrent_gate_fails_fast_without_waiting_for_lock(self) -> None:
        root = self.make_fixture()
        ready = root / "holder.ready"
        release = root / "holder.release"
        os.mkfifo(release, 0o600)
        staged_runtime = root / "tools" / CHECKER.name
        staged_runtime.write_text(
            staged_runtime.read_text(encoding="utf-8") +
            f"\nprintf ready >'{ready}'\nIFS= read -r token <'{release}'\n",
            encoding="utf-8",
        )
        staged_runtime.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        # Force the full compile route (see stage_trivial_go_change) so the
        # staged checker is actually executed and blocks on the fifo.
        self.stage_trivial_go_change(root)
        arguments = [
            str(TOOL), "--root", str(root), "--index-file",
            str(root / ".git" / "index"),
        ]
        environment = {
            "HOME": os.environ.get("HOME", "/tmp"),
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
        }
        holder = subprocess.Popen(
            arguments, cwd=root, env=environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and holder.poll() is None:
                if time.monotonic() >= deadline:
                    self.fail("holder did not acquire the deterministic workspace lock")
                time.sleep(0.01)
            self.assertIsNone(holder.poll())
            started = time.monotonic()
            contender = self.run_tool(root)
            elapsed = time.monotonic() - started
            self.assertNotEqual(contender.returncode, 0)
            self.assertLess(elapsed, 2.0)
            self.assertIn("lock concorrente; fail-fast", contender.stderr)
        finally:
            if holder.poll() is None:
                descriptor = os.open(release, os.O_WRONLY)
                try:
                    os.write(descriptor, b"release\n")
                finally:
                    os.close(descriptor)
            holder_stdout, holder_stderr = holder.communicate(timeout=10)
        self.assertEqual(holder.returncode, 0, holder_stderr)
        self.assertIn("go-index-compile-closure: PASS", holder_stdout)
        workspace, _ = self.workspace_paths(root)
        self.assertFalse(workspace.exists())

    def test_workspace_symlink_mode_and_lock_hardlink_are_rejected(self) -> None:
        root = self.make_fixture()
        baseline = self.run_tool(root)
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        workspace, lock = self.workspace_paths(root)

        target = root / "must-not-be-removed"
        target.mkdir()
        workspace.symlink_to(target, target_is_directory=True)
        symlink_result = self.run_tool(root)
        self.assertNotEqual(symlink_result.returncode, 0)
        self.assertIn("symlink/inseguro", symlink_result.stderr)
        self.assertTrue(workspace.is_symlink())
        self.assertTrue(target.exists())
        workspace.unlink()

        # mkdir(mode=...) is masked by the process umask (this sandbox runs
        # with 0o077), so a requested 0o755 can silently become 0o700 --
        # passing the tool's private-directory check instead of exercising
        # it.  chmod after creation pins the exact insecure mode regardless
        # of umask.
        workspace.mkdir(mode=0o755)
        workspace.chmod(0o755)
        mode_result = self.run_tool(root)
        self.assertNotEqual(mode_result.returncode, 0)
        self.assertIn("owner/mode/nlink inseguro", mode_result.stderr)
        workspace.rmdir()

        extra_link = root / "lock-hardlink"
        os.link(lock, extra_link)
        hardlink_result = self.run_tool(root)
        self.assertNotEqual(hardlink_result.returncode, 0)
        self.assertIn("lock do workspace possui owner/mode/nlink inseguro",
                      hardlink_result.stderr)
        extra_link.unlink()

    def test_workspace_from_alien_clone_rejected_and_rebuilt(self) -> None:
        """RCA_D48_LOOP_20260721.md section 7: a workspace materialized for
        a different repository clone/worktree must never be trusted at the
        deterministic path computed for THIS root -- it must be purged and
        rebuilt exclusively from this root's own staged git blobs.

        The alien clone's tree is planted directly at the path
        check-go-index-compile-closure computes for `actual_root` (the
        same cp/hardlink primitive the RCA describes: "usar alien_workspace
        em actual_root"). `_locked_workspace` always deletes the workspace
        directory on a normal exit, so a live capture of a still-running
        alien invocation is not observable from outside the process --
        this synthetic plant is the minimal fixture the gate can actually
        process while still proving the security property end to end.
        """
        alien_root = Path(tempfile.mkdtemp(
            prefix="wiki-go-index-closure-alien-")).resolve()
        self.addCleanup(shutil.rmtree, alien_root, ignore_errors=True)
        (alien_root / "lib").mkdir(parents=True)
        (alien_root / "go.mod").write_text(
            "module example.test/alienclone\n\ngo 1.26\n", encoding="utf-8")
        (alien_root / "go.sum").write_bytes(b"")
        # Deliberately unparsable: if the gate ever trusted this foreign
        # tree instead of rebuilding from actual_root's own staged blobs,
        # the run would fail to compile instead of reporting PASS.
        (alien_root / "lib" / "lib.go").write_text(
            "package lib\n\nfunc Value(\n", encoding="utf-8")

        actual_root = self.make_fixture()
        workspace, _ = self.workspace_paths(actual_root)
        self.assertFalse(workspace.exists())

        # Plant the alien clone's tree at the exact deterministic path
        # check-go-index-compile-closure will use for actual_root -- the
        # same private-directory shape (owner uid, mode 0700) a
        # crashed/foreign producer would leave behind.
        workspace.mkdir(mode=0o700)
        (workspace / "root" / "lib").mkdir(parents=True, mode=0o700)
        alien_source = workspace / "root" / "lib" / "lib.go"
        shutil.copyfile(alien_root / "lib" / "lib.go", alien_source)
        alien_source.chmod(0o600)
        alien_go_mod = workspace / "root" / "go.mod"
        alien_go_mod.write_bytes((alien_root / "go.mod").read_bytes())
        alien_go_mod.chmod(0o600)
        alien_marker = workspace / "alien-clone-marker.txt"
        alien_marker.write_bytes(b"materialized-by-a-different-worktree\n")
        alien_marker.chmod(0o600)

        result = self.run_tool(actual_root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("go-index-compile-closure: PASS", result.stdout)
        # The alien marker and the whole deterministic path are gone: the
        # foreign tree was purged, not merged with or layered under the
        # real materialization -- proof the reconstructed workspace bytes
        # differ from (and never included) the alien clone's artifact.
        self.assertFalse(alien_marker.exists())
        self.assertFalse(workspace.exists())
        # RCA section 7(c)/mission spec: the discard of a pre-existing
        # deterministic workspace must be visible on stderr, not silent --
        # this is the forensic-visibility gap RCA section 3 opens with
        # "cache/workspace não autenticado por worktree". As of this
        # commit _prepare_workspace's FileExistsError branch (tools/
        # check-go-index-compile-closure, ~line 1036) purges and rebuilds
        # WITHOUT emitting any diagnostic, so this assertion is expected
        # to fail (RED) until that diagnostic is added.
        self.assertIn(
            "workspace determinístico existente descartado", result.stderr)

    def test_hook_environment_index_is_the_authority(self) -> None:
        root = self.make_fixture()
        result = self.run_tool(root, index_from_environment=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_partial_commit_index_may_live_outside_git_directory(self) -> None:
        root = self.make_fixture()
        external_index = root / "partial-commit.index"
        shutil.copyfile(root / ".git" / "index", external_index)
        result = self.run_tool(root, index=external_index)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_staged_runtime_checker_bytes_execute_not_dirty_worktree_path(self) -> None:
        root = self.make_fixture()
        staged_runtime = root / "tools" / CHECKER.name
        original = staged_runtime.read_bytes()
        marker = b"staged-checker-executed"
        staged_runtime.write_bytes(
            original + b"\nprintf '%s\\n' '" + marker + b"' >&2\n")
        staged_runtime.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        # Force the full compile route (see stage_trivial_go_change) so the
        # staged checker is actually executed, not merely syntax-validated
        # by the authority-only fast path.
        self.stage_trivial_go_change(root)
        # The live fixture path is deliberately not the staged authority.
        staged_runtime.write_bytes(original)
        staged_runtime.chmod(0o755)
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(marker.decode(), result.stderr)
        self.assertIn("go-index-compile-closure: PASS", result.stdout)

    def test_running_self_wrapper_must_equal_its_staged_blob(self) -> None:
        root = self.make_fixture()
        staged_self = root / "tools" / TOOL.name
        staged_self.write_bytes(staged_self.read_bytes() + b"\n# drift\n")
        staged_self.chmod(0o755)
        self.git(root, "add", "--", f"tools/{TOOL.name}")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        # A self-only delta (no staged Go input) is routed through the
        # proportional authority-only fast path (see
        # test_checker_only_delta_is_authenticated_without_full_go_compile),
        # whose self-identity check reports "runtime Python diverge..."
        # rather than the full path's "runtime worktree diverge...";  both
        # phrasings guard the same self-blob authentication property.
        self.assertIn(
            "runtime Python diverge do blob staged autenticado",
            result.stderr)

    def test_authenticated_private_self_mode_0500_is_accepted(self) -> None:
        root = self.make_fixture()
        staged_self = root / "tools" / TOOL.name
        staged_self.chmod(0o500)
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pinned_toolchain_binds_exact_files_and_directory_identity(self) -> None:
        runtime_root = self.make_minimal_toolchain_runtime()
        toolchain_root = runtime_root.joinpath(*PINNED_TOOLCHAIN_REL.parts)
        file_bindings, directory_bindings = authenticate_pinned_toolchain(
            runtime_root)
        expected_files = {toolchain_root / "VERSION"}
        expected_files.update(
            toolchain_root.joinpath(*Path(relative).parts)
            for relative in PINNED_TOOL_DIGESTS)
        self.assertEqual(set(file_bindings), expected_files)
        self.assertEqual(set(directory_bindings), {toolchain_root})
        for path, binding in file_bindings.items():
            revalidate_file(path, binding, max_bytes=64 * 1024 * 1024)
        revalidate_runtime_directory(
            toolchain_root, directory_bindings[toolchain_root])

        version_path = toolchain_root / "VERSION"
        version_path.write_bytes(PINNED_GO_VERSION_PAYLOAD + b"late-drift\n")
        with self.assertRaisesRegex(
                SnapshotError, "arquivo mudou durante compilação"):
            revalidate_file(
                version_path, file_bindings[version_path], max_bytes=4096)

        toolchain_root.chmod(0o700)
        with self.assertRaisesRegex(
                SnapshotError, "diretório runtime mudou durante compilação"):
            revalidate_runtime_directory(
                toolchain_root, directory_bindings[toolchain_root])

    def test_pinned_toolchain_rejects_version_binary_and_symlink_drift(self) -> None:
        version_runtime = self.make_minimal_toolchain_runtime()
        version_path = version_runtime.joinpath(
            *PINNED_TOOLCHAIN_REL.parts, "VERSION")
        self.assertEqual(version_path.read_bytes(), PINNED_GO_VERSION_PAYLOAD)
        version_path.write_bytes(PINNED_GO_VERSION_PAYLOAD + b"drift\n")
        with self.assertRaisesRegex(SnapshotError, "VERSION"):
            authenticate_pinned_toolchain(version_runtime)

        version_symlink_runtime = self.make_minimal_toolchain_runtime()
        symlink_version = version_symlink_runtime.joinpath(
            *PINNED_TOOLCHAIN_REL.parts, "VERSION")
        version_authority = version_symlink_runtime / "VERSION.authority"
        shutil.copy2(symlink_version, version_authority)
        symlink_version.unlink()
        symlink_version.symlink_to(version_authority)
        with self.assertRaisesRegex(
                SnapshotError, "arquivo ausente/inseguro"):
            authenticate_pinned_toolchain(version_symlink_runtime)

        binary_runtime = self.make_minimal_toolchain_runtime()
        go_bin = binary_runtime.joinpath(
            *PINNED_TOOLCHAIN_REL.parts, "bin", "go")
        with go_bin.open("r+b") as stream:
            first = stream.read(1)
            self.assertTrue(first)
            stream.seek(0)
            stream.write(bytes([first[0] ^ 0x01]))
        with self.assertRaisesRegex(SnapshotError, "digest oficial"):
            authenticate_pinned_toolchain(binary_runtime)

        symlink_runtime = Path(tempfile.mkdtemp(
            prefix="go-index-toolchain-symlink-")).resolve()
        self.addCleanup(shutil.rmtree, symlink_runtime)
        namespace = symlink_runtime / ".toolchains"
        namespace.mkdir()
        namespace.joinpath(PINNED_GO_VERSION).symlink_to(
            REPO_ROOT.joinpath(*PINNED_TOOLCHAIN_REL.parts),
            target_is_directory=True)
        with self.assertRaisesRegex(
                SnapshotError, "diretório runtime ausente/inseguro"):
            authenticate_pinned_toolchain(symlink_runtime)

    def test_staged_checker_toolchain_divergence_fails_before_execution(self) -> None:
        root = self.make_fixture()
        staged_checker = root / "tools" / CHECKER.name
        divergent_version = PINNED_GO_VERSION[:-1] + "0"
        checker_text = staged_checker.read_text(encoding="utf-8")
        self.assertIn(PINNED_GO_VERSION, checker_text)
        staged_checker.write_text(
            checker_text.replace(PINNED_GO_VERSION, divergent_version),
            encoding="utf-8")
        staged_checker.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checker staged diverge", result.stderr)
        self.assertNotIn("go-compile-closure: PASS", result.stdout)

    def test_staged_break_is_not_hidden_by_repaired_worktree(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        good = library.read_text(encoding="utf-8")
        library.write_text(
            "package lib\n\nfunc Value(required int) string { return \"bad\" }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        library.write_text(good, encoding="utf-8")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not enough arguments", result.stderr)

    def test_body_and_private_addition_compile_only_changed_package(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\n"
            "func Value() string { return \"changed\" }\n\n"
            "func helper() int { return 1 }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=1", result.stdout)
        self.assertIn("closure_mode=direct", result.stdout)
        self.assertIn(
            "surface_reason=body_or_proven_private_delta_only", result.stdout)
        self.assertNotIn("cannot find module providing package", result.stderr)

    def test_added_private_build_tag_files_compile_only_changed_package(self) -> None:
        root = self.make_fixture()
        linux = root / "lib" / "snapshot_cache_lock_linux.go"
        other = root / "lib" / "snapshot_cache_lock_other.go"
        linux.write_text(
            "//go:build linux\n\npackage lib\n\n"
            "func privateSnapshotLock() int { return 1 }\n", encoding="utf-8")
        other.write_text(
            "//go:build !linux\n\npackage lib\n\n"
            "func privateSnapshotLock() int { return 2 }\n", encoding="utf-8")
        self.git(
            root, "add", "--", "lib/snapshot_cache_lock_linux.go",
            "lib/snapshot_cache_lock_other.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=1", result.stdout)
        self.assertIn("closure_mode=direct", result.stdout)
        self.assertIn(
            "surface_reason=body_or_proven_private_delta_only", result.stdout)

    def test_added_exported_file_keeps_reverse_dependants(self) -> None:
        root = self.make_fixture()
        added = root / "lib" / "added.go"
        added.write_text(
            "package lib\n\nfunc Added() string { return \"added\" }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/added.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=2", result.stdout)
        self.assertIn("closure_mode=reverse", result.stdout)
        self.assertIn(
            "surface_reason=added_file_surface_not_proven_private",
            result.stdout)

    def test_deleted_private_file_is_direct_and_internal_break_still_fails(self) -> None:
        root = self.make_fixture()
        helper = root / "lib" / "private.go"
        helper.write_text(
            "package lib\n\nfunc privateValue() string { return \"ok\" }\n",
            encoding="utf-8")
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\nfunc Value() string { return privateValue() }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go", "lib/private.go")
        self.git(root, "commit", "-q", "-m", "private helper baseline")
        helper.unlink()
        self.git(root, "add", "-u", "--", "lib/private.go")

        # Record the selected route before the real checker type-checks and
        # rejects the now-broken package.  The staged checker remains the
        # authenticated executable authority for this fixture.
        staged_checker = root / "tools" / CHECKER.name
        checker_text = staged_checker.read_text(encoding="utf-8")
        checker_text = checker_text.replace(
            "set -eu\n",
            "set -eu\ncase \"$*\" in *\"--package "
            "example.test/indexclosure/lib\"*) "
            "echo fixture-direct-route >&2;; esac\n",
            1,
        )
        staged_checker.write_text(checker_text, encoding="utf-8")
        staged_checker.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture-direct-route", result.stderr)
        self.assertIn("undefined: privateValue", result.stderr)

    def test_deleted_exported_file_keeps_reverse_dependants(self) -> None:
        root = self.make_fixture()
        exported = root / "lib" / "exported.go"
        exported.write_text(
            "package lib\n\nfunc Removed() string { return \"old\" }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/exported.go")
        self.git(root, "commit", "-q", "-m", "exported baseline")
        exported.unlink()
        self.git(root, "add", "-u", "--", "lib/exported.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=2", result.stdout)
        self.assertIn("closure_mode=reverse", result.stdout)
        self.assertIn(
            "surface_reason=deleted_file_surface_not_proven_private",
            result.stdout)

    def test_private_predeclared_shadowing_never_uses_direct_route(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\n"
            "func Value() string { return \"ok\" }\n\n"
            "var Exported = len(\"fixture\")\n", encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        self.git(root, "commit", "-q", "-m", "builtin inference baseline")
        library.write_text(
            "package lib\n\n"
            "func Value() string { return \"ok\" }\n\n"
            "var Exported = len(\"fixture\")\n\n"
            "type custom int\n\n"
            "func len(string) custom { return 1 }\n", encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=2", result.stdout)
        self.assertIn(
            "surface_reason=private_addition_shadows_predeclared",
            result.stdout)

    def test_exported_api_change_keeps_real_reverse_dependants(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        application = root / "cmd" / "app" / "main.go"
        library.write_text(
            "package lib\n\n"
            "func Value(prefix string) string { return prefix + \"ok\" }\n",
            encoding="utf-8")
        application.write_text(
            "package main\n\n"
            'import "example.test/indexclosure/lib"\n\n'
            'func main() { _ = lib.Value("") }\n', encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go", "cmd/app/main.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=2", result.stdout)
        self.assertIn("closure_mode=reverse", result.stdout)
        self.assertIn("surface_reason=exported_surface_changed", result.stdout)

    def test_ordinary_comment_change_does_not_expand_closure(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\n"
            "// Value returns the fixture value. This is ordinary prose.\n"
            "func Value() string { return \"ok\" }\n", encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=1", result.stdout)
        self.assertIn("closure_mode=direct", result.stdout)

    def test_exported_test_function_delta_stays_direct(self) -> None:
        root = self.make_fixture()
        test_file = root / "lib" / "lib_test.go"
        test_file.write_text(
            "package lib\n\nimport \"testing\"\n\n"
            "func TestOne(t *testing.T) {}\n", encoding="utf-8")
        self.git(root, "add", "--", "lib/lib_test.go")
        self.git(root, "commit", "-q", "-m", "test api baseline")
        test_file.write_text(
            "package lib\n\nimport \"testing\"\n\n"
            "func TestOne(t *testing.T) {}\n\n"
            "func TestTwo(t *testing.T) {}\n", encoding="utf-8")
        self.git(root, "add", "--", "lib/lib_test.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=1", result.stdout)
        self.assertIn("closure_mode=direct", result.stdout)

    def test_external_test_package_delta_stays_direct_and_is_compiled(self) -> None:
        root = self.make_fixture()
        external = root / "lib" / "external_test.go"
        external.write_text(
            "package lib_test\n\nimport (\n"
            '\t"testing"\n\n'
            '\t"example.test/indexclosure/lib"\n'
            ")\n\nfunc TestExternal(t *testing.T) { _ = lib.Value() }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/external_test.go")
        self.git(root, "commit", "-q", "-m", "external test baseline")
        external.write_text(
            "package lib_test\n\nimport (\n"
            '\t"testing"\n\n'
            '\t"example.test/indexclosure/lib"\n'
            ")\n\nfunc TestExternal(t *testing.T) { _ = lib.Value() }\n\n"
            "func TestSecond(t *testing.T) {}\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/external_test.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("affected_packages=1", result.stdout)
        self.assertIn("closure_mode=direct", result.stdout)

        external.write_text(
            "package lib_test\n\nimport \"testing\"\n\n"
            "func TestExternal(t *testing.T) { missing() }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/external_test.go")
        broken = self.run_tool(root)
        self.assertNotEqual(broken.returncode, 0)
        self.assertIn("undefined: missing", broken.stderr)

    def test_body_only_compile_error_is_not_a_false_green(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\n"
            "func Value() string { return missing }\n", encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undefined: missing", result.stderr)

    def test_ast_classifier_adversarial_surface_matrix(self) -> None:
        helper_root = Path(tempfile.mkdtemp(prefix="go-api-surface-helper-test-"))
        self.addCleanup(shutil.rmtree, helper_root)
        source = helper_root / "main.go"
        binary = helper_root / "classifier"
        source.write_text(API_SURFACE_HELPER, encoding="utf-8")
        go_bin = REPO_ROOT.joinpath(
            *PINNED_TOOLCHAIN_REL.parts, "bin", "go")
        environment = {
            "PATH": "/usr/bin:/bin",
            "HOME": os.environ.get("HOME", "/tmp"),
            "LC_ALL": "C",
            "GO111MODULE": "off",
            "GOENV": "off",
            "GOTOOLCHAIN": "local",
            "GOWORK": "off",
            "GOFLAGS": "",
            "GOROOT": str(go_bin.parents[1]),
        }
        compiled = subprocess.run(
            [str(go_bin), "build", "-o", str(binary), str(source)],
            cwd=helper_root, env=environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=15, check=False)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)

        case_number = 0

        def classify(before: str | None, after: str | None) -> dict[str, object]:
            nonlocal case_number
            case_number += 1
            case_root = helper_root / f"case-{case_number:02d}"
            case_root.mkdir()
            before_path = case_root / "before.go"
            after_path = case_root / "after.go"
            if before is not None:
                before_path.write_text(before, encoding="utf-8")
            if after is not None:
                after_path.write_text(after, encoding="utf-8")
            manifest = case_root / "manifest.json"
            manifest.write_text(json.dumps({"pairs": [{
                "path": "lib/lib.go",
                "before": str(before_path) if before is not None else "",
                "after": str(after_path) if after is not None else "",
            }]}), encoding="utf-8")
            completed = subprocess.run(
                [str(binary), str(manifest)], cwd=case_root,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=2, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decoded = json.loads(completed.stdout)
            self.assertEqual(set(decoded), {"direct_only", "reason"})
            return decoded

        base = "package lib\n\nfunc Value() string { return \"ok\" }\n"
        cases = {
            "ordinary_comment": (
                base,
                "package lib\n\n// ordinary prose\n"
                "func Value() string { return \"changed\" }\n",
                True, "body_or_proven_private_delta_only"),
            "private_addition": (
                base, base + "\nfunc helper() int { return 1 }\n",
                True, "body_or_proven_private_delta_only"),
            "exported_type_and_struct_tag": (
                base + "\ntype Public struct { Field int `json:\"a\"` }\n",
                base + "\ntype Public struct { Field int `json:\"b\"` }\n",
                False, "exported_surface_changed"),
            "exported_const": (
                base + "\nconst Public = 1\n",
                base + "\nconst Public = 2\n",
                False, "exported_surface_changed"),
            "import": (
                base,
                "package lib\n\nimport \"strings\"\n\n"
                "func Value() string { return strings.TrimSpace(\"ok\") }\n",
                False, "imports_changed"),
            "build_tag": (
                base, "//go:build linux\n\n" + base,
                False, "build_compiler_or_cgo_directive_changed"),
            "go_generate": (
                base, "package lib\n\n//go:generate echo fixture\n"
                "func Value() string { return \"ok\" }\n",
                False, "build_compiler_or_cgo_directive_changed"),
            "go_embed": (
                "package lib\n\n//go:embed one.txt\nvar asset string\n",
                "package lib\n\n//go:embed two.txt\nvar asset string\n",
                False, "build_compiler_or_cgo_directive_changed"),
            "go_linkname": (
                "package lib\n\n//go:linkname local runtime.one\nfunc local()\n",
                "package lib\n\n//go:linkname local runtime.two\nfunc local()\n",
                False, "build_compiler_or_cgo_directive_changed"),
            "linked_private_signature": (
                "package lib\n\n//go:linkname local runtime.one\n"
                "func local() int\n",
                "package lib\n\n//go:linkname local runtime.one\n"
                "func local() string\n",
                False, "private_delta_with_compiler_or_cgo_directive"),
            "compiler_directive": (
                base, "package lib\n\n//go:noinline\n"
                "func Value() string { return \"ok\" }\n",
                False, "build_compiler_or_cgo_directive_changed"),
            "cgo_preamble": (
                "package lib\n\n/* typedef int fixture; */\nimport \"C\"\n",
                "package lib\n\n/* typedef long fixture; */\nimport \"C\"\n",
                False, "build_compiler_or_cgo_directive_changed"),
            "inferred_export": (
                base + "\nfunc hidden() int { return 1 }\n"
                "var Public = hidden()\nconst private = 1\n"
                "const PublicConst = private\n",
                base + "\nfunc hidden() int64 { return 1 }\n"
                "var Public = hidden()\nconst private = 2\n"
                "const PublicConst = private\n",
                False, "private_delta_reaches_exported_surface"),
            "exported_alias_private_type": (
                base + "\ntype hidden struct { Field int }\n"
                "type Public = hidden\n",
                base + "\ntype hidden struct { Field string }\n"
                "type Public = hidden\n",
                False, "private_delta_reaches_exported_surface"),
            "interface_embedding_and_constraint": (
                base + "\ntype hidden interface { private() }\n"
                "type Public interface { hidden }\n"
                "func Generic[T hidden](value T) {}\n",
                base + "\ntype hidden interface { private(); second() }\n"
                "type Public interface { hidden }\n"
                "func Generic[T hidden](value T) {}\n",
                False, "private_delta_reaches_exported_surface"),
            "reachable_private_method": (
                base + "\ntype hidden struct{}\n"
                "func (hidden) helper() int { return 1 }\n"
                "func Public() hidden { return hidden{} }\n",
                base + "\ntype hidden struct{}\n"
                "func (hidden) helper() string { return \"one\" }\n"
                "func Public() hidden { return hidden{} }\n",
                False, "private_delta_reaches_exported_surface"),
            "promoted_method": (
                base + "\ntype hidden struct{}\n"
                "func (hidden) Public() int { return 1 }\n"
                "type Exported struct { hidden }\n",
                base + "\ntype hidden struct{}\n"
                "func (hidden) Public() string { return \"one\" }\n"
                "type Exported struct { hidden }\n",
                False, "private_delta_reaches_exported_surface"),
            "generated": (
                "// Code generated by fixture. DO NOT EDIT.\n\n" + base,
                "// Code generated by fixture. DO NOT EDIT.\n\n"
                "package lib\n\nfunc Value() string { return \"changed\" }\n",
                False, "generated_file_changed"),
            "predeclared_shadow_addition": (
                base + "\nvar Public = len(\"x\")\n",
                base + "\nvar Public = len(\"x\")\n"
                "type custom int\nfunc len(string) custom { return 1 }\n",
                False, "private_addition_shadows_predeclared"),
            "added_private_build_tag_file": (
                None, "//go:build linux\n\npackage lib\n\nfunc helper() {}\n",
                True, "body_or_proven_private_delta_only"),
            "added_unreachable_type_with_exported_method": (
                None, "package lib\n\ntype hidden struct{}\n"
                "func (hidden) Public() {}\n",
                True, "body_or_proven_private_delta_only"),
            "added_exported_file": (
                None, "package lib\n\nfunc Public() {}\n",
                False, "added_file_surface_not_proven_private"),
            "deleted_private_file": (
                "package lib\n\nfunc helper() {}\n", None,
                True, "body_or_proven_private_delta_only"),
            "deleted_private_method": (
                "package lib\n\ntype hidden struct{}\n"
                "func (hidden) helper() {}\n", None,
                True, "body_or_proven_private_delta_only"),
            "deleted_exported_file": (
                "package lib\n\nfunc Public() {}\n", None,
                False, "deleted_file_surface_not_proven_private"),
            "added_predeclared_shadow": (
                None, "package lib\n\ntype int string\n",
                False, "added_file_surface_not_proven_private"),
            "deleted_predeclared_shadow": (
                "package lib\n\ntype int string\n", None,
                False, "deleted_file_surface_not_proven_private"),
        }
        for name, (before, after, expected_direct, expected_reason) in cases.items():
            with self.subTest(name=name):
                observed = classify(before, after)
                self.assertEqual(observed["direct_only"], expected_direct)
                self.assertEqual(observed["reason"], expected_reason)

    @unittest.skipUnless(
        os.environ.get("WIKI_RUN_COLD_GO_BENCHMARK") == "1",
        "opt-in cold Go cache benchmark",
    )
    def test_direct_route_cold_and_warm_stay_under_twenty_seconds(self) -> None:
        root = self.make_fixture()
        private_home = root / "private-home"
        private_home.mkdir()
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\nfunc Value() string { return \"changed\" }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        started = time.monotonic()
        cold = self.run_tool(root, environment={"HOME": str(private_home)})
        cold_elapsed = time.monotonic() - started
        started = time.monotonic()
        warm = self.run_tool(root, environment={"HOME": str(private_home)})
        warm_elapsed = time.monotonic() - started
        self.assertEqual(cold.returncode, 0, cold.stderr)
        self.assertEqual(warm.returncode, 0, warm.stderr)
        self.assertIn("closure_mode=direct", cold.stdout)
        self.assertIn("closure_mode=direct", warm.stdout)
        cold_ms = re.search(r"elapsed_ms=(\d+)", cold.stdout)
        warm_ms = re.search(r"elapsed_ms=(\d+)", warm.stdout)
        self.assertIsNotNone(cold_ms, cold.stdout)
        self.assertIsNotNone(warm_ms, warm.stdout)
        assert cold_ms is not None and warm_ms is not None
        self.assertLess(int(warm_ms.group(1)), int(cold_ms.group(1)))
        self.assertLess(cold_elapsed + warm_elapsed, 20.0)

    def test_staged_devcmds_break_is_not_a_false_green(self) -> None:
        root = self.make_fixture()
        command = root / "cmd" / "devapp" / "main.go"
        good = command.read_text(encoding="utf-8")
        command.write_text(
            "//go:build devcmds\n\npackage main\n\nfunc main() { missing() }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "cmd/devapp/main.go")
        command.write_text(good, encoding="utf-8")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undefined: missing", result.stderr)

    def test_staged_devcmds_test_break_is_not_a_false_green(self) -> None:
        root = self.make_fixture()
        test_file = root / "cmd" / "devapp" / "main_test.go"
        good = test_file.read_text(encoding="utf-8")
        test_file.write_text(
            "//go:build devcmds\n\npackage main\n\nimport \"testing\"\n\n"
            "func TestFixture(t *testing.T) { missing() }\n", encoding="utf-8")
        self.git(root, "add", "--", "cmd/devapp/main_test.go")
        test_file.write_text(good, encoding="utf-8")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undefined: missing", result.stderr)

    def test_parallelism_override_is_optional_and_validated(self) -> None:
        root = self.make_fixture()
        automatic = self.run_tool(root)
        self.assertEqual(automatic.returncode, 0, automatic.stderr)

        explicit = self.run_tool(root, parallelism=1)
        self.assertEqual(explicit.returncode, 0, explicit.stderr)

        invalid = self.run_tool(root, parallelism=0)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("positive integer", invalid.stderr)

        invalid_budget = self.run_tool(root, budget_seconds=0)
        self.assertEqual(invalid_budget.returncode, 2)
        self.assertIn("budget-seconds must be a positive integer", invalid_budget.stderr)

    def test_global_budget_bounds_staged_checker_execution(self) -> None:
        root = self.make_fixture()
        staged_runtime = root / "tools" / CHECKER.name
        staged_runtime.write_text(
            staged_runtime.read_text(encoding="utf-8") + "\nsleep 5\n",
            encoding="utf-8")
        staged_runtime.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        # Force the full compile route (see stage_trivial_go_change) so the
        # staged checker is actually executed and the budget applies to it.
        self.stage_trivial_go_change(root)
        started = time.monotonic()
        result = self.run_tool(root, budget_seconds=1)
        elapsed = time.monotonic() - started
        self.assertNotEqual(result.returncode, 0)
        self.assertLess(elapsed, 3.0)
        self.assertIn("compile closure excedeu", result.stderr)
        workspace, _ = self.workspace_paths(root)
        self.assertFalse(workspace.exists())

    def test_unformatted_staged_go_is_not_hidden_by_formatted_worktree(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        formatted = library.read_bytes()
        library.write_bytes(b"package lib\n\nfunc Value()string{return \"ok\"}\n")
        self.git(root, "add", "--", "lib/lib.go")
        library.write_bytes(formatted)
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("staged não está formatada por gofmt: lib/lib.go", result.stderr)

    def test_unformatted_worktree_is_ignored_when_staged_go_is_formatted(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\nfunc Value() string { return \"staged\" }\n",
            encoding="utf-8")
        self.git(root, "add", "--", "lib/lib.go")
        library.write_bytes(b"package lib\nfunc Value()string{return \"dirty\"}\n")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_deleted_unformatted_go_is_not_checked_by_gofmt(self) -> None:
        root = self.make_fixture()
        obsolete = root / "lib" / "obsolete.go"
        obsolete.write_bytes(b"package lib\nfunc obsolete( ){ }\n")
        self.git(root, "add", "--", "lib/obsolete.go")
        self.git(root, "commit", "-q", "-m", "add obsolete")
        obsolete.unlink()
        self.git(root, "add", "-u", "--", "lib/obsolete.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_special_staged_go_path_is_checked_without_word_splitting(self) -> None:
        root = self.make_fixture()
        special_dir = root / "special package"
        special_dir.mkdir()
        special = special_dir / "name with tab\t.go"
        special.write_bytes(b"package special\nfunc Value()string{return \"x\"}\n")
        self.git(root, "add", "--", str(special.relative_to(root)))
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("staged não está formatada por gofmt", result.stderr)

    def test_untracked_go_is_ignored_but_staged_new_go_is_compiled(self) -> None:
        root = self.make_fixture()
        attacker = root / "lib" / "attacker.go"
        attacker.write_text("package lib\nfunc broken(\n", encoding="utf-8")
        untracked = self.run_tool(root)
        self.assertEqual(untracked.returncode, 0, untracked.stderr)
        self.git(root, "add", "--", "lib/attacker.go")
        staged = self.run_tool(root)
        self.assertNotEqual(staged.returncode, 0)

    def test_staged_deletion_is_not_resurrected_from_worktree(self) -> None:
        root = self.make_fixture()
        library = root / "lib" / "lib.go"
        payload = library.read_bytes()
        library.unlink()
        self.git(root, "add", "-u", "--", "lib/lib.go")
        library.write_bytes(payload)
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot find module providing package", result.stderr)

    def test_staged_embed_asset_is_materialized_even_if_worktree_is_deleted(self) -> None:
        root = self.make_fixture()
        embedded = root / "embedded"
        embedded.mkdir()
        (embedded / "embed.go").write_text(
            "package embedded\n\nimport _ \"embed\"\n\n"
            "//go:embed message.txt\nvar Message string\n", encoding="utf-8")
        asset = embedded / "message.txt"
        asset.write_text("staged truth\n", encoding="utf-8")
        self.git(root, "add", "--", "embedded/embed.go", "embedded/message.txt")
        asset.unlink()
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_asset_only_change_uses_staged_bytes_and_missing_embed_fails_closed(self) -> None:
        root = self.make_fixture()
        embedded = root / "embedded"
        embedded.mkdir()
        source = embedded / "embed.go"
        source.write_text(
            "package embedded\n\nimport _ \"embed\"\n\n"
            "//go:embed message.txt\nvar Message string\n", encoding="utf-8")
        asset = embedded / "message.txt"
        asset.write_text("baseline\n", encoding="utf-8")
        self.git(root, "add", "--", "embedded/embed.go", "embedded/message.txt")
        self.git(root, "commit", "-q", "-m", "embed baseline")

        asset.write_text("candidate bytes\n", encoding="utf-8")
        self.git(root, "add", "--", "embedded/message.txt")
        asset.unlink()
        changed = self.run_tool(root)
        self.assertEqual(changed.returncode, 0, changed.stderr)
        self.assertIn("closure_mode=reverse", changed.stdout)
        self.assertIn("affected_packages=1", changed.stdout)

        # This disposable fixture commits the first candidate, then stages a
        # deletion and resurrects only the mutable worktree copy. The live
        # repository is never rewritten by this test.
        asset.write_text("candidate bytes\n", encoding="utf-8")
        self.git(root, "commit", "-q", "-m", "asset candidate")
        asset.unlink()
        self.git(root, "add", "-u", "--", "embedded/message.txt")
        asset.write_text("worktree must not resurrect staged deletion\n",
                         encoding="utf-8")
        deleted = self.run_tool(root)
        self.assertNotEqual(deleted.returncode, 0)
        self.assertIn("pattern message.txt: no matching files found", deleted.stderr)

    def test_assembly_and_c_inputs_are_routed_without_extension_allowlist(self) -> None:
        for name, payload, expected in (
            ("broken.s", "THIS IS NOT GO ASSEMBLY\n", "unrecognized instruction"),
            ("broken.c", "this is not valid C;\n", "C source files not allowed"),
        ):
            with self.subTest(name=name):
                root = self.make_fixture()
                compiler_input = root / "lib" / name
                compiler_input.write_text(payload, encoding="utf-8")
                self.git(root, "add", "--", f"lib/{name}")
                compiler_input.unlink()
                result = self.run_tool(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)

    def test_nested_module_is_compiled_from_its_own_staged_root(self) -> None:
        root = self.make_fixture()
        nested = root / "nested"
        package = nested / "pkg"
        package.mkdir(parents=True)
        (nested / "go.mod").write_text(
            "module example.test/nested\n\ngo 1.26\n", encoding="utf-8")
        (nested / "go.sum").write_bytes(b"")
        source = package / "pkg.go"
        source.write_text(
            "package pkg\n\nfunc Value() int { return 1 }\n", encoding="utf-8")
        self.git(root, "add", "--", "nested")
        self.git(root, "commit", "-q", "-m", "nested module baseline")

        good = source.read_text(encoding="utf-8")
        source.write_text(
            'package pkg\n\nvar broken int = "candidate only"\n', encoding="utf-8")
        self.git(root, "add", "--", "nested/pkg/pkg.go")
        source.write_text(good, encoding="utf-8")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot use \"candidate only\"", result.stderr)

    def test_nested_module_change_recompiles_local_replace_consumers(self) -> None:
        root = self.make_fixture()
        nested = root / "nested"
        package = nested / "pkg"
        package.mkdir(parents=True)
        (nested / "go.mod").write_text(
            "module example.test/nested\n\ngo 1.26\n", encoding="utf-8")
        (nested / "go.sum").write_bytes(b"")
        source = package / "pkg.go"
        source.write_text(
            "package pkg\n\nfunc Value() int { return 1 }\n", encoding="utf-8")
        (root / "go.mod").write_text(
            "module example.test/indexclosure\n\ngo 1.26\n\n"
            "require example.test/nested v0.0.0\n\n"
            "replace example.test/nested => ./nested\n",
            encoding="utf-8",
        )
        application = root / "cmd" / "app" / "main.go"
        application.write_text(
            "package main\n\n"
            'import "example.test/nested/pkg"\n\n'
            "func main() { var value int = pkg.Value(); _ = value }\n",
            encoding="utf-8",
        )
        self.git(root, "add", "--", "go.mod", "nested", "cmd/app/main.go")
        self.git(root, "commit", "-q", "-m", "local replace baseline")

        source.write_text(
            'package pkg\n\nfunc Value() string { return "candidate" }\n',
            encoding="utf-8",
        )
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\nfunc Value() string { return \"root body\" }\n",
            encoding="utf-8",
        )
        self.git(root, "add", "--", "nested/pkg/pkg.go", "lib/lib.go")
        source.write_text(
            "package pkg\n\nfunc Value() int { return 1 }\n", encoding="utf-8")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot use pkg.Value()", result.stderr)

    def test_local_replace_outside_staged_snapshot_is_rejected(self) -> None:
        root = self.make_fixture()
        external = Path(tempfile.mkdtemp(prefix="go-index-external-module-"))
        self.addCleanup(shutil.rmtree, external)
        (external / "go.mod").write_text(
            "module example.test/external\n\ngo 1.26\n", encoding="utf-8")
        (external / "external.go").write_text(
            "package external\n\nfunc Value() int { return 1 }\n", encoding="utf-8")
        (root / "go.mod").write_text(
            "module example.test/indexclosure\n\ngo 1.26\n\n"
            "require example.test/external v0.0.0\n\n"
            f"replace example.test/external => {external}\n",
            encoding="utf-8",
        )
        application = root / "cmd" / "app" / "main.go"
        application.write_text(
            "package main\n\n"
            'import "example.test/external"\n\n'
            "func main() { _ = external.Value() }\n",
            encoding="utf-8",
        )
        self.git(root, "add", "--", "go.mod", "cmd/app/main.go")
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("replace local foge do snapshot staged", result.stderr)

    def test_independent_nested_modules_use_disjoint_surface_workspaces(self) -> None:
        root = self.make_fixture()
        sources: list[Path] = []
        for name in ("first", "second"):
            package = root / name / "pkg"
            package.mkdir(parents=True)
            (root / name / "go.mod").write_text(
                f"module example.test/{name}\n\ngo 1.26\n", encoding="utf-8")
            (root / name / "go.sum").write_bytes(b"")
            source = package / "pkg.go"
            source.write_text(
                "package pkg\n\nfunc private() int { return 1 }\n",
                encoding="utf-8",
            )
            sources.append(source)
        self.git(root, "add", "--", "first", "second")
        self.git(root, "commit", "-q", "-m", "independent modules baseline")
        for index, source in enumerate(sources, start=2):
            source.write_text(
                f"package pkg\n\nfunc private() int {{ return {index} }}\n",
                encoding="utf-8",
            )
        self.git(root, "add", "--", "first/pkg/pkg.go", "second/pkg/pkg.go")
        result = self.run_tool(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("modules=2", result.stdout)
        self.assertIn("closure_mode=direct", result.stdout)

    def test_added_nested_module_also_compiles_parent_topology(self) -> None:
        root = self.make_fixture()
        package = root / "nested" / "pkg"
        package.mkdir(parents=True)
        (package / "pkg.go").write_text(
            "package pkg\n\nfunc Value() int { return 1 }\n", encoding="utf-8")
        application = root / "cmd" / "app" / "main.go"
        application.write_text(
            "package main\n\nimport (\n"
            '\t"example.test/indexclosure/lib"\n'
            '\t"example.test/indexclosure/nested/pkg"\n'
            ")\n\nfunc main() {\n\t_ = lib.Value()\n\t_ = pkg.Value()\n}\n",
            encoding="utf-8")
        self.git(root, "add", "--", "nested/pkg/pkg.go", "cmd/app/main.go")
        self.git(root, "commit", "-q", "-m", "parent owns nested package")

        nested_mod = root / "nested" / "go.mod"
        nested_sum = root / "nested" / "go.sum"
        nested_mod.write_text(
            "module example.test/newnested\n\ngo 1.26\n", encoding="utf-8")
        nested_sum.write_bytes(b"")
        self.git(root, "add", "--", "nested/go.mod", "nested/go.sum")
        nested_mod.unlink()
        nested_sum.unlink()
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "cannot find module providing package "
            "example.test/indexclosure/nested/pkg", result.stderr)

    def test_unrelated_non_go_delta_is_a_fast_authenticated_skip(self) -> None:
        root = self.make_fixture()
        note = root / "docs" / "note.md"
        note.parent.mkdir()
        note.write_text("not a compiler input\n", encoding="utf-8")
        self.git(root, "add", "--", "docs/note.md")
        started = time.monotonic()
        result = self.run_tool(root)
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("go-index-compile-closure: SKIP", result.stdout)
        self.assertIn("reason=no_staged_build_impact", result.stdout)
        self.assertLess(elapsed, 2.0)

    def test_checker_only_delta_is_authenticated_without_full_go_compile(self) -> None:
        root = self.make_fixture()
        checker = root / "tools" / "check-go-compile-closure"
        baseline = checker.read_text(encoding="utf-8")
        checker.write_text(baseline + "\n# staged authority-only change\n", encoding="utf-8")
        self.git(root, "add", "--", "tools/check-go-compile-closure")
        started = time.monotonic()
        result = self.run_tool(root)
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reason=no_staged_build_impact", result.stdout)
        self.assertLess(elapsed, 2.0)

        # A versão fixada vem do próprio checker: um literal aqui apodrece a
        # cada bump da toolchain (ficou em go1.26.5 depois do bump para
        # go1.26.6 e o teste passou a falhar no assertNotEqual, não no gate).
        pinned = re.search(
            r'^PINNED_GOROOT="\$ROOT/\.toolchains/(go\d+\.\d+\.\d+)"$',
            baseline, re.MULTILINE)
        self.assertIsNotNone(pinned, "checker sem PINNED_GOROOT fixado")
        broken = baseline.replace(
            f'PINNED_GOROOT="$ROOT/.toolchains/{pinned.group(1)}"',
            'PINNED_GOROOT="$ROOT/.toolchains/untrusted"',
            1,
        )
        self.assertNotEqual(broken, baseline)
        checker.write_text(broken, encoding="utf-8")
        self.git(root, "add", "--", "tools/check-go-compile-closure")
        rejected = self.run_tool(root)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("contrato da toolchain autenticada", rejected.stderr)

    def test_conflicted_index_is_rejected(self) -> None:
        root = self.make_fixture()
        oid = self.git(root, "rev-parse", "HEAD:lib/lib.go").decode().strip()
        self.git(root, "update-index", "--force-remove", "--", "lib/lib.go")
        conflict = (
            f"100644 {oid} 1\tlib/lib.go\n"
            f"100644 {oid} 2\tlib/lib.go\n"
            f"100644 {oid} 3\tlib/lib.go\n").encode()
        self.git(root, "update-index", "--index-info", input_payload=conflict)
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflito", result.stderr)

    def test_symlink_and_hardlink_index_are_rejected(self) -> None:
        root = self.make_fixture()
        symlink = root / ".git" / "symlink-index"
        symlink.symlink_to(root / ".git" / "index")
        result = self.run_tool(root, index=symlink)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)

        hardlink = root / ".git" / "hardlink-index"
        os.link(root / ".git" / "index", hardlink)
        result = self.run_tool(root, index=hardlink)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular único", result.stderr)

    def test_world_writable_or_executable_index_mode_is_rejected(self) -> None:
        root = self.make_fixture()
        external_index = root / "unsafe-mode.index"
        shutil.copyfile(root / ".git" / "index", external_index)
        for mode in (0o666, 0o755):
            with self.subTest(mode=oct(mode)):
                external_index.chmod(mode)
                result = self.run_tool(root, index=external_index)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("mode gravável/executável inseguro", result.stderr)

    def test_linked_worktree_discovers_its_authoritative_index(self) -> None:
        root = self.make_fixture()
        linked = root.parent / (root.name + "-linked")
        self.addCleanup(shutil.rmtree, linked, True)
        self.git(root, "worktree", "add", "-q", "-b", "fixture-linked",
                 str(linked))
        git_file = linked / ".git"
        self.assertTrue(git_file.is_file())
        result = self.run_tool(linked, discover_index=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_private_index_mutation_during_checker_is_detected(self) -> None:
        root = self.make_fixture()
        staged_runtime = root / "tools" / CHECKER.name
        staged_runtime.write_bytes(
            staged_runtime.read_bytes() +
            b"\nprintf x >>\"$TMPDIR/snapshot.index\"\n")
        staged_runtime.chmod(0o755)
        self.git(root, "add", "--", f"tools/{CHECKER.name}")
        # Force the full compile route (see stage_trivial_go_change) so the
        # staged checker is actually executed and can mutate the private
        # index copy.
        self.stage_trivial_go_change(root)
        result = self.run_tool(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("arquivo mudou durante compilação", result.stderr)

    def test_staged_workspace_and_inherited_go_environment_are_disabled(self) -> None:
        root = self.make_fixture()
        (root / "go.work").write_text(
            "go 1.26\n\nuse ./missing-workspace-module\n", encoding="utf-8")
        library = root / "lib" / "lib.go"
        library.write_text(
            "package lib\n\nfunc Value() string { return \"candidate\" }\n",
            encoding="utf-8",
        )
        self.git(root, "add", "--", "go.work", "lib/lib.go")
        result = self.run_tool(root, environment={
            "GOWORK": str(root / "go.work"),
            "GOFLAGS": "-tags=poisoned",
            "GOENV": str(root / "attacker-goenv"),
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("go-index-compile-closure: PASS", result.stdout)
        self.assertNotIn("go-index-compile-closure: SKIP", result.stdout)

    def test_poisoned_environment_does_not_replace_git_or_go(self) -> None:
        root = self.make_fixture()
        poison = root / "poison"
        poison.mkdir()
        for name in ("git", "go", "python3", "sh"):
            executable = poison / name
            executable.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
            executable.chmod(0o755)
        result = self.run_tool(root, environment={
            "PATH": str(poison),
            "GIT_CONFIG_GLOBAL": str(root / "attacker.gitconfig"),
            "GIT_INDEX_FILE": str(root / "missing-index"),
            "GOFLAGS": "-tags=attacker",
            "GOENV": str(root / "attacker-goenv"),
            "GOWORK": str(root / "attacker.work"),
        })
        self.assertEqual(result.returncode, 0, result.stderr)

    # --- Binário de sistema por symlink de root (uutils na torre, 2026-09-24).
    # /usr/bin/env -> ../lib/cargo/bin/coreutils/env, multicall com 116
    # hardlinks. Os testes montam a mesma forma num diretório temporário; como
    # um teste sem privilégio não cria arquivo de root, o uid corrente passa a
    # valer como root do host só dentro do teste que declara isso.

    def trust_current_uid_as_host_root(self) -> None:
        original = TOOL_GLOBALS["_HOST_ROOT_UIDS"]
        TOOL_GLOBALS["_HOST_ROOT_UIDS"] = original | {os.getuid()}
        self.addCleanup(TOOL_GLOBALS.__setitem__, "_HOST_ROOT_UIDS", original)

    def make_system_binary_tree(self) -> tuple[Path, Path]:
        """bin/env -> ../lib/multicall/env, hardlink de um multicall (nlink 3)."""
        base = Path(tempfile.mkdtemp(prefix="go-index-system-binary-")).resolve()
        self.addCleanup(shutil.rmtree, base)
        bin_dir = base / "bin"
        multicall_dir = base / "lib" / "multicall"
        bin_dir.mkdir()
        multicall_dir.mkdir(parents=True)
        for directory in (base, bin_dir, base / "lib", multicall_dir):
            directory.chmod(0o755)
        multicall = multicall_dir / "multicall"
        multicall.write_bytes(b"#!/bin/sh\nexit 0\n")
        multicall.chmod(0o755)
        target = multicall_dir / "env"
        os.link(multicall, target)
        os.link(multicall, multicall_dir / "dirname")
        link = bin_dir / "env"
        link.symlink_to("../lib/multicall/env")
        return link, target

    def test_root_symlink_to_multilink_system_binary_is_bound(self) -> None:
        self.trust_current_uid_as_host_root()
        link, target = self.make_system_binary_tree()
        self.assertEqual(target.stat().st_nlink, 3)
        bound_path, binding = bind_system_binary(link)
        self.assertEqual(bound_path, target)
        self.assertEqual(binding[0], target.read_bytes())
        self.assertEqual(binding[1][5], 3)
        revalidate_file(
            bound_path, binding, max_bytes=64 * 1024 * 1024,
            allow_multilink=True)
        # Cadeia de dois saltos com alvo absoluto chega ao mesmo arquivo.
        second = link.parent / "env-absoluto"
        second.symlink_to(link)
        self.assertEqual(resolve_system_binary(second), target)
        # O default da revalidação continua exigindo um só link: o binding do
        # multicall só é revalidável pelo caminho que o declarou de sistema.
        with self.assertRaisesRegex(SnapshotError, "regular único"):
            revalidate_file(bound_path, binding, max_bytes=64 * 1024 * 1024)

    def test_system_binary_symlink_not_owned_by_root_is_rejected(self) -> None:
        if os.getuid() in TOOL_GLOBALS["_HOST_ROOT_UIDS"]:
            self.skipTest("rodando como root do host: todo elo é de root")
        link, _ = self.make_system_binary_tree()
        # O elo é do uid corrente, que não é root. A regra do dono do elo é
        # conferida ANTES da do diretório, e cada uma tem diagnóstico próprio.
        with self.assertRaisesRegex(
                SnapshotError,
                "symlink de binário de sistema não pertence a root/host-root: "
                + re.escape(str(link))):
            bind_system_binary(link)
        # Symlink do usuário para o binário REAL do sistema também reprova.
        foreign = link.parent / "git"
        foreign.symlink_to("/usr/bin/git")
        with self.assertRaisesRegex(
                SnapshotError, "symlink de binário de sistema não pertence"):
            resolve_system_binary(foreign)

    def test_system_binary_link_or_target_directory_writable_is_rejected(self) -> None:
        self.trust_current_uid_as_host_root()
        for writable, mode in (("link", 0o757), ("link", 0o775),
                               ("target", 0o757), ("target", 0o775)):
            with self.subTest(directory=writable, mode=oct(mode)):
                link, target = self.make_system_binary_tree()
                directory = link.parent if writable == "link" else target.parent
                directory.chmod(mode)
                with self.assertRaisesRegex(
                        SnapshotError,
                        "diretório de binário de sistema não pertence a "
                        "root/host-root ou é gravável por grupo/outros: "
                        + re.escape(str(directory))):
                    bind_system_binary(link)

    def test_system_binary_target_writable_by_others_is_rejected(self) -> None:
        self.trust_current_uid_as_host_root()
        for mode in (0o757, 0o775, 0o644):
            with self.subTest(mode=oct(mode)):
                link, target = self.make_system_binary_tree()
                target.chmod(mode)
                with self.assertRaisesRegex(
                        SnapshotError,
                        "runtime possui identidade/mode inseguro: "
                        + re.escape(f"{link} -> {target}")):
                    bind_system_binary(link)

    def test_system_binary_symlink_cycle_is_bounded(self) -> None:
        self.trust_current_uid_as_host_root()
        link, _ = self.make_system_binary_tree()
        first = link.parent / "ciclo-a"
        second = link.parent / "ciclo-b"
        first.symlink_to("ciclo-b")
        second.symlink_to("ciclo-a")
        with self.assertRaisesRegex(
                SnapshotError,
                f"excede {MAX_SYSTEM_BINARY_SYMLINK_HOPS} saltos"):
            resolve_system_binary(first)

    def test_multilink_stays_rejected_for_index_and_self_by_default(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="go-index-multilink-")).resolve()
        self.addCleanup(shutil.rmtree, base)
        payload = base / "arquivo"
        payload.write_bytes(b"conteudo\n")
        os.link(payload, base / "outro-nome")
        with self.assertRaisesRegex(SnapshotError, "regular único"):
            safe_payload(payload, max_bytes=1024)
        observed, identity = safe_payload(
            payload, max_bytes=1024, allow_multilink=True)
        self.assertEqual((observed, identity[5]), (b"conteudo\n", 2))

        # Ponta a ponta: o próprio script com um segundo nome reprova antes de
        # qualquer compilação, mesmo sendo idêntico ao blob staged.
        root = self.make_fixture()
        staged_self = root / "tools" / TOOL.name
        os.link(staged_self, root / "segundo-nome-do-script")
        result = subprocess.run(
            [str(staged_self), "--root", str(root),
             "--index-file", str(root / ".git" / "index"),
             "--runtime-root", str(REPO_ROOT)],
            cwd=root, env={"HOME": os.environ.get("HOME", "/tmp"),
                           "PATH": "/usr/bin:/bin", "LC_ALL": "C"},
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, check=False)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(
            f"arquivo não é regular único ou excede limite: {staged_self}",
            result.stderr)


if __name__ == "__main__":
    unittest.main()
