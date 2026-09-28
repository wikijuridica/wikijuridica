#!/usr/bin/env python3
"""Testes de tools/generate-risco-superacao sobre um grafo SQLite sintetico de
5 nos e 4 arestas, com contagem independente do esperado.

Cenario: pagina P cita o dispositivo D (norma_base N). Acordao A1 (2022-06-21)
cita D; acordao A2 (2026-09-01) cita a norma N inteira e a Sumula 7; acordao A3
cita D mas nao tem data (fica fora dos posteriores); A4 (2026-08-26, a data da
ancora) cita D e fica fora por ser igual, nao posterior. Ancora de P em
2026-08-26. Esperado: total 4, posteriores 1 (A2, laco norma, peso 0,2),
recencia 1.0 (7 dias em 2026-09-08), risco = min(1, 0.2/5) * 1.0 = 0.04, e a
explicacao cita a Sumula 7.
Mutacao coberta: trocar `>` por `>=` na comparacao de datas ou esquecer a
norma_base muda os numeros abaixo.
"""
from __future__ import annotations

import datetime
import importlib.machinery
import importlib.util
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GERADOR = RAIZ / "tools" / "generate-risco-superacao"


def carrega():
    loader = importlib.machinery.SourceFileLoader("gen_risco", str(GERADOR))
    spec = importlib.util.spec_from_loader("gen_risco", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def monta_grafo(caminho):
    db = sqlite3.connect(caminho)
    db.executescript("""
    create table nos (id integer primary key, tipo text, chave text unique, rotulo text, atributos text);
    create table arestas (origem integer, destino integer, tipo text, peso real default 1, fonte text default '', evidencia text default '');
    """)
    nos = [
        (1, "pagina", "/familia/p/", "P", json.dumps({"area": "familia"})),
        (2, "dispositivo", "urn:lex:br:federal:lei:2002-01-10;10406!art1694", "art. 1.694", json.dumps({"norma_base": "urn:lex:br:federal:lei:2002-01-10;10406"})),
        (3, "norma", "urn:lex:br:federal:lei:2002-01-10;10406", "Lei 10.406/2002", "{}"),
        (4, "acordao", "acordao:STJ:1", "REsp 1", json.dumps({"data_julgamento": "2022-06-21", "fonte_url": "https://dadosabertos.web.stj.jus.br/x"})),
        (5, "acordao", "acordao:STJ:2", "REsp 2", json.dumps({"data_julgamento": "2026-09-01", "fonte_url": "https://dadosabertos.web.stj.jus.br/y"})),
        (6, "acordao", "acordao:STJ:3", "REsp 3", json.dumps({})),
        (7, "sumula", "sumula:STJ:7", "Súmula 7 do STJ", "{}"),
        (8, "acordao", "acordao:STJ:4", "REsp 4", json.dumps({"data_julgamento": "2026-08-26"})),  # mesma data da ancora: fica fora
    ]
    db.executemany("insert into nos values (?,?,?,?,?)", nos)
    arestas = [(1, 2, "cita"), (4, 2, "cita"), (5, 3, "cita"), (5, 7, "cita"), (6, 2, "cita"), (8, 2, "cita")]
    db.executemany("insert into arestas(origem,destino,tipo) values (?,?,?)", arestas)
    db.commit()
    return db


class TestRiscoSuperacao(unittest.TestCase):
    def test_calculo_conta_so_posteriores_e_norma_base(self):
        mod = carrega()
        with tempfile.TemporaryDirectory() as d:
            db = monta_grafo(str(pathlib.Path(d) / "g.sqlite"))
            saida = mod.calcula(db, {"/familia/p/": ("2026-08-26", "approved_at")}, datetime.date(2026, 9, 8))
        self.assertEqual(len(saida), 1)
        r = saida[0]
        self.assertEqual(r["acordaos_total"], 4)
        self.assertEqual(r["acordaos_apos_revisao"], 1)  # A2; A4 tem a data da ancora e fica fora (mutacao > para >= derruba)
        self.assertEqual(r["mais_recente"], "2026-09-01")
        self.assertEqual(r["peso_apos_revisao"], 0.2)  # A2 cita so a norma inteira
        self.assertEqual(r["risco"], 0.04)
        self.assertEqual(r["ancora_origem"], "approved_at")
        self.assertTrue(r["medido"])
        self.assertIn("Súmula 7", r["explicacao"])
        self.assertEqual(r["fontes"][0]["chave"], "acordao:STJ:2")
        self.assertEqual(r["fontes"][0]["via"], ["urn:lex:br:federal:lei:2002-01-10;10406!art1694"])  # via = dispositivo DA PAGINA que liga ao acordao

    def test_sem_revisao_ou_sem_acordao_nao_gera_linha(self):
        mod = carrega()
        with tempfile.TemporaryDirectory() as d:
            db = monta_grafo(str(pathlib.Path(d) / "g.sqlite"))
            self.assertEqual(mod.calcula(db, {}, datetime.date(2026, 9, 8)), [])

    def test_recencia_decai_por_idade(self):
        mod = carrega()
        with tempfile.TemporaryDirectory() as d:
            db = monta_grafo(str(pathlib.Path(d) / "g.sqlite"))
            r = mod.calcula(db, {"/familia/p/": ("2022-01-01", "reviewed_at")}, datetime.date(2026, 9, 8))[0]
        # posteriores: A1 (2022, dispositivo, 1.0), A2 (2026, norma, 0.2), A4 (2026-08-26, dispositivo, 1.0) = 2.2; recencia 1.0
        self.assertEqual(r["acordaos_apos_revisao"], 3)
        self.assertEqual(r["risco"], 0.44)
        with tempfile.TemporaryDirectory() as d:
            db = monta_grafo(str(pathlib.Path(d) / "g.sqlite"))
            r = mod.calcula(db, {"/familia/p/": ("2022-01-01", "reviewed_at")}, datetime.date(2027, 10, 15))[0]
        self.assertEqual(r["risco"], 0.22)  # 2.2/5 * 0.5 (409 dias: entre 366 e 730; apagar a faixa 0,5 derruba)
        with tempfile.TemporaryDirectory() as d:
            db = monta_grafo(str(pathlib.Path(d) / "g.sqlite"))
            r = mod.calcula(db, {"/familia/p/": ("2022-01-01", "reviewed_at")}, datetime.date(2029, 9, 8))[0]
        self.assertEqual(r["risco"], 0.11)  # 2.2/5 * 0.25

    def test_ancora_prefere_checked_at_da_proveniencia(self):
        mod = carrega()
        self.assertEqual(mod.ancora_da_pagina({"reviewed_at": "2026-08-26", "approved_at": "2026-08-06",
                                              "source_provenance": [{"checked_at": "2026-07-31"}, {"checked_at": "2026-07-29T10:00:00Z"}]}),
                         ("2026-07-29", "source_provenance.checked_at"))
        self.assertEqual(mod.ancora_da_pagina({"reviewed_at": "2026-08-26", "approved_at": "2026-08-06"}), ("2026-08-06", "approved_at"))
        self.assertEqual(mod.ancora_da_pagina({"reviewed_at": "2026-08-26"}), ("2026-08-26", "reviewed_at"))

    def test_cli_escreve_jsonl_deterministico(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = pathlib.Path(d)
            (raiz / "data" / "ai").mkdir(parents=True)
            (raiz / "data" / "editorial").mkdir(parents=True)
            monta_grafo(str(raiz / "data" / "ai" / "grafo.sqlite")).close()
            (raiz / "data" / "editorial" / "published_manifest.jsonl").write_text(
                json.dumps({"path": "/familia/p/", "reviewed_at": "2026-08-26T10:00:00-03:00"}) + "\n")
            proc = subprocess.run([sys.executable, str(GERADOR), "--root", str(raiz), "--hoje", "2026-09-08"], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            linhas = (raiz / "data" / "ai" / "risco_superacao.jsonl").read_text().splitlines()
            self.assertEqual(len(linhas), 1)
            r = json.loads(linhas[0])
            self.assertEqual(r["schema_version"], "risco_superacao_v1")
            self.assertEqual(r["risco"], 0.04)
            self.assertEqual(r["reviewed_at"], "2026-08-26")


if __name__ == "__main__":
    unittest.main()
