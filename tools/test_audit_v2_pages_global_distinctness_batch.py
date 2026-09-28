#!/usr/bin/env python3
"""Regressions for the authenticated global distinctness v3 stream."""

import hashlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools import audit_v2_pages as audit


SHARD_A = 'data/editorial/v2_pages/civil-a.jsonl'
SHARD_B = 'data/editorial/v2_pages/civil-b.jsonl'
DIGEST_A = 'a' * 64
DIGEST_B = 'b' * 64
STOCK_ROOT = 'c' * 64
GENERATION_ROOT = 'd' * 64


def _line(event):
    return (json.dumps(
        event, ensure_ascii=False, separators=(',', ':')).encode('utf-8') +
        b'\n')


def issue_event(left_intent='alvo', right_intent='par',
                right_shard=SHARD_B, code='editorial_span_duplicate'):
    event = {
        'type': 'issue', 'code': code,
        'left': {'shard': SHARD_A, 'intent_id': left_intent},
        'right': {'shard': right_shard, 'intent_id': right_intent},
        'field': 'body',
        'max_identical_span_tokens': 40,
        'candidate_reasons': ['density'],
        'publication_allowed': False, 'index_policy': 'noindex',
    }
    if code == 'ngram_dup_global':
        event.pop('max_identical_span_tokens')
    return event


def local_event():
    return {
        'type': 'local_adjudication', 'shard': SHARD_A,
        'left_intent_id': 'alvo', 'right_intent_id': 'local',
        'max_identical_span_tokens': 12,
        'candidate_reasons': ['density'],
        'publication_allowed': False, 'index_policy': 'noindex',
    }


def valid_payload(results=(), candidate_routing=True, local_routing=True):
    events = [{
        'type': 'header',
        'schema_version': audit.GLOBAL_BATCH_SCHEMA_VERSION,
        'mode': 'global-distinctness-v3-read-only',
        'algorithm_fingerprint': audit.INCREMENTAL_ALGORITHM_FINGERPRINT,
        'batch_fingerprint': audit.GLOBAL_BATCH_ALGORITHM_FINGERPRINT,
        'generation_root': GENERATION_ROOT,
        'stock_root': STOCK_ROOT,
        'stock_shards': 2, 'stock_pages': 3,
        'visible_surfaces': list(audit.INCREMENTAL_VISIBLE_SURFACES),
        'publication_allowed': False, 'index_policy': 'noindex',
    }, {
        'type': 'shard', 'shard': SHARD_A, 'digest': DIGEST_A,
        'active_pages': 2,
        'publication_allowed': False, 'index_policy': 'noindex',
    }, {
        'type': 'shard', 'shard': SHARD_B, 'digest': DIGEST_B,
        'active_pages': 1,
        'publication_allowed': False, 'index_policy': 'noindex',
    }]
    events.extend(results)
    issue_count = sum(event['type'] == 'issue' for event in results)
    local_count = sum(
        event['type'] == 'local_adjudication' for event in results)
    compared_pair_codes = {
        'body_jaccard_near_duplicate', 'editorial_span_duplicate',
        'editorial_repeat_density',
        'distinctness_exact_adjudication_budget_exceeded'}
    compared_pairs = local_count + sum(
        event['type'] == 'issue' and
        event.get('code') in compared_pair_codes
        for event in results)
    prefix = b''.join(_line(event) for event in events)
    footer = {
        'type': 'footer',
        'inventory_complete': True, 'inventory_stable': True,
        'candidate_routing_complete': candidate_routing,
        'local_routing_complete': local_routing,
        'shards_emitted': 2, 'pages_emitted': 3,
        'terms_scanned': 4, 'postings_scanned': 12,
        'candidate_pairs_routed': compared_pairs,
        'candidate_pairs_compared': compared_pairs,
        'issues_emitted': issue_count,
        'local_adjudications_emitted': local_count,
        'passed': (issue_count == 0 and candidate_routing and local_routing),
        'payload_sha256': hashlib.sha256(prefix).hexdigest(),
        'publication_allowed': False, 'index_policy': 'noindex',
    }
    receipt_payload = json.dumps(
        footer, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')
    footer['receipt_sha256'] = hashlib.sha256(receipt_payload).hexdigest()
    return prefix + _line(footer)


def snapshot_contracts():
    return {
        SHARD_A: {
            'digest': DIGEST_A, 'active_pages': 2,
            'active_intents': frozenset(('alvo', 'local')),
        },
        SHARD_B: {
            'digest': DIGEST_B, 'active_pages': 1,
            'active_intents': frozenset(('par',)),
        },
    }


def per_file_results():
    return {
        SHARD_A: {
            'file': SHARD_A, 'defects': {
                'ngram_dup': ['alvo~local', 'local~alvo']},
            'evidence': {'ngram_dup': [
                {'target': 'alvo~local'}, {'target': 'local~alvo'}]},
        },
        SHARD_B: {'file': SHARD_B, 'defects': {}},
    }


class GlobalDistinctnessBatchTests(unittest.TestCase):

    def test_valid_stream_authenticates_zero_counters_and_footer(self):
        batch, error = audit.parse_global_distinctness_batch(valid_payload())
        self.assertIsNone(error)
        self.assertEqual(batch['footer']['candidate_pairs_compared'], 0)
        self.assertEqual(batch['footer']['issues_emitted'], 0)
        self.assertTrue(batch['footer']['passed'])

    def test_local_adjudication_removes_only_local_candidate_and_projects_pair(self):
        batch, error = audit.parse_global_distinctness_batch(
            valid_payload((local_event(), issue_event())))
        self.assertIsNone(error)
        results = per_file_results()
        with mock.patch.object(
                audit, 'query_global_distinctness_batch',
                return_value=(batch, None)):
            audit.apply_global_distinctness_batch(results, snapshot_contracts())
        self.assertNotIn('ngram_dup', results[SHARD_A]['defects'])
        self.assertEqual(
            results[SHARD_A]['defects']['editorial_span_duplicate'],
            ['alvo~par'])
        self.assertEqual(
            results[SHARD_B]['defects']['editorial_span_duplicate'],
            ['par~alvo'])
        self.assertEqual(results[SHARD_A]['distinctness_index']['status'],
                         'ready')
        self.assertNotIn('ngram_dup_global', results[SHARD_A]['defects'])

    def test_explicit_validated_batch_never_queries_mutable_factory_cache(self):
        batch, error = audit.parse_global_distinctness_batch(valid_payload())
        self.assertIsNone(error)
        results = per_file_results()
        with mock.patch.object(
                audit, 'query_global_distinctness_batch',
                side_effect=AssertionError('mutable cache reached')):
            audit.apply_validated_global_distinctness_batch(
                results, snapshot_contracts(), batch)
        self.assertEqual(results[SHARD_A]['distinctness_index']['status'],
                         'ready')

    def test_portfolio_duplicate_intent_fails_closed_in_sorted_private_stock(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            portfolio = root / 'data/editorial/portfolio_v2'
            portfolio.mkdir(parents=True)
            (portfolio / 'a.jsonl').write_text(
                '{"intent_id":"duplicado","page_type":"guia"}\n',
                encoding='utf-8')
            (portfolio / 'b.jsonl').write_text(
                '{"intent_id":"duplicado","page_type":"faq"}\n',
                encoding='utf-8')
            with mock.patch.object(audit, 'ROOT', str(root)), \
                    self.assertRaisesRegex(
                        ValueError, 'intent_id duplicado'):
                audit.load_portfolio()

    def test_unknown_intent_fails_every_shard_without_keyerror_or_removal(self):
        batch, error = audit.parse_global_distinctness_batch(
            valid_payload((issue_event(left_intent='fantasma'),)))
        self.assertIsNone(error)
        results = per_file_results()
        with mock.patch.object(
                audit, 'query_global_distinctness_batch',
                return_value=(batch, None)):
            audit.apply_global_distinctness_batch(results, snapshot_contracts())
        for result in results.values():
            self.assertIn('distinctness_index_unavailable', result['defects'])
            self.assertEqual(result['distinctness_index']['status'],
                             'global_batch_unavailable_fail_closed')
        self.assertIn('ngram_dup', results[SHARD_A]['defects'])

    def test_incomplete_routing_fails_every_shard(self):
        overflow = {
            'type': 'issue',
            'code': 'distinctness_candidate_budget_exceeded',
            'left': {'shard': SHARD_A, 'intent_id': 'alvo'},
            'detail': 'candidates=2001 max=2000',
            'publication_allowed': False, 'index_policy': 'noindex',
        }
        batch, error = audit.parse_global_distinctness_batch(
            valid_payload((overflow,), candidate_routing=False))
        self.assertIsNone(error)
        results = per_file_results()
        with mock.patch.object(
                audit, 'query_global_distinctness_batch',
                return_value=(batch, None)):
            audit.apply_global_distinctness_batch(results, snapshot_contracts())
        self.assertTrue(all(
            'distinctness_index_unavailable' in result['defects']
            for result in results.values()))

    def test_footer_mutation_missing_footer_and_unknown_shard_are_rejected(self):
        payload = valid_payload()
        lines = payload.splitlines(keepends=True)
        footer = json.loads(lines[-1])
        footer['postings_scanned'] = 4
        mutated = b''.join(lines[:-1]) + _line(footer)
        self.assertIsNotNone(
            audit.parse_global_distinctness_batch(mutated)[1])
        self.assertIsNotNone(
            audit.parse_global_distinctness_batch(b''.join(lines[:-1]))[1])
        self.assertIsNotNone(audit.parse_global_distinctness_batch(
            valid_payload((issue_event(right_shard=
                'data/editorial/v2_pages/ghost.jsonl'),)))[1])

    def test_duplicate_local_and_legacy_global_ngram_are_rejected(self):
        self.assertIn('global_batch_local_duplicate',
                      audit.parse_global_distinctness_batch(
                          valid_payload((local_event(), local_event())))[1])
        self.assertIn('global_batch_issue_contract',
                      audit.parse_global_distinctness_batch(
                          valid_payload((issue_event(
                              code='ngram_dup_global'),)))[1])

    def test_pair_budget_requires_peer_and_reasons_are_canonical(self):
        missing_peer = {
            'type': 'issue',
            'code': 'distinctness_exact_adjudication_budget_exceeded',
            'left': {'shard': SHARD_A, 'intent_id': 'alvo'},
            'candidate_reasons': ['density'],
            'publication_allowed': False, 'index_policy': 'noindex',
        }
        self.assertIn('global_batch_issue_contract',
                      audit.parse_global_distinctness_batch(
                          valid_payload((missing_peer,)))[1])
        unordered = issue_event()
        unordered['candidate_reasons'] = ['density', 'intent']
        self.assertIn('global_batch_issue_reasons',
                      audit.parse_global_distinctness_batch(
                          valid_payload((unordered,)))[1])

    def test_issue_contract_failure_reports_closed_discriminant(self):
        identical = issue_event()
        identical['right'] = dict(identical['left'])
        self.assertEqual(
            audit.parse_global_distinctness_batch(
                valid_payload((identical,)))[1],
            'global_batch_issue_contract:4:identical_endpoints')

        malformed = issue_event()
        malformed['left']['intent_id'] = 'Intent Inválido'
        self.assertEqual(
            audit.parse_global_distinctness_batch(
                valid_payload((malformed,)))[1],
            'global_batch_issue_contract:4:left_endpoint_intent')

        schema = issue_event()
        schema['field'] = 'unexpected'
        self.assertEqual(
            audit.parse_global_distinctness_batch(
                valid_payload((schema,)))[1],
            'global_batch_issue_contract:4:schema:'
            'editorial_span_duplicate:unexpected:density:'
            'candidate_reasons,code,field,index_policy,left,'
            'max_identical_span_tokens,publication_allowed,right,type')

    def test_local_adjudication_without_python_candidate_fails_closed(self):
        batch, error = audit.parse_global_distinctness_batch(
            valid_payload((local_event(),)))
        self.assertIsNone(error)
        results = per_file_results()
        results[SHARD_A]['evidence'] = {}
        with mock.patch.object(
                audit, 'query_global_distinctness_batch',
                return_value=(batch, None)):
            audit.apply_global_distinctness_batch(results, snapshot_contracts())
        self.assertIn('ngram_dup', results[SHARD_A]['defects'])
        self.assertIn('distinctness_index_unavailable',
                      results[SHARD_A]['defects'])


if __name__ == '__main__':
    unittest.main()
