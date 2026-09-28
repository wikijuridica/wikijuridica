#!/usr/bin/env python3
"""Testes de tools/check-v2-editorial-launch-risk — o veredito, não o detector.

A lógica de detecção (padrões OAB, encoding, citação, colisão) já existia e
funcionava; o que faltava era o corte crítico/não-crítico e o exit code. Este
arquivo prova as duas pontas exigidas pelo contrato do repositório:

  1. um caso SINTÉTICO defeituoso por classe crítica reprova (exit 1);
  2. um caso de FALSO POSITIVO conhecido deste projeto (a página que NEGA
     promessa de resultado, ou usa "rascunho" em sentido jurídico legítimo)
     continua aprovando (exit 0) — é a mesma armadilha que já produziu 46
     falsos positivos neste repositório em 2026-08-04.

Isolamento: cada teste aponta WIKI_LAUNCH_RISK_PAGES_DIR/
WIKI_LAUNCH_RISK_PORTFOLIO_DIR para um diretório temporário próprio e
recarrega o módulo (as duas variáveis só são lidas na importação) — nunca
toca data/editorial/v2_pages real.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TOOLS_DIR, "check-v2-editorial-launch-risk")


def _load_module():
    loader = importlib.machinery.SourceFileLoader(
        "check_v2_editorial_launch_risk_under_test", SCRIPT_PATH)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _write_jsonl(path: str, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _base_page(intent_id: str, **overrides) -> dict:
    """Página de acervo limpa — verbete de ~360 palavras, dentro da banda,
    sem nenhum sinal crítico. overrides sobrescreve/injeta o defeito."""
    filler = ("Este texto explica a situação jurídica descrita de forma "
               "sóbria e técnica para o leitor consultar antes de decidir. ")
    opening = (filler * 15).strip()  # ~180 palavras
    page = {
        "intent_id": intent_id,
        "title": "Como resolver esta situação jurídica específica hoje",
        "meta_description": (
            "Guia sobre como resolver esta situação jurídica específica, com "
            "explicação sobre prazos, documentos e órgãos responsáveis pelo caso."),
        "h1": "Como resolver esta questão jurídica específica",
        "opening": opening,
        "sections": [
            {"heading": "O que diz a lei", "text": (filler * 15).strip()},
        ],
        "faq": [
            {"q": "Isso tem prazo?", "a": (filler * 5).strip()},
        ],
        "word_count": 360,
        "official_sources": [
            {"url": "https://www.gov.br/exemplo", "http_status": 200,
             "verified_at": "2026-08-20T00:00:00Z"},
        ],
        "internal_link_topics": ["outro-topico"],
    }
    page.update(overrides)
    return page


def _base_portfolio_row(intent_id: str, seed_suffix: str, area: str = "consumidor") -> dict:
    return {
        "intent_id": intent_id,
        "page_type": "verbete",
        "practice_area": area,
        "long_tail_query": "duvida sobre " + seed_suffix.replace("-", " "),
    }


class _IsolatedStockTestCase(unittest.TestCase):
    """Base: monta um estoque v2_pages/portfolio_v2 isolado por teste."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pages_dir = os.path.join(self._tmp.name, "v2_pages")
        self.portfolio_dir = os.path.join(self._tmp.name, "portfolio_v2")
        os.makedirs(self.pages_dir)
        os.makedirs(self.portfolio_dir)
        self._old_env = {
            "WIKI_LAUNCH_RISK_PAGES_DIR": os.environ.get("WIKI_LAUNCH_RISK_PAGES_DIR"),
            "WIKI_LAUNCH_RISK_PORTFOLIO_DIR": os.environ.get("WIKI_LAUNCH_RISK_PORTFOLIO_DIR"),
        }
        os.environ["WIKI_LAUNCH_RISK_PAGES_DIR"] = self.pages_dir
        os.environ["WIKI_LAUNCH_RISK_PORTFOLIO_DIR"] = self.portfolio_dir

    def tearDown(self):
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def analisar(self, pages: list[dict], portfolio: list[dict]):
        _write_jsonl(os.path.join(self.pages_dir, "shard-0001.jsonl"), pages)
        _write_jsonl(os.path.join(self.portfolio_dir, "shard-0001.jsonl"), portfolio)
        module = _load_module()
        report = module.analyse(worst=5)
        aprovado, criticos = module.veredito(report)
        return aprovado, criticos, report


class LimpaAprovaTest(_IsolatedStockTestCase):
    def test_estoque_limpo_aprova(self):
        pages = [_base_page("cons-duvida-fatura-errada")]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertTrue(aprovado, criticos)
        self.assertEqual({}, criticos)


class PromessaOabReprovaTest(_IsolatedStockTestCase):
    def test_promessa_na_voz_do_portal_reprova(self):
        pages = [_base_page(
            "cons-duvida-fatura-errada",
            opening="Nós garantimos que você vai ganhar a indenização em qualquer caso.")]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertFalse(aprovado)
        self.assertIn("oab_promessa_resultado", criticos)


class PromessaNegadaNaoReprovaTest(_IsolatedStockTestCase):
    """O falso positivo histórico (2026-08-04): a página que NEGA a promessa,
    ou descreve o anúncio abusivo de um terceiro, é prosa técnica correta."""

    def test_negacao_de_promessa_nao_e_critico(self):
        pages = [_base_page(
            "cons-duvida-fatura-errada",
            opening=("Desconfie de quem promete resultado garantido. Não existe "
                     "indenização certa: o Provimento OAB 205/2021 veda essa "
                     "promessa, e uma clínica que anunciou resultado garantido "
                     "pode responder por publicidade enganosa."))]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertTrue(aprovado, criticos)
        self.assertNotIn("oab_promessa_resultado", criticos)


class VocabInternoLegitimoNaoReprovaTest(_IsolatedStockTestCase):
    """"rascunho do testamento" é português jurídico correto — não é
    vocabulário de pipeline vazando, mesmo casando o token bruto."""

    def test_rascunho_juridico_legitimo_nao_e_critico(self):
        pages = [_base_page(
            "cons-duvida-fatura-errada",
            opening="Guarde uma cópia simples, rascunho ou minuta do testamento assinado.")]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertTrue(aprovado, criticos)
        self.assertNotIn("vocab_interno_confirmado", criticos)


class VocabInternoConfirmadoReprovaTest(_IsolatedStockTestCase):
    def test_vocabulario_interno_vazado_reprova(self):
        pages = [_base_page(
            "cons-duvida-fatura-errada",
            opening="Este rascunho ainda não passou pelo release gate desta casa.")]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertFalse(aprovado)
        self.assertIn("vocab_interno_confirmado", criticos)


class ColisaoDeRotaReprovaTest(_IsolatedStockTestCase):
    def test_duas_paginas_mesma_rota_reprovam(self):
        pages = [
            _base_page("consa-duvida-fatura-errada"),
            _base_page("consb-duvida-fatura-errada"),
        ]
        portfolio = [
            _base_portfolio_row("consa-duvida-fatura-errada", "duvida-fatura-errada"),
            _base_portfolio_row("consb-duvida-fatura-errada", "duvida-fatura-errada"),
        ]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertFalse(aprovado)
        self.assertIn("colisao_public_path", criticos)


class CitacaoInexistenteReprovaTest(_IsolatedStockTestCase):
    def test_artigo_acima_do_ultimo_real_reprova(self):
        pages = [_base_page(
            "cons-duvida-fatura-errada",
            opening="O art. 5000 do Código Civil trata exatamente desta hipótese.")]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertFalse(aprovado)
        self.assertIn("citation_range", criticos)


class EncodingDefeituosoReprovaTest(_IsolatedStockTestCase):
    def test_entidade_html_crua_reprova(self):
        pages = [_base_page(
            "cons-duvida-fatura-errada",
            opening="O consumidor &amp; o fornecedor devem seguir o contrato firmado.")]
        portfolio = [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")]
        aprovado, criticos, _ = self.analisar(pages, portfolio)
        self.assertFalse(aprovado)
        self.assertIn("html_entity", criticos)


class JsonInvalidoReprovaTest(_IsolatedStockTestCase):
    def test_linha_corrompida_reprova(self):
        _write_jsonl(os.path.join(self.pages_dir, "shard-0001.jsonl"),
                     [_base_page("cons-duvida-fatura-errada")])
        with open(os.path.join(self.pages_dir, "shard-0001.jsonl"), "a", encoding="utf-8") as handle:
            handle.write("{ isto nao fecha\n")
        _write_jsonl(os.path.join(self.portfolio_dir, "shard-0001.jsonl"),
                     [_base_portfolio_row("cons-duvida-fatura-errada", "duvida-fatura-errada")])
        module = _load_module()
        report = module.analyse(worst=5)
        aprovado, criticos = module.veredito(report)
        self.assertFalse(aprovado)
        self.assertIn("json_invalid", criticos)


if __name__ == "__main__":
    unittest.main()
