#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes de tools/generate-planalto-anchor-registry-20260911.

O que se prova aqui é a regra que separa âncora BOA de âncora que MENTE. O
Planalto usa a mesma grafia para coisas diferentes: `art19i` pode ser o
"Art. 19-I" da Lei 8.080 ou o inciso I do art. 19 de outra lei, e as duas
existem. Emitir a errada dá um link que funciona e leva ao dispositivo errado —
pior que link raso, e a classe que o CLAUDE.md chama de P1 permanente sob a OAB.

Todos rodam OFFLINE: HTML sintético, nenhum download.

Rodar:
    python3 tools/test_generate_planalto_anchor_registry_20260911.py
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import inspect
import pathlib
import re
import textwrap
import unittest

FERRAMENTA = pathlib.Path(__file__).resolve().parent / "generate-planalto-anchor-registry-20260911"


def carrega():
    loader = importlib.machinery.SourceFileLoader("gerador_ancora_20260911", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


M = carrega()


class LeituraDoTexto(unittest.TestCase):
    def test_numero_do_artigo(self):
        casos = {
            "Art. 54-A. Os contratos de adesão...": "54a",
            "Art. 1.789. Havendo herdeiros...": "1789",
            "Art. 19-I. São estabelecidos...": "19i",
            "Artigo 5º As normas...": "5",
            "Art 206. Prescreve...": "206",
            "I - a saúde é direito de todos": None,
            "§ 3º Prescreve em três anos": None,
            "Parágrafo único. Aplica-se...": None,
            "": None,
        }
        for texto, esperado in casos.items():
            self.assertEqual(M.numero_do_artigo_no_texto(texto), esperado, texto)

    def test_numero_do_paragrafo(self):
        casos = {
            "§ 3º Prescreve em três anos": "3",
            "§1º O disposto...": "1",
            "§ 12. Nos casos...": "12",
            "Parágrafo único. Aplica-se...": None,
            "Art. 206. Prescreve...": None,
        }
        for texto, esperado in casos.items():
            self.assertEqual(M.numero_do_paragrafo_no_texto(texto), esperado, texto)


class Unanimidade(unittest.TestCase):
    """`None` NÃO é neutro: texto que existe e não casa é discordância."""

    def test_todas_confirmam(self):
        classe, _ = M.veredito_unanime(["54a", "54a"], "54a", "artigo_letrado", "artigo 54a")
        self.assertEqual(classe, "artigo_letrado")

    def test_uma_ocorrencia_que_nao_casa_derruba(self):
        classe, motivo = M.veredito_unanime(["19i", None], "19i", "artigo_letrado", "artigo 19i")
        self.assertEqual(classe, "indeterminado", motivo)
        self.assertIn("ambigua", motivo)

    def test_duas_leituras_diferentes_derrubam(self):
        classe, _ = M.veredito_unanime(["54a", "54b"], "54a", "artigo_letrado", "artigo 54a")
        self.assertEqual(classe, "indeterminado")

    def test_nenhuma_ocorrencia_com_texto(self):
        classe, motivo = M.veredito_unanime([], "54a", "artigo_letrado", "artigo 54a")
        self.assertEqual(classe, "indeterminado")
        self.assertIn("nenhuma ocorrencia", motivo)

    def test_mutante_que_trata_None_como_neutro_aceita_a_ancora_que_mente(self):
        """A prova: com `v is not None and v != esperado`, o inciso deixa de contradizer."""
        fonte = textwrap.dedent(inspect.getsource(M.veredito_unanime))
        self.assertIn("discordam = [v for v in vistos if v != esperado]", fonte,
                      "o fonte precisa contar TODA discordância; sem isso a mutação seria vazia")
        mutante_fonte = fonte.replace(
            "discordam = [v for v in vistos if v != esperado]",
            "discordam = [v for v in vistos if v is not None and v != esperado]")
        espaco: dict = {}
        exec(compile(mutante_fonte, "<mutante veredito_unanime>", "exec"), espaco)
        mutante = espaco["veredito_unanime"]

        vistos = ["19i", None]  # uma ocorrência "Art. 19-I", outra "I - ..."
        self.assertEqual(M.veredito_unanime(vistos, "19i", "artigo_letrado", "artigo 19i")[0],
                         "indeterminado")
        self.assertEqual(mutante(vistos, "19i", "artigo_letrado", "artigo 19i")[0],
                         "artigo_letrado",
                         "o mutante deveria aceitar a âncora ambígua e não aceitou")
        print("\n  mutante (None neutro) ACEITA art19i ambíguo; original recusa")


class ClassificacaoSobreHTML(unittest.TestCase):
    def mede(self, corpo: str) -> dict:
        html = ("<html><head><title>x</title></head><body>" + corpo + "</body></html>")
        return M.mede_documento("https://exemplo.invalido/doc.htm", html.encode("latin-1"))

    def test_artigo_letrado_confirmado_entra(self):
        r = self.mede('<a name="art54a"></a>Art. 54-A. Os contratos de adesão.')
        self.assertIn("art54a", r["ancoras_de_artigo_letrado"])

    def test_inciso_disfarcado_de_artigo_letrado_nao_vira_letrado(self):
        """O que ele NUNCA pode ser continua valendo; o que ele É mudou em 2026-09-11.

        Até essa data a âncora ficava `indeterminado`, e a asserção deste teste
        era `classes["indeterminado"] == 1`. A recusa estava certa para a
        pergunta que o validador fazia — "o texto diz 'artigo 19i'?" — e errada
        sobre o mundo: `art19i` é o art. 19, INCISO I, e o texto ao lado diz
        exatamente "I - ". Medido no `amostra_recusada` do registry: 1.862
        âncoras nesta situação, 1.722 confirmáveis pelo texto seguinte.

        O que este teste continua exigindo, e é o que importa: a âncora NÃO
        entra como artigo letrado. Link que funciona e leva ao dispositivo
        errado é a classe P1 permanente sob a OAB.
        """
        r = self.mede('<a name="art19i"></a>I - a saúde é direito de todos.')
        self.assertNotIn("art19i", r["ancoras_de_artigo_letrado"])
        self.assertIn("art19i", r["ancoras_de_inciso"])
        self.assertEqual(r["classes"].get("inciso"), 1)
        self.assertIsNone(r["classes"].get("indeterminado"))

    def test_mesma_chave_com_duas_leituras_fica_de_fora(self):
        r = self.mede('<a name="art19i"></a>Art. 19-I. São estabelecidos.'
                      '<p><a name="art19i"></a>I - a saúde é direito de todos.</p>')
        self.assertNotIn("art19i", r["ancoras_de_artigo_letrado"])

    def test_paragrafo_confirmado_entra(self):
        r = self.mede('<a name="art206§3"></a>§ 3º Prescreve em três anos.')
        self.assertIn("art206§3", r["ancoras_de_paragrafo"])

    def test_paragrafo_com_numero_errado_fica_de_fora(self):
        r = self.mede('<a name="art206§3"></a>§ 5º Prescreve em cinco anos.')
        self.assertNotIn("art206§3", r["ancoras_de_paragrafo"])

    def test_artigo_puro_nao_passa_pela_conferencia_de_texto(self):
        """A forma `artN` está em produção desde 2026-08-26; exigir texto encolheria a tabela."""
        r = self.mede('<a name="art206"></a>Sumário sem o texto do artigo.')
        self.assertIn("art206", r["ancoras_de_artigo"])

    def test_ancora_de_sumario_sem_texto_nao_derruba_a_boa(self):
        r = self.mede('<a name="art54a"></a><a name="outra"></a>'
                      '<p><a name="art54a"></a>Art. 54-A. Os contratos.</p>')
        self.assertIn("art54a", r["ancoras_de_artigo_letrado"])


class Inciso(unittest.TestCase):
    """O segundo ramo de `classifica`, e a ordem entre os dois.

    `art19i` tem a MESMA forma do artigo letrado e significado oposto. Quem
    desempata é o texto, nunca a forma — e a pergunta do artigo letrado vem
    SEMPRE primeiro, porque quando o documento diz "Art. 19-I" a âncora é mesmo
    o artigo letrado e perguntar pelo inciso antes roubaria o caso.
    """

    def mede(self, corpo: str) -> dict:
        html = ("<html><head><title>x</title></head><body>" + corpo + "</body></html>")
        return M.mede_documento("https://exemplo.invalido/doc.htm", html.encode("latin-1"))

    def test_inciso_confirmado_pelo_texto_entra(self):
        r = self.mede('<a name="art19ii"></a>II - o nome, a qualificação e o endereço.')
        self.assertIn("art19ii", r["ancoras_de_inciso"])
        self.assertIn("art19ii", M.emitiveis(r))

    def test_separadores_que_o_planalto_usa(self):
        for corpo, ancora in (
            ('<a name="art19iv"></a>IV - a modalidade da garantia;', "art19iv"),
            ('<a name="art19ix"></a>IX. o local e a data da emissão;', "art19ix"),
            ('<a name="art19v"></a>V) o número e a série da cédula;', "art19v"),
        ):
            with self.subTest(ancora=ancora):
                self.assertIn(ancora, self.mede(corpo)["ancoras_de_inciso"])

    def test_artigo_letrado_continua_ganhando_quando_o_texto_o_nomeia(self):
        """A ordem das duas perguntas, provada pelo caso que a inversão roubaria."""
        r = self.mede('<a name="art19i"></a>Art. 19-I. São estabelecidos os critérios.')
        self.assertIn("art19i", r["ancoras_de_artigo_letrado"])
        self.assertEqual(r.get("ancoras_de_inciso"), [])

    def test_duas_leituras_discordantes_derrubam_as_DUAS_perguntas(self):
        """O desenho original não muda: ambígua no documento fica fora de tudo."""
        r = self.mede('<a name="art19i"></a>Art. 19-I. São estabelecidos.'
                      '<p><a name="art19i"></a>I - a saúde é direito de todos.</p>')
        self.assertNotIn("art19i", r["ancoras_de_artigo_letrado"])
        self.assertNotIn("art19i", r.get("ancoras_de_inciso") or [])
        self.assertEqual(r["classes"].get("indeterminado"), 1)

    def test_palavra_que_comeca_por_romano_nao_vira_inciso(self):
        """Sem o separador, "Ivo" viraria o inciso IV e "Cidade" o inciso C."""
        self.assertIsNone(M.numero_do_inciso_no_texto("Ivo Pereira assinou o contrato."))
        self.assertIsNone(M.numero_do_inciso_no_texto("Cidade do Rio de Janeiro."))
        self.assertIsNone(M.numero_do_inciso_no_texto("Lei complementar."))
        self.assertEqual(M.numero_do_inciso_no_texto("IV - a modalidade"), "iv")

    def test_inciso_com_romano_errado_fica_de_fora(self):
        r = self.mede('<a name="art19ii"></a>III - o nome e a qualificação.')
        self.assertNotIn("art19ii", r.get("ancoras_de_inciso") or [])
        self.assertEqual(r["classes"].get("indeterminado"), 1)

    def test_mutante_que_dispensa_o_separador_aceita_palavra_como_inciso(self):
        fonte = inspect.getsource(M.numero_do_inciso_no_texto)
        self.assertIn(r'[-–—.)]', fonte,
                      "a mutação precisa deste literal para significar alguma coisa")
        escopo = {"re": re}
        exec(compile(fonte.replace(r'\s*[-–—.)]', ''), "<mutante>", "exec"), escopo)
        mutante = escopo["numero_do_inciso_no_texto"]
        self.assertIsNone(M.numero_do_inciso_no_texto("Ivo Pereira assinou."))
        # "Ivo" tem só o `I` maiúsculo — o mutante devolve o inciso I, e uma
        # âncora `art19i` passaria a "confirmar" contra o nome de uma pessoa.
        self.assertEqual(mutante("Ivo Pereira assinou."), "i")

    def test_mutante_que_pergunta_o_inciso_ANTES_rouba_o_artigo_letrado(self):
        """Inverter a ordem faz `art19i` com "Art. 19-I" virar inciso I."""
        texto_letrado = ["Art. 19-I. São estabelecidos os critérios."]
        classe, _ = M.classifica("art19i", texto_letrado)
        self.assertEqual(classe, "artigo_letrado")
        # A inversão simulada: perguntar pelo inciso primeiro sobre o MESMO texto.
        vistos = [M.numero_do_inciso_no_texto(t) for t in texto_letrado]
        self.assertEqual(vistos, [None],
                         "o texto do artigo letrado não confirma inciso nenhum — "
                         "é por isso que a ordem é segura, e não por sorte")


class GuardaDeRegressao(unittest.TestCase):
    def monta(self, sha_antes, sha_depois, ancoras_antes, ancoras_depois):
        url = "https://exemplo.invalido/doc.htm"
        antes = {url: {"url": url, "sha256_documento": sha_antes,
                       "ancoras_de_artigo": ancoras_antes, "bytes": 10}}
        agora = {url: {"url": url, "sha256_documento": sha_depois,
                       "ancoras_de_artigo": ancoras_depois,
                       "ancoras_de_artigo_letrado": [], "ancoras_de_paragrafo": [],
                       "bytes": 11}}
        return agora, antes

    def test_documento_inalterado_com_menos_ancoras_e_recusado(self):
        agora, antes = self.monta("aaa", "aaa", ["art1", "art2"], ["art1"])
        self.assertFalse(M.conferencia_de_regressao(agora, antes))

    def test_documento_mudado_com_menos_ancoras_segue(self):
        agora, antes = self.monta("aaa", "bbb", ["art1", "art2"], ["art1"])
        self.assertTrue(M.conferencia_de_regressao(agora, antes))

    def test_sem_perda_segue(self):
        agora, antes = self.monta("aaa", "aaa", ["art1"], ["art1", "art2"])
        self.assertTrue(M.conferencia_de_regressao(agora, antes))

    def test_mutante_que_ignora_o_sha_deixa_passar_a_regressao_do_parser(self):
        fonte = textwrap.dedent(inspect.getsource(M.conferencia_de_regressao))
        alvo = ('        sha_igual = (antes[url].get("sha256_documento")\n'
                '                     == registro.get("sha256_documento"))')
        self.assertIn(alvo, fonte,
                      "o fonte precisa comparar o sha; sem isso a mutação seria vazia")
        mutante_fonte = fonte.replace(alvo, "        sha_igual = False")
        espaco: dict = {"emitiveis": M.emitiveis, "sys": M.sys}
        exec(compile(mutante_fonte, "<mutante conferencia_de_regressao>", "exec"), espaco)
        mutante = espaco["conferencia_de_regressao"]
        agora, antes = self.monta("aaa", "aaa", ["art1", "art2"], ["art1"])
        self.assertFalse(M.conferencia_de_regressao(agora, antes))
        self.assertTrue(mutante(agora, antes),
                        "o mutante deveria deixar passar a regressão do parser")
        print("\n  mutante (sha ignorado) ACEITA tabela encolhida com documento inalterado")


class PisoDeLinks(unittest.TestCase):
    def test_o_piso_e_um_argumento_com_default_declarado(self):
        """O corte da cauda é explícito; nunca amostra silenciosa."""
        fonte = FERRAMENTA.read_text(encoding="utf-8")
        self.assertIn('"--minimo-de-links", type=int, default=10', fonte)
        self.assertIn("piso de {args.minimo_de_links} link(s)", fonte)


if __name__ == "__main__":
    unittest.main(verbosity=2)
