#!/usr/bin/env python3
"""Testes de tools/check-superficie-bots-live — o veredito (esperado × obtido
por camada), não a sonda de rede. `avaliar_divergencias` é uma função pura:
os testes fabricam `linhas` já coletadas (sem tocar rede) e conferem o corte.

Casos:
  1. tudo bate com o esperado                        -> aprova
  2. camada diverge de expectativa firme ("200")      -> reprova
  3. FALSO POSITIVO: "404 hoje" que hoje é 200 (ou
     qualquer drift de baseline "hoje") NÃO reprova,
     vira só aviso — é exatamente o precedente do
     /mcp/.well-known/oauth-protected-resource medido
     em 2026-08-27 (documentado "404 hoje", medido 200).
  4. "200 md" com status certo mas Content-Type errado -> reprova (armadilha
     A3: status não é prova).
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TOOLS_DIR, "check-superficie-bots-live")


def _load_module():
    loader = importlib.machinery.SourceFileLoader(
        "check_superficie_bots_live_under_test", SCRIPT_PATH)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _d(status: str, tipo: str = "text/html", bytes_: int = 100, ms: int = 5) -> dict:
    return {"status": status, "tipo": tipo, "bytes": bytes_, "ms": ms}


class TudoConformeAprovaTest(unittest.TestCase):
    def test_todas_as_camadas_batem_com_esperado(self):
        module = _load_module()
        linhas = [
            {"rota": "/", "accept": None, "achado": "M1", "esperado": "200",
             "go": _d("200"), "nginx": _d("200"), "borda": _d("200")},
            {"rota": "/nao-existe/", "accept": None, "achado": "M20", "esperado": "404",
             "go": _d("404"), "nginx": _d("404"), "borda": _d("404")},
        ]
        avaliacao = module.avaliar_divergencias(linhas, ["go", "nginx", "borda"])
        self.assertEqual([], avaliacao["divergencias"])
        self.assertEqual([], avaliacao["avisos_drift"])


class DivergenciaFirmeReprovaTest(unittest.TestCase):
    def test_nginx_404_onde_esperado_e_200_reprova(self):
        module = _load_module()
        linhas = [
            {"rota": "/api.md", "accept": None, "achado": "M14", "esperado": "200",
             "go": _d("200", tipo="text/markdown"), "nginx": _d("404"), "borda": _d("404")},
        ]
        avaliacao = module.avaliar_divergencias(linhas, ["go", "nginx", "borda"])
        self.assertEqual(2, len(avaliacao["divergencias"]))  # nginx e borda
        camadas_divergentes = {d["camada"] for d in avaliacao["divergencias"]}
        self.assertEqual({"nginx", "borda"}, camadas_divergentes)
        self.assertEqual([], avaliacao["avisos_drift"])


class BaselineHojeNaoReprovaSoAvisaTest(unittest.TestCase):
    """O precedente medido em 2026-08-27: /mcp/.well-known/oauth-protected-resource
    está documentado como '404 hoje' e a medição real deu 200 nas três camadas
    — capacidade nova, não defeito. Isto NÃO pode reprovar."""

    def test_drift_de_baseline_hoje_vira_aviso_nao_reprovacao(self):
        module = _load_module()
        linhas = [
            {"rota": "/mcp/.well-known/oauth-protected-resource", "accept": None,
             "achado": "T3.5 RFC 9728", "esperado": "404 hoje",
             "go": _d("200"), "nginx": _d("200"), "borda": _d("200")},
        ]
        avaliacao = module.avaliar_divergencias(linhas, ["go", "nginx", "borda"])
        self.assertEqual([], avaliacao["divergencias"])
        self.assertEqual(3, len(avaliacao["avisos_drift"]))


class ContentTypeErradoComStatusCertoReprovaTest(unittest.TestCase):
    """Armadilha A3 do próprio módulo: status 200 não é prova. Content-Type
    errado com status certo tem de reprovar quando o esperado exige md."""

    def test_status_200_com_content_type_html_reprova(self):
        module = _load_module()
        linhas = [
            {"rota": "/consumidor/index.md", "accept": None, "achado": "M2",
             "esperado": "200 md",
             "go": _d("200", tipo="text/markdown"),
             "nginx": _d("200", tipo="text/html")},
        ]
        avaliacao = module.avaliar_divergencias(linhas, ["go", "nginx"])
        self.assertEqual(1, len(avaliacao["divergencias"]))
        self.assertEqual("nginx", avaliacao["divergencias"][0]["camada"])


class ParseEsperadoTest(unittest.TestCase):
    def test_variantes(self):
        module = _load_module()
        self.assertEqual(
            {"hoje": False, "status_esperado": "200", "enforced": True, "precisa_markdown": False},
            module.parse_esperado("200"))
        self.assertEqual(
            {"hoje": False, "status_esperado": "200", "enforced": True, "precisa_markdown": True},
            module.parse_esperado("200 md"))
        self.assertEqual(
            {"hoje": True, "status_esperado": "404", "enforced": False, "precisa_markdown": False},
            module.parse_esperado("404 hoje"))
        self.assertEqual(
            {"hoje": True, "status_esperado": None, "enforced": False, "precisa_markdown": False},
            module.parse_esperado("html hoje"))


if __name__ == "__main__":
    unittest.main()
