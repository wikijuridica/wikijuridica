#!/usr/bin/env python3
"""Testes de tools/wikiuniverso.py — a fonte única do universo público.

Cada caso aqui é um defeito que a FAMÍLIA-A produziu de verdade em 2026-08-29,
não uma hipótese: o .br que estourava UnicodeDecodeError e o shard em carência
que inflava o universo em 81,6%.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikiuniverso  # noqa: E402


INDICE = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://wikijuridica.com.br/sitemaps/pages-0001.xml</loc></sitemap>
</sitemapindex>
"""

SHARD_DECLARADO = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://wikijuridica.com.br/a/</loc></url>
  <url><loc>https://wikijuridica.com.br/b/</loc></url>
</urlset>
"""

SHARD_EM_CARENCIA = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://wikijuridica.com.br/a/</loc></url>
  <url><loc>https://wikijuridica.com.br/retirada-ontem/</loc></url>
</urlset>
"""


def monta(raiz, com_br=False, com_carencia=False, shard_ausente=False):
    dir_shards = os.path.join(raiz, "public", "sitemaps")
    os.makedirs(dir_shards, exist_ok=True)
    with open(os.path.join(raiz, "public", "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(INDICE)
    if not shard_ausente:
        with open(os.path.join(dir_shards, "pages-0001.xml"), "w", encoding="utf-8") as fh:
            fh.write(SHARD_DECLARADO)
    if com_carencia:
        # Shard retirado do índice mas ainda servido: existe no disco por
        # desenho, e NÃO pode entrar no universo.
        with open(os.path.join(dir_shards, "pages-0099.xml"), "w", encoding="utf-8") as fh:
            fh.write(SHARD_EM_CARENCIA)
    if com_br:
        # A gêmea comprimida: bytes binários que fizeram o leitor ingênuo
        # estourar UnicodeDecodeError em 'utf-8' no byte 0xf1.
        with open(os.path.join(dir_shards, "pages-0001.xml.br"), "wb") as fh:
            fh.write(b"\xf1\x00\x8b\x1f dados brotli, nao XML")


class TestUniversoPublico(unittest.TestCase):
    def test_universo_vem_do_indice_e_ignora_carencia(self):
        with tempfile.TemporaryDirectory() as raiz:
            monta(raiz, com_carencia=True)
            urls = wikiuniverso.urls_publicas(raiz)
            self.assertEqual(urls, [
                "https://wikijuridica.com.br/a/",
                "https://wikijuridica.com.br/b/",
            ])
            self.assertNotIn("https://wikijuridica.com.br/retirada-ontem/", urls)

    def test_gemea_br_nao_derruba_nem_entra(self):
        with tempfile.TemporaryDirectory() as raiz:
            monta(raiz, com_br=True, com_carencia=True)
            urls = wikiuniverso.urls_publicas(raiz)  # não pode levantar
            self.assertEqual(len(urls), 2)

    def test_carencia_e_br_nao_mudam_o_universo(self):
        """O invariante que a FAMÍLIA-A quebrava: o depósito cresce, o universo não."""
        with tempfile.TemporaryDirectory() as limpo, tempfile.TemporaryDirectory() as sujo:
            monta(limpo)
            monta(sujo, com_br=True, com_carencia=True)
            self.assertEqual(wikiuniverso.urls_publicas(limpo), wikiuniverso.urls_publicas(sujo))

    def test_shard_anunciado_e_ausente_falha_alto(self):
        """404 anunciado ao crawler não pode virar silêncio."""
        with tempfile.TemporaryDirectory() as raiz:
            monta(raiz, shard_ausente=True)
            with self.assertRaises(wikiuniverso.UniversoIndisponivel):
                wikiuniverso.urls_publicas(raiz)

    def test_indice_ausente_falha_alto(self):
        with tempfile.TemporaryDirectory() as raiz:
            with self.assertRaises(wikiuniverso.UniversoIndisponivel):
                wikiuniverso.urls_publicas(raiz)

    def test_caminhos_publicos_reduzem_a_rota(self):
        with tempfile.TemporaryDirectory() as raiz:
            monta(raiz)
            self.assertEqual(wikiuniverso.caminhos_publicos(raiz), ["/a/", "/b/"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
