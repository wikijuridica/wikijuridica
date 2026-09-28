#!/usr/bin/env python3
"""Regressão para escapes de controle que vazam à prosa pública."""

import unittest

from tools import audit_v2_pages as auditor


class LiteralControlEscapeTest(unittest.TestCase):

    def test_rejects_decoded_literal_backslash_controls(self):
        for value, expected in (
                (r'primeiro parágrafo.\n\nsegundo parágrafo.', r'\n'),
                (r'coluna\tvalor', r'\t'),
                (r'linha\rretorno', r'\r')):
            with self.subTest(value=value):
                self.assertEqual(expected, auditor.literal_control_escape(value))

    def test_accepts_real_whitespace_decoded_from_canonical_json(self):
        for value in ('primeiro\n\nsegundo', 'coluna\tvalor', 'linha\rretorno'):
            with self.subTest(value=repr(value)):
                self.assertEqual('', auditor.literal_control_escape(value))

    def test_scans_every_public_visible_slot(self):
        page = {
            'title': 'Título natural',
            'meta_description': 'Descrição natural',
            'h1': 'Cabeçalho natural',
            'opening': 'Abertura natural.',
            'sections': [{'heading': 'Seção', 'text': r'Texto\n\nvazado'}],
            'faq': [{'q': 'Pergunta?', 'a': 'Resposta natural.'}],
        }
        findings = [
            (field, auditor.literal_control_escape(value))
            for field, value in auditor.labeled_visible_parts(page)
            if auditor.literal_control_escape(value)
        ]
        self.assertEqual([('sections[0].text', r'\n')], findings)


if __name__ == '__main__':
    unittest.main()
