import base64
import copy
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from tools import audit_v2_pages as auditor
from tools import generate_v2_review_queue as producer


def endpoint(node):
    return {"shard": node[0], "intent_id": node[1]}


def issue(code, left, right):
    field = {
        "title_dup_global": "title",
        "meta_dup_global": "meta_description",
        "h1_dup_global": "h1",
    }.get(code, "body")
    reasons = {
        "title_dup_global": "title",
        "meta_dup_global": "meta",
        "h1_dup_global": "h1",
        "body_jaccard_near_duplicate": "jaccard",
        "editorial_span_duplicate": "jaccard",
        "editorial_repeat_density": "density",
    }
    event = {
        "type": "issue",
        "code": code,
        "left": endpoint(left),
        "right": endpoint(right),
        "field": field,
        "candidate_reasons": [reasons[code]],
        "publication_allowed": False,
        "index_policy": "noindex",
    }
    if code in producer.V3_SIMILARITY_DEFECT_CLASSES:
        # O adjudicador Go projeta o mesmo vetor de métricas não-zero em cada
        # issue de similaridade que o par disparar; este é o envelope real.
        event.update({
            "body_jaccard": 0.73,
            "max_identical_span_tokens": 48,
            "target_repeated_density": 0.20,
            "peer_repeated_density": 0.10,
        })
    return event


def symmetric_report(nodes, edges):
    files = {
        node[0]: {"pages": 1, "defects": {}}
        for node in nodes
    }
    for code, left, right in edges:
        event = issue(code, left, right)
        for target, peer in ((left, right), (right, left)):
            result = files[target[0]]
            result["defects"].setdefault(code, []).append(
                f"{target[1]}~{peer[1]}")
            result.setdefault("evidence", {}).setdefault(
                "distinctness", []).append({
                    **event,
                    "projection_target": endpoint(target),
                    "projection_peer": endpoint(peer),
                })
    for result in files.values():
        for targets in result["defects"].values():
            targets[:] = sorted(set(targets))
    return {"files": files}


def legacy_ngram_report(left, right):
    phrase = "um dois tres quatro cinco seis sete oito nove dez onze doze"
    files = {
        left[0]: {
            "pages": 1,
            "defects": {
                "title_len": [left[1]],
                "ngram_dup_global": [f"{left[1]}~{right[1]}"],
            },
            "evidence": {"ngram_dup_global": [{
                "target": f"{left[1]}~{right[1]}",
                "phrase": phrase,
                "field": "opening",
                "peer_field": "sections[0].text",
            }]},
        },
        right[0]: {
            "pages": 1,
            "defects": {
                "ngram_dup_global": [f"{right[1]}~{left[1]}"],
            },
            "evidence": {"ngram_dup_global": [{
                "target": f"{right[1]}~{left[1]}",
                "phrase": phrase,
                "field": "sections[0].text",
                "peer_field": "opening",
            }]},
        },
    }
    return {"files": files}


class DistinctnessV3QueueTest(unittest.TestCase):
    def test_relaunch_consumes_the_review_scope_public_field(self):
        script = pathlib.Path("ops/relaunch-review.sh").read_text(
            encoding="utf-8")
        self.assertIn(
            "target_ids = set(projected_scope.target_intents)", script)
        self.assertNotIn(
            "projected_scope.target_intent_ids", script)
        self.assertIn("WIKI_REVIEW_MAX_QUEUE_BYTES", script)
        self.assertIn("select_review_items_by_encoded_budget", script)
        self.assertIn("if len(new_bytes) > max_queue_bytes", script)
        scope = producer.ReviewScope(False, ("intent-a", "intent-b"))
        self.assertEqual(set(scope.target_intents), {"intent-a", "intent-b"})

    def setUp(self):
        self.nodes = [
            (f"data/editorial/v2_pages/civil-{suffix}.jsonl", intent)
            for suffix, intent in (
                ("a", "alpha"), ("b", "beta"),
                ("c", "gamma"), ("d", "delta"))
        ]
        self.locations = {node: 1 for node in self.nodes}
        self.meta = {
            f"civil-{suffix}": {"area": "civil"}
            for suffix in ("a", "b", "c", "d")
        }

    def test_similarity_star_is_one_sided_vertex_cover(self):
        a, b, c, d = self.nodes
        report = symmetric_report(self.nodes, [
            ("body_jaccard_near_duplicate", a, b),
            ("body_jaccard_near_duplicate", a, c),
            ("body_jaccard_near_duplicate", a, d),
        ])
        todo = producer.build_todo(
            report, set(), self.meta, self.locations, set(report["files"]))
        self.assertEqual([item["slug"] for item in todo], ["civil-a"])
        self.assertEqual(todo[0]["alvos"]["body_jaccard_near_duplicate"], [
            "alpha~beta", "alpha~delta", "alpha~gamma"])
        self.assertEqual(
            len(todo[0]["evidencias_distinctness"][
                "body_jaccard_near_duplicate"]), 3)
        self.assertEqual(todo[0]["distinctness_dependency_paths"], [
            b[0], c[0], d[0]])

    def test_exact_component_plans_all_n_minus_one_targets_and_preserves_owner(self):
        a, b, c, d = self.nodes
        report = symmetric_report(self.nodes, [
            ("title_dup_global", a, b),
            ("title_dup_global", a, c),
            ("title_dup_global", a, d),
        ])
        todo = producer.build_todo(
            report, set(), self.meta, self.locations, set(report["files"]))
        self.assertEqual(
            [item["slug"] for item in todo],
            ["civil-b", "civil-c", "civil-d"])
        for item in todo:
            component = item["componentes_distinctness"][
                "title_dup_global"][0]
            self.assertEqual(component["preserved_owner"], endpoint(a))
            self.assertEqual(component["member_count"], 4)
            self.assertRegex(component["component_id"], r"^[0-9a-f]{64}$")

    def test_exact_component_repairs_all_targets_across_shards(self):
        owner = ("data/editorial/v2_pages/civil-a.jsonl", "alpha")
        first = ("data/editorial/v2_pages/civil-b.jsonl", "beta")
        second = ("data/editorial/v2_pages/civil-b.jsonl", "bravo")
        later = ("data/editorial/v2_pages/civil-c.jsonl", "gamma")
        nodes = (owner, first, second, later)
        report = symmetric_report(nodes, [
            ("title_dup_global", owner, first),
            ("title_dup_global", owner, second),
            ("title_dup_global", owner, later),
        ])
        report["files"][first[0]]["pages"] = 2
        locations = {owner: 1, first: 1, second: 2, later: 1}
        todo = producer.build_todo(
            report, set(), {
                "civil-a": {"area": "civil"},
                "civil-b": {"area": "civil"},
                "civil-c": {"area": "civil"},
            }, locations, set(report["files"]))
        self.assertEqual(
            [item["slug"] for item in todo], ["civil-b", "civil-c"])
        self.assertEqual(
            todo[0]["alvos"]["title_dup_global"],
            ["beta~alpha", "bravo~alpha"])
        components = todo[0]["componentes_distinctness"][
            "title_dup_global"]
        self.assertEqual(
            [item["projection_target"]["intent_id"] for item in components],
            ["beta", "bravo"])
        self.assertEqual(
            len({item["component_id"] for item in components}), 1)
        self.assertEqual(
            todo[1]["alvos"]["title_dup_global"], ["gamma~alpha"])

    def test_endpoints_disambiguate_same_intent_across_shards(self):
        a = (self.nodes[0][0], "same-intent")
        b = (self.nodes[1][0], "same-intent")
        report = symmetric_report((a, b), [("h1_dup_global", a, b)])
        todo = producer.build_todo(
            report, set(), self.meta, {a: 1, b: 1}, set(report["files"]))
        self.assertEqual([item["slug"] for item in todo], ["civil-b"])
        evidence = todo[0]["evidencias_distinctness"]["h1_dup_global"][0]
        self.assertEqual(evidence["projection_target"], endpoint(b))
        self.assertEqual(evidence["projection_peer"], endpoint(a))

    def test_unstable_peer_defers_whole_exact_component_and_pair(self):
        a, b, c, d = self.nodes
        report = symmetric_report(self.nodes, [
            ("meta_dup_global", a, b),
            ("meta_dup_global", a, d),
            ("editorial_span_duplicate", c, d),
        ])
        eligible = {a[0], b[0], c[0]}
        todo = producer.build_todo(
            report, set(), self.meta, self.locations, eligible)
        self.assertEqual(todo, [])

    def test_two_immutable_exact_members_are_operational(self):
        a, b, *_ = self.nodes
        report = symmetric_report((a, b), [("title_dup_global", a, b)])
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.build_todo(
                report, {"civil-a", "civil-b"}, self.meta,
                self.locations, set(report["files"]))
        self.assertEqual(caught.exception.rca["editorial_tasks"], 0)
        self.assertIn(
            "distinctness_exact_component_multiple_immutable",
            caught.exception.rca["reason_codes"])

    def test_large_exact_component_exposes_all_targets_for_bounded_cohorts(self):
        nodes = tuple(
            (f"data/editorial/v2_pages/civil-z-{index:02d}.jsonl",
             f"intent-{index:02d}")
            for index in range(40))
        independent = (
            ("data/editorial/v2_pages/civil-y-a.jsonl", "independent-a"),
            ("data/editorial/v2_pages/civil-y-b.jsonl", "independent-b"),
        )
        edges = [
            ("h1_dup_global", nodes[0], node) for node in nodes[1:]
        ] + [("title_dup_global", independent[0], independent[1])]
        report = symmetric_report(nodes + independent, edges)
        locations = {node: 1 for node in nodes + independent}
        todo = producer.build_todo(
            report, set(), {}, locations, set(report["files"]))
        self.assertEqual(len(todo), 40)
        self.assertEqual(todo[0]["slug"], "civil-y-b")
        self.assertEqual(todo[1]["slug"], "civil-z-01")
        self.assertEqual(todo[-1]["slug"], "civil-z-39")
        self.assertEqual(todo, producer.build_todo(
            report, set(), {}, locations, set(report["files"])))
        self.assertEqual(
            todo[1]["componentes_distinctness"]["h1_dup_global"][0][
                "member_count"],
            40)

    def test_component_in_twenty_shards_fits_one_wave(self):
        nodes = tuple(
            (f"data/editorial/v2_pages/civil-wave-{index:02d}.jsonl",
             f"intent-{index:02d}")
            for index in range(20))
        report = symmetric_report(nodes, [
            ("title_dup_global", nodes[0], node) for node in nodes[1:]
        ])
        todo = producer.build_todo(
            report, set(), {}, {node: 1 for node in nodes},
            set(report["files"]))
        self.assertEqual(len(todo), 19)
        cohorts = producer.plan_exact_component_wave_cohorts(todo)
        self.assertEqual(len(cohorts), 1)
        self.assertEqual(len(cohorts[0]["member_paths"]), 19)
        self.assertEqual(cohorts[0]["cohort_index"], 0)
        self.assertEqual(cohorts[0]["cohort_count"], 1)
        selected, selected_cohorts, deferred = (
            producer.select_review_wave_epoch(todo, 24))
        self.assertEqual(len(selected), 19)
        self.assertEqual(selected_cohorts, cohorts)
        self.assertEqual(deferred, 0)

    def test_component_above_hard_limit_fails_deterministically_before_drafts(self):
        nodes = tuple(
            (f"data/editorial/v2_pages/civil-huge-{index:02d}.jsonl",
             f"intent-{index:02d}")
            for index in range(70))
        report = symmetric_report(nodes, [
            ("h1_dup_global", nodes[0], node) for node in nodes[1:]
        ])
        todo = producer.build_todo(
            report, set(), {}, {node: 1 for node in nodes},
            set(report["files"]))
        failures = []
        for _ in range(2):
            with self.assertRaises(
                    producer.DistinctnessOperationalError) as caught:
                producer.plan_exact_component_wave_cohorts(todo)
            failures.append(caught.exception.rca)
        self.assertEqual(failures[0], failures[1])
        self.assertEqual(
            failures[0]["reason_codes"],
            ["exact_component_wave_hard_limit_exceeded"],
        )
        self.assertEqual(failures[0]["affected_shards_total"], 69)
        self.assertEqual(failures[0]["editorial_tasks"], 0)
        self.assertFalse(failures[0]["publication_allowed"])
        with self.assertRaisesRegex(ValueError, "1..31"):
            producer.plan_exact_component_wave_cohorts(
                todo, 32, hard_max_members=32)

    def test_component_between_default_and_hard_limit_requires_explicit_epoch(self):
        nodes = tuple(
            (f"data/editorial/v2_pages/civil-wave-{index:02d}.jsonl",
             f"intent-{index:02d}")
            for index in range(27))
        report = symmetric_report(nodes, [
            ("title_dup_global", nodes[0], node) for node in nodes[1:]
        ])
        todo = producer.build_todo(
            report, set(), {}, {node: 1 for node in nodes},
            set(report["files"]))
        with self.assertRaises(
                producer.DistinctnessOperationalError) as caught:
            producer.plan_exact_component_wave_cohorts(todo)
        self.assertEqual(
            caught.exception.rca["reason_codes"],
            ["exact_component_wave_epoch_budget_exceeded"],
        )
        cohorts = producer.plan_exact_component_wave_cohorts(todo, 31)
        self.assertEqual(len(cohorts), 1)
        self.assertEqual(len(cohorts[0]["member_paths"]), 26)
        self.assertEqual(cohorts[0]["cohort_count"], 1)

    def test_one_immutable_is_exact_owner_and_similarity_peer(self):
        a, b, *_ = self.nodes
        report = symmetric_report((a, b), [
            ("title_dup_global", a, b),
            ("body_jaccard_near_duplicate", a, b),
        ])
        todo = producer.build_todo(
            report, {"civil-a"}, self.meta, self.locations,
            set(report["files"]))
        self.assertEqual([item["slug"] for item in todo], ["civil-b"])
        self.assertEqual(set(todo[0]["alvos"]), {
            "title_dup_global", "body_jaccard_near_duplicate"})
        self.assertEqual(
            todo[0]["componentes_distinctness"]["title_dup_global"][0][
                "preserved_owner"], endpoint(a))
        self.assertEqual(todo[0]["distinctness_dependency_paths"], [a[0]])

    def test_operational_issue_and_intent_identity_never_become_editorial(self):
        path = self.nodes[0][0]
        for code in (
                "distinctness_candidate_budget_exceeded",
                "intent_id_dup_global"):
            report = {"files": {path: {
                "pages": 1, "defects": {code: ["alpha:budget"]}}}}
            with self.assertRaises(
                    producer.DistinctnessOperationalError) as caught:
                producer.build_todo(
                    report, set(), self.meta, {self.nodes[0]: 1}, {path})
            self.assertEqual(caught.exception.rca["editorial_tasks"], 0)
            self.assertEqual(caught.exception.rca["reason_codes"], [code])

    def test_missing_reverse_or_projection_is_rejected(self):
        a, b, *_ = self.nodes
        report = symmetric_report((a, b), [
            ("editorial_repeat_density", a, b)])
        report["files"][b[0]]["evidence"]["distinctness"].clear()
        with self.assertRaisesRegex(ValueError, "sem evidência autenticada"):
            producer.build_todo(
                report, set(), self.meta, self.locations, set(report["files"]))

    def test_code_specific_closed_schema_and_metrics_are_required(self):
        a, b, *_ = self.nodes
        cases = []

        exact_open = symmetric_report((a, b), [
            ("title_dup_global", a, b)])
        exact_open["files"][a[0]]["evidence"]["distinctness"][0][
            "unexpected"] = True
        cases.append((exact_open, "schema exato"))

        below_threshold = symmetric_report((a, b), [
            ("body_jaccard_near_duplicate", a, b)])
        for result in below_threshold["files"].values():
            result["evidence"]["distinctness"][0]["body_jaccard"] = 0.69
        cases.append((below_threshold, "abaixo do limiar"))

        unordered_reasons = symmetric_report((a, b), [
            ("editorial_repeat_density", a, b)])
        for result in unordered_reasons["files"].values():
            result["evidence"]["distinctness"][0][
                "candidate_reasons"] = ["density", "jaccard"]
        cases.append((unordered_reasons, "schema de similaridade"))

        for report, expected in cases:
            with self.subTest(expected=expected), self.assertRaisesRegex(
                    producer.DistinctnessOperationalError, expected):
                producer.build_todo(
                    report, set(), self.meta, self.locations,
                    set(report["files"]))

    def test_projection_and_reverse_payload_are_authenticated(self):
        a, b, c, *_ = self.nodes
        bad_projection = symmetric_report((a, b), [
            ("editorial_span_duplicate", a, b)])
        bad_projection["files"][a[0]]["evidence"]["distinctness"][0][
            "projection_peer"] = endpoint(c)
        with self.assertRaisesRegex(
                producer.DistinctnessOperationalError, "projeção"):
            producer.build_todo(
                bad_projection, set(), self.meta, self.locations,
                set(bad_projection["files"]))

        divergent_reverse = symmetric_report((a, b), [
            ("editorial_span_duplicate", a, b)])
        divergent_reverse["files"][b[0]]["evidence"]["distinctness"][0][
            "max_identical_span_tokens"] = 49
        with self.assertRaisesRegex(
                producer.DistinctnessOperationalError, "reverso simétrico"):
            producer.build_todo(
                divergent_reverse, set(), self.meta, self.locations,
                set(divergent_reverse["files"]))

    def test_raw_file_classes_are_routed_out_of_editorial_review(self):
        path = self.nodes[0][0]
        locations = {self.nodes[0]: 1}
        for defect_class, target in (
                ("json_invalido", "linha_1"),
                ("json_invalido", "jsonl_sem_lf_terminal"),
                ("contagem", "esperado=2 real=1")):
            with self.subTest(defect_class=defect_class, target=target):
                report = {"files": {path: {
                    "pages": 1,
                    "defects": {defect_class: [target]},
                }}}
                scope = producer.validate_review_scopes(report, locations)[path]
                self.assertFalse(scope.file_wide)
                self.assertEqual(scope.target_intents, ())
                with self.assertRaises(
                        producer.DistinctnessOperationalError) as caught:
                    producer.build_todo(
                        report, set(), self.meta, locations, {path})
                self.assertEqual(
                    caught.exception.rca["reason_codes"],
                    ["writing_recovery_route_owner_missing"])
                self.assertEqual(
                    producer.build_todo(
                        report, {"civil-a"}, self.meta, locations, {path}),
                    [])

    def test_unknown_record_target_is_operational_even_with_filewide_defect(self):
        path = self.nodes[0][0]
        report = {"files": {path: {
            "pages": 1,
            "defects": {"title_len": ["ghost"]},
        }}}
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.build_todo(
                report, set(), self.meta, {self.nodes[0]: 1}, {path})
        self.assertEqual(
            caught.exception.rca["reason_codes"],
            ["review_scope_record_target_unresolved"])
        self.assertEqual(caught.exception.rca["editorial_tasks"], 0)

        malformed_filewide = {"files": {path: {
            "pages": 1,
            "defects": {"json_invalido": ["qualquer-coisa"]},
        }}}
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.build_todo(
                malformed_filewide, set(), self.meta,
                {self.nodes[0]: 1}, {path})
        self.assertEqual(
            caught.exception.rca["reason_codes"],
            ["writing_recovery_finding_invalid"])

        malformed_count = {"files": {path: {
            "pages": 1,
            "defects": {"contagem": ["esperado=um real=1"]},
        }}}
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.build_todo(
                malformed_count, set(), self.meta,
                {self.nodes[0]: 1}, {path})
        self.assertEqual(
            caught.exception.rca["reason_codes"],
            ["writing_recovery_finding_invalid"])

    def test_raw_recovery_contract_covers_lf_json_and_count_end_to_end(self):
        path = self.nodes[0][0]
        cases = (
            (
                "missing_lf",
                b'{"intent_id":"alpha"}',
                ["alpha"],
                "json_invalido",
            ),
            (
                "invalid_json",
                b'{"intent_id":"alpha"\n',
                ["alpha"],
                "json_invalido",
            ),
            (
                "count_mismatch",
                b'{"intent_id":"alpha"}\n',
                ["alpha", "beta"],
                "contagem",
            ),
            (
                "tombstone_without_intent",
                b'{"skipped":true,"skip_reason":"incompleto"}\n',
                ["alpha"],
                "tombstone_invalido",
            ),
        )
        for label, payload, expected, expected_class in cases:
            with self.subTest(label=label):
                result = auditor.audit_file(
                    path, {}, expect_n=len(expected),
                    snapshot_bytes=payload)
                report = {"files": {path: result}}
                digest = producer._sha256(payload)
                contract = producer.build_writing_recovery_contract(
                    report, {"civil-a"}, {path: digest},
                    {path: expected})
                self.assertEqual(len(contract), 1)
                route = contract[0]
                self.assertEqual(route["route"], "writing_full_shard_recovery")
                self.assertEqual(route["target_sha256"], digest)
                self.assertEqual(route["expected_intent_ids"], expected)
                self.assertIn(expected_class, route["alvos"])
                self.assertFalse(route["review_allowed"])
                self.assertFalse(route["publication_allowed"])
                self.assertEqual(route["index_policy"], "noindex")
                self.assertEqual(
                    route["recovery_item_sha256"],
                    producer.writing_recovery_item_sha256(route))
                raw_projection = (
                    producer.derive_writing_raw_recovery_projection(
                        payload, path, digest, expected))
                self.assertIsNotNone(raw_projection)
                self.assertFalse(raw_projection["review_allowed"])
                self.assertFalse(raw_projection["publication_allowed"])
                self.assertEqual(
                    producer.validate_writing_raw_recovery_projection(
                        raw_projection, target_rel_path=path,
                        target_sha256=digest,
                        expected_intents=expected),
                    raw_projection)
                tampered = copy.deepcopy(raw_projection)
                tampered["reason_codes"] = ["unknown"]
                with self.assertRaises(ValueError):
                    producer.validate_writing_raw_recovery_projection(tampered)
                locations = {
                    (path, intent): index
                    for index, intent in enumerate(expected, 1)
                }
                self.assertEqual(
                    producer.build_todo(
                        report, {"civil-a"}, self.meta, locations, {path}),
                    [])

    def test_canonical_tombstone_defect_uses_all_row_review_map(self):
        path = self.nodes[0][0]
        payload = b'{"intent_id":"alpha","skipped":true}\n'
        result = auditor.audit_file(
            path, {}, expect_n=1, snapshot_bytes=payload)
        self.assertEqual(result["defects"]["tombstone_invalido"], ["alpha"])
        self.assertEqual(producer.writing_recovery_findings(result), {})
        self.assertTrue(producer.review_addressable_invalid_tombstone_batch(
            [{"intent_id": "alpha", "skipped": True}], ["alpha"]))
        self.assertFalse(producer.review_addressable_invalid_tombstone_batch(
            [{"skipped": True}], ["alpha"]))
        report = {"files": {path: result}}
        todo = producer.build_todo(
            report, set(), self.meta, {}, {path}, {(path, "alpha"): 1})
        self.assertEqual(len(todo), 1)
        self.assertEqual(todo[0]["alvos"]["tombstone_invalido"], ["alpha"])

    def test_raw_recovery_refuses_to_discard_valid_extra(self):
        path = self.nodes[0][0]
        payload = (
            b'{"intent_id":"alpha","sections":[{"text":"a"}]}\n'
            b'{"intent_id":"extra","sections":[{"text":"b"}]}\n'
        )
        with self.assertRaises(
                producer.DistinctnessOperationalError) as caught:
            producer.derive_writing_raw_recovery_projection(
                payload, path, producer._sha256(payload), ["alpha"])
        self.assertEqual(
            caught.exception.rca["reason_codes"],
            ["writing_raw_recovery_valid_extra_requires_migration"])

    def test_staged_raw_recovery_binds_opaque_target_and_exact_slice(self):
        path = self.nodes[0][0]
        target_payload = b'{"intent_id":"alpha","sections":[]}'
        target_digest = producer._sha256(target_payload)
        projection = producer.derive_writing_raw_recovery_projection(
            target_payload, path, target_digest, ["alpha"])
        encoded = base64.b64encode(json.dumps(
            projection, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).decode("ascii")
        semantic = producer.WritingSemanticContract(
            digest="a" * 64,
            unresolved_intents=frozenset(),
            requirement_fingerprints={}, portfolio_rel_paths={},
            target_rel_paths={}, superseded_target_rel_paths={},
            superseded_page_record_sha256={}, evidence_kinds={},
            evidence_rel_paths={}, evidence_sha256={},
            dependency_sha256={}, absent_dependency_paths=frozenset())
        resolution = producer.WritingSourceResolution(
            selected_intents=("alpha",), source_overrides={},
            strict_source_intents=())
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            target = root / path
            target.parent.mkdir(parents=True)
            target.write_bytes(target_payload)
            evidence = producer.persist_writing_raw_recovery_preimage(
                root, target_payload, target_digest)
            staged = root / "staged.jsonl"
            staged_payload = (
                b'{"intent_id":"alpha","skipped":true,'
                b'"skip_reason":"fonte indisponivel"}\n')
            staged.write_bytes(staged_payload)
            with (mock.patch.object(
                    producer, "verify_writing_source_resolution",
                    return_value=resolution),
                  mock.patch.object(
                    producer, "load_writing_semantic_contract",
                    return_value=semantic),
                  mock.patch.object(
                    producer,
                    "verify_writing_semantic_contract_dependencies")):
                captured = producer.verify_staged_writing_recovery(
                    root, staged, path, target_digest,
                    "data/editorial/portfolio_v2/civil.jsonl", "b" * 64,
                    "data/editorial/v2_source_hint_catalog.json", "c" * 64,
                    ["civil"], 0, 1, 1, None, "ignored", encoded,
                    evidence)
                self.assertEqual(captured.payload, staged_payload)
                target.write_bytes(target_payload + b" ")
                resumed = producer.verify_staged_writing_recovery(
                    root, staged, path, target_digest,
                    "data/editorial/portfolio_v2/civil.jsonl", "b" * 64,
                    "data/editorial/v2_source_hint_catalog.json", "c" * 64,
                    ["civil"], 0, 1, 1, None, "ignored", encoded,
                    evidence)
                self.assertEqual(resumed.payload, staged_payload)

    def test_relaunch_persists_authenticated_recovery_routes(self):
        script = pathlib.Path("ops/relaunch-review.sh").read_text(
            encoding="utf-8")
        for required in (
                "preimage_raw_recovery_paths",
                "producer.build_writing_recovery_contract(",
                "writing_recovery_auditor_contract_missing",
                "const WRITING_RECOVERY_ROUTES = ",
                "writing_recovery_routes = []"):
            self.assertIn(required, script)

    def test_legacy_global_ngram_peer_is_a_relational_dependency(self):
        left, right, *_ = self.nodes
        report = legacy_ngram_report(left, right)
        todo = producer.build_todo(
            report, set(), self.meta,
            {left: 1, right: 1}, set(report["files"]))
        self.assertEqual([item["slug"] for item in todo], ["civil-a"])
        self.assertEqual(
            todo[0]["distinctness_dependency_paths"], [right[0]])

        ambiguous = copy.deepcopy(report)
        duplicate_peer = (
            "data/editorial/v2_pages/civil-c.jsonl", right[1])
        ambiguous["files"][duplicate_peer[0]] = {
            "pages": 1, "defects": {}}
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.build_todo(
                ambiguous, set(), self.meta,
                {left: 1, right: 1, duplicate_peer: 1},
                set(ambiguous["files"]))
        self.assertIn(
            "review_ngram_global_endpoint_ambiguous",
            caught.exception.rca["reason_codes"])

    def test_queue_item_fingerprint_is_canonical_and_self_excluding(self):
        first = {
            "slug": "civil-a",
            "alvos": {"title_len": ["alpha"]},
            "nested": {"b": 2, "a": "ação"},
        }
        reordered = {
            "nested": {"a": "ação", "b": 2},
            "alvos": {"title_len": ["alpha"]},
            "slug": "civil-a",
        }
        digest = producer.review_queue_item_sha256(first)
        self.assertEqual(digest, producer.review_queue_item_sha256(reordered))
        with_receipt = copy.deepcopy(first)
        with_receipt["queue_item_sha256"] = "f" * 64
        self.assertEqual(
            digest, producer.review_queue_item_sha256(with_receipt))
        changed = copy.deepcopy(first)
        changed["alvos"]["title_len"] = ["beta"]
        self.assertNotEqual(
            digest, producer.review_queue_item_sha256(changed))
        self.assertNotIn("queue_item_sha256", first)
        with self.assertRaisesRegex(ValueError, "chave não textual"):
            producer.review_queue_item_sha256({"ok": {1: "inválido"}})
        with self.assertRaisesRegex(ValueError, "float inválido"):
            producer.review_queue_item_sha256({"value": float("nan")})
        with self.assertRaisesRegex(ValueError, "somente o recibo"):
            producer.review_queue_item_sha256({
                "queue_item_sha256": "f" * 64,
            })

    def test_queue_payload_budget_is_exact_and_packs_later_small_item(self):
        def authenticated(slug, text):
            item = {"slug": slug, "texto": text}
            item["queue_item_sha256"] = (
                producer.review_queue_item_sha256(item))
            return item

        first = authenticated("civil-a", "ação")
        too_large = authenticated("civil-b", "x" * 4000)
        later = authenticated("civil-c", "fim")
        first_bytes = len(json.dumps(
            first, ensure_ascii=False, allow_nan=False).encode("utf-8"))
        later_bytes = len(json.dumps(
            later, ensure_ascii=False, allow_nan=False).encode("utf-8"))
        budget = 2 + first_bytes + 2 + later_bytes
        selected, deferred, encoded_bytes = (
            producer.select_review_items_by_encoded_budget(
                [first, too_large, later], budget))
        self.assertEqual(
            [item["slug"] for item in selected], ["civil-a", "civil-c"])
        self.assertEqual(
            [item["slug"] for item in deferred], ["civil-b"])
        self.assertEqual(encoded_bytes, budget)
        self.assertEqual(encoded_bytes, len(json.dumps(
            selected, ensure_ascii=False).encode("utf-8")))
        self.assertEqual(
            (selected, deferred, encoded_bytes),
            producer.select_review_items_by_encoded_budget(
                [first, too_large, later], budget))

        forged = copy.deepcopy(first)
        forged["texto"] = "drift"
        with self.assertRaisesRegex(ValueError, "fingerprint válido"):
            producer.select_review_items_by_encoded_budget([forged], budget)
        with self.assertRaisesRegex(ValueError, "entre 2 bytes e 64 MiB"):
            producer.select_review_items_by_encoded_budget([first], 1)

    def test_epoch_is_bound_to_digest_and_single_roots(self):
        digest = "1" * 64
        generation = "2" * 64
        stock = "3" * 64
        algorithm = "4" * 64
        batch = "5" * 64
        files = {}
        authenticated = {}
        for node in self.nodes[:2]:
            files[node[0]] = {
                "file": node[0],
                "pages": 1,
                "active_pages": 1,
                "defects": {},
                "distinctness_index": {
                    "status": "ready",
                    "mode": producer.GLOBAL_DISTINCTNESS_MODE,
                    "schema_version": 1,
                    "algorithm_fingerprint": algorithm,
                    "batch_fingerprint": batch,
                    "generation_root": generation,
                    "stock_root": stock,
                    "target_digest": digest,
                    "target_snapshot_bound": True,
                    "inventory_complete": True,
                    "inventory_stable": True,
                    "stock_shards": 2,
                    "stock_pages": 2,
                    "visible_surface_scope_complete": True,
                    "visible_surfaces": ["title", "body"],
                    "candidate_routing_complete": True,
                    "local_routing_complete": True,
                    "publication_allowed": False,
                    "index_policy": "noindex",
                },
            }
            authenticated[node[0]] = digest
        report = {"files": files}
        epoch = producer.validate_global_distinctness_epoch(
            report, authenticated, files,
            expected_schema_version=1,
            expected_algorithm_fingerprint=algorithm,
            expected_batch_fingerprint=batch,
            expected_visible_surfaces=("title", "body"))
        self.assertEqual(epoch["authenticated_shards"], 2)
        stale = copy.deepcopy(report)
        stale["files"][self.nodes[1][0]]["distinctness_index"][
            "target_digest"] = "6" * 64
        with self.assertRaises(producer.DistinctnessOperationalError) as caught:
            producer.validate_global_distinctness_epoch(
                stale, authenticated, files,
                expected_schema_version=1,
                expected_algorithm_fingerprint=algorithm,
                expected_batch_fingerprint=batch,
                expected_visible_surfaces=("title", "body"))
        self.assertIn(
            "distinctness_epoch_authentication_failed",
            caught.exception.rca["reason_codes"])

    def test_dependency_snapshot_verifier_rejects_peer_evolution(self):
        previous = pathlib.Path.cwd()
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            pages = root / "data/editorial/v2_pages"
            pages.mkdir(parents=True)
            peer = pages / "civil-peer.jsonl"
            peer.write_text('{"intent_id":"peer"}\n', encoding="utf-8")
            os.chdir(root)
            try:
                path = "data/editorial/v2_pages/civil-peer.jsonl"
                digest = producer.snapshot_sha256(path)
                self.assertEqual(
                    producer.verify_review_dependency_snapshots({path: digest}),
                    1)
                peer.write_text('{"intent_id":"evolved"}\n', encoding="utf-8")
                with self.assertRaises(producer.CASMismatch):
                    producer.verify_review_dependency_snapshots({path: digest})
            finally:
                os.chdir(previous)

    def test_staged_review_scope_returns_the_authenticated_payload(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            pages = root / "data/editorial/v2_pages"
            pages.mkdir(parents=True)
            target = pages / "civil-a.jsonl"
            alpha_before = b'{"intent_id":"alpha","title":"antes"}'
            alpha_after = b'{"intent_id":"alpha","title":"depois"}'
            beta = b'{"intent_id":"beta","title":"preservado"}'
            target_payload = alpha_before + b"\n" + beta + b"\n"
            staged_payload = alpha_after + b"\n" + beta + b"\n"
            target.write_bytes(target_payload)
            expected = producer.snapshot_sha256(target)
            workspace = producer.create_workflow_workspace(
                "civil-a", expected, root)
            staged = workspace / "review.jsonl"
            staged.write_bytes(staged_payload)
            preserved = {"beta": producer._sha256(beta)}

            captured = producer.verify_staged_review_scope(
                root, workspace, staged,
                "data/editorial/v2_pages/civil-a.jsonl", expected,
                ["alpha", "beta"], ["alpha"], preserved,
                file_wide_review=False)
            staged.write_bytes(
                b'{"intent_id":"alpha","title":"troca-tardia"}\n' +
                b'{"intent_id":"beta","title":"troca-tardia"}\n')
            self.assertEqual(captured.payload, staged_payload)
            self.assertEqual(captured.digest, producer._sha256(staged_payload))

    def test_staged_review_scope_rejects_scope_and_path_attacks(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = pathlib.Path(raw_root)
            pages = root / "data/editorial/v2_pages"
            pages.mkdir(parents=True)
            target = pages / "civil-a.jsonl"
            alpha_before = b'{"intent_id":"alpha","title":"antes"}'
            alpha_after = b'{"intent_id":"alpha","title":"depois"}'
            beta = b'{"intent_id":"beta","title":"preservado"}'
            target_payload = alpha_before + b"\n" + beta + b"\n"
            staged_payload = alpha_after + b"\n" + beta + b"\n"
            target.write_bytes(target_payload)
            expected = producer.snapshot_sha256(target)
            workspace = producer.create_workflow_workspace(
                "civil-a", expected, root)
            staged = workspace / "review.jsonl"
            staged.write_bytes(staged_payload)
            preserved = {"beta": producer._sha256(beta)}

            def verify(
                staged_path=staged,
                target_sha256=expected,
                target_ids=None,
                review_ids=None,
                preserved_hashes=None,
                file_wide=False,
            ):
                return producer.verify_staged_review_scope(
                    root, workspace, staged_path,
                    "data/editorial/v2_pages/civil-a.jsonl", target_sha256,
                    ["alpha", "beta"] if target_ids is None else target_ids,
                    ["alpha"] if review_ids is None else review_ids,
                    preserved if preserved_hashes is None else preserved_hashes,
                    file_wide_review=file_wide)

            with self.assertRaisesRegex(ValueError, "hash preservado"):
                verify(preserved_hashes={"beta": "0" * 64})
            with self.assertRaisesRegex(ValueError, "file-wide"):
                verify(file_wide=True)
            with self.assertRaisesRegex(ValueError, "subsequência"):
                verify(review_ids=["beta", "alpha"], preserved_hashes={})
            with self.assertRaisesRegex(ValueError, "preimagem capturada"):
                verify(target_ids=["beta", "alpha"])

            staged.write_bytes(
                alpha_after + b"\n" +
                b'{"intent_id":"beta","title":"editado"}\n')
            with self.assertRaisesRegex(ValueError, "fora do escopo"):
                verify()
            staged.write_bytes(staged_payload)

            outside = root / "outside.jsonl"
            outside.write_bytes(staged_payload)
            with self.assertRaisesRegex(ValueError, "filho direto"):
                verify(staged_path=outside)

            hardlink = workspace / "hardlink.jsonl"
            os.link(staged, hardlink)
            try:
                with self.assertRaisesRegex(RuntimeError, "hardlink"):
                    verify()
            finally:
                hardlink.unlink()

            symlink = workspace / "symlink.jsonl"
            symlink.symlink_to(staged.name)
            try:
                with self.assertRaises(OSError):
                    verify(staged_path=symlink)
            finally:
                symlink.unlink()

            workspace.chmod(0o755)
            try:
                with self.assertRaisesRegex(RuntimeError, "0700"):
                    verify()
            finally:
                workspace.chmod(0o700)

            target.write_bytes(
                b'{"intent_id":"alpha","title":"drift"}\n' + beta + b"\n")
            with self.assertRaises(producer.CASMismatch):
                verify()


if __name__ == "__main__":
    unittest.main()
