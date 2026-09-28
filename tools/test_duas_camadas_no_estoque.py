#!/usr/bin/env python3
"""EIXO 4 do check-derived-authorial-floor: medir as duas camadas ANTES do ar.

★ O PONTO CEGO (medido em 2026-09-16)

Os eixos de piso e teto do gate leem `public/**/index.html`. Uma família nova
publica INTEIRA sem que o gate tenha medido uma linha dela: no dia em que este
teste nasceu o gate imprimia `texto citado max 52,3% (teto 55%)` e devolvia OK,
enquanto as 30 primeiras páginas de acórdão do cérebro esperavam no estoque.

★ A ARMADILHA QUE ESTE TESTE TRANCA

A primeira versão do eixo aplicou ao JSONL os limiares calibrados no HTML e
acusou 132 páginas — **123 delas já publicadas e aprovadas pelo eixo em HTML**.
Era o defeito que o próprio gate existe para acusar: duas réguas medindo corpos
diferentes. O offset foi medido sobre 1.213 pares (mesma página no JSONL e no
HTML servido):

    proporção citada   JSONL − HTML : mínimo +0,0041 · mediana +0,0358 · máximo +0,0726
    palavras autorais  HTML − JSONL : mínimo   +59   · mediana   +75   · máximo   +125

Os limiares do eixo saem daí, sempre pela ponta que evita acusar quem a página
publicada aprova. Este teste cobre as três consequências:

  1. FALSO POSITIVO — sobre o acervo REAL, o eixo não reprova ninguém;
  2. CONTROLE — o espelho de fonte oficial e a página sem camada própria
     continuam reprovando. Sem isto a calibração seria falso-verde;
  3. BANDA — o que o JSONL não decide sai nomeado, não vira aprovação.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-derived-authorial-floor"


def carrega():
    spec = importlib.util.spec_from_loader(
        "gate_sob_teste",
        importlib.machinery.SourceFileLoader("gate_sob_teste", str(GATE)))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def pagina_com(citado_palavras: int, autoral_palavras: int) -> dict:
    """Monta um registro v2 com as duas camadas no tamanho pedido.

    A citação vai entre aspas curvas e precedida de menção a ato oficial, que é
    o que `mede` exige para contar como transcrição (ATO_OFICIAL + 25 palavras).
    """
    citacao = " ".join(["mandado"] * citado_palavras)
    autoral = " ".join(["comentário"] * autoral_palavras)
    return {
        "intent_id": "controle-sintetico",
        "opening": f"Segundo o acórdão do Superior Tribunal de Justiça, “{citacao}”.",
        "sections": [{"heading": "Comentário", "text": autoral}],
        "faq": [],
    }


class ReguaCalibrada(unittest.TestCase):

    def test_limiares_saem_do_offset_medido(self):
        g = carrega()
        self.assertEqual(g.PISO_AUTORAL_NO_ESTOQUE,
                         g.PISO_AUTORAL - g.GANHO_AUTORAL_MINIMO)
        self.assertAlmostEqual(g.TETO_CITADO_NO_ESTOQUE,
                               g.TETO_CITADO + g.OFFSET_CITADO_MAXIMO)
        self.assertAlmostEqual(g.TETO_CITADO_INCERTO,
                               g.TETO_CITADO + g.OFFSET_CITADO_MINIMO)
        # A direção do arredondamento é o que impede o falso positivo.
        self.assertGreater(g.TETO_CITADO_NO_ESTOQUE, g.TETO_CITADO)
        self.assertLess(g.PISO_AUTORAL_NO_ESTOQUE, g.PISO_AUTORAL)


class FalsoPositivoSobreOAcervoReal(unittest.TestCase):

    def test_o_eixo_nao_reprova_nenhuma_pagina_do_acervo(self):
        g = carrega()
        medidas, fora, _ = g.duas_camadas_no_estoque(sys.stderr)
        self.assertIsNotNone(medidas)
        self.assertGreater(len(medidas), 1000,
                           "amostra pequena demais para falar pelo acervo")
        self.assertEqual(
            [f"{m[1]}:{m[2]} ({m[6]:.1%} citado, {m[5]} proprias)" for m in fora], [],
            "o eixo acusou pagina do acervo real — regua errada, como na 1a versao")

    def test_a_banda_de_incerteza_nomeia_quem_esta_nela(self):
        g = carrega()
        _, _, incertas = g.duas_camadas_no_estoque(sys.stderr)
        for m in incertas:
            self.assertGreater(m[6], g.TETO_CITADO_INCERTO)
            self.assertLessEqual(m[6], g.TETO_CITADO_NO_ESTOQUE)
            self.assertTrue(m[2], "página na banda sem intent_id nomeado")


class ControlesQueContinuamReprovando(unittest.TestCase):
    """Sem um controle que ainda reprova, a calibração seria falso-verde."""

    def test_espelho_de_fonte_oficial_reprova(self):
        g = carrega()
        # 900 palavras citadas contra 300 próprias = 75% citado, acima de
        # qualquer ponta do offset: é espelho, não comentário.
        total, citadas, oficial, _ = g.mede(g.corpo_v2(pagina_com(900, 300)))
        self.assertTrue(oficial)
        proporcao = citadas / total
        self.assertGreater(proporcao, g.TETO_CITADO_NO_ESTOQUE)

    def test_pagina_sem_camada_propria_reprova(self):
        g = carrega()
        total, citadas, oficial, _ = g.mede(g.corpo_v2(pagina_com(400, 40)))
        self.assertTrue(oficial)
        self.assertLess(total - citadas, g.PISO_AUTORAL_NO_ESTOQUE)

    def test_pagina_legitima_do_acervo_nao_reprova(self):
        g = carrega()
        total, citadas, oficial, _ = g.mede(g.corpo_v2(pagina_com(300, 500)))
        self.assertTrue(oficial)
        self.assertLessEqual(citadas / total, g.TETO_CITADO_NO_ESTOQUE)
        self.assertGreaterEqual(total - citadas, g.PISO_AUTORAL_NO_ESTOQUE)

    def test_mutante_que_afrouxa_o_teto_deixa_o_espelho_passar(self):
        """Mutante: teto do estoque vira 1,0. O controle acima morre."""
        fonte = GATE.read_text(encoding="utf-8")
        alvo = "TETO_CITADO_NO_ESTOQUE = TETO_CITADO + OFFSET_CITADO_MAXIMO"
        self.assertIn(alvo, fonte)
        mutado = fonte.replace(alvo, "TETO_CITADO_NO_ESTOQUE = 1.0")
        espaco: dict = {}
        exec(compile(mutado.split("def main(")[0], "gate_mutante", "exec"), espaco)
        total, citadas, _, _ = espaco["mede"](
            espaco["corpo_v2"](pagina_com(900, 300)))
        self.assertLessEqual(
            citadas / total, espaco["TETO_CITADO_NO_ESTOQUE"],
            "com o teto em 1,0 o espelho passa — e é isso que o controle acima mata")


class OGateChamaOEixo(unittest.TestCase):

    def test_main_usa_o_eixo_e_ele_entra_no_veredito(self):
        fonte = GATE.read_text(encoding="utf-8")
        self.assertIn("medidas_estoque, fora_do_estoque, incertas_estoque = duas_camadas_no_estoque(", fonte)
        self.assertIn("and not fora_do_estoque:", fonte)

    def test_mutante_que_desliga_o_eixo_do_veredito_morre(self):
        fonte = GATE.read_text(encoding="utf-8")
        alvo = "and not fora_do_estoque:"
        self.assertIn(alvo, fonte)
        mutado = fonte.replace(alvo, ":")
        self.assertNotIn(alvo, mutado,
                         "a mutacao nao removeu o eixo do veredito")
        self.assertNotEqual(mutado, fonte)


if __name__ == "__main__":
    unittest.main(verbosity=2)
