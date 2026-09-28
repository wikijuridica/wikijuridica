import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.audit_v2_pages import body_word_count
from tools.patch_v2_opening_paragraphs import (
    PatchError,
    parse_patch_json,
    patch_file,
    source_identity_sha256,
)


def page(intent_id, opening):
    record = {
        "intent_id": intent_id,
        "title": "Título jurídico",
        "meta_description": "Descrição jurídica útil.",
        "h1": "Título jurídico",
        "opening": opening,
        "sections": [{"heading": "Como agir", "text": "Guarde os documentos."}],
        "faq": [{"q": "O que fazer?", "a": "Confira o contrato."}],
        "official_sources": [{
            "url": "https://example.test/norma",
            "name": "Norma oficial",
            "anchor_claim": "disciplina o caso",
        }],
        "source_hints": ["fonte-a", "fonte-b"],
        "needs_source_research": True,
        "word_count": 0,
    }
    record["word_count"] = body_word_count(record)
    return record


class PatchV2OpeningParagraphsTest(unittest.TestCase):
    def write_shard(self, directory):
        path = Path(directory) / "shard.jsonl"
        records = [page("intent-a", "Abertura A."), page("intent-b", "Abertura B.")]
        path.write_text("".join(
            json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8")
        return path

    def test_atomic_patch_preserves_order_and_recounts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = patch_file(
                path, before, {"intent-b": "Parágrafo jurídico adicional."})

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(["intent-a", "intent-b"], [
                record["intent_id"] for record in records])
            self.assertEqual("Abertura A.", records[0]["opening"])
            self.assertEqual(
                "Abertura B.\n\nParágrafo jurídico adicional.",
                records[1]["opening"])
            self.assertEqual(body_word_count(records[1]), records[1]["word_count"])
            self.assertEqual(["intent-b"], result["changed_intents"])

    def test_source_clause_uses_exact_source_and_preserves_word_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original_word_count = [
                json.loads(line)["word_count"]
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
            result = patch_file(path, before, source_patches={
                "intent-a": {
                    "url": "https://example.test/norma",
                    "clause": "delimita a exceção aplicável",
                },
            })

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "disciplina o caso; delimita a exceção aplicável",
                records[0]["official_sources"][0]["anchor_claim"])
            self.assertEqual(
                original_word_count,
                [record["word_count"] for record in records])
            self.assertEqual(["intent-a"], result["changed_source_intents"])

    def test_append_idempotence_does_not_accept_partial_substrings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = patch_file(
                path,
                before,
                opening_patches={"intent-a": "Abertura"},
                source_patches={
                    "intent-a": {
                        "url": "https://example.test/norma",
                        "clause": "disciplina",
                    },
                },
            )
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "Abertura A.\n\nAbertura", records[0]["opening"])
            self.assertEqual(
                "disciplina o caso; disciplina",
                records[0]["official_sources"][0]["anchor_claim"])
            self.assertEqual(["intent-a"], result["changed_intents"])
            self.assertEqual(["intent-a"], result["changed_source_intents"])

    def test_exact_opening_rewrite_is_field_bound_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original = "Abertura B."
            replacement = "Abertura B revisada.\n\nSegundo parágrafo natural."
            rewrite = {
                "intent-b": {
                    "expected_sha256": hashlib.sha256(
                        original.encode("utf-8")).hexdigest(),
                    "replacement": replacement,
                },
            }
            result = patch_file(
                path, before, opening_rewrites=rewrite)

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(replacement, records[1]["opening"])
            self.assertEqual(body_word_count(records[1]), records[1]["word_count"])
            self.assertEqual(
                ["intent-b"], result["rewritten_opening_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(
                path, current, opening_rewrites=rewrite)
            self.assertEqual(
                ["intent-b"], second["already_rewritten_opening_intents"])
            self.assertEqual(current, second["output_sha256"])

    def test_stale_opening_field_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "opening stale"):
                patch_file(path, digest, opening_rewrites={
                    "intent-a": {
                        "expected_sha256": "0" * 64,
                        "replacement": "Abertura segura.",
                    },
                })
            self.assertEqual(before, path.read_bytes())

    def test_exact_faq_rewrite_is_question_bound_recounted_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original = "Confira o contrato."
            replacement = (
                "Confira o contrato e preserve o protocolo do atendimento.")
            rewrite = {
                "intent-a": {
                    "question": "O que fazer?",
                    "expected_sha256": hashlib.sha256(
                        original.encode("utf-8")).hexdigest(),
                    "replacement": replacement,
                },
            }
            result = patch_file(
                path, before, faq_rewrites=rewrite)

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(replacement, records[0]["faq"][0]["a"])
            self.assertEqual(body_word_count(records[0]), records[0]["word_count"])
            self.assertEqual(["intent-a"], result["rewritten_faq_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(path, current, faq_rewrites=rewrite)
            self.assertEqual(
                ["intent-a"], second["already_rewritten_faq_intents"])
            self.assertEqual(current, second["output_sha256"])

    def test_stale_faq_answer_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "FAQ stale"):
                patch_file(path, digest, faq_rewrites={
                    "intent-a": {
                        "question": "O que fazer?",
                        "expected_sha256": "0" * 64,
                        "replacement": "Guarde o protocolo.",
                    },
                })
            self.assertEqual(before, path.read_bytes())

    def test_exact_source_rewrite_and_source_addition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = patch_file(
                path,
                before,
                source_rewrites={
                    "intent-a": {
                        "url": "https://example.test/norma",
                        "expected_sha256": hashlib.sha256(
                            b"disciplina o caso").hexdigest(),
                        "replacement": "disciplina o caso sem repetição",
                    },
                },
                source_additions={
                    "intent-b": {
                        "url": "https://example.test/lei",
                        "name": "Lei oficial",
                        "anchor_claim": "protege informação adequada",
                    },
                })

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "disciplina o caso sem repetição",
                records[0]["official_sources"][0]["anchor_claim"])
            added = records[1]["official_sources"][1]
            self.assertEqual(
                {"url", "name", "anchor_claim"}, set(added))
            self.assertNotIn("verified_at", added)
            self.assertEqual(
                ["intent-a"], result["rewritten_source_intents"])
            self.assertEqual(
                ["intent-b"], result["added_source_intents"])

    def test_source_addition_rejects_existing_url_with_other_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "colide com URL existente"):
                patch_file(path, digest, source_additions={
                    "intent-a": {
                        "url": "https://example.test/norma",
                        "name": "Outro nome",
                        "anchor_claim": "outro fundamento",
                    },
                })
            self.assertEqual(before, path.read_bytes())

    def test_source_identity_rewrite_is_cas_idempotent_and_drops_stale_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            source = records[0]["official_sources"][0]
            source["verified_at"] = "2026-07-12"
            source["http_status"] = 200
            path.write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records), encoding="utf-8")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            patch = {
                "intent-a": {
                    "url": "https://example.test/norma",
                    "expected_sha256": source_identity_sha256(source),
                    "replacement": {
                        "url": "https://example.test/norma-atual",
                        "name": "Norma oficial atual",
                        "anchor_claim": "disciplina o caso atual",
                    },
                },
            }
            result = patch_file(
                path, before, source_identity_rewrites=patch)
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                patch["intent-a"]["replacement"],
                records[0]["official_sources"][0])
            self.assertEqual(
                ["intent-a"], result["rewritten_source_identity_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(
                path, current, source_identity_rewrites=patch)
            self.assertEqual(
                ["intent-a"],
                second["already_rewritten_source_identity_intents"])
            self.assertEqual(current, second["output_sha256"])

            records[0]["official_sources"][0]["verified_at"] = "2026-07-13"
            records[0]["official_sources"][0]["http_status"] = 206
            path.write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records), encoding="utf-8")
            enriched = hashlib.sha256(path.read_bytes()).hexdigest()
            third = patch_file(
                path, enriched, source_identity_rewrites=patch)
            self.assertEqual(
                ["intent-a"],
                third["already_rewritten_source_identity_intents"])
            enriched_records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "2026-07-13",
                enriched_records[0]["official_sources"][0]["verified_at"])
            self.assertEqual(206, enriched_records[0]["official_sources"][0]["http_status"])

    def test_source_identity_rewrite_rejects_stale_or_colliding_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            replacement = {
                "url": "https://example.test/norma-atual",
                "name": "Norma oficial atual",
                "anchor_claim": "disciplina o caso atual",
            }
            with self.assertRaisesRegex(PatchError, "fonte stale"):
                patch_file(path, digest, source_identity_rewrites={
                    "intent-a": {
                        "url": "https://example.test/norma",
                        "expected_sha256": "0" * 64,
                        "replacement": replacement,
                    },
                })
            self.assertEqual(before, path.read_bytes())

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            records[0]["official_sources"].append(dict(replacement))
            path.write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records), encoding="utf-8")
            collision = path.read_bytes()
            collision_digest = hashlib.sha256(collision).hexdigest()
            current = records[0]["official_sources"][0]
            with self.assertRaisesRegex(PatchError, "colide com URL existente"):
                patch_file(path, collision_digest, source_identity_rewrites={
                    "intent-a": {
                        "url": "https://example.test/norma",
                        "expected_sha256": source_identity_sha256(current),
                        "replacement": replacement,
                    },
                })
            self.assertEqual(collision, path.read_bytes())

    def test_source_identity_rewrite_rejects_ambiguous_combination(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            source = page("unused", "unused")["official_sources"][0]
            with self.assertRaisesRegex(PatchError, "conflita com source_rewrites"):
                patch_file(
                    path,
                    digest,
                    source_rewrites={
                        "intent-a": {
                            "url": source["url"],
                            "expected_sha256": hashlib.sha256(
                                source["anchor_claim"].encode("utf-8")).hexdigest(),
                            "replacement": "outro anchor",
                        },
                    },
                    source_identity_rewrites={
                        "intent-a": {
                            "url": source["url"],
                            "expected_sha256": source_identity_sha256(source),
                            "replacement": {
                                "url": "https://example.test/norma-atual",
                                "name": "Norma oficial atual",
                                "anchor_claim": "disciplina o caso atual",
                            },
                        },
                    })
            self.assertEqual(before, path.read_bytes())

    def test_source_identity_hash_is_canonical_and_field_complete(self):
        source_a = {
            "url": "https://example.test/norma",
            "name": "Norma oficial",
            "anchor_claim": "disciplina o caso",
        }
        source_b = {
            "anchor_claim": "disciplina o caso",
            "url": "https://example.test/norma",
            "name": "Norma oficial",
        }
        oracle = hashlib.sha256(
            b'{"anchor_claim":"disciplina o caso","name":"Norma oficial",'
            b'"url":"https://example.test/norma"}').hexdigest()
        self.assertEqual(oracle, source_identity_sha256(source_a))
        self.assertEqual(oracle, source_identity_sha256(source_b))
        source_b["http_status"] = 200
        self.assertNotEqual(oracle, source_identity_sha256(source_b))

    def test_patch_json_rejects_intent_collision_after_trim(self):
        raw = json.dumps({
            "intent-a": "Parágrafo A.",
            " intent-a ": "Parágrafo B.",
        }, ensure_ascii=False)
        with self.assertRaisesRegex(PatchError, "repetido após normalização"):
            parse_patch_json(raw)

    def test_exact_source_hints_rewrite_is_field_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            current = ["fonte-a", "fonte-b"]
            replacement = ["fonte-a", "lgt-art-3", "lgt-art-5"]
            result = patch_file(path, before, source_hint_rewrites={
                "intent-a": {
                    "expected_sha256": hashlib.sha256(json.dumps(
                        current, ensure_ascii=False,
                        separators=(",", ":")).encode("utf-8")).hexdigest(),
                    "replacement": replacement,
                },
            })

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(replacement, records[0]["source_hints"])
            self.assertEqual(
                ["intent-a"], result["rewritten_source_hint_intents"])

    def test_stale_source_hints_field_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "source_hints stale"):
                patch_file(path, digest, source_hint_rewrites={
                    "intent-a": {
                        "expected_sha256": "0" * 64,
                        "replacement": ["lgt-art-3"],
                    },
                })
            self.assertEqual(before, path.read_bytes())

    def test_exact_section_rewrite_recounts_body(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original = "Guarde os documentos."
            replacement = "Guarde os documentos e confira o protocolo."
            result = patch_file(path, before, section_rewrites={
                "intent-a": {
                    "heading": "Como agir",
                    "expected_sha256": hashlib.sha256(
                        original.encode("utf-8")).hexdigest(),
                    "replacement": replacement,
                },
            })

            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(replacement, records[0]["sections"][0]["text"])
            self.assertEqual(body_word_count(records[0]), records[0]["word_count"])
            self.assertEqual(
                ["intent-a"], result["rewritten_section_intents"])

    def test_section_heading_and_body_rewrite_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original = "Guarde os documentos."
            patch = {
                "intent-a": {
                    "heading": "Como agir",
                    "expected_sha256": hashlib.sha256(
                        original.encode("utf-8")).hexdigest(),
                    "replacement": "Organize a prova da falha concreta.",
                    "replacement_heading": "Como demonstrar a falha",
                },
            }
            result = patch_file(path, before, section_rewrites=patch)
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "Como demonstrar a falha", records[0]["sections"][0]["heading"])
            self.assertEqual(
                "Organize a prova da falha concreta.",
                records[0]["sections"][0]["text"])
            self.assertEqual(
                ["intent-a"], result["rewritten_section_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(path, current, section_rewrites=patch)
            self.assertEqual(
                ["intent-a"], second["already_rewritten_section_intents"])
            self.assertEqual(current, second["output_sha256"])

    def test_heading_only_rewrite_recounts_and_rejects_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original_body = "Guarde os documentos."
            result = patch_file(path, before, section_rewrites={
                "intent-a": {
                    "heading": "Como agir",
                    "expected_sha256": hashlib.sha256(
                        original_body.encode("utf-8")).hexdigest(),
                    "replacement": original_body,
                    "replacement_heading": "Como reunir documentos úteis",
                },
            })
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "Como reunir documentos úteis",
                records[0]["sections"][0]["heading"])
            self.assertEqual(body_word_count(records[0]), records[0]["word_count"])
            self.assertEqual(
                ["intent-a"], result["rewritten_section_intents"])

            records[1]["sections"].append({
                "heading": "Heading ocupado",
                "text": "Outro conteúdo.",
            })
            path.write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records), encoding="utf-8")
            collision_bytes = path.read_bytes()
            collision_digest = hashlib.sha256(collision_bytes).hexdigest()
            with self.assertRaisesRegex(PatchError, "já existe"):
                patch_file(path, collision_digest, section_rewrites={
                    "intent-b": {
                        "heading": "Como agir",
                        "expected_sha256": hashlib.sha256(
                            original_body.encode("utf-8")).hexdigest(),
                        "replacement": "Conteúdo revisado.",
                        "replacement_heading": "Heading ocupado",
                    },
                })
            self.assertEqual(collision_bytes, path.read_bytes())

            with self.assertRaisesRegex(PatchError, "não multilinha"):
                patch_file(path, collision_digest, section_rewrites={
                    "intent-b": {
                        "heading": "Como agir",
                        "expected_sha256": hashlib.sha256(
                            original_body.encode("utf-8")).hexdigest(),
                        "replacement": "Conteúdo revisado.",
                        "replacement_heading": "Heading\nquebrado",
                    },
                })
            self.assertEqual(collision_bytes, path.read_bytes())

    def test_multiple_safe_scalar_rewrites_are_field_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            original_word_count = json.loads(
                path.read_text(encoding="utf-8").splitlines()[0]
            )["word_count"]
            patches = {
                "intent-a": [
                    {
                        "field": "h1",
                        "expected_sha256": hashlib.sha256(
                            "Título jurídico".encode("utf-8")).hexdigest(),
                        "replacement": "Quando a regra jurídica se aplica",
                    },
                    {
                        "field": "meta_description",
                        "expected_sha256": hashlib.sha256(
                            "Descrição jurídica útil.".encode("utf-8")).hexdigest(),
                        "replacement": "Entenda quando a regra se aplica e como agir.",
                    },
                ],
            }
            result = patch_file(path, before, scalar_rewrites=patches)
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(
                "Quando a regra jurídica se aplica", records[0]["h1"])
            self.assertEqual(
                "Entenda quando a regra se aplica e como agir.",
                records[0]["meta_description"])
            self.assertEqual(original_word_count, records[0]["word_count"])
            self.assertEqual(
                ["intent-a"], result["rewritten_scalar_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(path, current, scalar_rewrites=patches)
            self.assertEqual(
                ["intent-a"], second["already_rewritten_scalar_intents"])

    def test_scalar_rewrite_rejects_protected_field_and_stale_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "campo escalar protegido"):
                patch_file(path, digest, scalar_rewrites={
                    "intent-a": [{
                        "field": "intent_id",
                        "expected_sha256": hashlib.sha256(
                            b"intent-a").hexdigest(),
                        "replacement": "intent-z",
                    }],
                })
            self.assertEqual(before, path.read_bytes())

    def test_boolean_scalar_rewrite_is_cas_bound_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            patches = {
                "intent-a": [{
                    "field": "needs_source_research",
                    "expected_sha256": hashlib.sha256(b"true").hexdigest(),
                    "replacement": False,
                }],
            }
            result = patch_file(path, before, scalar_rewrites=patches)
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertIs(records[0]["needs_source_research"], False)
            self.assertEqual(
                ["intent-a"], result["rewritten_scalar_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(path, current, scalar_rewrites=patches)
            self.assertEqual(
                ["intent-a"], second["already_rewritten_scalar_intents"])
            self.assertEqual(current, second["output_sha256"])

    def test_optional_source_research_note_can_be_removed_with_cas(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            note = "Falta conferir a fonte específica."
            records[0]["source_research_note"] = note
            path.write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records), encoding="utf-8")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            patches = {
                "intent-a": [{
                    "field": "source_research_note",
                    "expected_sha256": hashlib.sha256(
                        note.encode("utf-8")).hexdigest(),
                    "replacement": None,
                }],
            }

            result = patch_file(path, before, scalar_rewrites=patches)
            current_records = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertNotIn("source_research_note", current_records[0])
            self.assertEqual(
                ["intent-a"], result["rewritten_scalar_intents"])

            current = hashlib.sha256(path.read_bytes()).hexdigest()
            second = patch_file(path, current, scalar_rewrites=patches)
            self.assertEqual(
                ["intent-a"], second["already_rewritten_scalar_intents"])
            self.assertEqual(current, second["output_sha256"])

    def test_boolean_scalar_rewrite_rejects_text_and_stale_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "deve ser booleano"):
                parse_patch_json(json.dumps({
                    "intent-a": [{
                        "field": "needs_source_research",
                        "expected_sha256": hashlib.sha256(b"true").hexdigest(),
                        "replacement": "false",
                    }],
                }), value_kind="scalar_rewrite")
            with self.assertRaisesRegex(PatchError, "needs_source_research stale"):
                patch_file(path, digest, scalar_rewrites={
                    "intent-a": [{
                        "field": "needs_source_research",
                        "expected_sha256": "0" * 64,
                        "replacement": False,
                    }],
                })
            self.assertEqual(before, path.read_bytes())

    def test_scalar_multi_field_stale_is_atomic_and_shape_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "h1 stale"):
                patch_file(path, digest, scalar_rewrites={
                    "intent-a": [
                        {
                            "field": "title",
                            "expected_sha256": hashlib.sha256(
                                "Título jurídico".encode("utf-8")).hexdigest(),
                            "replacement": "Título já mutado em memória",
                        },
                        {
                            "field": "h1",
                            "expected_sha256": "0" * 64,
                            "replacement": "H1 inválido por CAS",
                        },
                    ],
                })
            self.assertEqual(before, path.read_bytes())

            with self.assertRaisesRegex(PatchError, "exige field"):
                patch_file(path, digest, scalar_rewrites={
                    "intent-a": [{
                        "field": "h1",
                        "replacement": "Sem hash",
                    }],
                })
            self.assertEqual(before, path.read_bytes())

            with self.assertRaisesRegex(PatchError, "não multilinha"):
                patch_file(path, digest, scalar_rewrites={
                    "intent-a": [{
                        "field": "h1",
                        "expected_sha256": hashlib.sha256(
                            "Título jurídico".encode("utf-8")).hexdigest(),
                        "replacement": "Título\nquebrado",
                    }],
                })
            self.assertEqual(before, path.read_bytes())

            with self.assertRaisesRegex(PatchError, "h1 stale"):
                patch_file(path, digest, scalar_rewrites={
                    "intent-a": [{
                        "field": "h1",
                        "expected_sha256": "0" * 64,
                        "replacement": "Outro título",
                    }],
                })
            self.assertEqual(before, path.read_bytes())

    def test_stale_snapshot_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            with self.assertRaisesRegex(PatchError, "snapshot stale"):
                patch_file(path, "0" * 64, {"intent-a": "Outro parágrafo."})
            self.assertEqual(before, path.read_bytes())

    def test_missing_or_duplicate_intent_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_shard(directory)
            before = path.read_bytes()
            digest = hashlib.sha256(before).hexdigest()
            with self.assertRaisesRegex(PatchError, "intent_id ausente"):
                patch_file(path, digest, {"intent-c": "Parágrafo."})
            self.assertEqual(before, path.read_bytes())

            duplicate = page("intent-a", "Outra abertura.")
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(duplicate, ensure_ascii=False) + "\n")
            duplicate_bytes = path.read_bytes()
            duplicate_digest = hashlib.sha256(duplicate_bytes).hexdigest()
            with self.assertRaisesRegex(PatchError, "intent_id duplicado"):
                patch_file(path, duplicate_digest, {"intent-a": "Parágrafo."})
            self.assertEqual(duplicate_bytes, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
