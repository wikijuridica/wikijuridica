#!/usr/bin/env python3
import json
import statistics
import sys
from importlib.metadata import version

from rapidfuzz import fuzz


MODULE_PATH = "rapidfuzz"
HIGH_TOKEN_SET_THRESHOLD = 92.0
HIGH_WRATIO_THRESHOLD = 88.0


def round2(value):
    return round(float(value), 2)


def mean(values):
    if not values:
        return 0.0
    return round2(statistics.fmean(values))


def p95(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    return round2(ordered[index])


def score_pair(pair):
    left_text = pair.get("left_text") or ""
    right_text = pair.get("right_text") or ""
    ratio = round2(fuzz.ratio(left_text, right_text))
    partial_ratio = round2(fuzz.partial_ratio(left_text, right_text))
    token_set_ratio = round2(fuzz.token_set_ratio(left_text, right_text))
    wratio = round2(fuzz.WRatio(left_text, right_text))
    return {
        "left_content_id": pair.get("left_content_id", ""),
        "right_content_id": pair.get("right_content_id", ""),
        "rapidfuzz_ratio": ratio,
        "rapidfuzz_partial_ratio": partial_ratio,
        "rapidfuzz_token_set_ratio": token_set_ratio,
        "rapidfuzz_wratio": wratio,
        "simhash_hamming_distance": int(pair.get("simhash_hamming_distance") or 0),
        "minhash_jaccard_score": round(float(pair.get("minhash_jaccard_score") or 0.0), 6),
        "high_similarity": token_set_ratio >= HIGH_TOKEN_SET_THRESHOLD or wratio >= HIGH_WRATIO_THRESHOLD,
    }


def main():
    payload = json.load(sys.stdin)
    pairs = payload.get("pairs") or []
    scored = [score_pair(pair) for pair in pairs]
    scored.sort(
        key=lambda item: (
            -item["rapidfuzz_token_set_ratio"],
            -item["rapidfuzz_wratio"],
            item["simhash_hamming_distance"],
            item["left_content_id"],
            item["right_content_id"],
        )
    )
    token_set_values = [item["rapidfuzz_token_set_ratio"] for item in scored]
    wratio_values = [item["rapidfuzz_wratio"] for item in scored]
    output = {
        "module_path": MODULE_PATH,
        "module_version": version(MODULE_PATH),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "candidate_pair_count": int(payload.get("candidate_pair_count") or len(scored)),
        "rescored_pair_count": len(scored),
        "bounded_pair_limit": int(payload.get("bounded_pair_limit") or len(scored)),
        "selection_policy": payload.get("selection_policy") or "",
        "high_similarity_pair_count": sum(1 for item in scored if item["high_similarity"]),
        "mean_token_set_ratio": mean(token_set_values),
        "p95_token_set_ratio": p95(token_set_values),
        "mean_wratio": mean(wratio_values),
        "p95_wratio": p95(wratio_values),
        "top_pairs": scored[: min(20, len(scored))],
    }
    json.dump(output, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
