#!/usr/bin/env python3
"""Adversarial Go/Python parity tests for the aereo-07 current-law gate."""

import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 12)

# Frozen independently after literal comparison with the Go implementation.
# The semantic snapshot binds the Python matrices; the implementation digest
# makes a later Go-only edit fail here instead of silently preserving a stale
# claim of parity.
AEREO07_PY_CONTRACT_SHA256 = (
    'fa9334c80c9a48d92d806c041fef0d15dfdc49a8fa0f8dbdabb3bb6fb9ea2b31')
AEREO07_GO_IMPLEMENTATION_SHA256 = (
    '5250f82ff183e6ea35d66804f806020b036eaa850ce45838654561544fbdd05b')


def contract_snapshot():
    return {
        'intent_order': auditor.AEREO07_INTENT_ORDER,
        'source_urls': sorted(auditor.AEREO07_SOURCE_URLS.items()),
        'source_requirements': sorted(
            auditor.AEREO07_SOURCE_REQUIREMENTS.items()),
        'misleading_anchors': sorted(
            (intent, kind, alternatives)
            for (intent, kind), alternatives in
            auditor.AEREO07_MISLEADING_ANCHOR_RULES.items()),
        'outcomes': sorted(auditor.AEREO07_OUTCOME_RULES.items()),
        'stale_rules': auditor.AEREO07_STALE_RULES,
        'stale_scopes': sorted(
            (code, sorted(scope)) for code, scope in
            auditor.AEREO07_STALE_RULE_INTENTS.items()),
        'forbidden_urls': sorted(
            auditor.AEREO07_FORBIDDEN_SOURCE_URLS.items()),
        'portaria_676_historical_intent':
            'aer-bebe-colo-passagem-assento',
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
        'url': auditor.AEREO07_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [source_fixture(requirement) for requirement in
            auditor.AEREO07_SOURCE_REQUIREMENTS[intent]]


def current_visible(intent):
    _, groups = auditor.AEREO07_OUTCOME_RULES[intent]
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
    return auditor.current_aereo07_legal_fact_reasons(
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
        urllib.parse.urlunsplit(
            parsed._replace(netloc=parsed.netloc + '.')),
        ' ' + raw_url,
        raw_url + ' ',
    )
    return tuple(dict.fromkeys(variants))


class Aereo07CurrentLawGateTest(unittest.TestCase):

    def test_literal_cardinalities_and_unique_matrices(self):
        self.assertEqual(19, len(auditor.AEREO07_INTENT_ORDER))
        self.assertEqual(19, len(auditor.AEREO07_INTENTS))
        self.assertEqual(
            auditor.AEREO07_INTENTS,
            frozenset(auditor.AEREO07_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO07_INTENTS,
            frozenset(auditor.AEREO07_OUTCOME_RULES))
        self.assertEqual(
            57, sum(len(items) for items in
                    auditor.AEREO07_SOURCE_REQUIREMENTS.values()))
        self.assertEqual(24, len(auditor.AEREO07_SOURCE_URLS))
        self.assertEqual(
            76, sum(len(groups) for _, groups in
                    auditor.AEREO07_OUTCOME_RULES.values()))
        self.assertEqual(19, len(auditor.AEREO07_STALE_RULES))
        self.assertEqual(19, len(auditor.AEREO07_STALE_RULE_INTENTS))
        self.assertEqual(3, len(auditor.AEREO07_FORBIDDEN_SOURCE_URLS))
        self.assertEqual(
            {code for code, _ in auditor.AEREO07_STALE_RULES},
            set(auditor.AEREO07_STALE_RULE_INTENTS))
        outcome_codes = [
            code for code, _ in auditor.AEREO07_OUTCOME_RULES.values()]
        self.assertEqual(len(outcome_codes), len(set(outcome_codes)))
        for intent, (code, groups) in auditor.AEREO07_OUTCOME_RULES.items():
            with self.subTest(intent=intent):
                self.assertTrue(code)
                self.assertEqual(4, len(groups))
                signatures = [tuple(auditor.norm_key(v) for v in group)
                              for group in groups]
                self.assertEqual(len(signatures), len(set(signatures)))

    def test_active_contract_matches_independent_digest(self):
        self.assertEqual(AEREO07_PY_CONTRACT_SHA256, contract_digest())
        go_path = pathlib.Path(__file__).resolve().parents[1] / (
            'internal/v2ingest/current_legal_facts_aereo07.go')
        self.assertEqual(
            AEREO07_GO_IMPLEMENTATION_SHA256,
            hashlib.sha256(go_path.read_bytes()).hexdigest(),
            'Go aereo-07 changed without an explicit parity review')

    def test_critical_current_and_revoked_url_identities(self):
        self.assertEqual(
            'https://www.planalto.gov.br/ccivil_03/leis/l8069compilado.htm',
            auditor.AEREO07_SOURCE_URLS['eca'])
        self.assertIn('/resolucoes/2026/resolucao-807',
                      auditor.AEREO07_SOURCE_URLS['res807'])
        self.assertIn('/portarias/2025/portaria-17476',
                      auditor.AEREO07_SOURCE_URLS['port17476'])
        self.assertIn('/portaria-no-0676-cg5-de-13-11-2000',
                      auditor.AEREO07_SOURCE_URLS['port676_revoked'])
        forbidden = auditor.AEREO07_FORBIDDEN_SOURCE_URLS
        self.assertTrue(any('portaria-13065' in url for url in forbidden))
        self.assertTrue(any('portaria-12307' in url for url in forbidden))
        self.assertTrue(any('resolucao-no-130' in url for url in forbidden))

    def test_synthetic_and_real_shard_fixtures_are_green(self):
        for intent in auditor.AEREO07_INTENT_ORDER:
            with self.subTest(kind='synthetic', intent=intent):
                self.assertEqual([], direct_reasons(page(intent)))
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/aereo-07.jsonl')
        records = [json.loads(line) for line in shard.read_text(
            encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(
            list(auditor.AEREO07_INTENT_ORDER),
            [record['intent_id'] for record in records])
        for record in records:
            with self.subTest(kind='real', intent=record['intent_id']):
                self.assertEqual([], direct_reasons(record))

    def test_removing_each_of_the_57_sources_is_detected(self):
        count = 0
        for intent in auditor.AEREO07_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO07_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                del sources[index]
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(57, count)

    def test_every_source_occurrence_rejects_hostile_url_decoys(self):
        count = 0
        for intent in auditor.AEREO07_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO07_SOURCE_REQUIREMENTS[intent]):
                for decoy in exact_url_decoys(
                        auditor.AEREO07_SOURCE_URLS[kind]):
                    count += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            direct_reasons(page(intent, sources=sources)))
        self.assertGreaterEqual(count, 680)

    def test_all_material_anchors_reject_generic_metadata(self):
        count = 0
        for intent in auditor.AEREO07_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.AEREO07_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                sources[index]['name'] = 'Fonte oficial sem escopo material'
                sources[index]['anchor_claim'] = 'Documento oficial.'
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(57, count)

    def test_every_anchor_group_rejects_meta_negation(self):
        prefixes = ('A fonte não afirma que ', 'É falso que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent in auditor.AEREO07_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.AEREO07_SOURCE_REQUIREMENTS[intent]):
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
        self.assertGreater(count, 500)

    def test_misleading_anchor_claims_are_blocked(self):
        cases = (
            ('aer-bebe-colo-passagem-assento', 'port676_revoked',
             'A Portaria 676 continua vigente.'),
            ('aer-pet-cabine-regras', 'port17476',
             'A Portaria 17.476 obriga toda empresa a transportar qualquer pet na cabine.'),
            ('aer-autorizacao-menor-voo-nacional', 'cnj103',
             'Qualquer assinatura digital substitui o ato notarial.'),
            ('aer-cao-guia-cabine-gratuito', 'guide_dog_law',
             'Todo animal de suporte emocional é cão-guia.'),
            ('aer-crianca-assento-junto-responsavel', 'res807',
             'A Portaria 13.065 continua sendo a fonte vigente.'),
        )
        for intent, kind, claim in cases:
            sources = current_sources(intent)
            requirements = auditor.AEREO07_SOURCE_REQUIREMENTS[intent]
            index = [item[0] for item in requirements].index(kind)
            sources[index]['anchor_claim'] += ' ' + claim
            code = requirements[index][1]
            with self.subTest(intent=intent, kind=kind):
                self.assertIn(
                    'current_legal_fact_source_anchor_missing:' + code,
                    direct_reasons(page(intent, sources=sources)))

    def test_each_of_the_76_outcome_groups_is_required(self):
        count = 0
        for intent, (code, groups) in auditor.AEREO07_OUTCOME_RULES.items():
            texts = [sentence(group[0]) for group in groups]
            for omitted in range(len(groups)):
                count += 1
                visible = ' '.join(texts[:omitted] + texts[omitted + 1:])
                with self.subTest(intent=intent, group=omitted):
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        direct_reasons(page(intent, visible=visible)))
        self.assertEqual(76, count)

    def test_every_outcome_group_rejects_meta_negation(self):
        prefixes = ('É falso que ', 'Não é verdade que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent, (code, groups) in auditor.AEREO07_OUTCOME_RULES.items():
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
        self.assertEqual(228, count)

    def test_every_stale_alternative_is_scoped_and_meta_negation_is_safe(self):
        all_intents = set(auditor.AEREO07_INTENTS)
        for code, alternatives in auditor.AEREO07_STALE_RULES:
            scope = auditor.AEREO07_STALE_RULE_INTENTS[code]
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
                    visible = current_visible(intent) + ' ' + sentence(alternative)
                    self.assertNotIn(
                        'current_legal_fact_stale_assertion:' + code,
                        direct_reasons(page(intent, visible=visible)))

    def test_three_revoked_sources_are_forbidden_exactly(self):
        intent = 'aer-crianca-assento-junto-responsavel'
        for raw_url, code in auditor.AEREO07_FORBIDDEN_SOURCE_URLS.items():
            sources = current_sources(intent)
            sources.append({
                'url': raw_url, 'name': 'Fonte antiga',
                'anchor_claim': 'Autoridade atual',
            })
            with self.subTest(code=code):
                self.assertIn(
                    'current_legal_fact_source_stale:' + code,
                    direct_reasons(page(intent, sources=sources)))

    def test_portaria_676_is_historical_only_on_the_infant_page(self):
        historical_kind = 'port676_revoked'
        owners = [intent for intent, requirements in
                  auditor.AEREO07_SOURCE_REQUIREMENTS.items()
                  if historical_kind in {item[0] for item in requirements}]
        self.assertEqual(['aer-bebe-colo-passagem-assento'], owners)
        infant = page(owners[0])
        self.assertEqual([], direct_reasons(infant))
        intent = 'aer-pet-cabine-regras'
        sources = current_sources(intent)
        sources.append({
            'url': auditor.AEREO07_SOURCE_URLS[historical_kind],
            'name': 'Portaria 676', 'anchor_claim': 'Autoridade atual',
        })
        self.assertIn(
            'current_legal_fact_source_stale:'
            'portaria_676_revoked_not_current_authority',
            direct_reasons(page(intent, sources=sources)))

    def test_central_dispatcher_and_unknown_intent_boundaries(self):
        intent = 'aer-crianca-assento-junto-responsavel'
        record = page(intent)
        record['official_sources'] = record['official_sources'][1:]
        self.assertIn(
            'current_legal_fact_source_missing:'
            'res807_under16_adjacent_seat_exceptions_and_portaria_13065_revocation',
            auditor.current_legal_fact_reasons(record, evaluation_date=CURRENT))
        self.assertEqual([], auditor.current_aereo07_legal_fact_reasons(
            {}, 'aer-outro-shard', 'Fato qualquer.', CURRENT))


if __name__ == '__main__':
    unittest.main()
