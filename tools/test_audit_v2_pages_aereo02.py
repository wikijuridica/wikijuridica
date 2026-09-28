#!/usr/bin/env python3
"""Focused parity regressions for the aereo-02 current-law gate."""

import json
from pathlib import Path
import unittest

from tools import audit_v2_pages as auditor


SOURCE_FIXTURES = {
    'res400_article12': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article20': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article21': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article27': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article28': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article29': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article30': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_article31': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'res400_current': auditor.AEREO02_RESOLUTION_400_CURRENT_URL,
    'cba': auditor.AEREO02_CBA_CAMARA_URL,
    'cdc': auditor.AEREO02_CDC_CAMARA_URL,
    'cc': auditor.AEREO02_CC_CAMARA_URL,
    'recovery_law': auditor.AEREO02_RECOVERY_LAW_CAMARA_URL,
    'stj_delay_damage': auditor.AEREO02_STJ_DELAY_DAMAGE_URL,
    'stj_intermediary': auditor.AEREO02_STJ_INTERMEDIARY_URL,
    'stj_downgrade': auditor.AEREO02_STJ_DOWNGRADE_URL,
    'stj_recovery_tema1051': auditor.AEREO02_STJ_RECOVERY_TEMA1051_URL,
    'stj_recovery_plan': auditor.AEREO02_STJ_RECOVERY_PLAN_URL,
    'tema1417': auditor.AEREO02_TEMA1417_TJSP_URL,
    'stj_error_fare': auditor.AEREO02_STJ_ERROR_FARE_DECISION_URL,
}


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def current_visible(intent):
    _, groups = auditor.AEREO02_OUTCOME_RULES[intent]
    return ' '.join(sentence(alternatives[0]) for alternatives in groups)


def current_sources(intent):
    seen = set()
    sources = []
    for kind, _ in auditor.AEREO02_SOURCE_REQUIREMENTS[intent]:
        url = SOURCE_FIXTURES[kind]
        if url in seen:
            continue
        seen.add(url)
        sources.append({'url': url})
    return sources


def page(intent, visible=None, sources=None):
    return {
        'intent_id': intent,
        'opening': current_visible(intent) if visible is None else visible,
        'official_sources': (
            current_sources(intent) if sources is None else sources),
    }


class Aereo02CurrentLawParityTest(unittest.TestCase):

    def test_covers_all_16_cancelamento_intents(self):
        self.assertEqual(16, len(auditor.AEREO02_INTENTS))
        self.assertEqual(
            auditor.AEREO02_INTENTS,
            frozenset(auditor.AEREO02_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO02_INTENTS,
            frozenset(auditor.AEREO02_OUTCOME_RULES))

    def test_accepts_current_fact_fixture_for_every_intent(self):
        for intent in sorted(auditor.AEREO02_INTENTS):
            with self.subTest(intent=intent):
                self.assertEqual(
                    [], auditor.current_legal_fact_reasons(page(intent)))

    def test_real_aereo02_jsonl_has_zero_current_fact_reasons(self):
        shard = (Path(__file__).resolve().parents[1] / 'data' / 'editorial' /
                 'v2_pages' / 'aereo-02.jsonl')
        pages = [
            json.loads(line) for line in shard.read_text(
                encoding='utf-8').splitlines() if line.strip()
        ]
        self.assertEqual(16, len(pages))
        failures = {}
        for record in pages:
            reasons = auditor.current_legal_fact_reasons(record)
            if reasons:
                failures[record['intent_id']] = reasons
        self.assertEqual({}, failures)

    def test_requires_each_specific_official_source_kind(self):
        for intent in sorted(auditor.AEREO02_INTENTS):
            for kind, code in auditor.AEREO02_SOURCE_REQUIREMENTS[intent]:
                with self.subTest(intent=intent, kind=kind):
                    sources = [
                        source for source in current_sources(intent)
                        if not auditor.has_aereo02_source_kind(
                            {'official_sources': [source]}, kind)
                    ]
                    reasons = auditor.current_legal_fact_reasons(
                        page(intent, sources=sources))
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code, reasons)

    def test_original_or_old_cef_cannot_alone_prove_current_res400(self):
        cases = (
            ('aer-alteracao-programada-aviso-72h',
             auditor.AEREO02_RESOLUTION_400_ORIGINAL_URL,
             'anac_resolution_400_article_12_schedule_change'),
            ('aer-cancelamento-credito-nao-pode-ser-imposto',
             auditor.AEREO02_RESOLUTION_400_CEF_2019_URL,
             'anac_resolution_400_article_31_credit_consent_and_use'),
            ('aer-cancelamento-reembolso-prazo-7-dias',
             auditor.AEREO02_REFUND_DECISION_URL,
             'anac_resolution_400_article_29_seven_day_refund'),
            ('aer-cancelamento-sem-reacomodacao-indenizacao',
             auditor.AEREO02_ARTICLE27_FULL_URL,
             'anac_resolution_400_article_27_material_assistance'),
        )
        for intent, old_url, code in cases:
            with self.subTest(intent=intent):
                reasons = auditor.current_legal_fact_reasons(page(
                    intent, sources=[{'url': old_url}]))
                self.assertIn(
                    'current_legal_fact_source_missing:' + code, reasons)

    def test_rejects_wrong_downgrade_cnot_even_beside_correct_source(self):
        intent = 'aer-reacomodacao-classe-inferior-downgrade'
        stale_url = auditor.AEREO02_STJ_WRONG_DOWNGRADE_URL
        variants = (
            stale_url, stale_url + '#crypto', stale_url + '&extra=1',
            stale_url.replace('?livre=', '?extra=1&livre=', 1),
            stale_url.replace('/informativo/?', '/informativo?', 1),
            stale_url.replace('stj.jus.br/', 'stj.jus.br//', 1),
            stale_url.replace(
                'https://processo.stj.jus.br/',
                'https://legacy@processo.stj.jus.br/', 1),
            stale_url.replace(
                '%40CNOT%3D021575', '%40CNOT+%3D+021575', 1),
            stale_url.replace(
                '%40CNOT%3D021575', '%40CNOT%3D%22021575%22', 1),
        )
        for variant in variants:
            with self.subTest(url=variant):
                sources = current_sources(intent) + [{'url': variant}]
                self.assertIn(
                    'current_legal_fact_source_stale:'
                    'stj_cnot_021575_unrelated_crypto_precedent',
                    auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_wrong_downgrade_matcher_has_semantic_boundaries(self):
        intent = 'aer-reacomodacao-classe-inferior-downgrade'
        reason = (
            'current_legal_fact_source_stale:'
            'stj_cnot_021575_unrelated_crypto_precedent')
        stale_url = auditor.AEREO02_STJ_WRONG_DOWNGRADE_URL
        for unrelated in (
                stale_url.replace('021575', '0215750', 1),
                stale_url.replace('%40CNOT', '%40XCNOT', 1)):
            with self.subTest(url=unrelated):
                sources = current_sources(intent) + [{'url': unrelated}]
                self.assertNotIn(
                    reason, auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_rejects_revoked_cefs_even_beside_current_source(self):
        intent = 'aer-cancelamento-reembolso-prazo-7-dias'
        reason = (
            'current_legal_fact_source_stale:'
            'anac_resolution_400_revoked_cef')
        for stale_url in (
                auditor.AEREO02_RESOLUTION_400_CEF_2019_URL,
                auditor.AEREO02_RESOLUTION_400_CEF_URL):
            for variant in (
                    stale_url, stale_url + '#art29',
                    stale_url + '?utm=legacy', stale_url + '/',
                    stale_url.replace(
                        'https://www.anac.gov.br/',
                        'https://www.anac.gov.br//', 1),
                    stale_url.replace(
                        'https://www.anac.gov.br/',
                        'https://legacy@www.anac.gov.br/', 1),
                    stale_url.replace(
                        'https://www.anac.gov.br/',
                        'https://www.anac.gov.br:443/', 1)):
                with self.subTest(stale_url=variant):
                    sources = current_sources(intent) + [{'url': variant}]
                    self.assertIn(
                        reason, auditor.current_legal_fact_reasons(
                            page(intent, sources=sources)))

    def test_rejects_natural_downgrade_contradictions_beside_correct_text(self):
        intent = 'aer-reacomodacao-classe-inferior-downgrade'
        reason = (
            'current_legal_fact_stale_assertion:'
            'aereo_downgrade_fixed_percentage_waiver_or_automatic_moral')
        contradictions = (
            'A Resolução 400 fixa uma porcentagem nacional automática para '
            'downgrade.',
            'A Resolução 400 estabelece tabela percentual geral para '
            'downgrade.',
            'Todo downgrade automaticamente gera dano moral.',
            'Aceitar a classe inferior significa quitação automática da '
            'diferença.',
            'Dano material dispensa demonstração e nexo.',
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                visible = current_visible(intent) + ' ' + contradiction
                self.assertIn(
                    reason, auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_rejects_exact_query_decoys(self):
        cases = (
            ('aer-alteracao-programada-aviso-72h', 'res400_article12',
             auditor.AEREO02_RESOLUTION_400_CURRENT_URL + '?extra=1',
             'anac_resolution_400_article_12_schedule_change'),
            ('aer-cancelamento-malha-aerea-motivo-valido', 'tema1417',
             auditor.AEREO02_TEMA1417_TJSP_URL + '&extra=1',
             'tema_1417_current_scope_official_judiciary'),
            ('aer-cancelamento-companhia-recuperacao-judicial',
             'stj_recovery_tema1051',
             auditor.AEREO02_STJ_RECOVERY_TEMA1051_URL + '&extra=1',
             'stj_tema_1051_credit_trigger_date'),
            ('aer-tarifa-erro-companhia-cancelou-bilhete', 'stj_error_fare',
             auditor.AEREO02_STJ_ERROR_FARE_DECISION_URL + '&extra=1',
             'stj_resp_1794991_gross_system_error_facts'),
        )
        for intent, kind, decoy, code in cases:
            with self.subTest(intent=intent, kind=kind):
                sources = [
                    source for source in current_sources(intent)
                    if not auditor.has_aereo02_source_kind(
                        {'official_sources': [source]}, kind)
                ]
                sources.append({'url': decoy})
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_requires_every_material_outcome_group(self):
        for intent in sorted(auditor.AEREO02_INTENTS):
            outcome_code, groups = auditor.AEREO02_OUTCOME_RULES[intent]
            for index, alternatives in enumerate(groups):
                with self.subTest(intent=intent, group=index):
                    visible = current_visible(intent).replace(
                        sentence(alternatives[0]), '', 1)
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + outcome_code,
                        auditor.current_legal_fact_reasons(
                            page(intent, visible=visible)))

    def test_rejects_each_stale_fact_and_accepts_corrective_negation(self):
        intent = 'aer-cancelamento-opcoes-passageiro-escolhe'
        for code, alternatives in auditor.AEREO02_STALE_RULES:
            for alternative in alternatives:
                with self.subTest(code=code, alternative=alternative):
                    stale = current_visible(intent) + ' ' + sentence(
                        alternative)
                    reason = 'current_legal_fact_stale_assertion:' + code
                    self.assertIn(
                        reason, auditor.current_legal_fact_reasons(
                            page(intent, visible=stale)))
                    corrective = (
                        current_visible(intent) + ' É falso que ' +
                        alternative + '.')
                    self.assertNotIn(
                        reason, auditor.current_legal_fact_reasons(
                            page(intent, visible=corrective)))

    def test_question_and_historical_claim_do_not_supply_outcome(self):
        intent = 'aer-cancelamento-reembolso-prazo-7-dias'
        outcome_code, groups = auditor.AEREO02_OUTCOME_RULES[intent]
        question = ' '.join(
            sentence(alternatives[0])[:-1] + '?' for alternatives in groups)
        historical = ' '.join(
            'A regra antiga dizia: ' + sentence(alternatives[0]).lower()
            for alternatives in groups)
        for visible in (question, historical):
            with self.subTest(visible=visible[:20]):
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + outcome_code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_accepts_carrier_cancellation_tariff_contrast(self):
        intent = 'aer-cancelamento-tarifa-nao-reembolsavel'
        first = sentence(auditor.AEREO02_OUTCOME_RULES[intent][1][0][0])
        contrast = (
            'Se a companhia cancela, a regra da tarifa não reembolsável não '
            'prevalece. Tarifa promocional pode impor condições ao '
            'cancelamento voluntário do passageiro, mas não permite à '
            'companhia cobrar multa quando ela própria cancela o voo.')
        visible = current_visible(intent).replace(first, contrast, 1)
        self.assertEqual(
            [], auditor.current_legal_fact_reasons(
                page(intent, visible=visible)))


if __name__ == '__main__':
    unittest.main()
