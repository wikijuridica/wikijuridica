#!/usr/bin/env python3
"""Testes de tools/generate-datasets-publicos — os dumps publicos para IA.

Fixtures REAIS, recortadas do repositorio no setUp (nunca sinteticas): 2 arquivos
mensais do corpus do STJ + manifest, todas as extracoes por LLM, um grafo.sqlite
com os primeiros 300 nos reais e as arestas entre eles, 40 linhas do indice de
co-citacao, 60 linhas do published_manifest com as paginas correspondentes de
content/pages.json e o site.json. O produtor roda de verdade (subprocess) numa
raiz temporaria e a purga da borda e substituida por um registrador.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-datasets-publicos"


def modulo():
    loader = importlib.machinery.SourceFileLoader("gdp", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader("gdp", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m


def le_gz(caminho):
    with gzip.open(caminho, "rt", encoding="utf-8") as handle:
        return [json.loads(l) for l in handle if l.strip()]


def monta_raiz(tmp):
    tmp = pathlib.Path(tmp)
    corpus = RAIZ / "data" / "corpus" / "jurisprudencia" / "stj-espelhos"
    dest = tmp / "data" / "corpus" / "jurisprudencia" / "stj-espelhos"
    dest.mkdir(parents=True)
    mensais = sorted(f for f in os.listdir(corpus) if f.startswith("registros-"))[:2]
    for f in mensais + ["manifest.jsonl"]:
        shutil.copyfile(corpus / f, dest / f)
    (tmp / "data" / "ai").mkdir(parents=True)
    shutil.copyfile(RAIZ / "data" / "ai" / "extracoes_dispositivos.jsonl", tmp / "data" / "ai" / "extracoes_dispositivos.jsonl")
    # grafo real recortado: 300 primeiros nos por chave + arestas internas
    origem = sqlite3.connect("file:%s?mode=ro" % (RAIZ / "data" / "ai" / "grafo.sqlite"), uri=True)
    alvo = sqlite3.connect(str(tmp / "data" / "ai" / "grafo.sqlite"))
    for (sql,) in origem.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('nos','arestas')"):
        alvo.execute(sql)
    # recorte REAL com todos os tipos: 40 nos por tipo em ordem de chave (so
    # "ORDER BY chave LIMIT 300" devolvia 300 acordaos e nenhuma norma)
    nos = []
    for (tipo,) in origem.execute("SELECT DISTINCT tipo FROM nos ORDER BY tipo"):
        nos += origem.execute("SELECT id, tipo, chave, rotulo, atributos FROM nos WHERE tipo=? ORDER BY chave LIMIT 40", (tipo,)).fetchall()
    ids = {n[0] for n in nos}
    alvo.executemany("INSERT INTO nos(id,tipo,chave,rotulo,atributos) VALUES (?,?,?,?,?)", nos)
    for a in origem.execute("SELECT origem,destino,tipo,peso,fonte,evidencia FROM arestas"):
        if a[0] in ids and a[1] in ids:
            alvo.execute("INSERT INTO arestas(origem,destino,tipo,peso,fonte,evidencia) VALUES (?,?,?,?,?,?)", a)
    alvo.commit(); alvo.close(); origem.close()
    (tmp / "content").mkdir()
    shutil.copyfile(RAIZ / "content" / "site.json", tmp / "content" / "site.json")
    wd = RAIZ / "data" / "corpus" / "wikidata" / "lexml_qids.jsonl"
    if wd.is_file():
        (tmp / "data" / "corpus" / "wikidata").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(wd, tmp / "data" / "corpus" / "wikidata" / "lexml_qids.jsonl")
    with open(RAIZ / "content" / "legal_cocitation_index.jsonl", encoding="utf-8") as src, \
            open(tmp / "content" / "legal_cocitation_index.jsonl", "w", encoding="utf-8") as dst:
        for i, l in enumerate(src):
            if i >= 40:
                break
            dst.write(l)
    (tmp / "data" / "editorial").mkdir()
    manifesto = []
    with open(RAIZ / "data" / "editorial" / "published_manifest.jsonl", encoding="utf-8") as src:
        for i, l in enumerate(src):
            if i >= 60:
                break
            manifesto.append(json.loads(l))
    with open(tmp / "data" / "editorial" / "published_manifest.jsonl", "w", encoding="utf-8") as dst:
        for m in manifesto:
            dst.write(json.dumps(m, ensure_ascii=False) + "\n")
    caminhos = {m["path"] for m in manifesto}
    with open(RAIZ / "content" / "pages.json", encoding="utf-8") as src:
        paginas = [p for p in json.load(src) if p.get("path") in caminhos]
    # uma pagina do manifesto fica FORA de pages.json de proposito: nao pode sair no dump
    paginas = paginas[:-1]
    with open(tmp / "content" / "pages.json", "w", encoding="utf-8") as dst:
        json.dump(paginas, dst, ensure_ascii=False)
    return tmp, manifesto, {p["path"] for p in paginas}


class TesteDatasetsPublicos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.raiz, cls.manifesto, cls.paginas = monta_raiz(cls.tmpdir.name)
        cls.m = modulo()
        cls.purgas = []
        cls.saida = cls.m.gera(str(cls.raiz), "2026-09-08", purgar=cls.purgas.append)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def arquivo(self, nome):
        d = [x for x in self.saida["datasets"] if x["nome"] == nome][0]
        return d, self.raiz / "public" / "datasets" / d["arquivo"]

    def test_sha256_do_manifesto_bate_com_o_arquivo(self):
        for d in self.saida["datasets"]:
            caminho = self.raiz / "public" / "datasets" / d["arquivo"]
            self.assertEqual(hashlib.sha256(caminho.read_bytes()).hexdigest(), d["sha256"], d["nome"])
            self.assertEqual(caminho.stat().st_size, d["bytes"])
            self.assertEqual(len(le_gz(caminho)), d["registros"])
        manifesto = json.loads((self.raiz / "public" / "datasets" / "datasets.json").read_text(encoding="utf-8"))
        self.assertEqual([d["sha256"] for d in manifesto["datasets"]], [d["sha256"] for d in self.saida["datasets"]])
        self.assertEqual(self.purgas, [manifesto["base_url"] + "/datasets/datasets.json"])

    def test_deterministico_na_segunda_execucao(self):
        antes = {d["nome"]: d["sha256"] for d in self.saida["datasets"]}
        de_novo = self.m.gera(str(self.raiz), "2026-09-08", purgar=lambda url: None)
        self.assertEqual({d["nome"]: d["sha256"] for d in de_novo["datasets"]}, antes)

    def test_acervo_e_a_intersecao_manifesto_x_paginas(self):
        d, caminho = self.arquivo("acervo-metadados")
        regs = le_gz(caminho)
        esperado = sorted(m["path"] for m in self.manifesto
                          if m["path"] in self.paginas and m.get("page_status") == "published" and m.get("index_policy") == "index")
        self.assertEqual([r["path"] for r in regs], esperado)
        self.assertLess(len(esperado), len(self.manifesto), "a pagina fora de pages.json tinha de ficar de fora")
        for r in regs:
            self.assertTrue(r["html_sha256"] and r["url"].startswith("https://"))
            self.assertNotIn("body", r); self.assertNotIn("sections", r)
            self.assertTrue(r["citar_url"].endswith("/api/v1/citar" + r["path"]))

    def test_extracoes_ultima_linha_por_chave(self):
        d, caminho = self.arquivo("extracoes-dispositivos")
        regs = le_gz(caminho)
        chaves = [r["chave"] for r in regs]
        self.assertEqual(len(chaves), len(set(chaves)))
        ultima = {}
        with open(self.raiz / "data" / "ai" / "extracoes_dispositivos.jsonl", encoding="utf-8") as handle:
            for l in handle:
                if l.strip():
                    r = json.loads(l); ultima[r["chave"]] = r
        # A ULTIMA linha vence, e a comparacao e do registro inteiro: nas 13
        # chaves reprocessadas de 2026-09-08 a primeira e a ultima extracao
        # diferem em conteudo (dispositivos/modelo), entao "primeira vence"
        # reprova aqui — e o texto_sha256 sozinho nao distinguiria as duas.
        self.assertEqual({r["chave"]: json.dumps(r, sort_keys=True) for r in regs},
                         {k: json.dumps(v, sort_keys=True) for k, v in ultima.items()})

    def test_corpus_stj_carrega_proveniencia_e_licenca(self):
        d, caminho = self.arquivo("stj-espelhos-acordaos")
        regs = le_gz(caminho)
        self.assertGreater(len(regs), 100)
        for r in regs[:20]:
            self.assertTrue(r["_proveniencia"]["url_fonte"].startswith("https://dadosabertos.web.stj.jus.br/"))
            self.assertIn("CC-BY", r["_proveniencia"]["licenca"].upper().replace("ATRIBUI", "CC-BY"))

    def test_grafo_nos_e_arestas_por_chave(self):
        _, nos = self.arquivo("grafo-juridico-nos")
        _, arestas = self.arquivo("grafo-juridico-arestas")
        chaves = {n["chave"] for n in le_gz(nos)}
        self.assertGreaterEqual(len(chaves), 200)
        for a in le_gz(arestas):
            self.assertIn(a["origem"], chaves); self.assertIn(a["destino"], chaves)

    def test_normas_do_grafo_carregam_o_qid_do_wikidata(self):
        """sameAs so onde o Wikidata (P9119) conhece a URN base; artigo herda o QID
        do diploma; tipos que nao sao norma/dispositivo nunca ganham QID."""
        _, nos = self.arquivo("grafo-juridico-nos")
        regs = le_gz(nos)
        qids = self.m.wikidata_por_urn(str(self.raiz))
        com = [n for n in regs if n.get("wikidata_qid")]
        self.assertGreater(len(com), 0, "nenhum no do recorte real casou com o Wikidata")
        for n in regs:
            esperado = qids.get(self.m.urn_base_da_chave(n["chave"])) if n["tipo"] in ("norma", "dispositivo") else None
            self.assertEqual(n.get("wikidata_qid"), esperado, n["chave"])
            if esperado:
                self.assertEqual(n["sameAs"], "https://www.wikidata.org/wiki/" + esperado)

    def test_versoes_antigas_sao_podadas(self):
        for data in ("2026-09-01", "2026-09-02", "2026-09-03"):
            self.m.gera(str(self.raiz), data, purgar=lambda url: None)
        pasta = self.raiz / "public" / "datasets"
        versoes = sorted(f for f in os.listdir(pasta) if f.startswith("acervo-metadados-"))
        self.assertEqual(len(versoes), self.m.MANTER_VERSOES)
        self.assertNotIn("acervo-metadados-20260901.jsonl.gz", versoes)


if __name__ == "__main__":
    unittest.main()
