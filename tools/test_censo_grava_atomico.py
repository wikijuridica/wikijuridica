#!/usr/bin/env python3
"""O censo de severidade nunca é publicado pela metade.

★ O DEFEITO (medido em 2026-09-16)

`tools/generate-v2-publication-severity` gravava com `open(OUT, "w")`, que
TRUNCA o arquivo antes de escrever os ~5 MB de volta. Quem lê esse arquivo é
`internal/v2publish.LoadSeverity` (v2publish.go:239), **durante a publicação**.
Leitor que pegue a janela vê um censo parcial; `SelectPublishable`
(v2publish.go:391) pula com `sem_linha_no_censo` todo intent que faltar, e o
publicador reescreve o `published_manifest` a partir do que sobrou — o estado
que `cmd/publish-v2-direct` documenta como "o servidor não sobe".

A janela existia desde sempre e passou a importar quando
`tools/deploy-publico` ganhou o passo `0.5/7`, que regenera o censo dentro do
deploy. Fechar a janela é pré-requisito daquele passo, não enfeite.

★ COMO O TESTE MEDE, SEM DEPENDER DE RELÓGIO

A observação é feita DE DENTRO do escritor: enquanto a gravação está em curso,
o teste lê o caminho vivo e exige encontrar o conteúdo ANTIGO inteiro. Isso é
determinístico — não há corrida para vencer nem espera para calibrar.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CENSO = RAIZ / "tools" / "generate-v2-publication-severity"


def carrega(caminho: pathlib.Path):
    spec = importlib.util.spec_from_loader(
        "censo_sob_teste",
        importlib.machinery.SourceFileLoader("censo_sob_teste", str(caminho)))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def grava_truncando(caminho, escritor):
    """O comportamento ANTIGO, para servir de mutante."""
    with open(caminho, "w", encoding="utf-8") as handle:
        escritor(handle)


class GravacaoAtomica(unittest.TestCase):

    def observa_durante_a_escrita(self, gravador) -> list[str]:
        """Devolve o que um leitor concorrente veria no meio da gravação."""
        observado: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            alvo = os.path.join(tmp, "censo.jsonl")
            with open(alvo, "w", encoding="utf-8") as handle:
                handle.write("ANTIGO INTEIRO\n")

            def escritor(handle):
                handle.write('{"intent_id":"novo"}\n')
                with open(alvo, encoding="utf-8") as leitor:
                    observado.append(leitor.read())

            gravador(alvo, escritor)
            with open(alvo, encoding="utf-8") as leitor:
                observado.append(leitor.read())
        return observado

    def test_leitor_concorrente_ve_o_arquivo_antigo_inteiro(self):
        modulo = carrega(CENSO)
        durante, depois = self.observa_durante_a_escrita(modulo.grava_atomico)
        self.assertEqual(durante, "ANTIGO INTEIRO\n",
                         "um leitor concorrente viu o censo pela metade")
        self.assertEqual(depois, '{"intent_id":"novo"}\n')

    def test_mutante_que_trunca_no_lugar_morre(self):
        """Mutante: volta o `open(caminho, 'w')` direto."""
        durante, _ = self.observa_durante_a_escrita(grava_truncando)
        self.assertNotEqual(
            durante, "ANTIGO INTEIRO\n",
            "o mutante deveria expor o arquivo truncado; se nao expoe, o teste "
            "acima nao estava medindo atomicidade")
        self.assertEqual(durante, "", "o truncamento deixa o arquivo vazio")

    def test_falha_no_meio_preserva_o_arquivo_vivo(self):
        modulo = carrega(CENSO)
        with tempfile.TemporaryDirectory() as tmp:
            alvo = os.path.join(tmp, "censo.jsonl")
            with open(alvo, "w", encoding="utf-8") as handle:
                handle.write("ANTIGO INTEIRO\n")

            def escritor_que_falha(handle):
                handle.write("meia linha")
                raise RuntimeError("disco cheio")

            with self.assertRaises(RuntimeError):
                modulo.grava_atomico(alvo, escritor_que_falha)
            with open(alvo, encoding="utf-8") as leitor:
                self.assertEqual(leitor.read(), "ANTIGO INTEIRO\n")
            restos = [nome for nome in os.listdir(tmp) if "parcial" in nome]
            self.assertEqual(restos, [], "sobrou arquivo parcial no disco")

    def test_o_modo_do_arquivo_anterior_e_preservado(self):
        """O censo vive 0600; gravação nova não pode abrir permissão."""
        modulo = carrega(CENSO)
        with tempfile.TemporaryDirectory() as tmp:
            alvo = os.path.join(tmp, "censo.jsonl")
            with open(alvo, "w", encoding="utf-8") as handle:
                handle.write("antigo\n")
            os.chmod(alvo, 0o600)
            modulo.grava_atomico(alvo, lambda handle: handle.write("novo\n"))
            self.assertEqual(os.stat(alvo).st_mode & 0o777, 0o600)

    def test_o_censo_usa_a_gravacao_atomica_nas_duas_saidas(self):
        fonte = CENSO.read_text(encoding="utf-8")
        self.assertIn("grava_atomico(OUT, escreve_censo)", fonte)
        self.assertIn("grava_atomico(SUMMARY_OUT, escreve_resumo)", fonte)
        self.assertNotIn('with open(OUT, "w"', fonte,
                         "voltou a truncar o censo no lugar")
        self.assertNotIn('with open(SUMMARY_OUT, "w"', fonte)

    def test_o_resumo_continua_json_valido(self):
        modulo = carrega(CENSO)
        with tempfile.TemporaryDirectory() as tmp:
            alvo = os.path.join(tmp, "resumo.json")
            modulo.grava_atomico(
                alvo, lambda handle: json.dump({"records": 3}, handle))
            with open(alvo, encoding="utf-8") as leitor:
                self.assertEqual(json.load(leitor), {"records": 3})


if __name__ == "__main__":
    unittest.main(verbosity=2)
