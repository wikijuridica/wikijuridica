"""Semantic current-law gate for four adversarially reviewed v2 samples."""


# Paridade literal com internal/v2ingest/current_legal_facts_sample_review.go.
# Cada deep link usa a grafia do Planalto que TEM a ancora do artigo, medida
# baixando os documentos (Go em 2026-08-30, fee8b9db; re-medido em
# 2026-09-05): l8078compilado.htm nao tem ancora de artigo; del2848compilado.htm
# nao tem art105/106/107; del3689compilado.htm nao tem art51. Este modulo ficou
# seis dias na grafia velha e reprovava as paginas ja corrigidas do estoque.
SOURCE_REQUIREMENTS = {
    'banc-tempo-maximo-nome-negativado': (
        (
            'https://www.planalto.gov.br/ccivil_03/leis/'
            'l8078.htm#art43',
            'cdc_article_43_five_year_credit_listing_limit',
            (('cinco anos', 'prazo maximo de cinco anos'),),
        ),
        (
            'https://processo.stj.jus.br/jurisprudencia/externo/'
            'informativo/?livre=%40CNOT%3D020788',
            'stj_resp_2095414_due_date_credit_listing_term',
            (('primeiro dia seguinte ao vencimento',
              'dia seguinte ao vencimento'),),
        ),
        (
            'https://processo.stj.jus.br/SCON/'
            'pesquisar.jsp?b=SUMU&sumula=323',
            'stj_sumula_323_five_year_credit_listing_limit',
            (('cinco anos', 'prazo maximo de cinco anos'),),
        ),
        (
            'https://processo.stj.jus.br/SCON/'
            'pesquisar.jsp?b=SUMU&sumula=548',
            'stj_sumula_548_paid_debt_removal',
            (
                ('cinco dias uteis', '5 dias uteis'),
                ('pagamento integral e efetivo',
                 'divida integralmente paga', 'quitacao integral'),
            ),
        ),
    ),
    'emp-duplicata-mercantil-vs-servicos': (
        (
            'https://www.planalto.gov.br/ccivil_03/leis/l5474.htm#art1',
            'law_5474_article_1_invoice_term',
            (('dever de extrair a fatura', 'extracao da fatura',
              'fatura nas vendas mercantis'),),
        ),
        (
            'https://www.planalto.gov.br/ccivil_03/leis/l5474.htm#art2',
            'law_5474_articles_2_3_paragraph_2_short_term_duplicate',
            (
                ('art 3 2', 'art 3 paragrafo 2',
                 'artigo 3 paragrafo 2'),
                ('prazo inferior a 30 dias', 'pagamento contra a entrega'),
            ),
        ),
        (
            'https://www.planalto.gov.br/ccivil_03/leis/l5474.htm#art20',
            'law_5474_article_20_service_duplicate',
            (
                ('prestadores de servicos podem emitir fatura e duplicata',
                 'prestacao de servicos emitam fatura e duplicata'),
                ('natureza e valor dos servicos',),
                ('prestacao efetiva e o vinculo contratual',
                 'prestacao efetiva e vinculo contratual'),
            ),
        ),
        (
            'https://processo.stj.jus.br/jurisprudencia/externo/'
            'informativo/?acao=pesquisar&aplicacao=informativo&'
            'livre=%40CNOT%3D%27020066%27',
            'stj_resp_2036764_duplicate_issuer_causality',
            (
                ('somente o vendedor ou o prestador credor',
                 'apenas o vendedor ou o prestador credor'),
                ('mercadoria ou ao servico correspondente',
                 'mercadoria ou servico correspondente'),
            ),
        ),
    ),
    'crim-perdao-do-ofendido': (
        ('https://www.planalto.gov.br/ccivil_03/decreto-lei/'
         'del2848.htm#art105',
         'penal_code_article_105_private_forgiveness',
         (('perdao do ofendido na acao privada',
           'perdao na acao privada'),
          ('antes de a condenacao transitar em julgado',
           'antes do transito em julgado da condenacao'))),
        ('https://www.planalto.gov.br/ccivil_03/decreto-lei/'
         'del2848.htm#art106',
         'penal_code_article_106_forgiveness_acceptance',
         (('perdao depende de aceitacao',
           'perdao so produz efeito se aceito'),
          ('concedido a um querelado aproveita a todos',
           'perdao concedido a um aproveita a todos'))),
        ('https://www.planalto.gov.br/ccivil_03/decreto-lei/'
         'del2848.htm#art107',
         'penal_code_article_107_v_accepted_forgiveness_extinction',
         (('inciso v',), ('perdao aceito',),
          ('extincao da punibilidade',), ('acao privada',))),
        ('https://www.planalto.gov.br/ccivil_03/decreto-lei/'
         'del3689.htm#art51',
         'criminal_procedure_article_51_forgiveness_acceptance',
         (('concedido a um dos querelados aproveita aos demais',
           'concedido a um dos querelados aproveita os demais',
           'concedido a um querelado aproveita a todos'),
          ('depende de aceitacao', 'so produz efeito se aceito'))),
    ),
    'trab-descontos-permitidos': (
        (
            'https://www.planalto.gov.br/ccivil_03/decreto-lei/'
            'del5452.htm#art462',
            'clt_articles_462_578_579_582_salary_and_union_deductions',
            (
                ('arts 462 578 579 e 582',
                 'artigos 462 578 579 e 582'),
                ('adiantamento dispositivo de lei ou norma coletiva',
                 'adiantamento lei ou norma coletiva'),
                ('desconto por dano', 'dano causado pelo empregado'),
                ('dolo',),
                ('culpa previamente acordada',
                 'possibilidade previamente acordada'),
                ('autorizacao previa e expressa',
                 'previa e expressamente autorizado'),
            ),
        ),
        (
            'https://www.tst.jus.br/documents/10157/63003/'
            'Livro-Internet.pdf',
            'tst_sumula_342_employee_authorized_deductions',
            (
                ('sumula 342',),
                ('autorizacao previa e por escrito',
                 'previamente autorizados por escrito'),
                ('assistencia odontologica ou medico hospitalar',
                 'assistencia odontologica e medico hospitalar'),
                ('seguro e previdencia privada',
                 'seguro previdencia privada'),
                ('entidades cooperativas culturais ou recreativo '
                 'associativas',
                 'cooperativas culturais e recreativo associativas'),
                ('salvo vicio de vontade', 'sem coacao fraude ou erro',
                 'salvo se houver coacao ou outro defeito que vicie o ato '
                 'juridico'),
            ),
        ),
    ),
}

LAW_10820_CONDITIONAL_SOURCE = (
    'https://www.planalto.gov.br/ccivil_03/leis/2003/l10.820compilado.htm',
    'law_10820_consigned_payroll_deductions',
    (
        ('lei 10 820', 'lei 10820'),
        ('desconto de prestacoes', 'desconto em folha'),
        ('emprestimos financiamentos', 'emprestimo consignado'),
    ),
)


OUTCOME_RULES = {
    'banc-tempo-maximo-nome-negativado': (
        'credit_listing_due_date_and_paid_removal_timeline',
        (
            (
                'teto de cinco anos comeca no primeiro dia seguinte ao '
                'vencimento',
                'limite de cinco anos comeca no primeiro dia seguinte ao '
                'vencimento',
                'quinquenio comeca no primeiro dia seguinte ao vencimento',
                'prazo de cinco anos tem inicio no dia seguinte ao '
                'vencimento',
            ),
            (
                'uma inclusao tardia nao reinicia a contagem',
                'inclusao posterior nao reinicia o prazo',
                'data da inscricao nao inicia novo prazo de cinco anos',
                'registro posterior nao alonga o quinquenio',
            ),
            (
                'depois do pagamento integral e efetivo a sumula 548 do stj '
                'atribui ao credor cinco dias uteis para requerer a exclusao',
                'a sumula 548 atribui ao credor cinco dias uteis para '
                'providenciar a baixa apos o pagamento integral e efetivo',
                'apos o pagamento integral e efetivo o credor tem cinco dias '
                'uteis para providenciar a baixa',
                'quitada integralmente a divida o credor tem cinco dias '
                'uteis para requerer a exclusao',
            ),
            (
                'a saida do cadastro nao declara por si so que a obrigacao '
                'foi paga ou extinta',
                'exclusao do cadastro nao extingue por si so a divida',
                'prazo prescricional depende da especie de divida',
                'prescricao da cobranca responde a outra pergunta',
            ),
        ),
    ),
    'emp-duplicata-mercantil-vs-servicos': (
        'duplicate_invoice_term_and_article_3_short_term_scope',
        (
            (
                'prazo minimo de 30 dias do art 1 refere se ao dever de '
                'extrair a fatura',
                'art 1 vincula o prazo nao inferior a 30 dias a obrigacao de '
                'emitir a fatura',
                'trinta dias do art 1 dizem respeito a extracao obrigatoria '
                'da fatura',
            ),
            (
                'isso nao significa que o titulo seja proibido em vencimentos '
                'mais curtos',
                'prazo inferior a 30 dias nao invalida sozinho a duplicata '
                'mercantil',
                'duplicata mercantil nao exige universalmente prazo minimo '
                'de 30 dias',
                'vencimento inferior a 30 dias nao impede por si so a '
                'duplicata mercantil',
            ),
            (
                'art 3 2 permite representar por duplicata tanto a venda com '
                'pagamento contra a entrega da mercadoria ou do conhecimento '
                'de transporte quanto aquela com prazo inferior a 30 dias',
                'art 3 paragrafo 2 admite duplicata contra entrega ou com '
                'prazo inferior a 30 dias',
                'paragrafo 2 do art 3 permite duplicata na venda contra '
                'entrega e na venda com prazo menor que 30 dias',
            ),
            (
                'desde que o titulo declare essa condicao',
                'titulo deve declarar a condicao de pagamento contra entrega '
                'ou em prazo inferior a 30 dias',
                'duplicata deve indicar a condicao de pagamento abreviado ou '
                'contra entrega',
            ),
        ),
    ),
    'crim-perdao-do-ofendido': (
        'private_forgiveness_state_punishment_and_acceptance',
        (
            ('estado conserva o poder de punir',
             'poder de punir permanece estatal',
             'jus puniendi continua pertencendo ao estado'),
            ('lei entrega ao ofendido a iniciativa e a conducao da queixa',
             'na acao privada a lei permite ao ofendido dispor da '
             'continuidade da queixa',
             'querelante dispoe da iniciativa processual e da continuidade '
             'da queixa'),
            ('art 107 v inclui o perdao aceito entre as causas de extincao da '
             'punibilidade na acao privada',
             'perdao aceito extingue a punibilidade na acao penal privada',
             'perdao aceito extingue a punibilidade nos crimes de acao '
             'privada'),
            ('so produz o efeito extintivo se for aceito pelo querelado',
             'perdao depende de aceitacao do querelado',
             'sem aceitacao o processo continua'),
            ('perdao nao e admissivel depois do transito em julgado da '
             'sentenca condenatoria',
             'perdao cabe antes de a condenacao transitar em julgado',
             'transito em julgado da condenacao impede o perdao'),
        ),
    ),
    'trab-descontos-permitidos': (
        'salary_deductions_article_462_damage_sumula_342_and_union_consent',
        (
            ('art 462 da clt proibe descontos no salario salvo quando '
             'resultem de adiantamento dispositivo de lei ou norma coletiva',
             'artigo 462 veda descontos salvo adiantamento lei ou instrumento '
             'coletivo',
             'caput do art 462 admite desconto por adiantamento previsao '
             'legal ou norma coletiva'),
            ('sumula 342 do tst considera licitos os abatimentos ajustados '
             'pelo trabalhador em proveito proprio',
             'sumula 342 admite descontos autorizados em beneficio do '
             'empregado',
             'desconto autorizado para beneficio do trabalhador pode ser '
             'valido'),
            ('sumula 342 do tst admite descontos com autorizacao previa e '
             'por escrito',
             'descontos da sumula 342 dependem de autorizacao previa e '
             'escrita',
             'beneficios enumerados foram previamente autorizados por '
             'escrito'),
            ('desde que nao haja coacao fraude ou erro',
             'salvo coacao fraude ou erro',
             'se nao houver vicio de vontade',
             'salvo se houver coacao ou outro defeito que vicie o ato '
             'juridico',
             'salvo se ficar demonstrada a existencia de coacao ou de outro '
             'defeito que vicie o ato juridico'),
            ('so e licito se houve dolo',
             'se houve dolo o desconto do dano e licito',
             'ocorrencia de dolo autoriza o desconto do dano',
             'dano doloso pode ser descontado'),
            ('no caso de simples culpa se essa possibilidade foi previamente '
             'acordada',
             'em caso de culpa a possibilidade de desconto deve ter sido '
             'previamente acordada',
             'dano culposo pode ser descontado se essa possibilidade foi '
             'acordada',
             'possibilidade de desconto por culpa foi acordada'),
            ('arts 578 579 e 582 condicionam o desconto a autorizacao previa '
             'e expressa do trabalhador',
             'contribuicao sindical exige autorizacao previa e expressa do '
             'empregado',
             'desconto da contribuicao sindical depende de consentimento '
             'previo e expresso'),
        ),
    ),
}


STALE_RULES = {
    'banc-tempo-maximo-nome-negativado': (
        (
            'credit_listing_five_year_term_from_registration',
            ('prazo de cinco anos conta a partir da inscricao',
             'prazo de cinco anos conta a partir dessa inscricao',
             'prazo de cinco anos conta a partir dessa inscricao nao do '
             'vencimento',
             'cinco anos contam da inscricao',
             'termo inicial e a data da inscricao',
             'prazo comeca na inclusao no cadastro',
             'data da inclusao inicia o quinquenio',
             'termo inicial nao e a data do contrato nem a data de nascimento '
             'da divida e sim a data da inscricao no cadastro restritivo'),
        ),
        (
            'credit_listing_paid_removal_wrong_period_or_trigger',
            ('apos o pagamento integral o credor tem cinco dias corridos '
             'para excluir',
             'credor pode manter a negativacao por cinco anos depois do '
             'pagamento',
             'pagamento integral nao abre prazo para a baixa',
             'cinco dias uteis contam da inclusao no cadastro'),
        ),
    ),
    'emp-duplicata-mercantil-vs-servicos': (
        (
            'duplicate_article_1_thirty_days_as_universal_title_requirement',
            ('duplicata mercantil exige prazo nao inferior a 30 dias',
             'duplicata mercantil exigindo prazo nao inferior a 30 dias',
             'duplicata mercantil e a extraida da fatura exigindo prazo nao '
             'inferior a 30 dias',
             'duplicata mercantil so pode ser emitida com prazo minimo de '
             '30 dias',
             'vencimento inferior a 30 dias invalida a duplicata mercantil',
             'art 1 proibe duplicata com prazo inferior a 30 dias'),
        ),
        (
            'duplicate_article_3_paragraph_2_short_or_delivery_denied',
            ('art 3 paragrafo 2 nao permite duplicata com prazo inferior a '
             '30 dias',
             'pagamento contra entrega nao pode ser representado por '
             'duplicata',
             'prazo inferior a 30 dias impede a duplicata'),
        ),
    ),
    'crim-perdao-do-ofendido': (
        (
            'private_action_jus_puniendi_transferred_to_victim',
            ('interesse na punicao pertence principalmente a quem foi '
             'atingido',
             'poder de punir pertence ao ofendido',
             'poder de punir pertence a vitima',
             'jus puniendi pertence ao querelante',
             'na acao privada o poder de punir deixa de ser estatal'),
        ),
        (
            'private_action_forgiveness_without_acceptance',
            ('perdao encerra o processo independentemente de aceitacao',
             'perdao nao depende de aceitacao',
             'vontade da vitima encerra o caso sozinha',
             'simples declaracao do ofendido extingue a punibilidade'),
        ),
    ),
    'trab-descontos-permitidos': (
        (
            'union_contribution_without_prior_express_authorization',
            ('contribuicao sindical independe de autorizacao especifica',
             'contribuicao sindical independe de autorizacao previa e '
             'expressa',
             'desconto sindical e automatico',
             'norma coletiva basta para autorizar a contribuicao sindical',
             'autorizacao previa e expressa nao e necessaria para a '
             'contribuicao sindical'),
        ),
        (
            'employee_damage_deduction_without_dolo_or_prior_fault_agreement',
            ('culpa basta para descontar o dano sem acordo previo',
             'desconto por dano independe de ajuste previo',
             'todo dano causado pelo empregado pode ser descontado'),
        ),
        (
            'employee_damage_deduction_written_form_mandatory',
            ('no caso de simples culpa se essa possibilidade foi previamente '
             'combinada por escrito',
             'no caso de simples culpa essa possibilidade deve ser '
             'previamente combinada por escrito',
             'culpa so permite desconto com acordo escrito',
             'paragrafo 1 do art 462 exige acordo escrito'),
        ),
        (
            'sumula_342_generic_authorization_for_every_deduction',
            ('autorizacao generica vale para qualquer desconto',
             'formulario generico permite todos os descontos',
             'sumula 342 dispensa consentimento real do empregado'),
        ),
        (
            'sumula_342_consigned_loan_misattribution',
            ('sumula 342 inclui emprestimo consignado',
             'sumula 342 disciplina emprestimo consignado'),
        ),
    ),
}


def _contains_any(value, *parts):
    return any(part in value for part in parts)


def relational_outcome_group_affirmed(
        intent, group, visible, semantic_clauses,
        clause_explicitly_nonaffirming):
    clauses = semantic_clauses(visible)
    for index, clause in enumerate(clauses):
        if clause_explicitly_nonaffirming(clause):
            continue
        if intent == 'banc-tempo-maximo-nome-negativado':
            if group == 0 and (
                    _contains_any(clause, 'quinquen', 'cinco anos', '5 anos') and
                    _contains_any(clause, 'comeca', 'inicia',
                                  'passa a correr', 'corre', 'termo inicial') and
                    'venciment' in clause and
                    _contains_any(clause, 'dia posterior', 'dia seguinte',
                                  'primeiro dia apos') and
                    not _contains_any(clause, 'nao comeca', 'nao inicia',
                                      'nao passa a correr', 'nao corre')):
                return True
            if group == 1 and (
                    _contains_any(clause, 'inclusao', 'inscricao',
                                  'negativacao', 'registro') and
                    _contains_any(clause, 'nao reinicia', 'nao reabre',
                                  'nao alonga', 'nao cria novo',
                                  'nao inicia novo')):
                return True
            if group == 2 and (
                    _contains_any(clause, 'pagamento integral',
                                  'quitacao integral', 'integralmente paga',
                                  'quitada integralmente',
                                  'quitado integralmente') and
                    _contains_any(clause, 'credor', 'fornecedor') and
                    _contains_any(clause, 'cinco dias uteis',
                                  '5 dias uteis') and
                    _contains_any(clause, 'exclu', 'baixa', 'retir') and
                    _contains_any(clause, 'deve', 'tem', 'cabe', 'atribui',
                                  'prazo') and
                    not _contains_any(clause, 'nao precisa', 'nao deve',
                                      'nao cabe', 'dispensa',
                                      'sem obrigacao')):
                return True
            if group == 3 and (
                    (_contains_any(clause, 'saida do cadastro',
                                   'exclusao do cadastro',
                                   'retirada do cadastro') and
                     _contains_any(clause, 'nao extingue', 'nao elimina',
                                   'nao quita')) or
                    ('prescri' in clause and _contains_any(
                        clause, 'distint', 'outra', 'depende da especie'))):
                return True
        elif intent == 'emp-duplicata-mercantil-vs-servicos':
            if group == 0 and (
                    _contains_any(clause, 'art 1', 'artigo 1') and
                    'fatura' in clause and
                    _contains_any(clause, 'obrigacao de emitir',
                                  'dever de emitir', 'dever de extrair',
                                  'extracao obrigatoria') and
                    _contains_any(clause, '30 dias', 'trinta dias') and
                    not _contains_any(clause, 'nao cria', 'nao impoe',
                                      'nao exige', 'sem dever', 'dispensa')):
                return True
            if group == 1 and (
                    _contains_any(clause, 'duplicata', 'titulo') and
                    _contains_any(clause, 'menos de 30 dias',
                                  'menos de trinta dias',
                                  'prazo inferior a 30 dias',
                                  'prazo inferior a trinta dias',
                                  'prazo menor que 30 dias',
                                  'prazo menor que trinta dias',
                                  'vencimento mais curto',
                                  'vencimentos mais curtos') and
                    _contains_any(clause, 'pode vencer', 'pode ter',
                                  'continua valida', 'e valida',
                                  'nao invalida', 'nao impede',
                                  'nao proibe', 'nao significa') and
                    not _contains_any(clause, 'nao pode', 'nao admite',
                                      'invalida', 'proibe')):
                return True
            if group == 2 and (
                    _contains_any(clause, 'art 3', 'artigo 3',
                                  'paragrafo 2') and
                    'duplicata' in clause and
                    _contains_any(clause, 'contra entrega',
                                  'pagamento contra a entrega') and
                    _contains_any(clause, 'prazo inferior', 'prazo menor') and
                    _contains_any(clause, 'admite', 'permite',
                                  'pode representar') and
                    not _contains_any(clause, 'nao admite', 'nao permite',
                                      'nao pode')):
                return True
            if group == 3 and (
                    'titulo' in clause and 'condicao' in clause and
                    _contains_any(clause, 'declara', 'declare', 'indica',
                                  'informa', 'deve constar') and
                    not _contains_any(clause, 'nao declara', 'nao indica',
                                      'nao informa', 'nao precisa')):
                return True
        elif intent == 'crim-perdao-do-ofendido':
            if group == 0 and (
                    _contains_any(clause, 'pretensao punitiva',
                                  'poder de punir', 'jus puniendi') and
                    _contains_any(clause, 'estado', 'estatal') and
                    _contains_any(clause, 'continua', 'permanece',
                                  'conserva', 'titularidade', 'pertence') and
                    not _contains_any(clause, 'deixa de ser estatal',
                                      'nao permanece estatal')):
                return True
            if group == 1 and (
                    _contains_any(clause, 'querelante', 'ofendido', 'vitima') and
                    _contains_any(clause, 'iniciativa', 'continuidade',
                                  'conducao') and
                    _contains_any(clause, 'acao privada', 'queixa') and
                    not _contains_any(clause, 'nao dispoe',
                                      'sem iniciativa')):
                return True
            if group == 2 and (
                    'perdao' in clause and 'aceit' in clause and
                    _contains_any(clause, 'extingue a punibilidade',
                                  'extincao da punibilidade') and
                    not _contains_any(clause, 'nao extingue',
                                      'nao causa extincao',
                                      'nao e causa')):
                return True
            if group == 3:
                context = clause
                if ('perdao' not in context and index and
                        'perdao' in clauses[index - 1]):
                    context = clauses[index - 1] + ' ' + context
                if 'perdao' in context and (
                        (_contains_any(context, 'depende', 'exige',
                                       'so produz') and
                         _contains_any(context, 'aceitacao', 'aceito',
                                       'concordancia')) or
                        (_contains_any(context, 'sem aceitacao',
                                       'sem concordancia', 'sem ela') and
                         'continua' in context)) and not _contains_any(
                            context, 'nao depende', 'independe',
                            'dispensa aceitacao', 'vale sem',
                            'produz efeito sem'):
                    return True
            if group == 4 and (
                    'perdao' in clause and 'transito em julgado' in clause and
                    _contains_any(clause, 'antes', 'nao e admissivel depois',
                                  'impede')):
                return True
        elif intent == 'trab-descontos-permitidos':
            if group == 0 and (
                    _contains_any(clause, 'empregador', 'art 462',
                                  'artigo 462') and
                    _contains_any(clause, 'nao pode', 'proibe', 'veda') and
                    _contains_any(clause, 'salario', 'desconto', 'abater') and
                    'adiantamento' in clause and
                    _contains_any(clause, 'lei', 'legal') and
                    'coletiv' in clause and
                    not _contains_any(clause, 'nao veda', 'nao proibe',
                                      'pode descontar fora',
                                      'pode abater fora')):
                return True
            if group == 1 and (
                    'sumula 342' in clause and
                    _contains_any(clause, 'admite', 'licitos', 'permite') and
                    _contains_any(clause, 'assistencia odontologica',
                                  'medico hospitalar', 'plano de saude') and
                    _contains_any(clause, 'seguro', 'previdencia privada') and
                    _contains_any(clause, 'cooperativ', 'cultur',
                                  'recreativo', 'associativ') and
                    not _contains_any(clause, 'nao admite', 'nao permite',
                                      'nao considera')):
                return True
            if group == 2 and (
                    'sumula 342' in clause and _contains_any(
                        clause, 'autorizacao previa e por escrito',
                        'previamente autorizados por escrito',
                        'autorizacao previa e escrita') and
                    _contains_any(clause, 'exige', 'depende',
                                  'com autorizacao',
                                  'foram previamente autorizados',
                                  'desde que haja', 'haja autorizacao') and
                    not _contains_any(clause, 'nao exige', 'nao depende',
                                      'dispensa', 'sem autorizacao')):
                return True
            if group == 3 and (
                    _contains_any(clause, 'coacao', 'vicio') and
                    _contains_any(clause, 'defeito', 'fraude', 'erro',
                                  'ato juridico') and
                    _contains_any(clause, 'salvo', 'sem coacao',
                                  'nao haja', 'nao exista', 'impede',
                                  'invalida') and
                    not _contains_any(clause, 'nao impedem', 'nao impede',
                                      'irrelevante', 'permite mesmo',
                                      'valido mesmo')):
                return True
            if group == 4 and (
                    'dano' in clause and 'dolo' in clause and
                    _contains_any(clause, 'licito', 'pode', 'autoriza') and
                    not _contains_any(clause, 'nao autoriza', 'nao permite',
                                      'nao pode', 'nao e licito')):
                return True
            if group == 5 and (
                    _contains_any(clause, 'culpa', 'negligencia') and
                    _contains_any(clause, 'previamente acordada',
                                  'acordo previo', 'previsao anterior') and
                    _contains_any(clause, 'pode', 'permite', 'autoriza',
                                  'possivel', 'licito', 'desconto') and
                    not _contains_any(clause, 'sem acordo', 'sem previsao',
                                      'nao autoriza', 'nao permite',
                                      'nao pode')):
                return True
            if group == 6 and (
                    'contribuicao sindical' in clause and
                    _contains_any(clause, 'autorizacao previa e expressa',
                                  'consentimento previo e expresso') and
                    _contains_any(clause, 'exige', 'depende', 'condiciona') and
                    not _contains_any(clause, 'nao exige', 'independe',
                                      'dispensa', 'automatica')):
                return True
    return False


def missing_outcome_groups(
        intent, visible, rule, affirmed, semantic_clauses,
        clause_explicitly_nonaffirming):
    missing = []
    for index, alternatives in enumerate(rule[1]):
        matched = relational_outcome_group_affirmed(
            intent, index, visible, semantic_clauses,
            clause_explicitly_nonaffirming)
        if intent not in OUTCOME_RULES:
            matched = any(affirmed(visible, alternative)
                          for alternative in alternatives)
        if not matched:
            missing.append(index)
    return missing


def relational_source_metadata_affirmed(code, metadata, semantic_clauses,
                                        clause_explicitly_nonaffirming):
    clauses = [
        clause for clause in semantic_clauses(metadata)
        if not clause_explicitly_nonaffirming(clause)
    ]
    value = ' '.join(clauses)
    if source_metadata_contradicts(code, value):
        return False
    if code == 'cdc_article_43_five_year_credit_listing_limit':
        return any(
            _contains_any(clause, 'cadastro', 'informacoes negativas',
                          'inscricao') and
            _contains_any(clause, 'cinco anos', '5 anos') and
            _contains_any(clause, 'limita', 'no maximo', 'prazo maximo',
                          'pode permanecer')
            for clause in clauses)
    if code == 'stj_resp_2095414_due_date_credit_listing_term':
        return any(
            'venciment' in clause and
            _contains_any(clause, 'primeiro dia seguinte', 'dia seguinte',
                          'dia posterior') and
            _contains_any(clause, 'termo inicial', 'inicio', 'comeca',
                          'passa a correr') and
            not _contains_any(clause, 'nao e o termo inicial',
                              'nao e termo inicial', 'nao inicia',
                              'nao comeca')
            for clause in clauses)
    if code == 'stj_sumula_323_five_year_credit_listing_limit':
        return any(
            _contains_any(clause, 'sumula 323', 'inscricao', 'inadimplente') and
            _contains_any(clause, 'cinco anos', '5 anos') and
            _contains_any(clause, 'no maximo', 'prazo maximo', 'limita',
                          'permanecer')
            for clause in clauses)
    if code == 'stj_sumula_548_paid_debt_removal':
        return any(
            _contains_any(clause, 'pagamento integral',
                          'integralmente paga', 'quitacao integral') and
            _contains_any(clause, 'credor', 'fornecedor') and
            _contains_any(clause, 'cinco dias uteis', '5 dias uteis') and
            _contains_any(clause, 'exclu', 'baixa', 'retir')
            for clause in clauses)
    if code == 'law_5474_article_1_invoice_term':
        return any(
            'fatura' in clause and 'venda' in clause and
            _contains_any(clause, 'extracao', 'extrair', 'emitir') and
            _contains_any(clause, '30 dias', 'trinta dias')
            for clause in clauses)
    if code == 'law_5474_articles_2_3_paragraph_2_short_term_duplicate':
        return any(
            _contains_any(clause, 'art 3 2', 'art 3 paragrafo 2',
                          'artigo 3 paragrafo 2') and
            _contains_any(clause, 'contra a entrega', 'contra entrega') and
            _contains_any(clause, 'prazo inferior', 'menos de 30 dias',
                          'menos de trinta dias')
            for clause in clauses)
    if code == 'law_5474_article_20_service_duplicate':
        emission = any(
            _contains_any(clause, 'prestador', 'prestadores',
                          'prestacao de servicos') and
            'fatura' in clause and 'duplicata' in clause and
            _contains_any(clause, 'podem emitir', 'pode emitir', 'emitam',
                          'emissao')
            for clause in clauses)
        description = any(
            'natureza' in clause and 'valor' in clause and 'servic' in clause
            for clause in clauses)
        proof = any(
            'prestacao efetiva' in clause and
            _contains_any(clause, 'vinculo contratual', 'contrato',
                          'relacao contratual')
            for clause in clauses)
        return emission and description and proof
    if code == 'stj_resp_2036764_duplicate_issuer_causality':
        return any(
            _contains_any(clause, 'somente o vendedor',
                          'apenas o vendedor') and
            'prestador' in clause and 'credor' in clause and
            'emit' in clause and 'duplicata' in clause and
            'mercadoria' in clause and 'servic' in clause and
            _contains_any(clause, 'correspondente', 'ligada', 'relativa')
            for clause in clauses)
    if code == 'penal_code_article_105_private_forgiveness':
        return any(
            'perdao' in clause and 'acao privada' in clause and
            'antes' in clause and 'transit' in clause and 'julgad' in clause
            for clause in clauses)
    if code == 'penal_code_article_106_forgiveness_acceptance':
        acceptance = any(
            'perdao' in clause and 'aceit' in clause and
            not _contains_any(clause, 'nao depende', 'independe', 'dispensa',
                              'sem aceitacao')
            for clause in clauses)
        extension = any(
            'querelado' in clause and
            _contains_any(clause, 'aproveita a todos',
                          'aproveita aos demais', 'aproveita os demais')
            for clause in clauses)
        return acceptance and extension
    if code == 'penal_code_article_107_v_accepted_forgiveness_extinction':
        return any(
            _contains_any(clause, 'inciso v', 'art 107 v') and
            'perdao' in clause and 'aceit' in clause and
            'extincao da punibilidade' in clause and
            'acao privada' in clause and
            not _contains_any(clause, 'nao causa extincao', 'nao extingue',
                              'nao e causa')
            for clause in clauses)
    if code == 'criminal_procedure_article_51_forgiveness_acceptance':
        return any(
            'perdao' in clause and 'querelado' in clause and
            _contains_any(clause, 'aproveita aos demais',
                          'aproveita os demais', 'aproveita a todos') and
            'aceit' in clause and
            not _contains_any(clause, 'nao depende', 'independe', 'dispensa',
                              'sem aceitacao')
            for clause in clauses)
    if code == 'clt_articles_462_578_579_582_salary_and_union_deductions':
        articles = all(article in value for article in ('462', '578', '579',
                                                         '582'))
        caput = any(
            '462' in clause and 'adiantamento' in clause and
            'lei' in clause and 'coletiv' in clause
            for clause in clauses)
        damage = any(
            'dano' in clause and _contains_any(clause, 'dolo', 'doloso') and
            'culpa' in clause and 'acordad' in clause and
            not _contains_any(clause, 'culpa sem acordo',
                              'sem possibilidade previamente acordada')
            for clause in clauses)
        union = any(
            'contribuicao sindical' in clause and
            'autorizacao previa e expressa' in clause and
            not _contains_any(clause, 'automatica', 'independe',
                              'nao exige', 'dispensa')
            for clause in clauses)
        return articles and caput and damage and union
    if code == 'tst_sumula_342_employee_authorized_deductions':
        return any(
            'sumula 342' in clause and
            _contains_any(clause, 'autorizacao previa e por escrito',
                          'previamente autorizados por escrito',
                          'autorizacao previa e escrita') and
            _contains_any(clause, 'assistencia odontologica',
                          'medico hospitalar', 'plano de saude') and
            _contains_any(clause, 'seguro', 'previdencia privada') and
            _contains_any(clause, 'cooperativ', 'cultur', 'recreativo',
                          'associativ') and
            _contains_any(clause, 'coacao', 'vicio', 'defeito') and
            not _contains_any(clause, 'nao exige autorizacao',
                              'dispensa autorizacao',
                              'sem autorizacao previa', 'mesmo com coacao',
                              'ainda que haja coacao')
            for clause in clauses)
    if code == 'law_10820_consigned_payroll_deductions':
        return any(
            _contains_any(clause, 'lei 10 820', 'lei 10820') and
            'desconto' in clause and
            _contains_any(clause, 'prestacoes', 'folha de pagamento',
                          'beneficio') and
            _contains_any(clause, 'emprestimo', 'financiamento',
                          'arrendamento') and
            not _contains_any(clause, 'nao autoriza', 'nao disciplina',
                              'independe de autorizacao')
            for clause in clauses)
    return False


def source_metadata_contradicts(code, value):
    if code == 'cdc_article_43_five_year_credit_listing_limit':
        return _contains_any(value, 'nao limita', 'sem limite de cinco anos',
                             'pode superar cinco anos')
    if code == 'stj_resp_2095414_due_date_credit_listing_term':
        return _contains_any(value, 'nao comeca no dia seguinte',
                             'nao e o dia seguinte',
                             'nao e o termo inicial',
                             'nao e termo inicial', 'nao o termo inicial',
                             'independe do vencimento')
    if code == 'stj_sumula_323_five_year_credit_listing_limit':
        return _contains_any(value, 'nao limita', 'permite mais de cinco anos',
                             'pode superar cinco anos')
    if code == 'stj_sumula_548_paid_debt_removal':
        return _contains_any(value, 'nao cabe ao credor',
                             'credor nao precisa', 'cinco dias corridos',
                             'independe do pagamento')
    if code == 'law_5474_article_1_invoice_term':
        return _contains_any(value, 'nao exige fatura', 'nao impoe',
                             'dispensa a fatura')
    if code == 'law_5474_articles_2_3_paragraph_2_short_term_duplicate':
        return _contains_any(value, 'nao admite', 'nao permite',
                             'prazo inferior invalida',
                             'contra entrega impede')
    if code == 'law_5474_article_20_service_duplicate':
        return _contains_any(value, 'nao podem emitir', 'nao pode emitir',
                             'nao exige natureza', 'dispensa natureza',
                             'sem prestacao efetiva',
                             'independe da prestacao efetiva',
                             'sem vinculo contratual',
                             'independe do contrato')
    if code == 'stj_resp_2036764_duplicate_issuer_causality':
        return _contains_any(value, 'nao e somente o vendedor',
                             'nao e apenas o vendedor',
                             'qualquer terceiro pode emitir',
                             'independe da mercadoria',
                             'independe do servico')
    if code == 'penal_code_article_105_private_forgiveness':
        return _contains_any(value, 'perdao nao cabe',
                             'perdao cabe depois do transito',
                             'perdao e admissivel depois do transito',
                             'perdao pode ser concedido apos o transito')
    if code in ('penal_code_article_106_forgiveness_acceptance',
                'criminal_procedure_article_51_forgiveness_acceptance'):
        return _contains_any(value, 'nao depende de aceitacao',
                             'independe de aceitacao', 'sem aceitacao',
                             'dispensa aceitacao')
    if code == 'penal_code_article_107_v_accepted_forgiveness_extinction':
        return _contains_any(value, 'nao extingue a punibilidade',
                             'nao causa extincao',
                             'nao e causa de extincao',
                             'punibilidade permanece')
    if code == 'clt_articles_462_578_579_582_salary_and_union_deductions':
        return _contains_any(value, 'culpa sem acordo', 'culpa independe',
                             'sem possibilidade previamente acordada',
                             'contribuicao sindical independe',
                             'contribuicao sindical nao exige',
                             'contribuicao sindical e automatica',
                             'dispensa autorizacao previa e expressa')
    if code == 'tst_sumula_342_employee_authorized_deductions':
        return _contains_any(value, 'nao exige autorizacao',
                             'dispensa autorizacao',
                             'sem autorizacao previa', 'mesmo com coacao',
                             'ainda que haja coacao', 'vale com coacao')
    if code == 'law_10820_consigned_payroll_deductions':
        return _contains_any(value, 'nao autoriza desconto',
                             'nao disciplina emprestimo',
                             'independe de autorizacao')
    return False


def _source_metadata_groups_affirmed(
        page, wanted_url, code, groups, affirmed, semantic_clauses,
        clause_explicitly_nonaffirming):
    for source in page.get('official_sources') or []:
        if (source.get('url') or '').strip() != wanted_url:
            continue
        metadata = ' '.join((source.get('name') or '',
                             source.get('anchor_claim') or '')).strip()
        exact = all(any(affirmed(metadata, alternative)
                        for alternative in alternatives)
                    for alternatives in groups)
        if has_relational_source_metadata_rule(code):
            return relational_source_metadata_affirmed(
                code, metadata, semantic_clauses,
                clause_explicitly_nonaffirming)
        return exact
    return False


def has_relational_source_metadata_rule(code):
    return code == 'law_10820_consigned_payroll_deductions' or code in {
        requirement[1]
        for requirements in SOURCE_REQUIREMENTS.values()
        for requirement in requirements
    }


def affirms_law_10820_consigned_loan(
        visible, semantic_clauses, clause_explicitly_nonaffirming):
    for clause in semantic_clauses(visible):
        if (clause_explicitly_nonaffirming(clause) or
                'emprestimo consignado' not in clause or
                not _contains_any(clause, 'lei 10 820', 'lei 10820') or
                not _contains_any(clause, 'e regido', 'regula', 'disciplina',
                                  'e disciplinado', 'segue', 'rege',
                                  'submete se') or
                _contains_any(clause, 'nao e regido', 'nao regula',
                              'nao disciplina', 'nao segue', 'nao rege',
                              'nao se submete')):
            continue
        return True
    return False


def _append_once(values, reason):
    if reason not in values:
        values.append(reason)


def sumula_342_scope_before_contrast(clause):
    indexes = [
        clause.find(marker)
        for marker in (' enquanto ', ' ao passo que ', ' ja o emprestimo',
                       ' e o emprestimo')
        if clause.find(marker) >= 0
    ]
    return clause[:min(indexes)] if indexes else clause


def stale_reasons(
        intent, visible, affirmed, semantic_clauses,
        clause_explicitly_nonaffirming):
    result = []
    for code, alternatives in STALE_RULES.get(intent, ()):
        if any(affirmed(visible, alternative)
               for alternative in alternatives):
            result.append('current_legal_fact_stale_assertion:' + code)

    clauses = semantic_clauses(visible)
    for clause in clauses:
        if clause_explicitly_nonaffirming(clause):
            continue
        code = None
        if intent == 'banc-tempo-maximo-nome-negativado':
            if (_contains_any(clause, 'quinquen', 'cinco anos', '5 anos') and
                    _contains_any(clause, 'comeca', 'inicia',
                                  'passa a correr', 'termo inicial') and
                    _contains_any(
                        clause, 'a partir da inscricao',
                        'a partir dessa inscricao', 'data da inscricao',
                        'na inscricao', 'a partir da inclusao',
                        'data da inclusao', 'na inclusao',
                        'quando o nome e negativado',
                        'data em que o nome e negativado',
                        'a partir da negativacao', 'data da negativacao',
                        'com a negativacao') and
                    not _contains_any(clause, 'nao comeca', 'nao inicia',
                                      'nao passa a correr',
                                      'nao e a negativacao')):
                code = 'credit_listing_five_year_term_from_registration'
        elif intent == 'emp-duplicata-mercantil-vs-servicos':
            if ('duplicata' in clause and
                    _contains_any(clause, 'so e valida', 'somente e valida',
                                  'so vale', 'exige', 'requer') and
                    _contains_any(clause, 'pelo menos 30 dias',
                                  'pelo menos trinta dias',
                                  'prazo minimo de 30 dias',
                                  'prazo minimo de trinta dias',
                                  'prazo nao inferior a 30 dias',
                                  'prazo nao inferior a trinta dias') and
                    not _contains_any(clause, 'nao exige', 'nao requer',
                                      'pode vencer em menos',
                                      'pode ter prazo inferior')):
                code = (
                    'duplicate_article_1_thirty_days_as_universal_'
                    'title_requirement')
        elif intent == 'crim-perdao-do-ofendido':
            if (_contains_any(clause, 'pretensao punitiva',
                              'poder de punir', 'jus puniendi') and
                    _contains_any(clause, 'vitima', 'ofendido',
                                  'querelante') and
                    _contains_any(clause, 'transferida', 'transferido',
                                  'passa a pertencer', 'pertence') and
                    not _contains_any(clause, 'nao e transferida',
                                      'nao se transfere',
                                      'apenas a iniciativa')):
                code = 'private_action_jus_puniendi_transferred_to_victim'
            elif ('perdao' in clause and
                  _contains_any(clause, 'vale', 'produz efeito', 'extingue') and
                  _contains_any(clause, 'sem concordancia', 'sem aceitacao',
                                'independentemente de aceitacao',
                                'mesmo quando o querelado nao concorda') and
                  not _contains_any(clause, 'nao vale sem',
                                    'nao produz efeito sem')):
                code = 'private_action_forgiveness_without_acceptance'
        elif intent == 'trab-descontos-permitidos':
            if (_contains_any(clause, 'dano', 'prejuizo') and
                    _contains_any(clause, 'culpa', 'negligencia') and
                    _contains_any(clause, 'pode descontar', 'pode abater',
                                  'desconto e permitido') and
                    _contains_any(clause, 'sem previsao anterior',
                                  'sem acordo previo', 'mesmo sem previsao',
                                  'independentemente de acordo') and
                    not _contains_any(clause, 'nao pode descontar',
                                      'nao e permitido')):
                code = (
                    'employee_damage_deduction_without_dolo_or_prior_'
                    'fault_agreement')
        if code:
            _append_once(
                result, 'current_legal_fact_stale_assertion:' + code)

    if intent == 'emp-duplicata-mercantil-vs-servicos':
        for clause in clauses:
            if (clause_explicitly_nonaffirming(clause) or
                    'duplicata mercantil' not in clause or
                    not any(part in clause for part in (
                        'prazo nao inferior a 30 dias',
                        'prazo nao inferior a trinta dias',
                        'prazo minimo de 30 dias',
                        'prazo minimo de trinta dias',
                        'prazo de pelo menos 30 dias',
                        'prazo de pelo menos trinta dias',
                        '30 dias no minimo', 'trinta dias no minimo')) or
                    not any(part in clause for part in
                            ('exige prazo', 'exigindo prazo',
                             'requer prazo')) or
                    any(part in clause for part in
                        ('nao exige prazo', 'nao requer prazo',
                         'nao e requisito'))):
                continue
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'duplicate_article_1_thirty_days_as_universal_title_'
                'requirement')
            break

    if intent == 'trab-descontos-permitidos':
        for clause in clauses:
            sumula_scope = sumula_342_scope_before_contrast(clause)
            sumula_attributes_consigned = (
                'sumula 342' in sumula_scope and
                'consignad' in sumula_scope and
                _contains_any(sumula_scope, 'inclui', 'abrange', 'admite',
                              'disciplina', 'considera licit', 'alcanca') and
                not _contains_any(sumula_scope, 'nao inclui', 'nao abrange',
                                  'nao admite', 'nao disciplina',
                                  'nao considera', 'nao alcanca',
                                  'nao emprestimo', 'nao o consignado'))
            consigned_contrast = (
                'emprestimo consignado' in clause and
                _contains_any(clause, 'lei 10 820', 'lei 10820') and
                _contains_any(clause, 'enquanto ', 'e o emprestimo',
                              'ja o emprestimo', 'ao passo que ') and
                _contains_any(clause, 'e regido', 'segue',
                              'disciplina o emprestimo',
                              'e disciplinado'))
            consigned_excluded = (
                _contains_any(clause, 'nao emprestimo consignado',
                              'mas nao emprestimo consignado',
                              'e nao emprestimo consignado') and
                _contains_any(clause, 'plano de saude',
                              'assistencia odontologica',
                              'medico hospitalar'))
            if (clause_explicitly_nonaffirming(clause) or
                    'sumula 342' not in clause or
                    'emprestimo consignado' not in clause or
                    (consigned_contrast and
                     not sumula_attributes_consigned) or
                    consigned_excluded or
                    not any(part in clause for part in
                            ('inclui', 'abrange', 'admite', 'disciplina',
                             'considera licit', 'alcanca')) or
                    any(part in clause for part in
                        ('nao inclui', 'nao abrange', 'nao admite',
                         'nao disciplina', 'nao considera', 'nao alcanca'))):
                continue
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'sumula_342_consigned_loan_misattribution')
            break
        blocks = (visible or '').replace('\r', '\n').split('\n')
        for block in blocks:
            block_clauses = semantic_clauses(block)
            for index, clause in enumerate(block_clauses):
                if (clause_explicitly_nonaffirming(clause) or
                        not any(part in clause for part in
                                ('independe de autorizacao',
                                 'independem de autorizacao',
                                 'dispensa autorizacao',
                                 'nao exige autorizacao'))):
                    continue
                context = clause
                has_union_subject = any(part in clause for part in
                                        ('contribuicao sindical',
                                         'contribuicoes sindicais'))
                refers_to_prior = clause.startswith((
                    'todos ', 'todas ', 'esses descontos ',
                    'essas contribuicoes ', 'tais descontos ',
                    'eles ', 'elas '))
                has_different_explicit_subject = any(
                    part in clause for part in (
                        'inss', 'imposto de renda', 'pensao alimenticia',
                        'descontos legais', 'descontos judiciais'))
                if not has_union_subject:
                    if (not index or not refers_to_prior or
                            has_different_explicit_subject):
                        continue
                    context = block_clauses[index - 1] + ' ' + clause
                if any(part in context for part in
                       ('contribuicao sindical',
                        'contribuicoes sindicais')):
                    _append_once(
                        result,
                        'current_legal_fact_stale_assertion:'
                        'union_contribution_without_prior_'
                        'express_authorization')
                    break
    return result


def reasons(
        page, visible, has_exact_source, affirmed, semantic_clauses,
        clause_explicitly_nonaffirming):
    intent = (page.get('intent_id') or '').strip()
    outcome = OUTCOME_RULES.get(intent)
    if outcome is None:
        return []

    result = []
    for wanted_url, code, metadata_groups in SOURCE_REQUIREMENTS[intent]:
        if not has_exact_source(page, wanted_url):
            result.append('current_legal_fact_source_missing:' + code)
        elif (metadata_groups and
              not _source_metadata_groups_affirmed(
                  page, wanted_url, code, metadata_groups, affirmed,
                  semantic_clauses, clause_explicitly_nonaffirming)):
            result.append(
                'current_legal_fact_source_anchor_missing:' + code)
    if (intent == 'trab-descontos-permitidos' and
            affirms_law_10820_consigned_loan(
                visible, semantic_clauses,
                clause_explicitly_nonaffirming)):
        wanted_url, code, metadata_groups = LAW_10820_CONDITIONAL_SOURCE
        if not has_exact_source(page, wanted_url):
            result.append('current_legal_fact_source_missing:' + code)
        elif not _source_metadata_groups_affirmed(
                page, wanted_url, code, metadata_groups, affirmed,
                semantic_clauses, clause_explicitly_nonaffirming):
            result.append('current_legal_fact_source_anchor_missing:' + code)
    if missing_outcome_groups(
            intent, visible, outcome, affirmed, semantic_clauses,
            clause_explicitly_nonaffirming):
        result.append('current_legal_fact_outcome_missing:' + outcome[0])
    result.extend(stale_reasons(
        intent, visible, affirmed, semantic_clauses,
        clause_explicitly_nonaffirming))
    return result
