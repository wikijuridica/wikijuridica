#!/usr/bin/env python3
"""Adversarial tests for the fonte_revogada gate in audit_v2_pages.py.

Lei 15.040/2024 (Marco Legal dos Seguros), art. 133, revogou os arts. 757
a 802 da Lei 10.406/2002 (Codigo Civil); vigencia desde dez/2025 (art. 134,
1 ano da publicacao no DOU de 10.12.2024 — conferido no texto oficial do
Planalto). Pagina que ancora fonte ou cita dispositivo dessa faixa sem
tratar a transicao no MESMO registro manda o leitor para regra morta.
"""

import json
import os
import tempfile
import unittest

from tools import audit_v2_pages as auditor


CC_URL = 'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm'
CDC_URL = 'https://www.planalto.gov.br/ccivil_03/leis/l8078compilada.htm'


def source(url, name='Código Civil (Planalto)',
           anchor_claim='O dispositivo disciplina o contrato de seguro.'):
    return {'url': url, 'name': name, 'anchor_claim': anchor_claim}


def page(opening, sources=(), intent_id='lei-cc-art-798', **extra):
    record = {
        'intent_id': intent_id,
        'title': 'Suicídio e seguro de vida: a regra dos dois anos',
        'meta_description': (
            'Entenda a regra dos dois anos para suicídio no seguro de vida '
            'e como a família deve reagir diante da negativa de capital.'),
        'h1': 'Suicídio nos dois primeiros anos do seguro',
        'opening': opening,
        'sections': [
            {'heading': 'A regra objetiva dos dois anos',
             'text': 'A seguradora nega o capital quando o evento ocorre '
                     'no biênio inicial do contrato.'},
        ],
        'official_sources': list(sources),
        'internal_link_topics': ['seguro de vida', 'negativa de cobertura'],
        'lane': 'informativa',
        'word_count': 40,
    }
    record.update(extra)
    return record


class FonteRevogadaDetectionTest(unittest.TestCase):
    """Casos da familia REVOKED_LEGAL_SOURCES (CC arts. 757-802)."""

    def test_source_anchor_revoked_without_transition_flags(self):
        record = page(
            'A negativa de capital por suicídio segue regra objetiva.',
            sources=[source(f'{CC_URL}#art798')])
        self.assertEqual(
            ['official_sources[0].url:art798'],
            auditor.revoked_source_defects(record))

    def test_range_edges_757_and_802_flag(self):
        record = page(
            'O contrato de seguro tem regras próprias.',
            sources=[source(f'{CC_URL}#art757'), source(f'{CC_URL}#art802')])
        self.assertEqual(
            ['official_sources[0].url:art757',
             'official_sources[1].url:art802'],
            auditor.revoked_source_defects(record))

    def test_articles_outside_range_are_clean(self):
        record = page(
            'O art. 756 do Código Civil trata do transporte cumulativo e o '
            'art. 803 do CC abre o capítulo da constituição de renda.',
            sources=[source(f'{CC_URL}#art756'), source(f'{CC_URL}#art803')])
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_text_citation_long_form_flags(self):
        record = page(
            'O art. 798 do Código Civil fixa o prazo de dois anos para a '
            'hipótese de suicídio do segurado.')
        self.assertEqual(
            ['opening:art798'], auditor.revoked_source_defects(record))

    def test_text_citation_short_form_cc_flags(self):
        record = page(
            'Segundo o art. 792 do CC, metade do capital vai ao cônjuge.')
        self.assertEqual(
            ['opening:art792'], auditor.revoked_source_defects(record))

    def test_text_citation_glued_article_flags_without_solid_suffix_match(self):
        record = page(
            'Segundo o art.798 do CC, o biênio regeria o seguro; o '
            'art. 1.798 do Código Civil trata de sucessão.')
        self.assertEqual(
            ['opening:art798'], auditor.revoked_source_defects(record))

    def test_list_citation_collects_only_revoked_numbers(self):
        record = page(
            'Os arts. 756, 760 e 802 do Código Civil aparecem na apólice, '
            'e os artigos 757 a 762 do CC abrem a disciplina do seguro.')
        self.assertEqual(
            ['opening:art757_760_762_802'],
            auditor.revoked_source_defects(record))

    def test_citation_of_other_statute_is_clean(self):
        record = page(
            'O art. 798 do Código de Processo Civil disciplina a execução, '
            'e o art. 42 do Código de Defesa do Consumidor veda o '
            'constrangimento na cobrança.',
            sources=[source(f'{CDC_URL}#art42', name='CDC (Planalto)')])
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_revocation_explained_in_text_is_clean(self):
        record = page(
            'O art. 798 do Código Civil regia o suicídio no seguro de vida, '
            'mas foi revogado pelo Marco Legal dos Seguros.',
            sources=[source(f'{CC_URL}#art798')])
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_new_law_number_in_text_is_clean(self):
        record = page(
            'A Lei 15.040/2024 passou a reger o contrato de seguro, e o '
            'art. 798 do Código Civil deixou de existir.',
            sources=[source(f'{CC_URL}#art798')])
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_na_vigencia_marker_is_clean(self):
        record = page(
            'Contratos celebrados na vigência do art. 798 do Código Civil '
            'seguem regras de transição próprias.')
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_exemption_in_anchor_claim_counts_as_record(self):
        record = page(
            'A regra dos dois anos segue orientando os contratos antigos.',
            sources=[source(
                f'{CC_URL}#art798',
                anchor_claim='Dispositivo revogado pela Lei nº 15.040, de '
                             '2024; rege apenas contratos anteriores.')])
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_direct_denial_does_not_turn_revogado_into_exemption(self):
        record = page(
            'O art. 798 do Código Civil não foi revogado e ainda fixa o '
            'biênio do seguro.')
        self.assertEqual(
            ['opening:art798'], auditor.revoked_source_defects(record))

    def test_meta_negation_does_not_turn_revogado_into_exemption(self):
        record = page(
            'É falso que o art. 798 do Código Civil foi revogado; ele ainda '
            'regeria o seguro.')
        self.assertEqual(
            ['opening:art798'], auditor.revoked_source_defects(record))

    def test_revoking_law_number_cannot_bypass_its_own_denial(self):
        record = page(
            'A Lei 15.040/2024 não revogou o art. 798 do Código Civil.')
        self.assertEqual(
            ['opening:art798'], auditor.revoked_source_defects(record))

    def test_false_transition_in_anchor_claim_does_not_exempt_source(self):
        record = page(
            'A fonte abaixo seria a regra atual.',
            sources=[source(
                f'{CC_URL}#art798',
                anchor_claim='O art. 798 não foi revogado.')])
        self.assertEqual(
            ['official_sources[0].url:art798'],
            auditor.revoked_source_defects(record))

    def test_affirmative_double_negation_still_treats_transition(self):
        record = page(
            'Não é falso que o art. 798 do Código Civil foi revogado; a '
            'regra atual está na legislação nova.',
            sources=[source(f'{CC_URL}#art798')])
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_unrelated_revogada_word_still_exempts_record_level(self):
        # Contrato explicito da regra: a isencao e por REGISTRO (tokens
        # "revogado/revogada/na vigencia/15.040" em qualquer campo textual),
        # nunca por proximidade — pagina que fala de revogacao esta tratando
        # transicao legislativa em algum nivel.
        record = page(
            'A Resolução antiga foi revogada. O art. 798 do Código Civil '
            'fixa a regra dos dois anos.')
        self.assertEqual([], auditor.revoked_source_defects(record))

    def test_evidence_lists_each_field(self):
        record = page(
            'O art. 763 do Código Civil trata da mora no prêmio.',
            sources=[source(f'{CC_URL}#art763'), source(f'{CC_URL}#art764')])
        self.assertEqual(
            ['official_sources[0].url:art763',
             'official_sources[1].url:art764',
             'opening:art763'],
            auditor.revoked_source_defects(record))

    def test_extensibility_contract_of_the_map(self):
        for entry in auditor.REVOKED_LEGAL_SOURCES:
            self.assertIn('law', entry)
            self.assertIn('law_names', entry)
            self.assertIn('articles', entry)
            self.assertIn('revoked_by', entry)
            self.assertIn('exemption_terms', entry)
            self.assertIn('note', entry)
        laws = [entry['law'] for entry in auditor.REVOKED_LEGAL_SOURCES]
        self.assertIn('l10406', laws)
        cc = next(entry for entry in auditor.REVOKED_LEGAL_SOURCES
                  if entry['law'] == 'l10406')
        self.assertIn(757, cc['articles'])
        self.assertIn(802, cc['articles'])
        self.assertNotIn(756, cc['articles'])
        self.assertNotIn(803, cc['articles'])
        self.assertEqual('Lei 15.040/2024, art. 133', cc['revoked_by'])


class FonteRevogadaAuditFileTest(unittest.TestCase):
    """A classe entra no relatorio de defects como as demais (fila review)."""

    def test_audit_file_reports_fonte_revogada(self):
        defective = page(
            'A negativa por suicídio no biênio tem base no dispositivo.',
            sources=[source(f'{CC_URL}#art798')])
        treated = page(
            'O art. 763 do Código Civil foi revogado pela Lei 15.040/2024, '
            'que hoje rege a mora no pagamento do prêmio.',
            sources=[source(f'{CC_URL}#art763')],
            intent_id='lei-cc-art-763',
            title='Art. 763 do Código Civil: mora no prêmio do seguro',
            h1='Mora no prêmio e perda da garantia')
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'fonte-revogada-fixture.jsonl')
            with open(path, 'w', encoding='utf-8') as handle:
                for record in (defective, treated):
                    handle.write(json.dumps(record, ensure_ascii=False))
                    handle.write('\n')
            result = auditor.audit_file(path, {})
        self.assertIn('fonte_revogada', result['defects'])
        self.assertEqual(
            ['lei-cc-art-798:official_sources[0].url:art798'],
            result['defects']['fonte_revogada'])
        self.assertFalse(result['ok'])


if __name__ == '__main__':
    unittest.main()
