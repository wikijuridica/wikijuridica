#!/usr/bin/env python3
"""Regression tests for the LGPD clause gate in audit_v2_pages.py."""

import json
import pathlib
import unittest

from tools import audit_v2_pages as auditor
from tools import lgpd_current_legal_facts as lgpd


ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX = (ROOT / 'internal' / 'v2ingest' / 'testdata' /
          'lgpd_semantic_matrix.json')


class LGPDSemanticGateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(MATRIX.read_text(encoding='utf-8'))['cases']

    def test_shared_semantic_matrix(self):
        for case in self.cases:
            with self.subTest(case=case['name']):
                page = self._page(case)
                visible = '\n'.join(auditor.visible_parts(page))
                reasons = lgpd.reasons(page, visible, auditor.norm_key)
                if 'want_exact' in case:
                    self.assertEqual(
                        sorted(case['want_exact']), sorted(reasons))
                if case.get('want_clear'):
                    self.assertEqual([], reasons)
                for wanted in case.get('want_contains', []):
                    self.assertIn(wanted, reasons)

    def test_canonical_auditor_dispatches_lgpd_gate(self):
        page = {
            'intent_id': 'lgpd-excluir-conta-loja-online',
            'opening': (
                'O art. 19 da LGPD obriga a excluir os dados no prazo de '
                '15 dias.'),
            'sections': [], 'faq': [], 'official_sources': [],
        }
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'article_19_fifteen_days_as_general_deletion_deadline',
            auditor.current_legal_fact_reasons(page))

    def test_article_source_identity_accepts_only_compiled_exact_path(self):
        compiled = (
            'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/'
            'lei/l13709compilado.htm#art19')
        legacy = (
            'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/'
            'lei/l13709.htm#art19')
        self.assertTrue(lgpd._canonical_statute_article(compiled, 'art19'))
        self.assertFalse(lgpd._canonical_statute_article(legacy, 'art19'))
        for source_url in (
            'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/'
            'lei/l13709compilado.htm?art=19#art19',
            'https://www.planalto.gov.br.example/ccivil_03/'
            '_ato2015-2018/2018/lei/l13709compilado.htm#art19',
        ):
            with self.subTest(source_url=source_url):
                self.assertFalse(
                    lgpd._canonical_statute_article(source_url, 'art19'))

    def test_anpd_child_basis_download_identity_is_exact(self):
        path = (
            '/anpd/pt-br/assuntos/noticias/'
            'anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-'
            'de-criancas-e-adolescentes/Enunciado1ANPD.pdf/@@download/file')
        cases = (
            ('official exact download', 'https://www.gov.br' + path, True),
            ('lookalike host', 'https://www.gov.br.example' + path, False),
            ('query', 'https://www.gov.br' + path + '?download=1', False),
            ('fragment', 'https://www.gov.br' + path + '#pagina=1', False),
            ('empty fragment delimiter',
             'https://www.gov.br' + path + '#', False),
            ('path extension', 'https://www.gov.br' + path + '-extra', False),
            ('double trailing slash',
             'https://www.gov.br' + path + '//', False),
        )
        for name, source_url, expected in cases:
            with self.subTest(case=name):
                page = {'official_sources': [{'url': source_url}]}
                self.assertEqual(
                    expected, len(lgpd._child_basis_sources(page)) == 1)

    def test_natural_child_basis_and_consent_stems_stay_fail_closed(self):
        positive_basis = (
            'Crianças e adolescentes podem se apoiar nas hipóteses dos '
            'arts. 7º ou 11 da LGPD, sempre conforme o melhor interesse.')
        self.assertTrue(lgpd._child_basis_anchor_specific(
            positive_basis, auditor.norm_key))
        self.assertTrue(lgpd._child_basis_and_best_interest_visible(
            [auditor.norm_key(positive_basis)]))
        negative_basis = (
            'Crianças e adolescentes não podem se apoiar nas hipóteses dos '
            'arts. 7º ou 11 da LGPD, ainda que se mencione o melhor interesse.',
            'Crianças e adolescentes nunca podem se apoiar nas hipóteses dos '
            'arts. 7º ou 11 da LGPD, ainda que se mencione o melhor interesse.',
            'Crianças e adolescentes jamais podem se apoiar nas hipóteses dos '
            'arts. 7º ou 11 da LGPD, ainda que se mencione o melhor interesse.',
        )
        for text in negative_basis:
            with self.subTest(negative_basis=text):
                self.assertFalse(lgpd._child_basis_anchor_specific(
                    text, auditor.norm_key))
                self.assertFalse(lgpd._child_basis_and_best_interest_visible(
                    [auditor.norm_key(text)]))

        positive_consent = (
            'Quando o consentimento for a base para dados de criança, ele '
            'deve ser específico e destacado, dado por pelo menos um dos '
            'pais ou pelo responsável legal.')
        self.assertTrue(lgpd._article_14_consent_anchor_specific(
            positive_consent, auditor.norm_key))
        self.assertTrue(lgpd._child_consent_requirements_visible(
            [auditor.norm_key(positive_consent)]))
        negative_consent = (
            'Quando o consentimento for a base para dados de criança, ele '
            'deve ser específico, mas não precisa ser destacado, ainda que '
            'dado por um dos pais.',
            'Quando o consentimento for a base para dados de criança, ele '
            'pode ser específico sem ser destacado, ainda que dado por um '
            'dos pais.',
            'Quando o consentimento for a base para dados de criança, ele '
            'pode ser específico sem qualquer destaque, ainda que dado por '
            'um dos pais.',
            'Quando o consentimento for a base para dados de criança, a ANPD '
            'destacou que ele deve ser específico e dado por um dos pais.',
            'Quando o consentimento for a base para dados de criança, a lei '
            'não exige destacar essa manifestação específica de um dos pais.',
        )
        for text in negative_consent:
            with self.subTest(negative_consent=text):
                self.assertFalse(lgpd._article_14_consent_anchor_specific(
                    text, auditor.norm_key))
                self.assertFalse(lgpd._child_consent_requirements_visible(
                    [auditor.norm_key(text)]))

    @staticmethod
    def _page(case):
        return {
            'intent_id': case['intent'],
            'title': case.get('title', ''),
            'opening': case['text'],
            'sections': [],
            'faq': [],
            'official_sources': case.get('sources', []),
        }


if __name__ == '__main__':
    unittest.main()
