#!/usr/bin/env python3
"""Contrato do launcher Claude-first do AI Terminal (ops/terminal/start-ai-terminal-claude.sh).

Frente 10 do plano docs/plans/IDE_TERMINAL_20260923_PLANO.md (2026-09-23): o
launcher so existia no home (~/start-ai-terminal-claude.sh), sem teste; o antigo,
do Codex, tem 37 assercoes em tools/test_start_ai_terminal.py. Este arquivo e o
par do Claude-first, no mesmo padrao: assercoes de texto sobre o contrato de
seguranca ("este script NUNCA pode deixar o dono sem terminal") e comportamento
real num servidor tmux ISOLADO (TMUX_TMPDIR e HOME no temporario, PATH hermetico
sem ~/.local/bin, entao nem o `claude` nem o `ai-top` do dono sao alcancaveis).

Cada verificacao de texto e uma funcao que devolve a lista de problemas e tem
mutantes que ela precisa matar.

Rodar: python3 tools/test_start_ai_terminal_claude.py   (saida 0 = verde)
Apontar para outra copia: TERMINAL_CONF_DIR=<dir>.
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIR = pathlib.Path(os.environ.get("TERMINAL_CONF_DIR", ROOT / "ops" / "terminal"))
LAUNCHER = DIR / "start-ai-terminal-claude.sh"
HOME_LAUNCHER = pathlib.Path.home() / "start-ai-terminal-claude.sh"
BASE_TMP = "/tmp/claude-1000" if pathlib.Path("/tmp/claude-1000").is_dir() else None
TETO_DA_MAQUINA = 512  # ~/.claude/settings.json (env) e ~/.claude/CLAUDE.md


def codigo(texto: str) -> str:
    """So as linhas que executam: comentario explica o passado (cita `codex doctor`)."""
    return "\n".join(l for l in texto.splitlines() if l.strip() and not l.strip().startswith("#"))


def problemas_launcher(texto: str) -> list[str]:
    p: list[str] = []
    c = codigo(texto)
    m = re.search(r'^export CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS="\$\{AI_TERM_MAX_AGENTS:-'
                  r'\$\{CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS:-(\d+)\}\}"$', c, re.M)
    if m is None:
        p.append("export de CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS fora da ordem "
                 "AI_TERM_MAX_AGENTS > ambiente > default")
    elif int(m.group(1)) < TETO_DA_MAQUINA:
        p.append(f"default de subagentes {m.group(1)} abaixo dos {TETO_DA_MAQUINA} configurados na maquina")
    corpo_fallback = re.search(r"fallback_shell\(\) \{\n(?P<corpo>.*?)\n\}", texto, re.S)
    if corpo_fallback is None or "exec bash -l" not in corpo_fallback.group("corpo"):
        p.append("fallback_shell() sem `exec bash -l`")
    if not re.search(r"^trap 'fallback_shell .*' ERR$", c, re.M):
        p.append("sem trap ERR que cai no fallback_shell")
    if not re.search(r"--plain\)\s+plain=1", c) or not re.search(r'if \[ "\$plain" -eq 1 \]; then\n\s+exec bash -l', c):
        p.append("--plain nao leva a `exec bash -l`")
    if not re.search(r"--shell-only\)\s+autostart_claude=0", c):
        p.append("--shell-only nao zera o autostart do claude")
    if not re.search(r'command -v tmux >/dev/null 2>&1; then\n\s+warn "tmux nao encontrado — shell puro"\n\s+exec bash -l', c):
        p.append("sem tmux o launcher nao cai em `exec bash -l`")
    if not c.rstrip().endswith("exec bash -l"):
        p.append("a ultima linha deixou de ser `exec bash -l` (attach que falha perderia o terminal)")
    if re.search(r"\bcodex\s+doctor\b", c):
        p.append("o launcher Claude-first voltou a rodar `codex doctor`")
    if re.search(r"exec\s+tmux\s+attach", c):
        p.append("`exec tmux attach` fecha a janela se o attach falhar")
    if "export COLORTERM=truecolor" not in c or "export AI_TERMINAL=claude" not in c:
        p.append("COLORTERM=truecolor e AI_TERMINAL=claude tem de ser exportados")
    if 'umask "${AI_TERM_UMASK:-022}"' not in c:
        p.append("umask padrao deixou de ser 022 (077 esconderia do sistema o que os agentes escrevem)")
    if "^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$" not in c:
        p.append("nome de sessao deixou de ser validado")
    return p


def env_hermetico(home: pathlib.Path, tmux_tmp: pathlib.Path, bin_dir: pathlib.Path | None = None) -> dict[str, str]:
    """HOME e TMUX_TMPDIR falsos; PATH sem ~/.local/bin (nem claude nem ai-top do dono)."""
    caminho = str(bin_dir) if bin_dir else "/usr/local/bin:/usr/bin:/bin"
    env = {"HOME": str(home), "PATH": caminho, "TMUX_TMPDIR": str(tmux_tmp), "LANG": "C.UTF-8",
           "XDG_CONFIG_HOME": str(home / ".config"), "TERM": "xterm-256color", "SHELL": "/bin/bash"}
    return env


class LauncherContratoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.texto = LAUNCHER.read_text(encoding="utf-8")

    def test_sintaxe_bash(self) -> None:
        r = subprocess.run(["bash", "-n", str(LAUNCHER)], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    @unittest.skipIf(shutil.which("shellcheck") is None, "shellcheck ausente")
    def test_shellcheck(self) -> None:
        r = subprocess.run(["shellcheck", "-S", "warning", "-x", str(LAUNCHER)], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_contrato_de_texto(self) -> None:
        self.assertEqual(problemas_launcher(self.texto), [])

    def test_executavel(self) -> None:
        self.assertTrue(os.access(LAUNCHER, os.X_OK))

    def test_codex_so_por_bandeira_explicita(self) -> None:
        # O unico caminho ao launcher do Codex e o braco de compatibilidade do case.
        c = codigo(self.texto)
        self.assertIn('readonly CODEX_LAUNCHER="$HOME/start-ai-terminal.sh"', c)
        linhas_codex = [l.strip() for l in c.splitlines() if "CODEX_LAUNCHER" in l]
        self.assertEqual(linhas_codex, [
            'readonly CODEX_LAUNCHER="$HOME/start-ai-terminal.sh"',
            'if [ -x "$CODEX_LAUNCHER" ]; then',
            'exec "$CODEX_LAUNCHER" "$@"',
            'fallback_shell "launcher Codex ausente: $CODEX_LAUNCHER"',
        ])

    def test_home_aponta_para_o_repo_quando_instalado(self) -> None:
        if not HOME_LAUNCHER.is_symlink():
            self.skipTest("ainda nao instalado (ops/terminal/instalar-terminal.sh cria o symlink)")
        self.assertEqual(HOME_LAUNCHER.resolve(), LAUNCHER.resolve())


class LauncherMutantesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.texto = LAUNCHER.read_text(encoding="utf-8")

    def _troca(self, velho: str, novo: str) -> str:
        self.assertEqual(self.texto.count(velho), 1, f"ancora do mutante nao e unica: {velho!r}")
        return self.texto.replace(velho, novo)

    def test_mutantes(self) -> None:
        mutantes = {
            "m1 teto de 48 de volta": self._troca(
                'export CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS="${AI_TERM_MAX_AGENTS:-${CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS:-512}}"',
                'export CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS="${AI_TERM_MAX_AGENTS:-48}"'),
            "m2 fallback sem shell": self._troca("  exec bash -l\n}\ntrap", "  exit 1\n}\ntrap"),
            "m3 codex doctor no caminho quente": self._troca(
                "export AI_TERMINAL=claude\n", "export AI_TERMINAL=claude\ncodex doctor --json >/dev/null\n"),
            "m4 exec no attach": self._troca(
                'if tmux attach-session -t "$attach_target"; then',
                'exec tmux attach-session -t "$attach_target"\nif false; then'),
            "m5 --shell-only ignorado": self._troca("--shell-only)         autostart_claude=0 ;;",
                                                    "--shell-only)         : ;;"),
            "m6 umask 077": self._troca('umask "${AI_TERM_UMASK:-022}"', 'umask "${AI_TERM_UMASK:-077}"'),
        }
        for nome, texto in mutantes.items():
            with self.subTest(mutante=nome):
                self.assertNotEqual(problemas_launcher(texto), [], f"mutante sobreviveu: {nome}")


@unittest.skipIf(shutil.which("tmux", path="/usr/local/bin:/usr/bin:/bin") is None, "tmux ausente")
class LauncherComportamentoTest(unittest.TestCase):
    """O launcher de verdade, num servidor tmux isolado e com PATH hermetico."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="launcher-claude-", dir=BASE_TMP)
        self.addCleanup(self.tmp.cleanup)
        base = pathlib.Path(self.tmp.name)
        self.home = base / "home"
        self.tmux_tmp = base / "tmux"
        self.home.mkdir()
        self.tmux_tmp.mkdir()
        self.addCleanup(self._mata_servidor)

    def _env(self, **extra: str) -> dict[str, str]:
        env = env_hermetico(self.home, self.tmux_tmp)
        env.update(extra)
        return env

    def _mata_servidor(self) -> None:
        subprocess.run(["tmux", "kill-server"], env=self._env(), capture_output=True, timeout=10, check=False)

    def _tmux(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["tmux", *args], env=self._env(), capture_output=True, text=True, timeout=10, check=False)

    def _roda(self, *args: str, env: dict[str, str] | None = None, launcher: pathlib.Path = LAUNCHER) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["/bin/bash", str(launcher), *args], env=env or self._env(), stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=30, check=False)

    def test_sessao_com_as_tres_janelas_e_o_ambiente(self) -> None:
        r = self._roda("--session=bancada-launcher", "--no-attach", f"--workdir={self.home}")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pronto (sem attach)", r.stdout)
        janelas = self._tmux("list-windows", "-t", "=bancada-launcher", "-F", "#{window_name}").stdout.split()
        self.assertEqual(janelas, ["claude", "shell", "mon"])
        for chave, valor in (("COLORTERM", "truecolor"), ("AI_TERMINAL", "claude"),
                             ("CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS", str(TETO_DA_MAQUINA))):
            with self.subTest(chave=chave):
                self.assertEqual(self._tmux("show-environment", "-g", chave).stdout.strip(), f"{chave}={valor}")

    def test_subagentes_pedido_explicito_vence(self) -> None:
        r = self._roda("--session=bancada-pedido", "--no-attach", env=self._env(AI_TERM_MAX_AGENTS="7"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._tmux("show-environment", "-g", "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS").stdout.strip(),
                         "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=7")

    def test_subagentes_valor_do_ambiente_nao_e_rebaixado(self) -> None:
        r = self._roda("--session=bancada-ambiente", "--no-attach",
                       env=self._env(CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS="900"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._tmux("show-environment", "-g", "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS").stdout.strip(),
                         "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=900")

    def test_mutante_de_48_e_visto_pelo_comportamento(self) -> None:
        mutante = pathlib.Path(self.tmp.name) / "launcher-48.sh"
        mutante.write_text(LAUNCHER.read_text(encoding="utf-8").replace(
            "${CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS:-512}}", "48}"), encoding="utf-8")
        r = self._roda("--session=bancada-mutante", "--no-attach", launcher=mutante)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(self._tmux("show-environment", "-g", "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS").stdout.strip(),
                            f"CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS={TETO_DA_MAQUINA}")

    def test_shell_only_nao_manda_o_claude(self) -> None:
        r = self._roda("--session=bancada-shell", "--no-attach", "--shell-only")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Claude Code iniciado", r.stdout)
        tela = self._tmux("capture-pane", "-p", "-t", "=bancada-shell:=claude").stdout
        self.assertNotIn("claude", tela.replace("[ai-terminal-claude]", ""))

    def test_sessao_existente_e_reusada(self) -> None:
        self.assertEqual(self._roda("--session=bancada-reuso", "--no-attach").returncode, 0)
        r = self._roda("--session=bancada-reuso", "--no-attach")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("sessao existente: bancada-reuso", r.stdout)
        self.assertEqual(self._tmux("list-sessions", "-F", "#{session_name}").stdout.split(), ["bancada-reuso"])

    def test_nome_de_sessao_invalido_vira_nome_derivado(self) -> None:
        r = self._roda("--session=nome com espaco", "--no-attach")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nome de sessao invalido", r.stderr)
        nomes = self._tmux("list-sessions", "-F", "#{session_name}").stdout.split()
        self.assertEqual(len(nomes), 1)
        self.assertRegex(nomes[0], r"^cc-\d{8}-\d{6}$")

    def test_plain_entrega_bash_de_login_sem_tmux(self) -> None:
        r = self._roda("--plain")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(self._tmux("list-sessions").returncode, 0, "o --plain criou sessao tmux")

    def test_sem_tmux_cai_no_shell(self) -> None:
        bin_dir = pathlib.Path(self.tmp.name) / "bin-sem-tmux"
        bin_dir.mkdir()
        for ferramenta in ("bash", "env", "date", "realpath", "grep", "sed", "cat", "tr", "id"):
            origem = shutil.which(ferramenta, path="/usr/bin:/bin")
            if origem:
                (bin_dir / ferramenta).symlink_to(origem)
        env = env_hermetico(self.home, self.tmux_tmp, bin_dir)
        r = self._roda("--no-attach", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tmux nao encontrado — shell puro", r.stderr)

    def test_argumento_desconhecido_e_avisado_e_ignorado(self) -> None:
        r = self._roda("--session=bancada-arg", "--no-attach", "--bandeira-que-nao-existe")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("argumento desconhecido ignorado: --bandeira-que-nao-existe", r.stderr)

    def test_ajuda(self) -> None:
        r = self._roda("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("USO", r.stdout)
        self.assertIn("--shell-only", LAUNCHER.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
