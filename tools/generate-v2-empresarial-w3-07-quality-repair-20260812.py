#!/usr/bin/env python3
"""Corrige title_len, ngram_dup e o gatilho Tema 987 no shard empresarial-w3-07.

Gerador datado (2026-08-12): a página já foi promovida pelo CAS canônico
(producer.atomic_replace_cas) e teve proveniência live aplicada. Este script
faz correção pontual pós-promoção, preservando verified_at/http_status de
cada fonte, e recalcula word_count com a mesma fórmula do auditor
(tools.audit_v2_pages.body_word_count) — nunca split() improvisado.
"""

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, "/opt/wiki")
from tools.audit_v2_pages import body_word_count

PATH = "/opt/wiki/data/editorial/v2_pages/empresarial-w3-07.jsonl"
EXPECTED_SHA256 = "1bfe00c1a4513efc4aaf1962664292e413153b1c1fec986b092d2ea7ced7bb9d"

TITLE_FIXES = {
    "emp-comprar-ativos-empresa-em-recuperacao-sem-sucessao": "Comprar ativos de empresa em recuperação sem herdar dívida",
    "emp-contrato-api-integracao-b2b-clausulas": "Cláusulas essenciais no contrato de integração via API",
    "emp-crime-falimentar-responsabilizacao-penal": "Crime falimentar: quando a gestão vira responsabilidade penal",
    "emp-descumprimento-plano-apos-fiscalizacao-dois-anos": "Descumprimento do plano após os dois anos de fiscalização",
    "emp-franqueado-abre-negocio-concorrente-durante-vigencia-contrato": "Franqueado que abre negócio concorrente na vigência do contrato",
    "emp-moeda-estrangeira-indexacao-contrato-empresarial-cobranca": "Contrato empresarial em moeda estrangeira é válido no Brasil?",
    "emp-novacao-divida-apos-aprovacao-plano-recuperacao": "Novação da dívida após aprovado o plano de recuperação",
}

# (intent_id, heading) -> new text
SECTION_TEXT_FIXES = {
    ("emp-termos-de-uso-plataforma-como-elaborar-empresa", "Passo 3 — privacidade e comunicação clara sobre dados"): (
        "Privacidade também é parte do documento. O usuário tem direito a intimidade preservada e a "
        "informação clara sobre a coleta de dados, garantias que o Marco Civil da Internet lhe atribui "
        "e que os termos de uso — normalmente ao lado de uma política de privacidade específica — "
        "precisam refletir de forma acessível, não apenas em juridiquês."
    ),
    ("emp-plataforma-suspender-banir-usuario-criterio-empresa", "O que muda quando envolve conteúdo ou comunicação do usuário"): (
        "Direitos do usuário como intimidade preservada e proteção de dados pessoais, previstos no "
        "Marco Civil da Internet, entram na conta quando o banimento se apoia em histórico de "
        "atividade ou em dado coletado sem transparência sobre essa finalidade — usar esse tipo de "
        "informação como justificativa exige que a coleta e o uso já estivessem previstos, com "
        "clareza, na política de privacidade da plataforma."
    ),
    ("emp-sociedade-simples-nao-empresaria-insolvencia-civil", "Por que a Lei 11.101/2005 não se aplica"): (
        "Sociedade simples — categoria que reúne profissões regulamentadas e atividades não "
        "organizadas como empresa, nos termos do art. 966 do Código Civil — fica de fora do conceito "
        "de empresário e sociedade empresária que a Lei nº 11.101, de 09/02/2005, usa para definir "
        "quem pode recorrer à recuperação judicial, à recuperação extrajudicial ou responder por "
        "pedido de falência. Mesmo movimentando valores relevantes, ela não pode requerer recuperação "
        "judicial nem está sujeita a pedido de falência por credor."
    ),
    ("emp-deposito-elisivo-contestar-pedido-de-falencia", "O que o depósito elisivo faz, na prática"): (
        "Diante de pedido de falência baseado em impontualidade injustificada — procedimento que a "
        "Lei 11.101/2005 disciplina para o empresário e a sociedade empresária —, a empresa pode "
        "depositar em juízo o valor correspondente ao total do crédito cobrado, acrescido de "
        "correção, juros e honorários. Esse depósito elide, ou seja, afasta, a decretação da falência "
        "com base naquele pedido específico, permitindo que a discussão sobre a dívida continue sem o "
        "risco imediato de quebra."
    ),
    ("emp-contestar-pedido-falencia-defesas-cabiveis", "Vício no protesto do título"): (
        "O pedido de falência fundado em impontualidade injustificada, disciplinado pela Lei "
        "11.101/2005 para o empresário e a sociedade empresária, depende de protesto regular do "
        "título não pago. Protesto feito sem a notificação adequada, em endereço desatualizado, ou "
        "com irregularidade formal no procedimento cartorário, pode ser usado como defesa para "
        "afastar a base do pedido de falência."
    ),
    ("emp-comprar-ativos-empresa-em-recuperacao-sem-sucessao", "A regra da venda livre de sucessão"): (
        "Vender filiais ou unidades produtivas isoladas da empresa em recuperação é possibilidade que "
        "a Lei 11.101/2005 abre expressamente, com uma proteção decisiva para quem compra: o objeto "
        "da alienação fica livre de qualquer ônus, sem que o arrematante suceda o devedor nas "
        "obrigações anteriores — nem as tributárias, nem as trabalhistas, nem as de acidente de "
        "trabalho. É essa proteção que viabiliza economicamente a compra de ativos de empresa em "
        "crise."
    ),
    ("emp-comprar-bens-empresa-falida-sem-sucessao-divida", "A venda de ativos na falência também é livre de sucessão"): (
        "Na falência, a alienação de bens da massa falida — em bloco ou individualmente — segue "
        "disciplina própria da Lei 11.101/2005: quando se trata de venda de filiais ou de unidades "
        "produtivas isoladas, o comprador não herda as obrigações do devedor falido, porque o objeto "
        "da venda sai livre de ônus, na mesma lógica de proteção que a lei também aplica à "
        "recuperação judicial."
    ),
    ("emp-crime-falimentar-responsabilizacao-penal", "O que diferencia crise de crime"): (
        "Dentro da disciplina que a Lei 11.101/2005 dá à recuperação judicial, à recuperação "
        "extrajudicial e à falência do empresário e da sociedade empresária, existe um capítulo à "
        "parte dedicado aos crimes falimentares — condutas praticadas antes ou depois da decretação "
        "da falência (ou, em algumas hipóteses, durante a recuperação judicial) que prejudicam "
        "credores de forma que a lei considera criminosa, não apenas civilmente reprovável."
    ),
    ("emp-descumprimento-plano-apos-fiscalizacao-dois-anos", "O que a fiscalização de dois anos realmente significa"): (
        "Enquanto não se cumprem as obrigações do plano com vencimento em até dois anos após a "
        "concessão da recuperação, o devedor permanece sob fiscalização direta do juízo — é assim que "
        "a Lei 11.101/2005 desenha o período ativo de acompanhamento da recuperação judicial. Passado "
        "esse período, sem pedido de descumprimento pendente, o processo de recuperação é encerrado — "
        "mas isso não significa que o plano deixou de ter obrigações a cumprir depois disso, quando "
        "ele prevê parcelas com vencimento posterior."
    ),
    ("emp-novacao-divida-apos-aprovacao-plano-recuperacao", "O que a novação muda no crédito original"): (
        "Aprovado o plano de recuperação judicial, os créditos anteriores ao pedido passam por "
        "novação — efeito que a Lei 11.101/2005 prevê expressamente e que obriga tanto o devedor "
        "quanto todos os credores a ele sujeitos, sem prejuízo das garantias que a própria lei "
        "ressalva. Isso significa que a dívida original é substituída pela obrigação nos termos do "
        "plano — não é apenas um parcelamento da dívida antiga, é uma nova obrigação juridicamente "
        "distinta."
    ),
}

EXTRA_SECTION_FOR = {
    "emp-comprar-ativos-empresa-em-recuperacao-sem-sucessao": {
        "heading": "O que muda para o vendedor original diante desse tipo de venda",
        "text": (
            "Para a empresa em recuperação, vender a unidade produtiva isolada dentro dessa estrutura "
            "formal costuma trazer o recurso mais rápido e com maior segurança jurídica do que uma "
            "venda avulsa fora do processo, justamente porque a proteção contra sucessão amplia o "
            "universo de interessados dispostos a pagar um preço melhor pelo ativo."
        ),
    },
}


def main():
    with open(PATH, "rb") as handle:
        raw = handle.read()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("empresarial-w3-07 mudou; releia antes de aplicar")

    lines = raw.decode("utf-8").splitlines()
    pages = [json.loads(line) for line in lines if line.strip()]
    by_id = {page["intent_id"]: page for page in pages}

    for intent_id, new_title in TITLE_FIXES.items():
        page = by_id[intent_id]
        assert 20 <= len(new_title) <= 65, (intent_id, len(new_title))
        page["title"] = new_title

    for (intent_id, heading), new_text in SECTION_TEXT_FIXES.items():
        page = by_id[intent_id]
        found = False
        for section in page["sections"]:
            if section["heading"] == heading:
                section["text"] = new_text
                found = True
                break
        if not found:
            raise SystemExit(f"heading ausente: {intent_id} / {heading}")

    for intent_id, extra in EXTRA_SECTION_FOR.items():
        page = by_id[intent_id]
        if not any(s["heading"] == extra["heading"] for s in page["sections"]):
            page["sections"].append(extra)

    for intent_id in set(TITLE_FIXES) | {i for i, _ in SECTION_TEXT_FIXES} | set(EXTRA_SECTION_FOR):
        page = by_id[intent_id]
        page["word_count"] = body_word_count(page)

    directory = os.path.dirname(PATH)
    fd, temporary = tempfile.mkstemp(
        prefix=".empresarial-w3-07.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for item in pages:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    new_hash = hashlib.sha256(open(PATH, "rb").read()).hexdigest()
    print("REPAIR OK new_sha256=" + new_hash)


if __name__ == "__main__":
    main()
