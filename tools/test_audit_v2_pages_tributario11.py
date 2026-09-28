#!/usr/bin/env python3
"""Current-law regressions for the two critical tributario-11 intents."""

import unittest

from tools import audit_v2_pages as auditor


ADI_STF = 'https://portal.stf.jus.br/processos/detalhe.asp?incidente=4357242'
TEMA_736_STF = (
    'https://portal.stf.jus.br/jurisprudenciaRepercussao/'
    'verAndamentoProcesso.asp?classeProcesso=RE&incidente=4531713&'
    'numeroProcesso=796939&numeroTema=736')
RFB_JURISPRUDENCE = (
    'https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/'
    'legislacao/jurisprudencia-vinculante/'
    'normas-gerais-de-direito-tributario')
LAW_9430 = 'https://www.planalto.gov.br/ccivil_03/leis/l9430compilada.htm'
DECREE_2138 = 'https://www.planalto.gov.br/ccivil_03/decreto/d2138.htm'
TEMA_874_STF = (
    'https://portal.stf.jus.br/jurisprudenciaRepercussao/'
    'verAndamentoProcesso.asp?classeProcesso=RE&incidente=4852220&'
    'numeroProcesso=917285&numeroTema=874')
TEMA_484_STJ = (
    'https://processo.stj.jus.br/repetitivos/temas_repetitivos/'
    'pesquisa.jsp?cod_tema_final=484&cod_tema_inicial=484&'
    'novaConsulta=true&tipo_pesquisa=T')
RFB_OFFICE = (
    'https://www.gov.br/pt-br/servicos/'
    'autorizar-ou-discordar-da-compensacao-de-oficio-da-receita-federal')
RFB_OFFICE_FAQ = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'orientacao-tributaria/restituicao-ressarcimento-reembolso-e-compensacao/'
    'perguntas-e-respostas/compensacao-de-oficio')

ADI_TEXT = (
    'A multa isolada de cinquenta por cento não incide automaticamente. '
    'O § 17 do art. 74 da Lei 9.430/1996 ainda aparece formalmente no '
    'texto compilado, acompanhado da anotação sobre a ADI 4.905. Não é '
    'correto dizer que o Congresso o revogou. O que impede sua aplicação '
    'à mera não homologação é a declaração de inconstitucionalidade. A '
    'decisão não concede imunidade a informação falsa, fraude, conluio ou '
    'uso consciente de crédito inexistente. Esses fatos podem atrair '
    'penalidades por outros fundamentos. Compensação considerada não '
    'declarada também tem disciplina própria e não deve ser tratada como '
    'simples não homologação.')

OFFICE_PARTS = (
    'O art. 73 da Lei 9.430/1996 manda verificar débitos antes da '
    'restituição federal. O art. 6º do Decreto 2.138/1997 disciplina a '
    'manifestação. O STJ, no Tema 484, reconheceu a compensação de ofício '
    'fora das hipóteses de suspensão da exigibilidade. ',
    'O art. 6º do Decreto 2.138/1997 estabelece que o contribuinte seja '
    'comunicado e se manifeste em quinze dias. ',
    'Concordar autoriza a compensação; não responder no prazo é tratado '
    'como aquiescência e também permite a operação. ',
    'A discordância impede essa conclusão automática, mas a restituição '
    'pode permanecer retida enquanto o débito exigível não for '
    'regularizado. ',
    'Débito com exigibilidade suspensa não pode ser compensado de ofício, ',
    'e o Tema 874 declarou inconstitucional a expressão parcelados sem '
    'garantia que pretendia alcançar parcelamentos no art. 73 da Lei '
    '9.430/1996.')
OFFICE_TEXT = ''.join(OFFICE_PARTS)


def page(intent, visible, sources):
    return {
        'intent_id': intent,
        'opening': visible,
        'official_sources': [{'url': source} for source in sources],
    }


def adi_sources(stf=ADI_STF):
    return [stf, RFB_JURISPRUDENCE, LAW_9430]


def office_sources(rfb=RFB_OFFICE):
    return [LAW_9430, DECREE_2138, TEMA_874_STF, TEMA_484_STJ, rfb]


class Tributario11CurrentLawTest(unittest.TestCase):

    def test_adi_accepts_canonical_adi_or_joint_tema_736(self):
        for stf in (ADI_STF, TEMA_736_STF):
            with self.subTest(stf=stf):
                self.assertEqual([], auditor.current_legal_fact_reasons(page(
                    'trib-perdcomp-multa-isolada-50', ADI_TEXT,
                    adi_sources(stf))))

    def test_adi_accepts_numeric_percentage(self):
        for rate in ('50%', '50 por cento'):
            visible_forms = (
                ADI_TEXT.replace('cinquenta por cento', rate, 1),
                ADI_TEXT.replace(
                    'A multa isolada de cinquenta por cento não incide '
                    'automaticamente.',
                    'Não pode ser aplicada multa isolada de ' + rate +
                    ' apenas porque a DCOMP foi não homologada.', 1),
            )
            for visible in visible_forms:
                with self.subTest(rate=rate, visible=visible[:40]):
                    self.assertEqual(
                        [], auditor.current_legal_fact_reasons(page(
                            'trib-perdcomp-multa-isolada-50', visible,
                            adi_sources())))

    def test_adi_rejects_spoofed_sources(self):
        cases = (
            ('adi', 0, ADI_STF,
             'stf_adi_4905_isolated_compensation_penalty'),
            ('tema_736', 0, TEMA_736_STF,
             'stf_adi_4905_isolated_compensation_penalty'),
            ('rfb', 1, ADI_STF, 'rfb_binding_jurisprudence_adi_4905'),
            ('law', 2, ADI_STF, 'law_9430_article_74_paragraph_17'),
        )
        for name, index, stf, code in cases:
            with self.subTest(name=name):
                sources = adi_sources(stf)
                sources[index] = 'https://example.com/?source=' + sources[index]
                reasons = auditor.current_legal_fact_reasons(page(
                    'trib-perdcomp-multa-isolada-50', ADI_TEXT, sources))
                self.assertIn('current_legal_fact_source_missing:' + code,
                              reasons)

    def test_adi_rejects_questions_negations_missing_exceptions_and_stale(self):
        outcome = (
            'current_legal_fact_outcome_missing:'
            'adi_4905_paragraph_17_formal_text_'
            'unconstitutionality_and_exceptions')
        false_greens = (
            'A ADI 4.905 declarou o § 17 do art. 74 inconstitucional? O '
            'dispositivo continua formalmente no texto? Fraude, falsidade '
            'e DCOMP não declarada ficaram fora da decisão?',
            'Não é verdade que, na ADI 4.905, o § 17 do art. 74 continue '
            'formalmente no texto e tenha sido declarado inconstitucional. '
            'Não é correto afirmar que fraude, falsidade e DCOMP não '
            'declarada tenham disciplina própria.',
            'Na ADI 4.905, o § 17 do art. 74 ainda aparece formalmente no '
            'texto compilado e foi declarado inconstitucional. A multa não '
            'incide pela mera não homologação.',
            ADI_TEXT.replace(
                'A multa isolada de cinquenta por cento não incide '
                'automaticamente. ', '', 1),
            ADI_TEXT.replace('cinquenta por cento', '50 reais', 1),
            ADI_TEXT.replace(
                'A decisão não concede imunidade',
                'É falso: a decisão não concede imunidade', 1),
            ADI_TEXT.replace(
                'Compensação considerada não declarada',
                'É falso: compensação considerada não declarada', 1),
        )
        for visible in false_greens:
            with self.subTest(visible=visible[:30]):
                self.assertIn(outcome, auditor.current_legal_fact_reasons(
                    page('trib-perdcomp-multa-isolada-50', visible,
                         adi_sources())))
        stale = (
            'current_legal_fact_stale_assertion:'
            'adi_4905_paragraph_17_revoked_or_automatic_penalty')
        for addition in (' O § 17 foi revogado.',
                         ' A multa incide pela mera não homologação.'):
            self.assertIn(stale, auditor.current_legal_fact_reasons(page(
                'trib-perdcomp-multa-isolada-50', ADI_TEXT + addition,
                adi_sources())))

    def test_preserves_affirmative_double_negation(self):
        visible = ADI_TEXT.replace(
            'A decisão não concede imunidade',
            'Não é falso que a decisão não concede imunidade', 1)
        self.assertEqual([], auditor.current_legal_fact_reasons(page(
            'trib-perdcomp-multa-isolada-50', visible, adi_sources())))

    def test_office_accepts_real_text_and_both_rfb_routes(self):
        for rfb in (RFB_OFFICE, RFB_OFFICE_FAQ):
            with self.subTest(rfb=rfb):
                self.assertEqual([], auditor.current_legal_fact_reasons(page(
                    'trib-compensacao-oficio-restituicao-retida',
                    OFFICE_TEXT, office_sources(rfb))))

    def test_office_rejects_spoofed_sources(self):
        codes = (
            'law_9430_article_73_compensation_office',
            'decree_2138_article_6_compensation_office',
            'stf_tema_874_compensation_office',
            'stj_tema_484_compensation_office',
            'rfb_compensation_office_procedure',
        )
        for index, code in enumerate(codes):
            with self.subTest(code=code):
                sources = office_sources()
                sources[index] = 'https://example.com/?source=' + sources[index]
                reasons = auditor.current_legal_fact_reasons(page(
                    'trib-compensacao-oficio-restituicao-retida',
                    OFFICE_TEXT, sources))
                self.assertIn('current_legal_fact_source_missing:' + code,
                              reasons)

    def test_rejects_noncanonical_source_identities(self):
        cases = (
            ('planalto_userinfo', False, 2,
             'https://attacker@www.planalto.gov.br/ccivil_03/leis/'
             'l9430compilada.htm', 'law_9430_article_74_paragraph_17'),
            ('planalto_port', False, 2,
             'https://www.planalto.gov.br:444/ccivil_03/leis/'
             'l9430compilada.htm', 'law_9430_article_74_paragraph_17'),
            ('planalto_query_decoy', False, 2,
             'https://www.planalto.gov.br/ccivil_03/leis/decoy.htm?'
             'source=l9430compilada.htm',
             'law_9430_article_74_paragraph_17'),
            ('planalto_fragment_decoy', False, 2,
             'https://www.planalto.gov.br/ccivil_03/leis/decoy.htm#'
             'l9430compilada.htm', 'law_9430_article_74_paragraph_17'),
            ('planalto_fragment', False, 2, LAW_9430 + '#art74',
             'law_9430_article_74_paragraph_17'),
            ('planalto_encoded_path', False, 2,
             'https://www.planalto.gov.br/ccivil_03/leis/'
             '%6c9430compilada.htm', 'law_9430_article_74_paragraph_17'),
            ('planalto_malformed_ipv6', False, 2,
             'https://[bad/path',
             'law_9430_article_74_paragraph_17'),
            ('stf_fragment', False, 0, ADI_STF + '#adi4905',
             'stf_adi_4905_isolated_compensation_penalty'),
            ('rfb_fragment', False, 1, RFB_JURISPRUDENCE + '#adi4905',
             'rfb_binding_jurisprudence_adi_4905'),
            ('stj_userinfo', True, 3,
             TEMA_484_STJ.replace('https://', 'https://attacker@', 1),
             'stj_tema_484_compensation_office'),
            ('stj_port', True, 3,
             TEMA_484_STJ.replace('stj.jus.br', 'stj.jus.br:444', 1),
             'stj_tema_484_compensation_office'),
            ('stj_query_decoy', True, 3,
             'https://processo.stj.jus.br/decoy?source=/repetitivos/'
             'temas_repetitivos/pesquisa.jsp&cod_tema_final=484',
             'stj_tema_484_compensation_office'),
            ('stj_fragment', True, 3, TEMA_484_STJ + '#tema484',
             'stj_tema_484_compensation_office'),
            ('stj_duplicate_case', True, 3,
             TEMA_484_STJ + '&COD_TEMA_FINAL=484',
             'stj_tema_484_compensation_office'),
            ('stj_conflicting_case', True, 3,
             TEMA_484_STJ + '&COD_TEMA_FINAL=999',
             'stj_tema_484_compensation_office'),
            ('stj_extra_query', True, 3,
             TEMA_484_STJ + '&utm_source=decoy',
             'stj_tema_484_compensation_office'),
            ('stf_duplicate_query', True, 2,
             TEMA_874_STF + '&numeroTema=874',
             'stf_tema_874_compensation_office'),
        )
        for name, office, index, bad_url, code in cases:
            with self.subTest(name=name):
                intent = 'trib-compensacao-oficio-restituicao-retida' if office else 'trib-perdcomp-multa-isolada-50'
                visible = OFFICE_TEXT if office else ADI_TEXT
                sources = office_sources() if office else adi_sources()
                sources[index] = bad_url
                reasons = auditor.current_legal_fact_reasons(
                    page(intent, visible, sources))
                self.assertIn('current_legal_fact_source_missing:' + code,
                              reasons)

    def test_rejects_noncanonical_query_key_casing(self):
        sources = office_sources()
        sources[2] = (
            'https://portal.stf.jus.br/jurisprudenciaRepercussao/'
            'verAndamentoProcesso.asp?CLASSEPROCESSO=RE&INCIDENTE=4852220&'
            'NUMEROPROCESSO=917285&NUMEROTEMA=874')
        sources[3] = (
            'https://processo.stj.jus.br/repetitivos/temas_repetitivos/'
            'pesquisa.jsp?COD_TEMA_FINAL=484&COD_TEMA_INICIAL=484&'
            'NOVACONSULTA=true&TIPO_PESQUISA=T')
        reasons = auditor.current_legal_fact_reasons(page(
            'trib-compensacao-oficio-restituicao-retida',
            OFFICE_TEXT, sources))
        self.assertIn(
            'current_legal_fact_source_missing:'
            'stf_tema_874_compensation_office', reasons)
        self.assertIn(
            'current_legal_fact_source_missing:'
            'stj_tema_484_compensation_office', reasons)

    def test_accepts_explicit_https_default_port(self):
        sources = [
            'https://www.planalto.gov.br:443/ccivil_03/leis/'
            'l9430compilada.htm',
            'https://www.planalto.gov.br:443/ccivil_03/decreto/d2138.htm',
            'https://portal.stf.jus.br:443/jurisprudenciaRepercussao/'
            'verAndamentoProcesso.asp?classeProcesso=RE&incidente=4852220&'
            'numeroProcesso=917285&numeroTema=874',
            'https://processo.stj.jus.br:443/repetitivos/temas_repetitivos/'
            'pesquisa.jsp?cod_tema_final=484&cod_tema_inicial=484&'
            'novaConsulta=true&tipo_pesquisa=T',
            'https://www.gov.br:443/pt-br/servicos/'
            'autorizar-ou-discordar-da-compensacao-de-oficio-da-receita-federal',
        ]
        self.assertEqual([], auditor.current_legal_fact_reasons(page(
            'trib-compensacao-oficio-restituicao-retida',
            OFFICE_TEXT, sources)))

    def test_office_rejects_omissions_questions_negations_and_stale(self):
        outcome = (
            'current_legal_fact_outcome_missing:'
            'compensation_office_fifteen_days_tacit_consent_'
            'retention_and_suspended_debt')
        for omitted in OFFICE_PARTS[1:]:
            self.assertIn(outcome, auditor.current_legal_fact_reasons(page(
                'trib-compensacao-oficio-restituicao-retida',
                OFFICE_TEXT.replace(omitted, '', 1), office_sources())))
        for visible in (
                'Os arts. 73 e 6 do Decreto 2.138 dão quinze dias? O '
                'silêncio gera anuência? A discordância retém? Os Temas '
                '484 e 874 excluem débito suspenso e parcelado sem garantia?',
                'Não é verdade que os arts. 73 e 6 do Decreto 2.138 deem '
                'quinze dias. Não se pode afirmar que os Temas 484 e 874 '
                'impeçam dívida suspensa ou parcelada sem garantia.',
                OFFICE_TEXT.replace(
                    'Débito com exigibilidade suspensa',
                    'É falso: débito com exigibilidade suspensa', 1),
                OFFICE_TEXT.replace(
                    'A discordância impede',
                    'É falso: a discordância impede', 1),
                OFFICE_TEXT.replace(
                    'O STJ, no Tema 484, reconheceu',
                    'É falso segundo antiga nota interna: o STJ, no Tema '
                    '484, reconheceu', 1)):
            self.assertIn(outcome, auditor.current_legal_fact_reasons(page(
                'trib-compensacao-oficio-restituicao-retida', visible,
                office_sources())))
        stale = (
            'current_legal_fact_stale_assertion:'
            'compensation_office_disagreement_release_or_'
            'suspended_installment_debt')
        for addition in (
                ' A discordância libera automaticamente a restituição.',
                ' Débito com exigibilidade suspensa pode ser compensado de ofício.',
                ' Débito parcelado sem garantia pode ser compensado de ofício.'):
            self.assertIn(stale, auditor.current_legal_fact_reasons(page(
                'trib-compensacao-oficio-restituicao-retida',
                OFFICE_TEXT + addition, office_sources())))

    def test_colon_scope_preserves_double_meta_negation_across_comma(self):
        assertion = (
            'O STJ, no Tema 484, reconheceu a compensação de ofício.')
        self.assertFalse(auditor.declarative_alternative_affirmed_in_text(
            'É falso segundo antiga nota interna: ' + assertion,
            'tema 484'))
        self.assertTrue(auditor.declarative_alternative_affirmed_in_text(
            'Não é falso: ' + assertion, 'tema 484'))


if __name__ == '__main__':
    unittest.main()
