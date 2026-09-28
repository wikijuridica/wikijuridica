#!/usr/bin/env python3
import argparse
import json
import sys
from importlib.metadata import version

from confusable_homoglyphs import confusables


TEXT_FIELDS = (
    "public_title",
    "public_meta_description",
    "public_h1",
    "public_summary",
    "public_legal_notice",
)


def text_values(record):
    for field in TEXT_FIELDS:
        value = record.get(field)
        if isinstance(value, str) and value:
            yield value
    for section in record.get("public_body_sections") or ():
        if not isinstance(section, dict):
            continue
        for field in ("heading", "text"):
            value = section.get(field)
            if isinstance(value, str) and value:
                yield value


def has_confusables_candidate_signal(value):
    # PT-BR accents live in Latin blocks; Greek/Cyrillic/math homoglyphs do not.
    return any(ord(ch) > 0x024F for ch in value)


def scan(path):
    input_records = 0
    text_fields = 0
    candidate_records = 0
    candidate_fields = 0
    mixed_script_records = 0
    mixed_script_fields = 0
    dangerous_records = 0
    dangerous_fields = 0
    blocker_records = 0
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid_json line={line_number}: {exc}") from exc
            input_records += 1
            record_candidate = False
            record_mixed = False
            record_dangerous = False
            for value in text_values(record):
                text_fields += 1
                if not has_confusables_candidate_signal(value):
                    continue
                candidate_fields += 1
                record_candidate = True
                mixed = bool(confusables.is_mixed_script(value))
                dangerous = bool(confusables.is_dangerous(value, preferred_aliases=["latin"]))
                if mixed:
                    mixed_script_fields += 1
                    record_mixed = True
                if dangerous:
                    dangerous_fields += 1
                    record_dangerous = True
            if record_candidate:
                candidate_records += 1
            if record_mixed:
                mixed_script_records += 1
            if record_dangerous:
                dangerous_records += 1
            if record_mixed or record_dangerous:
                blocker_records += 1
    return {
        "module_path": "confusable-homoglyphs",
        "module_version": version("confusable-homoglyphs"),
        "input_records": input_records,
        "text_fields_scanned": text_fields,
        "confusable_candidate_records": candidate_records,
        "confusable_candidate_fields": candidate_fields,
        "mixed_script_records": mixed_script_records,
        "mixed_script_fields": mixed_script_fields,
        "dangerous_confusable_records": dangerous_records,
        "dangerous_confusable_fields": dangerous_fields,
        "blocker_records": blocker_records,
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    json.dump(scan(args.input), sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
