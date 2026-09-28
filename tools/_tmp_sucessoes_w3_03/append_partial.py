#!/usr/bin/env python3
"""Valida um p<NN>.json ja recontado e apenda como linha compacta em partial.jsonl.

Uso: python3 append_partial.py <workdir> <arquivo.json> <intent_id-esperado>
Idempotente por intent_id: se a linha ja existir no partial para o mesmo
intent_id, nao duplica.
"""
import json
import sys
from pathlib import Path


def main():
    workdir = Path(sys.argv[1])
    page_path = Path(sys.argv[2])
    expected_intent = sys.argv[3]
    partial_path = workdir / "partial.jsonl"

    data = json.loads(page_path.read_text(encoding="utf-8"))
    if data.get("intent_id") != expected_intent:
        print(f"ERRO: intent_id {data.get('intent_id')!r} != esperado {expected_intent!r}")
        sys.exit(1)
    declared = data.get("word_count")
    if not isinstance(declared, int) or isinstance(declared, bool) or declared <= 0:
        print(f"ERRO: word_count invalido antes de apendar: {declared!r}")
        sys.exit(1)

    existing_intents = set()
    if partial_path.exists():
        for line in partial_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            existing_intents.add(json.loads(line).get("intent_id"))

    if expected_intent in existing_intents:
        print(f"OK (ja presente, nao duplicado): {expected_intent}")
        return

    line = json.dumps(data, ensure_ascii=False)
    with partial_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"OK apendado: {expected_intent} (word_count={declared})")


if __name__ == "__main__":
    main()
