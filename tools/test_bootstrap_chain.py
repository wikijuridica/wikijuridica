#!/usr/bin/env python3
"""Focused anti-loop contracts for tools/bootstrap-chain."""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import os
import re
import shlex
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "tools" / "bootstrap-chain"


class BootstrapChainAntiLoopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = BOOTSTRAP.read_text(encoding="utf-8")

    def test_shell_syntax_and_list_mode_are_bounded(self) -> None:
        subprocess.run(
            ["bash", "-n", str(BOOTSTRAP)],
            check=True,
            timeout=2,
            capture_output=True,
            text=True,
        )
        listed = subprocess.run(
            [str(BOOTSTRAP), "--list"],
            check=True,
            timeout=2,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "WIKI_V2_STOCK_READ_LEASE": "forged-marker-without-fds",
            },
        )
        self.assertIn("generate-authorial-mass-refinement-quality-report", listed.stdout)
        ordered = [line.split(maxsplit=1)[1] for line in listed.stdout.splitlines()]
        self.assertLess(
            ordered.index("generate-authorial-mass-signature-candidate-pairs"),
            ordered.index("generate-authorial-mass-refinement-quality-report"),
        )
        self.assertLess(
            ordered.index("generate-authorial-mass-signature-candidate-pairs"),
            ordered.index("generate-authorial-mass-global-similarity-audit"),
        )
        self.assertLess(
            ordered.index("generate-authorial-mass-editorial-quality-vectors"),
            ordered.index("generate-refined-public-prose"),
        )
        self.assertLess(
            ordered.index("generate-authorial-mass-publication-readiness"),
            ordered.index("generate-authorial-mass-legal-reviews"),
        )
        self.assertLess(
            ordered.index("generate-authorial-mass-legal-reviews"),
            ordered.index("generate-public-prose-candidate"),
        )

    def test_exit_75_is_not_retried_without_machine_readable_cause(self) -> None:
        self.assertNotIn("attempt=", self.source)
        self.assertNotIn("sleep 5", self.source)
        self.assertNotIn("tentativa $attempt", self.source)
        self.assertEqual(self.source.count('"$bootstrap_process_tree_supervisor" \\'), 1)
        self.assertIn('bootstrap_total_timeout_seconds="${P0_BOOTSTRAP_TOTAL_TIMEOUT_SECONDS:-600}"', self.source)
        self.assertIn('bootstrap_stock_lease_marker_expected=', self.source)
        self.assertEqual(
            self.source.count('"$bootstrap_stock_lease_helper" --verify-inherited'),
            1,
        )
        self.assertGreaterEqual(
            self.source.count("bootstrap_verify_inherited_stock_lease"), 4
        )
        self.assertNotIn(
            '-- "$bootstrap_stock_lease_helper" --require-inherited --', self.source
        )
        self.assertIn("bootstrap_forward_signal QUIT 131", self.source)
        self.assertNotIn("--pass-fd 3", self.source)
        self.assertNotIn("--pass-fd 4", self.source)
        self.assertNotIn("--pass-fd 5", self.source)
        self.assertIn("--pass-fd 7", self.source)
        self.assertIn("--pass-fd 8", self.source)
        self.assertIn("--fail-on-descendant-cleanup", self.source)
        self.assertNotIn("if command -v setsid", self.source)
        self.assertNotIn('nice -n 10 "tools/$step"', self.source)
        self.assertIn("exit=75 não classificado; sem retry cego", self.source)
        self.assertIn("tools/bootstrap-chain --from $n", self.source)
        self.assertEqual(
            self.source.count("bootstrap_compute_source_contract_sha256"), 2,
            "full source hashing must happen once, not after every step",
        )
        self.assertIn("bootstrap-chain-source-manifest/v2", self.source)

        lock_source = (ROOT / "tools" / "p0-factory-chain-lock.sh").read_text()
        self.assertNotIn("command-ledger.jsonl", lock_source)
        self.assertNotIn("p0_factory_chain_lock_materialize_artifact", lock_source)
        self.assertNotIn("p0_factory_chain_lock_validate_wait_classification", lock_source)
        self.assertNotIn("while ! flock", lock_source)
        receipt_source = (ROOT / "tools" / "bootstrap-step-receipts").read_text()
        self.assertIn("MAX_STALE_RENAME_ATTEMPTS = 16", receipt_source)
        self.assertNotIn("while True:", receipt_source)

    def test_receipt_resume_uses_authenticated_identity_without_payload_rehash(self) -> None:
        helper = ROOT / "tools" / "bootstrap-step-receipts"
        loader = importlib.machinery.SourceFileLoader(
            "bootstrap_step_receipts_test_module", str(helper)
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            artifact = root / "data/editorial/result.jsonl"
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"value":1}\n', encoding="utf-8")
            recorded = module.hash_regular(
                root, "data/editorial/result.jsonl", module.MAX_ARTIFACT_BYTES
            )

            original_hash = module.hash_regular
            module.hash_regular = lambda *_args, **_kwargs: self.fail(
                "resume identity check reread the artifact payload"
            )
            try:
                self.assertTrue(
                    module.artifact_identity_matches(
                        root, recorded, module.MAX_ARTIFACT_BYTES
                    )
                )
                before = artifact.stat()
                time.sleep(0.01)
                artifact.write_text('{"value":2}\n', encoding="utf-8")
                os.utime(
                    artifact,
                    ns=(before.st_atime_ns, before.st_mtime_ns),
                )
                self.assertFalse(
                    module.artifact_identity_matches(
                        root, recorded, module.MAX_ARTIFACT_BYTES
                    ),
                    "ctime/inode identity must reject a same-size in-place rewrite",
                )
            finally:
                module.hash_regular = original_hash

    def test_receipt_artifact_paths_are_canonical_and_confined(self) -> None:
        helper = ROOT / "tools" / "bootstrap-step-receipts"
        loader = importlib.machinery.SourceFileLoader(
            "bootstrap_step_receipts_path_test_module", str(helper)
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        self.assertEqual(
            module.parse_artifacts("data/editorial/ok.jsonl"),
            ("data/editorial/ok.jsonl",),
        )
        for unsafe in (
            "data/editorial/../public/escape.jsonl",
            "data/editorial//ambiguous.jsonl",
            "data/editorial/./ambiguous.jsonl",
            "data/editorial/line\nbreak.jsonl",
        ):
            with self.assertRaises(module.ReceiptError, msg=unsafe):
                module.parse_artifacts(unsafe)

    def build_fixture(self, directory: str) -> tuple[Path, list[str]]:
        root = Path(directory)
        tools = root / "tools"
        tools.mkdir(parents=True)
        bootstrap = tools / "bootstrap-chain"
        bootstrap.write_bytes(BOOTSTRAP.read_bytes())
        bootstrap.chmod(0o755)
        receipt_helper = tools / "bootstrap-step-receipts"
        receipt_helper.write_bytes(
            (ROOT / "tools" / "bootstrap-step-receipts").read_bytes()
        )
        receipt_helper.chmod(0o755)
        lock_helper = tools / "p0-factory-chain-lock.sh"
        lock_helper.write_bytes((ROOT / "tools" / "p0-factory-chain-lock.sh").read_bytes())
        lock_helper.chmod(0o755)
        supervisor = tools / "supervise-process-tree"
        supervisor.write_bytes((ROOT / "tools" / "supervise-process-tree").read_bytes())
        supervisor.chmod(0o755)
        for required in (
            "run-go-cmd-cached",
            "run-heavy-throttled",
            "run-generate-supervised",
            "go-modern",
            # Preflight de oráculos externos do bloco 12-31: no fixture não há
            # LanguageTool nem venv PT-BR, e o que está sob teste aqui é o
            # contrato de recibos/retomada, não a liveness dos oráculos.
            "check-oracle-liveness",
        ):
            path = tools / required
            path.write_text("#!/bin/sh\nexit 0\n")
            path.chmod(0o755)
        (tools / "simplemma_ptbr_lemma_audit.py").write_text(
            "raise SystemExit(0)\n", encoding="utf-8"
        )
        (tools / "requirements-simplemma-ptbr.txt").write_text(
            "simplemma==1.2.0\n", encoding="utf-8"
        )
        (tools / "requirements-wordfreq.txt").write_text(
            "wordfreq==3.1.1\n", encoding="utf-8"
        )
        (root / "cmd").mkdir()
        (root / "internal").mkdir()
        (root / "go.mod").write_text("module bootstrapfixture\n\ngo 1.25\n")
        (root / "go.sum").write_text("")
        lock_path, meta_path = self.expected_lock_paths(root, "bootstrap-chain")
        self.addCleanup(self.cleanup_lock_domain, lock_path, meta_path)
        self.addCleanup(
            self.cleanup_coordination_path, self.expected_coordination_path(root)
        )
        listed = subprocess.run(
            [str(bootstrap), "--list"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        steps = [line.split(maxsplit=1)[1] for line in listed.stdout.splitlines()]
        artifact_block = re.search(
            r"(?ms)^STEP_ARTIFACTS=\(\n(?P<body>.*?)^\)$", self.source
        )
        self.assertIsNotNone(artifact_block)
        artifact_specs: list[str] = []
        for line in artifact_block.group("body").splitlines():
            artifact_specs.extend(shlex.split(line, comments=True))
        self.assertEqual(len(artifact_specs), len(steps))
        for spec in artifact_specs:
            for relative in spec.split("|"):
                artifact = root / relative
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(f"fixture artifact for {relative}\n")
        for step in steps:
            wrapper = tools / step
            wrapper.write_text(
                "#!/bin/sh\n"
                "old_ifs=$IFS\n"
                "IFS='|'\n"
                "for artifact in $WIKI_BOOTSTRAP_STEP_ARTIFACTS; do\n"
                "  mkdir -p \"$(dirname -- \"$artifact\")\"\n"
                "  printf 'fixture artifact for %s by step %s\\n' \"$artifact\" "
                '"$WIKI_BOOTSTRAP_STEP_NUMBER" >"$artifact"\n'
                "done\n"
                "IFS=$old_ifs\n"
            )
            wrapper.chmod(0o755)
        preflight = tools / "check-v2-stock-epoch"
        preflight.write_text(
            "#!/bin/sh\n"
            "echo 'v2-stock-epoch: pass calculated=true approval=false "
            "publication=false stock_epoch_sha256=sha256:"
            + "a" * 64
            + " transaction_id=fixture'\n"
        )
        preflight.chmod(0o755)
        stock_lease = tools / "run-with-v2-stock-read-lease"
        stock_lease.write_text(
            "#!/usr/bin/env python3\n"
            "import os\n"
            "import pathlib\n"
            "import sys\n"
            "MARKER = 'canonical-stock-read-lease/v1;fds=3,4,5'\n"
            "def verify():\n"
            "    if os.environ.get('WIKI_V2_STOCK_READ_LEASE') != MARKER:\n"
            "        raise SystemExit(75)\n"
            "    for descriptor in (3, 4, 5):\n"
            "        try:\n"
            "            os.fstat(descriptor)\n"
            "        except OSError:\n"
            "            raise SystemExit(75)\n"
            "arguments = sys.argv[1:]\n"
            "if '--verify-inherited' in arguments:\n"
            "    verify()\n"
            "    raise SystemExit(0)\n"
            "if '--require-inherited' in arguments:\n"
            "    verify()\n"
            "    separator = arguments.index('--')\n"
            "    command = arguments[separator + 1:]\n"
            "    if not command:\n"
            "        raise SystemExit(2)\n"
            "    os.execvpe(command[0], command, os.environ.copy())\n"
            "separator = arguments.index('--')\n"
            "command = arguments[separator + 1:]\n"
            "lease_dir = pathlib.Path(os.environ.get('TMPDIR', '/tmp'))\n"
            "sources = []\n"
            "for index in range(3):\n"
            "    descriptor = os.open(lease_dir / f'fixture-stock-lease-{index}', "
            "os.O_RDWR | os.O_CREAT, 0o600)\n"
            "    sources.append(descriptor)\n"
            "for target, source in zip((3, 4, 5), sources):\n"
            "    if source != target:\n"
            "        os.dup2(source, target, inheritable=True)\n"
            "    os.set_inheritable(target, True)\n"
            "environment = os.environ.copy()\n"
            "environment['WIKI_V2_STOCK_READ_LEASE'] = MARKER\n"
            "os.execvpe(command[0], command, environment)\n"
        )
        stock_lease.chmod(0o755)
        return bootstrap, steps

    def seed_resume_state(
        self, bootstrap: Path, root: Path, through: int, environment: dict[str, str]
    ) -> None:
        seeded = subprocess.run(
            [str(bootstrap), "--from", "1", "--until", str(through)],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)

    def test_until_zero_cannot_authorize_resume_without_step_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            environment = {
                **os.environ,
                "TMPDIR": str(temporary_root),
                "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
            }
            detox = subprocess.run(
                [str(bootstrap), "--until", "0"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(detox.returncode, 0, detox.stdout + detox.stderr)
            future_output = root / "data/editorial/refined_public_prose.jsonl"
            self.assertFalse(
                future_output.exists(),
                "reset must not leave a future-generation refined input live",
            )
            self.assertTrue(
                list(future_output.parent.glob(
                    "refined_public_prose.jsonl.stale-resume-01-*"
                )),
                "reset must preserve the displaced output recoverably",
            )
            resumed = subprocess.run(
                [
                    str(bootstrap), "--from", str(len(steps)),
                    "--until", str(len(steps)),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(resumed.returncode, 75, resumed.stderr)
            self.assertIn("não possui cadeia de recibos", resumed.stderr)

    def test_stock_preflight_fails_before_recoverable_detox(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _steps = self.build_fixture(directory)
            root = Path(directory)
            preflight = root / "tools/check-v2-stock-epoch"
            preflight.write_text(
                "#!/bin/sh\necho stale-stock >&2\nexit 1\n",
                encoding="utf-8",
            )
            preflight.chmod(0o755)
            protected = root / "data/editorial/refined_public_prose.jsonl"
            before = protected.read_bytes()
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            completed = subprocess.run(
                [str(bootstrap), "--until", "0"],
                cwd=root,
                env={
                    **os.environ,
                    "TMPDIR": str(temporary_root),
                    "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "0",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                },
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("estoque v2 ausente ou stale", completed.stderr)
            self.assertEqual(protected.read_bytes(), before)
            self.assertFalse(list(protected.parent.glob(protected.name + ".stale-*")))

    def _repositorio_git(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True, timeout=20)

    def _roda_ate_zero(self, root: Path, bootstrap: Path):
        temporary_root = root / "tmp"
        temporary_root.mkdir(exist_ok=True)
        return subprocess.run(
            [str(bootstrap), "--until", "0"],
            cwd=root,
            env={
                **os.environ,
                "TMPDIR": str(temporary_root),
                "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "0",
                "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
            },
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def _arvore_de_pacote(self, root: Path, ignorada: bool) -> None:
        base = root / "tools" / "publicador-x"
        binario = base / "node_modules" / ".bin"
        binario.mkdir(parents=True)
        alvo = base / "node_modules" / "pacote" / "cli.js"
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text("// cli\n", encoding="utf-8")
        (binario / "cli").symlink_to("../pacote/cli.js")
        if ignorada:
            (base / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    def test_arvore_de_pacote_ignorada_nao_trava_o_contrato_de_codigo(self) -> None:
        # Em 2026-08-27 14:52 um `npm install` criou
        # tools/publicador-social/node_modules com UM link simbolico em .bin/, e a
        # varredura do contrato de codigo abortava em QUALQUER link simbolico.
        # Efeito medido: nenhum passo da cadeia conseguiu autenticar o contrato
        # entre aquela data e 2026-09-10, e a mensagem nomeava o achado
        # ("crosses symlink"), nunca a causa.
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _steps = self.build_fixture(directory)
            root = Path(directory)
            self._repositorio_git(root)
            self._arvore_de_pacote(root, ignorada=True)
            completed = self._roda_ate_zero(root, bootstrap)
            self.assertNotIn("crosses symlink", completed.stderr)
            self.assertNotIn("arvore de pacote RASTREADA", completed.stderr)

    def test_link_simbolico_fora_de_arvore_de_pacote_continua_abortando(self) -> None:
        # Controle negativo: a poda nao pode virar licenca para link simbolico em
        # qualquer lugar. Link dentro da fonte pode apontar para fora do
        # repositorio e trocar um produtor sem mudar o hash.
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _steps = self.build_fixture(directory)
            root = Path(directory)
            self._repositorio_git(root)
            (root / "tools" / "atalho-para-o-bootstrap").symlink_to("bootstrap-chain")
            completed = self._roda_ate_zero(root, bootstrap)
            self.assertIn("crosses symlink", completed.stderr)

    def test_arvore_de_pacote_rastreada_aborta_com_mensagem_propria(self) -> None:
        # A poda vem COM PROVA: node_modules rastreado e fonte de verdade, e
        # podar sem conferir deixaria um produtor fora do fingerprint.
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _steps = self.build_fixture(directory)
            root = Path(directory)
            self._repositorio_git(root)
            self._arvore_de_pacote(root, ignorada=False)
            completed = self._roda_ate_zero(root, bootstrap)
            self.assertIn("arvore de pacote RASTREADA", completed.stderr)

    def test_global_deadline_is_bounded_to_ten_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _steps = self.build_fixture(directory)
            root = Path(directory)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            for invalid in ("0", "601"):
                completed = subprocess.run(
                    [str(bootstrap), "--until", "0"],
                    cwd=root,
                    env={
                        **os.environ,
                        "TMPDIR": str(temporary_root),
                        "P0_BOOTSTRAP_TOTAL_TIMEOUT_SECONDS": invalid,
                        "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "0",
                        "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                    },
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn("entre 1 e 600", completed.stderr)

    def test_source_mutation_during_step_fails_before_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            first = root / "tools" / steps[0]
            first.write_text(
                first.read_text(encoding="utf-8") +
                "printf '\\n// concurrent source mutation\\n' >>go.mod\n",
                encoding="utf-8",
            )
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            completed = subprocess.run(
                [str(bootstrap), "--from", "1", "--until", "1"],
                cwd=root,
                env={
                    **os.environ,
                    "TMPDIR": str(temporary_root),
                    "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                },
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(completed.returncode, 75, completed.stderr)
            self.assertIn("código da fábrica mudou", completed.stderr)
            progress = root / ".agents/runtime/bootstrap-chain/progress.json"
            if progress.exists():
                self.assertNotIn(
                    '"completed_step":1', progress.read_text(encoding="utf-8")
                )

    def test_transitive_tool_mutation_during_step_fails_before_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            first = root / "tools" / steps[0]
            first.write_text(
                first.read_text(encoding="utf-8")
                + "printf '\\nmutated==1\\n' >>tools/requirements-wordfreq.txt\n",
                encoding="utf-8",
            )
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            completed = subprocess.run(
                [str(bootstrap), "--from", "1", "--until", "1"],
                cwd=root,
                env={
                    **os.environ,
                    "TMPDIR": str(temporary_root),
                    "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                },
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(completed.returncode, 75, completed.stderr)
            self.assertIn("código da fábrica mudou", completed.stderr)

    def test_resume_rejects_tampered_prefix_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            environment = {
                **os.environ,
                "TMPDIR": str(temporary_root),
                "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
            }
            self.seed_resume_state(bootstrap, root, len(steps) - 1, environment)
            prefix_output = (
                root / "data" / "editorial" /
                "authorial_mass_refinement_quality_report.jsonl"
            )
            prefix_output.write_text("tampered after receipt\n")
            resumed = subprocess.run(
                [
                    str(bootstrap), "--from", str(len(steps)),
                    "--until", str(len(steps)),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(resumed.returncode, 75, resumed.stderr)
            self.assertIn("resume output is stale", resumed.stderr)

    def test_resume_final_source_aggregate_has_no_duplicate_upstream_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _ = self.build_fixture(directory)
            root = Path(directory)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            environment = {
                **os.environ,
                "TMPDIR": str(temporary_root),
                "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
            }
            self.seed_resume_state(bootstrap, root, 37, environment)
            resumed = subprocess.run(
                [str(bootstrap), "--from", "37", "--until", "37"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertNotIn("earliest_safe_from=35", resumed.stderr)
            self.assertIn(
                "[37/42] generate-official-source-url-live-evidence", resumed.stderr
            )

    def test_one_lock_covers_preflight_and_entire_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            marker = root / "step-started"
            target = root / "tools" / steps[-1]
            target.write_text(
                "#!/bin/sh\n"
                "ROOT=\"$(pwd)\"\n"
                ". \"$ROOT/tools/p0-factory-chain-lock.sh\"\n"
                "p0_factory_chain_lock_acquire fixture-step\n"
                "printf 'held=%s fd=%s\\n' \"${P0_FACTORY_CHAIN_LOCK_HELD:-0}\" "
                "\"$(stat -Lc '%d:%i' /proc/$$/fd/8 2>/dev/null || true)\" "
                ">>\"$BOOTSTRAP_TEST_MARKER\"\n"
                "sleep \"${BOOTSTRAP_TEST_SLEEP_SECONDS:-1.2}\"\n"
                "old_ifs=$IFS; IFS='|'\n"
                "for artifact in $WIKI_BOOTSTRAP_STEP_ARTIFACTS; do "
                "mkdir -p \"$(dirname -- \"$artifact\")\"; "
                "printf 'lock fixture step %s\\n' \"$WIKI_BOOTSTRAP_STEP_NUMBER\" "
                ">\"$artifact\"; done\n"
                "IFS=$old_ifs\n"
            )
            target.chmod(0o755)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            environment = os.environ.copy()
            environment.update(
                {
                    "TMPDIR": str(temporary_root),
                    "BOOTSTRAP_TEST_MARKER": str(marker),
                    "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                }
            )
            self.seed_resume_state(bootstrap, root, len(steps) - 1, environment)
            arguments = [
                str(bootstrap),
                "--from",
                str(len(steps)),
                "--until",
                str(len(steps)),
            ]
            first = subprocess.Popen(
                arguments,
                cwd=root,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 2
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(), "first chain never entered its step")
                bypass_environment = environment.copy()
                bypass_environment["P0_FACTORY_CHAIN_LOCK_HELD"] = "1"
                bypass_environment["P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS"] = "0"
                started = time.monotonic()
                second = subprocess.run(
                    arguments,
                    cwd=root,
                    env=bypass_environment,
                    text=True,
                    capture_output=True,
                    timeout=2,
                    check=False,
                )
                self.assertEqual(second.returncode, 75, second.stderr)
                # RELOGIO REMOVIDO EM 2026-09-10: sob a suite diaria a ~290% de
                # CPU este limite caia por CARGA, nao por defeito, e o arquivo
                # inteiro passa em 150,4 s ocioso. A propriedade sob teste e
                # nao esperar passivamente pelo lock,
                # travada pelas assercoes ao lado; o `timeout=2` do subprocess
                # continua sendo o guarda de espera REAL, com folga.
                self.assertIn("passive wait disabled", second.stderr)
                first_stdout, first_stderr = first.communicate(timeout=3)
                self.assertEqual(first.returncode, 0, first_stdout + first_stderr)
                marker_lines = marker.read_text().splitlines()
                self.assertEqual(len(marker_lines), 1)
                self.assertRegex(marker_lines[0], r"^held=1 fd=[0-9]+:[0-9]+$")
            finally:
                if first.poll() is None:
                    first.terminate()
                    first.wait(timeout=2)

    def test_detox_preserves_every_existing_stale_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, _steps = self.build_fixture(directory)
            root = Path(directory)
            (root / "data" / "editorial").mkdir(parents=True, exist_ok=True)
            (root / "data" / "ops").mkdir(parents=True, exist_ok=True)
            manifest = root / "data" / "editorial" / "stock_manifest.json"
            manifest.write_text('{"drafts_expected":2,"expansion_expected":0}\n')
            source = root / "data" / "editorial" / "refined_public_prose.jsonl"
            preexisting = source.with_name(source.name + ".stale-preexisting")
            preexisting.write_text("preserve-me\n")
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            environment = os.environ.copy()
            environment.update(
                {
                    "TMPDIR": str(temporary_root),
                    "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                }
            )
            arguments = [str(bootstrap), "--until", "0"]
            source.write_text("first-version\n")
            first = subprocess.run(
                arguments,
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            source.write_text("second-version\n")
            second = subprocess.run(
                arguments,
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            stale_contents = {
                path.read_text()
                for path in source.parent.glob(source.name + ".stale-*")
            }
            self.assertEqual(
                stale_contents,
                {"preserve-me\n", "first-version\n", "second-version\n"},
            )
            self.assertFalse(source.exists())

    # --- convergência do passo do corpus refinado (pool de reuso) -----------
    #
    # O produtor do refined usa o PRÓPRIO output anterior como pool de reuso
    # idempotente. Enquanto prepare movia esse arquivo para .stale-resume-*, o
    # pool morria a cada retomada e nenhuma rodada cabia no teto de 540s/passo.
    # Agora o output declarado como --reuse-pool-artifact é PRESERVADO por
    # cópia; a testemunha de produção do mesmo passo continua sendo movida, e é
    # ela que impede um produtor que não fez nada de ganhar recibo.

    REFINED_STEP_NAME = "generate-refined-public-prose"
    REFINED_CORPUS = "data/editorial/refined_public_prose.jsonl"
    REFINED_WITNESS = "data/ops/refined_public_prose_generation_witness.json"

    def chain_environment(self, root: Path) -> dict[str, str]:
        temporary_root = root / "tmp"
        temporary_root.mkdir(exist_ok=True)
        environment = os.environ.copy()
        environment.update(
            {
                "TMPDIR": str(temporary_root),
                "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
            }
        )
        return environment

    def write_step_wrapper(self, root: Path, step: str, body: str) -> None:
        wrapper = root / "tools" / step
        wrapper.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        wrapper.chmod(0o755)

    def run_chain_step(
        self, bootstrap: Path, root: Path, step_number: int,
        environment: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(bootstrap), "--from", str(step_number), "--until", str(step_number)],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def refined_step_number(self, steps: list[str]) -> int:
        return steps.index(self.REFINED_STEP_NAME) + 1

    # O wrapper NÃO pode mudar entre invocações: tools/ inteiro entra no
    # contrato de código, e reescrevê-lo invalida o prefixo autenticado. Por
    # isso cada fase é escolhida por um arquivo de dado, fora do contrato.
    def install_phased_step_wrapper(self, root: Path, step: str, body: str) -> None:
        wrapper = root / "tools" / step
        wrapper.write_text(
            '#!/bin/sh\nphase="$(cat fixture-phase 2>/dev/null || echo 1)"\n' + body,
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

    def set_fixture_phase(self, root: Path, phase: str) -> None:
        (root / "fixture-phase").write_text(phase + "\n", encoding="utf-8")

    def test_reuse_pool_output_survives_a_failed_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            environment = self.chain_environment(root)
            number = self.refined_step_number(steps)
            self.install_phased_step_wrapper(
                root, self.REFINED_STEP_NAME,
                'if [ "$phase" = "1" ]; then\n'
                # Tentativa morta pelo teto: deixa progresso parcial e falha.
                f"  printf 'partial-progress\\n' >{self.REFINED_CORPUS}\n"
                "  exit 1\n"
                "fi\n"
                # Retomada: o produtor EXIGE encontrar o progresso anterior.
                f"if [ ! -f {self.REFINED_CORPUS} ]; then\n"
                "  echo 'reuse pool was destroyed before the retry' >&2\n"
                "  exit 1\n"
                "fi\n"
                f"grep -q partial-progress {self.REFINED_CORPUS} || {{\n"
                "  echo 'reuse pool content was lost before the retry' >&2\n"
                "  exit 1\n"
                "}\n"
                f"printf 'complete-corpus\\n' >{self.REFINED_CORPUS}\n"
                f"printf '{{\"run\":\"retry\"}}\\n' >{self.REFINED_WITNESS}\n",
            )
            self.set_fixture_phase(root, "1")
            self.seed_resume_state(bootstrap, root, number - 1, environment)

            failed = self.run_chain_step(bootstrap, root, number, environment)
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            self.assertEqual(
                (root / self.REFINED_CORPUS).read_text(), "partial-progress\n"
            )

            self.set_fixture_phase(root, "2")
            resumed = self.run_chain_step(bootstrap, root, number, environment)
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
            self.assertEqual(
                (root / self.REFINED_CORPUS).read_text(), "complete-corpus\n"
            )
            # A recuperabilidade forense do parcial continua garantida.
            corpus = root / self.REFINED_CORPUS
            preserved = {
                path.read_text()
                for path in corpus.parent.glob(corpus.name + ".stale-resume-*")
            }
            self.assertIn("partial-progress\n", preserved)

    def test_producer_that_does_nothing_cannot_earn_a_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            environment = self.chain_environment(root)
            number = self.refined_step_number(steps)
            self.install_phased_step_wrapper(
                root, self.REFINED_STEP_NAME,
                'if [ "$phase" = "1" ]; then\n'
                # Escreveu tudo e morreu antes do recibo: órfão completo.
                f"  printf 'corpus-from-the-killed-attempt\\n' >{self.REFINED_CORPUS}\n"
                f"  printf '{{\"run\":\"killed\"}}\\n' >{self.REFINED_WITNESS}\n"
                "  exit 1\n"
                "fi\n"
                # CONTROLE anti falso-verde: com o corpus preservado por cópia,
                # um produtor que não faz NADA deixa tudo byte-idêntico.
                "exit 0\n",
            )
            self.set_fixture_phase(root, "1")
            self.seed_resume_state(bootstrap, root, number - 1, environment)

            killed = self.run_chain_step(bootstrap, root, number, environment)
            self.assertNotEqual(killed.returncode, 0, killed.stdout)

            self.set_fixture_phase(root, "2")
            idle = self.run_chain_step(bootstrap, root, number, environment)
            self.assertEqual(idle.returncode, 75, idle.stdout + idle.stderr)
            # O órfão preservado continua no lugar (o pool não é destruído),
            # mas NÃO virou resultado autenticado.
            self.assertEqual(
                (root / self.REFINED_CORPUS).read_text(),
                "corpus-from-the-killed-attempt\n",
            )
            progress = root / ".cache/bootstrap-chain/step-progress.json"
            self.assertIn(
                f'"completed_step":{number - 1}',
                progress.read_text(encoding="utf-8"),
            )

    def test_unchanged_corpus_with_fresh_witness_keeps_advancing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            environment = self.chain_environment(root)
            number = self.refined_step_number(steps)
            # Ponto fixo real: a tentativa anterior já deixou o corpus completo,
            # a retomada reusa TUDO e regrava bytes idênticos. Sem a testemunha
            # por rodada, esse resultado — que é o CORRETO — reprovaria para
            # sempre na recusa de "todo output inalterado".
            self.install_phased_step_wrapper(
                root, self.REFINED_STEP_NAME,
                f"printf 'converged-corpus\\n' >{self.REFINED_CORPUS}\n"
                f"printf '{{\"generated_at\":\"%s\"}}\\n' \"$(date +%%s%%N)\" "
                f">{self.REFINED_WITNESS}\n"
                'if [ "$phase" = "1" ]; then\n'
                "  exit 1\n"
                "fi\n",
            )
            self.set_fixture_phase(root, "1")
            self.seed_resume_state(bootstrap, root, number - 1, environment)

            killed = self.run_chain_step(bootstrap, root, number, environment)
            self.assertNotEqual(killed.returncode, 0, killed.stdout)
            corpus_after_kill = (root / self.REFINED_CORPUS).read_text()

            self.set_fixture_phase(root, "2")
            resumed = self.run_chain_step(bootstrap, root, number, environment)
            self.assertEqual(
                resumed.returncode, 0,
                "a converged corpus with a fresh production witness must "
                "advance the chain:\n" + resumed.stdout + resumed.stderr,
            )
            self.assertEqual(
                (root / self.REFINED_CORPUS).read_text(), corpus_after_kill
            )

    def test_resume_past_reuse_pool_step_reauthenticates_the_prefix(self) -> None:
        # A declaração de pool entra no input_fingerprint do prepared, então a
        # RE-AUTENTICAÇÃO do prefixo (resume) tem que recompor o mesmo
        # fingerprint. Sem isso, o passo seguinte ao passo com pool fica
        # recusado em loop ("prepared receipt mismatch") mesmo com a cadeia
        # verde — o prefixo autenticado vira inalcançável.
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            environment = self.chain_environment(root)
            number = self.refined_step_number(steps)
            self.seed_resume_state(bootstrap, root, number, environment)

            resumed = self.run_chain_step(bootstrap, root, number + 1, environment)
            self.assertEqual(
                resumed.returncode, 0,
                "resume after the reuse-pool step must re-authenticate the "
                "prefix:\n" + resumed.stdout + resumed.stderr,
            )

    def test_step_without_declared_reuse_pool_still_loses_its_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            environment = self.chain_environment(root)
            number = self.refined_step_number(steps)
            neighbour = steps[number - 2]
            neighbour_artifact = "data/editorial/public_prose_candidate.jsonl"
            # CONTROLE de escopo: a preservação vale SÓ para o output declarado
            # como pool. O passo vizinho continua tendo o órfão movido, então
            # seu produtor não pode encontrá-lo vivo ao iniciar.
            self.install_phased_step_wrapper(
                root, neighbour,
                f"if [ -f {neighbour_artifact} ]; then\n"
                "  echo 'orphan of a non-pool step survived prepare' >&2\n"
                "  exit 1\n"
                "fi\n"
                f"printf 'candidate-corpus-%s\\n' \"$phase\" >{neighbour_artifact}\n",
            )
            self.set_fixture_phase(root, "1")
            self.seed_resume_state(bootstrap, root, number - 2, environment)

            # Órfão autêntico no caminho canônico antes da tentativa.
            (root / neighbour_artifact).write_text("orphan-from-a-dead-attempt\n")
            self.set_fixture_phase(root, "2")
            completed = self.run_chain_step(
                bootstrap, root, number - 1, environment
            )
            self.assertEqual(
                completed.returncode, 0, completed.stdout + completed.stderr
            )
            self.assertEqual(
                (root / neighbour_artifact).read_text(), "candidate-corpus-2\n"
            )
            orphan = root / neighbour_artifact
            preserved = {
                path.read_text()
                for path in orphan.parent.glob(orphan.name + ".stale-resume-*")
            }
            self.assertIn("orphan-from-a-dead-attempt\n", preserved)

    def test_term_stops_owned_step_cleans_meta_and_releases_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bootstrap, steps = self.build_fixture(directory)
            root = Path(directory)
            step_pid_path = root / "step.pid"
            meta_path_marker = root / "lock-meta.path"
            target = root / "tools" / steps[-1]
            target.write_text(
                "#!/bin/sh\n"
                "ROOT=\"$(pwd)\"\n"
                ". \"$ROOT/tools/p0-factory-chain-lock.sh\"\n"
                "p0_factory_chain_lock_acquire fixture-term-step\n"
                "printf '%s\\n' \"$P0_FACTORY_CHAIN_LOCK_META_PATH\" >\"$BOOTSTRAP_TEST_META_PATH_FILE\"\n"
                "printf '%s\\n' \"$$\" >\"$BOOTSTRAP_TEST_STEP_PID\"\n"
                "sleep \"${BOOTSTRAP_TEST_SLEEP_SECONDS:-10}\"\n"
                "old_ifs=$IFS; IFS='|'\n"
                "for artifact in $WIKI_BOOTSTRAP_STEP_ARTIFACTS; do "
                "mkdir -p \"$(dirname -- \"$artifact\")\"; "
                "printf 'term fixture step %s\\n' \"$WIKI_BOOTSTRAP_STEP_NUMBER\" "
                ">\"$artifact\"; done\n"
                "IFS=$old_ifs\n"
            )
            target.chmod(0o755)
            temporary_root = root / "tmp"
            temporary_root.mkdir()
            environment = os.environ.copy()
            environment.update(
                {
                    "TMPDIR": str(temporary_root),
                    "BOOTSTRAP_TEST_META_PATH_FILE": str(meta_path_marker),
                    "BOOTSTRAP_TEST_STEP_PID": str(step_pid_path),
                    # 2 s, nao 10: o teste espera o `step.pid` aparecer e manda
                    # TERM na hora seguinte, entao o sleep so precisa cobrir a
                    # janela entre o passo comecar e o sinal chegar. Os 10 s
                    # eram 5x essa janela e o caso mais caro do arquivo
                    # (31,1 s medidos em 2026-09-10) pagava a diferenca a toa.
                    # Encurtar o que o caso nao usa e consertar o teste;
                    # aumentar o teto do runner nao seria.
                    "BOOTSTRAP_TEST_SLEEP_SECONDS": "2",
                    "P0_BOOTSTRAP_SIGNAL_GRACE_SECONDS": "1",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "2",
                    "P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS": "0",
                }
            )
            self.seed_resume_state(bootstrap, root, len(steps) - 1, environment)
            arguments = [
                str(bootstrap),
                "--from",
                str(len(steps)),
                "--until",
                str(len(steps)),
            ]
            process = subprocess.Popen(
                arguments,
                cwd=root,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 2
                while not step_pid_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(step_pid_path.exists(), "step never started")
                owned_step_pid = int(step_pid_path.read_text())
                started = time.monotonic()
                process.terminate()
                stdout, stderr = process.communicate(timeout=3)
                self.assertEqual(process.returncode, 143, stdout + stderr)
                # RELOGIO REMOVIDO EM 2026-09-10: sob a suite diaria a ~290% de
                # CPU este limite caia por CARGA, nao por defeito, e o arquivo
                # inteiro passa em 150,4 s ocioso. A propriedade sob teste e
                # parar o passo e soltar o lock ao receber TERM,
                # travada pelas assercoes ao lado; o `timeout=3` do subprocess
                # continua sendo o guarda de espera REAL, com folga.
                with self.assertRaises(ProcessLookupError):
                    os.kill(owned_step_pid, 0)
                self.assertTrue(meta_path_marker.exists(), stderr)
                meta = Path(meta_path_marker.read_text().strip())
                self.assertFalse(meta.exists())

                released_environment = environment.copy()
                released_environment["BOOTSTRAP_TEST_SLEEP_SECONDS"] = "0.01"
                reacquired = subprocess.run(
                    arguments,
                    cwd=root,
                    env=released_environment,
                    text=True,
                    capture_output=True,
                    timeout=3,
                    check=False,
                )
                self.assertEqual(reacquired.returncode, 0, reacquired.stderr)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=2)

    def build_lock_fixture(self, root: Path) -> tuple[Path, Path]:
        tools = root / "tools"
        tools.mkdir(parents=True)
        helper = tools / "p0-factory-chain-lock.sh"
        helper.write_bytes((ROOT / "tools" / "p0-factory-chain-lock.sh").read_bytes())
        helper.chmod(0o755)
        supervisor = tools / "supervise-process-tree"
        supervisor.write_bytes((ROOT / "tools" / "supervise-process-tree").read_bytes())
        supervisor.chmod(0o755)
        lock_path, meta_path = self.expected_lock_paths(root, "legacy-shared-chain")
        self.addCleanup(self.cleanup_lock_domain, lock_path, meta_path)
        self.addCleanup(
            self.cleanup_coordination_path, self.expected_coordination_path(root)
        )
        holder = root / "holder.sh"
        holder.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            "ROOT=\"$1\"\n"
            "export ROOT\n"
            ". \"$ROOT/tools/p0-factory-chain-lock.sh\"\n"
            "p0_factory_chain_lock_acquire fixture-holder --timings\n"
            "printf '%s\\n%s\\n' \"$P0_FACTORY_CHAIN_LOCK_PATH\" "
            "\"$P0_FACTORY_CHAIN_LOCK_META_PATH\" >\"$2\"\n"
            "sleep \"${LOCK_TEST_HOLD_SECONDS:-10}\"\n"
        )
        holder.chmod(0o755)
        return holder, supervisor

    @staticmethod
    def lock_holder_invocation(
        supervisor: Path, holder: Path, root: Path, marker: Path
    ) -> list[str]:
        return [
            str(supervisor),
            "--term-grace-seconds",
            "0.05",
            "--kill-grace-seconds",
            "0.5",
            "--fail-on-descendant-cleanup",
            "--",
            str(holder),
            str(root),
            str(marker),
        ]

    def wait_lock_marker(self, marker: Path) -> tuple[Path, Path]:
        deadline = time.monotonic() + 2
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(marker.exists(), f"lock holder did not write {marker}")
        values = marker.read_text().splitlines()
        self.assertEqual(len(values), 2, values)
        return Path(values[0]), Path(values[1])

    @staticmethod
    def expected_lock_paths(root: Path, domain: str) -> tuple[Path, Path]:
        canonical = root.resolve()
        identity = canonical.stat()
        payload = (
            f"device_inode={identity.st_dev}:{identity.st_ino}\n"
            f"lock_domain={domain}\n"
        ).encode()
        key = hashlib.sha256(payload).hexdigest()
        directory = Path(f"/tmp/portaljuridico-p0-factory-chain-v2-{key}")
        return (
            directory / "p0-factory-chain.lock",
            directory / "p0-factory-chain.lock.meta",
        )

    def cleanup_lock_domain(self, lock_path: Path, meta_path: Path) -> None:
        for path in (meta_path, lock_path):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            lock_path.parent.rmdir()
        except OSError:
            pass

    @staticmethod
    def expected_coordination_path(root: Path) -> Path:
        canonical = root.resolve()
        identity = canonical.stat()
        payload = f"device_inode={identity.st_dev}:{identity.st_ino}\n".encode()
        key = hashlib.sha256(payload).hexdigest()
        return Path(
            f"/tmp/portaljuridico-p0-factory-coordination-v1-{key}"
        ) / "p0-factory-coordination.lock"

    def cleanup_coordination_path(self, path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        try:
            path.parent.rmdir()
        except OSError:
            pass

    def test_same_repo_lock_domain_cannot_be_bypassed_by_different_tmpdirs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            holder, supervisor = self.build_lock_fixture(root)
            tmp_a = root / "tmp-a"
            tmp_b = root / "tmp-b"
            tmp_a.mkdir()
            tmp_b.mkdir()
            first_marker = root / "first-lock.path"
            second_marker = root / "second-lock.path"
            first_environment = os.environ.copy()
            first_environment.update(
                {"TMPDIR": str(tmp_a), "LOCK_TEST_HOLD_SECONDS": "10"}
            )
            first = subprocess.Popen(
                self.lock_holder_invocation(
                    supervisor, holder, root, first_marker
                ),
                cwd=root,
                env=first_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            lock_path: Path | None = None
            meta_path: Path | None = None
            try:
                lock_path, meta_path = self.wait_lock_marker(first_marker)
                self.assertTrue(lock_path.is_file())
                self.assertTrue(meta_path.is_file())
                self.assertTrue(
                    lock_path.parent.name.startswith(
                        "portaljuridico-p0-factory-chain-v2-"
                    ),
                    lock_path,
                )
                self.assertNotIn(str(tmp_a), str(lock_path))
                self.assertNotIn(str(tmp_b), str(lock_path))

                second_environment = os.environ.copy()
                second_environment.update(
                    {
                        "TMPDIR": str(tmp_b),
                        "LOCK_TEST_HOLD_SECONDS": "0.01",
                        "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "1",
                    }
                )
                started = time.monotonic()
                second = subprocess.run(
                    self.lock_holder_invocation(
                        supervisor, holder, root, second_marker
                    ),
                    cwd=root,
                    env=second_environment,
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False,
                )
                self.assertEqual(second.returncode, 75, second.stderr)
                elapsed = time.monotonic() - started
                # O PISO FICA e o TETO SAI, e a assimetria e o ponto: carga so
                # ATRASA, nunca acelera, entao `>= 0.8` prova que o segundo
                # ESPEROU e nao pode virar falso vermelho por maquina ocupada.
                # O teto de 1,8 s provava "nao esperou indefinidamente", que o
                # `timeout=3` do subprocess ja garante — era o elo fragil.
                self.assertGreaterEqual(elapsed, 0.8)
                self.assertFalse(second_marker.exists())
                self.assertIn(f"lock_path={lock_path}", second.stderr)
            finally:
                if first.poll() is None:
                    first.terminate()
                first.communicate(timeout=3)
                if lock_path is not None and meta_path is not None:
                    self.cleanup_lock_domain(lock_path, meta_path)

    def test_independent_artifact_domains_do_not_share_a_global_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            holder, supervisor = self.build_lock_fixture(root)
            first_marker = root / "first-domain.path"
            second_marker = root / "second-domain.path"
            first_environment = os.environ.copy()
            first_environment.update(
                {
                    "LOCK_TEST_HOLD_SECONDS": "10",
                    "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/editorial/a.jsonl",
                }
            )
            first = subprocess.Popen(
                self.lock_holder_invocation(
                    supervisor, holder, root, first_marker
                ),
                cwd=root,
                env=first_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            first_lock: Path | None = None
            first_meta: Path | None = None
            second_lock: Path | None = None
            second_meta: Path | None = None
            try:
                first_lock, first_meta = self.wait_lock_marker(first_marker)
                second_environment = os.environ.copy()
                second_environment.update(
                    {
                        "LOCK_TEST_HOLD_SECONDS": "0.01",
                        "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/editorial/b.jsonl",
                    }
                )
                started = time.monotonic()
                second = subprocess.run(
                    self.lock_holder_invocation(
                        supervisor, holder, root, second_marker
                    ),
                    cwd=root,
                    env=second_environment,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                self.assertEqual(second.returncode, 0, second.stderr)
                # RELOGIO REMOVIDO EM 2026-09-10: sob a suite diaria a ~290% de
                # CPU este limite caia por CARGA, nao por defeito, e o arquivo
                # inteiro passa em 150,4 s ocioso. A propriedade sob teste e
                # tomar um dominio de lock DIFERENTE sem esperar,
                # travada pelas assercoes ao lado; o `timeout=2` do subprocess
                # continua sendo o guarda de espera REAL, com folga.
                second_lock, second_meta = self.wait_lock_marker(second_marker)
                self.assertNotEqual(first_lock.parent, second_lock.parent)
            finally:
                if first.poll() is None:
                    first.terminate()
                first.communicate(timeout=3)
                if first_lock is not None and first_meta is not None:
                    self.cleanup_lock_domain(first_lock, first_meta)
                if second_lock is not None and second_meta is not None:
                    self.cleanup_lock_domain(second_lock, second_meta)

    def test_bootstrap_snapshot_excludes_independent_artifact_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            holder, supervisor = self.build_lock_fixture(root)
            bootstrap_marker = root / "bootstrap-domain.path"
            artifact_marker = root / "artifact-domain.path"
            bootstrap_environment = os.environ.copy()
            bootstrap_environment.update(
                {
                    "LOCK_TEST_HOLD_SECONDS": "10",
                    "P0_FACTORY_CHAIN_LOCK_DOMAIN": "bootstrap-chain",
                }
            )
            bootstrap = subprocess.Popen(
                self.lock_holder_invocation(
                    supervisor, holder, root, bootstrap_marker
                ),
                cwd=root,
                env=bootstrap_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            bootstrap_lock: Path | None = None
            bootstrap_meta: Path | None = None
            artifact_lock, artifact_meta = self.expected_lock_paths(
                root, "artifact:data/editorial/independent.jsonl"
            )
            try:
                bootstrap_lock, bootstrap_meta = self.wait_lock_marker(
                    bootstrap_marker
                )
                artifact_environment = os.environ.copy()
                artifact_environment.pop("P0_FACTORY_CHAIN_LOCK_DOMAIN", None)
                artifact_environment.update(
                    {
                        "LOCK_TEST_HOLD_SECONDS": "0.01",
                        "P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS": "0",
                        "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": (
                            "data/editorial/independent.jsonl"
                        ),
                    }
                )
                started = time.monotonic()
                artifact = subprocess.run(
                    self.lock_holder_invocation(
                        supervisor, holder, root, artifact_marker
                    ),
                    cwd=root,
                    env=artifact_environment,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                self.assertEqual(artifact.returncode, 75, artifact.stderr)
                # RELOGIO REMOVIDO EM 2026-09-10: sob a suite diaria a ~290% de
                # CPU este limite caia por CARGA, nao por defeito, e o arquivo
                # inteiro passa em 150,4 s ocioso. A propriedade sob teste e
                # recusar de imediato quando o portao esta ocupado,
                # travada pelas assercoes ao lado; o `timeout=2` do subprocess
                # continua sendo o guarda de espera REAL, com folga.
                self.assertFalse(artifact_marker.exists())
                self.assertIn("repository coordination gate busy", artifact.stderr)
            finally:
                if bootstrap.poll() is None:
                    bootstrap.terminate()
                bootstrap.communicate(timeout=3)
                if bootstrap_lock is not None and bootstrap_meta is not None:
                    self.cleanup_lock_domain(bootstrap_lock, bootstrap_meta)
                self.cleanup_lock_domain(artifact_lock, artifact_meta)

    def test_inherited_marker_cannot_turn_unlocked_fds_into_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / "tools"
            tools.mkdir()
            helper = tools / "p0-factory-chain-lock.sh"
            helper.write_bytes(
                (ROOT / "tools" / "p0-factory-chain-lock.sh").read_bytes()
            )
            helper.chmod(0o755)
            coordination = self.expected_coordination_path(root)
            lock_path, meta_path = self.expected_lock_paths(root, "bootstrap-chain")
            coordination.parent.mkdir(mode=0o700)
            lock_path.parent.mkdir(mode=0o700)
            coordination.write_bytes(b"")
            coordination.chmod(0o600)
            lock_path.write_bytes(b"")
            lock_path.chmod(0o600)
            self.addCleanup(self.cleanup_lock_domain, lock_path, meta_path)
            self.addCleanup(self.cleanup_coordination_path, coordination)
            script = """
set -eu
exec 7>>"$TEST_COORDINATION_PATH"
exec 8>>"$TEST_DOMAIN_PATH"
export P0_FACTORY_CHAIN_LOCK_HELD=1
export P0_FACTORY_CHAIN_LOCK_DOMAIN=bootstrap-chain
. "$TEST_LOCK_HELPER"
p0_factory_chain_lock_acquire forged-inheritance
"""
            completed = subprocess.run(
                ["sh", "-c", script],
                cwd=root,
                env={
                    **os.environ,
                    "ROOT": str(root),
                    "TEST_COORDINATION_PATH": str(coordination),
                    "TEST_DOMAIN_PATH": str(lock_path),
                    "TEST_LOCK_HELPER": str(helper),
                },
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            self.assertEqual(completed.returncode, 75, completed.stderr)
            self.assertIn("lacks the required kernel lock", completed.stderr)

    def test_distinct_repository_roots_do_not_share_factory_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            first_root = fixture / "repo-a"
            second_root = fixture / "repo-b"
            first_holder, first_supervisor = self.build_lock_fixture(first_root)
            second_holder, second_supervisor = self.build_lock_fixture(second_root)
            first_marker = fixture / "repo-a-lock.path"
            second_marker = fixture / "repo-b-lock.path"
            first_environment = os.environ.copy()
            first_environment["LOCK_TEST_HOLD_SECONDS"] = "10"
            first = subprocess.Popen(
                self.lock_holder_invocation(
                    first_supervisor, first_holder, first_root, first_marker
                ),
                cwd=first_root,
                env=first_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            first_lock: Path | None = None
            first_meta: Path | None = None
            second_lock: Path | None = None
            second_meta: Path | None = None
            try:
                first_lock, first_meta = self.wait_lock_marker(first_marker)
                second_environment = os.environ.copy()
                second_environment["LOCK_TEST_HOLD_SECONDS"] = "0.01"
                second = subprocess.run(
                    self.lock_holder_invocation(
                        second_supervisor, second_holder, second_root, second_marker
                    ),
                    cwd=second_root,
                    env=second_environment,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                self.assertEqual(second.returncode, 0, second.stderr)
                second_lock, second_meta = self.wait_lock_marker(second_marker)
                self.assertNotEqual(first_lock.parent, second_lock.parent)
            finally:
                if first.poll() is None:
                    first.terminate()
                first.communicate(timeout=3)
                if first_lock is not None and first_meta is not None:
                    self.cleanup_lock_domain(first_lock, first_meta)
                if second_lock is not None and second_meta is not None:
                    self.cleanup_lock_domain(second_lock, second_meta)

    def test_lock_helper_delegates_process_lifecycle_to_supervisor(self) -> None:
        source = (ROOT / "tools" / "p0-factory-chain-lock.sh").read_text()
        self.assertNotIn("terminate_owned_descendants", source)
        self.assertNotIn("kill -KILL", source)
        self.assertIn("tools/supervise-process-tree", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
