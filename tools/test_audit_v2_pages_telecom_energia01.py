#!/usr/bin/env python3
"""Adversarial Go/Python parity tests for Telecom/Energia shard 01."""

import datetime
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 13)
OLD_RGC_URLS = (
    'https://informacoes.anatel.gov.br/legislacao/resolucoes/2014/'
    '750-resolucao-632',
)
SUMULA359_URL = (
    'https://processo.stj.jus.br/SCON/sumstj/toc.jsp?sumula=359.num.')
SUMULA479_URL = (
    'https://processo.stj.jus.br/SCON/sumstj/toc.jsp?sumula=479.num.')
SUMULA479_REASON = (
    'current_legal_fact_source_stale:'
    'stj_sumula_479_financial_institutions_not_telecom_authority')

SOURCE_UNISOLATABLE_OVERLAPS = frozenset({
    ('tel-cobranca-servico-nao-contratado', 'rgc', 5),
    ('tel-cobranca-apos-cancelamento', 'rgc', 4),
    ('tel-fatura-paga-duas-vezes', 'rgc', 5),
    ('tel-devolucao-em-dobro-telefonia', 'rgc', 0),
    ('tel-devolucao-em-dobro-telefonia', 'rgc', 3),
    ('tel-mudanca-plano-nao-autorizada', 'rgc', 4),
    ('tel-parcelas-aparelho-nao-comprado', 'rgc', 3),
    ('tel-negativacao-conta-telefone-contestada', 'rgc', 6),
    ('tel-contestar-fatura-operadora', 'rgc', 5),
    ('tel-ligacoes-nao-reconhecidas', 'rgc', 3),
})
OUTCOME_UNISOLATABLE_OVERLAPS = frozenset()
SCOPE_UNISOLATABLE_OVERLAPS = frozenset({
    ('tel-fatura-paga-duas-vezes', 0),
    ('tel-devolucao-em-dobro-telefonia', 0),
    ('tel-mudanca-plano-nao-autorizada', 0),
    ('tel-negativacao-conta-telefone-contestada', 0),
    ('tel-ligacoes-nao-reconhecidas', 0),
})


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
        'url': auditor.TELECOM01_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            witness_sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [source_fixture(requirement) for requirement in
            auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]]


def outcome_fixture_values(intent):
    """Choose affirmative fixtures that keep neighboring groups isolated."""
    _, groups = auditor.TELECOM01_OUTCOME_RULES[intent]
    values = [alternatives[0] for alternatives in groups]
    if intent == 'tel-fatura-papel-cobrada':
        # "Emissão sem ônus" would also satisfy the distinct no-fee group.
        values[0] = groups[0][1]
    return values


def current_visible(intent):
    values = [witness_sentence(value)
              for value in outcome_fixture_values(intent)]
    scope_rule = auditor.TELECOM01_PPP_SCOPE_RULES.get(intent)
    if scope_rule is not None:
        values.extend(witness_sentence(alternatives[0])
                      for alternatives in scope_rule[1])
    return ' '.join(values)


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


def exact_url_decoys(raw_url):
    """Variants that remain invalid because canonical sources are exact."""
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
    """Variants that must still identify a blacklisted endpoint."""
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


class TelecomEnergia01CurrentLawGateTest(unittest.TestCase):

    def test_literal_cardinalities_and_unique_matrices(self):
        self.assertEqual(14, len(auditor.TELECOM01_INTENT_ORDER))
        self.assertEqual(14, len(auditor.TELECOM01_INTENTS))
        self.assertEqual(
            auditor.TELECOM01_INTENTS,
            frozenset(auditor.TELECOM01_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.TELECOM01_INTENTS,
            frozenset(auditor.TELECOM01_OUTCOME_RULES))

        requirements = [
            item
            for intent in auditor.TELECOM01_INTENT_ORDER
            for item in auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]
        ]
        self.assertEqual(61, len(requirements))
        self.assertEqual(61, len({code for _, code, _ in requirements}))
        self.assertEqual(14, len(auditor.TELECOM01_SOURCE_URLS))
        self.assertEqual(
            set(auditor.TELECOM01_SOURCE_URLS),
            {kind for kind, _, _ in requirements})
        self.assertEqual(
            331, sum(len(groups) for _, _, groups in requirements))
        self.assertEqual(
            117, sum(len(groups) for _, groups in
                     auditor.TELECOM01_OUTCOME_RULES.values()))

        self.assertEqual(14, len(auditor.TELECOM01_STALE_RULES))
        self.assertEqual(14, len(auditor.TELECOM01_STALE_RULE_INTENTS))
        self.assertEqual(
            34, sum(len(alternatives) for _, alternatives in
                    auditor.TELECOM01_STALE_RULES))
        self.assertEqual(
            {code for code, _ in auditor.TELECOM01_STALE_RULES},
            set(auditor.TELECOM01_STALE_RULE_INTENTS))
        self.assertEqual(10, len(auditor.TELECOM01_MISLEADING_ANCHOR_RULES))
        self.assertEqual(
            14, sum(len(items) for items in
                    auditor.TELECOM01_MISLEADING_ANCHOR_RULES.values()))
        self.assertEqual(2, len(auditor.TELECOM01_FORBIDDEN_SOURCE_URLS))
        self.assertEqual(10, len(auditor.TELECOM_GLOBAL_STALE_RULES))
        self.assertEqual(
            33, sum(len(alternatives) for _, alternatives in
                   auditor.TELECOM_GLOBAL_STALE_RULES))
        self.assertEqual(14, len(auditor.TELECOM01_PPP_DEVICE_SCOPES))
        self.assertEqual(
            14, len(auditor.TELECOM01_PPP_VISIBLE_DEVICE_SCOPES))
        self.assertEqual(14, len(auditor.TELECOM01_PPP_SCOPE_RULES))
        self.assertEqual(
            81, sum(len(groups) for _, groups in
                    auditor.TELECOM01_PPP_SCOPE_RULES.values()))

        outcome_codes = [
            code for code, _ in auditor.TELECOM01_OUTCOME_RULES.values()]
        self.assertEqual(len(outcome_codes), len(set(outcome_codes)))
        for intent in auditor.TELECOM01_INTENT_ORDER:
            with self.subTest(intent=intent):
                requirements_for_intent = (
                    auditor.TELECOM01_SOURCE_REQUIREMENTS[intent])
                self.assertGreaterEqual(len(requirements_for_intent), 3)
                self.assertLessEqual(len(requirements_for_intent), 6)
                kinds = [kind for kind, _, _ in requirements_for_intent]
                self.assertEqual(len(kinds), len(set(kinds)))
                self.assertEqual(1, kinds.count('cdc'))
                self.assertEqual(1, kinds.count('lgt'))
        for code, scope in auditor.TELECOM01_STALE_RULE_INTENTS.items():
            with self.subTest(code=code):
                self.assertTrue(scope)
                self.assertLessEqual(scope, auditor.TELECOM01_INTENTS)

    def test_canonical_source_registry_is_literal_and_current(self):
        self.assertIn(
            'www.subtel.gob.cl', auditor.EXACT_ALLOWED_SOURCE_HOSTS)
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
            'lgpd': (
                'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/'
                'lei/l13709compilado.htm'),
            'anatel_cancel': (
                'https://www.gov.br/anatel/pt-br/consumidor/'
                'conheca-seus-direitos/cancelamento'),
            'anatel_billing': (
                'https://www.gov.br/anatel/pt-br/consumidor/'
                'conheca-seus-direitos/cobranca'),
            'anatel_prepaid_registry': (
                'https://www.gov.br/anatel/pt-br/regulado/'
                'acompanhamento-e-controle/combate-a-golpes-e-fraudes/'
                'cadastro-de-celulares-pre-pagos'),
            'stj_earesp_676608': (
                'https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ATC?'
                'CodOrgaoJgdr=&SeqCgrmaSessao=&dt=20210330&formato=PDF&'
                'nreg=201500497769&salvar=false&seq=58120459&tipo=5'),
            'stj_resp_1817576': (
                'https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/'
                'Noticias/12082021-E-abusiva-a-inclusao-de-novos-servicos-'
                'no-plano-de-celular-sem-o-consentimento-do-consumidor.aspx'),
            'stj_sumula_359': SUMULA359_URL,
            'stj_sumula_385': (
                'https://processo.stj.jus.br/SCON/pesquisar.jsp?'
                'b=SUMU&sumula=385'),
            'mercosur_roaming_decree': (
                'https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/'
                'decreto/d12782.htm'),
            'brazil_chile_roaming': (
                'https://www.subtel.gob.cl/'
                'chile-y-brasil-acuerdan-el-fin-de-los-cobros-adicionales-'
                'por-roaming-internacional-entre-ambos-paises/'),
        }, auditor.TELECOM01_SOURCE_URLS)

    def test_real_shard_order_source_budget_occurrences_and_gate(self):
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/telecom_energia-01.jsonl')
        records = [json.loads(line) for line in shard.read_text().splitlines()
                   if line.strip()]
        self.assertEqual(14, len(records))
        self.assertEqual(
            list(auditor.TELECOM01_INTENT_ORDER),
            [record['intent_id'] for record in records])
        self.assertEqual(
            61, sum(len(record['official_sources']) for record in records),
            'real shard must carry all 61 required source identities')
        self.assertEqual(
            14, len({source['url'] for record in records
                     for source in record['official_sources']}))

        by_intent = {record['intent_id']: record for record in records}
        self.assertEqual(14, len(by_intent))
        required = 0
        for intent in auditor.TELECOM01_INTENT_ORDER:
            record = by_intent[intent]
            sources = record['official_sources']
            with self.subTest(intent=intent):
                self.assertGreaterEqual(len(sources), 3)
                self.assertLessEqual(len(sources), 6)
                urls = [source['url'] for source in sources]
                self.assertEqual(len(urls), len(set(urls)))
                self.assertEqual(
                    1, urls.count(auditor.TELECOM01_SOURCE_URLS['cdc']))
                self.assertEqual(
                    1, urls.count(auditor.TELECOM01_SOURCE_URLS['lgt']))
                for kind, _, _ in (
                        auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]):
                    required += 1
                    self.assertEqual(
                        1, urls.count(auditor.TELECOM01_SOURCE_URLS[kind]))
                self.assertEqual([], direct_reasons(record))
        self.assertEqual(61, required)

    def test_synthetic_fixtures_are_green(self):
        for intent in auditor.TELECOM01_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual([], direct_reasons(page(intent)))

    def test_removing_each_of_the_61_required_sources_is_detected(self):
        count = 0
        for intent in auditor.TELECOM01_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                del sources[index]
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(61, count)

    def test_every_required_source_rejects_hostile_url_decoys(self):
        count = 0
        for intent in auditor.TELECOM01_INTENT_ORDER:
            for index, (kind, code, _) in enumerate(
                    auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]):
                for decoy in exact_url_decoys(
                        auditor.TELECOM01_SOURCE_URLS[kind]):
                    count += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            direct_reasons(page(intent, sources=sources)))
        self.assertEqual(793, count)

    def test_every_material_anchor_group_is_required(self):
        count = 0
        overlaps = set()
        for intent in auditor.TELECOM01_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]):
                for omitted in range(len(groups)):
                    count += 1
                    witnesses = isolated_witnesses(
                        groups, omitted, source_group_affirmed)
                    if witnesses is None:
                        overlaps.add((intent, kind, omitted))
                        continue
                    sources = current_sources(intent)
                    sources[source_index]['anchor_claim'] = ' '.join(witnesses)
                    with self.subTest(
                            intent=intent, kind=kind, group=omitted):
                        self.assertIn(
                            'current_legal_fact_source_anchor_missing:' + code,
                            direct_reasons(page(intent, sources=sources)))
        self.assertEqual(331, count)
        self.assertEqual(SOURCE_UNISOLATABLE_OVERLAPS, overlaps)

    def test_every_anchor_group_rejects_meta_negation(self):
        prefixes = (
            'A fonte não afirma que ',
            'É falso que ',
            'É incorreto afirmar que ',
        )
        count = 0
        overlaps = set()
        for intent in auditor.TELECOM01_INTENT_ORDER:
            for source_index, (kind, code, groups) in enumerate(
                    auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]):
                for target in range(len(groups)):
                    witnesses = isolated_witnesses(
                        groups, target, source_group_affirmed)
                    if witnesses is None:
                        overlaps.add((intent, kind, target))
                    for prefix in prefixes:
                        count += 1
                        if witnesses is None:
                            continue
                        claims = isolated_witnesses(
                            groups, target, source_group_affirmed,
                            prefix + groups[target][0])
                        self.assertIsNotNone(claims)
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
        self.assertEqual(993, count)
        self.assertEqual(SOURCE_UNISOLATABLE_OVERLAPS, overlaps)

    def test_all_14_misleading_anchor_claims_are_blocked(self):
        count = 0
        for (intent, kind), alternatives in (
                auditor.TELECOM01_MISLEADING_ANCHOR_RULES.items()):
            requirements = auditor.TELECOM01_SOURCE_REQUIREMENTS[intent]
            source_index = [item[0] for item in requirements].index(kind)
            for false_claim in alternatives:
                count += 1
                sources = current_sources(intent)
                sources[source_index]['anchor_claim'] += (
                    ' ' + sentence(false_claim))
                with self.subTest(
                        intent=intent, kind=kind, false_claim=false_claim):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' +
                        requirements[source_index][1],
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(14, count)

    def test_each_of_the_117_outcome_groups_is_required(self):
        count = 0
        overlaps = set()
        for intent, (code, groups) in (
                auditor.TELECOM01_OUTCOME_RULES.items()):
            for omitted in range(len(groups)):
                count += 1
                witnesses = isolated_witnesses(
                    groups, omitted, visible_group_affirmed)
                if witnesses is None:
                    overlaps.add((intent, omitted))
                    continue
                visible = ' '.join(witnesses)
                with self.subTest(intent=intent, group=omitted):
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        direct_reasons(page(intent, visible=visible)))
        self.assertEqual(117, count)
        self.assertEqual(OUTCOME_UNISOLATABLE_OVERLAPS, overlaps)

    def test_every_outcome_group_rejects_meta_negation(self):
        prefixes = (
            'É falso que ',
            'Não é verdade que ',
            'É incorreto afirmar que ',
        )
        count = 0
        overlaps = set()
        for intent, (code, groups) in (
                auditor.TELECOM01_OUTCOME_RULES.items()):
            for target in range(len(groups)):
                witnesses = isolated_witnesses(
                    groups, target, visible_group_affirmed)
                if witnesses is None:
                    overlaps.add((intent, target))
                for prefix in prefixes:
                    count += 1
                    if witnesses is None:
                        continue
                    values = isolated_witnesses(
                        groups, target, visible_group_affirmed,
                        prefix + groups[target][0])
                    self.assertIsNotNone(values)
                    with self.subTest(
                            intent=intent, group=target, prefix=prefix):
                        self.assertIn(
                            'current_legal_fact_outcome_missing:' + code,
                            direct_reasons(page(
                                intent, visible=' '.join(values))))
        self.assertEqual(351, count)
        self.assertEqual(OUTCOME_UNISOLATABLE_OVERLAPS, overlaps)

    def test_every_ppp_scope_group_is_required_and_negation_safe(self):
        omissions = 0
        negations = 0
        overlaps = set()
        for intent, (code, groups) in (
                auditor.TELECOM01_PPP_SCOPE_RULES.items()):
            _, primary_groups = auditor.TELECOM01_OUTCOME_RULES[intent]
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
        self.assertEqual(81, omissions)
        self.assertEqual(81, negations)
        self.assertEqual(SCOPE_UNISOLATABLE_OVERLAPS, overlaps)

    def test_coupled_outcomes_reject_keyword_collage(self):
        test_cases = {
            'tel-aumento-plano-sem-aviso': {
                'impede usar o art 23 do rgc como fundamento atual':
                    'o art 23 do rgc continua vigente outro dispositivo foi anulado',
            },
            'tel-parcelas-aparelho-nao-comprado': {
                'financiamento pode exigir contestacao paralela perante o credor':
                    'financiamento',
                'anatel alcanca a prestadora e a cobranca de telecomunicacoes':
                    'anatel',
            },
            'tel-fatura-papel-cobrada': {
                'proibido cobrar pela segunda via':
                    'a segunda via pode ser cobrada',
            },
        }
        for intent, replacements in test_cases.items():
            visible = current_visible(intent)
            for current, decoy in replacements.items():
                visible = visible.replace(current.capitalize(),
                                          decoy.capitalize())
            code, _ = auditor.TELECOM01_OUTCOME_RULES[intent]
            with self.subTest(intent=intent):
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + code,
                    direct_reasons(page(intent, visible=visible)))

    def test_chile_authority_attribution_cannot_stay_on_anatel(self):
        intent = 'tel-roaming-internacional-conta-alta'
        visible = current_visible(intent).replace(
            'Subtel regulador chileno', 'A Anatel informa')
        code, _ = auditor.TELECOM01_OUTCOME_RULES[intent]
        self.assertIn(
            'current_legal_fact_outcome_missing:' + code,
            direct_reasons(page(intent, visible=visible)))

    def test_all_34_stale_alternatives_are_scoped_and_negation_safe(self):
        all_intents = set(auditor.TELECOM01_INTENTS)
        count = 0
        for code, alternatives in auditor.TELECOM01_STALE_RULES:
            scope = auditor.TELECOM01_STALE_RULE_INTENTS[code]
            for alternative in alternatives:
                for intent in scope:
                    count += 1
                    visible = current_visible(intent) + ' ' + sentence(
                        alternative)
                    wanted = 'current_legal_fact_stale_assertion:' + code
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
        self.assertEqual(34, count)

    def test_resolution_632_source_is_globally_blocked_for_any_tel_intent(self):
        wanted = (
            'current_legal_fact_source_stale:'
            'anatel_resolution_632_revoked_as_current_rgc')
        count = 0
        for raw_url in OLD_RGC_URLS:
            for candidate in forbidden_url_identity_variants(raw_url):
                count += 1
                record = {
                    'intent_id': 'tel-futuro-shard',
                    'opening': 'Fato atual sem regra específica.',
                    'official_sources': [{
                        'url': candidate,
                        'name': 'Antigo RGC',
                        'anchor_claim': 'Texto histórico',
                    }],
                }
                with self.subTest(candidate=candidate):
                    self.assertIn(wanted, direct_reasons(record))
        self.assertGreaterEqual(count, 8)

    def test_resolution_632_source_requires_clear_historical_boundary(self):
        wanted = (
            'current_legal_fact_source_stale:'
            'anatel_resolution_632_revoked_as_current_rgc')
        historical = {
            'url': OLD_RGC_URLS[0],
            'name': 'Resolução Anatel 632/2014, fonte histórica',
            'anchor_claim': (
                'A Resolução Anatel 632/2014 foi revogada. '
                'É aplicável somente a fatos anteriores a 1º de setembro '
                'de 2025.'),
        }
        record = {
            'intent_id': 'tel-futuro-shard',
            'opening': 'Análise temporal do regime anterior.',
            'official_sources': [historical],
        }
        self.assertNotIn(wanted, direct_reasons(record))

        unclear = dict(record)
        unclear['official_sources'] = [dict(historical)]
        unclear['official_sources'][0]['anchor_claim'] = (
            'A Resolução Anatel 632/2014 foi revogada. Texto histórico.')
        self.assertIn(wanted, direct_reasons(unclear))

        negated = dict(record)
        negated['official_sources'] = [dict(historical)]
        negated['official_sources'][0]['anchor_claim'] = (
            'É falso que a Resolução Anatel 632/2014 foi revogada. '
            'É aplicável somente a fatos anteriores a 1º de setembro de '
            '2025.')
        self.assertIn(wanted, direct_reasons(negated))

        current_claim = dict(record)
        current_claim['opening'] = (
            'A Resolução Anatel 632/2014 é o RGC vigente.')
        reasons = direct_reasons(current_claim)
        self.assertNotIn(wanted, reasons)
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'anatel_resolution_632_current_rgc', reasons)

        recognized = page('tel-cobranca-servico-nao-contratado')
        recognized['official_sources'].append(historical)
        self.assertNotIn(wanted, direct_reasons(recognized))

    def test_global_telecom_stale_text_is_negation_safe(self):
        for code, alternatives in auditor.TELECOM_GLOBAL_STALE_RULES:
            for alternative in alternatives:
                wanted = 'current_legal_fact_stale_assertion:' + code
                record = {
                    'intent_id': 'tel-futuro-shard',
                    'opening': sentence(alternative),
                    'official_sources': [],
                }
                with self.subTest(code=code, alternative=alternative):
                    self.assertIn(wanted, direct_reasons(record))
                record['opening'] = 'É falso que ' + sentence(alternative)
                self.assertNotIn(wanted, direct_reasons(record))

    def test_sumula_479_is_scoped_and_query_sensitive(self):
        intent = 'tel-linha-no-meu-cpf-fraude'
        blocked = (
            SUMULA479_URL,
            SUMULA479_URL + '&tracking=1#top',
            SUMULA479_URL.replace('sumula=', 'SUMULA='),
            SUMULA479_URL.replace(
                'sumula=479.num.',
                'sumula=359.num.&sumula=479.num.'),
            SUMULA479_URL.replace(
                '479.num.', urllib.parse.quote(' 479.num. ')),
            ' ' + SUMULA479_URL + ' ',
        )
        for candidate in blocked:
            sources = current_sources(intent)
            sources.append({
                'url': candidate,
                'name': 'Súmula de instituições financeiras',
                'anchor_claim': 'Autoridade inadequada para telecom',
            })
            with self.subTest(candidate=candidate):
                self.assertIn(
                    SUMULA479_REASON,
                    direct_reasons(page(intent, sources=sources)))

        allowed_same_endpoint = (
            SUMULA359_URL,
            SUMULA479_URL.replace('479.num.', '479'),
            SUMULA479_URL.replace('479.num.', '359.num.'),
            SUMULA479_URL.replace(
                'processo.stj.jus.br', 'different.example'),
        )
        for candidate in allowed_same_endpoint:
            sources = current_sources(intent)
            sources.append({
                'url': candidate,
                'name': 'Fonte de controle',
                'anchor_claim': 'Consulta distinta',
            })
            with self.subTest(candidate=candidate):
                self.assertNotIn(
                    SUMULA479_REASON,
                    direct_reasons(page(intent, sources=sources)))

        other = 'tel-negativacao-conta-telefone-contestada'
        sources = current_sources(other)
        sources.append({
            'url': SUMULA479_URL,
            'name': 'Fonte fora do escopo',
            'anchor_claim': 'Autoridade inadequada para outro contexto',
        })
        self.assertNotIn(
            SUMULA479_REASON,
            direct_reasons(page(other, sources=sources)))

    def test_central_dispatcher_and_unknown_intent_boundaries(self):
        intent = auditor.TELECOM01_INTENT_ORDER[0]
        record = page(intent)
        first_code = auditor.TELECOM01_SOURCE_REQUIREMENTS[intent][0][1]
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


if __name__ == '__main__':
    unittest.main()
