#!/usr/bin/env python3
"""Focused adversarial regressions for the aereo-04 baggage gate."""

import copy
import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 12)
PRE_MONTREAL = datetime.date(2024, 12, 27)
MONTREAL_CUTOFF = datetime.date(2024, 12, 28)
PRE_RBAC11 = datetime.date(2027, 2, 22)
RBAC11_CUTOFF = datetime.date(2027, 2, 23)

# Frozen from the literal Go contract in
# internal/v2ingest/current_legal_facts_aereo04.go.  The digest deliberately
# does not derive an expectation from the Python maps under test: it binds all
# source identities/requirements, anchor codes/groups, outcome codes/groups,
# stale rules/scopes and temporal matrices in one independent fixture.
AEREO04_GO_CONTRACT_SHA256 = (
    'fcff7837a9ff503324e4776be6773f7b9488797989e9b32b2896d2325b2d1b56')


def aereo04_contract_snapshot():
    return {
        'source_urls': sorted(auditor.AEREO04_SOURCE_URLS.items()),
        'source_requirements': sorted(
            auditor.AEREO04_SOURCE_REQUIREMENTS.items()),
        'general_anchors': sorted(
            auditor.AEREO04_GENERAL_SOURCE_ANCHOR_RULES.items()),
        'specific_anchors': sorted(
            (intent, kind, rule)
            for (intent, kind), rule in
            auditor.AEREO04_INTENT_SOURCE_ANCHOR_RULES.items()),
        'outcomes': sorted(auditor.AEREO04_OUTCOME_RULES.items()),
        'stale_rules': auditor.AEREO04_STALE_RULES,
        'stale_scopes': sorted(
            (code, sorted(scope))
            for code, scope in auditor.AEREO04_STALE_RULE_INTENTS.items()),
        'pre_montreal_outcomes': sorted(
            auditor.AEREO04_PRE_MONTREAL_2024_OUTCOME_RULES.items()),
        'post_montreal_outcomes': sorted(
            auditor.AEREO04_POST_MONTREAL_2024_OUTCOME_RULES.items()),
        'pre_rbac_sources': sorted(
            auditor.AEREO04_PRE_RBAC107_SOURCE_REQUIREMENTS.items()),
        'post_rbac_sources': sorted(
            auditor.AEREO04_POST_RBAC107_SOURCE_REQUIREMENTS.items()),
        'pre_rbac_outcomes': sorted(
            auditor.AEREO04_PRE_RBAC107_OUTCOME_RULES.items()),
        'post_rbac_outcomes': sorted(
            auditor.AEREO04_POST_RBAC107_OUTCOME_RULES.items()),
        'pre_montreal_stale':
            auditor.AEREO04_PRE_MONTREAL_2024_STALE_RULES,
        'post_montreal_stale':
            auditor.AEREO04_POST_MONTREAL_2024_STALE_RULES,
        'pre_rbac_stale': auditor.AEREO04_PRE_RBAC107_STALE_RULES,
        'post_rbac_stale': auditor.AEREO04_POST_RBAC107_STALE_RULES,
    }


def aereo04_contract_digest():
    payload = json.dumps(
        aereo04_contract_snapshot(), sort_keys=True,
        separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def source_fixture(intent, kind):
    fixture = {
        'url': auditor.AEREO04_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': 'Escopo oficial específico.',
    }
    rule = auditor.AEREO04_SOURCE_ANCHOR_RULES.get((intent, kind))
    if rule is None:
        rule = auditor.AEREO04_GENERAL_SOURCE_ANCHOR_RULES.get(kind)
    if rule:
        fixture['anchor_claim'] = ' '.join(
            sentence(alternatives[0]) for alternatives in rule[1])
    return fixture


def current_sources(intent, evaluation_date=CURRENT):
    seen = set()
    result = []
    for kind, _ in auditor.aereo04_source_requirements_as_of(
            intent, evaluation_date):
        fixture = source_fixture(intent, kind)
        if fixture['url'] in seen:
            continue
        seen.add(fixture['url'])
        result.append(fixture)
    return result


def current_visible(intent, evaluation_date=CURRENT):
    return ' '.join(
        sentence(alternatives[0])
        for _, groups in auditor.aereo04_outcome_rules_as_of(
            intent, evaluation_date)
        for alternatives in groups)


def page(intent, visible=None, sources=None, evaluation_date=CURRENT):
    return {
        'intent_id': intent,
        'opening': (current_visible(intent, evaluation_date)
                    if visible is None else visible),
        'official_sources': (current_sources(intent, evaluation_date)
                             if sources is None else sources),
    }


def reasons(record, evaluation_date=CURRENT):
    return auditor.current_legal_fact_reasons(
        record, evaluation_date=evaluation_date)


def source_reason(intent, kind, evaluation_date=CURRENT):
    for candidate, code in auditor.aereo04_source_requirements_as_of(
            intent, evaluation_date):
        if candidate == kind:
            return 'current_legal_fact_source_missing:' + code
    raise AssertionError((intent, kind, evaluation_date))


def exact_url_decoys(raw_url):
    parsed = urllib.parse.urlsplit(raw_url)
    variants = [urllib.parse.urlunsplit(parsed._replace(fragment='decoy'))]
    path = parsed.path[:-1] if parsed.path.endswith('/') else parsed.path + '/'
    variants.append(urllib.parse.urlunsplit(parsed._replace(path=path)))
    variants.append(urllib.parse.urlunsplit(parsed._replace(scheme='http')))
    variants.append(urllib.parse.urlunsplit(
        parsed._replace(netloc=parsed.netloc.upper())))
    variants.append(urllib.parse.urlunsplit(
        parsed._replace(netloc=parsed.netloc + ':443')))
    variants.append(urllib.parse.urlunsplit(
        parsed._replace(netloc='legacy@' + parsed.netloc)))
    variants.append(urllib.parse.urlunsplit(
        parsed._replace(path='//' + parsed.path.lstrip('/'))))
    query = parsed.query + ('&' if parsed.query else '') + 'decoy=1'
    variants.append(urllib.parse.urlunsplit(parsed._replace(query=query)))
    return tuple(dict.fromkeys(variants))


class Aereo04CurrentLawGateTest(unittest.TestCase):

    def test_inventory_covers_the_19_portfolio_intents(self):
        self.assertEqual(19, len(auditor.AEREO04_INTENT_ORDER))
        self.assertEqual(19, len(auditor.AEREO04_INTENTS))
        self.assertEqual(
            auditor.AEREO04_INTENTS,
            frozenset(auditor.AEREO04_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO04_INTENTS,
            frozenset(auditor.AEREO04_OUTCOME_RULES))
        self.assertEqual(
            {code for code, _ in auditor.AEREO04_STALE_RULES},
            set(auditor.AEREO04_STALE_RULE_INTENTS))
        self.assertEqual(
            frozenset(auditor.AEREO04_PRE_MONTREAL_2024_OUTCOME_RULES),
            frozenset(auditor.AEREO04_POST_MONTREAL_2024_OUTCOME_RULES))
        self.assertEqual(
            frozenset(auditor.AEREO04_PRE_RBAC107_OUTCOME_RULES),
            frozenset(auditor.AEREO04_POST_RBAC107_OUTCOME_RULES))

    def test_active_contract_matches_the_explicit_go_fixture(self):
        self.assertEqual(AEREO04_GO_CONTRACT_SHA256,
                         aereo04_contract_digest())

    def test_canonical_swapped_and_temporal_urls_are_frozen(self):
        self.assertEqual(
            'https://www.icao.int/sites/default/files/secretariat/legal/'
            'LEB%20Treaty%20Collection%20Documents/'
            '2024_Revised_Limits_of_Liability_Under_the_Montreal_'
            'Convention_of_1999_en.pdf',
            auditor.AEREO04_ICAO_2024_LIMITS_URL)
        self.assertEqual(
            'https://noticias.stf.jus.br/postsnoticias/'
            'transporte-aereo-deve-seguir-convencoes-internacionais-'
            'sobre-extravio-de-bagagens/',
            auditor.AEREO04_STF_TEMA210_URL)
        self.assertEqual(
            'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/'
            'boletim-de-pessoal/2025/bps-v-20-no-5-03-a-07-02-2025/'
            'rbac-108-emd-08/visualizar_ato_normativo',
            auditor.AEREO04_RBAC108_EMD08_URL)
        self.assertEqual(
            'https://voos.infraero.gov.br/images/stories/Arquivos/'
            'carta_infraero.pdf',
            auditor.AEREO04_INFRAERO_LOST_URL)
        self.assertEqual(
            'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/'
            'boletim-de-pessoal/2026/bps-v-21-no-14-06-a-10-04-2026/'
            'is-175-001m/%40%40display-file/bps_arquivo_ato_normativo/'
            'IS%20175-001M.pdf',
            auditor.AEREO04_POWER_BANK_2026_URL)
        self.assertIn(
            '/2025/bps-v-20-no-5-03-a-07-02-2025/rbac-107-emd-10/'
            'visualizar_ato_normativo',
            auditor.AEREO04_RBAC107_EMD10_URL)
        self.assertIn(
            '/2026/bps-v-21-no-8-23-a-27-02-2026/rbac-107-emd-11/'
            'visualizar_ato_normativo',
            auditor.AEREO04_RBAC107_EMD11_URL)

    def test_accepts_current_fixture_for_every_intent(self):
        for intent in auditor.AEREO04_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual([], reasons(page(intent), CURRENT))

    def test_rib_does_not_guarantee_indemnity_even_beside_valid_text(self):
        intent = 'aer-bagagem-nao-apareceu-esteira-rib'
        visible = (
            current_visible(intent) +
            ' O RIB garante a indenização.')
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'aereo_baggage_rib_guarantee_or_delayed_protest',
            reasons(page(intent, visible=visible)))

    def test_go_stf_and_infraero_anchor_alternatives_are_accepted(self):
        cases = (
            (
                'aer-bagagem-extravio-definitivo-indenizacao',
                'stf_tema_210',
                'Transporte aéreo internacional. Dano material. '
                'Convenção de Montreal prevalece.',
            ),
            (
                'aer-objeto-esquecido-aviao-achados-perdidos',
                'infraero_achados',
                'Achados e perdidos. Sob operação da Infraero.',
            ),
        )
        for intent, kind, anchor_claim in cases:
            sources = current_sources(intent)
            wanted = auditor.AEREO04_SOURCE_URLS[kind]
            target = next(item for item in sources if item['url'] == wanted)
            target['anchor_claim'] = anchor_claim
            with self.subTest(intent=intent, kind=kind):
                self.assertEqual([], reasons(page(intent, sources=sources)))

    def test_exact_1519_claim_always_requires_specific_icao_evidence(self):
        intent = 'aer-bagagem-conexao-cias-diferentes-quem-responde'
        visible = (
            current_visible(intent) +
            ' O teto material atual da bagagem internacional é de '
            '1.519 DES por passageiro.')
        record = page(intent, visible=visible)
        missing = (
            'current_legal_fact_source_missing:'
            'icao_montreal_2024_exact_1519_claim')
        self.assertIn(missing, reasons(record))

        record['official_sources'].append(source_fixture(intent, 'icao_2024'))
        self.assertNotIn(missing, reasons(record))
        self.assertFalse(any(
            reason.startswith('current_legal_fact_source_anchor_missing:')
            for reason in reasons(record)))

        record['official_sources'][-1]['anchor_claim'] = (
            'Documento internacional sem o limite material.')
        self.assertIn(
            'current_legal_fact_source_anchor_missing:'
            'icao_montreal_2024_article_22_2_1519_effective_date',
            reasons(record))

    def test_cba_icao_anchor_binds_baggage_and_cargo_limits(self):
        code, groups = auditor.AEREO04_SOURCE_ANCHOR_RULES[
            ('aer-indenizacao-por-peso-cba-ou-cdc', 'icao_2024')]
        self.assertEqual(
            'icao_montreal_2024_baggage_and_cargo_limits_scope', code)
        self.assertEqual(5, len(groups))
        self.assertIn('artigo 22 paragrafo 3', groups[2])
        self.assertIn('26 des por quilograma de carga', groups[3])

    def test_real_shard_has_zero_current_law_reasons(self):
        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/aereo-04.jsonl')
        records = [
            json.loads(line) for line in shard.read_text(
                encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(19, len(records))
        for record in records:
            visible = '\n'.join(auditor.visible_parts(record))
            with self.subTest(intent=record['intent_id']):
                self.assertEqual([], auditor.current_aereo04_legal_fact_reasons(
                    record, record['intent_id'], visible, CURRENT))

    def test_visible_block_boundary_stops_negation_bleed(self):
        intent = 'aer-bagagem-extravio-temporario-dano-moral'
        record = page(intent)
        record['h1'] = 'O tempo sozinho não decide'
        self.assertEqual([], reasons(record, CURRENT))

    def test_semantic_clause_boundaries_stop_meta_negation_bleed(self):
        cases = {
            'editorial block': (
                'É falso que o contrato seja gratuito\n'
                'A morte dispensa comunicação ao locador.'),
            'coordinated clause': (
                'É falso que o contrato seja gratuito, e a morte '
                'dispensa comunicação ao locador.'),
        }
        expected = [
            'e falso que o contrato seja gratuito',
            'a morte dispensa comunicacao ao locador',
        ]
        for label, visible in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    expected, auditor.semantic_legal_fact_clauses(visible))

    def test_accepts_post_rbac11_fixture_for_every_intent(self):
        for intent in auditor.AEREO04_INTENT_ORDER:
            with self.subTest(intent=intent):
                self.assertEqual(
                    [], reasons(page(
                        intent, evaluation_date=RBAC11_CUTOFF),
                        RBAC11_CUTOFF))

    def test_requires_every_specific_source(self):
        for evaluation_date in (CURRENT, RBAC11_CUTOFF):
            for intent in auditor.AEREO04_INTENT_ORDER:
                for kind, code in auditor.aereo04_source_requirements_as_of(
                        intent, evaluation_date):
                    with self.subTest(
                            intent=intent, kind=kind, date=evaluation_date):
                        wanted = auditor.AEREO04_SOURCE_URLS[kind]
                        kept = [
                            item for item in current_sources(
                                intent, evaluation_date)
                            if item['url'] != wanted
                        ]
                        self.assertIn(
                            'current_legal_fact_source_missing:' + code,
                            reasons(page(
                                intent, sources=kept,
                                evaluation_date=evaluation_date),
                                evaluation_date))

    def test_every_exact_source_rejects_full_decoy_matrix(self):
        seen = set()
        for evaluation_date in (CURRENT, RBAC11_CUTOFF):
            for intent in auditor.AEREO04_INTENT_ORDER:
                for kind, _ in auditor.aereo04_source_requirements_as_of(
                        intent, evaluation_date):
                    key = (intent, kind, evaluation_date)
                    if key in seen:
                        continue
                    seen.add(key)
                    wanted = auditor.AEREO04_SOURCE_URLS[kind]
                    for decoy in exact_url_decoys(wanted):
                        with self.subTest(
                                intent=intent, kind=kind, decoy=decoy):
                            kept = [
                                item for item in current_sources(
                                    intent, evaluation_date)
                                if item['url'] != wanted
                            ]
                            mutated = source_fixture(intent, kind)
                            mutated['url'] = decoy
                            kept.append(mutated)
                            self.assertIn(
                                source_reason(intent, kind, evaluation_date),
                                reasons(page(
                                    intent, sources=kept,
                                    evaluation_date=evaluation_date),
                                    evaluation_date))

    def test_every_anchor_rejects_generic_metadata(self):
        for (intent, kind), (code, _) in (
                auditor.AEREO04_SOURCE_ANCHOR_RULES.items()):
            evaluation_date = (
                RBAC11_CUTOFF if kind == 'rbac_107_emd11' else CURRENT)
            sources = current_sources(intent, evaluation_date)
            wanted = auditor.AEREO04_SOURCE_URLS[kind]
            target = next(item for item in sources if item['url'] == wanted)
            target['name'] = 'Fonte oficial sem escopo material'
            target['anchor_claim'] = 'Documento oficial.'
            with self.subTest(intent=intent, kind=kind):
                self.assertIn(
                    'current_legal_fact_source_anchor_missing:' + code,
                    reasons(page(
                        intent, sources=sources,
                        evaluation_date=evaluation_date), evaluation_date))

    def test_critical_anchors_reject_questions_negation_and_history(self):
        cases = (
            ('aer-bagagem-limite-indenizacao-internacional', 'icao_2024'),
            ('aer-bagagem-declaracao-especial-valor', 'res400'),
            ('aer-bagagem-danificada-avaria', 'res400'),
            ('aer-indenizacao-por-peso-cba-ou-cdc', 'cba'),
            ('aer-furto-inspecao-raio-x-aeroporto', 'rbac_107_emd10'),
        )
        for intent, kind in cases:
            code, groups = auditor.AEREO04_SOURCE_ANCHOR_RULES[
                (intent, kind)]
            for mode in ('question', 'negated', 'historical'):
                sources = current_sources(intent)
                target = next(
                    item for item in sources
                    if item['url'] == auditor.AEREO04_SOURCE_URLS[kind])
                claims = []
                for alternatives in groups:
                    claim = sentence(alternatives[0])
                    if mode == 'question':
                        claim = claim[:-1] + '?'
                    elif mode == 'negated':
                        claim = 'Não ' + claim[:1].lower() + claim[1:]
                    else:
                        claim = 'A regra antiga dizia: ' + claim.lower()
                    claims.append(claim)
                target['anchor_claim'] = ' '.join(claims)
                with self.subTest(intent=intent, kind=kind, mode=mode):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' + code,
                        reasons(page(intent, sources=sources)))

    def test_requires_each_base_outcome_group(self):
        for intent, (code, groups) in auditor.AEREO04_OUTCOME_RULES.items():
            temporal = [
                sentence(group[0])
                for temporal_code, temporal_groups in
                auditor.aereo04_outcome_rules_as_of(intent, CURRENT)[1:]
                for group in temporal_groups
            ]
            base = [sentence(group[0]) for group in groups]
            for index in range(len(groups)):
                with self.subTest(intent=intent, group=index):
                    visible = ' '.join(
                        base[:index] + base[index + 1:] + temporal)
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        reasons(page(intent, visible=visible)))

    def test_requires_each_temporal_outcome_group(self):
        for evaluation_date in (
                PRE_MONTREAL, MONTREAL_CUTOFF,
                PRE_RBAC11, RBAC11_CUTOFF):
            for intent in auditor.AEREO04_INTENT_ORDER:
                rules = auditor.aereo04_outcome_rules_as_of(
                    intent, evaluation_date)
                for code, groups in rules[1:]:
                    all_sentences = [
                        (current_code, index, sentence(group[0]))
                        for current_code, current_groups in rules
                        for index, group in enumerate(current_groups)
                    ]
                    matching = [
                        item for item in all_sentences if item[0] == code]
                    for current_code, index, _ in matching:
                        visible = ' '.join(
                            text for candidate_code, candidate_index, text in
                            all_sentences
                            if not (candidate_code == current_code and
                                    candidate_index == index))
                        with self.subTest(
                                intent=intent, code=code, group=index,
                                date=evaluation_date):
                            self.assertIn(
                                'current_legal_fact_outcome_missing:' + code,
                                reasons(page(
                                    intent, visible=visible,
                                    evaluation_date=evaluation_date),
                                    evaluation_date))

    def test_every_stale_alternative_is_scoped_and_negation_safe(self):
        all_intents = set(auditor.AEREO04_INTENTS)
        for code, alternatives in auditor.AEREO04_STALE_RULES:
            scope = auditor.AEREO04_STALE_RULE_INTENTS[code]
            intent = next(iter(scope))
            out_of_scope = next(iter(all_intents - set(scope)))
            wanted = 'current_legal_fact_stale_assertion:' + code
            for alternative in alternatives:
                stale = current_visible(intent) + ' ' + sentence(alternative)
                corrective = (
                    current_visible(intent) + ' É falso que ' +
                    alternative + '.')
                unrelated = (
                    current_visible(out_of_scope) + ' ' +
                    sentence(alternative))
                with self.subTest(code=code, alternative=alternative):
                    self.assertIn(wanted, reasons(page(intent, visible=stale)))
                    self.assertNotIn(
                        wanted, reasons(page(intent, visible=corrective)))
                    self.assertNotIn(
                        wanted,
                        reasons(page(out_of_scope, visible=unrelated)))

    def test_rejects_stale_source_families(self):
        intent = 'aer-bagagem-nao-apareceu-esteira-rib'
        cases = (
            ('https://www.anac.gov.br/legislacao/'
             'cef-resolucao-no-400-de-2016.pdf',
             'anac_resolution_400_historical_cef', CURRENT),
            ('https://www.anac.gov.br/legislacao/'
             'anexo-iii-cef-resolucao-no-400.pdf',
             'anac_resolution_400_historical_cef', CURRENT),
            (auditor.AEREO04_OLD_BAGGAGE_GUIDE_URL,
             'anac_historical_baggage_guide_not_current_rule', CURRENT),
            (auditor.AEREO04_OLD_BAGGAGE_PAMPHLET_URL,
             'anac_historical_baggage_guide_not_current_rule', CURRENT),
            ('https://www.gov.br/anac/pt-br/publicacoes/'
             'copy_of_anac-passageiro.pdf',
             'anac_obsolete_passenger_copy_endpoint', CURRENT),
            ('https://www.icao.int/legal/2019_Revised_Limits.pdf',
             'icao_montreal_2019_limit_not_current_after_2024_12_28',
             CURRENT),
            ('https://www.anac.gov.br/legislacao/rbac-107-emd-09',
             'anac_rbac_107_superseded_emendment', CURRENT),
            (auditor.AEREO04_RBAC107_EMD11_URL,
             'anac_rbac_107_emd11_premature_before_2027_02_23', CURRENT),
            (auditor.AEREO04_RBAC107_EMD10_URL,
             'anac_rbac_107_emd10_expired_from_2027_02_23',
             RBAC11_CUTOFF),
        )
        for url, code, evaluation_date in cases:
            record = page(intent, evaluation_date=evaluation_date)
            record['official_sources'].append({'url': url})
            with self.subTest(url=url, date=evaluation_date):
                self.assertIn(
                    'current_legal_fact_source_stale:' + code,
                    reasons(record, evaluation_date))

    def test_montreal_cutoff_is_exact_and_bidirectional(self):
        for intent in auditor.AEREO04_PRE_MONTREAL_2024_OUTCOME_RULES:
            pre = page(intent, evaluation_date=PRE_MONTREAL)
            post = page(intent, evaluation_date=MONTREAL_CUTOFF)
            pre_code = auditor.AEREO04_PRE_MONTREAL_2024_OUTCOME_RULES[
                intent][0]
            post_code = auditor.AEREO04_POST_MONTREAL_2024_OUTCOME_RULES[
                intent][0]
            with self.subTest(intent=intent, phase='pre'):
                self.assertEqual([], reasons(pre, PRE_MONTREAL))
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + post_code,
                    reasons(pre, MONTREAL_CUTOFF))
            with self.subTest(intent=intent, phase='post'):
                self.assertEqual([], reasons(post, MONTREAL_CUTOFF))
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + pre_code,
                    reasons(post, PRE_MONTREAL))

    def test_obsolete_montreal_values_are_rejected_as_current(self):
        intent = 'aer-bagagem-limite-indenizacao-internacional'
        reason = (
            'current_legal_fact_stale_assertion:'
            'aereo_montreal_current_limit_wrong_scope')
        for assertion in (
                'O teto atual é de 1.288 DES.',
                'O teto internacional atual é de 1.131 DES.',
                '1.519 DES limita o dano moral.'):
            with self.subTest(assertion=assertion):
                visible = current_visible(intent) + ' ' + assertion
                self.assertIn(reason, reasons(page(intent, visible=visible)))

    def test_article17_1131_context_is_accepted_not_treated_as_current_cap(self):
        intent = 'aer-bagagem-declaracao-especial-valor'
        record = page(intent)
        self.assertIn('1 131', auditor.norm_key(record['opening']))
        self.assertIn('1 519', auditor.norm_key(record['opening']))
        self.assertEqual([], reasons(record))

    def test_montreal_1519_per_bag_and_lump_sum_are_rejected(self):
        intent = 'aer-bagagem-limite-indenizacao-internacional'
        reason = (
            'current_legal_fact_stale_assertion:'
            'aereo_montreal_current_limit_wrong_scope')
        for assertion in (
                'Cada volume recebe 1.519 DES.',
                'O passageiro recebe automaticamente 1.519 DES.',
                '1.519 DES limita o dano moral.'):
            visible = current_visible(intent) + ' ' + assertion
            with self.subTest(assertion=assertion):
                self.assertIn(reason, reasons(page(intent, visible=visible)))

    def test_damage_gate_rejects_free_regulatory_triad_but_accepts_civil_claim(self):
        intent = 'aer-bagagem-danificada-avaria'
        reason = (
            'current_legal_fact_stale_assertion:'
            'aereo_baggage_damage_free_cash_choice')
        stale = (
            current_visible(intent) +
            ' O passageiro escolhe livremente entre conserto, troca ou '
            'dinheiro.')
        self.assertIn(reason, reasons(page(intent, visible=stale)))
        self.assertEqual([], reasons(page(intent)))

    def test_cba_article260_and_262_false_weight_rule_is_rejected(self):
        intent = 'aer-indenizacao-por-peso-cba-ou-cdc'
        reason = (
            'current_legal_fact_stale_assertion:'
            'aereo_cba_cargo_rate_misattributed_to_baggage')
        for assertion in (
                'O CBA manda indenizar bagagem por quilo.',
                'O artigo 262 trata de bagagem.',
                'São 150 OTN por quilo de bagagem.'):
            visible = current_visible(intent) + ' ' + assertion
            with self.subTest(assertion=assertion):
                self.assertIn(reason, reasons(page(intent, visible=visible)))

    def test_pl5041_cannot_be_asserted_as_current_law(self):
        intent = 'aer-bagagem-mao-franquia-10kg'
        visible = current_visible(intent) + ' O PL 5.041 de 2025 já virou lei.'
        self.assertIn(
            'current_legal_fact_stale_assertion:'
            'aereo_cabin_baggage_allowance_or_bill_false_law',
            reasons(page(intent, visible=visible)))

    def test_rbac107_cutoff_switches_source_outcome_and_stale_rule(self):
        intent = 'aer-furto-inspecao-raio-x-aeroporto'
        pre = page(intent, evaluation_date=PRE_RBAC11)
        post = page(intent, evaluation_date=RBAC11_CUTOFF)
        self.assertEqual([], reasons(pre, PRE_RBAC11))
        self.assertEqual([], reasons(post, RBAC11_CUTOFF))
        self.assertIn(
            'current_legal_fact_source_missing:'
            'anac_rbac_107_emd11_current_from_2027_02_23',
            reasons(pre, RBAC11_CUTOFF))
        self.assertIn(
            'current_legal_fact_source_missing:'
            'anac_rbac_107_emd10_current_before_2027_02_23',
            reasons(post, PRE_RBAC11))
        premature = page(
            intent,
            visible=(current_visible(intent, PRE_RBAC11) +
                     ' A RBAC 107 Emenda 11 já está vigente.'),
            evaluation_date=PRE_RBAC11)
        self.assertIn(
            'current_legal_fact_temporal_stale:'
            'aereo_rbac107_emd11_premature_before_2027_02_23',
            reasons(premature, PRE_RBAC11))

    def test_questions_and_historical_text_do_not_satisfy_outcomes(self):
        intent = 'aer-indenizacao-por-peso-cba-ou-cdc'
        code, groups = auditor.AEREO04_OUTCOME_RULES[intent]
        temporal = ' '.join(
            sentence(group[0])
            for _, temporal_groups in
            auditor.aereo04_outcome_rules_as_of(intent, CURRENT)[1:]
            for group in temporal_groups)
        question = ' '.join(
            sentence(group[0])[:-1] + '?' for group in groups) + ' ' + temporal
        historical = ' '.join(
            'A regra antiga dizia: ' + sentence(group[0]).lower()
            for group in groups) + ' ' + temporal
        for visible in (question, historical):
            self.assertIn(
                'current_legal_fact_outcome_missing:' + code,
                reasons(page(intent, visible=visible)))

    def test_injected_date_and_brazilian_civil_cutoffs_are_deterministic(self):
        self.assertEqual(
            CURRENT, auditor.aereo04_evaluation_date())
        for value in (
                CURRENT,
                datetime.datetime(2026, 7, 12, 23, 59),
                '2026-07-12'):
            self.assertEqual(CURRENT, auditor.aereo04_evaluation_date(value))
        brt = datetime.timezone(datetime.timedelta(hours=-3))
        self.assertEqual(
            PRE_RBAC11,
            auditor.aereo04_evaluation_date(datetime.datetime(
                2027, 2, 22, 23, 59, tzinfo=brt)))
        self.assertEqual(
            RBAC11_CUTOFF,
            auditor.aereo04_evaluation_date(datetime.datetime(
                2027, 2, 23, 0, 0, tzinfo=brt)))
        with self.assertRaises((TypeError, ValueError)):
            auditor.aereo04_evaluation_date('12/07/2026')


if __name__ == '__main__':
    unittest.main()
