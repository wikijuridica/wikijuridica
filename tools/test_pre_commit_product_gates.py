#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
PRE_COMMIT = REPO_ROOT / ".githooks" / "pre-commit"
REFERENCE_TRANSACTION = REPO_ROOT / ".githooks" / "reference-transaction"
V2_LAUNCHER = REPO_ROOT / "tools" / "run-v2-index-product-gates"
V2_FINAL_CHECKER = REPO_ROOT / "tools" / "check-v2-finalized-commit"


class PreCommitProductGatesTest(unittest.TestCase):
    def make_fixture(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="wiki-pre-commit-product-gates-"))
        self.addCleanup(shutil.rmtree, root)
        (root / ".githooks").mkdir()
        (root / "tools").mkdir()
        for source in (PRE_COMMIT, REFERENCE_TRANSACTION):
            target = root / ".githooks" / source.name
            shutil.copyfile(source, target)
            target.chmod(0o755)

        for source in (V2_LAUNCHER, V2_FINAL_CHECKER):
            target = root / "tools" / source.name
            shutil.copyfile(source, target)
            target.chmod(0o755)

        # The Go index-closure dispatch is tested independently below. Product
        # v2 uses real compiled checkers from the immutable fixture commit.
        go_dispatch = (
            "#!/usr/bin/python3 -I\n"
            "from pathlib import Path\n"
            "import sys\n"
            "arguments = sys.argv[1:]\n"
            "root = Path(arguments[arguments.index('--root') + 1])\n"
            "with (root / 'gate-invocations').open('a', encoding='utf-8') as stream:\n"
            "    stream.write(Path(sys.argv[0]).name)\n"
            "    for argument in arguments:\n"
            "        stream.write('\\t' + argument)\n"
            "    stream.write('\\n')\n"
        )
        go_dispatch_path = root / "tools" / "check-go-index-compile-closure"
        go_dispatch_path.write_text(go_dispatch, encoding="utf-8")
        go_dispatch_path.chmod(0o755)

        command_source = (
            "package main\n\n"
            "import (\n"
            '    "bytes"\n'
            '    "fmt"\n'
            '    "os"\n'
            '    "os/exec"\n'
            ")\n\n"
            "func main() {\n"
            "    root := \".\"\n"
            "    gitIndex := false\n"
            "    for index := 1; index < len(os.Args); index++ {\n"
            "        if os.Args[index] == \"--root\" && index+1 < len(os.Args) {\n"
            "            root = os.Args[index+1]\n"
            "            index++\n"
            "        } else if os.Args[index] == \"--git-index\" {\n"
            "            gitIndex = true\n"
            "        }\n"
            "    }\n"
            "    indexFile := os.Getenv(\"GIT_INDEX_FILE\")\n"
            "    if !gitIndex || indexFile == \"\" {\n"
            "        fmt.Fprintln(os.Stderr, \"fixture gate requires staged index\")\n"
            "        os.Exit(2)\n"
            "    }\n"
            "    command := exec.Command(\"/usr/bin/git\", \"-C\", root, "
            "\"-c\", \"core.hooksPath=/dev/null\", \"show\", "
            "\":data/editorial/v2_pages/area-01.jsonl\")\n"
            "    command.Env = []string{\"PATH=/usr/bin:/bin\", "
            "\"HOME=/\", \"GIT_INDEX_FILE=\" + indexFile}\n"
            "    payload, err := command.Output()\n"
            "    if err != nil || !bytes.Contains(payload, []byte(\"\\\"gate_valid\\\":true\")) {\n"
            "        fmt.Fprintln(os.Stderr, \"fixture product gate rejected staged page\")\n"
            "        os.Exit(1)\n"
            "    }\n"
            "}\n"
        )
        for name in (
            "check-v2-supersession-integrity",
            "check-v2-writing-semantic-contract",
        ):
            command = root / "cmd" / name
            command.mkdir(parents=True)
            (command / "main.go").write_text(command_source, encoding="utf-8")
        (root / "internal" / "fixture").mkdir(parents=True)
        (root / "internal" / "fixture" / "fixture.go").write_text(
            "package fixture\n", encoding="utf-8")
        (root / "go.mod").write_text(
            "module fixture.test/v2gates\n\ngo 1.26\n", encoding="utf-8")
        (root / "go.sum").write_bytes(b"")
        archive = (
            root / ".toolchains" / "downloads" /
            "go1.26.5.linux-amd64.tar.gz"
        )
        archive.parent.mkdir(parents=True)
        subprocess.run(
            [
                "/usr/bin/cp", "--reflink=auto", "--",
                str(
                    REPO_ROOT / ".toolchains" / "downloads" /
                    "go1.26.5.linux-amd64.tar.gz"
                ),
                str(archive),
            ],
            check=True,
        )
        archive.chmod(0o644)

        portfolio = root / "data" / "editorial" / "portfolio_v2"
        portfolio.mkdir(parents=True)
        (portfolio / "area.jsonl").write_text(
            '{"intent_id":"fixture"}\n', encoding="utf-8")

        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Fixture")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        (root / "README.md").write_text("fixture\n", encoding="utf-8")
        self.git(
            root, "add", "--", ".githooks", "tools", "cmd", "internal",
            "go.mod", "go.sum", "README.md", "data/editorial/portfolio_v2")
        self.git(root, "commit", "-q", "-m", "fixture baseline")
        self.git(root, "config", "core.hooksPath", ".githooks")
        return root

    def v2_record(self, intent: str = "fixture", *, gate_valid: bool = True) -> str:
        return json.dumps({
            "intent_id": intent,
            "gate_valid": gate_valid,
            "public": False,
            "publication_allowed": False,
            "publication_candidate": False,
            "render_allowed": False,
            "sitemap_allowed": False,
            "indexable": False,
            "approval": False,
            "index_policy": "noindex",
            "public_path": "",
        }, separators=(",", ":")) + "\n"

    def git(
        self, root: Path, *arguments: str, environment: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        # Fixa o fator de carga do hook. Sem isto, as asserções sobre
        # `--budget-seconds 90` medem a carga da MÁQUINA em vez da invocação do
        # gate: o hook multiplica o orçamento por 1..4 conforme /proc/loadavg, e
        # numa máquina com onda de agentes o valor observado vira 180, 270 ou
        # 360. Medido em 2026-09-04: três testes vermelhos com load acima de 8
        # em 8 núcleos, e verdes com a máquina ociosa — o pior tipo de falha,
        # porque acusa código correto e some quando alguém vai investigar.
        env["WIKI_COMMIT_GATE_LOAD_FACTOR"] = "1"
        if environment:
            env.update(environment)
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(root), *arguments],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=90,
            check=False,
        )
        if check:
            self.assertEqual(
                completed.returncode, 0, completed.stdout + completed.stderr)
        return completed

    def invocations(self, root: Path) -> list[str]:
        path = root / "gate-invocations"
        if not path.exists():
            return []
        return path.read_text(encoding="utf-8").splitlines()

    def test_docs_and_unrelated_data_commit_without_heavy_product_gates(self) -> None:
        root = self.make_fixture()
        (root / "docs").mkdir()
        (root / "data" / "research").mkdir(parents=True)
        (root / "docs" / "note.md").write_text("nota\n", encoding="utf-8")
        (root / "data" / "research" / "signal.json").write_text(
            "{}\n", encoding="utf-8")
        self.git(root, "add", "--", "docs/note.md", "data/research/signal.json")

        committed = self.git(
            root, "commit", "-q", "-m", "docs and data", "--",
            "docs/note.md", "data/research/signal.json", check=False)
        self.assertEqual(committed.returncode, 0, committed.stderr)
        # The authenticated dispatcher performs the cheap package-topology
        # probe for every candidate delta; it returns before Go/toolchain work
        # for these paths. Product/release gates remain absent.
        self.assertEqual(len(self.invocations(root)), 1)
        self.assertIn("--budget-seconds\t90", self.invocations(root)[0])

    def test_partial_v2_commit_uses_staged_snapshot_and_leaves_unrelated_go(self) -> None:
        root = self.make_fixture()
        (root / "data" / "editorial" / "v2_pages").mkdir(parents=True)
        (root / "lib").mkdir()
        page = root / "data" / "editorial" / "v2_pages" / "area-01.jsonl"
        page.write_text(self.v2_record(), encoding="utf-8")
        broken = root / "lib" / "broken.go"
        broken.write_text("package lib\nfunc broken(\n", encoding="utf-8")
        self.git(root, "add", "--", str(page.relative_to(root)), "lib/broken.go")

        committed = self.git(
            root, "commit", "-q", "-m", "partial v2", "--",
            str(page.relative_to(root)), check=False)
        self.assertEqual(committed.returncode, 0, committed.stderr)
        commit_output = committed.stdout + committed.stderr
        self.assertEqual(
            commit_output.count("v2-index-product-gates: PASS"), 1,
            commit_output,
        )
        self.assertEqual(len(self.invocations(root)), 1)
        staged = self.git(root, "diff", "--cached", "--name-only").stdout.splitlines()
        self.assertEqual(staged, ["lib/broken.go"])

    def test_dirty_wrapper_and_binary_cache_cannot_approve_invalid_v2(self) -> None:
        root = self.make_fixture()
        temporary_gates_before = set(
            Path("/tmp").glob("wiki-v2-index-gates.*"))
        launcher = root / "tools" / V2_LAUNCHER.name
        launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        launcher.chmod(0o755)
        for name in (
            "check-v2-supersession-integrity",
            "check-v2-writing-semantic-contract",
        ):
            cached = root / ".cache" / "go-cmd-bin" / name / name
            cached.parent.mkdir(parents=True)
            cached.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            cached.chmod(0o755)
        mutable_go = root / ".toolchains" / "go1.26.5" / "bin" / "go"
        mutable_go.parent.mkdir(parents=True)
        mutable_go.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        mutable_go.chmod(0o755)

        page = root / "data" / "editorial" / "v2_pages" / "area-01.jsonl"
        page.parent.mkdir(parents=True)
        page.write_text(self.v2_record("orphan"), encoding="utf-8")
        self.git(root, "add", "--", str(page.relative_to(root)))
        before = self.git(root, "rev-parse", "HEAD").stdout.strip()
        committed = self.git(
            root, "commit", "-q", "-m", "must reject tampered runtime", "--",
            str(page.relative_to(root)), check=False)
        self.assertNotEqual(committed.returncode, 0)
        # A mensagem do emissor é ASCII (tools/check-v2-finalized-commit,
        # membership_hint): diagnóstico de stderr segue a regra de código, não a
        # de conteúdo visível. A asserção pedia "ambíguo" acentuado e por isso
        # NUNCA casou com a mensagem atual — o teste vinha vermelho por
        # ortografia própria, e não por defeito do hook.
        self.assertIn("intent fora/ambiguo no portfolio candidato", committed.stderr)
        # E a recusa tem de continuar ACIONÁVEL. membership_hint existe porque a
        # mensagem antiga ("intent fora/ambiguo no portfolio candidato: x:y")
        # não dizia qual dos dois casos era nem o que fazer, e um agente com o
        # índice íntegro repetiu o mesmo commit quatro vezes antes de ler o
        # código. Sem esta metade, alguém poderia encurtar a mensagem de volta e
        # o teste ficaria verde.
        self.assertIn("COMO CORRIGIR", committed.stderr)
        self.assertIn("check-v2-portfolio-pairing", committed.stderr)
        self.assertIn("ref updates aborted", committed.stderr)
        self.assertEqual(self.git(root, "rev-parse", "HEAD").stdout.strip(), before)
        self.assertEqual(
            set(Path("/tmp").glob("wiki-v2-index-gates.*")),
            temporary_gates_before,
            "a rejected product gate leaked its private toolchain/module cache",
        )

    def test_symlinked_official_archive_is_not_build_authority(self) -> None:
        root = self.make_fixture()
        archive = (
            root / ".toolchains" / "downloads" /
            "go1.26.5.linux-amd64.tar.gz"
        )
        archive.unlink()
        archive.symlink_to(
            REPO_ROOT / ".toolchains" / "downloads" /
            "go1.26.5.linux-amd64.tar.gz"
        )
        page = root / "data" / "editorial" / "v2_pages" / "area-01.jsonl"
        page.parent.mkdir(parents=True)
        page.write_text(self.v2_record(), encoding="utf-8")
        self.git(root, "add", "--", str(page.relative_to(root)))
        committed = self.git(
            root, "commit", "-q", "-m", "reject archive symlink", "--",
            str(page.relative_to(root)), check=False)
        self.assertNotEqual(committed.returncode, 0)
        self.assertIn("toolchain oficial inseguro", committed.stderr)

    def test_parent_go_mod_local_replace_cannot_read_mutable_worktree(self) -> None:
        root = self.make_fixture()
        mutable = root / "mutable-module"
        mutable.mkdir()
        (mutable / "go.mod").write_text(
            "module mutable.fixture/gate\n\ngo 1.26\n", encoding="utf-8")
        go_mod = root / "go.mod"
        go_mod.write_text(
            go_mod.read_text(encoding="utf-8") +
            "\nrequire mutable.fixture/gate v0.0.0\n" +
            f"replace mutable.fixture/gate => {mutable}\n",
            encoding="utf-8",
        )
        self.git(root, "add", "--", "go.mod")
        # This is deliberately the preceding gate-code/toolchain transaction:
        # the later v2 commit must still refuse filesystem inputs outside it.
        prerequisite = self.git(
            root, "commit", "--no-verify", "-q", "-m", "unsafe local replace",
            "--", "go.mod", check=False)
        self.assertEqual(prerequisite.returncode, 0, prerequisite.stderr)

        page = root / "data" / "editorial" / "v2_pages" / "area-01.jsonl"
        page.parent.mkdir(parents=True)
        page.write_text(self.v2_record(), encoding="utf-8")
        self.git(root, "add", "--", str(page.relative_to(root)))
        committed = self.git(
            root, "commit", "--no-verify", "-q", "-m", "reject local replace",
            "--", str(page.relative_to(root)), check=False)
        self.assertNotEqual(committed.returncode, 0)
        self.assertIn("replace local foge da closure imutável", committed.stderr)

    def test_go_parallelism_defaults_to_auto_and_accepts_explicit_override(self) -> None:
        root = self.make_fixture()
        (root / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
        self.git(root, "add", "--", "main.go")
        first = self.git(
            root, "commit", "-q", "-m", "go auto", "--", "main.go", check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue(any(
            line.endswith(
                f"--root\t{root}\t--runtime-root\t{root}"
                "\t--budget-seconds\t90") and
            "--parallelism" not in line
            for line in self.invocations(root)
            if line.startswith("check-go-index-compile-closure\t")
        ), self.invocations(root))

        (root / "main.go").write_text(
            "package main\nfunc main() { println(\"explicit\") }\n", encoding="utf-8")
        self.git(root, "add", "--", "main.go")
        second = self.git(
            root, "commit", "-q", "-m", "go explicit", "--", "main.go",
            environment={"WIKI_GO_COMPILE_PARALLELISM": "3"}, check=False)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(any(
            line.endswith(
                f"--root\t{root}\t--runtime-root\t{root}"
                "\t--budget-seconds\t90\t--parallelism\t3")
            for line in self.invocations(root)
            if line.startswith("check-go-index-compile-closure\t")
        ), self.invocations(root))

    def test_partial_go_commit_uses_candidate_index_checker_not_dirty_worktree(self) -> None:
        root = self.make_fixture()
        checker = root / "tools" / "check-go-index-compile-closure"
        checker.write_text(
            "#!/usr/bin/python3 -I\nraise SystemExit(97)\n",
            encoding="utf-8",
        )
        checker.chmod(0o755)
        (root / "main.go").write_text(
            "package main\nfunc main() {}\n", encoding="utf-8")
        self.git(root, "add", "--", "main.go")

        committed = self.git(
            root, "commit", "-q", "-m", "partial go", "--", "main.go",
            check=False,
        )
        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.assertEqual(len(self.invocations(root)), 1)
        self.assertIn("--runtime-root", self.invocations(root)[0])
        self.assertEqual(
            self.git(root, "status", "--short", "--", str(checker.relative_to(root))).stdout,
            " M tools/check-go-index-compile-closure\n",
        )

    def test_invalid_go_parallelism_fails_fast_before_compile_checker(self) -> None:
        root = self.make_fixture()
        (root / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
        self.git(root, "add", "--", "main.go")
        before = self.git(root, "rev-parse", "HEAD").stdout.strip()
        committed = self.git(
            root, "commit", "-q", "-m", "invalid parallelism", "--", "main.go",
            environment={"WIKI_GO_COMPILE_PARALLELISM": "0"}, check=False)
        # Git normaliza falha de hook para status 1, preservando o rc=2 no
        # diagnóstico emitido pelo próprio pre-commit.
        self.assertEqual(committed.returncode, 1, committed.stdout + committed.stderr)
        self.assertIn("comando reprovou rc=2", committed.stderr)
        self.assertIn("inteiro positivo", committed.stderr)
        self.assertEqual(self.invocations(root), [])
        self.assertEqual(self.git(root, "rev-parse", "HEAD").stdout.strip(), before)

    def test_hook_has_no_private_plumbing_only_commit_capability(self) -> None:
        source = PRE_COMMIT.read_text(encoding="utf-8")
        self.assertNotIn("private_v2_gate_capability", source)
        self.assertNotIn("commit ordinário recusado", source)
        self.assertNotIn("-p=2", source)
        self.assertNotIn("GOMAXPROCS=2", source)
        self.assertNotIn("run-go-cmd-cached", source)
        self.assertNotIn("run-v2-index-product-gates", source)
        self.assertNotIn("900", source)
        self.assertIn(
            "COMMIT_GATE_WALL_SECONDS=$((COMMIT_GATE_BUDGET_SECONDS + 5))",
            source,
        )
        self.assertEqual(
            source.count('"${COMMIT_GATE_WALL_SECONDS}s"'), 2,
            "timeout externo deve dar cleanup grace nas duas rotas de paralelismo",
        )
        self.assertEqual(
            source.count(
                '--budget-seconds "$COMMIT_GATE_BUDGET_SECONDS"'),
            2,
            "cleanup grace nao pode ampliar o orçamento lógico do checker",
        )


if __name__ == "__main__":
    unittest.main()
