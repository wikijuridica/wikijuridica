#!/usr/bin/env python3
"""Prova que check-enquadramento-pequeno-porte reprova quando deve.

Um gate de conformidade que so foi visto verde nao prova nada: ele pode estar
verde porque mede certo, ou porque nao mede nada. Estes testes o montam sobre
arvores temporarias e exigem o vermelho nos dois casos em que a norma pede
reavaliacao -- com o controle positivo ao lado, que e o padrao de teste de
mutacao desta casa.

Nenhum banco de producao e tocado, e nenhuma conta e semeada em var/social: as
arvores sao temporarias e morrem com o teste.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-enquadramento-pequeno-porte")
DOCUMENTO_REAL = os.path.join(RAIZ, "docs", "politica", "ENQUADRAMENTO_PEQUENO_PORTE.md")


def monta_arvore(quantas_contas, com_documento=True):
    """Cria uma raiz temporaria com o banco e o documento que o gate espera."""
    raiz = tempfile.mkdtemp(prefix="enquadramento-")
    os.makedirs(os.path.join(raiz, "var", "social"))
    os.makedirs(os.path.join(raiz, "docs", "politica"))

    banco = sqlite3.connect(os.path.join(raiz, "var", "social", "social.db"))
    banco.execute("create table contas(id TEXT PRIMARY KEY)")
    banco.execute("create table perfis(conta_id TEXT)")
    if quantas_contas:
        banco.executemany(
            "insert into contas(id) values(?)",
            [(f"conta-de-teste-{i:07d}",) for i in range(quantas_contas)],
        )
    banco.commit()
    banco.close()

    lgpd = sqlite3.connect(os.path.join(raiz, "var", "social", "lgpd.db"))
    lgpd.execute("create table registros_acesso(id INTEGER PRIMARY KEY)")
    lgpd.commit()
    lgpd.close()

    if com_documento:
        shutil.copy(DOCUMENTO_REAL, os.path.join(raiz, "docs", "politica", "ENQUADRAMENTO_PEQUENO_PORTE.md"))
    return raiz


def roda(raiz):
    ambiente = dict(os.environ, WIKI_RAIZ=raiz)
    return subprocess.run([sys.executable, GATE], capture_output=True, text=True, env=ambiente)


class TestEnquadramento(unittest.TestCase):
    def test_operacao_pequena_passa(self):
        """CONTROLE POSITIVO: com poucos titulares o gate tem de ficar verde.

        Sem ele, um gate que reprovasse sempre passaria nos testes de reprovacao
        e ninguem notaria que ele nunca aprova nada.
        """
        raiz = monta_arvore(10)
        try:
            resultado = roda(raiz)
            self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
            self.assertIn("pass", resultado.stdout)
            self.assertIn("10 titulares", resultado.stdout)
        finally:
            shutil.rmtree(raiz)

    def test_larga_escala_exige_reavaliacao(self):
        """A MUTACAO QUE IMPORTA: cruzado o gatilho, o gate reprova.

        E o caso que o documento de enquadramento nomeia na secao 6 -- o numero
        de titulares deixar de sustentar sozinho a afirmacao de que nao ha
        tratamento em larga escala.
        """
        raiz = monta_arvore(10_000)
        try:
            resultado = roda(raiz)
            self.assertEqual(resultado.returncode, 1, "o gate aprovou operacao acima do gatilho de reavaliacao")
            self.assertIn("FALHA", resultado.stdout)
            self.assertIn("larga escala", resultado.stdout)
            self.assertIn("art. 3o, I", resultado.stdout)
        finally:
            shutil.rmtree(raiz)

    def test_faixa_de_aviso_nao_reprova_mas_avisa(self):
        """Entre o aviso e o gatilho, o gate passa E avisa.

        A faixa existe para que a reavaliacao aconteca com folga: descobrir que
        o enquadramento mudou no dia em que a ANPD pergunta e descobrir tarde.
        """
        raiz = monta_arvore(1_500)
        try:
            resultado = roda(raiz)
            self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
            self.assertIn("AVISO", resultado.stdout)
            self.assertIn("1500 titulares", resultado.stdout)
        finally:
            shutil.rmtree(raiz)

    def test_sem_documento_reprova(self):
        """Sem o registro escrito, os quinze dias do art. 5o nao bastam.

        O prazo e para ENTREGAR a comprovacao, nao para produzi-la do zero.
        """
        raiz = monta_arvore(0, com_documento=False)
        try:
            resultado = roda(raiz)
            self.assertEqual(resultado.returncode, 1)
            self.assertIn("quinze dias", resultado.stdout)
        finally:
            shutil.rmtree(raiz)

    def test_banco_ausente_nao_e_falha(self):
        """Banco que ainda nao existe e estado legitimo, nao defeito.

        Gate cronicamente vermelho por motivo que nao e o dele e gate que
        ninguem le -- e a proxima falha de verdade passa junto.
        """
        raiz = tempfile.mkdtemp(prefix="enquadramento-vazio-")
        try:
            os.makedirs(os.path.join(raiz, "docs", "politica"))
            shutil.copy(DOCUMENTO_REAL, os.path.join(raiz, "docs", "politica", "ENQUADRAMENTO_PEQUENO_PORTE.md"))
            resultado = roda(raiz)
            self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
            self.assertIn("banco ausente", resultado.stdout)
        finally:
            shutil.rmtree(raiz)


if __name__ == "__main__":
    unittest.main()
