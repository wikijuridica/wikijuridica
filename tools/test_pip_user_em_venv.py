#!/usr/bin/env python3
"""Todo `pip install` dentro de venv deste repo tem de declarar PIP_USER=0.

POR QUE ESTE TESTE EXISTE (2026-09-10).

`~/.config/pip/pip.conf` desta maquina declara, com motivo escrito, que a
instalacao padrao vai para o user-site:

    [global]
    break-system-packages = true
    user = true

Fora de venv isso e a escolha do dono e esta certa. DENTRO de um venv o pip
recusa, com todas as letras:

    ERROR: Can not perform a '--user' install. User site-packages are not
    visible in this virtualenv.

Efeito medido: os QUINZE wrappers deste repo que criam venv falhavam ao
provisiona-lo, e TRES venvs estavam ausentes em silencio —
`.cache/oss-python-venv`, `.cache/python-quality-sca-venv` e
`.cache/zizmor-workflow-security-venv`. O do SCA e o ambiente de `ruff`, `mypy`,
`pip-audit` e `pip-licenses`, isto e, o ambiente do `sca-staticcheck`.

O defeito e INVISIVEL ate alguem tentar: o venv que ja existia de antes da
mudanca do pip.conf continua funcionando, e o wrapper so falha quando precisa
criar um novo. Foi `check-requirements-fixados` que o expos, ao apontar que o
pin `torch==2.12.1+cpu` de requirements-oss-install-matrix.txt resolvia para o
`2.13.0` do sistema — porque o venv que deveria servi-lo nunca fora criado.

PIP_USER=0 NAO CONTORNA A CONFIGURACAO DO DONO: afirma a intencao. Instalar no
user-site nunca e o que um venv pinado quer, e a variavel diz exatamente isso no
ponto de uso, sem tocar em nada fora do repositorio.

Uso:
    python3 tools/test_pip_user_em_venv.py
"""
from __future__ import annotations

import pathlib
import re
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTAS = RAIZ / "tools"
# `pip install` de verdade, nao mencao em comentario nem em texto de ajuda.
INSTALA = re.compile(r'^\s*(?!#)(?P<prefixo>[^\n#]*?)"\$(?:PY|PYTHON)"\s+-m\s+pip\s+install\b',
                     re.M)


def wrappers_que_instalam() -> dict:
    achados = {}
    for caminho in sorted(FERRAMENTAS.iterdir()):
        if not caminho.is_file() or caminho.suffix in {".py", ".txt", ".json", ".md"}:
            continue
        try:
            texto = caminho.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        linhas = [m.group(0).strip() for m in INSTALA.finditer(texto)]
        if linhas:
            achados[caminho.name] = linhas
    return achados


class TestPipUserEmVenv(unittest.TestCase):
    def test_todo_pip_install_de_venv_declara_pip_user_zero(self):
        """Mutacao que mata este caso: tirar `PIP_USER=0` de qualquer wrapper."""
        achados = wrappers_que_instalam()
        self.assertGreaterEqual(len(achados), 15,
                                f"a varredura encontrou {len(achados)} wrappers, "
                                f"menos que os 15 medidos — o padrao de busca "
                                f"parou de enxergar a chamada")
        sem_guarda = {nome: linhas for nome, linhas in achados.items()
                      if any("PIP_USER=0" not in linha for linha in linhas)}
        self.assertEqual(sem_guarda, {},
                         "wrapper cria venv e instala sem PIP_USER=0; com "
                         "`user = true` no pip.conf desta maquina o provisionamento "
                         "falha com \"Can not perform a '--user' install\"")

    def test_a_varredura_enxerga_a_chamada_de_verdade(self):
        """Controle negativo do INSTRUMENTO, nao do alvo.

        Sem ele, um padrao de busca que deixasse de casar devolveria conjunto
        vazio e o caso acima passaria por nao ver nada — que e a forma de falso
        verde que este repositorio mais paga.
        """
        achados = wrappers_que_instalam()
        for esperado in ("oss-install-matrix-env", "python-quality-sca-env",
                         "zizmor-workflow-security-env",
                         "generate-ptbr-morphsyntax-evidence"):
            self.assertIn(esperado, achados,
                          f"a varredura nao enxergou o pip install de {esperado}")

    def test_o_padrao_nao_casa_comentario_nem_mencao_em_texto(self):
        amostra = [
            '# "$PY" -m pip install -r req.txt   (exemplo em comentario)',
            'printf \'materialize com: <caminho>/bin/python -m pip install -r req\\n\'',
        ]
        for linha in amostra:
            self.assertIsNone(INSTALA.search(linha),
                              f"o padrao casou algo que nao e chamada: {linha!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
