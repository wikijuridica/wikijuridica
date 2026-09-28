from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import types
import unittest
import zipfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT / "tools" / "commit-verified-v2-workflow-results"
LOADER = importlib.machinery.SourceFileLoader(
    "commit_verified_v2_workflow_results_tests", os.fspath(TOOL_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = TOOL
LOADER.exec_module(TOOL)
GUARD_PATH = ROOT / "tools" / "check-v2-finalized-commit"
GUARD_LOADER = importlib.machinery.SourceFileLoader(
    "check_v2_finalized_commit_tests", os.fspath(GUARD_PATH))
GUARD_SPEC = importlib.util.spec_from_loader(GUARD_LOADER.name, GUARD_LOADER)
GUARD = importlib.util.module_from_spec(GUARD_SPEC)
sys.modules[GUARD_LOADER.name] = GUARD
GUARD_LOADER.exec_module(GUARD)


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class FakeTransaction:
    def __init__(
        self,
        root: pathlib.Path,
        target: pathlib.Path,
        target_payload: bytes,
        dependencies: dict[pathlib.Path, str],
    ) -> None:
        self.root = root
        self.kind = "mass"
        self.report = {
            "audit_merit_verified": False,
            "files": [{
                "file": target.relative_to(root).as_posix(),
                "sha256": digest(target_payload),
                "lines": 1,
            }],
            "required_artifacts": [],
        }
        self.dependencies = dict(dependencies)
        self.live_targets = {target: digest(target_payload)}
        self.revalidations = 0

    def revalidate(self) -> None:
        self.revalidations += 1
        for path, expected in {**self.dependencies, **self.live_targets}.items():
            if digest(path.read_bytes()) != expected:
                raise TOOL.CommitVerificationError(
                    f"fixture drift: {path}")


class PassingClosedAuditor:
    ROOT = None

    @staticmethod
    def audit_against_stock_legacy(path: str, expect_n: int | None = None):
        return {
            "file": os.path.relpath(path, PassingClosedAuditor.ROOT),
            "pages": expect_n,
            "active_pages": expect_n,
            "defects": {},
            "ok": True,
        }


class PlumbingCommitFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        self.target = (
            self.root / "data" / "editorial" / "v2_pages" /
            "civil-commit-01.jsonl")
        self.dependency = (
            self.root / "scripts" / "workflows" / "writing-mass-todo.js")
        self.unrelated = self.root / "notes.txt"
        for path, payload in (
            (self.target, b'{"intent_id":"intent-old"}\n'),
            (self.dependency, b"const batches = []\n"),
            (self.unrelated, b"base\n"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        self.finalized_guard = (
            self.root / "tools" / "check-v2-finalized-commit")
        self.finalized_guard.parent.mkdir(parents=True, exist_ok=True)
        self.finalized_guard.write_bytes(
            b"#!/usr/bin/python3 -I\nraise SystemExit(0)\n")
        self.finalized_guard.chmod(0o755)
        self.write_hook(self.passing_hook())
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("add", "--", ".")
        self.git("commit", "-q", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        previous_heavy_lock = TOOL.HEAVY_AUDIT_LOCK
        TOOL.HEAVY_AUDIT_LOCK = self.root / "heavy-audit.lock"
        self.addCleanup(
            setattr, TOOL, "HEAVY_AUDIT_LOCK", previous_heavy_lock)
        previous_auditor = TOOL._LOADED_AUDITOR
        TOOL._LOADED_AUDITOR = PassingClosedAuditor
        self.addCleanup(setattr, TOOL, "_LOADED_AUDITOR", previous_auditor)

    def passing_hook(self) -> str:
        return (
            "#!/bin/sh\n"
            "set -eu\n"
            'ROOT="$(CDPATH=\'\' cd -- "$(dirname -- "$0")/.." && pwd)"\n'
            '[ "$0" = "$ROOT/.githooks/pre-commit" ]\n'
            ': "${GIT_INDEX_FILE:?private index required}"\n'
            "/usr/bin/git -C \"$ROOT\" --no-replace-objects "
            "-c core.hooksPath=/dev/null diff --cached --quiet "
            "-- data/editorial/v2_pages && exit 41\n"
            "test $? -eq 1\n"
        )

    def write_hook(self, payload: str) -> None:
        hook = self.root / ".githooks" / "pre-commit"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text(payload, encoding="utf-8")
        hook.chmod(0o755)

    def commit_hook(self, payload: str) -> None:
        self.write_hook(payload)
        self.git("add", "--", ".githooks/pre-commit")
        self.git("commit", "-q", "-m", "fixture: change hook", "--",
                 ".githooks/pre-commit")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(
        self, *arguments: str, input_payload: bytes | None = None,
    ) -> str:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), *arguments],
            input=input_payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            self.fail(
                f"git {' '.join(arguments)} failed: " +
                completed.stderr.decode("utf-8", errors="replace"))
        return completed.stdout.decode("utf-8", errors="strict")

    def git_may_fail(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def transaction(self, target_payload: bytes) -> FakeTransaction:
        self.target.write_bytes(target_payload)
        return FakeTransaction(
            self.root,
            self.target,
            target_payload,
            {self.dependency: digest(self.dependency.read_bytes())},
        )

    def prepare_index_fixture(
        self, epoch: TOOL.CommitEpoch, workspace: pathlib.Path,
    ) -> TOOL.PreparedMainIndex:
        start_ticks = TOOL._proc_start_ticks(os.getpid())
        self.assertIsNotNone(start_ticks)
        lease = TOOL.SingleFlightLease(
            directory=TOOL._singleflight_directory(self.root), descriptor=-1,
            fingerprint=digest(os.urandom(32)), run_id=os.urandom(16).hex(),
            pid=os.getpid(), start_ticks=start_ticks,
            started_unix_ns=time.time_ns(), phase="prepare_index",
        )
        previous = TOOL._ACTIVE_SINGLEFLIGHT
        TOOL._ACTIVE_SINGLEFLIGHT = lease
        try:
            return TOOL._prepare_main_index(
                epoch, workspace, epoch.expected_head, "mass", lease)
        finally:
            TOOL._ACTIVE_SINGLEFLIGHT = previous

    def sigkill_at_prepared_boundary(
        self, boundary: str, *, target_payload: bytes | None = None,
    ) -> None:
        payload = target_payload or b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(payload)
        read_fd, write_fd = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            original = TOOL._prepared_index_boundary

            def stop_at_boundary(prepared, observed: str) -> None:
                original(prepared, observed)
                if observed == boundary:
                    os.write(write_fd, b"ready\n")
                    while True:
                        signal.pause()

            TOOL._prepared_index_boundary = stop_at_boundary
            try:
                TOOL._commit_transaction(
                    transaction, "content(v2): SIGKILL at " + boundary)
            except BaseException:
                os._exit(92)
            os._exit(93)
        os.close(write_fd)
        try:
            self.assertEqual(os.read(read_fd, 6), b"ready\n")
        finally:
            os.close(read_fd)
        os.kill(child, signal.SIGKILL)
        waited, status = os.waitpid(child, 0)
        self.assertEqual(waited, child)
        self.assertTrue(os.WIFSIGNALED(status))
        self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)

    def sigkill_at_prepared_recovery_boundary(self, boundary: str) -> None:
        read_fd, write_fd = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            original = TOOL._prepared_recovery_boundary

            def stop_at_boundary(artifact, observed: str) -> None:
                original(artifact, observed)
                if observed == boundary:
                    os.write(write_fd, b"ready\n")
                    while True:
                        signal.pause()

            TOOL._prepared_recovery_boundary = stop_at_boundary
            try:
                TOOL._recover_prepared_main_index(self.root)
            except BaseException:
                os._exit(92)
            os._exit(93)
        os.close(write_fd)
        try:
            self.assertEqual(os.read(read_fd, 6), b"ready\n")
        finally:
            os.close(read_fd)
        os.kill(child, signal.SIGKILL)
        waited, status = os.waitpid(child, 0)
        self.assertEqual(waited, child)
        self.assertTrue(os.WIFSIGNALED(status))
        self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)

    def canonical_record(
        self, intent: str, *, title: str = "Guia fechado", public: bool = False,
    ) -> bytes:
        return (json.dumps({
            "intent_id": intent,
            "public": public,
            "publication_allowed": False,
            "publication_candidate": False,
            "render_allowed": False,
            "sitemap_allowed": False,
            "indexable": False,
            "index_policy": "noindex",
            "approval": False,
            "public_path": "",
            "title": title,
        }, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

    def install_canonical_repair_parent(
        self, old_intent: str = "seguro-marítimo-carga",
    ) -> tuple[bytes, bytes]:
        old_payload = self.canonical_record(old_intent)
        new_intent = TOOL._canonical_intent_fold(old_intent)
        new_payload = old_payload.replace(
            old_intent.encode("utf-8"), new_intent.encode("utf-8"), 1)
        self.target.write_bytes(old_payload)
        self.git("add", "--", self.target.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: accented parent", "--",
                 self.target.relative_to(self.root).as_posix())
        self.base = self.git("rev-parse", "HEAD").strip()
        self.target.write_bytes(new_payload)
        return old_payload, new_payload

    def add_raw_artifact(
        self, transaction: FakeTransaction, payload: bytes,
    ) -> tuple[pathlib.Path, str]:
        artifact_sha = digest(payload)
        relative = (
            "data/editorial/v2_raw_recovery_preimages/" +
            artifact_sha + ".raw")
        artifact = self.root / relative
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(payload)
        transaction.report["required_artifacts"] = [{
            "file": relative,
            "sha256": artifact_sha,
            "role": "raw_recovery_preimage_evidence",
        }]
        transaction.dependencies[artifact] = artifact_sha
        return artifact, relative

    def review_transaction(
        self, target_payload: bytes, evidence_payload: bytes = b"{}\n",
    ) -> tuple[FakeTransaction, pathlib.Path, str]:
        transaction = self.transaction(target_payload)
        transaction.kind = "review"
        evidence_relative = (
            "data/source-registry/"
            "v2_source_provenance_live_evidence_sets/exact-" +
            "1" * 64 + ".jsonl")
        evidence = self.root / evidence_relative
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_bytes(evidence_payload)
        evidence_sha = digest(evidence_payload)
        transaction.report["files"][0]["source_provenance_evidence"] = {
            "file": evidence_relative,
            "sha256": evidence_sha,
        }
        transaction.report["required_artifacts"] = [{
            "file": evidence_relative,
            "sha256": evidence_sha,
            "role": "source_provenance_evidence",
        }]
        transaction.dependencies[evidence] = evidence_sha
        return transaction, evidence, evidence_relative

    def write_private_provenance_checker(
        self, snapshot_root: pathlib.Path, evidence_relative: str,
        *, status: int = 0,
    ) -> pathlib.Path:
        checker = snapshot_root / "tools" / "audit-v2-source-provenance"
        checker.parent.mkdir(parents=True, exist_ok=True)
        checker.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            f"[ {status} -eq 0 ] || exit {status}\n"
            "printf '%s\\n' 'v2-source-provenance: "
            "check=current-selection-pass release_eligible=false scope=all "
            "records=1 verified=1 blocked=0 path=" + evidence_relative +
            " publication=false'\n",
            encoding="utf-8",
        )
        checker.chmod(0o500)
        return checker

    def test_exact_plumbing_commit_preserves_unrelated_stage(self):
        staged = b"staged-for-another-agent\n"
        self.unrelated.write_bytes(staged)
        self.git("add", "--", "notes.txt")
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        artifact_payload = b'{"intent_id":"invalid-preimage"}'
        _, artifact_relative = self.add_raw_artifact(
            transaction, artifact_payload)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = TOOL._commit_transaction(
                transaction, "content(v2): integrate exact plumbing wave")
        self.assertEqual(status, 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report["commit_created"])
        self.assertFalse(report["index_reconciliation_required"])
        self.assertEqual(report["parent"], self.base)
        self.assertEqual(report["commit"], self.git("rev-parse", "HEAD").strip())
        self.assertEqual(
            self.git("show", "HEAD:data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(), target_payload)
        self.assertEqual(
            self.git("show", "HEAD:" + artifact_relative).encode(),
            artifact_payload)
        self.assertEqual(
            self.git("diff", "--cached", "--name-only").splitlines(),
            ["notes.txt"])
        self.assertEqual(self.git("show", ":notes.txt").encode(), staged)
        self.assertGreaterEqual(transaction.revalidations, 2)

    def test_finalized_guard_executes_expected_head_not_mutable_worktree(self):
        marker = self.root / "mutable-finalized-guard-ran"
        self.finalized_guard.write_text(
            "#!/usr/bin/python3 -I\n"
            "import pathlib\n"
            f"pathlib.Path({os.fspath(marker)!r}).write_text('forged')\n"
            "raise SystemExit(73)\n",
            encoding="utf-8",
        )
        self.finalized_guard.chmod(0o755)
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(TOOL._commit_transaction(
                transaction,
                "content(v2): expected head finalized guard wins"), 0)
        self.assertFalse(marker.exists())
        self.assertIn(
            "raise SystemExit(0)",
            self.git("show", "HEAD^:tools/check-v2-finalized-commit"))

    def test_failure_before_cas_touches_neither_head_index_nor_untracked_stage(self):
        self.commit_hook("#!/bin/sh\nexit 19\n")
        self.unrelated.write_bytes(b"keep-staged\n")
        self.git("add", "--", "notes.txt")
        index_path = pathlib.Path(
            self.git("rev-parse", "--git-path", "index").strip())
        if not index_path.is_absolute():
            index_path = self.root / index_path
        index_before = index_path.read_bytes()
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        _, artifact_relative = self.add_raw_artifact(
            transaction, b"raw-invalid-preimage")
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "pre-commit reprovou"):
            TOOL._commit_transaction(
                transaction, "content(v2): pre CAS failure is atomic")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual(index_path.read_bytes(), index_before)
        self.assertEqual(
            self.git("diff", "--cached", "--name-only").splitlines(),
            ["notes.txt"])
        self.assertEqual(
            self.git("ls-files", "--stage", "--", artifact_relative), "")

    def test_foreign_heavy_lock_is_busy_other_and_maps_to_exit_75(self):
        # Espera bounded existe somente no JOIN da mesma fingerprint. Um lock
        # pesado externo/diferente nunca serializa uma segunda compilação cega.
        lock_path = TOOL.HEAVY_AUDIT_LOCK
        descriptor = os.open(
            lock_path,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
        )
        TOOL.fcntl.flock(descriptor, TOOL.fcntl.LOCK_EX | TOOL.fcntl.LOCK_NB)
        try:
            transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
            with self.assertRaisesRegex(
                    TOOL.CommitBusy, "BUSY_OTHER heavy_lock"):
                TOOL._commit_transaction(
                    transaction, "content(v2): busy other on heavy lock")
        finally:
            TOOL.fcntl.flock(descriptor, TOOL.fcntl.LOCK_UN)
            os.close(descriptor)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        with mock.patch.object(
                TOOL, "main", side_effect=TOOL.CommitBusy("heavy busy")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(TOOL._entrypoint([]), 75)

    def test_head_drift_after_private_build_aborts_before_private_audit(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        original = TOOL._materialize_gate_snapshot_root
        concurrent_tree = self.git("rev-parse", self.base + "^{tree}").strip()
        concurrent = self.git(
            "commit-tree", concurrent_tree, "-p", self.base,
            input_payload=b"concurrent before private audit\n",
        ).strip()

        def build_then_advance(*arguments, **kwargs):
            result = original(*arguments, **kwargs)
            self.git("update-ref", "HEAD", concurrent, self.base)
            return result

        with mock.patch.object(
                TOOL, "_materialize_gate_snapshot_root",
                side_effect=build_then_advance), \
                mock.patch.object(
                    TOOL, "_audit_candidate_tree") as private_audit, \
                self.assertRaisesRegex(TOOL.CommitBusy, "durante o build"):
            TOOL._commit_transaction(
                transaction, "content(v2): abort stale epoch after build")
        private_audit.assert_not_called()
        probe = os.open(TOOL.HEAVY_AUDIT_LOCK, os.O_RDWR | os.O_CLOEXEC)
        try:
            TOOL.fcntl.flock(
                probe, TOOL.fcntl.LOCK_EX | TOOL.fcntl.LOCK_NB)
        finally:
            TOOL.fcntl.flock(probe, TOOL.fcntl.LOCK_UN)
            os.close(probe)

    def test_dependency_mutated_between_gate_and_cas_prevents_ref(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        index_before = (self.root / ".git" / "index").read_bytes()
        original = TOOL._run_pre_commit_snapshot

        def gate_then_mutate(*arguments, **kwargs):
            original(*arguments, **kwargs)
            self.dependency.write_bytes(b"drift-after-gate\n")

        with mock.patch.object(
                TOOL, "_run_pre_commit_snapshot", side_effect=gate_then_mutate):
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "fixture drift"):
                TOOL._commit_transaction(
                    transaction, "content(v2): reject dependency drift")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual((self.root / ".git" / "index").read_bytes(), index_before)

    def test_final_guard_dependency_drift_aborts_before_cas_and_unlocks_index(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        original = TOOL._run_finalized_commit_guard
        cas = mock.Mock()

        def guard_then_mutate(*arguments, **kwargs):
            original(*arguments, **kwargs)
            self.dependency.write_bytes(b"drift-after-final-guard\n")

        with mock.patch.object(
                TOOL, "_run_finalized_commit_guard",
                side_effect=guard_then_mutate), \
                mock.patch.object(TOOL, "_update_ref_cas", cas), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "fixture drift"):
            TOOL._commit_transaction(
                transaction,
                "content(v2): reject drift after finalized guard")
        cas.assert_not_called()
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(
            list((self.root / ".git").glob("index.prepared-*")), [])

    def test_final_guard_failure_retry_does_not_accumulate_prepared_artifacts(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        message = "content(v2): retry clean final guard failure"
        original = TOOL._run_finalized_commit_guard
        calls = 0

        def fail_once(*arguments, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TOOL.CommitVerificationError("fixture final guard failure")
            return original(*arguments, **kwargs)

        with mock.patch.object(
                TOOL, "_run_finalized_commit_guard", side_effect=fail_once), \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "fixture final guard"):
            TOOL._commit_transaction(transaction, message)
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(
            list((self.root / ".git").glob("index.prepared-*")), [])
        epoch = TOOL._build_commit_epoch(transaction, message)
        fingerprint = TOOL._singleflight_fingerprint(
            epoch, message, transaction.kind)
        terminal = TOOL._read_singleflight_terminal(
            TOOL._singleflight_directory(self.root), fingerprint)
        self.assertIsNotNone(terminal)
        assert terminal is not None
        output = io.StringIO()
        with mock.patch.object(
                TOOL, "_run_finalized_commit_guard", side_effect=fail_once), \
                contextlib.redirect_stdout(output), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(TOOL._commit_transaction(
                transaction, message,
                retry_failed=terminal["result_sha256"]), 0)
        self.assertTrue(json.loads(output.getvalue())["commit_created"])
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(
            list((self.root / ".git").glob("index.prepared-*")), [])

    def test_concurrent_head_cas_leaves_known_dangling_commit(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        tree = self.git("rev-parse", self.base + "^{tree}").strip()
        concurrent = self.git(
            "commit-tree", tree, "-p", self.base,
            input_payload=b"concurrent\n").strip()
        captured: list[str] = []
        original = TOOL._update_ref_cas

        def lose_cas(epoch, commit: str) -> None:
            captured.append(commit)
            self.git("update-ref", epoch.expected_ref, concurrent,
                     epoch.expected_head)
            original(epoch, commit)

        with mock.patch.object(TOOL, "_update_ref_cas", side_effect=lose_cas):
            with self.assertRaises(TOOL.CommitBusy):
                TOOL._commit_transaction(
                    transaction, "content(v2): preserve dangling on CAS loss")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), concurrent)
        self.assertEqual(len(captured), 1)
        self.assertEqual(self.git("cat-file", "-t", captured[0]).strip(), "commit")
        self.assertEqual(
            self.git("show", "HEAD:data/editorial/v2_pages/"
                     "civil-commit-01.jsonl"),
            '{"intent_id":"intent-old"}\n')
        self.assertTrue((self.root / ".git" / "index.lock").is_file())

    def test_update_ref_failure_with_exact_old_ref_is_retryable_and_unlocks(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        message = "content(v2): exact old ref proves CAS not applied"
        with mock.patch.object(
                TOOL, "_update_ref_cas",
                side_effect=TOOL.CommitBusy("fixture update-ref failure")), \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaisesRegex(TOOL.CommitBusy, "fixture"):
            TOOL._commit_transaction(transaction, message)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(
            list((self.root / ".git").glob("index.prepared-*")), [])
        epoch = TOOL._build_commit_epoch(transaction, message)
        fingerprint = TOOL._singleflight_fingerprint(
            epoch, message, transaction.kind)
        terminal = TOOL._read_singleflight_terminal(
            TOOL._singleflight_directory(self.root), fingerprint)
        self.assertIsNotNone(terminal)
        self.assertFalse(terminal["cas_may_have_applied"])

    def test_private_gate_capability_reports_exact_failed_invariant(self):
        with tempfile.TemporaryDirectory() as raw:
            snapshot = pathlib.Path(raw) / "gate-root"
            tools = snapshot / "tools"
            tools.mkdir(parents=True, mode=0o700)
            os.chmod(snapshot, 0o700)
            pointer = snapshot / ".git"
            pointer.write_bytes(b"gitdir: /tmp/fixture.git\n")
            pointer.chmod(0o400)
            for binary_name, _ in TOOL.GATE_COMMANDS:
                binary = tools / binary_name
                binary.write_bytes(b"\x7fELFfixture")
                binary.chmod(0o500)
            for tool_name in TOOL.HOOK_RUNTIME_TOOLS:
                helper = tools / tool_name
                helper.write_bytes(b"#!/bin/sh\nexit 0\n")
                helper.chmod(0o500)
            TOOL._assert_private_v2_gate_capability(snapshot)
            missing = tools / TOOL.HOOK_RUNTIME_TOOLS[0]
            missing.unlink()
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError,
                    r"hook_tool:check-go-index-compile-closure"):
                TOOL._assert_private_v2_gate_capability(snapshot)
            missing.write_bytes(b"#!/bin/sh\nexit 0\n")
            missing.chmod(0o500)
            os.chmod(snapshot, 0o755)
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError,
                    r"directory_mode:gate-root:0755"):
                TOOL._assert_private_v2_gate_capability(snapshot)

    def test_hook_runtime_snapshot_closes_0500_without_changing_git_mode(self):
        payload = b"#!/bin/sh\nexit 0\n"
        source_paths: list[pathlib.Path] = []
        for tool_name in TOOL.HOOK_RUNTIME_TOOLS:
            source = self.root / "tools" / tool_name
            source.write_bytes(payload)
            source.chmod(0o755)
            source_paths.append(source)
        relatives = [
            path.relative_to(self.root).as_posix() for path in source_paths]
        self.git("add", "--", *relatives)
        self.git("commit", "-q", "-m", "fixture: tracked runtime helpers", "--",
                 *relatives)

        with tempfile.TemporaryDirectory() as raw:
            snapshot = pathlib.Path(raw) / "gate-root"
            tools = snapshot / "tools"
            tools.mkdir(parents=True, mode=0o700)
            os.chmod(snapshot, 0o700)
            os.chmod(tools, 0o700)
            pointer = snapshot / ".git"
            pointer.write_bytes(b"gitdir: /tmp/fixture.git\n")
            pointer.chmod(0o400)
            for binary_name, _ in TOOL.GATE_COMMANDS:
                binary = tools / binary_name
                binary.write_bytes(b"\x7fELFfixture")
                binary.chmod(0o500)
            bindings: dict[pathlib.Path, str] = {}
            for tool_name in TOOL.HOOK_RUNTIME_TOOLS:
                helper = tools / tool_name
                helper.write_bytes(payload)
                helper.chmod(0o755)
                bindings[helper] = digest(payload)
            TOOL._normalize_private_hook_runtime_tools(snapshot, bindings)
            TOOL._assert_private_v2_gate_capability(snapshot)
            for helper in bindings:
                self.assertEqual(stat.S_IMODE(helper.stat().st_mode), 0o500)
                self.assertEqual(bindings[helper], digest(payload))

        for source, relative in zip(source_paths, relatives):
            self.assertEqual(stat.S_IMODE(source.stat().st_mode), 0o755)
            self.assertTrue(self.git(
                "ls-files", "--stage", "--", relative).startswith("100755 "))

    def test_later_head_advance_does_not_invalidate_known_commit_oid(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        original = TOOL._update_ref_cas
        later: list[str] = []

        def cas_then_advance(
            epoch, commit: str,
        ) -> None:
            original(epoch, commit)
            tree = self.git("rev-parse", commit + "^{tree}").strip()
            child = self.git(
                "commit-tree", tree, "-p", commit,
                input_payload=b"later\n").strip()
            self.git("update-ref", "HEAD", child, commit)
            later.append(child)

        output = io.StringIO()
        with mock.patch.object(
                TOOL, "_update_ref_cas", side_effect=cas_then_advance), \
                contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): known oid survives later advance"), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), later[0])
        self.assertEqual(
            self.git("rev-parse", later[0] + "^1").strip(), report["commit"])
        self.assertEqual(self.git("cat-file", "-t", report["commit"]).strip(),
                         "commit")
        self.assertTrue(report["index_reconciliation_required"])
        self.assertTrue((self.root / ".git" / "index.lock").is_file())

    def test_explicit_identity_and_no_commit_msg_or_post_commit_hooks(self):
        markers = []
        hooks = self.root / ".git" / "hooks"
        for name in ("commit-msg", "post-commit"):
            marker = self.root / (name + ".ran")
            markers.append(marker)
            hook = hooks / name
            hook.write_text(
                "#!/bin/sh\n/usr/bin/touch " + os.fspath(marker) + "\n",
                encoding="utf-8")
            hook.chmod(0o755)
        self.git_may_fail("config", "--unset-all", "user.name")
        self.git_may_fail("config", "--unset-all", "user.email")
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        with mock.patch.dict(os.environ, {}, clear=True), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): explicit deterministic identity"), 0)
        identity = self.git(
            "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce", "HEAD")
        self.assertEqual(
            identity.strip().split("\x00"),
            [TOOL.AUTHOR_NAME, TOOL.AUTHOR_EMAIL,
             TOOL.AUTHOR_NAME, TOOL.AUTHOR_EMAIL])
        self.assertFalse(any(marker.exists() for marker in markers))

    def test_index_lock_is_prepared_and_held_across_ref_cas(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        original = TOOL._update_ref_cas
        probes: list[subprocess.CompletedProcess[bytes]] = []

        def probe_then_cas(epoch, commit: str) -> None:
            self.assertTrue((self.root / ".git" / "index.lock").is_file())
            probes.append(self.git_may_fail(
                "commit", "-q", "-m", "must-not-race-index-lock"))
            original(epoch, commit)

        output = io.StringIO()
        with mock.patch.object(
                TOOL, "_update_ref_cas", side_effect=probe_then_cas), \
                contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): hold prepared index across CAS"), 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report["commit_created"])
        self.assertFalse(report["index_reconciliation_required"])
        self.assertEqual(len(probes), 1)
        self.assertNotEqual(probes[0].returncode, 0)
        self.assertIn(b"index.lock", probes[0].stderr)
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), report["commit"])

    def test_lost_cas_response_recovers_from_new_ref_and_promotes_index(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        original = TOOL._update_ref_cas

        def apply_then_lose_response(epoch, commit: str) -> None:
            original(epoch, commit)
            raise OSError("fixture response lost after durable CAS")

        output = io.StringIO()
        with mock.patch.object(
                TOOL, "_update_ref_cas", side_effect=apply_then_lose_response), \
                contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): recover lost CAS response"), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), report["commit"])
        self.assertFalse(report["index_reconciliation_required"])
        self.assertEqual(
            self.git("show", ":data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(), target_payload)
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_process_crash_after_cas_leaves_fsynced_prepared_index_lock(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        child = os.fork()
        if child == 0:
            original = TOOL._update_ref_cas

            def apply_then_crash(epoch, commit: str) -> None:
                original(epoch, commit)
                os._exit(91)

            TOOL._update_ref_cas = apply_then_crash
            try:
                TOOL._commit_transaction(
                    transaction, "content(v2): crash leaves prepared index")
            except BaseException:
                os._exit(92)
            os._exit(93)
        waited, status = os.waitpid(child, 0)
        self.assertEqual(waited, child)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 91)
        new_head = self.git("rev-parse", "HEAD").strip()
        self.assertNotEqual(new_head, self.base)
        self.assertEqual(
            self.git("show", "HEAD:data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(), target_payload)
        lock_path = self.root / ".git" / "index.lock"
        self.assertTrue(lock_path.is_file())
        environment = dict(os.environ)
        environment["GIT_INDEX_FILE"] = str(lock_path)
        staged = subprocess.run(
            ["/usr/bin/git", "-C", str(self.root), "show",
             ":data/editorial/v2_pages/civil-commit-01.jsonl"],
            env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False)
        self.assertEqual(staged.returncode, 0, staged.stderr)
        self.assertEqual(staged.stdout, target_payload)
        self.assertNotEqual(
            self.git_may_fail(
                "commit", "-q", "-m", "must-fail-closed-after-crash"
            ).returncode,
            0,
        )
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["recovered"])
        self.assertEqual(report["head"], new_head)
        self.assertEqual(report["parent"], self.base)
        self.assertFalse(lock_path.exists())
        self.assertEqual(
            self.git("show", ":data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(),
            target_payload,
        )
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_sigkill_after_nonce_before_sidecar_reclaims_exact_bound_name(self):
        self.sigkill_at_prepared_boundary("post_nonce")
        git_directory = self.root / ".git"
        nonces = list(git_directory.glob("index.prepared-*"))
        self.assertEqual(len(nonces), 1)
        self.assertFalse(nonces[0].name.endswith(".json"))
        active = TOOL._read_control_json(
            TOOL._singleflight_directory(self.root) / "active.json",
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        self.assertIsNotNone(active)
        assert active is not None
        self.assertEqual(active["prepared_nonce_name"], nonces[0].name)
        self.assertEqual(
            active["prepared_nonce_identity"],
            list(TOOL._descriptor_content_identity(nonces[0].stat())),
        )
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertEqual(report["orphan_nonces_reclaimed"], 1)
        self.assertTrue(report["reclaimed_pre_cas"])
        self.assertEqual(list(git_directory.glob("index.prepared-*")), [])

    def test_orphan_gc_never_selects_strange_nonce_from_same_run(self):
        self.sigkill_at_prepared_boundary("post_nonce")
        git_directory = self.root / ".git"
        active = TOOL._read_control_json(
            TOOL._singleflight_directory(self.root) / "active.json",
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        self.assertIsNotNone(active)
        assert active is not None
        bound = git_directory / active["prepared_nonce_name"]
        strange = git_directory / (
            "index.prepared-" + active["run_id"] + "-" + "f" * 32)
        strange.write_bytes(b"foreign same-run nonce\n")
        strange.chmod(0o600)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "outro nonce do mesmo run"):
            TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(bound.exists())
        self.assertTrue(strange.exists())

    def test_orphan_gc_rejects_exact_name_inode_replacement(self):
        self.sigkill_at_prepared_boundary("post_nonce")
        directory = TOOL._singleflight_directory(self.root)
        active = TOOL._read_control_json(
            directory / "active.json",
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        self.assertIsNotNone(active)
        assert active is not None
        self.assertIsNotNone(active["prepared_nonce_identity"])
        bound = self.root / ".git" / active["prepared_nonce_name"]
        bound.unlink()
        replacement = b"foreign exact-name inode replacement\n"
        bound.write_bytes(replacement)
        bound.chmod(0o600)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "identidade autenticada"):
            TOOL._recover_prepared_main_index(self.root)
        self.assertEqual(bound.read_bytes(), replacement)

    def test_legacy_active_without_exact_nonce_never_enumerates_or_unlinks(self):
        self.sigkill_at_prepared_boundary("post_nonce")
        directory = TOOL._singleflight_directory(self.root)
        active_path = directory / "active.json"
        active = TOOL._read_control_json(
            active_path, max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        self.assertIsNotNone(active)
        assert active is not None
        bound = self.root / ".git" / active.pop("prepared_nonce_name")
        active.pop("prepared_nonce_identity")
        TOOL._atomic_control_write(
            active_path, TOOL._canonical_json(active),
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "exatamente um prepared"):
            TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(bound.exists())

    def test_sigkill_before_index_lock_link_is_reclaimable(self):
        self.sigkill_at_prepared_boundary("before_link")
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["reclaimed_pre_cas"])
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual(list((self.root / ".git").glob(
            "index.prepared-*.json")), [])

    def test_sigkill_after_index_lock_link_is_reclaimable(self):
        self.sigkill_at_prepared_boundary("post_link")
        lock_path = self.root / ".git" / "index.lock"
        self.assertTrue(lock_path.is_file())
        sidecars = list((self.root / ".git").glob(
            "index.prepared-*.json"))
        self.assertEqual(len(sidecars), 1)
        nonce = sidecars[0].with_suffix("")
        for private_path in (sidecars[0], nonce, lock_path):
            info = private_path.stat()
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)
            self.assertEqual(info.st_uid, os.geteuid())
        self.assertEqual(nonce.stat().st_ino, lock_path.stat().st_ino)
        self.assertEqual(nonce.stat().st_nlink, 2)
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["reclaimed_pre_cas"])
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_sigkill_after_prepared_payload_is_reclaimable(self):
        self.sigkill_at_prepared_boundary("post_prepared")
        lock_path = self.root / ".git" / "index.lock"
        self.assertEqual(lock_path.stat().st_nlink, 2)
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["reclaimed_pre_cas"])
        self.assertFalse(lock_path.exists())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_new_generation_reclaims_dead_pre_cas_lock_without_deadlock(self):
        self.sigkill_at_prepared_boundary("post_prepared")
        self.assertTrue((self.root / ".git" / "index.lock").is_file())
        transaction = self.transaction(
            b'{"intent_id":"intent-new-generation"}\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                transaction,
                "content(v2): reclaim prior dead pre-CAS generation"), 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report["commit_created"])
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), report["commit"])

    def foreign_index_lock_lease(self) -> TOOL.SingleFlightLease:
        """Producer lease vivo enquanto um index.lock ALHEIO ocupa o repo."""
        start_ticks = TOOL._proc_start_ticks(os.getpid())
        self.assertIsNotNone(start_ticks)
        descriptor = os.open(
            self.root / ".git" / "index", os.O_RDONLY | os.O_CLOEXEC)
        self.addCleanup(os.close, descriptor)
        lease = TOOL.SingleFlightLease(
            directory=TOOL._singleflight_directory(self.root),
            descriptor=descriptor,
            fingerprint=digest(os.urandom(32)),
            run_id=os.urandom(16).hex(),
            pid=os.getpid(),
            start_ticks=start_ticks,
            started_unix_ns=time.time_ns(),
            phase="prepare_index",
        )
        previous = TOOL._ACTIVE_SINGLEFLIGHT
        TOOL._ACTIVE_SINGLEFLIGHT = lease
        self.addCleanup(setattr, TOOL, "_ACTIVE_SINGLEFLIGHT", previous)
        return lease

    def test_foreign_git_index_lock_is_busy_not_deterministic_failure(self):
        payload = b"foreign git transaction\n"
        lock_path = self.root / ".git" / "index.lock"
        lock_path.write_bytes(payload)
        self.foreign_index_lock_lease()
        with self.assertRaises(TOOL.CommitBusy) as caught:
            TOOL._reclaim_stale_pre_cas_lock(self.root)
        self.assertIn("transação Git alheia", str(caught.exception))
        # BUSY é transitório (exit 75) e nunca ambíguo quanto ao CAS: a
        # contenção acontece antes de qualquer update-ref.
        self.assertFalse(caught.exception.cas_may_have_applied)
        # O lock alheio permanece intacto: jamais desvinculado ou reivindicado.
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.read_bytes(), payload)
        self.assertEqual(lock_path.stat().st_nlink, 1)

    def test_prepare_main_index_propagates_foreign_lock_as_busy(self):
        transaction = self.transaction(b'{"intent_id":"intent-foreign"}\n')
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): foreign index.lock contention")
        lock_path = self.root / ".git" / "index.lock"
        lock_path.write_bytes(b"foreign git transaction\n")
        lease = self.foreign_index_lock_lease()
        with tempfile.TemporaryDirectory(dir="/tmp") as raw:
            with self.assertRaises(TOOL.CommitBusy) as caught:
                TOOL._prepare_main_index(
                    epoch, pathlib.Path(raw), epoch.expected_head, "mass",
                    lease)
        self.assertIn("transação Git alheia", str(caught.exception))
        self.assertTrue(lock_path.is_file())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_recovery_entry_treats_foreign_index_lock_as_transient_busy(self):
        payload = b"foreign git transaction\n"
        lock_path = self.root / ".git" / "index.lock"
        lock_path.write_bytes(payload)
        with self.assertRaises(TOOL.CommitBusy) as caught:
            TOOL._recover_prepared_main_index(self.root)
        self.assertIn("transação Git alheia", str(caught.exception))
        self.assertFalse(caught.exception.cas_may_have_applied)
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.read_bytes(), payload)
        with self.assertRaises(TOOL.CommitBusy) as opened:
            TOOL._open_prepared_index_lock(self.root)
        self.assertIn("transação Git alheia", str(opened.exception))
        self.assertEqual(lock_path.read_bytes(), payload)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_recovery_keeps_damaged_own_artifact_deterministic(self):
        """nlink 2 sem sidecar é adulteração nossa, não contenção alheia."""
        self.sigkill_at_prepared_boundary("post_prepared")
        lock_path = self.root / ".git" / "index.lock"
        self.assertEqual(lock_path.stat().st_nlink, 2)
        for sidecar in (self.root / ".git").glob("index.prepared-*.json"):
            sidecar.unlink()
        with self.assertRaises(TOOL.CommitVerificationError) as caught:
            TOOL._recover_prepared_main_index(self.root)
        self.assertNotIsInstance(caught.exception, TOOL.CommitBusy)
        self.assertTrue(lock_path.is_file())

    def test_utc_headroom_guard_skips_fingerprint_with_success_terminal(self):
        transaction = self.transaction(b'{"intent_id":"intent-utc-landed"}\n')
        message = "content(v2): utc guard skips landed fingerprint"
        epoch = TOOL._build_commit_epoch(transaction, message)
        start_ticks = TOOL._proc_start_ticks(os.getpid())
        self.assertIsNotNone(start_ticks)
        assert start_ticks is not None
        TOOL._write_terminal(
            TOOL._singleflight_directory(self.root),
            TOOL._terminal_record(
                fingerprint=TOOL._singleflight_fingerprint(
                    epoch, message, "mass"),
                run_id=os.urandom(16).hex(), pid=os.getpid(),
                start_ticks=start_ticks, started_unix_ns=time.time_ns(),
                state="success", exit_code=0, failure_kind=None,
                cas_may_have_applied=False, stdout="{}\n", stderr=""))
        with mock.patch.object(
                TOOL.time, "time", return_value=float(86400 * 100 - 100)):
            self.assertIsNone(
                TOOL._assert_utc_day_headroom_before_new_entry(
                    epoch, message, "mass"))

    def test_utc_headroom_guard_still_blocks_fingerprint_without_terminal(self):
        transaction = self.transaction(b'{"intent_id":"intent-utc-novo"}\n')
        message = "content(v2): utc guard blocks new entry"
        epoch = TOOL._build_commit_epoch(transaction, message)
        with mock.patch.object(
                TOOL.time, "time", return_value=float(86400 * 100 - 100)):
            with self.assertRaisesRegex(TOOL.CommitBusy, "virada UTC em 100s"):
                TOOL._assert_utc_day_headroom_before_new_entry(
                    epoch, message, "mass")

    def test_utc_headroom_guard_runs_before_the_singleflight_lease(self):
        """A recusa por virada UTC não pode deixar terminal durável.

        Um terminal failure é replayado por ``_begin_singleflight`` enquanto
        ``--retry-failed`` não for informado: se a guarda rodasse depois da
        posse do lease, o rerun após 00:00Z replayaria 75 em vez de executar.
        """
        transaction = self.transaction(b'{"intent_id":"intent-utc-guard"}\n')
        with mock.patch.object(
                TOOL, "_assert_utc_day_headroom_for_private_audit",
                side_effect=TOOL.CommitBusy("fixture utc rollover")):
            with self.assertRaisesRegex(TOOL.CommitBusy, "fixture utc rollover"):
                TOOL._commit_transaction(
                    transaction, "content(v2): utc rollover headroom")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual(
            sorted(TOOL._singleflight_directory(self.root).glob(
                "*.terminal.json")), [])
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_sigkill_after_rename_is_finalized_by_sidecar(self):
        target_payload = b'{"intent_id":"intent-after-rename"}\n'
        self.sigkill_at_prepared_boundary(
            "post_rename", target_payload=target_payload)
        new_head = self.git("rev-parse", "HEAD").strip()
        self.assertNotEqual(new_head, self.base)
        self.assertFalse((self.root / ".git" / "index.lock").exists())
        self.assertEqual((self.root / ".git" / "index").stat().st_nlink, 2)
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["recovered"])
        self.assertFalse(report["reclaimed_pre_cas"])
        self.assertEqual(report["head"], new_head)
        self.assertEqual((self.root / ".git" / "index").stat().st_nlink, 1)
        self.assertEqual(
            self.git("show", ":data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(), target_payload)

    def test_sigkill_after_promoted_rewrite_refreshes_ctime_and_resumes(self):
        target_payload = b'{"intent_id":"intent-promoted-recovery"}\n'
        self.sigkill_at_prepared_boundary(
            "post_rename", target_payload=target_payload)
        git_directory = self.root / ".git"
        index_path = git_directory / "index"
        sidecars = list(git_directory.glob("index.prepared-*.json"))
        self.assertEqual(len(sidecars), 1)
        sidecar = sidecars[0]
        nonce = sidecar.with_suffix("")
        before = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(before["phase"], "ref_applied")

        # Force the same ctime-only transition that rename(2) causes while
        # restoring the exact two-link topology before recovery begins.
        transition = git_directory / "index.recovery-ctime-transition"
        for _ in range(4):
            os.link(nonce, transition, follow_symlinks=False)
            transition.unlink()
            if nonce.stat().st_ctime_ns != before["index_ctime_ns"]:
                break
        transitioned = nonce.stat()
        self.assertEqual(
            (transitioned.st_dev, transitioned.st_ino, transitioned.st_size,
             transitioned.st_mtime_ns),
            (before["inode_dev"], before["inode_ino"], before["index_size"],
             before["index_mtime_ns"]),
        )
        self.assertNotEqual(
            transitioned.st_ctime_ns, before["index_ctime_ns"])

        self.sigkill_at_prepared_recovery_boundary(
            "post_rewrite_promoted")
        promoted = json.loads(sidecar.read_text(encoding="utf-8"))
        promoted_info = nonce.stat()
        self.assertEqual(promoted["phase"], "promoted")
        self.assertEqual(
            (promoted["inode_dev"], promoted["inode_ino"],
             promoted["index_size"], promoted["index_mtime_ns"],
             promoted["index_ctime_ns"]),
            TOOL._descriptor_content_identity(promoted_info),
        )

        # A stale promoted record from the previous implementation may still
        # exist after a crash. Only ctime may transition; exact path, inode,
        # size, mtime and content hash remain mandatory.
        for _ in range(4):
            os.link(nonce, transition, follow_symlinks=False)
            transition.unlink()
            if nonce.stat().st_ctime_ns != promoted["index_ctime_ns"]:
                break
        stale_promoted_info = nonce.stat()
        self.assertEqual(
            (stale_promoted_info.st_dev, stale_promoted_info.st_ino,
             stale_promoted_info.st_size, stale_promoted_info.st_mtime_ns),
            (promoted["inode_dev"], promoted["inode_ino"],
             promoted["index_size"], promoted["index_mtime_ns"]),
        )
        self.assertNotEqual(
            stale_promoted_info.st_ctime_ns, promoted["index_ctime_ns"])
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["recovered"])
        self.assertFalse(report["reclaimed_pre_cas"])
        self.assertEqual(index_path.stat().st_nlink, 1)
        self.assertEqual(list(git_directory.glob("index.prepared-*")), [])
        self.assertEqual(
            self.git("show", ":data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(), target_payload)

    def test_tampered_prepared_sidecar_never_authorizes_unlink(self):
        self.sigkill_at_prepared_boundary("post_link")
        sidecars = list((self.root / ".git").glob(
            "index.prepared-*.json"))
        self.assertEqual(len(sidecars), 1)
        record = json.loads(sidecars[0].read_text(encoding="utf-8"))
        record["phase"] = "prepared"
        sidecars[0].write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8")
        sidecars[0].chmod(0o600)
        lock_path = self.root / ".git" / "index.lock"
        inode = lock_path.stat().st_ino
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "sidecar.*SHA"):
            TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.stat().st_ino, inode)

    def test_keyboard_interrupt_after_durable_cas_retains_prepared_index(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        original = TOOL._update_ref_cas

        def apply_then_interrupt(epoch, commit: str) -> None:
            original(epoch, commit)
            raise KeyboardInterrupt("fixture after durable CAS")

        with mock.patch.object(
                TOOL, "_update_ref_cas", side_effect=apply_then_interrupt), \
                self.assertRaises(KeyboardInterrupt):
            TOOL._commit_transaction(
                transaction,
                "content(v2): retain index on interrupted durable CAS")

        new_head = self.git("rev-parse", "HEAD").strip()
        self.assertNotEqual(new_head, self.base)
        self.assertEqual(
            self.git("show", "HEAD:data/editorial/v2_pages/"
                     "civil-commit-01.jsonl").encode(),
            target_payload,
        )
        lock_path = self.root / ".git" / "index.lock"
        self.assertTrue(lock_path.is_file())
        environment = dict(os.environ)
        environment["GIT_INDEX_FILE"] = os.fspath(lock_path)
        staged = subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), "show",
             ":data/editorial/v2_pages/civil-commit-01.jsonl"],
            env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(staged.returncode, 0, staged.stderr)
        self.assertEqual(staged.stdout, target_payload)

    def test_recovery_ambiguity_preserves_prepared_index_lock(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        original = TOOL._update_ref_cas

        def apply_then_interrupt(epoch, commit: str) -> None:
            original(epoch, commit)
            raise KeyboardInterrupt("fixture leaves recovery lock")

        with mock.patch.object(
                TOOL, "_update_ref_cas", side_effect=apply_then_interrupt), \
                self.assertRaises(KeyboardInterrupt):
            TOOL._commit_transaction(
                transaction,
                "content(v2): leave lock for ambiguous recovery")
        candidate = self.git("rev-parse", "HEAD").strip()
        tree = self.git("rev-parse", candidate + "^{tree}").strip()
        child = self.git(
            "commit-tree", tree, "-p", candidate,
            input_payload=b"unrelated child after interrupted CAS\n",
        ).strip()
        self.git("update-ref", "HEAD", child, candidate)
        lock_path = self.root / ".git" / "index.lock"
        lock_before = lock_path.read_bytes()
        with self.assertRaises(TOOL.CommitVerificationError):
            TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.read_bytes(), lock_before)

    def test_recovery_accepts_authenticated_artifact_only_closure(self):
        self.commit_hook("#!/bin/sh\nexit 0\n")
        target_payload = b'{"intent_id":"intent-old"}\n'
        transaction = self.transaction(target_payload)
        artifact_payload = b'{"intent_id":"artifact-only-preimage"}'
        _, artifact_relative = self.add_raw_artifact(
            transaction, artifact_payload)
        child = os.fork()
        if child == 0:
            original = TOOL._update_ref_cas

            def apply_then_interrupt(epoch, commit: str) -> None:
                original(epoch, commit)
                raise KeyboardInterrupt("fixture artifact-only durable CAS")

            TOOL._update_ref_cas = apply_then_interrupt
            try:
                TOOL._commit_transaction(
                    transaction,
                    "content(v2): commit authenticated artifact-only closure")
            except KeyboardInterrupt:
                os._exit(91)
            except BaseException:
                os._exit(92)
            os._exit(93)
        _, status = os.waitpid(child, 0)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 91)
        lock_path = self.root / ".git" / "index.lock"
        self.assertTrue(lock_path.is_file())
        report = TOOL._recover_prepared_main_index(self.root)
        self.assertTrue(report["recovered"])
        self.assertEqual(report["closure_paths"], [artifact_relative])
        self.assertFalse(lock_path.exists())
        self.assertEqual(
            self.git("show", "HEAD:" + artifact_relative).encode(),
            artifact_payload,
        )
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_cleanup_never_unlinks_replaced_index_lock_inode(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): retain foreign replacement lock")
        with tempfile.TemporaryDirectory() as raw:
            prepared = self.prepare_index_fixture(epoch, pathlib.Path(raw))
            replacement = pathlib.Path(raw) / "foreign.index.lock"
            replacement.write_bytes(b"foreign lock marker\n")
            os.replace(replacement, prepared.lock_path)
            TOOL._release_prepared_main_index(prepared)
        self.assertEqual(
            (self.root / ".git" / "index.lock").read_bytes(),
            b"foreign lock marker\n")

    def test_prepared_ctime_drift_from_extra_hardlink_fails_closed(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): reject prepared hardlink drift")
        with tempfile.TemporaryDirectory() as raw:
            prepared = self.prepare_index_fixture(epoch, pathlib.Path(raw))
            record = TOOL._read_prepared_index_artifact(
                prepared.sidecar_path).record
            extra = self.root / ".git" / "foreign-prepared-hardlink"
            for _ in range(4):
                os.link(prepared.nonce_path, extra)
                os.unlink(extra)
                if (prepared.nonce_path.stat().st_ctime_ns !=
                        record["index_ctime_ns"]):
                    break
            self.assertNotEqual(
                prepared.nonce_path.stat().st_ctime_ns,
                record["index_ctime_ns"])
            try:
                with self.assertRaisesRegex(
                        TOOL.CommitVerificationError, "identidade"):
                    TOOL._cleanup_proven_pre_cas_prepared_index(prepared)
            finally:
                TOOL._release_prepared_main_index(prepared)
            self.assertTrue(prepared.lock_path.exists())
            self.assertTrue(prepared.nonce_path.exists())
            self.assertTrue(prepared.sidecar_path.exists())

    def test_large_prepared_index_hashes_once_with_bounded_streaming_cache(self):
        size = 5 * 1024 * 1024 + 17
        with tempfile.TemporaryDirectory() as raw:
            parent = pathlib.Path(raw)
            run_id = "a" * 32
            nonce = parent / (
                "index.prepared-" + run_id + "-" + "b" * 32)
            descriptor = os.open(
                nonce,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC |
                os.O_NOFOLLOW,
                0o600,
            )
            try:
                os.ftruncate(descriptor, size)
                os.fsync(descriptor)
                info = os.fstat(descriptor)
                prepared = TOOL.PreparedMainIndex(
                    root=self.root,
                    index_path=parent / "index",
                    lock_path=parent / "index.lock",
                    nonce_path=nonce,
                    sidecar_path=nonce.with_name(nonce.name + ".json"),
                    descriptor=descriptor,
                    lock_identity=(info.st_dev, info.st_ino),
                    fingerprint="1" * 64,
                    run_id=run_id,
                    owner_pid=os.getpid(),
                    owner_start_ticks=(
                        TOOL._proc_start_ticks(os.getpid()) or 1),
                    started_unix_ns=time.time_ns(),
                    kind="mass",
                    expected_ref="refs/heads/main",
                    expected_head="2" * 40,
                    candidate="3" * 40,
                    object_format="sha1",
                    closure_digest="4" * 64,
                )
                original_pread = TOOL.os.pread
                reads: list[int] = []

                def observe_pread(fd, count, offset):
                    if fd == descriptor:
                        reads.append(count)
                    return original_pread(fd, count, offset)

                with mock.patch.object(
                        TOOL.os, "pread", side_effect=observe_pread):
                    for phase in ("prepared", "cas", "ref_applied"):
                        TOOL._write_prepared_index_phase(prepared, phase)
                self.assertEqual(sum(reads), size)
                self.assertLessEqual(max(reads), 1024 * 1024)
                self.assertEqual(len(reads), (size + 1024 * 1024 - 1) //
                                 (1024 * 1024))
                self.assertIsNotNone(prepared.descriptor_identity_digest)
                self.assertFalse(hasattr(TOOL, "_descriptor_payload"))
            finally:
                os.close(descriptor)

    def test_recovery_rejects_index_lock_with_live_transaction_owner(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): live owner blocks recovery")
        with tempfile.TemporaryDirectory() as raw:
            prepared = self.prepare_index_fixture(epoch, pathlib.Path(raw))
            try:
                with self.assertRaisesRegex(
                        TOOL.CommitBusy, "outra transação"):
                    TOOL._open_prepared_index_lock(self.root)
            finally:
                TOOL._release_prepared_main_index(prepared)
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_private_gate_root_executes_index_bytes_without_worktree_data(self):
        gate_hook = (
            "#!/bin/sh\nset -eu\n"
            'ROOT="$(CDPATH=\'\' cd -- "$(dirname -- "$0")/.." && pwd)"\n'
            'cd "$ROOT"\n'
            ': "${GIT_INDEX_FILE:?}"\n'
            "./tools/check-v2-supersession-integrity --git-index\n"
            "./tools/check-v2-writing-semantic-contract --git-index\n"
        )
        self.commit_hook(gate_hook)
        target_payload = b'{"intent_id":"intent-private-index"}\n'
        transaction = self.transaction(target_payload)
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): private gate snapshot proof")
        fake_binary = (
            "#!/bin/sh\nset -eu\n"
            '[ "$1" = "--git-index" ]\n'
            "test ! -e data/editorial/v2_pages/civil-commit-01.jsonl\n"
            "value=$(/usr/bin/git --no-replace-objects show "
            ":data/editorial/v2_pages/civil-commit-01.jsonl)\n"
            '[ "$value" = \'{"intent_id":"intent-private-index"}\' ]\n'
        ).encode()
        def compile_fixture(epoch, snapshot_root, workspace):
            del epoch, workspace
            bindings = {}
            hashes = {}
            for binary_name, _ in TOOL.GATE_COMMANDS:
                binary = snapshot_root / "tools" / binary_name
                binary.write_bytes(fake_binary)
                binary.chmod(0o500)
                binary_digest = digest(fake_binary)
                bindings[binary] = binary_digest
                hashes[binary_name] = binary_digest
            return bindings, {"binaries": hashes, "fixture": True}
        with tempfile.TemporaryDirectory() as raw_workspace:
            workspace = pathlib.Path(raw_workspace)
            workspace.chmod(0o700)
            private_index = workspace / "candidate.index"
            TOOL._materialize_private_index(epoch, os.fspath(private_index))
            with mock.patch.object(TOOL, "INSTALL_ROOT", self.root), \
                    mock.patch.object(
                        TOOL, "_compile_tracked_gate_binaries",
                        side_effect=compile_fixture), \
                    mock.patch.object(
                        TOOL, "_assert_private_v2_gate_capability"):
                snapshot_root, bindings, attestation = (
                    TOOL._materialize_gate_snapshot_root(epoch, workspace))
            self.assertEqual(len(bindings), 2)
            self.assertTrue(attestation["fixture"])
            self.assertEqual(
                stat.S_IMODE(snapshot_root.stat().st_mode), 0o700)
            self.assertEqual(
                stat.S_IMODE(
                    (snapshot_root / ".githooks").stat().st_mode), 0o700)
            self.assertEqual(
                stat.S_IMODE((snapshot_root / "tools").stat().st_mode),
                0o700)
            self.assertFalse((snapshot_root / "data").exists())
            TOOL._run_pre_commit_snapshot(
                snapshot_root, epoch.hook_payload, os.fspath(private_index))

    def test_dirty_dependency_fails_closed(self):
        self.dependency.write_bytes(b"const batches = [{dirty:true}]\n")
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = FakeTransaction(
            self.root, self.target, target_payload,
            {self.dependency: digest(self.dependency.read_bytes())})
        self.target.write_bytes(target_payload)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "dirty fora da closure"):
            TOOL._commit_transaction(
                transaction, "content(v2): reject dirty repository floor")

    def test_exact_authenticated_target_may_already_be_staged(self):
        self.dependency.write_bytes(b"const batches = []\n")
        self.unrelated.write_bytes(b"preserve-unrelated-stage\n")
        self.git("add", "--", "notes.txt")
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        self.git("add", "--", transaction.report["files"][0]["file"])
        staged_before = self.git(
            "ls-files", "--stage", "--",
            transaction.report["files"][0]["file"],
        ).strip().split()
        self.assertEqual(staged_before[0], "100644")
        self.assertEqual(staged_before[2], "0")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                transaction,
                "content(v2): accept exact authenticated staged target"), 0)

        report = json.loads(output.getvalue())
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), report["commit"])
        self.assertEqual(
            self.git("show", "HEAD:" + transaction.report["files"][0]["file"]
                     ).encode(),
            target_payload,
        )
        self.assertEqual(
            self.git("diff", "--cached", "--name-only").splitlines(),
            ["notes.txt"],
        )
        self.assertEqual(
            self.git("show", ":notes.txt").encode(),
            b"preserve-unrelated-stage\n",
        )

    def test_staged_target_with_different_bytes_or_mode_fails_closed(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        divergent_payload = b'{"intent_id":"foreign-staged"}\n'
        self.target.write_bytes(divergent_payload)
        self.git("add", "--", self.target.relative_to(self.root).as_posix())
        transaction = self.transaction(target_payload)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "diverge no alvo"):
            TOOL._build_commit_epoch(
                transaction, "content(v2): reject divergent staged bytes")

        self.git("add", "--", self.target.relative_to(self.root).as_posix())
        self.git("update-index", "--chmod=+x", "--",
                 self.target.relative_to(self.root).as_posix())
        transaction = self.transaction(target_payload)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "diverge no alvo"):
            TOOL._build_commit_epoch(
                transaction, "content(v2): reject divergent staged mode")

    def test_conflicted_target_index_fails_closed(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        relative = self.target.relative_to(self.root).as_posix()
        old_oid = self.git("rev-parse", "HEAD:" + relative).strip()
        new_oid = self.git(
            "hash-object", "-w", "--stdin", input_payload=target_payload,
        ).strip()
        self.git("update-index", "--force-remove", "--", relative)
        conflict = (
            f"100644 {old_oid} 1\t{relative}\n"
            f"100644 {new_oid} 2\t{relative}\n"
        ).encode("ascii")
        self.git("update-index", "--index-info", input_payload=conflict)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "conflito/entrada insegura"):
            TOOL._build_commit_epoch(
                transaction, "content(v2): reject conflicted target index")

    def test_exact_staged_target_is_revalidated_under_index_lock(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        relative = self.target.relative_to(self.root).as_posix()
        self.git("add", "--", relative)
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): bind staged target before index lock")

        divergent_payload = b'{"intent_id":"foreign-after-capture"}\n'
        self.target.write_bytes(divergent_payload)
        self.git("add", "--", relative)
        self.target.write_bytes(target_payload)
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError,
                    "entradas-alvo do índice mudaram"):
                self.prepare_index_fixture(epoch, pathlib.Path(raw))
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_staged_target_bytes_are_revalidated_under_index_lock(self):
        target_payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(target_payload)
        relative = self.target.relative_to(self.root).as_posix()
        self.git("add", "--", relative)
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): bind exact staged object bytes")
        target_oid = epoch.closure[0]["git_blob_oid"]
        original = TOOL._run_git

        def forged_object(root, arguments, **kwargs):
            if arguments == ["cat-file", "blob", target_oid]:
                return subprocess.CompletedProcess(
                    arguments, 0, b"forged-object-bytes\n", b"")
            return original(root, arguments, **kwargs)

        with tempfile.TemporaryDirectory() as raw, \
                mock.patch.object(
                    TOOL, "_run_git", side_effect=forged_object), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError,
                    "diverge dos bytes autenticados"):
            self.prepare_index_fixture(epoch, pathlib.Path(raw))
        self.assertFalse((self.root / ".git" / "index.lock").exists())

    def test_forged_mass_audit_ok_cannot_bypass_private_auditor(self):
        class FailingAuditor:
            ROOT = None

            @staticmethod
            def audit_against_stock_legacy(path, expect_n=None):
                return {
                    "file": os.path.relpath(path, FailingAuditor.ROOT),
                    "pages": expect_n,
                    "active_pages": expect_n,
                    "defects": {"fonte_oficial": ["intent-new"]},
                    "ok": False,
                }

        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        transaction.report["audit_ok"] = True
        transaction.report["files"][0]["audit_ok"] = True
        index_before = (self.root / ".git" / "index").read_bytes()
        with mock.patch.object(TOOL, "_LOADED_AUDITOR", FailingAuditor), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError,
                    "auditor independente reprovou"):
            TOOL._commit_transaction(
                transaction, "content(v2): reject forged audit claim")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual((self.root / ".git" / "index").read_bytes(),
                         index_before)

    def test_review_private_audit_ignores_worktree_checker_and_factory_cache(self):
        target_payload = b'{"intent_id":"intent-review-private"}\n'
        transaction, _, evidence_relative = self.review_transaction(
            target_payload)
        poisoned_marker = self.root / "poisoned-worktree-checker-ran"
        mutable_checker = self.root / "tools" / "audit-v2-source-provenance"
        mutable_checker.parent.mkdir(parents=True, exist_ok=True)
        mutable_checker.write_text(
            "#!/bin/sh\n"
            f"touch {poisoned_marker}\n"
            "exit 0\n",
            encoding="utf-8",
        )
        mutable_checker.chmod(0o755)
        factory_poison = self.root / ".cache" / "factory" / "forged-pass.json"
        factory_poison.parent.mkdir(parents=True)
        factory_poison.write_text('{"ok":true}\n', encoding="utf-8")

        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): review private candidate audit")
        with tempfile.TemporaryDirectory() as raw_workspace:
            workspace = pathlib.Path(raw_workspace)
            private_index = workspace / "candidate.index"
            TOOL._materialize_private_index(epoch, os.fspath(private_index))
            snapshot_root = workspace / "gate-root"
            self.write_private_provenance_checker(
                snapshot_root, evidence_relative)

            class CacheRejectingAuditor(PassingClosedAuditor):
                @staticmethod
                def audit_against_stock_legacy(path, expect_n=None):
                    if (pathlib.Path(CacheRejectingAuditor.ROOT) / ".cache").exists():
                        raise AssertionError("factory cache reached private tree")
                    return PassingClosedAuditor.audit_against_stock_legacy(
                        path, expect_n)

            with mock.patch.object(
                    TOOL, "_LOADED_AUDITOR", CacheRejectingAuditor):
                attestation, _ = TOOL._audit_candidate_tree(
                    transaction, epoch, os.fspath(private_index), workspace,
                    snapshot_root)
        self.assertTrue(attestation["audit_ok"])
        self.assertEqual(
            attestation["schema"], "v2_review_private_candidate_audit_v1")
        self.assertFalse(attestation["factory_cache_used"])
        self.assertEqual(
            attestation["targets"][0]["source_provenance"]["evidence_file"],
            evidence_relative)
        self.assertFalse(poisoned_marker.exists())

    def test_forged_review_merit_and_worktree_checker_cannot_bypass_private_failures(self):
        transaction, _, evidence_relative = self.review_transaction(
            b'{"intent_id":"intent-review-forged"}\n')
        transaction.report["audit_merit_verified"] = True
        transaction.report["wave_commit_allowed"] = True
        transaction.report["audit_merit_attestation"] = {"ok": True}

        class FailingReviewAuditor:
            ROOT = None

            @staticmethod
            def audit_against_stock_legacy(path, expect_n=None):
                return {
                    "pages": expect_n,
                    "active_pages": expect_n,
                    "defects": {"duplicidade": ["intent-review-forged"]},
                    "ok": False,
                }

        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): reject forged review merit")
        with tempfile.TemporaryDirectory() as raw_workspace:
            workspace = pathlib.Path(raw_workspace)
            private_index = workspace / "candidate.index"
            TOOL._materialize_private_index(epoch, os.fspath(private_index))
            snapshot_root = workspace / "gate-root"
            self.write_private_provenance_checker(
                snapshot_root, evidence_relative)
            with mock.patch.object(
                    TOOL, "_LOADED_AUDITOR", FailingReviewAuditor), \
                    self.assertRaisesRegex(
                        TOOL.CommitVerificationError,
                        "auditor independente reprovou"):
                TOOL._audit_candidate_tree(
                    transaction, epoch, os.fspath(private_index), workspace,
                    snapshot_root)

        # A forged mutable checker also cannot rescue a failing exact checker.
        with tempfile.TemporaryDirectory() as raw_workspace:
            workspace = pathlib.Path(raw_workspace)
            private_index = workspace / "candidate.index"
            TOOL._materialize_private_index(epoch, os.fspath(private_index))
            snapshot_root = workspace / "gate-root"
            self.write_private_provenance_checker(
                snapshot_root, evidence_relative, status=23)
            with mock.patch.object(
                    TOOL, "_LOADED_AUDITOR", PassingClosedAuditor), \
                    self.assertRaisesRegex(
                        TOOL.CommitVerificationError,
                        "checker privado de proveniência reprovou"):
                TOOL._audit_candidate_tree(
                    transaction, epoch, os.fspath(private_index), workspace,
                    snapshot_root)

    def test_private_global_audit_uses_minimal_snapshot_checker_and_explicit_batch(self):
        marker = self.root / "mutable-distinctness-checker-ran"
        mutable_checker = self.root / "tools" / "check-v2-private-distinctness"
        mutable_checker.parent.mkdir(parents=True, exist_ok=True)
        mutable_checker.write_text(
            "#!/bin/sh\n"
            f"touch {marker}\n"
            "exit 0\n",
            encoding="utf-8")
        mutable_checker.chmod(0o755)
        shard = "data/editorial/v2_pages/civil-commit-01.jsonl"

        class ExplicitBatchAuditor:
            FACTORY_GLOBAL_BATCH_STDOUT_MAX_BYTES = 1024 * 1024

            @staticmethod
            def parse_global_distinctness_batch(payload):
                if payload != b"private-authenticated-batch\n":
                    return None, "unexpected-payload"
                return ({
                    "header": {
                        "mode": "global-distinctness-v3-read-only",
                        "generation_root": "a" * 64,
                        "stock_root": "b" * 64,
                        "stock_shards": 1,
                        "stock_pages": 1,
                    },
                    "footer": {
                        "inventory_complete": True,
                        "inventory_stable": True,
                        "candidate_routing_complete": True,
                        "local_routing_complete": True,
                    },
                    "shards": {shard: {}},
                }, None)

            @staticmethod
            def audit_global_with_distinctness_batch(batch):
                if batch["header"]["generation_root"] != "a" * 64:
                    raise AssertionError("foreign batch")
                return {
                    "total_pages": 1,
                    "files": {shard: {
                        "file": shard, "active_pages": 1,
                        "defects": {}, "ok": True,
                    }},
                }

        with tempfile.TemporaryDirectory() as raw:
            workspace = pathlib.Path(raw)
            audit_root = workspace / "audit-root"
            audit_root.mkdir()
            snapshot_root = workspace / "snapshot"
            private_checker = (
                snapshot_root / "tools" / "check-v2-private-distinctness")
            private_checker.parent.mkdir(parents=True)
            private_checker.write_text(
                "#!/bin/sh\n"
                "set -eu\n"
                "printf 'private-authenticated-batch\\n'\n",
                encoding="utf-8")
            private_checker.chmod(0o500)
            with mock.patch.object(
                    TOOL, "_LOADED_AUDITOR", ExplicitBatchAuditor):
                report, attestation, bindings = (
                    TOOL._run_private_global_audit(
                        audit_root, snapshot_root, workspace, self.root))
        self.assertFalse(marker.exists())
        self.assertEqual(set(report["files"]), {shard})
        self.assertEqual(attestation["generation_root"], "a" * 64)
        self.assertEqual(attestation["stock_root"], "b" * 64)
        self.assertIn(private_checker, bindings)

    def test_persistent_distinctness_store_is_private_and_reused(self):
        first = TOOL._persistent_private_distinctness_store(self.root)
        second = TOOL._persistent_private_distinctness_store(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first.name, "store")
        self.assertEqual(first.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(first.parent.stat().st_uid, os.geteuid())
        self.assertTrue(first.parent.is_relative_to(self.root / ".git"))

    def test_persistent_distinctness_store_rejects_symlink_boundary(self):
        cache = self.root / ".git" / "codex-private-v2-distinctness"
        target = self.root / "foreign-cache"
        target.mkdir()
        cache.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "autoridade ou modo inválido"):
            TOOL._persistent_private_distinctness_store(self.root)

    def test_persistent_go_build_caches_are_private_and_reused(self):
        first_build, first_module = TOOL._persistent_go_build_caches(self.root)
        second_build, second_module = (
            TOOL._persistent_go_build_caches(self.root))
        # Stable identity across commits: the compile cache is reused, never a
        # fresh cold-build tempdir.
        self.assertEqual(first_build, second_build)
        self.assertEqual(first_module, second_module)
        self.assertEqual(first_build.name, "build")
        self.assertEqual(first_module.name, "mod")
        self.assertEqual(first_build.parent.name, "codex-private-go-cache")
        self.assertEqual(first_build.parent, first_module.parent)
        for directory in (first_build.parent, first_build, first_module):
            info = directory.stat()
            self.assertEqual(info.st_mode & 0o777, 0o700)
            self.assertEqual(info.st_uid, os.geteuid())
            self.assertTrue(directory.is_relative_to(self.root / ".git"))

    def test_persistent_go_build_caches_reject_symlink_boundary(self):
        parent = self.root / ".git" / "codex-private-go-cache"
        parent.mkdir()
        os.chmod(parent, 0o700)
        target = self.root / "foreign-go-cache"
        target.mkdir()
        (parent / "build").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "autoridade ou modo inválido"):
            TOOL._persistent_go_build_caches(self.root)

    def test_persistent_audit_blob_store_is_private_and_reused(self):
        first = TOOL._persistent_audit_blob_store(self.root)
        second = TOOL._persistent_audit_blob_store(self.root)
        self.assertIsNotNone(first)
        self.assertEqual(first, second)
        self.assertEqual(first.name, "codex-private-v2-audit-blobs")
        self.assertEqual(first.stat().st_mode & 0o777, 0o700)
        self.assertEqual(first.stat().st_uid, os.geteuid())
        self.assertTrue(first.is_relative_to(self.root / ".git"))

    def test_persistent_audit_blob_store_degrades_on_symlink_boundary(self):
        # Optional accelerator: a poisoned boundary must degrade to ``None`` and
        # a full materialize — never abort a commit that would pass today.
        store_dir = self.root / ".git" / "codex-private-v2-audit-blobs"
        target = self.root / "foreign-audit-cache"
        target.mkdir()
        store_dir.symlink_to(target, target_is_directory=True)
        self.assertIsNone(TOOL._persistent_audit_blob_store(self.root))

    def test_audit_blob_store_reuse_is_content_identical_and_unique(self):
        store = TOOL._persistent_audit_blob_store(self.root)
        self.assertIsNotNone(store)
        roots = ("data/editorial/v2_pages",)
        cold_dest = self.root / "cold-audit"
        cold_dest.mkdir(mode=0o700)
        cold_manifest, cold_bindings = TOOL._materialize_git_tree_subset(
            self.root, "HEAD", roots, cold_dest, blob_store=store)
        # The cold run populated the store; the warm run must reuse every blob
        # without reading it back out of Git, while materializing a unique inode
        # so the audit reader's single-link boundary remains true.
        warm_dest = self.root / "warm-audit"
        warm_dest.mkdir(mode=0o700)
        with mock.patch.object(
                TOOL, "_cat_file_batch",
                side_effect=AssertionError("warm run re-read a blob")):
            warm_manifest, warm_bindings = TOOL._materialize_git_tree_subset(
                self.root, "HEAD", roots, warm_dest, blob_store=store)
        self.assertEqual(cold_manifest, warm_manifest)
        cold_rel = {
            path.relative_to(cold_dest): digest
            for path, digest in cold_bindings.items()}
        warm_rel = {
            path.relative_to(warm_dest): digest
            for path, digest in warm_bindings.items()}
        self.assertEqual(cold_rel, warm_rel)
        warm_file = warm_dest / self.target.relative_to(self.root)
        self.assertEqual(warm_file.stat().st_nlink, 1)
        target_entry = next(
            item for item in warm_manifest
            if item["path"] == self.target.relative_to(self.root).as_posix())
        cached_file = store / target_entry["oid"][:2] / target_entry["oid"][2:]
        self.assertNotEqual(warm_file.stat().st_ino, cached_file.stat().st_ino)

    def test_audit_materialize_rebuilds_when_cache_entry_is_mangled(self):
        store = TOOL._persistent_audit_blob_store(self.root)
        roots = ("data/editorial/v2_pages",)
        first_dest = self.root / "mangled-first"
        first_dest.mkdir(mode=0o700)
        first_manifest, _ = TOOL._materialize_git_tree_subset(
            self.root, "HEAD", roots, first_dest, blob_store=store)
        oid = first_manifest[0]["oid"]
        cached_content = store / oid[:2] / oid[2:]
        # A cache entry whose mode no longer matches 0o400 fails the per-hit
        # revalidation, so the blob must be rebuilt from Git (a miss), not
        # trusted — and the logical result stays identical.
        os.chmod(cached_content, 0o600)
        second_dest = self.root / "mangled-second"
        second_dest.mkdir(mode=0o700)
        with mock.patch.object(
                TOOL, "_cat_file_batch",
                wraps=TOOL._cat_file_batch) as spy:
            second_manifest, _ = TOOL._materialize_git_tree_subset(
                self.root, "HEAD", roots, second_dest, blob_store=store)
        spy.assert_called()
        self.assertEqual(first_manifest, second_manifest)
        third_dest = self.root / "mangled-third"
        third_dest.mkdir(mode=0o700)
        with mock.patch.object(
                TOOL, "_cat_file_batch",
                side_effect=AssertionError("repaired cache stayed cold")):
            third_manifest, _ = TOOL._materialize_git_tree_subset(
                self.root, "HEAD", roots, third_dest, blob_store=store)
        self.assertEqual(first_manifest, third_manifest)

    def test_audit_materialize_rejects_same_mode_forged_cache_content(self):
        store = TOOL._persistent_audit_blob_store(self.root)
        roots = ("data/editorial/v2_pages",)
        first_dest = self.root / "forged-first"
        first_dest.mkdir(mode=0o700)
        manifest, _ = TOOL._materialize_git_tree_subset(
            self.root, "HEAD", roots, first_dest, blob_store=store)
        oid = manifest[0]["oid"]
        cached_content = store / oid[:2] / oid[2:]
        os.chmod(cached_content, 0o600)
        cached_content.write_bytes(b"forged-same-mode-cache\n")
        os.chmod(cached_content, 0o400)
        second_dest = self.root / "forged-second"
        second_dest.mkdir(mode=0o700)
        with mock.patch.object(
                TOOL, "_cat_file_batch",
                wraps=TOOL._cat_file_batch) as spy:
            second_manifest, _ = TOOL._materialize_git_tree_subset(
                self.root, "HEAD", roots, second_dest, blob_store=store)
        spy.assert_called()
        self.assertEqual(manifest, second_manifest)

    def test_audit_materialize_fifo_sidecar_is_a_nonblocking_cache_miss(self):
        store = TOOL._persistent_audit_blob_store(self.root)
        roots = ("data/editorial/v2_pages",)
        first_dest = self.root / "fifo-first"
        first_dest.mkdir(mode=0o700)
        manifest, _ = TOOL._materialize_git_tree_subset(
            self.root, "HEAD", roots, first_dest, blob_store=store)
        oid = manifest[0]["oid"]
        sidecar = store / oid[:2] / (oid[2:] + ".s256")
        sidecar.unlink()
        os.mkfifo(sidecar, 0o400)
        second_dest = self.root / "fifo-second"
        second_dest.mkdir(mode=0o700)
        with mock.patch.object(
                TOOL, "_cat_file_batch",
                wraps=TOOL._cat_file_batch) as spy:
            second_manifest, _ = TOOL._materialize_git_tree_subset(
                self.root, "HEAD", roots, second_dest, blob_store=store)
        spy.assert_called()
        self.assertEqual(manifest, second_manifest)

    def test_minimal_go_environment_points_gocache_at_persistent_store(self):
        build_cache, module_cache = TOOL._persistent_go_build_caches(self.root)
        proxy = self.root / "module-proxy"
        proxy.mkdir()
        with tempfile.TemporaryDirectory() as raw:
            workspace = pathlib.Path(raw).resolve()
            os.chmod(workspace, 0o700)
            goroot = workspace / "goroot"
            goroot.mkdir()
            with mock.patch.object(TOOL, "MODULE_PROXY", proxy):
                environment = TOOL._minimal_go_environment(
                    workspace, goroot, build_cache, module_cache)
            # The compile cache and module cache must live in the persistent
            # store, never inside the throwaway per-commit workspace.
            self.assertEqual(environment["GOCACHE"], os.fspath(build_cache))
            self.assertEqual(environment["GOMODCACHE"], os.fspath(module_cache))
            self.assertFalse(
                pathlib.Path(environment["GOCACHE"]).is_relative_to(workspace))
            self.assertFalse(
                pathlib.Path(
                    environment["GOMODCACHE"]).is_relative_to(workspace))
            # Scratch tmp/gopath stay ephemeral in the workspace.
            self.assertTrue(
                pathlib.Path(environment["TMPDIR"]).is_relative_to(workspace))
            self.assertTrue(
                pathlib.Path(environment["GOPATH"]).is_relative_to(workspace))
        self.assertTrue(build_cache.is_dir())
        self.assertTrue(module_cache.is_dir())

    def test_detached_head_is_rejected_before_private_commit(self):
        self.git("update-ref", "--no-deref", "HEAD", self.base)
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "HEAD detached"):
            TOOL._commit_transaction(
                transaction, "content(v2): reject detached head")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_symbolic_head_git_failure_is_not_misreported_as_detached(self):
        failed = subprocess.CompletedProcess(
            ["git", "symbolic-ref"], 128, b"", b"fatal: ownership denied\n")
        with mock.patch.object(TOOL, "_run_git", return_value=failed), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "symbolic-ref falhou"):
            TOOL._capture_symbolic_head(self.root)

    def test_closed_git_commands_pin_the_resolved_root_as_safe_directory(self):
        observed: list[str] = []

        def capture(command, **kwargs):
            observed.extend(command)
            return subprocess.CompletedProcess(command, 0, b"", b"")

        with mock.patch.object(TOOL, "_run_closed_process", side_effect=capture):
            TOOL._run_git(self.root, ["status", "--porcelain"])
        self.assertIn("safe.directory=" + os.fspath(self.root), observed)

    def test_symbolic_head_retarget_is_rejected_on_exact_ref_cas(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        expected_ref = self.git("symbolic-ref", "HEAD").strip()
        original_gate = TOOL._run_pre_commit_snapshot

        def gate_then_retarget(*arguments, **kwargs):
            original_gate(*arguments, **kwargs)
            self.git("branch", "other", self.base)
            self.git("symbolic-ref", "HEAD", "refs/heads/other")

        with mock.patch.object(
                TOOL, "_run_pre_commit_snapshot",
                side_effect=gate_then_retarget), \
                self.assertRaisesRegex(TOOL.CommitBusy, "retargetado"):
            TOOL._commit_transaction(
                transaction, "content(v2): reject symbolic ref drift")
        self.assertEqual(
            self.git("rev-parse", expected_ref).strip(), self.base)
        self.assertEqual(
            self.git("rev-parse", "refs/heads/other").strip(), self.base)

    def test_canonical_id_repair_derives_one_exact_nfkd_transition_from_head(self):
        _, new_payload = self.install_canonical_repair_parent()
        transaction = TOOL._build_canonical_id_repair_transaction(
            self.root, self.target.relative_to(self.root).as_posix())
        self.assertEqual(transaction.kind, "canonical-id-repair")
        self.assertEqual(transaction.expected_head, self.base)
        self.assertEqual(transaction.target_payload, new_payload)
        self.assertEqual(transaction.transition.old_intent,
                         "seguro-marítimo-carga")
        self.assertEqual(transaction.transition.new_intent,
                         "seguro-maritimo-carga")
        self.assertEqual(transaction.transition.line_number, 1)
        transaction.revalidate()

    def test_canonical_id_repair_rejects_extra_field_change(self):
        self.install_canonical_repair_parent()
        payload = self.target.read_bytes().replace(
            b'"title":"Guia fechado"', b'"title":"Guia adulterado"')
        self.target.write_bytes(payload)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "bytes mudaram fora"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_rejects_nonexact_accent_fold(self):
        old_payload, _ = self.install_canonical_repair_parent()
        self.target.write_bytes(old_payload.replace(
            "seguro-marítimo-carga".encode(), b"seguro-marinho-carga", 1))
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "NFKD exato"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_rejects_global_new_intent_collision(self):
        self.install_canonical_repair_parent()
        collision = (
            self.root / "data/editorial/v2_pages/civil-collision-02.jsonl")
        collision.write_bytes(self.canonical_record("seguro-maritimo-carga"))
        self.git("add", "--", collision.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: canonical collision", "--",
                 collision.relative_to(self.root).as_posix())
        self.base = self.git("rev-parse", "HEAD").strip()
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "novo já existe"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_rejects_nfkd_alias_and_hidden_stock_path(self):
        self.install_canonical_repair_parent()
        alias = (
            self.root / "data/editorial/v2_pages/civil-collision-03.jsonl")
        alias.write_bytes(self.canonical_record(
            "seguro-mari\u0301timo-carga"))
        self.git("add", "--", alias.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: decomposed alias", "--",
                 alias.relative_to(self.root).as_posix())
        self.base = self.git("rev-parse", "HEAD").strip()
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "alias NFKD global"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

        alias.unlink()
        self.git("add", "-u", "--", alias.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: remove alias", "--",
                 alias.relative_to(self.root).as_posix())
        hidden = self.root / "data/editorial/v2_pages/legacy.jsonl"
        hidden.write_bytes(self.canonical_record("intent-legado"))
        self.git("add", "--", hidden.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: hidden stock path", "--",
                 hidden.relative_to(self.root).as_posix())
        self.base = self.git("rev-parse", "HEAD").strip()
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "path não canônico"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_rejects_duplicate_json_keys(self):
        old_intent = "seguro-marítimo-carga"
        old_payload = self.canonical_record(old_intent).replace(
            b'"title":"Guia fechado"',
            b'"title":"Guia fechado","title":"Duplicado"')
        self.target.write_bytes(old_payload)
        self.git("add", "--", self.target.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: duplicate JSON key", "--",
                 self.target.relative_to(self.root).as_posix())
        self.target.write_bytes(old_payload.replace(
            old_intent.encode("utf-8"), b"seguro-maritimo-carga", 1))
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "chave JSON duplicada"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_rejects_symlink_and_hardlink(self):
        _, new_payload = self.install_canonical_repair_parent()
        external = self.root / "external.jsonl"
        external.write_bytes(new_payload)
        self.target.unlink()
        self.target.symlink_to(external)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "ausente/inseguro"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())
        self.target.unlink()
        os.link(external, self.target)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "regular único"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_revalidation_rejects_inode_drift(self):
        _, new_payload = self.install_canonical_repair_parent()
        transaction = TOOL._build_canonical_id_repair_transaction(
            self.root, self.target.relative_to(self.root).as_posix())
        replacement = self.root / "replacement.jsonl"
        replacement.write_bytes(new_payload)
        replacement.chmod(0o644)
        os.replace(replacement, self.target)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "target/inode mudou"):
            transaction.revalidate()

    def test_canonical_id_repair_recovery_reconstructs_closed_receipt_mode(self):
        self.install_canonical_repair_parent()
        transaction = TOOL._build_canonical_id_repair_transaction(
            self.root, self.target.relative_to(self.root).as_posix())
        epoch = TOOL._build_commit_epoch(
            transaction, "content(v2): canonical repair recovery fixture")
        with tempfile.TemporaryDirectory() as raw:
            index = pathlib.Path(raw) / "candidate.index"
            TOOL._materialize_private_index(epoch, os.fspath(index))
            commit, _ = TOOL._create_commit_object(
                epoch, os.fspath(index),
                "content(v2): canonical repair recovery fixture")
        recovered = TOOL._recovery_guard_transaction(epoch, commit)
        self.assertEqual(recovered.kind, "canonical-id-repair")
        self.assertEqual(recovered.transition, transaction.transition)
        original_closed_process = TOOL._run_closed_process
        guard_environment: dict[str, str] = {}

        def observe_guard(command, **kwargs):
            if command[0] == os.fspath(TOOL.PYTHON_BIN):
                guard_environment.update(kwargs["environment"])
                return subprocess.CompletedProcess(command, 0, b"", b"")
            return original_closed_process(command, **kwargs)

        with tempfile.TemporaryDirectory() as raw, mock.patch.object(
                TOOL, "_run_closed_process",
                side_effect=observe_guard,
        ):
            TOOL._run_finalized_commit_guard(
                None, epoch, commit, pathlib.Path(raw))
        self.assertEqual(
            guard_environment["WIKI_V2_AUTHENTICATED_RECOVERY_OID"], commit)

    def test_canonical_id_repair_revalidation_rejects_head_and_index_drift(self):
        self.install_canonical_repair_parent()
        transaction = TOOL._build_canonical_id_repair_transaction(
            self.root, self.target.relative_to(self.root).as_posix())
        self.git("add", "--", self.target.relative_to(self.root).as_posix())
        with self.assertRaisesRegex(TOOL.CommitBusy, "index mudou"):
            transaction.revalidate()

        transaction = TOOL._build_canonical_id_repair_transaction(
            self.root, self.target.relative_to(self.root).as_posix())
        self.unrelated.write_bytes(b"advance-head-only\n")
        self.git("add", "--", self.unrelated.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: concurrent head", "--",
                 self.unrelated.relative_to(self.root).as_posix())
        with self.assertRaisesRegex(TOOL.CommitBusy, "HEAD mudou"):
            transaction.revalidate()

    def test_canonical_id_repair_rejects_open_public_flag(self):
        old_intent = "seguro-marítimo-carga"
        self.target.write_bytes(self.canonical_record(
            old_intent, public=True))
        self.git("add", "--", self.target.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: unsafe public parent", "--",
                 self.target.relative_to(self.root).as_posix())
        self.target.write_bytes(self.target.read_bytes().replace(
            old_intent.encode(), b"seguro-maritimo-carga", 1))
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "flag pública aberta"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_canonical_id_repair_rejects_add_and_delete(self):
        added = self.root / "data/editorial/v2_pages/civil-added-02.jsonl"
        added.write_bytes(self.canonical_record("ação-canonica"))
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "target novo/ausente"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, added.relative_to(self.root).as_posix())
        self.install_canonical_repair_parent()
        self.target.unlink()
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "ausente/inseguro"):
            TOOL._build_canonical_id_repair_transaction(
                self.root, self.target.relative_to(self.root).as_posix())

    def test_git_tree_materializer_uses_expected_commit_not_dirty_worktree(self):
        source = self.root / "internal" / "fixture" / "source.go"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"package fixture\nconst Value = 1\n")
        self.git("add", "--", "internal/fixture/source.go")
        self.git("commit", "-q", "-m", "fixture: tracked source", "--",
                 "internal/fixture/source.go")
        expected = self.git("rev-parse", "HEAD").strip()
        source.write_bytes(b"package fixture\nconst Value = 999\n")
        with tempfile.TemporaryDirectory() as raw:
            destination = pathlib.Path(raw) / "snapshot"
            destination.mkdir()
            manifest, _ = TOOL._materialize_git_tree_subset(
                self.root, expected, ("internal",), destination)
            self.assertIn("internal/fixture/source.go",
                          {item["path"] for item in manifest})
            self.assertEqual(
                (destination / "internal/fixture/source.go").read_bytes(),
                b"package fixture\nconst Value = 1\n")

    def test_git_tree_materializer_streams_sized_blob_groups(self):
        destination = self.root / "private-streamed-tree"
        original = TOOL._run_git
        batch_calls: list[tuple[str, ...]] = []

        def observe(root, arguments, **kwargs):
            if arguments == ["cat-file", "--batch"]:
                batch_calls.append(tuple(arguments))
            return original(root, arguments, **kwargs)

        with mock.patch.object(TOOL, "GIT_BATCH_TARGET_BYTES", 1), \
                mock.patch.object(TOOL, "_run_git", side_effect=observe):
            manifest, _ = TOOL._materialize_git_tree_subset(
                self.root,
                self.base,
                (
                    "data/editorial/v2_pages",
                    "scripts",
                    "notes.txt",
                    "tools/check-v2-finalized-commit",
                ),
                destination,
            )
        self.assertGreater(len(batch_calls), 1)
        self.assertEqual(
            [item["path"] for item in manifest],
            sorted(item["path"] for item in manifest),
        )
        for item in manifest:
            self.assertEqual(
                digest((destination / item["path"]).read_bytes()),
                item["sha256"],
            )

    def test_singleflight_and_heavy_locks_remain_owned_through_cas(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        original = TOOL._update_ref_cas
        observed: dict[str, object] = {}

        def assert_leases_then_cas(epoch, commit):
            lease = TOOL._ACTIVE_SINGLEFLIGHT
            self.assertIsNotNone(lease)
            assert lease is not None
            active = TOOL._read_control_json(
                lease.directory / "active.json",
                max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
            self.assertEqual(active["phase"], "cas")
            producer_probe = TOOL._singleflight_lock_descriptor(
                lease.directory)
            heavy_probe = os.open(
                TOOL.HEAVY_AUDIT_LOCK,
                os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
            try:
                with self.assertRaises(BlockingIOError):
                    TOOL.fcntl.flock(
                        producer_probe,
                        TOOL.fcntl.LOCK_EX | TOOL.fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):
                    TOOL.fcntl.flock(
                        heavy_probe,
                        TOOL.fcntl.LOCK_EX | TOOL.fcntl.LOCK_NB)
                observed["locked"] = True
            finally:
                os.close(producer_probe)
                os.close(heavy_probe)
            original(epoch, commit)

        with mock.patch.object(
                TOOL, "_update_ref_cas", side_effect=assert_leases_then_cas), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): hold leases through exact cas"), 0)
        self.assertTrue(observed["locked"])

    def assert_durable_success_survives_terminal_signal(
        self, *, operation: str, error: BaseException,
        message: str, active_expected: bool,
    ) -> None:
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        stdout = '{"commit_created":true}\n'
        captured: list[TOOL.SingleFlightLease] = []

        def owner(_transaction, _message, _epoch, lease):
            captured.append(lease)
            lease.heavy_descriptor = TOOL._acquire_heavy_audit_lock(lease)
            return stdout

        with mock.patch.object(
                TOOL, "_commit_transaction_owner", side_effect=owner), \
                mock.patch.object(TOOL, operation, side_effect=error), \
                mock.patch.object(
                    TOOL, "_finish_singleflight_failure",
                    wraps=TOOL._finish_singleflight_failure,
                ) as failure_terminalizer, \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaises(type(error)):
            TOOL._commit_transaction(transaction, message)

        self.assertEqual(len(captured), 1)
        lease = captured[0]
        terminal = TOOL._read_singleflight_terminal(
            lease.directory, lease.fingerprint)
        self.assertIsNotNone(terminal)
        assert terminal is not None
        self.assertEqual(terminal["state"], "success")
        self.assertEqual(terminal["stdout"], stdout)
        failure_terminalizer.assert_not_called()
        self.assertTrue(lease.terminal)
        self.assertEqual(lease.descriptor, -1)
        self.assertEqual(lease.heavy_descriptor, -1)
        self.assertIsNone(TOOL._ACTIVE_SINGLEFLIGHT)
        self.assertEqual(
            (lease.directory / "active.json").exists(), active_expected)

    def test_keyboard_interrupt_during_success_unlink_preserves_terminal(self):
        self.assert_durable_success_survives_terminal_signal(
            operation="_unlink_control",
            error=KeyboardInterrupt("fixture after SUCCESS rename"),
            message="content(v2): preserve success across active unlink",
            active_expected=True,
        )

    def test_system_exit_during_success_cleanup_preserves_terminal(self):
        self.assert_durable_success_survives_terminal_signal(
            operation="_cleanup_promoted_prepared_index",
            error=SystemExit(97),
            message="content(v2): preserve success across cleanup",
            active_expected=False,
        )

    def test_semantic_revalidate_ignores_unrelated_index_rewrite_only(self):
        target_payload = b'{"intent_id":"semantic-target"}\n'
        self.target.write_bytes(target_payload)
        target_relative = self.target.relative_to(self.root).as_posix()
        self.git("add", "--", target_relative)
        expected_head = self.git("rev-parse", "HEAD").strip()
        object_format = self.git(
            "rev-parse", "--show-object-format").strip()
        target_entry = TOOL._index_entries_for_paths(
            self.root, [target_relative])[target_relative]
        assert target_entry is not None
        item = {
            "path": target_relative,
            "mode": target_entry[0],
            "git_blob_oid": target_entry[1],
            "sha256": digest(target_payload),
            "role": "semantic_recut_staged_closure",
        }
        index_path = self.root / ".git" / "index"
        transaction = TOOL.SemanticRecutCommitTransaction(
            root=self.root, expected_head=expected_head,
            object_format=object_format, candidates={target_relative: item},
            payloads={target_relative: target_payload}, index_path=index_path,
            index_identity=TOOL._file_identity(os.stat(index_path)),
            index_entries={target_relative: target_entry},
            staged_source_payloads={target_relative: target_payload})
        inode_before = os.stat(index_path).st_ino
        self.unrelated.write_bytes(b"unrelated-stage-rewritten\n")
        self.git("add", "--", self.unrelated.relative_to(self.root).as_posix())
        # Git may replace or rewrite the index; either representation is not
        # authority as long as the target stage-zero tuple/object is unchanged.
        transaction.revalidate()
        self.assertEqual(
            self.git("show", ":" + target_relative).encode(), target_payload)
        self.assertTrue(
            os.stat(index_path).st_ino != inode_before or
            os.stat(index_path).st_mtime_ns > 0)
        self.target.write_bytes(b'{"intent_id":"semantic-foreign"}\n')
        self.git("add", "--", target_relative)
        with self.assertRaisesRegex(
                TOOL.CommitBusy, "entrada-alvo do index mudou"):
            transaction.revalidate()

    def unit_ledger_rows(self) -> list[dict]:
        return TOOL._read_unit_ledger(self.root)

    def test_rerun_of_landed_unit_replays_idempotent_no_op(self):
        payload = b'{"intent_id":"intent-new"}\n'
        transaction = self.transaction(payload)
        first = io.StringIO()
        with contextlib.redirect_stdout(first):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): land unit once"), 0)
        landed = json.loads(first.getvalue())["commit"]
        rows = self.unit_ledger_rows()
        self.assertEqual(
            [(row["state"], row["commit_oid"]) for row in rows],
            [("success", landed)])
        self.assertIsNotNone(rows[0]["unit_key"])
        self.assertIsNotNone(rows[0]["family_key"])
        # Forward history moves past the landed unit...
        self.target.write_bytes(b'{"intent_id":"intent-forward"}\n')
        self.git("add", "--",
                 self.target.relative_to(self.root).as_posix())
        self.git("commit", "-q", "-m", "fixture: forward edit")
        forward_head = self.git("rev-parse", "HEAD").strip()
        # ...and re-presenting the exact landed input bytes is a rerun of the
        # same unit, not new work: idempotent no-op, never a re-landing of
        # stale bytes over newer state.
        rerun = self.transaction(payload)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                rerun, "content(v2): identical rerun replays"), 0)
        replay = json.loads(output.getvalue())
        self.assertTrue(replay["replayed_no_op"])
        self.assertEqual(replay["commit"], landed)
        self.assertEqual(replay["unit_key"], rows[0]["unit_key"])
        self.assertFalse(replay["publication_allowed"])
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), forward_head)
        self.assertEqual(len(self.unit_ledger_rows()), 1)

    def test_new_inputs_land_and_share_family_budget_key(self):
        first_txn = self.transaction(b'{"intent_id":"intent-new"}\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(TOOL._commit_transaction(
                first_txn, "content(v2): first unit"), 0)
        second_txn = self.transaction(b'{"intent_id":"intent-second"}\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(TOOL._commit_transaction(
                second_txn, "content(v2): second unit lands"), 0)
        self.assertTrue(json.loads(output.getvalue())["commit_created"])
        rows = self.unit_ledger_rows()
        self.assertEqual(
            [row["state"] for row in rows], ["success", "success"])
        self.assertNotEqual(rows[0]["unit_key"], rows[1]["unit_key"])
        self.assertEqual(rows[0]["family_key"], rows[1]["family_key"])
        self.assertEqual([row["attempts"] for row in rows], [1, 2])

    def test_third_family_attempt_circuit_opens_and_reopens_with_motive(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        message = "content(v2): family budget fixture"
        with mock.patch.object(
                TOOL, "_run_finalized_commit_guard",
                side_effect=TOOL.CommitVerificationError("guard fixture 1")), \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "guard fixture 1"):
            TOOL._commit_transaction(transaction, message)
        epoch = TOOL._build_commit_epoch(transaction, message)
        fingerprint = TOOL._singleflight_fingerprint(epoch, message, "mass")
        terminal = TOOL._read_singleflight_terminal(
            TOOL._singleflight_directory(self.root), fingerprint)
        assert terminal is not None
        with mock.patch.object(
                TOOL, "_run_finalized_commit_guard",
                side_effect=TOOL.CommitVerificationError("guard fixture 2")), \
                contextlib.redirect_stderr(io.StringIO()), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "guard fixture 2"):
            TOOL._commit_transaction(
                transaction, message,
                retry_failed=terminal["result_sha256"])
        # Third attempt on the same family is refused BEFORE any execution.
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "circuit-open"):
            TOOL._commit_transaction(transaction, message)
        # Red-team 20260722 §1 control: a code edit must NOT reset the family
        # budget — the 2026-07-21 loop edited code between every rerun.
        self.commit_hook(self.passing_hook() + "# code epoch bump\n")
        edited = self.transaction(b'{"intent_id":"intent-new"}\n')
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "circuit-open"):
            TOOL._commit_transaction(edited, message)
        # Byte micro-adjustment produces a new unit_key but the SAME family
        # and stays refused too.
        adjusted = self.transaction(b'{"intent_id":"intent-micro"}\n')
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "circuit-open"):
            TOOL._commit_transaction(adjusted, message)
        self.assertEqual(
            [row["state"] for row in self.unit_ledger_rows()],
            ["failure", "failure"])
        family_key = TOOL._unit_identity(
            TOOL._build_commit_epoch(adjusted, message), "mass")[1]
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "motivo real"):
            TOOL._reopen_unit_family(self.root, family_key, "curto")
        report = TOOL._reopen_unit_family(
            self.root, family_key,
            "censo RCA fixture: causa-raiz do guard corrigida e validada")
        self.assertTrue(report["family_reopened"])
        self.assertEqual(report["deterministic_failures_cleared"], 2)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "redundante"):
            TOOL._reopen_unit_family(
                self.root, family_key,
                "segunda reabertura sem novo circuito deve ser recusada")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(
                TOOL._commit_transaction(adjusted, message), 0)
        self.assertTrue(json.loads(output.getvalue())["commit_created"])

    def test_transient_failure_budget_circuit_opens_with_diagnostic(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        message = "content(v2): transient budget fixture"
        epoch = TOOL._build_commit_epoch(transaction, message)
        unit_key, family_key, oids_digest = TOOL._unit_identity(epoch, "mass")
        for index in range(TOOL.MAX_UNIT_TRANSIENT_FAILURES):
            TOOL._append_unit_ledger_row(self.root, {
                "schema": TOOL.UNIT_LEDGER_SCHEMA,
                "unit_key": unit_key,
                "family_key": family_key,
                "kind": "mass",
                "input_oids_digest": oids_digest,
                "fingerprint": "a" * 64,
                "run_id": "b" * 32,
                "state": "failure",
                "failure_kind": "CommitBusy",
                "exit_code": 75,
                "cas_may_have_applied": False,
                "result_sha256": digest(str(index).encode()),
                "commit_oid": None,
                "attempts": index + 1,
                "ts_unix_ns": 1 + index,
            })
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "circuit-open.*transiente"):
            TOOL._commit_transaction(transaction, message)

    def test_unit_ledger_adulteration_fails_closed(self):
        transaction = self.transaction(b'{"intent_id":"intent-new"}\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(TOOL._commit_transaction(
                transaction, "content(v2): land before adulteration"), 0)
        ledger = TOOL._unit_ledger_path(self.root)
        raw = ledger.read_bytes()
        self.assertIn(b'"state":"success"', raw)
        ledger.write_bytes(
            raw.replace(b'"state":"success"', b'"state":"failure"', 1))
        follow_up = self.transaction(b'{"intent_id":"intent-second"}\n')
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "unit-ledger"):
            TOOL._commit_transaction(
                follow_up, "content(v2): must fail closed")


class SemanticRecutLandedNoOpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), "init", "-q"],
            check=True)
        for key, value in (("user.name", "Fixture"),
                           ("user.email", "fixture@example.invalid")):
            subprocess.run(
                ["/usr/bin/git", "-C", os.fspath(self.root),
                 "config", key, value], check=True)
        (self.root / "seed.txt").write_bytes(b"seed\n")
        subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), "add", "--", "."],
            check=True)
        subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root),
             "commit", "-q", "-m", "base"], check=True)
        self.head = subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root),
             "rev-parse", "HEAD"],
            check=True, stdout=subprocess.PIPE,
        ).stdout.decode("ascii").strip()

    def success_row(self, commit_oid: str | None) -> dict:
        return {
            "schema": TOOL.UNIT_LEDGER_SCHEMA,
            "unit_key": "1" * 64,
            "family_key": "2" * 64,
            "kind": "semantic-recut",
            "input_oids_digest": "3" * 64,
            "fingerprint": "4" * 64,
            "run_id": "5" * 32,
            "state": "success",
            "failure_kind": None,
            "exit_code": 0,
            "cas_may_have_applied": False,
            "result_sha256": "6" * 64,
            "commit_oid": commit_oid,
            "attempts": 1,
            "ts_unix_ns": 7,
        }

    def test_landed_ancestor_resolves_no_op_and_foreign_does_not(self):
        self.assertIsNone(TOOL._semantic_recut_landed_no_op(self.root))
        TOOL._append_unit_ledger_row(
            self.root, self.success_row("f" * 40))
        self.assertIsNone(
            TOOL._semantic_recut_landed_no_op(self.root),
            "OID desconhecido jamais prova pouso — controle fail-closed")
        TOOL._append_unit_ledger_row(self.root, self.success_row(self.head))
        report = TOOL._semantic_recut_landed_no_op(self.root)
        assert report is not None
        self.assertTrue(report["replayed_no_op"])
        self.assertEqual(report["commit"], self.head)
        self.assertEqual(report["kind"], "semantic-recut")
        self.assertFalse(report["publication_allowed"])


class SingleFlightProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), "init", "-q"],
            check=True)
        head_path = self.root / ".git" / "HEAD"
        self.epoch = TOOL.CommitEpoch(
            root=self.root, expected_head="1" * 40,
            expected_ref="refs/heads/main", head_path=head_path,
            head_payload=head_path.read_bytes(), object_format="sha1",
            closure=({
                "path": "data/editorial/v2_pages/teste-01.jsonl",
                "mode": "100644", "git_blob_oid": "2" * 40,
                "sha256": "3" * 64, "role": "fixture",
            },),
            closure_payloads={
                "data/editorial/v2_pages/teste-01.jsonl": b"{}\n"},
            dependencies=(), dependency_bindings={},
            main_index_targets_before={
                "data/editorial/v2_pages/teste-01.jsonl": None},
            hook_payload=b"#!/bin/sh\nexit 0\n")
        self.message = "content(v2): singleflight protocol fixture"
        previous_wait = TOOL.HEAVY_AUDIT_LOCK_WAIT_SECONDS
        TOOL.HEAVY_AUDIT_LOCK_WAIT_SECONDS = 5.0
        self.addCleanup(
            setattr, TOOL, "HEAVY_AUDIT_LOCK_WAIT_SECONDS", previous_wait)

    def begin(self, retry: str | None = None):
        return TOOL._begin_singleflight(
            self.epoch, self.message, "semantic-recut", retry)

    def finish_success(self, lease, stdout: str = '{"ok":true}\n'):
        try:
            return TOOL._finish_singleflight_success(lease, stdout)
        finally:
            TOOL._release_singleflight(lease)

    def test_same_fingerprint_joins_one_owner_and_replays_terminal(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        ready_read, ready_write = os.pipe()
        result_read, result_write = os.pipe()
        child = os.fork()
        if child == 0:
            try:
                os.close(ready_read)
                os.close(result_read)
                # Drop the inherited reference to the producer's open-file
                # description; the parent remains the sole lock owner.
                os.close(owner.descriptor)
                directory = TOOL._singleflight_directory(self.root)
                probe = TOOL._singleflight_lock_descriptor(directory)
                try:
                    try:
                        TOOL.fcntl.flock(
                            probe, TOOL.fcntl.LOCK_EX | TOOL.fcntl.LOCK_NB)
                    except BlockingIOError:
                        os.write(ready_write, b"joined")
                    else:
                        os.write(ready_write, b"unexpected-owner")
                finally:
                    os.close(probe)
                decision = self.begin()
                payload = json.dumps({
                    "replay": isinstance(decision, TOOL.SingleFlightReplay),
                    "state": (decision.record.get("state")
                              if isinstance(decision, TOOL.SingleFlightReplay)
                              else "owner"),
                }).encode()
                os.write(result_write, payload)
                os._exit(0)
            except BaseException as error:
                os.write(result_write, repr(error).encode())
                os._exit(91)
        os.close(ready_write)
        os.close(result_write)
        try:
            self.assertEqual(os.read(ready_read, 64), b"joined")
            terminal = self.finish_success(owner)
            child_payload = os.read(result_read, 4096)
            waited, status = os.waitpid(child, 0)
        finally:
            os.close(ready_read)
            os.close(result_read)
        self.assertEqual(waited, child)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 0, child_payload)
        self.assertEqual(
            json.loads(child_payload), {"replay": True, "state": "success"})
        replay = self.begin()
        self.assertIsInstance(replay, TOOL.SingleFlightReplay)
        self.assertEqual(replay.record["result_sha256"],
                         terminal["result_sha256"])

    def test_different_fingerprint_is_busy_other_with_owner_and_phase(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        different_item = dict(self.epoch.closure[0])
        different_item["sha256"] = "6" * 64
        different = dataclasses.replace(
            self.epoch, closure=(different_item,))
        try:
            with self.assertRaisesRegex(
                    TOOL.CommitBusy,
                    r"BUSY_OTHER fingerprint=.* owner=[0-9]+/[0-9]+ "
                    r"phase=claimed"):
                TOOL._begin_singleflight(
                    different, self.message, "semantic-recut", None)
        finally:
            self.finish_success(owner)

    def test_failure_replay_requires_exact_terminal_sha_for_retry(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        try:
            terminal = TOOL._finish_singleflight_failure(
                owner, TOOL.CommitVerificationError("fixture failure"))
        finally:
            TOOL._release_singleflight(owner)
        replay = self.begin()
        self.assertIsInstance(replay, TOOL.SingleFlightReplay)
        self.assertEqual(replay.record["state"], "failure")
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "diverge do SHA"):
            self.begin("f" * 64)
        retry = self.begin(terminal["result_sha256"])
        self.assertIsInstance(retry, TOOL.SingleFlightLease)
        self.assertNotEqual(retry.run_id, terminal["run_id"])
        self.finish_success(retry)

    def test_ambiguous_cas_failure_cannot_be_retried_blindly(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        TOOL._singleflight_phase(owner, "cas")
        try:
            terminal = TOOL._finish_singleflight_failure(
                owner, KeyboardInterrupt("after update-ref boundary"))
        finally:
            TOOL._release_singleflight(owner)
        self.assertTrue(terminal["cas_may_have_applied"])
        with self.assertRaisesRegex(TOOL.CommitBusy, "CAS ambíguo"):
            self.begin(terminal["result_sha256"])

    def test_phase_write_failure_does_not_publish_unwritten_phase_in_memory(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        try:
            with mock.patch.object(
                    TOOL, "_atomic_control_write",
                    side_effect=TOOL.CommitVerificationError("fsync fixture")), \
                    self.assertRaisesRegex(
                        TOOL.CommitVerificationError, "fsync fixture"):
                TOOL._singleflight_phase(owner, "cas")
            self.assertEqual(owner.phase, "claimed")
        finally:
            self.finish_success(owner)

    def test_dead_owner_with_live_material_child_stays_busy(self):
        directory = TOOL._singleflight_directory(self.root)
        fingerprint = TOOL._singleflight_fingerprint(
            self.epoch, self.message, "semantic-recut")
        now = time.time_ns()
        active = {
            "schema": TOOL.SINGLEFLIGHT_SCHEMA,
            "state": "active",
            "fingerprint": fingerprint,
            "run_id": "b" * 32,
            "pid": os.getpid(),
            "start_ticks": (TOOL._proc_start_ticks(os.getpid()) or 1) + 1,
            "owner_uid": os.geteuid(),
            "phase": "private_audit",
            "started_unix_ns": now,
            "heartbeat_unix_ns": now,
            "child_pid": os.getpid(),
            "child_start_ticks": TOOL._proc_start_ticks(os.getpid()),
        }
        TOOL._atomic_control_write(
            directory / "active.json", TOOL._canonical_json(active),
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        try:
            with self.assertRaisesRegex(TOOL.CommitBusy, "orphan child"):
                self.begin()
            self.assertTrue((directory / "active.json").exists())
            self.assertIsNone(
                TOOL._read_singleflight_terminal(directory, fingerprint))
        finally:
            TOOL._unlink_control(
                directory / "active.json",
                max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)

    def test_stale_active_reconciles_terminal_of_its_own_fingerprint(self):
        owner_a = self.begin()
        self.assertIsInstance(owner_a, TOOL.SingleFlightLease)
        terminal_a = self.finish_success(owner_a)
        directory = TOOL._singleflight_directory(self.root)
        now = time.time_ns()
        stale_a = {
            "schema": TOOL.SINGLEFLIGHT_SCHEMA,
            "state": "active",
            "fingerprint": owner_a.fingerprint,
            "run_id": owner_a.run_id,
            "pid": os.getpid(),
            "start_ticks": (TOOL._proc_start_ticks(os.getpid()) or 1) + 1,
            "owner_uid": os.geteuid(),
            "phase": "terminalizing_success_cas",
            "started_unix_ns": now,
            "heartbeat_unix_ns": now,
            "child_pid": None,
            "child_start_ticks": None,
        }
        TOOL._atomic_control_write(
            directory / "active.json", TOOL._canonical_json(stale_a),
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        different_item = dict(self.epoch.closure[0])
        different_item["sha256"] = "7" * 64
        different = dataclasses.replace(
            self.epoch, closure=(different_item,))
        owner_b = TOOL._begin_singleflight(
            different, self.message, "semantic-recut", None)
        self.assertIsInstance(owner_b, TOOL.SingleFlightLease)
        try:
            preserved = TOOL._read_singleflight_terminal(
                directory, owner_a.fingerprint)
            self.assertEqual(preserved["result_sha256"],
                             terminal_a["result_sha256"])
            self.assertEqual(preserved["state"], "success")
        finally:
            self.finish_success(owner_b)

    def test_dead_owner_safe_failure_terminalization_stays_retryable(self):
        directory = TOOL._singleflight_directory(self.root)
        fingerprint = TOOL._singleflight_fingerprint(
            self.epoch, self.message, "semantic-recut")
        now = time.time_ns()
        active = {
            "schema": TOOL.SINGLEFLIGHT_SCHEMA,
            "state": "active",
            "fingerprint": fingerprint,
            "run_id": "c" * 32,
            "pid": os.getpid(),
            "start_ticks": (TOOL._proc_start_ticks(os.getpid()) or 1) + 1,
            "owner_uid": os.geteuid(),
            "phase": "terminalizing_failure_safe",
            "started_unix_ns": now,
            "heartbeat_unix_ns": now,
            "child_pid": None,
            "child_start_ticks": None,
        }
        TOOL._atomic_control_write(
            directory / "active.json", TOOL._canonical_json(active),
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        replay = self.begin()
        self.assertIsInstance(replay, TOOL.SingleFlightReplay)
        self.assertFalse(replay.record["cas_may_have_applied"])
        retry = self.begin(replay.record["result_sha256"])
        self.assertIsInstance(retry, TOOL.SingleFlightLease)
        self.finish_success(retry)

    def test_unknown_phase_is_rejected_without_retryable_terminal(self):
        directory = TOOL._singleflight_directory(self.root)
        fingerprint = TOOL._singleflight_fingerprint(
            self.epoch, self.message, "semantic-recut")
        now = time.time_ns()
        active = {
            "schema": TOOL.SINGLEFLIGHT_SCHEMA,
            "state": "active",
            "fingerprint": fingerprint,
            "run_id": "d" * 32,
            "pid": os.getpid(),
            "start_ticks": (TOOL._proc_start_ticks(os.getpid()) or 1) + 1,
            "owner_uid": os.geteuid(),
            "phase": "banana",
            "started_unix_ns": now,
            "heartbeat_unix_ns": now,
            "child_pid": None,
            "child_start_ticks": None,
        }
        TOOL._atomic_control_write(
            directory / "active.json", TOOL._canonical_json(active),
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        try:
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "schema inválido"):
                self.begin()
            self.assertIsNone(
                TOOL._read_singleflight_terminal(directory, fingerprint))
        finally:
            TOOL._unlink_control(
                directory / "active.json",
                max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)

    def test_zombie_material_child_does_not_hold_singleflight_forever(self):
        child = os.fork()
        if child == 0:
            os._exit(0)
        try:
            deadline = time.monotonic() + 5
            observed = None
            while time.monotonic() < deadline:
                observed = TOOL._proc_state_and_start_ticks(child)
                if observed is not None and observed[0] == "Z":
                    break
                time.sleep(0.01)
            self.assertIsNotNone(observed)
            self.assertEqual(observed[0], "Z")
            directory = TOOL._singleflight_directory(self.root)
            fingerprint = TOOL._singleflight_fingerprint(
                self.epoch, self.message, "semantic-recut")
            now = time.time_ns()
            active = {
                "schema": TOOL.SINGLEFLIGHT_SCHEMA,
                "state": "active",
                "fingerprint": fingerprint,
                "run_id": "e" * 32,
                "pid": os.getpid(),
                "start_ticks":
                    (TOOL._proc_start_ticks(os.getpid()) or 1) + 1,
                "owner_uid": os.geteuid(),
                "phase": "private_audit",
                "started_unix_ns": now,
                "heartbeat_unix_ns": now,
                "child_pid": child,
                "child_start_ticks": observed[1],
            }
            TOOL._atomic_control_write(
                directory / "active.json", TOOL._canonical_json(active),
                max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
            replay = self.begin()
            self.assertIsInstance(replay, TOOL.SingleFlightReplay)
            self.assertEqual(replay.record["state"], "failure")
        finally:
            os.waitpid(child, 0)

    def test_dead_owner_and_pid_reuse_become_durable_failure(self):
        directory = TOOL._singleflight_directory(self.root)
        fingerprint = TOOL._singleflight_fingerprint(
            self.epoch, self.message, "semantic-recut")
        now = time.time_ns()
        active = {
            "schema": TOOL.SINGLEFLIGHT_SCHEMA,
            "state": "active",
            "fingerprint": fingerprint,
            "run_id": "a" * 32,
            "pid": os.getpid(),
            # Current PID with a different generation simulates PID reuse.
            "start_ticks": (TOOL._proc_start_ticks(os.getpid()) or 1) + 1,
            "owner_uid": os.geteuid(),
            "phase": "private_audit",
            "started_unix_ns": now,
            "heartbeat_unix_ns": now,
            "child_pid": None,
            "child_start_ticks": None,
        }
        TOOL._atomic_control_write(
            directory / "active.json", TOOL._canonical_json(active),
            max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
        replay = self.begin()
        self.assertIsInstance(replay, TOOL.SingleFlightReplay)
        self.assertEqual(replay.record["state"], "failure")
        self.assertIn("PID reutilizado", replay.record["stderr"])
        self.assertFalse((directory / "active.json").exists())

    def test_control_plane_rejects_symlink_hardlink_fifo_and_oversize(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = pathlib.Path(raw)
            target = directory / "target"
            target.write_bytes(b"{}\n")
            target.chmod(0o600)
            attacks = ("symlink", "hardlink", "fifo", "oversize")
            for attack in attacks:
                with self.subTest(attack=attack):
                    path = directory / "active.json"
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        pass
                    if attack == "symlink":
                        path.symlink_to(target)
                    elif attack == "hardlink":
                        os.link(target, path)
                    elif attack == "fifo":
                        os.mkfifo(path, 0o600)
                    else:
                        path.write_bytes(
                            b"x" * (TOOL.SINGLEFLIGHT_STATE_MAX_BYTES + 1))
                        path.chmod(0o600)
                    with self.assertRaisesRegex(
                            TOOL.CommitVerificationError,
                            "inseguro ou excedeu limite"):
                        TOOL._read_control_payload(
                            path, max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
                    if attack == "hardlink":
                        path.unlink()
                        # Restore nlink=1 for subsequent symlink targets.
                        replacement = directory / "replacement"
                        replacement.write_bytes(b"{}\n")
                        replacement.chmod(0o600)
                        os.replace(replacement, target)

    def test_terminal_content_adulteration_is_not_replayed(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        terminal = self.finish_success(owner)
        path = TOOL._singleflight_terminal_path(
            TOOL._singleflight_directory(self.root), owner.fingerprint)
        forged = dict(terminal)
        forged["stdout"] = '{"forged":true}\n'
        # Deliberately retain the old result_sha256.
        TOOL._atomic_control_write(
            path, TOOL._canonical_json(forged),
            max_bytes=TOOL.SINGLEFLIGHT_TERMINAL_MAX_BYTES)
        with self.assertRaisesRegex(
                TOOL.CommitVerificationError, "perdeu SHA"):
            self.begin()

    def test_active_state_exposes_phase_heartbeat_and_child_generation(self):
        owner = self.begin()
        self.assertIsInstance(owner, TOOL.SingleFlightLease)
        try:
            TOOL._singleflight_phase(
                owner, "private_audit", child_pid=os.getpid())
            record = TOOL._read_control_json(
                owner.directory / "active.json",
                max_bytes=TOOL.SINGLEFLIGHT_STATE_MAX_BYTES)
            validated = TOOL._validate_active_record(record)
            self.assertEqual(validated["phase"], "private_audit")
            self.assertEqual(validated["child_pid"], os.getpid())
            self.assertEqual(
                validated["child_start_ticks"],
                TOOL._proc_start_ticks(os.getpid()))
            self.assertGreaterEqual(
                validated["heartbeat_unix_ns"],
                validated["started_unix_ns"])
        finally:
            self.finish_success(owner)

    def test_package_atomic_preflight_rejects_omitted_staged_and_untracked(self):
        go_path = "internal/example/example.go"
        go_item = {
            "path": go_path, "mode": "100644", "git_blob_oid": "4" * 40,
            "sha256": "5" * 64, "role": "fixture",
        }
        epoch = dataclasses.replace(
            self.epoch, closure=(go_item,),
            closure_payloads={go_path: b"package example\n"})
        with mock.patch.object(
                TOOL, "_index_changed_paths",
                return_value=[go_path, "internal/example/other.go"]), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "staged omitido"):
            TOOL._preflight_uid_cache_and_package_atomic(epoch)
        untracked = subprocess.CompletedProcess(
            [], 0, b"internal/example/new.go\0", b"")
        with mock.patch.object(
                TOOL, "_index_changed_paths", return_value=[go_path]), \
                mock.patch.object(TOOL, "_run_git", return_value=untracked), \
                self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "source untracked"):
            TOOL._preflight_uid_cache_and_package_atomic(epoch)


class CanonicalIDRepairGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        self.target = (
            self.root / "data/editorial/v2_pages/seguros-repair-01.jsonl")
        self.target.parent.mkdir(parents=True)
        self.git("init", "-q")
        self.git("config", "user.name", "Portal Jurídico Workflow")
        self.git("config", "user.email",
                 "workflow-integrator@portal-juridico.invalid")
        self.target.write_bytes(self.record("seguro-marítimo-carga"))
        self.git("add", "--", self.relative(self.target))
        self.git("commit", "-q", "-m", "base")
        self.old, self.new = self.commit_changes({
            self.target: self.record("seguro-maritimo-carga"),
        })
        previous_root = GUARD.ROOT
        GUARD.ROOT = self.root
        self.addCleanup(setattr, GUARD, "ROOT", previous_root)

    def relative(self, path: pathlib.Path) -> str:
        return path.relative_to(self.root).as_posix()

    def record(
        self, intent: str, *, title: str = "Guia fechado", public: bool = False,
    ) -> bytes:
        return (json.dumps({
            "intent_id": intent,
            "public": public,
            "publication_allowed": False,
            "publication_candidate": False,
            "render_allowed": False,
            "sitemap_allowed": False,
            "indexable": False,
            "index_policy": "noindex",
            "approval": False,
            "public_path": "",
            "title": title,
        }, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

    def git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", os.fspath(self.root), *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if completed.returncode != 0:
            self.fail(completed.stderr.decode("utf-8", errors="replace"))
        return completed.stdout.decode("utf-8", errors="strict")

    def commit_changes(
        self, changes: dict[pathlib.Path, bytes | None],
    ) -> tuple[str, str]:
        old = self.git("rev-parse", "HEAD").strip()
        paths: list[str] = []
        existing: list[str] = []
        deleted: list[str] = []
        for path, payload in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if payload is None:
                path.unlink()
                deleted.append(self.relative(path))
            else:
                path.write_bytes(payload)
                path.chmod(0o644)
                existing.append(self.relative(path))
            paths.append(self.relative(path))
        if existing:
            self.git("add", "--", *existing)
        if deleted:
            self.git("add", "-u", "--", *deleted)
        self.git("commit", "-q", "-m", "candidate", "--", *paths)
        return old, self.git("rev-parse", "HEAD").strip()

    def environment(
        self, old: str, new: str, path: pathlib.Path,
    ) -> dict[str, str]:
        relative = self.relative(path)
        old_mode, old_oid = GUARD.tree_entry(old, relative)
        new_mode, new_oid = GUARD.tree_entry(new, relative)
        old_intent, new_intent, line_number = GUARD.canonical_repair_transition(
            GUARD.blob(old, relative), GUARD.blob(new, relative), relative)
        receipt = GUARD.canonical_repair_receipt_digest(
            old, new, relative, old_mode, old_oid, new_mode, new_oid,
            old_intent, new_intent, line_number)
        return {
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
            "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "canonical-id-repair",
            "WIKI_V2_AUTHENTICATED_REPAIR_SHA256": receipt,
        }

    def test_guard_accepts_exact_receipt_and_rejects_missing_receipt(self):
        environment = self.environment(self.old, self.new, self.target)
        with mock.patch.dict(os.environ, environment, clear=False):
            GUARD.check(self.old, self.new)
        without_receipt = dict(environment)
        del without_receipt["WIKI_V2_AUTHENTICATED_REPAIR_SHA256"]
        with mock.patch.dict(os.environ, without_receipt, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "receipt"):
            GUARD.check(self.old, self.new)

    def test_guard_rejects_second_finalized_file(self):
        first = self.root / "data/editorial/v2_pages/civil-repair-02.jsonl"
        second = self.root / "data/editorial/v2_pages/civil-repair-03.jsonl"
        self.commit_changes({
            first: self.record("ação-primeira"),
            second: self.record("ação-segunda"),
        })
        old, new = self.commit_changes({
            first: self.record("acao-primeira"),
            second: self.record("acao-segunda"),
        })
        environment = {
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
            "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "canonical-id-repair",
            "WIKI_V2_AUTHENTICATED_REPAIR_SHA256": "0" * 64,
        }
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "exatamente um shard"):
            GUARD.check(old, new)

    def test_guard_rejects_nfkd_equivalent_global_alias(self):
        target = self.root / "data/editorial/v2_pages/civil-repair-07.jsonl"
        alias = self.root / "data/editorial/v2_pages/civil-repair-08.jsonl"
        self.commit_changes({
            target: self.record("seguro-aéreo-bagagem"),
            alias: self.record("seguro-ae\u0301reo-bagagem"),
        })
        old, new = self.commit_changes({
            target: self.record("seguro-aereo-bagagem"),
        })
        environment = self.environment(old, new, target)
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "alias NFKD global"):
            GUARD.check(old, new)

    def test_guard_recovery_uses_current_candidate_not_mutable_worktree(self):
        environment = self.environment(self.old, self.new, self.target)
        self.target.write_bytes(self.record(
            "seguro-maritimo-carga", title="Edição concorrente posterior"))
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "worktree diverge"):
            GUARD.check(self.old, self.new)

        recovery = dict(environment)
        recovery["WIKI_V2_AUTHENTICATED_RECOVERY_OID"] = self.new
        with mock.patch.dict(os.environ, recovery, clear=True):
            GUARD.check(self.old, self.new)

        recovery["WIKI_V2_AUTHENTICATED_RECOVERY_OID"] = self.old
        with mock.patch.dict(os.environ, recovery, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "bind do commit"):
            GUARD.check(self.old, self.new)

    def test_mass_fallback_recovery_also_ignores_only_post_cas_worktree(self):
        portfolio = self.root / "data/editorial/portfolio_v2/seguros.jsonl"
        target = self.root / "data/editorial/v2_pages/seguros-mass-09.jsonl"
        self.commit_changes({
            portfolio: b'{"intent_id":"intent-mass"}\n',
            target: self.record("intent-mass", title="Versão anterior"),
        })
        old, new = self.commit_changes({
            target: self.record("intent-mass", title="Versão candidata"),
        })
        relative = self.relative(target)
        mode, oid = GUARD.tree_entry(new, relative)
        environment = {
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
            "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "mass",
            "WIKI_V2_AUTHENTICATED_CLOSURE_SHA256": GUARD.receipt_digest(
                old, new, [(relative, mode, oid)]),
        }
        target.write_bytes(self.record(
            "intent-mass", title="Edição posterior ao CAS"))
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "worktree diverge"):
            GUARD.check(old, new)
        environment["WIKI_V2_AUTHENTICATED_RECOVERY_OID"] = new
        with mock.patch.dict(os.environ, environment, clear=True):
            GUARD.check(old, new)

    def test_guard_rejects_extra_change_and_public_flag(self):
        path = self.root / "data/editorial/v2_pages/civil-repair-04.jsonl"
        self.commit_changes({path: self.record("ação-terceira")})
        old, new = self.commit_changes({
            path: self.record("acao-terceira", title="Outro título"),
        })
        environment = {
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
            "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "canonical-id-repair",
            "WIKI_V2_AUTHENTICATED_REPAIR_SHA256": "0" * 64,
        }
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "bytes extras"):
            GUARD.check(old, new)

        public_path = (
            self.root / "data/editorial/v2_pages/civil-repair-05.jsonl")
        self.commit_changes({
            public_path: self.record("ação-publica", public=True),
        })
        old, new = self.commit_changes({
            public_path: self.record("acao-publica", public=True),
        })
        environment.update({
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
        })
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "flag pública aberta"):
            GUARD.check(old, new)

    def test_guard_rejects_add_delete_and_unsafe_worktree_identity(self):
        added = self.root / "data/editorial/v2_pages/civil-added-06.jsonl"
        old, new = self.commit_changes({added: self.record("acao-adicionada")})
        environment = {
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
            "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "canonical-id-repair",
            "WIKI_V2_AUTHENTICATED_REPAIR_SHA256": "0" * 64,
        }
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaises(GUARD.GuardError):
            GUARD.check(old, new)
        old, new = self.commit_changes({added: None})
        environment.update({
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": new,
            "WIKI_V2_AUTHENTICATED_OLD_OID": old,
        })
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaises(GUARD.GuardError):
            GUARD.check(old, new)

        environment = self.environment(self.old, self.new, self.target)
        candidate_payload = GUARD.blob(self.new, self.relative(self.target))
        external = self.root / "external-guard.jsonl"
        external.write_bytes(candidate_payload)
        self.target.unlink()
        self.target.symlink_to(external)
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaises(GUARD.GuardError):
            GUARD.check(self.old, self.new)
        self.target.unlink()
        os.link(external, self.target)
        with mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "regular único"):
            GUARD.check(self.old, self.new)


class SemanticRecutPrivateClosureTest(unittest.TestCase):
    LOADED_DIRTY_HELPERS = {
        "tools/lgpd_current_legal_facts.py": "100644",
        "tools/audit_v2_pages.py": "100755",
        "tools/generate_v2_review_queue.py": "100644",
        "tools/v2_portfolio_intent_migrations.py": "100644",
        "tools/verify-v2-workflow-results": "100755",
    }
    PRIVATE_DISTINCTNESS_SOURCES = {
        "cmd/check-v2-private-distinctness/main.go",
        "cmd/check-v2-private-distinctness/main_test.go",
        "internal/v2pagedistinctness/batch.go",
        "internal/v2pagedistinctness/compare.go",
        "internal/v2pagedistinctness/compare_test.go",
        "internal/v2pagedistinctness/immutable_query.go",
        "internal/v2pagedistinctness/global_partition.go",
        "internal/v2pagedistinctness/global_partition_scratch.go",
        "internal/v2pagedistinctness/global_partition_scratch_linux.go",
        "internal/v2pagedistinctness/global_partition_scratch_other.go",
        "internal/v2pagedistinctness/global_partition_test.go",
        "internal/v2pagedistinctness/global_profile_adjudication.go",
        "internal/v2pagedistinctness/global_profile_sidecar.go",
        "internal/v2pagedistinctness/global_profile_sidecar_test.go",
        "internal/v2pagedistinctness/partition_census.go",
        "internal/v2pagedistinctness/partition_census_test.go",
        "internal/v2pagedistinctness/partition_stream.go",
        "internal/v2pagedistinctness/partition_stream_test.go",
        "internal/v2pagedistinctness/posting.go",
        "internal/v2pagedistinctness/posting_test.go",
        "internal/v2pagedistinctness/profile.go",
        "internal/v2pagedistinctness/querycursor.go",
        "internal/v2pagedistinctness/querycursor_test.go",
        "internal/v2pagedistinctness/store.go",
        "internal/v2pagedistinctness/store_test.go",
        "internal/v2pagedistinctness/termdirectory.go",
        "internal/v2pagedistinctness/types.go",
        "internal/v2pagedistinctness/update_lock_other.go",
    }
    AUDITOR_PAIRED_TEST = "tools/test_audit_v2_pages_portfolio_membership.py"

    def setUp(self) -> None:
        self.page = "data/editorial/v2_pages/familia-11.jsonl"
        self.portfolio = "data/editorial/portfolio_v2/familia.jsonl"
        self.paths = sorted(
            set(GUARD.SEMANTIC_FIXED_CLOSURE) |
            set(GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES) |
            set(GUARD.SEMANTIC_DUPLICATE_NORMALIZATIONS) |
            set(GUARD.SEMANTIC_CANONICAL_ID_NORMALIZATIONS) |
            set(GUARD.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS) |
            {self.page, self.portfolio})
        self.old = "1" * 40
        self.new = "2" * 40
        self.entries = [(
            path, GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path, "100644"),
            hashlib.sha1(path.encode()).hexdigest()) for path in self.paths]
        self.receipt = GUARD.semantic_recut_receipt_digest(
            self.old, self.new, self.entries)
        self.page_payload = (json.dumps({
            "intent_id": "fam-recut", "index_policy": "noindex",
            "publication_allowed": False, "render_allowed": False,
            "sitemap_allowed": False, "public_path": "",
        }, separators=(",", ":")) + "\n").encode()

    def guard(self, paths: list[str] | None = None, *, receipt: str | None = None):
        selected = self.paths if paths is None else paths
        entries = {path: (
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path, "100644"),
            hashlib.sha1(path.encode()).hexdigest())
                   for path in set(self.paths) | set(selected)}
        selected_entries = [(path, *entries[path]) for path in selected]
        selected_receipt = GUARD.semantic_recut_receipt_digest(
            self.old, self.new, selected_entries)
        environment = {
            "WIKI_V2_AUTHENTICATED_SEMANTIC_RECUT_SHA256":
                selected_receipt if receipt is None else receipt,
        }
        with mock.patch.object(GUARD, "changed_paths", return_value=selected), \
                mock.patch.object(GUARD, "tree_entry",
                                  side_effect=lambda _commit, path: entries[path]), \
                mock.patch.object(GUARD, "portfolio_membership",
                                  return_value={"fam-recut": 1}), \
                mock.patch.object(GUARD, "blob", return_value=self.page_payload), \
                mock.patch.object(
                    GUARD, "check_semantic_duplicate_normalizations"), \
                mock.patch.object(
                    GUARD, "check_semantic_canonical_id_normalizations"), \
                mock.patch.object(
                    GUARD, "check_semantic_exact_forward_normalizations"), \
                mock.patch.dict(os.environ, environment, clear=True):
            GUARD.check_semantic_recut(self.old, self.new, [self.page])

    def test_exact_private_closure_accepts_parent_candidate_digest(self):
        self.guard()

    def test_carried_anchor_accepted_extra_stale_env_and_partial_rejected(self):
        # Derived closure (plano 2026-07-22 Fase 1): every fixed anchor may be
        # carried unchanged outside the delta.  The mocked tree returns the
        # same entry on both sides, so each single omission must now PASS.
        for anchor in sorted(GUARD.SEMANTIC_FIXED_CLOSURE):
            carried = [path for path in self.paths if path != anchor]
            self.guard(carried)
        # Controls that must stay red: widened argv path, forged/stale
        # receipt, and a partial closure without portfolio/normalizations.
        extra = self.paths + ["notes/argv-widened.txt"]
        with self.assertRaisesRegex(GUARD.GuardError, "fora da closure"):
            self.guard(extra)
        with self.assertRaisesRegex(GUARD.GuardError, "receipt"):
            self.guard(receipt="0" * 64)
        partial = [path for path in self.paths
                   if GUARD.PORTFOLIO.fullmatch(path) is None]
        with self.assertRaisesRegex(
                GUARD.GuardError, "portfolio|normalização forward"):
            self.guard(partial)

    def test_immutable_anchor_unchanged_is_accepted_and_divergent_rejected(self):
        immutable = sorted(GUARD.SEMANTIC_FIXED_CLOSURE)
        self.assertTrue(immutable)
        for anchor in immutable:
            # Later generation: the anchor already belongs to HEAD unchanged
            # (first generation landed by aff5fd7e, second by 3d97d239) and
            # legitimately stays out of the delta — all four anchors now
            # follow the same carried-unchanged rule.
            self.guard([path for path in self.paths if path != anchor])
        anchor = immutable[0]
        selected = [path for path in self.paths if path != anchor]
        entries = {path: (
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path, "100644"),
            hashlib.sha1(path.encode()).hexdigest()) for path in self.paths}
        divergent = dict(entries)
        selected_entries = [(path, *entries[path]) for path in selected]
        receipt = GUARD.semantic_recut_receipt_digest(
            self.old, self.new, selected_entries)

        def tree_entry(commit: str, path: str) -> tuple[str, str]:
            if commit == self.new and path == anchor:
                return ("100644", "f" * 40)
            return divergent[path]

        with mock.patch.object(
                GUARD, "changed_paths", return_value=selected), \
                mock.patch.object(
                    GUARD, "tree_entry", side_effect=tree_entry), \
                mock.patch.dict(os.environ, {
                    "WIKI_V2_AUTHENTICATED_SEMANTIC_RECUT_SHA256": receipt,
                }, clear=True), \
                self.assertRaisesRegex(
                    GUARD.GuardError, "divergiu fora do delta"):
            GUARD.check_semantic_recut(self.old, self.new, [self.page])

    def test_landed_normalization_rejects_rejoining_delta(self):
        path, authority = next(iter(
            GUARD.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS.items()))
        landed = {target: (
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(target, "100644"),
            hashlib.sha1(target.encode()).hexdigest())
            for target in self.paths}
        landed[path] = ("100644", authority[1])
        selected = self.paths
        receipt = GUARD.semantic_recut_receipt_digest(
            self.old, self.new, [(target, *landed[target])
                                 for target in selected])
        with mock.patch.object(
                GUARD, "changed_paths", return_value=selected), \
                mock.patch.object(
                    GUARD, "tree_entry",
                    side_effect=lambda _commit, target: landed[target]), \
                mock.patch.dict(os.environ, {
                    "WIKI_V2_AUTHENTICATED_SEMANTIC_RECUT_SHA256": receipt,
                }, clear=True), \
                self.assertRaisesRegex(
                    GUARD.GuardError, "já pousada não aceita novo delta"):
            GUARD.check_semantic_recut(self.old, self.new, [self.page])

    def test_landed_normalization_payloads_bind_pinned_preimage(self):
        path, authority = next(iter(
            GUARD.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS.items()))
        old_oid, new_oid = authority[0], authority[1]
        entries = {
            (self.old, path): ("100644", new_oid),
            (self.new, path): ("100644", new_oid),
        }
        with mock.patch.object(
                GUARD, "tree_entry",
                side_effect=lambda commit, target: entries[(commit, target)]), \
                mock.patch.object(
                    GUARD, "blob_by_oid", return_value=b"old\n") as by_oid, \
                mock.patch.object(GUARD, "blob", return_value=b"new\n"):
            self.assertEqual(
                GUARD.semantic_normalization_payloads(
                    self.old, self.new, path, old_oid, new_oid),
                (b"old\n", b"new\n"))
        by_oid.assert_called_once_with(old_oid)
        divergent = dict(entries)
        divergent[(self.new, path)] = ("100644", "f" * 40)
        with mock.patch.object(
                GUARD, "tree_entry",
                side_effect=lambda commit, target: divergent[(commit, target)]), \
                self.assertRaisesRegex(
                    GUARD.GuardError, "pousada divergiu no candidate OID"):
            GUARD.semantic_normalization_payloads(
                self.old, self.new, path, old_oid, new_oid)

    def test_duplicate_normalization_omission_is_rejected(self):
        missing = [path for path in self.paths
                   if path != next(iter(GUARD.SEMANTIC_DUPLICATE_NORMALIZATIONS))]
        with self.assertRaisesRegex(GUARD.GuardError, "duplicate normalization"):
            self.guard(missing)

    def test_exact_forward_normalization_omission_is_rejected(self):
        omitted = next(iter(GUARD.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS))
        with self.assertRaisesRegex(GUARD.GuardError, "normalização forward"):
            self.guard([path for path in self.paths if path != omitted])

    def test_canonical_normalization_rejects_extra_second_line_and_wrong_fold(self):
        path = next(iter(TOOL.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS))
        closed = (b'{"intent_id":"seguro-mar\xc3\xadtimo-avaria-carga-protesto",'
                  b'"public":false,"publication_allowed":false,'
                  b'"publication_candidate":false,"render_allowed":false,'
                  b'"sitemap_allowed":false,"indexable":false,'
                  b'"index_policy":"noindex","approval":false,'
                  b'"public_path":""}\n')
        second = (b'{"intent_id":"seguro-segunda-linha","public":false,'
                  b'"publication_allowed":false,"publication_candidate":false,'
                  b'"render_allowed":false,"sitemap_allowed":false,'
                  b'"indexable":false,"index_policy":"noindex",'
                  b'"approval":false,"public_path":""}\n')
        old = closed + second
        good = closed.replace(b"mar\xc3\xadtimo", b"maritimo", 1) + second
        self.assertEqual(
            TOOL._validate_canonical_id_repair_payloads(old, good, path)[2:],
            (1, 2))
        bad_candidates = (
            good.replace(b'"public_path":""', b'"public_path":"x"', 1),
            good[:-1] + b" \n",
            closed.replace(b"mar\xc3\xadtimo", b"mar-timo", 1) + second,
        )
        for bad in bad_candidates:
            with self.assertRaises(TOOL.CommitVerificationError):
                TOOL._validate_canonical_id_repair_payloads(old, bad, path)

    def test_finalized_exact_forward_normalization_rejects_wrong_mode(self):
        path, authority = next(iter(
            GUARD.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS.items()))
        old_oid, new_oid, _, _, _, _ = authority
        payloads = {
            (self.old, path): subprocess.run(
                ["/usr/bin/git", "-C", os.fspath(ROOT), "cat-file", "blob",
                 old_oid], stdout=subprocess.PIPE, check=True).stdout,
            (self.new, path): subprocess.run(
                ["/usr/bin/git", "-C", os.fspath(ROOT), "cat-file", "blob",
                 new_oid], stdout=subprocess.PIPE, check=True).stdout,
        }
        entries = {
            (self.old, path): ("100644", old_oid),
            (self.new, path): ("100755", new_oid),
        }
        with mock.patch.object(
                GUARD, "tree_entry",
                side_effect=lambda commit, target: entries[(commit, target)]), \
                mock.patch.object(
                    GUARD, "blob",
                    side_effect=lambda commit, target: payloads[(commit, target)]), \
                self.assertRaisesRegex(GUARD.GuardError, "OID"):
            GUARD.check_semantic_exact_forward_normalizations(
                self.old, self.new)

    def test_page_and_portfolio_executable_modes_are_rejected(self):
        for target in (self.page, self.portfolio):
            selected = self.paths
            entries = {
                path: (GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(
                    path, "100644"), hashlib.sha1(path.encode()).hexdigest())
                for path in selected
            }
            entries[target] = ("100755", entries[target][1])
            receipt = GUARD.semantic_recut_receipt_digest(
                self.old, self.new,
                [(path, *entries[path]) for path in selected])
            with self.subTest(path=target), \
                    mock.patch.object(
                        GUARD, "changed_paths", return_value=selected), \
                    mock.patch.object(
                        GUARD, "tree_entry",
                        side_effect=lambda _commit, path: entries[path]), \
                    mock.patch.dict(
                        os.environ, {
                            "WIKI_V2_AUTHENTICATED_SEMANTIC_RECUT_SHA256":
                                receipt,
                        }, clear=True), \
                    self.assertRaisesRegex(GUARD.GuardError, "modo fixo"):
                GUARD.check_semantic_recut(
                    self.old, self.new, [self.page])

    def test_runtime_bootstrap_preintegrated_unchanged_is_accepted(self):
        runtime = next(iter(GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES))
        missing = [path for path in self.paths if path != runtime]
        self.guard(missing)
        selected = self.paths
        entries = {path: ("100644", hashlib.sha1(path.encode()).hexdigest())
                   for path in selected}
        for path, mode in GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.items():
            entries[path] = (mode, entries[path][1])
        entries[runtime] = (
            "100644" if entries[runtime][0] == "100755" else "100755",
            entries[runtime][1])
        with mock.patch.object(GUARD, "changed_paths", return_value=selected), \
                mock.patch.object(GUARD, "tree_entry",
                                  side_effect=lambda _commit, path: entries[path]):
            with self.assertRaisesRegex(GUARD.GuardError, "modo fixo"):
                GUARD.check_semantic_recut(self.old, self.new, [self.page])

    def test_runtime_missing_or_mutated_outside_delta_is_rejected(self):
        runtime = next(iter(GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES))
        selected = [path for path in self.paths if path != runtime]
        entries = {path: (
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path, "100644"),
            hashlib.sha1(path.encode()).hexdigest()) for path in self.paths}
        receipt = GUARD.semantic_recut_receipt_digest(
            self.old, self.new, [(path, *entries[path]) for path in selected])
        environment = {
            "WIKI_V2_AUTHENTICATED_SEMANTIC_RECUT_SHA256": receipt}

        def missing(commit, path):
            if commit == self.new and path == runtime:
                raise GUARD.GuardError("runtime ausente")
            return entries[path]

        with mock.patch.object(GUARD, "changed_paths", return_value=selected), \
                mock.patch.object(GUARD, "tree_entry", side_effect=missing), \
                mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "runtime ausente"):
            GUARD.check_semantic_recut(self.old, self.new, [self.page])

        def mutated(commit, path):
            mode, oid = entries[path]
            if path == runtime and commit == self.old:
                oid = "f" * 40
            return mode, oid

        with mock.patch.object(GUARD, "changed_paths", return_value=selected), \
                mock.patch.object(GUARD, "tree_entry", side_effect=mutated), \
                mock.patch.dict(os.environ, environment, clear=True), \
                self.assertRaisesRegex(GUARD.GuardError, "fora do delta"):
            GUARD.check_semantic_recut(self.old, self.new, [self.page])

    def test_loaded_dirty_helpers_have_exact_stage_zero_modes(self):
        self.assertTrue(set(self.LOADED_DIRTY_HELPERS).issubset(
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES))
        self.assertEqual(
            {path: GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES[path]
             for path in self.LOADED_DIRTY_HELPERS},
            self.LOADED_DIRTY_HELPERS)

    def test_private_hook_compile_helpers_are_closed_and_materialized(self):
        expected = {
            "tools/check-go-index-compile-closure": "100755",
            "tools/check-go-compile-closure": "100755",
        }
        self.assertEqual(
            {path: TOOL.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path)
             for path in expected}, expected)
        self.assertEqual(
            {path: GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path)
             for path in expected}, expected)
        self.assertTrue(set(expected).issubset(TOOL.GO_SOURCE_ROOTS))
        self.assertEqual(
            tuple(path.removeprefix("tools/") for path in expected),
            TOOL.HOOK_RUNTIME_TOOLS)

    def test_private_distinctness_candidate_sources_are_fixed_non_executable(self):
        self.assertEqual(
            TOOL.SEMANTIC_BOOTSTRAP_RUNTIME_MODES,
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES)
        self.assertEqual(
            {
                path: (
                    value["old_oid"], value["new_oid"],
                    value["old_sha256"], value["new_sha256"],
                    value["old_rows"], value["new_rows"],
                )
                for path, value in
                TOOL.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS.items()
            },
            GUARD.SEMANTIC_EXACT_FORWARD_NORMALIZATIONS,
        )
        self.assertEqual(
            {path: GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(path)
             for path in self.PRIVATE_DISTINCTNESS_SOURCES},
            {path: "100644" for path in self.PRIVATE_DISTINCTNESS_SOURCES})

    def test_final_guard_tree_entry_accepts_authenticated_executable_runtime(self):
        path = "tools/commit-verified-v2-workflow-results"
        oid = "a" * 40
        entry = f"100755 blob {oid}\t{path}\0".encode("ascii")
        with mock.patch.object(GUARD, "git", return_value=entry):
            self.assertEqual(GUARD.tree_entry(self.new, path), ("100755", oid))

        bad = f"120000 blob {oid}\t{path}\0".encode("ascii")
        with mock.patch.object(GUARD, "git", return_value=bad), \
                self.assertRaisesRegex(GUARD.GuardError, "100644/100755"):
            GUARD.tree_entry(self.new, path)

    def test_candidate_go_source_overlays_head_snapshot(self):
        relative = "cmd/check-v2-private-distinctness/main.go"
        payload = b"package main\n"
        item = {
            "path": relative, "mode": "100644", "sha256": digest(payload),
            "git_blob_oid": TOOL._git_blob_oid(payload, "sha1"),
        }
        epoch = types.SimpleNamespace(
            closure=(item,), closure_payloads={relative: payload},
            object_format="sha1")
        with tempfile.TemporaryDirectory() as raw:
            snapshot = pathlib.Path(raw)
            target = snapshot / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(b"package head_bad\n")
            divergent_worktree = snapshot / "untrusted-worktree" / relative
            divergent_worktree.parent.mkdir(parents=True)
            divergent_worktree.write_bytes(b"package worktree_bad\n")
            manifest = TOOL._overlay_candidate_go_sources(
                epoch, snapshot, [{
                    "path": relative, "mode": "100644", "oid": "0" * 40,
                    "sha256": digest(b"package head_bad\n")}], {})
            self.assertEqual(target.read_bytes(), payload)
            self.assertEqual(divergent_worktree.read_bytes(),
                             b"package worktree_bad\n")
            self.assertEqual(manifest[0]["path"], relative)
            self.assertEqual(manifest[0]["oid"], item["git_blob_oid"])

    def test_auditor_paired_test_is_mandatory_non_executable_runtime(self):
        self.assertEqual(
            GUARD.SEMANTIC_BOOTSTRAP_RUNTIME_MODES.get(
                self.AUDITOR_PAIRED_TEST), "100644")
        missing = [path for path in self.paths
                   if path != self.AUDITOR_PAIRED_TEST]
        self.guard(missing)

    def test_staged_blob_accepts_executable_hook_only_at_fixed_mode(self):
        path = ".githooks/pre-commit"
        payload = b"#!/bin/sh\nexit 0\n"
        oid = TOOL._git_blob_oid(payload, "sha1")
        completed = types.SimpleNamespace(stdout=payload)
        with mock.patch.object(TOOL, "_run_git", return_value=completed):
            item, observed = TOOL._staged_blob(
                ROOT, path, ("100755", oid, "0"), "sha1",
                expected_mode="100755")
            self.assertEqual(item["mode"], "100755")
            self.assertEqual(observed, payload)
            for wrong_mode in ("100644", "100664"):
                with self.assertRaisesRegex(
                        TOOL.CommitVerificationError, "stage-zero 100755"):
                    TOOL._staged_blob(
                        ROOT, path, (wrong_mode, oid, "0"), "sha1",
                        expected_mode="100755")

    def test_duplicate_normalization_rejects_second_value_and_extra_bytes(self):
        flags = (
            b',"publication_candidate":false,"public":false,'
            b'"indexable":false,"publication_allowed":false,'
            b'"render_allowed":false,"sitemap_allowed":false,'
            b'"approval":false,"index_policy":"noindex","public_path":""')
        old = (b'{"intent_id":"x","page_type":"verbete"' + flags +
               b',"page_type":"verbete"}\n')
        expected = old.replace(b',"page_type":"verbete"', b"", 1)
        authority = {
            "old_sha256": digest(old), "new_sha256": digest(expected),
            "rows": 1,
        }
        TOOL._validate_semantic_duplicate_normalization(
            "data/editorial/v2_pages/fixture-01.jsonl",
            old, expected, authority)
        remove_second = old.rsplit(b',"page_type":"verbete"', 1)[0] + b'}\n'
        different_value = old.replace(
            b',"page_type":"verbete"}', b',"page_type":"guia"}', 1)
        extra = expected.replace(b'}\n', b',"extra":false}\n')
        for candidate in (remove_second, different_value, extra):
            bad = dict(authority)
            bad["new_sha256"] = digest(candidate)
            with self.assertRaises(TOOL.CommitVerificationError):
                TOOL._validate_semantic_duplicate_normalization(
                    "data/editorial/v2_pages/fixture-01.jsonl",
                    old, candidate, bad)

    def test_finalized_normalization_rejects_wrong_parent_or_candidate_oid(self):
        entries: dict[tuple[str, str], tuple[str, str]] = {}
        payloads: dict[tuple[str, str], bytes] = {}
        for path, authority in GUARD.SEMANTIC_DUPLICATE_NORMALIZATIONS.items():
            old_oid, new_oid, _old_sha, _new_sha, _rows = authority
            entries[(self.old, path)] = ("100644", old_oid)
            entries[(self.new, path)] = ("100644", new_oid)
            payloads[(self.old, path)] = subprocess.run(
                ["/usr/bin/git", "-C", os.fspath(ROOT), "cat-file", "blob", old_oid],
                stdout=subprocess.PIPE, check=True).stdout
            payloads[(self.new, path)] = subprocess.run(
                ["/usr/bin/git", "-C", os.fspath(ROOT), "cat-file", "blob", new_oid],
                stdout=subprocess.PIPE, check=True).stdout
        with mock.patch.object(
                GUARD, "tree_entry", side_effect=lambda commit, path: entries[(commit, path)]), \
                mock.patch.object(
                    GUARD, "blob", side_effect=lambda commit, path: payloads[(commit, path)]):
            GUARD.check_semantic_duplicate_normalizations(self.old, self.new)
        wrong = dict(entries)
        first = next(iter(GUARD.SEMANTIC_DUPLICATE_NORMALIZATIONS))
        wrong[(self.old, first)] = ("100644", "0" * 40)
        with mock.patch.object(
                GUARD, "tree_entry", side_effect=lambda commit, path: wrong[(commit, path)]), \
                self.assertRaisesRegex(GUARD.GuardError, "OID"):
            GUARD.check_semantic_duplicate_normalizations(self.old, self.new)
        wrong = dict(entries)
        wrong[(self.new, first)] = ("100644", "f" * 40)
        with mock.patch.object(
                GUARD, "tree_entry", side_effect=lambda commit, path: wrong[(commit, path)]), \
                self.assertRaisesRegex(GUARD.GuardError, "OID"):
            GUARD.check_semantic_duplicate_normalizations(self.old, self.new)

    def test_recovery_is_bound_to_exact_live_candidate_and_not_replayable(self):
        environment = {"WIKI_V2_AUTHENTICATED_RECOVERY_OID": self.new}
        with mock.patch.dict(os.environ, environment, clear=True), \
                mock.patch.object(GUARD, "git", return_value=("3" * 40 + "\n").encode()), \
                self.assertRaisesRegex(GUARD.GuardError, "HEAD atual"):
            GUARD.authenticated_recovery(self.new)

    def test_minimal_portfolio_excludes_unrelated_staged_row(self):
        old_bound = b'{"intent_id":"bound","working_title":"old"}'
        old_other = b'{"intent_id":"other","working_title":"old"}'
        new_bound = b'{"intent_id":"bound","working_title":"reviewed"}'
        new_other = b'{"intent_id":"other","working_title":"unrelated"}'
        parent = old_bound + b"\n" + old_other + b"\n"
        staged = new_bound + b"\n" + new_other + b"\n"
        candidate = TOOL._minimal_semantic_portfolio_payload(
            "data/editorial/portfolio_v2/familia.jsonl", parent, staged,
            [{"intent_id": "bound",
              "portfolio_record_sha256": digest(new_bound)}])
        self.assertEqual(candidate, new_bound + b"\n" + old_other + b"\n")
        self.assertNotIn(new_other, candidate)

    def test_staged_candidate_bytes_do_not_read_divergent_worktree(self):
        payload = b"candidate-stage-zero\n"
        item = {
            "path": self.page, "mode": "100644",
            "sha256": digest(payload),
            "git_blob_oid": TOOL._git_blob_oid(payload, "sha1"),
            "role": "semantic_recut_staged_closure",
        }
        transaction = types.SimpleNamespace(
            kind="semantic-recut", staged_candidates={self.page: item},
            staged_payloads={self.page: payload})
        candidates, payloads = TOOL._authenticated_candidates(
            transaction, "sha1")
        self.assertEqual(candidates[self.page], item)
        self.assertEqual(payloads[self.page], payload)

    def test_authenticated_candidates_accepts_only_fixed_executable_hook_mode(self):
        path = ".githooks/pre-commit"
        payload = b"#!/bin/sh\nexit 0\n"
        base = {
            "path": path, "mode": "100755", "sha256": digest(payload),
            "git_blob_oid": TOOL._git_blob_oid(payload, "sha1"),
            "role": "semantic_recut_staged_closure",
        }
        transaction = types.SimpleNamespace(
            kind="semantic-recut", staged_candidates={path: base},
            staged_payloads={path: payload})
        candidates, observed = TOOL._authenticated_candidates(
            transaction, "sha1")
        self.assertEqual(candidates[path]["mode"], "100755")
        self.assertEqual(observed[path], payload)
        for wrong_mode in ("100644", "100664"):
            wrong = dict(base, mode=wrong_mode)
            transaction.staged_candidates = {path: wrong}
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "divergiu no blob staged"):
                TOOL._authenticated_candidates(transaction, "sha1")

    def test_authenticated_candidates_accepts_executable_loaded_helpers(self):
        payload = b"#!/usr/bin/python3\n"
        oid = TOOL._git_blob_oid(payload, "sha1")
        for path in (
                "tools/audit_v2_pages.py",
                "tools/verify-v2-workflow-results"):
            base = {
                "path": path, "mode": "100755", "sha256": digest(payload),
                "git_blob_oid": oid, "role": "semantic_recut_staged_closure",
            }
            transaction = types.SimpleNamespace(
                kind="semantic-recut", staged_candidates={path: base},
                staged_payloads={path: payload})
            candidates, _ = TOOL._authenticated_candidates(transaction, "sha1")
            self.assertEqual(candidates[path]["mode"], "100755")
            for wrong_mode in ("100644", "100664"):
                transaction.staged_candidates = {
                    path: dict(base, mode=wrong_mode)}
                with self.assertRaisesRegex(
                        TOOL.CommitVerificationError, "divergiu no blob staged"):
                    TOOL._authenticated_candidates(transaction, "sha1")


class IsolatedCliBoundaryTest(unittest.TestCase):
    def test_python_closure_has_all_transitive_helpers_and_no_repo_sys_path(self):
        names = {name for name, _ in TOOL.PYTHON_HELPERS}
        self.assertTrue({
            "tools.tema987_current_legal_facts",
            "tools.lgpd_current_legal_facts",
            "tools.sample_review_current_legal_facts",
            "tools.imobiliario09_current_legal_facts",
            "tools.audit_v2_pages",
            "tools.generate_v2_review_queue",
            "tools.v2_portfolio_intent_migrations",
        }.issubset(names))
        source = TOOL_PATH.read_text(encoding="utf-8")
        self.assertNotIn("canonical = [os.fspath(INSTALL_ROOT)]", source)
        self.assertNotIn("GATE_BINARY_CACHE_RELS", source)
        self.assertNotIn(".cache/go-cmd-bin", source)

    def test_direct_shebang_ignores_pythonpath_and_external_tools_package(self):
        with tempfile.TemporaryDirectory() as raw:
            evil = pathlib.Path(raw)
            marker = evil / "executed"
            (evil / "sitecustomize.py").write_text(
                "from pathlib import Path\nPath(" + repr(os.fspath(marker)) +
                ").write_text('sitecustomize')\n", encoding="utf-8")
            package = evil / "tools"
            package.mkdir()
            (package / "__init__.py").write_text(
                "from pathlib import Path\nPath(" + repr(os.fspath(marker)) +
                ").write_text('external-tools')\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.fspath(evil)
            environment["PYTHONUSERBASE"] = os.fspath(evil)
            completed = subprocess.run(
                [os.fspath(TOOL_PATH), "--kind", "mass", "--root",
                 os.fspath(evil / "missing-root"), "--results", "/dev/null",
                 "--message", "content(v2): isolation boundary probe"],
                cwd=ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False)
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(marker.exists(), completed.stderr.decode(
                "utf-8", errors="replace"))

    def test_retired_lease_and_forged_argv_are_rejected(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        self.assertNotIn("check-index-lease-fd", source)
        self.assertNotIn("producer_ancestor", source)
        completed = subprocess.run(
            [os.fspath(TOOL_PATH), "--kind", "mass", "--message",
             "content(v2): forged retired lease argv",
             "--check-index-lease-fd", "3"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unrecognized arguments", completed.stderr.decode(
            "utf-8", errors="replace"))


class AuthenticatedToolchainBoundaryTest(unittest.TestCase):
    def test_private_goroot_comes_from_pinned_archive_not_mutable_extracted_tree(self):
        self.assertEqual(
            digest(TOOL.GO_ARCHIVE.read_bytes()), TOOL.GO_ARCHIVE_SHA256)
        with tempfile.TemporaryDirectory(dir="/tmp") as raw:
            workspace = pathlib.Path(raw)
            poisoned = workspace / "mutable-extracted" / "bin" / "go"
            poisoned.parent.mkdir(parents=True)
            poisoned.write_bytes(b"#!/bin/sh\nexit 0\n")
            poisoned.chmod(0o755)
            go_binary, archive_sha, _ = TOOL._extract_pinned_go_toolchain(
                workspace)
            self.assertEqual(archive_sha, TOOL.GO_ARCHIVE_SHA256)
            self.assertTrue(go_binary.is_relative_to(workspace))
            self.assertNotEqual(go_binary, poisoned)
            completed = subprocess.run(
                [os.fspath(go_binary), "version"],
                env={
                    "GOROOT": os.fspath(go_binary.parent.parent),
                    "GOTOOLCHAIN": "local", "HOME": "/nonexistent",
                    "PATH": "/usr/bin:/bin",
                },
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(b"go version go1.26.4 linux/amd64", completed.stdout)

    def test_corrupted_official_archive_fails_before_compiler_execution(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as raw:
            workspace = pathlib.Path(raw)
            corrupted = workspace / "go.tar.gz"
            shutil.copyfile(TOOL.GO_ARCHIVE, corrupted)
            with corrupted.open("ab") as handle:
                handle.write(b"forged")
            with mock.patch.object(TOOL, "GO_ARCHIVE", corrupted), \
                    self.assertRaisesRegex(
                        TOOL.CommitVerificationError, "SHA256 pinado"):
                TOOL._extract_pinned_go_toolchain(workspace / "extract")

    def test_corrupted_module_zip_is_rejected_by_private_go_sum_closure(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as raw:
            root = pathlib.Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            go_binary, _, _ = TOOL._extract_pinned_go_toolchain(workspace)
            source_version = (
                pathlib.Path("/home/rafael/go/pkg/mod/cache/download") /
                "golang.org/x/time/@v")
            proxy_version = root / "proxy/golang.org/x/time/@v"
            proxy_version.mkdir(parents=True)
            for suffix in ("info", "mod", "zip", "ziphash"):
                shutil.copyfile(
                    source_version / f"v0.15.0.{suffix}",
                    proxy_version / f"v0.15.0.{suffix}")
            module_zip = proxy_version / "v0.15.0.zip"
            forged_zip = proxy_version / "v0.15.0.forged.zip"
            mutated = False
            with zipfile.ZipFile(module_zip, "r") as source, \
                    zipfile.ZipFile(forged_zip, "w") as destination:
                for member in source.infolist():
                    payload = source.read(member)
                    if not mutated and not member.is_dir():
                        payload += b"\nforged-module\n"
                        mutated = True
                    destination.writestr(member, payload)
            self.assertTrue(mutated)
            os.replace(forged_zip, module_zip)
            module = root / "module"
            module.mkdir()
            (module / "go.mod").write_text(
                "module example.invalid/private\n\n"
                "go 1.26.0\n\n"
                "require golang.org/x/time v0.15.0\n",
                encoding="utf-8")
            (module / "go.sum").write_text(
                "golang.org/x/time v0.15.0 "
                "h1:bbrp8t3bGUeFOx08pvsMYRTCVSMk89u4tKbNOZbp88U=\n"
                "golang.org/x/time v0.15.0/go.mod "
                "h1:Y4YMaQmXwGQZoFaVFk4YpCt4FLQMYKZe9oeV/f4MSno=\n",
                encoding="utf-8")
            (module / "main.go").write_text(
                "package main\n"
                "import \"golang.org/x/time/rate\"\n"
                "func main() { _ = rate.Inf }\n",
                encoding="utf-8")
            build_cache = workspace / "go-build-cache"
            module_cache = workspace / "go-module-cache"
            build_cache.mkdir()
            module_cache.mkdir()
            with mock.patch.object(TOOL, "MODULE_PROXY", root / "proxy"):
                environment = TOOL._minimal_go_environment(
                    workspace, go_binary.parent.parent,
                    build_cache, module_cache)
            completed = TOOL._run_closed_process(
                [os.fspath(go_binary), "build", "./..."], cwd=module,
                environment=environment, timeout=120)
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(
                b"checksum mismatch" in completed.stderr or
                b"SECURITY ERROR" in completed.stderr,
                completed.stderr.decode("utf-8", errors="replace"))

    def test_bounded_runner_kills_output_overflow(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as raw:
            with self.assertRaisesRegex(
                    TOOL.CommitVerificationError, "limite de stdout"):
                TOOL._run_closed_process_bounded(
                    ["/usr/bin/python3", "-c",
                     "import os,time;os.write(1,b'x'*65536);time.sleep(60)"],
                    cwd=pathlib.Path(raw),
                    environment={"PATH": "/usr/bin:/bin"}, timeout=10,
                    stdout_limit=1024, stderr_limit=1024)


class UTCDayHeadroomTest(unittest.TestCase):
    def test_rollover_inside_audit_window_refuses_entry_as_transient_busy(self):
        horizon = 2 * TOOL.HOOK_TIMEOUT_SECONDS
        with mock.patch.object(
                TOOL.time, "time", return_value=float(86400 * 100 - 100)):
            with self.assertRaises(TOOL.CommitBusy) as caught:
                TOOL._assert_utc_day_headroom_for_private_audit()
        message = str(caught.exception)
        self.assertIn("virada UTC em 100s", message)
        self.assertIn(str(horizon), message)
        self.assertIn("00:00Z", message)
        self.assertFalse(caught.exception.cas_may_have_applied)

    def test_exact_full_window_still_admits_entry(self):
        remaining = 2 * TOOL.HOOK_TIMEOUT_SECONDS
        with mock.patch.object(
                TOOL.time, "time",
                return_value=float(86400 * 100 + 86400 - remaining)):
            self.assertIsNone(
                TOOL._assert_utc_day_headroom_for_private_audit())

    def test_start_of_utc_day_admits_entry(self):
        with mock.patch.object(
                TOOL.time, "time", return_value=float(86400 * 100)):
            self.assertIsNone(
                TOOL._assert_utc_day_headroom_for_private_audit())


class UnitLedgerQuarantineRouteTest(unittest.TestCase):
    def ledger_row(self) -> dict:
        row = {
            "schema": TOOL.UNIT_LEDGER_SCHEMA,
            "unit_key": digest(b"unit"),
            "family_key": digest(b"family"),
            "kind": "mass",
            "input_oids_digest": digest(b"inputs"),
            "fingerprint": digest(b"fingerprint"),
            "run_id": os.urandom(16).hex(),
            "state": "success",
            "failure_kind": None,
            "exit_code": 0,
            "cas_may_have_applied": False,
            "result_sha256": digest(b"result"),
            "commit_oid": "0" * 40,
            "attempts": 1,
            "ts_unix_ns": time.time_ns(),
        }
        row["row_sha256"] = hashlib.sha256(
            TOOL._canonical_json(row)).hexdigest()
        return row

    def assert_quarantine_route(self, message: str) -> None:
        self.assertIn(TOOL.UNIT_LEDGER_QUARANTINE_REL, message)
        self.assertIn(TOOL.UNIT_LEDGER_REL, message)
        self.assertIn("append-only", message)
        self.assertIn("terminal.json", message)

    def test_valid_row_is_accepted(self):
        row = self.ledger_row()
        self.assertEqual(
            TOOL._validate_unit_ledger_row(row, label="fixture"), row)

    def test_schema_tamper_names_the_quarantine_route(self):
        row = self.ledger_row()
        row["attempts"] = -1
        with self.assertRaises(TOOL.CommitVerificationError) as caught:
            TOOL._validate_unit_ledger_row(row, label="ledger:7")
        message = str(caught.exception)
        self.assertIn("linha adulterada/inválida: ledger:7", message)
        self.assert_quarantine_route(message)
        # Fail-closed permanece determinístico: adulteração não é contenção.
        self.assertNotIsInstance(caught.exception, TOOL.CommitBusy)

    def test_row_sha_tamper_names_the_quarantine_route(self):
        row = self.ledger_row()
        row["kind"] = "review"
        with self.assertRaises(TOOL.CommitVerificationError) as caught:
            TOOL._validate_unit_ledger_row(row, label="ledger:9")
        message = str(caught.exception)
        self.assertIn("perdeu SHA da linha (adulteração): ledger:9", message)
        self.assert_quarantine_route(message)
        self.assertNotIsInstance(caught.exception, TOOL.CommitBusy)


if __name__ == "__main__":
    unittest.main()
