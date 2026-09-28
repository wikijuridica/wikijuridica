#!/usr/bin/env python3
"""Current-law regressions for the seven critical tributario-12 intents."""

import unittest

from tools import audit_v2_pages as auditor


RFB_DEADLINE = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'orientacao-tributaria/julgamento-administrativo/prazos-de-impugnacao')
LC_227 = (
    'https://www2.camara.leg.br/legin/fed/leicom/2026/'
    'leicomplementar-227-13-janeiro-2026-798657-normaatualizada-pl.html')
LAW_9430 = 'https://www.planalto.gov.br/ccivil_03/leis/l9430.htm'
RFB_WHO = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/quem/quem')
RFB_CHANGES = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/novidades/2026')
RFB_TABLE = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/tabelas/2026')
RFB_LOTS = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/restituicao/lotes/2026')
RFB_UNCLAIMED = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'orientacao-tributaria/restituicao-ressarcimento-reembolso-e-'
    'compensacao/creditos/retencao/beneficiario/pf/irpf/'
    'restituicao-nao-resgatada')
MEDICAL_DEADLINE = (
    'https://normasinternet2.receita.fazenda.gov.br/api/'
    'consulta-externa/ato/146385/visao/multivigente')
MEDICAL_SCOPE = (
    'https://normasinternet2.receita.fazenda.gov.br/api/'
    'consulta-externa/ato/142017/visao/multivigente')
MEDICAL_AUDIT = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/malha-fiscal/antecipacao/despesas-medicas')
LAW_9250 = 'https://www.planalto.gov.br/ccivil_03/leis/l9250.htm'
ESOCIAL = (
    'https://www.gov.br/esocial/pt-br/noticias/substituicao-da-dirf-pgd-'
    'por-eventos-do-esocial-comeca-no-periodo-de-apuracao-01-2025')
EFD_REINF = (
    'https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/'
    'perguntas-frequentes/sped/efd-reinf/efdr/1-geral/'
    '1-17-as-informacoes-sobre')
PERGUNTAO = (
    'https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/'
    'publicacoes/perguntas-e-respostas/dirpf/'
    'p-r-irpf-2026-v1-00-2026-04-23.pdf')
PGFN_DISEASE = (
    'https://www.gov.br/pgfn/pt-br/cidadania-tributaria/por-assunto/'
    'imposto-de-renda-pessoa-fisica-irpf-2/isencao-por-molestia-grave')
PGFN_OPINION = (
    'https://www.gov.br/pgfn/pt-br/assuntos/representacao-judicial/'
    'lista-dispensa-contestar-recorrer/'
    'parecer-sei-no-212-2025-redlit.pdf')
RFB_NO_GAIN = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/pagamento/ganhos-de-capital/'
    'operacoes-nao-sujeitas')
PGFN_GAIN = (
    'https://www.gov.br/pgfn/pt-br/cidadania-tributaria/por-assunto/'
    'imposto-de-renda-pessoa-fisica-irpf-2/ganho-capital')

NOTICE = (
    'A Lei Complementar 227/2026, em seu art. 173, fixou vinte dias úteis '
    'para a impugnação. O ADI RFB 2/2026 alcança intimações até 31 de março '
    'de 2026: compare vinte dias úteis e trinta dias corridos e use o que '
    'vencer por último. Não confunda o prazo processual de defesa com os '
    'trinta dias corridos ainda previstos em lei específica para certas '
    'reduções por pagamento ou parcelamento. A multa ordinária de ofício é '
    'de 75%. A Lei 9.430/1996 prevê 100% quando presentes sonegação, fraude '
    'ou conluio. O percentual de 150% depende de reincidência na conduta '
    'qualificada. A autoridade deve motivar o enquadramento; não basta '
    'chamar qualquer omissão de fraudulenta.')

FILING = (
    'A DIRPF 2026 retrata o ano-calendário 2025. Rendimentos tributáveis '
    'acima de R$ 35.584 obrigam a entrega. Rendimentos isentos, não '
    'tributáveis ou tributados exclusivamente na fonte acima de R$ 200 mil '
    'formam hipótese distinta. Receita bruta rural acima de R$ 177.920 e '
    'bens ou direitos acima de R$ 800 mil também obrigam. Na bolsa, a soma '
    'superou R$ 40 mil no ano ou houve ganho líquido sujeito ao imposto. A '
    'tabela de redução mensal vigente desde janeiro de 2026 afeta '
    'rendimentos do ano-calendário 2026, não os fatos de 2025.')

REFUND = (
    'O calendário regular de 2026 tem quatro lotes: 29 de maio, 30 de '
    'junho, 31 de julho e 31 de agosto. No Banco do Brasil, o valor fica '
    'disponível para reagendamento por um ano. Passado um ano sem resgate, '
    'o banco devolve o valor à Receita. O pedido administrativo observa '
    'cinco anos contados da primeira disponibilização na rede bancária.')

MEDICAL = (
    'Desde 1º de janeiro de 2025, médico, dentista, psicólogo, '
    'fisioterapeuta, fonoaudiólogo e terapeuta ocupacional, quando atendem '
    'como pessoa física, emitem Receita Saúde. A emissão extemporânea '
    'termina no último dia do mês de fevereiro do ano seguinte. Para '
    'pagamentos de 2025, a '
    'emissão retroativa terminou em 28 de fevereiro de 2026 e dependia de '
    'não ter começado procedimento de ofício. O recibo não cria presunção '
    'absoluta. Clínica, hospital ou consultório constituído como pessoa '
    'jurídica não emite Receita Saúde.')

WITHHOLDING = (
    'Nos fatos ocorridos em 2025, usados na DIRPF 2026, mudou a '
    'escrituração. A partir do período de apuração janeiro de 2025, eventos '
    'do eSocial substituem a DIRF para relações de trabalho. Pagamentos sem '
    'relação de trabalho a pessoa física aparecem no evento correspondente '
    'da EFD-Reinf. Para fatos anteriores a 2025, o canal histórico pode ser '
    'diferente; não aplique a substituição retroativamente a exercícios que '
    'ainda usavam DIRF.')

SEVERE_DISEASE = (
    'A moléstia grave deve pertencer ao rol legal e o beneficiário precisa '
    'estar aposentado pela Previdência Oficial. A doença e o plano privado, '
    'sozinhos, não bastam. A Receita reconhece a complementação paga por '
    'entidade de previdência complementar, Fapi e PGBL. O entendimento '
    'atual também alcança o VGBL. A PGFN registra a isenção do resgate de '
    'complementação. O pecúlio antecipado ao próprio participante, quando '
    'não equivale a aposentadoria, fica fora.')

CAPITAL_GAIN = (
    'Na venda à vista, o DARF vence no último dia útil do mês seguinte ao '
    'da alienação. Na venda a prazo, o ganho é apropriado proporcionalmente '
    'a cada parcela e o imposto vence no último dia útil do mês seguinte ao '
    'respectivo recebimento. A isenção do único imóvel de até R$ 440 mil '
    'exige que não haja outra alienação de imóvel, a qualquer título, '
    'tributada ou não, nos cinco anos anteriores. A jurisprudência admite '
    'usar o produto para quitar financiamento de imóvel '
    'residencial já adquirido.')


def page(intent, visible, sources):
    return {
        'intent_id': intent,
        'opening': visible,
        'official_sources': [{'url': source} for source in sources],
    }


FIXTURES = (
    ('trib-irpf-notificacao-lancamento-multa', NOTICE,
     (RFB_DEADLINE, LC_227, LAW_9430),
     ('rfb_2026_federal_impugnation_deadline',
      'lc_227_2026_article_173', 'law_9430_article_44_penalty_rates'),
     'irpf_launch_notice_twenty_business_days_transition_and_'
     'penalty_qualification'),
    ('trib-irpf-quem-e-obrigado-declarar', FILING,
     (RFB_WHO, RFB_CHANGES, RFB_TABLE),
     ('rfb_irpf_2026_who_must_file', 'rfb_irpf_2026_changes',
      'rfb_2026_monthly_table_context'),
     'irpf_2026_calendar_2025_thresholds_and_stock_exchange_boundary'),
    ('trib-irpf-restituicao-nao-caiu', REFUND,
     (RFB_LOTS, RFB_UNCLAIMED),
     ('rfb_irpf_2026_four_refund_batches',
      'rfb_unclaimed_refund_one_and_five_years'),
     'irpf_2026_four_refund_batches_and_one_five_year_rescue_windows'),
    ('trib-irpf-malha-despesas-medicas', MEDICAL,
     (MEDICAL_DEADLINE, MEDICAL_SCOPE, MEDICAL_AUDIT, LAW_9250),
     ('ade_cofis_11_2025_receita_saude_deadline',
      'in_rfb_2240_2024_receita_saude_scope',
      'rfb_medical_expense_audit_documents',
      'law_9250_article_8_medical_deduction'),
     'receita_saude_2025_six_individual_professions_cutoff_and_'
     'evidentiary_boundary'),
    ('trib-irpf-informe-rendimentos-errado', WITHHOLDING,
     (ESOCIAL, EFD_REINF),
     ('esocial_dirf_replacement_january_2025',
      'rfb_efd_reinf_nonemployment_payments'),
     'dirf_replacement_2025_esocial_work_and_efd_reinf_nonemployment'),
    ('trib-irpf-isencao-doenca-previdencia-privada', SEVERE_DISEASE,
     (PERGUNTAO, PGFN_DISEASE, PGFN_OPINION),
     ('rfb_irpf_2026_private_pension_severe_disease',
      'pgfn_severe_disease_private_pension_rescue',
      'pgfn_opinion_212_2025_vgbl_peculio'),
     'severe_disease_private_pension_official_retirement_rescue_and_'
     'peculio_boundaries'),
    ('trib-irpf-ganho-capital-venda-imovel', CAPITAL_GAIN,
     (PERGUNTAO, RFB_NO_GAIN, PGFN_GAIN),
     ('rfb_irpf_2026_installment_and_single_property_rules',
      'rfb_real_estate_capital_gain_exemptions',
      'pgfn_prior_residential_financing_payoff'),
     'real_estate_capital_gain_cash_installments_single_property_and_'
     'prior_financing'),
)


class Tributario12CurrentLawTest(unittest.TestCase):

    def test_accepts_current_rules(self):
        for intent, visible, sources, _, _ in FIXTURES:
            with self.subTest(intent=intent):
                self.assertEqual([], auditor.current_legal_fact_reasons(
                    page(intent, visible, sources)))

    def test_requires_no_prior_alienation(self):
        correct = (
            'A isenção do único imóvel de até R$ 440 mil exige que não haja '
            'outra alienação de imóvel, a qualquer título, tributada ou não, '
            'nos cinco anos anteriores.')
        equivalent = (
            'A isenção do único imóvel de até R$ 440 mil exige que não tenha '
            'realizado outra alienação de imóvel, a qualquer título, '
            'tributada ou não, nos cinco anos anteriores.')
        contradictory = (
            'A isenção do único imóvel de até R$ 440 mil foi examinada. A '
            'pessoa realizou outra alienação de imóvel, a qualquer título, '
            'tributada ou não, nos cinco anos anteriores.')
        self.assertIn(correct, CAPITAL_GAIN)
        equivalent_visible = CAPITAL_GAIN.replace(correct, equivalent, 1)
        self.assertEqual([], auditor.current_legal_fact_reasons(page(
            'trib-irpf-ganho-capital-venda-imovel', equivalent_visible,
            (PERGUNTAO, RFB_NO_GAIN, PGFN_GAIN))))
        visible = CAPITAL_GAIN.replace(correct, contradictory, 1)
        reasons = auditor.current_legal_fact_reasons(page(
            'trib-irpf-ganho-capital-venda-imovel', visible,
            (PERGUNTAO, RFB_NO_GAIN, PGFN_GAIN)))
        self.assertIn(
            'current_legal_fact_outcome_missing:'
            'real_estate_capital_gain_cash_installments_single_property_and_'
            'prior_financing', reasons)

    def test_rejects_generic_refund_schedule(self):
        reasons = auditor.current_legal_fact_reasons(page(
            'trib-irpf-restituicao-nao-caiu', REFUND,
            (RFB_LOTS.removesuffix('/2026'), RFB_UNCLAIMED)))
        self.assertIn(
            'current_legal_fact_source_missing:'
            'rfb_irpf_2026_four_refund_batches', reasons)

    def test_treats_nem_as_local_negation(self):
        self.assertEqual([], auditor.current_legal_fact_reasons(page(
            'trib-irpf-isencao-doenca-previdencia-privada',
            SEVERE_DISEASE +
            ' Nem o plano privado substitui a aposentadoria oficial.',
            (PERGUNTAO, PGFN_DISEASE, PGFN_OPINION))))

    def test_requires_every_canonical_source(self):
        for intent, visible, sources, codes, _ in FIXTURES:
            for index, code in enumerate(codes):
                with self.subTest(intent=intent, code=code):
                    spoofed = list(sources)
                    spoofed[index] = 'https://example.com/?source=' + sources[index]
                    reasons = auditor.current_legal_fact_reasons(
                        page(intent, visible, spoofed))
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code, reasons)

    def test_rejects_noncanonical_source_identity(self):
        bad_urls = (
            RFB_DEADLINE.replace('https://',
                                 'https://attacker@', 1),
            RFB_DEADLINE.replace('www.gov.br', 'www.gov.br:444', 1),
            RFB_DEADLINE + '#prazo',
            RFB_DEADLINE + '?utm_source=decoy',
            RFB_DEADLINE.replace('prazos-de-impugnacao',
                                 '%70razos-de-impugnacao'),
            'https://www.gov.br/decoy?source=/receitafederal/pt-br/'
            'assuntos/orientacao-tributaria/julgamento-administrativo/'
            'prazos-de-impugnacao',
            RFB_DEADLINE.replace('https://', 'http://', 1),
        )
        for bad_url in bad_urls:
            with self.subTest(bad_url=bad_url):
                sources = [bad_url, LC_227, LAW_9430]
                reasons = auditor.current_legal_fact_reasons(page(
                    'trib-irpf-notificacao-lancamento-multa',
                    NOTICE, sources))
                self.assertIn(
                    'current_legal_fact_source_missing:'
                    'rfb_2026_federal_impugnation_deadline', reasons)

    def test_rejects_outcome_omissions(self):
        cases = (
            ('trib-irpf-notificacao-lancamento-multa',
             NOTICE.replace(
                 'Não confunda o prazo processual de defesa com os trinta '
                 'dias corridos ainda previstos em lei específica para '
                 'certas reduções por pagamento ou parcelamento. ', '', 1),
             (RFB_DEADLINE, LC_227, LAW_9430),
             FIXTURES[0][4]),
            ('trib-irpf-quem-e-obrigado-declarar',
             FILING.replace('Receita bruta rural acima de R$ 177.920 e ',
                            '', 1),
             (RFB_WHO, RFB_CHANGES, RFB_TABLE), FIXTURES[1][4]),
            ('trib-irpf-restituicao-nao-caiu',
             REFUND.replace(' e 31 de agosto', '', 1),
             (RFB_LOTS, RFB_UNCLAIMED), FIXTURES[2][4]),
            ('trib-irpf-malha-despesas-medicas',
             MEDICAL.replace('fonoaudiólogo e ', '', 1),
             (MEDICAL_DEADLINE, MEDICAL_SCOPE, MEDICAL_AUDIT, LAW_9250),
             FIXTURES[3][4]),
            ('trib-irpf-malha-despesas-medicas',
             MEDICAL.replace(
                 'A emissão extemporânea termina no último dia do mês de '
                 'fevereiro do ano seguinte. ', '', 1),
             (MEDICAL_DEADLINE, MEDICAL_SCOPE, MEDICAL_AUDIT, LAW_9250),
             FIXTURES[3][4]),
            ('trib-irpf-informe-rendimentos-errado',
             WITHHOLDING.replace(
                 'Pagamentos sem relação de trabalho a pessoa física '
                 'aparecem no evento correspondente da EFD-Reinf. ', '', 1),
             (ESOCIAL, EFD_REINF), FIXTURES[4][4]),
            ('trib-irpf-isencao-doenca-previdencia-privada',
             SEVERE_DISEASE.replace(
                 'e o beneficiário precisa estar aposentado pela '
                 'Previdência Oficial', '', 1),
             (PERGUNTAO, PGFN_DISEASE, PGFN_OPINION), FIXTURES[5][4]),
            ('trib-irpf-ganho-capital-venda-imovel',
             CAPITAL_GAIN.replace(
                 'e o imposto vence no último dia útil do mês seguinte ao '
                 'respectivo recebimento', '', 1),
             (PERGUNTAO, RFB_NO_GAIN, PGFN_GAIN), FIXTURES[6][4]),
        )
        for intent, visible, sources, outcome in cases:
            with self.subTest(intent=intent):
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + outcome,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible, sources)))

    def test_rejects_questions_and_meta_negations(self):
        cases = (
            (FIXTURES[0],
             'A LC 227/2026 fixou vinte dias úteis? O ADI RFB 2/2026 '
             'criou a transição? As multas são 75%, 100% e 150%?'),
            (FIXTURES[1],
             'A DIRPF 2026 usa R$ 35.584, R$ 200 mil, R$ 177.920, '
             'R$ 800 mil e R$ 40 mil? Ganho tributável também obriga?'),
            (FIXTURES[2],
             'Não é verdade que o calendário de 2026 tenha quatro lotes '
             'em 29 de maio, 30 de junho, 31 de julho e 31 de agosto. Não '
             'se pode afirmar que o BB retenha por um ano ou que o prazo '
             'seja de cinco anos da primeira disponibilização.'),
            (FIXTURES[3],
             'Não é correto afirmar que desde 2025 os seis profissionais '
             'pessoa física usem Receita Saúde. É falso que o prazo '
             'retroativo tenha terminado em 28 de fevereiro de 2026 e que '
             'o recibo não crie presunção absoluta.'),
            (FIXTURES[4],
             'Para fatos de 2025, o eSocial substitui a DIRF nas relações '
             'de trabalho? A EFD-Reinf recebe pagamentos sem relação de '
             'trabalho? A regra não retroage?'),
            (FIXTURES[5],
             'Moléstia grave com aposentadoria oficial alcança Fapi, PGBL '
             'e VGBL? O resgate pode ser isento? O pecúlio antecipado fica '
             'fora?'),
            (FIXTURES[6],
             'Não é verdade que venda à vista vença no mês seguinte à '
             'alienação e venda a prazo acompanhe cada recebimento. É '
             'falso que qualquer alienação conte nos cinco anos ou que a '
             'quitação de financiamento anterior seja admitida.'),
        )
        for fixture, visible in cases:
            intent, _, sources, _, outcome = fixture
            with self.subTest(intent=intent):
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + outcome,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible, sources)))

    def test_rejects_stale_contradictions(self):
        cases = (
            (FIXTURES[0],
             ' O prazo vigente para impugnar é de trinta dias corridos.',
             'irpf_launch_notice_old_deadline_or_unqualified_penalty'),
            (FIXTURES[0],
             ' O prazo aplicável para impugnação permanece em trinta dias '
             'corridos.',
             'irpf_launch_notice_old_deadline_or_unqualified_penalty'),
            (FIXTURES[0], ' Qualquer erro aplica multa de 100%.',
             'irpf_launch_notice_old_deadline_or_unqualified_penalty'),
            (FIXTURES[1],
             ' O limite de rendimentos tributáveis da DIRPF 2026 é '
             'R$ 33.888.',
             'irpf_2026_old_threshold_or_monthly_table_confusion'),
            (FIXTURES[1],
             ' O teto dos rendimentos tributáveis permanece em R$ 33.888.',
             'irpf_2026_old_threshold_or_monthly_table_confusion'),
            (FIXTURES[1],
             ' Vendas abaixo de R$ 40 mil nunca obrigam a declarar.',
             'irpf_2026_old_threshold_or_monthly_table_confusion'),
            (FIXTURES[2],
             ' O calendário regular de 2026 tem cinco lotes.',
             'irpf_2026_refund_batch_or_rescue_window'),
            (FIXTURES[2],
             ' O calendário inclui um quinto lote regular em setembro de '
             '2026.',
             'irpf_2026_refund_batch_or_rescue_window'),
            (FIXTURES[2],
             ' O quarto lote é em 28 de agosto de 2026.',
             'irpf_2026_refund_batch_or_rescue_window'),
            (FIXTURES[2],
             ' Os cinco anos contam da devolução do valor à Receita.',
             'irpf_2026_refund_batch_or_rescue_window'),
            (FIXTURES[3],
             ' Prestador pessoa jurídica deve emitir Receita Saúde.',
             'receita_saude_scope_cutoff_or_absolute_presumption'),
            (FIXTURES[3],
             ' As pessoas jurídicas também precisam emitir Receita Saúde.',
             'receita_saude_scope_cutoff_or_absolute_presumption'),
            (FIXTURES[3],
             ' O recibo cria presunção absoluta da despesa.',
             'receita_saude_scope_cutoff_or_absolute_presumption'),
            (FIXTURES[4],
             ' Para fatos geradores de 2025, a fonte corrige a DIRF.',
             'dirf_2025_channel_reversal_or_retroactivity'),
            (FIXTURES[4],
             ' Pagamentos ligados ao trabalho seguem a EFD-Reinf.',
             'dirf_2025_channel_reversal_or_retroactivity'),
            (FIXTURES[4],
             ' Rendimentos do trabalho devem ser escriturados pela '
             'EFD-Reinf.',
             'dirf_2025_channel_reversal_or_retroactivity'),
            (FIXTURES[5],
             ' A aposentadoria pela Previdência Oficial não é necessária.',
             'severe_disease_private_pension_without_official_retirement_'
             'or_peculio_boundary'),
            (FIXTURES[5],
             ' Não se exige vínculo de aposentadoria com a Previdência '
             'Oficial.',
             'severe_disease_private_pension_without_official_retirement_'
             'or_peculio_boundary'),
            ((FIXTURES[5][0],
              FIXTURES[5][1] +
              ' Nem o plano privado substitui a aposentadoria oficial.',
              FIXTURES[5][2], FIXTURES[5][3], FIXTURES[5][4]),
             ' O plano privado substitui a aposentadoria oficial.',
             'severe_disease_private_pension_without_official_retirement_'
             'or_peculio_boundary'),
            (FIXTURES[5],
             ' Todo pecúlio de previdência privada é isento.',
             'severe_disease_private_pension_without_official_retirement_'
             'or_peculio_boundary'),
            (FIXTURES[6],
             ' Na venda parcelada, todo o DARF vence no mês seguinte à '
             'alienação.',
             'capital_gain_installment_single_property_or_prior_'
             'financing_boundary'),
            (FIXTURES[6],
             ' Alienação não tributada não conta nos cinco anos.',
             'capital_gain_installment_single_property_or_prior_'
             'financing_boundary'),
            (FIXTURES[6],
             ' Uma transferência gratuita do imóvel não interfere no '
             'quinquênio.',
             'capital_gain_installment_single_property_or_prior_'
             'financing_boundary'),
            (FIXTURES[6],
             ' Quitação de financiamento de imóvel residencial já '
             'adquirido nunca admite a isenção dos 180 dias.',
             'capital_gain_installment_single_property_or_prior_'
             'financing_boundary'),
        )
        for fixture, addition, stale_code in cases:
            intent, visible, sources, _, _ = fixture
            with self.subTest(intent=intent, addition=addition):
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + stale_code,
                    auditor.current_legal_fact_reasons(
                        page(intent, visible + addition, sources)))


if __name__ == '__main__':
    unittest.main()
