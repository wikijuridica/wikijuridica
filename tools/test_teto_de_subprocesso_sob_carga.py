#!/usr/bin/env python3
"""Testes de _teto_de_subprocesso_sob_carga, em tools/check-go-index-compile-closure.

O gate do commit já sabia esticar o ORÇAMENTO GLOBAL pela carga da máquina — a
lição de 2026-08-12, quando load 21 em 8 núcleos fez o hook recusar commits
CORRETOS com mensagem indistinguível de quebra de compilação.

Os tetos INTERNOS de subprocesso ficaram para trás como constantes fixas, e o
defeito voltou por outra porta: em 2026-09-05, com load 27, o orçamento global
esticou certo e o commit foi recusado assim mesmo, por "classificação estrutural
Go excedeu 15s".

Estes testes fixam as duas metades: o teto acompanha a máquina, e NUNCA permite
gastar mais do que o orçamento total concedido.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import pathlib
import unittest
from unittest import mock

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "check-go-index-compile-closure"


def carrega():
    loader = importlib.machinery.SourceFileLoader("closure_gate", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class TetoSobCargaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = carrega()

    def test_maquina_ociosa_nao_estica_nada(self):
        """Fator 1 devolve o valor base intacto: sem carga, sem folga extra."""
        with mock.patch.object(self.mod, "_load_stretch_factor", return_value=(1.0, "ociosa")):
            self.assertEqual(self.mod._teto_de_subprocesso_sob_carga(15), 15)
            self.assertEqual(self.mod._teto_de_subprocesso_sob_carga(30), 30)

    def test_maquina_carregada_estica_pelo_mesmo_fator_do_orcamento(self):
        """É o caso medido em 2026-09-05: load 27 em 8 núcleos."""
        with mock.patch.object(self.mod, "_load_stretch_factor", return_value=(2.0, "load alto")):
            self.assertEqual(self.mod._teto_de_subprocesso_sob_carga(15), 30)
            self.assertEqual(self.mod._teto_de_subprocesso_sob_carga(30), 60)

    def test_fator_abaixo_de_um_nunca_encolhe_o_teto(self):
        """Encolher transformaria uma máquina ociosa em motivo de reprovação —
        o inverso exato do propósito."""
        with mock.patch.object(self.mod, "_load_stretch_factor", return_value=(0.5, "ociosa")):
            self.assertEqual(self.mod._teto_de_subprocesso_sob_carga(15), 15)

    def test_os_tetos_internos_de_subprocesso_passam_pelo_ajuste(self):
        """A guarda que impede a regressão de voltar: se alguém acrescentar um
        subprocesso com teto fixo, ou remover o ajuste de um existente, isto
        reprova. Casa a FORMA da chamada, que é o que o defeito de 2026-09-05
        tinha errado."""
        fonte = ALVO.read_text(encoding="utf-8")
        for constante in ("API_SURFACE_TIMEOUT_SECONDS", "GOFMT_TIMEOUT_SECONDS"):
            chamada_crua = f"_remaining_timeout({constante})"
            self.assertNotIn(
                chamada_crua, fonte,
                f"{constante} voltou a ser teto FIXO: sob carga o commit correto será "
                "recusado com mensagem indistinguível de erro de código",
            )
            self.assertIn(
                f"_remaining_timeout(_teto_de_subprocesso_sob_carga({constante}))", fonte,
                f"{constante} precisa passar pelo ajuste de carga",
            )
        # COMPILE_TIMEOUT_SECONDS já tinha o ajuste, por outra forma; se ele
        # sumir, o teto principal volta a ser fixo.
        self.assertIn("COMPILE_TIMEOUT_SECONDS * fator_carga", fonte,
                      "o teto de compilação perdeu o ajuste de carga que já tinha")

    def test_o_orcamento_global_continua_sendo_o_limite_de_cima(self):
        """Esticar teto interno NÃO pode virar licença para gastar mais que o
        orçamento total. Quem pede --budget-seconds 1 continua abortando em 1 s,
        porque _remaining_timeout corta pelo ACTIVE_DEADLINE."""
        fonte = ALVO.read_text(encoding="utf-8")
        # todo teto ajustado continua DENTRO de _remaining_timeout
        for constante in ("API_SURFACE_TIMEOUT_SECONDS", "GOFMT_TIMEOUT_SECONDS"):
            self.assertIn(f"_remaining_timeout(_teto_de_subprocesso_sob_carga({constante}))", fonte)
            self.assertNotIn(f"timeout=_teto_de_subprocesso_sob_carga({constante})", fonte,
                             f"{constante} escapou do corte pelo orçamento global")

    def test_a_mensagem_de_erro_diz_o_teto_efetivo_nao_o_base(self):
        """Mensagem que cita 15s quando o teto valia 30s manda o desenvolvedor
        procurar defeito no lugar errado — foi como o defeito se disfarçou."""
        fonte = ALVO.read_text(encoding="utf-8")
        self.assertIn("ajustada pela carga", fonte,
                      "a mensagem de estouro precisa dizer o teto EFETIVO")


if __name__ == "__main__":
    unittest.main()
