#!/usr/bin/env python3
"""Corrige homografos e escolhas ruins do spellcheck no primeiro bloco."""

import hashlib
import json
import os
import re
import tempfile

from _tmp_fix_imobiliario_09_lib import body_word_count


TARGET = "data/editorial/v2_pages/imobiliario-09.jsonl"
EXPECTED_SHA256 = "96482282969396b55c8185bd1a51486b58660bad0691f9a345e15793235dedb3"
INTENTS = {
    "imob-vicio-construtivo-acao",
    "imob-vicio-oculto-imovel-usado",
    "imob-evicao-perdi-imovel",
    "imob-area-menor-escritura",
    "imob-metragem-planta-menor",
    "imob-itbi-base-calculo",
}
TOKEN = re.compile(r"[^\W_]+", re.UNICODE)

TOKENS = {
    "acoes": "ações",
    "analise": "análise",
    "anuncio": "anúncio",
    "ate": "até",
    "calculo": "cálculo",
    "clausula": "cláusula",
    "Clausula": "Cláusula",
    "comodo": "cômodo",
    "deficit": "déficit",
    "diagnostico": "diagnóstico",
    "diligencia": "diligência",
    "divida": "dívida",
    "estrategia": "estratégia",
    "especifico": "específico",
    "exito": "êxito",
    "forcado": "forçado",
    "ha": "há",
    "imoveis": "imóveis",
    "improprio": "impróprio",
    "matricula": "matrícula",
    "memoria": "memória",
    "moveis": "móveis",
    "negocio": "negócio",
    "numero": "número",
    "pagina": "página",
    "paragrafo": "parágrafo",
    "peca": "peça",
    "pericia": "perícia",
    "Pericia": "Perícia",
    "porem": "porém",
    "preconstituidos": "preconstituídos",
    "publica": "pública",
    "recalculo": "recálculo",
    "referencia": "referência",
    "sindico": "síndico",
    "SO": "só",
    "Titulo": "Título",
    "titulo": "título",
    "topografo": "topógrafo",
    "tributaria": "tributária",
    "uteis": "úteis",
    "valida": "válida",
    "vicio": "vício",
}

PHRASES = {
    "Areá": "Área",
    "areá": "área",
    "apuracão": "apuração",
    "fê": "fé",
    "conserva-la": "conservá-la",
    "cobrar a construtora, e preciso": "cobrar a construtora, é preciso",
    "O período e contado": "O período é contado",
    "peça quebrada e automaticamente": "peça quebrada é automaticamente",
    "também e preciso": "também é preciso",
    "valor da causa não e o": "valor da causa não é o",
    "só e redibitório": "só é redibitório",
    "preço não e oculto": "preço não é oculto",
    "regra geral e decadência": "regra geral é decadência",
    "o prazo e reduzido": "o prazo é reduzido",
    "E preciso ligar": "É preciso ligar",
    "não e consequência automática": "não é consequência automática",
    "Evicção e a perda": "Evicção é a perda",
    "não e obrigatória": "não é obrigatória",
    "medir corretamente, e preciso": "medir corretamente, é preciso",
    "o bem e identificado": "o bem é identificado",
    "a questão e contratual": "a questão é contratual",
    "privativa não e área": "privativa não é área",
    "artigo 500 e relativa": "artigo 500 é relativa",
    "o pedido e corrigir": "o pedido é corrigir",
    "vigésimo e presunção": "vigésimo é presunção",
    "a base e o valor": "a base é o valor",
    "presunção não e absoluta": "presunção não é absoluta",
    "ilegalidade e demonstrável": "ilegalidade é demonstrável",
    "prefeitura e obrigada": "prefeitura é obrigada",
    "Venda ocasional entre particulares não e": "Venda ocasional entre particulares não é",
    "Área privativa é área útil são": "Área privativa e área útil são",
    "matrícula contem": "matrícula contém",
    "segue logica": "segue lógica",
    "vinculada a do IPTU": "vinculada à do IPTU",
    "Cinco por cento e presunção": "Cinco por cento é presunção",
    "usa-lo": "usá-lo",
    "aplica, em regra, a prescrição de dez anos à reparação contratual": "aplica, em regra, o prazo prescricional de dez anos à pretensão de reparação contratual",
    "a origem esta na": "a origem está na",
    "a diferença esta na": "a diferença está na",
    "ligada a obra": "ligada à obra",
    "material ou a execução": "material ou à execução",
    "anos a reparação": "anos à reparação",
    "proporcional a gravidade": "proporcional à gravidade",
    "conduta a tentativa": "conduta à tentativa",
    "abrigo a omissão": "abrigo à omissão",
    "anterior a compra": "anterior à compra",
    "vincular a base do ITBI a do IPTU": "vincular a base do ITBI à do IPTU",
}


def fix(value):
    for old, new in PHRASES.items():
        value = value.replace(old, new)
    value = TOKEN.sub(lambda match: TOKENS.get(match.group(0), match.group(0)), value)
    for old, new in PHRASES.items():
        value = value.replace(old, new)
    return value


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    for page in pages:
        if page.get("intent_id") not in INTENTS:
            continue
        page["opening"] = fix(page.get("opening", ""))
        for item in page.get("sections", []):
            item["heading"] = fix(item.get("heading", ""))
            item["text"] = fix(item.get("text", ""))
        for item in page.get("faq", []):
            item["q"] = fix(item.get("q", ""))
            item["a"] = fix(item.get("a", ""))
        for item in page.get("official_sources", []):
            item["name"] = fix(item.get("name", ""))
            item["anchor_claim"] = fix(item.get("anchor_claim", ""))
        page["word_count"] = body_word_count(page)

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-09-post-a.", dir=os.path.dirname(TARGET))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        with open(TARGET, "rb") as handle:
            current = hashlib.sha256(handle.read()).hexdigest()
        if current != EXPECTED_SHA256:
            raise SystemExit(f"CAS falhou antes da promoção: {current}")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"homografos corrigidos; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()
