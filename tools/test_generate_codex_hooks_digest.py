#!/usr/bin/env python3
"""Testes do reancorador do digest do bundle anti-loop.

O valor era digitado à mão em três lanes de `.codex/hooks.json`. Em 2026-08-30
o commit `62bd1d19` mexeu em `internal/goalbaseline/baseline.go`, que está no
bundle, e o número não foi reescrito: por seis dias o hook recusou toda chamada
com `transitive_bundle_digest_mismatch`. A suíte acusou; ninguém a rodou.

Este teste cobra as duas pontas do reancorador — que ele reescreve quando está
defasado e que NÃO reescreve quando está em dia — e a guarda que importa mais
que as duas: se uma lane perder a amarração ao bundle, ele reprova em vez de
"consertar" as que sobraram. Um hook amarrado em duas das três lanes é pior que
um defasado, porque o buraco não aparece em lugar nenhum.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "generate-codex-hooks-digest"

VIVO = "sha256:" + "1" * 64
VELHO = "sha256:" + "0" * 64


def carrega():
    loader = importlib.machinery.SourceFileLoader("reancorador", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def hooks_json(*digests: str) -> str:
    """Reproduz a forma real: o digest dentro de uma linha de comando."""
    lanes = ",\n".join(
        f'      "command": "python3 .codex/hooks/anti_loop.py --lane {i} '
        f'--expected-bundle-digest {d}"'
        for i, d in enumerate(digests))
    return "{\n" + lanes + "\n}\n"


class TestReancora(unittest.TestCase):
    def setUp(self):
        self.tool = carrega()

    def test_tres_lanes_defasadas_sao_reescritas(self):
        fonte = hooks_json(VELHO, VELHO, VELHO)
        novo, defasadas = self.tool.reancora(fonte, VIVO)
        self.assertEqual(defasadas, 3)
        self.assertEqual(self.tool.digests_declarados(novo), [VIVO] * 3)

    def test_ja_em_dia_nao_reescreve_nada(self):
        fonte = hooks_json(VIVO, VIVO, VIVO)
        novo, defasadas = self.tool.reancora(fonte, VIVO)
        self.assertEqual(defasadas, 0)
        self.assertEqual(novo, fonte)

    def test_uma_lane_defasada_e_contada_sozinha(self):
        fonte = hooks_json(VIVO, VELHO, VIVO)
        novo, defasadas = self.tool.reancora(fonte, VIVO)
        self.assertEqual(defasadas, 1)
        self.assertEqual(self.tool.digests_declarados(novo), [VIVO] * 3)

    def test_lane_que_perdeu_a_amarracao_reprova_em_vez_de_consertar(self):
        """Duas lanes amarradas e uma solta é pior que três defasadas."""
        fonte = hooks_json(VELHO, VELHO)
        with self.assertRaises(ValueError) as capturado:
            self.tool.reancora(fonte, VIVO)
        self.assertIn("perdeu a amarração", str(capturado.exception))

    def test_lane_a_mais_tambem_reprova(self):
        fonte = hooks_json(VELHO, VELHO, VELHO, VELHO)
        with self.assertRaises(ValueError):
            self.tool.reancora(fonte, VIVO)

    def test_preserva_o_arquivo_byte_a_byte_fora_do_digest(self):
        """Reserializar o JSON enterraria a mudança num diff de arquivo inteiro."""
        fonte = hooks_json(VELHO, VELHO, VELHO)
        novo, _ = self.tool.reancora(fonte, VIVO)
        self.assertEqual(novo.replace(VIVO, VELHO), fonte)


class TestContraORepositorioReal(unittest.TestCase):
    def setUp(self):
        self.tool = carrega()

    def test_o_hooks_json_do_repo_aponta_para_o_bundle_vivo(self):
        """A regressão de 2026-08-30, travada: se voltar, este teste acusa.

        É o mesmo cálculo que o hook faz em runtime — importado de
        `anti_loop`, nunca reimplementado, porque uma segunda implementação
        divergiria em silêncio e é exatamente esse o defeito.
        """
        digest = self.tool.digest_vivo()
        declarados = self.tool.digests_declarados(
            self.tool.HOOKS_JSON.read_text(encoding="utf-8"))
        self.assertEqual(len(declarados), self.tool.OCORRENCIAS_ESPERADAS)
        self.assertEqual(
            set(declarados), {digest},
            "o digest de .codex/hooks.json não é o do bundle vivo; rode "
            "./tools/generate-codex-hooks-digest")


if __name__ == "__main__":
    unittest.main()
