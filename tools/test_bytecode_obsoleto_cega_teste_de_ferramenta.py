#!/usr/bin/env python3
"""Trava o teste cego que quase fez consertar código correto (2026-09-05).

O DEFEITO. Os 49 testes de `tools/test_*.py` carregam a ferramenta sob teste
com `importlib.machinery.SourceFileLoader`. As ferramentas de `tools/` não têm
extensão `.py`, e o CPython ainda grava bytecode para elas — hoje há 171 desses
`.pyc` em `tools/__pycache__/`, com nome degenerado
(`generate-...-censuscpython-311.pyc`, sem o ponto).

`SourceFileLoader` revalida esse bytecode por (mtime em segundos, tamanho em
bytes). Uma edição que PERMUTA linhas preserva o tamanho; se a gravação cair no
mesmo segundo da anterior, o par bate e o loader executa o bytecode ANTIGO
enquanto `inspect.getsource` devolve o arquivo NOVO. O teste então reprova
código correto, ou — pior — aprova código quebrado.

COMO ISSO APARECEU. Numa prova por mutação de
`tools/generate-writing-queue-blocker-census`: a mutação inverteu duas linhas de
precedência (tamanho idêntico), o teste reprovou como devia, o arquivo foi
restaurado byte a byte e o teste CONTINUOU reprovando. `diff` dizia idêntico ao
original. Aceitar aquele vermelho como veredito teria levado a "corrigir" a
precedência que já estava certa.

A DEFESA é `PYTHONDONTWRITEBYTECODE=1` no runner que executa a suíte Python de
`tools/`: sem `.pyc` gravado não há `.pyc` obsoleto para revalidar. Este teste
cobra as duas pontas — que o defeito é real sem a defesa, e que a defesa o
elimina — porque uma defesa que ninguém prova é uma linha que a próxima limpeza
apaga.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RUNNER = RAIZ / "tools" / "run-qualidade-diaria"

FERRAMENTA_A = "def veredito():\n    return 'ANTES'\n"
# Mesmo tamanho em bytes, comportamento diferente: é a forma exata da mutação
# que enganou o loader — permutação, não crescimento.
FERRAMENTA_B = "def veredito():\n    return 'APOS_'\n"


def _carrega(caminho: pathlib.Path, nome: str):
    loader = importlib.machinery.SourceFileLoader(nome, str(caminho))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class TestBytecodeObsoleto(unittest.TestCase):
    def test_a_mutacao_de_mesmo_tamanho_e_mesmo_mtime_e_invisivel(self):
        """O defeito, reproduzido: o loader executa bytecode que não existe mais."""
        self.assertEqual(len(FERRAMENTA_A), len(FERRAMENTA_B),
                         "a reprodução exige tamanho idêntico")
        with tempfile.TemporaryDirectory() as tmp:
            alvo = pathlib.Path(tmp) / "ferramenta-sem-extensao"
            alvo.write_text(FERRAMENTA_A, encoding="utf-8")
            marca = alvo.stat().st_mtime

            escrevia = sys.dont_write_bytecode
            sys.dont_write_bytecode = False
            try:
                self.assertEqual(_carrega(alvo, "alvo_cego").veredito(), "ANTES")
                pyc = list((pathlib.Path(tmp) / "__pycache__").glob("*"))
                self.assertTrue(pyc, "o CPython gravou bytecode para arquivo sem .py")

                alvo.write_text(FERRAMENTA_B, encoding="utf-8")
                os.utime(alvo, (marca, marca))  # o mesmo segundo, deliberado

                self.assertEqual(
                    _carrega(alvo, "alvo_cego").veredito(), "ANTES",
                    "se isto virar APOS_, o CPython passou a invalidar por hash "
                    "e a defesa no runner pode ser reavaliada — não apagada sem medir")
            finally:
                sys.dont_write_bytecode = escrevia

    def test_sem_gravar_bytecode_a_mutacao_e_vista(self):
        """A defesa: sem .pyc gravado, o loader lê a fonte e enxerga a mudança."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = pathlib.Path(tmp) / "ferramenta-sem-extensao"
            alvo.write_text(FERRAMENTA_A, encoding="utf-8")
            marca = alvo.stat().st_mtime

            escrevia = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                self.assertEqual(_carrega(alvo, "alvo_visivel").veredito(), "ANTES")
                self.assertFalse(
                    (pathlib.Path(tmp) / "__pycache__").exists(),
                    "com dont_write_bytecode nenhum .pyc pode nascer")

                alvo.write_text(FERRAMENTA_B, encoding="utf-8")
                os.utime(alvo, (marca, marca))

                self.assertEqual(_carrega(alvo, "alvo_visivel").veredito(), "APOS_")
            finally:
                sys.dont_write_bytecode = escrevia

    def test_o_runner_desliga_a_gravacao_de_bytecode(self):
        """A defesa vive no runner, e some se ninguém a cobrar."""
        fonte = RUNNER.read_text(encoding="utf-8")
        self.assertIn(
            "PYTHONDONTWRITEBYTECODE=1", fonte,
            "tools/run-qualidade-diaria precisa desligar a gravação de bytecode "
            "antes de executar a suíte Python de tools/, senão um .pyc obsoleto "
            "volta a dar veredito por código que já não existe")

    def test_o_runner_limpa_o_bytecode_degenerado_ja_no_disco(self):
        """Defesa em profundidade: não gravar não apaga o que já está lá.

        Uma execução manual de qualquer um dos 49 testes grava o .pyc de volta.
        A limpeza tem de isolar os de arquivo SEM extensão — sem o ponto antes
        de "cpython" — e poupar o cache legítimo dos módulos .py.
        """
        fonte = RUNNER.read_text(encoding="utf-8")
        self.assertIn("'*[!.]cpython-*.pyc'", fonte,
                      "o runner precisa apagar o bytecode degenerado antes da suíte")
        self.assertIn("-delete", fonte)

    def test_o_glob_da_limpeza_poupa_o_cache_legitimo(self):
        """O glob é a parte perigosa: errar apaga cache que não é o culpado."""
        import fnmatch
        degenerado = "generate-writing-queue-blocker-censuscpython-311.pyc"
        legitimo = "accessledger.cpython-311.pyc"
        padrao = "*[!.]cpython-*.pyc"
        self.assertTrue(fnmatch.fnmatch(degenerado, padrao))
        self.assertFalse(fnmatch.fnmatch(legitimo, padrao))

    def test_o_runner_e_executavel_e_valido(self):
        """Guarda barata contra a edição que quebra o script inteiro."""
        self.assertTrue(os.access(RUNNER, os.X_OK), "runner deixou de ser executável")
        verificado = subprocess.run(
            ["bash", "-n", str(RUNNER)], capture_output=True, text=True)
        self.assertEqual(verificado.returncode, 0, verificado.stderr)


if __name__ == "__main__":
    unittest.main()
