#!/usr/bin/env python3
"""Paridade Go/Python na identidade da URL oficial do Planalto.

Gemeo de internal/v2ingest/planalto_part_variante_test.go. Os comparadores por
SUBSTRING do auditor Python (`has_source_url_part`,
`has_planalto_source_url_part`, `has_consolidated_statute_article_metadata`)
ficaram para tras do lado Go na equivalencia de grafia do Planalto (BUG-120):
o Planalto publica o mesmo ato em duas grafias — `l10406.htm` (a eleita por
internal/lexml, com 4.030 ancoras de artigo) e `l10406compilada.htm` (5
ancoras) — e comparar bytes reprovava pagina que citava a fonte CERTA.

Medido em 2026-09-10 sobre as 11.201 paginas de data/editorial/v2_pages/,
antes e depois da correcao: 65 paginas PUBLICADAS de 17 shards reprovavam com
`current_legal_fact_source_missing` citando a grafia eleita (`l10406.htm#artN`,
`l8078.htm#artN`, `d3048.htm#artN`) contra regra que pedia a compilada — entre
elas bancario-02/banc-instagram-invadido-venda-falsa, o caso que o proprio
docstring de planaltoPartMatchesSource (internal/v2ingest) diz ter medido em
producao. Nenhuma pagina passou de verde a vermelho: a equivalencia so
acrescenta aceitacao de fonte que ja estava la.

A METADE QUE IMPEDE O AFROUXAMENTO tem peso igual: MESMO documento com
dispositivo DIFERENTE continua reprovando, ato diferente nunca casa, e o
emissor continua preso em `has_planalto_source_url_part` — citacao legal mal
atribuida e P1 permanente e a unica classe com risco real sob a etica da OAB.
"""

import json
import os
import unittest

from tools import audit_v2_pages as auditor


def pagina(*urls, name='', anchor_claim=''):
    return {'official_sources': [
        {'url': url, 'name': name, 'anchor_claim': anchor_claim}
        for url in urls]}


class PlanaltoURLVariantParityTest(unittest.TestCase):

    def test_aceita_a_outra_grafia_do_mesmo_artigo(self):
        page = pagina(
            'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art927')
        self.assertTrue(
            auditor.has_source_url_part(page, 'l10406compilada.htm#art927'),
            'a regra pedia a grafia compilada e a pagina tem a grafia eleita '
            'do mesmo artigo — deveria casar')
        self.assertTrue(
            auditor.has_planalto_source_url_part(
                page, 'l10406compilada.htm#art927'),
            'has_planalto_source_url_part tambem precisa da equivalencia')

    def test_part_sem_fragmento_e_coringa_de_artigo(self):
        page = pagina(
            'https://www.planalto.gov.br/ccivil_03/leis/l8078.htm#art39')
        self.assertTrue(
            auditor.has_source_url_part(page, 'l8078compilado.htm'),
            'part sem fragmento deveria casar com qualquer artigo do mesmo '
            'documento, na outra grafia')

    def test_recusa_outro_dispositivo_do_mesmo_documento(self):
        page = pagina(
            'https://www.planalto.gov.br/ccivil_03/leis/l8078.htm#art51')
        self.assertFalse(
            auditor.has_source_url_part(page, 'l8078compilado.htm#art43'),
            'aceitou artigo diferente do mesmo documento, na outra grafia')
        self.assertFalse(
            auditor.has_planalto_source_url_part(
                page, 'l8078compilado.htm#art43'),
            'aceitou artigo diferente do mesmo documento, na outra grafia')

    def test_recusa_outra_familia_de_ato(self):
        page = pagina(
            'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art927')
        self.assertFalse(
            auditor.has_source_url_part(page, 'l8078compilado.htm#art927'),
            'casou documentos de atos diferentes so porque o fragmento '
            'coincidiu')

    def test_ignora_partes_que_nao_sao_do_planalto(self):
        page = pagina(
            'https://www.stj.jus.br/SCON/pesquisar.jsp?b=SUMU&sumula=323')
        self.assertFalse(
            auditor.has_source_url_part(page, 'l8078compilado.htm'),
            'fonte de outro host nao deveria casar com parte do Planalto')
        self.assertFalse(
            auditor.planalto_part_matches_source(
                'https://www.planalto.gov.br/ccivil_03/leis/l8078.htm',
                'sumula=323'),
            'part que nao e nome de documento .htm nao deveria casar')

    def test_equivalencia_nao_solta_o_emissor(self):
        """O caminho do Planalto num host de terceiro continua reprovando.

        `has_planalto_source_url_part` prende o emissor (host planalto.gov.br,
        caminho /ccivil_03/) e a equivalencia de grafia nao pode abrir essa
        porta: e exatamente o ataque que
        TestV2PythonAuditorRequiresIssuerBoundImobiliario07Sources encena.
        """
        falsa = pagina(
            'https://www.stj.jus.br/falso/ccivil_03/leis/2002/l10406.htm#art618')
        self.assertFalse(
            auditor.has_planalto_source_url_part(
                falsa, 'l10406compilada.htm#art618'),
            'aceitou caminho do Planalto servido por outro emissor')
        self.assertFalse(
            auditor.planalto_part_matches_source(
                'https://www.stj.jus.br/falso/ccivil_03/leis/2002/'
                'l10406.htm#art618',
                'l10406compilada.htm#art618'),
            'a equivalencia de grafia precisa checar o host por conta propria')
        fora_do_ccivil = pagina(
            'https://www.planalto.gov.br/outro/l10406.htm#art618')
        self.assertFalse(
            auditor.has_planalto_source_url_part(
                fora_do_ccivil, 'l10406compilada.htm#art618'),
            'aceitou documento fora de /ccivil_03/ no host certo')

    def test_familia_e_fragmento_reconhece_sufixos_do_acervo(self):
        casos = (
            ('l8078compilado.htm#art39', 'l8078', 'art39'),
            ('l8078.htm', 'l8078', ''),
            ('l10406compilada.htm#art927', 'l10406', 'art927'),
            ('l8213cons.htm#art55', 'l8213', 'art55'),
            ('l8036consol.htm', 'l8036', ''),
            ('l6015consolidado.htm#art167', 'l6015', 'art167'),
            ('leis/2002/l10406compilada.htm', 'l10406', ''),
            ('ccivil_03/leis/l10.820.htm', 'l10.820', ''),
        )
        for trecho, want_familia, want_fragmento in casos:
            familia, fragmento, ok = auditor.planalto_doc_familia_e_fragmento(
                trecho)
            self.assertTrue(
                ok, f'{trecho!r}: esperava reconhecer documento .htm')
            self.assertEqual((familia, fragmento),
                             (want_familia, want_fragmento), trecho)
        self.assertFalse(
            auditor.planalto_doc_familia_e_fragmento('sumula=323')[2],
            'trecho sem sufixo .htm nao e documento do Planalto')

    def test_metadado_de_estatuto_consolidado_aceita_a_outra_grafia(self):
        page = pagina(
            'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406.htm#art927',
            name='Codigo Civil, art. 927',
            anchor_claim='responsabilidade civil do art. 927')
        self.assertTrue(
            auditor.has_consolidated_statute_article_metadata(
                page, 'l10406compilada.htm', '927'),
            'metadado do mesmo artigo na outra grafia deveria casar')
        self.assertFalse(
            auditor.has_consolidated_statute_article_metadata(
                page, 'l10406compilada.htm', '928'),
            'aceitou metadado que declara outro artigo')


DESTRAVADAS = (
    ('bancario-02', 'banc-instagram-invadido-venda-falsa',
     ('current_legal_fact_source_missing:cc_articles_186_927_profile_owner',)),
    ('familia-13', 'fam-incluir-pai-biologico-multiparentalidade',
     ('current_legal_fact_source_missing:stf_tema_622_biological_multiparentage',)),
    ('familia-13', 'fam-inseminacao-caseira-paternidade',
     ('current_legal_fact_source_missing:cnj_149_cfm_2320_home_insemination',)),
    ('familia-13', 'fam-investigacao-paternidade',
     ('current_legal_fact_source_missing:cc_1606_cpc_biological_parentage',)),
    ('familia-16', 'fam-indenizacao-vitima-violencia',
     ('current_legal_fact_source_missing:cc_art_200_criminal_fact_prescription',)),
    ('imobiliario-01', 'imob-fiador-faleceu',
     ('current_legal_fact_source_missing:cc_art_836_guarantor_death',)),
    ('imobiliario-02', 'imob-dividas-locatario-falecido',
     ('current_legal_fact_source_missing:cc_1792_tenancy_11_stj_439945_deceased_tenant_debts',)),
    ('imobiliario-02', 'imob-duas-garantias-vedacao',
     ('current_legal_fact_source_missing:tenancy_37_cc_1467_guarantee_boundary',)),
    ('imobiliario-02', 'imob-multa-juros-aluguel-atrasado',
     ('current_legal_fact_source_missing:law_14905_current_legal_rate',)),
    ('imobiliario-03', 'imob-imobiliaria-nao-repassa-alugueis',
     ('current_legal_fact_source_missing:cc_articles_667_668_property_manager_accounts',)),
    ('imobiliario-05', 'imob-arrematacao-dividas-anteriores',
     ('current_legal_fact_source_missing:auction_debts_ctn_130_tema_1134_cpc_908_stj_2042756_info_479',)),
    ('imobiliario-05', 'imob-arvore-vizinho-caiu-dano',
     ('current_legal_fact_source_missing:neighbor_tree_cc_186_927_393_1283',)),
    ('imobiliario-05', 'imob-cessao-direitos-hereditarios-imovel',
     ('current_legal_fact_source_missing:inheritance_assignment_cc_1793_1795_stj_1809548_registry',)),
    ('imobiliario-05', 'imob-condominio-negativar-devedor',
     ('current_legal_fact_source_missing:condominium_credit_listing_cpc_784_cdc_43_stj_359_548',)),
    ('imobiliario-05', 'imob-divida-condominio-omitida-venda',
     ('current_legal_fact_source_missing:hidden_condominium_debt_cc_1345_422_stj_tema_886_cpc_784',)),
    ('imobiliario-05', 'imob-doacao-imovel-revogacao',
     ('current_legal_fact_source_missing:donation_cc_541_555_562_1245',)),
    ('imobiliario-05', 'imob-exclusividade-corretor-vendi-sozinho',
     ('current_legal_fact_source_missing:broker_exclusivity_cc_725_727_stj_aresp_2072274',)),
    ('imobiliario-05', 'imob-fiador-executado-defesas',
     ('current_legal_fact_source_missing:cc_819_827_828_838_consolidated_metadata', 'current_legal_fact_source_missing:guarantor_cc_819_838_tenancy_40',)),
    ('imobiliario-05', 'imob-gaveta-comprador-nao-paga-banco',
     ('current_legal_fact_source_missing:drawer_contract_law_9514_29_26_stj_sumula_308_cc_475',)),
    ('imobiliario-05', 'imob-indisponibilidade-bens-vendedor',
     ('current_legal_fact_source_missing:cnib_provisions_149_188_cpc_792_cc_1245',)),
    ('imobiliario-05', 'imob-inquilino-rescindir-barulho-predio',
     ('current_legal_fact_source_missing:tenancy_art_22_ii_peaceful_use',)),
    ('imobiliario-05', 'imob-rateio-obra-luxo-minoria',
     ('current_legal_fact_source_missing:cc_1336_1341_1342_1343_1351_consolidated_metadata', 'current_legal_fact_source_missing:condominium_works_cc_1341_1342_1351_law_14405',)),
    ('imobiliario-05', 'imob-sublocacao-valor-maior',
     ('current_legal_fact_source_missing:cc_art_876_sublocation_restitution',)),
    ('imobiliario-05', 'imob-vendedor-atrasa-documentacao',
     ('current_legal_fact_source_missing:seller_documents_cc_397_475_417_420_registry',)),
    ('imobiliario-06', 'imob-built-to-suit-rescisao-multa',
     ('current_legal_fact_source_missing:tenancy_art_54a_cc_413_penalty_boundaries',)),
    ('imobiliario-06', 'imob-fundo-comercio-indenizacao',
     ('current_legal_fact_source_missing:cc_1142_tenancy_52_stj_406502_business_goodwill_indemnity',)),
    ('imobiliario-06', 'imob-ponto-comercial-verbete',
     ('current_legal_fact_source_missing:cc_1142_tenancy_51_commercial_point',)),
    ('imobiliario-06', 'imob-renovatoria-prazo-decadencial',
     ('current_legal_fact_source_missing:cc_207_208_195_198_decadence_exceptions',)),
    ('imobiliario-06', 'imob-trespasse-e-locacao',
     ('current_legal_fact_source_missing:tenancy_13_cc_1144_1146_stj_trespasse',)),
    ('imobiliario-07', 'imob-arrendamento-rural-vs-locacao',
     ('current_legal_fact_source_missing:land_statute_95_96_decree_59566_3_18_tenancy_1_rural_classification',)),
    ('imobiliario-07', 'imob-coworking-natureza-juridica',
     ('current_legal_fact_source_missing:cc_425_tenancy_1_coworking_fact_specific_classification',)),
    ('imobiliario-07', 'imob-locacao-quiosque-feira',
     ('current_legal_fact_source_missing:tenancy_1_51_54_cc_425_kiosk_contract_classification',)),
    ('imobiliario-07', 'imob-queda-faturamento-renegociar',
     ('current_legal_fact_source_missing:tenancy_18_19_68_cc_317_478_revenue_drop_and_rent_revision',)),
    ('imobiliario-08', 'imob-cessao-direitos-compra',
     ('current_legal_fact_source_missing:cc_286_299_stj_contract_position_assignment',)),
    ('imobiliario-08', 'imob-vicio-construtivo-prazos',
     ('current_legal_fact_source_missing:cc_445_stj_info_620_defect_deadlines',)),
    ('imobiliario-09', 'imob-area-menor-escritura',
     ('current_legal_fact_source_missing:imobiliario09_area_shortfall_relative_twentieth_and_deadline',)),
    ('imobiliario-09', 'imob-compra-imovel-espolio',
     ('current_legal_fact_source_missing:imobiliario09_estate_sale_judicial_extrajudicial_and_assignment',)),
    ('imobiliario-09', 'imob-comprei-nao-registrei',
     ('current_legal_fact_source_missing:imobiliario09_unregistered_purchase_property_and_remedies',)),
    ('imobiliario-09', 'imob-due-diligence-compra',
     ('current_legal_fact_source_missing:imobiliario09_due_diligence_registry_concentration_and_tax_fraud',)),
    ('imobiliario-09', 'imob-escritura-quando-obrigatoria',
     ('current_legal_fact_source_missing:imobiliario09_public_deed_threshold_exceptions_and_registration',)),
    ('imobiliario-09', 'imob-evicao-perdi-imovel',
     ('current_legal_fact_source_missing:imobiliario09_eviction_prior_right_indemnity_and_defense',)),
    ('imobiliario-09', 'imob-fraude-credores-vs-execucao',
     ('current_legal_fact_source_missing:imobiliario09_creditor_fraud_vs_enforcement_fraud',)),
    ('imobiliario-09', 'imob-itbi-base-calculo',
     ('current_legal_fact_source_missing:imobiliario09_itbi_market_value_presumption_and_arbitration',)),
    ('imobiliario-09', 'imob-itbi-cessao-direitos',
     ('current_legal_fact_source_missing:imobiliario09_itbi_assignment_tema_1124_pending',)),
    ('imobiliario-09', 'imob-itbi-quem-paga-quando',
     ('current_legal_fact_source_missing:imobiliario09_itbi_taxpayer_contract_and_registration_timing',)),
    ('imobiliario-09', 'imob-metragem-planta-menor',
     ('current_legal_fact_source_missing:imobiliario09_plan_area_offer_and_civil_measure_boundaries',)),
    ('imobiliario-09', 'imob-permuta-imoveis',
     ('current_legal_fact_source_missing:imobiliario09_real_estate_exchange_costs_torna_and_tax',)),
    ('imobiliario-09', 'imob-preferencia-condomino-venda-fracao',
     ('current_legal_fact_source_missing:imobiliario09_coowner_preference_indivisibility_deadline_and_deposit',)),
    ('imobiliario-09', 'imob-registro-imovel-passo-a-passo',
     ('current_legal_fact_source_missing:imobiliario09_registry_protocol_qualification_and_certificate',)),
    ('imobiliario-09', 'imob-retrovenda-verbete',
     ('current_legal_fact_source_missing:imobiliario09_retrosale_deadline_payment_transmission_and_publicity',)),
    ('imobiliario-09', 'imob-venda-ascendente-descendente',
     ('current_legal_fact_source_missing:imobiliario09_ascendant_sale_consents_form_and_deadline',)),
    ('imobiliario-09', 'imob-venda-sem-outorga-conjugal',
     ('current_legal_fact_source_missing:imobiliario09_spousal_consent_annulment_and_stable_union_boundary',)),
    ('imobiliario-09', 'imob-vendedor-nao-entrega-imovel',
     ('current_legal_fact_source_missing:imobiliario09_seller_non_delivery_specific_performance_and_damages',)),
    ('imobiliario-09', 'imob-vicio-construtivo-acao',
     ('current_legal_fact_source_missing:imobiliario09_construction_defect_guarantee_and_claims',)),
    ('imobiliario-09', 'imob-vicio-oculto-imovel-usado',
     ('current_legal_fact_source_missing:imobiliario09_hidden_defect_remedies_and_deadlines',)),
    ('imobiliario-10', 'imob-adimplemento-substancial',
     ('current_legal_fact_source_missing:substantial_performance_case_specific_and_no_adjudication_without_full_payment',)),
    ('imobiliario-10', 'imob-comprador-parou-pagar-particular',
     ('current_legal_fact_source_missing:private_sale_default_cc_474_475_resolution_and_interpellation',)),
    ('imobiliario-10', 'imob-financiamento-negado-clausula-suspensiva',
     ('current_legal_fact_source_missing:financing_condition_cc_121_125_cdc_51_effect_and_consumer_boundary',)),
    ('imobiliario-10', 'imob-habite-se-atraso-responsabilidade',
     ('current_legal_fact_source_missing:habite_se_law_4591_44_cc_186_post_grant_averment_and_fault',)),
    ('imobiliario-10', 'imob-lote-atraso-infraestrutura',
     ('current_legal_fact_source_missing:lot_infrastructure_law_6766_2_cdc_35_law_6766_38',)),
    ('imobiliario-13', 'imob-acordo-parcelamento-condominio',
     ('current_legal_fact_source_missing:cc_article_1348_delegated_powers',)),
    ('previdenciario-02', 'prev-inss-escolheu-regra-pior',
     ('current_legal_fact_source_missing:rps_art_176e_best_benefit',)),
    ('previdenciario-20', 'prev-desistir-pedido-em-andamento',
     ('current_legal_fact_source_missing:rps_art_176e_best_or_different_benefit',)),
    ('previdenciario-21', 'prev-acompanhar-processo-meu-inss',
     ('current_legal_fact_source_missing:rps_art_176_incomplete_documents',)),
    ('saude-06', 'saude-direito-de-arrependimento-plano',
     ('current_legal_fact_source_missing:cdc_article_49_distance_withdrawal',)),
)


class AcervoDestravadoTest(unittest.TestCase):
    """As 65 paginas publicadas que a divergencia de grafia reprovava.

    Vinte e seis viviam em imobiliario-07/08/09, que TEM teste de shard vivo;
    as outras 39 vivem em 14 shards que nao tinham nenhum — e foi por isso que
    a divergencia sobreviveu a uma campanha inteira de paridade. A tabela e
    congelada por CODIGO, nao por veredito vazio: pagina do acervo pode
    carregar outro motivo legitimo, e reprovar por isso nao e regressao desta
    frente.
    """

    def test_nenhum_codigo_destravado_reaparece(self):
        por_shard = {}
        for shard, intent, codigos in DESTRAVADAS:
            por_shard.setdefault(shard, {})[intent] = codigos
        encontradas = 0
        for shard, esperadas in sorted(por_shard.items()):
            caminho = os.path.join(
                auditor.ROOT, 'data', 'editorial', 'v2_pages', shard + '.jsonl')
            with open(caminho, encoding='utf-8') as fh:
                paginas = {}
                for linha in fh:
                    if not linha.strip():
                        continue
                    page = json.loads(linha)
                    paginas[page.get('intent_id')] = page
            for intent, codigos in sorted(esperadas.items()):
                page = paginas.get(intent)
                if page is None:
                    # Supersessao retira intencao do shard; ausencia nao e
                    # regressao desta regra.
                    continue
                encontradas += 1
                motivos = auditor.current_legal_fact_reasons(page)
                with self.subTest(shard=shard, intent=intent):
                    self.assertEqual(
                        [], [c for c in codigos if c in motivos],
                        'a divergencia de grafia do Planalto voltou')
        self.assertGreaterEqual(
            encontradas, 60,
            f'so {encontradas} das {len(DESTRAVADAS)} intencoes congeladas '
            'ainda existem no acervo — a cobertura evaporou em silencio')


class LiveImobiliarioShardsTest(unittest.TestCase):
    """As 26 paginas vivas que a divergencia reprovava.

    Trava a regressao do lado Python: os gemeos Go
    (TestV2PythonAuditorAcceptsLiveImobiliario07Rules/08/09CurrentLaw) so
    rodam com a toolchain Go compilada.
    """

    SHARDS = ('imobiliario-07', 'imobiliario-08', 'imobiliario-09')

    def test_shards_vivos_sem_fonte_ausente(self):
        for shard in self.SHARDS:
            caminho = os.path.join(
                auditor.ROOT, 'data', 'editorial', 'v2_pages', shard + '.jsonl')
            with open(caminho, encoding='utf-8') as fh:
                linhas = [linha for linha in fh if linha.strip()]
            self.assertTrue(linhas, f'{shard}: shard vazio')
            for linha in linhas:
                page = json.loads(linha)
                with self.subTest(shard=shard, intent=page.get('intent_id')):
                    self.assertEqual(
                        [], auditor.current_legal_fact_reasons(page))


if __name__ == '__main__':
    unittest.main()
