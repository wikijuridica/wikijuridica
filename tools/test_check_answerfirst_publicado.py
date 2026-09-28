#!/usr/bin/env python3
"""Testes de tools/check-answerfirst-publicado — o veredito do piso de 40
palavras, não o debate do teto (que a própria ferramenta se recusa a
arbitrar, de propósito — ver docstring do módulo, seção VEREDITO).

Casos cobertos:
  1. acervo sintético limpo (aberturas normais)               -> aprova
  2. acervo sintético com >8% de aberturas abaixo do piso      -> reprova
  3. FALSO POSITIVO: abertura com >1 parágrafo cujo PRIMEIRO
     parágrafo é curto mas o campo inteiro não é — é exatamente
     a "armadilha de definição" que o cabeçalho do módulo documenta,
     e o piso é medido sobre o primeiro parágrafo mesmo assim (por
     definição, não por engano) — o teste prova que a contagem usa
     a unidade documentada, não conta palavras demais por acidente.
  4. pages.json ausente/corrompido                             -> exit 2
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TOOLS_DIR, "check-answerfirst-publicado")


def _load_module():
    loader = importlib.machinery.SourceFileLoader(
        "check_answerfirst_publicado_under_test", SCRIPT_PATH)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _pagina(unique_intent_id: str, summary: str) -> dict:
    return {
        "index_policy": "index",
        "status": "published",
        "unique_intent_id": unique_intent_id,
        "summary": summary,
        "body_sections": [{"title": "Qual é o prazo para isso?"}],
        "faq": [],
    }


_ABERTURA_NORMAL = (
    "Quem recebeu uma cobrança de dívida já paga pode contestar diretamente "
    "com o fornecedor, apresentando o comprovante de pagamento, e pedir a "
    "baixa imediata do débito indevido antes que ele vire negativação no "
    "cadastro de proteção ao crédito, o que evita transtorno bem maior depois.")


def _conta_palavras_teste(texto: str) -> int:
    return len(texto.split())


assert 40 <= _conta_palavras_teste(_ABERTURA_NORMAL) <= 60, (
    "abertura de referência do teste tem de estar dentro da faixa 40-60 "
    "para servir de caso 'normal' sem ambiguidade")


class _IsolatedPagesJsonTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pages_json = os.path.join(self._tmp.name, "pages.json")
        self._old = os.environ.get("WIKI_ANSWERFIRST_PAGES_JSON")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("WIKI_ANSWERFIRST_PAGES_JSON", None)
        else:
            os.environ["WIKI_ANSWERFIRST_PAGES_JSON"] = self._old
        self._tmp.cleanup()

    def medir(self, paginas: list[dict]):
        with open(self.pages_json, "w", encoding="utf-8") as handle:
            json.dump(paginas, handle, ensure_ascii=False)
        os.environ["WIKI_ANSWERFIRST_PAGES_JSON"] = self.pages_json
        module = _load_module()
        import sys as _sys
        old_argv = _sys.argv
        _sys.argv = ["check-answerfirst-publicado", "--json"]
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                exit_code = module.main()
            resultado = json.loads(buf.getvalue()) if buf.getvalue().strip() else None
        finally:
            _sys.argv = old_argv
        return exit_code, resultado


class AcervoLimpoAprovaTest(_IsolatedPagesJsonTestCase):
    def test_acervo_com_aberturas_normais_aprova(self):
        paginas = [_pagina(f"intent-{i}", _ABERTURA_NORMAL) for i in range(20)]
        exit_code, resultado = self.medir(paginas)
        self.assertEqual(0, exit_code)
        self.assertTrue(resultado["veredito"]["aprovado"])


class AcervoComPisoEstouradoReprovaTest(_IsolatedPagesJsonTestCase):
    def test_acervo_com_mais_de_8pct_abaixo_do_piso_reprova(self):
        # 20 páginas normais + 5 com abertura de 10 palavras (< piso de 40) =
        # 5/25 = 20%, bem acima da tolerância de 8%.
        curtas = [_pagina(f"curta-{i}", "Isso aqui é uma abertura muito curta e incompleta hoje.")
                  for i in range(5)]
        normais = [_pagina(f"normal-{i}", _ABERTURA_NORMAL) for i in range(20)]
        exit_code, resultado = self.medir(curtas + normais)
        self.assertEqual(1, exit_code)
        self.assertFalse(resultado["veredito"]["aprovado"])
        self.assertGreaterEqual(resultado["veredito"]["pct_abaixo_do_piso_primeiro_paragrafo"], 8.0)


class DefinicaoDoParagrafoNaoInflaFalsoPositivoTest(_IsolatedPagesJsonTestCase):
    """O campo .summary inteiro pode ter várias frases longas, mas se o
    PRIMEIRO parágrafo (antes da primeira linha em branco) já é curto, o
    piso conta esse primeiro parágrafo — não o campo inteiro. Isto não é
    bug: é a definição documentada. O teste prova que a ferramenta não
    "esconde" abertura curta atrás de um campo longo."""

    def test_primeiro_paragrafo_curto_conta_mesmo_com_campo_longo_depois(self):
        abertura_curta_depois_longa = (
            "Isso é curto.\n\n" + _ABERTURA_NORMAL + " " + _ABERTURA_NORMAL)
        paginas = [_pagina("mista-1", abertura_curta_depois_longa)]
        _, resultado = self.medir(paginas)
        self.assertEqual(1, resultado["veredito"]["abaixo_do_piso_primeiro_paragrafo"])
        # o campo inteiro (bem mais longo) não conta como abaixo do piso —
        # confirma que as duas unidades são medidas separadamente, sem
        # contaminação de uma na outra.
        self.assertEqual(0, resultado["campo_inteiro"]["abaixo_do_piso"])


class PagesJsonAusenteFalhaDeMedicaoTest(_IsolatedPagesJsonTestCase):
    def test_pages_json_ausente_retorna_exit_2(self):
        os.environ["WIKI_ANSWERFIRST_PAGES_JSON"] = os.path.join(
            self._tmp.name, "nao-existe.json")
        module = _load_module()
        # main() usa argparse.parse_args() lendo sys.argv real; chamando sem
        # --json também é válido para este caso de erro (mensagem vai a stderr).
        import sys as _sys
        old_argv = _sys.argv
        _sys.argv = ["check-answerfirst-publicado"]
        try:
            exit_code = module.main()
        finally:
            _sys.argv = old_argv
        self.assertEqual(2, exit_code)


if __name__ == "__main__":
    unittest.main()
