#!/usr/bin/env python3
"""Testes das três portas dos fundos fechadas em 2026-08-29 (BUG-069 da caça).

Cada um destes gates aprovava com exit 0 quando o INSUMO sumia — o estado em que
eles menos podem aprovar, porque é justamente quando não conseguem verificar
nada. Num verificador anti-fraude, aprovar por ausência de dado é porta dos
fundos: basta apagar o arquivo para o gate dizer que está tudo bem.

Os testes rodam cada gate contra uma raiz temporária, sem tocar o repositório.
"""

import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def roda(script, args, cwd, env_extra=None):
    ambiente = dict(os.environ)
    if env_extra:
        ambiente.update(env_extra)
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "tools", script), *args],
        capture_output=True, text=True, timeout=120, cwd=cwd, env=ambiente,
    )


class TestAusenciaDeDadoNaoAprova(unittest.TestCase):
    def test_alertas_ledger_ausente_reprova(self):
        """Apagar o ledger não pode silenciar o canal de alerta."""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "data", "ops"), exist_ok=True)
            r = roda("check-owner-alerts-abertos", [], tmp,
                     {"WIKI_OWNER_ALERTS_LEDGER": os.path.join(tmp, "nao-existe.jsonl")})
            if r.returncode == 0:
                self.fail(f"ledger ausente aprovou com exit 0 — porta dos fundos reaberta\n{r.stdout}{r.stderr}")
            self.assertEqual(r.returncode, 2, f"esperava exit 2 (anomalia), veio {r.returncode}: {r.stderr[:200]}")

    def test_access_log_ausente_reprova(self):
        """Log sumido é rotação/permissão quebrada, não 'site sem tráfego'."""
        with tempfile.TemporaryDirectory() as tmp:
            r = roda("check-access-log-bots", ["--log", os.path.join(tmp, "nao-existe.log")], tmp)
            if r.returncode == 0:
                self.fail(f"log ausente aprovou com exit 0 — porta dos fundos reaberta\n{r.stdout}{r.stderr}")
            self.assertEqual(r.returncode, 2, f"esperava exit 2 (anomalia), veio {r.returncode}: {r.stderr[:200]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
