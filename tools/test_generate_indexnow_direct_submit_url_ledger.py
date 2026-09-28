#!/usr/bin/env python3
"""Prova, com a resposta HTTP SIMULADA (nenhuma requisição real a
api.indexnow.org), que generate-indexnow-direct-submit grava
`data/ops/indexnow_url_state.jsonl` — uma linha por URL por lote realmente
POSTado, com endpoint e http_status — e que ela cobre TANTO a submissão
direta quanto a incremental, porque a incremental sempre delega o POST a
este mesmo script (nunca fala com a API por conta própria).

POR QUE ESTE LEDGER EXISTE (medido em 2026-09-03): `indexnow_submission_state.json`
tinha 10.177 URLs e só 3.374 com `submitted_at` — as outras 6.803 carregavam
só a semente de 12/08, que o próprio `seed_note` diz não afirmar submissão.
Mesmo as 3.374 não guardavam ENDPOINT (agregador/bing/yandex). O objetivo:
responder "esta URL já foi submetida alguma vez, quando e com que resposta"
por leitura direta do ledger, sem reconstrução impossível.

Este teste NÃO faz nenhuma chamada de rede: `pedir` (posse + amostra) e
`urllib.request.urlopen` (o POST) são substituídos por dublês.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = str(RAIZ / "tools" / "generate-indexnow-direct-submit")


def _carrega_modulo_fresco():
    """Cada teste carrega uma CÓPIA nova do módulo: ele guarda ROOT/SITE/...
    como constantes calculadas na importação, e monkeypatch em uma instância
    compartilhada entre testes vazaria estado (ex.: EVIDENCIA de um teste
    sendo lida por outro)."""
    loader = SourceFileLoader("generate_indexnow_direct_submit_test_subject", _ALVO)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class _RespostaFalsa:
    """Dublê de `http.client.HTTPResponse` — e ele precisa ter os MESMOS
    atributos que o objeto real, não só os que o código usava ontem.

    `headers` entrou em 2026-09-16 e o motivo merece registro: o dublê tinha
    `status` e `read()` e mais nada, então quando a ferramenta passou a ler
    `resposta.headers` (para capturar a cota que o operador declara), o
    `AttributeError` caiu no `except Exception` do laço de POST e virou
    `status = 0` — três testes ficaram vermelhos acusando "lote recusado" numa
    submissão que o dublê tinha mandado aceitar. Dublê incompleto não falha
    dizendo "faltou um atributo": falha fingindo outro defeito.
    """

    def __init__(self, status: int, corpo: bytes, headers=None):
        self.status = status
        self._corpo = corpo
        self.headers = dict(headers or {})

    def read(self):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class TestLedgerPorURL(unittest.TestCase):
    CHAVE_VALOR = "chave-de-teste-indexnow"
    BASE = "https://e.com"

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="indexnow-direct-submit-")
        os.makedirs(os.path.join(self.tmp, "content"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, "data", "ops"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, "public", "sitemaps"), exist_ok=True)

        with open(os.path.join(self.tmp, "content", "site.json"), "w", encoding="utf-8") as h:
            json.dump({"base_url": self.BASE}, h)
        with open(os.path.join(self.tmp, "data", "ops", "indexnow_key.json"), "w", encoding="utf-8") as h:
            json.dump({"key": self.CHAVE_VALOR}, h)

        self.urls = [f"{self.BASE}/{letra}/" for letra in ("a", "b", "c")]
        for letra in ("a", "b", "c"):
            destino = os.path.join(self.tmp, "public", letra)
            os.makedirs(destino, exist_ok=True)
            with open(os.path.join(destino, "index.html"), "w", encoding="utf-8") as h:
                h.write("<html>conteudo real</html>")
        with open(os.path.join(self.tmp, "public", "sitemaps", "pages-0001.xml"), "w", encoding="utf-8") as h:
            h.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in self.urls:
                h.write(f"  <url><loc>{url}</loc></url>\n")
            h.write("</urlset>\n")

        self.mod = _carrega_modulo_fresco()
        self.mod.ROOT = self.tmp
        self.mod.SITE = os.path.join(self.tmp, "content", "site.json")
        self.mod.CHAVE = os.path.join(self.tmp, "data", "ops", "indexnow_key.json")
        self.mod.EVIDENCIA = os.path.join(self.tmp, "data", "ops", "indexnow_direct_submissions.jsonl")
        self.mod.ESTADO_COMPARTILHADO = os.path.join(self.tmp, "data", "ops", "indexnow_submission_state.json")
        self.mod.REVISAO_CONTEUDO = os.path.join(self.tmp, "data", "ops", "page_content_revision.jsonl")
        self.mod.LEDGER_URL_STATE = os.path.join(self.tmp, "data", "ops", "indexnow_url_state.jsonl")

        # Dublê de `pedir`: responde 200 para a prova de posse (local_chave)
        # e para qualquer URL amostrada — nenhuma requisição de rede real.
        local_chave_esperada = f"{self.BASE}/{self.CHAVE_VALOR}.txt"

        def _pedir_falso(url, timeout=20.0):
            if url == local_chave_esperada:
                return 200, self.CHAVE_VALOR.encode()
            return 200, b"<html>viva</html>"

        self.mod.pedir = _pedir_falso

        self._urlopen_original = urllib.request.urlopen
        self._proxima_resposta = (200, b'{"ok":true}')
        # Cabeçalhos que o operador devolveria. Vazio por padrão, que é o que
        # api.indexnow.org devolve hoje segundo a evidência registrada.
        self._proximos_cabecalhos = {}

        def _urlopen_falso(_pedido, timeout=60):
            status, corpo = self._proxima_resposta
            if status >= 400:
                # HTTPError REAL (nao um dublê): e o que
                # generate-indexnow-direct-submit de fato captura em
                # `except urllib.error.HTTPError`, e `.read()` dele delega
                # para o `fp` — por isso o BytesIO.
                raise urllib.error.HTTPError(
                    _pedido.full_url, status, "erro simulado",
                    self._proximos_cabecalhos, io.BytesIO(corpo))
            return _RespostaFalsa(status, corpo, self._proximos_cabecalhos)

        urllib.request.urlopen = _urlopen_falso

    def tearDown(self):
        urllib.request.urlopen = self._urlopen_original
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _le_ledger(self):
        if not os.path.isfile(self.mod.LEDGER_URL_STATE):
            return []
        with open(self.mod.LEDGER_URL_STATE, encoding="utf-8") as h:
            return [json.loads(linha) for linha in h if linha.strip()]

    def test_lote_aceito_grava_uma_linha_por_url(self):
        self._proxima_resposta = (200, b'{"ok":true}')
        sys.argv = ["generate-indexnow-direct-submit"]
        codigo = self.mod.main()
        self.assertEqual(codigo, 0)

        linhas = self._le_ledger()
        self.assertEqual(len(linhas), len(self.urls), linhas)
        urls_no_ledger = {linha["url"] for linha in linhas}
        self.assertEqual(urls_no_ledger, set(self.urls))
        for linha in linhas:
            self.assertEqual(linha["http_status"], 200)
            self.assertEqual(linha["endpoint"], self.mod.ENDPOINT_PADRAO)
            self.assertEqual(linha["lote"], 1)
            self.assertEqual(linha["url_count"], len(self.urls))
            self.assertIn("submitted_at", linha)
            self.assertEqual(linha["schema_version"], "indexnow_url_state_v1")

    def test_lote_recusado_tambem_grava_linha(self):
        # 403 e uma resposta REAL que aconteceu — merece registro, nao
        # apagamento. Diferente do estado compartilhado, que so avanca com
        # 200/202.
        self._proxima_resposta = (403, b"SiteVerificationNotCompleted")
        sys.argv = ["generate-indexnow-direct-submit"]
        codigo = self.mod.main()
        self.assertEqual(codigo, 1)  # a submissao FALHOU, e main() reporta isso

        linhas = self._le_ledger()
        self.assertEqual(len(linhas), len(self.urls), linhas)
        for linha in linhas:
            self.assertEqual(linha["http_status"], 403)

        # E o estado compartilhado (usado pelo delta do incremental) NAO
        # avancou — só o ledger novo registra a tentativa recusada.
        if os.path.isfile(self.mod.ESTADO_COMPARTILHADO):
            with open(self.mod.ESTADO_COMPARTILHADO, encoding="utf-8") as h:
                estado = json.load(h)
            self.assertEqual(estado.get("urls", {}), {})

    def test_endpoint_nao_padrao_fica_registrado_por_url(self):
        self._proxima_resposta = (200, b'{"ok":true}')
        sys.argv = ["generate-indexnow-direct-submit", "--endpoint", "bing"]
        codigo = self.mod.main()
        self.assertEqual(codigo, 0)

        linhas = self._le_ledger()
        self.assertEqual(len(linhas), len(self.urls))
        for linha in linhas:
            self.assertEqual(linha["endpoint"], self.mod.ENDPOINTS["bing"])

    def test_de_arquivo_via_incremental_tambem_grava_no_ledger(self):
        # Simula exatamente o que generate-indexnow-incremental-submit faz:
        # chama este script com --de-arquivo apontando para um SUBCONJUNTO.
        self._proxima_resposta = (200, b'{"ok":true}')
        lista = os.path.join(self.tmp, "delta.txt")
        subconjunto = self.urls[:2]
        with open(lista, "w", encoding="utf-8") as h:
            h.write("\n".join(subconjunto) + "\n")
        sys.argv = ["generate-indexnow-direct-submit", "--de-arquivo", lista]
        codigo = self.mod.main()
        self.assertEqual(codigo, 0)

        linhas = self._le_ledger()
        self.assertEqual({linha["url"] for linha in linhas}, set(subconjunto),
                          "o ledger cobre --de-arquivo (caminho usado pelo incremental) sem código extra")

    def _le_evidencia(self):
        with open(self.mod.EVIDENCIA, encoding="utf-8") as h:
            return [json.loads(linha) for linha in h if linha.strip()]

    def test_cota_declarada_pelo_operador_vai_para_a_evidencia(self):
        """O instrumento que faltava: o teto que vale é o que o operador diz.

        Sem capturar cabeçalho, a única forma de descobrir um teto externo
        seria bater nele. A frente do DJEN mediu o caso irmão: o CNJ publica
        `X-Ratelimit-Limit: 20` na resposta, e isso não estava em documentação
        nenhuma.
        """
        self._proxima_resposta = (200, b'{"ok":true}')
        self._proximos_cabecalhos = {"X-RateLimit-Limit": "500",
                                     "X-RateLimit-Remaining": "12",
                                     "Content-Type": "application/json"}
        sys.argv = ["generate-indexnow-direct-submit"]
        self.assertEqual(self.mod.main(), 0)

        registro = self._le_evidencia()[-1]
        self.assertEqual(registro["operator_rate_limit_headers"],
                         {"X-RateLimit-Limit": "500", "X-RateLimit-Remaining": "12"},
                         "só o que é cota entra; Content-Type não é cota")

    def test_ausencia_de_cota_fica_registrada_como_ausencia(self):
        # Dicionário vazio é informação: é o que sustenta, COM medição, a
        # afirmação de que este endpoint não declara teto.
        self._proxima_resposta = (200, b'{"ok":true}')
        self._proximos_cabecalhos = {}
        sys.argv = ["generate-indexnow-direct-submit"]
        self.assertEqual(self.mod.main(), 0)
        self.assertEqual(self._le_evidencia()[-1]["operator_rate_limit_headers"], {})

    def test_429_PARA_a_execucao_em_vez_de_insistir(self):
        """429 é o único teto que a Regra 18 admite: causa externa, medida,
        dita pelo operador. Insistir depois dele transforma freio em bloqueio."""
        self._proxima_resposta = (429, b'{"errorCode":"TooManyRequests"}')
        self._proximos_cabecalhos = {"Retry-After": "3600"}
        sys.argv = ["generate-indexnow-direct-submit"]
        self.assertEqual(self.mod.main(), 1)
        registro = self._le_evidencia()[-1]
        self.assertEqual(registro["http_status"], 429)
        self.assertFalse(registro["success"])
        self.assertEqual(registro["operator_rate_limit_headers"], {"Retry-After": "3600"})

    def test_a_amostra_de_vivacidade_nao_tem_semente_fixa(self):
        """Semente fixa fazia a amostra 'aleatória' ser sempre o mesmo
        subconjunto — uma rota quebrada fora dela nunca seria conferida."""
        sementes = set()
        for _ in range(3):
            self._proxima_resposta = (200, b'{"ok":true}')
            sys.argv = ["generate-indexnow-direct-submit"]
            self.assertEqual(self.mod.main(), 0)
            sementes.add(self._le_evidencia()[-1]["liveness_sample_seed"])
        self.assertGreater(len(sementes), 1,
                           "três execuções com a mesma entrada não podem sortear igual")


def main() -> int:
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    resultado = runner.run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
