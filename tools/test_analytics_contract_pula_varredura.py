#!/usr/bin/env python3
"""Testes do atalho de varredura de tools/check-analytics-contract.

A varredura das 10.370 páginas de public/ custava 5,1s dos 8,3s do gate e
responde uma pergunta de DEPLOY. O atalho a pula quando o commit não pode ter
mudado a resposta. Errar para o lado frouxo aqui deixa passar divergência entre
o script servido e o autorizado pela CSP — que faz o navegador bloquear a
medição em todas as páginas, em silêncio.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import unittest
from unittest import mock

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "check-analytics-contract"


def carrega():
    loader = importlib.machinery.SourceFileLoader("analytics_gate", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class AtalhoDaVarreduraTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = carrega()

    def test_o_parser_resolve_o_valor_e_nao_devolve_expressao_go(self):
        """A regressão de 2026-09-05: a regex devolvia 1.106 bytes com
        `agentsurface.SufixoGemeaMarkdown` cru dentro do JavaScript."""
        valor = self.mod.resolve_const_script(self.mod.FONTE_WEBMCP)
        self.assertNotIn("agentsurface.", valor)
        self.assertNotIn("` + ", valor)
        self.assertIn("index.md", valor, "o sufixo tem de estar RESOLVIDO")

    def test_script_inalterado_vs_head_pula(self):
        """Sem mudança no valor nem em public/, a resposta já valia."""
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="")
            with mock.patch.object(self.mod, "resolve_const_script", return_value="X"), \
                 mock.patch.object(self.mod, "corpo_do_loader", return_value="Y"):
                self.assertTrue(self.mod.script_composto_inalterado_vs_head())

    def test_public_sujo_sempre_varre(self):
        """public/ modificado é exatamente o caso em que a varredura tem de
        rodar — é a resposta dela que pode ter mudado."""
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="")
            self.assertFalse(self.mod.script_composto_inalterado_vs_head())

    def test_script_alterado_varre(self):
        """Valor diferente de HEAD: a varredura roda inteira."""
        chamadas = {"n": 0}

        def alterna(*a, **k):
            chamadas["n"] += 1
            return "ANTES" if chamadas["n"] > 1 else "AGORA"

        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="")
            with mock.patch.object(self.mod, "resolve_const_script", side_effect=alterna), \
                 mock.patch.object(self.mod, "corpo_do_loader", return_value=""):
                self.assertFalse(self.mod.script_composto_inalterado_vs_head())

    def test_erro_no_git_varre_fail_closed(self):
        """Não saber se mudou nunca pode virar 'não mudou'."""
        import subprocess
        for erro in (OSError("git sumiu"), subprocess.SubprocessError("falhou")):
            with mock.patch("subprocess.run", side_effect=erro):
                self.assertFalse(self.mod.script_composto_inalterado_vs_head(),
                                 f"{erro!r} devia mandar varrer")

    def test_parser_que_falha_varre_fail_closed(self):
        """Arquivo novo que não existe em HEAD, sintaxe que o parser não resolve:
        tudo isso manda varrer, não absolve."""
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="")
            with mock.patch.object(self.mod, "resolve_const_script",
                                   side_effect=SystemExit("nao achei a constante")):
                self.assertFalse(self.mod.script_composto_inalterado_vs_head())

    def test_o_atalho_so_vale_com_a_flag_explicita(self):
        """Sem a flag o gate varre sempre — quem chama fora do pre-commit não
        pode receber o atalho sem pedir."""
        fonte = ALVO.read_text(encoding="utf-8")
        self.assertIn('pular_se_inalterado = "--pular-public-se-inalterado" in sys.argv', fonte)
        self.assertIn("elif pular_se_inalterado and script_composto_inalterado_vs_head():", fonte)

    def test_o_pre_commit_passa_a_flag(self):
        """Se o hook perder a flag, o ganho some em silêncio."""
        hook = (RAIZ / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("check-analytics-contract\" --pular-public-se-inalterado", hook)


if __name__ == "__main__":
    unittest.main()
