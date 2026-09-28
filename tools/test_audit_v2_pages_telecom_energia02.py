#!/usr/bin/env python3
"""Adversarial Go/Python parity tests for Telecom/Energia shards 01-03."""

import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 13)
OLD_CANCEL_URL = (
    'https://www.gov.br/anatel/pt-br/consumidor/faq-cancelamento')
OLD_ADDRESS_URL = (
    'https://www.gov.br/anatel/pt-br/consumidor/'
    'conheca-seus-direitos-2/banda-larga/mudanca-de-endereco')

SOURCE_UNISOLATABLE_OVERLAPS = frozenset({
    ('tel-multa-fidelidade-quando-vale', 'rgc', 0),
    ('tel-multa-fidelidade-quando-vale', 'rgc', 8),
    ('tel-cancelar-sem-multa-servico-ruim', 'rgc', 0),
    ('tel-cancelar-sem-multa-servico-ruim', 'rgc', 4),
    ('tel-mudanca-endereco-sem-cobertura-multa', 'cdc', 1),
    ('tel-cancelamento-automatico-digital', 'rgc', 0),
    ('tel-operadora-dificulta-cancelamento', 'rgc', 0),
    ('tel-arrependimento-7-dias-telecom', 'rgc', 3),
    ('tel-suspensao-temporaria-linha', 'rgc', 0),
})
OUTCOME_UNISOLATABLE_OVERLAPS = frozenset()
SCOPE_UNISOLATABLE_OVERLAPS = frozenset()


def _contract_forbidden_sources(values):
    result = []
    for raw_url, rule in sorted(values.items()):
        result.append((
            raw_url,
            rule['code'],
            sorted(rule.get('intents', ())),
            rule.get('required_query_key', ''),
            rule.get('required_query_value', ''),
            rule.get('historical_metadata_groups', ()),
        ))
    return result


def _contract_matrix_snapshot(
        intent_order, source_urls, source_requirements,
        misleading_anchors, outcomes, scope_rules,
        stale_rules, stale_scopes):
    return {
        'intent_order': intent_order,
        'source_urls': sorted(source_urls.items()),
        'source_requirements': sorted(source_requirements.items()),
        'misleading_anchors': sorted(
            (intent, kind, alternatives)
            for (intent, kind), alternatives in misleading_anchors.items()),
        'outcomes': sorted(outcomes.items()),
        'scope_rules': sorted(scope_rules.items()),
        'stale_rules': stale_rules,
        'stale_scopes': sorted(
            (code, sorted(scope)) for code, scope in stale_scopes.items()),
    }


def telecom_cross_runtime_contract_snapshot():
    return {
        'schema_version': 1,
        'common': {
            'global_stale_rules': auditor.TELECOM_GLOBAL_STALE_RULES,
            'forbidden_sources': {
                'telecom01': _contract_forbidden_sources(
                    auditor.TELECOM01_FORBIDDEN_SOURCE_URLS),
                'telecom02': _contract_forbidden_sources(
                    auditor.TELECOM02_FORBIDDEN_SOURCE_URLS),
            },
        },
        'telecom01': _contract_matrix_snapshot(
            auditor.TELECOM01_INTENT_ORDER,
            auditor.TELECOM01_SOURCE_URLS,
            auditor.TELECOM01_SOURCE_REQUIREMENTS,
            auditor.TELECOM01_MISLEADING_ANCHOR_RULES,
            auditor.TELECOM01_OUTCOME_RULES,
            auditor.TELECOM01_PPP_SCOPE_RULES,
            auditor.TELECOM01_STALE_RULES,
            auditor.TELECOM01_STALE_RULE_INTENTS,
        ),
        'telecom02': _contract_matrix_snapshot(
            auditor.TELECOM02_INTENT_ORDER,
            auditor.TELECOM02_SOURCE_URLS,
            auditor.TELECOM02_SOURCE_REQUIREMENTS,
            auditor.TELECOM02_MISLEADING_ANCHOR_RULES,
            auditor.TELECOM02_OUTCOME_RULES,
            auditor.TELECOM02_PPP_SCOPE_RULES,
            auditor.TELECOM02_STALE_RULES,
            auditor.TELECOM02_STALE_RULE_INTENTS,
        ),
        'telecom03': _contract_matrix_snapshot(
            auditor.TELECOM03_INTENT_ORDER,
            auditor.TELECOM03_SOURCE_URLS,
            auditor.TELECOM03_SOURCE_REQUIREMENTS,
            auditor.TELECOM03_MISLEADING_ANCHOR_RULES,
            auditor.TELECOM03_OUTCOME_RULES,
            auditor.TELECOM03_PPP_SCOPE_RULES,
            auditor.TELECOM03_STALE_RULES,
            auditor.TELECOM03_STALE_RULE_INTENTS,
        ),
    }


def telecom_cross_runtime_contract_digest():
    payload = json.dumps(
        telecom_cross_runtime_contract_snapshot(),
        sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def witness_sentence(value):
    return 'Regra atual: ' + sentence(value)


def source_group_affirmed(text, alternatives):
    return auditor.aereo05_anchor_group_affirmed(text, alternatives)


def visible_group_affirmed(text, alternatives):
    return any(
        auditor.criminal13_declarative_alternative_affirmed_in_text(
            text, alternative)
        for alternative in alternatives)


def isolated_witnesses(groups, target, group_affirmed, target_value=None):
    """Cover every neighboring group without also covering target."""
    target_alternatives = groups[target]
    values = []
    for index, alternatives in enumerate(groups):
        if index == target:
            if target_value is not None:
                values.append(witness_sentence(target_value))
            continue
        compatible = next((
            alternative for alternative in alternatives
            if group_affirmed(witness_sentence(alternative), alternatives)
            and not group_affirmed(
                witness_sentence(alternative), target_alternatives)
        ), None)
        if compatible is None:
            return None
        values.append(witness_sentence(compatible))
    return values


def source_fixture(requirement):
    kind, _, groups = requirement
    return {
        'url': auditor.TELECOM02_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            witness_sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [source_fixture(requirement) for requirement in
            auditor.TELECOM02_SOURCE_REQUIREMENTS[intent]]


def current_visible(intent):
    _, groups = auditor.TELECOM02_OUTCOME_RULES[intent]
    values = [sentence(alternatives[0]) for alternatives in groups]
    scope_rule = auditor.TELECOM02_PPP_SCOPE_RULES.get(intent)
    if scope_rule is not None:
        values.extend(sentence(alternatives[0])
                      for alternatives in scope_rule[1])
    return ' '.join('Regra atual: ' + value for value in values)


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
    return auditor.current_telecom_legal_fact_reasons(
        record, intent, visible, CURRENT)


def alternative_page(
        source_urls, requirements, intent,
        target_source=-1, target_group=-1, target_alternative=-1,
        negated=False):
    sources = []
    for source_index, (kind, _, groups) in enumerate(requirements[intent]):
        claims = []
        for group_index, alternatives in enumerate(groups):
            value = alternatives[0]
            if (source_index == target_source and
                    group_index == target_group):
                value = alternatives[target_alternative]
                if negated:
                    value = 'É falso que ' + value
            claims.append(witness_sentence(value))
        sources.append({
            'url': source_urls[kind],
            'name': 'Fonte oficial específica',
            'anchor_claim': ' '.join(claims),
        })
    return {'intent_id': intent, 'official_sources': sources}


def alternative_visible(
        outcomes, scope_rules, intent,
        target_matrix='', target_group=-1, target_alternative=-1,
        negated=False):
    values = []
    matrices = [('outcome', outcomes[intent])]
    if intent in scope_rules:
        matrices.append(('scope', scope_rules[intent]))
    for matrix_name, (_, groups) in matrices:
        for group_index, alternatives in enumerate(groups):
            value = alternatives[0]
            if (matrix_name == target_matrix and
                    group_index == target_group):
                value = alternatives[target_alternative]
                if negated:
                    value = 'Não é verdade que ' + value
            values.append(witness_sentence(value))
    return ' '.join(values)


def exact_url_decoys(raw_url):
    """Hostile variants remain invalid because canonical sources are exact."""
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


def forbidden_url_identity_variants(raw_url):
    """Benign URL syntax variants still identify a forbidden endpoint."""
    parsed = urllib.parse.urlsplit(raw_url)
    query = parsed.query + ('&' if parsed.query else '') + 'tracking=1'
    hostname = parsed.hostname or ''
    variants = (
        raw_url,
        urllib.parse.urlunsplit(parsed._replace(fragment='tracking')),
        urllib.parse.urlunsplit(parsed._replace(query=query)),
        urllib.parse.urlunsplit(parsed._replace(netloc=hostname + ':443')),
        urllib.parse.urlunsplit(
            parsed._replace(netloc='decoy@' + parsed.netloc)),
        urllib.parse.urlunsplit(parsed._replace(netloc=parsed.netloc.upper())),
        urllib.parse.urlunsplit(parsed._replace(path=parsed.path + '/')),
        ' ' + raw_url,
        raw_url + ' ',
    )
    return tuple(dict.fromkeys(variants))


class TelecomEnergia02CurrentLawGateTest(unittest.TestCase):

    def test_cross_runtime_semantic_contract(self):
        fixture_path = pathlib.Path(__file__).resolve().parents[1] / (
            'internal/v2ingest/testdata/telecom_cross_runtime_contract.json')
        fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
        self.assertEqual(1, fixture.get('schema_version'))
        self.assertRegex(fixture.get('semantic_sha256', ''), r'^[0-9a-f]{64}$')
        self.assertEqual(
            fixture['semantic_sha256'],
            telecom_cross_runtime_contract_digest(),
            'Python/Go Telecom semantic matrices diverged')

    def test_every_declared_alternative_is_positive_and_negation_safe(self):
        contracts = (
            ('telecom01', auditor.TELECOM01_INTENT_ORDER,
             auditor.TELECOM01_SOURCE_URLS,
             auditor.TELECOM01_SOURCE_REQUIREMENTS,
             auditor.TELECOM01_OUTCOME_RULES,
             auditor.TELECOM01_PPP_SCOPE_RULES),
            ('telecom02', auditor.TELECOM02_INTENT_ORDER,
             auditor.TELECOM02_SOURCE_URLS,
             auditor.TELECOM02_SOURCE_REQUIREMENTS,
             auditor.TELECOM02_OUTCOME_RULES,
             auditor.TELECOM02_PPP_SCOPE_RULES),
            ('telecom03', auditor.TELECOM03_INTENT_ORDER,
             auditor.TELECOM03_SOURCE_URLS,
             auditor.TELECOM03_SOURCE_REQUIREMENTS,
             auditor.TELECOM03_OUTCOME_RULES,
             auditor.TELECOM03_PPP_SCOPE_RULES),
        )
        positive_cases = 0
        negated_cases = 0
        for (name, intent_order, source_urls, requirements,
             outcomes, scope_rules) in contracts:
            for intent in intent_order:
                for kind, _, groups in requirements[intent]:
                    for group_index, alternatives in enumerate(groups):
                        for alternative_index, alternative in enumerate(
                                alternatives):
                            positive_cases += 1
                            with self.subTest(
                                    contract=name, intent=intent, kind=kind,
                                    group=group_index,
                                    alternative=alternative_index,
                                    state='positive'):
                                self.assertTrue(
                                    auditor.aereo05_anchor_group_affirmed(
                                        'Fonte oficial específica; Regra atual: '
                                        + sentence(alternative),
                                        (alternative,)))

                            negated_cases += 1
                            with self.subTest(
                                    contract=name, intent=intent, kind=kind,
                                    group=group_index,
                                    alternative=alternative_index,
                                    state='negated'):
                                self.assertFalse(
                                    auditor.aereo05_anchor_group_affirmed(
                                        'Fonte oficial específica; É falso que '
                                        + sentence(alternative),
                                        (alternative,)))

                for matrix_name, rules in (
                        ('outcome', outcomes), ('scope', scope_rules)):
                    if intent not in rules:
                        continue
                    code, groups = rules[intent]
                    for group_index, alternatives in enumerate(groups):
                        for alternative_index, alternative in enumerate(
                                alternatives):
                            positive_cases += 1
                            with self.subTest(
                                    contract=name, intent=intent,
                                    matrix=matrix_name, group=group_index,
                                    alternative=alternative_index,
                                    state='positive'):
                                self.assertTrue(
                                    auditor.criminal13_declarative_alternative_affirmed_in_text(
                                        'Regra atual: ' + sentence(alternative),
                                        alternative))

                            negated_cases += 1
                            with self.subTest(
                                    contract=name, intent=intent,
                                    matrix=matrix_name, group=group_index,
                                    alternative=alternative_index,
                                    state='negated'):
                                self.assertFalse(
                                    auditor.criminal13_declarative_alternative_affirmed_in_text(
                                        'Não é verdade que ' +
                                        sentence(alternative), alternative))
        self.assertGreater(positive_cases, 0)
        self.assertEqual(positive_cases, negated_cases)

    def test_cdc_and_lgt_cannot_be_substituted_by_rgc_anchor_claim(self):
        contracts = (
            ('telecom01', auditor.TELECOM01_INTENT_ORDER,
             auditor.TELECOM01_SOURCE_URLS,
             auditor.TELECOM01_SOURCE_REQUIREMENTS,
             auditor.TELECOM01_OUTCOME_RULES,
             auditor.TELECOM01_PPP_SCOPE_RULES),
            ('telecom02', auditor.TELECOM02_INTENT_ORDER,
             auditor.TELECOM02_SOURCE_URLS,
             auditor.TELECOM02_SOURCE_REQUIREMENTS,
             auditor.TELECOM02_OUTCOME_RULES,
             auditor.TELECOM02_PPP_SCOPE_RULES),
            ('telecom03', auditor.TELECOM03_INTENT_ORDER,
             auditor.TELECOM03_SOURCE_URLS,
             auditor.TELECOM03_SOURCE_REQUIREMENTS,
             auditor.TELECOM03_OUTCOME_RULES,
             auditor.TELECOM03_PPP_SCOPE_RULES),
        )
        for (name, intent_order, source_urls, requirements,
             outcomes, scope_rules) in contracts:
            for intent in intent_order:
                record = alternative_page(
                    source_urls, requirements, intent)
                kept = []
                for source in record['official_sources']:
                    if source['url'] in {
                            source_urls['cdc'], source_urls['lgt']}:
                        continue
                    if source['url'] == source_urls['rgc']:
                        source['anchor_claim'] += (
                            '. CDC e LGT permanecem aplicáveis.')
                    kept.append(source)
                record['official_sources'] = kept
                reasons = direct_reasons(
                    record,
                    visible=alternative_visible(
                        outcomes, scope_rules, intent))
                for kind, code, _ in requirements[intent]:
                    if kind not in {'cdc', 'lgt'}:
                        continue
                    with self.subTest(
                            contract=name, intent=intent, kind=kind):
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            reasons)

    def test_telecom03_cardinality_dispatcher_and_stale_negation(self):
        self.assertEqual(20, len(auditor.TELECOM03_INTENT_ORDER))
        self.assertEqual(20, len(auditor.TELECOM03_INTENTS))
        self.assertEqual(
            auditor.TELECOM03_INTENTS,
            frozenset(auditor.TELECOM03_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.TELECOM03_INTENTS,
            frozenset(auditor.TELECOM03_OUTCOME_RULES))

        requirements = [
            requirement
            for intent in auditor.TELECOM03_INTENT_ORDER
            for requirement in auditor.TELECOM03_SOURCE_REQUIREMENTS[intent]
        ]
        self.assertEqual(84, len(requirements))
        self.assertEqual(84, len({code for _, code, _ in requirements}))
        self.assertEqual(19, len(auditor.TELECOM03_SOURCE_URLS))
        self.assertEqual(
            set(auditor.TELECOM03_SOURCE_URLS),
            {kind for kind, _, _ in requirements})
        self.assertEqual(
            293, sum(len(groups) for _, _, groups in requirements))
        self.assertEqual(
            162, sum(len(groups) for _, groups in
                     auditor.TELECOM03_OUTCOME_RULES.values()))
        self.assertEqual(16, len(auditor.TELECOM03_PPP_SCOPE_RULES))
        self.assertTrue(
            set(auditor.TELECOM03_PPP_SCOPE_RULES) <=
            auditor.TELECOM03_INTENTS)
        self.assertEqual(
            42, sum(len(groups) for _, groups in
                    auditor.TELECOM03_PPP_SCOPE_RULES.values()))
        self.assertEqual(54, len(auditor.TELECOM03_MICRO_FLOOR_ALTERNATIVES))
        self.assertEqual(22, len(
            auditor.TELECOM03_MISLEADING_ANCHOR_RULES))
        self.assertEqual(
            23, sum(len(claims) for claims in
                    auditor.TELECOM03_MISLEADING_ANCHOR_RULES.values()))
        self.assertEqual(20, len(auditor.TELECOM03_STALE_RULES))
        self.assertEqual(61, sum(len(alternatives) for _, alternatives in
                                 auditor.TELECOM03_STALE_RULES))
        self.assertEqual(
            {code for code, _ in auditor.TELECOM03_STALE_RULES},
            set(auditor.TELECOM03_STALE_RULE_INTENTS))

        stale_coverage = set()
        for code, scope in auditor.TELECOM03_STALE_RULE_INTENTS.items():
            with self.subTest(code=code, check='scope'):
                self.assertEqual(1, len(scope))
                self.assertTrue(stale_coverage.isdisjoint(scope))
                stale_coverage.update(scope)
        self.assertEqual(set(auditor.TELECOM03_INTENTS), stale_coverage)

        for intent in auditor.TELECOM03_INTENT_ORDER:
            record = alternative_page(
                auditor.TELECOM03_SOURCE_URLS,
                auditor.TELECOM03_SOURCE_REQUIREMENTS,
                intent)
            visible = alternative_visible(
                auditor.TELECOM03_OUTCOME_RULES,
                auditor.TELECOM03_PPP_SCOPE_RULES,
                intent)
            record['opening'] = visible
            with self.subTest(intent=intent, check='dispatcher_green'):
                self.assertEqual([], direct_reasons(record, visible))
                self.assertEqual(
                    [], auditor.current_legal_fact_reasons(record, CURRENT))

            first_kind, first_code, _ = (
                auditor.TELECOM03_SOURCE_REQUIREMENTS[intent][0])
            del record['official_sources'][0]
            with self.subTest(
                    intent=intent, kind=first_kind,
                    check='dispatcher_missing_source'):
                self.assertIn(
                    'current_legal_fact_source_missing:' + first_code,
                    direct_reasons(record, visible))
                self.assertIn(
                    'current_legal_fact_source_missing:' + first_code,
                    auditor.current_legal_fact_reasons(record, CURRENT))

        for code, alternatives in auditor.TELECOM03_STALE_RULES:
            intent = next(iter(
                auditor.TELECOM03_STALE_RULE_INTENTS[code]))
            record = alternative_page(
                auditor.TELECOM03_SOURCE_URLS,
                auditor.TELECOM03_SOURCE_REQUIREMENTS,
                intent)
            base = alternative_visible(
                auditor.TELECOM03_OUTCOME_RULES,
                auditor.TELECOM03_PPP_SCOPE_RULES,
                intent)
            for alternative in alternatives:
                wanted = 'current_legal_fact_stale_assertion:' + code
                with self.subTest(
                        code=code, alternative=alternative,
                        check='stale_positive'):
                    self.assertIn(
                        wanted,
                        direct_reasons(
                            record, base + ' ' + sentence(alternative)))
                with self.subTest(
                        code=code, alternative=alternative,
                        check='stale_negated'):
                    self.assertNotIn(
                        wanted,
                        direct_reasons(
                            record,
                            base + ' É falso que ' + sentence(alternative)))

    def test_telecom03_every_source_and_each_gate_family_is_enforced(self):
        """Exercise each T3 rule through the engine, not only its digest."""
        removals = 0
        decoys = 0
        decoy_kinds = set()
        anchor_omissions = 0
        anchor_negations = 0
        semantic_omissions = 0
        semantic_negations = 0

        for intent in auditor.TELECOM03_INTENT_ORDER:
            requirements = auditor.TELECOM03_SOURCE_REQUIREMENTS[intent]
            visible = alternative_visible(
                auditor.TELECOM03_OUTCOME_RULES,
                auditor.TELECOM03_PPP_SCOPE_RULES,
                intent)

            for source_index, (kind, code, groups) in enumerate(requirements):
                wanted_source = 'current_legal_fact_source_missing:' + code
                record = alternative_page(
                    auditor.TELECOM03_SOURCE_URLS,
                    auditor.TELECOM03_SOURCE_REQUIREMENTS, intent)
                del record['official_sources'][source_index]
                removals += 1
                with self.subTest(
                        intent=intent, kind=kind, action='remove_source'):
                    self.assertIn(wanted_source, direct_reasons(record, visible))

                if kind not in decoy_kinds:
                    decoy_kinds.add(kind)
                    decoy = exact_url_decoys(
                        auditor.TELECOM03_SOURCE_URLS[kind])[0]
                    record = alternative_page(
                        auditor.TELECOM03_SOURCE_URLS,
                        auditor.TELECOM03_SOURCE_REQUIREMENTS, intent)
                    record['official_sources'][source_index]['url'] = decoy
                    decoys += 1
                    with self.subTest(
                            intent=intent, kind=kind, decoy=decoy,
                            action='decoy_source'):
                        self.assertIn(
                            wanted_source, direct_reasons(record, visible))

                wanted_anchor = (
                    'current_legal_fact_source_anchor_missing:' + code)
                # Every requirement is independently exercised. The shared
                # alternative/negation test above covers every group literal.
                for target in (len(groups) - 1,):
                    witnesses = isolated_witnesses(
                        groups, target, source_group_affirmed)
                    self.assertIsNotNone(
                        witnesses,
                        'unisolatable T3 anchor group: '
                        f'{intent}/{kind}/group-{target}')
                    record = alternative_page(
                        auditor.TELECOM03_SOURCE_URLS,
                        auditor.TELECOM03_SOURCE_REQUIREMENTS, intent)
                    record['official_sources'][source_index][
                        'anchor_claim'] = ' '.join(witnesses)
                    anchor_omissions += 1
                    with self.subTest(
                            intent=intent, kind=kind, group=target,
                            action='omit_anchor'):
                        self.assertIn(
                            wanted_anchor, direct_reasons(record, visible))

                    negated = isolated_witnesses(
                        groups, target, source_group_affirmed,
                        'É falso que ' + groups[target][0])
                    self.assertIsNotNone(negated)
                    record = alternative_page(
                        auditor.TELECOM03_SOURCE_URLS,
                        auditor.TELECOM03_SOURCE_REQUIREMENTS, intent)
                    record['official_sources'][source_index][
                        'anchor_claim'] = ' '.join(negated)
                    anchor_negations += 1
                    with self.subTest(
                            intent=intent, kind=kind, group=target,
                            action='negate_anchor'):
                        self.assertIn(
                            wanted_anchor, direct_reasons(record, visible))

            primary_code, primary_groups = (
                auditor.TELECOM03_OUTCOME_RULES[intent])
            scope_rule = auditor.TELECOM03_PPP_SCOPE_RULES.get(intent)
            scope_groups = () if scope_rule is None else scope_rule[1]
            all_groups = tuple(primary_groups) + tuple(scope_groups)
            matrices = [('outcome', primary_code, primary_groups, 0)]
            if scope_rule is not None:
                matrices.append((
                    'scope', scope_rule[0], scope_groups,
                    len(primary_groups)))

            for matrix_name, code, groups, offset in matrices:
                wanted = 'current_legal_fact_outcome_missing:' + code
                # One independent group per outcome/scope code proves that
                # the generic engine consumes that exact T3 rule. Literal
                # coverage of every other group is enforced by the digest and
                # by test_every_declared_alternative_is_positive_and_negation_safe.
                for target in (len(groups) - 1,):
                    absolute_target = offset + target
                    witnesses = isolated_witnesses(
                        all_groups, absolute_target, visible_group_affirmed)
                    self.assertIsNotNone(
                        witnesses,
                        'unisolatable T3 semantic group: '
                        f'{intent}/{matrix_name}/group-{target}')
                    record = alternative_page(
                        auditor.TELECOM03_SOURCE_URLS,
                        auditor.TELECOM03_SOURCE_REQUIREMENTS, intent)
                    semantic_omissions += 1
                    with self.subTest(
                            intent=intent, matrix=matrix_name, group=target,
                            action='omit_semantic'):
                        self.assertIn(
                            wanted,
                            direct_reasons(record, ' '.join(witnesses)))

                    negated = isolated_witnesses(
                        all_groups, absolute_target, visible_group_affirmed,
                        'Não é verdade que ' + groups[target][0])
                    self.assertIsNotNone(negated)
                    semantic_negations += 1
                    with self.subTest(
                            intent=intent, matrix=matrix_name, group=target,
                            action='negate_semantic'):
                        self.assertIn(
                            wanted,
                            direct_reasons(record, ' '.join(negated)))

        misleading = 0
        for (intent, kind), claims in (
                auditor.TELECOM03_MISLEADING_ANCHOR_RULES.items()):
            requirements = auditor.TELECOM03_SOURCE_REQUIREMENTS[intent]
            source_index = [item[0] for item in requirements].index(kind)
            wanted = (
                'current_legal_fact_source_anchor_missing:' +
                requirements[source_index][1])
            visible = alternative_visible(
                auditor.TELECOM03_OUTCOME_RULES,
                auditor.TELECOM03_PPP_SCOPE_RULES,
                intent)
            for claim in claims:
                record = alternative_page(
                    auditor.TELECOM03_SOURCE_URLS,
                    auditor.TELECOM03_SOURCE_REQUIREMENTS, intent)
                record['official_sources'][source_index][
                    'anchor_claim'] += ' ' + sentence(claim)
                misleading += 1
                with self.subTest(
                        intent=intent, kind=kind, claim=claim,
                        action='misleading_anchor'):
                    self.assertIn(wanted, direct_reasons(record, visible))

        closed_intent = 'tel-provedor-fechou-plano-pago'
        closed_requirements = (
            auditor.TELECOM03_SOURCE_REQUIREMENTS[closed_intent])
        article_index = [item[0] for item in closed_requirements].index(
            'cdc_art20')
        article_code = closed_requirements[article_index][1]
        record = alternative_page(
            auditor.TELECOM03_SOURCE_URLS,
            auditor.TELECOM03_SOURCE_REQUIREMENTS, closed_intent)
        record['official_sources'][article_index]['url'] = (
            auditor.TELECOM03_SOURCE_URLS['cdc'])
        self.assertIn(
            'current_legal_fact_source_missing:' + article_code,
            direct_reasons(
                record,
                alternative_visible(
                    auditor.TELECOM03_OUTCOME_RULES,
                    auditor.TELECOM03_PPP_SCOPE_RULES,
                    closed_intent)))

        self.assertNotEqual(
            auditor.TELECOM03_SOURCE_URLS['cdc'],
            auditor.TELECOM03_SOURCE_URLS['cdc_art20'])
        self.assertEqual(84, removals)
        self.assertEqual(19, decoys)
        self.assertEqual(set(auditor.TELECOM03_SOURCE_URLS), decoy_kinds)
        self.assertEqual(84, anchor_omissions)
        self.assertEqual(anchor_omissions, anchor_negations)
        self.assertEqual(36, semantic_omissions)
        self.assertEqual(semantic_omissions, semantic_negations)
        self.assertEqual(23, misleading)

    def test_literal_cardinalities_and_unique_matrices(self):
        self.assertEqual(11, len(auditor.TELECOM02_INTENT_ORDER))
        self.assertEqual(11, len(auditor.TELECOM02_INTENTS))
        self.assertEqual(
            auditor.TELECOM02_INTENTS,
            frozenset(auditor.TELECOM02_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.TELECOM02_INTENTS,
            frozenset(auditor.TELECOM02_OUTCOME_RULES))

        requirements = [
            item
            for intent in auditor.TELECOM02_INTENT_ORDER
            for item in auditor.TELECOM02_SOURCE_REQUIREMENTS[intent]
        ]
        self.assertEqual(45, len(requirements))
        self.assertEqual(45, len({code for _, code, _ in requirements}))
        self.assertEqual(12, len(auditor.TELECOM02_SOURCE_URLS))
        self.assertEqual(
            set(auditor.TELECOM02_SOURCE_URLS),
            {kind for kind, _, _ in requirements})
        self.assertEqual(
            269, sum(len(groups) for _, _, groups in requirements))
        self.assertEqual(
            105, sum(len(groups) for _, groups in
                     auditor.TELECOM02_OUTCOME_RULES.values()))

        outcome_codes = [
            code for code, _ in auditor.TELECOM02_OUTCOME_RULES.values()]
        self.assertEqual(len(outcome_codes), len(set(outcome_codes)))
        for intent in auditor.TELECOM02_INTENT_ORDER:
            requirements_for_intent = (
                auditor.TELECOM02_SOURCE_REQUIREMENTS[intent])
            with self.subTest(intent=intent):
                self.assertGreaterEqual(len(requirements_for_intent), 3)
                self.assertLessEqual(len(requirements_for_intent), 5)
                kinds = [kind for kind, _, _ in requirements_for_intent]
                self.assertEqual(len(kinds), len(set(kinds)))
                self.assertEqual(1, kinds.count('cdc'))
                self.assertEqual(1, kinds.count('lgt'))

        self.assertEqual(11, len(auditor.TELECOM02_STALE_RULES))
        self.assertEqual(11, len(auditor.TELECOM02_STALE_RULE_INTENTS))
        self.assertEqual(
            30, sum(len(alternatives) for _, alternatives in
                    auditor.TELECOM02_STALE_RULES))
        self.assertEqual(
            {code for code, _ in auditor.TELECOM02_STALE_RULES},
            set(auditor.TELECOM02_STALE_RULE_INTENTS))
        coverage = set()
        for code, scope in auditor.TELECOM02_STALE_RULE_INTENTS.items():
            with self.subTest(code=code):
                self.assertEqual(1, len(scope))
                self.assertTrue(scope <= auditor.TELECOM02_INTENTS)
                self.assertTrue(coverage.isdisjoint(scope))
                coverage.update(scope)
        self.assertEqual(set(auditor.TELECOM02_INTENTS), coverage)
        self.assertEqual(14, len(auditor.TELECOM02_MISLEADING_ANCHOR_RULES))
        self.assertEqual(
            21, sum(len(items) for items in
                    auditor.TELECOM02_MISLEADING_ANCHOR_RULES.values()))
        self.assertEqual(11, len(auditor.TELECOM02_PPP_DEVICE_SCOPES))
        self.assertEqual(
            11, len(auditor.TELECOM02_PPP_VISIBLE_DEVICE_SCOPES))
        self.assertEqual(11, len(auditor.TELECOM02_PPP_SCOPE_CODES))
        self.assertEqual(11, len(auditor.TELECOM02_PPP_SCOPE_RULES))
        self.assertEqual(
            58, sum(len(groups) for _, groups in
                    auditor.TELECOM02_PPP_SCOPE_RULES.values()))
        self.assertEqual(3, len(auditor.TELECOM02_FORBIDDEN_SOURCE_URLS))
        self.assertEqual(2, len(auditor.TELECOM01_FORBIDDEN_SOURCE_URLS))

    def test_canonical_source_registry_is_literal_and_current(self):
        self.assertEqual({
            'rgc': (
                'https://informacoes.anatel.gov.br/legislacao/resolucoes/'
                '1900-resolucao-765'),
            'rgst': (
                'https://informacoes.anatel.gov.br/legislacao/resolucoes/'
                '2025/2022-resolucao-777'),
            'cdc': (
                'https://www.planalto.gov.br/ccivil_03/leis/'
                'l8078compilado.htm'),
            'lgt': (
                'https://www.planalto.gov.br/ccivil_03/leis/l9472.htm'),
            'civil_code': (
                'https://www.planalto.gov.br/ccivil_03/leis/2002/'
                'l10406compilada.htm'),
            'sac_decree': (
                'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/'
                'decreto/d11034.htm'),
            'ecommerce': (
                'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/'
                'decreto/d7962.htm'),
            'rqual_rule': (
                'https://informacoes.anatel.gov.br/legislacao/resolucoes/'
                '2019/1371-resolucao-717'),
            'anatel_rqual': (
                'https://www.gov.br/anatel/pt-br/dados/qualidade/'
                'qualidade-dos-servicos/regulamento'),
            'anatel_cancel': (
                'https://www.gov.br/anatel/pt-br/consumidor/'
                'conheca-seus-direitos/cancelamento'),
            'anatel_suspend': (
                'https://www.gov.br/anatel/pt-br/consumidor/'
                'conheca-seus-direitos/suspensao'),
            'anatel_offer': (
                'https://www.gov.br/anatel/pt-br/consumidor/'
                'conheca-seus-direitos/oferta-e-contratacao'),
        }, auditor.TELECOM02_SOURCE_URLS)

    def test_synthetic_fixtures_are_green(self):
        for intent in auditor.TELECOM02_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual([], direct_reasons(page(intent)))

    def test_every_required_source_and_exact_identity_are_enforced(self):
        removals = 0
        decoys = 0
        for intent in auditor.TELECOM02_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.TELECOM02_SOURCE_REQUIREMENTS[intent]):
                removals += 1
                sources = current_sources(intent)
                del sources[index]
                wanted = 'current_legal_fact_source_missing:' + code
                with self.subTest(intent=intent, kind=kind, action='remove'):
                    self.assertIn(
                        wanted, direct_reasons(page(intent, sources=sources)))
                for decoy in exact_url_decoys(
                        auditor.TELECOM02_SOURCE_URLS[kind]):
                    decoys += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(
                            intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            wanted,
                            direct_reasons(page(intent, sources=sources)))
        self.assertEqual(45, removals)
        self.assertEqual(585, decoys)

    def test_every_anchor_group_is_required_and_negation_safe(self):
        omissions = 0
        negations = 0
        overlaps = set()
        for intent in auditor.TELECOM02_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.TELECOM02_SOURCE_REQUIREMENTS[intent]):
                wanted = 'current_legal_fact_source_anchor_missing:' + code
                for target in range(len(groups)):
                    omissions += 1
                    witnesses = isolated_witnesses(
                        groups, target, source_group_affirmed)
                    if witnesses is None:
                        overlaps.add((intent, kind, target))
                        negations += 1
                        continue
                    sources = current_sources(intent)
                    sources[source_index]['anchor_claim'] = ' '.join(witnesses)
                    with self.subTest(
                            intent=intent, kind=kind, group=target,
                            action='omit'):
                        self.assertIn(
                            wanted,
                            direct_reasons(page(intent, sources=sources)))

                    negations += 1
                    claims = isolated_witnesses(
                        groups, target, source_group_affirmed,
                        'É falso que ' + groups[target][0])
                    self.assertIsNotNone(claims)
                    sources = current_sources(intent)
                    sources[source_index]['anchor_claim'] = ' '.join(claims)
                    with self.subTest(
                            intent=intent, kind=kind, group=target,
                            action='negate'):
                        self.assertIn(
                            wanted,
                            direct_reasons(page(intent, sources=sources)))
        self.assertEqual(269, omissions)
        self.assertEqual(269, negations)
        self.assertEqual(SOURCE_UNISOLATABLE_OVERLAPS, overlaps)

    def test_all_misleading_anchor_claims_are_blocked(self):
        count = 0
        for (intent, kind), claims in (
                auditor.TELECOM02_MISLEADING_ANCHOR_RULES.items()):
            requirements = auditor.TELECOM02_SOURCE_REQUIREMENTS[intent]
            source_index = [item[0] for item in requirements].index(kind)
            wanted = (
                'current_legal_fact_source_anchor_missing:' +
                requirements[source_index][1])
            for claim in claims:
                count += 1
                sources = current_sources(intent)
                sources[source_index]['anchor_claim'] += ' ' + sentence(claim)
                with self.subTest(intent=intent, kind=kind, claim=claim):
                    self.assertIn(
                        wanted,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(21, count)

    def test_every_outcome_group_is_required_and_negation_safe(self):
        omissions = 0
        negations = 0
        overlaps = set()
        for intent, (code, groups) in auditor.TELECOM02_OUTCOME_RULES.items():
            wanted = 'current_legal_fact_outcome_missing:' + code
            for target in range(len(groups)):
                omissions += 1
                witnesses = isolated_witnesses(
                    groups, target, visible_group_affirmed)
                if witnesses is None:
                    overlaps.add((intent, target))
                    negations += 1
                    continue
                visible = ' '.join(witnesses)
                with self.subTest(intent=intent, group=target, action='omit'):
                    self.assertIn(
                        wanted, direct_reasons(page(intent, visible=visible)))

                negations += 1
                values = isolated_witnesses(
                    groups, target, visible_group_affirmed,
                    'Não é verdade que ' + groups[target][0])
                self.assertIsNotNone(values)
                with self.subTest(
                        intent=intent, group=target, action='negate'):
                    self.assertIn(
                        wanted,
                        direct_reasons(page(
                            intent, visible=' '.join(values))))
        self.assertEqual(105, omissions)
        self.assertEqual(105, negations)
        self.assertEqual(OUTCOME_UNISOLATABLE_OVERLAPS, overlaps)

    def test_every_ppp_scope_group_is_required_and_negation_safe(self):
        omissions = 0
        negations = 0
        overlaps = set()
        for intent, (code, groups) in (
                auditor.TELECOM02_PPP_SCOPE_RULES.items()):
            _, primary_groups = auditor.TELECOM02_OUTCOME_RULES[intent]
            all_groups = tuple(primary_groups) + tuple(groups)
            for target in range(len(groups)):
                all_target = len(primary_groups) + target
                wanted = 'current_legal_fact_outcome_missing:' + code
                omissions += 1
                witnesses = isolated_witnesses(
                    all_groups, all_target, visible_group_affirmed)
                if witnesses is None:
                    overlaps.add((intent, target))
                    negations += 1
                    continue
                visible = ' '.join(witnesses)
                with self.subTest(intent=intent, group=target, action='omit'):
                    self.assertIn(
                        wanted, direct_reasons(page(intent, visible=visible)))

                negations += 1
                negated = isolated_witnesses(
                    all_groups, all_target, visible_group_affirmed,
                    'Não é verdade que ' + groups[target][0])
                self.assertIsNotNone(negated)
                with self.subTest(
                        intent=intent, group=target, action='negate'):
                    self.assertIn(
                        wanted, direct_reasons(page(
                            intent, visible=' '.join(negated))))
        self.assertEqual(58, omissions)
        self.assertEqual(58, negations)
        self.assertEqual(SCOPE_UNISOLATABLE_OVERLAPS, overlaps)

    def test_coupled_boundaries_reject_keyword_collage(self):
        cases = (
            ('tel-multa-fidelidade-quando-vale',
             'Pessoa natural', 'Qualquer consumidor'),
            ('tel-cancelar-sem-multa-servico-ruim',
             'Falha deve caracterizar descumprimento',
             'Qualquer oscilação basta'),
            ('tel-fidelidade-renovada-sem-consentimento',
             'Aceite expresso', 'Silêncio do consumidor'),
            ('tel-mudanca-endereco-sem-cobertura-multa',
             'Mudanca voluntaria nao prova descumprimento da prestadora',
             'Mudança sempre elimina a multa'),
            ('tel-cancelamento-automatico-digital',
             'Canal digital com atendente', 'Todo canal digital'),
            ('tel-operadora-dificulta-cancelamento',
             'Oferta de retencao nao substitui o pedido',
             'Retenção deve vir antes do pedido'),
            ('tel-cancelar-linha-de-falecido',
             'Rgc nao cria dispensa automatica de multa por morte',
             'Morte sempre elimina a multa'),
            ('tel-cancelar-um-servico-do-combo',
             'Isso nao garante editar parcialmente o combo',
             'O combo sempre pode ser editado parcialmente'),
            ('tel-arrependimento-7-dias-telecom',
             'Contratacao em loja nao tem esse direito geral',
             'Loja sempre tem sete dias'),
            ('tel-suspensao-temporaria-linha',
             'Consumidor adimplente', 'Qualquer consumidor'),
            ('tel-plano-antigo-descontinuado',
             'Escolha expressa do consumidor', 'Silêncio do consumidor'),
        )
        for intent, current, decoy in cases:
            visible = current_visible(intent).replace(current, decoy, 1)
            code, _ = auditor.TELECOM02_OUTCOME_RULES[intent]
            with self.subTest(intent=intent):
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + code,
                    direct_reasons(page(intent, visible=visible)))

    def test_all_stale_alternatives_are_scoped_and_negation_safe(self):
        all_intents = set(auditor.TELECOM02_INTENTS)
        count = 0
        for code, alternatives in auditor.TELECOM02_STALE_RULES:
            scope = auditor.TELECOM02_STALE_RULE_INTENTS[code]
            for alternative in alternatives:
                for intent in scope:
                    count += 1
                    wanted = 'current_legal_fact_stale_assertion:' + code
                    visible = current_visible(intent) + ' ' + sentence(
                        alternative)
                    with self.subTest(code=code, intent=intent):
                        self.assertIn(
                            wanted,
                            direct_reasons(page(intent, visible=visible)))
                    safe = (current_visible(intent) +
                            ' É falso que ' + sentence(alternative))
                    self.assertNotIn(
                        wanted,
                        direct_reasons(page(intent, visible=safe)))
                outside = all_intents - set(scope)
                if outside:
                    intent = sorted(outside)[0]
                    self.assertNotIn(
                        'current_legal_fact_stale_assertion:' + code,
                        direct_reasons(page(
                            intent, visible=current_visible(intent) +
                            ' ' + sentence(alternative))))
        self.assertEqual(30, count)

    def test_forbidden_sources_are_scoped_and_variant_safe(self):
        global_cases = {
            OLD_CANCEL_URL:
                'anatel_old_cancellation_faq_cites_revoked_resolution_632',
            OLD_ADDRESS_URL:
                'anatel_old_address_change_page_cites_revoked_resolution_614',
        }
        for raw_url, code in global_cases.items():
            for candidate in forbidden_url_identity_variants(raw_url):
                record = {
                    'intent_id': 'tel-futuro-shard',
                    'opening': 'Fato atual sem regra específica.',
                    'official_sources': [{'url': candidate}],
                }
                with self.subTest(code=code, candidate=candidate):
                    self.assertIn(
                        'current_legal_fact_source_stale:' + code,
                        direct_reasons(record))

        legacy = page('tel-plano-antigo-descontinuado')
        legacy['official_sources'].append({
            'url': auditor.TELECOM02_OFFER_URL,
            'name': 'Página de oferta e contratação',
            'anchor_claim': 'Orientação geral de oferta',
        })
        wanted = (
            'current_legal_fact_source_stale:'
            'anatel_offer_page_stale_silent_migration_for_legacy_plan')
        self.assertIn(wanted, direct_reasons(legacy))
        for intent in (
                'tel-multa-fidelidade-quando-vale',
                'tel-cancelar-um-servico-do-combo'):
            with self.subTest(intent=intent):
                self.assertNotIn(wanted, direct_reasons(page(intent)))

    def test_central_dispatcher_and_unknown_intent_boundaries(self):
        intent = auditor.TELECOM02_INTENT_ORDER[0]
        record = page(intent)
        first_code = auditor.TELECOM02_SOURCE_REQUIREMENTS[intent][0][1]
        record['official_sources'] = record['official_sources'][1:]
        self.assertIn(
            'current_legal_fact_source_missing:' + first_code,
            auditor.current_legal_fact_reasons(
                record, evaluation_date=CURRENT))

        unknown = {
            'intent_id': 'tel-futuro-shard',
            'opening': 'Fato atual sem regra específica.',
            'official_sources': [],
        }
        self.assertEqual([], direct_reasons(unknown))
        self.assertEqual([], auditor.current_telecom_legal_fact_reasons(
            {}, 'aer-outro-shard', 'Fato qualquer.', CURRENT))

    def test_expected_negative_cannot_be_copular_negated(self):
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'Se a parcela contestada ainda não foi quitada, sua cobrança '
                'fica suspensa.', 'fica suspensa'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A ADI manda informar em Rendimentos Isentos e Não '
                'Tributáveis, sem carnê-leão.', 'sem carne leao'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'É falso que a parcela foi quitada, sua cobrança fica '
                'suspensa.', 'fica suspensa'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'Não é falso que a parcela foi quitada, é falso que sua '
                'cobrança fica suspensa.', 'fica suspensa'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'É falso que a parcela foi quitada, não é falso que sua '
                'cobrança fica suspensa.', 'fica suspensa'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A cobrança fica suspensa, não é cancelada.',
                'fica suspensa'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A parcela foi quitada, a cobrança não fica suspensa.',
                'fica suspensa'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão não é sem cobrança.', 'sem cobrança'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão não fica sem cobrança.', 'sem cobrança'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão não pode ser sem cobrança.', 'sem cobrança'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão não fica totalmente sem cobrança.',
                'sem cobrança'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'Não há regra de que a multa não pode ultrapassar o '
                'benefício.',
                'não pode ultrapassar o benefício'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão é sem cobrança.', 'sem cobrança'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A multa não pode ultrapassar o benefício.',
                'não pode ultrapassar o benefício'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão não apenas é sem cobrança, como também '
                'preserva o número.',
                'sem cobrança'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A suspensão não altera o número e é sem cobrança.',
                'sem cobrança'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'Sem dúvida, a suspensão é sem cobrança.', 'sem cobrança'))
        self.assertFalse(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'É falso que a multa não pode ultrapassar o benefício.',
                'não pode ultrapassar o benefício'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'Não é falso que a multa não pode ultrapassar o benefício.',
                'não pode ultrapassar o benefício'))
        self.assertTrue(
            auditor.criminal13_declarative_alternative_affirmed_in_text(
                'A oferta individual não obriga a alteração parcial do '
                'contrato e não garante o desconto.',
                'oferta individual não obriga a alteração parcial do contrato'))

        intent = 'tel-suspensao-temporaria-linha'
        _, groups = auditor.TELECOM02_OUTCOME_RULES[intent]
        values = []
        for index, alternatives in enumerate(groups):
            values.append(
                'a suspensão não é sem cobrança'
                if index == 3 else alternatives[0])
        _, scope_groups = auditor.TELECOM02_PPP_SCOPE_RULES[intent]
        values.extend(alternatives[0] for alternatives in scope_groups)
        visible = '. '.join('Regra atual: ' + value for value in values) + '.'
        reasons = direct_reasons(page(intent, visible=visible))
        self.assertIn(
            'current_legal_fact_outcome_missing:' +
            auditor.TELECOM02_OUTCOME_RULES[intent][0],
            reasons)

    def test_real_shard_is_green_when_present(self):
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/telecom_energia-02.jsonl')
        self.assertTrue(
            shard.exists(), 'telecom_energia-02.jsonl is a required finalized shard')
        records = [json.loads(line) for line in shard.read_text().splitlines()
                   if line.strip()]
        self.assertEqual(11, len(records))
        self.assertEqual(
            list(auditor.TELECOM02_INTENT_ORDER),
            [record['intent_id'] for record in records])
        for record in records:
            sources = record.get('official_sources') or []
            with self.subTest(intent=record['intent_id']):
                self.assertGreaterEqual(len(sources), 3)
                self.assertLessEqual(len(sources), 5)
                urls = [source.get('url') for source in sources]
                self.assertEqual(len(urls), len(set(urls)))
                self.assertEqual(
                    1, urls.count(auditor.TELECOM02_SOURCE_URLS['cdc']))
                self.assertEqual(
                    1, urls.count(auditor.TELECOM02_SOURCE_URLS['lgt']))
                expected = {
                    auditor.TELECOM02_SOURCE_URLS[kind]
                    for kind, _, _ in auditor.TELECOM02_SOURCE_REQUIREMENTS[
                        record['intent_id']]
                }
                self.assertEqual(expected, set(urls))
                self.assertEqual([], direct_reasons(record))


if __name__ == '__main__':
    unittest.main()
