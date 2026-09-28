#!/usr/bin/env python3
"""Testes de tools/check-social-indexavel.

O QUE ELES IMPEDEM DE VOLTAR. Um gate de indexação só serve se for visto
REPROVANDO: gate que só foi visto aprovar nunca foi visto guardar. Cada teste
aqui monta a situação defeituosa concreta — canonical de outro host, rota
indexável fora do sitemap, `max-snippet` limitado, gêmea Markdown ausente,
robots.txt sem a diretiva de descoberta — e exige a reprovação.

Tudo offline: nenhum teste toca a rede, o log de produção ou o serviço. As
funções de veredito são puras de propósito, e é isso que as torna testáveis.
"""
import importlib.machinery
import importlib.util
import os
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVO = os.path.join(RAIZ, "tools", "check-social-indexavel")

_spec = importlib.util.spec_from_loader(
    "check_social_indexavel",
    importlib.machinery.SourceFileLoader("check_social_indexavel", ALVO),
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

BASE = "https://wikijuridica.com.br"

ROBOTS_PUBLICO = "index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1"


def pagina(caminho, robots=ROBOTS_PUBLICO, titulo=None, descricao=None, canonical=None, bytes_=2000):
    """Monta o dicionário que `avalia` produziria para uma página servida."""
    return {
        "titulo": titulo if titulo is not None else f"Titulo suficiente para {caminho}",
        "descricao": descricao if descricao is not None else ("D" * 100),
        "canonical": canonical if canonical is not None else BASE + caminho,
        "robots": robots,
        "x_robots": None,
        "bytes": bytes_,
        "indexavel": gate.indexavel(robots),
    }


class TestLeituraDaMarcacao(unittest.TestCase):
    def test_extrai_os_quatro_sinais_e_desfaz_entidade(self):
        corpo = (
            b'<html><head><title>Consulta ao acervo &amp; precedentes</title>'
            b'<meta name="description" content="Texto com &quot;aspas&quot;">'
            b'<link rel="canonical" href="https://wikijuridica.com.br/redesocial/">'
            b'<meta name="robots" content="noindex,follow"></head><body></body></html>'
        )
        lido = gate.le_marcacao(corpo)
        self.assertEqual(lido["titulo"], "Consulta ao acervo & precedentes")
        self.assertEqual(lido["descricao"], 'Texto com "aspas"')
        self.assertEqual(lido["canonical"], "https://wikijuridica.com.br/redesocial/")
        self.assertEqual(lido["robots"], "noindex,follow")

    def test_ausencia_de_meta_robots_e_indexacao_por_padrao(self):
        # É assim que o buscador lê. Tratar ausência como noindex esconderia
        # rota que de fato entra no índice.
        self.assertTrue(gate.indexavel(None))
        self.assertTrue(gate.indexavel("index,follow"))
        self.assertFalse(gate.indexavel("noindex, follow"))
        self.assertFalse(gate.indexavel("NOINDEX,FOLLOW"))


class TestAsercoesDePagina(unittest.TestCase):
    def test_conjunto_correto_nao_produz_falha(self):
        paginas = {
            "/redesocial/": pagina("/redesocial/"),
            "/redesocial/consulta/": pagina("/redesocial/consulta/", robots="noindex,follow",
                                            descricao="D" * 178),
        }
        self.assertEqual(gate.falhas_de_marcacao(paginas, BASE, 50000), [])

    def test_canonical_de_outro_host_reprova(self):
        paginas = {"/redesocial/": pagina("/redesocial/", canonical="https://exemplo.invalido/redesocial/")}
        falhas = gate.falhas_de_marcacao(paginas, BASE, 50000)
        self.assertTrue(any("canonical" in f for f in falhas), falhas)

    def test_canonical_relativo_reprova(self):
        paginas = {"/redesocial/": pagina("/redesocial/", canonical="/redesocial/")}
        self.assertTrue(gate.falhas_de_marcacao(paginas, BASE, 50000))

    def test_snippet_limitado_reprova(self):
        # Limitar o snippet reduz a chance de citação por IA: o contrato exige -1.
        paginas = {"/redesocial/": pagina("/redesocial/", robots="index,follow,max-snippet:160")}
        falhas = gate.falhas_de_marcacao(paginas, BASE, 50000)
        self.assertTrue(any("max-snippet:-1" in f for f in falhas), falhas)

    def test_noindex_de_conteudo_sem_follow_reprova(self):
        paginas = {"/redesocial/consulta/": pagina("/redesocial/consulta/", robots="noindex,nofollow",
                                                   descricao="D" * 100)}
        falhas = gate.falhas_de_marcacao(paginas, BASE, 50000)
        self.assertTrue(any("follow" in f for f in falhas), falhas)

    def test_tela_de_conta_pode_ser_nofollow(self):
        # Ali o motivo é privacidade de área autenticada, não política de SEO.
        paginas = {"/redesocial/conta/entrar/": pagina("/redesocial/conta/entrar/",
                                                       robots="noindex, nofollow, noarchive")}
        self.assertEqual(gate.falhas_de_marcacao(paginas, BASE, 50000), [])

    def test_x_robots_tag_contradizendo_a_meta_reprova(self):
        dados = pagina("/redesocial/")
        dados["x_robots"] = "noindex"
        falhas = gate.falhas_de_marcacao({"/redesocial/": dados}, BASE, 50000)
        self.assertTrue(any("X-Robots-Tag" in f for f in falhas), falhas)

    def test_title_fora_da_faixa_reprova_nos_dois_extremos(self):
        curto = gate.falhas_de_marcacao({"/redesocial/": pagina("/redesocial/", titulo="Curto")}, BASE, 50000)
        longo = gate.falhas_de_marcacao({"/redesocial/": pagina("/redesocial/", titulo="T" * 66)}, BASE, 50000)
        self.assertTrue(any("<title>" in f for f in curto), curto)
        self.assertTrue(any("<title>" in f for f in longo), longo)

    def test_title_repetido_reprova(self):
        paginas = {
            "/redesocial/": pagina("/redesocial/", titulo="Titulo identico nas duas rotas"),
            "/redesocial/perguntas/": pagina("/redesocial/perguntas/", titulo="Titulo identico nas duas rotas"),
        }
        falhas = gate.falhas_de_marcacao(paginas, BASE, 50000)
        self.assertTrue(any("repetido" in f for f in falhas), falhas)

    def test_description_longa_reprova_na_indexavel_e_passa_na_noindex(self):
        # A faixa 70-160 é regra de snippet de SERP: ela decide onde há SERP.
        indexavel = gate.falhas_de_marcacao(
            {"/redesocial/": pagina("/redesocial/", descricao="D" * 178)}, BASE, 50000)
        noindex = gate.falhas_de_marcacao(
            {"/redesocial/tese/": pagina("/redesocial/tese/", robots="noindex,follow", descricao="D" * 192)},
            BASE, 50000)
        self.assertTrue(any("description" in f for f in indexavel), indexavel)
        self.assertEqual(noindex, [])

    def test_teto_de_bytes_reprova(self):
        paginas = {"/redesocial/": pagina("/redesocial/", bytes_=50001)}
        falhas = gate.falhas_de_marcacao(paginas, BASE, 50000)
        self.assertTrue(any("50000" in f for f in falhas), falhas)


class TestSitemap(unittest.TestCase):
    def setUp(self):
        self.paginas = {
            "/redesocial/": pagina("/redesocial/"),
            "/redesocial/perguntas/": pagina("/redesocial/perguntas/"),
            "/redesocial/consulta/": pagina("/redesocial/consulta/", robots="noindex,follow"),
        }

    def test_conjunto_exato_nao_produz_falha(self):
        locs = [BASE + "/redesocial/", BASE + "/redesocial/perguntas/"]
        self.assertEqual(gate.falhas_de_sitemap(locs, self.paginas, BASE), [])

    def test_indexavel_fora_do_sitemap_e_descoberta_perdida(self):
        locs = [BASE + "/redesocial/"]
        falhas = gate.falhas_de_sitemap(locs, self.paginas, BASE)
        self.assertTrue(any("descoberta perdida" in f for f in falhas), falhas)

    def test_noindex_dentro_do_sitemap_e_contradicao(self):
        locs = [BASE + "/redesocial/", BASE + "/redesocial/perguntas/", BASE + "/redesocial/consulta/"]
        falhas = gate.falhas_de_sitemap(locs, self.paginas, BASE)
        self.assertTrue(any("contradição" in f for f in falhas), falhas)

    def test_loc_de_rota_que_nao_responde_reprova(self):
        locs = [BASE + "/redesocial/", BASE + "/redesocial/perguntas/", BASE + "/redesocial/fantasma/"]
        falhas = gate.falhas_de_sitemap(locs, self.paginas, BASE)
        self.assertTrue(any("fantasma" in f for f in falhas), falhas)

    def test_loc_de_outro_host_reprova(self):
        locs = ["https://exemplo.invalido/redesocial/", BASE + "/redesocial/", BASE + "/redesocial/perguntas/"]
        falhas = gate.falhas_de_sitemap(locs, self.paginas, BASE)
        self.assertTrue(any("base pública" in f for f in falhas), falhas)

    def test_caminho_de_loc_e_de_shard(self):
        self.assertEqual(gate.caminho_de(BASE + "/redesocial/x/", BASE), "/redesocial/x/")
        self.assertIsNone(gate.caminho_de("https://outro.invalido/x/", BASE))
        self.assertEqual(gate.caminho_do_shard(BASE + "/redesocial/sitemap/superficie.xml"),
                         "/redesocial/sitemap/superficie.xml")
        self.assertIsNone(gate.caminho_do_shard("superficie.xml"))


class TestDescoberta(unittest.TestCase):
    INDICE = "/redesocial/sitemap.xml"

    def test_robots_com_a_diretiva_passa(self):
        texto = "User-agent: *\nAllow: /\n\nSitemap: https://wikijuridica.com.br/sitemap.xml\n" \
                "Sitemap: https://wikijuridica.com.br/redesocial/sitemap.xml\n"
        self.assertEqual(
            gate.falhas_de_descoberta(texto, "teste", BASE, "/sitemap.xml", [self.INDICE], self.INDICE), [])

    def test_robots_sem_a_diretiva_reprova(self):
        # É o defeito medido em 2026-09-05: a política declara o sitemap social
        # e o robots.txt servido não o anuncia. Sitemap sem descoberta não é lido.
        texto = "User-agent: *\nAllow: /\n\nSitemap: https://wikijuridica.com.br/sitemap.xml\n"
        falhas = gate.falhas_de_descoberta(texto, "teste", BASE, "/sitemap.xml", [self.INDICE], self.INDICE)
        self.assertTrue(any("descobri-lo" in f for f in falhas), falhas)

    def test_politica_sem_o_adicional_reprova(self):
        texto = "Sitemap: https://wikijuridica.com.br/sitemap.xml\n"
        falhas = gate.falhas_de_descoberta(texto, "teste", BASE, "/sitemap.xml", [], self.INDICE)
        self.assertTrue(any("additional_sitemap_paths" in f for f in falhas), falhas)

    def test_social_como_sitemap_principal_reprova(self):
        texto = "Sitemap: https://wikijuridica.com.br/redesocial/sitemap.xml\n"
        falhas = gate.falhas_de_descoberta(texto, "teste", BASE, self.INDICE, [], self.INDICE)
        self.assertTrue(any("sitemap_path" in f for f in falhas), falhas)


class TestIsolamentoDoIndiceDoAcervo(unittest.TestCase):
    def test_loc_social_em_public_sitemap_reprova(self):
        with tempfile.TemporaryDirectory() as pasta:
            os.mkdir(os.path.join(pasta, "public"))
            with open(os.path.join(pasta, "public", "sitemap.xml"), "w", encoding="utf-8") as f:
                f.write("<sitemapindex><sitemap><loc>https://x/redesocial/sitemap.xml</loc></sitemap></sitemapindex>")
            falhas = gate.falhas_de_isolamento(pasta)
        self.assertTrue(falhas)

    def test_indice_limpo_passa(self):
        with tempfile.TemporaryDirectory() as pasta:
            os.mkdir(os.path.join(pasta, "public"))
            with open(os.path.join(pasta, "public", "sitemap.xml"), "w", encoding="utf-8") as f:
                f.write("<sitemapindex><sitemap><loc>https://x/sitemaps/pages-0001.xml</loc></sitemap></sitemapindex>")
            self.assertEqual(gate.falhas_de_isolamento(pasta), [])


class TestCenso(unittest.TestCase):
    def test_literais_ignoram_arquivo_de_teste_e_chave_de_template(self):
        with tempfile.TemporaryDirectory() as pasta:
            fonte = os.path.join(pasta, "cmd", "social")
            os.makedirs(fonte)
            with open(os.path.join(fonte, "rotas.go"), "w", encoding="utf-8") as f:
                f.write('const a = "/redesocial/"\nconst b = "/redesocial/perguntas/"\n'
                        'mux.HandleFunc("/redesocial/duvida/{slug}/", nil)\n')
            with open(os.path.join(fonte, "rotas_test.go"), "w", encoding="utf-8") as f:
                f.write('const fixture = "/redesocial/perfil/inventado/"\n')
            achados = gate.literais_de_rota(pasta)
        self.assertIn("/redesocial/", achados)
        self.assertIn("/redesocial/perguntas/", achados)
        self.assertNotIn("/redesocial/perfil/inventado/", achados)
        self.assertFalse([a for a in achados if "{" in a])

    def test_so_html_descarta_asset_e_documento_de_maquina(self):
        entrada = {"/redesocial/", "/redesocial/index.md", "/redesocial/sitemap.xml",
                   "/redesocial/assets/css/wj-social-abc.css", "/redesocial/assets/"}
        self.assertEqual(gate.so_html(entrada), {"/redesocial/"})


class TestTetoLidoDoFonte(unittest.TestCase):
    def test_le_a_constante_do_go(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = os.path.join(pasta, "internal", "htmlcontract")
            os.makedirs(destino)
            with open(os.path.join(destino, "htmlcontract.go"), "w", encoding="utf-8") as f:
                f.write("package htmlcontract\n\nconst (\n\tHTMLBudgetBytes = 50000\n)\n")
            self.assertEqual(gate.teto_de_bytes(pasta), 50000)

    def test_ausencia_da_constante_e_erro_e_nao_numero_chutado(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = os.path.join(pasta, "internal", "htmlcontract")
            os.makedirs(destino)
            with open(os.path.join(destino, "htmlcontract.go"), "w", encoding="utf-8") as f:
                f.write("package htmlcontract\n")
            with self.assertRaises(ValueError):
                gate.teto_de_bytes(pasta)


if __name__ == "__main__":
    unittest.main()
