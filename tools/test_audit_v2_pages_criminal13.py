#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name('audit_v2_pages.py')
SPEC = importlib.util.spec_from_file_location('audit_v2_pages', MODULE_PATH)
auditor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auditor)


INTENTS = (
    'crim-bo-online-quando-serve',
    'crim-representar-prazo-decadencial',
    'crim-retratar-representacao',
    'crim-crime-acao-publica-ou-privada',
    'crim-delegacia-nao-registrou-bo',
    'crim-acompanhar-andamento-inquerito',
    'crim-assistente-de-acusacao',
    'crim-direitos-da-vitima-no-processo',
    'crim-vitima-discorda-do-arquivamento',
    'crim-calunia-difamacao-injuria',
    'crim-como-processar-quem-me-ofendeu',
    'crim-xingamento-racial-injuria-ou-racismo',
    'crim-difamacao-nas-redes',
    'crim-retratacao-encerra-ofensa',
    'crim-excecao-da-verdade',
    'crim-homofobia-e-crime',
    'crim-intolerancia-religiosa',
)


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def current_visible(intent):
    return ' '.join(
        sentence(alternatives[0])
        for alternatives in auditor.CRIMINAL13_OUTCOME_RULES[intent][1])


def current_sources(intent):
    return [
        {
            'url': wanted_url,
            'name': 'Fonte oficial primária',
            'anchor_claim': 'Sustenta o desfecho material vigente.',
        }
        for wanted_url, _ in auditor.CRIMINAL13_SOURCE_REQUIREMENTS[intent]
    ]


def page(intent, visible=None, sources=None):
    return {
        'intent_id': intent,
        'opening': current_visible(intent) if visible is None else visible,
        'official_sources': (
            current_sources(intent) if sources is None else sources),
    }


class Criminal13CurrentLawTest(unittest.TestCase):

    def test_rule_coverage(self):
        self.assertEqual(17, len(INTENTS))
        self.assertEqual(len(INTENTS), len(
            auditor.CRIMINAL13_SOURCE_REQUIREMENTS))
        self.assertEqual(len(INTENTS), len(
            auditor.CRIMINAL13_OUTCOME_RULES))
        self.assertEqual(len(INTENTS), len(
            auditor.CRIMINAL13_STALE_RULES))
        for intent in INTENTS:
            with self.subTest(intent=intent):
                self.assertTrue(
                    auditor.CRIMINAL13_SOURCE_REQUIREMENTS.get(intent))
                self.assertTrue(auditor.CRIMINAL13_OUTCOME_RULES.get(intent))
                self.assertTrue(auditor.CRIMINAL13_STALE_RULES.get(intent))

    def test_accepts_current_rules(self):
        for intent in INTENTS:
            with self.subTest(intent=intent):
                self.assertEqual(
                    [], auditor.current_legal_fact_reasons(page(intent)))

    def test_live_snapshot_when_present(self):
        snapshot = MODULE_PATH.parent.parent / (
            'data/editorial/v2_pages/criminal-13.jsonl')
        if not snapshot.exists():
            self.skipTest('criminal-13 snapshot is not present')
        count = 0
        with snapshot.open(encoding='utf-8') as handle:
            for count, line in enumerate(handle, 1):
                record = json.loads(line)
                # One subTest per record. A bare assertEqual stopped at the
                # first failing page and hid the other twelve (measured on
                # 2026-09-05, before the source table regained parity with
                # the Go twin): the report must name every defective page.
                with self.subTest(intent=record.get('intent_id'), line=count):
                    self.assertEqual(
                        [], auditor.current_legal_fact_reasons(record),
                        record.get('intent_id'))
        self.assertEqual(17, count)

    def test_requires_every_exact_source(self):
        for intent in INTENTS:
            requirements = auditor.CRIMINAL13_SOURCE_REQUIREMENTS[intent]
            for index, (wanted_url, code) in enumerate(requirements):
                with self.subTest(intent=intent, code=code):
                    sources = [dict(item) for item in current_sources(intent)]
                    sources[index]['url'] = (
                        'https://attacker.invalid/decoy?official=' + wanted_url)
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        auditor.current_legal_fact_reasons(
                            page(intent, sources=sources)))

    def test_rejects_canonical_identity_decoys(self):
        intent = 'crim-bo-online-quando-serve'
        wanted_url, code = auditor.CRIMINAL13_SOURCE_REQUIREMENTS[intent][0]
        decoys = {
            'userinfo': wanted_url.replace(
                'https://', 'https://attacker@', 1),
            'port': wanted_url.replace(
                'www.planalto.gov.br', 'www.planalto.gov.br:444', 1),
            'query': wanted_url + '?extra=1',
            'fragment': wanted_url + '#extra',
            'embedded': 'https://attacker.invalid/?next=' + wanted_url,
        }
        for name, bad_url in decoys.items():
            with self.subTest(name=name):
                sources = [dict(item) for item in current_sources(intent)]
                sources[0]['url'] = bad_url
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, sources=sources)))

    def test_rejects_outcome_omissions(self):
        for intent in INTENTS:
            outcome_code, groups = auditor.CRIMINAL13_OUTCOME_RULES[intent]
            for index, alternatives in enumerate(groups):
                with self.subTest(intent=intent, group=index):
                    visible = current_visible(intent).replace(
                        sentence(alternatives[0]), '', 1)
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + outcome_code,
                        auditor.current_legal_fact_reasons(
                            page(intent, visible=visible)))

    def test_rejects_historically_framed_outcomes(self):
        for intent in INTENTS:
            outcome_code, groups = auditor.CRIMINAL13_OUTCOME_RULES[intent]
            for index, alternatives in enumerate(groups):
                with self.subTest(intent=intent, group=index):
                    current = sentence(alternatives[0])
                    historical = (
                        'A regra antiga dizia: ' + current[:1].lower() +
                        current[1:])
                    visible = current_visible(intent).replace(
                        current, historical, 1)
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + outcome_code,
                        auditor.current_legal_fact_reasons(
                            page(intent, visible=visible)))

    def test_rejects_question_only_outcomes(self):
        for intent in INTENTS:
            with self.subTest(intent=intent):
                outcome_code, groups = auditor.CRIMINAL13_OUTCOME_RULES[intent]
                visible = ' '.join(
                    sentence(alternatives[0])[:-1] + '?'
                    for alternatives in groups)
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + outcome_code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_rejects_meta_negated_and_revoked_outcomes(self):
        tests = {
            'crim-representar-prazo-decadencial': (
                'É falso que seis meses, conhecimento da autoria, '
                'Lei 15.438/2026, doze meses, violência doméstica e familiar '
                'contra a mulher e não transforma em condicionada uma ação '
                'sejam a regra.'),
            'crim-xingamento-racial-injuria-ou-racismo': current_visible(
                'crim-xingamento-racial-injuria-ou-racismo').replace(
                    'Art 2 a.', 'A regra revogada dizia art. 2-A.', 1),
        }
        for intent, visible in tests.items():
            with self.subTest(intent=intent):
                outcome_code = auditor.CRIMINAL13_OUTCOME_RULES[intent][0]
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + outcome_code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_rejects_stale_contradictions(self):
        for intent in INTENTS:
            with self.subTest(intent=intent):
                code, alternatives = auditor.CRIMINAL13_STALE_RULES[intent]
                visible = current_visible(intent) + ' ' + sentence(
                    alternatives[0])
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_rejects_semantic_stale_paraphrases(self):
        tests = {
            'crim-bo-online-quando-serve':
                'O BO eletrônico resolve qualquer crime nacionalmente e '
                'elimina a necessidade de perícia.',
            'crim-representar-prazo-decadencial':
                'No âmbito doméstico, permanece aplicável o prazo de seis '
                'meses.',
            'crim-retratar-representacao':
                'Na Lei Maria da Penha, o limite é antes da denúncia '
                'oferecida.',
            'crim-crime-acao-publica-ou-privada':
                'No estelionato, como regra, a ação é incondicionada.',
            'crim-delegacia-nao-registrou-bo':
                'Sendo ação privada, a polícia não pode investigar.',
            'crim-acompanhar-andamento-inquerito':
                'A vítima possui acesso integral a todas as diligências em '
                'andamento.',
            'crim-assistente-de-acusacao':
                'O assistente é obrigado a seguir o Ministério Público, sem '
                'autonomia.',
            'crim-direitos-da-vitima-no-processo':
                'A vítima não precisa ser comunicada da sentença.',
            'crim-vitima-discorda-do-arquivamento':
                'Hoje o arquivamento é revisado pelo juiz.',
            'crim-calunia-difamacao-injuria':
                'A difamação pressupõe falsidade do fato.',
            'crim-como-processar-quem-me-ofendeu':
                'O boletim dispensa a queixa-crime.',
            'crim-xingamento-racial-injuria-ou-racismo':
                'O artigo 2-A também abrange religião.',
            'crim-difamacao-nas-redes':
                'A difamação depende de o conteúdo ser falso.',
            'crim-retratacao-encerra-ofensa':
                'A retratação na injúria isenta o ofensor.',
            'crim-excecao-da-verdade':
                'Na injúria, cabe exceção da verdade.',
            'crim-homofobia-e-crime':
                'A ADO 26 instituiu um crime autônomo.',
            'crim-intolerancia-religiosa':
                'Discordar de dogmas sempre é crime.',
        }
        for intent in INTENTS:
            with self.subTest(intent=intent):
                code = auditor.CRIMINAL13_STALE_RULES[intent][0]
                visible = current_visible(intent) + ' ' + tests[intent]
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_rejects_new_honor_false_greens(self):
        tests = {
            'crim-calunia-difamacao-injuria': (
                'Na difamação, o fato não é criminoso e fato criminoso '
                'sempre configura calúnia.'),
            'crim-retratacao-encerra-ofensa': (
                'Na difamação, o ofensor reconhece que o fato não é '
                'verdadeiro ao se retratar.'),
        }
        for intent, stale in tests.items():
            with self.subTest(intent=intent):
                code = auditor.CRIMINAL13_STALE_RULES[intent][0]
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(page(
                        intent, visible=current_visible(intent) + ' ' +
                        stale)))

    def test_meta_prefix_cannot_hide_stale_assertion(self):
        for intent in INTENTS:
            code, alternatives = auditor.CRIMINAL13_STALE_RULES[intent]
            visible = (
                current_visible(intent) +
                ' É falso que este tópico seja irrelevante para estudantes, '
                'advogados, cidadãos, empresas, pesquisadores e jornalistas, '
                'porque ' + sentence(alternatives[0]))
            with self.subTest(intent=intent):
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible=visible)))

    def test_accepts_correct_negative_contrasts(self):
        tests = {
            'crim-bo-online-quando-serve':
                'O BO não substitui exame pericial nem atendimento '
                'presencial.',
            'crim-representar-prazo-decadencial':
                'Na violência doméstica, o prazo não continua em seis meses.',
            'crim-retratar-representacao':
                'Na Lei Maria da Penha, o limite não é antes do oferecimento '
                'da denúncia e a audiência de retratação não pode ser '
                'marcada sem pedido expresso.',
            'crim-crime-acao-publica-ou-privada':
                'No estelionato, a ação não é, como regra, incondicionada, '
                'nem qualquer ente público torna o caso incondicionado.',
            'crim-acompanhar-andamento-inquerito':
                'A vítima não tem acesso irrestrito a todas as diligências '
                'em andamento; o sigilo não impede qualquer acesso do '
                'advogado aos elementos documentados.',
            'crim-assistente-de-acusacao':
                'O assistente não é obrigado a seguir o Ministério Público e '
                'não está sem autonomia.',
            'crim-vitima-discorda-do-arquivamento':
                'Antes era homologado pelo juiz o arquivamento no modelo '
                'anterior.',
            'crim-calunia-difamacao-injuria':
                'A calúnia exige falsidade, não a difamação.',
            'crim-como-processar-quem-me-ofendeu':
                'O boletim não substitui nem dispensa a queixa-crime.',
            'crim-retratacao-encerra-ofensa':
                'A retratação isenta calúnia e difamação, não a injúria; '
                'pelos mesmos meios, somente a pedido do ofendido, não '
                'automaticamente; na difamação, retratar não significa que '
                'o ofensor reconhece que o fato não é verdadeiro.',
            'crim-excecao-da-verdade':
                'Na difamação, a exceção da verdade não cabe em todo caso.',
            'crim-homofobia-e-crime':
                'A ADO 26 não criou tipo penal autônomo e nem toda crítica '
                'sobre sexualidade é crime.',
        }
        for intent, correct in tests.items():
            with self.subTest(intent=intent):
                code = auditor.CRIMINAL13_STALE_RULES[intent][0]
                self.assertNotIn(
                    'current_legal_fact_stale_assertion:' + code,
                    auditor.current_legal_fact_reasons(page(
                        intent, visible=current_visible(intent) + ' ' +
                        correct)))

    def test_ignores_stale_questions_and_history(self):
        for intent in INTENTS:
            code, alternatives = auditor.CRIMINAL13_STALE_RULES[intent]
            for index, stale in enumerate(alternatives):
                contexts = {
                    'question': ' ' + stale + '?',
                    'history': ' A regra revogada dizia: ' + stale + '.',
                    'meta': ' É falso que ' + stale + '.',
                }
                for name, extra in contexts.items():
                    with self.subTest(
                            intent=intent, alternative=index, context=name):
                        self.assertNotIn(
                            'current_legal_fact_stale_assertion:' + code,
                            auditor.current_legal_fact_reasons(page(
                                intent,
                                visible=current_visible(intent) + extra)))


if __name__ == '__main__':
    unittest.main()
