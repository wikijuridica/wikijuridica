#!/usr/bin/env python3
"""Cross-runtime regression tests for four adversarial sample reviews."""

import json
import pathlib
import unittest

from tools import audit_v2_pages as auditor


rules = auditor.load_sample_review_current_legal_facts()
ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURE_PATH = (
    ROOT / 'internal' / 'v2ingest' / 'testdata' /
    'sample_review_semantic_cases.json'
)
with FIXTURE_PATH.open(encoding='utf-8') as fixture_handle:
    SEMANTIC_FIXTURE = json.load(fixture_handle)

INTENTS = (
    'banc-tempo-maximo-nome-negativado',
    'emp-duplicata-mercantil-vs-servicos',
    'crim-perdao-do-ofendido',
    'trab-descontos-permitidos',
)

REQUIRED_REPORTED_ASSERTIONS = {
    'O limite quinquenal passa a correr no dia posterior ao vencimento da '
    'obrigação.',
    'A obrigação de emitir a fatura do art. 1º incide nas vendas ajustadas '
    'por trinta dias ou mais.',
    'A pretensão punitiva continua sob titularidade estatal.',
    'Em regra, o empregador não pode abater salário, exceto por adiantamento '
    'ou fundamento legal ou coletivo.',
    'O quinquênio começa a correr na data em que o nome é negativado.',
    'A duplicata só é válida quando o vencimento ocorre pelo menos trinta '
    'dias depois da entrega.',
    'Na queixa privada, a pretensão punitiva é transferida à vítima.',
    'O perdão vale mesmo quando o querelado não concorda.',
    'O empregador pode descontar prejuízo causado por negligência mesmo sem '
    'previsão anterior.',
}

SHARDS = {
    'banc-tempo-maximo-nome-negativado': 'bancario-09.jsonl',
    'emp-duplicata-mercantil-vs-servicos': 'empresarial-09.jsonl',
    'crim-perdao-do-ofendido': 'criminal-09.jsonl',
    'trab-descontos-permitidos': 'trabalhista-11.jsonl',
}


def current_sources(intent):
    return [dict(source) for source in
            SEMANTIC_FIXTURE['source_profiles'][intent]]


def current_visible(intent, omitted=-1, alternative_index=0):
    parts = []
    for index, alternatives in enumerate(rules.OUTCOME_RULES[intent][1]):
        if index == omitted:
            continue
        selected = alternative_index
        if selected < 0 or selected >= len(alternatives):
            selected = len(alternatives) - 1
        value = alternatives[selected]
        parts.append(value[:1].upper() + value[1:] + '.')
    return ' '.join(parts)


def page(intent, visible=None, sources=None):
    return {
        'intent_id': intent,
        'opening': (SEMANTIC_FIXTURE['base_visible'][intent]
                    if visible is None else visible),
        'official_sources': (current_sources(intent)
                             if sources is None else sources),
    }


def fixture_visible(intent, extra=''):
    base = SEMANTIC_FIXTURE['base_visible'][intent]
    return base if not extra.strip() else base + ' ' + extra


class SampleReviewCurrentLegalFactsTest(unittest.TestCase):

    def test_rule_coverage(self):
        self.assertEqual(set(INTENTS), set(rules.SOURCE_REQUIREMENTS))
        self.assertEqual(set(INTENTS), set(rules.OUTCOME_RULES))
        self.assertEqual(set(INTENTS), set(rules.STALE_RULES))
        for intent in INTENTS:
            with self.subTest(intent=intent):
                self.assertTrue(rules.SOURCE_REQUIREMENTS[intent])
                self.assertTrue(rules.OUTCOME_RULES[intent][1])
                self.assertTrue(rules.STALE_RULES[intent])

    def test_shared_semantic_fixture_contract(self):
        self.assertEqual(1, SEMANTIC_FIXTURE.get('schema_version'))
        self.assertEqual(
            'sample-review-semantic-cases-v1',
            SEMANTIC_FIXTURE.get('fixture_id'))
        self.assertEqual(set(INTENTS),
                         set(SEMANTIC_FIXTURE['source_profiles']))
        self.assertEqual(set(INTENTS),
                         set(SEMANTIC_FIXTURE['base_visible']))
        cases = SEMANTIC_FIXTURE['cases']
        self.assertEqual(26, len(cases))
        self.assertEqual(len(cases), len({case['case_id'] for case in cases}))
        self.assertTrue(REQUIRED_REPORTED_ASSERTIONS.issubset(
            {case['assertion'] for case in cases}))
        self.assertEqual(13, sum(case['kind'] == 'correct' for case in cases))
        self.assertEqual(13, sum(case['kind'] == 'wrong' for case in cases))
        for case in cases:
            with self.subTest(case=case['case_id']):
                self.assertIn(case['intent_id'], INTENTS)
                self.assertTrue(case['assertion'].strip())
                if case['kind'] == 'correct':
                    self.assertEqual([], case['expected_reasons'])
                    self.assertNotIn('nonaffirming', case)
                else:
                    self.assertEqual(1, len(case['expected_reasons']))
                    self.assertEqual(
                        {'question', 'history', 'negation'},
                        set(case['nonaffirming']))
                    self.assertTrue(all(
                        value.strip()
                        for value in case['nonaffirming'].values()))
        for intent in INTENTS:
            shape = SEMANTIC_FIXTURE['rule_shape'][intent]
            self.assertEqual(shape['sources'],
                             len(rules.SOURCE_REQUIREMENTS[intent]))
            self.assertEqual(shape['outcomes'],
                             len(rules.OUTCOME_RULES[intent][1]))
            self.assertEqual(shape['stale'],
                             len(rules.STALE_RULES[intent]))
            self.assertEqual(
                shape['source_codes'],
                [requirement[1]
                 for requirement in rules.SOURCE_REQUIREMENTS[intent]])
            self.assertEqual(
                shape['outcome_code'], rules.OUTCOME_RULES[intent][0])
            self.assertEqual(
                shape['stale_codes'],
                [stale_rule[0] for stale_rule in rules.STALE_RULES[intent]])
            self.assertEqual(shape['outcomes'], len(
                SEMANTIC_FIXTURE['outcome_segments'][intent]))
            if intent == 'trab-descontos-permitidos':
                self.assertEqual(1, shape['conditional_sources'])
                self.assertEqual(
                    [rules.LAW_10820_CONDITIONAL_SOURCE[1]],
                    shape['conditional_source_codes'])
            else:
                self.assertNotIn('conditional_sources', shape)

    def test_shared_semantic_fixture_verdicts(self):
        for case in SEMANTIC_FIXTURE['cases']:
            with self.subTest(case=case['case_id'], mode='assertion'):
                visible = fixture_visible(
                    case['intent_id'], case['assertion'])
                self.assertEqual(
                    case['expected_reasons'],
                    auditor.current_legal_fact_reasons(
                        page(case['intent_id'], visible)))
            for mode, control in case.get('nonaffirming', {}).items():
                with self.subTest(case=case['case_id'], mode=mode):
                    self.assertEqual(
                        [], auditor.current_legal_fact_reasons(page(
                            case['intent_id'],
                            fixture_visible(case['intent_id'], control))))

    def test_shared_fixture_rejects_relational_anchor_decoys(self):
        for case in SEMANTIC_FIXTURE['source_anchor_cases']:
            with self.subTest(case=case['case_id']):
                sources = current_sources(case['intent_id'])
                matching = [source for source in sources
                            if source['url'] == case['source_url']]
                self.assertEqual(1, len(matching))
                matching[0]['anchor_claim'] = case['anchor_claim']
                reasons = auditor.current_legal_fact_reasons(page(
                    case['intent_id'],
                    fixture_visible(
                        case['intent_id'], case.get('visible_extra', '')),
                    sources=sources))
                self.assertIn(case['expected_reason'], reasons)

    def test_conditional_law_10820_source_is_required_for_affirmed_claim(self):
        wanted_url, code, _ = rules.LAW_10820_CONDITIONAL_SOURCE
        for case in SEMANTIC_FIXTURE['conditional_source_trigger_cases']:
            with self.subTest(case=case['case_id']):
                self.assertEqual(
                    'current_legal_fact_source_missing:' + code,
                    case['expected_reason'])
                sources = [
                    source for source in current_sources(case['intent_id'])
                    if source['url'] != wanted_url
                ]
                reasons = auditor.current_legal_fact_reasons(page(
                    case['intent_id'],
                    fixture_visible(case['intent_id'], case['assertion']),
                    sources=sources))
                self.assertIn(case['expected_reason'], reasons)

    def test_shared_fixture_rejects_every_negated_outcome_substitution(self):
        covered = {intent: set() for intent in INTENTS}
        for case in SEMANTIC_FIXTURE['outcome_substitution_cases']:
            with self.subTest(case=case['case_id']):
                segments = list(SEMANTIC_FIXTURE[
                    'outcome_segments'][case['intent_id']])
                self.assertGreaterEqual(case['group_index'], 0)
                self.assertLess(case['group_index'], len(segments))
                segments[case['group_index']] = case['replacement']
                reasons = auditor.current_legal_fact_reasons(page(
                    case['intent_id'], ' '.join(segments)))
                self.assertIn(case['expected_reason'], reasons)
                covered[case['intent_id']].add(case['group_index'])
        for intent in INTENTS:
            with self.subTest(intent=intent):
                self.assertEqual(
                    set(range(len(SEMANTIC_FIXTURE[
                        'outcome_segments'][intent]))), covered[intent])

    def test_rejects_every_outcome_group_omission(self):
        for intent in INTENTS:
            code, groups = rules.OUTCOME_RULES[intent]
            for omitted in range(len(groups)):
                with self.subTest(intent=intent, omitted=omitted):
                    reasons = auditor.current_legal_fact_reasons(page(
                        intent, current_visible(intent, omitted=omitted)))
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code, reasons)

    def test_requires_every_exact_source_and_material_anchor(self):
        for intent in INTENTS:
            requirements = rules.SOURCE_REQUIREMENTS[intent]
            for index, (wanted_url, code, metadata_groups) in enumerate(
                    requirements):
                with self.subTest(intent=intent, source=code):
                    sources = [dict(source)
                               for source in current_sources(intent)]
                    sources[index]['url'] = (
                        'https://attacker.invalid/?official=' + wanted_url)
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        auditor.current_legal_fact_reasons(page(
                            intent, fixture_visible(intent), sources=sources)))
                if not metadata_groups:
                    continue
                with self.subTest(intent=intent, anchor=code):
                    sources = [dict(source)
                               for source in current_sources(intent)]
                    sources[index]['name'] = 'Fonte genérica'
                    sources[index]['anchor_claim'] = (
                        'Documento oficial sem desfecho material.')
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' + code,
                        auditor.current_legal_fact_reasons(page(
                            intent, fixture_visible(intent), sources=sources)))

    def test_rejects_original_false_greens(self):
        tests = (
            (
                'banc-tempo-maximo-nome-negativado',
                'O prazo de cinco anos conta a partir dessa inscrição, '
                'não do vencimento.',
                'credit_listing_five_year_term_from_registration',
            ),
            (
                'emp-duplicata-mercantil-vs-servicos',
                'A duplicata mercantil é extraída da fatura, exigindo '
                'prazo não inferior a 30 dias contado da entrega.',
                'duplicate_article_1_thirty_days_as_universal_title_'
                'requirement',
            ),
            (
                'crim-perdao-do-ofendido',
                'Nesses crimes, o interesse na punição pertence '
                'principalmente a quem foi atingido.',
                'private_action_jus_puniendi_transferred_to_victim',
            ),
            (
                'trab-descontos-permitidos',
                'Os abatimentos incluem contribuições sindicais '
                'autorizadas. Todos têm respaldo em lei e por isso '
                'independem de autorização específica do empregado.',
                'union_contribution_without_prior_express_authorization',
            ),
        )
        for intent, false_text, code in tests:
            with self.subTest(intent=intent):
                reasons = auditor.current_legal_fact_reasons(page(
                    intent, fixture_visible(intent, false_text)))
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code, reasons)

    def test_rejects_contradictions_but_not_questions_or_history(self):
        for intent in INTENTS:
            base = fixture_visible(intent)
            for code, alternatives in rules.STALE_RULES[intent]:
                stale = alternatives[0]
                wanted = 'current_legal_fact_stale_assertion:' + code
                with self.subTest(intent=intent, code=code, mode='affirmed'):
                    self.assertIn(
                        wanted, auditor.current_legal_fact_reasons(page(
                            intent, base + ' ' + stale + '.')))
                contexts = {
                    'question': ' ' + stale + '?',
                    'history': ' A regra antiga dizia: ' + stale + '.',
                    'meta': ' É falso que ' + stale + '.',
                }
                for mode, context in contexts.items():
                    with self.subTest(
                            intent=intent, code=code, mode=mode):
                        self.assertNotIn(
                            wanted, auditor.current_legal_fact_reasons(page(
                                intent, base + context)))

    def test_rejects_labor_written_form_and_consigned_loan_misattribution(self):
        intent = 'trab-descontos-permitidos'
        base = fixture_visible(intent)
        tests = {
            'employee_damage_deduction_written_form_mandatory':
                'No caso de simples culpa, essa possibilidade deve ser '
                'previamente combinada por escrito.',
            'sumula_342_consigned_loan_misattribution':
                'A Súmula 342 admite plano de saúde, seguro de vida e '
                'empréstimo consignado.',
        }
        for code, false_text in tests.items():
            with self.subTest(code=code):
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(page(
                        intent, base + ' ' + false_text)))

    def test_semantic_guards_accept_natural_corrections(self):
        tests = (
            (
                'emp-duplicata-mercantil-vs-servicos',
                'A duplicata mercantil exige prazo indicado com clareza e '
                'pode vencer em menos de 30 dias.',
                'duplicate_article_1_thirty_days_as_universal_title_'
                'requirement',
            ),
            (
                'trab-descontos-permitidos',
                'A Súmula 342 não inclui nem disciplina empréstimo '
                'consignado.',
                'sumula_342_consigned_loan_misattribution',
            ),
            (
                'trab-descontos-permitidos',
                'A contribuição sindical exige autorização prévia e '
                'expressa. O desconto legal de INSS independe de autorização '
                'do empregado.',
                'union_contribution_without_prior_express_authorization',
            ),
            (
                'trab-descontos-permitidos',
                'A contribuição sindical exige autorização prévia e '
                'expressa.\nTodos os descontos legais de INSS independem de '
                'autorização do empregado.',
                'union_contribution_without_prior_express_authorization',
            ),
        )
        for intent, extra, code in tests:
            with self.subTest(intent=intent, code=code):
                self.assertNotIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(page(
                        intent, fixture_visible(intent, extra))))

    def test_accepts_live_corrected_shards(self):
        for intent, shard in SHARDS.items():
            with self.subTest(intent=intent):
                found = False
                path = ROOT / 'data' / 'editorial' / 'v2_pages' / shard
                with path.open(encoding='utf-8') as handle:
                    for line in handle:
                        record = json.loads(line)
                        if record.get('intent_id') != intent:
                            continue
                        found = True
                        self.assertEqual(
                            [], auditor.current_legal_fact_reasons(record))
                        break
                self.assertTrue(found, f'{intent} missing from {shard}')


if __name__ == '__main__':
    unittest.main()
