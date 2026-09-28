import base64
import datetime
import hashlib
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from tools import generate_v2_review_queue as producer


class WritingSemanticContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "data/editorial/portfolio_v2").mkdir(parents=True)
        (self.root / "data/editorial/v2_pages").mkdir(parents=True)
        self.intent_id = "intent-semantico"
        self.portfolio_rel = "data/editorial/portfolio_v2/area.jsonl"
        self.target_rel = "data/editorial/v2_pages/area-01.jsonl"
        self.portfolio_raw = self.json_raw({
            "intent_id": self.intent_id,
            "family": "familia",
            "question": "Qual é o requisito jurídico agora aplicável?",
            "source_hints": [],
            "needs_source_research": False,
        })
        self.old_page_raw = self.page_raw(
            "Página que respondia ao requisito anterior.")
        self.evidence_rel = (
            "data/editorial/v2_semantic_superseded/"
            "writing-semantic-recuts-20260715.jsonl"
        )
        self.evidence_source_sha256 = self.digest(self.old_page_raw + b"\n")
        self.write_raw(self.portfolio_rel, self.portfolio_raw)
        self.write_raw(self.target_rel, self.old_page_raw)
        self.requirement = {
            "intent_id": self.intent_id,
            "portfolio_rel_path": self.portfolio_rel,
            "portfolio_record_sha256": self.digest(self.portfolio_raw),
            "target_rel_path": self.target_rel,
            "superseded_target_rel_path": self.target_rel,
            "superseded_page_record_sha256": self.digest(self.old_page_raw),
            "superseded_evidence_kind": "archived_shard_snapshot",
            "superseded_evidence_rel_path": self.evidence_rel,
            "superseded_evidence_sha256": self.evidence_source_sha256,
            "reason": "portfolio_semantics_changed_after_page_review",
            "required_review": "codex_legal_editorial_semantic_exact_page",
        }
        self.write_snapshot_evidence()
        baseline = self.digest(json.dumps(
            [self.requirement],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        self.baseline_patch = mock.patch.object(
            producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline)
        self.baseline_patch.start()
        self.addCleanup(self.baseline_patch.stop)
        catalog = {
            "_meta": {
                "schema_version": 1,
                "purpose": "teste fechado",
                "source_policy": "fonte oficial específica",
            },
            "strict_intents": [],
            "source_hints": {},
        }
        self.write_raw(
            "data/editorial/v2_source_hint_catalog.json",
            self.json_raw(catalog),
        )
        self.write_contract([])

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def json_raw(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @staticmethod
    def digest(payload):
        return hashlib.sha256(payload).hexdigest()

    def page_raw(self, text):
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        opening = (
            "Esta orientação jurídica apresenta o contexto aplicável, delimita "
            "a dúvida do leitor e explica por que a análise depende dos fatos, "
            "dos documentos disponíveis e da legislação oficial vigente."
        )
        section_one = " ".join([text] * 12)
        section_two = " ".join([
            "A conferência documental deve considerar datas, partes, objeto, "
            "procedimento adequado e eventual necessidade de orientação "
            "profissional para o caso concreto."
        ] * 6)
        page = {
            "intent_id": self.intent_id,
            "title": "Requisito jurídico atualizado e seus efeitos",
            "meta_description": (
                "Entenda o requisito jurídico atualizado, os documentos úteis "
                "e os cuidados necessários para avaliar a situação concreta."
            ),
            "h1": "Como verificar o requisito jurídico atualmente aplicável",
            "opening": opening,
            "official_sources": [
                {
                    "name": "Lei oficial número um",
                    "url": (
                        "https://www.planalto.gov.br/ccivil_03/leis/l0001.htm"),
                    "anchor_claim": "regra jurídica material aplicável",
                    "verified_at": today,
                    "http_status": 200,
                },
                {
                    "name": "Lei oficial número dois",
                    "url": (
                        "https://www.planalto.gov.br/ccivil_03/leis/l0002.htm"),
                    "anchor_claim": "procedimento e documentos pertinentes",
                    "verified_at": today,
                    "http_status": 200,
                },
            ],
            "sections": [
                {"heading": "Regra aplicável", "text": section_one},
                {"heading": "Documentos e cautelas", "text": section_two},
            ],
            "faq": [],
            "lane": "informativa",
            "needs_source_research": False,
            "internal_link_topics": ["requisito-legal", "documentos"],
        }
        body = [page["opening"]]
        for section in page["sections"]:
            body.extend((section["heading"], section["text"]))
        page["word_count"] = len(re.findall(
            r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+", " ".join(body)))
        return self.json_raw(page)

    def write_raw(self, rel_path, raw_line):
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw_line + b"\n")

    def write_snapshot_evidence(self):
        meta = self.json_raw({"_meta": {
            "schema_version": "v2_semantic_superseded_evidence_v2",
            "purpose": (
                "preserve_exact_shard_for_semantic_preimage_and_absence"),
            "checked_at": "2026-07-15",
            "source_rel_path": self.requirement[
                "superseded_target_rel_path"],
            "source_sha256": self.evidence_source_sha256,
            "record_count": 1,
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
        }})
        path = self.root / self.evidence_rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(meta + b"\n" + self.old_page_raw + b"\n")

    def resolution(self, page_raw):
        page_sha256 = self.digest(page_raw)
        return {
            "intent_id": self.intent_id,
            "requirement_sha256": producer._semantic_contract_fingerprint(
                self.requirement),
            "target_rel_path": self.target_rel,
            "page_record_sha256": page_sha256,
            "reviewed_at": "2026-07-15",
            "reviewed_by": "codex-reviewer",
            "review_contract": (
                "codex_legal_semantic_exact_page+deterministic_material_v1"),
            "semantic_review_evidence": {
                "requirement_sha256": (
                    producer._semantic_contract_fingerprint(self.requirement)),
                "page_record_sha256": page_sha256,
                "review_dimensions": [
                    "legal_scope", "current_rule", "user_question",
                    "distinction_from_superseded",
                ],
                "finding": (
                    "current_portfolio_requirement_satisfied_by_exact_page"),
            },
            "material_validation": producer._semantic_page_material_evidence(
                json.loads(page_raw), "fixture"),
            "verdict": "portfolio_requirement_satisfied",
        }

    def write_contract(self, resolutions):
        value = {
            "_meta": {
                "schema_version": "v2_writing_semantic_contract_v2",
                "purpose": "block_reuse_until_exact_page_semantic_review",
                "requirements_sha256": (
                    producer._WRITING_SEMANTIC_REQUIREMENTS_SHA256),
                "index_policy": "noindex",
                "render_allowed": False,
                "sitemap_allowed": False,
                "publication_allowed": False,
            },
            "requirements": [self.requirement],
            "resolutions": resolutions,
        }
        path = self.root / "data/editorial/v2_writing_semantic_contract.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n")

    def write_contract_v3(self, *, forward=(), adoptions=(), resolutions=()):
        value = {
            "_meta": {
                "schema_version": "v2_writing_semantic_contract_v3",
                "purpose": "block_reuse_until_exact_page_semantic_review",
                "requirements_sha256": (
                    producer._WRITING_SEMANTIC_REQUIREMENTS_SHA256),
                "index_policy": "noindex",
                "render_allowed": False,
                "sitemap_allowed": False,
                "publication_allowed": False,
            },
            "requirements": [self.requirement],
            "forward_candidates": list(forward),
            "adopt_existing_targets": list(adoptions),
            "resolutions": list(resolutions),
        }
        path = self.root / "data/editorial/v2_writing_semantic_contract.json"
        path.write_bytes(self.json_raw(value) + b"\n")

    def forward_candidate(self, page_raw):
        page_sha256 = self.digest(page_raw)
        return {
            "intent_id": self.intent_id,
            "requirement_sha256": producer._semantic_contract_fingerprint(
                self.requirement),
            "archived_page_record_sha256": self.digest(self.old_page_raw),
            "current_source_rel_path": self.target_rel,
            "current_source_record_sha256": page_sha256,
            "target_rel_path": self.target_rel,
            "observed_at": datetime.datetime.now(
                datetime.timezone.utc).date().isoformat(),
            "observed_by": "codex-reviewer",
            "status": "internal_review_pending",
            "material_validation": producer._semantic_page_material_evidence(
                json.loads(page_raw), "fixture forward"),
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
        }

    def affirmation(self, page_raw):
        page_sha256 = self.digest(page_raw)
        requirement_sha256 = producer._semantic_contract_fingerprint(
            self.requirement)
        return {
            "intent_id": self.intent_id,
            "transition_kind": "affirm_existing_owner",
            "requirement_sha256": requirement_sha256,
            "archived_page_record_sha256": page_sha256,
            "source_rel_path": self.target_rel,
            "source_record_state": "exact_reviewed",
            "target_rel_path": self.target_rel,
            "target_page_record_sha256": page_sha256,
            "reviewed_at": datetime.datetime.now(
                datetime.timezone.utc).date().isoformat(),
            "reviewed_by": "codex-reviewer",
            "review_contract": (
                "codex_legal_semantic_exact_page+deterministic_material_v1"),
            "semantic_review_evidence": {
                "requirement_sha256": requirement_sha256,
                "page_record_sha256": page_sha256,
                "review_dimensions": [
                    "legal_scope", "current_rule", "user_question",
                    "distinction_from_superseded",
                ],
                "finding": (
                    "current_portfolio_requirement_satisfied_by_fresh_exact_"
                    "owner_affirmation"),
            },
            "material_validation": producer._semantic_page_material_evidence(
                json.loads(page_raw), "fixture affirmation"),
            "verdict": "portfolio_requirement_satisfied",
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
        }

    def test_pending_old_page_is_neither_complete_nor_reusable(self):
        contract = producer.load_writing_semantic_contract(self.root)
        self.assertEqual(contract.unresolved_intents, {self.intent_id})

        page = json.loads(self.old_page_raw)
        ordinary = producer.classify_batch_completion(
            [page], [self.intent_id], "area-01.jsonl", [],
            semantically_blocked_intents=())
        self.assertTrue(ordinary.complete)
        self.assertEqual(ordinary.reusable_expected, (self.intent_id,))

        guarded = producer.classify_batch_completion(
            [page], [self.intent_id], "area-01.jsonl", [],
            semantically_blocked_intents=contract.unresolved_intents)
        self.assertFalse(guarded.complete)
        self.assertEqual(guarded.reusable_expected, ())

    def test_v3_forward_candidate_authenticates_altered_owner_but_stays_pending(self):
        changed_raw = self.page_raw(
            "Página alterada e revisada que aguarda a resolução transacional.")
        self.write_raw(self.target_rel, changed_raw)
        self.write_contract_v3(forward=[self.forward_candidate(changed_raw)])
        contract = producer.load_writing_semantic_contract(self.root)
        self.assertEqual(contract.unresolved_intents, {self.intent_id})
        self.assertIn(self.target_rel, contract.dependency_sha256)

    def test_v3_affirm_existing_owner_is_resolved_without_rewrite(self):
        self.write_contract_v3(adoptions=[self.affirmation(self.old_page_raw)])
        contract = producer.load_writing_semantic_contract(self.root)
        self.assertEqual(contract.unresolved_intents, set())

    def test_v3_forward_candidate_rejects_global_duplicate(self):
        changed_raw = self.page_raw("Página forward com owner global único.")
        self.write_raw(self.target_rel, changed_raw)
        self.write_raw("data/editorial/v2_pages/area-02.jsonl", changed_raw)
        self.write_contract_v3(forward=[self.forward_candidate(changed_raw)])
        with self.assertRaisesRegex(ValueError, "globalmente exato e único"):
            producer.load_writing_semantic_contract(self.root)

    def test_loader_caps_aggregate_semantic_snapshot_bytes(self):
        contract_path = (
            self.root / "data/editorial/v2_writing_semantic_contract.json")
        with mock.patch.object(
                producer,
                "_MAX_WRITING_SEMANTIC_SNAPSHOT_BYTES",
                contract_path.stat().st_size):
            with self.assertRaisesRegex(ValueError, "orçamento agregado"):
                producer.load_writing_semantic_contract(self.root)

    def _write_stock_filler(self, count):
        for index in range(count):
            self.write_raw(
                f"data/editorial/v2_pages/area-fill-{index:02d}.jsonl",
                self.json_raw({
                    "intent_id": f"filler-{index:04d}",
                    "pad": "documento juridico de preenchimento " * 60,
                }))

    def test_v3_proportional_budget_admits_stock_beyond_legacy_ceiling(self):
        # Estoque maior que o teto fixo legado (aqui simulado fixando o teto no
        # tamanho do contrato): sob o teto legado a leitura estouraria
        # "orçamento agregado"; o orçamento proporcional v3 autentica TODOS os
        # shards sem abortar. Prova que o novo caminho é superset estrito do
        # antigo — nenhum shard deixa de entrar no CAS de dependências.
        changed_raw = self.page_raw("Owner global unico apos recorte novo.")
        self.write_raw(self.target_rel, changed_raw)
        self.write_contract_v3(forward=[self.forward_candidate(changed_raw)])
        self._write_stock_filler(12)
        filler_paths = [
            f"data/editorial/v2_pages/area-fill-{index:02d}.jsonl"
            for index in range(12)
        ]
        contract_path = (
            self.root / "data/editorial/v2_writing_semantic_contract.json")
        with mock.patch.object(
                producer,
                "_MAX_WRITING_SEMANTIC_SNAPSHOT_BYTES",
                contract_path.stat().st_size):
            contract = producer.load_writing_semantic_contract(self.root)
        self.assertEqual(contract.unresolved_intents, {self.intent_id})
        for rel in [self.target_rel, *filler_paths]:
            self.assertIn(rel, contract.dependency_sha256)

    def test_v3_proportional_budget_still_rejects_global_duplicate(self):
        # Mesma pressão de orçamento (teto legado fixado no contrato), mas o
        # intent aparece em dois shards: o veredito anti-fraude de unicidade
        # global tem de sobreviver ao teto elevado — a falha é a de unicidade,
        # nunca um abort de orçamento que mascararia a cópia oculta.
        changed_raw = self.page_raw("Owner duplicado em dois shards do estoque.")
        self.write_raw(self.target_rel, changed_raw)
        self.write_raw("data/editorial/v2_pages/area-02.jsonl", changed_raw)
        self.write_contract_v3(forward=[self.forward_candidate(changed_raw)])
        self._write_stock_filler(12)
        contract_path = (
            self.root / "data/editorial/v2_writing_semantic_contract.json")
        with mock.patch.object(
                producer,
                "_MAX_WRITING_SEMANTIC_SNAPSHOT_BYTES",
                contract_path.stat().st_size):
            with self.assertRaisesRegex(
                    ValueError, "globalmente exato e único"):
                producer.load_writing_semantic_contract(self.root)

    def test_batch_projection_preserves_nonlexicographic_inventory_order(self):
        contract = producer.WritingSemanticContract(
            "0" * 64,
            frozenset({"intent-a", "intent-c"}),
            {"intent-a": "1" * 64, "intent-c": "2" * 64},
            {}, {}, {}, {}, {}, {}, {}, {}, frozenset(),
        )
        self.assertEqual(
            producer.semantic_blocked_for_batch(
                ["intent-c", "intent-b", "intent-a"], contract),
            ("intent-c", "intent-a"),
        )

    def test_exact_new_reviewed_page_resolves_requirement(self):
        new_page_raw = self.page_raw(
            "Nova página que responde exatamente ao requisito recortado.")
        self.write_raw(self.target_rel, new_page_raw)
        self.write_contract([self.resolution(new_page_raw)])

        contract = producer.load_writing_semantic_contract(self.root)
        self.assertEqual(contract.unresolved_intents, set())
        self.assertEqual(
            set(contract.dependency_sha256),
            {self.portfolio_rel, self.target_rel, self.evidence_rel},
        )
        completion = producer.classify_batch_completion(
            [json.loads(new_page_raw)], [self.intent_id],
            "area-01.jsonl", [],
            semantically_blocked_intents=contract.unresolved_intents)
        self.assertTrue(completion.complete)
        self.assertEqual(completion.reusable_expected, (self.intent_id,))

    def test_relocated_owner_keeps_old_baseline_separate(self):
        superseded_target_rel = self.target_rel
        self.target_rel = "data/editorial/v2_pages/area-02.jsonl"
        self.requirement["target_rel_path"] = self.target_rel
        baseline = self.digest(json.dumps(
            [self.requirement], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            pending = producer.load_writing_semantic_contract(self.root)
            self.assertEqual(pending.unresolved_intents, {self.intent_id})
            self.assertEqual(
                set(pending.dependency_sha256),
                {self.portfolio_rel, self.evidence_rel,
                 superseded_target_rel},
            )
            self.assertEqual(
                pending.absent_dependency_paths, {self.target_rel}
            )

            new_page_raw = self.page_raw(
                "Nova página escrita no owner pinado após a migração."
            )
            self.write_raw(self.target_rel, new_page_raw)
            self.write_contract([self.resolution(new_page_raw)])
            self.write_raw(superseded_target_rel, self.json_raw({
                "intent_id": "outro-intent",
                "sections": [{"heading": "Outro", "text": "Preservado."}],
            }))
            resolved = producer.load_writing_semantic_contract(self.root)
            self.assertEqual(resolved.unresolved_intents, set())
            self.assertEqual(
                set(resolved.dependency_sha256),
                {self.portfolio_rel, self.evidence_rel, self.target_rel,
                 superseded_target_rel},
            )
            self.assertEqual(resolved.absent_dependency_paths, set())

    def test_relocated_present_owner_is_part_of_dependency_epoch(self):
        superseded_target_rel = self.target_rel
        self.target_rel = "data/editorial/v2_pages/area-02.jsonl"
        self.requirement["target_rel_path"] = self.target_rel
        self.write_raw(self.target_rel, self.json_raw({
            "intent_id": "outro-intent",
            "sections": [{"heading": "Outro", "text": "Outra página."}],
        }))
        baseline = self.digest(json.dumps(
            [self.requirement], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            contract = producer.load_writing_semantic_contract(self.root)
        self.assertEqual(
            set(contract.dependency_sha256),
            {self.portfolio_rel, self.evidence_rel, self.target_rel,
             superseded_target_rel},
        )
        self.assertEqual(contract.absent_dependency_paths, set())

    def test_relocated_absent_owner_appearance_breaks_dependency_cas(self):
        self.target_rel = "data/editorial/v2_pages/area-02.jsonl"
        self.requirement["target_rel_path"] = self.target_rel
        baseline = self.digest(json.dumps(
            [self.requirement], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            contract = producer.load_writing_semantic_contract(self.root)
            self.write_raw(self.target_rel, self.json_raw({
                "intent_id": "outro-intent",
                "sections": [{"heading": "Outro", "text": "Outra página."}],
            }))
            with self.assertRaisesRegex(
                    producer.CASMismatch, "dependência ausente"):
                producer.verify_writing_semantic_contract_dependencies(
                    self.root, contract
                )

    def test_relocated_contract_rejects_mutated_live_preimage(self):
        superseded_target_rel = self.target_rel
        self.target_rel = "data/editorial/v2_pages/area-02.jsonl"
        self.requirement["target_rel_path"] = self.target_rel
        baseline = self.digest(json.dumps(
            [self.requirement], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            self.write_raw(superseded_target_rel, self.json_raw({
                "intent_id": "outro-intent",
                "sections": [{"heading": "Outro", "text": "Evolução viva."}],
            }))
            with self.assertRaisesRegex(
                    ValueError, "saiu antes da resolução exata"):
                producer.load_writing_semantic_contract(self.root)

    def test_archived_snapshot_tamper_is_rejected(self):
        archive = self.root / self.evidence_rel
        archive.write_bytes(archive.read_bytes() + b"{}\n")
        with self.assertRaisesRegex(ValueError, "bundle semântico"):
            producer.load_writing_semantic_contract(self.root)

    def test_evidence_kind_cannot_change_sha_semantics(self):
        self.requirement["superseded_evidence_kind"] = (
            "duplicate_supersession_record")
        baseline = self.digest(json.dumps(
            [self.requirement], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            with self.assertRaisesRegex(ValueError, "tipo/path"):
                producer.load_writing_semantic_contract(self.root)

    def test_relocation_projection_is_exact_and_blocks_premature_absence(self):
        raw_a = self.json_raw({"intent_id": "intent-a", "sections": [{}]})
        raw_b = self.json_raw({"intent_id": "intent-b", "sections": [{}]})
        old_target = "data/editorial/v2_pages/area-01.jsonl"
        contract = producer.WritingSemanticContract(
            digest="0" * 64,
            unresolved_intents=frozenset({"intent-a", "intent-b"}),
            requirement_fingerprints={
                "intent-a": "1" * 64, "intent-b": "2" * 64},
            portfolio_rel_paths={"intent-a": "p", "intent-b": "p"},
            target_rel_paths={
                "intent-a": "data/editorial/v2_pages/area-02.jsonl",
                "intent-b": "data/editorial/v2_pages/area-03.jsonl",
            },
            superseded_target_rel_paths={
                "intent-a": old_target, "intent-b": old_target},
            superseded_page_record_sha256={
                "intent-a": self.digest(raw_a),
                "intent-b": self.digest(raw_b),
            },
            evidence_kinds={"intent-a": "k", "intent-b": "k"},
            evidence_rel_paths={"intent-a": "e", "intent-b": "e"},
            evidence_sha256={"intent-a": "3" * 64, "intent-b": "3" * 64},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        removals = producer.semantic_relocation_removals_for_target(
            old_target,
            ((raw_b, json.loads(raw_b)), (raw_a, json.loads(raw_a))),
            contract,
        )
        self.assertEqual(
            [item["intent_id"] for item in removals],
            ["intent-b", "intent-a"],
        )
        with self.assertRaisesRegex(ValueError, "antes da resolução"):
            producer.semantic_relocation_removals_for_target(
                old_target, ((raw_a, json.loads(raw_a)),), contract)
        resolved_b = contract._replace(
            unresolved_intents=frozenset({"intent-a"}))
        self.assertEqual(
            producer.semantic_relocation_removals_for_target(
                old_target, ((raw_a, json.loads(raw_a)),), resolved_b
            )[0]["intent_id"],
            "intent-a",
        )

    def test_relocation_projection_rejects_changed_baseline_bytes(self):
        old_target = "data/editorial/v2_pages/area-01.jsonl"
        raw = self.json_raw({"intent_id": "intent-a", "sections": [{}]})
        contract = producer.WritingSemanticContract(
            "0" * 64, frozenset({"intent-a"}), {"intent-a": "1" * 64},
            {"intent-a": "p"},
            {"intent-a": "data/editorial/v2_pages/area-02.jsonl"},
            {"intent-a": old_target}, {"intent-a": "2" * 64},
            {"intent-a": "k"}, {"intent-a": "e"},
            {"intent-a": "3" * 64}, {}, frozenset(),
        )
        with self.assertRaisesRegex(ValueError, "preimagem arquivada"):
            producer.semantic_relocation_removals_for_target(
                old_target, ((raw, json.loads(raw)),), contract)

    def test_loader_requires_atomic_relocation_resolution_and_old_removal(self):
        old_target = self.target_rel
        new_target = "data/editorial/v2_pages/area-02.jsonl"
        self.target_rel = new_target
        self.requirement["target_rel_path"] = new_target
        baseline = self.digest(json.dumps(
            [self.requirement],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            pending = producer.load_writing_semantic_contract(self.root)
            self.assertEqual(pending.unresolved_intents, {self.intent_id})

            (self.root / old_target).unlink()
            with self.assertRaisesRegex(
                    ValueError, "saiu antes da resolução exata"):
                producer.load_writing_semantic_contract(self.root)
            self.write_raw(old_target, self.old_page_raw)

            new_page_raw = self.page_raw(
                "Nova página que responde ao owner semanticamente recortado.")
            self.write_raw(new_target, new_page_raw)
            self.write_contract([self.resolution(new_page_raw)])
            with self.assertRaisesRegex(
                    ValueError, "resolvida permaneceu no target antigo"):
                producer.load_writing_semantic_contract(self.root)

            self.write_raw(old_target, self.json_raw({
                "intent_id": "outro-intent",
                "sections": [{"heading": "Outro", "text": "Preservado."}],
            }))
            resolved = producer.load_writing_semantic_contract(self.root)
            self.assertEqual(resolved.unresolved_intents, set())

    def test_resolution_cannot_reuse_superseded_page(self):
        self.write_contract([self.resolution(self.old_page_raw)])
        with self.assertRaisesRegex(ValueError, "semanticamente superada"):
            producer.load_writing_semantic_contract(self.root)

    def test_resolution_rejects_trivial_source_object(self):
        invalid_page = json.loads(self.page_raw(
            "Página nova que ainda precisa de proveniência válida."))
        invalid_page["official_sources"] = [{}, {}]
        invalid_raw = self.json_raw(invalid_page)
        self.write_raw(self.target_rel, invalid_raw)
        resolution = self.resolution(self.old_page_raw)
        invalid_sha256 = self.digest(invalid_raw)
        resolution["page_record_sha256"] = invalid_sha256
        resolution["semantic_review_evidence"][
            "page_record_sha256"] = invalid_sha256
        with self.assertRaisesRegex(ValueError, "proveniência inválido"):
            self.write_contract([resolution])
            producer.load_writing_semantic_contract(self.root)

    def test_legacy_missing_source_research_flag_uses_complete_sources(self):
        page = json.loads(self.page_raw("Texto jurídico atualizado."))
        del page["needs_source_research"]
        material = producer._semantic_page_material_evidence(
            page, self.intent_id)
        self.assertEqual(material["contract"], "v2_semantic_page_material_v1")
        page["needs_source_research"] = True
        with self.assertRaisesRegex(ValueError, "pesquisa de fonte"):
            producer._semantic_page_material_evidence(page, self.intent_id)

    def test_resolution_rejects_ambiguous_unicode_and_invalid_url_encoding(self):
        for invalid in ("\ud800", "\ufffd", "\u2028", "\u2029"):
            page = json.loads(self.page_raw("Texto jurídico atualizado."))
            page["opening"] += invalid
            with self.subTest(codepoint=repr(invalid)):
                with self.assertRaisesRegex(ValueError, "texto canônico"):
                    producer._semantic_page_material_evidence(
                        page, self.intent_id)
        self.assertFalse(producer._canonical_official_source_url(
            "https://www.planalto.gov.br/ccivil_03/%FF"))
        for canonical_url in (
                "https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763",
                "https://www.esteri.it/it/servizi-consolari/cittadinanza/",
                "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#art100"):
            with self.subTest(canonical_url=canonical_url):
                self.assertTrue(producer._canonical_official_source_url(
                    canonical_url))
        for noncanonical_url in (
                "https://boe.es/buscar/act.php?id=BOE-A-1889-4763",
                "https://evil.www.boe.es/buscar/act.php?id=BOE-A-1889-4763",
                "https://www.boe.es:443/buscar/act.php?id=BOE-A-1889-4763",
                "https://esteri.it/it/servizi-consolari/cittadinanza/",
                "https://evil.www.esteri.it/it/servizi-consolari/cittadinanza/",
                "https://www.esteri.it:443/it/servizi-consolari/cittadinanza/",
                "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#",
                "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm#%00"):
            with self.subTest(noncanonical_url=noncanonical_url):
                self.assertFalse(producer._canonical_official_source_url(
                    noncanonical_url))

    def test_resolution_rejects_future_and_malformed_source_dates(self):
        """A data da conferência só reprova quando é impossível ou ilegível.

        Este teste provava o contrário: que 31 dias reprovavam. A janela caía
        sozinha — nenhuma edição, nenhum agente, só o calendário — e travava a
        escrita do acervo inteiro. O propósito foi preservado, não removido: o
        que protege o leitor é data que não pode ter acontecido (fabricação) e
        data que não se lê, e as duas continuam reprovando aqui.
        """
        current_date = datetime.date(2026, 7, 16)
        page = json.loads(self.page_raw("Texto jurídico atualizado."))
        with mock.patch.object(
                producer, "_utc_validation_date",
                return_value=current_date):
            for source in page["official_sources"]:
                source["verified_at"] = (
                    current_date - datetime.timedelta(days=30)).isoformat()
            producer._semantic_page_material_evidence(page, self.intent_id)

            # A inversão: a idade que antes reprovava agora passa. 31 dias é o
            # caso exato que travou gloss-benfeitorias em 2026-08-12, e um ano
            # inteiro prova que não sobrou teto nenhum escondido.
            for idade in (31, 365):
                with self.subTest(idade_em_dias=idade):
                    page["official_sources"][0]["verified_at"] = (
                        current_date -
                        datetime.timedelta(days=idade)).isoformat()
                    producer._semantic_page_material_evidence(
                        page, self.intent_id)

            page["official_sources"][0]["verified_at"] = (
                current_date + datetime.timedelta(days=1)).isoformat()
            with self.assertRaisesRegex(ValueError, "futuro"):
                producer._semantic_page_material_evidence(
                    page, self.intent_id)

            # Ilegível reprova nos dois pontos em que pode falhar: a forma
            # (regex) e o calendário (mês 13, dia 45 passam pela regex).
            page["official_sources"][0]["verified_at"] = "2026-07-1"
            with self.assertRaisesRegex(ValueError, "não canônica"):
                producer._semantic_page_material_evidence(
                    page, self.intent_id)

            page["official_sources"][0]["verified_at"] = "2026-13-45"
            with self.assertRaisesRegex(ValueError, "inválida"):
                producer._semantic_page_material_evidence(
                    page, self.intent_id)

    def test_null_superseded_hash_cannot_hide_existing_page(self):
        self.requirement["superseded_page_record_sha256"] = None
        baseline = self.digest(json.dumps(
            [self.requirement], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        with mock.patch.object(
                producer, "_WRITING_SEMANTIC_REQUIREMENTS_SHA256", baseline):
            self.write_contract([])
            with self.assertRaisesRegex(ValueError, "evidência de ausência"):
                producer.load_writing_semantic_contract(self.root)

    def test_staged_verifier_rejects_reuse_and_unchanged_old_bytes(self):
        projection = base64.b64encode(json.dumps({
            "source_overrides": {},
            "strict_source_intents": [],
        }, sort_keys=True, separators=(",", ":")).encode()).decode("ascii")

        def verify(staged_raw, preservation):
            staged = self.root / "staged.jsonl"
            self.write_raw("staged.jsonl", staged_raw)
            encoded_preservation = base64.b64encode(json.dumps(
                preservation, sort_keys=True, separators=(",", ":"),
            ).encode()).decode("ascii")
            return producer.verify_staged_writing_source_resolution(
                self.root,
                staged,
                self.target_rel,
                producer.snapshot_sha256(self.root / self.target_rel),
                self.portfolio_rel,
                producer._sha256(self.portfolio_raw + b"\n"),
                "data/editorial/v2_source_hint_catalog.json",
                producer.snapshot_sha256(
                    self.root / "data/editorial/v2_source_hint_catalog.json"),
                ["familia"], 0, 0, 1, [self.intent_id], projection,
                encoded_preservation,
            )

        old_hash = self.digest(self.old_page_raw)
        with self.assertRaisesRegex(ValueError, "preservação da fila diverge"):
            verify(self.old_page_raw, {
                "reuse": [self.intent_id],
                "preserve_extras": [],
                "preserved_record_sha256": {self.intent_id: old_hash},
                "authenticated_replacement": False,
                "semantic_contract_sha256": producer.snapshot_sha256(
                    self.root /
                    "data/editorial/v2_writing_semantic_contract.json"),
                "semantic_relocation_removals": [],
            })
        empty_preservation = {
            "reuse": [],
            "preserve_extras": [],
            "preserved_record_sha256": {},
            "authenticated_replacement": False,
            "semantic_contract_sha256": producer.snapshot_sha256(
                self.root /
                "data/editorial/v2_writing_semantic_contract.json"),
            "semantic_relocation_removals": [],
        }
        with self.assertRaisesRegex(ValueError, "semanticamente superada"):
            verify(self.old_page_raw, empty_preservation)

        candidate = json.loads(self.page_raw(
            "A nova redação responde ao requisito jurídico recortado."))
        candidate["official_sources"] = [{
            key: source[key] for key in ("name", "url", "anchor_claim")
        } for source in candidate["official_sources"]]
        verify(self.json_raw(candidate), empty_preservation)

    def test_portfolio_recut_drift_invalidates_requirement(self):
        changed_portfolio = self.json_raw({
            "intent_id": self.intent_id,
            "family": "familia",
            "question": "O requisito jurídico mudou outra vez?",
        })
        self.write_raw(self.portfolio_rel, changed_portfolio)
        with self.assertRaisesRegex(ValueError, "stale no portfolio"):
            producer.load_writing_semantic_contract(self.root)

    def test_page_drift_after_resolution_breaks_dependency_cas(self):
        new_page_raw = self.page_raw("Página nova revisada e autenticada.")
        self.write_raw(self.target_rel, new_page_raw)
        self.write_contract([self.resolution(new_page_raw)])
        contract = producer.load_writing_semantic_contract(self.root)

        self.write_raw(
            self.target_rel,
            self.page_raw("Página alterada depois da revisão autenticada."),
        )
        with self.assertRaisesRegex(
                producer.CASMismatch, "dependência do contrato"):
            producer.verify_writing_semantic_contract_dependencies(
                self.root, contract)

    def test_contract_drift_breaks_sidecar_cas(self):
        contract = producer.load_writing_semantic_contract(self.root)
        path = self.root / "data/editorial/v2_writing_semantic_contract.json"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(
                producer.CASMismatch, "contrato semântico de escrita evoluiu"):
            producer.verify_writing_semantic_contract_dependencies(
                self.root, contract)


class RepositoryWritingSemanticContractTest(unittest.TestCase):
    def test_live_contract_authenticates_all_known_recuts(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        contract = producer.load_writing_semantic_contract(root)
        self.assertEqual(len(contract.requirement_fingerprints), 21)
        self.assertLess(len(contract.unresolved_intents), 21)
        self.assertNotIn(
            "imob-garantia-locacao-dupla-vedada",
            contract.unresolved_intents,
        )
        producer.verify_writing_semantic_contract_dependencies(root, contract)


if __name__ == "__main__":
    unittest.main()
