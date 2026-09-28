#!/usr/bin/env python3
"""Reconta ``word_count`` de paginas v2 com a formula canonica do auditor.

Aceita um ou mais arquivos JSON (uma pagina) ou JSONL (uma pagina por linha).
O modo padrao e read-only e reprova quando encontra divergencia. ``--write``
corrige somente ``word_count`` de paginas reais; tombstones permanecem intactos.
Cada troca e atomica e aborta se o arquivo mudar entre a leitura e a promocao.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from tools.audit_v2_pages import body_word_count
    from tools import generate_v2_review_queue as safe_cas
except ModuleNotFoundError:
    from audit_v2_pages import body_word_count
    import generate_v2_review_queue as safe_cas


class RecountError(RuntimeError):
    """Erro de entrada ou de concorrencia que impede uma correcao segura."""


def _decode_json_strict(text, label):
    """Decodifica JSON sem colapsar silenciosamente chaves repetidas."""

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RecountError(
                    f"{label}: chave JSON duplicada: {key}")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise RecountError(
            f"{label}: JSON invalido: {exc.msg}") from exc


def _decode_jsonl(path, text):
    records = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise RecountError(
                f"{path}: linha {line_number} vazia em arquivo JSONL")
        record = _decode_json_strict(
            line, f"{path}: linha {line_number}")
        if not isinstance(record, dict):
            raise RecountError(
                f"{path}: linha {line_number} nao contem objeto JSON")
        records.append(record)
    if not records:
        raise RecountError(f"{path}: arquivo JSONL vazio")
    return records


def load_document(path):
    try:
        before = path.read_bytes()
    except OSError as exc:
        raise RecountError(f"{path}: nao foi possivel ler: {exc}") from exc
    try:
        text = before.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RecountError(f"{path}: arquivo nao e UTF-8 valido") from exc

    if path.name.endswith(".jsonl"):
        kind = "jsonl"
        records = _decode_jsonl(path, text)
    else:
        record = _decode_json_strict(text, str(path))
        if not isinstance(record, dict):
            raise RecountError(f"{path}: JSON raiz deve ser um objeto")
        kind = "json"
        records = [record]
    return {
        "path": path,
        "before": before,
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "kind": kind,
        "records": records,
    }


def recount_document(document):
    mismatches = []
    skipped = 0
    for line_number, page in enumerate(document["records"], start=1):
        if page.get("skipped") is True:
            skipped += 1
            continue
        try:
            calculated = body_word_count(page)
        except (AttributeError, TypeError) as exc:
            raise RecountError(
                f"{document['path']}: estrutura invalida na linha "
                f"{line_number}: {exc}") from exc
        declared = page.get("word_count")
        coherent_integer = (
            isinstance(declared, int) and
            not isinstance(declared, bool) and
            declared == calculated
        )
        if coherent_integer:
            continue
        mismatches.append({
            "line": line_number,
            "intent_id": page.get("intent_id", ""),
            "declared": declared,
            "calculated": calculated,
        })
        page["word_count"] = calculated
    return mismatches, skipped


def serialize_document(document):
    if document["kind"] == "json":
        return (json.dumps(
            document["records"][0], ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return "".join(
        json.dumps(record, ensure_ascii=False) + "\n"
        for record in document["records"]
    ).encode("utf-8")


def atomic_replace_if_unchanged(document, payload):
    """Promove por RENAME_EXCHANGE e rejeita qualquer snapshot deslocado.

    Uma sequencia ``read -> os.replace`` nunca e CAS: escritor nao cooperativo
    pode alterar o alvo entre a ultima leitura e a troca. A primitiva comum da
    fila v2 troca as entradas primeiro, autentica o inode deslocado e restaura
    a evolucao concorrente quando os bytes/inode/modo deixaram de corresponder.
    """

    try:
        safe_cas.atomic_replace_cas(
            document["path"], payload, document["before_sha256"])
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise RecountError(
            f"{document['path']}: CAS seguro recusou a troca: {exc}") from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true",
        help="somente verifica (padrao); exit 1 quando houver divergencia")
    mode.add_argument(
        "--write", action="store_true",
        help="corrige word_count com troca atomica por arquivo")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        documents = [load_document(path) for path in args.files]
        plans = []
        total_mismatches = 0
        for document in documents:
            mismatches, skipped = recount_document(document)
            total_mismatches += len(mismatches)
            plans.append((document, mismatches, skipped))

        results = []
        for document, mismatches, skipped in plans:
            changed = False
            if args.write and mismatches:
                atomic_replace_if_unchanged(
                    document, serialize_document(document))
                changed = True
            results.append({
                "path": str(document["path"]),
                "input_sha256": document["before_sha256"],
                "pages": len(document["records"]),
                "skipped": skipped,
                "mismatches": len(mismatches),
                "changed": changed,
                "details": mismatches,
            })
    except RecountError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2

    ok = args.write or total_mismatches == 0
    print(json.dumps({
        "ok": ok,
        "mode": "write" if args.write else "check",
        "mismatches": total_mismatches,
        "files": results,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
