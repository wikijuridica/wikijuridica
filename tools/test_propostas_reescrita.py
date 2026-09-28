#!/usr/bin/env python3
"""Testes de tools/generate-propostas-reescrita -- a fila de propostas de
reescrita com evidencia (DEC-058, P2 do mandato AI-first/B2A).

Fixtures REAIS (nunca sinteticas na parte que pode ser real, como manda
CLAUDE.md "ZERO FAKE"): `tools/testdata/propostas_reescrita/manifest.jsonl`
e `severity.jsonl` sao linhas copiadas ipsis litteris de
`data/editorial/published_manifest.jsonl` e `data/editorial/v2_publication_severity.jsonl`
para 4 paginas reais (jur-stf-adi-4376, acon-resp-seguro-rc,
banc-adesao-automatica-seguro-opt-out-silencioso, e o controle limpo
aer-alteracao-aeroporto-mesma-cidade); `eventos-2026-09-06.jsonl` e a linha
real de `data/ops/eventos/eventos-2026-09-06.jsonl` para
/jurisprudencia/stf-adi-4376/; `pages.json` sao os registros reais de
`content/pages.json` para essas duas paginas, com UMA frase acrescentada ao
corpo de resp-seguro-rc citando "REsp 1723456" (para exercitar o requisito
"pagina ja cita o processo" sem esperar que o acervo real ja tenha esse caso).

Duas excecoes documentadas e necessarias, porque a janela real (3 dias,
2026-09-06..08) ainda nao tem nenhuma pagina com trafego dominado por agente
de IA (medido -- ver docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md): (1)
`eventos-2026-09-07.jsonl` e uma linha no formato evento_unificado_v1
construida a mao, com os MESMOS campos e tipos do schema real; (2) o
grafo.sqlite de teste e construido do zero por este arquivo, via sqlite3,
com o mesmo schema de data/ai/grafo.sqlite (tabelas nos/arestas) e poucos
nos -- o mandato pede exatamente isso ("construa um grafo.sqlite de teste
... no proprio teste").

Roda o produtor de verdade por importlib (arquivo sem extensao .py, mesmo
padrao de tools/test_evento_unificado.py para script sem extensao), contra
uma raiz temporaria -- nunca contra o repositorio real.

Rodar:
    python3 tools/test_propostas_reescrita.py
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import sqlite3
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-propostas-reescrita"
FIXTURES = RAIZ / "tools" / "testdata" / "propostas_reescrita"

# generate-propostas-reescrita nao tem extensao .py; spec_from_file_location
# so reconhece o loader certo com um SourceFileLoader explicito (mesma
# necessidade documentada em test_check_crawl_coverage_stall.py).
_loader = importlib.machinery.SourceFileLoader("generate_propostas_reescrita", str(FERRAMENTA))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)

HOJE = mod.datetime.date(2026, 9, 8)


def montar_raiz(tmp):
    tmp = pathlib.Path(tmp)
    (tmp / "data" / "editorial").mkdir(parents=True, exist_ok=True)
    (tmp / "data" / "ops" / "eventos").mkdir(parents=True, exist_ok=True)
    (tmp / "content").mkdir(parents=True, exist_ok=True)
    (tmp / "data" / "ai").mkdir(parents=True, exist_ok=True)

    shutil.copy(FIXTURES / "manifest.jsonl", tmp / "data" / "editorial" / "published_manifest.jsonl")
    shutil.copy(FIXTURES / "severity.jsonl", tmp / "data" / "editorial" / "v2_publication_severity.jsonl")
    shutil.copy(FIXTURES / "eventos-2026-09-06.jsonl", tmp / "data" / "ops" / "eventos" / "eventos-2026-09-06.jsonl")
    shutil.copy(FIXTURES / "eventos-2026-09-07.jsonl", tmp / "data" / "ops" / "eventos" / "eventos-2026-09-07.jsonl")
    shutil.copy(FIXTURES / "pages.json", tmp / "content" / "pages.json")

    construir_grafo_teste(tmp / "data" / "ai" / "grafo.sqlite")
    return tmp


def construir_grafo_teste(caminho_db):
    """Grafo minimo, no mesmo schema de data/ai/grafo.sqlite: uma norma com
    um acordao do STJ (com ementa), citada por dispositivo, citado pelas
    duas paginas fixture -- exatamente a cadeia que
    candidato_precedente() percorre."""
    conn = sqlite3.connect(str(caminho_db))
    conn.executescript(
        """
        CREATE TABLE nos (
            id INTEGER PRIMARY KEY,
            tipo TEXT NOT NULL,
            chave TEXT UNIQUE NOT NULL,
            rotulo TEXT NOT NULL,
            atributos TEXT NOT NULL
        );
        CREATE TABLE arestas (
            origem INTEGER NOT NULL,
            destino INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            peso REAL NOT NULL DEFAULT 1,
            fonte TEXT NOT NULL,
            evidencia TEXT NOT NULL,
            PRIMARY KEY(origem, destino, tipo)
        );
        """
    )
    acordao_atributos = json.dumps({
        "classe": "REsp", "numero_registro": 202000012345,
        "relator": "MINISTRO DE TESTE", "fonte_url": "https://dadosabertos.web.stj.jus.br/teste.json",
        "sha256_conteudo": "0" * 64,
        "ementa": "EMENTA DE TESTE. RESPONSABILIDADE CIVIL. SEGURO. TEMA PROXIMO.",
    }, ensure_ascii=False)
    # CONTROLE NEGATIVO no MESMO grafo: acordao que cita a norma inteira e
    # NENHUM artigo da pagina. Ementa deliberadamente proxima do tema, para que
    # o que o reprova seja o LACO e nao o cosseno -- se alguem voltar a indexar
    # por norma, este no vira proposta e o teste vermelho diz por que.
    so_norma_atributos = json.dumps({
        "classe": "REsp", "numero_registro": 202000099999,
        "relator": "MINISTRA DE TESTE", "fonte_url": "https://dadosabertos.web.stj.jus.br/so-norma.json",
        "sha256_conteudo": "1" * 64,
        "ementa": "EMENTA DE TESTE. RESPONSABILIDADE CIVIL. SEGURO. TEMA PROXIMO. OUTRO ARTIGO.",
    }, ensure_ascii=False)
    linhas = [
        (1, "pagina", "/jurisprudencia/stf-adi-4376/", "pagina jur", "{}"),
        (2, "pagina", "/autonomos/resp-seguro-rc/", "pagina resp", "{}"),
        (3, "dispositivo", "urn:lex:br:federal:lei:1990-12-11;9999!art5", "Lei de Teste, art. 5",
         json.dumps({"norma_base": "urn:lex:br:federal:lei:1990-12-11;9999"})),
        (4, "norma", "urn:lex:br:federal:lei:1990-12-11;9999", "Lei de Teste", "{}"),
        (5, "acordao", "acordao:STJ:TESTE0001", "REsp 1723456 (STJ, SEGUNDA TURMA, 2020-05-05)",
         acordao_atributos),
        (6, "acordao", "acordao:STJ:SONORMA01", "REsp 1888888 (STJ, QUARTA TURMA, 2020-06-06)",
         so_norma_atributos),
    ]
    conn.executemany("INSERT INTO nos VALUES (?,?,?,?,?)", linhas)
    arestas = [
        (1, 3, "cita", 1.0, "teste", "{}"),
        (2, 3, "cita", 1.0, "teste", "{}"),
        (3, 4, "pertence_a", 1.0, "teste", "{}"),
        (5, 4, "cita", 1.0, "teste", "{}"),
        # O LACO FORTE: o acordao cita o MESMO ARTIGO que a pagina cita. Sem
        # esta aresta nenhum precedente e proposto (regra de 2026-09-16).
        (5, 3, "cita", 1.0, "teste", "{}"),
        (6, 4, "cita", 1.0, "teste", "{}"),
    ]
    conn.executemany("INSERT INTO arestas VALUES (?,?,?,?,?,?)", arestas)
    conn.commit()
    conn.close()


def gerar(tmp, **kw):
    kw.setdefault("hoje", HOJE)
    kw.setdefault("dias_pedidos", 3)
    kw.setdefault("limite", 100)
    selecionadas, contagem, total = mod.gera_propostas(str(tmp), kw["dias_pedidos"], kw["limite"], hoje=kw["hoje"])
    return selecionadas, contagem, total


def por_path_motivo(selecionadas):
    return {(p["path"], p["motivo"]): p for p in selecionadas}


class TestMotivos(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmpdir = tempfile.mkdtemp(prefix="propostas-reescrita-")
        self.root = montar_raiz(self._tmpdir)
        self.selecionadas, self.contagem, self.total = gerar(self.root)
        self.idx = por_path_motivo(self.selecionadas)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_agentes_leem_humanos_nao_dispara_no_cenario_certo(self):
        chave = ("/bancario/adesao-automatica-seguro-opt-out-silencioso/", "agentes_leem_humanos_nao")
        self.assertIn(chave, self.idx, "esperava agentes_leem_humanos_nao para a pagina agent-dominant")
        ev = self.idx[chave]["evidencia"]
        self.assertEqual(ev["agentes_de_ia"], 5)
        self.assertEqual(ev["requisicoes"], 6)

    def test_agentes_leem_humanos_nao_nao_dispara_no_cenario_errado(self):
        # jur-stf-adi-4376 e humano-dominante (6 humanos, 0 agentes) -- o oposto.
        chave = ("/jurisprudencia/stf-adi-4376/", "agentes_leem_humanos_nao")
        self.assertNotIn(chave, self.idx)
        # a pagina de controle nao tem trafego nenhum.
        chave_controle = ("/aereo/alteracao-aeroporto-mesma-cidade/", "agentes_leem_humanos_nao")
        self.assertNotIn(chave_controle, self.idx)

    def test_humanos_leem_agentes_nao_dispara_no_cenario_certo(self):
        chave = ("/jurisprudencia/stf-adi-4376/", "humanos_leem_agentes_nao")
        self.assertIn(chave, self.idx)
        ev = self.idx[chave]["evidencia"]
        self.assertEqual(ev["humano_estimado"], 6)
        self.assertEqual(ev["requisicoes"], 6)

    def test_humanos_leem_agentes_nao_nao_dispara_no_cenario_errado(self):
        chave = ("/bancario/adesao-automatica-seguro-opt-out-silencioso/", "humanos_leem_agentes_nao")
        self.assertNotIn(chave, self.idx)

    def test_corpo_curto_dispara_no_cenario_certo(self):
        chave = ("/autonomos/resp-seguro-rc/", "corpo_curto")
        self.assertIn(chave, self.idx)
        self.assertEqual(self.idx[chave]["evidencia"]["word_count"], 396)

    def test_corpo_curto_nao_dispara_no_cenario_errado(self):
        # banc tem word_count=916 (>=400); controle e severidade limpa.
        self.assertNotIn(("/bancario/adesao-automatica-seguro-opt-out-silencioso/", "corpo_curto"), self.idx)
        self.assertNotIn(("/aereo/alteracao-aeroporto-mesma-cidade/", "corpo_curto"), self.idx)
        self.assertNotIn(("/jurisprudencia/stf-adi-4376/", "corpo_curto"), self.idx)

    def test_fonte_insuficiente_dispara_no_cenario_certo(self):
        self.assertIn(("/jurisprudencia/stf-adi-4376/", "fonte_insuficiente"), self.idx)
        self.assertIn(("/bancario/adesao-automatica-seguro-opt-out-silencioso/", "fonte_insuficiente"), self.idx)

    def test_fonte_insuficiente_nao_dispara_no_cenario_errado(self):
        # resp-seguro-rc so tem corpo_entre_250_e_400_palavras, nao fonte; controle e limpo.
        self.assertNotIn(("/autonomos/resp-seguro-rc/", "fonte_insuficiente"), self.idx)
        self.assertNotIn(("/aereo/alteracao-aeroporto-mesma-cidade/", "fonte_insuficiente"), self.idx)

    def test_precedente_dispara_quando_pagina_nao_cita_o_processo(self):
        chave = ("/jurisprudencia/stf-adi-4376/", "precedente_disponivel_nao_citado")
        self.assertIn(chave, self.idx)
        ev = self.idx[chave]["evidencia"]
        self.assertEqual(ev["numero_processo_extraido"], "1723456")
        self.assertEqual(ev["acordao_chave"], "acordao:STJ:TESTE0001")

    def test_precedente_so_com_norma_em_comum_nao_dispara(self):
        """CONTROLE NEGATIVO de ponta a ponta (2026-09-16). acordao:STJ:SONORMA01
        cita a MESMA norma que a pagina, tem ementa do mesmo tema e NAO cita o
        artigo. Norma inteira nao e laco: ele nao pode virar proposta em pagina
        nenhuma. Foi essa rota que produziu 37 das 100 propostas do lote de
        2026-09-08 e que punha o cosseno TF-IDF na casa de 10^8 chamadas.

        ALCANCE DESTE CONTROLE, medido por mutacao em 2026-09-16 e nao suposto:
        ele guarda o CAMINHO DE PONTA A PONTA (carrega_grafo -> gera_propostas),
        isto e, um acordao so-norma nem sequer entra no indice. Quem guarda a
        REGRA de selecao e test_sem_dispositivo_em_comum_nao_ha_candidato, que
        fica vermelho com o mutante que volta a varrer o indice por norma; este
        aqui nao fica, porque aquele mutante tambem le o indice por artigo."""
        for chave, proposta in self.idx.items():
            if proposta["motivo"] != "precedente_disponivel_nao_citado":
                continue
            self.assertNotEqual(proposta["evidencia"]["acordao_chave"], "acordao:STJ:SONORMA01",
                                "precedente por norma inteira voltou a ser proposto em %s" % (chave,))

    def test_precedente_nao_dispara_quando_pagina_ja_cita_o_processo(self):
        # requisito (v): resp-seguro-rc cita "REsp 1723456" no proprio corpo
        # (fixture), entao a proposta de precedente NAO pode disparar --
        # mesmo essa pagina tendo o mesmo dispositivo/norma no grafo.
        chave = ("/autonomos/resp-seguro-rc/", "precedente_disponivel_nao_citado")
        self.assertNotIn(chave, self.idx)

    def test_controle_sem_severidade_medio_e_sem_trafego_nao_gera_nada(self):
        for (path, _motivo) in self.idx:
            self.assertNotEqual(path, "/aereo/alteracao-aeroporto-mesma-cidade/")

    def test_toda_proposta_tem_ao_menos_um_numero_medido_na_evidencia(self):
        for p in self.selecionadas:
            numeros = [v for v in p["evidencia"].values()
                       if isinstance(v, (int, float)) and not isinstance(v, bool)]
            self.assertTrue(numeros, "proposta sem numero medido: %r" % (p,))

    def test_campos_de_contrato_presentes(self):
        for p in self.selecionadas:
            self.assertEqual(p["schema_version"], "proposta_reescrita_v1")
            self.assertEqual(p["aplicar_por"], "gerador datado com CAS; nunca edição manual")
            self.assertIn("§5", p["publicacao"])
            self.assertTrue(p["id"])
            self.assertTrue(p["patch_sugerido"])
            self.assertNotIn("garantimos", p["patch_sugerido"].lower())


class TestEvidenciaSemNumeroEImpossivel(unittest.TestCase):
    def test_evidencia_so_com_texto_reprova(self):
        with self.assertRaises(AssertionError):
            mod.exige_numero_medido({"motivo": "x", "reasons": ["a", "b"]})

    def test_evidencia_com_um_numero_passa(self):
        mod.exige_numero_medido({"motivo": "x", "word_count": 396})  # nao deve levantar

    def test_evidencia_vazia_reprova(self):
        with self.assertRaises(AssertionError):
            mod.exige_numero_medido({})


class TestIdempotenciaTetoEOrdenacao(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmpdir = tempfile.mkdtemp(prefix="propostas-reescrita-")
        self.root = montar_raiz(self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_idempotencia_byte_a_byte_fora_de_gerado_em(self):
        sel1, _, _ = gerar(self.root)
        sel2, _, _ = gerar(self.root)
        self.assertEqual(len(sel1), len(sel2))
        for p1, p2 in zip(sel1, sel2):
            d1 = dict(p1)
            d2 = dict(p2)
            self.assertIn("gerado_em", d1)
            del d1["gerado_em"]
            del d2["gerado_em"]
            self.assertEqual(d1, d2)
        linhas1 = [json.dumps(p, ensure_ascii=False, sort_keys=True) for p in sel1]
        linhas2 = [json.dumps(p, ensure_ascii=False, sort_keys=True) for p in sel2]
        self.assertEqual(linhas1, linhas2, "mesma entrada deve produzir os mesmos bytes (exceto gerado_em)")

    def test_teto_trunca_o_conjunto_ordenado_por_prioridade(self):
        completo, _, total_completo = gerar(self.root, limite=100)
        self.assertGreater(total_completo, 3, "fixture precisa gerar mais de 3 candidatos para provar o teto")
        truncado, _, total_truncado = gerar(self.root, limite=3)
        self.assertEqual(total_truncado, total_completo, "o teto nao muda quantas candidatas existem")
        self.assertEqual(len(truncado), 3)
        self.assertEqual(truncado, completo[:3])
        prioridades = [p["prioridade"] for p in completo]
        self.assertEqual(prioridades, sorted(prioridades, reverse=True))


class SimilaridadeDePrecedenteTest(unittest.TestCase):
    """Ranking TF-IDF: entre dois acordaos que citam a MESMA norma, vence o que
    fala do assunto da pagina; abaixo do minimo, nenhum e proposto."""

    def _cenario(self):
        pagina = {"path": "/familia/guarda-compartilhada/", "title": "Guarda compartilhada",
                  "body_sections": [{"title": "Regra", "body": "A guarda compartilhada e a regra quando ambos os genitores estao aptos; o juiz fixa a residencia da crianca e o convivio."}]}
        norma = "urn:lex:br:federal:lei:2002-01-10;10406"
        base = {"relator": "R", "fonte_url": "https://dadosabertos.web.stj.jus.br/x.json", "sha256_conteudo": "0" * 64}
        topico = dict(base, acordao_chave="acordao:STJ:T1", acordao_rotulo="REsp 1111111 (STJ, TERCEIRA TURMA, 2021-01-01)",
                      classe_numero="REsp 1111111", numero_digits="1111111",
                      ementa="GUARDA COMPARTILHADA. GENITORES APTOS. RESIDENCIA DA CRIANCA E CONVIVIO FIXADOS PELO JUIZ.")
        alheio = dict(base, acordao_chave="acordao:STJ:A1", acordao_rotulo="REsp 2222222 (STJ, PRIMEIRA TURMA, 2021-01-01)",
                      classe_numero="REsp 2222222", numero_digits="2222222",
                      ementa="TRIBUTARIO. ICMS. CREDITO PRESUMIDO. BASE DE CALCULO DO PIS E DA COFINS.")
        artigo = norma + "!art1694"
        topico["norma_chave"] = norma
        topico["dispositivos"] = {artigo}
        alheio["norma_chave"] = norma
        alheio["dispositivos"] = {artigo}
        pagina_normas = {pagina["path"]: [norma]}
        norma_acordaos = {norma: [alheio, topico]}  # alheio primeiro por chave: sem ranking, ele venceria
        disp_acordaos = {artigo: [alheio, topico]}
        pagina_dispositivos = {pagina["path"]: {artigo}}
        sim = mod.monta_similaridade({pagina["path"]: pagina}, pagina_normas, norma_acordaos)
        return pagina, disp_acordaos, pagina_dispositivos, sim

    def test_ranking_escolhe_o_acordao_do_assunto(self):
        pagina, da, pd, sim = self._cenario()
        motivo, evidencia, patch = mod.candidato_precedente(pagina["path"], pagina, da, {}, sim, 0.0, pd)
        self.assertEqual(motivo, "precedente_disponivel_nao_citado")
        self.assertEqual(evidencia["acordao_chave"], "acordao:STJ:T1")
        self.assertGreater(evidencia["similaridade_tfidf"], 0.3)
        self.assertEqual(evidencia["candidatos_avaliados"], 2)
        self.assertLess(evidencia["segunda_similaridade"], 0.05)
        self.assertIn("similaridade", patch.lower())

    def test_mesmo_acordao_em_dois_dispositivos_conta_uma_vez(self):
        pagina, da, pd, sim = self._cenario()
        artigo1 = sorted(pd[pagina["path"]])[0]
        artigo2 = artigo1.rsplit("!art", 1)[0] + "!art1696"
        topico = [ac for ac in da[artigo1] if ac["acordao_chave"] == "acordao:STJ:T1"][0]
        topico["dispositivos"] = {artigo1, artigo2}
        da[artigo2] = [topico]  # o acordao do assunto tambem cita o 2o artigo
        pd[pagina["path"]] = {artigo1, artigo2}
        _, evidencia, _ = mod.candidato_precedente(pagina["path"], pagina, da, {}, sim, 0.0, pd)
        self.assertEqual(evidencia["candidatos_avaliados"], 2)  # 2 acordaos, nao 3 pares
        self.assertEqual(evidencia["acordao_chave"], "acordao:STJ:T1")
        self.assertEqual(evidencia["dispositivos_em_comum"], sorted([artigo1, artigo2]))
        self.assertLess(evidencia["segunda_similaridade"], 0.05)  # a segunda e OUTRO acordao

    def test_sem_dispositivo_em_comum_nao_ha_candidato(self):
        """A REGRA de 2026-09-16, provada por mutacao: o acordao continua no
        indice, continua citando a mesma norma e continua com o cosseno alto --
        so nao compartilha ARTIGO com a pagina. Nenhuma proposta sai. Reverter
        a indexacao para `norma_acordaos` faz este teste ficar vermelho."""
        pagina, da, pd, sim = self._cenario()
        artigo = sorted(pd[pagina["path"]])[0]
        topico = [ac for ac in da[artigo] if ac["acordao_chave"] == "acordao:STJ:T1"][0]
        score = sim.cosseno("p:" + pagina["path"], "a:" + topico["acordao_chave"])
        self.assertGreater(score, 0.3, "o cenario tem de ter cosseno alto, senao o teste mede a coisa errada")
        # a pagina passa a citar OUTRO artigo da mesma norma: laco desfeito.
        pd[pagina["path"]] = {artigo.rsplit("!art", 1)[0] + "!art9999"}
        self.assertIsNone(mod.candidato_precedente(pagina["path"], pagina, da, {}, sim, 0.0, pd))
        # e pagina sem dispositivo nenhum tambem nao propoe.
        self.assertIsNone(mod.candidato_precedente(pagina["path"], pagina, da, {}, sim, 0.0, {}))

    def test_minimo_descarta_e_conta(self):
        pagina, da, pd, sim = self._cenario()
        self.assertIsNone(mod.candidato_precedente(pagina["path"], pagina, da, {}, sim, 0.99, pd))
        self.assertEqual(sim.descartados_por_similaridade, 1)

    def test_tokens_dobram_acento_e_cortam_boilerplate(self):
        self.assertEqual(mod._tokens("Agravo interno no recurso especial. Ação de guarda; provido."), ["acao", "guarda"])
        self.assertEqual(mod._tokens("art. 1.694 do CC e Habeas Corpus 747.318"), ["n1694", "n747318"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
