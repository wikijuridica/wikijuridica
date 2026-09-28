#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools.audit_v2_pages import body_word_count
from tools import recount_v2_page_word_counts as recounter


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "recount_v2_page_word_counts.py"


def page(intent_id, word_count=-1):
    return {
        "intent_id": intent_id,
        "opening": "Prazo—fatal e valor_composto contam como palavras separadas.",
        "sections": [{
            "heading": "Art. 10 e a prova",
            "text": "Documento útil demonstra o fato; recibo também ajuda.",
        }],
        "faq": [{"q": "Qual é o prazo?", "a": "Depende do termo inicial."}],
        "word_count": word_count,
    }


class RecountV2PageWordCountsTest(unittest.TestCase):
    def run_tool(self, *arguments):
        return subprocess.run(
            [sys.executable, str(TOOL), *map(str, arguments)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_check_is_read_only_and_write_uses_auditor_formula(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "p01.json"
            original_page = page("teste-contagem")
            path.write_text(
                json.dumps(original_page, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            before = path.read_bytes()

            checked = self.run_tool(path)
            self.assertEqual(1, checked.returncode, checked.stderr)
            self.assertEqual(before, path.read_bytes())
            self.assertEqual(1, json.loads(checked.stdout)["mismatches"])

            written = self.run_tool("--write", path)
            self.assertEqual(0, written.returncode, written.stderr)
            updated = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(body_word_count(updated), updated["word_count"])

            coherent = self.run_tool("--check", path)
            self.assertEqual(0, coherent.returncode, coherent.stderr)
            self.assertEqual(0, json.loads(coherent.stdout)["mismatches"])

    def test_jsonl_updates_pages_and_preserves_tombstones(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lote.jsonl"
            records = [
                page("pagina-um", None),
                {"intent_id": "sem-fonte", "skipped": True,
                 "skip_reason": "fonte oficial indisponível"},
                page("pagina-dois", True),
            ]
            path.write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records
            ), encoding="utf-8")

            result = self.run_tool("--write", path)
            self.assertEqual(0, result.returncode, result.stderr)
            updated = [json.loads(line) for line in path.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(body_word_count(updated[0]), updated[0]["word_count"])
            self.assertNotIn("word_count", updated[1])
            self.assertEqual(body_word_count(updated[2]), updated[2]["word_count"])
            report = json.loads(result.stdout)
            self.assertEqual(2, report["mismatches"])
            self.assertEqual(1, report["files"][0]["skipped"])

    def test_malformed_jsonl_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quebrado.jsonl"
            path.write_text(
                json.dumps(page("valida"), ensure_ascii=False) + "\n{" + "\n",
                encoding="utf-8",
            )
            before = path.read_bytes()
            result = self.run_tool("--write", path)
            self.assertEqual(2, result.returncode)
            self.assertEqual(before, path.read_bytes())
            self.assertFalse(json.loads(result.stdout)["ok"])

    def test_duplicate_json_key_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicado.jsonl"
            path.write_text(
                '{"intent_id":"primeiro","intent_id":"segundo",'
                '"opening":"Texto","sections":[],"faq":[],"word_count":1}\n',
                encoding="utf-8",
            )
            before = path.read_bytes()

            with self.assertRaisesRegex(
                    recounter.RecountError,
                    "chave JSON duplicada: intent_id"):
                recounter.load_document(path)
            self.assertEqual(before, path.read_bytes())

    def test_invalid_page_shape_is_rejected_before_any_batch_write(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "primeiro.jsonl"
            second = Path(directory) / "segundo.jsonl"
            first.write_text(
                json.dumps(page("primeira"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            second.write_text(json.dumps({
                "intent_id": "estrutura-quebrada",
                "opening": "Texto",
                "sections": ["nao e objeto"],
                "word_count": -1,
            }, ensure_ascii=False) + "\n", encoding="utf-8")
            before_first = first.read_bytes()
            before_second = second.read_bytes()

            result = self.run_tool("--write", first, second)
            self.assertEqual(2, result.returncode)
            self.assertEqual(before_first, first.read_bytes())
            self.assertEqual(before_second, second.read_bytes())

    def test_atomic_replace_refuses_a_concurrent_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pagina.json"
            path.write_text(
                json.dumps(page("concorrente"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            document = recounter.load_document(path)
            recounter.recount_document(document)
            concurrent = b'{"intent_id":"evolucao-concorrente"}\n'
            path.write_bytes(concurrent)

            with self.assertRaises(recounter.RecountError):
                recounter.atomic_replace_if_unchanged(
                    document, recounter.serialize_document(document))
            self.assertEqual(concurrent, path.read_bytes())

    def test_atomic_replace_rejects_change_at_exchange_window(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "janela-cas.json"
            path.write_text(
                json.dumps(page("janela-cas"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            document = recounter.load_document(path)
            recounter.recount_document(document)
            concurrent = b'{"intent_id":"evolucao-na-janela-cas"}\n'
            real_renameat2 = recounter.safe_cas._renameat2
            injected = False

            def racing_renameat2(
                    old_dir_fd, old_name, new_dir_fd, new_name, flags):
                nonlocal injected
                if (flags == recounter.safe_cas._RENAME_EXCHANGE and
                        not injected):
                    injected = True
                    path.write_bytes(concurrent)
                return real_renameat2(
                    old_dir_fd, old_name, new_dir_fd, new_name, flags)

            with mock.patch.object(
                    recounter.safe_cas, "_renameat2", racing_renameat2):
                with self.assertRaisesRegex(
                        recounter.RecountError, "CAS seguro recusou"):
                    recounter.atomic_replace_if_unchanged(
                        document, recounter.serialize_document(document))

            self.assertTrue(injected, "o teste não alcançou RENAME_EXCHANGE")
            self.assertEqual(
                concurrent, path.read_bytes(),
                "a evolução concorrente deve voltar ao path canônico")

    def test_tracked_workflows_use_the_canonical_recounter(self):
        workflows = [
            ROOT / "scripts/workflows/writing-mass.js",
            ROOT / "scripts/workflows/writing-mass-todo.js",
            ROOT / "scripts/workflows/writing-review.js",
            ROOT / "scripts/workflows/writing-review-todo.js",
        ]
        for path in workflows:
            text = path.read_text(encoding="utf-8")
            self.assertIn("recount_v2_page_word_counts.py", text, path)
            self.assertNotIn("Formula exata do gate: words = len(", text, path)
            self.assertNotIn("recompute word_count com a formula do gate: len(", text, path)


if __name__ == "__main__":
    unittest.main()
