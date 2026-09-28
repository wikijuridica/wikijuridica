#!/usr/bin/env python3
"""Bancada de block-display-zero-social.sh.

A guarda protege a sessao grafica do titular, onde roda a VM com PJe/e-SAJ e o
token de assinatura. Ela so vale enquanto for CRIVEL: guarda que barra comando
inocente ensina a contorna-la, e guarda contornada nao protege nada.

Por isso o controle negativo aqui pesa tanto quanto a deteccao. Os dois casos
marcados FALSO POSITIVO MEDIDO sao reais, de 2026-09-16.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block-display-zero-social.sh"
RAIZ = Path(__file__).resolve().parent.parent.parent


def roda(comando: str) -> int:
    """Devolve o exit code do hook para um comando Bash."""
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}})
    proc = subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
        env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(RAIZ), "HOME": str(Path.home())},
    )
    return proc.returncode


class TesteBloqueia(unittest.TestCase):
    """O que alcanca a sessao grafica do titular."""

    def test_xdotool_no_display_zero(self):
        self.assertEqual(roda("DISPLAY=:0 xdotool key ctrl+s"), 2)

    def test_scrot_da_tela_cheia(self):
        self.assertEqual(roda("DISPLAY=:0.0 scrot /tmp/tela.png"), 2)

    def test_virt_viewer_com_display_explicito(self):
        self.assertEqual(roda("virt-viewer --display :0 --attach pje"), 2)

    def test_import_do_imagemagick_em_posicao_de_comando(self):
        """`import` do ImageMagick captura tela — continua barrado."""
        self.assertEqual(roda("DISPLAY=:0 import -window root /tmp/x.png"), 2)

    def test_chromium_apontado_para_zero(self):
        self.assertEqual(roda("DISPLAY=:0 chromium --headless=new https://exemplo"), 2)

    def test_depois_de_separador_de_comando(self):
        self.assertEqual(roda("cd /opt/wiki && DISPLAY=:0 wmctrl -c janela"), 2)

    def test_com_prefixo_transparente(self):
        self.assertEqual(roda("env DISPLAY=:0 nohup firefox about:blank"), 2)

    def test_caminho_absoluto_da_ferramenta(self):
        self.assertEqual(roda("DISPLAY=:0 /usr/bin/xdotool type senha"), 2)


class TesteControleNegativo(unittest.TestCase):
    """O que a guarda NAO pode barrar. Os dois primeiros sao defeitos medidos."""

    def test_import_de_python_nao_e_captura_de_tela(self):
        """FALSO POSITIVO MEDIDO (2026-09-16).

        A versao anterior casava `import` por substring, entao todo script
        Python era classificado como "dirige entrada". Junto com o `:0` casado
        em qualquer posicao, barrava um `python3` que so reescrevia texto.
        """
        comando = (
            "python3 - <<'PY'\n"
            "import pathlib, re\n"
            "p = pathlib.Path('CLAUDE.md')\n"
            "s = p.read_text()\n"
            "s = s.replace('use :99, nunca :0, que tem a VM', 'use :99')\n"
            "p.write_text(s)\n"
            "PY"
        )
        self.assertEqual(roda(comando), 0)

    def test_dois_pontos_zero_dentro_de_prosa_nao_dispara(self):
        """FALSO POSITIVO MEDIDO: documentar a regra citava `:0` e era barrado."""
        self.assertEqual(
            roda("echo 'o display do agente e :99, nunca :0, que tem o token' >> docs/x.md"), 0
        )

    def test_hora_com_dois_pontos_zero(self):
        self.assertEqual(roda("journalctl --since today | grep '12:04:53'"), 0)

    def test_fatia_de_python(self):
        self.assertEqual(roda("python3 -c \"print('abc'[:0])\""), 0)

    def test_display_99_do_agente(self):
        self.assertEqual(roda("DISPLAY=:99 chromium --headless=new https://exemplo"), 0)

    def test_wrapper_sancionado_passa(self):
        self.assertEqual(roda("./tools/publicar-perfis-sociais --rede facebook --todas"), 0)

    def test_diagnostico_que_nao_dirige_entrada(self):
        self.assertEqual(roda("DISPLAY=:0 xdpyinfo | head -5"), 0)

    def test_git_grep_por_texto_com_display(self):
        self.assertEqual(roda("git grep -n 'DISPLAY=:0' -- docs/"), 0)


class TesteMutacao(unittest.TestCase):
    """Se o predicado for desligado, estes casos denunciam."""

    def test_o_caso_que_a_guarda_existe_para_pegar_continua_pegando(self):
        perigosos = [
            "DISPLAY=:0 xdotool key ctrl+shift+s",
            "DISPLAY=:0.0 import -window root /tmp/a.png",
            "virt-viewer --display :0 --attach vm-pje",
        ]
        for c in perigosos:
            with self.subTest(comando=c):
                self.assertEqual(roda(c), 2, f"deixou passar: {c}")


if __name__ == "__main__":
    if not HOOK.is_file():
        print(f"hook ausente: {HOOK}", file=sys.stderr)
        sys.exit(2)
    unittest.main(verbosity=2)
