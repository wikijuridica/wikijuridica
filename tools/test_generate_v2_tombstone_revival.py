"""Prova executável dos três defeitos de lote de generate-v2-tombstone-revival.

Nenhum teste toca o estoque real: cada caso monta um ROOT temporário com
shards sintéticos e chama as funções com esse root explícito (a ferramenta já
recebe ``root`` por parâmetro; não há flag nova de superfície).

Defeitos cobertos:
  (a) RevivalRefused derrubava o lote inteiro — o primeiro aprovado que caísse
      na recusa "esvaziaria o shard" fazia o --apply gravar zero.
  (b) o snapshot do censo era congelado uma vez: o segundo aprovado do MESMO
      shard morria com "shard evoluiu depois do censo".
  (c) o revert é o único consumidor do line_index do ledger — com o índice
      agora RESOLVIDO no shard vivo, reverter em LIFO tem que reconstruir a
      preimagem byte a byte.
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools/generate-v2-tombstone-revival"
MODULE_NAME = "tools.generate_v2_tombstone_revival_under_test"
# O script não tem sufixo .py: sem loader explícito o spec sai None.
SPEC = importlib.util.spec_from_file_location(
    MODULE_NAME, SCRIPT,
    loader=importlib.machinery.SourceFileLoader(MODULE_NAME, str(SCRIPT)))
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)

STOCK = "data/editorial/v2_pages"


def page_line(intent_id: str) -> bytes:
    """Linha de página comum — só precisa carregar intent_id canônico."""
    return json.dumps(
        {"intent_id": intent_id, "title": f"Pagina {intent_id}",
         "index_policy": "noindex"},
        ensure_ascii=False, sort_keys=True).encode("utf-8")


def tombstone_line(intent_id: str, reason: str) -> bytes:
    """Tombstone de schema fechado — o único formato que a rota candidata."""
    return json.dumps(
        {"intent_id": intent_id, "skipped": True, "skip_reason": reason},
        ensure_ascii=False, sort_keys=True).encode("utf-8")


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RevivalBatchTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="revival-test-"))
        (self.root / STOCK).mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write_shard(self, name: str, lines: list[bytes]) -> pathlib.Path:
        path = self.root / STOCK / name
        path.write_bytes(b"\n".join(lines) + b"\n")
        return path

    def decision(self, intent_id: str, shard: str, line_index: int) -> dict:
        return {
            "intent_id": intent_id,
            "shard_rel_path": f"{STOCK}/{shard}",
            "line_index": line_index,
            "skip_reason": "hint sem resolucao exata no catalogo",
            "reason_family": "defeito-catalogo-resolvedor",
            "approved": True,
            "refusal_codes": [],
            "evidence": {"resolved_overrides": {"hint-x": "slug-x"}},
        }

    def ledger_entries(self) -> list[dict]:
        path = self.root / module.LEDGER_REL_PATH
        if not path.exists():
            return []
        return [json.loads(line) for line in
                path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # ------------------------------------------------------------------ (a)
    def test_recusa_de_um_item_nao_derruba_o_lote(self):
        """Item que recusa vem PRIMEIRO — como aereo-11 na ordem alfabética."""
        solo_tomb = tombstone_line("aer-solo", "hint sem resolucao exata")
        solo = self.write_shard("aereo-11.jsonl", [solo_tomb])
        solo_digest_before = sha256_of(solo)

        keep_a = page_line("aer-pagina-a")
        tomb_b = tombstone_line("aer-reembolso", "hint sem resolucao exata")
        keep_c = page_line("aer-pagina-c")
        multi = self.write_shard("aereo-18.jsonl", [keep_a, tomb_b, keep_c])

        snapshots, _tombstones, _occ = module.scan_stock(self.root)
        approved = [
            self.decision("aer-solo", "aereo-11.jsonl", 1),
            self.decision("aer-reembolso", "aereo-18.jsonl", 2),
        ]
        applied, refused, halt = module.apply_approved(
            self.root, approved, snapshots)

        self.assertEqual("", halt)
        self.assertEqual(1, len(applied), "o aprovado aplicável tem que aplicar")
        self.assertEqual("aer-reembolso", applied[0]["intent_id"])
        self.assertEqual(1, len(refused))
        self.assertEqual("aer-solo", refused[0]["intent_id"])
        self.assertIn("esvaziaria o shard", refused[0]["refusal"])

        # O recusado fica intacto byte a byte; o aplicável perde só a linha.
        self.assertEqual(solo_digest_before, sha256_of(solo))
        self.assertEqual(b"\n".join([keep_a, keep_c]) + b"\n",
                         multi.read_bytes())
        ledger = self.ledger_entries()
        self.assertEqual(1, len(ledger))
        self.assertEqual("revive", ledger[0]["action"])
        self.assertEqual("aer-reembolso", ledger[0]["intent_id"])

    # ------------------------------------------------------------------ (b)
    def test_dois_aprovados_no_mesmo_shard_aplicam_os_dois(self):
        tomb_1 = tombstone_line("suc-itcmd", "hint sem resolucao exata")
        keep_a = page_line("suc-pagina-a")
        tomb_2 = tombstone_line("suc-holding", "hint sem resolucao exata")
        keep_b = page_line("suc-pagina-b")
        shard = self.write_shard(
            "sucessoes2-09.jsonl", [tomb_1, keep_a, tomb_2, keep_b])

        snapshots, _tombstones, _occ = module.scan_stock(self.root)
        approved = [
            self.decision("suc-itcmd", "sucessoes2-09.jsonl", 1),
            self.decision("suc-holding", "sucessoes2-09.jsonl", 3),
        ]
        applied, refused, halt = module.apply_approved(
            self.root, approved, snapshots)

        self.assertEqual("", halt)
        self.assertEqual([], refused, "nenhum item pode cair em 'shard evoluiu'")
        self.assertEqual(2, len(applied))
        self.assertEqual(b"\n".join([keep_a, keep_b]) + b"\n",
                         shard.read_bytes())
        # O índice do segundo é RESOLVIDO (2), não o do censo (3): a primeira
        # remoção deslocou a linha uma posição para cima.
        ledger = self.ledger_entries()
        self.assertEqual([1, 2], [entry["line_index"] for entry in ledger])
        self.assertEqual([1, 3], [entry["census_line_index"]
                                  for entry in ledger])
        # Encadeamento: o 'antes' do segundo é o 'depois' do primeiro.
        self.assertEqual(ledger[0]["shard_sha256_after"],
                         ledger[1]["shard_sha256_before"])

    # ------------------------------------------------------------------ (c)
    def test_revert_lifo_reconstroi_a_preimagem_exata(self):
        tomb_1 = tombstone_line("suc-itcmd", "hint sem resolucao exata")
        keep_a = page_line("suc-pagina-a")
        tomb_2 = tombstone_line("suc-holding", "hint sem resolucao exata")
        keep_b = page_line("suc-pagina-b")
        shard = self.write_shard(
            "sucessoes2-09.jsonl", [tomb_1, keep_a, tomb_2, keep_b])
        original_bytes = shard.read_bytes()
        original_digest = sha256_of(shard)

        snapshots, _tombstones, _occ = module.scan_stock(self.root)
        applied, refused, halt = module.apply_approved(
            self.root,
            [self.decision("suc-itcmd", "sucessoes2-09.jsonl", 1),
             self.decision("suc-holding", "sucessoes2-09.jsonl", 3)],
            snapshots)
        self.assertEqual(("", [], 2), (halt, refused, len(applied)))
        intermediate_digest = applied[0]["shard_sha256_after"]

        # LIFO: reverter o segundo devolve o estado logo após o primeiro.
        module.revert_revival(self.root, "suc-holding")
        self.assertEqual(intermediate_digest, sha256_of(shard))
        # E reverter o primeiro devolve a preimagem original byte a byte.
        module.revert_revival(self.root, "suc-itcmd")
        self.assertEqual(original_digest, sha256_of(shard))
        self.assertEqual(original_bytes, shard.read_bytes())

        actions = [entry["action"] for entry in self.ledger_entries()]
        self.assertEqual(["revive", "revive", "revert", "revert"], actions)

    def test_cas_continua_recusando_evolucao_alheia(self):
        """A outra metade do (b): terceiro que mexe no shard AINDA barra.

        A expectativa viva do lote só absorve as remoções do próprio lote; um
        append feito por fora entre o censo e a aplicação continua sendo
        'shard evoluiu depois do censo'.
        """
        tomb = tombstone_line("suc-itcmd", "hint sem resolucao exata")
        keep = page_line("suc-pagina-a")
        shard = self.write_shard("sucessoes2-09.jsonl", [tomb, keep])
        snapshots, _tombstones, _occ = module.scan_stock(self.root)

        # Escritor de fora acrescenta uma página depois do censo.
        alheio = page_line("suc-pagina-de-terceiro")
        shard.write_bytes(shard.read_bytes() + alheio + b"\n")
        digest_alheio = sha256_of(shard)

        applied, refused, halt = module.apply_approved(
            self.root,
            [self.decision("suc-itcmd", "sucessoes2-09.jsonl", 1)],
            snapshots)
        self.assertEqual(("", [], 1), (halt, applied, len(refused)))
        self.assertIn("shard evoluiu depois do censo", refused[0]["refusal"])
        self.assertEqual(digest_alheio, sha256_of(shard))
        self.assertEqual([], self.ledger_entries())

    def test_esvaziamento_segue_recusado_sem_rota_sancionada(self):
        """Controle negativo do (c): shard de linha única continua fechado.

        check-v2-finalized-commit:1368-1369 reprova shard finalizado vazio e
        removed_finalized:625-634 exige recibo de quarentena para o arquivo
        sumir — logo esvaziar aqui produziria estoque incommitável.
        """
        tomb = tombstone_line("aer-solo", "hint sem resolucao exata")
        shard = self.write_shard("aereo-11.jsonl", [tomb])
        snapshots, _tombstones, _occ = module.scan_stock(self.root)
        with self.assertRaises(module.RevivalRefused) as caught:
            module.apply_revival(
                self.root, self.decision("aer-solo", "aereo-11.jsonl", 1),
                snapshots)
        self.assertIn("esvaziaria o shard", str(caught.exception))
        self.assertEqual(b"\n".join([tomb]) + b"\n", shard.read_bytes())
        self.assertEqual([], self.ledger_entries())


if __name__ == "__main__":
    unittest.main()
