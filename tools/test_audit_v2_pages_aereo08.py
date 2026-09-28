#!/usr/bin/env python3
"""Adversarial Go/Python parity tests for the aereo-08 current-law gate."""

import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 13)
PRE_PROVENANCE_SHARD_SHA256 = (
    'b55145a9e428f6a23556484943596aa0ce8cd11231608eff3fdf89099c83177c')
LIVE_EVIDENCE_SHARD_SHA256 = (
    '74d2170af1e94033763c52adade96bb1aa145bbbc968aa5286e4a530ba5ccf88')

# Frozen independently after literal comparison with the Go implementation.
AEREO08_PY_CONTRACT_SHA256 = (
    '3dfd69e044ceb7998519bcda49693231ec18f12b3615645085f99b1d3a95ec93')
AEREO08_GO_IMPLEMENTATION_SHA256 = (
    'fb51f279bbfb6cf3190069cf6242748cdabb1105b92ed94bd8f951685bce9e11')


def contract_snapshot():
    return {
        'intent_order': auditor.AEREO08_INTENT_ORDER,
        'source_urls': sorted(auditor.AEREO08_SOURCE_URLS.items()),
        'source_requirements': sorted(
            auditor.AEREO08_SOURCE_REQUIREMENTS.items()),
        'misleading_anchors': sorted(
            (intent, kind, alternatives)
            for (intent, kind), alternatives in
            auditor.AEREO08_MISLEADING_ANCHOR_RULES.items()),
        'outcomes': sorted(auditor.AEREO08_OUTCOME_RULES.items()),
        'stale_rules': auditor.AEREO08_STALE_RULES,
        'stale_scopes': sorted(
            (code, sorted(scope)) for code, scope in
            auditor.AEREO08_STALE_RULE_INTENTS.items()),
        'forbidden_urls': sorted(
            auditor.AEREO08_FORBIDDEN_SOURCE_URLS.items()),
        'pre_provenance_shard_sha256': PRE_PROVENANCE_SHARD_SHA256,
        'live_evidence_shard_sha256': LIVE_EVIDENCE_SHARD_SHA256,
        'direct_validator_snapshot_date':
            auditor.AEREO08_DIRECT_VALIDATOR_SNAPSHOT_DATE.isoformat(),
        'eu_reform_status_snapshot_date':
            auditor.AEREO08_EU_REFORM_STATUS_SNAPSHOT_DATE.isoformat(),
        'eu_reform_status_max_age_days':
            auditor.AEREO08_EU_REFORM_STATUS_MAX_AGE_DAYS,
        'us_refund_enforcement_snapshot_date':
            auditor.AEREO08_US_REFUND_ENFORCEMENT_SNAPSHOT_DATE.isoformat(),
        'us_refund_enforcement_max_age_days':
            auditor.AEREO08_US_REFUND_ENFORCEMENT_MAX_AGE_DAYS,
        'us_refund_enforcement_expires_on':
            auditor.AEREO08_US_REFUND_ENFORCEMENT_EXPIRES_ON.isoformat(),
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
        'url': auditor.AEREO08_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [source_fixture(requirement) for requirement in
            auditor.AEREO08_SOURCE_REQUIREMENTS[intent]]


def current_visible(intent):
    _, groups = auditor.AEREO08_OUTCOME_RULES[intent]
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
    return auditor.current_aereo08_legal_fact_reasons(
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
        urllib.parse.urlunsplit(
            parsed._replace(netloc=hostname + ':443')),
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


class Aereo08CurrentLawGateTest(unittest.TestCase):

    def test_literal_cardinalities_and_unique_matrices(self):
        self.assertEqual(14, len(auditor.AEREO08_INTENT_ORDER))
        self.assertEqual(14, len(auditor.AEREO08_INTENTS))
        self.assertEqual(
            auditor.AEREO08_INTENTS,
            frozenset(auditor.AEREO08_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO08_INTENTS,
            frozenset(auditor.AEREO08_OUTCOME_RULES))
        self.assertEqual(
            53, sum(len(items) for items in
                    auditor.AEREO08_SOURCE_REQUIREMENTS.values()))
        self.assertEqual(20, len(auditor.AEREO08_SOURCE_URLS))
        self.assertEqual(
            65, sum(len(groups) for _, groups in
                    auditor.AEREO08_OUTCOME_RULES.values()))
        self.assertEqual(14, len(auditor.AEREO08_STALE_RULES))
        self.assertEqual(14, len(auditor.AEREO08_STALE_RULE_INTENTS))
        self.assertEqual(8, len(auditor.AEREO08_FORBIDDEN_SOURCE_URLS))
        self.assertEqual(
            {code for code, _ in auditor.AEREO08_STALE_RULES},
            set(auditor.AEREO08_STALE_RULE_INTENTS))
        outcome_codes = [
            code for code, _ in auditor.AEREO08_OUTCOME_RULES.values()]
        self.assertEqual(len(outcome_codes), len(set(outcome_codes)))
        for intent, (code, groups) in auditor.AEREO08_OUTCOME_RULES.items():
            with self.subTest(intent=intent):
                self.assertTrue(code)
                expected_groups = 4
                if intent == 'aer-limite-des-dano-material-internacional':
                    expected_groups = 6
                elif intent == 'aer-voo-eua-regras-reembolso':
                    expected_groups = 9
                elif intent == 'aer-regulamento-europeu-261-indenizacao':
                    expected_groups = 6
                self.assertEqual(expected_groups, len(groups))
                signatures = [tuple(auditor.norm_key(v) for v in group)
                              for group in groups]
                self.assertEqual(len(signatures), len(set(signatures)))

    def test_active_contract_and_go_implementation_digests(self):
        self.assertEqual(AEREO08_PY_CONTRACT_SHA256, contract_digest())
        go_path = pathlib.Path(__file__).resolve().parents[1] / (
            'internal/v2ingest/current_legal_facts_aereo08.go')
        self.assertEqual(
            AEREO08_GO_IMPLEMENTATION_SHA256,
            hashlib.sha256(go_path.read_bytes()).hexdigest(),
            'Go aereo-08 changed without an explicit parity review')

    def test_frozen_shard_and_real_records_are_green(self):
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/aereo-08.jsonl')
        payload = shard.read_bytes()
        self.assertNotEqual(
            PRE_PROVENANCE_SHARD_SHA256, LIVE_EVIDENCE_SHARD_SHA256)
        self.assertEqual(
            LIVE_EVIDENCE_SHARD_SHA256, hashlib.sha256(payload).hexdigest())
        records = [json.loads(line) for line in payload.decode().splitlines()
                   if line.strip()]
        self.assertEqual(
            list(auditor.AEREO08_INTENT_ORDER),
            [record['intent_id'] for record in records])
        self.assertEqual(53, sum(len(record['official_sources'])
                                 for record in records))
        for record in records:
            with self.subTest(intent=record['intent_id']):
                self.assertEqual([], direct_reasons(record))

    def test_synthetic_fixtures_are_green(self):
        for intent in auditor.AEREO08_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual([], direct_reasons(page(intent)))

    def test_removing_each_of_the_53_sources_is_detected(self):
        count = 0
        for intent in auditor.AEREO08_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO08_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                del sources[index]
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(53, count)

    def test_every_source_occurrence_rejects_hostile_url_decoys(self):
        count = 0
        for intent in auditor.AEREO08_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO08_SOURCE_REQUIREMENTS[intent]):
                for decoy in exact_url_decoys(
                        auditor.AEREO08_SOURCE_URLS[kind]):
                    count += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            direct_reasons(page(intent, sources=sources)))
        self.assertGreaterEqual(count, 600)

    def test_every_material_anchor_group_is_required(self):
        count = 0
        for intent in auditor.AEREO08_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.AEREO08_SOURCE_REQUIREMENTS[intent]):
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
        self.assertGreaterEqual(count, 160)

    def test_every_anchor_group_rejects_meta_negation(self):
        prefixes = ('A fonte não afirma que ', 'É falso que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent in auditor.AEREO08_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.AEREO08_SOURCE_REQUIREMENTS[intent]):
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
        self.assertGreaterEqual(count, 540)

    def test_misleading_anchor_claims_are_blocked(self):
        for (intent, kind), alternatives in (
                auditor.AEREO08_MISLEADING_ANCHOR_RULES.items()):
            requirements = auditor.AEREO08_SOURCE_REQUIREMENTS[intent]
            index = [item[0] for item in requirements].index(kind)
            for false_claim in alternatives:
                sources = current_sources(intent)
                sources[index]['anchor_claim'] += ' ' + sentence(false_claim)
                with self.subTest(
                        intent=intent, kind=kind, false_claim=false_claim):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' +
                        requirements[index][1],
                        direct_reasons(page(intent, sources=sources)))

    def test_each_of_the_65_outcome_groups_is_required(self):
        count = 0
        for intent, (code, groups) in auditor.AEREO08_OUTCOME_RULES.items():
            texts = [sentence(group[0]) for group in groups]
            for omitted in range(len(groups)):
                count += 1
                visible = ' '.join(texts[:omitted] + texts[omitted + 1:])
                with self.subTest(intent=intent, group=omitted):
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        direct_reasons(page(intent, visible=visible)))
        self.assertEqual(65, count)

    def test_every_outcome_group_rejects_meta_negation(self):
        prefixes = ('É falso que ', 'Não é verdade que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent, (code, groups) in auditor.AEREO08_OUTCOME_RULES.items():
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
        self.assertEqual(195, count)

    def test_every_stale_alternative_is_scoped_and_negation_safe(self):
        all_intents = set(auditor.AEREO08_INTENTS)
        for code, alternatives in auditor.AEREO08_STALE_RULES:
            scope = auditor.AEREO08_STALE_RULE_INTENTS[code]
            for alternative in alternatives:
                for intent in scope:
                    visible = current_visible(intent) + ' ' + sentence(alternative)
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

    def test_eight_substituted_or_blocked_sources_are_forbidden(self):
        intent = 'aer-des-direito-especial-saque'
        for raw_url, code in auditor.AEREO08_FORBIDDEN_SOURCE_URLS.items():
            sources = current_sources(intent)
            sources.append({
                'url': raw_url, 'name': 'Fonte substituída',
                'anchor_claim': 'Autoridade atual',
            })
            with self.subTest(code=code):
                self.assertIn(
                    'current_legal_fact_source_stale:' + code,
                    direct_reasons(page(intent, sources=sources)))

    def test_material_decoys_of_forbidden_sources_are_forbidden(self):
        intent = 'aer-des-direito-especial-saque'
        count = 0
        for raw_url, code in auditor.AEREO08_FORBIDDEN_SOURCE_URLS.items():
            for decoy in forbidden_url_identity_decoys(raw_url):
                count += 1
                sources = current_sources(intent)
                sources.append({
                    'url': decoy, 'name': 'Fonte substituída',
                    'anchor_claim': 'Autoridade atual',
                })
                with self.subTest(code=code, decoy=decoy):
                    self.assertIn(
                        'current_legal_fact_source_stale:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(64, count)

    def test_forbidden_eurlex_identity_checks_every_uri_value(self):
        count = 0
        intent = 'aer-des-direito-especial-saque'
        for raw_url, code in auditor.AEREO08_FORBIDDEN_SOURCE_URLS.items():
            parsed = urllib.parse.urlsplit(raw_url)
            wanted_uri = urllib.parse.parse_qs(
                parsed.query, keep_blank_values=True).get('uri', ())
            if not wanted_uri:
                continue
            count += 1
            decoy = urllib.parse.urlunsplit(parsed._replace(
                query='uri=DECOY&' + parsed.query))
            sources = current_sources(intent)
            sources.append({
                'url': decoy, 'name': 'Fonte substituída',
                'anchor_claim': 'Autoridade atual',
            })
            with self.subTest(code=code, decoy=decoy):
                self.assertIn(
                    'current_legal_fact_source_stale:' + code,
                    direct_reasons(page(intent, sources=sources)))
                different = urllib.parse.urlunsplit(parsed._replace(
                    query='uri=DECOY'))
                self.assertFalse(auditor.aereo08_forbidden_source_matches(
                    different, raw_url))
        self.assertEqual(2, count)

    def test_no_imf_source_is_canonical_and_govinfo_is_required(self):
        self.assertFalse(any(
            'imf.org' in raw_url
            for raw_url in auditor.AEREO08_SOURCE_URLS.values()))
        self.assertIn(
            'www.govinfo.gov',
            auditor.AEREO08_SOURCE_URLS['govinfo_refund'])
        self.assertEqual(
            2, sum('imf.org' in raw_url for raw_url in
                   auditor.AEREO08_FORBIDDEN_SOURCE_URLS))

    def test_current_stf_stj_endpoints_and_no_blocked_canonical_hosts(self):
        self.assertEqual(
            'https://noticias.stf.jus.br/postsnoticias/'
            'convencoes-internacionais-nao-se-aplicam-a-dano-moral-em-'
            'transporte-internacional-de-passageiros/',
            auditor.AEREO08_SOURCE_URLS['stf1240'])
        self.assertIn(
            '%40CNOT%3D%27020233%27',
            auditor.AEREO08_SOURCE_URLS['stj_codeshare'])
        self.assertEqual(
            'https://publications.europa.eu/resource/cellar/'
            '439cd3a7-fd3c-4da7-8bf4-b0f60600c1d6.0004.01/DOC_1',
            auditor.AEREO08_SOURCE_URLS['eu261'])
        self.assertEqual(
            'https://publications.europa.eu/resource/cellar/'
            'fce91149-7ad5-11ef-bbbe-01aa75ed71a1.0006.01/DOC_1',
            auditor.AEREO08_SOURCE_URLS['eu_guidelines'])
        self.assertEqual(
            'https://oeil.europarl.europa.eu/oeil/en/procedure-file?'
            'reference=2013%2F0072%28COD%29',
            auditor.AEREO08_SOURCE_URLS['eu_reform_procedure'])
        self.assertEqual(
            'https://www.govinfo.gov/content/pkg/FR-2026-07-07/pdf/'
            '2026-13675.pdf',
            auditor.AEREO08_SOURCE_URLS['govinfo_renumbering'])
        blocked = (
            'imf.org', 'transportation.gov', 'transport.ec.europa.eu',
            'travel.state.gov', 'portal.stf.jus.br', 'sv03.stj.jus.br',
            'eur-lex.europa.eu', '2106137', '2.106.137')
        for kind, raw_url in auditor.AEREO08_SOURCE_URLS.items():
            for fragment in blocked:
                with self.subTest(kind=kind, fragment=fragment):
                    self.assertNotIn(fragment, raw_url.lower())

    def test_eu_reform_pending_status_expires_for_semantic_recheck(self):
        self.assertEqual(
            CURRENT, auditor.AEREO08_DIRECT_VALIDATOR_SNAPSHOT_DATE)
        self.assertEqual(
            CURRENT, auditor.AEREO08_EU_REFORM_STATUS_SNAPSHOT_DATE)
        self.assertEqual(
            datetime.date(2026, 7, 21),
            auditor.AEREO08_EU_REFORM_STATUS_RECHECK_AT)
        intent = 'aer-regulamento-europeu-261-indenizacao'
        boundary = (
            auditor.AEREO08_EU_REFORM_STATUS_RECHECK_AT -
            datetime.timedelta(days=1))
        reason = (
            'current_legal_fact_temporal_stale:'
            'aereo08_eu261_reform_status_recheck_required_after_2026_07_20')
        self.assertNotIn(
            reason, direct_reasons(page(intent), visible=current_visible(intent)))
        self.assertNotIn(
            reason, auditor.current_aereo08_legal_fact_reasons(
                page(intent), intent, current_visible(intent), boundary))
        self.assertIn(
            reason, auditor.current_aereo08_legal_fact_reasons(
                page(intent), intent, current_visible(intent),
                auditor.AEREO08_EU_REFORM_STATUS_RECHECK_AT))
        other = 'aer-voo-eua-regras-reembolso'
        self.assertNotIn(
            reason, auditor.current_aereo08_legal_fact_reasons(
                page(other), other, current_visible(other),
                auditor.AEREO08_EU_REFORM_STATUS_RECHECK_AT))

    def test_us_renumbering_enforcement_status_expires_for_recheck(self):
        self.assertEqual(
            CURRENT, auditor.AEREO08_US_REFUND_ENFORCEMENT_SNAPSHOT_DATE)
        self.assertEqual(
            datetime.date(2026, 7, 21),
            auditor.AEREO08_US_REFUND_ENFORCEMENT_RECHECK_AT)
        self.assertEqual(
            datetime.date(2027, 7, 7),
            auditor.AEREO08_US_REFUND_ENFORCEMENT_EXPIRES_ON)
        intent = 'aer-voo-eua-regras-reembolso'
        boundary = (
            auditor.AEREO08_US_REFUND_ENFORCEMENT_RECHECK_AT -
            datetime.timedelta(days=1))
        reason = (
            'current_legal_fact_temporal_stale:'
            'aereo08_us_renumbering_enforcement_status_'
            'recheck_required_after_2026_07_20')
        self.assertNotIn(
            reason, auditor.current_aereo08_legal_fact_reasons(
                page(intent), intent, current_visible(intent), boundary))
        self.assertIn(
            reason, auditor.current_aereo08_legal_fact_reasons(
                page(intent), intent, current_visible(intent),
                auditor.AEREO08_US_REFUND_ENFORCEMENT_RECHECK_AT))
        other = 'aer-regulamento-europeu-261-indenizacao'
        self.assertNotIn(
            reason, auditor.current_aereo08_legal_fact_reasons(
                page(other), other, current_visible(other),
                auditor.AEREO08_US_REFUND_ENFORCEMENT_RECHECK_AT))

    def test_central_dispatcher_and_unknown_intent_boundaries(self):
        intent = 'aer-regulamento-europeu-261-indenizacao'
        record = page(intent)
        record['official_sources'] = record['official_sources'][1:]
        self.assertIn(
            'current_legal_fact_source_missing:'
            'eu261_scope_cancellation_compensation_refund_and_assistance',
            auditor.current_legal_fact_reasons(record, evaluation_date=CURRENT))
        self.assertEqual([], auditor.current_aereo08_legal_fact_reasons(
            {}, 'aer-outro-shard', 'Fato qualquer.', CURRENT))


if __name__ == '__main__':
    unittest.main()
