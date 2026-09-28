#!/usr/bin/env python3
"""Testes de tools/check-api-catalog-usage — o veredito ("endpoint anunciado
responde 404/5xx"), não o parser do log (que é o de tools/check-access-log-bots,
já coberto por tools/test_accessledger.py).

Casos:
  1. log sem nenhuma linha 404/5xx em href anunciado    -> aprova (exit 0)
  2. href anunciado com 404 real no log                 -> reprova (exit 1)
  3. FALSO POSITIVO: 405/401/403/429 em href anunciado —
     resposta protocolarmente correta (rota só-POST
     recebendo GET, recurso OAuth exigindo credencial) —
     NÃO deve reprovar.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TOOLS_DIR, "check-api-catalog-usage")


def _load_module():
    loader = importlib.machinery.SourceFileLoader(
        "check_api_catalog_usage_under_test", SCRIPT_PATH)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _linha(status: str, path: str = "/api.md", agent: str = "curl-teste/1.0",
           addr: str = "203.0.113.10") -> str:
    return (f'{addr} - [27/Aug/2026:09:19:14 -0300] host=wikijuridica.com.br '
            f'"GET {path} HTTP/1.1" {status} 146 "{agent}" allow=0 bot_sim=- '
            f'rt=0.000 cf_ray=teste reqlen=100 ref="-" warm=false\n')


_LINKSET_DOC = {
    "linkset": [
        {"anchor": "/", "item": [{"href": "https://wikijuridica.com.br/api.md"}]},
        {"anchor": "/", "item": [{"href": "https://wikijuridica.com.br/mcp"}]},
    ]
}


class _ApiCatalogUsageTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self._tmp.name, "access.log")
        self.module = _load_module()

    def tearDown(self):
        self._tmp.cleanup()

    def _catalog_targets(self):
        return self.module.extract_catalog_targets(_LINKSET_DOC)

    def _run(self, linhas: list[str]) -> tuple[int, dict]:
        with open(self.log_path, "w", encoding="utf-8") as handle:
            handle.writelines(linhas)
        catalog_targets, item_bases = self._catalog_targets()
        resultado = self.module.analyze([self.log_path], catalog_targets, item_bases, top=10)
        aprovado = resultado["enderecos_anunciados_quebrados_total"] == 0
        return (0 if aprovado else 1), resultado


class SemLinhaQuebradaAprovaTest(_ApiCatalogUsageTestCase):
    def test_apenas_200_aprova(self):
        exit_code, resultado = self._run([_linha("200"), _linha("200", path="/mcp")])
        self.assertEqual(0, exit_code)
        self.assertEqual(0, resultado["enderecos_anunciados_quebrados_total"])


class HrefAnunciado404ReprovaTest(_ApiCatalogUsageTestCase):
    def test_404_em_href_anunciado_reprova(self):
        exit_code, resultado = self._run([
            _linha("200"), _linha("404"), _linha("404"),
        ])
        self.assertEqual(1, exit_code)
        self.assertEqual(2, resultado["enderecos_anunciados_quebrados_total"])
        self.assertEqual("/api.md", resultado["enderecos_anunciados_quebrados"][0]["path"])


class Http5xxReprovaTest(_ApiCatalogUsageTestCase):
    def test_502_em_href_anunciado_reprova(self):
        exit_code, resultado = self._run([_linha("502", path="/mcp")])
        self.assertEqual(1, exit_code)
        self.assertEqual(1, resultado["enderecos_anunciados_quebrados_total"])


class RespostaProtocolarNaoReprovaTest(_ApiCatalogUsageTestCase):
    """405 (GET num endpoint só-POST), 401/403 (recurso exigindo credencial)
    e 429 (rate limit) são respostas CORRETAS do protocolo, não "endpoint
    quebrado" — este é o teste de falso-positivo obrigatório desta classe."""

    def test_405_401_403_429_nao_contam_como_quebrado(self):
        exit_code, resultado = self._run([
            _linha("405", path="/mcp"),
            _linha("401", path="/mcp"),
            _linha("403", path="/api.md"),
            _linha("429", path="/api.md"),
        ])
        self.assertEqual(0, exit_code)
        self.assertEqual(0, resultado["enderecos_anunciados_quebrados_total"])


class InternoContaComoQuebradoTest(_ApiCatalogUsageTestCase):
    """O catálogo estar quebrado não deixa de ser verdade porque quem
    tropeçou foi uma sonda interna deste repositório — precedente medido em
    2026-08-27 (o próprio check-superficie-bots-live apanhou /api.md 404)."""

    def test_404_de_sonda_interna_tambem_reprova(self):
        exit_code, resultado = self._run([
            _linha("404", agent="wikijuridica-superficie-probe/1.0"),
        ])
        self.assertEqual(1, exit_code)
        self.assertTrue(resultado["enderecos_anunciados_quebrados"][0]["interno_ou_sonda"])


if __name__ == "__main__":
    unittest.main()
