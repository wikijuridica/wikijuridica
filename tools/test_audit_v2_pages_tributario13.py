#!/usr/bin/env python3
"""Current-law regressions for the critical tributario-13 IRPF intents."""

import unittest

from tools import audit_v2_pages as auditor


PERGUNTAO = auditor.TRIBUTARIO13_PERGUNTAO_URL
RFB_NO_GAIN = auditor.TRIBUTARIO13_RFB_NO_GAIN_URL
COSIT_128 = auditor.TRIBUTARIO13_COSIT_128_URL
LAW_9250_23 = 'https://www.planalto.gov.br/ccivil_03/leis/l9250.htm#art23'
LAW_11196_39 = (
    'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/'
    'l11196.htm#art39')
PGFN_GAIN = (
    'https://www.gov.br/pgfn/pt-br/cidadania-tributaria/por-assunto/'
    'imposto-de-renda-pessoa-fisica-irpf-2/ganho-capital')
LAW_15265_7 = (
    'https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/'
    'l15265.htm#art7')
DEAP = 'https://www.gov.br/pt-br/servicos/atualizar-valor-de-bens-moveis-e-imoveis'
RFB_SUBJECT = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/pagamento/ganhos-de-capital/'
    'operacoes-sujeitas-ao-imposto')
LAW_8981_21 = 'https://www.planalto.gov.br/ccivil_03/leis/l8981.htm#art21'
LAW_9250_22 = 'https://www.planalto.gov.br/ccivil_03/leis/l9250.htm#art22'
LAW_7713_8 = 'https://www.planalto.gov.br/ccivil_03/leis/l7713.htm#art8'
RFB_RENT = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/pagamento/carne-leao/rendimentos')
RFB_CL_MANUAL = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/pagamento/carne-leao/manual')
LAW_9430_44 = 'https://www.planalto.gov.br/ccivil_03/leis/l9430.htm#art44'
RFB_EXPENSES = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/preenchimento/manual-mir/'
    'pagamentos-ou-doacoes/despesas-dedutiveis')
RFB_IRPF_CASES = (
    'https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/'
    'legislacao/jurisprudencia-vinculante/irpf')
DIMOB_SERVICE = (
    'https://www.gov.br/pt-br/servicos/declarar-atividades-imobiliarias'
    '?id=11039&origem=servico')
DIMOB_INFO = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'orientacao-tributaria/declaracoes-e-demonstrativos/dimob/'
    'informacoes-gerais')
STF_ALIMONY = (
    'https://portal.stf.jus.br/noticias/verNoticiaDetalhe.asp'
    '?idConteudo=488372&ori=1')
RFB_ALIMONY = (
    'https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/'
    'perguntas-frequentes/imposto-de-renda/dirpf/deducoes/'
    'como-declarar-a-pensao-alimenticia')
CHAMBER_7713 = (
    'https://www2.camara.leg.br/legin/fed/lei/1988/'
    'lei-7713-22-dezembro-1988-372153-normaatualizada-pl.html')
RFB_RRA = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/preenchimento/manual-mir/rendimentos/'
    'rendimentos-do-trabalho')
RFB_ESTATE = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/preenchimento/espolio')
RFB_CHANGES = (
    'https://www.gov.br/receitafederal/pt-br/assuntos/'
    'meu-imposto-de-renda/novidades/2026')
RFB_DESKTOP = (
    'https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/'
    'download/pgd/dirpf')
LAW_9250_8 = 'https://www.planalto.gov.br/ccivil_03/leis/l9250.htm#art8'


def source(url, name='Fonte oficial', anchor='Sustenta o desfecho material.'):
    return {'url': url, 'name': name, 'anchor_claim': anchor}


def question_source(anchor):
    return source(PERGUNTAO, 'Receita Federal — Perguntão IRPF 2026', anchor)


FIXTURES = (
    (
        'trib-irpf-isencao-unico-imovel-440',
        'O art. 23 alcança a alienação do único imóvel pelo valor de '
        'alienação de até R$ 440 mil. A pessoa não pode ter feito alienação '
        'nos cinco anos anteriores, a qualquer título, tributada ou não. '
        'Doação e dação em pagamento também contam.',
        (source(LAW_9250_23), source(RFB_NO_GAIN),
         question_source('As questões 683 a 686 tratam da isenção.')),
        ('law_9250_article_23_single_property',
         'rfb_single_property_exemption',
         'rfb_irpf_2026_questions_683_686'),
        'single_property_440_any_alienation_five_year_boundary',
        'tributada ou não',
        ' Somente venda tributada reinicia os cinco anos.',
        'single_property_440_taxable_sale_only_or_purchase_cures'),
    (
        'trib-irpf-isencao-180-dias-outro-imovel',
        'O art. 39 exige imóvel residencial, aplicação do produto da venda '
        'e 180 dias. O prazo nasce da celebração do contrato de venda, não '
        'do recebimento tardio do preço. A PGFN passou a dispensar '
        'contestação e recurso quando o dinheiro serve para quitar ou '
        'amortizar aquisição a prazo ou financiamento de imóvel residencial '
        'já possuído. O benefício só pode ser usado uma vez a cada cinco anos.',
        (source(LAW_11196_39), source(RFB_NO_GAIN), source(PGFN_GAIN)),
        ('law_11196_article_39_residential_reinvestment',
         'rfb_residential_reinvestment_180_days',
         'pgfn_prior_residential_financing_payoff_180_days'),
        'residential_reinvestment_180_days_and_prior_financing_payoff',
        'A PGFN passou a dispensar contestação e recurso',
        ' O prazo de 180 dias conta do recebimento integral.',
        'residential_reinvestment_receipt_clock_or_prior_financing_denial'),
    (
        'trib-irpf-fatores-reducao-imovel-antigo',
        'A Lei 15.265/2025, no art. 7º, determina que a alienação dentro de '
        'cinco anos contados da adesão desconsidera todos os efeitos da '
        'atualização. As exceções são transmissão causa mortis e partilha '
        'decorrente de dissolução da sociedade conjugal ou união estável. O '
        'imposto já pago na atualização é deduzido do imposto da alienação, '
        'atualizado pela Selic.',
        (source(LAW_15265_7), source(DEAP)),
        ('law_15265_article_7_rearp_early_alienation',
         'rfb_live_deap_rearp_service'),
        'rearp_article_7_five_year_exceptions_and_selic_deduction',
        'atualizado pela Selic',
        ' Venda em cinco anos preserva o custo atualizado pelo Rearp.',
        'rearp_early_sale_keeps_update_or_forfeits_paid_tax'),
    (
        'trib-irpf-ganho-capital-venda-parcelada',
        'O ganho total é apurado como se a operação fosse à vista. A '
        'proporção é aplicada ao principal de cada parcela recebida. O DARF '
        'vence no último dia útil do mês seguinte ao recebimento '
        'correspondente. Parcela não recebida não gera naquele momento o '
        'mesmo imposto.',
        (question_source('As questões 668 e 669 explicam a venda parcelada.'),
         source(RFB_SUBJECT), source(LAW_8981_21)),
        ('rfb_irpf_2026_questions_668_669_installment_sale',
         'rfb_installment_capital_gain_payment',
         'law_8981_article_21_capital_gain'),
        'installment_capital_gain_proportional_receipt_due_date',
        'último dia útil do mês seguinte ao recebimento correspondente',
        ' Todo imposto vence no mês seguinte à alienação.',
        'installment_tax_due_at_sale_or_before_receipt'),
    (
        'trib-irpf-permuta-imoveis',
        'A operação é uma permuta imobiliária verdadeira. Sem recebimento '
        'de diferença em dinheiro não fica sujeita ao imposto sobre ganho '
        'de capital. Havendo torna, o programa identifica a parcela de ganho '
        'associada à torna. A tributação não corresponde simplesmente a '
        'aplicar 15% sobre todo o dinheiro recebido. A regra exige unidades '
        'imobiliárias.',
        (source(RFB_NO_GAIN),
         source(COSIT_128,
                'Receita Federal — Solução de Consulta Cosit 128/2024',
                'Delimita o ganho à torna.'),
         question_source('As questões 632 e 634 explicam a permuta imobiliária.')),
        ('rfb_real_estate_exchange_without_cash',
         'rfb_cosit_128_2024_exchange_cash_adjustment',
         'rfb_irpf_2026_questions_632_634_exchange'),
        'real_estate_exchange_no_cash_and_cash_adjustment_boundary',
        'unidades imobiliárias',
        ' Permuta sem torna sempre tem ganho de capital.',
        'exchange_without_cash_taxed_or_cash_entirely_gain'),
    (
        'trib-irpf-venda-carro-usado',
        'O limite considera o valor de alienação de até R$ 35 mil no mesmo '
        'mês. Devem ser somados bens ou direitos da mesma natureza. A venda '
        'de outra categoria não entra automaticamente nesse grupo. '
        'Ultrapassar R$ 35 mil retira a isenção de pequeno valor, mas não '
        'transforma perda em renda.',
        (source(LAW_9250_22), source(RFB_NO_GAIN),
         question_source('A questão 679 explica bens da mesma natureza.')),
        ('law_9250_article_22_small_value_asset',
         'rfb_small_value_asset_exemption',
         'rfb_irpf_2026_question_679_same_nature_assets'),
        'small_value_vehicle_monthly_same_nature_35000',
        'bens ou direitos da mesma natureza',
        ' Alienações de naturezas diferentes devem ser somadas.',
        'small_value_independent_sales_or_cross_nature_aggregation'),
    (
        'trib-irpf-carne-leao-aluguel',
        'O inquilino pessoa física exige Carnê-Leão Web e DARF no último '
        'dia útil do mês seguinte ao recebimento. Considera-se recebido '
        'quando o inquilino paga ao proprietário ou à administradora, mesmo '
        'que esta demore a repassar. Se o locatário é pessoa jurídica, a '
        'renda segue a ficha própria. Não se recolhe carnê-leão sobre o '
        'mesmo valor.',
        (source(LAW_7713_8), source(RFB_RENT), source(RFB_CL_MANUAL)),
        ('law_7713_article_8_monthly_rent',
         'rfb_carne_leao_rent_cash_basis', 'rfb_carne_leao_web_manual'),
        'rent_cash_basis_tenant_payment_to_administrator',
        'quando o inquilino paga ao proprietário ou à administradora',
        ' Aluguel administrado é recebido apenas no repasse ao locador.',
        'rent_owner_transfer_date_or_intermediary_payer'),
    (
        'trib-irpf-carne-leao-atrasado-multa-isolada',
        'O art. 44 prevê multa isolada de 50% sobre o valor do pagamento '
        'mensal que deixou de ser realizado, mesmo quando os rendimentos '
        'foram incluídos na DIRPF. Ela é diferente da multa de mora. O DARF '
        'atualizado recebe multa de mora e Selic. A multa isolada decorre da '
        'falta do recolhimento mensal obrigatório.',
        (source(LAW_9430_44), source(RFB_EXPENSES), source(RFB_IRPF_CASES)),
        ('law_9430_article_44_carne_leao_isolated_penalty',
         'rfb_live_carne_leao_50_percent_penalty',
         'rfb_binding_irpf_carne_leao_penalty'),
        'carne_leao_50_percent_isolated_penalty_vs_late_payment',
        'diferente da multa de mora',
        ' Pagar na declaração anual elimina a multa isolada.',
        'carne_leao_annual_return_erases_penalty_or_gross_base'),
    (
        'trib-irpf-aluguel-imobiliaria-dimob',
        'A DIMOB reúne pagamentos realizados no ano, discriminados '
        'mensalmente. A DIMOB é obrigação da empresa, não do proprietário '
        'pessoa física. A data é quando o locatário paga ao proprietário ou '
        'à administradora, mesmo com repasse em data posterior. A entrega '
        'usa programa próprio e Receitanet até o último dia útil de fevereiro.',
        (source(DIMOB_SERVICE), source(DIMOB_INFO)),
        ('rfb_dimob_service_11039', 'rfb_dimob_general_information'),
        'dimob_monthly_tenant_payment_and_owner_classification',
        'obrigação da empresa, não do proprietário pessoa física',
        ' Proprietário pessoa física entrega DIMOB.',
        'dimob_owner_filing_transfer_month_or_absolute_proof'),
    (
        'trib-irpf-pensao-recebida-isenta',
        'A pensão alimentícia recebida no âmbito do direito de família não '
        'sofre Imposto de Renda. A ADI 5.422 manda informar em Rendimentos '
        'Isentos e Não Tributáveis, sem carnê-leão. Isso não transforma '
        'automaticamente qualquer transferência entre parentes em pensão '
        'isenta. Identifique o beneficiário da pensão.',
        (source(STF_ALIMONY), source(RFB_ALIMONY)),
        ('stf_adi_5422_family_alimony',
         'rfb_received_alimony_exempt_filing'),
        'adi_5422_family_alimony_receipt_exemption', 'ADI 5.422',
        ' Qualquer transferência entre parentes é pensão isenta.',
        'family_transfer_blanket_exemption_or_received_alimony_taxation'),
    (
        'trib-irpf-rra-acao-judicial',
        'O art. 12-A trata anos-calendário anteriores, com tributação '
        'exclusiva na fonte e número de meses a que as parcelas se referem. '
        'O art. 12-B cuida do próprio ano do recebimento e a parcela é '
        'tributada no mês do recebimento. Podem existir dois tratamentos no '
        'mesmo pagamento.',
        (source(CHAMBER_7713), source(RFB_RRA)),
        ('law_7713_articles_12a_12b_current_text',
         'rfb_rra_work_income_manual'),
        'rra_article_12a_prior_years_12b_receipt_year', 'art. 12-B',
        ' O art. 12-A alcança valores do próprio ano do recebimento.',
        'rra_articles_12a_12b_reversed_or_process_months'),
    (
        'trib-irpf-espolio-declaracao-falecido',
        'A declaração final corresponde ao período de 1º de janeiro até a '
        'data da decisão judicial transitada em julgado ou da escritura '
        'pública de inventário e partilha. Ela é obrigatória quando há bens '
        'a inventariar e segue o prazo da Declaração de Ajuste Anual. Na '
        'DIRPF 2026, a Receita informa que não pode ser criada no Meu '
        'Imposto de Renda on-line ou aplicativo; use o programa de computador.',
        (source(RFB_ESTATE), source(RFB_CHANGES), source(RFB_DESKTOP)),
        ('rfb_estate_return_rules', 'rfb_irpf_2026_estate_channel',
         'rfb_dirpf_desktop_program'),
        'estate_final_return_trigger_deadline_and_2026_desktop_channel',
        'não pode ser criada no Meu Imposto de Renda on-line ou aplicativo',
        ' A declaração final pode ser enviada pelo aplicativo em 2026.',
        'estate_final_return_app_channel_or_general_optional_status'),
    (
        'trib-irpf-deducao-educacao-limite',
        'Na DIRPF 2026, ano-calendário de 2025, há limite anual individual '
        'de R$ 3.561,50 para o próprio contribuinte, cada dependente e cada '
        'alimentando. O excedente não vai para outro dependente. Curso de '
        'idiomas e materiais ficam fora.',
        (source(LAW_9250_8), source(RFB_EXPENSES), source(PERGUNTAO)),
        ('law_9250_article_8_education_deduction',
         'rfb_education_deduction_manual',
         'rfb_irpf_2026_education_limit'),
        'irpf_2026_education_3561_50_individual_nontransferable_limit',
        'R$ 3.561,50',
        ' O excedente de um dependente pode completar o limite de outro.',
        'education_limit_transfer_or_nonstatutory_courses'),
)


def page(fixture, visible=None, sources=None):
    return {
        'intent_id': fixture[0],
        'opening': fixture[1] if visible is None else visible,
        'official_sources': list(fixture[2] if sources is None else sources),
    }


class Tributario13CurrentLawTest(unittest.TestCase):

    def test_accepts_current_rules(self):
        for fixture in FIXTURES:
            with self.subTest(intent=fixture[0]):
                self.assertEqual([], auditor.current_legal_fact_reasons(
                    page(fixture)))

    def test_requires_every_canonical_source(self):
        for fixture in FIXTURES:
            self.assertEqual(len(fixture[2]), len(fixture[3]))
            for index, code in enumerate(fixture[3]):
                with self.subTest(intent=fixture[0], code=code):
                    sources = [dict(item) for item in fixture[2]]
                    sources[index]['url'] = (
                        'https://example.com/decoy?official=' +
                        sources[index]['url'])
                    self.assertIn(
                        'current_legal_fact_source_missing:' + code,
                        auditor.current_legal_fact_reasons(
                            page(fixture, sources=sources)))

    def test_rejects_outcome_omissions(self):
        for fixture in FIXTURES:
            with self.subTest(intent=fixture[0]):
                visible = fixture[1].replace(fixture[5], '', 1)
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + fixture[4],
                    auditor.current_legal_fact_reasons(
                        page(fixture, visible=visible)))

    def test_rejects_question_only_outcomes(self):
        for fixture in FIXTURES:
            with self.subTest(intent=fixture[0]):
                visible = fixture[1].removesuffix('.').replace('. ', '? ') + '?'
                self.assertIn(
                    'current_legal_fact_outcome_missing:' + fixture[4],
                    auditor.current_legal_fact_reasons(
                        page(fixture, visible=visible)))

    def test_rejects_meta_negation(self):
        fixture = FIXTURES[0]
        visible = 'Não é verdade que ' + fixture[1]
        self.assertIn(
            'current_legal_fact_outcome_missing:' + fixture[4],
            auditor.current_legal_fact_reasons(
                page(fixture, visible=visible)))

    def test_rejects_stale_contradictions(self):
        for fixture in FIXTURES:
            with self.subTest(intent=fixture[0]):
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + fixture[7],
                    auditor.current_legal_fact_reasons(page(
                        fixture, visible=fixture[1] + fixture[6])))

    def test_rejects_metadata_regressions(self):
        cases = (
            (0, 2, 'Perguntão', 'As questões 682 a 686 tratam da isenção.',
             'rfb_irpf_2026_questions_683_686'),
            (3, 0, 'Perguntão',
             'As questões 667 a 669 explicam a venda parcelada.',
             'rfb_irpf_2026_questions_668_669_installment_sale'),
            (4, 1, 'Receita Federal — consulta genérica', 'Trata da torna.',
             'rfb_cosit_128_2024_exchange_cash_adjustment'),
            (4, 2, 'Perguntão', 'A questão 681 explica a permuta.',
             'rfb_irpf_2026_questions_632_634_exchange'),
            (5, 2, 'Perguntão',
             'A questão 678 explica bens de pequeno valor.',
             'rfb_irpf_2026_question_679_same_nature_assets'),
        )
        for fixture_index, source_index, name, anchor, code in cases:
            with self.subTest(code=code):
                fixture = FIXTURES[fixture_index]
                sources = [dict(item) for item in fixture[2]]
                sources[source_index]['name'] = name
                sources[source_index]['anchor_claim'] = anchor
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(fixture, sources=sources)))

    def test_rejects_canonical_identity_decoys(self):
        cases = (
            (0, 0,
             'https://attacker@www.planalto.gov.br/ccivil_03/leis/'
             'l9250.htm#art23', 'law_9250_article_23_single_property'),
            (2, 1,
             'https://www.gov.br/decoy?source=/pt-br/servicos/'
             'atualizar-valor-de-bens-moveis-e-imoveis',
             'rfb_live_deap_rearp_service'),
            (4, 1, COSIT_128 + '&extra=1',
             'rfb_cosit_128_2024_exchange_cash_adjustment'),
            (8, 0, DIMOB_SERVICE + '&extra=1',
             'rfb_dimob_service_11039'),
            (9, 0,
             'https://portal.stf.jus.br/noticias/verNoticiaDetalhe.asp'
             '?idConteudo=488372&ori=1%2F1000',
             'stf_adi_5422_family_alimony'),
        )
        for fixture_index, source_index, bad_url, code in cases:
            with self.subTest(code=code):
                fixture = FIXTURES[fixture_index]
                sources = [dict(item) for item in fixture[2]]
                sources[source_index]['url'] = bad_url
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(fixture, sources=sources)))

    def test_rejects_copular_negated_source_metadata(self):
        cases = (
            (0, 2, 'Perguntão',
             'Não são as questões 683 a 686; este trecho não trata da isenção.',
             'rfb_irpf_2026_questions_683_686'),
            (4, 1, 'Não é a Solução de Consulta Cosit 128/2024',
             'Trata de outro assunto.',
             'rfb_cosit_128_2024_exchange_cash_adjustment'),
            (5, 2, 'Perguntão',
             'Não é a questão 679; consulte a questão 678.',
             'rfb_irpf_2026_question_679_same_nature_assets'),
        )
        for fixture_index, source_index, name, anchor, code in cases:
            with self.subTest(code=code):
                fixture = FIXTURES[fixture_index]
                sources = [dict(item) for item in fixture[2]]
                sources[source_index]['name'] = name
                sources[source_index]['anchor_claim'] = anchor
                self.assertIn(
                    'current_legal_fact_source_missing:' + code,
                    auditor.current_legal_fact_reasons(
                        page(fixture, sources=sources)))

    def test_rejects_semantic_stale_paraphrases(self):
        cases = (
            (0, ' Uma doação realizada no quinquênio não afeta a isenção.'),
            (1, ' A contagem somente começa quando o comprador termina de pagar o preço.'),
            (2, ' A herança também desfaz a atualização feita pelo Rearp.'),
            (3, ' O tributo inteiro deve ser recolhido logo após a assinatura do contrato.'),
            (4, ' Mesmo sem diferença em dinheiro, a troca de imóveis é tributada.'),
            (5, ' Carro e moto têm, cada qual, teto próprio de R$ 35 mil.'),
            (6, ' Na locação administrada, o aluguel só é recebido quando o dinheiro chega ao dono.'),
            (7, ' A entrega da DIRPF afasta a penalidade isolada de cinquenta por cento.'),
            (8, ' A declaração deve ser entregue pelo locador pessoa física.'),
            (9, ' A pensão recebida continua tributável mensalmente pelo carnê-leão.'),
            (10, ' O artigo 12-A rege créditos do mesmo ano e o artigo 12-B, os atrasados.'),
            (11, ' Em 2026, o inventariante consegue criar a declaração final pelo celular.'),
            (12, ' É possível aproveitar em outro filho o saldo do limite que não foi usado.'),
        )
        for fixture_index, extra in cases:
            fixture = FIXTURES[fixture_index]
            with self.subTest(intent=fixture[0]):
                self.assertIn(
                    'current_legal_fact_stale_assertion:' + fixture[7],
                    auditor.current_legal_fact_reasons(page(
                        fixture, visible=fixture[1] + extra)))

    def test_rejects_revoked_assertion_contexts(self):
        estate = FIXTURES[11]
        visible = estate[1].replace(
            'Ela é obrigatória quando há bens a inventariar',
            'A regra revogada dizia: obrigatória quando há bens a inventariar',
            1)
        self.assertIn(
            'current_legal_fact_outcome_missing:' + estate[4],
            auditor.current_legal_fact_reasons(
                page(estate, visible=visible)))

        vehicle = FIXTURES[5]
        sources = [dict(item) for item in vehicle[2]]
        sources[2]['anchor_claim'] = (
            'Referência revogada: a questão 679 explica bens da mesma natureza.')
        self.assertIn(
            'current_legal_fact_source_missing:' + vehicle[3][2],
            auditor.current_legal_fact_reasons(
                page(vehicle, sources=sources)))


if __name__ == '__main__':
    unittest.main()
