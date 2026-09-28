#!/usr/bin/env python3
"""Testes de tools/generate-funil-de-maquina — a série do funil das portas de máquina.

O QUE ESTES TESTES GUARDAM, e é uma propriedade por vez:

1. AQUECIMENTO E SONDA INTERNA NÃO SÃO AUDIÊNCIA, mas também não somem: saem da
   conta e entram em `descartados`. Sem os dois lados, "zero uso" fica
   indistinguível de "o uso era nosso" — que é a contaminação que o anti-fraude
   do contrato proíbe.
2. A SÉRIE DECLARA A PRÓPRIA CEGUEIRA. `mcp_method` só existe no ledger do Go a
   partir de 2026-09-08; um dia anterior lê "0 tools/call" sem que ninguém tenha
   deixado de chamar. `cobertura_do_instrumento` é o que separa as duas coisas.
3. CONVERSÃO SEM DENOMINADOR É `null`, NUNCA 0.0. Gravar zero afirmaria que
   ninguém converteu, sobre um denominador que não existe.
4. O DIA VEM DO CARIMBO DA LINHA, não do nome do arquivo.

Rodar:
    python3 tools/test_generate_funil_de_maquina.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carrega_modulo():
    """Importa o gerador, que não tem extensão .py.

    `dont_write_bytecode` é obrigatório aqui: um .pyc obsoleto do mesmo tamanho
    e do mesmo segundo já cegou uma prova por mutação neste repositório — o
    loader servia o bytecode velho e o mutante "passava".
    """
    sys.dont_write_bytecode = True
    caminho = os.path.join(RAIZ, "tools/generate-funil-de-maquina")
    spec = importlib.util.spec_from_loader(
        "gerador_funil_de_maquina",
        importlib.machinery.SourceFileLoader("gerador_funil_de_maquina", caminho),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


GERADOR = carrega_modulo()


def linha(**campos):
    base = {"ts": "2026-09-10T12:00:00Z", "path": "/mcp", "method": "POST",
            "status": 200, "user_agent": "agente-de-teste/1.0"}
    base.update(campos)
    return base


def escreve_ledger(diretorio, nome, linhas):
    caminho = os.path.join(diretorio, nome)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for registro in linhas:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return caminho


class TestFunilDeMaquina(unittest.TestCase):
    def test_aquecimento_e_sonda_ficam_fora_da_conta_mas_contados(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-10.jsonl", [
                linha(mcp_method="tools/call", mcp_tool="buscar_paginas"),
                linha(mcp_method="tools/call", mcp_tool="buscar_paginas", warming=True),
                linha(mcp_method="tools/call", mcp_tool="buscar_paginas", bot_simulation=True),
            ])
            (dia,) = GERADOR.agrega([caminho])
        self.assertEqual(dia["uso"], 1, "aquecimento ou sonda entraram no uso")
        self.assertEqual(dia["portas"]["mcp"], 1)
        self.assertEqual(dia["descartados"],
                         {"aquecimento": 1, "sonda_interna": 1},
                         "o descarte tem de ficar visível, não sumir")

    def test_dia_sem_o_campo_declara_cobertura_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-01.jsonl", [
                linha(ts="2026-09-01T10:00:00Z"),
                linha(ts="2026-09-01T10:01:00Z"),
            ])
            (dia,) = GERADOR.agrega([caminho])
        self.assertEqual(dia["cobertura_do_instrumento"], 0.0)
        self.assertFalse(dia["instrumentado"],
                         "dia sem mcp_method não pode se declarar instrumentado")
        self.assertEqual(dia["uso"], 0)

    def test_cobertura_parcial_e_a_fracao_das_linhas_com_o_campo(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-08.jsonl", [
                linha(ts="2026-09-08T10:00:00Z", mcp_method="initialize"),
                linha(ts="2026-09-08T10:01:00Z", mcp_method="tools/list"),
                linha(ts="2026-09-08T10:02:00Z"),
                linha(ts="2026-09-08T10:03:00Z"),
            ])
            (dia,) = GERADOR.agrega([caminho])
        self.assertEqual(dia["cobertura_do_instrumento"], 0.5)
        self.assertFalse(dia["instrumentado"], "0,5 não é MAIS que 0,5")

    def test_conversao_sem_inventario_e_nula_e_nao_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-10.jsonl", [
                linha(mcp_method="initialize"),
            ])
            (dia,) = GERADOR.agrega([caminho])
        self.assertIsNone(dia["conversao_inventario_para_uso"],
                          "sem quem leia o inventário não há taxa de conversão")

    def test_conversao_e_uso_sobre_inventario(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-10.jsonl", [
                linha(mcp_method="tools/list"),
                linha(mcp_method="tools/list"),
                linha(mcp_method="tools/list"),
                linha(mcp_method="tools/list"),
                linha(mcp_method="tools/call", mcp_tool="search"),
            ])
            (dia,) = GERADOR.agrega([caminho])
        self.assertEqual(dia["inventario"], 4)
        self.assertEqual(dia["uso"], 1)
        self.assertEqual(dia["conversao_inventario_para_uso"], 0.25)

    def test_clientes_que_exerceram_conta_agentes_distintos(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-10.jsonl", [
                linha(mcp_method="tools/call", mcp_tool="search", user_agent="censo-a/1.0"),
                linha(mcp_method="tools/call", mcp_tool="search", user_agent="censo-a/1.0"),
                linha(mcp_method="tools/call", mcp_tool="fetch", user_agent="censo-b/1.0"),
                linha(mcp_method="tools/list", user_agent="censo-c/1.0"),
            ])
            (dia,) = GERADOR.agrega([caminho])
        self.assertEqual(dia["uso"], 3, "chamadas repetidas do mesmo agente contam todas")
        self.assertEqual(dia["clientes_que_exerceram_ferramenta"], 2,
                         "o que se conta aqui é AGENTE distinto, não chamada")
        self.assertEqual(dia["clientes_distintos"], 3)
        self.assertEqual(dia["ferramentas"], {"search": 2, "fetch": 1})

    def test_o_dia_vem_do_carimbo_da_linha_nao_do_nome_do_arquivo(self):
        # O ledger rotaciona por hora local: a última hora do dia cai no
        # arquivo do dia seguinte, e agrupar pelo nome do arquivo deslocaria
        # essas linhas em um dia inteiro.
        with tempfile.TemporaryDirectory() as tmp:
            caminho = escreve_ledger(tmp, "access-2026-09-10.jsonl", [
                linha(ts="2026-09-09T23:59:00Z", mcp_method="tools/call", mcp_tool="search"),
                linha(ts="2026-09-10T00:01:00Z", mcp_method="tools/call", mcp_tool="search"),
            ])
            serie = GERADOR.agrega([caminho])
        self.assertEqual([d["date"] for d in serie], ["2026-09-09", "2026-09-10"])

    def test_linha_ilegivel_e_contada_no_dia_do_arquivo(self):
        # O ledger do Go rasga em rajada: 173 linhas em 37 dias, 65 num dia só.
        # A linha rasgada não tem carimbo legível, então o dia vem do nome do
        # arquivo — e ela tem de aparecer, porque contagem que some sem rastro
        # faz "zero" e "não medido" parecerem a mesma coisa.
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "access-2026-09-10.jsonl")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(linha(mcp_method="tools/call", mcp_tool="search")) + "\n")
                arquivo.write('{"ts":"2026-09-10T16:53:24Z","method":"GET","pat\n')
                arquivo.write('h":"/consumidor/x/","status":200}\n')
            (dia,) = GERADOR.agrega([caminho])
        self.assertEqual(dia["descartados"].get("linha_ilegivel"), 2,
                         "linha rasgada tem de ser contada, nunca descartada em silêncio")
        self.assertEqual(dia["uso"], 1, "a linha boa continua contando")

    def test_porta_classifica_as_quatro_superficies(self):
        self.assertEqual(GERADOR.porta_de("/mcp"), "mcp")
        self.assertEqual(GERADOR.porta_de("/mcp/.well-known/mcp"), "mcp")
        self.assertEqual(GERADOR.porta_de("/a2a/v1"), "a2a")
        self.assertEqual(GERADOR.porta_de("/api/v1/search?q=x"), "api")
        self.assertEqual(GERADOR.porta_de("/familia/divorcio/index.md"), "gemea")
        self.assertIsNone(GERADOR.porta_de("/familia/divorcio/"),
                          "HTML humano não é porta de máquina")
        # Feed incremental e descritor são porta: nenhum serve leitor humano.
        self.assertEqual(GERADOR.porta_de("/changes.json"), "feed")
        self.assertEqual(GERADOR.porta_de("/.well-known/mcp"), "descritor")
        # E a precedência não muda: /mcp/.well-known/* continua sendo do MCP,
        # que é quem o serve.
        self.assertEqual(GERADOR.porta_de("/mcp/.well-known/mcp"), "mcp")

    def test_hash_de_fonte_ausente_diz_que_nao_leu(self):
        self.assertEqual(GERADOR.sha256_do_arquivo("/caminho/que/nao/existe"), "",
                         "hash vazio DIZ que não deu para ler; nunca se finge um")
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as arquivo:
            arquivo.write("conteudo\n")
            caminho = arquivo.name
        try:
            digest = GERADOR.sha256_do_arquivo(caminho)
            self.assertEqual(len(digest), 64)
            self.assertEqual(digest, GERADOR.sha256_do_arquivo(caminho))
        finally:
            os.unlink(caminho)


if __name__ == "__main__":
    unittest.main()
