import hashlib
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from tools import verify_v2_writing_queue_closure as closure
from tools.test_writing_raw_recovery_consumer import (
    LIVE_AEREO_18_EXPECTED,
    LIVE_AEREO_18_LINE_SHA256,
    LIVE_AEREO_18_LINES,
    LIVE_AEREO_18_SHA256,
)


class WritingQueueClosureInputSecurityTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write_workflow(self, name: str, payload: bytes) -> pathlib.Path:
        path = self.root / name
        path.write_bytes(payload)
        return path

    def test_static_todo_may_be_empty_at_terminal_closure(self):
        path = self.write_workflow("todo.js", b"const batches = []\n")
        batches, digest = closure._static_batches(
            path, max_bytes=1024, require_nonempty=False)
        self.assertEqual(batches, [])
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_static_inventory_still_requires_at_least_one_batch(self):
        path = self.write_workflow("full.js", b"const batches = []\n")
        with self.assertRaisesRegex(ValueError, "lista não vazia"):
            closure._static_batches(
                path, max_bytes=1024, require_nonempty=True)

    def test_static_json_rejects_duplicate_keys(self):
        path = self.write_workflow(
            "duplicate.js",
            b'const batches = [{"slug":"area-01","slug":"area-02"}]\n',
        )
        with self.assertRaisesRegex(ValueError, "JSON inválido"):
            closure._static_batches(
                path, max_bytes=4096, require_nonempty=True)

    def test_static_json_rejects_casefold_alias_and_nonfinite_number(self):
        cases = {
            "casefold": (
                b'const batches = [{"slug":"area-01",'
                b'"SLUG":"area-02"}]\n'),
            "unicode-simple-fold": (
                b'const batches = [{"key":1,"\xe2\x84\xaaey":2}]\n'),
            "nan": b'const batches = [{"n":NaN}]\n',
            "overflow": b'const batches = [{"n":1e9999}]\n',
        }
        for label, payload in cases.items():
            with self.subTest(label=label):
                path = self.write_workflow(label + ".js", payload)
                with self.assertRaisesRegex(
                        ValueError, "JSON inválido|ambígua|não finito"):
                    closure._static_batches(
                        path, max_bytes=4096, require_nonempty=True)

    def test_static_reader_rejects_oversize_symlink_hardlink_and_fifo(self):
        oversized = self.write_workflow(
            "oversized.js", b"const batches = []\n" + b"x" * 128)
        with self.assertRaisesRegex(ValueError, "excede limite"):
            closure._static_batches(
                oversized, max_bytes=32, require_nonempty=False)

        original = self.write_workflow("original.js", b"const batches = []\n")
        hardlink = self.root / "hardlink.js"
        os.link(original, hardlink)
        with self.assertRaisesRegex(RuntimeError, "hardlink"):
            closure._static_batches(
                hardlink, max_bytes=1024, require_nonempty=False)

        symlink = self.root / "symlink.js"
        symlink.symlink_to(original.name)
        with self.assertRaises(OSError):
            closure._static_batches(
                symlink, max_bytes=1024, require_nonempty=False)

        fifo = self.root / "fifo.js"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(RuntimeError, "arquivo regular"):
            closure._static_batches(
                fifo, max_bytes=1024, require_nonempty=False)

    def test_root_refuses_symlink(self):
        real = self.root / "real"
        real.mkdir()
        linked = self.root / "linked"
        linked.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            closure._canonical_root(linked)

    def test_canonical_closure_refuses_run_scoped_area_waiver(self):
        with self.assertRaisesRegex(ValueError, "não admite exclusão"):
            closure.verify(self.root, ["telecom_energia"])

    def test_batch_schemas_are_closed_and_type_safe(self):
        def oversized_utf8_url(prefix):
            remaining = (
                closure._MAX_OFFICIAL_SOURCE_URL_BYTES -
                len(prefix.encode("utf-8"))
            )
            exact = prefix + "á" * (remaining // 2) + "a" * (remaining % 2)
            self.assertEqual(
                len(exact.encode("utf-8")),
                closure._MAX_OFFICIAL_SOURCE_URL_BYTES,
            )
            return exact + "á"

        digest = "0" * 64
        base = {
            "families": ["familia"],
            "skip": 0,
            "take": 1,
            "n": 1,
            "area": "area",
            "file": "data/editorial/portfolio_v2/area.jsonl",
            "slug": "area-01",
        }
        todo = {
            **base,
            "writer": "redator-juridico",
            "sources": [],
            "source_overrides": {},
            "strict_source_intents": [],
            "source_hint_catalog_sha256": digest,
            "portfolio_sha256": digest,
            "semantic_contract_sha256": digest,
            "preserved_record_sha256": {},
            "target_sha256": digest,
        }
        self.assertEqual(
            closure._validate_todo_batch(todo, "lote"), "area-01")
        candidate = {
            **todo,
            "sources": [{
                "name": "Portal oficial",
                "url": "https://www.planalto.gov.br/",
            }],
        }
        self.assertEqual(
            closure._validate_todo_batch(candidate, "lote"), "area-01")
        unsafe_candidates = (
            {"name": "Portal\ninjetado", "url": "https://www.planalto.gov.br/"},
            {"name": "Atacante", "url": "https://www.planalto.gov.br.evil.test/"},
            {"name": "Traversal", "url": "https://www.planalto.gov.br/a/../b"},
            {"name": "Query sem path", "url": "https://www.planalto.gov.br/?ato=1"},
            {"name": "Porta", "url": "https://www.planalto.gov.br:443/"},
            {
                "name": "Path grande",
                "url": "https://www.planalto.gov.br/" +
                       "a" * (closure._MAX_OFFICIAL_SOURCE_URL_BYTES + 1),
            },
            {
                "name": "Query grande",
                "url": "https://www.planalto.gov.br/ato?id=" +
                       "a" * (closure._MAX_OFFICIAL_SOURCE_URL_BYTES + 1),
            },
            {
                "name": "Path UTF-8 grande",
                "url": oversized_utf8_url(
                    "https://www.planalto.gov.br/ato/"),
            },
            {
                "name": "Query UTF-8 grande",
                "url": oversized_utf8_url(
                    "https://www.planalto.gov.br/ato?id="),
            },
            {
                "name": "Surrogate inválido",
                "url": "https://www.planalto.gov.br/ato/\ud800",
            },
        )
        for source in unsafe_candidates:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "sources inválidas"):
                    closure._validate_todo_batch(
                        {**todo, "sources": [source]}, "lote")
        oversized_exact_urls = (
            "https://www.planalto.gov.br/" +
            "a" * (closure._MAX_OFFICIAL_SOURCE_URL_BYTES + 1),
            "https://www.planalto.gov.br/ato?id=" +
            "a" * (closure._MAX_OFFICIAL_SOURCE_URL_BYTES + 1),
            oversized_utf8_url("https://www.planalto.gov.br/ato/"),
            oversized_utf8_url("https://www.planalto.gov.br/ato?id="),
            "https://www.planalto.gov.br/ato/\ud800",
        )
        for url in oversized_exact_urls:
            with self.subTest(exact_url=url[:64]):
                with self.assertRaisesRegex(
                        ValueError, "resolução exata de fonte inválida"):
                    closure._validate_todo_batch({
                        **todo,
                        "source_overrides": {
                            "intent-a": {
                                "fonte-oficial": {
                                    "name": "Ato oficial",
                                    "url": url,
                                    "anchor_claim": "regra jurídica específica",
                                },
                            },
                        },
                    }, "lote")
        with self.assertRaisesRegex(ValueError, "schema aberto"):
            closure._validate_todo_batch({**todo, "surpresa": True}, "lote")
        with self.assertRaisesRegex(ValueError, "schema aberto"):
            incomplete = dict(todo)
            del incomplete["target_sha256"]
            closure._validate_todo_batch(incomplete, "lote")
        with self.assertRaisesRegex(ValueError, "lote-base"):
            closure._validate_base_batch(
                {**base, "families": [{"não": "hashable"}]}, "lote")
        with self.assertRaisesRegex(ValueError, "lote-base"):
            closure._validate_base_batch(
                {**base, "take": 23, "n": 23}, "lote")
        with self.assertRaisesRegex(ValueError, "lote-base"):
            closure._validate_base_batch(
                {**base,
                 "file": "data/editorial/portfolio_v2/outra.jsonl"},
                "lote")
        # O prefixo de area no slug caiu em 2026-08-30: ele reprovava 29 lotes
        # do inventario integral que tem shard escrito e contagem batendo
        # (`codex-sucessoes-transito-r14` escreve em `transito`,
        # `administrativo-r01` em `servidor`, `sucessoes-r01` em `sucessoes2`).
        # O nome do lote guarda a ORIGEM da campanha; o destino ja vem de
        # `file`. A guarda que de fato impede um lote de reivindicar intent de
        # outro portfolio esta em `_expected_intents`, e e ELA que este caso
        # passa a exercitar — teste movido para a camada certa, nao removido.
        with self.assertRaisesRegex(ValueError, "intent_id pinado fora do portfolio"):
            closure._expected_intents(
                {**base, "take": 0, "n": 1, "intent_ids": ["intent-de-outra-area"]},
                {"familia-a": ["intent-a"]})
        with self.assertRaisesRegex(ValueError, "family do intent_id pinado diverge"):
            closure._expected_intents(
                {**base, "take": 0, "n": 1, "intent_ids": ["intent-b"]},
                {"familia-a": ["intent-a"], "familia-b": ["intent-b"]})
        pinned = {
            **base,
            "take": 0,
            "n": 1,
            "intent_ids": ["intent-a"],
        }
        self.assertEqual(
            closure._validate_base_batch(pinned, "lote"), "area-01")
        for invalid in (
            {key: value for key, value in pinned.items()
             if key != "intent_ids"},
            {**pinned, "intent_ids": []},
            {**pinned, "intent_ids": ["intent-a", "intent-a"], "n": 2},
            {**base, "intent_ids": []},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "lote-base"):
                    closure._validate_base_batch(invalid, "lote")

    def test_expected_pins_require_complete_ordered_family_runs(self):
        by_family = {
            "familia-a": ["intent-a1", "intent-a2"],
            "familia-b": ["intent-b1"],
        }
        base = {
            "slug": "area-01",
            "families": ["familia-a", "familia-b"],
            "skip": 0,
            "take": 0,
            "n": 3,
        }
        valid = {**base, "intent_ids": [
            "intent-a2", "intent-a1", "intent-b1",
        ]}
        self.assertEqual(
            closure._expected_intents(valid, by_family),
            valid["intent_ids"],
        )
        invalid_pins = (
            ["intent-a1", "intent-a2"],
            ["intent-b1", "intent-a1", "intent-a2"],
            ["intent-a1", "intent-b1", "intent-a2"],
        )
        for pins in invalid_pins:
            with self.subTest(pins=pins):
                batch = {**base, "n": len(pins), "intent_ids": pins}
                with self.assertRaisesRegex(ValueError, "families do pin"):
                    closure._expected_intents(batch, by_family)


class WritingQueueClosureProjectionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        for rel in (
            "scripts/workflows",
            "data/editorial/portfolio_v2",
            "data/editorial/v2_pages",
        ):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        self.base = {
            "families": ["familia"], "skip": 0, "take": 2, "n": 2,
            "area": "area",
            "file": "data/editorial/portfolio_v2/area.jsonl",
            "slug": "area-01",
        }
        # ``needs_source_research`` é OBRIGATÓRIO e booleano no portfólio
        # (``generate_v2_review_queue.py:2111``: ``type(...) is not bool``
        # reprova). Sem ele, este fixture morria em "identidade/source_hints
        # não canônicos na linha 1" ANTES de qualquer asserção do caso: o
        # módulo estava VERMELHO em HEAD (2 errors + 1 failure, medido em
        # 2026-09-05) e três casos deixavam de medir o que dizem medir — entre
        # eles o controle de "reuse diverge"
        # (``test_unresolved_semantic_requirement_forces_todo_without_reuse``),
        # que guarda a família inteira de divergência entre produtores de
        # ``reuse``. Vermelho não atendido não é dívida de outra frente quando
        # o caso que ele apaga é o guarda desta.
        self.portfolio = b"".join(self.json_line(record) for record in (
            {"intent_id": "intent-a", "family": "familia", "source_hints": [],
             "needs_source_research": False},
            {"intent_id": "intent-b", "family": "familia", "source_hints": [],
             "needs_source_research": False},
        ))
        self.catalog = self.json_line({
            "_meta": {
                "schema_version": 1,
                "purpose": "teste fechado",
                "source_policy": "fonte oficial específica",
            },
            "strict_intents": [],
            "source_hints": {},
        })
        self.target_lines = [self.json_line({
            "intent_id": "intent-a",
            "sections": [{"heading": "Contexto", "text": "Texto autoral."}],
        })[:-1]]
        (self.root / self.base["file"]).write_bytes(self.portfolio)
        (self.root / "data/editorial/v2_source_hint_catalog.json").write_bytes(
            self.catalog)
        self.write_target(self.target_lines)
        self.write_full()
        self.write_todo(self.valid_todo())

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def json_line(value):
        return (json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")) + "\n").encode("utf-8")

    @staticmethod
    def digest(payload):
        return hashlib.sha256(payload).hexdigest()

    def write_full(self):
        payload = b"const batches = " + json.dumps(
            [self.base], sort_keys=True, separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        (self.root / "scripts/workflows/writing-mass-full.js").write_bytes(payload)

    def write_target(self, raw_lines):
        payload = b"\n".join(raw_lines) + b"\n"
        (self.root / "data/editorial/v2_pages/area-01.jsonl").write_bytes(payload)
        self.target = payload

    def valid_todo(self):
        return {
            **self.base,
            "writer": "redator-juridico",
            "sources": [],
            "source_overrides": {},
            "strict_source_intents": [],
            "source_hint_catalog_sha256": self.digest(self.catalog),
            "portfolio_sha256": self.digest(self.portfolio),
            "semantic_contract_sha256": "0" * 64,
            "reuse": ["intent-a"],
            "preserved_record_sha256": {
                "intent-a": self.digest(self.target_lines[0]),
            },
            "target_sha256": self.digest(self.target),
        }

    def write_todo(self, batch):
        payload = b"const batches = " + json.dumps(
            [batch], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        (self.root / "scripts/workflows/writing-mass-todo.js").write_bytes(payload)

    def verify(self, semantic_contract=None):
        catalog = closure.migrations.MigrationCatalog("0" * 64, {}, {})
        if semantic_contract is None:
            semantic_contract = closure.producer.WritingSemanticContract(
                digest="0" * 64,
                unresolved_intents=frozenset(),
                requirement_fingerprints={},
                portfolio_rel_paths={},
                target_rel_paths={},
                superseded_target_rel_paths={},
                superseded_page_record_sha256={},
                evidence_kinds={},
                evidence_rel_paths={},
                evidence_sha256={},
                dependency_sha256={},
                absent_dependency_paths=frozenset(),
            )
        with (
            mock.patch.object(closure.migrations, "load_catalog",
                              return_value=catalog),
            mock.patch.object(closure.migrations,
                              "_verify_catalog_dependencies"),
            mock.patch.object(
                closure.producer, "load_writing_semantic_contract",
                return_value=semantic_contract),
            mock.patch.object(
                closure.producer,
                "verify_writing_semantic_contract_dependencies"),
            mock.patch.object(
                closure.auditor, "validated_duplicate_supersession_winners",
                return_value=(set(), [])),
        ):
            return closure.verify(self.root)

    # ------------------------------------------------------------------
    # TERCEIRO ESTADO DA FILA (2026-09-10)
    #
    # O produtor emite-clean (2026-07-22, ``2956359d``) o lote cujo
    # ``source_hint`` nao tem resolucao exata: ele NAO entra na fila e cai no
    # manifesto de defeitos. A invariante original deste verificador e de
    # 2026-07-14, oito dias antes, e lia toda omissao como "shard completo".
    # Medido no acervo vivo em 2026-09-10: 86 lotes omitidos-e-incompletos,
    # 85 deles bloqueados por fonte.
    #
    # Os tres casos abaixo sao pareados de proposito: o exemption so vale para
    # o predicado emit-clean do produtor, medido ao vivo, e reprova nos dois
    # lados vizinhos.
    # ------------------------------------------------------------------
    def write_todo_vazia(self):
        (self.root / "scripts/workflows/writing-mass-todo.js").write_bytes(
            b"const batches = []\n")

    def portfolio_com_hint(self, needs_source_research):
        """Portfolio cujo intent-b cita um hint AUSENTE do catalogo."""
        payload = b"".join(self.json_line(record) for record in (
            {"intent_id": "intent-a", "family": "familia", "source_hints": [],
             "needs_source_research": False},
            {"intent_id": "intent-b", "family": "familia",
             "source_hints": ["hint-sem-resolucao"],
             "needs_source_research": needs_source_research},
        ))
        (self.root / self.base["file"]).write_bytes(payload)
        self.portfolio = payload

    def test_lote_omitido_e_incompleto_sem_bloqueio_de_fonte_reprova(self):
        """MUTACAO: sem bloqueio de fonte, a projecao negativa continua mordendo.

        Este e o caso que o exemption NAO pode cobrir. O shard tem 1 das 2
        linhas do slice e todos os hints resolvem (a lista e vazia), logo a
        omissao da fila e uma afirmacao falsa de completude.
        """
        self.write_todo_vazia()
        with self.assertRaisesRegex(
                ValueError, "writing queue não fecha o inventário vivo"):
            self.verify()

    def test_lote_omitido_e_incompleto_bloqueado_por_fonte_e_contado(self):
        """Bloqueio de FONTE justifica a omissao — contado e nomeado, nao sumido."""
        self.portfolio_com_hint(needs_source_research=False)
        self.write_todo_vazia()
        resultado = self.verify()
        self.assertEqual(resultado["source_blocked_batches"], 1)
        self.assertEqual(resultado["completed_batches"], 0)
        self.assertEqual(resultado["queued_batches"], 0)
        # A evidencia nomeia o lote E o motivo do produtor: contagem sozinha
        # nao deixa a divida de curadoria auditavel.
        self.assertEqual(len(resultado["source_blocked_evidence"]), 1)
        self.assertIn("area-01", resultado["source_blocked_evidence"][0])
        self.assertIn(
            "sem resolução exata", resultado["source_blocked_evidence"][0])
        # A aritmetica que o teste Go cobra tem de fechar com o terceiro estado.
        self.assertEqual(
            resultado["queued_batches"] + resultado["completed_batches"] +
            resultado["source_blocked_batches"] +
            resultado["excluded_batches"],
            resultado["full_batches"])

    def test_hint_aberto_com_pesquisa_declarada_pendente_nao_e_exemption(self):
        """Fail-closed: pesquisa ABERTA nao bloqueia o enfileiramento, logo nao excusa.

        Mesmo hint ausente do catalogo, mas com ``needs_source_research=True``
        o produtor NAO recusa o lote — ele seria enfileiravel. Omiti-lo da
        fila continua sendo afirmacao falsa de completude, e o verificador
        precisa continuar vermelho. E o que separa "bloqueado por fonte" de
        "qualquer hint nao resolvido".
        """
        self.portfolio_com_hint(needs_source_research=True)
        self.write_todo_vazia()
        with self.assertRaisesRegex(
                ValueError, "writing queue não fecha o inventário vivo"):
            self.verify()

    def test_unresolved_semantic_requirement_forces_todo_without_reuse(self):
        semantic_contract = closure.producer.WritingSemanticContract(
            digest="1" * 64,
            unresolved_intents=frozenset({"intent-a"}),
            requirement_fingerprints={"intent-a": "2" * 64},
            portfolio_rel_paths={"intent-a": self.base["file"]},
            target_rel_paths={
                "intent-a": "data/editorial/v2_pages/area-01.jsonl"},
            superseded_target_rel_paths={
                "intent-a": "data/editorial/v2_pages/area-01.jsonl"},
            superseded_page_record_sha256={
                "intent-a": self.digest(self.target_lines[0])},
            evidence_kinds={"intent-a": "duplicate_supersession_record"},
            evidence_rel_paths={"intent-a": "evidence"},
            evidence_sha256={"intent-a": "5" * 64},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        stale_reuse = self.valid_todo()
        stale_reuse["semantic_contract_sha256"] = semantic_contract.digest
        self.write_todo(stale_reuse)
        with self.assertRaisesRegex(ValueError, "reuse diverge"):
            self.verify(semantic_contract)

        queued = self.valid_todo()
        queued["semantic_contract_sha256"] = semantic_contract.digest
        queued.pop("reuse")
        queued["preserved_record_sha256"] = {}
        self.write_todo(queued)
        self.assertEqual(
            self.verify(semantic_contract)["queued_batches"], 1)

        complete_lines = self.target_lines + [self.json_line({
            "intent_id": "intent-b",
            "sections": [{"heading": "Passo", "text": "Outro texto."}],
        })[:-1]]
        self.write_target(complete_lines)
        (self.root / "scripts/workflows/writing-mass-todo.js").write_bytes(
            b"const batches = []\n")
        with self.assertRaisesRegex(
                ValueError, "classificador não confirmou lote completo"):
            self.verify(semantic_contract)

    def test_semantic_requirement_must_bind_to_owner_shard(self):
        semantic_contract = closure.producer.WritingSemanticContract(
            digest="3" * 64,
            unresolved_intents=frozenset({"intent-a"}),
            requirement_fingerprints={"intent-a": "4" * 64},
            portfolio_rel_paths={"intent-a": self.base["file"]},
            target_rel_paths={
                "intent-a": "data/editorial/v2_pages/outra-01.jsonl"},
            superseded_target_rel_paths={
                "intent-a": "data/editorial/v2_pages/outra-01.jsonl"},
            superseded_page_record_sha256={
                "intent-a": self.digest(self.target_lines[0])},
            evidence_kinds={"intent-a": "duplicate_supersession_record"},
            evidence_rel_paths={"intent-a": "evidence"},
            evidence_sha256={"intent-a": "5" * 64},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        queued = self.valid_todo()
        queued["semantic_contract_sha256"] = semantic_contract.digest
        self.write_todo(queued)
        with self.assertRaisesRegex(ValueError, "ligado ao shard errado"):
            self.verify(semantic_contract)

    def test_recomputes_sources_preservation_migration_and_completion(self):
        self.assertEqual(self.verify()["queued_batches"], 1)

        mutations = {}
        missing_reuse = self.valid_todo()
        del missing_reuse["reuse"]
        mutations["reuse"] = missing_reuse
        bad_hash = self.valid_todo()
        bad_hash["preserved_record_sha256"]["intent-a"] = "f" * 64
        mutations["preserved_record_sha256"] = bad_hash
        fake_migration = self.valid_todo()
        fake_migration["portfolio_intent_migration"] = None
        mutations["autorização de migração"] = fake_migration
        fake_source = self.valid_todo()
        fake_source["source_overrides"] = {
            "intent-a": {
                "fonte-falsa": {
                    "name": "Fonte oficial irrelevante",
                    "url": "https://www.planalto.gov.br/irrelevante",
                    "anchor_claim": "não pertence à intenção",
                },
            },
        }
        mutations["projeção exata"] = fake_source
        for expected_error, batch in mutations.items():
            with self.subTest(expected_error=expected_error):
                self.write_todo(batch)
                with self.assertRaisesRegex(ValueError, expected_error):
                    self.verify()

        complete_lines = self.target_lines + [self.json_line({
            "intent_id": "intent-b",
            "sections": [{"heading": "Passo", "text": "Outro texto."}],
        })[:-1]]
        self.write_target(complete_lines)
        complete = self.valid_todo()
        complete.pop("reuse")
        complete["preserved_record_sha256"] = {}
        complete["target_sha256"] = self.digest(self.target)
        self.write_todo(complete)
        with self.assertRaisesRegex(ValueError, "já completo"):
            self.verify()

    def test_pinned_inventory_preserves_order_and_todo_identity(self):
        self.base.update({
            "take": 0,
            "intent_ids": ["intent-b", "intent-a"],
        })
        # Apenas intent-a existe no shard, mas a ordem esperada agora começa
        # por intent-b; o pin continua sendo a ordem semântica do lote.
        self.write_full()
        queued = self.valid_todo()
        self.write_todo(queued)
        self.assertEqual(self.verify()["queued_batches"], 1)

        reordered = self.valid_todo()
        reordered["intent_ids"] = ["intent-a", "intent-b"]
        self.write_todo(reordered)
        with self.assertRaisesRegex(ValueError, "campos-base"):
            self.verify()

    def test_pinned_inventory_rejects_reordered_complete_shard(self):
        self.base.update({
            "take": 0,
            "intent_ids": ["intent-b", "intent-a"],
        })
        self.write_full()
        record_a = self.json_line({
            "intent_id": "intent-a",
            "sections": [{"heading": "Contexto", "text": "Texto A."}],
        })[:-1]
        record_b = self.json_line({
            "intent_id": "intent-b",
            "sections": [{"heading": "Contexto", "text": "Texto B."}],
        })[:-1]
        self.write_target([record_a, record_b])
        todo_path = self.root / "scripts/workflows/writing-mass-todo.js"
        todo_path.write_bytes(b"const batches = []\n")
        with self.assertRaisesRegex(
                ValueError, "classificador não confirmou lote completo"):
            self.verify()

        self.write_target([record_b, record_a])
        self.assertEqual(self.verify()["completed_batches"], 1)

    def test_pinned_inventory_rejects_missing_pin_and_family_mismatch(self):
        self.base.update({
            "take": 0,
            "intent_ids": ["intent-a", "intent-inexistente"],
        })
        self.write_full()
        self.write_todo(self.valid_todo())
        with self.assertRaisesRegex(ValueError, "pinado fora do portfolio"):
            self.verify()

        self.base["intent_ids"] = ["intent-a", "intent-b"]
        self.base["families"] = ["familia-outra"]
        self.write_full()
        self.write_todo(self.valid_todo())
        with self.assertRaisesRegex(ValueError, "family.*diverge"):
            self.verify()

    def test_pinned_inventory_requires_pin_in_full_and_todo(self):
        self.base.update({"take": 0})
        self.write_full()
        self.write_todo(self.valid_todo())
        with self.assertRaisesRegex(ValueError, "schema aberto"):
            self.verify()

    def test_rejects_portfolio_intent_without_inventory_owner(self):
        orphan = self.json_line({
            "intent_id": "intent-sem-lote",
            "family": "familia",
            "source_hints": [],
        })
        (self.root / self.base["file"]).write_bytes(self.portfolio + orphan)
        with self.assertRaisesRegex(ValueError, "portfolio sem lote"):
            self.verify()

    def test_evidencia_fecha_as_duas_contas(self):
        """A evidência tem de FECHAR, nas duas dimensões que ela contabiliza.

        Escrita em 2026-09-10, quando o consumidor Go reprovou por exigir
        ``inventory_intents == portfolio_intents`` — igualdade que este
        verificador abandonou em 2026-08-30, ao passar a aceitar "tem dono no
        inventário OU já tem página escrita". As duas medidas nunca voltariam a
        coincidir: hoje são 9.546 contra 11.416, com 1.870 páginas escritas por
        outra rota depois de o inventário ser congelado.

        A saída não é deixar a diferença sem nome — é emiti-la, e é o que
        ``written_outside_inventory_intents`` faz. Este teste cobra as duas
        identidades sobre o fixture, onde os números são conhecidos:

            inventory + written_outside == portfolio
            queued + completed + source_blocked + excluded == full
        """
        # O FIXTURE PRECISA DE UM ORFAO ESCRITO, ou a identidade fecharia por
        # coincidência (0 == 0) e a asserção não mediria nada: com o portfólio
        # inteiro dentro do inventário, qualquer valor constante passaria. Aqui
        # entra uma intenção de portfólio FORA do slice pinado e COM página no
        # shard — exatamente a forma das ondas -w3 e *-derivada-01.
        fora_do_inventario = self.json_line({
            "intent_id": "intent-escrita-fora",
            "family": "outra-familia",
            "source_hints": [],
            "needs_source_research": False,
        })
        # `self.portfolio` tambem muda: `valid_todo` deriva `portfolio_sha256`
        # dele, e a fila carrega esse digest.
        self.portfolio = self.portfolio + fora_do_inventario
        (self.root / self.base["file"]).write_bytes(self.portfolio)
        (self.root / "data/editorial/v2_pages/fora-01.jsonl").write_bytes(
            self.json_line({
                "intent_id": "intent-escrita-fora",
                "sections": [{"heading": "Contexto", "text": "Texto autoral."}],
            }))
        # A fila carrega o digest do portfólio: mudá-lo sem reescrevê-la
        # levanta "portfolio ou catálogo de fontes mudou depois da fila", que é
        # o guarda certo e não o que este caso mede.
        self.write_todo(self.valid_todo())
        evidencia = self.verify()
        self.assertIn("written_outside_inventory_intents", evidencia)
        self.assertEqual(1, evidencia["written_outside_inventory_intents"])
        self.assertEqual(
            evidencia["inventory_intents"] +
            evidencia["written_outside_inventory_intents"],
            evidencia["portfolio_intents"])
        self.assertEqual(
            evidencia["queued_batches"] + evidencia["completed_batches"] +
            evidencia["source_blocked_batches"] +
            evidencia["excluded_batches"],
            evidencia["full_batches"])

    def test_rejects_orphan_portfolio_file(self):
        orphan = self.json_line({
            "intent_id": "intent-sem-lote",
            "family": "familia-orfa",
            "source_hints": [],
        })
        (self.root / "data/editorial/portfolio_v2/orfa.jsonl").write_bytes(
            orphan)
        with self.assertRaisesRegex(ValueError, "portfolio sem lote"):
            self.verify()

    def test_rejects_intent_id_duplicated_across_portfolios(self):
        duplicate = self.json_line({
            "intent_id": "intent-a",
            "family": "outra-familia",
            "source_hints": [],
        })
        (self.root / "data/editorial/portfolio_v2/outra.jsonl").write_bytes(
            duplicate)
        with self.assertRaisesRegex(ValueError, "global duplicado"):
            self.verify()

    def test_rejects_casefold_alias_and_noncanonical_portfolio_ids(self):
        aliased = self.portfolio.replace(
            b'"intent_id":"intent-a"',
            b'"intent_id":"intent-a","INTENT_ID":"intent-b"',
            1,
        )
        (self.root / self.base["file"]).write_bytes(aliased)
        with self.assertRaisesRegex(ValueError, "chave JSON ambígua"):
            self.verify()

        noncanonical = self.portfolio.replace(b"intent-a", b"Intent-A", 1)
        (self.root / self.base["file"]).write_bytes(noncanonical)
        with self.assertRaisesRegex(ValueError, "portfolio não canônico"):
            self.verify()

    def test_rejects_symlinked_portfolio_entry(self):
        linked = self.root / "data/editorial/portfolio_v2/linked.jsonl"
        linked.symlink_to("area.jsonl")
        with self.assertRaises((OSError, RuntimeError)):
            self.verify()

    def test_rejects_portfolio_directory_membership_churn(self):
        original_snapshot_digest = closure._snapshot_digest
        changed = False

        def mutate_then_snapshot(path, *, max_bytes, missing_ok=False):
            nonlocal changed
            if not changed:
                changed = True
                orphan = self.json_line({
                    "intent_id": "intent-chegou-durante-fechamento",
                    "family": "familia-orfa",
                    "source_hints": [],
                })
                (self.root /
                 "data/editorial/portfolio_v2/churn.jsonl").write_bytes(
                    orphan)
            return original_snapshot_digest(
                path, max_bytes=max_bytes, missing_ok=missing_ok)

        with mock.patch.object(
                closure, "_snapshot_digest",
                side_effect=mutate_then_snapshot):
            with self.assertRaisesRegex(
                    ValueError, "conjunto de arquivos de portfólio evoluiu"):
                self.verify()


class WritingQueueTombstoneReuseClosureTest(unittest.TestCase):
    """O verificador continua recusando tombstone em ``reuse`` — bytes vivos.

    Reproduz o lote ``aereo-18`` da fila de 29/08/2026: duas tombstones
    fechadas por fonte não resolvida e uma intenção nunca escrita. A fila
    mandava preservar as tombstones (``reuse`` vindo da rota raw-recovery) e o
    fechamento respondia "reuse diverge da preimagem autenticada" porque o
    classificador nunca as pôs em reuse. Corrigido em 2026-09-05 na fonte
    (``producer.writing_reusable_page``): a fila regenerada sai sem ``reuse``
    e fecha; a forma antiga continua recusada — este é o controle.

    Fixture próprio e completo (portfolio com ``needs_source_research``,
    catálogo, inventário e o shard com os bytes reais), sem herdar o
    scaffolding de ``WritingQueueClosureProjectionTest``. O lote vai SEM
    ``writing_recovery`` de propósito: a divergência nasce na comparação com o
    classificador, e o campo ``writing_recovery`` na fila depende de alteração
    do verificador ainda em índice (outra frente, 2026-09-05).
    """

    BASE = {
        "families": ["pagamento-e-reembolso"], "skip": 0, "take": 3, "n": 3,
        "area": "aereo", "file": "data/editorial/portfolio_v2/aereo.jsonl",
        "slug": "aereo-18",
    }

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        for rel in (
            "scripts/workflows",
            "data/editorial/portfolio_v2",
            "data/editorial/v2_pages",
        ):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        self.portfolio = b"".join(self.json_line({
            "intent_id": intent_id,
            "family": "pagamento-e-reembolso",
            "source_hints": [],
            "needs_source_research": False,
        }) for intent_id in LIVE_AEREO_18_EXPECTED)
        self.catalog = self.json_line({
            "_meta": {
                "schema_version": 1,
                "purpose": "teste fechado",
                "source_policy": "fonte oficial específica",
            },
            "strict_intents": [],
            "source_hints": {},
        })
        self.target = b"\n".join(LIVE_AEREO_18_LINES) + b"\n"
        assert self.digest(self.target) == LIVE_AEREO_18_SHA256
        (self.root / self.BASE["file"]).write_bytes(self.portfolio)
        (self.root / "data/editorial/v2_source_hint_catalog.json").write_bytes(
            self.catalog)
        (self.root / "data/editorial/v2_pages/aereo-18.jsonl").write_bytes(
            self.target)
        (self.root / "scripts/workflows/writing-mass-full.js").write_bytes(
            b"const batches = " + json.dumps(
                [self.BASE], sort_keys=True, separators=(",", ":"),
            ).encode("utf-8") + b"\n")

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def json_line(value):
        return (json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")) + "\n").encode("utf-8")

    @staticmethod
    def digest(payload):
        return hashlib.sha256(payload).hexdigest()

    def todo(self, **overrides):
        batch = {
            **self.BASE,
            "writer": "redator-juridico",
            "sources": [],
            "source_overrides": {},
            "strict_source_intents": [],
            "source_hint_catalog_sha256": self.digest(self.catalog),
            "portfolio_sha256": self.digest(self.portfolio),
            "semantic_contract_sha256": "0" * 64,
            "preserved_record_sha256": {},
            "target_sha256": self.digest(self.target),
        }
        batch.update(overrides)
        return batch

    def write_todo(self, batch):
        (self.root / "scripts/workflows/writing-mass-todo.js").write_bytes(
            b"const batches = " + json.dumps(
                [batch], ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8") + b"\n")

    def verify(self):
        catalog = closure.migrations.MigrationCatalog("0" * 64, {}, {})
        semantic_contract = closure.producer.WritingSemanticContract(
            digest="0" * 64,
            unresolved_intents=frozenset(),
            requirement_fingerprints={},
            portfolio_rel_paths={},
            target_rel_paths={},
            superseded_target_rel_paths={},
            superseded_page_record_sha256={},
            evidence_kinds={},
            evidence_rel_paths={},
            evidence_sha256={},
            dependency_sha256={},
            absent_dependency_paths=frozenset(),
        )
        with (
            mock.patch.object(closure.migrations, "load_catalog",
                              return_value=catalog),
            mock.patch.object(closure.migrations,
                              "_verify_catalog_dependencies"),
            mock.patch.object(
                closure.producer, "load_writing_semantic_contract",
                return_value=semantic_contract),
            mock.patch.object(
                closure.producer,
                "verify_writing_semantic_contract_dependencies"),
            mock.patch.object(
                closure.auditor, "validated_duplicate_supersession_winners",
                return_value=(set(), [])),
        ):
            return closure.verify(self.root)

    def test_live_queue_shape_with_tombstones_in_reuse_is_refused(self):
        # Forma exata da fila de 29/08 (menos ``writing_recovery``): as duas
        # tombstones em ``reuse`` com os hashes reais.
        tombstones = (LIVE_AEREO_18_EXPECTED[0], LIVE_AEREO_18_EXPECTED[2])
        self.write_todo(self.todo(
            reuse=list(tombstones),
            preserved_record_sha256=dict(
                zip(tombstones, LIVE_AEREO_18_LINE_SHA256)),
        ))
        with self.assertRaisesRegex(
                ValueError, "aereo-18: reuse diverge da preimagem autenticada"):
            self.verify()

    def test_tombstone_hash_without_reuse_is_still_refused(self):
        self.write_todo(self.todo(preserved_record_sha256={
            LIVE_AEREO_18_EXPECTED[0]: LIVE_AEREO_18_LINE_SHA256[0]}))
        with self.assertRaisesRegex(
                ValueError, "preserved_record_sha256 diverge dos bytes vivos"):
            self.verify()

    def test_regenerated_queue_without_tombstone_reuse_closes_inventory(self):
        self.write_todo(self.todo())
        result = self.verify()
        self.assertEqual(result["full_batches"], 1)
        self.assertEqual(result["queued_batches"], 1)
        self.assertEqual(result["completed_batches"], 0)
        self.assertEqual(result["inventory_intents"], 3)
        self.assertEqual(result["portfolio_intents"], 3)


if __name__ == "__main__":
    unittest.main()
