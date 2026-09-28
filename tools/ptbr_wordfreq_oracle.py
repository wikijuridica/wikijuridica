#!/usr/bin/env python3
import argparse
import json
import re
import statistics
import sys
from importlib.metadata import version

from wordfreq import zipf_frequency


TEXT_FIELDS = (
    "public_title",
    "public_meta_description",
    "public_h1",
    "public_summary",
    "public_legal_notice",
)

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}")
ACCENT_RE = re.compile(r"[À-ÖØ-öø-ÿ]")


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
    token_count = 0
    accent_token_count = 0
    unknown_token_count = 0
    rare_token_count = 0
    record_with_tokens = 0
    record_with_accent = 0
    frequencies = []

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
            seen_token = False
            seen_accent = False
            for value in text_values(record):
                text_fields += 1
                for match in TOKEN_RE.finditer(value):
                    token = match.group(0).lower()
                    score = zipf_frequency(token, "pt")
                    token_count += 1
                    seen_token = True
                    frequencies.append(score)
                    if ACCENT_RE.search(token):
                        accent_token_count += 1
                        seen_accent = True
                    if score <= 0:
                        unknown_token_count += 1
                    elif score < 2.0:
                        rare_token_count += 1
            if seen_token:
                record_with_tokens += 1
            if seen_accent:
                record_with_accent += 1

    median_zipf = 0.0
    p10_zipf = 0.0
    if frequencies:
        median_zipf = float(statistics.median(frequencies))
        p10_zipf = float(sorted(frequencies)[max(0, int(len(frequencies) * 0.10) - 1)])

    return {
        "module_path": "wordfreq",
        "module_version": version("wordfreq"),
        "input_records": input_records,
        "text_fields_scanned": text_fields,
        "token_count": token_count,
        "record_with_tokens": record_with_tokens,
        "record_with_accent": record_with_accent,
        "accent_token_count": accent_token_count,
        "unknown_token_count": unknown_token_count,
        "rare_token_count": rare_token_count,
        "median_zipf_pt": round(median_zipf, 4),
        "p10_zipf_pt": round(p10_zipf, 4),
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    json.dump(scan(args.input), sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
