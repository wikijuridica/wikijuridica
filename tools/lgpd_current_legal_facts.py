"""Clause-aware LGPD semantic gate shared with internal/v2ingest."""

import re
import urllib.parse


ARTICLE_5_CODE = 'lgpd_article_5_photo_biometric_boundary'
ARTICLE_19_CODE = 'lgpd_article_19_access_deadline_boundary'
CHILD_BASIS_CODE = 'lgpd_child_legal_basis_boundary'
PHOTO_ANPD_NOTE_CODE = 'lgpd_photo_sensitive_context_anpd_note'
CHILD_CONSENT_ARTICLE_14_CODE = 'lgpd_child_consent_article_14_boundary'
SMALL_AGENT_ARTICLE_19_CODE = 'lgpd_small_agent_article_19_deadline_boundary'
ECA_DIGITAL_CONSENT_CODE = 'eca_digital_parental_consent_boundary'
LEGACY_STATUTE_PATH_CODE = 'lgpd_legacy_uncompiled_statute_path'

_STATUTE_PATHS = {
    '/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm',
}
_LEGACY_STATUTE_PATH = '/ccivil_03/_ato2015-2018/2018/lei/l13709.htm'

_ANPD_CHILD_BASIS_PATHS = {
    '/anpd/pt-br/assuntos/noticias/'
    'anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes',
    '/anpd/pt-br/assuntos/noticias/'
    'anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes/enunciado1anpd.pdf',
    '/anpd/pt-br/assuntos/noticias/'
    'anpd-divulga-enunciado-sobre-o-tratamento-de-dados-pessoais-de-criancas-e-adolescentes/enunciado1anpd.pdf/@@download/file',
    '/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/'
    'regulamentacoes_anpd/tratamento_de_dados_de_criancas_e_adolescentes.pdf',
}

_DOU_CHILD_BASIS_PATHS = {
    '/web/dou/-/enunciado-cd/anpd-n-1-de-22-de-maio-de-2023-485306934',
}

_ANPD_PHOTO_NOTE_PATHS = {
    '/anpd/pt-br/centrais-de-conteudo/documentos-tecnicos-orientativos/'
    'sei_anpd-0140555-nota-tecnica.pdf',
}

_ANPD_SMALL_AGENT_PATHS = {
    '/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/'
    'regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022',
}

_ECA_DIGITAL_PATHS = {
    '/ccivil_03/_ato2023-2026/2025/lei/l15211.htm',
}


def reasons(page, visible, norm_key):
    """Return fail-closed legal-fact reasons for an LGPD page."""
    intent = (page.get('intent_id') or '').strip()
    if not intent.startswith('lgpd-'):
        return []

    clauses = _clauses(visible, norm_key)
    result = []
    if _has_legacy_uncompiled_statute_source(page):
        _append_once(
            result,
            'current_legal_fact_source_stale:' + LEGACY_STATUTE_PATH_CODE)
    photo_boundary_relevant = False
    biometric_definition_relevant = False
    article_19_relevant = False
    article_19_deadline_relevant = False
    small_agent_article_19_relevant = False
    child_basis_relevant = False
    child_consent_invoked = False
    eca_digital_consent_relevant = False
    child_page = _page_has_child_context(intent, clauses)
    child_consent_page = _page_has_child_consent_context(intent, clauses)
    previous_clause_had_photo = False
    for clause in clauses:
        ordinary_photo_claim = (
            _photo_ordinary_boundary_context(clause) or
            (previous_clause_had_photo and
             _coreferent_photo_sensitivity_boundary(clause)))
        ordinary_photo_stale = (
            _ordinary_photo_called_sensitive(clause) or
            (previous_clause_had_photo and
             _coreferent_photo_called_sensitive(clause)))
        if ordinary_photo_claim or ordinary_photo_stale:
            photo_boundary_relevant = True
        if ordinary_photo_stale:
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'ordinary_photo_automatically_sensitive')
        if _biometric_definition_context(clause):
            biometric_definition_relevant = True
        if _biometric_definition_misattributed_to_article_11(clause):
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'article_11_misattributed_as_biometric_definition')
        if _article_19_visible_context(clause):
            article_19_relevant = True
        if _article_19_deadline_context(clause):
            article_19_deadline_relevant = True
        if _article_19_misattributed_to_deletion(clause):
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'article_19_fifteen_days_as_general_deletion_deadline')
        generic_code = _article_19_generic_deadline_stale_code(clause)
        if generic_code:
            _append_once(
                result, 'current_legal_fact_stale_assertion:' + generic_code)
        if _small_agent_article_19_context(clause):
            small_agent_article_19_relevant = True
        small_code = _small_agent_article_19_stale_code(clause)
        if small_code:
            _append_once(
                result, 'current_legal_fact_stale_assertion:' + small_code)
        if _eca_digital_consent_context(clause):
            eca_digital_consent_relevant = True
        if (_child_basis_context(child_page, clause) and
                not _eca_digital_consent_context(clause)):
            child_basis_relevant = True
        if _child_consent_called_universal(child_page, clause):
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'child_treatment_consent_as_universal_legal_basis')
        if _child_consent_invoked_as_basis(child_consent_page, clause):
            child_consent_invoked = True
        if _child_biometric_legitimate_interest(clause):
            _append_once(
                result,
                'current_legal_fact_stale_assertion:'
                'child_sensitive_biometric_legitimate_interest_not_article_11_basis')
        previous_clause_had_photo = _clause_has_photo(clause)
    if _article_19_universal_immediate_ignores_small_agent(clauses):
        _append_once(
            result,
            'current_legal_fact_stale_assertion:'
            'article_19_immediate_rule_ignores_small_agent_exception')

    article_5_sources = _article_anchor_evidence_sources(page, 'art5')
    if photo_boundary_relevant or biometric_definition_relevant:
        if not article_5_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' + ARTICLE_5_CODE)
        elif not any(_article_5_biometric_anchor_specific(
                source.get('anchor_claim') or '', norm_key)
                     for source in article_5_sources):
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' + ARTICLE_5_CODE)
    if photo_boundary_relevant:
        photo_sources = _exact_path_sources(
            page, 'www.gov.br', _ANPD_PHOTO_NOTE_PATHS, '')
        if not photo_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' + PHOTO_ANPD_NOTE_CODE)
        elif not any(_anpd_photo_anchor_specific(
                source.get('anchor_claim') or '', norm_key)
                     for source in photo_sources):
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' +
                PHOTO_ANPD_NOTE_CODE)

    article_19_sources = _article_anchor_evidence_sources(page, 'art19')
    article_19_validator = (_article_19_deadline_anchor_specific
                            if article_19_deadline_relevant
                            else _article_19_anchor_specific)
    article_19_specific = any(
        article_19_validator(
            source.get('anchor_claim') or '', norm_key)
        for source in article_19_sources)
    if article_19_relevant:
        if not article_19_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' + ARTICLE_19_CODE)
        elif not article_19_specific:
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' + ARTICLE_19_CODE)
    if (article_19_deadline_relevant and
            not _article_19_complete_declaration_visible(clauses)):
        _append_once(
            result,
            'current_legal_fact_outcome_missing:'
            'lgpd_article_19_complete_declaration_material')

    if small_agent_article_19_relevant:
        small_sources = _exact_path_sources(
            page, 'www.gov.br', _ANPD_SMALL_AGENT_PATHS, '')
        if not small_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' +
                SMALL_AGENT_ARTICLE_19_CODE)
        elif not any(_small_agent_article_19_anchor_specific(
                source.get('anchor_claim') or '', norm_key)
                     for source in small_sources):
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' +
                SMALL_AGENT_ARTICLE_19_CODE)

    if child_basis_relevant:
        child_sources = _child_basis_sources(page)
        if not child_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' + CHILD_BASIS_CODE)
        elif not any(_child_basis_anchor_specific(
                source.get('anchor_claim') or '', norm_key)
                     for source in child_sources):
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' +
                CHILD_BASIS_CODE)
        if not _child_basis_and_best_interest_visible(clauses):
            _append_once(
                result,
                'current_legal_fact_outcome_missing:'
                'lgpd_child_multiple_bases_and_best_interest')

    if child_consent_invoked:
        article_14_sources = _article_anchor_evidence_sources(page, 'art14')
        if not article_14_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' +
                CHILD_CONSENT_ARTICLE_14_CODE)
        elif not any(_article_14_consent_anchor_specific(
                source.get('anchor_claim') or '', norm_key)
                     for source in article_14_sources):
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' +
                CHILD_CONSENT_ARTICLE_14_CODE)
        if not _child_consent_requirements_visible(clauses):
            _append_once(
                result,
                'current_legal_fact_outcome_missing:'
                'lgpd_child_consent_specific_highlighted_parent')

    if eca_digital_consent_relevant:
        eca_sources = _exact_path_sources(
            page, 'www.planalto.gov.br', _ECA_DIGITAL_PATHS, 'art8')
        if not eca_sources:
            eca_sources = _exact_path_sources(
                page, 'planalto.gov.br', _ECA_DIGITAL_PATHS, 'art8')
        if not eca_sources:
            _append_once(
                result,
                'current_legal_fact_source_missing:' +
                ECA_DIGITAL_CONSENT_CODE)
        elif not any(_eca_digital_consent_anchor_specific(
                source.get('anchor_claim') or '', norm_key)
                     for source in eca_sources):
            _append_once(
                result,
                'current_legal_fact_source_anchor_missing:' +
                ECA_DIGITAL_CONSENT_CODE)
    return result


def _child_basis_sources(page):
    result = _exact_path_sources(
        page, 'www.gov.br', _ANPD_CHILD_BASIS_PATHS, '')
    result.extend(_exact_path_sources(
        page, 'www.in.gov.br', _DOU_CHILD_BASIS_PATHS, ''))
    return result


def _exact_path_sources(page, host, paths, fragment):
    result = []
    for source in page.get('official_sources') or []:
        raw_url = (source.get('url') or '').strip()
        try:
            parsed = urllib.parse.urlsplit(raw_url)
            port = parsed.port
        except (TypeError, ValueError):
            continue
        path = parsed.path.lower()
        if path.endswith('/'):
            path = path[:-1]
        if (parsed.scheme.lower() == 'https' and
                parsed.username is None and parsed.password is None and
                port is None and not parsed.query and
                '?' not in raw_url.split('#', 1)[0] and
                (fragment != '' or '#' not in raw_url) and
                parsed.fragment.lower() == fragment and
                (parsed.hostname or '').lower() == host and path in paths):
            result.append(source)
    return result


def _clauses(value, norm_key):
    clauses = []
    for block in re.split(r'[\r\n]+', value or ''):
        # Do not split the legal abbreviation "art." into an artificial
        # sentence boundary, and never turn a question into an assertion.
        safe = re.sub(r'\b(arts?|artigos?)\.', r'\1 ', block,
                      flags=re.IGNORECASE)
        for sentence in re.split(r'(?<=[.!?])\s+', safe):
            sentence = sentence.strip()
            if not sentence or sentence.endswith('?'):
                continue
            for part in re.split(
                    r';|,\s+(?:e|mas|por[eé]m|contudo|entretanto)\s+',
                    sentence, flags=re.IGNORECASE):
                # Go's semantic helper also treats contrast words without a
                # preceding comma as hard clause boundaries.
                for contrast in re.split(
                        r'\s+(?:mas|por[eé]m|contudo|entretanto)\s+',
                        part, flags=re.IGNORECASE):
                    folded = norm_key(contrast)
                    if folded:
                        clauses.append(folded)
    return clauses


def _article_sources(page, article):
    return [source for source in page.get('official_sources') or []
            if _canonical_statute_article(
                source.get('url') or '', article)]


def _article_anchor_evidence_sources(page, article):
    current = _article_sources(page, article)
    if current:
        return current
    return _legacy_article_sources(page, article)


def _legacy_article_sources(page, article):
    return [source for source in page.get('official_sources') or []
            if _canonical_legacy_statute_article(
                source.get('url') or '', article)]


def _fragmento_e_ancora_de_artigo(fragmento):
    """Espelha internal/v2ingest.lgpdFragmentoEAncoraDeArtigo, byte a byte.

    A forma vem do documento REAL: baixado em 2026-08-30, `l13709.htm` traz 357
    ancoras, 351 delas comecando por `art` seguido de digito. `art` sozinho,
    `artigo` e `topo` nao identificam dispositivo e por isso nao contam.
    """
    f = (fragmento or '').strip().lower()
    return f.startswith('art') and len(f) > 3 and f[3].isdigit()


def _has_legacy_uncompiled_statute_source(page):
    """Acusa a citacao ao texto NAO compilado da LGPD -- so quando ela NAO carrega
    ancora de artigo.

    ★ A REGUA PASSOU A SER POR CASO EM 2026-08-30, e a medicao e o motivo:

        l13709.htm          -> 357 ancoras, 351 de artigo
        l13709compilado.htm ->   2 ancoras, ZERO de artigo

    Exigir o compilado em toda citacao deixava 96 paginas de LGPD fora do estoque
    publicavel -- e o remedio prescrito destruia o deep-link, porque o compilado
    nao tem ancora de artigo. Onde a citacao e ao diploma inteiro (61 casos
    medidos, todos ja migrados) o compilado segue sendo o correto.

    Esta funcao e o par Python de `lgpdHasLegacyUncompiledStatuteSource`, e
    `TestLGPDGoPythonAndAuditorParity` compara as duas sobre as mesmas fixturas:
    foi ele que apanhou esta funcao ficando para tras da correcao em Go.
    """
    for source in page.get('official_sources') or []:
        raw_url = (source.get('url') or '').strip()
        try:
            parsed = urllib.parse.urlsplit(raw_url)
            port = parsed.port
        except (TypeError, ValueError):
            continue
        if (parsed.scheme.lower() == 'https' and
                parsed.username is None and parsed.password is None and
                port is None and not parsed.query and
                '?' not in raw_url.split('#', 1)[0] and
                (parsed.hostname or '').lower() in (
                    'planalto.gov.br', 'www.planalto.gov.br') and
                parsed.path.lower() == _LEGACY_STATUTE_PATH and
                not _fragmento_e_ancora_de_artigo(parsed.fragment)):
            return True
    return False


def _canonical_legacy_statute_article(raw_url, article):
    raw_url = (raw_url or '').strip()
    try:
        parsed = urllib.parse.urlsplit(raw_url)
        port = parsed.port
    except (TypeError, ValueError):
        return False
    return (
        parsed.scheme.lower() == 'https' and
        parsed.username is None and parsed.password is None and
        port is None and not parsed.query and
        '?' not in raw_url.split('#', 1)[0] and
        (parsed.hostname or '').lower() in ('planalto.gov.br',
                                             'www.planalto.gov.br') and
        parsed.path.lower() == _LEGACY_STATUTE_PATH and
        parsed.fragment.lower() == article)


def _canonical_statute_article(raw_url, article):
    raw_url = (raw_url or '').strip()
    try:
        parsed = urllib.parse.urlsplit(raw_url)
        port = parsed.port
    except (TypeError, ValueError):
        return False
    return (
        parsed.scheme.lower() == 'https' and
        parsed.username is None and parsed.password is None and
        port is None and not parsed.query and
        '?' not in raw_url.split('#', 1)[0] and
        (parsed.hostname or '').lower() in ('planalto.gov.br',
                                             'www.planalto.gov.br') and
        parsed.path.lower() in _STATUTE_PATHS and
        parsed.fragment.lower() == article)


def _article_5_biometric_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor)):
        return False
    statutory_roll = (
        _contains_any(anchor, 'rol taxativo', 'lista taxativa', 'rol legal',
                      'categorias de dado pessoal sensivel') and
        _contains_any(anchor, 'dado pessoal sensivel',
                      'dados pessoais sensiveis'))
    return (
        statutory_roll or
        ('biometr' in anchor and
         _contains_any(anchor, 'dado pessoal sensivel',
                       'dados pessoais sensiveis', 'categoria sensivel') and
         _contains_any(anchor, 'pessoa natural', 'identificacao individual',
                       'individualizar', 'reconhecimento facial',
                       'vinculado a pessoa', 'vinculada a pessoa')))


def _anpd_photo_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anpd_photo_anchor_negates_context(anchor)):
        return False
    has_photo = _contains_any(
        anchor, 'foto', 'fotografia', 'imagem', 'video', 'audio')
    not_sensitive_by_itself = _contains_any(
        anchor, 'nao e sensivel por si', 'nao sao sensiveis por si',
        'nao e dado pessoal sensivel por si',
        'nao sao dados pessoais sensiveis por si',
        'nao e automaticamente sensivel',
        'nao sao automaticamente sensiveis', 'a principio nao e',
        'a principio nao sao')
    context_can_be_sensitive = (
        'sensivel' in anchor and _contains_any(
            anchor, 'atributo biometrico', 'atributos biometricos',
            'reconhecimento facial', 'conteudo', 'contexto', 'revela dados',
            'revelem dados', 'categoria sensivel'))
    return has_photo and not_sensitive_by_itself and context_can_be_sensitive


def _anpd_photo_anchor_negates_context(anchor):
    return _contains_any(
        anchor, 'contexto nao pode tornar', 'conteudo nao pode tornar',
        'contexto nunca torna', 'conteudo nunca torna',
        'contexto jamais torna', 'conteudo jamais torna',
        'nao pode se tornar sensivel pelo contexto',
        'nao pode se tornar sensivel pelo conteudo',
        'atributo biometrico nao e sensivel',
        'atributos biometricos nao sao sensiveis',
        'reconhecimento facial nao e sensivel')


def _article_19_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor)):
        return False
    simplified_subject = _contains_any(
        anchor, 'confirmacao da existencia', 'confirmacao de existencia',
        'existencia de tratamento', 'acesso aos dados',
        'acesso a dados pessoais', 'acesso aos dados pessoais', 'resposta')
    simplified = (
        simplified_subject and
        'simplific' in anchor and 'imediat' in anchor)
    return simplified or _article_19_deadline_anchor_specific(
        value, norm_key)


def _article_19_deadline_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor) or
            _article_19_material_negated(anchor)):
        return False
    return (
        _contains_any(anchor, 'declaracao completa',
                      'declaracao clara e completa') and
        _contains_any(anchor, '15 dias', 'quinze dias') and
        'origem' in anchor and 'inexistencia de registro' in anchor and
        'criterios' in anchor and 'finalidade' in anchor and
        _contains_any(anchor, 'data do requerimento',
                      'contado do requerimento',
                      'contados do requerimento',
                      'a partir do requerimento') and
        not _contains_any(anchor, 'dias uteis', 'dia util'))


def _child_basis_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor)):
        return False
    children = _contains_any(
        anchor, 'crianca', 'criancas', 'adolescente', 'adolescentes')
    article_7 = _contains_any(anchor, 'art 7', 'artigo 7', 'arts 7')
    article_11 = _contains_any(
        anchor, 'art 11', 'artigo 11', 'arts 7 ou 11',
        'artigos 7 e 11', 'artigos 7 ou 11')
    permits_bases = _contains_any(
        anchor, 'podem ser tratad', 'podera ser realizad',
        'pode ser realizad', 'podem ter dados tratad',
        'pode se apoiar', 'podem se apoiar', 'hipoteses legais previstas',
        'bases legais previstas')
    return (children and article_7 and article_11 and permits_bases and
            'melhor interesse' in anchor and
            not _child_basis_material_negated(anchor))


def _article_14_consent_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor)):
        return False
    return (
        'consentimento' in anchor and 'especific' in anchor and
        _child_consent_highlight_affirmed(anchor) and
        _contains_any(anchor, 'um dos pais', 'pelo menos um dos pais',
                      'responsavel legal') and
        not _child_consent_material_negated(anchor))


def _child_consent_highlight_affirmed(value):
    # A raiz livre ``destac`` também casa o declarativo ``destacou`` e o
    # infinitivo negado ``não exige destacar``. Aceite só a locução material
    # ou os particípios que qualificam o consentimento.
    return _contains_any(
        value, 'em destaque', 'destacado', 'destacada',
        'destacados', 'destacadas')


def _small_agent_article_19_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor)):
        return False
    small = _contains_any(
        anchor, 'agente de tratamento de pequeno porte',
        'agentes de tratamento de pequeno porte', 'microempresa',
        'empresa de pequeno porte', 'startup')
    complete = (
        _contains_any(anchor, 'prazo em dobro', '30 dias', 'trinta dias') and
        _contains_any(anchor, 'declaracao completa', 'art 19 ii',
                      'artigo 19 ii'))
    simplified = (
        _contains_any(anchor, 'declaracao simplificada',
                      'formato simplificado', 'art 19 i', 'artigo 19 i') and
        _contains_any(anchor, 'ate 15 dias', 'ate quinze dias'))
    return small and complete and simplified


def _eca_digital_consent_anchor_specific(value, norm_key):
    anchor = norm_key(value)
    if (not anchor or _anchor_disclaims_rule(anchor) or
            _anchor_negates_material_rule(anchor)):
        return False
    return (
        _contains_any(anchor, 'download de aplicativo',
                      'download de aplicativos', 'baixar aplicativo') and
        'consentimento' in anchor and 'livre e informado' in anchor and
        _contains_any(anchor, 'pais ou responsaveis', 'responsavel legal'))


def _anchor_disclaims_rule(anchor):
    return _contains_any(
        anchor, 'nao trata do dispositivo', 'nao disciplina',
        'sem relacao com', 'alheio ao artigo', 'anchor generico')


def _anchor_negates_material_rule(anchor):
    return _contains_any(
        anchor, 'nao e dado pessoal sensivel',
        'nao sao dados pessoais sensiveis', 'nao integra a categoria',
        'nao precisa', 'nao deve', 'nao pode', 'nao permite', 'nao admite',
        'nao sera fornecid', 'bases legais sao proibid',
        'base legal e proibid', 'demais bases legais sao proibid',
        'outras bases legais sao proibid', 'sem melhor interesse')


def _photo_ordinary_boundary_context(clause):
    return (_photo_classification_asserted(clause) and 'sensiv' in clause and
            not _photo_sensitive_by_content_qualified(clause) and
            not _photo_biometric_use_qualified(clause))


def _coreferent_photo_sensitivity_boundary(clause):
    return (not _clause_has_photo(clause) and 'sensiv' in clause and
            _photo_sensitivity_denied(clause))


def _ordinary_photo_called_sensitive(clause):
    if (not _photo_classification_asserted(clause) or not _contains_any(
            clause, 'dado sensivel', 'dado pessoal sensivel',
            'dados sensiveis', 'categoria sensivel')):
        return False
    if (_photo_sensitivity_denied(clause) or
            _photo_biometric_use_qualified(clause) or
            _photo_sensitive_by_content_qualified(clause)):
        return False
    return True


def _coreferent_photo_called_sensitive(clause):
    if (_clause_has_photo(clause) or _photo_sensitivity_denied(clause) or
            _photo_biometric_use_qualified(clause) or
            _photo_sensitive_by_content_qualified(clause)):
        return False
    coreference = _contains_any(
        clause, 'ela ', 'essa imagem', 'esse retrato', 'isso ',
        'a mesma imagem')
    sensitive = _contains_any(
        clause, 'dado sensivel', 'dado pessoal sensivel',
        'dados sensiveis', 'categoria sensivel')
    assertion = _contains_any(
        clause, ' e dado', ' se torna', ' torna se', ' vira', ' constitui',
        ' integra', ' passa a ser')
    return coreference and sensitive and assertion


def _photo_sensitive_by_content_qualified(clause):
    sensitive_content = _contains_any(
        clause, 'dado de saude', 'dados de saude', 'laudo medico',
        'exame medico', 'prontuario', 'origem racial', 'origem etnica',
        'conviccao religiosa', 'opiniao politica', 'vida sexual',
        'dado genetico', 'dados geneticos')
    context_link = _contains_any(
        clause, 'conteudo', 'contem', 'revela', 'incorpora', 'documento',
        'laudo', 'exame')
    return sensitive_content and context_link


def _biometric_definition_context(clause):
    if (not ('biometr' in clause and 'sensiv' in clause) or
            not _contains_any(clause, 'dado', 'informacao', 'atributo') or
            _contains_any(clause, 'nao e sensivel',
                          'nao constitui dado sensivel', 'e falso que',
                          'incorreto dizer')):
        return False
    if (_contains_any(clause, 'art 5', 'artigo 5') and
            _contains_any(clause, 'lista taxativamente', 'rol taxativo',
                          'lista de forma fechada')):
        return True
    if (_contains_any(clause, 'dado sensivel como',
                      'dados sensiveis como') and
            not _contains_any(clause, 'operacoes de alto risco como',
                              'tratamento massivo')):
        return True
    tokens = clause.split()
    for sensitive_index, token in enumerate(tokens):
        if not token.startswith('sensiv'):
            continue
        for biometric_index in range(
                sensitive_index + 1,
                min(len(tokens), sensitive_index + 7)):
            if not tokens[biometric_index].startswith('biometr'):
                continue
            frame = ' '.join(tokens[sensitive_index:biometric_index + 1])
            if ' ou ' not in frame and 'ao lado' not in frame:
                return True
    for biometric_index, token in enumerate(tokens):
        if not token.startswith('biometr'):
            continue
        for sensitive_index in range(
                biometric_index + 1,
                min(len(tokens), biometric_index + 13)):
            if tokens[sensitive_index].startswith('sensiv'):
                return True
    return False


def _biometric_definition_misattributed_to_article_11(clause):
    return (
        _biometric_definition_context(clause) and
        _clause_cites_article_number(clause, '11') and
        _contains_any(clause, 'classific', 'define', 'consider',
                      'constitui', 'integra') and
        not _contains_any(clause, 'nao classifica', 'nao define',
                          'incorreto', 'e falso'))


def _photo_classification_asserted(clause):
    tokens = clause.split()
    photo_indexes = []
    category_indexes = []
    for index, token in enumerate(tokens):
        if (token.startswith(('foto', 'fotograf', 'imagem', 'retrato')) or
                token in ('rosto', 'face')):
            photo_indexes.append(index)
        if (token.startswith(('pessoal', 'sensivel', 'biometr')) and
                index > 0 and
                tokens[index - 1].startswith(('dado', 'categoria'))):
            category_indexes.append(index)
    for photo_index in photo_indexes:
        for category_index in category_indexes:
            left, right = sorted((photo_index, category_index))
            if right - left > 12:
                continue
            frame = tokens[max(0, left - 4):min(len(tokens), right + 2)]
            if (_tokens_have_prefix(
                    frame, 'classific', 'consider', 'constitu', 'represent',
                    'trat', 'torn', 'vir', 'entr', 'integr') or
                    _frame_has_copular_category(frame)):
                return True
    return False


def _frame_has_copular_category(tokens):
    for index, token in enumerate(tokens):
        if token not in ('e', 'sao'):
            continue
        following = index + 1
        if (following < len(tokens) and
                tokens[following] in ('um', 'uma')):
            following += 1
        if (following < len(tokens) and
                tokens[following].startswith(('dado', 'categoria'))):
            return True
    return False


def _clause_has_photo(clause):
    tokens = clause.split()
    return (_tokens_have_prefix(tokens, 'foto', 'fotograf', 'imagem',
                                'retrato') or
            any(token in ('rosto', 'face') for token in tokens))


def _photo_sensitivity_denied(clause):
    return _contains_any(
        clause, 'nao e dado sensivel', 'nao e um dado sensivel',
        'nao e automaticamente dado sensivel',
        'nao se torna dado sensivel',
        'nao transforma a foto em dado sensivel',
        'nao transforma a imagem em dado sensivel',
        'nao significa dado sensivel', 'nem toda foto e dado sensivel',
        'nem toda imagem e dado sensivel', 'so e dado sensivel quando',
        'somente e dado sensivel quando', 'apenas e dado sensivel quando',
        'e incorreto tratar toda foto', 'e falso que toda foto',
        'e falso que a foto', 'e falso que a imagem')


def _photo_biometric_use_qualified(clause):
    technical = _contains_any(
        clause, 'reconhecimento facial', 'identificacao automatizada',
        'identificacao automatica', 'autenticacao biometrica',
        'mapeamento facial', 'template biometrico',
        'processada para identificar', 'usada para identificar',
        'utilizada para identificar', 'leitor de digital',
        'leitura de digital', 'digital ou face', 'face ou digital',
        'sistema de acesso biometrico', 'controle de acesso biometrico',
        'cadastro biometrico')
    return technical and _contains_any(
        clause, 'biometr', 'sensivel', 'digital', 'face')


def _article_19_visible_context(clause):
    fifteen_days = _contains_any(clause, '15 dias', 'quinze dias')
    if _clause_cites_lgpd_article_19(clause):
        if _article_19_other_paragraph_only(clause):
            return False
        return _contains_any(
            clause, 'simplific', 'imediat', 'declaracao completa',
            'declaracao clara e completa', 'confirmacao',
            'acesso aos dados', 'acesso a dados pessoais',
            'origem dos dados', 'criterios utilizados',
            'finalidade do tratamento', 'pedido do titular',
            'requerimento do titular', 'elimin', 'exclu')
    return fifteen_days and _contains_any(
        clause, 'declaracao completa', 'declaracao clara e completa',
        'confirmacao de tratamento', 'confirmacao da existencia',
        'origem dos dados', 'criterios utilizados',
        'finalidade do tratamento', 'pedido do titular',
        'requerimento do titular')


def _article_19_deadline_context(clause):
    return (not _contractual_deadline_context(clause) and
            not _article_19_deadline_qualification_only(clause) and
            _contains_any(clause, '15 dias', 'quinze dias') and
            (_clause_cites_lgpd_article_19(clause) or _contains_any(
                clause, 'declaracao completa', 'declaracao clara e completa',
                'origem dos dados', 'criterios utilizados',
                'finalidade do tratamento', 'confirmacao',
                'pedido do titular', 'requerimento do titular', 'elimin',
                'exclu', 'apag', 'remov')))


def _article_19_other_paragraph_only(clause):
    paragraph_3 = (
        _contains_any(clause, 'art 19 3', 'artigo 19 3', 'paragrafo 3',
                      ' 3 do art 19') and
        _contains_any(clause, 'portabilidade', 'formato reutilizavel',
                      'copia eletronica', 'dados em formato'))
    paragraph_4 = (
        _contains_any(clause, 'art 19 4', 'artigo 19 4', 'paragrafo 4',
                      ' 4 do art 19') and
        _contains_any(clause, 'setor', 'setorial', 'prazos diferenciados',
                      'autoridade nacional', 'anpd'))
    paragraph_2 = (
        _contains_any(clause, 'art 19 2', 'artigo 19 2', 'paragrafo 2',
                      ' 2 do art 19') and
        _contains_any(clause, 'gratuit', 'custo', 'taxa',
                      'meio eletronico', 'forma impressa'))
    return paragraph_2 or paragraph_3 or paragraph_4


def _article_19_deadline_qualification_only(clause):
    if _article_19_other_paragraph_only(clause):
        return True
    if (_contains_any(clause, 'inciso ii que trata',
                      'inciso ii e que comporta',
                      'e que comporta o prazo') and
            _contains_any(clause, 'confirmacao', 'formato simplificado',
                          'resposta imediata', 'declaracao completa',
                          'declaracao clara e completa')):
        return True
    return _contains_any(
        clause, 'nao ha um numero magico de dias unico para todo pedido',
        'nao ha numero magico de dias unico para todo pedido',
        'nao existe prazo unico para todo pedido',
        'nao ha prazo unico para qualquer pedido')


def _article_19_universal_immediate_ignores_small_agent(clauses):
    joined = ' '.join(clauses)
    if (_contains_any(
            joined, 'agente de tratamento de pequeno porte',
            'agentes de tratamento de pequeno porte', 'microempresa',
            'empresa de pequeno porte', 'resolucao 2') and
            _contains_any(joined, 'ate 15 dias', 'ate quinze dias',
                          'prazo de 15 dias', 'prazo de quinze dias')):
        return False
    for start in range(len(clauses)):
        for width in (1, 2, 3):
            if start + width > len(clauses):
                continue
            window = ' '.join(clauses[start:start + width])
            subject = _contains_any(
                window, 'confirmacao', 'formato simplificado',
                'resposta simplificada')
            immediate = _contains_any(window, 'imediat', 'instantane')
            universal = _contains_any(
                window, 'nao ha margem de dias', 'sem margem de dias',
                'instantanea sempre', 'instantaneo sempre',
                'sempre instantanea', 'sempre instantaneo',
                'sem qualquer prazo', 'sem excecao')
            if (subject and immediate and universal and
                    not _contains_any(window, 'nao e instantane',
                                      'nao e imediat')):
                return True
    return False


def _article_19_complete_declaration_visible(clauses):
    for start, clause in enumerate(clauses):
        for width in (1, 2):
            if start + width > len(clauses):
                continue
            window = ' '.join(clauses[start:start + width])
            if (_contains_any(window, 'declaracao completa',
                              'declaracao clara e completa') and
                    _contains_any(window, '15 dias', 'quinze dias') and
                    'origem' in window and
                    'inexistencia de registro' in window and
                    'criterios' in window and 'finalidade' in window and
                    _contains_any(window, 'data do requerimento',
                                  'contado do requerimento',
                                  'contados do requerimento',
                                  'a partir do requerimento') and
                    not _contains_any(window, 'dias uteis', 'dia util') and
                    not _article_19_material_negated(window)):
                return True
    return False


def _article_19_material_negated(value):
    return _contains_any(
        value, 'nao informa', 'nao indica', 'nao contem',
        'nao precisa informar', 'nao precisa indicar',
        'sem informar a origem', 'sem indicar a origem',
        'dispensa a origem', 'origem nao e informada',
        'criterios nao sao informados', 'finalidade nao e informada',
        'inexistencia de registro nao e informada',
        'nao existe declaracao completa',
        'declaracao completa nao se aplica',
        'prazo de 15 dias nao se aplica',
        'prazo de quinze dias nao se aplica', 'e falso que',
        'nao e verdade que', 'incorreto dizer que')


def _page_has_child_context(intent, clauses):
    if _contains_any(
            (intent or '').strip(), 'crianc', 'adolesc', 'infantil'):
        return True
    return any(_clause_has_material_child_context(clause)
               for clause in clauses)


def _page_has_child_consent_context(intent, clauses):
    joined = ' '.join(clauses)
    return (
        _contains_any((intent or '').strip(), 'crianc', 'aluno', 'escola',
                      'filho', 'infantil') or
        _contains_any(joined, 'crianca', 'criancas', 'aluno', 'filho'))


def _child_basis_context(child_page, clause):
    if (not child_page or not _clause_has_material_child_context(clause) or
            _civil_image_authorization_context(clause) or
            _child_basis_disclaimed(clause)):
        return False
    if _contains_any(
            clause, 'base legal', 'bases legais', 'hipotese legal',
            'hipoteses legais', 'interesse legitimo', 'art 7', 'artigo 7',
            'arts 7', 'art 11', 'artigo 11', 'arts 11'):
        return True
    consent = _contains_any(clause, 'consentimento', 'autorizacao')
    statutory = (
        _contains_any(clause, 'art 14', 'artigo 14', 'lei 13 709',
                      'lei 13709') or
        ('lgpd' in clause and
         _contains_any(clause, 'tratamento', 'dados', 'base')))
    data_treatment = _contains_any(
        clause, 'tratamento de dados', 'tratar dados', 'dados de crianca',
        'dados de criancas', 'dado de crianca', 'dado de menor',
        'dados de menor', 'dados de menores') or (
            'uso de imagem' in clause and
            _contains_any(clause, 'tratamento', 'tratar'))
    return (consent and (statutory or data_treatment) and
            _contains_any(clause, 'tratamento', 'tratar', 'exige',
                          'exigida', 'obrig', 'necessari', 'indispens',
                          'depende', 'somente', 'apenas', 'so permite',
                          'unica', 'deve ser', 'precisa ser'))


def _clause_has_material_child_context(clause):
    if _contains_any(
            clause, 'crianca', 'criancas', 'adolescente', 'adolescentes',
            'infancia', 'infantil'):
        return True
    return _contains_any(
        clause, 'menor de idade', 'menores de idade', 'titular menor',
        'titulares menores', 'dados de menor', 'dados de menores',
        'dado de menor', 'interesse do menor', 'protecao do menor',
        'um dos pais', 'pelo menos um dos pais', 'pais ou responsaveis',
        'responsavel legal')


def _child_basis_disclaimed(clause):
    return _contains_any(
        clause, 'nao e um problema de', 'nao e caso de', 'nao se aplica',
        'nao substitui', 'diferente de uma empresa', 'nao e a lgpd',
        'nao pela lgpd', 'nao e base legal', 'sem base legal aqui nao',
        'poder familiar', 'vara de familia', 'segredo de justica',
        'processo judicial')


def _child_consent_called_universal(child_page, clause):
    if (not _child_basis_context(child_page, clause) or
            _eca_digital_consent_context(clause) or
            not _contains_any(clause, 'consentimento', 'autorizacao') or
            _child_consent_rule_qualified(clause) or
            _child_consent_universality_denied(clause)):
        return False
    return _contains_any(
        clause, 'exige consentimento', 'exigir consentimento',
        'consentimento obrigatorio', 'consentimento e obrigatorio',
        'autorizacao obrigatoria', 'autorizacao e obrigatoria',
        'autorizacao especifica passa a ser exigida',
        'somente com consentimento', 'apenas com consentimento',
        'somente com autorizacao', 'apenas com autorizacao', 'unica base',
        'sempre depende de consentimento', 'consentimento e indispensavel',
        'consentimento indispensavel', 'so permite tratar', 'so pode tratar',
        'e necessaria autorizacao', 'autorizacao e necessaria')


def _child_consent_rule_qualified(clause):
    return _contains_any(
        clause, 'quando o consentimento', 'quando a base',
        'se o consentimento', 'se a base', 'caso o consentimento',
        'caso a base', 'consentimento como base', 'base adotada',
        'base escolhida', 'base invocada',
        'controlador optar pelo consentimento')


def _child_consent_universality_denied(clause):
    return _contains_any(
        clause, 'consentimento nao e a unica base',
        'consentimento nao e obrigatorio em todo',
        'nao exige sempre consentimento',
        'nao depende sempre de consentimento',
        'nao e indispensavel para todo')


def _child_consent_invoked_as_basis(child_page, clause):
    return (child_page and not _adolescent_only_context(clause) and
            'consentimento' in clause and
            _child_consent_rule_qualified(clause))


def _adolescent_only_context(clause):
    has_adolescent = _contains_any(clause, 'adolescente', 'adolescentes')
    has_child = _contains_any(
        clause, 'crianca', 'criancas', 'infancia', 'infantil',
        'menor de 12', 'menores de 12')
    return has_adolescent and not has_child


def _child_basis_and_best_interest_visible(clauses):
    for start, clause in enumerate(clauses):
        for width in (1, 2):
            if start + width > len(clauses):
                continue
            window = ' '.join(clauses[start:start + width])
            article_7 = _contains_any(
                window, 'art 7', 'artigo 7', 'arts 7')
            article_11 = _contains_any(
                window, 'art 11', 'artigo 11', 'arts 7 ou 11',
                'artigos 7 e 11', 'artigos 7 ou 11')
            permits = _contains_any(
                window, 'podem ser tratad', 'podera ser realizad',
                'pode ser realizad', 'podem ter dados tratad',
                'pode se apoiar', 'podem se apoiar',
                'consentimento nao e a unica base',
                'hipoteses legais previstas')
            if (article_7 and article_11 and permits and
                    'melhor interesse' in window and
                    not _child_basis_material_negated(window)):
                return True
    return False


def _child_basis_material_negated(value):
    return _contains_any(
        value, 'art 7 nao', 'artigo 7 nao', 'art 11 nao',
        'artigo 11 nao', 'nao se aplica', 'nao pode ser realizad',
        'nao podem ser realizad', 'nao pode ser tratad',
        'nao podem ser tratad', 'nao pode se apoiar',
        'nao podem se apoiar', 'nunca pode se apoiar',
        'nunca podem se apoiar', 'jamais pode se apoiar',
        'jamais podem se apoiar', 'hipotese alguma pode se apoiar',
        'hipotese alguma podem se apoiar', 'nao podem ser usados',
        'nao pode ser usado', 'nao autorizam o tratamento',
        'nao autoriza o tratamento', 'bases legais sao proibid',
        'demais bases legais sao proibid',
        'outras bases legais sao proibid', 'e falso que',
        'nao e verdade que', 'incorreto dizer que')


def _child_consent_requirements_visible(clauses):
    for start, clause in enumerate(clauses):
        if ('consentimento' not in clause or
                not _child_consent_rule_qualified(clause)):
            continue
        window = ' '.join(clauses[start:start + 2])
        if ('especific' in window and
                _child_consent_highlight_affirmed(window) and
                _contains_any(window, 'um dos pais',
                              'pelo menos um dos pais',
                              'responsavel legal') and
                not _child_consent_material_negated(window)):
            return True
    return False


def _child_consent_material_negated(value):
    return _contains_any(
        value, 'nao precisa ser especific',
        'nao precisa estar em destaque', 'nao precisa ser destac',
        'nao sera especific', 'nao sera em destaque', 'nao sera destac',
        'nao e especific', 'nao e destac', 'sem destaque',
        'sem qualquer destaque', 'sem estar destac', 'sem ser destac',
        'nem em destaque', 'nem destac', 'dispensa o destaque',
        'dispensa estar destac', 'dispensa ser destac',
        'dispensa consentimento', 'generico basta',
        'consentimento generico', 'aceite generico', 'escondid',
        'tacito basta', 'presumido basta', 'e falso que',
        'nao e verdade que', 'incorreto dizer que')


def _civil_image_authorization_context(clause):
    return (
        _contains_any(clause, 'codigo civil', 'art 20', 'artigo 20',
                      'direito de imagem', 'uso comercial', 'fins comerciais',
                      'anuncio comercial', 'propaganda comercial',
                      'poder familiar', 'guarda', 'vara de familia') and
        not _contains_any(clause, 'base legal da lgpd', 'art 14',
                          'artigo 14'))


def _eca_digital_consent_context(clause):
    return (
        'consentimento' in clause and _contains_any(
            clause, 'download de aplicativo', 'download de aplicativos',
            'baixar aplicativo', 'loja de aplicativos') and
        _contains_any(clause, 'crianca', 'criancas', 'adolescente',
                      'adolescentes', 'pais', 'responsavel'))


def _child_biometric_legitimate_interest(clause):
    return (
        'biometr' in clause and 'sensiv' in clause and
        'interesse legitimo' in clause and _contains_any(
            clause, 'crianca', 'criancas', 'adolescente', 'adolescentes',
            'aluno', 'escola') and not _contains_any(
                clause, 'nao autoriza', 'nao permite', 'nao e base',
                'incorreto', 'e falso'))


def _article_19_misattributed_to_deletion(clause):
    if (not _contains_any(clause, '15 dias', 'quinze dias') or
            not _clause_has_deletion(clause) or
            _deletion_deadline_denied(clause) or
            _contractual_deadline_context(clause)):
        return False
    return _contains_any(
        clause, 'prazo', 'referencia', 'em ate 15 dias',
        'em ate quinze dias', 'em 15 dias', 'em quinze dias',
        'dentro de 15 dias', 'dentro de quinze dias', 'tem 15 dias',
        'tem quinze dias', 'da 15 dias', 'da quinze dias',
        'quinze dias para', '15 dias para', 'e de quinze dias',
        'e de 15 dias')


def _article_19_generic_deadline_stale_code(clause):
    if (not _contains_any(clause, '15 dias', 'quinze dias') or
            _contractual_deadline_context(clause)):
        return ''
    if _article_19_deadline_qualification_only(clause):
        return ''
    if (_contains_any(clause, 'dias uteis', 'dia util') and
            _article_19_visible_context(clause)):
        return 'article_19_fifteen_business_days'
    if (_contains_any(clause, 'qualquer pedido', 'todo pedido',
                      'todos os pedidos', 'qualquer requerimento') and
            (_clause_cites_lgpd_article_19(clause) or 'lgpd' in clause)):
        return 'article_19_fifteen_days_as_generic_response_deadline'
    if (_contains_any(clause, 'confirmar a existencia',
                      'confirmacao da existencia',
                      'confirmacao de existencia') and
            not _contains_any(clause, 'declaracao completa',
                              'declaracao clara e completa')):
        return 'article_19_fifteen_days_as_confirmation_deadline'
    if _contains_any(clause, 'a partir da resposta',
                     'a partir do recebimento',
                     'da confirmacao do recebimento'):
        return 'article_19_fifteen_days_wrong_starting_event'
    return ''


def _small_agent_article_19_context(clause):
    small = _contains_any(
        clause, 'agente de tratamento de pequeno porte',
        'agentes de tratamento de pequeno porte', 'microempresa',
        'microempresas', 'empresa de pequeno porte',
        'empresas de pequeno porte', 'startup', 'startups')
    return small and _contains_any(
        clause, 'art 19', 'artigo 19', 'declaracao completa',
        'declaracao simplificada', 'formato simplificado', 'confirmacao',
        'acesso aos dados', '15 dias', 'quinze dias', '30 dias',
        'trinta dias')


def _small_agent_article_19_stale_code(clause):
    small = _small_agent_article_19_context(clause)
    if (small and _contains_any(clause, 'simplific', 'confirmacao') and
            'imediat' in clause and not _contains_any(
                clause, 'regra geral', 'para os demais', 'exceto',
                'nao e imediat')):
        return 'small_agent_simplified_immediate_ignores_resolution_2'
    if (small and _contains_any(
            clause, 'declaracao completa', 'art 19 ii', 'artigo 19 ii') and
            _contains_any(clause, '15 dias', 'quinze dias') and
            not _contains_any(clause, 'prazo em dobro', '30 dias',
                              'trinta dias')):
        return 'small_agent_complete_declaration_fifteen_days_ignores_double_deadline'
    if (_contains_any(clause, 'simplific', 'confirmacao') and
            'imediat' in clause and _contains_any(
                clause, 'sempre', 'qualquer empresa', 'nao ha margem',
                'instantanea', 'sem excecao')):
        return 'article_19_immediate_rule_ignores_small_agent_exception'
    return ''


def _contractual_deadline_context(clause):
    return (
        _contains_any(clause, 'por contrato', 'prazo contratual',
                      'acordo contratual', 'sla', 'politica da empresa',
                      'compromisso voluntario') and
        not _contains_any(clause, 'segundo a lgpd', 'art 19 da lgpd',
                          'artigo 19 da lgpd'))


def _clause_cites_lgpd_article_19(clause):
    if not _clause_cites_article_number(clause, '19'):
        return False
    if _contains_any(clause, 'lgpd', 'lei 13 709', 'lei 13709'):
        return True
    return not _contains_any(
        clause, 'marco civil', 'codigo de defesa do consumidor',
        'codigo penal', 'codigo civil', 'lei 12 965', 'lei 12965',
        'lei 8 078', 'lei 8078', 'outra lei', 'propriedade industrial')


def _clause_cites_article_number(clause, article):
    tokens = clause.split()
    for index in range(len(tokens) - 1):
        if (tokens[index] in ('art', 'artigo') and
                tokens[index + 1] == article):
            if (index + 2 < len(tokens) and len(tokens[index + 2]) == 1 and
                    'a' <= tokens[index + 2] <= 'z'):
                return False
            return True
    return False


def _clause_has_deletion(clause):
    return _tokens_have_prefix(
        clause.split(), 'elimin', 'exclu', 'apag', 'remov')


def _deletion_deadline_denied(clause):
    return _contains_any(
        clause, 'nao fixa prazo', 'nao estabelece prazo',
        'nao cria prazo', 'nao e prazo', 'nao vale para eliminacao',
        'nao se aplica a eliminacao', 'nao alcanca a eliminacao',
        'nao vale para exclusao', 'nao se aplica a exclusao',
        'nao alcanca a exclusao', 'nao e para excluir',
        'nao e para eliminar', 'nao confunda com eliminacao',
        'nao confunda com exclusao', 'sem prazo geral',
        'nao ha prazo geral', 'e falso que',
        'e incorreto dizer')


def _tokens_have_prefix(tokens, *prefixes):
    return any(token.startswith(prefixes) for token in tokens)


def _contains_any(value, *candidates):
    return any(candidate in value for candidate in candidates)


def _append_once(items, value):
    if value not in items:
        items.append(value)
