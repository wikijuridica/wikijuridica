#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools import plan_v2_source_hint_resolution as planner


PLANALTO_CDC = "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm"


class SourceHintResolutionPlannerTests(unittest.TestCase):
    def fixture(self, *, catalog=None, portfolios=None, pages=None) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "data/editorial/portfolio_v2").mkdir(parents=True)
        (root / "data/editorial/v2_pages").mkdir(parents=True)
        (root / "data/source-registry").mkdir(parents=True)

        if catalog is None:
            catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                "cdc-art-14-defeito-servico": {
                    "name": "Lei 8.078/1990 (Código de Defesa do Consumidor), art. 14",
                    "url": PLANALTO_CDC,
                    "anchor_claim": "O art. 14 disciplina defeito do serviço.",
                },
            },
        }
        (root / "data/editorial/v2_source_hint_catalog.json").write_text(
            json.dumps(catalog, ensure_ascii=False) + "\n", encoding="utf-8")
        registry = {
            "source_id": "planalto-ccivil03",
            "official_domains": ["www.planalto.gov.br"],
            "canonical_base_urls": ["https://www.planalto.gov.br/ccivil_03/"],
        }
        (root / "data/source-registry/source_registry_v2.jsonl").write_text(
            json.dumps(registry) + "\n", encoding="utf-8")

        if portfolios is None:
            portfolios = [self.portfolio("intent-a")]
        (root / "data/editorial/portfolio_v2/a.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in portfolios),
            encoding="utf-8")
        if pages is None:
            pages = [
                ("a.jsonl", self.page("page-a")),
                ("b.jsonl", self.page("page-b")),
            ]
        for filename, row in pages:
            (root / "data/editorial/v2_pages" / filename).write_text(
                json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        return root

    @staticmethod
    def portfolio(intent: str, hint="cdc-lei-8078-1990-art-14", pending=False):
        return {
            "intent_id": intent,
            "source_hints": [hint],
            "needs_source_research": pending,
        }

    @staticmethod
    def page(intent: str, *, name="Lei 8.078/1990, art. 14", url=PLANALTO_CDC,
             claim="O art. 14 disciplina a responsabilidade.", verified="2026-07-15", status=200):
        return {
            "intent_id": intent,
            "official_sources": [{
                "name": name, "url": url, "anchor_claim": claim,
                "verified_at": verified, "http_status": status,
            }],
        }

    def plan(self, root: Path, **kwargs):
        kwargs.setdefault("as_of", dt.date(2026, 7, 16))
        return planner.build_plan(root, **kwargs)

    def test_exact_act_article_observations_only_create_blocked_review_candidate(self):
        report = self.plan(self.fixture())
        self.assertFalse(report["publication_allowed"])
        self.assertEqual(report["records_total"], 1)
        record = report["records"][0]
        self.assertEqual(
            record["resolution_status"],
            "existing_catalog_alias_review_candidate_exact_observation_only")
        self.assertEqual(record["candidate_catalog_hint"], "cdc-art-14-defeito-servico")
        self.assertFalse(record["resolution_applied"])
        self.assertTrue(record["needs_source_research_required_until_applied"])
        self.assertFalse(record["candidate_official_sources"][0][
            "independent_provenance_verified"])

    def test_article_mismatch_never_rewrites_to_nearby_catalog_alias(self):
        root = self.fixture(
            portfolios=[self.portfolio("intent-a", "cdc-lei-8078-1990-art-51")],
            pages=[
                ("a.jsonl", self.page("page-a")),
                ("b.jsonl", self.page("page-b")),
            ])
        record = self.plan(root)["records"][0]
        self.assertNotIn("catalog_alias_candidate", record["resolution_status"])
        self.assertEqual(record["candidate_catalog_hint"], "")

    def test_generic_court_label_and_unverified_sources_stay_research_blocked(self):
        root = self.fixture(
            portfolios=[self.portfolio("intent-a", "STJ")],
            pages=[
                ("a.jsonl", self.page("page-a", verified="", status=0)),
                ("b.jsonl", self.page("page-b", verified="", status=0)),
            ])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["resolution_status"], "generic_authority_research_required")
        self.assertEqual(record["candidate_official_sources"], [])

    def test_future_or_stale_verification_never_counts_as_observation(self):
        root = self.fixture(pages=[
            ("a.jsonl", self.page("page-a", verified="2026-06-15")),
            ("b.jsonl", self.page("page-b", verified="2026-07-17")),
        ])
        report = self.plan(root, as_of=dt.date(2026, 7, 16))
        record = report["records"][0]
        self.assertEqual(
            record["resolution_status"],
            "existing_catalog_alias_needs_independent_provenance")
        self.assertEqual(record["candidate_official_sources"], [])
        self.assertEqual(report["source_observation_counts"]["stale_verification"], 1)
        self.assertEqual(report["source_observation_counts"]["future_verification"], 1)

    def test_same_intent_repeated_in_two_files_does_not_fabricate_independence(self):
        root = self.fixture(pages=[
            ("a.jsonl", self.page("same-page")),
            ("b.jsonl", self.page("same-page")),
        ])
        record = self.plan(root)["records"][0]
        self.assertEqual(
            record["resolution_status"],
            "existing_catalog_alias_needs_independent_provenance")

    def test_conflicting_act_name_and_url_are_not_observational_evidence(self):
        root = self.fixture(pages=[
            ("a.jsonl", self.page("page-a", name="Lei 8.213/1991, art. 14")),
            ("b.jsonl", self.page("page-b", name="Lei 8.213/1991, art. 14")),
        ])
        record = self.plan(root)["records"][0]
        self.assertEqual(
            record["resolution_status"],
            "existing_catalog_alias_needs_independent_provenance")

    def test_act_label_on_unrelated_official_page_is_not_source_identity(self):
        self.assertIsNone(planner.source_identity(
            "STF — ADI 6327",
            "https://www.gov.br/pt-br/servicos/solicitar-salario-maternidade"))

    def test_regulatory_identity_requires_issuer_and_year(self):
        signature = planner.signature_from_hint("anac-res-400-2016-art-14", {})
        self.assertIsNotNone(signature)
        self.assertEqual(signature.identity.issuer, "anac")
        self.assertEqual(signature.identity.year, "2016")
        self.assertIsNone(planner.signature_from_hint("res-400-2016-art-14", {}))
        self.assertIsNone(planner.signature_from_hint("anac-res-400-art-14", {}))

    def test_material_locator_never_collapses_paragraph_or_inciso(self):
        catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                "cdc-art-14-paragrafo-2-inciso-i": {
                    "name": "Código de Defesa do Consumidor, art. 14, parágrafo 2º, inciso I",
                    "url": PLANALTO_CDC,
                    "anchor_claim": "O dispositivo trata do defeito do serviço.",
                },
            },
        }
        hint = "cdc-lei-8078-1990-art-14-paragrafo-3-inciso-ii"
        root = self.fixture(
            catalog=catalog,
            portfolios=[self.portfolio("intent-a", hint)],
            pages=[
                ("a.jsonl", self.page(
                    "page-a", name="Lei 8.078/1990, art. 14, parágrafo 3º, inciso II")),
                ("b.jsonl", self.page(
                    "page-b", name="Lei 8.078/1990, art. 14, parágrafo 3º, inciso II")),
            ])
        record = self.plan(root)["records"][0]
        self.assertEqual(
            record["resolution_status"],
            "official_source_cluster_research_plan_observation_only")
        self.assertEqual(record["candidate_catalog_hint"], "")
        self.assertIn(":artrel=single:par=3:inc=ii:", record["source_signature"])

    def test_cf_shorthand_preserves_implicit_inciso(self):
        signature = planner.signature_from_hint("CF art. 155 II", {})
        self.assertIsNotNone(signature)
        self.assertEqual(signature.articles, ("155",))
        self.assertEqual(signature.incisos, ("ii",))

    def test_alphanumeric_legal_number_never_crashes_year_detection(self):
        identities = planner.parse_explicit_identities("art. 911-C da lei")
        self.assertEqual(identities, [])
        signature = planner.signature_from_hint("lei-911c-1980-art-1", {})
        self.assertIsNotNone(signature)
        self.assertEqual(signature.identity.number, "911c")

    def test_law_number_that_looks_like_year_does_not_become_article(self):
        signature = planner.signature_from_hint("Lei 2.020/1953, art. 1", {})
        self.assertIsNotNone(signature)
        self.assertEqual(signature.identity.number, "2020")
        self.assertEqual(signature.identity.year, "1953")
        self.assertEqual(signature.articles, ("1",))

    def test_historical_constitution_is_not_forced_to_1988(self):
        signature = planner.signature_from_hint("CF 1967, art. 150", {})
        self.assertIsNotNone(signature)
        self.assertEqual(signature.identity.number, "1967")
        self.assertEqual(signature.identity.year, "1967")

    def test_article_range_and_list_have_distinct_signatures(self):
        interval = planner.signature_from_hint("lei-8078-1990-arts-10-a-20", {})
        listing = planner.signature_from_hint("lei-8078-1990-arts-10-e-20", {})
        self.assertIsNotNone(interval)
        self.assertIsNotNone(listing)
        self.assertEqual(interval.article_relation, "range")
        self.assertEqual(listing.article_relation, "list")
        self.assertNotEqual(interval, listing)

    def test_ambiguous_lettered_or_implicit_locator_fails_closed(self):
        for value in (
                "lei-8078-1990-art-14-§-3º-I",
                "lei-8078-1990-art-1º-A"):
            signature, status = planner.signature_from_hint_diagnostic(value, {})
            self.assertIsNone(signature)
            self.assertEqual(status, "compound_locator_research_required")

    def test_catalog_alias_rejects_unexplained_numeric_identity(self):
        root = self.fixture(
            portfolios=[self.portfolio("intent-a", "cdc-9999-art-14")])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["resolution_status"], "identity_conflict_research_required")

    def test_generic_instrument_kind_never_becomes_catalog_alias(self):
        root = self.fixture(
            portfolios=[self.portfolio("intent-a", "lei-art-14")])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["resolution_status"], "needs_source_research_no_exact_identity")
        self.assertEqual(record["candidate_catalog_hint"], "")

    def test_page_observations_never_teach_new_aliases(self):
        root = self.fixture(
            portfolios=[self.portfolio("intent-a", "apelido-inventado-art-14")],
            pages=[
                ("a.jsonl", self.page("page-a", name="Apelido inventado, art. 14")),
                ("b.jsonl", self.page("page-b", name="Apelido inventado, art. 14")),
            ])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["resolution_status"], "needs_source_research_no_exact_identity")
        self.assertEqual(record["candidate_official_sources"], [])

    def test_catalog_url_outside_registry_never_teaches_alias(self):
        catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                "cdc": {
                    "name": "Lei 8.078/1990, art. 14",
                    "url": "https://example.invalid/lei-8078",
                    "anchor_claim": "Referência não oficial.",
                },
            },
        }
        root = self.fixture(
            catalog=catalog,
            portfolios=[self.portfolio("intent-a", "cdc-art-14")])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["resolution_status"], "needs_source_research_no_exact_identity")
        self.assertEqual(record["candidate_catalog_hint"], "")

    def test_invalid_exact_catalog_entry_remains_visible_as_unresolved(self):
        catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                "cdc-art-14": {
                    "name": "Lei 8.078/1990, art. 14",
                    "url": "https://example.invalid/lei-8078",
                    "anchor_claim": "O art. 14 disciplina o defeito do serviço.",
                },
            },
        }
        root = self.fixture(
            catalog=catalog,
            portfolios=[self.portfolio("intent-a", "cdc-art-14")])
        report = self.plan(root)
        self.assertEqual(report["records_total"], 1)
        self.assertEqual(report["counts"]["valid_exact_catalog_hints"], 0)
        self.assertEqual(report["records"][0]["candidate_catalog_hint"], "")

    def test_catalog_key_act_conflict_never_becomes_alias(self):
        bad_hint = "inss-lei-8213-1991-art-14"
        catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                bad_hint: {
                    "name": "Lei 8.078/1990, art. 14",
                    "url": PLANALTO_CDC,
                    "anchor_claim": "O art. 14 disciplina o defeito do serviço.",
                },
            },
        }
        root = self.fixture(
            catalog=catalog,
            portfolios=[self.portfolio("intent-a", bad_hint)])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["candidate_catalog_hint"], "")

    def test_catalog_locator_hierarchy_conflict_stays_research(self):
        bad_hint = "cdc-lei-8078-1990-art-14-paragrafo-3"
        catalog = {
            "_meta": {}, "strict_intents": [],
            "source_hints": {
                bad_hint: {
                    "name": "Lei 8.078/1990, art. 14, parágrafo 2º",
                    "url": PLANALTO_CDC,
                    "anchor_claim": "O art. 14, parágrafo 3º, disciplina a hipótese.",
                },
            },
        }
        root = self.fixture(
            catalog=catalog,
            portfolios=[self.portfolio("intent-a", bad_hint)])
        report = self.plan(root)
        self.assertEqual(report["counts"]["valid_exact_catalog_hints"], 0)
        self.assertEqual(report["records"][0]["candidate_catalog_hint"], "")

    def test_url_identity_rejects_ambiguity_traversal_and_foreign_host(self):
        self.assertEqual(planner.normalize_url(
            "https://processo.stj.jus.br/SCON/pesquisar.jsp?sumula=7&sumula=8"), "")
        self.assertEqual(planner.normalize_url(
            "https://www.planalto.gov.br/ccivil_03/../outro/leis/l8078.htm"), "")
        self.assertEqual(planner.normalize_url(
            "https://www.planalto.gov.br:443/ccivil_03/leis/l8078.htm"), "")
        self.assertIsNone(planner.identity_from_url(
            "https://example.invalid/ccivil_03/leis/l8078.htm"))
        self.assertIsNone(planner.identity_from_url(
            "https://processo.stj.jus.br/repetitivos/pesquisa.jsp?"
            "cod_tema_final=7&cod_tema_inicial=8"))

    def test_redirect_status_without_final_url_never_counts(self):
        root = self.fixture(pages=[
            ("a.jsonl", self.page("page-a", status=302)),
            ("b.jsonl", self.page("page-b", status=302)),
        ])
        record = self.plan(root)["records"][0]
        self.assertEqual(record["candidate_official_sources"], [])

    def test_compound_or_negated_or_ambiguous_issuer_fails_closed(self):
        cases = {
            "lei-8078-1990-art-14-e-art-51-paragrafo-3":
                "compound_locator_research_required",
            "lei-8078-1990-art-14-caput-e-paragrafo-3":
                "compound_locator_research_required",
            "lei-8078-1990-art-14-nao-revogada":
                "temporal_conflict_research_required",
            "stj-stf-re-123": "missing_regulatory_authority_or_year",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                signature, status = planner.signature_from_hint_diagnostic(value, {})
                self.assertIsNone(signature)
                self.assertEqual(status, expected)

    def test_matching_evidence_is_cached_once_per_exact_signature(self):
        root = self.fixture(portfolios=[
            self.portfolio("intent-a", "cdc-lei-8078-1990-art-14"),
            self.portfolio("intent-b", "lei-8078-1990-art-14"),
        ])
        original = planner.matching_evidence
        calls = []

        def counted(*args, **kwargs):
            calls.append(args[0])
            return original(*args, **kwargs)

        with mock.patch.object(planner, "matching_evidence", side_effect=counted):
            report = self.plan(root)
        self.assertEqual(report["records_total"], 2)
        self.assertEqual(len(calls), 1)

    def test_temporal_identity_keeps_revoked_historical_separate(self):
        signature = planner.signature_from_hint(
            "lei-6194-1974-art-5-revogada-historica", {})
        self.assertIsNotNone(signature)
        self.assertEqual(signature.temporal_status, "revoked_historical")
        self.assertIsNone(planner.signature_from_hint(
            "lei-6194-1974-art-5-revogada-vigente", {}))

    def test_malformed_hint_member_fails_as_validation_not_type_error(self):
        row = self.portfolio("intent-a")
        row["source_hints"] = [{"bad": "shape"}]
        root = self.fixture(portfolios=[row])
        with self.assertRaisesRegex(ValueError, "invalid portfolio source identity"):
            self.plan(root)

    def test_invalid_json_diagnostic_names_the_input(self):
        with self.assertRaisesRegex(ValueError, r"fixture\.json: invalid JSON"):
            planner.decode_object(b"{broken", "fixture.json")
        with self.assertRaisesRegex(ValueError, "non-finite JSON number"):
            planner.decode_object(b'{"value":NaN}', "fixture.json")

    def test_deterministic_shards_partition_hints_without_opening_flags(self):
        rows = [
            self.portfolio("intent-a", "cdc-lei-8078-1990-art-14"),
            self.portfolio("intent-b", "STJ"),
            self.portfolio("intent-c", "fonte-inexistente"),
        ]
        root = self.fixture(portfolios=rows)
        whole = self.plan(root)
        shards = [self.plan(root, shard_count=2, shard_index=index) for index in range(2)]
        hints = sorted(record["source_hint"] for shard in shards for record in shard["records"])
        self.assertEqual(hints, sorted(record["source_hint"] for record in whole["records"]))
        self.assertTrue(all(not shard["publication_allowed"] for shard in shards))

    def test_same_snapshot_and_as_of_produce_byte_stable_report(self):
        root = self.fixture()
        first = json.dumps(self.plan(root), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"))
        second = json.dumps(self.plan(root), ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"))
        self.assertEqual(first, second)

    def test_symlink_and_fifo_inputs_fail_closed_without_blocking(self):
        root = self.fixture()
        path = root / "data/editorial/portfolio_v2/a.jsonl"
        outside = root / "outside.jsonl"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises(OSError):
            self.plan(root)
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, "unsafe"):
            self.plan(root)

    def test_symlinked_input_directory_fails_closed(self):
        root = self.fixture()
        directory = root / "data/editorial/portfolio_v2"
        outside = root / "outside-portfolio"
        directory.rename(outside)
        directory.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "expected real directory"):
            self.plan(root)

    def test_10k_repeated_cluster_is_linear_and_keeps_bounded_samples(self):
        rows = [self.portfolio(f"intent-{index:05d}") for index in range(10_000)]
        root = self.fixture(portfolios=rows)
        started = time.perf_counter()
        report = self.plan(root)
        elapsed = time.perf_counter() - started
        self.assertEqual(report["counts"]["portfolio_records"], 10_000)
        self.assertEqual(report["records_total"], 1)
        self.assertLessEqual(len(report["records"][0]["sample_intents"]), planner.MAX_SAMPLES)
        self.assertLess(elapsed, 5.0)

    def test_10k_distinct_provisions_do_not_trigger_hint_times_evidence_scan(self):
        rows = [
            self.portfolio(
                f"intent-{index:05d}",
                f"lei-8078-1990-art-{index + 1}")
            for index in range(10_000)
        ]
        root = self.fixture(portfolios=rows)
        started = time.perf_counter()
        report = self.plan(root)
        elapsed = time.perf_counter() - started
        self.assertEqual(report["records_total"], 10_000)
        self.assertLess(elapsed, 8.0)


if __name__ == "__main__":
    unittest.main()
