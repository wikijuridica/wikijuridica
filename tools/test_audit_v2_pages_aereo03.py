#!/usr/bin/env python3
"""Focused parity regressions for the aereo-03 current-law gate."""

import copy
import datetime
import json
from pathlib import Path
import unittest

from tools import audit_v2_pages as auditor


PRE_CUTOFF = datetime.date(2026, 9, 13)
CUTOFF = datetime.date(2026, 9, 14)

SOURCE_URLS = {
    'res400_current': auditor.AEREO03_RESOLUTION_400_CURRENT_URL,
    'res280': auditor.AEREO03_RESOLUTION_280_CURRENT_URL,
    'anacpedia_overbooking': auditor.AEREO03_ANACPEDIA_OVERBOOKING_URL,
    'cdc': auditor.AEREO03_CDC_CAMARA_URL,
    'anac_des_decision': auditor.AEREO03_DES_CONVERSION_DECISION_URL,
    'bcb_converter': auditor.AEREO03_BCB_CONVERTER_URL,
    'passenger_cartilha': auditor.AEREO03_PASSENGER_CARTILHA_URL,
    'stj_resp750128': auditor.AEREO03_STJ_RESP750128_URL,
    'document_guide': auditor.AEREO03_DOCUMENT_GUIDE_URL,
    'cnh_guide': auditor.AEREO03_CNH_GUIDE_URL,
    'electronic_documents': auditor.AEREO03_ELECTRONIC_DOCUMENTS_URL,
    'anac_passenger_service': auditor.AEREO03_ANAC_PASSENGER_SERVICE_URL,
    'smaller_aircraft_decision':
        auditor.AEREO03_SMALLER_AIRCRAFT_DECISION_URL,
    'cba': auditor.AEREO03_CBA_CAMARA_URL,
    'res800': auditor.AEREO03_RESOLUTION_800_URL,
    'rbac121_emd25': auditor.AEREO03_RBAC121_EMD25_URL,
    'rbac108_emd08': auditor.AEREO03_RBAC108_EMD08_URL,
    'rbac108_emd10': auditor.AEREO03_RBAC108_EMD10_URL,
    'res799': auditor.AEREO03_RESOLUTION_799_URL,
}

SOURCE_FIXTURES = {
    kind: {'url': url, 'name': 'Fonte oficial',
           'anchor_claim': 'Escopo oficial específico.'}
    for kind, url in SOURCE_URLS.items()
}
SOURCE_FIXTURES.update({
    'anac_des_decision': {
        'url': auditor.AEREO03_DES_CONVERSION_DECISION_URL,
        'name': 'ANAC — decisão sobre 500 DES',
        'anchor_claim': (
            'Naquele caso concreto, usa a cotação do dia da preterição.'),
    },
    'stj_resp750128': {
        'url': auditor.AEREO03_STJ_RESP750128_URL,
        'name': 'STJ — REsp 750.128/RS sobre overbooking',
        'anchor_claim': (
            'No caso concreto, examina acomodação indevida na cabine de '
            'comando e reduz o quantum.'),
    },
    'smaller_aircraft_decision': {
        'url': auditor.AEREO03_SMALLER_AIRCRAFT_DECISION_URL,
        'name': 'ANAC — decisão sobre aeronave substituta',
        'anchor_claim': (
            'Mantém o enquadramento de preterição após troca por '
            'equipamento de menor capacidade.'),
    },
    'rbac121_emd25': {
        'url': auditor.AEREO03_RBAC121_EMD25_URL,
        'name': 'ANAC — RBAC 121 EMD 25, item 121.575(c)',
        'anchor_claim': (
            'Proíbe o operador de admitir a bordo pessoa que aparente estar '
            'embriagada.'),
    },
    'rbac108_emd08': {
        'url': auditor.AEREO03_RBAC108_EMD08_URL,
        'name': 'ANAC — RBAC 108 EMD 08, item 108.33(a)(2)',
        'anchor_claim': (
            'Exige impedir o embarque de passageiro indisciplinado e '
            'registrar relatório anexado ao Despacho AVSEC.'),
    },
    'rbac108_emd10': {
        'url': auditor.AEREO03_RBAC108_EMD10_URL,
        'name': 'ANAC — RBAC 108 EMD 10, item 108.33(a)',
        'anchor_claim': (
            'Exige garantir o controle de passageiro indisciplinado por '
            'ações previstas em regulamentação específica; versão vigente '
            'em 14 de setembro de 2026.'),
    },
})


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def outcome_sentences(intent, evaluation_date=PRE_CUTOFF):
    base = auditor.AEREO03_OUTCOME_RULES.get(intent)
    groups = list(base[1]) if base else []
    temporal = (
        auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES if
        evaluation_date < CUTOFF else
        auditor.AEREO03_POST_CUTOFF_OUTCOME_RULES).get(intent)
    if temporal:
        groups.extend(temporal[1])
    return [sentence(alternatives[0]) for alternatives in groups]


def current_visible(intent, evaluation_date=PRE_CUTOFF):
    return ' '.join(outcome_sentences(intent, evaluation_date))


def current_sources(intent, evaluation_date=PRE_CUTOFF):
    seen = set()
    sources = []
    for kind, _ in auditor.aereo03_source_requirements_as_of(
            intent, evaluation_date):
        fixture = copy.deepcopy(SOURCE_FIXTURES[kind])
        if fixture['url'] in seen:
            continue
        seen.add(fixture['url'])
        sources.append(fixture)
    return sources


def page(intent, visible=None, sources=None, evaluation_date=PRE_CUTOFF):
    return {
        'intent_id': intent,
        'opening': (
            current_visible(intent, evaluation_date)
            if visible is None else visible),
        'official_sources': (
            current_sources(intent, evaluation_date)
            if sources is None else sources),
    }


def reasons(record, evaluation_date=PRE_CUTOFF):
    return auditor.current_legal_fact_reasons(
        record, evaluation_date=evaluation_date)


def source_kind_reason(intent, kind, evaluation_date=PRE_CUTOFF):
    for candidate, code in auditor.aereo03_source_requirements_as_of(
            intent, evaluation_date):
        if candidate == kind:
            return 'current_legal_fact_source_missing:' + code
    raise AssertionError((intent, kind))


class Aereo03CurrentLawParityTest(unittest.TestCase):

    def test_covers_all_10_preterition_intents_in_canonical_order(self):
        self.assertEqual(10, len(auditor.AEREO03_INTENTS))
        self.assertEqual(
            auditor.AEREO03_INTENTS,
            frozenset(auditor.AEREO03_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO03_INTENTS,
            frozenset(auditor.AEREO03_OUTCOME_RULES) |
            frozenset(auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES))
        self.assertEqual(
            frozenset(auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES),
            frozenset(auditor.AEREO03_POST_CUTOFF_OUTCOME_RULES))
        self.assertEqual(10, len(auditor.AEREO03_INTENT_ORDER))

    def test_rule_inventory_matches_the_live_go_gate_contract(self):
        self.assertEqual(
            {
                'aer-pretericao-embarque-o-que-e': 11,
                'aer-pretericao-compensacao-valores-des': 13,
                'aer-overbooking-voluntarios-negociacao': 10,
                'aer-pretericao-dano-moral-presumido': 12,
                'aer-negativa-embarque-documento-domestico': 13,
                'aer-pretericao-como-provar': 10,
                'aer-troca-aeronave-menor-pretericao': 9,
                'aer-compensacao-nao-paga-como-cobrar': 11,
            },
            {intent: len(rule[1])
             for intent, rule in auditor.AEREO03_OUTCOME_RULES.items()})
        self.assertEqual(
            {
                'aer-negativa-embarque-passageiro-alterado': 13,
                'aer-companhia-baniu-passageiro-pode': 19,
            },
            {intent: len(rule[1]) for intent, rule in
             auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES.items()})
        self.assertEqual(
            {
                'aer-negativa-embarque-passageiro-alterado': 9,
                'aer-companhia-baniu-passageiro-pode': 17,
            },
            {intent: len(rule[1]) for intent, rule in
             auditor.AEREO03_POST_CUTOFF_OUTCOME_RULES.items()})
        self.assertEqual(14, len(auditor.AEREO03_STALE_RULES))
        self.assertEqual(
            106, sum(len(alternatives) for _, alternatives in
                     auditor.AEREO03_STALE_RULES))
        self.assertEqual(
            {code for code, _ in auditor.AEREO03_STALE_RULES},
            set(auditor.AEREO03_STALE_RULE_INTENTS))
        self.assertEqual(4, len(auditor.AEREO03_PRE_CUTOFF_STALE_RULES[0][1]))
        self.assertEqual(10, len(auditor.AEREO03_POST_CUTOFF_STALE_RULES[0][1]))

    def test_accepts_current_pre_cutoff_fixture_for_every_intent(self):
        for intent in auditor.AEREO03_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual([], reasons(page(intent), PRE_CUTOFF))

    def test_real_aereo03_jsonl_has_zero_pre_cutoff_reasons(self):
        shard = (Path(__file__).resolve().parents[1] / 'data' / 'editorial' /
                 'v2_pages' / 'aereo-03.jsonl')
        records = [
            json.loads(line) for line in shard.read_text(
                encoding='utf-8').splitlines() if line.strip()
        ]
        self.assertEqual(
            list(auditor.AEREO03_INTENT_ORDER),
            [record['intent_id'] for record in records])
        failures = {}
        for record in records:
            current = reasons(record, datetime.date(2026, 7, 12))
            if current:
                failures[record['intent_id']] = current
        self.assertEqual({}, failures)

    def test_requires_each_specific_official_source_kind(self):
        for evaluation_date in (PRE_CUTOFF, CUTOFF):
            for intent in auditor.AEREO03_INTENT_ORDER:
                for kind, code in auditor.aereo03_source_requirements_as_of(
                        intent, evaluation_date):
                    with self.subTest(
                            intent=intent, kind=kind,
                            evaluation_date=evaluation_date):
                        kept = [
                            source for source in current_sources(
                                intent, evaluation_date)
                            if not auditor.has_aereo03_source_kind(
                                {'official_sources': [source]}, kind)
                        ]
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            reasons(page(
                                intent, sources=kept,
                                evaluation_date=evaluation_date),
                                evaluation_date))

    def test_exact_source_kinds_reject_query_and_fragment_decoys(self):
        for evaluation_date in (PRE_CUTOFF, CUTOFF):
            for intent in auditor.AEREO03_INTENT_ORDER:
                for kind, _ in auditor.aereo03_source_requirements_as_of(
                        intent, evaluation_date):
                    url = SOURCE_URLS[kind]
                    decoys = (
                        url + '#decoy',
                        url + ('&' if '?' in url else '?') + 'extra=1',
                    )
                    for decoy in decoys:
                        with self.subTest(
                                intent=intent, kind=kind, url=decoy):
                            kept = [
                                source for source in current_sources(
                                    intent, evaluation_date)
                                if source['url'] != url
                            ]
                            mutated = copy.deepcopy(SOURCE_FIXTURES[kind])
                            mutated['url'] = decoy
                            kept.append(mutated)
                            self.assertIn(
                                source_kind_reason(
                                    intent, kind, evaluation_date),
                                reasons(page(
                                    intent, sources=kept,
                                    evaluation_date=evaluation_date),
                                    evaluation_date))

    def test_each_anchor_gate_rejects_missing_scope_metadata(self):
        for kind, (code, _) in auditor.AEREO03_SOURCE_ANCHOR_RULES.items():
            intent, evaluation_date = next(
                (current_intent, current_date)
                for current_date in (PRE_CUTOFF, CUTOFF)
                for current_intent in auditor.AEREO03_INTENT_ORDER
                if any(candidate == kind for candidate, _ in
                       auditor.aereo03_source_requirements_as_of(
                           current_intent, current_date)))
            sources = current_sources(intent, evaluation_date)
            wanted = SOURCE_URLS[kind]
            target = next(item for item in sources if item['url'] == wanted)
            target['name'] = 'Fonte oficial sem descrição material'
            target['anchor_claim'] = 'Documento oficial.'
            with self.subTest(kind=kind, intent=intent):
                self.assertIn(
                    'current_legal_fact_source_anchor_missing:' + code,
                    reasons(page(
                        intent, sources=sources,
                        evaluation_date=evaluation_date), evaluation_date))

    def test_des_anchor_rejects_generic_case_concreto(self):
        intent = 'aer-pretericao-compensacao-valores-des'
        sources = current_sources(intent)
        source = next(
            item for item in sources
            if item['url'] == auditor.AEREO03_DES_CONVERSION_DECISION_URL)
        source['anchor_claim'] = (
            'Trata-se de caso concreto e usa a cotação do dia da '
            'preterição.')
        self.assertIn(
            'current_legal_fact_source_anchor_missing:'
            'anac_des_conversion_case_specific_decision',
            reasons(page(intent, sources=sources)))

    def test_anchor_gate_rejects_negated_rbac_rule(self):
        intent = 'aer-negativa-embarque-passageiro-alterado'
        sources = current_sources(intent)
        source = next(
            item for item in sources
            if item['url'] == auditor.AEREO03_RBAC121_EMD25_URL)
        source['anchor_claim'] = (
            'O item 121.575(c) não proíbe o operador de admitir a bordo '
            'pessoa que aparente estar embriagada.')
        self.assertIn(
            'current_legal_fact_source_anchor_missing:'
            'anac_rbac_121_575_c_apparent_intoxication_scope',
            reasons(page(intent, sources=sources)))

    def test_anchor_gate_rejects_questions_and_historical_claims(self):
        intent = 'aer-negativa-embarque-passageiro-alterado'
        reason = (
            'current_legal_fact_source_anchor_missing:'
            'anac_rbac_121_575_c_apparent_intoxication_scope')
        for claim in (
                'A fonte pergunta: proíbe o operador de admitir a bordo '
                'pessoa que aparente estar embriagada?',
                'A regra antiga dizia: proíbe o operador de admitir a bordo '
                'pessoa que aparente estar embriagada.'):
            sources = current_sources(intent)
            source = next(
                item for item in sources
                if item['url'] == auditor.AEREO03_RBAC121_EMD25_URL)
            source['anchor_claim'] = claim
            with self.subTest(claim=claim):
                self.assertIn(reason, reasons(page(intent, sources=sources)))

    def test_rejects_revoked_and_obsolete_source_endpoints(self):
        intent = 'aer-pretericao-embarque-o-que-e'
        cases = (
            (auditor.AEREO03_RESOLUTION_400_CEF_URL,
             'anac_resolution_400_revoked_cef'),
            (auditor.AEREO03_RESOLUTION_400_CEF_2019_URL,
             'anac_resolution_400_revoked_cef'),
            (auditor.AEREO03_RESOLUTION_130_REVOKED_URL,
             'anac_resolution_130_revoked'),
            (auditor.AEREO03_ANAC_PASSENGER_COPY_URL,
             'anac_passenger_obsolete_copy_endpoint'),
            ('https://www.gov.br/anac/pt-br/assuntos/passageiros/'
             'copy_of_anac-passageiro',
             'anac_passenger_obsolete_copy_endpoint'),
            ('https://www.anac.gov.br/decisoes/400-0026',
             'anac_unrelated_decision_400_0026'),
        )
        for url, code in cases:
            for variant in (url, url + '#legacy',
                            url + ('&' if '?' in url else '?') + 'old=1'):
                with self.subTest(url=variant):
                    current = current_sources(intent) + [{'url': variant}]
                    self.assertIn(
                        'current_legal_fact_source_stale:' + code,
                        reasons(page(intent, sources=current)))

    def test_historical_and_wrong_sources_cannot_substitute_exact_kind(self):
        cases = (
            ('aer-pretericao-embarque-o-que-e', 'res400_current',
             auditor.AEREO03_RESOLUTION_400_ORIGINAL_URL),
            ('aer-negativa-embarque-documento-domestico', 'res400_current',
             auditor.AEREO03_RESOLUTION_130_REVOKED_URL),
            ('aer-pretericao-como-provar', 'anac_passenger_service',
             auditor.AEREO03_ANAC_PASSENGER_COPY_URL),
            ('aer-troca-aeronave-menor-pretericao',
             'smaller_aircraft_decision',
             auditor.AEREO03_DES_CONVERSION_DECISION_URL),
            ('aer-negativa-embarque-passageiro-alterado',
             'rbac121_emd25',
             auditor.AEREO03_RBAC121_EMD25_URL.removesuffix(
                 '/visualizar_ato_normativo')),
            ('aer-negativa-embarque-passageiro-alterado',
             'rbac108_emd08',
             auditor.AEREO03_RBAC108_EMD10_URL),
        )
        for intent, kind, wrong_url in cases:
            with self.subTest(intent=intent, kind=kind):
                wanted = SOURCE_URLS[kind]
                current = [
                    item for item in current_sources(intent)
                    if item['url'] != wanted
                ] + [{'url': wrong_url}]
                self.assertIn(
                    source_kind_reason(intent, kind),
                    reasons(page(intent, sources=current)))

    def test_temporal_rbac_sources_do_not_substitute_each_other(self):
        intent = 'aer-negativa-embarque-passageiro-alterado'
        for evaluation_date, required, decoy, code in (
                (PRE_CUTOFF, 'rbac108_emd08',
                 auditor.AEREO03_RBAC108_EMD10_URL,
                 'anac_rbac_108_emd08_pretransition'),
                (CUTOFF, 'rbac108_emd10',
                 auditor.AEREO03_RBAC108_EMD08_URL,
                 'anac_rbac_108_emd10_posttransition')):
            current = [
                item for item in current_sources(intent, evaluation_date)
                if item['url'] != SOURCE_URLS[required]
            ] + [{'url': decoy}]
            self.assertIn(
                'current_legal_fact_source_missing:' + code,
                reasons(page(
                    intent, sources=current,
                    evaluation_date=evaluation_date), evaluation_date))

    def test_resp750128_old_reaccommodation_metadata_is_rejected(self):
        intent = 'aer-pretericao-dano-moral-presumido'
        sources = current_sources(intent)
        source = next(
            item for item in sources
            if item['url'] == auditor.AEREO03_STJ_RESP750128_URL)
        source['name'] = 'STJ — REsp 750.128/RS sobre voo internacional'
        source['anchor_claim'] = (
            'Examina circunstâncias graves da reacomodação internacional.')
        self.assertIn(
            'current_legal_fact_source_anchor_missing:'
            'stj_resp_750128_overbooking_cockpit_case_scope',
            reasons(page(intent, sources=sources)))

    def test_requires_every_material_outcome_group(self):
        for intent, (outcome_code, groups) in (
                auditor.AEREO03_OUTCOME_RULES.items()):
            base_sentences = [sentence(group[0]) for group in groups]
            for index in range(len(groups)):
                with self.subTest(intent=intent, group=index):
                    visible = ' '.join(
                        base_sentences[:index] + base_sentences[index + 1:])
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + outcome_code,
                        reasons(page(intent, visible=visible)))

    def test_requires_every_pre_and_post_cutoff_outcome_group(self):
        for rule_map, evaluation_date in (
                (auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES, PRE_CUTOFF),
                (auditor.AEREO03_POST_CUTOFF_OUTCOME_RULES, CUTOFF)):
            for intent, (code, groups) in rule_map.items():
                base_rule = auditor.AEREO03_OUTCOME_RULES.get(intent)
                base = ([sentence(group[0]) for group in base_rule[1]]
                        if base_rule else [])
                temporal = [sentence(group[0]) for group in groups]
                for index in range(len(groups)):
                    with self.subTest(
                            intent=intent, date=evaluation_date, group=index):
                        visible = ' '.join(
                            base + temporal[:index] + temporal[index + 1:])
                        self.assertIn(
                            'current_legal_fact_outcome_missing:' + code,
                            reasons(page(
                                intent, visible=visible,
                                evaluation_date=evaluation_date),
                                evaluation_date))

    def test_every_stale_alternative_is_rejected_only_in_scope(self):
        all_intents = set(auditor.AEREO03_INTENTS)
        for code, alternatives in auditor.AEREO03_STALE_RULES:
            scope = auditor.AEREO03_STALE_RULE_INTENTS[code]
            intent = next(iter(scope))
            out_of_scope = next(iter(all_intents - set(scope)))
            reason = 'current_legal_fact_stale_assertion:' + code
            for alternative in alternatives:
                with self.subTest(code=code, alternative=alternative):
                    stale = current_visible(intent) + ' ' + sentence(alternative)
                    self.assertIn(
                        reason, reasons(page(intent, visible=stale)))
                    corrective = (
                        current_visible(intent) + ' É falso que ' +
                        alternative + '.')
                    self.assertNotIn(
                        reason, reasons(page(intent, visible=corrective)))
                    unrelated = (
                        current_visible(out_of_scope) + ' ' +
                        sentence(alternative))
                    self.assertNotIn(
                        reason,
                        reasons(page(out_of_scope, visible=unrelated)))

    def test_temporal_stale_rules_are_scoped_to_the_two_transition_intents(self):
        intent = 'aer-pretericao-embarque-o-que-e'
        pre_visible = (
            current_visible(intent, PRE_CUTOFF) +
            ' A Resolução 800 já está integralmente em vigor.')
        post_visible = (
            current_visible(intent, CUTOFF) +
            ' Apenas o art. 12 da Resolução 800 está em vigor.')
        self.assertNotIn(
            'current_legal_fact_temporal_stale:'
            'aereo_resolution_800_premature_effectiveness',
            reasons(page(intent, visible=pre_visible), PRE_CUTOFF))
        self.assertNotIn(
            'current_legal_fact_temporal_stale:'
            'aereo_resolution_800_transition_expired_2026_09_14',
            reasons(page(intent, visible=post_visible,
                         evaluation_date=CUTOFF), CUTOFF))

    def test_cutoff_is_exact_and_bidirectional_for_both_temporal_intents(self):
        for intent in auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES:
            pre = page(intent, evaluation_date=PRE_CUTOFF)
            post = page(intent, evaluation_date=CUTOFF)
            pre_code = auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES[intent][0]
            post_code = auditor.AEREO03_POST_CUTOFF_OUTCOME_RULES[intent][0]
            with self.subTest(intent=intent, phase='pre'):
                self.assertEqual([], reasons(pre, PRE_CUTOFF))
                post_reasons = reasons(pre, CUTOFF)
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + post_code,
                    post_reasons)
                self.assertIn(
                    'current_legal_fact_temporal_stale:'
                    'aereo_resolution_800_transition_expired_2026_09_14', post_reasons)
            with self.subTest(intent=intent, phase='post'):
                self.assertEqual([], reasons(post, CUTOFF))
                pre_reasons = reasons(post, PRE_CUTOFF)
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + pre_code,
                    pre_reasons)
                premature = page(
                    intent,
                    visible=(current_visible(intent, CUTOFF) +
                             ' A Resolução 800 já está integralmente em '
                             'vigor.'),
                    evaluation_date=PRE_CUTOFF)
                self.assertIn(
                    'current_legal_fact_temporal_stale:'
                    'aereo_resolution_800_premature_effectiveness',
                    reasons(premature, PRE_CUTOFF))

    def test_post_cutoff_rejects_live_pretransition_wording(self):
        shard = (Path(__file__).resolve().parents[1] / 'data' / 'editorial' /
                 'v2_pages' / 'aereo-03.jsonl')
        records = {
            record['intent_id']: record
            for record in (
                json.loads(line) for line in shard.read_text(
                    encoding='utf-8').splitlines() if line.strip())
        }
        for intent in auditor.AEREO03_PRE_CUTOFF_OUTCOME_RULES:
            with self.subTest(intent=intent):
                current = reasons(records[intent], CUTOFF)
                self.assertIn(
                    'current_legal_fact_outcome_missing:' +
                    auditor.AEREO03_POST_CUTOFF_OUTCOME_RULES[intent][0],
                    current)
                self.assertIn(
                    'current_legal_fact_temporal_stale:'
                    'aereo_resolution_800_transition_expired_2026_09_14', current)

    def test_questions_and_historical_claims_do_not_supply_outcomes(self):
        intent = 'aer-pretericao-compensacao-valores-des'
        outcome_code, groups = auditor.AEREO03_OUTCOME_RULES[intent]
        question = ' '.join(
            sentence(alternatives[0])[:-1] + '?' for alternatives in groups)
        historical = ' '.join(
            'A regra antiga dizia: ' + sentence(alternatives[0]).lower()
            for alternatives in groups)
        for visible in (question, historical):
            with self.subTest(visible=visible[:24]):
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + outcome_code,
                    reasons(page(intent, visible=visible)))

    def test_injected_date_accepts_date_datetime_and_iso_without_clock(self):
        intent = 'aer-negativa-embarque-passageiro-alterado'
        record = page(intent, evaluation_date=PRE_CUTOFF)
        for value in (
                PRE_CUTOFF,
                datetime.datetime(2026, 9, 13, 23, 59),
                '2026-09-13'):
            with self.subTest(value=value):
                self.assertEqual([], reasons(record, value))
        with self.assertRaises((TypeError, ValueError)):
            auditor.aereo03_evaluation_date('13/09/2026')

    def test_aware_datetime_uses_the_brazilian_civil_cutoff(self):
        brt = datetime.timezone(datetime.timedelta(hours=-3))
        local_value = datetime.datetime(2026, 9, 13, 23, 30, tzinfo=brt)
        self.assertEqual(
            PRE_CUTOFF, auditor.aereo03_evaluation_date(local_value))
        intent = 'aer-negativa-embarque-passageiro-alterado'
        record = page(intent, evaluation_date=PRE_CUTOFF)
        self.assertEqual([], reasons(record, local_value))
        midnight = datetime.datetime(2026, 9, 14, 0, 0, tzinfo=brt)
        post_record = page(intent, evaluation_date=CUTOFF)
        self.assertEqual(CUTOFF, auditor.aereo03_evaluation_date(midnight))
        self.assertEqual([], reasons(post_record, midnight))

    def test_default_date_matches_the_go_direct_validator_snapshot(self):
        self.assertEqual(
            datetime.date(2026, 7, 11),
            auditor.aereo03_evaluation_date())


if __name__ == '__main__':
    unittest.main()
