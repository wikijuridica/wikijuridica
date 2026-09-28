#!/usr/bin/env python3
"""Prova do gate tools/check-checked-at-coerente: reprova no caso ruim, passa no bom.

Roda o gate REAL como subprocesso sobre pages.json/estoque/manifesto sintéticos
em tempfile — reimplementar a comparação aqui provaria a cópia, não o gate. As
propriedades vêm do defeito que o gate existe para pegar (2026-09-01):

  A. checked_at UM DIA à frente do verified_at máximo do documento reprova
     (tolerância zero), e a linha de reprovação nomeia página, URL, checked_at
     e o máximo encontrado — sem isso o operador corrige às cegas.
  B. O lastro é o MÁXIMO por documento (URL sem fragmento), não o último shard
     lido: com o shard mais novo no glob carregando a data mais VELHA, o gate
     tem de continuar verde. Foi assim que `/fontes/` reprovou por engano na
     primeira rodada — 5 falsos positivos que a chave por documento apagou.
  C. Rótulo sem conferência alguma reprova SÓ fora do manifesto (onde o gate do
     Go `source_verification_evidence` não chega); dentro dele é reportado e o
     exit continua 0 — reprovar duas vezes o mesmo fato competiria pela mesma
     cota de exibição.
  D. checked_at vazio não afirma nada e não conta.
  E. Formato fora de AAAA-MM-DD reprova: data que não se compara não se prova.
  F. Estoque sem verified_at válido ou pages.json ausente = exit 2, nunca 0.
  G. O SEGUNDO lastro (2026-09-05): `data/source-audit/institucional_source_verification.jsonl`,
     gravado por `tools/generate-institucional-source-verification`, soma ao
     estoque v2 com a MESMA régua. Documento sem verified_at nenhum no estoque
     mas com verified_at no ledger institucional PASSA (o ledger é lastro
     legítimo, não exceção); a mesma régua de tolerância zero e MÁXIMO entre as
     origens continua valendo — ledger com data ANTERIOR ao checked_at
     REPROVA igual, e ledger ausente não muda nada (retrocompatibilidade).

Rodar: nice -n 19 python3 tools/test_check_checked_at_coerente.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-checked-at-coerente"

DOCUMENTO = "https://www.planalto.gov.br/ccivil_03/leis/l8906.htm"
SEM_REGISTRO = "https://www.oab.org.br/leisnormas/legislacao/provimentos/205-2021"


def pagina(path: str, fontes: list[tuple[str, str]]) -> dict:
    return {
        "path": path,
        "unique_intent_id": "teste:" + path.strip("/").replace("/", "-"),
        "source_provenance": [
            {"source_id": "x", "source_name": "Fonte", "source_url": url,
             "checked_at": checked, "license_note": "n"}
            for url, checked in fontes
        ],
    }


def registro(fontes: list[tuple[str, str]]) -> str:
    return json.dumps({"intent_id": "i", "official_sources": [
        {"url": url, "name": "Fonte", "anchor_claim": "sustenta", "verified_at": verified, "http_status": 200}
        for url, verified in fontes
    ]}, ensure_ascii=False)


class CheckedAtCoerenteTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="checked-at-coerente-")
        self.dir = Path(self._tmp.name)
        self.estoque = self.dir / "estoque"
        self.estoque.mkdir()
        # Shard "a" (primeiro no glob) tem a conferência mais NOVA do documento;
        # shard "b" (último) tem a mais VELHA. Último-lido daria 2026-07-01.
        (self.estoque / "a.jsonl").write_text(
            registro([(DOCUMENTO + "#art7", "2026-07-16")]) + "\n", encoding="utf-8")
        (self.estoque / "b.jsonl").write_text(
            registro([(DOCUMENTO + "#art1", "2026-07-01")]) + "\n", encoding="utf-8")
        self.manifesto = self.dir / "published_manifest.jsonl"
        self.manifesto.write_text(json.dumps({"path": "/area/no-manifesto/"}) + "\n", encoding="utf-8")
        # Ledger institucional AUSENTE por padrão: os testes A-F não podem
        # depender dele para continuar provando o comportamento de antes de
        # 2026-09-05. Só os testes G apontam para um arquivo com conteúdo.
        self.ledger_institucional = self.dir / "ledger-ausente.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def roda(self, paginas: list[dict], *, estoque: Path | None = None, pages: Path | None = None,
              ledger_institucional: Path | None = None):
        if pages is None:
            pages = self.dir / "pages.json"
            pages.write_text(json.dumps(paginas, ensure_ascii=False), encoding="utf-8")
        executado = subprocess.run(
            [sys.executable, str(GATE), "--pages", str(pages),
             "--estoque", str(estoque or self.estoque), "--manifesto", str(self.manifesto),
             "--ledger-institucional", str(ledger_institucional or self.ledger_institucional)],
            cwd=str(RAIZ), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, timeout=120,
        )
        return executado.returncode, executado.stdout

    def test_A_um_dia_a_frente_reprova_e_nomeia(self) -> None:
        exit_code, saida = self.roda([pagina("/sobre/", [(DOCUMENTO, "2026-07-17")])])
        self.assertEqual(exit_code, 1, saida)
        self.assertIn("REPROVADO", saida)
        self.assertIn("/sobre/ · " + DOCUMENTO + " · checked_at=2026-07-17 > verified_at máximo=2026-07-16", saida)
        self.assertIn("com lastro mas checked_at À FRENTE        : 1", saida)

    def test_B_maximo_por_documento_nao_ultimo_shard(self) -> None:
        # Igual ao máximo (2026-07-16), citado por OUTRO fragmento: coerente.
        exit_code, saida = self.roda([pagina("/sobre/", [(DOCUMENTO + "#art44", "2026-07-16")])])
        self.assertEqual(exit_code, 0, saida)
        self.assertIn("com lastro coerente (checked_at <= máximo): 1", saida)
        self.assertIn("1 documento(s) distinto(s)", saida)

    def test_C_sem_lastro_reprova_so_fora_do_manifesto(self) -> None:
        exit_code, saida = self.roda([pagina("/area/no-manifesto/", [(SEM_REGISTRO, "2026-08-04")])])
        self.assertEqual(exit_code, 0, saida)
        self.assertIn("sem lastro nenhum, rota no manifesto      : 1", saida)
        self.assertIn("/area/no-manifesto/ · " + SEM_REGISTRO, saida)

        exit_code, saida = self.roda([pagina("/sobre/", [(SEM_REGISTRO, "2026-08-04")])])
        self.assertEqual(exit_code, 1, saida)
        self.assertIn("sem lastro nenhum, rota FORA do manifesto : 1", saida)
        self.assertIn("/sobre/ · " + SEM_REGISTRO + " · checked_at=2026-08-04 · verified_at: nenhum no estoque", saida)

    def test_D_checked_at_vazio_nao_conta(self) -> None:
        exit_code, saida = self.roda([pagina("/sobre/", [(SEM_REGISTRO, ""), (DOCUMENTO, "2026-07-01")])])
        self.assertEqual(exit_code, 0, saida)
        self.assertIn("fontes conferidas (com checked_at)          : 1", saida)

    def test_E_formato_invalido_reprova(self) -> None:
        exit_code, saida = self.roda([pagina("/sobre/", [(DOCUMENTO, "16/07/2026")])])
        self.assertEqual(exit_code, 1, saida)
        self.assertIn("checked_at fora de AAAA-MM-DD             : 1", saida)
        self.assertIn("checked_at='16/07/2026'", saida)

    def test_F_nao_rodou_e_exit_2(self) -> None:
        vazio = self.dir / "vazio"
        vazio.mkdir()
        (vazio / "z.jsonl").write_text(registro([(DOCUMENTO, "")]) + "\n", encoding="utf-8")
        exit_code, saida = self.roda([pagina("/sobre/", [(DOCUMENTO, "2026-07-16")])], estoque=vazio)
        self.assertEqual(exit_code, 2, saida)
        self.assertIn("NÃO RODOU: nenhum verified_at válido", saida)

        exit_code, saida = self.roda([], pages=self.dir / "nao-existe.json")
        self.assertEqual(exit_code, 2, saida)
        self.assertIn("NÃO RODOU", saida)

    def test_G_ledger_institucional_fornece_lastro_e_passa(self) -> None:
        # OAB_PROVIMENTO não tem verified_at algum no estoque v2 (é o caso real
        # medido em 2026-09-01: /sobre/, /metodologia/, /aviso-legal/,
        # /contato/advogado/). O ledger institucional, gravado por
        # generate-institucional-source-verification após um GET real, dá
        # lastro em 2026-09-05 — igual ou depois do checked_at, PASSA.
        ledger = self.dir / "ledger.jsonl"
        ledger.write_text(json.dumps({
            "url": SEM_REGISTRO, "documento": SEM_REGISTRO, "verified_at": "2026-09-05",
            "http_status": 200, "bytes": 73589, "sha256": "x" * 64,
            "tool": "generate-institucional-source-verification",
        }) + "\n", encoding="utf-8")

        exit_code, saida = self.roda(
            [pagina("/sobre/", [(SEM_REGISTRO, "2026-08-04")])], ledger_institucional=ledger)
        self.assertEqual(exit_code, 0, saida)
        self.assertIn("com lastro coerente (checked_at <= máximo): 1", saida)
        self.assertIn("ledger institucional", saida)
        self.assertNotIn("sem lastro nenhum, rota FORA do manifesto : 1", saida)

    def test_G_ledger_institucional_com_data_anterior_reprova_igual(self) -> None:
        # A MESMA régua vale para o segundo lastro: verified_at do ledger
        # ANTERIOR ao checked_at não cobre o rótulo — tolerância continua zero,
        # o ledger institucional não é uma exceção que afrouxa nada.
        ledger = self.dir / "ledger.jsonl"
        ledger.write_text(json.dumps({
            "url": SEM_REGISTRO, "documento": SEM_REGISTRO, "verified_at": "2026-07-01",
            "http_status": 200, "bytes": 73589, "sha256": "x" * 64,
            "tool": "generate-institucional-source-verification",
        }) + "\n", encoding="utf-8")

        exit_code, saida = self.roda(
            [pagina("/sobre/", [(SEM_REGISTRO, "2026-08-04")])], ledger_institucional=ledger)
        self.assertEqual(exit_code, 1, saida)
        self.assertIn("REPROVADO", saida)
        self.assertIn("com lastro mas checked_at À FRENTE        : 1", saida)
        self.assertIn(f"{SEM_REGISTRO} · checked_at=2026-08-04 > verified_at máximo=2026-07-01", saida)

    def test_gate_existe_e_e_executavel(self) -> None:
        self.assertTrue(GATE.is_file(), GATE)
        self.assertTrue(os.access(GATE, os.X_OK), "gate sem bit de execução")


if __name__ == "__main__":
    unittest.main()
