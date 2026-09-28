#!/usr/bin/env python3
"""Regression tests for tributario-09 current-law parity in the Python auditor."""

import unittest

from tools import audit_v2_pages as auditor


STJ_URL = (
    'https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2023/'
    '21032023-Pendencia-fiscal-de-matriz-ou-filial-impede-certidao-negativa-'
    'para-estabelecimento-do-mesmo-grupo.aspx'
)
INTENT = 'trib-certidao-filial-matriz-debito'


def page(visible, source=STJ_URL):
    return {
        'intent_id': INTENT,
        'opening': visible,
        'official_sources': [{'url': source}],
    }


class Tributario09MatrixBranchCurrentLawTest(unittest.TestCase):

    def test_accepts_current_stj_rule(self):
        current = page(
            'No EAREsp 2.025.237, o STJ decidiu que a pendência fiscal da '
            'matriz ou de uma filial impede a CND ou a CPEND de outro '
            'estabelecimento da mesma pessoa jurídica. Matriz e filiais '
            'não têm personalidades jurídicas distintas.')
        self.assertEqual([], auditor.current_legal_fact_reasons(current))

    def test_rejects_spoofed_source_and_superseded_autonomy(self):
        stale = page(
            'Embora o EAREsp 2.025.237 trate da mesma pessoa jurídica, o '
            'débito da filial não impede a certidão negativa da matriz. '
            'Cada estabelecimento pode obter certidão independente.',
            'https://example.com/' + STJ_URL)
        reasons = auditor.current_legal_fact_reasons(stale)
        self.assertIn(
            'current_legal_fact_source_missing:'
            'stj_earesp_2025237_matrix_branch_certificate', reasons)
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'matrix_branch_individual_certificate', reasons)

    def test_allows_qualified_history(self):
        qualified = page(
            'No EAREsp 2.025.237, o STJ decidiu que a pendência fiscal da '
            'matriz ou de uma filial impede a CND de outro estabelecimento '
            'da mesma pessoa jurídica, pois a personalidade jurídica é '
            'única. A tese superada de que o débito da filial não impede a '
            'certidão negativa da matriz não prevalece.')
        self.assertEqual([], auditor.current_legal_fact_reasons(qualified))

    def test_rejects_inverted_outcome_variants(self):
        variants = {
            'question_does_not_supply_outcome':
                'Débito da filial impede a CND da matriz? O EAREsp '
                '2.025.237 discute matriz e filial como a mesma pessoa '
                'jurídica, de personalidade jurídica única. A dívida de '
                'uma não compromete a certidão negativa do outro '
                'estabelecimento.',
            'does_not_contaminate':
                'O EAREsp 2.025.237 trata matriz e filial como a mesma '
                'pessoa jurídica, mas o débito da filial não contamina a '
                'CND da matriz.',
            'does_not_reverberate':
                'No EAREsp 2.025.237, matriz e filial integram a mesma '
                'pessoa jurídica, mas a pendência da matriz não repercute '
                'na certidão negativa da filial.',
            'installment_does_not_authorize_cnd':
                'No EAREsp 2.025.237, matriz e filial são a mesma pessoa '
                'jurídica, mas o débito parcelado da filial não impede a '
                'CND da matriz.',
            'asset_security_does_not_authorize_cnd':
                'No EAREsp 2.025.237, matriz e filial são a mesma pessoa '
                'jurídica, mas a dívida da filial garantida por um bem não '
                'impede a CND da matriz.',
        }
        for name, visible in variants.items():
            with self.subTest(name=name):
                reasons = auditor.current_legal_fact_reasons(page(visible))
                self.assertIn(
                    'current_legal_fact_outcome_missing:'
                    'matrix_branch_unified_fiscal_clearance', reasons)
                self.assertIn(
                    'current_legal_fact_stale_assertion:'
                    'matrix_branch_individual_certificate', reasons)

    def test_allows_extinguished_debt_and_cpend(self):
        current = page(
            'No EAREsp 2.025.237, a pendência fiscal da matriz ou da filial '
            'impede a CND de outro estabelecimento da mesma pessoa '
            'jurídica, cuja personalidade jurídica é única. Depois de o '
            'débito extinto da filial ser baixado, ele não impede a '
            'certidão negativa da matriz. Já o débito parcelado, com '
            'exigibilidade suspensa, não impede a CPEND da pessoa jurídica.')
        self.assertEqual([], auditor.current_legal_fact_reasons(current))


if __name__ == '__main__':
    unittest.main()
