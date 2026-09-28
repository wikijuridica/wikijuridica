from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import os
import pathlib
import re
import select
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
BASE_ENV = {
    **os.environ,
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": "",
}


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _snapshot(root: pathlib.Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            payload = os.readlink(path).encode("utf-8")
        elif path.is_file():
            payload = path.read_bytes()
        else:
            continue
        result[path.relative_to(root).as_posix()] = _digest(payload)
    return result


def _changed_paths(
    before: dict[str, str], after: dict[str, str]
) -> set[str]:
    return {
        name for name in before.keys() | after.keys()
        if before.get(name) != after.get(name)
    }


def _write_jsonl(path: pathlib.Path, records: list[dict]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        "\n".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
            for record in records
        ) + "\n"
    ).encode("utf-8")
    path.write_bytes(payload)
    return payload


class WriterFixture:
    def __init__(self, test: unittest.TestCase, *tool_names: str):
        self.test = test
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "tools").mkdir()
        (self.root / "go.mod").write_text("module fixture\n", encoding="utf-8")
        for name in {"v2_stock_epoch.py", *tool_names}:
            source = TOOLS / name
            target = self.root / "tools" / name
            shutil.copy2(source, target)

    def close(self) -> None:
        self.temporary.cleanup()

    def command(
        self,
        command: list[str],
        *,
        extra_env: dict[str, str] | None = None,
        timeout: float = 30,
    ) -> subprocess.CompletedProcess[str]:
        environment = dict(BASE_ENV)
        if extra_env:
            environment.update(extra_env)
        return subprocess.run(
            command,
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )

    @contextlib.contextmanager
    def held_write_lease(self):
        code = textwrap.dedent(
            """
            import pathlib
            import sys
            from tools.v2_stock_epoch import canonical_stock_write_lease

            with canonical_stock_write_lease(pathlib.Path.cwd()):
                print("HELD", flush=True)
                sys.stdin.buffer.read(1)
            """
        )
        process = subprocess.Popen(
            [sys.executable, "-c", code],
            cwd=self.root,
            env=BASE_ENV,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert process.stdout is not None
            ready, _, _ = select.select([process.stdout], [], [], 5)
            if not ready:
                stderr = process.stderr.read() if process.stderr else ""
                self.test.fail(f"lease holder did not become ready: {stderr}")
            self.test.assertEqual(process.stdout.readline().strip(), "HELD")
            yield
        finally:
            if process.poll() is None:
                assert process.stdin is not None
                process.stdin.write("\n")
                process.stdin.flush()
                process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            stderr = process.stderr.read() if process.stderr else ""
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            if process.returncode != 0:
                self.test.fail(
                    f"lease holder exited {process.returncode}: {stderr}")


class PythonCanonicalWriterLeaseTest(unittest.TestCase):
    maxDiff = None

    def _assert_busy_preserves_tree(
        self, fixture: WriterFixture, command: list[str], *,
        extra_env: dict[str, str] | None = None,
    ) -> None:
        before = _snapshot(fixture.root)
        with fixture.held_write_lease():
            result = fixture.command(command, extra_env=extra_env)
        self.assertEqual(
            result.returncode, 75,
            f"stdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertEqual(_snapshot(fixture.root), before)

    def test_lexical_write_boundaries_cover_every_migrated_writer(self) -> None:
        expected_calls = {
            "generate-v2-word-count-refresh": {"refresh"},
            "repair-v2-tema987-pages.py": {
                "_render_file", "_atomic_replace_if_unchanged"},
            "tombstone_aereo_r06_orphans_20260717.py": {"run_locked"},
            "tombstone_aereo_r07_r08_r09_orphans_20260717.py": {
                "reconcile_shard"},
            "consolidate_v2_duplicate_intents_20260711.py": {"run_locked"},
            "_wave3_materialize.py": {"_materialize"},
            "generate-portfolio-leis-sumulas-wave2": {"apply_wave2"},
        }
        for name, required_calls in expected_calls.items():
            with self.subTest(writer=name):
                source = (TOOLS / name).read_text(encoding="utf-8")
                if source.startswith("#!/usr/bin/env bash"):
                    source = source.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
                tree = ast.parse(source, filename=name)
                guarded_calls = set()
                for node in ast.walk(tree):
                    if not isinstance(node, ast.With):
                        continue
                    if not any(
                        isinstance(item.context_expr, ast.Call)
                        and isinstance(item.context_expr.func, ast.Name)
                        and item.context_expr.func.id == "canonical_stock_write_lease"
                        for item in node.items
                    ):
                        continue
                    for descendant in ast.walk(node):
                        if not isinstance(descendant, ast.Call):
                            continue
                        if isinstance(descendant.func, ast.Name):
                            guarded_calls.add(descendant.func.id)
                        elif isinstance(descendant.func, ast.Attribute):
                            guarded_calls.add(descendant.func.attr)
                self.assertTrue(
                    required_calls <= guarded_calls,
                    f"calls outside lexical lease: {required_calls - guarded_calls}",
                )
                self.assertIn("from tools.v2_stock_epoch import", source)
                self.assertIn("StockEpochBusy", source)
                self.assertIn("75", source)
        wave2 = (TOOLS / "generate-portfolio-leis-sumulas-wave2").read_text(
            encoding="utf-8")
        self.assertNotRegex(wave2, r"open\([^\n]+['\"]a['\"]")

    def test_word_count_entrypoint_busy_and_free(self) -> None:
        fixture = WriterFixture(
            self, "generate-v2-word-count-refresh", "audit_v2_pages.py")
        self.addCleanup(fixture.close)
        target_rel = "data/editorial/v2_pages/fixture.jsonl"
        target = fixture.root / target_rel
        _write_jsonl(target, [{
            "intent_id": "fixture-word-count",
            "opening": "a b",
            "sections": [{"heading": "c", "text": "d e"}],
            "faq": [{"q": "f", "a": "g h"}],
            "word_count": 1,
        }])
        command = [
            os.fspath(fixture.root / "tools/generate-v2-word-count-refresh"),
            target_rel,
        ]
        self._assert_busy_preserves_tree(fixture, command)
        before = _snapshot(fixture.root)
        result = fixture.command(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        after = _snapshot(fixture.root)
        self.assertEqual(_changed_paths(before, after), {target_rel})
        record = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(record["word_count"], 8)

    def test_tema987_entrypoint_boundary_busy_and_free(self) -> None:
        fixture = WriterFixture(
            self, "repair-v2-tema987-pages.py", "audit_v2_pages.py")
        self.addCleanup(fixture.close)
        target_rel = "data/editorial/v2_pages/fixture.jsonl"
        target = fixture.root / target_rel
        target.parent.mkdir(parents=True)
        target.write_bytes(b"before\n")
        code = textwrap.dedent(
            """
            import importlib.util
            import os
            import pathlib

            path = pathlib.Path(os.environ["WRITER"])
            spec = importlib.util.spec_from_file_location("tema987_writer", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            relative = "data/editorial/v2_pages/fixture.jsonl"
            module.ACTIVE_PAID_INTENTS = frozenset({"fixture"})
            module.UPDATES = {"fixture": (relative, "heading", "text")}
            def render(target, intents):
                before = pathlib.Path(target).read_bytes()
                return before, b"after\\n"
            module._render_file = render
            raise SystemExit(module.main(["--apply"]))
            """
        )
        command = [sys.executable, "-c", code]
        environment = {"WRITER": os.fspath(fixture.root / "tools/repair-v2-tema987-pages.py")}
        self._assert_busy_preserves_tree(
            fixture, command, extra_env=environment)
        before = _snapshot(fixture.root)
        result = fixture.command(command, extra_env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_changed_paths(before, _snapshot(fixture.root)), {target_rel})
        self.assertEqual(target.read_bytes(), b"after\n")

    def test_aereo_r06_entrypoint_busy_and_free(self) -> None:
        fixture = WriterFixture(
            self, "tombstone_aereo_r06_orphans_20260717.py")
        self.addCleanup(fixture.close)
        target_rel = "data/editorial/v2_pages/aereo-r06.jsonl"
        target = fixture.root / target_rel
        records = [
            {"intent_id": "aer-acompanhante-pcd-desconto", "skipped": False},
            {"intent_id": "aer-animal-apoio-emocional-cabine", "skipped": False},
            {"intent_id": "unrelated", "value": 1},
        ]
        payload = _write_jsonl(target, records)
        lock_rel = (
            "data/editorial/.tombstone-aereo-r06-orphans-20260717.lock")
        code = textwrap.dedent(
            """
            import importlib.util
            import os
            import pathlib

            path = pathlib.Path(os.environ["WRITER"])
            spec = importlib.util.spec_from_file_location("aereo_r06_writer", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.EXPECTED_SOURCE_SHA = os.environ["EXPECTED_SHA"]
            raise SystemExit(module.main())
            """
        )
        command = [sys.executable, "-c", code]
        environment = {
            "WRITER": os.fspath(
                fixture.root / "tools/tombstone_aereo_r06_orphans_20260717.py"),
            "EXPECTED_SHA": _digest(payload),
        }
        self._assert_busy_preserves_tree(fixture, command, extra_env=environment)
        before = _snapshot(fixture.root)
        result = fixture.command(command, extra_env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            _changed_paths(before, _snapshot(fixture.root)),
            {target_rel, lock_rel},
        )
        output = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(output[0]["skipped"])
        self.assertTrue(output[1]["skipped"])
        self.assertEqual(output[2], records[2])

    def test_aereo_r07_r09_entrypoint_busy_and_free(self) -> None:
        fixture = WriterFixture(
            self, "tombstone_aereo_r07_r08_r09_orphans_20260717.py")
        self.addCleanup(fixture.close)
        specs = {
            "data/editorial/v2_pages/aereo-r07.jsonl": {
                "r07-a": "canonical-a", "r07-b": "canonical-b"},
            "data/editorial/v2_pages/aereo-r08.jsonl": {
                "r08-a": "canonical-a", "r08-b": "canonical-b"},
            "data/editorial/v2_pages/aereo-r09.jsonl": {
                "r09-a": "canonical-a", "r09-b": "canonical-b"},
        }
        configuration = {}
        for relative, orphans in specs.items():
            payload = _write_jsonl(
                fixture.root / relative,
                [{"intent_id": intent, "skipped": False} for intent in orphans],
            )
            configuration[relative] = [_digest(payload), orphans]
        lock_rel = (
            "data/editorial/.tombstone-aereo-r07-r08-r09-orphans-20260717.lock")
        code = textwrap.dedent(
            """
            import importlib.util
            import json
            import os
            import pathlib

            path = pathlib.Path(os.environ["WRITER"])
            spec = importlib.util.spec_from_file_location("aereo_r07_r09_writer", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.SHARDS = json.loads(os.environ["SHARDS"])
            raise SystemExit(module.main())
            """
        )
        command = [sys.executable, "-c", code]
        environment = {
            "WRITER": os.fspath(
                fixture.root /
                "tools/tombstone_aereo_r07_r08_r09_orphans_20260717.py"),
            "SHARDS": json.dumps(configuration),
        }
        self._assert_busy_preserves_tree(fixture, command, extra_env=environment)
        before = _snapshot(fixture.root)
        result = fixture.command(command, extra_env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            _changed_paths(before, _snapshot(fixture.root)),
            set(specs) | {lock_rel},
        )
        for relative, orphans in specs.items():
            rows = [
                json.loads(line) for line in
                (fixture.root / relative).read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual({row["intent_id"] for row in rows}, set(orphans))
            self.assertTrue(all(row["skipped"] for row in rows))

    def test_duplicate_consolidator_entrypoint_busy_and_free(self) -> None:
        fixture = WriterFixture(
            self, "consolidate_v2_duplicate_intents_20260711.py")
        self.addCleanup(fixture.close)
        canonical_rel = "data/editorial/v2_pages/canonical.jsonl"
        loser_rel = "data/editorial/v2_pages/loser.jsonl"
        canonical_payload = _write_jsonl(
            fixture.root / canonical_rel,
            [{"intent_id": "fixture-duplicate", "body": "canonical"}],
        )
        loser_payload = _write_jsonl(
            fixture.root / loser_rel,
            [{"intent_id": "fixture-duplicate", "body": "loser"}],
        )
        lock_rel = (
            "data/editorial/.duplicate-intent-consolidation-20260711.lock")
        archive_rel = (
            "data/editorial/v2_superseded/fixture-duplicate-consolidation.jsonl")
        configuration = {
            "canonical": "canonical.jsonl",
            "expected_shas": {
                "canonical.jsonl": _digest(canonical_payload),
                "loser.jsonl": _digest(loser_payload),
            },
            "archive_rel": archive_rel,
        }
        code = textwrap.dedent(
            """
            import importlib.util
            import json
            import os
            import pathlib

            path = pathlib.Path(os.environ["WRITER"])
            spec = importlib.util.spec_from_file_location("consolidation_writer", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            config = json.loads(os.environ["CONFIG"])
            module.CANONICAL = config["canonical"]
            module.EXPECTED_SHAS = config["expected_shas"]
            module.EXPECTED_INTENTS = {"fixture-duplicate"}
            module.ARCHIVE_REL = config["archive_rel"]
            module.ARCHIVE = module.ROOT / module.ARCHIVE_REL
            raise SystemExit(module.main())
            """
        )
        command = [sys.executable, "-c", code]
        environment = {
            "WRITER": os.fspath(
                fixture.root / "tools/consolidate_v2_duplicate_intents_20260711.py"),
            "CONFIG": json.dumps(configuration),
        }
        self._assert_busy_preserves_tree(fixture, command, extra_env=environment)
        before = _snapshot(fixture.root)
        result = fixture.command(command, extra_env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            _changed_paths(before, _snapshot(fixture.root)),
            {loser_rel, archive_rel, lock_rel},
        )
        loser = json.loads((fixture.root / loser_rel).read_text(encoding="utf-8"))
        self.assertTrue(loser["skipped"])
        self.assertEqual(loser["superseded_record_sha256"], _digest(
            loser_payload.rstrip(b"\n")))
        archive = json.loads(
            (fixture.root / archive_rel).read_text(encoding="utf-8"))
        self.assertEqual(archive["original_line"], loser_payload.decode().rstrip("\n"))
        self.assertEqual((fixture.root / canonical_rel).read_bytes(), canonical_payload)

    def test_wave3_entrypoint_busy_and_free(self) -> None:
        fixture = WriterFixture(self, "_wave3_materialize.py")
        self.addCleanup(fixture.close)
        _write_jsonl(
            fixture.root / "data/editorial/portfolio_v2/base.jsonl",
            [{
                "intent_id": "existing-intent",
                "long_tail_query": "questao preexistente",
                "practice_area": "civil",
            }],
        )
        staged = {
            "intent_id": "civil-wave3-lease-fixture",
            "page_type": "pergunta",
            "practice_area": "civil",
            "family": "civil-w3",
            "long_tail_query": "como resolver uma fixture juridica exclusiva",
            "working_title": "Como resolver a fixture jurídica exclusiva",
            "reader_problem": "Leitor precisa de uma resposta específica.",
            "lane": "informativa",
            "source_hints": ["planalto-lei-10406"],
            "needs_source_research": True,
            "distinct_because": "A resposta exige fundamento e documento próprios.",
        }
        stage_dir = fixture.root / "stage"
        _write_jsonl(stage_dir / "wave3_stage_fixture.jsonl", [staged])
        command = [
            sys.executable,
            os.fspath(fixture.root / "tools/_wave3_materialize.py"),
            os.fspath(stage_dir),
            "--write",
        ]
        self._assert_busy_preserves_tree(fixture, command)
        before = _snapshot(fixture.root)
        result = fixture.command(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        target_rel = "data/editorial/portfolio_v2/civil-w3.jsonl"
        self.assertEqual(
            _changed_paths(before, _snapshot(fixture.root)), {target_rel})
        self.assertEqual(
            json.loads((fixture.root / target_rel).read_text(encoding="utf-8")),
            staged,
        )

    def test_wave2_entrypoint_busy_and_free_without_legacy_append(self) -> None:
        fixture = WriterFixture(
            self, "generate-portfolio-leis-sumulas-wave2")
        self.addCleanup(fixture.close)
        portfolio = fixture.root / "data/editorial/portfolio_v2"
        portfolio.mkdir(parents=True)
        (portfolio / "leis.jsonl").write_bytes(b"")
        (portfolio / "sumulas.jsonl").write_bytes(b"")
        workflow = fixture.root / "scripts/workflows/writing-mass-full.js"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("const batches = []\n", encoding="utf-8")
        command = [
            os.fspath(
                fixture.root / "tools/generate-portfolio-leis-sumulas-wave2")]
        self._assert_busy_preserves_tree(fixture, command)
        before = _snapshot(fixture.root)
        result = fixture.command(command, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"onda 2: \+(\d+) leis, \+(\d+) sumulas", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        leis_count, sumulas_count = map(int, match.groups())
        changed = {
            "data/editorial/portfolio_v2/leis.jsonl",
            "data/editorial/portfolio_v2/sumulas.jsonl",
            "scripts/workflows/writing-mass-full.js",
        }
        self.assertEqual(_changed_paths(before, _snapshot(fixture.root)), changed)
        leis_rows = [
            json.loads(line) for line in
            (portfolio / "leis.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        sumulas_rows = [
            json.loads(line) for line in
            (portfolio / "sumulas.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(leis_rows), leis_count)
        self.assertEqual(len(sumulas_rows), sumulas_count)
        self.assertEqual(
            len({row["intent_id"] for row in leis_rows + sumulas_rows}),
            leis_count + sumulas_count,
        )
        workflow_text = workflow.read_text(encoding="utf-8")
        batches = json.loads(re.search(
            r"const batches = (\[.*?\])\n", workflow_text, re.DOTALL).group(1))
        self.assertEqual(sum(batch["n"] for batch in batches),
                         leis_count + sumulas_count)


if __name__ == "__main__":
    unittest.main()
