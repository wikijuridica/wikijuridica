#!/usr/bin/env python3
"""Corrige a incompatibilidade entre contestação e purgação da mora."""

import hashlib
import json
import os
import re
import tempfile
import unicodedata


TARGET = "data/editorial/v2_pages/imobiliario-04.jsonl"
EXPECTED_SHA256 = "2f9c42b55edb5418195f95cbb61a9cfd31ca5c23250e8d61d77db7b78b88027d"
INFO_593 = "https://processo.stj.jus.br/SCON/GetPDFINFJ?edicao=0593"


def words(value):
    plain = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", plain.lower(), re.UNICODE)


def body_word_count(page):
    values = [page.get("opening", "")]
    for section in page.get("sections", []):
        values.extend((section.get("heading", ""), section.get("text", "")))
    for item in page.get("faq", []):
        values.extend((item.get("q", ""), item.get("a", "")))
    return sum(len(words(value)) for value in values)


def main():
    original = open(TARGET, "rb").read()
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual_sha}")
    pages = [json.loads(line) for line in original.decode("utf-8").splitlines() if line.strip()]
    page = next(item for item in pages if item.get("intent_id") == "imob-despejo-defesa-inquilino")

    page["opening"] = (
        "A defesa começa pela petição inicial e por eventual decisão liminar, não por uma lista genérica de argumentos. "
        "Falta de pagamento, término, infração e retomada possuem fatos e provas diferentes. Na cobrança de aluguel, "
        "a lei permite purgar a mora em condições estritas, mas não autoriza reter aluguel unilateralmente por defeito "
        "no imóvel nem garante que depósito parcial e contestação do restante funcionem juntos."
    )
    page["sections"][1]["text"] = (
        "O artigo 62, inciso II, permite ao locatário e ao fiador evitar a rescisão mediante depósito judicial, no "
        "prazo de quinze dias contado da citação, de aluguéis e acessórios vencidos, multas, juros, custas e honorários "
        "fixados em dez por cento se o contrato não dispuser de outro modo. O benefício não é admitido quando já "
        "utilizado nos vinte e quatro meses anteriores à ação.\n\n"
        "A purgação é uma faculdade processual com depósito integral, e não simples argumento de defesa. Antes de "
        "contestar parte do cálculo e depositar outra, é preciso avaliar a compatibilidade dos atos: a posição assumida "
        "na contestação pode impedir que a parcela omitida seja tratada depois como mero complemento."
    )
    page["sections"][2]["text"] = (
        "Se o locador alega insuficiência e justifica a diferença, o artigo 62, inciso III, permite complementar em "
        "dez dias contados da intimação. Isso pressupõe intenção de completar a oferta. No Informativo 593, ao julgar "
        "o REsp 1.444.008, o STJ concluiu que contestar as parcelas não depositadas é ato incompatível com a vontade de "
        "purgar essa parte da mora; nessa situação, não cabe exigir nova intimação para complemento.\n\n"
        "Portanto, não se deve prometer que qualquer depósito parcial afasta o despejo nem sugerir, de modo genérico, "
        "depósito do incontroverso e contestação do saldo como estratégia sem risco. Contrato, planilha, objetivo de "
        "manter a locação e histórico de uso da faculdade precisam ser examinados antes do ato. Pagamento feito fora "
        "dos autos também não substitui silenciosamente o depósito exigido no procedimento, e as parcelas que vencem "
        "durante o processo continuam relevantes."
    )
    page["faq"] = [{
        "q": "Posso depositar só o valor incontroverso e contestar o restante para evitar o despejo?",
        "a": (
            "Não é uma combinação sem risco. O STJ entende que contestar as parcelas não depositadas pode ser "
            "incompatível com a intenção de purgá-las e afastar a oportunidade de complemento prevista no art. 62, III."
        ),
    }]
    page["official_sources"].append({
        "url": INFO_593,
        "name": "STJ, Informativo 593, REsp 1.444.008/RS",
        "anchor_claim": "incompatibilidade entre contestar a parcela não depositada e exigir complemento para purgar a mora",
    })
    if len(page["official_sources"]) != 5:
        raise SystemExit(f"fontes inesperadas: {len(page['official_sources'])}")
    page["word_count"] = body_word_count(page)

    encoded = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in pages).encode("utf-8")
    directory = os.path.dirname(TARGET)
    fd, temporary = tempfile.mkstemp(prefix=".imobiliario-04-peer.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(open(TARGET, "rb").read()).hexdigest() != EXPECTED_SHA256:
            raise SystemExit("CAS mudou antes da troca")
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    print(hashlib.sha256(encoded).hexdigest())
    print(page["intent_id"], page["word_count"], len(page["official_sources"]))


if __name__ == "__main__":
    main()
