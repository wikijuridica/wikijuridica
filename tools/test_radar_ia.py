#!/usr/bin/env python3
"""Testes de tools/generate-radar-ia sobre fixture REAL (tools/testdata/evento_unificado/
nginx-2026-09-07.jsonl: 203 linhas do ledger do nginx, 8 delas `forged`) e as faixas
reais de data/ops/bot_ip_ranges. O radar so soma agente VERIFICADO; forjado e
aquecimento sao descontados e contados; sem faixa publicada fica a parte."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-radar-ia"
FIXTURE = RAIZ / "tools" / "testdata" / "evento_unificado" / "nginx-2026-09-07.jsonl"


def modulo():
    loader = importlib.machinery.SourceFileLoader("gri", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader("gri", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


class TesteRadar(unittest.TestCase):
    def setUp(self):
        self.m = modulo()
        self.tmp = tempfile.TemporaryDirectory()
        raiz = pathlib.Path(self.tmp.name)
        (raiz / "data" / "ops" / "access").mkdir(parents=True)
        shutil.copyfile(FIXTURE, raiz / "data" / "ops" / "access" / "nginx-2026-09-07.jsonl")
        shutil.copytree(RAIZ / "data" / "ops" / "bot_ip_ranges", raiz / "data" / "ops" / "bot_ip_ranges")
        self.raiz = raiz
        self.faixas = self.m.botagents.ler_faixas(str(raiz))

    def tearDown(self):
        self.tmp.cleanup()

    def filtro_independente(self):
        esperado = {}
        forjados = 0
        for l in open(FIXTURE, encoding="utf-8"):
            r = json.loads(l)
            if r.get("warming") or r.get("bot_simulation") or not r.get("agent_key"):
                continue
            if r.get("route_class") not in ("page", "markdown"):
                continue
            v = self.m.veredito(r, self.faixas)
            if v == "forged":
                forjados += 1
            if v != "authentic":
                continue
            esperado[r["agent_key"]] = esperado.get(r["agent_key"], 0) + 1
        return esperado, forjados

    def test_soma_so_verificados_e_conta_descontos(self):
        radar = self.m.radar_do_dia(str(self.raiz), "2026-09-07", self.faixas, {})
        esperado, forjados = self.filtro_independente()
        self.assertGreater(sum(esperado.values()), 0)
        self.assertEqual({a: v["leituras"] for a, v in radar["verificados"].items()}, esperado)
        self.assertEqual(radar["descontos"].get("forjado", 0), forjados)
        self.assertGreater(forjados, 0, "a fixture real tem linhas forged")
        for a, v in radar["verificados"].items():
            self.assertEqual(sum(x["leituras"] for x in v["areas"]), v["leituras"], a)
            self.assertLessEqual(len(v["paginas"]), self.m.TOP_PAGINAS)
            for pg in v["paginas"]:
                self.assertFalse(pg["path"].endswith("index.md"))
        self.assertNotIn("remote_addr", json.dumps(radar))

    def test_sem_faixas_ninguem_e_verificado(self):
        radar = self.m.radar_do_dia(str(self.raiz), "2026-09-07", {}, {})
        # so as linhas que o ledger ja carimbou (rede social) podem ser authentic sem faixas
        ledger_auth = sum(1 for l in open(FIXTURE, encoding="utf-8") if '"ip_verificacao": "authentic"' in l and ('"route_class": "page"' in l or '"route_class": "markdown"' in l))
        self.assertEqual(sum(v["leituras"] for v in radar["verificados"].values()), ledger_auth)
        self.assertGreater(sum(radar["nao_verificados_sem_faixa_publicada"].values()), 0)


if __name__ == "__main__":
    unittest.main()
