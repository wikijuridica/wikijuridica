#!/usr/bin/env python3
"""Bancada de tools/listar-produtores-de-pagina.

O QUE ELA PRENDE. O runner da onda diaria DERIVA o mapa de geradores deste
comando. Duas falhas dele publicam a menos em silencio, que e o defeito que a
frente inteira existe para matar:

  - mapa PARCIAL (linha malformada ignorada): o canal correspondente para de
    publicar e o log fica verde;
  - MENCAO lida como REGISTRO (nome do comando num comentario ou num campo
    livre): produtor orfao passa por registrado.

Uso: python3 tools/test_listar_produtores_de_pagina.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
COMANDO = os.path.join(RAIZ, "tools", "listar-produtores-de-pagina")

LINHA_ALFA = {
    "canal": "alfa", "cmd": "./cmd/generate-alfa-pages",
    "shard": "data/editorial/v2_pages/alfa-01.jsonl",
    "portfolio": "data/editorial/portfolio_v2/alfa-01.jsonl",
    "gatilho": "onda-diaria", "limite_env": "WIKI_LIMITE_ALFA", "limite_padrao": 40,
}
LINHA_BETA = {
    "canal": "beta", "cmd": "./cmd/generate-beta-pages",
    "shard": "data/editorial/v2_pages/beta-01.jsonl",
    "portfolio": "data/editorial/portfolio_v2/beta-01.jsonl",
    "gatilho": "publicador-cerebro", "limite_env": "WIKI_LIMITE_BETA", "limite_padrao": 30,
}


def raiz_com(*linhas: str) -> str:
    raiz = tempfile.mkdtemp(prefix="produtores-")
    os.makedirs(os.path.join(raiz, "ops"), exist_ok=True)
    with open(os.path.join(raiz, "ops", "produtores-de-pagina.jsonl"), "w", encoding="utf-8") as saida:
        saida.write("\n".join(linhas) + "\n")
    return raiz


def roda(raiz: str, *argumentos: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, COMANDO, "--raiz", raiz, *argumentos],
                          capture_output=True, text=True)


class TesteDerivacao(unittest.TestCase):
    def test_filtra_por_gatilho(self):
        raiz = raiz_com(json.dumps(LINHA_ALFA), json.dumps(LINHA_BETA))
        resultado = roda(raiz, "--gatilho", "onda-diaria")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        linhas = resultado.stdout.strip().split("\n")
        self.assertEqual(len(linhas), 1, resultado.stdout)
        self.assertEqual(linhas[0].split("\t")[0], "alfa")
        self.assertEqual(linhas[0].split("\t")[4], "WIKI_LIMITE_ALFA")
        self.assertEqual(linhas[0].split("\t")[5], "40")

    def test_ordem_das_colunas_e_contrato(self):
        """O runner le por INDICE. Trocar a ordem aqui trocaria o comando pelo shard."""
        raiz = raiz_com(json.dumps(LINHA_ALFA))
        campos = roda(raiz, "--gatilho", "onda-diaria").stdout.strip().split("\t")
        self.assertEqual(campos, ["alfa", "./cmd/generate-alfa-pages",
                                  "data/editorial/v2_pages/alfa-01.jsonl",
                                  "data/editorial/portfolio_v2/alfa-01.jsonl",
                                  "WIKI_LIMITE_ALFA", "40"])

    def test_comentario_nao_registra(self):
        """A linha INTEIRA e valida -- atras de um `#`. Nao pode virar produtor."""
        raiz = raiz_com(json.dumps(LINHA_ALFA), "# " + json.dumps(LINHA_BETA),
                        "#   ./cmd/generate-beta-pages roda todo dia, prometo")
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertNotIn("beta", resultado.stdout)
        self.assertEqual(len(resultado.stdout.strip().split("\n")), 1)

    def test_campo_livre_nao_registra(self):
        entrada = dict(LINHA_ALFA, nota="roda junto com ./cmd/generate-beta-pages")
        raiz = raiz_com(json.dumps(entrada))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(len(resultado.stdout.strip().split("\n")), 1)
        self.assertNotIn("generate-beta-pages", resultado.stdout)

    def test_linha_malformada_aborta_em_vez_de_devolver_mapa_parcial(self):
        raiz = raiz_com(json.dumps(LINHA_ALFA), '{"canal":"beta",')
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1, resultado.stdout)
        self.assertIn("JSON invalido", resultado.stderr)
        self.assertEqual(resultado.stdout, "",
                         "mapa PARCIAL e canal que para de publicar em silencio")

    def test_campo_fora_do_contrato_aborta(self):
        raiz = raiz_com(json.dumps(dict(LINHA_ALFA, limte_padrao=99)))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("fora do contrato", resultado.stderr)

    def test_gatilho_ausente_aborta(self):
        raiz = raiz_com(json.dumps(dict(LINHA_ALFA, gatilho="")))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1, resultado.stdout)
        self.assertIn("obrigatorio", resultado.stderr)

    def test_gatilho_inventado_aborta(self):
        raiz = raiz_com(json.dumps(dict(LINHA_ALFA, gatilho="quando-der")))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("conjunto fechado", resultado.stderr)

    def test_canal_repetido_aborta(self):
        raiz = raiz_com(json.dumps(LINHA_ALFA), json.dumps(dict(LINHA_BETA, canal="alfa")))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("ja declarado na linha", resultado.stderr)

    def test_canal_com_espaco_aborta(self):
        """A chave do array associativo do shell nao pode ter espaco: foi assim
        que o shfmt cegou o canal diario por cinco dias (d4c942f2)."""
        raiz = raiz_com(json.dumps(dict(LINHA_ALFA, canal="stj tema")))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("tem espaco", resultado.stderr)

    def test_limite_padrao_zero_aborta(self):
        raiz = raiz_com(json.dumps(dict(LINHA_ALFA, limite_padrao=0)))
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("inteiro positivo", resultado.stderr)

    def test_registro_so_com_comentario_aborta(self):
        raiz = raiz_com("# so comentario aqui")
        resultado = roda(raiz, "--todos")
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("NENHUM produtor", resultado.stderr)


class TesteRegistroReal(unittest.TestCase):
    def test_registro_do_repo_deriva_os_sete_produtores(self):
        onda = roda(RAIZ, "--gatilho", "onda-diaria")
        self.assertEqual(onda.returncode, 0, onda.stderr)
        canais_da_onda = [linha.split("\t")[0] for linha in onda.stdout.strip().split("\n")]
        self.assertEqual(sorted(canais_da_onda),
                         ["diarios", "leis", "noticias", "stf-informativo", "stj-sumula", "stj-tema"])

        cerebro = roda(RAIZ, "--gatilho", "publicador-cerebro")
        self.assertEqual(cerebro.returncode, 0, cerebro.stderr)
        canais_do_cerebro = [linha.split("\t")[0] for linha in cerebro.stdout.strip().split("\n")]
        self.assertEqual(canais_do_cerebro, ["acordaos"],
                         "generate-acordao-pages NAO entra na onda diaria: e o motor do P6")

        todos = roda(RAIZ, "--todos")
        self.assertEqual(len(todos.stdout.strip().split("\n")), 7)

    def test_cada_cmd_do_registro_existe_no_disco(self):
        for linha in roda(RAIZ, "--todos").stdout.strip().split("\n"):
            cmd = linha.split("\t")[1]
            caminho = os.path.join(RAIZ, cmd[len("./"):])
            self.assertTrue(os.path.isdir(caminho), f"{cmd} nao existe: o runner falharia em runtime")


if __name__ == "__main__":
    unittest.main(verbosity=2)
