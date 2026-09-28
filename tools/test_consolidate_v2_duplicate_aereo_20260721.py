import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools/consolidate_v2_duplicate_aereo_20260721.py"
SPEC = importlib.util.spec_from_file_location(
    "tools.consolidate_v2_duplicate_aereo_20260721", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def archived_source() -> bytes:
    """Preimagem do perdedor: antes da adjudicação é o shard vivo; depois dela,
    as ``original_line`` preservadas no archive (o shard vivo já é tombstone)."""
    if module.ARCHIVE.exists():
        rows = module.canonical_lines(
            module.ARCHIVE.read_bytes(), module.ARCHIVE_REL)
        return ("\n".join(row[1]["original_line"] for row in rows) + "\n"
                ).encode("utf-8")
    return (module.PAGES / module.SOURCE_SHARD).read_bytes()


def encode(records: list[dict]) -> bytes:
    return ("\n".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        for record in records) + "\n").encode("utf-8")


class ConsolidateAereoTest(unittest.TestCase):
    """O vencedor é estoque VIVO e o perdedor é preimagem congelada.

    Até 2026-09-05 a ferramenta pinava o byte do vencedor (CANONICAL_SHA256).
    O reparo de citação 8e49a419 (2026-08-12) reescreveu ``official_sources``
    das duas linhas do vencedor e a adjudicação passou a "divergir" sem nada
    ter divergido. A autenticação espelha agora o gate irmão em Go
    (internal/v2supersessionintegrity): intent única, ativa, na linha que o
    archive registra. Nenhum teste aqui chama ``module.run()`` — ele escreve.
    """

    def setUp(self) -> None:
        self.source = archived_source()
        self.canonical = (module.PAGES / module.CANONICAL_SHARD).read_bytes()
        # json.loads puro: canonical_lines só materializa o nível superior
        # como dict (os objetos aninhados ficam como pares, de propósito).
        self.records = [
            json.loads(line) for line in self.canonical[:-1].split(b"\n")]

    def test_exact_preimages_build_authenticated_private_transition(self):
        tombstones, archive = module.build_artifacts(
            self.source, self.canonical)
        tombstone_rows = module.canonical_lines(tombstones, "tombstones")
        archive_rows = module.canonical_lines(archive, "archive")
        self.assertEqual(2, len(tombstone_rows))
        self.assertEqual(2, len(archive_rows))
        for index, ((_, tombstone), (_, preserved)) in enumerate(
                zip(tombstone_rows, archive_rows), 1):
            self.assertTrue(tombstone["skipped"])
            self.assertEqual("duplicate_intent_consolidated",
                             tombstone["skip_reason"])
            self.assertEqual(module.CANONICAL_SHARD,
                             tombstone["superseded_by"])
            self.assertEqual(tombstone["superseded_record_sha256"],
                             preserved["source_record_sha256"])
            self.assertEqual(index, preserved["source_line"])
            self.assertEqual(index, preserved["canonical_line"])
            self.assertEqual(module.CANONICAL_SHA256,
                             preserved["canonical_shard_sha256"])
            self.assertFalse(preserved["publication_allowed"])
            self.assertEqual("", preserved["public_path"])

    def test_durable_state_on_disk_is_exactly_the_adjudication(self):
        """Controle positivo durável: com o vencedor VIVO de hoje, a
        reconstrução reproduz byte a byte o archive e os tombstones em disco."""
        self.assertTrue(module.ARCHIVE.exists(), module.ARCHIVE)
        tombstones, archive = module.build_artifacts(
            self.source, self.canonical)
        self.assertEqual(archive, module.ARCHIVE.read_bytes())
        self.assertEqual(
            tombstones, (module.PAGES / module.SOURCE_SHARD).read_bytes())

    def test_live_winner_evolves_without_breaking_the_adjudication(self):
        """Simula o reparo de citação: muda ``official_sources`` (campo não
        identitário) do vencedor. O byte sai do pino histórico e a adjudicação
        continua autenticada e reproduz o archive gravado."""
        evolved = []
        for record in self.records:
            record = dict(record)
            record["official_sources"] = [
                dict(source, anchor_claim=(
                    source.get("anchor_claim", "") + " (reparo de citação)"))
                for source in record["official_sources"]]
            evolved.append(record)
        payload = encode(evolved)
        self.assertNotEqual(module.sha256(payload), module.CANONICAL_SHA256)
        tombstones, archive = module.build_artifacts(self.source, payload)
        self.assertEqual(archive, module.ARCHIVE.read_bytes())
        self.assertEqual(
            tombstones, (module.PAGES / module.SOURCE_SHARD).read_bytes())

    def assert_winner_rejected(self, payload: bytes) -> None:
        with self.assertRaisesRegex(ValueError, "vencedor revisado divergiu"):
            module.build_artifacts(self.source, payload)

    def test_wrong_canonical_preimage_fails_closed(self):
        # Framing quebrado nas duas direções: linha vazia a mais e sem o
        # ``\n`` final. Ambos saem sob a mesma mensagem fechada.
        self.assert_winner_rejected(self.canonical + b"\n")
        self.assert_winner_rejected(self.canonical[:-1])

    def test_winner_without_the_adjudicated_invariant_fails_closed(self):
        renamed = [dict(record) for record in self.records]
        renamed[0]["intent_id"] = renamed[0]["intent_id"] + "-renomeada"
        skipped = [dict(record) for record in self.records]
        skipped[1]["skipped"] = True
        duplicated = [dict(record) for record in self.records]
        duplicated[1]["intent_id"] = duplicated[0]["intent_id"]
        reordered = list(reversed(self.records))
        only_one = self.records[:1]
        for label, records in (
                ("intent renomeada", renamed),
                ("registro tombstonado", skipped),
                ("intent duplicada", duplicated),
                ("ordem trocada (canonical_line diverge)", reordered),
                ("intent ausente", only_one)):
            with self.subTest(label):
                self.assert_winner_rejected(encode(records))

    def test_loser_preimage_stays_byte_pinned(self):
        tampered = self.source.replace(b"aer-", b"aer_", 1)
        self.assertNotEqual(tampered, self.source)
        with self.assertRaisesRegex(ValueError, "perdedor divergiu"):
            module.build_artifacts(tampered, self.canonical)


if __name__ == "__main__":
    unittest.main()
