#!/usr/bin/env python3
"""Corrige por CAS as nove paginas ativas do shard imobiliario-10.

As oito intencoes consolidadas no imobiliario-05 sao tombstones imutaveis:
esta transacao preserva suas linhas byte a byte e valida o hash de cada uma.
"""

import argparse
import datetime
import hashlib
import json
import os
import posixpath
import re
import tempfile
import unicodedata
import urllib.parse


TARGET = "data/editorial/v2_pages/imobiliario-10.jsonl"
INITIAL_SHA256 = "ae179872299403d9cd6dacac2d107e9ca0cae1d6cf19e1791999801d0538a013"
EXPECTED_SHA256 = "277ae857df0a75cfc631c2ad4d36e016d62eba6aea6cf0100e3bbee5d4c84bf3"
FINAL_SHA256 = "e20e6accdff5ba7a6c3637a41b904acb4dd4cf0771e28047e3e97ecffb6fd334"
CHECKED_AT = "2026-07-11"

ACTIVE_INTENTS = {
    "imob-comprador-parou-pagar-particular",
    "imob-adimplemento-substancial",
    "imob-lote-compromisso-6766",
    "imob-lote-atraso-infraestrutura",
    "imob-comprador-suspender-pagamento-lote",
    "imob-habite-se-atraso-responsabilidade",
    "imob-financiamento-negado-clausula-suspensiva",
    "imob-escritura-registro-matricula-diferenca",
    "imob-certidao-onus-reais",
}

TOMBSTONE_LINE_SHA256 = {
    "imob-dupla-venda-mesmo-imovel": "1a5cb4a87f6ba69b1c24a211ec6dcc40c5f606c261fb98504b4e0b055f1627fd",
    "imob-vendedor-atrasa-documentacao": "0041fd999fc0fa39de388051807d4f28bd2e8b73b55db7939f2b4b9039b61302",
    "imob-divida-condominio-omitida-venda": "c384e4148fb3b8ee06bd4cf5d1ac442524a7170fb34d05d2ece5f9c252323e98",
    "imob-indisponibilidade-bens-vendedor": "839cc83bae122ddaf60f821bfd363accf1b513dea666b3ef698130d7897aa5f5",
    "imob-arrematacao-dividas-anteriores": "2088ca6c48874fd95db206f0f206e17e7ca677fb10f6c80e9dca513319e96520",
    "imob-cessao-direitos-hereditarios-imovel": "872d162dbe23aef04d27700ac6644fea15e49fba1bc47723dea17554f5f8997d",
    "imob-doacao-imovel-revogacao": "9c47f8da143bb9c35c490e63bade7bc4434a7883236dbe17878f3470a01cdef7",
    "imob-exclusividade-corretor-vendi-sozinho": "3faaecd267373313320786fb84813fc40970c0199dc6e41690eb78f9ae88ecd5",
}

PAGE_BANDS = {
    "imob-comprador-parou-pagar-particular": (630, 1540),
    "imob-adimplemento-substancial": (315, 770),
    "imob-lote-compromisso-6766": (630, 1540),
    "imob-lote-atraso-infraestrutura": (630, 1540),
    "imob-comprador-suspender-pagamento-lote": (630, 1540),
    "imob-habite-se-atraso-responsabilidade": (630, 1540),
    "imob-financiamento-negado-clausula-suspensiva": (630, 1540),
    "imob-escritura-registro-matricula-diferenca": (315, 770),
    "imob-certidao-onus-reais": (315, 770),
}

PROBED_HTTP_STATUS = {
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/24082021-Para-Quarta-Turma--clausula-resolutiva-expressa-em-contrato-imobiliario-dispensa-acao-para-rescisao-por-falta-de.aspx": 200,
    "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20160928&formato=HTML&nreg=201502887137&salvar=false&seq=1531880&tipo=0": 200,
    "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2025/16072025-Teoria-do-adimplemento-substancial-nao-respalda-adjudicacao-compulsoria--decide-Terceira-Turma.aspx/": 200,
    "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20180831&formato=PDF&nreg=201502624970&salvar=false&seq=1745042&tipo=0": 200,
}


def request_url(value):
    parsed = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))


def normalized_source_url(value):
    """Espelha a chave de unicidade do auditor, inclusive a ancora de artigo."""
    parsed = urllib.parse.urlsplit((value or "").strip())
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        port = None
    if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
        port = None
    decoded_path = urllib.parse.unquote(parsed.path)
    clean_path = posixpath.normpath(decoded_path or "/")
    if not clean_path.startswith("/"):
        clean_path = "/" + clean_path
    query = urllib.parse.urlencode(
        sorted(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)),
        doseq=True,
    )
    fragment = urllib.parse.unquote(parsed.fragment)
    return scheme, host, port, clean_path, query, fragment


def source(url, name, claim):
    return {"url": url, "name": name, "anchor_claim": claim}


def set_sources(page, specs):
    previous = page.get("official_sources", [])
    exact = {item.get("url"): item for item in previous}
    by_request = {}
    for item in previous:
        if item.get("url"):
            by_request.setdefault(request_url(item["url"]), item)

    updated = []
    for spec in specs:
        item = dict(spec)
        prior = exact.get(item["url"]) or by_request.get(request_url(item["url"]))
        if item["url"] in PROBED_HTTP_STATUS:
            item["verified_at"] = CHECKED_AT
            item["http_status"] = PROBED_HTTP_STATUS[item["url"]]
        elif prior is not None:
            item["verified_at"] = prior.get("verified_at")
            item["http_status"] = prior.get("http_status")
        updated.append(item)
    page["official_sources"] = updated


def section(page, heading):
    for item in page.get("sections", []):
        if item.get("heading") == heading:
            return item
    raise RuntimeError(f"{page['intent_id']}: secao ausente: {heading}")


def rewrite_section(page, old_heading, new_heading, text):
    try:
        item = section(page, old_heading)
    except RuntimeError:
        item = section(page, new_heading)
    item["heading"] = new_heading
    item["text"] = text


def rewrite_buyer_default(page):
    page["title"] = "Comprador inadimplente em venda direta: como resolver"
    page["meta_description"] = (
        "Venda parcelada entre particulares exige conferir mora, cláusula resolutiva, saldo pago e posse antes de cobrar ou pedir a retomada do imóvel."
    )
    page["h1"] = "O comprador parou de pagar o imóvel vendido em parcelas: quais são os caminhos"
    page["opening"] = (
        "Na venda parcelada diretamente entre particulares, o atraso não autoriza trocar fechaduras, retirar bens do ocupante ou declarar perdida toda quantia recebida. "
        "O vendedor precisa identificar o tipo de contrato, a cláusula sobre inadimplemento, o vencimento das prestações e a forma exigida para constituir o comprador em mora. "
        "Só depois dessa leitura é possível escolher entre cobrar o saldo, resolver o negócio ou buscar a posse pela via adequada."
    )
    rewrite_section(
        page,
        "Cláusula resolutiva e o passo da interpelação (art. 474 do Código Civil)",
        "Cláusula expressa não elimina a constituição regular da mora",
        "O artigo 474 do Código Civil distingue a cláusula resolutiva expressa, que opera de pleno direito, da cláusula resolutiva tácita, que depende de interpelação judicial. "
        "Nos compromissos imobiliários, porém, não se deve confundir resolução sem sentença prévia com dispensa de notificação. No REsp 1.789.863, o STJ admitiu ação possessória fundada na cláusula expressa depois de notificação extrajudicial e do decurso do prazo para purgar a mora. "
        "A forma e o prazo variam conforme o regime do contrato; mensagem informal sem prova de entrega pode não cumprir a exigência aplicável.",
    )
    rewrite_section(
        page,
        "Resolução do contrato e o pedido de reintegração de posse",
        "Cobrança, resolução e posse são pretensões diferentes",
        "Pelo artigo 475 do Código Civil, a parte lesada pode exigir o cumprimento ou pedir a resolução, com perdas e danos quando comprovadas. "
        "Havendo cláusula resolutiva expressa e mora regularmente constituída, o vínculo pode extinguir-se extrajudicialmente; ainda assim, a retomada forçada da posse depende de entrega voluntária ou ordem judicial. "
        "Sem cláusula expressa, a resolução precisa ser pedida ao Judiciário. O pedido deve mostrar contrato, parcelas vencidas, notificação e ocupação atual, sem tratar cobrança e reintegração como se fossem o mesmo efeito.",
    )
    rewrite_section(
        page,
        "Quanto o vendedor pode reter das parcelas pagas",
        "Retenção exige conta justificável, não perda total",
        "Retomar o imóvel e conservar tudo o que foi pago pode produzir vantagem sem causa, vedada pelo artigo 884 do Código Civil. "
        "Na venda entre particulares não existe um percentual único aplicável a qualquer caso. A conta deve separar saldo, tempo de ocupação, valor de uso, tributos assumidos, danos efetivos e restituição corrigida. "
        "O artigo 413 permite reduzir equitativamente cláusula penal manifestamente excessiva, enquanto prejuízo apenas alegado não substitui prova. O cálculo deve ser apresentado de modo que cada rubrica possa ser conferida.",
    )
    rewrite_section(
        page,
        "Quando esse pedido não prospera",
        "Pagamento elevado não decide sozinho e autotutela continua vedada",
        "Ter pago grande parte do preço é dado relevante, mas não cria defesa automática: o adimplemento substancial exige exame qualitativo do saldo, da conduta das partes e da preservação do interesse do credor. "
        "No sentido inverso, inadimplemento expressivo também não autoriza o vendedor a recuperar o bem pela própria força. Falta de notificação exigível, cobrança já quitada ou cálculo opaco podem enfraquecer a pretensão e ampliar o litígio.",
    )
    rewrite_section(
        page,
        "Um exemplo prático",
        "Cronologia mínima para uma venda em sessenta parcelas",
        "Imagine uma casa vendida em sessenta prestações, com posse entregue na assinatura. Após doze pagamentos, o comprador deixa vencer quatro parcelas. "
        "O vendedor confere a cláusula resolutiva, expede a notificação pela forma exigida, oferece a oportunidade de purgação e guarda os comprovantes. "
        "Persistindo o inadimplemento, escolhe entre cobrar o débito ou sustentar a resolução e a restituição da posse, apresentando também uma conta discriminada das quantias a devolver ou compensar.",
    )
    rewrite_section(
        page,
        "Montar a notificação e a ação com apoio jurídico",
        "Contrato e planilha definem a estratégia",
        "Antes de protocolar uma medida, convém reunir o instrumento completo, aditivos, comprovantes de pagamento, mensagens sobre renegociação, prova da posse e memória do saldo. "
        "Também importa verificar se o título foi registrado e se há garantia real constituída, pois alienação fiduciária, compromisso registrado e simples instrumento particular não seguem necessariamente o mesmo procedimento. "
        "Um advogado particular pode confrontar esses documentos com a cláusula de resolução e estruturar a notificação ou a ação correspondente, sem prometer antecipadamente retenção ou retomada.",
    )
    page["faq"] = [{
        "q": "A cláusula resolutiva expressa permite retirar o comprador do imóvel sem processo?",
        "a": "Não pela força. Ela pode dispensar uma ação prévia apenas para declarar a resolução, desde que a mora tenha sido constituída como exige o regime aplicável; a restituição coercitiva da posse depende de ordem judicial.",
    }]
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art474", "Código Civil, art. 474", "distingue os efeitos da cláusula resolutiva expressa e da tácita"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art475", "Código Civil, art. 475", "permite exigir cumprimento ou resolução, sem confundir essas pretensões com a restituição forçada da posse"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art413", "Código Civil, art. 413", "autoriza redução equitativa da cláusula penal manifestamente excessiva"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art884", "Código Civil, art. 884", "veda vantagem patrimonial sem causa na composição das parcelas pagas"),
        source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/24082021-Para-Quarta-Turma--clausula-resolutiva-expressa-em-contrato-imobiliario-dispensa-acao-para-rescisao-por-falta-de.aspx", "STJ, REsp 1.789.863/MS", "admite resolução extrajudicial por cláusula expressa após notificação e prazo de purgação da mora"),
    ])


def rewrite_substantial_performance(page):
    page["title"] = "Adimplemento substancial: critérios e limites no imóvel"
    page["meta_description"] = (
        "A teoria do adimplemento substancial não depende só do percentual pago e não substitui a quitação exigida para adjudicação compulsória do imóvel."
    )
    page["opening"] = (
        "Adimplemento substancial limita o uso desproporcional da resolução quando o contrato foi cumprido quase por inteiro, mas não transforma qualquer saldo pequeno em perdão. "
        "Não existe percentual fixo: o percentual isolado não decide se o vínculo deve ser preservado. A conclusão depende da relevância concreta do descumprimento e da possibilidade de o credor receber por outro meio."
    )
    page["sections"] = [
        {
            "heading": "Boa-fé e resolução continuam submetidas ao caso concreto",
            "text": "Os artigos 421 e 422 do Código Civil orientam a função social e a boa-fé contratual, enquanto o artigo 475 permite ao lesado exigir cumprimento ou resolução. A teoria harmoniza essas normas em cada relação concreta: evita desfazimento desproporcional, mas não apaga o direito ao saldo, aos encargos válidos ou à reparação demonstrada.",
        },
        {
            "heading": "REsp 1.581.505 afastou uma conta puramente aritmética",
            "text": "No REsp 1.581.505, o STJ explicou que a análise qualitativa considera expectativas legítimas criadas pela conduta das partes, pequena importância do pagamento faltante e conservação do contrato sem prejuízo ao direito de cobrança. As circunstâncias do caso podem tornar relevante um saldo percentualmente baixo; por isso, dizer que 80%, 90% ou 95% bastam por si sós é incorreto.",
        },
        {
            "heading": "A dívida permanece exigível mesmo quando o contrato é preservado",
            "text": "Aplicar a teoria pode afastar a resolução e direcionar o credor à cobrança, mas não concede quitação nem autoriza o devedor a interromper os últimos pagamentos. Garantias especiais também podem ter disciplina legal própria. A natureza do contrato, a extensão da mora e a utilidade restante da prestação precisam ser identificadas antes de invocar o instituto.",
        },
        {
            "heading": "Adjudicação compulsória requer quitação integral",
            "text": "No REsp 2.207.433, julgado em 2025, a Terceira Turma decidiu que o adimplemento substancial não substitui a quitação integral exigida para adjudicação compulsória. O comprador não obtém a transferência forçada da propriedade deixando saldo aberto, ainda que as parcelas remanescentes estejam prescritas. Preservar o contrato e receber o domínio são questões jurídicas distintas.",
        },
    ]
    page["faq"] = []
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art421", "Código Civil, art. 421", "função social e liberdade contratual na preservação do vínculo"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art422", "Código Civil, art. 422", "boa-fé objetiva aplicada à execução do contrato"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art475", "Código Civil, art. 475", "direito de exigir cumprimento ou resolução por inadimplemento"),
        source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20160928&formato=HTML&nreg=201502887137&salvar=false&seq=1531880&tipo=0", "STJ, REsp 1.581.505/SC", "fixa exame qualitativo e não meramente percentual do adimplemento substancial"),
        source("https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2025/16072025-Teoria-do-adimplemento-substancial-nao-respalda-adjudicacao-compulsoria--decide-Terceira-Turma.aspx/", "STJ, REsp 2.207.433/SP", "exige quitação integral e afasta a teoria como fundamento de adjudicação compulsória"),
    ])


def rewrite_lot_termination(page):
    page["opening"] = (
        "A Lei 13.786/2018 alterou dois regimes diferentes: a Lei 4.591/1964, para incorporação imobiliária, e a Lei 6.766/1979, para loteamentos. "
        "Quem comprou um lote parcelado deve consultar os artigos 32 e 32-A da Lei 6.766, sem importar automaticamente percentuais ou prazos usados na compra de apartamento em incorporação. "
        "A causa do desfazimento, a posse e o estágio das obras mudam a conta."
    )
    rewrite_section(
        page,
        "E se quem quer sair do contrato é o próprio comprador?",
        "Pedido do comprador não gera devolução integral automática",
        "Quando o adquirente pede o fim do negócio sem inadimplemento do loteador, é preciso ler a cláusula de distrato e identificar como a resolução será formalizada. "
        "O artigo 32-A disciplina a restituição quando o desfazimento é imputável ao adquirente no contrato de loteamento, mas não autoriza inserir qualquer desconto por simples analogia. "
        "Fruição pressupõe posse; tributo ou encargo precisa corresponder ao lote e ao período; a comissão de corretagem integrada ao preço do lote pode compor a dedução; e a pena deve respeitar os requisitos e limites legais.",
    )
    rewrite_section(
        page,
        "Quando o pedido de devolução integral não prospera",
        "Teto legal não dispensa prova de cada dedução",
        "A existência de um teto de 0,75% ao mês para fruição e de limite de 10% para cláusula penal e despesas administrativas não torna esses abatimentos automáticos. "
        "O loteador deve mostrar a base atualizada, o período de posse e os encargos incluídos. Se a resolução decorre de falta do próprio loteador, a imputação e as consequências precisam ser examinadas por outro enquadramento, sem transferir ao comprador a culpa apenas porque ele pediu o encerramento.",
    )
    rewrite_section(
        page,
        "Como fica a devolução na prática",
        "Prazo de restituição varia com as obras e eventual revenda",
        "O artigo 32-A também disciplina quando o saldo deve ser restituído. O cronograma não é único: considera se as obras estavam em andamento ou concluídas e contém regra para a hipótese de nova venda do lote antes do prazo ordinário. "
        "A memória de cálculo deve indicar a data formal da resolução, a etapa do empreendimento e eventual alienação posterior, pois esses marcos influenciam o vencimento das parcelas de devolução.",
    )
    rewrite_section(
        page,
        "Conferir se os descontos aplicados respeitam a lei",
        "Demonstrativo contratual deve expor base, período e vencimentos",
        "Contrato, termo de posse, notificação, extrato pago e planilha do loteador permitem conferir o cálculo. A revisão deve separar fruição, pena, mora, tributos, associação e corretagem, sem somar rótulos repetidos. "
        "Se houver divergência, um advogado particular pode formular uma contraproposta fundamentada ou discutir a rubrica específica, preservando as parcelas incontroversas.",
    )
    page["faq"] = [{
        "q": "A Lei 13.786 criou uma única regra de distrato para lote e apartamento?",
        "a": "Não. Ela alterou tanto a Lei 6.766 quanto a Lei 4.591, mas cada diploma conserva artigos, percentuais e prazos próprios; para loteamento, a referência central é o artigo 32-A da Lei 6.766.",
    }]
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/l6766.htm#art32", "Lei 6.766/1979, art. 32", "constituição em mora e prazo de trinta dias antes da resolução por falta de pagamento"),
        source("https://www.planalto.gov.br/ccivil_03/leis/l6766.htm#art32-A", "Lei 6.766/1979, art. 32-A", "deduções, limites e cronograma de restituição próprios dos contratos de loteamento"),
        source("https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13786.htm", "Lei 13.786/2018", "alterou separadamente os regimes de incorporações e de loteamentos"),
    ])


def rewrite_lot_infrastructure(page):
    rewrite_section(
        page,
        "O comprador também é consumidor: o art. 35 do CDC",
        "CDC protege o adquirente destinatário final",
        "Quando uma loteadora profissional fornece o lote a adquirente que o recebe como destinatário final, configura-se relação de consumo. Diante da recusa ou do atraso relevante no cumprimento da oferta, o artigo 35 do Código de Defesa do Consumidor oferece três caminhos: rescindir o contrato com devolução dos valores pagos e perdas e danos cabíveis; aceitar prestação equivalente; ou exigir o cumprimento forçado da oferta. "
        "A destinação econômica do lote e as características das partes precisam ser verificadas; compra empresarial para revenda ou integração direta à atividade produtiva não deve ser chamada automaticamente de consumo.",
    )
    rewrite_section(
        page,
        "Suspender pagamento é diferente de simplesmente parar de pagar",
        "Artigo 38 alcança a execução irregular do projeto aprovado",
        "O artigo 38 da Lei 6.766 alcança o loteamento que não se acha registrado ou regularmente executado. "
        "Se a omissão de infraestrutura mostra desconformidade relevante com o projeto aprovado, o adquirente pode notificar o loteador, suspender o pagamento direto e efetuar o depósito das prestações junto ao Registro de Imóveis competente, nos termos legais. "
        "Esse procedimento não se confunde com reter o dinheiro na própria conta nem com reagir a qualquer atraso pontual.",
    )
    rewrite_section(
        page,
        "Atraso pontual não sustenta a rescisão do loteamento",
        "Cronograma vencido precisa ser comparado ao projeto e à licença",
        "Pequena demora sanada, etapa cujo prazo ainda corre ou obra que a licença atribuiu ao Município não demonstram, sozinhas, execução irregular pelo loteador. "
        "Por outro lado, o simples registro do parcelamento não neutraliza o artigo 38 quando redes, drenagem ou vias aprovadas deixam de ser executadas de modo relevante. "
        "O memorial, o cronograma, a aprovação municipal e uma vistoria atual permitem distinguir atraso contratual de irregularidade urbanística.",
    )
    rewrite_section(
        page,
        "Quando vale procurar um advogado",
        "Escolha da medida depende do estágio da implantação",
        "A documentação pode sustentar cumprimento forçado da oferta, resolução, indenização ou o procedimento de suspensão com depósito. "
        "Um advogado particular pode comparar o memorial com o que existe no local e indicar qual providência preserva o contrato ou organiza a saída, sem recomendar a interrupção informal das prestações.",
    )
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/l6766.htm#art2", "Lei 6.766/1979, art. 2º, §§ 4º e 5º", "define a infraestrutura básica do lote conforme a localização e o regime legal aplicável"),
        source("https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art35", "Código de Defesa do Consumidor, art. 35", "prevê alternativas por descumprimento da oferta quando configurada relação de consumo"),
        source("https://www.planalto.gov.br/ccivil_03/leis/l6766.htm#art38", "Lei 6.766/1979, art. 38", "prevê suspensão do pagamento direto e depósito das prestações junto ao Registro de Imóveis quando o loteamento não está registrado ou regularmente executado"),
    ])


def rewrite_lot_payment_suspension(page):
    page["title"] = "Artigo 38 do loteamento: suspensão e depósito das parcelas"
    page["meta_description"] = (
        "Saiba quando a falta de registro ou a execução irregular do loteamento permite suspender o pagamento direto e depositar as prestações no Registro de Imóveis."
    )
    page["h1"] = "Loteamento sem registro ou execução regular: como funciona o depósito das parcelas"
    page["opening"] = (
        "A Lei 6.766 criou um procedimento específico para proteger o adquirente sem transformar a irregularidade do loteamento em inadimplência comum. "
        "Ele não consiste em simplesmente parar de pagar: exige enquadramento no artigo 38, notificação do loteador e depósito das prestações pela via indicada na lei. "
        "O registro existente não encerra a análise, porque a execução do projeto aprovado também importa."
    )
    rewrite_section(
        page,
        "O mecanismo do art. 38: suspensão com depósito, não inadimplência",
        "Texto do artigo 38 cobre duas formas centrais de irregularidade",
        "O artigo 38 incide quando o loteamento ou desmembramento não se acha registrado ou regularmente executado, além da hipótese de falta da notificação municipal prevista no dispositivo. "
        "O adquirente deve suspender o pagamento direto, notificar o loteador para suprir a falta e manter o depósito das prestações. O Registro de Imóveis encaminha os valores a estabelecimento de crédito, em conta remunerada cuja movimentação depende de autorização judicial.",
    )
    rewrite_section(
        page,
        "Quando esse caminho não se aplica",
        "Atraso pontual não equivale necessariamente a execução irregular",
        "Dificuldade financeira, arrependimento ou mudança de planos não acionam o artigo 38. Também é preciso separar atraso pontual de execução irregular: uma etapa curta e ainda compatível com o cronograma pode gerar cobrança contratual sem justificar o depósito legal. "
        "Já a falta relevante de infraestrutura prevista no projeto pode caracterizar execução irregular mesmo quando o loteamento está registrado. Nessa situação, afirmar que o artigo 38 nunca se aplica seria contrário ao próprio texto legal.",
    )
    rewrite_section(
        page,
        "Como formalizar o depósito com segurança",
        "Prova da irregularidade deve acompanhar cada etapa",
        "Certidão do parcelamento, projeto aprovado, cronograma, manifestação municipal, contrato e recibos permitem mostrar por que o pagamento direto foi suspenso. "
        "O protocolo de notificação e os comprovantes mensais do depósito devem permanecer organizados. O depósito documentado preserva a continuidade das prestações enquanto a regularização segue o procedimento legal. "
        "Um advogado particular pode conferir o enquadramento e preparar o requerimento sem tratar uma deficiência documental como autorização para inadimplir.",
    )
    page["faq"] = [{
        "q": "O comprador precisa demonstrar a irregularidade sozinho para usar o artigo 38?",
        "a": "Não há prova única nem dispensa de demonstrar o enquadramento. Certidões registrais e municipais, projeto, cronograma e vistoria podem ser necessários conforme a irregularidade; Prefeitura, Distrito Federal ou Ministério Público também podem promover a notificação prevista na lei.",
    }]


def rewrite_habite_se(page):
    page["title"] = "Obra sem habite-se: deveres da incorporadora e prova do atraso"
    page["meta_description"] = (
        "A demora do habite-se e a demora posterior na averbação são etapas distintas; responsabilidade depende da causa, do contrato e dos prejuízos comprovados."
    )
    page["h1"] = "Prédio concluído sem habite-se: como apurar a responsabilidade pelo atraso"
    page["opening"] = (
        "Conclusão física, emissão do habite-se e averbação da construção são marcos diferentes. A falta de um deles pode impedir registro da unidade ou financiamento, mas não autoriza presumir a mesma causa em todos os empreendimentos. "
        "A análise deve identificar o cronograma contratual, as exigências administrativas, a conduta da incorporadora e o dano efetivamente suportado pelo adquirente."
    )
    rewrite_section(
        page,
        "Por que o habite-se é o marco jurídico da entrega (art. 44 da Lei 4.591/1964)",
        "Artigo 44 começa depois da concessão do habite-se",
        "O artigo 44 da Lei 4.591/1964 determina que, após a concessão do habite-se, o incorporador requeira a averbação da construção para individualização e discriminação das unidades. Ele responde por perdas e danos decorrentes da demora no cumprimento dessa obrigação. "
        "A norma fixa prazo máximo de quinze dias para esse requerimento. Comprovante de protocolo, nota de exigência e certidão registral permitem saber se a demora posterior decorreu de omissão do incorporador ou de exigência regularmente atendida. "
        "O art. 44 não cria responsabilidade objetiva pela obtenção do habite-se. Para o período anterior, é preciso examinar deveres contratuais, andamento da obra e causa das pendências perante a Prefeitura.",
    )
    rewrite_section(
        page,
        "O que o comprador perde sem o habite-se",
        "Efeitos concretos variam conforme o empreendimento",
        "Sem regularização, podem ficar impedidos a averbação da construção, a abertura ou atualização das matrículas e o financiamento definitivo. Ocupação, serviços públicos e instituição do condomínio dependem também de regras locais e de outros documentos, por isso não devem ser apresentados como consequências automáticas idênticas. "
        "O comprador precisa guardar a recusa bancária, a nota registral ou a exigência municipal que demonstre o obstáculo concreto.",
    )
    rewrite_section(
        page,
        "Cobrando a construtora pelo atraso",
        "Causa da pendência e nexo com o prejuízo precisam ser demonstrados",
        "O artigo 186 do Código Civil exige ação ou omissão negligente, dano e nexo causal. Pendência de projeto, obra executada em desacordo ou documento que competia à incorporadora pode sustentar reparação. "
        "No REsp 1.562.583, o STJ tratou riscos previsíveis da atividade como insuficientes para afastar a mora e considerou a averbação da carta de habite-se no termo do atraso examinado. O precedente não converte qualquer demora pública, em contexto diferente, em indenização automática.",
    )
    rewrite_section(
        page,
        "Quando a demora não é da construtora",
        "Exigência municipal não exonera nem condena por si só",
        "Uma norma superveniente, ato exclusivo do comprador ou evento realmente externo pode influir na imputação, mas o rótulo de exigência municipal não basta. "
        "É preciso saber se a adequação era previsível, se a obra contrariou o projeto, quando a documentação foi protocolada e se houve resposta diligente. Prazo de tolerância contratual também deve ser lido quanto ao objeto e à validade, sem estendê-lo automaticamente da entrega física à regularização registral.",
    )
    rewrite_section(
        page,
        "Buscando a indenização com apoio jurídico",
        "Linha do tempo separa atraso físico, administrativo e registral",
        "Contrato, cronograma, comunicações da Prefeitura, protocolo do habite-se, certidão da matrícula e despesas vinculadas ao atraso compõem a prova. "
        "Aluguel pago, custo de financiamento prorrogado e perda de renda locatícia exigem documentos próprios e relação temporal com a pendência; a data da imissão na posse também delimita o período discutido, e a mera expectativa não substitui demonstração do dano. "
        "Um advogado particular pode organizar esses marcos e delimitar o pedido ao período e ao dano demonstráveis, evitando somar prejuízos incompatíveis.",
    )
    page["faq"] = [{
        "q": "A ocupação antes do habite-se regulariza o prédio ou afasta o atraso?",
        "a": "Não. A ocupação de fato não substitui a licença municipal nem a averbação registral. Seus efeitos dependem das normas locais e do caso, e a entrega das chaves não elimina automaticamente eventual mora ligada à regularização.",
    }]
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/l4591.htm#art44", "Lei 4.591/1964, art. 44", "dever de averbar a construção depois do habite-se e responsabilidade pela demora nessa etapa"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art186", "Código Civil, art. 186", "responsabilidade por conduta causalmente ligada ao dano comprovado"),
        source("https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20180831&formato=PDF&nreg=201502624970&salvar=false&seq=1745042&tipo=0", "STJ, REsp 1.562.583/DF", "examina riscos da atividade e o marco da averbação da carta de habite-se no atraso do caso concreto"),
    ])


def rewrite_financing_condition(page):
    page["title"] = "Financiamento negado: devolução do sinal depende do contrato"
    page["meta_description"] = (
        "A recusa do banco não garante nem elimina sozinha a devolução do sinal; condição suspensiva, arras, causa da negativa e relação de consumo definem o efeito."
    )
    page["h1"] = "O banco negou o financiamento do imóvel: o que acontece com o sinal"
    page["opening"] = (
        "A resposta não nasce da carta de recusa isoladamente. É preciso verificar se a aprovação bancária foi escrita como condição para a eficácia da compra, se o valor pago era arras, quem provocou a negativa e se vendedor e comprador mantêm relação de consumo. "
        "Sem essas distinções, tratar todo crédito negado como desistência ou como devolução integral produz conclusões igualmente inseguras."
    )
    rewrite_section(
        page,
        "A diferença entre condição suspensiva e arrependimento (art. 121 do Código Civil)",
        "Condição precisa constar do negócio e ter alcance definido",
        "Pelo artigo 121 do Código Civil, condição é cláusula derivada da vontade das partes que subordina o efeito do negócio a evento futuro e incerto. "
        "Se o contrato afirma expressamente que a compra só produzirá efeitos com aprovação de determinado financiamento dentro de prazo definido, a recusa pode impedir a implementação da condição suspensiva. "
        "Nos termos do artigo 125, enquanto não se verificar a condição, não se terá adquirido o direito a que ela visa. "
        "Se o crédito aparece apenas como meio pretendido pelo comprador para pagar obrigação já firme, a negativa não desfaz o contrato por si só.",
    )
    rewrite_section(
        page,
        "Frustração do crédito não é desistência voluntária",
        "Motivo da recusa distribui a responsabilidade",
        "Renda insuficiente, informação falsa, documento omitido, avaliação baixa do imóvel, gravame do vendedor e mudança de política bancária não são fatos equivalentes. "
        "A recusa alheia à conduta do comprador pode confirmar o fracasso de uma condição expressa; conduta imputável ao comprador pode afastar essa leitura. Se o vendedor prometeu bem apto ao financiamento e não removeu o obstáculo que lhe cabia, a imputação pode seguir no sentido oposto.",
    )
    rewrite_section(
        page,
        "Cláusulas que tentam reter o sinal mesmo com negativa de crédito",
        "CDC só incide quando existe relação de consumo",
        "O artigo 51 do Código de Defesa do Consumidor permite controlar cláusula abusiva em contrato entre consumidor e fornecedor. Ele não se aplica automaticamente a toda venda entre duas pessoas físicas. "
        "Mesmo na relação de consumo, a análise deve considerar transparência, redação contratual, alocação do risco e causa da recusa, em vez de presumir que qualquer retenção é nula ou que qualquer cláusula escrita é suficiente. A negativa não gera devolução integral automática.",
    )
    rewrite_section(
        page,
        "Quando o vendedor pode reter parte do sinal mesmo assim",
        "Natureza das arras muda a consequência do desfazimento",
        "Os artigos 417 a 420 do Código Civil distinguem efeitos das arras e a hipótese de arrependimento pactuado. Antes de falar em perda ou devolução em dobro, o contrato precisa revelar a função do sinal e quem deu causa à inexecução. "
        "Uma cláusula penal também não deve ser confundida com arras. A existência de condição suspensiva pode significar que o efeito principal nem chegou a nascer, o que exige conta diferente da resolução por culpa.",
    )
    rewrite_section(
        page,
        "É preciso tentar outros bancos antes de considerar o crédito frustrado?",
        "Diligência exigível vem do texto e da boa-fé do contrato",
        "Não há dever genérico de consultar todas as instituições do mercado. O contrato pode, contudo, prever banco, modalidade, valor, prazo ou cooperação documental. "
        "Quando essas balizas faltam, pedidos enviados, respostas e datas ajudam a demonstrar atuação leal. Uma única solicitação incompatível com as condições prometidas pode não provar que o evento convencionado se tornou impossível.",
    )
    rewrite_section(
        page,
        "Como agir diante da negativa",
        "Carta bancária e cláusula precisam ser lidas em conjunto",
        "A carta de recusa, o contrato, o recibo do sinal, a proposta de crédito e os documentos exigidos pelo banco formam o conjunto inicial. "
        "Também convém obter do banco a razão registrada para a negativa e guardar a avaliação do imóvel, pois um comunicado genérico pode não revelar qual obrigação falhou. "
        "Um advogado particular pode classificar a condição e as arras antes de redigir a notificação, formulando pedido compatível com a causa efetivamente documentada.",
    )
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art121", "Código Civil, arts. 121 e 125", "conceito e efeitos da condição suspensiva ajustada pelas partes"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art125", "Código Civil, art. 125", "impede a aquisição do direito enquanto a condição suspensiva não se verifica"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art417", "Código Civil, arts. 417 a 420", "efeitos das arras conforme inexecução, culpa e direito de arrependimento"),
        source("https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm#art51", "Código de Defesa do Consumidor, art. 51", "controle de cláusulas abusivas apenas quando configurada relação de consumo"),
    ])


def rewrite_deed_registration_record(page):
    page["opening"] = (
        "Escritura, registro e matrícula pertencem a etapas diferentes. A escritura documenta o negócio quando essa forma é exigida; o registro do título realiza a transferência da propriedade; e a matrícula é o fólio que individualiza o imóvel e recebe os atos de sua história registral. "
        "Confundir os termos pode deixar o preço pago sem que o domínio tenha mudado."
    )
    rewrite_section(
        page,
        "Escritura: o contrato formalizado em cartório",
        "Escritura é um título, com exceções previstas em lei",
        "O artigo 108 do Código Civil exige escritura pública, salvo disposição legal diferente, para negócios que constituam, transfiram, modifiquem ou renunciem direitos reais sobre imóveis acima de trinta vezes o maior salário mínimo vigente. "
        "Há contratos aos quais lei especial atribui força de escritura pública e negócios abaixo do limite que admitem instrumento particular. Em qualquer dessas hipóteses, o título documenta a causa da transferência, mas não transfere a propriedade por si só.",
    )
    rewrite_section(
        page,
        "Registro: o ato que efetivamente transfere a propriedade (art. 1245 do Código Civil)",
        "Artigo 1.245 faz do registro o marco da propriedade",
        "Pelo artigo 1.245 do Código Civil, a propriedade entre vivos se transfere mediante o registro do título translativo no Registro de Imóveis. "
        "Enquanto o título não é registrado, o alienante continua havido como dono. Posse, pagamento e assinatura geram efeitos obrigacionais relevantes, mas não substituem o ato registral que muda a titularidade perante terceiros.",
    )
    rewrite_section(
        page,
        "Matrícula: o histórico permanente do imóvel",
        "Compra e venda entra na matrícula por registro, não por averbação",
        "A matrícula individualiza o imóvel e organiza seu histórico: proprietários, direitos reais, constrições e alterações juridicamente relevantes. O artigo 167 da Lei 6.015 inclui a compra e venda entre os atos de registro. "
        "Portanto, a escritura apresentada não averba a nova propriedade; ela serve de título para registrar a transferência. Averbações são reservadas a ocorrências que a lei classifica nessa categoria, como certas alterações do estado do imóvel ou das pessoas.",
    )
    rewrite_section(
        page,
        "Um exemplo que junta os três",
        "Um título, um ato de registro e a mesma matrícula",
        "Na compra de um apartamento, as partes podem lavrar a escritura no tabelionato de notas. O comprador apresenta esse título ao Registro de Imóveis competente. "
        "Depois da qualificação e do atendimento das exigências, o oficial pratica o registro da compra e venda na matrícula já aberta para a unidade. A partir desse registro, o adquirente passa a constar como proprietário; não nasce uma matrícula nova a cada alienação.",
    )
    page["faq"] = [{
        "q": "Pagar o preço e receber as chaves basta para ser proprietário?",
        "a": "Não. Esses fatos podem transferir a posse e gerar direitos contratuais, mas a propriedade entre vivos só muda com o registro do título na matrícula, conforme o artigo 1.245.",
    }]
    set_sources(page, [
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art108", "Código Civil, art. 108", "forma pública e exceções legais para negócios imobiliários"),
        source("https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1245", "Código Civil, art. 1.245", "registro do título como modo de transferência da propriedade entre vivos"),
        source("https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art167", "Lei 6.015/1973, art. 167", "classifica a compra e venda como ato de registro na matrícula, e não de averbação"),
    ])


def rewrite_encumbrance_certificate(page):
    page["opening"] = (
        "A certidão de ônus reais retrata o que consta do Registro de Imóveis até o momento da emissão. Ela identifica titularidade e atos lançados na matrícula, como hipoteca, usufruto, penhora ou indisponibilidade, conforme o tipo de certidão pedido. "
        "Não é uma fotografia completa de toda situação jurídica ou econômica ligada ao imóvel, porque fatos não registrados e débitos mantidos em outras bases exigem diligências próprias."
    )
    rewrite_section(
        page,
        "O que a certidão precisa mostrar (art. 19 da Lei 6.015/1973)",
        "Artigo 19 permite certidão de inteiro teor, resumo ou relatório",
        "O artigo 19 da Lei 6.015 autoriza certidão em inteiro teor, em resumo ou em relatório conforme os quesitos, autenticada pelo oficial. "
        "Por isso, o pedido deve ser claro: inteiro teor da matrícula, certidão de propriedade e ônus ou informação sobre ato determinado não são expressões necessariamente intercambiáveis em todas as serventias. Para conhecer a cadeia dos lançamentos, a certidão integral costuma oferecer contexto que um resumo de ônus vigentes não mostra.",
    )
    rewrite_section(
        page,
        "O que costuma aparecer na certidão",
        "Somente atos levados ao fólio registral aparecem como lançamentos",
        "Registro de compra e venda, hipoteca, usufruto, promessa registrada e constrições lançadas podem ser identificados na matrícula. "
        "A ausência de lançamento reduz determinados riscos, mas não prova quitação de condomínio, inexistência de ocupante, regularidade física da construção ou ausência de processo ainda não averbado. A leitura deve observar número do ato, data, titular atingido e eventual cancelamento posterior.",
    )
    rewrite_section(
        page,
        "Como e onde pedir a certidão",
        "Pedido deve chegar ao Registro de Imóveis competente",
        "A serventia da circunscrição onde a matrícula está aberta é responsável pela certidão. O requerimento pode ser feito pelos canais presenciais ou eletrônicos oficialmente disponibilizados para aquele registro. "
        "Convém conferir matrícula, endereço, nome do titular e finalidade do pedido e emitir o documento perto da assinatura, pois uma prenotação ou averbação posterior não aparece em certidão antiga.",
    )
    rewrite_section(
        page,
        "O que a certidão não garante sozinha",
        "Situação registral precisa ser combinada com outras verificações",
        "O artigo 1.245 do Código Civil estabelece a transferência pelo registro do título translativo, razão pela qual a matrícula é central para identificar o proprietário e a situação registral. A certidão não substitui outras certidões: a compra segura pode exigir documentos do vendedor, declaração condominial, informação tributária, vistoria, ocupação e regularidade edilícia. "
        "Também é necessário comparar o documento apresentado pelo vendedor com a descrição registral. Certidão atual não valida contrato falso, área divergente ou pagamento feito a pessoa sem poderes.",
    )
    page["faq"] = [{
        "q": "Certidão de matrícula e certidão de ônus são sempre o mesmo documento?",
        "a": "Não necessariamente. A nomenclatura e o conteúdo solicitado podem variar; o interessado deve dizer se precisa do inteiro teor da matrícula, da propriedade e ônus atuais ou de resposta a quesitos específicos.",
    }]


UPDATERS = {
    "imob-comprador-parou-pagar-particular": rewrite_buyer_default,
    "imob-adimplemento-substancial": rewrite_substantial_performance,
    "imob-lote-compromisso-6766": rewrite_lot_termination,
    "imob-lote-atraso-infraestrutura": rewrite_lot_infrastructure,
    "imob-comprador-suspender-pagamento-lote": rewrite_lot_payment_suspension,
    "imob-habite-se-atraso-responsabilidade": rewrite_habite_se,
    "imob-financiamento-negado-clausula-suspensiva": rewrite_financing_condition,
    "imob-escritura-registro-matricula-diferenca": rewrite_deed_registration_record,
    "imob-certidao-onus-reais": rewrite_encumbrance_certificate,
}


def deaccent(value):
    return "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )


def count_words(value):
    return len(re.findall(r"[^\W_]+", deaccent(value).lower(), re.UNICODE))


def body_word_count(page):
    total = count_words(page.get("opening", ""))
    for item in page.get("sections", []):
        total += count_words(item.get("heading", ""))
        total += count_words(item.get("text", ""))
    for item in page.get("faq", []):
        total += count_words(item.get("q", ""))
        total += count_words(item.get("a", ""))
    return total


def line_sha(raw_line):
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


def parse_original(payload):
    raw_lines = payload.decode("utf-8").splitlines()
    records = []
    seen = set()
    for position, raw_line in enumerate(raw_lines, 1):
        if not raw_line.strip():
            raise RuntimeError(f"linha vazia inesperada: {position}")
        page = json.loads(raw_line)
        intent = page.get("intent_id")
        if not intent or intent in seen:
            raise RuntimeError(f"intent ausente ou duplicado: {intent}")
        seen.add(intent)
        records.append((raw_line, page))
    if len(records) != 17:
        raise RuntimeError(f"contagem inesperada: {len(records)}")
    if seen != ACTIVE_INTENTS | set(TOMBSTONE_LINE_SHA256):
        raise RuntimeError("conjunto de intents divergiu do mapa de supersessao")
    for raw_line, page in records:
        intent = page["intent_id"]
        if intent in TOMBSTONE_LINE_SHA256:
            if page.get("skipped") is not True:
                raise RuntimeError(f"tombstone reativado: {intent}")
            if page.get("superseded_by") != "imobiliario-05.jsonl":
                raise RuntimeError(f"supersessao alterada: {intent}")
            if line_sha(raw_line) != TOMBSTONE_LINE_SHA256[intent]:
                raise RuntimeError(f"tombstone alterado: {intent}")
        elif page.get("skipped"):
            raise RuntimeError(f"pagina ativa marcada como skipped: {intent}")
    return records


def validate_active(page):
    intent = page["intent_id"]
    real = body_word_count(page)
    page["word_count"] = real
    low, high = PAGE_BANDS[intent]
    if not low <= real <= high:
        raise RuntimeError(f"{intent}: word_count={real} fora de {low}-{high}")
    sources = page.get("official_sources", [])
    if not 2 <= len(sources) <= 5:
        raise RuntimeError(f"{intent}: fontes={len(sources)}")
    urls = set()
    for item in sources:
        if not all(str(item.get(key, "")).strip() for key in ("url", "name", "anchor_claim", "verified_at")):
            raise RuntimeError(f"{intent}: fonte incompleta")
        try:
            datetime.date.fromisoformat(item["verified_at"])
        except ValueError as error:
            raise RuntimeError(f"{intent}: verified_at invalido") from error
        if item.get("http_status") not in {200, 203, 206}:
            raise RuntimeError(f"{intent}: http_status invalido: {item.get('http_status')}")
        normalized = normalized_source_url(item["url"])
        if normalized in urls:
            raise RuntimeError(f"{intent}: URL de fonte duplicada: {normalized}")
        urls.add(normalized)


def build_output(payload):
    records = parse_original(payload)
    rendered = []
    edited = set()
    for raw_line, page in records:
        intent = page["intent_id"]
        if intent in TOMBSTONE_LINE_SHA256:
            rendered.append(raw_line + "\n")
            continue
        UPDATERS[intent](page)
        validate_active(page)
        edited.add(intent)
        rendered.append(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n")
    if edited != ACTIVE_INTENTS:
        raise RuntimeError(f"paginas ativas nao editadas: {sorted(ACTIVE_INTENTS - edited)}")
    encoded = "".join(rendered).encode("utf-8")
    # Rele a saida e reaplica as protecoes antes de qualquer promocao.
    parse_original(encoded)
    return encoded


def validate_final_payload(payload):
    records = parse_original(payload)
    active = 0
    for _, page in records:
        if page["intent_id"] in ACTIVE_INTENTS:
            validate_active(page)
            active += 1
    if active != len(ACTIVE_INTENTS):
        raise RuntimeError(f"paginas ativas finais={active}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--candidate",
        metavar="PATH",
        help="no dry-run, grava atomicamente o candidato fora do shard para auditoria",
    )
    args = parser.parse_args()
    if args.dry_run and args.check:
        raise SystemExit("--dry-run e --check sao mutuamente exclusivos")
    if args.candidate and not args.dry_run:
        raise SystemExit("--candidate exige --dry-run")
    if args.candidate and os.path.abspath(args.candidate) == os.path.abspath(TARGET):
        raise SystemExit("--candidate nao pode apontar para o shard alvo")

    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()

    if args.check:
        if not FINAL_SHA256:
            raise SystemExit("FINAL_SHA256 ainda nao fixado")
        if actual != FINAL_SHA256:
            raise SystemExit(f"check CAS falhou: esperado {FINAL_SHA256}, encontrado {actual}")
        validate_final_payload(original)
        print(f"check=pass active=9 tombstones=8 sha256={actual}")
        return

    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    encoded = build_output(original)
    output_sha = hashlib.sha256(encoded).hexdigest()
    if FINAL_SHA256 and output_sha != FINAL_SHA256:
        raise SystemExit(f"output divergente: esperado {FINAL_SHA256}, encontrado {output_sha}")
    if args.dry_run:
        if args.candidate:
            candidate_directory = os.path.dirname(os.path.abspath(args.candidate))
            descriptor, temporary = tempfile.mkstemp(
                prefix=".imobiliario-10-candidate.", dir=candidate_directory
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, args.candidate)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        print(f"dry_run=pass active=9 tombstones=8 sha256={output_sha}")
        return

    directory = os.path.dirname(TARGET)
    descriptor, temporary = tempfile.mkstemp(prefix=".imobiliario-10.", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        with open(TARGET, "rb") as handle:
            current = hashlib.sha256(handle.read()).hexdigest()
        if current != EXPECTED_SHA256:
            raise SystemExit(f"CAS mudou antes da promocao: {current}")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"promoted=pass active=9 tombstones=8 sha256={output_sha}")


if __name__ == "__main__":
    main()
