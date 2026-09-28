#!/usr/bin/env python3
"""Regression tests for tributario-10 PF/BCN current-law parity."""

import unittest

from tools import audit_v2_pages as auditor


TCU_URL = (
    'https://pesquisa.apps.tcu.gov.br/doc/acordao-completo/990/2026/'
    'Plen%C3%A1rio'
)
INTENT = 'trib-transacao-prejuizo-fiscal'


def page(visible, source=TCU_URL):
    return {
        'intent_id': INTENT,
        'opening': visible,
        'official_sources': [{'url': source}],
    }


class Tributario10PFBCNCurrentLawTest(unittest.TestCase):

    def test_accepts_current_tcu_outcome(self):
        current = page(
            'O Acórdão 990/2026 do TCU reconheceu que o prejuízo fiscal '
            'pode alcançar o principal, até 70% do saldo remanescente '
            'depois dos descontos, quando a modalidade autorizar.')
        self.assertEqual([], auditor.current_legal_fact_reasons(current))

    def test_rejects_superseded_limit_and_spoofed_source(self):
        stale = page(
            'O Acórdão 2.670/2025 limita descontos e prejuízo fiscal '
            'juntos a 65% e impede que o crédito atinja o principal.',
            'https://example.com/' + TCU_URL)
        reasons = auditor.current_legal_fact_reasons(stale)
        self.assertIn(
            'current_legal_fact_source_missing:'
            'tcu_acordao_990_2026_pf_bcn', reasons)
        self.assertIn(
            'current_legal_fact_outcome_missing:'
            'tcu_990_pf_bcn_sequential_70_percent_principal', reasons)

    def test_rejects_inverted_principal_outcome(self):
        inverted = page(
            'O Acórdão 990/2026 do TCU trata do limite de 70% do saldo '
            'remanescente depois dos descontos, mas o prejuízo fiscal '
            'não pode alcançar o principal.')
        reasons = auditor.current_legal_fact_reasons(inverted)
        self.assertIn(
            'current_legal_fact_outcome_missing:'
            'tcu_990_pf_bcn_sequential_70_percent_principal', reasons)


if __name__ == '__main__':
    unittest.main()
