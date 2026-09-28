#!/usr/bin/env python3
"""Testes do gate/reconciliador de fontes exatas no estoque completo."""

from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import unittest

from tools import reconcile_v2_strict_source_stock as stock


def json_line(value: object) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ) + "\n").encode("utf-8")


class StrictSourceStockTest(unittest.TestCase):
    def fixture(self, *, include_expected_url: bool = True) -> pathlib.Path:
        root = pathlib.Path(tempfile.mkdtemp(prefix="wiki-strict-stock-"))
        self.addCleanup(lambda: shutil.rmtree(root))
        catalog = {
            "_meta": {
                "schema_version": 1,
                "purpose": "teste de estoque",
                "source_policy": "fonte oficial específica",
            },
            "strict_intents": ["seg-intent-exata"],
            "source_hints": {
                "lei-exata": {
                    "name": "Lei exata, art. 1º",
                    "url": "https://www.planalto.gov.br/lei-exata",
                    "anchor_claim": "regra material exata",
                },
            },
        }
        portfolio = {
            "intent_id": "seg-intent-exata",
            "family": "seguro",
            "source_hints": ["lei-exata"],
        }
        actual_url = (catalog["source_hints"]["lei-exata"]["url"]
                      if include_expected_url
                      else "https://www.planalto.gov.br/lei-outra")
        page = {
            "intent_id": "seg-intent-exata",
            "sections": [{"heading": "Regra", "text": "Conteúdo."}],
            "official_sources": [{
                "name": "Nome divergente",
                "url": actual_url,
                "anchor_claim": "claim divergente",
                "verified_at": "2026-07-14",
                "http_status": 200,
            }],
        }
        for rel, payload in (
            (stock.CATALOG_REL, json_line(catalog)),
            (stock.PORTFOLIO_DIR_REL + "/seguros.jsonl", json_line(portfolio)),
            (stock.PAGES_DIR_REL + "/seguros-01.jsonl", json_line(page)),
        ):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        return root

    def test_reconcile_existing_url_preserves_live_metadata(self) -> None:
        root = self.fixture()
        before = stock.check_stock(root)
        self.assertFalse(before["ok"])
        self.assertEqual(
            before["defects"][0]["kind"], "exact_source_identity_mismatch")
        result = stock.reconcile_file(
            root, "data/editorial/v2_pages/seguros-01.jsonl")
        self.assertTrue(result["ok"])
        self.assertEqual(result["changed_intents"], ["seg-intent-exata"])
        page = json.loads((
            root / "data/editorial/v2_pages/seguros-01.jsonl").read_text())
        source = page["official_sources"][0]
        self.assertEqual(source["name"], "Lei exata, art. 1º")
        self.assertEqual(source["anchor_claim"], "regra material exata")
        self.assertEqual(source["verified_at"], "2026-07-14")
        self.assertEqual(source["http_status"], 200)
        receipts = list((root / stock.PAGES_DIR_REL).glob(
            ".seguros-01.jsonl.stale-cas-*"))
        self.assertEqual(len(receipts), 1)

    def test_reconcile_refuses_to_add_unproven_url(self) -> None:
        root = self.fixture(include_expected_url=False)
        with self.assertRaisesRegex(ValueError, "recusa adicionar URL"):
            stock.reconcile_file(
                root, "data/editorial/v2_pages/seguros-01.jsonl")


if __name__ == "__main__":
    unittest.main()
