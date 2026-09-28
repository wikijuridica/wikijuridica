"""Clause-aware current-law gate for STF Tema 987 after 2026 embargoes."""

import re
import urllib.parse


TARGET_INTENTS = {
    'banc-golpe-telefone-falso-google-anuncio',
    'banc-whatsapp-clonado-pedindo-dinheiro',
    'banc-golpe-falso-leilao-veiculos',
    'banc-site-clonado-loja-falsa',
    'banc-golpe-romance-relacionamento-virtual',
    'banc-instagram-invadido-venda-falsa',
    'banc-golpe-aluguel-imovel-falso',
    'cons-golpe-em-compra-de-usado-entre-pessoas',
    'imob-golpe-anuncio-falso-aluguel',
}

INAUTHENTIC_ACCOUNT_RULE_INTENTS = {
    'banc-whatsapp-clonado-pedindo-dinheiro',
    'banc-golpe-romance-relacionamento-virtual',
    'banc-instagram-invadido-venda-falsa',
}

PAID_BOUNDARY_INTENTS = {
    'banc-golpe-telefone-falso-google-anuncio',
    'banc-golpe-falso-leilao-veiculos',
    'banc-site-clonado-loja-falsa',
    'banc-golpe-aluguel-imovel-falso',
    'imob-golpe-anuncio-falso-aluguel',
}

PRIVATE_BOUNDARY_INTENTS = {
    'banc-whatsapp-clonado-pedindo-dinheiro',
    'banc-instagram-invadido-venda-falsa',
}

_FINAL_OFFICIAL_SOURCE_URLS = {
    (
        'portal.stf.jus.br',
        '/jurisprudenciaRepercussao/verAndamentoProcesso.asp',
        'incidente=5160549&numeroTema=987',
    ),
    (
        'noticias.stf.jus.br',
        '/postsnoticias/plataformas-terao-60-dias-para-implementar-medidas-estruturais-decide-stf/',
        '',
    ),
}

_CURRENT_RULE_RELATION = (
    r'(?:tese(?: atual| final)?|orientacao(?: atual| final)?|'
    r'formulacao final|regime(?: atual| final)?)'
)
_CONTINUING_NOUN_RELATION = (
    r'(?:ato|atos|conduta|condutas|fato|fatos|situacao|situacoes)'
)
_CONTINUING_PAIR_RELATION = (
    r'(?:' + _CONTINUING_NOUN_RELATION +
    r'\s+continuad[oa]s?\s+(?:e|ou)\s+(?:' +
    _CONTINUING_NOUN_RELATION + r'\s+)?permanentes?|' +
    _CONTINUING_NOUN_RELATION +
    r'\s+permanentes?\s+(?:e|ou)\s+(?:' +
    _CONTINUING_NOUN_RELATION + r'\s+)?continuad[oa]s?)'
)
_FINAL_JUDGMENT_RELATION = (
    r'(?:coisa julgada|decisao transitada em julgado|'
    r'decisoes transitadas em julgado|transito em julgado)'
)
_DATE_EFFECT_RELATION_PATTERNS = (
    re.compile(
        r'\b' + _CURRENT_RULE_RELATION +
        r'\s+(?:vale|vigora|produz efeitos?|passa a valer|se aplica|'
        r'passa a produzir efeitos?|aplica se|incide)\s+'
        r'(?:desde|a partir de)\s+'
        r'(?:5 de agosto de 2025|05 08 2025|5 8 2025)\b'),
)
_CONTINUING_RELATION_PATTERNS = (
    re.compile(
        r'\b' + _CURRENT_RULE_RELATION +
        r'\s+(?:rege|alcanca|passa a reger)\s+(?:os?|as?)?\s*' +
        _CONTINUING_PAIR_RELATION + r'\b'),
    re.compile(
        r'\b' + _CURRENT_RULE_RELATION +
        r'\s+(?:aplica se|se aplica)\s+(?:a|aos|as)\s+' +
        _CONTINUING_PAIR_RELATION + r'\b'),
    re.compile(
        r'\b' + _CURRENT_RULE_RELATION + r'\s+incide\s+sobre\s+' +
        _CONTINUING_PAIR_RELATION + r'\b'),
    re.compile(
        r'\b' + _CONTINUING_PAIR_RELATION +
        r'\s+(?:recebe|recebem|segue|seguem)\s+'
        r'(?:a|ao|as|os|pela|pelo)\s+' + _CURRENT_RULE_RELATION + r'\b'),
    re.compile(
        r'\b' + _CONTINUING_PAIR_RELATION +
        r'\s+(?:e|sao|fica|ficam|permanece|permanecem)\s+'
        r'(?:regid[oa]s?|submetid[oa]s?|alcancad[oa]s?)\s+'
        r'(?:a|ao|as|os|pela|pelo)\s+' + _CURRENT_RULE_RELATION + r'\b'),
)
_FINAL_JUDGMENT_RELATION_PATTERNS = (
    re.compile(
        r'\b' + _FINAL_JUDGMENT_RELATION +
        r'\s+(?:e|sao|sera|serao|foi|foram|seja|sejam|deve ser|'
        r'devem ser|deve permanecer|devem permanecer|deve continuar|'
        r'devem continuar|fica|ficam|segue|seguem|permanece|permanecem|'
        r'continua|continuam)\s+'
        r'(?:preservad[oa]s?|protegid[oa]s?|resguardad[oa]s?|'
        r'respeitad[oa]s?|ressalvad[oa]s?)\b'),
    re.compile(
        r'\b' + _CURRENT_RULE_RELATION +
        r'\s+(?:preserva|preservam|protege|protegem|resguarda|resguardam|'
        r'respeita|respeitam|ressalva|ressalvam)\s+(?:a|as|o)\s+' +
        _FINAL_JUDGMENT_RELATION + r'\b'),
)
_RELATION_ADVERSATIVE_PATTERN = re.compile(
    r'\b(?:mas|porem|contudo|todavia|entretanto)\b')
_RELATION_REPORT_DENIAL_PATTERN = re.compile(
    r'\bnao se pode (?:afirmar|concluir|dizer|sustentar) que'
    r'(?: a| o| as| os)?$')


def _contains_any(value, *candidates):
    return any(candidate in value for candidate in candidates)


def _has_affirmed_relation(clause, patterns):
    """Match one subject-predicate relation with polarity scoped to its span."""
    for pattern in patterns:
        for match in pattern.finditer(clause):
            matched = f' {match.group(0)} '
            if _contains_any(
                    matched, ' nao ', ' jamais ', ' nunca ', ' sem ',
                    ' deixa de ', ' deixam de ', ' deixou de ',
                    ' deixaram de '):
                continue
            prefix_start = 0
            for boundary in _RELATION_ADVERSATIVE_PATTERN.finditer(
                    clause, 0, match.start()):
                prefix_start = boundary.end()
            prefix = clause[prefix_start:match.start()].strip()
            if (_meta_denied(prefix) or
                    _RELATION_REPORT_DENIAL_PATTERN.search(prefix) or
                    any(prefix == candidate or prefix.endswith(f' {candidate}')
                   for candidate in (
                       'nao', 'jamais', 'nunca', 'sem', 'nao mais',
                       'deixa de', 'deixam de', 'deixou de',
                       'deixaram de'))):
                continue
            return True
    return False


def _outcome_blocks(page, norm_key):
    values = [page.get('opening', '')]
    values.extend(section.get('text', '')
                  for section in page.get('sections', []) or [])
    values.extend(item.get('a', '') for item in page.get('faq', []) or [])
    blocks = []
    for value in values:
        folded = norm_key(value)
        if not folded:
            continue
        sentence_safe = re.sub(r'\b(art|artigo)\.', r'\1 ', value,
                               flags=re.IGNORECASE)
        clauses = [norm_key(part) for part in
                   re.split(r'[.!?;\r\n]+', sentence_safe)
                   if norm_key(part)]
        blocks.append({'folded': folded, 'clauses': clauses})
    return blocks


def _context_folded(page, norm_key):
    values = [page.get('title', ''), page.get('meta_description', ''),
              page.get('h1', ''), page.get('opening', '')]
    for section in page.get('sections', []) or []:
        values.extend((section.get('heading', ''), section.get('text', '')))
    for item in page.get('faq', []) or []:
        values.extend((item.get('q', ''), item.get('a', '')))
    return norm_key(' '.join(value for value in values if value))


def _has_final_official_source(page):
    for source in page.get('official_sources') or []:
        try:
            parsed = urllib.parse.urlsplit((source.get('url') or '').strip())
            port = parsed.port
        except (TypeError, ValueError):
            continue
        if (parsed.scheme != 'https' or parsed.username is not None or
                parsed.password is not None or port is not None or
                parsed.fragment):
            continue
        identity = ((parsed.hostname or '').lower(), parsed.path,
                    parsed.query)
        if identity in _FINAL_OFFICIAL_SOURCE_URLS:
            return True
    return False


def _has_final_embargo_context(blocks):
    for block in blocks:
        for clause in block['clauses']:
            if ('embargo' in clause and '2026' in clause and
                    _contains_any(clause, 'encerr', 'concluid', 'julgad',
                                  'transito em julgado', 'forma final',
                                  'tese final') and
                    not _embargo_pending(clause) and
                    not _meta_denied(clause)):
                return True
    return False


def _has_affirmed_2025_date_effect(clause):
    return _has_affirmed_relation(clause, _DATE_EFFECT_RELATION_PATTERNS)


def _only_2025_reference_is_effective_date(clause):
    if not _has_affirmed_2025_date_effect(clause):
        return False
    for date in ('5 de agosto de 2025', '05 08 2025', '5 8 2025'):
        start = 0
        while True:
            index = clause.find(date, start)
            if index < 0:
                break
            prefix = clause[:index].rstrip()
            temporal_start = (
                prefix == 'desde' or prefix.endswith(' desde') or
                prefix == 'a partir de' or prefix.endswith(' a partir de'))
            remainder = clause[:index] + clause[index + len(date):]
            if temporal_start and '2025' not in remainder:
                return True
            start = index + len(date)
    return False


def _merits_presented_as_final_without_embargo(
        blocks, final_embargo_context):
    for block in blocks:
        for clause in block['clauses']:
            if _meta_denied(clause):
                continue
            if ('embargo' in clause and '2026' in clause and
                    _embargo_pending(clause)):
                return True
            if '2025' not in clause:
                continue
            if (final_embargo_context and
                    _only_2025_reference_is_effective_date(clause)):
                continue
            if _contains_any(clause, 'decisao final', 'tese final',
                             'concluid', 'encerrad', 'transito em julgado'):
                return True
            if (_contains_any(clause, 'decidid', 'julgad', 'fixad') and
                    not _contains_any(clause, 'merito original',
                                      'julgamento original',
                                      'primeira decisao',
                                      'antes dos embargos')):
                return True
    return False


def _has_modulation(blocks):
    has_date_effect = False
    has_continuing = False
    has_final_judgment = False
    for block in blocks:
        for clause in block['clauses']:
            if _has_affirmed_2025_date_effect(clause):
                has_date_effect = True
            if _has_affirmed_relation(
                    clause, _CONTINUING_RELATION_PATTERNS):
                has_continuing = True
            if _has_affirmed_relation(
                    clause, _FINAL_JUDGMENT_RELATION_PATTERNS):
                has_final_judgment = True
    return has_date_effect and has_continuing and has_final_judgment


def _has_paid_assertion(blocks):
    for block in blocks:
        folded = block['folded']
        if (_contains_any(
                folded, 'anuncio pago', 'anuncio patrocinado',
                'resultado patrocinado', 'publicidade paga',
                'publicidade remunerada', 'veiculacao remunerada',
                'midia patrocinada', 'link patrocinado', 'post impulsionado',
                'impulsionamento pago',
                'conteudo impulsionado', 'rede artificial de distribuicao',
                'rede artificial de perfis') and
                _contains_any(folded, 'plataforma', 'provedor', 'servico',
                              'responsabil', 'presunc') and
                not _contains_any(folded, 'nao era anuncio pago',
                                  'sem publicidade paga',
                                  'nao houve impulsionamento',
                                  'nao houve rede artificial',
                                  'sem rede artificial')):
            return True
    return False


def _has_paid_context(context):
    return (_contains_any(
        context, 'anuncio pago', 'anuncio patrocinado',
        'resultado patrocinado', 'publicidade paga',
        'publicidade remunerada', 'veiculacao remunerada',
        'midia patrocinada', 'link patrocinado', 'post impulsionado',
        'impulsionamento pago',
        'conteudo impulsionado', 'rede artificial de distribuicao',
        'rede artificial de perfis') and not _contains_any(
            context, 'nao era anuncio pago', 'sem publicidade paga',
            'nao houve impulsionamento', 'nao houve rede artificial',
            'sem rede artificial'))


def _has_complete_paid_rule(blocks):
    has_presumption = False
    has_notice_independence = False
    has_diligence = False
    for block in blocks:
        for clause in block['clauses']:
            paid_surface = _contains_any(
                clause, 'anuncio pago', 'anuncio patrocinado',
                'resultado patrocinado', 'resultados patrocinados',
                'publicidade paga', 'publicidade remunerada',
                'veiculacao remunerada', 'midia patrocinada',
                'link patrocinado', 'post impulsionado',
                'impulsionamento pago', 'conteudo impulsionado',
                'rede artificial de distribuicao',
                'rede artificial de perfis')
            platform_actor = _contains_any(
                clause, 'plataforma', 'provedor', 'servico', 'empresa')
            presumption = 'presuncao relativa de culpa' in clause
            actor_index = _index_any(
                clause, 'plataforma', 'provedor', 'servico', 'empresa')
            presumption_index = clause.find('presuncao relativa de culpa')
            actor_linked = (
                actor_index >= 0 and presumption_index >= 0 and
                actor_index < presumption_index) or _contains_any(
                    clause, 'presuncao relativa de culpa da plataforma',
                    'presuncao relativa de culpa do provedor',
                    'presuncao relativa de culpa do servico',
                    'presuncao relativa de culpa da empresa')
            if (paid_surface and platform_actor and presumption and
                    actor_linked and not _meta_denied(clause) and
                    not _contains_any(
                        clause, 'nao ha presuncao', 'sem presuncao',
                        'presuncao nao', 'nao gera presuncao',
                        'nao assume presuncao', 'nao tem presuncao',
                        'nao fica sujeita a presuncao',
                        'presuncao do anunciante')):
                has_presumption = True
            independence_index = _index_any(
                clause, 'independentemente de notificacao',
                'mesmo sem notificacao', 'nao depende de notificacao',
                'sem exigir notificacao', 'dispensa aviso previo',
                'sem necessidade de aviso previo')
            notice_linked = ('presunc' in clause or
                             (actor_index >= 0 and
                              independence_index > actor_index) or
                             _contains_any(
                                 clause, 'responsabilidade da plataforma',
                                 'responsabilidade do provedor'))
            if (independence_index >= 0 and notice_linked and
                    not _contains_any(clause, 'nao e independentemente',
                                      'nao dispensa aviso') and
                    not _meta_denied(clause)):
                has_notice_independence = True
            rebuttal = _contains_any(
                clause, 'afast', 'elid', 'refut', 'derrub', 'desconstitu')
            proof = _contains_any(clause, 'prova', 'provar', 'demonstra')
            diligent = ('diligent' in clause and _contains_any(
                clause, 'tempestiv', 'tempo razoavel', 'imediat'))
            content_action = _contains_any(
                clause, 'retir', 'remov', 'indispon', 'preven', 'imped')
            proof_index = _index_any(clause, 'prova', 'provar', 'demonstra')
            wrong_actor_index = _index_any(
                clause, 'vitima', 'usuario', 'anunciante', 'banco')
            wrong_actor_controls_proof = (
                wrong_actor_index >= 0 and wrong_actor_index < proof_index and
                wrong_actor_index > actor_index)
            if (platform_actor and actor_index >= 0 and proof_index >= 0 and
                    actor_index < proof_index and rebuttal and proof and diligent and
                    content_action and not wrong_actor_controls_proof and
                    not _contains_any(
                        clause, 'vitima deve provar', 'vitima pode afastar',
                        'vitima consegue afastar', 'usuario deve provar',
                        'usuario pode afastar', 'anunciante deve provar',
                        'anunciante pode afastar', 'banco deve provar',
                        'banco pode afastar', 'diligencia e irrelevante',
                        'nao afasta', 'jamais afasta',
                        'nao consegue afast', 'nao pode afast') and
                    not _meta_denied(clause)):
                has_diligence = True
    return has_presumption and has_notice_independence and has_diligence


def _has_stale_paid_responsibility_presumption(blocks):
    """Reject the pre-embargo responsibility-presumption formulation."""
    for block in blocks:
        for clause in block['clauses']:
            paid_surface = _contains_any(
                clause, 'anuncio pago', 'anuncio patrocinado',
                'resultado patrocinado', 'resultados patrocinados',
                'publicidade paga', 'publicidade remunerada',
                'veiculacao remunerada', 'midia patrocinada',
                'link patrocinado', 'post impulsionado',
                'impulsionamento pago', 'conteudo impulsionado',
                'rede artificial de distribuicao',
                'rede artificial de perfis')
            platform_actor = _contains_any(
                clause, 'plataforma', 'provedor', 'servico', 'empresa')
            legacy = _contains_any(
                clause, 'presuncao de responsabilidade',
                'presuncao relativa de responsabilidade',
                'presuncao relativa de sua responsabilidade',
                'responsabilidade presumida',
                'responsabilidade da plataforma e presumida',
                'responsabilidade da plataforma fica presumida',
                'presume se a responsabilidade')
            negated = _contains_any(
                clause, 'nao ha presuncao', 'sem presuncao',
                'presuncao nao', 'nao gera presuncao',
                'nao assume presuncao', 'nao tem presuncao',
                'nao fica sujeita a presuncao',
                'responsabilidade nao e presumida',
                'responsabilidade da plataforma nao e presumida')
            if (paid_surface and platform_actor and legacy and
                    not negated and not _meta_denied(clause)):
                return True
    return False


def _has_paid_notice_prerequisite(blocks):
    for block in blocks:
        for clause in block['clauses']:
            if (not _contains_any(
                    clause, 'anuncio pago', 'anuncio patrocinado',
                    'resultado patrocinado', 'publicidade paga',
                    'publicidade remunerada', 'veiculacao remunerada',
                    'midia patrocinada', 'link patrocinado',
                    'post impulsionado', 'impulsionamento pago',
                    'rede artificial de distribuicao') or
                    not _contains_any(clause, 'notific', 'avis')):
                continue
            if _contains_any(
                    clause, 'independentemente de notificacao',
                    'mesmo sem notificacao', 'nao depende de notificacao',
                    'sem exigir notificacao'):
                continue
            if _contains_any(
                    clause, 'depende de notificacao', 'exige notificacao',
                    'somente apos notificacao', 'so apos notificacao',
                    'quando a plataforma e notificada',
                    'responsavel apos notificacao',
                    'notificacao e requisito', 'notificacao e condicao',
                    'depois de a vitima avisar',
                    'depois que a vitima avisa',
                    'so gera responsabilidade depois de avis',
                    'aviso e requisito', 'aviso e condicao'):
                return True
    return False


def _has_private_assertion(blocks):
    for block in blocks:
        if (_contains_any(
                block['folded'], 'comunicacoes interpessoais privadas',
                'mensagens interpessoais privadas', 'mensagens privadas',
                'conversas individuais sigilosas',
                'trocas privadas entre usuarios',
                'conversas privadas entre usuarios', 'mensageria privada',
                'chat privado', 'mensagens diretas privadas',
                'conversa no direct') and _contains_any(
                    block['folded'], 'art 19', 'artigo 19', 'ordem judicial',
                    'plataforma', 'provedor', 'responsabil')):
            return True
    return False


def _has_private_context(context):
    return _contains_any(
        context, 'comunicacoes interpessoais privadas',
        'mensagens interpessoais privadas', 'mensagens privadas',
        'conversas individuais sigilosas', 'trocas privadas entre usuarios',
        'conversas privadas entre usuarios', 'mensageria privada',
        'chat privado', 'mensagens diretas privadas',
        'conversa no direct')


def _has_private_boundary(blocks):
    for block in blocks:
        for clause in block['clauses']:
            private = _contains_any(
                clause, 'comunicacoes interpessoais privadas',
                'mensagens interpessoais privadas', 'mensagens privadas',
                'conversas individuais sigilosas',
                'trocas privadas entre usuarios',
                'conversas privadas entre usuarios', 'mensageria privada',
                'chat privado', 'mensagens diretas privadas',
                'conversa no direct')
            article = _contains_any(clause, 'art 19', 'artigo 19')
            order = _contains_any(
                clause, 'ordem judicial', 'decisao judicial',
                'ordem do judiciario')
            required = _contains_any(
                clause, 'exig', 'depende', 'pressupoe', 'somente apos',
                'continua a')
            negated = _contains_any(
                clause, 'nao exige', 'nao depende', 'dispensa ordem',
                'sem ordem judicial', 'ordem judicial jamais',
                'ordem judicial nao e necessaria',
                'nao estao sujeitas ao art 19', 'nao para elas',
                'nao para as mensagens', 'nao se aplica as mensagens',
                'apenas para publicacoes abertas',
                'somente para publicacoes abertas',
                'para publicacoes abertas nao para')
            private_index = _index_any(
                clause, 'comunicacoes interpessoais privadas',
                'mensagens interpessoais privadas', 'mensagens privadas',
                'conversas individuais sigilosas',
                'trocas privadas entre usuarios',
                'conversas privadas entre usuarios', 'mensageria privada',
                'chat privado', 'mensagens diretas privadas',
                'conversa no direct')
            article_index = _index_any(clause, 'art 19', 'artigo 19')
            order_index = _index_any(
                clause, 'ordem judicial', 'decisao judicial',
                'ordem do judiciario')
            if (private and article and order and required and
                    private_index >= 0 and article_index > private_index and
                    order_index > private_index and not negated and
                    not _meta_denied(clause)):
                return True
    return False


def _has_invaded_assertion(blocks):
    return any(
        'conta' in block['folded'] and _contains_any(
            block['folded'], 'invadid', 'tomad', 'sequestrad') and
        _contains_any(block['folded'], 'conta inautentica',
                      'cadastro inautentico', 'cadastro falso',
                      'conta falsa', 'perfil falso')
        for block in blocks)


def _has_invaded_boundary(blocks):
    for block in blocks:
        for clause in block['clauses']:
            if (not ('conta' in clause and _contains_any(
                    clause, 'invadid', 'tomad', 'sequestrad') and
                    _contains_any(clause, 'conta inautentica',
                                  'cadastro inautentico', 'cadastro falso',
                                  'conta falsa', 'perfil falso'))):
                continue
            positive = _contains_any(
                clause, 'nao se confunde', 'e diferente', 'e distinta',
                'difere de', 'distingue se de')
            negative = _contains_any(
                clause, 'nao e diferente', 'nao e distinta', 'nao difere',
                'equivale a', 'e o mesmo que') or (
                    'se confunde com' in clause and
                    'nao se confunde com' not in clause)
            if positive and not negative and not _meta_denied(clause):
                return True
    return False


def _has_inauthentic_assertion(blocks):
    return any(
        _contains_any(block['folded'], 'conta inautentica',
                      'cadastro inautentico', 'cadastro falso',
                      'conta falsa', 'perfil falso') and
        _contains_any(block['folded'], 'plataforma', 'rede social',
                      'provedor') and _contains_any(
                          block['folded'], 'responsabil', 'ciencia', 'omissao',
                          'notific', 'denunci') for block in blocks)


def _has_inauthentic_rule(blocks):
    for block in blocks:
        for clause in block['clauses']:
            account = _contains_any(
                clause, 'conta inautentica', 'cadastro inautentico',
                'cadastros inautenticos', 'cadastro falso',
                'cadastros falsos', 'conta falsa', 'perfil falso')
            platform = _contains_any(
                clause, 'plataforma', 'rede social', 'provedor', 'servico')
            account_notice = _contains_any(
                clause, 'conta inautentica denunci',
                'cadastro inautentico denunci',
                'cadastros inautenticos denunci',
                'cadastro falso denunci', 'cadastros falsos denunci',
                'conta falsa denunci', 'perfil falso denunci')
            platform_notice = _contains_any(
                clause, 'plataforma avisada', 'plataforma notificada',
                'plataforma ciente', 'rede social avisada',
                'rede social notificada', 'rede social ciente',
                'provedor avisado', 'provedor notificado', 'provedor ciente',
                'servico avisado', 'servico notificado', 'servico ciente')
            notice = account_notice or platform_notice
            omission = _contains_any(
                clause, 'omissao', 'falta de providencia', 'nao remov',
                'nao retir', 'deixou de agir')
            platform_index = _index_any(
                clause, 'plataforma', 'rede social', 'provedor', 'servico')
            omission_index = _index_any(
                clause, 'omissao', 'omiss', 'nao remov', 'nao retir',
                'deixou de agir')
            wrong_actor_index = _index_any(
                clause, 'vitima', 'usuario', 'anunciante', 'banco')
            wrong_actor_controls_omission = (
                wrong_actor_index >= 0 and
                wrong_actor_index < omission_index and
                wrong_actor_index > platform_index)
            wrong = _contains_any(
                clause, 'ordem judicial e requisito',
                'somente com ordem judicial',
                'so responde com ordem judicial',
                'apenas responde com ordem judicial',
                'depende de ordem judicial', 'nunca e responsabilizada',
                'jamais responde', 'nao responde mesmo', 'nao teve ciencia',
                'nao tem ciencia', 'sem ciencia', 'nao permaneceu omiss',
                'nao houve omissao', 'omissao da vitima',
                'ciencia da vitima', 'plataforma denunciou a vitima')
            if (account and platform and notice and omission and
                    platform_index >= 0 and omission_index > platform_index and
                    not wrong_actor_controls_omission and not wrong and
                    not _meta_denied(clause)):
                return True
    return False


def _has_marketplace_assertion(blocks):
    return any(
        _contains_any(block['folded'], 'marketplace',
                      'plataforma de comercio eletronico',
                      'intermediario digital de vendas') and _contains_any(
            block['folded'], 'cdc', 'consumidor', 'responsabil',
            'intermedeia', 'intermedia', 'pagamento', 'garantia') and
        _contains_any(block['folded'], 'classificado', 'mero hospeda',
                      'conteudo de terceiro', 'tema 987', 'art 19')
        for block in blocks)


def _has_marketplace_boundary(blocks):
    marketplace_current = False
    classified_current = False
    for block in blocks:
        for clause in block['clauses']:
            market_function = _contains_any(
                clause, 'intermedeia a venda', 'intermedia a venda',
                'participa da contratacao', 'processa o pagamento',
                'recebe o pagamento', 'oferece garantia',
                'organiza a entrega', 'resolve conflitos')
            cdc_affirmed = ('cdc' in clause and _contains_any(
                clause, 'segue', 'aplica', 'submete', 'responde segundo',
                'incide') and not _contains_any(
                    clause, 'nao segue', 'nao se aplica', 'nao incide') and
                not _meta_denied(clause))
            market_index = _index_any(
                clause, 'marketplace', 'plataforma de comercio eletronico',
                'intermediario digital de vendas')
            function_index = _index_any(
                clause, 'intermedeia a venda', 'intermedia a venda',
                'participa da contratacao', 'processa o pagamento',
                'recebe o pagamento', 'oferece garantia',
                'organiza a entrega', 'resolve conflitos')
            if (market_index >= 0 and function_index > market_index and
                    market_function and cdc_affirmed):
                marketplace_current = True
            classified = (_contains_any(
                clause, 'mero classificado', 'mural eletronico',
                'site de classificados') and _contains_any(
                    clause, 'apenas hospeda', 'somente hospeda',
                    'apenas exibe', 'mero hospedeiro'))
            general = (_contains_any(
                clause, 'regime geral', 'conteudo de terceiro',
                'ciencia e omissao') and _contains_any(
                    clause, 'segue', 'aplica', 'submete'))
            if (classified and general and 'segue o cdc' not in clause and
                    not _meta_denied(clause)):
                classified_current = True
    return marketplace_current and classified_current


def _has_general_assertion(blocks):
    return any(
        _contains_any(block['folded'], 'conteudo de terceiro',
                      'anuncio organico', 'resultado organico',
                      'resultados organicos', 'exibicao organica',
                      'publicacao fraudulenta') and _contains_any(
                          block['folded'], 'plataforma', 'provedor',
                          'regime geral', 'responsabil', 'ciencia', 'omissao')
        for block in blocks)


def _has_general_rule(blocks):
    has_notice_omission = False
    has_specific_notice = False
    has_diligent_response_boundary = False
    has_reasonable_doubt_boundary = False
    for block in blocks:
        context = _contains_any(
            block['folded'], 'conteudo de terceiro', 'anuncio organico',
            'resultado organico', 'resultados organicos', 'exibicao organica',
            'publicacao fraudulenta', 'mero classificado')
        if not context:
            continue
        for clause in block['clauses']:
            notice = _contains_any(
                clause, 'ciencia', 'aviso', 'denuncia', 'notificacao')
            omission = _contains_any(
                clause, 'omissao', 'falta de providencia',
                'nao remover', 'nao retirar', 'demora')
            general_relation = _contains_any(
                clause, 'regime geral', 'conteudo de terceiro',
                'anuncio organico', 'resultado organico',
                'resultados organicos', 'exibicao organica',
                'publicacao fraudulenta', 'mero classificado')
            platform_index = _index_any(
                clause, 'plataforma', 'provedor', 'servico',
                'mero classificado', 'hospedagem')
            notice_index = _index_any(
                clause, 'ciencia', 'aviso', 'denuncia', 'notificacao')
            wrong_actor_index = _index_any(
                clause, 'vitima', 'usuario', 'anunciante', 'banco')
            actor_linked = (platform_index >= 0 and
                            (platform_index < notice_index or _contains_any(
                                clause, 'ciencia e omissao da plataforma',
                                'ciencia da plataforma',
                                'omissao da plataforma')))
            wrong_actor_controls_notice = (
                wrong_actor_index >= 0 and wrong_actor_index < notice_index and
                (platform_index < 0 or wrong_actor_index > platform_index))
            wrong = _contains_any(
                clause, 'somente depois de ordem judicial',
                'apenas com ordem judicial', 'nunca responde mesmo avisada',
                'nao houve omissao', 'sem omissao', 'nao teve ciencia',
                'sem ciencia', 'omissao da vitima', 'ciencia da vitima',
                'omissao do banco', 'ciencia do banco')
            if (general_relation and notice and omission and actor_linked and
                    not wrong_actor_controls_notice and not wrong and
                    not _meta_denied(clause)):
                has_notice_omission = True
            identifies_content = _contains_any(
                clause, 'identifique suficientemente o conteudo',
                'identifica suficientemente o conteudo',
                'conteudo suficientemente identificado',
                'indicacao especifica do conteudo',
                'individualize a url ou a publicacao',
                'individualize o link ou a publicacao',
                'aponte com precisao o post',
                'aponte com precisao o conteudo',
                'descreva precisamente o anuncio',
                'indique de modo preciso qual anuncio')
            identifies_illegality = _contains_any(
                clause, 'ilicitude apontada', 'indique a ilicitude',
                'identifique a ilicitude', 'razoes da ilicitude',
                'explique por que e ilicito',
                'explique por que e ilicita',
                'exponha a razao da ilicitude',
                'fundamente a alegada ilicitude',
                'expor por que seria ilicito',
                'expor por que seria ilicita')
            diligent_removal = _contains_any(
                clause, 'remocao diligente em tempo razoavel',
                'agir diligentemente em tempo razoavel',
                'atuar diligentemente em tempo razoavel',
                'providencia diligente em tempo razoavel',
                'providencia cuidadosa e tempestiva para retirada',
                'resposta diligente dentro de prazo razoavel',
                'retirada cuidadosa e tempestiva',
                'providencia efetiva em prazo razoavel')
            if (general_relation and notice and identifies_content and
                    identifies_illegality and not _meta_denied(clause)):
                has_specific_notice = True
            if (general_relation and platform_index >= 0 and omission and
                    diligent_removal and not _meta_denied(clause)):
                has_diligent_response_boundary = True
            if ('duvida razoavel' in clause and 'ilicitude' in clause and
                    _contains_any(clause, 'analise qualificada',
                                  'avaliacao qualificada',
                                  'exame qualificado',
                                  'avaliacao fundamentada') and
                    not _contains_any(clause, 'nao ha duvida razoavel',
                                      'duvida razoavel e irrelevante') and
                    not _meta_denied(clause)):
                has_reasonable_doubt_boundary = True
    return (has_notice_omission and has_specific_notice and
            has_diligent_response_boundary and
            has_reasonable_doubt_boundary)


def _platform_liability_assertion(blocks):
    """Require the platform-liability relation inside one outcome block."""
    for block in blocks:
        folded = block['folded']
        has_platform = _contains_any(
            folded, 'plataforma', 'provedor', 'rede social', 'marketplace',
            'site de classificados')
        has_liability = _contains_any(
            folded, 'responsabil', 'indeniz', 'dever de reparar',
            'reparacao civil')
        if (has_platform and has_liability and _contains_any(
                folded, 'tema 987', 'art 19 do marco civil',
                'conteudo de terceiro')):
            return True
    return False


def _append(out, reason):
    if reason not in out:
        out.append(reason)


def _meta_denied(clause):
    return _contains_any(
        clause, 'e falso que', 'e mentira que', 'nao e verdade que',
        'nao procede que', 'nao corresponde a verdade que',
        'nao e correto afirmar que', 'e incorreto afirmar que',
        'e equivocada a afirmacao de que')


def _index_any(value, *candidates):
    indexes = [value.find(candidate) for candidate in candidates]
    indexes = [index for index in indexes if index >= 0]
    return min(indexes) if indexes else -1


def _embargo_pending(clause):
    return 'embargo' in clause and _contains_any(
        clause, 'nao foi encerr', 'nao foram encerr',
        'jamais foi encerr', 'jamais foram encerr', 'ainda nao encerr',
        'nao foi conclu', 'nao foram concluid', 'ainda nao concluid',
        'continuava pendente', 'continuavam pendentes',
        'permanece pendente', 'permanecem pendentes',
        'ainda estava pendente', 'ainda estavam pendentes',
        'embargo em curso', 'embargos em curso', 'sem encerramento',
        'sem encerrar', 'segue sem encerr', 'seguem sem encerr',
        'continua sem encerr', 'continuam sem encerr')


def reasons(page, folded, has_source_url_part, norm_key):
    """Return clause-aware blockers; compatibility args are intentionally ignored."""
    del folded, has_source_url_part
    intent = (page.get('intent_id') or '').strip()
    blocks = _outcome_blocks(page, norm_key)
    context = _context_folded(page, norm_key)
    paid = (_has_paid_assertion(blocks) or
            (intent in PAID_BOUNDARY_INTENTS and _has_paid_context(context)))
    private = (_has_private_assertion(blocks) or
               (intent in PRIVATE_BOUNDARY_INTENTS and
                _has_private_context(context)))
    marketplace = (_has_marketplace_assertion(blocks) or
                   (intent == 'cons-golpe-em-compra-de-usado-entre-pessoas' and
                    'marketplace' in context))
    invaded = _has_invaded_assertion(blocks)
    inauthentic = (intent in INAUTHENTIC_ACCOUNT_RULE_INTENTS or
                   _has_inauthentic_assertion(blocks))
    general = _has_general_assertion(blocks)
    relevant = (intent in TARGET_INTENTS or paid or private or marketplace or
                invaded or inauthentic or general or
                _platform_liability_assertion(blocks))
    if not relevant:
        return []

    out = []
    if not _has_final_official_source(page):
        _append(out, 'current_legal_fact_source_missing:stf_tema_987_final_2026')
    final_embargo_context = _has_final_embargo_context(blocks)
    if _merits_presented_as_final_without_embargo(
            blocks, final_embargo_context):
        _append(out, 'current_legal_fact_stale_assertion:tema_987_2025_merit_presented_as_final')
    if not final_embargo_context:
        _append(out, 'current_legal_fact_outcome_missing:tema_987_2026_final_embargo_context')
    if not _has_modulation(blocks):
        _append(out, 'current_legal_fact_outcome_missing:tema_987_modulation_2025_continuing_final_judgments')
    if paid:
        if _has_stale_paid_responsibility_presumption(blocks):
            _append(
                out,
                'current_legal_fact_stale_assertion:'
                'tema_987_paid_ad_responsibility_presumption')
        if _has_paid_notice_prerequisite(blocks):
            _append(out, 'current_legal_fact_stale_assertion:tema_987_paid_ad_notice_prerequisite')
        if not _has_complete_paid_rule(blocks):
            _append(out, 'current_legal_fact_outcome_missing:tema_987_paid_ad_rebuttable_presumption')
    if private and not _has_private_boundary(blocks):
        _append(out, 'current_legal_fact_stale_assertion:tema_987_private_message_extrajudicial_only')
    if invaded and not _has_invaded_boundary(blocks):
        _append(out, 'current_legal_fact_stale_assertion:tema_987_hacked_account_equated_to_inauthentic')
    if inauthentic and not _has_inauthentic_rule(blocks):
        _append(out, 'current_legal_fact_outcome_missing:tema_987_inauthentic_account_notice_omission')
    if marketplace and not _has_marketplace_boundary(blocks):
        _append(out, 'current_legal_fact_outcome_missing:tema_987_marketplace_cdc_boundary')
    if general and not _has_general_rule(blocks):
        _append(out, 'current_legal_fact_outcome_missing:tema_987_general_notice_omission_rule')
    return out
