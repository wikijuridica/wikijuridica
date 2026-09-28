#!/usr/bin/env python3
"""Testes do detector de contador de volume-zero em contrato (BUG-106 da caça).

O GOAL.md é o PRIMEIRO na cadeia de precedência do projeto, e quatro parágrafos
dele declaravam `published_manifest=0` e `deficit_to_10000=10000` — três se
autodeclarando como atualização que "prevalece sobre qualquer parágrafo
histórico abaixo". O portal publica desde 2026-08-13, com 10.116 rotas.

Agente lê por grep. Quem casasse aquele parágrafo concluiria que o portal nunca
publicou nada — e já aconteceu: uma sessão propôs "publicar as ~104 páginas
prontas" porque a documentação induzia a existir estoque parado.

O detector precisa separar três coisas que se parecem no texto:
  1. contador que se apresenta como ESTADO           -> acusa
  2. registro histórico DATADO                        -> não acusa (é o registro
     que o projeto quer preservar; apagá-lo seria reescrever a história)
  3. o próprio aviso que DESCREVE o contador vencido  -> não acusa (senão o
     remédio vira doença — e foi o que aconteceu na primeira execução)
"""

import importlib.util
import os
import sys
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carrega():
    caminho = os.path.join(RAIZ, "tools", "check-contrato-vs-medicao")
    loader = SourceFileLoader("check_contrato", caminho)
    spec = importlib.util.spec_from_loader("check_contrato", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class TestDetectorDeContadorVencido(unittest.TestCase):
    def setUp(self):
        self.mod = carrega()

    def test_contador_como_estado_e_acusado(self):
        linha = "Estado atual validado neste ciclo: `published_manifest=0`, `deficit_to_10000=10000`."
        self.assertFalse(
            self.mod._e_registro_historico(linha),
            "contador sem data foi tratado como registro histórico e escaparia do gate",
        )
        casou = any(p.search(linha) for p in self.mod.CONTADORES_ZERO)
        self.assertTrue(casou, "o padrão de contador-zero não casou a forma chave=valor")

    def test_registro_datado_nao_e_acusado(self):
        for linha in (
            "Registro histórico do ciclo 376 em 2026-06-19: `published_manifest=0`.",
            "Atualização viva do ciclo 393 em 2026-06-21: `published_manifest=0`.",
            "Registro histórico Codex 1 do ciclo 362, de 2026-06-14 (contadores VENCIDOS): `published_manifest=0`.",
        ):
            self.assertTrue(
                self.mod._e_registro_historico(linha),
                f"registro DATADO foi acusado, o que puniria a preservação da história: {linha}",
            )

    def test_rotulo_sem_data_nao_escapa(self):
        """'Registro histórico' sem data seria um rótulo que qualquer parágrafo veste."""
        linha = "Registro histórico do ciclo 999: `published_manifest=0`."
        self.assertFalse(
            self.mod._e_registro_historico(linha),
            "rótulo de registro SEM data deixou o contador escapar do gate",
        )

    def test_frases_zero_em_prosa_continuam_cobertas(self):
        """A cobertura anterior (prosa) não pode ter regredido."""
        self.assertIn("publicação zero", self.mod.FRASES_ZERO)
        self.assertIn("nenhuma página jurídica pública", self.mod.FRASES_ZERO)

    def test_contratos_extra_incluem_goal_e_agents(self):
        self.assertIn("GOAL.md", self.mod.CONTRATOS_EXTRA)
        self.assertIn("AGENTS.md", self.mod.CONTRATOS_EXTRA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
