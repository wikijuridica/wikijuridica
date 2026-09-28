#!/usr/bin/env python3
"""Adversarial parity tests for the aereo-06 current-law gate."""

import copy
import datetime
import hashlib
import json
import pathlib
import unittest
import urllib.parse

from tools import audit_v2_pages as auditor


CURRENT = datetime.date(2026, 7, 12)

# Frozen from the reviewed Go/Python contract.  The snapshot binds the 11
# ordered intents, 33 source occurrences, 13 exact URLs plus the closed list
# of alternate official surfaces of the same norm (parity with Go
# `aereo06SourceURLAlternates`, 9ac7ff75 / BUG-211, reviewed 2026-09-05),
# every material anchor, all 76 outcomes, 11 stale families/scopes,
# misleading-anchor rules, and the intent-specific ban on using REsp
# 1.966.032 as retroactive-mileage authority.  Updating a literal requires
# an intentional digest review.
AEREO06_CONTRACT_SHA256 = (
    'e7436a005613549b10cddf7ff3018352d2c7c83b667808fc7068a052fbd9f26a')


def contract_snapshot():
    return {
        'intent_order': auditor.AEREO06_INTENT_ORDER,
        'source_urls': sorted(auditor.AEREO06_SOURCE_URLS.items()),
        'source_url_alternates': sorted(
            (kind, list(urls)) for kind, urls in
            auditor.AEREO06_SOURCE_URL_ALTERNATES.items()),
        'source_requirements': sorted(
            auditor.AEREO06_SOURCE_REQUIREMENTS.items()),
        'general_anchors': sorted(
            auditor.AEREO06_GENERAL_SOURCE_ANCHOR_RULES.items()),
        'specific_anchors': sorted(
            (intent, kind, rule)
            for (intent, kind), rule in
            auditor.AEREO06_INTENT_SOURCE_ANCHOR_RULES.items()),
        'misleading_anchors': sorted(
            (intent, kind, alternatives)
            for (intent, kind), alternatives in
            auditor.AEREO06_MISLEADING_SOURCE_ANCHOR_RULES.items()),
        'outcomes': sorted(auditor.AEREO06_OUTCOME_RULES.items()),
        'stale_rules': auditor.AEREO06_STALE_RULES,
        'stale_scopes': sorted(
            (code, sorted(scope))
            for code, scope in auditor.AEREO06_STALE_RULE_INTENTS.items()),
        'forbidden_sources': sorted(
            (intent, sorted(kinds))
            for intent, kinds in
            auditor.AEREO06_FORBIDDEN_SOURCE_KINDS.items()),
    }


def contract_digest():
    payload = json.dumps(
        contract_snapshot(), sort_keys=True, separators=(',', ':'),
        ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def sentence(value):
    return value[:1].upper() + value[1:] + '.'


def anchor_rule(intent, kind):
    rule = auditor.AEREO06_INTENT_SOURCE_ANCHOR_RULES.get((intent, kind))
    if rule is None:
        rule = auditor.AEREO06_GENERAL_SOURCE_ANCHOR_RULES.get(kind)
    return rule


def source_fixture(intent, kind):
    code, groups = anchor_rule(intent, kind)
    del code
    return {
        'url': auditor.AEREO06_SOURCE_URLS[kind],
        'name': 'Fonte oficial específica',
        'anchor_claim': ' '.join(
            sentence(alternatives[0]) for alternatives in groups),
    }


def current_sources(intent):
    return [
        source_fixture(intent, kind)
        for kind, _ in auditor.AEREO06_SOURCE_REQUIREMENTS[intent]
    ]


def current_visible(intent):
    _, groups = auditor.AEREO06_OUTCOME_RULES[intent]
    visible = ' '.join(sentence(alternatives[0]) for alternatives in groups)
    if intent == 'aer-conta-milhas-bloqueada-fraude':
        visible += (
            ' A lei não garante que a revisão seja feita por uma pessoa '
            'natural.')
    return visible


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
    return auditor.current_aereo06_legal_fact_reasons(
        record, intent, visible, CURRENT)


def source_reason(intent, kind):
    for candidate, code in auditor.AEREO06_SOURCE_REQUIREMENTS[intent]:
        if candidate == kind:
            return 'current_legal_fact_source_missing:' + code
    raise AssertionError((intent, kind))


def exact_url_decoys(raw_url):
    parsed = urllib.parse.urlsplit(raw_url)
    path = parsed.path[:-1] if parsed.path.endswith('/') else parsed.path + '/'
    query = parsed.query + ('&' if parsed.query else '') + 'decoy=1'
    hostname = parsed.hostname or ''
    variants = (
        urllib.parse.urlunsplit(parsed._replace(fragment='decoy')),
        urllib.parse.urlunsplit(parsed._replace(query=query)),
        urllib.parse.urlunsplit(parsed._replace(path=path)),
        urllib.parse.urlunsplit(parsed._replace(
            path='//' + parsed.path.lstrip('/'))),
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


class Aereo06CurrentLawGateTest(unittest.TestCase):

    def test_inventory_order_and_literal_cardinalities(self):
        expected_order = (
            'aer-milhas-expiradas-recuperar',
            'aer-conta-milhas-bloqueada-fraude',
            'aer-milhas-resgate-nao-reconhecido-furto',
            'aer-passagem-milhas-voo-cancelado-direitos',
            'aer-vender-milhas-legalidade-risco',
            'aer-milhas-nao-creditadas-voo',
            'aer-programa-mudou-tabela-resgate',
            'aer-milhas-falecido-heranca',
            'aer-cancelar-passagem-milhas-estorno',
            'aer-clube-milhas-cancelar-assinatura',
            'aer-pontos-cartao-nao-transferidos',
        )
        self.assertEqual(expected_order, auditor.AEREO06_INTENT_ORDER)
        self.assertEqual(11, len(auditor.AEREO06_INTENTS))
        self.assertEqual(
            auditor.AEREO06_INTENTS,
            frozenset(auditor.AEREO06_SOURCE_REQUIREMENTS))
        self.assertEqual(
            auditor.AEREO06_INTENTS,
            frozenset(auditor.AEREO06_OUTCOME_RULES))
        self.assertEqual(
            33, sum(len(items) for items in
                    auditor.AEREO06_SOURCE_REQUIREMENTS.values()))
        self.assertEqual(33, len(auditor.AEREO06_SOURCE_ANCHOR_RULES))
        self.assertEqual(13, len(auditor.AEREO06_SOURCE_URLS))
        self.assertEqual(
            76, sum(len(groups) for _, groups in
                    auditor.AEREO06_OUTCOME_RULES.values()))
        self.assertEqual(11, len(auditor.AEREO06_STALE_RULES))
        self.assertEqual(
            {code for code, _ in auditor.AEREO06_STALE_RULES},
            set(auditor.AEREO06_STALE_RULE_INTENTS))
        outcome_codes = [
            code for code, _ in auditor.AEREO06_OUTCOME_RULES.values()]
        self.assertEqual(len(outcome_codes), len(set(outcome_codes)))
        for intent, (_, groups) in auditor.AEREO06_OUTCOME_RULES.items():
            signatures = [
                tuple(auditor.norm_key(item) for item in group)
                for group in groups]
            with self.subTest(intent=intent):
                self.assertEqual(len(signatures), len(set(signatures)))

    def test_active_contract_matches_reviewed_digest(self):
        self.assertEqual(AEREO06_CONTRACT_SHA256, contract_digest())

    def test_all_thirteen_source_urls_are_literal(self):
        expected = {
            'cdc': 'https://www2.camara.leg.br/legin/fed/lei/1990/lei-8078-11-setembro-1990-365086-normaatualizada-pl.html',
            'civil_code': 'https://www2.camara.leg.br/legin/fed/lei/2002/lei-10406-10-janeiro-2002-432893-normaatualizada-pl.html',
            'consumidor_gov': 'https://www.gov.br/pt-br/servicos/reclamar-contra-servico-ou-produto-de-empresas-privadas',
            'lgpd': 'https://www2.camara.leg.br/legin/fed/lei/2018/lei-13709-14-agosto-2018-787077-normaatualizada-pl.html',
            'anpd_titular': 'https://www.gov.br/anpd/pt-br/canais_atendimento/cidadao-titular-de-dados/denuncia-peticao-de-titular-referente-lgpd',
            'anpd_guide': 'https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-do-consumidor_como-proteger-seus-dados-pessoais-final.pdf',
            'res400': 'https://www.anac.gov.br/assuntos/legislacao/legislacao-1/resolucoes/resolucoes-2016/resolucao-no-400-13-12-2016',
            'stj_resp_1966032': 'https://scon.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&aplicacao=informativo&livre=%40CNOT%3D%27019282%27',
            'stj_resp_2011456': 'https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2024/07062024-Companhias-aereas-podem-proibir-venda-de-milhas-em-programas-de-fidelidade--define-Terceira-Turma.aspx',
            'stj_resp_1878651': 'https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2022/21102022-Programa-de-fidelidade-aerea-gratuito-pode-cancelar-pontos-com-o-falecimento-do-titular.aspx',
            'stj_resp_1878651_report': 'https://processo.stj.jus.br/jurisprudencia/externo/informativo/?acao=pesquisar&livre=%40CNOT%3D%27019461%27',
            'sac_decree_11034': 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/d11034.htm',
            'cmn_resolution_4949': 'https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4949&tipo=RESOLU%C3%87%C3%83O+CMN',
        }
        self.assertEqual(expected, auditor.AEREO06_SOURCE_URLS)

    def test_cmn_4949_alternate_surfaces_are_literal_and_closed(self):
        # Parity with internal/v2ingest/current_legal_facts_aereo06.go
        # (aereo06SourceURLAlternates): the DOU publication and the BCB
        # consolidated PDF are the two surfaces the stock actually cites for
        # Resolucao CMN 4.949/2021.  Nothing else is accepted for any kind.
        self.assertEqual(
            {
                'cmn_resolution_4949': (
                    'https://www.in.gov.br/web/dou/-/resolucao-cmn-n-4.949-de-30-de-setembro-de-2021-350015767',
                    'https://normativos.bcb.gov.br/Lists/Normativos/Attachments/51207/Res_4949_v2_L.pdf',
                ),
            },
            auditor.AEREO06_SOURCE_URL_ALTERNATES)
        self.assertTrue(set(auditor.AEREO06_SOURCE_URL_ALTERNATES) <=
                        set(auditor.AEREO06_SOURCE_URLS))

    def test_each_alternate_official_surface_is_accepted_exactly(self):
        intent = 'aer-pontos-cartao-nao-transferidos'
        kinds = [kind for kind, _ in auditor.AEREO06_SOURCE_REQUIREMENTS[intent]]
        index = kinds.index('cmn_resolution_4949')
        for alternate in auditor.AEREO06_SOURCE_URL_ALTERNATES[
                'cmn_resolution_4949']:
            sources = current_sources(intent)
            sources[index]['url'] = alternate
            with self.subTest(alternate=alternate):
                self.assertNotIn(
                    source_reason(intent, 'cmn_resolution_4949'),
                    direct_reasons(page(intent, sources=sources)))

    def test_alternate_surfaces_reject_hostile_decoys_and_other_norms(self):
        # Controls that MUST keep failing: every exact-identity decoy of each
        # alternate, and the same surfaces pointing at a different norm or a
        # different attachment id (byte-exact identity, never "same host").
        intent = 'aer-pontos-cartao-nao-transferidos'
        kinds = [kind for kind, _ in auditor.AEREO06_SOURCE_REQUIREMENTS[intent]]
        index = kinds.index('cmn_resolution_4949')
        other_norms = (
            'https://www.in.gov.br/web/dou/-/resolucao-cmn-n-4.950-de-30-de-setembro-de-2021-350015767',
            'https://www.in.gov.br/web/dou/-/resolucao-cmn-n-4.949-de-30-de-setembro-de-2021-350015768',
            'https://normativos.bcb.gov.br/Lists/Normativos/Attachments/51208/Res_4949_v2_L.pdf',
            'https://normativos.bcb.gov.br/Lists/Normativos/Attachments/51207/Res_4950_v2_L.pdf',
            'https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4950&tipo=RESOLU%C3%87%C3%83O+CMN',
        )
        count = 0
        for alternate in auditor.AEREO06_SOURCE_URL_ALTERNATES[
                'cmn_resolution_4949']:
            for decoy in exact_url_decoys(alternate) + other_norms:
                count += 1
                sources = current_sources(intent)
                sources[index]['url'] = decoy
                with self.subTest(alternate=alternate, decoy=decoy):
                    self.assertIn(
                        source_reason(intent, 'cmn_resolution_4949'),
                        direct_reasons(page(intent, sources=sources)))
        self.assertGreaterEqual(count, 36)

    def test_synthetic_and_real_shard_fixtures_are_green(self):
        for intent in auditor.AEREO06_INTENT_ORDER:
            with self.subTest(kind='synthetic', intent=intent):
                self.assertEqual([], direct_reasons(page(intent)))

        shard = pathlib.Path(__file__).resolve().parents[1] / (
            'data/editorial/v2_pages/aereo-06.jsonl')
        records = [
            json.loads(line) for line in shard.read_text(
                encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(
            list(auditor.AEREO06_INTENT_ORDER),
            [record['intent_id'] for record in records])
        for record in records:
            with self.subTest(kind='real', intent=record['intent_id']):
                self.assertEqual([], direct_reasons(record))

    def test_removing_each_source_is_detected(self):
        count = 0
        for intent in auditor.AEREO06_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO06_SOURCE_REQUIREMENTS[intent]):
                count += 1
                sources = current_sources(intent)
                del sources[index]
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        source_reason(intent, kind),
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(33, count)

    def test_every_source_occurrence_rejects_hostile_exact_url_decoys(self):
        count = 0
        for intent in auditor.AEREO06_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO06_SOURCE_REQUIREMENTS[intent]):
                for decoy in exact_url_decoys(
                        auditor.AEREO06_SOURCE_URLS[kind]):
                    count += 1
                    sources = current_sources(intent)
                    sources[index]['url'] = decoy
                    with self.subTest(intent=intent, kind=kind, decoy=decoy):
                        self.assertIn(
                            source_reason(intent, kind),
                            direct_reasons(page(intent, sources=sources)))
        self.assertGreaterEqual(count, 396)

    def test_every_material_anchor_rejects_generic_metadata(self):
        count = 0
        for intent in auditor.AEREO06_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO06_SOURCE_REQUIREMENTS[intent]):
                count += 1
                code, _ = anchor_rule(intent, kind)
                sources = current_sources(intent)
                sources[index]['name'] = 'Fonte oficial sem escopo material'
                sources[index]['anchor_claim'] = 'Documento oficial.'
                with self.subTest(intent=intent, kind=kind):
                    self.assertIn(
                        'current_legal_fact_source_anchor_missing:' + code,
                        direct_reasons(page(intent, sources=sources)))
        self.assertEqual(33, count)

    def test_every_anchor_group_rejects_meta_negation(self):
        prefixes = (
            'A fonte não afirma que ',
            'É falso que ',
            'É incorreto afirmar que ',
        )
        count = 0
        for intent in auditor.AEREO06_INTENT_ORDER:
            for index, (kind, _) in enumerate(
                    auditor.AEREO06_SOURCE_REQUIREMENTS[intent]):
                code, groups = anchor_rule(intent, kind)
                for group_index in range(len(groups)):
                    for prefix in prefixes:
                        count += 1
                        claims = []
                        for index_in_rule, alternatives in enumerate(groups):
                            claim = alternatives[0]
                            if index_in_rule == group_index:
                                claim = prefix + claim
                            claims.append(sentence(claim))
                        sources = current_sources(intent)
                        sources[index]['anchor_claim'] = ' '.join(claims)
                        with self.subTest(
                                intent=intent, kind=kind,
                                group=group_index, prefix=prefix):
                            self.assertIn(
                                'current_legal_fact_source_anchor_missing:' +
                                code,
                                direct_reasons(page(
                                    intent, sources=sources)))
        self.assertGreater(count, 300)

    def test_misleading_anchors_cannot_pass_by_keywords(self):
        cases = (
            ('aer-conta-milhas-bloqueada-fraude', 'lgpd',
             'O art. 20 garante revisor humano.'),
            ('aer-passagem-milhas-voo-cancelado-direitos',
             'stj_resp_1966032',
             'O REsp 1.966.032 fixa indenização para todo cancelamento.'),
            ('aer-vender-milhas-legalidade-risco', 'stj_resp_2011456',
             'O REsp 2.011.456 declarou crime toda venda de milhas.'),
            ('aer-milhas-falecido-heranca', 'stj_resp_1878651',
             'O REsp 1.878.651 proibiu a sucessão de qualquer milha.'),
        )
        for intent, kind, false_claim in cases:
            sources = current_sources(intent)
            index = [candidate for candidate, _ in
                     auditor.AEREO06_SOURCE_REQUIREMENTS[intent]].index(kind)
            sources[index]['anchor_claim'] += ' ' + false_claim
            code, _ = anchor_rule(intent, kind)
            with self.subTest(intent=intent, kind=kind):
                self.assertIn(
                    'current_legal_fact_source_anchor_missing:' + code,
                    direct_reasons(page(intent, sources=sources)))

    def test_each_of_the_76_outcome_groups_is_individually_required(self):
        count = 0
        for intent, (code, groups) in auditor.AEREO06_OUTCOME_RULES.items():
            texts = [sentence(group[0]) for group in groups]
            for omitted in range(len(groups)):
                count += 1
                visible = ' '.join(texts[:omitted] + texts[omitted + 1:])
                if intent == 'aer-conta-milhas-bloqueada-fraude':
                    visible += (
                        ' A lei não garante que a revisão seja feita por uma '
                        'pessoa natural.')
                with self.subTest(intent=intent, group=omitted):
                    self.assertIn(
                        'current_legal_fact_outcome_missing:' + code,
                        direct_reasons(page(intent, visible=visible)))
        self.assertEqual(76, count)

    def test_every_outcome_group_rejects_meta_negation(self):
        prefixes = ('É falso que ', 'Não é verdade que ',
                    'É incorreto afirmar que ')
        count = 0
        for intent, (code, groups) in auditor.AEREO06_OUTCOME_RULES.items():
            for target in range(len(groups)):
                for prefix in prefixes:
                    count += 1
                    texts = []
                    for index, group in enumerate(groups):
                        value = group[0]
                        if index == target:
                            value = prefix + value
                        texts.append(sentence(value))
                    visible = ' '.join(texts)
                    if intent == 'aer-conta-milhas-bloqueada-fraude':
                        visible += (
                            ' A lei não garante que a revisão seja feita por '
                            'uma pessoa natural.')
                    with self.subTest(
                            intent=intent, group=target, prefix=prefix):
                        self.assertIn(
                            'current_legal_fact_outcome_missing:' + code,
                            direct_reasons(page(intent, visible=visible)))
        self.assertEqual(228, count)

    def test_every_stale_alternative_is_scoped_and_natural_negation_is_safe(self):
        all_intents = set(auditor.AEREO06_INTENTS)
        for code, alternatives in auditor.AEREO06_STALE_RULES:
            scope = auditor.AEREO06_STALE_RULE_INTENTS[code]
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

    def test_resp_1966032_is_forbidden_as_retroactive_credit_authority(self):
        intent = 'aer-milhas-nao-creditadas-voo'
        required_kinds = {
            kind for kind, _ in auditor.AEREO06_SOURCE_REQUIREMENTS[intent]}
        self.assertNotIn('stj_resp_1966032', required_kinds)
        sources = current_sources(intent)
        sources.append({
            'url': auditor.AEREO06_SOURCE_URLS['stj_resp_1966032'],
            'name': 'STJ',
            'anchor_claim': 'REsp 1.966.032 e Informativo 745.',
        })
        self.assertIn(
            'current_legal_fact_source_stale:'
            'stj_resp_1966032_irrelevant_to_retroactive_flight_mileage',
            direct_reasons(page(intent, sources=sources)))

    def test_stj_019461_binds_award_tickets_to_the_exact_report(self):
        intent = 'aer-milhas-falecido-heranca'
        kind = 'stj_resp_1878651_report'
        self.assertIn(
            '%40CNOT%3D%27019461%27', auditor.AEREO06_SOURCE_URLS[kind])
        self.assertIn(
            (kind, 'stj_resp_1878651_exact_report_free_personal_contract'),
            auditor.AEREO06_SOURCE_REQUIREMENTS[intent])
        _, groups = anchor_rule(intent, kind)
        self.assertIn(('pontos e passagens premio',), groups)
        _, outcomes = auditor.AEREO06_OUTCOME_RULES[intent]
        self.assertIn(
            ('a clausula examinada tambem previa o cancelamento das passagens premio emitidas',),
            outcomes)

    def test_article_27_paragraphs_two_and_three_distinctions_are_required(self):
        intent = 'aer-passagem-milhas-voo-cancelado-direitos'
        code, groups = auditor.AEREO06_OUTCOME_RULES[intent]
        required = (
            ('para pnae e acompanhantes a hospedagem e o traslado devem ser fornecidos mesmo sem pernoite',),
            ('se o passageiro escolher reacomodacao em voo proprio da transportadora em data e horario de sua conveniencia ou o reembolso integral a empresa pode suspender a assistencia material',),
        )
        for group in required:
            self.assertIn(group, groups)
            visible = ' '.join(
                sentence(alternatives[0])
                for alternatives in groups if alternatives != group)
            self.assertIn(
                'current_legal_fact_outcome_missing:' + code,
                direct_reasons(page(intent, visible=visible)))

    def test_lgpd_article_20_and_46_limits_are_required(self):
        blocked = 'aer-conta-milhas-bloqueada-fraude'
        qualifier = (
            'A lei não garante que a revisão seja feita por uma pessoa natural.')
        missing = current_visible(blocked).replace(' ' + qualifier, '')
        code, _ = auditor.AEREO06_OUTCOME_RULES[blocked]
        self.assertIn(
            'current_legal_fact_outcome_missing:' + code,
            direct_reasons(page(blocked, visible=missing)))
        meta_negated = missing + ' É falso que ' + qualifier
        self.assertIn(
            'current_legal_fact_outcome_missing:' + code,
            direct_reasons(page(blocked, visible=meta_negated)))

        fraud = 'aer-milhas-resgate-nao-reconhecido-furto'
        lgpd_code, lgpd_groups = anchor_rule(fraud, 'lgpd')
        self.assertIn(('art 46', 'artigo 46'), lgpd_groups)
        self.assertIn(('acessos nao autorizados',), lgpd_groups)
        self.assertEqual(
            'lgpd_article_46_security_against_unauthorized_access',
            lgpd_code)

    def test_article_42_requires_paid_excess_and_table_scope_is_precise(self):
        club = 'aer-clube-milhas-cancelar-assinatura'
        club_code, club_groups = auditor.AEREO06_OUTCOME_RULES[club]
        paid_excess = (
            'a repeticao em dobro do art 42 do cdc pressupoe quantia efetivamente paga em excesso',)
        self.assertIn(paid_excess, club_groups)
        visible = ' '.join(
            sentence(group[0]) for group in club_groups
            if group != paid_excess)
        self.assertIn(
            'current_legal_fact_outcome_missing:' + club_code,
            direct_reasons(page(club, visible=visible)))

        table = 'aer-programa-mudou-tabela-resgate'
        table_code, table_groups = auditor.AEREO06_OUTCOME_RULES[table]
        distinctions = (
            'uma simulacao sem reserva uma oferta com prazo um pagamento iniciado e um bilhete emitido produzem graus diferentes de confianca e prova',)
        issued = (
            'o programa nao deve exigir pontos extras apenas porque a tabela mudou depois',)
        self.assertIn(distinctions, table_groups)
        self.assertIn(issued, table_groups)
        for group in (distinctions, issued):
            visible = ' '.join(
                sentence(item[0]) for item in table_groups if item != group)
            self.assertIn(
                'current_legal_fact_outcome_missing:' + table_code,
                direct_reasons(page(table, visible=visible)))

    def test_central_dispatcher_executes_aereo06_and_unknown_intent_is_ignored(self):
        intent = 'aer-milhas-nao-creditadas-voo'
        record = page(intent)
        record['official_sources'] = record['official_sources'][1:]
        self.assertIn(
            'current_legal_fact_source_missing:'
            'cdc_precise_mileage_offer_enforcement',
            auditor.current_legal_fact_reasons(record, evaluation_date=CURRENT))
        self.assertEqual([], auditor.current_aereo06_legal_fact_reasons(
            {}, 'aer-outro-shard', 'Fato qualquer.', CURRENT))


if __name__ == '__main__':
    unittest.main()
