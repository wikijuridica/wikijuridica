#!/usr/bin/env python3
"""Testes de tools/check-social-lastmod-causal.

O QUE ELES IMPEDEM DE VOLTAR. Gate que só foi visto aprovar nunca foi visto
guardar. Cada teste aqui monta a situação defeituosa CONCRETA que a entrega
`F2-lastmod-causal` proíbe — data que anda com a visualização, consulta que
lê a tabela de curtidas, `lastmod` no futuro, índice que não acompanha o
filho, nome de shard derivado de posição — e exige a reprovação.

Tudo offline: nenhum teste toca a rede nem o serviço. As funções de veredito
do gate são puras de propósito, e é isso que as torna testáveis.
"""
import importlib.machinery
import importlib.util
import os
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVO = os.path.join(RAIZ, "tools", "check-social-lastmod-causal")

_spec = importlib.util.spec_from_loader(
    "check_social_lastmod_causal",
    importlib.machinery.SourceFileLoader("check_social_lastmod_causal", ALVO),
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

HOJE = "2026-09-05"


def padrao():
    """O padrão real, derivado do fonte versionado deste repositório."""
    compilado, _ = gate.padrao_de_shard(RAIZ)
    return compilado


class TestPadraoDeShardVemDoFonte(unittest.TestCase):
    def test_aceita_as_tres_formas_que_o_servidor_serve(self):
        p = padrao()
        for nome in ("superficie.xml", "temas.xml", "duvidas-2026-09.xml",
                     "duvidas-2026-09-2.xml", "duvidas-2027-12-10.xml"):
            self.assertTrue(p.match(nome), nome)

    def test_recusa_o_que_socialrender_tambem_recusa(self):
        p = padrao()
        for nome in ("duvidas.xml", "duvidas-.xml", "duvidas-2026-09",
                     "duvidas-2026-9.xml", "duvidas-2026-13.xml",
                     "duvidas-2026-09-1.xml", "duvidas-2026-09-0.xml",
                     "sitemap-1.xml", "../sitemap.xml"):
            self.assertIsNone(p.match(nome), nome)

    def test_o_padrao_nao_esta_digitado_no_gate(self):
        """Se alguém copiar o nome para dentro do script, esta prova cai.

        O valor tem de sair de internal/socialrender/sitemap.go: duas cópias do
        mesmo nome divergem na primeira correção, e o gate passaria a aprovar um
        nome que o servidor recusa.
        """
        with open(ALVO, encoding="utf-8") as f:
            texto = f.read()
        codigo = "\n".join(linha for linha in texto.split("\n") if not linha.strip().startswith("#"))
        self.assertNotIn('"superficie.xml"', codigo)
        self.assertNotIn('"duvidas-"', codigo)

    def test_fonte_sem_a_constante_e_erro_declarado(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = os.path.join(tmp, "internal", "socialrender")
            os.makedirs(pasta)
            with open(os.path.join(pasta, "sitemap.go"), "w", encoding="utf-8") as f:
                f.write("package socialrender\n\nconst NomeDoShardFixo = \"superficie.xml\"\n")
            with self.assertRaises(ValueError):
                gate.padrao_de_shard(tmp)


class TestCarimbo(unittest.TestCase):
    def test_aceita_as_duas_formas_canonicas(self):
        self.assertTrue(gate.carimbo_valido("2026-09-05"))
        self.assertTrue(gate.carimbo_valido("2026-09-05T10:00:00Z"))

    def test_recusa_forma_que_o_portal_nao_emite(self):
        for valor in ("2026-9-5", "05/09/2026", "2026-09-05T10:00:00+00:00", "agora", ""):
            self.assertFalse(gate.carimbo_valido(valor), valor)


class TestPlano(unittest.TestCase):
    def test_plano_coerente_nao_reprova(self):
        indice = {"superficie.xml": "2026-09-04", "duvidas-2026-09.xml": "2026-09-03T10:00:00Z"}
        shards = {
            "superficie.xml": [("https://x/redesocial/", "2026-09-04")],
            "duvidas-2026-09.xml": [
                ("https://x/redesocial/duvida/a/", "2026-09-01"),
                ("https://x/redesocial/duvida/b/", "2026-09-03T10:00:00Z"),
            ],
        }
        self.assertEqual(gate.falhas_do_plano(indice, shards, HOJE, padrao()), [])

    def test_lastmod_no_futuro_reprova(self):
        indice = {"superficie.xml": "2026-12-01"}
        shards = {"superficie.xml": [("https://x/redesocial/", "2026-12-01")]}
        falhas = gate.falhas_do_plano(indice, shards, HOJE, padrao())
        self.assertTrue(any("FUTURO" in f for f in falhas), falhas)

    def test_indice_que_nao_acompanha_o_filho_reprova(self):
        """Quem relê o índice tem de descobrir que o shard mudou."""
        indice = {"duvidas-2026-09.xml": "2026-09-01"}
        shards = {"duvidas-2026-09.xml": [
            ("https://x/redesocial/duvida/a/", "2026-09-01"),
            ("https://x/redesocial/duvida/b/", "2026-09-04"),
        ]}
        falhas = gate.falhas_do_plano(indice, shards, HOJE, padrao())
        self.assertTrue(any("maior lastmod dos filhos" in f for f in falhas), falhas)

    def test_nome_de_shard_posicional_reprova(self):
        """Ordinal posicional some quando o plano encolhe — é a armadilha do acervo."""
        indice = {"sitemap-3.xml": "2026-09-01"}
        shards = {"sitemap-3.xml": [("https://x/redesocial/duvida/a/", "2026-09-01")]}
        falhas = gate.falhas_do_plano(indice, shards, HOJE, padrao())
        self.assertTrue(any("padrão de nome estável" in f for f in falhas), falhas)

    def test_lastmod_ausente_reprova(self):
        indice = {"superficie.xml": ""}
        shards = {"superficie.xml": [("https://x/redesocial/", "")]}
        falhas = gate.falhas_do_plano(indice, shards, HOJE, padrao())
        self.assertTrue(any("não traz lastmod" in f for f in falhas), falhas)

    def test_carimbo_fora_do_formato_do_portal_reprova(self):
        indice = {"superficie.xml": "2026-09-05T10:00:00+00:00"}
        shards = {"superficie.xml": [("https://x/redesocial/", "2026-09-05T10:00:00+00:00")]}
        falhas = gate.falhas_do_plano(indice, shards, HOJE, padrao())
        self.assertTrue(any("carimbo canônico" in f for f in falhas), falhas)

    def test_shard_vazio_reprova(self):
        indice = {"superficie.xml": "2026-09-04"}
        shards = {"superficie.xml": []}
        falhas = gate.falhas_do_plano(indice, shards, HOJE, padrao())
        self.assertTrue(any("sem nenhuma URL" in f for f in falhas), falhas)


class TestEstabilidade(unittest.TestCase):
    def test_documento_identico_apos_as_visitas_nao_reprova(self):
        antes = {"/redesocial/sitemap.xml": b"<x/>"}
        self.assertEqual(gate.falhas_de_estabilidade(antes, dict(antes), 7), [])

    def test_documento_que_muda_por_ter_sido_lido_reprova(self):
        antes = {"/redesocial/sitemap.xml": b"<lastmod>2026-09-04</lastmod>"}
        depois = {"/redesocial/sitemap.xml": b"<lastmod>2026-09-05</lastmod>"}
        falhas = gate.falhas_de_estabilidade(antes, depois, 7)
        self.assertEqual(len(falhas), 1)
        self.assertIn("visualização não altera o HTML servido", falhas[0])
        self.assertIn("7 visita(s)", falhas[0])

    def test_documento_que_some_depois_das_visitas_reprova(self):
        antes = {"/redesocial/sitemap.xml": b"<x/>"}
        falhas = gate.falhas_de_estabilidade(antes, {}, 3)
        self.assertEqual(len(falhas), 1)
        self.assertIn("não respondeu depois", falhas[0])


class TestConsultaDoSitemap(unittest.TestCase):
    def test_a_consulta_real_deste_repositorio_nao_olha_engajamento(self):
        corpo = gate.consulta_do_sitemap(RAIZ)
        self.assertEqual(gate.falhas_da_consulta(corpo), [])

    def test_consulta_que_junta_a_tabela_de_curtidas_reprova(self):
        corpo = """func (s *superficie) duvidasIndexaveis(ctx context.Context) error {
	consulta := `SELECT d.slug, COUNT(x.conta_id) FROM duvidas d
	              LEFT JOIN reacoes x ON x.alvo_id = d.id`
	return nil
}"""
        falhas = gate.falhas_da_consulta(corpo)
        self.assertEqual(len(falhas), 1)
        self.assertIn("reacoes", falhas[0])

    def test_comentario_que_explica_a_regra_nao_reprova(self):
        """O arquivo que documenta por que a curtida não entra não pode reprovar."""
        corpo = """func (s *superficie) duvidasIndexaveis(ctx context.Context) error {
	// A tabela reacoes NAO entra aqui: curtida nao muda o HTML.
	// orcamento_diario tambem nao.
	return nil
}"""
        self.assertEqual(gate.falhas_da_consulta(corpo), [])

    def test_recorte_e_a_funcao_e_nao_o_arquivo_inteiro(self):
        corpo = gate.consulta_do_sitemap(RAIZ)
        self.assertTrue(corpo.startswith("func (s *superficie) duvidasIndexaveis("))
        self.assertNotIn("func (s *superficie) planoDoSitemapEm(", corpo)


class TestLeituraDeXML(unittest.TestCase):
    ESPACO = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'

    def test_le_indice_reduz_o_loc_ao_nome_do_arquivo(self):
        corpo = (
            f'<?xml version="1.0"?><sitemapindex {self.ESPACO}>'
            "<sitemap><loc>https://x/redesocial/sitemap/superficie.xml</loc>"
            "<lastmod>2026-09-04</lastmod></sitemap></sitemapindex>"
        ).encode()
        self.assertEqual(gate.le_indice(corpo), {"superficie.xml": "2026-09-04"})

    def test_le_urlset_devolve_os_pares(self):
        corpo = (
            f'<?xml version="1.0"?><urlset {self.ESPACO}>'
            "<url><loc>https://x/redesocial/</loc><lastmod>2026-09-04</lastmod></url>"
            "</urlset>"
        ).encode()
        self.assertEqual(gate.le_urlset(corpo), [("https://x/redesocial/", "2026-09-04")])

    def test_loc_de_outro_host_nao_vira_caminho(self):
        self.assertIsNone(gate.caminho_de("https://outro.example/redesocial/", "https://x"))
        self.assertEqual(gate.caminho_de("https://x/redesocial/", "https://x"), "/redesocial/")


if __name__ == "__main__":
    unittest.main()
