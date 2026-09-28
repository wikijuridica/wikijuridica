#!/usr/bin/env python3
"""Focused parity regressions for the aereo-01 current-law gate."""

import json
from pathlib import Path
import unittest

from tools import audit_v2_pages as auditor


SOURCE_FIXTURES = {
    'res400_article21': auditor.AEREO01_RESOLUTION_400_TJSP_CORE_URL,
    'res400_thresholds': auditor.AEREO01_RESOLUTION_400_TJSP_THRESHOLDS_URL,
    'res400_article27_full': (
        auditor.AEREO01_RESOLUTION_400_ARTICLE27_TJSP_URL),
    'res400_article12': (
        auditor.AEREO01_RESOLUTION_400_ARTICLE12_TJSP_URL),
    'res400_article20': auditor.AEREO01_ANAC_ARTICLES_20_27_AIR_URL,
    'res400_article30': (
        auditor.AEREO01_RESOLUTION_400_ARTICLE30_ANAC_URL),
    'res400_charter': auditor.AEREO01_ANAC_CHARTER_AIR_URL,
    'res800': auditor.AEREO01_RESOLUTION_800_ANAC_URL,
    'cba': auditor.AEREO01_CBA_CAMARA_URL,
    'cdc': auditor.AEREO01_CDC_CAMARA_URL,
    'jec': auditor.AEREO01_JEC_CAMARA_URL,
    'cc': auditor.AEREO01_CC_CAMARA_URL,
    'montreal': auditor.AEREO01_MONTREAL_CAMARA_URL,
    'consumidor_gov_general': (
        auditor.AEREO01_CONSUMIDOR_GOV_SERVICE_URL),
    'stj_delay_damage': auditor.AEREO01_STJ_DELAY_DAMAGE_URL,
    'stj_domestic_prescription': (
        auditor.AEREO01_STJ_DOMESTIC_PRESCRIPTION_URL),
    'tema1417': auditor.AEREO01_TEMA1417_TJSP_URL,
    'anac_passageiro_current': (
        'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/'
        'portaria-regulatoria/2026/portaria-1'),
    'anac_passageiro_scope': (
        'https://www.gov.br/pt-br/servicos/'
        'registrar-reclamacao-contra-empresa-aerea'),
}


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def current_visible(intent):
    _, groups = auditor.AEREO01_OUTCOME_RULES[intent]
    return ' '.join(sentence(alternatives[0]) for alternatives in groups)


def current_sources(intent):
    seen = set()
    sources = []
    for kind, _ in auditor.AEREO01_SOURCE_REQUIREMENTS[intent]:
        if kind in seen:
            continue
        seen.add(kind)
        sources.append({'url': SOURCE_FIXTURES[kind]})
    return sources


def page(intent, visible=None, sources=None):
    return {
        'intent_id': intent,
        'opening': current_visible(intent) if visible is None else visible,
        'official_sources': (
            current_sources(intent) if sources is None else sources),
    }


class Aereo01CurrentLawParityTest(unittest.TestCase):

    def test_covers_all_21_atraso_de_voo_intents(self):
        self.assertEqual(21, len(auditor.AEREO01_INTENTS))
        self.assertEqual(
            auditor.AEREO01_INTENTS,
            frozenset(auditor.AEREO01_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO01_INTENTS,
            frozenset(auditor.AEREO01_OUTCOME_RULES))

    def test_accepts_current_fact_fixture_for_every_intent(self):
        for intent in sorted(auditor.AEREO01_INTENTS):
            with self.subTest(intent=intent):
                self.assertEqual(
                    [], auditor.current_legal_fact_reasons(page(intent)))

    def test_real_aereo01_jsonl_has_zero_current_fact_reasons(self):
        shard = (Path(__file__).resolve().parents[1] / 'data' / 'editorial' /
                 'v2_pages' / 'aereo-01.jsonl')
        pages = [
            json.loads(line) for line in shard.read_text(
                encoding='utf-8').splitlines() if line.strip()
        ]
        self.assertEqual(21, len(pages))
        failures = {}
        for record in pages:
            reasons = auditor.current_legal_fact_reasons(record)
            if reasons:
                failures[record['intent_id']] = reasons
        self.assertEqual({}, failures)

    def test_requires_each_specific_official_source_kind(self):
        for intent in sorted(auditor.AEREO01_INTENTS):
            requirements = auditor.AEREO01_SOURCE_REQUIREMENTS[intent]
            for kind, code in requirements:
                with self.subTest(intent=intent, kind=kind):
                    sources = [
                        source for source in current_sources(intent)
                        if not auditor.has_aereo01_source_kind(
                            {'official_sources': [source]}, kind)
                    ]
                    reasons = auditor.current_legal_fact_reasons(
                        page(intent, sources=sources))
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code, reasons)

    def test_rejects_official_url_embedded_in_decoy(self):
        intent = 'aer-atraso-1h-direito-comunicacao'
        sources = [{
            'url': 'https://attacker.invalid/?next=' +
                   auditor.AEREO01_RESOLUTION_400_ARTICLE27_FULL_URL,
        }]
        self.assertIn(
            'current_legal_fact_source_missing:'
            'anac_resolution_400_article_27_over_one_hour',
            auditor.current_legal_fact_reasons(
                page(intent, sources=sources)))

    def test_accepts_safe_official_source_alternatives(self):
        cases = (
            ('aer-atraso-2h-alimentacao-voucher', 'res400_thresholds',
             auditor.AEREO01_RESOLUTION_400_ARTICLE27_TJSP_URL),
            ('aer-atraso-perda-conexao-mesmo-bilhete',
             'res400_article21',
             auditor.AEREO01_RESOLUTION_400_ARTICLE30_ANAC_URL),
            ('aer-atraso-como-provar-declaracao-motivo',
             'res400_article20',
             auditor.AEREO01_RESOLUTION_400_TJSP_CORE_URL),
            ('aer-reclamacao-consumidor-gov-companhia',
             'anac_passageiro_current',
             SOURCE_FIXTURES['anac_passageiro_scope']),
        )
        for intent, kind, replacement in cases:
            with self.subTest(intent=intent, kind=kind):
                sources = current_sources(intent)
                for source in sources:
                    if source['url'] == SOURCE_FIXTURES[kind]:
                        source['url'] = replacement
                self.assertEqual(
                    [], auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_rejects_tjsp_and_dou_query_decoys(self):
        cases = (
            ('aer-atraso-2h-alimentacao-voucher', 'res400_thresholds',
             auditor.AEREO01_RESOLUTION_400_TJSP_THRESHOLDS_URL + '&extra=1',
             'anac_resolution_400_article_27_over_two_hours'),
            ('aer-atraso-perda-conexao-mesmo-bilhete',
             'res400_article21',
             auditor.AEREO01_RESOLUTION_400_TJSP_CORE_URL.replace(
                 'casChecked=true&', ''),
             'anac_resolution_400_article_21_iv_connection_cause'),
            ('aer-atraso-dano-moral-quando-cabe', 'tema1417',
             auditor.AEREO01_TEMA1417_TJSP_URL + '&extra=1',
             'tema_1417_current_scope_official_judiciary'),
            ('aer-reclamacao-consumidor-gov-companhia',
             'anac_passageiro_current',
             auditor.AEREO01_ANAC_PASSAGEIRO_DOU_URL.replace(
                 'pagina=64', 'pagina=65'),
             'anac_passageiro_2026_effective_channel'),
        )
        for intent, kind, decoy, code in cases:
            with self.subTest(intent=intent):
                sources = [{'url': decoy}]
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_path_sources_allow_anchor_but_reject_empty_or_extra_query(self):
        base = auditor.AEREO01_RESOLUTION_800_ANAC_URL
        self.assertTrue(auditor.has_aereo01_source_kind(
            {'official_sources': [{'url': base + '#art1'}]}, 'res800'))
        for suffix in ('?', '?#art256', '?extra=1', '/extra#art256'):
            with self.subTest(suffix=suffix):
                self.assertFalse(auditor.has_aereo01_source_kind(
                    {'official_sources': [{'url': base + suffix}]}, 'res800'))

    def test_partial_res400_sources_do_not_satisfy_full_claim_kinds(self):
        cases = (
            ('aer-atraso-4h-reacomodacao-reembolso',
             'res400_article30',
             auditor.AEREO01_RESOLUTION_400_TJSP_CORE_URL,
             'anac_resolution_400_article_30_refund_utility'),
            ('aer-atraso-decolagem-ou-chegada-o-que-conta',
             'res400_article12',
             auditor.AEREO01_RESOLUTION_400_TJSP_CORE_URL,
             'anac_resolution_400_article_12_schedule_change'),
            ('aer-atraso-pernoite-hospedagem-transporte',
             'res400_article27_full',
             auditor.AEREO01_RESOLUTION_400_TJSP_THRESHOLDS_URL,
             'anac_resolution_400_article_27_overnight_lodging'),
            ('aer-atraso-como-provar-declaracao-motivo',
             'res400_article20',
             auditor.AEREO01_RESOLUTION_400_ARTICLE12_TJSP_URL,
             'anac_resolution_400_article_20_written_reason_on_request'),
            ('aer-atraso-voo-fretado-charter',
             'res400_charter',
             auditor.AEREO01_ANAC_ARTICLES_20_27_AIR_URL,
             'anac_resolution_400_article_1_nonregular_flight_scope'),
        )
        for intent, kind, partial, code in cases:
            with self.subTest(intent=intent):
                sources = current_sources(intent)
                for source in sources:
                    if source['url'] == SOURCE_FIXTURES[kind]:
                        source['url'] = partial
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_unstable_urls_do_not_satisfy_current_source_kinds(self):
        cases = (
            ('aer-reclamacao-anac-o-que-resolve',
             'anac_passageiro_current',
             auditor.AEREO01_ANAC_PASSAGEIRO_DOU_URL,
             'anac_passageiro_2026_effective_channel'),
            ('aer-resolucao-400-anac-direitos-resumo',
             'res800', auditor.AEREO01_RESOLUTION_800_DOU_URL,
             'anac_resolution_800_2026_current_amendment'),
            ('aer-atraso-dano-moral-quando-cabe', 'tema1417',
             'https://www.tjdft.jus.br/consultas/jurisprudencia/'
             'informativos/2026/informativo-de-jurisprudencia-n-546',
             'tema_1417_current_scope_official_judiciary'),
            ('aer-atraso-dano-moral-quando-cabe', 'tema1417',
             'https://www.tjdft.jus.br/consultas/jurisprudencia/'
             'arquivos/2026/3_inf_-546_pdf.pdf',
             'tema_1417_current_scope_official_judiciary'),
            ('aer-atraso-perda-conexao-mesmo-bilhete',
             'res400_article21', auditor.AEREO01_RESOLUTION_400_CEF_URL,
             'anac_resolution_400_article_21_iv_connection_cause'),
            ('aer-atraso-como-provar-declaracao-motivo',
             'res400_article20', auditor.AEREO01_RESOLUTION_400_CEF_URL,
             'anac_resolution_400_article_20_written_reason_on_request'),
            ('aer-atraso-pernoite-hospedagem-transporte',
             'res400_article27_full',
             auditor.AEREO01_RESOLUTION_400_ARTICLE27_FULL_URL,
             'anac_resolution_400_article_27_overnight_lodging'),
        )
        for intent, kind, unstable_url, code in cases:
            with self.subTest(intent=intent):
                sources = [
                    source for source in current_sources(intent)
                    if not auditor.has_aereo01_source_kind(
                        {'official_sources': [source]}, kind)
                ]
                sources.append({'url': unstable_url})
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_requires_every_material_outcome_group(self):
        for intent in sorted(auditor.AEREO01_INTENTS):
            outcome_code, groups = auditor.AEREO01_OUTCOME_RULES[intent]
            for index, alternatives in enumerate(groups):
                with self.subTest(intent=intent, group=index):
                    visible = current_visible(intent).replace(
                        sentence(alternatives[0]), '', 1)
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + outcome_code,
                        auditor.current_legal_fact_reasons(
                            page(intent, visible=visible)))

    def test_rejects_each_explicit_stale_fact(self):
        intent = 'aer-resolucao-400-anac-direitos-resumo'
        for code, alternatives in auditor.AEREO01_STALE_RULES:
            with self.subTest(code=code):
                visible = current_visible(intent) + ' ' + sentence(
                    alternatives[0])
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_corrective_negation_does_not_trigger_stale_fact(self):
        intent = 'aer-resolucao-400-anac-direitos-resumo'
        for code, alternatives in auditor.AEREO01_STALE_RULES:
            with self.subTest(code=code):
                visible = (
                    current_visible(intent) + ' É falso que ' +
                    alternatives[0] + '.')
                reasons = auditor.current_legal_fact_reasons(
                    page(intent, visible=visible))
                self.assertNotIn(
                    'current_legal_fact_stale_assertion:' + code, reasons)

    def test_rejects_inverted_article30_refund_relationships(self):
        code = 'aereo_article_30_refund_utility_relation_inverted'
        claims = (
            'Reembolso integral quando o trecho utilizado ainda foi útil.',
            'Reembolso proporcional quando o trecho utilizado perdeu utilidade.',
        )
        for intent in (
                'aer-atraso-4h-reacomodacao-reembolso',
                'aer-resolucao-400-anac-direitos-resumo'):
            for claim in claims:
                with self.subTest(intent=intent, claim=claim):
                    reasons = auditor.current_legal_fact_reasons(page(
                        intent, visible=current_visible(intent) + ' ' + claim))
                    self.assertIn(
                        'current_legal_fact_stale_assertion:' + code, reasons)

    def test_unrelated_negation_does_not_mask_later_false_fact(self):
        intent = 'aer-atraso-mau-tempo-direitos'
        visible = (
            current_visible(intent) +
            ' É falso que todo atraso gere indenização, mas qualquer chuva '
            'é força maior do CBA.')
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'aereo_weather_without_cba_qualified_restriction',
            auditor.current_legal_fact_reasons(
                page(intent, visible=visible)))

    def test_rejects_revoked_cefs_even_beside_valid_source(self):
        intent = 'aer-atraso-1h-direito-comunicacao'
        reason = (
            'current_legal_fact_source_stale:'
            'anac_resolution_400_revoked_cef')
        for stale_url in (
                auditor.AEREO01_RESOLUTION_400_CEF_2019_URL,
                auditor.AEREO01_RESOLUTION_400_CEF_URL):
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

    def test_question_and_historical_claim_do_not_supply_outcome(self):
        intent = 'aer-atraso-como-provar-declaracao-motivo'
        outcome_code, groups = auditor.AEREO01_OUTCOME_RULES[intent]
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


if __name__ == '__main__':
    unittest.main()
