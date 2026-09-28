#!/usr/bin/env python3
"""Data-driven Python mirror of the Go imobiliario-09 current-law gate."""

import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(
    ROOT, "internal", "v2ingest", "imobiliario09_current_legal_fact_rules.json")


with open(RULES_PATH, encoding="utf-8") as rules_file:
    RULES = json.load(rules_file)


def reasons(page, folded, has_source_url_part, has_stj_source_url_part,
            norm_key):
    intent = (page.get("intent_id") or "").strip()
    rule = RULES.get(intent)
    if not rule:
        return []

    output = []
    missing_source = any(
        not has_source_url_part(page, part)
        for part in rule.get("source_parts", []))
    missing_source = missing_source or any(
        not has_stj_source_url_part(page, part)
        for part in rule.get("stj_parts", []))
    key = rule["key"]
    if missing_source:
        output.append(
            "current_legal_fact_source_missing:imobiliario09_" + key)

    for alternatives in rule.get("outcomes", []):
        if not any(part in folded for part in alternatives):
            output.append(
                "current_legal_fact_outcome_missing:imobiliario09_" + key)
            break

    assertions = [page.get("opening") or ""]
    assertions.extend(
        section.get("text") or "" for section in page.get("sections") or [])
    assertions.extend(
        item.get("a") or "" for item in page.get("faq") or [])
    folded_assertions = [norm_key(value) for value in assertions]
    if any(
            forbidden in assertion
            for forbidden in rule.get("forbidden", [])
            for assertion in folded_assertions):
        output.append(
            "current_legal_fact_stale_assertion:imobiliario09_" + key)
    return output
