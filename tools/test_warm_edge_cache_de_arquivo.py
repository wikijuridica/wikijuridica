#!/usr/bin/env python3
"""`warm-edge-cache --de-arquivo` vira a lista de purga do deploy em URLs públicas
com a base do sitemap — o aquecimento dirigido pós-purga (2026-09-09) que deixou
a varredura cair de seis para duas por dia sem deixar página fria por 12 h."""
import importlib.machinery
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "warm-edge-cache")


class DeArquivo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = importlib.machinery.SourceFileLoader("warm_edge_cache", FERRAMENTA).load_module()

    def test_rotas_viram_urls_com_a_base_do_sitemap_sem_duplicata(self):
        base = self.m.urls_do_sitemap()[0].split("/")
        base = base[0] + "//" + base[2]
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("/familia/x/\n/familia/x/index.md\n# comentário\n\n/api/v1/citar/familia/x/\n/familia/x/\n"
                    + base + "/sitemap.xml\nlixo-sem-barra\n")
            caminho = f.name
        try:
            urls = self.m.urls_de_arquivo(caminho)
        finally:
            os.unlink(caminho)
        self.assertEqual(urls, [base + "/familia/x/", base + "/familia/x/index.md",
                                base + "/api/v1/citar/familia/x/", base + "/sitemap.xml"])

    def test_arquivo_vazio_faz_a_ferramenta_sair_com_2_sem_tocar_na_borda(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("# nada\n")
            caminho = f.name
        try:
            saida = subprocess.run([sys.executable, FERRAMENTA, "--de-arquivo", caminho, "--rps", "1"],
                                   cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        finally:
            os.unlink(caminho)
        self.assertEqual(saida.returncode, 2, saida.stdout + saida.stderr)
        self.assertIn("nada a aquecer", saida.stderr)

    def test_a_flag_existe_na_ajuda(self):
        saida = subprocess.run([sys.executable, FERRAMENTA, "--help"], cwd=RAIZ,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        self.assertIn("--de-arquivo", saida.stdout)


if __name__ == "__main__":
    unittest.main()
