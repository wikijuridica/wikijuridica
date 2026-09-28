#!/usr/bin/env python3
"""Adversarial coverage for calendar facts in the 12-gram gate."""

import json
import os
import tempfile
import unittest

from tools import audit_v2_pages as auditor


DATE_RANGE = 'de 1º de janeiro de 2021 a 14 de novembro de 2023'
REPEATED_PROSE = (
    'Guarde o protocolo oficial porque o canal somente analisa acidentes '
    'ocorridos de 1º de janeiro de 2021 a 14 de novembro de 2023.')


def page(intent_id, opening):
    suffix = intent_id.rsplit('-', 1)[-1]
    return {
        'intent_id': intent_id,
        'title': f'Janela temporal do pedido residual {suffix}',
        'meta_description': f'Descrição individual {suffix} do pedido residual.',
        'h1': f'Período aplicável ao requerimento {suffix}',
        'opening': opening,
        'sections': [{
            'heading': f'Prova individual do caso {suffix}',
            'text': f'O documento {suffix} comprova o caso específico.',
        }],
        'official_sources': [],
        'internal_link_topics': ['documentos do acidente', 'canal oficial'],
        'lane': 'informativa',
        'word_count': 45,
    }


class CanonicalCalendarRangeNgramTest(unittest.TestCase):

    def test_exact_twelve_token_official_range_is_not_authorial(self):
        tokens = tuple(auditor.words_of(DATE_RANGE))
        self.assertEqual(auditor.NGRAM, len(tokens))
        self.assertTrue(auditor.is_canonical_calendar_range_ngram(tokens))
        record = page('data-a', DATE_RANGE)
        self.assertNotIn(tokens, auditor.exact_page_ngrams(record))
        self.assertNotIn(hash(tokens), auditor.page_ngrams(record))

    def test_date_fragment_with_context_remains_authorial(self):
        tokens = tuple(auditor.words_of(
            'para acidentes ocorridos de 1º de janeiro de 2021 a 14 de'))
        self.assertEqual(auditor.NGRAM, len(tokens))
        self.assertFalse(auditor.is_canonical_calendar_range_ngram(tokens))

    def test_legal_citation_with_month_and_numbers_is_not_a_date_range(self):
        tokens = tuple(auditor.words_of(
            'art 5 de janeiro de 2024 e lei 8 078 1990 vigente'))
        self.assertEqual(auditor.NGRAM, len(tokens))
        self.assertFalse(auditor.is_canonical_calendar_range_ngram(tokens))

    def test_statute_effective_date_is_not_an_authorial_signature(self):
        statement = tuple(auditor.words_of(
            'A Lei 15.040/2024 entrou em vigor em 11 de dezembro de 2025'))
        windows = {
            statement[index:index + auditor.NGRAM]
            for index in range(len(statement) - auditor.NGRAM + 1)}
        self.assertEqual(3, len(windows))
        self.assertTrue(all(
            auditor.is_canonical_effective_date_ngram(tokens)
            for tokens in windows))
        record = page('vigencia-a', ' '.join(statement))
        self.assertTrue(windows.isdisjoint(auditor.exact_page_ngrams(record)))

    def test_generic_effective_date_sentence_keeps_editorial_tokens(self):
        generic = (
            'regra', 'entrou', 'em', 'vigor', 'em', '11', 'de',
            'dezembro', 'de', '2025', 'e', 'prejudica')
        trailing = (
            'entrou', 'em', 'vigor', 'em', '11', 'de', 'dezembro', 'de',
            '2025', 'sem', 'cobertura', 'ampla')
        self.assertFalse(
            auditor.is_canonical_effective_date_ngram(generic))
        self.assertFalse(
            auditor.is_canonical_effective_date_ngram(trailing))

    def test_repeated_editorial_prose_around_date_remains_blocking(self):
        first = page('prosa-a', REPEATED_PROSE)
        second = page('prosa-b', REPEATED_PROSE)
        common = auditor.exact_page_ngrams(first).intersection(
            auditor.exact_page_ngrams(second))
        self.assertTrue(common)
        self.assertTrue(any(
            not auditor.is_canonical_calendar_range_ngram(gram)
            for gram in common))

    def test_numbers_without_calendar_month_do_not_gain_exception(self):
        tokens = tuple(auditor.words_of(
            'a resolução cnsp 457 2022 registra a operação dos sinistros de 2023'))
        self.assertEqual(auditor.NGRAM, len(tokens))
        self.assertFalse(auditor.is_canonical_calendar_range_ngram(tokens))

    def test_local_audit_ignores_date_only_but_flags_repeated_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'calendar.jsonl')
            with open(path, 'w', encoding='utf-8') as handle:
                for record in (page('data-a', DATE_RANGE),
                               page('data-b', DATE_RANGE)):
                    handle.write(json.dumps(record, ensure_ascii=False) + '\n')
            result = auditor.audit_file(path, {})
            self.assertNotIn('ngram_dup', result['defects'])

            with open(path, 'w', encoding='utf-8') as handle:
                for record in (page('prosa-a', REPEATED_PROSE),
                               page('prosa-b', REPEATED_PROSE)):
                    handle.write(json.dumps(record, ensure_ascii=False) + '\n')
            result = auditor.audit_file(path, {})
            self.assertEqual(2, len(result['defects']['ngram_dup']))

    def test_incremental_contract_keeps_fact_and_editorial_results_distinct(self):
        target_shard = 'data/editorial/v2_pages/target.jsonl'
        target_digest = 'd' * 64
        base = {
            'file': target_shard, 'pages': 1, 'active_pages': 1,
            'ok': True, 'defects': {}}
        report = {
            'schema_version': 3,
            'algorithm_fingerprint':
                auditor.INCREMENTAL_ALGORITHM_FINGERPRINT,
            'passed': True,
            'stock_root': 'a' * 64,
            'generation_root': 'b' * 64,
            'target_shard': target_shard,
            'target_digest': target_digest,
            'target_pages': 1,
            'stock_shards_verified': 1,
            'overlay_shards_parsed': 0,
            'overlay_pages': 0,
            'stock_pages_indexed': 1,
            'stock_bytes_hashed': 1024,
            'stock_metadata_scanned': 2,
            'profiles_loaded': 0,
            'candidates_compared': 0,
            'stock_candidates_compared': 0,
            'local_pairs_compared': 0,
            'candidate_terms_read': 1,
            'postings_scanned': 1,
            'inventory_complete': True,
            'candidate_routing_complete': True,
            'local_routing_complete': True,
            'target_snapshot_bound': True,
            'visible_surface_scope_complete': True,
            'visible_surfaces': list(
                auditor.INCREMENTAL_VISIBLE_SURFACES),
            'issues': [],
            'neighbors': [],
            'local_ngram_adjudications': [],
            'publication_allowed': False,
            'index_policy': 'noindex',
        }
        fact_result = auditor.apply_incremental_distinctness(
            dict(base), report, target_shard, target_digest, 1)
        self.assertNotIn('ngram_dup', fact_result['defects'])

        issue = {
            'code': 'editorial_span_duplicate',
            'target_intent_id': 'prosa-target',
            'peer_intent_id': 'prosa-stock',
            'peer_shard': 'data/editorial/v2_pages/stock.jsonl',
            'max_identical_span_tokens': 42,
            'candidate_reasons': ['density'],
        }
        repeated_report = dict(report, passed=False, issues=[issue],
                               candidates_compared=1,
                               stock_candidates_compared=1,
                               profiles_loaded=1)
        repeated_result = auditor.apply_incremental_distinctness(
            dict(base), repeated_report, target_shard, target_digest, 1)
        self.assertIn(
            'editorial_span_duplicate', repeated_result['defects'])


if __name__ == '__main__':
    unittest.main()
