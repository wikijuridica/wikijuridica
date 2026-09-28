#!/usr/bin/env python3
"""Prova por MUTAÇÃO que `check-social-temas-espelhados` reprova quando uma página
publicada não tem tema espelhado — que foi o defeito medido em 2026-09-10 (898
páginas sem tema, 1.161 requisições de GPTBot e PerplexityBot em 404).

Um gate que só sabe dizer "verde" não é guarda: cada caso abaixo mexe UMA coisa e
exige que o veredito mude por causa dela.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-social-temas-espelhados")


def escreve_manifesto(caminho, rotas):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for rota in rotas:
            arquivo.write(json.dumps({"path": rota, "unique_intent_id": rota}, ensure_ascii=False) + "\n")


def escreve_banco(caminho, caminhos):
    conexao = sqlite3.connect(caminho)
    conexao.execute("CREATE TABLE temas (id INTEGER PRIMARY KEY, area TEXT, slug TEXT, titulo TEXT, caminho TEXT)")
    for rota in caminhos:
        partes = rota.strip("/").split("/")
        conexao.execute("INSERT INTO temas (area, slug, titulo, caminho) VALUES (?,?,?,?)",
                        (partes[0], partes[1], "titulo", rota))
    conexao.commit()
    conexao.close()


def roda(manifesto, banco, extra=()):
    return subprocess.run([sys.executable, GATE, "--manifesto", manifesto, "--banco", banco, *extra],
                          cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)


class Espelho(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.manifesto = os.path.join(self.dir, "published_manifest.jsonl")
        self.banco = os.path.join(self.dir, "social.db")

    def test_espelho_completo_passa(self):
        rotas = ["/familia/x/", "/jurisprudencia/stj-tema-910/"]
        escreve_manifesto(self.manifesto, rotas)
        escreve_banco(self.banco, rotas)
        saida = roda(self.manifesto, self.banco)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("FALTANDO tema                    : 0", saida.stdout)

    def test_pagina_sem_tema_reprova_e_nomeia_a_rota(self):
        # A MUTAÇÃO: o caso real de 2026-09-10 — a página está publicada, o HTML
        # dela anuncia /redesocial/tema/..., e o tema não existe.
        escreve_manifesto(self.manifesto, ["/familia/x/", "/jurisprudencia/stj-tema-910/"])
        escreve_banco(self.banco, ["/familia/x/"])
        saida = roda(self.manifesto, self.banco)
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("/jurisprudencia/stj-tema-910/", saida.stdout)
        self.assertIn("/redesocial/tema/jurisprudencia/stj-tema-910/", saida.stdout)
        self.assertIn("generate-social-temas --aplicar", saida.stderr)

    def test_tema_orfao_nao_reprova_e_e_relatado(self):
        # Página supersedida sai do manifesto e o tema fica, com as respostas e os
        # follows dele. Reprovar aqui empurraria para apagar conteúdo.
        escreve_manifesto(self.manifesto, ["/familia/x/"])
        escreve_banco(self.banco, ["/familia/x/", "/familia/retirada/"])
        saida = roda(self.manifesto, self.banco)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("orfaos (tema sem pagina)         : 1", saida.stdout)
        self.assertIn("nunca removidos", saida.stdout)

    def test_hub_e_paginacao_nao_exigem_tema(self):
        # Só /área/slug/ vira tema; /área/pagina/2/ e a raiz não.
        escreve_manifesto(self.manifesto, ["/familia/x/", "/familia/pagina/2/", "/", "/glossario/"])
        escreve_banco(self.banco, ["/familia/x/"])
        saida = roda(self.manifesto, self.banco)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("paginas /area/slug/ no manifesto : 1", saida.stdout)

    def test_json_traz_os_numeros(self):
        escreve_manifesto(self.manifesto, ["/familia/x/", "/familia/y/"])
        escreve_banco(self.banco, ["/familia/x/"])
        saida = roda(self.manifesto, self.banco, ("--json",))
        self.assertEqual(saida.returncode, 1)
        dados = json.loads(saida.stdout)
        self.assertEqual(dados["paginas_no_manifesto"], 2)
        self.assertEqual(dados["temas_no_banco"], 1)
        self.assertEqual(dados["faltantes"], 1)
        self.assertEqual(dados["amostra"], ["/familia/y/"])

    def test_infra_ausente_sai_com_2_e_nao_e_veredito(self):
        escreve_manifesto(self.manifesto, ["/familia/x/"])
        saida = roda(self.manifesto, os.path.join(self.dir, "nao-existe.db"))
        self.assertEqual(saida.returncode, 2, saida.stdout + saida.stderr)
        self.assertIn("banco social ausente", saida.stderr)

    def test_gate_nao_escreve_no_banco(self):
        # check-* é read-only por contrato: abre em mode=ro.
        rotas = ["/familia/x/"]
        escreve_manifesto(self.manifesto, rotas)
        escreve_banco(self.banco, rotas)
        antes = os.stat(self.banco).st_mtime_ns
        roda(self.manifesto, self.banco)
        self.assertEqual(os.stat(self.banco).st_mtime_ns, antes)


if __name__ == "__main__":
    unittest.main()
