#!/usr/bin/env python3
"""Testes do resolvedor determinístico de briefs (controles positivos E
negativos). Os negativos são o contrato anti-falso-verde: número parecido
NUNCA pode casar norma errada, e súmula sem tribunal explícito NUNCA casa
o acervo STF por palpite."""

import datetime
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import generate_v2_writing_briefs as briefs  # noqa: E402


def _fake_index():
    by_norm = {
        ("lei", "8078"): {"urn": "urn:lex:br:federal:lei:1990-09-11;8078",
                          "ano": "1990"},
        ("lei", "10406"): {"urn": "urn:lex:br:federal:lei:2002-01-10;10406",
                           "ano": "2002"},
        ("decreto.lei", "5452"):
            {"urn": "urn:lex:br:federal:decreto.lei:1943-05-01;5452",
             "ano": "1943"},
        ("lei.complementar", "116"):
            {"urn": "urn:lex:br:federal:lei.complementar:2003-07-31;116",
             "ano": "2003"},
        ("decreto", "11034"):
            {"urn": "urn:lex:br:federal:decreto:2022-04-05;11034",
             "ano": "2022"},
        ("sumula-stf", "145"):
            {"urn": "urn:lex:br:supremo.tribunal.federal:sumula:1963;145",
             "ano": ""},
    }
    by_series = {
        ("urn:lex:br:federal:lei:1990-09-11;8078", ""): {"version_seq": 1},
        ("urn:lex:br:federal:lei:1990-09-11;8078", "art_104-B"):
            {"version_seq": 1},
        ("urn:lex:br:federal:lei:1990-09-11;8078", "art_49"):
            {"version_seq": 1},
        ("urn:lex:br:federal:lei:2002-01-10;10406", ""): {"version_seq": 1},
        ("urn:lex:br:federal:lei:2002-01-10;10406", "art_951"):
            {"version_seq": 1},
        ("urn:lex:br:federal:decreto.lei:1943-05-01;5452", ""):
            {"version_seq": 1},
        ("urn:lex:br:federal:decreto.lei:1943-05-01;5452", "art_477"):
            {"version_seq": 1},
        ("urn:lex:br:federal:lei.complementar:2003-07-31;116", ""):
            {"version_seq": 1},
        ("urn:lex:br:federal:decreto:2022-04-05;11034", ""):
            {"version_seq": 1},
        ("urn:lex:br:supremo.tribunal.federal:sumula:1963;145", ""):
            {"version_seq": 1},
    }
    return by_norm, by_series


class ResolvePositive(unittest.TestCase):
    def setUp(self):
        self.by_norm, self.by_series = _fake_index()

    def resolve(self, hint):
        parsed = briefs.parse_hint(hint)
        if parsed is None:
            return ("unparsed", None, None)
        return briefs.resolve_norm(parsed, self.by_norm, self.by_series)

    def test_slug_article_with_suffix(self):
        status, urn, disp = self.resolve("lei-8078-1990-art-104-b")
        self.assertEqual(
            (status, disp), ("corpus_article", "art_104-B"))
        self.assertTrue(urn.endswith(";8078"))

    def test_alias_cdc_free_text(self):
        status, urn, disp = self.resolve("CDC art. 49")
        self.assertEqual((status, disp), ("corpus_article", "art_49"))

    def test_alias_codigo_civil_free_text(self):
        status, urn, disp = self.resolve("Código Civil art. 951")
        self.assertEqual((status, disp), ("corpus_article", "art_951"))
        self.assertTrue(urn.endswith(";10406"))

    def test_clt_year_only_slug(self):
        status, urn, disp = self.resolve("clt-5452-1943-art-477")
        self.assertEqual((status, disp), ("corpus_article", "art_477"))
        self.assertIn("decreto.lei", urn)

    def test_lei_prefixed_clt_falls_to_decreto_lei_safe_number(self):
        # "Lei 5.452/1943" é a CLT (decreto-lei) — fallback seguro por
        # número consagrado + ano concordante.
        status, urn, disp = self.resolve("Lei 5.452/1943 art. 477")
        self.assertEqual(status, "corpus_article")
        self.assertIn("decreto.lei", urn)

    def test_sumula_stf_explicit_court(self):
        status, urn, disp = self.resolve("sumula-145-stf")
        self.assertEqual(status, "corpus_article")
        self.assertIn("supremo.tribunal.federal", urn)

    def test_article_missing_degrades_to_norm(self):
        status, urn, disp = self.resolve("cdc-lei-8078-1990-art-999")
        self.assertEqual(status, "corpus_norm_article_missing")
        self.assertEqual(disp, "")


class ResolveNegativeControls(unittest.TestCase):
    """Falso-verde proibido: cada caso abaixo DEVE ficar fora do corpus."""

    def setUp(self):
        self.by_norm, self.by_series = _fake_index()

    def resolve(self, hint):
        parsed = briefs.parse_hint(hint)
        if parsed is None:
            return ("unparsed", None, None)
        return briefs.resolve_norm(parsed, self.by_norm, self.by_series)

    def test_lc_123_nao_casa_lc_116(self):
        status, _, _ = self.resolve("lc-123-2006")
        self.assertEqual(status, "off_corpus")

    def test_lei_11034_nao_casa_decreto_11034(self):
        # Lei 11.034/2004 existe e NÃO é o Decreto 11.034/2022: sem ano
        # concordante e fora da lista segura, fallback de tipo é proibido.
        status, _, _ = self.resolve("lei-11034")
        self.assertEqual(status, "off_corpus")
        status, _, _ = self.resolve("Lei 11.034/2004")
        self.assertEqual(status, "off_corpus")

    def test_ano_divergente_reprova(self):
        # lei-8078 com ano errado não pode casar o CDC.
        status, _, _ = self.resolve("lei-8078-1991")
        self.assertEqual(status, "off_corpus")

    def test_sumula_sem_tribunal_nao_casa_stf(self):
        status, _, _ = self.resolve("sumula-145")
        self.assertEqual(status, "off_corpus")

    def test_sumula_stj_nao_casa_acervo_stf(self):
        status, _, _ = self.resolve("sumula-145-stj")
        self.assertEqual(status, "off_corpus")

    def test_sumula_vinculante_nao_casa_serie_1963(self):
        status, _, _ = self.resolve("sumula-vinculante-145-stf")
        self.assertEqual(status, "off_corpus")

    def test_ctb_fora_do_corpus(self):
        status, _, _ = self.resolve("CTB Lei 9.503/1997 art. 261")
        self.assertEqual(status, "off_corpus")

    def test_hint_institucional_sem_norma_e_unparsed(self):
        self.assertIsNone(briefs.parse_hint("susep-seguro-viagem"))
        self.assertIsNone(briefs.parse_hint("gov-br-consumidor"))

    def test_ato_de_agencia_numerado_nao_vira_lei(self):
        # ren-aneel-1000-2021 NÃO é a "Lei 1.000/2021"; prov-cnj-100-2020
        # NÃO é a "Lei 100/2020". O par NNN-AAAA em contexto de agência/
        # conselho fica sem identidade de lei e vai para o conector certo.
        for hint in ("ren-aneel-1000-2021", "res-aneel-1000-2021",
                     "prov-cnj-100-2020", "rn-465-2021-ans",
                     "susep-circular-666-2022"):
            parsed = briefs.parse_hint(hint)
            self.assertIsNone(parsed, hint)
            self.assertEqual(
                briefs.classify_connector(hint, parsed),
                "norma_de_agencia_ou_regulador", hint)

    def test_jurisprudencia_numerada_nao_vira_lei(self):
        for hint in ("stj-tema-1061", "resp-1061-2020"):
            parsed = briefs.parse_hint(hint)
            self.assertIsNone(parsed, hint)
            self.assertEqual(
                briefs.classify_connector(hint, parsed),
                "jurisprudencia_tribunal", hint)


class ConnectorClassification(unittest.TestCase):
    def test_sumula_courts(self):
        parsed = briefs.parse_hint("sumula-479-stj")
        self.assertEqual(
            briefs.classify_connector("sumula-479-stj", parsed),
            "sumula_stj")
        parsed = briefs.parse_hint("sumula-331-tst")
        self.assertEqual(
            briefs.classify_connector("sumula-331-tst", parsed),
            "sumula_tst")

    def test_constituicao(self):
        parsed = briefs.parse_hint("cf-1988-art-5")
        self.assertEqual(
            briefs.classify_connector("cf-1988-art-5", parsed),
            "constituicao_federal")

    def test_agencia(self):
        self.assertEqual(
            briefs.classify_connector("susep-seguro-viagem", None),
            "norma_de_agencia_ou_regulador")

    def test_legislacao_fora_do_corpus(self):
        parsed = briefs.parse_hint("lei-9503-1997-art-261")
        self.assertEqual(
            briefs.classify_connector("lei-9503-1997-art-261", parsed),
            "legislacao_federal_fora_do_corpus")


class DisplayName(unittest.TestCase):
    def test_ordinal_and_suffix(self):
        self.assertEqual(
            briefs.display_name(
                "urn:lex:br:federal:lei:1990-09-11;8078", "art_5"),
            "Lei nº 8.078/1990 (CDC), art. 5º")
        self.assertEqual(
            briefs.display_name(
                "urn:lex:br:federal:lei:1990-09-11;8078", "art_104-B"),
            "Lei nº 8.078/1990 (CDC), art. 104-B")

    def test_sumula(self):
        self.assertEqual(
            briefs.display_name(
                "urn:lex:br:supremo.tribunal.federal:sumula:1963;145", ""),
            "Súmula nº 145 do STF")


class AlertaDeVigencia(unittest.TestCase):
    """O alerta que o redator lê é a última barreira antes de um dispositivo
    sem eficácia virar texto público. `vetado` (corpus.VigenciaStatusVetado,
    ADR de 2026-09-05) não pode se dissolver no genérico "vigência não
    verificada": o veto é um fato provado pela fonte oficial, não uma dúvida
    do corpus."""

    def _alerta(self, **campos):
        rec = {"vigencia_status": "", "vigencia_inicio": "",
               "vigencia_fim": "", "revogado_por": "",
               "last_verified_at": "2026-09-05", "source_url": "",
               "content_sha256": "", "blob_ref": "", "http_status": 200,
               "robots_ok": True, "source_channel": "camara_legin_html"}
        rec.update(campos)
        entrada = briefs.corpus_source_entry(
            "Lei 8.078/1990, art. 109", "corpus_norm",
            "urn:lex:br:federal:lei:1990-09-11;8078", "art_109", rec, None,
            pathlib.Path("/caminho/nao/usado/sem/blob"), {},
            datetime.date(2026, 9, 5), 90, 800, [])
        return entrada["source"].get("alerta_vigencia", "")

    def test_vetado_diz_que_nunca_entrou_em_vigor(self):
        alerta = self._alerta(vigencia_status="vetado")
        self.assertIn("VETADO", alerta)
        self.assertIn("NUNCA entrou em vigor", alerta)

    def test_vetado_nao_cai_no_generico_de_vigencia_nao_verificada(self):
        self.assertNotIn("vigência não verificada",
                         self._alerta(vigencia_status="vetado"))

    def test_revogado_continua_com_o_alerta_de_revogacao(self):
        alerta = self._alerta(vigencia_status="revogado",
                              vigencia_fim="2015-03-16")
        self.assertIn("REVOGADO", alerta)

    def test_nao_verificado_continua_no_alerta_generico(self):
        self.assertIn("vigência não verificada",
                      self._alerta(vigencia_status="nao_verificado"))

    def test_vigente_recente_nao_gera_alerta(self):
        self.assertEqual("", self._alerta(vigencia_status="vigente"))


if __name__ == "__main__":
    unittest.main()
