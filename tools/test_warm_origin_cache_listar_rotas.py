#!/usr/bin/env python3
"""`warm-origin-cache --listar-rotas` imprime o conjunto dinâmico inteiro, sem duplicata,
sem tocar na origem — é a lista que `deploy-publico` purga na borda quando só o binário
do servidor mudou (2026-09-09). Um conjunto menor que o aquecido deixaria rota dinâmica
velha na borda por até 7 dias (`/{área}/index.md` sai com s-maxage=604800)."""
import importlib.machinery
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "warm-origin-cache")


class ListarRotas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modulo = importlib.machinery.SourceFileLoader("warm_origin_cache", FERRAMENTA).load_module()
        saida = subprocess.run([sys.executable, FERRAMENTA, "--listar-rotas"], cwd=RAIZ,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        cls.codigo = saida.returncode
        cls.linhas = saida.stdout.splitlines()
        cls.stderr = saida.stderr

    def test_sai_zero_e_imprime_uma_rota_por_linha(self):
        self.assertEqual(self.codigo, 0, self.stderr)
        self.assertTrue(self.linhas)
        for linha in self.linhas:
            self.assertTrue(linha.startswith("/"), linha)
            self.assertNotIn(" ", linha)

    def test_cobre_o_mesmo_conjunto_que_o_aquecimento_e_sem_duplicata(self):
        m = self.modulo
        esperado = list(m.DESCRITORES) + m.rotas_de_lote() + m.rotas_de_texto_integral() + m.gemeas()
        self.assertEqual(len(self.linhas), len(set(self.linhas)), "duplicata na lista")
        self.assertEqual(set(self.linhas), set(esperado))

    def test_inclui_os_indices_em_markdown_e_os_descritores(self):
        conjunto = set(self.linhas)
        self.assertIn("/index.md", conjunto)
        self.assertTrue(any(r.count("/") == 2 and r.endswith("/index.md") for r in conjunto),
                        "nenhum /{área}/index.md na lista")
        self.assertIn("/.well-known/agent-card.json", conjunto)
        # O HTML estático das páginas (/{área}/{slug}/) NÃO entra: ele mora em public/
        # e não muda por binário — é exatamente o que a purga por camada preserva.
        self.assertFalse(any(r.endswith("/") and r.count("/") == 3 for r in conjunto),
                         "rota de página HTML na lista dinâmica")


if __name__ == "__main__":
    unittest.main()
