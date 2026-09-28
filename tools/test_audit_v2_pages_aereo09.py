#!/usr/bin/env python3
"""Adversarial Go/Python parity tests for the aereo-09 current-law gate."""

import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 13)
# Parity review of 2026-09-05. The three pins were frozen at c017c97f
# (2026-07-13) and had aged legitimately: the Go gate changed in 0614047b
# (2026-07-15, sentence-boundary restoration for two stale codes) and in
# 63534292 (2026-08-04, onda W5: +6 tourism/lodging intents, +4 Planalto
# URLs, +13 requirements, +6 outcome and stale rules); the shard grew from 17
# to 23 records in 66ef276b (2026-07-31) with the 17 originals byte-identical.
# The Python tables were ported literally from the Go file before re-pinning,
# and all 23 real records are green under both runtimes.
AEREO09_PY_CONTRACT_SHA256 = (
    '3fe37d157a8a5cf790f18b315d88f653f22342c5fa90bffeadc97abca08758db')
AEREO09_GO_IMPLEMENTATION_SHA256 = (
    '8649617a59aa1d4a5ba01349683b63e8e5dfa6697a41d72d22a61b157c4d4d71')
AEREO09_SHARD_SHA256 = (
    'e3915e3a2dbf9c86a98d555e2618dd90a5e6c94010c892c2d86772e7ed07153f')


def contract_snapshot():
    return {
        'intent_order': auditor.AEREO09_INTENT_ORDER,
        'source_urls': sorted(auditor.AEREO09_SOURCE_URLS.items()),
        'source_requirements': sorted(
            auditor.AEREO09_SOURCE_REQUIREMENTS.items()),
        'misleading_anchors': sorted(
            (intent, kind, alternatives)
            for (intent, kind), alternatives in
            auditor.AEREO09_MISLEADING_ANCHOR_RULES.items()),
        'outcomes': sorted(auditor.AEREO09_OUTCOME_RULES.items()),
        'stale_rules': auditor.AEREO09_STALE_RULES,
        'stale_scopes': sorted(
            (code, sorted(scope)) for code, scope in
            auditor.AEREO09_STALE_RULE_INTENTS.items()),
        'forbidden_urls': sorted(
            auditor.AEREO09_FORBIDDEN_SOURCE_URLS.items()),
        'source_budget': (2, 5),
    }


def contract_digest():
    payload = json.dumps(
        contract_snapshot(), sort_keys=True, separators=(',', ':'),
        ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def source_fixture(requirement):
    kind, _, groups = requirement
    return {
        'url': auditor.AEREO09_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [source_fixture(requirement) for requirement in
            auditor.AEREO09_SOURCE_REQUIREMENTS[intent]]


def current_visible(intent):
    _, groups = auditor.AEREO09_OUTCOME_RULES[intent]
    return ' '.join(sentence(alternatives[0]) for alternatives in groups)


def page(intent, visible=None, sources=None):
    return {
        'intent_id': intent,
        'opening': current_visible(intent) if visible is None else visible,
        'official_sources': (
            current_sources(intent) if sources is None else sources),
    }


def direct_reasons(record, visible=None):
    intent = record.get('intent_id', '')
    if visible is None:
        visible = '\n'.join(auditor.visible_parts(record))
    return auditor.current_aereo09_legal_fact_reasons(
        record, intent, visible, CURRENT)


def exact_url_decoys(raw_url):
    parsed = urllib.parse.urlsplit(raw_url)
    path = parsed.path[:-1] if parsed.path.endswith('/') else parsed.path + '/'
    query = parsed.query + ('&' if parsed.query else '') + 'decoy=1'
    hostname = parsed.hostname or ''
    variants = (
        urllib.parse.urlunsplit(parsed._replace(fragment='decoy')),
        urllib.parse.urlunsplit(parsed._replace(query=query)),
        urllib.parse.urlunsplit(parsed._replace(path=path)),
        urllib.parse.urlunsplit(
            parsed._replace(path='//' + parsed.path.lstrip('/'))),
        urllib.parse.urlunsplit(parsed._replace(scheme='http')),
        urllib.parse.urlunsplit(parsed._replace(netloc=parsed.netloc.upper())),
        urllib.parse.urlunsplit(parsed._replace(netloc=hostname + ':443')),
        urllib.parse.urlunsplit(
            parsed._replace(netloc='legacy@' + parsed.netloc)),
        urllib.parse.urlunsplit(
            parsed._replace(netloc='prefix-' + parsed.netloc)),
        urllib.parse.urlunsplit(
            parsed._replace(netloc=parsed.netloc + '.evil.invalid')),
        urllib.parse.urlunsplit(parsed._replace(netloc=parsed.netloc + '.')),
        ' ' + raw_url,
        raw_url + ' ',
    )
    return tuple(dict.fromkeys(variants))


def forbidden_url_identity_decoys(raw_url):
    parsed = urllib.parse.urlsplit(raw_url)
    query = parsed.query + ('&' if parsed.query else '') + 'tracking=1'
    hostname = parsed.hostname or ''
    variants = (
        urllib.parse.urlunsplit(parsed._replace(fragment='tracking')),
        urllib.parse.urlunsplit(parsed._replace(query=query)),
        urllib.parse.urlunsplit(parsed._replace(netloc=hostname + ':443')),
        urllib.parse.urlunsplit(
            parsed._replace(netloc='decoy@' + parsed.netloc)),
        urllib.parse.urlunsplit(
            parsed._replace(netloc=parsed.netloc.upper())),
        urllib.parse.urlunsplit(
            parsed._replace(path=parsed.path + '/')),
        ' ' + raw_url,
        raw_url + ' ',
    )
    return tuple(dict.fromkeys(variants))


class Aereo09CurrentLawGateTest(unittest.TestCase):

    def test_literal_cardinalities_and_unique_matrices(self):
        self.assertEqual(23, len(auditor.AEREO09_INTENT_ORDER))
        self.assertEqual(23, len(auditor.AEREO09_INTENTS))
        self.assertEqual(
            auditor.AEREO09_INTENTS,
            frozenset(auditor.AEREO09_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO09_INTENTS,
            frozenset(auditor.AEREO09_OUTCOME_RULES))
        requirements = [
            item for items in auditor.AEREO09_SOURCE_REQUIREMENTS.values()
            for item in items]
        self.assertEqual(87, len(requirements))
        self.assertEqual(87, len({code for _, code, _ in requirements}))
        self.assertEqual(30, len(auditor.AEREO09_SOURCE_URLS))
        self.assertEqual(
            set(auditor.AEREO09_SOURCE_URLS),
            {kind for kind, _, _ in requirements})
        self.assertEqual(
            302, sum(len(groups) for _, _, groups in requirements))
        self.assertEqual(
            115, sum(len(groups) for _, groups in
                    auditor.AEREO09_OUTCOME_RULES.values()))
        self.assertEqual(23, len(auditor.AEREO09_STALE_RULES))
        self.assertEqual(23, len(auditor.AEREO09_STALE_RULE_INTENTS))
        self.assertEqual(8, len(auditor.AEREO09_FORBIDDEN_SOURCE_URLS))
        self.assertEqual(
            {code for code, _ in auditor.AEREO09_STALE_RULES},
            set(auditor.AEREO09_STALE_RULE_INTENTS))
        self.assertEqual(6, len(auditor.AEREO09_MISLEADING_ANCHOR_RULES))
        self.assertEqual(
            7, sum(len(items) for items in
                   auditor.AEREO09_MISLEADING_ANCHOR_RULES.values()))
        self.assertEqual(
            3, sum(kind == 'consumer_gov'
                   for kind, _, _ in requirements))
        outcome_codes = [
            code for code, _ in auditor.AEREO09_OUTCOME_RULES.values()]
        self.assertEqual(len(outcome_codes), len(set(outcome_codes)))
        for code, scope in auditor.AEREO09_STALE_RULE_INTENTS.items():
            with self.subTest(code=code):
                self.assertTrue(scope)
                self.assertLessEqual(scope, auditor.AEREO09_INTENTS)

    def test_active_contract_and_go_implementation_digests(self):
        self.assertEqual(AEREO09_PY_CONTRACT_SHA256, contract_digest())
        go_path = pathlib.Path(__file__).resolve().parents[1] / (
            'internal/v2ingest/current_legal_facts_aereo09.go')
        self.assertEqual(
            AEREO09_GO_IMPLEMENTATION_SHA256,
            hashlib.sha256(go_path.read_bytes()).hexdigest(),
            'Go aereo-09 changed without explicit parity review')

    def test_frozen_shard_real_records_and_source_budget_are_green(self):
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/aereo-09.jsonl')
        payload = shard.read_bytes()
        self.assertEqual(
            AEREO09_SHARD_SHA256, hashlib.sha256(payload).hexdigest())
        records = [json.loads(line) for line in payload.decode().splitlines()
                   if line.strip()]
        self.assertEqual(
            list(auditor.AEREO09_INTENT_ORDER),
            [record['intent_id'] for record in records])
        self.assertEqual(
            87, sum(len(record['official_sources']) for record in records))
        self.assertEqual(
            30, len({source['url'] for record in records
                     for source in record['official_sources']}))
        # The 17 original records were verified on 2026-07-13; the six W5
        # records on 2026-07-31 (66ef276b). Any other stamp is drift.
        verified_dates = {'2026-07-13', '2026-07-31'}
        required_occurrences = 0
        for record in records:
            with self.subTest(intent=record['intent_id']):
                sources = record['official_sources']
                self.assertGreaterEqual(len(sources), 2)
                self.assertLessEqual(len(sources), 5)
                self.assertTrue(all(
                    source.get('verified_at') in verified_dates and
                    200 <= int(source.get('http_status', 0)) < 400
                    for source in sources))
                # Parity with Go
                # TestCurrentLegalFactsAereo09SourceOccurrenceCardinalityMatchesRealShard:
                # every required canonical URL occurs exactly once, and the
                # record carries no source beyond the required ones.
                urls = [source['url'] for source in sources]
                self.assertEqual(len(urls), len(set(urls)))
                requirements = auditor.AEREO09_SOURCE_REQUIREMENTS[
                    record['intent_id']]
                for kind, _, _ in requirements:
                    self.assertEqual(
                        1, urls.count(auditor.AEREO09_SOURCE_URLS[kind]),
                        (record['intent_id'], kind))
                self.assertEqual(len(requirements), len(sources))
                required_occurrences += len(requirements)
                self.assertEqual([], direct_reasons(record))
        self.assertEqual(87, required_occurrences)

    def test_synthetic_fixtures_are_green(self):
        for intent in auditor.AEREO09_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual([], direct_reasons(page(intent)))

    def test_removing_each_of_the_87_sources_is_detected(self):
        count = 0
        for intent in auditor.AEREO09_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO09_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                del sources[index]
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(87, count)

    def test_every_source_occurrence_rejects_hostile_url_decoys(self):
        count = 0
        for intent in auditor.AEREO09_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO09_SOURCE_REQUIREMENTS[intent]):
                for decoy in exact_url_decoys(
                        auditor.AEREO09_SOURCE_URLS[kind]):
                    count += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            direct_reasons(page(intent, sources=sources)))
        self.assertGreaterEqual(count, 870)

    def test_every_material_anchor_group_is_required(self):
        count = 0
        for intent in auditor.AEREO09_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.AEREO09_SOURCE_REQUIREMENTS[intent]):
                for omitted in range(len(groups)):
                    count += 1
                    sources = current_sources(intent)
                    sources[source_index]['anchor_claim'] = ' '.join(
                        sentence(group[0]) for index, group in
                        enumerate(groups) if index != omitted)
                    with self.subTest(
                            intent=intent, kind=kind, group=omitted):
                        self.assertIn(
                            'current_legal_fact_source_anchor_missing:' + code,
                            direct_reasons(page(intent, sources=sources)))
        self.assertEqual(302, count)

    def test_every_anchor_group_rejects_meta_negation(self):
        prefixes = ('A fonte não afirma que ', 'É falso que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent in auditor.AEREO09_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.AEREO09_SOURCE_REQUIREMENTS[intent]):
                for target in range(len(groups)):
                    for prefix in prefixes:
                        count += 1
                        claims = []
                        for index, alternatives in enumerate(groups):
                            value = alternatives[0]
                            if index == target:
                                value = prefix + value
                            claims.append(sentence(value))
                        sources = current_sources(intent)
                        sources[source_index]['anchor_claim'] = ' '.join(claims)
                        with self.subTest(
                                intent=intent, kind=kind, group=target,
                                prefix=prefix):
                            self.assertIn(
                                'current_legal_fact_source_anchor_missing:' +
                                code,
                                direct_reasons(page(
                                    intent, sources=sources)))
        self.assertEqual(906, count)

    def test_misleading_anchor_claims_are_blocked(self):
        count = 0
        for (intent, kind), alternatives in (
                auditor.AEREO09_MISLEADING_ANCHOR_RULES.items()):
            requirements = auditor.AEREO09_SOURCE_REQUIREMENTS[intent]
            index = [item[0] for item in requirements].index(kind)
            for false_claim in alternatives:
                count += 1
                sources = current_sources(intent)
                sources[index]['anchor_claim'] += ' ' + sentence(false_claim)
                with self.subTest(
                        intent=intent, kind=kind, false_claim=false_claim):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' +
                        requirements[index][1],
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(7, count)

    def test_each_of_the_115_outcome_groups_is_required(self):
        count = 0
        for intent, (code, groups) in auditor.AEREO09_OUTCOME_RULES.items():
            texts = [sentence(group[0]) for group in groups]
            for omitted in range(len(groups)):
                count += 1
                visible = ' '.join(texts[:omitted] + texts[omitted + 1:])
                with self.subTest(intent=intent, group=omitted):
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        direct_reasons(page(intent, visible=visible)))
        self.assertEqual(115, count)

    def test_every_outcome_group_rejects_meta_negation(self):
        prefixes = ('É falso que ', 'Não é verdade que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent, (code, groups) in auditor.AEREO09_OUTCOME_RULES.items():
            for target in range(len(groups)):
                for prefix in prefixes:
                    count += 1
                    values = []
                    for index, group in enumerate(groups):
                        value = group[0]
                        if index == target:
                            value = prefix + value
                        values.append(sentence(value))
                    with self.subTest(
                            intent=intent, group=target, prefix=prefix):
                        self.assertIn(
                            'current_legal_fact_outcome_missing:' + code,
                            direct_reasons(page(
                                intent, visible=' '.join(values))))
        self.assertEqual(345, count)

    def test_every_stale_alternative_is_scoped_and_negation_safe(self):
        all_intents = set(auditor.AEREO09_INTENTS)
        for code, alternatives in auditor.AEREO09_STALE_RULES:
            scope = auditor.AEREO09_STALE_RULE_INTENTS[code]
            for alternative in alternatives:
                for intent in scope:
                    visible = current_visible(intent) + ' ' + sentence(
                        alternative)
                    with self.subTest(code=code, intent=intent):
                        self.assertIn(
                            'current_legal_fact_stale_assertion:' + code,
                            direct_reasons(page(intent, visible=visible)))
                    safe = (current_visible(intent) +
                            ' É falso que ' + sentence(alternative))
                    self.assertNotIn(
                        'current_legal_fact_stale_assertion:' + code,
                        direct_reasons(page(intent, visible=safe)))
                outside = all_intents - set(scope)
                if outside:
                    intent = sorted(outside)[0]
                    self.assertNotIn(
                        'current_legal_fact_stale_assertion:' + code,
                        direct_reasons(page(
                            intent, visible=current_visible(intent) +
                            ' ' + sentence(alternative))))

    def test_eight_forbidden_endpoints_and_variants_are_blocked(self):
        intent = auditor.AEREO09_INTENT_ORDER[0]
        count = 0
        for raw_url, code in auditor.AEREO09_FORBIDDEN_SOURCE_URLS.items():
            for candidate in (raw_url,) + forbidden_url_identity_decoys(
                    raw_url):
                count += 1
                sources = current_sources(intent)
                sources.append({
                    'url': candidate, 'name': 'Fonte obsoleta',
                    'anchor_claim': 'Autoridade atual',
                })
                with self.subTest(code=code, candidate=candidate):
                    self.assertIn(
                        'current_legal_fact_source_stale:' + code,
                        direct_reasons(page(intent, sources=sources)))
            parsed = urllib.parse.urlsplit(raw_url)
            different = urllib.parse.urlunsplit(
                parsed._replace(netloc='different.example'))
            self.assertFalse(
                auditor.aereo_source_endpoint_matches(different, raw_url))
        self.assertEqual(72, count)

    def test_current_source_identities_and_scoped_consumer_gov(self):
        chamber_kinds = {
            'cdc', 'tourism_law', 'tourism_decree', 'civil_code',
            'bankruptcy_law', 'jec'}
        for kind in chamber_kinds:
            with self.subTest(kind=kind):
                self.assertTrue(
                    auditor.AEREO09_SOURCE_URLS[kind].startswith(
                        'https://www2.camara.leg.br/'))
        self.assertIn(
            '%40CNOT%3D020233',
            auditor.AEREO09_SOURCE_URLS['stj_ticket_only'])
        self.assertTrue(
            auditor.AEREO09_SOURCE_URLS['stj_short_stay'].endswith(
                'GetPDFINFJ?edicao=0889'))
        consumer_intents = {
            intent for intent, requirements in
            auditor.AEREO09_SOURCE_REQUIREMENTS.items()
            if any(kind == 'consumer_gov'
                   for kind, _, _ in requirements)}
        self.assertEqual({
            'aer-agencia-cancelou-pacote-reembolso',
            'aer-cruzeiro-cancelado-direitos',
            'aer-operadora-falencia-viagem-paga',
        }, consumer_intents)

    def test_central_dispatcher_and_unknown_intent_boundaries(self):
        intent = 'aer-agencia-cancelou-pacote-reembolso'
        record = page(intent)
        first_code = auditor.AEREO09_SOURCE_REQUIREMENTS[intent][0][1]
        record['official_sources'] = record['official_sources'][1:]
        self.assertIn(
            'current_legal_fact_source_missing:' + first_code,
            auditor.current_legal_fact_reasons(
                record, evaluation_date=CURRENT))
        self.assertEqual([], auditor.current_aereo09_legal_fact_reasons(
            {}, 'aer-outro-shard', 'Fato qualquer.', CURRENT))


if __name__ == '__main__':
    unittest.main()
