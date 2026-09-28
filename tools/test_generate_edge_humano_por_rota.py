#!/usr/bin/env python3
"""Testes de tools/generate-edge-humano-por-rota — sem rede: a consulta
GraphQL e a resolução da zona são injetadas.

O que estes testes travam:
  - exclusão de scanner (prefixos do contrato e extensão .php) com o que saiu
    CONTADO em `scanners_excluidos`, nunca sumido;
  - `humano_provavel` = o path existe em content/pages.json, e só isso;
  - corte no topo de 200 depois de tirar scanner, ordenação determinística;
  - os cinco filtros de servidor e a exclusão do tráfego próprio estão na
    consulta enviada;
  - sem credencial: exit 2 e nada gravado; linha idêntica não se regrava.
"""
import datetime as dt
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-edge-humano-por-rota")


def carrega_modulo():
    loader = SourceFileLoader("generate_edge_humano_por_rota", FERRAMENTA)
    spec = importlib.util.spec_from_loader("generate_edge_humano_por_rota", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def grupo(path, count, intervalo=1.0):
    return {"count": count, "avg": {"sampleInterval": intervalo},
            "dimensions": {"clientRequestPath": path}}


def resposta(grupos):
    return {"viewer": {"zones": [{"httpRequestsAdaptiveGroups": grupos}]}}


PUBLICADOS = {"/", "/familia/divorcio-consensual/", "/leis/cc-art-393/", "/buscar/"}

GRUPOS = [
    grupo("/", 104, 1.2),
    grupo("/wp-login.php", 30),
    grupo("/familia/divorcio-consensual/", 7),
    grupo("/.env", 6),
    grupo("/admin/", 5),
    grupo("/redesocial/", 5),
    grupo("/index.PHP", 4),
    grupo("/xmlrpc.php", 3),
    grupo("/cgi-bin/test", 2),
    grupo("/phpmyadmin/", 2),
    grupo("/.git/config", 2),
    grupo("/leis/cc-art-393/", 2),
    grupo("/buscar/", 1),
    grupo("/wp-admin/", 1),
]


class TestClassificacao(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()

    def test_scanner_e_reconhecido_pelo_contrato(self):
        for path in ["/wp-login.php", "/wp-admin/", "/.git/config", "/.env", "/xmlrpc.php",
                     "/cgi-bin/test", "/admin/", "/phpmyadmin/", "/index.PHP", "/qualquer/coisa.php"]:
            self.assertTrue(self.mod.e_scanner(path), path)
        for path in ["/", "/familia/divorcio-consensual/", "/administrativo/x/", "/php/nao-e-extensao/",
                     "/leis/cc-art-393/", "/glossario/phpmyadmin-nao-e-prefixo/", "/xmlrpcteste/"]:
            self.assertFalse(self.mod.e_scanner(path), path)

    def test_falso_positivo_sobre_o_acervo_real(self):
        """Detector novo nasce com teste de falso positivo sobre amostra real:
        nenhuma página publicada pode sair do ranking como scanner. A forma
        literal do contrato (`^/(…|admin|…)`) reprovava aqui com 45 páginas de
        /administrativo/ (medido em 2026-09-09)."""
        caminho = os.path.join(RAIZ, "content", "pages.json")
        if not os.path.isfile(caminho):
            self.skipTest("content/pages.json ausente neste checkout")
        publicados = self.mod.caminhos_publicados(caminho)
        self.assertGreater(len(publicados), 1000, "acervo real esperado")
        acusados = sorted(p for p in publicados if self.mod.e_scanner(p))
        self.assertEqual(acusados, [], "paginas publicadas marcadas como scanner: %s" % acusados[:5])

    def test_exclui_scanner_e_conta_o_que_saiu(self):
        r = self.mod.classifica(GRUPOS, PUBLICADOS)
        paths = [x["path"] for x in r["rotas"]]
        self.assertEqual(paths, ["/", "/familia/divorcio-consensual/", "/redesocial/",
                                 "/leis/cc-art-393/", "/buscar/"])
        self.assertEqual(r["scanners_excluidos"], {"grupos": 9, "requests": 30 + 6 + 5 + 4 + 3 + 2 + 2 + 2 + 1})
        self.assertEqual(r["rotas_total_grupos"], 5)
        self.assertEqual(r["requests_total"], 104 + 7 + 5 + 2 + 1)
        self.assertFalse(r["query_truncated"])

    def test_humano_provavel_e_presenca_em_pages_json(self):
        r = self.mod.classifica(GRUPOS, PUBLICADOS)
        por_path = {x["path"]: x for x in r["rotas"]}
        self.assertTrue(por_path["/"]["humano_provavel"])
        self.assertTrue(por_path["/buscar/"]["humano_provavel"])
        self.assertFalse(por_path["/redesocial/"]["humano_provavel"])
        self.assertEqual(r["rotas_publicadas_no_topo"], 4)
        self.assertEqual(por_path["/"]["requests"], 104)
        self.assertEqual(por_path["/"]["sample_interval_medio"], 1.2)
        self.assertNotIn("requests_estimated", por_path["/"], "count x sampleInterval extrapola duas vezes")

    def test_corta_no_topo_depois_de_tirar_scanner(self):
        grupos = [grupo("/wp-%d.php" % i, 1000) for i in range(50)]
        grupos += [grupo("/pagina-%03d/" % i, 300 - i) for i in range(250)]
        r = self.mod.classifica(grupos, set(), topo=200)
        self.assertEqual(len(r["rotas"]), 200)
        self.assertEqual(r["rotas"][0]["path"], "/pagina-000/")
        self.assertEqual(r["rotas"][-1]["path"], "/pagina-199/")
        self.assertEqual(r["rotas_total_grupos"], 250)
        self.assertEqual(r["scanners_excluidos"]["grupos"], 50)

    def test_empate_ordena_por_path_para_saida_deterministica(self):
        r = self.mod.classifica([grupo("/b/", 1), grupo("/a/", 1), grupo("/c/", 2)], set())
        self.assertEqual([x["path"] for x in r["rotas"]], ["/c/", "/a/", "/b/"])

    def test_teto_da_consulta_marca_truncamento(self):
        grupos = [grupo("/p%d/" % i, 1) for i in range(3)]
        self.assertTrue(self.mod.classifica(grupos, set(), limite=3)["query_truncated"])

    def test_filtros_de_servidor_estao_na_consulta(self):
        for trecho in ['verifiedBotCategory: ""', "edgeResponseStatus: 200",
                       'edgeResponseContentTypeName: "html"', 'clientRequestHTTPMethodName: "GET"',
                       'userAgent_notlike: "wikijuridica%"', "clientRequestPath"]:
            self.assertIn(trecho, self.mod.CONSULTA, trecho)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mod.RAIZ = self.tmp.name
        self.mod.SAIDA = os.path.join(self.tmp.name, "edge_humano_por_rota_daily.jsonl")
        self.mod.PAGINAS = os.path.join(self.tmp.name, "pages.json")
        with open(self.mod.PAGINAS, "w", encoding="utf-8") as fh:
            json.dump([{"path": p} for p in sorted(PUBLICADOS)], fh)
        self.mod.RESOLVER_ZONA = lambda env: ("z", None)
        ambiente_original = self.mod.cloudflare_auth.ambiente
        self.addCleanup(setattr, self.mod.cloudflare_auth, "ambiente", ambiente_original)

    def linhas(self):
        if not os.path.exists(self.mod.SAIDA):
            return []
        with open(self.mod.SAIDA, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_sem_credencial_exit_2_e_nada_gravado(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {}
        self.assertEqual(self.mod.main(["--dia", "2026-09-08"]), 2)
        self.assertEqual(self.linhas(), [])

    def test_api_fora_exit_2_e_nada_gravado(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {"CLOUDFLARE_ZONE_TOKEN": "t"}
        self.mod.GRAPHQL = lambda consulta, variaveis, **kw: (None, "HTTP 502")
        self.assertEqual(self.mod.main(["--dia", "2026-09-08"]), 2)
        self.assertEqual(self.linhas(), [])

    def test_dia_alem_da_retencao_exit_2(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {"CLOUDFLARE_ZONE_TOKEN": "t"}
        antigo = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=30)).isoformat()
        self.assertEqual(self.mod.main(["--dia", antigo]), 2)
        self.assertEqual(self.linhas(), [])

    def test_grava_uma_linha_por_dia_e_nao_regrava_identica(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {"CLOUDFLARE_ZONE_TOKEN": "t"}
        variaveis_vistas = []

        def falso_graphql(consulta, variaveis, **kw):
            variaveis_vistas.append(variaveis)
            return resposta(GRUPOS), ""

        self.mod.GRAPHQL = falso_graphql
        self.assertEqual(self.mod.main(["--dia", "2026-09-08"]), 0)
        self.assertEqual(self.mod.main(["--dia", "2026-09-08"]), 0)
        gravadas = self.linhas()
        self.assertEqual(len(gravadas), 1)
        linha = gravadas[0]
        self.assertEqual(linha["schema_version"], "edge_humano_por_rota_v1")
        self.assertEqual(linha["date"], "2026-09-08")
        self.assertEqual(variaveis_vistas[0]["since"], "2026-09-08T00:00:00Z")
        self.assertEqual(variaveis_vistas[0]["limite"], 1000)
        self.assertEqual(len(linha["rotas"]), 5)
        self.assertEqual(linha["rotas"][0], {"path": "/", "requests": 104, "sample_interval_medio": 1.2,
                                             "humano_provavel": True})
        self.assertEqual(linha["scanners_excluidos"]["grupos"], 9)
        self.assertIn("gerado_em", linha)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + sys.argv[1:])
