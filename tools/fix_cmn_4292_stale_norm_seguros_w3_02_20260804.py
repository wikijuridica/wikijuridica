#!/usr/bin/env python3
"""Corrige a Resolução CMN nº 4.292/2013 (revogada em 1º/3/2023) citada como
norma VIGENTE no corpo de data/editorial/v2_pages/seguros-w3-02.jsonl
(intent_id=seg-danos-prestamista-portabilidade-credito).

Motivação (2026-08-04, redator-juridico): auditoria de passivo normativo
achou 4 ocorrências de "4.292" em 3 shards (bancario-w3-03.jsonl x2,
seguros-17.jsonl x1, seguros-w3-02.jsonl x1). Das 4, apenas a de
seguros-w3-02.jsonl é ERRO: a seção "O que exatamente acontece na
portabilidade" descreve, em tempo presente e como regra vinculante ATUAL
("A Resolução CMN nº 4.292/2013 obriga... A mesma norma exige... determina..."),
disposições que hoje são regidas pela Resolução CMN nº 5.057, de 15 de
dezembro de 2022 (em vigor desde 1º de março de 2023, quando revogou a
4.292/2013 — DOU: https://www.in.gov.br/web/dou/-/resolucao-cmn-n-5.057-de-
15-de-dezembro-de-2022-451608611). As outras 3 ocorrências (bancario-w3-03.jsonl
x2 e seguros-17.jsonl x1) já narram corretamente a revogação/substituição e
NÃO são tocadas por este script.

Mapeamento de dispositivo (fonte oficial, verificado 2026-08-04):
  - definição de portabilidade: antes CMN 4.292/2013 (sem art. citado no
    texto) -> agora CMN 5.057/2022, art. 2º, I.
  - limite de valor/prazo ao saldo devedor/prazo remanescente: agora
    CMN 5.057/2022, art. 6º (mesmo artigo já citado alhures no acervo,
    ex.: bancario-w3-03.jsonl).
  - troca eletrônica de informações entre credora original e proponente:
    agora CMN 5.057/2022, art. 5º.

Segurança: lock exclusivo de estoque canônico + CAS sobre os bytes exatos do
shard, escrita atômica (mkstemp + fsync + os.replace + fsync do diretório),
preimagem gravada em data/ops/ antes de aplicar. --dry-run (padrão) só
imprime o diff; --apply escreve. Idempotente: se o texto já estiver
corrigido, é no-op verde.
"""

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if os.fspath(ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(ROOT))

from tools.v2_stock_epoch import StockEpochBusy, canonical_stock_write_lease

SHARD_REL = "data/editorial/v2_pages/seguros-w3-02.jsonl"
SHARD = ROOT / SHARD_REL
LOCK = ROOT / "data/editorial/.fix-cmn-4292-seguros-w3-02-20260804.lock"
LEDGER = ROOT / "data/ops/fix_cmn_4292_stale_norm_20260804.jsonl"

INTENT_ID = "seg-danos-prestamista-portabilidade-credito"
SECTION_HEADING = "O que exatamente acontece na portabilidade"

OLD_TEXT = (
    "A Resolução CMN nº 4.292/2013 obriga as instituições financeiras a "
    "garantir a portabilidade das operações de crédito realizadas com "
    "pessoas naturais, definindo-a como a transferência da operação da "
    "instituição credora original para a instituição proponente, por "
    "solicitação do devedor.\n\nA mesma norma exige que o valor e o prazo "
    "na nova instituição não superem o saldo devedor e o prazo "
    "remanescente da operação original, e determina que a troca de "
    "informações entre os bancos ocorra eletronicamente. O ponto que "
    "interessa aqui: a operação original é quitada. Ela deixa de existir "
    "naquele banco."
)

NEW_TEXT = (
    "A Resolução CMN nº 5.057/2022 obriga as instituições financeiras a "
    "garantir a portabilidade das operações de crédito realizadas com "
    "pessoas naturais, definindo-a, no art. 2º, inciso I, como a "
    "transferência da operação da instituição credora original para a "
    "instituição proponente, por solicitação do devedor.\n\nA mesma norma "
    "exige, no art. 6º, que o valor e o prazo na nova instituição não "
    "superem o saldo devedor e o prazo remanescente da operação original, "
    "e determina, no art. 5º, que a troca de informações entre os bancos "
    "ocorra por meio de sistema eletrônico gerenciado por entidade "
    "operadora de sistema de registro, depósito, compensação ou "
    "liquidação autorizada a funcionar pelo Banco Central. O ponto que "
    "interessa aqui: a operação original é quitada. Ela deixa de existir "
    "naquele banco."
)

assert "4.292" not in NEW_TEXT
assert "5.057" in NEW_TEXT


@contextmanager
def exclusive_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        os.fchmod(fd, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def words_of(value):
    folded = "".join(
        char for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )
    return re.findall(r"[^\W_]+", folded.lower(), re.UNICODE)


def body_word_count(page):
    total = len(words_of(page.get("opening", "")))
    for section in page.get("sections", []):
        total += len(words_of(section.get("heading", "")))
        total += len(words_of(section.get("text", "")))
    for item in page.get("faq", []):
        total += len(words_of(item.get("q", "")))
        total += len(words_of(item.get("a", "")))
    return total


def atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_ledger(entry):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
    fd = os.open(LEDGER, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def run(apply_changes):
    if not SHARD.exists():
        raise SystemExit(f"{SHARD_REL}: não encontrado")

    payload = SHARD.read_bytes()
    actual_sha_before = sha256(payload)
    lines = payload.decode("utf-8").splitlines()
    if not lines:
        raise SystemExit(f"{SHARD_REL}: shard vazio")

    parsed = []
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            raise SystemExit(f"{SHARD_REL}: linha em branco {line_number}")
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise SystemExit(f"{SHARD_REL}: linha {line_number} não é objeto")
        parsed.append((line_number, raw, record))

    target_index = None
    for index, (line_number, raw, record) in enumerate(parsed):
        if record.get("intent_id") == INTENT_ID:
            target_index = index
            break
    if target_index is None:
        raise SystemExit(f"{SHARD_REL}: intent_id={INTENT_ID} não encontrado")

    line_number, raw, record = parsed[target_index]
    sections = record.get("sections", [])
    section_index = None
    for index, section in enumerate(sections):
        if section.get("heading") == SECTION_HEADING:
            section_index = index
            break
    if section_index is None:
        raise SystemExit(
            f"{SHARD_REL}: seção '{SECTION_HEADING}' não encontrada em {INTENT_ID}"
        )

    current_text = sections[section_index].get("text", "")

    if current_text == NEW_TEXT:
        print(f"already-fixed shard={SHARD_REL} intent={INTENT_ID} sha256={actual_sha_before}")
        return

    if current_text != OLD_TEXT:
        raise SystemExit(
            f"{SHARD_REL}: texto da seção não bate com o OLD_TEXT esperado nem "
            "com o NEW_TEXT já aplicado — divergência inesperada, abortando "
            "para evitar sobrescrever edição concorrente"
        )

    before_word_count = record.get("word_count")

    print(f"--- shard={SHARD_REL} intent={INTENT_ID} seção='{SECTION_HEADING}' ---")
    print("ANTES:")
    print(current_text)
    print()
    print("DEPOIS:")
    print(NEW_TEXT)
    print()

    if not apply_changes:
        print("(dry-run: nenhuma escrita realizada)")
        return

    record = json.loads(raw)  # cópia limpa a partir do raw original
    record["sections"][section_index]["text"] = NEW_TEXT
    after_word_count = body_word_count(record)
    record["word_count"] = after_word_count

    new_raw = json.dumps(record, ensure_ascii=False)

    parsed[target_index] = (line_number, new_raw, record)

    # CAS final: re-lê o shard e confirma que ninguém mudou os bytes desde a
    # leitura inicial.
    if SHARD.read_bytes() != payload:
        raise SystemExit(f"{SHARD_REL}: mudou durante a transação — abortado")

    output_lines = [entry_raw for _, entry_raw, _ in parsed]
    rewritten = ("\n".join(output_lines) + "\n").encode("utf-8")

    append_ledger(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "shard": SHARD_REL,
            "intent_id": INTENT_ID,
            "section_heading": SECTION_HEADING,
            "sha256_before": actual_sha_before,
            "text_before": current_text,
            "text_after": NEW_TEXT,
            "word_count_before": before_word_count,
            "word_count_after": after_word_count,
            "reason": (
                "Resolução CMN 4.292/2013 revogada desde 2023-03-01; "
                "substituída pela Resolução CMN 5.057/2022 (arts. 2, I; 5; 6) "
                "conforme in.gov.br DOU"
            ),
        }
    )

    atomic_write(SHARD, rewritten)
    print(
        f"fixed shard={SHARD_REL} intent={INTENT_ID} "
        f"sha256_after={sha256(rewritten)} word_count {before_word_count}->{after_word_count}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="aplica a escrita (padrão: dry-run)")
    args = parser.parse_args()

    try:
        with canonical_stock_write_lease(ROOT):
            with exclusive_lock(LOCK):
                run(apply_changes=args.apply)
    except StockEpochBusy as error:
        print(f"fix-cmn-4292: canonical stock busy: {error}", file=sys.stderr)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
