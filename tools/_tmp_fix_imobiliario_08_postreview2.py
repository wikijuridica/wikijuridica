#!/usr/bin/env python3
"""Aplica por CAS as correções da segunda pós-revisão do imobiliário-08."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path


TARGET = Path("data/editorial/v2_pages/imobiliario-08.jsonl")
EXPECTED_SHA256 = "4a478db66f02edc2fb009a7bd675187ff8efc9eac53569639aa721d1f41ecd94"
INTERMEDIATE_SHA256 = "5dedbbd9c1c33c3c0e432ad17072e80b210478efe8f6c03c0957ccd470b4ca31"
OUTPUT_SHA256 = "807ce8486c4010b34b6c97cfc24db0df38eab01a0fbb188ca9a602b3d7a3b016"
TOUCHED = {
    "imob-lucros-cessantes-cumulacao-multa",
    "imob-correcao-incc-atraso",
    "imob-taxa-evolucao-obra",
    "imob-adjudicacao-extrajudicial-procedimento",
    "imob-contrato-gaveta-riscos",
}


def words(value):
    folded = "".join(
        char
        for char in unicodedata.normalize("NFD", (value or "").lower())
        if unicodedata.category(char) != "Mn"
    )
    return re.findall(r"[^\W_]+", folded, re.UNICODE)


def body_word_count(page):
    values = [page.get("opening", "")]
    for item in page.get("sections", []):
        values.extend((item.get("heading", ""), item.get("text", "")))
    for item in page.get("faq", []):
        values.extend((item.get("q", ""), item.get("a", "")))
    return sum(len(words(value)) for value in values)


def section(page, heading):
    return next(item for item in page["sections"] if item["heading"] == heading)


def rewrite_lost_profits(page):
    target = section(page, "Por que lucros cessantes de mesma natureza tendem a ser absorvidos")
    target["text"] += (
        " A questão de ordem do julgamento registrou que os dispositivos da Lei 13.786/2018 "
        "não seriam aplicados diretamente aos repetitivos, formados sobre contratos anteriores. "
        "Por isso, o Tema 970 não deve ser estendido mecanicamente para apagar o regime legal "
        "dos contratos posteriores à lei."
    )


def tema_996_scope_text():
    return (
        " O alcance vinculante descrito pelo STJ é o da promessa de compra e venda de imóvel "
        "na planta no Programa Minha Casa, Minha Vida, em financiamento associativo, para as "
        "faixas de renda 1,5, 2 e 3. Fora desse recorte, o Tema 996 não deve ser apresentado "
        "como tese repetitiva universal; o enquadramento depende das normas, do contrato e dos "
        "precedentes aplicáveis ao caso."
    )


def rewrite_incc(page):
    target = section(page, "A tese do Tema 996 para o indexador depois do prazo")
    target["text"] += tema_996_scope_text()


def rewrite_construction_interest(page):
    target = section(page, "Por que a cobrança se torna questionável durante o atraso")
    target["text"] += (
        " O Tema 996 delimitou essas teses ao Programa Minha Casa, Minha Vida, nas faixas de "
        "renda 1,5, 2 e 3. O julgamento examinou contratos com financiamento associativo; por "
        "isso, negócio situado fora desse programa não recebe automaticamente o mesmo resultado "
        "como precedente repetitivo universal e exige enquadramento próprio."
    )


def rewrite_adjudication_registry(page):
    section(page, "Documentos que o requerente precisa reunir")["text"] = (
        "Além da ata notarial e da prova de notificação, o pedido deve trazer o instrumento de "
        "promessa de compra e venda ou de cessão, os comprovantes de quitação, a certidão da "
        "matrícula e a qualificação das partes. Se o requerimento inicial não preencher os "
        "requisitos, o art. 440-Q do Provimento 150 determina que o requerente seja intimado, "
        "por escrito e de forma fundamentada, para emendá-lo em 10 dias úteis. Sem a providência, "
        "o processo é extinto e a prenotação é cancelada. Na qualificação posterior, eventual "
        "exigência pode gerar nota devolutiva e, em caso de exigência ou rejeição, cabe a dúvida "
        "do art. 198 da Lei 6.015/1973. A falta inicial não autoriza pular a emenda e suscitar de "
        "ofício a dúvida como primeira resposta."
    )


def rewrite_unregistered_promise(page):
    page["faq"][0]["a"] = (
        "Não é automaticamente ilegal. Sem registro, o compromisso não constitui o direito real "
        "do art. 1.417, mas seus efeitos não se limitam exclusivamente às partes: nas condições "
        "da Súmula 84 do STJ, a posse oriunda do compromisso não registrado pode fundamentar "
        "embargos de terceiro contra uma penhora. Isso não elimina os riscos perante o credor "
        "fiduciário nem substitui a regularização."
    )


REWRITERS = {
    "imob-lucros-cessantes-cumulacao-multa": rewrite_lost_profits,
    "imob-correcao-incc-atraso": rewrite_incc,
    "imob-taxa-evolucao-obra": rewrite_construction_interest,
    "imob-adjudicacao-extrajudicial-procedimento": rewrite_adjudication_registry,
    "imob-contrato-gaveta-riscos": rewrite_unregistered_promise,
}


def build_output(payload):
    original_lines = payload.decode("utf-8").splitlines(keepends=True)
    pages = [json.loads(line) for line in original_lines if line.strip()]
    if len(pages) != 22 or len({page["intent_id"] for page in pages}) != 22:
        raise RuntimeError("o shard deve manter 22 intents únicos")
    for page in pages:
        rewrite = REWRITERS.get(page["intent_id"])
        if rewrite is not None:
            rewrite(page)
            page["word_count"] = body_word_count(page)
    output_lines = []
    for original, page in zip(original_lines, pages):
        if page["intent_id"] in TOUCHED:
            output_lines.append(
                json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
        else:
            output_lines.append(original)
    changed = {
        json.loads(before)["intent_id"]
        for before, after in zip(original_lines, output_lines)
        if before != after
    }
    if changed != TOUCHED:
        raise RuntimeError(f"escopo alterado divergiu: {sorted(changed)}")
    for page in pages:
        if page["word_count"] != body_word_count(page):
            raise RuntimeError(f"word_count inexato: {page['intent_id']}")
        if not 2 <= len(page["official_sources"]) <= 5:
            raise RuntimeError(f"fontes fora da faixa: {page['intent_id']}")
    return "".join(output_lines).encode("utf-8"), pages


def build_dedupe_output(payload):
    original_lines = payload.decode("utf-8").splitlines(keepends=True)
    pages = [json.loads(line) for line in original_lines if line.strip()]
    target_page = next(
        page for page in pages if page["intent_id"] == "imob-taxa-evolucao-obra"
    )
    target_section = section(
        target_page, "Por que a cobrança se torna questionável durante o atraso"
    )
    old_scope = tema_996_scope_text()
    new_scope = (
        " O Tema 996 delimitou essas teses ao Programa Minha Casa, Minha Vida, nas faixas de "
        "renda 1,5, 2 e 3. O julgamento examinou contratos com financiamento associativo; por "
        "isso, negócio situado fora desse programa não recebe automaticamente o mesmo resultado "
        "como precedente repetitivo universal e exige enquadramento próprio."
    )
    if target_section["text"].count(old_scope) != 1:
        raise RuntimeError("parágrafo duplicado do Tema 996 não foi localizado uma vez")
    target_section["text"] = target_section["text"].replace(old_scope, new_scope)
    target_page["word_count"] = body_word_count(target_page)
    output_lines = []
    for original, page in zip(original_lines, pages):
        if page["intent_id"] == target_page["intent_id"]:
            output_lines.append(
                json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
        else:
            output_lines.append(original)
    changed = {
        json.loads(before)["intent_id"]
        for before, after in zip(original_lines, output_lines)
        if before != after
    }
    if changed != {target_page["intent_id"]}:
        raise RuntimeError(f"escopo anti-duplicidade divergiu: {sorted(changed)}")
    if target_page["word_count"] != body_word_count(target_page):
        raise RuntimeError("word_count inexato após correção anti-duplicidade")
    return "".join(output_lines).encode("utf-8"), pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    payload = TARGET.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if actual == EXPECTED_SHA256:
        encoded, pages = build_output(payload)
    elif actual == INTERMEDIATE_SHA256:
        encoded, pages = build_dedupe_output(payload)
    elif OUTPUT_SHA256 and actual == OUTPUT_SHA256:
        encoded, pages = payload, [
            json.loads(line) for line in payload.decode("utf-8").splitlines() if line
        ]
    else:
        raise SystemExit(
            f"CAS falhou: esperado {EXPECTED_SHA256} ou {INTERMEDIATE_SHA256}, encontrado {actual}"
        )
    output_hash = hashlib.sha256(encoded).hexdigest()
    print(output_hash)
    for page in pages:
        if page["intent_id"] in TOUCHED:
            print(page["intent_id"], f"words={page['word_count']}")
    if not args.apply:
        return
    if output_hash != OUTPUT_SHA256:
        raise SystemExit(
            f"fingerprint de saída não fixado: esperado {OUTPUT_SHA256!r}, calculado {output_hash}"
        )
    fd, temporary = tempfile.mkstemp(
        prefix=".imobiliario-08-postreview2.", suffix=".tmp", dir=TARGET.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if hashlib.sha256(TARGET.read_bytes()).hexdigest() != actual:
            raise RuntimeError("CAS mudou antes da troca atômica")
        os.replace(temporary, TARGET)
        directory_fd = os.open(TARGET.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == "__main__":
    main()
