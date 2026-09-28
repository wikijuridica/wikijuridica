#!/usr/bin/env python3

import json
import os
import pathlib
import tempfile
import unittest

from tools import check_v2_portfolio_source_hints as check


class PortfolioSourceHintCheckTests(unittest.TestCase):
    def fixture(self, rows, hints=("fonte-exata",),
                source_kind="legal_act", url="https://example.gov.br/norma/1"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        portfolio = root / "data/editorial/portfolio_v2"
        portfolio.mkdir(parents=True)
        registry = root / "data/source-registry"
        registry.mkdir(parents=True)
        (registry / "source_registry_v2.jsonl").write_text(json.dumps({
            "source_id": "example-registry",
            "official_domains": ["example.gov.br"],
            "canonical_base_urls": ["https://example.gov.br/norma/"],
        }) + "\n", encoding="utf-8")
        catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                hint: {"name": hint, "url": url,
                       "anchor_claim": "regra material oficial específica",
                       "source_kind": source_kind} for hint in hints},
        }
        (root / "data/editorial/v2_source_hint_catalog.json").write_text(
            json.dumps(catalog) + "\n", encoding="utf-8")
        (portfolio / "a.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8")
        return root

    @staticmethod
    def row(intent, hint, needs_research):
        return {"intent_id": intent, "source_hints": [hint],
                "needs_source_research": needs_research}

    def test_researched_exact_hint_passes(self):
        report = check.audit(self.fixture([
            self.row("intent-a", "fonte-exata", False)]))
        self.assertTrue(report["passed"])
        self.assertEqual(report["researched_records"], 1)

    def test_all_closed_source_kinds_include_guidance_and_service(self):
        for kind in ("legal_act", "binding_precedent", "judicial_decision",
                     "official_guidance", "official_service"):
            with self.subTest(kind=kind):
                report = check.audit(self.fixture([
                    self.row("intent-a", "fonte-exata", False)],
                    source_kind=kind))
                self.assertTrue(report["passed"])

    def test_catalog_source_kind_is_required_and_closed_enum(self):
        for kind in (None, "news", True):
            with self.subTest(kind=kind):
                root = self.fixture([
                    self.row("intent-a", "fonte-exata", False)])
                path = root / "data/editorial/v2_source_hint_catalog.json"
                catalog = json.loads(path.read_text(encoding="utf-8"))
                if kind is None:
                    del catalog["source_hints"]["fonte-exata"]["source_kind"]
                else:
                    catalog["source_hints"]["fonte-exata"]["source_kind"] = kind
                path.write_text(json.dumps(catalog) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "invalid shape|not resolved"):
                    check.audit(root)

    def test_url_must_be_https_and_match_exact_registry_prefix(self):
        for url in (
                "http://example.gov.br/norma/1",
                "https://example.gov.br/fora/1",
                "https://example.gov.br.evil.invalid/norma/1",
                "https://example.gov.br/norma/1#artigo"):
            with self.subTest(url=url):
                root = self.fixture([
                    self.row("intent-a", "fonte-exata", False)], url=url)
                with self.assertRaisesRegex(ValueError, "not resolved"):
                    check.audit(root)

    def test_catalog_requires_real_source_shape_and_anchor_claim(self):
        root = self.fixture([
            self.row("intent-a", "fonte-exata", False)])
        path = root / "data/editorial/v2_source_hint_catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        catalog["source_hints"]["fonte-exata"]["anchor_claim"] = "  "
        path.write_text(json.dumps(catalog) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not resolved"):
            check.audit(root)

    def test_researched_unknown_or_free_text_hint_fails(self):
        report = check.audit(self.fixture([
            self.row("intent-a", "fonte-desconhecida", False),
            self.row("intent-b", "Lei 1, art. 2", False),
        ]))
        self.assertFalse(report["passed"])
        self.assertEqual(report["researched_with_unresolved_sources"], 2)
        self.assertTrue(all(
            item["next_action"].endswith("needs_source_research=true")
            for item in report["findings"]))

    def test_pending_research_remains_blocked_without_false_resolution(self):
        report = check.audit(self.fixture([
            self.row("intent-a", "Lei 1, art. 2", True)]))
        self.assertTrue(report["passed"])
        self.assertEqual(report["research_pending_records"], 1)
        self.assertEqual(report["research_pending_fully_unresolved_records"], 1)
        self.assertEqual(report["research_pending_mixed_records"], 0)
        self.assertEqual(report["researched_records"], 0)

    def test_pending_census_splits_mixed_and_fully_resolved(self):
        # O intent misto (um hint resolvido + um pendente) continua apenas
        # contado — a fila de escrita já o força a tombstone-only; o censo
        # existe para dimensionar a rota de completar catálogo/alias.
        mixed = {"intent_id": "intent-misto",
                 "source_hints": ["fonte-exata", "Lei 1, art. 2"],
                 "needs_source_research": True}
        stale_flag = self.row("intent-resolvido", "fonte-exata", True)
        report = check.audit(self.fixture([mixed, stale_flag]))
        self.assertTrue(report["passed"])
        self.assertEqual(report["research_pending_records"], 2)
        self.assertEqual(report["research_pending_mixed_records"], 1)
        self.assertEqual(report["research_pending_fully_unresolved_records"], 0)
        self.assertEqual(report["research_pending_fully_resolved_records"], 1)
        self.assertEqual(report["researched_with_unresolved_sources"], 0)

    def test_duplicate_intent_and_noncanonical_jsonl_fail_closed(self):
        root = self.fixture([
            self.row("intent-a", "fonte-exata", False),
            self.row("intent-a", "fonte-exata", False),
        ])
        with self.assertRaisesRegex(ValueError, "invalid portfolio"):
            check.audit(root)
        path = root / "data/editorial/portfolio_v2/a.jsonl"
        path.write_bytes(path.read_bytes().rstrip(b"\n"))
        with self.assertRaisesRegex(ValueError, "not canonical"):
            check.audit(root)

    def test_nonfinite_json_and_symlinked_portfolio_directory_fail_closed(self):
        root = self.fixture([
            self.row("intent-a", "fonte-exata", False)])
        portfolio = root / "data/editorial/portfolio_v2"
        path = portfolio / "a.jsonl"
        path.write_text(
            '{"intent_id":"intent-a","source_hints":["fonte-exata"],'
            '"needs_source_research":false,"score":NaN}\n',
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            check.audit(root)

        path.unlink()
        portfolio.rmdir()
        outside = root / "outside-portfolio"
        outside.mkdir()
        (outside / "a.jsonl").write_text(
            json.dumps(self.row("outside", "fonte-exata", False)) + "\n",
            encoding="utf-8")
        portfolio.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinked"):
            check.audit(root)

    def test_symlink_and_fifo_are_rejected_without_external_read_or_block(self):
        root = self.fixture([
            self.row("intent-a", "fonte-exata", False)])
        path = root / "data/editorial/portfolio_v2/a.jsonl"
        outside = root / "outside.jsonl"
        outside.write_text(
            json.dumps(self.row("outside", "fonte-exata", False)) + "\n",
            encoding="utf-8")
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises(OSError):
            check.audit(root)
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, "unsafe"):
            check.audit(root)


if __name__ == "__main__":
    unittest.main()
