#!/usr/bin/env python3
"""Testes de tools/generate-grafo-juridico e tools/consultar-grafo.

Fixture REAL e pequena em tools/testdata/grafo_juridico/ — 30 linhas de
content/legal_cocitation_index.jsonl, 30 de data/source-snapshots/manifest.jsonl
(com duas linhas de revogado_por reais — uma resolvivel contra outra norma da
propria fixture, outra propositalmente NAO resolvivel porque o alvo nunca foi
coletado pelo oraculo — e uma sumula do STF, com o blob copiado), 5 de
data/editorial/published_manifest.jsonl (so as 5 primeiras paginas do recorte
de cocitacao — as outras 25 ficam SEM no de pagina de proposito, para provar
que o gerador descarta aresta orfa em vez de inventar no) e 12 de
data/source-registry/stj_precedentes_qualificados.jsonl (incluindo um par
(tipo,numero) duplicado, para provar que a chave natural colapsa
deterministicamente).

Os numeros esperados abaixo vieram de uma contagem INDEPENDENTE sobre os
proprios arquivos de fixture (nao do modulo sob teste) — qualquer um pode
reproduzi-la lendo tools/testdata/grafo_juridico/*.jsonl com um
`json.loads` por linha.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FIXTURE_DIR = RAIZ / "tools" / "testdata" / "grafo_juridico"
GERADOR_PATH = RAIZ / "tools" / "generate-grafo-juridico"
CONSULTAR_PATH = RAIZ / "tools" / "consultar-grafo"


def carrega(caminho, nome):
    loader = importlib.machinery.SourceFileLoader(nome, str(caminho))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def montar_root_fixture(destino):
    """Copia os 4 arquivos de fixture (+ blob da sumula) para a estrutura de
    diretorio que o gerador espera sob --root."""
    (destino / "content").mkdir(parents=True, exist_ok=True)
    (destino / "data" / "source-snapshots" / "blobs" / "3b").mkdir(parents=True, exist_ok=True)
    (destino / "data" / "source-registry").mkdir(parents=True, exist_ok=True)
    (destino / "data" / "editorial").mkdir(parents=True, exist_ok=True)

    shutil.copy(
        FIXTURE_DIR / "legal_cocitation_index_sample.jsonl",
        destino / "content" / "legal_cocitation_index.jsonl",
    )
    shutil.copy(
        FIXTURE_DIR / "oraculo_manifest_sample.jsonl",
        destino / "data" / "source-snapshots" / "manifest.jsonl",
    )
    shutil.copy(
        FIXTURE_DIR / "stj_precedentes_sample.jsonl",
        destino / "data" / "source-registry" / "stj_precedentes_qualificados.jsonl",
    )
    shutil.copy(
        FIXTURE_DIR / "published_manifest_sample.jsonl",
        destino / "data" / "editorial" / "published_manifest.jsonl",
    )
    blob_nome = "3b0398e5de56b22ed2f630b70a3b29dc3856d92a6438d87d5f52ca0e5bac08aa.blob"
    shutil.copy(
        FIXTURE_DIR / "blobs" / "3b" / blob_nome,
        destino / "data" / "source-snapshots" / "blobs" / "3b" / blob_nome,
    )


def montar_root_fixture_com_acordaos(destino):
    """Igual a montar_root_fixture, mais o diretorio de espelhos do STJ com
    os 6 acordaos reais de tools/testdata/grafo_juridico/stj_espelhos_sample.jsonl
    (4 com dispositivos_citados_urn, 2 sem)."""
    montar_root_fixture(destino)
    espelhos_dir = destino / "data" / "corpus" / "jurisprudencia" / "stj-espelhos"
    espelhos_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURE_DIR / "stj_espelhos_sample.jsonl",
        espelhos_dir / "registros-fixture.jsonl",
    )
    # Fonte 6: extracoes por LLM. 3 linhas: duas para 000813705 (a segunda vence
    # e traz art. 1.022 do CPC + Sumula 7; a primeira, Sumula 182, tem de sumir)
    # e uma para 999999999, que nao existe na fonte 5 e e descartada.
    (destino / "data" / "ai").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURE_DIR / "extracoes_dispositivos_sample.jsonl",
        destino / "data" / "ai" / "extracoes_dispositivos.jsonl",
    )


class ConstruirGrafoTest(unittest.TestCase):
    """Testa o gerador operando diretamente sobre as funcoes em memoria
    (construir_grafo), sem passar pelo SQLite — mais rapido e mais direto
    para checar contagem e forma dos dados."""

    @classmethod
    def setUpClass(cls):
        cls.mod = carrega(GERADOR_PATH, "grafo_juridico_gerador")
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.tmpdir.name)
        montar_root_fixture(cls.root)
        cls.grafo = cls.mod.construir_grafo(str(cls.root))

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def _nos_por_tipo(self, tipo):
        return {chave: no for chave, no in self.grafo["nos"].items() if no["tipo"] == tipo}

    def _arestas_por_tipo(self, tipo):
        return {chaves: info for chaves, info in self.grafo["arestas"].items() if chaves[2] == tipo}

    # -- (1) contagens de nos/arestas batem com o esperado da fixture -----

    def test_contagem_de_nos_e_arestas_bate_com_a_fixture(self):
        self.assertEqual(len(self._nos_por_tipo("dispositivo")), 37)
        self.assertEqual(len(self._nos_por_tipo("norma")), 24)
        self.assertEqual(len(self._nos_por_tipo("pagina")), 5)
        self.assertEqual(len(self._nos_por_tipo("area")), 1)
        self.assertEqual(len(self._nos_por_tipo("sumula")), 1)
        self.assertEqual(len(self._nos_por_tipo("tribunal")), 2)  # STF + STJ
        self.assertEqual(len(self._nos_por_tipo("tema")), 11)  # 12 linhas, 1 par duplicado colapsa

        self.assertEqual(len(self._arestas_por_tipo("cita")), 8)
        self.assertEqual(len(self._arestas_por_tipo("pertence_a")), 37)
        self.assertEqual(len(self._arestas_por_tipo("cocitada_com")), 1)
        self.assertEqual(len(self._arestas_por_tipo("da_area")), 5)
        self.assertEqual(len(self._arestas_por_tipo("julgado_por")), 12)  # 11 tema + 1 sumula
        self.assertEqual(len(self._arestas_por_tipo("revoga")), 1)
        self.assertEqual(len(self._arestas_por_tipo("altera")), 0)
        self.assertEqual(len(self._arestas_por_tipo("aplica")), 0)
        self.assertEqual(len(self._arestas_por_tipo("supera")), 0)
        self.assertEqual(len(self._arestas_por_tipo("impactada_por")), 0)

    def test_aresta_cita_descarta_pagina_sem_no_em_vez_de_inventar(self):
        """25 das 30 paginas do recorte de cocitacao NAO estao no
        published_manifest de fixture (de proposito). Nenhuma delas pode
        aparecer como origem de aresta 'cita'."""
        paths_com_no = set(self._nos_por_tipo("pagina").keys())
        for (origem, _destino, _tipo) in self._arestas_por_tipo("cita"):
            self.assertIn(origem, paths_com_no)

    def test_revoga_resolve_so_o_alvo_que_existe_no_grafo(self):
        """art_1494 do Codigo Civil (10406) foi revogado pela Lei 14.382 —
        14.382 esta na fixture, entao resolve. art_38 da LOAS (8742) foi
        revogado pela Lei 12.435 — nunca coletada nem citada, entao NAO pode
        virar aresta."""
        arestas_revoga = self._arestas_por_tipo("revoga")
        self.assertEqual(len(arestas_revoga), 1)
        (origem, destino, _tipo), info = next(iter(arestas_revoga.items()))
        self.assertEqual(origem, "urn:lex:br:federal:lei:2022-06-27;14382")
        self.assertEqual(destino, "urn:lex:br:federal:lei:2002-01-10;10406")
        self.assertIn("art_1494", info["evidencia"]["dispositivos_atingidos"])
        self.assertNotIn("urn:lex:br:federal:lei:2011-07-06;12435", self.grafo["nos"])

    def test_cocitada_com_peso_e_direcao(self):
        arestas = self._arestas_por_tipo("cocitada_com")
        self.assertEqual(len(arestas), 1)
        (origem, destino, _tipo), info = next(iter(arestas.items()))
        self.assertEqual(origem, "/autonomos/b2b-escopo-alterado/")
        self.assertEqual(destino, "/autonomos/b2b-exclusividade/")
        self.assertLess(origem, destino, "grava uma direcao so, origem<destino")
        self.assertEqual(info["peso"], 1.0)
        self.assertEqual(
            info["evidencia"]["dispositivos_urn"],
            ["urn:lex:br:federal:lei:2002-01-10;10406!art421"],
        )
        self.assertNotIn(
            ("/autonomos/b2b-exclusividade/", "/autonomos/b2b-escopo-alterado/", "cocitada_com"),
            self.grafo["arestas"],
        )

    def test_pertence_a_deriva_urn_base_com_dispositivo(self):
        arestas = self._arestas_por_tipo("pertence_a")
        chave = (
            "urn:lex:br:federal:lei:2002-01-10;10406!art421",
            "urn:lex:br:federal:lei:2002-01-10;10406",
            "pertence_a",
        )
        self.assertIn(chave, arestas)

    def test_pertence_a_urn_sem_dispositivo_fica_intacta(self):
        """Divisao por '!' numa URN de norma (sem dispositivo) devolve a
        propria URN, sem quebrar nem truncar — mesma funcao que separa
        dispositivo de norma nos percursos."""
        urn_norma = "urn:lex:br:federal:lei:2002-01-10;10406"
        self.assertEqual(urn_norma.split("!")[0], urn_norma)
        for chave in self._nos_por_tipo("norma"):
            self.assertNotIn("!", chave, "no de norma nunca carrega '!' na chave")

    def test_rotulo_de_norma_citada_vem_do_texto_real_da_pagina(self):
        no = self.grafo["nos"]["urn:lex:br:federal:lei:2002-01-10;10406"]
        self.assertEqual(no["rotulo"], "Código Civil")

    def test_sumula_ganha_rotulo_do_enunciado_e_tribunal_stf(self):
        no = self.grafo["nos"]["sumula:STF:10"]
        self.assertEqual(no["tipo"], "sumula")
        self.assertIn("SERVIÇO MILITAR", no["rotulo"])
        self.assertEqual(self.grafo["nos"]["STF"]["rotulo"], "Supremo Tribunal Federal")

    def test_tema_duplicado_colapsa_na_mesma_chave(self):
        self.assertIn("tema:STJ:controversia:75", self.grafo["nos"])
        self.assertIn(
            ("tema:STJ:controversia:75", "STJ", "julgado_por"),
            self._arestas_por_tipo("julgado_por"),
        )


class EscritaSqliteTest(unittest.TestCase):
    """Roda o gerador de ponta a ponta (CLI real) contra a fixture e
    inspeciona o .sqlite escrito."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.tmpdir.name)
        montar_root_fixture(cls.root)
        cls.db_path = cls.root / "data" / "ai" / "grafo.sqlite"
        resultado = subprocess.run(
            [sys.executable, str(GERADOR_PATH), "--root", str(cls.root), "--out", str(cls.db_path)],
            capture_output=True, text=True, timeout=60,
        )
        cls.exit_code_geracao = resultado.returncode
        cls.stdout_geracao = resultado.stdout
        cls.stderr_geracao = resultado.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_geracao_termina_com_sucesso_e_escreve_o_arquivo(self):
        self.assertEqual(
            self.exit_code_geracao, 0,
            f"stdout={self.stdout_geracao!r} stderr={self.stderr_geracao!r}",
        )
        self.assertTrue(self.db_path.exists())

    def test_manifesto_json_tem_sha256_e_contagens(self):
        manifesto_path = self.root / "data" / "ai" / "grafo_manifest.json"
        self.assertTrue(manifesto_path.exists())
        manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
        self.assertEqual(manifesto["schema_version"], "grafo_juridico_v1")
        self.assertEqual(manifesto["total_nos"], 81)
        self.assertEqual(manifesto["total_arestas"], 64)
        self.assertEqual(len(manifesto["fontes"]), 4)
        for fonte in manifesto["fontes"]:
            self.assertEqual(len(fonte["sha256"]), 64)
            self.assertGreater(fonte["linhas"], 0)
        self.assertIn("nos_por_tipo", manifesto)
        self.assertIn("arestas_por_tipo", manifesto)
        self.assertGreater(manifesto["tamanho_sqlite_bytes"], 0)

    def test_fts5_acha_codigo_civil(self):
        conn = sqlite3.connect(str(self.db_path))
        try:
            linhas = conn.execute(
                "SELECT n.chave FROM nos_fts f JOIN nos n ON n.id = f.rowid "
                "WHERE nos_fts MATCH ?", ("Código Civil",),
            ).fetchall()
        finally:
            conn.close()
        chaves = {l[0] for l in linhas}
        self.assertIn("urn:lex:br:federal:lei:2002-01-10;10406", chaves)

    def test_consultar_grafo_json_formato_estavel(self):
        resultado = subprocess.run(
            [sys.executable, str(CONSULTAR_PATH), "--db", str(self.db_path),
             "urn:lex:br:federal:lei:2002-01-10;10406", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        saida = json.loads(resultado.stdout)
        self.assertIn("no", saida)
        self.assertIn("vizinhos", saida)
        no = saida["no"]
        for campo in ("id", "tipo", "chave", "rotulo", "atributos"):
            self.assertIn(campo, no)
        self.assertEqual(no["chave"], "urn:lex:br:federal:lei:2002-01-10;10406")
        self.assertIsInstance(saida["vizinhos"], list)
        self.assertGreater(len(saida["vizinhos"]), 0)
        for viz in saida["vizinhos"]:
            for campo in ("tipo_aresta", "direcao", "peso", "fonte", "no"):
                self.assertIn(campo, viz)
            self.assertIn(viz["direcao"], ("entrada", "saida"))

    def test_consultar_grafo_por_termo_fts_resolve(self):
        resultado = subprocess.run(
            [sys.executable, str(CONSULTAR_PATH), "--db", str(self.db_path), "Código Civil", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        saida = json.loads(resultado.stdout)
        self.assertEqual(saida["no"]["chave"], "urn:lex:br:federal:lei:2002-01-10;10406")


class IdempotenciaTest(unittest.TestCase):
    """Gerar duas vezes sobre a mesma fixture da o mesmo conjunto de nos e
    arestas — comparando por CHAVE NATURAL, nunca pelo id interno (que so e
    estavel dentro de UMA geracao)."""

    def test_duas_geracoes_produzem_o_mesmo_grafo(self):
        mod = carrega(GERADOR_PATH, "grafo_juridico_gerador_idem")
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            montar_root_fixture(root)
            grafo_a = mod.construir_grafo(str(root))
            grafo_b = mod.construir_grafo(str(root))

        def dump(grafo):
            nos = sorted(
                (chave, no["tipo"], no["rotulo"], json.dumps(no["atributos"], sort_keys=True))
                for chave, no in grafo["nos"].items()
            )
            arestas = sorted(
                (o, d, tipo, info["peso"], info["fonte"], json.dumps(info["evidencia"], sort_keys=True))
                for (o, d, tipo), info in grafo["arestas"].items()
            )
            return nos, arestas

        self.assertEqual(dump(grafo_a), dump(grafo_b))


class AcordaoStjTest(unittest.TestCase):
    """Fonte 5 (v1.1): tools/testdata/grafo_juridico/stj_espelhos_sample.jsonl
    tem 6 acordaos REAIS da Primeira Turma do STJ (id_fonte 000813619,
    000815091, 000816183, 000819468, 000813705, 000816172), 4 deles com
    dispositivos_citados_urn nao vazio. Numeros abaixo vieram de contagem
    INDEPENDENTE sobre o proprio JSONL da fixture (nao do modulo sob teste):
    5 URNs citadas ao todo (000815091 cita duas), das quais so
    'urn:lex:br:federal:decreto:1932-01-06;20910' e nova (as outras 3 —
    Codigo Civil 10406, CPC 13105, Constituicao 1988 — ja existem no grafo
    base via legal_cocitation_index_sample.jsonl). Medido tambem: nenhuma das
    70 URNs distintas do corpus real (862 registros, 2026-09-08) carrega '!'
    de artigo — a fonte so da granularidade de norma, por isso as arestas
    'cita' de acordao real neste teste sempre apontam para no tipo 'norma',
    nunca 'dispositivo'."""

    @classmethod
    def setUpClass(cls):
        cls.mod = carrega(GERADOR_PATH, "grafo_juridico_gerador_acordao")
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.tmpdir.name)
        montar_root_fixture_com_acordaos(cls.root)
        cls.grafo = cls.mod.construir_grafo(str(cls.root))

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def _nos_por_tipo(self, tipo):
        return {chave: no for chave, no in self.grafo["nos"].items() if no["tipo"] == tipo}

    def _arestas_por_tipo(self, tipo):
        return {chaves: info for chaves, info in self.grafo["arestas"].items() if chaves[2] == tipo}

    def test_contagens_de_acordao_e_arestas_batem_com_a_fixture(self):
        self.assertEqual(len(self._nos_por_tipo("acordao")), 6)
        self.assertEqual(len(self._nos_por_tipo("norma")), 25)  # 24 da base + 1 orfa (decreto 20910)
        self.assertEqual(len(self._nos_por_tipo("dispositivo")), 38)  # 37 da base (sem URN de artigo na fonte 5) + art. 1.022 do CPC vindo da extracao LLM (fonte 6)
        self.assertEqual(len(self._arestas_por_tipo("cita")), 15)  # 8 da base (pagina) + 5 (acordao, fonte 5) + 2 (extracao LLM, fonte 6)
        self.assertEqual(len(self._arestas_por_tipo("julgado_por")), 19)  # 12 da base (tema+sumula) + 6 (acordao) + 1 (sumula:STJ:7 da fonte 6)
        self.assertEqual(len(self._arestas_por_tipo("pertence_a")), 38)  # 37 da base + art. 1.022 -> CPC pela extracao LLM (fonte 6)
        self.assertEqual(len(self.grafo["nos"]), 90)  # 88 + dispositivo art. 1.022 + sumula:STJ:7 (fonte 6)
        self.assertEqual(len(self.grafo["arestas"]), 79)  # 75 + 2 cita + 1 pertence_a + 1 julgado_por (fonte 6)

    def test_acordao_ganha_atributos_com_ementa_integral_e_proveniencia(self):
        no = self.grafo["nos"]["acordao:STJ:000813619"]
        self.assertEqual(no["tipo"], "acordao")
        self.assertIn("(STJ, PRIMEIRA TURMA,", no["rotulo"])
        for campo in ("relator", "classe", "numero_registro", "data_julgamento", "data_publicacao",
                      "ementa", "base_legal", "fonte_url", "sha256_conteudo"):
            self.assertIn(campo, no["atributos"])
        self.assertTrue(no["atributos"]["ementa"])
        self.assertEqual(len(no["atributos"]["sha256_conteudo"]), 64)

    def test_acordao_cita_norma_orfa_criada_pela_citacao(self):
        """decreto 20910 nunca foi coletado pelo oraculo nem citado por
        pagina na fixture base — so aparece porque o acordao 000815091 cita
        essa URN. Vira no 'norma' (nao 'dispositivo', pois a URN nao tem
        '!'), igual ao padrao ja usado para norma_bases orfas da cocitacao."""
        chave_norma = "urn:lex:br:federal:decreto:1932-01-06;20910"
        self.assertIn(chave_norma, self.grafo["nos"])
        self.assertEqual(self.grafo["nos"][chave_norma]["tipo"], "norma")
        self.assertIn(
            ("acordao:STJ:000815091", chave_norma, "cita"),
            self._arestas_por_tipo("cita"),
        )

    def test_acordao_sem_urn_nao_gera_aresta_cita(self):
        origens_cita = {origem for (origem, _d, _t) in self._arestas_por_tipo("cita")}
        self.assertNotIn("acordao:STJ:000816172", origens_cita)

    def test_extracao_llm_cita_so_o_que_tem_urn_e_a_ultima_linha_vence(self):
        arestas = self.grafo["arestas"]
        # a segunda linha de 000813705 vence: art. 1.022 (dispositivo + pertence_a) e Sumula 7
        disp = "urn:lex:br:federal:lei:2015-03-16;13105!art1022"
        self.assertIn(("acordao:STJ:000813705", disp, "cita"), arestas)
        self.assertIn((disp, "urn:lex:br:federal:lei:2015-03-16;13105", "pertence_a"), arestas)
        self.assertIn(("acordao:STJ:000813705", "sumula:STJ:7", "cita"), arestas)
        self.assertIn(("sumula:STJ:7", "STJ", "julgado_por"), arestas)
        self.assertNotIn(("acordao:STJ:000813705", "sumula:STJ:182", "cita"), arestas)
        self.assertNotIn("sumula:STJ:182", self.grafo["nos"])
        # proveniencia: fonte 6 e evidencia com o trecho literal e o modelo
        aresta = arestas[("acordao:STJ:000813705", disp, "cita")]
        self.assertEqual(aresta["fonte"], "data/ai/extracoes_dispositivos.jsonl")
        self.assertEqual(aresta["evidencia"]["texto_citado"], "Inexiste ofensa ao art. 1.022 do CPC/2015")
        self.assertEqual(aresta["evidencia"]["modelo"], "qwen3.5:4b")
        # item sem urn (lei estadual) nao vira no nem aresta; acordao fora da fonte 5 e descartado
        self.assertFalse(any("14/1982" in chave for chave in self.grafo["nos"]))
        self.assertNotIn("acordao:STJ:999999999", self.grafo["nos"])
        self.assertEqual(self.grafo["extracoes"], {
            "registros": 3, "acordaos": 1, "itens_com_urn": 2, "itens_sem_urn": 1, "acordaos_fora_do_grafo": 1,
        })

    def test_acordao_julgado_por_stj_para_os_6(self):
        arestas = self._arestas_por_tipo("julgado_por")
        for id_fonte in ("000813619", "000815091", "000816183", "000819468", "000813705", "000816172"):
            self.assertIn((f"acordao:STJ:{id_fonte}", "STJ", "julgado_por"), arestas)

    def test_urn_com_dispositivo_hipotetico_cria_no_dispositivo_e_pertence_a(self):
        """A fonte real medida (862 registros) nunca entrega URN de artigo em
        dispositivos_citados_urn (0/70 distintas). Este teste exercita o
        ramo dispositivo+pertence_a diretamente via _processar_acordao_stj,
        com um registro construido a mao (nao um dos 6 REAIS da fixture),
        para provar que o codigo trata corretamente o dia em que o coletor
        passar a entregar granularidade de artigo."""
        grafo = self.mod.novo_grafo()
        registro_hipotetico = {
            "id_fonte": "999999999",
            "classe": "REsp",
            "numero_processo": "0000000",
            "orgao_julgador": "PRIMEIRA TURMA",
            "data_julgamento": "2022-01-01",
            "data_publicacao": "2022-01-02",
            "relator": "MINISTRO HIPOTETICO",
            "numero_registro": "202200000000",
            "ementa": "ementa hipotetica de teste.",
            "base_legal": "teste",
            "fonte_url": "https://dadosabertos.web.stj.jus.br/teste",
            "sha256_conteudo": "0" * 64,
            "dispositivos_citados_urn": ["urn:lex:br:federal:lei:2002-01-10;10406!art421"],
        }
        self.mod._processar_acordao_stj(grafo, registro_hipotetico, "fixture-hipotetica")
        urn_dispositivo = "urn:lex:br:federal:lei:2002-01-10;10406!art421"
        urn_norma = "urn:lex:br:federal:lei:2002-01-10;10406"
        self.assertEqual(grafo["nos"][urn_dispositivo]["tipo"], "dispositivo")
        self.assertEqual(grafo["nos"][urn_dispositivo]["atributos"]["norma_base"], urn_norma)
        self.assertIn((urn_dispositivo, urn_norma, "pertence_a"), grafo["arestas"])
        self.assertIn(("acordao:STJ:999999999", urn_dispositivo, "cita"), grafo["arestas"])

    def test_diretorio_de_acordaos_ausente_nao_quebra_a_geracao(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            montar_root_fixture(root)  # SEM stj-espelhos/
            grafo_sem_acordaos = self.mod.construir_grafo(str(root))
        acordaos = {c: n for c, n in grafo_sem_acordaos["nos"].items() if n["tipo"] == "acordao"}
        self.assertEqual(acordaos, {})
        # a base sem acordaos continua com os mesmos totais que ConstruirGrafoTest mede
        self.assertEqual(len(grafo_sem_acordaos["nos"]), 81)
        self.assertEqual(len(grafo_sem_acordaos["arestas"]), 64)


class VizinhancaTest(unittest.TestCase):
    """data/ai/grafo_vizinhanca.jsonl: uma linha por no, sem cocitada_com,
    ordenada por chave (e vizinhos por aresta/direcao/chave)."""

    @classmethod
    def setUpClass(cls):
        cls.mod = carrega(GERADOR_PATH, "grafo_juridico_gerador_vizinhanca")
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.tmpdir.name)
        montar_root_fixture_com_acordaos(cls.root)
        cls.grafo = cls.mod.construir_grafo(str(cls.root))
        cls.vizinhanca_path = cls.root / "data" / "ai" / "grafo_vizinhanca.jsonl"
        cls.total_linhas, cls.tamanho_bytes = cls.mod.escrever_vizinhanca(cls.grafo, str(cls.vizinhanca_path))
        cls.linhas = [json.loads(l) for l in cls.vizinhanca_path.read_text(encoding="utf-8").splitlines()]

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_uma_linha_por_no(self):
        self.assertEqual(self.total_linhas, len(self.grafo["nos"]))
        self.assertEqual(len(self.linhas), len(self.grafo["nos"]))
        self.assertGreater(self.tamanho_bytes, 0)
        self.assertEqual(self.tamanho_bytes, self.vizinhanca_path.stat().st_size)

    def test_linhas_ordenadas_por_chave(self):
        chaves = [l["chave"] for l in self.linhas]
        self.assertEqual(chaves, sorted(chaves))

    def test_sem_cocitada_com_em_nenhum_vizinho(self):
        for linha in self.linhas:
            for v in linha["vizinhos"]:
                self.assertNotEqual(v["aresta"], "cocitada_com")

    def test_da_area_de_saida_de_pagina_fica_fora_mas_entrada_na_area_fica(self):
        por_chave = {l["chave"]: l for l in self.linhas}
        pagina = por_chave["/autonomos/b2b-escopo-alterado/"]
        self.assertFalse(
            any(v["aresta"] == "da_area" and v["direcao"] == "saida" for v in pagina["vizinhos"])
        )
        area = por_chave[self.grafo["nos"]["/autonomos/b2b-escopo-alterado/"]["atributos"]["area"]]
        self.assertTrue(
            any(v["aresta"] == "da_area" and v["direcao"] == "entrada" and v["chave"] == "/autonomos/b2b-escopo-alterado/"
                for v in area["vizinhos"])
        )

    def test_vizinhos_ordenados_por_aresta_direcao_chave(self):
        for linha in self.linhas:
            chaves_ordem = [(v["aresta"], v["direcao"], v["chave"]) for v in linha["vizinhos"]]
            self.assertEqual(chaves_ordem, sorted(chaves_ordem))

    def test_norma_orfa_citada_por_acordao_lista_o_acordao_como_entrada_cita(self):
        """decreto 20910 (sem granularidade de artigo, ver AcordaoStjTest) e
        o 'dispositivo legal' citado pelo acordao 000815091 nesta fonte real
        — modelado como no tipo 'norma' porque a URN nao tem '!'. A linha de
        vizinhanca dele deve listar o acordao como vizinho de ENTRADA cita,
        que e o comportamento pedido para 'a linha de um dispositivo lista o
        acordao como vizinho de entrada cita' quando a fonte real so entrega
        granularidade de norma."""
        por_chave = {l["chave"]: l for l in self.linhas}
        norma = por_chave["urn:lex:br:federal:decreto:1932-01-06;20910"]
        self.assertTrue(any(
            v["aresta"] == "cita" and v["direcao"] == "entrada" and v["chave"] == "acordao:STJ:000815091"
            for v in norma["vizinhos"]
        ))

    def test_atributos_e_campos_obrigatorios_presentes(self):
        for linha in self.linhas:
            for campo in ("chave", "tipo", "rotulo", "atributos", "vizinhos"):
                self.assertIn(campo, linha)
            self.assertIsInstance(linha["atributos"], dict)
            for v in linha["vizinhos"]:
                for campo in ("aresta", "direcao", "chave", "tipo", "rotulo", "peso"):
                    self.assertIn(campo, v)


class SumulaCitadaTest(unittest.TestCase):
    """sumulas_citadas do coletor (2026-09-08) vira aresta acordao -cita-> sumula.
    Sumula do STJ nasce como no sem enunciado (o oraculo so cobre o STF)."""

    def test_acordao_cita_sumula_do_stf_e_do_stj(self):
        import json as _json
        with tempfile.TemporaryDirectory() as tmp:
            destino = pathlib.Path(tmp)
            montar_root_fixture_com_acordaos(destino)
            caminho = destino / "data" / "corpus" / "jurisprudencia" / "stj-espelhos" / "registros-fixture.jsonl"
            linhas = [_json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines() if l.strip()]
            linhas[0]["sumulas_citadas"] = ["STF:280", "STJ:7", "TST:331"]
            linhas[1]["sumulas_citadas"] = ["STJ:7"]
            caminho.write_text("".join(_json.dumps(l, ensure_ascii=False) + "\n" for l in linhas), encoding="utf-8")
            mod = carrega(GERADOR_PATH, "grafo_juridico_gerador_sumulas")
            grafo = mod.construir_grafo(str(destino))
            chave0 = "acordao:STJ:" + linhas[0]["id_fonte"]
            chave1 = "acordao:STJ:" + linhas[1]["id_fonte"]
            self.assertIn("sumula:STJ:7", grafo["nos"])
            self.assertEqual(grafo["nos"]["sumula:STJ:7"]["tipo"], "sumula")
            self.assertNotIn("sumula:TST:331", grafo["nos"], "so STF e STJ sao chaves do grafo")
            citas = {(o, d) for (o, d, tipo) in grafo["arestas"] if tipo == "cita" and d.startswith("sumula:")}
            self.assertIn((chave0, "sumula:STF:280"), citas)
            self.assertIn((chave0, "sumula:STJ:7"), citas)
            self.assertIn((chave1, "sumula:STJ:7"), citas)
            self.assertEqual(len([1 for (o, d, tipo) in grafo["arestas"] if tipo == "cita" and d == "sumula:STJ:7"]), 3)  # 2 da fonte 5 + 000813705 pela extracao LLM (fonte 6)
            julgado = [1 for (o, d, tipo) in grafo["arestas"] if tipo == "julgado_por" and o == "sumula:STJ:7"]
            self.assertEqual(len(julgado), 1)


class FrenteDTest(unittest.TestCase):
    """As tres familias derivadas de 2026-09-09: pagina->sumula,
    dispositivo<->dispositivo e tema->dispositivo.

    Grafo SINTETICO, montado no e para o teste: a regra a provar e o corte por
    suporte, e amarra-la ao acervo real faria o teste mudar de veredito toda vez
    que a coleta trouxesse um acordao novo."""

    def setUp(self):
        self.mod = carrega(GERADOR_PATH, "grafo_juridico_frente_d")

    def _monta(self, quantos_acordaos):
        """Uma pagina que cita art5, uma sumula, e N acordaos que citam os dois
        (mais art6, para exercitar dispositivo<->dispositivo no mesmo laco)."""
        mod = self.mod
        grafo = mod.novo_grafo()
        mod.add_no(grafo, "pagina", "/familia/x/", "Pagina X", {})
        mod.add_no(grafo, "sumula", "sumula:STJ:7", "Sumula 7 do STJ", {})
        mod.add_no(grafo, "dispositivo", "urn:lex:br:federal:lei:2002-01-10;10406!art5", "art. 5", {})
        mod.add_no(grafo, "dispositivo", "urn:lex:br:federal:lei:2002-01-10;10406!art6", "art. 6", {})
        mod.add_aresta(grafo, "/familia/x/", "urn:lex:br:federal:lei:2002-01-10;10406!art5", "cita", 1.0, "teste", {})
        for i in range(quantos_acordaos):
            chave = "acordao:STJ:%06d" % i
            mod.add_no(grafo, "acordao", chave, "Acordao %d" % i, {})
            mod.add_aresta(grafo, chave, "urn:lex:br:federal:lei:2002-01-10;10406!art5", "cita", 1.0, "teste", {})
            mod.add_aresta(grafo, chave, "urn:lex:br:federal:lei:2002-01-10;10406!art6", "cita", 1.0, "teste", {})
            mod.add_aresta(grafo, chave, "sumula:STJ:7", "cita", 1.0, "teste", {})
        return grafo

    def test_suporte_abaixo_do_minimo_nao_vira_aresta(self):
        grafo = self._monta(self.mod.SUPORTE_MINIMO_ACORDAOS - 1)
        contagem = self.mod._derivar_arestas_frente_d(grafo)
        self.assertEqual(contagem["pagina_sumula"], 0)
        self.assertEqual(contagem["dispositivo_dispositivo"], 0)
        self.assertGreaterEqual(contagem["pares_pagina_sumula_descartados"], 1)
        self.assertNotIn(("/familia/x/", "sumula:STJ:7", "aplica"), grafo["arestas"])

    def test_suporte_no_minimo_vira_aresta_com_peso_e_evidencia(self):
        n = self.mod.SUPORTE_MINIMO_ACORDAOS
        grafo = self._monta(n)
        contagem = self.mod._derivar_arestas_frente_d(grafo)
        self.assertEqual(contagem["pagina_sumula"], 1)
        aresta = grafo["arestas"][("/familia/x/", "sumula:STJ:7", "aplica")]
        self.assertEqual(aresta["peso"], float(n))
        self.assertEqual(aresta["fonte"], "derivado:frente-d")
        self.assertEqual(aresta["evidencia"]["acordaos_de_suporte"], n)
        self.assertIn("urn:lex:br:federal:lei:2002-01-10;10406!art5", aresta["evidencia"]["dispositivos_em_comum"])

    def test_cocitacao_de_dispositivo_sai_nos_dois_sentidos(self):
        grafo = self._monta(self.mod.SUPORTE_MINIMO_ACORDAOS)
        contagem = self.mod._derivar_arestas_frente_d(grafo)
        a = "urn:lex:br:federal:lei:2002-01-10;10406!art5"
        b = "urn:lex:br:federal:lei:2002-01-10;10406!art6"
        self.assertEqual(contagem["dispositivo_dispositivo"], 2)
        self.assertIn((a, b, "cocitada_com"), grafo["arestas"])
        self.assertIn((b, a, "cocitada_com"), grafo["arestas"])

    def test_cocitacao_de_dispositivo_nao_e_excluida_da_vizinhanca(self):
        """A exclusao de `cocitada_com` no dump era por TIPO DE ARESTA e teria
        engolido as arestas entre DISPOSITIVOS — o trabalho da Frente D ficaria
        invisivel para o Go sem nenhum erro aparecer."""
        self.assertTrue(self.mod._exclui_do_vizinho("pagina", "cocitada_com", "saida"))
        self.assertFalse(self.mod._exclui_do_vizinho("dispositivo", "cocitada_com", "saida"))

    def test_tema_so_liga_dispositivo_quando_o_tema_existe_no_grafo(self):
        mod = self.mod
        grafo = mod.novo_grafo()
        mod.add_no(grafo, "pagina", "/jurisprudencia/stj-tema-42/", "Tema 42", {})
        mod.add_no(grafo, "dispositivo", "urn:lex:br:federal:lei:2002-01-10;10406!art5", "art. 5", {})
        mod.add_aresta(grafo, "/jurisprudencia/stj-tema-42/", "urn:lex:br:federal:lei:2002-01-10;10406!art5", "cita", 1.0, "teste", {})
        sem_tema = mod._derivar_arestas_frente_d(grafo)
        self.assertEqual(sem_tema["tema_dispositivo"], 0, "tema ausente do grafo nao se inventa")

        mod.add_no(grafo, "tema", "tema:STJ:tema:42", "Tema 42 do STJ", {})
        com_tema = mod._derivar_arestas_frente_d(grafo)
        self.assertEqual(com_tema["tema_dispositivo"], 1)
        self.assertIn(("tema:STJ:tema:42", "urn:lex:br:federal:lei:2002-01-10;10406!art5", "cita"), grafo["arestas"])


class TestCorteJulgadoPorEmTribunal(unittest.TestCase):
    """O corte de 2026-09-22 e o atributo que impede a fabricacao de ausencia.

    Cada acordao aponta para o seu tribunal, entao o no `tribunal` acumula uma
    aresta `julgado_por` de ENTRADA por acordao do corpus. Medido no artefato
    vivo: STJ com 168.605 arestas numa linha de 30.348.998 bytes, que derrubou
    o boot do servidor em 2026-09-21T21:10 e produziu 591 reinicios.

    Duas coisas tem de valer ao mesmo tempo, e e por isso que sao um teste so:
    a linha encolhe (vizinhos == []) E o total sobrevive em
    atributos.julgado_por_entrada. So a primeira faria o MCP responder
    "Total = 0" para o STJ, que e falso.
    """

    def setUp(self):
        self.mod = carrega(GERADOR_PATH, "gerador_grafo_corte")
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _grafo_com_tribunal(self, quantos_acordaos):
        mod = self.mod
        grafo = mod.novo_grafo()
        mod.add_no(grafo, "tribunal", "STJ", "Superior Tribunal de Justiça", {})
        for i in range(quantos_acordaos):
            chave = "acordao:STJ:%06d" % i
            mod.add_no(grafo, "acordao", chave, "AgInt no AREsp %d (STJ)" % i, {})
            mod.add_aresta(grafo, chave, "STJ", "julgado_por", 1, "teste", "")
        return grafo

    def _linhas(self, grafo):
        destino = pathlib.Path(self.tmp) / "vizinhanca.jsonl"
        self.mod.escrever_vizinhanca(grafo, str(destino))
        return {
            d["chave"]: d
            for d in (json.loads(l) for l in destino.read_text(encoding="utf-8").splitlines() if l.strip())
        }

    def test_tribunal_perde_os_vizinhos_de_entrada_e_ganha_a_contagem(self):
        linhas = self._linhas(self._grafo_com_tribunal(37))
        tribunal = linhas["STJ"]
        self.assertEqual(tribunal["vizinhos"], [], "o no tribunal tem de ficar sem vizinhos de entrada")
        self.assertEqual(
            tribunal["atributos"].get("julgado_por_entrada"), 37,
            "o total cortado tem de sobrar no atributo, senao o MCP diz Total = 0",
        )

    def test_o_acordao_conserva_a_aresta_de_saida(self):
        """O corte e por PAR. Visto do acordao, `julgado_por` e uma aresta de
        SAIDA e continua existindo -- quem quiser saber o tribunal de um
        acordao continua sabendo. So o lado que explodia foi cortado."""
        linhas = self._linhas(self._grafo_com_tribunal(3))
        saidas = [v for v in linhas["acordao:STJ:000000"]["vizinhos"] if v["aresta"] == "julgado_por"]
        self.assertEqual(len(saidas), 1, "o acordao tem de continuar apontando para o tribunal")
        self.assertEqual(saidas[0]["direcao"], "saida")
        self.assertEqual(saidas[0]["chave"], "STJ")

    def test_a_linha_do_tribunal_encolhe_de_verdade(self):
        """Medicao, nao intencao: a linha do tribunal com 2.000 acordaos tem de
        caber em menos de 1 KiB. Sem o corte ela passa de 200 KiB."""
        linhas = self._linhas(self._grafo_com_tribunal(2000))
        bytes_da_linha = len(json.dumps(linhas["STJ"], ensure_ascii=False))
        self.assertLess(bytes_da_linha, 1024, "linha do tribunal com %d bytes" % bytes_da_linha)

    def test_no_sem_corte_nao_ganha_atributo_nenhum(self):
        """A guarda contra efeito colateral: o acordao nao teve nada cortado,
        entao a chave `julgado_por_entrada` nao pode aparecer nele."""
        linhas = self._linhas(self._grafo_com_tribunal(3))
        self.assertNotIn("julgado_por_entrada", linhas["acordao:STJ:000000"]["atributos"])

    def test_atributos_do_no_de_origem_nao_sao_mutados(self):
        """O gerador monta a linha a partir de no["atributos"]. Escrever a
        contagem direto ali contaminaria o dicionario que outros produtores
        (manifesto, sqlite) leem depois."""
        grafo = self._grafo_com_tribunal(5)
        self._linhas(grafo)
        self.assertEqual(
            grafo["nos"]["STJ"]["atributos"], {},
            "escrever_vizinhanca nao pode mutar os atributos do grafo em memoria",
        )


if __name__ == "__main__":
    unittest.main()
