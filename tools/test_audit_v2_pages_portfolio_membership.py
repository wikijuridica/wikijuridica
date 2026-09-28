#!/usr/bin/env python3
"""Regressoes da paridade de membership entre auditor Python e ingest Go."""

import json
import unittest

from tools import audit_v2_pages as auditor


def page(intent_id, **updates):
    record = {
        'intent_id': intent_id,
        'title': 'Como contestar uma cobrança jurídica indevida',
        # Curta de proposito: prova que o auditor continua nos gates
        # editoriais depois de encontrar o orphan.
        'meta_description': 'Descrição curta.',
        'h1': 'Contestação de cobrança indevida passo a passo',
        'opening': (
            'A contestação começa pela identificação do vínculo e pela '
            'preservação dos documentos que explicam a cobrança.'),
        'sections': [{
            'heading': 'Documentos que delimitam a controvérsia',
            'text': (
                'Separe contrato, comprovantes e comunicações para comparar '
                'o valor exigido com a obrigação efetivamente assumida.'),
        }],
        'official_sources': [],
        'internal_link_topics': ['cobrança indevida', 'defesa contratual'],
        'lane': 'informativa',
        'page_type': 'guia_problema',
        'word_count': 42,
    }
    record.update(updates)
    return record


def payload(*records):
    return b''.join(
        json.dumps(record, ensure_ascii=False).encode('utf-8') + b'\n'
        for record in records)


class PortfolioMembershipAuditTest(unittest.TestCase):

    def test_active_orphan_is_blocked_without_hiding_editorial_defects(self):
        result = auditor.audit_file(
            '/not/reopened.jsonl', {},
            snapshot_bytes=payload(page('intent-orfa-ativo')))

        self.assertEqual(
            ['intent-orfa-ativo'],
            result['defects']['intent_fora_portfolio'])
        self.assertEqual(
            ['intent-orfa-ativo'], result['defects']['meta_len'])
        self.assertFalse(result['ok'])

    def test_structural_failure_does_not_hide_active_orphan_membership(self):
        result = auditor.audit_file(
            '/not/reopened.jsonl', {},
            snapshot_bytes=payload(page('intent-orfa-sem-secoes', sections=[])))

        self.assertEqual(
            ['intent-orfa-sem-secoes'],
            result['defects']['intent_fora_portfolio'])
        self.assertEqual(
            ['intent-orfa-sem-secoes'], result['defects']['estrutura'])

    def test_known_active_intent_does_not_receive_membership_blocker(self):
        intent_id = 'intent-canonico'
        portfolio = {
            intent_id: {'page_type': 'guia_problema', 'lane': 'informativa'},
        }
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(page(intent_id)))

        self.assertNotIn('intent_fora_portfolio', result['defects'])
        self.assertIn('meta_len', result['defects'])

    def test_active_page_public_controls_fail_closed_with_exact_types(self):
        intent_id = 'intent-privado'
        portfolio = {
            intent_id: {'page_type': 'guia_problema', 'lane': 'informativa'},
        }
        mutations = {
            'public': True,
            'publication_allowed': True,
            'publication_candidate': True,
            'render_allowed': True,
            'sitemap_allowed': True,
            'indexable': True,
            'approval': True,
            'publicly_indexable': True,
            'manifest_allowed': True,
            'index_policy': 'index',
            'public_path': '/consumidor/cobranca/',
            'public_numeric_false_alias': ('public', 0),
            'public_null_alias': ('public', None),
            'index_policy_null_alias': ('index_policy', None),
            'public_path_null_alias': ('public_path', None),
            'public_path_whitespace_alias': ('public_path', '  '),
        }
        for case, mutation in mutations.items():
            if isinstance(mutation, tuple):
                field, value = mutation
            else:
                field, value = case, mutation
            with self.subTest(case=case):
                result = auditor.audit_file(
                    '/not/reopened.jsonl', portfolio,
                    snapshot_bytes=payload(page(intent_id, **{field: value})))

                self.assertEqual(
                    [f'{intent_id}:{field}'],
                    result['defects']['public_state_open'])
                self.assertFalse(result['ok'])

    def test_absent_or_exact_closed_public_controls_remain_private(self):
        intent_id = 'intent-privado-fechado'
        portfolio = {
            intent_id: {'page_type': 'guia_problema', 'lane': 'informativa'},
        }
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(page(
                intent_id, public=False, publication_allowed=False,
                publication_candidate=False, render_allowed=False,
                sitemap_allowed=False, indexable=False, approval=False,
                publicly_indexable=False, manifest_allowed=False,
                index_policy='noindex', public_path='')))

        self.assertNotIn('public_state_open', result['defects'])

    def test_tombstone_cannot_bypass_exact_private_controls(self):
        intent_id = 'intent-tombstone-privado'
        result = auditor.audit_file(
            '/not/reopened.jsonl', {},
            snapshot_bytes=payload({
                'intent_id': intent_id,
                'skipped': True,
                'skip_reason': 'fonte oficial ainda não localizada',
                'publication_allowed': 0,
                'public_path': ' ',
            }))

        self.assertEqual(
            [f'{intent_id}:public_path',
             f'{intent_id}:publication_allowed'],
            result['defects']['public_state_open'])
        self.assertFalse(result['ok'])

    def test_known_intent_with_wrong_page_type_is_blocked(self):
        intent_id = 'intent-tipo-divergente'
        portfolio = {
            intent_id: {'page_type': 'guia_problema', 'lane': 'comercial'},
        }
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(page(
                intent_id, page_type='guide', lane='comercial')))

        self.assertEqual(
            [intent_id], result['defects']['portfolio_page_type_mismatch'])
        self.assertNotIn('portfolio_lane_mismatch', result['defects'])
        self.assertFalse(result['ok'])

    def test_known_intent_with_wrong_lane_is_blocked(self):
        intent_id = 'intent-lane-divergente'
        portfolio = {
            intent_id: {'page_type': 'guia_problema', 'lane': 'comercial'},
        }
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(page(
                intent_id, page_type='guia_problema', lane='informativa')))

        self.assertEqual(
            [intent_id], result['defects']['portfolio_lane_mismatch'])
        self.assertNotIn('portfolio_page_type_mismatch', result['defects'])
        self.assertFalse(result['ok'])

    def test_materialized_taxonomy_must_match_portfolio(self):
        intent_id = 'intent-taxonomia-divergente'
        portfolio = {intent_id: {
            'page_type': 'guia_problema', 'lane': 'comercial',
            'practice_area': 'consumidor', 'family': 'cobranca',
        }}
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(page(
                intent_id, practice_area='Direito do Consumidor',
                family='contratos', lane='comercial')))

        self.assertEqual(
            [intent_id],
            result['defects']['portfolio_practice_area_mismatch'])
        self.assertEqual(
            [intent_id], result['defects']['portfolio_family_mismatch'])
        self.assertFalse(result['ok'])

    def test_known_intent_may_omit_legacy_derived_metadata(self):
        intent_id = 'intent-legado-sem-metadata'
        portfolio = {intent_id: {
            'page_type': 'guia_problema', 'lane': 'comercial',
            'practice_area': 'consumidor', 'family': 'cobranca',
        }}
        record = page(
            intent_id, practice_area='consumidor', family='cobranca')
        for field in ('page_type', 'lane', 'practice_area', 'family'):
            record.pop(field)
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(record))

        self.assertNotIn('portfolio_page_type_mismatch', result['defects'])
        self.assertNotIn('portfolio_lane_mismatch', result['defects'])
        self.assertNotIn(
            'portfolio_practice_area_mismatch', result['defects'])
        self.assertNotIn('portfolio_family_mismatch', result['defects'])

    def test_explicit_null_metadata_does_not_masquerade_as_legacy_absence(self):
        intent_id = 'intent-metadata-nula'
        portfolio = {intent_id: {
            'page_type': 'guia_problema', 'lane': 'comercial',
            'practice_area': 'consumidor', 'family': 'cobranca',
        }}
        result = auditor.audit_file(
            '/not/reopened.jsonl', portfolio,
            snapshot_bytes=payload(page(
                intent_id, page_type=None, lane=None,
                practice_area=None, family=None)))

        self.assertEqual(
            [intent_id], result['defects']['portfolio_page_type_mismatch'])
        self.assertEqual(
            [intent_id], result['defects']['portfolio_lane_mismatch'])
        self.assertEqual(
            [intent_id],
            result['defects']['portfolio_practice_area_mismatch'])
        self.assertEqual(
            [intent_id], result['defects']['portfolio_family_mismatch'])
        self.assertFalse(result['ok'])

    def test_valid_tombstone_may_preserve_retired_intent_outside_portfolio(self):
        record = {
            'intent_id': 'intent-retirado',
            'skipped': True,
            'skip_reason': 'Consolidado em intenção canônica revisada.',
        }
        result = auditor.audit_file(
            '/not/reopened.jsonl', {}, snapshot_bytes=payload(record))

        self.assertNotIn('intent_fora_portfolio', result['defects'])
        self.assertEqual(['intent-retirado'], result['defects']['skipped'])
        self.assertTrue(result['ok'])


if __name__ == '__main__':
    unittest.main()
