#!/usr/bin/env python3
import argparse
import json
import sys
from importlib.metadata import version

from ftfy import fix_text


TEXT_FIELDS = (
    "public_title",
    "public_meta_description",
    "public_h1",
    "public_summary",
    "public_legal_notice",
)


def has_ftfy_candidate_signal(value):
    if not value:
        return False
    if "\ufffd" in value or "\u00a0" in value:
        return True
    for marker in ("Ã", "Â", "â€", "â€œ", "â€�", "â€“", "â€”", "&"):
        if marker in value:
            return True
    return False


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


def scan(path):
    input_records = 0
    text_fields = 0
    changed_records = 0
    changed_fields = 0
    candidate_records = 0
    candidate_fields = 0
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
            record_changed = False
            record_candidate = False
            for value in text_values(record):
                text_fields += 1
                if has_ftfy_candidate_signal(value):
                    candidate_fields += 1
                    record_candidate = True
                    fixed = fix_text(value)
                    if fixed != value:
                        changed_fields += 1
                        record_changed = True
            if record_changed:
                changed_records += 1
            if record_candidate:
                candidate_records += 1
    return {
        "module_path": "ftfy",
        "module_version": version("ftfy"),
        "input_records": input_records,
        "text_fields_scanned": text_fields,
        "ftfy_candidate_fields": candidate_fields,
        "ftfy_changed_records": changed_records,
        "ftfy_changed_fields": changed_fields,
        "mojibake_signal_records": candidate_records,
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    json.dump(scan(args.input), sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
