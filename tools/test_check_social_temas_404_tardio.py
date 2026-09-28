#!/usr/bin/env python3
"""Prova por MUTAÇÃO que `check-social-temas-404-tardio` enxerga o que o gate de
conjunto não enxerga: o 404 que JÁ aconteceu numa URL cujo tema existe hoje.

O defeito medido em 2026-09-16: manifesto 11.116 = espelho 11.116 (o gate irmão
verde) e, ainda assim, 1.194 respostas 404 sob `/redesocial/` em 7 dias — 25
delas no mesmo dia do gate verde. Cada caso abaixo mexe UMA coisa e exige que o
veredito mude por causa dela.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-social-temas-404-tardio")
HOJE = "2026-09-16"
ONTEM = "2026-09-15"


def escreve_banco(caminho, pares):
    conexao = sqlite3.connect(caminho)
    conexao.execute("CREATE TABLE temas (id INTEGER PRIMARY KEY, area TEXT, slug TEXT, titulo TEXT, caminho TEXT)")
    for area, slug in pares:
        conexao.execute("INSERT INTO temas (area, slug, titulo, caminho) VALUES (?,?,?,?)",
                        (area, slug, "titulo", "/%s/%s/" % (area, slug)))
    conexao.commit()
    conexao.close()


def escreve_acesso(dir_acesso, dia, linhas):
    with open(os.path.join(dir_acesso, "nginx-%s.jsonl" % dia), "w", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")


def acesso(rota, status=404, agente="gptbot", **extra):
    linha = {"path": rota, "status": status, "agent_key": agente,
             "bot_simulation": False, "warming": False}
    linha.update(extra)
    return linha


def roda(banco, dir_acesso, extra=()):
    return subprocess.run(
        [sys.executable, GATE, "--banco", banco, "--acesso-dir", dir_acesso, "--hoje", HOJE, *extra],
        cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)


class QuatrocentosEQuatroTardio(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.banco = os.path.join(self.dir, "social.db")
        self.acesso = os.path.join(self.dir, "access")
        os.makedirs(self.acesso)
        escreve_banco(self.banco, [("leis", "cpc-art-536"), ("familia", "guarda")])

    def test_404_de_tema_que_existe_hoje_reprova_e_nomeia(self):
        escreve_acesso(self.acesso, HOJE, [acesso("/redesocial/tema/leis/cpc-art-536/")])
        saida = roda(self.banco, self.acesso)
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("/redesocial/tema/leis/cpc-art-536/", saida.stdout)
        self.assertIn("gptbot=1", saida.stdout)
        self.assertIn("generate-social-temas --aplicar", saida.stderr)

    def test_404_de_tema_que_nao_existe_nao_e_deste_gate(self):
        """Tema ausente do espelho é o veredito do gate IRMÃO (de conjunto).

        Aqui ele não reprova de propósito: dois gates acusando o mesmo fato com
        réguas diferentes é como se perde a autoridade de ambos.
        MUTANTE: apagar o filtro `par not in temas` faz este caso reprovar.
        """
        escreve_acesso(self.acesso, HOJE, [acesso("/redesocial/tema/inexistente/qualquer/")])
        saida = roda(self.banco, self.acesso)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_fluxo_reprova_contexto_apenas_relata(self):
        """MUTANTE: contar o contexto no exit code faz este caso reprovar."""
        escreve_acesso(self.acesso, ONTEM, [acesso("/redesocial/tema/familia/guarda/")])
        saida = roda(self.banco, self.acesso)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("404 tardio no FLUXO (1 dia(s))   : 0", saida.stdout)
        self.assertIn("404 tardio no CONTEXTO (7 dias)  : 1", saida.stdout)

    def test_simulacao_de_paridade_e_aquecimento_nunca_contam(self):
        """Sonda interna e simulação de bot são tráfego NOSSO: contá-las faria o
        gate medir o próprio eco. MUTANTE: tirar o filtro reprova este caso."""
        escreve_acesso(self.acesso, HOJE, [
            acesso("/redesocial/tema/leis/cpc-art-536/", bot_simulation=True),
            acesso("/redesocial/tema/familia/guarda/", warming=True),
        ])
        saida = roda(self.banco, self.acesso)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_resposta_200_nao_e_incidente(self):
        escreve_acesso(self.acesso, HOJE, [acesso("/redesocial/tema/leis/cpc-art-536/", status=200)])
        self.assertEqual(roda(self.banco, self.acesso).returncode, 0)

    def test_json_traz_fluxo_contexto_e_agentes(self):
        escreve_acesso(self.acesso, HOJE, [
            acesso("/redesocial/tema/leis/cpc-art-536/"),
            acesso("/redesocial/tema/familia/guarda/", agente="perplexitybot"),
        ])
        escreve_acesso(self.acesso, ONTEM, [acesso("/redesocial/tema/familia/guarda/")])
        saida = roda(self.banco, self.acesso, extra=("--json",))
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        dados = json.loads(saida.stdout)
        self.assertEqual(dados["respostas_404_no_fluxo"], 2)
        self.assertEqual(dados["respostas_404_no_contexto"], 3)
        self.assertEqual(dados["agentes_no_fluxo"], {"gptbot": 1, "perplexitybot": 1})
        self.assertEqual(dados["temas_no_espelho"], 2)

    def test_dia_sem_arquivo_nao_quebra(self):
        saida = roda(self.banco, self.acesso)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    def test_infra_ausente_sai_com_2_e_nao_e_veredito(self):
        saida = roda(os.path.join(self.dir, "nao-existe.db"), self.acesso)
        self.assertEqual(saida.returncode, 2, saida.stdout + saida.stderr)
        self.assertIn("banco social ausente", saida.stderr)

    def test_gate_nao_escreve_no_banco(self):
        escreve_acesso(self.acesso, HOJE, [acesso("/redesocial/tema/leis/cpc-art-536/")])
        antes = os.stat(self.banco).st_mtime_ns, os.path.getsize(self.banco)
        roda(self.banco, self.acesso)
        self.assertEqual((os.stat(self.banco).st_mtime_ns, os.path.getsize(self.banco)), antes)


if __name__ == "__main__":
    unittest.main()
