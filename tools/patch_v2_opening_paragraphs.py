#!/usr/bin/env python3
"""Edita opening e fontes de páginas v2 com CAS e recontagem.

O arquivo JSONL inteiro é promovido de forma atômica somente quando o SHA-256
informado ainda corresponde aos bytes lidos. Cada ``intent_id`` solicitado
deve existir exatamente uma vez; isso evita editar a página errada em shards
concorrentes ou aceitar silenciosamente uma fila obsoleta.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    from tools.audit_v2_pages import body_word_count
    from tools.recount_v2_page_word_counts import (
        RecountError,
        atomic_replace_if_unchanged,
        load_document,
        serialize_document,
    )
except ModuleNotFoundError:
    from audit_v2_pages import body_word_count
    from recount_v2_page_word_counts import (
        RecountError,
        atomic_replace_if_unchanged,
        load_document,
        serialize_document,
    )


class PatchError(RuntimeError):
    """Entrada ambígua, stale ou estruturalmente insegura."""


SAFE_TEXT_SCALAR_FIELDS = frozenset({"title", "meta_description", "h1"})
SAFE_OPTIONAL_TEXT_SCALAR_FIELDS = frozenset({"source_research_note"})
SAFE_BOOLEAN_SCALAR_FIELDS = frozenset({"needs_source_research"})
SAFE_SCALAR_FIELDS = (SAFE_TEXT_SCALAR_FIELDS |
                      SAFE_OPTIONAL_TEXT_SCALAR_FIELDS |
                      SAFE_BOOLEAN_SCALAR_FIELDS)


def parse_patch_json(raw, value_kind="paragraph"):
    """Decodifica um objeto JSON e rejeita chaves repetidas."""

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PatchError(f"chave repetida no patch: {key}")
            result[key] = value
        return result

    try:
        patches = json.loads(raw, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise PatchError(f"patch JSON inválido: {exc.msg}") from exc
    if not isinstance(patches, dict) or not patches:
        raise PatchError("patch deve ser um objeto JSON não vazio")
    normalized_intents = set()
    for intent_id, value in patches.items():
        if not isinstance(intent_id, str) or not intent_id.strip():
            raise PatchError("todo intent_id do patch deve ser texto não vazio")
        normalized_intent = intent_id.strip()
        if normalized_intent in normalized_intents:
            raise PatchError(
                f"intent_id repetido após normalização: {normalized_intent}")
        normalized_intents.add(normalized_intent)
        if value_kind == "source":
            if not isinstance(value, dict):
                raise PatchError(
                    f"fonte de {intent_id!r} deve ser um objeto")
            if set(value) != {"url", "clause"}:
                raise PatchError(
                    f"fonte de {intent_id!r} exige apenas url e clause")
            if not all(isinstance(value[key], str) and value[key].strip()
                       for key in ("url", "clause")):
                raise PatchError(
                    f"url e clause de {intent_id!r} devem ser textos não vazios")
            continue
        if value_kind == "opening_rewrite":
            if not isinstance(value, dict) or set(value) != {
                    "expected_sha256", "replacement"}:
                raise PatchError(
                    f"rewrite de {intent_id!r} exige expected_sha256 e replacement")
            if not re.fullmatch(r"[0-9a-f]{64}", value["expected_sha256"] or ""):
                raise PatchError(
                    f"expected_sha256 do opening de {intent_id!r} é inválido")
            if not isinstance(value["replacement"], str) or not value["replacement"].strip():
                raise PatchError(
                    f"replacement do opening de {intent_id!r} deve ser texto não vazio")
            continue
        if value_kind == "source_rewrite":
            if not isinstance(value, dict) or set(value) != {
                    "url", "expected_sha256", "replacement"}:
                raise PatchError(
                    f"rewrite de fonte de {intent_id!r} exige url, expected_sha256 e replacement")
            if not isinstance(value["url"], str) or not value["url"].strip():
                raise PatchError(f"url de fonte de {intent_id!r} é inválida")
            if not re.fullmatch(r"[0-9a-f]{64}", value["expected_sha256"] or ""):
                raise PatchError(
                    f"expected_sha256 do anchor de {intent_id!r} é inválido")
            if not isinstance(value["replacement"], str) or not value["replacement"].strip():
                raise PatchError(
                    f"replacement do anchor de {intent_id!r} deve ser texto não vazio")
            continue
        if value_kind == "source_identity_rewrite":
            if not isinstance(value, dict) or set(value) != {
                    "url", "expected_sha256", "replacement"}:
                raise PatchError(
                    f"substituição de fonte de {intent_id!r} exige url, expected_sha256 e replacement")
            if not isinstance(value["url"], str) or not value["url"].strip():
                raise PatchError(f"url atual de fonte de {intent_id!r} é inválida")
            if not re.fullmatch(r"[0-9a-f]{64}", value["expected_sha256"] or ""):
                raise PatchError(
                    f"expected_sha256 da fonte de {intent_id!r} é inválido")
            replacement = value["replacement"]
            if not isinstance(replacement, dict) or set(replacement) != {
                    "url", "name", "anchor_claim"}:
                raise PatchError(
                    f"replacement de fonte de {intent_id!r} exige url, name e anchor_claim")
            if not all(isinstance(replacement[key], str) and
                       replacement[key].strip()
                       for key in ("url", "name", "anchor_claim")):
                raise PatchError(
                    f"campos do replacement de fonte de {intent_id!r} devem ser textos não vazios")
            if value["url"].strip() == replacement["url"].strip():
                raise PatchError(
                    f"substituição integral de fonte de {intent_id!r} exige mudança de URL")
            continue
        if value_kind == "source_addition":
            if not isinstance(value, dict) or set(value) != {
                    "url", "name", "anchor_claim"}:
                raise PatchError(
                    f"nova fonte de {intent_id!r} exige url, name e anchor_claim")
            if not all(isinstance(value[key], str) and value[key].strip()
                       for key in ("url", "name", "anchor_claim")):
                raise PatchError(
                    f"campos da nova fonte de {intent_id!r} devem ser textos não vazios")
            continue
        if value_kind == "source_hints_rewrite":
            if not isinstance(value, dict) or set(value) != {
                    "expected_sha256", "replacement"}:
                raise PatchError(
                    f"rewrite de source_hints de {intent_id!r} exige expected_sha256 e replacement")
            if not re.fullmatch(r"[0-9a-f]{64}", value["expected_sha256"] or ""):
                raise PatchError(
                    f"expected_sha256 de source_hints de {intent_id!r} é inválido")
            replacement = value["replacement"]
            if (not isinstance(replacement, list) or not replacement or
                    not all(isinstance(item, str) and item.strip()
                            for item in replacement)):
                raise PatchError(
                    f"replacement de source_hints de {intent_id!r} deve ser lista textual não vazia")
            normalized = [item.strip() for item in replacement]
            if len(normalized) != len(set(normalized)):
                raise PatchError(
                    f"replacement de source_hints de {intent_id!r} contém duplicata")
            continue
        if value_kind == "section_rewrite":
            required = {"heading", "expected_sha256", "replacement"}
            allowed = required | {"replacement_heading"}
            if (not isinstance(value, dict) or
                    not required.issubset(value) or not set(value) <= allowed):
                raise PatchError(
                    f"rewrite de seção de {intent_id!r} exige heading, expected_sha256 e replacement; replacement_heading é opcional")
            if not isinstance(value["heading"], str) or not value["heading"].strip():
                raise PatchError(f"heading de {intent_id!r} é inválido")
            if not re.fullmatch(r"[0-9a-f]{64}", value["expected_sha256"] or ""):
                raise PatchError(
                    f"expected_sha256 da seção de {intent_id!r} é inválido")
            if not isinstance(value["replacement"], str) or not value["replacement"].strip():
                raise PatchError(
                    f"replacement da seção de {intent_id!r} deve ser texto não vazio")
            if ("replacement_heading" in value and
                    (not isinstance(value["replacement_heading"], str) or
                     not value["replacement_heading"].strip())):
                raise PatchError(
                    f"replacement_heading da seção de {intent_id!r} deve ser texto não vazio")
            if ("replacement_heading" in value and
                    ("\n" in value["replacement_heading"] or
                     "\r" in value["replacement_heading"])):
                raise PatchError(
                    f"replacement_heading da seção de {intent_id!r} não pode ser multilinha")
            continue
        if value_kind == "faq_rewrite":
            if not isinstance(value, dict) or set(value) != {
                    "question", "expected_sha256", "replacement"}:
                raise PatchError(
                    f"rewrite de FAQ de {intent_id!r} exige question, expected_sha256 e replacement")
            if (not isinstance(value["question"], str) or
                    not value["question"].strip() or
                    "\n" in value["question"] or "\r" in value["question"]):
                raise PatchError(
                    f"question de FAQ de {intent_id!r} deve ser texto não vazio e não multilinha")
            if not re.fullmatch(r"[0-9a-f]{64}", value["expected_sha256"] or ""):
                raise PatchError(
                    f"expected_sha256 da FAQ de {intent_id!r} é inválido")
            if not isinstance(value["replacement"], str) or not value["replacement"].strip():
                raise PatchError(
                    f"replacement da FAQ de {intent_id!r} deve ser texto não vazio")
            continue
        if value_kind == "scalar_rewrite":
            if not isinstance(value, list) or not value:
                raise PatchError(
                    f"rewrite escalar de {intent_id!r} deve ser uma lista não vazia")
            seen_fields = set()
            for item in value:
                if not isinstance(item, dict) or set(item) != {
                        "field", "expected_sha256", "replacement"}:
                    raise PatchError(
                        f"cada rewrite escalar de {intent_id!r} exige field, expected_sha256 e replacement")
                field = item.get("field")
                if field not in SAFE_SCALAR_FIELDS:
                    raise PatchError(
                        f"campo escalar protegido ou desconhecido em {intent_id!r}: {field!r}")
                if field in seen_fields:
                    raise PatchError(
                        f"campo escalar repetido em {intent_id!r}: {field}")
                seen_fields.add(field)
                if not re.fullmatch(
                        r"[0-9a-f]{64}", item.get("expected_sha256") or ""):
                    raise PatchError(
                        f"expected_sha256 de {field} em {intent_id!r} é inválido")
                replacement = item.get("replacement")
                if field in SAFE_TEXT_SCALAR_FIELDS:
                    if not isinstance(replacement, str) or not replacement.strip():
                        raise PatchError(
                            f"replacement de {field} em {intent_id!r} deve ser texto não vazio")
                    if "\n" in replacement or "\r" in replacement:
                        raise PatchError(
                            f"replacement de {field} em {intent_id!r} não pode ser multilinha")
                elif field in SAFE_OPTIONAL_TEXT_SCALAR_FIELDS:
                    if (replacement is not None and
                            (not isinstance(replacement, str) or
                             not replacement.strip())):
                        raise PatchError(
                            f"replacement de {field} em {intent_id!r} deve ser texto não vazio ou null")
                    if (isinstance(replacement, str) and
                            ("\n" in replacement or "\r" in replacement)):
                        raise PatchError(
                            f"replacement de {field} em {intent_id!r} não pode ser multilinha")
                elif type(replacement) is not bool:
                    raise PatchError(
                        f"replacement de {field} em {intent_id!r} deve ser booleano")
            continue
        if not isinstance(value, str) or not value.strip():
            raise PatchError(
                f"parágrafo de {intent_id!r} deve ser texto não vazio")
        if "\n\n" in value.strip():
            raise PatchError(
                f"parágrafo de {intent_id!r} contém quebra dupla")
    if value_kind == "source":
        return {
            key.strip(): {
                "url": value["url"].strip(),
                "clause": value["clause"].strip(),
            }
            for key, value in patches.items()
        }
    if value_kind == "source_identity_rewrite":
        return {
            key.strip(): {
                "url": value["url"].strip(),
                "expected_sha256": value["expected_sha256"].strip(),
                "replacement": {
                    field: value["replacement"][field].strip()
                    for field in ("url", "name", "anchor_claim")
                },
            }
            for key, value in patches.items()
        }
    if value_kind in {"opening_rewrite", "source_rewrite", "source_addition",
                      "section_rewrite", "faq_rewrite"}:
        return {
            key.strip(): {
                field: item.strip() for field, item in value.items()
            }
            for key, value in patches.items()
        }
    if value_kind == "scalar_rewrite":
        return {
            key.strip(): [{
                "field": item["field"].strip(),
                "expected_sha256": item["expected_sha256"].strip(),
                "replacement": (
                    item["replacement"].strip()
                    if isinstance(item["replacement"], str)
                    else item["replacement"]),
            } for item in value]
            for key, value in patches.items()
        }
    if value_kind == "source_hints_rewrite":
        return {
            key.strip(): {
                "expected_sha256": value["expected_sha256"].strip(),
                "replacement": [item.strip() for item in value["replacement"]],
            }
            for key, value in patches.items()
        }
    return {key.strip(): value.strip() for key, value in patches.items()}


def pages_by_intent(document):
    if document["kind"] != "jsonl":
        raise PatchError("o editor aceita somente shards JSONL")
    result = {}
    for line_number, page in enumerate(document["records"], start=1):
        intent_id = page.get("intent_id")
        if not isinstance(intent_id, str) or not intent_id.strip():
            raise PatchError(
                f"linha {line_number} sem intent_id textual não vazio")
        if intent_id in result:
            raise PatchError(f"intent_id duplicado no shard: {intent_id}")
        result[intent_id] = (line_number, page)
    return result


def require_patch_intents(pages, patches):
    missing = sorted(set(patches) - set(pages))
    if missing:
        raise PatchError("intent_id ausente no shard: " + ", ".join(missing))


def apply_opening_paragraphs(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)

    changed = []
    already_present = []
    for intent_id, paragraph in patches.items():
        line_number, page = pages[intent_id]
        opening = page.get("opening")
        if not isinstance(opening, str) or not opening.strip():
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem opening textual")
        opening_paragraphs = {
            item.strip() for item in opening.split("\n\n") if item.strip()}
        if paragraph == opening.strip() or paragraph in opening_paragraphs:
            already_present.append(intent_id)
            continue
        page["opening"] = opening.rstrip() + "\n\n" + paragraph
        page["word_count"] = body_word_count(page)
        changed.append(intent_id)
    return changed, already_present


def apply_opening_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        opening = page.get("opening")
        if not isinstance(opening, str) or not opening.strip():
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem opening textual")
        replacement = patch["replacement"]
        if opening == replacement:
            already_present.append(intent_id)
            continue
        current_sha256 = hashlib.sha256(opening.encode("utf-8")).hexdigest()
        if current_sha256 != patch["expected_sha256"]:
            raise PatchError(
                f"{intent_id}: opening stale expected={patch['expected_sha256']} "
                f"actual={current_sha256}")
        page["opening"] = replacement
        page["word_count"] = body_word_count(page)
        changed.append(intent_id)
    return changed, already_present


def apply_source_anchor_clauses(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)

    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        sources = page.get("official_sources")
        if not isinstance(sources, list):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem official_sources")
        matches = [source for source in sources
                   if isinstance(source, dict) and
                   source.get("url") == patch["url"]]
        if len(matches) != 1:
            raise PatchError(
                f"{intent_id}: fonte {patch['url']} ocorre {len(matches)} vez(es)")
        source = matches[0]
        anchor = source.get("anchor_claim")
        if not isinstance(anchor, str) or not anchor.strip():
            raise PatchError(f"{intent_id}: fonte sem anchor_claim textual")
        clause = patch["clause"]
        anchor_clauses = {
            item.strip() for item in anchor.split(";") if item.strip()}
        if clause == anchor.strip() or clause in anchor_clauses:
            already_present.append(intent_id)
            continue
        source["anchor_claim"] = anchor.rstrip().rstrip(";") + "; " + clause
        changed.append(intent_id)
    return changed, already_present


def apply_source_anchor_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        sources = page.get("official_sources")
        if not isinstance(sources, list):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem official_sources")
        matches = [source for source in sources
                   if isinstance(source, dict) and source.get("url") == patch["url"]]
        if len(matches) != 1:
            raise PatchError(
                f"{intent_id}: fonte {patch['url']} ocorre {len(matches)} vez(es)")
        source = matches[0]
        anchor = source.get("anchor_claim")
        if not isinstance(anchor, str) or not anchor.strip():
            raise PatchError(f"{intent_id}: fonte sem anchor_claim textual")
        replacement = patch["replacement"]
        if anchor == replacement:
            already_present.append(intent_id)
            continue
        current_sha256 = hashlib.sha256(anchor.encode("utf-8")).hexdigest()
        if current_sha256 != patch["expected_sha256"]:
            raise PatchError(
                f"{intent_id}: anchor stale expected={patch['expected_sha256']} "
                f"actual={current_sha256}")
        source["anchor_claim"] = replacement
        changed.append(intent_id)
    return changed, already_present


def apply_source_additions(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        sources = page.get("official_sources")
        if not isinstance(sources, list):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem official_sources")
        matches = [source for source in sources
                   if isinstance(source, dict) and source.get("url") == patch["url"]]
        if matches:
            if len(matches) == 1 and all(
                    matches[0].get(key) == value for key, value in patch.items()):
                already_present.append(intent_id)
                continue
            raise PatchError(
                f"{intent_id}: nova fonte colide com URL existente {patch['url']}")
        sources.append(dict(patch))
        changed.append(intent_id)
    return changed, already_present


def source_identity_sha256(source):
    payload = json.dumps(
        source, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def apply_source_identity_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        sources = page.get("official_sources")
        if not isinstance(sources, list):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem official_sources")
        current_indexes = [
            index for index, source in enumerate(sources)
            if isinstance(source, dict) and source.get("url") == patch["url"]]
        replacement = patch["replacement"]
        replacement_indexes = [
            index for index, source in enumerate(sources)
            if isinstance(source, dict) and
            source.get("url") == replacement["url"]]
        if not current_indexes:
            if (len(replacement_indexes) == 1 and all(
                    sources[replacement_indexes[0]].get(field) == value
                    for field, value in replacement.items())):
                # Proveniência atual da identidade nova pode ter sido
                # repovoada depois do primeiro rewrite; ela não torna o CAS
                # aplicado obsoleto nem deve ser removida num rerun.
                already_present.append(intent_id)
                continue
            raise PatchError(
                f"{intent_id}: fonte atual {patch['url']} ocorre 0 vez(es) e replacement não é idempotente")
        if len(current_indexes) != 1:
            raise PatchError(
                f"{intent_id}: fonte atual {patch['url']} ocorre {len(current_indexes)} vez(es)")
        current_index = current_indexes[0]
        if replacement["url"] == patch["url"]:
            raise PatchError(
                f"{intent_id}: substituição integral exige mudança de URL")
        if (replacement["url"] != patch["url"] and
                replacement_indexes):
            raise PatchError(
                f"{intent_id}: replacement colide com URL existente {replacement['url']}")
        current = sources[current_index]
        current_sha256 = source_identity_sha256(current)
        if current_sha256 != patch["expected_sha256"]:
            raise PatchError(
                f"{intent_id}: fonte stale expected={patch['expected_sha256']} "
                f"actual={current_sha256}")
        # A URL nova invalida qualquer verified_at/http_status da identidade
        # anterior. A proveniência viva deve repovoar esses campos depois.
        sources[current_index] = dict(replacement)
        changed.append(intent_id)
    return changed, already_present


def source_hints_sha256(values):
    payload = json.dumps(
        values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def apply_source_hint_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        source_hints = page.get("source_hints")
        if (not isinstance(source_hints, list) or
                not all(isinstance(item, str) for item in source_hints)):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem source_hints textual")
        replacement = patch["replacement"]
        if source_hints == replacement:
            already_present.append(intent_id)
            continue
        current_sha256 = source_hints_sha256(source_hints)
        if current_sha256 != patch["expected_sha256"]:
            raise PatchError(
                f"{intent_id}: source_hints stale expected={patch['expected_sha256']} "
                f"actual={current_sha256}")
        page["source_hints"] = replacement
        changed.append(intent_id)
    return changed, already_present


def apply_section_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        sections = page.get("sections")
        if not isinstance(sections, list):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem sections")
        heading = patch["heading"]
        replacement_heading = patch.get("replacement_heading", heading)
        if (not isinstance(heading, str) or not heading.strip() or
                "\n" in heading or "\r" in heading):
            raise PatchError(
                f"{intent_id}: heading deve ser texto não vazio e não multilinha")
        if (not isinstance(replacement_heading, str) or
                not replacement_heading.strip() or
                "\n" in replacement_heading or "\r" in replacement_heading):
            raise PatchError(
                f"{intent_id}: replacement_heading deve ser texto não vazio e não multilinha")
        matches = [section for section in sections
                   if isinstance(section, dict) and
                   section.get("heading") == heading]
        if not matches and replacement_heading != heading:
            replacement_matches = [
                section for section in sections
                if isinstance(section, dict) and
                section.get("heading") == replacement_heading]
            if len(replacement_matches) == 1:
                section = replacement_matches[0]
                if (isinstance(section.get("text"), str) and
                        section["text"] == patch["replacement"]):
                    already_present.append(intent_id)
                    continue
        if len(matches) != 1:
            raise PatchError(
                f"{intent_id}: seção {heading!r} ocorre {len(matches)} vez(es)")
        section = matches[0]
        if replacement_heading != heading and any(
                isinstance(other, dict) and
                other is not section and
                other.get("heading") == replacement_heading
                for other in sections):
            raise PatchError(
                f"{intent_id}: replacement_heading {replacement_heading!r} já existe")
        if not isinstance(section.get("text"), str):
            raise PatchError(
                f"{intent_id}: seção {heading!r} exige text textual canônico")
        current = section["text"]
        replacement = patch["replacement"]
        if current == replacement and heading == replacement_heading:
            already_present.append(intent_id)
            continue
        if current != replacement:
            current_sha256 = hashlib.sha256(current.encode("utf-8")).hexdigest()
            if current_sha256 != patch["expected_sha256"]:
                raise PatchError(
                    f"{intent_id}: section stale expected={patch['expected_sha256']} "
                    f"actual={current_sha256}")
        section["text"] = replacement
        section["heading"] = replacement_heading
        page["word_count"] = body_word_count(page)
        changed.append(intent_id)
    return changed, already_present


def apply_faq_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, patch in patches.items():
        line_number, page = pages[intent_id]
        faq = page.get("faq")
        if not isinstance(faq, list):
            raise PatchError(
                f"linha {line_number} ({intent_id}) sem faq")
        question = patch["question"]
        matches = [item for item in faq
                   if isinstance(item, dict) and item.get("q") == question]
        if len(matches) != 1:
            raise PatchError(
                f"{intent_id}: pergunta de FAQ {question!r} ocorre {len(matches)} vez(es)")
        item = matches[0]
        answer = item.get("a")
        if not isinstance(answer, str) or not answer.strip():
            raise PatchError(
                f"{intent_id}: resposta da FAQ {question!r} deve ser texto não vazio")
        replacement = patch["replacement"]
        if answer == replacement:
            already_present.append(intent_id)
            continue
        current_sha256 = hashlib.sha256(answer.encode("utf-8")).hexdigest()
        if current_sha256 != patch["expected_sha256"]:
            raise PatchError(
                f"{intent_id}: FAQ stale expected={patch['expected_sha256']} "
                f"actual={current_sha256}")
        item["a"] = replacement
        page["word_count"] = body_word_count(page)
        changed.append(intent_id)
    return changed, already_present


def apply_scalar_rewrites(document, patches):
    pages = pages_by_intent(document)
    require_patch_intents(pages, patches)
    changed = []
    already_present = []
    for intent_id, field_patches in patches.items():
        line_number, page = pages[intent_id]
        intent_changed = False
        if not isinstance(field_patches, list) or not field_patches:
            raise PatchError(
                f"rewrite escalar de {intent_id!r} deve ser uma lista não vazia")
        for item in field_patches:
            if not isinstance(item, dict) or set(item) != {
                    "field", "expected_sha256", "replacement"}:
                raise PatchError(
                    f"cada rewrite escalar de {intent_id!r} exige field, expected_sha256 e replacement")
            if not isinstance(item["field"], str):
                raise PatchError(
                    f"field de rewrite escalar de {intent_id!r} deve ser texto")
            expected_sha256 = item["expected_sha256"]
            if (not isinstance(expected_sha256, str) or
                    not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)):
                raise PatchError(
                    f"expected_sha256 de {item['field']} em {intent_id!r} é inválido")
        by_field = {patch["field"]: patch for patch in field_patches}
        if len(by_field) != len(field_patches):
            raise PatchError(f"campo escalar repetido em {intent_id!r}")
        unknown_fields = set(by_field) - SAFE_SCALAR_FIELDS
        if unknown_fields:
            field = sorted(unknown_fields)[0]
            raise PatchError(
                f"campo escalar protegido ou desconhecido em {intent_id!r}: {field!r}")
        for field in ("title", "meta_description", "h1",
                      "needs_source_research", "source_research_note"):
            patch = by_field.get(field)
            if patch is None:
                continue
            replacement = patch.get("replacement")
            current = page.get(field)
            if field in SAFE_TEXT_SCALAR_FIELDS:
                if (not isinstance(replacement, str) or not replacement.strip() or
                        "\n" in replacement or "\r" in replacement):
                    raise PatchError(
                        f"replacement de {field} em {intent_id!r} deve ser texto não vazio e não multilinha")
                if not isinstance(current, str) or not current.strip():
                    raise PatchError(
                        f"linha {line_number} ({intent_id}) sem {field} textual")
                current_payload = current.encode("utf-8")
            elif field in SAFE_OPTIONAL_TEXT_SCALAR_FIELDS:
                if (replacement is not None and
                        (not isinstance(replacement, str) or
                         not replacement.strip() or
                         "\n" in replacement or "\r" in replacement)):
                    raise PatchError(
                        f"replacement de {field} em {intent_id!r} deve ser texto não vazio, não multilinha ou null")
                if replacement is None and field not in page:
                    continue
                if not isinstance(current, str) or not current.strip():
                    raise PatchError(
                        f"linha {line_number} ({intent_id}) sem {field} textual para remoção")
                current_payload = current.encode("utf-8")
            else:
                if type(replacement) is not bool:
                    raise PatchError(
                        f"replacement de {field} em {intent_id!r} deve ser booleano")
                if type(current) is not bool:
                    raise PatchError(
                        f"linha {line_number} ({intent_id}) sem {field} booleano")
                current_payload = json.dumps(current).encode("ascii")
            if current == replacement:
                continue
            current_sha256 = hashlib.sha256(current_payload).hexdigest()
            if current_sha256 != patch["expected_sha256"]:
                raise PatchError(
                    f"{intent_id}: {field} stale expected={patch['expected_sha256']} "
                    f"actual={current_sha256}")
            if field in SAFE_OPTIONAL_TEXT_SCALAR_FIELDS and replacement is None:
                del page[field]
            else:
                page[field] = replacement
            intent_changed = True
        if intent_changed:
            changed.append(intent_id)
        else:
            already_present.append(intent_id)
    return changed, already_present


def patch_file(path, expected_sha256, opening_patches=None, source_patches=None,
               opening_rewrites=None, source_rewrites=None,
               source_additions=None, source_hint_rewrites=None,
               section_rewrites=None, scalar_rewrites=None,
               source_identity_rewrites=None, faq_rewrites=None):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256 or ""):
        raise PatchError("expected SHA-256 deve ter 64 caracteres hexadecimais")
    document = load_document(path)
    if document["before_sha256"] != expected_sha256:
        raise PatchError(
            "snapshot stale: expected=" + expected_sha256 +
            " actual=" + document["before_sha256"])

    opening_patches = opening_patches or {}
    source_patches = source_patches or {}
    opening_rewrites = opening_rewrites or {}
    source_rewrites = source_rewrites or {}
    source_additions = source_additions or {}
    source_hint_rewrites = source_hint_rewrites or {}
    section_rewrites = section_rewrites or {}
    scalar_rewrites = scalar_rewrites or {}
    source_identity_rewrites = source_identity_rewrites or {}
    faq_rewrites = faq_rewrites or {}
    if set(opening_patches) & set(opening_rewrites):
        raise PatchError("um intent não pode acrescentar e reescrever opening na mesma operação")
    for label, other_patches in (
            ("source_patches", source_patches),
            ("source_rewrites", source_rewrites),
            ("source_additions", source_additions)):
        overlap = set(source_identity_rewrites) & set(other_patches)
        if overlap:
            raise PatchError(
                "substituição integral de fonte conflita com " + label +
                " nos intents: " + ", ".join(sorted(overlap)))
    if not any((opening_patches, source_patches, opening_rewrites,
                source_rewrites, source_additions, source_hint_rewrites,
                section_rewrites, scalar_rewrites,
                source_identity_rewrites, faq_rewrites)):
        raise PatchError("informe ao menos um patch de opening ou fonte")
    changed, already_present = apply_opening_paragraphs(
        document, opening_patches) if opening_patches else ([], [])
    source_changed, source_already_present = apply_source_anchor_clauses(
        document, source_patches) if source_patches else ([], [])
    rewritten, rewrite_already_present = apply_opening_rewrites(
        document, opening_rewrites) if opening_rewrites else ([], [])
    source_rewritten, source_rewrite_already_present = apply_source_anchor_rewrites(
        document, source_rewrites) if source_rewrites else ([], [])
    sources_added, sources_already_present = apply_source_additions(
        document, source_additions) if source_additions else ([], [])
    source_identities_rewritten, source_identities_already_present = (
        apply_source_identity_rewrites(document, source_identity_rewrites)
        if source_identity_rewrites else ([], []))
    hints_rewritten, hints_already_present = apply_source_hint_rewrites(
        document, source_hint_rewrites) if source_hint_rewrites else ([], [])
    sections_rewritten, sections_already_present = apply_section_rewrites(
        document, section_rewrites) if section_rewrites else ([], [])
    scalars_rewritten, scalars_already_present = apply_scalar_rewrites(
        document, scalar_rewrites) if scalar_rewrites else ([], [])
    faqs_rewritten, faqs_already_present = apply_faq_rewrites(
        document, faq_rewrites) if faq_rewrites else ([], [])
    if (changed or source_changed or rewritten or source_rewritten or
            sources_added or hints_rewritten or sections_rewritten or
            scalars_rewritten or source_identities_rewritten or
            faqs_rewritten):
        atomic_replace_if_unchanged(document, serialize_document(document))
    output_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": str(path),
        "input_sha256": document["before_sha256"],
        "output_sha256": output_sha256,
        "changed_intents": changed,
        "already_present_intents": already_present,
        "changed_source_intents": source_changed,
        "already_present_source_intents": source_already_present,
        "rewritten_opening_intents": rewritten,
        "already_rewritten_opening_intents": rewrite_already_present,
        "rewritten_source_intents": source_rewritten,
        "already_rewritten_source_intents": source_rewrite_already_present,
        "added_source_intents": sources_added,
        "already_added_source_intents": sources_already_present,
        "rewritten_source_identity_intents": source_identities_rewritten,
        "already_rewritten_source_identity_intents": source_identities_already_present,
        "rewritten_source_hint_intents": hints_rewritten,
        "already_rewritten_source_hint_intents": hints_already_present,
        "rewritten_section_intents": sections_rewritten,
        "already_rewritten_section_intents": sections_already_present,
        "rewritten_scalar_intents": scalars_rewritten,
        "already_rewritten_scalar_intents": scalars_already_present,
        "rewritten_faq_intents": faqs_rewritten,
        "already_rewritten_faq_intents": faqs_already_present,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument(
        "--patch-json",
        help="objeto JSON {intent_id: parágrafo a acrescentar}")
    parser.add_argument(
        "--source-anchor-json",
        help="objeto JSON {intent_id: {url: URL, clause: trecho}}")
    parser.add_argument(
        "--opening-rewrite-json",
        help="objeto JSON {intent_id: {expected_sha256: SHA, replacement: texto}}")
    parser.add_argument(
        "--source-anchor-rewrite-json",
        help="objeto JSON {intent_id: {url: URL, expected_sha256: SHA, replacement: texto}}")
    parser.add_argument(
        "--source-add-json",
        help="objeto JSON {intent_id: {url: URL, name: nome, anchor_claim: trecho}}")
    parser.add_argument(
        "--source-identity-rewrite-json",
        help="objeto JSON {intent_id: {url, expected_sha256, replacement: {url, name, anchor_claim}}}")
    parser.add_argument(
        "--source-hints-rewrite-json",
        help="objeto JSON {intent_id: {expected_sha256: SHA, replacement: [hints]}}")
    parser.add_argument(
        "--section-rewrite-json",
        help="objeto JSON {intent_id: {heading, expected_sha256, replacement, replacement_heading?}}")
    parser.add_argument(
        "--field-rewrite-json",
        help="objeto JSON {intent_id: [{field, expected_sha256, replacement}]} para title/meta_description/h1/needs_source_research")
    parser.add_argument(
        "--faq-rewrite-json",
        help="objeto JSON {intent_id: {question, expected_sha256, replacement}}")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        opening_patches = (
            parse_patch_json(args.patch_json) if args.patch_json else {})
        source_patches = (
            parse_patch_json(args.source_anchor_json, value_kind="source")
            if args.source_anchor_json else {})
        opening_rewrites = (
            parse_patch_json(args.opening_rewrite_json,
                             value_kind="opening_rewrite")
            if args.opening_rewrite_json else {})
        source_rewrites = (
            parse_patch_json(args.source_anchor_rewrite_json,
                             value_kind="source_rewrite")
            if args.source_anchor_rewrite_json else {})
        source_additions = (
            parse_patch_json(args.source_add_json,
                             value_kind="source_addition")
            if args.source_add_json else {})
        source_identity_rewrites = (
            parse_patch_json(
                args.source_identity_rewrite_json,
                value_kind="source_identity_rewrite")
            if args.source_identity_rewrite_json else {})
        source_hint_rewrites = (
            parse_patch_json(args.source_hints_rewrite_json,
                             value_kind="source_hints_rewrite")
            if args.source_hints_rewrite_json else {})
        section_rewrites = (
            parse_patch_json(args.section_rewrite_json,
                             value_kind="section_rewrite")
            if args.section_rewrite_json else {})
        scalar_rewrites = (
            parse_patch_json(args.field_rewrite_json,
                             value_kind="scalar_rewrite")
            if args.field_rewrite_json else {})
        faq_rewrites = (
            parse_patch_json(args.faq_rewrite_json,
                             value_kind="faq_rewrite")
            if args.faq_rewrite_json else {})
        result = patch_file(
            args.file, args.expected_sha256, opening_patches, source_patches,
            opening_rewrites, source_rewrites, source_additions,
            source_hint_rewrites, section_rewrites, scalar_rewrites,
            source_identity_rewrites, faq_rewrites)
    except (PatchError, RecountError, OSError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
