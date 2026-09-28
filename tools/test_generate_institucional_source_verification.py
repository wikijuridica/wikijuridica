#!/usr/bin/env python3
"""Prova de tools/generate-institucional-source-verification: fetcher
INJETADO, nunca toca a rede — mesmo padrão de
test_generate_bot_agents_daily_ip_lane.py (importlib.machinery.SourceFileLoader,
porque o produtor não tem extensão .py).

Os três casos são o defeito medido em 2026-09-05, e o que o gerador tem de
fazer diante de cada um:

  A. GET 200 com corpo grande (o Provimento OAB 205/2021 respondeu 73.589
     bytes de verdade) -> GRAVA uma linha com sha256, bytes, http_status e
     verified_at = hoje.
  B. GET não-200 (rede fora, 404, 503...) -> NÃO grava; reporta a recusa.
  C. GET 200 com 1.783 bytes — o TAMANHO EXATO do interstitial do WAF F5 da
     raiz do Planalto, medido nesta mesma sessão -> NÃO grava; reporta que
     reconheceu o interstitial (por assinatura) ou o piso de bytes, e o
     `/fontes/planalto/` real do repositório segue sem lastro até decisão
     editorial sobre a URL citada.

Rodar: nice -n 19 python3 tools/test_generate_institucional_source_verification.py
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "generate-institucional-source-verification"

sys.path.insert(0, str(RAIZ / "tools"))
_loader = importlib.machinery.SourceFileLoader("gisv", str(ALVO))
_spec = importlib.util.spec_from_loader("gisv", _loader)
gisv = importlib.util.module_from_spec(_spec)
# O produtor usa @dataclass, que resolve anotações procurando o próprio módulo
# em sys.modules — sem este registro prévio, exec_module falha com
# "NoneType has no attribute '__dict__'" porque o módulo ainda não existe lá.
sys.modules["gisv"] = gisv
_loader.exec_module(gisv)

OAB_URL = "https://www.oab.org.br/leisnormas/legislacao/provimentos/205-2021"
PLANALTO_URL = "https://www.planalto.gov.br/"
INTERSTITIAL_REAL = (
    b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">\n<html>\n<head>\n'
    b'<title>PRESID\xcaNCIA DA REP\xdaBLICA</title>\n'
    b'<meta http-equiv="REFRESH" content="0;url=http://www.gov.br/planalto"></HEAD>\n'
    b'<BODY>\n</BODY>\n</HTML><script id="f5_cspm">(function(){var f5_cspm={};f5_cspm.go();}());</script>'
)  # 267 bytes -- assinatura idêntica ao real (1.783 no site); tamanho não importa para o teste de assinatura


class TestAvaliaResposta(unittest.TestCase):
    def test_A_corpo_grande_e_aceito(self):
        corpo = b"<html><body>" + b"Provimento CFOAB 205/2021. " * 3000 + b"</body></html>"
        self.assertGreater(len(corpo), gisv.PISO_BYTES_CONFERENCIA)
        aceita, motivo = gisv.avalia_resposta(200, corpo)
        self.assertTrue(aceita, motivo)

    def test_B_status_diferente_de_200_e_recusado(self):
        for status in (0, 404, 500, 503):
            corpo = b"x" * 100000
            aceita, motivo = gisv.avalia_resposta(status if status else None, corpo)
            self.assertFalse(aceita, f"status {status} deveria recusar: {motivo}")

    def test_C_interstitial_do_planalto_e_recusado_por_assinatura(self):
        # O CASO REAL medido em 2026-09-05: 1.783 bytes exatos.
        corpo_real_medido = INTERSTITIAL_REAL + b" " * (1783 - len(INTERSTITIAL_REAL))
        self.assertEqual(len(corpo_real_medido), 1783)
        aceita, motivo = gisv.avalia_resposta(200, corpo_real_medido)
        self.assertFalse(aceita, motivo)
        self.assertIn("interstitial", motivo)

    def test_C_corpo_abaixo_do_piso_e_recusado_mesmo_sem_a_assinatura(self):
        # Segunda rede de proteção: mesmo SEM "f5_cspm" nem "refresh", corpo
        # pequeno demais não prova nada.
        corpo_curto_sem_assinatura = b"<html><body>ok</body></html>"
        self.assertLess(len(corpo_curto_sem_assinatura), gisv.PISO_BYTES_CONFERENCIA)
        aceita, motivo = gisv.avalia_resposta(200, corpo_curto_sem_assinatura)
        self.assertFalse(aceita, motivo)
        self.assertIn("piso", motivo)

    def test_f5_cspm_sozinho_em_corpo_real_nao_e_recusado(self):
        # FALSO POSITIVO REAL, medido em 2026-09-05 nesta mesma sessão: o
        # marcador "f5_cspm" NÃO é exclusivo do interstitial — o mesmo WAF F5
        # o injeta em TODA página que serve, inclusive documento real
        # (https://www.planalto.gov.br/ccivil_03/leis/l8906.htm, 194.129 bytes,
        # contém "f5_cspm" e NÃO contém "refresh"). Um detector que usasse
        # f5_cspm como assinatura reprovaria o próprio Estatuto da OAB — por
        # isso avalia_resposta não tem essa checagem, só a de meta refresh.
        corpo_real_com_f5_cspm_sem_refresh = (
            b"<html><body>" + b"Lei federal de verdade, artigo por artigo. " * 3000 +
            b'<script id="f5_cspm">(function(){var f5_cspm={};f5_cspm.go();}());</script>'
            b"</body></html>"
        )
        self.assertIn(b"f5_cspm", corpo_real_com_f5_cspm_sem_refresh)
        self.assertNotIn(b"refresh", corpo_real_com_f5_cspm_sem_refresh.lower())
        self.assertGreater(len(corpo_real_com_f5_cspm_sem_refresh), gisv.PISO_BYTES_CONFERENCIA)
        aceita, motivo = gisv.avalia_resposta(200, corpo_real_com_f5_cspm_sem_refresh)
        self.assertTrue(aceita, motivo)

    def test_C_regressao_1783_bytes_exatos_sem_assinatura_e_recusado(self):
        # O NÚMERO EXATO do caso real (1.783 bytes), mas SEM "f5_cspm" nem
        # "refresh" — prova que quem recusa aqui é o PISO, não a assinatura.
        # Sem este teste, baixar PISO_BYTES_CONFERENCIA para menos de 1.783
        # continuaria com todos os outros testes verdes e deixaria passar
        # exatamente o interstitial que motivou o piso, caso um WAF futuro
        # pare de incluir a assinatura reconhecida.
        corpo = b"x" * 1783
        self.assertNotIn(b"refresh", corpo.lower())
        self.assertNotIn(b"f5_cspm", corpo)
        aceita, motivo = gisv.avalia_resposta(200, corpo)
        self.assertFalse(aceita, motivo)
        self.assertIn("piso", motivo)
        self.assertIn("1783", motivo)


class TestVerificarDocumentos(unittest.TestCase):
    def test_grava_so_o_que_passou_no_criterio(self):
        faltantes = {
            OAB_URL: gisv.DocumentoFaltante(documento=OAB_URL, url_original=OAB_URL,
                                             paginas={"/sobre/", "/aviso-legal/"}),
            PLANALTO_URL: gisv.DocumentoFaltante(documento=PLANALTO_URL, url_original=PLANALTO_URL,
                                                  paginas={"/fontes/planalto/"}),
        }

        def fetch_falso(url: str) -> gisv.RespostaHTTP:
            if url == OAB_URL:
                corpo = b"Provimento CFOAB 205/2021 na integra. " * 2000
                return gisv.RespostaHTTP(status=200, corpo=corpo)
            if url == PLANALTO_URL:
                corpo_real_medido = INTERSTITIAL_REAL + b" " * (1783 - len(INTERSTITIAL_REAL))
                return gisv.RespostaHTTP(status=200, corpo=corpo_real_medido)
            raise AssertionError(f"fetch chamado para URL inesperada: {url}")

        novas, recusas = gisv.verificar_documentos(faltantes, fetch_falso, hoje="2026-09-05")

        self.assertEqual(len(novas), 1)
        self.assertEqual(novas[0]["url"], OAB_URL)
        self.assertEqual(novas[0]["verified_at"], "2026-09-05")
        self.assertEqual(novas[0]["http_status"], 200)
        self.assertIn("paginas_citantes", novas[0])
        self.assertEqual(novas[0]["paginas_citantes"], ["/aviso-legal/", "/sobre/"])
        self.assertTrue(len(novas[0]["sha256"]) == 64)

        self.assertEqual(len(recusas), 1)
        chave, url, motivo = recusas[0]
        self.assertEqual(url, PLANALTO_URL)
        self.assertIn("interstitial", motivo)

    def test_erro_de_rede_nao_grava(self):
        faltantes = {
            OAB_URL: gisv.DocumentoFaltante(documento=OAB_URL, url_original=OAB_URL, paginas={"/sobre/"}),
        }

        def fetch_com_erro(url: str) -> gisv.RespostaHTTP:
            return gisv.RespostaHTTP(status=None, corpo=b"", erro="timed out")

        novas, recusas = gisv.verificar_documentos(faltantes, fetch_com_erro, hoje="2026-09-05")
        self.assertEqual(novas, [])
        self.assertEqual(len(recusas), 1)
        self.assertIn("falha de rede", recusas[0][2])

    def test_status_404_nao_grava(self):
        # O pedido do maestro nomeia os três casos por VERIFICAR_DOCUMENTOS,
        # não só por avalia_resposta: 200 grande (grava), não-200 (não grava),
        # 200 com 1.783 bytes (não grava). Este cobre o "não-200" ponta a
        # ponta, com corpo de página de erro real (pequeno, sem assinatura).
        faltantes = {
            OAB_URL: gisv.DocumentoFaltante(documento=OAB_URL, url_original=OAB_URL, paginas={"/sobre/"}),
        }

        def fetch_404(url: str) -> gisv.RespostaHTTP:
            return gisv.RespostaHTTP(status=404, corpo=b"<html>not found</html>")

        novas, recusas = gisv.verificar_documentos(faltantes, fetch_404, hoje="2026-09-05")
        self.assertEqual(novas, [])
        self.assertEqual(len(recusas), 1)
        chave, url, motivo = recusas[0]
        self.assertEqual(url, OAB_URL)
        self.assertIn("404", motivo)


class TestDocumentosFaltantes(unittest.TestCase):
    def test_so_lista_o_que_esta_fora_do_manifesto_e_sem_cobertura(self):
        paginas = [
            {"path": "/sobre/", "source_provenance": [
                {"source_url": OAB_URL, "checked_at": "2026-08-04"},
            ]},
            {"path": "/area/no-manifesto/", "source_provenance": [
                {"source_url": "https://exemplo.gov.br/x", "checked_at": "2026-08-04"},
            ]},
            {"path": "/ja-coberta/", "source_provenance": [
                {"source_url": "https://ja.gov.br/coberta", "checked_at": "2026-08-04"},
            ]},
        ]
        faltando = gisv.documentos_faltantes(
            paginas,
            rotas_manifesto={"/area/no-manifesto/"},
            cobertura={"https://ja.gov.br/coberta": "2026-07-01"},
        )
        self.assertEqual(set(faltando.keys()), {OAB_URL})
        self.assertEqual(faltando[OAB_URL].paginas, {"/sobre/"})

    def test_gerador_existe_e_e_executavel(self):
        self.assertTrue(ALVO.is_file(), ALVO)
        self.assertTrue(os.access(ALVO, os.X_OK), "gerador sem bit de execucao")


class TestEscritaAtomicaDoLedger(unittest.TestCase):
    """Fim a fim, com --seco e com escrita real, sobre um ledger sintético em
    tempdir — nunca sobre data/source-audit/ do repositório."""

    def test_seco_nao_escreve_nada(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp) / "pages.json"
            pages.write_text(json.dumps([
                {"path": "/sobre/", "source_provenance": [
                    {"source_url": OAB_URL, "checked_at": "2026-08-04"},
                ]},
            ]), encoding="utf-8")
            estoque = Path(tmp) / "estoque"
            estoque.mkdir()
            # Shard sintético com PELO MENOS um verified_at válido: a guarda
            # espelhada do gate irmão recusa (exit 2) estoque vazio, para não
            # tratar caminho errado como "acervo inteiro sem lastro" e sair
            # varrendo milhares de URLs — este teste prova o modo --seco, não
            # essa guarda (que tem cobertura própria em TestGuardaEstoqueVazio).
            (estoque / "a.jsonl").write_text(json.dumps({
                "official_sources": [{"url": "https://outra.gov.br/x", "verified_at": "2026-01-01"}],
            }) + "\n", encoding="utf-8")
            manifesto = Path(tmp) / "manifesto.jsonl"
            manifesto.write_text("", encoding="utf-8")
            ledger = Path(tmp) / "ledger.jsonl"

            import subprocess
            executado = subprocess.run(
                [sys.executable, str(ALVO), "--pages", str(pages), "--estoque", str(estoque),
                 "--manifesto", str(manifesto), "--ledger", str(ledger), "--seco"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60,
            )
            self.assertEqual(executado.returncode, 0, executado.stdout)
            self.assertFalse(ledger.exists(), "modo --seco não pode gravar nada")


class TestGuardaEstoqueVazio(unittest.TestCase):
    """Estoque vazio (ou --estoque apontando para caminho errado) tem de
    RECUSAR (exit 2), nunca tratar todo o acervo como 'sem lastro' e sair
    fazendo GET em milhares de URLs — é o "não varra o site deles" do
    contrato aplicado a este gerador."""

    def test_estoque_sem_shard_nenhum_recusa_com_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp) / "pages.json"
            pages.write_text(json.dumps([
                {"path": "/sobre/", "source_provenance": [
                    {"source_url": OAB_URL, "checked_at": "2026-08-04"},
                ]},
            ]), encoding="utf-8")
            estoque_vazio = Path(tmp) / "estoque-vazio"
            estoque_vazio.mkdir()
            manifesto = Path(tmp) / "manifesto.jsonl"
            manifesto.write_text("", encoding="utf-8")
            ledger = Path(tmp) / "ledger.jsonl"

            import subprocess
            executado = subprocess.run(
                [sys.executable, str(ALVO), "--pages", str(pages), "--estoque", str(estoque_vazio),
                 "--manifesto", str(manifesto), "--ledger", str(ledger)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60,
            )
            self.assertEqual(executado.returncode, 2, executado.stdout)
            self.assertIn("NÃO RODOU", executado.stdout)
            self.assertFalse(ledger.exists())


if __name__ == "__main__":
    unittest.main()
