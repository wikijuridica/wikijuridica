import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import time
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_NAMES = (
    "check-coord-inbox",
    "check-coord-status",
    "check-load-headroom",
    "generate-coord-message",
    "generate-coord-presence",
)


class CoordinationSafeIOTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.tools = self.root / "tools"
        self.coord = self.root / ".agents" / "runtime" / "coordination"
        self.presence = self.coord / "presence"
        self.tools.mkdir(parents=True)
        self.presence.mkdir(parents=True)
        for name in SCRIPT_NAMES:
            shutil.copy2(REPO_ROOT / "tools" / name, self.tools / name)

    def tearDown(self):
        self.temporary.cleanup()

    def run_tool(self, name, *arguments, timeout=8):
        return subprocess.run(
            [str(self.tools / name), *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )

    def post(self, body="corpo"):
        return self.run_tool(
            "generate-coord-message",
            "--from", "codex-safe-pts1",
            "--to", "claude-maestro-pts2",
            "--subject", "assunto",
            "--body", body,
        )

    def presence_update(self, front="frente um"):
        return self.run_tool(
            "generate-coord-presence",
            "--agent", "codex-safe-pts1",
            "--front", front,
            "--heavy", "none",
            "--pane", "%1",
            "--pid", "1234",
            "--tty", "pts/1",
        )

    def test_message_append_and_bounded_inbox_round_trip(self):
        bus = self.coord / "bus.jsonl"
        original = (
            '{"ts":"2026-07-14T00:00:00-03:00","from":"prior","to":"all",'
            '"priority":"normal","subject":"prévio","body":"preservar"}\n'
        ).encode()
        bus.write_bytes(original)
        result = self.post("evolução material")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(bus.read_bytes().startswith(original))
        records = [json.loads(line) for line in bus.read_text().splitlines()]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["body"], "evolução material")
        self.assertEqual(os.stat(bus).st_nlink, 1)

        inbox = self.run_tool(
            "check-coord-inbox",
            "--agent", "claude-maestro-pts2",
            "--last", "1",
        )
        self.assertEqual(inbox.returncode, 0, inbox.stderr)
        self.assertIn("evolução material", inbox.stdout)
        too_many = self.run_tool(
            "check-coord-inbox",
            "--agent", "claude-maestro-pts2",
            "--last", "101",
        )
        self.assertEqual(too_many.returncode, 2)
        self.assertIn("entre 1 e 100", too_many.stderr)

    def test_message_rotates_bus_before_the_cap_without_losing_any_message(self):
        # Sem rotação, chegar ao teto tira PERMANENTEMENTE de todo agente a
        # capacidade de postar. A rotação tem de preservar TODA mensagem
        # (arquivo morto + cauda) e nunca partir um JSON ao meio.
        bus = self.coord / "bus.jsonl"
        archive = self.coord / "bus-archive.jsonl"
        line_template = (
            '{{"ts":"2026-07-14T00:00:00-03:00","from":"prior","to":"all",'
            '"priority":"normal","subject":"prévio","body":"mensagem {index} '
            'com corpo suficientemente longo para encher o bus rápido"}}\n'
        )
        lines = []
        total = 0
        index = 0
        while total <= 6 * 1024 * 1024:
            encoded = line_template.format(index=index).encode("utf-8")
            lines.append(encoded)
            total += len(encoded)
            index += 1
        bus.write_bytes(b"".join(lines))
        before_size = bus.stat().st_size
        self.assertGreater(before_size, 6 * 1024 * 1024)

        result = self.post("mensagem após rotação")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bus rotacionado", result.stderr)

        after_size = bus.stat().st_size
        self.assertLess(after_size, 6 * 1024 * 1024)
        self.assertTrue(archive.exists(), "prefixo antigo tem de ser arquivado, nunca apagado")
        self.assertEqual(os.stat(bus).st_nlink, 1)

        archived = archive.read_bytes()
        retained = bus.read_bytes()
        # Nenhum byte perdido: arquivo morto + cauda == original + nova mensagem.
        self.assertEqual(len(archived) + len(retained) - before_size,
                         len(retained) - retained.rfind(b"\n", 0, len(retained) - 1) - 1)
        self.assertEqual(archived + retained[: len(retained) - (len(archived) + len(retained) - before_size)],
                         b"".join(lines))

        # Toda linha permanece JSON válido nos dois lados (corte em fronteira).
        for line in archived.splitlines():
            json.loads(line)
        records = [json.loads(line) for line in retained.splitlines()]
        self.assertEqual(records[-1]["body"], "mensagem após rotação")
        self.assertEqual(records[0]["subject"], "prévio")

        # O inbox continua enxergando o recente após a rotação.
        inbox = self.run_tool(
            "check-coord-inbox",
            "--agent", "claude-maestro-pts2",
            "--last", "1",
        )
        self.assertEqual(inbox.returncode, 0, inbox.stderr)
        self.assertIn("mensagem após rotação", inbox.stdout)

    def test_message_rejects_symlink_and_hardlink_lock_without_touching_victim(self):
        victim = self.root / "victim-lock"
        victim.write_text("não tocar")
        lock = self.coord / ".bus.lock"
        lock.symlink_to(victim)
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(victim.read_text(), "não tocar")

        lock.unlink()
        lock.write_text("estado de lock não pode ser truncado")
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(lock.read_text(), "estado de lock não pode ser truncado")

        lock.unlink()
        os.link(victim, lock)
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(victim.read_text(), "não tocar")

    def test_message_rejects_symlink_hardlink_fifo_and_oversized_bus(self):
        victim = self.root / "victim-bus"
        victim.write_text("sentinela")
        bus = self.coord / "bus.jsonl"

        bus.symlink_to(victim)
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(victim.read_text(), "sentinela")

        bus.unlink()
        os.link(victim, bus)
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(victim.read_text(), "sentinela")

        bus.unlink()
        os.mkfifo(bus)
        started = time.monotonic()
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertLess(time.monotonic() - started, 2.0)

        bus.unlink()
        bus.touch()
        os.truncate(bus, 8 * 1024 * 1024 + 1)
        result = self.post()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("teto", result.stderr)

    def test_inbox_rejects_unsafe_or_unbounded_bus(self):
        victim = self.root / "inbox-victim"
        victim.write_text('{"to":"all"}\n')
        bus = self.coord / "bus.jsonl"
        os.link(victim, bus)
        result = self.run_tool("check-coord-inbox", "--agent", "codex-safe-pts1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hardlink", result.stderr)

        bus.unlink()
        bus.touch()
        os.truncate(bus, 8 * 1024 * 1024 + 1)
        result = self.run_tool("check-coord-inbox", "--agent", "codex-safe-pts1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("teto", result.stderr)

    def test_presence_atomic_update_preserves_session_and_uses_random_temp(self):
        trap = self.presence / ".codex-safe-pts1.json.tmp.1234"
        trap.write_text("previsível e hostil")
        first = self.presence_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        target = self.presence / "codex-safe-pts1.json"
        first_record = json.loads(target.read_text())
        second = self.presence_update("frente dois")
        self.assertEqual(second.returncode, 0, second.stderr)
        second_record = json.loads(target.read_text())
        self.assertEqual(second_record["front"], "frente dois")
        self.assertEqual(second_record["session_start"], first_record["session_start"])
        self.assertEqual(trap.read_text(), "previsível e hostil")
        self.assertEqual(os.stat(target).st_nlink, 1)
        leftovers = [path.name for path in self.presence.iterdir() if ".tmp-" in path.name]
        self.assertEqual(leftovers, [])

    def test_presence_rejects_symlink_and_hardlink_target(self):
        victim = self.root / "presence-victim"
        victim.write_text("não tocar")
        target = self.presence / "codex-safe-pts1.json"
        target.symlink_to(victim)
        result = self.presence_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(victim.read_text(), "não tocar")

        target.unlink()
        os.link(victim, target)
        result = self.presence_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(victim.read_text(), "não tocar")

    def test_presence_rejects_symlink_ancestor_and_fifo_lock_without_blocking(self):
        shutil.rmtree(self.presence)
        attacker = self.root / "attacker-presence"
        attacker.mkdir()
        self.presence.symlink_to(attacker, target_is_directory=True)
        result = self.presence_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(attacker.iterdir()), [])

        self.presence.unlink()
        self.presence.mkdir()
        lock = self.presence / ".presence.lock"
        os.mkfifo(lock)
        started = time.monotonic()
        result = self.presence_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertLess(time.monotonic() - started, 2.0)

    def test_status_does_not_follow_unsafe_presence_or_bus(self):
        victim = self.root / "status-victim"
        victim.write_text("{}")
        os.link(victim, self.presence / "codex-safe-pts1.json")
        status = self.run_tool("check-coord-status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("ilegível/inseguro", status.stderr)

        bus = self.coord / "bus.jsonl"
        bus.symlink_to(victim)
        status = self.run_tool("check-coord-status")
        self.assertNotEqual(status.returncode, 0)

    def test_load_gate_is_one_shot_and_refuses_wait_loops(self):
        started = time.monotonic()
        waiting = self.run_tool(
            "check-load-headroom", "--max", "999999", "--wait", "1"
        )
        self.assertEqual(waiting.returncode, 2)
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertIn("polling/loop passivo", waiting.stderr)

        one_shot = self.run_tool("check-load-headroom", "--max", "999999")
        self.assertEqual(one_shot.returncode, 0, one_shot.stderr)
        invalid = self.run_tool("check-load-headroom", "--max", "inf")
        self.assertEqual(invalid.returncode, 2)

    def test_writers_enforce_input_bounds(self):
        oversized = self.post("x" * 4097)
        self.assertEqual(oversized.returncode, 2)
        self.assertFalse((self.coord / "bus.jsonl").exists())

        invalid_agent = self.run_tool(
            "generate-coord-presence",
            "--agent", "../fora",
            "--front", "x",
            "--heavy", "none",
        )
        self.assertEqual(invalid_agent.returncode, 2)
        self.assertFalse((self.root / "fora.json").exists())


if __name__ == "__main__":
    unittest.main()
