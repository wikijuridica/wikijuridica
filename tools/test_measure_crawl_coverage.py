#!/usr/bin/env python3
"""Testes focados para tools/measure-crawl-coverage.

Cobre dois defeitos corrigidos em 2026-09-02:

  1. `window_complete` vazava a variável da ÚLTIMA iteração do laço de coleta
     (sempre a de HOJE, quase sempre incompleta) para TODAS as linhas gravadas
     na segunda passada — inclusive dias fechados. Medido em
     measure-crawl-coverage:509 (antes da correção): `coletas[dia] = (coleta,
     truncado)` não guardava `janela_completa`, e o segundo laço lia a
     variável solta do escopo de fora, não do dia que estava processando.

  2. A segunda lane de verificação por FAIXA DE IP oficial (v3) nunca pode
     tentar expandir uma faixa grande (Googlebot publica /64 IPv6: bilhões de
     endereços por prefixo) — o teto tem que ser checado ANTES de iterar.
"""
from __future__ import annotations

import datetime
import importlib.machinery
import importlib.util
import ipaddress
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TOOL_PATH = TOOLS_DIR / "measure-crawl-coverage"
LOADER = importlib.machinery.SourceFileLoader("measure_crawl_coverage", str(TOOL_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
MCC = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = MCC
LOADER.exec_module(MCC)


class JanelaCompletaTest(unittest.TestCase):
    """`coletar_dia` devolve `window_complete` CORRETO por dia — não a última
    iteração de um laço externo. Testado direto na função, com `graphql`
    substituído para não bater na rede."""

    def setUp(self) -> None:
        self._graphql_original = MCC.graphql
        MCC.graphql = lambda headers, variaveis, consulta=MCC.CONSULTA: (
            {"httpRequestsAdaptiveGroups": []}, "")

    def tearDown(self) -> None:
        MCC.graphql = self._graphql_original

    def test_dia_fechado_e_janela_completa(self) -> None:
        ontem = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).date()
        _coleta, _truncado, erro, janela_completa = MCC.coletar_dia({}, ontem, "%teste%")
        self.assertEqual(erro, "")
        self.assertTrue(janela_completa, "dia UTC fechado (ontem) tem que vir window_complete=True")

    def test_dia_corrente_nao_e_janela_completa(self) -> None:
        hoje = datetime.datetime.now(datetime.timezone.utc).date()
        _coleta, _truncado, erro, janela_completa = MCC.coletar_dia({}, hoje, "%teste%")
        self.assertEqual(erro, "")
        self.assertFalse(janela_completa, "dia UTC em curso (hoje) tem que vir window_complete=False")

    def test_tupla_de_coletas_carrega_janela_completa_por_dia(self) -> None:
        """Reproduz a forma exata do bug: um dicionário `coletas` indexado por
        data, cada entrada com a PRÓPRIA `janela_completa` — não a variável de
        uma última iteração de um laço externo compartilhado."""
        hoje = datetime.datetime.now(datetime.timezone.utc).date()
        ontem = hoje - datetime.timedelta(days=1)
        coletas = {}
        for dia in (ontem, hoje):
            coleta, truncado, erro, janela_completa = MCC.coletar_dia({}, dia, "%teste%")
            self.assertEqual(erro, "")
            coletas[dia.isoformat()] = (coleta, truncado, janela_completa)
        self.assertEqual(len(coletas[ontem.isoformat()]), 3)
        self.assertTrue(coletas[ontem.isoformat()][2],
                        "ontem tem que preservar window_complete=True mesmo depois de hoje "
                        "ser processado por último")
        self.assertFalse(coletas[hoje.isoformat()][2])

    def test_padrao_antigo_provava_o_bug(self) -> None:
        """Reproduz o padrão ANTERIOR à correção (tupla de 2, `janela_completa`
        lida de uma variável só, fora do laço) para provar que ele produzia o
        defeito medido: o valor de HOJE (quase sempre False) sobrescrevendo o
        de ONTEM (que deveria ser True) para todo dia da segunda passada."""
        hoje = datetime.datetime.now(datetime.timezone.utc).date()
        ontem = hoje - datetime.timedelta(days=1)
        coletas_bug = {}
        janela_completa = None  # a variável única do código antigo
        for dia in (ontem, hoje):  # ordem crescente, igual ao laço real
            coleta, truncado, erro, janela_completa = MCC.coletar_dia({}, dia, "%teste%")
            self.assertEqual(erro, "")
            coletas_bug[dia.isoformat()] = (coleta, truncado)  # SEM janela_completa
        # Segunda passada do código antigo: lê a MESMA `janela_completa` de
        # fora, que agora vale o que a ÚLTIMA iteração do laço de cima gravou.
        for data_iso in sorted(coletas_bug):
            _coleta, _truncado = coletas_bug[data_iso]
            gravado_pelo_bug = bool(janela_completa)
            if data_iso == ontem.isoformat():
                self.assertFalse(gravado_pelo_bug,
                                 "o BUG gravava window_complete=False para ONTEM (falso "
                                 "negativo) porque a variável já tinha o valor de HOJE")


class EnderecosDaFaixaTest(unittest.TestCase):
    """O teto de endereços é checado por ARITMÉTICA (`num_addresses`), nunca
    por iteração de uma rede grande."""

    def test_faixa_pequena_expande(self) -> None:
        faixas = {"perplexitybot": [ipaddress.ip_network("18.97.9.96/29"),
                                    ipaddress.ip_network("107.20.236.150/32")]}
        enderecos, total = MCC.enderecos_da_faixa("perplexitybot", faixas)
        self.assertEqual(total, 9)
        self.assertIsNotNone(enderecos)
        self.assertEqual(len(enderecos), 9)
        self.assertIn("107.20.236.150", enderecos)

    def test_faixa_grande_e_pulada_sem_iterar(self) -> None:
        # Um único /64 IPv6 já teria 2**64 endereços — se `enderecos_da_faixa`
        # tentasse iterar, este teste travaria (timeout) em vez de falhar
        # rápido. Ele tem que devolver None por ARITMÉTICA, não por iteração.
        faixas = {"googlebot": [ipaddress.ip_network("2001:4860:4801::/64")]}
        enderecos, total = MCC.enderecos_da_faixa("googlebot", faixas)
        self.assertIsNone(enderecos)
        self.assertEqual(total, 2 ** 64)

    def test_agente_sem_faixa_devolve_none(self) -> None:
        enderecos, total = MCC.enderecos_da_faixa("amazonbot", {})
        self.assertIsNone(enderecos)
        self.assertEqual(total, 0)

    def test_teto_e_configuravel_e_medido(self) -> None:
        self.assertEqual(MCC.TETO_ENDERECOS_FAIXA_IP, 1024)


if __name__ == "__main__":
    unittest.main()
