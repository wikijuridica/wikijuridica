#!/usr/bin/env python3
"""Focused contract tests for the Rafael Codex launcher."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import select
import shutil
import sqlite3
import stat
import subprocess
import tempfile
import time
import tomllib
import unittest
import uuid


ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools" / "start-ai-terminal"
PROJECT_CONFIG = ROOT / ".codex" / "config.toml"
OFFICIAL_CODEX = pathlib.Path("/home/rafael/.npm-global/bin/codex")
HOME_LAUNCHER = pathlib.Path("/home/rafael/start-ai-terminal.sh")
CODEX_BASE_HOME = pathlib.Path("/home/rafael/.codex")
TERMINAL_HOMES = CODEX_BASE_HOME / "terminal-homes"
SESSION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def canonical_home(session: str) -> pathlib.Path:
    if SESSION_NAME_RE.fullmatch(session) is None:
        raise ValueError(f"non-canonical tmux session name: {session}")
    safe = session[:48]
    digest = hashlib.sha256(session.encode("utf-8")).hexdigest()
    return TERMINAL_HOMES / f"{safe}--{digest}"


class StartAITerminalContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.launcher = LAUNCHER.read_text(encoding="utf-8")
        cls.project_config = PROJECT_CONFIG.read_text(encoding="utf-8")

    def test_shell_syntax_is_valid(self) -> None:
        subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)

    def test_installed_rafael_launcher_matches_versioned_launcher(self) -> None:
        self.assertTrue(HOME_LAUNCHER.is_file())
        self.assertEqual(HOME_LAUNCHER.read_bytes(), LAUNCHER.read_bytes())

    def test_only_official_rafael_npm_codex_is_executable(self) -> None:
        self.assertIn('if [ "$(id -un)" != "rafael" ]', self.launcher)
        self.assertIn("/.npm-global/lib/node_modules/@openai/codex/", self.launcher)
        self.assertIn("stable_resolved_codex_bin", self.launcher)
        self.assertNotIn("openai-codex-adaptive", self.launcher)

    def test_official_doctor_is_the_runtime_gate_not_a_version_floor(self) -> None:
        self.assertIn("run_official_doctor", self.launcher)
        self.assertIn("doctor --json", self.launcher)
        self.assertIn("LC_ALL=C.UTF-8 LANG=C.UTF-8", self.launcher)
        self.assertNotIn("LC_ALL=C NO_COLOR=1", self.launcher)
        self.assertIn('status not in {"ok", "warning"}', self.launcher)
        self.assertIn('check_status != "ok"', self.launcher)
        self.assertNotIn("codex_version_has_fast_doctor", self.launcher)
        self.assertNotIn("0.145.0-alpha.25", self.launcher)

    def test_manual_codex_commands_receive_the_official_capacity_override(self) -> None:
        self.assertIn("install_codex_command_wrapper", self.launcher)
        self.assertIn('wrapper_path="$CODEX_HOME/bin/codex"', self.launcher)
        self.assertIn("Encaminha exclusivamente ao pacote npm oficial", self.launcher)
        self.assertIn("agents.max_threads=$codex_max_threads", self.launcher)
        self.assertIn('codex_max_threads_override_set=0', self.launcher)
        self.assertIn('printf \'exec %q "$@"\\n\' "$codex_bin"', self.launcher)
        self.assertIn('export PATH="$wrapper_dir:$PATH"', self.launcher)
        self.assertNotIn("export -f codex", self.launcher)

    def test_default_capacity_is_left_to_official_codex(self) -> None:
        for fragment in (
            "--max-agents=*",
            "requested_codex_max_threads_set=1",
            "AI_CODEX_MAX_THREADS",
            "codex_max_threads_override_set=1",
            "padrão oficial do Codex",
            "Sem override, nenhum `-c` é injetado",
            'agents.max_threads=$codex_max_threads',
            "run_official_doctor",
            "doctor --json",
            "--strict-config -C",
            "timeout --signal=TERM --kill-after=2s 20s",
        ):
            self.assertIn(fragment, self.launcher)
        for forbidden in (
            "resolve_system_agent_headroom",
            "ulimit -Su",
            "/proc/self/cgroup",
            "pids.max",
            "pids.current",
            "headroom de segurança",
        ):
            self.assertNotIn(forbidden, self.launcher)
        self.assertNotRegex(self.launcher, r"codex_max_threads=[\"']?[0-9]+")
        self.assertNotIn("features.multi_agent_v2.enabled", self.launcher)
        self.assertNotIn("max_concurrent_threads_per_session", self.launcher)

        launch_function = re.search(
            r"codex_launch_command\(\) \{\n(?P<body>.*?)\n\}", self.launcher, re.DOTALL
        )
        self.assertIsNotNone(launch_function)
        launch_body = launch_function.group("body")
        self.assertIn('if [ "$codex_max_threads_override_set" -eq 1 ]; then', launch_body)
        self.assertIn("printf ' -c %s'", launch_body)

    def test_aliases_and_worker_shortcuts_are_rejected_by_contract(self) -> None:
        self.assertIn(
            '[[ ! "$codex_max_threads" =~ ^[1-9][0-9]*$ ]]', self.launcher
        )
        for forbidden in (
            "openai-codex-adaptive",
            "multi_agent_v2",
            "max_concurrent_threads_per_session",
            "workers=2",
            'codex_max_threads="adaptive"',
            'codex_max_threads="unlimited"',
        ):
            self.assertNotIn(forbidden, self.launcher)

    def test_explicit_override_12_is_accepted_by_official_codex_parser(self) -> None:
        resolved = OFFICIAL_CODEX.resolve(strict=True)
        self.assertIn("/@openai/codex/", str(resolved))
        environment = os.environ.copy()
        environment["CODEX_HOME"] = "/home/rafael/.codex"
        result = subprocess.run(
            [str(resolved), "-c", "agents.max_threads=12", "features", "list"],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_project_config_has_no_persistent_numeric_agent_cap(self) -> None:
        parsed = tomllib.loads(self.project_config)
        self.assertNotIn("max_threads", parsed.get("agents", {}))
        self.assertNotIn('"adaptive"', self.project_config)
        # ★ A ASSERÇÃO ANTERIOR EXIGIA O NÚMERO QUE ESTE TESTE EXISTE PARA PROIBIR.
        #
        # Ela era `assertIn("padrão do Codex (6 threads abertas)", …)`, e o nome
        # deste teste é "has_no_persistent_numeric_agent_cap". O config foi
        # corrigido — ele hoje diz, com todas as letras, que "citar um número
        # aqui, mesmo como descrição do padrão alheio, é o que o contrato proíbe:
        # número em documento de projeto vira teto por citação" — e a asserção
        # ficou exigindo a frase velha, com o 6 dentro. Resultado: o teste
        # reprovava o config CERTO e passaria a aprovar o errado, e ia vermelho
        # todo dia no ledger da varredura desde 2026-08-30.
        #
        # A âncora nova é a afirmação, não o número: o config precisa continuar
        # DOCUMENTANDO a ausência de teto (senão a próxima edição distraída
        # apenas apaga a explicação), sem que nenhum número volte a ser citado.
        self.assertIn("não declara teto de agentes", self.project_config)
        self.assertNotRegex(self.project_config, r"max_threads\s*=\s*\d")

    def test_launcher_does_not_delete_resume_history(self) -> None:
        self.assertNotIn("--include-history", self.launcher)
        self.assertNotRegex(self.launcher, r"ai-terminal-gc[^\n]*--apply")
        self.assertNotRegex(self.launcher, r"\b(rm|find)\b[^\n]*(sessions|terminal-homes)")

    def test_isolated_home_does_not_link_sessions_or_sqlite(self) -> None:
        self.assertIn("session_hash", self.launcher)
        self.assertIn("${safe_prefix}--${session_hash}", self.launcher)
        self.assertIn("CODEX_HOME compartilhado foi desativado", self.launcher)
        self.assertIn("AI_CODEX_HOME divergente recusado", self.launcher)
        self.assertIn("sessions archived_sessions", self.launcher)
        self.assertIn("é symlink (backfill/estado compartilhado proibido)", self.launcher)
        self.assertIn(
            'for candidate in "$CODEX_HOME"/*.sqlite* "$CODEX_HOME"/.*.sqlite*',
            self.launcher,
        )
        self.assertIn("thread_history_1.sqlite", self.launcher)
        self.assertNotRegex(self.launcher, r"for shared_dir in[^\n]*\bsessions\b")
        self.assertIn("CODEX_SQLITE_HOME", self.launcher)
        self.assertIn("sqlite_home e pode", self.launcher)
        self.assertNotIn('link_shared_codex_path "sessions"', self.launcher)

    def test_resume_is_exact_local_and_never_imports_global_history(self) -> None:
        self.assertIn("--resume=<UUID>", self.launcher)
        self.assertIn("codex resume $resume_thread_id", self.launcher)
        self.assertIn("SELECT rollout_path FROM threads", self.launcher)
        self.assertIn('header.get("type") != "session_meta"', self.launcher)
        self.assertIn("Consulte", self.launcher)
        self.assertIn("todos em read-only", self.launcher)
        self.assertNotIn("run_official_non_tty_probe", self.launcher)
        self.assertNotIn("stdin is not a terminal", self.launcher)
        self.assertIn("não está indexado neste home", self.launcher)
        self.assertIn('"$CODEX_HOME"/sessions/*.jsonl', self.launcher)
        self.assertNotIn("CODEX_BASE_HOME/sessions", self.launcher)

    def test_exact_legacy_home_has_a_forward_compatible_adoption_path(self) -> None:
        self.assertIn("adopt_existing_session_home", self.launcher)
        self.assertIn('legacy_codex_home="$CODEX_BASE_HOME/terminal-homes/$session"', self.launcher)
        self.assertIn("home legado exato da sessão", self.launcher)
        self.assertIn("nunca copie/linke sessions ou SQLite", self.launcher)

    def test_preflight_uses_the_actual_isolated_home(self) -> None:
        self.assertIn("preflight_codex_home", self.launcher)
        self.assertIn(
            'CODEX_HOME="$CODEX_HOME" CODEX_SQLITE_HOME="$CODEX_SQLITE_HOME"',
            self.launcher,
        )
        self.assertNotIn('CODEX_HOME="$CODEX_BASE_HOME" "$codex_bin"', self.launcher)
        self.assertNotIn("features list >/dev/null", self.launcher)
        self.assertIn("doctor --json", self.launcher)
        self.assertIn('status not in {"ok", "warning"}', self.launcher)

    def test_session_names_and_tmux_targets_are_canonical_and_exact(self) -> None:
        self.assertIn(
            '[[ ! "$session" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$ ]]',
            self.launcher,
        )
        self.assertIn('tmux_session_target="=$session"', self.launcher)
        self.assertIn('tmux_shell_target="${tmux_session_target}:=shell"', self.launcher)
        self.assertIn('tmux_codex_target="${tmux_session_target}:=codex"', self.launcher)
        self.assertNotRegex(self.launcher, r'tmux (?:has-session|show-environment|set-environment)[^\n]*-t "\$session"')

    def test_persistent_capacity_guard_parses_toml_and_scans_all_layers(self) -> None:
        self.assertIn("import tomllib", self.launcher)
        self.assertIn('"max_threads" in agents', self.launcher)
        self.assertIn('"$CODEX_BASE_HOME/config.toml"', self.launcher)
        self.assertIn('/etc/codex/config.toml', self.launcher)
        self.assertIn('config_path="$cursor/.codex/config.toml"', self.launcher)
        self.assertIn("remova o cap persistente ou use override explícito", self.launcher)

    def test_each_existing_home_path_component_is_checked_before_realpath(self) -> None:
        function = re.search(
            r"reject_symlink_components\(\) \{\n(?P<body>.*?)\n\}",
            self.launcher,
            re.DOTALL,
        )
        self.assertIsNotNone(function)
        self.assertIn('reject_symlink_components "$CODEX_BASE_HOME/terminal-homes"', self.launcher)
        self.assertIn('reject_symlink_components "$expected_home"', self.launcher)
        with tempfile.TemporaryDirectory(prefix="codex-launcher-path-guard-") as fixture:
            fixture_path = pathlib.Path(fixture)
            real_parent = fixture_path / "real-parent"
            real_parent.mkdir()
            linked_parent = fixture_path / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            script = (
                function.group(0)
                + '\nhome_contract_error() { printf "%s\\n" "$1" >&2; exit 2; }\n'
                + 'reject_symlink_components "$1"\n'
            )
            result = subprocess.run(
                ["bash", "-c", script, "bash", str(linked_parent / "child")],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("componente intermediário symlinkado", result.stderr)

    def test_unknown_arguments_are_rejected_by_default_case(self) -> None:
        self.assertIn("argumento desconhecido recusado", self.launcher)

    def test_private_permissions_are_propagated_to_wrapper_and_panes(self) -> None:
        self.assertIn("umask 077", self.launcher)
        self.assertIn('chmod 0700 "$CODEX_HOME"', self.launcher)
        self.assertIn(
            'tmux set-environment -t "$tmux_session_target" CODEX_SQLITE_HOME "$CODEX_SQLITE_HOME"',
            self.launcher,
        )
        self.assertIn('export CODEX_HOME=%q CODEX_SQLITE_HOME=%q', self.launcher)

    def test_existing_process_is_not_reported_as_reconfigured(self) -> None:
        self.assertIn("Cap de threads de agentes abertas para novos processos", self.launcher)
        self.assertIn("o cap de threads carregado não muda", self.launcher)
        self.assertNotIn("subagentes + raiz", self.launcher)

    def test_missing_tmux_fails_instead_of_losing_the_wrapper(self) -> None:
        self.assertIn("tmux é obrigatório", self.launcher)
        self.assertNotIn("tmux nao encontrado; abrindo shell", self.launcher)


@unittest.skipUnless(
    os.getuid() == 1000
    and pathlib.Path.home() == pathlib.Path("/home/rafael")
    and OFFICIAL_CODEX.exists(),
    "fixtures do launcher exigem o usuário rafael e o Codex oficial local",
)
class StartAITerminalBehaviorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.session = f"codex-launcher-test-{uuid.uuid4().hex}"
        self.home = canonical_home(self.session)
        self.assertFalse(self.home.exists() or self.home.is_symlink())
        self.addCleanup(self._remove_owned_fixture, self.home)
        self.tmux_tmp = tempfile.TemporaryDirectory(prefix="codex-launcher-tmux-")
        self.tmux_tmp_path = pathlib.Path(self.tmux_tmp.name)
        self.addCleanup(self.tmux_tmp.cleanup)
        self.addCleanup(self._stop_isolated_tmux_server)

    @staticmethod
    def _remove_owned_fixture(path: pathlib.Path) -> None:
        if path.parent != TERMINAL_HOMES or not path.name.startswith("codex-launcher-test-"):
            raise AssertionError(f"refusing unsafe fixture cleanup: {path}")
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        for name in (
            "AI_CODEX_HOME",
            "AI_CODEX_MAX_THREADS",
            "AI_TMUX_SESSION",
            "CODEX_TMUX_SESSION",
            "CODEX_HOME",
            "TMUX",
            "TMUX_PANE",
        ):
            environment.pop(name, None)
        environment["AI_WORKDIR"] = str(ROOT)
        environment["AI_TERMINAL_ISOLATE_CODEX_HOME"] = "1"
        environment["CODEX_SQLITE_HOME"] = str(CODEX_BASE_HOME)
        environment["TMUX_TMPDIR"] = str(self.tmux_tmp_path)
        return environment

    def _stop_isolated_tmux_server(self) -> None:
        subprocess.run(
            ["tmux", "kill-server"],
            env=self._environment(),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )

    def _tmux(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        # -f os.devnull: tmux always reads ~/.tmux.conf at server start, no
        # matter which TMUX_TMPDIR isolates the socket. This host's config
        # turns on tmux-continuum's "@continuum-restore on" (~/.tmux.conf),
        # which resurrects the operator's real ai-* sessions into ANY fresh
        # server -- including one meant to be a throwaway per-test sandbox.
        # An empty config file suppresses that hook so the isolated server
        # only ever contains what this test itself created.
        return subprocess.run(
            ["tmux", "-f", os.devnull, *args],
            env=self._environment(),
            check=check,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _run(
        self,
        *extra_args: str,
        environment: dict[str, str] | None = None,
        include_session: bool = True,
        validate_only: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        command = [str(LAUNCHER)]
        if include_session:
            command.append(f"--session={self.session}")
        if validate_only:
            command.append("--validate-only")
        command.extend(("--no-attach", *extra_args))
        return subprocess.run(
            command,
            cwd=ROOT,
            env=environment or self._environment(),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    @staticmethod
    def _send_app_server_message(
        process: subprocess.Popen[str], message: dict[str, object]
    ) -> None:
        assert process.stdin is not None
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def _read_app_server_response(
        self, process: subprocess.Popen[str], request_id: int, timeout: float = 10
    ) -> dict[str, object]:
        assert process.stdout is not None
        deadline = time.monotonic() + timeout
        observed: list[dict[str, object]] = []
        while time.monotonic() < deadline:
            ready, _, _ = select.select(
                [process.stdout], [], [], max(0.0, deadline - time.monotonic())
            )
            if not ready:
                break
            line = process.stdout.readline()
            if not line:
                break
            message = json.loads(line)
            observed.append(message)
            if message.get("id") == request_id:
                return message
        self.fail(f"app-server did not answer request {request_id}; observed={observed!r}")

    def _create_official_thread(self) -> tuple[str, pathlib.Path]:
        environment = self._environment()
        environment["CODEX_HOME"] = str(self.home)
        environment["CODEX_SQLITE_HOME"] = str(self.home)
        process = subprocess.Popen(
            [
                str(OFFICIAL_CODEX.resolve(strict=True)),
                "--strict-config",
                "-C",
                str(ROOT),
                "app-server",
                "--listen",
                "stdio://",
            ],
            cwd=ROOT,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self._send_app_server_message(
                process,
                {
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {"name": "launcher-test", "version": "1.0"},
                        "capabilities": {"experimentalApi": True},
                    },
                },
            )
            initialized = self._read_app_server_response(process, 1)
            self.assertNotIn("error", initialized)
            self._send_app_server_message(process, {"method": "initialized"})
            self._send_app_server_message(
                process,
                {
                    "id": 2,
                    "method": "thread/start",
                    "params": {"cwd": str(ROOT), "ephemeral": False},
                },
            )
            started = self._read_app_server_response(process, 2)
            self.assertNotIn("error", started)
            thread = started["result"]["thread"]  # type: ignore[index]
            self._send_app_server_message(
                process,
                {
                    "id": 3,
                    "method": "thread/name/set",
                    "params": {
                        "threadId": thread["id"],
                        "name": "isolated launcher resume fixture",
                    },
                },
            )
            named = self._read_app_server_response(process, 3)
            self.assertNotIn("error", named)
            return str(thread["id"]), pathlib.Path(thread["path"])
        finally:
            if process.stdin is not None:
                process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

    def test_legacy_sessions_symlink_fails_closed_without_touching_it(self) -> None:
        self.home.mkdir(mode=0o700)
        with tempfile.TemporaryDirectory(prefix="codex-launcher-target-") as target:
            target_path = pathlib.Path(target)
            sessions_link = self.home / "sessions"
            sessions_link.symlink_to(target_path, target_is_directory=True)
            before_target = os.readlink(sessions_link)

            result = self._run()

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("sessions é symlink", result.stderr)
            self.assertTrue(sessions_link.is_symlink())
            self.assertEqual(os.readlink(sessions_link), before_target)
            self.assertTrue(target_path.is_dir())
            self.assertFalse((self.home / "bin").exists())

    def test_validate_only_creates_private_canonical_home_and_wrapper(self) -> None:
        result = self._run()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("terminal.env", result.stderr)
        self.assertNotIn("locale is not UTF-8", result.stderr)
        self.assertEqual(stat.S_IMODE(self.home.stat().st_mode), 0o700)
        self.assertEqual((self.home / "config.toml").resolve(), (CODEX_BASE_HOME / "config.toml").resolve())
        self.assertFalse((self.home / "sessions").is_symlink())
        wrapper = (self.home / "bin" / "codex").read_text(encoding="utf-8")
        self.assertIn("umask 077", wrapper)
        self.assertIn(f"CODEX_HOME={self.home}", wrapper)
        self.assertIn(f"CODEX_SQLITE_HOME={self.home}", wrapper)
        self.assertNotIn("agents.max_threads=", wrapper)

    def test_explicit_capacity_override_reaches_only_official_key(self) -> None:
        result = self._run("--max-agents=12")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        wrapper = (self.home / "bin" / "codex").read_text(encoding="utf-8")
        self.assertIn("-c agents.max_threads=12", wrapper)
        self.assertNotIn("multi_agent_v2", wrapper)
        self.assertNotIn("max_concurrent_threads_per_session", wrapper)

    def test_stale_regular_config_is_refused_and_not_replaced(self) -> None:
        self.home.mkdir(mode=0o700)
        stale_config = self.home / "config.toml"
        marker = "# config stale que não pode ser confiada\n"
        stale_config.write_text(marker, encoding="utf-8")

        result = self._run()

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("cópia local/stale", result.stderr)
        self.assertFalse(stale_config.is_symlink())
        self.assertEqual(stale_config.read_text(encoding="utf-8"), marker)
        self.assertFalse((self.home / "bin").exists())

    def test_divergent_explicit_home_is_rejected_without_creation(self) -> None:
        divergent = TERMINAL_HOMES / f"codex-launcher-test-divergent-{uuid.uuid4().hex}"
        self.addCleanup(self._remove_owned_fixture, divergent)
        environment = self._environment()
        environment["AI_CODEX_HOME"] = str(divergent)

        result = self._run(environment=environment)

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("AI_CODEX_HOME divergente recusado", result.stderr)
        self.assertFalse(divergent.exists())
        self.assertFalse(self.home.exists())

    def test_tmux_normalizing_names_are_rejected_before_home_creation(self) -> None:
        stem = f"codex-launcher-test-{uuid.uuid4().hex[:12]}"
        for suffix in (".dot", ":colon", " space"):
            session = stem + suffix
            legacy_safe = re.sub(r"[^A-Za-z0-9._-]", "_", session)[:48] or "session"
            legacy_home = TERMINAL_HOMES / (
                f"{legacy_safe}--{hashlib.sha256(session.encode('utf-8')).hexdigest()}"
            )
            self.addCleanup(self._remove_owned_fixture, legacy_home)
            result = subprocess.run(
                [str(LAUNCHER), f"--session={session}", "--validate-only", "--no-attach"],
                cwd=ROOT,
                env=self._environment(),
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("nome de sessão não canônico", result.stderr)
            self.assertFalse(legacy_home.exists() or legacy_home.is_symlink())

    def test_real_tmux_prefix_collision_uses_exact_session_targets(self) -> None:
        longer_session = f"{self.session}-long"
        self._tmux("new-session", "-d", "-s", longer_session, "-n", "shell", check=True)

        result = self._run("--shell-only", validate_only=False)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        sessions = self._tmux("list-sessions", "-F", "#{session_name}", check=True)
        self.assertEqual(set(sessions.stdout.splitlines()), {self.session, longer_session})
        self.assertTrue(self.home.is_dir())

    def test_live_tmux_session_adopts_its_exact_legacy_home_without_migration(self) -> None:
        legacy_home = TERMINAL_HOMES / self.session
        self.addCleanup(self._remove_owned_fixture, legacy_home)
        sessions = legacy_home / "sessions"
        sessions.mkdir(parents=True, mode=0o700)
        marker = sessions / "preserve-me.txt"
        marker.write_text("estado local preservado\n", encoding="utf-8")
        self._tmux(
            "new-session",
            "-d",
            "-s",
            self.session,
            "-n",
            "shell",
            "-e",
            f"CODEX_HOME={legacy_home}",
            check=True,
        )

        result = self._run()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(str(legacy_home), result.stdout)
        self.assertFalse(self.home.exists() or self.home.is_symlink())
        self.assertFalse(sessions.is_symlink())
        self.assertEqual(marker.read_text(encoding="utf-8"), "estado local preservado\n")

    def test_unknown_argument_fails_before_home_creation(self) -> None:
        result = self._run("--definitely-unknown")

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("argumento desconhecido recusado", result.stderr)
        self.assertFalse(self.home.exists() or self.home.is_symlink())

    def test_resume_without_explicit_session_is_deterministic_and_creates_nothing(self) -> None:
        thread_id = str(uuid.uuid4())
        marker_session = f"codex-launcher-test-{uuid.uuid4().hex}"
        marker_home = canonical_home(marker_session)
        self.addCleanup(self._remove_owned_fixture, marker_home)
        environment = self._environment()
        environment["AI_CODEX_HOME"] = str(marker_home)

        result = self._run(
            f"--resume={thread_id}",
            environment=environment,
            include_session=False,
        )

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("exige --session=<nome>", result.stderr)
        self.assertIn("nenhum home foi criado", result.stderr)
        self.assertFalse(marker_home.exists() or marker_home.is_symlink())

    def test_resume_requires_thread_already_indexed_in_same_home(self) -> None:
        thread_id = str(uuid.uuid4())
        result = self._run(f"--resume={thread_id}")

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("não está indexado neste home", result.stderr)
        self.assertNotIn(str(CODEX_BASE_HOME / "sessions"), result.stderr)
        self.assertFalse((self.home / "sessions").is_symlink())

    def test_resume_rejects_minimal_fake_database_and_rollout(self) -> None:
        thread_id = str(uuid.uuid4())
        rollout_dir = self.home / "sessions" / "2026" / "07" / "21"
        rollout_dir.mkdir(parents=True, mode=0o700)
        rollout = rollout_dir / f"rollout-2026-07-21T00-00-00-{thread_id}.jsonl"
        rollout.write_text("{}\n", encoding="utf-8")
        database = self.home / "state_5.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT NOT NULL, archived INTEGER NOT NULL)"
            )
            connection.execute(
                "INSERT INTO threads(id, rollout_path, archived) VALUES (?, ?, 0)",
                (thread_id, str(rollout)),
            )

        result = self._run(f"--resume={thread_id}")

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Doctor oficial concluiu com avisos", result.stderr)
        self.assertIn("state.rollout_db_parity", result.stderr)
        self.assertIn("não tem header oficial válido", result.stderr)
        self.assertEqual(rollout.read_text(encoding="utf-8"), "{}\n")

    def test_resume_accepts_only_state_and_rollout_created_by_official_app_server(self) -> None:
        initialized = self._run()
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        thread_id, rollout = self._create_official_thread()
        before = rollout.read_bytes()
        first = json.loads(before.splitlines()[0])
        self.assertEqual(first["type"], "session_meta")
        self.assertEqual(first["payload"]["id"].lower(), thread_id.lower())
        # Simula upgrade oficial que preserva um state DB anterior. O resume
        # deve consultar todos em read-only, não exigir exatamente um arquivo.
        previous_database = self.home / "state_4.sqlite"
        with sqlite3.connect(previous_database) as connection:
            connection.execute(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT NOT NULL, archived INTEGER NOT NULL)"
            )
        result = self._run(f"--resume={thread_id}")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Home canônico validado", result.stdout)
        self.assertEqual(rollout.read_bytes(), before)

    def test_official_preflight_loads_invalid_nested_project_config(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".codex-launcher-invalid-config-", dir=ROOT
        ) as fixture:
            workdir = pathlib.Path(fixture)
            config_dir = workdir / ".codex"
            config_dir.mkdir()
            (config_dir / "config.toml").write_text("[broken\n", encoding="utf-8")
            environment = self._environment()
            environment["AI_WORKDIR"] = str(workdir)

            result = self._run(environment=environment)

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Doctor oficial recusou", result.stderr)
        self.assertEqual(result.stderr.count("Doctor oficial recusou"), 1)
        self.assertIn(str(workdir), result.stderr)
        self.assertIn('"id": "config.load"', result.stderr)
        self.assertIn("Fix the reported config error, then rerun codex doctor.", result.stderr)
        self.assertIn("Reproduza sem launcher:", result.stderr)
        self.assertIn("doctor --no-color --all", result.stderr)
        self.assertNotIn("stdin is not a terminal", result.stderr)

    def test_persistent_project_agent_caps_require_explicit_override(self) -> None:
        forms = {
            "dotted": "agents.max_threads = 12\n",
            "table": "[agents]\nmax_threads = 12\n",
            "inline": "agents = { max_threads = 12 }\n",
        }
        for label, config_text in forms.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f".codex-launcher-cap-{label}-", dir=ROOT
            ) as fixture:
                workdir = pathlib.Path(fixture)
                config_dir = workdir / ".codex"
                config_dir.mkdir()
                (config_dir / "config.toml").write_text(config_text, encoding="utf-8")
                environment = self._environment()
                environment["AI_WORKDIR"] = str(workdir)

                refused = self._run(environment=environment)
                self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
                self.assertIn("fixa agents.max_threads", refused.stderr)
                self.assertFalse(self.home.exists() or self.home.is_symlink())

                allowed = self._run("--max-agents=7", environment=environment)
                self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
                wrapper = (self.home / "bin" / "codex").read_text(encoding="utf-8")
                self.assertIn("-c agents.max_threads=7", wrapper)
                self._remove_owned_fixture(self.home)

    def test_all_sqlite_names_and_sidecars_reject_symlinks(self) -> None:
        for name in (
            "thread_history_1.sqlite",
            "future.sqlite-wal",
            "future.sqlite-shm",
            ".hidden.sqlite-journal",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="codex-launcher-sqlite-target-"
            ) as target:
                self.home.mkdir(mode=0o700)
                linked = self.home / name
                linked.symlink_to(pathlib.Path(target) / "missing-target")

                result = self._run()

                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("SQLite/sidecar symlinkado", result.stderr)
                self.assertTrue(linked.is_symlink())
                self._remove_owned_fixture(self.home)


if __name__ == "__main__":
    unittest.main(verbosity=2)
