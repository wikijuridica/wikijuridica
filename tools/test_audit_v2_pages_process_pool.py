#!/usr/bin/env python3
"""Regression tests for deterministic per-shard process-pool orchestration."""

import unittest
from unittest import mock

from tools import audit_v2_pages as audit


class _FakeExecutor:
    def __init__(self, *, map_results=None, map_error=None, **kwargs):
        self.map_results = map_results
        self.map_error = map_error
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def map(self, function, files):
        del function
        self.files = list(files)
        if self.map_error is not None:
            raise self.map_error
        return iter(self.map_results)


class PerShardProcessPoolTests(unittest.TestCase):
    def test_parallel_results_keep_file_order_and_require_full_coverage(self):
        files = ('a.jsonl', 'b.jsonl')
        executor = _FakeExecutor(map_results=(
            ('a.jsonl', {'file': 'a'}),
            ('b.jsonl', {'file': 'b'}),
        ))
        pool = mock.Mock(return_value=executor)
        with mock.patch.object(audit.os, 'cpu_count', return_value=8), \
                mock.patch.object(
                    audit.concurrent.futures, 'ProcessPoolExecutor',
                    pool):
            result = audit._run_per_shard_audits(files, {'intent': {}})
        self.assertEqual(list(result), list(files))
        self.assertEqual(executor.files, list(files))
        pool.assert_called_once_with(
            max_workers=6, initializer=audit._init_shard_worker,
            initargs=({'intent': {}},))

    def test_incomplete_parallel_result_is_discarded_and_rebuilt_serially(self):
        files = ('a.jsonl', 'b.jsonl')
        executor = _FakeExecutor(map_results=(
            ('a.jsonl', {'file': 'parallel-a'}),
        ))
        serial_calls = []

        def fake_audit_file(path, portfolio, collect_pages=False):
            serial_calls.append((path, portfolio, collect_pages))
            return {'file': path, '_page_gram_sets': {'large'}}

        portfolio = {'intent': {}}
        with mock.patch.object(audit.os, 'cpu_count', return_value=8), \
                mock.patch.object(
                    audit.concurrent.futures, 'ProcessPoolExecutor',
                    return_value=executor), \
                mock.patch.object(audit, 'audit_file', fake_audit_file):
            result = audit._run_per_shard_audits(files, portfolio)
        self.assertEqual(list(result), list(files))
        self.assertEqual(
            serial_calls,
            [(path, portfolio, True) for path in files])
        self.assertTrue(all(
            '_page_gram_sets' not in item for item in result.values()))

    def test_pool_exception_is_fail_safe_serial_fallback(self):
        files = ('a.jsonl', 'b.jsonl')
        executor = _FakeExecutor(map_error=RuntimeError('broken pool'))

        def fake_audit_file(path, portfolio, collect_pages=False):
            self.assertTrue(collect_pages)
            return {'file': path, '_page_gram_sets': []}

        with mock.patch.object(audit.os, 'cpu_count', return_value=8), \
                mock.patch.object(
                    audit.concurrent.futures, 'ProcessPoolExecutor',
                    return_value=executor), \
                mock.patch.object(audit, 'audit_file', fake_audit_file):
            result = audit._run_per_shard_audits(files, {})
        self.assertEqual(list(result), list(files))


if __name__ == '__main__':
    unittest.main()
