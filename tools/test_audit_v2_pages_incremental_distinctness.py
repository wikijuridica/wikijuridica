#!/usr/bin/env python3
"""Regressões da ponte read-only auditor -> índice incremental."""

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import unittest
from unittest import mock

from tools import audit_v2_pages as audit


TARGET_SHARD = 'data/editorial/v2_pages/bancario-01.jsonl'
TARGET_DIGEST = 'b' * 64
STOCK_ROOT = 'a' * 64
GENERATION_ROOT = 'c' * 64


def valid_report(**updates):
    report = {
        'schema_version': 3,
        'passed': True,
        'stock_root': STOCK_ROOT,
        'generation_root': GENERATION_ROOT,
        'algorithm_fingerprint': audit.INCREMENTAL_ALGORITHM_FINGERPRINT,
        'target_shard': TARGET_SHARD,
        'target_digest': TARGET_DIGEST,
        'target_pages': 1,
        'stock_shards_verified': 10,
        'overlay_shards_parsed': 0,
        'overlay_pages': 0,
        'stock_pages_indexed': 100,
        'stock_bytes_hashed': 33_000_000,
        'stock_metadata_scanned': 11,
        'profiles_loaded': 1,
        'candidates_compared': 1,
        'stock_candidates_compared': 1,
        'local_pairs_compared': 0,
        'candidate_terms_read': 10,
        'postings_scanned': 20,
        'inventory_complete': True,
        'candidate_routing_complete': True,
        'local_routing_complete': True,
        'target_snapshot_bound': True,
        'visible_surface_scope_complete': True,
        'visible_surfaces': list(audit.INCREMENTAL_VISIBLE_SURFACES),
        'issues': [],
        'neighbors': [],
        'local_ngram_adjudications': [],
        'publication_allowed': False,
        'index_policy': 'noindex',
    }
    report.update(updates)
    return report


def valid_envelope(report=None, **updates):
    envelope = {
        'mode': 'incremental-distinctness-read-only',
        'scope': 'shard',
        'run_key': 'v2-distinctness',
        'publication_allowed': False,
        'index_policy': 'noindex',
        'distinctness': valid_report() if report is None else report,
    }
    envelope.update(updates)
    return envelope


class FakeProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode


class IncrementalDistinctnessBridgeTests(unittest.TestCase):

    def test_exact_adjudication_replaces_bare_12gram_blocker(self):
        result = {
            'ok': False,
            'defects': {
                'ngram_dup': ['alvo~par'],
                'fonte_nao_verificada': ['outro'],
            },
            'evidence': {
                'ngram_dup': [{
                    'target': 'alvo~par',
                    'phrase': 'frase antes bloqueante'}],
            },
        }
        issues = [{
            'code': 'editorial_span_duplicate',
            'target_intent_id': 'alvo',
            'peer_intent_id': 'par',
            'peer_shard': 'data/editorial/v2_pages/civil-01.jsonl',
            'max_identical_span_tokens': 42,
            'candidate_reasons': ['density'],
        }]
        report = valid_report(
            passed=False, issues=issues,
            local_ngram_adjudications=[{
                'left_intent_id': 'alvo',
                'right_intent_id': 'par',
                'max_identical_span_tokens': 42,
                'candidate_reasons': ['density'],
            }])
        updated = audit.apply_incremental_distinctness(
            result, report, TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertNotIn('ngram_dup', updated['defects'])
        self.assertNotIn('ngram_dup', updated.get('evidence', {}))
        self.assertEqual(
            updated['defects']['editorial_span_duplicate'], ['alvo~par'])
        self.assertEqual(updated['candidates_compared'], 1)
        self.assertEqual(updated['profiles_loaded'], 1)
        self.assertNotIn('stock_pages_compared', updated)
        self.assertEqual(updated['stock_pages_indexed'], 100)
        self.assertFalse(updated['ok'])
        self.assertFalse(
            updated['distinctness_index']['publication_allowed'])

    def test_candidate_without_exact_blocker_is_nonblocking_neighbor(self):
        result = {
            'ok': False,
            'defects': {'ngram_dup': ['alvo~par']},
            'evidence': {'ngram_dup': [{'phrase': 'doze tokens'}]},
        }
        neighbor = {
            'target_intent_id': 'alvo',
            'peer_intent_id': 'par',
            'peer_shard': 'data/editorial/v2_pages/civil-01.jsonl',
            'body_jaccard': 0.12,
            'max_identical_span_tokens': 12,
            'target_repeated_density': 0.0,
            'peer_repeated_density': 0.0,
            'candidate_reasons': ['density'],
        }
        report = valid_report(
            neighbors=[neighbor], local_ngram_adjudications=[{
                'left_intent_id': 'alvo',
                'right_intent_id': 'par',
                'max_identical_span_tokens': 12,
                'candidate_reasons': ['density'],
            }])
        updated = audit.apply_incremental_distinctness(
            result, report, TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertTrue(updated['ok'])
        self.assertEqual(updated['defects'], {})
        self.assertEqual(len(updated['distinctness_neighbors']), 1)

    def test_unadjudicated_local_ngram_remains_fail_closed(self):
        result = {
            'ok': False,
            'defects': {'ngram_dup': ['alvo~par']},
            'evidence': {'ngram_dup': [{
                'target': 'alvo~par', 'phrase': 'doze tokens'}]},
        }
        updated = audit.apply_incremental_distinctness(
            result, valid_report(), TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertEqual(updated['defects']['ngram_dup'], ['alvo~par'])
        self.assertIn('ngram_dup', updated['evidence'])
        self.assertFalse(updated['ok'])

    def test_malformed_issue_fails_closed_without_removing_ngram(self):
        result = {
            'ok': False,
            'defects': {'ngram_dup': ['alvo~par']},
            'evidence': {'ngram_dup': [{'phrase': 'doze tokens'}]},
        }
        report = valid_report(passed=False, issues=[{}])
        updated = audit.apply_incremental_distinctness(
            result, report, TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertFalse(updated['ok'])
        self.assertEqual(updated['defects']['ngram_dup'], ['alvo~par'])
        self.assertIn('ngram_dup', updated['evidence'])
        self.assertIn(
            'distinctness_index_invalid_report', updated['defects'])

    def test_contract_carries_overlay_without_opening_public_flags(self):
        result = {'ok': True, 'defects': {}}
        report = valid_report(
            overlay_shards_parsed=2, overlay_pages=20,
            stock_pages_indexed=120, stock_metadata_scanned=13)
        updated = audit.apply_incremental_distinctness(
            result, report, TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertEqual(
            updated['distinctness_index']['overlay_shards_parsed'], 2)
        self.assertEqual(updated['distinctness_index']['overlay_pages'], 20)
        self.assertFalse(updated['distinctness_index']['publication_allowed'])

    def test_audit_file_consumes_supplied_snapshot_without_reopening_path(self):
        with mock.patch.object(
                audit, 'read_target_snapshot',
                side_effect=AssertionError('path reopened')):
            result = audit.audit_file(
                '/path/that/does/not/exist.jsonl', {}, snapshot_bytes=b'\n')
        self.assertTrue(result['ok'])
        self.assertEqual(result['pages'], 0)

    def test_snapshot_parser_does_not_split_unicode_line_separator_in_json(self):
        payload = json.dumps(
            {'intent_id': 'alvo', 'opening': 'antes\u2028depois'},
            ensure_ascii=False).encode('utf-8') + b'\n'
        result = audit.audit_file('/not/reopened.jsonl', {},
                                  snapshot_bytes=payload)
        self.assertEqual(result['pages'], 1)
        self.assertNotIn('json_invalido', result['defects'])

    def test_snapshot_digest_race_fails_closed_and_keeps_local_ngram(self):
        original = b'original shard snapshot\n'
        replacement_digest = hashlib.sha256(b'replaced shard\n').hexdigest()
        report = valid_report(target_digest=replacement_digest)
        focal = {
            'file': TARGET_SHARD,
            'pages': 1,
            'active_pages': 1,
            'ok': False,
            'defects': {'ngram_dup': ['alvo~par']},
            'evidence': {'ngram_dup': [{'phrase': 'doze tokens'}]},
        }
        with mock.patch.object(
                audit, 'canonical_incremental_target_shard',
                return_value=TARGET_SHARD), mock.patch.object(
                    audit, 'read_target_snapshot', return_value=original), \
                mock.patch.object(audit, 'load_portfolio', return_value={}), \
                mock.patch.object(
                    audit, 'audit_file', return_value=focal), \
                mock.patch.object(
                    audit, 'query_incremental_distinctness',
                    return_value=(report, None)):
            updated = audit.audit_against_stock('/synthetic/target.jsonl')
        self.assertFalse(updated['ok'])
        self.assertEqual(updated['defects']['ngram_dup'], ['alvo~par'])
        self.assertIn(
            'distinctness_index_invalid_report', updated['defects'])
        self.assertEqual(
            updated['distinctness_index']['reason'],
            'target_digest_sha256_or_snapshot_mismatch')

    def test_envelope_rejects_contradictions_types_and_public_flags(self):
        cases = {
            'mode': valid_envelope(mode='legacy-shadow-read-only'),
            'scope': valid_envelope(scope='all'),
            'run_key': valid_envelope(run_key='other'),
            'outer_public': valid_envelope(publication_allowed=True),
            'schema_bool': valid_envelope(valid_report(schema_version=True)),
            'digest': valid_envelope(valid_report(target_digest='A' * 64)),
            'root': valid_envelope(valid_report(stock_root='not-a-sha')),
            'generation_root': valid_envelope(valid_report(
                generation_root='not-a-sha')),
            'algorithm': valid_envelope(valid_report(
                algorithm_fingerprint='0' * 64)),
            'shard': valid_envelope(valid_report(
                target_shard='data/editorial/v2_pages/../escape.jsonl')),
            'passed_type': valid_envelope(valid_report(passed=1)),
            'passed_contradiction': valid_envelope(valid_report(
                passed=False, issues=[])),
            'negative_counter': valid_envelope(valid_report(target_pages=-1)),
            'bool_counter': valid_envelope(valid_report(profiles_loaded=True)),
            'counter_sum': valid_envelope(valid_report(
                candidates_compared=2)),
            'issues_type': valid_envelope(valid_report(issues={})),
            'neighbors_type': valid_envelope(valid_report(neighbors={})),
            'inner_public': valid_envelope(valid_report(
                publication_allowed=True)),
            'inventory_incomplete': valid_envelope(valid_report(
                stock_shards_verified=9)),
            'target_pages_snapshot': valid_envelope(valid_report(
                target_pages=2)),
            'surface_scope': valid_envelope(valid_report(
                visible_surface_scope_complete=False)),
            'routing_without_issue': valid_envelope(valid_report(
                passed=False, candidate_routing_complete=False,
                issues=[])),
            'local_adjudication_shape': valid_envelope(valid_report(
                local_ngram_adjudications=[{
                    'left_intent_id': 'par',
                    'right_intent_id': 'alvo',
                    'max_identical_span_tokens': 12,
                    'candidate_reasons': ['density'],
                }])),
        }
        for label, payload in cases.items():
            with self.subTest(label=label):
                self.assertIsNotNone(
                    audit.incremental_envelope_contract_error(
                        payload, TARGET_SHARD, TARGET_DIGEST, 1))

    def test_neighbor_at_each_blocking_threshold_requires_matching_issue(self):
        base_neighbor = {
            'target_intent_id': 'alvo',
            'peer_intent_id': 'par',
            'peer_shard': 'data/editorial/v2_pages/civil-01.jsonl',
            'body_jaccard': 0.70,
            'max_identical_span_tokens': 40,
            'target_repeated_density': 0.15,
            'peer_repeated_density': 0.0,
            'candidate_reasons': ['density'],
        }
        report = valid_report(neighbors=[base_neighbor])
        error = audit.incremental_report_contract_error(
            report, TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertIn('neighbor_blocker_without_issue', error)

        issues = []
        for code in ('body_jaccard_near_duplicate',
                     'editorial_span_duplicate',
                     'editorial_repeat_density'):
            issues.append({
                'code': code,
                'target_intent_id': 'alvo',
                'peer_intent_id': 'par',
                'peer_shard': base_neighbor['peer_shard'],
                'body_jaccard': 0.70,
                'max_identical_span_tokens': 40,
                'target_repeated_density': 0.15,
                'peer_repeated_density': 0.0,
                'candidate_reasons': ['density'],
            })
        report = valid_report(
            passed=False, neighbors=[base_neighbor], issues=issues)
        self.assertIsNone(audit.incremental_report_contract_error(
            report, TARGET_SHARD, TARGET_DIGEST, 1))

    def test_active_page_counter_excludes_tombstones(self):
        active = {'intent_id': 'ativa', 'opening': 'texto ativo'}
        tombstone = {
            'intent_id': 'removida', 'skipped': True,
            'skip_reason': 'duplicate_intent_consolidated'}
        payload = b''.join(
            json.dumps(value).encode('utf-8') + b'\n'
            for value in (active, tombstone))
        result = audit.audit_file(
            '/not/reopened.jsonl', {}, snapshot_bytes=payload)
        self.assertEqual(result['pages'], 2)
        self.assertEqual(result['active_pages'], 1)

    def test_query_rejects_preamble_and_multiple_json_documents(self):
        encoded = json.dumps(valid_envelope()).encode('utf-8')
        for label, stdout in (
                ('preamble', b'build log\n' + encoded),
                ('multiple', encoded + b'\n{}\n')):
            with self.subTest(label=label), mock.patch.object(
                    audit, 'cached_factory_binary_error', return_value=None), \
                    mock.patch.object(
                        audit.subprocess, 'Popen',
                        return_value=FakeProcess()) as popen, \
                    mock.patch.object(
                        audit, '_read_process_output_bounded',
                        return_value=(stdout, b'', None)):
                report, reason = audit.query_incremental_distinctness(
                    TARGET_SHARD, TARGET_DIGEST, 1)
                self.assertIsNone(report)
                self.assertIn('incremental_query_invalid_json', reason)
                command = popen.call_args.args[0]
                self.assertEqual(command[0], audit.FACTORY_BINARY)
                self.assertNotIn('tools/factory', command[0])

    def test_query_accepts_one_strict_document(self):
        encoded = json.dumps(valid_envelope()).encode('utf-8')
        with mock.patch.object(
                audit, 'cached_factory_binary_error', return_value=None), \
                mock.patch.object(
                    audit.subprocess, 'Popen',
                    return_value=FakeProcess()), \
                mock.patch.object(
                    audit, '_read_process_output_bounded',
                    return_value=(encoded, b'', None)):
            report, reason = audit.query_incremental_distinctness(
                TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertIsNone(reason)
        self.assertEqual(report['target_digest'], TARGET_DIGEST)

    def test_missing_or_stale_binary_never_starts_subprocess(self):
        with mock.patch.object(
                audit, 'cached_factory_binary_error',
                return_value='cached_factory_stale:cmd/factory/main.go'), \
                mock.patch.object(audit.subprocess, 'Popen') as popen:
            report, reason = audit.query_incremental_distinctness(
                TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertIsNone(report)
        self.assertIn('cached_factory_stale', reason)
        popen.assert_not_called()

    def test_query_enforces_output_limit(self):
        stdout = b'x' * (audit.FACTORY_QUERY_STDOUT_MAX_BYTES + 1)
        with mock.patch.object(
                audit, 'cached_factory_binary_error', return_value=None), \
                mock.patch.object(
                    audit.subprocess, 'Popen',
                    return_value=FakeProcess()), \
                mock.patch.object(
                    audit, '_read_process_output_bounded',
                    return_value=(stdout, b'', 'output_limit')):
            report, reason = audit.query_incremental_distinctness(
                TARGET_SHARD, TARGET_DIGEST, 1)
        self.assertIsNone(report)
        self.assertEqual(reason, 'incremental_query_output_limit_exceeded')

    def test_bounded_reader_stops_at_cap_and_reaps_process(self):
        process = subprocess.Popen(
            [sys.executable, '-c',
             'import os\nwhile True: os.write(1, b"x" * 65536)'],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0)
        stdout, stderr, status = audit._read_process_output_bounded(
            process, 2, 4096, 4096)
        self.assertEqual(status, 'output_limit')
        self.assertLessEqual(len(stdout), 4097)
        self.assertLessEqual(len(stderr), 4097)
        self.assertIsNotNone(process.poll())

    def test_bounded_reader_drains_stderr_without_deadlock(self):
        process = subprocess.Popen(
            [sys.executable, '-c',
             'import os\nos.write(2, b"e" * 100000)\n'
             'os.write(1, b"ok")'],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0)
        stdout, stderr, status = audit._read_process_output_bounded(
            process, 2, 200000, 200000)
        self.assertIsNone(status)
        self.assertEqual(stdout, b'ok')
        self.assertEqual(len(stderr), 100000)
        self.assertEqual(process.returncode, 0)

    def test_bounded_reader_timeout_reaps_without_communicate(self):
        process = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(10)'],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0)
        stdout, stderr, status = audit._read_process_output_bounded(
            process, 0.05, 4096, 4096)
        self.assertEqual((stdout, stderr, status), (b'', b'', 'timeout'))
        self.assertIsNotNone(process.poll())

    def test_bounded_reader_timeout_kills_descendant_process_group(self):
        process = subprocess.Popen(
            [sys.executable, '-c',
             'import subprocess, sys, time\n'
             'child = subprocess.Popen([sys.executable, "-c", '
             '"import time; time.sleep(30)"])\n'
             'print(child.pid, flush=True)\n'
             'time.sleep(30)'],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, start_new_session=True)
        stdout, _, status = audit._read_process_output_bounded(
            process, 0.2, 4096, 4096)
        self.assertEqual(status, 'timeout')
        child_pid = int(stdout.strip())
        child_status = pathlib.Path(f'/proc/{child_pid}/stat')
        deadline = time.monotonic() + 1
        state = None
        while time.monotonic() < deadline:
            try:
                state = child_status.read_text().split()[2]
            except (FileNotFoundError, ProcessLookupError):
                state = None
                break
            if state == 'Z':
                break
            time.sleep(0.005)
        if state is not None:
            # A killed orphan can remain a zombie briefly until PID 1 reaps it;
            # it must never remain runnable or sleeping.
            self.assertEqual(state, 'Z')
        else:
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)


if __name__ == '__main__':
    unittest.main()
