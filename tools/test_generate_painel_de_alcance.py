#!/usr/bin/env python3
"""Testes de `tools/generate-painel-de-alcance`, com ledgers SINTETICOS.

Cada caso aqui cobra uma regra que este projeto pagou para aprender:

  - ausencia e' `null`, nunca zero (senao a lacuna NOSSA vira, no relatorio
    seguinte, um fato sobre o mundo);
  - as tres camadas olham o MESMO dia, senao o painel poe numeros
    incomparaveis lado a lado — que e' o erro que ele existe para nao cometer;
  - `edge_bot_agents_daily` e' CUMULATIVO dentro do dia: somar linhas conta o
    mesmo trafego varias vezes;
  - aquecimento e simulacao ficam FORA da conta e sao contados A PARTE, para
    ninguem suspeitar que a exclusao esconde volume.

Descoberto pelo passo 2c de `tools/run-qualidade-diaria` (glob `tools/test_*.py`).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
GERADOR = os.path.join(RAIZ, "tools", "generate-painel-de-alcance")


def escreve_jsonl(caminho, linhas):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")


def monta(raiz, *, edge=(), bing=(), acesso=None, dia_do_acesso="2026-09-15"):
    escreve_jsonl(os.path.join(raiz, "data", "ops", "edge_bot_agents_daily.jsonl"), edge)
    escreve_jsonl(os.path.join(raiz, "data", "ops", "bing_webmaster_daily.jsonl"), bing)
    escreve_jsonl(
        os.path.join(raiz, "data", "ops", "access", "access-%s.jsonl" % dia_do_acesso),
        acesso or [],
    )


def roda(raiz, hoje, extra=()):
    comando = [sys.executable, GERADOR, "--raiz", raiz, "--hoje", hoje, *extra]
    processo = subprocess.run(comando, capture_output=True, text=True, timeout=180)
    return processo.returncode, processo.stdout + processo.stderr


def painel_de(saida):
    return json.loads(saida)


class PainelDeAlcance(unittest.TestCase):

    def test_camada_de_citacao_sem_serie_sai_null_e_nunca_zero(self):
        """"Ainda nao medi" e "medi e nao houve" sao afirmacoes opostas."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp)
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 0, saida)
            citacao = painel_de(saida)["camadas"]["citacao"]
            self.assertIsNone(citacao["citacoes"])
            self.assertEqual(citacao["estado"], "aguarda")
            self.assertIn("collect-bing-ai-citations --login", citacao["motivo"])

    def test_as_tres_camadas_olham_o_mesmo_dia(self):
        """Borda fechada ao lado de origem de meio-dia seriam incomparaveis."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(
                tmp,
                edge=[{"date": "2026-09-15", "agent_key": "gptbot", "function": "training",
                       "requests_estimated": 10},
                      {"date": "2026-09-16", "agent_key": "gptbot", "function": "training",
                       "requests_estimated": 999}],
                acesso=[{"ts": "2026-09-15T10:00:00Z", "path": "/x", "route_class": "html"}],
            )
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 0, saida)
            painel = painel_de(saida)
            self.assertEqual(painel["dia_de_referencia"], "2026-09-15")
            self.assertEqual(painel["camadas"]["borda"]["dia"], "2026-09-15")
            self.assertEqual(painel["camadas"]["origem"]["dia"], "2026-09-15")
            # o dia corrente, parcial, NAO pode vazar para o numero da borda
            self.assertEqual(painel["camadas"]["borda"]["requisicoes_de_bot_classificadas"], 10)

    def test_ledger_da_borda_e_cumulativo_ultima_linha_do_dia_vence(self):
        """Somar as linhas contaria o mesmo trafego tres vezes."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp, edge=[
                {"date": "2026-09-15", "agent_key": "gptbot", "function": "training",
                 "requests_estimated": 100},
                {"date": "2026-09-15", "agent_key": "gptbot", "function": "training",
                 "requests_estimated": 250},
                {"date": "2026-09-15", "agent_key": "gptbot", "function": "training",
                 "requests_estimated": 400},
            ])
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 0, saida)
            borda = painel_de(saida)["camadas"]["borda"]
            self.assertEqual(borda["requisicoes_de_bot_classificadas"], 400)
            self.assertEqual(borda["requisicoes_de_agentes_de_ia"], 400)

    def test_aquecimento_e_simulacao_ficam_fora_e_sao_contados_a_parte(self):
        """Sonda que entra na metrica faz o portal medir o proprio eco."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp, acesso=[
                {"ts": "2026-09-15T01:00:00Z", "path": "/a", "route_class": "html"},
                {"ts": "2026-09-15T01:01:00Z", "path": "/b", "route_class": "html",
                 "warming": True},
                {"ts": "2026-09-15T01:02:00Z", "path": "/c", "route_class": "html",
                 "bot_simulation": True},
                {"ts": "2026-09-15T01:03:00Z", "path": "/mcp", "route_class": "mcp",
                 "mcp_method": "tools/call", "warming": True},
                {"ts": "2026-09-15T01:04:00Z", "path": "/mcp", "route_class": "mcp",
                 "mcp_method": "tools/call"},
            ])
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 0, saida)
            origem = painel_de(saida)["camadas"]["origem"]
            self.assertEqual(origem["requisicoes_reais"], 2)
            self.assertEqual(origem["trafego_proprio_excluido"], 3)
            self.assertEqual(origem["mcp_tools_call_externos"], 1)
            self.assertEqual(origem["mcp_tools_call_internos"], 1)

    def test_gemea_markdown_e_contada(self):
        """A gemea e' rota dinamica: so' a origem a ve."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp, acesso=[
                {"ts": "2026-09-15T01:00:00Z", "path": "/familia/x/index.md",
                 "route_class": "markdown"},
                {"ts": "2026-09-15T01:01:00Z", "path": "/familia/x/", "route_class": "html"},
            ])
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 0, saida)
            self.assertEqual(painel_de(saida)["camadas"]["origem"]["gemea_markdown"], 1)

    def test_citacao_com_export_e_sem_contagem_diz_fase_1(self):
        """Coleta ativa nao e' contagem: o parser so' nasce depois do cabecalho."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp, bing=[{"tipo": "citacao_ia_export", "ok": True,
                              "coletado_em": "2026-09-15T05:50:00Z"}])
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 0, saida)
            citacao = painel_de(saida)["camadas"]["citacao"]
            self.assertEqual(citacao["estado"], "coleta_ativa_sem_contagem")
            self.assertIsNone(citacao["citacoes"])
            self.assertIn("inventar esquema", citacao["motivo"])

    def test_hoje_invalido_e_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp)
            codigo, _ = roda(tmp, "15/09/2026", extra=["--stdout"])
            self.assertEqual(codigo, 2)

    def test_fonte_ilegivel_e_exit_2_nunca_painel_pela_metade(self):
        """Painel incompleto sem aviso e' pior que painel nenhum."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp)
            alvo = os.path.join(tmp, "data", "ops", "access", "access-2026-09-15.jsonl")
            os.remove(alvo)
            os.makedirs(alvo)
            codigo, saida = roda(tmp, "2026-09-16", extra=["--stdout"])
            self.assertEqual(codigo, 2, saida)
            self.assertIn("NAO GEROU", saida)

    def test_grava_e_nao_regrava_quando_o_conteudo_nao_muda(self):
        """`gerado_em` sozinho sujaria a arvore do git a cada execucao do timer."""
        with tempfile.TemporaryDirectory() as tmp:
            monta(tmp)
            codigo, _ = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 0)
            destino = os.path.join(tmp, "data", "ops", "painel", "alcance.json")
            self.assertTrue(os.path.exists(destino))
            antes = os.stat(destino).st_mtime_ns
            codigo, saida = roda(tmp, "2026-09-16")
            self.assertEqual(codigo, 0, saida)
            self.assertIn("inalterado", saida)
            self.assertEqual(os.stat(destino).st_mtime_ns, antes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
