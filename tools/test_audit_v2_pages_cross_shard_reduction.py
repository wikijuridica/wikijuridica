#!/usr/bin/env python3
"""Byte-identity proof for the cross-shard body-reduction of ``_audit_global``.

The global audit used to retain every shard's ``_loaded_pages`` (full prose
bodies of every active page) in the parent process simultaneously — O(total
corpus) peak memory that OOMs at 10M pages. ``_reduce_shard_for_cross_shard``
collapses each shard to only the two projections the cross-shard phase reads:
``(intent, line)`` tuples for active pages and whole superseded tombstones.

This test locks the reduction to be verdict-identical: for a battery of
adversarial shard fixtures it recomputes the five quantities the cross-shard
loop derives (active_intents frozenset, supersession order, per-intent counter,
per-intent last line, total_pages) both the LEGACY way (iterating the original
``_loaded_pages``) and the NEW way (iterating the reduced entries) and asserts
they are equal object-for-object and order-for-order.
"""

import collections
import copy
import unittest

from tools import audit_v2_pages as audit


def _legacy_cross_shard(files, per_shard_results):
    """Reference implementation: the pre-reduction cross-shard projection."""
    active_intents_by_file = {}
    supersessions = []
    active_by_file_intent = collections.Counter()
    active_line_by_file_intent = {}
    total_pages = 0
    for f in files:
        res = per_shard_results[f]
        loaded_pages = res['_loaded_pages']
        loaded_page_lines = res['_loaded_page_lines']
        active_intents_by_file[res['file']] = frozenset(
            (page.get('intent_id') or '').strip()
            for page in loaded_pages if not page.get('skipped'))
        for p, line_number in zip(loaded_pages, loaded_page_lines):
            if p.get('skipped'):
                if p.get('superseded_by') is not None:
                    supersessions.append((res['file'], line_number, id(p)))
                continue
            total_pages += 1
            intent = (p.get('intent_id') or '').strip()
            if intent:
                active_by_file_intent[(res['file'], intent)] += 1
                active_line_by_file_intent[(res['file'], intent)] = line_number
    return (active_intents_by_file, supersessions, active_by_file_intent,
            dict(active_line_by_file_intent), total_pages)


def _new_cross_shard(files, per_shard_results):
    """Post-reduction cross-shard projection mirroring ``_audit_global``."""
    active_intents_by_file = {}
    supersessions = []
    active_by_file_intent = collections.Counter()
    active_line_by_file_intent = {}
    total_pages = 0
    for f in files:
        res = per_shard_results[f]
        audit._reduce_shard_for_cross_shard(res)
        active_entries = res.pop('_active_entries')
        superseded_entries = res.pop('_superseded_entries')
        active_intents_by_file[res['file']] = frozenset(
            intent for intent, _line in active_entries)
        for line_number, p in superseded_entries:
            supersessions.append((res['file'], line_number, id(p)))
        for intent, line_number in active_entries:
            total_pages += 1
            if intent:
                active_by_file_intent[(res['file'], intent)] += 1
                active_line_by_file_intent[(res['file'], intent)] = line_number
    return (active_intents_by_file, supersessions, active_by_file_intent,
            dict(active_line_by_file_intent), total_pages)


def _tombstone(intent, target):
    return {
        'intent_id': intent, 'skipped': True, 'superseded_by': target,
        'skip_reason': 'duplicate_intent_consolidated',
    }


def _fixture_shards():
    """Adversarial shards: empty intent, duplicate intent (last-line-wins),
    superseded vs. non-superseded tombstones, interleaving, and body prose that
    must never influence the verdict."""
    return {
        'a.jsonl': {
            'file': 'a',
            '_loaded_pages': [
                {'intent_id': 'div-consensual', 'body': 'x' * 5000},
                {'intent_id': '  div-consensual  ', 'body': 'y' * 5000},
                _tombstone('div-litigioso', 'b.jsonl'),
                {'intent_id': '', 'body': 'z' * 5000},
                {'skipped': True, 'superseded_by': None},
                {'intent_id': 'guarda', 'body': 'w' * 5000},
            ],
            '_loaded_page_lines': [1, 2, 3, 4, 5, 6],
            '_snapshot_digest': 'deadbeef',
            'active_pages': 3,
        },
        'b.jsonl': {
            'file': 'b',
            '_loaded_pages': [
                _tombstone('div-consensual', 'a.jsonl'),
                {'intent_id': 'pensao', 'body': 'p' * 5000},
                {'skipped': True},
                _tombstone('alimentos', 'a.jsonl'),
            ],
            '_loaded_page_lines': [1, 2, 3, 4],
            '_snapshot_digest': 'cafef00d',
            'active_pages': 1,
        },
        'c.jsonl': {
            'file': 'c',
            '_loaded_pages': [],
            '_loaded_page_lines': [],
            '_snapshot_digest': 'feedface',
            'active_pages': 0,
        },
    }


class CrossShardReductionByteIdentityTests(unittest.TestCase):
    def test_reduction_preserves_every_cross_shard_quantity(self):
        files = ['a.jsonl', 'b.jsonl', 'c.jsonl']
        legacy = _legacy_cross_shard(files, copy.deepcopy(_fixture_shards()))
        new = _new_cross_shard(files, copy.deepcopy(_fixture_shards()))
        (l_intents, l_super, l_counter, l_lines, l_total) = legacy
        (n_intents, n_super, n_counter, n_lines, n_total) = new
        self.assertEqual(l_intents, n_intents)
        # Supersession ORDER is load-bearing (consumed_archive_claims is
        # order-dependent); compare positionally by (file, line).
        self.assertEqual(
            [(f, ln) for f, ln, _ in l_super],
            [(f, ln) for f, ln, _ in n_super])
        self.assertEqual(dict(l_counter), dict(n_counter))
        self.assertEqual(l_lines, n_lines)
        self.assertEqual(l_total, n_total)
        # Duplicate-intent last-line-wins and empty-intent inclusion are exactly
        # what the frozenset/counter encode; assert the concrete expectations so
        # a future refactor of either side cannot silently agree on a wrong value.
        self.assertIn('', n_intents['a'])
        self.assertEqual(n_counter[('a', 'div-consensual')], 2)
        self.assertEqual(n_lines[('a', 'div-consensual')], 2)
        # a.jsonl has 4 active pages, b.jsonl has 1, c.jsonl has 0.
        self.assertEqual(n_total, 5)

    def test_reducer_is_noop_without_loaded_pages(self):
        # Test doubles / incremental path emit shards without collect_pages.
        res = {'file': 'x', 'defects': {}}
        returned = audit._reduce_shard_for_cross_shard(res)
        self.assertIs(returned, res)
        self.assertNotIn('_active_entries', res)
        self.assertNotIn('_superseded_entries', res)

    def test_active_bodies_are_dropped_but_tombstones_kept_whole(self):
        shard = _fixture_shards()['a.jsonl']
        audit._reduce_shard_for_cross_shard(shard)
        self.assertNotIn('_loaded_pages', shard)
        # No active-page prose survives the reduction.
        for entry in shard['_active_entries']:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 2)
        # Superseded tombstones keep every field supersession_archive_issue reads.
        self.assertEqual(len(shard['_superseded_entries']), 1)
        _line, page = shard['_superseded_entries'][0]
        self.assertEqual(page['superseded_by'], 'b.jsonl')
        self.assertEqual(page['skip_reason'], 'duplicate_intent_consolidated')


if __name__ == '__main__':
    unittest.main()
