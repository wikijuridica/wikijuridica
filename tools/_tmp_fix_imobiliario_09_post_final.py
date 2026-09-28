#!/usr/bin/env python3
"""Ajustes finais de faixa, granularidade de artigo e PT-BR do imobiliário-09."""

import hashlib
import json
import os
import tempfile

from _tmp_fix_imobiliario_09_lib import body_word_count


TARGET = "data/editorial/v2_pages/imobiliario-09.jsonl"
EXPECTED_SHA256 = "e68afe5666cbf187a9c723e17fd10744e6a687103f2efcfc77d311c7480dbda2"

APPENDS = {
    "imob-area-menor-escritura": (
        " Leve ao cálculo a área nominal e a efetivamente levantada, porque o percentual deve usar grandezas comparáveis. "
        "Se houver mais de uma matrícula ou lote, não agregue medidas sem demonstrar qual objeto foi vendido."
    ),
    "imob-metragem-planta-menor": (
        " O relatório técnico deve ser assinado, identificar a unidade e anexar a planta usada como referência. "
        "Sem essa correspondência, uma diferença aparente pode resultar apenas de métodos de medição incompatíveis."
    ),
    "imob-itbi-base-calculo": (
        " Preserve também a data da avaliação municipal e os imóveis comparados, pois mercado e estado de conservação mudam. "
        "Uma tabela sem memória individual não substitui o arbitramento previsto no CTN."
    ),
    "imob-comprei-nao-registrei": (
        " Enquanto a regularização tramita, acompanhe a matrícula para detectar novos protocolos e não entregue documentos originais "
        "sem recibo. A demora pode permitir fatos supervenientes que exigem medida diferente daquela inicialmente planejada."
    ),
    "imob-venda-sem-outorga-conjugal": (
        " Se o título ainda não foi registrado, informe a divergência ao profissional responsável e evite novos pagamentos até definir "
        "a forma válida. O simples protocolo não transforma consentimento ausente em anuência regular."
    ),
    "imob-compra-imovel-espolio": (
        " Antes do protocolo final, confira se surgiu nova indisponibilidade ou decisão no inventário e se a proposta continua dentro "
        "dos limites autorizados. Mudança de preço ou comprador pode exigir nova apreciação ou escritura."
    ),
    "imob-compra-imovel-leilao-ocupado": (
        " Consulte o processo novamente antes de pedir a posse, porque recursos, acordos ou ordens posteriores ao edital podem alterar "
        "o cumprimento. A certidão da arrematação não resume todo o histórico processual relevante."
    ),
    "imob-preferencia-condomino-venda-fracao": (
        " Calcule o depósito com base no título e nos encargos efetivamente assumidos pelo terceiro, documentando a origem dos recursos. "
        "Oferta de valor nominal menor não reproduz igualdade quando ignora prazo, garantia ou comissão."
    ),
}


def replace_visible(page, old, new):
    page["opening"] = page.get("opening", "").replace(old, new)
    for item in page.get("sections", []):
        item["heading"] = item.get("heading", "").replace(old, new)
        item["text"] = item.get("text", "").replace(old, new)
    for item in page.get("faq", []):
        item["q"] = item.get("q", "").replace(old, new)
        item["a"] = item.get("a", "").replace(old, new)


def main():
    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    by_intent = {page["intent_id"]: page for page in pages}

    for intent_id, text in APPENDS.items():
        by_intent[intent_id]["sections"][-1]["text"] += text

    replacements = {
        "O artigo 1.245 do Código Civil estabelece": "O artigo 1245 (art. 1.245) do Código Civil estabelece",
        "Pelo artigo 1.245 do Código Civil": "Pelo artigo 1245 (art. 1.245) do Código Civil",
        "O artigo 1.245 do Código Civil exige": "O artigo 1245 (art. 1.245) do Código Civil exige",
        "do artigo 1.245 do Código Civil": "do artigo 1245 (art. 1.245) do Código Civil",
        "conforme o artigo 1.647 do Código Civil": "conforme o artigo 1647 (art. 1.647) do Código Civil",
        "inciso I do artigo 1.647": "inciso I do artigo 1647 (art. 1.647)",
        "O artigo 1.648 permite": "O artigo 1648 (art. 1.648) permite",
        "Pelo artigo 1.649": "Pelo artigo 1649 (art. 1.649)",
        "O artigo 1.650 reserva": "O artigo 1650 (art. 1.650) reserva",
    }
    for page in pages:
        for old, new in replacements.items():
            replace_visible(page, old, new)

    hidden_form = by_intent["imob-escritura-quando-obrigatoria"]["sections"][0]
    hidden_form["text"] = hidden_form["text"].replace(
        "O contrato produz os efeitos que lhe cabem, mas a propriedade entre vivos só passa com a inscrição do título no Registro de Imóveis.",
        "O contrato produz os efeitos que lhe cabem, mas, conforme o artigo 1245 (art. 1.245) do Código Civil, a propriedade entre vivos só passa com a inscrição do título no Registro de Imóveis.",
    )
    eviction = by_intent["imob-evicao-perdi-imovel"]["sections"][1]
    eviction["text"] = "Nos termos do artigo 450, " + eviction["text"][0].lower() + eviction["text"][1:]
    latent = by_intent["imob-vicio-oculto-imovel-usado"]["sections"][0]
    latent["text"] = latent["text"].replace(
        "Provado o vício oculto,", "Nos termos do artigo 441, provado o vício oculto,"
    )
    preference = by_intent["imob-preferencia-condomino-venda-fracao"]["sections"][2]
    preference["text"] = preference["text"].replace(
        "o registro da escritura de compra e venda inicia o prazo,",
        "o registro da escritura de compra e venda, com a publicidade prevista pelo artigo 1245 (art. 1.245) do Código Civil, inicia o prazo,",
    )

    for page in pages:
        for item in page.get("official_sources", []):
            item["name"] = item.get("name", "").replace("ART.", "art.")
            item["anchor_claim"] = (
                item.get("anchor_claim", "")
                .replace("especifica do parágrafo", "específica do parágrafo")
                .replace("garantia da evicção, clausulas", "garantia da evicção, cláusulas")
                .replace("artigo 501 a pretensão", "artigo 501 à pretensão")
            )
        page["word_count"] = body_word_count(page)
        if not 600 <= page["word_count"] <= 1400:
            raise SystemExit(f"faixa final inválida: {page['intent_id']}={page['word_count']}")

    rendered = "".join(
        json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n" for page in pages
    ).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-09-post-final.", dir=os.path.dirname(TARGET))
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
    print(f"ajustes finais promovidos; sha256={hashlib.sha256(rendered).hexdigest()}")


if __name__ == "__main__":
    main()

