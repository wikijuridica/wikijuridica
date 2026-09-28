#!/usr/bin/env python3
import argparse
import json
import random
import re
import statistics
import sys
from importlib.metadata import version

from lexicalrichness import LexicalRichness


TEXT_FIELDS = (
    "public_title",
    "public_meta_description",
    "public_h1",
    "public_summary",
    "public_legal_notice",
)

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}")
MATTR_WINDOW_SIZE = 50
HDD_DRAWS = 42
VOCD_NTOKENS = 35
VOCD_WITHIN_SAMPLE = 8
VOCD_ITERATIONS = 1
DEFAULT_SHARD_SIZE = 1000
DEFAULT_MAX_TOKENS_PER_SHARD = 75000


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


def tokenize(text):
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def round4(value):
    return round(float(value), 4)


def p10(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return round4(ordered[max(0, int(len(ordered) * 0.10) - 1)])


def mean(values):
    if not values:
        return 0.0
    return round4(statistics.fmean(values))


def safe_call(callable_metric):
    try:
        value = callable_metric()
    except Exception:
        return 0.0
    if value is None:
        return 0.0
    return round4(value)


def compute_shard_metric(shard):
    tokens = shard["tokens"]
    words = len(tokens)
    metric = {
        "shard_id": shard["shard_id"],
        "input_records": shard["input_records"],
        "records_with_tokens": shard["records_with_tokens"],
        "token_count": shard["token_count"],
        "sampled_token_count": words,
        "mattr": 0.0,
        "mtld": 0.0,
        "hdd": 0.0,
        "vocd": 0.0,
    }
    if words < 2:
        return metric
    lex = LexicalRichness(tokens, preprocessor=None, tokenizer=None)
    mattr_window = max(1, min(MATTR_WINDOW_SIZE, words))
    hdd_draws = max(1, min(HDD_DRAWS, words - 1))
    random.seed(42000 + shard["shard_id"])
    try:
        import numpy

        numpy.random.seed(42000 + shard["shard_id"])
    except Exception:
        pass
    metric["mattr"] = safe_call(lambda: lex.mattr(window_size=mattr_window))
    metric["mtld"] = safe_call(lambda: lex.mtld(threshold=0.72))
    metric["hdd"] = safe_call(lambda: lex.hdd(draws=hdd_draws))
    if words >= VOCD_NTOKENS:
        metric["vocd"] = safe_call(
            lambda: lex.vocd(
                ntokens=VOCD_NTOKENS,
                within_sample=VOCD_WITHIN_SAMPLE,
                iterations=VOCD_ITERATIONS,
            )
        )
    return metric


def scan(path, shard_size, max_tokens_per_shard):
    input_records = 0
    text_fields = 0
    token_count = 0
    records_with_tokens = 0
    short_text_records = 0
    shards = []

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
            shard_id = (input_records - 1) // shard_size
            while len(shards) <= shard_id:
                shards.append(
                    {
                        "shard_id": len(shards),
                        "input_records": 0,
                        "records_with_tokens": 0,
                        "token_count": 0,
                        "tokens": [],
                    }
                )
            shard = shards[shard_id]
            shard["input_records"] += 1
            record_tokens = []
            for value in text_values(record):
                text_fields += 1
                record_tokens.extend(tokenize(value))
            if record_tokens:
                records_with_tokens += 1
                shard["records_with_tokens"] += 1
            if len(record_tokens) < MATTR_WINDOW_SIZE:
                short_text_records += 1
            token_count += len(record_tokens)
            shard["token_count"] += len(record_tokens)
            remaining = max_tokens_per_shard - len(shard["tokens"])
            if remaining > 0:
                shard["tokens"].extend(record_tokens[:remaining])

    shard_metrics = [compute_shard_metric(shard) for shard in shards]
    mattr_values = [metric["mattr"] for metric in shard_metrics if metric["mattr"] > 0]
    mtld_values = [metric["mtld"] for metric in shard_metrics if metric["mtld"] > 0]
    hdd_values = [metric["hdd"] for metric in shard_metrics if metric["hdd"] > 0]
    vocd_values = [metric["vocd"] for metric in shard_metrics if metric["vocd"] > 0]
    low_diversity_shards = sum(
        1
        for metric in shard_metrics
        if metric["mattr"] < 0.32 or metric["mtld"] < 20.0 or metric["hdd"] < 0.45 or metric["vocd"] < 10.0
    )

    return {
        "module_path": "lexicalrichness",
        "module_version": version("lexicalrichness"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "input_records": input_records,
        "shard_size": shard_size,
        "shard_count": len(shard_metrics),
        "max_tokens_per_shard": max_tokens_per_shard,
        "text_fields_scanned": text_fields,
        "token_count": token_count,
        "records_with_tokens": records_with_tokens,
        "short_text_records": short_text_records,
        "mattr_window_size": MATTR_WINDOW_SIZE,
        "hdd_draws": HDD_DRAWS,
        "vocd_ntokens": VOCD_NTOKENS,
        "vocd_within_sample": VOCD_WITHIN_SAMPLE,
        "vocd_iterations": VOCD_ITERATIONS,
        "mean_mattr": mean(mattr_values),
        "p10_mattr": p10(mattr_values),
        "mean_mtld": mean(mtld_values),
        "p10_mtld": p10(mtld_values),
        "mean_hdd": mean(hdd_values),
        "p10_hdd": p10(hdd_values),
        "mean_vocd": mean(vocd_values),
        "p10_vocd": p10(vocd_values),
        "low_diversity_shards": low_diversity_shards,
        "shard_metrics": shard_metrics,
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--shard-size", type=int, default=DEFAULT_SHARD_SIZE)
    parser.add_argument("--max-tokens-per-shard", type=int, default=DEFAULT_MAX_TOKENS_PER_SHARD)
    args = parser.parse_args(argv)
    if args.shard_size <= 0:
        raise SystemExit("--shard-size must be positive")
    if args.max_tokens_per_shard <= 0:
        raise SystemExit("--max-tokens-per-shard must be positive")
    json.dump(
        scan(args.input, args.shard_size, args.max_tokens_per_shard),
        sys.stdout,
        ensure_ascii=False,
        sort_keys=True,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
