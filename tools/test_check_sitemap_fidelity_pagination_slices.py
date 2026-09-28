#!/usr/bin/env python3
"""Prova, em árvore sintética, que fatias_de_paginacao_conhecidas() de
tools/check-sitemap-fidelity reconhece a fatia de paginação LEGÍTIMA sem
afrouxar a detecção de órfão real.

POR QUE ESTE TESTE EXISTE (medido em 2026-09-03): `./tools/check-sitemap-fidelity`
acusava 186 "HTML órfão em public/" — todas as fatias `/{area}/pagina/N/` que
o commit 02b79b52 tirou do sitemap por desenho. A causa NÃO era a aritmética
de conjuntos do gate (`conhecidas` já incluía `derivadas_todas` desde aquele
commit); era que `cmd/inspect-derived-artifacts` monta o candidato a partir do
que o SITEMAP anuncia (internal/publishedmanifest/derived_artifacts.go:152),
e as fatias saíram do sitemap — a classe "area-hub-pagination" ficou
inalcançável na prática (medido: 39 records, 0 area-hub-pagination).

A correção reconhece a fatia por ASSINATURA ESTRUTURAL do próprio artefato
(canonical autorreferente + robots index,follow + `<nav class="pagination">`),
sobre uma área JÁ VERIFICADA como hub real. Este teste prova as DUAS metades:
a fatia legítima passa a ser conhecida, E um órfão que só coincide com o
FORMATO do caminho — sem os três sinais, ou sob área que não é hub — continua
órfão. Sem a segunda metade, a "correção" seria afrouxar o gate.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import shutil
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = str(RAIZ / "tools" / "check-sitemap-fidelity")
_LOADER = SourceFileLoader("check_sitemap_fidelity_test_subject", _ALVO)
_SPEC = importlib.util.spec_from_loader("check_sitemap_fidelity_test_subject", _LOADER)
fidelidade = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(fidelidade)

BASE = "https://e.com"


def _pagina(canonical_ok=True, robots_ok=True, nav_ok=True, url_no_canonical=None):
    """Corpo HTML mínimo, com os três sinais LIGÁVEIS um a um — é o que prova
    que a exigência dos três é real, não decorativa."""
    canonical_href = url_no_canonical or "{url}"
    partes = ["<!doctype html><html lang=\"pt-BR\"><head>"]
    if canonical_ok:
        partes.append('<link rel="canonical" href="%s">' % canonical_href)
    if robots_ok:
        partes.append('<meta name="robots" content="index,follow,max-snippet:-1">')
    partes.append("</head><body>")
    if nav_ok:
        partes.append('<nav class="pagination" aria-label="Paginação da área">x</nav>')
    partes.append("</body></html>")
    return "\n".join(partes)


def _escreve(public_dir, rota_relativa, corpo):
    destino = os.path.join(public_dir, rota_relativa, "index.html")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as handle:
        # {url} vira a URL canônica REAL desta página — cada teste decide se
        # deixa correto (autorreferente) ou deliberadamente errado.
        url = BASE + "/" + rota_relativa.rstrip("/") + "/"
        handle.write(corpo.format(url=url))


class FatiasDePaginacaoTestCase(unittest.TestCase):
    def setUp(self):
        self.public_dir = tempfile.mkdtemp(prefix="check-sitemap-fidelity-pub-")

    def tearDown(self):
        shutil.rmtree(self.public_dir, ignore_errors=True)


class TestFatiaLegitimaEReconhecida(FatiasDePaginacaoTestCase):
    def test_fatia_com_os_tres_sinais_e_conhecida(self):
        _escreve(self.public_dir, "aereo/pagina/2", _pagina())
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"aereo"})
        self.assertEqual(conhecidas, {BASE + "/aereo/pagina/2/"})

    def test_varias_fatias_da_mesma_area(self):
        for n in (2, 3, 4):
            _escreve(self.public_dir, f"bancario/pagina/{n}", _pagina())
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"bancario"})
        self.assertEqual(conhecidas, {BASE + f"/bancario/pagina/{n}/" for n in (2, 3, 4)})


class TestOrfaoRealContinuaOrfao(FatiasDePaginacaoTestCase):
    """A METADE QUE PROVA QUE NÃO AFROUXOU. Cada caso aqui tem o FORMATO
    "/{area}/pagina/N/" — o mesmo que um órfão de colisão de rota teria — e
    nenhum pode ser reconhecido como fatia conhecida."""

    def test_area_fora_de_areas_com_hub_nao_e_reconhecida(self):
        # Mesmo formato de caminho de uma pagina institucional de UM segmento
        # ("aviso-legal") -- se contasse como area so pelo nome, um residuo
        # de colisao sob ela escaparia.
        _escreve(self.public_dir, "aviso-legal/pagina/2", _pagina())
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"aereo"})  # "aviso-legal" NAO esta aqui
        self.assertEqual(conhecidas, set())

    def test_sem_canonical_autorreferente_nao_e_reconhecida(self):
        _escreve(self.public_dir, "aereo/pagina/2", _pagina(canonical_ok=False))
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"aereo"})
        self.assertEqual(conhecidas, set())

    def test_canonical_apontando_para_outro_lugar_nao_e_reconhecida(self):
        _escreve(self.public_dir, "aereo/pagina/2",
                 _pagina(url_no_canonical=BASE + "/aereo/"))
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"aereo"})
        self.assertEqual(conhecidas, set())

    def test_sem_robots_indexfollow_nao_e_reconhecida(self):
        _escreve(self.public_dir, "aereo/pagina/2", _pagina(robots_ok=False))
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"aereo"})
        self.assertEqual(conhecidas, set())

    def test_sem_nav_pagination_nao_e_reconhecida(self):
        _escreve(self.public_dir, "aereo/pagina/2", _pagina(nav_ok=False))
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub={"aereo"})
        self.assertEqual(conhecidas, set())

    def test_sem_areas_com_hub_nenhuma_nunca_e_reconhecida(self):
        _escreve(self.public_dir, "aereo/pagina/2", _pagina())
        conhecidas = fidelidade.fatias_de_paginacao_conhecidas(
            self.public_dir, BASE, areas_com_hub=set())
        self.assertEqual(conhecidas, set())


class TestIntegracaoComOOrfaoDoScript(unittest.TestCase):
    """Fecha o laço com a MESMA lógica que main() usa para achar órfão: uma
    fatia legítima some da lista de órfãos quando entra em `conhecidas`; um
    órfão de verdade (formato igual, sem os sinais) continua lá."""

    def test_conhecidas_exclui_fatia_legitima_e_mantem_orfao_real(self):
        public_dir = tempfile.mkdtemp(prefix="check-sitemap-fidelity-integ-")
        try:
            _escreve(public_dir, "aereo/pagina/2", _pagina())  # legítima
            _escreve(public_dir, "aereo/pagina/99",             # órfão de verdade:
                     _pagina(canonical_ok=False))               # mesmo formato, sem sinal
            fatias = fidelidade.fatias_de_paginacao_conhecidas(
                public_dir, BASE, areas_com_hub={"aereo"})
            conhecidas = {BASE + "/"} | fatias  # simula o resto de `conhecidas` no script real

            orfas = set()
            for raiz, _, arquivos in os.walk(public_dir):
                if "index.html" not in arquivos:
                    continue
                relativo = os.path.relpath(raiz, public_dir)
                rota = "/" if relativo == "." else "/" + relativo.replace(os.sep, "/").strip("/") + "/"
                url = BASE + rota
                if url not in conhecidas:
                    orfas.add(url)

            self.assertNotIn(BASE + "/aereo/pagina/2/", orfas, "fatia legítima não pode ficar órfã")
            self.assertIn(BASE + "/aereo/pagina/99/", orfas, "órfão real tem de continuar reprovando")
        finally:
            shutil.rmtree(public_dir, ignore_errors=True)


def main() -> int:
    import sys
    import unittest as _unittest
    runner = _unittest.TextTestRunner(verbosity=2)
    suite = _unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    resultado = runner.run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
