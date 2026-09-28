#!/usr/bin/env python3
"""Testes de .githooks/commit-msg — o hook que reprova co-autoria de MODELO.

POR QUE ELE EXISTE (2026-09-23). O CLAUDE.md do repositorio fixa que "nenhum
commit leva co-autoria de modelo" e nada o cobrava: 132 dos 200 commits mais
recentes traziam `Co-Authored-By: Claude ... <noreply@anthropic.com>`, e o
lembrete de atribuicao do harness propoe o trailer a cada sessao. Regra que
depende de o autor lembrar nao e regra.

O QUE FICA TRAVADO, e por que cada caso importa:

  1. mensagem limpa PASSA; `Claude-Session:` sozinho PASSA (e rastreabilidade
     da sessao, nao autoria); co-autor HUMANO passa;
  2. `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` REPROVA, com a
     regra e o remedio em PT-BR -- e o remedio nas DUAS ULTIMAS linhas do
     stderr, porque os dois timers que commitam dado capturam a saida do git
     com `tail -2`;
  3. caixa nao importa (`co-authored-by: claude ...`); `Claude` sem `anthropic`
     no e-mail reprova (3a) tanto quanto `anthropic` sem `Claude` (3b);
  4. prosa que MENCIONA o trailer no corpo nao e trailer (a linha nao comeca
     por `Co-Authored-By:`) e passa -- o hook nao pode impedir de documentar a
     propria regra;
  5. o git ACIONA o hook num `commit -F`: num repositorio temporario com
     `core.hooksPath` apontando para um diretorio que contem SO este hook, o
     commit com trailer e abortado e NAO cria commit; o limpo cria, e o
     `Claude-Session:` atravessa intacto;
  6. o arquivo e executavel -- git ignora hook sem +x com um `hint` e segue;
  7. dois MUTANTES do regex morrem: sem `Claude` deixa passar o caso 3a; sem
     `Anthropic` deixa passar o caso 3b. E o que prova que os dois ramos da
     alternativa sao medidos, nao decorativos -- o e-mail @anthropic.com casa o
     segundo ramo, entao um caso com Claude E anthropic na mesma linha nao
     separaria o mutante do original.

O repositorio temporario NUNCA aponta para o .githooks real: o pre-commit de la
resolve ROOT=/opt/wiki pelo proprio caminho e rodaria os gates de producao sobre
este repositorio de mentira. E o git roda sem a config global do dono
(GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1, HOME temporario).

Rodar:
    python3 tools/test_commit_msg_hook.py
"""
from __future__ import annotations

import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True  # o hook nao tem .py; sem isto sobra .pyc em tools/__pycache__

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOK = RAIZ / ".githooks" / "commit-msg"

LIMPA = "fix(x): conserta a coisa\n\nCorpo explicando por que.\n"
SESSAO = LIMPA + "\nClaude-Session: https://claude.ai/code/session_0123456789\n"
HUMANO = LIMPA + "\nCo-Authored-By: Fulano de Tal <fulano@exemplo.invalid>\n"
MODELO_CANONICO = (LIMPA
                   + "\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>\n"
                   + "Claude-Session: https://claude.ai/code/session_0123456789\n")
MODELO_MINUSCULO = LIMPA + "\nco-authored-by: claude opus 5 <noreply@anthropic.com>\n"
CLAUDE_SEM_ANTHROPIC = LIMPA + "\nCo-Authored-By: Claude <noreply@exemplo.invalid>\n"
ANTHROPIC_SEM_CLAUDE = LIMPA + "\nCo-Authored-By: Opus 5 <noreply@anthropic.com>\n"
PROSA = ("docs: explica a regra\n\n"
         "Removido o Co-Authored-By: Claude das ferramentas de commit diario.\n")


def roda_hook(hook: pathlib.Path, texto: str) -> subprocess.CompletedProcess:
    """Chama o hook como o git chama: executavel direto, com o caminho da mensagem em $1."""
    with tempfile.NamedTemporaryFile("w", suffix=".msg", delete=False, encoding="utf-8") as f:
        f.write(texto)
        caminho = f.name
    try:
        return subprocess.run([str(hook), caminho], capture_output=True, text=True, timeout=30)
    finally:
        os.unlink(caminho)


def mutante(fonte: str, de: str, para: str, destino: pathlib.Path) -> pathlib.Path:
    assert fonte.count(de) == 1, f"o regex {de!r} tem de aparecer exatamente uma vez no hook"
    destino.write_text(fonte.replace(de, para), encoding="utf-8")
    destino.chmod(destino.stat().st_mode | stat.S_IXUSR | stat.S_IRUSR)
    return destino


class HookDireto(unittest.TestCase):
    def test_hook_existe_e_e_executavel(self):
        self.assertTrue(HOOK.is_file(), HOOK)
        self.assertTrue(os.access(HOOK, os.X_OK),
                        "git ignora hook sem +x (imprime um hint e segue): o arquivo tem de ser executavel")
        self.assertTrue(HOOK.read_text(encoding="utf-8").startswith("#!/bin/bash"),
                        "shebang fixo em /bin/bash, sem env resolvido por PATH")

    def test_mensagem_limpa_passa(self):
        r = roda_hook(HOOK, LIMPA)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")

    def test_claude_session_sozinho_passa(self):
        r = roda_hook(HOOK, SESSAO)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_coautor_humano_passa(self):
        r = roda_hook(HOOK, HUMANO)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_prosa_que_menciona_o_trailer_passa(self):
        r = roda_hook(HOOK, PROSA)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_trailer_canonico_reprova_e_ensina(self):
        r = roda_hook(HOOK, MODELO_CANONICO)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("co-autoria de MODELO", r.stderr)
        self.assertIn("Co-Authored-By: Claude Fable 5.1", r.stderr, "a linha ofensora e transcrita")
        self.assertIn("nenhum commit", r.stderr)
        ultimas = [linha for linha in r.stderr.splitlines() if linha.strip()][-2:]
        self.assertTrue(any("Claude-Session" in linha for linha in ultimas),
                        f"as duas ultimas linhas (o tail -2 dos timers) tem de dizer o que FICA: {ultimas}")
        self.assertTrue(any("Remedio" in linha and "--no-verify" in linha for linha in ultimas),
                        f"...e o remedio, sem abrir a porta do --no-verify: {ultimas}")

    def test_caixa_nao_importa(self):
        self.assertEqual(roda_hook(HOOK, MODELO_MINUSCULO).returncode, 1)

    def test_3a_claude_sem_anthropic_reprova(self):
        self.assertEqual(roda_hook(HOOK, CLAUDE_SEM_ANTHROPIC).returncode, 1)

    def test_3b_anthropic_sem_claude_reprova(self):
        self.assertEqual(roda_hook(HOOK, ANTHROPIC_SEM_CLAUDE).returncode, 1)

    def test_sem_arquivo_reprova_nomeando(self):
        r = subprocess.run([str(HOOK)], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nao recebi o arquivo", r.stderr)


class Mutantes(unittest.TestCase):
    """Os dois ramos do regex sao medidos: tirar um deles deixa passar o caso que so ele pega."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="commit-msg-mutantes."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.fonte = HOOK.read_text(encoding="utf-8")

    def test_mutante_sem_claude_deixa_passar_o_caso_3a(self):
        m = mutante(self.fonte, "(Claude|Anthropic)", "(Anthropic)", self.tmp / "sem-claude")
        self.assertEqual(roda_hook(m, CLAUDE_SEM_ANTHROPIC).returncode, 0,
                         "o mutante TEM de deixar passar; se reprovou, o caso 3a nao mede o ramo Claude")
        self.assertEqual(roda_hook(m, MODELO_CANONICO).returncode, 1,
                         "o e-mail @anthropic.com ainda e pego pelo outro ramo: e por isso que o caso 3a existe")
        self.assertEqual(roda_hook(HOOK, CLAUDE_SEM_ANTHROPIC).returncode, 1, "o hook real reprova o mesmo caso")

    def test_mutante_sem_anthropic_deixa_passar_o_caso_3b(self):
        m = mutante(self.fonte, "(Claude|Anthropic)", "(Claude)", self.tmp / "sem-anthropic")
        self.assertEqual(roda_hook(m, ANTHROPIC_SEM_CLAUDE).returncode, 0,
                         "o mutante TEM de deixar passar; se reprovou, o caso 3b nao mede o ramo Anthropic")
        self.assertEqual(roda_hook(HOOK, ANTHROPIC_SEM_CLAUDE).returncode, 1, "o hook real reprova o mesmo caso")


class GitAcionaOHook(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="commit-msg-repo."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        hooks = self.tmp / "hooks-so-commit-msg"
        hooks.mkdir()
        shutil.copy2(HOOK, hooks / "commit-msg")  # copia com o +x; NUNCA o .githooks real
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(self.tmp),
            "GIT_AUTHOR_NAME": "teste", "GIT_AUTHOR_EMAIL": "teste@exemplo.invalid",
            "GIT_COMMITTER_NAME": "teste", "GIT_COMMITTER_EMAIL": "teste@exemplo.invalid",
        }
        self.assertEqual(self.git("init", "-q").returncode, 0)
        self.assertEqual(self.git("config", "core.hooksPath", str(hooks)).returncode, 0)
        (self.repo / "arquivo.txt").write_text("um\n", encoding="utf-8")
        self.assertEqual(self.git("add", "arquivo.txt").returncode, 0)

    def git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              capture_output=True, text=True, env=self.env, timeout=60)

    def commits(self) -> int:
        r = self.git("rev-list", "--count", "HEAD")
        return int(r.stdout.strip()) if r.returncode == 0 else 0

    def test_commit_F_com_trailer_e_abortado_e_o_limpo_passa(self):
        suja = self.tmp / "suja.msg"
        suja.write_text(MODELO_CANONICO, encoding="utf-8")
        r = self.git("commit", "-F", str(suja))
        self.assertNotEqual(r.returncode, 0, "commit -F com o trailer tem de abortar")
        self.assertIn("co-autoria de MODELO", r.stderr, "e a explicacao do hook chega ao operador")
        self.assertNotIn("was ignored because it's not set as executable", r.stderr)
        self.assertEqual(self.commits(), 0, "commit abortado nao pode ter criado commit")

        limpa = self.tmp / "limpa.msg"
        limpa.write_text(SESSAO, encoding="utf-8")
        r = self.git("commit", "-F", str(limpa))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.commits(), 1)
        corpo = self.git("log", "-1", "--format=%B").stdout
        self.assertIn("Claude-Session:", corpo, "o trailer de sessao atravessa intacto")
        self.assertNotIn("Co-Authored-By", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
