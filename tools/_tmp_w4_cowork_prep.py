#!/usr/bin/env python3
"""Helper efêmero da onda W4 (cowork): extrai os argumentos literais do contrato
do lote e executa preflight / promoção sem transcrição manual de blobs base64.

Uso:
  python3 tools/_tmp_w4_cowork_prep.py preflight <slug>
  python3 tools/_tmp_w4_cowork_prep.py promote  <slug> <workdir>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import generate_v2_review_queue as producer  # noqa: E402


def contract_text(slug: str) -> str:
    p = ROOT / ".agents/runtime/staging/prompt_dump_w4" / f"{slug}.prompt.txt"
    return p.read_text(encoding="utf-8")


def parse_contract(slug: str) -> dict:
    txt = contract_text(slug)
    out = {"slug": slug}
    # sha256 constants
    out["semantic_digest"] = re.search(
        r"semantic_contract\.digest == '([0-9a-f]{64})'", txt
    ).group(1)
    out["portfolio_rel"] = re.search(
        r"'(data/editorial/portfolio_v2/[^']+\.jsonl)'", txt
    ).group(1)
    out["portfolio_sha"] = re.search(
        re.escape(out["portfolio_rel"]) + r"', '([0-9a-f]{64})'", txt
    ).group(1)
    out["catalog_rel"] = "data/editorial/v2_source_hint_catalog.json"
    out["catalog_sha"] = re.search(
        re.escape(out["catalog_rel"]) + r"', '([0-9a-f]{64})'", txt
    ).group(1)
    out["target_rel"] = f"data/editorial/v2_pages/{slug}.jsonl"
    out["target_sha"] = re.search(
        re.escape(out["target_rel"]) + r"', '([0-9a-f]{64})'", txt
    ).group(1)
    # families + counts + intents + blob, from the verify_writing_source_resolution call
    m = re.search(
        re.escape(out["catalog_sha"])
        + r"', (\[[^\]]*\]), (\d+), (\d+), (\d+), (\[[^\]]*\]), '([A-Za-z0-9+/=]+)'",
        txt,
    )
    out["families"] = json.loads(m.group(1).replace("'", '"'))
    out["arg_a"] = int(m.group(2))
    out["arg_b"] = int(m.group(3))
    out["expect_n"] = int(m.group(4))
    out["intents"] = json.loads(m.group(5).replace("'", '"'))
    out["resolution_blob"] = m.group(6)
    # second blob (reuse/preserve_extras) — appears right after the resolution blob in promote
    blobs = re.findall(r"'([A-Za-z0-9+/]{120,}={0,2})'", txt)
    tail = [b for b in blobs if b != out["resolution_blob"]]
    out["promote_blob"] = tail[-1] if tail else None
    out["source_map"] = json.loads(
        re.search(r"MAPA EXATO DE FONTES POR INTENCAO: (\{.*?\})\. Para cada intent_id", txt, re.S).group(1)
    )
    return out


def preflight(slug: str) -> None:
    c = parse_contract(slug)
    sc = producer.load_writing_semantic_contract(ROOT)
    assert sc.digest == c["semantic_digest"], f"semantic contract stale: {sc.digest}"
    producer.verify_writing_semantic_contract_dependencies(ROOT, sc)
    producer.verify_writing_source_resolution(
        ROOT,
        c["portfolio_rel"],
        c["portfolio_sha"],
        c["catalog_rel"],
        c["catalog_sha"],
        c["families"],
        c["arg_a"],
        c["arg_b"],
        c["expect_n"],
        c["intents"],
        c["resolution_blob"],
    )
    p = ROOT / c["target_rel"]
    actual = producer.snapshot_sha256(p, max_bytes=64 * 1024 * 1024)
    assert actual == c["target_sha"], f"snapshot stale: expected={c['target_sha']} actual={actual}"
    assert (
        producer.snapshot_sha256(ROOT / c["portfolio_rel"], max_bytes=64 * 1024 * 1024)
        == c["portfolio_sha"]
    ), "portfolio stale"
    assert (
        producer.snapshot_sha256(ROOT / c["catalog_rel"], max_bytes=8 * 1024 * 1024)
        == c["catalog_sha"]
    ), "source hint catalog stale"
    work = producer.create_workflow_workspace(
        slug, c["target_sha"], str(ROOT / ".agents/runtime/wworkspaces")
    )
    print(json.dumps({"workdir": str(work), "contract": {k: v for k, v in c.items() if k not in ("resolution_blob", "promote_blob", "source_map")}}, ensure_ascii=False))


def promote(slug: str, workdir: str) -> None:
    c = parse_contract(slug)
    target = ROOT / c["target_rel"]
    staged = Path(workdir) / "final.jsonl"
    sc = producer.load_writing_semantic_contract(ROOT)
    assert sc.digest == c["semantic_digest"], "semantic contract stale"
    producer.verify_writing_semantic_contract_dependencies(ROOT, sc)
    staged_snapshot = producer.verify_staged_writing_source_resolution(
        ROOT,
        staged,
        c["target_rel"],
        c["target_sha"],
        c["portfolio_rel"],
        c["portfolio_sha"],
        c["catalog_rel"],
        c["catalog_sha"],
        c["families"],
        c["arg_a"],
        c["arg_b"],
        c["expect_n"],
        c["intents"],
        c["resolution_blob"],
        c["promote_blob"],
    )
    assert (
        producer.snapshot_sha256(ROOT / c["portfolio_rel"], max_bytes=64 * 1024 * 1024)
        == c["portfolio_sha"]
    ), "portfolio stale before promote"
    assert (
        producer.snapshot_sha256(ROOT / c["catalog_rel"], max_bytes=8 * 1024 * 1024)
        == c["catalog_sha"]
    ), "source hint catalog stale before promote"
    dependency_epoch = producer.writing_promotion_dependency_epoch(
        ROOT,
        sc,
        c["portfolio_rel"],
        c["portfolio_sha"],
        c["catalog_rel"],
        c["catalog_sha"],
        raw_recovery_preimage_evidence=None,
    )
    producer.atomic_replace_cas(
        target,
        staged_snapshot.payload,
        c["target_sha"],
        dependency_sha256=dependency_epoch,
    )
    (Path(workdir) / "promoted.sha256").write_text(
        producer.snapshot_sha256(target, max_bytes=64 * 1024 * 1024)
    )
    print("PROMOTED " + (Path(workdir) / "promoted.sha256").read_text())


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "preflight":
        preflight(sys.argv[2])
    elif cmd == "promote":
        promote(sys.argv[2], sys.argv[3])
    elif cmd == "dump":
        c = parse_contract(sys.argv[2])
        print(json.dumps(c, ensure_ascii=False, indent=1))
    else:
        raise SystemExit("uso: preflight|promote|dump")
