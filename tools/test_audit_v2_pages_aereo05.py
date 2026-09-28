#!/usr/bin/env python3
"""Adversarial parity tests for the aereo-05 current-law gate."""

import copy
import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 12)
PRE_CEF_REVOCATION = datetime.date(2026, 4, 27)
CEF_REVOCATION = datetime.date(2026, 4, 28)
ARTICLE12_INTENT = 'aer-remarcacao-taxa-diferenca-tarifaria'

# Frozen independently from the literal declarations in
# internal/v2ingest/current_legal_facts_aereo05.go.  It binds the ordered
# portfolio, all 30 source requirements, 8 exact identities, every generic
# and intent-specific anchor, every outcome, all stale alternatives/scopes,
# and the Portaria 8.018 revocation boundary in one Go-contract fixture.
AEREO05_GO_CONTRACT_SHA256 = (
    '80cc51e949ba038d1682fbe41a2d7df97c6580215d4620c77496b75304ae5013')


def contract_snapshot():
    return {
        'intent_order': auditor.AEREO05_INTENT_ORDER,
        'source_urls': sorted(auditor.AEREO05_SOURCE_URLS.items()),
        'source_requirements': sorted(
            auditor.AEREO05_SOURCE_REQUIREMENTS.items()),
        'general_anchors': sorted(
            auditor.AEREO05_GENERAL_SOURCE_ANCHOR_RULES.items()),
        'specific_anchors': sorted(
            (intent, kind, rule)
            for (intent, kind), rule in
            auditor.AEREO05_INTENT_SOURCE_ANCHOR_RULES.items()),
        'outcomes': sorted(auditor.AEREO05_OUTCOME_RULES.items()),
        'stale_rules': auditor.AEREO05_STALE_RULES,
        'stale_scopes': sorted(
            (code, sorted(scope))
            for code, scope in auditor.AEREO05_STALE_RULE_INTENTS.items()),
        'cef_revoked_at':
            auditor.AEREO05_CEF_8018_REVOKED_AT.isoformat(),
        'cef_stale_source_markers':
            auditor.AEREO05_CEF_STALE_SOURCE_MARKERS,
        'cef_current_identifiers':
            auditor.AEREO05_CEF_CURRENT_IDENTIFIERS,
        'cef_current_assertions':
            auditor.AEREO05_CEF_CURRENT_ASSERTIONS,
        'cef_current_disclaimers':
            auditor.AEREO05_CEF_CURRENT_DISCLAIMERS,
    }


def contract_digest():
    payload = json.dumps(
        contract_snapshot(), sort_keys=True, separators=(',', ':'),
        ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def anchor_rule(intent, kind):
    rule = auditor.AEREO05_INTENT_SOURCE_ANCHOR_RULES.get((intent, kind))
    if rule is None:
        rule = auditor.AEREO05_GENERAL_SOURCE_ANCHOR_RULES.get(kind)
    return rule


def source_fixture(intent, kind):
    code, groups = anchor_rule(intent, kind)
    del code
    return {
        'url': auditor.AEREO05_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [
        source_fixture(intent, kind)
        for kind, _ in auditor.AEREO05_SOURCE_REQUIREMENTS[intent]
    ]


def current_visible(intent):
    _, groups = auditor.AEREO05_OUTCOME_RULES[intent]
    return ' '.join(sentence(alternatives[0]) for alternatives in groups)


def article12_semantic_cases():
    fixture = pathlib.Path(__file__).resolve().parents[1] / (
        'internal/v2ingest/testdata/'
        'aereo05_article12_semantic_matrix.json')
    cases = json.loads(fixture.read_text(encoding='utf-8'))
    if not cases:
        raise AssertionError('aereo-05 article 12 semantic matrix is empty')
    return cases


def article12_case_visible(case):
    _, groups = auditor.AEREO05_OUTCOME_RULES[ARTICLE12_INTENT]
    parts = []
    for index, alternatives in enumerate(groups):
        if case['mode'] == 'append_valid':
            skip = False
        elif case['mode'] == 'replace_article12':
            skip = 5 <= index <= 8
        elif case['mode'] == 'replace_late_notice':
            skip = index == 5
        elif case['mode'] == 'replace_threshold':
            skip = index == 6
        else:
            raise AssertionError(
                'unknown aereo-05 semantic fixture mode ' +
                repr(case['mode']))
        if not skip:
            parts.append(sentence(alternatives[0]))
    parts.append(case['text'])
    return ' '.join(parts)


def page(intent, visible=None, sources=None):
    return {
        'intent_id': intent,
        'opening': (current_visible(intent) if visible is None else visible),
        'official_sources': (
            current_sources(intent) if sources is None else sources),
    }


def reasons(record, evaluation_date=CURRENT):
    return auditor.current_legal_fact_reasons(
        record, evaluation_date=evaluation_date)


def source_reason(intent, kind):
    for candidate, code in auditor.AEREO05_SOURCE_REQUIREMENTS[intent]:
        if candidate == kind:
            return 'current_legal_fact_source_missing:' + code
    raise AssertionError((intent, kind))


def exact_url_decoys(raw_url):
    parsed = urllib.parse.urlsplit(raw_url)
    path = parsed.path[:-1] if parsed.path.endswith('/') else parsed.path + '/'
    query = parsed.query + ('&' if parsed.query else '') + 'decoy=1'
    variants = (
        urllib.parse.urlunsplit(parsed._replace(fragment='decoy')),
        urllib.parse.urlunsplit(parsed._replace(path=path)),
        urllib.parse.urlunsplit(parsed._replace(scheme='http')),
        urllib.parse.urlunsplit(parsed._replace(netloc=parsed.netloc.upper())),
        urllib.parse.urlunsplit(
            parsed._replace(netloc=parsed.netloc + ':443')),
        urllib.parse.urlunsplit(
            parsed._replace(netloc='legacy@' + parsed.netloc)),
        urllib.parse.urlunsplit(
            parsed._replace(path='//' + parsed.path.lstrip('/'))),
        urllib.parse.urlunsplit(parsed._replace(query=query)),
        ' ' + raw_url,
        raw_url + ' ',
    )
    return tuple(dict.fromkeys(variants))


class Aereo05CurrentLawGateTest(unittest.TestCase):

    def test_inventory_and_order_cover_the_literal_go_contract(self):
        expected_order = (
            'aer-no-show-ida-cancelamento-volta',
            'aer-arrependimento-24-horas-compra',
            'aer-cancelar-passagem-multa-limites',
            'aer-remarcacao-taxa-diferenca-tarifaria',
            'aer-perdi-o-voo-no-show-direitos',
            'aer-nome-errado-passagem-correcao',
            'aer-transferir-passagem-outra-pessoa',
            'aer-doenca-remarcacao-sem-multa',
            'aer-cobranca-escolha-assento-legalidade',
            'aer-perdi-voo-fila-companhia-culpa',
            'aer-preco-mudou-finalizar-compra',
        )
        self.assertEqual(expected_order, auditor.AEREO05_INTENT_ORDER)
        self.assertEqual(11, len(auditor.AEREO05_INTENTS))
        self.assertEqual(
            auditor.AEREO05_INTENTS,
            frozenset(auditor.AEREO05_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO05_INTENTS,
            frozenset(auditor.AEREO05_OUTCOME_RULES))
        self.assertEqual(
            30, sum(len(items) for items in
                    auditor.AEREO05_SOURCE_REQUIREMENTS.values()))
        self.assertEqual(30, len(auditor.AEREO05_SOURCE_ANCHOR_RULES))
        self.assertEqual(8, len(auditor.AEREO05_SOURCE_URLS))
        self.assertEqual(16, len(auditor.AEREO05_STALE_RULES))
        self.assertEqual(
            {code for code, _ in auditor.AEREO05_STALE_RULES},
            set(auditor.AEREO05_STALE_RULE_INTENTS))
        for intent, (_, groups) in auditor.AEREO05_OUTCOME_RULES.items():
            signatures = [tuple(auditor.norm_key(item) for item in group)
                          for group in groups]
            with self.subTest(intent=intent):
                self.assertEqual(len(signatures), len(set(signatures)))

    def test_active_contract_matches_the_independent_go_digest(self):
        self.assertEqual(AEREO05_GO_CONTRACT_SHA256, contract_digest())

    def test_all_eight_source_urls_are_literal(self):
        expected = {
            'res400': 'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/resolucoes/resolucoes-2016/resolucao-no-400-13-12-2016',
            'cdc': 'https://www2.camara.leg.br/legin/fed/lei/1990/lei-8078-11-setembro-1990-365086-normaatualizada-pl.html',
            'stj_no_show': 'https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisarumaedicao&livre=%270018E%27.cod.',
            'stj_resp_1913986': 'https://www.stj.jus.br/sites/portalp/paginas/comunicacao/noticias/2025/18112025-passagem-aerea-pela-internet-relator-da-sete-dias-para-desistencia-com-devolucao-do-dinheiro.aspx',
            'res280': 'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/resolucoes/resolucoes-2013/resolucao-no-280-de-11-07-2013',
            'stj_damage': 'https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=%40CNOT%3D020857',
            'portaria_13065': 'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/portarias/2023/portaria-13065',
            'stj_price': 'https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Erro-grosseiro-de-sistema-nao-obriga-empresas-a-emitir-passagens-compradas-a-preco-muito-baixo.aspx',
        }
        self.assertEqual(expected, auditor.AEREO05_SOURCE_URLS)

    def test_synthetic_fixtures_pass_without_provenance_runtime_fields(self):
        for intent in auditor.AEREO05_INTENT_ORDER:
            record = page(intent)
            for source in record['official_sources']:
                self.assertNotIn('verified_at', source)
                self.assertNotIn('http_status', source)
            with self.subTest(intent=intent):
                self.assertEqual([], reasons(record))

    def test_article12_shared_semantic_matrix(self):
        outcome_code, _ = auditor.AEREO05_OUTCOME_RULES[ARTICLE12_INTENT]
        outcome_reason = 'current_legal_fact_outcome_missing:' + outcome_code
        stale_prefix = (
            'current_legal_fact_stale_assertion:'
            'aereo05_carrier_schedule_change_')
        for case in article12_semantic_cases():
            got_reasons = reasons(page(
                ARTICLE12_INTENT, visible=article12_case_visible(case)))
            got_stale = sorted(
                reason.removeprefix(
                    'current_legal_fact_stale_assertion:')
                for reason in got_reasons
                if reason.startswith(stale_prefix))
            with self.subTest(case=case['name']):
                self.assertEqual(
                    case['outcome_missing'], outcome_reason in got_reasons,
                    got_reasons)
                self.assertEqual(
                    sorted(case['stale_codes']), got_stale, got_reasons)

    def test_real_shard_order_and_current_law_reasons_are_green(self):
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/aereo-05.jsonl')
        records = [
            json.loads(line) for line in shard.read_text(
                encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(
            list(auditor.AEREO05_INTENT_ORDER),
            [record['intent_id'] for record in records])
        for record in records:
            visible = '\n'.join(auditor.visible_parts(record))
            direct = auditor.current_aereo05_legal_fact_reasons(
                record, record['intent_id'], visible, CURRENT)
            with self.subTest(intent=record['intent_id']):
                self.assertEqual([], direct)
                self.assertEqual([], reasons(record))

    def test_removing_each_of_the_30_sources_is_detected(self):
        count = 0
        for intent in auditor.AEREO05_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO05_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                del sources[index]
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        source_reason(intent, kind),
                        reasons(page(intent, sources=sources)))
        self.assertEqual(30, count)

    def test_every_exact_source_rejects_decoys(self):
        count = 0
        for intent in auditor.AEREO05_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO05_SOURCE_REQUIREMENTS[intent]):
                wanted = auditor.AEREO05_SOURCE_URLS[kind]
                for decoy in exact_url_decoys(wanted):
                    count += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            source_reason(intent, kind),
                            reasons(page(intent, sources=sources)))
        self.assertEqual(300, count)

    def test_all_30_material_anchors_reject_generic_metadata(self):
        count = 0
        for intent in auditor.AEREO05_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO05_SOURCE_REQUIREMENTS[intent]):
                count += 1
                code, _ = anchor_rule(intent, kind)
                sources = current_sources(intent)
                sources[index]['name'] = 'Fonte oficial sem escopo material'
                sources[index]['anchor_claim'] = 'Documento oficial.'
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' + code,
                        reasons(page(intent, sources=sources)))
        self.assertEqual(30, count)

    def test_every_material_anchor_group_rejects_negation(self):
        count = 0
        for intent in auditor.AEREO05_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO05_SOURCE_REQUIREMENTS[intent]):
                code, groups = anchor_rule(intent, kind)
                for negated_group in range(len(groups)):
                    count += 1
                    claims = []
                    for group_index, alternatives in enumerate(groups):
                        claim = alternatives[0]
                        if group_index == negated_group:
                            claim = 'A fonte não afirma que ' + claim
                        claims.append(sentence(claim))
                    sources = current_sources(intent)
                    sources[index]['anchor_claim'] = ' '.join(claims)
                    with self.subTest(
                            intent=intent, kind=kind,
                            group=negated_group):
                        self.assertIn(
                            'current_legal_fact_source_anchor_missing:' + code,
                            reasons(page(intent, sources=sources)))
        self.assertGreater(count, 90)

    def test_materially_misleading_anchors_do_not_pass_by_keywords(self):
        cases = (
            (
                'aer-arrependimento-24-horas-compra',
                'stj_resp_1913986',
                'Registra voto do relator contra a aplicação do art. 49, '
                'pedido de vista e julgamento suspenso.',
                'stj_resp_1913986_relator_vote_and_view_request_pending_scope',
            ),
            (
                'aer-doenca-remarcacao-sem-multa',
                'stj_damage',
                'Afirma que atraso ou cancelamento de voo sempre gera dano '
                'moral, conforme as circunstâncias.',
                'stj_agint_aresp_2150150_no_presumed_moral_damage_scope',
            ),
            (
                'aer-preco-mudou-finalizar-compra',
                'stj_price',
                'Caso específico de erro sistêmico grosseiro, com e-ticket '
                'e cobrança, comunicado rapidamente.',
                'stj_resp_1794991_gross_error_no_eticket_no_charge_prompt_notice_scope',
            ),
            (
                'aer-perdi-o-voo-no-show-direitos',
                'res400',
                'Disciplina no-show, apresentação para embarque, reembolso, '
                'preservação da volta e preterição como situações equivalentes.',
                'anac_resolution_400_no_show_presentation_refund_return_and_preterition_scope',
            ),
        )
        for intent, kind, claim, code in cases:
            sources = current_sources(intent)
            index = [
                candidate for candidate, _ in
                auditor.AEREO05_SOURCE_REQUIREMENTS[intent]].index(kind)
            sources[index]['anchor_claim'] = claim
            with self.subTest(intent=intent, kind=kind):
                self.assertIn(
                    'current_legal_fact_source_anchor_missing:' + code,
                    reasons(page(intent, sources=sources)))

    def test_each_outcome_group_is_individually_required(self):
        omissions = 0
        for intent, (code, groups) in auditor.AEREO05_OUTCOME_RULES.items():
            texts = [sentence(group[0]) for group in groups]
            for omitted in range(len(groups)):
                omissions += 1
                visible = ' '.join(
                    texts[:omitted] + texts[omitted + 1:])
                with self.subTest(intent=intent, group=omitted):
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        reasons(page(intent, visible=visible)))
        self.assertEqual(84, omissions)

    def test_critical_contradiction_for_every_intent_is_blocked(self):
        cases = (
            ('aer-no-show-ida-cancelamento-volta', 'A companhia pode cancelar a volta doméstica mesmo avisada até o horário original da ida.', 'aereo05_article_19_return_cancelled_despite_timely_domestic_notice'),
            ('aer-arrependimento-24-horas-compra', 'O REsp 1.913.986 já fixou tese definitiva.', 'aereo05_online_withdrawal_24h_or_seven_days_absolute'),
            ('aer-cancelar-passagem-multa-limites', 'Toda multa de passagem está limitada a 5%.', 'aereo05_five_percent_universal_or_wrong_base'),
            ('aer-remarcacao-taxa-diferenca-tarifaria', 'Se o novo voo for mais barato, a companhia fica com a diferença.', 'aereo05_fare_difference_only_positive_or_hidden'),
            ('aer-perdi-o-voo-no-show-direitos', 'O mero no-show garante 250 DES no voo doméstico.', 'aereo05_no_show_gets_preterition_des_or_assistance'),
            ('aer-nome-errado-passagem-correcao', 'A correção de nome permite trocar o passageiro.', 'aereo05_name_correction_changes_passenger_or_cost_rule'),
            ('aer-transferir-passagem-outra-pessoa', 'A passagem pode ser livremente transferida para outra pessoa.', 'aereo05_ticket_transfer_or_credit_compulsion'),
            ('aer-doenca-remarcacao-sem-multa', 'Qualquer atestado elimina automaticamente a multa.', 'aereo05_illness_automatic_waiver_or_medif_confusion'),
            ('aer-cobranca-escolha-assento-legalidade', 'Menor de 16 anos deve pagar para ficar adjacente ao responsável.', 'aereo05_seat_optional_minor_or_pnae_wrong_rule'),
            ('aer-perdi-voo-fila-companhia-culpa', 'A compensação é de 250 reais no voo doméstico.', 'aereo05_queue_automatic_preterition_or_wrong_des'),
            ('aer-preco-mudou-finalizar-compra', 'Erro de sistema sempre permite cancelar mesmo com e-ticket e cobrança.', 'aereo05_dynamic_price_cancels_precise_offer_or_gross_error_absolute'),
        )
        for intent, false_fact, code in cases:
            record = page(
                intent, visible=current_visible(intent) + ' ' + false_fact)
            with self.subTest(intent=intent):
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    reasons(record))

    def test_every_stale_alternative_is_enforced_only_in_its_scope(self):
        all_intents = set(auditor.AEREO05_INTENTS)
        for code, alternatives in auditor.AEREO05_STALE_RULES:
            scope = auditor.AEREO05_STALE_RULE_INTENTS.get(
                code, frozenset(all_intents))
            for alternative in alternatives:
                for intent in scope:
                    record = page(
                        intent,
                        visible=(current_visible(intent) + ' ' +
                                 sentence(alternative)))
                    with self.subTest(code=code, intent=intent):
                        self.assertIn(
                            'current_legal_fact_stale_assertion:' + code,
                            reasons(record))
                outside = all_intents - set(scope)
                if outside:
                    intent = sorted(outside)[0]
                    record = page(
                        intent,
                        visible=(current_visible(intent) + ' ' +
                                 sentence(alternative)))
                    self.assertNotIn(
                        'current_legal_fact_stale_assertion:' + code,
                        reasons(record))

    def test_revoked_cef_8018_source_obeys_the_exact_cutoff(self):
        intent = 'aer-cancelar-passagem-multa-limites'
        stale = {
            'url': ('https://www.anac.gov.br/assuntos/legislacao/'
                    'legislacao-1/portarias/2022/portaria-8018'),
            'name': 'Portaria histórica',
            'anchor_claim': 'CEF histórico.',
        }
        record = page(intent)
        record['official_sources'].append(stale)
        code = ('current_legal_fact_source_stale:'
                'anac_portaria_8018_cef_revoked_2026_04_28')
        self.assertNotIn(code, reasons(record, PRE_CEF_REVOCATION))
        self.assertIn(code, reasons(record, CEF_REVOCATION))
        self.assertIn(code, reasons(record, CURRENT))

        encoded = copy.deepcopy(record)
        encoded['official_sources'][-1]['url'] = (
            'https://www.anac.gov.br/x/CEF-RESOLUCAO-NO-400')
        self.assertIn(code, reasons(encoded, CURRENT))

    def test_revoked_cef_current_assertion_is_blocked(self):
        intent = 'aer-cancelar-passagem-multa-limites'
        record = page(
            intent, visible=(current_visible(intent) +
                             ' A Portaria 8.018 de 2022 está vigente.'))
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'aereo05_cef_8018_revoked_treated_as_current',
            reasons(record))

    def test_natural_negations_and_historical_framing_are_safe(self):
        cases = (
            ('aer-arrependimento-24-horas-compra',
             'O REsp 1.913.986 não fixou tese definitiva.'),
            ('aer-perdi-o-voo-no-show-direitos',
             'O mero no-show não garante 250 DES no voo doméstico.'),
            ('aer-cancelar-passagem-multa-limites',
             'A regra revogada dizia que a Portaria 8.018 de 2022 estava vigente.'),
            ('aer-preco-mudou-finalizar-compra',
             'É falso que todo preço baixo seja erro grosseiro.'),
        )
        for intent, safe_fact in cases:
            record = page(
                intent,
                visible=current_visible(intent) + ' ' + safe_fact)
            with self.subTest(intent=intent, safe_fact=safe_fact):
                self.assertFalse(any(
                    reason.startswith('current_legal_fact_stale_assertion:')
                    for reason in reasons(record)))

    def test_minor_adjacent_anchor_rejects_all_go_nonaffirming_forms(self):
        intent = 'aer-cobranca-escolha-assento-legalidade'
        kind = 'portaria_13065'
        index = [
            candidate for candidate, _ in
            auditor.AEREO05_SOURCE_REQUIREMENTS[intent]].index(kind)
        code, groups = anchor_rule(intent, kind)
        suffix = ' '.join(
            sentence(alternatives[0]) for alternatives in groups[1:])
        prefixes = (
            'Não assegura assento adjacente para menor de 16 anos.',
            'Não afirma que assegura assento adjacente para menor de 16 anos.',
            'É falso que assegura assento adjacente para menor de 16 anos.',
            'Seria incorreto afirmar que assegura assento adjacente para menor de 16 anos.',
        )
        for prefix in prefixes:
            sources = current_sources(intent)
            sources[index]['anchor_claim'] = prefix + ' ' + suffix
            with self.subTest(prefix=prefix):
                self.assertIn(
                    'current_legal_fact_source_anchor_missing:' + code,
                    reasons(page(intent, sources=sources)))

    def test_unknown_intent_does_not_enter_the_aereo05_gate(self):
        self.assertEqual([], auditor.current_aereo05_legal_fact_reasons(
            {}, 'aer-outro-shard', 'Fato qualquer.', CURRENT))


if __name__ == '__main__':
    unittest.main()
