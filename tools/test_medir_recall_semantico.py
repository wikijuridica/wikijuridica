#!/usr/bin/env python3
"""Testes de tools/medir-recall-semantico: carga do indice (ultimo vence), metricas e amostra."""
import importlib.machinery
import importlib.util
import json
import os
import struct
import tempfile
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
loader = importlib.machinery.SourceFileLoader("medir_recall_semantico", os.path.join(RAIZ, "tools", "medir-recall-semantico"))
spec = importlib.util.spec_from_loader("medir_recall_semantico", loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)


def grava_indice(dir_indice, registros):
    """registros: lista de (path, vetor). Grava vetores.f32 + indice.jsonl como o cerebro."""
    os.makedirs(dir_indice, exist_ok=True)
    offset = 0
    with open(os.path.join(dir_indice, "vetores.f32"), "wb") as fv, open(os.path.join(dir_indice, "indice.jsonl"), "w") as fi:
        for path, vetor in registros:
            fv.write(struct.pack("<%df" % len(vetor), *vetor))
            fi.write(json.dumps({"path": path, "sha256_texto": "h", "modelo": "m", "dim": len(vetor), "offset": offset}) + "\n")
            offset += len(vetor)


class TestIndice(unittest.TestCase):
    def test_ultimo_registro_por_caminho_vence_e_normaliza(self):
        with tempfile.TemporaryDirectory() as d:
            grava_indice(d, [("/a/", [2, 0, 0]), ("/b/", [0, 3, 0]), ("/a/", [0, 0, 5])])
            caminhos, matriz, dim, modelo = mod.carrega_indice(d)
            self.assertEqual(caminhos, ["/a/", "/b/"])
            self.assertEqual((dim, modelo), (3, "m"))
            np.testing.assert_allclose(matriz[0], [0, 0, 1])
            np.testing.assert_allclose(np.linalg.norm(matriz, axis=1), [1, 1])

    def test_registro_alem_do_arquivo_e_erro(self):
        with tempfile.TemporaryDirectory() as d:
            grava_indice(d, [("/a/", [1, 0])])
            with open(os.path.join(d, "indice.jsonl"), "a") as f:
                f.write(json.dumps({"path": "/orfao/", "modelo": "m", "dim": 2, "offset": 2}) + "\n")
            with self.assertRaises(SystemExit):
                mod.carrega_indice(d)


class TestMetricas(unittest.TestCase):
    def test_posicoes_semanticas_e_metricas(self):
        caminhos = ["/a/", "/b/", "/c/"]
        matriz = np.eye(3, dtype=np.float32)
        consultas = np.array([[0.9, 0.1, 0], [0.1, 0.2, 0.9], [0, 1, 0]], dtype=np.float32)
        pos = mod.posicoes_semanticas(matriz, caminhos, consultas, ["/a/", "/a/", "/b/"], 10)
        self.assertEqual(pos, [1, 3, 1])
        m = mod.metricas(pos, 10)
        self.assertEqual(m["consultas"], 3)
        self.assertAlmostEqual(m["recall_at_1"], 2 / 3, places=4)
        self.assertAlmostEqual(m["recall_at_5"], 1.0)
        self.assertAlmostEqual(m["mrr"], (1 + 1 / 3 + 1) / 3, places=4)

    def test_metricas_ignoram_erros_mas_os_contam(self):
        m = mod.metricas([1, None, ("erro", "x")], 10)
        self.assertEqual((m["consultas"], m["erros"]), (2, 1))
        self.assertAlmostEqual(m["recall_at_10"], 0.5)
        self.assertAlmostEqual(m["mrr"], 0.5)
        self.assertEqual(mod.metricas([("erro", "x")], 10), {"consultas": 0})

    def test_amostra_por_passo_e_deterministica_e_cobre_o_conjunto(self):
        chaves = [f"/p{i:03d}/" for i in range(100)]
        a = mod.amostra_por_passo(chaves, 10, 20260908)
        b = mod.amostra_por_passo(chaves, 10, 20260908)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 10)
        self.assertEqual(len(set(a)), 10)
        self.assertNotEqual(a, chaves[:10], "prefixo conveniente nao e amostra")
        self.assertEqual(mod.amostra_por_passo(chaves[:5], 10, 1), sorted(chaves[:5]))


if __name__ == "__main__":
    unittest.main()
