#!/usr/bin/env python3
"""Testes de tools/check-edge-live — o ramo de resolução de alerta.

O defeito que estes testes travam (BUG-060 da caça, 2026-08-29): o script
gravava o evento atual no ledger e SÓ ENTÃO lia "o estado anterior", que é a
última linha DESSE MESMO ledger. O anterior era, portanto, o evento recém-
gravado, `anterior_ok` nunca discordava do agora, e o ramo `elif not
anterior_ok` ficou inalcançável por construção.

Medido no ledger antes da correção: 63 alertas emitidos, ZERO resoluções em todo
o histórico. `borda-origem`, severidade crítica, ficou 38 horas aberta com a
condição comprovadamente curada.
"""

import json
import os
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
import importlib.util

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carrega_modulo():
    caminho = os.path.join(RAIZ, "tools", "check-edge-live")
    loader = SourceFileLoader("check_edge_live", caminho)
    spec = importlib.util.spec_from_loader("check_edge_live", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class TestResolucaoDeAlerta(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mod.HISTORICO = os.path.join(self.tmp.name, "edge_live.jsonl")
        self.avisos = []

        def avisar_falso(chave, severidade, titulo, mensagem, evidencia, resolvido=False):
            self.avisos.append({"chave": chave, "severidade": severidade, "resolvido": resolvido})

        self.mod.avisar = avisar_falso
        # Sondas: origem saudável e rápida. O que se mede aqui é a transição de
        # estado, não a rede.
        self.mod.sondar = lambda url, timeout=15: (200, 0.12, {}, None)
        self.mod.uma_pagina_do_acervo = lambda: "/familia/exemplo/"

    def grava_estado(self, ok, chave_alertada=None):
        with open(self.mod.HISTORICO, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ok": ok, "chave_alertada": chave_alertada}) + "\n")

    def roda(self):
        argv = sys.argv
        sys.argv = ["check-edge-live"]
        try:
            self.mod.main()
        except SystemExit:
            pass
        finally:
            sys.argv = argv

    def test_normalizacao_apos_alerta_emite_resolucao(self):
        """O caso que ficou 38h aberto: alerta antes, tudo bem agora."""
        self.grava_estado(ok=False, chave_alertada="borda-origem")
        self.roda()
        resolucoes = [a for a in self.avisos if a["resolvido"]]
        self.assertTrue(
            resolucoes,
            "condição curada não emitiu resolução — o ramo voltou a ser inalcançável",
        )
        self.assertEqual(resolucoes[0]["chave"], "borda-origem",
                         "a resolução tem de fechar a chave que foi alertada")

    def test_resolucao_fecha_a_chave_certa_quando_o_alerta_foi_borda_lenta(self):
        self.grava_estado(ok=False, chave_alertada="borda-lenta")
        self.roda()
        resolucoes = [a for a in self.avisos if a["resolvido"]]
        self.assertTrue(resolucoes, "sem resolução para borda-lenta")
        self.assertEqual(resolucoes[0]["chave"], "borda-lenta")

    def test_estado_ja_saudavel_nao_emite_nada(self):
        """Sem alerta aberto não há o que resolver: ruído também é defeito."""
        self.grava_estado(ok=True)
        self.roda()
        self.assertEqual(self.avisos, [], f"emitiu alerta sem motivo: {self.avisos}")

    def test_le_o_anterior_antes_de_gravar_o_atual(self):
        """A causa raiz, medida diretamente: o ledger cresce e o veredito não muda."""
        self.grava_estado(ok=False, chave_alertada="borda-origem")
        antes = sum(1 for _ in open(self.mod.HISTORICO, encoding="utf-8"))
        self.roda()
        depois = sum(1 for _ in open(self.mod.HISTORICO, encoding="utf-8"))
        self.assertEqual(depois, antes + 1, "o evento atual precisa ser gravado")
        self.assertTrue(
            [a for a in self.avisos if a["resolvido"]],
            "se a leitura voltasse para depois da gravação, o anterior seria o próprio "
            "evento novo (ok=true) e nenhuma resolução sairia",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
